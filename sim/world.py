"""sim/world.py: the outside world of the agent month (BACKLOG §1.17 item 4). Invented data only.

The world plays everyone outside the firm: clients, vendors, subs, the architect, the inspector and the bank.
It brings three kinds of things into the company, always through the paths a real party would use:
- scripted events from sim/world_book.json (converted from tests/month_book.json by sim/make_book.py): mail,
  calendar invites, Drive files, bank and card lines (as a statement the bank mails the controller, which the
  controller imports through Banking > Import Statement), "facts" (a hand-typed line, a journal draft) and
  "situations": what a person runs into in the physical world (a no-show on site, a notched joist, the client
  making up their mind). A situation reaches only that person, through `act <uid> news`; they act on it
  through the app, mail or a call;
- held-out events, generated each morning from a seeded random generator and the company's live records
  (open POs, vendors, jobs), so a month cannot be memorised: late deliveries, partial shipments, a price
  change, a client change request, a failed inspection, a vendor invoice that does not match its PO, a meeting
  transcript dropped into Drive, and card lines;
- replies to what the staff send out: a vendor answers an RFQ, confirms or slips an order, a client approves or
  promises a payment (and the deposit then shows up at the bank). Simple rules with delays and some
  randomness; some parties never answer.

THE WORLD-AGENT HOOK. With `simctl world-agent on`, every reply the rules schedule is also written to
sim/runs/<run>/world/pending/<id>.json ({party, persona, their_message, template_reply, due}). The main session
may run an LLM as that party and write the free-text reply to sim/runs/<run>/world/answers/<id>.txt before
the due slot; the world sends that text instead of the template. Nothing else changes: delays, who never
answers and the money that follows stay with the rules, so the referee's numbers do not depend on the LLM.

THE VOICER (10-26). With `simctl world-voice on` the world does that itself: when a reply falls due and no answer is
written, sim/voicer.py has the live model write it in the party's voice through /api/ai (SIM_AI_TOKEN_FILE), with a
style seeded per run and reply (plain, terse, a question back, another layout, late by a slot, or in two parts), and
checks that every fact of the template (prices, dates, quantities, numbers) is kept and none is invented. On any
failure the template goes out and world/voice.jsonl (and "World voice" in ledger.md) says so.
"""
import asyncio, json, os, random, re, hashlib
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
BOOK = os.path.join(HERE, 'world_book.json')
CYCLE = os.path.join(HERE, 'cycle_book.json')   # Pilot 3's required-work book (sim/cycle_book.py), on with `simctl cycle on`
SLOT_ORDER = ['morning', 'work1', 'work2', 'eod']
SI = lambda s: SLOT_ORDER.index('work2' if s == 'work' else s)   # the lean plan's one 'work' slot covers both work slots
STAFF = {
    'u_owner': ('Alan Mishali', 'alan@smartdesign.nyc'), 'u_alan': ('Alan', 'alan.pm@smartdesign.nyc'),
    'u_chen': ('Chen Biron', 'chen@smartdesign.nyc'), 'u_angel': ('Angel', 'angel@smartdesign.nyc'),
    'u_sarah': ('Sarah Davis', 'sarah@smartdesign.nyc'), 'u_billing': ('Billing', 'billing@smartdesign.nyc'),
    'u_controller': ('Controller', 'controller@smartdesign.nyc'), 'u_alberto': ('Alberto', 'alberto@smartdesign.nyc'),
    'u_alex': ('Alex', 'alex@smartdesign.nyc'),
}
ROLE_ALIAS = {'pm': 'u_alan', 'the pm': 'u_alan', 'alan (pm)': 'u_alan', 'alan pm': 'u_alan', 'project manager': 'u_alan', 'owner': 'u_owner', 'the owner': 'u_owner',
              'alan (owner)': 'u_owner', 'coordinator': 'u_chen', 'procurement': 'u_chen', 'foreman': 'u_angel', 'designer': 'u_sarah', 'accounts': 'u_billing',
              'the controller': 'u_controller', 'driver': 'u_alex', 'crew': 'u_alberto'}
# people outside the firm who are played by an agent (their mail goes to the agent's mailbox, not to the rules)
AGENTS = {'u_klein': ['Sarah Klein <sarah.klein@example.com>', 'David Klein <david.klein@example.com>']}
TZ = '-04:00'


def slot_of(hm):
    return 'morning' if hm < '10:00' else 'work1' if hm < '13:30' else 'work2' if hm < '16:30' else 'eod'


def email_of(a):
    m = re.search(r'<([^>]+)>', a or '')
    return (m.group(1) if m else (a or '')).strip().lower()


def money(s):
    m = re.findall(r'\$\s?([\d,]+(?:\.\d{2})?)', s or '')
    return float(m[0].replace(',', '')) if m else 0.0


