"""The task module on the phone (CONSOLIDATION §2.3; Alan, 2026-10-21: "The task module is one of the most important and it
isn't great on mobile"). Desktop and 390px, as the owner, the PM, the coordinator, the foreman and the crew.

  list      Tasks opens on Due Soon (overdue and the next 7 days, grouped by day) and never opens empty while work is
            coming; rows are 64 to 72px with a 44px check circle and a 16px title; one header line on the phone (a
            filter chip and a search icon) and a round + New Task above the bar; nothing scrolls sideways
  one       "Due Soon" (the old "Next 7 Days"), "Today" and "Overdue" read one number: the list's chip, the rows it
            shows, tkMyCounts(), Ask, and the designer's Today
  sheet     a tap on a task opens one sheet with the keyboard down (Done, quick dates, Hand Off, the source); the same
            sheet opens from Today, the job's list, Sales, the foreman's Today's Work and a toast's Open; Edit is second
  hand      the PM hands a task to the coordinator from the sheet: it stays the PM's until she accepts, it is on her
            Today with Accept, and Accept moves the owner to her; a decline needs a reason and sends it back
  find      at 390px, after every way of making a task (the + button, a job's New Task, the quick add, Today's New ›
            Task), the new task is on the screen, its sheet opens from its row, and after a reload it is still there
  forward   Sales Tasks and the owner's and PM's My Day open Tasks with their chip; the crew's Tasks page is gone from
            their menu and its old link lands on Clock; the crew's work rows open the sheet
  proof     Done on a task the Standard needs proof for asks for the photo (the list, the sheet and the foreman's row)
  dupes     Make It a Task offers the matching decision first; adding to it makes no third copy
  scale     one priority scale: High, Medium, Low
Invented data only."""
import asyncio, json, os
from harness import async_playwright, open_app, sign_in, go, Checks, ROOT

ROW = r"""() => { const v = document.querySelector('.view.on'); const vis = e => !!e && e.getClientRects().length > 0 && getComputedStyle(e).visibility !== 'hidden';
  const F = (() => { const b = [...document.querySelectorAll('#mtabs, #tabbar')].find(vis); return b ? b.getBoundingClientRect().top : innerHeight; })();
  const rows = [...v.querySelectorAll('.tk2-row')].filter(vis).map(r => { const b = r.getBoundingClientRect(), c = r.querySelector('.tk2-check, .tk2-donemark'), cb = c ? c.getBoundingClientRect() : { width: 0, height: 0 }, t = r.querySelector('.tk2-title');
    return { key: r.dataset.tkkey, h: Math.round(b.height), y: Math.round(b.top), cw: Math.round(cb.width), ch: Math.round(cb.height), fs: t ? parseFloat(getComputedStyle(t).fontSize) : 0, lines: t ? Math.round(t.getBoundingClientRect().height / parseFloat(getComputedStyle(t).lineHeight)) : 0 }; });
  const small = [...v.querySelectorAll('button, a.btn, input[type=checkbox], select, summary')].filter(vis).filter(b => { const r = b.getBoundingClientRect(); return r.top < F && r.bottom > 0 && (r.height < 44 || r.width < 44) && r.width > 0; }).map(b => ((b.innerText || b.getAttribute('aria-label') || '?').replace(/\s+/g, ' ').slice(0, 20)) + ' ' + Math.round(b.getBoundingClientRect().width) + 'x' + Math.round(b.getBoundingClientRect().height));
  const chip = v.querySelector('[data-tkfilter]'), fab = document.querySelector('.view.on .tk2-fab'), fb = fab ? fab.getBoundingClientRect() : null, srch = v.querySelector('[data-tksearch]');
  return { view, t2View, tkWho, rows, small, above: rows.filter(r => r.y < F - 16).length, sw: document.documentElement.scrollWidth,
    chip: chip ? chip.innerText.replace(/\s+/g, ' ').trim() : '', chipN: chip && chip.querySelector('.n') ? +chip.querySelector('.n').textContent : null,
    fab: fb ? { w: Math.round(fb.width), h: Math.round(fb.height), right: Math.round(innerWidth - fb.right), bottom: Math.round(F - fb.bottom) } : null, search: !!srch,
    groups: [...v.querySelectorAll('.tk2-ghd')].filter(vis).map(h => h.childNodes[0] ? h.childNodes[0].textContent.trim() : ''), empty: (v.querySelector('.tk2-empty') || {}).textContent || '' }; }"""

