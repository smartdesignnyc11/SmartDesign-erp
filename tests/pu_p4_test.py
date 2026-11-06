"""Purchasing lane P4: Quotes, the Request for Quote record, the request sheet, bid intake and leveling, the award and
the assistant's purchasing answers (the coordinator expert's review, 11-05: scratchpad pu_review/coord S1_/S2_ shots).
Each section runs in a fresh browser (fresh seeded DB, app day 2026-09-03).

  new     S1  New Request for Quote is the same sheet opened empty (one path, two doors).
  sheet   S1  Ask for Quotes opens a request sheet prefilled from the picked lines (rfqStartFromLines): item-level
              lines with quantity and unit, scope, due date and vendors suggested by trade and history; nothing is
              created until Send or Save; the record is headed "Request for Quote", the list "Quotes", never "RFQs".
  three   S1  Over $2,500 a request goes to three vendors, or a reason is logged in the Standard's words; a vendor can
              be added after the request went out.
  match   S1  A quote from the mail prices a Buy Board line only when the trades match (the windows quote is not the
              paint line), each match says why, and bulk apply is never the blue button and never prices a line.
  prose   S1  Prices written in prose are read ("$19,400 lump sum", "Total 15,550", "twenty one thousand eight
              hundred"); a reply with no price is Price Needed and the request is never Leveled on it; sub labour is
              leveled without sales tax, on scope, against the line's budget.
  award   S1  The award's saving compares pre-tax totals: $3,850 against the next-best bid, never the sales tax.
  status  S1  One status per need: rfqLineState(lineKey) says draft, out, price needed, leveled or awarded; a draft
              request is never "waiting on the vendors"; after an award the line is not "Ask for Bids".
  ask     S2  The assistant maps "warehouse" to Stock, answers "what is owed back" with the Orders tile's figure, and
              tells a foreman what was ordered for his job with no dollars.
  phone   S1  Phone: request cards show Budget, Quotes In and Due; vendor rows are 44px; nothing scrolls sideways.

    python3 pu_p4_test.py [--section sheet,three,...]
"""
import asyncio, re, sys, argparse
from harness import *

MODAL = """() => { const m = document.querySelector('#mbm'); if (!m || !m.getClientRects().length) return null;
  return { title: (m.querySelector('.mbm-hd h3') || {}).innerText || '', text: m.innerText,
           buttons: [...m.querySelectorAll('button')].filter(b => b.getClientRects().length).map(b => b.innerText.trim()).filter(Boolean),
           primary: [...m.querySelectorAll('button.primary')].filter(b => b.getClientRects().length).map(b => b.innerText.trim()) }; }"""
TOAST = """() => { const t = document.getElementById('toast'); if (!t) return { text: '', open: false };
  return { text: t.innerText.trim(), open: !!t.querySelector('.toast-open') }; }"""
HSCROLL = "() => document.documentElement.scrollWidth - innerWidth"

async def modal(pg): return await pg.evaluate(MODAL)
async def toast(pg): return await pg.evaluate(TOAST)

# Three demolition subs with mail on file, and the demolition line's request sent to them (the coordinator's walk).
SUBS_JS = """() => {
  const S3 = [['vsub_gow', 'Gowanus Demo Corp', 'NYC Manhattan/Brooklyn', 'bids@gowanusdemo.example'],
              ['vsub_jsy', 'Jersey Strip-Out LLC', 'NY-NJ-CT', 'office@jerseystrip.example'],
              ['vsub_qns', 'Queens Wrecking Co', 'NYC other boroughs', 'est@queenswreck.example']];
  S3.forEach(([id, name, region, email]) => DB.vendors.some(v => v.id === id) || DB.vendors.push({ id, name, trade: 'Demolition', kind: 'sub', region, email, contact: name, insuranceExp: '2027-06-30', w9: true }));
  const r = rfqFromLines('p121', ['estimate:es1:l1'], { sub: true, category: 'Demolition' });
  r.status = 'purchasing';
  const ok = rfqSend(r, S3.map(x => x[0]), today());
  return { id: r.id, number: r.number, ok, status: r.status, sub: !!r.sub };
}"""
def replies_js(texts):
    return """([id, T]) => { const r = rfqById(id), M = { vsub_gow: 'bids@gowanusdemo.example', vsub_jsy: 'office@jerseystrip.example', vsub_qns: 'est@queenswreck.example' };
  Object.entries(T).forEach(([vid, text], i) => DB.comms.push({ id: 'p4c_' + id + '_' + vid, from: { email: M[vid], name: vid }, subject: 'Re: ' + r.number + ' — Demolition', text, date: today(), direction: 'in', proposals: [], channel: 'email' }));
  rfqIngest(); return { status: r.status, quotes: (r.quotes || []).map(q => ({ v: q.vendorId, unreadable: !!q.unreadable, need: !!q.priceNeeded, lines: q.lines.map(x => x.unit), inc: q.includes || '', exc: q.excludes || '' })) }; }"""
