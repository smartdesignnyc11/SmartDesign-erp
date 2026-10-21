"""The order's money and its vendor's papers (coordinator expert, 2026-10-21, two severity-1s). PO-2026-049 went to
Tino with no certificate of insurance on file and an order already open with them, and $34,800 went out on a $32,500
estimate line with nothing said. Now: the Order sheet says both as they are entered and stops them; the one validator
refuses them on every issue path; an overage needs a reason, and over $1,000 the owner approves it, with the
overage and the reason on the card. Desktop and phone.
Run: python3 po_gates_test.py"""
import asyncio
from harness import async_playwright, open_app, sign_in, Checks

ROW = """() => { const p = DB.projects.find(x => x.id === 'p121'); const r = buyList(p.id).find(x => x.kind === 'line' && /Trim, doors/.test(x.name));
  return r ? JSON.stringify(flRowKey(r)) : null }"""
SHEET = """(k) => { const o = JSON.parse(k); buyOrderDialog(o); return true }"""

async def sheet_state(pg):
    return await pg.evaluate("""() => { const m = document.getElementById('mbm'); const p = m.querySelector('.fl-paper'), o = m.querySelector('.fl-over');
      return { paper: p && !p.hidden ? p.textContent : '', paperBad: p && p.classList.contains('bad'), over: o && !o.hidden ? o.textContent : '',
        why: !!(o && !o.hidden && o.querySelector('[data-f="overWhy"]')) } }""")

