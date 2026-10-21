"""menu_test: each role's menu is pinned so it cannot drift again (BACKLOG §1.15; docs/MENU_DRAFT.md, the Navigation and
Pages Workshop's recommended menus, every bracketed recommendation adopted by Alan on 2026-10-19).

For every role in the SmartDesign workspace, on desktop (1440x900) and phone (390x844), it checks:
  MENU      the rail reads exactly the decided menu, top to bottom, with More and Settings at the foot; the office
            roles' phone bar and the field roles' tab bar read exactly their decided 4-5 daily pages
  HOME      sign-in opens the role's first page (Billing on Billing, the controller on Banking, the designer on Today)
  REACH     every page the role may open (ROLE_VIEWS) is reachable from the menu: a rail entry, a sub-tab, More, Settings,
            or the Ask button. Nothing is orphaned. A page cut from the daily menu sits under More; CUTS lists them.
  OPEN      every rail entry and every sub-tab, pressed for real, opens its page and lights itself
  HEADING   the page heading reads as the menu entry that is lit (rail group, else sub-tab), as the screen lint reads it
  ASK       the Ask button is in the header on every screen; pressing it opens Ask and lights it; Ask is no menu item
  PRIMARY   at most one blue primary button on each screen the menu opens
  PHONE     at 390px: no sideways scroll on any page the bar or the menu opens; More (office) and the menu button (field)
            open the rest one tap away
  BADGE     a group's badge is its overview's needs(); Today's is the approvals queue; Billing's is billingNeeds()
Usage: python3 menu_test.py [--user u_owner,...] [--desktop|--phone]
"""
import asyncio, re, sys
from harness import *

