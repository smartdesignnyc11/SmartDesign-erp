"""No budget plan yet, and the sample plan a firm's own records received (11-05, financial truth).

What was wrong. budSeed was not a demo seed, so a firm's own records (the team workspace) got the demo's budget plan on
their first budget read: invented revenue and cost by month, three versions and a history stamped by the demo's owner.
A budget figure the firm never made read as theirs, on the device and on the server.

NONE   On a firm's own records with no plan, for the owner and the controller, desktop and the 390px phone: the
       Budget page says No Budget Plan Yet with New Budget Plan; Financial Statements' Budget vs Actual says the same
       (its button plain: the Pack is that page's blue); the Monthly Pack has no "budget $0" and no P&L vs budget
       table; the Weekly Flash has no Budget card; the KPI Income vs Budget reads no figure; Ask's budget questions
       say no plan yet and how to make one; Safe to Spend and the 13-week forecast read; the close checklist reads.
       No page errors, no sideways scroll. New Budget Plan makes one empty draft for the year, with a toast and Open,
       and the Budget page then shows it.
CLEAN  The sample plan nobody touched is removed once, with an audit row by the system saying why; the same plan
       stamped "Owner" (what the team workspaces received) too. One a person edited is kept and the owner gets a task
       to review it. A plan a person made is never touched. A demo keeps its sample plan.
"""
import asyncio, re, sys
from harness import *

NOPLAN = "() => { DB.__liveData = true; delete DB.budgetPlan; save(); return sdSeedsOff(); }"
TXT = "() => ({ t: (document.querySelector('.view.on') || {}).innerText || '', sw: document.scrollingElement.scrollWidth, w: innerWidth, blues: [...document.querySelectorAll('.view.on .btn.primary')].filter(b => b.getClientRects().length).map(b => b.innerText.trim()) })"


async def surfaces(c, pg, tag):
    await go(pg, 'budget')
    r = await pg.evaluate(TXT)
    c.ok('No Budget Plan Yet' in r['t'] and 'New Budget Plan' in r['t'], f'NONE {tag}: the Budget page says No Budget Plan Yet with New Budget Plan: {r["t"][:300]!r}')
    c.ok(not re.search(r'Reforecast Q3|Original 20\d\d|Working Draft', r['t']), f'NONE {tag}: no sample version on the Budget page')
    c.ok(r['sw'] <= r['w'], f'NONE {tag}: the Budget page does not scroll sideways ({r["sw"]} > {r["w"]})')
    for tab in ('budget', 'pack', 'flash'):
        await pg.evaluate("t => { view = 'reports'; repTab = t; render(); }", tab)
        await pg.wait_for_timeout(150)
        r = await pg.evaluate(TXT)
        c.ok(not re.search(r'budget [−-]?\$0(\.00)?\b', r['t'], re.I), f"NONE {tag}: Reports {tab} shows no $0 budget: {[l for l in r['t'].splitlines() if re.search(r'budget', l, re.I)][:4]}")
        c.ok(r['sw'] <= r['w'], f'NONE {tag}: Reports {tab} does not scroll sideways')
        c.ok(len(r['blues']) <= 1, f'NONE {tag}: Reports {tab} has at most one blue button: {r["blues"]}')
    r = await pg.evaluate("() => { view = 'reports'; repTab = 'budget'; render(); return (document.querySelector('.view.on') || {}).innerText || ''; }")
    c.ok('No Budget Plan Yet' in r, f'NONE {tag}: Budget vs Actual says No Budget Plan Yet')
    r = await pg.evaluate("() => { view = 'reports'; repTab = 'flash'; render(); return !!document.querySelector('.view.on .bud-flash'); }")
    c.ok(not r, f'NONE {tag}: the Weekly Flash has no Budget card')
    r = await pg.evaluate("""async () => { const k = kpiEval('budgetVar', 'ty'); const A = [];
      for (const q of ['how are we doing against the budget', 'budget variance this month']) { const a = await Promise.resolve(paAsk(q)); A.push([a && a.headline, a && a.note]); }
      const S = safeToSpend(), F = cashForecast(); let close = 'ok'; try { closeChecklist(today().slice(0, 7)); } catch (e) { close = e.message; }
      return { kpi: k && k.cur, fmt: k && kpiFmt('budgetVar', k.cur), ask: A, safe: S.safe, low: F.low, close }; }""")
    c.ok(r['kpi'] is None and r['fmt'] == '—', f'NONE {tag}: Income vs Budget reads no figure: {r["kpi"]} {r["fmt"]}')
    c.ok(all(a[0] and re.search(r'no .*budget', a[0], re.I) and 'New Budget Plan' in (a[1] or '') for a in r['ask']), f'NONE {tag}: Ask says no plan yet and how to make one: {r["ask"]}')
    c.ok(isinstance(r['safe'], (int, float)) and isinstance(r['low'], (int, float)) and r['close'] == 'ok', f'NONE {tag}: Safe to Spend, the forecast and the close checklist read: {r}')


