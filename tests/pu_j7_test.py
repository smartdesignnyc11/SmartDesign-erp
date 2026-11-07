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
            r = await pg.evaluate("() => { const b = DB.bills.find(x => x.number === 'NEM-5851'), po = DB.pos.find(x => x.id === b.poId); return { left: pay3ArrivedLeft(b), over: pay3OverArrived(b), route: rtFor(b).top, want: r2(169 * 14.5 * (1 + (+po.tax || 0) / 100)), wantS: money2(r2(169 * 14.5 * (1 + (+po.tax || 0) / 100))) }; }")
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
        # the order's lines carry their estimate lines' cost codes, as an order bought off the estimate does
        await pg.evaluate("() => { const po = DB.pos.find(x => x.id === 'po_j7'); po.lines.forEach(l => { const f = findLine(l.line); l.code = f ? lineCode(f.line, f.doc) : ''; }); save(); }")
        await pg.evaluate("() => { const po = DB.pos.find(x => x.id === 'po_j7'); vbReview({ vendor: 'Ferguson', number: 'GOW-5490', date: today(), due: today(), amount: 3910, projectId: 'p121', code: '', line: '', poId: po.id, txnId: '', src: 'mail' }); }")
        await pg.wait_for_timeout(400)
        m = await modal(pg)
        c.ok(m and 'two lines' in m['text'].lower(), f"lines: the sheet says the order's two lines keep their own estimate lines ({m and m['text'][:300]!r})")
        ACT = """keys => { const p = DB.projects.find(x => x.id === 'p121'), J = jobFin(p), E = J.eacLines || jobFinEacLines(J, p) || [];
          return keys.map(k => ({ fin: (lineFin(k) || {}).actual || 0, eac: ((E.find(x => x.key === k) || {}).actual) || 0, codes: J.byCode.map(r => [r.code, r.bills]) })); }"""
        before = await pg.evaluate(ACT, S0['L'])   # before the bill is entered (an entered bill is accrued cost)
        if m:
            await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(600)
            r = await pg.evaluate("() => { const b = DB.bills.find(x => x.number === 'GOW-5490'); return b ? b.lines.map(l => [l.poLineId, l.line, l.amount]) : null; }")
            c.ok(r and len(r) == 2 and r[0][1] == S0['L'][0] and r[1][1] == S0['L'][1] and abs(sum(x[2] for x in r) - 3910) < 0.01 and r[0][0] == 'j7a',
                 f'lines: the bill has the two lines, each on its own estimate line, adding to $3,910 ({r}; {S0["L"]})')
            # each estimate line's actual takes its own bill line, by every reader of cost by line (the CoS, 11-06: the
            # split bill's cost reached no estimate line, since lineFin and jobFinEacLines read only the bill's own line)
            await pg.evaluate("() => { const b = DB.bills.find(x => x.number === 'GOW-5490'); b.status = 'approved'; b.approvedAt = today(); save(); }")
            after = await pg.evaluate(ACT, S0['L'])
            amts = [x[2] for x in r] if r else [0, 0]
            d = [(round(after[i]['fin'] - before[i]['fin'], 2), round(after[i]['eac'] - before[i]['eac'], 2)) for i in range(2)]
            c.ok(all(abs(d[i][0] - amts[i]) < 0.02 for i in range(2)), f"lines: each estimate line's actual (Cost by Line) rises by its own bill line ({d} vs {amts})")
            c.ok(all(abs(d[i][1] - amts[i]) < 0.02 for i in range(2)), f"lines: each estimate line's actual in the job's lines (jobFinEacLines) rises by its own bill line ({d} vs {amts}; codes {after[0]['codes']})")
        c.ok(not errs, f'lines: page errors {errs[:2]}')
    finally:
        await b.close()

