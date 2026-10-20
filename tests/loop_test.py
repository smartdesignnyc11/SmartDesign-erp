"""The improvement loop (BACKLOG §1.19, §1.32 items 1, 3, 4, 5), walked as the people it serves.
Foreman on the phone and the PM on the desktop report the same problem; the coordinator's usage is counted; the
owner finds it ranked under Company › Meetings › Changes, approves the build (a ticket and a GitHub issue body), marks
it shipped; the PM gets a Today task, the foreman the answer and Still Wrong, which reopens it. A standard broken on two
days becomes a rule the owner applies and undoes. A month later the loop keeps what held and reopens what did not.
Lessons infer their moment and kind of job and say where they raise next; renewals are put on the calendar and chased
under each person's rule. The server's inbox is filed once. Desktop 1440 and phone 390.
Run: python3 build.py && cd tests && ./slot.sh python3 loop_test.py"""
import asyncio, json, os, sys
from harness import *

OUT = os.path.join(ROOT, 'review', 'loop')
os.makedirs(OUT, exist_ok=True)
c = Checks()

async def no_sideways(pg, what):
    w = await pg.evaluate("[document.documentElement.scrollWidth, innerWidth]")
    c.ok(w[0] <= w[1] + 1, f'{what}: no sideways scroll at 390 ({w})')

async def load_state(pg, state):
    """Carry the firm's records from one device to the next, the way sync does; the job on screen is this device's."""
    await pg.evaluate("""s => { const D = JSON.parse(s); Object.keys(D).forEach(k => DB[k] = D[k]);
        S = DB.projects.find(p => p.id === (S && S.id)) || DB.projects[0]; iaOneClock(); }""", state)
    c.ok(await pg.evaluate("today()") == '2026-09-03', 'the app day carries over with the records')

async def report(pg, what, bad, text, phone=False):
    """Report a Problem through the button on the screen, as a person would."""
    btn = await pg.query_selector('#rp-btn')
    vis = btn and await btn.is_visible()
    c.ok(vis, f'the Report a Problem button is on the screen ({"phone" if phone else "desktop"})')
    if vis: await btn.click()
    else: await pg.evaluate("rpOpen()")
    await pg.wait_for_selector('#rp-panel [data-rpv="%s"]' % what, timeout=5000)
    await pg.click('#rp-panel [data-rpv="%s"]' % what)
    await pg.fill('#rp-text', text)
    await pg.click('#rp-panel [data-rpv="%s"]' % bad)
    if phone: await no_sideways(pg, 'the report sheet')
    await pg.click('#rp-send')
    await pg.wait_for_timeout(250)