class World:
    def __init__(self, sim):
        self.sim = sim
        self.book = json.load(open(BOOK, encoding='utf-8'))
        self.days = self.book['days']
        self.parties = self.book['parties']
        for k, v in (sim.state.get('world', {}).get('party_patch') or {}).items(): self.parties[k] = v
        self.staff_addr = {u: f'{n} <{e}>' for u, (n, e) in STAFF.items()}
        self.agent_addr = {u: L[0] for u, L in AGENTS.items()}
        self.cycle = json.load(open(CYCLE, encoding='utf-8')) if os.path.exists(CYCLE) else None
        if self.cycle_on: self.enable_cycle()

    # ---- Pilot 3: the business cycle (sim/cycle_book.json), its parties, and the roles the world plays for it
    @property
    def cycle_on(self):
        return bool(self.cycle and self.sim.state.get('world', {}).get('cycle'))

    def enable_cycle(self):
        self.sim.state.setdefault('world', {})['cycle'] = True
        for k, v in self.cycle['parties'].items(): self.parties[k] = dict(self.parties.get(k, {}), **v)
        for k, v in (self.sim.state['world'].get('party_patch') or {}).items(): self.parties[k] = v

    def scripted(self, uid, do=None):
        """a role the world plays in this run (Pilot 3: everyone outside the cycle book's four roles). A role that plays
        after all (`cycle on --play u_controller`) does its own steps; `uid:do` plays one kind of step only (the screen
        walk: 'u_angel:receive', the coordinator receives the trucks herself, while the foreman's field day stays scripted)."""
        play = self.sim.state['world'].get('cycle_play') or []
        return (self.cycle_on and uid in (self.cycle.get('scripted') or {}) and uid not in play
                and not (do and f'{uid}:{do}' in play))

    @property
    def bank_feed(self):
        """the bank's own feed (Plaid on the hosted app): each statement line lands in Banking as it clears, unmatched,
        for the people who match it; on with `cycle on --feed` (the screen walk, where the controller plays)"""
        return bool(self.sim.state['world'].get('bank_feed'))

    def book_list(self):
        return self.book['events'] + (self.cycle['events'] if self.cycle_on else [])

    @property
    def st(self):
        w = self.sim.state['world']
        for k, v in (('fired', {}), ('pending', []), ('heldout', {}), ('extra', []), ('bank', []), ('done', {}), ('replied', {}), ('n', 0)):
            w.setdefault(k, v)
        return w

    def rng(self, *salt):
        return random.Random(int(hashlib.sha1(f"{self.sim.state['seed']}:{':'.join(map(str, salt))}".encode()).hexdigest()[:12], 16))

    def start(self):
        self.st

    def next_day(self, d):
        if d in self.days and self.days.index(d) + 1 < len(self.days): return self.days[self.days.index(d) + 1]
        x = date.fromisoformat(d) + timedelta(days=1)
        while x.weekday() >= 5: x += timedelta(days=1)
        return x.isoformat()

    def wd_add(self, d, n):
        if d in self.days and self.days.index(d) + n < len(self.days): return self.days[max(0, self.days.index(d) + n)]   # the book's calendar (holidays out)
        x = date.fromisoformat(d)
        while n > 0:
            x += timedelta(days=1)
            if x.weekday() < 5: n -= 1
        return x.isoformat()

    # ---- who is who
    def who_is(self, s):
        s0 = (s or '').strip(); e = email_of(s0); low = s0.lower()
        for u, (n, em) in STAFF.items():
            if e == em or low == u or low == n.lower(): return u
        if low in ROLE_ALIAS: return ROLE_ALIAS[low]   # "the PM", "Alan (PM)", "the owner": two people are called Alan
        # a colleague by first or last name alone ("Chen", "Alan"), when only one person carries it
        if low and ' ' not in low and '@' not in low:
            hits = [u for u, (n, em) in STAFF.items() if low in n.lower().split()]
            if len(hits) == 1: return hits[0]
        for u, L in AGENTS.items():
            if e in [email_of(x) for x in L] or low == u or any(low == x.split('<')[0].strip().lower() for x in L) or (low and low in ('the kleins', 'kleins', 'klein')): return u
        return None

    def resolve_party(self, s):
        low = (s or '').strip().lower(); e = email_of(s)
        for k, p in self.parties.items():   # an exact name, key or address first ("Gowanus Building Supply" is not "Gowanus Stone Yard")
            if low == k or low == p['name'].lower() or e == email_of(p['addr']): return k
        for k, p in self.parties.items():
            if len(low) > 3 and low in p['name'].lower(): return k
        return None

    def resolve_addr(self, s):
        u = self.who_is(s)
        if u in STAFF: return self.staff_addr[u]
        if u in AGENTS: return AGENTS[u][0]
        k = self.resolve_party(s)
        if k: return self.parties[k]['addr']
        return s if '@' in (s or '') else None

    # ---- what the referee scores: the book's events and today's held-out ones
    def all_events(self):
        return self.book_events() + [e for d in sorted(self.st['heldout']) for e in self.st['heldout'][d]] + self.st['extra']

    # ---- gated events (Pilot 2 chains, sim/make_book.py): an event with `gate` or `after` exists once it has fired
    def book_events(self):
        G = self.st.setdefault('gated', {})
        return [e if not (e.get('gate') or e.get('after')) else self.materialize(e, G[e['id']]) for e in self.book_list()
                if not (e.get('gate') or e.get('after')) or e['id'] in G]

    @staticmethod
    def fill(x, bind):
        """{name} placeholders from what a gate found: "{x}" alone keeps the value's type, "{x$}" is money."""
        if isinstance(x, dict): return {k: World.fill(v, bind) for k, v in x.items()}
        if isinstance(x, list): return [World.fill(v, bind) for v in x]
        if not isinstance(x, str) or '{' not in x: return x
        m = re.fullmatch(r'\{(\w+)\}', x)
        if m and m.group(1) in bind: return bind[m.group(1)]
        def one(mm):
            k, cur = mm.group(1), mm.group(2)
            if k not in bind: return mm.group(0)
            v = bind[k]
            if cur:
                try: return f'${float(v):,.2f}'
                except Exception: return str(v)
            return str(v)
        return re.sub(r'\{(\w+)(\$?)\}', one, x)

    def materialize(self, e, rec):
        x = self.fill({k: v for k, v in e.items() if k not in ('gate', 'after', 'mint', 'delay')}, rec.get('bind') or {})
        x['day'], x['time'] = rec['day'], rec.get('time') or e.get('time', '07:00')
        ex = x.get('expect')
        if ex and isinstance(ex.get('money'), str):
            try: ex['money'] = float(ex['money'])
            except Exception: ex['money'] = 0.0
        if x['kind'] == 'bank':
            try: x['payload']['amt'] = float(x['payload']['amt'])
            except Exception: pass
        return x

    def mint(self, kind, bind, eid):
        r = self.rng('mint', eid)
        if kind == 'vendor_invoice':
            return f"{re.sub(r'[^A-Z]', '', str(bind.get('vendor', '')).upper())[:3] or 'INV'}-{r.randrange(1000, 9999)}"
        return f'{kind[:3].upper()}-{r.randrange(1000, 9999)}'

    async def open_gates(self, pg, day, slot):
        """Fire every gated event whose gate passes now (in book order, so a chain can move one step per slot only
        when the step before it fired in an earlier slot or earlier in this one)."""
        G, fired = self.st.setdefault('gated', {}), []
        for e in self.book_list():
            if not (e.get('gate') or e.get('after')) or e['id'] in G or e['day'] > day: continue
            if e['day'] == day and SI(slot) < SI(slot_of(e.get('time', '07:00'))): continue
            bind = {}
            if e.get('after'):
                if e['after'] not in G or G[e['after']]['day'] > day: continue
                bind.update(G[e['after']].get('bind') or {})
            ok = True
            if e.get('gate') and e['gate'].get('t') == 'cy':   # a cycle step, checked in Python on the raw records (sim/cycle.py)
                ok, det, b = self.sim.cycle_gate(self.fill(e['gate'], bind))
                bind.update(b or {})
            elif e.get('gate'):
                ok, det, b = await pg.evaluate("([c, ev]) => __MS.gate(c, ev)", [self.fill(e['gate'], bind), {'id': e['id'], 'day': e['day'], 'payload': {}}])
                bind.update(b or {})
            if not ok: continue
            on = self.wd_add(day, e['delay']) if e.get('delay') else day
            bind['today'] = on
            for k, kind in (e.get('mint') or {}).items(): bind[k] = self.mint(kind, bind, e['id'])
            if bind.get('vendor') and 'vendor_addr' not in bind:
                k = self.resolve_party(bind['vendor'])
                bind['vendor_addr'] = self.parties[k]['addr'] if k else f"{bind['vendor']} <ap@{re.sub(r'[^a-z]', '', bind['vendor'].lower())[:20] or 'vendor'}.example>"
            G[e['id']] = {'day': on, 'time': e.get('time') if e.get('delay') else self.sim.clock_str(), 'bind': bind, 'opened': [day, slot]}
            fired.append([e['id'], on])
        return fired

    def po_tracked(self, body, po=''):
        """an order a chain plays itself (Pilot 2's short delivery and its bill; Pilot 3's orders for the cycle job): the
        reply rules leave its truck and its invoice alone"""
        rx = (self.book.get('pilot2') or {}).get('po_rx')
        if rx and re.search(rx, body or '', re.I): return True
        return bool(self.cycle_on and po and po in self.sim.cycle_po_numbers())

    async def post_portal(self, text):
        """The client writes in the portal's chat, on their own phone page (the client's side played by rules)."""
        sim = self.sim
        pg, _ = await sim.fresh('u_klein')
        ok = await pg.evaluate("""async (q) => { view = 'chat'; render(); await new Promise(r => setTimeout(r, 200)); const ta = document.querySelector('#chat-text'), b = document.querySelector('#chat-send');
            if (!ta || !b) return false; ta.value = q; ta.dispatchEvent(new Event('input', { bubbles: true })); b.click(); return true; }""", text)
        await sim.commit('u_klein')
        return 'in the portal chat' if ok else 'no chat box on the portal'

    def open_needles(self):
        day = self.sim.state['day'] or ''
        return {e['id']: e['expect']['see'] for e in self.all_events()
                if e['day'] <= day and e.get('expect') and e['expect'].get('see') and e['id'] not in self.st['done']}

    # ---- a slot of the world
    async def step(self, slot, watchers=None):
        sim = self.sim
        day = sim.state['day']
        pg, _ = await sim.fresh('__world')
        await sim.set_clock()
        out = {'day': day, 'slot': slot, 'events': [], 'replies': [], 'watchers': {}, 'situations': []}
        if slot == 'morning' and day not in self.st['heldout']:
            facts = await pg.evaluate(FACTS_JS)
            self.st['heldout'][day] = self.heldout(day, facts)
        out['gates'] = await self.open_gates(pg, day, slot)
        todays =[e for e in self.all_events() if e['day'] == day and e['id'] not in self.st['fired']]
        now = SI(slot)   # anything of today up to this slot that has not gone out yet (a late-booked delivery too)
        due = [e for e in todays if SI(slot_of(e.get('time', '07:00'))) <= now or e['kind'] == 'bank']
        bank = {}
        for e in due:
            k, p = e['kind'], e.get('payload') or {}
            r = 'kept'
            try:
                if k == 'mail': r = await self.inject_mail(pg, e)
                elif k == 'calendar':
                    s0 = f"{p['start']}:00{TZ}"
                    ev = {'id': f"wde_{e['id']}", 'status': 'confirmed', 'summary': p['title'], 'description': p.get('description', ''), 'location': p.get('where', ''),
                          'htmlLink': '', 'updated': f'{day}T06:00:00Z', 'organizer': {'email': STAFF.get(p['uid'], ('', ''))[1]},
                          'attendees': [{'email': STAFF.get(p['uid'], ('', ''))[1], 'responseStatus': 'accepted'}], 'transparency': 'opaque',
                          'start': {'dateTime': s0}, 'end': {'dateTime': s0}}
                    ev['end'] = {'dateTime': await pg.evaluate("([s, m]) => new Date(new Date(s).getTime() + 60000 * m).toISOString()", [s0, p.get('mins', 60)])}
                    r = 'on the calendar' if await pg.evaluate("([u, e]) => __SIM.mbEvent(u, e)", [p['uid'], ev]) else 'already there'
                elif k == 'drive':
                    f = {'id': f"wdf_{e['id']}", 'name': p['name'], 'mimeType': 'text/plain' if p['name'].endswith('.txt') else 'application/pdf',
                         'modifiedTime': f"{day}T{e.get('time', '09:00')}:00{TZ}", 'size': str(60000 + 300 * len(p.get('text', ''))),
                         'owners': [{'displayName': STAFF.get(p['uid'], ('', ''))[0], 'emailAddress': STAFF.get(p['uid'], ('', ''))[1]}],
                         'webViewLink': '', 'parents': ['dwroot_' + p['uid']], 'text': p.get('text', ''), 'trashed': False}
                    sim.state['drive'].append({'uid': p['uid'], 'file': f}); await pg.evaluate("f => __SIM.driveSync(f)", [{'uid': p['uid'], 'file': f}])
                    sim.state['version'] += 1; sim.page_ver['__world'] = sim.state['version']   # every other page reloads to see the new file
                    r = 'in Drive'
                elif k == 'bank':
                    bank.setdefault(p['acct'], []).append(p); self.st['bank'].append(p); r = 'on the statement'
                elif k == 'portal' or (k == 'situation' and p.get('uid') == 'u_klein' and self.st.get('client_rules')
                                       and ((e.get('orig') or {}).get('payload') or {}).get('do') in ('chat', 'coAsk')):
                    # the client's question goes where the client would ask it: the portal chat (the client by rules has no turns)
                    op = (e.get('orig') or {}).get('payload') or {}
                    r = await self.post_portal(op.get('text') or p['text'] if k == 'situation' else p['text'])
                    pg, _ = await sim.fresh('__world')
                elif k == 'situation' and p.get('uid') == 'u_klein' and self.st.get('client_rules') and 'client change' in (e.get('tags') or []):
                    want = (re.findall(r'You decide you want (.+?)\. Ask', p['text']) or [p['text']])[0]
                    r = await self.post_portal(f'We have decided we would like {want}. What would it cost, and how many days does it add?')
                    pg, _ = await sim.fresh('__world')
                elif k == 'situation':
                    sim.state['news'].setdefault(p['uid'], []).append(f"{day} {e.get('time', '')}: {p['text']}"); r = 'told ' + p['uid']
                    out['situations'].append([p['uid'], p['text'][:80]])
                elif k == 'fact':
                    r = await pg.evaluate("async ([u, ev]) => { __MS.as(u); const r = await __MS.own(ev); return String(r); }", [e['actor_uid'], e['orig']])
                elif k == 'script':   # Pilot 3: a role the world plays does its step through the app (sim/script_p3.js)
                    r = await self.run_script(pg, e)
                elif k == 'interrupt':   # Pilot 3: something that cuts into a person's turn (the server delivers it mid-turn)
                    self.sim.state.setdefault('interrupts', {}).setdefault(p['uid'], []).append(dict(p, id=e['id'], queued=[day, slot]))
                    r = 'queued for ' + p['uid']
                elif k in ('seed', 'due'): r = 'expectation'
            except Exception as ex:
                r = 'ERR ' + str(ex)[:160]
            self.st['fired'][e['id']] = r
            out['events'].append([e['id'], k, str(r)[:80]])
        for acct, L in bank.items():
            if self.scripted('u_controller'): out['events'].append([f'statement {acct}', 'bank', await self.import_statement(pg, acct, day, L)])
            elif self.bank_feed: out['events'].append([f'statement {acct}', 'bank', await self.import_statement(pg, acct, day, L, match=False)])
            else: out['events'].append([f'statement {acct}', 'bank', await self.mail_statement(pg, acct, day, L)])
        out['replies'] = await self.deliver_replies(pg, day, slot)
        if slot in ('work1', 'work', 'work2') and self.st.get('client_rules'):
            out['portal'] = await self.client_portal(day, slot)
            pg, _ = await sim.fresh('__world')
        out['mail'] = await sim.post_office(pg)
        if watchers is None: watchers = slot in ('morning', 'work', 'work2')
        if watchers:
            for u in STAFF:
                try: out['watchers'][u] = await pg.evaluate("async u => { __MS.as(u); const r = await __MS.sync(u); return r ? `${r.mail} mail ${r.events} events ${r.files} files` : 'not connected'; }", u)
                except Exception as ex: out['watchers'][u] = 'ERR ' + str(ex)[:100]
        await sim.commit('__world')
        sim.log({'uid': '__world', 'cmd': 'world', 'args': [slot], 'result': out})
        sim.save_state()
        return out

    async def inject_mail(self, pg, e, extra_to_agent=True):
        p, day, hm = e['payload'], e['day'], e.get('time', '09:00')
        at = await pg.evaluate("s => new Date(s).getTime()", f'{day}T{hm}:00{TZ}')
        frm = self.who_is(p['from'])
        rcpt = [self.who_is(a) for a in p['to'] + p.get('cc', [])]
        got = []
        for uid in [u for u in dict.fromkeys([frm] + rcpt) if u]:
            if uid in STAFF:
                msg = {'id': f"wm_{e['id']}_{uid}", 'threadId': f"wmt_{p.get('thread') or e['id']}", 'labelIds': (p.get('labels') or ['SENT']) if uid == frm else ['INBOX', 'UNREAD'],
                       'internalDate': at, 'headers': {'From': p['from'], 'To': ', '.join(p['to']), 'Cc': ', '.join(p.get('cc', [])), 'Subject': p['subject'], 'Date': ''},
                       'body': p['text'], 'attachments': [{'id': f"wma_{e['id']}_{uid}_{i}", 'filename': a['filename'], 'mime': a.get('mime', 'application/pdf'),
                                                           'size': 40000 + 100 * len(a.get('text', '')), 'text': a.get('text', '')} for i, a in enumerate(p.get('att', []))]}
                if uid == frm: self.sim.state['sent_seen'][msg['id']] = {'by': uid, 'how': 'book', 'done': True}
                if await pg.evaluate("([u, m]) => __SIM.mbPut(u, m)", [uid, msg]): got.append(uid)
            elif uid in AGENTS and uid != frm:
                self.sim.ext_box(uid).append({'id': f"wm_{e['id']}_{uid}", 'from': p['from'], 'to': ', '.join(p['to']), 'subject': p['subject'], 'body': p['text'],
                                              'at': at, 'thread': p.get('thread') or e['id'], 'unread': True, 'att': p.get('att', [])})
                got.append(uid)
        return ','.join(got) or 'no mailbox'

    async def run_script(self, pg, e):
        """a scripted world action (sim/script_p3.js) with what its gate found, then what it tells the people who play"""
        p = dict(e['payload'])
        if not self.scripted(p.get('as') or 'u_controller', p['do']):
            return await self.played(pg, e, p)
        if p['do'] == 'field_day': p['refs'] = self.sim.cycle_refs()
        res = await pg.evaluate("async (p) => __P3.run(p)", p)
        G = self.st.setdefault('gated', {})
        if isinstance(res, dict) and res.get('bind'):
            G.setdefault(e['id'], {'day': e['day'], 'time': e.get('time'), 'bind': {}, 'opened': [e['day'], 'script']})['bind'].update(res['bind'])
        if p['do'] == 'receive' and isinstance(res, dict) and res.get('ok') and p.get('notify'):
            txt = (f"{p['number']} from {res.get('vendor', '')} came to 214 Lincoln this morning. " + ('; '.join(res.get('notes') or []) or 'Everything on the slip arrived.') +
                   '. Slip photo attached. - Angel')
            ev = {'id': f"{e['id']}_slip", 'day': self.sim.state['day'], 'time': self.sim.clock_str(), 'payload': {
                'from': self.staff_addr['u_angel'], 'to': [self.staff_addr[p['notify']]], 'cc': [], 'thread': f"cy_recv_{p['number']}", 'subject': f"Delivery {p['number']}",
                'text': txt, 'att': [{'filename': f"Packing slip {p['number']}.pdf", 'text': f"PACKING SLIP {p['number']}\n{res.get('vendor', '')}\nShip to: 214 Lincoln Place\n" + ('\n'.join(res.get('notes') or []) or 'complete')}]}}
            await self.inject_mail(pg, ev)
            self.sim.state['news'].setdefault(p['notify'], []).append(f"{self.sim.state['day']} {self.sim.clock_str()}: Angel texted you: {txt}")
        return (res.get('text') or '')[:200] if isinstance(res, dict) else str(res)[:200]

    async def played(self, pg, e, p):
        """a scripted step whose role plays it this run: the world brings what that person meets, and nothing is done
        for them. A truck (receive): what came, short and damaged, told to the person who receives it, with the slip."""
        if p['do'] != 'receive':
            return f"played by {p.get('as')}: done through the screens, not scripted"
        po = await pg.evaluate("""n => { const po = (DB.pos || []).find(x => x.number === n); if (!po) return null;
            return { vendor: po.vendor || '', lines: (po.lines || []).map(l => ({ item: l.item || l.desc || '', qty: +l.qty || 0, unit: l.unit || '' })) }; }""", p['number'])
        if not po: return 'no PO ' + p['number']
        notes = []
        if p.get('short'): notes.append(f"{p['short']['qty']} cement boards short ({p['short']['why']})")
        if p.get('damaged'): notes.append(f"{p['damaged']['qty']} {p['damaged']['unit']} of the tile damaged ({p['damaged']['why']}): photo of the boxes attached")
        who = p.get('notify') or 'u_chen'
        told = self.st.setdefault('trucks', {})   # one truck per order: the lumber and the drywall come on one PO when one yard won both
        if p['number'] in told:
            if not notes: return f"the truck for {p['number']} was already told to {who}"
            self.sim.state['news'].setdefault(who, []).append(f"{self.sim.state['day']} {self.sim.clock_str()}: Angel texted you again about {p['number']}: " + '; '.join(notes))
            told[p['number']] += notes
            return f"the truck for {p['number']}: also {'; '.join(notes)}"
        told[p['number']] = list(notes)
        txt = (f"{p['number']} from {po['vendor']} came to 214 Lincoln this morning. " + ('; '.join(notes) if notes else 'Everything on the slip arrived') +
               '. It is on the sidewalk; the slip is attached. Please receive it in the app. - Angel')
        slip = '\n'.join(f"{l['item']}: {l['qty']:g} {l['unit']} shipped" for l in po['lines'])
        ev = {'id': f"{e['id']}_truck", 'day': self.sim.state['day'], 'time': self.sim.clock_str(), 'payload': {
            'from': self.staff_addr['u_angel'], 'to': [self.staff_addr[who]], 'cc': [], 'thread': f"cy_recv_{p['number']}", 'subject': f"Delivery {p['number']}",
            'text': txt, 'att': [{'filename': f"Packing slip {p['number']}.jpg", 'mime': 'image/jpeg',
                                  'text': f"PACKING SLIP {p['number']}\n{po['vendor']}\nShip to: 214 Lincoln Place\n{slip}"}]
                               + ([{'filename': f"Damaged boxes {p['number']}.jpg", 'mime': 'image/jpeg', 'text': 'photo: two tile boxes, corners crushed, tiles cracked'}] if p.get('damaged') else [])}}
        await self.inject_mail(pg, ev)
        self.sim.state['news'].setdefault(who, []).append(f"{self.sim.state['day']} {self.sim.clock_str()}: Angel texted you: {txt}")
        return f"the truck for {p['number']} told to {who} (receiving is played): " + ('; '.join(notes) or 'complete')

    async def import_statement(self, pg, acct, day, lines, match=True):
        """the controller does not play (Pilot 3): the statement is imported through Banking > Import Statement as he
        would, then only the matches the app proposed are confirmed and the cycle job's card purchase is coded to it.
        match=False: the bank's own feed (the controller plays): the lines land unmatched for the people to match."""
        csv = 'Date,Description,Amount,Reference\n' + ''.join(f"{l['date']},{l['desc']},{float(l['amt']):.2f},{l['ref']}\n" for l in lines)
        r = await pg.evaluate("async (p) => __P3.run(p)", {'do': 'import_statement', 'as': 'u_controller', 'acct': acct, 'name': f'{acct}_{day}.csv', 'csv': csv})
        if not match: return f"the bank feed: {(r or {}).get('text', '')}"[:200]
        job = self.sim.cycle_job() if self.cycle_on else ''
        m = await pg.evaluate("async (p) => __P3.run(p)", {'do': 'match', 'as': 'u_controller', 'rx': '|'.join(re.escape(l['desc'][:14]) for l in lines) or '#',
                                                          'code': [{'rx': 'LIGHTOLOGY', 'project': job, 'cat': 'materials', 'memo': 'Lightology receipt: 2 pendant lights'}] if job else []})
        return f"{(r or {}).get('text', '')} · {(m or {}).get('text', '')}"[:200]

    async def mail_statement(self, pg, acct, day, lines):
        """The bank mails the controller the day's lines as a CSV; the controller imports it in Banking."""
        csv = 'Date,Description,Amount,Reference\n' + ''.join(f"{l['date']},{l['desc']},{float(l['amt']):.2f},{l['ref']}\n" for l in lines)
        name = self.book.get('accounts', {}).get(acct, acct)
        e = {'id': f'stmt_{acct}_{day}', 'day': day, 'time': '07:05', 'payload': {
            'from': self.parties['bank']['addr'], 'to': [self.staff_addr['u_controller']], 'cc': [], 'thread': f'stmt_{acct}',
            'subject': f'{name}: new activity, {len(lines)} lines ({day})',
            'text': f'New activity on {name} ({acct}). The lines are attached as a CSV for import (Banking > Import Statement).',
            'att': [{'filename': f'{acct}_{day}.csv', 'mime': 'text/csv', 'text': csv}]}}
        return await self.inject_mail(pg, e)

    # ---- held-out events (seeded by the run and the day; built from the live records)
    def heldout(self, day, facts):
        cfg = self.book.get('heldout', {})
        r = self.rng('heldout', day)
        kinds = cfg.get('kinds', ['late', 'partial', 'price', 'change', 'inspection', 'mismatch', 'transcript', 'card'])
        n = r.choice(cfg.get('per_day', [1, 2, 2, 3]))
        out, used = [], set()
        pos = [p for p in facts.get('pos', []) if p['status'] not in ('cancelled', 'draft', 'received', 'closed', 'billed') and p.get('vendor')]
        for i in range(n):
            k = r.choice(kinds)
            if k in used and k != 'card': continue
            used.add(k)
            eid = f"H{day[5:].replace('-', '')}-{i + 1}"
            hm = r.choice(['08:40', '09:15', '10:30', '11:45', '13:50', '14:40'])
            ev = None
            if k in ('late', 'partial', 'price', 'mismatch'):
                if not pos: continue
                po = r.choice(pos)
                v = self.party_for_vendor(po['vendor'], facts)
                item = (po.get('lines') or [{'item': 'the order'}])[0].get('item') or 'the order'
                if k == 'late':
                    eta = self.wd_add(max(day, po.get('expected') or day), r.choice([2, 3, 5]))
                    ev = self.mail_ev(eid, day, hm, v, 'u_chen', f"{po['number']}: ship date moved to {eta}",
                                      f"Sorry, {item} on {po['number']} will not ship on the date we gave you. New ship date {eta}. We will confirm the truck the day before.",
                                      {'who': 'u_chen', 'what': f"Move {po['number']} to {eta} and tell the site", 'by': 1, 'see': [po['number']],
                                       'check': {'t': 'poEta', 'number': po['number'], 'eta': eta}, 'days': 0})
                elif k == 'partial':
                    bal = self.wd_add(day, r.choice([2, 4]))
                    ev = self.mail_ev(eid, day, hm, v, 'u_chen', f"{po['number']}: partial shipment today",
                                      f"Part of {po['number']} shipped today. Backordered: {item}. Balance ships {bal}. Packing slip attached.",
                                      {'who': 'u_chen', 'what': f"Receive {po['number']} as partial and chase the balance due {bal}", 'by': 2, 'see': [po['number']],
                                       'check': {'t': 'seenBy', 'uid': 'u_chen'}},
                                      att=[{'filename': f"Packing slip {po['number']}.pdf", 'text': f"PACKING SLIP {po['number']} PARTIAL. Backordered: {item}. Balance {bal}."}])
                    ev['also'] = [{'uid': 'u_angel', 'text': f"The delivery for {po['number']} ({po['vendor']}) came short today: {item} is not on the truck."}]
                elif k == 'price':
                    pct = r.choice([4, 6, 9])
                    ev = self.mail_ev(eid, day, hm, v, 'u_chen', f"Price change on {item}",
                                      f"Notice: {item} goes up {pct}% on orders placed after {self.wd_add(day, 5)}. Open orders ({po['number']}) keep the quoted price.",
                                      {'who': 'u_chen', 'what': f'Weigh the {pct}% rise on {item} before the next order', 'by': 3, 'see': [item[:24]],
                                       'check': {'t': 'seenBy', 'uid': 'u_chen'}})
                else:
                    over = round(float(po.get('total') or 1000) * r.choice([0.06, 0.08, 0.12]), 2)
                    inv = f"{re.sub(r'[^A-Z]', '', po['vendor'].upper())[:3] or 'VND'}-{r.randrange(2000, 9999)}"
                    total = round(float(po.get('total') or 1000) + over, 2)
                    ev = self.mail_ev(eid, day, hm, v, 'u_chen', f"Invoice {inv} for {po['number']}",
                                      f"Please find invoice {inv} for {po['number']} attached, ${total:,.2f}, due net 30.",
                                      {'who': 'u_chen', 'what': f"Enter {inv} against {po['number']} and hold the ${over:,.2f} over the PO (three-way match)", 'by': 2,
                                       'see': [inv], 'check': {'t': 'billShortAny', 'number': inv}, 'money': over},
                                      att=[{'filename': f'Invoice {inv}.pdf', 'text': f"INVOICE {inv}\nPO: {po['number']}\nProject: {po.get('projectName', '')}\n{item}\nTOTAL ${total:,.2f}"}])
            elif k == 'change':
                what = r.choice(['a second towel bar and a recessed medicine cabinet in the garden bath', 'dimmers on every bedroom circuit', 'a gas line stub for a future range'])
                ev = {'id': eid, 'day': day, 'time': hm, 'kind': 'situation', 'payload': {'uid': 'u_klein', 'text': f'You decide you want {what}. Ask the firm what it costs and how long it adds.'},
                      'expect': {'who': 'u_alan', 'what': f'Price the change ({what}) and send a CO within 48 hours', 'by': 2, 'see': ['Klein'],
                                 'check': {'t': 'co', 'project': 'p121', 'status': ['sent', 'approved'], 'rx': what.split()[1]}}, 'tags': ['held-out', 'client change']}
            elif k == 'inspection':
                why = r.choice(['firestopping missing at the 3rd floor penetrations', 'no nail plates where the plumbing crosses the studs', 'smoke detector not interconnected'])
                ev = self.mail_ev(eid, day, hm, 'inspector', 'u_alan', 'Inspection result 121 State Street: FAILED',
                                  f'Inspection at 121 State Street failed: {why}. Correct and request a re-inspection.',
                                  {'who': 'u_alan', 'what': 'Plan the correction and book the re-inspection', 'by': 1, 'see': ['FAILED', 'Inspection result'],
                                   'check': {'t': 'task', 'title': 're-?insp|inspection|firestop|nail plate|detector'}, 'days': 1})
                ev['also'] = [{'uid': 'u_angel', 'text': f'The inspector failed us today: {why}.'}]
            elif k == 'transcript':
                proj = r.choice(facts.get('projects') or [{'name': '121 State Street'}])['name']
                who = r.choice(['Chen', 'Sarah', 'Angel'])
                text = (f"Transcript - {proj} coordination - {day}\nAlan: where are we on the kitchen?\n{who}: the cabinet shop drawings come back Thursday.\n"
                        f"Alan: {who}, can you get me the revised dates by Friday?\n{who}: yes, I will send them by Friday.\nAlan: and we need the electrician's walk booked next week.")
                ev = {'id': eid, 'day': day, 'time': hm, 'kind': 'drive', 'payload': {'uid': 'u_alan', 'name': f'Transcript - {proj} coordination - {day}.txt', 'text': text},
                      'expect': {'who': 'u_alan', 'what': f'Turn the {proj} coordination meeting into owned, dated tasks', 'by': 2, 'see': ['coordination'],
                                 'check': {'t': 'meetingFrom', 'rx': 'coordination'}}, 'tags': ['held-out', 'transcript']}
            elif k == 'card':
                vend = r.choice(['HOME DEPOT PRO #6120 BROOKLYN', 'SHELL OIL 57442 BROOKLYN', 'BROOKLYN LUMBER YARD', 'NEMO TILE CO'])
                amt = -round(r.uniform(38, 640), 2)
                ref = f"AC2-{day.replace('-', '')}-H{i}"
                ev = {'id': eid, 'day': day, 'time': '07:40', 'kind': 'bank', 'payload': {'acct': 'ac2', 'date': day, 'desc': vend, 'amt': amt, 'ref': ref},
                      'expect': {'who': 'u_controller', 'what': f'Code and match the card charge {vend} ${-amt:,.2f}', 'by': 3, 'see': [vend[:18]],
                                 'check': {'t': 'txn', 'desc': vend[:18], 'coded': True}}, 'tags': ['held-out', 'card']}
            if ev:
                ev.setdefault('tags', ['held-out', k])
                out.append(ev)
                for j, s in enumerate(ev.pop('also', [])):
                    out.append({'id': f'{eid}s{j}', 'day': day, 'time': hm, 'kind': 'situation', 'payload': s, 'tags': ['held-out', k]})
        return out

    def party_for_vendor(self, vendor, facts):
        k = self.resolve_party(vendor)
        if k: return k
        v = next((x for x in facts.get('vendors', []) if x['name'] == vendor), None)
        key = re.sub(r'\W+', '_', vendor.lower()).strip('_')[:24]
        self.parties[key] = {'name': vendor, 'addr': f"{vendor} <{(v or {}).get('email') or key.replace('_', '') + '@vendor.example'}>", 'kind': 'vendor',
                             'reply_p': 0.8, 'delay': [0, 2]}
        return key

    def mail_ev(self, eid, day, hm, party, to_uid, subject, text, expect, att=None):
        return {'id': eid, 'day': day, 'time': hm, 'kind': 'mail',
                'payload': {'from': self.parties[party]['addr'], 'to': [self.staff_addr[to_uid]], 'cc': [], 'subject': subject, 'text': text, 'att': att or [], 'thread': eid},
                'expect': expect, 'tags': ['held-out']}

    # ---- replies to what the firm sends out
    def classify(self, m, party):
        t = f"{m['subject']} {m['body']}".lower()
        kind = party.get('kind', 'other')
        if re.search(r'\brfq\b|request for quot|quote|pricing|price for', t): return 'quote'
        if re.search(r'\bpo-\d|purchase order|please (ship|deliver)|\border\b', t) and kind in ('vendor', 'sub'): return 'order'
        if re.search(r'\bcoi\b|certificate of insurance|insurance', t): return 'coi'
        if kind == 'client' and re.search(r'invoice|payment|past due|overdue|balance', t): return 'pay'
        if kind == 'client' and re.search(r'approv|change order|\bco-\d|decision|choose|select', t): return 'approve'
        if kind == 'inspector' and re.search(r'inspect|re-?inspection|schedule', t): return 'inspect'
        if kind == 'architect': return 'architect'
        return 'other'

    def on_outbound(self, m, addr):
        k = self.resolve_party(addr)
        if not k:
            self.st['replied'][m['id'] + addr] = 'unknown party: no answer'; return
        p = self.parties[k]
        r = self.rng('reply', m['id'], addr)
        kind = self.classify(m, p)
        hit = next((t for rx, t in p.get('answers') or [] if re.search(rx, f"{m['subject']} {m['body']}", re.I)), None)
        if hit:   # a party with something to say about this (the client's answer to a question back)
            subj = m['subject'] if m['subject'].lower().startswith('re:') else 'Re: ' + m['subject']
            self.st['pending'].append(self._reply(k, m, addr, subj, hit, [], self.sim.state['day'], SLOT_ORDER[min(3, SI(self.sim.state['slot']) + 1)], 'answer'))
            return
        if kind in (p.get('book_plays') or []):
            self.st['replied'][m['id'] + addr] = f'{k}: the book plays this ({kind})'; return
        if r.random() > p.get('reply_p', 0.75):
            self.st['replied'][m['id'] + addr] = f'{k}: never answers'; return
        dmin, dmax = p.get('delay', [0, 2])
        due_day = self.wd_add(self.sim.state['day'], r.randint(dmin, dmax))
        due_slot = r.choice(SLOT_ORDER[1:]) if due_day != self.sim.state['day'] else SLOT_ORDER[min(3, SI(self.sim.state['slot']) + 1)]
        subj = m['subject'] if m['subject'].lower().startswith('re:') else 'Re: ' + m['subject']
        po = (re.findall(r'PO-\d{4}-\d+', m['subject'] + ' ' + m['body']) or [''])[0]
        amt = money(m['body'])
        text, att, bank = '', [], None
        if kind == 'quote' and p.get('quotes') and self.cycle:
            text, att = self.quote_reply(p, m)
        elif kind == 'quote':
            price = amt * r.uniform(0.9, 1.15) if amt else r.uniform(800, 9000)
            text = f"Thanks for the request. Our price: ${price:,.2f} for the items as listed, lead time {r.choice([3, 5, 8, 10])} working days, valid 30 days."
            att = [{'filename': f"Quote {p['name'][:20]}.pdf", 'text': f"QUOTE\n{p['name']}\nRe: {m['subject']}\nTOTAL ${price:,.2f}"}]
        elif kind == 'order':
            ship = self.wd_add(due_day, r.choice(p.get('ship', [2, 3, 4, 6])))
            text = f"Order received{(' for ' + po) if po else ''}. It ships {ship}." + (' We are short on part of it and will confirm.' if r.random() < 0.2 else '')
            if po and not self.po_tracked(m['body'] + ' ' + m['subject'], po): self.order_flow(k, p, m, po, amt, ship, r)
            if r.random() < p.get('late_p', 0.25):
                late = self.wd_add(ship, r.choice([2, 3]))
                self.st['pending'].append(self._reply(k, m, addr, subj, f"Update{(' on ' + po) if po else ''}: the ship date moves to {late}.", [], self.wd_add(ship, -1) if ship > due_day else due_day, 'work1', 'slip'))
        elif kind == 'coi':
            text = 'Certificate attached.'
            att = [{'filename': f"COI {p['name'][:24]}.pdf", 'text': f"CERTIFICATE OF LIABILITY INSURANCE\nInsured: {p['name']}\nCertificate holder: SmartDesign Group LLC\nPolicy period {self.sim.state['day']} to {self.wd_add(self.sim.state['day'], 260)}"}]
        elif kind == 'pay':
            when = self.wd_add(due_day, r.choice([0, 1, 3]))
            text = f"Thanks. We will send the payment on {when}."
            if amt and r.random() < 0.85 and not p.get('no_bank'):   # a party whose payment the book plays (Pilot 2's prospect) sends no second one
                bank = {'acct': 'ac1', 'date': when, 'desc': f"ONLINE TRANSFER FROM {p['name'].upper()[:24]}", 'amt': round(amt, 2), 'ref': f"AC1-{when.replace('-', '')}-W{self.st['n']}"}
        elif kind == 'approve':
            text = r.choice(['Approved. Go ahead.', 'We approve this. Thank you.', 'Can you tell us how many days this adds before we sign?'])
        elif kind == 'inspect':
            text = f"Re-inspection booked for {self.wd_add(due_day, 2)} between 9 and 12."
        elif kind == 'architect':
            text = r.choice(['Reviewed. Approved as noted; see the markups.', 'Revise and resubmit: the detail at the parapet does not match A-501.', 'Received. I will respond by Friday.'])
        else:
            text = r.choice(['Got it, thanks.', 'Received. I will get back to you.', 'Noted.'])
        self.st['pending'].append(self._reply(k, m, addr, subj, text, att, due_day, due_slot, kind, bank))

    def quote_reply(self, p, m):
        """A planted vendor's answer to an RFQ (sim/cycle_book.py QUOTES), in its own format: a table, a PDF with a typo
        price, prose with no lead time, or per box. Lines are the RFQ's own (L1 | item | spec | qty | unit), else the
        quantities the mail names; a lump-sum line is priced as the lot the job's material schedule lists."""
        import math
        Q, C = p['quotes'], self.cycle
        rows = [(a, b.strip(), float(c), d.strip()) for a, b, c, d in re.findall(r'^\s*(L\d+)\s*\|\s*([^|\n]+?)\s*\|[^|\n]*\|\s*([\d.]+)\s*\|\s*([^|\n]+?)\s*$', m['body'], re.M)]
        if not rows:
            rows = [('-', it.strip(), float(q), u) for q, u, it in re.findall(r'(\d+(?:\.\d+)?)\s*(sheets?|pcs?|pieces|sf|rolls?|ea|boxes)\s+(?:of\s+)?([^\n,;]+)', m['body'], re.I)]
        key_of = lambda t: next((k for k, rx in C['item_rx'].items() if re.search(rx, t, re.I) and k in Q['prices']), None)
        out = []
        for lid, item, qty, unit in rows:
            if re.match(r'ls|lot|lump', unit, re.I):
                lot = next((k for k, rx in C['lots'].items() if re.search(rx, item, re.I)), None)
                parts = [(x, key_of(x['item'])) for x in C['schedule'].get(lot, [])] if lot else []
                parts = [(x, kk) for x, kk in parts if kk]
                if not parts: out.append((lid, item, qty, unit, None, None, '')); continue
                ext = sum(x['qty'] * Q['prices'][kk] for x, kk in parts) * qty
                shown = '; '.join(f"{x['qty']} {x['unit']} {x['item']} @ ${(Q['prices'][kk] * (100 if Q.get('typo') == kk else 1)):,.2f}" for x, kk in parts)
                out.append((lid, item, qty, unit, round(ext / qty, 2), round(ext, 2), 'incl. ' + shown))
                continue
            kk = key_of(item)
            if not kk: out.append((lid, item, qty, unit, None, None, '')); continue
            u = Q['prices'][kk]
            if Q.get('form') == 'box':
                boxes = math.ceil(qty / Q['box_sf']); out.append((lid, item, boxes, 'box', u, round(u * boxes, 2), f"{Q['box_sf']} sf per box, {boxes} boxes for {qty:g} {unit}")); continue
            out.append((lid, item, qty, unit, round(u * (100 if Q.get('typo') == kk else 1), 2), round(u * qty, 2), ''))
        who = (m.get('from') or '').split('<')[0].strip().split(' ')[0] or 'there'
        rfq = (re.findall(r'RFQ-\d{4}-\d+', m['subject'] + ' ' + m['body']) or [''])[0]
        head = (f"Freight: ${Q['freight']:,.2f} delivered to site" if Q['freight'] else 'Free delivery to site') + \
               (f"\nLead time: {Q['lead']} working days" if Q.get('lead') else '') + f"\nPrices valid {Q['valid']} days"
        sign = f"{p.get('contact', p['name'])}\n{p['name']}"

        def row(x, sep=True):
            lid, item, qty, unit, u, ext, note = x
            if u is None: return f"{lid} | {item} | no quote" if sep else f"{lid}  {item}  NO QUOTE"
            s = f"{lid} | {item} | {qty:g} {unit} | ${u:,.2f} | ${ext:,.2f}" if sep else f"{lid}  {item}  {qty:g} {unit.upper()}  {u:,.2f}  {ext:,.2f}"
            return s + (f"\n     {note}" if note else '')
        if Q['form'] == 'pdf':
            return (f"Hello {who},\n\nPlease see our quote attached for {rfq or 'your request'}.\n\n{sign}",
                    [{'filename': f"Quote {p['name'][:20]} {rfq}.pdf", 'text': f"{p['name'].upper()}\nQUOTATION\nRef: {rfq}\nTo: SmartDesign\n\nLINE ITEM QTY UNIT EXT\n" +
                      '\n'.join(row(x, False) for x in out) + f"\n\n{head}\nTerms: net 30"}])
        if Q['form'] == 'prose':
            parts = [f"{x[0]} the {x[1]} at ${x[4]:,.2f} ({x[2]:g} {x[3]}, ${x[5]:,.2f})" + (f" ({x[6]})" if x[6] else '') for x in out if x[4] is not None]
            return (f"Hi {who},\n\nThanks for thinking of us for {rfq or 'this one'}. We can do " + ', and '.join(parts or ['nothing on this list']) +
                    f". {'Free delivery' if not Q['freight'] else 'Delivery $' + str(Q['freight'])}, prices good for {Q['valid']} days.\n\n{sign}", [])
        return (f"Hi {who},\n\nThanks for the request. Our quote for {rfq or 'your list'}:\n\nLine | Item | Qty | Unit Price | Extended\n" +
                '\n'.join(row(x) for x in out) + f"\n\n{head}\n\n{sign}", [])

    def order_flow(self, k, p, m, po, amt, ship, r):
        """An order the world accepted: the truck comes on the ship day (the foreman meets it), the invoice follows,
        and a vendor paid on delivery shows up on the card the next morning."""
        L = [x.strip('- ').strip() for x in m['body'].splitlines() if x.strip().startswith('-')]
        items = '; '.join([x for x in L if re.search(r'@|\$|\d+ (ea|sheet|box|roll|lf|sf|ls|pc)', x)][:3] or L[:1])[:160] or 'the order'
        sid = f'D{self.st["n"] + 1:04d}'
        self.st['extra'].append({'id': sid, 'day': ship, 'time': '09:20', 'kind': 'situation', 'payload': {'uid': 'u_angel',
            'text': f"{p['name']} delivered {po} to the site this morning: {items}. You have the packing slip in your hand."},
            'expect': {'who': 'u_angel', 'what': f'Receive {po} on the app (count it, photograph the slip)', 'by': 1, 'see': [po],
                       'check': {'t': 'poStatus', 'number': po, 'status': ['received', 'partial', 'closed', 'billed']}}, 'tags': ['world', 'delivery']})
        inv = f"{re.sub(r'[^A-Z]', '', p['name'].upper())[:3] or 'INV'}-{r.randrange(1000, 9999)}"
        total = round(amt, 2) if amt else round(r.uniform(300, 4000), 2)
        self.st['n'] += 1
        self.st['pending'].append({'id': f"R{self.st['n']:04d}", 'party': k, 'to_uid': m['uid'], 'to': m['from'], 'subject': f'Invoice {inv} for {po}',
            'text': f'Invoice {inv} for {po} is attached: ${total:,.2f}. Thank you for the order.', 'kind': 'invoice', 'thread': f'inv_{inv}', 'bank': None,
            'att': [{'filename': f'Invoice {inv}.pdf', 'text': f"INVOICE {inv}\n{p['name']}\nPO: {po}\n{items}\nTOTAL ${total:,.2f}"}], 'day': ship, 'slot': 'work2',
            'their_message': m['subject'], 'expect': {'who': m['uid'], 'what': f'Enter {inv} against {po}', 'by': 2, 'see': [inv],
                                                      'check': {'t': 'bill', 'number': inv, 'poNumber': po}, 'money': total}})
        if p.get('pay') == 'card':
            desc = re.sub(r'[^A-Z ]', '', p['name'].upper())[:22]
            self.st.setdefault('scheduled_bank', []).append({'acct': 'ac2', 'date': ship, 'desc': desc, 'amt': -total, 'ref': f"AC2-{ship.replace('-', '')}-{inv}",
                                                             'expect_matched': True})

    def _reply(self, k, m, addr, subj, text, att, day, slot, kind, bank=None):
        self.st['n'] += 1
        rid = f"R{self.st['n']:04d}"
        rec = {'id': rid, 'party': k, 'to_uid': m['uid'], 'to': m['from'], 'subject': subj, 'text': text, 'att': att, 'day': day, 'slot': slot, 'kind': kind,
               'thread': m.get('thread') or m['id'], 'bank': bank, 'their_message': f"{m['subject']}\n{m['body'][:1500]}"}
        if self.sim.state['world'].get('agent') or self.voice_on:
            d = os.path.join(self.sim.dir, 'world', 'pending'); os.makedirs(d, exist_ok=True)
            json.dump(self.pending_rec(rec), open(os.path.join(d, rid + '.json'), 'w'), indent=1)
        return rec

    # ---- the voicer (sim/voicer.py): the reply in the party's own words, the rule's facts kept
    @property
    def voice_on(self):
        return bool(self.sim.state.get('world', {}).get('voice'))

    def pending_rec(self, rp):
        p = self.parties.get(rp['party'], {})
        return {'id': rp['id'], 'party': p, 'persona': p.get('voice', ''), 'kind': rp.get('kind'), 'their_message': rp.get('their_message', ''),
                'template_reply': rp['text'], 'att': [a.get('filename') for a in rp.get('att') or []], 'due': [rp['day'], rp['slot']],
                'answer_file': os.path.join(self.sim.dir, 'world', 'answers', rp['id'] + '.txt')}

    def next_slot(self, day, slot):
        i = SI(slot)
        return (day, SLOT_ORDER[i + 1]) if i < 3 else (self.wd_add(day, 1), 'work1')

    async def voice_reply(self, rp, day, slot):
        """Voice a reply that is due now: returns 'deliver', or 'later' when its style holds it a slot (late) """
        import voicer as V
        rec = self.pending_rec(rp)
        r = await asyncio.to_thread(V.voice, rec, self.sim.state['seed'])
        rp['voiced'] = r['style']
        ans = rec['answer_file']; os.makedirs(os.path.dirname(ans), exist_ok=True)
        if r['ok']: open(ans, 'w', encoding='utf-8').write(r['text'])
        when = 'now'
        if r['style'] == 'late' and r['ok']:
            rp['day'], rp['slot'] = self.next_slot(day, slot); when = f"late, at {rp['day']} {rp['slot']}"
        if r['ok'] and r['second']:
            d2, s2 = self.next_slot(day, slot)
            self.st['pending'].append({**{k: v for k, v in rp.items() if k not in ('expect', 'bank', 'att')}, 'id': rp['id'] + 'b', 'text': r['second'], 'att': [],
                                       'day': d2, 'slot': s2, 'voiced': 'partial (the rest)', 'kind': rp.get('kind', '') + ' (rest)'})
            when = f"now, the rest at {d2} {s2}"
        V.log(self.sim.dir, {'id': rp['id'], 'party': (self.parties.get(rp['party']) or {}).get('name', rp['party']), 'kind': rp.get('kind'), 'style': r['style'],
                             'ok': r['ok'], 'why': r['why'], 'missing': r['missing'], 'invented': r['invented'], 'facts': len(V.facts(rp['text'])), 'when': when,
                             'day': day, 'slot': slot, 'usage': r['usage']})
        self.sim.log({'uid': '__world', 'cmd': 'voice', 'args': [rp['id'], r['style']], 'ok': r['ok'], 'result': (r['why'] or when)[:200]})
        return 'later' if when.startswith('late') else 'deliver'

    async def deliver_replies(self, pg, day, slot):
        out, keep = [], []
        now = (day, SI(slot))
        due = [rp for rp in self.st['pending'] if (rp['day'], SI(rp['slot'])) <= now]
        keep = [rp for rp in self.st['pending'] if (rp['day'], SI(rp['slot'])) > now]
        self.st['pending'] = keep   # a voiced reply's second part is appended here while the due ones go out
        for rp in due:
            ans = os.path.join(self.sim.dir, 'world', 'answers', rp['id'] + '.txt')
            if self.voice_on and not rp.get('voiced') and not os.path.exists(ans):
                if await self.voice_reply(rp, day, slot) == 'later': self.st['pending'].append(rp); continue
            text = open(ans).read().strip() if os.path.exists(ans) else rp['text']
            p = self.parties[rp['party']]
            e = {'id': rp['id'], 'day': day, 'time': self.sim.clock_str(), 'payload': {'from': p['addr'], 'to': [rp['to']], 'cc': [], 'subject': rp['subject'], 'text': text,
                                                                                    'att': rp['att'], 'thread': rp['thread']}}
            r = await self.inject_mail(pg, e)
            if rp.get('expect'):
                self.st['extra'].append({'id': rp['id'], 'day': day, 'time': self.sim.clock_str(), 'kind': 'reply', 'payload': {}, 'expect': rp['expect'], 'tags': ['world reply', rp['kind']]})
                self.st['fired'][rp['id']] = 'delivered'
            if rp.get('bank'): self.st.setdefault('scheduled_bank', []).append(rp['bank'])
            out.append([rp['id'], rp['party'], rp['kind'], r] + ([f"voiced: {rp['voiced']}"] if rp.get('voiced') else []))
        # promised payments arrive at the bank on their day, on the next statement
        sb, rest = self.st.get('scheduled_bank', []), []
        for b in sb:
            if b['date'] <= day:
                self.book_bank_line(b)
            else: rest.append(b)
        self.st['scheduled_bank'] = rest
        return out

    def book_bank_line(self, b):
        eid = 'B' + b['ref']
        if any(e['id'] == eid for e in self.st['extra']): return
        on = self.next_day(self.sim.state['day'])   # on the next morning's statement
        b = dict(b); matched = b.pop('expect_matched', False)
        ex = ({'who': 'u_controller', 'what': f"Match the card line {b['desc']} ${-b['amt']:,.2f} to its bill", 'by': 3, 'see': [b['desc'][:18]],
               'check': {'t': 'txn', 'desc': b['desc'][:18], 'matched': True}} if matched else
              {'who': 'u_billing', 'what': f"Record the payment {b['desc']} ${b['amt']:,.2f}", 'by': 2, 'see': [b['desc'][:18]],
               'check': {'t': 'txn', 'desc': b['desc'][:18], 'resolved': True}})
        self.st['extra'].append({'id': eid, 'day': on, 'time': '07:40', 'kind': 'bank', 'payload': b, 'expect': ex, 'tags': ['world', 'card' if matched else 'payment']})

    async def client_portal(self, day, slot):
        """The Kleins, played by rules when no client agent takes turns (the lean plan): they approve or question what
        the firm sends to the portal after a day or so, and pay invoices by bank transfer. Done on their own phone page,
        through the portal's buttons. A question is template text, or the world-agent hook's answer if one is written."""
        sim, out = self.sim, []
        P = self.st.setdefault('portal', {})
        pg, _ = await sim.fresh('u_klein')
        await sim.set_clock()
        items = await pg.evaluate("""() => { const c = DB.clients.find(x => x.id === userClientOf(DB.users.find(u => u.id === 'u_klein'))); if (!c) return [];
            const t = d => { try { return docTotal(d).total; } catch (e) { return 0; } }, paid = d => (c.payments || []).filter(p => p.invoiceId === d.id).reduce((a, p) => a + (+p.amount || 0), 0);
            return [].concat((c.estimates || []).filter(d => d.status === 'sent').map(d => ({ key: 'estimate:' + d.id, kind: 'approve', number: d.number, title: d.title })),
              (c.changeOrders || []).filter(d => d.status === 'sent').map(d => ({ key: 'co:' + d.id, kind: 'approve', number: d.number, title: d.title })),
              (c.invoices || []).filter(d => ['sent', 'overdue', 'partial'].includes(d.status)).map(d => ({ key: 'inv:' + d.id, kind: 'pay', number: d.number, title: d.title, due: d.due || '', owed: Math.round((t(d) - paid(d)) * 100) / 100 }))); }""")
        for it in items:
            st = P.get(it['key'])
            r = self.rng('portal', it['key'], (st or {}).get('round', 0))
            if not st:
                st = P[it['key']] = {'seen': day, 'round': 0, 'number': it['number'],
                                     'on': self.wd_add(day, r.choice([0, 1, 1, 2])), 'do': 'approve' if (it['kind'] == 'pay' or r.random() < 0.8) else 'ask'}
                if it['kind'] == 'pay':
                    if r.random() < 0.85 and it['owed'] > 0:
                        when = max(it['due'] or day, self.wd_add(day, 1))
                        self.st.setdefault('scheduled_bank', []).append({'acct': 'ac1', 'date': when, 'desc': 'ONLINE TRANSFER FROM KLEIN S', 'amt': it['owed'],
                                                                         'ref': f"AC1-{when.replace('-', '')}-{it['number']}"})
                        st['did'] = f"will pay ${it['owed']:,.2f} by transfer on {when}"
                    else: st['did'] = 'not paying yet'
                    out.append([it['number'], st['did']]); continue
            if it['kind'] == 'pay' or st.get('done') or st['on'] > day: continue
            if st['do'] == 'ask':
                q = f"Before we sign {it['number']} ({it['title']}): how many days does it add, and what exactly is included?"
                rid = f"Q{it['key'].replace(':', '_')}"
                if self.st.get('agent'):
                    d = os.path.join(sim.dir, 'world', 'pending'); os.makedirs(d, exist_ok=True)
                    json.dump({'id': rid, 'party': 'the Kleins (client)', 'persona': self.parties.get('sarah_klein', {}).get('voice', ''), 'their_message': f"{it['number']} {it['title']} sent for approval",
                               'template_reply': q, 'answer_file': os.path.join(sim.dir, 'world', 'answers', rid + '.txt')}, open(os.path.join(d, rid + '.json'), 'w'), indent=1)
                af = os.path.join(sim.dir, 'world', 'answers', rid + '.txt')
                if self.voice_on and not os.path.exists(af):   # the Kleins ask in their own words (a portal chat line: plain or terse)
                    import voicer as V
                    rec = {'id': rid, 'party': self.parties.get('sarah_klein', {'name': 'Sarah Klein'}), 'persona': self.parties.get('sarah_klein', {}).get('voice', ''), 'kind': 'portal question',
                           'their_message': f"{it['number']} {it['title']} sent for approval", 'template_reply': q, 'att': []}
                    st0 = V.style_for(rec, sim.state['seed']); st0 = st0 if st0 in ('plain', 'terse', 'question_back') else 'plain'
                    vr = await asyncio.to_thread(V.voice, rec, sim.state['seed'], st0)
                    os.makedirs(os.path.dirname(af), exist_ok=True)
                    if vr['ok']: open(af, 'w', encoding='utf-8').write(vr['text'])
                    V.log(sim.dir, {'id': rid, 'party': 'Sarah Klein', 'kind': 'portal question', 'style': vr['style'], 'ok': vr['ok'], 'why': vr['why'],
                                    'missing': vr['missing'], 'invented': vr['invented'], 'facts': len(V.facts(q)), 'when': 'now', 'day': day, 'slot': slot, 'usage': vr['usage']})
                if os.path.exists(af): q = open(af).read().strip()
                ok = await pg.evaluate("""async (q) => { view = 'chat'; render(); await new Promise(r => setTimeout(r, 200)); const ta = document.querySelector('#chat-text'), b = document.querySelector('#chat-send');
                    if (!ta || !b) return false; ta.value = q; ta.dispatchEvent(new Event('input', { bubbles: true })); b.click(); return true; }""", q)
                st.update({'round': st['round'] + 1, 'do': 'approve', 'on': self.wd_add(day, 1), 'asked': q if ok else 'no chat box on the portal'})
                out.append([it['number'], 'asked in the portal chat' if ok else 'could not ask: no chat box'])
                continue
            await pg.evaluate("() => { view = 'client'; render(); }"); await sim.settle(pg, 300)
            btn = pg.locator(f"section.view.on [data-papprove='{it['key']}']")
            if not await btn.count():
                st.update({'done': True, 'did': 'no Approve button on the portal'}); out.append([it['number'], st['did']]); continue
            await btn.first.click(timeout=4000); await sim.settle(pg, 400)
            if await pg.locator('#pa-name').count() and not await pg.locator('#pa-name').input_value(): await pg.fill('#pa-name', 'Sarah Klein')
            if await pg.locator('#pa-agree').count() and not await pg.locator('#pa-agree').is_checked(): await pg.locator('#pa-agree').click()
            if await pg.locator('#mbm #mbm-ok').count(): await pg.locator('#mbm #mbm-ok').click(timeout=4000); await sim.settle(pg, 500)
            toast = (await pg.evaluate("__SIM.toasts"))[-1:] or ['']
            st.update({'done': True, 'did': 'approved on the portal: ' + toast[0][:80]}); out.append([it['number'], st['did']])
        await sim.commit('u_klein')
        sim.log({'uid': '__world', 'cmd': 'client_portal', 'result': out})
        return out

    def on_call(self, uid, party, said):
        p = self.parties.get(party, {'name': party, 'kind': 'other'})
        r = self.rng('call', uid, party, self.sim.state['day'], self.sim.state['actions'])
        if r.random() > p.get('reply_p', 0.75) + 0.1: return f"{p['name']}: no answer; voicemail. (Logged in your diary only.)"
        kind = self.classify({'subject': '', 'body': said}, p)
        ans = {'order': f"{p['name']}: we have it; it ships {self.wd_add(self.sim.state['day'], r.choice([1, 2, 3]))}.",
               'quote': f"{p['name']}: send me the list by mail and I will price it today.",
               'pay': f"{p['name']}: we will look at the invoice tonight.",
               'approve': f"{p['name']}: send it in writing and we will sign.",
               'inspect': f"{p['name']}: book it in DOB NOW; the next window is {self.wd_add(self.sim.state['day'], 3)}."}.get(kind, f"{p['name']}: understood.")
        return ans + ' (A call is not a record: log it in the app if it is a promise.)'


FACTS_JS = """() => { const tot = po => { try { return poTotal(po).total; } catch (e) { return (po.lines || []).reduce((a, l) => a + (+l.qty || 0) * (+l.cost || +l.rate || 0), 0); } };
  return {
    pos: (DB.pos || []).map(po => ({ number: po.number, vendor: po.vendor, status: po.status, expected: po.expected || '', projectId: po.projectId,
      projectName: ((DB.projects.find(p => p.id === po.projectId) || {}).project || {}).name || '', total: tot(po), lines: (po.lines || []).slice(0, 3).map(l => ({ item: l.item || l.desc || '' })) })),
    vendors: (DB.vendors || []).map(v => ({ name: v.name, email: v.email || '' })),
    projects: DB.projects.map(p => ({ id: p.id, name: (p.project || {}).name || p.name || p.id, clientId: p.clientId })) }; }"""
