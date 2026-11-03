"""menu_order_test: the menu Alan approved on 11-03 (docs/DECISIONS.md, the 11-03 row; docs/mockups/job-structure:
MenuNow and Main for the phone, Desk's left rail for the desktop). From his 10-27 recording: "the menu itself is just
extremely messy, and the order of everything is not great"; a number beside every item; "do we need the arrow? It could
be better if you just press Projects and then it comes down."

Done as the person, for every staff role, on the phone (390x844, touch, the menu opened from its button) and the desktop
(1440x900, the rail):
  ORDER    the menu reads, top to bottom: Your Day (Today, Tasks, Messages), Work (Projects, Purchasing, Sales and
           Clients, Accounting, Design, Reports), then Company and Settings and Record a Feedback Session at the foot;
           each role sees only the entries ROLE_VIEWS lets it open (a group with nothing for the role is not drawn).
           The field roles keep a short, field-first list under the same headings.
  ONCE     no page appears twice in the menu (Tasks once), and no entry opens a page the role may not open.
  OPEN     a group opens when its name is tapped: the whole row is the target, no arrow icon, the page does not change
           and the phone's menu stays open; one group open at a time (tap another, the first closes; tap again, it
           closes).
  NUMBERS  numbers only on entries that open a page, never on a group's name; one style (a filled badge); each equals
           what the page it opens shows for that person (its marked count, Today's Late chip, Messages' tabs, Billing's
           "N to bill or send"). A number with nothing on its page to match is a plain count and fails.
  REACH    every entry of the old menu (master 4c32735, pinned below as OLD) still opens its page, from the new menu
           (a group's page, a job's tab, Today's Approvals link, or the page an old name now forwards to). The table
           old -> new is printed for every role.
  JOB      (desktop and phone) Projects lists the person's jobs, then All Projects; a job opened from it is lit under
           Projects and its group stays open.
  PHONE    at 390: the open menu never scrolls sideways; every entry is at least 44px tall.
  LABELS   Title Case on captions, groups and entries (job names are data, not labels); each top entry and group has a
           line icon; no glyphs standing in for icons.
Screenshots per role and device: review/menu_order/ (the menu open, one group open; the desktop on a job).
Usage: python3 menu_order_test.py [--user u_owner,...] [--desktop|--phone] [--no-reach]
"""
import asyncio, json, os, re, sys
from harness import *

SHOTS = os.path.join(ROOT, 'review', 'menu_order')
OFFICE = ['u_owner', 'u_alan', 'u_chen', 'u_billing', 'u_controller', 'u_sarah']
FIELD = ['u_angel', 'u_alberto', 'u_alex']
STAFF = OFFICE + FIELD
DAY, WORK = '[Your Day]', '[Work]'
FOOT = ['Company and Settings', 'Record a Feedback Session']
W6 = ['Projects', 'Purchasing', 'Sales and Clients', 'Accounting', 'Design', 'Reports']
# The approved order, filtered by what each role may open (ROLE_VIEWS on master; this lane adds no page to any role).
ORDER = {
    'u_owner': [DAY, 'Today', 'Tasks', 'Messages', WORK] + W6 + FOOT,
    'u_alan': [DAY, 'Today', 'Tasks', 'Messages', WORK] + W6 + FOOT,
    'u_chen': [DAY, 'Today', 'Tasks', 'Messages', WORK] + W6 + FOOT,
    # billing and the controller open no design page; the designer no purchasing or accounting page
    'u_billing': [DAY, 'Today', 'Tasks', 'Messages', WORK, 'Projects', 'Purchasing', 'Sales and Clients', 'Accounting', 'Reports'] + FOOT,
    'u_controller': [DAY, 'Today', 'Tasks', 'Messages', WORK, 'Projects', 'Purchasing', 'Sales and Clients', 'Accounting', 'Reports'] + FOOT,
    'u_sarah': [DAY, 'Today', 'Tasks', 'Messages', WORK, 'Projects', 'Sales and Clients', 'Design', 'Reports'] + FOOT,
    # the field: short and field-first, the role's own day page and Messages, then the job's pages in the bar's order
    'u_angel': [DAY, 'Today', 'Messages', WORK, 'Daily Log', 'Site', 'Requests', 'Crew', 'Drawings', 'Schedule', 'Photos', 'Documents', 'Raise'] + FOOT,
    'u_alberto': [DAY, 'Clock', 'Messages', WORK, 'Requests', 'Schedule', 'Photos', 'Deliveries', 'Drawings'] + FOOT,
    'u_alex': [DAY, 'Route', 'Messages', WORK, 'Clock', 'Receipts', 'Requests'] + FOOT,
}
GROUPS = set(W6) | {'Company and Settings'}

