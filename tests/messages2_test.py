"""Messages, phase 2 (BACKLOG §1.21): checked as the people who use it.

  1. The crew on a job: the PM puts a person on a job from the job's team thread (Change Crew), the toast opens the
     thread, and from then on that person reads the job's thread and nobody else in the field does. The foreman cannot
     change a crew. Project Settings shows the same line. A field person's local build lists only their jobs' threads.

  python3 messages2_test.py        # prints ALL PASS (n checks) or each failure
"""
import asyncio, re
from harness import *


async def fresh(p, uid, phone=False):
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, uid)
    return b, pg, errs


async def keys_for(pg, uid):
    return await pg.evaluate("u => { signIn(u); render(); return msgThreadsFor().map(T => T.key); }", uid)


# ------------------------------------------------------------------------------------------------ 1. the crew
async def t_crew(c, p):
    b, pg, errs = await fresh(p, 'u_alan')
    first = await pg.evaluate("() => Object.fromEntries(DB.projects.map(p => [p.id, p.team]))")
    c.ok(first.get('p121') and set(first['p121']) == {'u_angel', 'u_alberto', 'u_satish', 'u_alex'}, f"crew: 121 State's first crew is the people who clocked, logged and asked there ({first.get('p121')})")
    c.ok(first.get('p206') == ['u_alberto', 'u_alex'] and first.get('p140') == [], f"crew: 206 Lenox has its two, the design job nobody ({first})")
    for u, want in (('u_angel', {'job:p121'}), ('u_satish', {'job:p121'}), ('u_alberto', {'job:p121', 'job:p206'})):
        k = await keys_for(pg, u)
        jobs = {x for x in k if x.startswith('job:') or x.startswith('client:')}
        c.ok(jobs == want, f"crew: {u}'s local build lists only the threads of the jobs they are on ({sorted(jobs)})")
    # the PM opens 206 Lenox's thread: the crew line and Change Crew
    await sign_in(pg, 'u_alan')
    await pg.evaluate("() => { setCurrent('p206'); msgOpen('job:p206'); }")
    await pg.wait_for_timeout(200)
    head = await pg.evaluate("() => document.getElementById('msg-head').innerText")
    c.ok('Crew:' in head and 'Alberto, Alex' in head and 'Change Crew' in head, f"crew: the job's thread names its crew, with Change Crew for the PM ({head!r})")
    await pg.click('[data-msgcrew="p206"]')
    await pg.wait_for_timeout(200)
    modal = await pg.evaluate("() => (document.getElementById('mbm') || {}).innerText || ''")
    c.ok('Crew on' in modal and 'Angel' in modal and 'Satish' in modal and 'Chen' not in modal, f'crew: the picker lists the people in the field only ({modal[:200]!r})')
    await pg.check('#mbm [data-f="c_u_angel"]')
    await pg.uncheck('#mbm [data-f="c_u_alex"]')
    await pg.click('#mbm #mbm-ok')
    await pg.wait_for_timeout(300)
    r = await pg.evaluate("() => ({ team: DB.projects.find(p => p.id === 'p206').team, toast: document.getElementById('toast').innerText, head: document.getElementById('msg-head').innerText })")
    c.ok(r['team'] == ['u_angel', 'u_alberto'], f"crew: Save Crew puts Angel on and takes Alex off ({r['team']})")
    c.ok('Crew on' in r['toast'] and 'Angel' in r['toast'] and 'Open' in r['toast'], f"crew: the toast says who is on it, with Open ({r['toast']!r})")
    c.ok('Angel, Alberto' in r['head'], f"crew: the thread's crew line reads the new crew ({r['head']!r})")
    k = await keys_for(pg, 'u_angel')
    c.ok('job:p206' in k, f'crew: Angel now has the 206 Lenox thread ({k})')
    k = await keys_for(pg, 'u_alex')
    c.ok('job:p206' not in k and 'job:p121' in k, f'crew: Alex no longer has it, and keeps 121 State ({k})')
    ok_open = await pg.evaluate("() => { signIn('u_alex'); render(); return !!msgThread('job:p206'); }")
    c.ok(not ok_open, 'crew: Alex cannot open the thread by its key either')
    # the foreman sees the crew but cannot change it
    await sign_in(pg, 'u_angel')
    await pg.evaluate("() => { setCurrent('p206'); msgOpen('job:p206'); }")
    await pg.wait_for_timeout(200)
    r = await pg.evaluate("() => { const h = document.getElementById('msg-head').innerText; msgTeamEdit('p206'); return { h, modal: !!document.getElementById('mbm'), toast: document.getElementById('toast').innerText, team: DB.projects.find(p => p.id === 'p206').team } }")
    c.ok('Crew:' in r['h'] and 'Change Crew' not in r['h'], f"crew: the foreman reads who is on his job, with no Change Crew ({r['h']!r})")
    c.ok(not r['modal'] and 'PM or the owner' in r['toast'], f"crew: and cannot change it ({r['toast']!r})")
    # Project Settings: the same line, the same door
    await sign_in(pg, 'u_alan')
    await pg.evaluate("() => { setCurrent('p121'); view = 'proj'; render(); }")
    await pg.wait_for_timeout(200)
    t = await pg.evaluate("() => (document.getElementById('p-crew') || {}).innerText || ''")
    c.ok('Crew on This Job' in t and 'Satish' in t and 'Change Crew' in t, f'crew: Project Settings shows the crew with Change Crew ({t!r})')
    # the audit trail records who changed a crew
    a = await pg.evaluate("() => (DB.audit || []).filter(x => x.action === 'crew' || x.field === 'crew' || JSON.stringify(x).includes('set the crew')).length")
    c.ok(a >= 1, f'crew: the change is on the audit trail ({a})')
    c.ok(not errs, f'crew: no page errors {errs[:2]}')
    await b.close()
    # the phone: the crew line fits, no sideways scroll
    b, pg, errs = await fresh(p, 'u_alan', phone=True)
    await pg.evaluate("() => { setCurrent('p121'); msgOpen('job:p121'); }")
    await pg.wait_for_timeout(250)
    r = await pg.evaluate("() => { const b = document.querySelector('[data-msgcrew]'); const r = b ? b.getBoundingClientRect() : {}; return { sw: document.documentElement.scrollWidth, h: r.height || 0, right: r.right || 0 } }")
    c.ok(r['sw'] <= 390 and r['h'] >= 30 and r['right'] <= 390, f'crew: on the phone the line fits and Change Crew is on screen ({r})')
    c.ok(not errs, f'crew phone: no page errors {errs[:2]}')
    await b.close()


TESTS = [t_crew]


async def main():
    c = Checks()
    async with async_playwright() as p:
        for t in TESTS:
            try:
                await t(c, p)
            except Exception as e:
                c.ok(False, f'{t.__name__}: {type(e).__name__}: {str(e)[:300]}')
    return c.done()

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
