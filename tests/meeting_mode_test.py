"""The task record and Meeting Mode (docs/TASKS_PLAN.md Phase 1, items 3 and 4; Alan, 2026-10-23).

The team walks the board twice a week, project by project, one task at a time, by keys like PAD-23. This suite
runs the meeting the way the coordinator runs it on the screen share (desktop) and the way the owner runs it on the
phone (390px), with every one-tap action, and checks the record each action leaves:
  - keys: every board task has one, unique, shown on its row and in its sheet, found by Tasks search, Cmd-K, Ask and
    erpQuery; a number is never given twice (deleted, duplicated after a merge, prefix renamed);
  - the owner: a vendor, consultant or client is never the owner; the boot migration makes them Waiting On, gives the
    task to the job's lead (or its maker) and flags it to confirm; the creation path and the board editor refuse it;
  - the meeting: the agenda builds itself; New Date, Note, Done, Reassign, Waiting On, Track Until, FYI, Skip,
    Decision, Move Up and Move Down, a task added inline, a project added inline with its prefix; the screen log
    (which task was on screen from when to when) and the changes (who changed what, from and to) are right;
  - End Meeting writes the minutes (moved, new, done, decisions aligned and to discuss, who owes what by when) onto
    the meeting's record and puts one line on each person's Today, which opens them;
  - Follow: a second screen shows the presenter's card.
Invented data only (CLAUDE.md, Privacy)."""
import asyncio, re
from harness import async_playwright, open_app, sign_in, go, Checks

CODE = re.compile(r'^[A-Z][A-Z0-9]{0,7}-\d{1,5}$')

# invented tasks for the meeting: a late money task, one due before the next meeting, one waiting on a vendor, one FYI,
# one quiet (only on the agenda when the whole board is walked), on two jobs and the firm's own list
SEED = r"""
() => {
  const P = DB.projects.find(p => p.id === 'p206') || DB.projects[0], Q = DB.projects.find(p => p.id === 'p121') || DB.projects[1];
  const td = today(), d = (n) => iso(addDays(td, n));
  const mk = (p, f) => { const a = Object.assign({ id: uid('a'), status: 'todo', priority: 'med', link: null, notes: '', source: null, createdAt: d(-10), completedAt: '', createdBy: 'Chen Biron' }, f); (p.actions = p.actions || []).push(a); return a; };
  const made = {
    late:  mk(P, { title: 'Release the deposit to the stone fabricator', assignee: 'Owner', due: d(-2) }),
    soon:  mk(P, { title: 'Get the credit for the wrong tile delivery', assignee: 'Chen Biron', due: d(1) }),
    wait:  mk(Q, { title: 'Dining boxes from the millworker', assignee: 'Alan', due: d(6), waitsOn: 'Invented Millwork Co', escalateOn: d(3) }),
    fyi:   mk(Q, { title: 'Permit sign-off posted at the site', assignee: 'Alan', due: '', status: 'fyi' }),
    quiet: mk(Q, { title: 'Order the spare hinges', assignee: 'Chen Biron', due: d(30) }),
    outside: mk(Q, { title: 'Shop drawings for the library', assignee: 'Carlos Invented', due: d(4) }),
  };
  asFirmTasks().push({ id: uid('a'), title: 'Finish the overhead calculation before the cost-plus invoice', assignee: 'Controller', due: d(-1), status: 'todo', priority: 'med', section: 'Finance', code: '', tags: [], blockedBy: [], blocking: [], createdAt: d(-5), modifiedAt: d(-5), notes: 'Needs the September payroll' });
  save();
  tkItems();
  const out = {};
  Object.entries(made).forEach(([k, a]) => out[k] = a.id);
  return out;
}
"""

REC = r"""(id) => { for (const r of tkKeyedRecs()) if (r.rec.id === id) return JSON.parse(JSON.stringify(Object.assign({ board: r.board, kind: r.kind }, r.rec))); return null; }"""


async def click(pg, sel, wait=180):
    ok = await pg.evaluate("s => { const e = document.querySelector(s); if (!e) return false; e.click(); return true; }", sel)
    await pg.wait_for_timeout(wait)
    return ok


async def card(pg):
    return await pg.evaluate("() => { const c = document.querySelector('.mm-card'); const k = c && c.querySelector('.mm-key'); return { code: k ? k.innerText.trim() : '', at: mmAt, text: c ? c.innerText : '' }; }")


async def meeting(pg):
    return await pg.evaluate("() => { const m = mtCurrent() || mtTeam().slice(-1)[0]; return m ? JSON.parse(JSON.stringify(m)) : null; }")


async def nxt(pg, phone):
    if phone:
        await click(pg, '[data-mmnext]')
    else:
        await pg.keyboard.press('ArrowRight')
        await pg.wait_for_timeout(180)


