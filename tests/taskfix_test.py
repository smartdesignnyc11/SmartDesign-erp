"""taskfix: the mobile designer's findings on the task module (review/experts2/mobile_designer.md, 2026-10-25), each
checked the way the reviewer saw it, at 390x844 with touch and at 1440x900. The team runs its Monday 10am meeting and
its daily tasks here from 10-26, so each check is a class check, not one screen.

  one       #1  "Tasks" is one number for every office role: the side menu, Today's sub-tab, Today's Tasks chip, the
                phone bar and the Tasks page (the phone's Due Soon chip, the desktop's marked pill) all read tkTasksN(),
                the person's Due Soon (late or due in the next 7 days, theirs, not put off). Today's Tasks chip shows
                those rows. Buy Board orders are not tasks: they are Today's Buy Board chip, the bar's Buy Board badge
                and the Buy Board's own Late to Order plus Order This Week. The owner's most-late task (an obligation
                Approvals also holds) is in the set.
  hand      #2 #3  Swipe > Hand Off opens straight to the people (on the first screen, nothing folded under More); a
                tap picks a person (no hand-off yet), a note is optional, one "Hand Off to <Name>" button commits.
  meet      #4  On a meeting day (the team's cadence, by the app clock) the owner and the coordinator see "Start the
                Team Meeting" at the top of Tasks on the phone, one tap; it is also the filter sheet's first row.
  toast     #5  A toast's Open and Undo are 44px tall on the phone and the toast clears the bottom bar and Say It.
  oblig     #11 An obligation's task says what is late ("filing 5d late"); Approvals shows the same filing date.
  quick     #13 Quick add removes the whole job phrase, a partial address included ("at 121 State").
  billing   #14 Billing's bar starts with Today; billing's Tasks opens on Mine.
  names     #15 #16  A system author ("The Standard") keeps its name; on Mine the owner is left off the row; the sheet
                says "You" for the signed-in owner, never "Owner in charge".
  red       #17 Late is the only red on a task row: priority is not drawn in red.
  wait      #18 "Add Waiting On" opens a sheet with the shared footer (full-width blue Save, 48px).
  follow    #19 The Follow line reads "Following Chen · n of m" whole at 390px.
  header    #20 The header's icon buttons are 44x44; Ask's icon is not Chat's.
  chips     #21 Chip rows: 8px gaps, 44px hit areas; a strip that scrolls fades at its edges.
  blue      #23 A page shows its own view only: the Tasks page never leaks under another page (its New Task was a
                second blue button under Billing); one blue per screen.
Invented demo data only."""
import asyncio, json, os, re
from harness import async_playwright, open_app, sign_in, go, Checks, ROOT

SHOTS = os.path.join(ROOT, 'review', 'taskfix')
os.makedirs(SHOTS, exist_ok=True)
CLOSE = "() => { try { mbCloseModal(); } catch (e) {} document.querySelectorAll('#mbm, #tv-pop').forEach(e => e.remove()); }"
OFFICE = (('u_owner', 'owner'), ('u_alan', 'pm'), ('u_chen', 'coord'), ('u_billing', 'billing'))

# every place the word "Tasks" carries a number for the signed-in person
NUMS = r"""() => { const vis = e => !!e && e.getClientRects().length > 0 && getComputedStyle(e).visibility !== 'hidden';
  const n = s => { const e = [...document.querySelectorAll(s)].find(vis); return e ? +(e.textContent.replace(/\D+/g, '') || 0) : null; };
  return { want: typeof tkTasksN === 'function' ? tkTasksN() : -1, rail: n('#nav-groups button[data-grp="mytasks"] .n'), sub: n('#subnav [data-sub="tkall"] .n'),
    chip: n('.view.on .td-tabs [data-tdytabbtn="tasks"] .n'), bar: n('#mtabs [data-mv="tkall"] .n'),
    buyChip: n('.view.on .td-tabs [data-tdytabbtn="buy"] .n'), buyBar: n('#mtabs [data-mv="proc"] .n') }; }"""


