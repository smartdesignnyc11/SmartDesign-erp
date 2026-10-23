"""asana_import_test: the Asana board comes in once, from Asana's CSV export, with nothing lost (TASKS_PLAN §2 Phase 1 item 2).

The export is invented (tests/asana_invented/: Asana's exact columns, invented people, jobs and vendors; the firm's real
export never enters the repo). Three project files: a job whose tasks carry IDs in their names (PAD-21), an office
project whose IDs sit in a custom field (Ref: OPS-12), and a job with no IDs at all; a task in two projects, subtasks,
a subtask whose parent was not exported, notes with commas, quotes and a line break, finished rows, someone outside the
team as assignee (a vendor on file, and someone on file nowhere), a row with no assignee.

It proves: the dry run's counts tie to the rows read; each Asana project becomes a project with its prefix; IDs are
kept, and numbered in order where there are none, never twice; sections give order and section; a team member becomes
the owner, anyone else Waiting On with the owner left for review; notes are the first comment; finished rows are done
with their date; subtasks are checklist steps; nothing lands in a "General" project; the review list waits for an owner
and becomes tasks when one is picked; a second import updates and never duplicates, and keeps what was changed in the
app; the screen (desktop and phone 390) shows the summary before anything is written, with one blue button; nothing
from the export is written to the console.
Run: python3 asana_import_test.py"""
import asyncio, json, os, re, sys
from harness import *
H = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(H, 'asana_invented')
FILES = [{'name': f, 'text': open(os.path.join(D, f), encoding='utf-8').read()} for f in sorted(os.listdir(D)) if f.endswith('.csv')]

SETUP = """() => {
  DB.users.push({id: 'u_dana', name: 'Dana Whitfield', role: 'owner', contact: 'dana@example.com'},
                {id: 'u_priya', name: 'Priya Natarajan', role: 'coord', contact: 'priya@example.com'},
                {id: 'u_leo', name: 'Leo Marchetti', role: 'billing', contact: 'leo@example.com'});
  DB.vendors.push({id: 'v_bay', name: 'Bayside Millwork', email: 'orders@bayside.example'});
  save(); return true; }"""
TASKS = """() => { const out = {}; (DB.projects || []).forEach(p => (p.actions || []).forEach(a => { if (a.asana) out[a.key] = Object.assign({}, a, {projectName: p.project.name, prefixP: p.project.prefix, sched: (p.tasks || []).length}); })); return out; }"""

