"""Cross-set consistency (BACKLOG §1.23 phase 1): the AI checks every set against the others. Done as the people who do it.

  designer   Sarah issues A-501 Rev B (rear window W-3 widened) that conflicts with the LPC set: the check runs on the
             new revision, Rev B is issued but not for construction, the findings name both values, the sheets, the
             location and a confidence, LPC governs what is legal and the amendment is flagged, the area under way is
             held on its own, the RFI is routed to the drawing's owner with a due date from the schedule; the toast's
             Open lands on the finding.
  beam       the pilot's miss, as an invented analogue: CALC-S2 (9/1) put the steel post at the garden bedroom's rear
             wall; A-102 Rev B (9/2) moved the wall. Alan runs Check the Sets: a safety finding, framing held, the
             engineer of record asked by an email draft, due before framing starts; Caught for You ranks it first.
  order      Chen tries to order millwork for the parlor kitchen held by the shop drawing conflict: the PO is refused
             with the set check named, the PO page says so, the order already placed is flagged, procurement was told.
  field      at 390px Angel sees the hold on his Today in plain words, with the sheet one tap away, Started warns,
             nothing scrolls sideways and the targets are big enough.
  resolve    Sarah resolves the LPC conflict: A-501 Rev C, Rev B VOID, both findings settled, Angel acknowledges and
             the hold lifts; the engineer's revised calc resolves the beam case (our cost); the kitchen goes to the sub
             (a backcharge, drafted); a client's change on the backsplash becomes a change order.
  owner      the owner sees the measures on Plans and Reports (found before work against the field, rework avoided,
             our cost, days to resolve), the brain's proposed lesson, approves it, and the checklist is on New Revision.
  findable   erpQuery, ⌘K, Ask, Needs Your Hand; every new CATCH id mapped to a line of the Standard; the predicate's
             count is its rows; after a reload the findings and the history are kept; no page errors.
Invented data only."""
import asyncio
from harness import async_playwright, open_app, sign_in, Checks

TOAST_OPEN = """() => { const t = document.getElementById('toast'); if (!t) return false;
  const a = [...t.querySelectorAll('a, button')].find(x => /^Open$/.test((x.innerText || '').trim())); if (!a) return false; a.click(); return true; }"""
TOAST = "() => (document.getElementById('toast') || {}).innerText || ''"
CLOSE = """() => { document.querySelectorAll('#mbm').forEach(m => m.remove()); const v = document.getElementById('viewer'); v && v.classList.remove('on'); }"""
PRIMARY = """() => [...document.querySelectorAll('.view.on .btn.primary')].filter(b => b.getClientRects().length && getComputedStyle(b).visibility !== 'hidden').length"""
SW = "() => document.documentElement.scrollWidth"
SEEN = """(sel) => { const e = document.querySelector(sel); if (!e) return null; const r = e.getBoundingClientRect();
  return { vis: r.height > 0 && r.bottom > 0 && r.top < innerHeight, flash: e.classList.contains('tk-flash'), text: e.innerText }; }"""


async def click(pg, sel, wait=300):
    await pg.evaluate("s => { const e = document.querySelector(s); if (!e) throw new Error('no ' + s); e.click(); }", sel)
    await pg.wait_for_timeout(wait)


async def plans(pg, uid):
    await sign_in(pg, uid)
    await pg.evaluate("() => { setCurrent('p121'); plStatusF = 'current'; plSetF = ''; view = 'plans'; render(); }")
    await pg.wait_for_timeout(300)


