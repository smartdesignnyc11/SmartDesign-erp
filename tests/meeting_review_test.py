"""The Meeting Review (docs/TASKS_PLAN.md §2 item 6; src/meetdoc_core.js, src/mtreview.js): the transcript of a team
meeting reconciles the board, and the meeting's owner approves it. An invented meeting (tests/meeting_sample_gemini.md:
demo people and jobs, an invented expediter and stone fabricator) is read as Gemini writes it, against an invented
Meeting Mode record (its screen log and the changes made live), as the coordinator and the owner, desktop and 390px:
  - every sentence lands on the task that was on screen when it was said (LEN-7's new date is said without its ID);
  - what was entered live in Meeting Mode, or is already so on the board, is not proposed again;
  - an outsider's promise is Waiting On, and a new one with no team member named waits for an owner to be picked;
  - Accept All updates the board through the task functions, with an audit line, and the toast opens the record;
  - nothing is lost: every item read is on the review, in exactly one state;
  - the transcript stays off the shared meeting record and is shown to attendees only;
  - the review is the meeting owner's card on Today and one item in Approvals.
Run: python3 build.py && cd tests && ./slot.sh python3 meeting_review_test.py"""
import asyncio, json, os, re, sys
from harness import *

c = Checks()
OUT = os.path.join(ROOT, 'review', 'mtreview')
os.makedirs(OUT, exist_ok=True)
DOC = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'meeting_sample_gemini.md'), encoding='utf-8').read()
NAME = 'Weekly Jobs - 2026/09/03 09:58 EDT - Notes by Gemini'
DAY = '2026-09-03'

SETUP = """([day]) => {
  mrvInit();
  const P = (id) => DB.projects.find(p => p.id === id);
  P('p121').project.prefix = 'STA'; P('p206').project.prefix = 'LEN';
  const add = (pid, ref, title, who, due, status) => { const p = P(pid); p.actions = p.actions || [];
    p.actions = p.actions.filter(a => a.ref !== ref);
    p.actions.push({id: 'a_' + ref.replace('-', ''), ref, title, assignee: who, due, priority: 'med', status: status || 'todo', link: null, notes: '', createdAt: '2026-08-20', completedAt: status === 'done' ? day : ''}); };
  add('p121', 'STA-21', 'Millwork shop drawings from Carlos', 'Chen Biron', '2026-09-04');   // moved live to Friday
  add('p121', 'STA-22', 'Release the deposit to Kestrel Stone for the parlor counters', 'Chen Biron', '2026-09-05', 'done');  // done live
  add('p121', 'STA-23', 'Window Works: credit for the wrong sash delivery', 'Chen Biron', '2026-09-01');
  add('p121', 'STA-24', 'Confirm the hall light fixture with the designer', 'Alan', '2026-09-04');
  add('p206', 'LEN-7', 'Order the vanity for the 3rd floor bath', 'Chen Biron', '2026-09-08');
  add('p206', 'LEN-8', 'Book the plumbing inspection', 'Alan', '2026-09-10');
  DB.meetings = DB.meetings.filter(m => m.id !== 'mt_live');
  DB.meetText = DB.meetText.filter(t => t.meetingId !== 'mt_live');
  const T = (h) => day + 'T' + h;
  // Meeting Mode's record (lane A's shape): what was on screen when, and what was changed live
  DB.meetings.push({id: 'mt_live', title: 'Weekly Jobs', date: day, source: 'live', status: 'new', createdAt: day, proposals: [], attendees: ['Chen Biron', 'Alan', 'Angel', 'Owner'],
    owner: {uid: 'u_chen', name: 'Chen Biron'}, startedAt: T('09:59:30'),
    screenLog: [{taskKey: 'STA-21', from: T('10:00:40'), to: T('10:03:10')}, {taskKey: 'STA-22', from: T('10:03:10'), to: T('10:05:40')},
                {taskKey: 'STA-23', from: T('10:05:40'), to: T('10:07:20')}, {taskKey: 'STA-24', from: T('10:07:20'), to: T('10:08:30')},
                {taskKey: 'LEN-7', from: T('10:08:30'), to: T('10:11:00')}, {taskKey: 'LEN-8', from: T('10:11:00'), to: T('10:13:00')}],
    changes: [{taskKey: 'STA-21', field: 'due', from: '2026-09-02', to: '2026-09-04', by: 'Chen Biron', at: T('10:02:15')},
              {taskKey: 'STA-22', field: 'status', from: 'todo', to: 'done', by: 'Chen Biron', at: T('10:04:55')}]});
  DB.audit = DB.audit || [];
  save();
}"""

