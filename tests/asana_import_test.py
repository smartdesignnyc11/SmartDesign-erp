"""asana_import_test: the Asana board comes in once, from Asana's CSV export, with nothing lost (TASKS_PLAN §2 Phase 1 item 2).

The export is invented (tests/asana_invented/: Asana's exact columns, invented people, jobs and vendors; the firm's real
export never enters the repo). Three per-project files: a job whose tasks carry IDs in their names (PAD-21), an office
project whose IDs sit in a custom field (Ref: OPS-12), and a job with no IDs at all; a task in two projects, subtasks,
a subtask whose parent was not exported, notes with commas, quotes and a line break, finished rows, assignees outside
the team (a vendor on file, someone on file nowhere) and a row with no assignee. Then the team board's own export (one
file: PROJECT NAME names the job, a second Task ID column carries the code, rows with no job are the firm's own lists).

It proves, on the task record lane A merged (code, assignee as the one internal owner, ownerFlag, waitingOn, thread):
the dry run's counts tie to the rows read; each project gets its prefix; IDs are kept in `code`, numbered in order where
there are none, never twice; sections give order and section; a team member is the owner; an outside or missing
assignee lands with the board's lead as owner, flagged to confirm, and the outsider Waiting On (linked to the vendor on
file); notes are the first comment; finished rows are done with their date; subtasks are checklist steps; nothing lands
in a "General" project; a row with no project waits on the screen and is named on Tasks; a second import updates and
never duplicates, and keeps what was changed in the app; a task the older board import made (same code) is matched, not
doubled; the screen (desktop and phone 390, the owner and the coordinator) shows the summary before anything is
written, with one blue button; nothing from the export reaches the console.
Run: python3 asana_import_test.py"""
import asyncio, json, os, re, sys
from harness import *
H = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(H, 'asana_invented')
FILES = [{'name': f, 'text': open(os.path.join(D, f), encoding='utf-8').read()} for f in sorted(os.listdir(D)) if f.endswith('.csv')]
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
        c.ok((T['tasks'], T['create'], T['done'], T['flagged'], T['steps'], T['review'], T['orphans'], T['duplicates'], T['newProjects']) == (13, 13, 2, 4, 2, 0, 1, 1, 3), f'the summary: {T}')
        PR = {x['name']: x for x in P['projects']}
        c.ok(set(PR) == {'PAD - Pine Ave Duplex', 'Operations', 'Hollis Kitchen Renovation'}, f'three projects: {sorted(PR)}')
        c.ok((PR['PAD - Pine Ave Duplex']['prefix'], PR['Operations']['prefix'], PR['Hollis Kitchen Renovation']['prefix']) == ('PAD', 'OPS', 'HKR'),
             f"prefixes from the IDs in the names, in a custom field, from the name: {[(k, v['prefix']) for k, v in PR.items()]}")
        c.ok([(PR[k]['create'], PR[k]['flag'], PR[k]['sub']) for k in ('PAD - Pine Ave Duplex', 'Operations', 'Hollis Kitchen Renovation')] == [(7, 3, 2), (4, 1, 0), (2, 0, 0)], f'counts per project: {[(k, v["create"], v["flag"], v["sub"]) for k, v in PR.items()]}')
        PE = {x['name']: x for x in P['people']}
        c.ok(PE['Priya Natarajan']['owner'] == 3 and PE['Dana Whitfield']['owner'] == 3 and PE['Leo Marchetti']['owner'] == 3, f'counts per person: {P["people"]}')
        c.ok(PE['Bayside Millwork']['waitingOn'] == 1 and PE['Rita Okafor']['waitingOn'] == 1 and PE['Former Staffer']['waitingOn'] == 1 and PE['Nobody']['flag'] == 1, f'who is waited on, and the row with nobody: {P["people"]}')
        codes = sorted(t['code'] for t in P['tasks'])
        c.ok(codes == sorted(['PAD-21', 'PAD-22', 'PAD-23', 'PAD-24', 'PAD-25', 'PAD-26', 'PAD-27', 'OPS-12', 'OPS-13', 'OPS-14', 'OPS-15', 'HKR-1', 'HKR-2']), f'IDs kept and numbered in order, never twice: {codes}')
        # ---- the import
        r = await pg.evaluate("files => aimApply(aimPlan(files), {})", FILES)
        c.ok(r['created'] == 13 and r['flagged'] == 4 and r['waiting'] == 0 and r['projects'] == 3, f'thirteen tasks and three projects written, four flagged to confirm: {r}')
        t = await pg.evaluate(TASKS)
        c.ok(len(t) == 13, f'thirteen tasks with their Asana id, by code: {sorted(t)}')
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
        c.ok(h2.get('status') == 'doing' and h2.get('blockedBy') == ['1401'], f'"In Progress" reads as Doing; the dependency is kept: {h2.get("status")} {h2.get("blockedBy")}')
        c.ok(t.get('HKR-1', {}).get('start') == '2026-10-26', 'the start date is kept')
        c.ok(t.get('OPS-15', {}).get('assignee') == 'Dana Whitfield', 'a first name only one team member carries ("Dana") is that person')
        c.ok(t.get('OPS-12', {}).get('assignee') == 'Leo Marchetti' and t.get('OPS-12', {}).get('due') == '2026-11-05', "the ID from the custom field is the task's code")
        w = t.get('PAD-23', {})
        c.ok(w.get('assignee') == lead and (w.get('ownerFlag') or {}).get('why') == 'outside' and w['ownerFlag'].get('was') == 'Bayside Millwork', f"an outside assignee: the board's lead ({lead}) owns it, flagged to confirm: {w.get('assignee')} {w.get('ownerFlag')}")
        wo = w.get('waitingOn') or {}
        c.ok(wo.get('name') == 'Bayside Millwork' and (wo.get('contactRef') or {}).get('id') == 'v_bay' and wo.get('promised') == '2026-10-29' and w.get('status') == 'waiting', f'and the vendor is Waiting On, linked to the vendor on file, with the date: {wo} {w.get("status")}')
        n = t.get('PAD-26', {})
        c.ok(n.get('assignee') == lead and (n.get('ownerFlag') or {}).get('why') == 'none' and not n.get('waitingOn'), f'a row with no assignee: the lead owns it, flagged: {n.get("ownerFlag")}')
        o14 = t.get('OPS-14', {})
        c.ok(o14.get('status') == 'done' and (o14.get('ownerFlag') or {}).get('why') == 'outside', 'a finished row with an outside assignee is done and flagged too')
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
        c.ok(P2['create'] == 0 and P2['same'] == 13 and P2['update'] == 0, f'the same export again: nothing new, thirteen unchanged: {P2}')
        r2 = await pg.evaluate("files => aimApply(aimPlan(files), {})", FILES)
        t2 = await pg.evaluate(TASKS)
        c.ok(r2['created'] == 0 and len(t2) == 13, f'a second import adds no task: {r2} {len(t2)}')
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
        c.ok(len(t3) == 13, 'still thirteen tasks')
        # ---- IDs never twice: a hand-made task already holds HKR-3
        k = await pg.evaluate("""head => { const p = DB.projects.find(p => p.project.prefix === 'HKR'); p.actions.push({id: 'a_hand', code: 'HKR-3', title: 'Made by hand', assignee: 'Priya Natarajan', status: 'todo', createdAt: '2026-10-20'});
          const f = head + '\\n1403,2026-10-12,,2026-10-22,Order the hood,To Do,Priya Natarajan,priya@example.com,,,,,Hollis Kitchen Renovation,,,\\n1404,2026-10-12,,2026-10-22,HKR-3 Tile backsplash,To Do,Priya Natarajan,priya@example.com,,,,,Hollis Kitchen Renovation,,,\\n';
          return aimPlan([{name: 'hollis2.csv', text: f}]).tasks.map(t => [t.asanaId, t.code, t.keyWas || '']); }""", HEAD)
        km = {x[0]: x for x in k}
        c.ok(km['1403'][1] == 'HKR-4' and km['1404'][1] == 'HKR-5' and km['1404'][2] == 'HKR-3', f'a new row takes the next free number; a row naming an ID already used gets a new one and keeps the old as keyWas: {k}')
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
        c.ok(rv['r']['waiting'] == 1 and rv['pending'][0][0] == '3001' and 'no project' in rv['pending'][0][1], f'a row naming no project (its file holds two) waits on the screen: {rv}')
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
            c.ok('17 rows read' in tie and 'Nothing is lost' in tie and '4 with the owner to confirm' in tie, f'the summary ties before anything is written ({tag}): {tie}')
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
            c.ok('13 new tasks' in toast and '4 with the owner to confirm' in toast, f'the import toasts what happened: {toast}')
            c.ok(await pg.locator('#toast .toast-open').count() == 1, 'with an Open link')
            c.ok(await pg.evaluate("tkKeyedRecs().filter(r => r.rec.asana).length") == 13, 'thirteen tasks written')
            c.ok(not errs, f'no page errors ({tag}): {errs[:3]}')
            await b.close()
    return c.done()

sys.exit(asyncio.run(main()))