# the walk's J7 order (11-06): lumber and drywall bought as two lump-sum lines (1 ls each) off an RFQ whose awarded quote
# breaks each lot into pieces; both lots came, 6 cement boards short, reported on the line (Report a Problem)
LOT = """() => { setCurrent('p121'); const L = lineOptions('p121').map(o => o.key).filter(Boolean);
  const v = (DB.vendors || []).find(x => x.name === 'Ferguson') || {};
  const rfq = { id: 'rfq_lot', number: 'RFQ-2026-901', projectId: 'p121', status: 'awarded', lines: [{ id: 'L1', item: 'Framing lumber: supply', qty: 1, unit: 'ls' }, { id: 'L2', item: 'Drywall & cement board: supply', qty: 1, unit: 'ls' }],
    quotes: [{ id: 'q_lot', vendorId: v.id || '', vendor: 'Ferguson', round: 1, lines: [], replyText: 'QUOTATION\\nRef: RFQ-2026-901\\nL1  Framing lumber: supply  1 LS  826.80  826.80\\n     incl. 60 pc 2x4x8 SPF stud @ $5.95; 12 pc 2x6x10 SPF @ $10.90\\nL2  Drywall & cement board: supply  1 LS  2,169.00  2,169.00\\n     incl. 80 sheet 5/8\\" Type X drywall 4x8 @ $16.95; 30 sheet 1/2\\" cement board 3x5 @ $27.10\\nFreight: $45.00' }] };
  (DB.rfqs = DB.rfqs || []).push(rfq);
  const po = { id: 'po_lot', number: nextPO(), projectId: 'p121', vendor: 'Ferguson', vendorId: v.id || '', date: today(), expected: today(), status: 'issued', shipTo: 'Site', tax: 0, shipping: 0, matchedTxns: [], rfqId: rfq.id,
    lines: [{ id: 'lla', item: 'Framing lumber: supply', qty: 1, unit: 'ls', price: 826.8, received: 0, line: L[0], rfqId: rfq.id, rfqLineId: 'L1' }, { id: 'llb', item: 'Drywall & cement board: supply', qty: 1, unit: 'ls', price: 2169, received: 0, line: L[1], rfqId: rfq.id, rfqLineId: 'L2' }] };
  DB.pos.push(po); puReceiveLines(po, [{ l: po.lines[0], q: 1 }, { l: po.lines[1], q: 1 }], 'test', 'slip.jpg'); save(); render();
  return { po: po.number, L: L.slice(0, 2) }; }"""

