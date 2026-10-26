"""sim/live.py: the toolkit against the LIVE site (Alan 10-26: "we only see 50% of the puzzle").

The local world (sim/server.py) is one browser on a pinned copy of the build with an invented outside world. The
firm will use the hosted app: real sign-in, a phone and a desktop that each keep their own copy of the records and
meet through sync, a network that drops. Live mode serves the SAME `sim/act` verbs against
https://smartdesigns-erp.netlify.app, signed in as one role's QA account (platform/test/qa_accounts.py; the accounts
file from SD_QA_USERS, outside the repo), so an expert can do one live turn a round through the toolkit they know.

    SD_QA_USERS=/abs/qa_users.json python3 sim/server.py --run live-pm-1 --live pm      # owner, pm, coord, billing, controller
    SIM_RUN=live-pm-1 sim/act u_alan screen
    SIM_RUN=live-pm-1 sim/simctl begin u_alan live --device phone; SIM_RUN=live-pm-1 sim/simctl prompt u_alan

What is different from the local world, on purpose:
- Two devices, two copies. The phone (390x844, touch) and the desktop (1440x900) are separate browsers, each signed in
  through the real sign-in screen; `device phone|desktop` puts one down and picks up the other (always allowed here).
  What one saved reaches the other only through sync; every screen ends with the app's own save status.
- No world and no clock pin: no vendors, clients, news, calls or mail (`news`, `call`, `mail` say so); the toolkit's
  clock is the real New York time; the app's day is whatever the workspace's clock says.
- The records are the 'qa-loop' workspace's: the demo company, filled by the first office sign-in, shared by the loop's
  live turns and the live journeys check (never emptied by the live database checks, which use 'qa').
- The assistant is the live one, charged to the QA account. Nothing reaches a real person: QA accounts have no Google.
- A device that is signed out is signed in again by the harness the way a phone fills a saved password, and the
  result says so; the password never enters the action log.
The conductor's controls (/admin, the run's token): status, begin_turn, end_turn, brief, note_prompt, cost, shutdown,
and for the live journeys check (platform/test/live_journeys_test.py) only: offline (a device's network off or on),
signin (a device signs in again) and records (a read-only look at one device's own copy, for the referee).
"""
import asyncio, json, os, re, secrets, sys, time
from datetime import datetime
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import server as SV   # noqa: E402

SITE = os.environ.get('SDP_SITE', 'https://smartdesigns-erp.netlify.app').rstrip('/')
NY = ZoneInfo('America/New_York')
# role -> (QA accounts key, the person in the app); all in the 'qa-loop' workspace (platform/test/qa_accounts.py), which the
# live database checks never empty
ROLES = {'owner': ('loopowner', 'u_owner'), 'pm': ('pm', 'u_alan'), 'coord': ('coord', 'u_chen'), 'billing': ('billing', 'u_billing'),
         'controller': ('controller', 'u_controller')}
# the in-page reader without its local-world parts: the live app keeps its own timers (Google sync, the brain)
LIVE_TOOLS = SV.PAGE_TOOLS.replace("try { clearInterval(bnTimer); bnTimer = 1; } catch (e) {}", "").replace("try { clearInterval(gsTimerId); } catch (e) {}", "")
assert LIVE_TOOLS != SV.PAGE_TOOLS, 'page_tools.js changed: update LIVE_TOOLS'
SYNC_JS = """() => { const C = window.Cloud, s = (C && C.state) || {}; const el = document.getElementById('save-status');
  return { online: navigator.onLine, syncing: !!s.syncing, pending: !!s.pending, err: s.err || '', note: s.note || '',
           status: el ? String(el.innerText || '').replace(/\\s+/g, ' ').trim() : '', signedIn: !!(C && C.user && C.user()) }; }"""