async def designer_lpc(c, pg):
    await plans(pg, 'u_sarah')
    c.ok(await pg.evaluate("() => !!document.querySelector('.view.on #xs-card') && !!document.querySelector('.view.on [data-xscheck]')"), "designer: Plans carries the Set Check card with Check the Sets")
    await click(pg, '.view.on [data-plnew="A-501"]')
    gate = await pg.evaluate("() => (document.querySelector('#mbm .xs-gate') || {}).innerText || ''")
    c.ok('Issued for Construction' in gate, f"designer: New Revision says the check gates Issued for Construction ({gate[:60]})")
    await pg.fill('#mbm [data-f="changed"]', 'Rear window W-3 widened from 3\'-2" to 3\'-6" for egress at the third floor')
    await click(pg, '#mbm #mbm-ok', 700)
    r = await pg.evaluate("""() => { const s = plCurrent('p121', 'A-501'), F = xsFindings('p121', { status: 'open' }).filter(f => [f.a.sheetId, f.b.sheetId].includes(s.id));
      const lpc = F.find(f => f.a.number === 'L-201' || f.b.number === 'L-201'), shop = F.find(f => f.a.number === 'WW-1187' || f.b.number === 'WW-1187');
      const w = (s.facts || []).find(x => x.key === 'win:W-3:width'), p = plJob('p121'), iss = lpc && p.issues.find(i => i.id === lpc.issueId);
      return { rev: s.rev, st: plStatus(s), gate: !!s.xsGate, val: w && w.value, n: F.length, toast: (document.getElementById('toast') || {}).innerText || '',
        lpc: lpc && { a: [lpc.a.number, lpc.a.value], b: [lpc.b.number, lpc.b.value], rule: lpc.rule, conf: lpc.conf, loc: lpc.loc, room: lpc.room, risk: lpc.risk.tags, amend: lpc.amend, owner: lpc.owner.kind, due: lpc.due, need: lpc.needBy, held: lpc.holdIds.length, id: lpc.id },
        shop: shop && { gov: shop.a.number, owner: shop.owner.kind, draft: !!(DB.outbox || []).find(o => o.id === shop.draftId && o.status === 'draft') },
        iss: iss && [iss.type, iss.status, iss.owner, iss.due], hold: plHolds('p121').filter(h => h.roomId === 'r121ext').map(h => h.why) }; }""")
    c.ok(r['rev'] == 'B' and r['val'] == '3\'-6"', f"designer: A-501 Rev B is read with W-3 at 3'-6\" ({r['rev']}, {r['val']})")
    c.ok(r['st'] == 'revision' and r['gate'], f"designer: the check keeps Rev B from Issued for Construction ({r['st']})")
    L = r['lpc'] or {}
    c.ok(L and L.get('a') == ['L-201', '3\'-2"'] and L.get('b') == ['A-501', '3\'-6"'], f"designer: the finding names both values and both sheets, LPC first ({L.get('a')}, {L.get('b')})")
    c.ok(L.get('rule') == 'legal' and L.get('amend', {}).get('agency') == 'LPC', f"designer: filed LPC governs what is legal and the amendment is flagged ({L.get('rule')}, {L.get('amend')})")
    c.ok(L.get('conf') and 0 < L['conf'] <= 1 and L.get('loc') and L.get('room') == 'r121ext', f"designer: with its location and a confidence ({L.get('loc')}, {L.get('conf')})")
    c.ok('work' in (L.get('risk') or []) and 'filed' in (L.get('risk') or []) and L.get('held') == 1 and r['hold'], f"designer: work under way there, so the facade is held on its own ({L.get('risk')})")
    c.ok(L.get('owner') == 'designer' and r['iss'] and r['iss'][0] == 'rfi' and r['iss'][3] == L.get('due') and L.get('need'), f"designer: an RFI to our designer, due from the schedule ({r['iss']}, {L.get('need')})")
    c.ok(r['shop'] and r['shop']['gov'] == 'A-501' and r['shop']['owner'] == 'sub' and r['shop']['draft'], f"designer: the window shop drawing must match the construction documents: Window Works asked by email draft ({r['shop']})")
    c.ok('not for construction' in r['toast'] and 'Open' in r['toast'], f"designer: the toast says so, with Open ({r['toast'][:90]})")
    await pg.evaluate("() => { view = 'sday'; render(); }")
    opened = await pg.evaluate(TOAST_OPEN); await pg.wait_for_timeout(400)
    s = await pg.evaluate(SEEN, f'.view.on [data-xsfind="{L.get("id")}"]')
    c.ok(opened and s and s['vis'] and s['flash'], f"designer: the toast's Open lands on the finding, highlighted ({s and s['vis']})")
    c.ok(s and 'Filed DOB and LPC drawings govern what is legal' in s['text'] and 'LPC filed drawing' in s['text'], "designer: the finding shows the order of precedence and the amendment")
    c.ok(await pg.evaluate(PRIMARY) == 1, "designer: one blue button on Plans")
    await click(pg, f'.view.on [data-xsrfi="{L.get("id")}"]', 500)
    e = await pg.evaluate("() => ({ view, drawer: document.getElementById('drawer').classList.contains('on'), t: (document.getElementById('e-name') || {}).value || '' })")
    c.ok(e['view'] == 'field' and e['drawer'] and 'set check' in e['t'], f"designer: Open RFI lands on the RFI in the job's field list ({e['t'][:60]})")
    await pg.evaluate("() => { document.getElementById('drawer').classList.remove('on'); document.getElementById('scrim').classList.remove('on'); }")
    return L.get('id')


