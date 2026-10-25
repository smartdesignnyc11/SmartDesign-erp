"""flow: what the month (tests/month_sim.py, review/month/ledger.md at db8d418) scored as slipping through the
hands of the person who should have moved it. Each section reproduces one class on a fresh seeded build, with
the month's own events (tests/month_book.json) put in through the app's paths (the Demo Workspace mailboxes,
the foreman's functions), and drives the real buttons the person sees.

  order     1. A late or due Buy Board line says Order on the coordinator's Home and on the Buy Board, and the
               sheet is prefilled (vendor from the applied quote, price, quantity, the on-site date) and issues
               through poValid; Buy never sends a contract line to the FF&E board; a quote's Apply opens the
               order (the Brooklyn Lumber trim quote $6,840 becomes an issued PO).
  field     2. Angel's emailed ask (25 GWB + cement board by Thursday) becomes a request on the Buy Board, not a
               note; a damaged delivery raised on a Friday afternoon is the coordinator's on Monday morning, not
               escalated over the weekend.
  co        3. The knob-and-tube extra answered from Do Now drafts a priced change order ($3,200) and the send
               follows; the joist extra answered "I will write the CO" stays on the PM's Do Now with Write the
               Change Order until a CO goes out; a client's ask to add an outlet drafts a CO from the answer; the
               Kleins disputing the joist CO by mail land on the PM's Do Now (Answer: Revise / Explain / Withdraw).
  choice    4. The Kleins' choice by mail (honed Calacatta) is one tap on the PM's Do Now (Record Choice) and the
               portal stops asking; their dated ask (the laundry layout before Friday) is the PM's task due Friday.
  chase     5. Every Chase writes a draft: Tino's COI to the address his mail came from, a lead with no address to
               the outbox; billing's past-due row chases the Jessops; a new inquiry gets a reply draft and a
               lead; Hannah Brooks' call makes a lead and a call task; Ines Ward's "meet 10/6 at 10" is a hold on
               the owner's calendar; a proposal nobody answered comes back on Caught for You and chases.
  visits    6. A delivery or a sub's visit in mail (Diamond 9/25 8-12, the plumber Thursday 7am) is applied once
               and shows on the foreman's Arriving Today on its day.
  owner     7. "Sign the 45 Cranberry PW1 by 9/28" is the owner's task due 9/28; the LLC biennial is on the
               owner's Do Now and Draft the Renewal records the filing (next expiry 9/28/2028).
  client    8. The garden bath tile sample is approved from the portal by the button the client sees, and the
               coordinator can order the tile.

    python3 flow_test.py [--section order,field,...]
"""
import asyncio, json, os, re, sys, argparse
from harness import *

HERE = os.path.dirname(os.path.abspath(__file__))
RUNTIME = open(os.path.join(HERE, 'month_runtime.js'), encoding='utf-8').read()
BOOK = {e['id']: e for e in json.load(open(os.path.join(HERE, 'month_book.json'), encoding='utf-8'))['events']}

MODAL = """() => { const m = document.querySelector('#mbm'); if (!m || !m.getClientRects().length) return null;
  return { title: (m.querySelector('.mbm-hd h3') || {}).innerText || '', text: m.innerText.replace(/\\s+/g, ' '),
           ok: ((m.querySelector('#mbm-ok') || {}).innerText || '').trim(),
           fields: Object.fromEntries([...m.querySelectorAll('[data-f]')].map(i => [i.dataset.f, i.type === 'checkbox' ? i.checked : String(i.value || '')])) }; }"""
TOAST = "() => ((document.getElementById('toast') || {}).innerText || '').trim()"

async def modal(pg): return await pg.evaluate(MODAL)
async def toast(pg): return await pg.evaluate(TOAST)
async def ok(pg, wait=700):
    await pg.locator('#mbm #mbm-ok').click(timeout=4000); await pg.wait_for_timeout(wait)

async def wait_send(pg, ms=6000):
    """The send sheet follows a drafted change order once the draft is written (a moment on a slow machine)."""
    try:
        await pg.wait_for_function("() => { const h = document.querySelector('#mbm .mbm-hd h3'); return h && /^Send to Client/.test(h.innerText); }", timeout=ms)
        return True
    except Exception:
        return False

async def fresh(p, personas=(), day=None):
    b, pg, errs = await open_app(p)
    await pg.evaluate(RUNTIME)
    for u in personas: await pg.evaluate("u => __MS.connect(u)", u)
    if day: await pg.evaluate("d => appSetDay(d)", day)
    return b, pg, errs

async def inject(pg, *ids):
    for i in ids:
        e = BOOK[i]
        if e['kind'] == 'mail': await pg.evaluate("e => __MS.wsMail(e)", e)
        else: await pg.evaluate("async e => { __MS.as(e.actor); return await __MS.own(e); }", e)

async def sync(pg, *uids):
    for u in uids: await pg.evaluate("async u => { __MS.as(u); return await __MS.sync(u); }", u)

async def home(pg, uid):
    # Home is Today (lane "today"): All opened in full is every row the person has there, as Caught for You's "more" is
    await pg.evaluate("u => { __MS.as(u); try { tdCatchAll = true; tdyTabSet('all'); tdyAllOpen = true; } catch (e) {} view = 'home'; render(); }", uid); await pg.wait_for_timeout(400)

ROWS = """() => [...document.querySelectorAll('#v-home .td-do .td-card, #v-home .td-catch .td-card, #v-home .h4r[data-ea]')].filter(e => e.getClientRects().length)
  .map(e => ({ text: e.innerText.replace(/\\s+/g, ' ').slice(0, 220), data: e.dataset.ea || '', verb: ((e.querySelector('[data-tdverb], [data-tdcatch], .h4-act, em') || {}).innerText || '').trim() }))"""

async def rows(pg): return await pg.evaluate(ROWS)

