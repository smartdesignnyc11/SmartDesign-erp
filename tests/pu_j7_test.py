"""J7, Receive and match (the walk's J7 failed these on both devices, on live too): the three-way match reads the receipt;
the person who received holds a bill at what arrived and only the Owner approves part of a bill; a vendor's credit memo
is read as a credit on its bill, order and claim, with one tap; a bill on a two-line order keeps each line's estimate line.
Each section starts fresh, on the seeded data, the app day 2026-09-03.

    python3 pu_j7_test.py [--section match,hold,memo,lines]
"""
import asyncio, re, sys, argparse
from harness import *

MODAL = """() => { const m = document.querySelector('#mbm'); if (!m || !m.getClientRects().length) return null;
  return { title: (m.querySelector('.mbm-hd h3') || {}).innerText || '', text: m.innerText,
           buttons: [...m.querySelectorAll('button')].filter(b => b.getClientRects().length).map(b => b.innerText.trim()).filter(Boolean) }; }"""
TOAST = "() => { const t = document.getElementById('toast'); return t ? { text: t.innerText.trim(), open: !!t.querySelector('.toast-open') } : { text: '', open: false }; }"
# a 100-board drywall order on one estimate line and 200 sf of tile on another, issued; 94 boards and 169 sf good came
# (6 short, 31 cracked); the vendors bill the whole order
SETUP = """() => { setCurrent('p121'); const L = lineOptions('p121').map(o => o.key).filter(Boolean);
  const po = { id: 'po_j7', number: nextPO(), projectId: 'p121', vendor: 'Ferguson', date: today(), expected: today(), status: 'issued', shipTo: 'Site', tax: 0, shipping: 0, matchedTxns: [],
    lines: [{ id: 'j7a', item: 'Framing lumber: supply', qty: 40, unit: 'ea', price: 6.5, received: 0, line: L[0] }, { id: 'j7b', item: 'Drywall & cement board: supply', qty: 100, unit: 'ea', price: 26.5, received: 0, line: L[1] }] };
  const tile = { id: 'po_j7t', number: nextPO(), projectId: 'p121', vendor: 'Nemo Tile', date: today(), expected: today(), status: 'issued', shipTo: 'Site', tax: 0, shipping: 0, matchedTxns: [],
    lines: [{ id: 'j7c', item: 'Porcelain floor tile 12x24 matte: supply', qty: 200, unit: 'sf', price: 14.5, received: 0, line: L[1] }] };
  DB.pos.push(po, tile);
  puReceiveLines(po, [{ l: po.lines[0], q: 40 }, { l: po.lines[1], q: 94 }], 'test', 'slip.jpg');
  po.issues = [{ claim: true, status: 'open', type: 'short', lineId: 'j7b', item: po.lines[1].item, qty: 6, unit: 'ea', amount: 159 }];
  puReceiveLines(tile, [{ l: tile.lines[0], q: 169 }], 'test', 'slip.jpg');
  tile.issues = [{ claim: true, status: 'open', type: 'damaged', lineId: 'j7c', item: tile.lines[0].item, qty: 31, unit: 'sf', amount: 449.5 }];
  const mk = (id, number, v, p, amt) => ({ id, number, vendor: v, poId: p.id, projectId: 'p121', date: today(), due: today(), status: 'submitted', createdBy: 'Chen Biron', entityId: 'ent1', cat: 'materials',
    lines: [{ id: uid('bl'), desc: 'Invoice ' + number, amount: amt, poLineId: p.lines[0].id, line: p.lines[0].line }], approvals: [] });
  save(); render();   // the order's tax status and rate settle on render; each vendor bills the whole order with its tax
  DB.bills.push(mk('b_gow', 'GOW-5482', 'Ferguson', po, poTotal(po).total), mk('b_nem', 'NEM-5851', 'Nemo Tile', tile, poTotal(tile).total)); save();
  return { L: L.slice(0, 2), po: po.number, tile: tile.number, tax: [+po.tax || 0, +tile.tax || 0], gow: poTotal(po).total, nem: poTotal(tile).total }; }"""