async def beam(c, pg):
    await plans(pg, 'u_alan')
    await click(pg, '.view.on [data-xscheck]', 700)
    r = await pg.evaluate("""() => { const f = xsFindings('p121', { status: 'open' }).find(f => f.key === 'dim:r121gbr:rear-wall');
      const d = f && (DB.outbox || []).find(o => o.id === f.draftId), p = plJob('p121'), t = p.tasks.find(x => x.id === 'gframe');
      return f && { id: f.id, safety: f.safety, rule: f.rule, a: [f.a.number, f.a.value], b: [f.b.number, f.b.value, f.b.assume], risk: f.risk.tags, owner: [f.owner.kind, f.owner.name], due: f.due,
        draft: d && [d.to.email, d.subject, d.status], held: plHolds('p121').some(h => h.roomId === 'r121gbr' && (h.xsFindings || []).includes(f.id)),
        wait: plTaskReasons(p, t).map(x => x.text), toast: (document.getElementById('toast') || {}).innerText || '', found: f.foundAt,
        catch: CATCH.find(x => x.name === 'xsetSafety').rows().map(x => x.what) }; }""")
    c.ok(r and r['safety'] and r['rule'] == 'calc', f"beam: the engineer's calc against the moved wall is a safety finding ({r and r['rule']})")
    c.ok(r and r['a'] == ['A-102', '15\'-8"'] and r['b'][:2] == ['CALC-S2', '16\'-4"'] and r['b'][2], f"beam: A-102 Rev B 15'-8\" against the calc's assumption 16'-4\" ({r and r['a']}, {r and r['b']})")
    c.ok(r and 'work' in r['risk'] and r['held'] and any('garden bedroom' in x.lower() or 'Garden bedroom' in x for x in r['wait']), f"beam: framing starts this week, so the garden bedroom is held ({r and r['wait'][:1]})")
    c.ok(r and r['owner'][0] == 'eor' and r['draft'] and r['draft'][0] and r['draft'][2] == 'draft', f"beam: the engineer of record is asked by an email draft ({r and r['draft']})")
    c.ok(r and '2026-09-03' <= r['due'] < '2026-09-08' and r['found'] == 'before', f"beam: due before framing starts on 9/8, found before work ({r and r['due']})")
    c.ok(r and 'safety' in r['toast'] and 'Open' in r['toast'], f"beam: the toast counts the safety finding, with Open ({r and r['toast'][:100]})")
    c.ok(r and any('Rear wall' in x or 'rear wall' in x for x in r['catch']), f"beam: Caught for You names it ({r and r['catch']})")
    await sign_in(pg, 'u_owner')
    k = await pg.evaluate("""() => { const C = tdCaught(tdQueue()); const i = C.findIndex(x => /^Safety: /.test(x.what || x.title || '')); return { i, n: C.length, first: (C[0] || {}).what || (C[0] || {}).title || '' }; }""")
    c.ok(k['i'] == 0, f"beam: the safety finding ranks first in the owner's Caught for You ({k})")
    return r and r['id']


