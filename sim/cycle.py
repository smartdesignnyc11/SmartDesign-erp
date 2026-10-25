"""sim/cycle.py: Pilot 3's business-cycle referee (sim/cycle_book.json). Pure Python on the raw database.

Every figure here is computed from the records themselves (db.json, the snapshot the harness writes after every
change), never from the app's report functions, so a report that is wrong cannot grade itself right. It answers:
- each required step (sim/cycle_book.json `steps`): done right, done wrong (what), not done, or scripted (a world
  action standing in for a role that does not play), and who owned it;
- each planted money leak: whether the plant held (the people's own records made it real), who caught it (the app,
  a person, nobody) and the money left behind;
- the referee's own numbers (job cost per estimate line, lines over, work done not billed, reimbursables not billed
  back, cash, AR) and each person's written answers graded against them;
- coverage: of each role's main module, the pages the person opened, and whether the grade is valid (the floor);
- the realism judge's verdicts (sim/realism_judge.md) and the grades discounted for flagged turns.
The world asks it for gates too (`gate`): a chained book event fires when its step is done, with what it found.

    python3 sim/cycle.py <db.json> [actions.jsonl]     print the steps, the leaks and the figures for a snapshot
"""
import json, os, re, sys
from collections import defaultdict
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
BOOK = os.path.join(HERE, 'cycle_book.json')
SENT = ('sent', 'viewed', 'partial', 'paid', 'overdue')
LIVE_PO = ('issued', 'sent', 'acknowledged', 'confirmed', 'partial', 'received', 'billed', 'closed')
r2 = lambda x: round(float(x or 0) + 0.0, 2)
num = lambda x: float(x) if isinstance(x, (int, float)) else (float(re.sub(r'[^\d.\-]', '', str(x))) if re.search(r'\d', str(x or '')) else 0.0)


def load_book(path=BOOK):
    return json.load(open(path, encoding='utf-8'))


def wd_between(a, b):
    """working days from a to b (b after a), weekends out"""
    if not a or not b or b <= a: return 0
    x, y, n = date.fromisoformat(a[:10]), date.fromisoformat(b[:10]), 0
    while x < y:
        x += timedelta(days=1)
        if x.weekday() < 5: n += 1
    return n


# ---------------------------------------------------------------- documents, the referee's own arithmetic
def doc_total(d):
    """an estimate, change order or invoice: lines, less discount, plus tax on taxable lines; an SOV invoice is this
    period's % of each scheduled line less retainage (checked against the app's stored amounts on Pilot 2's data)"""
    L = d.get('lines') or []
    if d.get('mode') == 'sov':
        amt = lambda l: num(l.get('scheduled')) * num(l.get('pct')) / 100
    else:
        amt = lambda l: num(l.get('qty') if l.get('qty') not in (None, '') else 1) * num(l.get('rate'))
    sub = sum(amt(l) for l in L); tx = sum(amt(l) for l in L if l.get('taxable'))
    dc = d.get('discount') or {}
    disc = sub * num(dc.get('value')) / 100 if dc.get('type') == 'pct' else num(dc.get('value'))
    f = (sub - disc) / sub if sub else 1
    ret = (sub - disc) * num(d.get('retainagePct')) / 100 if d.get('mode') == 'sov' else 0
    if not L and d.get('amount') is not None: return r2(d['amount'])
    return r2(sub - disc + tx * f * num(d.get('taxRate')) / 100 - ret)


def po_total(po):
    return r2(sum(num(l.get('qty')) * num(l.get('price') if l.get('price') not in (None, '') else l.get('cost')) for l in po.get('lines') or [])
              + num(po.get('tax')) + num(po.get('shipping')))


def po_line_total(l):
    return r2(num(l.get('qty')) * num(l.get('price') if l.get('price') not in (None, '') else l.get('cost')))


def bill_total(b):
    L = b.get('lines') or []
    return r2(sum(num(l.get('amount')) for l in L)) if L else r2(b.get('amount'))


def held_on(b):
    """what a bill holds back: the approved-short split, or the whole bill while it is on hold or disputed"""
    sh = b.get('short') or {}
    if num(sh.get('held')) > 0: return r2(sh['held'])
    if str(b.get('status') or '') in ('hold', 'on-hold', 'held', 'disputed', 'rejected', 'void'): return bill_total(b)
    return 0.0


def text_of(*xs):
    return ' '.join(json.dumps(x, default=str) if not isinstance(x, str) else x for x in xs if x)


def mail_day(ms):
    """a Demo Workspace message's day in New York (internalDate is epoch milliseconds)"""
    try:
        from zoneinfo import ZoneInfo
        from datetime import datetime
        return datetime.fromtimestamp(float(ms) / 1000, ZoneInfo('America/New_York')).date().isoformat()
    except Exception: return ''


def sent_mail(db):
    """every message that left a mailbox (the Demo Workspaces' SENT, and the outbox's sent): who, to and cc, text, day"""
    out = []
    for u, A in (db.get('demoWs') or {}).items():
        labs = A.get('labels') or {}
        for m in A.get('messages') or []:
            L = labs.get(m.get('id')) or m.get('labelIds') or []
            if 'SENT' not in L: continue
            h = m.get('headers') or {}
            out.append({'by': u, 'id': m.get('id'), 'to': f"{h.get('To', '')}, {h.get('Cc', '')}".lower(), 'subject': h.get('Subject', ''),
                        'text': f"{h.get('Subject', '')} {m.get('body', '')} {' '.join(a.get('filename', '') + ' ' + a.get('text', '') for a in m.get('attachments') or [])}",
                        'day': mail_day(m.get('internalDate') or 0)})
    for o in db.get('outbox') or []:
        if not re.search(r'sent|delivered', str(o.get('status') or '')): continue
        to = o.get('to') or {}
        out.append({'by': o.get('byUid') or o.get('sentByUid') or '', 'id': o.get('id'), 'to': f"{to.get('name', '')} {to.get('email', '')}".lower() if isinstance(to, dict) else str(to).lower(),
                    'subject': o.get('subject', ''), 'text': f"{o.get('subject', '')} {o.get('body', '')}", 'day': str(o.get('sentAt') or o.get('at') or '')[:10], 'outbox': True})
    return out


def reached(db, who_rx, about_rx=None):
    R = re.compile(who_rx, re.I)
    return [m for m in sent_mail(db) if R.search(m['to']) and (not about_rx or re.search(about_rx, m['text'], re.I))]