ICON_NEW = 'Ask'
# The decided menus (docs/MENU_DRAFT.md "Recommended menus"). Rail: top level, then More and Settings at the foot.
RAIL = {
    'u_owner': ['Today', 'Projects', 'Accounting', 'Sales', 'Clients', 'Purchasing', 'Design', 'Company', 'Reports', 'More', 'Settings'],
    'u_alan': ['Today', 'Projects', 'Clients', 'Purchasing', 'Reports', 'Company', 'More', 'Settings'],
    'u_chen': ['Today', 'Purchasing', 'Vendors', 'Projects', 'Company', 'More', 'Settings'],
    'u_billing': ['Billing', 'Today', 'Clients', 'Projects', 'Banking', 'Reports', 'More', 'Settings'],
    'u_controller': ['Banking', 'Bills & Payroll', 'Today', 'Ledger', 'Purchasing', 'Billing', 'Reports', 'More', 'Settings'],
    'u_sarah': ['Today', 'Drawings', 'Projects', 'Design', 'Clients', 'Dashboard', 'Settings'],
    # field roles: one list, the tab bar first, then the rest, then Connections and the Standard
    'u_angel': ['Today', 'Site', 'Daily Log', 'Chat', 'Requests', 'Crew', 'Drawings', 'Schedule', 'Photos', 'Documents', 'Raise', 'Connections', 'The SmartDesign Standard'],
    'u_alberto': ['Clock', 'Requests', 'Schedule', 'Chat', 'Photos', 'Deliveries', 'Drawings', 'Connections', 'The SmartDesign Standard'],
    'u_alex': ['Route', 'Chat', 'Clock', 'Receipts', 'Requests', 'Connections', 'The SmartDesign Standard'],
    # the client portal keeps its own menu (out of scope; Klein took no part in the workshop)
    'u_klein': ['Overview', 'Schedule', 'Decisions', 'Account', 'Chat'],
}
# The sub-tab strip of the groups the workshop reshaped, sections captioned.
STRIPS = {
    ('u_owner', 'jobs'): ['Projects', 'Overview', 'Project Settings', '[Plan]', 'Schedule', 'Tasks', 'Decisions', 'Submittals', 'Permits',
                          '[Field]', 'Field', 'Photos', 'Deliveries', 'Materials', '[Costs & Billing]', 'Costs', 'Change Orders', 'Estimates',
                          '[Files & Mail]', 'Documents', 'Drawings', 'Mail'],
    ('u_alan', 'jobs'): ['Projects', 'Overview', 'Project Settings', '[Plan]', 'Schedule', 'Tasks', 'Decisions', 'Submittals', 'Permits',
                         '[Field]', 'Field', 'Photos', 'Deliveries', 'Materials', '[Costs & Billing]', 'Costs', 'Change Orders', 'Estimates', 'Billing',
                         '[Files & Mail]', 'Documents', 'Drawings', 'Mail'],
    ('u_owner', 'home'): ['Today', 'Approvals', 'Inbox', 'Tasks'],
    ('u_owner', 'money'): ['Accounting', 'Bills & Payroll', 'Time & Crew', 'Banking', 'Spend', 'Billing', 'Ledger', 'Controls', 'Budget'],
    ('u_owner', 'buy'): ['Purchasing', '[Buy]', 'Requests', 'Buy Board', 'RFQs', 'Purchase Orders', '[Receive]', 'Deliveries', 'Route',
                         '[Vendors & Stock]', 'Vendors', 'Inventory'],
    ('u_owner', 'studio'): ['Design', 'Project Board', 'Drawings', 'Filings', 'Selections'],
    ('u_owner', 'office'): ['Company', 'Calendar', 'Meetings', 'The Brain', 'Obligations'],
    ('u_owner', 'reports'): ['Reports', 'Dashboard'],
    ('u_owner', 'setup'): ['Settings', 'Connections', 'The SmartDesign Standard', 'Problem Reports', 'Your Own Data', 'Sales Settings'],
    ('u_chen', 'buy'): ['Purchasing', '[Buy]', 'Selections', 'Requests', 'Buy Board', 'RFQs', 'Purchase Orders', '[Receive]', 'Deliveries', 'Route',
                        '[Stock]', 'Inventory'],
    ('u_controller', 'bank'): ['Banking', 'Spend'],
    ('u_controller', 'ap'): ['Bills & Payroll', 'Time & Crew'],
    ('u_controller', 'gl'): ['Ledger', 'Controls', 'Budget'],
    ('u_controller', 'buy'): ['Purchasing', 'Purchase Orders', 'Vendors'],
    ('u_sarah', 'home'): ['Today', 'Inbox', 'Tasks'],
    ('u_sarah', 'studio'): ['Design', 'Project Board', 'Filings', 'Selections'],
}
# Pages cut from each role's daily menu (the workshop's cut list and the decided menus). Each is still one tap away
# under More; nothing a role could open before is lost. A page that lands here without being listed fails the test:
# place it in MENU (src/app.js, the menu section) or add it here on purpose.
# 2026-10-21 (CONSOLIDATION §2.1, the tasks lane): Sales Tasks (hbtasks) and the owner's and PM's My Day (sday) are no
# longer pages: they are Tasks with the Sales chip and with Mine (their old ids forward there); the crew's Tasks page
# left the crew's menu (Clock is their list; the old id lands on Clock).
CUTS = {
    'u_owner': ['cos'],
    # PMs do not get Sales, Design or Accounting by default (open question 4, workshop cut list)
    'u_alan': ['bank', 'ap', 'time', 'spend', 'verify', 'ovmoney', 'hbcontacts', 'hbcompanies', 'ovsales', 'partners',
               'playbook', 'salesnum', 'sboard', 'sfile', 'ovstudio', 'cos'],
    # Sales and Time & Crew leave the coordinator's rail
    'u_chen': ['time', 'hbcontacts', 'hbcompanies', 'hbforecast', 'hbdash', 'ovsales', 'partners', 'playbook', 'clients',
               'dashboard', 'cos'],
    'u_billing': ['ap', 'spend', 'ovmoney', 'hbcontacts', 'hbcompanies', 'hbforecast', 'hbdash', 'ovsales', 'partners',
                  'playbook', 'vendors', 'meetings', 'cos'],
    'u_controller': ['ovjobs', 'ovmoney', 'clients', 'meetings', 'calendar', 'brain', 'obligations', 'ovoffice', 'cos'],
    'u_sarah': ['dashboard'],
    'u_angel': [], 'u_alberto': [], 'u_alex': [],
}
HOME = {'u_owner': 'home', 'u_alan': 'home', 'u_chen': 'home', 'u_billing': 'billing', 'u_controller': 'bank', 'u_sarah': 'sday',
        'u_angel': 'ftoday', 'u_alberto': 'time', 'u_alex': 'route', 'u_klein': 'client'}