PROSE = {'vsub_gow': 'Chen, for 121 State St garden unit and 3rd floor demo incl. 3 x 20yd dumpsters and floor protection: $19,400 lump sum. Start 5 working days from award. Permit by others.',
         'vsub_jsy': 'Demo 121 State: labor $11,200, dumpsters 3 @ $1,150 = $3,450, protection $900. Total 15,550. Crew available next Wed.',
         'vsub_qns': 'We can do it for twenty one thousand eight hundred, everything included. Two weeks out.'}

async def s_sheet(p, c):
    b, pg, errs = await open_app(p)
    try:
        await sign_in(pg, 'u_chen')
        has = await pg.evaluate("() => typeof rfqStartFromLines === 'function'")
        c.ok(has, 'sheet: rfqStartFromLines(items, opts) exists for the Buy Board to call')
        if not has: return
        st = await pg.evaluate("""() => { const p = DB.projects.find(x => x.id === 'p121'), m = p.materials.find(x => /parlor kitchen countertop slab/i.test(x.name));
          const n0 = DB.rfqs.length; rfqStartFromLines([{ key: 'estimate:es1:l9', materialId: m.id }]); return { n0, n1: DB.rfqs.length, mid: m.id }; }""")
        await pg.wait_for_timeout(400)
        m = await modal(pg)
        c.ok(m and 'request for quote' in m['title'].lower(), f'sheet: Ask for Quotes opens a Request for Quote sheet ({m and m["title"]})')
        c.ok(st['n1'] == st['n0'], f'sheet: nothing is created before Send or Save ({st})')
        if not m: return
        items = await pg.evaluate("() => [...document.querySelectorAll('#mbm [data-rsi]')].map(i => i.value)")
        c.ok(items == ['Parlor kitchen countertop slab'], f'sheet: the line is the material picked (the slab), not the whole millwork line ({items})')
        flds = await pg.evaluate("() => [...document.querySelectorAll('#mbm [data-rsq], #mbm [data-rsu], #mbm [data-f=due], #mbm [data-f=scope]')].map(e => e.dataset.rsq ? 'qty' : e.dataset.rsu ? 'unit' : e.dataset.f)")
        c.ok(all(k in flds for k in ('qty', 'unit', 'due', 'scope')), f'sheet: quantity, unit, scope and due date are on the sheet ({flds})')
        ticks = await pg.evaluate("() => [...document.querySelectorAll('#mbm [data-rsv]')].map(i => [i.closest('label').innerText.split('\\n')[0], i.checked])")
        on = [t for t, k in ticks if k]
        c.ok(any('Carlos Millwork' in t for t in on), f'sheet: the millwork vendor is suggested and ticked ({on})')
        c.ok(not any(re.search(r'lumber', t, re.I) for t in on), f'sheet: no lumber yard ticked for millwork ({on})')
        why = await pg.evaluate("() => { const i = [...document.querySelectorAll('#mbm [data-rsv]')].find(x => /carlos/i.test(x.closest('label').innerText)); return i ? i.closest('label').innerText : ''; }")
        c.ok(re.search(r'millwork', why, re.I) and re.search(r'order|history|\$', why, re.I), f'sheet: the suggestion says why: trade and history ({why[:160]})')
        c.ok(m['buttons'] and any(re.match(r'^Send', x) for x in m['buttons']) and any(re.match(r'^Save', x) for x in m['buttons']), f'sheet: Send and Save ({m["buttons"]})')
        c.ok(len(m['primary']) == 1, f'sheet: one blue button ({m["primary"]})')
        await pg.locator('#mbm #mbm-alt').click(); await pg.wait_for_timeout(600)
        t = await toast(pg)
        r = await pg.evaluate("() => { const r = DB.rfqs[DB.rfqs.length - 1]; return r && { number: r.number, n: r.lines.length, item: r.lines[0].item, from: r.lines[0].fromLine, mat: r.lines[0].materialId, unit: r.lines[0].unit, status: r.status }; }")
        c.ok(r and r['item'] == 'Parlor kitchen countertop slab' and r['from'] == 'estimate:es1:l9' and r['mat'] == st['mid'], f'sheet: Save creates the request, its line linked to the estimate line and the material ({r})')
        c.ok(r and r['number'] in t['text'] and t['open'], f'sheet: the toast names it with Open ({t})')
        await pg.evaluate("n => rfqOpenFor(n)", r['number']); await pg.wait_for_timeout(400)
        h = await pg.evaluate("() => [...document.querySelectorAll('#v-rfq h2, #v-rfq h3, #v-rfq button')].filter(e => e.getClientRects().length).map(e => e.innerText.trim())")
        c.ok(any(x.startswith('Request for Quote') for x in h), f'sheet: the record is headed Request for Quote ({h[:3]})')
        c.ok(not any(re.search(r'\bRFQs\b', x) for x in h), f'sheet: no heading or button says RFQs ({[x for x in h if "RFQs" in x]})')
        await pg.evaluate("() => { window.rfqOpen = ''; view = 'rfq'; render(); }"); await pg.wait_for_timeout(300)
        h2 = await pg.evaluate("() => [...document.querySelectorAll('#v-rfq h2')].filter(e => e.getClientRects().length).map(e => e.innerText.trim())")
        c.ok(h2 and h2[0] == 'Quotes', f'sheet: the list page is Quotes ({h2})')
        # Send from the sheet: one vendor over $2,500 is refused in place; with a reason it goes out, the foreman's check beside it
        await pg.evaluate("() => { DB.vendors.find(v => v.id === 'v3').email = 'shop@carlosmillwork.example'; rfqStartFromLines(['estimate:es1:l9']); }"); await pg.wait_for_timeout(400)
        await pg.evaluate("() => document.querySelectorAll('#mbm [data-rsv]').forEach(i => { i.checked = /carlos/i.test(i.closest('label').innerText); })")
        n0 = await pg.evaluate("() => DB.rfqs.length")
        await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(500)
        m2 = await modal(pg); t2 = await toast(pg)
        refused = await pg.evaluate("() => document.querySelector('#mbm') && document.querySelector('#mbm').innerText + ' ' + ((document.getElementById('toast') || {}).innerText || '')")
        c.ok(m2 is not None and await pg.evaluate("() => DB.rfqs.length") == n0, 'sheet: Send to one vendor over $2,500 with no reason keeps the sheet open and creates nothing')
        c.ok(re.search(r'three quotes', refused or '', re.I), f'sheet: it says why: three quotes ({(refused or "")[-200:]})')
        await pg.locator('#mbm [data-f="reason"]').fill('Only Carlos builds to our shop drawings')
        await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(600)
        s = await pg.evaluate("() => { const r = DB.rfqs[DB.rfqs.length - 1]; return { status: r.status, v: (r.vendors || []).length, fq: !!r.fewerQuotes, fm: rfqForemanRows().some(x => x.id === r.id), toast: (document.getElementById('toast') || {}).innerText || '' }; }")
        c.ok(s['status'] == 'sent' and s['v'] == 1 and s['fq'], f'sheet: with a reason Send sends it and logs the reason ({s})')
        c.ok(s['fm'], 'sheet: the foreman\'s quantity check runs beside the sent request (on his Today), not as a lock')
        # the foreman changes a quantity after it went out: Tell the Vendors shows the email and the coordinator's tap sends
        # it to every invited vendor (CoS 11-06: her tap is the approval); until it went, the award cuts no PO
        fm = await pg.evaluate("""() => { const r = DB.rfqs[DB.rfqs.length - 1]; signIn('u_angel'); render(); rfqForemanSheet(r.id); return r.id; }""")
        await pg.wait_for_timeout(300)
        await pg.locator('#mbm [data-rfqup="L1"]').click(); await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(400)
        await sign_in(pg, 'u_chen'); await pg.evaluate("id => rfqOpenFor(id)", fm); await pg.wait_for_timeout(300)
        tell = await pg.locator('#v-rfq #rfq-tell').count()
        c.ok(tell == 1, 'sheet: a quantity the foreman changed after sending offers Tell the Vendors on the request')
        blk = await pg.evaluate("id => { const r = rfqById(id), s0 = r.status; r.status = 'leveled'; const out = rfqAward(r, Object.fromEntries(r.lines.map(l => [l.id, r.vendors[0].id]))); r.status = s0; return { po: !!(out && out.length), toast: (document.getElementById('toast') || {}).innerText || '' }; }", fm)
        c.ok(not blk['po'] and 'Tell the Vendors' in blk['toast'], f'sheet: the award cuts no PO on quantities the vendors were never told ({blk})')
        if tell:
            await pg.locator('#v-rfq #rfq-tell').click(); await pg.wait_for_timeout(400)
        pv = await modal(pg)
        c.ok(pv and 'Tell the Vendors' in pv['title'] and 'revised quantities' not in pv['title'] and re.search(r'Please quote these instead', pv['text']) and pv['primary'] and pv['primary'][0].startswith('Send to'), f'sheet: Tell the Vendors previews the email, with one blue Send ({pv and (pv["title"], pv["primary"])})')
        if pv: await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(500)
        tv = await pg.evaluate("id => { const r = rfqById(id); return { told: r.fmTold && r.fmTold.n, sent: (DB.outbox || []).filter(o => o.kind === 'rfq-change' && o.about.rfqId === id && o.status === 'sent').length, drafts: (DB.outbox || []).filter(o => o.kind === 'rfq-change' && o.status === 'draft').length, v: (r.vendors || []).length, toast: (document.getElementById('toast') || {}).innerText || '' }; }", fm)
        c.ok(tv['told'] == tv['v'] == tv['sent'] and tv['sent'] >= 1 and tv['drafts'] == 0, f'sheet: her tap sends the change to every invited vendor, nothing waits in Approvals ({tv})')
        c.ok('Open' in tv['toast'] and 'sent to' in tv['toast'], f'sheet: the send toasts with Open ({tv["toast"][:120]})')
        c.ok(not errs, f'sheet: page errors {errs[:2]}')
    finally:
        await b.close()

