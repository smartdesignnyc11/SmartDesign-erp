"""menu_test: each role's menu is pinned so it cannot drift again (BACKLOG §1.15). The pins are the menu Alan approved on
11-03 (docs/DECISIONS.md, the 11-03 row; docs/mockups/job-structure: MenuNow and Main for the phone, Desk's rail for
the desktop), which replaced the Navigation and Pages Workshop's menus of 2026-10-19 (docs/MENU_DRAFT.md): Your Day
(Today, Tasks, Messages), Work (Projects, Purchasing, Sales and Clients, Accounting, Design, Reports), Company and
Settings at the foot; a group opens on its name; no More.

For every role in the SmartDesign workspace, on desktop (1440x900) and phone (390x844), it checks:
  MENU      the menu reads exactly the decided entries, top to bottom (Your Day's entries, the Work groups, Company and
            Settings); each group lists exactly its decided pages; the office roles' phone bar and the field roles'
            tab bar read exactly their decided 4-5 daily pages
  HOME      sign-in opens the role's first page (Today for every office role; the designer's Today is My Day)
  REACH     every page the role may open (ROLE_VIEWS) is reachable: a menu entry, a job's tab (the strip while a job is
            open), Today's Approvals link, the Ask button, or the page an old name forwards to. Nothing is orphaned.
  OPEN      every entry, pressed for real (its group opened by its name first), opens its page and lights itself; a
            job opened from Projects lights itself, and every tab of the job's strip opens and lights itself
  HEADING   the page heading reads as the entry that is lit (a job's tab, the entry, else its group), as the screen
            lint reads it
  ASK       the Ask button is in the header on every screen; pressing it opens Ask and lights it; Ask is no menu item
  PRIMARY   at most one blue primary button on each screen the menu opens
  PHONE     at 390px: no sideways scroll on any page the bar or the menu opens; the menu button opens the whole menu
  BADGE     an entry's number is the count its page states for the person (mnItemN: Today's late rows, Tasks' Due Soon,
            Messages' unread, Billing's to-do, onecount's badge); no group name carries one
Usage: python3 menu_test.py [--user u_owner,...] [--desktop|--phone]
"""
import asyncio, re, sys
from harness import *

