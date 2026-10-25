"""The task views (docs/TASKS_PLAN.md §2 item 5; Alan, 2026-10-23: "the table needs updating as it looks like a
spreadsheet", "more modern than a spreadsheet and very easy to read, sort, filter"). src/taskviews.js.
Desktop 1440 and phone 390, as the coordinator (who runs the meeting) and the owner.

  one       every layout (List, Table, Board, Calendar) shows the list's own number: its summary, the rows it draws,
            tvRows(), and for Mine the Due Soon chip and tkMyCounts(); a filter chip (Owner) and each saved tab
            (My Week, Waiting on Others, By Project, All Open) give the count the list gives for the same filter
  edit      a cell edits in place with its control (due, follow-up, owner, status, Waiting On), the change is on the
            record, it toasts with Open, and it is still there after a reload
  drag      the board moves a task to Doing (status) and Undo puts it back; the calendar moves its due date to
            another day and Undo puts it back
  bulk      two rows selected, Move Date to Tomorrow moves both, one Undo puts both back
  sheet     a row's title, a board card and a calendar chip open the one task sheet; at 1440 it is a panel on the
            right and the table stays in view beside it
  table     no cell borders (computed style), sticky header, sort by a header, a second sort with Shift, the
            keyboard moves between rows
  phone     no sideways scroll in any layout; every target on the first screen is 44px and 8px from the next
  views     a view saved by the coordinator is hers: the owner's views do not change
  polish    at 1280 and 1440 every open row, card and List row has its ID, no column is cut off, one filter row,
            initials for owners, Waiting On filled; Tasks sits under Today in each office role's menu (not the
            field's) with its late and due-today badge and opens the list; at 390 the meeting's eight actions are on
            the first screen above Previous and Next, with the toast above them
Screenshots: review/taskviews/ (desktop and phone; never committed).
Invented data only."""
import asyncio, os, sys
from harness import async_playwright, open_app, sign_in, go, Checks, ROOT

SHOTS = os.path.join(ROOT, 'review', 'taskviews')
os.makedirs(SHOTS, exist_ok=True)
CLOSE = "() => { try { mbCloseModal(); } catch (e) {} try { tvPopClose(); } catch (e) {} document.querySelectorAll('#mbm, #tv-pop').forEach(e => e.remove()); }"

# what one layout shows: its summary's number and the tasks it draws (a task drawn twice, as its due and its follow-up, is one)
SHOWN = r"""() => { const h = document.getElementById('tkall-body'); const s = h.querySelector('[data-tvn]');
  const mode = tkMode, vis = e => e.getClientRects().length > 0;
  let keys = [];
  if (mode === 'board') keys = [...h.querySelectorAll('.tv-bcol:not(.tv-bextra) [data-tvrow]')];
  else if (mode === 'cal') keys = [...h.querySelectorAll('.tv-ev[data-tvfield="due"]')];
  else if (mode === 'table') keys = [...h.querySelectorAll('.tv-tr[data-tvrow], .tk2-row[data-tvrow]')];
  else keys = h.querySelector('.tk2-empty') ? [] : [...h.querySelectorAll('.tk2-row[data-tkkey]')];
  return { mode, n: s ? +s.dataset.tvn : null, rows: new Set(keys.map(e => e.dataset.tvrow || e.dataset.tkkey)).size, list: tvRows().length,
    sw: document.documentElement.scrollWidth, iw: innerWidth }; }"""

# every visible target in the view and the picker: under 44px, or closer than 8px to another
TARGETS = r"""() => { const v = document.querySelector('.view.on'); const pop = document.getElementById('tv-pop');
  const vis = e => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && r.bottom > 0 && r.top < innerHeight; };
  const F = (() => { const b = [...document.querySelectorAll('#mtabs, #tabbar')].find(e => e.getClientRects().length); return b ? b.getBoundingClientRect().top : innerHeight; })();
  const scope = [v, pop].filter(Boolean);
  const T = scope.flatMap(s => [...s.querySelectorAll('#tkall-body button, #tkall-body input[type=checkbox], #tkall-body select, .tv-pop button')]).filter(vis)
    .filter(e => !e.closest('.tk2-acts') && !e.closest('.tv-cal.month') && !e.closest('.tk2-fab'));
  const R = T.map(e => ({ e, r: e.getBoundingClientRect() })).filter(o => o.r.top < F);
  const small = R.filter(o => o.r.height < 44 || o.r.width < 44).map(o => (o.e.innerText || o.e.getAttribute('aria-label') || '?').trim().slice(0, 18) + ' ' + Math.round(o.r.width) + 'x' + Math.round(o.r.height));
  const close = [];
  for (let i = 0; i < R.length; i++) for (let j = i + 1; j < R.length; j++) {
    const a = R[i], b = R[j]; if (a.e.contains(b.e) || b.e.contains(a.e)) continue;
    const gx = Math.max(b.r.left - a.r.right, a.r.left - b.r.right), gy = Math.max(b.r.top - a.r.bottom, a.r.top - b.r.bottom);
    if (gx < 8 && gy < 8) close.push((a.e.innerText || a.e.getAttribute('aria-label') || '?').trim().slice(0, 14) + ' / ' + (b.e.innerText || b.e.getAttribute('aria-label') || '?').trim().slice(0, 14));
  }
  return { small: small.slice(0, 6), close: close.slice(0, 6), n: R.length }; }"""


async def mode(pg, m, who='all', v='all'):
    await pg.evaluate(CLOSE)
    await pg.evaluate("([m, w, v]) => { tkWho = w; tkProject = ''; tkArea = ''; tkPri = ''; t2Q = ''; t2View = v; tkSetMode(m); }", [m, who, v])
    await pg.wait_for_timeout(300)


async def toast_of(pg):
    return await pg.evaluate("() => { const t = document.getElementById('toast'); return t ? { text: t.innerText, open: [...t.querySelectorAll('a')].map(a => a.textContent) } : null; }")


async def toast_click(pg, label):
    await pg.evaluate("l => { const a = [...document.querySelectorAll('#toast a')].find(a => a.textContent === l); a && a.click(); }", label)
    await pg.wait_for_timeout(350)


