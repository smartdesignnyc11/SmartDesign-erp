"""labour_rules: the two labour rules the owner decided on 11-15 ("Yes to both"), BACKLOG section 12, as the people who
live them, through the screens.

  logged   Rule 1. Hours logged, not clocked. Only clocked, approved time is job cost and payroll. The demo's 206 Lenox
           has 46.5 hours on its daily logs and none clocked: its cost reads $0. The controller's Budget says so; the
           job's PM has ONE flag on Today's Caught for You ("46.5 hours logged, not clocked"), and its sheet has one
           row per person, day and log (the flag's hours are its rows' hours). Approve as Time makes one time entry
           carrying who, when and why; it is cost and pays through the run; Dismiss records who and why and the row
           does not come back. A foreman's log for a crew of four is four rows, each its own approval. A log edited
           after approval makes no second entry and does not double the hours: the change is a row of its own, and
           approving it changes the one entry. Salaried office staff (a coordinator on a log) never raise it.
  offline  Rule 2. Hours on a cost code with no estimate line. Clock-in on the phone offers the job's estimate and
           approved change-order lines, most likely first, a short list, with Other (which asks for a note), in
           Spanish for a Spanish-speaking crew. The demo's 121 State has 37.92 crew hours on cost code 12 ($1,466.05)
           that no line carries: the PM has a proposal, Move to a Line (the likely line, Trim, doors, paint &
           hardware) or Draft a Change Order. Nothing moves by itself. Moving through the sheet records who, when,
           from and to on each entry, keeps every amount, and puts the job's estimate at completion back to
           388,887.50 on every screen that prints it; a move of an entry in a closed month posts in the open period
           and the closed month reads exactly as before.

Invented demo data only (a crew-of-four log, an office person on a log, an August entry in a closed month).
Run: python3 labour_rules_test.py [logged|offline]"""
import asyncio, os, re, sys
from harness import async_playwright, open_app, sign_in, go, Checks, ROOT

SHOTS = os.path.join(ROOT, 'review', 'labour_rules')
os.makedirs(SHOTS, exist_ok=True)
CLOSE = "() => { try { mbCloseModal(); } catch (e) {} document.querySelectorAll('#mbm').forEach(e => e.remove()); }"
TOAST = "() => (document.getElementById('toast') || {}).innerText || ''"
MBM = "() => (document.querySelector('#mbm') || {}).innerText || ''"


async def shot(pg, name):
    try:
        await pg.screenshot(path=os.path.join(SHOTS, name + '.png'))
    except Exception:
        pass


async def tap(pg, sel, text=None, phone=False):
    """a real click (or tap on the phone) on the first visible element matching sel and holding text"""
    h = await pg.evaluate_handle("([s, t]) => [...document.querySelectorAll(s)].find(e => e.getClientRects().length && (!t || (e.innerText || e.value || '').includes(t))) || null", [sel, text])
    el = h.as_element()
    if not el: return False
    await el.scroll_into_view_if_needed()
    await (el.tap() if phone else el.click())
    await pg.wait_for_timeout(350)
    return True


async def caught_open(pg, src):
    """Today's Caught for You, as the person sees it: open the fold, show every row, press the row's verb"""
    await go(pg, 'home')
    await pg.wait_for_timeout(300)
    if not await pg.evaluate("() => !!document.querySelector('.td-catch')"):
        await tap(pg, '[data-td2quiet]')
    if await pg.evaluate("() => !!document.querySelector('[data-tdcatchall]') && !/Fewer/.test(document.querySelector('[data-tdcatchall]').innerText)"):
        await tap(pg, '[data-tdcatchall]')
    card = await pg.evaluate("s => { const c = [...document.querySelectorAll('.td-c')].find(x => x.dataset.src === s); return c ? c.innerText.replace(/\\s+/g, ' ').trim() : ''; }", src)
    ok = card and await tap(pg, f'.td-c[data-src="{src}"] [data-tdcatch]')
    await pg.wait_for_timeout(300)
    return card, ok


