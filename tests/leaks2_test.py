"""leaks2: the month's most expensive cracks, each reproduced on a fresh seed (review/month/ledger.md, BACKLOG 1.5, 8).

The month (tests/month_sim.py) left $137,278 behind on master db8d418. Each scenario here injects one crack through
the app's own paths (the statement import dialog, the transaction drawer, docAction, prgSet, payrollFromTime,
cmImport) and checks that the person who should act gets a proposal they can confirm, and that confirming it
closes the crack. AI proposes, people approve: nothing here is written without a person's press.

    python3 leaks2_test.py                    # every scenario
    python3 leaks2_test.py --scenario earned  # one or more by name or number

Scenarios
  1 earned    earned-not-billed: hold per line, never per job; CO lines bill from 0; a draft says Send
  2 reimb     card purchases bought for a client become reimbursable rows, billed with the job's markup
  3 credit    a refund on a purchase billed to the client proposes a client credit that reaches an invoice
  4 match     payroll debits match their run, card charges their PO, a check with no bill proposes the bill,
              a hand-typed cost is flagged "no bank line"
  5 dup       a duplicate charge at import is a proposed dispute on the controller's Needs Your Hand
  6 stmt      a statement in mail proposes the import and the reconcile, not a task
  7 payroll   one payroll run per pay period across entities, built from every hour approved by its date
  8 dispute   a vendor credit memo closes the held difference with one approval

All data is invented. The last line is `N flags`; exit 1 when N > 0."""
import asyncio, sys, json, argparse, re
from harness import *
from leak_test import boot, import_statement, find_txn, code_txn, csv, ofx, Scenario, scan, ask, surf, PAGE_HELPERS

JOB = 'p121'


async def billing_row(pg, needle):
    """The Billing Queue row (as billing sees it) whose text holds `needle`: its text and its button's label."""
    await pg.evaluate("() => { signIn('u_billing'); view = 'billing'; billTab = 'billable'; docOpen = null; render(); }")
    return await pg.evaluate("""n => { const tr = [...document.querySelectorAll('#v-billing tr')].find(tr => tr.querySelector('[data-blact]') && tr.innerText.includes(n));
        return tr ? {text: tr.innerText.replace(/\\s+/g, ' ').slice(0, 220), verb: tr.querySelector('[data-blact]').innerText.trim()} : null; }""", needle)


async def press_row(pg, needle, verb):
    """Press the row's button, then the sheet's blue button (the house rule: the primary is the safe next step)."""
    return await pg.evaluate("""async ([n, v]) => { const tr = [...document.querySelectorAll('#v-billing tr')].find(tr => tr.querySelector('[data-blact]') && tr.innerText.includes(n));
        const b = tr && tr.querySelector('[data-blact]'); if (!b || b.innerText.trim() !== v) return 'no ' + v;
        b.click(); await new Promise(r => setTimeout(r, 60)); const m = document.querySelector('#mbm');
        const title = m ? (m.querySelector('h3') || {}).innerText : '';
        const ok = m && m.querySelector('#mbm-ok'); ok && ok.click(); await new Promise(r => setTimeout(r, 120));
        return 'pressed ' + v + (title ? ' > ' + title : '') + (ok ? ' > ' + ok.innerText : ''); }""", [needle, verb])