async def go_to(pg, code):
    """Walk with Next or Previous until the code is on screen, the way the room does it."""
    for _ in range(80):
        cur = await card(pg)
        if cur['code'] == code:
            return True
        d = await pg.evaluate("(c) => { const S = mtSeq(mtCurrent()).map(s => s.code); return S.indexOf(c) - S.indexOf(mmAt); }", code)
        if d == 0:
            return False
        await click(pg, '[data-mmnext]' if d > 0 else '[data-mmprev]')
    return False


async def layout(c, pg, tag, phone):
    st = await pg.evaluate("""() => {
      const vis = (e) => { const r = e.getBoundingClientRect(), cs = getComputedStyle(e); return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none'; };
      const small = [...document.querySelectorAll('#v-tkall .mm button, #v-tkall .mm select, #v-tkall .mm input:not([type=hidden]):not([type=date]):not([type=checkbox]), #v-tkall .mm label.tks-chip')].filter(vis)
        .filter(b => { const r = b.getBoundingClientRect(); return r.height < 40 && !b.closest('.mm-side'); }).map(b => (b.innerText || b.getAttribute('aria-label') || b.tagName).trim().slice(0, 30));
      const prim = [...document.querySelectorAll('.btn.primary')].filter(vis).filter(b => !b.closest('#mbm')).map(b => b.innerText.trim());
      return { sw: document.documentElement.scrollWidth, small, prim };
    }""")
    if phone:
        c.ok(st['sw'] <= 390, f'{tag}: no sideways scroll at 390px (scrollWidth {st["sw"]})')
        c.ok(not st['small'], f'{tag}: tap targets at least 40px on the phone: {st["small"][:6]}')
    c.ok(len(st['prim']) <= 1, f'{tag}: one blue button on the screen, got {st["prim"]}')


