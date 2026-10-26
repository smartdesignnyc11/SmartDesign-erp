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
DIST = os.environ.get('SIM_DIST') or os.path.join(ROOT, 'dist', 'smartdesigns_projects.html')  # SIM_DIST pins a run to one build across --resume
RUNS = os.path.join(HERE, 'runs')
PAGE_TOOLS = open(os.path.join(HERE, 'page_tools.js'), encoding='utf-8').read()
RUNTIME_JS = open(os.path.join(ROOT, 'tests', 'month_runtime.js'), encoding='utf-8').read()
CHECKS_JS = open(os.path.join(HERE, 'checks_p2.js'), encoding='utf-8').read()   # Pilot 2's checks, on top of the month's
SCRIPT_JS = open(os.path.join(HERE, 'script_p3.js'), encoding='utf-8').read()   # Pilot 3's scripted world actions (the roles that do not play)
# The working day (Pilot 3, Alan 10-25: "time per action counted against a realistic working day"): the minutes each
# verb takes a person, which move their clock; a turn may carry a budget of minutes as well as of actions.
MINUTES = {'tap': 0.5, 'type': 1.0, 'pick': 0.5, 'upload': 1.5, 'photo': 1.0, 'back': 0.25, 'go': 0.5, 'key': 0.25, 'ask': 3.0, 'screen': 0.5,
           'find': 0.5, 'scroll': 0.25, 'news': 1.0, 'call': 6.0, 'device': 0.5, 'help': 0.0, 'mail': 1.0}
MAIL_MINUTES = {'read': 3.0, 'send': 6.0, 'reply': 5.0, 'senddraft': 1.0}
# The live assistant (Pilot 3): /api/ is forwarded to the hosted copy's AI proxy only when a signed-in session's token is
# given at run time (SIM_AI_TOKEN, or SIM_AI_TOKEN_FILE re-read on every call so it can be refreshed); never in the repo.
AI_URL = os.environ.get('SIM_AI_URL', 'https://smartdesigns-erp.netlify.app').rstrip('/')
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
VERBS = {'do', 'screen', 'find', 'tap', 'type', 'pick', 'upload', 'photo', 'back', 'scroll', 'go', 'ask', 'mail', 'call', 'news', 'help', 'key', 'device'}
PAGE_CHARS = 3600
MUTATING = {'tap', 'type', 'pick', 'upload', 'photo', 'back', 'go', 'ask', 'key'}
CLICKS = {'tap', 'key', 'go', 'back'}   # the click check: where each of these landed against what its label promised
OVERHEAD = 10000   # tokens of fixed subagent overhead per model call (system prompt and tools): an assumption, see day_plan.md
# The page as a picture (Alan 10-26, "we only see 50% of the puzzle"): when an action lands on a screen the person has not
# seen this turn (a new view, record, tab or sheet), the server saves what the eye sees at the device's size (JPEG, quality
# 70) and the result ends with `Screen picture: <path>`; the expert looks at it before acting. One picture per new screen
# per turn. SIM_PICTURES=0 turns it off (the screen walk, which reads no pictures).
PICTURES = os.environ.get('SIM_PICTURES', '1') != '0'
PICTURE_CAP = int(os.environ.get('SIM_PICTURE_CAP', '8'))   # pictures per turn: each costs a model call to read (docs/IMPROVEMENT_LOOP.md, cost)
# The cap by the kind of turn (round one: the 8 ran out in the owner's page walk at 10:29). A journey turn keeps
# SIM_PICTURE_CAP; a page walk (`begin --kind pages`) sees every page it opens, up to SIM_PICTURE_CAP_PAGES; `--pictures N`
# sets one turn's cap outright.
PICTURE_CAPS = {'journey': PICTURE_CAP, 'pages': int(os.environ.get('SIM_PICTURE_CAP_PAGES', '30'))}


def picture_cap(t):
    t = t or {}
    if t.get('picture_cap'): return int(t['picture_cap'])
    return PICTURE_CAPS.get(t.get('kind') or 'journey', PICTURE_CAP)
