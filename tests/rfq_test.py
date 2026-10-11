"""RFQ: AI-run requests for quote, from the plans to the negotiated price (BACKLOG §1.8, phase one).
Walks the flow as the people who do it, on the seeded demo (app day 2026-09-03, 121 State) with the invented
supply houses and their invented replies in the Demo Workspace:

  takeoff   rfqFramingTakeoff (the one takeoff function) against an independent Python computation
  lines     New RFQ opens on "Which Lines?" at 390px: one estimate line, then several (the framing lump sum
            gets the assistant's material list, approved first); each RFQ line keeps estimateLineId/coLineId
            and the line's budget; the line drill-down shows the line's RFQs
  foreman   the foreman at 390px: For You > Review, steppers, remove, add, Send Back with a note (redraft), Approve
            (44px targets, no sideways scroll); then it waits on the coordinator
  send      the coordinator picks vendors (each with a because, one outside NYC) and presses Send RFQ
  quotes    the app day advances: replies are read (table, PDF text, partial with an alternate, a scan nobody can
            read, one that never answers); flags; a chase draft; the unreadable one is entered by hand later
  level     leveling numbers against an independent Python computation; phone stacked cards, desktop grid
  negotiate drafts name no competitor and cite only figures from received quotes; approve; round two read
  award     POs through poAction, linked to the RFQ and the estimate line (po.origin rfq); savings correct
  matbudget savings against budget use the line's MATERIAL portion (merge review): no split shows "No material
            budget on this line" and no figure; a split counts only the material; an old award is re-read
  invoice   invoice lines (T&M, reimbursable) are RFQ sources: Which Lines?, invoiceLineId on every RFQ and PO
            line, the material budget of the line, and the invoice line's drill-down shows its RFQs
  prospect  a supplier named in a reply is a prospect; Add puts it on file and the next RFQ suggests it
  research  sourcing research: facts with sources apart from hypotheses, landed cost against Python, a species or
            grade change flagged as a substitution, Add to Next RFQ
  watch     every RFQ predicate's count equals its rows; queue and CATCH; Ask; erpQuery; reload persistence

    python3 rfq_test.py
"""
import asyncio, math, re, sys, json
from harness import *

def r2(x):
    return math.floor(100 * x + 0.5) / 100

def takeoff_py(rooms, A=None):
    A = dict({'wallHeight': 9, 'studSpacing': 16, 'joistSpacing': 16, 'span': 20, 'floorFramedPct': 25, 'waste': 10}, **(A or {}))
    s = lambda k: sum(r.get(k, 0) for r in rooms)
    n = len(rooms); wall = s('wallSf'); floor = s('floorSf'); doors = s('doors'); win = s('windows')
    w = 1 + A['waste'] / 100
    wallLf = math.ceil(wall / A['wallHeight'])
    field = math.ceil(wallLf * 12 / A['studSpacing'])
    studs = math.ceil((field + n * 8 + n * 2 + doors * 4 + win * 2) * w)
    plates = math.ceil(3 * wallLf / 16 * w)
    headers = math.ceil(doors * w)
    F = floor * A['floorFramedPct'] / 100
    run = F / A['span']
    jr = math.ceil(run * 12 / A['joistSpacing']) + 1 if F > 0 else 0
    joists = math.ceil(jr * w)
    rim = math.ceil(2 * run / 16 * w)
    rows = max(1, math.floor(A['span'] / 8))
    block = math.ceil(run * rows / 8 * w) if F > 0 else 0
    sub = math.ceil(F / 32 * w)
    hang = 2 * jr
    nc = studs * 8 + plates * 16 + joists * 12 + block * 6
    out = {'stud': studs, 'plate': plates, 'header': headers, 'joist': joists, 'rim': rim, 'block': block, 'subfloor': sub,
           'hanger': hang, 'nails': math.ceil(nc / 2500) if nc else 0, 'hnails': math.ceil(hang * 10 / 1000) if hang else 0,
           'adhesive': math.ceil(sub / 4)}
    return {k: v for k, v in out.items() if v > 0}

def level_py(rfq, V, rate):
    """Independent leveling: latest readable round per vendor, same spec only, whole basket, per line, best split.
    Landed = goods + freight + minimum shortfall + NY tax (sales or use, the same rate) + a hand-unload allowance
    when the vendor has neither a lift gate nor carry-in."""
    def extra(vid, g):
        v = V.get(vid, {}); d = v.get('delivery') or {}
        hand = 120 if d and not d.get('liftGate') and not d.get('carryIn') else 0
        return r2(g * rate / 100) + hand
    latest = {}
    for q in rfq['quotes']:
        if q.get('unreadable'): continue
        if q['vendorId'] not in latest or latest[q['vendorId']]['round'] < q['round']: latest[q['vendorId']] = q
    Q = sorted(latest.values(), key=lambda q: q['vendor'])
    lines = rfq['lines']
    def unit(q, lid):
        x = next((y for y in q['lines'] if y['lineId'] == lid), None)
        return x['unit'] if x and not x.get('missing') and x.get('unit') is not None and not x.get('sub') else None
    baskets = []
    for q in Q:
        if all(unit(q, l['id']) is not None for l in lines):
            g = 0
            for l in lines: g = r2(g + r2(unit(q, l['id']) * l['qty']))
            sf = r2(max(0, (q.get('min') or 0) - g))
            baskets.append((q['vendor'], r2(g + (q.get('freight') or 0) + sf + r2(g * rate / 100) + (extra(q['vendorId'], g) - r2(g * rate / 100)))))
    baskets.sort(key=lambda b: b[1])
    best = None
    for mask in range(1, 1 << len(Q)):
        sub = [q for i, q in enumerate(Q) if mask & (1 << i)]
        assign = {}
        ok = True
        for l in lines:
            c = sorted([(unit(q, l['id']), q['vendor'], q) for q in sub if unit(q, l['id']) is not None], key=lambda x: (x[0], x[1]))
            if not c: ok = False; break
            assign[l['id']] = c[0][2]['vendorId']
        if not ok: continue
        by = {}
        for l in lines:
            vid = assign[l['id']]; q = latest[vid]
            by[vid] = r2(by.get(vid, 0) + r2(unit(q, l['id']) * l['qty']))
        tot = 0
        for vid, g in by.items():
            q = latest[vid]
            tot = r2(tot + r2(g + (q.get('freight') or 0) + r2(max(0, (q.get('min') or 0) - g)) + r2(g * rate / 100) + (extra(vid, g) - r2(g * rate / 100))))
        if best is None or tot < best[0] - 0.004 or (abs(tot - best[0]) < 0.005 and len(by) < best[2]): best = (tot, assign, len(by))
    perline = {}
    for l in lines:
        P = sorted([(unit(q, l['id']), q['vendor']) for q in Q if unit(q, l['id']) is not None])
        perline[l['id']] = P[0] if P else None
    return {'baskets': baskets, 'split': best[0] if best else None, 'assign': best[1] if best else None, 'perline': perline}

