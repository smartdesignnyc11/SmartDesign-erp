"""sim/workshop.py: the Navigation and Pages Workshop at the end of the pilot (SmartDesign workspace only; Mercer &
Bond is out of scope). Prompts and the answer format: sim/workshop_nav.md.

    python3 sim/workshop.py usage            # runs/<run>/nav_usage.json from the action log (+ menus.json if captured)
    python3 sim/workshop.py prompt <uid>     # the filled expert prompt for one person
    python3 sim/workshop.py score            # group every finding across roles into runs/<run>/nav_workshop.md and
                                             # print the synthesis prompt that completes it

Usage comes from actions.jsonl, so it is exactly what each person did through `act`:
- pages: visits, taps and seconds spent on each page (seconds = agent wall time until their next action in the
  same turn, which includes their thinking; `act_s` = the toolkit's own time);
- trails: the pages visited in a row to finish one job, ended by an action whose toast or created record says
  something was done; with taps, seconds and back-tracks (a page already in the trail, or Back);
- top jobs: trails grouped by the first words of the finishing toast, with median taps and seconds;
- first looked: per kind of thing (owed, approve, money, a job's documents, a vendor, a client), the page each
  person first acted from, each day.
"""
import json, os, re, statistics, sys
from collections import Counter, OrderedDict, defaultdict
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KINDS = OrderedDict([
    ('approve', r'\b(approve|reject|decline|authori[sz]e|sign off|accept)\b'),
    ('money', r'\b(pay|paid|bill it|record payment|match|reconcile|categor|invoice|deposit|import|payroll|short-?pay|dispute|bank)\b'),
    ('documents', r'\b(document|drawing|sheet|plan|photo|file|submittal|spec|transcript|daily log)\b'),
    ('vendor', r'\b(vendor|supplier|po-\d|purchase order|quote|rfq|delivery|deliveries|receive)\b'),
    ('client', r'\b(client|portal|change order|co-\d|decision|selection|klein)\b'),
    ('owed', r'\b(done|complete|send|reply|answer|order|confirm|chase|got it|raise|request|task|acknowledge)\b'),
])
NAME_PAIRS = [('Purchasing', 'Buying'), ('Company', 'Office'), ('Design', 'Studio')]
NAV = ('go', 'tap', 'back', 'key', 'screen', 'scroll', 'find', 'type', 'pick', 'upload', 'photo', 'ask')


def run_dir():
    run = os.environ.get('SIM_RUN') or open(os.path.join(HERE, 'runs', '.current')).read().strip()
    return run, os.path.join(HERE, 'runs', run)


def ts(a):
    try: return datetime.fromisoformat(a['t']).timestamp()
    except Exception: return 0


