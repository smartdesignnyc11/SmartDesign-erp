"""sim/pilot3.py: what Pilot 3 hands each person and each judge (Alan, 2026-10-25). Invented data only.

- `standard_md(db, uid, book)`: the SmartDesign Standard as the app holds it today (DB.company.standard, the live,
  versioned copy Alan edits), laid out the way the app's own assistant gets it (standardPrompt in src/app.js): the
  company sections in full and the playbooks of the role the person plays. Loaded from the run's database at prompt
  time, never paraphrased into the repo.
- `trail_md(actions, uid, day)`: one person's day as the judge reads it: per turn, every action with its clock,
  minutes, the screen it landed on, the reason the person gave (`--why`), the result, the interruptions and calls.
- `judge_prompt(...)`: sim/realism_judge.md filled for one person and one day.

    python3 sim/pilot3.py standard <uid>            print the Standard as <uid> gets it (from the current run's db.json)
    python3 sim/pilot3.py trail <uid> <day>         print the judge's trail for that day
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
strip = lambda s: re.sub(r'\*(.+?)\*', r'\1', re.sub(r'\*\*(.+?)\*\*', r'\1', str(s or ''))).strip()
li = lambda L: '\n'.join(f'- {strip(x)}' for x in (L or []))


def standard_md(db, uid, book):
    S = ((db.get('company') or {}).get('standard') or {})
    B = S.get('body') or {}
    if not B: return '(the company has no Standard on file: read docs/STANDARD.md)'
    want = (book.get('standard_for') or {}).get(uid) or {'role': '', 'playbooks': []}
    P = B.get('playbooks') or {}
    out = [f"# {B.get('title', 'The SmartDesign Standard')} (version {S.get('version', '?')}, {S.get('at', '')[:10]}, {S.get('by', '')})",
           f"_{strip(B.get('subtitle'))}_", '', 'The company\'s own copy, as the app holds it today. It outranks everything else you were told.', '']
    out.append('## Who we are'); out += [strip(x.get('p') if isinstance(x, dict) else x) for x in B.get('whoWeAre') or []]
    out.append('\n## Core values'); out.append(strip(B.get('valuesIntro')))
    for i, v in enumerate(B.get('values') or [], 1):
        out.append(f"\n### {i}. {v.get('name')}\n{strip(v.get('line'))}\n{li(v.get('bullets'))}" + (f"\nWhy: {strip(v.get('why'))}" if v.get('why') else '') +
                   (f"\n{(v.get('whyMatters') or {}).get('label', '')}: {strip((v.get('whyMatters') or {}).get('text'))}" if v.get('whyMatters') else ''))
    out.append(f"\n## Decision principles\n{strip(B.get('principlesIntro'))}")
    out += [f"{i}. **{p.get('name')}**: {strip(p.get('text'))}" for i, p in enumerate(B.get('principles') or [], 1)]
    out.append(strip(B.get('principlesClosing')))
    T = B.get('fourTests') or {}
    out.append(f"\n### The four tests\n{strip(T.get('intro'))}"); out += [f"- **{t.get('name')}**: {strip(t.get('text'))}" for t in T.get('tests') or []]
    out.append('\n### Decide or escalate'); out.append(li(B.get('decideOrEscalate')))
    St = B.get('standards') or {}
    out.append(f"\n## Company-wide standards\n{strip(St.get('intro'))}")
    for a in St.get('areas') or []: out.append(f"\n### {a.get('name')}\n{li(a.get('items'))}")
    out.append(f"\n## Escalation triggers\n{strip(B.get('escalationIntro'))}")
    out += [f"- {x.get('situation')}: raise to {x.get('raiseTo')}; {x.get('howFast')}; client told: {x.get('clientTold')}" for x in B.get('escalation') or []]
    out.append(strip(B.get('escalationFormat')))
    for k in want.get('playbooks') or []:
        pb = P.get(k)
        if not pb: continue
        out.append(f"\n## Your playbook: {pb.get('title')}\nMission: {strip(pb.get('mission'))}\n\nAct from:\n{li(pb.get('actFrom'))}\n\nStandards:\n{li(pb.get('standards'))}" +
                   (f"\n\n{pb.get('approvalLabel') or 'Requires approval'}:\n{li(pb.get('approval'))}" if pb.get('approval') else '') + f"\n\nNever:\n{li(pb.get('never'))}")
    if not want.get('playbooks'): out.append('\nYou lead the firm: every section above applies to you in full, and every playbook is yours to hold people to.')
    return '\n'.join(x for x in out if x is not None) + '\n'


def trail_md(actions, uid, day):
    """one person's day for the realism judge"""
    L = [f'# {uid} on {day}: the action trail\n', 'Each line: clock, minutes, the verb and what was typed or tapped, the screen it landed on, the reason given (why), the result. '
         'INTERRUPTION lines are what cut in; CALL lines what was said on the phone.\n']
    cur = None
    for a in actions:
        if a.get('uid') != uid or a.get('day') != day or a.get('cmd') in ('fia_after_reload',): continue
        if a.get('cmd') == 'begin_turn':
            cur = a.get('args', [''])[0]; L.append(f"\n## Turn: {cur} ({a.get('device', '')}, {a.get('result', '')})"); continue
        if a.get('cmd') == 'end_turn': L.append(f"(turn ends: {a.get('used')} actions)"); continue
        if a.get('cmd') == 'interrupt': L.append(f"- INTERRUPTION: {a.get('result', '')[:240]}"); continue
        if a.get('cmd') == 'call': L.append(f"- CALL {' / '.join(str(x)[:140] for x in a.get('args') or [])} -> {str(a.get('result', ''))[:160]}"); continue
        if a.get('cmd') == 'why': L.append(f"  why: {a.get('why', '')} (for the {(a.get('args') or [''])[0]})"); continue
        w = a.get('where') or {}
        args = ' '.join(json.dumps(x) if ' ' in str(x) else str(x) for x in (a.get('args') or []))[:220]
        res = str(a.get('result') or '').split('\n')[0][:160]
        L.append(f"- {a.get('clock', '')} +{a.get('minutes', '')}m {a.get('cmd')} {args} -> {a.get('after') or w.get('title') or ''}"
                 + (f" [{w.get('view')}{':' + w['tab'] if w.get('tab') else ''}{' job ' + w['cur'] if w.get('cur') else ''}]" if w.get('view') else '')
                 + (f" | why: {a['why']}" if a.get('why') else '') + (f" | {res}" if res and a.get('cmd') not in ('screen', 'scroll') else ''))
    return '\n'.join(L) + '\n'


def judge_prompt(tpl, vals):
    for k, v in vals.items(): tpl = tpl.replace('{' + k + '}', str(v))
    return tpl


def _run():
    run = os.environ.get('SIM_RUN') or open(os.path.join(HERE, 'runs', '.current')).read().strip()
    return run, os.path.join(HERE, 'runs', run)


if __name__ == '__main__':
    import cycle as CY
    run, d = _run()
    if sys.argv[1] == 'standard':
        print(standard_md(json.load(open(os.path.join(d, 'db.json'))), sys.argv[2], CY.load_book()))
    elif sys.argv[1] == 'trail':
        A = [json.loads(l) for l in open(os.path.join(d, 'actions.jsonl')) if l.strip()]
        print(trail_md(A, sys.argv[2], sys.argv[3]))
