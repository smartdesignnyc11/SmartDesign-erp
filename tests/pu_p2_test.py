"""pu_p2_test: lane P2 of the purchasing push (11-05). Each check starts from how the coordinator expert, the field
expert or the screen capture saw it fail (scratchpad pu_review/coord, field, existing):

  bar       the Buy Board's pick bar adds the figures its picked rows show (rows read $21,500 and $75,000, the bar
            "$19,850 priced"), and says how many picked rows have no price; Needs You equals its rows and the badge
  commit    one commitment per line (lineCommitment): after a draft PO-049 of $13,900 on Demolition, the order sheet,
            the Buy Board, Client Funds and the panel say the same left ($5,950) for three lines; the sheet fills in
            what is left, never the whole budget; the one budget test (lineBudgetTest, actual included) stops Windows
            ($0 left); a second subcontract order on a line asks for a reason; the job's Orders shows Over the Line
  request   an order on a line covers the field request on it: the studs leave the store run (path order) and the PO
            line names the studs
  docs      only approved estimates and change orders are bought from (no draft estimate on the sheet or its door)
  status    one status per need (puNeedStatus): a draft RFQ is the coordinator's, not "waiting on the vendors"; Today's
            Buy Board card says what the board's row says
  item      stock and price history keyed on the item: the drywall panel's shop agrees with its row, its last buys are
            not the insulation's $52/bag; the stock gate's blue is Use the Stock, Buy the Rest; a price above the best
            known is flagged on the order sheet; unit prices keep their cents ($4.60, not $5)
  split     Set the Material Portion opens its one-field sheet, and the PM has it in Approvals
  ffe       FF&E Buying Tools is headed as its button reads; its tabs stay Title Case after a tap; New Buy Run is blue
            only with something ticked, and then opens the buy run
  door      the estimate's Buy These Lines: tick one or several lines on the document (phone too), one blue, then the
            same order sheet with those lines ticked
  phone     the order sheet from lines on the phone: cards, nothing sideways, the item in full, a full-width vendor,
            44px inputs, the pre-ticked line still ticked
Usage: python3 pu_p2_test.py [--only bar,commit,...]"""
import asyncio, re, sys
from harness import *

ONLY = sys.argv[sys.argv.index('--only') + 1].split(',') if '--only' in sys.argv else None
want = lambda k: not ONLY or k in ONLY
L1, L2, L3, L7 = 'estimate:es1:l1', 'estimate:es1:l2', 'estimate:es1:l3', 'estimate:es1:l7'

async def board(pg):
    await pg.evaluate("() => { procMode = 'lines'; procPane = 'board'; bbProj = ''; bbVendor = ''; bbTrade = ''; bbPick.clear(); view = 'proc'; render(); }")
    await pg.wait_for_timeout(300)

async def sheet(pg, keys, doc='es1'):
    await pg.evaluate("([k, d]) => { mbCloseModal(); ctPOPicker('p121', d, k); }", [keys, doc])
    await pg.wait_for_timeout(400)

ROW = """k => { const tr = document.querySelector(`#mbm tr[data-pukey="${k}"]`); if (!tr) return null;
  const q = s => tr.querySelector(s); return { text: tr.innerText, on: q('[data-ctpsel]').checked, cost: (q('[data-ctpc]') || {}).value,
  note: (q('[data-puctpn]') || {}).innerText || '', req: [...tr.querySelectorAll('[data-ctpreq]')].map(i => ({ id: i.value, on: i.checked })) }; }"""

async def fill(pg, k, cost=None, vendor=None, tick=True):
    await pg.evaluate("""([k, cost, vendor, tick]) => { const tr = document.querySelector(`#mbm tr[data-pukey="${k}"]`); const cb = tr.querySelector('[data-ctpsel]');
      if (cb.checked !== tick) cb.click();
      const set = (s, v) => { const i = tr.querySelector(s); if (i && v !== null) { i.value = v; i.dispatchEvent(new Event('input', { bubbles: true })); } };
      set('[data-ctpc]', cost); set('[data-ctpv]', vendor); }""", [k, cost, vendor, tick])
    await pg.wait_for_timeout(150)

async def closeall(pg):
    """close every sheet as a person would (Cancel), including one a confirm held aside"""
    for _ in range(4):
        n = await pg.evaluate("() => { const m = document.querySelector('#mbm'); if (!m) return 0; const c = m.querySelector('#mbm-cancel'); c ? c.click() : mbCloseModal(); return 1; }")
        await pg.wait_for_timeout(250)
        if not n and not await pg.evaluate("() => !!document.querySelector('#mbm, #mbm-held')"): return

async def okb(pg):
    """the sheet's own blue button, as a person taps it"""
    n = await pg.evaluate("() => document.querySelectorAll('#mbm-ok').length")
    if n != 1: print('note: #mbm-ok count', n)
    await pg.locator('#mbm-ok').locator('visible=true').last.click(timeout=8000)

MODAL = "() => { const m = document.querySelector('#mbm'); return m && m.getClientRects().length ? { title: (m.querySelector('.mbm-hd h3') || {}).innerText || '', text: m.innerText, ok: (m.querySelector('#mbm-ok') || {}).innerText || '' } : null; }"

