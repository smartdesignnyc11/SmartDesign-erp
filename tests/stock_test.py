"""Inventory before buying (BACKLOG §1.8 item 12; Alan, 2026-10-11): "the foreman orders 24 boards of 5/8 Sheetrock
but we have 12 in inventory ... only [the driver or procurement manager] can override purchasing an additional 12,
with a reason". Each section runs in a fresh browser (fresh seeded DB, app day 2026-09-03) and drives the real
buttons; the foreman's phone lays out at 390px. The demo stock carries 12 sheets of 5/8" Type X and 8 sheets of 5/8"
moisture-resistant drywall at the Warehouse (iv16, iv17).

  split     The foreman asks for 24 sheets of 5/8" Type X on the phone: the request splits 12 from stock (reserved,
            with the Warehouse as its pickup) and 12 to buy; the receipt and the toast say "12 from stock at the
            Warehouse, 12 to buy" with no sideways scroll; the coordinator has a Needs Your Hand row, the driver the
            pick on his day plan and his route; the foreman and the PM cannot override; it survives a reload.
  override  The driver overrides with "Count was wrong" (5 really there): the count is corrected with a logged
            adjustment, 5 stay from stock and 19 are bought, the item comes back for a recount (Count This clears
            it); the coordinator overrides another split with "Damaged" from Needs Your Hand: all 24 are bought.
            Overrides and adjustments are rows in erpQuery; the owner's Override Patterns count equals its rows.
  spec      Moisture-resistant stock against a Type X request does not split and asks the coordinator; a request
            with no type ("5/8 sheetrock") asks too, and "Same Item" makes the split.
  po        A PO line buying stocked drywall is refused at Issue with the reason, warned inline on the PO page;
            Take From Stock reduces the line and puts the pick on the driver's list, then it issues; another
            line is cleared by the coordinator's override; the PM sees no Override.
  after     A card purchase of stocked drywall with no override is flagged (CATCH boughtWhileInStock, PRED count =
            rows, Ask "what did we buy this month that we had in stock"); the coordinator's after-the-fact
            override clears it. Ask "do we have 5/8 drywall in stock" answers from the stock. Delivered stock is a
            cost to the job's line; Return to Stock credits it; a cost-plus job's leftovers go to the PM; a pick
            not made in five days is released and the coordinator is told.

    python3 stock_test.py [--section split,override,...]
"""
import asyncio, re, sys, argparse
from harness import *

TOAST = """() => { const t = document.getElementById('toast'); return t ? { text: t.innerText.trim(), open: !!t.querySelector('.toast-open') } : { text: '', open: false }; }"""
LAST = "(() => { const p = DB.projects.find(x => x.id === 'p121'); return p.requests[p.requests.length - 1]; })()"

async def foreman_request(pg, text):
    await sign_in(pg, 'u_angel'); await go(pg, 'req')
    await pg.fill('#cp-text', text)
    await pg.click('#cp-read'); await pg.wait_for_timeout(1200)
    await pg.click('#cp-send'); await pg.wait_for_timeout(900)

async def modal_submit(pg, fields):
    for k, v in fields.items():
        el = pg.locator(f'#mbm [data-f="{k}"]')
        if await el.evaluate('e => e.tagName') == 'SELECT': await el.select_option(v)
        else: await el.fill(str(v))
    await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(600)

async def reload(pg):
    await pg.evaluate("() => (typeof saveNow === 'function' ? saveNow() : save())"); await pg.wait_for_timeout(800)
    await pg.reload(); await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)

