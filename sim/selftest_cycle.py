"""sim/selftest_cycle.py: Pilot 3's harness checked without a browser (sim/selftest.py runs it first; `--unit` runs only it).

- the book: four roles, the takeoff a real estimate (8+ lines, five kinds), every event's step is a step the referee
  knows, the plants hold by construction (every yard's drywall above its line, Nemo's tile the cheapest and above the
  last price, the stocked items in the seed's stock), objectives framed as outcomes (no screen names);
- the referee's step checks on three fixture databases (invented): every step done right, every step done wrong, and
  nothing done; the planted leaks caught, missed and not reached; the referee's own numbers and the answers graded;
- the coverage floor; the realism judge's file format and the grade discounted for flagged turns; the diary parsers;
- the planted vendors' quote replies in their formats; what reached the person on a document ("Missing").
"""
import copy, json, os, re, sys
from datetime import datetime
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cycle as CY

FAILS, N = [], [0]


def check(ok, msg):
    N[0] += 1
    print(('PASS ' if ok else 'FAIL ') + msg, flush=True)
    if not ok: FAILS.append(msg)
    return ok


def ms(day, hm='12:00'):
    return int(datetime.fromisoformat(f'{day}T{hm}:00').replace(tzinfo=ZoneInfo('America/New_York')).timestamp() * 1000)


def mail(to, subject, body, day='2026-09-04'):
    return {'id': f'm{abs(hash((to, subject))) % 10 ** 8}', 'labelIds': ['SENT'], 'internalDate': ms(day),
            'headers': {'From': 'x', 'To': to, 'Cc': '', 'Subject': subject}, 'body': body, 'attachments': []}


