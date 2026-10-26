"""Procurement P0, money first (the coordinator's buying day, 2026-10-25, review/procurement/coordinator_day.md findings
1, 3, 6, 7 and 25). Each money rule is proven to the cent, as the people who touch it, on the desktop and the phone.
1. A deposit is applied once: a $4,400 deposit, then the vendor's $8,800 invoice, leaves $4,400 due and $8,800 of job
   cost (not $13,200), the same in AP aging, the cash forecast and the vendor ledger; the owner is never offered
   "Approve as Billed" at the full amount.
2. The $8,000 card charge to Tino on 9/1, before any bill or delivery, is a prepayment on PO-2026-047: never left
   uncategorised, on the coordinator's and the controller's Today with Tino's papers, and the order's "paid" and the
   Vendors page's "paid" are the same number. His invoice then pays only the balance.
3. One purchase-tax rule: the same item from the same vendor is taxed the same on every path; the old default
   "Exempt — capital improvement (ST-124)" is gone, and the orders issued under it are repaired with a note to review.
Run: python3 p0money_test.py"""
import asyncio, sys, os
from harness import async_playwright, open_app, sign_in, go, Checks, ROOT

SHOTS = os.path.join(ROOT, 'review', 'p0money')
async def shot(pg, tag, name):
    os.makedirs(SHOTS, exist_ok=True)
    try: await pg.screenshot(path=os.path.join(SHOTS, f'{tag}_{name}.png'))
    except Exception: pass

T = "() => document.getElementById('toast').innerText"
SW = "() => document.documentElement.scrollWidth"

# an out-of-state stone fabricator (charges no NY tax: use tax), papers on file; an order for two slabs, 50% on order
MKPO = """([pid, vname]) => {
  let v = DB.vendors.find(x => x.name === vname);
  if (!v) { v = { id: uid('v'), name: vname, trade: 'Stone fabrication', email: 'orders@atlanticstone.example', city: 'Newark, NJ', state: 'NJ', chargesTax: false, insuranceExp: '2027-05-01', w9: true, createdBy: 'Alan' }; DB.vendors.push(v); }
  const p = DB.projects.find(x => x.id === pid), l = (DB.clients.flatMap(c => c.estimates || []).find(e => e.id === 'es1') || { lines: [] }).lines.find(x => x.id === 'l9');
  const po = { id: uid('po'), number: nextPO(), projectId: pid, vendor: vname, vendorId: v.id, date: today(), expected: iso(addDays(today(), 21)), status: 'issued', shipTo: 'site', notes: '',
    lines: [{ id: uid('pl'), item: 'Parlor kitchen countertop slab', desc: 'Calacatta, 3cm', qty: 2, unit: 'slab', price: 4400, materialId: '', line: 'estimate:es1:l9', code: '10', received: 0 }],
    tax: 0, shipping: 0, matchedTxns: [], createdBy: 'Chen Biron', type: 'materials', entityId: p.entityId || '', receipts: [], srcDocs: [], __v2: 1 };
  applyTerms(po, '5050'); DB.pos.push(po); save();
  return { id: po.id, no: po.number, tot: poTotal(po).total, ts: po.taxStatus, ut: po.useTax && po.useTax.amount, dep: po.depositPct } }"""

FIN = """([pid, poid, vname]) => { const p = DB.projects.find(x => x.id === pid), po = DB.pos.find(x => x.id === poid), J = jobFin(p), L = scLedger(vname, ''), A = apAging();
  const F = cashForecast(), fc = r2(F.weeks.reduce((a, w) => a + w.items.filter(([l, x]) => x < 0 && (l === 'Bill ' + vname || l === 'PO ' + po.number)).reduce((s, [l, x]) => s - x, 0), 0));
  const bills = DB.bills.filter(b => b.poId === po.id && !['void','rejected'].includes(b.status));
  return { actual: J.actual, committed: J.committed, ap: r2(A.items.filter(i => i.kind === 'bill' && bills.some(b => b.id === i.id)).reduce((a, i) => a + i.amt, 0)), fc: fc,
    lBilled: L.billed, lPaid: L.paid, lPayable: L.payable, lDeposits: L.deposits, lPre: L.prepaidOpen, poPaid: poPaid(po), poBilled: poBilled(po), vPaid: vendorSpend(DB.vendors.find(v => v.name === vname)),
    bills: bills.map(b => ({ n: b.number, st: b.status, tot: billTotal(b), inv: p0Invoice(b), dep: p0IsDeposit(b), lines: b.lines.map(l => [l.desc, l.amount, l.prepayOf || '']) })) } }"""