RFQ = "id => JSON.parse(JSON.stringify(DB.rfqs.find(r => r.id === id || r.number === id)))"
NOSIDE = "() => document.documentElement.scrollWidth <= innerWidth + 1"
SMALL_TAPS = """sel => [...document.querySelectorAll(sel)].filter(b => b.getClientRects().length).map(b => { const r = b.getBoundingClientRect(); return [b.getAttribute('aria-label') || b.innerText.trim(), Math.round(r.width), Math.round(r.height)]; }).filter(x => x[1] < 44 || x[2] < 44)"""
PRED_EQ = """() => ['rfqForeman','rfqPurchasing','rfqNoReply','rfqLeveledNoNeg','rfqUnderQuoted','rfqNoOutNyc'].map(k => [k, PRED[k].count(), PRED[k].rows().length, PRED[k].label])"""

# The PM splits l4, then l2, into material and labour; the walk then puts the seed back.
MATSPLIT = """id => { signIn('u_alan'); const a = rfqSetMatBudget('estimate:es1:l4', 21000); const L1 = rfqLevel(DB.rfqs.find(r => r.id === id));
  const one = [L1.budgets.map(b => [b.key, b.budget]), L1.budgetComplete, L1.budgetTotal];
  rfqSetMatBudget('estimate:es1:l2', 14000); const L2 = rfqLevel(DB.rfqs.find(r => r.id === id));
  const E = DB.clients.flatMap(c => c.estimates).find(e => e.id === 'es1'), l4 = E.lines.find(l => l.id === 'l4');
  const two = [L2.budgets.map(b => [b.key, b.budget]), L2.budgetComplete, L2.budgetTotal, l4.costMaterial, l4.costLabor];
  const t = (document.getElementById('toast') || {}).innerText || '';
  E.lines.forEach(l => { delete l.costMaterial; delete l.costLabor; }); save();
  signIn('u_chen'); return { one, two, t, a: !!a }; }"""
# An invented T&M invoice on 121 State: a T&M line split into material and labour, and a reimbursable line.
TM_INVOICE = """() => { const c = DB.clients.find(c => c.invoices.some(i => i.projectId === 'p121'));
  c.invoices.push({ id: 'inTM1', type: 'invoice', number: 'INV-2026-T01', title: 'T&M repairs', date: '2026-09-02', due: '2026-09-09', status: 'sent', projectId: 'p121',
    lines: [{ id: 'tm1', item: 'T&M — rear stair stringer repair', desc: 'materials and labour', qty: 1, unit: 'ls', rate: 2400, cost: 1800, costMaterial: 950, taxable: false },
            { id: 'tm2', item: 'Reimbursable — LVL beam', qty: 1, unit: 'ls', rate: 704, cost: 640, cat: 'reimbursable', taxable: false }],
    discount: { type: 'pct', value: 0 }, taxRate: 0, retainagePct: 0, terms: '', memo: '', internal: '' }); save(); }"""

# An award stamped the old way (against the whole line) is re-read by rfqSavings; the award is put back after.
OLD_AWARD = """id => { const r = DB.rfqs.find(x => x.id === id), keep = JSON.parse(JSON.stringify(r.award));
  r.award.budget = 32000; r.award.savingsVsBudget = Math.round((32000 - r.award.final) * 100) / 100; delete r.award.budgetBasis; delete r.award.budgetNote;
  const s = rfqSavings('2026-09'), out = { vs: r.award.savingsVsBudget, sb: s.vsBudget, nb: s.noBudget, basis: r.award.budgetBasis, was: r.award.budgetWas };
  r.award = keep; return out; }"""

async def ok_modal(pg, wait=500):
    await pg.locator('#mbm #mbm-ok').click(timeout=4000); await pg.wait_for_timeout(wait)