async def one_number(c, pg, who, phone):
    for m in (('cards', 'table', 'cal') if phone else ('cards', 'table', 'board', 'cal')):
        for v in ('all', 'week', 'blocked'):
            await mode(pg, m, 'all', v)
            if m == 'cal':
                # the calendar shows the month around the latest date in the list, with the rest in its trays
                await pg.evaluate("() => { tvPrefs().calMode = 'month'; renderTkAll(); }")
                await pg.wait_for_timeout(200)
            s = await pg.evaluate(SHOWN)
            if m != 'cards':
                c.ok(s['n'] == s['list'], f'{who}: {m} · {v}: the summary says {s["n"]}, the list has {s["list"]}')
            c.ok(s['rows'] == s['list'], f'{who}: {m} · {v}: {s["rows"]} tasks drawn, the list has {s["list"]}')
            c.ok(s['sw'] <= s['iw'], f'{who}: {m} · {v}: nothing scrolls sideways ({s["sw"]} > {s["iw"]})')
        await pg.screenshot(path=os.path.join(SHOTS, f'{"ph" if phone else "dt"}_{who}_{m}.png'))
    # Mine · Due Soon: the layouts, the list's count and Ask's number are one
    for m in (('table',) if phone else ('table', 'board')):
        await mode(pg, m, 'me', 'week')
        s = await pg.evaluate(SHOWN)
        want = await pg.evaluate("() => tkMyCounts().week")
        c.ok(s['n'] == want, f'{who}: {m} · Mine · Due Soon says {s["n"]}, the list counts {want}')
    # saved tabs: each gives the count of the list it stands for (on the Table: the Board's bar has no tabs, as its mockup)
    await mode(pg, 'table', 'all', 'all')
    for vid in ('b:open', 'b:week', 'b:wait', 'b:all'):
        await pg.evaluate(CLOSE)
        await pg.evaluate("id => tvApply(id)", vid)
        await pg.wait_for_timeout(300)
        s = await pg.evaluate(SHOWN)
        want = await pg.evaluate("""id => { const v = tvViews().find(x => x.id === id); const R = v.s.t2View === 'done' ? t2DonePool() : t2ViewOf(openTasks(v.s.tkWho === 'me' ? 'me' : 'all'), v.s.t2View); return R.length; }""", vid)
        c.ok(s['rows'] == want, f'{who}: saved tab {vid} draws {s["rows"]}, the list for it counts {want} ({s["mode"]})')
        if not phone:
            tab = await pg.evaluate("id => { const b = document.querySelector(`.tv-sv[data-tvview='${id}']`); return b ? { on: b.classList.contains('on'), n: +((b.querySelector('.n') || {}).textContent || -1) } : null; }", vid)
            c.ok(tab and tab['on'] and tab['n'] == want, f'{who}: the tab {vid} is the one showing and reads {want} ({tab})')
    if phone:
        return
    # a filter chip: Owner, through the bar's Filter, gives the owner's own count
    await mode(pg, 'table', 'all', 'all')
    await pg.click('[data-tvfadd]')
    await pg.wait_for_timeout(150)
    await pg.click('#tv-pop [data-tvfk="owner"]')
    await pg.wait_for_timeout(150)
    # on Tasks the Owner filter offers Me, Everyone, Nobody and A Person (one filter row, 2026-10-24)
    if await pg.evaluate("() => !!document.querySelector('#tv-pop [data-tvfwp]')"):
        await pg.click('#tv-pop [data-tvfwp]')
        await pg.wait_for_timeout(150)
    name = await pg.evaluate("() => { const b = [...document.querySelectorAll('#tv-pop [data-tvp]')].find(b => /^Chen/.test(b.dataset.tvp)) || document.querySelector('#tv-pop [data-tvp]'); const n = b.dataset.tvp; b.click(); return n; }")
    await pg.wait_for_timeout(300)
    s = await pg.evaluate(SHOWN)
    chip = await pg.evaluate("() => (document.querySelector('.tv-fchip-b') || {}).innerText || ''")
    want = await pg.evaluate("n => openTasks(n).length", name)
    c.ok(chip.startswith('Owner: ') and s['rows'] == want, f'{who}: the "{chip}" chip shows {s["rows"]} tasks, {name} has {want} open')
    await pg.click('[data-tvfx="owner"]')
    await pg.wait_for_timeout(250)
    c.ok(await pg.evaluate("() => tkWho === 'all' && !document.querySelector('.tv-fchip')"), f'{who}: the chip\'s close takes the filter off')


async def edits(c, pg, who):
    """each cell's control writes the record, toasts with Open, and survives a reload"""
    await mode(pg, 'table', 'all', 'all')
    key = await pg.evaluate("""() => { const m = crCreateTask({ title: 'Views check: confirm the stair stringer delivery', for: 'p:' + DB.projects[0].id, assignee: tkMe(), due: today() });
      save(); renderTkAll(); return `${m.kind}:${m.id}:${m.projectId || ''}`; }""")
    cell = lambda f: f'#tkall-body .tv-tr[data-tvrow="{key}"] [data-tved="{f}"]'
    tom = await pg.evaluate("() => iso(addDays(parse(today()), 1))")
    nxt = await pg.evaluate("() => tvNextMeeting()")
    # due: Tomorrow
    await pg.click(cell('due')); await pg.wait_for_timeout(150)
    labels = await pg.evaluate("() => [...document.querySelectorAll('#tv-pop [data-tvd]')].map(b => b.childNodes[0].textContent)")
    c.ok(labels[:3] == ['Today', 'Tomorrow', 'Next Meeting'], f'{who}: the date picker offers Today, Tomorrow, Next Meeting ({labels})')
    await pg.click(f'#tv-pop [data-tvd="{tom}"]'); await pg.wait_for_timeout(300)
    t = await toast_of(pg)
    due = await pg.evaluate("k => tkResolve(k).x.due", key)
    c.ok(due == tom and t and 'Open' in t['open'], f'{who}: Due to Tomorrow is on the record ({due}) and toasts with Open ({t})')
    # follow-up: Next Meeting
    await pg.click(cell('follow')); await pg.wait_for_timeout(150)
    await pg.click(f'#tv-pop [data-tvd="{nxt}"]'); await pg.wait_for_timeout(300)
    fu = await pg.evaluate("k => tkResolve(k).rec.followUp", key)
    t = await toast_of(pg)
    c.ok(fu == nxt and t and 'Open' in t['open'], f'{who}: Follow-Up to the next meeting ({fu}, want {nxt}) toasts with Open')
    # owner: the person picker, searched
    await pg.click(cell('owner')); await pg.wait_for_timeout(150)
    cur = await pg.evaluate("k => tkResolve(k).rec.assignee || ''", key)
    pick = await pg.evaluate("c => [...document.querySelectorAll('#tv-pop [data-tvp]')].map(b => b.dataset.tvp).find(n => !tkOwnerMatch(c, n) && !/crew|driver/i.test(n))", cur)
    q = pick.split()[0].lower()
    await pg.fill('#tv-pop [data-tvpq]', q); await pg.wait_for_timeout(80)
    shown = await pg.evaluate("() => [...document.querySelectorAll('#tv-pop [data-tvp]')].filter(b => !b.hidden).map(b => b.dataset.tvp)")
    c.ok(shown and all(q in n.lower() for n in shown), f'{who}: the person picker narrows as you type "{q}" ({shown})')
    await pg.press('#tv-pop [data-tvpq]', 'Enter'); await pg.wait_for_timeout(300)
    rec_owner = await pg.evaluate("k => tkResolve(k).rec.assignee", key)
    c.ok(rec_owner and rec_owner.lower().startswith(q), f'{who}: the owner is now {rec_owner} (picked {pick}, was {cur})')
    # status: Doing
    await pg.click(cell('status')); await pg.wait_for_timeout(150)
    await pg.click('#tv-pop [data-tvs="doing"]'); await pg.wait_for_timeout(300)
    st = await pg.evaluate("k => tkResolve(k).rec.status", key)
    c.ok(st == 'doing', f'{who}: the status is Doing ({st})')
    # Waiting On: who, what, when promised
    await pg.click(cell('wait')); await pg.wait_for_timeout(150)
    await pg.fill('#tv-pop [data-tvw="name"]', 'Nemo Tile'); await pg.fill('#tv-pop [data-tvw="what"]', 'the delivery date')
    await pg.click(f'#tv-pop [data-tvwd="{tom}"]'); await pg.click('#tv-pop [data-tvwsave]'); await pg.wait_for_timeout(300)
    w = await pg.evaluate("k => { const R = tkResolve(k); return { w: R.rec.waitingOn, st: R.rec.status, inWaiting: t2ViewOf(openTasks('all'), 'blocked').some(x => t2Key(x) === k) }; }", key)
    chip = await pg.evaluate("k => (document.querySelector(`#tkall-body .tv-tr[data-tvrow='${k}'] .tv-wait.on`) || {}).innerText || ''", key)
    c.ok(w['w'] and w['w'].get('name') == 'Nemo Tile' and w['w'].get('promised') == tom and w['inWaiting'], f'{who}: Waiting On is on the record and in the Waiting list ({w})')
    c.ok(chip.startswith('Nemo Tile · '), f'{who}: the chip reads who and when ("{chip}")')
    # the thread keeps what changed
    ev = await pg.evaluate("k => (tkResolve(k).rec.thread || []).map(e => e.ev).filter(Boolean)", key)
    c.ok(all(e in ev for e in ('due', 'followUp', 'owner', 'status', 'waiting')), f'{who}: each change is on the task\'s thread ({ev})')
    # after a reload, all of it is still there
    await pg.evaluate("async () => { await saveNow(); }")
    await pg.reload()
    await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
    await sign_in(pg, 'u_chen' if who.startswith('coord') else 'u_owner'); await go(pg, 'tkall')
    after = await pg.evaluate("k => { const R = tkResolve(k); return R ? { due: R.x.due, fu: R.rec.followUp, st: R.rec.status, w: (R.rec.waitingOn || {}).name } : null; }", key)
    c.ok(after and after['due'] == tom and after['fu'] == nxt and after['w'] == 'Nemo Tile', f'{who}: after a reload the edits are kept ({after})')
    return key


