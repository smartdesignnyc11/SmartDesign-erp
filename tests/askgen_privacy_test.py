"""Ask never shows a client anything that is not theirs, and never shows a field role money (BACKLOG 1.3, S1).

A client once asked "when was my last payment" and got every payment the firm holds, other clients' included.
Privacy is enforced in one place, eqRows (the query layer under erpQuery and every Ask reader). This suite
proves it from the outside: each client asks 30 varied questions, and every answer (headline, note, rows,
"I ran" line) is searched for anything that belongs to someone else:
  - another client's name, or the name of a job that is not theirs;
  - another client's document numbers (invoices, estimates, change orders) and amounts;
  - the firm's own books: vendor bills, purchase orders, cash, receivables, payables, backlog.
Then the foreman, crew and driver ask money questions and no dollar figure may come back.

  python3 askgen_privacy_test.py        # prints ALL PASS (n checks) or each leak
"""
import asyncio, re
from harness import *

CLIENT_QS = [
    # payments and invoices
    'when was my last payment', 'how much have we paid so far', 'what do I owe', 'which invoices are open',
    'list every invoice', 'what payments came in this month',
    # photos, decisions, schedule
    'show me the photos', 'how many photos were shared this week', 'what decisions are waiting on me',
    'what is waiting on me', 'when will my job finish', 'how far along are we',
    # documents
    'what change orders do I have', 'show me every estimate', 'which documents do you have',
    # people and vendors
    'who is on the crew', 'who has not submitted their hours', 'what is on order from Tino', 'which vendor do you owe the most',
    # amounts and "everyone"
    'what is our AR', 'payments by client', 'how much did everyone pay in August', 'which client owes the most',
    'how much cash does the firm have', 'how much did you spend at Home Depot',
    # other clients and other jobs by name
    'how much did the Riveras pay', 'how much does the Jessop family owe', 'when will 206 Lenox finish',
    'what is late on 140 Prospect', 'photos on 45 Cranberry',
]
FIELD_QS = [
    'how much cash do we have', 'how much did we spend at Home Depot in August', 'what do we owe vendors',
    'what is our AR', 'how much is the contract on 121 State', 'what did we pay M Rodriguez', 'what is ready to bill',
    'what is the EAC on 121 State Street', 'gross margin YTD', 'how much is PO-2026-047',
]

SETUP = r"""
(uid) => {
  signIn(uid); const u = currentUser(), cid = u.clientId;
  const mineJobs = DB.projects.filter(p => p.clientId === cid);
  const short = p => String(p.project.name).replace(/ —.*$/, '');
  const others = DB.clients.filter(c => c.id !== cid);
  const ownAmts = new Set(DB.clients.filter(c => c.id === cid).flatMap(c => [...(c.invoices || []), ...(c.estimates || []), ...(c.changeOrders || [])].map(d => money(docTotal(d).total)).concat((c.payments || []).map(p => money(p.amount)))));
  const amts = others.flatMap(c => [...(c.invoices || []), ...(c.estimates || []), ...(c.changeOrders || [])].map(d => money(docTotal(d).total)).concat((c.payments || []).map(p => money(p.amount)))).filter(a => a !== '$0' && !ownAmts.has(a));
  const B = briefFacts().B;
  const firm = [B.cash, B.arOut, B.backlog, B.apAccrued, B.payrollAccrued].map(money).filter(a => a !== '$0' && !ownAmts.has(a));
  const words = others.map(c => String(c.name).split(/[^A-Za-z]+/).filter(t => t.length >= 4 && !/^(family|the|llc|lenox)$/i.test(t)).pop()).filter(Boolean)
    .concat(DB.projects.filter(p => p.clientId !== cid).map(short))
    .concat(others.flatMap(c => [...(c.invoices || []), ...(c.estimates || []), ...(c.changeOrders || [])].map(d => d.number)))
    .concat((DB.bills || []).map(b => b.number)).concat((DB.pos || []).map(p => p.number)).concat((DB.vendors || []).map(v => v.name).filter(n => n.length >= 5));
  return { me: u.name, jobs: mineJobs.map(short), words: [...new Set(words)], amts: [...new Set(amts.concat(firm))] };
}
"""
ASK = r"""
async ([uid, q]) => {
  try { Object.values(DB.asst || {}).forEach(A => { if (A && typeof A === 'object') { A.thread = []; delete A.ctx; } }); } catch (e) {}
  signIn(uid); view = 'home'; render();
  let a = await Promise.resolve(paAsk(q)); a = a || {};
  return [a.headline, a.note, a.interp].concat(a.work || []).map(x => typeof x === 'string' ? x : JSON.stringify(x || '')).join(' \n ');
}
"""

async def main():
    C = Checks()
    async with async_playwright() as p:
        b, pg, errs = await open_app(p)
        for uid in ('u_klein', 'u_cambri'):
            S = await pg.evaluate(SETUP, uid)
            for q in CLIENT_QS:
                t = await pg.evaluate(ASK, [uid, q])
                low = t.lower()
                leak = [w for w in S['words'] if re.search(r'(?<![\w-])' + re.escape(w.lower()) + r'(?![\w-])', low)]
                leak += [a for a in S['amts'] if re.search(re.escape(a) + r'(?![\d,])', t)]
                C.ok(not leak, f'{uid} "{q}" shows what is not theirs: {leak[:5]} | {t[:160]!r}')
        for uid in ('u_angel', 'u_alberto', 'u_alex'):
            for q in FIELD_QS:
                t = await pg.evaluate(ASK, [uid, q])
                C.ok(not re.search(r'\$\s?\d', t), f'{uid} "{q}" shows money: {t[:160]!r}')
        C.ok(not errs, f'page errors: {errs[:3]}')
        await b.close()
    raise SystemExit(C.done())

asyncio.run(main())