async def press(pg, text_rx, verb_rx):
    """Press the verb on the Home row (Do Now, Caught for You or the classic Home list) whose text matches."""
    return await pg.evaluate("""([t, v]) => { const T = new RegExp(t, 'i'), V = new RegExp(v);
      for (const e of document.querySelectorAll('#v-home .td-do .td-card, #v-home .td-catch .td-card, #v-home .h4r[data-ea]')) {
        if (!e.getClientRects().length || !T.test(e.innerText)) continue;
        const b = [...e.querySelectorAll('[data-tdverb], [data-tdcatch], button, .h4-act, em')].find(x => V.test((x.innerText || '').trim()));
        if (b) { (e.matches('.h4r') ? e : b).click(); return (b.innerText || '').trim(); }
      } return ''; }""", [text_rx, verb_rx])


async def press_any(pg, uid, text_rx, verb_rx):
    """Home first; a Do Now card past the first five is in Approvals, where the person finds the rest."""
    await home(pg, uid)
    v = await press(pg, text_rx, verb_rx)
    if v: return v
    await pg.evaluate("() => { window.mApprKind = 'all'; view = 'mapprove'; render(); }"); await pg.wait_for_timeout(400)
    v = await pg.evaluate("""([t, vb]) => { const T = new RegExp(t, 'i'), V = new RegExp(vb);
      // the first matching row that has the verb, not the first matching row (a decision "Laundry layout..." can
      // match before the mailed laundry ask that carries Make It a Task)
      const b = [...document.querySelectorAll('.m-appr')].filter(x => x.getClientRects().length && T.test(x.innerText))
        .map(e => [...e.querySelectorAll('button')].find(x => V.test(x.innerText.trim()))).find(Boolean); b && b.click(); return b ? b.innerText.trim() : ''; }""", [text_rx, verb_rx])
    await pg.wait_for_timeout(300)
    return v

async def listed(pg, uid, text_rx):
    """The rows a person has for this: Home (Do Now, Caught for You, the classic list) and Approvals."""
    await home(pg, uid)
    R = [r for r in await rows(pg) if re.search(text_rx, r['text'], re.I)]
    await pg.evaluate("() => { window.mApprKind = 'all'; view = 'mapprove'; render(); }"); await pg.wait_for_timeout(300)
    R += await pg.evaluate("""(t) => [...document.querySelectorAll('.m-appr')].filter(x => x.getClientRects().length && new RegExp(t, 'i').test(x.innerText))
      .map(x => ({ text: x.innerText.replace(/\\s+/g, ' ').slice(0, 200), data: '', verb: ((x.querySelector('[data-myes]') || {}).innerText || '').trim() }))""", text_rx)
    return R