async def drag(pg, src, dst):
    """a drag as the browser sends it: dragstart on the item, dragover and drop on the target, dragend"""
    await pg.evaluate("""([s, d]) => { const a = document.querySelector('#tkall-body ' + s), b = document.querySelector('#tkall-body ' + d); if (!a || !b) throw new Error('drag: missing ' + (a ? d : s));
      a.scrollIntoView({ block: 'center' }); const dt = new DataTransfer(), ev = (t, el) => el.dispatchEvent(new DragEvent(t, { bubbles: true, cancelable: true, dataTransfer: dt }));
      ev('dragstart', a); ev('dragenter', b); ev('dragover', b); ev('drop', b); ev('dragend', a); }""", [src, dst])
    await pg.wait_for_timeout(350)


async def drags(c, pg, who):
    await mode(pg, 'board', 'all', 'all')
    await pg.evaluate("() => { tvPrefs().boardBy = 'status'; renderTkAll(); }")
    key = await pg.evaluate("""() => { const m = crCreateTask({ title: 'Views check: drag me to Doing', for: 'p:' + DB.projects[0].id, assignee: tkMe(), due: today() });
      save(); renderTkAll(); return `${m.kind}:${m.id}:${m.projectId || ''}`; }""")
    await drag(pg, f'.tv-card[data-tvrow="{key}"]', '[data-tvdrop="doing"]')
    st = await pg.evaluate("k => tkResolve(k).rec.status", key)
    t = await toast_of(pg)
    c.ok(st == 'doing' and t and 'Undo' in t['open'] and 'Open' in t['open'], f'{who}: a card dragged to Doing is Doing ({st}), the toast has Open and Undo ({t})')
    incol = await pg.evaluate("k => !!document.querySelector(`[data-tvdrop='doing'] [data-tvrow='${k}']`)", key)
    c.ok(incol, f'{who}: the card is in the Doing column after the move')
    await toast_click(pg, 'Undo')
    st = await pg.evaluate("k => tkResolve(k).rec.status", key)
    c.ok(st == 'todo', f'{who}: Undo puts it back to To Do ({st})')
    await pg.screenshot(path=os.path.join(SHOTS, f'dt_{who}_board_drag.png'))
    # the calendar: drag the due date two days on
    await mode(pg, 'cal', 'all', 'all')
    await pg.evaluate("() => { tvPrefs().calMode = 'month'; tvCalAt = today(); renderTkAll(); }")
    await pg.wait_for_timeout(200)
    was = await pg.evaluate("k => tkResolve(k).x.due", key)
    to = await pg.evaluate("() => iso(addDays(parse(today()), 2))")
    await drag(pg, f'.tv-ev[data-tvrow="{key}"][data-tvfield="due"]', f'[data-tvday="{to}"]')
    due = await pg.evaluate("k => tkResolve(k).x.due", key)
    t = await toast_of(pg)
    c.ok(due == to and t and 'Undo' in t['open'], f'{who}: a chip dragged on the calendar re-dates the task ({was} to {due}, want {to})')
    await toast_click(pg, 'Undo')
    due = await pg.evaluate("k => tkResolve(k).x.due", key)
    c.ok(due == was, f'{who}: Undo puts the date back ({due})')
    await pg.screenshot(path=os.path.join(SHOTS, f'dt_{who}_calendar.png'))


async def bulk(c, pg, who):
    await mode(pg, 'table', 'all', 'all')
    keys = await pg.evaluate("""() => { const p = DB.projects[0].id; const k = [1, 2].map(i => { const m = crCreateTask({ title: 'Views check: bulk move ' + i, for: 'p:' + p, assignee: tkMe(), due: today() }); return `${m.kind}:${m.id}:${m.projectId || ''}`; });
      save(); renderTkAll(); return k; }""")
    for k in keys:
        await pg.click(f'#tkall-body input[data-tvsel="{k}"]')
        await pg.wait_for_timeout(150)
    bar = await pg.evaluate("() => (document.querySelector('.tv-bulk') || {}).innerText || ''")
    c.ok('2 Selected' in bar and all(w in bar for w in ('Move Date', 'Reassign', 'Status', 'Done')), f'{who}: the floating bar offers Move Date, Reassign, Status, Done ("{bar[:80]}")')
    tom = await pg.evaluate("() => iso(addDays(parse(today()), 1))")
    await pg.click('[data-tvbulk="due"]'); await pg.wait_for_timeout(150)
    await pg.click(f'#tv-pop [data-tvd="{tom}"]'); await pg.wait_for_timeout(350)
    d = await pg.evaluate("K => K.map(k => tkResolve(k).x.due)", keys)
    c.ok(d == [tom, tom], f'{who}: Move Date moved both to tomorrow ({d})')
    await toast_click(pg, 'Undo')
    d = await pg.evaluate("K => K.map(k => tkResolve(k).x.due)", keys)
    td = await pg.evaluate("() => today()")
    c.ok(d == [td, td], f'{who}: one Undo puts both back ({d})')