# Phone: the office roles' bottom bar (then More), the field roles' tab bar.
PHONE_BAR = {
    # four shortcuts at most, Chat one of them (Alan, 2026-10-19: "The chat should be in the bottom main menu. And you
    # need to have a max of 4 shortcuts there"); everyone opens the rest from the hamburger at the top left ("the
    # hamburger menu should be on the top left of the page"), so the office bar has no More
    'u_owner': ['Today', 'Chat', 'Projects', 'Accounting'],
    'u_alan': ['Today', 'Chat', 'Projects', 'Field'],
    'u_chen': ['Today', 'Chat', 'Requests', 'Buy Board'],
    'u_billing': ['Billing', 'Today', 'Chat', 'Clients'],
    'u_controller': ['Banking', 'Today', 'Chat', 'Bills & Payroll'],
    'u_sarah': ['Today', 'Chat', 'Drawings', 'Projects'],
    'u_angel': ['Today', 'Site', 'Daily Log', 'Chat'],
    'u_alberto': ['Clock', 'Requests', 'Schedule', 'Chat'],
    'u_alex': ['Route', 'Chat', 'Clock', 'Receipts'],
}
FIELD = {'u_angel', 'u_alberto', 'u_alex'}

STATE = r"""() => {
  const vis = el => { if (!el) return false; const r = el.getBoundingClientRect(), s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  const txt = el => el ? (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim() : '';
  const strip = el => txt(el).replace(/\s*\d+\+?$/, '').trim();
  const v = document.querySelector('.view.on');
  let h = v && ([...v.querySelectorAll('h1')].find(vis) || [...v.querySelectorAll('h2')].find(vis));
  const cr = document.querySelector('#crumbs b');
  if (innerWidth <= 760 && v && v.querySelector('.ph h2.td-in-hdr, .td-ph h2.td-in-hdr') && vis(cr)) h = cr;
  const grp = document.querySelector('#nav-groups button.on'), sub = document.querySelector('#subnav .sub-tabs button.on');
  const bar = [...document.querySelectorAll('#mtabs button.on, #tabbar button.on')].find(vis);
  const ask = document.getElementById('tb-ask');
  return { view, folded: typeof paMenuView === 'function' ? paMenuView() : '', heading: txt(h), grp: grp ? strip(grp) : '', grpId: grp ? grp.dataset.grp : '', sub: sub && vis(sub) ? strip(sub) : '',
    bar: bar ? strip(bar) : '', ask: !!(ask && !ask.hidden && vis(ask)), askOn: !!(ask && ask.classList.contains('on')),
    prim: [...(v ? v.querySelectorAll('.btn.primary') : [])].filter(vis).map(txt),
    sw: document.documentElement.scrollWidth, w: innerWidth };
}"""
RAIL_JS = r"""() => [...document.querySelectorAll('#nav-groups > button')].map(b => ({ grp: b.dataset.grp, v: b.dataset.v,
  label: (b.innerText || b.textContent).replace(/\s+/g, ' ').replace(/\s*\d+\+?$/, '').trim(), n: +((b.querySelector('.n') || {}).textContent || 0) }))"""
SUB_JS = r"""() => [...document.querySelectorAll('#subnav .sub-tabs > *')].map(e => e.dataset && e.dataset.sub ? (e.innerText || e.textContent).replace(/\s+/g, ' ').replace(/\s*\d+\+?$/, '').trim() : '[' + e.textContent.trim() + ']')"""
REACH_JS = r"""() => { const m = mnMap(), rv = (ROLE_VIEWS[role()] || []).filter((v, i, a) => a.indexOf(v) === i), mb = typeof MB_VIEWS !== 'undefined' ? MB_VIEWS : [];
  const items = (m.field ? m.bar.concat(m.rest) : m.groups.flatMap(g => g.items)).concat(m.more, m.bottom).map(s => s.split('=')[0].split(':')[0]);
  const placed = new Set(items), out = [];
  rv.forEach(v => { if (mb.includes(v) || placed.has(v) || MN_BUTTON.has(v) || ['client', 'clacct'].includes(v)) return;
    const a = MN_ALIAS[v]; if (a && placed.has(a)) return;
    if (MN_QUIET.has(v)) return;   // retired: listed while open, under its group
    out.push(v); });
  return { orphans: out, more: m.more.map(s => s.split('=')[0]), home: m.home }; }"""