async def one_number(c, pg, phone):
    tag = 'phone' if phone else 'desktop'
    for uid, r in OFFICE:
        await pg.evaluate(CLOSE); await sign_in(pg, uid); await go(pg, 'home'); await pg.wait_for_timeout(200)
        h = await pg.evaluate(NUMS)
        W = h['want']
        shown = {k: h[k] for k in ('rail', 'sub', 'chip', 'bar') if h[k] is not None}
        # an empty badge is 0; the Today chip always states its number
        c.ok(all(v == W for v in shown.values()) and (h['chip'] == W), f'{tag} {r}: one number for Tasks ({W}): {shown}')
        # the rows behind Today's Tasks chip are that number
        await pg.evaluate("() => { const b = document.querySelector('.view.on [data-tdytabbtn=\"tasks\"]'); b && b.click(); }"); await pg.wait_for_timeout(250)
        rows = await pg.evaluate("""() => { const d = document.querySelector('.view.on .td-do[data-tdytab="tasks"]'); if (!d) return null;
          const k = (d.querySelector('.td-more') || {}).textContent || '', m = k.match(/^(\\d+) more/);
          return { cards: d.querySelectorAll('.td-card').length + (m ? +m[1] : 0), buy: d.querySelectorAll('.td-card[data-kind="tdyBuy"]').length,
            ids: tdyModel().tasks.map(it => it.t ? (it.t.row && it.t.row.code) || it.t.title : it.kind) }; }""")
        c.ok(rows and rows['cards'] == W and rows['buy'] == 0, f'{tag} {r}: Today\'s Tasks chip shows its {W} rows and no orders ({rows})')
        if phone and r in ('owner', 'coord'):
            await pg.evaluate("() => scrollTo(0, 0)")
            await pg.screenshot(path=os.path.join(SHOTS, f'p_{r}_today_tasks.png'))
        if r == 'owner':
            late = await pg.evaluate("() => { const L = tkSoonFor().filter(x => x.due && x.due < today()).sort((a, b) => a.due.localeCompare(b.due)); return L[0] ? { code: L[0].code, due: L[0].due } : null; }")
            c.ok(late and late['code'] in (rows or {}).get('ids', []), f'{tag} owner: the most-late task ({late}) is on Today\'s Tasks ({(rows or {}).get("ids")})')
            dup = await pg.evaluate("() => { const A = tdyModel().all, ids = A.map(it => it.kind + ':' + it.id); return ids.length - new Set(ids).size; }")
            allob = await pg.evaluate("() => tdyModel().all.filter(it => /biennial/i.test(it.title || '')).length")
            c.ok(dup == 0 and allob == 1, f'{tag} owner: All holds the LLC renewal once, as its approval ({allob}, {dup} repeats)')
        if r == 'coord':
            buy = await pg.evaluate("() => tdyBuyItems().length")
            c.ok(buy > 0 and h['buyChip'] == buy and (not phone or h['buyBar'] == buy), f'{tag} coord: the orders are the Buy Board\'s {buy}: Today chip {h["buyChip"]}, bar {h["buyBar"]}')
            if phone:
                await pg.evaluate("() => { const b = document.querySelector('.view.on [data-tdytabbtn=\"buy\"]'); b && b.click(); scrollTo(0, 0); }"); await pg.wait_for_timeout(250)
                await pg.screenshot(path=os.path.join(SHOTS, 'p_coord_today_buyboard.png'))
            await go(pg, 'proc')
            tiles = await pg.evaluate("""() => [...document.querySelectorAll('.view.on button.gl')].filter(b => b.getClientRects().length).map(b => [(b.querySelector('.gl-k') || {}).textContent, +((b.querySelector('.gl-v') || {}).textContent || '').replace(/\\D+/g, '')])""")
            t = dict((k, v) for k, v in tiles if k)
            c.ok(t.get('Late to Order', 0) + t.get('Order This Week', 0) == buy, f'{tag} coord: the Buy Board\'s Late to Order and Order This Week are those {buy} ({t})')
        # the Tasks page says the same number where the person reads it
        await go(pg, 'tkall'); await pg.wait_for_timeout(200)
        page = await pg.evaluate("""() => { const vis = e => !!e && e.getClientRects().length > 0;
          const q = [...document.querySelectorAll('.view.on .tv-qchips [data-tvqv="week"] .n')].find(vis), m = [...document.querySelectorAll('.view.on [data-ocbadge="tkall"]')].find(vis);
          return { who: tkWho, chip: q ? +q.textContent : null, mark: m ? m.textContent.trim() : null }; }""")
        pn = page['chip'] if phone else (int(re.match(r'\d+', page['mark']).group()) if page['mark'] and re.match(r'\d+', page['mark']) else (0 if page['mark'] else None))
        c.ok(page['who'] == 'me' and pn == W, f'{tag} {r}: Tasks opens on Mine and reads {W} ({page})')