async def desktop(c, p):
    b, pg, errs = await open_app(p, False)
    try:
        await sign_in(pg, 'u_chen')
        vend = await pg.evaluate("() => (DB.vendors.find(v => /Kent Avenue|Ferguson/.test(v.name)) || DB.vendors[0]).name")
        if want('bar'):
            await board(pg)
            await pg.evaluate("() => { buyList('').filter(r => /^(\\d+\\. )?Demolition/.test(r.name) || /^Parlor kitchen countertop/.test(r.name)).forEach(r => bbPick.add(r.id)); render(); }")
            await pg.wait_for_timeout(300)
            B = await pg.evaluate("""() => { const bar = document.querySelector('#buy-board [data-pubar]'); const rows = [...bbPick].map(id => document.querySelector(`#buy-board [data-purow="${id}"]`)).filter(Boolean);
              return { bar: bar ? +bar.dataset.pubar : null, none: bar ? +bar.dataset.punoprice : null, text: bar ? bar.parentElement.innerText : '', n: rows.length,
                sum: rows.reduce((a, r) => a + (+r.dataset.puamt || 0), 0), zero: rows.filter(r => !(+r.dataset.puamt > 0)).length,
                shown: rows.map(r => [+r.dataset.puamt, r.innerText]) }; }""")
            c.ok(B['n'] == 2 and B['bar'] is not None and abs(B['bar'] - B['sum']) < 0.01, f"bar: the pick bar's total is the sum of the picked rows' figures ({B['bar']} vs {B['sum']})")
            c.ok(B['none'] == B['zero'] == 1 and 'with no price yet' in B['text'], f"bar: the bar names the picked line with no price ({B['text']})")
            c.ok(all((not a) or (re.sub(r'\.00$', '', f"${a:,.2f}") in t) for a, t in B['shown']), f"bar: each picked row shows the figure the bar adds {B['shown']}")
            N = await pg.evaluate("() => { const v = document.querySelector('#v-proc'); const n = v.querySelector('[data-pusec=\"mine\"] .pu-sh .n'); return { n: n ? +n.innerText : 0, rows: v.querySelectorAll('[data-pusec=\"mine\"] [data-purow]').length, badge: puCount('proc') }; }")
            c.ok(N['n'] == N['rows'] == N['badge'], f'bar: Needs You is its rows and the menu badge {N}')
            await pg.evaluate("() => { bbPick.clear(); }")
        if want('commit'):
            await sheet(pg, [L1])
            await fill(pg, L1, '13900', vend)
            await okb(pg); await pg.wait_for_timeout(500)
            m = await pg.evaluate(MODAL)
            if m and 'Confirm' in m['title']: await okb(pg); await pg.wait_for_timeout(500)
            po = await pg.evaluate("k => { const po = DB.pos.filter(p => p.status === 'draft' && p.lines.some(l => l.line === k)).pop(); return po && po.number; }", L1)
            c.ok(bool(po), f'commit: the order sheet made a draft on Demolition ({po})')
            for k in (L1, L3, L7):
                await sheet(pg, [k])
                S = await pg.evaluate(ROW, k)
                C = await pg.evaluate("k => { const c = lineCommitment(k); const f = clientFundsLedger().find(r => r.key === k); return { left: c.left, over: c.over, used: c.used, budget: c.budget, funds: f ? f.remainingToBuy : null, kind: f ? f.kind : '' }; }", k)
                lefttxt = f"${C['left']:,.0f} left" if not C['over'] else f"${C['over']:,.0f} over"
                c.ok(S and lefttxt in S['text'], f"commit: the order sheet says {lefttxt} for {k} ({S and S['text'][:160]})")
                c.ok(C['funds'] is None or C['kind'] == 'labor' or abs(C['funds'] - C['left']) < 0.01, f"commit: Client Funds' left to buy is the line's left for {k} ({C})")
                c.ok(S and (float(S['cost'] or 0) == round(C['left'], 2) or (not S['cost'] and C['left'] < 1)), f"commit: the sheet fills in what is left on {k}, not the budget (unit cost {S and S['cost']}, left {C['left']})")
            # Demolition: $5,950 left after the draft (21,500 budget - 1,650 spent - 13,900 drafted)
            c.ok(abs(await pg.evaluate("k => lineCommitment(k).left", L1) - 5950) < 0.01, 'commit: Demolition has $5,950 left after the $13,900 draft')
            # covered only by the draft: it stays on the Buy Board, in Needs You, as Issue the Draft with its order-by date (the
            # chief of staff, 11-05: the held Demolition sub dropped off the board with no order-by chase), never Ask for Bids
            P = await pg.evaluate("""k => { const r = buyList('').find(x => x.lineKey === k && !x.ordered); if (!r) return { gone: true };
              const x = puNeed(r); procMode = 'lines'; view = 'proc'; bbProj = ''; bbVendor = ''; bbTrade = ''; render(); const row = document.querySelector(`#buy-board [data-pusec="mine"] [data-purow="${r.id}"]`);
              const T = bbTodayItems().find(i => i.id === r.id); return { gone: false, b: x.b, act: x.act, orderBy: r.orderBy, when: x.when, row: row ? row.innerText : '', pick: !!(row && row.querySelector('[data-bbpick]')), today: T ? bbTodayCard(T).verb : null }; }""", L1)
            c.ok(not P['gone'] and P['b'] == 'mine' and P['act'] == 'Issue the Draft' and P['orderBy'] and 'Issue the Draft' in P['row'] and 'Order by' in P['row'] and not P['pick'],
                 f'commit: Demolition, covered only by its draft, stays in Needs You as Issue the Draft with its order-by date ({P})')
            c.ok(P.get('today') in (None, 'Issue the Draft'), f"commit: Today says Issue the Draft too ({P.get('today')})")
            # the panel of a need on a line says the line's one left
            P2 = await pg.evaluate("""() => { const r = buyList('').find(x => x.kind === 'material' && x.lineKey && !x.ordered && x.tab === 'buy'); if (!r) return null; bbSel = r.id; procMode = 'lines'; view = 'proc'; render();
              const t = (document.querySelector('#buy-board .bb-panel') || {}).innerText || ''; const c = lineCommitment(r.lineKey); return { t, left: c.left, over: c.over, name: r.name }; }""")
            want_t = f"${P2['left']:,.0f}" if P2 and not P2['over'] else (f"${P2['over']:,.0f}" if P2 else '')
            c.ok(P2 and want_t in P2['t'] and re.search(r'(Left on|Over) the line', P2['t']), f"commit: the need's panel says the line's left ({P2 and P2['name']}: {want_t})")
            # Windows: $0 left; a buy is tested with actual included
            await sheet(pg, [L3])
            await fill(pg, L3, '3300', vend)
            W = await pg.evaluate(ROW, L3)
            c.ok('Over budget' in W['note'], f"commit: ticking Windows ($0 left) says it goes over, as typed ({W['note']})")
            await okb(pg); await pg.wait_for_timeout(400)
            m = await pg.evaluate(MODAL)
            c.ok(m and 'Confirm' in m['title'] and 'over' in m['text'], f"commit: create stops at the one budget test for Windows ({m and m['text'][:160]})")
            await closeall(pg)
            T = await pg.evaluate("k => lineBudgetTest(k, 100)", L3)
            c.ok(not T['ok'] and T['by'] >= 100, f'commit: lineBudgetTest counts actual (Windows +$100 is over: {T["say"]})')
            # a second order on the demolition subcontract asks why
            await sheet(pg, [L1])
            await fill(pg, L1, '1000', vend)
            W2 = await pg.evaluate("() => { const b = document.querySelector('#mbm .pu-ctpwhy'); return b && !b.hidden ? b.innerText : null; }")
            c.ok(W2 and 'second subcontract' in W2, f'commit: ticking Demolition again shows the Why for a second subcontract order in the sheet ({W2})')
            await okb(pg); await pg.wait_for_timeout(400)
            m = await pg.evaluate(MODAL)
            n0 = await pg.evaluate("k => DB.pos.filter(p => p.lines.some(l => l.line === k)).length", L1)
            c.ok(m and 'Purchase Orders' in m['title'], f"commit: with no reason the sheet stays open, the lines kept ({m and m['title']})")
            await pg.fill('#mbm #pu-ctpwhy', 'the scope is split: the garden unit goes to a second sub')
            await okb(pg); await pg.wait_for_timeout(500)
            m = await pg.evaluate(MODAL)
            if m and 'Confirm' in m['title']: await okb(pg); await pg.wait_for_timeout(500)
            R2 = await pg.evaluate("k => { const P = DB.pos.filter(p => p.lines.some(l => l.line === k)); const po = P[P.length - 1]; return { n: P.length, why: po.secondOrderWhy || '', valid: poValid(po).filter(x => /second subcontract/.test(x)) }; }", L1)
            c.ok(R2['n'] == n0 + 1 and R2['why'] and not R2['valid'], f'commit: with the reason the second order is made and carries it ({R2})')
            await closeall(pg)
            # every path: an award that makes a second subcontract on the line is held at Issue until the reason is on the order
            AW = await pg.evaluate("""k => { const s = rfqLineSources('p121').find(x => x.key === k); const q = rfqFromLines('p121', [k]); if (!q) return null;
              const v = ensureVendor('Five Boro Wrecking', { trade: 'Demolition' }); v.kind = 'sub'; v.insuranceExp = '2027-06-30';
              q.status = 'leveled'; q.vendors = [v.id];
              q.quotes = [{ vendorId: v.id, vendor: v.name, round: 1, lines: q.lines.map(l => ({ lineId: l.id, unit: 4000, ext: 4000 })), freight: 0, lead: 5, confirmed: { by: 'test', at: appNowIso(), how: 'test' } }];
              const po = (rfqAward(q, Object.fromEntries(q.lines.map(l => [l.id, v.id]))) || [])[0]; if (!po) return { po: null };
              const before = poValid(po).filter(x => /second subcontract/.test(x)); po.secondOrderWhy = 'the scope is split: the garden unit goes to a second sub'; const after = poValid(po).filter(x => /second subcontract/.test(x));
              return { po: po.number, before, after }; }""", L1)
            c.ok(AW and AW.get('po') and AW['before'] and not AW['after'], f'commit: the award path holds a second subcontract at Issue until the reason is given ({AW})')
            # the job's Orders: Over the Line equals its rows
            await pg.evaluate("() => { view = 'po'; poOpen = null; render(); }"); await pg.wait_for_timeout(400)
            O = await pg.evaluate("""() => { const t = document.querySelector('[data-putile="lineover"]'); if (!t) return null; const v = t.querySelector('b').innerText; t.click(); return v; }""")
            await pg.wait_for_timeout(300)
            rows = await pg.evaluate("() => puOrderRows('').filter(x => x.tile === 'lineover').reduce((a, x) => a + x.money, 0)")
            c.ok(O is not None and abs(float(re.sub(r'[^\d.]', '', O) or 0) - rows) < 1, f'commit: Orders shows Over the Line ({O}) equal to its rows ({rows})')
        if want('linefin'):
            # lineFin at the root (lineCommitment reads it): a line-less bill on a multi-line order is shared by what is open
            # on each line, not taken off each whole; a card payment matched to an order with no bill is counted once; a
            # vendor credit on the order frees the line's budget (the chief of staff, 11-05)
            LF = await pg.evaluate("""() => { const k1 = 'estimate:es1:l12', k2 = 'estimate:es1:l13', v = DB.vendors[0].name;
              const mk = (lines) => { const po = { id: uid('po'), number: 'PO-TEST-' + Math.random().toString(36).slice(2, 6), projectId: 'p121', vendor: v, date: '2026-09-01', status: 'issued', lines: lines.map((x, i) => Object.assign({ id: uid('pl'), item: 'test ' + i, qty: 1, unit: 'ea', received: 0 }, x)), matchedTxns: [], tax: 0, shipping: 0 }; DB.pos.push(po); return po; };
              const c0 = [k1, k2].map(k => lineCommitment(k));
              const po = mk([{ line: k1, price: 3000 }, { line: k2, price: 1000 }]);
              const c1 = [k1, k2].map(k => lineCommitment(k));
              DB.bills.push({ id: uid('b'), number: 'TB-1', vendor: v, poId: po.id, projectId: 'p121', date: '2026-09-02', status: 'approved', lines: [{ desc: 'goods', amount: 2000 }], amount: 2000, total: 2000 });
              const c2 = [k1, k2].map(k => lineCommitment(k));
              const po2 = mk([{ line: k1, price: 500 }]); const t = { id: uid('t'), date: '2026-09-02', amt: -500, vendor: v, line: k1, acct: (DB.accounts[0] || {}).id }; DB.txns.push(t); po2.matchedTxns = [t.id];
              const c3 = lineCommitment(k1);
              const cr = { id: uid('t'), date: '2026-09-03', amt: 200, vendor: v, acct: (DB.accounts[0] || {}).id }; DB.txns.push(cr); po.matchedTxns = [cr.id];
              const c4 = lineCommitment(k1);
              return { c0: c0.map(c => [c.actual, c.committed]), c1: c1.map(c => [c.actual, c.committed]), c2: c2.map(c => [c.actual, c.committed]), c3: [c3.actual, c3.committed], c4: [c4.actual, c4.committed] }; }""")
            d1 = [round(LF['c2'][i][1] - LF['c0'][i][1], 2) for i in (0, 1)]
            c.ok(d1 == [1500, 500], f"linefin: a $2,000 bill with no line on a $3,000 + $1,000 order leaves $1,500 and $500 committed, not $1,000 and $0 ({d1}; {LF})")
            da = [round(LF['c2'][i][0] - LF['c0'][i][0], 2) for i in (0, 1)]
            c.ok(da == [1500, 500], f"linefin: the line-less bill is cost on each line by its share ({da})")
            c.ok(round(LF['c3'][0] + LF['c3'][1] - LF['c2'][0][0] - LF['c2'][0][1], 2) == 500, f"linefin: a $500 card line on an order with no bill counts once, as actual, not again as committed ({LF['c3']} after {LF['c2'][0]})")
            c.ok(round(LF['c3'][0] - LF['c4'][0], 2) == 150 and LF['c4'][0] < LF['c3'][0], f"linefin: a $200 vendor credit on the $3,000 + $1,000 order frees its share of the line ($150 of it) ({LF['c3']} -> {LF['c4']})")
        if want('preaward'):
            # long-lead lines before award: drafted with a reason, issued only with the owner's approval, flagged if lost
            PA = await pg.evaluate("""() => { const c = DB.clients.find(c => c.estimates.some(e => ['sent', 'draft'].includes(e.status) && e.lines.length > 1)); if (!c) return null;
              const d = c.estimates.find(e => ['sent', 'draft'].includes(e.status) && e.lines.length > 1); const p = DB.projects.find(x => x.clientId === c.id) || DB.projects[0];
              d.projectId = d.projectId || p.id; d.lines[0].longLead = true; save();
              const h = docActions(c, d); return { cid: c.id, id: d.id, n: d.number, pid: d.projectId, door: /data-docact="preaward"/.test(h), pos: /data-docact="pos"/.test(h) }; }""")
            c.ok(PA and PA['door'] and not PA['pos'], f'preaward: an unapproved estimate with a long-lead line offers Long-Lead Lines Before Award, not Buy These Lines ({PA})')
            if PA:
                await pg.evaluate("a => { const c = DB.clients.find(x => x.id === a.cid); docAction(c, c.estimates.find(e => e.id === a.id), 'preaward'); }", PA)
                await pg.wait_for_timeout(400)
                S = await pg.evaluate("() => [...document.querySelectorAll('#mbm [data-ctpsel]')].map(i => [i.closest('tr').dataset.pukey, i.checked, i.disabled])")
                c.ok(S and S[0][1] and all(x[2] for x in S[1:]), f'preaward: the sheet ticks the long-lead line and holds the rest ({S[:3]})')
                k0 = S[0][0] if S else ''
                await fill(pg, k0, '1200', vend)
                W3 = await pg.evaluate("() => { const b = document.querySelector('#mbm .pu-ctpwhy'); return b && !b.hidden ? b.innerText : null; }")
                c.ok(W3 and 'before' in W3, f'preaward: the sheet asks why it is bought before award ({W3})')
                await pg.fill('#mbm #pu-ctpwhy', 'the windows take 14 weeks; the client signs next week')
                await okb(pg); await pg.wait_for_timeout(500)
                m = await pg.evaluate(MODAL)
                if m and 'Confirm' in m['title']: await okb(pg); await pg.wait_for_timeout(500)
                PO = await pg.evaluate("n => { const po = DB.pos.filter(x => x.preAward && x.preAward.number === n).pop(); return po && { id: po.id, n: po.number, why: po.preAward.why, note: po.notes, v: poValid(po).filter(x => /owner approves|lost/.test(x)) }; }", PA['n'])
                c.ok(PO and PO['why'] and PO['note'].startswith('Long-Lead, Before Award') and PO['v'], f'preaward: the draft is marked Long-Lead, Before Award, with the reason, and held at Issue for the owner ({PO})')
                if PO:
                    await sign_in(pg, 'u_owner')
                    A = await pg.evaluate("id => mApprovals().some(x => x.kind === 'preaward' && x.id === id)", PO['id'])
                    c.ok(A, "preaward: it is in the owner's Approvals")
                    await pg.evaluate("id => mGo({ puPreAward: id })", PO['id']); await pg.wait_for_timeout(300)
                    await okb(pg); await pg.wait_for_timeout(300)
                    ok = await pg.evaluate("id => { const po = DB.pos.find(x => x.id === id); return { ap: !!po.preAward.approved, v: poValid(po).filter(x => /owner approves/.test(x)) }; }", PO['id'])
                    c.ok(ok['ap'] and not ok['v'], f'preaward: once the owner approves, the order can be issued ({ok})')
                    lost = await pg.evaluate("a => { const c = DB.clients.find(x => x.id === a.cid); c.estimates.find(e => e.id === a.id).status = 'rejected'; const po = DB.pos.find(x => x.id === a.po); return { v: poValid(po).filter(x => /lost/.test(x)), row: puOrderRows('').some(x => x.id === 'preaward:' + po.id) }; }", {'cid': PA['cid'], 'id': PA['id'], 'po': PO['id']})
                    c.ok(lost['v'] and lost['row'], f'preaward: a lost estimate holds the order and flags it on Orders to cancel ({lost})')
                    await sign_in(pg, 'u_chen')
        if want('request'):
            q = await pg.evaluate("k => { const p = DB.projects.find(x => x.id === 'p121'); const q = p.requests.find(r => /stud/i.test(r.what || '')); if (!q) return null; q.line = k; save(); return { id: q.id, what: q.what }; }", L2)
            await sheet(pg, [L2])
            S = await pg.evaluate(ROW, L2)
            c.ok(q and S and any(x['id'] == q['id'] and x['on'] for x in S['req']), f"request: the order sheet offers the studs request under line 2, ticked ({S and S['req']})")
            await fill(pg, L2, '4.6', vend)
            await pg.evaluate("k => { const tr = document.querySelector(`#mbm tr[data-pukey=\"${k}\"]`); const i = tr.querySelector('[data-ctpq]'); i.value = '40'; i.dispatchEvent(new Event('input', { bubbles: true })); const u = tr.querySelector('[data-ctpu]'); u.value = 'ea'; u.dispatchEvent(new Event('input', { bubbles: true })); }", L2)
            await pg.wait_for_timeout(200)
            await okb(pg); await pg.wait_for_timeout(500)
            m = await pg.evaluate(MODAL)
            if m and 'Confirm' in m['title']: await okb(pg); await pg.wait_for_timeout(500)
            R = await pg.evaluate("""id => { const p = DB.projects.find(x => x.id === 'p121'); const q = p.requests.find(r => r.id === id);
              const po = DB.pos.find(x => x.lines.some(l => l.requestId === id)); const run = (typeof runItems === 'function' ? runItems() : []).some(x => x && x.r && x.r.id === id);
              return { path: q.path, po: po && po.number, item: po && po.lines.find(l => l.requestId === id).item, run }; }""", q['id'] if q else '')
            c.ok(R['path'] == 'order' and R['po'] and not R['run'], f'request: the order covers the studs request; it is off the store run ({R})')
            c.ok(q and R['item'] == q['what'], f"request: the PO line names the studs, not the estimate line ({R['item']})")
        if want('docs'):
            D = await pg.evaluate("""() => { mbCloseModal(); ctPOPicker('p121', '*'); const o = [...document.querySelectorAll('#mbm #ctp-doc option')].map(x => x.value).filter(v => v !== '*');
              const all = DB.clients.flatMap(c => [...c.estimates, ...c.changeOrders, ...c.invoices]); return o.map(id => { const d = all.find(x => x.id === id); return d.type + ':' + d.status; }); }""")
            c.ok(D and all(re.match(r'(estimate:(approved|converted)|co:(approved|billed)|invoice:(?!draft|void))', x) for x in D), f'docs: the order sheet lists only documents the firm may buy from ({D})')
        if want('status'):
            S = await pg.evaluate("""() => { const r = buyList('').find(x => x.lineKey && !x.ordered && x.tab === 'buy' && x.kind === 'material'); if (!r) return null;
              const q = rfqCreate({ projectId: r.p.id, title: 'test draft', lines: [{ item: r.name, qty: 1, unit: 'ea', fromLine: r.lineKey, line: r.lineKey }] });
              const s = puNeedStatusFor(r.lineKey); return { s, n: q.number }; }""")
            c.ok(S and S['s'] and S['s']['actor'] == 'coord' and 'draft' in S['s']['why'] and 'vendors' in S['s']['why'], f"status: a draft RFQ is the coordinator's to send, not the vendors' ({S})")
            T = await pg.evaluate("""() => { const I = bbTodayItems(); return I.map(it => { const c = bbTodayCard(it), x = puNeed(it.x); return [c.verb, x ? x.act : null, it.x.name]; }); }""")
            c.ok(T and all(v == a for v, a, n in T), f'status: each Today Buy Board card says what its Buy Board row says {[t for t in T if t[0] != t[1]][:3]}')
        if want('item'):
            await board(pg)
            G = await pg.evaluate("""() => { const r = buyList('').find(x => /^GWB/.test(x.name)); if (!r) return null; bbSel = r.id; render();
              const t = (document.querySelector('#buy-board .bb-panel') || {}).innerText || '', row = puNeed(r);
              return { t, stock: puStockFor(r.name).length, why: row && row.why }; }""")
            shop = re.search(r'At the shop\s*\n?\s*([^\n]+)', G['t']) if G else None
            c.ok(G and (G['stock'] == 0 or (shop and shop.group(1).strip() != 'none')), f"item: the drywall panel's shop agrees with its row ({shop and shop.group(1)}; row stock {G and G['stock']})")
            c.ok(G and '$52' not in G['t'], 'item: the drywall panel does not show the insulation price as its last buy')
            # the stock gate
            await pg.evaluate("() => { const r = buyList('').find(x => puStockFor(x.name).length && !x.ordered && x.tab === 'buy'); r && puStockGate([r], () => toast('went')); }")
            await pg.wait_for_timeout(300)
            m = await pg.evaluate(MODAL)
            c.ok(m and m['ok'] == 'Use the Stock, Buy the Rest', f"item: the stock gate's blue is Use the Stock, Buy the Rest ({m and m['ok']})")
            await closeall(pg)
            # the price history prices a billed order line on the bill lines that pay for it (P3, 11-05: $55.56/ea windows)
            # (the chief of staff, 11-05: a bill line with no quantity is a payment, not a price; a lump sum billed in part keeps
            # the order's price; quantities and amounts add up across a PO line's bills; a bill across orders goes line by line)
            PH = await pg.evaluate("""() => { const H = itemPriceHistory(pwKeyFor('Double-hung windows, front & rear', 'ea')); const D = pwData(), bad = [], seen = [];
              const gd = x => { const d = String(x.desc || x.item || '').split(' \u2014 ')[0]; return !/^(sales |use )?tax\\b/i.test(d) && !PW_FEE_RE.test(d); };
              const desc = l => String(l.desc || l.item || '').split(' \u2014 ')[0], goods = po => (po.lines || []).filter(x => !PW_FEE_RE.test(x.item || x.desc || ''));
              const live = DB.bills.filter(b => !['void', 'rejected', 'draft'].includes(b.status));
              Object.values(D.items).forEach(I => I.buys.filter(B => B.kind === 'po').forEach(B => { const po = DB.pos.find(p => p.id === B.poId), pl = po && po.lines.find(l => l.id === B.poLineId); if (!pl) return;
                let amt = 0, q = 0; const ids = new Set();
                live.forEach(b => { const G = (b.lines || []).filter(gd); G.forEach(l => { const lpo = (l.poId && DB.pos.find(p => p.id === l.poId)) || (l.poLineId && DB.pos.find(p => p.lines.some(x => x.id === l.poLineId))) || DB.pos.find(p => p.id === b.poId);
                  if (lpo !== po || pwBillPoLine(lpo, goods(lpo), l, desc(l), lpo.id === b.poId ? G.length : 1) !== pl) return; ids.add(b.id); +l.qty > 0 && +l.amount > 0 && ((amt += +l.amount), (q += +l.qty)); }); });
                const lump = /^(ls|lot|lump)/i.test(pl.unit || '') || +pl.qty === 1, priced = q > 0 && amt > 0 && !(lump && amt < pl.qty * pl.price * 0.98);
                if (priced ? Math.abs(amt / q / B.packF - B.price) > 0.01 : B.paidPrice != null) bad.push([I.label, B.price, priced ? amt / q : 'order price']);
                const S = B.sources.filter(s => s.billId).map(s => s.billId); (new Set(S).size !== S.length || S.length !== ids.size) && bad.push(['sources', I.label, S.length, ids.size]);
                ids.size && seen.push([po.number, B.price]); }));
              const cm = live.find(b => /CM-0091/.test(b.number || '')), cmB = cm && Object.values(D.items).flatMap(I => I.buys).find(B => B.poId === cm.poId && B.kind === 'po');
              return { w: H && H.rows[0].price, bad, cm: cm ? { price: cmB && cmB.price, order: cmB && cmB.qty * cmB.price } : null, seen }; }""")
            c.ok(PH['w'] and abs(PH['w'] - 3300) < 0.01, f"item: the windows read the order's $3,300 (the bill gives no quantity: a payment, not a price), not $55.56 ({PH['w']})")
            c.ok(PH['cm'] is None or (PH['cm']['price'] and PH['cm']['price'] > 38000), f"item: CM-0091, $38,000 on a $76,000 lump sum, is a progress payment, not the price ({PH['cm']})")
            c.ok(not PH['bad'], f"item: every billed price is its bills' amount over their quantity, summed across bills, each bill once ({PH['bad']})")
            # unit prices keep their cents (unitMoney); money() stays whole dollars, so a client document's lines add up to
            # its printed total (the chief of staff's review, 11-05: a $45.50 line beside rounded ones did not add up)
            M = await pg.evaluate("() => [unitMoney(4.6), unitMoney(3.98), unitMoney(3300), unitMoney(-4.6), money(4.6), money(45.5), money(1719.42)]")
            c.ok(M == ['$4.60', '$3.98', '$3,300.00', '−$4.60', '$5', '$46', '$1,719'], f'item: unit prices keep their cents, money() stays whole dollars ({M})')
            LP = await pg.evaluate("""() => { const r = buyList('').find(x => x.tab === 'buy' && !x.ordered && bbLastPrices(x).some(p => p.p % 1)); if (!r) return null; bbSel = r.id; procMode = 'lines'; view = 'proc'; render();
              return { t: (document.querySelector('#buy-board .bb-panel') || {}).innerText || '', p: bbLastPrices(r).find(p => p.p % 1).p }; }""")
            c.ok(LP is None or f"{LP['p']:,.2f}" in LP['t'], f"item: the panel's last buys show cents ({LP and LP['p']})")
            # a price above the best known, flagged as typed on the order sheet
            B2 = await pg.evaluate("() => { const H = itemPriceHistory('2x4x8 KD stud'); return H && H.best ? { p: H.best.price, u: H.unit } : null; }")
            if B2:
                await pg.evaluate("k => { const p = DB.projects.find(x => x.id === 'p121'); p.requests.filter(r => /stud/i.test(r.what || '')).forEach(r => { r.path = ''; r.status = 'ack'; r.line = k; }); }", L2)
                await sheet(pg, [L2])
                await fill(pg, L2, str(round(B2['p'] * 1.2, 2)), vend)
                F = await pg.evaluate(ROW, L2)
                c.ok('above the best price known' in F['note'], f"item: a price 20% above the best known for the studs is flagged ({F['note']})")
                await closeall(pg)
        if want('split'):
            await sign_in(pg, 'u_alan')
            A = await pg.evaluate("() => mApprovals().filter(x => x.kind === 'matsplit').map(x => x.id)")
            c.ok(A, f'split: the PM has the material portion in Approvals ({A})')
            if A:
                await pg.evaluate("k => puMatSheet(k)", A[0]); await pg.wait_for_timeout(300)
                m = await pg.evaluate(MODAL)
                c.ok(m and m['title'] == 'Set the Material Portion', f"split: Set the Material Portion opens its one-field sheet ({m and m['title']})")
                await pg.fill('#mbm [data-f="mat"]', '40%'); await okb(pg); await pg.wait_for_timeout(400)
                v = await pg.evaluate("k => { const r = findLine(k); return r && r.line.costMaterial; }", A[0])
                c.ok(v is not None and v > 0, f'split: 40% sets the material portion ({v})')
            await sign_in(pg, 'u_chen')
        if want('ffe'):
            for dev_pg in (pg,):
                await board(dev_pg)
                lab = await dev_pg.evaluate("() => (document.querySelector('#bb-more') || {}).innerText")
                await dev_pg.click('#bb-more'); await dev_pg.wait_for_timeout(400)
                F = await dev_pg.evaluate("() => ({ h: (document.querySelector('#proc-body .ph h2') || {}).innerText, tabs: [...document.querySelectorAll('#proc-body [data-pf], #proc-body [data-ppane]')].map(b => b.innerText.trim()), run: !!document.querySelector('#proc-run.primary') })")
                c.ok(F['h'] == lab == 'FF&E Buying Tools', f"ffe: the page is headed as its button reads ({F['h']} / {lab})")
                c.ok(not F['run'], 'ffe: no blue New Buy Run that only toasts when nothing is ticked')
                await dev_pg.click('#proc-body [data-pf="late"]'); await dev_pg.wait_for_timeout(300)
                F2 = await dev_pg.evaluate("() => [...document.querySelectorAll('#proc-body [data-pf], #proc-body [data-ppane]')].map(b => b.innerText.trim())")
                c.ok(F2 == F['tabs'] and all(re.match(r'^([A-Z&][^ ]*)( (the|to|of|a|and|by|at|on|for|in)?( ?[A-Z&][^ ]*)?)*$', t) for t in F2), f"ffe: the tabs keep their Title Case after a tap ({F2} vs {F['tabs']})")
                await dev_pg.click('#proc-body [data-pf="open"]'); await dev_pg.wait_for_timeout(300)
                await dev_pg.evaluate("() => { const tr = [...document.querySelectorAll('#proc-body tr')].find(t => /fireclay sink/i.test(t.innerText)); const cb = tr && tr.querySelector('[data-pick]'); cb && cb.click(); }"); await dev_pg.wait_for_timeout(300)
                run = await dev_pg.evaluate("() => { const b = document.querySelector('#proc-run'); return b && { blue: b.classList.contains('primary'), t: b.innerText }; }")
                c.ok(run and run['blue'], f'ffe: New Buy Run is the blue once an item is ticked ({run})')
                if run:
                    n0 = await dev_pg.evaluate("() => DB.pos.length")
                    await dev_pg.click('#proc-run'); await dev_pg.wait_for_timeout(400)
                    m = await dev_pg.evaluate(MODAL)
                    n1 = await dev_pg.evaluate("() => DB.pos.length")
                    c.ok(m is not None or n1 > n0, f"ffe: New Buy Run makes something real: the buy run sheet or a drafted order ({m and m['title']}, orders {n0} -> {n1})")
                    await closeall(dev_pg); await dev_pg.evaluate("() => { procSel.clear(); procMode = 'lines'; }")
        await door(c, pg, 'desktop')
        c.ok(not errs, f'desktop: no page errors {errs[:3]}')
    finally:
        await b.close()