ICON_NEW = 'Ask'
W_ALL = ['Projects', 'Purchasing', 'Sales and Clients', 'Accounting', 'Design', 'Reports']
DAY3 = ['Today', 'Tasks', 'Messages']
FOOT = ['Company and Settings']
# The decided menus (the 11-03 menu): the entries in order, Your Day, the Work groups, then the foot's group. Each role
# has the entries ROLE_VIEWS lets it open.
RAIL = {
    'u_owner': DAY3 + W_ALL + FOOT,
    # no Design menu for the PM or the coordinator (docs/mockups/design/SPEC.md, 11-03)
    'u_alan': DAY3 + ['Projects', 'Purchasing', 'Sales and Clients', 'Accounting', 'Reports'] + FOOT,
    'u_chen': DAY3 + ['Projects', 'Purchasing', 'Sales and Clients', 'Accounting', 'Reports'] + FOOT,
    'u_billing': DAY3 + ['Projects', 'Purchasing', 'Sales and Clients', 'Accounting', 'Reports'] + FOOT,
    'u_controller': DAY3 + ['Projects', 'Purchasing', 'Sales and Clients', 'Accounting', 'Reports'] + FOOT,
    'u_sarah': DAY3 + ['Projects', 'Sales and Clients', 'Design', 'Reports'] + FOOT,
    # field roles: their own day page and Messages, then the rest of the bar and the menu in order, then the foot
    'u_angel': ['Today', 'Messages', 'Daily Log', 'Site', 'Requests', 'Crew', 'Drawings', 'Schedule', 'Photos', 'Documents', 'Raise'] + FOOT,
    'u_alberto': ['Clock', 'Messages', 'Requests', 'Schedule', 'Photos', 'Deliveries', 'Drawings'] + FOOT,
    'u_alex': ['Route', 'Messages', 'Clock', 'Receipts', 'Requests', 'Stock'] + FOOT,
    # the client portal keeps its own menu (out of scope)
    'u_klein': ['Overview', 'Schedule', 'Decisions', 'Account', 'Chat'],
}
# Purchasing (docs/mockups/purchasing/SPEC.md, 11-03): Alan's five; Stock for the coordinator and the driver only
BUY = ['Buy Board', 'Orders', 'Quotes', 'Deliveries', 'Vendors']
SETTINGS = ['Settings', 'Connections', 'The SmartDesign Standard', 'Problem Reports']
# Each group's pages (Projects lists the person's jobs first: checked by name below, then All Projects).
KIDS = {
    ('u_owner', 'buy'): BUY,
    ('u_owner', 'sales'): ['Pipeline', 'Estimates', 'Clients', 'Numbers', 'Partners', 'Playbook'],
    ('u_owner', 'money'): ['Billing', 'Banking', 'Bills and Payroll', 'Time and Crew', 'Spend', 'Ledger', 'Controls', 'Budget', 'Accounting Overview'],
    ('u_owner', 'studio'): ['Selections', 'Drawings'],
    ('u_owner', 'reports'): ['All Reports', 'Dashboard'],
    ('u_owner', 'setup'): ['Company', 'Calendar', 'Team', 'Meetings', 'Obligations', 'The Brain', 'Chief of Staff'] + SETTINGS + ['Your Own Data', 'Sales Settings'],
    ('u_alan', 'buy'): BUY,
    ('u_alan', 'sales'): ['Pipeline', 'Estimates', 'Clients', 'Numbers', 'Partners', 'Playbook'],
    ('u_alan', 'money'): ['Billing', 'Banking', 'Bills and Payroll', 'Time and Crew', 'Spend', 'Controls', 'Accounting Overview'],
    ('u_alan', 'setup'): ['Company', 'Calendar', 'Team', 'Meetings', 'Obligations', 'The Brain', 'Chief of Staff'] + SETTINGS + ['Sales Settings'],
    ('u_chen', 'buy'): BUY + ['Stock'],
    ('u_chen', 'sales'): ['Pipeline', 'Clients', 'Forecast', 'Sales Dashboard', 'Partners', 'Playbook'],
    ('u_chen', 'money'): ['Time and Crew'],
    ('u_billing', 'buy'): ['Vendors'],
    ('u_billing', 'money'): ['Billing', 'Banking', 'Bills and Payroll', 'Spend', 'Accounting Overview'],
    ('u_controller', 'buy'): ['Orders', 'Vendors'],
    ('u_controller', 'money'): ['Billing', 'Banking', 'Bills and Payroll', 'Time and Crew', 'Spend', 'Ledger', 'Controls', 'Budget', 'Accounting Overview'],
    ('u_sarah', 'studio'): ['Selections', 'Drawings'],
    ('u_sarah', 'setup'): ['Team', 'Connections', 'The SmartDesign Standard'],
    ('u_angel', 'setup'): ['Team', 'Connections', 'The SmartDesign Standard'],
}
# A job's tabs (Alan, 11-03: docs/mockups/job-structure/): eight, in this order, for a role that may open each page;
# the job-structure lane's pin, read on the job's page (the desktop's strip; the phone's Overview lists them)
JOB_TABS = ['Overview', 'Schedule', 'Contract and Billing', 'Budget', 'Purchasing', 'Decisions', 'Site', 'Documents']
JOB_TABS_FOR = {'u_owner': JOB_TABS, 'u_alan': JOB_TABS,
                'u_chen': ['Overview', 'Schedule', 'Purchasing', 'Decisions', 'Site', 'Documents'],
                'u_billing': ['Overview', 'Contract and Billing', 'Documents'],
                'u_sarah': ['Schedule', 'Decisions', 'Documents']}
# every office role and billing and the controller start on Today (their approved boards, 2026-10-25)
HOME = {'u_owner': 'home', 'u_alan': 'home', 'u_chen': 'home', 'u_billing': 'home', 'u_controller': 'home', 'u_sarah': 'sday',
        'u_angel': 'ftoday', 'u_alberto': 'time', 'u_alex': 'route', 'u_klein': 'client'}