async def drawer_bill(pg, vname, number, po_no, desc, amount):
    """Billing keys a vendor bill in the New Bill drawer, against the order, as the expert did."""
    await pg.evaluate("() => { mbCloseModal(); closeEditor && closeEditor(); openBill(null) }"); await pg.wait_for_timeout(300)
    await pg.fill('#e-vendor', vname); await pg.fill('#e-number', number)
    await pg.evaluate("""([vname]) => { const s = document.getElementById('e-po'); if (![...s.options].some(o => /PO-/.test(o.text))) {
        s.innerHTML += DB.pos.filter(p => p.vendor === vname).map(p => `<option value="${p.id}">${p.number}</option>`).join('') } }""", [vname])
    await pg.evaluate("""(no) => { const s = document.getElementById('e-po'); const o = [...s.options].find(o => o.text.includes(no)); s.value = o.value; s.dispatchEvent(new Event('change', { bubbles: true })) }""", po_no)
    await pg.locator('#d-body table.lines input[data-f="desc"]').first.fill(desc)
    await pg.locator('#d-body table.lines input[data-f="amount"]').first.fill(str(amount))
    await pg.locator('#d-save').click(); await pg.wait_for_timeout(500)
    return await pg.evaluate("(n) => { const b = DB.bills.find(x => x.number === n); return b && b.id }", number)