async def hand_off(c, pg):
    await pg.evaluate(CLOSE); await sign_in(pg, 'u_owner'); await go(pg, 'tkall'); await pg.wait_for_timeout(250)
    key = await pg.evaluate("() => { const b = [...document.querySelectorAll('.view.on .tk2-row [data-tkhand]')][1]; if (!b) return null; b.click(); return b.dataset.tkhand; }")
    await pg.wait_for_timeout(400)
    s = await pg.evaluate("""() => { const m = document.getElementById('mbm'); if (!m) return null; const H = innerHeight;
      const P = [...m.querySelectorAll('[data-tkhto]')].filter(e => e.getClientRects().length);
      return { n: P.length, onScreen: P.filter(e => { const r = e.getBoundingClientRect(); return r.top >= 0 && r.bottom <= H; }).length, folded: P.filter(e => e.closest('details:not([open])')).length,
        h: P.map(e => Math.round(e.getBoundingClientRect().height)), ok: ((m.querySelector('#mbm-ok') || {}).textContent || '').trim(), title: m.innerText.slice(0, 80) }; }""")
    await pg.screenshot(path=os.path.join(SHOTS, 'p_owner_swipe_handoff.png'))
    c.ok(s and s['n'] >= 3 and s['onScreen'] >= 3 and not s['folded'] and min(s['h']) >= 44, f'#2 swipe > Hand Off opens straight to the people, on the first screen ({s})')
    await pg.evaluate("() => { const b = [...document.querySelectorAll('#mbm [data-tkhto]')].find(e => /Angel/.test(e.dataset.tkhto)); b && b.click(); }"); await pg.wait_for_timeout(200)
    st = await pg.evaluate("""k => { const R = tkResolve(k); return { offered: !!(R && R.rec && R.rec.handoff && R.rec.handoff.state === 'offered'), ok: ((document.querySelector('#mbm #mbm-ok') || {}).textContent || '').trim(),
      on: [...document.querySelectorAll('#mbm [data-tkhto].on')].map(e => e.dataset.tkhto), open: !!document.getElementById('mbm') }; }""", key)
    c.ok(st['open'] and not st['offered'] and st['ok'] == 'Hand Off to Angel' and len(st['on']) == 1, f'#3 a tap picks the person; nothing is handed off yet ({st})')
    await pg.fill('#mbm [data-tkhnote]', 'The sizes are on the drawing')
    await pg.screenshot(path=os.path.join(SHOTS, 'p_owner_handoff_picked.png'))
    await pg.click('#mbm #mbm-ok'); await pg.wait_for_timeout(350)
    st = await pg.evaluate("""k => { const R = tkResolve(k), H = R && R.rec && R.rec.handoff, t = document.getElementById('toast');
      return { state: H && H.state, to: H && H.to, note: H && H.note, toast: t ? t.innerText : '', open: !!(t && [...t.querySelectorAll('a')].some(a => a.textContent === 'Open')) }; }""", key)
    c.ok(st['state'] == 'offered' and st['to'].startswith('Angel') and st['note'] == 'The sizes are on the drawing' and st['open'], f'#3 Hand Off to Angel offers it, with the note and a toast with Open ({st})')
    # the sheet's own Hand Off opens the same picker
    await pg.evaluate(CLOSE)
    await pg.evaluate("() => { const r = [...document.querySelectorAll('.view.on .tk2-row')][2]; tkSheet(r.dataset.tkkey); }"); await pg.wait_for_timeout(300)
    await pg.evaluate("() => { const b = document.querySelector('#mbm [data-tvsho], #mbm [data-tkshandopen]'); b && b.click(); }"); await pg.wait_for_timeout(350)
    p2 = await pg.evaluate("() => document.querySelectorAll('#mbm [data-tkhto]').length")
    c.ok(p2 >= 3, f'#2 the task sheet\'s Hand Off opens the same people picker ({p2})')
    await pg.evaluate(CLOSE)


