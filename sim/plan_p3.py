"""sim/plan_p3.py: Pilot 3's turns, caps and token estimate, measured from Pilot 2's run (Alan, 2026-10-25).

What it rests on, all from runs/pilot2 (actions.jsonl, cost.jsonl, docs_usage.json):
- tokens per turn against tool uses per turn, fitted on Pilot 2's 69 measured turns (linear; the fit and its R^2 are
  printed), and the plain mean (about 82k a turn at about 15 tool uses);
- actions per document of each kind, from the trail that led to each document Pilot 2's people made;
- the share of actions that were looking (screen, find, news, menu, reading mail): about 45% in Pilot 2;
- how often a turn ended on its cap (Pilot 2: most of them, so the cap, not the work, set the cost).
What it assumes (named in the output): the actions a step Pilot 2 never finished would take (a 12-line estimate,
three vendors set up, two RFQs sent), the tool uses an action costs with `do` batching (0.7), 20% for dead ends, and
the judge's reading.

    python3 sim/plan_p3.py <pilot2 run dir>        prints the per-role need, the caps and the estimate as JSON
"""
import json, os, statistics, sys
from collections import Counter

DAYS, SLOTS = 3, ['morning', 'work1', 'work2', 'eod']
# per role: (step, expected actions, what the number rests on); "P2" = measured in Pilot 2's trails
NEED = {
    'u_owner': [('lead on file, won, the project', 18, 'P2 selftest walk: lead 5, won 5, project 8'),
                ('the radiator question; the Ashbys\' call', 8, 'mail send 1 + call 1 + looking'),
                ('estimate checked, sent; the signature, contract and SOV', 16, 'P2 CO send 4 + approval record 6 + reading 6 (assumed)'),
                ('approvals over three days (bills, payroll, a PO over its line)', 20, 'P2 owner: about 6 approvals a day'),
                ('Tuesday\'s numbers (cash, AR, lines over, unbilled, reimbursables)', 25, 'assumed: 5 reports, about 5 actions each'),
                ('routine: the morning money and approvals, x3', 30, 'P2 owner mornings: about 14 actions, half looking')],
    'u_alan': [('the estimate, 12 to 13 real lines', 77, 'assumed: 5 actions a line + 12; P2 never finished a multi-line estimate (EST-2026-016: 20 actions, one empty line)'),
               ('the vanity change: priced, sent, approval recorded', 21, 'P2 CO: 13 to 15 actions + 6 to record the approval'),
               ('the pendants to billing; Angel\'s call', 8, 'mail and call'),
               ('Friday review, 5 pages x 2 jobs', 20, '2 actions a page'),
               ('two client updates', 12, 'P2 mail send: about 6 actions with reading'),
               ('Tuesday\'s numbers', 20, 'assumed'),
               ('routine: look-ahead and field questions, x3', 36, 'P2 PM turns: 14 to 16 actions')],
    'u_chen': [('three vendors on file (two new yards, Nemo\'s email)', 24, 'assumed: 8 actions each'),
               ('two RFQs from estimate lines, out to three vendors each', 46, 'P2 RFQ: 14 actions to a draft + 9 to send, x2'),
               ('six quotes in three formats read, leveled, negotiated once', 24, 'P2 mail read: 3 actions each + 1'),
               ('award; three or four POs issued and sent', 56, 'P2 PO: 8 actions to a draft + 6 to issue and send, x4'),
               ('stock: the NM-B and the boxes from stock', 8, 'assumed'),
               ('two bills against their POs, with the holds', 40, 'P2 bill: 8 to 22 actions, 20 each'),
               ('the short and damaged claims', 12, 'assumed'),
               ('Tuesday\'s numbers', 15, 'assumed'),
               ('routine: requests, buy board, deliveries, x3', 30, 'P2 Chen mornings: about 14 actions')],
    'u_billing': [('deposit invoice, sent', 12, 'P2 invoice: 7 to 9 actions + send'),
                  ('the deposit recorded against its bank line', 10, 'P2 payment: about 8'),
                  ('progress invoice from the SOV, retainage', 14, 'P2 pay application: 7 + checks'),
                  ('the change and the pendants billed', 14, 'P2 invoice 9 + a reimbursable line'),
                  ('David Klein\'s mail', 6, 'mail'),
                  ('Tuesday\'s numbers', 20, 'assumed'),
                  ('routine: queue, bank, collections, x3', 36, 'P2 billing turns: about 14 actions')],
}
SLACK = 1.2          # dead ends, back-tracks and a control that does not answer (P2: 5% failed taps, 2-4% back-tracks)
TU_PER_ACTION = 0.7  # tool uses per action with `do` batching (P2: 0.99 with 10% of calls batched)
READS = 4            # tool uses to read the prompt's files at the start of a turn
# caps: per role and slot, and the days the required work peaks (cap_days)
CAPS = {'u_owner': {'morning': 14, 'work1': 18, 'work2': 16, 'eod': 14}, 'u_alan': {'morning': 15, 'work1': 22, 'work2': 22, 'eod': 16},
        'u_chen': {'morning': 15, 'work1': 22, 'work2': 22, 'eod': 15}, 'u_billing': {'morning': 12, 'work1': 18, 'work2': 18, 'eod': 14}}