async def order(c, pg):
    await sign_in(pg, 'u_chen')
    r = await pg.evaluate("""() => { setCurrent('p121');
      const po = { id: 'poXS1', number: 'PO-2026-XS1', vendor: 'Carlos Millwork', projectId: 'p121', status: 'draft', type: 'subcontract', date: today(), needBy: '2026-09-20',
        lines: [{ id: 'l1', item: 'Parlor kitchen upper cabinets and island panels', qty: 1, unit: 'ls', price: 9800, line: '' }] };
      DB.pos.push(po); const reasons = poValid(po); poAction(po, 'issue');
      const f = xsFindings('p121', { status: 'open' }).find(f => f.key === 'dim:r121pk:island');
      const me = (DB.asst.u_chen || { thread: [] }).thread.filter(m => m.ref && m.ref.kind === 'xset').map(m => m.text);
      return { reasons: reasons.filter(x => /Parlor kitchen/.test(x)), status: po.status, toast: (document.getElementById('toast') || {}).innerText || '', f: f && [f.a.number, f.b.number, f.owner.kind, f.risk.tags],
        told: me, nyh: nyhRows().filter(r => /^xshold:/.test(r.key)).map(r => r.title), ordered: CATCH.find(x => x.name === 'plansOrderedInRevision').rows().map(r => r.what) }; }""")
    c.ok(r['f'] and r['f'][:3] == ['A-202', 'SD-1', 'sub'] and 'fab' in r['f'][3], f"order: the shop drawing disagrees with A-202, millwork in fabrication ({r['f']})")
    c.ok(r['reasons'] and 'set check' in r['reasons'][0] and 'order anyway with a reason' in r['reasons'][0], f"order: the PO for the held kitchen carries the set check as its reason ({r['reasons'][:1]})")
    c.ok(r['status'] == 'draft' and 'Parlor kitchen' in r['toast'], f"order: and is refused at Issue ({r['toast'][:90]})")
    c.ok(any('PO-2026-048' in x for x in r['ordered']), f"order: the millwork already ordered is flagged ({r['ordered']})")
    c.ok(any('PO-2026-048' in x for x in r['told']) and r['nyh'], f"order: procurement was told and holds the order from Needs Your Hand ({r['nyh']})")
    w = await pg.evaluate("() => { poOpen = 'poXS1'; view = 'po'; render(); const w = document.querySelector('.view.on .pl-warn'); return w ? w.innerText : ''; }")
    c.ok('Parlor kitchen' in w and 'set check' in w, f"order: the PO page says why ({w[:90]})")


