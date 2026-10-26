"""sim/selftest_gaps.py: the units for what closed the gaps between an expert and an employee (Alan 10-26), no browser,
no network (run by `python3 sim/selftest.py --unit`):
  - the page as a picture: one picture per new screen per turn, a new one on the other device, the path at the end;
  - memory: what a person said and promised is kept in files/<uid>/said.md; the turn prompt points at it;
  - the voicer: the facts of a reply, kept or not in a voiced one, invented ones caught, styles seeded and allowed,
    and the template (with the reason) when the live model cannot be reached;
  - live mode: the reader without the local world's timers, the roles, the live prompt;
  - the run ledger: a green suite on the same build is skipped, a red one is not.
"""
import asyncio, json, os, shutil, subprocess, sys, tempfile, types

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
FAILS, N = [], [0]


def check(ok, msg):
    N[0] += 1
    print(('PASS ' if ok else 'FAIL ') + msg, flush=True)
    if not ok: FAILS.append(msg)
    return ok


class FakePage:
    def __init__(self): self.fp = 'today | Today |  |  | '
    async def evaluate(self, js, *a): return self.fp


def picture_unit(tmp):
    import server as SV
    shots = []
    fake = types.SimpleNamespace(pictured={}, device={'u_alan': False}, dir=tmp, state={'day': '2026-09-03', 'actions': 7}, logs=[])
    fake.clock_str = lambda: '10:02'
    async def shot(uid, path, jpeg=False): shots.append((path, jpeg)); open(path, 'wb').write(b'\xff\xd8jpeg')
    fake.shot = shot
    fake.log = lambda rec: fake.logs.append(rec)
    pg, t = FakePage(), {'uid': 'u_alan'}
    run = lambda out: (asyncio.run(SV.Sim.picture(fake, 'u_alan', pg, t, out)), out)[1]
    o1 = run({'ok': True, 'text': 'screen one'})
    check(o1['text'].splitlines()[-1].startswith('Screen picture: ' + os.path.join(tmp, 'shots', 'u_alan')) and shots[-1][1] and shots[-1][0].endswith('_desktop.jpg'),
          'picture: a new screen ends the result with "Screen picture: <path>", a JPEG under shots/<uid>/')
    o2 = run({'ok': True, 'text': 'screen one again'})
    check('Screen picture' not in o2['text'] and len(shots) == 1, 'picture: the same screen in the same turn is not pictured twice')
    fake.device['u_alan'] = True
    o3 = run({'ok': True, 'text': 'the same page on the phone'})
    check('Screen picture' in o3['text'] and shots[-1][0].endswith('_phone.jpg'), 'picture: the same page on the other device is a new screen to the eye')
    pg.fp = 'billing | Estimate EST-2026-015 | Line 1 |  | '
    o4 = run({'ok': True, 'text': 'a sheet'})
    check('Screen picture' in o4['text'] and t.get('pictures') == 3, f"picture: a new sheet is pictured; the turn counts its pictures ({t.get('pictures')})")
    check(run({'ok': False, 'text': ''})['text'] == '', 'picture: an action with no screen gets no picture')
    check({'tap', 'go', 'back', 'screen', 'device'} <= SV.PICTURE_CMDS and 'mail' not in SV.PICTURE_CMDS, 'picture: taps, menu goes, back, screen and device switches are pictured; mail is not')


def memory_unit(tmp):
    import server as SV
    fake = types.SimpleNamespace(dir=tmp, state={'day': '2026-09-03'})
    fake.clock_str = lambda: '13:37'
    SV.Sim.said_line(fake, 'u_alan', 'you mailed Wren Ashby: "Radiator": I will price it by Friday')
    SV.Sim.said_line(fake, 'u_chen', 'Alan (PM) called you and said: "tile quantities by Thursday noon"')
    SV.Sim.said_line(fake, 'nobody', 'not a person')
    a = open(os.path.join(tmp, 'files', 'u_alan', 'said.md')).read()
    check(a.startswith('- 2026-09-03 13:37: you mailed Wren Ashby') and os.path.exists(os.path.join(tmp, 'files', 'u_chen', 'said.md'))
          and not os.path.exists(os.path.join(tmp, 'files', 'nobody')), 'memory: what a person said and promised goes in their said.md, dated, both sides of a call')
    tp = open(os.path.join(HERE, 'turn_prompt_p3.md')).read()
    check('said.md' in tp and 'news.md' in tp and '## Open promises' in tp and 'last `## Open promises` list' in tp,
          'memory: the turn prompt reads news.md and said.md, the last Open promises list, and ends each turn by writing it')