async def main():
    c = Checks()
    async with async_playwright() as p:
        for phone in (False, True):
            dev = 'phone' if phone else 'desktop'
            for uid in ('u_owner', 'u_controller'):
                tag = f'{dev} {uid}'
                b, pg, errs = await open_app(p, phone)
                await sign_in(pg, uid)
                off = await pg.evaluate(NOPLAN)
                c.ok(off, f'{tag}: the firm\'s own records (seeds off)')
                await surfaces(c, pg, tag)
                if uid == 'u_owner' and not phone:
                    await go(pg, 'budget')
                    await pg.locator('.view.on [data-budnewplan]').first.click(); await pg.wait_for_timeout(300)
                    await pg.locator('#mbm #mbm-ok').first.click(); await pg.wait_for_timeout(500)
                    r = await pg.evaluate("""() => { const P = DB.budgetPlan, v = P.versions[0]; return { n: P.versions.length, name: v && v.name, lines: v && Object.keys(v.lines).length, active: v && P.active[v.year] === v.id,
                      by: v && v.createdBy, toast: document.getElementById('toast').innerText, page: (document.querySelector('.view.on') || {}).innerText.slice(0, 400) }; }""")
                    c.ok(r['n'] == 1 and r['lines'] == 0 and r['active'] and r['by'] == OWNER, f'NONE {tag}: New Budget Plan makes one empty draft, by the owner: {r}')
                    c.ok('created' in r['toast'] and 'Open' in r['toast'], f'NONE {tag}: its toast says so, with Open: {r["toast"]!r}')
                    c.ok('No Budget Plan Yet' not in r['page'], f'NONE {tag}: the Budget page shows the plan: {r["page"][:200]!r}')
                c.ok(not errs, f'{tag}: no page errors: {errs[:3]}')
                await b.close()

        # the cleanup
        b, pg, errs = await open_app(p)
        await sign_in(pg, 'u_owner')
        r = await pg.evaluate("() => { const P = budPlan(); return { n: P.versions.length, checked: P.sampleChecked || '' }; }")
        c.ok(r['n'] == 3 and not r['checked'], f'CLEAN: the demo keeps its sample plan: {r}')
        SNAP = "() => { window.__sample = JSON.stringify(DB.budgetPlan); return true; }"
        await pg.evaluate(SNAP)
        RUN = """(how) => { const P = JSON.parse(window.__sample); delete P.sampleChecked;
          if (how === 'Owner') { P.versions.forEach(v => { v.createdBy === DEMO_OWNER && (v.createdBy = 'Owner'); v.lockedBy === DEMO_OWNER && (v.lockedBy = 'Owner'); }); P.audit.forEach(a => a.by === DEMO_OWNER && (a.by = 'Owner')); }
          DB.budgetPlan = P; DB.__liveData = true; const n0 = DB.audit.length, t0 = (asFirmTasks() || []).length;
          if (how === 'edited') { DB.__liveData = false; budSetCell(P.versions.find(v => v.id === 'bv_draft'), 'ent1', '7100', 10, 1300); DB.__liveData = true; }
          if (how === 'mine') { P.versions = [{ id: 'bv_mine', name: '2026 Plan', kind: 'draft', year: '2026', status: 'open', createdOn: '2026-08-01', createdBy: 'Maren Holloway', lines: { 'ent1|7100': Array(12).fill(1000) }, jobs: {} }]; P.audit = []; P.active = { '2026': 'bv_mine' }; }
          const after = budPlan(), rows = DB.audit.slice(n0).filter(a => a.kind === 'budget' && a.refId === 'sample-plan');
          const tasks = (asFirmTasks() || []).slice(t0).filter(t => /sample plan/.test(t.title));
          return { n: after.versions.length, checked: after.sampleChecked, rows: rows.map(a => [a.action, a.by, a.note]), tasks: tasks.map(t => [t.title, t.assignee]) }; }"""
        r = await pg.evaluate(RUN, 'demo')
        c.ok(r['n'] == 0 and r['checked'] == 'removed' and r['rows'] and r['rows'][0][0] == 'removed' and r['rows'][0][1] == 'system' and 'removed the sample budget plan that setup added' in r['rows'][0][2] and 'nobody had edited it' in r['rows'][0][2],
             f'CLEAN: the untouched sample plan is removed, with an audit row by the system and the reason: {r}')
        r = await pg.evaluate(RUN, 'Owner')
        c.ok(r['n'] == 0 and r['checked'] == 'removed', f'CLEAN: the same plan stamped "Owner" (what team workspaces received) is removed: {r}')
        r = await pg.evaluate(RUN, 'edited')
        c.ok(r['n'] == 3 and r['checked'] == 'kept' and r['rows'] and r['rows'][0][0] == 'kept' and r['tasks'] and r['tasks'][0][1] == OWNER,
             f'CLEAN: an edited sample plan is kept, and the owner gets a task to review it: {r}')
        r = await pg.evaluate(RUN, 'mine')
        c.ok(r['n'] == 1 and r['checked'] == 'no sample' and not r['rows'] and not r['tasks'], f'CLEAN: a plan a person made is not touched: {r}')
        r = await pg.evaluate("() => { budSampleCleanup(); return [DB.budgetPlan.versions.length, DB.budgetPlan.sampleChecked]; }")
        c.ok(r == [1, 'no sample'], f'CLEAN: the check runs once per plan: {r}')
        c.ok(not errs, f'CLEAN: no page errors: {errs[:3]}')
        await b.close()
    return c.done()

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
