"""asana_import_test: the Asana board comes in once, from Asana's CSV export, with nothing lost (TASKS_PLAN §2 Phase 1 item 2).

The export is invented (tests/asana_invented/: Asana's exact columns, invented people, jobs and vendors; the firm's real
export never enters the repo). Three per-project files: a job whose tasks carry IDs in their names (PAD-21), an office
project whose IDs sit in a custom field (Ref: OPS-12), and a job with no IDs at all; a task in two projects, subtasks,
a subtask whose parent was not exported, notes with commas, quotes and a line break, finished rows, assignees outside
the team (a vendor on file, someone on file nowhere) and a row with no assignee. Then the team board's own export (one
file: PROJECT NAME names the job, a second Task ID column carries the code, rows with no job are the firm's own lists).

It proves, on the task record lane A merged (code, assignee as the one internal owner, waitingOn, thread):
the dry run's counts tie to the rows read; each project gets its prefix; IDs are kept in `code`, numbered in order where
there are none, never twice; sections give order and section; the owner is the assignee, matched by email or the exact
full name; an assignee who is not on the team (a vendor, someone on file nowhere, a first name alone) or nobody waits on
the screen for an owner, never given to the board's lead (Alan, 10-26), and a vendor stays Waiting On once an owner is
picked; notes are the first comment; finished rows are done with their date; subtasks are checklist steps; nothing
lands in a "General" project; a row with no project waits on the screen and is named on Tasks; a second import updates
and never duplicates, and keeps what was changed in the app; a task the older board import made (same code) is matched,
not doubled; the screen (desktop and phone 390, the owner and the coordinator) shows the summary before anything is
written, with one blue button; nothing from the export reaches the console.

Then the team board's weekly check-in export (tests/asana_invented/board/, invented, the real board's shape: header
names with trailing spaces, Asana's Task ID and the team's own, GENERAL NOTES, PROJECT NAME, NEW?CARRIED, PRIORITY). The
first dry run of the real board scrambled it (10-26); each of the six is reproduced here: keys kept exactly as written
(ELM-02 never ELM-2, a numeric series 301-01 never a made-up prefix, a key mentioned in the notes never the task's, a
row with no key gets the next in its project's series, padded); two series in one project and a series firm-wide (FIN
on a job and on the Office list), a true duplicate refused; owners by email or exact full name, never a first name
(Leo Fontaine is not Leo Marchetti), an assignee with no member waits by name and can be added to the team; PROJECT
NAME is the project, its spellings one, "General" and the meeting-notes section the Office list; every field kept
(dates, both notes, priority, NEW or CARRIED, dependencies, the Asana id); re-import changes nothing, a newer export
updates what changed; the plan screen says all of it before anything is written.
Run: python3 asana_import_test.py"""
import asyncio, json, os, re, sys
from harness import *
H = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(H, 'asana_invented')
FILES = [{'name': f, 'text': open(os.path.join(D, f), encoding='utf-8').read()} for f in sorted(os.listdir(D)) if f.endswith('.csv')]
BOARD = open(os.path.join(D, 'board', 'weekly_checkins.csv'), encoding='utf-8').read()
HEAD = 'Task ID,Created At,Completed At,Last Modified,Name,Section/Column,Assignee,Assignee Email,Start Date,Due Date,Tags,Notes,Projects,Parent task,Blocked By (Dependencies),Blocking (Dependencies)'

SETUP = """() => {
  DB.users.push({id: 'u_dana', name: 'Dana Whitfield', role: 'owner', contact: 'dana@example.com'},
                {id: 'u_priya', name: 'Priya Natarajan', role: 'coord', contact: 'priya@example.com'},
                {id: 'u_leo', name: 'Leo Marchetti', role: 'billing', contact: 'leo@example.com'});
  DB.vendors.push({id: 'v_bay', name: 'Bayside Millwork', email: 'orders@bayside.example'});
  save(); return true; }"""
TASKS = """() => { const out = {}; tkKeyedRecs().forEach(r => { const a = r.rec; if (a.asana) out[a.code] = Object.assign({}, a, {projectName: r.p ? r.p.project.name : '', board: r.board, sched: r.p ? (r.p.tasks || []).length : 0}); }); return out; }"""