async def s_new(p, c):
    """New Request for Quote is the same sheet, opened empty, from the page's real + (no Which Lines?, no Create RFQ)"""
    for phone in (False, True):
        dev = 'phone' if phone else 'desktop'
        b, pg, errs = await open_app(p, phone=phone)
        try:
            await sign_in(pg, 'u_chen')
            await pg.evaluate("() => { window.rfqOpen = ''; view = 'rfq'; render(); }"); await pg.wait_for_timeout(300)
            await pg.locator('#v-rfq .pu-plusb').first.click(); await pg.wait_for_timeout(200)
            await pg.locator('#v-rfq .pu-mi').filter(has_text='New Request for Quote').first.click(); await pg.wait_for_timeout(500)
            m = await modal(pg)
            c.ok(m and m['title'] == 'Request for Quote' and m['primary'] == ['Send to Vendors'], f'new {dev}: New Request for Quote opens the one request sheet, one blue ({m and (m["title"], m["primary"])})')
            c.ok(m and 'Create RFQ' not in m['buttons'] and 'Which Lines?' not in m['text'], f'new {dev}: no Which Lines? and no Create RFQ ({m and m["buttons"]})')
            rows = await pg.evaluate("() => [...document.querySelectorAll('#mbm [data-rsp]')].map(i => i.dataset.rsp)")
            c.ok('k:estimate:es1:l3' in rows and not await pg.evaluate("() => document.querySelectorAll('#mbm [data-rsq]').length"), f"new {dev}: it starts empty with the job's lines to pick ({rows[:4]})")
            await pg.locator('#mbm [data-rsp="k:estimate:es1:l3"]').check(); await pg.wait_for_timeout(300)
            n = await pg.evaluate("() => [document.querySelectorAll('#mbm [data-rsq]').length, document.querySelectorAll('#mbm [data-rsv]').length]")
            c.ok(n[0] == 1 and n[1] >= 1, f'new {dev}: a ticked line becomes a line to quote, and vendors are suggested ({n})')
            c.ok(await pg.evaluate("() => document.documentElement.scrollWidth - innerWidth") <= 1 and await pg.evaluate("() => { const m = document.querySelector('#mbm .mbm-box'); return m.scrollWidth - m.clientWidth; }") <= 1, f'new {dev}: no sideways scroll')
            c.ok(not errs, f'new {dev}: page errors {errs[:2]}')
        finally:
            await b.close()