BADGE_JS = r"""() => { const out = []; document.querySelectorAll('#nav-groups > button').forEach(b => { const g = b.dataset.grp, n = +((b.querySelector('.n') || {}).textContent || 0);
  let want = null; const rv = ROLE_VIEWS[role()] || [];
  if (OV_VIEW[g] && rv.includes(OV_VIEW[g]) && b.dataset.v === OV_VIEW[g]) want = needs(g);
  else if (g === 'home' && rv.includes('mapprove')) want = mApproveCount();
  else if (g === 'billing') want = billingNeeds();
  if (want !== null && want !== n) out.push(`${g} shows ${n}, its list holds ${want}`); }); return out; }"""
NORM = lambda s: re.sub(r'\s+', ' ', (s or '').replace('&', 'and')).strip().lower()

def heading_ok(st):
    h = NORM(st['heading'])
    for l in (st['sub'], st['grp'], st['bar']):
        l = NORM(l)
        if l and (h == l or h.startswith(l + ' — ') or h.startswith(l + ' · ')): return True
    return False

async def press(pg, sel):
    ok = await pg.evaluate("s => { const e = document.querySelector(s); if (!e) return false; e.click(); return true; }", sel)
    await pg.wait_for_timeout(160)
    return ok

async def check_screen(c, pg, tag, errs, want_view=None, phone=False):
    st = await pg.evaluate(STATE)
    # The Brain and the Chief of Staff are tabs of the one assistant (assistant lane): their entries open it on that tab
    if want_view: c.ok(st['view'] == want_view or (st['view'] == 'pa' and st['folded'] == want_view), f'{tag}: opens {want_view}, got {st["view"]}')
    c.ok(heading_ok(st), f'{tag}: heading "{st["heading"]}" vs menu entry (group "{st["grp"]}", sub-tab "{st["sub"]}", bar "{st["bar"]}")')
    c.ok(len(st['prim']) <= 1, f'{tag}: {len(st["prim"])} blue primary buttons {st["prim"][:3]}')
    c.ok(st['ask'] or st['view'] == 'pa', f'{tag}: no Ask button in the header')
    if phone: c.ok(st['sw'] <= st['w'], f'{tag}: scrolls sideways ({st["sw"]}px at {st["w"]})')
    c.ok(not errs, f'{tag}: page errors {errs[:2]}')
    del errs[:]
    return st