def fixture(kind, B):
    """an invented company after the cycle: 'right' (each step as a pro does it), 'wrong' (each step done, badly), 'none'"""
    db = {'company': {'today': '2026-09-08'}, 'accounts': [{'id': 'ac1', 'name': 'Chase Business Checking', 'type': 'bank', 'opening': 100000.0},
                                                           {'id': 'ac2', 'name': 'Amex 1009', 'type': 'card', 'opening': 0.0}],
          'employees': [{'id': 'em1', 'name': 'Angel', 'rate': 42, 'burden': 22}], 'users': [{'id': 'u_angel', 'employeeId': 'em1'}],
          'stock': {'opening': {'lines': [{'invId': 'iv9', 'qty': 42, 'cost': 1.2}, {'invId': 'iv10', 'qty': 3, 'cost': 98}, {'invId': 'iv16', 'qty': 12, 'cost': 16.8}]}},
          'clients': [], 'leads': [], 'projects': [], 'rfqs': [], 'pos': [{'id': 'old', 'number': 'PO-2026-041', 'projectId': 'p121', 'vendor': 'Nemo Tile', 'status': 'received', 'date': '2026-08-01',
                                                                     'lines': [{'item': 'Calacatta porcelain 12x24', 'qty': 320, 'unit': 'sf', 'price': 12.5}]}],
          'bills': [], 'txns': [], 'time': [], 'field': {'logs': []}, 'payroll': [], 'outbox': [], 'demoWs': {},
          'vendors': [{'id': 'v1', 'name': 'Nemo Tile', 'email': 'sales@nemotile.example'}, {'id': 'vg', 'name': 'Gowanus Building Supply', 'email': 'orders@gowanusbuilding.example'},
                      {'id': 'vb', 'name': 'Brooklyn Lumber', 'email': 'orders@brooklynlumber.example'}, {'id': 'va', 'name': 'Atlantic Yard Supply', 'email': 'sales@atlanticyardsupply.example'},
                      {'id': 'vt', 'name': 'Bergen Tile Gallery', 'email': 'quotes@bergentile.example'}, {'id': 'vc', 'name': 'Carroll Street Tile', 'email': 'desk@carrollstreettile.example'}]}
    world = {'gated': {}, 'calls': [], 'interrupts_done': {}}
    if kind == 'none': return db, world
    right = kind == 'right'
    T = B['takeoff'] + [B['radiator']]
    if not right: T = T[:6]
    lines = [{'id': f'l{i}', 'item': t['item'], 'qty': t['qty'], 'unit': t['unit'], 'rate': t['price'] if (right or i != 2) else 0, 'cost': t['cost'], 'code': f'{i:02d}'}
             for i, t in enumerate(T, 1)]
    E = {'id': 'eA', 'number': 'EST-2026-020', 'status': 'converted' if right else 'approved', 'projectId': 'pA', 'lines': lines, 'taxRate': 0,
         'clientApproval': {'via': 'mail', 'at': '2026-09-03T16:40:00'} if right else None}
    tot = CY.doc_total(E)
    sov = [{'id': f's{i}', 'projectId': 'pA', 'lineRef': f'estimate:eA:{l["id"]}', 'scheduled': l['qty'] * l['rate'], 'desc': l['item']} for i, l in enumerate(lines, 1)]
    dep = {'id': 'iD', 'number': 'INV-2026-050', 'depositOf': 'eA', 'status': 'sent', 'projectId': 'pA', 'date': '2026-09-04', 'sentAt': '2026-09-04',
           'lines': [{'item': 'Deposit', 'qty': 1, 'rate': round(tot * (0.25 if right else 0.10), 2)}]}
    co = {'id': 'co1', 'number': 'CO-2026-010', 'title': 'Garden bath vanity: 36-inch Rhea in walnut', 'projectId': 'pA', 'status': 'approved', 'date': '2026-09-04',
          'scheduleDays': 0 if right else None, 'approvedAt': '2026-09-04', 'lines': [{'item': 'Vanity upgrade', 'qty': 1, 'rate': 890, 'cost': 740, 'fromEstLine': 'l11'}]}
    prog = {'id': 'iP', 'number': 'INV-2026-051', 'mode': 'sov', 'status': 'sent', 'retainagePct': 10 if right else 0, 'projectId': 'pA', 'date': '2026-09-08',
            'lines': [{'sovId': 's1', 'item': lines[0]['item'], 'scheduled': sov[0]['scheduled'], 'pct': 40 if right else 60, 'prevPct': 0}]}
    invs = [dep, prog]
    if right: invs.append({'id': 'iC', 'number': 'INV-2026-052', 'status': 'sent', 'projectId': 'pA', 'date': '2026-09-08',
                           'lines': [{'item': 'CO-2026-010 vanity upgrade', 'qty': 1, 'rate': 890, 'coId': 'co1'}, {'item': 'Pendant lights for the island (Lightology, at cost)', 'qty': 1, 'rate': 612.40}]})
    dep_amt = CY.doc_total(dep)
    C = {'id': 'cA', 'name': 'Wren & Julian Ashby', 'contacts': [{'name': 'Wren Ashby', 'email': 'wren.ashby@example.com'}], 'contract': tot if right else 0,
         'estimates': [E], 'invoices': invs, 'changeOrders': [co], 'payments': [{'id': 'py1', 'invoiceId': 'iD', 'amount': dep_amt, 'date': '2026-09-08', 'txnId': 'tx1' if right else ''}],
         'sov': sov if right else sov[:2]}
    db['clients'] = [C] + ([] if right else [{'id': 'cB', 'name': 'Wren Ashby', 'contacts': [], 'estimates': [], 'invoices': [], 'changeOrders': [], 'payments': []}])
    db['leads'] = [{'id': 'ld1', 'name': 'Wren Ashby, 214 Lincoln Place', 'stage': 'won' if right else 'site-visit', 'clientId': 'cA' if right else '', 'contactIds': ['k1'] if right else []}]
    db['projects'] = [{'id': 'pA', 'clientId': 'cA', 'project': {'name': '214 Lincoln Place', 'addr': '214 Lincoln Place, Brooklyn'}, 'tasks': [{'id': 't1', 'name': 'Demo', 'pct': 40}],
                       'requests': [{'id': 'rq1', 'note': 'From stock instead of buying', 'items': [{'invId': 'iv10', 'qty': 3}, {'invId': 'iv9', 'qty': 30}, {'invId': 'iv16', 'qty': 12}]}] if right else [],
                       'chat': []}]
    ref = lambda i: f'estimate:eA:l{i}'
    q3 = [{'vendorId': v} for v in ('vb', 'vg', 'va')]
    db['rfqs'] = [{'id': 'r1', 'number': 'RFQ-2026-005', 'projectId': 'pA', 'status': 'awarded' if right else 'sent',
                   'lines': [{'id': 'L1', 'item': 'Framing lumber', 'line': ref(3)}, {'id': 'L2', 'item': 'Drywall', 'line': ref(4)}] if right else [{'id': 'L1', 'item': 'Drywall', 'line': ref(4)}],
                   'vendors': q3 if right else q3[:1], 'sent': [dict(x, via='outbox') for x in (q3 if right else q3[:1])], 'quotes': q3 if right else [],
                   'history': [{'what': 'took from stock', 'note': '3 roll 12/2 NM-B'}] if right else []},
                  {'id': 'r2', 'number': 'RFQ-2026-006', 'projectId': 'pA', 'status': 'awarded' if right else 'sent', 'lines': [{'id': 'L1', 'item': 'Porcelain tile', 'line': ref(6)}],
                   'vendors': [{'vendorId': v} for v in ('v1', 'vt', 'vc')], 'sent': [{'vendorId': v, 'via': 'outbox'} for v in ('v1', 'vt', 'vc')],
                   'quotes': [{'vendorId': v} for v in ('v1', 'vt', 'vc')] if right else [{'vendorId': 'v1'}]}]
    po = lambda pid, num, vend, vid, L, **kw: dict({'id': pid, 'number': num, 'projectId': 'pA', 'vendor': vend, 'vendorId': vid, 'status': 'issued', 'date': '2026-09-04', 'lines': L}, **kw)
    P1 = po('P1', 'PO-2026-060', 'Gowanus Building Supply', 'vg', [{'item': 'Framing lumber: supply', 'qty': 1, 'unit': 'ls', 'price': 826.80, 'line': ref(3)}], rfqId='r1')
    P2 = po('P2', 'PO-2026-061', 'Gowanus Building Supply', 'vg', [{'item': 'Drywall & cement board: supply', 'qty': 1, 'unit': 'ls', 'price': 2169.00, 'line': ref(4)}], rfqId='r1',
            overReason={'why': 'all three yards are over the line; the owner approved the $369', 'over': 369} if right else None,
            issues=[{'type': 'short', 'qty': 6}], receipts=[{'date': '2026-09-08'}])
    P3 = po('P3', 'PO-2026-062', 'Nemo Tile', 'v1', [{'item': 'Porcelain floor tile 12x24 matte', 'qty': 380, 'unit': 'sf', 'price': 13.90, 'line': ref(6)}], rfqId='r2',
            notes='Best of three; $1.40/sf over the $12.50 on PO-2026-041, Nemo would not hold it' if right else '', issues=[{'type': 'damaged', 'qty': 31}], receipts=[{'date': '2026-09-08'}])
    pos = [P1, P2, P3]
    if not right: pos.append(po('P4', 'PO-2026-063', 'Home Depot Pro', '', [{'item': '12/2 NM-B 250 ft', 'qty': 3, 'unit': 'roll', 'price': 104, 'line': ref(5)}]))
    db['pos'] += pos
    db['outbox'] = [{'id': f'o{p["id"]}', 'status': 'sent', 'to': {'name': p['vendor'], 'email': next((v['email'] for v in db['vendors'] if v['id'] == p['vendorId']), '')},
                     'subject': f'{p["number"]}: purchase order', 'body': '', 'sentAt': '2026-09-04'} for p in pos if right or p['id'] != 'P1']
    world['gated'] = {'Y-32': {'bind': {'inv': 'GOW-1111', 'number': 'PO-2026-061', 'total': 2169.00}}, 'Y-33': {'bind': {'inv': 'NEM-2222', 'number': 'PO-2026-062', 'total': 5282.00}},
                      'Y-34': {'bind': {'measured': {'demo': 40}}}}
    held_dw = 6 * 27.10 if right else 0; held_tile = 140 + 31 * 13.90 if right else 0
    db['bills'] = [{'id': 'b1', 'number': 'GOW-1111', 'vendor': 'Gowanus Building Supply', 'poId': 'P2', 'projectId': 'pA', 'code': '04', 'status': 'approved',
                    'lines': [{'amount': 2169.00}], 'short': {'held': held_dw} if right else None},
                   {'id': 'b2', 'number': 'NEM-2222', 'vendor': 'Nemo Tile', 'poId': 'P3', 'projectId': 'pA' if right else '', 'code': '06', 'status': 'approved',
                    'lines': [{'amount': 5282.00}, {'amount': 95.0}, {'amount': 45.0}], 'short': {'held': held_tile} if right else None}]
    db['txns'] = [{'id': 'tx1', 'acct': 'ac1', 'date': '2026-09-08', 'desc': 'ONLINE TRANSFER FROM ASHBY W', 'amt': dep_amt, 'status': 'categorized' if right else 'new', 'invoiceId': 'iD' if right else ''},
                  {'id': 'tx2', 'acct': 'ac2', 'date': '2026-09-04', 'desc': 'LIGHTOLOGY CHICAGO IL', 'amt': -612.40, 'projectId': 'pA', 'status': 'categorized'}]
    db['time'] = [{'id': 'te1', 'empId': 'em1', 'date': '2026-09-08', 'projectId': 'pA', 'work': [{'projectId': 'pA', 'code': '01', 'line': ref(1), 'hours': 8.5}]}]
    db['field']['logs'] = [{'projectId': 'pA', 'date': '2026-09-08'}]
    db['payroll'] = [{'id': 'pr9', 'from': '2026-08-31', 'to': '2026-09-04', 'status': 'approved' if right else 'submitted', 'total': 4655.82,
                      'approvals': [{'role': 'owner', 'action': 'approved by the Owner'}] if right else []}]
    W = {'u_owner': [mail('Wren Ashby <wren.ashby@example.com>', 'The garden bath radiator', 'Keep it or move it under the window?', '2026-09-03'),
                     mail('Wren Ashby <wren.ashby@example.com>', 'Your estimate EST-2026-020', 'Attached is EST-2026-020.', '2026-09-03')] if right else [],
         'u_alan': [mail('Wren Ashby <wren.ashby@example.com>', 'Weekly update, 214 Lincoln', 'This week and next week', '2026-09-04'),
                    mail('Sarah Klein <sarah.klein@example.com>', 'Weekly update, 121 State', 'This week', '2026-09-04'),
                    mail('Wren Ashby <wren.ashby@example.com>', 'CO-2026-010 vanity', 'The change order', '2026-09-04')] if right else [],
         'u_billing': [mail('David Klein <david.klein@example.com>', 'Re: INV-2026-040', 'Retainage held so far: $9,000', '2026-09-08')] if right else []}
    db['demoWs'] = {u: {'messages': M, 'labels': {}} for u, M in W.items()}
    if right:
        world['calls'] = [{'from': 'u_owner', 'to': 'ashby', 'said': 'Tuesday works; no need to be home'}, {'from': 'u_chen', 'to': 'gowanus_supply', 'said': 'Durock at the same price is fine'},
                          {'from': 'u_alan', 'to': 'u_angel', 'said': 'Yes, the pantry GFI is approved; Monday is fine'}]
    world['interrupts_done'] = {k: ['2026-09-04', 'work1', '10:30'] for k in ('Y-07', 'Y-18', 'Y-19', 'Y-40')}
    return db, world


