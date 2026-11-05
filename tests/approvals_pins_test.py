"""Approvals pins (BACKLOG §1.36, CoS 11-05): two things the danger sweep fixed that no check held.

ww       WW-2026-118 (Window Works, $33,500 paid from the Amex before approval, $3,800 over PO-2026-044) is on the
         Owner's Today, Approvals tab, and the button that leads it is Dispute Difference, the safe step (blue on the
         phone's card and the desk's side panel). The read fails when the bill is missing from the tab, not only when
         its button is wrong (chain_test step 7 passed over a missing bill).
topay    A bill paid before approval never reaches To Pay: before the Owner decides it and after (Dispute Difference
         through the sheet), its status is never "approved", it is not on Ready to Pay (ydReadyToPay), not on Bills and
         Payroll's To Pay chip, and not on the controller's Today. The same after Approve as Billed (the other decision,
         fin2ApproveAsBilled, the function its button calls). An instrument check plants an approved-and-unpaid copy
         and requires every one of those reads to see it, so a read that went blind fails loudly.
Desktop and the 390px phone."""
import asyncio, sys
from harness import *

WW = 'WW-2026-118'

APPR = r"""async (n) => { const sl = ms => new Promise(r => setTimeout(r, ms)), vis = e => !!e && e.getClientRects().length > 0;
  try { tdyTabSet('appr'); tdyAllOpen = true; } catch (e) {} view = 'home'; render(); await sl(200);
  const chip = [...document.querySelectorAll('.view.on .td2-chips button')].find(b => /Approvals/.test(b.innerText));
  const cards = [...document.querySelectorAll('.view.on .td-do .td-card')].filter(vis), e = cards.find(x => x.innerText.includes(n));
  if (!e) return { found: false, chip: chip && chip.innerText, rows: cards.map(c => c.innerText.split('\n')[0]) };
  let b = e.querySelector('[data-tdverb]');
  if (!vis(b)) { e.click(); await sl(200); b = document.querySelector('.view.on .td2-aside [data-td2lead]'); }
  return { found: true, chip: chip && chip.innerText, lead: vis(b) ? b.innerText.trim().replace(/,\s*[−-]?\$[\d,.]+$/, '') : '', blue: !!(b && b.classList.contains('primary')) }; }"""

# every read of To Pay, for the bills named: status, Ready to Pay, the To Pay chip, the controller's Today
TOPAY = r"""async (nums) => { const sl = ms => new Promise(r => setTimeout(r, ms)), vis = e => !!e && e.getClientRects().length > 0;
  const keep = DB.deviceUser, out = {};
  const B = nums.map(n => DB.bills.find(b => b.number === n)).filter(Boolean);
  out.status = Object.fromEntries(B.map(b => [b.number, b.status]));
  out.ready = ydReadyToPay().map(b => b.number).filter(n => nums.includes(n));
  signIn('u_controller'); view = 'ap'; render(); await sl(150);
  const chip = document.querySelector('.view.on [data-acchip="ap:pay"]'); chip && chip.click(); await sl(200);
  // the chip's bill list (#ap-table); its Disputed with Vendors card above it is the held difference, not a bill to pay
  const pane = (document.querySelector('#v-ap #ap-table') || {}).innerText || '';
  out.chip = !!chip; out.toPay = nums.filter(n => pane.includes(n));
  // the controller's Today, every chip (Ready to Pay rows sit under the chip their due date puts them)
  view = 'home'; render(); await sl(200);
  let home = '';
  for (const k of [...document.querySelectorAll('.view.on [data-tdytabbtn]')].map(b => b.dataset.tdytabbtn)) {
    const btn = document.querySelector(`.view.on [data-tdytabbtn="${k}"]`); btn && btn.click(); await sl(200);
    home += [...document.querySelectorAll('.view.on .td-card')].filter(vis).map(e => e.innerText).join('\n') + '\n';
  }
  out.ctlToday = nums.filter(n => home.includes(n));
  signIn(keep); render(); return out; }"""

PLANT = r"""() => { const w = DB.bills.find(b => b.number === 'WW-2026-118'), x = JSON.parse(JSON.stringify(w));
  Object.assign(x, { id: 'bPINCTL', number: 'PIN-CONTROL-1', status: 'approved', paidAt: '', txnId: '', short: null, onHold: null, approvals: [] }); delete x.paidBeforeApproval;
  DB.bills.push(x); save(); return x.number; }"""


