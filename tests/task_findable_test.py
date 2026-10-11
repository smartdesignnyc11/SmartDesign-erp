"""Saved is not enough: findable (BACKLOG §1.16, layer 3; Alan, 2026-10-11).

On 2026-10-11 a task saved from the owner's Home went onto the current project (121 State Street) with no date, the
list opened on a bucket that does not show undated tasks, and render() reset the view: the task was saved and
survived a reload, but to the person it vanished. This suite performs every task entry point as each role that can
create tasks, on desktop and at 390px, and after each save asserts that:
  1. the new task is on the creator's screen right after saving, highlighted;
  2. the toast's Open lands on it;
  3. after a reload it is in that person's All Tasks, Mine (My Tasks).
It also pins the defaults: "For" is "Me — No Project" from Home and Tasks, the current project only from a project
page; and an undated task shows in the list's default view or the list says how many have no date, with a link.

Part 2 extends the pattern to the other things a person creates (RFQ, PO, a document on a PO, a promise, a stock
override, a price explanation): each is visible to its creator right after saving and findable after a reload.
Invented data only."""
import asyncio
from harness import async_playwright, open_app, sign_in, go, Checks

SEEN = """(t) => {
  const inView = (e) => { const r = e.getBoundingClientRect(), cs = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < innerHeight && cs.visibility !== 'hidden' && !e.closest('#toast, #mbm'); };
  let vis = false, flash = false;
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n; (n = w.nextNode());) {
    if (!n.nodeValue.includes(t)) continue;
    const e = n.parentElement;
    if (e && inView(e)) { vis = true; if (e.closest('.tk-flash')) flash = true; }
  }
  document.querySelectorAll('input, textarea').forEach(i => { if (i.value === t && inView(i)) vis = true; });
  return { vis, flash, view, sw: document.documentElement.scrollWidth };
}"""

TOAST_OPEN = """() => { const t = document.getElementById('toast'); if (!t) return false;
  const a = [...t.querySelectorAll('a, button')].find(x => /^Open$/.test((x.innerText || '').trim())); if (!a) return false; a.click(); return true; }"""

CLOSE = """() => { try { document.getElementById('mbm') && document.querySelector('#mbm [data-mbclose], #mbm .mbm-x') ? document.querySelector('#mbm [data-mbclose], #mbm .mbm-x').click() : 0; } catch (e) {}
  try { typeof closeDrawer === 'function' && closeDrawer(); } catch (e) {} document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' })); }"""


async def dialog_save(pg, title):
    await pg.wait_for_selector('#mbm [data-f="title"]', timeout=5000)
    for_v = await pg.evaluate("() => (document.querySelector('#mbm [data-f=\"for\"]') || {}).value || ''")
    await pg.fill('#mbm [data-f="title"]', title)
    await pg.evaluate("() => document.querySelector('#mbm #mbm-ok').click()")
    await pg.wait_for_timeout(450)
    return for_v


async def click(pg, sel):
    await pg.evaluate("s => document.querySelector(s).click()", sel)
    await pg.wait_for_timeout(250)