# Phone: the office roles' bottom bar, the field roles' tab bar (unchanged by the 11-03 menu).
PHONE_BAR = {
    # four shortcuts at most, Chat one of them (Alan, 2026-10-19); the approved Today boards (2026-10-25) set each bar;
    # the PM's holds five (TodayPM)
    'u_owner': ['Today', 'Projects', 'Sales', 'Messages'],
    'u_alan': ['Today', 'Projects', 'Clients', 'Tasks', 'Messages'],
    'u_chen': ['Today', 'Messages', 'Tasks', 'Buy Board'],
    'u_billing': ['Today', 'Billing', 'Clients', 'Messages'],
    'u_controller': ['Today', 'Banking', 'Bills and Payroll', 'Messages'],
    'u_sarah': ['Today', 'Messages', 'Drawings', 'Projects'],
    'u_angel': ['Today', 'Daily Log', 'Site', 'Requests', 'Messages'],   # TodayForeman holds five
    'u_alberto': ['Clock', 'Requests', 'Schedule', 'Messages'],
    'u_alex': ['Route', 'Messages', 'Clock', 'Receipts'],
}
FIELD = {'u_angel', 'u_alberto', 'u_alex'}

STATE = r"""() => {
  const vis = el => { if (!el) return false; const r = el.getBoundingClientRect(), s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  const txt = el => el ? (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim() : '';
  const lab = el => { if (!el) return ''; const c = el.cloneNode(true); c.querySelectorAll('.n, svg').forEach(x => x.remove()); return c.textContent.replace(/\s+/g, ' ').trim(); };
  const strip = el => txt(el).replace(/\s*\d+\+?$/, '').trim();
  const v = document.querySelector('.view.on');
  let h = v && ([...v.querySelectorAll('h1')].find(vis) || [...v.querySelectorAll('h2')].find(vis));
  const cr = document.querySelector('#crumbs b');
  if (innerWidth <= 760 && v && v.querySelector('.ph h2.td-in-hdr, .td-ph h2.td-in-hdr') && vis(cr)) h = cr;
  const ent = document.querySelector('#nav-groups button.on'), head = document.querySelector('#nav-groups .mn-head.cur');
  const sub = document.querySelector('#subnav .sub-tabs button.on');
  const bar = [...document.querySelectorAll('#mtabs button.on, #tabbar button.on')].find(vis);
  const ask = document.getElementById('tb-ask');
  let page = ''; try { page = mnCurLabel(mnCur(mnBuild(role()))); } catch (e) {}
  return { view, folded: typeof paMenuView === 'function' ? paMenuView() : '', heading: txt(h), ent: lab(ent), page, entV: ent ? ent.dataset.v : '', pid: ent ? (ent.dataset.pid || '') : '',
    grp: lab(head), sub: sub && vis(sub) ? strip(sub) : '',
    bar: bar ? strip(bar) : '', ask: !!(ask && !ask.hidden && vis(ask)), askOn: !!(ask && ask.classList.contains('on')),
    prim: [...(v ? v.querySelectorAll('.btn.primary') : [])].filter(vis).map(txt),
    sw: document.documentElement.scrollWidth, w: innerWidth };
}"""
# the menu's entries in order: Your Day's and the field's entries, the groups' names (not their pages)
RAIL_JS = r"""() => [...document.querySelectorAll('#nav-groups button.mn-top, #nav-groups [data-mnhead]')].map(b => { const c = b.cloneNode(true); c.querySelectorAll('.n, svg').forEach(x => x.remove());
  return { head: b.matches('[data-mnhead]'), grp: b.dataset.grp || b.dataset.mnhead, v: b.dataset.v || '', label: c.textContent.replace(/\s+/g, ' ').trim(), n: +((b.querySelector('.n') || {}).textContent || 0) }; })"""