def clean(r, nums):
    return r['status'] and all(r['status'].get(n) != 'approved' for n in nums) and not r['ready'] and not r['toPay'] and not r['ctlToday']


async def main():
    c = Checks()
    async with async_playwright() as p:
        for phone in (False, True):
            dev = 'phone' if phone else 'desktop'
            b, pg, errs = await open_app(p, phone)
            await sign_in(pg, 'u_owner')
            pbu = await pg.evaluate("() => DB.bills.filter(b => billPaidUnapproved(b)).map(b => b.number)")
            c.ok(WW in pbu, f'{dev}: {WW} is paid before approval in the seed ({pbu})')
            # the instrument: an approved, unpaid bill is seen by every To Pay read
            ctl = await pg.evaluate(PLANT)
            r = await pg.evaluate(TOPAY, [ctl])
            c.ok(r['chip'] and r['ready'] == [ctl] and r['toPay'] == [ctl] and r['ctlToday'] == [ctl], f'{dev}: instrument: an approved, unpaid bill is on Ready to Pay, the To Pay chip and the controller\'s Today: {r}')
            await pg.evaluate("() => { DB.bills = DB.bills.filter(b => b.id !== 'bPINCTL'); save(); }")
            # before the Owner decides
            r = await pg.evaluate(TOPAY, pbu)
            c.ok(clean(r, pbu), f'{dev}: before approval, no bill paid before approval reaches To Pay: {r}')
            # the Owner's Today, Approvals: WW-2026-118 with Dispute Difference leading
            a = await pg.evaluate(APPR, WW)
            c.ok(a['found'], f"{dev}: {WW} is on the Owner's Today, Approvals tab: {a}")
            c.ok(a.get('lead') == 'Dispute Difference' and a.get('blue'), f'{dev}: Dispute Difference leads it, blue: {a}')
            if a.get('lead'):
                await pg.evaluate("() => { const b = document.querySelector('.view.on .td-do .td-card [data-tdverb]'); const vis = e => !!e && e.getClientRects().length > 0;"
                                  " const L = [...document.querySelectorAll('.view.on .td2-aside [data-td2lead], .view.on .td-do .td-card [data-tdverb]')].filter(vis)"
                                  ".find(x => x.closest('.td-card') ? x.closest('.td-card').innerText.includes('WW-2026-118') : true); L && L.click(); }")
                await pg.wait_for_timeout(400)
                title = await pg.evaluate("() => { const m = document.querySelector('#mbm'); return m ? m.innerText.split('\\n')[0] : ''; }")
                c.ok(title.startswith('Approve PO Amount, Dispute Difference'), f'{dev}: it opens the short-pay sheet: {title!r}')
                await pg.fill('#mbm [data-f=why]', 'Approved at the PO; the field-added window is disputed until the change order settles it')
                await pg.evaluate("() => [...document.querySelectorAll('#mbm button')].find(x => x.innerText.trim() === 'Approve and Dispute').click()")
                await pg.wait_for_timeout(400)
                st = await pg.evaluate("n => { const b = DB.bills.find(x => x.number === n); return [b.status, b.short && b.short.approved, billPaidUnapproved(b)]; }", WW)
                c.ok(st[0] in ('paid', 'verified') and st[1] == 29700 and st[2] is False, f'{dev}: {WW} is approved at the PO and stays paid, not approved-to-pay: {st}')
                r = await pg.evaluate(TOPAY, [WW])
                c.ok(clean(r, [WW]), f'{dev}: after Dispute Difference, {WW} never reaches To Pay: {r}')
            c.ok(not errs, f'{dev}: no page errors: {errs[:3]}')
            await b.close()
        # the other decision: Approve as Billed
        b, pg, errs = await open_app(p)
        await sign_in(pg, 'u_owner')
        st = await pg.evaluate("n => { const b = DB.bills.find(x => x.number === n); fin2ApproveAsBilled(b, 'the extra window was ordered by the client on site'); try { mbCloseModal(); } catch (e) {} return [b.status, billPaidUnapproved(b)]; }", WW)
        r = await pg.evaluate(TOPAY, [WW])
        c.ok(st[0] in ('paid', 'verified') and not st[1] and clean(r, [WW]), f'after Approve as Billed, {WW} stays paid and never reaches To Pay: {st} {r}')
        c.ok(not errs, f'no page errors: {errs[:3]}')
        await b.close()
    return c.done()

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
