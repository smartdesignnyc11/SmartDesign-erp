"""The live journeys check (Alan 10-26: "the live site with sign-in and sync, not only a local copy"). Scripted, no AI.

One person, two devices, the real hosted app: the role's QA account (default the PM, in the 'qa-loop' workspace) signs in
on a phone and on a desktop, each its own browser with its own copy of the records, through sim/live.py (the same `act`
verbs the experts use: menu by label, tap, type, pick; never a function call or a view jump). Then, as a person would:
  1. on the phone: a task, and an estimate with a line;
  2. on the desktop: both arrived (and how long it took); the estimate finished there (a second line, saved); the task done;
  3. back on the phone: the desktop's work arrived;
  4. the same record edited on both while the phone has no signal: different fields must both stand; the same field
     must end the same on both devices, and the device whose edit lost must say so on its screen (nothing lost silently);
  5. the phone offline: a task made there stays on the phone and lands on the desktop when the signal is back;
  6. Switch User on the desktop (its copy is erased) and sign in again: everything is still there.
The records are read by the referee (the live server's read-only `records` look into each device's own copy), never
written. Each step is timed and its taps counted. Records are stamped (LJ<time>) so runs never collide.

    SD_QA_USERS=/abs/qa_users.json python3 test/live_journeys_test.py [--role pm] [--keep]
Last line: `LIVE JOURNEYS N checks · F failed`; exit 1 on any failure. The details go to review/live_journeys/.
"""
import json, os, re, signal, subprocess, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SIM = os.path.join(ROOT, 'sim')
sys.path.insert(0, os.path.join(ROOT, 'tests')); sys.path.insert(0, SIM)
import cycle_walk as CW   # noqa: E402  the screen reader and the person (tests/cycle_walk.py), shared with the screen walk

QA = os.environ.get('SD_QA_USERS') or sys.exit('set SD_QA_USERS to the QA accounts file (outside the repo)')
ROLE = sys.argv[sys.argv.index('--role') + 1] if '--role' in sys.argv else 'pm'
UID = {'owner': 'u_owner', 'pm': 'u_alan', 'coord': 'u_chen', 'billing': 'u_billing', 'controller': 'u_controller'}[ROLE]
STAMP = 'LJ' + time.strftime('%m%d%H%M')
RUN = f'livej-{ROLE}-{int(time.time())}'
OUT = os.path.join(ROOT, 'review', 'live_journeys')
ADMIN_OK = {'status', 'begin_turn', 'end_turn', 'offline', 'signin', 'records', 'shutdown'}
n, fails, steps = 0, [], []


def ok(c, msg, got=''):
    global n; n += 1
    print(('ok  ' if c else 'FAIL'), msg + ('' if c or not got else f'  [{str(got)[:300]}]'), flush=True)
    if not c: fails.append({'check': msg, 'got': str(got)[:600]})
    return c


class LiveWorld:
    """the live-mode server (sim/server.py --live): driven through /act like a person; /admin only for the network,
    a sign-in and the referee's read-only look"""

    def __init__(self):
        self.dir = os.path.join(SIM, 'runs', RUN)

    def start(self):
        log = os.path.join(SIM, 'runs', RUN + '.server.log'); os.makedirs(os.path.dirname(log), exist_ok=True)
        self.log = open(log, 'w')
        env = dict(os.environ, SIM_PICTURES='0', SIM_RUN=RUN)
        self.proc = subprocess.Popen([sys.executable, os.path.join(SIM, 'server.py'), '--run', RUN, '--live', ROLE], cwd=ROOT, env=env, stdout=self.log, stderr=subprocess.STDOUT)
        t0 = time.time()
        while time.time() - t0 < 300:
            if self.proc.poll() is not None: sys.exit('the live server stopped: ' + open(log).read()[-800:])
            if 'sim: ready' in open(log).read(): break
            time.sleep(1)
        else: sys.exit('the live server did not get ready in 5 minutes')
        return round(time.time() - t0, 1)

    def _post(self, path, body, admin=False):
        port = json.load(open(os.path.join(self.dir, 'server.json')))['port']
        h = {'Content-Type': 'application/json'}
        if admin: h['X-Sim-Token'] = open(os.path.join(self.dir, '.admin_token')).read().strip()
        req = urllib.request.Request(f'http://127.0.0.1:{port}{path}', data=json.dumps(body).encode(), headers=h)
        with urllib.request.urlopen(req, timeout=600) as f: return json.loads(f.read())

    def admin(self, cmd, **kw):
        assert cmd in ADMIN_OK, cmd
        return self._post('/admin', {'cmd': cmd, **kw}, admin=True)

    def act(self, uid, cmd, args=(), **opts):
        return self._post('/act', {'uid': uid, 'cmd': cmd, 'args': [str(a) for a in args], 'opts': opts})

    def records(self, dev, match):
        r = self.admin('records', device=dev, match=match)
        return r.get('records') or [], r.get('sync') or {}

    def stop(self):
        try: self.admin('shutdown')
        except Exception: pass
        try: self.proc.wait(60)
        except Exception: self.proc.send_signal(signal.SIGKILL)


