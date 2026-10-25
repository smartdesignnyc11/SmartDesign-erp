"""sim/make_book.py: build sim/world_book.json from tests/month_book.json (run it again when the month's book changes).

The scripted month's events are converted for a world where people act for themselves:
- mail, calendar, Drive and bank events stay as they are (the world delivers them through the same paths);
- field events (a foreman's raise, request or % update) and client events (a hold, a choice, a question)
  become "situations": what that person runs into, told to them through `act <uid> news`. Whether it reaches
  the app is now up to the person, which is the point;
- "due" events that put a fact in place (a task left unowned, a hand-typed bank line, a journal draft) become
  "facts" the world applies through the app's own functions, as the scripted month does;
- every event keeps its expectation (who, what, by, see, check, money, days), so the referee scores the same
  things the scripted month scores.
It also writes the parties (clients, vendors, subs, the architect, the inspector, the bank) with their reply
rules, and the held-out generator's settings. Invented data only.
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), 'tests', 'month_book.json')
OUT = os.path.join(HERE, 'world_book.json')

# kind, chance of answering, delay in working days [min, max], chance an order slips
KINDS = {
    'client': ['Sarah Klein', 'David Klein', 'Elena Rivera', 'Cambri Jessop', 'Jaleena Jessop', 'Ines Ward', 'Mark Hyland', 'Sofia Adler', 'Marcus Bell', 'Lenox Coffee'],
    'sub': ['Alberto M Plumbing', 'Satish Electric', 'Tomas Restoration', 'Carlos Millwork', 'Clear Cut Glass', 'Window Works'],
    'consultant': ['Priya Natarajan', 'Metro Expediting'],
    'agency': ['DOB NOW', 'LPC Staff'],
    'noreply': ['Answering service', 'Builder Webinars', 'Stoop and Cornice', 'ToolPro', 'Payroll Service', 'American Express', 'Meeting notes', 'Home Depot'],
    'broker': ['Kings Insurance', 'Liberty Brokerage', 'Harbor Insurance'],
}
EXTRA = {   # invented parties the scripted month never wrote to, so the world can play them
    'architect': {'name': 'Ruth Okafor, RA', 'addr': 'Ruth Okafor, RA <ruth@okafor-architects.example>', 'kind': 'architect', 'reply_p': 0.85, 'delay': [1, 3],
                  'voice': 'Architect of record on 121 State and 45 Cranberry. Precise, slow to commit, answers submittals in writing.'},
    'inspector': {'name': 'DOB Inspections', 'addr': 'DOB Inspections <inspections@dob.example>', 'kind': 'inspector', 'reply_p': 0.7, 'delay': [1, 3],
                  'voice': 'A city building inspector. Short, formal, never discusses anything but the inspection.'},
    'bank': {'name': 'The Bank (statements)', 'addr': 'Statements <statements@bank.example>', 'kind': 'bank', 'reply_p': 0.0, 'delay': [0, 0],
             'voice': 'The bank. Sends statements; never answers mail.'},
}
VOICE = {'client': 'A homeowner client. Busy, polite, wants to know cost and days before saying yes; sometimes slow to decide.',
         'vendor': 'A supply house. Answers quotes and order questions; dates slip now and then.',
         'sub': 'A trade subcontractor. Practical, terse, often on a job site; confirms by phone more than by mail.',
         'consultant': 'A consultant (engineer or expediter). Answers in a day or two, in writing.',
         'agency': 'A city agency mailbox. Never answers mail.', 'noreply': 'A no-reply sender.', 'broker': 'An insurance broker. Sends certificates when asked.'}
RULES = {'client': (0.85, [0, 2], 0), 'vendor': (0.8, [0, 2], 0.25), 'sub': (0.75, [0, 1], 0.2), 'consultant': (0.8, [1, 2], 0),
         'agency': (0.0, [0, 0], 0), 'noreply': (0.0, [0, 0], 0), 'broker': (0.9, [0, 1], 0)}


def kind_of(name):
    for k, L in KINDS.items():
        if any(x.lower() in name.lower() for x in L): return k
    return 'vendor'


def key_of(name):
    return re.sub(r'\W+', '_', name.lower()).strip('_')[:28]


def situation(e):
    p, x = e['payload'], e['expect']
    see = (x.get('see') or [''])[0]
    if e['kind'] == 'field':
        if p['do'] == 'raise':
            return f"On site: {p['title']}. {p.get('note', '')} This needs the office ({p.get('type', 'question')}).".strip()
        if p['do'] == 'request':
            return f"You need {p.get('qty', '')} {p.get('unit', '')} {p['what']} by {p.get('neededBy', 'soon')} for the work ({p.get('taskId', '')}). Nobody has ordered it yet."
        if p['do'] == 'pct':
            return f"Work progress: {p.get('note', p.get('taskId', ''))}. That task ({p.get('taskId')}) is now {p['pct']}% done."
    if e['kind'] == 'client':
        if p['do'] == 'hold':
            return f"You are not ready to decide on {see or p['decision']} (decision {p['decision']}) until {p['until']}. If the firm asks before then, say you need more time."
        if p['do'] == 'choose':
            m = f" (you want {p['match'].replace('|', ' / ')})" if p.get('match') else ''
            return f"You have made up your mind on {see or p['decision']} (decision {p['decision']}): option {int(p.get('option') or 0) + 1}{m}. Make the choice in your portal."
        if p['do'] == 'chat':
            return f"You want to ask the firm, in your portal's chat: \"{p['text']}\""
        if p['do'] == 'coAsk':
            return f"You have a question about {p.get('number', 'the change order')}; ask it on the portal: \"{p['text']}\""
    return x.get('what', '')


def main():
    b = json.load(open(SRC, encoding='utf-8'))
    parties = dict(EXTRA)
    for e in b['events']:
        if e['kind'] != 'mail': continue
        p = e['payload']
        for a in [p['from']] + p['to'] + p.get('cc', []):
            if 'smartdesign.nyc' in a: continue
            name = a.split('<')[0].strip()
            k = key_of(name)
            if k in parties: continue
            kd = kind_of(name)
            rp, delay, late = RULES[kd]
            parties[k] = {'name': name, 'addr': a, 'kind': kd if kd in ('client', 'sub', 'vendor', 'consultant') else kd, 'reply_p': rp, 'delay': delay, 'late_p': late,
                          'voice': VOICE[kd]}
    for k, (name, addr) in {'harbor': ('Harbor Insurance Brokers', 'Harbor Insurance Brokers <certs@harborins.example>'),
                            'marcus_bell': ('Marcus Bell', 'Marcus Bell <marcus.bell@example.com>'),
                            'lenox': ('Lenox Coffee Co.', 'Lenox Coffee Co. <manager@lenoxcoffee.example>'),
                            'home_depot': ('Home Depot Pro', 'Home Depot Pro <noreply@homedepot.example>')}.items():
        if k not in parties:
            kd = kind_of(name); rp, delay, late = RULES[kd]
            parties[k] = {'name': name, 'addr': addr, 'kind': kd, 'reply_p': rp, 'delay': delay, 'late_p': late, 'voice': VOICE[kd]}
    # the Kleins are played by an agent: their mail goes to u_klein's mailbox, not to these rules
    for k in ('sarah_klein', 'david_klein'):
        if k in parties: parties[k]['agent'] = 'u_klein'
    events = []
    for e in b['events']:
        k, p = e['kind'], e.get('payload') or {}
        e2 = {kk: e[kk] for kk in ('id', 'day', 'time', 'kind', 'actor', 'payload', 'expect', 'tags') if kk in e}
        if k in ('field', 'client'):
            uid = e['actor']
            day = e['day']
            if k == 'client' and p.get('on') and p['on'] > day: day = p['on']
            e2.update({'kind': 'situation', 'day': day, 'payload': {'uid': uid, 'text': situation(e)}, 'orig': e})
            if k == 'client' and p.get('do') == 'hold':
                events.append(e2)
                e2 = {'id': e['id'] + 'r', 'day': p['until'], 'time': '08:00', 'kind': 'situation', 'actor': uid,
                      'payload': {'uid': uid, 'text': f"You are ready now to decide on {(e['expect'].get('see') or [p['decision']])[0]} (decision {p['decision']}). Choose in your portal."},
                      'tags': ['the hold ends']}
        elif k == 'due' and (p.get('create') or p.get('typed') or p.get('journal')):
            e2.update({'kind': 'fact', 'actor_uid': 'u_owner' if p.get('create') else 'u_chen' if p.get('typed') else 'u_controller', 'orig': e})
        events.append(e2)
    out = {'title': 'The agent month: the outside world (converted from tests/month_book.json; invented data only)',
           'source': 'tests/month_book.json', 'days': b['days'],
           'accounts': {'ac1': 'Chase Business Checking', 'ac2': 'Amex 1009', 'ac3': 'Square card'},
           'heldout': {'per_day': [1, 2, 2, 3], 'kinds': ['late', 'partial', 'price', 'change', 'inspection', 'mismatch', 'transcript', 'card']},
           'parties': parties, 'events': events}
    add_pilot2(out)
    json.dump(out, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    from collections import Counter
    print(f"wrote {OUT}: {len(out['events'])} events {dict(Counter(e['kind'] for e in out['events']))}, {len(out['parties'])} parties")


# ---------------------------------------------------------------------------------------------------------------
# Pilot 2 (Alan, 2026-10-25): the same three days, widened to the whole firm. Every event is tagged 'pilot2', so the
# referee reports "Pilot 1 events" (the ones above, unchanged) and "all events" side by side. Invented data only.
#
# Chains. An event with a `gate` (a check, sim/checks_p2.js or month_runtime) waits until the gate passes on the world
# page: it is then dated that slot (plus `delay` working days), and what the gate found (a number, a total, a vendor)
# fills the {placeholders} in its text and its expectation. `after` waits for another gated event and inherits what
# it found; `mint` makes a number the outside party writes (an invoice number). A gated event that never fires is not
# scored: the step before it is the one that was missed. Placeholders: "{x}" alone keeps the value's type, "{x$}" is
# money ($1,234.50), {today} is the day it fired.
D1, D2, D3 = '2026-09-03', '2026-09-04', '2026-09-08'
OKORO = 'Nadia Okoro <nadia.okoro@example.com>'
PILOT2_PARTIES = {
    'nadia_okoro': {'name': 'Nadia Okoro', 'addr': OKORO, 'kind': 'client', 'reply_p': 1.0, 'delay': [0, 0], 'late_p': 0, 'no_bank': True,
                    'voice': 'A new prospect: bought a brownstone at 88 Garfield Place, Park Slope. Organised, quick to answer, '
                             'wants a clear price and a start date. Pays by bank transfer the day after an invoice.'},
}
PILOT2_CONFIG = {'po_rx': r'GWB|gypsum|drywall|sheetrock|cement board',
                 'about': 'Pilot 2 events: the prospect to progress-invoice chain, a CO, a PO received short and its bill, '
                          'clock in and out, payroll, bank lines, the portal, task hand-offs and the Monday meeting in Meeting Mode.'}
X = lambda who, what, by, check, see=None, money=0, days=0: {'who': who, 'what': what, 'by': by, 'see': see or [], 'check': check, 'money': money, 'days': days}
OK_RX = 'Okoro'
SENT = ['sent', 'viewed', 'partial', 'paid', 'overdue']
PILOT2 = [
    # ---- a prospect, from the first mail to a progress invoice (owner, billing, designer, controller)
    {'id': 'P2-01', 'day': D1, 'time': '08:05', 'kind': 'mail', 'tags': ['prospect'],
     'payload': {'from': OKORO, 'to': ['Alan Mishali <alan@smartdesign.nyc>'], 'cc': [], 'thread': 'p2_okoro', 'att': [],
                 'subject': 'Renovating 88 Garfield Place (Park Slope)',
                 'text': 'Hello, we closed on a brownstone at 88 Garfield Place in Park Slope and want a new kitchen, a powder room and the '
                         'parlor floors redone. Our budget is around $210,000. Could someone walk it with us this week? '
                         'Nadia Okoro, (917) 555-0143'},
     'expect': X('u_owner', 'Put Nadia Okoro (88 Garfield Place) on file as a lead', 1, {'t': 'lead', 'name': OK_RX}, ['Okoro'])},
    {'id': 'P2-02', 'day': D1, 'time': '08:05', 'kind': 'seed', 'tags': ['prospect'], 'payload': {},
     'expect': X('u_owner', 'Answer Nadia Okoro the same day (the first reply within 2 hours, the Standard)', 0, {'t': 'outreach', 'to': 'okoro'}, ['Okoro'])},
    {'id': 'P2-03', 'day': D1, 'time': '12:30', 'kind': 'situation', 'tags': ['prospect'], 'gate': {'t': 'lead', 'name': OK_RX},
     'payload': {'uid': 'u_owner', 'text': 'You just walked 88 Garfield Place with Nadia Okoro. She wants the firm: a new kitchen, a powder room '
                                           'and the parlor floors, about $210,000, and asked for the estimate by Tuesday. Make her a client so the estimate can start.'},
     'expect': X('u_owner', 'Make Nadia Okoro a client (the lead won)', 1, {'t': 'leadWon', 'rx': OK_RX}, ['Okoro'])},
    {'id': 'P2-04', 'day': D1, 'time': '12:30', 'kind': 'seed', 'tags': ['prospect'], 'gate': {'t': 'leadWon', 'rx': OK_RX}, 'payload': {},
     'expect': X('u_owner', 'Send Nadia Okoro the estimate by Tuesday (kitchen, powder room, parlor floors)', 2,
                 {'t': 'estFor', 'rx': OK_RX, 'status': ['sent', 'approved', 'converted'], 'min': 1000}, ['Okoro'])},
    {'id': 'P2-05', 'day': D1, 'time': '07:00', 'kind': 'mail', 'tags': ['prospect', 'contract'],
     'gate': {'t': 'estFor', 'rx': OK_RX, 'status': ['sent', 'approved', 'converted'], 'min': 1000},
     'payload': {'from': OKORO, 'to': ['Alan Mishali <alan@smartdesign.nyc>'], 'cc': [], 'thread': 'p2_okoro', 'subject': 'Re: estimate {number}',
                 'text': 'We read {number} ({total$}) and we accept it as written. The signed copy is attached. Please send the deposit invoice '
                         'and tell us the start date. Nadia',
                 'att': [{'filename': 'Signed {number}.pdf', 'text': 'ACCEPTANCE\n{number}\nAccepted as written, {total$}.\nSigned: Nadia Okoro, {today}'}]},
     'expect': X('u_owner', 'Record the Okoros\' acceptance: {number} becomes the contract', 1,
                 {'t': 'estFor', 'rx': OK_RX, 'status': ['approved', 'converted']}, ['{number}'])},
    {'id': 'P2-06', 'day': D1, 'time': '07:00', 'kind': 'seed', 'tags': ['prospect', 'deposit'], 'gate': {'t': 'estFor', 'rx': OK_RX, 'status': ['approved', 'converted']},
     'payload': {},
     'expect': X('u_billing', 'Send the Okoro deposit invoice on {number} within 2 business days of signing', 2,
                 {'t': 'depositFor', 'rx': OK_RX, 'status': SENT}, ['Okoro'], money='{ten}')},
    {'id': 'P2-07', 'day': D1, 'time': '07:00', 'kind': 'situation', 'tags': ['prospect', 'progress'], 'gate': {'t': 'estFor', 'rx': OK_RX, 'status': ['approved', 'converted']},
     'payload': {'uid': 'u_sarah', 'text': 'You measured 88 Garfield Place for the Okoros and drew the existing conditions: the first design milestone '
                                           '(measure and existing conditions) is done. Billing bills each milestone.'},
     'expect': X('u_billing', 'Bill the Okoros\' measure-and-existing-conditions milestone on a progress invoice', 2,
                 {'t': 'progressFor', 'rx': OK_RX, 'status': SENT}, ['Okoro'])},
    {'id': 'P2-08', 'day': D1, 'time': '07:40', 'kind': 'bank', 'tags': ['prospect', 'payment'], 'gate': {'t': 'depositFor', 'rx': OK_RX, 'status': SENT}, 'delay': 1,
     'payload': {'acct': 'ac1', 'date': '{today}', 'desc': 'ONLINE TRANSFER FROM OKORO N', 'amt': '{total}', 'ref': 'AC1-{today}-OKORO'},
     'expect': X('u_billing', 'Record the Okoros\' deposit ({total$}) against {number} when it lands', 1,
                 {'t': 'paymentFor', 'rx': OK_RX, 'amount': '{total}'}, ['OKORO'], money='{total}')},
    {'id': 'P2-09', 'day': D1, 'time': '07:40', 'kind': 'seed', 'tags': ['prospect', 'bank'], 'after': 'P2-08', 'payload': {},
     'expect': X('u_controller', 'Match the Okoro deposit on Chase to its invoice', 2, {'t': 'txn', 'desc': 'OKORO', 'resolved': True}, ['OKORO'])},
    # ---- change orders: written and sent; the approved one billed
    {'id': 'P2-10', 'day': D1, 'time': '10:30', 'kind': 'seed', 'tags': ['change order'], 'payload': {},
     'expect': X('u_alan', 'Send the Kleins the pantry GFI change order, priced, with its days (within 48 hours)', 2,
                 {'t': 'coFor', 'project': 'p121', 'rx': 'GFI|pantry|outlet', 'status': ['sent', 'approved']}, ['GFI'], money=650)},
    {'id': 'P2-11', 'day': D1, 'time': '10:30', 'kind': 'seed', 'tags': ['change order', 'billing'], 'gate': {'t': 'coFor', 'project': 'p121', 'rx': 'GFI|pantry|outlet', 'status': ['approved']},
     'payload': {},
     'expect': X('u_billing', 'Bill the approved {number} (pantry GFI) on the next invoice', 2, {'t': 'coInvoiced', 'number': '{number}'}, ['{number}'], money='{total}')},
    {'id': 'P2-12', 'day': D3, 'time': '10:30', 'kind': 'seed', 'tags': ['change order'], 'payload': {},
     'expect': X('u_alan', 'Send the stair landing guard change order (42 inches, code), priced', 2,
                 {'t': 'coFor', 'project': 'p121', 'rx': 'guard|42', 'status': ['sent', 'approved']}, ['guard'])},
    # ---- a PO from the estimate line, received one line short, the vendor's bill matched and the short line held
    {'id': 'P2-20', 'day': D1, 'time': '10:30', 'kind': 'seed', 'tags': ['PO'], 'payload': {},
     'expect': X('u_chen', 'Order the GWB and cement board from the estimate line: a PO with a vendor and a price', 0,
                 {'t': 'poFor', 'project': 'p121', 'rx': PILOT2_CONFIG['po_rx'], 'linked': True}, ['GWB'])},
    {'id': 'P2-21', 'day': D1, 'time': '10:30', 'kind': 'seed', 'tags': ['PO'], 'gate': {'t': 'poFor', 'project': 'p121', 'rx': PILOT2_CONFIG['po_rx']}, 'payload': {},
     'expect': X('u_chen', 'Send {number} to {vendor}', 0, {'t': 'poSent', 'number': '{number}'}, ['{number}'])},
    {'id': 'P2-22', 'day': D1, 'time': '08:50', 'kind': 'situation', 'tags': ['PO', 'receiving'], 'after': 'P2-21', 'gate': {'t': 'poSent', 'number': '{number}'}, 'delay': 1,
     'payload': {'uid': 'u_angel', 'text': '{vendor} delivered {number} to 121 State this morning. The packing slip shows everything except {short_n} of the '
                                           '{short_item} (backordered, balance next week). The slip is in your hand.'},
     'expect': X('u_angel', 'Receive {number} as a partial delivery ({short_n} short on {short_item}) and photograph the slip', 0,
                 {'t': 'poStatus', 'number': '{number}', 'status': ['partial']}, ['{number}'], days=1)},
    {'id': 'P2-23', 'day': D1, 'time': '13:40', 'kind': 'mail', 'tags': ['PO', 'bill'], 'after': 'P2-22',
     'gate': {'t': 'poStatus', 'number': '{number}', 'status': ['partial', 'received', 'closed', 'billed']}, 'mint': {'inv': 'vendor_invoice'},
     'payload': {'from': '{vendor_addr}', 'to': ['Chen Biron <chen@smartdesign.nyc>'], 'cc': [], 'thread': 'p2_inv', 'subject': 'Invoice {inv} for {number}',
                 'text': 'Invoice {inv} for {number} is attached: {total$} for the order as written, net 30.',
                 'att': [{'filename': 'Invoice {inv}.pdf', 'text': 'INVOICE {inv}\n{vendor}\nPO: {number}\nAll lines as ordered, including {short_n} {short_item}\nTOTAL {total$}\nNet 30'}]},
     'expect': X('u_chen', 'Enter {inv} against {number}', 1, {'t': 'bill', 'number': '{inv}', 'poNumber': '{number}'}, ['{inv}'], money='{total}')},
    {'id': 'P2-24', 'day': D1, 'time': '13:40', 'kind': 'seed', 'tags': ['PO', 'three-way match'], 'after': 'P2-23', 'payload': {},
     'expect': X('u_chen', 'Hold the {short_n} {short_item} not delivered on {inv} (three-way match: pay what came)', 1,
                 {'t': 'billShortAny', 'number': '{inv}'}, ['{inv}'], money='{short_value}')},
    # ---- clock in and out (foreman every day, crew and driver on day 3), payroll to approval
    {'id': 'P2-30', 'day': D1, 'time': '07:00', 'kind': 'seed', 'tags': ['time'], 'payload': {},
     'expect': X('u_angel', 'Clock in and out on 9/3 (the foreman\'s own hours)', 0, {'t': 'clocked', 'uid': 'u_angel', 'day': D1})},
    {'id': 'P2-31', 'day': D2, 'time': '07:00', 'kind': 'seed', 'tags': ['time'], 'payload': {},
     'expect': X('u_angel', 'Clock in and out on 9/4', 0, {'t': 'clocked', 'uid': 'u_angel', 'day': D2})},
    {'id': 'P2-32', 'day': D3, 'time': '07:00', 'kind': 'seed', 'tags': ['time'], 'payload': {},
     'expect': X('u_angel', 'Clock in and out on 9/8', 0, {'t': 'clocked', 'uid': 'u_angel', 'day': D3})},
    {'id': 'P2-33', 'day': D3, 'time': '07:00', 'kind': 'seed', 'tags': ['time'], 'payload': {},
     'expect': X('u_alberto', 'Clock in and out on 9/8 (crew)', 0, {'t': 'clocked', 'uid': 'u_alberto', 'day': D3})},
    {'id': 'P2-34', 'day': D3, 'time': '07:00', 'kind': 'seed', 'tags': ['time'], 'payload': {},
     'expect': X('u_alex', 'Clock in and out on 9/8 (driver)', 0, {'t': 'clocked', 'uid': 'u_alex', 'day': D3})},
    {'id': 'P2-35', 'day': D3, 'time': '10:30', 'kind': 'seed', 'tags': ['payroll'], 'payload': {},
     'expect': X('u_controller', 'Build the 8/31-9/4 payroll from the approved hours', 0, {'t': 'payrollRun', 'from': '2026-08-31', 'to': '2026-09-04'})},
    {'id': 'P2-36', 'day': D3, 'time': '10:30', 'kind': 'seed', 'tags': ['payroll'], 'payload': {},
     'expect': X('u_owner', 'Approve the 8/31-9/4 payroll run (the owner approves payroll)', 1, {'t': 'payrollRun', 'from': '2026-08-31', 'to': '2026-09-04', 'approved': True})},
    # ---- the client asks in the portal
    {'id': 'P2-40', 'day': D2, 'time': '08:20', 'kind': 'portal', 'tags': ['portal'],
     'payload': {'uid': 'u_klein', 'text': 'Quick question: does the pantry outlet change the cabinet install date? We need to know before the weekend.'},
     'expect': X('u_alan', 'Answer the Kleins\' portal question (the pantry outlet and the cabinet date) within 2 hours', 0,
                 {'t': 'clientAnswered', 'project': 'p121', 'rx': 'pantry outlet'}, ['pantry outlet'])},
    # ---- tasks handed off and closed
    {'id': 'P2-50', 'day': D1, 'time': '10:30', 'kind': 'situation', 'tags': ['task'],
     'payload': {'uid': 'u_alan', 'text': 'Carlos Millwork needs the freight elevator at 121 State for the 9/18 millwork delivery, 7 to 10 am. '
                                          'Hand it to Chen as a task: book the elevator with Luis (the super), due Thu 9/10.'},
     'expect': X('u_alan', 'Hand the freight elevator booking to Chen as a task', 0, {'t': 'taskBy', 'rx': 'elevator', 'assignee': 'Chen'}, ['elevator'])},
    {'id': 'P2-51', 'day': D1, 'time': '10:30', 'kind': 'situation', 'tags': ['task'], 'gate': {'t': 'taskBy', 'rx': 'elevator', 'assignee': 'Chen'},
     'payload': {'uid': 'u_chen', 'text': 'Luis, the super at 121 State, confirmed the freight elevator for Fri 9/18, 7 to 10 am.'},
     'expect': X('u_chen', 'Close the elevator task now that Luis confirmed', 1, {'t': 'taskBy', 'rx': 'elevator', 'assignee': 'Chen', 'done': True}, ['elevator'])},
    {'id': 'P2-52', 'day': D3, 'time': '07:00', 'kind': 'situation', 'tags': ['task'],
     'payload': {'uid': 'u_angel', 'text': 'Alberto has to finish the blocking for the garden bath vanity today, before the plumber comes. Give it to him as a task on the app.'},
     'expect': X('u_angel', 'Give Alberto the vanity blocking as a task', 0, {'t': 'taskBy', 'rx': 'blocking', 'assignee': 'Alberto'}, ['blocking'])},
    {'id': 'P2-53', 'day': D3, 'time': '07:00', 'kind': 'situation', 'tags': ['task'], 'gate': {'t': 'taskBy', 'rx': 'blocking', 'assignee': 'Alberto'},
     'payload': {'uid': 'u_alberto', 'text': 'You finished the blocking for the garden bath vanity.'},
     'expect': X('u_alberto', 'Mark the vanity blocking task done', 0, {'t': 'taskBy', 'rx': 'blocking', 'assignee': 'Alberto', 'done': True}, ['blocking'])},
    # ---- the Monday team meeting (Tuesday 9/8, after Labor Day) in Meeting Mode
    {'id': 'P2-60', 'day': D3, 'time': '06:30', 'kind': 'calendar', 'tags': ['meeting'],
     'payload': {'uid': 'u_owner', 'title': 'Team Meeting (Monday\'s, moved for Labor Day)', 'start': f'{D3}T10:00', 'mins': 45, 'where': 'Office',
                 'description': 'Walk the board job by job in Meeting Mode; minutes to everyone.'},
     'expect': X('u_owner', 'Run the Monday team meeting (Tuesday after Labor Day) in Meeting Mode, with minutes', 0,
                 {'t': 'teamMeeting', 'day': D3, 'min': 3}, ['Team Meeting'])},
]


def add_pilot2(book):
    """Put the Pilot 2 events (tagged 'pilot2') and their party into a book, replacing any earlier copy of them."""
    book['events'] = [e for e in book['events'] if 'pilot2' not in (e.get('tags') or [])] + [dict(e, tags=['pilot2'] + e.get('tags', [])) for e in PILOT2]
    book['parties'].update(PILOT2_PARTIES)
    book['pilot2'] = PILOT2_CONFIG
    return book


def pilot2_only():
    """Add the Pilot 2 events to the existing world_book.json without rebuilding Pilot 1's events, so both pilots score
    the same Pilot 1 events (tests/month_book.json moved on after Pilot 1's book was made)."""
    book = add_pilot2(json.load(open(OUT, encoding='utf-8')))
    json.dump(book, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    n = sum(1 for e in book['events'] if 'pilot2' in e['tags'])
    print(f"wrote {OUT}: {len(book['events'])} events, {n} of them Pilot 2's")


if __name__ == '__main__':
    import sys
    pilot2_only() if '--pilot2-only' in sys.argv else main()