# The menu on master 4c32735, read from mnMap() for each role: (where it sat, "view[:tab]=Label"). Every one of these
# must still open its page from the new menu.
OLD = {
    'u_owner': [
        ('Today', 'home=Today'), ('Today', 'mapprove=Approvals'), ('Today', 'tkall=Tasks'), ('Tasks', 'tkall=Tasks'),
        ('Messages', 'chat=Messages'), ('Projects', 'ovjobs=Projects'), ('Projects', 'dash=Overview'),
        ('Projects', 'proj=Project Settings'), ('Projects', 'sched=Schedule'), ('Projects', 'tasks=Tasks'),
        ('Projects', 'dec=Decisions'), ('Projects', 'subm=Submittals'), ('Projects', 'insp=Permits'),
        ('Projects', 'field=Field'), ('Projects', 'photos=Photos'), ('Projects', 'recv=Deliveries'),
        ('Projects', 'mat=Materials'), ('Projects', 'costs=Costs'), ('Projects', 'billing:co=Change Orders'),
        ('Projects', 'billing:estimates=Estimates'), ('Projects', 'files=Documents'), ('Projects', 'plans=Drawings'),
        ('Projects', 'inbox=Mail'), ('Accounting', 'ovmoney=Accounting'), ('Accounting', 'ap=Bills & Payroll'),
        ('Accounting', 'time=Time & Crew'), ('Accounting', 'bank=Banking'), ('Accounting', 'spend=Spend'),
        ('Accounting', 'billing=Billing'), ('Accounting', 'gl=Ledger'), ('Accounting', 'verify=Controls'),
        ('Accounting', 'budget=Budget'), ('Sales', 'ovsales=Sales'), ('Sales', 'billing:estimates=Estimates'),
        ('Sales', 'salesnum=Numbers'), ('Sales', 'partners=Partners'), ('Sales', 'playbook=Playbook'),
        ('Clients', 'clients=Clients'), ('Purchasing', 'proc=Buy Board'), ('Purchasing', 'rfq=Quotes'),
        ('Purchasing', 'po=Orders'), ('Purchasing', 'recv=Deliveries'), ('Purchasing', 'vendors=Vendors'),
        ('Purchasing', 'inv=Stock'), ('Design', 'ovstudio=Design'), ('Design', 'sboard=Project Board'),
        ('Design', 'plans=Drawings'), ('Design', 'sfile=Filings'), ('Design', 'sel=Selections'),
        ('Company', 'ovoffice=Company'), ('Company', 'calendar=Calendar'), ('Company', 'team=Team'),
        ('Company', 'meetings=Meetings'), ('Company', 'brain=The Brain'), ('Company', 'obligations=Obligations'),
        ('Reports', 'reports=Reports'), ('Reports', 'dashboard=Dashboard'), ('More', 'req=Requests'),
        ('More', 'route=Route'), ('More', 'cos=Chief of Staff'), ('Settings', 'setup=Settings'),
        ('Settings', 'conn=Connections'), ('Settings', 'standard=The SmartDesign Standard'),
        ('Settings', 'rpbox=Problem Reports'), ('Settings', 'rdata=Your Own Data'),
        ('Settings', 'hbsettings=Sales Settings'),
    ],
    'u_alan': [
        ('Today', 'home=Today'), ('Today', 'mapprove=Approvals'), ('Today', 'tkall=Tasks'), ('Tasks', 'tkall=Tasks'),
        ('Messages', 'chat=Messages'), ('Projects', 'ovjobs=Projects'), ('Projects', 'dash=Overview'),
        ('Projects', 'proj=Project Settings'), ('Projects', 'sched=Schedule'), ('Projects', 'tasks=Tasks'),
        ('Projects', 'dec=Decisions'), ('Projects', 'subm=Submittals'), ('Projects', 'insp=Permits'),
        ('Projects', 'field=Field'), ('Projects', 'photos=Photos'), ('Projects', 'recv=Deliveries'),
        ('Projects', 'mat=Materials'), ('Projects', 'costs=Costs'), ('Projects', 'billing:co=Change Orders'),
        ('Projects', 'billing:estimates=Estimates'), ('Projects', 'billing=Billing'), ('Projects', 'files=Documents'),
        ('Projects', 'plans=Drawings'), ('Projects', 'inbox=Mail'), ('Estimates', 'billing:estimates=Estimates'),
        ('Clients', 'clients=Clients'), ('Purchasing', 'proc=Buy Board'), ('Purchasing', 'rfq=Quotes'),
        ('Purchasing', 'po=Orders'), ('Purchasing', 'recv=Deliveries'), ('Purchasing', 'vendors=Vendors'),
        ('Purchasing', 'inv=Stock'), ('Reports', 'reports=Reports'), ('Reports', 'dashboard=Dashboard'),
        ('Company', 'ovoffice=Company'), ('Company', 'calendar=Calendar'), ('Company', 'team=Team'),
        ('Company', 'meetings=Meetings'), ('Company', 'brain=The Brain'), ('Company', 'obligations=Obligations'),
        ('More', 'bank=Banking'), ('More', 'ap=Bills & Payroll'), ('More', 'time=Time & Crew'), ('More', 'spend=Spend'),
        ('More', 'verify=Controls'), ('More', 'ovmoney=Accounting'), ('More', 'ovsales=Sales'),
        ('More', 'partners=Partners'), ('More', 'playbook=Playbook'), ('More', 'salesnum=Numbers'),
        ('More', 'req=Requests'), ('More', 'route=Route'), ('More', 'sboard=Project Board'), ('More', 'sfile=Filings'),
        ('More', 'sel=Selections'), ('More', 'ovstudio=Design'), ('More', 'cos=Chief of Staff'),
        ('Settings', 'setup=Settings'), ('Settings', 'conn=Connections'),
        ('Settings', 'standard=The SmartDesign Standard'), ('Settings', 'rpbox=Problem Reports'),
        ('Settings', 'hbsettings=Sales Settings'),
    ],
    'u_chen': [
        ('Today', 'home=Today'), ('Today', 'mapprove=Approvals'), ('Today', 'tkall=Tasks'), ('Tasks', 'tkall=Tasks'),
        ('Messages', 'chat=Messages'), ('Purchasing', 'proc=Buy Board'), ('Purchasing', 'rfq=Quotes'),
        ('Purchasing', 'po=Orders'), ('Purchasing', 'recv=Deliveries'), ('Purchasing', 'vendors=Vendors'),
        ('Purchasing', 'inv=Stock'), ('Projects', 'ovjobs=Projects'), ('Projects', 'dash=Overview'),
        ('Projects', 'proj=Project Settings'), ('Projects', 'sched=Schedule'), ('Projects', 'tasks=Tasks'),
        ('Projects', 'dec=Decisions'), ('Projects', 'subm=Submittals'), ('Projects', 'insp=Permits'),
        ('Projects', 'field=Field'), ('Projects', 'photos=Photos'), ('Projects', 'recv=Deliveries'),
        ('Projects', 'mat=Materials'), ('Projects', 'files=Documents'), ('Projects', 'plans=Drawings'),
        ('Projects', 'inbox=Mail'), ('Company', 'ovoffice=Company'), ('Company', 'calendar=Calendar'),
        ('Company', 'team=Team'), ('Company', 'meetings=Meetings'), ('Company', 'brain=The Brain'),
        ('Company', 'obligations=Obligations'), ('More', 'time=Time & Crew'), ('More', 'hbforecast=Forecast'),
        ('More', 'hbdash=Sales Dashboard'), ('More', 'ovsales=Sales'), ('More', 'partners=Partners'),
        ('More', 'playbook=Playbook'), ('More', 'clients=Clients'), ('More', 'req=Requests'), ('More', 'route=Route'),
        ('More', 'sel=Selections'), ('More', 'dashboard=Dashboard'), ('More', 'cos=Chief of Staff'),
        ('Settings', 'conn=Connections'), ('Settings', 'standard=The SmartDesign Standard'),
        ('Settings', 'rdata=Your Own Data'), ('Settings', 'hbsettings=Sales Settings'),
    ],
    'u_billing': [
        ('Billing', 'billing=Billing'), ('Today', 'home=Today'), ('Today', 'mapprove=Approvals'), ('Today', 'tkall=Tasks'),
        ('Tasks', 'tkall=Tasks'), ('Messages', 'chat=Messages'), ('Clients', 'clients=Clients'),
        ('Projects', 'ovjobs=Projects'), ('Projects', 'dash=Overview'), ('Projects', 'files=Documents'),
        ('Banking', 'bank=Banking'), ('Reports', 'reports=Reports'), ('Reports', 'dashboard=Dashboard'),
        ('More', 'ap=Bills & Payroll'), ('More', 'spend=Spend'), ('More', 'ovmoney=Accounting'),
        ('More', 'hbforecast=Forecast'), ('More', 'hbdash=Sales Dashboard'), ('More', 'ovsales=Sales'),
        ('More', 'partners=Partners'), ('More', 'playbook=Playbook'), ('More', 'vendors=Vendors'),
        ('More', 'meetings=Meetings'), ('More', 'team=Team'), ('More', 'cos=Chief of Staff'),
        ('Settings', 'conn=Connections'), ('Settings', 'standard=The SmartDesign Standard'),
        ('Settings', 'hbsettings=Sales Settings'),
    ],
    'u_controller': [
        ('Banking', 'bank=Banking'), ('Banking', 'spend=Spend'), ('Bills & Payroll', 'ap=Bills & Payroll'),
        ('Bills & Payroll', 'time=Time & Crew'), ('Today', 'home=Today'), ('Today', 'mapprove=Approvals'),
        ('Today', 'tkall=Tasks'), ('Tasks', 'tkall=Tasks'), ('Messages', 'chat=Messages'), ('Ledger', 'gl=Ledger'),
        ('Ledger', 'verify=Controls'), ('Ledger', 'budget=Budget'), ('Purchasing', 'ovbuy=Purchasing'),
        ('Purchasing', 'po=Orders'), ('Purchasing', 'vendors=Vendors'), ('Billing', 'billing=Billing'),
        ('Reports', 'reports=Reports'), ('Reports', 'dashboard=Dashboard'), ('More', 'ovjobs=Projects'),
        ('More', 'ovmoney=Accounting'), ('More', 'clients=Clients'), ('More', 'meetings=Meetings'),
        ('More', 'calendar=Calendar'), ('More', 'brain=The Brain'), ('More', 'obligations=Obligations'),
        ('More', 'ovoffice=Company'), ('More', 'team=Team'), ('More', 'cos=Chief of Staff'),
        ('Settings', 'setup=Settings'), ('Settings', 'conn=Connections'),
        ('Settings', 'standard=The SmartDesign Standard'),
    ],
    'u_sarah': [
        ('Today', 'sday=Today'), ('Today', 'tkall=Tasks'), ('Tasks', 'tkall=Tasks'), ('Messages', 'chat=Messages'),
        ('Drawings', 'plans=Drawings'), ('Projects', 'ovjobs=Projects'), ('Projects', 'sched=Schedule'),
        ('Projects', 'tasks=Tasks'), ('Projects', 'dec=Decisions'), ('Projects', 'photos=Photos'),
        ('Projects', 'files=Documents'), ('Design', 'ovstudio=Design'), ('Design', 'sboard=Project Board'),
        ('Design', 'sfile=Filings'), ('Design', 'sel=Selections'), ('Clients', 'clients=Clients'), ('More', 'team=Team'),
        ('More', 'dashboard=Dashboard'), ('Settings', 'conn=Connections'),
        ('Settings', 'standard=The SmartDesign Standard'),
    ],
    'u_angel': [
        ('Bar', 'ftoday=Today'), ('Bar', 'flog=Daily Log'), ('Bar', 'fsite=Site'), ('Bar', 'req=Requests'),
        ('Bar', 'chat=Messages'), ('Menu', 'fcrew=Crew'), ('Menu', 'plans=Drawings'), ('Menu', 'sched=Schedule'),
        ('Menu', 'photos=Photos'), ('Menu', 'files=Documents'), ('Menu', 'fraise=Raise'), ('Menu', 'team=Team'),
        ('Settings', 'conn=Connections'), ('Settings', 'standard=The SmartDesign Standard'),
    ],
    'u_alberto': [
        ('Bar', 'time=Clock'), ('Bar', 'req=Requests'), ('Bar', 'sched=Schedule'), ('Bar', 'chat=Messages'),
        ('Menu', 'files=Photos'), ('Menu', 'recv=Deliveries'), ('Menu', 'plans=Drawings'), ('Menu', 'team=Team'),
        ('Settings', 'conn=Connections'), ('Settings', 'standard=The SmartDesign Standard'),
    ],
    'u_alex': [
        ('Bar', 'route=Route'), ('Bar', 'chat=Messages'), ('Bar', 'time=Clock'), ('Bar', 'files=Receipts'),
        ('Menu', 'req=Requests'), ('Menu', 'team=Team'), ('Settings', 'conn=Connections'),
        ('Settings', 'standard=The SmartDesign Standard'),
    ],
}

