"""Company and Settings as the approved mock-up draws it (docs/mockups/company/SPEC.md, the chief of staff's must-fix
list, BACKLOG section 10 items 2, 8 and 9). Done as the person, on the phone and the desktop: the owner, the PM and the
controller open the hub and each page from the menu.

The hub      six rows (Team, The Brain, Insurance and Licenses, Connections, The SmartDesign Standard, Company
             Settings), a number only where something waits, each equal to its page's Needs You.
Team         every person once: one headcount everywhere (the header, the hub, Company Settings' Your Data, the foot of
             Tasks' Team chip); every login is a person (the PM is listed); a phone or email two people share is a
             Needs You row; a person's page holds their approval limits (only the owner changes one), their
             assistant's rules (Messages to Clients never Act Alone) and what it did on its own; their open tasks are
             the same Mine count Tasks shows.
The Brain    To Approve equals its rows, the hub and Today's line; one lesson drafted twice is one row.
Insurance    the firm's own policies, licenses and filings; a required record not on file (workers' comp, the trade
             licenses) is a Needs You row; removing one moves the row, the hub and Today's Compliance.
Connections  the firm's one-time Google setup first, then your account, then banks and cards with reconciled dates.
Standard     opens on the measured lines open today, the 2-hour client reply among them.
Settings     Sales Settings, Your Own Data and Problem Reports fold in; As Of, Clear Everything and Turn the Demo On
             sit behind the owner and a typed confirm."""
import asyncio, re, sys
from playwright.async_api import async_playwright
from harness import open_app, sign_in, go, Checks
from ydcheck import MENU_ITEMS, phone_fit

c = Checks()

PAGE = """() => { const v = document.querySelector('.view.on'); const chips = [...v.querySelectorAll('[data-ydchip]')].filter(b => b.getClientRects().length).map(b => ({ k: b.dataset.ydchip,
    label: b.childNodes[0].textContent.trim(), n: ((b.querySelector('.n') || {}).textContent || '').trim(), on: b.classList.contains('on') }));
  const rows = [...v.querySelectorAll('[data-ydrow]')].filter(e => e.getClientRects().length).map(e => ({ id: e.dataset.ydrow, sec: e.dataset.sec || '', n: e.dataset.n || '', text: e.innerText }));
  return { view: view, chips, rows, text: v.innerText }; }"""


async def hub_as(p, uid, phone):
    who = f'{uid} {"phone" if phone else "desktop"}'
    b, pg, errs = await open_app(p, phone)
    await sign_in(pg, uid)
    items = await pg.evaluate("() => (mnBuild(role()).bottom || {items: []}).items.filter(i => !i.head).map(i => i.l)")
    if uid == 'u_owner':
        c.ok(items == ['Team', 'The Brain', 'Insurance and Licenses', 'Connections', 'The SmartDesign Standard', 'Company Settings'], f'{who}: Company and Settings holds {items}')
    else:
        c.ok(items and all(i in ['Team', 'The Brain', 'Insurance and Licenses', 'Connections', 'The SmartDesign Standard', 'Company Settings'] for i in items), f'{who}: Company and Settings holds {items}')
    await go(pg, 'cohub')
    m = await pg.evaluate(PAGE)
    c.ok(m['view'] == 'cohub', f'{who}: the hub does not open ({m["view"]})')
    hub = {x['id']: x for x in m['rows']}
    c.ok(set(hub) <= {'team', 'brain', 'obligations', 'conn', 'standard', 'cosettings'} and hub, f'{who}: hub rows {list(hub)}')
    # each number is its page's Needs You
    for k, n in [(k, x['n']) for k, x in hub.items() if x['n']]:
        await pg.evaluate("k => document.querySelector('.view.on [data-ydrow=\"' + k + '\"]').click()", k)
        await pg.wait_for_timeout(200)
        mk = await pg.evaluate(PAGE)
        need = [x for x in mk['rows'] if x['sec'] == 'need']
        c.ok(mk['view'] == k and str(len(need)) == n, f'{who}: the hub says {k} {n}, the page shows {len(need)} ({mk["view"]})')
        await go(pg, 'cohub')
    # old pages land on their new homes
    for old, new in (('ovoffice', 'cohub'), ('setup', 'cohub')):
        if not await pg.evaluate("v => (ROLE_VIEWS[role()] || []).includes(v)", old): continue
        await pg.evaluate("v => setView(v)", old)
        await pg.wait_for_timeout(150)
        st = await pg.evaluate("() => view")
        c.ok(st == new, f'{who}: {old} lands on {st}, want {new}')
    # Sales Settings, Your Own Data and Problem Reports open in place under Company Settings: lit there, nothing lost
    for old in ('hbsettings', 'rdata', 'rpbox'):
        if not await pg.evaluate("v => (ROLE_VIEWS[role()] || []).includes(v)", old): continue
        await pg.evaluate("v => setView(v)", old)
        await pg.wait_for_timeout(150)
        st = await pg.evaluate("() => { const c = mnCur(mnBuild(role())); return [view, c ? c.it.v : '']; }")
        c.ok(st == [old, 'cosettings'], f'{who}: {old} opens as {st}, want its page lit as Company Settings')
    if phone:
        await go(pg, 'cohub')
        await phone_fit(c, pg, f'{who} hub')
    c.ok(not errs, f'{who} hub: errors {errs[:2]}')
    await b.close()