# ------------------------------------------------------------------------------------------------ 1. order
async def s_order(p, c):
    b, pg, errs = await fresh(p, ['u_chen'])
    try:
        await home(pg, 'u_chen')
        R = await rows(pg)
        proc = [r for r in R if '"view":"proc"' in r['data']]
        c.ok(not proc, f'order: no Home row sends a line to the FF&E board ({[r["text"][:60] for r in proc]})')
        late = [r for r in R if 'order-by' in r['text'] and '"order"' in r['data']]
        c.ok(len(late) >= 3 and all(r['verb'] == 'Order' for r in late), f'order: the late lines say Order ({[(r["text"][:40], r["verb"]) for r in late][:4]})')
        v = await press(pg, r'Parlor kitchen countertop slab', r'^Order$')
        m = await modal(pg)
        need = await pg.evaluate("() => { const p = DB.projects.find(x => x.id === 'p121'); return withProject(p, () => matDates(p.materials.find(m => m.id === 'm19')).needBy); }")
        c.ok(v == 'Order' and m and m['title'].startswith('Order') and m['fields'].get('needBy') == need and 'vendor' in m['fields'],
             f"order: Order opens the PO sheet prefilled with the on-site date {need} ({m and m['title']}, {m and m['fields']})")
        if m:
            n0 = await pg.evaluate("() => DB.pos.length")
            await ok(pg)
            c.ok(await modal(pg) and await pg.evaluate("() => DB.pos.length") == n0, 'order: with no supplier chosen nothing is issued (the sheet asks for one)')
            await pg.keyboard.press('Escape')
        # the Buy Board's row says Order too, and a contract line opens the same sheet (never the FF&E board)
        await pg.evaluate("() => { setCurrent('p121'); procMode = 'lines'; buyScope = ''; buyOpen = true; view = 'proc'; render(); }"); await pg.wait_for_timeout(500)
        # the Buy Board (procurement P1): a need still to buy has Order as its next step in its panel
        nb = await pg.evaluate("() => buyList('').filter(r => r.tab === 'buy' && !r.ordered && !r.dec && ['line', 'material'].includes(r.kind)).slice(0, 4).map(r => { bbSel = r.id; render(); const b = document.querySelector('#buy-board .bb-panel [data-bbstep]'); return b ? b.innerText.trim() : ''; })")
        c.ok(len(nb) >= 3 and set(nb) == {'Order'}, f'order: the Buy Board needs say Order ({nb[:5]})')
        await pg.evaluate("() => { const r = buyList('').find(x => /Trim, doors, paint/.test(x.name)); bbSel = r.id; render(); }")
        await pg.locator('#buy-board .bb-panel [data-buy^="order|"]').first.click(timeout=4000); await pg.wait_for_timeout(400)
        m = await modal(pg)
        c.ok(m and 'Trim, doors, paint' in m['title'] and float(m['fields'].get('price') or 0) > 0 and await pg.evaluate("() => view") == 'proc' and await pg.evaluate("() => procMode") == 'lines',
             f"order: a contract line opens the order sheet with its budget as the price, on the Buy Board ({m and m['fields']})")
        await pg.keyboard.press('Escape')
        # the quote path: Brooklyn Lumber on file (the 9/3 unrouted apply), the quote arrives, Apply prices the line and opens the order
        await pg.evaluate("() => { const c = DB.comms.find(x => /88412/.test(x.subject)); cmApply(c, c.proposals.find(p => p.kind === 'unrouted')); mbCloseModal(); save(); }")
        await pg.evaluate("d => appSetDay(d)", '2026-09-09')
        await inject(pg, 'E065'); await sync(pg, 'u_chen')
        q = await pg.evaluate("() => { const c = DB.comms.find(x => /BLQ-2210/.test(x.subject)); const p = c && c.proposals.find(x => x.kind === 'quote'); return p && { m: p.materialId, a: p.amount, v: p.vendorId }; }")
        c.ok(q and q['m'] == 'm13' and q['a'] == 6840 and q['v'], f'order: the trim quote (a PDF named BLQ-2210.pdf) is read as a quote on Base molding & casing ({q})')
        await home(pg, 'u_chen')
        v = await press(pg, r'Brooklyn Lumber sent a quote', r'^Apply$')
        m = await modal(pg)
        c.ok(v == 'Apply' and m and m['title'].startswith('Order') and m['fields'].get('vendor') == 'Brooklyn Lumber' and float(m['fields'].get('price') or 0) == 6840,
             f"order: Apply on the quote opens the order with Brooklyn Lumber at $6,840 ({m and m['fields']})")
        if m:
            await ok(pg, 900)
            po = await pg.evaluate("() => { const o = DB.pos.find(x => x.lines.some(l => l.materialId === 'm13')); const m = DB.projects.find(x => x.id === 'p121').materials.find(x => x.id === 'm13');"
                                   " return o && { n: o.number, v: o.vendor, st: o.status, t: poTotal(o).total, need: o.needBy, valid: poValid(o).length, mst: m.status, mpo: m.po }; }")
            c.ok(po and po['st'] == 'issued' and po['v'] == 'Brooklyn Lumber' and po['t'] == 6840 and po['need'] and po['valid'] == 0,
                 f'order: the PO is issued to Brooklyn Lumber for $6,840 with an on-site date, through poValid ({po})')
            c.ok(po and po['mst'] == 'ordered' and po['mpo'] == po['n'], f'order: the line reads ordered on the PO ({po})')
            c.ok('issued' in (await toast(pg)), f'order: the toast says issued ({await toast(pg)!r})')
        c.ok(not errs, f'order: page errors {errs[:2]}')
    finally:
        await b.close()
    # a quote from a stone yard nobody has on file: the offer to put them on file rides along, then Order finds them
    b, pg, errs = await fresh(p, ['u_chen'], '2026-09-10')
    try:
        await inject(pg, 'E074'); await sync(pg, 'u_chen')
        ks = await pg.evaluate("() => (DB.comms.find(x => /GS-418/.test(x.subject)) || { proposals: [] }).proposals.map(p => p.kind + (p.as ? ':' + p.as : ''))")
        c.ok('quote' in ks and 'unrouted:vendor' in ks, f'order: the Gowanus quote comes with the offer to put the yard on file ({ks})')
        await pg.evaluate("""() => { const c = DB.comms.find(x => /GS-418/.test(x.subject)); cmApply(c, c.proposals.find(p => p.kind === 'quote')); mbCloseModal();
          cmApply(c, c.proposals.find(p => p.kind === 'unrouted')); mbCloseModal(); save(); }""")
        await home(pg, 'u_chen')
        await press(pg, r'countertop slab', r'^Order$')
        m = await modal(pg)
        c.ok(m and m['fields'].get('vendor') == 'Gowanus Stone Yard' and float(m['fields'].get('price') or 0) == 7450, f"order: the slab's Order picks the yard from its quote at $7,450 ({m and m['fields']})")
        if m:
            # Plans control put 121 State's rooms on the drawing register, so the slab for the Parlor kitchen meets the
            # measurement gate (poFabGate: the fabricator's own field measurements before a fabricated item is
            # ordered). The slab is template-to-install (its task "Parlor kitchen countertop (template → install)", the
            # quote "two weeks from template"): the fabricator's template on site, which comes because of this order, is
            # that second measurement. Asking for it before the order deadlocked the slab (order-by 9/1, template 9/21:
            # the month never ordered it unless someone ticked "measurements received" when they were not). The sheet
            # says so, asks for no tick, and the PO issues saying fabrication starts from the template.
            gate = await pg.evaluate("() => (document.querySelector('#mbm .fl-fabgate') || {}).innerText || ''")
            c.ok('templates the site' in gate and 'second measurement' in gate and await pg.locator('#mbm [data-f="tradeOk"]').count() == 0,
                 f'order: the slab sheet says the fabricator\'s template is the second measurement, and asks no tick ({gate!r})')
            # the slab has no line of its own: it goes on Millwork & countertops, all $75,000 of it already spent or
            # committed, so the sheet says the overage and asks why before it issues
            over = await pg.evaluate("() => { const o = document.querySelector('#mbm .fl-over'); return o && !o.hidden ? o.innerText : '' }")
            c.ok('over what is left on Millwork' in over, f'order: the slab sheet says it is over what is left on the millwork line ({over!r})')
            over and await pg.fill('#mbm [data-f="overWhy"]', 'countertops were carried in the millwork line; a change order follows')
            await ok(pg, 900)
            # $7,450 over the line is over $1,000: it waits on the owner, who approves it from the card
            ap = await pg.evaluate("""() => { const o = DB.pos.find(x => x.lines.some(l => l.materialId === 'm19')); if (!o || o.status !== 'pending') return o && o.status;
              const why = (o.overReason || {}).why || ''; signIn('u_owner'); const card = mApprovals().find(a => a.kind === 'po' && a.id === o.id);
              const said = !!(card && /over what is left on Millwork/.test(card.detail) && card.detail.includes(why)); apprPOYes({ id: o.id }); signIn('u_chen'); return said ? 'approved' : 'card silent' }""")
            c.ok(ap == 'approved', f'order: the slab waits on the owner, whose card says the overage and why; approved, it issues ({ap})')
            po = await pg.evaluate("() => { const o = DB.pos.find(x => x.lines.some(l => l.materialId === 'm19')); return o && [o.status, o.vendor, poTotal(o).total, !!o.tradeVerified, poDoubleOrder(o), (o.templateFirst || {}).task || '', o.notes || '']; }")
            c.ok(po and po[0] == 'issued' and po[2] == 7450 and not po[3] and 'template' in po[5] and 'template' in po[6],
                 f'order: the slab PO is issued, fabrication from the template on it, no measurement claimed ({po})')
            # a room in the name is where the goods go, not what they are: the millwork PO for the same kitchen is not a double order
            c.ok(po and not po[4], f'order: no double-order warning against the kitchen millwork PO ({po and po[4]})')
        # the gate still holds a fabricated item that is built from our numbers (no template under the order): a
        # built-in for the parlor kitchen (an invented line, as a PM would add it) asks the tick, Issue PO without it
        # orders nothing, with it the PO issues carrying who confirmed the measurements
        gx = await pg.evaluate("""() => { const p = DB.projects.find(x => x.id === 'p121');
            p.materials.push({ id: 'mfx1', name: 'Parlor kitchen built-in bench', cat: 'finish', taskId: 'millpk', lead: 10, when: 'start', status: 'not-ordered', eta: '', vendor: '', po: '', qty: '1 ea', cost: '', deliverTo: 'Site', notes: '', line: '' });
            buyOrderDialog({ pid: 'p121', mid: 'mfx1' });
            return (document.querySelector('#mbm .fl-fabgate') || {}).innerText || ''; }""")
        c.ok(gx and 'Second measurement' in gx and await pg.locator('#mbm [data-f="tradeOk"]').count() == 1, f'order: a non-template fabricated item still asks the measurement tick ({gx!r})')
        if gx:
            await pg.evaluate("() => { const set = (k, v) => { const e = document.querySelector(`#mbm [data-f=\"${k}\"]`); if (e) { e.value = v; e.dispatchEvent(new Event('input', { bubbles: true })); e.dispatchEvent(new Event('change', { bubbles: true })); } }; const s = document.querySelector('#mbm [data-f=\"vendor\"]'); const o = [...s.options].find(o => /Carlos Millwork/.test(o.text)); s.value = o ? o.value : s.value; s.dispatchEvent(new Event('change', { bubbles: true })); set('price', '900'); set('needBy', '2026-09-24'); }")
            n0 = await pg.evaluate("() => DB.pos.length")
            await ok(pg, 500)
            c.ok(await modal(pg) and await pg.evaluate("() => DB.pos.length") == n0, 'order: without the tick nothing is ordered and the sheet stays open')
            await pg.locator('#mbm [data-f="tradeOk"]').check()
            # the bench goes on the millwork line too, which has nothing left: the reason goes with it
            if await pg.evaluate("() => { const o = document.querySelector('#mbm .fl-over'); return !!(o && !o.hidden) }"):
                await pg.fill('#mbm [data-f="overWhy"]', 'the bench was added by the client; a change order follows')
            await ok(pg, 900)
            po = await pg.evaluate("() => { const o = DB.pos.filter(x => x.lines.some(l => l.materialId === 'mfx1')).pop(); return o && [o.status, !!o.tradeVerified, !!o.tradeVerifiedBy, !!o.templateFirst]; }")
            c.ok(po and po[0] == 'issued' and po[1] and po[2] and not po[3], f'order: with the tick the PO issues, the measurements confirmed on it ({po})')
        # an order a guard holds says which guard and opens the PO (it said only "it was not issued")
        held = await pg.evaluate("""() => { const p = DB.projects.find(x => x.id === 'p121');
            p.materials.push({ id: 'mfx2', name: 'Parlor kitchen built-in shelves', cat: 'finish', taskId: 'millpk', lead: 10, when: 'start', status: 'not-ordered', eta: '', vendor: '', po: '', qty: '1 ea', cost: '', deliverTo: 'Site', notes: '', line: '' });
            const r = flBuyRow({ pid: 'p121', mid: 'mfx2' }), v = DB.vendors.find(x => x.name === 'Gowanus Stone Yard');
            const o = flIssueOrder(r, v, { item: 'Parlor kitchen built-in shelves', qty: 1, unit: 'lot', price: 1200, needBy: '2026-09-24' }, null);
            const t = document.getElementById('toast').innerText; o && (DB.pos = DB.pos.filter(x => x !== o)); return { st: o && o.status, t }; }""")
        c.ok(held['st'] == 'draft' and 'Second measurement' in held['t'] and 'Open' in held['t'], f'order: a PO the measurement gate holds toasts why, with Open ({held})')
        c.ok(not errs, f'order: page errors {errs[:2]}')
    finally:
        await b.close()


