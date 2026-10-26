"""buyboard_test: procurement P1, One Buy Board (docs/PROCUREMENT_PLAN.md sections 4 and 6; buying day 2026-10-25).

Each check starts from how the reviews saw it fail:
  ONE LATE   the late set is one rule (not ordered by order-by; ordered with a promise after need-by; promised and not
             here): the rail badge, the board's late pill and Late section, PRED.lateMaterial, Today's Buy Board items and
             Ask's "what's late to order" read one number (10-21 F4, F14; buying day 1, 11, 12)
  REACH      a change-order line, an approved FF&E item, a field request and a sub scope (demolition) reach the board;
             a late promise (insulation 9/16 vs 9/11) reaches the coordinator's Do Now with the fix choices; a backorder
             moved on a PO reaches Do Now the same day (10-21 F9, F13; buying day 4, 16, 22)
  BOARD      opens on To Buy for the coordinator; sections Late, Order This Week, Waiting on Quotes, Later; Arriving;
             tab and chip counts equal their rows; one blue button; no tiles; no board on the Purchase Orders page;
             phone: cards, no table, no sideways scroll, 44px picks, Order N Lines and Ask for Quotes (F4, F22, F26)
  LINKS      a request carries its line (picker, never a guess); an RFQ award copies requestId and materialId into the
             PO lines and moves the request to ordered; a sub-scope award is a subcontract and the COI gate holds it
  ONE PATH   a request on an order leaves the driver's list; a store-run buy cancels its draft order; never both
  ROUTE      the driver's route waits in the coordinator's Approvals and Do Now, due before the van leaves (F6)
  ROLES      PM (late needs on Today, Buying on This Job), foreman (no board, Requests), driver (Route), owner (board)
  MENU       Purchasing reads Buy Board, Quotes, Orders, Deliveries, Vendors, Stock; the phone's Buy Board tab is lit on
             Orders and Deliveries (F19); no project strip on Orders or Deliveries (F20)
Usage: python3 buyboard_test.py"""
import asyncio, os, sys
from harness import *

OUT = os.path.join(ROOT, 'review', 'p1')

LATE = "() => ({ pred: PRED.lateMaterial.rows().length, board: buyList('').filter(r => r.late).length, badge: needs('buy'), need: PRED.buyNeeds.rows().length, week: PRED.orderThisWeek.rows().length })"

async def board(pg, uid='u_chen', tab='buy'):
    await sign_in(pg, uid)
    await pg.evaluate("t => { bbTab = t; bbFilter = 'all'; bbProj = ''; bbVendor = ''; bbTrade = ''; bbQ = ''; bbPick.clear(); delete tlFocus.proc; procMode = 'lines'; view = 'proc'; render(); }", tab)
    await pg.wait_for_timeout(300)

async def shot(pg, name):
    os.makedirs(OUT, exist_ok=True)
    await pg.screenshot(path=os.path.join(OUT, name), full_page=False)