async def sheet_and_table(c, pg, who):
    await mode(pg, 'table', 'all', 'all')
    # no cell borders: every th and td in the table has zero borders
    b = await pg.evaluate("""() => { const T = [...document.querySelectorAll('#tkall-body .tv-th, #tkall-body .tv-td')]; const bad = T.filter(e => { const s = getComputedStyle(e); return ['Top','Right','Bottom','Left'].some(k => parseFloat(s['border' + k + 'Width']) > 0 && s['border' + k + 'Style'] !== 'none'); });
      const R = [...document.querySelectorAll('#tkall-body .tv-tr')].slice(0, 3).map(r => Math.round(r.getBoundingClientRect().height)); const card = getComputedStyle(document.querySelector('#tkall-body .tv-gcard') || document.body).borderRadius;
      return { n: T.length, bad: bad.length, rows: R, card }; }""")
    c.ok(b['n'] > 0 and b['bad'] == 0, f'{who}: the table has no cell borders ({b})')
    c.ok(all(r >= 64 for r in b['rows']) and b['card'] == '12px', f'{who}: rows are 64px in a 12px rounded card ({b["rows"]}, {b["card"]})')
    hd = await pg.evaluate("() => { const h = document.querySelector('#tkall-body .tv-thead'); const s = getComputedStyle(h.querySelector('.tv-th[data-tvcol]')); return [getComputedStyle(h).position, s.textTransform, s.fontSize]; }")
    c.ok(hd == ['sticky', 'uppercase', '12px'], f'{who}: the header is sticky, 12px uppercase ({hd})')
    rows = await pg.evaluate("() => document.querySelectorAll('#tkall-body .tv-th[data-tvcol]').length")
    c.ok(rows <= 6, f'{who}: no more than 6 default columns ({rows})')
    # sort by Due, then a second sort with Shift
    await pg.click('[data-tvsort="due"]'); await pg.wait_for_timeout(250)
    await pg.click('[data-tvsort="owner"]', modifiers=['Shift']); await pg.wait_for_timeout(250)
    S = await pg.evaluate("() => tvSorts()")
    c.ok([s['k'] for s in S] == ['due', 'owner'], f'{who}: a header sorts and Shift adds a second sort ({S})')
    order = await pg.evaluate("""() => { const g = [...document.querySelectorAll('#tkall-body .tv-tg')][0] || document; return [...g.querySelectorAll('.tv-tr')].map(r => tkResolve(r.dataset.tvrow).x.due || '9999'); }""")
    c.ok(order == sorted(order), f'{who}: the rows read in due order ({order[:6]})')
    await pg.evaluate("() => { delete tvPrefs().table.sort; renderTkAll(); }")
    # the keyboard: ArrowDown moves to the next row's title
    mv = await pg.evaluate("""() => { const T = [...document.querySelectorAll('#tkall-body .tv-tr [data-tved="title"]')]; if (T.length < 2) return null; T[0].focus();
      T[0].dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true })); const a = document.activeElement.closest('.tv-tr'); return [T[1].closest('.tv-tr').dataset.tvrow, a && a.dataset.tvrow]; }""")
    c.ok(mv and mv[0] == mv[1], f'{who}: ArrowDown moves to the next row ({mv})')
    # a row's title opens the one sheet, as a panel on the right with the table still in view
    key = await pg.evaluate("() => document.querySelector('#tkall-body .tv-tr').dataset.tvrow")
    await pg.click(f'#tkall-body .tv-tr[data-tvrow="{key}"] [data-tved="title"]')
    await pg.wait_for_timeout(400)
    p = await pg.evaluate("""() => { const m = document.getElementById('mbm'), b = m && m.querySelector('.mbm-box'), f = document.querySelector('#tkall-body .tv-tframe');
      if (!b || !f) return null; const r = b.getBoundingClientRect(), t = f.getBoundingClientRect(); const pe = getComputedStyle(m).pointerEvents;
      const bars = document.querySelector('#tkall-body .tk2-bar').getBoundingClientRect();
      const wcol = document.querySelector('#tkall-body .tv-th.tv-col-wait');
      return { key: (m.querySelector('[data-tks]') || { dataset: {} }).dataset.tks, left: Math.round(r.left), w: Math.round(r.width), h: Math.round(r.height), top: Math.round(r.top), bottom: Math.round(r.bottom), bars: Math.round(bars.bottom), tright: Math.round(t.right), tw: Math.round(t.width), pe,
        waitHidden: !wcol || getComputedStyle(wcol).display === 'none', parts: [...m.querySelectorAll('.tks-h')].map(h => h.textContent), wait: !!m.querySelector('.tvs-wait, .tvs-addwait'), owner: !!m.querySelector('[data-tvsf="owner"]'),
        foot: [...m.querySelectorAll('.mbm-ft .btn')].map(b => b.textContent.trim()) }; }""")
    c.ok(p and p['key'] == key, f'{who}: the title opens the task\'s own sheet ({p and p["key"]} for {key})')
    # Main.dc.html: the panel sits under the page's bars, beside the table, down to the foot of the screen
    c.ok(p and p['left'] >= 1440 - 480 and abs(p['top'] - p['bars']) <= 2 and p['bottom'] >= 898, f'{who}: at 1440 the sheet is a panel on the right, under the bars ({p})')
    c.ok(p and p['tright'] <= p['left'] + 2 and p['tw'] >= 600 and p['pe'] == 'none', f'{who}: the table stays in view and usable beside it ({p})')
    c.ok(p and p['w'] == 420 and p['waitHidden'], f'{who}: the panel is 420px and the table drops Waiting On and Follow-Up beside it ({p and p["w"]}, {p and p["waitHidden"]})')
    c.ok(p and p['owner'] and p['wait'] and p['parts'][:3] == ['Move the Date', 'Linked', 'Comments'] and 'Hand Off' in p['foot'], f'{who}: the panel holds Owner, Waiting On, then Move the Date, Linked, Comments, and Hand Off ({p and (p["parts"], p["foot"])})')
    await pg.screenshot(path=os.path.join(SHOTS, f'dt_{who}_table_panel.png'))
    # another row's title, clicked with the panel open, opens that one
    k2 = await pg.evaluate("() => [...document.querySelectorAll('#tkall-body .tv-tr')][1].dataset.tvrow")
    await pg.click(f'#tkall-body .tv-tr[data-tvrow="{k2}"] [data-tved="title"]')
    await pg.wait_for_timeout(350)
    now = await pg.evaluate("() => (document.querySelector('#mbm [data-tks]') || { dataset: {} }).dataset.tks")
    c.ok(now == k2, f'{who}: with the panel open, another row opens in it ({now})')
    await pg.evaluate(CLOSE)
    # a board card and a calendar chip open the same sheet
    for m, sel in (('board', '.tv-card .tv-card-t'), ('cal', '.tv-ev[data-tvfield="due"] .tv-evt')):
        await mode(pg, m, 'all', 'all')
        k = await pg.evaluate("s => { const e = document.querySelector('#tkall-body ' + s); if (!e) return null; const r = e.closest('[data-tvrow]').dataset.tvrow; e.click(); return r; }", sel)
        await pg.wait_for_timeout(350)
        got = await pg.evaluate("() => (document.querySelector('#mbm [data-tks]') || { dataset: {} }).dataset.tks")
        c.ok(k and got == k, f'{who}: a {m} item opens the task sheet ({got} for {k})')
        await pg.evaluate(CLOSE)