KIDS_JS = r"""g => [...document.querySelectorAll(`#nav-groups [data-mngr="${g}"] button`)].map(b => { const c = b.cloneNode(true); c.querySelectorAll('.n, svg').forEach(x => x.remove());
  return { v: b.dataset.v, tab: b.dataset.tab || '', pid: b.dataset.pid || '', label: c.textContent.replace(/\s+/g, ' ').trim(), n: +((b.querySelector('.n') || {}).textContent || 0) }; })"""
SUB_JS = r"""() => [...document.querySelectorAll('#subnav .sub-tabs > *')].map(e => e.dataset && e.dataset.sub ? (e.innerText || e.textContent).replace(/\s+/g, ' ').replace(/\s*\d+\+?$/, '').trim() : '[' + e.textContent.trim() + ']')"""
# every page the role may open, and where it is reached: an entry, a job's tab, Today's Approvals link, a button
REACH_JS = r"""() => { const m = mnMap(), rv = (ROLE_VIEWS[role()] || []).filter((v, i, a) => a.indexOf(v) === i), mb = typeof MB_VIEWS !== 'undefined' ? MB_VIEWS : [];
  const items = (m.field ? m.day.concat(m.work) : m.day.concat(m.work.flatMap(g => g.items))).concat(m.foot).map(s => s.split('=')[0].split(':')[0]);
  const placed = new Set(items.concat(mnJobStrip(role()).map(i => i.v), m.field ? [] : [mnJobLanding(role())])), out = [];
  rv.forEach(v => { if (mb.includes(v) || placed.has(v) || MN_BUTTON.has(v) || ['client', 'clacct'].includes(v)) return;
    for (let a = MN_ALIAS[v], k = 0; a && k < 3; a = MN_ALIAS[a], k++) if (placed.has(a)) return;   // an alias may lead to an alias
    if (MN_QUIET.has(v)) return;   // retired: listed while open, under its group
    out.push(v); });
  return { orphans: out, home: m.home }; }"""
# an entry's number against what its page counts for the person; a group's name carries none
BADGE_JS = r"""() => { const out = []; document.querySelectorAll('#nav-groups button[data-v], #nav-groups [data-mnhead]').forEach(b => {
  const n = +((b.querySelector('.n') || {}).textContent || 0);
  if (b.matches('[data-mnhead]')) { if (b.querySelector('.n')) out.push(`the group ${b.dataset.mnhead} carries a number`); return; }
  const v = b.dataset.v; if (b.dataset.tab || b.dataset.pid || /^ov/.test(v)) { if (n) out.push(`${v} carries ${n}`); return; }
  let want = null;
  if (v === 'home') want = (typeof TD2_SPEC === 'object' && TD2_SPEC[role()]) ? td2LateN() : 0;
  else if (v === 'tkall') want = tkTasksN();
  else if (v === 'chat') want = p2nMsgN().n;
  else if (v === 'billing') want = billingNeeds();
  else if (MENU[role()] && MENU[role()].field) want = 0;   // the field's menu: Messages only (its tab bar carries its own)
  else { const k = ocBadgeN(v); want = k == null ? 0 : k; }
  if (want !== n) out.push(`${v} shows ${n}, its list holds ${want}`); }); return out; }"""
NORM = lambda s: re.sub(r'\s+', ' ', (s or '').replace('&', 'and')).strip().lower()

def heading_ok(st):
    h = NORM(st['heading'])
    for l in (st['sub'], st['page'], st['ent'], st['grp'], st['bar']):
        l = NORM(l)
        if l and (h == l or h.startswith(l + ' — ') or h.startswith(l + ' · ')): return True
    return False

async def press(pg, sel):
    ok = await pg.evaluate("s => { const e = document.querySelector(s); if (!e) return false; e.click(); return true; }", sel)
    await pg.wait_for_timeout(160)
    return ok

async def open_group(pg, gid):
    """a group opens on its name; tapping an open group's name closes it, so only a closed one is tapped"""
    return await pg.evaluate("g => { const h = document.querySelector(`#nav-groups [data-mnhead=\"${g}\"]`); if (!h) return false;"
                             " if (h.getAttribute('aria-expanded') !== 'true') h.click(); return document.querySelector(`#nav-groups [data-mnhead=\"${g}\"]`).getAttribute('aria-expanded') === 'true'; }", gid)