def usage():
    run, d = run_dir()
    A = [json.loads(l) for l in open(os.path.join(d, 'actions.jsonl')) if l.strip()]
    menus = json.load(open(os.path.join(d, 'menus.json'))) if os.path.exists(os.path.join(d, 'menus.json')) else {}
    by = defaultdict(list)
    for a in A:
        if a.get('uid', '').startswith('u_') and a.get('cmd') in NAV: by[a['uid']].append(a)
    res = {}
    for uid, L in by.items():
        pages = defaultdict(lambda: {'visits': 0, 'taps': 0, 'seconds': 0.0, 'act_s': 0.0, 'controls': Counter()})
        first = defaultdict(Counter); seen_kind = set()
        trails, cur, prev_page = [], None, None
        for i, a in enumerate(L):
            src = a.get('screen') or '?'; dst = a.get('after') or src
            nxt = L[i + 1] if i + 1 < len(L) else None
            same_turn = nxt and nxt['day'] == a['day'] and nxt['slot'] == a['slot']
            gap = max(0.0, min(600.0, ts(nxt) - ts(a))) if same_turn else (a.get('ms') or 0) / 1000
            P = pages[src]; P['seconds'] += gap; P['act_s'] += (a.get('ms') or 0) / 1000
            if a['cmd'] in ('tap', 'key'):
                P['taps'] += 1
                if a.get('control'): P['controls'][str(a['control'])[:40]] += 1
            if dst != prev_page: pages[dst]['visits'] += 1
            prev_page = dst
            if cur is None or cur['day'] != a['day'] or cur['slot'] != a['slot']:
                cur = {'day': a['day'], 'slot': a['slot'], 'pages': [src], 'taps': 0, 'seconds': 0.0, 'backtracks': 0, 'done': ''}
            if a['cmd'] in ('tap', 'key', 'go', 'type', 'pick', 'upload', 'photo'): cur['taps'] += 1
            cur['seconds'] += gap
            if a['cmd'] == 'back': cur['backtracks'] += 1
            if dst != cur['pages'][-1]:
                if dst in cur['pages']: cur['backtracks'] += 1
                cur['pages'].append(dst)
            done = (a.get('toasts') or [''])[-1] or (a.get('creates') and 'created ' + a['creates'][0]['name'])
            if done and a['cmd'] not in ('screen', 'scroll', 'find'):
                cur['done'] = str(done)[:90]; trails.append(cur); cur = None
            if a['cmd'] in ('tap', 'key') and a.get('control'):
                text = f"{a['control']} {src} {a.get('result', '')[:200]}".lower()
                for k, rx in KINDS.items():
                    if re.search(rx, text) and (a['day'], k) not in seen_kind:
                        seen_kind.add((a['day'], k)); first[k][src] += 1; break
        jobs = defaultdict(list)
        for t in trails: jobs[' '.join(re.sub(r'[\d$,.#:/-]+', ' ', t['done']).split()[:4]).lower() or 'other'].append(t)
        top = sorted(jobs.items(), key=lambda kv: -len(kv[1]))[:5]
        res[uid] = {
            'menu_seen': menus.get(uid, {}).get('menu'), 'phone': menus.get(uid, {}).get('phone'),
            'pages': {p: {'visits': v['visits'], 'taps': v['taps'], 'seconds': round(v['seconds']), 'act_s': round(v['act_s'], 1),
                          'top_controls': v['controls'].most_common(5)} for p, v in sorted(pages.items(), key=lambda kv: -kv[1]['seconds'])},
            'trails': [{**t, 'seconds': round(t['seconds'])} for t in trails],
            'backtracks': sum(t['backtracks'] for t in trails),
            'top_jobs': [{'job': j, 'times': len(T), 'median_taps': statistics.median(t['taps'] for t in T),
                          'median_seconds': round(statistics.median(t['seconds'] for t in T)),
                          'typical_trail': max(T, key=lambda t: len(t['pages']))['pages'][:8]} for j, T in top],
            'first_looked_for': {k: v.most_common(4) for k, v in first.items()}}
    p = os.path.join(d, 'nav_usage.json')
    json.dump(res, open(p, 'w'), indent=1)
    print(f'wrote {p} for {len(res)} people' + ('' if menus else ' (no menus.json: run `sim/simctl menus` first for the menus as seen)'))
    return res


def compact(uid, U):
    """the usage, short (a few hundred tokens): what an expert needs to judge their own navigation"""
    u = U.get(uid) or {}
    pg = list((u.get('pages') or {}).items())[:8]
    L = ['Pages (visits, taps, seconds incl. your thinking): ' + '; '.join(f"{p} {v['visits']}v {v['taps']}t {v['seconds']}s" for p, v in pg),
         'Top jobs (times, median taps, median seconds, typical trail): ' + '; '.join(
             f"{j['job']} x{j['times']} {j['median_taps']}t {j['median_seconds']}s [{' > '.join(j['typical_trail'])}]" for j in u.get('top_jobs') or []),
         f"Back-tracks: {u.get('backtracks', 0)} over {len(u.get('trails') or [])} jobs",
         'Where you first acted, per kind (page, days): ' + '; '.join(f"{k}: " + ', '.join(f'{p} {n}' for p, n in v) for k, v in (u.get('first_looked_for') or {}).items())]
    m = u.get('menu_seen')
    if m: L.append('Your menu (entry: tabs): ' + ' | '.join(f"{x['label']}: {', '.join(x['tabs'][:8]) or '-'}" for x in m))
    return '\n'.join(L)


