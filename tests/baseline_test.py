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
        # leaks (BACKLOG 1.5 #2): a job is held per line, never whole. 121 State's measured framing and electrical
        # ($12,651.25) were held because the job is billed ahead on the WIP schedule; they now propose an application:
        # ready to bill 20980 / 2 rows / 1 held -> 33631.25 / 3 rows / 0 held, and Billing's badge 2 -> 3.
        # leaks (BACKLOG 1.5 #1): the windows line floats $13,968.74 of materials bought and delivered beyond what
        # the Kleins have been billed for it; it is a row to bill as stored materials: 33631.25 / 3 -> 47599.99 / 4,
        # and Billing's badge 3 -> 4.
        # chain (2026-10-11): what a line has billed is read in dollars, line by line, not as the sum of its percentages
        # rounded to two places (51.67% of $37,800 overstated the windows line's billing by $1.25): the floated windows
        # row is $13,969.99, not $13,968.74, so 47599.99 -> 47601.24. Less the seed's 6.5 designer hours dated 9/4
        # (a day not yet worked, read as ready to bill), removed by pilotfix2: 46301.24.
        c.ok(r['rtb'] == 46301.24 and r['rtbN'] == 4 and r['held'] == 0, f"ready to bill {r['rtb']} / {r['rtbN']} rows / {r['held']} held")
        # Purchasing 10 -> 17 (procurement P1, 2026-10-25): the badge is the Buy Board's one reader, late or due to order
        # this week (PRED.buyNeeds, the coordinator's Buy Board chip on Today), no longer "late to order, held, due this
        # week or waiting on a decision". 16 late: 12 not ordered by their order-by date (the 6 it counted before, plus 2
        # approved FF&E items, 2 change-order lines and the 2 sub scopes, demolition and scaffold, with no sub contracted)
        # and 4 ordered with a promise after the site needs them (appliances, insulation, white oak flooring, Carlos's
        # millwork); and 1 due this week (the acknowledged tape-and-plastic request; the unacknowledged studs are an
        # Approvals card). The 4 waiting on a decision and not yet late left it.
        c.ok(r['badges'] == {'jobs': 2, 'sales': 4, 'buy': 17, 'money': 6, 'billing': 4}, f"rail badges {r['badges']}")
        c.ok('$0' in r['owe'], f"AP owed: {r['owe']}")
        c.ok('Tino' in r['po'] and '8,010' in r['po'], f"PO lookup: {r['po']}")
        c.ok(not r['users'], f"missing demo users {r['users']}")
        c.ok(not errs, f'errors {errs[:3]}')
        await b.close()
    sys.exit(c.done())
asyncio.run(main())
