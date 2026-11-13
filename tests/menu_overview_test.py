"""menu_overview_test: a module's name in the menu opens the module's overview page (Alan, 11-12: "When I click projects
or purchasing it just shows me a drop down. That's not effective. It's better that it takes me to an overview page for
the modules.").

For the owner, the PM, the controller and billing, on the desktop (1440x900) and the phone (390x844), pressed for real:
  OPEN      each module's name (Projects, Purchasing, Sales and Clients, Accounting, Design, Reports, Company and
            Settings) opens its overview: All Projects, the Purchasing overview, the Pipeline, the Accounting overview,
            Reports' own page (Job Profitability), the Company and Settings hub. A role that may not open the overview
            (ROLE_VIEWS) lands on the group's first page it may open; Design has no overview of its own.
  HEADING   the page's heading reads as the module's name where the page is the module's own, else as the entry lit
  CURRENT   the name is lit (aria-current) while its overview is the page on screen, and the group shows its pages
  CHEVRON   the chevron at the right of the name shows and hides the pages and never changes the page; it is a line
            SVG, and on the phone a 44px target beside a 44px name
  LINKS     the retired overviews still forward for a link that names them (ovbuy to the Buy Board or Orders, ovmoney to
            Banking); only the module's name opens the overview
  PHONE     no sideways scroll on any page a name opens; the sheet closes on the page and opens again on the module
  ERRORS    no page errors
Usage: python3 menu_overview_test.py [--user u_owner,...] [--desktop|--phone]
"""
import asyncio, sys
from harness import *

USERS4 = ['u_owner', 'u_alan', 'u_controller', 'u_billing']
# the module -> (the overview view, the heading the page carries: the module's name where the page is the module's own)
OVER = {
    'jobs': ('ovjobs', 'Projects'),
    'buy': ('ovbuy', 'Purchasing'),
    'sales': ('ovsales', 'Pipeline'),
    'money': ('ovmoney', 'Accounting'),
    'reports': ('reports', 'Job Profitability'),
    'setup': ('cohub', 'Company and Settings'),
}
STATE = r"""() => { const vis = e => !!e && e.getClientRects().length > 0;
  const v = document.querySelector('.view.on');
  let h = v && ([...v.querySelectorAll('.ph h2, .ph h1, .td-ph h2, .yd-ph h2')].find(vis) || [...v.querySelectorAll('h1, h2')].find(vis));
  // the phone's slim header carries the page's name where the page's own heading is folded into it (td-in-hdr)
  const crumb = [...document.querySelectorAll('#crumbs b')].filter(vis).map(x => x.textContent.trim()).pop() || '';
  if (innerWidth <= 760 && v && v.querySelector('.ph h2.td-in-hdr, .td-ph h2.td-in-hdr') && crumb) h = { textContent: crumb };
  const on = document.querySelector('#nav-groups button.on');
  const lbl = e => { if (!e) return ''; const c = e.cloneNode(true); c.querySelectorAll('.n, svg').forEach(x => x.remove()); return c.textContent.replace(/\s+/g, ' ').trim(); };
  return { view, heading: h ? h.textContent.replace(/\s+/g, ' ').trim() : '', crumb, ent: lbl(on),
    here: [...document.querySelectorAll('#nav-groups [data-mnhead][aria-current="page"]')].map(x => x.dataset.mnhead),
    open: [...document.querySelectorAll('#nav-groups [data-mnhead][aria-expanded="true"]')].map(x => x.dataset.mnhead),
    sheet: document.querySelector('.rail').classList.contains('open'),
    wide: document.documentElement.scrollWidth - innerWidth,
    body: v ? v.innerText.trim().length : 0 }; }"""
HEADS = r"""(rv) => { const B = mnBuild(); return B.work.concat(B.bottom ? [B.bottom] : []).map(g => { const first = g.items.find(x => !x.job);
  return { id: g.id, n: g.n, first: first ? first.v : '', firstL: first ? first.l : '', firstTab: first ? first.tab : '', may: Object.fromEntries(rv.map(v => [v, (ROLE_VIEWS[role()] || []).includes(v)])) }; }); }"""