async def modal(pg): return await pg.evaluate(MODAL)
async def toast(pg): return await pg.evaluate(TOAST)
async def bill_page(pg, number):
    await pg.evaluate("n => { const b = DB.bills.find(x => x.number === n); flowGo.bill(b)(); }", number); await pg.wait_for_timeout(600)

async def s_match(p, c):
    """the Owner: a bill over what arrived opens Approve Part on its page; the sheet says what arrived; approving it and
    disputing the rest holds the difference against the vendor"""
    for phone in (False, True):
        dev = 'phone' if phone else 'desktop'
        b, pg, errs = await open_app(p, phone)
        try:
            await sign_in(pg, 'u_chen'); S0 = await pg.evaluate(SETUP); await sign_in(pg, 'u_owner')
            r = await pg.evaluate("() => { const b = DB.bills.find(x => x.number === 'NEM-5851'), po = DB.pos.find(x => x.id === b.poId); return { left: pay3ArrivedLeft(b), over: pay3OverArrived(b), route: rtFor(b).top, want: r2(169 * 14.5 * (1 + (+po.tax || 0) / 100)), wantS: money(r2(169 * 14.5 * (1 + (+po.tax || 0) / 100))) }; }")
            want = r['want']
            c.ok(r['left'] == want and r['over'] == want and r['route'] == 'owner', f"match ({dev}): NEM-5851 is read against the receipt, 169 sf at $14.50 and the order's tax, and goes to the Owner ({r})")
            await bill_page(pg, 'NEM-5851')
            btn = pg.locator('.view.on button:visible, #drawer button:visible').filter(has_text=re.compile(r'^(Approve Part|Approve PO Amount)'))
            c.ok(await btn.count() > 0, f'match ({dev}): the bill offers Approve Part, Dispute the Rest')
            if await btn.count():
                await btn.first.click(); await pg.wait_for_timeout(500)
                m = await modal(pg)
                c.ok(m and r['wantS'] in m['text'] and 'arrived' in m['text'], f"match ({dev}): the sheet says what arrived, {r['wantS']} ({m and m['text'][:240]!r})")
                if m:
                    await pg.locator('#mbm [data-f="amount"]').fill(f'{want:.2f}')
                    await pg.locator('#mbm [data-f="why"]').fill('31 sf of tile arrived cracked (claimed)')
                    await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(700)
                    r = await pg.evaluate("() => { const b = DB.bills.find(x => x.number === 'NEM-5851'); return { st: b.status, held: (b.short || {}).held, state: (b.short || {}).state }; }")
                    t = await toast(pg)
                    c.ok(r['held'] is not None and abs(r['held'] - round(S0['nem'] - want, 2)) < 0.01 and r['state'] == 'open' and re.search(r'disputed|held', t['text'], re.I), f"match ({dev}): approved at what arrived, the rest, ${S0['nem'] - want:,.2f}, held in dispute ({r}, {t['text']!r})")
            c.ok(not errs, f'match ({dev}): page errors {errs[:2]}')
        finally:
            await b.close()

