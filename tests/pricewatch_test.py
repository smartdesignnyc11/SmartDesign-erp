"""Price watch: paid more than before, or something looks off (BACKLOG §1.8 item 11; Alan, 2026-10-11).
Walks the module on the seeded demo (app day 2026-09-03, 121 State) with an INVENTED purchase history injected
on top: known overpays and anomalies, and normal noise around them (prices within a few percent, a same-vendor
re-buy, a will-call order, an out-of-state bill that did carry tax). Every name, price and line is invented.

  history   one itemPriceHistory: PO lines, bill lines, confirmed quotes and a matched card line; a box of 50 is
            50 each; a near match ("2x4 10' KD stud") is a proposal the coordinator confirms, never assumed
  detect    each detector fires on its case and not on the noise; a bill over its PO stays on Billed Over the PO
  minhist   two earlier buys: no flag, and the PO draft says "not enough history"
  podraft   the PO draft carries a Price Check with the history before it is issued
  match     a card line matched to a flagged order says so at once
  ask       where did we pay more than usual this month / price history for 2x4 studs / why is this flagged
  explain   the coordinator's explanation leaves the flag open and the baseline where it was; the owner's decline
            needs a reason, keeps the flag open and records the reason; the owner's approval of a baseline change
            moves it and closes the flag; a purchase explanation closes its flag; the brain records the lesson
  precision under 50% confirmed over 30 days, the owner is asked to tune the threshold
  usetax    an out-of-state vendor's bill with no NY tax: use tax to accrue, recorded by the controller
  counts    every detector's count equals its rows (PRED, CATCH, the Price Watch page)
  figure    paid above the best recent price, in dollars, queryable
  phone     390px: the page, a case and the explanation sheet do not scroll sideways; one blue primary
  reload    everything survives a reload

    python3 pricewatch_test.py
"""
import asyncio, math, sys, json
from harness import *

def r2(x):
    return math.floor(100 * x + 0.5) / 100

NOSIDE = "() => document.documentElement.scrollWidth <= innerWidth + 1"
PRIMARY = "sel => [...document.querySelectorAll(sel + ' .btn.primary')].filter(b => b.getClientRects().length).map(b => b.innerText.trim())"
DETS = ['pwPaidMore', 'pwQtyOver', 'pwDupCharge', 'pwSplit', 'pwFeeSpike', 'pwRareVendor', 'pwNotDelivered', 'pwCardNoJob', 'pwUseTax']
COUNTS = """dets => dets.map(d => [d, PRED[d].count(), PRED[d].rows().length, (CATCH.find(c => c.name === d) || { rows: () => [] }).rows().length, PRED[d].label])"""
KEYS = "d => PRED[d].rows().map(c => c.key)"

