"""Items that fill themselves in (BACKLOG §1.18): one item library, one picker on every typed line.

Walked as the people who type the lines, on the seeded demo (app day 2026-09-03), desktop 1440 and phone 390:
  search    itemFind: words in any order and cut short, the field's Spanish trade words, most used first,
            the library's assemblies on the sell side only
  po        the coordinator types "calac" on a PO line for Nemo Tile: one picker (the native datalist is off), the
            last price paid at that vendor with its PO; Enter fills item, unit, vendor-facing description and price
            on the PO's own record (to the cent), the line says where it came from, the toast opens the item
  estimate  the PM adds a line on the draft estimate and picks "Porcelain tile": cost code 08, category, unit and a
            description in the house style land on the line; an assembly ("Bathroom gut and rebuild", 60 sq ft)
            adds its lines with quantities from the measure, and no second general-conditions line when the
            estimate already has one
  bill      a bill line picks an item; the bill's cost code fills when empty
  rfq       an RFQ line added after a pick carries the item's spec, cost code and library link
  request   the foreman on the phone types "40 2x4" and "cinta" in the request box: the items, no price anywhere,
            rows at least 44px, no sideways scroll; the line becomes "40 ea 2x4x8 KD studs"
  receipt   the driver's receipt line picks an item and its cost code
  learn     proposals from use, purchases and signed estimates; the owner approves (history: who, when, why) or
            declines (not proposed again); the foreman cannot; a new price from a PO is proposed, approved, dated;
            approving never rewrites a sent document
  dialog    the item form holds the vendor's words, Spanish name, lead time, markup; saved and on the history
  query     erpQuery items: the owner reads the last price, the foreman reads no money
Screenshots: review/items_spanish/items_*.png.
    python3 items_test.py
"""
import asyncio, os
from harness import *

SHOTS = os.path.join(ROOT, 'review', 'items_spanish')
os.makedirs(SHOTS, exist_ok=True)


async def shot(pg, name):
    await pg.screenshot(path=os.path.join(SHOTS, f'items_{name}.png'))


async def picker(pg):
    return await pg.evaluate("""() => { const p = document.querySelector('.itp'); if (!p) return null;
      return { rows: [...p.querySelectorAll('.itp-row')].map(r => ({ text: r.innerText, h: Math.round(r.getBoundingClientRect().height), w: Math.round(r.getBoundingClientRect().right) })),
               head: (p.querySelector('.itp-h') || {}).innerText || '', sw: document.documentElement.scrollWidth }; }""")


async def type_into(pg, sel, text):
    await pg.click(sel)
    await pg.keyboard.type(text, delay=30)
    await pg.wait_for_timeout(250)