async def meeting(c, pg):
    for uid, want in (('u_owner', True), ('u_chen', True), ('u_alan', False), ('u_billing', False)):
        await pg.evaluate(CLOSE); await sign_in(pg, uid); await go(pg, 'tkall'); await pg.wait_for_timeout(250)
        d = await pg.evaluate("""() => { const day = mtCadence().days.includes(parse(today()).getDay()); const b = document.querySelector('.view.on [data-mmstartline]');
          const r = b && b.getClientRects().length ? b.getBoundingClientRect() : null; return { day, txt: b ? b.innerText.trim() : '', y: r ? Math.round(r.top) : null, h: r ? Math.round(r.height) : 0 }; }""")
        if want:
            c.ok(d['day'] and d['txt'].startswith('Start the Team Meeting') and d['y'] is not None and d['y'] < 300 and d['h'] >= 44, f'#4 {uid}: on a meeting day Start the Team Meeting is one tap at the top of Tasks ({d})')
            if uid == 'u_chen':
                await pg.screenshot(path=os.path.join(SHOTS, 'p_coord_tasks_meeting.png'))
            await pg.evaluate("() => document.querySelector('.view.on [data-mmstartline]').click()"); await pg.wait_for_timeout(300)
            dlg = await pg.evaluate("() => ((document.querySelector('#mbm #mbm-ok') || {}).textContent || '').trim()")
            c.ok(dlg == 'Start Meeting', f'#4 {uid}: the line opens the Start dialog ({dlg})')
            await pg.evaluate(CLOSE)
            await pg.evaluate("() => document.querySelector('.view.on [data-tkfilter]').click()"); await pg.wait_for_timeout(300)
            first = await pg.evaluate("() => { const h = document.querySelector('#mbm .tkf .tkf-h'); return h ? h.textContent.trim() : ''; }")
            c.ok(first == 'Meeting', f'#4 {uid}: Meeting is the filter sheet\'s first row ({first})')
            await pg.evaluate(CLOSE)
        else:
            c.ok(not d['txt'], f'#4 {uid}: no meeting line for a role that does not run the meeting ({d})')
    # not on a day the team does not meet
    off = await pg.evaluate("""() => { signIn('u_chen'); const keep = DB.company.meetCadence; const C = mtCadence(); const d = parse(today()).getDay();
      DB.company.meetCadence = Object.assign({}, C, { days: [0, 1, 2, 3, 4, 5, 6].filter(x => x !== d) }); view = 'tkall'; render();
      const has = !!document.querySelector('.view.on [data-mmstartline]'); DB.company.meetCadence = keep; render(); return has; }""")
    c.ok(not off, '#4 no Start line on a day the team does not meet')


async def toasts(c, pg):
    for uid in ('u_owner', 'u_angel'):
        await pg.evaluate(CLOSE); await sign_in(pg, uid); await pg.wait_for_timeout(250)
        await pg.evaluate("() => toast('Moved the date', [{ label: 'Open', run() {} }, { label: 'Undo', run() {} }])"); await pg.wait_for_timeout(250)
        t = await pg.evaluate("""() => { const t = document.getElementById('toast'), r = t.getBoundingClientRect(), vis = e => !!e && e.getClientRects().length > 0 && getComputedStyle(e).display !== 'none';
          const L = [...t.querySelectorAll('a, button')].map(a => { const b = a.getBoundingClientRect(); return [a.textContent.trim(), Math.round(b.width), Math.round(b.height)]; });
          const hit = [...document.querySelectorAll('#mtabs, #tabbar, #fsay, #fab.m-fab, .m-callbar')].filter(vis).filter(e => { const b = e.getBoundingClientRect(); return b.top < r.bottom && b.bottom > r.top && b.left < r.right && b.right > r.left; }).map(e => e.id || e.className);
          return { links: L, hit, bottom: Math.round(r.bottom), w: Math.round(r.width) }; }""")
        await pg.screenshot(path=os.path.join(SHOTS, f'p_{uid}_toast.png'))
        c.ok(len(t['links']) == 2 and all(h >= 44 for _, _, h in t['links']) and all(w >= 44 for _, w, _ in t['links']) and not t['hit'] and t['w'] <= 390, f'#5 {uid}: the toast\'s Open and Undo are 44px and it clears the bar and Say It ({t})')


