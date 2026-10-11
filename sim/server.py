"""sim/server.py: the world for the agent month (docs/BACKLOG.md §1.17).

One long-running process holds ONE company: the built app served over http on localhost, ONE browser context
(so every page shares one IndexedDB), the app's clock, and the outside world (sim/world.py). Each person has
their own page in that context (desktop for the office, a 390px phone for the field and the client). Agents
reach it only through sim/act, which posts to /act; the main session drives days through sim/simctl, which
posts to /admin with the run's token.

Rules the server enforces:
- Turns are serialised (one lock). Before a person acts, their page reloads the shared state if anyone else
  saved since it last loaded; after the action the page saves (saveNow) and the server bumps the version.
  Idle pages cannot write: their IndexedDB writes are dropped (a stale timer must not overwrite the company).
- The clock: appSetDay for the day (the day's APP_DAY_HOOKS run once, on the world page), and the time of day
  pinned with the context clock: morning 07:30, work1 10:00, work2 13:30, eod 16:30, plus two minutes per
  action in the slot.
- Agents never evaluate JavaScript. /act takes a fixed set of verbs and passes their text only as data.
- Every action is logged (actions.jsonl: who, app day and time, screen, control, result, toasts, errors, and
  the find-it-again check after any create). The DB is snapshotted to db.json after every change, and the
  server state to world.json, so a run resumes after a crash or a usage pause (--resume).

    python3 sim/server.py --run pilot1            # a fresh run (refuses if the run exists)
    python3 sim/server.py --run pilot1 --resume   # pick up where it stopped
"""
import argparse, asyncio, base64, hashlib, json, os, random, re, secrets, struct, sys, time, zlib
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
DIST = os.path.join(ROOT, 'dist', 'smartdesigns_projects.html')
RUNS = os.path.join(HERE, 'runs')
PAGE_TOOLS = open(os.path.join(HERE, 'page_tools.js'), encoding='utf-8').read()
RUNTIME_JS = open(os.path.join(ROOT, 'tests', 'month_runtime.js'), encoding='utf-8').read()
DB_KEY = 'smartdesigns:portfolio:v2'
DESKTOP = {'width': 1440, 'height': 900}
PHONE = {'width': 390, 'height': 844}
SITE = {'latitude': 40.6893, 'longitude': -73.9908}
TZ = '-04:00'
# uid: (role, phone, name, first view). The order is the order of a morning (the field first).
PEOPLE = {
    'u_angel': ('foreman', True, 'Angel'), 'u_alberto': ('crew', True, 'Alberto'), 'u_alex': ('driver', True, 'Alex'),
    'u_owner': ('owner', False, 'Alan Mishali'), 'u_alan': ('pm', False, 'Alan (PM)'), 'u_chen': ('coord', False, 'Chen Biron'),
    'u_sarah': ('designer', False, 'Sarah Davis'), 'u_billing': ('billing', False, 'Billing'), 'u_controller': ('controller', False, 'Controller'),
    'u_klein': ('client', True, 'Sarah & David Klein'),
}
STAFF_MAIL = ['u_owner', 'u_alan', 'u_chen', 'u_angel', 'u_sarah', 'u_billing', 'u_controller', 'u_alberto', 'u_alex']
DEFAULT_PROJECT = {'u_angel': 'p121', 'u_alberto': 'p121', 'u_alex': 'p121'}   # the seed's field crew is on 121 State
SLOTS = {'morning': '07:30', 'work1': '10:00', 'work': '10:30', 'work2': '13:30', 'eod': '16:30'}   # 'work' is the lean plan's one work slot
VERBS = {'screen', 'find', 'tap', 'type', 'pick', 'upload', 'photo', 'back', 'scroll', 'go', 'ask', 'mail', 'call', 'news', 'help', 'key'}
PAGE_CHARS = 3600
MUTATING = {'tap', 'type', 'pick', 'upload', 'photo', 'back', 'go', 'ask', 'key'}

INIT_JS = r"""
(() => { try { const pos = { coords: { latitude: 40.6893, longitude: -73.9908, accuracy: 12 }, timestamp: 0 };
  Object.defineProperty(navigator, 'geolocation', { value: { getCurrentPosition: (ok) => setTimeout(() => ok(pos), 0), watchPosition: (ok) => { setTimeout(() => ok(pos), 0); return 1; }, clearWatch: () => {} } }); } catch (e) {} })();
(() => { const q = new URLSearchParams(location.search); let s = (+q.get('s') || 20260903) >>> 0;
  Math.random = function () { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; })();
"""
HASH_JS = """async () => { try { await saveNow(); } catch (e) {} const s = (typeof lastSaved === 'string' && lastSaved) || JSON.stringify(DB);
  let h = 2166136261 >>> 0; for (let i = 0; i < s.length; i += 7) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; }
  return [s.length, h.toString(16), window.__simDropped || 0]; }"""


def now_iso(): return datetime.now().isoformat(timespec='seconds')


def weekdays_after(d, n):
    out, x = [], date.fromisoformat(d)
    while len(out) < n:
        x += timedelta(days=1)
        if x.weekday() < 5: out.append(x.isoformat())
    return out


def png_bytes(seed, w=480, h=360):
    """An invented photo: a seeded block picture, nothing real (a site photo stand-in)."""
    r = random.Random(seed)
    base = [r.randrange(60, 200) for _ in range(3)]
    blocks = [(r.randrange(w), r.randrange(h), r.randrange(40, 200), r.randrange(30, 150), [r.randrange(256) for _ in range(3)]) for _ in range(9)]
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            c = base
            for bx, by, bw, bh, col in blocks:
                if bx <= x < bx + bw and by <= y < by + bh: c = col
            g = (x + y) % 23
            raw += bytes((min(255, c[0] + g), min(255, c[1] + g), min(255, c[2] + g)))
    def chunk(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(bytes(raw), 6)) + chunk(b'IEND', b'')


def pdf_bytes(text):
    """A minimal one-page PDF carrying the attachment's text (invented data from the world)."""
    lines = [l[:95] for l in str(text or '').splitlines()][:55] or ['']
    esc = lambda s: s.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
    body = 'BT /F1 10 Tf 40 800 Td 12 TL ' + ' '.join(f'({esc(l)}) Tj T*' for l in lines) + ' ET'
    objs = ['<< /Type /Catalog /Pages 2 0 R >>', '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
            '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>',
            f'<< /Length {len(body.encode("latin-1", "replace"))} >>\nstream\n{body}\nendstream',
            '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>']
    out, offs = b'%PDF-1.4\n', []
    for i, o in enumerate(objs, 1):
        offs.append(len(out)); out += f'{i} 0 obj\n{o}\nendobj\n'.encode('latin-1', 'replace')
    x = len(out)
    out += f'xref\n0 {len(objs) + 1}\n0000000000 65535 f \n'.encode() + b''.join(f'{o:010d} 00000 n \n'.encode() for o in offs)
    out += f'trailer << /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{x}\n%%EOF\n'.encode()
    return out