W = LiveWorld()


def wait_rec(dev, match, pred=lambda R: bool(R), secs=90):
    """the referee waits for a device's own copy to show the record (the app's change feed, or its 30 s poll)"""
    t0 = time.time()
    while True:
        R, s = W.records(dev, match)
        if pred(R): return R, round(time.time() - t0, 1)
        if time.time() - t0 > secs: return R, None
        time.sleep(3)


def est_rec(R, num):
    return next((r['rec'] for r in R if r['rec'].get('number') == num), None)


def lines_of(e):
    L = (e or {}).get('lines')
    return [x for x in L if isinstance(x, dict)] if isinstance(L, list) else []


def task_rec(R):
    return next((r['rec'] for r in R if re.search(r'task', r['path'], re.I) or 'due' in r['rec'] or 'assignee' in r['rec']), None)


def switch(p, dev):
    r, txt = p._act('device', dev)
    p.device = dev
    p.scr = CW.screen_of(txt)
    if 'Red banner across the top' in p.scr.text:
        ok(False, f'the app starts on the {dev} (it showed the red "Could not start" banner)', p.scr.excerpt('Red banner', 3))
        p.tap('Reload')
    return p.scr


class Step:
    def __init__(self, p, name):
        self.p, self.name = p, name

    def __enter__(self):
        self.t0, self.taps0 = time.time(), self.p.taps
        print(f'\n-- {self.name}', flush=True)
        return self

    def __exit__(self, et, e, tb):
        rec = {'step': self.name, 'device': self.p.device, 'taps': self.p.taps - self.taps0, 'seconds': round(time.time() - self.t0, 1)}
        if et is not None and issubclass(et, CW.Stuck):
            ok(False, f'{self.name}: {e.what} (expected {e.expected})', (e.screen.excerpt(n=10) if e.screen else '') + f' · last control: {e.control}')
            rec['stuck'] = e.what
        elif et is not None:
            ok(False, f'{self.name}: the harness failed: {e}'); rec['error'] = str(e)[:300]
        print(f'   ({rec["taps"]} taps, {rec["seconds"]} s)', flush=True)
        steps.append(rec)
        return True   # every step runs, whatever happened before it


def task_new(p, title):
    p.go('Tasks', expect_menu=False)
    p.tap('New Task', expect='Say or type the task')
    p.do([('type', 'Say or type the task', title), ('tap', 'New Task')])
    ok('Added' in (p.scr.toast or '') or p.scr.has(title[:20]), f'the task is made on the {p.device} and the toast says so', p.scr.toast)


def open_est(p, num):
    p.go('Projects', expect_menu=False)
    sw = p.scr.find('Switch project', field=True)
    if sw and CW.norm(sw.value) != CW.norm('121 State Street'): p.pick('Switch project', '121 State Street')
    elif not sw: p.tap_row('121 State Street')
    p.tap('Estimates', exact=True)
    p.tap_row(num, expect='Estimate ' + num)