async def s_lot(p, c):
    """a short on a lump-sum line: the claim is priced at the quoted piece (6 boards at $27.10, never 6 lots at $2,169), and
    the bill for the whole order is over what arrived by that much, for the coordinator to hold and the Owner to approve part"""
    for phone in (False, True):
        dev = 'phone' if phone else 'desktop'
        b, pg, errs = await open_app(p, phone)
        try:
            await sign_in(pg, 'u_chen'); S0 = await pg.evaluate(LOT)
            await pg.evaluate("() => deliveryProblem(DB.pos.find(x => x.id === 'po_lot'))"); await pg.wait_for_timeout(400)
            await pg.locator('#dp-type').select_option('short'); await pg.locator('#dp-line').select_option('llb')
            await pg.locator('#dp-qty').fill('6'); await pg.locator('#dp-note').fill('6 cement boards backordered, balance next week (Angel)')
            await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(500)
            iss = await pg.evaluate("() => (DB.pos.find(x => x.id === 'po_lot').issues || []).map(i => [i.type, i.qty, i.amount, i.priceFrom || ''])")
            c.ok(len(iss) == 1 and iss[0][2] == 162.6 and 'quote' in iss[0][3], f'lot ({dev}): 6 cement boards short on a 1 ls line are claimed at the quoted $27.10 each, $162.60, not at the lot price ({iss})')
            tax = await pg.evaluate("() => +DB.pos.find(x => x.id === 'po_lot').tax || 0")
            await pg.evaluate("""() => { const po = DB.pos.find(x => x.id === 'po_lot');
              DB.bills.push({ id: 'b_lot', number: 'GOW-5482', vendor: 'Ferguson', poId: po.id, projectId: 'p121', date: today(), due: today(), status: 'submitted', createdBy: 'Chen Biron', entityId: 'ent1', cat: 'materials',
                lines: [{ id: uid('bl'), desc: 'Invoice GOW-5482', amount: poTotal(po).total, poLineId: 'lla', line: po.lines[0].line }], approvals: [] }); save(); render(); }""")
            want = round((826.8 + 2169 - 162.6) * (1 + tax / 100), 2)
            r = await pg.evaluate("() => { const b = DB.bills.find(x => x.id === 'b_lot'); return { left: pay3ArrivedLeft(b), over: pay3OverArrived(b), top: rtFor(b).top }; }")
            c.ok(r['over'] is not None and abs(r['left'] - want) < 0.02 and r['top'] == 'owner', f'lot ({dev}): the whole-order bill is over what arrived, ${want:,.2f}, and goes to the Owner ({r})')
            await pg.evaluate("() => { setCurrent('p121'); poOpen = 'po_lot'; view = 'po'; render(); }"); await pg.wait_for_timeout(500)
            note = await pg.evaluate("() => { const n = document.querySelector('.view.on .pu-arr'); return n ? n.innerText : ''; }")
            wantS = await pg.evaluate("x => money2(x)", want)
            c.ok('GOW-5482' in note and wantS in note and 'cement board' in note and '162.60' in note, f'lot ({dev}): the order says what arrived, {wantS}, less the 6 cement boards claimed ({note[:240]!r})')
            # a claim whose piece the quote does not name: unknown, never a guess, and the bill still waits on what arrived
            await pg.evaluate("""() => { const po = DB.pos.find(x => x.id === 'po_lot'); po.issues.push({ claim: true, status: 'open', type: 'damaged', lineId: 'lla', qty: 2, note: 'two came split', item: po.lines[0].item, unit: 'ls',
              ...puClaimAmount(po, po.lines[0], 2, 'two came split') }); }""")
            r = await pg.evaluate("() => { const po = DB.pos.find(x => x.id === 'po_lot'), i = po.issues[1]; return { amt: i.amount, words: pay3ClaimWords(po) }; }")
            c.ok(r['amt'] is None and 'not on the order' in r['words'], f'lot ({dev}): a claim the quote cannot price is not guessed ({r})')
            c.ok(not errs, f'lot ({dev}): page errors {errs[:2]}')
        finally:
            await b.close()

async def s_phone(p, c):
    """the phone's Deliveries: Receive opens the one receive sheet on the order; the lot that came with 6 cement boards
    short is received and the 6 boards claimed at the quoted price"""
    b, pg, errs = await open_app(p, True)
    try:
        await sign_in(pg, 'u_chen')
        await pg.evaluate(LOT.replace("puReceiveLines(po, [{ l: po.lines[0], q: 1 }, { l: po.lines[1], q: 1 }], 'test', 'slip.jpg'); ", ''))
        await pg.evaluate("() => { setCurrent('p121'); view = 'recv'; render(); }"); await pg.wait_for_timeout(600)
        btn = pg.locator('.view.on [data-purecv="po_lot"]:visible')
        c.ok(await btn.count() == 1 and (await btn.first.inner_text()).strip() == 'Receive', "phone: the order has Receive on its Deliveries row, under Arriving")
        if await btn.count():
            await btn.first.click(); await pg.wait_for_timeout(500)
            m = await modal(pg)
            no = await pg.evaluate("() => DB.pos.find(x => x.id === 'po_lot').number")
            c.ok(m and no in m['title'] and 'Short' in m['buttons'] and 'Damaged' in m['buttons'] and 'Photo of the Slip' in m['text'], f"phone: Receive opens the receive sheet on {no}: a count and a condition per line, the slip's photo ({m and m['title']!r}, {m and m['buttons'][:8]})")
            if m:
                await pg.locator('#mbm [data-purq="lla"]').fill('1'); await pg.locator('#mbm [data-purq="llb"]').fill('1')
                await pg.locator('#mbm [data-pucond="short"][data-pul="llb"]').click(); await pg.wait_for_timeout(200)
                bad = pg.locator('#mbm [data-pubad="llb"]')
                c.ok(await bad.is_visible(), 'phone: Short on the 1 ls drywall line asks how many pieces are short')
                await bad.fill('6'); await pg.locator('#mbm [data-punote]').fill('6 cement boards short: backordered, balance next week')
                await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(600)
                r = await pg.evaluate("() => { const po = DB.pos.find(x => x.id === 'po_lot'); return { got: po.lines.map(l => l.received), iss: (po.issues || []).map(i => [i.type, i.qty, i.unit, i.amount]) }; }")
                t = await toast(pg)
                c.ok(r['got'] == [1, 1] and r['iss'] == [['short', 6, 'pc', 162.6]] and 'claimed' in t['text'], f"phone: both lots received, the 6 boards claimed at $162.60 ({r}, {t['text'][:160]!r})")
        c.ok(not errs, f'phone: page errors {errs[:2]}')
    finally:
        await b.close()