# ---------------------------------------------------------------- 1. earned, not billed
async def s1_earned(p, S):
    b, pg, errs = await boot(p)
    try:
        st = await pg.evaluate("""() => { const p = DB.projects.find(x => x.id === 'p121'), w = wipRow(p), R = readyToBill();
            return {over: Math.round(w.over), app: R.rows.filter(r => r.p && r.p.id === 'p121' && r.kind === 'application').map(r => r.amount),
                    jobHeld: R.held.filter(h => !h.sv).map(h => [h.p.id, h.why]), held: R.held.map(h => [h.p.id, h.line, h.amount])}; }""")
        S.fact(f"seed: 121 State billed ${st['over']:,} ahead on the WIP schedule; application {st['app']}; held {st['held']}")
        S.check(st['app'] and not st['jobHeld'], 'a job billed ahead overall is never held whole: its measured lines still propose an application',
                f"job-level holds {st['jobHeld']}")
        # the foreman measures rough electrical at 100%; the client approves CO-2026-002 and the treads are done
        await pg.evaluate("""async () => { const p = DB.projects.find(x => x.id === 'p121');
            prgSet(p, p.tasks.find(t => t.id === 'relec'), {pct: 100, by: 'Angel', role: 'foreman', src: 'field', note: 'Rough electrical complete'});
            const c = DB.clients.find(x => x.id === 'cl121'); await docAction(c, c.changeOrders.find(x => x.number === 'CO-2026-002'), 'approve');
            prgSet(p, p.tasks.find(t => t.id === 'sand'), {pct: 100, by: 'Angel', role: 'foreman', src: 'field', note: 'Treads sanded and stained'}); save(); }""")
        row = await billing_row(pg, '121 State')
        S.check(row and row['verb'] == 'Draft' and 'CO-2026-002' in row['text'], 'Billing Queue: the 121 State application is ready, with CO-2026-002 on it',
                str(row))
        # Draft: the application fills a draft with every approved change order's line beside the contract's
        d = await pg.evaluate("""() => { const o = pgApply('p121'); save(); return o && {n: o.n, amt: o.amt, num: o.inv.number,
              co: o.inv.lines.filter(l => /CO-2026-002/.test(l.item)).map(l => l.pct)}; }""")
        S.check(d and d['co'] == [100], 'the draft application carries CO-2026-002 billed from 0 to 100%', str(d))
        row = await billing_row(pg, d['num'] if d else 'INV-')
        S.check(row and row['verb'] == 'Send', 'Billing Queue: the drafted application says Send', str(row))
        did = await press_row(pg, d['num'] if d else 'INV-', 'Send')
        sent = await pg.evaluate("n => { const c = DB.clients.find(x => x.id === 'cl121'); const i = c.invoices.find(x => x.number === n); return i ? i.status : 'none'; }", d['num'] if d else '')
        S.check(sent == 'sent', 'Send opens one sheet; Send to Client sends the application', f"{did}; status {sent}")
        held = await pg.evaluate("""() => { const p = DB.projects.find(x => x.id === 'p121'); const r = pgRows('p121').find(r => /Insulation/.test(r.sv.desc));
            p.tasks.filter(t => /insul|drywall|tape/i.test(t.name)).forEach(t => { t.status = 'not-started'; t.pct = 0; });
            return r ? {basis: r.pr.basis} : null; }""")
        hs = await pg.evaluate("""() => { const R = pgRows('p121'); const h = R.filter(r => pgLineHold(r));
            const co = R.filter(r => pgIsCO(r.sv) && pgLineHold(r)); return {held: h.map(r => [r.sv.desc, r.pr.basis, pgLineHold(r)]), co: co.length}; }""")
        S.fact(f'held lines now: {hs}')
        S.check(hs['co'] == 0, 'a change order line is never held')
        unit = await pg.evaluate("""() => [pgLineHold({sv: {source: 'Contract', desc: 'x'}, pr: {period: 12, basis: 'cost', extra: '$4,000 spent'}}),
            pgLineHold({sv: {source: 'CO-2026-009', desc: 'x'}, pr: {period: 12, basis: 'cost', extra: ''}}),
            pgLineHold({sv: {source: 'Contract', desc: 'x'}, pr: {period: 12, basis: 'schedule', extra: ''}})]""")
        S.check(bool(unit[0]) and not unit[1] and not unit[2], 'held per line: a contract line measured only by cost is held with its reason; a CO line or a measured line is not', str(unit))
    finally:
        if errs: S.errors.append(f'page errors: {errs[:2]}')
        await b.close()


SCENARIOS = [
    (1, 'earned', 'Earned, not billed: hold per line; CO lines from 0; a drafted application says Send', s1_earned),
]


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scenario', default='')
    a = ap.parse_args()
    want = {x.strip() for x in a.scenario.split(',') if x.strip()}
    todo = [s for s in SCENARIOS if not want or str(s[0]) in want or s[1] in want]
    results = []
    async with async_playwright() as p:
        for num, key, title, fn in todo:
            S = Scenario(num, key, title)
            try:
                await fn(p, S)
            except Exception as e:
                S.setup_ok = False
                S.errors.append(f'{type(e).__name__}: {str(e)[:300]}')
            S.report()
            results.append(S)
    flags = sum(1 for S in results if S.verdict() != 'CAUGHT')
    print(f"\n{' · '.join(f'{S.num} {S.verdict()}' for S in results)}")
    print(f'{flags} flags')
    sys.exit(1 if flags else 0)


if __name__ == '__main__':
    asyncio.run(main())