# ------------------------------------------------------------------------------------------------ 2. field
async def s_field(p, c):
    b, pg, errs = await fresh(p, ['u_alan', 'u_chen', 'u_angel'])
    try:
        await home(pg, 'u_chen')
        R = await rows(pg)
        g = [r for r in R if 'GWB' in r['text'] and 'Angel' in r['text']]
        c.ok(g and g[0]['verb'] == 'Apply', f"field: Angel's emailed ask is on the coordinator's Needs Your Hand with Apply ({[r['text'][:80] for r in g]})")
        await press(pg, r'Angel asks for 25 boards GWB', r'^Apply$')
        rq = await pg.evaluate("() => (DB.projects.find(x => x.id === 'p121').requests || []).filter(r => /GWB/.test(r.what)).map(r => ({ what: r.what, qty: r.qty, st: r.status, need: r.neededBy, by: r.by }))")
        c.ok(len(rq) == 1 and rq[0]['qty'] == 25 and 'cement board' in rq[0]['what'] and rq[0]['st'] == 'new' and rq[0]['by'] == 'Angel', f'field: the ask is a request on the Buy Board ({rq})')
        # Each recipient's copy (the PM's and the coordinator's) carries the request and reads applied once one of
        # them applies it. Angel's own copy is his sent mail: since the own-mail rule (agent-month selftest,
        # 2026-10-11) the sender's SENT copy proposes nothing to him, so it has no request to read applied. This
        # check predates that rule and counted Angel's copy as a third mailbox to apply.
        left = await pg.evaluate("() => DB.comms.filter(c => /need 25 boards GWB/.test(c.subject)).map(c => ({ u: c.owner, sent: (c.labels || []).includes('SENT'), req: !!c.proposals.find(p => p.kind === 'request'), applied: !!(c.proposals.find(p => p.kind === 'request') || {}).applied }))")
        got = [x for x in left if not x['sent']]
        c.ok(len(got) == 2 and all(x['req'] and x['applied'] for x in got), f"field: every recipient's copy reads applied ({left})")
        c.ok([x['u'] for x in left if x['sent']] == ['u_angel'] and not any(x['req'] for x in left if x['sent']), f"field: Angel's own sent copy proposes nothing to him ({left})")
        # a delivery problem raised Friday afternoon is the coordinator's Monday morning, not escalated past her
        await pg.evaluate("d => appSetDay(d)", '2026-09-11')
        # sent on Friday one hour later in the day than it is now on Monday: 71 hours on the wall, 23 working hours
        await pg.evaluate("() => { __MS.as('u_angel'); setCurrent('p121'); fSend({ type: 'delivery', title: 'Carlos delivered 2 laundry boxes damaged', note: 'Corners crushed.', taskId: 'millpk' }); save(); }")
        await pg.evaluate("d => appSetDay(d)", '2026-09-14')
        st = await pg.evaluate("""() => { const r = DB.field.raises.find(x => /laundry boxes/.test(x.title)), n = new Date(appNowMs() - 71 * 36e5), z = (x) => String(x).padStart(2, '0');
          r.at = `${n.getFullYear()}-${z(n.getMonth() + 1)}-${z(n.getDate())}T${z(n.getHours())}:${z(n.getMinutes())}:00`; r.escalated = false; fTick();
          __MS.as('u_chen'); return { at: r.at, esc: r.escalated, due: r.dueBy, chen: mApprovals().some(a => a.kind === 'raise' && a.id === r.id) }; }""")
        c.ok(not st['esc'] and st['chen'], f'field: on Monday the damaged delivery is in the coordinator\'s Approvals, not escalated over the weekend ({st})')
        c.ok(not errs, f'field: page errors {errs[:2]}')
    finally:
        await b.close()