SHEET = r"""() => { const m = document.getElementById('mbm'); if (!m) return null; const a = document.activeElement;
  const ctl = [...m.querySelectorAll('button, input, select')].filter(c => c.getClientRects().length).map(c => (c.innerText || c.getAttribute('aria-label') || c.placeholder || '').replace(/\s+/g, ' ').trim());
  return { title: (m.querySelector('.mbm-hd h3') || {}).innerText || '', key: (m.querySelector('[data-tks]') || { dataset: {} }).dataset.tks || '', ctl,
    primary: ((m.querySelector('#mbm-ok') || {}).innerText || '').trim(), kbd: !!(a && /^(INPUT|TEXTAREA)$/.test(a.tagName) && m.contains(a)), text: m.innerText }; }"""

CLOSE = "() => { try { mbCloseModal(); } catch (e) {} document.querySelectorAll('#mbm').forEach(e => e.remove()); }"


async def tap_row(pg, sel='.view.on .tk2-row .tk2-title', i=0):
    ok = await pg.evaluate("([s, i]) => { const e = [...document.querySelectorAll(s)].filter(x => x.getClientRects().length)[i]; if (!e) return false; e.click(); return true; }", [sel, i])
    await pg.wait_for_timeout(350)
    return await pg.evaluate(SHEET) if ok else None


async def reset(pg, uid, v='tkall'):
    await pg.evaluate(CLOSE)
    await sign_in(pg, uid)
    await go(pg, v)
    await pg.wait_for_timeout(250)