# ---------------------------------------------------------------- reading the menu as it is drawn
MENU_JS = r"""() => {
  const W = document.getElementById('nav-groups'); if (!W) return [];
  const vis = e => !!e && e.getClientRects().length > 0 && getComputedStyle(e).visibility !== 'hidden' && !e.closest('[hidden]');
  const lab = e => { const c = e.cloneNode(true); c.querySelectorAll('.n, svg').forEach(x => x.remove()); return c.textContent.replace(/\s+/g, ' ').trim(); };
  const num = e => { const n = e.querySelector('.n'); const t = n ? n.textContent.trim() : ''; return /^\d+$/.test(t) ? +t : 0; };
  const nodes = [...W.querySelectorAll('.mn-cap, button[data-grp], [data-mnhead], [data-mnkid], #fbs-rail')];
  const fbs = document.getElementById('fbs-rail'); if (fbs && !W.contains(fbs)) nodes.push(fbs);
  return nodes.map((e, i) => { const r = e.getBoundingClientRect(), kid = !!e.closest('.mn-kids, .mn-gr');
    const g = e.dataset.grp || e.dataset.mnhead || ((e.closest('[data-mngr]') || {}).dataset || {}).mngr || '';
    return { i, kind: e.matches('.mn-cap') ? 'cap' : e.id === 'fbs-rail' ? 'fbs' : e.matches('[data-mnhead]') ? 'head' : kid ? 'kid' : 'top',
      label: lab(e), v: e.dataset.v || '', tab: e.dataset.tab || '', grp: g, pid: e.dataset.pid || '', n: num(e), vis: vis(e),
      exp: e.getAttribute('aria-expanded'), on: e.classList.contains('on') || e.getAttribute('aria-current') === 'page',
      h: Math.round(r.height), w: Math.round(r.width), svgs: e.querySelectorAll('svg').length,
      svgFirst: !!(e.firstElementChild && e.firstElementChild.tagName.toLowerCase() === 'svg'),
      arrow: !!e.querySelector('.mn-exp, [data-mnexp]') || !!(e.nextElementSibling && e.nextElementSibling.querySelector && e.nextElementSibling.querySelector(':scope > .mn-exp')),
      badge: (() => { const n = e.querySelector('.n'); if (!n || !n.textContent.trim()) return null; const s = getComputedStyle(n);
        return { bg: s.backgroundColor, radius: parseFloat(s.borderTopLeftRadius) || 0, color: s.color }; })() }; });
}"""
OPEN_JS = "() => { const r = document.querySelector('.rail'); return !!(r && r.classList.contains('open')); }"
STATE_JS = r"""() => ({ view, folded: typeof paMenuView === 'function' ? paMenuView() : '', billTab: typeof billTab !== 'undefined' ? billTab : '',
  pid: (typeof S !== 'undefined' && S) ? S.id : '', sw: document.documentElement.scrollWidth, w: innerWidth,
  open: !!(document.querySelector('.rail') || {classList: {contains: () => false}}).classList.contains('open') })"""