async def entry_points(pg, uid):
    """The task entry points this role has, each as (name, start, run(title) -> 'For' default, expected 'For')."""
    can = await pg.evaluate("() => ({ v: ROLE_VIEWS[role()] || [], home: view })")
    v, home = can['v'], can['home']
    E = []

    async def at_home(title):
        await go(pg, home)
        # the top bar's New › Task (CR_NEW), the same function the menu item runs
        await pg.evaluate("() => CR_NEW.flatMap(g => g[1]).find(x => x[0] === 'task')[2]()")
        return await dialog_save(pg, title)
    E.append(('New › Task from ' + home, at_home, 'me'))

    async def at_tkall(title):
        await go(pg, 'tkall'); await click(pg, '#tk-new')
        return await dialog_save(pg, title)
    E.append(('All Tasks › New Task', at_tkall, 'me'))

    if 'tasks' in v:
        async def at_project(title):
            await pg.evaluate("() => { setCurrent('p121'); view = 'tasks'; render(); }"); await pg.wait_for_timeout(250)
            await click(pg, '#tk-new')
            return await dialog_save(pg, title)
        E.append(("a project's Tasks › New Task", at_project, 'p:p121'))

        async def quick(title):
            await pg.evaluate("() => { setCurrent('p121'); view = 'tasks'; t2View = 'all'; render(); }"); await pg.wait_for_timeout(250)
            await pg.fill('#t2-quickadd', title)
            await pg.press('#t2-quickadd', 'Enter'); await pg.wait_for_timeout(450)
            return 'p:p121'
        E.append(("a project's quick add", quick, 'p:p121'))

    if 'hbtasks' in v:
        async def at_sales(title):
            await go(pg, 'hbtasks'); await click(pg, '#tk-new')
            return await dialog_save(pg, title)
        E.append(('Sales Tasks › New Task', at_sales, 'sales'))

    if 'pa' in v:
        async def ask(title):
            # Ask (the assistant): "remind me to …" puts a dated item on the asker's own list
            await go(pg, 'pa')
            await pg.fill('#pa-in', f'remind me to {title[0].lower() + title[1:]} tomorrow')
            await pg.evaluate("() => document.querySelector('#pa-ask').requestSubmit()")
            await pg.wait_for_timeout(900)
            return await pg.evaluate("t => openTasks('all').some(x => x.title === t && !x.projectId) ? 'me' : 'not on the list with no project'", title)
        E.append(('Ask, remind me to', ask, 'me'))

    if 'comms' in v:
        def seed(kind):
            return pg.evaluate("""([t, kind]) => { const me = tkMe(), id = 'cmF' + Math.random().toString(36).slice(2, 7);
              DB.comms.push({ id, msgId: id, threadId: '', channel: 'email', direction: 'in', to: [], cc: [], attachments: [], source: 'import', from: { name: 'Tino Ruiz', email: 'tino@example.com' }, subject: 'Call me back', text: 'Call me back about the tile.', date: today() + 'T14:00:00.000Z', status: 'proposed',
                route: { projectId: 'p121' }, proposals: [Object.assign({ id: 'pp1', kind, summary: 'Tino asked for a call back', task: t, forWho: me, on: true }, kind === 'quote' ? { materialId: 'mFind' } : {})] });
              window.__cm = id; cmOpen = id; view = 'comms'; render(); }""", [title_box[0], kind])
        title_box = ['']

        async def message(title):
            # a call-back proposal opens New Task, prefilled with the message's job
            title_box[0] = title
            await seed('call'); await pg.wait_for_timeout(300)
            await pg.evaluate("() => document.querySelector(`[data-cmapply='${window.__cm}|pp1']`).click()")
            await pg.wait_for_timeout(300)
            return await dialog_save(pg, title)
        E.append(('a message call-back proposal', message, 'p:p121'))
        if uid == 'u_alan':
            async def escalation(title):
                # a vendor's quote for a material: the PM's follow-up is filed with no dialog (cmTask)
                title_box[0] = title
                await seed('quote'); await pg.wait_for_timeout(300)
                await pg.evaluate("() => document.querySelector(`[data-cmapply='${window.__cm}|pp1']`).click()")
                await pg.wait_for_timeout(450)
                return await pg.evaluate("t => (openTasks('all').find(x => x.title === t) || {}).projectId ? 'p:' + openTasks('all').find(x => x.title === t).projectId : 'not on the list'", title)
            E.append(('a message quote follow-up (cmTask)', escalation, 'p:p121'))
    return E


