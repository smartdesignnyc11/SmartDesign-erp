"""Sales and Clients as the approved mock-up draws them (docs/mockups/sales/SPEC.md, the chief of staff's must-fix list,
BACKLOG section 10 items 1, 3, 4 and 5). Done as the person, on the phone and the desktop: the owner sells, the PM and
the coordinator read, billing opens a client for the money.

Pipeline   opens on Need You (a next step past its date, no touch in 14 days, or signed with no job set up: the
           Nakamuras); On Track, then All Open and Won and Lost one tap; How Sales Is Going folds in Numbers, Forecast,
           the Dashboard and Partners' figures. Need You equals its rows and Today's "Deals That Need You". A deal's
           next step is its open task: one date (Ana Petrova reads 9/4 everywhere, so she is not in Need You).
Clients    opens on Need You (a client waiting on us, money past due, someone writing as a client who is not on file);
           All and Partners one tap.
A client   everything is the client's: Waiting on Us, Waiting on Them, They Owe, Left to Bill, each equal to its rows;
           three tabs (Overview, Contract and Billing, Messages); one + tied to the client; billed gross and net,
           labelled, tying to the cent through one function; the activity names an invoice by its own number.
A deal     the next step with its button, the road to signed, Set Up the Job before Won.
Estimates  leaves the Sales menu (one switch restores it): an old link lands on Pipeline's Proposals Out, each
           estimate with its deal."""
import asyncio, re, sys
from playwright.async_api import async_playwright
from harness import open_app, sign_in, go, Checks
from ydcheck import MENU_ITEMS, phone_fit

c = Checks()

PAGE = """() => { const chips = [...document.querySelectorAll('.view.on [data-ydchip]')].filter(b => b.getClientRects().length).map(b => ({ k: b.dataset.ydchip,
    label: b.childNodes[0].textContent.trim(), n: ((b.querySelector('.n') || {}).textContent || '').trim(), on: b.classList.contains('on') }));
  const rows = [...document.querySelectorAll('.view.on [data-ydrow]')].filter(e => e.getClientRects().length).map(e => ({ id: e.dataset.ydrow, sec: e.dataset.sec || '', text: e.innerText }));
  const tiles = [...document.querySelectorAll('.view.on [data-ydtile]')].filter(e => e.getClientRects().length).map(e => ({ k: e.dataset.ydtile, v: e.dataset.n, text: e.innerText }));
  const tabs = [...document.querySelectorAll('.view.on [data-ydtab]')].filter(e => e.getClientRects().length).map(e => e.textContent.trim());
  return { chips, rows, tiles, tabs, text: document.querySelector('.view.on').innerText }; }"""