async def desktop(c, p, users):
    b, pg, errs = await open_app(p, False)
    for u in users:
        await sign_in(pg, u)
        v0 = await pg.evaluate('view')
        c.ok(v0 == HOME[u], f'{u}: signs in on {v0}, want {HOME[u]}')
        rail = await pg.evaluate(RAIL_JS)
        labels = [r['label'] for r in rail]
        c.ok(labels == RAIL[u], f'{u}: rail {labels}\n      want {RAIL[u]}')
        if u == 'u_klein': continue
        r = await pg.evaluate(REACH_JS)
        c.ok(not r['orphans'], f'{u}: pages the role may open that no menu entry reaches: {r["orphans"]}')
        c.ok(sorted(r['more']) == sorted(CUTS[u]), f'{u}: More holds {r["more"]}; cut list {CUTS[u]} (a new page lands in More: place it or list it)')
        bad = await pg.evaluate(BADGE_JS)
        c.ok(not bad, f'{u}: rail badges differ from their lists: {bad}')
        c.ok(not any(x['label'] == 'Ask' for x in rail), f'{u}: Ask is a menu item')
        # every rail entry, then every sub-tab of its group, pressed for real
        for i, g in enumerate(rail):
            await press(pg, f'#nav-groups > button:nth-child({i + 1})')
            st = await check_screen(c, pg, f'{u} desktop rail "{g["label"]}"', errs, g['v'])
            c.ok(st['grp'] == g['label'], f'{u} desktop rail "{g["label"]}": lit entry is "{st["grp"]}"')
            subs = await pg.evaluate(SUB_JS)
            if (u, g['grp']) in STRIPS:
                c.ok(subs == STRIPS[(u, g['grp'])], f'{u} {g["grp"]} strip {subs}\n      want {STRIPS[(u, g["grp"])]}')
            n = await pg.evaluate("() => document.querySelectorAll('#subnav [data-mni]').length")
            for k in range(n):
                lab = await pg.evaluate("k => { const b = document.querySelector(`#subnav [data-mni='${k}']`); return b ? (b.innerText || b.textContent).replace(/\\s+/g, ' ').replace(/\\s*\\d+$/, '').trim() : '' }", k)
                want = await pg.evaluate("k => (document.querySelector(`#subnav [data-mni='${k}']`) || {dataset: {}}).dataset.sub", k)
                if not await press(pg, f"#subnav [data-mni='{k}']"):
                    # a quiet (retired) page drops out of the strip once another page is open
                    continue
                st = await check_screen(c, pg, f'{u} desktop "{g["label"]} > {lab}"', errs, want)
                c.ok(st['sub'] == lab, f'{u} desktop "{g["label"]} > {lab}": lit sub-tab is "{st["sub"]}"')
                c.ok(st['grp'] == g['label'], f'{u} desktop "{g["label"]} > {lab}": lit group is "{st["grp"]}"')
        # Ask: the header button opens the assistant and lights itself
        await press(pg, '#tb-ask')
        st = await pg.evaluate(STATE)
        c.ok(st['view'] == 'pa' and st['askOn'], f'{u}: the Ask button opens Ask ({st["view"]}, lit {st["askOn"]})')
        # Chat: beside Ask for every office role (Alan, 2026-10-19: "Where's the chat?"); it opens the threads and lights itself
        if u not in FIELD:
            ch = await pg.evaluate("() => { const b = document.getElementById('tb-chat'); return !!b && !b.hidden && !!b.offsetParent; }")
            c.ok(ch, f'{u}: a Chat button in the header')
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
        c.ok(len([x for x in bar if x != 'More']) <= 4 and 'Chat' in bar, f'{u} phone: at most four shortcuts, Chat one of them {bar}')
        await check_screen(c, pg, f'{u} phone landing', errs, HOME[u], phone=True)
        n = await pg.evaluate("s => document.querySelectorAll(s).length", sel)
        for k in range(n):
            lab = bar[k] if k < len(bar) else ''
            if lab == 'More': continue
            await press(pg, f'{sel}:nth-child({k + 1})')
            st = await check_screen(c, pg, f'{u} phone bar "{lab}"', errs, phone=True)
            c.ok(st['bar'] == lab, f'{u} phone bar "{lab}": lit entry is "{st["bar"]}"')
        # the rest is one tap away: More (office) or the menu button (field) opens the whole menu
        # the hamburger, top left, for every role
        hb = await pg.evaluate("() => { const b = document.getElementById('menu-btn'); if (!b || !b.offsetParent) return null; const r = b.getBoundingClientRect(); return {x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height)}; }")
        c.ok(hb and hb['x'] < 60 and hb['y'] < 60 and hb['w'] >= 40 and hb['h'] >= 40, f'{u} phone: the menu button is at the top left, a full tap target {hb}')
        await press(pg, '#menu-btn')
        await pg.wait_for_timeout(250)
        opened = await pg.evaluate("() => { const r = document.querySelector('.rail'); return !!(r && r.classList.contains('open')) }")
        c.ok(opened, f'{u} phone: the menu button opens the menu')
        rail = await pg.evaluate(RAIL_JS)
        c.ok([x['label'] for x in rail] == RAIL[u], f'{u} phone: the menu reads {[x["label"] for x in rail]}')
        # every rail entry opens a page that does not scroll sideways
        for i, g in enumerate(rail):
            await pg.evaluate("() => { document.querySelector('.rail')?.classList.add('open'); }")
            await press(pg, f'#nav-groups > button:nth-child({i + 1})')
            await check_screen(c, pg, f'{u} phone menu "{g["label"]}"', errs, g['v'], phone=True)
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