async def team_as(p, uid, phone):
    who = f'{uid} {"phone" if phone else "desktop"}'
    b, pg, errs = await open_app(p, phone)
    await sign_in(pg, uid)
    await go(pg, 'team')
    m = await pg.evaluate(PAGE)
    n = await pg.evaluate("() => typeof ydPeople === 'function' ? ydPeople().length : 0")
    c.ok(n >= 14, f'{who}: the one people list holds {n}; the demo has 14 (the PM with his login)')
    c.ok(re.search(rf'\b{n} people\b', m['text']), f'{who}: Team\'s header does not say {n} people')
    people = [x for x in m['rows'] if x['sec'] == 'all']
    c.ok(len(people) == n, f'{who}: Team lists {len(people)} people, the one list {n}')
    c.ok(any(x['id'] == 'u_alan' for x in people), f'{who}: the PM (a login with tasks) is not on Team')
    # section 10 item 8: every login is a person; phone and email unique, or a Needs You row
    lint = await pg.evaluate("() => ydPeopleLint()")
    c.ok(not lint['noPerson'], f'{who}: logins with no person: {lint["noPerson"]}')
    c.ok(not lint['dupes'], f'{who}: two people share a phone or email: {lint["dupes"]}')
    planted = await pg.evaluate("""() => { const u = DB.users.find(x => x.id === 'u_billing'), keep = u.phone; u.phone = DB.users.find(x => x.id === 'u_chen').phone;
       render(); const t = document.querySelector('.view.on').innerText; u.phone = keep; render(); return /share/i.test(t) && /Needs You/.test(t); }""")
    c.ok(planted, f'{who}: a phone two people share is not a Needs You row on Team')
    # one Mine count: the person page's open tasks equal Tasks' Mine
    await pg.evaluate("() => ydOpenPerson(currentUser().id)")
    await pg.wait_for_timeout(200)
    pm = await pg.evaluate(PAGE)
    mine = await pg.evaluate("() => openTasks('me').length")
    c.ok(re.search(rf'\b{mine} open\b', pm['text']), f'{who}: the person page does not say {mine} open (Tasks\' Mine)')
    for k in ('What Reaches You for Approval', 'Your Assistant', 'What It Did on Its Own'):
        c.ok(k in pm['text'], f'{who}: the person page has no {k}')
    lock = await pg.evaluate("""() => { const b = document.querySelector('.view.on [data-parule$="|clientMessages|alone"]'); return b ? b.disabled : 'none'; }""")
    c.ok(lock in (True, 'none'), f'{who}: Messages to Clients can be set to Act Alone')
    lim = await pg.evaluate("() => !!document.querySelector('.view.on [data-ydlimit]:not([disabled])')")
    c.ok(lim == (uid == 'u_owner'), f'{who}: the approval limit is editable: {lim}')
    if phone: await phone_fit(c, pg, f'{who} person')
    c.ok(not errs, f'{who} Team: errors {errs[:2]}')
    await b.close()