async def list_checks(c, pg, label, phone):
    """the list as each office role opens it"""
    for uid in ('u_owner', 'u_alan', 'u_chen'):
        await reset(pg, uid)
        m = await pg.evaluate(ROW)
        who = f'{label} {uid}'
        c.ok(m['view'] == 'tkall' and m['t2View'] == 'week' and m['tkWho'] == 'me', f'{who}: Tasks opens on Mine, Due Soon ({m["view"]}, {m["t2View"]}, {m["tkWho"]})')
        soon = await pg.evaluate("() => tkMyCounts().week")
        c.ok(len(m['rows']) == soon, f'{who}: Due Soon lists every task due soon ({len(m["rows"])} rows, {soon} due soon)')
        c.ok(soon == 0 or len(m['rows']) > 0, f'{who}: it does not open empty while {soon} are due soon')
        bad = [r for r in m['rows'] if not (64 <= r['h'] <= 72)]
        c.ok(m['rows'] and not bad, f'{who}: every row is 64 to 72px tall ({bad[:3] or [r["h"] for r in m["rows"][:6]]})')
        c.ok(all(r['cw'] >= 44 and r['ch'] >= 44 for r in m['rows']), f'{who}: the check circle is at least 44px ({[(r["cw"], r["ch"]) for r in m["rows"][:3]]})')
        c.ok(all(r['fs'] >= 16 and r['lines'] <= 2 for r in m['rows']), f'{who}: titles are 16px on at most two lines ({[(r["fs"], r["lines"]) for r in m["rows"][:3]]})')
        c.ok(m['sw'] <= (390 if phone else 1440), f'{who}: nothing scrolls sideways ({m["sw"]})')
        if phone:
            c.ok(not m['small'], f'{who}: every target on the first screen is at least 44px ({m["small"][:4]})')
            c.ok(m['chip'].startswith('Mine · Due Soon') and m['search'], f'{who}: one header line, a filter chip and a search icon ("{m["chip"]}", search {m["search"]})')
            c.ok(m['fab'] and m['fab']['w'] >= 44 and m['fab']['right'] <= 24 and 0 <= m['fab']['bottom'] <= 40, f'{who}: New Task is a round + above the bar, bottom right ({m["fab"]})')
            c.ok(m['chipN'] == soon, f'{who}: the chip reads the same Due Soon number ({m["chipN"]} vs {soon})')
            if m['rows']:
                c.ok(m['above'] >= min(3, len(m['rows'])), f'{who}: at least three rows above the fold ({m["above"]})')
        else:
            n = await pg.evaluate("() => { const b = document.querySelector('.view.on [data-t2view=\"week\"] .n'); return b ? +b.textContent : 0; }")
            c.ok(n == soon, f'{who}: the Due Soon chip on the wide screen reads the same number ({n} vs {soon})')
        day = lambda g: g in ('Overdue', 'Today', 'Tomorrow', 'No Date', 'Later On') or g.count(',') == 1
        c.ok(soon == 0 or (m['groups'] and all(day(g) for g in m['groups'])), f'{who}: grouped by day ({m["groups"][:4]})')
        # one number: Today, Overdue and Due Soon, the list against the counts and Ask
        for v in ('today', 'overdue', 'week'):
            await pg.evaluate("v => { t2View = v; renderTkAll(); }", v)
            n = len((await pg.evaluate(ROW))['rows'])
            want = await pg.evaluate("v => tkMyCounts()[v]", v)
            c.ok(n == want, f'{who}: {v} shows {n} rows and counts {want}')
        a = await pg.evaluate("async () => { let r = paAsk('how many of my tasks are due soon'); if (r && r.then) r = await r; return (r && r.headline) || ''; }")
        n_ask = int(a.split()[0]) if a and a.split()[0].isdigit() else (0 if a.startswith('Nothing') else -1)
        c.ok(n_ask == soon, f'{who}: Ask gives the same Due Soon number ({n_ask} vs {soon}: "{a[:90]}")')
        a = await pg.evaluate("async () => { let r = paAsk('which of my tasks are overdue'); if (r && r.then) r = await r; return (r && r.headline) || ''; }")
        od = await pg.evaluate("() => tkMyCounts().overdue")
        n_ask = int(a.split()[0]) if a and a.split()[0].isdigit() else (0 if a.startswith('Nothing') else -1)
        c.ok(n_ask == od, f'{who}: Ask gives the same Overdue number ({n_ask} vs {od}: "{a[:90]}")')
        await pg.evaluate("() => { t2View = 'week'; renderTkAll(); }")
        # a tap opens the sheet, keyboard down, with Done, the dates and Hand Off
        sh = await tap_row(pg)
        c.ok(sh and sh['key'], f'{who}: a tap on a row opens the task sheet ({(sh or {}).get("title")})')
        if sh:
            c.ok(not sh['kbd'], f'{who}: the keyboard stays down')
            c.ok(any(x == 'Hand Off' or x.startswith('Hand Off') for x in sh['ctl']), f'{who}: the sheet has Hand Off ({sh["ctl"][:8]})')
            c.ok(any(x.startswith(('Today', 'Tomorrow')) for x in sh['ctl']), f'{who}: the sheet has quick dates')
            c.ok(sh['primary'] in ('Mark Done', 'Accept') or 'Mark Done' in sh['ctl'], f'{who}: Done is the blue button or beside it (blue: {sh["primary"]})')
            c.ok(any(x in ('Edit', 'Edit Schedule') for x in sh['ctl']) and sh['primary'] not in ('Edit', 'Edit Schedule'), f'{who}: Edit is second, never blue')
        await pg.evaluate(CLOSE)


