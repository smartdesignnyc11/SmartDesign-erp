"""undated_job: the app opens and every job page renders on a job whose schedule tasks have no dates or no deps
(10-26: a bare job stopped the hosted app at boot in computeCPM, getDay of null; Asana imports and hand-made jobs
arrive with no dates)."""
import asyncio
from harness import *

async def main():
    c = Checks()
    async with async_playwright() as p:
        for phone in (False, True):
            b, pg, errs = await open_app(p, phone)
            await sign_in(pg, 'u_alan')
            await pg.evaluate("""() => { const P = blankProject ? blankProject('Bare Test Job') : null;
              const j = P || { id: 'pbare', name: 'Bare Test Job', project: {}, tasks: [] };
              j.tasks = [{ id: 'tb1', name: 'No dates', status: 'planned' }, { id: 'tb2', name: 'Deps on an undated task', status: 'planned', deps: ['tb1'] }];
              if (!DB.projects.includes(j)) DB.projects.push(j); DB.currentId = j.id; return saveNow ? saveNow() : save(); }""")
            # the job arrives the way a sync or an import brings it: in the stored records, read at the next boot
            await pg.reload(); await pg.wait_for_timeout(1500); await sign_in(pg, 'u_alan')
            n0 = len(errs)
            for v in ('dash', 'sched', 'tasks', 'costs', 'home', 'ovjobs'):
                await go(pg, v); await pg.wait_for_timeout(250)
            await pg.reload(); await pg.wait_for_timeout(1500)
            booted = await pg.evaluate("() => !!document.querySelector('.view.on')")
            c.ok(booted and len(errs) == n0, f"{'phone' if phone else 'desktop'}: the app opens and the job pages render on an undated job ({errs[n0:][:2]})")
            await b.close()
    c.done()

asyncio.run(main())