async def field(c, p):
    b, pg, errs = await open_app(p, phone=True)
    await pg.evaluate("() => { signIn('u_alan'); setCurrent('p121'); xsCheck('p121', { trigger: 'demand' }); save(); }")
    await sign_in(pg, 'u_angel')
    await pg.evaluate("() => { setCurrent('p121'); view = 'ftoday'; render(); }"); await pg.wait_for_timeout(400)
    r = await pg.evaluate("""() => { const card = document.querySelector('.view.on .xs-fyou'); const b = card && card.querySelector('[data-plopen]');
      const br = b && b.getBoundingClientRect(); const t = (DB.asst.u_angel || { thread: [] }).thread.filter(m => m.ref && m.ref.kind === 'xset').length;
      return { text: card ? card.innerText : '', h: br ? Math.round(br.height) : 0, sw: document.documentElement.scrollWidth, told: t }; }""")
    c.ok('Do not start' in r['text'] and 'Framing' in r['text'] and 'engineer' in r['text'], f"field: Angel sees the hold on his phone in plain words ({r['text'][:100]})")
    c.ok('answers by' in r['text'] and r['h'] >= 44, f"field: who answers by when, and the sheet one big tap away ({r['h']}px)")
    c.ok(r['sw'] <= 390 and r['told'] >= 1, f"field: no sideways scroll at 390px ({r['sw']}); his assistant told him ({r['told']})")
    await pg.evaluate("() => { const row = [...document.querySelectorAll('.view.on .xs-fyou .xs-frow')].find(e => /Framing/.test(e.innerText)); row.querySelector('[data-plopen]').click(); }"); await pg.wait_for_timeout(600)
    v = await pg.evaluate("() => ({ on: document.getElementById('viewer').classList.contains('on'), name: document.getElementById('v-name').textContent })")
    c.ok(v['on'] and 'A-102' in v['name'], f"field: one tap opens the current sheet ({v['name']})")
    await pg.evaluate(CLOSE)
    m = await pg.evaluate("() => { const t = S.tasks.find(x => x.id === 'gframe'); return fTaskNeeds(t).filter(n => n.k === 'plan').map(n => n.t); }")
    c.ok(any('set check' in x for x in m), f"field: the held framing carries the hold into the look-ahead and the Started warning ({m[:1]})")
    await sign_in(pg, 'u_sarah')
    await pg.evaluate("() => { setCurrent('p121'); view = 'plans'; render(); }"); await pg.wait_for_timeout(300)
    c.ok(await pg.evaluate(SW) <= 390 and await pg.evaluate("() => !!document.querySelector('.view.on .xs-find')"), "field: the designer's Plans with its findings does not scroll sideways at 390px")
    c.ok(not errs, f'field: no page errors on the phone {errs[:3]}')
    await b.close()


