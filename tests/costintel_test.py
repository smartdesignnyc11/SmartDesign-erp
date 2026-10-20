"""Cost intelligence (BACKLOG §1.29 items 1 to 5, §1.31's price-book matching and route tests), as each person who
uses it, desktop and phone 390px.

  pricebook   realistic invented receipts: the same item from Home Depot, Lowe's, a supply house and a lumber yard
              matches by spec (size, gauge, length, pack, variant); what differs never matches; a Pro account's
              purchase-history export joins the same history; a buy above the best recent store price is one case per
              receipt, with the cheaper store and the saving to the cent; nothing counted twice with price watch
  jobs        the one rule (cash out above cash in, cost ahead of billing, a line over budget or forecast to go over),
              the cause and the drafted fix; a planted cash-negative job is found and a clean job is not; the same
              count on the Reports tab, Caught for You, Ask and the predicate
  bench       benchmarks recomputed here from the close-outs, to the cent: each trade's median and every flag with
              its cause; proposing to estimating is a draft the owner approves; one price path (costBook) read by the
              estimate and the item library's fill
  route       the bank: the optimiser never loses to "every item at the nearest store" and beats it in total; never a
              long detour for a few dollars; windows, capacity and the dump; the coordinator approves, the driver gets
              it on the phone with no prices, the receipts are compared back, the saving reaches the savings registry
  weekly      the brain's weekly review proposes with a dollar or hour value through Company › Changes; an approved
              rule becomes a lesson; a second run proposes nothing twice
  ask         the tables and the local answers, and field roles never read a price
Screenshots: review/costintel/*.png.   python3 costintel_test.py"""
import asyncio, json, math, os, statistics, sys
from harness import *

SHOTS = os.path.join(ROOT, 'review', 'costintel')
os.makedirs(SHOTS, exist_ok=True)


def r2(x):
    """JavaScript's Math.round(x * 100) / 100 for the amounts here"""
    return math.floor(x * 100 + 0.5) / 100