# ------------------------------------------------------------------------------------------------ 3. change orders
async def s_co(p, c):
    b, pg, errs = await fresh(p, ['u_alan', 'u_angel'])
    try:
        cos = "() => (DB.clients.find(x => x.id === 'cl121').changeOrders || []).map(d => ({ n: d.number, t: d.title, st: d.status, amt: docTotal(d).total }))"
        # the knob-and-tube extra: Angel raises it; the PM answers it from Do Now
        await pg.evaluate("d => appSetDay(d)", '2026-09-25')
        await inject(pg, 'E235')
        v = await press_any(pg, 'u_alan', r'knob-and-tube', r'^Answer$')
        m = await modal(pg)
        c.ok(v == 'Answer' and m and m['fields'].get('co') is True and float(m['fields'].get('coAmt') or 0) == 3200,
             f"co: answering the extra offers Write the Change Order at $3,200 ({m and m['fields']})")
        if m:
            await pg.fill('#mbm [data-f="a"]', 'Replace both bays; photograph first. The CO goes to the Kleins today.')
            await ok(pg, 300)
            await wait_send(pg)
            m2 = await modal(pg)
            c.ok(m2 and re.search(r'Send', m2['ok'] or ''), f"co: the priced draft's send follows ({m2 and (m2['title'], m2['ok'])})")
            if m2: await ok(pg, 900)
        k = [x for x in await pg.evaluate(cos) if 'knob' in x['t'].lower()]
        c.ok(k and k[0]['amt'] == 3200 and k[0]['st'] == 'sent', f'co: the knob-and-tube CO is $3,200 and sent ({k})')
        # the joist extra the PM answered "I will write the CO" (the seed) stays on Do Now until a CO goes out
        R = await listed(pg, 'u_alan', 'joist')
        j = [r for r in R if r['verb'] == 'Write the Change Order']
        c.ok(j, f"co: the joist extra is on the PM's Do Now with Write the Change Order ({[r['text'][:80] for r in R]})")
        if j:
            await press_any(pg, 'u_alan', r'joist', r'^Write the Change Order$')
            m = await modal(pg)
            c.ok(m and 'amount' in m['fields'], f"co: Write the Change Order asks for the amount ({m and m['fields']})")
            if m:
                await pg.fill('#mbm [data-f="amount"]', '1450'); await ok(pg, 300)
                if await wait_send(pg): await ok(pg, 900)
                await pg.wait_for_timeout(500)
            jo = [x for x in await pg.evaluate(cos) if 'joist' in x['t'].lower()]
            c.ok(jo and jo[0]['amt'] == 1450 and jo[0]['st'] == 'sent', f'co: the joist CO is $1,450 and sent ({jo})')
            c.ok(not [r for r in await listed(pg, 'u_alan', 'joist') if 'change order' in r['text'].lower()], 'co: once sent, the joist extra leaves Do Now')
        # the Kleins dispute the joist CO by mail: the PM's Do Now, Answer -> Revise / Explain / Withdraw
        await pg.evaluate("d => appSetDay(d)", '2026-09-22')
        await inject(pg, 'E187'); await sync(pg, 'u_alan')
        d = await listed(pg, 'u_alan', 'disputes')
        c.ok(d and d[0]['verb'] == 'Answer', f"co: the dispute is on the PM's Do Now with Answer ({[r['text'][:90] for r in d]})")
        if d:
            await press_any(pg, 'u_alan', r'disputes', r'^Answer$')
            m = await modal(pg)
            c.ok(m and all(w in m['text'] for w in ('Revise', 'Explain', 'Withdraw')), f"co: Answer offers Revise, Explain, Withdraw ({m and m['text'][:200]})")
            if m:
                await pg.locator('#mbm input[name="fl-disp"][value="revise"]').check()
                await pg.fill('#mbm [data-f="amount"]', '725')
                await pg.fill('#mbm [data-f="why"]', 'The damage was there before; we split the repair.')
                await ok(pg, 900)
                if await modal(pg): await ok(pg, 900)
            r1 = [x for x in await pg.evaluate(cos) if re.search(r'-R\d', x['n'])]
            c.ok(r1 and r1[0]['amt'] == 725, f'co: the revision goes to the Kleins at $725 ({r1})')
        # the client's ask to add an outlet: answering it drafts a CO
        await inject(pg, 'E165')
        v = await press_any(pg, 'u_alan', r'outlet in the pantry', r'^Answer$')
        m = await modal(pg)
        c.ok(m and m['fields'].get('co') is True, f"co: answering the client's ask offers Write the Change Order ({m and m['fields']})")
        if m:
            await pg.fill('#mbm [data-f="a"]', 'Yes; pricing it as a change order for the Kleins.'); await ok(pg, 900)
            if await modal(pg): await pg.keyboard.press('Escape')
        o = [x for x in await pg.evaluate(cos) if 'outlet' in x['t'].lower()]
        c.ok(o and o[0]['st'] in ('draft', 'sent'), f'co: the pantry outlet CO is drafted ({o})')
        c.ok(not errs, f'co: page errors {errs[:2]}')
    finally:
        await b.close()