QUOTE = """Hi Chen,

Thanks for the request. Our quote for RFQ-2026-031:

Line | Item | Qty | Unit Price | Extended
L1 | 2x4 studs 8ft | 120 pcs | $6.10 | $732.00
L2 | 2x6 joists 12ft | 24 pcs | $11.20 | $268.80
L3 | Type X gypsum 5/8 | 60 sheets | $1,695.00 | $1,044.00

Free delivery to site
Lead time: 2 working days
Prices valid 30 days"""


def voicer_unit():
    import voicer as V
    F = V.facts(QUOTE)
    check(F[:4] == ['RFQ-2026-031', '120 pcs', '$6.10', '$732.00'] and '$1,695.00' in F and '2 working days' in F and '30 days' in F,
          f'voicer: the facts of a quote in reading order, the typo price kept as a fact ({len(F)} facts)')
    check(V.facts('Move it, please: under the window. Wren') == ['Move it'] and V.facts('Tuesday the 8th works for us') == ['Tuesday', 'the 8th'],
          'voicer: a decision with no figures keeps its opening words; a day and a date word are facts')
    good = QUOTE.replace('Thanks for the request.', 'Thanks Chen, here you go.').replace('$1,695.00', '$1695.00')
    check(V.check(QUOTE, good)[0], 'voicer: the same facts in other words (1695.00 for 1,695.00) pass')
    ok, miss, inv = V.check(QUOTE, QUOTE.replace('$11.20', '$11.00'))
    check(not ok and '$11.20' in miss and '$11.00' in inv, f'voicer: a changed price is a dropped fact and an invented one ({miss}, {inv})')
    ok, miss, inv = V.check(QUOTE, QUOTE + '\nWe can also do the plywood at $55.00.')
    check(not ok and inv == ['$55.00'], 'voicer: a price the template did not have is caught')
    check(V.kept('2026-09-10', 'ships Sept 10') and V.kept('2026-09-10', 'ships 9/10') and not V.kept('2026-09-10', 'ships 9/11'), 'voicer: a date may be written the way people write it')
    rec = {'id': 'R0003', 'party': {'name': 'Brooklyn Lumber', 'quotes': {'form': 'table'}}, 'template_reply': QUOTE, 'att': []}
    S = [V.style_for(dict(rec, id=f'R{i:04d}'), 42) for i in range(300)]
    check(V.style_for(rec, 42) == V.style_for(rec, 42) and 'different_format' not in S and len(set(S)) == 5,
          f'voicer: styles are the same per seed and reply, varied across replies, and a planted quote keeps its book format ({sorted(set(S))})')
    S2 = [V.style_for({'id': f'X{i}', 'party': {'name': 'Gowanus'}, 'template_reply': QUOTE, 'att': ['q.pdf']}, 42) for i in range(300)]
    check('partial' not in S2 and 'different_format' in S2, 'voicer: a reply with an attachment is never split; others may change layout')
    old = os.environ.pop('SIM_AI_TOKEN_FILE', None), os.environ.pop('SIM_AI_TOKEN', None)
    try:
        r = V.voice(rec, 42, 'plain')
    finally:
        if old[0]: os.environ['SIM_AI_TOKEN_FILE'] = old[0]
        if old[1]: os.environ['SIM_AI_TOKEN'] = old[1]
    check(not r['ok'] and r['text'] == QUOTE and 'token' in r['why'], f"voicer: with no live model the template goes out and says why ({r['why']})")
    d = tempfile.mkdtemp(); os.makedirs(os.path.join(d, 'world'))
    V.log(d, {'id': 'R1', 'party': 'Brooklyn Lumber', 'kind': 'quote', 'style': 'plain', 'ok': True, 'why': ''})
    V.log(d, {'id': 'R2', 'party': 'Wren Ashby', 'kind': 'answer', 'style': 'terse', 'ok': False, 'why': 'a fact was dropped or invented', 'missing': ['Move it']})
    md = V.ledger_md(d)
    check('1 replies voiced, 1 sent as the template' in md and 'missing Move it' in md, 'voicer: the ledger says which replies went out as the template and why')
    shutil.rmtree(d, ignore_errors=True)