async def run_meeting(c, p, uid, phone):
    tag = f'{uid}{" phone" if phone else ""}'
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, uid)
    ids = await pg.evaluate(SEED)
    me = await pg.evaluate("tdyMe().name")
    await go(pg, 'tkall')
    # the button: Start Meeting on Tasks for the owner and the coordinator, no new menu item
    c.ok(await pg.evaluate("() => !!document.querySelector('#v-tkall [data-mmstart]')"), f'{tag}: Start Meeting on Tasks')
    c.ok(await pg.evaluate("() => !Object.values(ROLE_VIEWS).some(L => L.includes('meeting') || L.includes('mmode'))"), f'{tag}: no new view or menu item')
    await click(pg, '#v-tkall [data-mmstart]', 250)
    await pg.evaluate("() => document.querySelector('#mbm #mbm-ok').click()")
    await pg.wait_for_timeout(400)
    m = await meeting(pg)
    c.ok(m and m['kind'] == 'team' and m['startedAt'] and not m['endedAt'], f'{tag}: the meeting is a record in DB.meetings, kind team')
    for k in ('id', 'kind', 'title', 'startedAt', 'endedAt', 'attendees', 'agenda', 'screenLog', 'changes', 'created', 'minutes'):
        c.ok(k in (m or {}), f'{tag}: the meeting record has {k} (lane B builds on the shape)')
    c.ok(me in m['attendees'], f'{tag}: the person who started it is in it')
    # the agenda builds itself: projects in the team's order, the late, the due, the waiting; FYI last and folded
    R = {k: await pg.evaluate(REC, v) for k, v in ids.items()}
    ag = m['agenda']
    items = [x for bb in ag for x in bb['items']]
    fyis = [x for bb in ag for x in bb['fyi']]
    c.ok(R['late']['code'] in items, f'{tag}: a late task is on the agenda')
    c.ok(R['soon']['code'] in items, f'{tag}: a task due before the next meeting is on the agenda')
    c.ok(R['wait']['code'] in items, f'{tag}: a task waiting on someone is on the agenda')
    c.ok(R['fyi']['code'] in fyis and R['fyi']['code'] not in items, f'{tag}: an FYI item is folded at the end of its project')
    c.ok(R['quiet']['code'] not in items, f'{tag}: a quiet task (due in a month, nothing changed) is not on the agenda')
    order = await pg.evaluate("mtOrder()")
    c.ok([bb['board'] for bb in ag] == [x for x in order if x in [bb['board'] for bb in ag]], f'{tag}: projects in the team order')
    for bb in ag:
        seq = await pg.evaluate("(b) => mtSeq(mtCurrent()).filter(s => s.board === b).map(s => s.t)", bb['board'])
        if bb['fyi']:
            c.ok(seq[-1] == 'fyi', f'{tag}: the FYI card comes last in {bb["name"]}')
    first = await card(pg)
    c.ok(CODE.match(first['code'] or ''), f'{tag}: the card shows the key ({first["code"]})')
    c.ok(len(m['screenLog']) == 1 and m['screenLog'][0]['taskKey'] == first['code'] and not m['screenLog'][0]['to'], f'{tag}: the screen log opens on the first card')
    await layout(c, pg, f'{tag} meeting card', phone)
    if phone:
        await pg.screenshot(path=f'../review/meeting/{uid}_phone_card.png')
    else:
        await pg.screenshot(path=f'../review/meeting/{uid}_desktop_card.png')
    visited = [first['code']]

    # ---- New Date: Tomorrow on the late task's due
    c.ok(await go_to(pg, R['late']['code']), f'{tag}: walk to the late task')
    visited.append(R['late']['code'])
    await click(pg, '[data-mmact="date"]')
    tom = await pg.evaluate("iso(addDays(today(), 1))")
    await click(pg, f'[data-mmdate="{tom}"]', 250)
    late = await pg.evaluate(REC, ids['late'])
    c.ok(late['due'] == tom, f'{tag}: New Date Tomorrow moved the due date ({late["due"]})')
    c.ok(late.get('lastDiscussed', {}).get('meetingId') == m['id'], f'{tag}: the task records that it was discussed in this meeting')
    m = await meeting(pg)
    ch = m['changes'][-1]
    c.ok(ch['field'] == 'due' and ch['to'] == tom and ch['taskKey'] == late['code'] and ch['by'] == me and ch['at'], f'{tag}: the change says who, what, from and to: {ch}')
    # ---- Note
    await click(pg, '[data-mmact="note"]')
    await pg.fill('[data-mmnotein]', 'Fabricator confirmed the slab is cut')
    await click(pg, '[data-mmnoteadd]', 250)
    late = await pg.evaluate(REC, ids['late'])
    c.ok(any(e.get('text') == 'Fabricator confirmed the slab is cut' and e.get('id') for e in late.get('thread', [])), f'{tag}: Note is a comment on the task, with an id')
    c.ok('Fabricator confirmed' in (await card(pg))['text'], f'{tag}: the card shows the last comments')
    # ---- Reassign
    await click(pg, '[data-mmact="owner"]')
    await click(pg, '[data-mmowner="Alan"]', 250)
    late = await pg.evaluate(REC, ids['late'])
    c.ok(late['assignee'] == 'Alan', f'{tag}: Reassign makes Alan the owner')
    c.ok(not late.get('handoff') or late['handoff'].get('state') != 'offered', f'{tag}: a reassignment in the meeting is not left as an offer')
    # ---- Decision (behind More)
    await click(pg, '[data-mmact="more"]')
    await click(pg, '[data-mmpanel="decision"]')
    await pg.fill('[data-mmdecin]', 'Release the deposit once the slab photos are in')
    await click(pg, '[data-mmdec="aligned"]', 250)
    # ---- Move Down (behind More: the order never changes by a stray click)
    c.ok(not await pg.evaluate("() => [...document.querySelectorAll('.mm [draggable=true]')].length"), f'{tag}: nothing in Meeting Mode can be dragged')
    o0 = await pg.evaluate("(c) => mtSeq(mtCurrent()).map(s => s.code).indexOf(c)", late['code'])
    await click(pg, '[data-mmact="more"]')
    await click(pg, '[data-mmmove="1"]', 250)
    o1 = await pg.evaluate("(c) => mtSeq(mtCurrent()).map(s => s.code).indexOf(c)", late['code'])
    late2 = await pg.evaluate(REC, ids['late'])
    c.ok(o1 == o0 + 1 or o0 == o1 and late2.get('order'), f'{tag}: Move Down moves it one place in its project ({o0} to {o1})')
    await click(pg, '[data-mmact="more"]')
    await click(pg, '[data-mmmove="-1"]', 250)
    # ---- Done on the task due soon (no proof needed)
    c.ok(await go_to(pg, R['soon']['code']), f'{tag}: walk to the task due soon')
    visited.append(R['soon']['code'])
    await click(pg, '[data-mmact="done"]', 300)
    soon = await pg.evaluate(REC, ids['soon'])
    c.ok(soon['status'] == 'done', f'{tag}: Done closes the task')
    c.ok((await card(pg))['code'] != R['soon']['code'], f'{tag}: Done moves on to the next card')
    # ---- Waiting On: the vendor owes the boxes, by a promised date, with the evidence
    c.ok(await go_to(pg, R['wait']['code']), f'{tag}: walk to the waiting task')
    visited.append(R['wait']['code'])
    c.ok('Waiting on Invented Millwork Co' in (await card(pg))['text'], f'{tag}: the card shows Waiting On as a chip')
    await click(pg, '[data-mmact="wait"]')
    await pg.fill('[data-mmw="what"]', 'dining boxes')
    nm = await pg.evaluate("mtNextMeeting()")
    await click(pg, f'[data-mmwprom="{nm}"]')
    await click(pg, '[data-mmwsave]', 250)
    w = await pg.evaluate(REC, ids['wait'])
    W = w.get('waitingOn') or {}
    c.ok(W.get('name') == 'Invented Millwork Co' and W.get('what') == 'dining boxes' and W.get('promised') == nm and W.get('evidence'), f'{tag}: Waiting On holds who, what, promised and evidence: {W}')
    c.ok(w['status'] == 'waiting' and w['assignee'] == 'Alan', f'{tag}: the task is Waiting On and Alan still owns it')
    chip = await pg.evaluate("(w) => tkWaitSay(w)", W)
    c.ok(re.match(r'^Waiting on Invented Millwork Co: dining boxes, promised \w{3} \d+/\d+$', chip or ''), f'{tag}: the chip reads "{chip}"')
    # ---- New Date on the follow-up (a waiting task's date is its chase date)
    await click(pg, '[data-mmact="date"]')
    td = await pg.evaluate("today()")
    await click(pg, f'[data-mmdate="{td}"]', 250)
    w = await pg.evaluate(REC, ids['wait'])
    c.ok(w.get('followUp') == td and w['due'] != td, f'{tag}: New Date on a waiting task moves the follow-up, apart from the due date')
    # ---- Track Until
    await click(pg, '[data-mmact="track"]')
    await click(pg, f'[data-mmtrack="{nm}"]', 250)
    w = await pg.evaluate(REC, ids['wait'])
    c.ok(w.get('watchUntil') == nm, f'{tag}: Track Until sets the watch date')
    # ---- the outside owner, migrated at boot: Waiting On Carlos, owner the job's lead, flagged
    c.ok(await go_to(pg, R['outside']['code']), f'{tag}: walk to the migrated task')
    visited.append(R['outside']['code'])
    c.ok('Confirm or reassign' in (await card(pg))['text'], f'{tag}: the card flags an owner set by the migration')
    # ---- Skip
    await click(pg, '[data-mmact="skip"]', 250)
    m = await meeting(pg)
    c.ok(m['changes'][-1]['field'] == 'skip' and m['changes'][-1]['taskKey'] == R['outside']['code'], f'{tag}: Skip is logged and moves on')
    # ---- FYI on the quiet-for-now task in the firm list (Finance)
    fin = await pg.evaluate("() => { const r = tkKeyedRecs().find(r => r.board === 's:Finance'); return r ? r.rec.code : ''; }")
    c.ok(await go_to(pg, fin), f'{tag}: walk to the Finance list ({fin})')
    visited.append(fin)
    await click(pg, '[data-mmact="fyi"]', 250)
    st = await pg.evaluate("(c) => { const T = tkByCode(c); return tkStatusOf(T.kind, T.rec); }", fin)
    c.ok(st == 'fyi', f'{tag}: FYI makes it status only')
    c.ok(not await pg.evaluate("(c) => { const x = tkItems().find(x => x.code === c); return !!(x && x.late); }", fin), f'{tag}: an FYI item never counts as late')
    # ---- add a task inline under the project on screen
    c.ok(await go_to(pg, R['wait']['code']), f'{tag}: back to the job to add a task')
    visited.append(R['wait']['code'])
    await pg.fill('[data-mmaddt]', 'Send the library shop drawings to the client')
    await pg.select_option('[data-mmaddo]', 'Chen Biron')
    await click(pg, '[data-mmadd]', 300)
    m = await meeting(pg)
    new = m['created'][-1] if m['created'] else ''
    T = await pg.evaluate("(c) => { const T = tkByCode(c); return T ? { board: T.board, owner: T.rec.assignee, src: T.rec.source } : null; }", new)
    c.ok(CODE.match(new) and T and T['board'] == R['wait']['board'] and T['owner'] == 'Chen Biron', f'{tag}: the new task gets the project key and its owner ({new}, {T})')
    c.ok(new in [x for bb in m['agenda'] for x in bb['items']], f'{tag}: the new task joins the agenda after the card on screen')
    # ---- add a project inline: its prefix on the spot, and its first task
    await click(pg, '[data-mmact="addproj"]')
    await pg.fill('[data-mmp="name"]', 'Invented Park Duplex')
    pre = await pg.evaluate("() => document.querySelector('[data-mmp=\"prefix\"]').value")
    c.ok(pre == 'IPD', f'{tag}: the prefix fills from the name ({pre})')
    await pg.fill('[data-mmp="prefix"]', 'PAD' if not phone else 'PDX')
    await click(pg, '[data-mmpsave]', 300)
    m = await meeting(pg)
    bid = 's:Invented Park Duplex'
    c.ok(any(bb['board'] == bid for bb in m['agenda']), f'{tag}: the new project is on the agenda')
    c.ok((await card(pg))['at'] == 'EMPTY:' + bid, f'{tag}: the screen moves to the new project')
    await pg.fill('[data-mmaddt]', 'Measure the windows at the new job')
    await click(pg, '[data-mmadd]', 300)
    m = await meeting(pg)
    want = ('PAD' if not phone else 'PDX') + '-1'
    c.ok(m['created'][-1] == want, f'{tag}: the new project first task is {want} ({m["created"][-1:]})')
    visited.append(want)
    # ---- a second decision, to discuss
    await click(pg, '[data-mmact="more"]')
    await click(pg, '[data-mmpanel="decision"]')
    await pg.fill('[data-mmdecin]', 'The client still has to confirm the finish')
    await click(pg, '[data-mmdec="to-discuss"]', 250)
    # ---- Previous goes back
    before = (await card(pg))['code']
    if phone:
        await click(pg, '[data-mmprev]')
    else:
        await pg.keyboard.press('ArrowLeft')
        await pg.wait_for_timeout(180)
    c.ok((await card(pg))['code'] != before, f'{tag}: Previous goes back a card')
    # ---- the screen log: in order, each closed when the next opened, every card that was on screen
    m = await meeting(pg)
    L = m['screenLog']
    c.ok(all(L[i]['to'] and L[i]['to'] >= L[i]['from'] for i in range(len(L) - 1)), f'{tag}: each screen line is closed')
    c.ok(all(L[i]['to'] <= L[i + 1]['from'] for i in range(len(L) - 1)), f'{tag}: no two lines overlap: one card on screen at a time')
    c.ok(all(x in [l['taskKey'] for l in L] for x in visited if x), f'{tag}: every card shown is in the screen log')
    c.ok(all(l.get('ref') for l in L), f'{tag}: each screen line carries its record')
    # ---- Follow: a second screen shows the presenter's card
    other = await pg.evaluate("(c) => { const m = mtCurrent(); const s = mtSeq(m).find(s => s.t === 'task' && s.code !== mmAt); return s ? s.code : ''; }", before)
    await pg.evaluate("(c) => { const m = mtCurrent(); m.presenterUid = 'u_someone_else'; m.cursor = { code: c, at: appNowIso(), by: 'Someone' }; renderTkAll(); }", other)
    await pg.wait_for_timeout(200)
    c.ok((await card(pg))['code'] == other, f'{tag}: Follow shows the presenter card')
    await pg.evaluate("() => { const f = document.querySelector('[data-mmfollow]'); f.checked = false; f.dispatchEvent(new Event('change')); }")
    await pg.wait_for_timeout(150)
    await pg.evaluate("() => { const m = mtCurrent(); const s = mtSeq(m).filter(s => s.t === 'task'); m.cursor = { code: s[0].code, at: appNowIso(), by: 'Someone' }; renderTkAll(); }")
    await pg.wait_for_timeout(150)
    c.ok((await card(pg))['code'] == other, f'{tag}: Follow off keeps this screen where it is')
    await pg.evaluate(f"() => {{ const m = mtCurrent(); m.presenterUid = tdyMe().id; mmFollow = true; renderTkAll(); }}")
    await layout(c, pg, f'{tag} meeting end', phone)
    # ---- End Meeting writes the minutes
    await click(pg, '[data-mmend]', 300)
    c.ok(await pg.evaluate("() => !!document.querySelector('#mbm .mm-minutes')"), f'{tag}: End Meeting shows the minutes first')
    await pg.evaluate("() => document.querySelector('#mbm #mbm-ok').click()")
    await pg.wait_for_timeout(400)
    m = await meeting(pg)
    c.ok(m['endedAt'] and m['minutes'], f'{tag}: the meeting is ended with its minutes')
    M = m['minutes']
    c.ok(any(x['code'] == late['code'] and x['field'] == 'due' and x['to'] == tom for x in M['moved']), f'{tag}: minutes, moved: {late["code"]} to tomorrow')
    c.ok(any(x['code'] == w['code'] and x['field'] == 'followUp' for x in M['moved']), f'{tag}: minutes, moved: the follow-up')
    c.ok(any(x['code'] == w['code'] and x['field'] == 'watchUntil' for x in M['moved']), f'{tag}: minutes, moved: the tracking date')
    c.ok({x['code'] for x in M['created']} == {new, want}, f'{tag}: minutes, new: {[x["code"] for x in M["created"]]}')
    c.ok([x['code'] for x in M['done']] == [soon['code']], f'{tag}: minutes, done: {[x["code"] for x in M["done"]]}')
    c.ok([d['text'] for d in M['decisions']['aligned']] == ['Release the deposit once the slab photos are in'], f'{tag}: minutes, decisions aligned')
    c.ok([d['text'] for d in M['decisions']['discuss']] == ['The client still has to confirm the finish'], f'{tag}: minutes, decisions to discuss')
    owes = M['owes']
    c.ok(any(x['code'] == late['code'] and x['by'] == tom for x in owes.get('Alan', [])), f'{tag}: minutes, Alan owes {late["code"]} by tomorrow')
    c.ok(any(x['code'] == new for x in owes.get('Chen Biron', [])), f'{tag}: minutes, Chen owes the new task')
    c.ok(any(x['code'] == w['code'] and x['waitingOn'] == 'Invented Millwork Co' for x in owes.get('Alan', [])), f'{tag}: minutes, the waiting task names who it waits on')
    c.ok(not any(x['code'] == soon['code'] for L2 in owes.values() for x in L2), f'{tag}: minutes, a done task is owed by nobody')
    c.ok('Who owes what by when' in M.get('text', ''), f'{tag}: the minutes as text')
    kinds = {x['field'] for x in m['changes']}
    for f in ('due', 'followUp', 'watchUntil', 'comment', 'owner', 'status', 'waitingOn', 'skip', 'decision', 'created', 'project', 'order'):
        c.ok(f in kinds, f'{tag}: the changes hold a {f} change')
    c.ok(all(x.get('id') and x.get('at') and x.get('by') for x in m['changes']), f'{tag}: every change has an id, a time and a person')
    c.ok(not m['screenLog'][-1]['to'] == '', f'{tag}: the last screen line closes at the end')
    # findable: on Meetings, and on Today for each person, one line that opens the minutes
    await pg.evaluate("(id) => { view = 'meetings'; mtTab = 'meetings'; mtOpen = id; render(); }", m['id'])
    await pg.wait_for_timeout(250)
    c.ok(await pg.evaluate("() => /Minutes/.test(document.getElementById('meetings-body').innerText) && !!document.querySelector('#meetings-body .mm-minutes')"), f'{tag}: the minutes are on the meeting record in Meetings')
    for who in ('u_alan', 'u_chen'):
        await sign_in(pg, who)
        L = await pg.evaluate("() => tdyModel().tasks.filter(i => i.kind === 'tdyMinutes').map(i => ({ id: i.id, title: i.title, detail: i.detail }))")
        c.ok(len([x for x in L if x['id'] == m['id']]) == 1, f'{tag}: {who} has one Today line for the minutes: {L}')
        await pg.evaluate("() => { tdyTabSet('tasks'); tdyAllOpen = true; view = 'home'; render(); }")
        await pg.wait_for_timeout(200)
        opened = await pg.evaluate("""(id) => { const a = [...document.querySelectorAll('[data-tdrec]')].find(a => /^Minutes:/.test(a.innerText.trim())); if (!a) return false; a.click(); return true; }""", m['id'])
        await pg.wait_for_timeout(300)
        shown = await pg.evaluate("() => !!document.querySelector('#mbm .mm-minutes')")
        c.ok(opened and shown, f'{tag}: {who} opens the minutes from Today')
        if who == 'u_alan':
            c.ok(await pg.evaluate("() => /You owe/.test(document.querySelector('#mbm').innerText)"), f'{tag}: Alan sees what he owes first')
        await pg.evaluate("() => mbCloseModal()")
        gone = await pg.evaluate("(id) => !tdyModel().tasks.some(i => i.kind === 'tdyMinutes' && i.id === id)", m['id'])
        c.ok(gone, f'{tag}: {who}: once read, the line leaves Today')
    c.ok(not errs, f'{tag}: no page errors: {errs[:3]}')
    await b.close()


