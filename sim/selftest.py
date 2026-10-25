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


def click_unit():
    """The click check's classifier on invented log lines (no server): each verdict it must give."""
    sys.path.insert(0, HERE)
    from referee import classify_clicks, click_summary
    L = lambda v, t, s, h, top='': {'view': v, 'title': t, 'sheet': s, 'hash': h, 'top': top, 'toastOpen': False, 'toast': ''}
    base = {'uid': 'u_chen', 'day': '2026-09-03', 'slot': 'work', 'ok': True}
    A = [dict(base, cmd='go', control='menu: Purchasing > Purchase Orders', device='desktop', land={'from': L('today', 'Today', '', 'a'), 'to': L('purchasing', 'Purchase Orders', '', 'b')}),
         dict(base, cmd='tap', control='Flagged Orders', kind='button', device='desktop', land={'from': L('purchasing', 'Purchase Orders', '', 'b'), 'to': L('purchasing', 'Purchase Orders', '', 'b')}),
         dict(base, cmd='tap', control='Deliveries', kind='button', device='phone', land={'from': L('purchasing', 'Purchase Orders', '', 'b'), 'to': L('home', 'Home', '', 'c')}),
         dict(base, cmd='back', control='back', device='phone', land={'from': L('home', 'Home', '', 'c'), 'to': L('purchasing', 'Purchase Orders', '', 'b')}),
         dict(base, cmd='tap', control='Save', kind='button', device='phone', changed=True, toasts=[], land={'from': L('purchasing', 'Purchase Orders', 'Edit PO', 'd'), 'to': L('purchasing', 'Purchase Orders', 'Edit PO', 'e')}),
         dict(base, cmd='tap', control='Issue PO', kind='button', device='phone', changed=True, toasts=['PO-2026-052 issued Open'], land={'from': L('purchasing', 'PO-2026-052', '', 'e'), 'to': L('purchasing', 'PO-2026-052', '', 'f')})]
    V = [r['verdict'] for r in classify_clicks(A)]
    check(V == ['landed', 'dead', 'wrong', 'landed', 'done', 'done'], f'click check: a menu go lands, a dead tap, a wrong landing backed out of, a save and an issue (verdicts {V})')
    S = click_summary(classify_clicks(A))
    check(S['totals']['phone']['silent'] == 1 and S['totals']['desktop']['dead'] == 1 and S['totals']['phone']['backtrack'] == 1,
          f"click check: phone and desktop apart (a silent save on the phone, the dead tap on the desktop, one back-track): {S['totals']}")