def phone_line(p, item, rate, qty, unit, cost):
    """a line on the phone: Add Line Item opens the full-screen line editor; fill it and tap Done"""
    p.tap('Add Line Item'); p.look()
    if not p.scr.sheet: raise CW.Stuck('Add Line Item on the phone', 'the line editor to open', p.scr, 'Add Line Item')
    F = {lab: p.scr.find(lab, field=True) for lab in ('Item', 'Quantity', 'Unit', 'Rate')}
    bc = p.scr.find('', field=True, after='Budget cost')
    miss = [k for k, c in F.items() if c is None] + ([] if bc else ['Budget cost'])
    if miss: raise CW.Stuck('the phone line editor', 'fields for ' + ', '.join(miss), p.scr, 'Add Line Item')
    if 'budget' not in CW.norm(bc.label): print(f'   note: the budget cost field on the phone has no label of its own (read as "{bc.label}")', flush=True)
    p.do_ctls([('type', F['Item'], item)])   # the item may pull a price from the library and redraw the sheet
    for lab, val in (('Budget cost', cost), ('Quantity', qty), ('Unit', unit), ('Rate', rate)):   # one at a time: each may redraw the sheet
        p.look()
        c = p.scr.find('', field=True, after='Budget cost') if lab == 'Budget cost' else p.scr.find(lab, field=True)
        if c is None: raise CW.Stuck('the phone line editor', f'the {lab} field after typing the item', p.scr, 'Add Line Item')
        try: p.do_ctls([('type', c, val)])
        except CW.Stuck as e:
            if lab != 'Budget cost': raise
            print(f'   note: the budget cost field on the phone could not be typed into ({(e.control or "")[-90:]})', flush=True)
    p.tap('Done', exact=True)


def save_est(p):
    for _ in range(3):
        if not (p.scr.has('Unsaved changes') or p.look().has('Unsaved changes')): return True
        p.tap('Save', exact=True)
    return not p.look().has('Unsaved changes')


