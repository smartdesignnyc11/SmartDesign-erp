"""sim/selftest.py: a scripted mini-day through the agent-month harness, with no LLM (BACKLOG §1.17).

Two to four personas act ONLY through sim/act, as an agent would, reading the numbered controls off their own
screens. It proves the harness, not the app:
  1. the toolkit refuses database and code access, and a person cannot act out of turn;
  2. shared state across pages: the foreman's request (her phone page) is on the coordinator's screen (his
     desktop page), and the PO he makes is what the foreman receives;
  3. the world: the PO goes out by mail, the supplier confirms, the truck comes (a situation for the foreman),
     the invoice follows by mail, and the card charge lands on the next morning's statement;
  4. the coordinator enters the bill from his Inbox; the controller imports the statement through Banking and
     confirms the match;
  5. resume: the server is stopped mid-day and resumed from its snapshot, and the PO is still there;
  6. the referee scores the day, including the find-it-again failure this script provokes on purpose (the
     statement import is only ever named in a toast), and the PERSIST reload check finds nothing lost.

    python3 sim/selftest.py            # about 5-10 minutes; prints PASS/FAIL per check and exits 1 on any FAIL
    python3 sim/selftest.py --keep     # keep the run directory (sim/runs/selftest-*) for inspection
"""
import json, os, re, shutil, subprocess, sys, time, urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RUN = f'selftest-{int(time.time())}'
ENV = dict(os.environ, SIM_RUN=RUN)
RD = os.path.join(HERE, 'runs', RUN)
FAILS, N = [], [0]
PROC = [None]


def check(ok, msg):
    N[0] += 1
    print(('PASS ' if ok else 'FAIL ') + msg, flush=True)
    if not ok: FAILS.append(msg)
    return ok


def act(uid, *a):
    if any(x is None for x in a): raise Stop(f'{uid}: the control for {a[0]} was not on the screen')
    p = subprocess.run([os.path.join(HERE, 'act'), uid, *a], capture_output=True, text=True, env=ENV, timeout=600)
    return p.returncode, p.stdout


def ctl(*a):
    p = subprocess.run([os.path.join(HERE, 'simctl'), *a], capture_output=True, text=True, env=ENV, timeout=1800)
    try: return json.loads(p.stdout)
    except Exception: return {'raw': p.stdout, 'err': p.stderr}


def start(resume=False):
    log = open(os.path.join(HERE, 'runs', f'{RUN}.server.log'), 'a')
    cmd = [sys.executable, os.path.join(HERE, 'server.py'), '--run', RUN] + (['--resume'] if resume else [])
    PROC[0] = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=ENV)
    t0 = time.time()
    while time.time() - t0 < 600:
        if PROC[0].poll() is not None: raise SystemExit('the server stopped: see ' + log.name)
        if os.path.exists(os.path.join(RD, 'server.json')) and 'ready' in open(log.name).read().split('starting the browser')[-1]: return round(time.time() - t0)
        time.sleep(2)
    raise SystemExit('the server did not come up')


def stop():
    ctl('stop')
    try: PROC[0].wait(timeout=60)
    except Exception: PROC[0].kill()


MARK = re.compile(r'\[(\d+)(?: (?:tab|link))? ([^\]]*)\]')


ROW = re.compile(r'\[(\d+)(?: tab)?\] ([^\[\n]+)')


class Stop(Exception): pass


def num(text, rx):
    """the number of the first button/link/tab whose label matches (a labelled control, or a row: "[n] its text")"""
    for m in MARK.finditer(text):
        if re.search(rx, m.group(2), re.I) and not m.group(2).startswith(('input ', 'select ', 'text ', 'check ', 'date ', 'file ')): return m.group(1)
    for m in ROW.finditer(text):
        if re.search(rx, m.group(2).strip(), re.I): return m.group(1)
    return None


def field(text, kind, label_rx):
    m = re.search(r'\[(\d+) ' + kind + r' "' + label_rx, text, re.I)
    return m.group(1) if m else None


def row_before(text, rx):
    """the row marker of the record whose text matches (the [n] at the start of its first line)"""
    L = text.splitlines()
    for i, l in enumerate(L):
        if re.search(rx, l):
            for j in range(i, max(-1, i - 4), -1):
                ms = re.findall(r'\[(\d+)\]', L[j])
                if ms: return ms[-1]
    return None