# ------------------------------------------------------------------------------------------------ 4. a choice by mail
async def s_choice(p, c):
    b, pg, errs = await fresh(p, ['u_owner', 'u_alan'])
    try:
        await home(pg, 'u_alan')
        R = await rows(pg)
        ch = [r for r in R if r['verb'] == 'Record Choice']
        c.ok(ch and 'Calacatta' in ch[0]['text'] and 'honed' in ch[0]['text'], f"choice: the Kleins' mailed choice is on the PM's Do Now with Record Choice ({[r['text'][:90] for r in ch]})")
        if ch:
            await press(pg, r'honed Calacatta', r'^Record Choice$')
            d6 = await pg.evaluate("() => { const d = DB.projects.find(x => x.id === 'p121').decisions.find(x => x.id === 'd6'); return { st: d.status, ch: d.decision, by: d.decidedBy, via: (d.clientChoice || {}).via, who: (d.clientChoice || {}).by }; }")
            c.ok(d6['st'] != 'open' and 'Calacatta' in d6['ch'] and 'Klein' not in d6['by'] and d6['via'] == 'email' and 'Klein' in d6['who'],
                 f'choice: the decision is recorded from the email, by the PM, with the client as the chooser ({d6})')
        await pg.evaluate("() => { __MS.as('u_klein'); view = 'client'; render(); }"); await pg.wait_for_timeout(400)
        cl = await pg.evaluate("() => [...document.querySelectorAll('.cl-waiting .pa-row')].map(e => e.innerText.replace(/\\s+/g, ' '))")
        c.ok(not [x for x in cl if 'backsplash' in x.lower() and 'Choose' in x], f'choice: the portal no longer asks the Kleins to choose the backsplash ({[x[:80] for x in cl if "backsplash" in x.lower()]})')
        # the dated ask: confirm the laundry layout before Friday -> the PM's task due Friday 9/4
        v = await press_any(pg, 'u_alan', r'laundry layout', r'^Make It a Task$')
        m = await modal(pg)
        c.ok(v and m and m['fields'].get('due') == '2026-09-04' and 'laundry' in m['fields'].get('title', '').lower(), f"choice: the laundry ask opens a task due Friday 9/4 ({m and m['fields']})")
        if m:
            await ok(pg, 800)
            t = await pg.evaluate("() => DB.projects.flatMap(p => p.actions || []).concat(DB.tasks || []).filter(a => /laundry/i.test(a.title || '')).map(a => ({ t: a.title, who: a.assignee, due: a.due }))")
            c.ok(t and any('Alan' in (x['who'] or '') and x['due'] == '2026-09-04' for x in t), f'choice: the task is on Alan, due 9/4 ({t})')
        c.ok(not errs, f'choice: page errors {errs[:2]}')
    finally:
        await b.close()


# ------------------------------------------------------------------------------------------------ 5. chases
SENT = """(rx) => { const R = new RegExp(rx, 'i'), out = [];
  (DB.outbox || []).forEach(o => { if (R.test(JSON.stringify(o.to || '') + ' ' + (o.subject || ''))) out.push('outbox:' + (o.to || {}).name + ':' + ((o.to || {}).email || '')); });
  Object.entries(DB.demoWs || {}).forEach(([u, A]) => (A.messages || []).forEach(m => { if ((m.labelIds || []).includes('DRAFT') && R.test(String(m.headers.To) + ' ' + m.headers.Subject)) out.push('draft:' + u + ':' + m.headers.To); }));
  return out; }"""