async def resolve(c, pg, lpc_id, beam_id):
    # the designer resolves the LPC conflict: LPC governs, W-3 stays 3'-2"
    await plans(pg, 'u_sarah')
    await pg.evaluate("id => { xsShowResolved = false; render(); }", lpc_id)
    await click(pg, f'.view.on [data-xsresolve="{lpc_id}"]')
    pv = await pg.evaluate("() => (document.getElementById('xs-res-prev') || {}).innerText || ''")
    c.ok('A-501 Rev C' in pv and 'VOID' in pv, f"resolve: the dialog says which sheet is revised and which goes VOID ({pv[:70]})")
    await pg.fill('#mbm [data-f="amount"]', '350')
    await click(pg, '#mbm #mbm-ok', 700)
    r = await pg.evaluate("""id => { const f = xsRow(id), s = plCurrent('p121', 'A-501'), old = plDB().sheets.find(x => x.projectId === 'p121' && x.number === 'A-501' && x.rev === 'B'), p = plJob('p121');
      const shop = xsFindings('p121', { all: true }).find(x => x.key === 'win:W-3:width' && x.id !== id), h = plDB().holds.find(x => (x.xsFindings || []).includes(id));
      return { st: f.status, rev: s.rev, ifc: plStatus(s), old: old.status, oldGate: !!s.xsGate, shop: shop && shop.status, liftOn: h && h.liftOn === s.id, lifted: !!(h && h.liftedAt),
        rfi: (p.issues.find(i => i.id === f.issueId) || {}).status, money: f.money && [f.money.payer, f.money.ours], toast: (document.getElementById('toast') || {}).innerText || '', need: plAckState(s).pending.map(n => n.name), sid: s.id }; }""", lpc_id)
    c.ok(r['st'] == 'resolved' and r['rev'] == 'C' and r['old'] == 'superseded' and r['ifc'] == 'ifc', f"resolve: A-501 Rev C is Issued for Construction and Rev B is VOID ({r['rev']}, {r['ifc']}, {r['old']})")
    c.ok(r['shop'] == 'resolved' and r['rfi'] == 'closed', f"resolve: the window shop drawing conflict settles with it and the RFI closes ({r['shop']}, {r['rfi']})")
    c.ok(r['liftOn'] and not r['lifted'] and 'Angel' in r['need'], f"resolve: the hold waits for the field's acknowledgment, the foreman and the window trade ({r['need']})")
    c.ok(r['money'] == ['ours', 350] and 'Our Design or Coordination Error' in r['toast'] and 'Open' in r['toast'], f"resolve: our error is our cost, tracked ({r['money']}, {r['toast'][:80]})")
    await sign_in(pg, 'u_angel')
    a = await pg.evaluate("""([sid, id]) => { setCurrent('p121'); plAckNow(sid); plAck(sid, { vendor: 'Window Works', how: 'by email' }); const h = plDB().holds.find(x => (x.xsFindings || []).includes(id)), p = plJob('p121'), t = p.tasks.find(x => x.id === 'ext');
      return { lifted: !!(h && h.liftedAt), wait: plTaskReasons(p, t).map(x => x.text), a501: plStatus(plCurrent('p121', 'A-501')) }; }""", [r['sid'], lpc_id])
    c.ok(a['lifted'] and not a['wait'] and a['a501'] == 'ifc', f"resolve: Angel acknowledges, Window Works' confirmation is recorded, and the hold lifts ({a})")
    # the engineer's revised calc resolves the beam case; our coordination error (the 9/2 change never went to her)
    await sign_in(pg, 'u_alan')
    b = await pg.evaluate("""id => { setCurrent('p121'); const row = xsResolve(id, { stand: 'a', changed: 'Engineer re-ran the beam and post for the rear wall at 15\\'-8"; the post moves with the wall, W8x18 holds', payer: 'ours', amount: 450, issuer: 'Maya Natarajan, PE (structural consultant)' }); save(); render();
      const f = xsRow(id); return { rev: row && row.rev, num: row && row.number, st: f.status, ours: f.money.ours, cs: (plCurrent('p121', 'CALC-S2').facts.find(x => x.key === 'dim:r121gbr:rear-wall') || {}).value, a102: plStatus(plCurrent('p121', 'A-102')) }; }""", beam_id)
    c.ok(b['num'] == 'CALC-S2' and b['rev'] == '2' and b['st'] == 'resolved' and b['cs'] == '15\'-8"', f"resolve: CALC-S2 Rev 2 at 15'-8\" resolves the safety finding ({b})")
    await sign_in(pg, 'u_angel')
    a2 = await pg.evaluate("""id => { setCurrent('p121'); const s = plCurrent('p121', 'CALC-S2'); plAckNow(s.id); const p = plJob('p121'), t = p.tasks.find(x => x.id === 'gframe');
      return { wait: plTaskReasons(p, t).filter(x => /set check|revision/i.test(x.text)).map(x => x.text), a102: plStatus(plCurrent('p121', 'A-102')) }; }""", beam_id)
    c.ok(not a2['wait'] and a2['a102'] == 'ifc', f"resolve: after the field acknowledges, the framing is released and A-102 is back to Issued for Construction ({a2})")
    # the kitchen: the shop drawing must match A-202; it cost us a site visit, backcharged
    await sign_in(pg, 'u_alan')
    k = await pg.evaluate("""() => { const f = xsFindings('p121', { status: 'open' }).find(x => x.key === 'dim:r121pk:island');
      const row = xsResolve(f.id, { stand: 'a', changed: 'Island panels redrawn at 8\\'-0" to match A-202 Rev C', payer: 'consultant', amount: 600 }); save();
      const d = (DB.outbox || []).find(o => o.id === f.money.draftId); return { num: row && plRev(row), bc: f.money.backcharge, draft: d && [d.kind, d.to.name, d.status], ripple: f.money.ripple }; }""")
    c.ok(k['num'] == 'SD-1 Rev 2' and k['bc'] == 600 and k['draft'] == ['backcharge', 'Carlos Millwork', 'draft'], f"resolve: SD-1 Rev 2 from Carlos, the cost backcharged by a drafted notice ({k})")
    c.ok(any('PO-2026-048' in x for x in k['ripple']), f"resolve: the ripple names the order to correct ({k['ripple']})")
    # a client's change: the Kleins chose the polished backsplash shown in the presentation
    co = await pg.evaluate("""() => { const f = xsFindings('p121', { status: 'open' }).find(x => x.key === 'fin:r121gk:backsplash'); const n0 = DB.clients.find(c => c.id === 'cl121').changeOrders.length;
      const row = xsResolve(f.id, { stand: 'b', changed: 'Backsplash polished Calacatta marble, the Kleins chose the presentation finish', payer: 'client', amount: 1850 }); save();
      const C = DB.clients.find(c => c.id === 'cl121').changeOrders, d = C.find(x => x.id === f.money.coId);
      return { num: row && plRev(row), co: d && [d.status, d.projectId, docTotal(d).total], n: C.length - n0, risk: f.risk.top }; }""")
    c.ok(co['num'] == 'FS-01 Rev C' and co['co'] and co['co'][0] == 'draft' and co['co'][1] == 'p121' and abs(co['co'][2] - 1850) < 1 and co['n'] == 1, f"resolve: a client change becomes a change order draft ({co})")