LENOX_COST = "() => { const p = DB.projects.find(x => x.id === 'p206'), J = jobFin(p); return { actual: J.actual, labor: J.labor != null ? J.labor : null, hours: J.hours != null ? J.hours : null }; }"


async def s_logged(pg, c, phone_pg):
    # ---- the controller: 206 Lenox's cost is $0 and the Budget says why
    await sign_in(pg, 'u_controller')
    r = await pg.evaluate(LENOX_COST)
    c.ok(abs(r['actual']) < 0.005, f"logged: 206 Lenox's cost to date is $0 before anyone decides ({r})")
    await pg.evaluate("() => { setCurrent('p206'); view = 'costs'; render(); }")
    await pg.wait_for_timeout(400)
    say = await pg.evaluate("() => { const n = document.querySelector('#v-costs .lab-lognc'); return n ? n.innerText.replace(/\\s+/g, ' ') : ''; }")
    await shot(pg, 'controller_lenox_budget')
    c.ok('46.5 hours logged, not clocked' in say and 'not in cost' in say, f"logged: the controller's Budget for 206 Lenox says 46.5 hours are logged, not clocked, and not in cost ({say[:160]!r})")

    # ---- invented: a crew of four on one log, and the coordinator (salaried office) on another
    await pg.evaluate("""() => { DB.field.logs.push({ id: 'lab_t4', projectId: 'p206', date: '2026-09-03', status: 'submitted', by: 'Angel', signedBy: 'Angel',
        crew: [{ name: 'Angel', empId: 'em1', trade: 'Site lead', hours: 8 }, { name: 'Alberto', empId: 'em2', trade: 'Framing', hours: 8 }, { name: 'Alex', empId: 'em3', trade: 'Helper', hours: 6 }, { name: 'Satish', empId: 'em4', trade: 'Electrician', hours: 4 }],
        subs: [], work: [], delays: [], photoIds: [], photos: [] });
      DB.field.logs.push({ id: 'lab_off', projectId: 'p206', date: '2026-09-02', status: 'submitted', by: 'Chen Biron', signedBy: 'Chen Biron',
        crew: [{ name: 'Chen Biron', empId: 'em5', trade: 'Coordinator', hours: 4 }], subs: [], work: [], delays: [], photoIds: [], photos: [] }); save(); }""")
    # 46.5 seeded + the crew of four's 26 = 72.5; the coordinator's 4 h never count
    want = 72.5

    # ---- the PM: one flag on Today's Caught for You, its sheet one row per person, day and log
    await sign_in(pg, 'u_alan')
    card, ok = await caught_open(pg, 'loggedNotClocked')
    await shot(pg, 'pm_caught')
    lenox = await pg.evaluate("() => [...document.querySelectorAll('.td-c')].filter(x => x.dataset.src === 'loggedNotClocked').map(x => x.innerText.replace(/\\s+/g, ' '))")
    c.ok(any(f'{want:g} hours logged, not clocked' in x and '206 Lenox' in x for x in lenox), f"logged: the PM's Caught for You has one flag for 206 Lenox, {want:g} hours logged, not clocked ({lenox})")
    c.ok(len([x for x in lenox if '206 Lenox' in x]) == 1, f"logged: one flag per job, not one per row ({len(lenox)})")
    r = await pg.evaluate("""() => { const m = document.getElementById('mbm'); if (!m) return null;
      const R = [...m.querySelectorAll('[data-labrow]')].map(x => ({ key: x.dataset.labrow, h: +x.dataset.h, t: x.innerText.replace(/\\s+/g, ' '), ok: !!x.querySelector('[data-labok]'), no: !!x.querySelector('[data-labno]') }));
      return { R, text: m.innerText, blue: m.querySelectorAll('.btn.primary').length }; }""")
    await shot(pg, 'pm_sheet')
    c.ok(bool(r), 'logged: the flag opens its sheet')
    if r:
        tot = round(sum(x['h'] for x in r['R']), 2)
        c.ok(abs(tot - want) < 0.01, f"logged: the flag's hours are its rows' hours ({tot} vs {want})")
        c.ok(all(x['ok'] and x['no'] for x in r['R']), "logged: every row has Approve as Time and Dismiss")
        four = [x for x in r['R'] if x['key'].startswith('lab_t4:')]
        c.ok(len(four) == 4 and all(any(n in x['t'] for n in ('Angel', 'Alberto', 'Alex', 'Satish')) for x in four), f"logged: a log for a crew of four is four rows, one approval each ({[x['t'][:40] for x in four]})")
        c.ok(not any(x['key'].startswith('lab_off:') for x in r['R']) and 'Chen' not in r['text'], 'logged: the salaried coordinator on a log raises nothing')
        a = next((x for x in r['R'] if x['key'] == 'fls20620260831:em2'), None)
        c.ok(bool(a) and 'Alberto' in a['t'] and '8 h' in a['t'] and ('Aug 31' in a['t'] or '8/31' in a['t']) and 'log' in a['t'].lower(), f"logged: a row names the person, the hours, the day and the log ({a})")
        c.ok(r['blue'] <= 1, f"logged: one blue button on the sheet at most ({r['blue']})")

    # ---- Approve as Time: one entry with who, when and why; job cost moves by exactly its hours
    cost0 = (await pg.evaluate(LENOX_COST))['actual']
    n0 = await pg.evaluate("() => DB.time.length")
    await tap(pg, '#mbm [data-labrow="fls20620260831:em2"] [data-labok]')
    m = await pg.evaluate(MBM)
    c.ok('Approve as Time' in m, f"logged: Approve as Time asks why before it commits ({m[:120]!r})")
    await pg.evaluate("() => { const i = document.querySelector('#mbm [data-f=\"why\"]'); i && (i.value = 'Alberto worked the day; the phone was dead'); }")
    await tap(pg, '#mbm #mbm-ok')
    await pg.wait_for_timeout(300)
    t = await pg.evaluate(TOAST)
    r = await pg.evaluate("""() => { const T = DB.time.filter(e => e.fromLog && e.fromLog.logId === 'fls20620260831' && e.empId === 'em2');
      return { n: T.length, e: T[0] ? { status: T[0].status, by: T[0].approvedBy, at: T[0].approvedAt || '', why: T[0].approveWhy || '', h: hoursOf(T[0]), pid: T[0].projectId, date: T[0].date } : null,
        rate: laborRate(DB.employees.find(x => x.id === 'em2')) }; }""")
    cost1 = (await pg.evaluate(LENOX_COST))['actual']
    e = r['e'] or {}
    c.ok(r['n'] == 1 and e.get('status') == 'approved' and e.get('by') == 'Alan' and e.get('at', '').startswith('2026-09-03') and 'dead' in e.get('why', '') and e.get('h') == 8 and e.get('date') == '2026-08-31', f"logged: Approve as Time makes one approved time entry with who, when (the app's clock) and why ({r})")
    c.ok(abs((cost1 - cost0) - 8 * r['rate']) < 0.02, f"logged: the job's cost moves by those 8 hours at the burdened rate, and only then ({cost0} -> {cost1}, rate {r['rate']})")
    c.ok('Open' in t and 'Alberto' in t, f"logged: the toast says what happened, with Open ({t[:120]!r})")

    # ---- Dismiss: who and why, and the row does not come back
    card, ok = await caught_open(pg, 'loggedNotClocked')
    c.ok(f'{want - 8:g} hours logged, not clocked' in card, f"logged: the flag drops to {want - 8:g} hours ({card[:100]!r})")
    await tap(pg, '#mbm [data-labrow="fls20620260831:em3"] [data-labno]')
    await tap(pg, '#mbm #mbm-ok')
    still = await pg.evaluate("() => !!document.querySelector('#mbm [data-f=\"why\"]')")
    c.ok(still, 'logged: Dismiss will not go through without a reason')
    await pg.evaluate("() => { const i = document.querySelector('#mbm [data-f=\"why\"]'); i && (i.value = 'Alex was at the yard, not on site'); }")
    await tap(pg, '#mbm #mbm-ok')
    r = await pg.evaluate("""() => { const l = DB.field.logs.find(x => x.id === 'fls20620260831'), D = (l.timeDecisions || {}).em3 || {};
      return { D, rows: labUnclocked('p206').filter(x => x.l.id === l.id && x.cw.empId === 'em3').length, entries: DB.time.filter(e => e.fromLog && e.fromLog.logId === l.id && e.empId === 'em3').length }; }""")
    c.ok(r['D'].get('kind') == 'dismissed' and r['D'].get('by') == 'Alan' and 'yard' in r['D'].get('why', '') and r['rows'] == 0 and r['entries'] == 0, f"logged: Dismiss records who and why, costs nothing and the row does not come back ({r})")

    # ---- the foreman edits the approved log: no second entry, no doubled hours
    await pg.evaluate("() => { const l = DB.field.logs.find(x => x.id === 'fls20620260831'); l.crew.find(c => c.empId === 'em2').hours = 9; save(); render(); }")
    r = await pg.evaluate("""() => ({ entries: DB.time.filter(e => e.fromLog && e.fromLog.logId === 'fls20620260831' && e.empId === 'em2').length,
      h: DB.time.filter(e => e.projectId === 'p206' && e.empId === 'em2' && e.date === '2026-08-31').reduce((a, e) => a + hoursOf(e), 0),
      row: labUnclocked('p206').filter(x => x.l.id === 'fls20620260831' && x.cw.empId === 'em2').map(x => ({ kind: x.kind, h: x.hours })) })""")
    c.ok(r['entries'] == 1 and r['h'] == 8 and r['row'] == [{'kind': 'changed', 'h': 1}], f"logged: a log edited after approval makes no second entry and does not double the hours; the hour it added is a row to decide ({r})")
    await caught_open(pg, 'loggedNotClocked')
    t = await pg.evaluate("() => { const x = document.querySelector('#mbm [data-labrow=\"fls20620260831:em2\"]'); return x ? x.innerText.replace(/\\s+/g, ' ') : ''; }")
    c.ok('changed' in t.lower() and '8 h' in t and '9 h' in t, f"logged: the row says the log changed after approval, 8 h approved and 9 h now ({t[:140]!r})")
    await tap(pg, '#mbm [data-labrow="fls20620260831:em2"] [data-labok]')
    await tap(pg, '#mbm #mbm-ok')
    r = await pg.evaluate("""() => ({ entries: DB.time.filter(e => e.fromLog && e.fromLog.logId === 'fls20620260831' && e.empId === 'em2').map(e => hoursOf(e)),
      rows: labUnclocked('p206').filter(x => x.l.id === 'fls20620260831' && x.cw.empId === 'em2').length })""")
    c.ok(r['entries'] == [9] and r['rows'] == 0, f"logged: approving the change moves the one entry to 9 h ({r})")

    # ---- payroll follows the approved entry, never the log
    r = await pg.evaluate("""() => { const run = payrollFromTime({ quiet: true }); if (!run) return { run: null };
      const inRun = DB.time.filter(e => e.payrollId === run.id), logged = inRun.filter(e => e.fromLog);
      const unapproved = inRun.filter(e => e.status !== 'approved' && !/paid|locked/.test(e.status || ''));
      return { run: run.id, n: inRun.length, logged: logged.map(e => e.empId + ':' + hoursOf(e)), unapproved: unapproved.length,
        dismissed: inRun.filter(e => e.fromLog && e.empId === 'em3' && e.fromLog.logId === 'fls20620260831').length }; }""")
    c.ok(r.get('run') and r['unapproved'] == 0 and r['dismissed'] == 0, f"logged: the pay run holds approved entries only, the dismissed hours nowhere ({r})")

    # ---- the four of the crew's log: each its own approval
    await caught_open(pg, 'loggedNotClocked')
    await tap(pg, '#mbm [data-labrow="lab_t4:em4"] [data-labok]')
    await tap(pg, '#mbm #mbm-ok')
    r = await pg.evaluate("() => ({ made: DB.time.filter(e => e.fromLog && e.fromLog.logId === 'lab_t4').map(e => e.empId), left: labUnclocked('p206').filter(x => x.l.id === 'lab_t4').map(x => x.cw.empId) })")
    c.ok(r['made'] == ['em4'] and sorted(r['left']) == ['em1', 'em2', 'em3'], f"logged: approving Satish approves Satish only; the other three still wait ({r})")
    await pg.evaluate(CLOSE)