def main():
    keep = '--keep' in sys.argv
    os.makedirs(os.path.join(HERE, 'runs'), exist_ok=True)
    t0 = time.time()
    secs = start()
    print(f'world up in {secs}s (run {RUN})', flush=True)
    try:
        flow()
    except Stop as e:
        check(False, f'the flow stopped: {e}')
    finally:
        try: stop()
        except Exception: pass
    print(f"\n{N[0] - len(FAILS)}/{N[0]} checks passed in {round(time.time() - t0)}s" + (f" · run kept at {RD}" if keep else ''))
    if not keep and not FAILS:
        shutil.rmtree(RD, ignore_errors=True)
        try: os.remove(os.path.join(HERE, 'runs', f'{RUN}.server.log'))
        except Exception: pass
    elif FAILS: print(f'run kept for inspection at {RD}')
    return 1 if FAILS else 0


def flow():
    # ---- 1. the toolkit refuses what a person cannot do
    rc, out = act('u_angel', 'eval', 'DB.pos')
    check(rc == 3 and 'refused' in out, 'act refuses "eval" (no JavaScript)')
    rc, out = act('u_angel', 'db')
    check(rc == 3 and 'refused' in out, 'act refuses "db" (no database)')
    port = json.load(open(os.path.join(RD, 'server.json')))['port']
    raw = json.loads(urllib.request.urlopen(urllib.request.Request(f'http://127.0.0.1:{port}/act', data=json.dumps(
        {'uid': 'u_angel', 'cmd': 'evaluate', 'args': ['DB']}).encode(), headers={'Content-Type': 'application/json'})).read())
    check(not raw.get('ok') and 'refused' in raw.get('text', ''), 'the server refuses a raw "evaluate" sent around the CLI')
    try:
        urllib.request.urlopen(urllib.request.Request(f'http://127.0.0.1:{port}/admin', data=b'{"cmd":"status"}', headers={'Content-Type': 'application/json'}))
        check(False, 'admin without the run token is refused')
    except urllib.error.HTTPError as e:
        check(e.code == 403, 'admin without the run token is refused')
    ctl('party', 'Brooklyn Lumber', json.dumps({'reply_p': 1, 'delay': [0, 0], 'ship': [0], 'pay': 'card', 'late_p': 0}))
    w = ctl('world', 'morning', '--no-watchers')

    # ---- 2. the foreman asks for material on her phone
    ctl('begin', 'u_angel', 'morning', '--cap', '15')
    rc, out = act('u_chen', 'screen')
    check(rc != 0 and 'turn' in out, 'a person cannot act during someone else\'s turn')
    rc, out = act('u_angel', 'go', 'Ask')
    n = num(out, r'^Materials or a Tool')
    check(bool(n), 'foreman: the Ask tab offers Materials or a Tool')
    # a batch: four steps in one call, targets by label, only the lines with "Send" back
    rc, out = act('u_angel', 'do', 'tap "Materials or a Tool"; pick "What Is It For" "Framing"; type "What Do You Need" "8 sheets 3/4 plywood (selftest)"; tap "Next — Check the List"',
                  '--find', 'Send')
    check(rc == 0 and out.startswith('do: 4 of 4 steps') and 'Send 1 Line' in out and len(out) < 1500,
          f'do: a four-step batch by label in one call, one compact result ({len(out)} characters)')
    rc, out = act('u_angel', 'do', 'tap "No Such Button"; tap "Send 1 Line"')
    check(rc != 0 and 'do: 0 of 2 steps' in out and 'STOPPED' in out, 'do: stops at the first step whose target is not on the screen, and does not run the rest')
    rc, out = act('u_angel', 'tap', 'Send 1 Line')
    check('Request sent' in out, 'foreman: the request is sent (tap by label; toast)')
    ctl('end')

    # ---- 3. the coordinator sees it on his own page and buys it
    ctl('begin', 'u_chen', 'morning', '--cap', '30')
    rc, out = act('u_chen', 'find', 'plywood (selftest)')
    check('plywood (selftest)' in out, 'shared state: the foreman\'s request is on the coordinator\'s Home (another page)')
    rc, out = act('u_chen', 'go', 'Purchasing > Purchase Orders')
    rc, out = act('u_chen', 'tap', num(out, r'^New PO$'))
    rc, full = act('u_chen', 'screen', '--full')
    m = re.search(r'\[(\d+) check "[^"]*" (?:on|off)\] \| 2\. Framing', full)
    check(bool(m), 'coordinator: the estimate\'s Framing line is in the New PO sheet')
    c = int(m.group(1))
    act('u_chen', 'tap', str(c))
    for i, v in enumerate(['8', 'sheet', '62', 'Brooklyn Lumber'], 1): act('u_chen', 'type', str(c + i), v)
    rc, full = act('u_chen', 'screen', '--full')
    rc, out = act('u_chen', 'tap', num(full, r'^Create the Purchase Orders'))
    po = (re.findall(r'Purchase Order (PO-\d{4}-\d+)', out) or [''])[0]
    check(bool(po) and 'created' in out, f'coordinator: {po or "no PO"} created in draft from the line')
    rc, full = act('u_chen', 'screen', '--full')
    rc, out = act('u_chen', 'tap', num(full, r'^Issue PO'))
    check('issued' in out, f'coordinator: {po} issued')
    rc, full = act('u_chen', 'screen', '--full')
    rc, out = act('u_chen', 'tap', num(full, r'^Draft Email to Vendor'))
    act('u_chen', 'type', field(out, 'input', 'To'), 'Brooklyn Lumber <orders@brooklynlumber.example>')
    rc, out = act('u_chen', 'tap', num(out, r'^Save to Mailbox Drafts'))
    rc, out = act('u_chen', 'mail', 'drafts')
    k = next((ln.split('.')[0] for ln in out.splitlines() if po in ln), None)
    rc, out = act('u_chen', 'mail', 'senddraft', k or '1')
    check('sent to Brooklyn Lumber' in out, 'coordinator: the PO goes to the supplier from his mailbox')
    ctl('end')

    # ---- 4. a usage pause: the world stops and resumes from its snapshot
    v0 = ctl('status').get('version')
    stop()
    secs = start(resume=True)
    v1 = ctl('status').get('version')
    ctl('begin', 'u_chen', 'work1', '--cap', '5')
    rc, out = act('u_chen', 'go', 'Purchasing > Purchase Orders')
    rc, out = act('u_chen', 'find', po)
    check(v1 == v0 and po in out, f'resume: back in {secs}s at version {v1}, and {po} is still on the coordinator\'s screen')
    ctl('end')

    # ---- 5. the world: the supplier confirms and the truck comes; the foreman receives
    w = ctl('world', 'work1', '--no-watchers')
    ctl('begin', 'u_angel', 'work1', '--cap', '10')
    rc, out = act('u_angel', 'news')
    check(f'delivered {po}' in out, 'world: the delivery reaches the foreman as something that happened on site')
    act('u_angel', 'go', 'Today')
    rc, out = act('u_angel', 'find', po)
    n = num(out, r'^Check In')
    check(bool(n), f'foreman: {po} is on her Today with Check In')
    rc, out = act('u_angel', 'tap', n)
    rc, out = act('u_angel', 'tap', num(out, r'^Record Receipt'))
    check('received' in out, f'foreman: {po} received in full (toast)')
    ctl('end')

    # ---- 6. the bill arrives by mail; the coordinator enters it from his Inbox
    w = ctl('world', 'work2', '--watchers')
    ctl('begin', 'u_chen', 'work2', '--cap', '15')
    rc, out = act('u_chen', 'mail')
    inv = (re.findall(r'Invoice ([A-Z]{2,4}-\d+) for ' + re.escape(po), out) or [''])[0]
    check(bool(inv), f'world: the supplier\'s invoice {inv} is in the coordinator\'s mailbox')
    rc, out = act('u_chen', 'go', 'Home > Inbox')
    rc, out = act('u_chen', 'tap', num(out, r'^To Decide'))
    rc, full = act('u_chen', 'screen', '--full')
    rc, out = act('u_chen', 'tap', row_before(full, r'Invoice ' + re.escape(inv)))
    rc, out = act('u_chen', 'find', 'Vendor bill')
    rc, out = act('u_chen', 'tap', num(out, r'^Apply$'))
    check('bill' in out.lower() and po in out, f'coordinator: {inv} entered as a bill against {po}')
    ctl('end')

    # ---- 7. next morning: the card line comes on the statement; the controller imports and matches it
    a = ctl('advance')
    check(bool(a.get('day')), f"the day advances to {a.get('day')} (the day's hooks ran: {len((a.get('hooks') or {}).get('ran') or [])})")
    w = ctl('world', 'morning', '--no-watchers')
    ctl('begin', 'u_controller', 'morning', '--cap', '25')
    rc, out = act('u_controller', 'mail')
    k = next((ln.split('.')[0] for ln in out.splitlines() if 'Amex 1009: new activity' in ln and a.get('day', 'x') in ln), None)
    rc, out = act('u_controller', 'mail', 'read', k or '1')
    f = (re.findall(r'-> (\S+\.csv)', out) or [''])[0]
    check(bool(f) and os.path.exists(f), 'controller: the bank\'s statement CSV is attached and saved for upload')
    act('u_controller', 'go', 'Accounting > Banking')
    rc, out = act('u_controller', 'find', 'Import Statement')
    rc, out = act('u_controller', 'tap', num(out, r'^Import Statement'))
    act('u_controller', 'pick', field(out, 'select', 'Account'), 'Amex')
    rc, out = act('u_controller', 'upload', field(out, 'file', ''), f)
    rc, out = act('u_controller', 'tap', num(out, r'^Import \d+ Line'))
    check('imported' in out, 'controller: the statement imports through Banking > Import Statement')
    rc, out = act('u_controller', 'find', 'Categorize & Match')
    act('u_controller', 'tap', num(out, r'^Categorize & Match'))
    rc, out = act('u_controller', 'find', 'BROOKLYN LUMBER')
    m = re.search(r'BROOKLYN LUMBER\$?[\d,.]*[^\n]*\n(?:[^\n]*\n){0,3}?\[(\d+) Confirm\]', out)
    if m:
        rc, out2 = act('u_controller', 'tap', m.group(1))
        check(rc == 0, f'controller: the card line is confirmed against its match ({(re.findall(r"Toast: ([^\n]*)", out2) or [""])[0][:80]})')
    else:
        check(False, 'controller: a proposed match for the BROOKLYN LUMBER card line is on Banking')
    ctl('end')

    # ---- 8. the referee
    r = ctl('referee')
    L = json.load(open(os.path.join(RD, 'ledger.json')))
    print('   ' + r.get('line', str(r)))
    ev = {e['id']: e for e in L['events']}
    dl = [e for e in L['events'] if e['check'] == 'poStatus']
    check(any(e['verdict'] == 'on time' for e in dl), 'referee: the delivery is scored received on time')
    bl = [e for e in L['events'] if e['check'] == 'bill' and inv and inv in e['what']]
    check(any(e['verdict'] in ('on time', 'open') and e['done'] for e in bl), f'referee: {inv} is scored entered against {po}')
    fails = L['fia']['failures']
    check(any(x['name'].endswith('.csv') for x in fails), 'referee: the deliberate find-it-again failure (the import named only in a toast) is caught: '
          + '; '.join(f"{x['uid']} {x['name']}" for x in fails[:3]))
    check(L['fia']['found'] >= 3, f"referee: creates seen by their creator are counted ({L['fia']['found']})")
    check(len(L['standard']['refused']) >= 2, f"referee: the refused attempts are on the record ({len(L['standard']['refused'])})")
    check(bool(L['places']['rows']), f"referee: places-to-look counted per person and kind ({len(L['places']['rows'])} person-days)")
    check(bool(L['tie']['accounts']), 'referee: the bank tie-out ran (' + '; '.join(f"{k} {v['erpLines']} lines, {len(v['notImported'])} not imported" for k, v in L['tie']['accounts'].items()) + ')')
    p = ctl('persist')
    print('   ' + str(p.get('line')))
    check(p.get('n_lost') == 0, 'PERSIST: nothing lost after saveNow and a reload')
    acts = [json.loads(x) for x in open(os.path.join(RD, 'actions.jsonl'))]
    check(all(('day' in x and 'slot' in x) for x in acts) and any(x.get('creates') for x in acts), f'the action log has who, day, slot, screen, control, result and creates ({len(acts)} lines)')


if __name__ == '__main__':
    sys.exit(main())