async def s_hold(p, c):
    """the coordinator who received: Hold at What Arrived on the bill, for the Owner; she cannot approve part herself"""
    b, pg, errs = await open_app(p)
    try:
        await sign_in(pg, 'u_chen'); S0 = await pg.evaluate(SETUP)
        # what arrived: 40 x $6.50 + 94 x $26.50 = $2,751, with the order's tax
        arr = round(2751 * (1 + S0['tax'][0] / 100), 2); arrS = await pg.evaluate("x => money(x)", arr)
        # the coordinator cannot open Bills and Payroll: the bill over what arrived is on the order she received
        await pg.evaluate("() => { setCurrent('p121'); poOpen = 'po_j7'; view = 'po'; render(); }"); await pg.wait_for_timeout(500)
        h = pg.locator('.view.on .pu-arr button:visible').filter(has_text=re.compile(r'^Hold at What Arrived$'))
        c.ok(await h.count() > 0, "hold: the coordinator has Hold at What Arrived for GOW-5482 on its order's page")
        if await h.count():
            await h.first.click(); await pg.wait_for_timeout(500)
            m = await modal(pg)
            c.ok(m and arrS in m['text'], f"hold: the sheet says what arrived, {arrS} ({m and m['text'][:200]!r})")
            await pg.locator('#mbm [data-f="amount"]').fill(f'{arr:.2f}')
            await pg.locator('#mbm [data-f="why"]').fill('6 cement boards not delivered (backordered); paid when they come')
            await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(600)
            r = await pg.evaluate("() => { const b = DB.bills.find(x => x.number === 'GOW-5482'); return { hold: b.arrivedHold, st: b.status, short: !!b.short, top: rtFor(b).top, aud: DB.audit.filter(a => a.refId === b.id && a.action === 'held-at-arrived').map(a => a.by) }; }")
            t = await toast(pg)
            c.ok(r['hold'] and abs(r['hold']['amount'] - arr) < 0.01 and abs(r['hold']['held'] - round(S0['gow'] - arr, 2)) < 0.01 and r['st'] == 'submitted' and not r['short'], f'hold: held at what arrived, the rest held back, nothing approved ({r})')
            c.ok(r['top'] == 'owner' and r['aud'] == ['Chen Biron'] and t['open'] and 'Owner' in t['text'], f"hold: it goes to the Owner, with Chen's audit row and a toast with Open ({r}, {t['text']!r})")
            ok = await pg.evaluate("x => { const b = DB.bills.find(y => y.number === 'GOW-5482'); return pay3ShortPay(b, x, 'test'); }", arr)
            c.ok(not ok, 'hold: the coordinator cannot approve part of the bill herself (only the Owner does)')
        c.ok(not errs, f'hold: page errors {errs[:2]}')
    finally:
        await b.close()

MEMO = """([po, amt]) => { const c = { id: 'cm_j7', msgId: 'm_j7', threadId: 't_j7', channel: 'email', direction: 'in', owner: paMe().id, subject: 'Credit memo CRE-8129 for ' + po,
  from: { name: 'Nemo Tile', email: 'ar@nemotile.example' }, to: [{ name: 'Chen Biron', email: 'chen@smartdesign.nyc' }], cc: [], date: appNowIso(), source: 'mail', status: 'new', links: [], route: null,
  text: 'Sorry about the cracked boxes. Credit memo CRE-8129 for ' + po + ': ' + amt + ' credited against invoice NEM-5851. Please take it off what you pay us.',
  attachments: [{ filename: 'Credit memo CRE-8129.pdf', name: 'Credit memo CRE-8129.pdf', text: 'CREDIT MEMO CRE-8129\\nNemo Tile\\nPO: ' + po + '\\nInvoice: NEM-5851\\n31 sf porcelain tile received damaged\\nCREDIT ' + amt }] };
  DB.comms = DB.comms || []; DB.comms.push(c); c.proposals = cmRead(c) || []; save(); return (c.proposals || []).map(p => [p.kind, p.summary || p.title || p.t || '', p.billId || '', CM_CATS[p.kind] || '']); }"""