async def main():
    c = Checks()
    async with async_playwright() as p:
        for phone in (False, True):
            tag = 'phone' if phone else 'desktop'
            b, pg, errs = await open_app(p, phone)
            await sign_in(pg, 'u_chen')
            r = await pg.evaluate("() => { const v = poVendorReal('Tino'); return v && { coi: v.insuranceExp || '', w9: !!v.w9, open: DB.pos.filter(x => x.vendor === 'Tino' && ['issued','partial','pending'].includes(x.status)).map(x => x.number) } }")
            c.ok(r and not r['coi'] and r['open'], f'{tag}: Tino is on file with no COI and an order open ({r})')
            key = await pg.evaluate(ROW)
            c.ok(bool(key), f'{tag}: the Trim, doors, paint & hardware line is on the Buy Board ({key})')
            pos0 = await pg.evaluate("() => DB.pos.length")
            # 1. the sheet: Tino is stopped as soon as he is chosen, and Issue PO creates nothing
            await pg.evaluate(SHEET, key); await pg.wait_for_timeout(300)
            await pg.select_option('#mbm [data-f="vendor"]', label='Tino'); await pg.wait_for_timeout(200)
            s = await sheet_state(pg)
            c.ok('no certificate of insurance' in s['paper'] and 'PO-2026-047' in s['paper'] and s['paperBad'], f'{tag}: the sheet says Tino has no COI and an order open ({s})')
            await pg.click('#mbm-ok'); await pg.wait_for_timeout(400)
            t = await pg.evaluate("() => document.getElementById('toast').innerText")
            n = await pg.evaluate("() => DB.pos.length")
            c.ok(n == pos0 and 'no certificate of insurance' in t, f'{tag}: Issue PO to Tino is refused and creates no order ({t!r}, {n - pos0} new)')
            # 2. the overage: $34,800 on the $32,500 line, with a vendor whose papers are on file
            await pg.select_option('#mbm [data-f="vendor"]', value='Carlos Millwork')
            await pg.fill('#mbm [data-f="qty"]', '1'); await pg.fill('#mbm [data-f="price"]', '34800'); await pg.wait_for_timeout(200)
            s = await sheet_state(pg)
            c.ok('$2,300' in s['over'] and 'owner approves' in s['over'] and s['why'] and not s['paper'], f'{tag}: the sheet says $2,300 over the line, asks why ({s})')
            await pg.click('#mbm-ok'); await pg.wait_for_timeout(400)
            t = await pg.evaluate("() => document.getElementById('toast').innerText")
            c.ok(await pg.evaluate("() => DB.pos.length") == pos0 and '$2,300' in t and 'say why' in t, f'{tag}: no reason, no order ({t!r})')
            await pg.fill('#mbm [data-f="overWhy"]', 'Carlos repriced the oak casing; a change order follows'); await pg.click('#mbm-ok'); await pg.wait_for_timeout(700)
            po = await pg.evaluate("""() => { const po = DB.pos[DB.pos.length - 1]; return { n: DB.pos.length, no: po.number, st: po.status, why: po.overReason && po.overReason.why, by: po.overReason && po.overReason.by,
              over: po.overReason && po.overReason.over, toast: document.getElementById('toast').innerText } }""")
            c.ok(po['n'] == pos0 + 1 and po['st'] == 'pending' and po['over'] == 2300 and 'repriced' in (po['why'] or '') and po['by'], f'{tag}: with a reason it goes to the owner, the reason kept with who ({po})')
            c.ok('$2,300 over' in po['toast'] and 'sent for the owner' in po['toast'], f'{tag}: the toast says the overage, not only the threshold ({po["toast"]!r})')
            # 3. the owner's card says the overage and the reason; approving issues it
            await sign_in(pg, 'u_owner')
            card = await pg.evaluate("(no) => { const x = mApprovals().find(a => a.kind === 'po' && a.title.startsWith(no)); return x && { d: x.detail, sev: x.sev } }", po['no'])
            c.ok(card and '$2,300 over what is left on Trim, doors' in card['d'] and 'repriced' in card['d'] and card['sev'] == 'bad', f'{tag}: the owner card carries the overage and why ({card})')
            st = await pg.evaluate("(no) => { const po = DB.pos.find(x => x.number === no); apprPOYes({ id: po.id }); return po.status }", po['no'])
            c.ok(st == 'issued', f'{tag}: the owner approves and it issues ({st})')
            # 4. every issue path: a draft over the line with no reason is refused by poAction itself; the order page says it
            r = await pg.evaluate("""() => { const src = DB.pos.find(x => x.number === '%s'); const po = JSON.parse(JSON.stringify(src));
              Object.assign(po, { id: 'po_gt', number: 'PO-GT-1', status: 'draft' }); delete po.overReason; po.lines.forEach(l => { l.id = l.id + 'x'; l.price = 5000; });
              DB.pos.push(po); poAction(po, 'issue'); return { st: po.status, v: poValid(po) } }""" % po['no'])
            c.ok(r['st'] == 'draft' and any('say why on the order' in x for x in r['v']), f'{tag}: a draft over the line with no reason does not issue from the order page ({r})')
            h = await pg.evaluate("() => renderPODoc(DB.pos.find(x => x.id === 'po_gt'))")
            c.ok('Over the Estimate Line' in h and 'data-poover' in h, f'{tag}: the order page says it with Give the Reason')
            # under $1,000 over: a reason, no owner
            r = await pg.evaluate("""() => { signIn('u_chen'); const po = DB.pos.find(x => x.id === 'po_gt'); const L = poLineOver(po)[0]; po.lines[0].price = L.left + 400;
              po.overReason = { by: 'Chen', at: appNowIso(), why: 'freight added by the yard', over: poOverTotal(po) }; poAction(po, 'issue'); return { st: po.status, over: poOverTotal(po) } }""")
            c.ok(r['st'] == 'issued' and 399 < r['over'] < 401, f'{tag}: $400 over with a reason issues without the owner ({r})')
            # a reason covers the overage it was given for, not a higher price later
            r = await pg.evaluate("""() => { const po = JSON.parse(JSON.stringify(DB.pos.find(x => x.id === 'po_gt'))); Object.assign(po, { id: 'po_gt2', number: 'PO-GT-2', status: 'draft' });
              DB.pos.push(po); po.overReason = { by: 'Chen', at: appNowIso(), why: 'freight added by the yard', over: 100 }; return poValid(po).some(x => /say why/.test(x)) }""")
            c.ok(r, f'{tag}: a higher price than the reason covered asks again')
            # 5. papers: no W-9 is said, not stopped; a vendor with a current COI and no open order is not stopped
            r = await pg.evaluate("() => { const P = poPaper({ id: '', vendor: 'Nemo Tile', type: 'materials', lines: [{ qty: 1, price: 900 }] }); return P }")
            c.ok(not r['stop'] and any('No W-9 from Nemo Tile' in x for x in r['warn']), f'{tag}: Nemo Tile, no W-9: said, not stopped ({r})')
            r = await pg.evaluate("() => [poPaper({ id: '', vendor: 'Window Works', type: 'materials', lines: [{ qty: 1, price: 900 }] }).stop, poPaper({ id: '', vendor: 'Window Works', type: 'service', lines: [{ qty: 1, price: 900 }] }).stop]")
            c.ok(not r[0] and any('expired' in x and 'on site' in x for x in r[1]), f'{tag}: Window Works, COI expired 8/15, its order received: goods may be ordered, a service visit is stopped ({r})')
            # issued orders already out are not re-judged (the lesson scan reads poValid on them)
            r = await pg.evaluate("() => poValid(DB.pos.find(x => x.number === 'PO-2026-047'))")
            c.ok(not any('certificate' in x or 'over what is left' in x for x in r), f'{tag}: an issued order is not re-judged ({r})')
            c.ok(not errs, f'{tag}: no page errors ({errs[:3]})')
            await b.close()
    c.done()

asyncio.run(main())
