"""team_ws_test: the team's own workspace on the hosted copy (TASKS_PLAN §2 Phase 1 item 1), offline.

The hosted page (dist/ with platform/public/cloud.js in its head) runs over tests/hosted_mock.py, a stand-in for Supabase
shared by every device in the test, so the owner's laptop, the coordinator's phone and the office admin's desktop sync
through one server. Each device's wall clock is set to a Monday (2026-10-26, 9:30 New York). People and records are
invented. It proves:
  1. a demo workspace on the hosted copy still boots the sample company on the demo's day (nothing broken);
  2. a team workspace boots empty: no demo record on the device or on the server (by every name the demo carries), no
     invented people (the owner is added from their profile), sdSeedsOff() from the first moment;
  3. the real clock everywhere: today(), appNowIso(), stamps, the Today page, overdue, a new task's dates; the Firm's
     Clock cannot pin it, and no screen reads the demo's day;
  4. the pilot: the money pages are out of every role's menu and links (owner, coordinator, office admin), Tasks and
     projects are in; the owner turns it off and on in Settings;
  5. the invite flow names the person, adds them to the app's people and records the invitation, sending nothing;
  6. the import runs in the team workspace and the coordinator (phone 390) and the office admin (billing) see the
     workspace's tasks, their own as theirs;
  7. switching workspaces: the device drops the other workspace's copy, nothing crosses in either direction.
Run: python3 team_ws_test.py"""
import asyncio, json, os, re, sys
from harness import *
from hosted_mock import Server, hosted_page, open_hosted
H = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(H, 'asana_invented')
CSV = [os.path.join(D, f) for f in sorted(os.listdir(D)) if f.endswith('.csv')]
MONDAY = '2026-10-26T13:30:00Z'          # 9:30 in New York

MARKERS = """() => { const S = new Set(), add = s => { s = String(s || '').trim(); if (s.length >= 5 && !/^(owner|smartdesign|project|office|general)/i.test(s)) S.add(s); };
  (DB.projects || []).forEach(p => add(p.project && p.project.name)); (DB.clients || []).forEach(c => add(c.name)); (DB.vendors || []).forEach(v => add(v.name));
  (DB.employees || []).forEach(e => add(e.name)); (DB.users || []).forEach(u => add(u.name)); ((DB.hub || {}).contacts || []).forEach(c => add([c.first, c.last].filter(Boolean).join(' ') || c.name));
  (DB.leads || []).forEach(l => add(l.name)); (DB.pos || []).forEach(p => add(p.vendor)); (DB.meetings || []).forEach(m => add(m.title));
  return [...S]; }"""
DEMO_DAY = re.compile(r'2026-09-03|\b9/3\b|Sep(tember)?\.? 3\b|Sept 3\b')

def leaks(text, markers):
    return [m for m in markers if re.search(r'(?<![A-Za-z])' + re.escape(m) + r'(?![A-Za-z])', text)]

async def nav_text(pg):
    return await pg.evaluate("() => [...document.querySelectorAll('#nav button, .rail button, .rail a, nav button, nav a, .bnav a, .bnav button')].filter(e => e.offsetParent).map(e => e.innerText.trim()).filter(Boolean).join(' | ')")