# ---- the invented history (2026). Item, qty, unit, price per unit; dates spaced so only the planted cases fire.
SEED = r"""() => {
  const V = (id, name, x) => { if (!DB.vendors.some(v => v.name === name)) DB.vendors.push(Object.assign({ id, name, trade: 'Lumber', email: id + '@example.com', contact: 'Sam Ortiz', insuranceExp: '2027-06-30', w9: true, cats: ['Lumber'] }, x || {})); };
  V('vbl', 'Brooklyn Lumber Co', { city: 'Brooklyn, NY', region: 'NYC Manhattan/Brooklyn', chargesTax: true });
  V('vay', 'Atlantic Yard Supply', { city: 'Brooklyn, NY', region: 'NYC Manhattan/Brooklyn', chargesTax: true, cats: ['Lumber', 'Drywall'] });
  V('vrf', 'Ridge Fasteners', { city: 'Queens, NY', trade: 'Hardware', cats: ['Fasteners'] });
  V('vvl', 'Valley Lumber Outlet', { city: 'Bronx, NY' });
  V('vkm', 'Keystone Mill Direct', { city: 'York, PA', region: 'Out of state', chargesTax: false });
  V('vqh', 'Quality Hardware', { city: 'Brooklyn, NY', trade: 'Hardware' });
  let n = 900;
  const PO = (id, vendor, date, lines, o) => { DB.pos.push(Object.assign({ id, number: 'PO-2026-' + (++n), projectId: 'p121', vendor, date, status: 'received', type: 'materials', shipTo: 'site', tax: 0, shipping: 0,
      lines: lines.map((l, i) => Object.assign({ id: id + 'l' + i, item: l[0], desc: '', qty: l[1], unit: l[2], price: l[3], code: '03', line: '', received: l[1] }, l[4] || {})), receipts: [], matchedTxns: [], srcDocs: [], createdBy: 'Chen Biron', __v2: 1 }, o || {})); return id; };
  const BILL = (id, number, vendor, date, lines, o) => { DB.bills.push(Object.assign({ id, number, vendor, date, due: date, status: 'submitted', projectId: 'p121', cat: 'materials', code: '03', lines: lines.map((l, i) => Object.assign({ id: id + 'l' + i }, l)), approvals: [], createdBy: 'Chen Biron', payMethod: 'ACH', notes: '' }, o || {})); return id; };
  const TX = (id, date, desc, amt, o) => { DB.txns.push(Object.assign({ id, date, desc, amt, acct: 'ac2', vendor: '', cat: 'office', status: 'categorized', projectId: '', memo: '', receipt: '' }, o || {})); return id; };
  const S = "2x4 x 10' stud", P = '1/2in CDX plywood 4x8', D = '1/2in drywall 4x12 sheet';
  // studs: five buys before July (noise within 3%), a same-vendor re-buy in July (+4%, noise), the overpay in August
  PO('pwt_s1', 'Brooklyn Lumber Co', '2026-03-10', [[S, 120, 'ea', 6.30]], { shipping: 75 });
  PO('pwt_s2', 'Atlantic Yard Supply', '2026-04-10', [[S, 120, 'ea', 6.40]]);
  PO('pwt_s3', 'Brooklyn Lumber Co', '2026-05-08', [[S, 120, 'ea', 6.20]], { shipping: 80 });
  PO('pwt_s4', 'Atlantic Yard Supply', '2026-06-05', [[S, 120, 'ea', 6.35]]);
  PO('pwt_s5', 'Brooklyn Lumber Co', '2026-06-20', [[S, 120, 'ea', 6.25]], { shipping: 70 });
  PO('pwt_kd', 'Atlantic Yard Supply', '2026-06-12', [["2x4 10' KD stud", 100, 'ea', 6.38]]);
  PO('pwt_s6', 'Brooklyn Lumber Co', '2026-07-15', [[S, 120, 'ea', 6.55]], { shipping: 75 });
  PO('pwt_s7', 'Brooklyn Lumber Co', '2026-08-28', [[S, 120, 'ea', 7.40]], { shipping: 195, status: 'issued' });
  // plywood: three earlier buys, then a bill at $40.00 against the PO's $38.50 (36 of 40 sheets, under the PO total)
  PO('pwt_p1', 'Brooklyn Lumber Co', '2026-05-20', [[P, 40, 'sheet', 38.00]], { shipping: 75 });
  PO('pwt_p2', 'Brooklyn Lumber Co', '2026-06-25', [[P, 40, 'sheet', 38.40]], { shipping: 80 });
  PO('pwt_p3', 'Brooklyn Lumber Co', '2026-07-25', [[P, 40, 'sheet', 37.80]], { shipping: 75 });
  PO('pwt_p4', 'Brooklyn Lumber Co', '2026-08-22', [[P, 40, 'sheet', 38.50, { received: 36 }]], { shipping: 85, status: 'partial' });
  BILL('pwt_bp4', 'BL-7781', 'Brooklyn Lumber Co', '2026-08-26', [{ desc: P, qty: 36, unit: 'sheet', amount: 1440, poLineId: 'pwt_p4l0' }], { poId: 'pwt_p4' });
  // drywall: three buys near $13, then $14.90 in September; the August one was a will-call pickup (noise)
  PO('pwt_d1', 'Atlantic Yard Supply', '2026-06-10', [[D, 60, 'sheet', 13.00]]);
  PO('pwt_d2', 'Atlantic Yard Supply', '2026-07-10', [[D, 60, 'sheet', 13.20]]);
  PO('pwt_d3', 'Atlantic Yard Supply', '2026-08-10', [[D, 60, 'sheet', 12.90]], { shipTo: 'willcall' });
  PO('pwt_d4', 'Atlantic Yard Supply', '2026-09-02', [[D, 60, 'sheet', 14.90]], { status: 'issued' });
  // hangers: a box of 50 and loose ones at the same price each, then +45% with only two earlier buys (min history)
  PO('pwt_h1', 'Ridge Fasteners', '2026-06-01', [['Joist hanger LUS26 (box of 50)', 2, 'box', 55.00]]);
  PO('pwt_h2', 'Ridge Fasteners', '2026-07-01', [['Joist hanger LUS26', 100, 'ea', 1.12]]);
  PO('pwt_h3', 'Ridge Fasteners', '2026-08-25', [['Joist hangers LUS26', 100, 'ea', 1.60]], { status: 'issued' });
  // a bill over its PO: the three-way match's, never counted again here
  PO('pwt_st', 'Ridge Fasteners', '2026-08-20', [['Simpson strap ST2215', 100, 'ea', 2.00]], { status: 'issued' });
  BILL('pwt_bst', 'RF-3302', 'Ridge Fasteners', '2026-08-24', [{ desc: 'Simpson strap ST2215', qty: 100, unit: 'ea', amount: 240, poLineId: 'pwt_stl0' }], { poId: 'pwt_st' });
  // split: two screw orders a day apart, each under $2,500, together over it
  PO('pwt_sp1', 'Ridge Fasteners', '2026-08-26', [['Simpson SDWS screw 3in (box of 50)', 28, 'box', 50]], { status: 'issued' });
  PO('pwt_sp2', 'Ridge Fasteners', '2026-08-27', [['Simpson SDWS screw 3in (box of 50)', 26, 'box', 50]], { status: 'issued' });
  // not delivered: a job's order shipped to the shop; a billed order never received a week after its date
  PO('pwt_shop', 'Ridge Fasteners', '2026-08-12', [['Simpson A35 clip', 50, 'ea', 0.90]], { shipTo: 'shop', status: 'issued' });
  PO('pwt_ty', 'Atlantic Yard Supply', '2026-08-10', [['Tyvek house wrap 9x150', 2, 'roll', 180, { received: 0 }]], { status: 'issued', expected: '2026-08-14' });
  BILL('pwt_bty', 'AY-5460', 'Atlantic Yard Supply', '2026-08-15', [{ desc: 'Tyvek house wrap 9x150', qty: 2, unit: 'roll', amount: 360, poLineId: 'pwt_tyl0' }], { poId: 'pwt_ty' });
  // a rarely used vendor for lumber
  PO('pwt_vl', 'Valley Lumber Outlet', '2026-08-20', [["2x6 x 12' joist", 40, 'ea', 9.80]], { status: 'issued' });
  // the quote it was bought against: a confirmed RFQ quote at $11.20, the PO at $12.10
  DB.rfqs = DB.rfqs || [];
  DB.rfqs.push({ id: 'pwt_rfq', number: 'RFQ-2026-901', projectId: 'p121', title: 'Floor joists', category: 'Lumber', shippable: true, status: 'awarded', createdAt: '2026-08-08T10:00:00', createdBy: 'Chen Biron', needBy: '2026-08-20', orderBy: '', taskId: '', estLine: null, budgets: null, facts: [], assumptions: [], takeoff: null,
    lines: [{ id: 'L1', key: 'line', item: "2x8 x 12' joist", qty: 20, unit: 'ea' }], vendors: [{ id: 'vbl', name: 'Brooklyn Lumber Co', region: 'NYC Manhattan/Brooklyn' }], dueDate: '2026-08-10', sent: [], neg: [], history: [], foreman: 'Angel',
    quotes: [{ id: 'pwt_q1', vendorId: 'vbl', vendor: 'Brooklyn Lumber Co', round: 1, date: '2026-08-10', confirmed: true, lines: [{ lineId: 'L1', unit: 11.20 }], flags: [], freight: 0, lead: 3 }] });
  PO('pwt_rq', 'Brooklyn Lumber Co', '2026-08-15', [["2x8 x 12' joist", 20, 'ea', 12.10, { rfqId: 'pwt_rfq', rfqLineId: 'L1' }]], { status: 'issued', origin: 'rfq', rfqId: 'pwt_rfq' });
  // quantity: three more windows on the nine-window estimate line (12 against 9)
  PO('pwt_win', 'Window Works', '2026-08-30', [['Double-hung windows, front & rear', 3, 'ea', 3300, { line: 'estimate:es1:l3', code: '04' }]], { status: 'issued' });
  // duplicates: two Atlantic bills 1.5% apart three days apart; an earlier one far off (noise); two hardware charges
  BILL('pwt_ay1', 'AY-5512', 'Atlantic Yard Supply', '2026-08-29', [{ desc: 'Lumber delivered Aug 29', amount: 1212.40 }]);
  BILL('pwt_ay2', 'AY-5519', 'Atlantic Yard Supply', '2026-09-01', [{ desc: 'Lumber delivered Sep 1', amount: 1230.00 }]);
  BILL('pwt_ay0', 'AY-5490', 'Atlantic Yard Supply', '2026-08-12', [{ desc: 'Lumber delivered Aug 12', amount: 980.00 }]);
  TX('pwt_hw1', '2026-08-30', 'QUALITY HARDWARE 0441', -212.18, { vendor: 'Quality Hardware', receipt: 'https://drive.example/r1' });
  TX('pwt_hw2', '2026-09-01', 'QUALITY HARDWARE 0441', -214.40, { vendor: 'Quality Hardware', receipt: 'https://drive.example/r2' });
  // a card buy at a supply house with no job, PO or receipt; the same with a receipt (noise)
  TX('pwt_hd', '2026-09-01', 'HOME DEPOT #6166 BROOKLYN NY', -312.45, { vendor: 'Home Depot' });
  TX('pwt_hd2', '2026-08-31', 'HOME DEPOT #6166 BROOKLYN NY', -98.20, { vendor: 'Home Depot', receipt: 'https://drive.example/r3' });
  // use tax: an out-of-state bill with no NY tax; another that carried it (noise)
  BILL('pwt_km', 'KMD-881', 'Keystone Mill Direct', '2026-09-02', [{ desc: "2x10 x 16' joist, 80 pcs", amount: 1840 }]);
  BILL('pwt_km0', 'KMD-870', 'Keystone Mill Direct', '2026-08-20', [{ desc: 'Joists', amount: 900 }, { desc: 'NY use tax', amount: 79.88 }]);
  // the card line for the August stud order, matched later
  TX('pwt_cbl', '2026-08-29', 'BROOKLYN LUMBER CO', -1083.00, { vendor: 'Brooklyn Lumber Co', cat: 'materials', projectId: 'p121', status: 'new' });
  save(); pwFresh(); return true; }"""