async def tap(pg, loc, phone):
    await loc.scroll_into_view_if_needed()
    await (loc.tap() if phone else loc.click())
    await pg.wait_for_timeout(350)

async def open_menu(pg, phone):
    if not phone: return
    if not await pg.evaluate("document.querySelector('.rail').classList.contains('open')"):
        await tap(pg, pg.locator('#menu-btn:visible, .view.on [data-tvmenu]:visible').first, phone)

async def run(p, c, uid, phone):
    tag0 = f'{uid} {"phone" if phone else "desktop"}'
    b, pg, errs = await open_app(p, phone)
    await sign_in(pg, uid)
    heads = await pg.evaluate(HEADS, [v for v, _ in OVER.values()])
    c.ok(len(heads) >= 4, f'{tag0}: the menu has {len(heads)} modules')
    for h in heads:
        gid, tag = h['id'], f'{tag0} "{h["n"]}"'
        ov = OVER.get(gid)
        want, head = (ov if ov and h['may'].get(ov[0]) else (h['first'], h['firstL']))
        # start from Today, the module closed
        await go(pg, await pg.evaluate("MENU[role()].home"))
        await open_menu(pg, phone)
        name = pg.locator(f'#nav-groups [data-mnhead="{gid}"]').first
        chev = pg.locator(f'#nav-groups [data-mnchev="{gid}"]').first
        c.ok(await name.count() == 1 and await chev.count() == 1, f'{tag}: a name and a chevron')
        if not await chev.count(): continue
        # CHEVRON: a line SVG at the right of the name; shows and hides the pages; never changes the page
        v0 = await pg.evaluate('view')
        g = await pg.evaluate("""g => { const n = document.querySelector(`#nav-groups [data-mnhead="${g}"]`), k = document.querySelector(`#nav-groups [data-mnchev="${g}"]`);
          const a = n.getBoundingClientRect(), b = k.getBoundingClientRect(), s = k.querySelector('svg');
          return { nw: Math.round(a.width), nh: Math.round(a.height), kw: Math.round(b.width), kh: Math.round(b.height), right: b.left >= a.right - 1, row: Math.abs(a.top - b.top) < 3,
            svg: !!s && getComputedStyle(s).fill === 'none' && k.textContent.trim() === '', label: k.getAttribute('aria-label') || '' }; }""", gid)
        c.ok(g['svg'], f'{tag}: the chevron is not a line SVG ({g})')
        c.ok(g['right'] and g['row'], f'{tag}: the chevron is not at the right of the name ({g})')
        c.ok(g['label'].startswith('Show ') or g['label'].startswith('Hide '), f'{tag}: the chevron has no label ({g["label"]})')
        if phone: c.ok(g['kh'] >= 44 and g['kw'] >= 44 and g['nh'] >= 44, f'{tag}: targets under 44px ({g})')
        was = await chev.get_attribute('aria-expanded') == 'true'
        await tap(pg, chev, phone)
        st = await pg.evaluate(STATE)
        kids = await pg.evaluate("g => { const k = document.querySelector(`#nav-groups [data-mngr=\"${g}\"]`); return !!k && !k.hidden && k.getClientRects().length > 0; }", gid)
        c.ok(st['view'] == v0, f'{tag}: the chevron changed the page to {st["view"]}')
        c.ok(kids == (not was) and (gid in st['open']) == (not was), f'{tag}: the chevron did not toggle the pages (was open {was}, now {kids}, {st["open"]})')
        if phone: c.ok(st['sheet'], f'{tag}: the sheet closed on the chevron')
        await tap(pg, chev, phone)
        st = await pg.evaluate(STATE)
        kids = await pg.evaluate("g => { const k = document.querySelector(`#nav-groups [data-mngr=\"${g}\"]`); return !!k && !k.hidden && k.getClientRects().length > 0; }", gid)
        c.ok(st['view'] == v0 and kids == was, f'{tag}: the second press on the chevron did not put the pages back (view {st["view"]}, open {kids})')
        # OPEN: the name opens the overview, or the first page the role may open
        await tap(pg, name, phone)
        await pg.wait_for_timeout(250)
        st = await pg.evaluate(STATE)
        c.ok(st['view'] == want, f'{tag}: the name opens {st["view"]}, expected {want}')
        c.ok(st['heading'] == head, f'{tag}: the heading reads "{st["heading"]}", expected "{head}"')
        c.ok(st['body'] > 40, f'{tag}: the page is empty')
        c.ok(gid in st['open'], f'{tag}: the module does not show its pages after its name is pressed ({st["open"]})')
        if ov and h['may'].get(ov[0]):
            c.ok(st['here'] == [gid], f'{tag}: the name is not the one lit for its overview ({st["here"]})')
        else:
            c.ok(st['ent'] == head, f'{tag}: the entry lit is "{st["ent"]}", expected "{head}"')
        if phone:
            c.ok(not st['sheet'], f'{tag}: the sheet stayed over the page')
            c.ok(st['wide'] <= 1, f'{tag}: the page scrolls sideways by {st["wide"]}px')
            await open_menu(pg, phone)
            st2 = await pg.evaluate(STATE)
            c.ok(gid in st2['open'], f'{tag}: the menu does not open on the module ({st2["open"]})')
        # a second press keeps the overview and the pages
        await open_menu(pg, phone)
        await tap(pg, pg.locator(f'#nav-groups [data-mnhead="{gid}"]').first, phone)
        st = await pg.evaluate(STATE)
        c.ok(st['view'] == want and gid in st['open'], f'{tag}: a second press left {st["view"]}, open {st["open"]}')
        # a page of the module opened from the overview: the name is no longer the one lit
        await open_menu(pg, phone)
        kid = pg.locator(f'#nav-groups [data-mngr="{gid}"] button[data-v]:not([data-pid])')
        n = await kid.count()
        if n:
            await tap(pg, kid.nth(n - 1), phone)
            st = await pg.evaluate(STATE)
            last_is_over = await pg.evaluate("g => { const B = mnBuild(), x = B.groups.concat(B.bottom || []).find(y => y.id === g), it = x.items.filter(i => !i.job).pop(); return it === x.over; }", gid)
            if not last_is_over: c.ok(gid not in st['here'], f'{tag}: the name stays lit on {st["view"]}')
    # FILL: the Purchasing overview links into each Purchasing page of the person's menu, each with that page's own
    # Needs You (the menu's number); the Projects overview flags a job with no contract value, with the way in
    await go(pg, await pg.evaluate("MENU[role()].home"))
    await open_menu(pg, phone)
    await tap(pg, pg.locator('#nav-groups [data-mnhead="buy"]').first, phone)
    if await pg.evaluate('view') == 'ovbuy':
        pgs = await pg.evaluate(r"""() => { const B = mnBuild(), g = B.work.find(x => x.id === 'buy');
          const want = g.items.filter(it => !it.job).map(it => ({ l: it.l, v: it.v, n: puCount(it.v) }));
          const got = [...document.querySelectorAll('#v-ovbuy [data-ovpages] .ov-pg')].map(b => { const r = b.getBoundingClientRect();
            return { l: b.querySelector('b').textContent.trim(), say: b.querySelector('.ov-pg-n').textContent.trim(), h: Math.round(r.height), svg: !!b.querySelector('svg'), in: r.left >= 0 && r.right <= innerWidth + 1 }; });
          return { want, got, wide: document.documentElement.scrollWidth - innerWidth }; }""")
        c.ok([x['l'] for x in pgs['got']] == [x['l'] for x in pgs['want']], f'{tag0}: the Purchasing overview links {[x["l"] for x in pgs["got"]]}, the menu lists {[x["l"] for x in pgs["want"]]}')
        for w, g in zip(pgs['want'], pgs['got']):
            said = int(g['say'].split(' ')[0]) if g['say'][:1].isdigit() else 0
            c.ok(said == w['n'], f'{tag0}: the overview says "{g["say"]}" for {w["l"]}, its page counts {w["n"]}')
            c.ok(g['svg'] and g['in'] and (not phone or g['h'] >= 44), f'{tag0}: the link to {w["l"]} ({g})')
        c.ok(pgs['wide'] <= 1, f'{tag0}: the Purchasing overview scrolls sideways by {pgs["wide"]}px')
        for i, w in enumerate(pgs['want']):
            await pg.evaluate("() => { mnOverV = 'ovbuy'; view = 'ovbuy'; render(); }")
            await pg.wait_for_timeout(150)
            await tap(pg, pg.locator('#v-ovbuy [data-ovpages] .ov-pg').nth(i), phone)
            st = await pg.evaluate(STATE)
            c.ok(st['view'] == w['v'] and st['ent'] == w['l'], f'{tag0}: the overview\'s link to {w["l"]} opens {st["view"]} (lit "{st["ent"]}")')
    await go(pg, await pg.evaluate("MENU[role()].home"))
    await open_menu(pg, phone)
    await tap(pg, pg.locator('#nav-groups [data-mnhead="jobs"]').first, phone)
    fl = await pg.evaluate(r"""() => ({ want: OV_BUILD.jobs().filter(r => !(r.J.contract > 0)).map(r => r.p.id), got: [...document.querySelectorAll('#v-ovjobs [data-ovflag]')].map(x => x.dataset.ovflag),
      n: document.querySelectorAll('#v-ovjobs [data-ovflags]').length, wide: document.documentElement.scrollWidth - innerWidth })""")
    c.ok(fl['got'] == fl['want'] and fl['n'] <= 1, f'{tag0}: the Projects overview flags {fl["got"]}, the jobs with no contract value are {fl["want"]}')
    c.ok(fl['wide'] <= 1, f'{tag0}: the Projects overview scrolls sideways by {fl["wide"]}px')
    if fl['got']:
        await tap(pg, pg.locator('#v-ovjobs [data-ovflaggo]').first, phone)
        st = await pg.evaluate("({ view, job: S && S.id })")
        c.ok(st['job'] == fl['got'][0] and st['view'] in ('jbill', 'dash'), f'{tag0}: the flag opens {st}')
    # RECORD: with a record open, the chevron leaves it open (it changes nothing but the list); the name leaves it, as
    # every menu entry does
    if await pg.evaluate("(ROLE_VIEWS[role()] || []).includes('billing') && !!document.querySelector('#nav-groups [data-mnhead=\"money\"]')"):
        opened = await pg.evaluate("""() => { const c = DB.clients.find(x => (x.invoices || []).length); if (!c) return false;
          clientOpen = c.id; docOpen = { kind: 'invoice', id: c.invoices[0].id }; view = 'billing'; render(); return !!docOpen; }""")
        if opened:
            await pg.wait_for_timeout(300)
            await open_menu(pg, phone)
            await tap(pg, pg.locator('#nav-groups [data-mnchev="buy"]').first, phone)
            c.ok(await pg.evaluate("!!docOpen && view === 'billing'"), f'{tag0}: the chevron closed the open invoice')
            await tap(pg, pg.locator('#nav-groups [data-mnhead="money"]').first, phone)
            st = await pg.evaluate("({ doc: !!docOpen, view })")
            c.ok(not st['doc'] and st['view'] != 'billing', f'{tag0}: the name left the open invoice open ({st})')
    # LINKS: a link that names a retired overview still lands where its content moved
    for v in ('ovbuy', 'ovmoney'):
        if not await pg.evaluate("v => (ROLE_VIEWS[role()] || []).includes(v)", v): continue
        await go(pg, await pg.evaluate("MENU[role()].home"))
        await pg.evaluate("v => setView(v)", v)
        await pg.wait_for_timeout(250)
        got = await pg.evaluate('view')
        exp = await pg.evaluate("v => 'ovbuy' === v ? puHomeView() : (acMay('bank') ? 'bank' : v)", v)
        c.ok(got == exp, f'{tag0}: a link to {v} lands on {got}, expected {exp}')
    c.ok(not errs, f'{tag0}: page errors {errs[:3]}')
    await b.close()

async def main():
    users = USERS4
    if '--user' in sys.argv: users = sys.argv[sys.argv.index('--user') + 1].split(',')
    modes = [False] if '--desktop' in sys.argv else [True] if '--phone' in sys.argv else [False, True]
    c = Checks()
    async with async_playwright() as p:
        for phone in modes:
            for u in users:
                await run(p, c, u, phone)
    sys.exit(c.done())

asyncio.run(main())
