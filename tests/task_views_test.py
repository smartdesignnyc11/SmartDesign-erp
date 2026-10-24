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
    for m in ('cards', 'table', 'board', 'cal'):
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
    for m in ('table', 'board'):
        await mode(pg, m, 'me', 'week')
        s = await pg.evaluate(SHOWN)
        want = await pg.evaluate("() => tkMyCounts().week")
        c.ok(s['n'] == want, f'{who}: {m} · Mine · Due Soon says {s["n"]}, the list counts {want}')
    # saved tabs: each gives the count of the list it stands for
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
      const wcol = document.querySelector('#tkall-body .tv-th.tv-col-wait');
      return { key: (m.querySelector('[data-tks]') || { dataset: {} }).dataset.tks, left: Math.round(r.left), w: Math.round(r.width), h: Math.round(r.height), tright: Math.round(t.right), tw: Math.round(t.width), pe,
        waitHidden: !wcol || getComputedStyle(wcol).display === 'none', parts: [...m.querySelectorAll('.tks-h')].map(h => h.textContent), wait: !!m.querySelector('.tvs-wait, .tvs-addwait'), owner: !!m.querySelector('[data-tvsf="owner"]'),
        foot: [...m.querySelectorAll('.mbm-ft .btn')].map(b => b.textContent.trim()) }; }""")
    c.ok(p and p['key'] == key, f'{who}: the title opens the task\'s own sheet ({p and p["key"]} for {key})')
    c.ok(p and p['left'] >= 1440 - 480 and p['h'] >= 880, f'{who}: at 1440 the sheet is a panel on the right ({p})')
    c.ok(p and p['tright'] <= p['left'] + 2 and p['tw'] >= 600 and p['pe'] == 'none', f'{who}: the table stays in view and usable beside it ({p})')
    c.ok(p and p['w'] == 420 and p['waitHidden'], f'{who}: the panel is 420px and the table drops Waiting On and Follow-Up beside it ({p and p["w"]}, {p and p["waitHidden"]})')
    c.ok(p and p['owner'] and p['wait'] and 'Move the Date' in p['parts'] and 'Comments' in p['parts'] and 'Hand Off' in p['foot'], f'{who}: the panel holds Owner, Waiting On, Move the Date, Comments and Hand Off ({p and (p["parts"], p["foot"])})')
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
    for m in ('cards', 'table', 'board', 'cal'):
        await mode(pg, m, 'all', 'all')
        t = await pg.evaluate(TARGETS)
        await pg.screenshot(path=os.path.join(SHOTS, f'ph_{who}_{m}_first.png'))
        c.ok(not t['small'], f'{who}: {m}: every target on the first screen is at least 44px ({t["small"]})')
        c.ok(not t['close'], f'{who}: {m}: targets are 8px apart ({t["close"]})')
    # the picker on the phone is a sheet from the bottom with the same 44px targets
    await mode(pg, 'board', 'all', 'all')
    opened = await pg.evaluate("() => { const b = document.querySelector('#tkall-body .tv-card [data-tved=\"owner\"]'); b && b.click(); return !!document.getElementById('tv-pop'); }")
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
                  return { under: i > 0 && B[i - 1] === 'home', has: i >= 0, view, n, want: tkMyCounts().today || 0,
                    lit: !!document.querySelector('#nav-groups > button[data-grp="mytasks"].on'), label: t ? t.innerText.replace(/\\s*\\d+$/, '').trim() : '' }; }""")
                if uid in FIELD_ROLES:
                    c.ok(not r['has'], f'{uid}: the field menu has no Tasks entry')
                else:
                    c.ok(r['under'] and r['label'] == 'Tasks' and r['view'] == 'tkall' and r['lit'], f'{uid}: Tasks sits under Today and opens the one list ({r})')
                    c.ok(r['n'] == r['want'], f'{uid}: the Tasks badge is their late and due-today count ({r["n"]} vs {r["want"]})')
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
    c.ok(m['topH'] <= 60 and m['menu'], f'owner 390: the meeting header is one line, Follow, Agenda and End behind one menu ({m["topH"]}px)')
    c.ok(m['toast'] <= m['nav'], f'owner 390: the toast sits above the meeting footer ({m["toast"]} vs {m["nav"]})')
    c.ok(m['notes'] <= 1 and m['sw'] <= 390, f'owner 390: the notes are cut to the latest behind More, no sideways scroll ({m["notes"]}, {m["sw"]})')
    await pg.wait_for_timeout(2600)
    await pg.screenshot(path=os.path.join(SHOTS, 'ph_polish_meeting.png'))
    c.ok(not errs, f'polish: no page errors ({errs[:3]})')
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
    sys.exit(c.done())

asyncio.run(main())