def prompt(uid):
    run, d = run_dir()
    p = os.path.join(d, 'nav_usage.json')
    U = json.load(open(p)) if os.path.exists(p) else usage()
    tpl = open(os.path.join(HERE, 'workshop_nav.md')).read().split('<!-- EXPERT -->')[1].split('<!-- /EXPERT -->')[0]
    draft = os.path.join(ROOT, 'docs', 'MENU_DRAFT.md')
    from server import PEOPLE
    role, phone, name = PEOPLE[uid]
    vals = {'uid': uid, 'name': name, 'role': role, 'device': 'on a phone' if phone else 'on a desktop', 'usage': compact(uid, U),
            'draft': draft if os.path.exists(draft) else '(no draft yet: judge what you used)',
            'answer': os.path.join(d, 'workshop', uid + '.md'), 'diary': os.path.join(d, 'diary', uid + '.md'),
            'phone_part': 'the 4-5 bottom-bar items, comma-separated, in order' if phone else 'none (desktop)'}
    for k, v in vals.items(): tpl = tpl.replace('{' + k + '}', v)
    os.makedirs(os.path.join(d, 'workshop'), exist_ok=True)
    return tpl.strip()


def parse(text):
    sec, out = None, defaultdict(list)
    for l in text.splitlines():
        h = re.match(r'^##\s*(.+)', l)
        if h: sec = h.group(1).strip().lower(); continue
        if sec and l.strip(): out[sec].append(l.strip())
    return out


SEV = {'blocks': 3, 'slows': 2, 'annoys': 1}
FREQ = {'daily': 3, 'weekly': 2, 'rarely': 1}
QNAME = {1: 'Change', 2: 'Combine', 3: 'Confusing', 4: 'Missing information', 5: 'Scattered information', 6: 'Too many pages',
         7: 'Came to do / finished here', 8: 'Had to leave to decide', 9: 'Never used', 10: 'First thing not at the top', 11: 'Blue button',
         12: 'Numbers disagree', 13: 'Trust', 14: 'Lost my place', 15: 'Top jobs', 17: 'Phone: scroll, zoom, two hands', 18: 'In a hurry, gloves',
         19: 'Words', 20: 'Done by hand', 21: 'Assistant', 22: 'Fear of an undoable mistake', 23: 'Outside the app', 24: 'Day one',
         25: 'Could not find', 26: 'Need from another role', 27: 'Wrong in the draft'}