def kid_sel(gid, k):
    return f'#nav-groups [data-mngr="{gid}"] button[data-v="{k["v"]}"]' + (f'[data-tab="{k["tab"]}"]' if k['tab'] else ':not([data-tab])') + (f'[data-pid="{k["pid"]}"]' if k['pid'] else '')

async def check_screen(c, pg, tag, errs, want_view=None, phone=False):
    st = await pg.evaluate(STATE)
    # The Brain and the Chief of Staff are tabs of the one assistant (assistant lane): their entries open it on that tab
    if want_view: c.ok(st['view'] == want_view or (st['view'] == 'pa' and st['folded'] == want_view), f'{tag}: opens {want_view}, got {st["view"]}')
    c.ok(heading_ok(st), f'{tag}: heading "{st["heading"]}" vs menu entry (entry "{st["ent"]}", group "{st["grp"]}", tab "{st["sub"]}", bar "{st["bar"]}")')
    c.ok(len(st['prim']) <= 1, f'{tag}: {len(st["prim"])} blue primary buttons {st["prim"][:3]}')
    # the phone's Tasks page carries its own header: one search, the filter, the add line (Alan, 2026-10-24, Phone.dc.html)
    c.ok(st['ask'] or st['view'] == 'pa' or (phone and st['view'] in ('tkall', 'tasks')), f'{tag}: no Ask button in the header')
    if phone: c.ok(st['sw'] <= st['w'], f'{tag}: scrolls sideways ({st["sw"]}px at {st["w"]})')
    c.ok(not errs, f'{tag}: page errors {errs[:2]}')
    del errs[:]
    return st

async def walk_menu(c, pg, u, errs, phone):
    """every entry pressed for real, its group opened by its name first; a job and its strip's tabs"""
    dev = 'phone' if phone else 'desktop'
    menu = lambda: pg.evaluate("() => { document.querySelector('.rail')?.classList.add('open'); }") if phone else asyncio.sleep(0)
    await menu()
    rail = await pg.evaluate(RAIL_JS)
    for g in rail:
        if not g['head']:
            await menu()
            await press(pg, f'#nav-groups button.mn-top[data-v="{g["v"]}"]')
            st = await check_screen(c, pg, f'{u} {dev} "{g["label"]}"', errs, g['v'], phone)
            c.ok(st['ent'] == g['label'], f'{u} {dev} "{g["label"]}": lit entry is "{st["ent"]}"')
            continue
        await menu()
        c.ok(await open_group(pg, g['grp']), f'{u} {dev}: "{g["label"]}" opens on its name')
        kids = await pg.evaluate(KIDS_JS, g['grp'])
        if (u, g['grp']) in KIDS:
            c.ok([k['label'] for k in kids] == KIDS[(u, g['grp'])], f'{u} {dev} {g["label"]} lists {[k["label"] for k in kids]}\n      want {KIDS[(u, g["grp"])]}')
        if g['grp'] == 'jobs':
            want = await pg.evaluate("() => mnJobItems(role()).map(x => x.l).concat(['All Projects'])")
            c.ok([k['label'] for k in kids] == want, f'{u} {dev} Projects lists {[k["label"] for k in kids]}, want the jobs then All Projects {want}')
        for k in kids:
            await menu()
            await open_group(pg, g['grp'])
            if not await press(pg, kid_sel(g['grp'], k)):
                c.ok(False, f'{u} {dev}: "{g["label"]} > {k["label"]}" not found'); continue
            st = await check_screen(c, pg, f'{u} {dev} "{g["label"]} > {k["label"]}"', errs, None if k['pid'] else k['v'], phone)
            got = await pg.evaluate("() => S.id") if k['pid'] else None
            c.ok(st['ent'] == k['label'], f'{u} {dev} "{g["label"]} > {k["label"]}": lit entry is "{st["ent"]}"')
            c.ok(st['grp'] == g['label'], f'{u} {dev} "{g["label"]} > {k["label"]}": lit group is "{st["grp"]}"')
            # every role's tap on a job opens that job (jpOpenJob, the one way into a job)
            if k['pid']: c.ok(got == k['pid'], f'{u} {dev}: the job "{k["label"]}" opens that job ({got}, {st["view"]})')
        # a job's tabs (the desktop's strip; on the phone the job's Overview lists them, job_structure_test): each opens
        # and lights itself, and the job stays lit under Projects
        if g['grp'] == 'jobs' and not phone and any(k['pid'] for k in kids):
            j = next(k for k in kids if k['pid'])
            await menu(); await open_group(pg, 'jobs'); await press(pg, kid_sel('jobs', j))
            subs = await pg.evaluate(SUB_JS)
            if u in JOB_TABS_FOR: c.ok(subs == JOB_TABS_FOR[u], f'{u} {dev} a job\'s tabs {subs}\n      want {JOB_TABS_FOR[u]}')
            n = await pg.evaluate("() => document.querySelectorAll('#subnav [data-mni]').length")
            for i in range(n):
                lab = await pg.evaluate("k => { const b = document.querySelectorAll('#subnav [data-mni]')[k]; return b ? (b.innerText || b.textContent).replace(/\\s+/g, ' ').replace(/\\s*\\d+$/, '').trim() : '' }", i)
                want = await pg.evaluate("k => (document.querySelectorAll('#subnav [data-mni]')[k] || {dataset: {}}).dataset.sub", i)
                await pg.evaluate("k => document.querySelectorAll('#subnav [data-mni]')[k].click()", i)
                await pg.wait_for_timeout(160)
                st = await check_screen(c, pg, f'{u} {dev} job "{j["label"]} > {lab}"', errs, want, phone)
                c.ok(st['sub'] == lab, f'{u} {dev} job "{j["label"]} > {lab}": lit tab is "{st["sub"]}"')
                c.ok(st['pid'] == j['pid'], f'{u} {dev} job "{j["label"]} > {lab}": the job is not lit under Projects ({st["ent"]})')

