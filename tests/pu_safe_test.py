"""PU-Safe (the coordinator's walk of Ron's jobs, 11-17): procurement is safe before any agent sends a word.
As Chen, through the screens, on the desktop and on the phone, from the seeded data (the app day 2026-09-03):
  1  a message about an order goes only to the order's own vendor (PO-2026-049, Garden State Lumber, went to Kent
     Avenue Lumber's Dana because both names carry "Lumber"); a common word never matches a vendor by itself
  2  with no email on file a follow-up is Needs Address, never "sent", and nothing downstream reads it as sent
  3  a material's internal notes never reach an RFQ, a PO's paper or its mail
  4  a unit price prints to the cent ($4.50, never $5)
  5  a line with no count asks a lump-sum price, in words
  6  a confirmation that differs is one Needs You row on Orders and Today; Accept takes its date onto the order with a
     reason; its date past the need-by escalates to the coordinator and the PM
  7  "we do not carry" is a no bid on that vendor's row, never Price Needed

    python3 pu_safe_test.py [--section desk,phone]
"""
import asyncio, re, sys, argparse
from harness import *

MODAL = """() => { const m = document.querySelector('#mbm'); if (!m || !m.getClientRects().length) return null;
  return { title: (m.querySelector('.mbm-hd h3') || {}).innerText || '', text: m.innerText,
           buttons: [...m.querySelectorAll('button')].filter(b => b.getClientRects().length).map(b => b.innerText.trim()).filter(Boolean),
           primary: [...m.querySelectorAll('button.primary')].filter(b => b.getClientRects().length).map(b => b.innerText.trim()) }; }"""
TOAST = "() => { const t = document.getElementById('toast'); return t ? t.innerText.trim() : ''; }"
TXT = "s => (document.querySelector(s) || {}).innerText || ''"
NOSIDE = "() => document.documentElement.scrollWidth - innerWidth"
NOTE = 'decide crew vs sub'
# every vendor message the app calls sent has an address: the class check for finding 2
SENT_NO_ADDR = "() => (DB.outbox || []).filter(o => /^(sent|delivered)$/.test(o.status) && !/@/.test((o.to || {}).email || '')).map(o => [o.kind, o.subject, (o.to || {}).name])"

async def modal(pg): return await pg.evaluate(MODAL)
async def toast(pg): return await pg.evaluate(TOAST)
async def view_text(pg): return await pg.evaluate(TXT, '.view.on')