PICTURE_TOKENS = {'phone': 437, 'desktop': 1719}   # measured on claude-opus-5-5 through /api/ai (sim/picture_cost.py), 10-26
PICTURE_CMDS = {'tap', 'go', 'back', 'key', 'screen', 'upload', 'photo', 'device', 'ask'}
FINGERPRINT_JS = """() => { const l = __SIM.landing(), w = __SIM.where(); return [l.view, l.title, l.sheet, w.cur, w.tab].join(' | '); }"""

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
        self.pictured = {}  # uid -> the screens pictured this turn (one picture per new fingerprint per turn)
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
        if rec.get('uid') in PEOPLE and 'device' not in rec: rec['device'] = self.device_of(rec['uid'])
        if rec.get('uid') in PEOPLE and 'clock' not in rec and self.state.get('day'): rec['clock'] = self.clock_str()
        with open(os.path.join(self.dir, 'actions.jsonl'), 'a') as f: f.write(json.dumps(rec, default=str) + '\n')

    def device_of(self, uid):
        """the device a person is on right now: their page's, or their role's own before they have a page"""
        d = self.device.get(uid)
        if d is None: d = (self.state.get('turn') or {}).get('phone') if (self.state.get('turn') or {}).get('uid') == uid else PEOPLE[uid][1]
        return 'phone' if d else 'desktop'

    def clock_str(self):
        hh, mm = map(int, SLOTS[self.state['slot']].split(':'))
        m = hh * 60 + mm + int(min(self.state.get('slot_min', 2 * self.state.get('slot_n', 0)), 600))
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

    async def shot(self, uid, path, jpeg=False):
        """A screenshot that keeps a phone a phone: Playwright's own screenshot puts the context's desktop viewport back,
        so phone pages are captured through CDP as they are laid out. jpeg: the picture an expert reads, at the device's
        own size in CSS pixels (390x844 on the phone, 1440x900 on the desktop), quality 70."""
        if self.device.get(uid):
            q = {'format': 'png'}
            if jpeg:
                vp = await self.pages[uid].evaluate("() => { const v = window.visualViewport; return [v ? v.pageLeft : scrollX, v ? v.pageTop : scrollY, innerWidth, innerHeight]; }")
                q = {'format': 'jpeg', 'quality': 70, 'clip': {'x': vp[0], 'y': vp[1], 'width': vp[2], 'height': vp[3], 'scale': 0.5}}   # the phone runs at 2x: half is its CSS size
            r = await self.cdp[uid].send('Page.captureScreenshot', q)
            open(path, 'wb').write(base64.b64decode(r['data']))
        elif jpeg:
            await self.pages[uid].screenshot(path=path, full_page=False, type='jpeg', quality=70)
        else:
            await self.pages[uid].screenshot(path=path, full_page=False)

    async def picture(self, uid, pg, t, out):
        """The page as a picture: a screen this person has not seen this turn is saved as the eye sees it and named at the
        end of the result. Never more than one picture per fingerprint (view, page heading, sheet, record, tab) per turn."""
        if not PICTURES or not out or not out.get('text'): return
        try: fp = await pg.evaluate(FINGERPRINT_JS) + (' | phone' if self.device.get(uid) else ' | desktop')   # the same page on the other device is a new screen to the eye
        except Exception: return
        seen = self.pictured.setdefault(uid, [])
        if fp in seen: return
        if t is not None and t.get('pictures', 0) >= picture_cap(t):
            out['text'] = (out.get('text') or '').rstrip('\n') + f'\n(No picture of this new screen: this turn\'s {picture_cap(t)} are used. `screen --shot` takes one if you need it.)'
            return
        seen.append(fp)
        d = os.path.join(self.dir, 'shots', uid); os.makedirs(d, exist_ok=True)
        p = os.path.join(d, f"{(self.state.get('day') or 'live')}_{self.clock_str().replace(':', '')}_{self.state['actions']}_{'phone' if self.device.get(uid) else 'desktop'}.jpg")
        try: await self.shot(uid, p, jpeg=True)
        except Exception as e:
            self.log({'uid': uid, 'cmd': 'picture', 'error': str(e)[:200]}); return
        out['text'] = (out.get('text') or '').rstrip('\n') + f'\nScreen picture: {p}'
        if t is not None: t['pictures'] = t.get('pictures', 0) + 1
        self.log({'uid': uid, 'cmd': 'picture', 'args': [fp[:160]], 'result': p, 'bytes': os.path.getsize(p)})

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
            await pg.evaluate(CHECKS_JS)
            await pg.evaluate(SCRIPT_JS)
            if self.state.get("world", {}).get("p2_time_base") is not None: await pg.evaluate("b => { __MS.p2base = b; }", self.state["world"]["p2_time_base"])
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
        # the time entries as the run begins (Pilot 2's clock checks count only what the run itself clocks)
        self.state["world"]["p2_time_base"] = await pg.evaluate("() => Object.fromEntries((DB.time || []).map(t => [t.id, t.out || '']))")
        await pg.evaluate("b => { __MS.p2base = b; }", self.state["world"]["p2_time_base"])
        await self.commit('__world')
        self.world.start()
        for u in PEOPLE: self.diary_init(u)
        self.save_state()

    def diary_size(self, uid):
        try: return os.path.getsize(os.path.join(self.dir, 'diary', f'{uid}.md'))
        except Exception: return 0

    # ------------------------------------------------------------------ cost (day_plan.md, "Measuring the cost")
    def cost_turn(self, t):
        """One line per turn in cost.jsonl: what the harness measured (calls, characters in and out, the prompt and the
        files it points to, the diary written) and the estimate it implies; `simctl cost` adds the conductor's real count."""
        m = t.get('meter') or {'calls': 0, 'req': 0, 'resp': 0, 'sizes': []}
        pr = t.get('prompt') or {'chars': 0, 'reads': 0}
        diary = max(0, self.diary_size(t['uid']) - (t.get('diary0') or 0))
        ctx = (pr['chars'] + pr['reads']) / 4; processed = 0.0
        steps = [[0, 0]] * 2 + m['sizes'] + [[diary, 0]]   # the reads at the start and the diary write at the end are calls too
        for q, r in steps:
            processed += OVERHEAD + ctx; ctx += (q + r) / 4 + 150   # 150: the model's own words around each call (assumed)
        rec = {'day': t.get('day') or self.state['day'], 'slot': t['slot'], 'uid': t['uid'], 'device': t.get('device'), 'cap': t['cap'], 'actions': t['used'],
               'calls': m['calls'], 'pictures': t.get('pictures', 0), 'picture_tokens': m.get('picture_tokens', 0), 'prompt_chars': pr['chars'], 'read_chars': pr['reads'], 'sent_chars': m['req'], 'result_chars': m['resp'], 'diary_chars': diary,
               'est_new_context': round(ctx), 'est_processed': round(processed), 'est_output': round((m['req'] + diary) / 4 + 150 * len(steps)),
               'measured': None, 'started': t.get('started'), 'ended': now_iso()}
        with open(os.path.join(self.dir, 'cost.jsonl'), 'a') as f: f.write(json.dumps(rec) + '\n')
        self.cost_write()

    def cost_measured(self, a):
        p = os.path.join(self.dir, 'cost.jsonl')
        L = [json.loads(l) for l in open(p)] if os.path.exists(p) else []
        who = a.get('uid') or a.get('label') or ''
        meas = {k: a[k] for k in ('tokens', 'tool_uses', 'ms', 'input', 'output', 'cache_read') if a.get(k) is not None}
        hit = next((r for r in reversed(L) if r.get('uid') == who and not r.get('measured')), None)
        if hit is None:   # a workshop step or anything else the conductor ran: a line of its own
            hit = {'day': self.state['day'], 'slot': a.get('slot') or 'after', 'uid': who, 'device': '', 'calls': 0, 'measured': None, 'ended': now_iso()}; L.append(hit)
        hit['measured'] = meas
        open(p, 'w').write(''.join(json.dumps(r) + '\n' for r in L))
        self.cost_write()
        return {'recorded': who, 'measured': meas, 'day': hit['day'], 'slot': hit['slot']}

    def cost_write(self):
        """cost_<day>.json and cost.md: per day, the turns, the measured tokens (where the conductor gave them) and the
        harness's estimate, so day 1's real cost can be reported before days 2 and 3 run."""
        p = os.path.join(self.dir, 'cost.jsonl')
        L = [json.loads(l) for l in open(p)] if os.path.exists(p) else []
        days = {}
        for r in L:
            D = days.setdefault(r['day'], {'turns': 0, 'calls': 0, 'measured_turns': 0, 'measured_tokens': 0, 'measured_tool_uses': 0, 'measured_ms': 0,
                                            'est_processed': 0, 'est_new_context': 0, 'est_output': 0, 'by_slot': {}})
            D['turns'] += 1; D['calls'] += r.get('calls') or 0
            for k in ('est_processed', 'est_new_context', 'est_output'): D[k] += r.get(k) or 0
            mm = r.get('measured') or {}
            if mm:
                D['measured_turns'] += 1; D['measured_tokens'] += int(mm.get('tokens') or 0)
                D['measured_tool_uses'] += int(mm.get('tool_uses') or 0); D['measured_ms'] += int(mm.get('ms') or 0)
            S = D['by_slot'].setdefault(r['slot'], {'turns': 0, 'measured_tokens': 0, 'est_processed': 0})
            S['turns'] += 1; S['measured_tokens'] += int(mm.get('tokens') or 0); S['est_processed'] += r.get('est_processed') or 0
        for d, D in days.items(): json.dump(D, open(os.path.join(self.dir, f'cost_{d}.json'), 'w'), indent=1)
        M = ['# Cost of the run, per day\n', "Measured = the token counts the conductor copied from each subagent's result (`simctl cost`). "
             "Estimated = the harness's own count (calls, characters in and out) with a fixed 10k-token overhead per call assumed. "
             'Read the measured column; the estimate stands in for turns with no measurement.\n',
             '| Day | Turns | Calls | Measured turns | Measured tokens | Tool uses | Agent minutes | Est. processed input | Est. new context | Est. output |',
             '|---|---|---|---|---|---|---|---|---|---|']
        for d, D in sorted(days.items()):
            M.append(f"| {d} | {D['turns']} | {D['calls']} | {D['measured_turns']} | {D['measured_tokens']:,} | {D['measured_tool_uses']} | {round(D['measured_ms'] / 60000)} | "
                     f"{D['est_processed']:,} | {D['est_new_context']:,} | {D['est_output']:,} |")
        M.append('\n| Day | Slot | Turns | Measured tokens | Est. processed input |\n|---|---|---|---|---|')
        for d, D in sorted(days.items()):
            for sl, S in D['by_slot'].items(): M.append(f"| {d} | {sl} | {S['turns']} | {S['measured_tokens']:,} | {S['est_processed']:,} |")
        open(os.path.join(self.dir, 'cost.md'), 'w').write('\n'.join(M) + '\n')

    def diary_init(self, uid):
        p = os.path.join(self.dir, 'diary', f'{uid}.md')
        if not os.path.exists(p):
            open(p, 'w').write(f"# {PEOPLE[uid][2]}: work diary ({PEOPLE[uid][0]})\n\nKept by {PEOPLE[uid][2]}. Read it each morning; write it at the end of each day.\n\n")

    def said_line(self, uid, text):
        """Memory between turns (Alan 10-26): what a person said and promised to whom (mail they sent, calls both ways) is
        kept in their notes, files/<uid>/said.md, beside news.md (what they were told), so the next turn (a fresh agent)
        knows what it owes. One line each, with the day and the time."""
        if uid not in PEOPLE: return
        fd = os.path.join(self.dir, 'files', uid); os.makedirs(fd, exist_ok=True)
        with open(os.path.join(fd, 'said.md'), 'a', encoding='utf-8') as f:
            f.write(f"- {self.state.get('day') or ''} {self.clock_str()}: " + re.sub(r'\s+', ' ', text).strip()[:600] + '\n')

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
                out = {'ok': False, 'text': f"your turn is over: {t['used']} actions used of {t['cap']}. Write your diary and stop."}
            elif t and t.get('min_cap') and t.get('minutes', 0) >= t['min_cap']:
                out = {'ok': False, 'text': f"your working time for this part of the day is used ({round(t['minutes'])} of {round(t['min_cap'])} minutes). Write your diary and stop."}
            elif cmd == 'do': out = await self.do_batch(uid, args, opts, t)
            else: out = await self._one(uid, cmd, args, opts, t)
            self.meter(t, args, out)
            return out

    def meter(self, t, args, out):
        """The cost of a turn as the harness sees it: each call the agent made, what it sent and what came back
        (every result is new context the model reads on every later call). The conductor adds the real token count."""
        if not t: return
        m = t.setdefault('meter', {'calls': 0, 'req': 0, 'resp': 0, 'sizes': []})
        q, r = len(json.dumps(args)), len((out or {}).get('text') or '')
        m['calls'] += 1; m['req'] += q; m['resp'] += r; m['sizes'].append([q, r])
        pic = re.search(r'Screen picture: \S+_(phone|desktop)\.jpg', (out or {}).get('text') or '')
        if pic:   # the expert reads the picture: one more model call, and the picture's tokens stay in the context after it
            m['sizes'].append([0, PICTURE_TOKENS[pic.group(1)] * 4]); m['picture_tokens'] = m.get('picture_tokens', 0) + PICTURE_TOKENS[pic.group(1)]

    async def _one(self, uid, cmd, args, opts, t):
        '''one action, start to finish: fresh page, act, find-it-again, save, log (the lock is held by the caller)'''
        if t: t['used'] += 1
        self.state['actions'] += 1
        if cmd in MUTATING: self.state['slot_n'] = self.state.get('slot_n', 0) + 1
        mins = MAIL_MINUTES.get(str((args or ['list'])[0]).lower(), 1.0) if cmd == 'mail' else MINUTES.get(cmd, 0.5)
        if t: t['minutes'] = t.get('minutes', 0.0) + mins
        self.state['slot_min'] = self.state.get('slot_min', 0.0) + mins
        await self.set_clock()
        if cmd in ('news', 'call'):
            out = await getattr(self, 'v_' + cmd)(uid, None, args, opts)
            if opts.get('why'): self.log({'uid': uid, 'cmd': 'why', 'args': [cmd], 'why': opts['why'][:300]})
            await self.interrupt_check(uid, t, out, None)
            self.save_state(); return out
        t_act = time.time()
        pg, reloaded = await self.fresh(uid)
        self.last_dialog = ''
        n_toast = await pg.evaluate("__SIM.toasts.length"); n_err = len(self.errs[uid])
        before = await pg.evaluate("__SIM.keys()") if cmd in MUTATING else None
        title0 = await pg.evaluate("__SIM.title()")
        land0 = await pg.evaluate("__SIM.landing()") if cmd in CLICKS else None
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
                if nm.get('mine') is False: continue   # another person's record (synced in on the live site), not this person's own
                seen = await pg.evaluate("n => __SIM.onScreen(n)", nm['name'])
                creates.append({'key': k, 'name': nm['name'], 'on_screen': seen['on'], 'in_toast': seen['toast']})
                if not seen['on']:
                    self.state['fia_pending'].setdefault(uid, []).append({'key': k, 'name': nm['name'], 'day': self.state['day']})
        changed = await self.commit(uid)
        await pg.evaluate("window.__simActive = true")   # still this person's page until someone else acts
        land = {'from': land0, 'to': await pg.evaluate("__SIM.landing()")} if land0 is not None else None
        if self.last_dialog: out['text'] = self.last_dialog + '\n' + out.get('text', '')
        if toasts and cmd not in ('screen', 'scroll'): out['text'] = 'Toast: ' + ' / '.join(toasts[-2:]) + '\n' + out.get('text', '')
        if errs: out['text'] += '\n(the app reported an error: ' + errs[-1][:160] + ')'
        self.log({'uid': uid, 'cmd': cmd, 'args': args, 'screen': title0, 'after': await pg.evaluate("__SIM.title()"), 'control': out.get('control'),
                  'kind': out.get('kind'), 'ok': out.get('ok'), 'result': (out.get('text') or '')[:300] if cmd not in ('screen', 'scroll') else out.get('summary', ''),
                  'toasts': toasts, 'errors': errs, 'creates': creates, 'changed': changed, 'reloaded': reloaded, 'clock': self.clock_str(), 'ms': int((time.time() - t_act) * 1000),
                  'device': 'phone' if self.device.get(uid) else 'desktop', 'form': form if creates else None,
                  'turn_used': (t or {}).get('used'), 'land': land, 'where': await pg.evaluate("__SIM.where()"), 'why': (opts.get('why') or '')[:300] or None,
                  'minutes': mins, 'turn_minutes': round((t or {}).get('minutes', 0), 1)})
        for c in creates:
            if not c['on_screen']: out['text'] += f"\n(find it again: you just created \"{c['name'][:60]}\"; it is {'only in the toast' if c['in_toast'] else 'not on your screen'})"
        if not opts.get('quiet') and (cmd in PICTURE_CMDS or (cmd == 'type' and opts.get('enter'))): await self.picture(uid, pg, t, out)
        await self.interrupt_check(uid, t, out, pg)
        self.save_state()
        return out

    async def interrupt_check(self, uid, t, out, pg):
        """Pilot 3: an interruption from the book (a call, a client's mail) cuts into the turn once the person has worked
        its minutes into it (or is near the end of the turn). It is put in front of the next result, in their news and,
        for a mail, in their mailbox; they handle it and come back to what they were doing."""
        Q = (self.state.get('interrupts') or {}).get(uid) or []
        if not t or not Q: return
        x = next((q for q in Q if t.get('minutes', 0) >= float(q.get('after_min') or 0) or t['used'] >= t['cap'] - 4), None)
        if not x: return
        Q.remove(x)
        if x.get('mail') and pg is not None and self.has_box(uid):
            m = x['mail']; at = int(datetime.fromisoformat(f"{self.state['day']}T{self.clock_str()}:00{TZ}").timestamp() * 1000)
            await pg.evaluate("([u, m]) => __SIM.mbPut(u, m)", [uid, {'id': f"wm_{x['id']}_{uid}", 'threadId': f"wmt_{x['id']}", 'labelIds': ['INBOX', 'UNREAD'], 'internalDate': at,
                                                                 'headers': {'From': m['from'], 'To': ', '.join(m['to']), 'Cc': '', 'Subject': m['subject'], 'Date': ''}, 'body': m['text'], 'attachments': []}])
        out['text'] = (f"INTERRUPTION ({x.get('via', 'call')} from {x.get('from', '')}): {x['text']}\n(Deal with it the way you would, then go back to what you were doing.)\n" + (out.get('text') or ''))
        out['interrupt'] = x['id']
        self.state['news'].setdefault(uid, []).append(f"{self.state['day']} {self.clock_str()}: {x['text']}")
        self.world.st.setdefault('interrupts_done', {})[x['id']] = [self.state['day'], self.state['slot'], self.clock_str()]
        self.log({'uid': uid, 'cmd': 'interrupt', 'args': [x['id']], 'result': x['text'][:200], 'turn_minutes': round(t.get('minutes', 0), 1)})

    BATCHABLE = ('tap', 'type', 'pick', 'key', 'go', 'find', 'scroll', 'back', 'upload', 'photo')
    VALID = re.compile(r"\b(required|missing|cannot|can't|must|invalid|enter a|choose a|pick a|not allowed|refused|before you)\b", re.I)

    async def do_batch(self, uid, args, opts, t):
        '''`do "step; step; ..."`: up to 8 steps in one call. Each step is a real action (logged, saved, counted against
        the turn's cap). It stops at the first error, validation stop or dialog, or a numbered target that is no longer
        the control it was. A `find` step is a check: the batch stops if the text is not on the screen. One result.'''
        import shlex
        raw = ' '.join(args)
        steps = [x.strip() for x in re.split(r';(?=(?:[^"]*"[^"]*")*[^"]*$)', raw) if x.strip()]
        if not steps: return {'ok': False, 'text': 'do what? e.g. do \'type 3 "8"; pick "Unit" "sheet"; tap "Save"\''}
        if len(steps) > 8: return {'ok': False, 'text': f'{len(steps)} steps: at most 8 in one do'}
        lines, toasts, stop, done = [], [], '', 0
        for i, st in enumerate(steps, 1):
            try: parts = shlex.split(st)
            except ValueError as e: stop = f'step {i} "{st}": {e}'; break
            verb, sargs = parts[0].lower(), parts[1:]
            sopts = {'quiet': True}
            if '--enter' in sargs: sargs.remove('--enter'); sopts['enter'] = True
            if verb not in self.BATCHABLE: stop = f'step {i}: "{verb}" cannot be batched (only {", ".join(self.BATCHABLE)})'; break
            if t and t['used'] >= t['cap']: stop = f"step {i}: your turn is over ({t['used']} of {t['cap']} actions)"; break
            if verb == 'find':
                pg, _ = await self.fresh(uid)
                txt = (await pg.evaluate("__SIM.visibleText()")).lower()
                if sargs and sargs[0].lower() not in txt: stop = f'step {i}: "{sargs[0]}" is not on the screen'; break
                lines.append(f'{i}. find "{sargs[0] if sargs else ""}": on the screen'); done += 1; continue
            if verb == 'scroll': lines.append(f'{i}. scroll: (the final screen shows the page)'); done += 1; continue
            n_dialog = len(self.errs.get('dialogs', []))
            out = await self._one(uid, verb, sargs, sopts, t)
            if out.get('interrupt'):
                intr = '\n'.join((out.get('text') or '').split('\n')[:2])
                lines.append(f'{i}. {verb} done'); done += 1; stop = f'step {i}: you were interrupted'; lines.insert(0, intr); break
            first = (out.get('text') or '').split('\n')
            tl = [x[7:] for x in first if x.startswith('Toast: ')]
            toasts += tl
            msg = next((x for x in first if x and not x.startswith('Toast: ')), '') or verb
            lines.append(f'{i}. {msg[:140]}')
            if out.get('ok') is False: stop = f'step {i} stopped: {msg[:200]}'; break
            done += 1
            if any(self.VALID.search(x) for x in tl): stop = f'step {i}: the app said "{tl[-1][:160]}"'; break
            if len(self.errs.get('dialogs', [])) > n_dialog: stop = f'step {i}: the app asked a question ({self.errs["dialogs"][-1][:160]})'; break
            if '(the app reported an error' in (out.get('text') or ''): stop = f'step {i}: the app reported an error'; break
        pg, _ = await self.fresh(uid)
        fin = await self.v_find(uid, pg, [opts['find']], {}) if opts.get('find') else await self.render_screen(uid, pg, full=opts.get('full'), shot=opts.get('shot'), marks=opts.get('marks'))
        head = f"do: {done} of {len(steps)} steps" + (f" · STOPPED: {stop}" if stop else ' · all done')
        txt = '\n'.join([head] + lines + ([f"Toasts: {' / '.join(dict.fromkeys(toasts))}"] if toasts else []) + ['', fin['text']])
        self.log({'uid': uid, 'cmd': 'do', 'args': steps, 'ok': not stop, 'result': head[:300], 'why': (opts.get('why') or '')[:300] or None})
        res = {'ok': not stop, 'text': txt}
        await self.picture(uid, pg, t, res)
        self.save_state()
        return res

    def has_box(self, uid): return uid in STAFF_MAIL

    async def render_screen(self, uid, pg, full=False, shot=False, marks=False):
        S = await pg.evaluate("m => __SIM.screen(m)", bool(marks))
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
        return await self.render_screen(uid, pg, full=opts.get('full'), shot=opts.get('shot'), marks=opts.get('marks'))

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

    async def _resolve(self, pg, n, want='action'):
        """A control by its number on the last screen, or by the label the person reads ("Save Change Order"); the
        number must still be the same control, the label must name exactly one. Returns (sig, error, selector, key)."""
        if str(n).strip().isdigit():
            n = int(n)
            r = await pg.evaluate("n => __SIM.resolve(n)", n)
            if not r['ok']: return None, {'ok': False, 'text': r['why']}, None, None
            return r['sig'], None, f'[data-simn="{n}"]', n
        r = await pg.evaluate("([l, w]) => __SIM.markByLabel(l, w)", [str(n), want])
        if not r['ok'] and want == 'action' and r['why'].startswith('no '):   # a checkbox or a tick is tapped too
            r2 = await pg.evaluate("([l, w]) => __SIM.markByLabel(l, w)", [str(n), 'field'])
            if r2['ok'] and r2['sig']['k'] == 'check': r = r2
        if not r['ok']: return None, {'ok': False, 'text': r['why']}, None, None
        return r['sig'], None, '[data-simlab="1"]', '[data-simlab="1"]'

    async def _after(self, uid, pg, opts):
        """the screen after an action, unless it is a step inside a batch (the batch shows the screen once, at the end)"""
        if opts.get('quiet'): return {'ok': True, 'text': ''}
        return await self.render_screen(uid, pg, full=opts.get('full'), shot=opts.get('shot'), marks=opts.get('marks'))

    async def v_tap(self, uid, pg, args, opts):
        if not args: return {'ok': False, 'text': 'tap which number?'}
        sig, err, sel, key = await self._resolve(pg, args[0])
        if err: return err
        loc = pg.locator(sel).first
        forced = ''
        try: await loc.click(timeout=4000)
        except Exception:
            # a click that landed late (the control was covered for a few seconds, then tapped) has already run and its
            # control may be gone: the fallback must not wait 30 seconds for it, nor tap it a second time (cycle walk J1b)
            try: await loc.evaluate("e => e.click()", timeout=2500); forced = ' (it was covered; tapped through)'
            except Exception: forced = ' (the tap took over 4 seconds to land: something covered the control, or it went away)'
        await self.settle(pg, 400)
        out = await self._after(uid, pg, opts)
        out['control'] = sig['label']; out['kind'] = sig['k']
        out['text'] = f"tapped {args[0]} \"{sig['label'][:60]}\"{forced}\n" + out['text']
        return out

    async def v_type(self, uid, pg, args, opts):
        if len(args) < 2: return {'ok': False, 'text': 'usage: type <n> "text"'}
        sig, err, sel, key = await self._resolve(pg, args[0], 'field')
        if err: return err
        text = args[1]
        if re.match(r'\s*javascript:', text, re.I): return {'ok': False, 'text': 'refused: that is code, not something a person types'}
        loc = pg.locator(sel).first
        info = await pg.evaluate("n => __SIM.fieldInfo(n)", key)
        if info and info['kind'] in ('select', 'check', 'file'): return {'ok': False, 'text': f"{args[0]} is a {info['kind']}: use {'pick' if info['kind'] == 'select' else 'tap' if info['kind'] == 'check' else 'upload'}"}
        try: await loc.fill(text, timeout=4000)
        except Exception:
            await loc.click(timeout=3000); await pg.keyboard.type(text)
        try: await loc.dispatch_event('change')
        except Exception: pass
        if opts.get('enter'):
            await loc.press('Enter'); await self.settle(pg, 400)
            out = await self._after(uid, pg, opts)
            out['text'] = f"typed into {args[0]} \"{sig['label'][:50]}\" and pressed Enter\n" + out['text']
            out['control'] = sig['label']; out['kind'] = 'input'
            return out
        await self.settle(pg, 150)
        return {'ok': True, 'text': f"typed into {args[0]} \"{sig['label'][:50]}\"", 'control': sig['label'], 'kind': 'input'}

    async def v_key(self, uid, pg, args, opts):
        k = (args or ['Enter'])[0]
        if k not in ('Enter', 'Escape', 'Tab'): return {'ok': False, 'text': 'key: Enter, Escape or Tab'}
        await pg.keyboard.press(k); await self.settle(pg, 400)
        out = await self._after(uid, pg, opts); out['text'] = f'pressed {k}\n' + out['text']; out['control'] = k
        return out

    async def v_pick(self, uid, pg, args, opts):
        if len(args) < 2: return {'ok': False, 'text': 'usage: pick <n> "option"'}
        sig, err, sel, key = await self._resolve(pg, args[0], 'field')
        if err: return err
        r = await pg.evaluate("([n, o]) => __SIM.pick(n, o)", [key, args[1]])
        if not r['ok']: return {'ok': False, 'text': r['why']}
        await pg.locator(sel).first.select_option(r['value'], timeout=4000)
        await self.settle(pg, 250)
        return {'ok': True, 'text': f"picked \"{r['text']}\" in {args[0]} \"{sig['label'][:50]}\"", 'control': sig['label'], 'kind': 'select'}

    async def _upload(self, uid, pg, n, path, sig, opts, sel=None):
        if not os.path.isfile(path): return {'ok': False, 'text': f'no such file: {path}'}
        loc = pg.locator(sel or f'[data-simn="{int(n)}"]').first
        how = ''
        if sig['k'] == 'file':
            await loc.set_input_files(path); how = 'set on the file field'
        else:
            try:
                async with pg.expect_file_chooser(timeout=3000) as fc:
                    await loc.click(timeout=3000)
                ch = await fc.value; await ch.set_files(path); how = 'chosen in the file picker'
            except Exception:
                if await pg.evaluate("n => __SIM.fileInputNear(n)", n if isinstance(n, str) and not n.isdigit() else int(n)):
                    await pg.locator('[data-simfile="1"]').first.set_input_files(path); how = 'put in the file field next to it'
                else: return {'ok': False, 'text': f'{n} does not open a file picker'}
        await self.settle(pg, 700)
        out = await self._after(uid, pg, opts)
        out['text'] = f"uploaded {os.path.basename(path)} ({how})\n" + out['text']; out['control'] = sig['label']; out['kind'] = 'upload'
        return out

    async def v_upload(self, uid, pg, args, opts):
        if len(args) < 2: return {'ok': False, 'text': 'usage: upload <n> <file>'}
        sig, err, sel, key = await self._resolve(pg, args[0], 'field' if not str(args[0]).isdigit() else 'action')
        if err and not str(args[0]).isdigit(): sig, err, sel, key = await self._resolve(pg, args[0])
        if err: return err
        return await self._upload(uid, pg, key if isinstance(key, str) else args[0], os.path.abspath(args[1]), sig, opts, sel)

    async def v_photo(self, uid, pg, args, opts):
        if not args: return {'ok': False, 'text': 'usage: photo <n>'}
        sig, err, sel, key = await self._resolve(pg, args[0])
        if err: return err
        d = os.path.join(self.dir, 'files', uid); os.makedirs(d, exist_ok=True)
        p = os.path.join(d, f"IMG_{self.state['day'].replace('-', '')}_{self.clock_str().replace(':', '')}_{self.state['actions']}.png")
        open(p, 'wb').write(png_bytes(f"{self.state['seed']}:{uid}:{self.state['actions']}"))
        return await self._upload(uid, pg, key if isinstance(key, str) else args[0], p, sig, opts, sel)

    async def v_back(self, uid, pg, args, opts):
        r = await pg.evaluate("__SIM.closeTop()")
        if not r:
            # the app's own Back first: the previous screen inside a page (a document, a tab), as a person's back does
            if await pg.evaluate("() => typeof appBack === 'function' && appBack()"):
                await self.settle(pg, 400); r = 'back to the previous screen'
        if not r:
            hist = self.state['people'].get(uid, {}).get('hist', [])
            if len(hist) >= 2:
                hist.pop(); prev = hist[-1]
                await pg.evaluate("v => { if ((ROLE_VIEWS[role()] || []).includes(v)) { view = v; render(); } }", prev)
                r = 'back to the previous screen'
            else: r = 'nothing to go back to'
        await self.settle(pg, 300)
        out = await self._after(uid, pg, opts); out['text'] = r + '\n' + out['text']; out['control'] = 'back'
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
        S2 = await pg.evaluate("({ view: typeof view !== 'undefined' ? view : '' })")
        self.state['people'].setdefault(uid, {})['view'] = S2['view']
        out = await self._after(uid, pg, opts)
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
            # the labelled Ask button (p2nav, 10-25) in the header or in the open sheet's header: the way a person opens it
            if await pg.evaluate("() => { const B = [...document.querySelectorAll('[data-p2nask], .tb-ask, #tb-ask')].filter(b => b.getClientRects().length); const b = B.reverse().find(x => { const r = x.getBoundingClientRect(); const t = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2); return t && (t === x || x.contains(t)) }); if (b) { b.click(); return true } return false }"):
                await self.settle(pg, 500)
                has = await pg.evaluate("() => { const e = document.querySelector('#pa-in'); return !!(e && e.getClientRects().length) }")
        if not has:
            for lab in ('Ask', 'Assistant'):
                r = await pg.evaluate("l => __SIM.go(l)", lab)
                if r['ok']:
                    await self.settle(pg, 400)
                    has = await pg.evaluate("() => { const e = document.querySelector('#pa-in'); return !!(e && e.getClientRects().length) }")
                    if has: break
        if not has:
            # the header's Ask is an icon button (#tb-ask) with no text, so the menu search cannot see it
            if await pg.evaluate("() => { const b = document.getElementById('tb-ask'); if (b && b.getClientRects().length) { b.click(); return true } return false }"):
                await self.settle(pg, 400)
                has = await pg.evaluate("() => { const e = document.querySelector('#pa-in'); return !!(e && e.getClientRects().length) }")
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
            self.said_line(uid, f"you sent the app's draft to {r['to'] or '(nobody)'}: \"{r['subject']}\"")
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
                cc = ''
                if opts.get('all'):   # reply to all: everyone on the To and Cc but me
                    mine = (me.split('<')[-1].strip('> ').lower() if me else '#')
                    others = [x.strip() for x in re.split(r',\s*(?=[^,]*@)', f"{m.get('to') or ''},{m.get('cc') or ''}") if x.strip() and mine not in x.lower() and x.strip() not in to]
                    cc = ', '.join(dict.fromkeys(others))
            else:
                if len(args) < 4: return {'ok': False, 'text': 'usage: mail send "to, to" "subject" "body" [--cc "name, name"]'}
                to, bad = self.addrs(args[1])
                cc, bad2 = self.addrs(opts.get('cc') or '')
                if bad or bad2: return {'ok': False, 'text': f'no address for {", ".join(chr(34) + b + chr(34) for b in bad + bad2)}; use a name from your contacts or an email'}
                if not to: return {'ok': False, 'text': 'send it to whom?'}
                subj, body, thread = args[2], args[3], ''
            if sub == 'send' or not opts.get('all'): cc = cc if sub == 'send' else ''
            r = await self.send_mail(uid, pg, to, subj, body, thread, cc)
            return {'ok': True, 'text': f'sent to {to}' + (f' (cc {cc})' if cc else '') + f': {subj}' + (f'\n{r}' if r else ''), 'control': 'mail ' + sub, 'kind': 'send'}
        return {'ok': False, 'text': 'mail | mail sent | mail drafts | mail read <n> | mail senddraft <n> | mail reply <n> "text" | mail send "to" "subject" "body"'}

    def addrs(self, s):
        """several people in one field ("Chen, Billing, wren.ashby@example.com"): each resolved; the ones with no address"""
        out, bad = [], []
        for x in [y.strip() for y in re.split(r'[,;]\s*(?![^<]*>)', s or '') if y.strip()]:
            a = self.world.resolve_addr(x)
            (out.append(a) if a else bad.append(x))
        return ', '.join(dict.fromkeys(out)), bad

    def _mail_id(self, uid, a):
        try: return self.mail_map.get(uid, [])[int(a[0]) - 1]
        except Exception: return None

    def addr_of(self, uid):
        if uid in self.world.staff_addr: return self.world.staff_addr[uid]
        return self.world.agent_addr.get(uid, '')

    async def send_mail(self, uid, pg, to, subject, body, thread, cc=''):
        at = int(datetime.fromisoformat(f"{self.state['day']}T{self.clock_str()}:00{TZ}").timestamp() * 1000)
        mid = f"sim_{uid}_{self.state['actions']}"
        frm = self.addr_of(uid)
        msg = {'id': mid, 'threadId': thread or f'simt_{mid}', 'labelIds': ['SENT'], 'internalDate': at,
               'headers': {'From': frm, 'To': to, 'Cc': cc, 'Subject': subject, 'Date': datetime.fromtimestamp(at / 1000).strftime('%a, %d %b %Y %H:%M:%S')},
               'body': body, 'attachments': []}
        self.said_line(uid, f'you mailed {to}' + (f' (cc {cc})' if cc else '') + f': "{subject}": {body}')
        if self.has_box(uid):
            await pg.evaluate("([u, m]) => __SIM.mbPut(u, m)", [uid, msg])
            self.state['sent_seen'].setdefault(mid, {'by': uid, 'how': 'person'})
        else:
            self.ext_box(uid).append({'id': mid, 'from': frm, 'to': to, 'cc': cc, 'subject': subject, 'body': body, 'at': at, 'thread': msg['threadId'], 'sent': True, 'att': []})
        return await self.post_office(pg, [{'uid': uid, 'id': mid, 'from': frm, 'to': to, 'cc': cc, 'subject': subject, 'body': body, 'at': at, 'thread': msg['threadId'], 'att': []}])

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
                    self.ext_box(who).append({'id': f"{m['id']}_to_{who}", 'from': m['from'], 'to': m['to'], 'cc': m.get('cc', ''), 'subject': m['subject'], 'body': m['body'],
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
            self.said_line(who, f'{PEOPLE[uid][2]} called you and said: "{said}"')
            self.state['news'].setdefault(who, []).append(f"{when} call from {PEOPLE[uid][2]}: \"{said}\"")
            reply = f'{PEOPLE[who][2]} heard it. It is in both diaries; it is a promise only if someone logs it in the app.'
        else:
            reply = self.world.on_call(uid, who, said)
            self.diary_line(uid, f"  they said: \"{reply}\"")
        self.said_line(uid, f'you called {PEOPLE[who][2] if who in PEOPLE else who} and said: "{said}"; they said: "{reply}"')
        self.log({'uid': uid, 'cmd': 'call', 'args': args, 'result': reply[:200]})
        return {'ok': True, 'text': reply, 'kind': 'call', 'control': 'call'}

    async def v_device(self, uid, pg, args, opts):
        """`device` says which device you are on; `device phone|desktop` picks up the other one, when this turn allows it
        (the day plan says so: an office person checking the phone, a field person looking at the desktop once)."""
        now = self.device_of(uid)
        want = (args[0].lower() if args else '').strip()
        t = self.state.get('turn') or {}
        if not want: return {'ok': True, 'text': f'You are on your {now}.' + (' This turn you may switch: `device phone` or `device desktop`.' if t.get('switch') else '')}
        if want not in ('phone', 'desktop'): return {'ok': False, 'text': 'device phone | device desktop'}
        if want == now: return {'ok': True, 'text': f'You are already on your {now}.'}
        if not t.get('switch'): return {'ok': False, 'text': f'This turn is on your {now}; the day plan does not have you switch devices now.'}
        await self.set_device(uid, want == 'phone')
        await pg.evaluate("() => { try { render(); } catch (e) {} }"); await self.settle(pg, 500)
        out = await self._after(uid, pg, opts)
        out['text'] = f'You put down your {now} and picked up your {want}. Same company, same login.\n' + out['text']
        out['control'] = 'device ' + want; out['kind'] = 'device'
        return out

    async def v_news(self, uid, pg, args, opts):
        items = self.state['news'].pop(uid, [])
        self.log({'uid': uid, 'cmd': 'news', 'result': f'{len(items)} items'})
        # a person remembers what they heard: every item is kept in their notes (files/<uid>/news.md), so a later turn
        # (a fresh agent) can read it again; Pilot 3 lost the owner's takeoff between turns without this
        if items:
            fd = os.path.join(self.dir, 'files', uid); os.makedirs(fd, exist_ok=True)
            with open(os.path.join(fd, 'news.md'), 'a', encoding='utf-8') as f:
                f.write(f"\n## {self.state['day']} {self.state['slot']} {self.clock_str()}\n" + '\n'.join('- ' + x for x in items) + '\n')
        note = f"\n(Everything you have heard is kept in your notes: {os.path.join(self.dir, 'files', uid, 'news.md')})"
        return {'ok': True, 'text': (('What happened around you since your last turn:\n' + '\n'.join('- ' + x for x in items)) if items else 'Nothing new around you.') + note}

    # ------------------------------------------------------------------ the main session's controls
    async def admin(self, cmd, a):
        async with self.lock:
            if cmd == 'status':
                return {'run': self.run, 'day': self.state['day'], 'slot': self.state['slot'], 'clock': self.clock_str(), 'version': self.state['version'],
                        'turn': self.state['turn'], 'actions': self.state['actions'], 'days': self.world.days, 'days_done': self.state['days_done']}
            if cmd == 'slot':
                if a.get('slot') not in SLOTS: return {'error': 'slot is one of ' + ', '.join(SLOTS)}
                self.state['slot'] = a['slot']; self.state['slot_n'] = 0; self.state['slot_min'] = 0; self.save_state(); return {'slot': a['slot'], 'clock': self.clock_str()}
            if cmd == 'begin_turn':
                uid = a['uid']
                if uid not in PEOPLE: return {'error': 'unknown person'}
                if a.get('slot'): self.state['slot'] = a['slot']; self.state['slot_n'] = 0; self.state['slot_min'] = 0
                # the device: the day plan's for this person and slot (phone | desktop), else the role's own; `switch` lets
                # the person pick up the other device during the turn (`act <uid> device desktop`)
                dev = (a.get('device') or '').lower()
                phone = (dev == 'phone') if dev in ('phone', 'desktop') else (bool(a.get('phone')) or PEOPLE[uid][1])
                self.state['turn'] = {'uid': uid, 'cap': int(a.get('cap') or 25), 'used': 0, 'minutes': 0.0, 'min_cap': float(a.get('minutes') or 0), 'slot': self.state['slot'], 'started': now_iso(), 'phone': phone,
                                      'device': 'phone' if phone else 'desktop', 'switch': bool(a.get('switch')), 'day': self.state['day'],
                                      'diary0': self.diary_size(uid), 'kind': a.get('kind') or 'journey', 'picture_cap': int(a.get('pictures') or 0)}
                await self.page(uid); await self.set_device(uid, phone)
                self.pictured[uid] = []
                self.log({'uid': uid, 'cmd': 'begin_turn', 'args': [self.state['slot']], 'device': self.state['turn']['device'],
                          'result': f"cap {self.state['turn']['cap']}" + (' · may switch device' if a.get('switch') else '')})
                self.save_state(); return {'turn': self.state['turn'], 'clock': self.clock_str()}
            if cmd == 'note_prompt':   # simctl prompt: the size of the prompt and of the files it tells the person to read
                t = self.state['turn']
                if t and t['uid'] == a.get('uid'): t['prompt'] = {'chars': int(a.get('chars') or 0), 'reads': int(a.get('reads') or 0)}; self.save_state()
                return {'noted': bool(t and t['uid'] == a.get('uid'))}
            if cmd == 'cost':   # the conductor's measured numbers for a turn it just ended (or a workshop step, by label)
                return self.cost_measured(a)
            if cmd == 'end_turn':
                t = self.state['turn']
                if t and t['uid'] in self.pages:
                    await self.commit(t['uid']); await self.set_device(t['uid'], PEOPLE[t['uid']][1])
                if t: self.cost_turn(t)
                pg, _ = await self.fresh('__world')
                await self.set_clock()
                notes = await self.post_office(pg)
                await self.commit('__world')
                self.state['turn'] = None
                self.log({'uid': (t or {}).get('uid'), 'cmd': 'end_turn', 'result': notes, 'used': (t or {}).get('used')})
                self.save_state(); return {'ended': t, 'mail': notes}
            if cmd == 'world':
                if a.get('slot'): self.state['slot'] = a['slot']; self.state['slot_n'] = 0; self.state['slot_min'] = 0
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
            if cmd == 'shots':   # the workshop's visual review: a person's pages on the phone and on the desktop (no turn open)
                if self.state['turn']: return {'error': 'end the open turn first'}
                uid = a['uid']; outd = os.path.join(self.dir, 'workshop', 'shots', uid); os.makedirs(outd, exist_ok=True)
                pg, _ = await self.fresh(uid); done = []
                for dev in ('phone', 'desktop'):
                    await self.set_device(uid, dev == 'phone')
                    for lab in a.get('pages') or []:
                        r = await pg.evaluate("l => __SIM.go(l)", lab)
                        if not r['ok']: done.append([dev, lab, 'not in the menu']); continue
                        await pg.evaluate("() => { try { render(); } catch (e) {} }"); await self.settle(pg, 700)
                        p = os.path.join(outd, f"{dev}_{re.sub(r'[^A-Za-z0-9]+', '_', lab).strip('_')[:40]}.png"); await self.shot(uid, p); done.append([dev, lab, p])
                await self.set_device(uid, PEOPLE[uid][1]); await self.commit(uid)
                return {'uid': uid, 'shots': done}
            if cmd == 'party':   # adjust an outside party's rules (the selftest makes its supplier answer at once)
                k = self.world.resolve_party(a['party'])
                if not k: return {'error': 'no such party'}
                self.world.parties[k].update(a.get('patch') or {}); self.state['world'].setdefault('party_patch', {})[k] = self.world.parties[k]
                self.save_state(); return {'party': k, 'rules': self.world.parties[k]}
            if cmd == 'world_client':   # the client's side played by world rules on the portal (no client agent turns)
                self.state['world']['client_rules'] = bool(a.get('on')); self.save_state(); return {'client_rules': self.state['world']['client_rules']}
            if cmd == 'script':   # Pilot 3: run one scripted world action again by hand (the conductor's repair; the selftest)
                if self.state['turn']: return {'error': 'end the open turn first'}
                pg, _ = await self.fresh('__world')
                r = await pg.evaluate("async (p) => __P3.run(p)", a.get('payload') or {})
                await self.commit('__world')
                self.log({'uid': '__world', 'cmd': 'script', 'args': [(a.get('payload') or {}).get('do')], 'result': r})
                return {'result': r}
            if cmd == 'cycle':   # Pilot 3: the business-cycle book (sim/cycle_book.json) and its scripted roles
                if a.get('on'):   # a scripted role that plays this run after all ('u_controller', or one kind of step: 'u_angel:receive'); feed: the bank feed
                    self.world.enable_cycle(); self.state['world']['cycle_play'] = list(a.get('play') or []); self.state['world']['bank_feed'] = bool(a.get('feed'))
                else: self.state['world']['cycle'] = False
                self.save_state(); return {'cycle': self.world.cycle_on, 'roles': (self.world.cycle or {}).get('roles'),
                                           'scripted': [u for u in ((self.world.cycle or {}).get('scripted') or {}) if self.world.scripted(u)], 'play': self.state['world'].get('cycle_play') or [], 'feed': bool(self.state['world'].get('bank_feed'))}
            if cmd == 'world_agent':
                self.state['world']['agent'] = bool(a.get('on')); self.save_state(); return {'world_agent': self.state['world']['agent']}
            if cmd == 'world_voice':   # the voicer (sim/voicer.py): outside replies in the party's own words, the rule's facts kept
                self.state['world']['voice'] = bool(a.get('on')); self.save_state()
                return {'world_voice': self.state['world']['voice'], 'token': bool(os.environ.get('SIM_AI_TOKEN_FILE') or os.environ.get('SIM_AI_TOKEN'))}
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
        self.state['day'] = nxt; self.state['slot'] = 'morning'; self.state['slot_n'] = 0; self.state['slot_min'] = 0
        await self.ctx.clock.set_system_time(f"{nxt}T06:30:00{TZ}")
        r = await pg.evaluate("d => appSetDay(d)", nxt)
        await self.commit('__world')
        self.log({'uid': '__world', 'cmd': 'advance', 'result': r})
        self.save_state()
        return {'scored': sc.get('line'), 'day': nxt, 'hooks': r}

    # ---- Pilot 3: the cycle referee on the latest snapshot (sim/cycle.py), for the world's gates and scripts
    def cycle_obj(self):
        import cycle as CY
        p = os.path.join(self.dir, 'db.json')
        db = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}
        W = self.world.st
        return CY.Cycle(db, self.world.cycle, {'gated': W.get('gated', {}), 'calls': self.state.get('calls', []), 'interrupts_done': W.get('interrupts_done', {})}, None, self.state['day'])

    def cycle_gate(self, c):
        try: return self.cycle_obj().gate(c)
        except Exception as e: return False, f'gate error: {e}', {}

    def cycle_po_numbers(self):
        try: return {po['number'] for po in self.cycle_obj().pos(live=False)}
        except Exception: return set()

    def cycle_job(self):
        try: return (self.cycle_obj().project() or {}).get('id', '')
        except Exception: return ''

    def cycle_refs(self):
        try: return self.cycle_obj().refs()
        except Exception: return {}

    async def ai_forward(self, method, path, hdrs, body):
        """/api/ to the hosted copy's AI proxy, as the signed-in member whose session token the conductor gave at run time
        (SIM_AI_TOKEN or SIM_AI_TOKEN_FILE). The token, the prompt and the answer are never logged: only the path, the
        status, the size and the time. Off (503, the assistant's built-in logic answers) without a token or between turns."""
        f = os.environ.get('SIM_AI_TOKEN_FILE', '')
        tok = (open(f).read().strip() if f and os.path.exists(f) else os.environ.get('SIM_AI_TOKEN', '').strip())
        t = self.state.get('turn')
        if not tok: return 503, 'application/json', b'{"error":"not available in the simulation (no SIM_AI_TOKEN)"}'
        if not t: return 503, 'application/json', b'{"error":"the live assistant answers only during a person\'s turn"}'
        import ssl, urllib.request, urllib.error
        ca = os.environ.get('SSL_CERT_FILE') or os.environ.get('REQUESTS_CA_BUNDLE')
        ctx = ssl.create_default_context(cafile=ca) if ca and os.path.exists(ca) else ssl.create_default_context()
        req = urllib.request.Request(AI_URL + path, data=body if method in ('POST', 'PUT') else None, method=method,
                                     headers={'Content-Type': hdrs.get('content-type', 'application/json'), 'Authorization': 'Bearer ' + tok})
        t0 = time.time()
        def go():
            try:
                with urllib.request.urlopen(req, timeout=180, context=ctx) as r: return r.status, r.headers.get('Content-Type', 'application/json'), r.read()
            except urllib.error.HTTPError as e: return e.code, e.headers.get('Content-Type', 'application/json'), e.read()
            except Exception as e: return 502, 'application/json', json.dumps({'error': f'the live proxy did not answer: {str(e)[:120]}'}).encode()
        st, ct, out = await asyncio.to_thread(go)
        self.log({'uid': '__ai', 'cmd': 'ai', 'args': [path.split('?')[0]], 'result': st, 'for': t.get('uid'), 'ms': int((time.time() - t0) * 1000), 'bytes': len(out)})
        return st, ct, out

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
        t = self.state.get('turn') or {}
        if t.get('uid') == uid: phone = t.get('phone', phone)
        return {'uid': uid, 'name': name, 'role': role, 'phone': phone, 'switch': bool(t.get('switch')) if t.get('uid') == uid else False, 'day': self.state['day'], 'slot': self.state['slot'], 'clock': self.clock_str(),
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
                # The app's /api/ai (the Claude-backed assistant) and the hosted functions: forwarded to the live proxy when
                # the run has a signed-in session token (ai_forward); otherwise 503 and the assistant's built-in logic answers.
                status, ctype, out = await self.ai_forward(method, path, hdrs, body)
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
  screen [--full] [--shot] [--marks]   what is on your screen, controls numbered [n ...]; --marks adds {blue} on the
                               blue (primary) button and {disabled} on a greyed-out one
  do "step; step; ..." [--find "text"]   up to 8 steps in one call (tap, type, pick, key, go, find, scroll, back,
                               upload, photo); stops at the first error; one result and the final screen
                               (or only the lines with the text). Steps target a number or a label: tap "Save" .
  scroll                       the next page of the same screen
  find "text"                  only the lines of your screen with that text, and the controls next to them
  tap <n> | tap "Label"        tap control n, or the one control with that label
  type <n> "text" [--enter]    type into field n
  pick <n> "option"            choose an option in select n
  upload <n> <file>            attach a file through control n (a file field or a button that opens the picker)
  photo <n>                    take a photo with control n (an invented picture)
  key Enter|Escape|Tab         press a key
  back                         close the open sheet, or go back a screen
  go "<menu label>"            open a menu entry by its label ("Purchasing" or "Purchasing > Deliveries"); also a button you
                               see outside the page by its exact words (the menu's footer: "Switch User")
  ask "question"               ask your assistant
  mail | mail sent | mail drafts | mail read <n> | mail reply <n> "text" [--all] | mail send "to, to" "subject" "body" [--cc "a, b"]
  mail senddraft <n>           send a draft the app saved to your mailbox (after `mail drafts`)
  --why "..."                  on any action: the one-line reason (the measure or the Standard behind it); it goes in the record
  call "<person>" "what was said"   a phone call: it goes in both diaries, nothing else
  news                         what happened around you (on site, calls you got) since your last turn
  device | device phone|desktop   which device you are on; pick up the other one when your turn allows it"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', required=True)
    ap.add_argument('--port', type=int, default=0)
    ap.add_argument('--resume', action='store_true')
    ap.add_argument('--seed', type=int, default=0, help='the held-out events seed (default: from the run name)')
    ap.add_argument('--debug', action='store_true', help='developer only: allow simctl debug-eval (never for a run with agents)')
    ap.add_argument('--live', metavar='ROLE', help='the same verbs against the live site as that role\'s QA account (owner, pm, coord, billing, '
                                                   'controller; SD_QA_USERS names the accounts file): sim/live.py')
    a = ap.parse_args()
    if not re.match(r'^[\w.-]+$', a.run): raise SystemExit('run names are letters, digits, dot, dash, underscore')
    if a.live:
        import live
        os.makedirs(RUNS, exist_ok=True)
        qa = os.environ.get('SD_QA_USERS') or sys.exit('live mode needs SD_QA_USERS (the QA accounts file, outside the repo)')
        asyncio.run(live.LiveSim(a.run, a.port, a.live, qa).main()); return
    if not os.path.exists(DIST): raise SystemExit('build first: python3 build.py')
    seed = a.seed or int(hashlib.sha1(a.run.encode()).hexdigest()[:6], 16)
    os.makedirs(RUNS, exist_ok=True)
    sim = Sim(a.run, a.port, a.resume, seed, a.debug)
    asyncio.run(sim.main())


if __name__ == '__main__':
    main()