def live_unit():
    import live as L, server as SV
    check(L.LIVE_TOOLS != SV.PAGE_TOOLS and 'clearInterval(gsTimerId)' not in L.LIVE_TOOLS, 'live: the reader keeps the live app\'s own timers')
    check(set(L.ROLES) == {'owner', 'pm', 'coord', 'billing', 'controller'} and L.ROLES['pm'] == ('pm', 'u_alan') and L.ROLES['owner'][0] == 'loopowner',
          'live: the five loop roles map to their QA accounts and people')
    tp = open(os.path.join(HERE, 'turn_prompt_live.md')).read()
    keys = {'name', 'role', 'weekday', 'clock', 'device', 'site', 'live', 'uid', 'root', 'briefing', 'diary', 'cap', 'run'}
    import re
    used = set(re.findall(r'\{(\w+)\}', tp))
    check(used <= keys and all(x in tp for x in ('No world', 'No clock pin', 'Real sign-in and sync')),
          f'live: the live prompt fills every placeholder and says what is different ({sorted(used - keys)})')
    pt = open(os.path.join(HERE, 'page_tools.js')).read()
    check("getElementById('fatal')" in pt and '.ct-sheet' in pt and 'COVERS' in pt, 'reader: the red start banner and any full-screen sheet (the phone line editor) are read')


def ledger_unit():
    d = tempfile.mkdtemp()
    env = dict(os.environ, SD_RUNS_LEDGER=os.path.join(d, 'runs.md'))
    t = os.path.join(ROOT, 'tests')
    r1 = subprocess.run([os.path.join(t, 'run_once.sh'), 'bash', '-c', 'echo "ALL PASS (1)"'], cwd=t, env=env, capture_output=True, text=True)
    r2 = subprocess.run([os.path.join(t, 'run_once.sh'), 'bash', '-c', 'echo "ALL PASS (1)"'], cwd=t, env=env, capture_output=True, text=True)
    r3 = subprocess.run([os.path.join(t, 'run_once.sh'), 'bash', '-c', 'echo "1 FAILED"; exit 4'], cwd=t, env=env, capture_output=True, text=True)
    r4 = subprocess.run([os.path.join(t, 'run_once.sh'), 'bash', '-c', 'echo "1 FAILED"; exit 4'], cwd=t, env=env, capture_output=True, text=True)
    led = open(os.path.join(d, 'runs.md')).read() if os.path.exists(os.path.join(d, 'runs.md')) else ''
    check(r1.returncode == 0 and 'ALL PASS' in r1.stdout and r2.returncode == 0 and 'run_once: skipped' in r2.stdout and 'ALL PASS (1)' in r2.stdout,
          'ledger: a suite green on this build is skipped the second time, with the earlier result')
    check(r3.returncode == 4 and r4.returncode == 4 and 'skipped' not in r4.stdout and led.count('| FAIL |') == 2 and led.count('| PASS |') == 1,
          'ledger: a red suite is never skipped; every run is a row with its result and last line')
    shutil.rmtree(d, ignore_errors=True)


def picture_cap_unit(tmp):
    """the picture cap by the kind of turn (round one: the owner's page walk ran out of its 8 at 10:29)"""
    import server as SV
    check(SV.picture_cap({}) == SV.PICTURE_CAP == 8 and SV.picture_cap({'kind': 'journey'}) == 8, 'picture cap: a journey turn keeps 8 (SIM_PICTURE_CAP)')
    check(SV.picture_cap({'kind': 'pages'}) == 30, 'picture cap: a page walk (begin --kind pages) gets 30 (SIM_PICTURE_CAP_PAGES)')
    check(SV.picture_cap({'kind': 'pages', 'picture_cap': 12}) == 12, 'picture cap: --pictures N sets one turn\'s cap')
    fake = types.SimpleNamespace(pictured={}, device={'u_owner': False}, dir=tmp, state={'day': '2026-09-03', 'actions': 1}, logs=[])
    fake.clock_str = lambda: '10:29'
    async def shot(uid, path, jpeg=False): open(path, 'wb').write(b'\xff\xd8jpeg')
    fake.shot = shot; fake.log = lambda rec: fake.logs.append(rec)
    pg, t = FakePage(), {'uid': 'u_owner', 'kind': 'pages', 'pictures': 8}
    out = {'ok': True, 'text': 'the ninth page'}; asyncio.run(SV.Sim.picture(fake, 'u_owner', pg, t, out))
    check('Screen picture' in out['text'] and t['pictures'] == 9, 'picture cap: a page walk is still pictured after 8')
    t2 = {'uid': 'u_owner', 'pictures': 8}; pg.fp = 'other | Other |  |  | '; out2 = {'ok': True, 'text': 'the ninth screen'}
    asyncio.run(SV.Sim.picture(fake, 'u_owner', pg, t2, out2))
    check('Screen picture' not in out2['text'] and 'this turn\'s 8 are used' in out2['text'], 'picture cap: a journey turn stops at 8 and says so')
    sc = open(os.path.join(HERE, 'simctl')).read()
    check("'--kind'" in sc and "'--pictures'" in sc, 'picture cap: simctl begin takes --kind and --pictures')