async def s_three(p, c):
    b, pg, errs = await open_app(p)
    try:
        await sign_in(pg, 'u_chen')
        r = await pg.evaluate("""() => { DB.vendors.find(v => v.id === 'v3').email = 'shop@carlosmillwork.example'; DB.vendors.find(v => v.name === 'Tino').email = 'sales@tino.example';
          const r = rfqFromLines('p121', ['estimate:es1:l9']); r.status = 'purchasing'; save();
          const P = rfqProposeVendors(r), ok = rfqSend(r, ['v3'], today());
          return { id: r.id, number: r.number, need3: P.need3, ok, status: r.status, toast: (document.getElementById('toast') || {}).innerText || '' }; }""")
        c.ok(r['need3'], f'three: a request on the $75,000 millwork line needs three quotes ({r["need3"]})')
        c.ok(not r['ok'] and r['status'] == 'purchasing', f'three: one vendor and no reason is refused ({r["ok"]}, {r["status"]})')
        c.ok(re.search(r'three', r['toast'], re.I), f'three: the refusal names the three-quote rule ({r["toast"][:160]})')
        # the record: one vendor ticked, Send refused; the reason box opens; with a reason it goes
        await pg.evaluate("id => rfqOpenFor(id)", r['id']); await pg.wait_for_timeout(400)
        reason = await pg.locator('#v-rfq #rfq-reason').count()
        c.ok(reason > 0, 'three: the record offers a reason for fewer than three vendors')
        r2 = await pg.evaluate("""id => { const r = rfqById(id); const ok = rfqSend(r, ['v3'], today(), { reason: 'Only Carlos builds to our shop drawings' });
          return { ok, status: r.status, fq: r.fewerQuotes || null, hist: (r.history || []).map(h => h.what + ' ' + h.note).join(' | ') }; }""", r['id'])
        c.ok(r2['ok'] and r2['status'] == 'sent', f'three: with a reason it sends ({r2["ok"]}, {r2["status"]})')
        c.ok(r2['fq'] and r2['fq'].get('reason') and r2['fq'].get('by') and re.search(r'three quotes', r2['fq'].get('rule', ''), re.I), f'three: the reason is logged with who and the Standard\'s words ({r2["fq"]})')
        c.ok(re.search(r'fewer than three', r2['hist'], re.I), f'three: the history names it ({r2["hist"][-200:]})')
        await pg.evaluate("() => render()"); await pg.wait_for_timeout(300)
        add = await pg.locator('#v-rfq #rfq-addv').count()
        c.ok(add > 0, 'three: the sent request offers Add a Vendor')
        r3 = await pg.evaluate("""id => { const r = rfqById(id); const ok = typeof rfqAddVendor === 'function' && rfqAddVendor(r, DB.vendors.find(v => v.name === 'Tino').id), tid = DB.vendors.find(v => v.name === 'Tino').id;
          return { ok: !!ok, n: (r.vendors || []).length, sent: (r.sent || []).filter(s => s.vendorId === tid).length, toast: (document.getElementById('toast') || {}).innerText || '' }; }""", r['id'])
        c.ok(r3['ok'] and r3['n'] == 2 and r3['sent'] == 1, f'three: a vendor added after sending gets the same request ({r3})')
        c.ok('Tino' in r3['toast'], f'three: the toast names the vendor ({r3["toast"][:120]})')
        c.ok(not errs, f'three: page errors {errs[:2]}')
    finally:
        await b.close()