CAP_DAYS = {'1': {'u_owner': {'work1': 26, 'work2': 22}, 'u_alan': {'work1': 90, 'work2': 26}},
            '2': {'u_chen': {'morning': 22, 'work1': 50, 'work2': 60, 'eod': 25}, 'u_alan': {'work1': 32, 'eod': 30}},
            '3': {'u_chen': {'work1': 45, 'work2': 35, 'eod': 25}, 'u_owner': {'eod': 34}, 'u_alan': {'eod': 30}, 'u_billing': {'work2': 26, 'eod': 30}}}
MINUTES = {'morning': 150, 'work1': 210, 'work2': 180, 'eod': 90}


def measure(run):
    C = [json.loads(l) for l in open(os.path.join(run, 'cost.jsonl'))]
    T = [c for c in C if c.get('measured') and str(c.get('uid', '')).startswith('u_') and 'actions' in c]
    x = [c['measured']['tool_uses'] for c in T]; y = [c['measured']['tokens'] for c in T]
    n = len(x); mx, my = sum(x) / n, sum(y) / n
    b = sum((a - mx) * (c - my) for a, c in zip(x, y)) / sum((a - mx) ** 2 for a in x); a0 = my - b * mx
    r2 = 1 - sum((c - (a0 + b * a)) ** 2 for a, c in zip(x, y)) / sum((c - my) ** 2 for c in y)
    W = [c for c in C if not str(c.get('uid', '')).startswith('u_') and c.get('measured')]
    A = [json.loads(l) for l in open(os.path.join(run, 'actions.jsonl'))]
    P = [a for a in A if str(a.get('uid', '')).startswith('u_') and a.get('cmd') not in ('begin_turn', 'end_turn', 'fia_after_reload', 'do')]
    look = sum(1 for a in P if a['cmd'] in ('screen', 'find', 'scroll', 'news', 'go', 'back') or (a['cmd'] == 'mail' and (not a.get('args') or a['args'][0] in ('list', 'read', 'inbox', 'drafts', 'sent'))))
    U = json.load(open(os.path.join(run, 'docs_usage.json'))) if os.path.exists(os.path.join(run, 'docs_usage.json')) else []
    docs = {}
    for u in U: docs.setdefault(u['type'], []).append(u['actions'])
    return {'turns': n, 'tokens_mean': round(my), 'tool_uses_mean': round(mx, 1), 'fit': {'base': round(a0), 'per_tool_use': round(b), 'r2': round(r2, 2)},
            'tokens_per_tool_use': round(sum(y) / sum(x)), 'capped_turns': sum(1 for c in T if c['actions'] >= c['cap']), 'look_share': round(look / len(P), 2),
            'actions': len(P), 'actions_per_doc': {k: {'n': len(v), 'median': statistics.median(v)} for k, v in docs.items()},
            'workshop_tokens': sum(int(c['measured'].get('tokens') or 0) for c in W), 'workshop_runs': len(W)}


def estimate(M):
    tok = lambda tu: M['fit']['base'] + M['fit']['per_tool_use'] * tu
    out = {'roles': {}, 'turns': 0, 'tokens_expected': 0, 'tokens_if_every_cap_used': 0}
    for uid, steps in NEED.items():
        need = round(sum(s[1] for s in steps) * SLACK)
        caps = [(d, s, int(((CAP_DAYS.get(str(d)) or {}).get(uid) or {}).get(s) or CAPS[uid][s])) for d in range(1, DAYS + 1) for s in SLOTS]
        total_cap = sum(c for _, _, c in caps)
        # the expected use: each turn uses its share of the need, never more than its cap
        exp = [min(c, need * c / total_cap) for _, _, c in caps]
        tu_exp = [READS + TU_PER_ACTION * e for e in exp]; tu_cap = [READS + TU_PER_ACTION * c for _, _, c in caps]
        R = {'need_actions': need, 'cap_total': total_cap, 'turns': len(caps), 'expected_tokens': round(sum(tok(t) for t in tu_exp)),
             'tokens_if_capped': round(sum(tok(t) for t in tu_cap)), 'steps': [[s[0], s[1], s[2]] for s in steps],
             'biggest_turn': max(caps, key=lambda x: x[2])}
        out['roles'][uid] = R; out['turns'] += len(caps); out['tokens_expected'] += R['expected_tokens']; out['tokens_if_every_cap_used'] += R['tokens_if_capped']
    judge = DAYS * len(NEED)
    jt = tok(8) + 25000   # 8 tool uses (the brief, standard, diary, trail, the answer) + the trail and diary as context (assumed)
    out['judge'] = {'runs': judge, 'tokens_each': round(jt), 'tokens': round(judge * jt), 'rests_on': 'one judge run per role per day; 8 tool uses; 25k tokens of trail and diary read (assumed)'}
    out['tokens_expected'] += out['judge']['tokens']; out['tokens_if_every_cap_used'] += out['judge']['tokens']
    out['tokens_at_p2_mean_per_turn'] = out['turns'] * M['tokens_mean'] + out['judge']['tokens']
    return out


if __name__ == '__main__':
    M = measure(sys.argv[1])
    E = estimate(M)
    print(json.dumps({'measured': M, 'estimate': E, 'caps': CAPS, 'cap_days': CAP_DAYS, 'minutes': MINUTES}, indent=1))