async def handoff(c, pg, label):
    """PM to coordinator: the sheet's person picker, her Today with Accept, Accept moves the owner"""
    await reset(pg, 'u_alan')
    key = await pg.evaluate("""() => { const m = crCreateTask({ title: 'Hand-off check: confirm the tile ETA with Nemo', for: 'p:p121', assignee: tkMe(), due: addWork(today(), 2) });
      save(); return `${m.kind}:${m.id}:${m.projectId || ''}`; }""")
    await pg.evaluate("k => tkSheet(k)", key)
    await pg.wait_for_timeout(250)
    await pg.evaluate("() => document.querySelector('#mbm [data-tkshandopen]').click()")
    await pg.wait_for_timeout(100)
    sent = await pg.evaluate("() => { const b = [...document.querySelectorAll('#mbm [data-tksto]')].find(b => /^Chen/.test(b.dataset.tksto)); if (!b) return false; document.querySelector('#mbm [data-tkshandnote]').value = 'Nemo owes us the date'; b.click(); return true; }")
    await pg.wait_for_timeout(300)
    st = await pg.evaluate("k => { const x = tkAll().find(t => t.key === k); return x ? { owner: x.owner, offered: x.offeredTo, state: (x.handoff || {}).state, log: ((tdyRec(x.row) || {}).handoffs || []).length } : null; }", key)
    c.ok(sent and st and st['state'] == 'offered' and st['offered'].startswith('Chen') and st['owner'].startswith('Alan'), f'{label}: the PM offered it to Chen and still owns it ({st})')
    toast = await pg.evaluate("() => (document.getElementById('toast') || {}).innerText || ''")
    c.ok('Chen' in toast and 'Open' in toast, f'{label}: the hand-off toasts with Open ("{toast[:80]}")')
    mine = await pg.evaluate("k => openTasks('me').some(x => t2Key(x) === k)", key)
    c.ok(mine, f'{label}: until she accepts it stays on the PM\'s Mine')
    # her Today: on the first screen of the Tasks filter with Accept, and on All
    await reset(pg, 'u_chen', 'home')
    r = await pg.evaluate("""k => { tdyTabSet('all'); render(); const id = k; const cards = [...document.querySelectorAll('.view.on .td-do .td-card')].filter(e => e.getClientRects().length);
      const A = tdyModel().all, i = A.findIndex(it => it.kind === 'tdyTask' && it.id === id), shown = cards.some(e => e.dataset.id === id); const all = i >= 0 ? { i, of: A.length, shown } : null;
      tdyTabSet('tasks'); render(); const c2 = [...document.querySelectorAll('.view.on .td-do .td-card')].filter(e => e.getClientRects().length);
      const j = c2.findIndex(e => e.dataset.id === id); return { all, tasks: j >= 0 ? { j, verb: c2[j].querySelector('[data-tdverb]').innerText.trim(), y: Math.round(c2[j].getBoundingClientRect().top) } : null }; }""", key)
    c.ok(r['tasks'] and r['tasks']['verb'] == 'Accept', f'{label}: it is on Chen\'s Today with Accept ({r})')
    # its place in All is Today's order (the Coming Up lane's); the Tasks filter and the list's offer line always show it
    c.ok(r['all'] is not None, f'{label}: and in her Today, All ({r["all"]})')
    off = await pg.evaluate("() => { view = 'tkall'; render(); const b = document.querySelector('.view.on [data-tkoffer]'); return b ? b.innerText.replace(/\\s+/g, ' ') : ''; }")
    c.ok('offered' in off.lower(), f'{label}: her Tasks shows it offered to her ("{off[:80]}")')
    # Accept from the sheet moves the owner
    await pg.evaluate("k => tkSheet(k)", key)
    await pg.wait_for_timeout(250)
    sh = await pg.evaluate(SHEET)
    c.ok(sh and sh['primary'] == 'Accept' and 'Decline' in sh['ctl'], f'{label}: her sheet says Accept, with Decline beside it ({sh and sh["primary"]})')
    await pg.evaluate("() => document.querySelector('#mbm #mbm-ok').click()")
    await pg.wait_for_timeout(300)
    st = await pg.evaluate("k => { const x = tkAll().find(t => t.key === k); return x ? { owner: x.owner, state: (x.handoff || {}).state, mine: openTasks('me').some(y => t2Key(y) === k) } : null; }", key)
    c.ok(st and st['owner'].startswith('Chen') and st['state'] == 'accepted' and st['mine'], f'{label}: Accept makes it hers ({st})')
    # a decline needs a reason and goes back
    key2 = await pg.evaluate("""() => { signIn('u_alan'); const m = crCreateTask({ title: 'Hand-off check two: order the access panels', for: 'p:p121', assignee: tkMe(), due: addWork(today(), 3) });
      const x = tkItems().find(y => y.id === m.id); tdyHandOff(x, 'Chen Biron', ''); signIn('u_chen'); render(); return `${m.kind}:${m.id}:${m.projectId || ''}`; }""")
    await pg.evaluate("k => tkSheet(k)", key2)
    await pg.wait_for_timeout(200)
    await pg.evaluate("() => document.querySelector('#mbm [data-tksdecline]').click()")
    still = await pg.evaluate("k => (tkAll().find(t => t.key === k).handoff || {}).state", key2)
    c.ok(still == 'offered', f'{label}: Decline with no reason is refused ({still})')
    await pg.evaluate("() => { document.querySelector('#mbm [data-tksreason]').value = 'Not mine: the PM orders access panels'; document.querySelector('#mbm [data-tksdecline]').click(); }")
    await pg.wait_for_timeout(200)
    st = await pg.evaluate("k => { const x = tkAll().find(t => t.key === k); return { state: (x.handoff || {}).state, owner: x.owner }; }", key2)
    c.ok(st['state'] == 'declined' and st['owner'].startswith('Alan'), f'{label}: Decline with a reason sends it back ({st})')
    await pg.evaluate(CLOSE)