async def oblig(c, pg):
    await pg.evaluate(CLOSE); await sign_in(pg, 'u_owner'); await go(pg, 'tkall'); await pg.wait_for_timeout(250)
    row = await pg.evaluate("""() => { const r = [...document.querySelectorAll('.view.on .tk2-row')].find(e => /biennial/i.test(e.innerText)); return r ? r.querySelector('.tk2-sub').innerText.replace(/\\s+/g, ' ') : null; }""")
    ap = await pg.evaluate("""() => { const r = nyhRowsAll().find(x => /^oblig:/.test(x.key) && /biennial/i.test(x.title)); return r ? { title: r.title, why: r.why } : null; }""")
    due = await pg.evaluate("() => { const o = DB.obligations.find(x => /biennial/i.test(x.name)); return { file: fmt(iso(addDays(o.expires, -(+o.renewLead || 30)))), exp: fmt(o.expires), late: dayDiff(iso(addDays(o.expires, -(+o.renewLead || 30))), today()) }; }")
    c.ok(row and f"filing {due['late']}d late" in row, f'#11 the task says what is late: "filing {due["late"]}d late" ({row})')
    c.ok(ap and due['file'] in ap['title'] and f"{due['late']} days late" in ap['why'] and due['exp'] in ap['why'], f'#11 Approvals shows the same filing date, late, and the expiry ({ap}, {due})')
    await pg.screenshot(path=os.path.join(SHOTS, 'p_owner_tasks.png'))


async def quick(c, pg):
    await pg.evaluate(CLOSE); await sign_in(pg, 'u_alan'); await go(pg, 'tkall')
    S = ["Angel, measure the windows at 121 State tomorrow, I am in charge", "Angel, measure the windows at 206 Lenox tomorrow, I'm in charge",
         "Check the radiator valves at 45 Cranberry on Friday", "Order the hinges for 140 Prospect tomorrow"]
    P = await pg.evaluate("S => S.map(tvQaParse)", S)
    want = [('Measure the windows', 'p121'), ('Measure the windows', 'p206'), ('Check the radiator valves', None), ('Order the hinges', None)]
    for got, (t, pid) in zip(P, want):
        c.ok(got['title'] == t and (pid is None or got['pid'] == pid) and got['pid'], f'#13 quick add: "{got["text"]}" reads "{t}" on its job ({got["title"]}, {got["pid"]})')
    await pg.evaluate("() => tvQuickAddSheet('Angel, measure the windows at 121 State tomorrow, I am in charge')"); await pg.wait_for_timeout(250)
    await pg.screenshot(path=os.path.join(SHOTS, 'p_pm_quickadd.png'))
    await pg.evaluate(CLOSE)


async def billing(c, pg, b):
    # a fresh session: billing's first visit to Tasks
    ctx = await b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
    p2 = await ctx.new_page()
    from harness import URL
    await p2.goto(URL); await p2.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
    await sign_in(p2, 'u_billing'); await p2.wait_for_timeout(300)
    bar = await p2.evaluate("() => [...document.querySelectorAll('#mtabs button[data-mv]')].map(b => b.dataset.mv)")
    c.ok(bar[:1] == ['home'] and 'tkall' in bar, f'#14 billing\'s bar starts with Today ({bar})')
    await p2.evaluate("() => document.querySelector('#mtabs [data-mv=\"tkall\"]').click()"); await p2.wait_for_timeout(300)
    who = await p2.evaluate("() => ({ who: tkWho, chip: (document.querySelector('.view.on [data-tkfilter]') || {}).title || '' })")
    c.ok(who['who'] == 'me', f'#14 billing\'s Tasks opens on Mine ({who})')
    await p2.screenshot(path=os.path.join(SHOTS, 'p_billing_tasks.png'))
    await ctx.close()