async def phone_targets(c, pg, who):
    await pg.evaluate("() => { tvPrefs().calMode = 'week'; }")
    for m in ('cards', 'table', 'cal'):
        await mode(pg, m, 'all', 'all')
        t = await pg.evaluate(TARGETS)
        await pg.screenshot(path=os.path.join(SHOTS, f'ph_{who}_{m}_first.png'))
        c.ok(not t['small'], f'{who}: {m}: every target on the first screen is at least 44px ({t["small"]})')
        c.ok(not t['close'], f'{who}: {m}: targets are 8px apart ({t["close"]})')
    # the Board is the wide screen's: asked for on the phone, the List draws (Alan, 2026-10-24)
    await mode(pg, 'board', 'all', 'all')
    c.ok(await pg.evaluate("() => tkMode === 'cards' && !document.querySelector('#tkall-body .tv-board')"), f'{who}: the phone has no Board; it draws the List')
    # the picker on the phone is a sheet from the bottom with the same 44px targets
    opened = await pg.evaluate("() => { const b = document.querySelector('#tkall-body [data-tved=\"owner\"]'); b && b.click(); return !!document.getElementById('tv-pop'); }")
    await pg.wait_for_timeout(200)
    if opened:
        t = await pg.evaluate(TARGETS)
        box = await pg.evaluate("() => { const r = document.getElementById('tv-pop').getBoundingClientRect(); return [Math.round(r.left), Math.round(r.right), Math.round(innerHeight - r.bottom)]; }")
        c.ok(box[0] == 0 and box[1] == 390 and abs(box[2]) <= 1, f'{who}: the picker is a bottom sheet on the phone ({box})')
        c.ok(not t['small'], f'{who}: the picker\'s targets are 44px ({t["small"]})')
        await pg.screenshot(path=os.path.join(SHOTS, f'ph_{who}_picker.png'))
    await pg.evaluate(CLOSE)
    # the task sheet on the phone, as the mockup reads it: ID and job, the title, the rows, the four date buttons, Latest,
    # and a footer of photo, note and the blue next step
    await mode(pg, 'cards', 'all', 'all')
    await pg.evaluate("() => { const r = [...document.querySelectorAll('#tkall-body .tk2-row')].find(r => /^action:/.test(r.dataset.tkkey)); r && r.querySelector('.tk2-title').click(); }")
    await pg.wait_for_timeout(400)
    sh = await pg.evaluate("""() => { const m = document.getElementById('mbm'); if (!m) return null; const r = e => e ? e.getBoundingClientRect() : null;
      const dates = [...m.querySelectorAll('.tvs-dates > *')].map(b => { const q = r(b); return [b.textContent.trim(), Math.round(q.height), Math.round(q.top)]; });
      const rows = [...m.querySelectorAll('.tvs-f')].map(b => Math.round(r(b).height));
      const ft = [...m.querySelectorAll('.mbm-ft button')].filter(b => b.getClientRects().length).map(b => [b.getAttribute('aria-label') || b.textContent.trim(), Math.round(r(b).height), b.classList.contains('primary')]);
      const h3 = m.querySelector('.mbm-hd h3'); const x = m.querySelector('.mbm-x');
      return { kp: !!m.querySelector('.tvs-kp'), title: h3 ? parseFloat(getComputedStyle(h3).fontSize) : 0, close: x ? Math.round(r(x).width) : 0, dates, rows, latest: [...m.querySelectorAll('.tks-h')].some(h => h.textContent === 'Latest'), ft,
        sw: document.documentElement.scrollWidth }; }""")
    c.ok(sh and sh['kp'] and sh['title'] == 22 and sh['close'] >= 44, f'{who}: the phone sheet has ID and job, a 22px title, a 44px close ({sh and (sh["title"], sh["close"])})')
    c.ok(sh and len(sh['dates']) == 4 and all(d[1] >= 44 for d in sh['dates']) and len({d[2] for d in sh['dates']}) == 1 and sh['dates'][0][0] == 'Today' and sh['dates'][2][0].endswith('Mtg') and sh['dates'][3][0] == 'Pick',
         f'{who}: Move the Date is four 44px buttons in a row: Today, Tomorrow, the meeting, Pick ({sh and sh["dates"]})')
    c.ok(sh and sh['rows'] and all(h >= 52 for h in sh['rows']) and sh['latest'], f'{who}: Owner, Due and Follow-Up are 52px rows, and Latest is there ({sh and sh["rows"]})')
    c.ok(sh and len(sh['ft']) == 3 and sh['ft'][0][1] >= 52 and sh['ft'][1][1] >= 52 and sh['ft'][2][2], f'{who}: the footer is photo, note and the blue next step ({sh and sh["ft"]})')
    c.ok(sh and sh['sw'] <= 390, f'{who}: the sheet does not scroll sideways ({sh and sh["sw"]})')
    await pg.screenshot(path=os.path.join(SHOTS, f'ph_{who}_task_sheet.png'))
    await pg.evaluate(CLOSE)
    # the phone's one chip opens the sheet with saved views and layouts
    await mode(pg, 'cards', 'me', 'week')
    await pg.evaluate("() => { const b = document.querySelector('[data-tkfilter]'); b && b.click(); }")
    await pg.wait_for_timeout(250)
    sh = await pg.evaluate("() => [...document.querySelectorAll('#mbm .tkf-h')].map(h => h.textContent)")
    c.ok('Saved Views' in sh and 'Layout' in sh, f'{who}: the filter sheet holds Saved Views and Layout ({sh})')
    await pg.screenshot(path=os.path.join(SHOTS, f'ph_{who}_sheet.png'))
    await pg.evaluate(CLOSE)


async def mine_views(c, pg):
    await sign_in(pg, 'u_chen'); await go(pg, 'tkall')
    await mode(pg, 'table', 'all', 'blocked')
    await pg.evaluate("() => tvSaveDialog()")
    await pg.wait_for_timeout(150)
    await pg.fill('#mbm [data-f="name"]', 'Chen meeting walk')
    await pg.click('#mbm #mbm-ok'); await pg.wait_for_timeout(300)
    t = await toast_of(pg)
    mine = await pg.evaluate("() => tvViews().map(v => v.name)")
    c.ok('Chen meeting walk' in mine and t and 'Open' in t['open'], f'coord: her saved view is in her tabs and toasts with Open ({mine[-2:]})')
    await sign_in(pg, 'u_owner'); await go(pg, 'tkall')
    theirs = await pg.evaluate("() => tvViews().map(v => v.name)")
    c.ok('Chen meeting walk' not in theirs and theirs == ['All Open', 'My Week', 'Waiting on Others', 'Everything'], f'owner: the coordinator\'s view is not in the owner\'s tabs ({theirs})')
    await sign_in(pg, 'u_chen'); await go(pg, 'tkall')
    vid = await pg.evaluate("() => (tvViews().find(v => v.name === 'Chen meeting walk') || {}).id")
    await pg.evaluate("() => { tkWho = 'me'; t2View = 'week'; tkSetMode('cards'); }")
    await pg.evaluate("id => tvApply(id)", vid)
    await pg.wait_for_timeout(250)
    st = await pg.evaluate("() => ({ mode: tkMode, view: t2View, who: tkWho })")
    c.ok(st == {'mode': 'table', 'view': 'blocked', 'who': 'all'}, f'coord: her view puts back what she saved ({st})')


RAIL_ROLES = ('u_owner', 'u_alan', 'u_chen', 'u_billing', 'u_controller', 'u_sarah')
FIELD_ROLES = ('u_angel', 'u_alberto', 'u_alex')

# the table at a width: every open row has its ID, no column past the frame's edge, no sideways scroll; one filter row
TABLE_FIT = r"""() => { const h = document.getElementById('tkall-body'), fr = h.querySelector('.tv-tframe');
  const rows = [...h.querySelectorAll('.tv-tr[data-tvrow]')].filter(r => !r.classList.contains('done'));
  const noid = rows.filter(r => !((r.querySelector('.tv-col-ref .tv-ref') || {}).textContent || '').trim()).map(r => tkResolve(r.dataset.tvrow).x.kind + ': ' + r.innerText.split('\n')[0]);
  const F = fr.getBoundingClientRect(), cut = [...h.querySelectorAll('.tv-th[data-tvcol]')].filter(t => t.getBoundingClientRect().right > F.right + 1).map(t => t.dataset.tvcol);
  const vis = e => e.getClientRects().length > 0;
  return { rows: rows.length, noid: noid.slice(0, 4), cut, fsw: fr.scrollWidth, fcw: fr.clientWidth, sw: document.documentElement.scrollWidth, iw: innerWidth,
    scope: [...h.querySelectorAll('.t2-scope, .tk2-views')].filter(vis).length, saved: !!h.querySelector('.tv-saved'),
    chips: [...h.querySelectorAll('.tv-fchip-b')].map(b => b.innerText.trim()), av: [...h.querySelectorAll('.tv-av')].slice(0, 30).map(a => a.querySelector('svg') ? 'svg' : a.textContent.trim()),
    wait: h.querySelectorAll('.tv-tr .tv-wait.on').length }; }"""