# ------------------------------------------------------------------------------------------------ split
async def s_split(p, c):
    b, pg, errs = await open_app(p, phone=True)
    try:
        await foreman_request(pg, '24 sheets 5/8" Type X drywall')
        r = await pg.evaluate(f"() => {{ const r = {LAST}; return {{ items: r.items.map(i => [i.qty, i.invId, i.pickupFrom]), id: r.id }}; }}")
        c.ok(r['items'] == [[12, 'iv16', 'wh'], [12, '', '']], f'split: 24 sheets split 12 from stock (Warehouse) and 12 to buy, got {r["items"]}')
        m = await pg.evaluate("() => (document.querySelector('#mbm') || {}).innerText || ''")
        c.ok('12 from stock at the Warehouse, 12 to buy' in m, f'split: the receipt says it plainly, got {m[:300]!r}')
        t = await pg.evaluate(TOAST)
        c.ok('12 from stock at the Warehouse, 12 to buy' in t['text'] and t['open'], f'split: the toast says the split with Open, got {t}')
        sw = await pg.evaluate("() => document.scrollingElement.scrollWidth")
        c.ok(sw <= 390, f'split: no sideways scroll at 390px with the receipt open, scrollWidth {sw}')
        avail = await pg.evaluate("() => invAvailable(DB.inventory.find(i => i.id === 'iv16'))")
        c.ok(avail == 0, f'split: the 12 are reserved (available {avail})')
        await pg.evaluate("() => mbCloseModal()")
        # the foreman and the PM see it as fixed
        for uid in ('u_angel', 'u_alan'):
            await sign_in(pg, uid)
            got = await pg.evaluate("() => { const sp = DB.stock.splits[0]; const o = stockOverride({ split: sp.id, reason: 'damaged' }); return { o: !!o, n: DB.stock.overrides.length, state: sp.state }; }")
            c.ok(not got['o'] and got['n'] == 0 and got['state'] == 'held', f'split: {uid} cannot override, got {got}')
            await pg.evaluate("() => stockOverrideDialog({ split: DB.stock.splits[0].id })")
            c.ok(not await pg.evaluate("() => !!document.querySelector('#mbm [data-f=reason]')"), f'split: {uid} gets no override sheet')
        # the coordinator: a Needs Your Hand row
        await sign_in(pg, 'u_chen')
        row = await pg.evaluate("() => nyhRows().find(r => r.key.startsWith('stk:split:'))")
        c.ok(bool(row) and '12' in row['title'] and 'buy only 12' in row['why'], f'split: the coordinator has a Needs Your Hand row, got {row}')
        c.ok(bool(row) and 'waste nothing' in row['why'].lower(), 'split: the row cites the Standard (waste nothing)')
        # the driver: the pick on his day plan and his route
        await sign_in(pg, 'u_alex')
        plan = await pg.evaluate("() => planDriverDay('Alex').stops.flatMap(s => s.lines).join(' | ')")
        c.ok('Load 12 sheet 5/8" Type X drywall' in plan, f'split: the pick is on the driver day plan, got {plan[:300]!r}')
        await go(pg, 'route')
        card = await pg.evaluate("() => { const c = document.getElementById('stk-route'); return c ? { text: c.innerText, n: +c.querySelector('[data-stkn]').dataset.stkn, rows: c.querySelectorAll('[data-stkov]').length, pred: PRED.stockPicks.count() } : null; }")
        c.ok(bool(card) and 'Warehouse' in card['text'] and card['rows'] == 1, f'split: the driver route shows the pick with Override, got {card}')
        c.ok(bool(card) and card['n'] == card['rows'] == card['pred'], f'split: Picks from Stock count equals its rows and PRED, got {card}')
        sw = await pg.evaluate("() => document.scrollingElement.scrollWidth")
        c.ok(sw <= 390, f'split: the driver route has no sideways scroll, scrollWidth {sw}')
        await reload(pg)
        got = await pg.evaluate(f"() => {{ const r = {LAST}; return {{ splits: (DB.stock || {{}}).splits.length, items: r.items.map(i => [i.qty, i.invId]) }}; }}")
        c.ok(got['splits'] == 1 and got['items'] == [[12, 'iv16'], [12, '']], f'split: survives a reload, got {got}')
        c.ok(not errs, f'split: page errors {errs[:3]}')
    finally:
        await b.close()