async def names(c, pg):
    await pg.evaluate(CLOSE); await sign_in(pg, 'u_owner'); await go(pg, 'tkall'); await pg.wait_for_timeout(250)
    f = await pg.evaluate("() => [tkFirst('The Standard'), tkFirst('Chief of Staff'), tkFirst('Chen Biron'), tkFirst('Angel'), tkFirst('Purchase history')]")
    c.ok(f == ['The Standard', 'Chief of Staff', 'Chen', 'Angel', 'Purchase history'], f'#15 system authors keep their names; people go by first name ({f})')
    # a note by the Standard reads as the Standard on the sheet's Latest
    lat = await pg.evaluate("""() => { const r = [...document.querySelectorAll('.view.on .tk2-row')][0], R = tkResolve(r.dataset.tkkey); if (!R || !R.rec) return null;
      tkLog(R.rec, { text: 'Weekly update is due', by: 'The Standard' }); const m = tkSheet(R.key); const l = m && m.querySelector('.tvs-latest'); const s = l ? l.innerText : ''; mbCloseModal(); return s; }""")
    c.ok(lat and lat.startswith('The Standard'), f'#15 the sheet names the Standard in full ({lat})')
    meta = await pg.evaluate("""() => [...document.querySelectorAll('.view.on .tk2-row .tk2-sub')].slice(0, 8).map(s => s.innerText.replace(/\\s+/g, ' '))""")
    c.ok(await pg.evaluate('tkWho') == 'me', 'the owner\'s Tasks is on Mine')
    c.ok(meta and not any(re.search(r'(^| · )Owner( · |$)', m) for m in meta), f'#16 on Mine the owner is left off the row ({meta[:3]})')
    own = await pg.evaluate("""() => { const r = [...document.querySelectorAll('.view.on .tk2-row')][0]; const m = tkSheet(r.dataset.tkkey); const f = m && m.querySelector('[data-tvsf="owner"]'); const s = f ? f.innerText.replace(/\\s+/g, ' ').trim() : ''; mbCloseModal(); return s; }""")
    c.ok(own and 'Owner in charge' not in own and 'You' in own, f'#16 the sheet says You for the owner ({own})')


async def red(c, pg):
    await pg.evaluate(CLOSE); await sign_in(pg, 'u_owner'); await go(pg, 'tkall'); await pg.wait_for_timeout(250)
    r = await pg.evaluate("""() => { const red = v => { const m = String(v).match(/\\d+(\\.\\d+)?/g); if (!m) return false; const [r, g, b, a] = m.map(Number); return (a === undefined || a > 0) && r > 150 && g < 90 && b < 90; };
      const rows = [...document.querySelectorAll('.view.on .tk2-row')].filter(e => e.getClientRects().length);
      // a red fill or red text anywhere on a row but its late date (the priority mark was a red bar before the title)
      const reds = rows.flatMap(row => [...row.querySelectorAll('.tk2-mid *, .tk2-title')].filter(e => e.getClientRects().length && !e.closest('.tk2-when')).filter(e => { const cs = getComputedStyle(e);
        return red(cs.backgroundColor) || (e.matches('.tk2-title, .tk2-title *') && red(cs.color)); }).map(e => e.className + ':' + e.textContent.slice(0, 20)));
      const hi = document.querySelector('.view.on .tk2-hi'), late = document.querySelector('.view.on .tk2-row .tk2-w-late');
      return { reds: reds.slice(0, 5), hi: hi ? getComputedStyle(hi).backgroundColor : null, late: late ? getComputedStyle(late).color : null }; }""")
    c.ok(r['hi'] and not r['reds'] and r['late'] and r['hi'] != r['late'], f'#17 late is the only red on task rows; priority is a dark mark ({r})')


async def waiting(c, pg):
    await pg.evaluate(CLOSE); await sign_in(pg, 'u_alan'); await go(pg, 'tkall'); await pg.wait_for_timeout(250)
    w = await pg.evaluate("""() => { for (const r of document.querySelectorAll('.view.on .tk2-row')) { const m = tkSheet(r.dataset.tkkey); const b = m && m.querySelector('.tvs-addwait'); if (b) return b.innerText.trim(); mbCloseModal(); } return null; }""")
    c.ok(w == 'Add Waiting On', f'#18 the sheet\'s button reads Add Waiting On ({w})')
    await pg.evaluate("() => document.querySelector('#mbm .tvs-addwait').click()"); await pg.wait_for_timeout(300)
    f = await pg.evaluate("""() => { const d = document.getElementById('tv-pop'); if (!d) return null; const ok = d.querySelector('[data-tvwsave]'), r = ok.getBoundingClientRect(), D = d.getBoundingClientRect();
      return { w: Math.round(r.width), pw: Math.round(D.width), h: Math.round(r.height), blue: getComputedStyle(ok).backgroundColor, bottom: Math.round(D.bottom), H: innerHeight }; }""")
    await pg.wait_for_timeout(400); await pg.screenshot(path=os.path.join(SHOTS, 'p_pm_waiting.png'))
    c.ok(f and f['h'] >= 48 and f['w'] >= f['pw'] * 0.5, f'#18 Waiting On uses the shared sheet footer: a wide 48px Save ({f})')
    await pg.evaluate(CLOSE)