async def desktop(c, p):
    b, pg, errs = await open_app(p, False)
    try:
        # ---- ONE LATE
        await board(pg)
        L = await pg.evaluate(LATE)
        c.ok(L['pred'] == L['board'] and L['pred'] > 0, f'one late: PRED.lateMaterial and the board agree {L}')
        c.ok(L['badge'] == L['need'] and L['need'] >= L['pred'], f'the Buy Board badge is late or due this week (PRED.buyNeeds) {L}')
        st = await pg.evaluate("""() => { const v = document.querySelector('#v-proc');
          const n = s => { const e = v.querySelector(s); return e ? +((e.innerText.match(/\\d+/) || [0])[0]) : null; };
          const sec = k => v.querySelectorAll(`[data-bbsec="${k}"] [data-bbrow]`).length;
          return { pill: n('.bb-latepill'), ack: sec('ack'), late: sec('late'), week: sec('week'), quotes: sec('quotes'), later: sec('later'),
            tabBuy: n('[data-bbtab="buy"] .n'), tabArr: n('[data-bbtab="arriving"] .n'), rows: v.querySelectorAll('.bb-list [data-bbrow]').length,
            chips: [...v.querySelectorAll('[data-bbf]')].map(b => [b.dataset.bbf, +b.querySelector('.n').innerText]),
            prim: [...v.querySelectorAll('.btn.primary')].filter(b => b.getClientRects().length).map(b => b.innerText.trim()),
            tiles: v.querySelectorAll('button.gl, .kpi').length, panel: !!v.querySelector('.bb-panel h3'), h: (v.querySelector('h2') || {}).innerText,
            head: [...v.querySelectorAll('.bb-sh span')].map(s => s.innerText) }; }""")
        c.ok(st['h'] == 'Buy Board' and st['tabBuy'] == st['rows'], f"board: opens on To Buy, the tab count is the rows ({st['tabBuy']} vs {st['rows']})")
        c.ok(st['pill'] == L['badge'] and st['late'] == L['pred'], f"board: the pill {st['pill']} is the rail badge {L['badge']}; the Late section is the late set")
        # a field request waiting to be acknowledged has its own first section (10-26), so Late plus Order This Week is the chip
        hd = [h for h in st['head'] if h != 'TO ACKNOWLEDGE']
        c.ok(hd[:1] == ['LATE'] and st['ack'] + st['late'] + st['week'] + st['quotes'] + st['later'] == st['rows'], f"board: sections To Acknowledge, Late, Order This Week, Waiting on Quotes, Later hold every row {st['head']}")
        ch = dict(st['chips'])
        c.ok(ch.get('all') == st['rows'] and ch.get('late') == st['late'] and ch.get('week') == st['week'] and ch.get('quotes') == st['quotes'], f"board: each chip is its rows {st['chips']}")
        c.ok(len(st['prim']) == 1 and st['tiles'] == 0 and st['panel'], f"board: one blue button {st['prim']}, no tiles ({st['tiles']}), the need's panel")
        for k in ['late', 'week']:
            await pg.evaluate("k => { bbFilter = k; render(); }", k); await pg.wait_for_timeout(200)
            n = await pg.evaluate("() => document.querySelectorAll('#v-proc .bb-list [data-bbrow]').length")
            c.ok(n == ch.get(k), f'board: the {k} chip shows its {ch.get(k)} rows ({n})')
        await pg.evaluate("() => { bbFilter = 'all'; render(); }")
        await shot(pg, 'd1_buyboard.png')
        # Today: the coordinator's Buy Board items are the late set and this week's (none other)
        # Do Now: every one of them once (the today lane's rule); the three the site needs soonest rank as the Standard ranks
        # them, the rest after the day's other work of the same urgency (tier 9), so the vendors' new dates stay in his top five
        td = await pg.evaluate("""() => { const M = tdyModel(); const B = M.all.filter(i => i.kind === 'tdyBuy');
          const want = PRED.buyNeeds.rows().map(r => r.id);
          return { all: B.map(i => i.id).sort(), chip: (M.buy || []).map(i => i.id).sort(), want: want.sort(), top: B.filter(i => i.tier !== 9).length,
                   fix: B.filter(i => i.ea.fix).map(i => [i.x.name, tdCard(i).verb]), ins: (M.buy || []).some(i => /Insulation/.test(i.x.name)) }; }""")
        c.ok(td['chip'] == td['want'] and td['all'] == td['want'], f"Today: the Buy Board chip and All hold PRED.buyNeeds, the badge's set ({len(td['chip'])}, {len(td['all'])} vs {len(td['want'])})")
        c.ok(0 < td['top'] <= 3, f"Do Now: at most three Buy Board lines rank first; the rest follow the day's other work ({td['top']} of {len(td['all'])})")
        c.ok(any(v == 'Fix' for n, v in td['fix']) and td['ins'], f"Do Now: a late promise is there with Fix, and the insulation (promised 9/16 for 9/11) is in the chip {td['fix']}")
        a = await pg.evaluate("() => paAsk(\"what's late to order\").headline")
        c.ok(str(L['pred']) in a, f'Ask: "what\'s late to order" says {L["pred"]} ({a[:90]})')
        # the late promise opens with the fix choices
        await pg.evaluate("() => { const r = buyList('').find(x => /Insulation/.test(x.name)); bbSel = r.id; render(); }"); await pg.wait_for_timeout(200)
        steps = await pg.evaluate("() => [...document.querySelectorAll('#v-proc .bb-panel [data-bbstep]')].map(b => b.innerText.trim())")
        c.ok(len(steps) == 3 and steps[0].startswith('Expedite') and 'Other Vendor' in steps and 'Move the Task' in steps, f'panel: a late promise offers Expedite, Other Vendor, Move the Task {steps}')
        await shot(pg, 'd2_panel_late_promise.png')
        # ---- REACH
        R = await pg.evaluate("""() => { const B = buyList('');
          return { co: B.filter(r => r.src === 'co').map(r => [r.name, r.lineKey, r.tab]), ffe: B.filter(r => r.kind === 'ffe').map(r => r.it.stage),
                   req: B.filter(r => r.kind === 'request').map(r => r.q.id), sub: B.filter(r => r.kind === 'sub').map(r => [r.name, r.late]),
                   labour: B.filter(r => /General conditions|Permits/.test(r.name)).length }; }""")
        c.ok(any(k.startswith('co:') and t == 'buy' for n, k, t in R['co']), f"reach: a change-order line is on the board with its line link {R['co']}")
        c.ok(R['ffe'] and all(s in ('appr', 'po', 'ord', 'ship') for s in R['ffe']), f"reach: approved FF&E items are on the board, none still with the designer {R['ffe']}")
        c.ok('rq2' in R['req'], f"reach: an open field request is a need {R['req']}")
        c.ok(any('Demolition' in n and late for n, late in R['sub']) and R['labour'] == 0, f"reach: demolition with no sub contracted is a late sub buyout; our own labour lines never show {R['sub']}")
        # a backorder moved on a PO reaches Do Now the same day
        bo = await pg.evaluate("""() => { const po = DB.pos.find(p => p.number === 'PO-2026-047'); po.expected = '2026-10-23';
          const p = DB.projects.find(x => x.id === po.projectId); const m = p.materials.find(x => x.id === 'm10'); m.eta = '2026-10-23'; save(); view = 'home'; render();
          const B = tdyModel().all.filter(i => i.kind === 'tdyBuy'), r = buyList('').find(x => x.m && x.m.id === 'm10');
          const own = B.find(i => i.x.m && i.x.m.id === 'm10'), more = null;
          bbSel = r.id; bbTab = 'buy'; view = 'proc'; render();
          return { why: r.lateWhy, today: own ? tdCard(own).verb : more ? 'in ' + more.title : null, steps: [...document.querySelectorAll('#v-proc .bb-panel [data-bbstep]')].map(b => b.innerText.trim()), ask: paAsk("what's backordered").headline }; }""")
        c.ok(bo and '10/23' in bo['why'] and bo['today'] and bo['steps'][:1] and bo['steps'][0].startswith('Expedite') and 'White oak' in bo['ask'], f'Do Now: a backorder to 10/23 on a 10/2 need is late, on Today, with the fix choices, and in Ask {bo}')
        # ---- LINKS: a request gets its line from the picker, ranked by match, never guessed
        lk = await pg.evaluate("""() => { const r = buyList('').find(x => x.kind === 'request' && x.q.id === 'rq2'); const before = r.q.line;
          bbLinkLine(r); const opts = [...document.querySelectorAll('#mbm [data-bbl]')].map(i => i.dataset.bbl);
          const pick = opts.find(k => k.startsWith('estimate:')); document.querySelector(`#mbm [data-bbl="${pick}"]`).checked = true;
          document.querySelector('#mbm #mbm-ok').click();
          const q = DB.projects.find(p => p.id === 'p121').requests.find(x => x.id === 'rq2');
          return { before, opts: opts.length, line: q.line, pick, label: bbLineLabel(buyList('').find(x => x.kind === 'request' && x.q.id === 'rq2')) }; }""")
        c.ok(not lk['before'] and lk['opts'] > 3 and lk['line'] == lk['pick'] and lk['label'] != 'No line yet', f'links: the coordinator links a request to a line from the picker {lk}')
        # RFQ award: requestId and materialId reach the PO lines; the request reads ordered
        aw = await pg.evaluate("""() => { rfqInit();
          const v = DB.vendors.find(x => x.name === 'Nemo Tile');
          const r = rfqCreate({ projectId: 'p121', title: 'tape and plastic', category: 'Materials', lines: [{ item: 'Blue tape', qty: 1, unit: 'case', requestId: 'rq2', line: '' }] });
          r.requestId = 'rq2'; r.status = 'leveled'; r.vendors = [v.id];
          r.quotes = [{ vendorId: v.id, vendor: v.name, round: 1, lines: [{ lineId: r.lines[0].id, unit: 40, ext: 40 }], freight: 0, lead: 2, confirmed: { by: 'test', at: appNowIso(), how: 'test' } }];
          const made = rfqAward(r, { [r.lines[0].id]: v.id }) || [];
          const po = made[0], q = DB.projects.find(p => p.id === 'p121').requests.find(x => x.id === 'rq2');
          return { po: po && po.number, st: po && po.status, type: po && po.type, req: po && po.lines[0].requestId, qpo: q.poId === (po && po.id), qst: q.status, path: q.path }; }""")
        c.ok(aw['po'] and aw['req'] == 'rq2' and aw['qpo'] and aw['qst'] in ('ordered', 'ack') and aw['path'] == 'order' and aw['type'] == 'materials', f'links: the award copies the request into the PO line and moves the request {aw}')
        sb = await pg.evaluate("""() => { const r0 = buyList('').find(x => x.kind === 'sub' && /Demolition/.test(x.name));
          const q = bbQuote([r0]); if (!q) return null;
          const vp = rfqProposeVendors(q);
          const v = ensureVendor('Brick City Demolition', { trade: 'Demolition' }); v.kind = 'sub'; delete v.insuranceExp;
          q.status = 'leveled'; q.vendors = [v.id];
          q.quotes = [{ vendorId: v.id, vendor: v.name, round: 1, lines: q.lines.map(l => ({ lineId: l.id, unit: 18000, ext: 18000 })), freight: 0, lead: 5, confirmed: { by: 'test', at: appNowIso(), how: 'test' } }];
          const made = rfqAward(q, Object.fromEntries(q.lines.map(l => [l.id, v.id]))) || [];
          const po = made[0];
          return { sub: !!q.sub, cat: q.category, st0: q.status, offered: vp.list.length, picked: vp.pick.length, type: po && po.type, status: po && po.status, why: po ? poValid(po).join(' | ').slice(0, 160) : '' }; }""")
        c.ok(sb and sb['sub'] and sb['cat'] != 'Materials' and sb['offered'] > 0, f'sub: Ask for Bids on demolition starts a sub RFQ, the vendors offered by hand {sb}')
        c.ok(sb and sb['type'] == 'subcontract' and sb['status'] == 'draft' and 'insurance' in sb['why'], f'sub: the award is a subcontract and a sub with no COI is held {sb}')
        # the P0 lane saw it: an RFQ for demolition started from the line (the plain Ask for Quotes, no sub flag), awarded
        # to a vendor not marked as a sub, was typed "materials" and carried use tax; sub scope is read off the lines
        sl = await pg.evaluate("""() => { const r0 = buyList('').find(x => x.kind === 'sub' && /Demolition/.test(x.name)); const pid = r0.p.id;
          const s = rfqLineSources(pid).find(x => /Demolition/i.test(x.item)); if (!s) return { src: null };
          const q = rfqFromLines(pid, [s.key]); if (!q) return { src: s.key, q: null };
          const v = ensureVendor('Five Boro Wrecking', { trade: 'General' }); delete v.kind; v.insuranceExp = '2027-06-30';
          q.status = 'leveled'; q.vendors = [v.id];
          q.quotes = [{ vendorId: v.id, vendor: v.name, round: 1, lines: q.lines.map(l => ({ lineId: l.id, unit: 9000, ext: 9000 })), freight: 0, lead: 5, confirmed: { by: 'test', at: appNowIso(), how: 'test' } }];
          const po = (rfqAward(q, Object.fromEntries(q.lines.map(l => [l.id, v.id]))) || [])[0];
          return { sub: !!q.sub, cat: q.category, st0: q.status, type: po && po.type, tax: po && po.tax, use: po && po.useTax, note: po && /use tax/.test(po.notes) }; }""")
        c.ok(sl and sl.get('sub') and sl['type'] == 'subcontract' and not sl['tax'] and not sl['use'] and not sl['note'], f"sub: a demolition line's RFQ is a sub package from the line itself; its award is a subcontract with no purchase or use tax {sl}")
        # ---- ONE PATH: order a request and it leaves the route; a run buy cancels the draft
        op = await pg.evaluate("""() => { const p = DB.projects.find(x => x.id === 'p121');
          const onRun = id => runItems({ bought: {} }).some(x => x.r.id === id);
          const before = onRun('rq1'); requestAction('p121', 'rq1', 'po'); mbCloseModal();
          const after = onRun('rq1'); const r1 = p.requests.find(x => x.id === 'rq1');
          // a second request: legacy data with a draft order, then the driver buys it on a run
          setCurrent('p121'); const r3 = addRequest({ what: 'Shims, 2 bundles', qty: 2, unit: 'bundle', neededBy: today() }, 'Alberto');
          const po = { id: uid('po'), number: nextPO(), projectId: p.id, vendor: '', date: today(), status: 'draft', lines: [{ id: uid('pl'), item: 'Shims', qty: 2, unit: 'bundle', price: 0, requestId: r3.id }], tax: 0, shipping: 0, matchedTxns: [] };
          DB.pos.push(po); r3.poId = po.id;
          const run = { id: uid('run'), store: 'Home Depot', driver: 'Alex', status: 'open', bought: {} };
          (DB.storeRuns = DB.storeRuns || []).push(run);
          runItems(run).filter(x => x.r.id === r3.id).forEach(x => run.bought[x.key] = true);
          closeRun(run);
          const both = DB.projects.flatMap(q => q.requests || []).filter(q => onRun(q.id) && DB.pos.some(o => ['draft', 'pending', 'issued'].includes(o.status) && (o.id === q.poId || o.lines.some(l => l.requestId === q.id))));
          return { before, after, path1: r1.path, poSt: po.status, r3: r3.status, both: both.map(q => q.id) }; }""")
        c.ok(op['before'] and not op['after'] and op['path1'] == 'order', f'one path: an ordered request leaves the driver\'s list {op}')
        c.ok(op['poSt'] == 'cancelled' and op['r3'] == 'bought' and not op['both'], f'one path: a store-run buy cancels its draft order; no request is on a route and an order at once {op}')
        # ---- ROUTE: the coordinator's Approvals and Do Now
        await sign_in(pg, 'u_chen')
        rt = await pg.evaluate("""() => { const a = mApprovals().find(i => i.kind === 'route'); if (!a) return null;
          const inDo = tdyModel().appr.some(i => i.kind === 'route'); const card = tdCard(a); card.run();
          return { title: a.title, detail: a.detail, inDo, verb: card.verb, after: mApprovals().some(i => i.kind === 'route'), run: (DB.storeRuns || []).some(r => r.status === 'approved') }; }""")
        c.ok(rt and 'before the van leaves' in rt['detail'] and rt['inDo'] and rt['verb'] == 'Approve Route', f'route: the driver\'s route waits in Approvals and Do Now {rt}')
        c.ok(rt and rt['run'] and not rt['after'], f'route: Approve Route approves it and the card leaves {rt}')
        # ---- the Purchase Orders page carries no board; no project strip on Orders or Deliveries
        await pg.evaluate("() => { setCurrent('p121'); poOpen = null; view = 'po'; render(); }"); await pg.wait_for_timeout(300)
        po = await pg.evaluate("() => ({ board: !!document.querySelector('#v-po #buy-board, #v-po .bb'), strip: (() => { const b = document.getElementById('projhdr'); return !!b && !b.hidden && !!b.offsetParent; })(), h: (document.querySelector('#v-po h2') || {}).innerText })")
        c.ok(not po['board'] and not po['strip'], f'orders: no Buy Board copy and no project strip on the Purchase Orders page {po}')
        await pg.evaluate("() => { view = 'recv'; render(); }"); await pg.wait_for_timeout(200)
        c.ok(not await pg.evaluate("() => { const b = document.getElementById('projhdr'); return !!b && !b.hidden && !!b.offsetParent; }"), 'deliveries: no project strip (F20)')
        # ---- MENU
        sub = await pg.evaluate("() => { view = 'proc'; render(); return [...document.querySelectorAll('#subnav [data-sub]')].map(b => b.innerText.replace(/\\s*\\d+$/, '').trim()); }")
        c.ok(sub[:6] == ['Buy Board', 'Quotes', 'Orders', 'Deliveries', 'Vendors', 'Stock'], f'menu: Purchasing reads Buy Board, Quotes, Orders, Deliveries, Vendors, Stock {sub}')
        # ---- ROLES
        await sign_in(pg, 'u_alan')
        pm = await pg.evaluate("""() => { setCurrent('p121'); view = 'dash'; render();
          const card = document.querySelector('#v-dash #bb-job'), rail = document.querySelector('#nav-groups button[data-grp="buy"] .n');
          return { card: card && card.innerText.slice(0, 120), rows: card ? card.querySelectorAll('[data-bbjob], [data-bbjpo]').length : 0, rail: rail ? +rail.innerText : null, need: needs('buy') }; }""")
        c.ok(pm['card'] and 'late' in pm['card'] and pm['rows'] > 0 and pm['rail'] == pm['need'], f'PM: Buying on This Job on the job page (late needs, open orders) and the Purchasing badge {pm}')
        await sign_in(pg, 'u_owner'); await pg.evaluate("() => { view = 'proc'; render(); }"); await pg.wait_for_timeout(200)
        c.ok(await pg.evaluate("() => !!document.querySelector('#v-proc .bb')"), 'owner: opens the Buy Board')
        await sign_in(pg, 'u_angel')
        fm = await pg.evaluate("() => ({ proc: (ROLE_VIEWS[role()] || []).includes('proc'), req: (ROLE_VIEWS[role()] || []).includes('req') })")
        c.ok(not fm['proc'] and fm['req'], f'foreman: asks from Requests, no Buy Board {fm}')
        await sign_in(pg, 'u_alex')
        c.ok(await pg.evaluate("() => (ROLE_VIEWS[role()] || []).includes('route') && !(ROLE_VIEWS[role()] || []).includes('proc')"), 'driver: Route, no Buy Board')
        c.ok(not errs, f'desktop: page errors {errs[:3]}')
    finally:
        await b.close()