async def find_again(c, pg, label):
    """at 390px: every way of making a task leaves it on the screen, its sheet opens from its row, and a reload keeps it"""
    made = []
    for uid in ('u_owner', 'u_alan', 'u_chen'):
        ways = [('the + button', "() => { view = 'tkall'; render(); document.querySelector('.view.on #tk-new').click(); }"),
                ("Today's New › Task", "() => { view = 'home'; render(); CR_NEW.flatMap(g => g[1]).find(x => x[0] === 'task')[2](); }")]
        if uid != 'u_chen':
            ways.append(("a job's New Task", "() => { setCurrent('p121'); view = 'tasks'; render(); document.querySelector('.view.on #tk-new').click(); }"))
        for i, (how, js) in enumerate(ways):
            title = f'Find again {uid[2:]} {i} {label}'
            await reset(pg, uid, 'home')
            await pg.evaluate(js)
            await pg.wait_for_timeout(300)
            ok = await pg.evaluate("t => { const i = document.querySelector('#mbm [data-f=\"title\"]'); if (!i) return false; i.value = t; i.dispatchEvent(new Event('input', { bubbles: true })); document.querySelector('#mbm #mbm-ok').click(); return true; }", title)
            await pg.wait_for_timeout(500)
            seen = await pg.evaluate("""t => { const r = [...document.querySelectorAll('.view.on .tk2-row')].find(e => e.innerText.includes(t)); if (!r) return { vis: false, view };
              const b = r.getBoundingClientRect(); return { vis: b.bottom > 0 && b.top < innerHeight, flash: r.classList.contains('tk-flash'), view, key: r.dataset.tkkey }; }""", title)
            c.ok(ok and seen['vis'], f'{label} {uid} {how}: the new task is on the screen right after saving ({seen})')
            if seen.get('key'):
                await pg.evaluate("t => { const r = [...document.querySelectorAll('.view.on .tk2-row')].find(e => e.innerText.includes(t)); r.querySelector('.tk2-title').click(); }", title)
                await pg.wait_for_timeout(300)
                sh = await pg.evaluate(SHEET)
                c.ok(sh and sh['key'] == seen['key'], f'{label} {uid} {how}: its row opens its sheet')
                await pg.evaluate(CLOSE)
            made.append((uid, how, title))
    await pg.evaluate("async () => { await saveNow(); }")
    await pg.reload()
    await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
    for uid, how, title in made:
        await sign_in(pg, uid)
        r = await pg.evaluate("""t => { view = 'tkall'; tkWho = 'me'; tkProject = ''; t2View = 'all'; render(); const x = openTasks('me').find(y => y.title === t);
          return { mine: !!x, listed: [...document.querySelectorAll('.view.on .tk2-row')].some(e => e.innerText.includes(t)) }; }""", title)
        c.ok(r['mine'] and r['listed'], f'{label} {uid} {how}: after a reload it is on Tasks, Mine ({r})')


