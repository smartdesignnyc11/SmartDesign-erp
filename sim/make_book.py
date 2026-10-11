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
    json.dump(out, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    from collections import Counter
    print(f"wrote {OUT}: {len(events)} events {dict(Counter(e['kind'] for e in events))}, {len(parties)} parties")


if __name__ == '__main__':
    main()