async def s_match(p, c):
    b, pg, errs = await open_app(p)
    try:
        await sign_in(pg, 'u_chen')
        await pg.evaluate("async () => { await gcDemoConnect(); }"); await pg.wait_for_timeout(300)
        q = await pg.evaluate("""() => { const c = DB.comms.find(x => /WQ-2290/.test(x.subject || '')); if (!c) return null;
          try { cmRead(c); } catch (e) {}
          const P = (c.proposals || []).filter(p => p.kind === 'quote'); return { id: c.id, P: P.map(p => ({ mat: p.materialId || '', sum: p.summary })) }; }""")
        c.ok(q and q['P'], f'match: the Window Works quote is read as a quote ({q})')
        if q and q['P']:
            c.ok(all(x['mat'] != 'lm1' for x in q['P']), f'match: the windows quote does not price the paint line ({q["P"]})')
            c.ok(all(not x['mat'] or re.search(r'because|both', x['sum'], re.I) for x in q['P']), f'match: a match says why ({q["P"]})')
        await go(pg, 'comms'); await pg.wait_for_timeout(400)
        cls = await pg.evaluate("() => { const b = document.getElementById('cm-applyall'); return b ? b.className : null; }")
        c.ok(cls is None or 'primary' not in cls, f'match: Apply Everything I\'m Sure Of is never the blue button ({cls})')
        if cls is not None:
            await pg.locator('#cm-applyall').click(); await pg.wait_for_timeout(500)
            m = await pg.evaluate("() => { const m = DB.projects.find(x => x.id === 'p206').materials.find(x => x.id === 'lm1'); return { cost: m.cost, vendor: m.vendor, status: m.status }; }")
            c.ok(not m['cost'] and m['vendor'] != 'Window Works', f'match: bulk apply never prices a line ({m})')
        c.ok(not errs, f'match: page errors {errs[:2]}')
    finally:
        await b.close()

async def s_prose(p, c):
    b, pg, errs = await open_app(p)
    try:
        await sign_in(pg, 'u_chen')
        r = await pg.evaluate(SUBS_JS)
        c.ok(r['ok'] and r['sub'], f'prose: the demolition request went to three subs ({r})')
        x = await pg.evaluate(replies_js(PROSE), [r['id'], PROSE])
        got = {q['v']: q['lines'] for q in x['quotes']}
        c.ok(got.get('vsub_gow') == [19400] and got.get('vsub_jsy') == [15550] and got.get('vsub_qns') == [21800], f'prose: lump sum, total and words are read ({got})')
        inc = {q['v']: (q['inc'], q['exc']) for q in x['quotes']}
        c.ok(re.search(r'permit', inc.get('vsub_gow', ('', ''))[1], re.I) and re.search(r'everything', inc.get('vsub_qns', ('', ''))[0], re.I), f'prose: scope read: includes and excludes ({inc})')
        L = await pg.evaluate("id => { const r = rfqById(id), L = rfqLevel(r); return { tax: L.baskets.map(b => b.tax), landed: L.baskets.map(b => b.landed), budget: L.budgetTotal, complete: L.budgetComplete }; }", r['id'])
        c.ok(L['tax'] and all(t == 0 for t in L['tax']) and min(L['landed']) == 15550, f'prose: sub labour is leveled without sales tax ({L})')
        c.ok(L['complete'] and L['budget'] == 21500, f'prose: subs level against the line budget, $21,500 ({L})')
        await pg.evaluate("id => rfqOpenFor(id)", r['id']); await pg.wait_for_timeout(400)
        txt = await pg.evaluate("() => document.getElementById('v-rfq').innerText")
        c.ok('sales tax' not in txt.lower() and 'use tax' not in txt.lower(), 'prose: the leveling page shows no tax on sub labour')
        c.ok(re.search(r'Includes', txt) and re.search(r'Excludes', txt), 'prose: each bid shows what it includes and excludes')
        # a reply with no price: Price Needed, and the request is not Leveled on it
        r2 = await pg.evaluate(SUBS_JS)
        T2 = {'vsub_gow': 'Thanks Chen, we walked it. Numbers to you Monday.', 'vsub_jsy': PROSE['vsub_jsy'], 'vsub_qns': PROSE['vsub_qns']}
        y = await pg.evaluate(replies_js(T2), [r2['id'], T2])
        gow = next((q for q in y['quotes'] if q['v'] == 'vsub_gow'), None)
        c.ok(gow and gow['need'], f'prose: a reply with no price is Price Needed ({gow})')
        c.ok(y['status'] != 'leveled', f'prose: the request is not Leveled while a price is needed ({y["status"]})')
        await pg.evaluate("id => rfqOpenFor(id)", r2['id']); await pg.wait_for_timeout(400)
        txt = await pg.evaluate("() => document.getElementById('v-rfq').innerText")
        c.ok('Price Needed' in txt and not re.search(r'\bLeveled\b', txt.split('Leveling')[0]), 'prose: the record says Price Needed, not Leveled')
        c.ok(not errs, f'prose: page errors {errs[:2]}')
    finally:
        await b.close()