# what the page it opens shows: the number the page states for the same question
PAGE_N = r"""v => { const vis = e => !!e && e.getClientRects().length > 0;
  const first = s => { const m = String(s || '').match(/\d+/); return m ? +m[0] : 0; };
  const V = document.querySelector('.view.on'); if (!V) return null;
  if (v === 'home') { const c = [...V.querySelectorAll('.td-tabs [data-tdytabbtn="late"] .n, .td-tabs [data-tdytabbtn="late"]')].find(vis); return c ? { n: first(c.textContent), how: 'the Late chip' } : null; }
  if (v === 'chat') { const T = [...V.querySelectorAll('[data-p2nmt]')].filter(vis); if (!T.length) return null;
    return { n: T.reduce((a, b) => a + first((b.querySelector('.n') || b).textContent.replace(/^[^\d]*/, '')), 0), how: 'the sum of the Team, Mail and Field tabs' }; }
  if (v === 'billing') { const m = V.innerText.match(/(\d+) to bill or send/); return m ? { n: +m[1], how: '"N to bill or send"' } : null; }
  // the phone's Tasks page states its Due Soon on the chip (the marked line is the desktop's)
  if (v === 'tkall' && ![...V.querySelectorAll('[data-ocbadge="tkall"]')].some(vis)) { const q = [...V.querySelectorAll('.tv-qchips [data-tvqv="week"]')].find(vis);
    return q ? { n: first(q.textContent), how: 'the Due Soon chip' } : null; }
  const el = [...V.querySelectorAll(`[data-ocbadge="${v}"]`)].find(vis);
  if (!el) return null;
  const g = el.querySelector('.gl-v, b, .n'); return { n: first(g && /\d/.test(g.textContent) ? g.textContent : el.textContent), how: `its marked count "${el.innerText.replace(/\s+/g, ' ').slice(0, 40)}"` }; }"""