def stud_key(): return 'pw:paid:po:pwt_s7:pwt_s7l0'

async def ask(pg, q):
    return await pg.evaluate("async q => { const r = await paAsk(q); const o = typeof r === 'string' ? { headline: r } : (r || {}); return [o.headline || o.text || '', (o.work || []).join(' | ')].join(' || '); }", q)

async def main():
    C = Checks()
    async with async_playwright() as p:
        b, pg, errs = await open_app(p)
        await sign_in(pg, 'u_owner')
        seed_counts = dict((d, c) for d, c, *_ in await pg.evaluate(COUNTS, DETS))
        await pg.evaluate(SEED)

        # ---- history: one function, normalised, with sources
        H = await pg.evaluate("() => { const H = itemPriceHistory(\"2x4 x 10' stud\"); return { label: H.label, n: H.n, unit: H.unit, rows: H.rows.map(r => [r.date, r.vendor, r.price, r.sources]), median: H.median }; }")
        C.ok(H['n'] == 7 and H['unit'] == 'ea' and all(r[3] for r in H['rows']), f'stud history: seven buys from POs, each with its source ({H["n"]})')
        hg = await pg.evaluate("() => itemPriceHistory('Joist hanger LUS26').rows.map(r => [r.date, r.price, r.qty, r.unit])")
        C.ok(hg[:2] == [['2026-06-01', 1.1, 100, 'ea'], ['2026-07-01', 1.12, 100, 'ea']], f'a box of 50 at $55 reads as 100 each at $1.10, beside the loose ones ({hg[:2]})')
        src = await pg.evaluate("() => itemPriceHistory('1/2in CDX plywood 4x8').rows.filter(r => r.date === '2026-08-22').map(r => [r.price, r.sources])")
        C.ok(src and src[0][0] == 40 and any('BL-7781' in s for s in src[0][1]) and any('PO-' in s for s in src[0][1]), f'a bill on a PO line is the same buy: its paid price and both sources ({src})')
        qh = await pg.evaluate("() => itemPriceHistory(\"2x8 x 12' joist\").rows.map(r => [r.kind, r.price])")
        C.ok(['quote', 11.2] in qh and ['po', 12.1] in qh, f'confirmed quotes are in the history beside the buys ({qh})')
        mp = await pg.evaluate("() => pwMatchProps().map(m => [m.fromLabel, m.toLabel])")
        C.ok(["2x4 10' KD stud", "2x4 x 10' stud"] in mp, f'a near match is a proposal, not assumed ({mp})')
        await sign_in(pg, 'u_chen')
        qm = await pg.evaluate("() => mApprovals().filter(i => i.kind === 'priceMatch').map(i => [i.title, i.who])")
        C.ok(any("KD stud" in t and w == 'coord' for t, w in qm), f'the coordinator confirms it, in Approvals ({qm})')
        await pg.evaluate("() => { const m = pwMatchProps().find(x => /KD/.test(x.fromLabel)); pwMatchDecide(m.id, true); }")
        H2 = await pg.evaluate("() => itemPriceHistory(\"2x4 x 10' stud\").n")
        C.ok(H2 == 8 and not await pg.evaluate("() => pwMatchProps().some(m => /KD/.test(m.fromLabel))"), f'confirmed: the KD stud is read as the same item ({H2} buys)')
        rp = await pg.evaluate("() => rfqPayNow('Lumber')")
        C.ok(rp and rp['unit'] == 7.4 and 'price history' in rp['source'], f'the RFQ module reads the same history for what we pay now ({rp})')

        # ---- detectors: each fires on its case and not on the noise
        await sign_in(pg, 'u_owner')
        K = {d: await pg.evaluate(KEYS, d) for d in DETS}
        want = {
            'pwPaidMore': {stud_key(), 'pw:paid:po:pwt_p4:pwt_p4l0', 'pw:paid:po:pwt_d4:pwt_d4l0', 'pw:paid:po:pwt_rq:pwt_rql0'},
            'pwQtyOver': {'pw:qty:estimate:es1:l3'},
            'pwDupCharge': {'pw:dup:bill:pwt_ay2', 'pw:dup:txn:pwt_hw2'},
            'pwFeeSpike': {'pw:fee:po:pwt_s7'},
            'pwRareVendor': {'pw:rare:po:pwt_vl'},
            'pwNotDelivered': {'pw:away:pwt_shop', 'pw:notrecv:pwt_ty'},
            'pwCardNoJob': {'pw:card:pwt_hd'},
            'pwUseTax': {'pw:usetax:pwt_km'},
        }
        for d, w in want.items():
            mine = {k for k in K[d] if 'pwt_' in k or k == 'pw:qty:estimate:es1:l3'}
            C.ok(mine == w, f'{d} fires on its case and not on the noise ({sorted(mine)} vs {sorted(w)})')
        sp = await pg.evaluate("() => PRED.pwSplit.rows().filter(c => c.refs.includes('pwt_sp1') && c.refs.includes('pwt_sp2')).map(c => [c.amount, c.limit])")
        C.ok(len(sp) == 1 and sp[0][1] == 2500, f'split: the two screw orders under $2,500 that together pass it ({sp})')
        C.ok(not any(k for k in K['pwSplit'] if 'pwt_s' in k.replace('pwt_sp', '') or 't8' in k), f'split: no stud order and no exact duplicate counted as a split ({K["pwSplit"]})')
        kinds = await pg.evaluate("() => Object.fromEntries(PRED.pwPaidMore.rows().filter(c => /pwt_/.test(c.key)).map(c => [c.key, c.kinds]))")
        C.ok(set(kinds[stud_key()]) == {'median', 'otherVendor'}, f'studs: over the trailing median and over a cheaper recent price from another vendor ({kinds[stud_key()]})')
        C.ok(kinds['pw:paid:po:pwt_p4:pwt_p4l0'] == ['againstPO'] and kinds['pw:paid:po:pwt_rq:pwt_rql0'] == ['againstQuote'] and kinds['pw:paid:po:pwt_d4:pwt_d4l0'] == ['median'], f'plywood over its PO price, joists over their quote, drywall over the median ({kinds})')
        st = await pg.evaluate("() => ({ over: CATCH.find(c => c.name === 'overPO').rows().some(r => r.key === 'bill:pwt_bst'), pw: pwCasesAll().some(c => c.refs.includes('pwt_bst')) })")
        C.ok(st['over'] and not st['pw'], f'a bill over its PO stays on Billed Over the PO and is not counted again ({st})')
        am = await pg.evaluate("k => PRED.pwPaidMore.rows().find(c => c.key === k).amount", stud_key())
        C.ok(abs(am - r2((7.40 - 6.35) * 120)) < 0.02, f'money at stake on the studs: (7.40 - the usual 6.35) x 120 ({am})')
        st0 = {d: c for d, c in seed_counts.items()}
        C.ok(st0['pwPaidMore'] == 0 and st0['pwSplit'] == 0, f'the seed alone raises no price flag and no split from its exact duplicate ({seed_counts})')

        # ---- min history: two earlier buys are not enough
        mh = await pg.evaluate("() => { const B = pwData().byId['po:pwt_h3:pwt_h3l0']; return pwPriceCheck(B, pwData().items[B.key]); }")
        C.ok(mh['n'] == 2 and not mh['reasons'] and 'not enough history' in mh['note'], f'hangers at +45% with two earlier buys: no flag, "not enough history" ({mh["note"]})')

        # ---- counts equal rows
        ce = await pg.evaluate(COUNTS, DETS)
        C.ok(all(c == r == k for _, c, r, k, _ in ce) and len({l for *_, l in ce}) == len(DETS), f'every detector: count = rows = Caught for You rows, one label each ({ce})')

        # ---- the PO draft: a Price Check with the history before it is committed
        await sign_in(pg, 'u_chen')
        dr = await pg.evaluate("""() => { const po = { id: 'pwt_draft', number: 'PO-2026-990', projectId: 'p121', vendor: 'Brooklyn Lumber Co', date: today(), status: 'draft', type: 'materials', shipTo: 'site', tax: 0, shipping: 0,
            lines: [{ id: 'dl1', item: "2x4 x 10' stud", qty: 100, unit: 'ea', price: 7.60, code: '03' }, { id: 'dl2', item: 'Simpson SDWS screw 3in (box of 50)', qty: 10, unit: 'box', price: 50, code: '03' }], receipts: [], matchedTxns: [], srcDocs: [], __v2: 1 };
            DB.pos.push(po); poOpen = po.id; view = 'po'; render(); const v = document.getElementById('v-po'); const box = v && v.querySelector('.pw-po');
            return { box: box ? box.innerText : '', rows: box ? box.querySelectorAll('.pw-hist tbody tr').length : 0, html: renderPODoc(po).includes('Price Check Before You Commit') }; }""")
        C.ok(dr['html'] and 'Price Check Before You Commit' in dr['box'], f'the PO draft shows a Price Check ({dr["box"][:80]})')
        C.ok('over the usual' in dr['box'] and dr['rows'] >= 5, f'the overpriced line says how far over, with its history ({dr["rows"]} rows)')
        C.ok('not enough history' in dr['box'], 'a line with two earlier buys says "not enough history"')
        iss = await pg.evaluate("() => { const po = DB.pos.find(x => x.id === 'pwt_draft'); po.status = 'issued'; render(); return renderPODoc(po).includes('Price Check Before You Commit'); }")
        C.ok(not iss, 'once issued, the draft warning is gone (the case takes over)')
        await pg.evaluate("() => { DB.pos = DB.pos.filter(x => x.id !== 'pwt_draft'); poOpen = null; save(); pwFresh(); }")

        # ---- a card line matched to a flagged order says so at once
        await sign_in(pg, 'u_controller')
        mt = await pg.evaluate("async () => { const t = DB.txns.find(x => x.id === 'pwt_cbl'); const r = truthSetMatch(t, { poId: 'pwt_s7', poLineId: 'pwt_s7l0' }); await new Promise(s => setTimeout(s, 60)); return { ok: r && r.ok !== false, chk: t.pwChecked, toast: (document.getElementById('toast') || {}).innerText || '' }; }")
        C.ok(mt['ok'] and mt['chk'] and mt['chk']['key'] in (stud_key(), 'pw:fee:po:pwt_s7') and 'Price watch' in mt['toast'], f'matching the card line to the flagged order raises it ({mt})')
        hs = await pg.evaluate("k => (pwCase(k).hist.find(h => h.date === '2026-08-28') || {}).sources", stud_key())
        C.ok(hs and any('card line' in s for s in hs), f'the matched card line is a source on the buy ({hs})')

        # ---- the figure: paid above the best recent price, queryable
        F = await pg.evaluate("() => ({ f: pwAboveBest('2026-09'), q: EQ_TABLES.paidabovebest().filter(r => r.month === '2026-09').reduce((a, r) => a + r.amount, 0) })")
        C.ok(abs(F['f']['total'] - r2((14.90 - 12.90) * 60)) < 0.005 and abs(F['q'] - F['f']['total']) < 0.005, f'September: $120.00 paid above the best recent price, the same in erpQuery ({F["f"]["total"]}, {F["q"]})')
        eq = await pg.evaluate("() => ({ c: EQ_TABLES.pricewatch().length, h: EQ_TABLES.pricehistory().length, x: EQ_TABLES.priceexplanations().length })")
        C.ok(eq['c'] >= 12 and eq['h'] >= 25, f'erpQuery: pricewatch, pricehistory, priceexplanations, paidabovebest ({eq})')

        # ---- Ask
        await sign_in(pg, 'u_owner')
        a1 = await ask(pg, 'where did we pay more than usual this month')
        C.ok('over the usual price' in a1 and 'drywall' in a1.lower() and '$120' in a1, f'Ask where we paid more: {a1[:200]}')
        a2 = await ask(pg, 'price history for 2x4 studs')
        C.ok("2x4 x 10' stud" in a2 and '8 buys' in a2 and 'Brooklyn Lumber Co' in a2, f'Ask price history: {a2[:200]}')
        await pg.evaluate("k => { pwCaseSheet(k); mbCloseModal(); }", stud_key())
        a3 = await ask(pg, 'why is this flagged')
        C.ok('Paid More Than Before' in a3 and 'Hypothesis' in a3 and 'raises, bonuses' in a3, f'Ask why is this flagged: {a3[:200]}')

        # ---- the case: history with sources, money at stake, hypotheses, a next step, the money line, neutral words
        await sign_in(pg, 'u_chen')
        await pg.evaluate("k => pwCaseSheet(k)", stud_key())
        cs = await pg.evaluate("() => ({ t: (document.querySelector('#mbm') || {}).innerText || '', prim: [...document.querySelectorAll('#mbm .btn.primary')].map(b => b.innerText.trim()), rows: document.querySelectorAll('#mbm .pw-hist tbody tr').length })")
        C.ok('Money at Stake' in cs['t'] and 'Hypothesis' in cs['t'] and 'Wasted money comes out of raises, bonuses, staff and the extra value we give clients.' in cs['t'] and cs['rows'] >= 8, f'the case: money at stake, hypotheses, history with sources, the money line ({cs["rows"]} rows)')
        C.ok(cs['prim'] == ['Ask Vendor for Credit'] and all(w in cs['t'] for w in ('Update the Price Book', 'Add to Next RFQ', 'Propose Explanation')), f'one blue primary, the next steps beside it ({cs["prim"]})')
        C.ok(not any(w in cs['t'].lower() for w in ('fraud', 'theft', 'suspicious', 'stole', 'accus')), 'neutral words, never an accusation')

        # ---- explain: the coordinator's explanation leaves the flag open and the baseline where it was
        await pg.locator('#mbm [data-pwstep="explain"]').click(); await pg.wait_for_timeout(300)
        await pg.locator('#mbm [data-f="text"]').fill('Rush delivery for the framing inspection')
        await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(400)
        e1 = await pg.evaluate("() => JSON.parse(JSON.stringify(DB.priceWatch.expl.slice(-1)[0]))")
        st1 = await pg.evaluate("k => ({ open: PRED.pwPaidMore.rows().some(c => c.key === k), base: DB.priceWatch.baselines.length, mine: mApprovals().filter(i => i.kind === 'priceExplain').length, all: mApprovals({ everyone: true }).filter(i => i.kind === 'priceExplain').map(i => i.who) })", stud_key())
        C.ok(e1['status'] == 'proposed' and e1['by'] == 'Chen Biron' and e1['flagKey'] == stud_key() and e1['history'][0]['what'] == 'proposed', f'proposed by the coordinator ({e1["status"]}, {e1["by"]})')
        C.ok(st1['open'] and st1['base'] == 0 and st1['mine'] == 0 and st1['all'] == ['owner'], f'the flag stays open and counted, the baseline does not move, it waits on the owner only ({st1})')
        await sign_in(pg, 'u_owner')
        q = await pg.evaluate("() => ({ a: mApprovals().filter(i => i.kind === 'priceExplain').map(i => i.title), d: tdQueue().filter(i => i.kind === 'priceExplain').map(i => tdCard(i).verb) })")
        C.ok(len(q['a']) == 1 and q['d'] == ['Decide'], f'the owner sees it in Approvals and Do Now ({q})')
        # the decline needs a reason
        none = await pg.evaluate("id => pwDecide(id, 'decline', '')", e1['id'])
        C.ok(none is None and await pg.evaluate("id => DB.priceWatch.expl.find(e => e.id === id).status", e1['id']) == 'proposed', 'a decline with no reason is refused')
        await go(pg, 'mapprove')
        await pg.locator(f'#v-mapprove .m-appr[data-mid="{e1["id"]}"] [data-mno]').click(); await pg.wait_for_timeout(300)
        await pg.locator('#mbm #mbm-alt').click(); await pg.wait_for_timeout(200)
        C.ok(await pg.evaluate("id => DB.priceWatch.expl.find(e => e.id === id).status", e1['id']) == 'proposed' and await pg.evaluate("() => !!document.querySelector('#mbm')"), 'Decline with the reason empty keeps the sheet open')
        await pg.locator('#mbm [data-f="reason"]').fill('The inspection was booked two weeks ahead; no rush was needed')
        await pg.locator('#mbm #mbm-alt').click(); await pg.wait_for_timeout(400)
        e1b = await pg.evaluate("id => JSON.parse(JSON.stringify(DB.priceWatch.expl.find(e => e.id === id)))", e1['id'])
        st2 = await pg.evaluate("k => ({ open: PRED.pwPaidMore.rows().some(c => c.key === k), base: DB.priceWatch.baselines.length, closed: !!DB.priceWatch.closed[k] })", stud_key())
        C.ok(e1b['status'] == 'declined' and e1b['reason'].startswith('The inspection') and [h['what'] for h in e1b['history']] == ['proposed', 'declined'] and e1b['history'][1]['by'] and e1b['history'][1]['note'].startswith('The inspection'), f'declined with the reason; the history is proposed then declined, who and when ({[h["what"] for h in e1b["history"]]})')
        C.ok(st2['open'] and not st2['closed'] and st2['base'] == 0, f'after the decline the flag stays open ({st2})')
        # a baseline change: lumber up 8% this quarter
        await sign_in(pg, 'u_chen')
        await pg.evaluate("k => pwCaseSheet(k)", stud_key())
        await pg.locator('#mbm [data-pwstep="explain"]').click(); await pg.wait_for_timeout(300)
        await pg.locator('#mbm [data-f="text"]').fill('Lumber up 8% this quarter')
        await pg.locator('#mbm [data-f="scope"]').select_option('baseline')
        await pg.locator('#mbm [data-f="pct"]').fill('8')
        await pg.locator('#mbm [data-f="for"]').select_option('cat')
        await pg.locator('#mbm [data-f="from"]').fill('2026-07-01')
        await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(400)
        e2 = await pg.evaluate("() => JSON.parse(JSON.stringify(DB.priceWatch.expl.slice(-1)[0]))")
        st3 = await pg.evaluate("k => ({ open: PRED.pwPaidMore.rows().some(c => c.key === k), base: DB.priceWatch.baselines.length, med: pwCase(k).median })", stud_key())
        C.ok(e2['scope'] == 'baseline' and e2['category'] == 'Lumber' and e2['pct'] == 8 and e2['from'] == '2026-07-01' and e2['status'] == 'proposed', f'a baseline change is proposed ({e2["scope"]}, {e2["category"]}, {e2["pct"]})')
        C.ok(st3['open'] and st3['base'] == 0 and abs(st3['med'] - 6.35) < 0.001, f'until the owner approves, the baseline does not move and the flag stays ({st3})')
        C.ok(not await pg.evaluate("() => Object.keys((DB.learn || {}).events || {}).some(k => k.startsWith('pricex:'))"), 'no lesson before the owner approves')
        await sign_in(pg, 'u_owner')
        await go(pg, 'mapprove')
        await pg.locator(f'#v-mapprove .m-appr[data-mid="{e2["id"]}"] [data-myes]').click(); await pg.wait_for_timeout(500)
        st4 = await pg.evaluate("k => ({ open: PRED.pwPaidMore.rows().some(c => c.key === k), base: DB.priceWatch.baselines.map(b => [b.category, b.pct, b.from, b.by]), v: DB.priceWatch.flags[k].verdict, st: DB.priceWatch.expl.slice(-1)[0].status, hist: DB.priceWatch.expl.slice(-1)[0].history.map(h => h.what), ev: Object.keys(DB.learn.events).filter(x => x.startsWith('pricex:')).length, lesson: (DB.lessons || []).some(l => l.learn === 'priceExplained'), prop: (DB.learn.props.priceExplained || {}).status })", stud_key())
        C.ok(st4['st'] == 'approved' and st4['hist'] == ['proposed', 'approved'] and len(st4['base']) == 1 and st4['base'][0][:3] == ['Lumber', 8, '2026-07-01'], f'the owner approves: the baseline moves ({st4["base"]})')
        C.ok(not st4['open'] and st4['v'] == 'normal', f'the studs are no longer flagged: the normal change is not flagged again ({st4["open"]}, {st4["v"]})')
        C.ok(st4['ev'] == 1 and st4['lesson'] and st4['prop'] == 'approved', f'the brain records the lesson only now ({st4})')
        oth = await pg.evaluate("() => ['pw:paid:po:pwt_p4:pwt_p4l0', 'pw:paid:po:pwt_rq:pwt_rql0'].map(k => PRED.pwPaidMore.rows().some(c => c.key === k))")
        C.ok(oth == [True, True], 'a price over its PO or quote is not moved by a market baseline')
        # a "this quarter" explanation ends at the quarter's end and is then checked again; one purchase never expires
        qe = await pg.evaluate("""() => { const b = DB.priceWatch.baselines.slice(-1)[0], I = Object.values(pwData().items).find(i => i.cat === b.category) || { key: '', cat: b.category };
            const inQ = pwAdj(I, 100, '2026-06-15', '2026-09-20'), after = pwAdj(I, 100, '2026-06-15', '2026-10-05');
            const one = DB.priceWatch.expl.filter(e => e.scope === 'purchase' && e.status === 'approved').map(e => e.until || '');
            return { until: b.until, ex: DB.priceWatch.expl.find(e => e.id === b.explId).until, inQ, after, one }; }""")
        C.ok(qe['until'] == '2026-09-30' and qe['ex'] == '2026-09-30', f'the quarter\'s baseline ends on its last day ({qe})')
        C.ok(abs(qe['inQ'] - 108) < 0.001 and abs(qe['after'] - 100) < 0.001, f'inside the quarter the baseline applies; after it the purchase is checked against the plain history ({qe})')
        C.ok(all(u == '' for u in qe['one']), f'an explanation for one purchase never expires ({qe["one"]})')
        # a purchase explanation, approved: the fee spike closes
        await sign_in(pg, 'u_chen')
        e3 = await pg.evaluate("() => pwPropose({ flagKey: 'pw:fee:po:pwt_s7', text: 'Saturday delivery for the framing inspection', scope: 'purchase' }).id")
        C.ok(await pg.evaluate("() => PRED.pwFeeSpike.count()") == 1, 'the fee flag stays counted while the owner decides')
        await sign_in(pg, 'u_owner')
        await pg.evaluate("id => pwDecideSheet(id)", e3); await pg.wait_for_timeout(200)
        C.ok(await pg.evaluate(PRIMARY, '#mbm') == ['Approve'], 'the decision sheet: one blue primary, Approve')
        await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(400)
        f3 = await pg.evaluate("() => ({ n: PRED.pwFeeSpike.count(), closed: DB.priceWatch.closed['pw:fee:po:pwt_s7'], t: (document.getElementById('toast') || {}).innerText || '' })")
        C.ok(f3['n'] == 0 and f3['closed'] and f3['closed']['how'] == 'explained' and 'Approved' in f3['t'], f'approved: the fee flag is closed as explained, toasted ({f3["n"]})')

        # ---- precision: under 50% confirmed over 30 days, the owner is asked to tune
        await sign_in(pg, 'u_chen')
        for k in ('pw:paid:po:pwt_p4:pwt_p4l0', 'pw:paid:po:pwt_d4:pwt_d4l0'):
            await pg.evaluate("k => pwPropose({ flagKey: k, text: 'A different grade from the earlier buys', scope: 'purchase' })", k)
        await sign_in(pg, 'u_owner')
        await pg.evaluate("() => DB.priceWatch.expl.filter(e => e.status === 'proposed').forEach(e => pwDecide(e.id, 'approve'))")
        pr0 = await pg.evaluate("() => ({ p: pwPrecision('pwPaidMore'), t: !!DB.priceWatch.tune.pwPaidMore })")
        C.ok(pr0['p']['counted'] == 3 and pr0['p']['real'] == 0 and not pr0['t'], f'three ruled normal and one still young: not enough to judge yet ({pr0["p"]})')
        await pg.evaluate("() => pwCaseSheet('pw:paid:po:pwt_rq:pwt_rql0')")
        await pg.locator('#mbm [data-pwreal]').click(); await pg.wait_for_timeout(400)
        pr = await pg.evaluate("() => ({ p: pwPrecision('pwPaidMore'), t: DB.priceWatch.tune.pwPaidMore, a: mApprovals().filter(i => i.kind === 'priceTune').map(i => [i.title, i.who]) })")
        C.ok(pr['p']['counted'] == 4 and pr['p']['real'] == 1 and pr['p']['pct'] == 25, f'precision 1 of 4 confirmed real, 25% ({pr["p"]})')
        C.ok(pr['t'] and pr['t']['from'] == 10 and pr['t']['to'] == 15 and pr['a'] and pr['a'][0][1] == 'owner', f'the owner is asked to tune: 10% to 15% ({pr["a"]})')
        C.ok(await pg.evaluate("() => pwPrecision('pwFeeSpike').counted") < 4 and not await pg.evaluate("() => !!DB.priceWatch.tune.pwFeeSpike"), 'a detector with too few flags is not tuned')
        await go(pg, 'mapprove')
        await pg.locator('#v-mapprove .m-appr[data-mk="priceTune"] [data-myes]').click(); await pg.wait_for_timeout(400)
        tu = await pg.evaluate("() => ({ s: pwSet().overPct, log: DB.priceWatch.settingsLog.slice(-1)[0] })")
        C.ok(tu['s'] == 15 and tu['log']['from'] == 10 and tu['log']['by'], f'approved: the threshold is 15%, logged ({tu})')

        # ---- use tax on the out-of-state bill
        ut = await pg.evaluate("() => ({ amt: (PRED.pwUseTax.rows().find(c => c.billId === 'pwt_km') || {}).amount, flags: billFlags(DB.bills.find(b => b.id === 'pwt_km')), noise: billFlags(DB.bills.find(b => b.id === 'pwt_km0')).some(f => /use tax/.test(f)), rate: rfqTaxRate() })")
        C.ok(abs(ut['amt'] - r2(1840 * ut['rate'] / 100)) < 0.005 and any('use tax' in f and 'confirm with the accountant' in f for f in ut['flags']) and not ut['noise'], f'use tax to accrue on the bill, at the RFQ module\'s rate; none on the bill that carried tax ({ut["amt"]})')
        await sign_in(pg, 'u_controller')
        await pg.evaluate("() => pwCaseSheet('pw:usetax:pwt_km')")
        await pg.locator('#mbm [data-pwstep="accrue"]').click(); await pg.wait_for_timeout(400)
        ua = await pg.evaluate("() => ({ n: PRED.pwUseTax.rows().filter(c => c.billId === 'pwt_km').length, b: DB.bills.find(b => b.id === 'pwt_km').useTaxAccrued })")
        C.ok(ua['n'] == 0 and ua['b'] and ua['b']['by'], f'the controller records the accrual; the flag closes ({ua})')

        # ---- the page: counts equal rows; then 390px
        await sign_in(pg, 'u_owner')
        await pg.evaluate("() => pwOpenPage()"); await pg.wait_for_timeout(300)
        pgc = await pg.evaluate("() => [...document.querySelectorAll('#v-rfq [data-pwdet]')].map(e => [e.dataset.pwdet, +e.dataset.pwn, e.querySelectorAll('[data-pwopen]').length, PRED[e.dataset.pwdet].count()])")
        C.ok(pgc and all(n == r == c for _, n, r, c in pgc), f'Price Watch page: each section\'s count equals its rows and the predicate ({pgc})')
        C.ok(await pg.evaluate(PRIMARY, '#v-rfq') == [], 'the Price Watch tab has no blue primary of its own (New RFQ stays plain here)')
        ce = await pg.evaluate(COUNTS, DETS)
        C.ok(all(c == r == k for _, c, r, k, _ in ce), f'after the decisions: counts still equal rows ({ce})')
        await pg.set_viewport_size({'width': 390, 'height': 844}); await pg.evaluate("() => render()"); await pg.wait_for_timeout(300)
        C.ok(await pg.evaluate(NOSIDE), 'phone: the Price Watch page does not scroll sideways')
        await pg.evaluate("() => pwCaseSheet('pw:paid:po:pwt_rq:pwt_rql0')"); await pg.wait_for_timeout(200)
        C.ok(await pg.evaluate(NOSIDE), 'phone: a case does not scroll sideways')
        await pg.evaluate("() => { mbCloseModal(); pwExplainSheet('pw:rare:po:pwt_vl'); }"); await pg.wait_for_timeout(200)
        C.ok(await pg.evaluate(NOSIDE) and await pg.evaluate(PRIMARY, '#mbm') == ['Send to the Owner'], 'phone: the explanation sheet fits, one blue primary')
        await pg.evaluate("() => mbCloseModal()")
        await pg.set_viewport_size({'width': 1440, 'height': 900})

        # ---- reload: everything survives
        snap = "() => JSON.stringify({ e: DB.priceWatch.expl.map(e => [e.id, e.status, e.reason || '', e.history.length]), b: DB.priceWatch.baselines.map(b => [b.category, b.pct]), c: Object.keys(DB.priceWatch.closed).sort(), v: Object.values(DB.priceWatch.flags).filter(f => f.verdict).map(f => [f.key, f.verdict]).sort(), s: pwSet().overPct, a: DB.priceWatch.alias, open: Object.fromEntries(" + json.dumps(DETS) + ".map(d => [d, PRED[d].count()])) })"
        before = await pg.evaluate(snap)
        await pg.wait_for_timeout(1200)
        await pg.evaluate("() => (typeof trFlush === 'function' ? trFlush() : saveNow())")
        await pg.wait_for_timeout(600)
        await pg.reload(); await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
        after = await pg.evaluate(snap)
        C.ok(before == after, f'explanations, baselines, closed flags, verdicts, thresholds and counts survive a reload ({after[:200]})')
        C.ok(not errs, f'no page errors ({errs[:3]})')
        await b.close()
    return C.done()

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