# ------------------------------------------------------------------------------------------------ override
async def s_override(p, c):
    b, pg, errs = await open_app(p, phone=True)
    try:
        await foreman_request(pg, '24 sheets 5/8" Type X drywall')
        await pg.evaluate("() => mbCloseModal()")
        await sign_in(pg, 'u_alex'); await go(pg, 'route')
        await pg.locator('#stk-route [data-stkov]').first.click(); await pg.wait_for_timeout(400)
        await modal_submit(pg, {'reason': 'count', 'count': 5, 'note': 'only five on the rack'})
        got = await pg.evaluate(f"""() => {{ const r = {LAST}, iv = DB.inventory.find(i => i.id === 'iv16');
          return {{ qty: iv.qty, items: r.items.map(i => [i.qty, i.invId]), adj: DB.stock.adjust.map(a => [a.from, a.to, a.by, a.reason]),
                   ov: DB.stock.overrides.map(o => [o.by, o.reasonLabel, o.qty, !!o.at]) }}; }}""")
        c.ok(got['qty'] == 5, f'override: the count is corrected to 5, got {got["qty"]}')
        c.ok(got['adj'] == [[12, 5, 'Alex', 'Count was wrong']], f'override: the adjustment is logged, got {got["adj"]}')
        c.ok(sorted(got['items']) == sorted([[5, 'iv16'], [19, '']]), f'override: 5 stay from stock and 19 are bought, got {got["items"]}')
        c.ok(got['ov'] == [['Alex', 'Count was wrong', 7, True]], f'override: who, why, how many moved to buying and when are recorded, got {got["ov"]}')
        t = await pg.evaluate(TOAST)
        c.ok('Count was wrong' in t['text'] and t['open'], f'override: the toast says it with Open, got {t}')
        rc = await pg.evaluate("() => stockRecounts().map(i => i.id)")
        c.ok(rc == ['iv16'], f'override: the corrected item comes back for a recount, got {rc}')
        await go(pg, 'route')
        await pg.locator('#stk-route [data-stkcount="iv16"]').click(); await pg.wait_for_timeout(300)
        await modal_submit(pg, {'count': 5})
        rc = await pg.evaluate("() => stockRecounts().length")
        c.ok(rc == 0, f'override: Count This clears the recount, {rc} left')
        # the coordinator, from Needs Your Hand, with a reason
        await foreman_request(pg, '24 sheets 5/8" moisture-resistant drywall')
        await pg.evaluate("() => mbCloseModal()")
        await sign_in(pg, 'u_chen')
        key = await pg.evaluate("() => (nyhRows().find(r => r.key.startsWith('stk:split:') && /moisture/.test(r.title)) || {}).key")
        c.ok(bool(key), 'override: the coordinator has the new split on Needs Your Hand')
        await pg.evaluate("k => nyhRun(k, true)", key); await pg.wait_for_timeout(300)
        await modal_submit(pg, {'reason': 'damaged', 'note': 'water damage on the bottom sheets'})
        got = await pg.evaluate(f"() => {{ const r = {LAST}; return {{ items: r.items.map(i => [i.qty, i.invId]), ov: DB.stock.overrides.slice(-1).map(o => [o.by, o.role, o.reasonLabel, o.qty])[0], avail: invAvailable(DB.inventory.find(i => i.id === 'iv17')) }}; }}")
        c.ok(got['items'] == [[24, '']], f'override: Damaged buys all 24, got {got["items"]}')
        c.ok(got['ov'] == ['Chen Biron', 'coord', 'Damaged', 8], f'override: the coordinator override is recorded, got {got["ov"]}')
        c.ok(got['avail'] == 8, f'override: the stock is free again, got {got["avail"]}')
        q = await pg.evaluate("() => ({ ov: erpQuery({ entity: 'stockoverrides' }).rows.length, adj: erpQuery({ entity: 'stockadjustments' }).rows.length })")
        c.ok(q == {'ov': 2, 'adj': 2}, f'override: overrides and adjustments are queryable, got {q}')
        await sign_in(pg, 'u_owner'); await go(pg, 'inv')
        pat = await pg.evaluate("() => { const c = document.getElementById('stk-patterns'); return c ? { n: +c.querySelector('[data-stkpat]').dataset.stkpat, rows: c.querySelectorAll('.stk-ovrow').length } : null; }")
        c.ok(bool(pat) and pat['n'] == pat['rows'] == 2, f'override: the owner sees Override Patterns, count equals rows, got {pat}')
        await sign_in(pg, 'u_chen'); await go(pg, 'inv')
        c.ok(not await pg.evaluate("() => !!document.getElementById('stk-patterns')"), 'override: Override Patterns is the owner\'s only')
        await reload(pg)
        n = await pg.evaluate("() => [DB.stock.overrides.length, DB.stock.adjust.length, DB.inventory.find(i => i.id === 'iv16').qty]")
        c.ok(n == [2, 2, 5], f'override: survives a reload, got {n}')
        c.ok(not errs, f'override: page errors {errs[:3]}')
    finally:
        await b.close()