async def main():
    C = Checks()
    async with async_playwright() as p:
        b, pg, errs = await open_app(p, phone=True)

        # ---- takeoff: the one function against Python
        cases = [
            [{'wallSf': 420, 'floorSf': 168, 'doors': 2, 'windows': 2}, {'wallSf': 260, 'floorSf': 48, 'doors': 1, 'windows': 1}],
            [{'wallSf': 1000, 'floorSf': 640, 'doors': 5, 'windows': 0}],
            [{'wallSf': 333, 'floorSf': 0, 'doors': 0, 'windows': 3}, {'wallSf': 95, 'floorSf': 77, 'doors': 1, 'windows': 0}, {'wallSf': 12, 'floorSf': 5, 'doors': 0, 'windows': 0}],
        ]
        for i, rooms in enumerate(cases):
            for A in (None, {'waste': 15, 'studSpacing': 12, 'wallHeight': 8}):
                js = await pg.evaluate("([R, A]) => { const T = rfqFramingTakeoff(R, A || undefined); return { q: Object.fromEntries(T.lines.map(l => [l.key, l.qty])), d: T.lines.every(l => l.derivation && l.assumption) }; }", [rooms, A])
                C.ok(js['q'] == takeoff_py(rooms, A), f'takeoff case {i} {A}: JS {js["q"]} vs Python {takeoff_py(rooms, A)}')
                C.ok(js['d'], f'takeoff case {i}: every line shows its derivation and its assumption')

        # ---- lines: New RFQ opens on Which Lines? (phone), one estimate line, then several with the lump-sum breakdown
        await sign_in(pg, 'u_chen')
        await pg.evaluate("() => { setCurrent('p121'); }")
        await go(pg, 'rfq')
        C.ok(await pg.evaluate(NOSIDE), 'phone: the RFQ page does not scroll sideways (empty)')
        await pg.locator('#rfq-new').click(); await pg.wait_for_timeout(400)
        m = await pg.evaluate("() => ({ txt: (document.querySelector('#mbm') || {}).innerText || '', t: (document.querySelector('#mbm h3') || {}).innerText, rows: [...document.querySelectorAll('[data-rfqpk]')].map(i => i.dataset.rfqpk), prim: [...document.querySelectorAll('#mbm .btn.primary')].map(b => b.innerText), plans: !!document.querySelector('#rfq-plans:not(.primary)'), blank: !!document.querySelector('#rfq-blank:not(.primary)') })")
        C.ok(m['t'] == 'Which Lines?' and m['prim'] == ['Create RFQ'] and m['plans'] and m['blank'], f'New RFQ opens on Which Lines? with one blue Create RFQ; From Plans and Start Blank are secondary ({m})')
        C.ok('estimate:es1:l3' in m['rows'] and 'estimate:es1:l2' in m['rows'], f'the sheet lists the job\'s estimate lines ({m["rows"][:6]})')
        C.ok(await pg.evaluate(NOSIDE), 'phone: Which Lines? does not scroll sideways')
        await pg.locator('[data-rfqpk="estimate:es1:l3"]').check(); await ok_modal(pg)
        one = await pg.evaluate("() => { const r = DB.rfqs.slice(-1)[0]; return JSON.parse(JSON.stringify(r)); }")
        est = await pg.evaluate("() => { const e = DB.clients.flatMap(c => c.estimates).find(e => e.id === 'es1'); return Object.fromEntries(e.lines.map(l => [l.id, +l.cost || 0])); }")
        l1 = one['lines'][0] if one['lines'] else {}
        C.ok(len(one['lines']) == 1 and l1.get('estimateLineId') == 'l3' and l1.get('line') == 'estimate:es1:l3' and l1.get('budget') is None, f'one estimate line: the RFQ line keeps estimateLineId l3; supply-and-install with no split has no material budget ({l1})')
        C.ok('No material budget on this line' in m['txt'] and 'budget $29,700' not in m['txt'], 'the sheet says when a line has no material budget, never the whole line as a budget')
        C.ok(one['status'] == 'foreman-review', f'an estimate line is field material: it goes to the foreman ({one["status"]})')
        await pg.evaluate("() => rfqLinesSheet('p121')"); await pg.wait_for_timeout(300)
        for k in ('estimate:es1:l2', 'estimate:es1:l4'):
            await pg.locator(f'[data-rfqpk="{k}"]').check()
        await ok_modal(pg)
        bd = await pg.evaluate("() => ({ t: (document.querySelector('#mbm h3') || {}).innerText || '', txt: (document.querySelector('#mbm') || {}).innerText || '' })")
        C.ok('Material List' in bd['t'] and 'Assumed' in bd['txt'], f'a lump-sum framing line gets a proposed material list with its assumptions, approved first ({bd["t"]})')
        C.ok(await pg.evaluate("() => DB.rfqs.length") == 1, 'nothing is created before the person approves the breakdown')
        await ok_modal(pg, 800)
        multi = await pg.evaluate("() => JSON.parse(JSON.stringify(DB.rfqs.slice(-1)[0]))")
        fr = [l for l in multi['lines'] if l.get('estimateLineId') == 'l2']
        C.ok(len(fr) >= 8 and all(l.get('line') == 'estimate:es1:l2' for l in fr) and any(l.get('estimateLineId') == 'l4' for l in multi['lines']), f'multi-select: the breakdown lines keep l2, the other line keeps l4 ({len(fr)} framing lines)')
        lv = await pg.evaluate("id => { const L = rfqLevel(DB.rfqs.find(r => r.id === id)); return [L.budgets.map(b => [b.key, b.budget]), L.budgetComplete, L.budgetTotal]; }", multi['id'])
        C.ok(sorted(lv[0]) == sorted([['estimate:es1:l2', None], ['estimate:es1:l4', None]]) and lv[1] is False and lv[2] == 0, f'no split on the lines: no material budget and no total to measure against ({lv})')
        # ---- matbudget: a split counts only the material; a line with none is never measured
        mb = await pg.evaluate(MATSPLIT, multi['id'])
        C.ok(mb['a'] and sorted(mb['one'][0]) == sorted([['estimate:es1:l2', None], ['estimate:es1:l4', 21000]]) and mb['one'][1] is False and mb['one'][2] == 0, f'one line split: its material counts, the other still has none, so no total is claimed ({mb["one"]})')
        C.ok(mb['two'][1] is True and mb['two'][2] == 35000 and mb['two'][3] == 21000 and mb['two'][4] == est['l4'] - 21000, f'both split: the budget is the material portions only, 35,000, not the lines\' {est["l2"] + est["l4"]} ({mb["two"]})')
        C.ok('material budget' in mb['t'], f'setting the split toasts ({mb["t"][:80]})')
        nopm = await pg.evaluate("() => { signIn('u_chen'); return rfqSetMatBudget('estimate:es1:l4', 100); }")
        C.ok(nopm is None, 'the coordinator cannot set a line\'s budget split (owner or PM)')

        # ---- invoice: T&M and reimbursable invoice lines are RFQ sources (Alan: purchases start from estimate or invoice lines)
        await pg.evaluate(TM_INVOICE)
        await pg.evaluate("() => rfqLinesSheet('p121')"); await pg.wait_for_timeout(300)
        iv = await pg.evaluate("() => ({ keys: [...document.querySelectorAll('[data-rfqpk]')].map(i => i.dataset.rfqpk), txt: (document.querySelector('#mbm') || {}).innerText || '' })")
        C.ok('invoice:inTM1:tm1' in iv['keys'] and 'invoice:inTM1:tm2' in iv['keys'] and 'invoice' in iv['txt'].lower(), f'Which Lines? lists the invoice lines ({[k for k in iv["keys"] if k.startswith("invoice")]})')
        C.ok('No material budget on this line' in iv['txt'] and 'material budget $950' in iv['txt'] and 'material budget $640' in iv['txt'], 'each row shows its material budget, or says there is none')
        C.ok(await pg.evaluate(NOSIDE), 'phone: Which Lines? with invoice lines does not scroll sideways')
        for k in ('invoice:inTM1:tm1', 'invoice:inTM1:tm2'):
            await pg.locator(f'[data-rfqpk="{k}"]').check()
        await ok_modal(pg, 600)
        inv = await pg.evaluate("() => JSON.parse(JSON.stringify(DB.rfqs.slice(-1)[0]))")
        got = sorted((l.get('invoiceLineId'), l.get('invoiceId'), l.get('line'), l.get('budget')) for l in inv['lines'])
        C.ok(got == [('tm1', 'inTM1', 'invoice:inTM1:tm1', 950), ('tm2', 'inTM1', 'invoice:inTM1:tm2', 640)], f'each RFQ line keeps invoiceLineId and the material budget ({got})')
        ilv = await pg.evaluate("id => { const L = rfqLevel(DB.rfqs.find(r => r.id === id)); return [L.budgetComplete, L.budgetTotal]; }", inv['id'])
        C.ok(ilv == [True, 1590], f'the invoice lines\' material budgets add up: 950 + 640 ({ilv})')
        dr = await pg.evaluate("() => { finLineModal('invoice:inTM1:tm1'); const t = (document.querySelector('#mbm .rfq-onl') || {}).innerText || ''; mbCloseModal(); return t; }")
        C.ok(inv['number'] in dr and 'Create RFQ' in dr, f'the invoice line drill-down shows its RFQs and Create RFQ ({dr[:120]})')
        await pg.evaluate("id => { DB.rfqs.find(r => r.id === id).status = 'closed'; save(); }", inv['id'])
        dr = await pg.evaluate("() => { finLineModal('estimate:es1:l2'); const t = (document.querySelector('#mbm .rfq-onl') || {}).innerText || ''; mbCloseModal(); return t; }")
        C.ok(multi['number'] in dr and 'Create RFQ' in dr, f'the line drill-down shows its open RFQs and Create RFQ ({dr[:120]})')
        # the two line-first RFQs stand aside; the walk continues on the plans draft
        await pg.evaluate("ids => { DB.rfqs.forEach(r => ids.includes(r.id) && (r.status = 'closed')); save(); }", [one['id'], multi['id']])

        # ---- the plans draft, routed to the foreman
        rid = await pg.evaluate("() => { rfqDemoReady(); const r = rfqDraftFromPlans('p121'); render(); return r.id; }")
        R0 = await pg.evaluate(RFQ, rid)
        C.ok(R0['status'] == 'foreman-review' and R0['needBy'] == '2026-09-08' and 'cannot be read in the demo' in R0['drawingsNote'], f'from plans: foreman review, need-by the framing task start, the drawings note ({R0["status"]}, {R0["needBy"]})')
        C.ok(all(l['line'] == 'estimate:es1:l2' and l['estimateLineId'] == 'l2' for l in R0['lines']), 'every plans line carries its estimate line link')
        q = {l['key']: l['qty'] for l in R0['lines']}
        rooms = await pg.evaluate("() => DB.projects.find(p => p.id === 'p121').takeoff.rooms.filter(r => r.floor === 'Garden')")
        C.ok(q == takeoff_py(rooms), f'the draft equals the takeoff of the Garden floor rooms ({q})')
        pe = await pg.evaluate(PRED_EQ)
        C.ok(all(c == n for _, c, n, _ in pe) and dict((k, c) for k, c, _, _ in pe)['rfqForeman'] == 1, f'counts equal rows; one waiting on the foreman ({pe})')
        chen_q = await pg.evaluate("() => mApprovals().filter(i => i.kind === 'rfq').length")
        C.ok(chen_q == 0, 'nothing waits on the coordinator while the foreman checks')

        # ---- the foreman, on the phone
        await sign_in(pg, 'u_angel')
        await go(pg, 'ftoday')
        card = await pg.evaluate("() => (document.querySelector('.rfq-fm') || {}).innerText || ''")
        C.ok(R0['number'] in card and 'Materials to Check' in card, f'the foreman\'s For You card lists the draft ({card[:80]})')
        await pg.locator(f'[data-rfqrev="{rid}"]').click(); await pg.wait_for_timeout(400)
        small = await pg.evaluate(SMALL_TAPS, '#mbm [data-rfqdn], #mbm [data-rfqup], #mbm [data-rfqrm], #mbm #rfq-add-go, #mbm #mbm-ok, #mbm #mbm-alt, #mbm .rfq-qty')
        C.ok(not small, f'every tap target in the sheet is at least 44px ({small[:4]})')
        prim = await pg.evaluate("() => [...document.querySelectorAll('#mbm .btn.primary')].filter(b => b.getClientRects().length).map(b => b.innerText.trim())")
        C.ok(prim == ['Approve'], f'one blue primary, Approve ({prim})')
        C.ok(await pg.evaluate(NOSIDE), 'phone: the foreman sheet does not scroll sideways')
        # send back with a note: the assistant redrafts at 15% waste
        await pg.locator('#rfq-fm-note').fill('use waste 15% on everything')
        await pg.locator('#mbm #mbm-alt').click(); await pg.wait_for_timeout(500)
        R1 = await pg.evaluate(RFQ, rid)
        C.ok(R1['status'] == 'foreman-review' and R1['takeoff']['assumptions']['waste'] == 15 and {l['key']: l['qty'] for l in R1['lines']} == takeoff_py(rooms, {'waste': 15}), f'Send Back with a note: the assistant redrafted at 15% waste ({R1.get("note")})')
        await pg.locator(f'[data-rfqrev="{rid}"]').click(); await pg.wait_for_timeout(400)
        await pg.locator('#mbm [data-rfqup="L1"]').click(); await pg.locator('#mbm [data-rfqup="L1"]').click()
        await pg.locator('#mbm [data-rfqrm="L11"]').click()
        await pg.locator('#rfq-add-item').fill("2x6 x 10' stud"); await pg.locator('#rfq-add-qty').fill('12'); await pg.locator('#rfq-add-go').click()
        await ok_modal(pg, 600)
        R2 = await pg.evaluate(RFQ, rid)
        st = next(l for l in R2['lines'] if l['id'] == 'L1')
        C.ok(R2['status'] == 'purchasing' and st['qty'] == R1['lines'][0]['qty'] + 2 and not any(l['id'] == 'L11' for l in R2['lines']) and any(l['item'].startswith('2x6') and l['line'] == 'estimate:es1:l2' for l in R2['lines']), 'Approve: +2 studs, adhesive removed, a 2x6 line added with the line link; it goes to purchasing')
        C.ok('approved by the foreman' in json.dumps(R2['history']) and R2['history'][-1]['what'] == 'sent to purchasing', 'the history says who approved and where it went')
        # put the adhesive back for the comparisons below (it was a line the foreman removed; the coordinator keeps his list)
        pe = await pg.evaluate(PRED_EQ)
        d = {k: c for k, c, _, _ in pe}
        C.ok(d['rfqForeman'] == 0 and d['rfqPurchasing'] == 1 and all(c == n for _, c, n, _ in pe), f'counts move: purchasing 1 ({pe})')

        # ---- the coordinator picks vendors and sends (desktop width)
        await pg.set_viewport_size({'width': 1440, 'height': 900})
        await sign_in(pg, 'u_chen')
        qi = await pg.evaluate("() => mApprovals().filter(i => i.kind === 'rfq').map(i => [i.title, i.who])")
        C.ok(len(qi) == 1 and qi[0][1] == 'coord' and 'Pick vendors' in qi[0][0], f'the coordinator\'s Approvals holds Pick Vendors ({qi})')
        await pg.evaluate("id => { rfqOpen = id; view = 'rfq'; render(); }", rid); await pg.wait_for_timeout(300)
        vp = await pg.evaluate("() => [...document.querySelectorAll('[data-rfqv]')].map(i => [i.dataset.rfqv, i.checked, i.closest('label').innerText])")
        C.ok(len(vp) >= 5 and all('because' in t for _, _, t in vp), f'every proposed vendor has a because ({len(vp)})')
        C.ok(any(c and 'outside NYC' in t for _, c, t in vp), 'at least one vendor outside NYC is ticked')
        C.ok(any('(Procurement playbook)' in t for _, _, t in vp), 'the because names the line of the Standard and where it is (standardWhy)')
        prim = await pg.evaluate("() => [...document.querySelectorAll('#v-rfq .btn.primary')].filter(b => b.getClientRects().length).map(b => b.innerText.trim())")
        C.ok(prim == ['Send RFQ'], f'one blue primary on the pick: Send RFQ ({prim})')
        await pg.locator('#rfq-due').fill('2026-09-04')
        await pg.locator('#rfq-send').click(); await pg.wait_for_timeout(600)
        R3 = await pg.evaluate(RFQ, rid)
        ob = await pg.evaluate("() => DB.outbox.filter(o => o.kind === 'rfq').map(o => ({ s: o.subject, st: o.status, att: (o.attachments || []).map(a => a.filename), body: o.body }))")
        C.ok(R3['status'] == 'sent' and len(R3['sent']) == len(R3['vendors']) == 5 and len(ob) == 5, f'one email per vendor ({len(ob)}), sent from the outbox')
        C.ok(all(R3['number'] in o['s'] and o['att'] == [R3['number'] + '.csv'] and 'Line | Item' in o['body'] and '!' not in o['body'] for o in ob), 'the RFQ number in the subject, a line table and a CSV, no exclamation marks')
        pe = await pg.evaluate(PRED_EQ)
        C.ok(all(c == n for _, c, n, _ in pe) and dict((k, c) for k, c, _, _ in pe)['rfqNoOutNyc'] == 0, f'counts equal rows after send ({pe})')

        # ---- quotes back: the app day turns
        day = await pg.evaluate("() => appSetDay('2026-09-04')")
        C.ok('rfqDayTick' in day['ran'] and not day['errors'], f'the RFQ hook runs with the day ({day})')
        R4 = await pg.evaluate(RFQ, rid)
        Q = {q['vendor']: q for q in R4['quotes']}
        C.ok(set(Q) == {'Kent Avenue Lumber', 'Queens Builders Supply', 'Garden State Lumber', 'Lancaster Timber Direct'}, f'four replies read; Harlem River never answered ({sorted(Q)})')
        C.ok(Q['Lancaster Timber Direct']['unreadable'] and 'could not read' in Q['Lancaster Timber Direct']['flags'][0], 'a scan nobody can read says so and asks a person')
        C.ok(Q['Queens Builders Supply']['file'].endswith('.pdf') and all(not x['missing'] for x in Q['Queens Builders Supply']['lines'] if x['lineId'] != 'L12'), 'the PDF reply is read from its text')
        gs = Q['Garden State Lumber']
        C.ok(any('alternate' in f for f in gs['flags']) and any(f.startswith('missing') for f in gs['flags']), f'the partial reply flags missing items and the substitution ({gs["flags"]})')
        C.ok(all(Q[v]['freight'] is not None and Q[v]['lead'] is not None for v in ('Kent Avenue Lumber', 'Queens Builders Supply', 'Garden State Lumber')), 'freight and lead times read')
        chase = await pg.evaluate("() => DB.outbox.filter(o => o.kind === 'rfq-chase').map(o => [o.to.name, o.status, o.forName])")
        C.ok(chase == [['Lou Grant', 'draft', 'Chen Biron']], f'the non-responder gets a chase draft the coordinator approves ({chase})')
        C.ok(await pg.evaluate("() => mApprovals().some(i => i.kind === 'draft' && /Reminder — RFQ/.test(i.title))"), 'the chase draft waits in Chen\'s Approvals')
        pe = await pg.evaluate(PRED_EQ)
        d = {k: c for k, c, _, _ in pe}
        C.ok(all(c == n for _, c, n, _ in pe) and d['rfqNoReply'] == 1, f'quotes due today with no reply: 1 (Harlem River) ({pe})')
        catch = await pg.evaluate("() => CATCH.filter(c => /^rfq/.test(c.name)).map(c => [c.name, c.rows().length])")
        C.ok(dict(catch).get('rfqNoReply') == 1, f'CATCH carries the same row ({catch})')
        pr = await pg.evaluate("() => DB.rfqProspects.map(x => [x.name, x.source, x.status])")
        C.ok(['Tri-State Connector Supply', 'mail', 'proposed'] in pr, f'the supplier named in a reply is a prospect ({pr})')

        # ---- leveling
        await pg.evaluate("id => { rfqOpen = id; view = 'rfq'; render(); }", rid); await pg.wait_for_timeout(300)
        await pg.locator('#rfq-level').click(); await pg.wait_for_timeout(400)
        R5 = await pg.evaluate(RFQ, rid)
        L = await pg.evaluate("id => { const L = rfqLevel(DB.rfqs.find(r => r.id === id)); return { b: L.baskets.map(x => [x.vendor, x.landed]), split: L.split && L.split.total, assign: L.split && L.split.assign, per: Object.fromEntries(L.perLine.map(x => [x.lineId, x.best ? [x.best.unit, x.best.vendor] : null])), budget: L.budgetTotal }; }", rid)
        VV = await pg.evaluate("() => Object.fromEntries(DB.vendors.map(v => [v.id, { delivery: v.delivery || null, chargesTax: v.chargesTax }]))")
        RATE = await pg.evaluate("() => rfqTaxRate()")
        P = level_py(R5, VV, RATE)
        C.ok(R5['status'] == 'leveled', 'Level Now: leveled')
        C.ok([list(x) for x in P['baskets']] == L['b'], f'whole baskets match Python ({L["b"]} vs {P["baskets"]})')
        C.ok(P['split'] == L['split'] and P['assign'] == L['assign'], f'best split after freight and minimums matches Python ({L["split"]} vs {P["split"]})')
        C.ok({k: (list(v) if v else None) for k, v in P['perline'].items()} == L['per'], 'cheapest per line matches Python')
        C.ok(L['budget'] == 0, f'from plans: the $32,000 framing line is labour and material with no split, so no budget figure ({L["budget"]})')
        lt = await pg.evaluate("() => document.querySelector('#v-rfq').innerText")
        C.ok('No material budget on this line' in lt and 'under the material budget' not in lt, 'leveling says "No material budget on this line" and shows no saving against budget')
        C.ok(RATE == 8.875 and 'use tax' in (await pg.evaluate("() => document.querySelector('#v-rfq').innerText")) and 'confirm with the accountant' in (await pg.evaluate("() => document.querySelector('#v-rfq').innerText")), 'landed cost counts NY sales or use tax, labelled confirm with the accountant')
        C.ok('Relationship:' in (await pg.evaluate("() => document.querySelector('#v-rfq').innerText")) and 'Delivery:' in (await pg.evaluate("() => document.querySelector('#v-rfq').innerText")), 'leveling shows relationship and delivery facts next to price')
        page = await pg.evaluate("() => document.querySelector('#v-rfq').innerText")
        C.ok(all(w in page for w in ('What Happened', 'Impact on Cost, Schedule and Quality', 'Options', 'Recommendation', 'Decide By')), 'the recommendation is in the Standard\'s format')
        C.ok(await pg.evaluate("() => !!document.querySelector('#v-rfq table.rfq-grid')"), 'desktop: the per-line grid')
        await pg.set_viewport_size({'width': 390, 'height': 844}); await pg.evaluate("() => render()"); await pg.wait_for_timeout(300)
        C.ok(await pg.evaluate("() => !document.querySelector('#v-rfq table.rfq-grid') && document.querySelectorAll('#v-rfq .rfq-card').length > 5"), 'phone: stacked cards, no grid')
        C.ok(await pg.evaluate(NOSIDE), 'phone: leveling does not scroll sideways')
        await pg.set_viewport_size({'width': 1440, 'height': 900}); await pg.evaluate("() => render()")
        pe = await pg.evaluate(PRED_EQ)
        C.ok(all(c == n for _, c, n, _ in pe) and dict((k, c) for k, c, _, _ in pe)['rfqLeveledNoNeg'] == 1, f'leveled, no negotiation: 1 ({pe})')

        # ---- negotiation
        await pg.locator('#rfq-negdraft').click(); await pg.wait_for_timeout(400)
        R6 = await pg.evaluate(RFQ, rid)
        names = [v['name'] for v in R6['vendors']]
        held = set()
        for qq in R6['quotes']:
            if qq.get('freight') is not None: held.add('%.2f' % qq['freight'])
            for x in qq['lines']:
                if x.get('unit') is not None: held.add('%.2f' % x['unit'])
        for n in [n for n in R6['neg'] if n['status'] == 'draft']:
            other = [nm for nm in names if nm != n['vendor']]
            C.ok(not any(nm.lower() in n['body'].lower() for nm in other), f'{n["vendor"]}: no competitor named')
            figs = [f.replace(',', '') for f in re.findall(r'\$(\d[\d,]*\.\d{2})', n['body'])]
            C.ok(all(f in held for f in figs), f'{n["vendor"]}: every figure is from a received quote ({figs})')
        kent = next(n for n in R6['neg'] if n['vendor'] == 'Kent Avenue Lumber')
        C.ok(len(kent['lines']) >= 3 and '$' in kent['body'], 'Kent is asked on the lines where it is not best, with the figure we hold')
        prim = await pg.evaluate("() => [...document.querySelectorAll('#v-rfq .btn.primary')].filter(b => b.getClientRects().length).map(b => b.innerText.trim())")
        C.ok(prim == ['Approve and Send'], f'one blue primary: Approve and Send ({prim})')
        # an edit that names a competitor is refused (integrity)
        await pg.locator(f'[data-rfqnb="{kent["id"]}"]').fill(kent['body'] + '\nQueens Builders Supply beat you.')
        await pg.locator('#rfq-negsend').click(); await pg.wait_for_timeout(400)
        C.ok((await pg.evaluate(RFQ, rid))['status'] == 'leveled', 'an email naming a competitor is refused')
        await pg.locator(f'[data-rfqnb="{kent["id"]}"]').fill(kent['body'])
        await pg.locator('#rfq-negsend').click(); await pg.wait_for_timeout(400)
        C.ok((await pg.evaluate(RFQ, rid))['status'] == 'leveled', 'figures read by AI and not confirmed are refused for negotiation')
        nconf = 0
        while await pg.locator('[data-rfqconf]').count():
            await pg.locator('[data-rfqconf]').first.click(); await pg.wait_for_timeout(250)
            C.ok('Confirm the Prices' in (await pg.evaluate("() => (document.querySelector('#mbm h3') || {}).innerText || ''")), 'Confirm shows each line\'s arithmetic against the reply')
            await ok_modal(pg, 300); nconf += 1
            if nconf > 6: break
        C.ok(nconf == 3, f'one tap per readable quote ({nconf})')
        await pg.locator(f'[data-rfqnb="{kent["id"]}"]').fill(kent['body'])
        await pg.locator('#rfq-negsend').click(); await pg.wait_for_timeout(500)
        R7 = await pg.evaluate(RFQ, rid)
        C.ok(R7['status'] == 'negotiating' and all(n['status'] == 'sent' and n['approvedBy'] == 'Chen Biron' for n in R7['neg']), 'approved and sent by Chen')

        # ---- round two, then award
        await pg.evaluate("() => appSetDay('2026-09-05')")
        R8 = await pg.evaluate(RFQ, rid)
        r2q = [q for q in R8['quotes'] if q['round'] == 2]
        C.ok(len(r2q) == 3 and R8.get('round2In'), f'round two read as round 2 ({len(r2q)})')
        await pg.evaluate("id => { rfqOpen = id; view = 'rfq'; render(); }", rid); await pg.wait_for_timeout(300)
        P2 = level_py(R8, VV, RATE)
        await pg.locator('#rfq-award').click(); await pg.wait_for_timeout(500)
        C.ok((await pg.evaluate(RFQ, rid))['status'] == 'negotiating', 'the award waits until round-two figures are confirmed')
        while await pg.locator('[data-rfqconf]').count():
            await pg.locator('[data-rfqconf]').first.click(); await pg.wait_for_timeout(250); await ok_modal(pg, 300)
        await pg.locator('#rfq-award').click(); await pg.wait_for_timeout(800)
        R9 = await pg.evaluate(RFQ, rid)
        A = R9.get('award') or {}
        pos = await pg.evaluate("ids => DB.pos.filter(p => ids.includes(p.id)).map(p => ({ n: p.number, v: p.vendor, st: p.status, o: p.origin, rfq: p.rfqId, src: p.sourcing, tot: poTotal(p).total, landed: p.landed, tax: p.tax, use: p.useTax, notes: p.notes, ln: p.lines.map(l => [l.line, l.estimateLineId, l.rfqId, l.rfqLineId]) }))", A.get('pos', []))
        C.ok(R9['status'] == 'awarded' and pos and all(p['o'] == 'rfq' and p['rfq'] == rid and p['src']['rfqNumber'] == R9['number'] and p['src']['choice'] in ('direct', 'middleman') for p in pos), f'POs from the award carry the RFQ and the sourcing choice ({[(p["n"], p["st"]) for p in pos]})')
        C.ok(all(all(l[0] == 'estimate:es1:l2' and l[1] == 'l2' and l[2] == rid and l[3] for l in p['ln']) for p in pos), 'every PO line keeps the estimate line link and its RFQ line')
        C.ok(all(p['st'] in ('issued', 'pending') for p in pos), 'the POs went through poAction (issued, or pending the owner over the threshold)')
        final = r2(sum(p['landed'] for p in pos))
        C.ok(all((p['use'] is None and p['tax'] == RATE) or (p['use'] and p['tax'] == 0 and 'confirm with the accountant' in p['use']['note']) for p in pos), f'a vendor that charges no NY tax gets use tax to accrue on the PO ({[(p["v"], p["tax"], p["use"]) for p in pos]})')
        C.ok(all('never by prepaid wire' in p['notes'] for p in pos), 'a first order says card or terms, never a prepaid wire')
        P1 = level_py(dict(R8, quotes=[q for q in R8['quotes'] if q['round'] == 1]), VV, RATE)
        C.ok(abs(A['final'] - final) < 0.005 and abs(A['final'] - P2['split']) < 0.005, f'final equals the POs and the recommended split ({A["final"]}, {final}, {P2["split"]})')
        C.ok(abs(A['firstQuote'] - P1['baskets'][0][1]) < 0.005 and abs(A['savingsVsFirst'] - r2(P1['baskets'][0][1] - final)) < 0.005 and A['savingsVsFirst'] > 0, f'savings against the first quote ({A["savingsVsFirst"]})')
        C.ok(A['savingsVsBudget'] is None and A['budget'] is None and 'No material budget' in A.get('budgetNote', ''), f'no saving against budget is claimed on a line with no material budget (it was 32,000 minus the award) ({A.get("savingsVsBudget")}, {A.get("budgetNote")})')
        aw = await pg.evaluate("() => document.querySelector('#v-rfq').innerText")
        C.ok('No material budget on this line' in aw and 'under the material budget' not in aw, 'the award says so and shows no budget figure')
        old = await pg.evaluate(OLD_AWARD, rid)
        C.ok(old['vs'] is None and old['sb'] == 0 and old['nb'] >= 1 and old['basis'] == 'material' and old['was'] == 32000, f'an award stamped before the rule is re-read: the whole-line figure is dropped ({old})')
        C.ok(abs(A['poTotal'] - r2(sum(p['tot'] for p in pos))) < 0.005, 'the award records the PO totals beside the landed figure')
        sv = await pg.evaluate("() => ({ s: rfqSavings('2026-09').vsFirst, q: erpQuery ? (EQ_TABLES.rfqs().filter(r => r.awardedOn.startsWith('2026-09')).reduce((a, r) => a + r.savings, 0)) : null })")
        C.ok(abs(sv['s'] - A['savingsVsFirst']) < 0.005 and abs(sv['q'] - A['savingsVsFirst']) < 0.005, f'the month\'s savings are queryable ({sv})')
        t = await pg.evaluate("() => ({ text: (document.getElementById('toast') || {}).innerText || '', open: (document.getElementById('toast') || document.body).querySelectorAll('.toast-open').length })")
        C.ok('awarded' in t['text'] and t['open'] >= 1, f'the award toasts with Open ({t})')

        # ---- prospects: add the referral; the next RFQ suggests it
        await pg.evaluate("() => { rfqOpen = ''; rfqTab = 'prospects'; view = 'rfq'; render(); }"); await pg.wait_for_timeout(300)
        pid = await pg.evaluate("() => (DB.rfqProspects.find(x => x.name === 'Tri-State Connector Supply') || {}).id")
        await pg.locator(f'[data-rfqpadd="{pid}"]').click(); await pg.wait_for_timeout(400)
        v = await pg.evaluate("() => DB.vendors.find(v => v.name === 'Tri-State Connector Supply')")
        C.ok(v and v.get('rfqSuggest'), f'Add puts the prospect on file ({v and v.get("rfqSuggest")})')
        sug = await pg.evaluate("() => { const r = rfqCreate({ projectId: 'p121', title: 'hangers', category: 'Lumber', lines: [{ item: 'joist hanger', qty: 10, unit: 'ea' }] }); r.status = 'purchasing'; const V = rfqProposeVendors(r); const x = V.list.find(y => y.v.name === 'Tri-State Connector Supply'); r.status = 'closed'; save(); return x ? x.because.map(b => b.t) : null; }")
        C.ok(sug and any('added from' in s for s in sug), f'the next RFQ suggests the added prospect ({sug})')
        vv = await pg.evaluate("() => { const po = { number: 'PO-TEST', vendor: 'Tri-State Connector Supply', lines: [{ item: 'hanger', qty: 10, price: 2 }], needBy: '2026-09-10' }; return poValid(po); }")
        C.ok(any('not yet vetted' in x for x in vv), f'a new vendor gets no PO until it is vetted ({vv})')
        await pg.evaluate("() => { rfqOpen = ''; rfqTab = 'prospects'; view = 'rfq'; render(); }"); await pg.wait_for_timeout(300)
        await pg.locator('[data-rfqvet]').first.click(); await pg.wait_for_timeout(300)
        for k in ('w9', 'coi', 'registration', 'address', 'reviews'):
            await pg.locator(f'#mbm [data-f="{k}"]').check()
        await ok_modal(pg, 400)
        vv = await pg.evaluate("() => ({ r: poValid({ number: 'PO-TEST', vendor: 'Tri-State Connector Supply', lines: [{ item: 'hanger', qty: 10, price: 2 }], needBy: '2026-09-10' }), by: DB.vendors.find(v => v.name === 'Tri-State Connector Supply').vetting.w9.by })")
        # since the chain lane, poValid also refuses a line with no estimate, change-order or overhead link; this
        # synthetic PO has none, so only that reason may remain: vetting no longer stops it
        C.ok(not [x for x in vv['r'] if 'not linked' not in x] and vv['by'] == 'Chen Biron', f'vetted, with who and when recorded; vetting no longer stops the PO ({vv})')

        # ---- sourcing research
        R = await pg.evaluate("() => JSON.parse(JSON.stringify(sourcingResearch('Lumber')))")
        C.ok(R['demo'] and 'Demo data' in R['provider'], 'the demo provider labels its output demo data')
        C.ok(all(h['label'].startswith('hypothesis') for h in R['hypotheses']), 'reasons are labelled hypotheses until quotes back them')
        C.ok(all(f['source']['url'].startswith('https://') and '.example.com' in f['source']['url'] for x in R['prospects'] for f in x['facts']), 'every fact has a source (example.com, demo)')
        fr_t = await pg.evaluate("() => rfqFreightTable()")
        okland = True
        for x in R['prospects']:
            qn = R['qty']; mode = 'truckload' if qn >= fr_t['truckloadPieces'] else 'ltl'
            fr_c = r2(max(fr_t[mode]['min'], x['miles'] * fr_t[mode]['perMile']))
            goods = r2(x['price'] * qn); sf = r2(max(0, x['minimum'] - goods)); tx = r2(goods * RATE / 100); hd = 0 if x['liftGate'] else 120
            tot = r2(goods + fr_c + sf + tx + hd)
            okland &= abs(x['landed']['total'] - tot) < 0.005 and abs(x['landed']['perUnit'] - r2(tot / qn)) < 0.005
            if R['now']: okland &= abs(x['saving'] - r2((R['now']['unit'] - r2(tot / qn)) * qn)) < 0.005
        C.ok(okland, 'landed cost arithmetic matches Python')
        subs = {x['name']: x['quality']['substitution'] for x in R['prospects']}
        C.ok(subs['Susquehanna Valley Sawmill'] and subs['Catskill Family Mill'] and not subs['Tri-County Lumber Wholesale'], f'a species or grade change is a substitution needing approval ({subs})')
        C.ok(all('PM' in x['quality']['substitutionWhy'] for x in R['prospects'] if x['quality']['substitution']), 'the substitution names the PM and designer approval')
        await pg.evaluate("() => { rfqTab = 'research'; rfqResCat = 'Lumber'; view = 'rfq'; render(); }"); await pg.wait_for_timeout(300)
        prim = await pg.evaluate("() => [...document.querySelectorAll('#v-rfq .btn.primary')].filter(b => b.getClientRects().length).map(b => b.innerText.trim())")
        C.ok(prim == ['Add to Next RFQ'], f'research: one blue primary, Add to Next RFQ ({prim})')
        first = await pg.evaluate("() => document.querySelector('[data-srcadd].primary').dataset.srcadd")
        await pg.locator(f'[data-srcadd="{first}"]').click(); await pg.wait_for_timeout(400)
        added = await pg.evaluate("id => { const x = DB.sourcing.research.Lumber.prospects.find(y => y.id === id); const v = DB.vendors.find(v => v.name === x.name); return { st: x.status, v: !!v, sug: v && v.rfqSuggest, res: v && v.researchId }; }", first)
        C.ok(added['st'] == 'added' and added['v'] and 'sourcing research' in (added['sug'] or ''), f'Add to Next RFQ puts it on file, suggested next time ({added})')
        await pg.locator('[data-srcpl]').first.click(); await pg.wait_for_timeout(300)
        C.ok(await pg.evaluate("() => DB.outbox.some(o => o.kind === 'pricelist' && o.status === 'draft')"), 'Ask for Price List drafts an email the coordinator approves')
        await pg.set_viewport_size({'width': 390, 'height': 844}); await pg.evaluate("() => render()"); await pg.wait_for_timeout(300)
        C.ok(await pg.evaluate(NOSIDE), 'phone: research does not scroll sideways')
        await pg.set_viewport_size({'width': 1440, 'height': 900})

        # ---- Ask
        asks = {
            f'status of {R9["number"]}': 'Awarded',
            'who\'s cheapest on the framing RFQ': 'cheapest',
            'what did we save on RFQs this month': 'no material budget',
            'who sells lumber outside NYC': 'outside NYC',
            'where is lumber cheapest': 'Demo data',
            'why is Tri-County cheaper': 'Hypothesis',
        }
        for qtxt, want in asks.items():
            a = await pg.evaluate("async q => { const r = await paAsk(q); const o = typeof r === 'string' ? { headline: r } : (r || {}); return [o.headline || o.text || '', (o.work || []).join(' | ')].join(' || '); }", qtxt)
            C.ok(want in a, f'Ask "{qtxt}" -> {a[:160]}')

        # ---- watch: counts equal rows; erpQuery; reload
        pe = await pg.evaluate(PRED_EQ)
        C.ok(all(c == n for _, c, n, _ in pe) and len({l for *_, l in pe}) == 6, f'every RFQ predicate: count equals rows, one label each ({pe})')
        eq = await pg.evaluate("() => ({ r: EQ_TABLES.rfqs().length, q: EQ_TABLES.rfqquotes().length, p: EQ_TABLES.rfqprospects().length })")
        C.ok(eq['r'] >= 4 and eq['q'] >= 7 and eq['p'] >= 1, f'erpQuery tables rfqs, rfqquotes, rfqprospects ({eq})')
        pal = await pg.evaluate("() => palIndex().filter(i => i.k === 'RFQ').length")
        C.ok(pal >= 4, f'the RFQs are in ⌘K ({pal})')
        before = await pg.evaluate("() => JSON.stringify({ r: DB.rfqs.map(r => [r.number, r.status, r.quotes.length, r.award && r.award.final]), p: DB.rfqProspects.map(x => x.status), s: Object.keys(DB.sourcing.research), o: DB.sourcing.research.Lumber.prospects.map(x => x.status) })")
        await pg.wait_for_timeout(1200)
        await pg.evaluate("() => (typeof trFlush === 'function' ? trFlush() : saveNow())")
        await pg.wait_for_timeout(600)
        await pg.reload(); await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
        after = await pg.evaluate("() => JSON.stringify({ r: DB.rfqs.map(r => [r.number, r.status, r.quotes.length, r.award && r.award.final]), p: DB.rfqProspects.map(x => x.status), s: Object.keys(DB.sourcing.research), o: DB.sourcing.research.Lumber.prospects.map(x => x.status) })")
        C.ok(before == after, f'RFQs, quotes, prospects and research survive a reload')
        C.ok(not errs, f'no page errors ({errs[:3]})')
        await b.close()
    return C.done()

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
