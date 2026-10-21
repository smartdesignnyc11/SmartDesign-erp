"""The field never sees money (CLAUDE.md), on the screens a foreman, crew member or driver opens: Documents leaves out
contracts, change orders, purchase orders, invoices and estimates (the list, its tabs, its counts), and the Plans set
check shows no dollar tiles. Found by the foreman expert's review (2026-10-21): a signed estimate under Contracts and
"Our Cost $0" on Drawings. The office still sees all of it. Desktop and phone.
Run: python3 field_money_test.py"""
import asyncio
from harness import async_playwright, open_app, sign_in, Checks

SEE = """() => { setCurrent('p121'); fileFilter = 'all'; view = 'files'; render();
  const list = document.getElementById('file-list'), tabs = [...document.querySelectorAll('#file-filter button')].map(b => b.dataset.f);
  const money = (S.files || []).filter(f => fileIsMoney(f)).map(f => f.name);
  const txt = list ? list.innerText : '';
  return { tabs, moneyOnFile: money.length, shown: money.filter(n => txt.includes(String(n).slice(0, 18))).length, kpis: xsKpis({ before: 1, field: 0, avoided: 1200, ours: 300, avgDays: 2, open: 0 }) } }"""

async def main():
    c = Checks()
    async with async_playwright() as p:
        for phone in (False, True):
            tag = 'phone' if phone else 'desktop'
            b, pg, errs = await open_app(p, phone)
            for uid in ('u_angel', 'u_alberto', 'u_alex'):
                await sign_in(pg, uid)
                r = await pg.evaluate(SEE)
                c.ok(r['moneyOnFile'] >= 1, f'{tag} {uid}: the job has money documents on file to hide ({r["moneyOnFile"]})')
                c.ok(r['shown'] == 0, f'{tag} {uid}: Documents lists no contract, change order, purchase order or invoice ({r["shown"]} shown)')
                c.ok(not any(t in ('contract', 'change-order', 'purchase-order', 'invoice', 'estimate') for t in r['tabs']), f'{tag} {uid}: no money tabs ({r["tabs"]})')
                c.ok('Our Cost' not in r['kpis'] and '$' not in r['kpis'], f'{tag} {uid}: the set check shows no dollar tiles')
            await sign_in(pg, 'u_alan')
            r = await pg.evaluate(SEE)
            c.ok(r['shown'] >= 1 and 'Our Cost' in r['kpis'], f'{tag}: the PM still sees the contract and the cost tiles ({r["shown"]})')
            c.ok(not errs, f'{tag}: page errors {errs[:2]}')
            await b.close()
    print(f'{len(c.fail)} FAILED ({c.n} checks)' if c.fail else f'ALL PASS ({c.n} checks)')
    raise SystemExit(1 if c.fail else 0)

asyncio.run(main())