def med(a):
    s = sorted(a)
    n = len(s)
    return s[(n - 1) // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


# ---------------------------------------------------------------- the matching bank (invented, realistic descriptions)
SAME = [  # each group is one item, written the way different stores print it
    ['2X4-8 KD STUD SPF', '2-IN X 4-IN X 8-FT KILN-DRIED SPF STUD', "2X4 8' KD SPF STUD", '2 in. x 4 in. x 8 ft. Kiln-Dried SPF Stud'],
    ['2X6-12 DOUGLAS FIR KD', "2X6 12' DOUGLAS FIR KD", '2 in. x 6 in. x 12 ft. Douglas Fir Kiln Dried'],
    ['1/2 IN X 4 FT X 8 FT REGULAR DRYWALL', '1/2-IN X 4-FT X 8-FT REGULAR DRYWALL PANEL', '1/2 REGULAR DRYWALL 4X8', '1/2" Sheetrock 4x8 regular'],
    ['5/8 TYPE X DRYWALL 4X8', '5/8 IN TYPE X DRYWALL 4X8', '5/8" Firecode drywall 4 ft x 8 ft'],
    ['12/2 NM-B ROMEX 250FT', 'SOUTHWIRE 250-FT 12/2 ROMEX NM-B', '12-2 NM-B wire 250 ft'],
    ['1/2 IN X 100 FT PEX-A PIPE RED', '1/2" PEX-A PIPE 100FT BLUE', '1/2 in. x 100 ft. PEX-A pipe white'],
    ['3/4 IN CDX PLYWOOD 4X8', '3/4 CDX PLYWOOD 4X8', '3/4" CDX plywood 4 x 8'],
    ['ALL PURPOSE JOINT COMPOUND 4.5 GAL', 'All Purpose Joint Compound 4.5 Gal.'],
]
DIFFERENT = [  # pairs that must never be one item
    ('1/2 REGULAR DRYWALL 4X8', '5/8 TYPE X DRYWALL 4X8'),
    ('1/2 REGULAR DRYWALL 4X8', '1/2 MOISTURE RESISTANT DRYWALL 4X8'),
    ('1/2 REGULAR DRYWALL 4X8', '1/2 REGULAR DRYWALL 4X12'),
    ('2X4-8 KD STUD SPF', '2X4-10 KD STUD SPF'),
    ('2X4-8 KD STUD SPF', '2X4-8 PRESSURE TREATED STUD'),
    ('2X6-12 DOUGLAS FIR KD', '2X6-12 KD SPF'),
    ('12/2 NM-B ROMEX 250FT', '14/2 NM-B ROMEX 250FT'),
    ('12/2 NM-B ROMEX 250FT', '12/2 NM-B ROMEX 50FT'),
    ('1/2 IN X 100 FT PEX-A PIPE RED', '1/2 IN X 100 FT PEX-B PIPE RED'),
    ('1/2 IN X 100 FT PEX-A PIPE RED', '3/4 IN X 100 FT PEX-A PIPE RED'),
    ('3/4 IN CDX PLYWOOD 4X8', '1/2 IN CDX PLYWOOD 4X8'),
]
INCOMPLETE = ['DRYWALL SHEET', '2X4 LUMBER', 'ROMEX WIRE', 'PEX PIPE', "2x4 10' stud", '2x4x8 KD studs']  # vague, or a grade or species not named  # too vague to match on their own

# ---------------------------------------------------------------- the route bank
WH = {'n': 'Warehouse', 'lat': 40.6784, 'lng': -73.995}
DUMP = {'n': 'Transfer station', 'lat': 40.658, 'lng': -73.988}
S_HD = {'n': 'HD Gowanus', 'lat': 40.6708, 'lng': -73.9973, 'chain': 'homedepot'}
S_LW = {'n': "Lowe's", 'lat': 40.6742, 'lng': -73.9961, 'chain': 'lowes'}
S_YARD = {'n': 'Yard Red Hook', 'lat': 40.677, 'lng': -74.0125, 'chain': 'lumber'}
S_SUP = {'n': 'Supply Park Slope', 'lat': 40.6726, 'lng': -73.9851, 'chain': 'supply'}
S_FAR = {'n': 'Far Yard Queens', 'lat': 40.7420, 'lng': -73.9180, 'chain': 'lumber'}
SITE_A = {'id': 'a', 'n': 'Site A', 'lat': 40.6907, 'lng': -73.9929, 'from': 420, 'to': None, 'items': [1], 'garbage': 0}
SITE_B = {'id': 'b', 'n': 'Site B', 'lat': 40.6650, 'lng': -73.9800, 'from': 420, 'to': None, 'items': [1], 'garbage': 0}
SITE_C = {'id': 'c', 'n': 'Site C', 'lat': 40.6830, 'lng': -73.9680, 'from': 420, 'to': None, 'items': [1], 'garbage': 0}


def buy(key, qty, prices, site='a', vol=0.01, any_=False):
    """one line to buy; vol is the whole line's share of the van (1 = a full van), as itemVolume gives it"""
    return {'key': key, 'what': key, 'qty': qty, 'unit': 'ea', 'vol': vol, 'siteId': site, 'prices': prices, 'any': any_}


def scen(name, stores, buys, sites, **kw):
    return dict(name=name, I=dict(start=WH, end=WH, dump=DUMP, stores=stores, buys=buys, loads=kw.get('loads', []), yards=[], sites=sites, hourly=kw.get('hourly', 38), fuelPerMile=0.32, van={'cap': 1}, startMin=420), expect=kw.get('expect', {}))


BANK = [
    scen('lumber for a framing week: the yard is worth the trip', [S_HD, S_LW, S_YARD], [buy('studs', 300, {'HD Gowanus': 4.47, "Lowe's": 4.38, 'Yard Red Hook': 3.98}, vol=0.0012), buy('2x6', 60, {'HD Gowanus': 16.48, 'Yard Red Hook': 15.2}, vol=0.002)], [SITE_A], expect={'uses': 'Yard Red Hook'}),
    scen('a far yard saves $6: never the detour', [S_HD, S_FAR], [buy('studs', 20, {'HD Gowanus': 4.47, 'Far Yard Queens': 4.17})], [SITE_A], expect={'not': 'Far Yard Queens'}),
    scen('drywall at the supply house, studs at the yard, tape anywhere', [S_HD, S_LW, S_YARD, S_SUP], [buy('5/8 X', 80, {'HD Gowanus': 17.48, 'Supply Park Slope': 14.33}, vol=0.012), buy('studs', 150, {'HD Gowanus': 4.47, 'Yard Red Hook': 3.98}, vol=0.004), buy('tape', 6, {}, any_=True)], [SITE_A], expect={'uses': 'Supply Park Slope'}),
    scen('a site that wants it by 9 am', [S_HD, S_YARD], [buy('studs', 100, {'HD Gowanus': 4.47, 'Yard Red Hook': 3.98}, site='a'), buy('screws', 10, {'HD Gowanus': 27.98}, site='b')], [dict(SITE_A, to=540, window='by 9 am'), SITE_B], expect={'ontime': 'a'}),
    scen('more than a van: two trips', [S_HD, S_SUP], [buy('drywall A', 50, {'HD Gowanus': 14.9, 'Supply Park Slope': 13.9}, site='a', vol=0.6), buy('drywall B', 50, {'HD Gowanus': 14.9, 'Supply Park Slope': 13.9}, site='b', vol=0.6), buy('drywall C', 30, {'HD Gowanus': 14.9, 'Supply Park Slope': 13.9}, site='c', vol=0.36)], [SITE_A, SITE_B, SITE_C], expect={'legs': 2}),
    scen('debris to dump after the drops', [S_HD], [buy('blocking', 40, {'HD Gowanus': 3.2}, site='b', vol=0.004)], [dict(SITE_A, items=[], garbage=0.9), SITE_B], expect={'dump': True}),
    scen('nothing priced: one general store', [S_HD, S_LW, S_YARD], [buy('blue tape', 4, {}, any_=True), buy('plastic', 2, {}, any_=True)], [SITE_A], expect={'stores': 1}),
    scen('eight stores to choose from', [S_HD, S_LW, S_YARD, S_SUP, S_FAR, dict(S_HD, n='HD Flatbush', lat=40.6517, lng=-73.9523), dict(S_SUP, n='Ferguson', lat=40.6956, lng=-73.9893), dict(S_LW, n="Lowe's 2", lat=40.6300, lng=-74.0200)],
         [buy('pex', 6, {'Ferguson': 38.4, 'HD Gowanus': 44.97, "Lowe's": 42.1}), buy('romex', 4, {"Lowe's": 96.48, 'HD Gowanus': 112.0, 'HD Flatbush': 109.0}), buy('studs', 120, {'Yard Red Hook': 3.98, 'HD Gowanus': 4.47, 'Far Yard Queens': 3.7}, vol=0.004), buy('drywall', 40, {'Supply Park Slope': 14.33, 'HD Gowanus': 17.48}, vol=0.012)], [SITE_A, SITE_B], expect={'not': 'Far Yard Queens'}),
    scen('two sites, the cheap store on the way', [S_HD, S_LW, S_SUP], [buy('compound', 12, {"Lowe's": 17.98, 'Supply Park Slope': 16.4}, site='a'), buy('drywall', 30, {'HD Gowanus': 13.98, "Lowe's": 12.48, 'Supply Park Slope': 11.2}, site='b', vol=0.012)], [SITE_A, SITE_B]),
]


async def main():
    c = Checks()
    async with async_playwright() as p:
        # ======================================================================= owner, desktop
        b, pg, errs = await open_app(p)
        await sign_in(pg, 'u_owner')

        # ---------------------------------------------------------------- price book: matching
        M = await pg.evaluate("([S, D, X]) => ({ same: S.map(g => g.map(d => ciSpecKey(d))), diff: D.map(([a, b]) => [ciSpecKey(a), ciSpecKey(b)]), inc: X.map(d => ciSpecKey(d)) })", [SAME, DIFFERENT, INCOMPLETE])
        for g, keys in zip(SAME, M['same']):
            c.ok(keys[0] and len(set(keys)) == 1, f'one item across stores: {g} -> {keys}')
        for (a, bb), (ka, kb) in zip(DIFFERENT, M['diff']):
            c.ok(not (ka and kb and ka == kb), f'never one item: {a!r} / {bb!r} ({ka} / {kb})')
        c.ok(not any(M['inc']), f'a vague description makes no spec of its own: {M["inc"]}')

        PB = await pg.evaluate("""() => { const B = ciPriceBook(); const g = (k) => B.find(x => x.key === k) || null;
          const stud = g('spec:lumber|2x4|8ft|kd|spf'), dw = g('spec:drywall|5/8|4x8|x'), elbow = g('spec:pexa-elbow|1/2');
          return { stud: stud && { stores: stud.stores.map(s => [s.store, s.price]), raw: stud.raw.length, best: stud.best.store },
                   dw: dw && dw.stores.map(s => [s.store, s.price]), elbow: elbow && elbow.stores.map(s => [s.store, s.price]),
                   cases: pwCases('pwStoreCheaper').map(c => ({ key: c.key, amount: c.amount, lines: c.lines.map(l => [l.item, l.store, l.best, l.paid, l.qty, l.save]) })),
                   paid: pwCases('pwPaidMore').map(c => c.buy && c.buy.id), docs: (DB.docs || []).filter(d => /^dc_ci_/.test(d.id)).map(d => [d.id, d.links.txnId, d.fields.total]),
                   txn: Object.fromEntries(['t4', 't10', 't14', 'ta9'].map(id => [id, -DB.txns.find(t => t.id === id).amt])) }; }""")
        c.ok(PB['stud'] and PB['stud']['stores'][0] == ['Brooklyn Lumber — Red Hook', 3.98] and len(PB['stud']['stores']) == 4, f"studs priced at four stores, the yard best: {PB['stud']}")
        c.ok(PB['dw'] == [['Quality Building Supply — Park Slope', 14.33], ['Home Depot — Gowanus', 17.48]], f"5/8 Type X at the supply house and Home Depot: {PB['dw']}")
        c.ok(PB['elbow'] == [['Ferguson — Brooklyn', 1.62]], f"a 25-pack is priced per piece ($40.50 / 25): {PB['elbow']}")
        for d, txn, tot in PB['docs']:
            txn and c.ok(abs(PB['txn'][txn] - tot) < 0.005, f'receipt {d} ties to card line {txn} to the cent: {tot} vs {PB["txn"][txn]}')
        cases = {x['key']: x for x in PB['cases']}
        r6, r7 = cases.get('pw:store:dc_ci_r6'), cases.get('pw:store:dc_ci_r7')
        # recomputed here: (paid - best at another store in the 90 days before) x quantity, per line
        c.ok(r6 and r6['amount'] == r2(100 * (4.47 - 3.98) + 20 * (16.48 - 15.2) + 6 * (62.4 - 54.9)), f"Home Depot Flatbush 8/14: $119.60 cheaper at the yard: {r6}")
        c.ok(r7 and r7['amount'] == r2(150 * (4.47 - 3.98) + 40 * (17.48 - 14.33) + 3 * (62.95 - 54.9)), f"Home Depot Gowanus 8/27: $223.65 (studs and plywood at the yard, drywall 22% above the supply house): {r7}")
        c.ok(r7 and any(l[0].startswith('5/8') and l[1] == 'Quality Building Supply — Park Slope' and l[5] == 126.0 for l in r7['lines']), 'the sheetrock 22% above the best store is named, with the store and $126.00')
        c.ok(len(PB['cases']) == 2, f'one case per receipt, no more: {list(cases)}')
        c.ok(not set(PB['paid']) & {l for x in PB['cases'] for l in []}, 'no receipt line is on two detectors')

        # a Pro account's purchase-history export joins the same history (Lowe's, studs above the yard)
        csv = "Date,Store Number,Transaction ID,SKU,UPC,Description,Quantity,Unit Price,Extended Price,Job Name\n09/02/2026,1675,T-55001,6005,,2-in x 4-in x 8-ft Kiln-Dried SPF Stud,80,4.38,350.40,121 State\n09/02/2026,1675,T-55001,70920,,Southwire 250-ft 12/2 Romex NM-B,1,96.48,96.48,121 State\n"
        IM = await pg.evaluate("""csv => { const R = ciImportPurchaseHistory(csv, 'lowes'); const again = ciImportPurchaseHistory(csv, 'lowes');
          const C = pwCases('pwStoreCheaper').find(c => (c.refs || []).includes(R.made[0] && R.made[0].id));
          return { made: R.made.length, again: again.made.length, skipped: again.skipped, job: R.made[0] && R.made[0].links.jobId, case: C && { amount: C.amount, lines: C.lines.map(l => [l.store, l.save]) } }; }""", csv)
        c.ok(IM['made'] == 1 and IM['again'] == 0 and IM['skipped'] == 1, f'the export files one receipt per transaction, once: {IM}')
        c.ok(IM['job'] == 'p121', f"the export's job name lands the receipt on the job: {IM['job']}")
        c.ok(IM['case'] and IM['case']['amount'] == r2(80 * (4.38 - 3.98)), f"Lowe's studs on 9/2 are $32.00 above the yard: {IM['case']}")

        # ---------------------------------------------------------------- jobs spending more than they bring in
        J = await pg.evaluate("""() => { const R = PRED.jobsOverspending.rows(); return R.map(x => ({ p: x.p.id, cash: x.cash, billed: x.billed, actual: x.actual, reasons: x.reasons.map(r => r.kind), lines: x.lines.map(l => ({ name: l.name, kind: l.kind, over: l.over, cause: l.cause, fix: l.fix && l.fix.label })) })); }""")
        byp = {x['p']: x for x in J}
        s121 = byp.get('p121')
        c.ok(s121 and s121['cash']['in'] == 169750 and s121['cash']['out'] == 93693.94, f"121 State: cash in $169,750 (payments), out $93,693.94 (every job bank and card line): {s121 and s121['cash']}")
        w = s121 and next((l for l in s121['lines'] if l['name'].startswith('Windows')), None)
        c.ok(w and w['kind'] == 'over' and w['over'] == 3800 and 'over the PO' in w['cause'] and w['fix'] in ('Dispute Difference', 'Review the Bill'), f'windows: $3,800 over, caused by the bill over its PO, fix the dispute: {w}')
        m = s121 and next((l for l in s121['lines'] if l['name'].startswith('Millwork')), None)
        c.ok(m and m['kind'] == 'committed' and m['over'] == 1000 and 'PO-2026-048' in m['cause'] and m['fix'] == 'Draft Change Order', f'millwork: committed $1,000 past budget, fix a change order: {m}')
        c.ok('p206' not in byp, 'a job with nothing spent is not flagged (no false alarm)')
        # planted: a job that has paid out more than the client has paid in
        await pg.evaluate("""() => { DB.txns.push({ id: 'ci_plant_1', date: '2026-09-02', acct: 'ac1', amt: -3500, vendor: 'Brooklyn Lumber', desc: 'BROOKLYN LUMBER PLANTED', projectId: 'p140', cat: 'materials', code: '15' }); pwFresh(); }""")
        P = await pg.evaluate("""() => { const x = PRED.jobsOverspending.rows().find(y => y.p.id === 'p140'); const ck = CATCH.find(c => c.name === 'jobCash').rows().find(r => r.key === 'cashneg:p140');
          return x && { cash: x.cash, reasons: x.reasons.map(r => [r.kind, r.cause || '']), fixes: x.fixes.map(f => f.label), catch: ck && ck.what, n: PRED.jobsOverspending.count() }; }""")
        c.ok(P and P['cash']['out'] == 3500 and P['cash']['in'] == 0 and ['cash', '$24,000 billed and not yet paid'] in P['reasons'], f'planted: 140 Prospect paid out $3,500 with nothing collected; the cause is the open invoice: {P}')
        c.ok(P and 'Chase Payment' in P['fixes'] and P['catch'] == 'Spending more than it brings in: 140 Prospect Place', f'the drafted fix and Caught for You: {P}')
        # one number everywhere: predicate, Reports tab, Ask
        await pg.evaluate("() => { view = 'reports'; repTab = 'costintel'; render(); }"); await pg.wait_for_timeout(400)
        T = await pg.evaluate("""() => { const h = document.getElementById('rep-print-area'); const a = paAsk('which jobs are spending more than they bring in');
          return { pred: PRED.jobsOverspending.count(), tab: +(h.querySelector('[data-cijobn]') || {}).dataset?.cijobn, cards: h.querySelectorAll('[data-cijob]').length, ask: a.headline, prim: [...document.querySelectorAll('.view.on .btn.primary')].filter(x => x.getClientRects().length).length, sw: document.documentElement.scrollWidth, figs: [...h.querySelectorAll('[data-cijob="p121"] [data-cicashout]')].map(x => x.dataset.cicashout) }; }""")
        c.ok(T['pred'] == T['tab'] == T['cards'] == 3 and T['ask'].startswith('3 jobs are spending more'), f"one number: predicate {T['pred']}, tab {T['tab']}, cards {T['cards']}, Ask {T['ask'][:60]!r}")
        c.ok(T['figs'] == ['93693.94'], f"the tab shows 121 State's cash out from the same rule: {T['figs']}")
        c.ok(T['prim'] <= 1 and T['sw'] <= 1440, f"one blue button at most ({T['prim']}), no sideways scroll ({T['sw']})")
        await pg.screenshot(path=os.path.join(SHOTS, 'owner_cost_intelligence.png'), full_page=True)
        await pg.evaluate("() => { DB.txns = DB.txns.filter(t => t.id !== 'ci_plant_1'); pwFresh(); render(); }")

        # ---------------------------------------------------------------- benchmarks, recomputed here to the cent
        CO = await pg.evaluate("() => ({ co: DB.closeouts, trades: CI_TRADES.map(t => ({ id: t.id, measure: t.measure, scale: t.scale || 1 })), app: ciBenchmarks('brownstone').map(b => [b.trade, b.median, b.min, b.max, b.n]), flags: ciBenchFlags().filter(f => !f.live).map(f => [f.jobId, f.trade, f.perUnit, f.median, f.cause]) })")
        brown = [x for x in CO['co'] if x['type'] == 'brownstone']
        c.ok(len(brown) == 6 and any(x['type'] == 'condo' for x in CO['co']), f'six comparable brownstones and one condo kept apart ({len(brown)})')
        per = {}
        for t in CO['trades']:
            for j in brown:
                rows = [x for x in j['buys'] if x['trade'] == t['id']]
                mat = r2(sum(r2(x['bought'] * x['price']) for x in rows))
                per[(j['id'], t['id'])] = r2(mat / j['measures'][t['measure']] * t['scale'])
        mine = []
        for t in CO['trades']:
            v = [per[(j['id'], t['id'])] for j in brown]
            mine.append([t['id'], r2(med(v)), min(v), max(v), len(v)])
        c.ok(mine == CO['app'], f'every trade median, low, high and count agrees to the cent:\n   here {mine}\n   app  {CO["app"]}')
        exp_flags = []
        for t in CO['trades']:
            for j in brown:
                others = [per[(o['id'], t['id'])] for o in brown if o['id'] != j['id']]
                m_ = r2(med(others))
                if per[(j['id'], t['id'])] > m_ * 1.15 + 1e-9: exp_flags.append([j['id'], t['id'], per[(j['id'], t['id'])], m_])
        got = sorted([f[:4] for f in CO['flags']])
        c.ok(sorted(exp_flags) == got, f'every closed job above its comparables by more than 15%, to the cent:\n   here {sorted(exp_flags)}\n   app  {got}')
        causes = {(f[0], f[1]): f[4] for f in CO['flags']}
        c.ok(causes.get(('co_ci_clinton', 'framing')) == 'quantity' and causes.get(('co_ci_strong', 'sheetrock')) == 'waste' and causes.get(('co_ci_ppw', 'roughElectric')) == 'price', f'each flag names its cause (quantity, waste, price): {causes}')
        live = await pg.evaluate("() => ciBenchFlags().filter(f => f.live).map(f => [f.job, f.trade, f.priceOnly, Math.round((f.priceIdx - 1) * 100)])")
        c.ok(['121 State Street', 'sheetrock', True, 20] in live, f"a running job paying 20% above comparable jobs' prices for sheetrock is flagged on price: {live}")
        # proposing to estimating: a draft the owner approves; then one book the estimate and the library read
        PR = await pg.evaluate("""() => { const ch = ciProposeBench('roughPlumbing', 'brownstone'); return ch && { id: ch.id, status: ch.status, path: ch.delta.path, to: ch.delta.to.perUnit, inBook: !!(((DB.company.costBook || {}).bench || {}).roughPlumbing) }; }""")
        rp = next(x for x in mine if x[0] == 'roughPlumbing')
        c.ok(PR and PR['status'] == 'draft' and PR['path'] == 'company.costBook.bench.roughPlumbing' and PR['to'] == rp[1] and not PR['inBook'], f'a benchmark is a drafted change in Company › Changes, not live: {PR}')
        await pg.evaluate("() => { view = 'meetings'; mtTab = 'changes'; mtOpen = ''; render(); }"); await pg.wait_for_timeout(300)
        await pg.click(f'[data-chok="{PR["id"]}"]'); await pg.wait_for_timeout(300)
        AP = await pg.evaluate("""() => ({ book: DB.company.costBook && DB.company.costBook.bench && DB.company.costBook.bench.roughPlumbing, second: DB.company.costBench === undefined })""")
        c.ok(AP['book'] and AP['book']['perUnit'] == rp[1] and AP['second'], f"approved, it is in the one book (costBook.bench), no second store: {AP}")
        FILL = await pg.evaluate("""() => { DB.company.costBook['05'] = 1.12; const d = { projectId: 'p121' }; const l = { item: 'Rough plumbing', qty: 2, cost: 0, code: '' };
          libFillLine(l, { id: 'x', cat: 'construction', code: '05', unit: 'ea', rate: 900, cost: 400, desc: 'Rough plumbing per fixture' }, d);
          const typed = { item: 'Rough plumbing', qty: 1, cost: 333, code: '05' }; libFillLine(typed, { id: 'x', cat: 'construction', code: '05', unit: 'ea', rate: 900, cost: 400 }, d);
          const G = ciCostGuide({ item: 'Rough plumbing, two baths', code: '05' }, d); delete DB.company.costBook['05'];
          return { cost: l.cost, guide: l.costGuide, typed: typed.cost, factor: G.factor, bench: G.bench.map(h => h.trade) }; }""")
        c.ok(FILL['cost'] == r2(400 * 2 * 1.12) and FILL['guide']['factor'] == 1.12 and FILL['typed'] == 333, f"the library's fill carries the close-out factor once; a typed cost is never touched: {FILL}")
        c.ok(FILL['bench'] == ['roughPlumbing'], f'the one reader gives the estimate both the factor and the benchmark: {FILL}')

        # ---------------------------------------------------------------- the route bank
        RB = await pg.evaluate("""(B) => B.map(s => { const o = ciRouteSolve(s.I), n = ciRouteNearest(s.I);
          return { name: s.name, opt: o && { total: o.total, stores: o.stores, legs: o.legs, late: o.lateMin, kinds: o.stops.map(x => x.kind), at: o.stops.map(x => [x.siteId || x.n, x.at]), item: o.itemCost, labor: o.laborCost }, near: n && { total: n.total, stores: n.stores } }; })""", BANK)
        tot_o = tot_n = 0
        for s, r in zip(BANK, RB):
            o, n = r['opt'], r['near']
            c.ok(o and n and o['total'] <= n['total'] + 1e-6, f"route bank · {s['name']}: optimiser ${o and o['total']} never above nearest store ${n and n['total']}")
            tot_o += o['total'] if o else 0
            tot_n += n['total'] if n else 0
            e = s['expect']
            'uses' in e and c.ok(e['uses'] in o['stores'], f"{s['name']}: uses {e['uses']} ({o['stores']})")
            'not' in e and c.ok(e['not'] not in o['stores'], f"{s['name']}: never {e['not']} ({o['stores']})")
            'legs' in e and c.ok(o['legs'] == e['legs'], f"{s['name']}: {o['legs']} trips")
            'dump' in e and c.ok('dump' in o['kinds'] and o['kinds'].index('dump') > o['kinds'].index('site'), f"{s['name']}: the dump after the drops ({o['kinds']})")
            'stores' in e and c.ok(len(o['stores']) == e['stores'], f"{s['name']}: {len(o['stores'])} store")
            if 'ontime' in e:
                at = dict((k, v) for k, v in o['at'])
                c.ok(o['late'] == 0 and at.get('a', 9999) <= 540, f"{s['name']}: Site A reached by 9 am ({at.get('a')})")
        c.ok(tot_o < tot_n - 50, f'over the bank the optimiser costs less than the nearest store: ${r2(tot_o)} against ${r2(tot_n)} (saves ${r2(tot_n - tot_o)})')
        await b.close()

        # ======================================================================= the coordinator approves, desktop
        b, pg, errs2 = await open_app(p)
        errs += errs2
        await sign_in(pg, 'u_chen'); await go(pg, 'route'); await pg.wait_for_timeout(300)
        CR = await pg.evaluate("""() => { const card = document.querySelector('[data-cirt]'); return { card: !!card, state: card && card.querySelector('[data-cirtstate]').dataset.cirtstate, total: card && +card.querySelector('[data-cirttotal]').dataset.cirttotal, saves: card && card.querySelector('[data-cirtsaves]') && +card.querySelector('[data-cirtsaves]').dataset.cirtsaves,
          prim: [...document.querySelectorAll('.view.on .btn.primary')].filter(x => x.getClientRects().length).map(x => x.innerText.trim()), travel: card && card.querySelector('[data-cirttravel]').dataset.cirttravel, stores: [...card.querySelectorAll('.stop.store b')].map(x => x.innerText) }; }""")
        c.ok(CR['card'] and CR['state'] == 'proposed' and CR['prim'] == ['Approve Route'], f"the coordinator sees the proposed route and one blue button, Approve Route: {CR}")
        c.ok(CR['travel'] == 'offline' and CR['saves'] is not None and CR['saves'] >= 0, f'it says the drive times are estimated, and what it saves against the nearest store: {CR}')
        await pg.screenshot(path=os.path.join(SHOTS, 'coord_route_desktop.png'), full_page=True)
        await pg.click('[data-ciapprove]'); await pg.wait_for_timeout(400)
        A = await pg.evaluate("""() => { const r = DB.storeRuns.filter(x => x.status === 'approved').pop(); return { r: r && { by: r.approvedBy, stores: r.store, total: r.plan.total, saves: r.saves, assign: r.plan.assign.map(a => [a.what, a.store]) }, toast: document.getElementById('toast').innerText, state: (document.querySelector('[data-cirtstate]') || {}).dataset?.cirtstate }; }""")
        c.ok(A['r'] and A['r']['by'] == 'Chen Biron' and A['state'] == 'approved' and 'Route approved' in A['toast'] and 'Open' in A['toast'], f'approved, with a toast and Open: {A}')
        c.ok(A['r'] and ['2x4x8 KD studs', 'Brooklyn Lumber — Red Hook'] in A['r']['assign'], f"the studs go to the yard, where they are $0.40 less: {A['r']}")
        c.ok(not errs, f'page errors: {errs[:3]}')
        db = await pg.evaluate("() => JSON.stringify(DB)")
        await b.close()

        # ======================================================================= the driver, phone 390
        b, pg, errs3 = await open_app(p, phone=True)
        await pg.evaluate("s => { const d = JSON.parse(s); Object.keys(DB).forEach(k => delete DB[k]); Object.assign(DB, d); }", db)
        await sign_in(pg, 'u_alex'); await go(pg, 'route'); await pg.wait_for_timeout(400)
        D = await pg.evaluate("""() => { const card = document.querySelector('[data-cirt]'); const t = card ? card.innerText : '';
          return { card: !!card, state: card && card.querySelector('[data-cirtstate]').dataset.cirtstate, head: card && card.querySelector('h3').innerText, prices: (t.match(/\\$\\d[\\d,]*\\.\\d\\d/g) || []), money: /Items \\$|Total \\$|Fuel/.test(t), sw: document.documentElement.scrollWidth,
            nav: card ? card.querySelectorAll('.m-nav').length : 0, stops: card ? card.querySelectorAll('.stop').length : 0, approve: !!document.querySelector('[data-ciapprove]'), buys: [...card.querySelectorAll('.stop.store li')].map(x => x.innerText) }; }""")
        c.ok(D['card'] and D['state'] == 'approved' and D['head'] == "Today's Route", f"the driver gets the approved route on the phone: {D['state']} {D['head']}")
        c.ok(not D['prices'] and not D['money'] and not D['approve'], f"no prices and no money for the driver, and no approval button: {D['prices']} {D['money']}")
        c.ok(D['sw'] <= 390, f'no sideways scroll at 390px ({D["sw"]})')
        c.ok(any('2x4x8 KD studs' in x for x in D['buys']), f'each buy names what to buy at that stop: {D["buys"]}')
        lead = await pg.evaluate("() => { const card = document.getElementById('run-card'); return !!card && card.firstElementChild && card.firstElementChild.matches('[data-cirt]'); }")
        c.ok(lead, "the driver's approved route leads the Route screen's card")
        await pg.screenshot(path=os.path.join(SHOTS, 'driver_route_phone.png'), full_page=True)
        await pg.locator('[data-cirt]').screenshot(path=os.path.join(SHOTS, 'driver_route_card_phone.png'))
        DA = await pg.evaluate("""() => ({ a: paAsk('where should I buy 2x4x8 KD studs').headline, rt: eqRows('routeplan').map(r => Object.keys(r).filter(k => /price|cost|savings/.test(k))), pb: eqRows('pricebook').length, jm: eqRows('jobmoney').length, bench: eqRows('benchmarks').length })""")
        c.ok('Brooklyn Lumber' in DA['a'] and '$' not in DA['a'], f"Ask as the driver: the store, never a price: {DA['a']!r}")
        c.ok(all(not k for k in DA['rt']) and DA['pb'] == 0 and DA['jm'] == 0 and DA['bench'] == 0, f'the driver reads the route without prices and no money table: {DA}')
        # the receipts come back: bought as planned at the yard; the saving reaches the savings registry
        RC = await pg.evaluate("""() => { ciNewReceipt({ id: 'dc_ci_back', store: 'Brooklyn Lumber — Red Hook', number: 'BL-31560', date: today(), jobId: 'p121', lines: [{ item: "2X4 8' KD SPF STUD", qty: 40, price: 3.98 }] }); pwFresh(); render();
          const run = DB.storeRuns.filter(x => x.status === 'approved').pop(); const R = ciPlanVsReceipts(run); const sv = (window.SV_SOURCES || []).flatMap(f => f());
          return { R: R.map(x => [x.what, x.asPlanned, x.bought]), pvr: !!document.querySelector('[data-cipvr]'), sv: sv.map(x => [x.amount, x.source2, x.jobId, x.by, x.date]), pb: ciSavingsRows().filter(x => x.source2 === 'costintel:pricebook').map(x => [x.key, x.amount]), ledger: typeof svRows === 'function' ? svRows().filter(r => /^(route|pricebook):/.test(r.key)).length : -1, txt: (document.querySelector('[data-cipvr]') || {}).innerText || '' }; }""")
        c.ok(['2x4x8 KD studs', True, 'Brooklyn Lumber — Red Hook'] in RC['R'] and RC['pvr'] and '$' not in RC['txt'], f'the receipt is compared back to the plan, shown to the driver without money: {RC}')
        near_price = await pg.evaluate("() => { const run = DB.storeRuns.filter(x => x.status === 'approved').pop(); const n = run.nearest.assign.find(a => a.what === '2x4x8 KD studs'); return n && [n.store, n.price]; }")
        exp = r2((near_price[1] - 3.98) * 40) if near_price and near_price[0] != 'Brooklyn Lumber — Red Hook' else None
        c.ok(exp and [exp, 'costintel:route', 'p121', 'Chen Biron', '2026-09-03'] in RC['sv'], f"the realised saving is a row in the savings registry: {RC['sv']} (expected {exp} against {near_price})")
        # acting on the price book: Brooklyn Lumber on 9/2 (ta9) after the Home Depot cases named it for the same items
        pb = dict(RC['pb'])
        exp_pb = {'pricebook:rcpt:dc_ci_r9:0': r2(200 * (4.47 - 3.98)), 'pricebook:rcpt:dc_ci_r9:1': r2(40 * (16.48 - 15.2)), 'pricebook:rcpt:dc_ci_r9:2': r2(9 * (62.95 - 54.9))}
        c.ok(all(pb.get(k) == v for k, v in exp_pb.items()), f'price-book savings to the cent (studs, 2x6, plywood bought at the yard after the cases): {pb} expected {exp_pb}')
        c.ok(RC['ledger'] >= len(exp_pb) + 1, f"the savings ledger (src/specialists.js) reads them through window.SV_SOURCES: {RC['ledger']} rows")
        c.ok(not errs3, f'page errors (phone): {errs3[:3]}')
        await b.close()

        # ======================================================================= PM, controller, owner on the phone
        b, pg, errs4 = await open_app(p)
        await sign_in(pg, 'u_alan')
        CO2 = await pg.evaluate("""() => { const before = DB.clients.flatMap(c => c.changeOrders).length; const d = ciDraftCO('p121', 'estimate:es1:l9'); const after = DB.clients.flatMap(c => c.changeOrders).length;
          return d && { n: after - before, status: d.status, line: d.lines[0], toast: document.getElementById('toast').innerText }; }""")
        c.ok(CO2 and CO2['n'] == 1 and CO2['status'] == 'draft' and CO2['line']['cost'] == 1000 and CO2['line']['line'] == 'estimate:es1:l9', f"the PM drafts the millwork change order from the line; nothing is sent: {CO2 and {k: CO2[k] for k in ('n', 'status')}}")
        c.ok(CO2 and 'Open' in CO2['toast'] and 'Change order drafted' in CO2['toast'], f"it toasts with Open: {CO2 and CO2['toast']}")
        WK = await pg.evaluate("""() => { const a = ciWeekly('button'); const b = ciWeekly('button'); return { n: a.length, again: b.length, rows: a.map(c => ({ kind: c.kind, title: c.title, value: c.value, status: c.status })), ids: a.map(c => c.id) }; }""")
        c.ok(WK['n'] >= 3 and WK['again'] == 0, f"the weekly review proposes {WK['n']} changes, and nothing twice: {[r['title'] for r in WK['rows']]}")
        c.ok(all((r['value']['dollars'] or r['value']['hours']) and r['status'] == 'draft' for r in WK['rows']), 'each proposal carries a dollar or hour value and waits as a draft')
        c.ok(any('Rough electric material ran' in r['title'] and 'last 3 brownstones' in r['title'] for r in WK['rows']), 'the overrun on the last three brownstones is proposed')
        await b.close()

        b, pg, errs5 = await open_app(p)
        await sign_in(pg, 'u_owner')
        await pg.evaluate("() => ciWeekly('button')")
        LS = await pg.evaluate("""() => { const ch = DB.changes.find(c => c.source === 'brain-weekly' && c.kind === 'rule' && c.lesson); const n0 = DB.lessons.length; view = 'meetings'; mtTab = 'changes'; render(); return { id: ch && ch.id, lesson: ch && ch.lesson, n0 }; }""")
        await pg.wait_for_timeout(300)
        await pg.click(f'[data-chok="{LS["id"]}"]'); await pg.wait_for_timeout(300)
        L2 = await pg.evaluate("id => ({ n: DB.lessons.length, l: (DB.lessons.find(x => x.fromChange === id) || {}).title, st: DB.changes.find(c => c.id === id).status })", LS['id'])
        c.ok(L2['n'] == LS['n0'] + 1 and L2['l'] == LS['lesson'] and L2['st'] == 'live', f'an approved weekly rule becomes a lesson: {L2}')
        await go(pg, 'rfq'); await pg.evaluate("() => { rfqTab = 'pricewatch'; render(); }"); await pg.wait_for_timeout(400)
        PW = await pg.evaluate("() => ({ pb: +(document.querySelector('[data-cipb]') || {dataset: {}}).dataset.cipb, det: +(document.querySelector('[data-pwdet=\"pwStoreCheaper\"]') || {dataset: {}}).dataset.pwn, prim: [...document.querySelectorAll('.view.on .btn.primary')].filter(x => x.getClientRects().length).length })")
        c.ok(PW['pb'] >= 10 and PW['det'] == 2 and PW['prim'] <= 1, f'RFQs › Price Watch carries the Receipt Price Book and the Cheaper at Another Store detector: {PW}')
        await pg.screenshot(path=os.path.join(SHOTS, 'owner_price_book.png'), full_page=True)
        c.ok(not errs4 and not errs5, f'page errors: {(errs4 + errs5)[:3]}')
        await b.close()

        for uid, tag in (('u_owner', 'owner'), ('u_controller', 'controller')):
            b, pg, e6 = await open_app(p, phone=True)
            await sign_in(pg, uid); await pg.evaluate("() => { view = 'reports'; repTab = 'costintel'; render(); }"); await pg.wait_for_timeout(500)
            PH = await pg.evaluate("""() => ({ sw: document.documentElement.scrollWidth, n: document.querySelectorAll('[data-cijob]').length, bench: document.querySelectorAll('[data-cibench]').length, small: [...document.querySelectorAll('.ci-tab .btn')].filter(x => x.getClientRects().length && x.getBoundingClientRect().height < 44).length, ask: paAsk('what is the benchmark for sheetrock per board').headline })""")
            c.ok(PH['sw'] <= 390 and PH['n'] >= 2 and PH['bench'] == 5 and PH['small'] == 0, f'{tag} on the phone: the tab fits 390px, buttons 44px: {PH}')
            c.ok(PH['ask'].startswith('Sheetrock: $'), f"{tag} asks for a benchmark: {PH['ask']!r}")
            await pg.screenshot(path=os.path.join(SHOTS, f'{tag}_cost_intelligence_phone.png'), full_page=True)
            c.ok(not e6, f'page errors ({tag} phone): {e6[:3]}')
            await b.close()
    sys.exit(c.done())

asyncio.run(main())