READER_JS = r"""
const src = require('fs').readFileSync(process.argv[2], 'utf8');
const noop = () => {};
global.window = { addEventListener: noop }; global.addEventListener = noop; global.innerWidth = 1440; global.innerHeight = 900;
global.document = { getElementById: () => null, querySelectorAll: () => [], querySelector: () => null, body: { children: [] }, addEventListener: noop };
global.MutationObserver = function () { this.observe = noop; };
global.getComputedStyle = () => ({ display: 'block', visibility: 'visible', opacity: '1', position: 'static' });
eval(src)();
const S = window.__SIM, C = labels => labels.map(l => ({ l }));
const lines = ['This Period % \u2014 1', 'This Period % \u2014 10', 'This Period % \u2014 11', 'This Period % \u2014 12', 'Stored \u2014 1'];
const out = {
  exact: S.matchLabel('This Period % \u2014 1', C(lines)).hit,
  ten: S.matchLabel('This Period % \u2014 10', C(lines)).hit,
  prefix: S.matchLabel('This Period %', C(lines)),
  count: S.matchLabel('Approvals', C(['Approvals 33', 'Approve'])).hit,
  stale: S.matchLabel('Approvals 32', C(['Approvals 33', 'Approve'])).hit,
  twice: S.matchLabel('Save', C(['Save', 'Save'])),
  part: S.matchLabel('Quote', C(['Save the Quote'])).hit,
  none: S.matchLabel('Delete', C(['Save'])),
  me: [S.isMe(''), S.isMe('Billing'), S.isMe('System')],
};
console.log(JSON.stringify(out));
"""


def reader_unit():
    """the in-page reader's label matching and attribution, run under node with a stub page (no browser)"""
    pt = os.path.join(HERE, 'page_tools.js')
    js = os.path.join(tempfile.mkdtemp(), 'reader_unit.js'); open(js, 'w').write(READER_JS)
    r = subprocess.run(['node', js, pt], capture_output=True, text=True)
    if not check(r.returncode == 0, f'reader: page_tools.js loads under node ({r.stderr.strip()[-200:]})'): return
    o = json.loads(r.stdout.strip().splitlines()[-1])
    one, ten = (o['exact'] or {}).get('l', ''), (o['ten'] or {}).get('l', '')
    check(one.endswith(' 1') and ten.endswith(' 10'), 'reader: "This Period % - 1" matches line 1 only, not lines 10 to 12 (its number is not a count)')
    check(not o['prefix'].get('hit') and '4 labels' in o['prefix'].get('why', ''), f"reader: a prefix that starts several labels is refused, naming them ({o['prefix'].get('why', '')[:80]})")
    check((o['count'] or {}).get('l') == 'Approvals 33' and (o['stale'] or {}).get('l') == 'Approvals 33', 'reader: a menu count after a label is still the same control')
    check(not o['twice'].get('hit') and '2 controls are labelled' in o['twice'].get('why', ''), 'reader: two controls with one label are refused (use the number)')
    check((o['part'] or {}).get('l') == 'Save the Quote' and not o['none'].get('hit'), 'reader: a part of one label still finds it; no match is no match')
    pt_src = open(pt).read()
    check('FLOATS' in pt_src and '.drawer.on' in pt_src and 'S.modal' in pt_src and 'is under the open sheet' in pt_src,
          'reader: drawers and floating boxes at the top of the page are sheets; a tap under a covering sheet is refused')
    check(o['me'][0] is True and o['me'][2] is False, 'reader: a record with no maker is the actor\'s; one made by "System" or another account is not "you just created"')


def unit():
    tmp = tempfile.mkdtemp()
    try:
        picture_unit(tmp); picture_cap_unit(tmp); reader_unit(); memory_unit(tmp); voicer_unit(); live_unit(); ledger_unit()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    unit()
    print(f"\n{N[0] - len(FAILS)}/{N[0]} checks passed (the gaps' units)")
    sys.exit(1 if FAILS else 0)