def unit():
    B = CY.load_book()
    # ---- the book
    check(B['roles'] == ['u_owner', 'u_alan', 'u_chen', 'u_billing'], f"cycle book: four roles play ({', '.join(B['roles'])}); scripted: {', '.join(B['scripted'])}")
    kinds = {t['kind'] for t in B['takeoff']}
    check(len(B['takeoff']) >= 8 and {'labor', 'materials', 'sub', 'allowance', 'fee'} <= kinds and all(t['qty'] > 0 and t['price'] > 0 for t in B['takeoff']),
          f"cycle book: the takeoff is a real estimate ({len(B['takeoff'])} lines, ${sum(t['qty'] * t['price'] for t in B['takeoff']):,.0f}, kinds {sorted(kinds)})")
    steps = {s['id'] for s in B['steps']}
    bad = [e['id'] for e in B['events'] if (e.get('expect') or {}).get('check', {}).get('t') == 'cy' and e['expect']['check']['step'] not in steps] + \
          [e['id'] for e in B['events'] if (e.get('gate') or {}).get('t') == 'cy' and e['gate']['step'] not in steps]
    check(not bad and len(B['events']) >= 30, f'cycle book: every event\'s step and gate is a step the referee checks ({len(B["events"])} events; bad: {bad or "none"})')
    Q, S = B['parties'], B['schedule']
    lot = lambda k, key: sum(x['qty'] * Q[k]['quotes']['prices'][kk] for x in S[key] for kk in [next(kk for kk, rx in B['item_rx'].items() if re.search(rx, x['item'], re.I) and kk in Q[k]['quotes']['prices'])])
    dw = {k: lot(k, 'drywall') for k in ('brooklyn_lumber', 'gowanus_supply', 'atlantic_yard')}
    dw_budget = next(t['cost'] for t in B['takeoff'] if t['key'] == 'drywall')
    check(min(dw.values()) > dw_budget, f'plant L1 holds by construction: every yard\'s drywall lot is over the ${dw_budget:,} line ({", ".join(f"{k} ${v:,.2f}" for k, v in dw.items())})')
    tile_sf = {k: Q[k]['quotes']['prices']['porcelain|tile'] / (Q[k]['quotes'].get('box_sf') or 1) for k in ('nemo_tile', 'bergen_tile', 'carroll_tile')}
    check(min(tile_sf, key=tile_sf.get) == 'nemo_tile' and tile_sf['nemo_tile'] > B['last_price']['unit_price'] and tile_sf['nemo_tile'] * 380 <= next(t['cost'] for t in B['takeoff'] if t['key'] == 'tile'),
          f"plant L3 holds: Nemo is the cheapest tile per sf (${tile_sf['nemo_tile']:.2f}; Carroll's per box is ${tile_sf['carroll_tile']:.2f}/sf), above the ${B['last_price']['unit_price']:.2f} last paid, and under the line")
    check({x['inv'] for x in B['in_stock']} == {'iv9', 'iv10', 'iv16'}, 'plant L2: the stocked items are the seed\'s own (iv9 boxes, iv10 NM-B, iv16 Type X)')
    SCREEN = re.compile(r'\b(tap|click|screen|menu|button|Billing Queue|Buy Board|Purchasing >|Projects >)\b', re.I)
    check(not [o for L in B['objectives'].values() for o in L if SCREEN.search(o)], 'objectives are outcomes, never steps or screen names')
    roles_dir = os.path.join(HERE, 'roles', 'p3')
    check(all(os.path.exists(os.path.join(roles_dir, u + '.md')) and not re.search(r'\b(tap|click)\b', open(os.path.join(roles_dir, u + '.md')).read(), re.I) for u in B['roles']),
          'role cards (sim/roles/p3): one per role, goals and routine with no click lists')
    # ---- the referee on three invented companies
    out = {}
    for kind in ('right', 'wrong', 'none'):
        db, w = fixture(kind, B)
        review = [{'uid': 'u_alan', 'where': {'view': v.split(':')[0], 'tab': (v.split(':') + [''])[1], 'cur': j}} for j in ('p121', 'pA') for v in ('sched', 'costs', 'billing:co', 'dec', 'subm')]
        C = CY.Cycle(db, B, w, review if kind == 'right' else [], '2026-09-08')
        out[kind] = (C, {s['id']: s for s in C.steps()}, {p['id']: p for p in C.plants()})
    _, R, LR = out['right']; _, Wr, LW = out['wrong']; _, Nn, LN = out['none']
    people = [s for s in R.values() if not s['scripted'] and not s['id'].startswith('C5')]
    check(all(R[s['id']]['status'] == 'right' for s in people), 'referee, done right: every person\'s step reads right' +
          ('' if all(R[s['id']]['status'] == 'right' for s in people) else ': ' + '; '.join(f"{k} {v['status']} ({v['detail'][:70]})" for k, v in R.items() if v['status'] != 'right' and not v['scripted'] and not k.startswith('C5'))))
    check(all(R[k]['status'] == 'scripted' for k in ('C20', 'C21', 'C22', 'C23')), 'referee: the scripted steps (receiving, field day, statements, payroll build) read scripted when their records landed ' +
          str({k: R[k]['status'] for k in ('C20', 'C21', 'C22', 'C23')}))
    want_wrong = {'C02': 'clients', 'C05': 'lines', 'C06': 'nothing reached', 'C07': 'no record', 'C08': 'SOV', 'C10': 'one line', 'C11': 'vendors reached', 'C30': 'is not 25%', 'C31': 'not matched', 'C32': 'retainage', 'C40': 'schedule days'}
    got = {k: (Wr[k]['status'], Wr[k]['detail']) for k in want_wrong}
    check(all(st == 'wrong' and re.search(rx, det, re.I) for (st, det), rx in zip(got.values(), want_wrong.values())),
          'referee, done wrong: each step says what is wrong: ' + '; '.join(f"{k} {st}: {det[:60]}" for k, (st, det) in got.items()))
    check(Wr['C32']['status'] == 'wrong' and 'measured' in Wr['C32']['detail'], f"referee: billing ahead of the measure is wrong ({Wr['C32']['detail'][:90]})")
    check(all(s['status'] == 'not done' for s in Nn.values() if s['id'] != 'C42'), 'referee, nothing done: every step reads not done')
    caught = {k: LR[k]['caught'] for k in LR}; missed = {k: LW[k]['caught'] for k in LW}
    check(all(v not in ('nobody', 'not reached') for v in caught.values()) and sum(LR[k]['left'] for k in LR) == 0,
          'leaks, done right: every plant caught, $0 left behind (' + '; '.join(f'{k} {v}' for k, v in caught.items()) + ')')
    lw = {k: LW[k]['left'] for k in LW}
    check(all(missed[k] == 'nobody' for k in ('L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7', 'L8')) and lw['L9'] == 0 and lw['L1'] == 369.0 and lw['L4'] == 140.0 and abs(lw['L5'] - 162.6) < 0.01 and lw['L7'] == 612.40,
          f"leaks, done wrong: every plant missed, money left ${sum(lw.values()):,.2f} (" + '; '.join(f'{k} ${v:,.2f}' for k, v in lw.items()) + ')')
    check(all(LN[k]['caught'] == 'not reached' for k in LN), 'leaks, nothing done: every plant not reached (no money counted twice)')
    # ---- the referee's own numbers and the answers graded against them
    C = out['right'][0]
    F = C.figures()
    row = {r['line'][:20]: r for r in F['line_table']}
    dwr = next(r for r in F['line_table'] if r['line'].startswith('Drywall & cement'))
    check(abs(dwr['committed'] - 2169) < 0.01 and dwr['over'] == 369.0, f"figures: the drywall line committed ${dwr['committed']:,.2f} vs budget ${dwr['budget']:,.2f}, over ${dwr['over']:,.2f}")
    demo = F['line_table'][0]
    check(abs(demo['actual'] - round(8.5 * 42 * 1.22, 2)) < 0.02, f"figures: labor on the demo line from the hours at rate plus burden (${demo['actual']:,.2f})")
    check(F['cash']['cash'] == round(100000 + CY.doc_total(C.deposit_inv()), 2) and F['ar']['total'] > 0, f"figures: cash ${F['cash']['cash']:,.2f} from the opening and the bank lines; AR ${F['ar']['total']:,.2f}")
    Cw = out['wrong'][0]; Fw = Cw.figures()
    check(any(x['po'] == 'PO-2026-062' and abs(x['more'] - 532.0) < 0.01 for x in Fw['price_vs_last']) and Fw['reimb'] and 'pA' in Fw['unbilled'],
          f"figures, done wrong: paid more than last time {Fw['price_vs_last']}, reimbursables {Fw['reimb']}, unbilled {Fw['unbilled']}")
    good = {q[0]: '; '.join(f'{n} ${v:,.2f}' for n, v in Cw.expected(q[1], Fw)) for q in B['questions']['u_owner']}
    G = Cw.grade_answers('u_owner', good)
    G2 = Cw.grade_answers('u_billing', {'Q1': 'AR is about $12,000', 'Q2': ''})
    check(all(g['grade'] == 'right' for g in G) and G2[0]['grade'] == 'wrong' and G2[1]['grade'] == 'not answered',
          f"answers: the owner's figures graded right ({', '.join(g['grade'] for g in G)}); a wrong AR and a blank read wrong and not answered")
    diary = ('# diary\n\n## 2026-09-03 end of day\nGrade, phone: 6/10\nGrade, desktop: 8/10\n\n## 2026-09-08 end of day\nGrade, phone: 4/10\n\n'
             '## Numbers for the team meeting\nQ1: cash $123,456.00 in Chase\nQ2: AR $9,000\n continued on the next line\nQ3: none over\n')
    A = CY.diary_answers(diary); Gr = CY.diary_grades(diary)
    check(A == {'Q1': 'cash $123,456.00 in Chase', 'Q2': 'AR $9,000 continued on the next line', 'Q3': 'none over'} and Gr == {'2026-09-03': {'phone': 6.0, 'desktop': 8.0}, '2026-09-08': {'phone': 4.0}},
          f'diary: the meeting answers ({A}) and the day grades ({Gr}) are read back')
    # ---- coverage and its floor
    pages = B['coverage']['u_alan']['pages']
    acts = [{'uid': 'u_alan', 'where': {'view': k.split(':')[0], 'tab': (k.split(':') + [''])[1], 'cur': 'p121'}, 'ms': 1000} for k, _ in pages[:12]] + \
           [{'uid': 'u_chen', 'where': {'view': k.split(':')[0]}} for k, _ in B['coverage']['u_chen']['pages'][:5]] + \
           [{'uid': 'u_billing', 'land': {'to': {'view': 'billing'}}, 'where': {'view': 'billing', 'tab': 'invoices'}}]
    cv = {u: CY.coverage(acts, B, u) for u in ('u_alan', 'u_chen', 'u_billing')}
    check(cv['u_alan']['valid'] and cv['u_alan']['opened'] == 12 and not cv['u_chen']['valid'] and cv['u_chen']['pct'] == 0.5 and cv['u_billing']['opened'] == 1,
          f"coverage: the PM opened {cv['u_alan']['opened']} of {cv['u_alan']['pages']} Projects pages ({cv['u_alan']['pct']:.0%}, valid); the coordinator {cv['u_chen']['pct']:.0%} of Purchasing: NOT a valid grade (floor {B['coverage']['floor']:.0%})")
    rv = [{'uid': 'u_alan', 'where': {'view': v.split(':')[0], 'tab': (v.split(':') + [''])[1], 'cur': j}} for j in ('p121', 'pA') for v in ('sched', 'costs', 'billing:co', 'dec', 'subm')]
    Cr = CY.Cycle(out['right'][0].db, B, out['right'][0].w, rv, '2026-09-08')
    Cr2 = CY.Cycle(out['right'][0].db, B, out['right'][0].w, rv[:7], '2026-09-08')
    check(Cr.s_C41()[0] == 'right' and Cr2.s_C41()[0] == 'wrong' and 'pA' in Cr2.s_C41()[1], f"the PM's Friday review: both jobs' pages read right; one job half done reads wrong ({Cr2.s_C41()[1][:80]})")
    # ---- the realism judge: its file format and the discount
    import tempfile
    d = tempfile.mkdtemp(prefix='judge_')
    json.dump({'uid': 'u_chen', 'day': '2026-09-03', 'turns': [{'slot': 'morning', 'realistic': True, 'flags': []}, {'slot': 'work1', 'realistic': True, 'flags': []},
              {'slot': 'work2', 'realistic': False, 'flags': [{'kind': 'skipped-check', 'action': '10:42 tap Issue PO', 'note': 'no price check against last time'}]},
              {'slot': 'eod', 'realistic': True, 'flags': []}], 'summary': 'mostly real'}, open(os.path.join(d, 'u_chen_2026-09-03.json'), 'w'))
    json.dump({'uid': 'u_chen', 'day': '2026-09-08', 'turns': [{'slot': 'morning', 'realistic': False, 'flags': [{'kind': 'tester-probing', 'note': 'clicked every tab'}]}]},
              open(os.path.join(d, 'u_chen_2026-09-08.json'), 'w'))
    open(os.path.join(d, 'u_alan_2026-09-03.json'), 'w').write('{"uid": "u_alan", "turns": [{"slot": "morning", "realistic": "yes"}, {"slot": "eod", "realistic": false, "flags": [{"kind": "lazy"}]}]}')
    J1, e1 = CY.judge_load(os.path.join(d, 'u_chen_2026-09-03.json')); J3, e3 = CY.judge_load(os.path.join(d, 'u_alan_2026-09-03.json'))
    check(J1 and not e1 and len(e3) == 3, f'judge: a good file loads clean; a malformed one is reported, never a silent pass ({"; ".join(e3)})')
    dsc = CY.discount({'2026-09-03': {'phone': 6.0, 'desktop': 8.0}, '2026-09-08': {'phone': 4.0}},
                      {'2026-09-03': J1['turns'], '2026-09-08': [{'slot': 'morning', 'realistic': False}]})
    check(dsc['phone'] == {'raw': 5.0, 'discounted': 6.0} and dsc['desktop'] == {'raw': 8.0, 'discounted': 8.0} and dsc['flagged'] == 2 and dsc['turns'] == 5,
          f"judge: flagged turns discounted (phone raw {dsc['phone']['raw']} -> {dsc['phone']['discounted']}: day 3's only turn flagged counts nothing, day 1 at 3/4), {dsc['flagged']} of {dsc['turns']} turns flagged")
    db, w = fixture('right', B)
    w['cycle_done'] = {'C14': ['2026-09-03', 'work2']}
    res = CY.score(db, B, w, [], '2026-09-08', {'u_chen': diary}, d)
    md = CY.ledger_md(res)
    check(res['judge']['u_chen']['discount']['flagged'] == 2 and next(s for s in res['steps'] if s['id'] == 'C14').get('flagged') and 'judge file error' in md
          and '## Business cycle' in md and '### Money leaks planted in the cycle' in md and 'Coverage of each role' in md,
          'ledger: the Business cycle section with the step table, the money-leak table, coverage and the judge (a step done in a flagged turn is marked; file errors listed)')
    # ---- the planted vendors' replies, in their formats
    import world as WD
    class Fake: pass
    fw = Fake(); fw.cycle = B
    body = 'Please quote:\n\nLine | Item | Spec | Qty | Unit\nL1 | Framing lumber: supply | - | 1 | ls\nL2 | Drywall & cement board: supply | - | 1 | ls\n'
    m = {'subject': 'RFQ-2026-005 — request for quote', 'body': body, 'from': 'Chen Biron <chen@smartdesign.nyc>'}
    t1, a1 = WD.World.quote_reply(fw, B['parties']['brooklyn_lumber'], m)
    t2, a2 = WD.World.quote_reply(fw, B['parties']['gowanus_supply'], m)
    t3, a3 = WD.World.quote_reply(fw, B['parties']['atlantic_yard'], m)
    t4, _ = WD.World.quote_reply(fw, B['parties']['carroll_tile'], {'subject': 'RFQ-2026-006', 'body': 'L1 | Porcelain floor tile 12x24 matte: supply | - | 380 | sf\n', 'from': 'Chen'})
    check(re.search(r'^L2 \| Drywall & cement board: supply \| 1 ls \| \$2,187\.00 \| \$2,187\.00$', t1, re.M) and 'Lead time: 2' in t1,
          'quotes: Brooklyn Lumber answers in a table the app reads (L2 drywall lot $2,187.00, lead time)')
    check(a2 and '$1,695.00' in a2[0]['text'] and not a1 and 'Lead time' not in t3 and 'L2 the Drywall' in t3 and re.search(r'L1 \| .* \| 25 box \| \$229\.50 \| \$5,737\.50', t4),
          'quotes: Gowanus as a PDF with the typo price ($1,695.00 a sheet), Atlantic in prose with no lead time, Carroll by the box (25 boxes for 380 sf)')
    wh = {x: WD.World.who_is(fw, x) for x in ('the PM', 'Alan (PM)', 'the owner', 'Chen', 'Billing', 'Alan')}
    check(wh == {'the PM': 'u_alan', 'Alan (PM)': 'u_alan', 'the owner': 'u_owner', 'Chen': 'u_chen', 'Billing': 'u_billing', 'Alan': 'u_alan'},
          f'mail: every colleague resolves by name or role ("Alan" is the PM; the owner is "Alan Mishali" or "the owner") {wh}')
    # ---- what reached the person (docs "Missing")
    import docs as DC
    db, w = fixture('wrong', B)
    db['pos'].append({'id': 'P9', 'number': 'PO-2026-099', 'projectId': 'pA', 'vendor': 'Brooklyn Lumber', 'status': 'draft', 'lines': [{'item': 'GWB', 'qty': 25, 'price': 0}]})
    db['rfqs'].append({'id': 'r9', 'number': 'RFQ-2026-009', 'projectId': 'pA', 'vendors': [{'vendorId': 'vb'}, {'vendorId': 'vg'}, {'vendorId': 'va'}], 'sent': [], 'quotes': []})
    m1, m2, m3 = DC.missing(db, 'pos:P9'), DC.missing(db, 'rfqs:r9'), DC.missing(db, 'c.estimates:eA')
    check(any('draft' in x for x in m1) and any('$0' in x for x in m1) and any('none asked' in x for x in m2) and any('reaching the client' in x for x in m3),
          f'documents: "Missing" reads what reached the person: a $0 draft PO ({"; ".join(m1)}), an RFQ with vendors and none asked ({m2[0]}), an estimate marked sent that never reached the client')
    return FAILS


if __name__ == '__main__':
    unit()
    print(f"\n{N[0] - len(FAILS)}/{N[0]} checks passed")
    sys.exit(1 if FAILS else 0)