async def door(c, pg, dev):
    if not want('door'): return
    await sign_in(pg, 'u_alan')
    await pg.evaluate("() => { const c = DB.clients.find(c => c.estimates.some(e => e.number === 'EST-2026-014')); flowGo.doc(c, 'estimate', c.estimates.find(e => e.number === 'EST-2026-014'))(); }")
    await pg.wait_for_timeout(600)
    lab = await pg.evaluate("() => (document.querySelector('.view.on [data-docact=\"pos\"]') || {}).innerText")
    c.ok(lab == 'Buy These Lines', f'door {dev}: the estimate reads Buy These Lines ({lab})')
    await pg.locator('.view.on [data-docact="pos"]').first.click(); await pg.wait_for_timeout(500)
    D = await pg.evaluate("() => ({ ticks: document.querySelectorAll('.view.on [data-pubuy]').length, rows: document.querySelectorAll('.view.on table.rx-lines tr[data-rxline]').length })")
    c.ok(D['ticks'] > 0 and D['ticks'] == D['rows'], f'door {dev}: every line of the estimate can be ticked {D}')
    for lid in ('l1', 'l4'):
        await pg.locator(f'.view.on [data-pubuy="{lid}"]').first.click(); await pg.wait_for_timeout(150)
    B = await pg.evaluate("() => ({ t: (document.querySelector('.pu-docbar') || {}).innerText || '', blue: [...document.querySelectorAll('.btn.primary')].filter(b => b.checkVisibility({ visibilityProperty: true, opacityProperty: true }) && b.innerText.trim() && !b.closest('#mbm')).map(b => b.innerText.trim()) })")
    c.ok('2 lines picked' in B['t'] and B['blue'] == ['Buy These Lines'], f"door {dev}: two picked, one blue: the bar's Buy These Lines ({B})")
    tgt = await pg.evaluate("() => { const b = document.querySelector('#pu-docbuy-go').getBoundingClientRect(); return { h: b.height, inview: b.bottom <= innerHeight && b.top >= 0 }; }")
    c.ok(tgt['h'] >= (44 if dev == 'phone' else 32) and tgt['inview'], f'door {dev}: the bar button is in view and big enough {tgt}')
    await pg.click('#pu-docbuy-go'); await pg.wait_for_timeout(500)
    S = await pg.evaluate("() => [...document.querySelectorAll('#mbm [data-ctpsel]:checked')].map(i => i.closest('tr').dataset.pukey)")
    c.ok(sorted(S) == ['estimate:es1:l1', 'estimate:es1:l4'], f'door {dev}: the order sheet opens with those two lines ticked ({S})')
    await closeall(pg)
    # a draft estimate has no buying door
    dr = await pg.evaluate("() => { const c = DB.clients.find(c => c.estimates.some(e => e.status === 'draft' && e.lines.length)); if (!c) return null; const d = c.estimates.find(e => e.status === 'draft' && e.lines.length); return docActions(c, d).includes('data-docact=\"pos\"'); }")
    c.ok(dr in (None, False), f'door {dev}: a draft estimate cannot be bought from ({dr})')
    await sign_in(pg, 'u_chen')