async def places(c, pg, label, phone):
    """the same sheet from Today, the job, Sales, the foreman and a toast; the forwards; the crew"""
    # Today: a tap on a task card's words opens the sheet
    await reset(pg, 'u_alan', 'home')
    await pg.evaluate("() => { tdyTabSet('tasks'); render(); }")
    sh = await tap_row(pg, '.view.on .td-do .td-card[data-kind="tdyTask"] .td-l2')
    c.ok(sh and sh['key'], f'{label}: a tap on a Today task card opens the task sheet ({(sh or {}).get("title")})')
    await pg.evaluate(CLOSE)
    if phone:
        t = await pg.evaluate("() => [...document.querySelectorAll('.view.on .td-tabs button')].filter(b => b.getClientRects().length).map(b => Math.round(b.getBoundingClientRect().height))")
        c.ok(t and min(t) >= 44, f'{label}: Today\'s filter chips are 44px tall ({t})')
    # the job's list is the same list with the job chip
    await pg.evaluate("() => { setCurrent('p121'); view = 'tasks'; render(); }")
    await pg.wait_for_timeout(200)
    m = await pg.evaluate(ROW)
    c.ok(m['rows'] and m['t2View'] == 'week', f'{label}: Projects › Tasks is the list with the job chip, on Due Soon ({m["t2View"]}, {len(m["rows"])} rows, "{m["chip"]}")')
    sh = await tap_row(pg)
    c.ok(sh and sh['key'], f'{label}: and its rows open the same sheet')
    await pg.evaluate(CLOSE)
    # Sales Tasks and My Day forward to Tasks with their chip
    await reset(pg, 'u_owner', 'hbtasks')
    s = await pg.evaluate("() => ({ view, tkProject, sales: [...document.querySelectorAll('.view.on .tk2-row')].length, allSales: tkItems().filter(x => !x.done && (x.kind === 'hub' || x.kind === 'lead')).length })")
    c.ok(s['view'] == 'tkall' and s['tkProject'] == '__sales' and s['sales'] > 0, f'{label}: Sales Tasks opens Tasks with the Sales chip ({s})')
    await reset(pg, 'u_owner', 'sday')
    s = await pg.evaluate("() => ({ view, tkWho, menu: JSON.stringify(typeof mnMap === 'function' ? mnMap() : {}).includes('\"sday') })")
    c.ok(s['view'] == 'tkall' and s['tkWho'] == 'me', f'{label}: the owner\'s My Day opens Tasks, Mine ({s})')
    for uid in ('u_owner', 'u_alan', 'u_chen'):
        rv = await pg.evaluate("u => { signIn(u); return (ROLE_VIEWS[role()] || []).filter(v => ['hbtasks', 'sday'].includes(v)); }", uid)
        c.ok(not rv, f'{label} {uid}: Sales Tasks and My Day are no longer pages of their own ({rv})')
    # the designer keeps My Day as her Today, and its card is her Due Soon from the one list
    await reset(pg, 'u_sarah', 'sday')
    d = await pg.evaluate("() => { const c = document.querySelector('.view.on .tk2-host'); return c ? { n: +((c.querySelector('.tk2-hd .n') || {}).textContent || -1), rows: c.querySelectorAll('.tk2-row').length, want: tkMyCounts().week, view } : { view }; }")
    c.ok(d.get('n') == d.get('want') and d.get('rows') == min(6, d.get('want', 0)), f'{label}: the designer\'s Today reads her Due Soon, the same number ({d})')
    if d.get('rows'):
        sh = await tap_row(pg)
        c.ok(sh and sh['key'], f'{label}: and its rows open the sheet')
        await pg.evaluate(CLOSE)
    # the foreman: a tap on Today's Work opens the schedule line's card, Edit Schedule second
    await reset(pg, 'u_angel', 'ftoday')
    sh = await tap_row(pg, '.view.on .f-row:has([data-fdone]) .grow > b')
    c.ok(sh and sh['key'].startswith('sched:') and 'Edit Schedule' in sh['ctl'] and sh['primary'] in ('Start It', 'Update Progress', 'Mark Done'), f'{label}: the foreman\'s work row opens its card, Edit Schedule second ({sh and (sh["key"], sh["primary"])})')
    await pg.evaluate(CLOSE)
    if phone:
        m = await pg.evaluate("() => { const bar = [...document.querySelectorAll('#mtabs, #tabbar')].find(e => e.getClientRects().length); const F = bar ? bar.getBoundingClientRect().top : innerHeight; return [...document.querySelectorAll('.view.on .f-row, .view.on .td-card')].filter(e => e.getClientRects().length && e.getBoundingClientRect().top < F - 16).length; }")
        c.ok(m >= 3, f'{label}: the foreman\'s first screen holds three work rows or more ({m})')
    # the crew: no Tasks page; the old link lands on Clock; their work rows open the sheet
    await reset(pg, 'u_alberto', 'tasks')
    s = await pg.evaluate("() => ({ view, may: (ROLE_VIEWS.crew || []).includes('tasks'), menu: (MENU.crew.rest || []).some(x => x[0] === 'tasks') })")
    c.ok(s['view'] == 'time' and not s['may'] and not s['menu'], f'{label}: the crew\'s Tasks link lands on Clock and the page has left their menu ({s})')
    if phone:   # the crew run their day on the phone; Clock's desktop layout is a table of hours
        sh = await tap_row(pg, '.view.on .f-row:has([data-fdone]) .grow > b, .view.on .fm-row:has([data-fm-done]) b')
        c.ok(sh and sh['key'].startswith('sched:'), f'{label}: the crew\'s work rows open the same card ({sh and sh["key"]})')
        await pg.evaluate(CLOSE)
    # a toast's Open lands on the task and opens its sheet
    await reset(pg, 'u_alan')
    k = await pg.evaluate("() => { const m = crCreateTask({ title: 'Toast check: walk the parlor with Angel', for: 'me', assignee: tkMe(), due: today() }); save(); crOpenTask(m); return `${m.kind}:${m.id}:`; }")
    await pg.wait_for_timeout(400)
    sh = await pg.evaluate(SHEET)
    c.ok(sh and sh['key'] == k and await pg.evaluate("() => view") == 'tkall', f'{label}: a toast\'s Open lands on Tasks with the task\'s sheet ({sh and sh["key"]})')
    await pg.evaluate(CLOSE)