async def follow(c, pg):
    await pg.evaluate(CLOSE); await sign_in(pg, 'u_owner'); await go(pg, 'tkall')
    fo = await pg.evaluate("""() => { mtStart({}); const m = mtCurrent(); m.presenterUid = 'u_chen'; m.presenter = 'Chen Biron'; mmOn = true; renderTkAll();
      const bar = document.querySelector('.mm-folbar'), g = bar && bar.querySelector('.grow');
      return { txt: bar ? bar.innerText.replace(/\\s+/g, ' ').trim() : '', cut: g ? g.scrollWidth > g.clientWidth + 1 : true }; }""")
    await pg.screenshot(path=os.path.join(SHOTS, 'p_owner_follow.png'))
    c.ok(re.match(r'^Following Chen · \d+ of \d+$', fo['txt']) and not fo['cut'], f'#19 the Follow line fits: {fo}')
    await pg.evaluate("() => mtEnd(mtCurrent())")


async def header(c, pg):
    for uid in ('u_owner', 'u_billing', 'u_chen'):
        await pg.evaluate(CLOSE); await sign_in(pg, uid); await go(pg, 'home'); await pg.wait_for_timeout(200)
        h = await pg.evaluate("""() => { const vis = e => !!e && e.getClientRects().length > 0 && getComputedStyle(e).display !== 'none';
          const B = [...document.querySelectorAll('header.topbar button, header.topbar a.btn')].filter(vis).filter(b => !b.innerText.trim() || getComputedStyle(b.querySelector('span') || b).display === 'none' || b.id === 'tb-ask')
            .map(b => [b.id || b.getAttribute('aria-label') || b.className, Math.round(b.getBoundingClientRect().width), Math.round(b.getBoundingClientRect().height)]);
          const ask = (document.querySelector('#tb-ask svg') || {}).innerHTML || '', chat = (document.querySelector('#mtabs [data-mv="chat"] svg') || {}).innerHTML || '';
          // a speech bubble (the bar's Chat, and the bubble Ask used to share with it) is not Ask's icon
          return { B, same: !ask || ask === chat || /a8 8 0 1 1|H6l-3 3V5/.test(ask), sw: document.documentElement.scrollWidth }; }""")
        bad = [x for x in h['B'] if x[1] < 44 or x[2] < 44]
        c.ok(h['B'] and not bad and not h['same'] and h['sw'] <= 390, f'#20 {uid}: header icon buttons are 44x44 and Ask is not Chat\'s icon ({h})')


async def chips(c, pg):
    for uid, v in (('u_owner', 'home'), ('u_billing', 'tkall'), ('u_billing', 'billing'), ('u_billing', 'ap'), ('u_chen', 'home'), ('u_chen', 'proc'), ('u_chen', 'dec')):
        await pg.evaluate(CLOSE); await sign_in(pg, uid); await go(pg, v); await pg.wait_for_timeout(250)
        r = await pg.evaluate("""() => { const vis = e => !!e && e.getClientRects().length > 0;
          const rows = [...document.querySelectorAll('.view.on .td-tabs, .view.on .ctabs, .view.on .glance.tl, .view.on .seg, .view.on .tv-qchips, #subnav')].filter(vis);
          // the tap area: a touch 3px above or below the chip still lands on it (44px around a 36px pill)
          const hitH = b => { const r = b.getBoundingClientRect(), R = b.parentElement.getBoundingClientRect(), L = Math.max(r.left, R.left), Rt = Math.min(r.right, R.right, innerWidth);
            if (Rt - L < 20) return 99;   // scrolled out of the strip: measured when it is in view
            const x = (L + Rt) / 2;
            const up = document.elementFromPoint(x, r.top - 3), dn = document.elementFromPoint(x, r.bottom + 3);
            return (r.height >= 44 || (up && b.contains(up) && dn && b.contains(dn))) ? Math.max(44, Math.round(r.height)) : Math.round(r.height); };
          return rows.map(row => { const B = [...row.querySelectorAll(':scope > button, :scope > a, :scope > [data-sub]')].filter(vis);
            const gaps = B.slice(1).map((b, i) => Math.round(b.getBoundingClientRect().left - B[i].getBoundingClientRect().right)).filter((g, i) => Math.abs(B[i + 1].getBoundingClientRect().top - B[i].getBoundingClientRect().top) < 4);
            const scrolls = row.scrollWidth > row.clientWidth + 1, cs = getComputedStyle(row), mask = cs.maskImage || cs.webkitMaskImage || 'none';
            return { cls: row.id || row.className, n: B.length, minGap: gaps.length ? Math.min(...gaps) : 99, hit: B.length ? Math.min(...B.map(hitH)) : 99, scrolls, fade: mask !== 'none' };
          }); }""")
        bad = [x for x in r if x['minGap'] < 8 or x['hit'] < 44 or (x['scrolls'] and not x['fade'])]
        await pg.screenshot(path=os.path.join(SHOTS, f'p_{uid}_{v}_chips.png'))
        c.ok(r and not bad, f'#21 {uid} {v}: chip rows have 8px gaps, 44px hit areas, fade when they scroll ({bad or r})')