async def rfq_from_board(pg, c, picks, tick):
    """The Buy Board's Table, the lines picked, Request Quotes, the stock sheet, the vendors ticked, Send."""
    await go(pg, 'proc'); await pg.wait_for_timeout(400)
    tb = pg.locator('#v-proc [data-psmode="table"]')
    if await tb.count(): await tb.first.click(); await pg.wait_for_timeout(600)
    rows = await pg.evaluate("() => [...document.querySelectorAll('#v-proc [data-psrow]')].map(r => [r.dataset.psrow, !!r.querySelector('[data-pspick]'), r.innerText.replace(/\\s+/g, ' ')])")
    for w in picks:
        hit = [r for r in rows if r[1] and w.lower() in r[2].lower()]
        c.ok(hit, f'the Buy Board has a row to pick for {w}')
        if hit: await pg.locator(f'#v-proc [data-pspick="{hit[0][0]}"]').click(); await pg.wait_for_timeout(300)
    await pg.locator('#v-proc [data-psdo="quote"]').click(); await pg.wait_for_timeout(800)
    for _ in range(2):
        m = await modal(pg)
        if m and 'Stock' in m['title']:
            await pg.locator('#mbm button').filter(has_text='Buy It Anyway').first.click(); await pg.wait_for_timeout(700)
    m = await modal(pg)
    c.ok(m and 'Request for Quote' in m['title'], f'the RFQ sheet opens ({m and m["title"]})')
    lines = await pg.evaluate("() => [...document.querySelectorAll('#mbm [data-rsi]')].map((i, k) => [i.value, document.querySelectorAll('#mbm [data-rsq]')[k].value, document.querySelectorAll('#mbm [data-rsu]')[k].value])")
    more = pg.locator('#mbm summary').filter(has_text=re.compile('More Vendors'))
    if await more.count(): await more.first.click(); await pg.wait_for_timeout(300)
    # only the vendors asked: untick the rest, tick these
    V = await pg.evaluate("() => [...document.querySelectorAll('#mbm [data-rsv]')].map(i => [i.dataset.rsv, i.checked, (i.closest('label') || i.parentElement).textContent.replace(/\\s+/g, ' ').trim()])")
    for vid, on, label in V:
        want = any(label.startswith(t) for t in tick)
        if on != want:
            loc = pg.locator(f'#mbm [data-rsv="{vid}"]')
            if await loc.is_visible(): await loc.click(); await pg.wait_for_timeout(150)
    await pg.locator('#mbm [data-f="due"]').fill('2026-09-08')
    reason = pg.locator('#mbm [data-f="reason"], #mbm #rfq-reason, #mbm textarea').first
    if await reason.count():
        try: await reason.fill('Three yards asked; the rest do not stock it this week')
        except Exception: pass
    ob0 = await pg.evaluate("() => (DB.outbox || []).length")
    await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(900)
    t = await toast(pg)
    c.ok('sent to' in t, f'the RFQ is sent ({t[:120]})')
    r = await pg.evaluate("() => { const r = DB.rfqs.slice(-1)[0]; return { id: r.id, number: r.number, status: r.status, lines: r.lines.map(l => [l.item, l.qty, l.unit, l.spec || '']) }; }")
    ob = await pg.evaluate("n => DB.outbox.slice(n).map(o => ({ kind: o.kind, to: o.to, body: o.body, att: (o.attachments || []).map(a => a.text).join('\\n') }))", ob0)
    return lines, r, ob

