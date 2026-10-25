"""sim/cycle_book.py: write sim/cycle_book.json, Pilot 3's required-work book (Alan, 2026-10-25). Invented data only.

Pilot 2 fed people mail and due dates to react to; nobody had to run the business. Pilot 3 adds ONE new invented
job, carried from the first inquiry to the progress invoice by the people who do each step, on top of the event
book, and plants the money leaks a seasoned person catches. Four roles play (Alan, 10-25: the owner, the PM, the
coordinator and billing). The other roles' steps are scripted world actions (the foreman's receiving, time and
daily log; the controller's statement import, the app's own matches and the payroll build) so the cycle still
closes end to end; the referee checks them like any step and collects no grades for them.

What the people get is top-down: the firm's goals and their own weekly objectives, as their boss would set them,
never steps or screen names (`objectives`, in the role cards). What the referee checks is bottom-up (`steps`,
`plants`, `questions`), computed by sim/cycle.py from the raw database, never from the app's report functions.

Inputs are messy on purpose: three lumber quotes in three formats (a table, a PDF with a typo price, prose with no
lead time), three tile quotes (one per box, not per square foot), a client who changes a selection, walk-through
notes with a gap that needs a question back, interruptions in the middle of a task.

    python3 sim/cycle_book.py        # writes sim/cycle_book.json and prints a summary
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'cycle_book.json')
D1, D2, D3 = '2026-09-03', '2026-09-04', '2026-09-08'
ROLES = ['u_owner', 'u_alan', 'u_chen', 'u_billing']

# ---------------------------------------------------------------- the job (invented)
WREN = 'Wren Ashby <wren.ashby@example.com>'
JULIAN = 'Julian Ashby <julian.ashby@example.com>'
JOB = {
    'client': 'Wren & Julian Ashby', 'client_rx': r'Ashby', 'job': '214 Lincoln Place', 'job_rx': r'Lincoln',
    'addr': '214 Lincoln Place, Park Slope, Brooklyn: parlor kitchen and garden-level bath', 'emails': ['wren.ashby@example.com', 'julian.ashby@example.com'],
    'phone': '(347) 555-0186', 'budget_said': 90000, 'start': '2026-09-08', 'deposit_pct': 25, 'retainage_pct': 10,
    'bank_desc': 'ONLINE TRANSFER FROM ASHBY W',
}
# The owner's takeoff from the walk-through: what a seasoned estimator would price. item, qty, unit, price (each),
# budget (the line's total cost), kind, the key the referee uses for the line.
TAKEOFF = [
    ('Demolition & protection: parlor kitchen and garden bath', 1, 'ls', 8400, 5600, 'labor', 'demo'),
    ('Framing & blocking: pantry wall, vanity and cabinet blocking', 1, 'ls', 6200, 4100, 'labor', 'frame'),
    ('Framing lumber: supply', 1, 'ls', 1450, 1100, 'materials', 'lumber'),
    ('Drywall & cement board: supply', 1, 'ls', 2450, 1800, 'materials', 'drywall'),
    ('Drywall hang, tape & prime (SD crew)', 1, 'ls', 7800, 5200, 'labor', 'hang'),
    ('Porcelain floor tile 12x24 matte: supply', 380, 'sf', 19, 5510, 'materials', 'tile'),
    ('Tile setting & waterproofing (SD crew)', 1, 'ls', 9600, 6400, 'labor', 'set'),
    ('Electrical rough-in & devices (SD Electric)', 1, 'ls', 11500, 7900, 'labor', 'elec'),
    ('Plumbing rough & finish, garden bath (SD Plumbing)', 1, 'ls', 14200, 10300, 'labor', 'plumb'),
    ('Rear wall repointing (Ironbound Masonry, sub)', 1, 'ls', 6800, 5400, 'sub', 'mason'),
    ('Plumbing fixture allowance: garden bath', 1, 'ls', 6500, 6500, 'allowance', 'allow'),
    ("General conditions & builder's fee", 1, 'ls', 9000, 0, 'fee', 'fee'),
]
RADIATOR = ('Relocate the garden bath radiator under the window', 1, 'ls', 1400, 950, 'labor', 'radiator')
# what the job needs bought (the material schedule the coordinator receives once it is signed)
SCHEDULE = {
    'lumber': [('2x4x8 SPF stud', 60, 'pc'), ('2x6x10 SPF', 12, 'pc'), ('3/4" CDX plywood 4x8', 6, 'sheet')],
    'drywall': [('5/8" Type X drywall 4x8', 80, 'sheet'), ('1/2" cement board 3x5', 30, 'sheet')],
    'tile': [('Porcelain floor tile 12x24 matte, Warm Grey', 380, 'sf')],
    'elec': [('12/2 NM-B 250 ft', 3, 'roll'), ('1-gang new-work boxes', 30, 'ea')],
}
# the firm's own stock on day one (the app's seed, DB.stock.opening): what the job needs that already sits there
IN_STOCK = [{'inv': 'iv10', 'name': '12/2 NM-B', 'rx': r'12/2|NM-?B|romex', 'need': 3, 'unit': 'roll', 'cost': 98.0},
            {'inv': 'iv9', 'name': '1-gang new-work boxes', 'rx': r'1-?gang|new.?work box|boxes', 'need': 30, 'unit': 'ea', 'cost': 1.2},
            {'inv': 'iv16', 'name': '5/8" Type X drywall 4x8', 'rx': r'type x|5/8', 'need': 12, 'unit': 'sheet', 'cost': 16.8}]
LAST_PRICE = {'vendor': 'Nemo Tile', 'po': 'PO-2026-041', 'item': 'Calacatta porcelain 12x24', 'unit_price': 12.50, 'unit': 'sf'}

# ---------------------------------------------------------------- the vendors and their quotes (planted)
# unit prices by the schedule's item; `form` is how the quote comes back (messy on purpose)
QUOTES = {
    'brooklyn_lumber': {'form': 'table', 'lead': 2, 'freight': 0, 'valid': 30,
                        'prices': {'2x4': 6.10, '2x6': 11.20, 'plywood': 58.00, 'type x': 17.40, 'cement': 26.50}},
    'gowanus_supply': {'form': 'pdf', 'lead': 3, 'freight': 45, 'valid': 15, 'typo': 'type x',
                       'prices': {'2x4': 5.95, '2x6': 10.90, 'plywood': 56.50, 'type x': 16.95, 'cement': 27.10}},
    'atlantic_yard': {'form': 'prose', 'lead': None, 'freight': 0, 'valid': 30,
                      'prices': {'2x4': 6.40, '2x6': 11.75, 'plywood': 61.00, 'type x': 18.10, 'cement': 28.00}},
    'nemo_tile': {'form': 'table', 'lead': 4, 'freight': 0, 'valid': 30, 'prices': {'porcelain|tile': 13.90}},
    'bergen_tile': {'form': 'pdf', 'lead': 6, 'freight': 75, 'valid': 30, 'prices': {'porcelain|tile': 14.75}},
    'carroll_tile': {'form': 'box', 'lead': 5, 'freight': 0, 'valid': 20, 'box_sf': 15.5, 'prices': {'porcelain|tile': 229.50}},
}
ITEM_RX = {'2x4': r'2x4', '2x6': r'2x6', 'plywood': r'ply', 'type x': r'type x|5/8|gwb|gypsum|sheetrock',
           'cement': r'cement|durock|backer', 'porcelain|tile': r'porcelain|tile'}
LOTS = {'lumber': r'lumber|framing', 'drywall': r'drywall|cement board|gwb|gypsum', 'tile': r'tile|porcelain'}
PARTIES = {
    'ashby': {'name': 'Wren Ashby', 'addr': WREN, 'kind': 'client', 'reply_p': 1.0, 'delay': [0, 0], 'late_p': 0, 'no_bank': True,
              'book_plays': ['approve', 'pay'],
              'answers': [[r'radiator', "Move it, please: under the window where we want the vanity it is in the way. Julian agrees. Wren"],
                          [r'start|schedule|when', "Tuesday the 8th works for us; we will leave a key with the super. Wren"],
                          [r'update|week', "Thank you for the update, that is clear. Wren"]],
              'voice': 'A new client: bought 214 Lincoln Place, Park Slope. Decisive, writes short mails, wants the price and the start date in writing.'},
    'julian_ashby': {'name': 'Julian Ashby', 'addr': JULIAN, 'kind': 'client', 'reply_p': 0.0, 'delay': [0, 0], 'late_p': 0, 'no_bank': True,
                     'voice': 'Wren\'s husband; reads everything, rarely answers.'},
    'brooklyn_lumber': {'name': 'Brooklyn Lumber', 'addr': 'Brooklyn Lumber <orders@brooklynlumber.example>', 'kind': 'vendor', 'reply_p': 1.0, 'delay': [0, 0], 'late_p': 0,
                        'contact': 'Sal Ferro', 'voice': 'The yard the firm uses most for lumber and drywall. Quick, quotes in a table.'},
    'gowanus_supply': {'name': 'Gowanus Building Supply', 'addr': 'Gowanus Building Supply <orders@gowanusbuilding.example>', 'kind': 'vendor', 'reply_p': 1.0, 'delay': [0, 0], 'late_p': 0,
                       'contact': 'Dee Marsh', 'voice': 'A smaller yard on 3rd Avenue; sends quotes as a PDF off their system.'},
    'atlantic_yard': {'name': 'Atlantic Yard Supply', 'addr': 'Atlantic Yard Supply <sales@atlanticyardsupply.example>', 'kind': 'vendor', 'reply_p': 1.0, 'delay': [0, 0], 'late_p': 0,
                      'contact': 'Ray Quint', 'voice': 'A yard on Atlantic Avenue; answers in a paragraph, forgets details.'},
    'nemo_tile': {'name': 'Nemo Tile', 'addr': 'Nemo Tile <sales@nemotile.example>', 'kind': 'vendor', 'reply_p': 1.0, 'delay': [0, 0], 'late_p': 0,
                  'contact': 'Lena Russo', 'voice': 'The tile house the firm bought from in August (PO-2026-041).'},
    'bergen_tile': {'name': 'Bergen Tile Gallery', 'addr': 'Bergen Tile Gallery <quotes@bergentile.example>', 'kind': 'vendor', 'reply_p': 1.0, 'delay': [0, 0], 'late_p': 0,
                    'contact': 'Omar Haddad', 'voice': 'A tile showroom on Bergen Street.'},
    'carroll_tile': {'name': 'Carroll Street Tile', 'addr': 'Carroll Street Tile <desk@carrollstreettile.example>', 'kind': 'vendor', 'reply_p': 1.0, 'delay': [0, 0], 'late_p': 0,
                     'contact': 'June Pak', 'voice': 'A tile importer; prices by the box.'},
    'ironbound': {'name': 'Ironbound Masonry', 'addr': 'Ironbound Masonry <office@ironboundmasonry.example>', 'kind': 'sub', 'reply_p': 0.9, 'delay': [0, 1], 'late_p': 0,
                  'voice': 'A masonry sub the firm uses for repointing.'},
}
for k, q in QUOTES.items(): PARTIES[k]['quotes'] = q

# ---------------------------------------------------------------- what each role is asked for (top-down)
# The goals a boss sets for the week, from the role's measures in docs/STANDARD.md (loaded at run time from the
# app's live copy, never paraphrased here). Outcomes, never steps or screen names.
OBJECTIVES = {
    'u_owner': [
        'Win the Ashbys (214 Lincoln Place) this week at the firm\'s margin: they want a signed price by Friday and to start Tuesday 9/8.',
        'Keep cash and AR honest: know what is in the bank, what is owed to us and what is owed by us, every day.',
        'Nothing that only you can approve waits more than a day; nothing that should not reach you does.',
        'At Tuesday\'s team meeting, bring the numbers: where each job stands against its estimate, what is over, what is done and not billed, and cash.',
    ],
    'u_alan': [
        '214 Lincoln Place: price it right from the walk-through and get it started Tuesday 9/8 with the field fed: no crew waiting on a decision, a drawing or material.',
        'Margin on every job you run holds at or above the estimate; every change is priced and signed within 48 hours of the cause.',
        'Friday: the weekly review of each of your jobs (the next three weeks, budget against committed and actual by estimate line, open changes, RFIs, submittals and decisions) and the client update.',
        'At Tuesday\'s team meeting, bring each job\'s numbers by estimate line and what is over.',
    ],
    'u_chen': [
        'Buy out 214 Lincoln Place (lumber, drywall and cement board, tile, the electrical rough-in material) under each estimate line, on site before the crew needs it, without moving the schedule.',
        'Three quotes on anything over $2,500; every price checked against what we paid last time; nothing bought that we already have.',
        'Every vendor bill matches its PO and what actually arrived before anyone pays it.',
        'At Tuesday\'s meeting: what is committed against each line you bought for, and what is over.',
    ],
    'u_billing': [
        'Every milestone invoiced within 2 business days, deposits the day a contract is signed, changes billed once approved, and anything bought for a client billed back.',
        'Every payment that lands is matched to its invoice and its bank line the day it arrives; collections at due, 7, 15 and 30 days.',
        'At Tuesday\'s meeting: AR by client, cash received this week, what is done and not yet billed, and anything bought for a client not billed back.',
    ],
}
# Which parts of the live Standard each person is handed (the app's STD_ROLE_PLAYBOOKS, plus the company sections)
STANDARD_FOR = {'u_owner': {'role': 'owner', 'playbooks': []}, 'u_alan': {'role': 'pm', 'playbooks': ['pm', 'client', 'estimating']},
                'u_chen': {'role': 'coord', 'playbooks': ['procurement']}, 'u_billing': {'role': 'billing', 'playbooks': ['office', 'client']}}
# The questions for Tuesday's meeting (day 3, end of day). The referee computes every answer from the raw records.
QUESTIONS = {
    'u_owner': [['Q1', 'cash', 'Cash in the bank today, by account and in total.'],
                ['Q2', 'ar', 'What clients owe us today (open invoices), by client and in total.'],
                ['Q3', 'over_lines', 'On 214 Lincoln Place, which estimate lines are over budget (committed or actual above the line\'s budget) and by how much.'],
                ['Q4', 'unbilled', 'Work done and not billed, by job.'],
                ['Q5', 'reimb', 'Purchases made for a client that are not billed back yet.']],
    'u_alan': [['Q1', 'line_table', 'For 214 Lincoln Place: each estimate line\'s budget, committed and actual.'],
               ['Q2', 'over_lines', 'Which of those lines are over, and by how much.'],
               ['Q3', 'open_cos', 'Change orders on your jobs not yet approved, or approved and not billed.'],
               ['Q4', 'unbilled', 'Work done and not billed on 214 Lincoln Place and 121 State Street.']],
    'u_chen': [['Q1', 'committed_lines', 'For 214 Lincoln Place: committed (POs) against each line you bought for, and its budget.'],
               ['Q2', 'over_lines', 'Which lines are over budget and by how much.'],
               ['Q3', 'price_vs_last', 'Where we paid more than the last time we bought the same thing, and how much more.']],
    'u_billing': [['Q1', 'ar', 'AR by client and in total.'],
                  ['Q2', 'cash_in', 'Payments received this week (9/3 to 9/8) and the invoices they paid.'],
                  ['Q3', 'unbilled', 'Work done and not billed, by job.'],
                  ['Q4', 'reimb', 'Purchases made for a client that are not billed back yet.']],
}

# ---------------------------------------------------------------- the steps the referee checks (sim/cycle.py)
# id, the role who owns it (u_* in ROLES; 'script:<role>' for a scripted world action), what it is, due day, by
# (working days), the money at stake if missed
STEPS = [
    ['C01', 'u_owner', 'The Ashbys\' inquiry on file as a lead (name, contact, property)', D1, 0, 0],
    ['C02', 'u_owner', 'The lead won: the Ashbys a client, once (no duplicate client)', D1, 1, 0],
    ['C03', 'u_owner', 'A project for 214 Lincoln Place under the client', D1, 1, 0],
    ['C04', 'u_owner|u_alan', 'The gap in the walk-through (the radiator) asked back to the client before it is priced', D1, 1, 0],
    ['C05', 'u_alan|u_owner', 'The estimate: 8+ lines (labor, materials, a sub, an allowance, a fee), quantity, price and budget on every line, on the project', D1, 1, 0],
    ['C06', 'u_owner|u_alan', 'The estimate sent, and it reached the Ashbys', D1, 1, 0],
    ['C07', 'u_owner|u_alan', 'The Ashbys\' signature recorded on the estimate (who, when)', D1, 1, 0],
    ['C08', 'u_owner|u_alan|u_billing', 'The contract and the schedule of values from the estimate (every SOV line linked to its estimate line)', D1, 1, 0],
    ['C10', 'u_chen', 'An RFQ from several estimate lines at once (each RFQ line linked to its estimate line)', D2, 1, 0],
    ['C11', 'u_chen', 'RFQs sent to three vendors each, and they reached the vendors', D2, 1, 0],
    ['C12', 'u_chen', 'Three quotes behind every order over $2,500 on 214 Lincoln', D2, 1, 0],
    ['C13', 'u_chen', 'The quotes recorded and the award made', D2, 1, 0],
    ['C14', 'u_chen', 'POs from the estimate lines (vendor, price, every line linked), sent, and they reached the vendor', D2, 1, 0],
    ['C15', 'u_chen', 'The vendors\' bills entered against their POs (job, cost code, PO)', D3, 1, 0],
    ['C20', 'script:u_angel', 'Deliveries received against their POs, one short and one damaged (scripted foreman)', D3, 0, 0],
    ['C21', 'script:u_angel', 'Hours on 214 Lincoln on cost codes, and the daily log (scripted field)', D3, 0, 0],
    ['C22', 'script:u_controller', 'Bank and card statements imported; the app\'s own proposed matches confirmed (scripted controller)', D3, 0, 0],
    ['C23', 'script:u_controller', 'The 8/31-9/4 payroll built from approved hours (scripted controller)', D3, 0, 0],
    ['C24', 'u_owner', 'The 8/31-9/4 payroll approved by the owner', D3, 1, 0],
    ['C30', 'u_billing', 'The deposit invoice on the contract, sent within 2 business days of signing', D1, 2, 0],
    ['C31', 'u_billing', 'The Ashbys\' deposit recorded against the invoice and its bank line', D3, 1, 0],
    ['C32', 'u_billing', 'The progress invoice from the schedule of values, with retainage, sent', D3, 2, 0],
    ['C33', 'u_billing', 'The approved change order billed', D2, 2, 0],
    ['C40', 'u_alan', 'The vanity change priced (price, cost, days), sent within 48 hours and its approval recorded', D2, 2, 0],
    ['C41', 'u_alan', 'The Friday review of each job: look-ahead, budget against committed and actual, changes, RFIs, submittals, decisions', D2, 0, 0],
    ['C42', 'u_alan', 'The Friday client update (each job\'s client)', D2, 0, 0],
    ['C50', 'u_owner', 'The owner\'s numbers for the meeting, against the referee\'s', D3, 0, 0],
    ['C51', 'u_alan', 'The PM\'s numbers for the meeting, against the referee\'s', D3, 0, 0],
    ['C52', 'u_chen', 'The coordinator\'s numbers for the meeting, against the referee\'s', D3, 0, 0],
    ['C53', 'u_billing', 'Billing\'s numbers for the meeting, against the referee\'s', D3, 0, 0],
    ['C60', 'u_owner', 'The Ashbys\' call in the middle of the estimate answered', D1, 0, 0],
    ['C61', 'u_chen', 'The yard\'s backorder call handled (decided and written down)', D2, 0, 0],
    ['C62', 'u_alan', 'Angel\'s call about the pantry GFI answered', D2, 0, 0],
    ['C63', 'u_billing', 'David Klein\'s mail about the retainage answered within 2 hours', D3, 0, 0],
]
# The planted money leaks. The referee says whether each plant held (the people's own records made it real), who
# caught it (the app, a person, nobody) and the money left behind if nobody did.
PLANTS = [
    {'id': 'L1', 'kind': 'over_line', 'line': 'drywall', 'what': 'A PO priced over its estimate line\'s budget (every yard\'s drywall price is above the line)', 'owner': 'u_chen'},
    {'id': 'L2', 'kind': 'in_stock', 'what': 'Material the job needs already in the firm\'s stock (12/2 NM-B, 1-gang boxes, 5/8 Type X)', 'owner': 'u_chen'},
    {'id': 'L3', 'kind': 'price_vs_last', 'line': 'tile', 'what': 'The cheapest tile quote is Nemo Tile at $13.90/sf, above the $12.50/sf on PO-2026-041', 'owner': 'u_chen'},
    {'id': 'L4', 'kind': 'bill_over_po', 'line': 'tile', 'what': 'The tile invoice adds a $95 fuel surcharge and a $45 pallet deposit the PO never had', 'owner': 'u_chen', 'over': 140.0},
    {'id': 'L5', 'kind': 'short', 'line': 'drywall', 'what': 'The drywall delivery came 6 cement boards short; the invoice bills all of them', 'owner': 'u_chen', 'qty': 6},
    {'id': 'L6', 'kind': 'damaged', 'line': 'tile', 'what': 'Two boxes of tile (31 sf) arrived cracked; the invoice bills all of them', 'owner': 'u_chen', 'qty_sf': 31},
    {'id': 'L7', 'kind': 'reimbursable', 'what': 'Two pendant lights bought for the Ashbys on the Amex ($612.40) to bill back at cost', 'owner': 'u_billing', 'amount': 612.40, 'desc': 'LIGHTOLOGY CHICAGO IL'},
    {'id': 'L8', 'kind': 'co_unbilled', 'what': 'The approved vanity change order not billed', 'owner': 'u_billing'},
    {'id': 'L9', 'kind': 'work_unbilled', 'what': 'Demolition measured on site and not billed', 'owner': 'u_billing'},
]

X = lambda who, what, by, step, see=None, money=0, days=0: {'who': who, 'what': what, 'by': by, 'see': see or [], 'check': {'t': 'cy', 'step': step}, 'money': money, 'days': days}
G = lambda step, **kw: dict({'t': 'cy', 'step': step}, **kw)
NOTES = ('Walk-through, 214 Lincoln Place (Wren and Julian Ashby), yesterday 5 pm. Parlor kitchen gut and a new garden-level bath. '
         'They said about $90,000 and want to start Tuesday 9/8. My takeoff (price to them / our cost):\n'
         + '\n'.join(f'- {it}: {q} {u} at ${p:,.2f} each (cost ${c:,.0f})' for it, q, u, p, c, k, key in TAKEOFF)
         + '\n- Garden bath radiator: Wren was not sure whether to keep it or move it under the window. Ask before pricing the plumbing '
           f'(moving it: ${RADIATOR[3]:,} to them, ${RADIATOR[4]:,} cost).\n'
         'Terms: 25% deposit on signing, progress billing monthly from the schedule of values, 10% retainage. Valid 30 days.')
BUYLIST = ('214 Lincoln Place is signed. Demo starts Tuesday 9/8. Material, with the dates it is needed on site:\n'
           + '- Framing lumber, by Tue 9/8: ' + '; '.join(f'{q} {u} {it}' for it, q, u in SCHEDULE['lumber']) + '\n'
           + '- Drywall and cement board, by Wed 9/9: ' + '; '.join(f'{q} {u} {it}' for it, q, u in SCHEDULE['drywall']) + '\n'
           + '- Floor tile, by Fri 9/11: ' + '; '.join(f'{q} {u} {it}' for it, q, u in SCHEDULE['tile']) + '\n'
           + '- Electrical rough-in material, by Tue 9/8: ' + '; '.join(f'{q} {u} {it}' for it, q, u in SCHEDULE['elec']) + '\n'
           'The yards we use for lumber and drywall: Brooklyn Lumber (orders@brooklynlumber.example), Gowanus Building Supply '
           '(orders@gowanusbuilding.example), Atlantic Yard Supply (sales@atlanticyardsupply.example). For tile: Nemo Tile '
           '(sales@nemotile.example), Bergen Tile Gallery (quotes@bergentile.example), Carroll Street Tile (desk@carrollstreettile.example).')

EVENTS = [
    # ---- day 1: the inquiry, the walk-through notes, the estimate, the signature
    {'id': 'Y-01', 'day': D1, 'time': '07:20', 'kind': 'mail', 'tags': ['cycle', 'lead'],
     'payload': {'from': WREN, 'to': ['Alan Mishali <alan@smartdesign.nyc>'], 'cc': ['Alan <alan.pm@smartdesign.nyc>', JULIAN], 'thread': 'cy_ashby', 'att': [],
                 'subject': '214 Lincoln Place: thank you for yesterday',
                 'text': 'Hi Alan, thank you both for walking the house with us yesterday. As we said, the parlor kitchen and a new bath on the garden '
                         'level, about $90,000 all in, and we would love to start Tuesday the 8th. Can we have your price by Friday? '
                         f'Wren Ashby, {JOB["phone"]}'},
     'expect': X('u_owner', 'Put the Ashbys (214 Lincoln Place) on file', 0, 'C01', ['Ashby'])},
    {'id': 'Y-02', 'day': D1, 'time': '07:20', 'kind': 'situation', 'tags': ['cycle', 'lead'], 'payload': {'uid': 'u_owner', 'text': 'Your own notes from yesterday: ' + NOTES},
     'expect': X('u_owner', 'Make the Ashbys a client and open 214 Lincoln Place', 1, 'C02', ['Ashby'])},
    {'id': 'Y-03', 'day': D1, 'time': '07:20', 'kind': 'situation', 'tags': ['cycle', 'estimate'],
     'payload': {'uid': 'u_alan', 'text': 'You walked 214 Lincoln Place with Alan (the owner) and the Ashbys yesterday. Alan\'s notes, which he read out in the car: ' + NOTES},
     'expect': X('u_alan', 'Price 214 Lincoln Place from the walk-through (8+ real lines on the project)', 1, 'C05', ['Lincoln'])},
    {'id': 'Y-04', 'day': D1, 'time': '07:20', 'kind': 'seed', 'tags': ['cycle'], 'payload': {},
     'expect': X('u_owner', 'Open 214 Lincoln Place under the Ashbys', 1, 'C03', ['Lincoln'])},
    {'id': 'Y-05', 'day': D1, 'time': '07:20', 'kind': 'seed', 'tags': ['cycle'], 'payload': {},
     'expect': X('u_owner', 'Ask the Ashbys about the radiator before pricing the plumbing', 1, 'C04', ['radiator'])},
    {'id': 'Y-06', 'day': D1, 'time': '07:20', 'kind': 'seed', 'tags': ['cycle'], 'payload': {},
     'expect': X('u_owner', 'Send the Ashbys the estimate by Friday', 1, 'C06', ['Ashby'])},
    {'id': 'Y-07', 'day': D1, 'time': '10:30', 'kind': 'interrupt', 'tags': ['cycle', 'interrupt'], 'gate': G('C03'),
     'payload': {'uid': 'u_owner', 'after_min': 20, 'from': 'Wren Ashby', 'via': 'call',
                 'text': 'Your phone rings: Wren Ashby. "Sorry to bother you. Two things: can you really start Tuesday the 8th, and do you need us home for anything before then?"'},
     'expect': X('u_owner', 'Answer Wren\'s call (start date, access) and come back to the work', 0, 'C60', ['Ashby'])},
    {'id': 'Y-08', 'day': D1, 'time': '07:00', 'kind': 'mail', 'tags': ['cycle', 'contract'], 'gate': G('C06', need='right'),
     'payload': {'from': WREN, 'to': ['Alan Mishali <alan@smartdesign.nyc>'], 'cc': ['Alan <alan.pm@smartdesign.nyc>', JULIAN], 'thread': 'cy_ashby',
                 'subject': 'Re: {number}: signed',
                 'text': 'We read {number} ({total$}) and accept it as written. Signed copy attached. Please send the deposit invoice. Wren',
                 'att': [{'filename': 'Signed {number}.pdf', 'text': 'ACCEPTANCE\n{number}\n214 Lincoln Place\nAccepted as written, {total$}.\nSigned: Wren Ashby, Julian Ashby, {today}'}]},
     'expect': X('u_owner', 'Record the Ashbys\' signature on {number}', 1, 'C07', ['{number}'])},
    {'id': 'Y-09', 'day': D1, 'time': '07:00', 'kind': 'seed', 'tags': ['cycle', 'contract'], 'gate': G('C07'), 'payload': {},
     'expect': X('u_owner', 'The contract and the schedule of values from {number}', 1, 'C08', ['{number}'])},
    # ---- day 2: buying out, the deposit, the change, Friday's review
    {'id': 'Y-10', 'day': D2, 'time': '07:30', 'kind': 'situation', 'tags': ['cycle', 'buy'], 'gate': G('C07'),
     'payload': {'uid': 'u_chen', 'text': 'At the 8:00 huddle Alan (the owner) said: ' + BUYLIST},
     'expect': X('u_chen', 'Ask for quotes on 214 Lincoln\'s material from the estimate lines', 1, 'C10', ['Lincoln'])},
    {'id': 'Y-11', 'day': D2, 'time': '07:30', 'kind': 'seed', 'tags': ['cycle', 'buy'], 'gate': G('C07'), 'payload': {},
     'expect': X('u_chen', 'Three vendors asked on each RFQ, and the requests reached them', 1, 'C11', ['RFQ'])},
    {'id': 'Y-12', 'day': D2, 'time': '07:30', 'kind': 'seed', 'tags': ['cycle', 'buy'], 'gate': G('C07'), 'payload': {},
     'expect': X('u_chen', 'Award and order 214 Lincoln\'s material from the estimate lines, and send the POs', 1, 'C14', ['Lincoln'])},
    {'id': 'Y-13', 'day': D2, 'time': '07:30', 'kind': 'situation', 'tags': ['cycle', 'deposit'], 'gate': G('C07'),
     'payload': {'uid': 'u_billing', 'text': 'At the huddle you heard 214 Lincoln Place (the Ashbys) signed yesterday: 25% deposit on signing, progress monthly, 10% retainage.'},
     'expect': X('u_billing', 'The Ashbys\' deposit invoice, sent', 2, 'C30', ['Ashby'])},
    {'id': 'Y-14', 'day': D2, 'time': '07:30', 'kind': 'situation', 'tags': ['cycle', 'reimbursable'],
     'payload': {'uid': 'u_alan', 'text': 'Last night on your way home you picked up the two pendant lights Wren chose for the kitchen island at Lightology, '
                                          '$612.40 on the firm\'s Amex 1009. They are not in the contract; Wren said to put them on the next invoice at cost. The receipt is in your bag.'},
     'expect': X('u_billing', 'Bill the Ashbys back for the pendants ($612.40)', 3, 'C34', ['pendant'], money=612.40)},
    {'id': 'Y-15', 'day': D2, 'time': '08:15', 'kind': 'mail', 'tags': ['cycle', 'change'], 'gate': G('C07'),
     'payload': {'from': WREN, 'to': ['Alan <alan.pm@smartdesign.nyc>'], 'cc': [JULIAN], 'thread': 'cy_ashby_vanity', 'att': [],
                 'subject': 'Garden bath vanity: change of plan',
                 'text': 'Hi Alan, we went to the showroom: we want the 36-inch Rhea vanity in walnut ($2,380) instead of the 30-inch one in the allowance '
                         '($1,640). Does it change anything else, and what does it add? Wren'},
     'expect': X('u_alan', 'Price the vanity change (price, cost, days) and send it within 48 hours', 2, 'C40', ['vanity'])},
    {'id': 'Y-16', 'day': D2, 'time': '07:00', 'kind': 'mail', 'tags': ['cycle', 'change'], 'gate': G('C40', state='sent'),
     'payload': {'from': WREN, 'to': ['Alan <alan.pm@smartdesign.nyc>'], 'cc': [JULIAN], 'thread': 'cy_ashby_vanity', 'att': [],
                 'subject': 'Re: {number}', 'text': 'Approved, go ahead with the 36-inch vanity ({number}, {total$}). Wren'},
     'expect': X('u_alan', 'Record the Ashbys\' approval of {number}', 1, 'C40', ['{number}'])},
    {'id': 'Y-17', 'day': D2, 'time': '07:00', 'kind': 'seed', 'tags': ['cycle', 'change'], 'gate': G('C40'), 'payload': {},
     'expect': X('u_billing', 'Bill the approved {number}', 2, 'C33', ['{number}'], money='{total}')},
    {'id': 'Y-18', 'day': D2, 'time': '10:30', 'kind': 'interrupt', 'tags': ['cycle', 'interrupt'], 'gate': G('C11'),
     'payload': {'uid': 'u_chen', 'after_min': 20, 'from': 'Gowanus Building Supply', 'via': 'call',
                 'text': 'Your phone rings: Dee at Gowanus Building Supply. "About your RFQ: the 1/2-inch cement board is backordered a week on our side. '
                         'I can do 1/2-inch Durock NEXT Gen at the same price, in stock. Want me to quote that instead?"'},
     'expect': X('u_chen', 'Decide on Gowanus\' substitute and write it down', 0, 'C61', ['Durock'])},
    {'id': 'Y-19', 'day': D2, 'time': '10:30', 'kind': 'interrupt', 'tags': ['cycle', 'interrupt'],
     'payload': {'uid': 'u_alan', 'after_min': 15, 'from': 'Angel', 'via': 'call',
                 'text': 'Your phone rings: Angel, from 121 State. "John the plumber asks if the pantry GFI change is approved, so he can do it Monday with the rough. Yes or no?"'},
     'expect': X('u_alan', 'Answer Angel about the pantry GFI', 0, 'C62', ['GFI'])},
    {'id': 'Y-20', 'day': D2, 'time': '13:30', 'kind': 'seed', 'tags': ['cycle', 'routine'], 'payload': {},
     'expect': X('u_alan', 'Friday: review each job (look-ahead, budget against committed and actual, changes, RFIs, submittals, decisions)', 0, 'C41')},
    {'id': 'Y-21', 'day': D2, 'time': '13:30', 'kind': 'seed', 'tags': ['cycle', 'routine'], 'payload': {},
     'expect': X('u_alan', 'Friday: the weekly client update for each job', 0, 'C42')},
    # ---- day 3: the trucks, the bills, the bank, the progress invoice, the numbers
    {'id': 'Y-30', 'day': D2, 'time': '07:00', 'kind': 'script', 'tags': ['cycle', 'receiving'], 'gate': G('C14', line='drywall'), 'delay': 1,
     'payload': {'do': 'receive', 'as': 'u_angel', 'number': '{number}', 'line': 'drywall', 'short': {'rx': 'cement', 'qty': 6, 'why': 'backordered, balance next week'}, 'notify': 'u_chen'},
     'expect': X('u_angel', 'Receive the drywall order short 6 cement boards (scripted foreman)', 0, 'C20')},
    {'id': 'Y-31', 'day': D2, 'time': '07:00', 'kind': 'script', 'tags': ['cycle', 'receiving'], 'gate': G('C14', line='tile'), 'delay': 1,
     'payload': {'do': 'receive', 'as': 'u_angel', 'number': '{number}', 'line': 'tile', 'damaged': {'rx': 'tile|porcelain', 'qty': 31, 'unit': 'sf', 'why': 'two boxes cracked in the pallet'}, 'notify': 'u_chen'},
     'expect': X('u_angel', 'Receive the tile with two boxes damaged (scripted foreman)', 0, 'C20')},
    {'id': 'Y-29', 'day': D2, 'time': '07:00', 'kind': 'script', 'tags': ['cycle', 'receiving'], 'gate': G('C14', line='lumber'), 'delay': 1,
     'payload': {'do': 'receive', 'as': 'u_angel', 'number': '{number}', 'line': 'lumber', 'notify': 'u_chen'},
     'expect': X('u_angel', 'Receive the lumber in full (scripted foreman)', 0, 'C20')},
    {'id': 'Y-32', 'day': D3, 'time': '10:30', 'kind': 'mail', 'tags': ['cycle', 'bill'], 'after': 'Y-30', 'mint': {'inv': 'vendor_invoice'},
     'payload': {'from': '{vendor_addr}', 'to': ['Chen Biron <chen@smartdesign.nyc>'], 'cc': [], 'thread': 'cy_inv_dw', 'subject': 'Invoice {inv} for {number}',
                 'text': 'Invoice {inv} for {number} (214 Lincoln Place) attached: {total$}, net 30.',
                 'att': [{'filename': 'Invoice {inv}.pdf', 'text': 'INVOICE {inv}\n{vendor}\nPO: {number}\nShip to: 214 Lincoln Place\nAll lines as ordered\nTOTAL {total$}\nNet 30'}]},
     'expect': X('u_chen', 'Enter {inv} against {number}', 1, 'C15', ['{inv}'])},
    {'id': 'Y-33', 'day': D3, 'time': '10:30', 'kind': 'mail', 'tags': ['cycle', 'bill'], 'after': 'Y-31', 'mint': {'inv': 'vendor_invoice'},
     'payload': {'from': '{vendor_addr}', 'to': ['Chen Biron <chen@smartdesign.nyc>'], 'cc': [], 'thread': 'cy_inv_tile', 'subject': 'Invoice {inv} for {number}',
                 'text': 'Please find invoice {inv} for {number} attached: {over_total$} including fuel surcharge and pallet deposit. Due net 30.',
                 'att': [{'filename': 'Invoice {inv}.pdf', 'text': 'INVOICE {inv}\n{vendor}\nPO: {number}\nShip to: 214 Lincoln Place\nMaterial as ordered {total$}\n'
                                                                  'Fuel surcharge $95.00\nPallet deposit $45.00\nTOTAL {over_total$}\nNet 30'}]},
     'expect': X('u_chen', 'Enter {inv} against {number}', 1, 'C15', ['{inv}'])},
    {'id': 'Y-37', 'day': D3, 'time': '07:05', 'kind': 'script', 'tags': ['cycle', 'scripted'], 'payload': {'do': 'payroll', 'as': 'u_controller'},
     'expect': X('u_controller', 'The 8/31-9/4 payroll built from approved hours (scripted controller)', 0, 'C23')},
    {'id': 'Y-34', 'day': D3, 'time': '07:10', 'kind': 'script', 'tags': ['cycle', 'field'], 'gate': G('C03'),
     'payload': {'do': 'field_day', 'as': 'u_angel', 'project': '{job}', 'task_rx': {'demo': 'demo'}, 'hours': [['u_angel', 'demo', 8.5, 'Demo, parlor kitchen'], ['u_alberto', 'demo', 8.0, 'Demo and protection'],
                                                              ['u_alex', 'demo', 4.0, 'Dumpster runs']], 'measure': [['demo', 40]],
                 'log': 'Demo started at 214 Lincoln Place: parlor kitchen cabinets and plaster out, floor protected; dumpster swapped once.'},
     'expect': X('u_angel', 'Hours on cost codes and the daily log on 214 Lincoln (scripted field)', 0, 'C21')},
    {'id': 'Y-35', 'day': D3, 'time': '07:40', 'kind': 'bank', 'tags': ['cycle', 'reimbursable'],
     'payload': {'acct': 'ac2', 'date': D2, 'desc': 'LIGHTOLOGY CHICAGO IL', 'amt': -612.40, 'ref': 'AC2-20260904-LIGHT'},
     'expect': X('u_billing', 'The pendants on the Amex billed back to the Ashbys', 3, 'C34', ['LIGHTOLOGY'], money=612.40)},
    {'id': 'Y-36', 'day': D1, 'time': '07:40', 'kind': 'bank', 'tags': ['cycle', 'deposit'], 'gate': G('C30'), 'delay': 1,
     'payload': {'acct': 'ac1', 'date': '{today}', 'desc': JOB['bank_desc'], 'amt': '{total}', 'ref': 'AC1-{today}-ASHBY'},
     'expect': X('u_billing', 'Record the Ashbys\' deposit ({total$}) against {number}', 1, 'C31', ['ASHBY'], money='{total}')},
    {'id': 'Y-38', 'day': D3, 'time': '10:30', 'kind': 'seed', 'tags': ['cycle', 'payroll'], 'payload': {},
     'expect': X('u_owner', 'Approve the 8/31-9/4 payroll', 1, 'C24')},
    {'id': 'Y-39', 'day': D3, 'time': '07:10', 'kind': 'seed', 'tags': ['cycle', 'progress'], 'after': 'Y-34', 'payload': {},
     'expect': X('u_billing', 'Bill 214 Lincoln\'s measured work from the schedule of values, with retainage', 2, 'C32', ['Lincoln'])},
    {'id': 'Y-40', 'day': D3, 'time': '10:30', 'kind': 'interrupt', 'tags': ['cycle', 'interrupt'],
     'payload': {'uid': 'u_billing', 'after_min': 15, 'from': 'David Klein', 'via': 'mail',
                 'mail': {'from': 'David Klein <david.klein@example.com>', 'to': ['Billing <billing@smartdesign.nyc>'], 'subject': 'INV-2026-040 and retainage',
                          'text': 'Hi, could you resend INV-2026-040 and tell us how much retainage you are holding so far on 121 State? Our lender asks. David'},
                 'text': 'A mail just came in from David Klein (121 State): he wants INV-2026-040 again and the retainage held so far, for their lender.'},
     'expect': X('u_billing', 'Answer David Klein (INV-2026-040, the retainage held) within 2 hours', 0, 'C63', ['retainage'])},
    {'id': 'Y-41', 'day': D3, 'time': '16:30', 'kind': 'seed', 'tags': ['cycle', 'reports'], 'payload': {},
     'expect': X('u_owner', 'The owner\'s numbers for the meeting', 0, 'C50')},
    {'id': 'Y-42', 'day': D3, 'time': '16:30', 'kind': 'seed', 'tags': ['cycle', 'reports'], 'payload': {}, 'expect': X('u_alan', 'The PM\'s numbers for the meeting', 0, 'C51')},
    {'id': 'Y-43', 'day': D3, 'time': '16:30', 'kind': 'seed', 'tags': ['cycle', 'reports'], 'payload': {}, 'expect': X('u_chen', 'The coordinator\'s numbers', 0, 'C52')},
    {'id': 'Y-44', 'day': D3, 'time': '16:30', 'kind': 'seed', 'tags': ['cycle', 'reports'], 'payload': {}, 'expect': X('u_billing', 'Billing\'s numbers', 0, 'C53')},
]
STEPS.append(['C34', 'u_billing', 'The pendants bought for the Ashbys billed back', D3, 3, 612.40])

# Coverage (BACKLOG §1.16; Alan, 10-25): each role's main module, the pages and sub-pages from the app's own menu
# (MN_JOBS, MN_BUY, MN_SALES, BILL_TABS in src/app.js) until docs/modules/projects_census.md lands. A page is
# [key, label]: key "view" or "view:tab" as the harness logs it (page_tools.js S.where).
COVERAGE = {
    'floor': 0.6,
    'u_owner': {'module': 'Sales, Approvals and Reports', 'pages': [
        ['home', 'Today'], ['mapprove', 'Approvals'], ['ovsales', 'Sales'], ['billing:estimates', 'Estimates'], ['hbcontacts', 'People'],
        ['hbcompanies', 'Companies'], ['salesnum', 'Numbers'], ['ovmoney', 'Accounting'], ['bank', 'Banking'], ['reports', 'Reports'], ['dashboard', 'Dashboard']]},
    'u_alan': {'module': 'Projects', 'pages': [
        ['ovjobs', 'Projects'], ['dash', 'Overview'], ['proj', 'Project Settings'], ['sched', 'Schedule'], ['tasks', 'Tasks'], ['dec', 'Decisions'],
        ['subm', 'Submittals'], ['insp', 'Permits'], ['field', 'Field'], ['photos', 'Photos'], ['recv', 'Deliveries'], ['mat', 'Materials'],
        ['costs', 'Costs'], ['billing:co', 'Change Orders'], ['billing:estimates', 'Estimates'], ['billing', 'Billing'], ['files', 'Documents'],
        ['plans', 'Drawings'], ['inbox', 'Mail']],
        'per_job': {'jobs': ['p121', '{job}'], 'pages': ['sched', 'costs', 'billing:co', 'dec', 'subm']}},
    'u_chen': {'module': 'Purchasing', 'pages': [
        ['ovbuy', 'Purchasing'], ['sel', 'Selections'], ['req', 'Requests'], ['proc', 'Buy Board'], ['rfq', 'RFQs'], ['po', 'Purchase Orders'],
        ['recv', 'Deliveries'], ['route', 'Route'], ['inv', 'Inventory'], ['vendors', 'Vendors']]},
    'u_billing': {'module': 'Billing', 'pages': [
        ['billing:billable', 'Billable Now'], ['billing:progress', 'Progress Billing'], ['billing:estimates', 'Estimates'], ['billing:co', 'Change Orders'],
        ['billing:invoices', 'Invoices'], ['billing:sov', 'Schedule of Values'], ['billing:payments', 'Payments'], ['billing:funds', 'Client Funds'], ['bank', 'Banking']]},
}


def main():
    book = {'title': 'Pilot 3: the business cycle (sim/cycle_book.py; invented data only)', 'days': [D1, D2, D3], 'roles': ROLES,
            'scripted': {'u_angel': 'receiving against the PO (short, damaged), hours on cost codes, the daily log and the measured %',
                         'u_alberto': 'hours on cost codes', 'u_alex': 'hours on cost codes',
                         'u_controller': 'statement import, the app\'s own proposed matches confirmed, the payroll build',
                         'u_sarah': 'not in this pilot', 'u_klein': 'the Kleins answer by world rules'},
            'job': JOB, 'takeoff': [dict(zip(('item', 'qty', 'unit', 'price', 'cost', 'kind', 'key'), t)) for t in TAKEOFF],
            'radiator': dict(zip(('item', 'qty', 'unit', 'price', 'cost', 'kind', 'key'), RADIATOR)),
            'schedule': {k: [dict(zip(('item', 'qty', 'unit'), x)) for x in v] for k, v in SCHEDULE.items()}, 'in_stock': IN_STOCK, 'last_price': LAST_PRICE,
            'item_rx': ITEM_RX, 'lots': LOTS, 'parties': PARTIES, 'objectives': OBJECTIVES, 'standard_for': STANDARD_FOR, 'questions': QUESTIONS,
            'steps': [dict(zip(('id', 'owner', 'what', 'day', 'by', 'money'), s)) for s in STEPS], 'plants': PLANTS, 'coverage': COVERAGE,
            'events': [dict(e, tags=['pilot3'] + e.get('tags', [])) for e in EVENTS]}
    json.dump(book, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print(f"wrote {OUT}: {len(book['events'])} events, {len(book['steps'])} steps, {len(PLANTS)} planted leaks, {len(PARTIES)} parties, "
          f"estimate takeoff {len(TAKEOFF)} lines ${sum(t[1] * t[3] for t in TAKEOFF):,.0f}")
    return book


if __name__ == '__main__':
    main()