async def main():
    async with async_playwright() as p:
        # ---------------------------------------------------------------- an office device runs the loop's day when idle
        b, pg, errs0 = await open_app(p)
        await sign_in(pg, 'u_alan')
        early = await pg.evaluate("!!DB.company.loopLast")
        await pg.wait_for_function("DB.company.loopLast && DB.company.loopLast.src === 'boot'", timeout=20000)
        last = await pg.evaluate("DB.company.loopLast")
        c.ok(not early and last['watch'] > 0 and last['drafted'] == 0, f'after the app settles, not in the way of the first screen: the Standard Watch kept day by day, nothing drafted from one day: {last}')
        await b.close()

        # ---------------------------------------------------------------- the foreman, on the phone
        b, pg, errs = await open_app(p, phone=True)
        await sign_in(pg, 'u_angel')
        await pg.wait_for_timeout(1500)
        c.ok(await pg.evaluate("!DB.company.loopLast"), 'a field phone does not run the loop\'s day (an office device does, when it is idle)')
        await pg.evaluate("setView('sched')")
        await report(pg, 'save', 'stuck', 'Moved the framing date, it went back after a reload. Call me 555-1212, about $4,200', phone=True)
        s = await pg.evaluate("DB.signals.filter(s => s.kind === 'report').map(s => ({id: s.id, uid: s.uid, role: s.role, screen: s.screen, what: s.what, sev: s.sev, text: s.text, rec: s.rec, trail: (s.trail||[]).length, photo: (s.rep||{}).photo || ''}))")
        c.ok(len(s) == 1 and s[0]['role'] == 'foreman' and s[0]['screen'] == 'sched' and s[0]['sev'] == 'stuck' and s[0]['uid'] == 'u_angel', f'the report is a shared signal with the screen, the role and who: {s}')
        c.ok(s and '555-1212' not in s[0]['text'] and '4,200' not in s[0]['text'] and '[phone]' in s[0]['text'] and '[amount]' in s[0]['text'], f'no phone number or amount in what is kept: {s and s[0]["text"]}')
        c.ok(s and isinstance(s[0]['rec'], dict) and s[0]['trail'] > 0, 'the record on screen and the last steps are captured')
        ch = await pg.evaluate("DB.changes.filter(c => c.source === 'loop').map(c => ({key: c.key, status: c.status, title: c.title, people: c.loop.people}))")
        c.ok(len(ch) == 1 and ch[0]['key'] == 'imp:rp|sched|save' and ch[0]['status'] == 'draft', f'the brain triages it into one problem at once: {ch}')
        c.ok(await pg.evaluate("!(ROLE_VIEWS[role()] || []).includes('meetings')"), 'the foreman cannot open the Changes list (the owner decides)')
        await pg.screenshot(path=os.path.join(OUT, 'phone_foreman_report.png'))
        state = await pg.evaluate("JSON.stringify(DB)")
        await b.close()

        # ---------------------------------------------------------------- the PM, on the desktop, same problem
        b, pg, errs2 = await open_app(p)
        await load_state(pg, state)
        await sign_in(pg, 'u_alan')
        await go(pg, 'sched')
        await report(pg, 'save', 'slows', 'Same here: the date I typed on the schedule did not stay.')
        ch = await pg.evaluate("DB.changes.filter(c => c.source === 'loop').map(c => ({key: c.key, people: c.loop.people, roles: c.loop.roles, n: c.loop.n, stuck: c.loop.stuck, ev: c.evidence.length, rank: c.loop.rank, p: c.loop.p}))")
        c.ok(len(ch) == 1 and ch[0]['people'] == 2 and sorted(ch[0]['roles']) == ['foreman', 'pm'] and ch[0]['stuck'] == 1 and ch[0]['p'] == 'integrity', f'two people, one problem, ranked by integrity: {ch}')
        c.ok(await pg.evaluate("DB.changes.find(c => c.key === 'imp:rp|sched|save').id === lpId('ch', 'imp:rp|sched|save')"), "the problem's id comes from its key, so two devices drafting it the same morning make one record")

        # ---------------------------------------------------------------- the coordinator: what she does around the screens
        await sign_in(pg, 'u_chen')
        await go(pg, 'po')
        for i in range(3):
            await pg.evaluate("URL.createObjectURL(new Blob(['a,b\\n1,2'], {type: 'text/csv'}))")
        for i in range(3):
            await pg.evaluate("mbModal('New Note', '<div class=\"f\"><label>Note</label><input data-f=\"x\"></div>', {onSubmit: () => {}})")
            await pg.fill('#mbm input', 'half a thought')
            await pg.click('#mbm-cancel')
        u = await pg.evaluate("(DB.signals.find(s => s.id === 'us:' + today() + ':u_chen') || {}).by")
        c.ok(u and u.get('po', {}).get('export') == 3 and u.get('po', {}).get('abandon') == 3, f'exports and abandoned forms are counted on the screen: {u}')
        c.ok('half a thought' not in json.dumps(u), 'counts and screens only: nothing typed is kept')
        r = await pg.evaluate("lpTriage('test')")
        keys = await pg.evaluate("DB.changes.filter(c => c.source === 'loop').map(c => c.key)")
        c.ok('imp:us|po|export' in keys and 'imp:us|po|abandon' in keys, f'usage over its floor becomes a problem: {keys}')
        c.ok(not await pg.evaluate("(ROLE_VIEWS[role()]||[]).includes('meetings') && document.querySelector('[data-lpact^=\"ok|\"]')"), 'only the owner sees Approve')

        # a standard broken on two days: yesterday's Watch day plus today's
        await pg.evaluate("""() => { lpWatchSnap(); const t = DB.signals.find(s => s.kind === 'watch'); const y = iso(addDays(today(), -1));
            DB.signals.push(Object.assign({}, t, {id: 'sw:' + t.what + ':' + y, day: y})); window.__rule = t.what; lpTriage('test'); }""")
        rule = await pg.evaluate("window.__rule")

        # ---------------------------------------------------------------- the owner decides
        await sign_in(pg, 'u_owner')
        await pg.evaluate("lpOpen()")
        await pg.wait_for_timeout(250)
        cards = await pg.evaluate("[...document.querySelectorAll('.lp-card')].map(e => ({id: e.dataset.lpcard, rank: e.querySelector('.lp-rank').textContent, t: e.querySelector('.lp-title').textContent}))")
        c.ok(len(cards) >= 4, f'the ranked problems are on Meetings › Changes: {cards}')
        prim = await pg.evaluate("[...document.querySelectorAll('.view.on .btn.primary')].filter(b => b.offsetParent).length")
        c.ok(prim == 1, f'one blue button on the screen: {prim}')
        ranks = [x['rank'] for x in cards if x['rank']]
        c.ok(ranks == [f'#{i + 1}' for i in range(len(ranks))], f'ranked 1..n: {ranks}')
        order = await pg.evaluate("DB.changes.filter(c => c.source === 'loop' && c.status === 'draft').sort((a,b) => a.loop.rank - b.loop.rank).map(c => c.loop.p)")
        idx = await pg.evaluate("lpOrder()")
        c.ok([idx.index(x) for x in order] == sorted(idx.index(x) for x in order), f'by the Standard\'s order: {order}')
        tiles = await pg.evaluate("[...document.querySelectorAll('[data-lpmeasure] .gl')].map(g => [g.querySelector('.gl-k').textContent, g.querySelector('.gl-v').textContent])")
        st = await pg.evaluate("LOOP_CORE.stats(DB.changes, today())")
        c.ok(dict(tiles).get('Found') == str(st['found']) and dict(tiles).get('Waiting on You') == str(st['waiting']), f'the measures read the same numbers as the rules: {tiles} {st}')
        await pg.screenshot(path=os.path.join(OUT, 'desktop_owner_changes.png'))
        # Problem Reports names the change each report is part of
        await go(pg, 'rpbox')
        part = await pg.evaluate("[...document.querySelectorAll('.lp-part')].map(e => e.textContent)")
        c.ok(len(part) >= 2 and all('Part of' in x for x in part), f'each report says which problem it is part of: {part}')
        # approve the save problem: a build ticket
        sid = await pg.evaluate("DB.changes.find(c => c.key === 'imp:rp|sched|save').id")
        await pg.evaluate("lpOpen()")
        await pg.click(f'[data-lpact="ok|{sid}"]')
        await pg.wait_for_timeout(200)
        t = await pg.evaluate(f"(c => ({{status: c.status, no: (c.loop.ticket||{{}}).no, body: (c.loop.ticket||{{}}).body}}))(lpFind('{sid}'))")
        c.ok(t['status'] == 'approved' and t['no'] and t['no'].startswith('IMP-'), f'approving a change to the ERP makes a build ticket: {t["status"]} {t["no"]}')
        c.ok(t['body'] and '### Acceptance test' in t['body'] and '### Evidence' in t['body'] and '- [ ]' in t['body'] and '555' not in t['body'], 'the ticket is a GitHub issue body with the evidence and the acceptance test, and no phone number')
        toast = await pg.evaluate("document.getElementById('toast').innerText")
        c.ok('IMP-' in toast and 'Open' in toast, f'the approval toasts with Open: {toast}')
        reps = await pg.evaluate("rpAll().filter(r => r.screen === 'sched').map(r => [r.status, r.reply])")
        c.ok(len(reps) == 2 and all(r[0] == 'accepted' and 'Accepted' in r[1] for r in reps), f'both reporters are told it is accepted: {reps}')
        await pg.click(f'[data-lpact="issue|{sid}"]')
        await pg.wait_for_selector('#mbm .lp-issue', timeout=3000)
        c.ok('Acceptance test' in await pg.evaluate("document.querySelector('#mbm .lp-issue').value"), 'Copy as GitHub Issue shows the body to paste; nothing is opened on GitHub')
        await pg.click('#mbm-cancel')
        await pg.click(f'[data-lpact="ship|{sid}"]')
        await pg.wait_for_timeout(200)
        live = await pg.evaluate(f"lpFind('{sid}').status")
        c.ok(live == 'live', f'Mark Shipped makes it live: {live}')
        task = await pg.evaluate("asFirmTasks().filter(a => a.source && a.source.kind === 'improve' && /See what changed/.test(a.title)).map(a => [a.assignee, a.due])")
        c.ok(task == [['Alan', await pg.evaluate("today()")]], f'the PM who reported it gets a Today task, the foreman does not (the field reads the answer on the report): {task}')
        # a rule: apply, audited, undo
        rid = await pg.evaluate(f"DB.changes.find(c => c.key === 'imp:sw|{rule}').id")
        n0 = await pg.evaluate("asFirmTasks().length")
        await pg.evaluate("lpOpen()")
        await pg.click(f'[data-lpact="ok|{rid}"]')
        await pg.wait_for_timeout(150)
        rr = await pg.evaluate(f"(c => ({{status: c.status, on: DB.company.loopWatch['{rule}'], applied: c.loop.applied}}))(lpFind('{rid}'))")
        fired = await pg.evaluate("asFirmTasks().length") - n0
        c.ok(rr['status'] == 'live' and rr['on'] is True and rr['applied']['from'] is False, f'a rule applies on approval with its from and to: {rr}')
        c.ok(fired >= 1, f'and each breach is now a dated task for the rule\'s owner: {fired}')
        await pg.click(f'[data-lpact="undo|{rid}"]')
        rr = await pg.evaluate(f"(c => ({{status: c.status, on: DB.company.loopWatch['{rule}'], audit: (DB.audit||[]).filter(a => a.refId === c.id).map(a => a.action)}}))(lpFind('{rid}'))")
        c.ok(rr['status'] == 'reverted' and rr['on'] is False and 'applied' in rr['audit'] and 'reverted' in rr['audit'], f'Undo puts it back, on the audit trail: {rr}')
        # decline needs a reason, and is never proposed again
        did = await pg.evaluate("DB.changes.find(c => c.key === 'imp:us|po|abandon').id")
        await pg.click(f'[data-lpact="no|{did}"]')
        await pg.click('#mbm-ok')
        c.ok(await pg.evaluate(f"lpFind('{did}').status") == 'draft', 'declining with no reason is refused')
        await pg.fill('#mbm textarea', 'Cancel is the way to leave a note half written; working as intended.')
        await pg.click('#mbm-ok')
        await pg.evaluate("for (let i = 0; i < 4; i++) lpUsage('po', 'abandon'); lpTriage('test')")
        c.ok(await pg.evaluate(f"lpFind('{did}').status") == 'declined' and await pg.evaluate("DB.changes.filter(c => c.key === 'imp:us|po|abandon').length") == 1, 'declined, and not proposed again when it happens again')
        # Ask reads the same numbers
        a = await pg.evaluate("(paAsk('what has been fixed by the improvement loop') || {})")
        st = await pg.evaluate("LOOP_CORE.stats(DB.changes, today())")
        txt = json.dumps(a)
        c.ok(f"{st['found']} problem" in txt and f"{st['fixed']} fixed" in txt, f'Ask answers from the same measures: {txt[:300]}')
        c.ok(await pg.evaluate("eqRows ? eqRows('improvements').length : 0") == st['found'], 'Ask and the Report Builder read the improvements table')
        state = await pg.evaluate("JSON.stringify(DB)")
        await b.close()

        # ---------------------------------------------------------------- the foreman reads the answer, and says Still Wrong
        b, pg, errs3 = await open_app(p, phone=True)
        await load_state(pg, state)
        await sign_in(pg, 'u_angel')
        await pg.evaluate("rpOpen()")
        await pg.wait_for_selector('#rp-panel', timeout=3000)
        mine = await pg.evaluate("[...document.querySelectorAll('#rp-panel .rp-mine-row')].map(r => r.innerText)")
        c.ok(mine and 'Fixed in the ERP' in mine[0] and 'at the root' not in mine[0], f'the foreman reads, in plain words, that it was fixed (not the build instructions): {mine[:1]}')
        btn = await pg.query_selector('#rp-panel [data-lpstill]')
        c.ok(btn is not None, 'a fixed report offers Still Wrong')
        if btn:
            bb = await btn.bounding_box()
            c.ok(bb and bb['height'] >= 30, f'Still Wrong is a tap target on the phone: {bb}')
            await btn.click()
            await pg.wait_for_timeout(200)
        r = await pg.evaluate(f"(c => ({{status: c.status, rep: c.loop.repeat, n: c.loop.reopened, rank: c.loop.rank}}))(DB.changes.find(c => c.key === 'imp:rp|sched|save'))")
        c.ok(r['status'] == 'draft' and r['rep'] and r['n'] == 1, f'Still Wrong reopens it at once, as a repeat: {r}')
        await pg.screenshot(path=os.path.join(OUT, 'phone_foreman_still_wrong.png'))
        state = await pg.evaluate("JSON.stringify(DB)")
        await b.close()

        # ---------------------------------------------------------------- a month later; lessons; renewals; the server's inbox
        b, pg, errs4 = await open_app(p)
        await load_state(pg, state)
        await sign_in(pg, 'u_owner')
        # two fixes go live today: one that holds, one that keeps happening
        await pg.evaluate("""() => {
            const mk = (key, screen) => { const c = DB.changes.find(x => x.key === key); return c; };
            const ex = DB.changes.find(c => c.key === 'imp:us|po|export'); ex.status = 'live'; ex.loop.liveAt = today();
            const s1 = DB.changes.find(c => c.key === 'imp:rp|sched|save'); s1.status = 'live'; s1.loop.liveAt = today(); delete s1.loop.verified; }""")
        start = await pg.evaluate("today()")
        mid = await pg.evaluate("iso(addDays(today(), 10))")
        # ten days on, the schedule still loses dates for two people
        await pg.evaluate(f"""() => {{ ['u_alan','u_chen'].forEach((u, i) => DB.signals.push({{id: 'rp:later' + i, kind: 'report', day: '{mid}', uid: u, role: i ? 'coord' : 'pm', screen: 'sched', what: 'save', sev: 'slows', text: 'again'}})); }}""")
        r = await pg.evaluate(f"appSetDay(iso(addDays('{start}', 31)))")
        c.ok('lpDay' in r['ran'] and not [e for e in r['errors'] if 'lpDay' in e or 'lpAdmin' in e], f'the new day runs the loop: {r["ran"][-4:]} {r["errors"][:2]}')
        v = await pg.evaluate("DB.changes.filter(c => ['imp:us|po|export','imp:rp|sched|save'].includes(c.key)).map(c => [c.key, c.status, (c.loop.verified||{}).result || '', c.loop.reopened])")
        vd = {k: (s, res, n) for k, s, res, n in v}
        c.ok(vd['imp:us|po|export'][0] == 'live' and vd['imp:us|po|export'][1] == 'stopped', f'a fix that held is kept and says so: {vd}')
        c.ok(vd['imp:rp|sched|save'][0] == 'draft' and vd['imp:rp|sched|save'][2] >= 2, f'a fix that did not hold reopens a month later, a repeat: {vd}')
        st = await pg.evaluate("LOOP_CORE.stats(DB.changes, today())")
        c.ok(st['held'] >= 1 and st['repeats'] >= 1 and st['medianDays'] is not None, f'measured: held, repeats, time to fix: {st}')
        await pg.evaluate("appSetDay('2026-09-03')")

        # lessons: the moment and the kind of job from the lesson's own words, and where it raises next
        await go(pg, 'brain')
        await pg.evaluate("bnTeachModal({title: 'Millwork samples are approved by the client during design', then: {kind: 'task', title: 'Millshop samples approved', owner: 'designer'}, trigger: 'always', why: 'From the 8/28 meeting: samples came too late.'})")
        await pg.wait_for_selector('#mbm [data-f="jobType"]', timeout=3000)
        w = await pg.evaluate("[document.querySelector('#mbm [data-f=\"when\"]').value, document.querySelector('#mbm [data-f=\"jobType\"]').value]")
        c.ok(w[0] == 'design', f'a lesson read from a meeting opens with its moment (the design phase), not "as soon as it matches": {w}')
        await pg.select_option('#mbm [data-f="jobType"]', 'build')
        await pg.click('#mbm-ok')
        l = await pg.evaluate("(l => l && {when: l.when, jobType: l.jobType, id: l.id})(DB.lessons.find(l => /Millwork samples are approved/.test(l.title)))")
        c.ok(l and l['when'] == 'design' and l['jobType'] == 'build', f'the lesson keeps its moment and kind of job: {l}')
        nx = await pg.evaluate(f"lpLessonNext(DB.lessons.find(l => l.id === '{l['id']}'))") if l else []
        design_hit = await pg.evaluate(f"lpLessonNext(DB.lessons.find(l => l.id === '{l['id']}')).filter(x => lsIsDesign(DB.projects.find(p => p.id === x.projectId))).length") if l else 1
        c.ok(design_hit == 0, f'a construction-only lesson is never raised on a design job: {nx}')
        card = await pg.evaluate(f"bnLessonCard(DB.lessons.find(l => l.id === '{l['id']}'))") if l else ''
        c.ok('Construction jobs only' in card and ('Raises next on' in card or 'No live job matches it now' in card), 'the lesson card says the kind of job and where it raises next')

        # renewals: on the calendar and chased under the coordinator's own rule
        await sign_in(pg, 'u_chen')
        due = await pg.evaluate("lpAdminDue().filter(x => x.uid === 'u_chen').map(x => x.key)")
        c.ok(len(due) >= 1, f'the coordinator has renewals due (the office\'s go to her): {due}')
        await pg.evaluate("DB.company.adminChase = {}")
        r = await pg.evaluate("lpAdminSweep('test')")
        c.ok(r['held'] == len(due) and r['drafted'] == len(due) and r['sent'] == 0, f'Ask First (the default): each on her calendar and drafted into Approvals, nothing sent: {r}')
        cal = await pg.evaluate("DB.calendar.external.filter(e => e.adminKey && e.owner === 'u_chen').length")
        c.ok(cal == len(due), f'on her calendar: {cal}')
        act = await pg.evaluate("paActivity('u_chen').filter(e => e.type === 'adminChases').map(e => e.kind)")
        c.ok('proposed' in act, f"in her assistant's Activity: {act}")
        c.ok(await pg.evaluate("lpAdminSweep('again').drafted") == 0, 'never chased twice')
        await pg.evaluate("DB.company.adminChase = {}; DB.outbox = DB.outbox.filter(o => o.asstType !== 'adminChases'); paRuleSet('u_chen', 'adminChases', 'hand')")
        r = await pg.evaluate("lpAdminSweep('test')")
        c.ok(r['handed'] == len(due) and r['drafted'] == 0, f'Hand It to Me: handed back in Findings, nothing drafted: {r}')
        await pg.evaluate("DB.company.adminChase = {}; paRuleSet('u_chen', 'adminChases', 'alone'); DB.vendors.forEach(v => v.email = v.email || 'office@' + v.id + '.example')")
        r = await pg.evaluate("lpAdminSweep('test')")
        sent = await pg.evaluate("DB.outbox.filter(o => o.asstType === 'adminChases' && o.status === 'sent').map(o => o.to.email)")
        c.ok(r['sent'] + r['drafted'] == len(due) and all('@' in e for e in sent), f'Act Alone sends only to an address on file; without one it waits for her: {r} {sent}')

        # the server's nightly inbox is filed once
        await sign_in(pg, 'u_owner')
        box = {'loop': [{'at': '2026-09-03', 'drafts': [{'key': 'imp:rp|bank|wrong', 'title': 'Banking: it showed the wrong number', 'what': '1 report', 'kind': 'code', 'loop': {'gkey': 'rp|bank|wrong', 'p': 'integrity', 'people': 1, 'n': 1, 'days': 1, 'rank': 1}, 'evidence': [], 'fix': 'Trace it', 'risk': 'Low', 'accept': ['It ties'], 'aiText': {'title': 'Banking shows a wrong figure', 'what': 'One report.', 'fix': 'Trace it.', 'risk': 'Low.'}}], 'reopen': [], 'checks': []}]}
        n1 = await pg.evaluate("b => gsIngestServer(b)", box)
        n2 = await pg.evaluate("b => gsIngestServer(b)", box)
        k = await pg.evaluate("DB.changes.filter(c => c.key === 'imp:rp|bank|wrong').map(c => [c.loop.wordedBy, lpT(c, 'title')])")
        c.ok(n1 >= 1 and len(k) == 1 and k[0][0] == 'assistant' and k[0][1] == 'Banking shows a wrong figure', f"the server's problems are filed once, in the model's words when it had them: {n1} {n2} {k}")
        await b.close()

        # ---------------------------------------------------------------- the owner on the phone
        b, pg, errs5 = await open_app(p, phone=True)
        await load_state(pg, state)
        await sign_in(pg, 'u_owner')
        await pg.evaluate("lpOpen()")
        await pg.wait_for_timeout(250)
        await no_sideways(pg, "the owner's Changes list")
        small = await pg.evaluate("[...document.querySelectorAll('.lp-acts .btn')].filter(b => b.offsetParent).map(b => b.getBoundingClientRect().height).filter(h => h < 44)")
        c.ok(not small, f'the owner\'s buttons are 44px on the phone: {small}')
        await pg.screenshot(path=os.path.join(OUT, 'phone_owner_changes.png'))
        await b.close()

        allerrs = [e for e in errs0 + errs + errs2 + errs3 + errs4 + errs5 if 'favicon' not in e]
        c.ok(not allerrs, f'no errors: {allerrs[:4]}')
    return c.done()

sys.exit(asyncio.run(main()))