# ------------------------------------------------------------------------------------------------ spec
async def s_spec(p, c):
    b, pg, errs = await open_app(p, phone=True)
    try:
        await pg.evaluate("() => { DB.inventory = DB.inventory.filter(i => i.id !== 'iv16'); save(); }")
        await foreman_request(pg, '24 sheets 5/8" Type X drywall')
        got = await pg.evaluate(f"() => {{ const r = {LAST}; return {{ items: r.items.map(i => [i.qty, i.invId, !!i.stockQ]), splits: DB.stock.splits.length, q: DB.stock.questions.map(q => [q.level, q.invId, q.state]) }}; }}")
        c.ok(got['items'] == [[24, '', True]] and got['splits'] == 0, f'spec: moisture-resistant stock does not split a Type X request, got {got}')
        c.ok(got['q'] == [['near', 'iv17', 'open']], f'spec: it raises a question, got {got["q"]}')
        m = await pg.evaluate("() => (document.querySelector('#mbm') || {}).innerText || ''")
        c.ok('Checking the stock' in m, f'spec: the foreman is told it is being checked, got {m[:200]!r}')
        await pg.evaluate("() => mbCloseModal()")
        await sign_in(pg, 'u_chen')
        row = await pg.evaluate("() => nyhRows().find(r => r.key.startsWith('stk:q:'))")
        c.ok(bool(row) and 'Type X' in row['why'] and row['verb'] == 'Same Item', f'spec: the coordinator gets the question, got {row}')
        await pg.evaluate("k => nyhRun(k, true)", row['key']); await pg.wait_for_timeout(300)
        got = await pg.evaluate(f"() => ({{ q: DB.stock.questions[0].state, items: {LAST}.items.map(i => [i.qty, i.invId]) }})")
        c.ok(got == {'q': 'different', 'items': [[24, '']]}, f'spec: Not the Same buys as asked, got {got}')
        # no type named: a question, and Same Item makes the split
        await pg.evaluate("() => { DB.inventory.push(STOCK_SEED_ADD()[0]); save(); }")
        await foreman_request(pg, '24 sheets 5/8 sheetrock')
        got = await pg.evaluate(f"() => ({{ items: {LAST}.items.map(i => [i.qty, i.invId]), q: DB.stock.questions.slice(-1)[0] }})")
        c.ok(got['items'] == [[24, '']] and got['q']['level'] == 'uncertain', f'spec: a request with no type is asked, not assumed, got {got}')
        await pg.evaluate("() => mbCloseModal()")
        await sign_in(pg, 'u_chen')
        key = await pg.evaluate("() => nyhRows().find(r => r.key.startsWith('stk:q:')).key")
        await pg.evaluate("k => nyhRun(k)", key); await pg.wait_for_timeout(300)
        c.ok(await pg.evaluate("() => /Which Stock Is It/.test((document.querySelector('#mbm') || {}).innerText || '')"), 'spec: with two stock items that fit, the coordinator picks which')
        await modal_submit(pg, {'inv': 'iv16'})
        got = await pg.evaluate(f"() => {LAST}.items.map(i => [i.qty, i.invId])")
        c.ok(got == [[12, 'iv16'], [12, '']], f'spec: Same Item makes the split, got {got}')
        t = await pg.evaluate(TOAST)
        c.ok('12 from stock' in t['text'] and t['open'], f'spec: the toast says it with Open, got {t}')
        c.ok(not errs, f'spec: page errors {errs[:3]}')
    finally:
        await b.close()