# the server's path: the watcher filed the doc on the meeting; the coordinator's app builds the review on opening Today
INGEST = """([doc, name]) => { const m = mrvIngest(doc, {name, source: 'drive', docId: 'doc1', url: 'https://docs.google.com/document/d/doc1/edit'}); return m && m.id; }"""

def task_of(pr):
    return (pr.get('ref') or '') + ' ' + pr.get('kind', '')

async def setup(pg, who):
    await sign_in(pg, who)
    await pg.evaluate(SETUP, [DAY])

async def review(pg):
    return await pg.evaluate("""() => { const m = DB.meetings.find(x => x.id === 'mt_live');
      return {review: m.review, P: (m.proposals || []).filter(p => p.review).map(p => ({id: p.id, kind: p.kind, status: p.status, ref: p.ref, how: p.how, taskKey: p.taskKey, title: p.title, ts: p.ts,
        projectId: p.projectId, needs: mrvNeeds(p), apply: p.apply, source: p.source, line: p.line, head: p.head}))}; }""")

async def main():
    async with async_playwright() as p:
        # ---------------------------------------------------------------- the coordinator, desktop
        b, pg, errs = await open_app(p)
        await setup(pg, 'u_chen')
        mid = await pg.evaluate(INGEST, [DOC, NAME])
        c.ok(mid == 'mt_live', f"the doc joins Meeting Mode's record of that day, not a second meeting: {mid}")
        shared = await pg.evaluate("JSON.stringify(DB.meetings)")
        c.ok('Halden kitchen' not in shared and 'confirmed it by phone' not in shared, 'the transcript is not on the shared meeting record')
        T = await pg.evaluate("(t => t && {members: t.members, n: t.lines.length, start: t.start})(DB.meetText.find(t => t.meetingId === 'mt_live'))")
        c.ok(T and T['n'] == 22 and T['start'] == '2026-09-03T09:58:00' and set(['u_chen', 'u_alan', 'u_angel', 'u_owner']) <= set(T['members']) and 'u_billing' not in T['members'],
             f"the whole transcript is kept for the attendees, timed from the file's start: {T}")
        # Today builds it and shows the card
        await go(pg, 'home')
        await pg.wait_for_timeout(300)
        R = await review(pg)
        c.ok(R['review']['state'] == 'built' and R['review']['by'] == 'rules', f"the review is built on opening Today: {R['review']}")
        P = R['P']
        def one(kind, ref=None, rx=None):
            L = [x for x in P if x['kind'] == kind and (ref is None or x['ref'] == ref) and (rx is None or re.search(rx, x['title'] + json.dumps(x['apply']), re.I))]
            return L[0] if len(L) == 1 else (L or None)
        # each sentence lands on the task that was on screen
        d7 = one('tkdate', 'LEN-7')
        c.ok(isinstance(d7, dict) and d7['how'] == 'screen' and d7['apply']['due'] == '2026-09-04' and d7['status'] == 'proposed', f'"Move it to tomorrow then" (no ID said) lands on LEN-7, on screen at 10:10:27: {d7}')
        note = one('tknote', 'STA-23'); own = one('tkowner', 'STA-23'); cr = one('money', 'STA-23')
        c.ok(isinstance(note, dict) and 'phone' in note['apply']['text'] and isinstance(own, dict) and own['apply']['owner'] == 'Alan', f'the note and the reassignment land on STA-23: {note} {own}')
        c.ok(isinstance(cr, dict) and cr['apply']['amount'] == 1250 and (cr['apply'].get('link') or {}).get('kind') == 'bill', f"the credit carries its amount and the Window Works bill it touches: {cr}")
        w8 = one('tkwait', 'LEN-8')
        c.ok(isinstance(w8, dict) and w8['apply']['party'] == 'Ruth Okafor' and w8['apply']['by'] == '2026-09-08' and w8['apply']['owner'] == 'Alan', f"the expediter's promise is Waiting On, on LEN-8, owned by its owner: {w8}")
        w21 = one('tkwait', 'STA-21')
        c.ok(isinstance(w21, dict) and w21['apply']['party'] == 'Carlos' and w21['apply']['by'] == '2026-09-04', f"the millwork vendor's promise is Waiting On, on STA-21: {w21}")
        ang = one('task', rx='clear the bathroom')
        c.ok(isinstance(ang, dict) and ang['apply']['assignee'] == 'Angel' and ang['projectId'] == 'p206' and ang['apply']['due'] == '2026-09-07' and ang['status'] == 'proposed',
             f"a new task asked of Angel while LEN-8 was on screen is on 206 Lenox, with Gemini's duplicate merged: {ang}")
        # reconciled, never doubled
        live = [x for x in P if x['status'] == 'live']
        c.ok(any(x['kind'] == 'tkdate' and x['ref'] == 'STA-21' for x in live) and any(x['kind'] == 'tkdone' and x['ref'] == 'STA-22' for x in live), f'what was entered live is matched and left alone: {[(x["kind"], x["ref"]) for x in live]}')
        c.ok(not any(x['status'] == 'proposed' and ((x['kind'] == 'tkdate' and x['ref'] == 'STA-21') or (x['kind'] == 'tkdone' and x['ref'] == 'STA-22')) for x in P), 'and is not proposed again')
        board = [x for x in P if x['status'] == 'board']
        c.ok(len([x for x in board if x['source'] == 'notes']) >= 2, f"Gemini's next steps for tasks already on the board are not new tasks: {[x['title'] for x in board]}")
        # an outsider's promise with no team member named waits for an owner
        car = one('task', rx='portal samples')
        c.ok(isinstance(car, dict) and car['apply']['party'] == 'Carlos' and 'owner' in car['needs'] and car['status'] == 'proposed', f'a new Waiting On item asks for its internal owner: {car}')
        c.ok(all(x['kind'] != 'task' or x['apply'].get('party') != x['apply'].get('assignee') for x in P), 'a vendor is never the owner')
        # nothing lost: every item read is on the review once, in one state
        n_items = R['review']['items']
        c.ok(n_items == len(P) and all(x['status'] in ('proposed', 'live', 'board') for x in P), f'nothing lost: {n_items} items read, {len(P)} on the review')
        c.ok(len({x['id'] for x in P}) == len(P), 'one item once')
        # Today: the coordinator's card, one item in Approvals
        card = await pg.evaluate("(document.querySelector('#v-home') || document.body).innerText")
        c.ok('Meeting Review' in card, 'the review is a card on the coordinator\'s Today')
        ap = await pg.evaluate("mApprovals().filter(x => x.kind === 'meeting' && x.id === 'mt_live').map(x => ({who: x.who, yes: x.yes, n: x.n}))")
        c.ok(len(ap) == 1 and ap[0]['who'] == 'coord' and ap[0]['yes'] == 'Review', f'one item in Approvals, the meeting owner\'s: {ap}')
        await pg.screenshot(path=os.path.join(OUT, 'desktop_today_coord.png'))
        # open the review
        await pg.evaluate("mrvOpen('mt_live')")
        await pg.wait_for_timeout(250)
        txt = await pg.evaluate("document.getElementById('meetings-body').innerText")
        c.ok('Meeting Review' in txt and '206 Lenox' in txt and '121 State' in txt and 'Needs a Project or a Task' in txt, 'the review is grouped by project, with what waits for a pick')
        c.ok('“' in txt and '10:10' in txt, 'each item shows the sentence and its time of day')
        lnk = await pg.evaluate("[...document.querySelectorAll('.mrv-doc')].map(a => a.href)")
        c.ok(any('doc1' in h and '#heading=h.t0740' in h for h in lnk), f'the time links to the Gemini doc at that heading: {lnk[:3]}')
        prim = await pg.evaluate("[...document.querySelectorAll('#v-meetings .btn.primary')].filter(x => x.offsetParent).map(x => x.textContent)")
        c.ok(len(prim) == 1 and prim[0].startswith('Accept All'), f'one blue button, Accept All: {prim}')
        dis = await pg.evaluate(f"(b => b && b.disabled)(document.querySelector('[data-mrvok=\"{car['id']}\"]'))")
        c.ok(dis is True, 'Accept is off until the owner is picked')
        await pg.screenshot(path=os.path.join(OUT, 'desktop_review_coord.png'), full_page=True)
        # Accept All
        a0 = await pg.evaluate("DB.audit.length")
        await pg.click('#mrv-all')
        await pg.wait_for_timeout(300)
        toast = await pg.evaluate("document.getElementById('toast').innerText")
        c.ok(re.search(r'Applied \d+ from the meeting; \d+ wait', toast) and 'Open' in toast, f'Accept All toasts what it did and what waits, with Open: {toast}')
        B = await pg.evaluate("""() => { const P = id => DB.projects.find(p => p.id === id), A = (pid, ref) => P(pid).actions.find(a => a.ref === ref);
          return {len7: A('p206', 'LEN-7').due, sta23: A('p121', 'STA-23').assignee, sta23note: (A('p121', 'STA-23').thread || []).map(e => e.text || '').join('|'),
            sta23link: A('p121', 'STA-23').link, len8: [A('p206', 'LEN-8').waitsOn, A('p206', 'LEN-8').followUp], sta21: A('p121', 'STA-21').waitsOn,
            angel: P('p206').actions.filter(a => /clear the bathroom/i.test(a.title)).map(a => [a.assignee, a.due, a.source && a.source.kind]),
            orchard: DB.projects.filter(p => /Orchard/.test(p.project.name)).map(p => [p.project.prefix, p.project.createdFrom]),
            ev: DB.projects.flatMap(p => p.actions || []).concat(typeof asFirmTasks === 'function' ? asFirmTasks() : []).filter(a => /schedule meeting/i.test(a.title || a.text || '')).length,
            sta22: A('p121', 'STA-22').status, sta21due: A('p121', 'STA-21').due,
            changes: DB.meetings.find(m => m.id === 'mt_live').changes.filter(x => x.via === 'review').length}; }""")
        c.ok(B['len7'] == '2026-09-04', f"LEN-7's date moved: {B['len7']}")
        c.ok(B['sta23'] == 'Alan' and 'phone' in B['sta23note'] and '1,250' in B['sta23note'] and (B['sta23link'] or {}).get('kind') == 'bill', f'STA-23 reassigned, noted, the credit on its thread and linked to the bill: {B}')
        c.ok(B['len8'] == ['Ruth Okafor', '2026-09-08'] and B['sta21'] == 'Carlos', f'Waiting On set with the promised date as the follow-up: {B["len8"]} {B["sta21"]}')
        c.ok(B['angel'] == [['Angel', '2026-09-07', 'meeting']], f"Angel's new task is on 206 Lenox with the meeting as its source: {B['angel']}")
        c.ok(B['orchard'] == [['ORC', 'meeting']] and B['ev'] >= 1, f'the new project (with its prefix) and the follow-up meeting: {B["orchard"]} {B["ev"]}')
        c.ok(B['sta22'] == 'done' and B['sta21due'] == '2026-09-04', 'what was entered live is untouched')
        c.ok(B['changes'] >= 6, f"each applied item is on the meeting's changes, so the minutes and a re-read see it: {B['changes']}")
        a1 = await pg.evaluate("DB.audit.length")
        c.ok(a1 - a0 >= 8, f'every change has an audit line: {a1 - a0}')
        R2 = await review(pg)
        left = [x for x in R2['P'] if x['status'] == 'proposed']
        c.ok(left and all(x['needs'] for x in left), f'what waits is only what needs a pick: {[(x["title"], x["needs"]) for x in left]}')
        # pick the owner for the vendor's promise, then accept it
        await pg.select_option(f"[data-mrvowner=\"{car['id']}\"]", 'Chen Biron')
        await pg.wait_for_timeout(200)
        needs = await pg.evaluate(f"mrvNeeds(DB.meetings.find(m => m.id === 'mt_live').proposals.find(p => p.id === '{car['id']}'))")
        if 'project' in needs:
            await pg.select_option(f"[data-mrvproj=\"{car['id']}\"]", 'p121')
            await pg.wait_for_timeout(200)
        await pg.click(f"[data-mrvok=\"{car['id']}\"]")
        await pg.wait_for_timeout(250)
        made = await pg.evaluate("DB.projects.flatMap(p => p.actions || []).filter(a => /portal samples/i.test(a.title)).map(a => [a.assignee, a.waitsOn, a.waitingOn && a.waitingOn.by])")
        c.ok(made == [['Chen Biron', 'Carlos', '2026-09-09']], f'with an owner picked, the promise is a task waiting on Carlos, owned by Chen: {made}')
        toast = await pg.evaluate("document.getElementById('toast').innerText")
        c.ok('Applied' in toast and 'Open' in toast, f'the accept toasts with Open: {toast}')
        # the toast's Open lands on the task
        await pg.evaluate("[...document.querySelectorAll('#toast a')].find(a => a.textContent === 'Open').click()")
        await pg.wait_for_timeout(400)
        sheet = await pg.evaluate("(document.querySelector('#mbm') || {}).innerText || ''")
        c.ok('portal samples' in sheet.lower(), f'Open lands on the task it made: {sheet[:80]}')
        await pg.evaluate("mbCloseModal()")
        # findable on the board: the task list shows Angel's task under 206 Lenox
        found = await pg.evaluate("tkItems().filter(x => /clear the bathroom/i.test(x.title)).map(x => [x.projectId, x.assignee])")
        c.ok(found == [['p206', 'Angel']], f"the new task is on the one task list: {found}")
        # a rebuild never doubles what was decided
        await pg.evaluate("(m => { m.review.state = 'new'; mrvSweep(); })(DB.meetings.find(m => m.id === 'mt_live'))")
        R3 = await review(pg)
        c.ok(not [x for x in R3['P'] if x['status'] == 'proposed' and not x['needs']], f'read again, nothing applied comes back: {[x["title"] for x in R3["P"] if x["status"] == "proposed"]}')
        n_angel = await pg.evaluate("DB.projects.flatMap(p => p.actions || []).filter(a => /clear the bathroom/i.test(a.title)).length")
        c.ok(n_angel == 1, 'one task, once')
        await b.close()

        # ---------------------------------------------------------------- the owner, desktop: the review and privacy
        b, pg, errs2 = await open_app(p)
        await setup(pg, 'u_owner')
        await pg.evaluate(INGEST, [DOC, NAME])
        await go(pg, 'home')
        await pg.wait_for_timeout(300)
        ev = await pg.evaluate("mApprovals({everyone: true}).filter(x => x.kind === 'meeting' && x.id === 'mt_live').map(x => x.who)")
        c.ok(ev == ['coord'], f"the owner sees it in Everyone, waiting on the coordinator: {ev}")
        await pg.evaluate("mrvOpen('mt_live')")
        await pg.wait_for_timeout(250)
        q = await pg.evaluate("document.querySelectorAll('.mrv-q span').length")
        c.ok(q > 5, f'the owner reads the quotes: {q}')
        await pg.click('#mrv-all')
        await pg.wait_for_timeout(300)
        d = await pg.evaluate("DB.projects.find(p => p.id === 'p206').actions.find(a => a.ref === 'LEN-7').due")
        c.ok(d == '2026-09-04', 'the owner can accept it too')
        await b.close()

        b, pg, errs3 = await open_app(p)
        await setup(pg, 'u_chen')
        await pg.evaluate(INGEST, [DOC, NAME])
        await pg.evaluate("mrvRun(DB.meetings.find(m => m.id === 'mt_live'))")
        await sign_in(pg, 'u_billing')
        await pg.evaluate("mrvOpen('mt_live')")
        await pg.wait_for_timeout(250)
        txt = await pg.evaluate("document.getElementById('meetings-body').innerText")
        c.ok('attendees' in txt and 'phone' not in txt, 'someone who was not in the meeting sees the items, not the words')
        await b.close()

        # ---------------------------------------------------------------- the coordinator on the phone: paste, review, accept
        b, pg, errs4 = await open_app(p, phone=True)
        await setup(pg, 'u_chen')
        await pg.evaluate("mtTab = 'meetings'; mtOpen = 'mt_live'; view = 'meetings'; render()")
        await pg.wait_for_timeout(250)
        await pg.click('[data-mrvpaste="mt_live"]')
        await pg.fill('#mrv-text', DOC)
        await pg.fill('[data-f="start"]', '09:58:00')
        await pg.click('#mbm-ok')
        await pg.wait_for_timeout(500)
        R = await review(pg)
        d7 = [x for x in R['P'] if x['kind'] == 'tkdate' and x['ref'] == 'LEN-7']
        c.ok(R['review']['state'] == 'built' and d7 and d7[0]['how'] == 'screen', f'a pasted doc is read the same way on the phone: {R["review"]}')
        w = await pg.evaluate("[document.documentElement.scrollWidth, innerWidth]")
        c.ok(w[0] <= w[1] + 1, f'the review at 390: no sideways scroll ({w})')
        small = await pg.evaluate("[...document.querySelectorAll('.mrv-a .btn, .mrv-ph .acts .btn')].filter(x => x.offsetParent && x.getBoundingClientRect().height < 44).map(x => x.textContent)")
        c.ok(not small, f'tap targets at least 44px: {small}')
        await pg.screenshot(path=os.path.join(OUT, 'phone_review_coord.png'), full_page=True)
        await pg.click('#mrv-all')
        await pg.wait_for_timeout(300)
        d = await pg.evaluate("DB.projects.find(p => p.id === 'p206').actions.find(a => a.ref === 'LEN-7').due")
        c.ok(d == '2026-09-04', 'Accept All on the phone updates the board')
        await go(pg, 'home')
        await pg.wait_for_timeout(300)
        w = await pg.evaluate("[document.documentElement.scrollWidth, innerWidth]")
        c.ok(w[0] <= w[1] + 1, f'Today at 390 with the card: no sideways scroll ({w})')
        await pg.screenshot(path=os.path.join(OUT, 'phone_today_coord.png'))
        await b.close()

        # ---------------------------------------------------------------- no Meeting Mode: by the ID said, then the words
        b, pg, errs5 = await open_app(p)
        await setup(pg, 'u_chen')
        await pg.evaluate("(m => { delete m.screenLog; m.changes = []; })(DB.meetings.find(m => m.id === 'mt_live'))")
        await pg.evaluate(INGEST, [DOC, NAME])
        await pg.evaluate("mrvRun(DB.meetings.find(m => m.id === 'mt_live'))")
        R = await review(pg)
        st = [x for x in R['P'] if x['kind'] == 'tkdone' and x['ref'] == 'STA-22']
        c.ok(st and st[0]['status'] == 'board', f'with no screen log a done task is still not proposed again (already done on the board): {st}')
        unm = [x for x in R['P'] if x['kind'] == 'tkdate' and x['status'] == 'proposed']
        c.ok(all(x['how'] in ('id', 'words') or 'task' in x['needs'] for x in unm), f'with no screen log, an update finds its task by ID or words, or waits for one to be picked: {[(x["ref"], x["how"], x["needs"]) for x in unm]}')
        c.ok(not any(x['projectId'] == '' and x['status'] == 'applied' for x in R['P']), 'nothing is filed under no project')
        await b.close()

        allerrs = [e for e in errs + errs2 + errs3 + errs4 + errs5 if 'favicon' not in e]
        c.ok(not allerrs, f'no errors: {allerrs[:3]}')
    return c.done()

sys.exit(asyncio.run(main()))
