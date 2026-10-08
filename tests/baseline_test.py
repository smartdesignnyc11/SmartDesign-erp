"""Pins the figures the round-4 build produced (app day 2026-09-03, owner). If a change moves one,
it must be on purpose: update the number here and say why in the commit."""
import asyncio, sys
from harness import *
async def main():
    c = Checks()
    async with async_playwright() as p:
        b, pg, errs = await open_app(p)
        await sign_in(pg, 'u_owner')
        r = await pg.evaluate("""() => {
          const pl = companyPL(['2026-01-01', today()]);
          const rtb = readyToBill();
          return {
            today: today(),
            income: Math.round(pl.income), net: Math.round(pl.net),
            rtb: rtb.amount, rtbN: rtb.n, held: rtb.held.length,
            badges: Object.fromEntries(['jobs','sales','buy','money','billing'].map(g => [g, needs(g)])),
            owe: paAsk('how much do we owe vendors').headline,
            po: paAsk('PO-2026-047').headline,
            users: ['u_owner','u_alan','u_chen','u_angel','u_alberto','u_alex','u_klein','u_cambri','u_sarah','u_billing','u_controller']
                     .filter(u => !(DB.users || []).some(x => x.id === u)),
          };
        }""")
        c.ok(r['today'] == '2026-09-03', f"app day {r['today']}")
        # truthpct (BACKLOG §1.2): the EAC rolls up by estimate line, so 121 State earns $1,532.47 less this year
        # (EAC $384,087.50 -> $388,887.50). Income 144292 -> 142759, net -3797 -> -5330.
        c.ok(r['income'] == 142759, f"YTD income {r['income']} (was 144292 before truthpct)")
        c.ok(r['net'] == -5330, f"YTD net {r['net']} (was -3797 before truthpct)")
        c.ok(r['rtb'] == 20980 and r['rtbN'] == 2 and r['held'] == 1, f"ready to bill {r['rtb']} / {r['rtbN']} rows / {r['held']} held")
        c.ok(r['badges'] == {'jobs': 2, 'sales': 4, 'buy': 10, 'money': 6, 'billing': 2}, f"rail badges {r['badges']}")
        c.ok('$0' in r['owe'], f"AP owed: {r['owe']}")
        c.ok('Tino' in r['po'] and '8,010' in r['po'], f"PO lookup: {r['po']}")
        c.ok(not r['users'], f"missing demo users {r['users']}")
        c.ok(not errs, f'errors {errs[:3]}')
        await b.close()
    sys.exit(c.done())
asyncio.run(main())