# ------------------------------------------------------------------------------------------------ po
NEWPO = """(qty) => { const v = DB.vendors.find(x => !(vendorBlocked(x.name) || []).length) || DB.vendors[0];
  const po = { id: uid('po'), number: nextPO(), projectId: 'p121', vendor: v.name, vendorId: v.id, date: today(), expected: '', needBy: addWork(today(), 3),
    status: 'draft', shipTo: 'site', notes: '', lines: [{ id: uid('pl'), item: '5/8" Type X drywall 4x8', desc: '', qty: qty, unit: 'sheet', price: 17, materialId: '', line: '', code: '07', received: 0 }],
    tax: 0, shipping: 0, matchedTxns: [], createdBy: 'Chen Biron', type: 'materials', receipts: [], srcDocs: [], __v2: 1 };
  DB.pos.push(po); save(); return po.id; }"""
async def s_po(p, c):
    b, pg, errs = await open_app(p)
    try:
        await sign_in(pg, 'u_chen')
        pid = await pg.evaluate(NEWPO, 24)
        R = await pg.evaluate("id => poValid(DB.pos.find(x => x.id === id))", pid)
        c.ok(any('12 sheet of 5/8" Type X drywall 4x8 are in stock at Warehouse' in r for r in R), f'po: poValid names the stock, got {R}')
        await pg.evaluate("id => { const po = DB.pos.find(x => x.id === id); setCurrent('p121'); poAction(po, 'issue'); }", pid); await pg.wait_for_timeout(300)
        st = await pg.evaluate("id => DB.pos.find(x => x.id === id).status", pid)
        c.ok(st == 'draft', f'po: Issue is refused while the line buys stock, status {st}')
        t = await pg.evaluate(TOAST)
        c.ok('in stock' in t['text'] and t['open'], f'po: the refusal says why with Open, got {t}')
        await pg.evaluate("id => { setCurrent('p121'); poOpen = id; view = 'po'; render(); }", pid); await pg.wait_for_timeout(400)
        w = await pg.evaluate("() => [...document.querySelectorAll('.stk-warn')].map(e => e.innerText).join(' | ')")
        c.ok('In Stock' in w and 'Take 12 from Stock' in w and 'Override' in w, f'po: the PO page warns inline with Take and Override, got {w!r}')
        await pg.locator('[data-stktake]').first.click(); await pg.wait_for_timeout(500)
        got = await pg.evaluate("id => { const po = DB.pos.find(x => x.id === id), p = DB.projects.find(x => x.id === 'p121'), r = p.requests[p.requests.length - 1]; return { qty: po.lines[0].qty, pick: r.items.map(i => [i.qty, i.invId]), R: poValid(po) }; }", pid)
        c.ok(got['qty'] == 12 and got['pick'] == [[12, 'iv16']], f'po: Take From Stock reduces the line to 12 and puts 12 on the driver pick, got {got}')
        c.ok(not any('in stock' in r for r in got['R']), f'po: the line no longer buys stock, got {got["R"]}')
        await pg.evaluate("id => { const po = DB.pos.find(x => x.id === id); setCurrent('p121'); poAction(po, 'issue'); }", pid); await pg.wait_for_timeout(300)
        st = await pg.evaluate("id => DB.pos.find(x => x.id === id).status", pid)
        c.ok(st in ('issued', 'pending'), f'po: it issues once reduced, status {st}')
        # an override clears another line; the PM sees no Override
        pid2 = await pg.evaluate(NEWPO, 8)
        await pg.evaluate("() => { const sp = DB.stock.splits; DB.inventory.find(i => i.id === 'iv16').qty = 20; save(); }")
        await sign_in(pg, 'u_alan')
        await pg.evaluate("id => { setCurrent('p121'); poOpen = id; view = 'po'; render(); }", pid2); await pg.wait_for_timeout(400)
        c.ok(await pg.evaluate("() => !document.querySelector('[data-stkovline]') && !!document.querySelector('.stk-warn')"), 'po: the PM sees the warning but no Override')
        await sign_in(pg, 'u_chen')
        await pg.evaluate("id => { setCurrent('p121'); poOpen = id; view = 'po'; render(); }", pid2); await pg.wait_for_timeout(400)
        await pg.locator('[data-stkovline]').first.click(); await pg.wait_for_timeout(300)
        await modal_submit(pg, {'reason': 'reserved', 'note': 'held for 206 Lenox'})
        R = await pg.evaluate("id => poValid(DB.pos.find(x => x.id === id))", pid2)
        c.ok(not any('in stock' in r for r in R), f'po: the override clears the line, got {R}')
        ov = await pg.evaluate("() => DB.stock.overrides.slice(-1).map(o => [o.kind, o.reasonLabel, o.by])[0]")
        c.ok(ov == ['po', 'Reserved for another job', 'Chen Biron'], f'po: the PO override is recorded, got {ov}')
        c.ok(not errs, f'po: page errors {errs[:3]}')
    finally:
        await b.close()