async def main():
    c = Checks()
    async with async_playwright() as p:
        b, pg, errs = await open_app(p)
        logs = []
        pg.on('console', lambda m: logs.append(m.text))
        await sign_in(pg, 'u_owner')
        await pg.evaluate(SETUP)
        projects0 = await pg.evaluate("DB.projects.length")
        lead = await pg.evaluate("tdyLeadOf({kind: 'action', projectId: ''}).name")
        # ---- the dry run: nothing written, the counts tie
        P = await pg.evaluate("files => { const before = JSON.stringify([DB.projects, DB.tasks]); const P = aimPlan(files); return Object.assign(P, {untouched: before === JSON.stringify([DB.projects, DB.tasks])}); }", FILES)
        T = P['totals']
        c.ok(P['untouched'], 'the dry run writes nothing')
        c.ok(not P['errors'], f"the three files read as Asana exports: {P['errors']}")
        tie = T['tasks'] + T['steps'] + T['review'] + T['orphans'] + T['duplicates']
        c.ok(T['rows'] == 17 and tie == T['rows'], f'the counts tie: {T["tasks"]} tasks + {T["steps"]} steps + {T["review"]} waiting + {T["orphans"]} orphan + {T["duplicates"]} repeated = {tie} of {T["rows"]}')
        c.ok((T['tasks'], T['create'], T['done'], T['flagged'], T['steps'], T['review'], T['orphans'], T['duplicates'], T['newProjects']) == (8, 8, 1, 0, 2, 5, 1, 1, 3), f'the summary: {T}')
        PR = {x['name']: x for x in P['projects']}
        c.ok(set(PR) == {'PAD - Pine Ave Duplex', 'Operations', 'Hollis Kitchen Renovation'}, f'three projects: {sorted(PR)}')
        c.ok((PR['PAD - Pine Ave Duplex']['prefix'], PR['Operations']['prefix'], PR['Hollis Kitchen Renovation']['prefix']) == ('PAD', 'OPS', 'HKR'),
             f"prefixes from the IDs in the names, in a custom field, from the name: {[(k, v['prefix']) for k, v in PR.items()]}")
        c.ok([(PR[k]['create'], PR[k]['waiting'], PR[k]['sub']) for k in ('PAD - Pine Ave Duplex', 'Operations', 'Hollis Kitchen Renovation')] == [(4, 3, 2), (2, 2, 0), (2, 0, 0)], f'counts per project: {[(k, v["create"], v["waiting"], v["sub"]) for k, v in PR.items()]}')
        PE = {x['name']: x for x in P['people']}
        c.ok(PE['Priya Natarajan']['owner'] == 3 and PE['Dana Whitfield']['owner'] == 2 and PE['Leo Marchetti']['owner'] == 3, f'counts per person: {P["people"]}')
        c.ok(PE['Bayside Millwork']['waiting'] == 1 and PE['Bayside Millwork']['waitingOn'] == 1 and PE['Rita Okafor']['waiting'] == 1 and PE['Former Staffer']['waiting'] == 1 and PE['Nobody']['waiting'] == 1 and PE['Dana']['waiting'] == 1,
             f'who waits for an owner: the vendor (Waiting On), the outsider, the former staffer, nobody, a first name alone: {P["people"]}')
        c.ok(not PE['Dana'].get('here'), 'a first name alone ("Dana") is never a team member, even when one person carries it')
        codes = sorted(t['code'] for t in P['tasks'] + P['review'])
        c.ok(codes == sorted(['PAD-21', 'PAD-22', 'PAD-23', 'PAD-24', 'PAD-25', 'PAD-26', 'PAD-27', 'OPS-12', 'OPS-13', 'OPS-14', 'OPS-15', 'HKR-1', 'HKR-2']), f'IDs kept and numbered in order, never twice: {codes}')
        RV = {t['code']: t for t in P['review']}
        c.ok(set(RV) == {'PAD-23', 'PAD-25', 'PAD-26', 'OPS-14', 'OPS-15'} and all(not t.get('ownerName') for t in RV.values()), f'five rows wait for an owner, none given to anyone: {sorted(RV)}')
        c.ok('outside the team' in RV['PAD-23']['why'] and (RV['PAD-23'].get('waitingOn') or {}).get('id') == 'v_bay', f"the vendor is named and stays Waiting On: {RV['PAD-23']['why']}")
        c.ok('Dana' in RV['OPS-15']['why'] and 'not on the team' in RV['OPS-15']['why'], f"the first name is named as not on the team: {RV['OPS-15']['why']}")
        # ---- the import
        r = await pg.evaluate("files => aimApply(aimPlan(files), {})", FILES)
        c.ok(r['created'] == 8 and r['flagged'] == 0 and r['waiting'] == 5 and r['projects'] == 3, f'eight tasks and three projects written, five waiting for an owner: {r}')
        t = await pg.evaluate(TASKS)
        c.ok(len(t) == 8, f'eight tasks with their Asana id, by code: {sorted(t)}')
        c.ok(not any(x.get('ownerFlag') for x in t.values()) and all(x.get('assignee') in ('Priya Natarajan', 'Dana Whitfield', 'Leo Marchetti') for x in t.values()), f'each task is its assignee\'s, nobody is given one: {[(k, x.get("assignee")) for k, x in t.items()]}')
        a = t.get('PAD-21', {})
        c.ok(a.get('title') == 'Confirm tile layout with client' and a.get('assignee') == 'Priya Natarajan' and not a.get('ownerFlag'), f'PAD-21: the title without its ID, Priya the owner: {a.get("title")} {a.get("assignee")}')
        c.ok(a.get('section') == 'Design' and a.get('order') == 1 and a.get('due') == '2026-10-27' and a.get('status') == 'todo' and a.get('code') == 'PAD-21', f"section, order, due, status: {[a.get(k) for k in ('section', 'order', 'due', 'status')]}")
        cm = (a.get('thread') or [{}])[0]
        c.ok(cm.get('text') == 'Client wants the herringbone, "not" the straight lay.\nCheck the grout color with her.' and cm.get('by') == 'Asana' and cm.get('id'), f'the notes are the first comment, with an id; commas, quotes and line break intact: {cm}')
        ck = a.get('checklist') or []
        c.ok(len(ck) == 2 and [x['done'] for x in ck] == [False, True] and ck[0]['t'].startswith('Pick grout color'), f'the two subtasks are checklist steps, one ticked: {ck}')
        c.ok(a.get('tags') == ['client'] and (a.get('custom') or {}).get('Priority') == 'High', f"tags and the custom field kept: {a.get('tags')} {a.get('custom')}")
        d = t.get('PAD-24', {})
        c.ok(d.get('status') == 'done' and d.get('completedAt') == '2026-10-15', f'a finished row is done, with its date: {d.get("status")} {d.get("completedAt")}')
        h2 = t.get('HKR-2', {})
        c.ok(h2.get('status') == 'doing' and h2.get('blockedBy') == ['HKR-1'] and (h2.get('asana') or {}).get('blockedBy') == ['1401'], f'"In Progress" reads as Doing; the dependency is kept by its key here (the Asana id kept too): {h2.get("status")} {h2.get("blockedBy")}')
        c.ok(t.get('HKR-1', {}).get('start') == '2026-10-26', 'the start date is kept')
        c.ok('OPS-15' not in t and t.get('OPS-13', {}).get('assignee') == 'Dana Whitfield', 'the exact full name with no email is that person; a first name alone waits')
        c.ok(t.get('OPS-12', {}).get('assignee') == 'Leo Marchetti' and t.get('OPS-12', {}).get('due') == '2026-11-05', "the ID from the custom field is the task's code")
        c.ok('PAD-23' not in t and 'PAD-26' not in t and 'OPS-14' not in t, 'the vendor, nobody and the former staffer are not tasks until an owner is picked')
        pend = await pg.evaluate("DB.asanaImport.pending.map(x => x.code).sort()")
        c.ok(pend == ['OPS-14', 'OPS-15', 'PAD-23', 'PAD-25', 'PAD-26'], f'they wait on the screen with their keys: {pend}')
        # the owner picks Priya for the vendor's row: Priya owns it, the vendor is Waiting On, linked, with the date
        w = await pg.evaluate("() => { const r = aimResolve('1203', 'u_priya'); return r && JSON.parse(JSON.stringify(r.a)); }")
        wo = (w or {}).get('waitingOn') or {}
        c.ok(w and w.get('assignee') == 'Priya Natarajan' and w.get('code') == 'PAD-23' and not w.get('ownerFlag'), f"the picked owner owns it, keeping its key: {w and (w.get('assignee'), w.get('code'))}")
        c.ok(wo.get('name') == 'Bayside Millwork' and (wo.get('contactRef') or {}).get('id') == 'v_bay' and wo.get('promised') == '2026-10-29' and w.get('status') == 'waiting', f'and the vendor is Waiting On, linked to the vendor on file, with the date: {wo} {w and w.get("status")}')
        c.ok(any('Asana named Bayside Millwork' in (x.get('text') or '') for x in (w or {}).get('thread') or []), 'the task says who Asana named')
        o14 = await pg.evaluate("() => { const r = aimResolve('1303', 'u_dana'); return r && {status: r.a.status, at: r.a.completedAt, who: r.a.assignee}; }")
        c.ok(o14 == {'status': 'done', 'at': '2026-10-01', 'who': 'Dana Whitfield'}, f'a finished row given an owner is done, with its date: {o14}')
        t = await pg.evaluate(TASKS)
        c.ok(all(x.get('projectName') != 'General' for x in t.values()) and await pg.evaluate("!DB.projects.some(p => /^general$/i.test(p.project.name))"), 'nothing goes to "General"')
        pj = await pg.evaluate("() => DB.projects.filter(p => p.project.asanaName).map(p => ({name: p.project.name, prefix: p.project.prefix, next: p.project.keyNext, sched: p.tasks.length, today: p.project.today}))")
        c.ok(len(pj) == 3 and all(x['sched'] == 0 and x['today'] == '' for x in pj), f'each project is a project here, no schedule invented, no pinned day: {pj}')
        pad = next((x for x in pj if x['prefix'] == 'PAD'), {})
        c.ok(pad.get('next') == 28, f"the board's next number follows the import (PAD-28), so a task added in the meeting never reuses one: {pad}")
        c.ok(await pg.evaluate("DB.projects.length") == projects0 + 3, 'three projects added, none twice')
        bc = await pg.evaluate("() => ['PAD-21', 'OPS-12', 'HKR-2'].map(k => { const r = tkByCode(k); return r && r.rec.title; })")
        c.ok(all(bc), f'Meeting Mode finds each by its code (tkByCode): {bc}')
        # ---- a second import of the same files: nothing duplicated
        P2 = await pg.evaluate("files => aimPlan(files).totals", FILES)
        c.ok(P2['create'] == 0 and P2['same'] == 10 and P2['update'] == 0 and P2['review'] == 3, f'the same export again: nothing new, ten unchanged, the three still waiting: {P2}')
        pc = await pg.evaluate("files => aimPlan(files).review.map(t => t.code).sort()", FILES)
        c.ok(pc == ['OPS-15', 'PAD-25', 'PAD-26'], f'a row with no key keeps the key it was given while it waits: {pc}')
        r2 = await pg.evaluate("files => aimApply(aimPlan(files), {})", FILES)
        t2 = await pg.evaluate(TASKS)
        c.ok(r2['created'] == 0 and len(t2) == 10 and r2['waiting'] == 3, f'a second import adds no task and no waiting row: {r2} {len(t2)}')
        c.ok(len([x for x in t2['PAD-21']['thread'] if x.get('text')]) == 1 and len(t2['PAD-21']['checklist']) == 2, 'no comment or step twice')
        c.ok(await pg.evaluate("DB.projects.length") == projects0 + 3, 'no project twice')
        # ---- a newer export: Asana's changes come in; what the meeting changed in the app stays
        await pg.evaluate("() => { tkByCode('PAD-22').rec.due = '2026-10-26'; save(); }")
        newer = [dict(f) for f in FILES]
        pf = next(f for f in newer if f['name'] == 'pad_pine_ave.csv')
        pf['text'] = (pf['text']
            .replace('1202,2026-09-29,,2026-10-21,PAD-22 Release deposit to fabricator,Money,Dana Whitfield,dana@example.com,,2026-10-23',
                     '1202,2026-09-29,,2026-10-24,PAD-22 Release deposit to the fabricator,Money,Dana Whitfield,dana@example.com,,2026-10-30')
            .replace('1201,2026-09-28,,2026-10-20,PAD-21 Confirm tile layout with client,Design,Priya Natarajan,priya@example.com,,2026-10-27',
                     '1201,2026-09-28,,2026-10-24,PAD-21 Confirm tile layout with client,Design,Priya Natarajan,priya@example.com,,2026-10-29')
            .replace('1206,2026-10-03,,2026-10-22,Measure for shower glass', '1206,2026-10-03,2026-10-24,2026-10-24,Measure for shower glass'))
        P3 = await pg.evaluate("files => aimPlan(files).totals", newer)
        c.ok(P3['update'] == 3 and P3['create'] == 0, f'three tasks changed in Asana: {P3}')
        await pg.evaluate("files => aimApply(aimPlan(files), {})", newer)
        t3 = await pg.evaluate(TASKS)
        c.ok(t3['PAD-22']['due'] == '2026-10-26' and t3['PAD-22']['title'] == 'Release deposit to the fabricator', f"PAD-22: the date moved in the app is kept, the new title comes in: {t3['PAD-22']['due']} {t3['PAD-22']['title']}")
        c.ok(t3['PAD-21']['due'] == '2026-10-29', 'PAD-21: the date moved in Asana comes in')
        c.ok(t3['PAD-27']['status'] == 'done' and t3['PAD-27']['completedAt'] == '2026-10-24', 'PAD-27: finished in Asana, done here with its date')
        c.ok(len(t3) == 10, 'still ten tasks')
        # ---- IDs never twice: a hand-made task already holds HKR-3
        k = await pg.evaluate("""head => { const p = DB.projects.find(p => p.project.prefix === 'HKR'); p.actions.push({id: 'a_hand', code: 'HKR-3', title: 'Made by hand', assignee: 'Priya Natarajan', status: 'todo', createdAt: '2026-10-20'});
          const f = head + '\\n1403,2026-10-12,,2026-10-22,Order the hood,To Do,Priya Natarajan,priya@example.com,,,,,Hollis Kitchen Renovation,,,\\n1404,2026-10-12,,2026-10-22,HKR-3 Tile backsplash,To Do,Priya Natarajan,priya@example.com,,,,,Hollis Kitchen Renovation,,,\\n';
          const P = aimPlan([{name: 'hollis2.csv', text: f}]); return P.tasks.concat(P.review).map(t => [t.asanaId, t.code, t.refused || '']); }""", HEAD)
        km = {x[0]: x for x in k}
        c.ok(km['1403'][1] == 'HKR-4' and km['1404'][1] == 'HKR-3' and km['1404'][2] == 'duplicate', f'a new row takes the next free number; a row naming a key another task holds is refused, never renumbered: {k}')
        # ---- the team board's own export: PROJECT NAME and the code column; the rest on the firm's own lists
        board = ('Task ID,Created At,Completed At,Last Modified,Name,Section/Column,Assignee,Assignee Email,Start Date,Due Date,Tags,Notes,Projects,Parent task,Blocked By (Dependencies),Blocking (Dependencies),GENERAL NOTES,PROJECT NAME,Task ID,NEW?CARRIED,PRIORITY\n'
                 '2001,2026-10-01,,2026-10-22,Window sample to the client,121 State,Priya Natarajan,priya@example.com,,2026-10-28,,,Team Board,,,,,121 State,STA-7,CARRIED,P1\n'
                 '2002,2026-10-01,,2026-10-22,Renew the auto policy,Finance & Admin,Leo Marchetti,leo@example.com,,2026-11-01,,,Team Board,,,,,,FA-3,NEW,P2\n')
        bp = await pg.evaluate("text => { const P = aimPlan([{name: 'board.csv', text}]); return {tasks: P.tasks.map(t => [t.code, t.project, t.firm]), proj: P.projects.map(x => [x.name, x.firm, x.projectId, x.prefix]), T: P.totals}; }", board)
        c.ok(sorted(bp['tasks']) == [['FA-3', 'Finance & Admin', True], ['STA-7', '121 State', False]], f"the board export: the job by PROJECT NAME, the rest on the firm's list by section, codes from the second Task ID column: {bp['tasks']}")
        c.ok(any(x[0] == '121 State' and x[2] == 'p121' for x in bp['proj']), f"'121 State' is the job 121 State Street (one job, two names): {bp['proj']}")
        await pg.evaluate("text => aimApply(aimPlan([{name: 'board.csv', text}]), {})", board)
        fa = await pg.evaluate("() => { const r = tkByCode('FA-3'); return r && {board: r.board, section: r.rec.section, kind: r.kind}; }")
        c.ok(fa == {'board': 's:Finance & Admin', 'section': 'Finance & Admin', 'kind': 'firm'}, f"FA-3 is on the firm's Finance & Admin list: {fa}")
        c.ok(await pg.evaluate("(DB.company.tkBoards['s:Finance & Admin'] || {}).prefix") == 'FA', "and that list's prefix is FA")
        # a task the older one-step board import made (code, no Asana id) is matched by its code, not doubled
        old = await pg.evaluate("""text => { const p = DB.projects.find(p => p.id === 'p121'); p.actions.push({id: 'a_old', code: 'STA-9', title: 'Old import row', assignee: 'Priya Natarajan', status: 'todo', source: {asana: true}});
          const f = text.split('\\n')[0] + '\\n2009,2026-10-01,,2026-10-22,Old import row,121 State,Priya Natarajan,,,2026-11-03,,,Team Board,,,,,121 State,STA-9,,\\n';
          const r = aimApply(aimPlan([{name: 'board2.csv', text: f}]), {}); return {r, n: p.actions.filter(a => a.code === 'STA-9').length, id: (p.actions.find(a => a.code === 'STA-9').asana || {}).id}; }""", board)
        c.ok(old['n'] == 1 and old['r']['created'] == 0 and old['id'] == '2009', f'a task from the older board import is matched by its code and brought under this one: {old}')
        # ---- a row with no project waits on the screen, never in "General"
        rv = await pg.evaluate("""head => { const f = head + '\\n3001,2026-10-12,,2026-10-22,No project row,,Priya Natarajan,priya@example.com,,,,,,,,\\n3002,2026-10-12,,2026-10-22,Row A,,Priya Natarajan,,,,,,Alpha,,,\\n3003,2026-10-12,,2026-10-22,Row B,,Priya Natarajan,,,,,,Beta,,,\\n';
          const r = aimApply(aimPlan([{name: 'mixed.csv', text: f}]), {}); return {r, pending: DB.asanaImport.pending.map(x => [x.asanaId, x.why])}; }""", HEAD)
        np = [x for x in rv['pending'] if x[0] == '3001']
        c.ok(rv['r']['created'] == 2 and np and 'no project' in np[0][1], f'a row naming no project (its file holds two) waits on the screen: {rv}')
        # ---- not an Asana export
        e = await pg.evaluate("() => { const n = DB.projects.length; const P = aimPlan([{name: 'contacts.csv', text: 'Name,Email\\nA,b@c.d\\n'}]); return {err: P.errors, tasks: P.tasks.length, same: n === DB.projects.length}; }")
        c.ok(e['err'] and 'not an Asana export' in e['err'][0] and e['tasks'] == 0 and e['same'], f'another CSV is refused by name, nothing read: {e}')
        c.ok(not any(re.search(r'herringbone|Bayside|Rita Okafor|fabricator', l) for l in logs), 'nothing from the export reaches the console')
        c.ok(not errs, f'no page errors: {errs[:3]}')
        await b.close()

        # ---- the screen: the owner on desktop and phone, then the coordinator from Tasks
        for who, phone in (('u_owner', False), ('u_owner', True), ('u_chen', True)):
            b, pg, errs = await open_app(p, phone=phone)
            await sign_in(pg, who)
            await pg.evaluate(SETUP)
            await go(pg, 'tkall')
            imp = pg.locator('#v-tkall #tk-import')
            if await imp.count() and await imp.is_visible():
                await imp.click()
            else:
                await go(pg, 'rdata')
            await pg.wait_for_timeout(300)
            tag = f'{who} {"phone" if phone else "desktop"}'
            c.ok(await pg.evaluate("view") == 'rdata' and await pg.locator('#aim-card').count() == 1, f'Import the Board opens the one import ({tag})')
            if who == 'u_chen':
                c.ok(await pg.locator('#rd-wipe-all, #rd-sample, #rd-backup2').count() == 0, 'the coordinator sees the import and none of the owner\'s clear or backup buttons')
            await pg.set_input_files('#aim-file', [os.path.join(D, f['name']) for f in FILES])
            await pg.wait_for_selector('#aim-tie', timeout=10000)
            tie = await pg.inner_text('#aim-tie')
            c.ok('17 rows read' in tie and 'Nothing is lost' in tie and '5 waiting on this screen (5 for an owner)' in tie, f'the summary ties before anything is written ({tag}): {tie}')
            c.ok(await pg.evaluate("!DB.projects.some(p => p.project.asanaName)"), 'and nothing is written yet')
            c.ok(await pg.locator('#aim-projects tbody tr').count() == 3 and await pg.locator('#aim-people tbody tr').count() >= 6, 'counts per project and per person')
            prim = await pg.evaluate("[...document.querySelectorAll('#v-rdata .btn.primary')].filter(b => b.offsetParent).length")
            c.ok(prim == 1, f'one blue button on the screen: {prim}')
            sw = await pg.evaluate("document.documentElement.scrollWidth - innerWidth")
            c.ok(sw <= 0, f'no sideways scroll ({sw}px)')
            os.makedirs(os.path.join(ROOT, 'review', 'laneD'), exist_ok=True)
            await pg.screenshot(path=os.path.join(ROOT, 'review', 'laneD', f'asana_summary_{who}_{"phone" if phone else "desktop"}.png'), full_page=True)
            await pg.click('#aim-go')
            await pg.wait_for_timeout(300)
            toast = await pg.inner_text('#toast')
            c.ok('8 new tasks' in toast and '5 wait on Your Own Data for an owner' in toast, f'the import toasts what happened: {toast}')
            c.ok(await pg.locator('#toast .toast-open').count() == 1, 'with an Open link')
            c.ok(await pg.evaluate("tkKeyedRecs().filter(r => r.rec.asana).length") == 8, 'eight tasks written')
            c.ok(not errs, f'no page errors ({tag}): {errs[:3]}')
            await b.close()
        # ==== the team board's weekly check-in export: the six ways the first real dry run scrambled it (10-26) ====
        b, pg, errs = await open_app(p)
        logs = []
        pg.on('console', lambda m: logs.append(m.text))
        await sign_in(pg, 'u_owner')
        await pg.evaluate(SETUP)
        BP = await pg.evaluate("""text => { const before = JSON.stringify([DB.projects, DB.tasks, DB.users]); const P = aimPlan([{name: 'weekly_checkins.csv', text}]);
          const row = t => ({id: t.asanaId, code: t.code, key: t.keyFound, title: t.title, project: t.project, firm: t.firm, owner: t.ownerName, how: t.ownerHow, why: t.why || '', refused: t.refused || '', due: t.row.due,
                             blockedBy: t.blockedBy, blocking: t.blocking, made: !!t.made, steps: t.checklist.length});
          return {T: P.totals, rows: P.tasks.map(row), review: P.review.map(row), proj: P.projects.map(x => ({name: x.name, prefix: x.prefix, firm: x.firm, kept: x.kept, waiting: x.waiting})),
                  people: P.people, untouched: before === JSON.stringify([DB.projects, DB.tasks, DB.users])}; }""", BOARD)
        BT = BP['T']
        R = {x['id']: x for x in BP['rows'] + BP['review']}
        c.ok(BP['untouched'] and BT['rows'] == 12 and BT['tasks'] + BT['steps'] + BT['review'] + BT['orphans'] + BT['duplicates'] == 12, f'board: the dry run writes nothing and ties: {BT}')
        # 1. keys exactly as written: zero padding, a numeric series, never a key mentioned in the notes; a row with
        # none gets the next in its project's series, padded like its neighbours
        c.ok(R['5001']['code'] == 'ELM-02' and R['5002']['code'] == 'ELM-03' and R['5008']['code'] == 'FIN-12', f"zero padding kept: {[R[i]['code'] for i in ('5001', '5002', '5008')]}")
        c.ok(R['5004']['code'] == '301-01' and R['5005']['code'] == '301-02', f"a numeric series keeps its key: {R['5004']['code']} {R['5005']['code']}")
        c.ok(R['5007']['code'] == 'FIN-11', f"the Task ID column is the key, never the OPS-05 its notes mention: {R['5007']['code']}")
        c.ok(R['5003']['code'] == 'ELM-04' and R['5003']['made'] and BT['keysMade'] == 1, f"the row with no key takes the next in its project's series, padded: {R['5003']['code']}")
        c.ok(BT['keysKept'] == 9 and all(x['code'] == x['key'] for x in BP['rows'] + BP['review'] if x['key']), f"every key kept exactly: {BT['keysKept']}")
        c.ok(R['5001']['title'] == 'Confirm the stair runner sample' and R['5007']['title'] == 'Reconcile the supplier credit', f"the title without its own key: {R['5001']['title']}")
        # 2. several series in one project, a series firm-wide, a true duplicate refused
        PJ = {x['name']: x for x in BP['proj']}
        c.ok(set(PJ) == {'12 Elm St', '301 Oak Ave', 'Office'}, f'three projects: {sorted(PJ)}')
        c.ok(PJ['12 Elm St']['prefix'] == 'ELM' and PJ['301 Oak Ave']['prefix'] == '301' and PJ['Office']['prefix'] == 'OPS', f"each project's own series is its prefix; FIN, on a job and the Office list, is nobody's: {[(k, v['prefix']) for k, v in PJ.items()]}")
        c.ok(R['5008']['project'] == '12 Elm St' and R['5007']['project'] == 'Office', 'a FIN key sits on the job and on the Office list')
        c.ok(R['5010']['refused'] == 'duplicate' and 'ELM-03' in R['5010']['why'] and BT['refused'] == 1, f"a second row with ELM-03 is refused to the review list: {R['5010']['why']}")
        # 3. owners: by email (the Asana name differs), by exact full name, never a first name, never someone else
        c.ok(R['5002']['owner'] == 'Priya Natarajan' and R['5002']['how'] == 'email', f"by email though Asana spells her name otherwise: {R['5002']['owner']} {R['5002']['how']}")
        c.ok(R['5004']['owner'] == 'Dana Whitfield' and R['5006']['owner'] == 'Leo Marchetti', 'each assignee owns their own')
        c.ok(not R['5009']['owner'] and 'Leo Fontaine' in R['5009']['why'], f"Leo Fontaine is not Leo Marchetti: he waits for an owner: {R['5009']['owner']!r} {R['5009']['why']}")
        c.ok(not R['5005']['owner'] and not R['5007']['owner'] and 'Marisol Vega' in R['5005']['why'], 'an assignee with no member waits, by name, never given to the owner')
        PE = {x['name']: x for x in BP['people']}
        c.ok(PE['Marisol Vega']['waiting'] == 2 and not PE['Marisol Vega']['here'] and PE['Leo Fontaine']['waiting'] == 1 and BT['waitingOwner'] == 3, f'the plan names who is unmatched and how many rows: {BP["people"]}')
        c.ok(BT['byEmail'] == 7 and BT['byName'] == 0, f"seven owners matched by email: {BT['byEmail']} {BT['byName']}")
        # 4. PROJECT NAME is the project, one however spelled; "General" and the meeting-notes section are the Office list
        c.ok(all(R[i]['project'] == '12 Elm St' for i in ('5001', '5002', '5003', '5008', '5010')), f"'12 Elm St ', '12 elm  st' and '12 ELM St' are one project: {[R[i]['project'] for i in ('5001', '5002', '5003')]}")
        c.ok(R['5006']['firm'] and R['5006']['project'] == 'Office' and R['5009']['project'] == 'Office' and PJ['Office']['firm'], '"General" and the meeting-notes section are the firm\'s Office list, not a job')
        # 5. every field: dependencies as the keys here, the subtask a step, the due dates
        c.ok(R['5002']['blockedBy'] == ['ELM-02'] and R['5001']['blocking'] == ['ELM-03'], f"dependencies by the keys here: {R['5002']['blockedBy']} {R['5001']['blocking']}")
        c.ok(R['5001']['steps'] == 1 and BT['steps'] == 1, 'the subtask with no key is a checklist step on its parent')
        c.ok(BT['due'] == 10 and BT['noDue'] == 1, f"due dates: {BT['due']} kept, {BT['noDue']} with none")
        # ---- written
        ra = await pg.evaluate("text => aimApply(aimPlan([{name: 'weekly_checkins.csv', text}]), {})", BOARD)
        c.ok(ra['created'] == 7 and ra['waiting'] == 4 and ra['refused'] == 1 and ra['projects'] == 2, f'board: seven tasks, two new jobs (the Office list is the firm\'s), four waiting, one refused: {ra}')
        W = await pg.evaluate("""() => { const o = {}; tkKeyedRecs().forEach(r => { const a = r.rec; if (a.asana && /^50/.test(a.asana.id)) o[a.code] = JSON.parse(JSON.stringify(Object.assign({}, a, {board: r.board, prefix: (tkBoardMeta(r.board) || {}).prefix}))); }); return o; }""")
        e2 = W.get('ELM-02', {})
        c.ok(sorted(W) == sorted(['ELM-02', 'ELM-03', 'ELM-04', '301-01', 'OPS-07', 'FIN-12', 'FIN-13']), f'the keys written are the team\'s: {sorted(W)}')
        c.ok(e2.get('priority') == 'high' and e2.get('pri3') == 'P1' and e2.get('carried') == 'CARRIED' and e2.get('start') == '2026-10-20' and e2.get('due') == '2026-10-27' and e2.get('tags') == ['client'],
             f"priority, NEW or CARRIED, dates and tags kept: {[e2.get(k) for k in ('priority', 'pri3', 'carried', 'start', 'due', 'tags')]}")
        th = [x.get('text') for x in e2.get('thread') or []]
        c.ok(th == ['Asked the client twice for the sample.', 'General notes: Client prefers wool.'] and e2.get('generalNotes') == 'Client prefers wool.', f'both notes are comments, the general notes kept: {th}')
        c.ok((e2.get('asana') or {}).get('id') == '5001' and e2.get('blocking') == ['ELM-03'] and W.get('ELM-03', {}).get('blockedBy') == ['ELM-02'] and len(e2.get('checklist') or []) == 1, 'the Asana id, the dependencies and the step are on the tasks')
        c.ok(W.get('FIN-13', {}).get('status') == 'done' and W['FIN-13'].get('completedAt') == '2026-10-20' and W['FIN-13'].get('board') == 's:Office', f"a finished row is done with its date, on the Office list: {W.get('FIN-13', {}).get('status')} {W.get('FIN-13', {}).get('board')}")
        c.ok(W.get('FIN-12', {}).get('prefix') == 'ELM' and W.get('301-01', {}).get('prefix') == '301', f"the jobs' prefixes are their own series: {W.get('FIN-12', {}).get('prefix')} {W.get('301-01', {}).get('prefix')}")
        nk = await pg.evaluate("() => { const e = tkByCode('ELM-02'), o = tkByCode('301-01'); return {elm: tkNextKey(e.board), oak: tkNextKey(o.board), aloud: (tkByCode('ELM-2') || {}).rec && tkByCode('ELM-2').rec.code}; }")
        c.ok(nk == {'elm': 'ELM-05', 'oak': '301-03', 'aloud': 'ELM-02'}, f"a task added in the meeting takes the next key, padded, after the waiting ones; ELM-2 finds ELM-02: {nk}")
        sw = await pg.evaluate("() => { tkRecSweep(); return tkKeyedRecs().filter(r => r.rec.asana && /^50/.test(r.rec.asana.id)).map(r => r.rec.code).sort(); }")
        c.ok(sw == sorted(W), f'the sweep changes no imported key: {sw}')
        # ---- re-import the same file: nothing changes; a newer export updates what changed
        snap0 = await pg.evaluate("() => JSON.stringify(tkKeyedRecs().filter(r => r.rec.asana).map(r => [r.rec.code, r.rec.assignee, r.rec.due, r.rec.title, r.rec.priority, (r.rec.thread || []).length]))")
        R2 = await pg.evaluate("text => { const P = aimPlan([{name: 'weekly_checkins.csv', text}]); const r = aimApply(P, {}); return {T: P.totals, r, pend: DB.asanaImport.pending.length}; }", BOARD)
        snap1 = await pg.evaluate("() => JSON.stringify(tkKeyedRecs().filter(r => r.rec.asana).map(r => [r.rec.code, r.rec.assignee, r.rec.due, r.rec.title, r.rec.priority, (r.rec.thread || []).length]))")
        c.ok(R2['T']['same'] == 7 and R2['T']['create'] == 0 and R2['T']['update'] == 0 and R2['pend'] == 4 and snap0 == snap1, f'the same export again changes nothing: {R2}')
        await pg.evaluate("() => { tkByCode('OPS-07').rec.due = '2026-10-30'; save(); }")
        newer = BOARD.replace('2026-10-20,2026-10-27,client,Asked', '2026-10-20,2026-11-02,client,Asked').replace(',General ,OPS-07,CARRIED,P2', ',General ,OPS-07,CARRIED,P1').replace('2026-10-22,OPS-07 Renew the van lease', '2026-10-24,OPS-07 Renew the van lease')
        R3 = await pg.evaluate("text => { const P = aimPlan([{name: 'weekly_checkins.csv', text}]); aimApply(P, {}); const e = tkByCode('ELM-02').rec, o = tkByCode('OPS-07').rec; return {T: P.totals, elm: e.due, ops: [o.due, o.pri3, o.priority]}; }", newer)
        c.ok(R3['T']['update'] == 2 and R3['elm'] == '2026-11-02' and R3['ops'] == ['2026-10-30', 'P1', 'high'], f"a newer export: the due date and priority from Asana come in, the date moved here stays: {R3}")
        # ---- the people not on the team: the owner adds one, and her rows become her tasks
        await go(pg, 'rdata')
        await pg.wait_for_timeout(200)
        grp = pg.locator('[data-aimgrp="marisol@example.com"]')
        c.ok(await grp.count() == 1 and 'not on the team' in await grp.inner_text(), 'the screen names Marisol Vega as not on the team, with her rows')
        c.ok(await pg.locator('[data-aimgrp="leo.f@example.com"] [data-aimadd]').count() == 1 and await pg.locator('[data-aimgrp="refused"] select').count() == 0, 'Leo Fontaine can be added; a refused row has no owner to pick')
        await pg.locator('[data-aimadd="marisol@example.com"]').click()
        await pg.wait_for_timeout(250)
        mv = await pg.evaluate("() => ({u: DB.users.filter(u => u.contact === 'marisol@example.com').map(u => u.name), t: ['301-02', 'FIN-11'].map(k => (tkByCode(k) || {rec: {}}).rec.assignee), pend: DB.asanaImport.pending.map(x => x.code).sort()})")
        c.ok(mv['u'] == ['Marisol Vega'] and mv['t'] == ['Marisol Vega', 'Marisol Vega'] and mv['pend'] == ['ELM-03', 'OPS-08'], f'added to the team: her two rows are her tasks, the rest still wait: {mv}')
        toast = await pg.inner_text('#toast')
        c.ok('Marisol Vega added to the team' in toast and await pg.locator('#toast .toast-open').count() == 1, f'it toasts what happened, with an Open link: {toast}')
        c.ok(not any(re.search(r'stair runner|Marisol|wool', l) for l in logs), 'nothing from the board export reaches the console')
        c.ok(not errs, f'no page errors (board): {errs[:3]}')
        await b.close()
        # ---- the plan screen on the phone: what is kept, matched, unmatched and refused, before anything is written
        for phone in (False, True):
            b, pg, errs = await open_app(p, phone=phone)
            await sign_in(pg, 'u_owner')
            await pg.evaluate(SETUP)
            await go(pg, 'rdata')
            await pg.set_input_files('#aim-file', [os.path.join(D, 'board', 'weekly_checkins.csv')])
            await pg.wait_for_selector('#aim-tie', timeout=10000)
            tag = 'phone' if phone else 'desktop'
            keys, owners, due, refd = [await pg.inner_text(s) for s in ('#aim-keys', '#aim-owners', '#aim-due', '#aim-refused')]
            c.ok('9 kept exactly as written' in keys and 'ELM-04' in keys, f'the plan says the keys kept and made ({tag}): {keys}')
            c.ok('7 matched by email' in owners and 'Marisol Vega' in owners and 'Leo Fontaine' in owners, f'who is matched and who is not ({tag}): {owners}')
            c.ok('10 kept' in due and 'ELM-03' in refd, f'the due dates and the refused row ({tag}): {due} {refd}')
            c.ok(await pg.locator('#aim-rows [data-aimline]').count() == 11, 'every row with its key, owner and due date')
            c.ok(await pg.evaluate("!DB.projects.some(p => p.project.asanaName)"), 'and nothing is written yet')
            prim = await pg.evaluate("[...document.querySelectorAll('#v-rdata .btn.primary')].filter(b => b.offsetParent).length")
            sw = await pg.evaluate("document.documentElement.scrollWidth - innerWidth")
            c.ok(prim == 1 and sw <= 0, f'one blue button, no sideways scroll ({tag}): {prim} {sw}px')
            await pg.screenshot(path=os.path.join(ROOT, 'review', 'laneD', f'asana_board_plan_{tag}.png'), full_page=True)
            c.ok(not errs, f'no page errors ({tag}): {errs[:3]}')
            await b.close()
    return c.done()

sys.exit(asyncio.run(main()))