async def s_memo(p, c):
    """the tile house's credit memo: read as a credit against NEM-5851 on its order (214 Lincoln's job in the walk; here
    121 State), applied with one tap by the coordinator who claimed it: the dispute credited and the claim closed"""
    b, pg, errs = await open_app(p)
    try:
        await sign_in(pg, 'u_chen'); S0 = await pg.evaluate(SETUP)
        await sign_in(pg, 'u_owner')
        held = await pg.evaluate("() => { const b = DB.bills.find(x => x.number === 'NEM-5851'); pay3ShortPay(b, pay3ArrivedLeft(b), '31 sf cracked, claimed'); return (b.short || {}).held; }")
        c.ok(bool(held), f'memo: the Owner approved what arrived and disputed {held}')
        await sign_in(pg, 'u_chen')
        amtS = await pg.evaluate("x => '$' + (+x).toFixed(2)", held or 0)
        P = await pg.evaluate(MEMO, [S0['tile'], amtS])
        cr = next((x for x in P if x[0] in ('credit', 'dispute-credit')), None)
        c.ok(cr and cr[3] == 'Credit memo' and 'NEM-5851' in cr[1] and S0['tile'] in cr[1] and '121 State' in cr[1] and cr[2], f'memo: read as a credit memo against NEM-5851 on {S0["tile"]} and its job ({P})')
        c.ok(not any(x[0] in ('credit', 'dispute-credit') and 'NEM-5851' not in x[1] for x in P), f'memo: not also read as a return on another purchase ({P})')
        if cr:
            did = await pg.evaluate("() => { const c = DB.comms.find(x => x.id === 'cm_j7'); const p = c.proposals.find(x => ['credit', 'dispute-credit'].includes(x.kind)); return cmApply(c, p); }")
            r = await pg.evaluate("""() => { const b = DB.bills.find(x => x.number === 'NEM-5851'), po = DB.pos.find(x => x.id === b.poId);
              return { state: (b.short || {}).state, memo: (b.short || {}).creditMemo, claims: (po.issues || []).filter(i => i.claim && i.status === 'open').length }; }""")
            c.ok(r['state'] == 'credited' and r['memo'] == 'CRE-8129' and r['claims'] == 0, f'memo: the coordinator applies it: the dispute credited (CRE-8129) and the claim closed ({r}; {did!r})')
        c.ok(not errs, f'memo: page errors {errs[:2]}')
    finally:
        await b.close()

async def s_lines(p, c):
    """a bill entered against the two-line order keeps each line's estimate line"""
    b, pg, errs = await open_app(p)
    try:
        await sign_in(pg, 'u_chen'); S0 = await pg.evaluate(SETUP)
        await pg.evaluate("() => { const po = DB.pos.find(x => x.id === 'po_j7'); vbReview({ vendor: 'Ferguson', number: 'GOW-5490', date: today(), due: today(), amount: 3910, projectId: 'p121', code: '', line: '', poId: po.id, txnId: '', src: 'mail' }); }")
        await pg.wait_for_timeout(400)
        m = await modal(pg)
        c.ok(m and 'two lines' in m['text'].lower(), f"lines: the sheet says the order's two lines keep their own estimate lines ({m and m['text'][:300]!r})")
        if m:
            await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(600)
            r = await pg.evaluate("() => { const b = DB.bills.find(x => x.number === 'GOW-5490'); return b ? b.lines.map(l => [l.poLineId, l.line, l.amount]) : null; }")
            c.ok(r and len(r) == 2 and r[0][1] == S0['L'][0] and r[1][1] == S0['L'][1] and abs(sum(x[2] for x in r) - 3910) < 0.01 and r[0][0] == 'j7a',
                 f'lines: the bill has the two lines, each on its own estimate line, adding to $3,910 ({r}; {S0["L"]})')
        c.ok(not errs, f'lines: page errors {errs[:2]}')
    finally:
        await b.close()

SECTIONS = [('match', s_match), ('hold', s_hold), ('memo', s_memo), ('lines', s_lines)]
async def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--section', default=''); a = ap.parse_args()
    want = {x.strip() for x in a.section.split(',') if x.strip()}
    c = Checks()
    async with async_playwright() as p:
        for name, fn in SECTIONS:
            if want and name not in want: continue
            n0, f0 = c.n, len(c.fail)
            try:
                await fn(p, c)
            except Exception as e:
                c.ok(False, f'{name}: crashed: {str(e)[:300]}')
            print(f'-- {name}: {c.n - n0} checks, {len(c.fail) - f0} failed')
    sys.exit(c.done())
asyncio.run(main())