SMALL = {'and', 'or', 'of', 'the', 'a', 'an', 'to', 'for', 'in', 'on', 'at', 'by', 'with', '&'}
def title_case(s):
    return all(w[0].isupper() or w in SMALL or not w[0].isalpha() for w in s.replace('[', '').replace(']', '').split())

async def tap(pg, loc, phone):
    try:
        if phone: await loc.tap(timeout=4000)
        else: await loc.click(timeout=4000)
    except Exception as x:
        print('  (tap fell back to a DOM click:', getattr(loc, '_selector', '')[:120], str(x).splitlines()[0][:60] + ')')
        await loc.evaluate('e => e.click()')
    await pg.wait_for_timeout(220)

async def open_menu(pg, phone):
    if not phone: return
    if not await pg.evaluate(OPEN_JS):
        await tap(pg, pg.locator('#menu-btn:visible, .view.on [data-tvmenu]:visible').first, phone)
        await pg.wait_for_timeout(200)

async def head(pg, gid):
    return pg.locator(f'#nav-groups [data-mnhead="{gid}"]').first

async def ensure_open(pg, gid, phone):
    """open a group by tapping its name, unless it is open"""
    await open_menu(pg, phone)
    h = await head(pg, gid)
    if not await h.count(): return False
    if await h.get_attribute('aria-expanded') != 'true':
        await tap(pg, h, phone)
    return await h.get_attribute('aria-expanded') == 'true'