async def pipeline_as(p, uid, phone):
    who = f'{uid} {"phone" if phone else "desktop"}'
    b, pg, errs = await open_app(p, phone)
    await sign_in(pg, uid)
    may = await pg.evaluate("() => (ROLE_VIEWS[role()] || []).includes('ovsales')")
    if not may:
        c.ok(True, ''); await b.close(); return
    await go(pg, 'ovsales')
    m = await pg.evaluate(PAGE)
    labels = [x['label'] for x in m['chips']]
    c.ok(labels == ['Need You', 'All Open', 'Won and Lost', 'Proposals Out'], f'{who}: Pipeline chips {labels}')
    c.ok([x['label'] for x in m['chips'] if x['on']] == ['Need You'], f'{who}: Pipeline does not open on Need You')
    need = [x for x in m['rows'] if x['sec'] == 'need']
    n = next((x['n'] for x in m['chips'] if x['k'] == 'need'), '')
    c.ok(n == str(len(need)) and need, f'{who}: Need You says {n!r}, shows {len(need)} rows')
    rule = await pg.evaluate("() => typeof slNeedYou === 'function' ? slNeedYou().map(x => x.l.name) : null")
    c.ok(rule is not None and len(rule) == len(need), f'{who}: Need You rows {len(need)} vs the one rule {rule}')
    t = ' '.join(x['text'] for x in need)
    c.ok('Nakamura' in t and ('Set Up the Job' in t or uid != 'u_owner') and 'no job set up' in t, f'{who}: the signed Nakamuras with no job are not in Need You with Set Up the Job')
    c.ok('Ana Petrova' not in t, f'{who}: Ana Petrova is in Need You: her deal and her task disagree on the date')
    c.ok(any(x['sec'] == 'track' for x in m['rows']), f'{who}: no On Track rows under Need You')
    c.ok('How Sales Is Going' in m['text'], f'{who}: no How Sales Is Going fold')
    await pg.evaluate("() => { const f = document.querySelector('.view.on [data-ydfold=\"nums\"]'); f && f.click(); }")
    await pg.wait_for_timeout(120)
    txt = await pg.evaluate("() => document.querySelector('.view.on').innerText")
    for k in ('First Reply', 'Proposals Out', 'Signed This Quarter', 'Thank-Yous Owed'):
        c.ok(k in txt, f'{who}: How Sales Is Going has no {k}')
    # section 10 item 1: one record, one date; the deal shows its open task's date
    bad = await pg.evaluate("""() => { const out = []; (DB.leads || []).filter(l => !['won', 'lost'].includes(l.stage)).forEach(l => { const s = slNextStep(l);
        if (s.task && s.due !== s.task.due) out.push(l.name + ' ' + s.due + ' vs ' + s.task.due); if (!s.task && s.title !== 'No Next Step') out.push(l.name + ' says ' + s.title + ' with no task'); }); return out; }""")
    c.ok(not bad, f'{who}: a deal and its task disagree on the next step: {bad}')
    # Today's Deals That Need You reads the same rule
    tn = await pg.evaluate("() => { try { return ydFirmRows().find(r => r.k === 'deals').v; } catch (e) { return null; } }")
    c.ok(str(tn) == n, f"{who}: Today's Deals That Need You {tn} vs the Pipeline's {n}")
    # roles: whoever the old Sales page let add a lead (ROLE_VIEWS holds scleads) has the one + (New Lead: from a mail,
    # typed in, or a list imported); the others read (drafts crawl, 11-04: billing and the coordinator had lost it)
    plus = await pg.evaluate("() => !!document.querySelector('.view.on [data-ydnew]')")
    may = await pg.evaluate("() => (ROLE_VIEWS[role()] || []).includes('scleads')")
    c.ok(plus == may, f'{who}: the Pipeline + shows {plus}, the role adds leads {may}')
    # the old pages land here
    for old in ('salesnum', 'hbforecast', 'hbdash'):
        ok = await pg.evaluate("v => (ROLE_VIEWS[role()] || []).includes(v)", old)
        if not ok: continue
        await pg.evaluate("v => setView(v)", old)
        await pg.wait_for_timeout(150)
        st = await pg.evaluate("() => [view, !!document.querySelector('.view.on [data-ydfold=\"nums\"][aria-expanded=\"true\"]')]")
        c.ok(st == ['ovsales', True], f'{who}: {old} lands on {st}, want Pipeline with How Sales Is Going open')
    # a repeat client's second signed deal needs its own job (the first job does not set it up, and its deposit waits)
    if uid == 'u_owner':
        rep = await pg.evaluate("""() => { DB.leads.push({ id: 'ldrepeat', name: 'Sarah & David Klein', clientId: 'cl121', stage: 'won', wonAt: '2026-08-30', value: 64000,
          addr: '121 State Street, parlor floor', history: [{ stage: 'won', at: '2026-08-30' }], touches: [], closePlan: [], stakeholders: [], qual: {}, source: 'Repeat client' });
          const n = slNeedYou().some(x => x.l.id === 'ldrepeat' && x.why === 'signed'); DB.leads = DB.leads.filter(x => x.id !== 'ldrepeat'); return n; }""")
        c.ok(rep, f'{who}: a repeat client\'s second signed deal does not show as needing its job set up')
    if phone:
        await go(pg, 'ovsales')
        await phone_fit(c, pg, f'{who} Pipeline')
    c.ok(not errs, f'{who} Pipeline: errors {errs[:2]}')
    await b.close()