async def desktop(c, p, users):
    b, pg, errs = await open_app(p, False)
    for u in users:
        await sign_in(pg, u)
        v0 = await pg.evaluate('view')
        c.ok(v0 == HOME[u], f'{u}: signs in on {v0}, want {HOME[u]}')
        if u == 'u_klein':
            labels = await pg.evaluate(r"""() => [...document.querySelectorAll('#nav-groups button[data-grp]')].map(b => (b.innerText || b.textContent).replace(/\s+/g, ' ').replace(/\s*\d+\+?$/, '').trim())""")
            c.ok(labels == RAIL[u], f'{u}: rail {labels}\n      want {RAIL[u]}')
            continue
        rail = await pg.evaluate(RAIL_JS)
        labels = [r['label'] for r in rail]
        c.ok(labels == RAIL[u], f'{u}: rail {labels}\n      want {RAIL[u]}')
        r = await pg.evaluate(REACH_JS)
        c.ok(not r['orphans'], f'{u}: pages the role may open that no menu entry reaches: {r["orphans"]}')
        bad = await pg.evaluate(BADGE_JS)
        c.ok(not bad, f'{u}: menu numbers differ from their lists: {bad}')
        c.ok(not any(x['label'] == 'Ask' for x in rail), f'{u}: Ask is a menu item')
        await walk_menu(c, pg, u, errs, False)
        # Ask: the header button opens the assistant and lights itself
        await press(pg, '#tb-ask')
        st = await pg.evaluate(STATE)
        c.ok(st['view'] == 'pa' and st['askOn'], f'{u}: the Ask button opens Ask ({st["view"]}, lit {st["askOn"]})')
        # Chat: beside Ask for every office role (Alan, 2026-10-19: "Where's the chat?"); it opens the threads and lights itself
        if u not in FIELD:
            ch = await pg.evaluate("() => { const b = document.getElementById('tb-chat'); return !!b && !b.hidden && !!b.offsetParent; }")
            c.ok(ch, f'{u}: a Messages button in the header')
            if ch:
                await press(pg, '#tb-chat')
                st = await pg.evaluate("() => ({ view, on: document.getElementById('tb-chat').classList.contains('on'), list: !!document.querySelector('#v-chat .msg-side, #v-chat .msg-rows') })")
                c.ok(st['view'] == 'chat' and st['on'] and st['list'], f'{u}: the Chat button opens the threads and lights itself {st}')
        del errs[:]
    await b.close()