# ------------------------------------------------------------------------------------------------ after
async def s_after(p, c):
    b, pg, errs = await open_app(p)
    try:
        await sign_in(pg, 'u_owner')
        a = await pg.evaluate("() => paAsk('do we have 5/8 drywall in stock').headline")
        c.ok('20 sheets' in a and 'Type X' in a and 'moisture-resistant' in a, f'after: Ask answers the stock, got {a!r}')
        n0 = await pg.evaluate("() => boughtWhileInStock().length")
        c.ok(n0 == 0, f'after: nothing flagged in the seed, got {n0}')
        await pg.evaluate("""() => { DB.txns.push({ id: 'tstk1', date: today(), acct: 'ac2', desc: 'HOME DEPOT #6166 BROOKLYN NY', amt: -201.6, cat: 'materials', projectId: 'p121',
          code: '07', vendor: 'Home Depot', memo: '5/8" Type X drywall 4x8', status: 'categorized', actor: 'Chen', source: 'test', line: 'estimate:es1:l6', qty: 12, unit: 'sheet', extId: '' }); save(); }""")
        got = await pg.evaluate("() => ({ rows: boughtWhileInStock().length, pred: PRED.boughtWhileInStock.count(), catch: CATCH.find(x => x.name === 'boughtWhileInStock').rows().length, abnormal: CATCH.find(x => x.name === 'boughtWhileInStock').abnormal })")
        c.ok(got == {'rows': 1, 'pred': 1, 'catch': 1, 'abnormal': True}, f'after: the card purchase is flagged, count equals rows, got {got}')
        a = await pg.evaluate("() => paAsk('what did we buy this month that we had in stock')")
        c.ok('1 purchase' in a['headline'] and any('HOME DEPOT' in w for w in a['work']), f'after: Ask lists it, got {a["headline"]!r}')
        await sign_in(pg, 'u_chen')
        await pg.evaluate("() => CATCH.find(x => x.name === 'boughtWhileInStock').rows()[0].run()"); await pg.wait_for_timeout(300)
        await modal_submit(pg, {'reason': 'trip', 'note': 'needed in an hour, the yard is across town'})
        got = await pg.evaluate("() => ({ rows: boughtWhileInStock().length, pred: PRED.boughtWhileInStock.count(), ov: DB.stock.overrides.slice(-1).map(o => [o.kind, o.txnId])[0] })")
        c.ok(got == {'rows': 0, 'pred': 0, 'ov': ['card', 'tstk1']}, f'after: the override after the fact clears it, got {got}')
        # stock used on a job is its cost; returns credit it; cost-plus leftovers go to the PM
        await sign_in(pg, 'u_alex')
        await pg.evaluate("""() => { setCurrent('p121'); const r = addRequest({ items: [{ what: '5/8" Type X drywall', qty: 4, unit: 'sheet' }] }, 'Angel');
          requestAction('p121', r.id, 'delivered'); save(); }""")
        u = await pg.evaluate("() => DB.stock.use.map(x => [x.kind, x.qty, x.amount, x.line])")
        c.ok(u == [['use', 4, 67.2, 'estimate:es1:l6']], f'after: stock delivered to the job is its cost on the line, got {u}')
        await go(pg, 'route')
        await pg.locator('#stk-route [data-stkreturn]').click(); await pg.wait_for_timeout(300)
        await modal_submit(pg, {'pid': 'p121', 'inv': 'iv16', 'qty': 2, 'loc': 'wh'})
        got = await pg.evaluate("() => ({ use: DB.stock.use.slice(-1).map(x => [x.kind, x.amount])[0], qty: DB.inventory.find(i => i.id === 'iv16').qty })")
        c.ok(got == {'use': ['return', -33.6], 'qty': 10}, f'after: Return to Stock puts it back and credits the job, got {got}')
        await pg.evaluate("() => { DB.projects.find(p => p.id === 'p121').project.contractType = 'cost-plus'; save(); }")
        await pg.evaluate("() => stockReturn({ projectId: 'p121', invId: 'iv16', qty: 1, loc: 'wh' })")
        got = await pg.evaluate("() => ({ qty: DB.inventory.find(i => i.id === 'iv16').qty, surplus: DB.stock.surplus.length })")
        c.ok(got == {'qty': 10, 'surplus': 1}, f'after: cost-plus leftovers are not returned on their own, got {got}')
        await sign_in(pg, 'u_alan')
        row = await pg.evaluate("() => nyhRows().find(r => r.key.startsWith('stk:surplus:'))")
        c.ok(bool(row) and 'Client-owned surplus' in row['title'], f'after: the PM is asked about client-owned surplus, got {row}')
        # a pick not made in five days is released
        await pg.evaluate("""() => { setCurrent('p121'); addRequest({ items: [{ what: '5/8" moisture-resistant drywall', qty: 6, unit: 'sheet' }] }, 'Angel');
          DB.stock.splits.slice(-1)[0].at = iso(addDays(parse(today()), -6)) + 'T08:00:00'; save(); }""")
        n = await pg.evaluate("() => stockSweep()")
        got = await pg.evaluate("() => ({ avail: invAvailable(DB.inventory.find(i => i.id === 'iv17')), ev: DB.stock.events.length })")
        c.ok(n == 1 and got == {'avail': 8, 'ev': 1}, f'after: a stale pick is released, got {n} {got}')
        await sign_in(pg, 'u_chen')
        c.ok(await pg.evaluate("() => nyhRows().some(r => r.key.startsWith('stk:exp:'))"), 'after: the coordinator is told the stock was released')
        await reload(pg)
        got = await pg.evaluate("() => [DB.stock.use.length, DB.stock.surplus.length, DB.stock.events.length, boughtWhileInStock().length]")
        c.ok(got == [2, 1, 1, 0], f'after: survives a reload, got {got}')
        c.ok(not errs, f'after: page errors {errs[:3]}')
    finally:
        await b.close()

SECTIONS = {'split': s_split, 'override': s_override, 'spec': s_spec, 'po': s_po, 'after': s_after}
async def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--section', default=','.join(SECTIONS))
    a = ap.parse_args(); c = Checks()
    async with async_playwright() as p:
        for s in a.section.split(','):
            print('--', s); await SECTIONS[s](p, c)
    sys.exit(c.done())
asyncio.run(main())