async def s_stmt(p, c):
    """a vendor's mail that names no order is put on their one open order only if that order existed when it was sent
    (Nemo's 9/1 statement was read onto PO-2026-050, issued 9/4, and NEM-5851 was flagged as billed twice)"""
    b, pg, errs = await open_app(p)
    try:
        await sign_in(pg, 'u_chen'); S0 = await pg.evaluate(SETUP)
        r = await pg.evaluate("""() => { const open = DB.pos.filter(po => po.vendor === 'Nemo Tile' && ['issued', 'partial'].includes(po.status)).map(po => po.number);
          const m = d => ({ date: d + 'T18:00:00.000Z', subject: 'Statement', text: 'There is 1 invoice outstanding: #88431, $2,140.', attachments: [] });
          const before = cmBillPO(m('2026-09-01'), { vendor: 'Nemo Tile' }), after = cmBillPO(m(today()), { vendor: 'Nemo Tile' });
          return { open, before: before && before.number, after: after && after.number }; }""")
        c.ok(r['open'] == [S0['tile']] and r['before'] is None and r['after'] == S0['tile'], f"stmt: a statement sent before {S0['tile']} existed is not read onto it; one sent after is ({r})")
        c.ok(not errs, f'stmt: page errors {errs[:2]}')
    finally:
        await b.close()

# a credit memo mail from a vendor against one of their bills: (id, po number, bill number, amount text, memo number or '')
MAIL = """([id, po, bill, amt, memo, vendor, email]) => { const c = { id: id, msgId: 'm_' + id, threadId: 't_' + id, channel: 'email', direction: 'in', owner: paMe().id,
  subject: (memo ? 'Credit memo ' + memo : 'Credit') + ' for ' + po, from: { name: vendor, email: email }, to: [{ name: 'Chen Biron', email: 'chen@smartdesign.nyc' }], cc: [], date: appNowIso(),
  source: 'mail', status: 'new', links: [], route: null,
  text: (memo ? 'Credit memo ' + memo : 'A credit') + ' for ' + po + ': ' + amt + ' credited against invoice ' + bill + '. Please take it off what you pay us.', attachments: [] };
  DB.comms = DB.comms || []; DB.comms.push(c); c.proposals = cmRead(c) || []; save();
  const p = c.proposals.find(x => ['credit', 'dispute-credit'].includes(x.kind)); return p ? { kind: p.kind, memo: p.memo || '', text: p.summary || p.title || p.t || '' } : null; }"""
APPLY = """id => { const c = DB.comms.find(x => x.id === id), p = c.proposals.find(x => ['credit', 'dispute-credit'].includes(x.kind)); const did = cmApply(c, p);
  return { did: did || '', applied: p.applied || '', waits: p.waits || '' }; }"""
