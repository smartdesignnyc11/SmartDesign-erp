"""Quantity on progress bills (Alan, 11-09: "have qnty on our templates and be able to show that to the client").
A pay application shows each schedule-of-values line's agreed quantity and unit price, read from the estimate line it
came from; a progress invoice billed line by line against an estimate shows quantity, unit price, contract and this
invoice; a contract of lump sums keeps the plain layout. Invented demo data only."""
import asyncio
from playwright.async_api import async_playwright
from harness import open_app, sign_in, Checks

SETUP = r"""() => {
  const c = blankClient("Quantity Test Client"); DB.clients.push(c);
  const e = newDoc(c, "estimate", {template: "construction"});
  e.lines = [
    {id: "lq1", item: "Window installation", desc: "", qty: 15, unit: "ea", rate: 2500, taxable: false},
    {id: "lq2", item: "Oak flooring", desc: "", qty: 900, unit: "sf", rate: 8.9, taxable: false},
    {id: "lq3", item: "General conditions", desc: "", qty: 1, unit: "ls", rate: 31072.8, taxable: false}];
  e.status = "approved"; c.estimates.push(e);
  // its schedule of values, as Convert builds it (lineRef estimate:<doc>:<line>)
  c.sov = e.lines.map((l, i) => ({id: "sq" + i, desc: l.item, scheduled: l.qty * l.rate, source: "Contract", order: i, lineRef: `estimate:${e.id}:${l.id}`}));
  const pay = {id: "inq1", type: "invoice", number: "INV-Q-1", title: "Progress billing #1", mode: "sov", date: today(), due: today(), status: "draft", projectId: "",
    lines: c.sov.map((v, i) => ({id: "pl" + i, sovId: v.id, item: v.desc, desc: "", scheduled: v.scheduled, prevPct: 0, pct: 20, taxable: false})),
    discount: {type: "pct", value: 0}, taxRate: 0, retainagePct: 0, terms: "Net 7", memo: "", internal: ""};
  const prog = {id: "inq2", type: "invoice", number: "INV-Q-2", title: "Progress #2", mode: "items", date: today(), due: today(), status: "draft", projectId: "",
    lines: [{id: "il1", item: "Window installation", desc: "", qty: 1, unit: "ls", rate: 7500, taxable: false, estId: e.id, estLineId: "lq1"},
            {id: "il2", item: "General conditions", desc: "", qty: 1, unit: "ls", rate: 3107.28, taxable: false, estId: e.id, estLineId: "lq3"}],
    discount: {type: "pct", value: 0}, taxRate: 0, retainagePct: 0, terms: "", memo: "", internal: ""};
  // a contract of lump sums only
  const c2 = blankClient("Lump Sum Client"); DB.clients.push(c2);
  const e2 = newDoc(c2, "estimate", {template: "construction"}); e2.lines = [{id: "lz1", item: "All work", desc: "", qty: 1, unit: "ls", rate: 100000, taxable: false}]; c2.estimates.push(e2);
  c2.sov = [{id: "sz0", desc: "All work", scheduled: 100000, source: "Contract", order: 0, lineRef: `estimate:${e2.id}:lz1`}];
  const pay2 = {id: "inq3", type: "invoice", number: "INV-Q-3", title: "Progress billing #1", mode: "sov", date: today(), due: today(), status: "draft", projectId: "",
    lines: [{id: "pz", sovId: "sz0", item: "All work", desc: "", scheduled: 100000, prevPct: 0, pct: 10, taxable: false}],
    discount: {type: "pct", value: 0}, taxRate: 0, retainagePct: 0, terms: "", memo: "", internal: ""};
  c.invoices.push(pay, prog); c2.invoices.push(pay2);
  const txt = (cl, d) => cxDocHtml(cl, d, {print: false}).replace(/<[^>]+>/g, " ").replace(/\s+/g, " ");
  return {pay: txt(c, pay), prog: txt(c, prog), lump: txt(c2, pay2), progTotal: docTotal(prog).total, payTotal: docTotal(pay).total};
}"""

async def main():
    c = Checks()
    async with async_playwright() as p:
        b, pg, errs = await open_app(p)
        await sign_in(pg, 'u_billing')
        r = await pg.evaluate(SETUP)
        pay, prog, lump = r['pay'], r['prog'], r['lump']
        c.ok('Quantity' in pay and 'Unit price' in pay, 'the pay application has Quantity and Unit price columns')
        c.ok('15 each' in pay or '15 ea' in pay, f'the window line shows its 15 each: {pay[pay.find("Window"):pay.find("Window") + 120]}')
        c.ok('900 sq ft' in pay or '900 sf' in pay, 'the flooring line shows 900 sq ft')
        c.ok('$8.90' in pay, 'unit prices keep their cents ($8.90)')
        c.ok('Scheduled value' in pay and 'This period' in pay, 'the AIA columns are still there')
        c.ok('Quantity' in prog and 'Unit price' in prog and 'Contract' in prog and 'This invoice' in prog, 'a progress invoice billed against estimate lines shows quantity, unit price, contract and this invoice')
        c.ok('$37,500' in prog and '$7,500' in prog and '20%' in prog, f'the window line shows its $37,500 contract and $7,500 billed (20%): {prog[prog.find("Window"):prog.find("Window") + 140]}')
        c.ok('Lump sum' in prog, 'the lump-sum line says Lump sum')
        c.ok(abs(r['progTotal'] - 10607.28) < 0.01, f"the progress invoice total is unchanged ({r['progTotal']})")
        c.ok(abs(r['payTotal'] - 0.2 * (37500 + 8010 + 31072.8)) < 0.02, f"the pay application total is unchanged ({r['payTotal']})")
        c.ok('Quantity' not in lump, 'a contract of lump sums keeps the plain pay application (no empty Quantity column)')
        c.ok(not errs, f'page errors: {errs[:2]}')
        await b.close()
    raise SystemExit(c.done())

asyncio.run(main())