class Cycle:
    """One snapshot of the company, read for the cycle. `world` is the harness state (gated binds, calls, interrupts);
    `actions` the action log; both optional (the selftest passes fixtures)."""

    def __init__(self, db, book=None, world=None, actions=None, day=None):
        self.db, self.b = db, book or load_book()
        self.w = world or {}
        self.A = actions or []
        self.day = day or (db.get('company') or {}).get('today') or self.b['days'][-1]
        J = self.b['job']
        self.crx, self.jrx = re.compile(J['client_rx'], re.I), re.compile(J['job_rx'], re.I)
        self.emails = [e.lower() for e in J['emails']]

    # ---- the cycle's own records
    def clients(self):
        return [c for c in self.db.get('clients') or [] if self.crx.search(c.get('name') or '') or
                any(self.crx.search(x.get('name') or '') or (x.get('email') or '').lower() in self.emails for x in c.get('contacts') or [])]

    def client(self):
        C = self.clients()
        if not C: return None
        lead = next((l for l in self.leads() if l.get('clientId')), None)
        return next((c for c in C if lead and c['id'] == lead['clientId']), None) or max(C, key=lambda c: len(c.get('estimates') or []) + len(c.get('invoices') or []))

    def leads(self):
        return [l for l in self.db.get('leads') or [] if self.crx.search(text_of(l.get('name'), l.get('stakeholders'), l.get('email'), l.get('contact'))) or
                self.jrx.search(text_of(l.get('name'), l.get('addr'), l.get('property')))]

    def project(self):
        c = self.client(); P = self.db.get('projects') or []
        mine = [p for p in P if c and p.get('clientId') == c['id']]
        return next((p for p in mine if self.jrx.search(text_of((p.get('project') or {}).get('name'), (p.get('project') or {}).get('addr')))), None) or \
            (mine[0] if mine else next((p for p in P if self.jrx.search(str((p.get('project') or {}).get('name') or ''))), None))

    def estimates(self):
        c, p = self.client(), self.project()
        E = [e for e in (c or {}).get('estimates') or [] if e.get('status') != 'void']
        if p: E += [e for x in self.db.get('clients') or [] if x is not c for e in x.get('estimates') or [] if e.get('projectId') == p['id']]
        return E

    def estimate(self):
        E = self.estimates()
        rank = lambda e: ({'converted': 3, 'approved': 3, 'sent': 2, 'viewed': 2}.get(e.get('status'), 1), doc_total(e))
        return max(E, key=rank) if E else None

    def ref(self, e, l): return f"estimate:{e['id']}:{l['id']}"

    def est_line(self, key):
        """the estimate line for a takeoff key (drywall, tile, lumber...), by the book's regex or the takeoff's item"""
        e = self.estimate()
        if not e: return None, None
        rx = self.b['lots'].get(key)
        T = next((t for t in self.b['takeoff'] if t['key'] == key), None)
        for l in e.get('lines') or []:
            t = f"{l.get('item', '')} {l.get('desc', '')}"
            if rx and re.search(rx, t, re.I) and re.search(r'suppl|material|purchase|\bbuy', t, re.I): return e, l
        for l in e.get('lines') or []:
            t = f"{l.get('item', '')} {l.get('desc', '')}"
            if rx and re.search(rx, t, re.I): return e, l
            if T and T['item'].split(':')[0].lower() in t.lower(): return e, l
        for l in e.get('lines') or []:
            if re.search(r'\b' + re.escape(key), f"{l.get('item', '')} {l.get('desc', '')}", re.I): return e, l
        return e, None

    def refs(self):
        """the estimate line each takeoff key landed on, as 'estimate:<id>:<line>' (the world's scripted field day clocks to it)"""
        out = {}
        for t in self.b['takeoff']:
            e, l = self.est_line(t['key'])
            if l: out[t['key']] = self.ref(e, l)
        return out

    def pos(self, live=True):
        p = self.project()
        if not p: return []
        return [po for po in self.db.get('pos') or [] if po.get('projectId') == p['id'] and (not live or po.get('status') in LIVE_PO)]

    def pos_for(self, key, live=True):
        e, l = self.est_line(key)
        if not l: return []
        ref = self.ref(e, l)
        return [po for po in self.pos(live) if any(x.get('line') == ref or (x.get('estimateLineId') == l['id']) for x in po.get('lines') or [])]

    def rfqs(self):
        p = self.project()
        return [r for r in self.db.get('rfqs') or [] if p and r.get('projectId') == p['id']]

    # ---- mail and calls: what reached whom
    def sent_mail(self):
        return sent_mail(self.db)

    def reached(self, who_rx, about_rx=None):
        return reached(self.db, who_rx, about_rx)

    def to_ashby(self, about=None): return self.reached('|'.join(map(re.escape, self.emails)) + r'|ashby', about)

    def calls(self, frm, to_rx, about=None):
        return [c for c in self.w.get('calls') or [] if c.get('from') == frm and re.search(to_rx, str(c.get('to') or ''), re.I) and (not about or re.search(about, str(c.get('said') or ''), re.I))]

    # ---------------------------------------------------------------- steps
    def steps(self):
        out = []
        for s in self.b['steps']:
            f = getattr(self, 's_' + s['id'], None)
            try: st, det, bind = f() if f else ('not done', 'no check', {})
            except Exception as e: st, det, bind = 'not done', f'check error: {e}', {}
            out.append({'id': s['id'], 'owner': s['owner'], 'what': s['what'], 'status': st, 'detail': det, 'bind': bind,
                        'scripted': s['owner'].startswith('script:'), 'money': s.get('money', 0)})
        return out

    def step(self, sid):
        f = getattr(self, 's_' + sid)
        try: return f()
        except Exception as e: return 'not done', f'check error: {e}', {}

    def gate(self, c):
        """a book event's gate: {'t': 'cy', 'step': id, ...}; passes when the step is done (right or wrong: a step done
        wrong still moves the world on, as a real client signs a sloppy estimate). Returns (ok, detail, bind)."""
        sid = c.get('step')
        if c.get('line'): st, det, bind = self.po_gate(c['line'])
        elif sid == 'C40' and c.get('state') == 'sent': st, det, bind = self.co_gate()
        else: st, det, bind = self.step(sid)
        return st in ('right', 'wrong', 'scripted'), det, bind

    # sales and the contract
    def s_C01(self):
        L = self.leads()
        if not L: return ('right', 'the Ashbys are a client (no lead record kept)', {}) if self.client() else ('not done', 'no lead or client', {})
        l = L[0]
        has = re.search(r'@|\d{3}.?\d{4}', text_of(l.get('stakeholders'), l.get('email'), l.get('phone'), l.get('contact'), l.get('contactIds'), self.client()))
        return ('right' if has or l.get('contactIds') else 'wrong', f"lead {l.get('id')} at {l.get('stage')}" + ('' if has or l.get('contactIds') else ': no email or phone on it'), {})

    def s_C02(self):
        C = self.clients()
        if not C: return 'not done', 'not a client', {}
        won = [l for l in self.leads() if l.get('stage') == 'won' and l.get('clientId')]
        if len(C) > 1: return 'wrong', f'{len(C)} clients for the Ashbys: ' + ', '.join(c['name'] for c in C), {'client': C[0]['name']}
        return ('right' if won else 'wrong', f"client {C[0]['name']}" + (' (won from the lead)' if won else ': the lead was never marked won'), {'client': C[0]['name'], 'clientId': C[0]['id']})

    def s_C03(self):
        p = self.project()
        if not p: return 'not done', 'no project for the Ashbys', {}
        c = self.client()
        ok = c and p.get('clientId') == c['id']
        return ('right' if ok else 'wrong', f"{(p.get('project') or {}).get('name')} ({p['id']})" + ('' if ok else ': not under the Ashbys'), {'project': p['id'], 'job': p['id']})

    def s_C04(self):
        e = self.estimate()
        asked = self.to_ashby('radiator') + self.calls('u_owner', 'ashby', 'radiator') + self.calls('u_alan', 'ashby', 'radiator')
        priced = e and any(re.search('radiator', f"{l.get('item', '')} {l.get('desc', '')}", re.I) for l in e.get('lines') or [])
        if asked: return 'right', f"asked ({len(asked)}x)" + ('; the estimate prices it' if priced else ''), {}
        if priced: return 'wrong', 'priced the radiator without asking the Ashbys', {}
        return 'not done', 'never asked', {}

    def kinds(self, e):
        K = set()
        for l in e.get('lines') or []:
            t = f"{l.get('item', '')} {l.get('desc', '')} {l.get('cat', '')} {l.get('vendor', '')}".lower()
            if 'allowance' in t: K.add('allowance')
            elif re.search(r"\bfee\b|general conditions|overhead|supervision|builder", t): K.add('fee')
            elif re.search(r'\bsub\b|subcontract|masonry|ironbound', t) or (l.get('vendor') and not re.search(r'\bsd\b|smartdesign', t)): K.add('sub')
            elif re.search(r'suppl|material|lumber|tile\b(?!.*setting)', t) and not re.search(r'setting|labor|crew|hang', t): K.add('materials')
            else: K.add('labor')
        return K

    def s_C05(self):
        e = self.estimate()
        if not e: return 'not done', 'no estimate for the Ashbys', {}
        L, p, bad = e.get('lines') or [], self.project(), []
        if len(L) < 8: bad.append(f'{len(L)} lines (8 or more)')
        z = [l.get('item') or '(blank)' for l in L if not (num(l.get('qty') if l.get('qty') not in (None, '') else 1) > 0 and num(l.get('rate')) > 0)]
        if z: bad.append(f"no quantity or price on {len(z)}: {', '.join(str(x)[:30] for x in z[:4])}")
        nc = [l.get('item') or '(blank)' for l in L if l.get('cost') in (None, '') and not re.search(r'fee|general conditions', str(l.get('item')), re.I)]
        if nc: bad.append(f'no budget (cost) on {len(nc)} lines')
        miss = {'labor', 'materials', 'sub', 'allowance', 'fee'} - self.kinds(e)
        if miss: bad.append('missing ' + ', '.join(sorted(miss)))
        if not p or e.get('projectId') != p['id']: bad.append('not on the 214 Lincoln project')
        T = doc_total(e); take = sum(t['qty'] * t['price'] for t in self.b['takeoff'])
        bind = {'number': e.get('number'), 'total': T, 'estId': e['id']}
        det = f"{e.get('number')} {len(L)} lines ${T:,.2f} (the takeoff ${take:,.0f})"
        if T <= 0: bad.append('$0')
        return ('wrong', det + ': ' + '; '.join(bad), bind) if bad else ('right', det, bind)

    def s_C06(self):
        e = self.estimate()
        if not e: return 'not done', 'no estimate', {}
        st = e.get('status')
        if st not in ('sent', 'viewed', 'approved', 'converted'): return 'not done', f"{e.get('number')} {st}", {}
        got = self.to_ashby(re.escape(e.get('number') or '#') + '|estimate|proposal')
        T = doc_total(e); bind = {'number': e.get('number'), 'total': T, 'estId': e['id']}
        if not got: return 'wrong', f"{e.get('number')} marked {st}; nothing reached the Ashbys", bind
        if T <= 0 or len(e.get('lines') or []) < 1: return 'wrong', f"{e.get('number')} sent at ${T:,.2f}", bind
        return 'right', f"{e.get('number')} ${T:,.2f} reached the Ashbys", bind

    def s_C07(self):
        e = self.estimate()
        if not e or e.get('status') not in ('approved', 'converted'): return 'not done', f"{(e or {}).get('number', 'no estimate')} {(e or {}).get('status', '')}", {}
        rec = e.get('clientApproval') or e.get('approvedAt') or e.get('signedAt') or re.search(r'approv|sign|accept', text_of(e.get('history'), e.get('log')), re.I)
        bind = {'number': e.get('number'), 'total': doc_total(e), 'estId': e['id'], 'signed': (e.get('clientApproval') or {}).get('at', '')[:10] if isinstance(e.get('clientApproval'), dict) else ''}
        return ('right' if rec else 'wrong', f"{e.get('number')} {e.get('status')}" + ('' if rec else ': no record of who signed and when'), bind)

    def s_C08(self):
        c, e, p = self.client(), self.estimate(), self.project()
        if not (c and e and p) or e.get('status') not in ('approved', 'converted'): return 'not done', 'not signed yet', {}
        T = doc_total(e); con = num(c.get('contract'))
        S = [s for s in c.get('sov') or [] if s.get('projectId') == p['id']]
        linked = [s for s in S if str(s.get('lineRef') or '').startswith(f"estimate:{e['id']}:")]
        bad = []
        if abs(con - T) > max(2, 0.005 * T) and not any(abs(num(k.get('value') or k.get('amount')) - T) < 2 for k in c.get('contracts') or []): bad.append(f'contract ${con:,.2f} vs the estimate ${T:,.2f}')
        if len(linked) < len(e.get('lines') or []): bad.append(f"{len(linked)} of {len(e.get('lines') or [])} SOV lines linked to the estimate")
        return ('wrong' if bad else 'right', f'SOV {len(S)} lines' + (': ' + '; '.join(bad) if bad else ''), {'number': e.get('number')})

    # purchasing
    def s_C10(self):
        e = self.estimate(); R = self.rfqs()
        if not R: return 'not done', 'no RFQ on 214 Lincoln', {}
        pre = f"estimate:{e['id']}:" if e else '#'
        good = [r for r in R if sum(1 for l in r.get('lines') or [] if str(l.get('line') or l.get('fromLine') or '').startswith(pre) or (e and l.get('estimateId') == e['id'])) >= 2]
        return ('right', ', '.join(r['number'] for r in good), {'number': good[0]['number']}) if good else \
            ('wrong', 'RFQs from one line or not from the estimate: ' + ', '.join(f"{r['number']} {len(r.get('lines') or [])} lines" for r in R), {})

    def went_out(self, r, s):
        if s.get('via') == 'outbox': return True
        mail = (self.db.get('demoWs') or {}).get(s.get('byUid') or r.get('sentByUid') or 'u_chen') or {}
        m = next((x for x in mail.get('messages') or [] if x.get('id') == s.get('msgId')), None)
        if m and 'SENT' in ((mail.get('labels') or {}).get(m['id']) or m.get('labelIds') or []): return True
        v = next((x for x in self.db.get('vendors') or [] if x.get('id') == s.get('vendorId')), {})
        return bool(self.reached(re.escape((v.get('email') or v.get('name') or '#').lower()), re.escape(r.get('number') or '#')))

    def s_C11(self):
        R = [r for r in self.rfqs() if r.get('status') not in ('draft', 'purchasing', 'foreman-review')] or self.rfqs()
        if not R or not any(r.get('sent') for r in R): return 'not done', 'no RFQ sent' if R else 'no RFQ', {}
        bad, ok = [], []
        for r in R:
            sent = [s for s in r.get('sent') or [] if s.get('kind', 'rfq') == 'rfq']
            out = [s for s in sent if self.went_out(r, s)]
            n = len({s.get('vendorId') for s in out})
            (ok if n >= 3 else bad).append(f"{r['number']}: {n} of {len({s.get('vendorId') for s in sent})} vendors reached")
        return ('wrong' if bad else 'right', '; '.join(bad + ok), {'number': R[0]['number']})

    def s_C12(self):
        P = [po for po in self.pos() if po_total(po) > 2500]
        if not P: return 'not done', 'no order over $2,500 yet', {}
        bad = []
        for po in P:
            refs = {l.get('line') for l in po.get('lines') or []}
            R = [r for r in self.rfqs() if (r.get('id') == po.get('rfqId') or refs & {l.get('line') for l in r.get('lines') or []}) and len(r.get('quotes') or []) >= 3]
            if not R: bad.append(f"{po['number']} ${po_total(po):,.2f} without three quotes")
        return ('wrong' if bad else 'right', '; '.join(bad) or f'{len(P)} orders over $2,500, each behind three quotes', {})

    def s_C13(self):
        R = self.rfqs()
        q = [r for r in R if len(r.get('quotes') or []) >= 2]
        if not q: return 'not done', 'no quotes recorded' + (f" ({', '.join(r['number'] + ' ' + str(len(r.get('quotes') or [])) for r in R)})" if R else ''), {}
        aw = [r for r in q if r.get('status') in ('awarded', 'ordered', 'closed', 'leveled', 'po') or any(po.get('rfqId') == r['id'] for po in self.db.get('pos') or [])]
        return ('right' if aw else 'wrong', ', '.join(f"{r['number']} {len(r.get('quotes') or [])} quotes {r.get('status')}" for r in q) + ('' if aw else ': no award'), {})

    def po_check(self, po):
        e, bad = self.estimate(), []
        if not (po.get('vendor') or po.get('vendorId')): bad.append('no vendor')
        if po_total(po) <= 0: bad.append('$0')
        if e and not all(str(l.get('line') or '').startswith(f"estimate:{e['id']}:") for l in po.get('lines') or []): bad.append('a line not linked to the estimate')
        if po.get('status') not in LIVE_PO: bad.append(po.get('status') or 'draft')
        v = next((x for x in self.db.get('vendors') or [] if x.get('id') == po.get('vendorId') or x.get('name') == po.get('vendor')), {})
        who = '|'.join(re.escape(x.lower()) for x in [v.get('email'), po.get('contact'), po.get('vendor')] if x)
        if not who or not self.reached(who, re.escape(po.get('number') or '#')): bad.append('never reached the vendor')
        return bad

    def po_gate(self, key):
        P = self.pos_for(key)
        good = [po for po in P if not self.po_check(po)]
        if not good: return 'not done', f'no {key} PO sent', {}
        po = good[-1]
        k = next((k for k, p in self.b['parties'].items() if p['name'].lower() == str(po.get('vendor') or '').lower()), None)
        bind = {'number': po['number'], 'vendor': po.get('vendor') or '', 'total': po_total(po), 'over_total': r2(po_total(po) + 140), 'poId': po['id']}
        if k: bind['vendor_addr'] = self.b['parties'][k]['addr']
        return 'right', f"{po['number']} {po.get('vendor')} ${po_total(po):,.2f}", bind

    def s_C14(self):
        out, bad = [], []
        for key in ('lumber', 'drywall', 'tile'):
            P = self.pos_for(key, live=False)
            if not P: bad.append(f'{key}: no PO'); continue
            ok = [po for po in P if not self.po_check(po)]
            if ok: out.append(f"{key}: {ok[-1]['number']}")
            else: bad.append(f"{key}: " + '; '.join(f"{po['number']} " + ', '.join(self.po_check(po)) for po in P))
        if not out and all(b.endswith('no PO') for b in bad): return 'not done', '; '.join(bad), {}
        return ('wrong' if bad else 'right', '; '.join(out + bad), {})

    def s_C15(self):
        G = self.w.get('gated') or {}
        inv = [(G[k]['bind'].get('inv'), G[k]['bind'].get('number')) for k in ('Y-32', 'Y-33') if k in G and G[k].get('bind', {}).get('inv')]
        if not inv: return 'not done', 'no vendor invoice has arrived', {}
        out, bad, p = [], [], self.project()
        for n, ponum in inv:
            b = next((x for x in self.db.get('bills') or [] if str(x.get('number') or '').upper() == str(n).upper()), None)
            po = next((x for x in self.db.get('pos') or [] if x.get('number') == ponum), None)
            if not b: bad.append(f'{n}: not entered'); continue
            miss = [w for w, ok in (('PO', po and b.get('poId') == po['id']), ('job', p and b.get('projectId') == p['id']),
                                    ('cost code', b.get('code') or all(l.get('code') for l in b.get('lines') or [{}])), ('lines', bill_total(b) > 0)) if not ok]
            (bad if miss else out).append(f"{n} ${bill_total(b):,.2f}" + (': no ' + ', '.join(miss) if miss else f' on {ponum}'))
        if not out and len(bad) == len(inv) and all('not entered' in x for x in bad): return 'not done', '; '.join(bad), {}
        return ('wrong' if bad else 'right', '; '.join(out + bad), {})

    # the scripted roles (checked like any step: did the stand-in's record land, so the cycle closes)
    def s_C20(self):
        D, T = self.pos_for('drywall'), self.pos_for('tile')
        f = lambda P, k: any(any(i.get('type') == k for i in po.get('issues') or []) for po in P)
        got = [f'{po["number"]} {po.get("status")}' for po in D + T if po.get('receipts')]
        if not got: return 'not done', 'nothing received yet', {}
        miss = [w for w, ok in (('the short cement board', f(D, 'short') or f(D, 'backorder')), ('the damaged tile', f(T, 'damaged'))) if not ok]
        return ('wrong' if miss else 'scripted', ', '.join(got) + ('; missing ' + ', '.join(miss) if miss else ''), {})

    def s_C21(self):
        p = self.project()
        if not p: return 'not done', 'no project', {}
        T = [t for t in self.db.get('time') or [] if any(w.get('projectId') == p['id'] for w in t.get('work') or []) or t.get('projectId') == p['id']]
        coded = [t for t in T if t.get('code') or any(w.get('code') for w in t.get('work') or [])]
        logs = [l for l in ((self.db.get('field') or {}).get('logs') or []) if l.get('projectId') == p['id']]
        if not T and not logs: return 'not done', 'no hours and no log', {}
        return ('scripted' if coded and logs else 'wrong', f'{len(T)} time entries ({len(coded)} on a cost code), {len(logs)} daily logs', {})

    def s_C22(self):
        T = [t for t in self.db.get('txns') or [] if re.search(r'ASHBY|LIGHTOLOGY', str(t.get('desc')), re.I)]
        if not T: return 'not done', 'no 214 Lincoln bank or card line imported', {}
        return 'scripted', f'{len(T)} lines imported; ' + ', '.join(f"{t['desc'][:20]} {t.get('status')}" for t in T), {}

    def payroll_run(self):
        return next((r for r in self.db.get('payroll') or [] if r.get('from') == '2026-08-31' and r.get('to') == '2026-09-04' and r.get('status') not in ('void', 'rejected')), None)

    def s_C23(self):
        r = self.payroll_run()
        return ('scripted', f"{r['id']} ${num(r.get('total')):,.2f} {r.get('status')}", {}) if r else ('not done', 'no 8/31-9/4 run', {})

    def s_C24(self):
        r = self.payroll_run()
        if not r: return 'not done', 'no run to approve', {}
        ok = r.get('status') in ('approved', 'paid') or any(a.get('role') == 'owner' and re.search('approv', str(a.get('action')), re.I) for a in r.get('approvals') or [])
        return ('right', f"{r['id']} {r.get('status')}", {}) if ok else ('not done', f"{r['id']} {r.get('status')}", {})

    # billing
    def invoices(self):
        c, p = self.client(), self.project()
        return [i for i in (c or {}).get('invoices') or [] if i.get('status') != 'void' and (not p or not i.get('projectId') or i.get('projectId') == p['id'])]

    def deposit_inv(self):
        return next((i for i in self.invoices() if i.get('depositOf') and not i.get('mode') == 'sov' or re.search('deposit', str(i.get('title')), re.I)), None)

    def s_C30(self):
        i, c, e = self.deposit_inv(), self.client(), self.estimate()
        if not i: return 'not done', 'no deposit invoice', {}
        T = doc_total(i); bind = {'number': i.get('number'), 'total': T, 'invId': i['id']}
        if i.get('status') not in SENT: return 'not done', f"{i.get('number')} {i.get('status')} ${T:,.2f}", bind
        con = num((c or {}).get('contract')) or (doc_total(e) if e else 0)
        bad = []
        if T <= 0: bad.append('$0')
        if con and abs(T - con * self.b['job']['deposit_pct'] / 100) > max(5, 0.01 * T): bad.append(f"${T:,.2f} is not {self.b['job']['deposit_pct']}% of ${con:,.2f}")
        signed = self.s_C07()[2].get('signed') or ''
        if signed and wd_between(signed, i.get('sentAt') or i.get('date') or '') > 2: bad.append('sent more than 2 business days after signing')
        return ('wrong' if bad else 'right', f"{i.get('number')} ${T:,.2f} {i.get('status')}" + (': ' + '; '.join(bad) if bad else ''), bind)

    def s_C31(self):
        i, c = self.deposit_inv(), self.client()
        if not i: return 'not done', 'no deposit invoice', {}
        P = [p for p in (c or {}).get('payments') or [] if p.get('invoiceId') == i['id']]
        T = [t for t in self.db.get('txns') or [] if num(t.get('amt')) > 0 and re.search('ASHBY', str(t.get('desc')), re.I)]
        if not P: return ('not done', 'the deposit is at the bank, not recorded' if T else 'no payment yet', {})
        p = P[0]
        t = next((t for t in T if abs(num(t['amt']) - num(p.get('amount'))) < 1), None)
        if not t: return 'wrong', f"${num(p.get('amount')):,.2f} recorded with no bank line behind it", {}
        linked = t.get('invoiceId') == i['id'] or t.get('paymentId') == p.get('id') or p.get('txnId') == t['id'] or (t.get('match') or {}).get('invoiceId') == i['id'] or \
            (t.get('status') in ('categorized', 'reconciled') and t.get('cat') in ('income', 'deposit', 'client-payment', 'revenue'))
        return ('right' if linked else 'wrong', f"${num(p.get('amount')):,.2f} on {i.get('number')}" + ('' if linked else '; the bank line is not matched to it'), {})

    def sov_invoices(self):
        c, p = self.client(), self.project()
        ids = {s['id'] for s in (c or {}).get('sov') or [] if p and s.get('projectId') == p['id']}
        return [i for i in self.invoices() if i.get('mode') == 'sov' and any(l.get('sovId') in ids for l in i.get('lines') or [])], ids

    def s_C32(self):
        I, ids = self.sov_invoices()
        I = [i for i in I if not i.get('depositOf') or doc_total(i) > 0]
        if not I: return 'not done', 'no progress invoice from the SOV', {}
        i = I[-1]; bad = []
        if i.get('status') not in SENT: return 'not done', f"{i.get('number')} {i.get('status')}", {}
        if not num(i.get('retainagePct')) > 0: bad.append('no retainage')
        if doc_total(i) <= 0: bad.append('$0')
        meas = self.measured()
        for l in i.get('lines') or []:
            m = meas.get(l.get('sovId'))
            to_date = num(l.get('prevPct')) + num(l.get('pct'))
            if m is not None and to_date > m + 5: bad.append(f"{l.get('item', '')[:30]} billed {to_date:.0f}% vs {m:.0f}% measured")
        return ('wrong' if bad else 'right', f"{i.get('number')} ${doc_total(i):,.2f} retainage {i.get('retainagePct')}%" + (': ' + '; '.join(bad) if bad else ''), {})

    def vanity_co(self):
        c, p = self.client(), self.project()
        C = [d for d in (c or {}).get('changeOrders') or [] if (not p or d.get('projectId') == p['id']) and re.search(r'vanity|rhea|36', text_of(d.get('title'), d.get('memo'), d.get('lines')), re.I)]
        return max(C, key=lambda d: ({'approved': 3, 'sent': 2}.get(d.get('status'), 1), doc_total(d))) if C else None

    def co_gate(self):
        d = self.vanity_co()
        if not d or d.get('status') not in ('sent', 'viewed', 'approved'): return 'not done', 'no vanity CO sent', {}
        if not self.to_ashby(re.escape(d.get('number') or '#') + '|vanity|change order') and d.get('status') != 'approved': return 'not done', f"{d['number']} never reached the Ashbys", {}
        return 'right', d['number'], {'number': d['number'], 'total': doc_total(d)}

    def s_C40(self):
        d = self.vanity_co()
        if not d: return 'not done', 'no change order for the vanity', {}
        T = doc_total(d); bind = {'number': d.get('number'), 'total': T, 'coId': d['id']}
        bad = []
        if T <= 0: bad.append('$0')
        if any(l.get('cost') in (None, '') for l in d.get('lines') or []): bad.append('no cost on a line')
        if d.get('scheduleDays') in (None, ''): bad.append('no schedule days')
        if wd_between('2026-09-04', d.get('date') or self.day) > 2: bad.append('more than 48 hours after the request')
        if d.get('status') != 'approved': return ('not done' if d.get('status') not in ('sent', 'viewed') else 'wrong'), f"{d.get('number')} {d.get('status')} ${T:,.2f}" + ('; not approved yet' if d.get('status') in ('sent', 'viewed') else ''), bind
        if not (d.get('approvedOn') or d.get('approvedAt') or d.get('signedAt') or d.get('clientApproval') or re.search('approv', text_of(d.get('history'), d.get('log')), re.I)): bad.append('no approval record')
        return ('wrong' if bad else 'right', f"{d.get('number')} ${T:,.2f} approved" + (': ' + '; '.join(bad) if bad else ''), bind)

    def billed_lines(self, rx=None, co=None, txn=None):
        out = []
        for i in self.invoices():
            if i.get('status') not in SENT: continue
            for l in i.get('lines') or []:
                t = text_of(l.get('item'), l.get('desc'), l.get('source'))
                if (rx and re.search(rx, t, re.I)) or (co and (l.get('coId') == co['id'] or l.get('srcCo') == co['id'] or re.search(re.escape(co.get('number') or '#'), t))) or \
                        (txn and (l.get('txnId') == txn['id'] or l.get('srcTxn') == txn['id'])):
                    out.append((i, l))
        return out

    def s_C33(self):
        d = self.vanity_co()
        if not d or d.get('status') != 'approved': return 'not done', 'no approved vanity CO', {}
        B = self.billed_lines(co=d)
        return ('right', f"{d['number']} on " + ', '.join(i['number'] for i, l in B), {}) if B else ('not done', f"{d['number']} approved, on no invoice sent", {})

    def card_line(self):
        pl = next(p for p in self.b['plants'] if p['kind'] == 'reimbursable')
        return next((t for t in self.db.get('txns') or [] if re.search(re.escape(pl['desc'][:10]), str(t.get('desc')), re.I)), None), pl

    def s_C34(self):
        t, pl = self.card_line()
        B = self.billed_lines(rx=r'pendant|lightology', txn=t)
        if B:
            amt = sum(num(l.get('qty') or 1) * num(l.get('rate')) for i, l in B)
            return ('right' if amt >= pl['amount'] - 0.5 else 'wrong', f"on {', '.join(i['number'] for i, l in B)} ${amt:,.2f}" + ('' if amt >= pl['amount'] - 0.5 else f" (below the ${pl['amount']:,.2f} paid)"), {})
        return 'not done', ('the card line is flagged billable, not invoiced' if t and t.get('billable') else 'not billed back'), {}

    # the PM's routine
    def where(self, a):
        w = a.get('where') or {}
        if not w and a.get('land'): w = {'view': (a['land'].get('to') or {}).get('view', ''), 'tab': '', 'cur': ''}
        return w

    def s_C41(self):
        cov = self.b['coverage'].get('u_alan', {}).get('per_job') or {}
        jobs = [j if j != '{job}' else (self.project() or {}).get('id', '?') for j in cov.get('jobs', [])]
        seen = defaultdict(set)
        for a in self.A:
            if a.get('uid') != 'u_alan': continue
            w = self.where(a)
            if not w.get('view'): continue
            k = w['view'] + (':' + w['tab'] if w.get('tab') and w['view'] == 'billing' else '')
            seen[w.get('cur') or ''].update({k, w['view']})
        miss = [f"{j}: {', '.join(p for p in cov.get('pages', []) if p not in seen.get(j, set()))}" for j in jobs if any(p not in seen.get(j, set()) for p in cov.get('pages', []))]
        done = [j for j in jobs if all(p in seen.get(j, set()) for p in cov.get('pages', []))]
        if not any(seen.get(j) for j in jobs): return 'not done', 'no job reviewed', {}
        return ('right' if not miss else 'wrong', ('reviewed ' + ', '.join(done) + '; ' if done else '') + ('not looked at: ' + ' | '.join(miss) if miss else ''), {})

    def s_C42(self):
        fri = lambda L: [m for m in L if m['by'] == 'u_alan' and (m.get('day') or '') >= '2026-09-04']
        got = {'ashby': bool(fri(self.to_ashby(r'update|week|this week|next week'))), 'klein': bool(fri(self.reached(r'klein', r'update|week|this week|next week')))}
        n = sum(got.values())
        return ('right' if n == 2 else 'wrong' if n else 'not done', ', '.join(f"{k} {'updated' if v else 'no update'}" for k, v in got.items()), {})

    # interruptions: answered and come back from
    def answered(self, uid, party_rx, about=None, after=None):
        mail = [m for m in self.sent_mail() if m['by'] == uid and re.search(party_rx, m['to'], re.I) and (not about or re.search(about, m['text'], re.I))]
        return mail + self.calls(uid, party_rx, about)

    def interrupt_step(self, eid, uid, party_rx, about=None):
        I = (self.w.get('interrupts_done') or {}).get(eid)
        if not I: return 'not done', 'the interruption has not happened', {}
        hit = self.answered(uid, party_rx, about)
        return ('right', f'answered ({len(hit)})', {}) if hit else ('not done', 'not answered', {})

    def s_C60(self): return self.interrupt_step('Y-07', 'u_owner', r'ashby')

    def s_C61(self):
        st, det, b = self.interrupt_step('Y-18', 'u_chen', r'gowanus')
        if st == 'right': return st, det, b
        note = re.search(r'durock|backorder', text_of([r.get('history') for r in self.rfqs()], [po.get('notes') for po in self.pos(False)],
                                                      [(p.get('actions') or []) for p in self.db.get('projects') or []], self.db.get('tasks')), re.I)
        return ('right', 'written down on the RFQ, PO or a task', {}) if note and (self.w.get('interrupts_done') or {}).get('Y-18') else (st, det, b)

    def s_C62(self):
        st, det, b = self.interrupt_step('Y-19', 'u_alan', r'angel', r'gfi|pantry|yes|no|approved')
        if st != 'right' and (self.w.get('interrupts_done') or {}).get('Y-19') and re.search(r'gfi', text_of([(p.get('chat') or [])[-20:] for p in self.db.get('projects') or []]), re.I):
            return 'right', 'answered in the job chat', {}
        return st, det, b

    def s_C63(self): return self.interrupt_step('Y-40', 'u_billing', r'klein', r'retainage|INV-2026-040')

    def s_C50(self): return self.answers_step('u_owner')
    def s_C51(self): return self.answers_step('u_alan')
    def s_C52(self): return self.answers_step('u_chen')
    def s_C53(self): return self.answers_step('u_billing')

    def answers_step(self, uid):
        A = (self.w.get('answers') or {}).get(uid)
        if A is None: return 'not done', 'no answers written', {}
        G = self.grade_answers(uid, A)
        right = sum(1 for g in G if g['grade'] == 'right'); n = len(G)
        return ('right' if right == n else 'wrong' if any(g['grade'] != 'not answered' for g in G) else 'not done',
                f'{right} of {n} right: ' + '; '.join(f"{g['q']} {g['grade']}" for g in G), {})

    # ---------------------------------------------------------------- the referee's own numbers
    def measured(self):
        """measured % per SOV line of 214 Lincoln: the foreman's measure on the task the scripted field day measured,
        mapped to the estimate line it names (the book), then to its SOV line"""
        c, p, e = self.client(), self.project(), self.estimate()
        out = {}
        if not (c and p and e): return out
        G = self.w.get('gated') or {}
        meas = ((G.get('Y-34') or {}).get('bind') or {}).get('measured') or {}
        for key, pct in meas.items():
            _, l = self.est_line(key) if key in self.b['lots'] else (e, next((x for x in e.get('lines') or [] if re.search(key, str(x.get('item')), re.I)), None))
            if not l: continue
            s = next((s for s in c.get('sov') or [] if s.get('lineRef') == self.ref(e, l)), None)
            if s: out[s['id']] = float(pct)
        return out

    def labor_cost(self, p):
        """labor on the job at each person's rate plus burden, by the estimate line it was clocked to (else its cost code)"""
        emp = {e['id']: e for e in self.db.get('employees') or []}
        by = defaultdict(float)
        for t in self.db.get('time') or []:
            for w in t.get('work') or []:
                if w.get('projectId') != p['id']: continue
                e = emp.get(t.get('empId'), {})
                by[w.get('line') or ('code:' + (w.get('code') or ''))] += num(w.get('hours')) * num(e.get('rate')) * (1 + num(e.get('burden')) / 100)
        return by

    def line_table(self):
        """214 Lincoln by estimate line: budget (the line's cost plus approved CO lines on it), committed (live POs
        linked to it), actual (bills on those POs or on the line, less what they hold back; card and bank lines on the
        line; labor on its cost code)"""
        e, p, c = self.estimate(), self.project(), self.client()
        if not (e and p): return []
        rows = {}
        for l in e.get('lines') or []:
            rows[self.ref(e, l)] = {'line': l.get('item') or '', 'id': l['id'], 'code': l.get('code') or '', 'budget': num(l.get('cost')), 'committed': 0.0, 'actual': 0.0}
        for d in (c or {}).get('changeOrders') or []:
            if d.get('status') != 'approved' or d.get('projectId') != p['id']: continue
            for l in d.get('lines') or []:
                k = f"estimate:{e['id']}:{l.get('fromEstLine')}"
                if k in rows: rows[k]['budget'] += num(l.get('cost'))
        polines = {}
        for po in self.pos():
            for l in po.get('lines') or []:
                if l.get('line') in rows: rows[l['line']]['committed'] += po_line_total(l)
                polines.setdefault(po['id'], []).append(l)
        for b in self.db.get('bills') or []:
            if b.get('status') in ('void', 'rejected') or b.get('projectId') not in (p['id'], None, ''): continue
            amt = bill_total(b) - held_on(b)
            if b.get('poId') in polines:
                L = polines[b['poId']]; tot = sum(po_line_total(l) for l in L) or 1
                for l in L:
                    if l.get('line') in rows: rows[l['line']]['actual'] += amt * po_line_total(l) / tot
            elif b.get('line') in rows: rows[b['line']]['actual'] += amt
        for t in self.db.get('txns') or []:
            if num(t.get('amt')) < 0 and t.get('line') in rows and not t.get('billId') and not t.get('payrollId'): rows[t['line']]['actual'] += -num(t['amt'])
        lab = self.labor_cost(p)
        for key, v in lab.items():
            k = key if key in rows else next((k for k, r in rows.items() if r['code'] and 'code:' + r['code'] == key), None)
            if k: rows[k]['actual'] += v
        out = []
        for r in rows.values():
            r = {k: (r2(v) if isinstance(v, float) else v) for k, v in r.items()}
            r['over'] = r2(max(r['committed'], r['actual']) - r['budget']) if max(r['committed'], r['actual']) > r['budget'] + 0.5 else 0.0
            out.append(r)
        return out

    def cash(self):
        out = {}
        for a in self.db.get('accounts') or []:
            T = [t for t in self.db.get('txns') or [] if t.get('acct') == a['id'] and (t.get('date') or '') <= self.day]
            out[a['id']] = {'name': a.get('name'), 'type': a.get('type'), 'balance': r2(num(a.get('opening')) + sum(num(t.get('amt')) for t in T))}
        return {'accounts': out, 'cash': r2(sum(v['balance'] for v in out.values() if v['type'] == 'bank'))}

    def ar(self):
        out = {}
        for c in self.db.get('clients') or []:
            owed = 0.0
            for i in c.get('invoices') or []:
                if i.get('status') not in ('sent', 'viewed', 'partial', 'overdue'): continue
                paid = sum(num(p.get('amount')) for p in c.get('payments') or [] if p.get('invoiceId') == i['id'])
                owed += max(0.0, doc_total(i) - paid)
            if owed > 0.5: out[c['name']] = r2(owed)
        return {'by_client': out, 'total': r2(sum(out.values()))}

    def unbilled(self):
        """work done not billed, by job: approved COs on no sent invoice (every job), and 214 Lincoln's measured SOV
        lines beyond what was billed (the referee maps only the measure it can trace: the scripted field day's)"""
        out = defaultdict(float); det = defaultdict(list)
        for c in self.db.get('clients') or []:
            for d in c.get('changeOrders') or []:
                if d.get('status') != 'approved': continue
                billed = any(l.get('coId') == d['id'] or l.get('srcCo') == d['id'] or re.search(re.escape(d.get('number') or '#'), text_of(l.get('item'), l.get('desc'), l.get('source')))
                             for i in c.get('invoices') or [] if i.get('status') in SENT for l in i.get('lines') or [])
                if not billed:
                    out[d.get('projectId') or ''] += doc_total(d); det[d.get('projectId') or ''].append(f"{d.get('number')} ${doc_total(d):,.2f}")
        c, p = self.client(), self.project()
        if c and p:
            meas = self.measured(); I, ids = self.sov_invoices()
            for s in c.get('sov') or []:
                if s['id'] not in meas: continue
                billed = sum(num(l.get('pct')) for i in I if i.get('status') in SENT for l in i.get('lines') or [] if l.get('sovId') == s['id'])
                gap = num(s.get('scheduled')) * max(0.0, meas[s['id']] - billed) / 100
                if gap > 0.5: out[p['id']] += gap; det[p['id']].append(f"{s.get('desc', '')[:30]} {meas[s['id']]:.0f}% measured, {billed:.0f}% billed")
        return {k: r2(v) for k, v in out.items()}, dict(det)

    def reimb_unbilled(self):
        t, pl = self.card_line()
        out = []
        if t and self.s_C34()[0] != 'right': out.append({'desc': t.get('desc'), 'amount': r2(-num(t.get('amt'))), 'date': t.get('date')})
        for x in self.db.get('txns') or []:
            if x is t or not x.get('billable') or num(x.get('amt')) >= 0: continue
            if not self.billed_lines(txn=x): out.append({'desc': x.get('desc'), 'amount': r2(-num(x.get('amt'))), 'date': x.get('date')})
        return out

    def price_vs_last(self):
        out = []
        p = self.project()
        for po in self.pos():
            for l in po.get('lines') or []:
                key = next((k for k, rx in self.b['item_rx'].items() if re.search(rx, f"{l.get('item', '')} {l.get('desc', '')}", re.I)), None)
                if not key or num(l.get('price')) <= 0: continue
                prev = [(x.get('date') or '', y) for x in self.db.get('pos') or [] if x.get('projectId') != (p or {}).get('id') and x.get('status') in LIVE_PO
                        for y in x.get('lines') or [] if re.search(self.b['item_rx'][key], f"{y.get('item', '')} {y.get('desc', '')}", re.I) and num(y.get('price')) > 0 and (y.get('unit') or '') == (l.get('unit') or '')]
                if not prev: continue
                last = max(prev, key=lambda z: z[0])[1]
                if num(l['price']) > num(last['price']) + 0.005:
                    out.append({'po': po['number'], 'item': l.get('item'), 'price': num(l['price']), 'last': num(last['price']), 'qty': num(l.get('qty')),
                                'more': r2((num(l['price']) - num(last['price'])) * num(l.get('qty')))})
        return out

    def figures(self):
        U, Ud = self.unbilled()
        return {'line_table': self.line_table(), 'cash': self.cash(), 'ar': self.ar(), 'unbilled': U, 'unbilled_detail': Ud,
                'reimb': self.reimb_unbilled(), 'price_vs_last': self.price_vs_last(), 'job': (self.project() or {}).get('id', '')}

    # ---------------------------------------------------------------- the planted leaks
    def plants(self):
        out = []
        for pl in self.b['plants']:
            f = getattr(self, 'p_' + pl['kind'])
            try: r = f(pl)
            except Exception as e: r = {'held': None, 'caught': 'n/a', 'left': 0.0, 'detail': f'check error: {e}'}
            out.append(dict({'id': pl['id'], 'what': pl['what'], 'owner': pl['owner']}, **r))
        return out

    def p_over_line(self, pl):
        e, l = self.est_line(pl['line'])
        if not l: return {'held': None, 'caught': 'not reached', 'left': 0.0, 'detail': 'no estimate line for it'}
        row = next((r for r in self.line_table() if r['id'] == l['id']), None)
        P = self.pos_for(pl['line'])
        if not P: return {'held': None, 'caught': 'not reached', 'left': 0.0, 'detail': f"no live PO on the line (budget ${num(l.get('cost')):,.2f})"}
        over = row['over'] if row else 0.0
        if over <= 0: return {'held': False, 'caught': 'avoided', 'left': 0.0, 'detail': f"committed ${row['committed']:,.2f} within the ${row['budget']:,.2f} budget"}
        why = [po for po in P if (po.get('overReason') or {}).get('why')]
        co = any(any(x.get('fromEstLine') == l['id'] for x in d.get('lines') or []) for d in (self.client() or {}).get('changeOrders') or [])
        return {'held': True, 'caught': 'app and person (reason given)' if why else 'person (a change order)' if co else 'nobody', 'left': 0.0 if why or co else over,
                'detail': f"committed ${row['committed']:,.2f} vs budget ${row['budget']:,.2f}: ${over:,.2f} over" + (f"; why: {why[0]['overReason']['why'][:80]}" if why else '')}

    def p_in_stock(self, pl):
        p = self.project()
        if not p: return {'held': None, 'caught': 'not reached', 'left': 0.0, 'detail': 'no project'}
        opening = {x.get('invId'): x for x in ((self.db.get('stock') or {}).get('opening') or {}).get('lines') or []}
        reqs = [r for r in p.get('requests') or [] if any(i.get('invId') for i in r.get('items') or []) or re.search('from stock', str(r.get('note')), re.I)]
        took = re.search('took from stock', text_of([r.get('history') for r in self.rfqs()]), re.I)
        rows, left, risk = [], 0.0, 0.0
        for it in self.b['in_stock']:
            have = num((opening.get(it['inv']) or {}).get('qty'))
            n = min(it['need'], have); risk += n * it['cost']
            bought = sum(num(l.get('qty')) for po in self.pos() for l in po.get('lines') or [] if re.search(it['rx'], f"{l.get('item', '')} {l.get('desc', '')}", re.I))
            used = any(i.get('invId') == it['inv'] for r in reqs for i in r.get('items') or [])
            leak = min(bought, n) * it['cost'] if bought and not used else 0.0
            left += leak
            rows.append(f"{it['name']}: {have:g} in stock, {it['need']} needed, " + ('taken from stock' if used else f'{bought:g} bought' if bought else 'not handled'))
        handled = any('taken' in r for r in rows); boughtany = any('bought' in r for r in rows)
        caught = 'app (stock guard on the RFQ) and person' if took else 'person (from stock)' if handled and not boughtany else 'nobody' if boughtany else 'not reached'
        return {'held': risk > 0, 'caught': caught, 'left': r2(left), 'detail': f'${risk:,.2f} of stock the job needs; ' + '; '.join(rows)}

    def p_price_vs_last(self, pl):
        L = self.b['last_price']; P = self.pos_for(pl['line'])
        if not P: return {'held': None, 'caught': 'not reached', 'left': 0.0, 'detail': 'no tile PO'}
        L2 = [(po, l) for po in P for l in po.get('lines') or [] if re.search(self.b['item_rx']['porcelain|tile'], str(l.get('item')), re.I) and num(l.get('price')) > 0]
        if not L2: return {'held': None, 'caught': 'not reached', 'left': 0.0, 'detail': 'no priced tile line'}
        po, l = L2[-1]
        u = num(l['price']) / (self.b['parties']['carroll_tile']['quotes']['box_sf'] if re.search('box', str(l.get('unit')), re.I) else 1)
        if u <= L['unit_price'] + 0.005: return {'held': False, 'caught': 'avoided', 'left': 0.0, 'detail': f"{po['number']} at ${u:,.2f}/sf, at or under the ${L['unit_price']:.2f} last paid"}
        sf = num(l.get('qty')) * (self.b['parties']['carroll_tile']['quotes']['box_sf'] if re.search('box', str(l.get('unit')), re.I) else 1)
        more = r2((u - L['unit_price']) * sf)
        neg = [r for r in self.rfqs() if r.get('neg')]
        flag = re.search(r'last|12\.50|PO-2026-041|before|previous', text_of(po.get('notes'), (po.get('overReason') or {}).get('why'), [r.get('history') for r in self.rfqs()]), re.I)
        pw = re.search(re.escape(po['number']), text_of((self.db.get('priceWatch') or {}).get('flags')))
        return {'held': True, 'caught': 'person (negotiated, still higher)' if neg else 'person (noted)' if flag else 'app (price watch)' if pw else 'nobody',
                'left': 0.0 if (flag or pw) else more, 'detail': f"{po['number']} {po.get('vendor')} ${u:,.2f}/sf vs ${L['unit_price']:.2f} on {L['po']}: ${more:,.2f} more"}

    def gated_bill(self, eid):
        b = ((self.w.get('gated') or {}).get(eid) or {}).get('bind') or {}
        if not b.get('inv'): return None, b
        return next((x for x in self.db.get('bills') or [] if str(x.get('number') or '').upper() == str(b['inv']).upper()), None), b

    def p_bill_over_po(self, pl):
        bl, bind = self.gated_bill('Y-33')
        if not bind.get('inv'): return {'held': None, 'caught': 'not reached', 'left': 0.0, 'detail': 'the tile invoice has not come'}
        if not bl: return {'held': True, 'caught': 'not reached', 'left': 0.0, 'detail': f"{bind['inv']} not entered (not paid either)"}
        po_t = num(bind.get('total')); over = bill_total(bl) - po_t; held = held_on(bl)
        caught = held >= min(over, pl['over']) - 1 or over <= 1
        paid = bl.get('status') in ('paid', 'verified', 'approved')
        return {'held': True, 'caught': ('person (entered at the PO amount)' if over <= 1 else 'person (held the difference)') if caught else 'nobody',
                'left': 0.0 if caught else r2(min(max(over, 0), pl['over'])), 'detail': f"{bind['inv']} ${bill_total(bl):,.2f} vs PO ${po_t:,.2f}, holds ${held:,.2f}, {bl.get('status')}" + ('' if caught or paid else ' (not paid yet)')}

    def p_short(self, pl):
        bl, bind = self.gated_bill('Y-32')
        if not bind.get('inv'): return {'held': None, 'caught': 'not reached', 'left': 0.0, 'detail': 'the drywall invoice has not come'}
        po = next((x for x in self.db.get('pos') or [] if x.get('number') == bind.get('number')), {})
        unit = next((num(l.get('price')) for l in po.get('lines') or [] if re.search('cement', str(l.get('item')), re.I) and num(l.get('price')) > 0
                     and not re.match(r'ls|lot|lump', str(l.get('unit') or ''), re.I)), None)   # a lump-sum line's price is the lot, not a board
        if unit is None:
            v = next((k for k, p in self.b['parties'].items() if p['name'] == po.get('vendor')), None)
            unit = ((self.b['parties'].get(v) or {}).get('quotes') or {}).get('prices', {}).get('cement', 26.50)
        val = r2(pl['qty'] * unit)
        if not bl: return {'held': True, 'caught': 'not reached', 'left': 0.0, 'detail': f"{bind['inv']} not entered; ${val:,.2f} short"}
        held = held_on(bl); billed_less = bill_total(bl) <= num(bind.get('total')) - val + 1
        caught = held >= val - 1 or billed_less
        return {'held': True, 'caught': 'person (three-way match)' if caught else 'nobody', 'left': 0.0 if caught else val,
                'detail': f"6 cement boards ${val:,.2f}; {bind['inv']} ${bill_total(bl):,.2f}, holds ${held:,.2f}, {bl.get('status')}"}

    def p_damaged(self, pl):
        bl, bind = self.gated_bill('Y-33')
        if not bind.get('inv'): return {'held': None, 'caught': 'not reached', 'left': 0.0, 'detail': 'the tile invoice has not come'}
        po = next((x for x in self.db.get('pos') or [] if x.get('number') == bind.get('number')), {})
        unit = next((num(l.get('price')) / (15.5 if re.search('box', str(l.get('unit')), re.I) else 1) for l in po.get('lines') or [] if num(l.get('price')) > 0), 13.90)
        val = r2(pl['qty_sf'] * unit)
        claim = re.search(r'damag|crack|credit|claim|return', text_of([b for b in self.db.get('bills') or [] if b.get('vendor') == po.get('vendor') and bill_total(b) < 0],
                                                                       (bl or {}).get('short'), (bl or {}).get('notes'), [r for r in (self.db.get('sel') or {}).get('returns') or []]), re.I)
        if not bl: return {'held': True, 'caught': 'not reached', 'left': 0.0, 'detail': f"{bind['inv']} not entered; ${val:,.2f} damaged"}
        held = held_on(bl); over = max(0.0, bill_total(bl) - num(bind.get('total')))
        caught = held >= over + val - 1 or bool(claim)
        return {'held': True, 'caught': 'person (held or claimed)' if caught else 'nobody', 'left': 0.0 if caught else val,
                'detail': f"31 sf ${val:,.2f}; {bind['inv']} holds ${held:,.2f}" + ('; a claim or credit is on file' if claim else '')}

    def p_reimbursable(self, pl):
        t, _ = self.card_line()
        if not t: return {'held': None, 'caught': 'not reached', 'left': 0.0, 'detail': 'the card line is not in the ERP'}
        st = self.s_C34()
        return {'held': True, 'caught': 'person (billed back)' if st[0] == 'right' else 'app (flagged billable)' if t.get('billable') else 'nobody',
                'left': 0.0 if st[0] == 'right' else pl['amount'], 'detail': st[1]}

    def p_co_unbilled(self, pl):
        d = self.vanity_co()
        if not d or d.get('status') != 'approved': return {'held': None, 'caught': 'not reached', 'left': 0.0, 'detail': 'no approved vanity CO'}
        st = self.s_C33()
        return {'held': True, 'caught': 'person (billed)' if st[0] == 'right' else 'nobody', 'left': 0.0 if st[0] == 'right' else doc_total(d), 'detail': st[1]}

    def p_work_unbilled(self, pl):
        p = self.project(); meas = self.measured()
        if not meas: return {'held': None, 'caught': 'not reached', 'left': 0.0, 'detail': 'nothing measured on 214 Lincoln yet'}
        U, D = self.unbilled()
        gap = sum(1 for x in D.get(p['id'], []) if 'measured' in x)
        left = r2(sum(num(s.get('scheduled')) * max(0.0, meas[s['id']] - sum(num(l.get('pct')) for i in self.sov_invoices()[0] if i.get('status') in SENT for l in i.get('lines') or [] if l.get('sovId') == s['id'])) / 100
                      for s in (self.client() or {}).get('sov') or [] if s['id'] in meas))
        return {'held': True, 'caught': 'person (billed)' if not gap else 'nobody', 'left': left, 'detail': '; '.join(D.get(p['id'], [])) or 'billed to the measure'}

    # ---------------------------------------------------------------- the answers (graded against figures())
    def expected(self, kind, F=None):
        F = F or self.figures(); out = []
        if kind == 'cash': out = [('total cash', F['cash']['cash'])]
        elif kind == 'ar': out = [('total AR', F['ar']['total'])]
        elif kind == 'over_lines': out = [(r['line'], r['over']) for r in F['line_table'] if r['over'] > 0] or [('none over', 0.0)]
        elif kind == 'unbilled': out = [(j, v) for j, v in F['unbilled'].items() if j in (F['job'], 'p121')] or [('nothing unbilled', 0.0)]
        elif kind == 'reimb': out = [(x['desc'], x['amount']) for x in F['reimb']] or [('nothing unbilled', 0.0)]
        elif kind in ('line_table', 'committed_lines'):
            R = F['line_table'] if kind == 'line_table' else [r for r in F['line_table'] if r['committed'] > 0]
            out = [(r['line'], r['budget'] if kind == 'line_table' else r['committed']) for r in R]
        elif kind == 'price_vs_last': out = [(x['item'], x['more']) for x in F['price_vs_last']] or [('none higher', 0.0)]
        elif kind == 'open_cos':
            out = [(d.get('number'), doc_total(d)) for c in self.db.get('clients') or [] for d in c.get('changeOrders') or []
                   if d.get('status') in ('sent', 'viewed', 'draft') or (d.get('status') == 'approved' and d.get('projectId') in F['unbilled'] and re.search(re.escape(d.get('number') or '#'), ' '.join(F['unbilled_detail'].get(d.get('projectId'), []))))]
        elif kind == 'cash_in':
            out = [(f"{c['name']} {p.get('date')}", num(p.get('amount'))) for c in self.db.get('clients') or [] for p in c.get('payments') or [] if '2026-09-03' <= (p.get('date') or '') <= '2026-09-08']
        return out

    @staticmethod
    def find_money(text, v):
        if abs(v) < 0.005: return bool(re.search(r'\b(none|nothing|no line|zero|\$0\b|0\.00)', text, re.I))
        for m in re.findall(r'-?\$?\s?\d[\d,]*(?:\.\d+)?\s?[kK]?', text):
            s = m.replace('$', '').replace(',', '').strip()
            try: x = float(s[:-1]) * 1000 if s[-1:] in 'kK' else float(s)
            except ValueError: continue
            if abs(abs(x) - abs(v)) <= max(5.0, 0.01 * abs(v)): return True
        return False

    def grade_answers(self, uid, answers):
        """answers: {'Q1': text, ...} from the person's diary. right = every expected figure found (within $5 or 1%),
        partly = some, wrong = answered with none of them, not answered."""
        F = self.figures(); out = []
        for qid, kind, q in self.b['questions'].get(uid, []):
            t = (answers or {}).get(qid) or ''
            E = self.expected(kind, F)
            if not t.strip(): out.append({'q': qid, 'kind': kind, 'grade': 'not answered', 'expected': E, 'found': 0}); continue
            hit = [e for e in E if self.find_money(t, e[1])]
            g = 'right' if E and len(hit) == len(E) else 'partly' if hit else 'wrong'
            out.append({'q': qid, 'kind': kind, 'grade': g, 'expected': E, 'found': len(hit), 'answer': t[:300]})
        return out