async def s_chase(p, c):
    b, pg, errs = await fresh(p, ['u_owner', 'u_chen', 'u_billing'])
    try:
        # Tino's COI from the coordinator's Home: the address his mail came from, a draft in her mailbox, an expectation
        await home(pg, 'u_chen')
        await press(pg, r'Tino', r'^Chase( COI)?$')
        m = await modal(pg)
        c.ok(m and m['fields'].get('email') == 'orders@tino.example', f"chase: the chase knows Tino's address from his mail ({m and m['fields'].get('email')!r})")
        if m: await ok(pg, 900)
        s = await pg.evaluate(SENT, 'tino')
        ex = await pg.evaluate("() => paExpectLedger().filter(e => /tino/i.test(e.who)).map(e => e.by)")
        c.ok(any(x.startswith('draft:u_chen') for x in s) and ex, f'chase: a draft to Tino is in the mailbox and the follow-up is logged ({s}, {ex})')
        # the owner's Caught for You: a quiet lead with no address still gets a draft (outbox), and leaves the list
        await home(pg, 'u_owner')
        R = await rows(pg)
        q = [r for r in R if 'Gone quiet' in r['text'] and r['verb'] == 'Chase']
        c.ok(len(q) >= 2, f'chase: quiet leads are on Caught for You ({[r["text"][:50] for r in q]})')
        name = 'The Lindqvists'
        await press(pg, name, r'^Chase$')
        m = await modal(pg)
        if m: await ok(pg, 800)
        s = await pg.evaluate(SENT, 'Lindqvist')
        c.ok(s, f'chase: the Lindqvists, with no address on file, get a draft in the outbox ({s})')
        await home(pg, 'u_owner')
        c.ok(not [r for r in await rows(pg) if name in r['text'] and 'Gone quiet' in r['text']], 'chase: once chased, the lead leaves Caught for You until the follow-up date')
        # Marcus Bell: his address is in the mail
        await press(pg, r'Marcus Bell', r'^Chase$')
        if await modal(pg): await ok(pg, 800)
        await pg.wait_for_timeout(300)
        c.ok(await pg.evaluate(SENT, 'marcus'), f"chase: Marcus Bell's chase is drafted ({await pg.evaluate(SENT, 'marcus')})")
        # billing's Home: the Jessops' retainer a day past due has Chase
        await pg.evaluate("d => appSetDay(d)", '2026-09-16')
        await home(pg, 'u_billing')
        R = await rows(pg)
        j = [r for r in R if 'D140-R' in r['text']]
        c.ok(j and j[0]['verb'] == 'Chase', f"chase: billing's past-due row says Chase ({[r['text'][:80] + ' / ' + r['verb'] for r in j]})")
        if j:
            await press(pg, r'D140-R', r'^Chase$')
            if await modal(pg): await ok(pg, 800)
            await pg.wait_for_timeout(300)
            s = await pg.evaluate(SENT, 'jessop|cambri')
            c.ok(s, f'chase: the reminder to the Jessops is drafted ({s})')
        # a new inquiry: Apply on the lead proposal puts her on file and drafts the reply
        await pg.evaluate("d => appSetDay(d)", '2026-09-04')
        await pg.evaluate("() => { __MS.as('u_owner'); const c = DB.comms.find(x => /70 Remsen/.test(x.subject) && x.owner === 'u_owner'); const p = c.proposals.find(x => x.kind === 'lead'); cmApply(c, p); }")
        if await modal(pg): await ok(pg, 800)
        await pg.wait_for_timeout(400)
        c.ok(await pg.evaluate(SENT, 'adler'), f"chase: Sofia Adler's inquiry gets a reply draft ({await pg.evaluate(SENT, 'adler')})")
        # a lead's two questions: Draft the Reply, not a task
        await pg.evaluate("d => appSetDay(d)", '2026-09-14')
        await inject(pg, 'E115'); await sync(pg, 'u_owner')
        n0 = len(await pg.evaluate(SENT, 'adler'))
        v = await press_any(pg, 'u_owner', r'Sofia Adler asks', r'^Draft the Reply$')
        await pg.wait_for_timeout(500)
        c.ok(v == 'Draft the Reply' and len(await pg.evaluate(SENT, 'adler')) > n0, f"chase: Sofia Adler's questions get a reply draft ({v!r})")
        # a call: Hannah Brooks on file as a lead, and the call back is a task
        await pg.evaluate("d => appSetDay(d)", '2026-09-25')
        await inject(pg, 'E236'); await sync(pg, 'u_owner')
        await pg.evaluate("() => { __MS.as('u_owner'); const c = DB.comms.find(x => /Hannah Brooks/.test(x.subject) && x.owner === 'u_owner'); cmApply(c, c.proposals.find(x => x.kind === 'call')); }")
        await pg.wait_for_timeout(300)
        m = await modal(pg)
        if m: await ok(pg, 800)
        st = await pg.evaluate("() => ({ lead: (DB.leads || []).filter(l => /Brooks/.test(l.name)).map(l => l.stage + ' ' + l.phone), task: DB.projects.flatMap(p => p.actions || []).concat(DB.tasks || []).filter(a => /Hannah Brooks/.test(a.title || '')).map(a => a.title) })")
        c.ok(st['lead'] and st['task'], f'chase: Hannah Brooks is a lead and the call back is a task ({st})')
        # Ines Ward asks to meet 10/6 at 10: Book It holds it on the owner's calendar
        await pg.evaluate("d => appSetDay(d)", '2026-09-29')
        await inject(pg, 'E256'); await sync(pg, 'u_owner')
        v = await press_any(pg, 'u_owner', r'Ines Ward', r'^Book It$')
        m = await modal(pg)
        c.ok(v == 'Book It' and m and m['fields'].get('date') == '2026-10-06' and m['fields'].get('from') == '10:00', f"chase: Book It proposes 10/6 at 10:00 ({m and m['fields']})")
        if m: await ok(pg, 800)
        cal = await pg.evaluate("() => (DB.calendar.external || []).filter(e => e.owner === 'u_owner' && /Ward|Lefferts/.test(e.title) && String(e.start).slice(0, 10) === '2026-10-06').map(e => e.title)")
        c.ok(cal, f'chase: the meeting is on the owner\'s calendar for 10/6 ({cal})')
        c.ok(not errs, f'chase: page errors {errs[:2]}')
    finally:
        await b.close()
    # a proposal the owner sent and nobody answered: an expectation, then Caught for You chases it
    b, pg, errs = await fresh(p, ['u_owner'], '2026-09-11')
    try:
        await inject(pg, 'E102'); await sync(pg, 'u_owner')
        ex = await pg.evaluate("() => { __MS.as('u_owner'); return paExpectLedger().filter(e => /Ines/.test(e.who)).map(e => ({ by: e.by, email: e.email })); }")
        c.ok(ex and ex[0]['by'] == '2026-09-16', f'chase: the proposal to Ines Ward is watched, follow-up 9/16 ({ex})')
        await pg.evaluate("d => appSetDay(d)", '2026-09-16'); await sync(pg, 'u_owner')
        await home(pg, 'u_owner')
        v = await press(pg, r'Not come back: Ines Ward', r'^Chase$')
        if await modal(pg): await ok(pg, 800)
        await pg.wait_for_timeout(400)
        s = await pg.evaluate(SENT, 'ines')
        c.ok(v == 'Chase' and s, f'chase: Caught for You chases Ines Ward ({v!r}, {s})')
        c.ok(not errs, f'chase: page errors {errs[:2]}')
    finally:
        await b.close()