async def desk(p, c):
    b, pg, errs = await open_app(p, phone=False)
    await sign_in(pg, 'u_chen')
    # ---- 3 and 5: the RFQ a vendor reads
    lines, r, ob = await rfq_from_board(pg, c, ['GWB boards', 'Waterproofing membrane', 'Base molding'], ['Garden State Lumber', 'Kent Avenue Lumber', 'Harlem River Building Supply'])
    base = [l for l in lines if 'Base molding' in l[0]]
    c.ok(base and base[0][2] == 'ls', f'5: a material with no count is a lump-sum line on the sheet, not "1 ea" ({base})')
    c.ok(ob and all(NOTE not in o['body'] and NOTE not in o['att'] for o in ob), '3: no RFQ mail or sheet carries the material\'s internal note')
    c.ok(ob and all(re.search(r'Base molding & casing \| - \| 1 \| lump sum', o['body']) and 'one price for the whole line' in o['body'] for o in ob), '5: the RFQ asks for the lump-sum line as a lump sum, in words')
    c.ok(ob and all('one price for the whole line' in o['att'] for o in ob), '5: the attached sheet says one price for the whole lump-sum line')
    # ---- 7: Harlem River declines; the reply is a no bid, never Price Needed
    await pg.evaluate("""n => { DB.comms.push({ id: 'ps_nobid', from: { email: 'desk@harlemriverbuilding.example', name: 'Lou Grant' }, subject: 'Re: ' + n + ' request for quote',
        text: 'Hi Chen, regarding ' + n + ', we do not carry cement board or membrane. Thanks, Lou', date: today(), direction: 'in', proposals: [], channel: 'email' }); save(); }""", r['number'])
    await pg.evaluate("() => appSetDay('2026-09-04')")
    await pg.evaluate("id => rfqOpenFor(id)", r['id']); await pg.wait_for_timeout(500)
    if await pg.locator('#rfq-check').count(): await pg.locator('#rfq-check').first.click(); await pg.wait_for_timeout(700)
    q = await pg.evaluate("id => rfqById(id).quotes.filter(q => q.vendor === 'Harlem River Building Supply').map(q => ({ noBid: !!q.noBid, need: !!q.priceNeeded }))", r['id'])
    t = await view_text(pg)
    c.ok(q and q[0]['noBid'] and not q[0]['need'], f'7: "we do not carry" is a no bid ({q})')
    hr = [ln for ln in t.split('\n') if 'Harlem River' in ln]
    c.ok(any('No Bid' in ln for ln in t[t.find('Harlem River'):].split('\n')[:2]) and not any('Harlem River' in ln and 'Price needed' in ln for ln in t.split('\n')), f'7: the vendor\'s row reads No Bid, and it is not in Price Needed ({hr[:3]})')
    c.ok('declined (no bid)' in t, '7: the three-quote count says one declined')
    # ---- level, confirm, award (as the coordinator)
    if await pg.locator('#rfq-level').count(): await pg.locator('#rfq-level').click(); await pg.wait_for_timeout(700)
    n = 0
    while await pg.locator('[data-rfqconf]').count() and n < 5:
        await pg.locator('[data-rfqconf]').first.click(); await pg.wait_for_timeout(300)
        if await modal(pg): await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(400)
        n += 1
    if await pg.locator('#rfq-skipneg').count(): await pg.locator('#rfq-skipneg').click(); await pg.wait_for_timeout(600)
    sel = pg.locator('#rfq-award-all')
    if await sel.count():
        vid = await pg.evaluate("() => (DB.vendors.find(v => v.name === 'Garden State Lumber') || {}).id")
        await sel.select_option(vid); await pg.wait_for_timeout(300)
    if await pg.locator('#rfq-award-reason').count(): await pg.locator('#rfq-award-reason').fill('Two priced and one declined; Garden State lands in time')
    po0 = await pg.evaluate("() => DB.pos.length")
    await pg.locator('#rfq-award').click(); await pg.wait_for_timeout(900)
    po = await pg.evaluate("n => { const p = DB.pos.slice(n)[0]; return p && { id: p.id, n: p.number, v: p.vendor, vid: p.vendorId, notes: p.notes || '', price: p.lines.map(l => l.price) }; }", po0)
    c.ok(po and po['v'] == 'Garden State Lumber', f'the award makes a PO to Garden State Lumber ({po})')
    if not po: return await b.close()
    c.ok('prepaid wire' not in po['notes'] and 'use tax' not in po['notes'], f'3: the firm\'s reasoning is not in the Notes to vendor ({po["notes"][:120]})')
    # ---- 3 and 4: the order as the vendor reads it: the paper and the mail
    await pg.evaluate("id => { poOpen = id; view = 'po'; render(); }", po['id']); await pg.wait_for_timeout(700)
    t = await view_text(pg)
    paper = t[t.find('ITEM'):t.find('Subtotal')] if 'ITEM' in t else t
    c.ok(NOTE not in t, '3: the PO\'s paper does not print the internal note')
    c.ok(re.search(r'\tbd\t\$4\.50\t', paper) and not re.search(r'\t(bd|ls)\t\$5\t', paper), f'4: the unit price prints to the cent ({paper[:300]!r})')
    await pg.locator('.view.on button').filter(has_text='Draft Email to Vendor').first.click(); await pg.wait_for_timeout(600)
    body = await pg.evaluate("() => (document.querySelector('#em-body') || {}).value || ''")
    c.ok(body and NOTE not in body and '@ $4.50' in body, f'3 and 4: the PO mail has no internal note and the price to the cent ({body[:260]!r})')
    await pg.evaluate("() => { try { closeEditor(); } catch (e) {} }")
    # ---- 1 and 2: the follow-ups the days bring
    for d in ['2026-09-07', '2026-09-08', '2026-09-16']:
        await pg.evaluate("d => appSetDay(d)", d)
    fu = await pg.evaluate("""() => DB.outbox.filter(o => o.kind === 'order-followup').map(o => ({ po: (DB.pos.find(p => p.id === (o.about || {}).poId) || {}).number, to: o.to, status: o.status, need: !!o.needsAddress }))""")
    g = [o for o in fu if o['po'] == po['n']]
    c.ok(g and all(o['to']['email'] == 'sales@gardenstatelumber.example' and 'Dana' not in o['to']['name'] for o in g), f'1: {po["n"]}\'s follow-up goes to Garden State Lumber, never Kent Avenue\'s Dana ({g})')
    nm = [o for o in fu if o['po'] in ('PO-2026-047', 'PO-2026-048')]
    c.ok(nm and all(o['status'] == 'draft' and o['need'] for o in nm), f'2: follow-ups to Tino and Carlos (no email) are Needs Address, not sent ({nm})')
    c.ok(not await pg.evaluate(SENT_NO_ADDR), f'2: no message the app calls sent lacks an address ({await pg.evaluate(SENT_NO_ADDR)})')
    pr = await pg.evaluate("n => DB.pos.filter(p => ['PO-2026-047', 'PO-2026-048'].includes(p.number)).flatMap(p => (p.followups || []).map(f => [p.number, f.status, trkSent(f)]))", po['n'])
    c.ok(pr and not any(x[2] for x in pr) and all(x[1] == 'needs-address' for x in pr), f'2: the orders\' follow-ups read needs-address and trkSent is false ({pr})')
    await pg.evaluate("() => { const p = DB.pos.find(x => x.number === 'PO-2026-048'); poOpen = p.id; view = 'po'; render(); }"); await pg.wait_for_timeout(600)
    t = await view_text(pg)
    c.ok('Needs Address' in t and 'Add the Email' in t, '2: the PO\'s history says Needs Address with the step to add the email')
    await go(pg, 'home'); await pg.wait_for_timeout(400)
    ap = await pg.evaluate("() => mApprovals().filter(i => i.kind === 'draft').map(i => i.title)")
    c.ok(any(x.startswith('Needs Address: PO-2026-048') for x in ap) and not any(x.startswith('Send: PO-2026-048') for x in ap), f'2: Today asks for the address, not a Send ({[x for x in ap if "PO-2026-04" in x][:3]})')
    # the shared word never chooses by itself (the class, through the one matcher)
    cls = await pg.evaluate("""() => { if ("function" != typeof vendorNameSame) return { missing: true, same: true }; return ({ same: vendorNameSame('Garden State Lumber', 'Kent Avenue Lumber'), lumber: (vendorByName('Lumber') || {}).name || '',
        up: (vendorByName('GARDEN STATE LUMBER') || {}).name || '', empty: vendorNameSame('', 'Kent Avenue Lumber'), chase: (DB.vendors.find(v => v.name === (bnContactFor(DB.projects[0], 'Lumber yard') || {}).name) || {}).name || '',
        mail: (cmVendorFor('quotes@lumber.example', 'Quotes') || {}).name || '' }); }""")
    c.ok(not cls['same'] and not cls.get('lumber') and cls.get('up') == 'Garden State Lumber' and not cls.get('empty') and not cls.get('chase') and not cls.get('mail'), f'1: a common word names no vendor; the same name in capitals does ({cls})')
    # ---- 6: the confirmation that differs
    await pg.evaluate("""n => { const p = DB.pos.find(x => x.number === n); const L = p.lines[0];
        const t = 'GARDEN STATE LUMBER\\nOrder Acknowledgment No. ACK-7781\\nDate: Sep 16, 2026\\nAgainst ' + n + '\\n\\n' + L.item + '   ' + (L.qty - 5) + ' ' + L.unit + ' @ $' + (L.price * 1.08).toFixed(2) + '   $' + ((L.qty - 5) * +(L.price * 1.08).toFixed(2)).toFixed(2) + '\\n\\nShip date: Sep 21, 2026\\nTerms: NET 30';
        trkFileMail([{ id: 'ps_ack', date: today() + 'T10:00:00', from: 'Garden State Lumber <orders@gardenstatelumber.example>', subject: 'Order acknowledgment', text: 'Acknowledgment attached.', attachments: [{ name: 'ACK-7781.pdf', text: t }] }]); }""", po['n'])
    pm = await pg.evaluate("n => (DB.promises || []).filter(p => /ACK-7781/.test(p.what)).map(p => p.vendor)", po['n'])
    c.ok(pm and all(v == 'Garden State Lumber' for v in pm), f'1: the confirmation\'s promise is Garden State\'s ({pm})')
    await go(pg, 'home'); await pg.wait_for_timeout(400)
    tab = pg.locator('.view.on button').filter(has_text=re.compile(r'^Approvals'))
    if await tab.count(): await tab.first.click(); await pg.wait_for_timeout(500)
    t = await view_text(pg)
    c.ok(f'Confirmation differs: {po["n"]}' in t, '6a: the confirmation that differs is on Chen\'s Today')
    rk = await pg.evaluate("n => nyhRows().filter(r => r.kind === 'slip' && r.title.includes(n) && /ACK-7781 ships/.test(r.title)).length", po['n'])
    c.ok(rk == 1 and f'At risk: {po["n"]}' in t, '6c: its ship date past the need-by is on Chen\'s Today as an escalation')
    await pg.evaluate("() => { poOpen = null; view = 'po'; render(); }"); await pg.wait_for_timeout(500)
    t = await view_text(pg)
    mine = t[:t.find('Waiting on Someone Else')] if 'Waiting on Someone Else' in t else t[:t.find('Orders:')]
    c.ok('confirmation ACK-7781 differs' in mine and '20 bd confirmed of 25 bd ordered' in mine and '$4.86 a unit against $4.50' in mine and 'ships Mon, Sep 21' in mine, '6a: one Needs You row on Orders says what differs in quantity, price and date')
    act = pg.locator('[data-puact^="ack:"]')
    c.ok(await act.count() == 1, '6a: the row\'s next step is Review')
    if not await act.count(): return await b.close()
    await act.first.click(); await pg.wait_for_timeout(500)
    m = await modal(pg)
    c.ok(m and 'Confirmation Differs' in m['title'] and m['primary'] == ['Reply to the Vendor'] and 'Accept the Confirmation' in m['buttons'], f'6a: Review opens accept or reply, Reply the one blue button ({m and (m["title"], m["primary"], m["buttons"])})')
    await pg.locator('#mbm #mbm-alt').click(); await pg.wait_for_timeout(400)
    t1 = await toast(pg)
    still = await pg.evaluate("n => DB.pos.find(p => p.number === n).expected", po['n'])
    m1 = await modal(pg)
    c.ok(m1 and 'Say why you accept' in (m1['text'] + t1) and still != '2026-09-21', f'6: a price or quantity change is never accepted without a reason ({t1})')
    await pg.locator('#mbm [data-f="why"]').fill('Twenty boards cover the third floor; the price holds the job date')
    await pg.locator('#mbm #mbm-alt').click(); await pg.wait_for_timeout(600)
    t2 = await toast(pg)
    P = await pg.evaluate("n => { const p = DB.pos.find(x => x.number === n); return { exp: p.expected, conf: p.confirmed, lines: p.lines.map(l => [l.qty, l.price]) }; }", po['n'])
    c.ok(P['exp'] == '2026-09-21' and P['conf'] and P['conf']['number'] == 'ACK-7781' and P['conf']['was'] == '2026-09-07', f'6b: accepted, the confirmed date is the order\'s, the old date kept ({P})')
    # PU-Safe 2 (11-18) changed this pin: the accepted quantity and price become the order's lines (the walk found the
    # order left at 25 at $4.50, so Receive asked for 5 that never come and the bill at $4.86 was flagged again)
    c.ok(P['lines'][0] == [20, 4.86], f'6: accepting takes the confirmed quantity and price onto the order\'s line ({P["lines"][0]})')
    c.ok('ACK-7781' in t2 and 'Open' in t2, f'6: the acceptance toasts with Open ({t2})')
    t = await view_text(pg)
    c.ok('confirmation ACK-7781 differs' not in t, '6: the row leaves Needs You once accepted')
    await go(pg, 'proc'); await pg.wait_for_timeout(400)
    tb = pg.locator('#v-proc [data-psmode="table"]')
    if await tb.count(): await tb.first.click(); await pg.wait_for_timeout(600)
    row = await pg.evaluate("() => [...document.querySelectorAll('#v-proc [data-psrow]')].map(r => r.innerText.replace(/\\s+/g, ' ')).filter(t => /GWB boards/.test(t))")
    c.ok(row and any('9/21' in x and 'confirmed' in x for x in row), f'6b: the Buy Board shows the confirmed date ({[x[:200] for x in row][:2]})')
    # 6c for the PM: the escalation is on Alan's Today
    await sign_in(pg, 'u_alan'); await go(pg, 'home'); await pg.wait_for_timeout(400)
    tab = pg.locator('.view.on button').filter(has_text=re.compile(r'^Approvals'))
    if await tab.count(): await tab.first.click(); await pg.wait_for_timeout(500)
    t = await view_text(pg)
    rk = await pg.evaluate("n => nyhRows().filter(r => r.kind === 'slip' && r.title.includes(n) && /ACK-7781/.test(r.title)).length", po['n'])
    c.ok(rk == 1 and f'At risk: {po["n"]}' in t, '6c: the PM hears the confirmed date past the need-by on his Today')
    c.ok(not errs, f'no page errors ({errs[:3]})')
    await b.close()