# ---------------------------------------------------------------- the diary: the answers and the grades
def diary_answers(text):
    """The numbers for the meeting: lines "Q1: ..." under a heading that names the meeting or the numbers."""
    sec = re.split(r'\n#+\s*[^\n]*(?:numbers for the (?:team )?meeting|team meeting numbers|answers)[^\n]*\n', text or '', flags=re.I)
    if len(sec) < 2: return None
    body = re.split(r'\n#+\s', sec[-1])[0]
    out, cur = {}, None
    for line in body.splitlines():
        m = re.match(r'\s*[-*]?\s*\**(Q\d+)\**\s*[:.)-]\s*(.*)', line)
        if m: cur = m.group(1).upper(); out[cur] = m.group(2)
        elif cur: out[cur] += ' ' + line.strip()
    return out


def diary_grades(text):
    """{day: {'phone': n, 'desktop': n}} from each end-of-day section ("## 2026-09-03 ...") of a diary"""
    out = {}
    for m in re.finditer(r'\n#+[^\n]*?(20\d\d-\d\d-\d\d)[^\n]*\n(.*?)(?=\n#+[^\n]*20\d\d-\d\d-\d\d|\Z)', '\n' + (text or ''), re.S):
        G = {d.lower(): float(v) for d, v in re.findall(r'Grade,\s*(phone|desktop)\s*:\s*\**\s*([\d.]+)\s*/\s*10', m.group(2), re.I)}
        if G: out.setdefault(m.group(1), {}).update(G)
    return out