async def proof_dupes_scale(c, pg, label):
    await reset(pg, 'u_alan')
    # a task the Standard needs proof for: Done asks for the photo
    k = await pg.evaluate("() => { const m = crCreateTask({ title: 'Close the garden bath walls (drywall)', for: 'p:p121', assignee: tkMe(), due: today() }); save(); render(); return `${m.kind}:${m.id}:${m.projectId}`; }")
    await pg.evaluate("k => tkCheckDone(k)", k)
    await pg.wait_for_timeout(300)
    r = await pg.evaluate("k => ({ open: !tkItems().find(x => t2Key(x) === k).done, sheet: ((document.querySelector('#mbm .mbm-hd h3') || {}).innerText || '') })", k)
    c.ok(r['open'] and r['sheet'].startswith('Proof Needed'), f'{label}: Done on a wall about to close asks for the photo first ({r})')
    await pg.evaluate(CLOSE)
    # Make It a Task offers the matching decision first; adding to it makes no third copy
    before = await pg.evaluate("() => openTasks('all').length")
    await pg.evaluate("() => newTaskDialog({ title: 'Laundry layout: new washer/dryer sizes', projectId: 'p121', notes: 'Sarah Klein asked about the stacked units', source: { label: 'a message from Sarah Klein' } })")
    await pg.wait_for_timeout(250)
    d = await pg.evaluate("() => ({ title: ((document.querySelector('#mbm .mbm-hd h3') || {}).innerText || ''), n: document.querySelectorAll('#mbm [data-tkdupi]').length, first: ((document.querySelector('#mbm [data-tkdupi]') || {}).innerText || '').replace(/\\s+/g, ' '), dec: [...document.querySelectorAll('#mbm [data-tkdupi]')].findIndex(b => / · decision/.test(b.innerText)) })")
    c.ok(d['title'] == 'This May Already Be There' and d['dec'] >= 0, f'{label}: Make It a Task offers the open decision (and the matching task) before a new one ({d})')
    if d['dec'] >= 0:
        await pg.evaluate("i => document.querySelectorAll('#mbm [data-tkdupi]')[i].click()", d['dec'])
        await pg.wait_for_timeout(250)
        after = await pg.evaluate("() => openTasks('all').length")
        note = await pg.evaluate("() => { const p = DB.projects.find(p => p.id === 'p121'); const d = p.decisions.find(d => /laundry/i.test(d.name)); return d ? (d.notes || '') : ''; }")
        c.ok(after == before and 'stacked units' in note, f'{label}: adding to it makes no new task and keeps the words on the decision ({before} -> {after})')
    await pg.evaluate(CLOSE)
    # one priority scale
    pr = await pg.evaluate("""() => { const a = crCreateTask({ title: 'Priority scale check', for: 'me', assignee: tkMe() }).rec; asTaskDialog(a.id);
      const s = document.querySelector('#mbm [data-f="pri3"]'); const o = s ? [...s.options].map(o => o.textContent) : []; mbCloseModal(); return o; }""")
    c.ok(bool(pr) and all(x.split(' ')[0] in ('High', 'Medium', 'Low') for x in pr), f'{label}: one priority scale, High, Medium, Low ({pr})')