def main():
    os.makedirs(OUT, exist_ok=True)
    boot = W.start()
    print(f'live server up in {boot}s (run {RUN}, stamp {STAMP})', flush=True)
    W.admin('begin_turn', uid=UID, cap=100000, device='phone')
    p = CW.Person(W, UID, 'phone', 'LJ', [])
    TASK1, TASK2 = f'Check the tile sample board {STAMP} by Friday', f'Photograph the stair stringer {STAMP} offline by Friday'
    num, phone_lines, desk_line = '', 0, False
    try:
        p.look()
        if 'Red banner across the top' in p.scr.text:
            ok(False, 'the app starts on the phone (it showed the red "Could not start" banner)', p.scr.excerpt('Red banner', 3)); p.tap('Reload')
        with Step(p, '1a. phone: a task'):
            task_new(p, TASK1)
            R, _ = W.records('phone', STAMP)
            ok(task_rec(R) is not None, 'the task is in the phone\'s own copy', R[:1])
        with Step(p, '1b. phone: an estimate with a line'):
            p.go('Projects', expect_menu=False)
            p.tap_row('121 State Street')
            p.tap('New Estimate', expect='Start Estimate')
            p.tap('Start Estimate', expect='Estimate EST-')
            num = (re.findall(r'EST-\d{4}-\d+', (p.scr.toast or '') + p.scr.text) or [''])[0]
            ok(bool(num), 'the new estimate has a number on the phone', p.scr.toast)
            phone_line(p, f'Tile setting {STAMP}', 9600, 1, 'ls', 6400)
            ok(save_est(p), 'the phone\'s estimate saves (no "Unsaved changes" left)', p.scr.excerpt('Unsaved', 4))
            R, _ = W.records('phone', num)
            phone_lines = len(lines_of(est_rec(R, num)))
            ok(phone_lines >= 1, f'{num} holds the phone\'s line in the phone\'s own copy', est_rec(R, num))
        with Step(p, '2a. desktop: it arrived; the task done there'):
            switch(p, 'desktop')
            R, secs = wait_rec('desktop', STAMP, lambda R: task_rec(R) is not None)
            ok(secs is not None, f'the phone\'s task reached the desktop' + (f' ({secs} s after picking it up)' if secs is not None else ' (not within 90 s)'))
            p.go('Tasks', expect_menu=False)
            p.look()
            hit = p.scr.text.find(STAMP)
            done = [c for c in p.scr.ctls if c.action and CW.norm(c.label) == 'mark done' and 0 <= c.pos < hit] if hit >= 0 else []
            if not done: raise CW.Stuck('mark the task done on the desktop', f'a Mark Done next to "{TASK1}" in Tasks', p.scr, p.last_control)
            p.tap_ctl(done[-1])
        with Step(p, '2b. desktop: the estimate finished there (a second line, saved)'):
            if num:
                R, secs = wait_rec('desktop', num, lambda R: est_rec(R, num) is not None)
                ok(secs is not None, f'{num} reached the desktop' + (f' ({secs} s)' if secs is not None else ' (not within 90 s)'))
                open_est(p, num)
                k = max(1, phone_lines) + (1 if phone_lines else 0)
                item = CW.line_fields(p.look() and p, k)[0]
                if not item or item.value: p.tap('Add Line'); p.look()
                item, rate, qty, unit, cost = CW.line_fields(p, k)
                if not item: raise CW.Stuck(f'line {k} on the desktop', 'an empty line to type into', p.scr, p.last_control)
                if cost is None: print(f'   note: line {k} on the desktop shows no budget cost field to type into', flush=True)
                p.do_ctls([('type', item, f'Waterproofing {STAMP}'), ('type', rate, 2400), ('type', qty, 1)] + ([('type', cost, 1500)] if cost else []))
                desk_line = save_est(p)
                ok(desk_line, 'the desktop\'s estimate saves within three taps of Save', p.scr.excerpt('Unsaved', 4))
        with Step(p, '3. phone: the desktop\'s work arrived'):
            switch(p, 'phone')
            if num and not desk_line: print('   (the desktop added no line, so there is none to look for on the phone)', flush=True)
            if num and desk_line:
                R, secs = wait_rec('phone', num, lambda R: any(f'Waterproofing {STAMP}' in str(x.get('item')) for x in lines_of(est_rec(R, num))))
                ok(secs is not None, f'the desktop\'s line on {num} reached the phone' + (f' ({secs} s)' if secs is not None else ' (not within 90 s)'),
                   [x.get('item') for x in lines_of(est_rec(R, num))])
            R, secs = wait_rec('phone', STAMP, lambda R: any(r['rec'].get('done') or r['rec'].get('status') == 'done' or r['rec'].get('doneAt') for r in R))
            ok(secs is not None, 'the task done on the desktop reads done on the phone' + (f' ({secs} s)' if secs is not None else ' (not within 90 s)'), R[:1])
        if num:
            for same in (False, True):
                with Step(p, f'4{"b" if same else "a"}. both devices edit {num} while the phone has no signal: {"the same field" if same else "different fields"}'):
                    mine, theirs = f'Kitchen and baths {STAMP} phone{" 2" if same else ""}', f'Kitchen and baths {STAMP} desktop'
                    switch(p, 'phone'); open_est(p, num)
                    W.admin('offline', device='phone', on=True)
                    p.do([('type', 'Title', mine)]); save_est(p)
                    switch(p, 'desktop'); open_est(p, num)
                    p.do([('type', 'Title', theirs)] if same else [('type', 'Valid Until', '2026-12-15')]); save_est(p)
                    switch(p, 'phone')
                    W.admin('offline', device='phone', on=False)
                    time.sleep(20)
                    E = {d: est_rec(W.records(d, num)[0], num) or {} for d in ('phone', 'desktop')}
                    S = {d: W.records(d, num)[1] for d in ('phone', 'desktop')}
                    if not same:
                        R, secs = wait_rec('desktop', num, lambda R: (est_rec(R, num) or {}).get('title') == mine, 60)
                        E['desktop'] = est_rec(R, num) or E['desktop']; E['phone'] = est_rec(W.records('phone', num)[0], num) or E['phone']
                        both = {d: (E[d].get('title') == mine, (E[d].get('validUntil') or E[d].get('valid') or '') == '2026-12-15') for d in E}
                        ok(all(a and b for a, b in both.values()), 'different fields edited on two devices: both edits stand on both devices',
                           {d: [E[d].get('title'), E[d].get('validUntil') or E[d].get('valid')] for d in E})
                    else:
                        R, secs = wait_rec('desktop', num, lambda R: (est_rec(R, num) or {}).get('title') == E['phone'].get('title'), 60)
                        E['desktop'] = est_rec(R, num) or E['desktop']
                        won = E['phone'].get('title')
                        ok(bool(won) and won == E['desktop'].get('title'), 'the same field edited on two devices ends the same on both', [E['phone'].get('title'), E['desktop'].get('title')])
                        loser = 'phone' if won != mine else 'desktop'
                        S = {d: W.records(d, num)[1] for d in ('phone', 'desktop')}
                        told = 'kept the other device' in (S[loser].get('status') or '')
                        ok(told, f'the {loser}, whose edit lost, says so on its screen (nothing lost silently)',
                           f"its save status reads \"{S[loser].get('status') or '(not on the screen)'}\"; the app's note: \"{S[loser].get('note')}\"")
        with Step(p, '5. phone offline: a task made there lands on the desktop when the signal is back'):
            switch(p, 'phone')
            W.admin('offline', device='phone', on=True)
            task_new(p, TASK2)
            st = W.records('phone', STAMP)[1]
            ok('offline' in (st.get('status') or '').lower() or 'saved on this phone' in (st.get('status') or '').lower(),
               'the phone says the task is saved on the phone and waits for the signal', f"save status: \"{st.get('status') or '(not on the screen)'}\"")
            R, _ = W.records('desktop', 'offline')
            ok(not any(STAMP in json.dumps(r['rec']) for r in R), 'the desktop does not have it while the phone has no signal')
            W.admin('offline', device='phone', on=False)
            R, secs = wait_rec('desktop', TASK2[:30], lambda R: any(STAMP in json.dumps(r['rec']) for r in R))
            ok(secs is not None, 'the offline task reached the desktop once the phone was back online' + (f' ({secs} s)' if secs is not None else ' (not within 90 s)'))
        with Step(p, '6. desktop: Switch User, sign in again, everything is still there'):
            switch(p, 'desktop')
            p.go('Switch User', expect_menu=False)
            p.look()
            R, _ = W.records('desktop', STAMP)
            have = json.dumps(R)
            ok(TASK1[:20] in have and TASK2[:20] in have, 'after signing in again the desktop has both tasks', [r['rec'].get('title') or r['rec'].get('name') for r in R][:6])
            if num:
                R, _ = W.records('desktop', num)
                have_items = [str(x.get('item')) for x in lines_of(est_rec(R, num))]
                ok(any(STAMP in x for x in have_items) and (not desk_line or any('Waterproofing' in x for x in have_items)), f'and {num} with its lines', have_items)
            st = W.admin('status')
            ok(st.get('signins', {}).get('desktop', 0) >= 2, 'the desktop really signed out and in again', st.get('signins'))
    finally:
        try: W.admin('offline', device='phone', on=False)
        except Exception: pass
        if '--keep' not in sys.argv: W.stop()
    rep = {'run': RUN, 'role': ROLE, 'stamp': STAMP, 'estimate': num, 'steps': steps, 'fails': fails, 'checks': n}
    json.dump(rep, open(os.path.join(OUT, 'report.json'), 'w'), indent=1)
    md = [f'# Live journeys ({ROLE}, {time.strftime("%Y-%m-%d %H:%M")}, stamp {STAMP})\n', '| Step | Device | Taps | Seconds | Stuck |', '|---|---|---|---|---|']
    md += [f"| {s['step']} | {s['device']} | {s['taps']} | {s['seconds']} | {s.get('stuck') or s.get('error') or ''} |" for s in steps]
    md += ['', '## Failures', ''] + [f"- {f['check']}: {f['got']}" for f in fails]
    open(os.path.join(OUT, 'report.md'), 'w').write('\n'.join(md) + '\n')
    print(f'\nLIVE JOURNEYS {n} checks · {len(fails)} failed')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