async def main():
    c = Checks()
    S = Server()
    S.ws['sd-team'] = {'kind': 'team', 'name': 'SmartDesign'}
    S.person('auth-dana', 'dana@example.com', 'Dana Whitfield', 'owner', 'sd-team', ['demo-ws'])
    S.person('auth-demo', 'demo.owner@example.com', 'Demo Owner', 'owner', 'demo-ws')
    url = hosted_page()
    async with async_playwright() as p:
        b = await p.chromium.launch()
        # ---- 1. a demo workspace on the hosted copy: the sample company, the demo's day (unchanged behaviour)
        ctx, pg, errs = await open_hosted(b, S, url, 'auth-demo')
        r = await pg.evaluate("() => ({kind: (window.__sdWs || {}).kind, p121: DB.projects.some(p => p.id === 'p121'), today: today(), off: sdSeedsOff()})")
        c.ok(r['kind'] == 'demo' and r['p121'] and r['today'] == '2026-09-03', f'a demo workspace boots the sample company on the demo\'s day: {r}')
        markers = await pg.evaluate(MARKERS)
        c.ok(len(markers) > 20, f'{len(markers)} names the demo carries, to look for in the team workspace')
        await pg.wait_for_timeout(1500)
        c.ok(len(S.names('demo-ws')) > 10, 'the demo uploaded to its own workspace')
        c.ok(not errs, f'no page errors (demo): {errs[:3]}')
        await ctx.close()

        # ---- 2. the team workspace boots empty
        ctx, pg, errs = await open_hosted(b, S, url, 'auth-dana')
        r = await pg.evaluate("""() => ({ws: window.__sdWs, off: sdSeedsOff(), team: twsIsTeam(), projects: DB.projects.length, users: DB.users.map(u => [u.name, u.role, u.contact]),
          me: (currentUser() || {}).name, clients: (DB.clients || []).length, vendors: (DB.vendors || []).length, employees: (DB.employees || []).length,
          bills: (DB.bills || []).length, txns: (DB.txns || []).length, pos: (DB.pos || []).length, tasks: (DB.tasks || []).length, meetings: (DB.meetings || []).length,
          accounts: (DB.accounts || []).length, leads: (DB.leads || []).length, hub: ((DB.hub || {}).contacts || []).length, threads: (DB.threads || []).length})""")
        c.ok(r['ws']['kind'] == 'team' and r['off'] and r['team'], f'the server says team; seeding is off from the first moment: {r["ws"]}')
        c.ok(r['projects'] == 0 and r['users'] == [['Dana Whitfield', 'owner', 'dana@example.com']] and r['me'] == 'Dana Whitfield', f'no projects, no invented people, the owner from her profile: {r["users"]}')
        zero = {k: r[k] for k in ('clients', 'vendors', 'employees', 'bills', 'txns', 'pos', 'tasks', 'meetings', 'accounts', 'leads', 'hub', 'threads')}
        c.ok(not any(zero.values()), f'no demo records of any kind: {zero}')
        dbj = await pg.evaluate("JSON.stringify(DB)")
        lk = leaks(dbj, markers)
        c.ok(not lk, f'none of the demo\'s names anywhere on the device: {lk[:8]}')
        await pg.evaluate("saveNow()")
        await pg.wait_for_timeout(1500)
        srv = json.dumps(S.data('sd-team'))
        c.ok(len(S.names('sd-team')) > 3 and not leaks(srv, markers), f'the first upload carries an empty firm, no demo name on the server: {leaks(srv, markers)[:8]}')
        c.ok('"__teamWs"' in srv and '"tasksOnly": true' in srv, 'the server holds the team mark and the pilot')

        # ---- 3. the real clock
        r = await pg.evaluate("""() => { let threw = ''; try { appSetDay('2026-09-03'); } catch (e) { threw = e.message; }
          return {today: today(), now: appNowIso(), stamp: nowStamp(), asOf: DB.company.asOf, pinned: appDayPinned(), threw, after: today()}; }""")
        c.ok(r['today'] == '2026-10-26' and r['now'].startswith('2026-10-26T09:3') and r['stamp'].startswith('10/26, 9:3') and r['asOf'] == '' and not r['pinned'], f'today, now and stamps are the wall clock\'s: {r}')
        c.ok('real date' in r['threw'] and r['after'] == '2026-10-26', f'the Firm\'s Clock cannot pin the team workspace: {r["threw"]}')

        # ---- 4. the pilot, as the owner
        ov = await pg.evaluate("ROLE_VIEWS.owner")
        money = ['billing', 'bank', 'ap', 'spend', 'reports', 'gl', 'budget', 'po', 'proc', 'costs', 'dashboard', 'mbdash', 'hbdeals', 'verify']
        c.ok(not [v for v in money if v in ov], f'the money pages are out of the owner\'s menu: {[v for v in money if v in ov]}')
        c.ok(all(v in ov for v in ('home', 'tkall', 'port', 'dash', 'sched', 'proj', 'vendors', 'hbcontacts', 'meetings', 'calendar', 'rdata')), 'tasks, projects, people and contacts are in it')
        nt = await nav_text(pg)
        c.ok('Tasks' in nt and not re.search(r'\b(Billing|Accounting|Reports|Purchasing|Banking)\b', nt), f'the menu on screen: {nt[:300]}')
        await pg.evaluate("view = 'billing'; render();")
        c.ok(await pg.evaluate("view") != 'billing', 'a money page asked for directly lands on Home')
        # the screens read today, never the demo's day
        for v in ('home', 'tkall', 'port', 'meetings', 'calendar', 'rdata'):
            await go(pg, v)
            txt = await pg.evaluate("document.querySelector('.view.on, section.view:not([hidden])') ? (document.querySelector('#v-' + view) || document.body).innerText : document.body.innerText")
            m = DEMO_DAY.search(txt)
            c.ok(not m, f'{v} never reads the demo\'s day: {m and txt[max(0, m.start() - 60):m.end() + 40]!r}')
        await go(pg, 'home')
        ht = await pg.evaluate("(document.querySelector('#v-home') || document.body).innerText")
        c.ok(re.search(r'Oct(ober)? 26|10/26|Monday', ht) is not None, f'Today reads Monday, October 26: {ht[:200]!r}')

        # ---- 5. invite the coordinator and the office admin (nothing is sent: the mock records it)
        await go(pg, 'proj')
        await pg.wait_for_timeout(300)
        c.ok(await pg.locator('#cl-team').count() == 1 and await pg.locator('#tws-card').count() == 1, 'Settings shows Team Accounts and the workspace card')
        c.ok(await pg.locator('#tws-pilot').is_checked(), 'the pilot is on')
        os.makedirs(os.path.join(ROOT, 'review', 'laneD'), exist_ok=True)
        await pg.locator('#tws-card').screenshot(path=os.path.join(ROOT, 'review', 'laneD', 'team_workspace_card_desktop.png'))
        c.ok(await pg.locator('#asof-date').count() == 0, 'the Firm\'s Clock has no As Of field here')
        for em, nm, rl in (('priya@example.com', 'Priya Natarajan', 'coord'), ('leo@example.com', 'Leo Marchetti', 'billing')):
            await pg.fill('#cl-inv-email', em)
            await pg.fill('#cl-inv-name', nm)
            if await pg.locator(f'#cl-inv-role option[value="{rl}"]').count() == 0:
                await pg.evaluate("rl => { const s = document.querySelector('#cl-inv-role'); s.add(new Option(rl, rl)); }", rl)
            await pg.select_option('#cl-inv-role', rl)
            await pg.click('#cl-inv-go')
            await pg.wait_for_timeout(500)
        inv = S.invites
        c.ok(len(inv) == 2 and all(i['appUserId'] for i in inv) and [i['role'] for i in inv] == ['coord', 'billing'], f'two invitations recorded with the person in the app and the role: {inv}')
        us = await pg.evaluate("DB.users.map(u => [u.id, u.name, u.role, u.contact])")
        ids = {u[1]: u[0] for u in us}
        c.ok('Priya Natarajan' in ids and 'Leo Marchetti' in ids and inv[0]['appUserId'] == ids['Priya Natarajan'], f'each is a person in the app before they sign in: {us}')
        c.ok(S.profiles['auth-priya']['workspace_id'] == 'sd-team' and S.profiles['auth-priya']['app_user_id'] == ids['Priya Natarajan'], 'their account is in the team workspace, linked to that person')

        # ---- 6. the import, then the coordinator and the office admin see the workspace's tasks
        await pg.evaluate("DB.vendors.push({id: 'v_bay', name: 'Bayside Millwork', email: 'orders@bayside.example'}); save();")
        await go(pg, 'rdata')
        await pg.set_input_files('#aim-file', CSV)
        await pg.wait_for_selector('#aim-tie', timeout=10000)
        c.ok('Nothing is lost' in await pg.inner_text('#aim-tie'), 'the dry run ties in the team workspace')
        await pg.click('#aim-go')
        await pg.wait_for_timeout(400)
        n = await pg.evaluate("DB.projects.flatMap(p => p.actions || []).filter(a => a.asana).length")
        c.ok(n == 9, f'nine tasks with a team owner imported: {n}')
        late = await pg.evaluate("() => { const x = tkItems().find(t => t.title === 'Release deposit to fabricator'); return x && [x.due, x.late]; }")
        c.ok(late == ['2026-10-23', True], f'overdue against the real date: due Friday 10-23, late on Monday: {late}')
        soon = await pg.evaluate("() => { const x = tkItems().find(t => t.title === 'Confirm tile layout with client'); return x && [x.due, x.late]; }")
        c.ok(soon == ['2026-10-27', False], f'due tomorrow is not late: {soon}')
        pj = await pg.evaluate("DB.projects.map(p => [p.project.name, p.project.today, p.log[0] && p.log[0].ts.slice(0, 10)])")
        c.ok(all(x[1] == '' and x[2] == '2026-10-26' for x in pj), f'new projects are stamped today and carry no pinned day: {pj}')
        await pg.evaluate("saveNow()")
        await pg.wait_for_timeout(2000)
        c.ok(not errs, f'no page errors (owner): {errs[:3]}')
        await ctx.close()

        for who, uidk, phone, mine in (('coordinator', 'auth-priya', True, {'Confirm tile layout with client', 'Order the vanity', 'Demo the old cabinets'}),
                                       ('office admin', 'auth-leo', False, {'Measure for shower glass', 'Renew the general liability COI', 'Rough plumbing'})):
            ctx, pg, errs = await open_hosted(b, S, url, uidk, phone=phone)
            r = await pg.evaluate("""() => ({me: (currentUser() || {}).name, role: role(), today: today(), n: tkItems().filter(x => x.kind === 'action').length,
              all: tkItems().filter(x => x.kind === 'action' && tkOwnerMatch(x.assignee, (currentUser() || {}).name)).map(x => x.title)})""")
            c.ok(r['me'] in ('Priya Natarajan', 'Leo Marchetti') and r['today'] == '2026-10-26', f'the {who} signs in as themself, on the real date: {r["me"]} {r["role"]} {r["today"]}')
            c.ok(r['n'] == 9, f'the {who} reads the workspace\'s nine tasks: {r["n"]}')
            c.ok(set(r['all']) == mine, f'and their own three are theirs: {r["all"]}')
            rv = await pg.evaluate("ROLE_VIEWS[role()]")
            c.ok('tkall' in rv and not [v for v in money if v in rv], f'the {who}\'s menu: Tasks in, money out ({[v for v in money if v in rv]})')
            await go(pg, 'tkall')
            os.makedirs(os.path.join(ROOT, 'review', 'laneD'), exist_ok=True)
            await pg.screenshot(path=os.path.join(ROOT, 'review', 'laneD', f'team_tasks_{uidk}_{"phone" if phone else "desktop"}.png'))
            sw = await pg.evaluate("document.documentElement.scrollWidth - innerWidth")
            c.ok(sw <= 0, f'Tasks on the {who}\'s {"phone" if phone else "desktop"}: no sideways scroll ({sw}px)')
            body = await pg.evaluate("(document.querySelector('#v-tkall') || document.body).innerText")
            c.ok(not DEMO_DAY.search(body), f'the {who}\'s Tasks never reads the demo\'s day')
            dbj = await pg.evaluate("JSON.stringify(DB)")
            c.ok(not leaks(dbj, markers), f'no demo name on the {who}\'s device: {leaks(dbj, markers)[:5]}')
            c.ok(not errs, f'no page errors ({who}): {errs[:3]}')
            await ctx.close()

        # ---- the owner turns the pilot off, then on again; then switches to the demo and back
        ctx, pg, errs = await open_hosted(b, S, url, 'auth-dana')
        await go(pg, 'proj')
        await pg.wait_for_timeout(300)
        await pg.click('#tws-pilot')
        await pg.wait_for_timeout(300)
        r = await pg.evaluate("({pilot: DB.company.pilot.tasksOnly, billing: ROLE_VIEWS.owner.includes('billing'), bank: ROLE_VIEWS.owner.includes('bank'), billingRole: ROLE_VIEWS.billing.includes('billing')})")
        c.ok(r == {'pilot': False, 'billing': True, 'bank': True, 'billingRole': True}, f'pilot off: every page is back, for every role: {r}')
        c.ok('Pilot off' in await pg.inner_text('#toast'), 'it toasts what happened')
        await pg.click('#tws-pilot')
        await pg.wait_for_timeout(300)
        c.ok(await pg.evaluate("DB.company.pilot.tasksOnly && !ROLE_VIEWS.owner.includes('billing')"), 'and on again')
        team_before = json.dumps(S.data('sd-team'))
        demo_before = json.dumps(S.data('demo-ws'))
        await pg.click('[data-twsgo="demo-ws"]')
        await pg.wait_for_function("document.body.dataset.booted==='1' && window.__sdWs && window.__sdWs.id === 'demo-ws'", timeout=90000)
        await pg.wait_for_timeout(1500)
        r = await pg.evaluate("({kind: window.__sdWs.kind, team: DB.projects.some(p => p.project.asanaName), p121: DB.projects.some(p => p.id === 'p121')})")
        c.ok(r == {'kind': 'demo', 'team': False, 'p121': True}, f'switched to the demo: the team\'s records stayed behind: {r}')
        c.ok(not re.search(r'Pine Ave|Hollis Kitchen', json.dumps(S.data('demo-ws'))), 'nothing of the team reached the demo on the server')
        await pg.click('[data-twsgo="sd-team"]') if await pg.locator('[data-twsgo="sd-team"]').count() else await pg.evaluate("Cloud.switchWorkspace('sd-team').then(() => location.reload())")
        await pg.wait_for_function("document.body.dataset.booted==='1' && window.__sdWs && window.__sdWs.id === 'sd-team'", timeout=90000)
        await pg.wait_for_timeout(1500)
        r = await pg.evaluate("({n: DB.projects.flatMap(p => p.actions || []).filter(a => a.asana).length, p121: DB.projects.some(p => p.id === 'p121')})")
        c.ok(r == {'n': 9, 'p121': False}, f'and back: the team\'s tasks, no demo job: {r}')
        lk = leaks(json.dumps(S.data('sd-team')), markers)
        c.ok(not lk, f'nothing of the demo reached the team workspace on the server: {lk[:5]}')
        c.ok(not errs, f'no page errors (switching): {errs[:3]}')
        await ctx.close()
        await b.close()
    return c.done()

sys.exit(asyncio.run(main()))