async def main():
    c = Checks()
    async with async_playwright() as p:
        # ------------------------------------------------------------------ search
        b, pg, errs = await open_app(p)
        await sign_in(pg, 'u_chen')
        S = await pg.evaluate("""() => ({
          stud: itemFind('stud', {side: 'buy'}).map(h => h.name),
          studs2: itemFind('kd 2x4', {side: 'buy'}).map(h => h.name),
          cinta: itemFind('cinta', {side: 'buy'}).map(h => h.name),
          porc: itemFind('porc til', {side: 'sell'}).map(h => h.name),
          asmSell: itemFind('bathroom gut', {side: 'sell'}).map(h => h.kind),
          asmBuy: itemFind('bathroom gut', {side: 'buy'}).map(h => h.kind),
          lib: itemLib().length, asm: itemLib().filter(x => x.kind === 'assembly').map(x => x.name) })""")
        c.ok('2x4x8 KD studs' in S['stud'], f"search: 'stud' finds the studs the field asked for ({S['stud']})")
        c.ok(S['studs2'][:1] == ['2x4x8 KD studs'], f"search: words in any order, 'kd 2x4' ({S['studs2']})")
        c.ok('Blue tape + 4 mil plastic' in S['cinta'], f"search: the crew's Spanish, 'cinta', finds the tape ({S['cinta']})")
        c.ok(S['porc'][:1] == ['Porcelain tile'], f"search: cut-short words, 'porc til', library first ({S['porc']})")
        c.ok('assembly' in S['asmSell'], 'search: an assembly is offered on a sell line')
        c.ok('assembly' not in S['asmBuy'], 'search: an assembly is never offered on a purchase line')
        c.ok(len(S['asm']) == 3, f"the library holds the three default assemblies ({S['asm']})")

        # ------------------------------------------------------------------ po (coordinator, desktop)
        await pg.evaluate("""() => { setCurrent('p121');
          DB.pos.push({ id: 'po_it1', number: 'PO-2026-971', projectId: 'p121', vendor: 'Nemo Tile', date: today(), status: 'draft', shipTo: 'site', notes: '',
            lines: [{ id: 'pl_it1', item: '', desc: '', qty: 300, unit: 'ea', price: 0, materialId: '', line: '', received: 0 }], tax: 0, shipping: 0, matchedTxns: [] });
          poOpen = 'po_it1'; view = 'po'; render(); }""")
        await pg.wait_for_timeout(400)
        sel = '#po-po_it1 tr[data-line="pl_it1"] input[data-f="item"]'
        c.ok(await pg.locator(sel).count() == 1, 'po: the draft PO line is on screen')
        await type_into(pg, sel, 'calac')
        P = await picker(pg)
        c.ok(P is not None and P['rows'], 'po: typing "calac" opens the item picker')
        if P and P['rows']:
            first = P['rows'][0]['text']
            c.ok('Calacatta porcelain 12x24' in first, f'po: the first row is the tile ({first!r})')
            c.ok('$12.50' in first and 'Nemo Tile' in first and 'PO-' in first, f'po: the row says what we paid this vendor last, with its PO ({first!r})')
        lst = await pg.evaluate(f"() => document.querySelector('{sel}').getAttribute('list')")
        c.ok(not lst, 'po: one picker on the line (no native datalist beside it)')
        await shot(pg, 'po_picker_desktop')
        await pg.keyboard.press('Enter')
        await pg.wait_for_timeout(500)
        L = await pg.evaluate("() => { const po = DB.pos.find(x => x.id === 'po_it1'); return JSON.parse(JSON.stringify(po.lines[0])); }")
        c.ok(L['item'] == 'Calacatta porcelain 12x24', f"po: the item is on the PO line ({L['item']})")
        c.ok(L['unit'] == 'sf', f"po: the unit came with it ({L['unit']})")
        c.ok(abs(L['price'] - 12.5) < 0.005, f"po: the price is the last paid at Nemo Tile, $12.50 ({L['price']})")
        c.ok(abs(L['qty'] * L['price'] - 3750.00) < 0.005, f"po: 300 sf at $12.50 is $3,750.00 to the cent ({L['qty'] * L['price']})")
        c.ok(bool(L['desc']) and 'Calacatta' in L['desc'], f"po: the vendor-facing description is filled ({L['desc']!r})")
        c.ok((L.get('fill') or {}).get('src') == 'bought' and 'price' in (L.get('fill') or {}).get('fields', []), f"po: the line records where it was filled from ({L.get('fill')})")
        c.ok('Nemo Tile' in ((L.get('fill') or {}).get('priceFrom') or ''), 'po: the price records its source (last paid at Nemo Tile)')
        T = await pg.evaluate("() => { const t = document.getElementById('toast'); return { text: t.innerText, link: !!t.querySelector('a.toast-open') }; }")
        c.ok('filled from what we bought before' in T['text'] and T['link'], f"po: the toast says what filled and has a link ({T['text']!r})")
        D = await pg.evaluate(f"() => {{ const i = document.querySelector('{sel}'); return i ? {{ cls: i.className, title: i.title }} : null; }}")
        c.ok(D and 'itp-filled' in D['cls'] and 'Nemo Tile' in D['title'], f'po: the filled field shows where it came from on screen ({D})')
        # the toast's link is Add to Library for an item the library does not hold yet: it opens the item form, named
        await pg.evaluate("() => document.querySelector('#toast a.toast-open').click()")
        await pg.wait_for_timeout(400)
        nm = await pg.evaluate("() => (document.getElementById('li-name') || {}).value || ''")
        c.ok(nm == 'Calacatta porcelain 12x24', f'po: the toast opens the item form for it ({nm!r})')
        await pg.evaluate("() => mbCloseModal()")
        # a library item on a PO: the vendor-facing description from the library, the code, the link
        await pg.evaluate("""() => { const po = DB.pos.find(x => x.id === 'po_it1'); po.lines.push({ id: 'pl_it2', item: '', desc: '', qty: 2, unit: 'ea', price: 0, materialId: '', line: '', received: 0 }); render(); }""")
        await pg.wait_for_timeout(300)
        sel2 = '#po-po_it1 tr[data-line="pl_it2"] input[data-f="item"]'
        await type_into(pg, sel2, 'door cab hard')
        await pg.keyboard.press('Enter'); await pg.wait_for_timeout(500)
        L2 = await pg.evaluate("() => JSON.parse(JSON.stringify(DB.pos.find(x => x.id === 'po_it1').lines[1]))")
        c.ok(L2['item'] == 'Door & cabinet hardware' and L2.get('libId') and L2.get('code') == '11', f"po: a library item brings its cost code and link ({L2.get('item')}, {L2.get('code')}, {L2.get('libId')})")

        # ------------------------------------------------------------------ bill (coordinator, desktop)
        await pg.evaluate("() => { setCurrent('p121'); view = 'ap'; render(); openBill(null); }")
        await pg.wait_for_timeout(400)
        await type_into(pg, 'tr[data-bl] input[data-f="desc"]', 'white oak')
        P = await picker(pg)
        c.ok(P and any('white oak' in r['text'] for r in P['rows']), 'bill: a bill line offers the item (white oak flooring)')
        await pg.keyboard.press('Enter'); await pg.wait_for_timeout(300)
        B = await pg.evaluate("() => ({ desc: document.querySelector('tr[data-bl] input[data-f=desc]').value, code: (document.getElementById('e-code') || {}).value })")
        c.ok('white oak' in B['desc'], f"bill: the line reads the item ({B['desc']!r})")
        c.ok(B['code'] == '09', f"bill: the bill's cost code filled from the item, 09 Flooring ({B['code']})")
        await pg.evaluate("() => { document.getElementById('scrim')?.classList.remove('on'); document.getElementById('drawer')?.classList.remove('on'); }")

        # ------------------------------------------------------------------ rfq (coordinator, desktop)
        rid = await pg.evaluate("() => { const r = rfqCreate({ projectId: 'p121', title: 'Item check', category: 'Lumber', needBy: '2026-09-10', lines: [] }); r.lines = []; window.rfqOpen = r.id; window.rfqTab = 'requests'; view = 'rfq'; render(); return r.id; }")
        await pg.wait_for_timeout(400)
        if await pg.locator('#rfq-b-item').count():
            await type_into(pg, '#rfq-b-item', 'porcelain tile')
            await pg.keyboard.press('Enter'); await pg.wait_for_timeout(250)
            await pg.fill('#rfq-b-qty', '120')
            await pg.click('#rfq-b-add'); await pg.wait_for_timeout(400)
            R = await pg.evaluate("id => JSON.parse(JSON.stringify(rfqById(id).lines))", rid)
            last = R[-1] if R else {}
            c.ok(last.get('item') == 'Porcelain tile' and last.get('qty') == 120 and last.get('unit') == 'sf', f'rfq: the line is the item, 120 sf ({last})')
            c.ok(last.get('costCode') == '08' and last.get('libId') and last.get('spec'), f"rfq: the line carries the item's cost code, link and spec for the vendor ({last.get('costCode')}, {last.get('libId')}, {last.get('spec')!r})")
        else:
            c.ok(False, 'rfq: the draft RFQ shows its Add a Line box')

        # ------------------------------------------------------------------ estimate (PM, desktop)
        await sign_in(pg, 'u_alan')
        await pg.evaluate("() => { view = 'clients'; clientOpen = 'cl121'; clientTab = 'fin'; docOpen = { kind: 'estimate', id: 'es13881' }; render(); }")
        await pg.wait_for_timeout(500)
        n0 = await pg.evaluate("() => findDoc(DB.clients.find(c => c.id === 'cl121'), 'estimate', 'es13881').lines.length")
        await pg.evaluate("() => document.querySelector('section.view.on [data-ctadd]').click()")
        await pg.wait_for_timeout(500)
        lid = await pg.evaluate("() => { const d = findDoc(DB.clients.find(c => c.id === 'cl121'), 'estimate', 'es13881'); return d.lines[d.lines.length - 1].id; }")
        esel = f'[data-ctl="{lid}"] input[data-ctf="item"]'
        c.ok(await pg.locator(esel).count() == 1, 'estimate: the new line is on screen')
        await pg.locator(esel).scroll_into_view_if_needed()
        await type_into(pg, esel, 'porcelain t')
        P = await picker(pg)
        c.ok(P and 'Porcelain tile' in P['rows'][0]['text'], f"estimate: the picker offers Porcelain tile first ({P and P['rows'][0]['text']!r})")
        await shot(pg, 'estimate_picker_desktop')
        await pg.keyboard.press('Enter'); await pg.wait_for_timeout(600)
        E = await pg.evaluate(f"() => JSON.parse(JSON.stringify(findDoc(DB.clients.find(c => c.id === 'cl121'), 'estimate', 'es13881').lines.find(l => l.id === '{lid}')))")
        c.ok(E['item'] == 'Porcelain tile', f"estimate: the line is the item ({E['item']})")
        c.ok(E.get('code') == '08' and E.get('cat') == 'materials', f"estimate: cost code 08 and the materials category came with it ({E.get('code')}, {E.get('cat')})")
        c.ok(E.get('unit') == 'sf', f"estimate: the unit came with it ({E.get('unit')})")
        c.ok(bool(E.get('desc')) and 'Includes' in E['desc'] and 'Excludes' in E['desc'], f"estimate: a description in the house style, with what is and is not included ({E.get('desc')!r})")
        c.ok((E.get('fill') or {}).get('src') == 'library' and E.get('libId'), 'estimate: the line records that it came from the library, with the link')
        # the assembly, on a fresh line
        await pg.evaluate("() => document.querySelector('section.view.on [data-ctadd]').click()")
        await pg.wait_for_timeout(500)
        lid2 = await pg.evaluate("() => { const d = findDoc(DB.clients.find(c => c.id === 'cl121'), 'estimate', 'es13881'); return d.lines[d.lines.length - 1].id; }")
        esel2 = f'[data-ctl="{lid2}"] input[data-ctf="item"]'
        await pg.locator(esel2).scroll_into_view_if_needed()
        await type_into(pg, esel2, 'bathroom gut')
        await pg.keyboard.press('Enter'); await pg.wait_for_timeout(500)
        c.ok(await pg.locator('#itasm-n').count() == 1, 'estimate: the assembly asks for its one measurement')
        await pg.fill('#itasm-n', '60')
        await pg.click('#mbm-ok'); await pg.wait_for_timeout(600)
        A = await pg.evaluate("""() => { const d = findDoc(DB.clients.find(c => c.id === 'cl121'), 'estimate', 'es13881');
          return { n: d.lines.length, tile: d.lines.filter(l => l.item === 'Porcelain tile').map(l => [l.qty, l.unit]), gc: d.lines.filter(l => /general conditions/i.test(l.item)).length,
                   permits: d.lines.filter(l => (l.code || lineCode(l, d)) === '14').length, asm: d.lines.filter(l => l.fill && l.fill.asm).map(l => l.item),
                   junk: d.lines.filter(l => /bathroom gut/i.test(l.item || '')).length }; }""")
        c.ok(len(A['asm']) >= 8 and all(x in A['asm'] for x in ['Demolition & disposal', 'Porcelain tile', 'Tile & waterproofing']), f"estimate: the assembly added its 8 parts ({A['asm']})")
        c.ok(A['permits'] == 1, f"estimate: permits are on the estimate once, as the Standard's general conditions require ({A['permits']})")
        c.ok(A['junk'] == 0, 'estimate: neither the typed words nor the assembly name are left behind as a line')
        c.ok([156, 'sf'] in A['tile'], f"estimate: tile is 60 sq ft x 2.6 = 156 sf from the measure ({A['tile']})")
        c.ok(A['gc'] == 1, f"estimate: no second general-conditions line, the estimate already has one ({A['gc']})")
        c.ok(A['n'] == n0 + 1 + len(A['asm']), f"estimate: lines {n0} + 1 picked + {len(A['asm'])} from the assembly ({A['n']})")
        await b.close()

        # ------------------------------------------------------------------ request (foreman, phone)
        b, pg, errs2 = await open_app(p, True)
        errs += errs2
        await sign_in(pg, 'u_angel'); await go(pg, 'req')
        await pg.wait_for_timeout(300)
        await type_into(pg, '#cp-text', '40 2x4')
        P = await picker(pg)
        c.ok(P and P['rows'] and '2x4x8 KD studs' in P['rows'][0]['text'], f"request: '40 2x4' offers the studs ({P and P['rows'][:1]})")
        if P:
            c.ok(all('$' not in r['text'] for r in P['rows']), 'request: the field sees no price in the picker')
            c.ok(all(r['h'] >= 44 for r in P['rows']), f"request: every row is at least 44px tall ({[r['h'] for r in P['rows']]})")
            c.ok(P['sw'] <= 390 and all(r['w'] <= 390 for r in P['rows']), 'request: the picker fits the phone, no sideways scroll')
        await shot(pg, 'request_picker_phone')
        await pg.locator('.itp .itp-row').first.click()
        await pg.wait_for_timeout(300)
        v = await pg.evaluate("() => document.getElementById('cp-text').value")
        c.ok(v.strip() == '40 ea 2x4x8 KD studs', f'request: the line reads "40 ea 2x4x8 KD studs" ({v!r})')
        await pg.keyboard.press('End')
        await pg.keyboard.type(', 2 cinta', delay=30); await pg.wait_for_timeout(300)
        P = await picker(pg)
        c.ok(P and any('Blue tape' in r['text'] for r in P['rows']), "request: the crew's Spanish, 'cinta', offers the tape")
        await pg.locator('.itp .itp-row').filter(has_text='Blue tape').first.click(); await pg.wait_for_timeout(300)
        v = await pg.evaluate("() => document.getElementById('cp-text').value")
        c.ok(v == '40 ea 2x4x8 KD studs, 2 case Blue tape + 4 mil plastic', f'request: the item after a comma is filled in its own unit ({v!r})')
        await b.close()

        # ------------------------------------------------------------------ receipt (driver, phone)
        b, pg, errs2 = await open_app(p, True)
        errs += errs2
        await sign_in(pg, 'u_alex'); await go(pg, 'files')
        await pg.evaluate("() => { setCurrent('p121'); spCaptureModal({ projectId: 'p121' }); }")
        await pg.wait_for_timeout(400)
        await type_into(pg, '#mbm tr[data-spl] input[data-slf="note"]', 'porcelain')
        P = await picker(pg)
        c.ok(P and P['rows'] and all('$' not in r['text'] for r in P['rows']), 'receipt: the driver gets items and no prices')
        await pg.locator('.itp .itp-row').first.click(); await pg.wait_for_timeout(500)
        R = await pg.evaluate("() => ({ note: (document.querySelector('#mbm tr[data-spl] [data-slf=note]') || {}).value, code: (document.querySelector('#mbm tr[data-spl] [data-slf=code]') || {}).value })")
        c.ok(R['note'] and 'orcelain' in R['note'] and R['code'] == '08', f'receipt: the line reads the item and its cost code ({R})')
        await shot(pg, 'receipt_phone')
        await b.close()

        # ------------------------------------------------------------------ learn (owner, desktop)
        b, pg, errs2 = await open_app(p)
        errs += errs2
        await sign_in(pg, 'u_angel')
        F = await pg.evaluate("() => { const P = itemProposals(); const t = document.getElementById('toast'); const ok = itemPropApprove(P[0].id); return { ok, n: P.length, n2: itemProposals().length }; }")
        c.ok(F['ok'] is False and F['n'] == F['n2'], 'learn: the foreman cannot change the library')
        # as the owner finds it: Settings, then Company Settings
        await sign_in(pg, 'u_owner'); await go(pg, 'setup')
        await pg.locator('#v-setup button', has_text='Company Settings').first.click()
        await pg.wait_for_timeout(500)
        L = await pg.evaluate("""() => { const card = document.getElementById('lib-card'); const pr = card && card.querySelector('[data-itprops]');
          return { h: card && card.querySelector('h3').textContent, n: pr ? +pr.dataset.itprops : 0, P: itemProposals().map(p => ({ id: p.id, kind: p.kind, itemId: p.itemId || '' })) }; }""")
        c.ok(L['h'] == 'Item Library', f"learn: the card is the Item Library ({L['h']})")
        c.ok(L['n'] == len(L['P']) and L['n'] > 0, f"learn: Proposed from Use shows every proposal, one number ({L['n']} vs {len(L['P'])})")
        await pg.locator('#lib-card').scroll_into_view_if_needed()
        await shot(pg, 'library_desktop')
        desc = next((x for x in L['P'] if x['kind'] == 'desc'), None)
        if desc:
            before = await pg.evaluate("""() => { const d = DB.clients.find(c => c.id === 'cl121').estimates.find(x => x.id === 'es1'); return d.lines.map(l => l.desc).join('|'); }""")
            await pg.evaluate("id => document.querySelector(`[data-itpok=\"${id}\"]`).click()", desc['id'])
            await pg.wait_for_timeout(400)
            it = await pg.evaluate("id => JSON.parse(JSON.stringify(itemLib().find(x => x.id === id)))", desc['itemId'])
            c.ok(bool(it.get('desc')), 'learn: approving writes the description on the item')
            h = (it.get('hist') or [{}])[-1]
            c.ok(h.get('by') and h.get('at', '').startswith('2026-09-03') and h.get('why'), f'learn: the item keeps who, when and why ({h})')
            after = await pg.evaluate("""() => { const d = DB.clients.find(c => c.id === 'cl121').estimates.find(x => x.id === 'es1'); return d.lines.map(l => l.desc).join('|'); }""")
            c.ok(before == after, 'learn: the signed estimate keeps its own words (the library never rewrites a sent document)')
            T = await pg.evaluate("() => document.getElementById('toast').innerText")
            c.ok(T.startswith('Approved:'), f'learn: the approval toasts ({T!r})')
        nxt = await pg.evaluate("() => itemProposals()[0]")
        if nxt:
            await pg.evaluate("id => itemPropDecline(id, 'we price this one per job')", nxt['id'])
            again = await pg.evaluate("id => itemProposals().some(p => p.id === id)", nxt['id'])
            dec = await pg.evaluate("id => DB.company.itemLibDeclined[id]", nxt['id'])
            c.ok(not again and dec and dec['why'] == 'we price this one per job', 'learn: a declined proposal is kept with its reason and not proposed again')
        # a new price: the coordinator buys Hardwood flooring at a new price; the library is told, the owner approves
        PR = await pg.evaluate("""() => { const it = itemLib().find(x => x.name === 'Hardwood flooring'); it.cost = 8; it.costAt = '2026-06-01';
          DB.pos.push({ id: 'po_it2', number: 'PO-2026-972', projectId: 'p121', vendor: 'Tino', date: '2026-09-02', status: 'issued', shipTo: 'site', notes: '',
            lines: [{ id: 'pl_it3', item: 'Hardwood flooring', desc: '', qty: 500, unit: 'sf', price: 9.4, materialId: '', line: '', received: 0 }], tax: 0, shipping: 0, matchedTxns: [] });
          pwFresh && pwFresh(); const P = itemProposals().find(p => p.kind === 'price' && p.itemId === it.id); return P ? { id: P.id, from: P.from, to: P.to, what: P.what } : null; }""")
        c.ok(PR and PR['from'] == 8 and abs(PR['to'] - 9.4) < 0.005, f'learn: a buy at $9.40 against the library\'s $8.00 is proposed ({PR})')
        if PR:
            await pg.evaluate("id => itemPropApprove(id)", PR['id'])
            it = await pg.evaluate("() => JSON.parse(JSON.stringify(itemLib().find(x => x.name === 'Hardwood flooring')))")
            c.ok(abs(it['cost'] - 9.4) < 0.005 and it['costAt'] == '2026-09-02' and 'Tino' in it.get('costSrc', ''), f"learn: the unit cost moves to $9.40, dated 9/2, from Tino's PO ({it['cost']}, {it['costAt']}, {it.get('costSrc')})")
        # ------------------------------------------------------------------ dialog
        await pg.evaluate("() => itemOpen(itemLib().find(x => x.name === 'Porcelain tile').id)")
        await pg.wait_for_timeout(300)
        c.ok(await pg.locator('#li-vdesc').count() == 1 and await pg.locator('#li-es').count() == 1, 'dialog: the item form holds the vendor\'s words and the Spanish name')
        await pg.fill('#li-vdesc', 'Porcelain tile, rectified, first quality; tell us the lot number.')
        await pg.fill('#li-es', 'loseta de porcelana')
        await pg.fill('#li-lead', '10')
        await pg.click('#mbm-ok'); await pg.wait_for_timeout(400)
        it = await pg.evaluate("() => JSON.parse(JSON.stringify(itemLib().find(x => x.name === 'Porcelain tile')))")
        c.ok(it.get('vendorDesc', '').startswith('Porcelain tile, rectified') and it.get('es') == 'loseta de porcelana' and it.get('leadDays') == 10, f'dialog: saved on the item ({it.get("vendorDesc")!r}, {it.get("es")!r}, {it.get("leadDays")})')
        c.ok((it.get('hist') or [{}])[-1].get('what') == 'edited', 'dialog: the edit is on the item\'s history')
        es = await pg.evaluate("() => itemFind('loseta porcelana', {side: 'buy'}).map(h => h.name)")
        c.ok(es[:1] == ['Porcelain tile'], f"dialog: the Spanish name finds the item ({es})")
        # ------------------------------------------------------------------ query
        Q = await pg.evaluate("() => { const r = erpQuery({ entity: 'items', where: { name: 'Calacatta porcelain 12x24' } }); return (r.rows || r)[0] || null; }")
        c.ok(Q and Q.get('unitPrice') == 12.5 and Q.get('lastVendor') == 'Nemo Tile', f'query: the owner reads the item with its last price ({Q})')
        await sign_in(pg, 'u_angel')
        Qf = await pg.evaluate("() => { const r = erpQuery({ entity: 'items', where: { name: 'Calacatta porcelain 12x24' } }); return (r.rows || r)[0] || null; }")
        c.ok(Qf and 'unitPrice' not in Qf and 'unitCost' not in Qf and 'price' not in Qf, f'query: the foreman reads the item without money ({Qf})')
        await b.close()
    c.ok(not errs, f'no page errors ({errs[:3]})')
    return c.done()

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