class Sim:
    def __init__(self, run, port, resume, seed, debug=False):
        self.run, self.port, self.debug = run, port, debug
        self.dir = os.path.join(RUNS, run)
        self.lock = asyncio.Lock()
        self.pages, self.page_ver, self.errs, self.cdp, self.device = {}, {}, {}, {}, {}
        self.last_active = None
        self.screens = {}   # uid -> {'pages': [...], 'i': n, 'header': str}
        self.mail_map = {}  # uid -> [message ids] from the last `mail` list
        self.stop = asyncio.Event()
        if resume:
            if not os.path.exists(os.path.join(self.dir, 'world.json')): raise SystemExit(f'no run {run} to resume')
            self.state = json.load(open(os.path.join(self.dir, 'world.json')))
            self.token = open(os.path.join(self.dir, '.admin_token')).read().strip()
        else:
            if os.path.exists(os.path.join(self.dir, 'world.json')): raise SystemExit(f'run {run} exists: pass --resume, or pick a new name')
            for d in ('diary', 'files', 'shots', 'world'): os.makedirs(os.path.join(self.dir, d), exist_ok=True)
            self.token = secrets.token_hex(16)
            open(os.path.join(self.dir, '.admin_token'), 'w').write(self.token)
            self.state = {'run': run, 'seed': seed, 'created': now_iso(), 'day': None, 'slot': 'morning', 'slot_n': 0, 'version': 0, 'hash': '',
                          'boots': 0, 'actions': 0, 'turn': None, 'people': {}, 'ext_mail': {}, 'drive': [], 'calls': [], 'news': {},
                          'seen': {}, 'fia_pending': {}, 'sent_seen': {}, 'world': {}, 'days_done': []}
        self.resume = resume
        import world as W, referee as R
        self.World, self.Referee = W, R
        self.world = W.World(self)
        self.referee = R.Referee(self)

    # ------------------------------------------------------------------ persistence
    def save_state(self):
        p = os.path.join(self.dir, 'world.json')
        json.dump(self.state, open(p + '.tmp', 'w'), indent=1, default=str); os.replace(p + '.tmp', p)

    def log(self, rec):
        rec = {'t': now_iso(), 'day': self.state['day'], 'slot': self.state['slot'], **rec}
        with open(os.path.join(self.dir, 'actions.jsonl'), 'a') as f: f.write(json.dumps(rec, default=str) + '\n')

    def clock_str(self):
        hh, mm = map(int, SLOTS[self.state['slot']].split(':'))
        m = hh * 60 + mm + 2 * min(self.state.get('slot_n', 0), 80)
        return f"{m // 60:02d}:{m % 60:02d}"

    async def set_clock(self):
        if self.state['day']: await self.ctx.clock.set_system_time(f"{self.state['day']}T{self.clock_str()}:00{TZ}")

    # ------------------------------------------------------------------ the browser
    async def start_browser(self):
        from playwright.async_api import async_playwright
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.launch()
        self.ctx = await self.browser.new_context(viewport=DESKTOP, geolocation=SITE, permissions=['geolocation'], timezone_id='America/New_York',
                                                  accept_downloads=True)
        await self.ctx.add_init_script(INIT_JS)
        base = f'http://127.0.0.1:{self.port}'
        await self.ctx.route('**/*', lambda r: r.continue_() if r.request.url.startswith(base) or r.request.url.startswith('data:') or r.request.url.startswith('blob:') else r.abort())
        first = (self.state['day'] or self.world.days[0])
        await self.ctx.clock.set_system_time(f"{first}T06:30:00{TZ}")
        if self.resume:   # put the snapshot back into IndexedDB before the app boots
            snap = os.path.join(self.dir, 'db.json')
            pg = await self.ctx.new_page()
            await pg.goto(base + '/blank')
            txt = open(snap, encoding='utf-8').read()
            await pg.evaluate("""([k, v]) => new Promise((res, rej) => { const r = indexedDB.open('smartdesigns', 1);
                r.onupgradeneeded = () => r.result.createObjectStore('kv');
                r.onsuccess = () => { const tx = r.result.transaction('kv', 'readwrite'); tx.objectStore('kv').put(v, k); tx.oncomplete = () => res(true); tx.onerror = () => rej(tx.error); };
                r.onerror = () => rej(r.error); })""", [DB_KEY, txt])
            await pg.close()
        await self.page('__world')
        if not self.resume:
            await self.setup_fresh()

    async def page(self, uid):
        if uid in self.pages: return self.pages[uid]
        pg = await self.ctx.new_page()
        self.errs[uid] = []
        pg.on('pageerror', lambda e, u=uid: self.errs[u].append(str(e)[:240]))
        pg.on('dialog', lambda d, u=uid: asyncio.ensure_future(self._dialog(u, d)))
        self.cdp[uid] = await self.ctx.new_cdp_session(pg)
        self.device[uid] = None
        await self.set_device(uid, uid in PEOPLE and PEOPLE[uid][1])
        self.pages[uid] = pg
        self.page_ver[uid] = -1
        await self.boot(uid)
        return pg

    async def set_device(self, uid, phone, force=False):
        """A 390px phone with touch (field roles and the client always; an office person when a task says so)."""
        if self.device.get(uid) == bool(phone) and not force: return
        c = self.cdp[uid]
        if phone:
            await c.send('Emulation.setDeviceMetricsOverride', {'width': PHONE['width'], 'height': PHONE['height'], 'deviceScaleFactor': 2, 'mobile': True})
            await c.send('Emulation.setTouchEmulationEnabled', {'enabled': True, 'maxTouchPoints': 5})
        else:
            await c.send('Emulation.clearDeviceMetricsOverride')
            await c.send('Emulation.setTouchEmulationEnabled', {'enabled': False})
        self.device[uid] = bool(phone)

    async def shot(self, uid, path):
        """A screenshot that keeps a phone a phone: Playwright's own screenshot puts the context's desktop viewport back,
        so phone pages are captured through CDP as they are laid out."""
        if self.device.get(uid):
            r = await self.cdp[uid].send('Page.captureScreenshot', {'format': 'png'})
            open(path, 'wb').write(base64.b64decode(r['data']))
        else:
            await self.pages[uid].screenshot(path=path, full_page=False)

    async def _dialog(self, uid, d):
        self.errs.setdefault('dialogs', []).append(f'{uid}: {d.type}: {d.message[:160]}')
        self.last_dialog = f'The app asked ({d.type}): "{d.message[:200]}". Answered OK.'
        try: await d.accept()
        except Exception: pass

    async def boot(self, uid):
        """Load (or reload) a person's page from the shared state and bring them back to where they were."""
        pg = self.pages[uid]
        self.state['boots'] += 1
        s = (int(hashlib.sha1(f"{self.state['seed']}:{self.state['boots']}".encode()).hexdigest()[:8], 16)) or 1
        t0 = time.time()
        await pg.goto(f'http://127.0.0.1:{self.port}/app?s={s}')
        await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=120000)
        await pg.evaluate(PAGE_TOOLS)
        await pg.evaluate("window.__simActive = false")
        if self.state['drive']: await pg.evaluate("f => __SIM.driveSync(f)", self.state['drive'])
        if uid == '__world':
            await pg.evaluate(RUNTIME_JS)
        elif uid in PEOPLE:
            where = self.state['people'].get(uid) or {'cur': DEFAULT_PROJECT.get(uid, ''), 'view': ''}
            await pg.evaluate("""([u, w]) => { if ((DB.deviceUser || '') !== u || (currentUser() || {}).id !== u) signIn(u);
                if (w && w.cur) try { setCurrent(w.cur); } catch (e) {}
                if (w && w.view && (ROLE_VIEWS[role()] || []).includes(w.view)) view = w.view;
                render(); }""", [uid, where])
        self.page_ver[uid] = self.state['version']
        return round(time.time() - t0, 1)

    async def fresh(self, uid):
        """The page `uid` is about to act: the last actor's work is flushed first, then this page reloads if stale."""
        if self.last_active and self.last_active != uid and self.last_active in self.pages:
            await self.commit(self.last_active)
        pg = await self.page(uid)
        reloaded = False
        if self.page_ver[uid] < self.state['version']:
            await self.boot(uid); reloaded = True
            if uid in self.state['fia_pending']: await self.fia_after_reload(uid)
        self.last_active = uid
        if self.device.get(uid) and await pg.evaluate("innerWidth") != PHONE['width']: await self.set_device(uid, True, force=True)
        await pg.evaluate("window.__simActive = true")
        return pg, reloaded

    async def fia_after_reload(self, uid):
        """A record its creator could not see right after saving: is it on their screen after a reload?"""
        pg = self.pages[uid]
        for x in self.state['fia_pending'].pop(uid, []):
            seen = await pg.evaluate("n => __SIM.onScreen(n)", x['name'])
            self.log({'uid': uid, 'cmd': 'fia_after_reload', 'args': [x['key']], 'ok': bool(seen['on']), 'result': x['name'][:80]})

    async def commit(self, uid):
        """Save the page's state to the shared database; a change bumps the version and writes the snapshot."""
        pg = self.pages[uid]
        if self.page_ver.get(uid, -1) < self.state['version']:
            # a stale page must never write: someone else saved since it loaded (its own changes were saved when it acted)
            return False
        await pg.evaluate("window.__simActive = true")
        try: n, h, dropped = await pg.evaluate(HASH_JS)
        except Exception as e: return False
        changed = h != self.state['hash']
        if changed:
            self.state['version'] += 1; self.state['hash'] = h
            txt = await pg.evaluate("() => (typeof lastSaved === 'string' && lastSaved) || JSON.stringify(DB)")
            p = os.path.join(self.dir, 'db.json')
            open(p + '.tmp', 'w', encoding='utf-8').write(txt); os.replace(p + '.tmp', p)
        self.page_ver[uid] = self.state['version']
        await pg.evaluate("window.__simActive = false")
        self.save_state()
        return changed

    async def setup_fresh(self):
        """Day one: the company as seeded, the app day pinned, every staff Demo Workspace connected."""
        pg, _ = await self.fresh('__world')
        self.state['day'] = self.world.days[0]; self.state['slot'] = 'morning'
        await self.ctx.clock.set_system_time(f"{self.state['day']}T06:40:00{TZ}")
        await pg.evaluate("d => appSetDay(d)", self.state['day'])
        for u in STAFF_MAIL:
            try: await pg.evaluate("u => __MS.connect(u)", u)
            except Exception as e: self.log({'uid': '__world', 'cmd': 'connect', 'args': [u], 'error': str(e)[:200]})
        await pg.evaluate("() => { try { clearInterval(gsTimerId); } catch (e) {} }")
        await self.commit('__world')
        self.world.start()
        for u in PEOPLE: self.diary_init(u)
        self.save_state()

    def diary_init(self, uid):
        p = os.path.join(self.dir, 'diary', f'{uid}.md')
        if not os.path.exists(p):
            open(p, 'w').write(f"# {PEOPLE[uid][2]}: work diary ({PEOPLE[uid][0]})\n\nKept by {PEOPLE[uid][2]}. Read it each morning; write it at the end of each day.\n\n")

    def diary_line(self, uid, text):
        if uid not in PEOPLE: return
        self.diary_init(uid)
        with open(os.path.join(self.dir, 'diary', f'{uid}.md'), 'a') as f: f.write(text.rstrip() + '\n')

    # ------------------------------------------------------------------ the agents' verbs
    async def act(self, uid, cmd, args, opts):
        if uid not in PEOPLE: return {'ok': False, 'text': f'unknown person {uid}; people: {", ".join(PEOPLE)}'}
        if cmd not in VERBS:
            self.log({'uid': uid, 'cmd': cmd, 'args': args, 'refused': True})
            return {'ok': False, 'text': f'refused: "{cmd}" is not something a person can do on their screen. Verbs: {", ".join(sorted(VERBS))}'}
        if cmd == 'help': return {'ok': True, 'text': HELP}
        async with self.lock:
            t = self.state['turn']
            if t and t['uid'] != uid:
                return {'ok': False, 'text': f"it is {PEOPLE.get(t['uid'], ('', '', t['uid']))[2]}'s turn, not yours ({uid})"}
            if t and t['used'] >= t['cap']:
                return {'ok': False, 'text': f"your turn is over: {t['used']} actions used of {t['cap']}. Write your diary and stop."}
            if t: t['used'] += 1
            self.state['actions'] += 1
            if cmd in MUTATING: self.state['slot_n'] = self.state.get('slot_n', 0) + 1
            await self.set_clock()
            if cmd in ('news', 'call'):
                out = await getattr(self, 'v_' + cmd)(uid, None, args, opts)
                self.save_state(); return out
            t_act = time.time()
            pg, reloaded = await self.fresh(uid)
            self.last_dialog = ''
            n_toast = await pg.evaluate("__SIM.toasts.length"); n_err = len(self.errs[uid])
            before = await pg.evaluate("__SIM.keys()") if cmd in MUTATING else None
            title0 = await pg.evaluate("__SIM.title()")
            form = await pg.evaluate("__SIM.formStats()") if cmd == 'tap' else None
            try:
                if reloaded and cmd in ('tap', 'type', 'pick', 'upload', 'photo'):
                    out = await self.render_screen(uid, pg)
                    out['ok'] = False
                    out['text'] = 'Your screen refreshed since you last looked (the company moved on). Nothing was tapped; here it is now:\n' + out['text']
                else:
                    out = await getattr(self, 'v_' + cmd)(uid, pg, args, opts)
            except Exception as e:
                out = {'ok': False, 'text': f'that did not work: {str(e).splitlines()[0][:200]}'}
            toasts = (await pg.evaluate("__SIM.toasts"))[n_toast:]
            errs = self.errs[uid][n_err:]
            creates = []
            if before is not None:
                await pg.wait_for_timeout(150)
                after = await pg.evaluate("__SIM.keys()")
                new = [k for k in after if k not in before][:12]
                for k in new:
                    nm = await pg.evaluate("k => __SIM.recordName(k)", k)
                    if not nm['name']: continue   # a record with no name a person could look for (a line, a log row)
                    seen = await pg.evaluate("n => __SIM.onScreen(n)", nm['name'])
                    creates.append({'key': k, 'name': nm['name'], 'on_screen': seen['on'], 'in_toast': seen['toast']})
                    if not seen['on']:
                        self.state['fia_pending'].setdefault(uid, []).append({'key': k, 'name': nm['name'], 'day': self.state['day']})
            changed = await self.commit(uid)
            await pg.evaluate("window.__simActive = true")   # still this person's page until someone else acts
            if self.last_dialog: out['text'] = self.last_dialog + '\n' + out.get('text', '')
            if toasts and cmd not in ('screen', 'scroll'): out['text'] = 'Toast: ' + ' / '.join(toasts[-2:]) + '\n' + out.get('text', '')
            if errs: out['text'] += '\n(the app reported an error: ' + errs[-1][:160] + ')'
            self.log({'uid': uid, 'cmd': cmd, 'args': args, 'screen': title0, 'after': await pg.evaluate("__SIM.title()"), 'control': out.get('control'),
                      'kind': out.get('kind'), 'ok': out.get('ok'), 'result': (out.get('text') or '')[:300] if cmd not in ('screen', 'scroll') else out.get('summary', ''),
                      'toasts': toasts, 'errors': errs, 'creates': creates, 'changed': changed, 'reloaded': reloaded, 'clock': self.clock_str(), 'ms': int((time.time() - t_act) * 1000),
                      'device': 'phone' if self.device.get(uid) else 'desktop', 'form': form if creates else None,
                      'turn_used': (t or {}).get('used')})
            for c in creates:
                if not c['on_screen']: out['text'] += f"\n(find it again: you just created \"{c['name'][:60]}\"; it is {'only in the toast' if c['in_toast'] else 'not on your screen'})"
            self.save_state()
            return out

    def has_box(self, uid): return uid in STAFF_MAIL

    async def render_screen(self, uid, pg, full=False, shot=False):
        S = await pg.evaluate("__SIM.screen()")
        role, phone, name = PEOPLE[uid]
        wd = datetime.fromisoformat(self.state['day']).strftime('%a %b %-d')
        head = f"{wd} {self.clock_str()} · {name} ({role}{', phone' if self.device.get(uid) else ''}) · {S['title']}"
        menu = 'Menu: ' + ' · '.join(S['menu']) if S['menu'] else ''
        pages, cur = [], []
        size = 0
        for l in S['lines']:
            if size + len(l) > PAGE_CHARS and cur: pages.append(cur); cur, size = [], 0
            cur.append(l); size += len(l) + 1
        if cur or not pages: pages.append(cur)
        self.screens[uid] = {'pages': pages, 'i': 0, 'head': head, 'menu': menu}
        self.note_seen(uid, S['title'], '\n'.join(S['lines']))
        self.state['people'].setdefault(uid, {}).update({'view': S['view'], 'title': S['title']})
        try: self.state['people'][uid]['cur'] = await pg.evaluate("DB.currentId || ''")
        except Exception: pass
        txt = self.page_text(uid, full)
        if shot:
            p = os.path.join(self.dir, 'shots', f"{self.state['day']}_{self.clock_str().replace(':', '')}_{uid}_{self.state['actions']}.png")
            await self.shot(uid, p)
            txt += f'\nscreenshot: {p}'
        return {'ok': True, 'text': txt, 'summary': f"{S['title']} · {S['n']} controls · {len(pages)} pages"}

    def page_text(self, uid, full=False):
        sc = self.screens[uid]
        pages = sc['pages']
        body = '\n'.join(l for p in pages for l in p) if full else '\n'.join(pages[sc['i']])
        foot = '' if full or len(pages) == 1 else f"\n-- page {sc['i'] + 1} of {len(pages)}" + (" · `scroll` for more" if sc['i'] + 1 < len(pages) else '') + ' --'
        return '\n'.join(x for x in (sc['head'], sc['menu'] if sc['i'] == 0 else '', body) if x) + foot

    def note_seen(self, uid, title, text):
        low = text.lower()
        for eid, needles in self.world.open_needles().items():
            if any(n.lower() in low for n in needles):
                self.state['seen'].setdefault(eid, {}).setdefault(uid, [self.state['day'], self.state['slot'], title])

    async def settle(self, pg, ms=350):
        await pg.wait_for_timeout(ms)
        try: await pg.wait_for_load_state('domcontentloaded', timeout=3000)
        except Exception: pass

    async def v_screen(self, uid, pg, args, opts):
        return await self.render_screen(uid, pg, full=opts.get('full'), shot=opts.get('shot'))

    async def v_find(self, uid, pg, args, opts):
        """Scan the whole screen for a word, the way a person's eye does: the matching lines with the controls near them."""
        if not args: return {'ok': False, 'text': 'find what?'}
        await self.render_screen(uid, pg)
        sc = self.screens[uid]; lines = [l for p in sc['pages'] for l in p]
        want = args[0].lower(); hits = [i for i, l in enumerate(lines) if want in l.lower()]
        if not hits: return {'ok': True, 'text': f'{sc["head"]}\n"{args[0]}" is not on this screen.'}
        keep = sorted({j for i in hits[:8] for j in range(max(0, i - 2), min(len(lines), i + 5))})
        out, prev = [], -2
        for j in keep:
            if j != prev + 1: out.append('…')
            out.append(lines[j]); prev = j
        return {'ok': True, 'text': sc['head'] + '\n' + '\n'.join(out), 'summary': f'find {args[0]}: {len(hits)} lines'}

    async def v_scroll(self, uid, pg, args, opts):
        sc = self.screens.get(uid)
        if not sc: return await self.render_screen(uid, pg)
        if sc['i'] + 1 >= len(sc['pages']): return {'ok': True, 'text': '(that is the end of this screen)'}
        sc['i'] += 1
        await pg.evaluate("window.scrollBy(0, innerHeight * 0.9)")
        return {'ok': True, 'text': self.page_text(uid), 'summary': f"page {sc['i'] + 1}"}

    async def _resolve(self, pg, n):
        try: n = int(n)
        except Exception: return None, {'ok': False, 'text': f'"{n}" is not a control number from your screen'}
        r = await pg.evaluate("n => __SIM.resolve(n)", n)
        if not r['ok']: return None, {'ok': False, 'text': r['why']}
        return r['sig'], None

    async def v_tap(self, uid, pg, args, opts):
        if not args: return {'ok': False, 'text': 'tap which number?'}
        sig, err = await self._resolve(pg, args[0])
        if err: return err
        loc = pg.locator(f'[data-simn="{int(args[0])}"]').first
        forced = ''
        try: await loc.click(timeout=4000)
        except Exception:
            await loc.evaluate("e => e.click()"); forced = ' (it was covered; tapped through)'
        await self.settle(pg, 400)
        out = await self.render_screen(uid, pg, shot=opts.get('shot'))
        out['control'] = sig['label']; out['kind'] = sig['k']
        out['text'] = f"tapped {args[0]} \"{sig['label'][:60]}\"{forced}\n" + out['text']
        return out

    async def v_type(self, uid, pg, args, opts):
        if len(args) < 2: return {'ok': False, 'text': 'usage: type <n> "text"'}
        sig, err = await self._resolve(pg, args[0])
        if err: return err
        text = args[1]
        if re.match(r'\s*javascript:', text, re.I): return {'ok': False, 'text': 'refused: that is code, not something a person types'}
        loc = pg.locator(f'[data-simn="{int(args[0])}"]').first
        info = await pg.evaluate("n => __SIM.fieldInfo(n)", int(args[0]))
        if info and info['kind'] in ('select', 'check', 'file'): return {'ok': False, 'text': f"{args[0]} is a {info['kind']}: use {'pick' if info['kind'] == 'select' else 'tap' if info['kind'] == 'check' else 'upload'}"}
        try: await loc.fill(text, timeout=4000)
        except Exception:
            await loc.click(timeout=3000); await pg.keyboard.type(text)
        try: await loc.dispatch_event('change')
        except Exception: pass
        if opts.get('enter'):
            await loc.press('Enter'); await self.settle(pg, 400)
            out = await self.render_screen(uid, pg)
            out['text'] = f"typed into {args[0]} \"{sig['label'][:50]}\" and pressed Enter\n" + out['text']
            out['control'] = sig['label']; out['kind'] = 'input'
            return out
        await self.settle(pg, 150)
        return {'ok': True, 'text': f"typed into {args[0]} \"{sig['label'][:50]}\"", 'control': sig['label'], 'kind': 'input'}

    async def v_key(self, uid, pg, args, opts):
        k = (args or ['Enter'])[0]
        if k not in ('Enter', 'Escape', 'Tab'): return {'ok': False, 'text': 'key: Enter, Escape or Tab'}
        await pg.keyboard.press(k); await self.settle(pg, 400)
        out = await self.render_screen(uid, pg); out['text'] = f'pressed {k}\n' + out['text']; out['control'] = k
        return out

    async def v_pick(self, uid, pg, args, opts):
        if len(args) < 2: return {'ok': False, 'text': 'usage: pick <n> "option"'}
        sig, err = await self._resolve(pg, args[0])
        if err: return err
        r = await pg.evaluate("([n, o]) => __SIM.pick(n, o)", [int(args[0]), args[1]])
        if not r['ok']: return {'ok': False, 'text': r['why']}
        await pg.locator(f'[data-simn="{int(args[0])}"]').first.select_option(r['value'], timeout=4000)
        await self.settle(pg, 250)
        return {'ok': True, 'text': f"picked \"{r['text']}\" in {args[0]} \"{sig['label'][:50]}\"", 'control': sig['label'], 'kind': 'select'}

    async def _upload(self, uid, pg, n, path, sig, opts):
        if not os.path.isfile(path): return {'ok': False, 'text': f'no such file: {path}'}
        loc = pg.locator(f'[data-simn="{int(n)}"]').first
        how = ''
        if sig['k'] == 'file':
            await loc.set_input_files(path); how = 'set on the file field'
        else:
            try:
                async with pg.expect_file_chooser(timeout=3000) as fc:
                    await loc.click(timeout=3000)
                ch = await fc.value; await ch.set_files(path); how = 'chosen in the file picker'
            except Exception:
                if await pg.evaluate("n => __SIM.fileInputNear(n)", int(n)):
                    await pg.locator('[data-simfile="1"]').first.set_input_files(path); how = 'put in the file field next to it'
                else: return {'ok': False, 'text': f'{n} does not open a file picker'}
        await self.settle(pg, 700)
        out = await self.render_screen(uid, pg, shot=opts.get('shot'))
        out['text'] = f"uploaded {os.path.basename(path)} ({how})\n" + out['text']; out['control'] = sig['label']; out['kind'] = 'upload'
        return out

    async def v_upload(self, uid, pg, args, opts):
        if len(args) < 2: return {'ok': False, 'text': 'usage: upload <n> <file>'}
        sig, err = await self._resolve(pg, args[0])
        if err: return err
        return await self._upload(uid, pg, args[0], os.path.abspath(args[1]), sig, opts)

    async def v_photo(self, uid, pg, args, opts):
        if not args: return {'ok': False, 'text': 'usage: photo <n>'}
        sig, err = await self._resolve(pg, args[0])
        if err: return err
        d = os.path.join(self.dir, 'files', uid); os.makedirs(d, exist_ok=True)
        p = os.path.join(d, f"IMG_{self.state['day'].replace('-', '')}_{self.clock_str().replace(':', '')}_{self.state['actions']}.png")
        open(p, 'wb').write(png_bytes(f"{self.state['seed']}:{uid}:{self.state['actions']}"))
        return await self._upload(uid, pg, args[0], p, sig, opts)

    async def v_back(self, uid, pg, args, opts):
        r = await pg.evaluate("__SIM.closeTop()")
        if not r:
            hist = self.state['people'].get(uid, {}).get('hist', [])
            if len(hist) >= 2:
                hist.pop(); prev = hist[-1]
                await pg.evaluate("v => { if ((ROLE_VIEWS[role()] || []).includes(v)) { view = v; render(); } }", prev)
                r = 'back to the previous screen'
            else: r = 'nothing to go back to'
        await self.settle(pg, 300)
        out = await self.render_screen(uid, pg); out['text'] = r + '\n' + out['text']; out['control'] = 'back'
        return out

    async def v_go(self, uid, pg, args, opts):
        if not args: return {'ok': False, 'text': 'go where? use a label from your menu'}
        parts = [x.strip() for x in re.split(r'\s*(?:>|›|/)\s*', args[0]) if x.strip()]
        r = await pg.evaluate("l => __SIM.go(l)", parts[0])
        if not r['ok']: return {'ok': False, 'text': r['why']}
        await self.settle(pg, 400)
        for sub in parts[1:]:
            S = await pg.evaluate("__SIM.screen()")
            want = sub.lower()
            hit = next((i for i, s in enumerate(S['sig']) if s['k'] in ('tab', 'button', 'link') and re.sub(r'\s+\d+$', '', s['label'].lower()) == want), None)
            if hit is None: hit = next((i for i, s in enumerate(S['sig']) if s['k'] in ('tab', 'button', 'link') and s['label'].lower().startswith(want)), None)
            if hit is None: break
            await pg.locator(f'[data-simn="{hit + 1}"]').first.click(timeout=4000); await self.settle(pg, 400)
        out = await self.render_screen(uid, pg, shot=opts.get('shot'))
        v = out['text']
        h = self.state['people'].setdefault(uid, {}).setdefault('hist', [])
        cur = self.state['people'][uid].get('view')
        if cur and (not h or h[-1] != cur): h.append(cur); del h[:-12]
        out['control'] = 'menu: ' + args[0]; out['kind'] = 'nav'
        return out

    async def v_ask(self, uid, pg, args, opts):
        if not args: return {'ok': False, 'text': 'ask what?'}
        q = args[0]
        has = await pg.evaluate("() => { const e = document.querySelector('#pa-in'); return !!(e && e.getClientRects().length) }")
        if not has:
            for lab in ('Ask', 'Assistant', 'Raise'):
                r = await pg.evaluate("l => __SIM.go(l)", lab)
                if r['ok']:
                    await self.settle(pg, 400)
                    has = await pg.evaluate("() => { const e = document.querySelector('#pa-in'); return !!(e && e.getClientRects().length) }")
                    if has: break
        if has:
            n0 = await pg.evaluate("document.querySelectorAll('.pa-m').length")
            await pg.fill('#pa-in', q); await pg.press('#pa-in', 'Enter')
            for _ in range(120):
                await pg.wait_for_timeout(250)
                busy = await pg.evaluate("() => { try { return !!paBusy } catch (e) { return false } }")
                if not busy and await pg.evaluate("document.querySelectorAll('.pa-m').length") > n0: break
            ans = await pg.evaluate("() => { const A = [...document.querySelectorAll('#pa-thread .pa-m.a')].pop(); return A ? A.innerText : '' }")
        else:
            has_brief = await pg.evaluate("() => { const e = document.querySelector('#jv-q'); return !!(e && e.getClientRects().length) }")
            if not has_brief: return {'ok': False, 'text': 'there is no assistant box on your screens (no Ask in your menu)'}
            await pg.fill('#jv-q', q); await pg.click('#jv-go'); await pg.wait_for_timeout(1500)
            ans = await pg.evaluate("() => (document.querySelector('#jv-answer') || {}).innerText || ''")
        ans = re.sub(r'\n{2,}', '\n', ans or '').strip()
        await self.render_screen(uid, pg)
        return {'ok': True, 'text': f'You asked: {q}\nAssistant: {ans[:2400] or "(no answer)"}\n(run `screen` to use the buttons in its answer)', 'control': 'ask', 'kind': 'ask'}

    # ---- mail: the person's own mailbox (the Demo Workspace for staff; a world mailbox for the client)
    def ext_box(self, uid): return self.state['ext_mail'].setdefault(uid, [])

    def fmt_when(self, ms):
        try: return datetime.fromtimestamp(ms / 1000, ZoneInfo('America/New_York')).strftime('%-m/%-d %H:%M')
        except Exception: return ''

    async def v_mail(self, uid, pg, args, opts):
        sub = (args[0] if args else 'list').lower()
        staff = self.has_box(uid)
        if sub == 'senddraft':
            mid = self._mail_id(uid, args[1:2])
            if not mid or not staff: return {'ok': False, 'text': 'send which draft? run `mail drafts` first'}
            r = await pg.evaluate("([u, i]) => __SIM.mbSendDraft(u, i)", [uid, mid])
            if not r: return {'ok': False, 'text': 'no such draft'}
            self.state['sent_seen'].setdefault(r['id'], {'by': uid, 'how': 'person'})
            notes = await self.post_office(pg)
            return {'ok': True, 'text': f"sent to {r['to'] or '(nobody: the draft has no To)'}: {r['subject']}" + (f'\n{notes}' if notes else ''), 'control': 'mail senddraft', 'kind': 'send'}
        if sub in ('list', 'inbox', 'sent', 'drafts'):
            box = sub if sub in ('sent', 'drafts') else 'inbox'
            L = await pg.evaluate("([u, b]) => __SIM.mbList(u, b)", [uid, box]) if staff else \
                [m for m in sorted(self.ext_box(uid), key=lambda m: -m['at']) if (box == 'sent') == bool(m.get('sent'))]
            page = int(opts.get('page') or 1); L2 = L[(page - 1) * 15: page * 15]
            self.mail_map[uid] = [m['id'] for m in L]
            if not L2: return {'ok': True, 'text': f'({box}: nothing)'}
            rows = [f"{(page - 1) * 15 + i + 1}. {'* ' if m.get('unread') else ''}{self.fmt_when(m['at'])} {('to ' + (m['to'] or '(no To yet)')) if box != 'inbox' else m['from']} | {m['subject']}"
                    + (f" [{len(m['att'])} att]" if m.get('att') else '') for i, m in enumerate(L2)]
            more = f'\n(page {page}; `mail --page {page + 1}` for older)' if len(L) > page * 15 else ''
            return {'ok': True, 'text': f"Mail, {box} ({sum(1 for m in L if m.get('unread'))} unread; * = unread)\n" + '\n'.join(rows) + more, 'kind': 'mail'}
        if sub == 'read':
            mid = self._mail_id(uid, args[1:2])
            if not mid: return {'ok': False, 'text': 'read which number? run `mail` first'}
            if staff: m = await pg.evaluate("([u, i]) => __SIM.mbRead(u, i)", [uid, mid])
            else:
                m = next((x for x in self.ext_box(uid) if x['id'] == mid), None)
                if m: m['unread'] = False
            if not m: return {'ok': False, 'text': 'no such message'}
            paths = []
            for a in m.get('att') or []:
                d = os.path.join(self.dir, 'files', uid); os.makedirs(d, exist_ok=True)
                fn = re.sub(r'[^\w.\- ]', '_', a['filename'])[:90] or 'attachment'
                p = os.path.join(d, fn)
                if fn.lower().endswith('.pdf'): open(p, 'wb').write(pdf_bytes(a.get('text', '')))
                else: open(p, 'w').write(a.get('text', ''))
                paths.append(f"  {a['filename']} -> {p}" + (f"\n    {a.get('text', '')[:600]}" if a.get('text') else ''))
            txt = f"From: {m['from']}\nTo: {m['to']}\n" + (f"Cc: {m['cc']}\n" if m.get('cc') else '') + f"Date: {self.fmt_when(m['at'])}\nSubject: {m['subject']}\n\n{m['body'][:3000]}"
            if paths: txt += '\n\nAttachments (saved for upload):\n' + '\n'.join(paths)
            return {'ok': True, 'text': txt, 'kind': 'mail'}
        if sub in ('reply', 'send'):
            if sub == 'reply':
                mid = self._mail_id(uid, args[1:2])
                if not mid or len(args) < 3: return {'ok': False, 'text': 'usage: mail reply <n> "text"'}
                if staff: m = await pg.evaluate("([u, i]) => __SIM.mbRead(u, i)", [uid, mid])
                else: m = next((x for x in self.ext_box(uid) if x['id'] == mid), None)
                if not m: return {'ok': False, 'text': 'no such message'}
                me = self.addr_of(uid)
                to = m['to'] if me and me.split('<')[-1].strip('> ').lower() in m['from'].lower() else m['from']
                subj = m['subject'] if m['subject'].lower().startswith('re:') else 'Re: ' + m['subject']
                body, thread = args[2], m.get('thread') or ''
            else:
                if len(args) < 4: return {'ok': False, 'text': 'usage: mail send "to" "subject" "body"'}
                to = self.world.resolve_addr(args[1])
                if not to: return {'ok': False, 'text': f'no address for "{args[1]}"; use a name from your contacts or an email'}
                subj, body, thread = args[2], args[3], ''
            r = await self.send_mail(uid, pg, to, subj, body, thread)
            return {'ok': True, 'text': f'sent to {to}: {subj}' + (f'\n{r}' if r else ''), 'control': 'mail ' + sub, 'kind': 'send'}
        return {'ok': False, 'text': 'mail | mail sent | mail drafts | mail read <n> | mail senddraft <n> | mail reply <n> "text" | mail send "to" "subject" "body"'}

    def _mail_id(self, uid, a):
        try: return self.mail_map.get(uid, [])[int(a[0]) - 1]
        except Exception: return None

    def addr_of(self, uid):
        if uid in self.world.staff_addr: return self.world.staff_addr[uid]
        return self.world.agent_addr.get(uid, '')

    async def send_mail(self, uid, pg, to, subject, body, thread):
        at = int(datetime.fromisoformat(f"{self.state['day']}T{self.clock_str()}:00{TZ}").timestamp() * 1000)
        mid = f"sim_{uid}_{self.state['actions']}"
        frm = self.addr_of(uid)
        msg = {'id': mid, 'threadId': thread or f'simt_{mid}', 'labelIds': ['SENT'], 'internalDate': at,
               'headers': {'From': frm, 'To': to, 'Cc': '', 'Subject': subject, 'Date': datetime.fromtimestamp(at / 1000).strftime('%a, %d %b %Y %H:%M:%S')},
               'body': body, 'attachments': []}
        if self.has_box(uid):
            await pg.evaluate("([u, m]) => __SIM.mbPut(u, m)", [uid, msg])
            self.state['sent_seen'].setdefault(mid, {'by': uid, 'how': 'person'})
        else:
            self.ext_box(uid).append({'id': mid, 'from': frm, 'to': to, 'subject': subject, 'body': body, 'at': at, 'thread': msg['threadId'], 'sent': True, 'att': []})
        return await self.post_office(pg, [{'uid': uid, 'id': mid, 'from': frm, 'to': to, 'cc': '', 'subject': subject, 'body': body, 'at': at, 'thread': msg['threadId'], 'att': []}])

    async def post_office(self, pg, msgs=None):
        """Deliver what staff sent: to a colleague's mailbox, to the client agent's mailbox, or out to the world."""
        if msgs is None:
            msgs = [m for m in await pg.evaluate("__SIM.mbSentAll()") if m['id'] not in self.state['sent_seen'] or not self.state['sent_seen'][m['id']].get('done')]
        notes = []
        for m in msgs:
            rec = self.state['sent_seen'].setdefault(m['id'], {'by': m['uid'], 'how': 'system' if not self.state['turn'] else ('person' if self.state['turn']['uid'] == m['uid'] else 'system')})
            if rec.get('done'): continue
            rec.update({'done': True, 'to': m['to'], 'subject': m['subject'], 'day': self.state['day'], 'slot': self.state['slot']})
            for addr in re.split(r',\s*(?=[^,]*@)', (m['to'] or '') + (',' + m['cc'] if m.get('cc') else '')):
                addr = addr.strip()
                if not addr: continue
                who = self.world.who_is(addr)
                if who in STAFF_MAIL and who != m['uid']:
                    copy = {'id': f"{m['id']}_to_{who}", 'threadId': m['thread'] or m['id'], 'labelIds': ['INBOX', 'UNREAD'], 'internalDate': m['at'],
                            'headers': {'From': m['from'], 'To': m['to'], 'Cc': m.get('cc', ''), 'Subject': m['subject'], 'Date': ''}, 'body': m['body'],
                            'attachments': [{'id': f"{m['id']}_a{i}", 'filename': a['filename'], 'mime': 'application/pdf', 'size': 40000, 'text': a.get('text', '')} for i, a in enumerate(m.get('att') or [])]}
                    await pg.evaluate("([u, x]) => __SIM.mbPut(u, x)", [who, copy]); notes.append(f'delivered to {who}')
                elif who in PEOPLE and who not in STAFF_MAIL:
                    self.ext_box(who).append({'id': f"{m['id']}_to_{who}", 'from': m['from'], 'to': m['to'], 'subject': m['subject'], 'body': m['body'],
                                              'at': m['at'], 'thread': m['thread'], 'unread': True, 'att': m.get('att') or []})
                    notes.append(f'delivered to {who}')
                elif who != m['uid']:
                    self.world.on_outbound(m, addr)
        return '; '.join(notes)

    async def v_call(self, uid, pg, args, opts):
        if len(args) < 2: return {'ok': False, 'text': 'usage: call "<person>" "what was said"'}
        who = self.world.who_is(args[0]) or self.world.resolve_party(args[0])
        if not who: return {'ok': False, 'text': f'no number for "{args[0]}"'}
        when = f"{self.state['day']} {self.clock_str()}"
        said = args[1]
        self.state['calls'].append({'from': uid, 'to': who, 'at': when, 'said': said})
        self.diary_line(uid, f"- call {when}, you called {who}: \"{said}\"")
        reply = ''
        if who in PEOPLE:
            self.diary_line(who, f"- call {when}, {PEOPLE[uid][2]} called you: \"{said}\"")
            self.state['news'].setdefault(who, []).append(f"{when} call from {PEOPLE[uid][2]}: \"{said}\"")
            reply = f'{PEOPLE[who][2]} heard it. It is in both diaries; it is a promise only if someone logs it in the app.'
        else:
            reply = self.world.on_call(uid, who, said)
            self.diary_line(uid, f"  they said: \"{reply}\"")
        self.log({'uid': uid, 'cmd': 'call', 'args': args, 'result': reply[:200]})
        return {'ok': True, 'text': reply, 'kind': 'call', 'control': 'call'}

    async def v_news(self, uid, pg, args, opts):
        items = self.state['news'].pop(uid, [])
        self.log({'uid': uid, 'cmd': 'news', 'result': f'{len(items)} items'})
        return {'ok': True, 'text': ('What happened around you since your last turn:\n' + '\n'.join('- ' + x for x in items)) if items else 'Nothing new around you.'}

    # ------------------------------------------------------------------ the main session's controls
    async def admin(self, cmd, a):
        async with self.lock:
            if cmd == 'status':
                return {'run': self.run, 'day': self.state['day'], 'slot': self.state['slot'], 'clock': self.clock_str(), 'version': self.state['version'],
                        'turn': self.state['turn'], 'actions': self.state['actions'], 'days': self.world.days, 'days_done': self.state['days_done']}
            if cmd == 'slot':
                if a.get('slot') not in SLOTS: return {'error': 'slot is one of ' + ', '.join(SLOTS)}
                self.state['slot'] = a['slot']; self.state['slot_n'] = 0; self.save_state(); return {'slot': a['slot'], 'clock': self.clock_str()}
            if cmd == 'begin_turn':
                uid = a['uid']
                if uid not in PEOPLE: return {'error': 'unknown person'}
                if a.get('slot'): self.state['slot'] = a['slot']; self.state['slot_n'] = 0
                phone = bool(a.get('phone')) or PEOPLE[uid][1]
                self.state['turn'] = {'uid': uid, 'cap': int(a.get('cap') or 25), 'used': 0, 'slot': self.state['slot'], 'started': now_iso(), 'phone': phone}
                await self.page(uid); await self.set_device(uid, phone)
                self.save_state(); return {'turn': self.state['turn'], 'clock': self.clock_str()}
            if cmd == 'end_turn':
                t = self.state['turn']
                if t and t['uid'] in self.pages:
                    await self.commit(t['uid']); await self.set_device(t['uid'], PEOPLE[t['uid']][1])
                pg, _ = await self.fresh('__world')
                await self.set_clock()
                notes = await self.post_office(pg)
                await self.commit('__world')
                self.state['turn'] = None
                self.log({'uid': (t or {}).get('uid'), 'cmd': 'end_turn', 'result': notes, 'used': (t or {}).get('used')})
                self.save_state(); return {'ended': t, 'mail': notes}
            if cmd == 'world':
                if a.get('slot'): self.state['slot'] = a['slot']; self.state['slot_n'] = 0
                return await self.world.step(self.state['slot'], watchers=a.get('watchers'))
            if cmd == 'advance':
                return await self.advance()
            if cmd == 'referee':
                return await self.referee.score(final=bool(a.get('final')))
            if cmd == 'persist_check':
                return await self.referee.persist_check()
            if cmd == 'check':
                pg, _ = await self.fresh('__world')
                return {'results': await pg.evaluate("L => __MS.checkAll(L)", [[c, {'day': a.get('day') or self.state['day'], 'id': 'adhoc'}] for c in a['checks']])}
            if cmd == 'brief':
                return await self.turn_brief(a['uid'])
            if cmd == 'debug_eval' and self.debug:   # developer use only (server started with --debug); never in a real run
                pg = await self.page(a.get('uid') or '__world')
                return {'result': await pg.evaluate(a['js'])}
            if cmd == 'menu_capture':   # the menu each person sees (SmartDesign workspace only), with each entry's tabs
                out = {}
                for uid in PEOPLE:
                    pg, _ = await self.fresh(uid)
                    top = await pg.evaluate("__SIM.menu()")
                    tree = []
                    for lab in top:
                        r = await pg.evaluate("l => __SIM.go(l)", lab)
                        await self.settle(pg, 300)
                        subs = await pg.evaluate("""() => [...document.querySelectorAll('#subnav button, #mtabs button')].filter(e => e.getClientRects().length && !e.closest('section.view'))
                            .map(e => e.innerText.replace(/\\s+/g, ' ').trim()).filter(Boolean)""")
                        tree.append({'label': lab, 'tabs': subs if r.get('ok') else []})
                    await self.commit(uid)
                    out[uid] = {'role': PEOPLE[uid][0], 'phone': PEOPLE[uid][1], 'menu': tree}
                json.dump(out, open(os.path.join(self.dir, 'menus.json'), 'w'), indent=1)
                return {'menus': os.path.join(self.dir, 'menus.json'), 'people': len(out)}
            if cmd == 'client_docs':
                return await self.client_docs()
            if cmd == 'party':   # adjust an outside party's rules (the selftest makes its supplier answer at once)
                k = self.world.resolve_party(a['party'])
                if not k: return {'error': 'no such party'}
                self.world.parties[k].update(a.get('patch') or {}); self.state['world'].setdefault('party_patch', {})[k] = self.world.parties[k]
                self.save_state(); return {'party': k, 'rules': self.world.parties[k]}
            if cmd == 'world_client':   # the client's side played by world rules on the portal (no client agent turns)
                self.state['world']['client_rules'] = bool(a.get('on')); self.save_state(); return {'client_rules': self.state['world']['client_rules']}
            if cmd == 'world_agent':
                self.state['world']['agent'] = bool(a.get('on')); self.save_state(); return {'world_agent': self.state['world']['agent']}
            if cmd == 'shutdown':
                if self.last_active in self.pages:
                    try: await self.commit(self.last_active)
                    except Exception: pass
                self.save_state(); self.stop.set(); return {'bye': True}
            return {'error': 'unknown admin command ' + cmd}

    async def advance(self):
        """End of day: the referee scores it, a daily copy of the snapshot is kept, the app moves to the next working day."""
        sc = await self.referee.score()
        day = self.state['day']
        self.state['days_done'].append(day)
        try:
            import shutil; shutil.copy(os.path.join(self.dir, 'db.json'), os.path.join(self.dir, f'db_{day}.json'))
        except Exception: pass
        nxt = self.world.next_day(day)
        pg, _ = await self.fresh('__world')
        self.state['day'] = nxt; self.state['slot'] = 'morning'; self.state['slot_n'] = 0
        await self.ctx.clock.set_system_time(f"{nxt}T06:30:00{TZ}")
        r = await pg.evaluate("d => appSetDay(d)", nxt)
        await self.commit('__world')
        self.log({'uid': '__world', 'cmd': 'advance', 'result': r})
        self.save_state()
        return {'scored': sc.get('line'), 'day': nxt, 'hooks': r}

    async def client_docs(self):
        """Every client-facing document a person created, as the client receives it: the print / PDF the firm sends,
        and the portal on the client's phone. Screenshots, PDFs and text go to runs/<run>/client_docs/."""
        cd = os.path.join(self.dir, 'client_docs'); os.makedirs(cd, exist_ok=True)
        keys = []
        for l in open(os.path.join(self.dir, 'actions.jsonl')):
            a = json.loads(l)
            for c in a.get('creates') or []:
                if c['key'].split(':')[0] in ('c.estimates', 'c.changeOrders', 'c.invoices') and c['key'] not in keys: keys.append(c['key'])
        pg, _ = await self.fresh('__world')
        docs = await pg.evaluate("""(keys) => keys.map(k => { const [coll, id] = [k.split(':')[0].slice(2), k.split(':').slice(1).join(':')];
            for (const c of DB.clients) { const d = (c[coll] || []).find(x => x.id === id); if (!d) continue; let t = 0; try { t = docTotal(d).total; } catch (e) {}
              let h = ''; try { h = docPrintHtml(c, d); } catch (e) { h = ''; }
              return { key: k, client: c.name, clientId: c.id, number: d.number || d.id, title: d.title || '', status: d.status || '', total: t,
                type: d.type === 'co' ? 'change order' : d.mode === 'sov' ? 'pay application' : d.type, html: h }; } return null; }).filter(Boolean)""", keys)
        klein = await pg.evaluate("() => { try { return userClientOf(DB.users.find(u => u.id === 'u_klein')); } catch (e) { return ''; } }")
        view = await self.ctx.new_page()
        out = []
        for d in docs:
            base = os.path.join(cd, re.sub(r'[^\w.-]', '_', d['number']))
            rec = {k: v for k, v in d.items() if k != 'html'}
            if d['html']:
                await view.set_content(d['html'], wait_until='load')
                await view.screenshot(path=base + '_print.png', full_page=True)
                try: await view.pdf(path=base + '.pdf', format='Letter', print_background=True); rec['pdf'] = base + '.pdf'
                except Exception: pass
                open(base + '.txt', 'w').write(await view.evaluate("document.body.innerText"))
                rec.update({'print_png': base + '_print.png', 'txt': base + '.txt'})
            if d['clientId'] == klein and d['status'] not in ('draft', ''):
                cp, _ = await self.fresh('u_klein')
                await cp.evaluate("() => { try { view = 'client'; render(); } catch (e) {} }")
                await self.settle(cp, 400)
                hit = await cp.evaluate("""(n) => { const el = [...document.querySelectorAll('section.view.on *')].filter(e => e.children.length < 4 && (e.innerText || '').includes(n)).pop();
                    if (!el) return false; el.scrollIntoView({ block: 'center' });
                    let row = el; while (row && row.parentElement && !row.querySelector('button')) row = row.parentElement;
                    const v = row && [...row.querySelectorAll('button, a')].find(b => /^(View|Open|Review)$/i.test((b.innerText || '').trim()));
                    if (v) v.setAttribute('data-simdoc', '1'); return true; }""", d['number'])
                if hit:
                    await self.shot('u_klein', base + '_portal_row.png'); rec['portal_row_png'] = base + '_portal_row.png'
                    if await cp.locator('[data-simdoc="1"]').count():
                        try: await cp.locator('[data-simdoc="1"]').first.click(timeout=3000); await self.settle(cp, 700)
                        except Exception: pass
                    await self.shot('u_klein', base + '_portal.png'); rec['portal_png'] = base + '_portal.png'
                    await cp.evaluate("() => { document.querySelectorAll('[data-simdoc]').forEach(e => e.removeAttribute('data-simdoc')); try { __SIM.closeTop(); } catch (e) {} }")
                await self.commit('u_klein')
            out.append(rec)
        await view.close()
        json.dump(out, open(os.path.join(cd, 'docs.json'), 'w'), indent=1)
        return {'docs': len(out), 'dir': cd, 'portal': sum(1 for x in out if x.get('portal_png'))}

    async def turn_brief(self, uid):
        role, phone, name = PEOPLE[uid]
        unread = 0
        if self.has_box(uid):
            pg, _ = await self.fresh('__world')
            unread = sum(1 for m in await pg.evaluate("([u, b]) => __SIM.mbList(u, b)", [uid, 'inbox']) if m['unread'])
        else: unread = sum(1 for m in self.ext_box(uid) if m.get('unread'))
        return {'uid': uid, 'name': name, 'role': role, 'phone': phone, 'day': self.state['day'], 'slot': self.state['slot'], 'clock': self.clock_str(),
                'news': len(self.state['news'].get(uid, [])), 'unread': unread, 'run': self.run}

    # ------------------------------------------------------------------ http
    async def handle(self, reader, writer):
        try:
            head = await reader.readuntil(b'\r\n\r\n')
            lines = head.decode('latin-1').split('\r\n')
            method, path, _ = lines[0].split(' ', 2)
            hdrs = {l.split(':', 1)[0].lower(): l.split(':', 1)[1].strip() for l in lines[1:] if ':' in l}
            n = int(hdrs.get('content-length') or 0)
            body = await reader.readexactly(n) if n else b''
            status, ctype, out = 200, 'application/json', b''
            p = path.split('?')[0]
            if p == '/app':
                ctype, out = 'text/html; charset=utf-8', self.app_bytes
            elif p == '/blank':
                ctype, out = 'text/html', b'<!doctype html><title>blank</title>'
            elif p == '/act' and method == 'POST':
                q = json.loads(body or b'{}')
                r = await self.act(q.get('uid', ''), q.get('cmd', ''), q.get('args') or [], q.get('opts') or {})
                out = json.dumps(r).encode()
            elif p == '/admin' and method == 'POST':
                if hdrs.get('x-sim-token') != self.token: status, out = 403, b'{"error":"admin needs the run token"}'
                else:
                    q = json.loads(body or b'{}')
                    try: r = await self.admin(q.get('cmd', ''), q)
                    except Exception as e:
                        import traceback; r = {'error': str(e)[:400], 'trace': traceback.format_exc()[-1500:]}
                    out = json.dumps(r, default=str).encode()
            elif p.startswith('/api/') or p.startswith('/.netlify/'):
                # The app's /api/ai (the Claude-backed assistant) and the hosted functions are not wired in the sim: the
                # assistant answers from its built-in logic. To run the real assistant, forward these here (README).
                status, out = 503, b'{"error":"not available in the simulation"}'
            else:
                status, out = 404, b'{"error":"not found"}'
            writer.write(f'HTTP/1.1 {status} OK\r\nContent-Type: {ctype}\r\nContent-Length: {len(out)}\r\nConnection: close\r\n\r\n'.encode() + out)
            await writer.drain()
        except Exception as e:
            try:
                msg = json.dumps({'ok': False, 'text': 'server error: ' + str(e)[:300]}).encode()
                writer.write(b'HTTP/1.1 500 ERR\r\nContent-Type: application/json\r\nContent-Length: ' + str(len(msg)).encode() + b'\r\nConnection: close\r\n\r\n' + msg)
                await writer.drain()
            except Exception: pass
        finally:
            try: writer.close()
            except Exception: pass

    async def main(self):
        self.app_bytes = open(DIST, 'rb').read()
        srv = await asyncio.start_server(self.handle, '127.0.0.1', self.port, limit=2 ** 24)
        self.port = srv.sockets[0].getsockname()[1]
        json.dump({'port': self.port, 'pid': os.getpid(), 'started': now_iso()}, open(os.path.join(self.dir, 'server.json'), 'w'))
        open(os.path.join(RUNS, '.current'), 'w').write(self.run)
        print(f'sim: run {self.run} on http://127.0.0.1:{self.port} (pid {os.getpid()}); starting the browser', flush=True)
        await self.start_browser()
        print(f"sim: ready · day {self.state['day']} · slot {self.state['slot']} · version {self.state['version']}", flush=True)
        async with srv:
            await self.stop.wait()
        await self.browser.close(); await self.pw.stop()
        try:   # only this server's own address card (a restarted server may already have written a new one)
            sj = os.path.join(self.dir, 'server.json')
            if json.load(open(sj)).get('pid') == os.getpid(): os.remove(sj)
        except Exception: pass