async def phone(c, p):
    b, pg, errs = await open_app(p, True)
    try:
        await sign_in(pg, 'u_chen')
        if want('phone'):
            await pg.evaluate("() => { view = 'proc'; render(); }")
            await sheet(pg, [L1, L3])
            P = await pg.evaluate("""() => { const m = document.querySelector('#mbm .mbm-box'), bd = m.querySelector('.mbm-bd'), rows = [...m.querySelectorAll('table.ctp tr.ctp-line')];
              const v = rows.map(tr => tr.querySelector('[data-ctpv]')).filter(Boolean), inp = rows.flatMap(tr => [...tr.querySelectorAll('input:not([type=checkbox])')]);
              const names = rows.map(tr => tr.cells[1].querySelector('b')).filter(Boolean);
              return { sw: bd.scrollWidth, cw: bd.clientWidth, tw: [...m.querySelectorAll('.tw')].map(t => [t.scrollWidth, t.clientWidth]), docsw: document.documentElement.scrollWidth,
                vmin: Math.min(...v.map(x => x.getBoundingClientRect().width)), hmin: Math.min(...inp.map(x => x.getBoundingClientRect().height)),
                cut: names.filter(n => n.scrollWidth > n.clientWidth + 1 || n.getBoundingClientRect().right > innerWidth).map(n => n.innerText),
                overlap: rows.flatMap(tr => [...tr.cells]).filter(td => td.getClientRects().length && td.scrollHeight > td.clientHeight + 1).map(td => td.innerText.slice(0, 30)),
                ticked: [...m.querySelectorAll('[data-ctpsel]:checked')].map(i => i.closest('tr').dataset.pukey) }; }""")
            c.ok(P['sw'] <= P['cw'] + 1 and all(a <= b2 + 1 for a, b2 in P['tw']) and P['docsw'] <= 390, f'phone: the order sheet does not scroll sideways {P["sw"]}/{P["cw"]} {P["tw"]} doc {P["docsw"]}')
            c.ok(P['vmin'] >= 300, f"phone: the vendor picker is full width ({P['vmin']:.0f}px)")
            c.ok(P['hmin'] >= 44, f"phone: the sheet's inputs are 44px tall ({P['hmin']:.0f}px)")
            c.ok(not P['overlap'], f"phone: no card's text runs over the next field ({P['overlap']})")
            c.ok(not P['cut'], f"phone: no item name is cut off ({P['cut']})")
            c.ok(sorted(P['ticked']) == sorted([L1, L3]), f"phone: the lines it opened for stay ticked ({P['ticked']})")
            await closeall(pg)
        await door(c, pg, 'phone')
        if want('ffe'):
            await board(pg)
            await pg.click('#bb-more'); await pg.wait_for_timeout(400)
            h = await pg.evaluate("() => (document.querySelector('#proc-body .ph h2') || {}).innerText")
            c.ok(h == 'FF&E Buying Tools', f'phone ffe: headed FF&E Buying Tools ({h})')
            sw = await pg.evaluate("() => document.documentElement.scrollWidth")
            c.ok(sw <= 390, f'phone ffe: no sideways scroll ({sw})')
        c.ok(not errs, f'phone: no page errors {errs[:3]}')
    finally:
        await b.close()

async def main():
    c = Checks()
    async with async_playwright() as p:
        await desktop(c, p)
        await phone(c, p)
    return c.done()

sys.exit(asyncio.run(main()))