# ------------------------------------------------------------------------------------------------ 6. visits
async def s_visits(p, c):
    b, pg, errs = await fresh(p, ['u_alan', 'u_chen', 'u_angel'], '2026-09-16')
    try:
        await inject(pg, 'E144'); await sync(pg, 'u_chen')
        await home(pg, 'u_chen')
        v = await press(pg, r'Diamond Appliances: delivery', r'^Apply$')
        ev = await pg.evaluate("() => (DB.calendar.external || []).filter(e => e.projectId === 'p121' && /Diamond/.test(e.title)).map(e => [e.kind, e.start, e.end])")
        c.ok(v == 'Apply' and ev and ev[0][1].startswith('2026-09-25T08:00') and ev[0][2].startswith('2026-09-25T12:00'), f'visits: the appliance delivery is on the job calendar 9/25 8-12 ({ev})')
        await pg.evaluate("d => appSetDay(d)", '2026-09-21')
        await inject(pg, 'E186'); await sync(pg, 'u_alan', 'u_angel')
        await home(pg, 'u_chen')
        v = await press(pg, r'Alberto M Plumbing: on site', r'^Apply$')
        c.ok(v == 'Apply', "visits: the plumber's Thursday, mailed to the PM and the foreman, reaches the coordinator's Needs Your Hand")
        for day, rx in (('2026-09-24', 'Alberto M Plumbing'), ('2026-09-25', 'Diamond Appliances')):
            await pg.evaluate("d => appSetDay(d)", day)
            await pg.evaluate("() => { __MS.as('u_angel'); setCurrent('p121'); view = 'ftoday'; render(); }"); await pg.wait_for_timeout(400)
            t = await pg.evaluate("() => ((document.querySelector('.f3-arriving') || {}).innerText || '').replace(/\\s+/g, ' ')")
            c.ok(re.search(rx, t), f"visits: {rx} is on the foreman's Arriving Today on {day} ({t[:200]!r})")
        c.ok(not errs, f'visits: page errors {errs[:2]}')
    finally:
        await b.close()


# ------------------------------------------------------------------------------------------------ 7. owner
async def s_owner(p, c):
    b, pg, errs = await fresh(p, ['u_owner'], '2026-09-23')
    try:
        await inject(pg, 'E206'); await sync(pg, 'u_owner')
        v = await press_any(pg, 'u_owner', r'PW1', r'^Make It a Task$')
        m = await modal(pg)
        c.ok(v and m and m['fields'].get('due') == '2026-09-28' and 'PW1' in m['fields'].get('title', ''), f"owner: the PW1 deadline opens a task due 9/28 ({m and m['fields']})")
        if m:
            await ok(pg, 800)
            t = await pg.evaluate("() => DB.projects.flatMap(p => p.actions || []).concat(DB.tasks || []).filter(a => /PW1/.test(a.title || '')).map(a => [a.assignee, a.due])")
            c.ok(t and t[0][1] == '2026-09-28', f"owner: the owner's task is due 9/28 ({t})")
        v = await press_any(pg, 'u_owner', r'LLC biennial', r'^Draft the Renewal$')
        m = await modal(pg)
        c.ok(v and m and m['fields'].get('next') == '2028-09-28', f"owner: Draft the Renewal on Do Now opens the filing with the next period ({m and m['fields']})")
        if m:
            await ok(pg, 800)
            o = await pg.evaluate("() => { const o = DB.obligations.find(x => /biennial/i.test(x.name)); return { exp: o.expires, st: o.status, h: (o.history || []).length }; }")
            c.ok(o['exp'] == '2028-09-28' and o['h'] == 1, f'owner: the filing is recorded; the register runs to 9/28/2028 ({o})')
            c.ok(not await listed(pg, 'u_owner', 'biennial'), 'owner: once filed it leaves Do Now')
        c.ok(not errs, f'owner: page errors {errs[:2]}')
    finally:
        await b.close()


# ------------------------------------------------------------------------------------------------ 8. client
async def s_client(p, c):
    b, pg, errs = await fresh(p, ['u_chen'], '2026-09-04')
    try:
        await pg.evaluate("() => { __MS.as('u_klein'); __MS.open('client', true); }"); await pg.wait_for_timeout(300)
        its = await pg.evaluate("() => __MS.items('client').map(i => ({ t: i.text.slice(0, 60), v: i.verbs.map(x => x.label) }))")
        s = [i for i in its if 'tile' in i['t'].lower() and 'sample' in i['t'].lower()]
        c.ok(s and 'Approve' in s[0]['v'], f"client: the month's client sees Approve on the tile sample, as the client does ({s})")
        await pg.locator('[data-smcl="ok|sb121tile2"]:visible').first.click(timeout=4000); await pg.wait_for_timeout(400)
        await ok(pg, 700)
        st = await pg.evaluate("() => smOf(DB.projects.find(x => x.id === 'p121')).find(s => s.id === 'sb121tile2').status")
        c.ok(st == 'approved', f'client: the sample is approved from the portal ({st})')
        # the coordinator can now order it: the Nemo quote on the line, one tap through
        await pg.evaluate("() => { __MS.as('u_chen'); const c = DB.comms.find(x => (x.proposals || []).some(p => p.kind === 'quote' && p.materialId === 'm9')); cmApply(c, c.proposals.find(p => p.kind === 'quote' && p.materialId === 'm9')); }")
        await pg.wait_for_timeout(300)
        m = await modal(pg)
        c.ok(m and m['fields'].get('vendor') == 'Nemo Tile', f"client: the released tile opens its order with Nemo Tile ({m and m['fields']})")
        if m:
            await ok(pg, 900)
            po = await pg.evaluate("() => { const o = DB.pos.find(x => x.lines.some(l => l.materialId === 'm9')); return o && [o.number, o.status, o.vendor, poTotal(o).total]; }")
            c.ok(po and po[1] == 'issued', f'client: the tile PO is issued ({po})')
        c.ok(not errs, f'client: page errors {errs[:2]}')
    finally:
        await b.close()


SECTIONS = {'order': s_order, 'field': s_field, 'co': s_co, 'choice': s_choice, 'chase': s_chase, 'visits': s_visits, 'owner': s_owner, 'client': s_client}

async def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--section', default='')
    a = ap.parse_args()
    run = [s for s in (a.section.split(',') if a.section else SECTIONS) if s]
    c = Checks()
    async with async_playwright() as p:
        for s in run:
            print('--', s, flush=True)
            try:
                await SECTIONS[s](p, c)
            except Exception as e:
                c.ok(False, f'{s}: stopped — {str(e).splitlines()[0][:200]}')
    sys.exit(c.done())

if __name__ == '__main__':
    asyncio.run(main())