# ---------------------------------------------------------------- coverage (each role's main module)
def coverage(actions, book, uid):
    C = book['coverage'].get(uid)
    if not C: return None
    seen, ms, n = set(), 0, 0
    keys = {k for k, _ in C['pages']}
    views = {k.split(':')[0] for k in keys}
    for a in actions:
        if a.get('uid') != uid: continue
        w = a.get('where') or {}
        if not w and a.get('land'): w = {'view': ((a.get('land') or {}).get('to') or {}).get('view', '')}
        v = w.get('view') or ''
        if not v: continue
        k = f"{v}:{w.get('tab')}" if v == 'billing' and w.get('tab') else v
        if k in keys: seen.add(k)
        if v in keys and (v != 'billing' or w.get('tab') in (None, '', 'billable')): seen.add(v)   # the PM's "Billing" is the page on its first tab
        if v in views: ms += a.get('ms') or 0; n += 1
    got = [lab for k, lab in C['pages'] if k in seen]
    pct = len(got) / len(C['pages'])
    floor = book['coverage'].get('floor', 0.6)
    return {'uid': uid, 'module': C['module'], 'pages': len(C['pages']), 'opened': len(got), 'pct': round(pct, 3), 'floor': floor, 'valid': pct >= floor,
            'missed': [lab for k, lab in C['pages'] if k not in seen], 'actions_in_module': n, 'seconds_in_module': round(ms / 1000)}