BILL = """n => { const b = DB.bills.find(x => x.number === n), po = DB.pos.find(x => x.id === b.poId);
  return { state: (b.short || {}).state || '', held: (b.short || {}).held || 0, claims: (po.issues || []).map(i => [i.type, i.lineId, i.status]),
    aud: DB.audit.filter(a => a.refId === b.id && a.action === 'credit-memo-applied').map(a => a.after), owed: retList().filter(r => (r.fromCredit || {}).billId === b.id).map(r => [r.unitCost * r.qty, r.expect]) }; }"""

async def s_memo2(p, c):
    """the CoS's credit memo rules (11-06): who may apply it, its number, never more than the dispute (the rest to Owed
    Back), a paid bill's credit is a refund due, a memo that arrived first waits for the dispute and then offers to
    apply, claims close only up to the memo (the backordered boards stay open), an audit row, the Owner's brief"""
    b, pg, errs = await open_app(p)
    try:
        await sign_in(pg, 'u_chen'); S0 = await pg.evaluate(SETUP)
        # the drywall order: 6 boards short (backordered) on the drywall line, and 2 studs cracked on the lumber line
        await pg.evaluate("""() => { const po = DB.pos.find(x => x.id === 'po_j7');
          po.issues.push({ claim: true, status: 'open', type: 'damaged', lineId: 'j7a', item: po.lines[0].item, qty: 2, unit: 'ea', amount: 13, note: '2 studs cracked' }); save(); }""")
        # 1. a memo that arrives before the dispute: read as a credit on GOW-5482, says it waits, and does not apply
        r = await pg.evaluate(MAIL, ['cm_a', S0['po'], 'GOW-5482', '$14.15', 'CM-4410', 'Ferguson', 'ar@ferguson.example'])
        c.ok(r and 'before the dispute' in r['text'], f'memo2: a memo before the dispute says it waits for it ({r})')
        a = await pg.evaluate(APPLY, 'cm_a')
        c.ok(not a['applied'] and 'before the dispute' in a['waits'], f'memo2: applying it before the dispute leaves it unapplied, saying why ({a})')
        # the Owner approves what arrived and disputes the 2 cracked studs (with tax); the waiting memo now offers to apply
        await sign_in(pg, 'u_owner')
        held = await pg.evaluate("t => { const b = DB.bills.find(x => x.number === 'GOW-5482'); pay3ShortPay(b, r2(billTotal(b) - 13 * (1 + t / 100)), '2 studs cracked, claimed'); return (b.short || {}).held; }", S0['tax'][0])
        row = await pg.evaluate("() => { const b = DB.bills.find(x => x.number === 'GOW-5482'); return (nyhRowsAll() || []).filter(x => x.key === 'lk:disp:' + b.id || x.commId === 'cm_a').map(x => [x.title, x.pkind]); }")
        c.ok(row and 'applies now' in row[0][0], f'memo2: once the dispute is open, the waiting memo offers to apply ({row}, held {held})')
        # 2. who: the PM may not apply it; it stays unapplied
        await sign_in(pg, 'u_alan')
        a = await pg.evaluate(APPLY, 'cm_a')
        c.ok(not a['applied'] and 'Owner' in a['waits'], f'memo2: the PM cannot apply a vendor credit memo; it stays unapplied ({a})')
        # 3. the coordinator applies it: the studs' claim closes, the backordered boards' claim stays open, an audit row
        await sign_in(pg, 'u_chen')
        a = await pg.evaluate(APPLY, 'cm_a')
        B = await pg.evaluate(BILL, 'GOW-5482')
        c.ok(a['applied'] and B['state'] == 'credited', f'memo2: the coordinator applies it ({a})')
        c.ok(['damaged', 'j7a', 'closed'] in B['claims'] and ['short', 'j7b', 'open'] in B['claims'], f"memo2: the memo closes the cracked studs' claim only; the backordered boards' claim stays open ({B['claims']})")
        c.ok(len(B['aud']) == 1 and B['aud'][0]['memo'] == 'CM-4410', f"memo2: one audit row for the apply ({B['aud']})")
        # 4. more than is held: the dispute closes and the rest is a vendor credit under Owed Back, not lost
        await sign_in(pg, 'u_owner')
        await pg.evaluate("() => { const b = DB.bills.find(x => x.number === 'NEM-5851'); pay3ShortPay(b, r2(billTotal(b) - 100), 'test: 100 disputed'); }")
        await sign_in(pg, 'u_chen')
        r = await pg.evaluate(MAIL, ['cm_b', S0['tile'], 'NEM-5851', '$150.00', 'CRE-9001', 'Nemo Tile', 'ar@nemotile.example'])
        a = await pg.evaluate(APPLY, 'cm_b')
        B = await pg.evaluate(BILL, 'NEM-5851')
        c.ok(a['applied'] and B['state'] == 'credited' and [50, 'refund'] in [[round(x[0], 2), x[1]] for x in B['owed']], f"memo2: $150 against $100 held: the dispute closes and $50 is a vendor credit under Owed Back ({a}; {B['owed']})")
        # 5. the memo's number is required
        await pg.evaluate("() => { DB.bills.push({ id: 'b_nono', number: 'FER-7781', vendor: 'Ferguson', poId: 'po_j7', projectId: 'p121', date: today(), due: today(), status: 'submitted', createdBy: 'Chen Biron', entityId: 'ent1', cat: 'materials', lines: [{ id: uid('bl'), desc: 'x', amount: 500 }], approvals: [] }); save(); }")
        await sign_in(pg, 'u_owner')
        await pg.evaluate("() => { const b = DB.bills.find(x => x.id === 'b_nono'); pay3ShortPay(b, 400, 'test: 100 disputed'); }")
        await sign_in(pg, 'u_chen')
        await pg.evaluate(MAIL, ['cm_c', S0['po'], 'FER-7781', '$100.00', '', 'Ferguson', 'ar@ferguson.example'])
        a = await pg.evaluate(APPLY, 'cm_c')
        c.ok(not a['applied'] and 'number' in a['waits'], f"memo2: a memo with no number of its own is not applied ({a})")
        # 6. a paid bill: the credit is a refund due under Owed Back, to match a bank line
        await pg.evaluate("() => { const b = DB.bills.find(x => x.id === 'b_nono'); b.short.paid = true; save(); }")
        await pg.evaluate(MAIL, ['cm_d', S0['po'], 'FER-7781', '$100.00', 'CM-5512', 'Ferguson', 'ar@ferguson.example'])
        a = await pg.evaluate(APPLY, 'cm_d')
        B = await pg.evaluate(BILL, 'FER-7781')
        c.ok(a['applied'] and 'refund due' in a['applied'] and [100, 'refund'] in [[round(x[0], 2), x[1]] for x in B['owed']], f"memo2: on a paid bill the credit is a refund due under Owed Back ({a}; {B['owed']})")
        # 7. the Owner's brief shows the credits applied
        await sign_in(pg, 'u_owner')
        t = await pg.evaluate("() => (paBriefModel(true).today || []).filter(x => x.k === 'Vendor Credit').map(x => x.title)")
        c.ok(any('GOW-5482' in x for x in t) and any('NEM-5851' in x for x in t), f"memo2: the Owner's brief lists the vendor credits applied ({t})")
        c.ok(not errs, f'memo2: page errors {errs[:2]}')
    finally:
        await b.close()

SECTIONS = [('match', s_match), ('hold', s_hold), ('memo', s_memo), ('lines', s_lines), ('lot', s_lot), ('phone', s_phone), ('stmt', s_stmt), ('memo2', s_memo2)]
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