async def record_checks(c, p):
    """Keys, owners, search and the sheet, as the owner on desktop."""
    b, pg, errs = await open_app(p)
    await sign_in(pg, 'u_owner')
    ids = await pg.evaluate(SEED)
    # every board task has a key, unique; every board a unique prefix
    st = await pg.evaluate("""() => { const R = tkKeyedRecs(); const codes = R.map(r => r.rec.code); const B = tkBoards().map(id => (tkBoardMeta(id) || {}).prefix);
      return { n: R.length, codes, dup: codes.filter((c, i) => codes.indexOf(c) !== i), pre: B, dupPre: B.filter((c, i) => B.indexOf(c) !== i) }; }""")
    c.ok(st['n'] > 10 and all(CODE.match(x or '') for x in st['codes']), f'record: every board task has a key: {[x for x in st["codes"] if not CODE.match(x or "")][:5]}')
    c.ok(not st['dup'], f'record: keys are unique: {st["dup"]}')
    c.ok(not st['dupPre'] and all(st['pre']), f'record: prefixes are unique: {st["pre"]}')
    # the migration: an outside owner becomes Waiting On, the job's lead owns it, flagged to confirm
    o = await pg.evaluate(REC, ids['outside'])
    lead = await pg.evaluate("() => nsJobLead(DB.projects.find(p => p.id === 'p121') || DB.projects[1])")
    c.ok(o['assignee'] == lead and o['assignee'] != 'Carlos Invented', f'record: the outside owner is replaced by the job lead ({o["assignee"]})')
    c.ok((o.get('waitingOn') or {}).get('name') == 'Carlos Invented' and o.get('status') == 'waiting', f'record: the outside person is Waiting On: {o.get("waitingOn")}')
    c.ok((o.get('ownerFlag') or {}).get('why') == 'outside' and o['ownerFlag'].get('was') == 'Carlos Invented', f'record: the change is flagged to confirm: {o.get("ownerFlag")}')
    w = await pg.evaluate(REC, ids['wait'])
    c.ok((w.get('waitingOn') or {}).get('name') == 'Invented Millwork Co' and w['waitingOn'].get('promised'), f'record: an old waitsOn becomes a Waiting On record: {w.get("waitingOn")}')
    fin = await pg.evaluate("() => { const r = tkKeyedRecs().find(r => r.board === 's:Finance'); return JSON.parse(JSON.stringify(r.rec)); }")
    c.ok(fin.get('notesMoved') and fin['thread'][0]['text'] == 'Needs the September payroll', 'record: notes become the first comment')
    c.ok(await pg.evaluate("() => tkKeyedRecs().every(r => tkRecDone(r.kind, r.rec) || !!tkInternal(r.rec.assignee))"), 'record: every open board task has an owner on the team')
    # a vendor can never be the owner: the record, the creation path and the board editor
    r = await pg.evaluate("(id) => { const T = tkKeyedRecs().find(r => r.rec.id === id); return tkSetOwner(T, 'Invented Millwork Co'); }", ids['wait'])
    c.ok(not r['ok'] and 'not on the team' in r['why'], f'record: tkSetOwner refuses a vendor: {r}')
    r = await pg.evaluate("() => { const m = crCreateTask({ title: 'Invented: get the stair quote', for: 'p:p121', assignee: 'Invented Millwork Co', source: { assistant: true } }); return JSON.parse(JSON.stringify({ a: m.rec.assignee, w: m.rec.waitingOn, f: m.rec.ownerFlag, code: m.rec.code })); }")
    c.ok(r['a'] == 'Owner' and (r['w'] or {}).get('name') == 'Invented Millwork Co' and (r['f'] or {}).get('why') == 'outside' and CODE.match(r['code']), f'record: the creation path makes the vendor Waiting On and the maker the owner: {r}')
    await go(pg, 'tkall')
    gate = await pg.evaluate("""() => { const a = asAllTasks()[0]; asTaskDialog(a.a.id); const m = document.getElementById('mbm'); if (!m) return 'no dialog';
      const who = m.querySelector('[data-f="assignee"]'); who.value = 'Invented Millwork Co'; const was = a.a.assignee; m.querySelector('#mbm-ok').click();
      const still = !!document.getElementById('mbm'); mbCloseModal(); return { still, kept: a.a.assignee === was }; }""")
    c.ok(gate.get('still') and gate.get('kept') if isinstance(gate, dict) else False, f'record: the board editor will not save a vendor as the owner: {gate}')
    # keys never reused: delete the newest, the next is the number after it; a duplicate after a merge moves on
    k = await pg.evaluate("""() => { const p = DB.projects.find(p => p.id === 'p121'); const m1 = crCreateTask({ title: 'Invented one', for: 'p:p121', assignee: 'Alan' });
      const c1 = m1.rec.code; p.actions = p.actions.filter(a => a.id !== m1.rec.id); save(); tkItems();
      const m2 = crCreateTask({ title: 'Invented two', for: 'p:p121', assignee: 'Alan' }); return { c1, c2: m2.rec.code, id2: m2.rec.id }; }""")
    n1, n2 = int(k['c1'].split('-')[1]), int(k['c2'].split('-')[1])
    c.ok(n2 == n1 + 1, f'record: a deleted number is never given again ({k["c1"]} deleted, next {k["c2"]})')
    d = await pg.evaluate("""(id2) => { const p = DB.projects.find(p => p.id === 'p121'); const a = { id: 'a_zz_dup', title: 'Invented made on another device', assignee: 'Alan', status: 'todo', createdAt: '2099-01-01', code: p.actions.find(x => x.id === id2).code };
      p.actions.push(a); tkRecSweep(); const codes = tkKeyedRecs().map(r => r.rec.code); return { kept: p.actions.find(x => x.id === id2).code, moved: a.code, was: a.keyWas, dup: codes.filter((c, i) => codes.indexOf(c) !== i) }; }""", k['id2'])
    c.ok(d['kept'] == k['c2'] and d['moved'] != k['c2'] and d['was'] == [k['c2']] and not d['dup'], f'record: two devices that both said {k["c2"]}: the later one moves on ({d})')
    pr = await pg.evaluate("""() => { const id = 'p:p121', was = tkBoardMeta(id).prefix; const one = tkKeyedRecs().find(r => r.board === id).rec; const old = one.code;
      const bad = tkSetPrefix(id, tkBoardMeta('p:p206').prefix); const ok = tkSetPrefix(id, 'SST'); return { was, bad, ok, old, now: one.code, found: (tkByCode(old) || {}).rec === one }; }""")
    c.ok(not pr['bad']['ok'], f'record: a prefix another project holds is refused: {pr["bad"]}')
    c.ok(pr['ok']['ok'] and pr['now'].startswith('SST-') and pr['found'], f'record: renaming the prefix moves the keys and the old key still finds the task: {pr}')
    # shown on every row and in the sheet; found by Tasks search, Cmd-K, Ask and erpQuery
    code = (await pg.evaluate(REC, ids['wait']))['code']
    await pg.evaluate("() => { tkWho = 'all'; t2View = 'all'; tkProject = ''; renderTkAll(); }")
    await pg.wait_for_timeout(200)
    c.ok(await pg.evaluate("(c) => [...document.querySelectorAll('#tkall-body .tk2-key')].some(e => e.innerText.trim() === c)", code), f'record: the row shows {code}')
    c.ok(await pg.evaluate("() => [...document.querySelectorAll('#tkall-body .tk2-row')].filter(r => /^(action|firm|hub):/.test(r.dataset.tkkey)).every(r => r.querySelector('.tk2-key'))"), 'record: every board row shows its key')
    await pg.evaluate("(c) => { t2Q = c; renderTkAll(); }", code)
    await pg.wait_for_timeout(200)
    rows = await pg.evaluate("() => [...document.querySelectorAll('#tkall-body .tk2-row')].map(r => r.innerText)")
    c.ok(len(rows) == 1 and code in rows[0], f'record: Tasks search finds {code}: {len(rows)} rows')
    await pg.evaluate("() => { t2Q = ''; renderTkAll(); }")
    pal = await pg.evaluate("(c) => palIndex().filter(i => i.t.startsWith(c + ' ')).map(i => i.k + ': ' + i.t)", code)
    c.ok(len(pal) == 1, f'record: Cmd-K lists {code} once: {pal}')
    c.ok(not await pg.evaluate("() => palIndex().some(i => i.k === 'to-do')"), 'record: Cmd-K has one row per task (the keyless to-do rows are gone)')
    a = await pg.evaluate("(c) => Promise.resolve(paAsk('what is ' + c.toLowerCase() + '?')).then(a => a && a.headline || '')", code)
    c.ok(code in a and 'Invented Millwork Co' in a, f'record: Ask answers about {code}: {a[:160]}')
    eq = await pg.evaluate("(c) => eqTasks().filter(r => r.key === c).map(r => [r.key, r.waitingOnName, r.statusLabel])", code)
    c.ok(eq == [[code, 'Invented Millwork Co', 'Waiting On']], f'record: erpQuery reads the key and Waiting On: {eq}')
    # the sheet: the key, status, follow-up, Waiting On, collaborators, links, attachments
    key = await pg.evaluate("(id) => { const r = tkKeyedRecs().find(r => r.rec.id === id); return tkRecKey(r); }", ids['wait'])
    await pg.evaluate("(k) => tkSheet(k)", key)
    await pg.wait_for_timeout(200)
    sh = await pg.evaluate("() => { const m = document.getElementById('mbm'); return { key: (m.querySelector('.tks-key') || {}).innerText, st: [...m.querySelectorAll('[data-tksst]')].map(b => b.innerText), wait: !!m.querySelector('[data-tkswait]'), link: !!m.querySelector('[data-tkslinkadd]'), file: !!m.querySelector('[data-tksfile]') }; }")
    c.ok(sh['key'] == code and sh['st'] == ['To Do', 'Doing', 'Waiting On', 'FYI'] and sh['wait'] and sh['link'] and sh['file'], f'record: the sheet shows the key and the record fields: {sh}')
    tom = await pg.evaluate("iso(addDays(today(), 1))")
    await click(pg, f'#mbm [data-tksfu="{tom}"]', 250)
    c.ok((await pg.evaluate(REC, ids['wait'])).get('followUp') == tom, 'record: Follow Up from the sheet')
    await click(pg, '#mbm [data-tkscollab]', 200)
    await click(pg, '#mbm [data-tkcol="Chen Biron"]')
    await pg.evaluate("() => document.querySelector('#mbm #mbm-ok').click()")
    await pg.wait_for_timeout(300)
    c.ok((await pg.evaluate(REC, ids['wait'])).get('collaborators') == ['Chen Biron'], 'record: a collaborator from the sheet')
    await click(pg, '#mbm [data-tkslinkadd]', 200)
    v = await pg.evaluate("() => { const b = document.querySelector('#mbm [data-tklk^=\"vendor|\"]'); if (!b) return ''; const id = b.dataset.tklk; b.click(); return id; }")
    await pg.wait_for_timeout(250)
    lk = (await pg.evaluate(REC, ids['wait']))
    c.ok(v and any(f"{l['kind']}|{l['id']}" == v for l in ([lk.get('link')] + (lk.get('links') or [])) if l), f'record: a link to a vendor from the sheet ({v})')
    c.ok(await pg.evaluate("() => !!document.querySelector('#mbm [data-tkslink]')"), 'record: the sheet lists the link with Open')
    await pg.evaluate("() => mbCloseModal()")
    # Settings: the cadence
    await pg.evaluate("() => { view = 'meetings'; mtTab = 'settings'; mtOpen = ''; render(); }")
    await pg.wait_for_timeout(250)
    has = await pg.evaluate("() => !!document.querySelector('[data-mmcadence]')")
    c.ok(has, 'record: Settings holds the team meeting days')
    if has:
        await pg.evaluate("() => { const b = document.querySelector('[data-mmday=\"2\"]'); b.checked = true; b.dispatchEvent(new Event('change', { bubbles: true })); }")
        await pg.wait_for_timeout(150)
        c.ok(await pg.evaluate("() => JSON.stringify(mtCadence().days) === '[1,2,4]'"), 'record: the cadence saves')
    c.ok(not errs, f'record: no page errors: {errs[:3]}')
    await b.close()


async def main():
    import os
    os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'review', 'meeting'), exist_ok=True)
    c = Checks()
    async with async_playwright() as p:
        await record_checks(c, p)
        await run_meeting(c, p, 'u_chen', False)
        await run_meeting(c, p, 'u_owner', True)
    return c.done()

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