async def s_award(p, c):
    b, pg, errs = await open_app(p)
    try:
        await sign_in(pg, 'u_chen')
        r = await pg.evaluate(SUBS_JS)
        await pg.evaluate(replies_js(PROSE), [r['id'], PROSE])
        a = await pg.evaluate("""id => { const r = rfqById(id); (r.quotes || []).forEach(q => q.unreadable || q.confirmed || rfqConfirmQuote(r, q));
          r.status = 'negotiating'; r.round2In = today(); const made = rfqAward(r, { L1: 'vsub_jsy' }) || [];
          return { n: made.length, saved: r.award && r.award.savingsVsFirst, final: r.award && r.award.final, basis: r.award && r.award.firstBasis }; }""", r['id'])
        c.ok(a['n'] == 1 and a['saved'] == 3850, f'award: the saving is $3,850 against the next-best bid, pre-tax ({a})')
        c.ok(a['final'] == 15550, f'award: the final is the pre-tax award, $15,550 ({a})')
        t = await toast(pg)
        c.ok('$3,850' in t['text'] and '$1,380' not in t['text'], f'award: the toast says $3,850 ({t["text"][:160]})')
        await pg.evaluate("id => rfqOpenFor(id)", r['id']); await pg.wait_for_timeout(400)
        txt = await pg.evaluate("() => document.getElementById('v-rfq').innerText")
        c.ok('$3,850' in txt and '$1,380 saved' not in txt and 'Negotiation:' in txt, 'award: the record says $3,850 saved, with the negotiation figure beside it')
        # an award stamped on the old basis (landed with tax, the $1,380) is re-read on the pre-tax basis, so the month's
        # total adds one kind of saving; the old figure is kept beside it (CoS 11-06)
        old = await pg.evaluate("""id => { const r = rfqById(id), A = r.award; Object.assign(A, { savingsVsFirst: 1380, firstQuote: 16930, final: A.landed, preTax: false }); delete A.basis;
          const S = rfqSavings(); return { vs: S.vsFirst, basis: A.basis, saved: A.savingsVsFirst, was: A.was && A.was.savingsVsFirst, old: S.oldBasis }; }""", r['id'])
        c.ok(old['vs'] == 3850 and old['saved'] == 3850 and old['was'] == 1380 and old['basis'] and not old['old'], f'award: an old award is re-read on the pre-tax basis; the month adds one basis ({old})')
        c.ok(not errs, f'award: page errors {errs[:2]}')
    finally:
        await b.close()

async def s_award3(p, c):
    """three asked, one priced, Level Now, award: the award asks why, in a sentence, and the request stays on the Standard's
    three-quote check as "awarded on fewer than three, because ..." (CoS 11-06)"""
    b, pg, errs = await open_app(p)
    try:
        await sign_in(pg, 'u_chen')
        r = await pg.evaluate(SUBS_JS)
        T1 = {'vsub_jsy': PROSE['vsub_jsy'], 'vsub_gow': 'Thanks Chen, numbers Monday.', 'vsub_qns': 'We will look at it next week.'}
        await pg.evaluate(replies_js(T1), [r['id'], T1])
        await pg.evaluate("id => rfqOpenFor(id)", r['id']); await pg.wait_for_timeout(300)
        await pg.locator('#v-rfq #rfq-level').click(); await pg.wait_for_timeout(300)
        await pg.evaluate("id => { const r = rfqById(id); (r.quotes || []).forEach(q => q.unreadable || q.confirmed || rfqConfirmQuote(r, q)); }", r['id'])
        await pg.locator('#v-rfq #rfq-skipneg').click(); await pg.wait_for_timeout(300)
        box = await pg.locator('#v-rfq #rfq-award-reason').count()
        c.ok(box == 1, 'award3: with one priced bid the award card asks why it is awarded on fewer than three')
        await pg.locator('#v-rfq #rfq-award').click(); await pg.wait_for_timeout(400)
        a0 = await pg.evaluate("id => ({ st: rfqById(id).status, toast: (document.getElementById('toast') || {}).innerText || '' })", r['id'])
        c.ok(a0['st'] != 'awarded' and re.search(r'fewer than three', a0['toast'], re.I), f'award3: no reason, no award ({a0})')
        await pg.locator('#v-rfq #rfq-award-reason').fill('urgent'); await pg.locator('#v-rfq #rfq-award').click(); await pg.wait_for_timeout(400)
        a1 = await pg.evaluate("id => ({ st: rfqById(id).status, toast: (document.getElementById('toast') || {}).innerText || '' })", r['id'])
        c.ok(a1['st'] != 'awarded' and re.search(r'sentence', a1['toast'], re.I), f'award3: one word is not a reason ({a1})')
        await pg.locator('#v-rfq #rfq-award-reason').fill('The other two would not price before the start date')
        await pg.locator('#v-rfq #rfq-award').click(); await pg.wait_for_timeout(600)
        a2 = await pg.evaluate("""id => { const r = rfqById(id); return { st: r.status, reason: (r.awardReason || {}).reason, fewer: !!(r.award || {}).fewer,
          pred: PRED.rfqUnderQuoted.rows().some(x => x.id === id), row: (CATCH.find(c => c.name === 'rfqUnderQuoted').rows().find(x => x.key === 'rfq3:' + id) || {}).what || '' }; }""", r['id'])
        c.ok(a2['st'] == 'awarded' and a2['reason'] and a2['fewer'], f'award3: with a sentence the award goes, the reason logged on it ({a2})')
        c.ok(a2['pred'], f"award3: the awarded request still counts on the Standard's three-quote check ({a2})")
        c.ok(a2['row'].startswith('Awarded on fewer than three, because The other two'), f'award3: the check names it with its reason ({a2["row"]})')
        txt = await pg.evaluate("() => document.getElementById('v-rfq').innerText")
        c.ok('Awarded on fewer than three' in txt, 'award3: the record says it was awarded on fewer than three, and why')
        snd = await pg.evaluate("""() => { const r = rfqFromLines('p121', ['estimate:es1:l11'], { sub: true, category: 'Scaffold' }); r.status = 'purchasing';
          return rfqSend(r, ['vsub_gow'], today(), { reason: 'ok fine' }); }""")
        c.ok(not snd, 'award3: Send to one sub with a two-word reason is refused: a reason is a sentence')
        c.ok(not errs, f'award3: page errors {errs[:2]}')
    finally:
        await b.close()