EAC = "() => { const p = DB.projects.find(x => x.id === 'p121'), J = jobFin(p); return J.eac; }"


async def s_offline(pg, c, phone_pg):
    # ---- the crew on the phone: Clock In offers the job's lines, most likely first, with Other
    ph = phone_pg
    await sign_in(ph, 'u_alberto'); await go(ph, 'time')
    await ph.evaluate("() => { window.getGeo = async () => null; const e = myEmp(); DB.time = DB.time.filter(t => !(t.empId === e.id && t.date === today())); save(); render(); }")
    await tap(ph, '#clock-in', phone=True)
    await ph.wait_for_timeout(500)
    r = await ph.evaluate("""() => { const box = document.querySelector('.view.on .lab-pick'); const e = DB.time.find(t => t.empId === myEmp().id && !t.out);
      const chips = box ? [...box.querySelectorAll('[data-labline]')].filter(b => b.getClientRects().length) : [];
      const keys = new Set(); try { const p = DB.projects.find(x => x.id === e.projectId); jobFinEacLines(jobFin(p), p).forEach(x => keys.add(x.key)); } catch (x) {}
      const R = chips.map(b => b.getBoundingClientRect());
      let gap = 99; for (let i = 0; i < R.length; i++) for (let j = i + 1; j < R.length; j++) { const a = R[i], b = R[j];
        const dx = Math.max(0, Math.max(a.left, b.left) - Math.min(a.right, b.right)), dy = Math.max(0, Math.max(a.top, b.top) - Math.min(a.bottom, b.bottom)); gap = Math.min(gap, Math.max(dx, dy)); }
      return { open: !!e, box: !!box, head: box ? box.innerText.split('\\n')[0] : '', n: chips.length, onJob: chips.every(b => keys.has(b.dataset.labline)), h: Math.min(...R.map(x => x.height), 99), gap,
        other: !!(box && box.querySelector('[data-labother]')), side: document.documentElement.scrollWidth - innerWidth }; }""")
    await shot(ph, 'crew_clockin_lines')
    c.ok(r['open'] and r['box'], f"offline: after Clock In the crew's Clock page asks which line ({r})")
    c.ok(1 <= r['n'] <= 4 and r['onJob'], f"offline: a short list, the job's estimate and change-order lines only ({r['n']}, on the job {r['onJob']})")
    c.ok(r['other'], 'offline: Other stays on the list')
    c.ok(r['h'] >= 44 and r['gap'] >= 8 and r['side'] <= 0, f"offline: one-handed: 44px targets, 8px apart, no sideways scroll ({r['h']}, {r['gap']}, {r['side']})")
    first = await ph.evaluate("() => { const b = document.querySelector('.view.on .lab-pick [data-labline]'); return b ? { key: b.dataset.labline, name: b.innerText.trim() } : null; }")
    await tap(ph, '.view.on .lab-pick [data-labline]', phone=True)
    r = await ph.evaluate("() => { const e = DB.time.find(t => t.empId === myEmp().id && !t.out); return { line: e.line || '', code: e.code || '', pick: e.linePick || null, toast: (document.getElementById('toast') || {}).innerText || '', box: ((document.querySelector('.view.on .lab-pick') || {}).innerText || '') }; }")
    c.ok(first and r['line'] == first['key'] and r['code'] and r['pick'] and r['pick'].get('at', '').startswith('2026-09-03'), f"offline: a tap puts the punch on that line and its cost code, stamped on the app's clock ({r})")
    c.ok('Change' in r['box'], f"offline: the page then says the line, with Change ({r['box'][:80]!r})")
    # Other asks for a note
    await tap(ph, '.view.on .lab-pick [data-labchange]', phone=True)
    await tap(ph, '.view.on .lab-pick [data-labother]', phone=True)
    m = await ph.evaluate(MBM)
    await tap(ph, '#mbm #mbm-ok', phone=True)
    held = await ph.evaluate("() => !!document.getElementById('mbm')")
    await ph.evaluate("() => { const i = document.querySelector('#mbm [data-f=\"note\"]'); i && (i.value = 'Moving the dumpster for the city'); }")
    await tap(ph, '#mbm #mbm-ok', phone=True)
    r = await ph.evaluate("() => { const e = DB.time.find(t => t.empId === myEmp().id && !t.out); return { other: e.lineOther || '', line: e.line || '' }; }")
    c.ok('note' in m.lower() or 'what' in m.lower(), f"offline: Other asks for a short note ({m[:80]!r})")
    c.ok(held and 'dumpster' in r['other'] and not r['line'], f"offline: Other needs its note, and keeps the punch off a line ({r}, held {held})")
    # in Spanish for a Spanish-speaking crew
    await ph.evaluate("() => { currentUser().lang = 'es'; const e = DB.time.find(t => t.empId === myEmp().id && !t.out); delete e.lineOther; e.code = ''; save(); render(); }")
    await ph.wait_for_timeout(300)
    es = await ph.evaluate("() => ((document.querySelector('.view.on .lab-pick') || {}).innerText || '')")
    await shot(ph, 'crew_clockin_lines_es')
    c.ok(es and 'What Are You Working On' not in es and 'Other' not in es and 'More Lines' not in es, f"offline: the line picker reads in Spanish ({es[:120]!r})")
    await ph.evaluate("() => { currentUser().lang = 'en'; const e = DB.time.find(t => t.empId === myEmp().id && !t.out); DB.time = DB.time.filter(t => t !== e); save(); render(); }")

    # ---- the PM: the proposal for 121 State's cost on code 12
    await sign_in(pg, 'u_alan')
    eac0 = await pg.evaluate(EAC)
    c.ok(abs(eac0 - 390353.55) < 0.005, f"offline: 121 State's estimate at completion is 390,353.55 with the code-12 hours off a line ({eac0})")
    T0 = await pg.evaluate("() => DB.time.filter(t => t.projectId === 'p121' && t.code === '12').map(t => ({ id: t.id, h: hoursOf(t), st: t.status }))")
    card, ok = await caught_open(pg, 'offLine')
    await shot(pg, 'pm_offline_sheet')
    m = await pg.evaluate(MBM)
    c.ok('121 State' in card and '1,466.05' in card, f"offline: the PM's Caught for You proposes the move for 121 State's $1,466.05 off a line ({card[:140]!r})")
    c.ok('37.92' in m and 'Trim, doors, paint & hardware' in m and 'Move to a Line' in m and 'Draft a Change Order' in m, f"offline: the sheet shows the 37.92 hours, offers the likely line, Move to a Line and Draft a Change Order ({m[:240]!r})")
    sel = await pg.evaluate("() => { const s = document.querySelector('#mbm [data-f=\"line\"]'); return s ? s.options[s.selectedIndex].text : ''; }")
    c.ok(sel.startswith('Trim, doors, paint & hardware'), f"offline: the likely line is the one picked ({sel!r})")
    same = await pg.evaluate("() => DB.time.filter(t => t.projectId === 'p121' && t.code === '12').length")
    c.ok(same == len(T0) == 5, f"offline: nothing moved by itself ({same} of {len(T0)})")
    await tap(pg, '#mbm #mbm-ok')
    await pg.wait_for_timeout(300)
    t = await pg.evaluate(TOAST)
    r = await pg.evaluate("""ids => { const T = DB.time.filter(t => ids.includes(t.id));
      return { codes: [...new Set(T.map(t => t.code))], lines: [...new Set(T.map(t => t.line || ''))], h: T.map(t => hoursOf(t)), st: T.map(t => t.status),
        moves: T.map(t => (t.moves || []).slice(-1)[0] || null) }; }""", [x['id'] for x in T0])
    eac1 = await pg.evaluate(EAC)
    mv = [x for x in r['moves'] if x]
    c.ok(r['codes'] == ['11'] and r['lines'] == ['estimate:es1:l10'], f"offline: Move to a Line puts the five entries on the line and its code ({r['codes']}, {r['lines']})")
    c.ok(r['h'] == [x['h'] for x in T0] and r['st'] == [x['st'] for x in T0], f"offline: every entry keeps its hours and status ({r['h']})")
    c.ok(len(mv) == 5 and all(x.get('by') == 'Alan' and x.get('from') == '12' and x.get('to') == '11' and x.get('at', '').startswith('2026-09-03') for x in mv), f"offline: the move is recorded on each entry: who, when, from and to ({mv[:1]})")
    c.ok(abs(eac1 - 388887.50) < 0.005, f"offline: 121 State's estimate at completion is back to 388,887.50 ({eac0} -> {eac1}; 390,353.55 - 1,466.05)")
    c.ok('Open' in t and 'Trim' in t, f"offline: the toast says what moved, with Open ({t[:140]!r})")
    # one EAC on every screen that prints it: the job's Budget, the job header tile, Projects, Ask
    await pg.evaluate("() => { setCurrent('p121'); view = 'costs'; render(); }")
    await pg.wait_for_timeout(400)
    r = await pg.evaluate("""() => { const v = document.getElementById('jp-eac'); const nl = [...document.querySelectorAll('#jp-btable [data-jpline="__noline"]')].length;
      return { budget: v ? v.innerText.trim() : '', noline: nl }; }""")
    await shot(pg, 'pm_budget_after_move')
    c.ok(r['budget'] == '$388,888' or r['budget'] == '$388,887.50', f"offline: the Budget's estimate at completion reads the same figure ({r['budget']!r})")
    c.ok(r['noline'] == 0, f"offline: the Budget's Not on an Estimate Line row is gone ({r['noline']})")
    card2 = await pg.evaluate("() => tdCaught([]).filter(x => x.src === 'offLine' && /121 State/.test(x.what)).length")
    c.ok(card2 == 0, f"offline: the proposal is gone once the cost is on its line ({card2})")

    # ---- invented: an August entry in a closed month moves in the open period; August reads exactly as before
    await pg.evaluate("""() => { DB.periods.lockedThrough = '2026-08';
      DB.time.push({ id: 'lab_aug', empId: 'em2', date: '2026-08-20', in: '2026-08-20T07:30:00', out: '2026-08-20T11:30:00', breakMin: 0, projectId: 'p121', code: '12', notes: '', status: 'approved', approvedBy: 'Alan', source: 'manual', work: [{ projectId: 'p121', code: '12', hours: 4, note: '' }] }); save(); }""")
    AUG = """() => { const p = DB.projects.find(x => x.id === 'p121'), J = jobFin(p, ['2026-08-01', '2026-08-31']);
      return { actual: J.actual, codes: (J.byCode || []).map(r => [r.code, Math.round(100 * (+r.actual || 0)) / 100]).filter(x => x[1]).sort() }; }"""
    aug0 = await pg.evaluate(AUG)
    eacA = await pg.evaluate(EAC)
    card, ok = await caught_open(pg, 'offLine')
    m = await pg.evaluate(MBM)
    c.ok(ok and '4' in m, f"offline: the August entry on code 12 raises the proposal ({card[:100]!r})")
    await tap(pg, '#mbm #mbm-ok')
    aug1 = await pg.evaluate(AUG)
    r = await pg.evaluate("() => { const t = DB.time.find(x => x.id === 'lab_aug'); return { code: t.code, mv: (t.moves || [])[0] || null }; }")
    eacB = await pg.evaluate(EAC)
    c.ok(aug1 == aug0, f"offline: closed August's figures are identical before and after the move ({aug0} -> {aug1})")
    c.ok(r['code'] == '11' and r['mv'] and r['mv'].get('postOn') == '2026-09-03', f"offline: the move of a closed-month entry posts in the open period ({r})")
    c.ok(abs(eacB - eacA) > 0.005 and abs(eacB - 388887.50) < 0.005, f"offline: and the job's estimate at completion today takes it ({eacA} -> {eacB})")

    # ---- Draft a Change Order: the other answer, and still nothing moves by itself
    await pg.evaluate("""() => { DB.periods.lockedThrough = '';
      DB.time.push({ id: 'lab_co', empId: 'em3', date: '2026-09-02', in: '2026-09-02T16:00:00', out: '2026-09-02T18:00:00', breakMin: 0, projectId: 'p121', code: '13', notes: '', status: 'approved', approvedBy: 'Alan', source: 'manual', work: [{ projectId: 'p121', code: '13', hours: 2, note: '' }] }); save(); }""")
    card, ok = await caught_open(pg, 'offLine')
    n0 = await pg.evaluate("() => DB.clients.find(c => c.id === DB.projects.find(p => p.id === 'p121').clientId).changeOrders.length")
    await tap(pg, '#mbm #mbm-alt')
    r = await pg.evaluate("""n0 => { const c = DB.clients.find(c => c.id === DB.projects.find(p => p.id === 'p121').clientId), d = c.changeOrders[c.changeOrders.length - 1];
      const t = DB.time.find(x => x.id === 'lab_co');
      return { made: c.changeOrders.length - n0, status: d && d.status, lines: d ? d.lines.map(l => ({ code: l.code, qty: l.qty, unit: l.unit })) : [], code: t.code, toast: (document.getElementById('toast') || {}).innerText || '' }; }""", n0)
    c.ok(r['made'] == 1 and r['status'] == 'draft' and r['lines'] and r['lines'][0]['code'] == '13' and r['lines'][0]['qty'] == 2, f"offline: Draft a Change Order drafts one, for the 2 hours on code 13 ({r})")
    c.ok(r['code'] == '13', f"offline: and the entry stays where it was until the change order is approved ({r['code']})")
    await pg.evaluate(CLOSE)


SECTIONS = {'logged': s_logged, 'offline': s_offline}


async def main():
    c = Checks()
    want = [a for a in sys.argv[1:] if a in SECTIONS] or list(SECTIONS)
    async with async_playwright() as p:
        for name in want:
            b, pg, errs = await open_app(p)
            b2, ph, errs2 = await open_app(p, phone=True)
            try:
                await SECTIONS[name](pg, c, ph)
            except Exception as e:
                c.ok(False, f'{name}: stopped: {str(e)[:300]}')
            c.ok(not errs and not errs2, f'{name}: no page errors ({(errs + errs2)[:2]})')
            await b.close(); await b2.close()
    return c.done()

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