def score():
    run, d = run_dir()
    from server import PEOPLE
    W = os.path.join(d, 'workshop')
    answers = {f[:-3]: parse(open(os.path.join(W, f)).read()) for f in sorted(os.listdir(W)) if f.endswith('.md')} if os.path.isdir(W) else {}
    names = {pair: Counter() for pair in NAME_PAIRS}
    keep, finds = Counter(), defaultdict(list)
    menus = []
    for uid, A in answers.items():
        role = PEOPLE.get(uid, ('?',))[0]
        menu = [re.sub(r'^\d+[.)]\s*', '', x) for x in A.get('menu', [])]
        bar = ' · '.join(A.get('phone bar', [])) if A.get('phone bar') and 'none' not in A['phone bar'][0].lower() else ''
        menus.append(f"- **{role}** ({uid}): " + ' / '.join(x.split(':')[0].strip() for x in menu) + (f" · phone bar: {bar}" if bar else ''))
        for x in ','.join(A.get('keep five', [])).split(','):
            if x.strip(): keep[x.strip().title()] += 1
        for x in A.get('names', []):
            for a, b in NAME_PAIRS:
                m = re.match(rf'{a}\s*\|\s*{b}\s*:\s*(\w+)', x, re.I)
                if m: names[(a, b)][m.group(1).title()] += 1
        for x in A.get('findings', []):
            parts = [p.strip() for p in x.lstrip('- ').split('|')]
            m = re.match(r'Q(\d+)', parts[0], re.I)
            if not m or len(parts) < 5: continue
            q = int(m.group(1)); page = parts[1].strip().title() or 'Menu'
            finds[(q, page)].append({'role': role, 'uid': uid, 'freq': parts[2].lower(), 'sev': parts[3].lower(), 'text': ' | '.join(parts[4:])[:200]})
    def weight(F): return (len({f['role'] for f in F}), max(SEV.get(f['sev'], 0) for f in F), max(FREQ.get(f['freq'], 0) for f in F))
    L = [f'# Navigation and Pages Workshop: {run}\n', f'SmartDesign workspace; Mercer & Bond out of scope. {len(answers)} experts answered. '
         'Everything above "Synthesis" is grouped mechanically by sim/workshop.py; the synthesis step writes the rest.\n']
    for q in (3, 5):
        G = sorted([(k, F) for k, F in finds.items() if k[0] == q], key=lambda kv: weight(kv[1]), reverse=True)
        L.append(f'## Shared first: {QNAME[q]} (by how many roles)\n')
        L += [f"- **{k[1]}** · {weight(F)[0]} roles ({', '.join(sorted({f['role'] for f in F}))}) · worst {max(F, key=lambda f: SEV.get(f['sev'], 0))['sev']}: "
              + ' // '.join(f"{f['role']}: {f['text']}" for f in F[:5]) for k, F in G] or ['- (none)']
        L.append('')
    heat = defaultdict(lambda: Counter())
    for (q, page), F in finds.items():
        for f in F: heat[page][f['sev']] += 1; heat[page]['roles:' + f['role']] += 1
    L.append('## Page heat (findings by severity, and the roles that hit them)\n')
    for page, c in sorted(heat.items(), key=lambda kv: -(3 * kv[1]['blocks'] + 2 * kv[1]['slows'] + kv[1]['annoys']))[:25]:
        L.append(f"- {page}: {c['blocks']} blocks, {c['slows']} slows, {c['annoys']} annoys · " + ', '.join(sorted(k[6:] for k in c if k.startswith('roles:'))))
    L.append('\n## Every other finding, by question and page (most roles, worst, most frequent first)\n')
    for q in sorted({k[0] for k in finds} - {3, 5}):
        G = sorted([(k, F) for k, F in finds.items() if k[0] == q], key=lambda kv: weight(kv[1]), reverse=True)
        L.append(f"### Q{q} {QNAME.get(q, '')}")
        L += [f"- {k[1]} · {weight(F)[0]} roles: " + ' // '.join(f"{f['role']} ({f['freq']}, {f['sev']}): {f['text']}" for f in F[:4]) for k, F in G[:12]]
    L.append('\n## Each role\'s own menu, as asked\n')
    L += menus or ['- (none)']
    L.append('\n## Keep five (votes)\n')
    L.append(', '.join(f'{k} {n}' for k, n in keep.most_common(20)) or '(none)')
    L.append('\n## Names\n')
    for (a, b), c in names.items(): L.append(f"- {a} or {b}: " + (', '.join(f'{k} {n}' for k, n in c.most_common()) or 'no votes'))
    L.append('\n## Synthesis: (a) menus per role, (b) page merges and cuts, (c) one place for each kind of information, (d) disagreements for Alan\n\n(to be written by the synthesis step)\n')
    p = os.path.join(d, 'nav_workshop.md')
    open(p, 'w').write('\n'.join(L) + '\n')
    syn = open(os.path.join(HERE, 'workshop_nav.md')).read().split('<!-- SYNTHESIS -->')[1].split('<!-- /SYNTHESIS -->')[0]
    print(syn.replace('{workshop}', p).replace('{answers}', W).replace('{usage}', os.path.join(d, 'nav_usage.json'))
          .replace('{menus}', os.path.join(d, 'menus.json')).replace('{draft}', os.path.join(ROOT, 'docs', 'MENU_DRAFT.md')).strip())


if __name__ == '__main__':
    sys.path.insert(0, HERE)
    a = sys.argv[1:]
    if not a or a[0] in ('-h', '--help'): print(__doc__.strip()); sys.exit(2)
    if a[0] == 'usage': usage()
    elif a[0] == 'prompt': print(prompt(a[1]))
    elif a[0] == 'score': score()
    else: print(__doc__.strip()); sys.exit(2)