async def owner(c, pg):
    await sign_in(pg, 'u_owner')
    await pg.evaluate("() => { setCurrent('p121'); view = 'plans'; render(); }"); await pg.wait_for_timeout(300)
    r = await pg.evaluate("""() => { const M = xsMeasures('p121'), k = {}; document.querySelectorAll('.view.on .xs-kpis .kpi').forEach(e => k[e.querySelector('span').innerText] = e.querySelector('b').innerText);
      const all = xsMeasures(); return { M, k, all }; }""")
    M, k = r['M'], r['k']
    c.ok(M['before'] + M['field'] == M['found'] and int(k.get('Found Before Work', -1)) == M['before'] and int(k.get('Found in the Field', -1)) == M['field'], f"owner: Plans shows found before work against in the field ({k})")
    c.ok(M['ours'] >= 800 and 'Rework Avoided' in k and 'Days to Resolve' in k and int(k.get('Open Conflicts', -1)) == M['open'], f"owner: rework avoided, our cost, days to resolve, open ({M['ours']}, {k.get('Days to Resolve')})")
    await pg.evaluate("() => { view = 'reports'; repTab = 'company'; render(); }"); await pg.wait_for_timeout(500)
    t = await pg.evaluate("""() => { const t = document.querySelector('.view.on #xs-rep'); if (!t) return null; const tot = [...t.querySelectorAll('tr.xs-total td')].map(x => x.innerText);
      return { tot, rows: t.querySelectorAll('tbody tr').length, lead: t.querySelector('p').innerText }; }""")
    c.ok(t and int(t['tot'][1]) == r['all']['found'] and int(t['tot'][2]) == r['all']['before'] and t['rows'] >= 3, f"owner: Reports carry the measures, firm-wide and by job ({t and t['tot'][:4]})")
    c.ok(t and 'raises' in t['lead'], "owner: our cost says what wasted money cannot pay for")
    les = await pg.evaluate("""() => { lnLoop('test'); const P = lnInit().props.xset; return P && { st: P.status, title: P.title, n: P.events.length }; }""")
    c.ok(les and les['st'] == 'proposed' and les['n'] >= 5 and 'presentation' in les['title'], f"owner: the issue log feeds a proposed lesson ({les})")
    a = await pg.evaluate("""() => { const l = lnApprove('xset', 'test'); return l && [l.learn, l.then.kind]; }""")
    c.ok(a == ['xset', 'checklist'], f"owner: the owner approves it as a pre-issue checklist ({a})")
    await sign_in(pg, 'u_sarah')
    await pg.evaluate("() => { setCurrent('p121'); view = 'plans'; render(); }"); await pg.wait_for_timeout(250)
    await click(pg, '.view.on [data-plnew="A-102"]')
    ck = await pg.evaluate("() => [...document.querySelectorAll('#mbm .xs-pre .chk')].map(e => e.innerText)")
    c.ok(len(ck) >= 2 and any('engineer of record' in x for x in ck) and any('presentation' in x for x in ck), f"owner: the checklist is on New Revision ({len(ck)})")
    await pg.evaluate(CLOSE)