async def polish(c, p):
    """the polish round (2026-10-24): IDs everywhere, initials, one filter row, a table that fits, Tasks in the menu,
    and the phone meeting's actions on the first screen"""
    for w in (1280, 1440):
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={'width': w, 'height': 900})
        pg = await ctx.new_page()
        from harness import URL
        await pg.goto(URL); await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
        await sign_in(pg, 'u_chen'); await go(pg, 'tkall')
        await pg.evaluate("() => { tkSetMode('table'); tvApply('b:all'); }"); await pg.wait_for_timeout(400)
        t = await pg.evaluate(TABLE_FIT)
        c.ok(t['rows'] > 20 and not t['noid'], f'{w}: every open task row has its ID ({t["rows"]} rows; without: {t["noid"]})')
        c.ok(not t['cut'] and t['fsw'] <= t['fcw'] and t['sw'] <= t['iw'], f'{w}: no column cut off and no sideways scroll (cut {t["cut"]}, frame {t["fsw"]}/{t["fcw"]}, page {t["sw"]}/{t["iw"]})')
        c.ok(t['scope'] == 0 and t['saved'], f'{w}: one filter row under the saved tabs ({t["scope"]} old switch rows)')
        c.ok(t['av'] and all(len(a) == 1 and a.isalnum() for a in t['av']), f'{w}: owner avatars are initials ({t["av"][:6]})')
        c.ok(t['wait'] >= 2, f'{w}: the Waiting On column shows who the demo waits on ({t["wait"]} chips)')
        await pg.evaluate("() => tvApply('b:week')"); await pg.wait_for_timeout(300)
        t = await pg.evaluate(TABLE_FIT)
        c.ok(t['chips'][:2] == ['Owner: Me', 'Due: Soon'], f'{w}: My Week says its filters as chips ({t["chips"]})')
        # the board and the List show the ID too
        await pg.evaluate("() => { tvApply('b:all'); tkSetMode('board'); }"); await pg.wait_for_timeout(300)
        bd = await pg.evaluate("() => [...document.querySelectorAll('#tkall-body .tv-bcol:not(.tv-bextra) .tv-card')].filter(c => !(c.querySelector('.tv-ref') || {}).textContent).length")
        c.ok(bd == 0, f'{w}: every board card shows its ID ({bd} without)')
        await pg.evaluate("() => tkSetMode('cards')"); await pg.wait_for_timeout(300)
        ls = await pg.evaluate("() => [...document.querySelectorAll('#tkall-body .tk2-row[data-tkkey]')].filter(r => !r.querySelector('.tk2-key, .tv-ref')).map(r => r.dataset.tkkey).slice(0, 4)")
        c.ok(not ls, f'{w}: every List row shows its ID ({ls})')
        if w == 1440:
            await pg.screenshot(path=os.path.join(SHOTS, 'dt_polish_list.png'))
            # Tasks under Today in the rail for every office role; it opens the one list; the field keeps its menus
            for uid in RAIL_ROLES + FIELD_ROLES:
                await sign_in(pg, uid); await pg.wait_for_timeout(150)
                r = await pg.evaluate("""() => { const B = [...document.querySelectorAll('#nav-groups > button')].map(b => b.dataset.grp);
                  const i = B.indexOf('mytasks'), t = document.querySelector('#nav-groups > button[data-grp="mytasks"]');
                  if (t) t.click();
                  const n = t ? +((t.querySelector('.n') || {}).textContent || 0) : null;
                  return { under: i > 0 && B[i - 1] === 'home', has: i >= 0, view, n, want: tkTasksN(),
                    lit: !!document.querySelector('#nav-groups > button[data-grp="mytasks"].on'), label: t ? t.innerText.replace(/\\s*\\d+$/, '').trim() : '' }; }""")
                if uid in FIELD_ROLES:
                    c.ok(not r['has'], f'{uid}: the field menu has no Tasks entry')
                else:
                    c.ok(r['under'] and r['label'] == 'Tasks' and r['view'] == 'tkall' and r['lit'], f'{uid}: Tasks sits under Today and opens the one list ({r})')
                    c.ok(r['n'] == r['want'], f'{uid}: the Tasks badge is the one Tasks number, their Due Soon ({r["n"]} vs {r["want"]})')
        await b.close()
    # the phone: Tasks in the menu drawer, and Meeting Mode's eight actions on the first screen with the toast above Next
    b, pg, errs = await open_app(p, True)
    await sign_in(pg, 'u_alan')
    r = await pg.evaluate("() => { const B = [...document.querySelectorAll('#nav-groups > button')].map(b => b.dataset.grp); return B.indexOf('mytasks') === B.indexOf('home') + 1; }")
    c.ok(r, 'pm 390: Tasks sits under Today in the phone menu')
    bar = await pg.evaluate("() => [...document.querySelectorAll('#mtabs button[data-mv]')].map(b => b.dataset.mv)")
    c.ok(bar == ['home', 'chat', 'ovjobs', 'tkall'], f'pm 390: Tasks is the fourth shortcut ({bar})')
    await sign_in(pg, 'u_owner'); await go(pg, 'tkall')
    await pg.evaluate("() => { mtStart({}); renderTkAll(); window.scrollTo(0, 0); }"); await pg.wait_for_timeout(500)
    m = await pg.evaluate("""() => { const A = [...document.querySelectorAll('.mm-act')].map(e => e.getBoundingClientRect()), nav = document.querySelector('.mm-nav').getBoundingClientRect();
      const top = document.querySelector('.mm-top'), t = top.getBoundingClientRect();
      toast('Phone toast check', [{ label: 'Open', run: () => {} }]);
      const T = document.getElementById('toast').getBoundingClientRect();
      return { n: A.length, bottom: Math.round(Math.max(...A.map(r => r.bottom))), nav: Math.round(nav.top), topH: Math.round(t.height),
        menu: !!top.querySelector('details [data-mmend]') && !!top.querySelector('details [data-mmagenda]') && !!top.querySelector('details [data-mmfollow]'),
        toast: Math.round(T.bottom), sw: document.documentElement.scrollWidth, title: document.querySelector('.mm-card .mm-title').getClientRects().length,
        notes: [...document.querySelectorAll('.mm-comments .mm-comment')].filter(e => e.getClientRects().length).length }; }""")
    c.ok(m['n'] == 8 and m['bottom'] <= min(844, m['nav']), f'owner 390: the eight meeting actions sit on the first screen, above Previous and Next ({m})')
    c.ok(m['title'] > 0, f'owner 390: the card keeps its title (the page header never lifts it out)')
    c.ok(m['topH'] <= 116 and m['menu'], f'owner 390: the meeting header is two short lines (PhoneMeeting.dc.html), Follow, Agenda and End behind one menu ({m["topH"]}px)')
    c.ok(m['toast'] <= m['nav'], f'owner 390: the toast sits above the meeting footer ({m["toast"]} vs {m["nav"]})')
    c.ok(m['notes'] <= 1 and m['sw'] <= 390, f'owner 390: the notes are cut to the latest behind More, no sideways scroll ({m["notes"]}, {m["sw"]})')
    await pg.wait_for_timeout(2600)
    await pg.screenshot(path=os.path.join(SHOTS, 'ph_polish_meeting.png'))
    c.ok(not errs, f'polish: no page errors ({errs[:3]})')
    await b.close()


# ---- Alan's mockup (taskmock, approved 2026-10-24): the computed sizes and colours of the key parts, the phone's page,
# the bar, Follow mode and the quick-add rules. A difference here is a difference Alan would see side by side.
DESK = r"""() => { const q = s => document.querySelector(s), cs = e => e ? getComputedStyle(e) : {}, R = e => e ? e.getBoundingClientRect() : { height: 0, width: 0, top: 0, bottom: 0 };
  const row = [...document.querySelectorAll('#tkall-body .tv-tr')].slice(0, 3), pill = k => { const e = q('#tkall-body .tv-pill.tv-st-' + k); return e ? [cs(e).backgroundColor, cs(e).color] : null; };
  const chip = q('#tkall-body .tv-tr .tv-wait.on .tv-chip-in'), gc = q('#tkall-body .tv-gcard'), h2 = q('#tkall-body .tv-ph h2'), srch = q('#tkall-body .tv-search'), nt = q('#tkall-body #tk-new');
  const tab = q('#tkall-body .tv-sv.on'), tabn = q('#tkall-body .tv-sv.on .n'), gbar = q('#tkall-body .tv-tg .tv-bar'), th = q('#tkall-body .tv-thead');
  return { rows: row.map(r => Math.round(R(r).height)), circle: Math.round(R(q('#tkall-body .tv-tr .tv-check')).width), title: [cs(q('#tkall-body .tv-ttx')).fontSize, cs(q('#tkall-body .tv-ttx')).fontWeight],
    id: [cs(q('#tkall-body .tv-tr .tv-ref')).fontSize, cs(q('#tkall-body .tv-tr .tv-ref')).fontVariantNumeric, cs(q('#tkall-body .tv-tr .tv-ref')).color],
    pills: { todo: pill('todo'), doing: pill('doing'), waiting: pill('waiting') }, chip: chip ? [cs(chip).backgroundColor, cs(chip).color, !!chip.querySelector('svg'), Math.round(R(chip).height)] : null,
    card: gc ? [cs(gc).borderRadius, cs(gc).boxShadow.includes('236, 238, 242')] : null, head: [Math.round(R(th).height), cs(th).position, cs(q('#tkall-body .tv-th[data-tvcol]')).fontSize],
    h2: [cs(h2).fontSize, cs(h2).fontWeight], lead: !!q('#tkall-body .tv-ph .lead') && R(q('#tkall-body .tv-ph .lead')).height > 0, search: Math.round(R(srch).width), newTask: cs(nt).backgroundColor,
    tab: [cs(tab).fontSize, cs(tab).boxShadow.includes('36, 86, 201'), cs(tabn).color], bar: gbar ? [Math.round(R(gbar).width), Math.round(R(gbar).height)] : null }; }"""