async def owner_pages(p, phone):
    who = f'owner {"phone" if phone else "desktop"}'
    b, pg, errs = await open_app(p, phone)
    await sign_in(pg, 'u_owner')
    # The Brain: To Approve equals its rows, the hub and Today's line; one lesson once
    await go(pg, 'brain')
    m = await pg.evaluate(PAGE)
    need = [x for x in m['rows'] if x['sec'] == 'need']
    n = next((x['n'] for x in m['chips'] if x['k'] == 'need'), '')
    c.ok(m['view'] == 'brain' and n == str(len(need)) and need, f'{who}: The Brain To Approve {n!r}, rows {len(need)} ({m["view"]})')
    titles = [re.sub(r'^Lesson:\s*', '', x['text'].split('\n')[0]).strip().lower() for x in need]
    c.ok(len(titles) == len(set(titles)), f'{who}: The Brain shows one proposal twice')
    firm = await pg.evaluate("() => { try { return ydFirmRows().find(r => r.k === 'brain').v; } catch (e) { return null; } }")
    c.ok(str(firm) == n, f"{who}: Today's lessons line {firm} vs The Brain {n}")
    # Insurance and Licenses
    await go(pg, 'obligations')
    m = await pg.evaluate(PAGE)
    t = m['text']
    c.ok('Insurance and Licenses' in t, f'{who}: the page is not Insurance and Licenses')
    need = [x for x in m['rows'] if x['sec'] == 'need']
    nt = ' '.join(x['text'] for x in need)
    for k in ("Workers' Comp", 'Trade License', 'LLC'):
        c.ok(k.lower() in nt.lower(), f'{who}: {k} is not a Needs You row')
    c.ok('Window Works' not in ' '.join(x['text'] for x in m['rows'] if x['sec'] in ('need', 'file')), f'{who}: a vendor certificate is listed as the firm\'s own')
    before = await pg.evaluate("() => [ydInsNeeds().length, ydFirmRows().find(r => r.k === 'comp').v]")
    after = await pg.evaluate("""() => { const o = (DB.obligations || []).find(x => /general liability/i.test(x.name || x.title || '')); if (!o) return null; const keep = o.status; o.status = 'cancelled';
       const r = [ydInsNeeds().length, ydFirmRows().find(r => r.k === 'comp').v]; o.status = keep; return r; }""")
    c.ok(after and after[0] == before[0] + 1 and after[1] == before[1] + 1, f'{who}: removing the general liability policy moves Needs You and Compliance {before} -> {after}')
    # Connections: the firm's setup first
    await go(pg, 'conn')
    m = await pg.evaluate(PAGE)
    ids = [x['id'] for x in m['rows']]
    c.ok(ids[:1] == ['firm'], f'{who}: Connections opens on {ids[:2]}, want the firm\'s one-time Google setup first')
    c.ok('Reconciled through' in m['text'] and not re.search(r'\bReconcile\b(?! )', m['text']), f'{who}: Connections lacks reconciled dates or keeps Reconcile buttons')
    prim = await pg.evaluate("() => [...document.querySelectorAll('.view.on .btn.primary')].filter(e => e.getClientRects().length).map(e => e.textContent.trim())")
    c.ok(len(prim) == 1, f'{who}: Connections has blue buttons {prim}')
    # the Standard opens on the measured lines open today, the 2-hour client reply among them
    await go(pg, 'standard')
    m = await pg.evaluate(PAGE)
    c.ok([x['label'] for x in m['chips'] if x['on']] == ['Open Today'], f'{who}: the Standard opens on {[x["label"] for x in m["chips"] if x["on"]]}')
    two = [x for x in m['rows'] if 'acknowledged within 2' in x['text']]
    c.ok(two and two[0]['n'] not in ('', '0'), f'{who}: the 2-hour client acknowledgement reads {two and two[0]["n"]}; Aliya Chen and Sarah Klein wait past it')
    n = next((x['n'] for x in m['chips'] if x['k'] == 'open'), '')
    c.ok(n == str(len([x for x in m['rows'] if x['sec'] == 'need'])), f'{who}: Open Today {n} vs its rows')
    # Company Settings: the folded pages, and the clock behind a typed confirm
    await go(pg, 'cosettings')
    m = await pg.evaluate(PAGE)
    for k in ('Sales Settings', 'Your Own Data', 'Problem Reports', 'As Of', 'Clear Everything', 'Turn the Demo On'):
        c.ok(k in m['text'], f'{who}: Company Settings has no {k}')
    n = await pg.evaluate("() => ydPeople().length")
    c.ok(re.search(rf'\b{n} people\b', m['text']), f'{who}: Your Data does not say {n} people')
    conf = await pg.evaluate("""async () => { const b = document.querySelector('.view.on [data-ydwipe]'); b.click(); await new Promise(r => setTimeout(r, 150));
       const ok = document.querySelector('#mbm-ok'), inp = document.querySelector('#mbm input[name=confirm], #mbm [data-f=confirm]');
       const r = { input: !!inp, disabledOk: ok ? ok.disabled : null }; const x = document.querySelector('#mbm-cancel, .mbm-x'); x && x.click(); return r; }""")
    c.ok(conf['input'] and conf['disabledOk'], f'{who}: Clear Everything does not ask for a typed confirm {conf}')
    if phone: await phone_fit(c, pg, f'{who} Company Settings')
    c.ok(not errs, f'{who} pages: errors {errs[:2]}')
    await b.close()


async def pm_settings(p):
    b, pg, errs = await open_app(p, False)
    await sign_in(pg, 'u_alan')
    if await pg.evaluate("() => (ROLE_VIEWS[role()] || []).includes('cosettings')"):
        await go(pg, 'cosettings')
        t = await pg.evaluate("() => document.querySelector('.view.on').innerText")
        c.ok('Clear Everything' not in t and 'Turn the Demo On' not in t, 'pm: Clear Everything or the demo switch shows to the PM')
    c.ok(not errs, f'pm settings: errors {errs[:2]}')
    await b.close()


async def main():
    only = sys.argv[1:]
    async with async_playwright() as p:
        for phone in (False, True):
            for uid in ('u_owner', 'u_alan', 'u_controller'):
                if not only or 'hub' in only: await hub_as(p, uid, phone)
                if not only or 'team' in only: await team_as(p, uid, phone)
            if not only or 'pages' in only: await owner_pages(p, phone)
        if not only or 'pm' in only: await pm_settings(p)
    sys.exit(c.done())

asyncio.run(main())