async def s_status(p, c):
    b, pg, errs = await open_app(p)
    try:
        await sign_in(pg, 'u_chen')
        has = await pg.evaluate("() => typeof rfqLineState === 'function'")
        c.ok(has, 'status: rfqLineState(lineKey) exists')
        if not has: return
        s0 = await pg.evaluate("() => rfqLineState('estimate:es1:l1')")
        c.ok(s0 is None or s0.get('stage') in (None, '', 'none'), f'status: a line with no request has no quote stage ({s0})')
        d = await pg.evaluate("""() => { const r = rfqFromLines('p121', ['estimate:es1:l11'], { sub: true, category: 'Scaffold' }); const s = rfqLineState('estimate:es1:l11');
          const row = puQuoteRows().find(x => x.id === 'rfq:' + r.id); return { s, row: row && { actor: row.actor, why: row.why, who: row.who, b: row.b } }; }""")
        c.ok(d['s'] and d['s']['stage'] == 'draft', f'status: a request not yet sent is a draft ({d["s"]})')
        c.ok(d['row'] and d['row']['actor'] != 'vendor' and not re.search(r'vendor', (d['row']['why'] or '') + (d['row']['who'] or ''), re.I), f'status: a draft is never waiting on the vendors ({d["row"]})')
        r = await pg.evaluate(SUBS_JS)
        s1 = await pg.evaluate("() => rfqLineState('estimate:es1:l1')")
        c.ok(s1 and s1['stage'] == 'out', f'status: sent is out to the vendors ({s1})')
        await pg.evaluate(replies_js(PROSE), [r['id'], PROSE])
        s2 = await pg.evaluate("() => rfqLineState('estimate:es1:l1')")
        c.ok(s2 and s2['stage'] == 'leveled', f'status: every price in is leveled ({s2})')
        await pg.evaluate("""id => { const r = rfqById(id); (r.quotes || []).forEach(q => q.confirmed || rfqConfirmQuote(r, q)); r.status = 'negotiating'; r.round2In = today(); rfqAward(r, { L1: 'vsub_jsy' }); }""", r['id'])
        s3 = await pg.evaluate("() => { const s = rfqLineState('estimate:es1:l1'); return s && { stage: s.stage, po: s.po && s.po.number, label: s.label }; }")
        c.ok(s3 and s3['stage'] == 'awarded' and s3['po'], f'status: after the award the line is awarded, with its PO ({s3})')
        pure = await pg.evaluate("() => { const a = JSON.stringify(DB.rfqs); rfqLineState('estimate:es1:l1'); rfqLineState('estimate:es1:l9'); return a === JSON.stringify(DB.rfqs); }")
        c.ok(pure, 'status: rfqLineState is a pure read')
        # Today and the Buy Board read the one status (P2's puNeedStatusFor when it has landed)
        today_ = await pg.evaluate("""() => { const st = typeof puNeedStatusFor === 'function' ? puNeedStatusFor('estimate:es1:l1') : null;
          const rows = puNeeds('').filter(x => (x.r.lineKey || x.r.key) === 'estimate:es1:l1'); return { p2: !!st, acts: rows.map(x => x.act) }; }""")
        if today_['p2']:
            c.ok(not any(a == 'Ask for Bids' for a in today_['acts']), f'status: after the award the line is not Ask for Bids ({today_})')
        else:
            print('NOTE status: puNeedStatusFor (P2) not in this build; the Buy Board row reads', today_['acts'])
        c.ok(not errs, f'status: page errors {errs[:2]}')
    finally:
        await b.close()