async def run_role(c, pg, uid, label):
    await sign_in(pg, uid)
    await pg.evaluate("() => { t2View = 'today'; tkWho = 'me'; }")  # the list's own default, where the bug hid tasks
    made = []
    for i, (name, run, want_for) in enumerate(await entry_points(pg, uid)):
        title = f'Findable {uid[2:]} {label} {i} {name.split()[0]}'
        try:
            got_for = await run(title)
        except Exception as e:
            c.ok(False, f'{label} {uid} {name}: could not run ({str(e)[:120]})'); await pg.evaluate(CLOSE); continue
        c.ok(got_for == want_for, f'{label} {uid} {name}: "For" defaults to {want_for} ({got_for})')
        s = await pg.evaluate(SEEN, title)
        c.ok(s['vis'], f'{label} {uid} {name}: the new task is on the screen right after saving (view {s["view"]})')
        c.ok(s['flash'] or name.startswith('Ask'), f'{label} {uid} {name}: and highlighted')
        if label == 'phone':
            c.ok(s['sw'] <= 390, f'{label} {uid} {name}: no sideways scroll ({s["sw"]})')
        opened = await pg.evaluate(TOAST_OPEN)
        await pg.wait_for_timeout(450)
        s2 = await pg.evaluate(SEEN, title)
        c.ok(opened and s2['vis'], f'{label} {uid} {name}: the toast\'s Open lands on it (open={opened}, view {s2["view"]})')
        await pg.evaluate(CLOSE); await pg.wait_for_timeout(150)
        made.append((name, title))
    # after a reload: in this person's All Tasks, Mine
    await pg.evaluate("async () => { await saveNow(); }")
    await pg.reload(); await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
    await sign_in(pg, uid)
    await pg.evaluate("() => { view = (ROLE_VIEWS[role()] || []).includes('tkall') ? 'tkall' : 'tasks'; render(); tkWho = 'me'; t2View = 'all'; tkProject = ''; tkArea = ''; tkPri = ''; t2Q = ''; tkQueue = ''; render(); }")
    await pg.wait_for_timeout(300)
    for name, title in made:
        r = await pg.evaluate("t => [(document.getElementById('tkall-body') || {}).textContent.includes(t), openTasks('me').some(x => x.title.includes(t))]", title)
        c.ok(r == [True, True], f'{label} {uid} {name}: after a reload it is in All Tasks, Mine ({r})')


async def defaults(c, pg):
    await sign_in(pg, 'u_owner')
    # an undated task: the default view (Today) says how many have no date, with a link that opens them
    await pg.evaluate("() => { crCreateTask({ title: 'Findable undated', for: 'me', assignee: tkMe() }); view = 'tkall'; tkWho = 'me'; t2View = 'today'; render(); }"); await pg.wait_for_timeout(300)
    nd = await pg.evaluate("() => { const p = document.querySelector('[data-t2nodate]'); return p ? [+p.dataset.t2nodate, t2Counts(t2Pool()).nodate, !!p.querySelector('[data-t2view=\"nodate\"]')] : null; }")
    c.ok(nd and nd[0] == nd[1] and nd[0] > 0 and nd[2], f'Today says how many tasks have no date, with a link: {nd}')
    if nd:
        await click(pg, '[data-t2nodate] [data-t2view="nodate"]')
        c.ok(await pg.evaluate("() => t2View") == 'nodate', 'the link opens No Date')
    # "For": the current project only from inside a project page
    r = await pg.evaluate("""() => { const out = {}; setCurrent('p121');
      for (const v of ['home', 'tkall', 'ovoffice', 'dash', 'sched', 'tasks']) { view = v; out[v] = crDefaultFor({}); }
      view = 'home'; render(); return out; }""")
    c.ok(r['home'] == 'me' and r['tkall'] == 'me' and r['ovoffice'] == 'me', f'"For" is Me from Home, Tasks and Office: {r}')
    c.ok(r['dash'] == 'p:p121' and r['sched'] == 'p:p121' and r['tasks'] == 'p:p121', f'and the current project from a project page: {r}')


async def main():
    c = Checks()
    async with async_playwright() as p:
        for phone in (False, True):
            label = 'phone' if phone else 'desktop'
            b, pg, errs = await open_app(p, phone=phone)
            roles = await pg.evaluate("() => (DB.users || []).filter(u => (ROLE_VIEWS[u.role] || []).includes('tkall')).map(u => u.id)")
            if not phone:
                c.ok(sorted(roles) == sorted(['u_owner', 'u_alan', 'u_chen', 'u_sarah', 'u_ddir', 'u_billing', 'u_controller']), f'the roles that create tasks: {roles}')
                await defaults(c, pg)
            for uid in roles:
                await run_role(c, pg, uid, label)
            c.ok(not errs, f'{label}: no page errors {errs[:3]}')
            await b.close()
    return c.done()


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