async def shots(pg, label):
    """review/tasks/: the list, a sheet, Today and the job's list as the PM, the foreman's Today (never git-added)"""
    d = os.path.join(ROOT, 'review', 'tasks')
    os.makedirs(d, exist_ok=True)
    for uid, v, js, name in [('u_alan', 'tkall', '', 'pm_tasks'), ('u_alan', 'tkall', "() => { const r = document.querySelector('.view.on .tk2-row .tk2-title'); r && r.click(); }", 'pm_sheet'),
                             ('u_alan', 'home', "() => { tdyTabSet('tasks'); render(); }", 'pm_today_tasks'), ('u_alan', 'tasks', "() => { setCurrent('p121'); view = 'tasks'; render(); }", 'pm_job_tasks'),
                             ('u_owner', 'tkall', "() => { tkWho = 'team'; t2Group = null; renderTkAll(); }", 'owner_team'), ('u_angel', 'ftoday', '', 'foreman_today'), ('u_sarah', 'sday', '', 'designer_today')]:
        await reset(pg, uid, v)
        if js: await pg.evaluate(js); await pg.wait_for_timeout(300)
        await pg.screenshot(path=os.path.join(d, f'{label}_{name}.png'))
    await pg.evaluate(CLOSE)


async def main():
    c = Checks()
    async with async_playwright() as p:
        for phone in (True, False):
            label = 'phone' if phone else 'desktop'
            b, pg, errs = await open_app(p, phone=phone)
            await list_checks(c, pg, label, phone)
            await places(c, pg, label, phone)
            if phone:
                await handoff(c, pg, label)
                await proof_dupes_scale(c, pg, label)
                await find_again(c, pg, label)
            await shots(pg, label)
            c.ok(not errs, f'{label}: no page errors {errs[:3]}')
            await b.close()
    return c.done()


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