async def estimates_and_deal(p, phone):
    who = f'owner {"phone" if phone else "desktop"}'
    b, pg, errs = await open_app(p, phone)
    await sign_in(pg, 'u_owner')
    items = await pg.evaluate("() => (mnBuild('owner').work.find(g => g.id === 'sales') || {items: []}).items.map(i => i.l)")
    c.ok(items == ['Pipeline', 'Clients'], f'{who}: Sales and Clients holds {items}, want Pipeline, Clients (Estimates off, flagged)')
    sw = await pg.evaluate("() => typeof YD_ESTIMATES_IN_MENU !== 'undefined'")
    c.ok(sw, f'{who}: no one switch to restore Estimates to the menu (YD_ESTIMATES_IN_MENU)')
    # an old Estimates link lands on Proposals Out, each estimate with its deal
    await pg.evaluate("() => { mnLastGrp = 'sales'; billTab = 'estimates'; setView('billing'); }")
    await pg.wait_for_timeout(200)
    st = await pg.evaluate("() => [view, (document.querySelector('.view.on [data-ydchip].on') || {dataset: {}}).dataset.ydchip || '', document.querySelector('.view.on').innerText]")
    c.ok(st[0] == 'ovsales' and st[1] == 'props', f'{who}: the old Estimates lands on {st[:2]}, want Pipeline, Proposals Out')
    c.ok('Marcus Bell' in st[2] and 'Ana Petrova' in st[2], f'{who}: Proposals Out does not list the proposals with their deals')
    # Billing's own Estimates tab still opens Billing (it is Accounting's page)
    await pg.evaluate("() => { mnLastGrp = 'money'; billTab = 'estimates'; setView('billing'); }")
    await pg.wait_for_timeout(150)
    c.ok(await pg.evaluate("() => view") == 'billing', f'{who}: Accounting\'s Billing no longer opens')
    # a deal's page: Ana Petrova
    await pg.evaluate("() => { const l = DB.leads.find(x => x.name === 'Ana Petrova'); slOpenDeal(l.id); }")
    await pg.wait_for_timeout(200)
    m = await pg.evaluate(PAGE)
    t = m['text']
    c.ok('Ana Petrova' in t and 'Next Step' in t and 'Road to Signed' in t, f'{who}: the deal page lacks its next step or road to signed')
    c.ok(t.find('Set Up the Job') >= 0 and (t.find('Won') < 0 or t.find('Set Up the Job') < t.rfind('Won')), f'{who}: Set Up the Job does not come before Won on the deal')
    c.ok('Sep 4' in t or '9/4' in t, f"{who}: Ana's next step does not read her task's date (9/4)")
    prim = await pg.evaluate("() => [...document.querySelectorAll('.view.on .btn.primary')].filter(e => e.getClientRects().length).length")
    c.ok(prim == 1, f'{who}: the deal page has {prim} blue buttons')
    if phone: await phone_fit(c, pg, f'{who} deal')
    c.ok(not errs, f'{who} deal: errors {errs[:2]}')
    await b.close()