async def run(p, c, phone):
    tag = 'phone' if phone else 'desktop'
    b, pg, errs = await open_app(p, phone)
    try:
        # ================================================================== 3. one purchase-tax rule (and the repair)
        await sign_in(pg, 'u_controller')
        r = await pg.evaluate("""() => ({ opts: Object.values(TAX_STATUS), rep: DB.company.p0TaxRepaired.map(id => { const po = DB.pos.find(x => x.id === id); return [po.number, po.taxStatus, poTotal(po).total, po.useTax && po.useTax.amount, po.taxRepair.fromWords] }),
          any: DB.pos.some(po => po.taxStatus === 'exempt-ci') || DB.bills.some(b => b.taxStatus === 'exempt-ci'), card: mApprovals().filter(a => a.kind === 'taxfix').map(a => a.title) })""")
        c.ok(not any('capital improvement' in o for o in r['opts']) and not r['any'], f'{tag}: no order or bill is "Exempt — capital improvement"; the options are {r["opts"]}')
        rep = {x[0]: x for x in r['rep']}
        # Nemo Tile and Window Works were billed and paid with no tax: their totals stand and use tax accrues, 8.875%
        # of the goods (320 sf x $12.50 = $4,000 -> $355.00; 9 x $3,300 = $29,700 -> $2,635.88). Tino's order is not
        # billed: Tino charges NY tax, so the order reads 900 sf x $8.90 = $8,010 + 8.875% = $8,720.89.
        c.ok(rep.get('PO-2026-041', [0, 0, 0, 0])[1:4] == ['use-tax', 4250, 355], f"{tag}: PO-2026-041 repaired to use tax $355.00 on a $4,250 order ({rep.get('PO-2026-041')})")
        c.ok(rep.get('PO-2026-044', [0, 0, 0, 0])[1:4] == ['use-tax', 29700, 2635.88], f"{tag}: PO-2026-044 repaired to use tax $2,635.88 ({rep.get('PO-2026-044')})")
        c.ok(rep.get('PO-2026-047', [0, 0, 0])[1:3] == ['taxable', 8720.89], f"{tag}: PO-2026-047 taxed at 8.875%, $8,720.89 ({rep.get('PO-2026-047')})")
        c.ok(r['card'] == ['Purchase tax corrected on 3 orders'], f'{tag}: the controller has one card to review the 3 corrections ({r["card"]})')
        await pg.evaluate("() => { poOpen = 'po3'; view = 'po'; render(); }"); await pg.wait_for_timeout(300)
        t = await pg.evaluate("() => document.querySelector('.view.on').innerText")
        await shot(pg, tag, 'po047_tax_repair')
        c.ok('Purchase tax corrected' in t and 'Exempt — capital improvement' in t and 'Mark Reviewed' in t, f'{tag}: PO-2026-047 says what was corrected and offers the review')
        c.ok(await pg.evaluate(SW) <= (390 if phone else 1440), f'{tag}: the order page does not scroll sideways')
        await pg.evaluate("() => p0TaxFixSheet()"); await pg.wait_for_timeout(200)
        await pg.click('#mbm-ok'); await pg.wait_for_timeout(300)
        r = await pg.evaluate("() => ({ left: DB.pos.filter(po => po.taxRepair && !po.taxRepair.reviewed).length, card: mApprovals().filter(a => a.kind === 'taxfix').length, by: DB.pos.find(x => x.id === 'po3').taxRepair.reviewed })")
        c.ok(r['left'] == 0 and r['card'] == 0 and r['by'] and r['by']['by'], f'{tag}: Mark Reviewed clears the card and keeps who reviewed ({r})')
        c.ok('reviewed' in (await pg.evaluate(T)) and 'Open' in (await pg.evaluate(T)), f'{tag}: the review toasts with Open')

        # the same item from the same vendor, every path that makes an order: one answer
        await sign_in(pg, 'u_chen')
        r = await pg.evaluate("""() => { let v = DB.vendors.find(x => x.name === 'Court Street Tile');
          v || DB.vendors.push(v = { id: uid('v'), name: 'Court Street Tile', trade: 'Tile', email: 'orders@courtstile.example', city: 'Brooklyn, NY', state: 'NY', insuranceExp: '2027-06-30', w9: true, createdBy: 'Alan' });
          const mk = (extra) => { const po = Object.assign({ id: uid('po'), number: nextPO(), projectId: 'p121', vendor: v.name, date: today(), expected: '', status: 'draft', shipTo: 'site', notes: '',
            lines: [{ id: uid('pl'), item: 'Calacatta porcelain 12x24', desc: '', qty: 100, unit: 'sf', price: 12.5, materialId: '', line: 'estimate:es1:l7', received: 0 }], tax: 0, shipping: 0, matchedTxns: [], createdBy: 'Chen Biron', type: 'materials' }, extra);
            DB.pos.push(po); return po };
          const paths = {
            assistant: mk({}),                                          // the assistant's proposal, a field request, Which Lines: tax 0, no status
            oldDefault: mk({ taxStatus: 'exempt-ci', __v2: 1 }),        // a path still writing the old default
            rfqTaxed: mk({ origin: 'rfq', tax: 8.875, __v2: 1 }),        // the RFQ award for a vendor who charges tax
            submittal: smPO ? null : null,
          };
          delete paths.submittal; save();
          const out = Object.fromEntries(Object.entries(paths).map(([k, po]) => [k, [po.taxStatus, po.tax, poTotal(po).total]]));
          out.rule = [p0TaxStatusFor({ type: 'materials', vendor: v.name }), 0, 0];
          out.sub = (() => { const po = mk({ type: 'subcontract' }); save(); return [po.taxStatus, po.tax, poTotal(po).total] })();
          out.oos = (() => { const w = DB.vendors.find(x => pwOutOfState(x) || x.chargesTax === false) || (() => { const x = { id: uid('v'), name: 'Lancaster Mill Direct', city: 'Lancaster, PA', state: 'PA', chargesTax: false, insuranceExp: '2027-01-01', w9: true }; DB.vendors.push(x); return x })();
            const po = mk({ vendor: w.name }); save(); return [po.taxStatus, po.tax, poTotal(po).total, po.useTax && po.useTax.amount] })();
          // a bill keyed with the old default takes its order's status
          const bp = paths.assistant, bl = { id: uid('b'), vendor: v.name, number: 'P0-TAX-1', date: today(), due: today(), projectId: 'p121', poId: bp.id, cat: 'materials', lines: [{ id: uid('bl'), desc: 'tile', amount: 1250 }], status: 'draft', approvals: [], taxStatus: 'exempt-ci' };
          DB.bills.push(bl); save(); out.bill = [bl.taxStatus];
          return { v: v.name, out: out } }""")
        o = r['out']
        same = ['taxable', 8.875, 1360.94]   # 100 sf x $12.50 = $1,250.00 + 8.875% ($110.94) = $1,360.94
        for k in ('assistant', 'oldDefault', 'rfqTaxed'):
            c.ok(o[k] == same, f"{tag}: path {k}: {r['v']}'s tile is taxed {o[k]}, the rule says {same}")
        c.ok(o['rule'][0] == 'taxable', f"{tag}: the rule itself says taxable for {r['v']} ({o['rule']})")
        c.ok(o['sub'] == ['none', 0, 1250], f"{tag}: a subcontract carries no purchase tax ({o['sub']})")
        c.ok(o['oos'][:3] == ['use-tax', 0, 1250] and o['oos'][3] == 110.94, f"{tag}: a vendor who charges no NY tax: use tax $110.94 to accrue, the order stays $1,250 ({o['oos']})")
        c.ok(o['bill'] == ['taxable'], f"{tag}: a bill keyed with the old default takes its order's status ({o['bill']})")
        await pg.evaluate("(n) => { const po = DB.pos.find(x => x.status === 'draft' && x.vendor === n); poOpen = po.id; view = 'po'; render(); }", r['v']); await pg.wait_for_timeout(300)
        t = await pg.evaluate("() => { const e = document.querySelector('.view.on .p0-taxrule'); return e ? [e.innerText, e.getBoundingClientRect().width > 0] : null }")
        c.ok(t and 'Confirm the treatment with the accountant' in t[0] and 'NY sales tax 8.875%' in t[0], f'{tag}: on a draft order the Sales Tax field, where a person chooses, says the rule and to confirm with the accountant ({t})')
        # the Order sheet (the Buy Board's one-line order) says the tax as the supplier is chosen
        key = await pg.evaluate("""() => { const r = buyList('p121').find(x => x.kind === 'line'); return r ? JSON.stringify(flRowKey(r)) : null }""")
        if key:
            await pg.evaluate("(k) => buyOrderDialog(JSON.parse(k))", key); await pg.wait_for_timeout(300)
            await pg.evaluate("(v) => { const s = document.querySelector('#mbm [data-f=\"vendor\"]'); s.value = v; s.dispatchEvent(new Event('change', { bubbles: true })) }", r['v'])
            await pg.fill('#mbm [data-f="qty"]', '100'); await pg.fill('#mbm [data-f="price"]', '12.50'); await pg.wait_for_timeout(200)
            await shot(pg, tag, 'order_sheet_tax')
            tl = await pg.evaluate("() => { const e = document.querySelector('#mbm .p0-taxline'); return e ? [e.textContent, e.getBoundingClientRect().width > 0] : null }")
            c.ok(tl and 'NY sales tax 8.875%, $110.94' in tl[0] and tl[1], f'{tag}: the Order sheet says the tax the order will carry ({tl})')
            c.ok('accountant' not in (tl[0] if tl else ''), f'{tag}: the sheet decides by the rule; the accountant note is only where a person chooses')
            await pg.evaluate("() => mbCloseModal()")
        else:
            c.ok(False, f'{tag}: no contract line on the Buy Board to open the Order sheet from')

        # ================================================================== 2. the $8,000 to Tino before delivery
        r = await pg.evaluate("""() => { const t = DB.txns.find(x => x.id === 't13'), po = DB.pos.find(x => x.id === 'po3');
          return { cat: t.cat, pid: t.projectId, po: t.poId, code: t.code, line: t.line, pre: !!t.prepay, poPaid: poPaid(po), vPaid: vendorSpend(DB.vendors.find(v => v.name === 'Tino')) } }""")
        c.ok(r['cat'] == 'materials' and r['pid'] == 'p121' and r['po'] == 'po3' and r['pre'] and r['line'] == 'estimate:es1:l8', f'{tag}: the 9/1 card charge is linked to PO-2026-047, its job and line, as a prepayment ({r})')
        c.ok(r['poPaid'] == 8000 and r['vPaid'] == 8000, f"{tag}: the order's paid and the Vendors page's paid agree: {r['poPaid']} and {r['vPaid']}")
        cards = {}
        for u in ('u_chen', 'u_controller', 'u_owner', 'u_billing'):
            await sign_in(pg, u)
            cards[u] = await pg.evaluate("() => mApprovals().filter(a => a.kind === 'prepay').map(a => a.title + ' | ' + a.n + ' | ' + a.detail)")
        x = cards['u_chen'][0] if cards['u_chen'] else ''
        c.ok(len(cards['u_chen']) == 1 and 'Tino' in x and '$8,000' in x and 'PO-2026-047' in x and 'No COI on file' in x and 'No W-9 on file' in x, f"{tag}: the coordinator's Approvals carry the prepayment with the order and Tino's papers ({cards['u_chen']})")
        c.ok(not cards['u_controller'] and not cards['u_owner'] and not cards['u_billing'], f"{tag}: one item, one owner: nobody else is asked ({cards})")
        await sign_in(pg, 'u_controller'); await go(pg, 'home'); await pg.wait_for_timeout(300)
        # the approved Today (2026-10-25) keeps Caught for You behind the quiet line at the foot. The prepayment is the
        # coordinator's to confirm (one item, one owner), so it is not a row of the controller's; it reaches her in the
        # update at the top, with the papers, ranked by the Standard (integrity), and Caught for You keeps its row
        r = await pg.evaluate("""() => { const R = (typeof homeRoot === 'function' && homeRoot()) || document.querySelector('.view.on');
          const upd = [...R.querySelectorAll('.td2-brief .td2-bl')].map(p => p.innerText).find(t => /Paid ahead: Tino/.test(t)) || '';
          td2QuietOpen = true; render();
          const R2 = (typeof homeRoot === 'function' && homeRoot()) || document.querySelector('.view.on');
          const cf = [...R2.querySelectorAll('.td-catch .td-card')].map(e => e.innerText.replace(/\\s+/g, ' ')).find(t => /Paid ahead: Tino/.test(t)) || '';
          td2QuietOpen = false; render();
          return { rows: tdCaught([]).filter(x => x.src === 'prepaidAhead').map(x => x.what + ' | ' + x.sub), upd, cf, first: !!R.querySelector('.td2-brief .td2-bl') && /Paid ahead: Tino/.test(R.querySelector('.td2-brief .td2-bl').innerText) }; }""")
        c.ok(len(r['rows']) == 1 and 'Tino' in r['rows'][0] and '$8,000' in r['rows'][0] and 'no COI, no W-9' in r['rows'][0], f"{tag}: Caught for You holds it with the papers ({r['rows']})")
        c.ok('$8,000' in r['upd'] and 'no COI, no W-9' in r['upd'] and r['first'], f"{tag}: the controller's Today says it first in the update, with the papers ({r['upd']!r})")
        c.ok('Paid ahead: Tino' in r['cf'], f"{tag}: and the quiet line opens to it in Caught for You ({r['cf']!r})")
        await shot(pg, tag, 'controller_today')
        c.ok(await pg.evaluate(SW) <= (390 if phone else 1440), f"{tag}: the controller's Today does not scroll sideways")
        await sign_in(pg, 'u_chen'); await go(pg, 'home'); await pg.wait_for_timeout(300)
        h = await pg.evaluate("() => { const r = (typeof homeRoot === 'function' && homeRoot()) || document.querySelector('.view.on'); return r ? r.innerText : '' }")
        await shot(pg, tag, 'coord_today')
        da = await pg.evaluate("() => tdyModel().all.some(i => i.kind === 'prepay' && i.id === 't13')")
        c.ok(da, f"{tag}: the coordinator's Today has it on Do Now (All), ranked by the Standard, not over the vendors' mail")
        await pg.evaluate("() => { tdyTabSet('appr'); render(); }"); await pg.wait_for_timeout(200)
        h = await pg.evaluate("() => { const r = (typeof homeRoot === 'function' && homeRoot()) || document.querySelector('.view.on'); return r ? r.innerText : '' }")
        c.ok('Paid before delivery' in h and 'Review' in h, f"{tag}: and under Approvals, with Review")
        await pg.evaluate("() => { tdyTabSet('all'); render(); }")
        c.ok(await pg.evaluate(SW) <= (390 if phone else 1440), f'{tag}: Today does not scroll sideways')
        await pg.evaluate("() => p0PrepaySheet('t13')"); await pg.wait_for_timeout(200)
        await shot(pg, tag, 'prepay_sheet')
        s = await pg.evaluate("() => document.getElementById('mbm').innerText")
        c.ok('PO-2026-047' in s and 'No COI on file' in s and 'No W-9 on file' in s and 'Confirm Prepayment' in s and 'Not This Order' in s, f'{tag}: the review sheet shows the order, the papers and the two answers')
        await pg.click('#mbm-ok'); await pg.wait_for_timeout(300)
        t = await pg.evaluate(T)
        r = await pg.evaluate("() => ({ c: DB.txns.find(x => x.id === 't13').prepay.confirmed, left: mApprovals().filter(a => a.kind === 'prepay').length, caught: (signIn('u_controller'), tdCaught([]).filter(x => x.src === 'prepaidAhead').length) })")
        await sign_in(pg, 'u_chen')
        c.ok(r['c'] and r['c']['by'] == 'Chen Biron' and r['left'] == 0 and r['caught'] == 0, f"{tag}: confirmed by the coordinator; gone from her Approvals and the controller's Caught for You ({r})")
        c.ok('confirmed as a prepayment on PO-2026-047' in t and 'Open' in t, f'{tag}: the confirmation toasts with Open ({t!r})')
        # a second charge to Tino is linked, then refused: back to Banking, never linked again
        r = await pg.evaluate("""() => { DB.txns.push({ id: 'tp0x', date: today(), acct: 'ac2', desc: 'TINO FLOORING', amt: -500, cat: 'uncat', projectId: '', code: '', vendor: 'Tino', memo: '', status: 'new', line: '' }); save();
          const t = DB.txns.find(x => x.id === 'tp0x'), was = t.poId; p0PrepayUnlink('tp0x'); save();
          return { was: was, now: t.poId, cat: t.cat, no: !!t.prepayNo, again: t.poId } }""")
        c.ok(r['was'] == 'po3' and r['now'] == '' and r['cat'] == 'uncat' and r['no'], f'{tag}: Not This Order puts the line back for Banking and it stays unlinked ({r})')
        await pg.evaluate("() => { DB.txns = DB.txns.filter(x => x.id !== 'tp0x'); save(); }")
        # Tino's invoice TN-2291 (in the demo mail): 900 sf x $9.15 = $8,235.00 + 8.875% $730.86 + freight $450 = $9,415.86
        await sign_in(pg, 'u_billing')
        j0 = await pg.evaluate("() => jobFin(DB.projects.find(p => p.id === 'p121')).actual")
        r = await pg.evaluate("""() => { const po = DB.pos.find(x => x.id === 'po3'), b = { id: uid('b'), vendor: 'Tino', number: 'TN-2291', date: today(), due: iso(addDays(today(), 15)), entityId: po.entityId || 'ent1', projectId: 'p121', poId: 'po3', cat: 'materials', code: '09', line: 'estimate:es1:l8',
            lines: [{ id: uid('bl'), desc: '5in white oak flooring, select', amount: 8235, poLineId: po.lines[0].id }, { id: uid('bl'), desc: 'Sales tax 8.875%', amount: 730.86 }, { id: uid('bl'), desc: 'Freight', amount: 450 }],
            payMethod: 'ACH', notes: '', status: 'submitted', approvals: [], createdBy: 'Jeanette', createdAt: appNowIso() };
          DB.bills.push(b); save();
          return { tot: billTotal(b), inv: p0Invoice(b), flags: billFlags(b), left: pay3PO(b).left, j: jobFin(DB.projects.find(p => p.id === 'p121')).actual, paid: poPaid(po), billed: poBilled(po), vPaid: vendorSpend(DB.vendors.find(v => v.name === 'Tino')) } }""")
        c.ok(r['tot'] == 1415.86 and r['inv'] == 9415.86, f"{tag}: Tino's $9,415.86 invoice takes the $8,000 paid ahead: $1,415.86 due ({r['tot']})")
        c.ok(round(r['j'] - j0, 2) == 1415.86, f"{tag}: job cost rises by the balance only: $8,000 card + $1,415.86 = $9,415.86 once ({round(r['j'] - j0, 2)})")
        c.ok(any('$9,415.86 with the $8,000 paid ahead' in f and '$8,720.89' in f for f in r['flags']), f"{tag}: the bill is over its order by $694.97 with the prepayment counted ({r['flags']})")
        c.ok(r['left'] == 720.89, f"{tag}: the approval measures it against $720.89 left on the order ({r['left']})")
        c.ok(r['paid'] == 8000 == r['vPaid'] and r['billed'] == 9415.86, f"{tag}: the order reads billed $9,415.86, paid $8,000, and Vendors agrees ({r})")
        await pg.evaluate("() => { DB.bills = DB.bills.filter(x => x.number !== 'TN-2291'); save(); }")

        # ================================================================== 1. the deposit, applied once
        await sign_in(pg, 'u_chen')
        j0 = await pg.evaluate("() => jobFin(DB.projects.find(p => p.id === 'p121')).actual")
        po = await pg.evaluate(MKPO, ['p121', 'Atlantic Stone Fab'])
        c.ok(po['tot'] == 8800 and po['ts'] == 'use-tax' and po['ut'] == 781 and po['dep'] == 50, f'{tag}: the slab order is $8,800, no tax charged by the NJ fabricator, use tax $781.00 to accrue, 50% on order ({po})')
        await pg.evaluate("(id) => { poOpen = id; view = 'po'; render(); }", po['id']); await pg.wait_for_timeout(300)
        t = await pg.evaluate("() => document.querySelector('.view.on .po-money') ? document.querySelector('.view.on .po-money').innerText : ''")
        c.ok('Bill the Deposit $4,400' in t, f'{tag}: the order offers Bill the Deposit $4,400 ({t[-200:]!r})')
        # the expert's own path: billing keys the deposit request in the New Bill drawer, in the vendor's words
        await sign_in(pg, 'u_billing')
        dep_id = await drawer_bill(pg, 'Atlantic Stone Fab', 'ASF-DEP-1001', po['no'], 'Deposit 50% to release slabs', 4400)
        r = await pg.evaluate("""(id) => { const b = DB.bills.find(x => x.id === id); return { dep: p0IsDeposit(b), flags: billFlags(b), tot: billTotal(b) } }""", dep_id)
        c.ok(r['dep'] and r['tot'] == 4400 and not any('nothing received' in f for f in r['flags']), f'{tag}: the deposit is a deposit, not "nothing received yet" ({r})')
        await pg.evaluate("(id) => { const b = DB.bills.find(x => x.id === id); editing = { collect: () => ({}) }; billAction(b, 'submit'); }", dep_id)
        await sign_in(pg, 'u_controller')
        ut1 = await pg.evaluate("(id) => { const u = pwUseTaxAccrue(id); return u && u.amount }", dep_id)
        await sign_in(pg, 'u_owner')
        r = await pg.evaluate("""(id) => { const b = DB.bills.find(x => x.id === id); billAction(b, 'approve'); const m = document.getElementById('mbm'); const st1 = b.status;
          const R = pcCheck(b); return { st: st1, modal: m && m.getClientRects().length ? m.innerText.slice(0, 300) : '', holds: R.holds.map(h => h.key + ': ' + h.what), three: R.ok.filter(k => k.key === 'threeway').map(k => k.text) } }""", dep_id)
        c.ok(r['st'] == 'approved' and not r['modal'], f'{tag}: the owner approves the deposit with no override reason ({r})')
        c.ok(r['three'] and 'terms allow' in r['three'][0] and not any(h.startswith('threeway') for h in r['holds']), f'{tag}: the Payment Check reads it as a deposit the terms allow ({r})')
        await pg.evaluate("""(id) => { const b = DB.bills.find(x => x.id === id); (DB.payments = DB.payments || []).push({ id: uid('pay'), billId: b.id, amount: 4400, date: today(), method: 'ACH', by: 'Jeanette' }); b.status = 'paid'; b.paidAt = appNowIso(); save(); }""", dep_id)
        f1 = await pg.evaluate(FIN, ['p121', po['id'], 'Atlantic Stone Fab'])
        c.ok(round(f1['actual'] - j0, 2) == 4400 and f1['poPaid'] == 4400 == f1['vPaid'] and f1['poBilled'] == 0, f"{tag}: after the deposit: $4,400 of cost (a deposit, not progress), paid $4,400 on the order and on Vendors, nothing invoiced yet ({f1['actual'] - j0}, {f1['poPaid']}, {f1['vPaid']}, {f1['poBilled']})")
        c.ok(f1['fc'] == 4400 and f1['ap'] == 0, f"{tag}: the forecast holds the $4,400 balance once, AP is clear ({f1['fc']}, {f1['ap']})")
        # the vendor's final invoice for the whole order, $8,800, keyed as it reads
        await sign_in(pg, 'u_billing')
        await pg.evaluate("(id) => { const po = DB.pos.find(x => x.id === id); po.lines.forEach(l => l.received = l.qty); po.status = 'received'; po.receivedOn = today(); save(); }", po['id'])
        fin_id = await drawer_bill(pg, 'Atlantic Stone Fab', 'ASF-2231', po['no'], 'Two Calacatta slabs, 3cm, fabricated', 8800)
        t = await pg.evaluate(T)
        c.ok('$4,400 prepaid on ' + po['no'] in t and '$8,800 invoiced, $4,400 due' in t and 'Open' in t, f'{tag}: billing is told the deposit came off: {t!r}')
        r = await pg.evaluate("(id) => { const b = DB.bills.find(x => x.id === id); return { tot: billTotal(b), inv: p0Invoice(b), lines: b.lines.map(l => [l.desc, l.amount]) } }", fin_id)
        c.ok(r['tot'] == 4400 and r['inv'] == 8800 and any(a == -4400 and 'Less prepaid on ' + po['no'] in d for d, a in r['lines']), f"{tag}: the bill reads $8,800 invoiced, less $4,400 prepaid, $4,400 due ({r})")
        # the drawer, as billing opens it (the phone too): invoice, less prepaid, due; the rule's line is not typed
        await pg.evaluate("(id) => openBill(id)", fin_id); await pg.wait_for_timeout(300)
        await shot(pg, tag, 'final_bill_drawer')
        r = await pg.evaluate("""() => { const n = document.querySelector('#d-body .p0-billdep'); const tr = document.querySelector('#d-body tr[data-bl^="bl_p0_"] input[data-f="amount"]');
          return { n: n ? n.innerText : '', ro: tr ? tr.readOnly : null, sw: document.documentElement.scrollWidth } }""")
        c.ok('$8,800 invoiced' in r['n'] and '$4,400' in r['n'] and '$4,400 due' in r['n'] and r['ro'] is True, f'{tag}: the bill drawer shows invoice, less prepaid, due, and the prepaid line is read-only ({r})')
        c.ok(r['sw'] <= (390 if phone else 1440), f"{tag}: the bill drawer does not scroll sideways ({r['sw']})")
        # editing the bill keeps the deposit taken off once (the drawer rebuilds its lines on save)
        await pg.locator('#d-save').click(); await pg.wait_for_timeout(400)
        r = await pg.evaluate("(id) => { const b = DB.bills.find(x => x.id === id); return [billTotal(b), b.lines.filter(l => l.amount < 0).length] }", fin_id)
        c.ok(r == [4400, 1], f'{tag}: saved again from the drawer, still $4,400 due and one prepaid line ({r})')
        await pg.evaluate("(id) => { const b = DB.bills.find(x => x.id === id); editing = { collect: () => ({}) }; billAction(b, 'submit'); }", fin_id)
        await sign_in(pg, 'u_controller')
        ut2 = await pg.evaluate("(id) => { const u = pwUseTaxAccrue(id); return u && u.amount }", fin_id)
        c.ok(round((ut1 or 0) + (ut2 or 0), 2) == 781, f"{tag}: use tax accrues once on the order's $8,800, split $4,400 and $4,400: {ut1} + {ut2} = $781.00")
        await sign_in(pg, 'u_owner')
        r = await pg.evaluate("""(id) => { const b = DB.bills.find(x => x.id === id); const card = mApprovals({ everyone: true }).find(a => a.kind === 'bill' && a.id === id);
          billAction(b, 'approve'); const m = document.getElementById('mbm'); const modal = m && m.getClientRects().length ? m.innerText : ''; mbCloseModal();
          b.status === 'approved' || billAction(b, 'approve', 'Slabs delivered and checked on site; PM away'); return { st: b.status, modal: modal, card: card && card.detail } }""", fin_id)
        c.ok('Approve as Billed' not in r['modal'] and '$8,800' not in r['modal'], f"{tag}: the owner is never offered Approve as Billed at $8,800 ({r['modal'][:200]!r})")
        c.ok(r['st'] in ('approved', 'pm-approved'), f"{tag}: the owner approves the balance ({r['st']})")
        c.ok(r['card'] and '$8,800 invoiced less $4,400 prepaid, $4,400 due' in r['card'], f"{tag}: the owner's card says it ({r['card']})")
        f2 = await pg.evaluate(FIN, ['p121', po['id'], 'Atlantic Stone Fab'])
        c.ok(round(f2['actual'] - j0, 2) == 8800, f"{tag}: job cost $8,800, not $13,200 ({round(f2['actual'] - j0, 2)})")
        c.ok(f2['ap'] == 4400, f"{tag}: AP aging $4,400 ({f2['ap']})")
        c.ok(f2['fc'] == 4400, f"{tag}: the cash forecast $4,400, once ({f2['fc']})")
        c.ok(f2['lBilled'] == 8800 and f2['lPaid'] == 4400 and f2['lPayable'] == 4400 and f2['lPre'] == 0, f"{tag}: the vendor ledger: billed $8,800, paid $4,400, payable $4,400, nothing paid ahead left ({f2['lBilled']}, {f2['lPaid']}, {f2['lPayable']}, {f2['lPre']})")
        c.ok(f2['poBilled'] == 8800 and f2['poPaid'] == 4400 == f2['vPaid'], f"{tag}: the order reads billed $8,800, paid $4,400; Vendors agrees ({f2['poBilled']}, {f2['poPaid']}, {f2['vPaid']})")
        # Bill This PO after a deposit bills the whole order, and the deposit comes off it (never "Bill Remaining $4,400")
        st = await pg.evaluate("""([pid, vname]) => { const po = DB.pos.find(x => x.vendor === vname && x.status === 'issued' && !DB.bills.some(b => b.poId === x.id)) || null; return po && lkPOBillState(po) }""", ['p121', 'Atlantic Stone Fab'])
        po2 = await pg.evaluate(MKPO, ['p121', 'Atlantic Stone Fab'])
        # the coordinator's way: Bill the Deposit on the order's Accounting card (one tap, one field)
        await sign_in(pg, 'u_chen')
        await pg.evaluate("(id) => { poOpen = id; view = 'po'; render(); }", po2['id']); await pg.wait_for_timeout(300)
        btn = pg.locator('.view.on [data-p0dep]')
        c.ok(await btn.count() == 1, f'{tag}: Bill the Deposit is on the second order')
        if await btn.count():
            bb = await btn.first.bounding_box()
            c.ok(not phone or (bb and bb['height'] >= 44), f'{tag}: Bill the Deposit is a tappable button ({bb})')
            await btn.first.click(); await pg.wait_for_timeout(300)
            await pg.fill('#mbm [data-f="number"]', 'ASF-DEP-2002'); await pg.click('#mbm-ok'); await pg.wait_for_timeout(400)
            t = await pg.evaluate(T)
            r = await pg.evaluate("(id) => { const b = DB.bills.find(x => x.poId === id && x.number === 'ASF-DEP-2002'); return b && { dep: b.deposit, tot: billTotal(b), st: b.status, code: b.code, pid: b.projectId } }", po2['id'])
            c.ok(r and r['dep'] is True and r['tot'] == 4400 and r['st'] == 'submitted' and r['pid'] == 'p121', f'{tag}: a $4,400 deposit bill on the order, submitted, on the job ({r})')
            c.ok('Deposit bill ASF-DEP-2002' in t and 'Open' in t, f'{tag}: it toasts with Open ({t!r})')
            await pg.evaluate("(id) => { const b = DB.bills.find(x => x.poId === id && x.number === 'ASF-DEP-2002'); b.status = 'approved'; save(); }", po2['id'])
        st = await pg.evaluate("(id) => lkPOBillState(DB.pos.find(x => x.id === id))", po2['id'])
        c.ok(st['remaining'] == 8800 and not st['partial'], f'{tag}: after a deposit, Bill This PO bills the whole $8,800 order ({st})')
        # a gate: an open bill never pays at the full amount while a prepayment sits unapplied on its order
        g = await pg.evaluate("""(id) => { const po = DB.pos.find(x => x.id === id), b = { id: uid('b'), vendor: po.vendor, number: 'ASF-2232', date: today(), due: today(), projectId: po.projectId, poId: po.id, cat: 'materials', code: '10', lines: [{ id: uid('bl'), desc: 'slabs', amount: 8800 }], status: 'submitted', approvals: [] };
          DB.bills.push(b); const before = billTotal(b); billAction(b, 'approve'); return { before: before, after: billTotal(b) } }""", po2['id'])
        c.ok(g['before'] == 8800 and g['after'] == 4400, f'{tag}: a bill pushed past save() is brought down to $4,400 before it is approved ({g})')

        # ================================================================== Ask: vendor money is never client money
        await sign_in(pg, 'u_chen')
        a1 = await pg.evaluate("() => paAsk('what deposits have I paid').headline")
        a2 = await pg.evaluate("() => paAsk('what does Atlantic Stone Fab owe us').headline")
        a3 = await pg.evaluate("() => paAsk('what does Nemo Tile owe us').headline")
        c.ok('paid ahead' in a1 and 'receivable' not in a1.lower(), f'{tag}: "what deposits have I paid" answers with orders ({a1!r})')
        c.ok('Atlantic Stone Fab' in a2 and 'receivable' not in a2.lower(), f'{tag}: "what does Atlantic Stone Fab owe us" is about the vendor ({a2!r})')
        c.ok('Nemo Tile' in a3 and 'receivable' not in a3.lower() and '92,265' not in a3, f'{tag}: "what does Nemo Tile owe us" never answers with client receivables ({a3!r})')
        c.ok(not errs, f'{tag}: no page errors {errs[:3]}')
    finally:
        await b.close()

async def main():
    c = Checks()
    async with async_playwright() as p:
        for phone in (False, True):
            await run(p, c, phone)
    sys.exit(c.done())
if __name__ == '__main__':
    asyncio.run(main())