ASKS = [('u_chen', 'what is in the warehouse?'), ('u_chen', 'what is owed back to us?'), ('u_angel', 'what was ordered for my job?')]
async def s_ask(p, c):
    b, pg, errs = await open_app(p)
    try:
        out = []
        for uid, q in ASKS:
            await sign_in(pg, uid)
            a = await pg.evaluate("async q => { const a = await Promise.resolve(paAsk(q)); return a && { h: a.headline || '', w: (a.work || []).join(' | '), k: a.kind || '' }; }", q)
            out.append(a)
        st, ow, fo = out
        stock = await pg.evaluate("() => (DB.inventory || []).filter(i => +i.qty > 0).map(i => i.name)")
        c.ok(st and st['k'] not in ('blocked', 'notUnderstood') and 'not understand' not in st['h'] and re.search(r'stock', st['h'], re.I), f'ask: "warehouse" is read as Stock ({st and st["h"][:160]})')
        c.ok(st and any(n in st['h'] + st['w'] for n in stock[:5]), f'ask: the stock answer names what is on the shelf ({stock[:3]})')
        await sign_in(pg, 'u_chen')
        tile = await pg.evaluate("() => { const R = puOrderRows('').filter(x => 'owed' === x.tile); return money(r2(R.reduce((a, x) => a + (x.money || 0), 0))); }")
        c.ok(ow and ow['k'] != 'blocked' and tile in ow['h'], f'ask: "what is owed back" says the Owed Back tile\'s {tile} ({ow and ow["h"][:160]})')
        mats = await pg.evaluate("() => DB.projects.find(p => p.id === 'p121').materials.filter(m => ['ordered', 'shipped'].includes(m.status)).map(m => m.name)")
        c.ok(fo and fo['k'] != 'blocked' and not re.search(r'not part of what your account', fo['h']), f'ask: the foreman is told what was ordered for his job ({fo and fo["h"][:160]})')
        c.ok(fo and '$' not in fo['h'] + fo['w'], f'ask: no dollars to the field ({fo and (fo["h"] + fo["w"])[:200]})')
        c.ok(fo and any(m in fo['h'] + fo['w'] for m in mats), f'ask: the answer names the items ordered ({mats[:3]})')
        c.ok(fo and re.search(r'\b(site|drop|deliver)', fo['w'] + fo['h'], re.I), 'ask: the answer says where it drops')
        c.ok(not errs, f'ask: page errors {errs[:2]}')
    finally:
        await b.close()

async def s_phone(p, c):
    b, pg, errs = await open_app(p, phone=True)
    try:
        await sign_in(pg, 'u_chen')
        r = await pg.evaluate(SUBS_JS)
        await pg.evaluate("() => { window.rfqOpen = ''; view = 'rfq'; render(); }"); await pg.wait_for_timeout(500)
        txt = await pg.evaluate("() => document.getElementById('v-rfq').innerText")
        row = [l for l in txt.split('\n') if r['number'] in l]
        blk = txt[txt.find(r['number']):][:300]
        c.ok(all(w in blk for w in ('Budget', 'Quotes In', 'Due')), f'phone: the request card shows Budget, Quotes In and Due ({blk[:200]!r})')
        c.ok(await pg.evaluate(HSCROLL) <= 1, 'phone: Quotes does not scroll sideways')
        await pg.evaluate("id => rfqOpenFor(id)", r['id']); await pg.wait_for_timeout(400)
        hs = await pg.evaluate("() => [...document.querySelectorAll('#v-rfq .rfq-vrow')].map(e => Math.round(e.getBoundingClientRect().height))")
        c.ok(hs and min(hs) >= 44, f'phone: vendor rows are 44px ({hs})')
        c.ok(await pg.evaluate(HSCROLL) <= 1, 'phone: the record does not scroll sideways')
        has = await pg.evaluate("() => typeof rfqStartFromLines === 'function'")
        if has:
            await pg.evaluate("() => rfqStartFromLines(['estimate:es1:l9'])"); await pg.wait_for_timeout(400)
            ov = await pg.evaluate("() => { const m = document.querySelector('#mbm .mbm-box'); return m ? [m.scrollWidth - m.clientWidth, document.documentElement.scrollWidth - innerWidth] : null; }")
            c.ok(ov and max(ov) <= 1, f'phone: the request sheet does not scroll sideways ({ov})')
            hv = await pg.evaluate("() => [...document.querySelectorAll('#mbm .rfq-pick')].map(e => Math.round(e.getBoundingClientRect().height))")
            c.ok(hv and min(hv) >= 44, f'phone: the sheet\'s vendor rows are 44px ({hv[:5]})')
        c.ok(not errs, f'phone: page errors {errs[:2]}')
    finally:
        await b.close()

SECTIONS = [('sheet', s_sheet), ('new', s_new), ('three', s_three), ('match', s_match), ('prose', s_prose), ('award', s_award), ('award3', s_award3), ('status', s_status), ('ask', s_ask), ('phone', s_phone)]

async def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--section', default='')
    a = ap.parse_args()
    want = {x.strip() for x in a.section.split(',') if x.strip()}
    c = Checks()
    async with async_playwright() as p:
        for name, fn in SECTIONS:
            if want and name not in want: continue
            n0 = c.n; f0 = len(c.fail)
            try:
                await fn(p, c)
            except Exception as e:
                c.ok(False, f'{name}: crashed: {str(e)[:300]}')
            print(f'-- {name}: {c.n - n0} checks, {len(c.fail) - f0} failed')
    sys.exit(c.done())
asyncio.run(main())