async def main():
    c = Checks()
    async with async_playwright() as p:
        b, pg, errs = await open_app(p)
        logs = []
        pg.on('console', lambda m: logs.append(m.text))
        await sign_in(pg, 'u_owner')
        await pg.evaluate(SETUP)
        projects0 = await pg.evaluate("DB.projects.length")
        # ---- the dry run: nothing written, the counts tie
        P = await pg.evaluate("files => { const before = JSON.stringify(DB.projects); const P = aimPlan(files); return Object.assign(P, {untouched: before === JSON.stringify(DB.projects)}); }", FILES)
        T = P['totals']
        c.ok(P['untouched'], 'the dry run writes nothing')
        c.ok(not P['errors'], f"the three files read as Asana exports: {P['errors']}")
        c.ok(T['rows'] == 17, f"17 rows read across the three files: {T['rows']}")
        tie = T['tasks'] + T['steps'] + T['review'] + T['orphans'] + T['duplicates']
        c.ok(tie == T['rows'], f'the counts tie: {T["tasks"]} tasks + {T["steps"]} steps + {T["review"]} for review + {T["orphans"]} orphan + {T["duplicates"]} repeated = {tie} of {T["rows"]}')
        c.ok((T['tasks'], T['create'], T['done'], T['steps'], T['review'], T['orphans'], T['duplicates'], T['newProjects']) == (9, 9, 1, 2, 4, 1, 1, 3), f'the summary: {T}')
        PR = {x['name']: x for x in P['projects']}
        c.ok(set(PR) == {'PAD - Pine Ave Duplex', 'Operations', 'Hollis Kitchen Renovation'}, f'three Asana projects: {sorted(PR)}')
        c.ok(PR['PAD - Pine Ave Duplex']['prefix'] == 'PAD' and PR['Operations']['prefix'] == 'OPS' and PR['Hollis Kitchen Renovation']['prefix'] == 'HKR',
             f"prefixes: from the IDs in the names (PAD), in a custom field (OPS), from the name when there are none (HKR): {[(k, v['prefix']) for k, v in PR.items()]}")
        c.ok((PR['PAD - Pine Ave Duplex']['create'], PR['PAD - Pine Ave Duplex']['review'], PR['PAD - Pine Ave Duplex']['sub'], PR['Operations']['create'], PR['Operations']['review'], PR['Hollis Kitchen Renovation']['create']) == (4, 3, 2, 3, 1, 2),
             f'counts per project: {[(k, v["create"], v["review"], v["sub"]) for k, v in PR.items()]}')
        PE = {x['name']: x for x in P['people']}
        c.ok(PE['Priya Natarajan']['owner'] == 3 and PE['Dana Whitfield']['owner'] == 3 and PE['Leo Marchetti']['owner'] == 3, f'counts per person, owners: {P["people"]}')
        c.ok(PE['Bayside Millwork']['waitingOn'] == 1 and PE['Rita Okafor']['waitingOn'] == 1 and PE['Former Staffer']['waitingOn'] == 1 and PE['Nobody']['review'] == 1, f'and who is waited on: {P["people"]}')
        keys = sorted(t[0] if isinstance(t, list) else t['key'] for t in P['tasks'])
        c.ok(keys == sorted(['PAD-21', 'PAD-22', 'PAD-24', 'PAD-27', 'OPS-12', 'OPS-13', 'OPS-15', 'HKR-1', 'HKR-2']), f'IDs kept and numbered in order, never twice: {keys}')
        rv = sorted(t['key'] for t in P['review'])
        c.ok(rv == ['OPS-14', 'PAD-23', 'PAD-25', 'PAD-26'], f'four rows wait for an owner: {rv}')
        allkeys = keys + rv
        c.ok(len(set(allkeys)) == len(allkeys), 'no ID is given twice')
        # ---- the import
        r = await pg.evaluate("files => aimApply(aimPlan(files), {})", FILES)
        c.ok(r['created'] == 9 and r['waiting'] == 4 and r['projects'] == 3, f'nine tasks and three projects written, four wait: {r}')
        t = await pg.evaluate(TASKS)
        c.ok(len(t) == 9, f'nine tasks with their Asana id: {sorted(t)}')
        a = t.get('PAD-21', {})
        c.ok(a.get('title') == 'Confirm tile layout with client' and a.get('owner') == 'u_priya' and a.get('assignee') == 'Priya Natarajan', f'PAD-21: the title without its ID, Priya the owner: {a.get("title")} {a.get("owner")}')
        c.ok(a.get('section') == 'Design' and a.get('order') == 1 and a.get('due') == '2026-10-27' and a.get('status') == 'todo' and a.get('prefix') == 'PAD', f"section, order, due, status, prefix: {[a.get(k) for k in ('section', 'order', 'due', 'status', 'prefix')]}")
        cm = (a.get('comments') or [{}])[0]
        c.ok(cm.get('text') == 'Client wants the herringbone, "not" the straight lay.\nCheck the grout color with her.' and cm.get('by') == 'Asana', f'the notes are the first comment, commas, quotes and line break intact: {cm}')
        c.ok(a.get('thread') and a['thread'][0].get('text') == cm.get('text'), 'and show on the task sheet\'s notes')
        ck = a.get('checklist') or []
        c.ok(len(ck) == 2 and [x['done'] for x in ck] == [False, True] and ck[0]['t'].startswith('Pick grout color'), f'the two subtasks are checklist steps, one ticked: {ck}')
        c.ok(a.get('tags') == ['client'] and (a.get('custom') or {}).get('Priority') == 'High', f"tags and the custom field kept: {a.get('tags')} {a.get('custom')}")
        d = t.get('PAD-24', {})
        c.ok(d.get('status') == 'done' and d.get('completedAt') == '2026-10-15', f'a finished row is done, with its date: {d.get("status")} {d.get("completedAt")}')
        h2 = t.get('HKR-2', {})
        c.ok(h2.get('status') == 'doing' and (h2.get('deps') or {}).get('blockedBy') == ['1401'], f'the "In Progress" section reads as Doing; the dependency is kept: {h2.get("status")} {h2.get("deps")}')
        c.ok(t.get('HKR-1', {}).get('start') == '2026-10-26', 'the start date is kept')
        c.ok(t.get('OPS-15', {}).get('owner') == 'u_dana', 'a first name only one team member carries ("Dana") is that person')
        c.ok(t.get('OPS-12', {}).get('owner') == 'u_leo' and t.get('OPS-12', {}).get('due') == '2026-11-05', 'the ID from the custom field is the task\'s ID')
        c.ok(all(x.get('projectName') != 'General' for x in t.values()) and await pg.evaluate("!DB.projects.some(p => /^general$/i.test(p.project.name))"), 'nothing goes to "General"')
        pj = await pg.evaluate("() => DB.projects.filter(p => p.project.asanaName).map(p => ({name: p.project.name, prefix: p.project.prefix, sched: p.tasks.length, today: p.project.today}))")
        c.ok(len(pj) == 3 and all(x['sched'] == 0 and x['today'] == '' for x in pj), f'each Asana project is a project here, no schedule invented, no pinned day: {pj}')
        c.ok(await pg.evaluate("DB.projects.length") == projects0 + 3, 'three projects added, none twice')
        ti = await pg.evaluate("() => tkItems().filter(x => x.kind === 'action' && /^(PAD|OPS|HKR)-/.test(((DB.projects.find(p => p.id === x.projectId) || {actions: []}).actions.find(a => a.id === x.id) || {}).key || '')).length")
        c.ok(ti == 9, f'the one task list reads all nine: {ti}')
        # ---- the review list: owners picked, tasks made
        pend = await pg.evaluate("() => DB.asanaImport.pending.map(x => x.key).sort()")
        c.ok(pend == ['OPS-14', 'PAD-23', 'PAD-25', 'PAD-26'], f'the review list holds the four: {pend}')
        w = await pg.evaluate("() => { const r = aimResolve('1203', 'u_dana'); return r && {owner: r.a.owner, wo: r.a.waitingOn, status: r.a.status, waitsOn: r.a.waitsOn, key: r.a.key}; }")
        c.ok(w and w['owner'] == 'u_dana' and w['key'] == 'PAD-23' and w['status'] == 'waiting', f'PAD-23 gets its owner and becomes a task: {w}')
        c.ok(w and (w['wo'] or {}).get('name') == 'Bayside Millwork' and (w['wo'].get('contactRef') or {}).get('id') == 'v_bay' and w['wo'].get('promised') == '2026-10-29', f"the vendor is Waiting On, linked to the vendor on file, with the date: {w and w['wo']}")
        c.ok(w and w['waitsOn'] == 'Bayside Millwork', 'the list shows it waiting on them')
        c.ok(await pg.evaluate("aimResolve('1207', 'u_nobody_here')") is None, 'a row is never given an owner who is not a team member')
        # ---- a second import of the same files: nothing duplicated
        P2 = await pg.evaluate("files => aimPlan(files).totals", FILES)
        c.ok(P2['create'] == 0 and P2['same'] == 10 and P2['update'] == 0 and P2['review'] == 3, f'the same export again: nothing new, ten unchanged, three still waiting: {P2}')
        r2 = await pg.evaluate("files => aimApply(aimPlan(files), {})", FILES)
        t2 = await pg.evaluate(TASKS)
        c.ok(r2['created'] == 0 and len(t2) == 10, f'a second import adds no task: {r2} {len(t2)}')
        c.ok(await pg.evaluate("DB.asanaImport.pending.length") == 3, 'the review list is replaced, not doubled')
        c.ok(len(t2['PAD-21']['comments']) == 1 and len(t2['PAD-21']['checklist']) == 2, 'no comment or step twice')
        c.ok(await pg.evaluate("DB.projects.length") == projects0 + 3, 'no project twice')
        # ---- a newer export: Asana's changes come in; what the meeting changed in the app stays
        await pg.evaluate("() => { const a = DB.projects.flatMap(p => p.actions || []).find(a => a.key === 'PAD-22'); a.due = '2026-10-26'; save(); }")
        newer = [dict(f) for f in FILES]
        pad = next(f for f in newer if f['name'] == 'pad_pine_ave.csv')
        pad['text'] = (pad['text']
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
        k = await pg.evaluate("""files => { const p = DB.projects.find(p => p.project.prefix === 'HKR'); p.actions.push({id: 'a_hand', key: 'HKR-3', title: 'Made by hand', owner: 'u_priya', assignee: 'Priya Natarajan', status: 'todo'});
          const f = 'Task ID,Created At,Completed At,Last Modified,Name,Section/Column,Assignee,Assignee Email,Start Date,Due Date,Tags,Notes,Projects,Parent task,Blocked By (Dependencies),Blocking (Dependencies)\\n' +
            '1403,2026-10-12,,2026-10-22,Order the hood,To Do,Priya Natarajan,priya@example.com,,,,,Hollis Kitchen Renovation,,,\\n1404,2026-10-12,,2026-10-22,HKR-3 Tile backsplash,To Do,Priya Natarajan,priya@example.com,,,,,Hollis Kitchen Renovation,,,\\n';
          const P = aimPlan([{name: 'hollis2.csv', text: f}]); return P.tasks.map(t => [t.asanaId, t.key, t.keyWas || '']); }""")
        km = {x[0]: x for x in k}
        c.ok(km['1403'][1] == 'HKR-4' and km['1404'][1] == 'HKR-5' and km['1404'][2] == 'HKR-3', f'a new row takes the next free number; a row naming an ID already used gets a new one and says so: {k}')
        # ---- not an Asana export
        e = await pg.evaluate("() => { const n = DB.projects.length; const P = aimPlan([{name: 'contacts.csv', text: 'Name,Email\\nA,b@c.d\\n'}]); return {err: P.errors, tasks: P.tasks.length, same: n === DB.projects.length}; }")
        c.ok(e['err'] and 'not an Asana export' in e['err'][0] and e['tasks'] == 0 and e['same'], f'another CSV is refused by name, nothing read: {e}')
        c.ok(not any(re.search(r'herringbone|Bayside|Rita Okafor|fabricator', l) for l in logs), 'nothing from the export reaches the console')
        c.ok(not errs, f'no page errors: {errs[:3]}')
        await b.close()

        # ---- the screen, desktop then phone: summary first, one blue button, review, import, findable from Tasks
        for phone in (False, True):
            b, pg, errs = await open_app(p, phone=phone)
            await sign_in(pg, 'u_owner')
            await pg.evaluate(SETUP)
            await go(pg, 'rdata')
            c.ok(await pg.locator('#aim-card').count() == 1, f'Your Own Data has Import From Asana ({"phone" if phone else "desktop"})')
            await pg.set_input_files('#aim-file', [os.path.join(D, f['name']) for f in FILES])
            await pg.wait_for_selector('#aim-tie', timeout=10000)
            tie = await pg.inner_text('#aim-tie')
            c.ok('17 rows read' in tie and 'Nothing is lost' in tie, f'the summary ties before anything is written: {tie}')
            c.ok(await pg.evaluate("!DB.projects.some(p => p.project.asanaName)"), 'and nothing is written yet')
            os.makedirs(os.path.join(ROOT, 'review', 'laneD'), exist_ok=True)
            await pg.screenshot(path=os.path.join(ROOT, 'review', 'laneD', f'asana_summary_{"phone" if phone else "desktop"}.png'), full_page=True)
            c.ok(await pg.locator('#aim-projects tbody tr').count() == 3 and await pg.locator('#aim-people tbody tr').count() >= 6, 'counts per project and per person')
            prim = await pg.evaluate("[...document.querySelectorAll('#v-rdata .btn.primary')].filter(b => b.offsetParent).length")
            c.ok(prim == 1, f'one blue button on the screen: {prim}')
            sw = await pg.evaluate("document.documentElement.scrollWidth - innerWidth")
            c.ok(sw <= 0, f'no sideways scroll ({sw}px)')
            await pg.select_option('[data-aimown="1205"]', 'u_leo')
            await pg.click('#aim-go')
            await pg.wait_for_timeout(300)
            toast = await pg.inner_text('#toast')
            c.ok('10 new tasks' in toast and '3 wait for an owner' in toast, f'the import toasts what happened: {toast}')
            c.ok(await pg.locator('#toast .toast-open').count() == 1, 'with an Open link')
            n = await pg.evaluate("DB.projects.flatMap(p => p.actions || []).filter(a => a.asana).length")
            c.ok(n == 10, f'ten tasks: nine with team owners and the row given Leo: {n}')
            await go(pg, 'tkall')
            c.ok(await pg.locator('#aim-wait').count() == 1 and '3 tasks from Asana wait' in await pg.inner_text('#aim-wait'), 'Tasks names the rows still waiting, one tap from the review')
            await pg.click('#aim-wait-go')
            await pg.wait_for_timeout(200)
            c.ok(await pg.evaluate("view") == 'rdata' and await pg.locator('[data-aimown]').count() == 2, 'which opens the review with the two open rows (the finished one is picked for its project)')
            await pg.select_option('[data-aimown="1203"]', 'u_dana')
            await pg.click('#aim-resolve')
            await pg.wait_for_timeout(200)
            c.ok(await pg.evaluate("DB.asanaImport.pending.length") == 2, 'picking an owner makes the task; the rest still wait')
            c.ok(not errs, f'no page errors: {errs[:3]}')
            await b.close()
    return c.done()

sys.exit(asyncio.run(main()))