async def phone(c, p):
    b, pg, errs = await open_app(p, True)
    try:
        await board(pg)
        st = await pg.evaluate("""() => { const v = document.querySelector('#v-proc');
          const picks = [...v.querySelectorAll('.bb-pick')].filter(x => x.getClientRects().length).slice(0, 6).map(x => { const r = x.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; });
          return { cards: v.querySelectorAll('.bb-card').length, tables: v.querySelectorAll('table').length, sw: document.documentElement.scrollWidth, w: innerWidth, picks,
                   tabs: [...v.querySelectorAll('[data-bbtab] ')].filter(x => x.matches('button')).map(x => x.innerText.replace(/\\s+/g, ' ').trim()),
                   lit: (document.querySelector('#mtabs button.on') || {}).innerText }; }""")
        c.ok(st['cards'] > 5 and st['tables'] == 0 and st['sw'] <= st['w'], f"phone: cards, no table, no sideways scroll {st['cards']} {st['tables']} {st['sw']}")
        c.ok(all(w >= 44 and h >= 44 for w, h in st['picks']), f"phone: picks are 44px targets {st['picks']}")
        c.ok(st['tabs'][:1] and st['tabs'][0].startswith('To Buy') and 'Buy Board' in (st['lit'] or ''), f"phone: To Buy first, the Buy Board tab lit {st}")
        await shot(pg, 'p1_tobuy.png')
        await pg.locator('#v-proc .bb-pick').nth(2).click(); await pg.wait_for_timeout(200)
        await pg.locator('#v-proc .bb-pick').nth(4).click(); await pg.wait_for_timeout(250)
        bar = await pg.evaluate("() => { const b = document.querySelector('#v-proc .bb-bar'); return b ? { t: b.innerText.replace(/\\s+/g, ' '), prim: [...document.querySelectorAll('#v-proc .btn.primary')].filter(x => x.getClientRects().length).map(x => x.innerText.trim()) } : null; }")
        c.ok(bar and 'Order 2 Lines' in bar['t'] and 'Ask for Quotes' in bar['t'] and bar['prim'] == ['Order 2 Lines'], f'phone: two picked lines offer Order 2 Lines (the one blue) and Ask for Quotes {bar}')
        await shot(pg, 'p2_two_picked.png')
        await pg.evaluate("() => { bbPick.clear(); render(); }")
        # a card opens the need as a sheet
        await pg.locator('#v-proc .bb-cbody').first.click(); await pg.wait_for_timeout(300)
        sh = await pg.evaluate("() => { const m = document.querySelector('#mbm'); return m ? { steps: [...m.querySelectorAll('[data-bbstep]')].map(b => b.innerText.trim()), sw: document.documentElement.scrollWidth } : null; }")
        c.ok(sh and sh['steps'] and sh['sw'] <= 390, f'phone: a card opens its need with the next steps {sh}')
        await shot(pg, 'p3_need_sheet.png')
        await pg.evaluate("() => mbCloseModal()")
        await board(pg, 'u_chen', 'arriving')
        ar = await pg.evaluate("() => ({ n: document.querySelectorAll('#v-proc .bb-arr').length, tab: +((document.querySelector('button[data-bbtab=\"arriving\"] .n') || {}).innerText || -1), acts: [...document.querySelectorAll('#v-proc .bb-act')].map(b => [b.innerText, Math.round(b.getBoundingClientRect().height)]) })")
        c.ok(ar['n'] == ar['tab'] and all(h >= 44 for _, h in ar['acts']), f'phone: Arriving lists its tab count, 44px actions {ar}')
        await shot(pg, 'p4_arriving.png')
        # the bottom tab: Orders and Deliveries light Buy Board (F19)
        for v in ['po', 'recv']:
            await pg.evaluate("v => { view = v; render(); }", v); await pg.wait_for_timeout(200)
            lit = await pg.evaluate("() => (document.querySelector('#mtabs button.on') || {}).innerText || ''")
            c.ok('Buy Board' in lit, f'phone: {v} lights the Buy Board tab ({lit!r})')
        c.ok(not errs, f'phone: page errors {errs[:3]}')
    finally:
        await b.close()

async def main():
    c = Checks()
    async with async_playwright() as p:
        await desktop(c, p)
        await phone(c, p)
    return c.done()

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