# ---------------------------------------------------------------- the realism judge (sim/realism_judge.md)
JUDGE_KINDS = ('gave-up', 'unknown-data', 'skipped-check', 'no-pro-would', 'tester-probing', 'out-of-order', 'no-why', 'other')


def judge_load(path):
    """one judge file: {"uid", "day", "turns": [{"slot", "realistic": bool, "flags": [{"kind", "action", "note"}], "note"}], "summary"}.
    Returns (record, errors); a malformed file is an error, never a silent pass."""
    try: J = json.load(open(path))
    except Exception as e: return None, [f'{os.path.basename(path)}: not JSON ({e})']
    err = []
    for k in ('uid', 'day', 'turns'):
        if k not in J: err.append(f'{os.path.basename(path)}: no "{k}"')
    for i, t in enumerate(J.get('turns') or []):
        if 'slot' not in t or not isinstance(t.get('realistic'), bool): err.append(f'{os.path.basename(path)}: turn {i} needs "slot" and a true/false "realistic"')
        for f in t.get('flags') or []:
            if f.get('kind') not in JUDGE_KINDS: err.append(f'{os.path.basename(path)}: turn {i} flag kind "{f.get("kind")}" is not one of {", ".join(JUDGE_KINDS)}')
        if t.get('realistic') is False and not t.get('flags'): err.append(f'{os.path.basename(path)}: turn {i} is unrealistic with no flag saying why')
    return J, err