async def go_entry(pg, e, phone):
    """open a menu entry as the person: the menu (phone), its group by its name, then the entry"""
    await open_menu(pg, phone)
    if e['kind'] == 'kid' and not await ensure_open(pg, e['grp'], phone): return False
    sel = f'#nav-groups button[data-v="{e["v"]}"]' + (f'[data-tab="{e["tab"]}"]' if e['tab'] else ':not([data-tab])') + (f'[data-pid="{e["pid"]}"]' if e['pid'] else '')
    loc = pg.locator(sel).first
    if not await loc.count(): return False
    await tap(pg, loc, phone)
    await pg.wait_for_timeout(150)
    return True

def key(e): return f"{e['v']}:{e['tab']}" if e['tab'] else e['v']

async def shot(pg, name):
    try:
        os.makedirs(SHOTS, exist_ok=True)
        await pg.screenshot(path=os.path.join(SHOTS, name + '.png'))
    except Exception as x:
        print('shot', name, x)

# ---------------------------------------------------------------- one role, one device
async def run_role(c, pg, u, phone, errs, reach, table):
    dev = 'phone' if phone else 'desktop'
    tag = f'{u} {dev}'
    await sign_in(pg, u)
    await pg.evaluate("() => { document.querySelector('.rail')?.classList.remove('open'); document.getElementById('railscrim')?.classList.remove('on'); }")
    await open_menu(pg, phone)
    M = await pg.evaluate(MENU_JS)
    rv = set(await pg.evaluate("() => ROLE_VIEWS[role()] || []"))
    # ---- ORDER
    seq = [('[' + e['label'] + ']') if e['kind'] == 'cap' else e['label'] for e in M if e['kind'] in ('cap', 'top', 'head', 'fbs')]
    c.ok(seq == ORDER[u], f'{tag}: the menu reads\n      {seq}\n      want {ORDER[u]}')
    # ---- ONCE
    ent = [e for e in M if e['kind'] in ('top', 'kid')]
    keys = [key(e) + (':' + e['pid'] if e['pid'] else '') for e in ent]
    dup = sorted({k for k in keys if keys.count(k) > 1})
    c.ok(not dup, f'{tag}: a page listed twice: {dup}')
    labs = [e['label'] for e in ent if not e['pid']]
    c.ok(labs.count('Tasks') <= 1, f'{tag}: Tasks is listed {labs.count("Tasks")} times')
    dlab = sorted({l for l in labs if labs.count(l) > 1})
    c.ok(not dlab, f'{tag}: one label on two entries: {dlab}')
    bad = [key(e) for e in ent if not e['pid'] and e['v'] not in rv]
    c.ok(not bad, f'{tag}: entries for pages the role may not open: {bad}')
    # ---- LABELS and icons
    for e in M:
        if e['kind'] in ('cap', 'top', 'head', 'kid', 'fbs') and not e['pid']:
            c.ok(title_case(e['label']), f'{tag}: "{e["label"]}" is not in Title Case')
            c.ok(not re.search(r'[←-⇿✀-➿■-◿›‹\U0001F300-\U0001FAFF]', e['label']), f'{tag}: "{e["label"]}" carries a glyph')
        if e['kind'] in ('top', 'head') and e['vis']:
            c.ok(e['svgs'] == 1 and e['svgFirst'], f'{tag}: "{e["label"]}" has {e["svgs"]} icons (want one line icon before the name)')
    # ---- PHONE: the open menu at 390
    if phone:
        st = await pg.evaluate(STATE_JS)
        c.ok(st['sw'] <= st['w'], f'{tag}: the open menu scrolls sideways ({st["sw"]}px at {st["w"]})')
        short = [f"{e['label']} {e['h']}px" for e in M if e['vis'] and e['kind'] in ('top', 'head', 'kid', 'fbs') and e['h'] < 44]
        c.ok(not short, f'{tag}: entries under 44px tall: {short}')
    # ---- OPEN: a group opens on its name; one at a time; the page stays; the phone's menu stays open
    heads = [e for e in M if e['kind'] == 'head']
    c.ok(not any(e['arrow'] for e in M), f'{tag}: an arrow toggle beside a group')
    nav_w = await pg.evaluate("() => Math.round(document.getElementById('nav-groups').getBoundingClientRect().width)")
    v0 = await pg.evaluate('view')
    for h in heads:
        loc = await head(pg, h['grp'])
        if not await loc.count(): continue
        await open_menu(pg, phone)
        if await loc.get_attribute('aria-expanded') == 'true': await tap(pg, loc, phone)   # closed first
        await tap(pg, loc, phone)
        s = await pg.evaluate(f"""() => {{ const vis = e => !!e && e.getClientRects().length > 0 && !e.closest('[hidden]');
          const H = [...document.querySelectorAll('#nav-groups [data-mnhead]')];
          const me = document.querySelector('#nav-groups [data-mnhead="{h['grp']}"]'), kids = document.querySelector('#nav-groups [data-mngr="{h['grp']}"]');
          const r = me.getBoundingClientRect();
          return {{ exp: me.getAttribute('aria-expanded'), kids: !!kids && vis(kids) && [...kids.querySelectorAll('button')].some(vis),
            others: H.filter(x => x !== me && x.getAttribute('aria-expanded') === 'true').map(x => x.dataset.mnhead), view, w: Math.round(r.width), h: Math.round(r.height),
            open: document.querySelector('.rail').classList.contains('open') }}; }}""")
        c.ok(s['exp'] == 'true' and s['kids'], f'{tag}: tapping "{h["label"]}" opens it ({s})')
        c.ok(not s['others'], f'{tag}: "{h["label"]}" open beside {s["others"]} (one group at a time)')
        c.ok(s['view'] == v0, f'{tag}: tapping the group "{h["label"]}" changed the page to {s["view"]}')
        c.ok(s['w'] >= nav_w - 24, f'{tag}: "{h["label"]}" is {s["w"]}px of a {nav_w}px menu (the whole row is the target)')
        if phone: c.ok(s['open'], f'{tag}: the menu closed when "{h["label"]}" was tapped')
        await tap(pg, loc, phone)
        ex = await loc.get_attribute('aria-expanded')
        c.ok(ex == 'false', f'{tag}: tapping "{h["label"]}" again leaves it {ex}')
    # ---- NUMBERS: only where something waits, one style, each equals its page
    M = await pg.evaluate(MENU_JS)
    styles = set()
    for e in M:
        if not e['n']: continue
        c.ok(e['kind'] in ('top', 'kid'), f'{tag}: a number on the group name "{e["label"]}" ({e["n"]})')
        if e['badge']:
            transparent = e['badge']['bg'] in ('rgba(0, 0, 0, 0)', 'transparent')
            c.ok(not transparent and e['badge']['radius'] >= 8, f'{tag}: "{e["label"]}" {e["n"]} is not a filled badge {e["badge"]}')
            styles.add((e['badge']['bg'], e['badge']['color']))
    c.ok(len(styles) <= 1, f'{tag}: badges in {len(styles)} styles {styles}')
    numbered = [e for e in M if e['n'] and e['kind'] in ('top', 'kid')]
    for e in numbered:
        if not await go_entry(pg, e, phone):
            c.ok(False, f'{tag}: could not open "{e["label"]}" to check its number'); continue
        src = await pg.evaluate(PAGE_N, e['v'])
        c.ok(src is not None, f'{tag}: "{e["label"]}" shows {e["n"]} and its page states no such count (a plain count of records?)')
        if src: c.ok(src['n'] == e['n'], f'{tag}: "{e["label"]}" shows {e["n"]}; its page shows {src["n"]} ({src["how"]})')
    # ---- JOB: Projects lists the person's jobs, then All Projects; the job opened is lit under Projects
    if u in OFFICE:
        M = await pg.evaluate(MENU_JS)
        jobs = [e for e in M if e['grp'] == 'jobs' and e['kind'] == 'kid']
        # the person's jobs: the jobs their All Projects lists, in its order; none for a role that opens no job page
        want_jobs = await pg.evaluate("() => (ROLE_VIEWS[role()] || []).some(v => ['dash', 'sboard', 'sched', 'ftoday'].includes(v)) ? ovRows('jobs').map(r => r.p.id).slice(0, 6) : []")
        c.ok(jobs and jobs[-1]['v'] == 'ovjobs' and jobs[-1]['label'] == 'All Projects', f'{tag}: Projects ends with All Projects {[j["label"] for j in jobs]}')
        c.ok([j['pid'] for j in jobs[:-1]] == want_jobs, f'{tag}: Projects lists the person\'s jobs first {[j["pid"] for j in jobs]} (want {want_jobs})')
        if len(jobs) > 2:
            j = jobs[1]
            await go_entry(pg, j, phone)
            st = await pg.evaluate(STATE_JS)
            c.ok(st['pid'] == j['pid'], f'{tag}: the job "{j["label"]}" opens that job ({st["pid"]}, {st["view"]})')
            await open_menu(pg, phone)
            M2 = await pg.evaluate(MENU_JS)
            lit = [e for e in M2 if e['on'] and e['kind'] in ('top', 'kid')]
            hj = [e for e in M2 if e['kind'] == 'head' and e['grp'] == 'jobs']
            c.ok([x['pid'] for x in lit] == [j['pid']], f'{tag}: lit under Projects {[x["label"] for x in lit]}, want {j["label"]}')
            c.ok(hj and hj[0]['exp'] == 'true', f'{tag}: Projects is open on the job')
            await shot(pg, f'{u}_{dev}_job')
    # screenshot: the menu open, the group of the page on screen open (Projects for the office, as the mockup)
    await sign_in(pg, u)
    if u in OFFICE: await ensure_open(pg, 'jobs', phone)
    else: await open_menu(pg, phone)
    await shot(pg, f'{u}_{dev}')
    # ---- REACH: every old entry still opens its page
    if reach:
        await sign_in(pg, u)
        await open_menu(pg, phone)
        M = await pg.evaluate(MENU_JS)
        alias = await pg.evaluate("() => (typeof MN_ALIAS !== 'undefined' ? MN_ALIAS : {})")
        for place, s in OLD[u]:
            k, label = s.split('=', 1)
            v, _, tb = k.partition(':')
            row = {'role': u, 'dev': dev, 'old': f'{place} > {label}', 'new': '', 'ok': False}
            hit = [e for e in M if e['kind'] in ('top', 'kid') and not e['pid'] and e['v'] == v and e['tab'] == tb]
            # Approvals lights Today (an alias for the menu's light) but is reached through Today's link, checked below
            al = alias.get(v) if v != 'mapprove' else None
            if not hit and al: hit = [e for e in M if e['kind'] in ('top', 'kid') and not e['pid'] and e['v'] == al and not e['tab']]
            if hit:
                e = hit[0]
                g = next((x['label'] for x in M if x['kind'] == 'head' and x['grp'] == e['grp']), '')
                row['new'] = (g + ' > ' if e['kind'] == 'kid' else '') + e['label']
                await go_entry(pg, e, phone)
                st = await pg.evaluate(STATE_JS)
                row['ok'] = (st['view'] in (v, al) or st['folded'] == v) and (not tb or st['billTab'] == tb)
                row['got'] = st['view'] + (':' + st['billTab'] if tb else '')
            elif v == 'mapprove':
                row['new'] = 'Today > Open the Approvals Page'
                tod = next((e for e in M if e['kind'] == 'top' and e['v'] in ('home', 'sday')), None)
                if tod: await go_entry(pg, tod, phone)
                if await pg.locator('.view.on [data-tdytabbtn="appr"]').count():
                    await tap(pg, pg.locator('.view.on [data-tdytabbtn="appr"]').first, phone)
                a = pg.locator('.view.on [data-tdall], .view.on [data-mnappr]').first
                if await a.count():
                    await a.scroll_into_view_if_needed(); await tap(pg, a, phone)
                st = await pg.evaluate(STATE_JS)
                row['ok'] = st['view'] == 'mapprove'; row['got'] = st['view']
            else:
                # a job's own page: Projects > a job > its tab (the job page's tabs belong to the job-structure lane)
                jobs = [e for e in M if e['grp'] == 'jobs' and e['kind'] == 'kid' and e['pid']]
                if jobs:
                    await go_entry(pg, jobs[0], phone)
                    sel = f'#subnav [data-sub="{v}"]' + (f'[data-subtab="{tb}"]' if tb else ':not([data-subtab])')
                    t = pg.locator(sel).first
                    if await t.count():
                        row['new'] = f'Projects > {jobs[0]["label"]} > {label} tab'
                        await t.scroll_into_view_if_needed()
                        await tap(pg, t, phone)
                        st = await pg.evaluate(STATE_JS)
                        row['ok'] = (st['view'] == v or st['view'] == alias.get(v)) and (not tb or st['billTab'] == tb)
                        row['got'] = st['view'] + (':' + st['billTab'] if tb else '')
            c.ok(row['ok'], f"{tag}: old entry {row['old']} -> {row['new'] or 'NOWHERE'} (landed {row.get('got', '-')})")
            table.append(row)
            M = await pg.evaluate(MENU_JS) if not phone else M
        if phone:
            await pg.evaluate("() => { document.querySelector('.rail')?.classList.remove('open'); }")
    c.ok(not errs, f'{tag}: page errors {errs[:2]}')
    del errs[:]

async def main():
    args = sys.argv[1:]
    users = args[args.index('--user') + 1].split(',') if '--user' in args else STAFF
    devs = [False] if '--desktop' in args else [True] if '--phone' in args else [False, True]
    reach = '--no-reach' not in args
    c = Checks()
    table = []
    async with async_playwright() as p:
        for phone in devs:
            b, pg, errs = await open_app(p, phone)
            for u in users:
                await run_role(c, pg, u, phone, errs, reach, table)
            await b.close()
    if table:
        print('\nOld entry -> new place (both devices agree unless marked)')
        seen = {}
        for r in table: seen.setdefault((r['role'], r['old']), []).append(r)
        for (u, old), rs in seen.items():
            news = {r['new'] for r in rs}
            okd = ','.join(r['dev'] for r in rs if not r['ok'])
            print(f"  {u:13} {old:42} -> {' | '.join(sorted(news)) or 'NOWHERE'}{'   FAIL on ' + okd if okd else ''}")
    return c.done()

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