async def match(c, p):
    b, pg, errs = await open_app(p, False)
    await sign_in(pg, 'u_chen'); await go(pg, 'tkall')
    await pg.evaluate("() => { tkSetMode('table'); tvApply('b:all'); }"); await pg.wait_for_timeout(400)
    d = await pg.evaluate(DESK)
    c.ok(all(h == 64 for h in d['rows']) and d['circle'] == 44, f'mockup: rows are 64px with a 44px done circle ({d["rows"]}, {d["circle"]})')
    c.ok(d['title'] == ['15px', '500'] and d['id'][0] == '13px' and 'tabular-nums' in d['id'][1] and d['id'][2] == 'rgb(106, 112, 128)', f'mockup: title 15px/500, ID 13px gray tabular figures ({d["title"]}, {d["id"]})')
    c.ok(d['pills'] == {'todo': ['rgb(238, 240, 243)', 'rgb(62, 68, 80)'], 'doing': ['rgb(230, 238, 253)', 'rgb(29, 71, 168)'], 'waiting': ['rgb(255, 241, 214)', 'rgb(122, 74, 0)']}, f'mockup: the status pills\' colours ({d["pills"]})')
    c.ok(d['chip'] and d['chip'][:3] == ['rgb(255, 246, 229)', 'rgb(122, 74, 0)', True] and d['chip'][3] == 28, f'mockup: the Waiting On chip is amber with a clock, 28px ({d["chip"]})')
    c.ok(d['card'] == ['12px', True] and d['head'] == [44, 'sticky', '12px'], f'mockup: rows in a 12px card with the #ECEEF2 ring; a 44px sticky 12px header ({d["card"]}, {d["head"]})')
    c.ok(d['h2'] == ['22px', '700'] and not d['lead'] and d['search'] == 280 and d['newTask'] == 'rgb(36, 86, 201)', f'mockup: the top bar: Tasks 22px/700, no subtitle, a 280px search, New Task blue ({d})')
    c.ok(d['tab'][0] == '14px' and d['tab'][1] and d['tab'][2] == 'rgb(106, 112, 128)' and d['bar'] == [120, 6], f'mockup: underline tabs 14px with gray counts; the group bar 120 by 6 ({d["tab"]}, {d["bar"]})')
    # the panel: 420px, a 21px title, label and value rows
    key = await pg.evaluate("() => document.querySelector('#tkall-body .tv-tr').dataset.tvrow")
    await pg.evaluate("k => tkSheet(k)", key); await pg.wait_for_timeout(400)
    pn = await pg.evaluate("""() => { const m = document.getElementById('mbm'), b = m.querySelector('.mbm-box'), h = m.querySelector('.mbm-hd h3'), f = m.querySelector('.tvs-f');
      return { w: Math.round(b.getBoundingClientRect().width), h: [getComputedStyle(h).fontSize, getComputedStyle(h).fontWeight], rows: getComputedStyle(f).display, cols: getComputedStyle(f).gridTemplateColumns.split(' ')[0] }; }""")
    c.ok(pn['w'] == 420 and pn['h'] == ['21px', '700'] and pn['rows'] == 'grid' and pn['cols'] == '110px', f'mockup: the panel is 420px, a 21px/700 title, label and value rows ({pn})')
    await pg.evaluate(CLOSE)
    # the Board: gray wells, white 12px cards
    await pg.evaluate("() => { tkSetMode('board'); tvPrefs().boardBy = 'status'; renderTkAll(); }"); await pg.wait_for_timeout(400)
    bd = await pg.evaluate("""() => { const w = document.querySelector('#tkall-body .tv-bcol'), k = document.querySelector('#tkall-body .tv-card'), s = getComputedStyle(w), t = getComputedStyle(k);
      return [s.backgroundColor, s.borderRadius, s.padding, t.borderRadius, t.padding, getComputedStyle(k.querySelector('.tv-card-t')).fontSize, !document.querySelector('#tkall-body .tv-saved')]; }""")
    c.ok(bd == ['rgb(239, 241, 244)', '14px', '12px', '12px', '14px', '15px', True], f'mockup: the board\'s wells #EFF1F4, 14px, 12px padding; cards 12px, 14px padding, 15px titles; no tabs ({bd})')
    await pg.screenshot(path=os.path.join(SHOTS, 'dt_match_board.png'))
    await b.close()
    # ---- the phone (Phone.dc.html)
    b, pg, errs2 = await open_app(p, True)
    await sign_in(pg, 'u_chen'); await go(pg, 'tkall')
    await pg.evaluate("() => { tkMode = 'cards'; tkWho = 'me'; t2View = 'week'; t2Group = null; renderTkAll(); window.scrollTo(0, 0); }"); await pg.wait_for_timeout(400)
    ph = await pg.evaluate("""() => { const vis = e => { if (!e) return false; const r = e.getBoundingClientRect(), s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
      const row = [...document.querySelectorAll('#tkall-body .tk2-row')].find(r => r.querySelector('.tv-mwait'));
      const sub = row && row.querySelector('.tk2-sub'), w = row && row.querySelector('.tv-mwait');
      const search = [...document.querySelectorAll('button, input')].filter(vis).filter(e => /search/i.test(e.getAttribute('aria-label') || e.placeholder || e.id || ''));
      const adds = [...document.querySelectorAll('[data-tvqa], .tk2-fab, #tb-new, [data-tvqaopen]')].filter(vis);
      const h = document.querySelector('#tkall-body .tv-phtitle');
      return { own: !!(row && sub && w && !sub.contains(w) && w.getBoundingClientRect().top >= sub.getBoundingClientRect().bottom - 1 && w.getBoundingClientRect().right <= row.getBoundingClientRect().right),
        search: search.length, adds: adds.map(e => e.dataset.tvqa !== undefined ? 'line' : e.dataset.tvqaopen !== undefined ? 'plus' : e.id || e.className),
        title: h ? [getComputedStyle(h).fontSize, getComputedStyle(h).fontWeight] : null, sub: !!document.querySelector('#subnav') && vis(document.querySelector('#subnav')), top: vis(document.querySelector('.topbar')) }; }""")
    c.ok(ph['own'], f'mockup 390: the Waiting On chip sits on its own line under the meta line, not cut off')
    c.ok(ph['search'] == 1 and ph['adds'] == ['plus', 'line'] and not ph['sub'] and not ph['top'], f'mockup 390: one search and one add line, no app header extras or sub-tabs ({ph})')
    c.ok(ph['title'] == ['22px', '700'], f'mockup 390: Tasks 22px/700 ({ph["title"]})')
    await sign_in(pg, 'u_owner'); await go(pg, 'tkall')
    await pg.evaluate("() => { tkMode = 'cards'; tkWho = 'all'; t2View = 'all'; t2Group = null; renderTkAll(); window.scrollTo(0, 0); }"); await pg.wait_for_timeout(400)
    n7 = await pg.evaluate("""() => { const bar = document.getElementById('mtabs'), floor = bar ? bar.getBoundingClientRect().top : innerHeight;
      const R = [...document.querySelectorAll('#tkall-body .tk2-row')].map(r => r.getBoundingClientRect()).filter(r => r.top >= 0 && r.bottom <= floor);
      return { n: R.length, h: R.slice(0, 3).map(r => Math.round(r.height)) }; }""")
    c.ok(n7['n'] >= 7 and all(h >= 64 for h in n7['h']), f'mockup 390: at least 7 task rows on the first screen, 64px each ({n7})')
    await pg.screenshot(path=os.path.join(SHOTS, 'ph_match_list.png'))
    # the bar: Tasks for the coordinator and billing, its badge the one Tasks number (tkTasksN, the person's Due Soon;
    # taskfix #1); billing's bar starts with Today like everyone's (taskfix #14)
    for uid, at in (('u_chen', 2), ('u_billing', 2), ('u_owner', 3), ('u_alan', 3)):
        await sign_in(pg, uid); await pg.wait_for_timeout(200)
        t = await pg.evaluate("""() => { const B = [...document.querySelectorAll('#mtabs button[data-mv]')], i = B.findIndex(b => b.dataset.mv === 'tkall'), b = B[i];
          return { i, n: b ? +((b.querySelector('.n') || {}).textContent || 0) : -1, want: tkTasksN() }; }""")
        c.ok(t['i'] == at and t['n'] == t['want'], f'mockup 390: {uid} has Tasks in the bar at {at} with the one Tasks badge ({t})')
    # the quick add: invented sentences, filled in by the rules; the fourth names its job by part of its address (the
    # whole phrase leaves the title: taskfix #13)
    await sign_in(pg, 'u_chen'); await go(pg, 'tkall')
    P = await pg.evaluate("""() => ["Angel, measure the windows at 206 Lenox tomorrow, I'm in charge", 'Sarah to confirm the tile selection for 121 State Street by Friday', 'Call the plumbing inspector next meeting, Alan is in charge', 'Angel, measure the windows at 121 State tomorrow, I am in charge'].map(tvQaParse)""")
    td = await pg.evaluate("() => ({ tom: iso(addDays(parse(today()), 1)), fri: (() => { const d = parse(today()); const n = (5 - d.getDay() + 7) % 7 || 7; return iso(addDays(d, n)); })(), nm: tvNextMeeting() })")
    want = [('Measure the windows', 'p206', 'Chen Biron', 'Angel', td['tom']), ('Confirm the tile selection', 'p121', 'Chen Biron', 'Sarah Davis', td['fri']), ('Call the plumbing inspector', '', 'Alan', '', td['nm']), ('Measure the windows', 'p121', 'Chen Biron', 'Angel', td['tom'])]
    for got, w in zip(P, want):
        c.ok((got['title'], got['pid'], got['owner'], got['doer'], got['due']) == w, f'quick add: "{got["text"]}" reads {w} ({got})')
    c.ok(await pg.evaluate("() => tvQaParse('Finish the overhead rate before billing').doer === ''"), 'quick add: "before billing" names nobody (a seat named for its job is a person only as a name)')
    made = await pg.evaluate("""() => { const m = tvQaCreate(tvQaParse("Angel, measure the windows at 206 Lenox tomorrow, I'm in charge")); const t = document.getElementById('toast');
      return m ? { code: m.rec.code, owner: m.rec.assignee, collab: m.rec.collaborators, due: m.rec.due, toast: t ? t.innerText : '', open: !!(t && [...t.querySelectorAll('a')].some(a => a.textContent === 'Open')) } : null; }""")
    c.ok(made and made['code'].startswith('LEN-') and made['owner'] == 'Chen Biron' and made['collab'] == ['Angel'] and made['due'] == td['tom'] and made['open'], f'quick add: Add makes the task through the one create path, with its ID, owner, doer, date and a toast with Open ({made})')
    sheet = await pg.evaluate("""() => { tvQuickAddSheet("Angel, measure the windows at 206 Lenox tomorrow, I'm in charge"); const m = document.getElementById('mbm');
      return { rows: [...m.querySelectorAll('.tvqa-l')].map(e => e.textContent), h: [...m.querySelectorAll('.tvqa-row')].map(e => Math.round(e.getBoundingClientRect().height)), id: (m.querySelector('[data-tvqaf="pid"] .tvqa-g') || {}).textContent || '' }; }""")
    c.ok(sheet['rows'] == ['Task', 'Project', 'Owner', 'Doing It', 'Due'] and all(h >= 52 for h in sheet['h']) and sheet['id'].startswith('· LEN-'), f'quick add: the sheet fills Task, Project with the new ID, Owner, Doing It and Due in 52px rows ({sheet})')
    await pg.screenshot(path=os.path.join(SHOTS, 'ph_match_quickadd.png'))
    await pg.evaluate(CLOSE)
    # Follow mode: on the phone, someone who is not driving follows the driver's card, with Actions in a sheet
    await sign_in(pg, 'u_owner'); await go(pg, 'tkall')
    fo = await pg.evaluate("""() => { mtStart({}); const m = mtCurrent(); m.presenterUid = 'u_chen'; m.presenter = 'Chen Biron'; mmOn = true; renderTkAll();
      const bar = document.querySelector('.mm-folbar');
      return { follow: mmFollow, fol: !!document.querySelector('.mm-phone.mm-fol'), bar: bar ? bar.innerText.replace(/\\s+/g, ' ').trim() : '', acts: document.querySelectorAll('.mm-main > .mm-acts').length,
        sheet: !!document.querySelector('[data-mmactsheet]'), sofar: !!document.querySelector('.mm-sofar') }; }""")
    c.ok(fo['follow'] and fo['fol'] and fo['bar'].startswith('Following Chen') and fo['acts'] == 0 and fo['sheet'] and fo['sofar'], f'Follow mode is the default on the phone for someone not driving ({fo})')
    await pg.evaluate("() => document.querySelector('[data-mmactsheet]').click()"); await pg.wait_for_timeout(250)
    acts = await pg.evaluate("() => [...document.querySelectorAll('#mbm [data-mmsact]')].map(b => b.dataset.mmsact)")
    c.ok(acts == ['date', 'note', 'done', 'owner', 'wait', 'track', 'fyi', 'skip'], f'Follow mode: Actions opens the eight actions as a sheet ({acts})')
    await pg.evaluate(CLOSE)
    await pg.screenshot(path=os.path.join(SHOTS, 'ph_match_follow.png'))
    await pg.evaluate("() => mtEnd(mtCurrent())")
    c.ok(not errs and not errs2, f'mockup: no page errors ({(errs + errs2)[:3]})')
    await b.close()


async def main():
    c = Checks()
    async with async_playwright() as p:
        for phone in (False, True):
            b, pg, errs = await open_app(p, phone)
            for uid, who in (('u_chen', 'coord'), ('u_owner', 'owner')):
                await sign_in(pg, uid); await go(pg, 'tkall')
                label = f'{who} {"390" if phone else "1440"}'
                await one_number(c, pg, label, phone)
                if phone:
                    await phone_targets(c, pg, label)
                else:
                    await sheet_and_table(c, pg, label)
                    await drags(c, pg, label)
                    await bulk(c, pg, label)
                    await edits(c, pg, label)
            if not phone:
                await mine_views(c, pg)
            c.ok(not errs, f'{"phone" if phone else "desktop"}: no page errors ({errs[:3]})')
            await b.close()
        await polish(c, p)
        await match(c, p)
    sys.exit(c.done())

asyncio.run(main())