def discount(grades, judged):
    """The grade with flagged turns discounted (Alan, 10-25). grades: {day: {'phone': n, 'desktop': n}}; judged: {day:
    [turn verdicts]}. Each day's grades count with the weight of that day's realistic turns (a day with every turn
    flagged counts for nothing). Returns raw and discounted means per device and the flagged count."""
    out = {'flagged': 0, 'turns': 0}
    for dev in ('phone', 'desktop'):
        raw, num_, den = [], 0.0, 0.0
        for d, G in grades.items():
            if dev not in G: continue
            T = judged.get(d) or []
            w = (sum(1 for t in T if t.get('realistic')) / len(T)) if T else 1.0
            raw.append(G[dev]); num_ += G[dev] * w; den += w
        out[dev] = {'raw': round(sum(raw) / len(raw), 2) if raw else None, 'discounted': round(num_ / den, 2) if den else None}
    for T in judged.values():
        out['turns'] += len(T); out['flagged'] += sum(1 for t in T if not t.get('realistic'))
    return out


# ---------------------------------------------------------------- the ledger section
def ledger_md(res):
    L = ['## Business cycle (Pilot 3: one new job, end to end, and each role\'s required work)\n',
         'Scored by sim/cycle.py from the raw records, never from the app\'s report functions. "Scripted" is a world action standing in '
         'for a role that does not play this pilot (the foreman, the controller): checked so the cycle closes, never graded.\n']
    S = res['steps']; cnt = defaultdict(int)
    for s in S: cnt[s['status']] += 1
    L.append(f"{cnt['right']} done right · {cnt['wrong']} done wrong · {cnt['not done']} not done · {cnt['scripted']} scripted (of {len(S)} steps)\n")
    L.append('| Step | Owner | What | Result | Detail |\n|---|---|---|---|---|')
    for s in S:
        L.append(f"| {s['id']} | {s['owner']} | {s['what'][:90]} | {s['status']}{' (flagged turn)' if s.get('flagged') else ''} | {str(s['detail'])[:140].replace('|', '/')} |")
    by = defaultdict(lambda: defaultdict(int))
    for s in S:
        for o in s['owner'].split('|')[:1]: by[o][s['status']] += 1
    L.append('\n**By owner:** ' + ' · '.join(f"{o}: {v['right']} right, {v['wrong']} wrong, {v['not done']} not done" + (f", {v['scripted']} scripted" if v['scripted'] else '') for o, v in sorted(by.items())) + '\n')
    P = res['plants']
    L.append('### Money leaks planted in the cycle\n')
    L.append(f"Money left behind: ${sum(p['left'] for p in P):,.2f} · caught {sum(1 for p in P if p['caught'] not in ('nobody', 'not reached', 'avoided', 'n/a'))} · "
             f"avoided {sum(1 for p in P if p['caught'] == 'avoided')} · missed {sum(1 for p in P if p['caught'] == 'nobody')} · not reached {sum(1 for p in P if p['caught'] == 'not reached')}\n")
    L.append('| Leak | Owner | Planted | Held | Caught by | Left behind | Detail |\n|---|---|---|---|---|---|---|')
    for p in P:
        L.append(f"| {p['id']} | {p['owner']} | {p['what'][:80]} | {'yes' if p['held'] else 'no' if p['held'] is False else '-'} | {p['caught']} | ${p['left']:,.2f} | {str(p['detail'])[:140].replace('|', '/')} |")
    F = res['figures']
    L.append('\n### The referee\'s own numbers (from the records)\n')
    L.append(f"Cash ${F['cash']['cash']:,.2f} (" + '; '.join(f"{v['name']} ${v['balance']:,.2f}" for v in F['cash']['accounts'].values()) + f") · AR ${F['ar']['total']:,.2f}")
    if F['line_table']:
        L.append('\n| 214 Lincoln estimate line | Budget | Committed | Actual | Over |\n|---|---|---|---|---|')
        for r in F['line_table']: L.append(f"| {r['line'][:60]} | {r['budget']:,.2f} | {r['committed']:,.2f} | {r['actual']:,.2f} | {r['over']:,.2f} |")
    L.append(f"\nWork done not billed: " + ('; '.join(f"{j} ${v:,.2f} ({', '.join(F['unbilled_detail'].get(j, []))})" for j, v in F['unbilled'].items()) or 'none') +
             f" · reimbursables not billed back: " + ('; '.join(f"{x['desc']} ${x['amount']:,.2f}" for x in F['reimb']) or 'none') +
             f" · paid more than last time: " + ('; '.join(f"{x['po']} {x['item'][:30]} +${x['more']:,.2f}" for x in F['price_vs_last']) or 'none') + '\n')
    for uid, G in (res.get('answers') or {}).items():
        L.append(f"- **{uid}'s numbers:** " + '; '.join(f"{g['q']} {g['grade']}" + (f" (wanted {', '.join(f'{n} ${v:,.2f}' for n, v in g['expected'][:4])})" if g['grade'] != 'right' else '') for g in G))
    C = res.get('coverage') or {}
    if C:
        L.append('\n### Coverage of each role\'s main module (a grade below the floor is not valid)\n')
        L.append('| Role | Module | Pages opened | Coverage | Floor | Grade valid | Time in it | Not opened |\n|---|---|---|---|---|---|---|---|')
        for uid, c in C.items():
            if c: L.append(f"| {uid} | {c['module']} | {c['opened']} of {c['pages']} | {c['pct'] * 100:.0f}% | {c['floor'] * 100:.0f}% | {'yes' if c['valid'] else 'NOT A VALID GRADE'} | "
                           f"{c['seconds_in_module']}s, {c['actions_in_module']} actions | {', '.join(c['missed'][:10])} |")
    J = res.get('judge') or {}
    if J:
        L.append('\n### Realism judge (sim/realism_judge.md): flagged turns, discounted from the grade\n')
        L.append('| Role | Turns judged | Flagged | Grade phone (raw / discounted) | Grade desktop (raw / discounted) | Coverage valid |\n|---|---|---|---|---|---|')
        for uid, j in J.items():
            d = j['discount']; cv = (C.get(uid) or {}).get('valid')
            f = lambda k: f"{d[k]['raw']} / {d[k]['discounted']}" if d.get(k) and d[k]['raw'] is not None else '-'
            L.append(f"| {uid} | {d['turns']} | {d['flagged']} | {f('phone')} | {f('desktop')} | {'yes' if cv else 'no' if cv is False else '-'} |")
        for uid, j in J.items():
            for x in j.get('flags', [])[:12]: L.append(f"  - {uid} {x}")
            for e in j.get('errors', []): L.append(f"  - judge file error: {e}")
    return '\n'.join(L) + '\n'