async def phone(c, p, users):
    b, pg, errs = await open_app(p, True)
    for u in users:
        if u == 'u_klein': continue
        await sign_in(pg, u)
        sel = '#tabbar button' if u in FIELD else '#mtabs button'
        bar = await pg.evaluate("s => [...document.querySelectorAll(s)].filter(b => b.getClientRects().length).map(b => (b.innerText || '').replace(/\\s+/g, ' ').replace(/\\s*\\d+$/, '').trim())", sel)
        c.ok(bar == PHONE_BAR[u], f'{u} phone: bar {bar}\n      want {PHONE_BAR[u]}')
        # at most four shortcuts (Alan, 2026-10-19), five where an approved board draws five (TodayPM, TodayForeman)
        cap = 5 if u in ('u_alan', 'u_angel') else 4
        c.ok(len([x for x in bar if x != 'More']) <= cap and 'Messages' in bar, f'{u} phone: at most {cap} shortcuts, Messages one of them {bar}')
        await check_screen(c, pg, f'{u} phone landing', errs, HOME[u], phone=True)
        n = await pg.evaluate("s => document.querySelectorAll(s).length", sel)
        for k in range(n):
            lab = bar[k] if k < len(bar) else ''
            if lab == 'More': continue
            await press(pg, f'{sel}:nth-child({k + 1})')
            st = await check_screen(c, pg, f'{u} phone bar "{lab}"', errs, phone=True)
            c.ok(st['bar'] == lab, f'{u} phone bar "{lab}": lit entry is "{st["bar"]}"')
        # the hamburger, top left, for every role (the phone's Tasks page carries it in its own header, Phone.dc.html)
        hb = await pg.evaluate("() => { const b = [document.getElementById('menu-btn'), document.querySelector('.view.on [data-tvmenu]')].find(x => x && x.offsetParent); if (!b) return null; const r = b.getBoundingClientRect(); return {x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height)}; }")
        c.ok(hb and hb['x'] < 60 and hb['y'] < 60 and hb['w'] >= 40 and hb['h'] >= 40, f'{u} phone: the menu button is at the top left, a full tap target {hb}')
        await press(pg, '#menu-btn')
        await pg.wait_for_timeout(250)
        opened = await pg.evaluate("() => { const r = document.querySelector('.rail'); return !!(r && r.classList.contains('open')) }")
        c.ok(opened, f'{u} phone: the menu button opens the menu')
        rail = await pg.evaluate(RAIL_JS)
        c.ok([x['label'] for x in rail] == RAIL[u], f'{u} phone: the menu reads {[x["label"] for x in rail]}')
        # every entry opens a page that does not scroll sideways
        await walk_menu(c, pg, u, errs, True)
        await press(pg, '#tb-ask')
        st = await pg.evaluate(STATE)
        c.ok(st['view'] == 'pa', f'{u} phone: the Ask button opens Ask ({st["view"]})')
        c.ok(st['sw'] <= st['w'], f'{u} phone Ask: scrolls sideways ({st["sw"]}px)')
        if u not in FIELD:
            # on the phone Chat is in the bottom bar, not the header (one place per screen size)
            hdr = await pg.evaluate("() => { const a = document.getElementById('tb-chat'); return !!(a && a.offsetParent); }")
            c.ok(not hdr, f'{u} phone: no second Chat button in the header')
        del errs[:]
    await b.close()

async def main():
    args = sys.argv[1:]
    users = args[args.index('--user') + 1].split(',') if '--user' in args else list(RAIL)
    c = Checks()
    async with async_playwright() as p:
        if '--phone' not in args: await desktop(c, p, users)
        if '--desktop' not in args: await phone(c, p, users)
    return c.done()

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