# the referee's read-only look into one device's own copy: every record (at any depth) whose words carry the text
RECORDS_JS = """(want) => { const low = s => String(s == null ? '' : s).toLowerCase(), w = low(want), out = [], seen = new Set();
  const walk = (o, path, depth) => { if (!o || typeof o !== 'object' || seen.has(o) || depth > 7 || out.length > 12) return; seen.add(o);
    if (!Array.isArray(o) && Object.keys(o).some(k => typeof o[k] === 'string' && low(o[k]).includes(w))) {
      const r = {}; for (const k of Object.keys(o)) { const v = o[k]; if (v == null || typeof v !== 'object') r[k] = v; else if (Array.isArray(v)) r[k] = v.length > 40 ? '[' + v.length + ']' : v.map(x => (x && typeof x === 'object') ? Object.fromEntries(Object.entries(x).filter(([, y]) => y == null || typeof y !== 'object')) : x); }
      out.push({ path, rec: r }); }
    for (const k of Object.keys(o)) walk(o[k], path + '.' + k, depth + 1); };
  walk(typeof DB !== 'undefined' ? DB : window.DB, 'DB', 0); return out; }"""


def ny_now(): return datetime.now(NY)


class LiveSim(SV.Sim):
    def __init__(self, run, port, role, qa_path):
        if role not in ROLES: raise SystemExit(f'--live takes one of {", ".join(ROLES)}')
        self.run, self.port, self.debug, self.role = run, port, False, role
        self.key, self.uid = ROLES[role]
        self.qa = json.load(open(qa_path))
        if self.key not in self.qa: raise SystemExit(f'no QA account "{self.key}" in {qa_path}: run platform/test/qa_accounts.py --add {self.key}')
        self.dir = os.path.join(SV.RUNS, run)
        if os.path.exists(os.path.join(self.dir, 'world.json')): raise SystemExit(f'run {run} exists: pick a new name')
        for d in ('diary', 'files', 'shots'): os.makedirs(os.path.join(self.dir, d), exist_ok=True)
        self.lock = asyncio.Lock()
        self.pages, self.page_ver, self.errs, self.cdp, self.device = {}, {}, {}, {}, {}
        self.screens, self.mail_map, self.pictured = {}, {}, {}
        self.last_active, self.stop, self.resume = None, asyncio.Event(), False
        self.token = secrets.token_hex(16)
        open(os.path.join(self.dir, '.admin_token'), 'w').write(self.token)
        self.state = {'run': run, 'live': role, 'site': SITE, 'seed': 0, 'created': SV.now_iso(), 'day': ny_now().date().isoformat(), 'slot': 'work1',
                      'slot_n': 0, 'version': 0, 'hash': '', 'boots': 0, 'actions': 0, 'turn': None, 'people': {}, 'ext_mail': {}, 'drive': [],
                      'calls': [], 'news': {}, 'seen': {}, 'fia_pending': {}, 'sent_seen': {}, 'world': {}, 'days_done': []}
        self.world = self.referee = None
        self.dev = {}        # 'phone' | 'desktop' -> {'ctx', 'page', 'signins'}
        self.cur = 'desktop'
        self.diary_init(self.uid)

    # ---- the clock is the real one
    def clock_str(self):
        return ny_now().strftime('%H:%M')

    async def set_clock(self):
        self.state['day'] = ny_now().date().isoformat()

    def note_seen(self, uid, title, text): pass

    # ---- two devices, each its own browser and its own copy
    async def start_browser(self):
        from playwright.async_api import async_playwright
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.launch()
        for d in ('desktop', 'phone'):
            ph = d == 'phone'
            ctx = await self.browser.new_context(viewport=SV.PHONE if ph else SV.DESKTOP, is_mobile=ph, has_touch=ph, device_scale_factor=2 if ph else 1,
                                                 timezone_id='America/New_York', accept_downloads=True)
            pg = await ctx.new_page()
            self.dev[d] = {'ctx': ctx, 'page': pg, 'signins': 0, 'errs': []}
            pg.on('pageerror', lambda e, dd=d: self.dev[dd]['errs'].append(str(e)[:240]))
            pg.on('dialog', lambda x, u=self.uid: asyncio.ensure_future(self._dialog(u, x)))
            await self.sign_in(d)
        self.use(self.cur)

    def use(self, d):
        """the device in the person's hand"""
        self.cur = d
        self.pages[self.uid] = self.dev[d]['page']
        self.device[self.uid] = d == 'phone'
        self.errs[self.uid] = self.dev[d]['errs']
        self.page_ver[self.uid] = self.state['version']

    async def sign_in(self, d):
        """through the real sign-in screen, as live_app_test.py does; the password is typed by the harness, never logged"""
        pg, acc = self.dev[d]['page'], self.qa[self.key]
        if not await pg.evaluate("() => !!document.querySelector('#cl-email')"):
            await pg.goto(SITE)
        await pg.wait_for_selector('#cl-email', timeout=90000)
        await pg.fill('#cl-email', acc['email']); await pg.fill('#cl-pass', acc['password'])
        await pg.click('#cl-form button[type=submit]')
        await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=180000)
        await pg.wait_for_timeout(1500)
        await self.tools(pg)
        self.dev[d]['signins'] += 1
        self.log({'uid': self.uid, 'cmd': 'sign_in', 'args': [d], 'result': f"signed in on the {d} as {acc['email']}"})

    async def tools(self, pg):
        if not await pg.evaluate("() => !!window.__SIM"):
            await pg.evaluate(LIVE_TOOLS)

    async def signed_out(self, pg):
        try: return await pg.evaluate("() => { const e = document.querySelector('#cl-email'); return !!(e && e.getClientRects().length) || document.body.dataset.booted !== '1'; }")
        except Exception: return True

    async def page(self, uid):
        return self.pages[self.uid]

    async def fresh(self, uid):
        pg = self.pages[self.uid]
        self.note = ''
        if await self.signed_out(pg):
            try:
                await pg.wait_for_function("document.body.dataset.booted==='1' || !!document.querySelector('#cl-email')", timeout=60000)
            except Exception: pass
            if await self.signed_out(pg):
                await self.sign_in(self.cur)
                self.note = f'(You were signed out on your {self.cur}; you signed in again with your saved password.)'
        await self.tools(pg)
        self.last_active = uid
        return pg, False

    async def commit(self, uid):
        """the app saves and syncs on its own; the harness waits (up to 12 s) for this device's sync to settle, as a
        person glances at the status, and reports it"""
        pg = self.pages[self.uid]
        t0 = time.time(); s = {}
        while time.time() - t0 < 12:
            try: s = await pg.evaluate(SYNC_JS)
            except Exception: break
            if not s.get('online') or (not s.get('syncing') and not s.get('pending')): break
            await asyncio.sleep(0.5)
        self.last_sync = s
        return bool(s) and not s.get('pending')

    async def boot(self, uid):
        return 0

    async def render_screen(self, uid, pg, full=False, shot=False, marks=False):
        # a tap may reload the page (Reload on the red banner, Switch User): wait for it to start or to ask for a sign-in
        try: await pg.wait_for_function("document.body && (document.body.dataset.booted==='1' || !!document.querySelector('#cl-email') || !!document.getElementById('fatal'))", timeout=90000)
        except Exception: pass
        if await self.signed_out(pg) and not await pg.evaluate("() => !!document.getElementById('fatal')"):
            await self.sign_in(self.cur)
            self.note = f'(You were signed out on your {self.cur}; you signed in again with your saved password.)'
        await self.tools(pg)
        out = await super().render_screen(uid, pg, full, shot, marks)
        try: s = await pg.evaluate(SYNC_JS)
        except Exception: s = {}
        state = s.get('status') or ('offline' if s and not s.get('online') else '')
        out['text'] += f"\n[the app's save status on your {self.cur}: {state or 'not shown on this screen'}" + (' · no network' if s and not s.get('online') else '') + ']'
        if getattr(self, 'note', ''): out['text'] = self.note + '\n' + out['text']; self.note = ''
        return out

    # ---- no outside world here
    async def v_news(self, uid, pg, args, opts):
        return {'ok': True, 'text': 'Live site: there is no outside world here (no site events, calls or news). What you know comes from your screens and your diary.'}

    async def v_call(self, uid, pg, args, opts):
        return {'ok': False, 'text': 'Live site: nobody answers calls here (no outside world). Use Messages in the app to reach the team.'}

    async def v_mail(self, uid, pg, args, opts):
        return {'ok': False, 'text': 'Live site: your QA account has no mailbox connected and there is no outside world, so there is no mail. '
                                     'Anything the app would send stops at a draft or a mail app; note it.'}

    async def v_device(self, uid, pg, args, opts):
        want = (args[0].lower() if args else '').strip()
        if not want: return {'ok': True, 'text': f'You are on your {self.cur}. Your other device is on the desk: `device phone` or `device desktop`.'}
        if want not in ('phone', 'desktop'): return {'ok': False, 'text': 'device phone | device desktop'}
        if want == self.cur: return {'ok': True, 'text': f'You are already on your {want}.'}
        was = self.cur
        self.use(want)
        pg2, _ = await self.fresh(uid)
        await self.settle(pg2, 500)
        out = await self._after(uid, pg2, opts)
        out['text'] = (f'You put down your {was} and picked up your {want}. It is another device with its own copy of the records: what you '
                       f'saved on the {was} shows here once it has synced.\n') + out['text']
        out['control'] = 'device ' + want; out['kind'] = 'device'
        return out

    async def _reloads(self, fn, uid, pg, args, opts):
        """a tap that reloads the page (Switch User, Reload, Reset local data) ends on the page it reloaded into"""
        try: return await fn(uid, pg, args, opts)
        except Exception as e:
            if not re.search(r'context was destroyed|navigat|__SIM|Target closed|detached', str(e)): raise
            out = await self.render_screen(uid, pg)
            out['text'] = '(the page reloaded)\n' + out['text']
            return out

    async def _one(self, uid, cmd, args, opts, t):
        """the same action as on the local world; when the page reloads under the harness's own reads after it (the reload
        lands a moment late), the person simply sees the page it reloaded into"""
        try: return await super()._one(uid, cmd, args, opts, t)
        except Exception as e:
            if not re.search(r'context was destroyed|navigat|__SIM|Target closed|detached', str(e)): raise
            out = await self.render_screen(uid, self.pages[self.uid])
            out['text'] = '(the page reloaded)\n' + out['text']
            self.log({'uid': uid, 'cmd': cmd, 'args': args, 'result': 'the page reloaded under the action', 'ok': True})
            return out

    async def v_go(self, uid, pg, args, opts): return await self._reloads(super().v_go, uid, pg, args, opts)
    async def v_tap(self, uid, pg, args, opts): return await self._reloads(super().v_tap, uid, pg, args, opts)
    async def v_back(self, uid, pg, args, opts): return await self._reloads(super().v_back, uid, pg, args, opts)
    async def v_key(self, uid, pg, args, opts): return await self._reloads(super().v_key, uid, pg, args, opts)

    async def act(self, uid, cmd, args, opts):
        if uid != self.uid: return {'ok': False, 'text': f'this live run is {SV.PEOPLE[self.uid][2]} ({self.uid}, the QA {self.role} account); {uid} is not signed in here'}
        return await super().act(uid, cmd, args, opts)

    async def shot(self, uid, path, jpeg=False):
        """a real phone browser here: its own screenshot is the phone's, at its CSS size"""
        pg = self.pages[self.uid]
        if jpeg: await pg.screenshot(path=path, full_page=False, type='jpeg', quality=70, scale='css')
        else: await pg.screenshot(path=path, full_page=False, scale='css')

    # ---- the conductor's controls
    async def admin(self, cmd, a):
        async with self.lock:
            if cmd == 'status':
                return {'run': self.run, 'live': self.role, 'site': SITE, 'uid': self.uid, 'device': self.cur, 'day': self.state['day'], 'slot': self.state['slot'],
                        'clock': self.clock_str(), 'turn': self.state['turn'], 'actions': self.state['actions'], 'days': [self.state['day']], 'days_done': [],
                        'signins': {d: v['signins'] for d, v in self.dev.items()}}
            if cmd == 'begin_turn':
                if a.get('uid') != self.uid: return {'error': f'this live run is {self.uid} ({self.role})'}
                dev = (a.get('device') or self.cur).lower()
                if dev in self.dev: self.use(dev)
                self.state['turn'] = {'uid': self.uid, 'cap': int(a.get('cap') or 15), 'used': 0, 'minutes': 0.0, 'min_cap': float(a.get('minutes') or 0),
                                      'slot': 'live', 'started': SV.now_iso(), 'phone': self.cur == 'phone', 'device': self.cur, 'switch': True,
                                      'day': self.state['day'], 'diary0': self.diary_size(self.uid)}
                self.pictured[self.uid] = []
                self.log({'uid': self.uid, 'cmd': 'begin_turn', 'args': ['live'], 'device': self.cur, 'result': f"cap {self.state['turn']['cap']} · live {SITE}"})
                self.save_state(); return {'turn': self.state['turn'], 'clock': self.clock_str()}
            if cmd == 'end_turn':
                t = self.state['turn']
                await self.commit(self.uid)
                if t: self.cost_turn(t)
                self.state['turn'] = None
                self.log({'uid': self.uid, 'cmd': 'end_turn', 'used': (t or {}).get('used')})
                self.save_state(); return {'ended': t, 'sync': getattr(self, 'last_sync', {})}
            if cmd == 'brief':
                t = self.state.get('turn') or {}
                return {'uid': self.uid, 'name': SV.PEOPLE[self.uid][2], 'role': SV.PEOPLE[self.uid][0], 'phone': self.cur == 'phone', 'switch': True,
                        'day': self.state['day'], 'slot': 'live', 'clock': self.clock_str(), 'news': 0, 'unread': 0, 'run': self.run, 'live': self.role, 'site': SITE}
            if cmd == 'note_prompt':
                t = self.state['turn']
                if t and t['uid'] == a.get('uid'): t['prompt'] = {'chars': int(a.get('chars') or 0), 'reads': int(a.get('reads') or 0)}; self.save_state()
                return {'noted': bool(t and t['uid'] == a.get('uid'))}
            if cmd == 'cost': return self.cost_measured(a)
            if cmd == 'offline':   # a device's network off or on (a phone in a basement, then back on the street)
                d = a.get('device') or 'phone'
                await self.dev[d]['ctx'].set_offline(bool(a.get('on')))
                if not a.get('on'):   # back online: the app pushes what waited; give it a moment, as a person would
                    await self.dev[d]['page'].wait_for_timeout(1500)
                self.log({'uid': self.uid, 'cmd': 'network', 'args': [d, 'off' if a.get('on') else 'on']})
                return {'device': d, 'offline': bool(a.get('on'))}
            if cmd == 'signin':
                d = a.get('device') or self.cur
                pg = self.dev[d]['page']
                if await self.signed_out(pg): await self.sign_in(d); return {'device': d, 'signed_in': True}
                return {'device': d, 'signed_in': False, 'why': 'already signed in'}
            if cmd == 'records':   # the referee: read-only, never a person's action
                d = a.get('device') or self.cur
                pg = self.dev[d]['page']
                try: recs = await pg.evaluate(RECORDS_JS, str(a.get('match') or ''))
                except Exception as e: recs = {'error': str(e)[:200]}
                try: s = await pg.evaluate(SYNC_JS)
                except Exception: s = {}
                return {'device': d, 'records': recs, 'sync': s}
            if cmd == 'shutdown':
                self.save_state(); self.stop.set(); return {'bye': True}
            return {'error': f'"{cmd}" is not a live-mode control (status, begin_turn, end_turn, brief, note_prompt, cost, offline, signin, records, shutdown)'}

    async def main(self):
        srv = await asyncio.start_server(self.handle, '127.0.0.1', self.port, limit=2 ** 24)
        self.port = srv.sockets[0].getsockname()[1]
        json.dump({'port': self.port, 'pid': os.getpid(), 'started': SV.now_iso(), 'live': self.role}, open(os.path.join(self.dir, 'server.json'), 'w'))
        # never runs/.current: a live run is reached by SIM_RUN only, so the local world's pointer is left alone
        print(f'sim: LIVE run {self.run} ({self.role}, {self.qa[self.key]["email"]}) on http://127.0.0.1:{self.port} (pid {os.getpid()}); signing in on {SITE}', flush=True)
        await self.start_browser()
        self.save_state()
        print(f"sim: ready · live · {self.uid} on the phone and the desktop · {self.clock_str()} New York", flush=True)
        async with srv:
            await self.stop.wait()
        await self.browser.close(); await self.pw.stop()
        try: os.remove(os.path.join(self.dir, 'server.json'))
        except Exception: pass