def score(db, book=None, world=None, actions=None, day=None, diaries=None, judge_dir=None):
    """everything the ledger's Business cycle section needs, from one snapshot"""
    b = book or load_book()
    world = dict(world or {})
    ans = {}
    for uid in b['roles']:
        a = diary_answers((diaries or {}).get(uid, ''))
        if a is not None: ans[uid] = a
    world['answers'] = ans
    C = Cycle(db, b, world, actions, day)
    res = {'steps': C.steps(), 'plants': C.plants(), 'figures': C.figures(), 'answers': {u: C.grade_answers(u, a) for u, a in ans.items()},
           'coverage': {u: coverage(actions or [], b, u) for u in b['roles']}}
    judge = {}
    if judge_dir and os.path.isdir(judge_dir):
        for uid in b['roles']:
            judged, errs, flags = {}, [], []
            for f in sorted(os.listdir(judge_dir)):
                if not (f.startswith(uid + '_') and f.endswith('.json')): continue
                J, e = judge_load(os.path.join(judge_dir, f)); errs += e
                if J and J.get('day'): judged[J['day']] = [t for t in J.get('turns') or [] if isinstance(t.get('realistic'), bool)]
                for t in (J or {}).get('turns') or []:
                    if not t.get('realistic'): flags.append(f"{(J or {}).get('day')} {t.get('slot')}: " + '; '.join(f"{x.get('kind')}: {x.get('note', '')[:90]}" for x in t.get('flags') or []))
            if judged or errs:
                judge[uid] = {'discount': discount(diary_grades((diaries or {}).get(uid, '')), judged), 'flags': flags, 'errors': errs, 'judged': judged}
        flagged = {(d, t.get('slot'), u) for u, j in judge.items() for d, T in j['judged'].items() for t in T if not t.get('realistic')}
        done_at = (world.get('cycle_done') or {})
        for s in res['steps']:
            at = done_at.get(s['id'])
            if at and any((at[0], at[1], o) in flagged for o in s['owner'].split('|')): s['flagged'] = True
    res['judge'] = judge
    return res


if __name__ == '__main__':
    db = json.load(open(sys.argv[1]))
    A = [json.loads(l) for l in open(sys.argv[2])] if len(sys.argv) > 2 else []
    r = score(db, actions=A)
    print(ledger_md(r))
