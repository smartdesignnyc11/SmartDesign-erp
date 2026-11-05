"""The set-aside reads the work done (BACKLOG §1.36, 11-05; §1.35 item 1).

What was wrong. Reports > Cash said "Set aside: 214 Lincoln Place, $22,780 received less $0 earned" after $5,760 of
work was billed on the job ($1,440 of it taken from the deposit): earned was cost to cost only, and a job with no cost
posted yet earned nothing, so the whole deposit stayed set aside and Safe to Spend read low.

Now earned is the greater of the cost to date and the work done on the schedule of values as the progress grid reads
it (setAsideEarned over pgRows): a line measured in the field to its measure, a change order's line to what it billed.
Billing past the measure is never work done.

WORK  The Ashbys sign; their $22,780 deposit is paid with a bank line; the foreman measures demolition at 40% ($3,680 of
      $9,200); billing's New Invoice drafts the job's application and sends it. Reports > Cash, opened from the menu as
      the owner, reads "214 Lincoln Place, $22,780 received less $3,680 earned" and sets aside $19,100, on the desktop
      and the 390px phone, with no sideways scroll. A change order line billed in full ($2,080) adds to it: $5,760
      earned, $17,020 set aside. Safe to Spend's set-aside is the same figure (one number).
AHEAD Billing types 10% on framing with nothing measured and sends it: earned does not move (billing ahead of the
      measure never releases client money).
SEED  121 State Street still reads $169,750 received less $122,626 earned, $47,124.21 set aside (its measured work,
      $68,283, is under its cost to date).
"""
import asyncio, re, sys
from harness import *

LINES = [('Demolition and protection', 9200), ('Framing', 11400), ('Plumbing rough and finish', 12600), ('Electrical rough and finish', 10800),
         ('Drywall and cement board', 6400), ('Tile: floors and walls', 9800), ('Cabinetry install', 7200), ('Doors and trim', 5600),
         ('Paint', 4800), ('Plumbing fixture allowance', 6500), ('Lighting allowance', 3820), ('Supervision and fee', 3000)]

SETUP = r"""async (arg) => { const sl = ms => new Promise(r => setTimeout(r, ms));
  const c = blankClient('Wren & Julian Ashby'); c.propertyAddr = '214 Lincoln Place, Brooklyn';
  c.contacts = [{ id: uid('ct'), name: 'Wren Ashby', email: 'wren.ashby@example.com', role: 'Owner', primary: true }]; DB.clients.push(c);
  const p = blankProject('214 Lincoln Place', '214 Lincoln Place, Brooklyn', today(), ''); p.clientId = c.id; DB.projects.push(p);
  const e = newDoc(c, 'estimate', { template: 'construction', fields: { title: '214 Lincoln Place — renovation', projectId: p.id } });
  e.lines = arg.map(([item, amt]) => ({ id: uid('l'), item, desc: '', qty: 1, unit: 'ls', rate: amt, cost: Math.round(amt * 0.7), taxable: false }));
  e.status = 'sent'; e.sentAt = today(); e.sentTo = 'wren.ashby@example.com'; docMark(e); save();
  // the owner records the signed copy (lkapprove, as billing_path_test's owner does)
  view = 'clients'; clientOpen = c.id; clientTab = 'fin'; finTab = 'estimates'; docOpen = { kind: 'estimate', id: e.id }; render(); await sl(300);
  let b = document.querySelector(`#doc-${e.id} [data-docact="lkapprove"]`);
  if (!(b && b.getClientRects().length)) { const s = [...document.querySelectorAll(`#doc-${e.id} summary`)].find(x => /More/.test(x.innerText)); s && s.click(); await sl(200); b = document.querySelector(`#doc-${e.id} [data-docact="lkapprove"]`); }
  b.click(); await sl(300); const w = document.querySelector('#mbm [data-f="why"]'); w.value = 'Signed copy by email from Wren Ashby'; w.dispatchEvent(new Event('input', { bubbles: true }));
  document.querySelector('#mbm #mbm-ok').click(); await sl(500); docOpen = null; clientOpen = null;
  // the deposit, invoiced and paid, its payment matched to the bank's line (J8 done)
  const DEP = 22780, inv = newDoc(c, 'invoice', { mode: 'items' });
  Object.assign(inv, { template: 'construction', projectId: p.id, depositOf: e.id, isDeposit: true, title: 'Deposit — 25% of the contract', terms: 'Due on receipt', retainagePct: 0, status: 'sent', sentAt: today() });
  inv.due = inv.date; inv.lines = [{ id: uid('l'), item: 'Deposit on the contract', qty: 1, unit: 'ls', rate: DEP, taxable: false }]; docMark(inv);
  const t = txnStamp({ id: uid('t'), acct: 'ac1', date: today(), amt: DEP, desc: 'DEPOSIT ASHBY WREN 214 LINCOLN', cat: 'income', source: 'ofx', status: 'categorized' }, 'stmt:ashby', 'dep1');
  DB.txns.push(t); c.payments.push({ id: uid('py'), invoiceId: inv.id, date: today(), amount: DEP, method: 'ACH', ref: 'deposit', txnId: t.id }); inv.status = 'paid';
  // the foreman measures demolition at 40% (the field's measure, on the job's schedule line for it)
  const sv = c.sov.find(v => /Demolition/.test(v.desc || ''));
  const task = { id: uid('t'), name: 'Demolition and protection', trade: 'demo', start: today(), end: iso(addDays(today(), 5)), owner: 'Angel', status: 'in-progress', type: 'task', deps: [], lineRef: sv.lineRef };
  (p.tasks = p.tasks || []).push(task); prgSet(p, task, { pct: 40, by: 'Angel', role: 'foreman', src: 'field', note: 'measured on site' }); save();
  return { cid: c.id, pid: p.id, eid: e.id }; }"""