async def findable(c, pg):
    await sign_in(pg, 'u_owner')
    r = await pg.evaluate("""() => { const q = erpQuery({ entity: 'setfindings' }), F = xsDB().findings, k = palIndex().filter(i => i.k === 'Set Check');
      const keys = ['xsetSafety', 'xsetConflict', 'nyh:xset', 'nyh:xsethold', 'learn:xset'];
      const a = paAsk('which drawing sets disagree on 121 State?');
      return { q: q.rows.length === F.length, k: k.length === F.filter(f => !f.seed).length && k.length > 0, facts: erpQuery({ entity: 'facts' }).rows.length,
        mapped: keys.filter(k0 => !(standardMapOf(k0).exact && /^Because: .+ \\(.+\\)$/.test(standardWhy(k0)))), inCatch: ['xsetSafety', 'xsetConflict'].every(k0 => CATCH.some(x => x.name === k0)),
        pred: PRED.xsetOpen && PRED.xsetOpen.count() === PRED.xsetOpen.rows().length, ask: a.headline, open: xsFindings('', { status: 'open' }).length }; }""")
    c.ok(r['q'] and r['facts'] >= 20, f"findable: every finding and the facts read are in erpQuery ({r['facts']} facts)")
    c.ok(r['k'], "findable: ⌘K finds every finding")
    c.ok(not r['mapped'] and r['inCatch'], f"findable: every new CATCH id is mapped to a line of the Standard ({r['mapped']})")
    c.ok(r['pred'], "findable: the predicate's count is its rows")
    c.ok(('No open' in r['ask'] and r['open'] == 0) or str(r['open']) in r['ask'], f"findable: Ask answers the open conflicts ({r['ask'][:80]})")
    await pg.evaluate("async () => { await saveNow(); }")
    n0 = await pg.evaluate("() => xsDB().findings.length")
    await pg.reload(); await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
    await sign_in(pg, 'u_sarah')
    await pg.evaluate("() => { setCurrent('p121'); xsShowResolved = true; view = 'plans'; render(); }"); await pg.wait_for_timeout(300)
    a = await pg.evaluate("() => ({ n: xsDB().findings.length, shown: document.querySelectorAll('.view.on .xs-find').length, a501: plCurrent('p121', 'A-501').rev, seeded: plDB().sheets.filter(s => s.id === 'sh121a102b').length })")
    c.ok(a['n'] == n0 and a['shown'] >= 1 and a['a501'] == 'C' and a['seeded'] == 1, f"findable: after a reload the findings and revisions are kept, the seed not repeated ({a}, {n0})")


async def main():
    c = Checks()
    async with async_playwright() as p:
        await field(c, p)
        b, pg, errs = await open_app(p)
        lpc = await designer_lpc(c, pg)
        bid = await beam(c, pg)
        await order(c, pg)
        await resolve(c, pg, lpc, bid)
        await owner(c, pg)
        await findable(c, pg)
        c.ok(not errs, f'desktop: no page errors {errs[:3]}')
        await b.close()
    return c.done()


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