async def phone(p, c):
    b, pg, errs = await open_app(p, phone=True)
    await sign_in(pg, 'u_chen')
    # Carlos confirms the millwork late and short; Chen reviews it on her phone and replies
    await pg.evaluate("""() => { const p = DB.pos.find(x => x.number === 'PO-2026-048'); const L = p.lines[0];
        const t = 'CARLOS MILLWORK\\nOrder Acknowledgment No. CM-311\\nAgainst PO-2026-048\\n\\n' + L.item + '   ' + L.qty + ' ' + L.unit + ' @ $' + (L.price * 1.05).toFixed(2) + '   $' + (L.qty * +(L.price * 1.05).toFixed(2)).toFixed(2) + '\\n\\nShip date: Sep 30, 2026';
        trkFileMail([{ id: 'ps_ack2', date: today() + 'T09:00:00', from: 'Carlos Millwork <shop@carlosmillwork.example>', subject: 'Acknowledgment', text: 'See attached.', attachments: [{ name: 'CM-311.pdf', text: t }] }]); }""")
    await pg.evaluate("() => { poOpen = null; view = 'po'; render(); }"); await pg.wait_for_timeout(500)
    c.ok(await pg.evaluate(NOSIDE) <= 0, 'phone: Orders never scrolls sideways')
    act = pg.locator('[data-puact^="ack:"]')
    c.ok(await act.count() == 1, 'phone: the confirmation that differs is one Needs You row on Orders')
    if await act.count():
        await act.first.click(); await pg.wait_for_timeout(500)
        m = await modal(pg)
        c.ok(m and 'Confirmation Differs' in m['title'] and m['primary'] == ['Reply to the Vendor'], 'phone: Review opens the sheet, Reply the safe step')
        c.ok(await pg.evaluate(NOSIDE) <= 0, 'phone: the sheet never scrolls sideways')
        ob0 = await pg.evaluate("() => DB.outbox.length")
        await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(600)
        o = await pg.evaluate("n => DB.outbox.slice(n).map(o => ({ kind: o.kind, status: o.status, need: !!o.needsAddress, to: o.to }))", ob0)
        t = await toast(pg)
        c.ok(o and o[0]['kind'] == 'ack-reply' and o[0]['status'] == 'draft' and o[0]['need'], f'phone: the reply is a draft, Needs Address for Carlos (no email), never sent ({o})')
        c.ok('outbox' in t and 'Open' in t, f'phone: the reply toasts with Open ({t})')
        rows = await pg.evaluate("() => puOrderRows('').filter(r => /^ack:/.test(r.id)).map(r => [r.actor, puMine(r)])")
        c.ok(rows == [], f'phone: replied, it leaves Needs You ({rows})')
    c.ok(not errs, f'no page errors ({errs[:3]})')
    await b.close()

SECTIONS = {'desk': desk, 'phone': phone}

async def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--section', default=','.join(SECTIONS))
    a = ap.parse_args(); c = Checks()
    async with async_playwright() as p:
        for s in a.section.split(','):
            print(f'-- {s}', flush=True)
            await SECTIONS[s](p, c)
    sys.exit(c.done())

asyncio.run(main())