READ = r"""() => { const t = (document.querySelector('.view.on') || {}).innerText || '';
  const m = t.match(/Set aside: 214 Lincoln Place[^\n]*/); return { line: m ? m[0] : '', all: (t.match(/Set aside: [^\n]*/g) || []), sw: document.scrollingElement.scrollWidth, w: innerWidth }; }"""


async def open_cash(pg, phone):
    """Reports > Cash from the menu, as the owner taps it"""
    if phone and not await pg.evaluate("() => !!document.querySelector('.rail.open')"):
        await pg.locator('#menu-btn:visible').first.click(); await pg.wait_for_timeout(300)
    h = pg.locator('#nav-groups [data-mnhead="reports"]').first
    if await h.get_attribute('aria-expanded') != 'true': await h.click(); await pg.wait_for_timeout(250)
    await pg.locator('#nav-groups [data-mngr="reports"] button').filter(has_text=re.compile(r'^\s*Cash\s*$')).first.click()
    await pg.wait_for_timeout(500)


async def main():
    c = Checks()
    async with async_playwright() as p:
        for phone in (False, True):
            dev = 'phone' if phone else 'desktop'
            b, pg, errs = await open_app(p, phone)
            await sign_in(pg, 'u_owner')
            seed = await pg.evaluate("() => setAsideRows().map(x => [shortName(x.p), x.collected, x.earned, x.amt])")
            c.ok(['121 State Street', 169750, 122625.79, 47124.21] in seed, f'SEED {dev}: 121 State still sets aside $47,124.21 ($169,750 received less $122,626 earned): {seed}')
            S = await pg.evaluate(SETUP, LINES)
            # billing drafts the job's application from the client's New Invoice and sends it
            await sign_in(pg, 'u_billing')
            r = await pg.evaluate("""async (S) => { const c = DB.clients.find(x => x.id === S.cid); slOpenClient(c.id); render(); await new Promise(r => setTimeout(r, 300));
              slNewInvoice(c); await new Promise(r => setTimeout(r, 400)); const a = (c.invoices || []).find(i => i.mode === 'sov' && i.status === 'draft');
              if (!a) return null; await docAction(c, a, 'send'); try { mbCloseModal(); } catch (e) {} return { n: a.number, status: a.status, gross: r2(docTotal(a).sub - docTotal(a).disc) }; }""", S)
            c.ok(r and r['status'] != 'draft' and abs(r['gross'] - 3680) < 0.01, f'WORK {dev}: New Invoice bills the measured demolition ($3,680) and it is sent: {r}')
            await sign_in(pg, 'u_owner')
            await open_cash(pg, phone)
            t = await pg.evaluate(READ)
            c.ok('$22,780 received less $3,680 earned' in t['line'], f"WORK {dev}: Reports > Cash reads 214 Lincoln's measured work as earned: {t['line']!r} (all: {t['all']})")
            c.ok(t['sw'] <= t['w'], f"WORK {dev}: Reports > Cash does not scroll sideways ({t['sw']} > {t['w']})")
            one = await pg.evaluate("(pid) => { const R = setAsideRows().find(x => x.p.id === pid); const B = companyBalance(); return [R && R.amt, (B.setAsideBy || []).filter(x => x.pid === pid || x.name === '214 Lincoln Place').map(x => x.amt)[0], safeToSpend().setAside, setAside().total]; }", S['pid'])
            c.ok(one[0] == 19100 and one[1] == 19100 and abs(one[2] - one[3]) < 0.01, f'WORK {dev}: one set-aside: $19,100 on the job, the same in the balance and Safe to Spend: {one}')
            # a change order line billed in full is work done on its own evidence
            co = await pg.evaluate("""(S) => { const c = DB.clients.find(x => x.id === S.cid), p = DB.projects.find(x => x.id === S.pid);
              const sv = { id: uid('sv'), desc: 'CO-2026-901 Sister the parlor joists', source: 'CO-2026-901', scheduled: 2080, projectId: p.id, order: 99 }; c.sov.push(sv);
              const inv = newDoc(c, 'invoice', { mode: 'sov' }); inv.projectId = p.id; inv.lines = [{ id: uid('l'), sovId: sv.id, item: sv.desc, pct: 100, prevPct: 0, qty: 1, rate: 2080 }]; inv.status = 'sent'; inv.sentAt = today(); docMark(inv); save();
              const R = setAsideRows().find(x => x.p.id === p.id); return [R.earned, R.amt]; }""", S)
            c.ok(co == [5760, 17020], f'WORK {dev}: the change order billed in full adds its $2,080: $5,760 earned, $17,020 set aside: {co}')
            # billing ahead of the measure releases nothing
            ah = await pg.evaluate("""(S) => { const c = DB.clients.find(x => x.id === S.cid), p = DB.projects.find(x => x.id === S.pid), sv = c.sov.find(v => /Framing/.test(v.desc || ''));
              const inv = newDoc(c, 'invoice', { mode: 'sov' }); inv.projectId = p.id; inv.lines = [{ id: uid('l'), sovId: sv.id, item: sv.desc, pct: 10, prevPct: 0, qty: 1, rate: sv.scheduled }]; inv.status = 'sent'; inv.sentAt = today(); docMark(inv); save();
              const R = setAsideRows().find(x => x.p.id === p.id); return [R.earned, R.amt]; }""", S)
            c.ok(ah == [5760, 17020], f'AHEAD {dev}: 10% of framing billed with nothing measured does not move earned: {ah}')
            c.ok(not errs, f'{dev}: no page errors: {errs[:3]}')
            await b.close()
    return c.done()

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