async def clients_as(p, uid, phone):
    who = f'{uid} {"phone" if phone else "desktop"}'
    b, pg, errs = await open_app(p, phone)
    await sign_in(pg, uid)
    if not await pg.evaluate("() => (ROLE_VIEWS[role()] || []).includes('clients')"):
        await b.close(); return
    await pg.evaluate("() => { clientOpen = null; docOpen = null; }")
    await go(pg, 'clients')
    m = await pg.evaluate(PAGE)
    labels = [x['label'] for x in m['chips']]
    c.ok(labels == ['Need You', 'All', 'Partners'], f'{who}: Clients chips {labels}')
    c.ok([x['label'] for x in m['chips'] if x['on']] == ['Need You'], f'{who}: Clients does not open on Need You')
    need = [x for x in m['rows'] if x['sec'] == 'need']
    n = next((x['n'] for x in m['chips'] if x['k'] == 'need'), '')
    c.ok(n == str(len(need)), f'{who}: Clients Need You says {n!r}, shows {len(need)}')
    t = ' '.join(x['text'] for x in need)
    # section 10 item 4: someone writing as a client with no record, a repeat client with no record
    c.ok('Aliya Chen' in t, f'{who}: Aliya Chen writes as a client with no record and is not a Who Is This? row')
    c.ok('Sarah' in t or 'Klein' in t, f'{who}: the Kleins wait on us (Sarah 9/2) and are not in Need You')
    rep = await pg.evaluate("() => (DB.leads || []).filter(l => /repeat/i.test(l.source || '') && !slClientOf(l)).map(l => l.name)")
    for nm in rep:
        c.ok(nm in t, f'{who}: {nm} is called a repeat client with no client record, and Clients does not say so')
    for k in ('all', 'partners'):
        await pg.evaluate("k => document.querySelector('.view.on [data-ydchip=\"' + k + '\"]').click()", k)
        await pg.wait_for_timeout(120)
        mk = await pg.evaluate(PAGE)
        c.ok(mk['rows'], f'{who}: Clients {k} shows no rows')
    if phone: await phone_fit(c, pg, f'{who} Clients')
    # the Kleins
    await pg.evaluate("() => slOpenClient('cl121')")
    await pg.wait_for_timeout(250)
    money = uid != 'u_sarah'   # the designer reads a client's decisions, not its money (SPEC section 4)
    first = await pg.evaluate("() => (document.querySelector('.view.on [data-ydtab].on') || {}).textContent || ''")
    c.ok(first == ('Contract and Billing' if uid == 'u_billing' else 'Overview'), f'{who}: the client page opens on {first!r}')
    await pg.evaluate("() => { const b = [...document.querySelectorAll('.view.on [data-ydtab]')].find(e => /Overview/.test(e.textContent)); b && b.click(); }")
    await pg.wait_for_timeout(150)
    m = await pg.evaluate(PAGE)
    c.ok(m['tabs'] == (['Overview', 'Contract and Billing', 'Messages'] if money else ['Overview', 'Messages']), f'{who}: the client page tabs {m["tabs"]}')
    tiles = {x['k']: x for x in m['tiles']}
    for k in (('us', 'them', 'owe', 'left') if money else ('us', 'them')):
        c.ok(k in tiles, f'{who}: the client page has no {k} tile')
    rows = {}
    for x in m['rows']: rows.setdefault(x['sec'], []).append(x)
    for k in ('us', 'them'):
        if k in tiles:
            c.ok(tiles[k]['v'] == str(len(rows.get(k, []))), f'{who}: tile {k} says {tiles[k]["v"]}, shows {len(rows.get(k, []))}')
    c.ok(tiles.get('us') and int(tiles['us']['v'] or 0) >= 2, f'{who}: Waiting on Us {tiles.get("us")}; Sarah\'s 9/2 mail and the managing agent\'s call both wait')
    tx = ' '.join(x['text'] for x in rows.get('us', []))
    c.ok('Torres' in tx, f"{who}: the managing agent's call (R. Torres, 121 State) is not the Kleins' Waiting on Us")
    # section 10 item 5: billed gross and net, labelled, tied to the cent by one function
    if not money:
        c.ok(not re.search(r'\$\d', m['text']), f'{who}: the designer sees money on the client page')
        c.ok(not errs, f'{who} Clients: errors {errs[:2]}')
        await b.close(); return
    tie = await pg.evaluate("() => { const B = slBilled('cl121'); return [B.gross, B.ret, B.net, Math.round((B.net + B.ret - B.gross) * 100)]; }")
    c.ok(tie[3] == 0, f'{who}: billed net {tie[2]} plus retainage {tie[1]} is not gross {tie[0]} to the cent')
    await pg.evaluate("() => { const b = [...document.querySelectorAll('.view.on [data-ydtab]')].find(e => /Contract/.test(e.textContent)); b && b.click(); }")
    await pg.wait_for_timeout(150)
    txt = await pg.evaluate("() => document.querySelector('.view.on').innerText")
    c.ok(re.search(r'Billed, gross', txt) and re.search(r'Billed, net of retainage', txt), f'{who}: the client page prints Billed without gross or net')
    c.ok(not re.search(r'\bBilled\b(?!, (gross|net))', txt.replace('Left to Bill', '')), f'{who}: a "Billed" figure has no gross or net beside it')
    # section 10 item 3: a record is named by its own number
    names = await pg.evaluate("""() => { const c = DB.clients.find(x => x.id === 'cl121'); const txt = [...document.querySelectorAll('.view.on')].map(e => e.innerText).join(' ') + ' ' + (c.activity || []).map(a => typeof slActivityText === 'function' ? slActivityText(c, a) : (a.text || '')).join(' ');
       const nums = new Set(); DB.clients.forEach(x => ['invoices', 'estimates', 'changeOrders', 'cos'].forEach(k => (x[k] || []).forEach(d => d.number && nums.add(d.number)))); (DB.pos || []).forEach(p => p.number && nums.add(p.number));
       return (txt.match(/\\b(?:INV|EST|CO|PO)-[0-9][0-9-]*\\b/g) || []).filter(n => !nums.has(n)); }""")
    c.ok(not names, f'{who}: names a record by a number no record has: {sorted(set(names))[:4]}')
    plus = await pg.evaluate("() => { const b = document.querySelector('.view.on [data-ydnew]'); if (!b) return null; b.click(); return [...document.querySelectorAll('.view.on [data-ydnewitem]')].map(e => e.textContent.trim()); }")
    if uid in ('u_owner', 'u_alan'):
        c.ok(plus and 'Message' in plus and 'Task' in plus, f'{who}: the client\'s + offers {plus}')
        hd = await pg.evaluate("() => (document.querySelector('.view.on .yd-menu .yd-mh') || {}).textContent || ''")
        c.ok('Klein' in hd, f'{who}: the client\'s + is not tied to the client ({hd!r})')
    if phone: await phone_fit(c, pg, f'{who} client page')
    c.ok(not errs, f'{who} Clients: errors {errs[:2]}')
    await b.close()


async def main():
    only = sys.argv[1:]
    async with async_playwright() as p:
        for phone in (False, True):
            if not only or 'deal' in only: await estimates_and_deal(p, phone)
            for uid in ('u_owner', 'u_alan', 'u_chen'):
                if not only or 'pipeline' in only: await pipeline_as(p, uid, phone)
            for uid in ('u_owner', 'u_alan', 'u_billing', 'u_sarah'):
                if not only or 'clients' in only: await clients_as(p, uid, phone)
    sys.exit(c.done())

asyncio.run(main())