def main():
    keep = '--keep' in sys.argv
    os.makedirs(os.path.join(HERE, 'runs'), exist_ok=True)
    t0 = time.time()
    click_unit()
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
    check('P2-01 · mail' in str(w.get('raw') or w), 'Pilot 2 book: the prospect\'s first mail (P2-01) goes out with the morning')

    # ---- 1b. Pilot 2: the owner works the morning on his phone and puts the new prospect on file
    b = ctl('begin', 'u_owner', 'morning', '--device', 'phone', '--cap', '20')
    rc, out = act('u_owner', 'screen')
    check('(owner, phone)' in out.split('\n')[0], 'device: an office person\'s turn on the phone (the screen says so)')
    rc, out = act('u_owner', 'device', 'desktop')
    check(rc != 0 and 'does not have you switch' in out, 'device: switching is refused when the turn does not allow it')
    rc, out = act('u_owner', 'go', 'Sales')
    rc, out = act('u_owner', 'tap', 'New Lead')
    n = (re.findall(r'\[(\d+) New Lead\]', out) or [None])[-1]
    rc, out = act('u_owner', 'do', f'type "Name" "Nadia Okoro"; type "Email" "nadia.okoro@example.com"; type "Property" "88 Garfield Place"; pick "Source" "Email"; tap {n}')
    check('is a lead' in out, 'owner (phone): Nadia Okoro is on file as a lead')
    ctl('end')
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

    # ---- 5b. Pilot 2: the gated walk-through reaches the owner; he wins the lead, starting at his desk, then on his phone
    wr = str(w.get('raw') or w)
    check(re.search(r'chains opened:.*P2-03', wr) and 'P2-03 · situation · told u_owner' in wr,
          f"chains: the walk-through (P2-03) opened once the lead was on file and went to the owner ({(re.findall(r'chains opened:[^\n]*', wr) or ['none'])[0]})")
    ctl('begin', 'u_owner', 'work1', '--switch', '--cap', '20')
    rc, out = act('u_owner', 'news')
    check('Nadia Okoro' in out, 'owner: the walk-through is in his news')
    rc, out = act('u_owner', 'go', 'Sales')
    check('(owner)' in out.split('\n')[0], 'device: the plan-less default puts the owner on his desktop')
    rc, full = act('u_owner', 'screen', '--full')
    check('the first screen ends here' in full, 'the screen marks where the first screen ends (the five-second test)')
    rc, out = act('u_owner', 'tap', 'Sales')   # the page's own tab, already open: nothing happens (the click check's dead tap)
    rc, out = act('u_owner', 'device', 'phone')
    check(rc == 0 and '(owner, phone)' in out, 'device: a turn with --switch picks up the phone mid-turn (same page, same company)')
    rc, out = act('u_owner', 'find', 'Nadia Okoro')
    r0 = row_before(out, r'Nadia Okoro')
    rc, out = act('u_owner', 'do', f'tap {r0}; tap "Convert to Opportunity"; tap "Convert"; tap "Closed Won"; tap "Close as Won"')
    check('is a client' in out, 'owner (phone): the lead is won and Nadia Okoro is a client')
    ctl('end')
    ctl('cost', 'u_owner', '--tokens', '123456', '--tool-uses', '9', '--ms', '61000')

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
    # ---- 9. Pilot 2: the new events scored apart, the click check per device, the device on every action, the cost
    S = L.get('sets') or {}
    check(bool(S.get('pilot1_events')) and bool(S.get('pilot2_events')), f"referee: Pilot 1 events and all events apart ({L.get('line_sets')})")
    check(ev.get('P2-01', {}).get('verdict') == 'on time' and ev.get('P2-03', {}).get('verdict') == 'on time',
          f"referee: the prospect on file and made a client, both on time, end to end through the screens (P2-01 {ev.get('P2-01', {}).get('verdict')}, P2-03 {ev.get('P2-03', {}).get('verdict')})")
    check('P2-04' in ev and 'P2-05' not in ev, 'chains: the estimate expectation (P2-04) opened with the client; the acceptance (P2-05) waits for an estimate')
    T = (L.get('clicks') or {}).get('totals') or {}
    check(T.get('phone', {}).get('taps', 0) > 0 and T.get('desktop', {}).get('taps', 0) > 0, f"click check: taps counted on the phone and the desktop apart ({L.get('line_clicks')})")
    check(any(r['verdict'] == 'dead' and r['device'] == 'desktop' and r['label'] == 'Sales' for r in L.get('click_rows') or []),
          'click check: the tap on the tab already open is a dead tap, on the desktop')
    check(any(r['verdict'] in ('landed', 'done') and r['device'] == 'phone' and r['uid'] == 'u_owner' for r in L.get('click_rows') or []),
          'click check: the owner\'s phone taps landed where their labels said')
    mine = [x for x in acts if (x.get('uid') or '').startswith('u_')]
    check(all(x.get('device') in ('phone', 'desktop') for x in mine), f'every action logs its device ({len(mine)} lines)')
    C = [json.loads(x) for x in open(os.path.join(RD, 'cost.jsonl'))]
    check(len(C) >= 5 and {'phone', 'desktop'} <= {c.get('device') for c in C} and all(c.get('calls', 0) >= 0 and 'est_processed' in c for c in C if c.get('uid', '').startswith('u_')),
          f'cost: one line per turn with calls, characters and the estimate ({len(C)} turns)')
    md = open(os.path.join(RD, 'cost.md')).read()
    check('123,456' in md and any(os.path.exists(os.path.join(RD, f'cost_{d}.json')) for d in ('2026-09-03', '2026-09-04')),
          'cost: the conductor\'s measured tokens reach cost.md and the per-day file')


if __name__ == '__main__':
    sys.exit(main())