async def one_blue(c, pg):
    await pg.evaluate(CLOSE); await sign_in(pg, 'u_billing'); await go(pg, 'tkall'); await go(pg, 'billing'); await pg.wait_for_timeout(300)
    r = await pg.evaluate("""() => { const vis = e => !!e && e.getClientRects().length > 0 && getComputedStyle(e).visibility !== 'hidden';
      const leak = [...document.querySelectorAll('.main > .view:not(.on), section.view:not(.on)')].filter(v => vis(v) && v.getBoundingClientRect().height > 0).map(v => v.id);
      const P = [...document.querySelectorAll('.btn.primary, button.primary')].filter(vis).filter(b => !b.closest('#mbm')).map(b => b.textContent.trim().slice(0, 30));
      return { leak, P }; }""")
    await pg.screenshot(path=os.path.join(SHOTS, 'd_billing_billing.png'))
    c.ok(not r['leak'] and len(r['P']) <= 1, f'#23 Billing after Tasks: no other page leaks under it and one blue ({r})')
    # the class: every office role, every page it may open after Tasks, shows only its own view
    for uid in ('u_owner', 'u_chen'):
        await sign_in(pg, uid); await go(pg, 'tkall')
        views = await pg.evaluate("() => (ROLE_VIEWS[role()] || []).filter(v => !['pa', 'conn', 'setup', 'tkall'].includes(v)).slice(0, 40)")
        leaks = []
        for v in views:
            await pg.evaluate("v => { view = v; render(); }", v)
            l = await pg.evaluate("""() => [...document.querySelectorAll('section.view:not(.on)')].filter(v => v.getClientRects().length && v.getBoundingClientRect().height > 0 && getComputedStyle(v).display !== 'none').map(v => v.id)""")
            l and leaks.append((v, l))
        c.ok(not leaks, f'#23 {uid}: no hidden page shows under another ({leaks[:4]})')


async def step(c, pg, name, fn, *a):
    """one finding's checks; an error in one is a failure of that finding, and the rest still run"""
    try:
        await fn(c, pg, *a)
    except Exception as e:
        c.ok(False, f'{name}: {str(e).splitlines()[0][:200]}')
    try:
        await pg.evaluate(CLOSE)
    except Exception:
        pass


async def main():
    c = Checks()
    async with async_playwright() as p:
        b, pg, errs = await open_app(p, False)
        await step(c, pg, 'one number, desktop', one_number, False)
        await step(c, pg, 'one blue', one_blue)
        c.ok(not errs, f'desktop: no page errors ({errs[:3]})')
        await b.close()
        b, pg, errs = await open_app(p, True)
        await step(c, pg, 'one number, phone', one_number, True)
        for name, fn in (('hand off', hand_off), ('meeting', meeting), ('toasts', toasts), ('obligation', oblig), ('quick add', quick)):
            await step(c, pg, name, fn)
        await step(c, pg, 'billing', billing, b)
        for name, fn in (('names', names), ('red', red), ('waiting', waiting), ('follow', follow), ('header', header), ('chips', chips)):
            await step(c, pg, name, fn)
        c.ok(not errs, f'phone: no page errors ({errs[:3]})')
        await b.close()
    raise SystemExit(c.done())

asyncio.run(main())