HELP = """sim/act <uid> <verb> ...   (you act only through your own screens)
  screen [--full] [--shot]     what is on your screen, controls numbered [n ...]
  scroll                       the next page of the same screen
  find "text"                  only the lines of your screen with that text, and the controls next to them
  tap <n>                      tap control n
  type <n> "text" [--enter]    type into field n
  pick <n> "option"            choose an option in select n
  upload <n> <file>            attach a file through control n (a file field or a button that opens the picker)
  photo <n>                    take a photo with control n (an invented picture)
  key Enter|Escape|Tab         press a key
  back                         close the open sheet, or go back a screen
  go "<menu label>"            open a menu entry by its label ("Purchasing" or "Purchasing > Deliveries")
  ask "question"               ask your assistant
  mail | mail sent | mail drafts | mail read <n> | mail reply <n> "text" | mail send "to" "subject" "body"
  mail senddraft <n>           send a draft the app saved to your mailbox (after `mail drafts`)
  call "<person>" "what was said"   a phone call: it goes in both diaries, nothing else
  news                         what happened around you (on site, calls you got) since your last turn"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', required=True)
    ap.add_argument('--port', type=int, default=0)
    ap.add_argument('--resume', action='store_true')
    ap.add_argument('--seed', type=int, default=0, help='the held-out events seed (default: from the run name)')
    ap.add_argument('--debug', action='store_true', help='developer only: allow simctl debug-eval (never for a run with agents)')
    a = ap.parse_args()
    if not re.match(r'^[\w.-]+$', a.run): raise SystemExit('run names are letters, digits, dot, dash, underscore')
    if not os.path.exists(DIST): raise SystemExit('build first: python3 build.py')
    seed = a.seed or int(hashlib.sha1(a.run.encode()).hexdigest()[:6], 16)
    os.makedirs(RUNS, exist_ok=True)
    sim = Sim(a.run, a.port, a.resume, seed, a.debug)
    asyncio.run(sim.main())


if __name__ == '__main__':
    main()
