"""Plans control (BACKLOG §1.22 phase 1): nobody builds from an outdated drawing. Done as the people who do it.

  register   121 State's register: one row per revision, sets and statuses, a superseded revision VOID; the Plans
             page per job (sheet index, filter by set and status), current sheets only by default.
  void       a superseded revision never opens as current: it opens stamped VOID, with the way to the current one,
             from the Plans page and from Documents.
  designer   Sarah marks the garden kitchen In Revision, then issues A-201 Rev C from an uploaded file: the old
             revision is VOID, the row is on her screen highlighted, the toast's Open lands on it, the field is
             told in the job's thread, and after a reload it is still in the register.
  order      Chen tries to order cabinets for the garden kitchen while it is in revision: the PO is refused with
             the reason, the PO page says so, an RFQ is not sent, a field request is flagged for procurement; the
             PM cannot override; Chen orders anyway with a reason recorded.
  field      at 390px Angel sees the new revision on Today, opens it and acknowledges it; who saw which revision and
             when is kept; tasks in the area wait for that acknowledgment, the hold lifts after it; a task in an
             area in revision shows the hold and warns before Started; the schedule shows the hold.
  mail       a PDF from the architect saying "A-301 rev 3" becomes a proposal on the PM's Needs Your Hand; the PM
             confirms it in one tap; meeting notes and a job message propose the same way.
  filed      a revision of a sheet filed with DOB is flagged "amendment needed before this work"; the work there is
             held until the PM records the approval.
  impact     what changed and what it touches: tasks, open POs, selections, estimate lines, the follow-ups.
  thread     the job's thread and the job's page pin current sheets only.
  switch     switching job on Plans (and the Studio's Drawings) shows that job's sheets, desktop and phone.
  question   the field question naming A-301 opens the current A-301 in one tap from the designer's My Day, on
             desktop and phone; the designer reaches every job's Plans page.
  findable   erpQuery, ⌘K, Ask; every new CATCH id mapped to a line of the Standard; one blue button; no sideways
             scroll at 390px; no page errors.
Invented data only."""
import asyncio, os, tempfile, base64
from harness import async_playwright, open_app, sign_in, go, Checks

TOAST_OPEN = """() => { const t = document.getElementById('toast'); if (!t) return false;
  const a = [...t.querySelectorAll('a, button')].find(x => /^Open$/.test((x.innerText || '').trim())); if (!a) return false; a.click(); return true; }"""
TOAST_TEXT = "() => (document.getElementById('toast') || {}).innerText || ''"
CLOSE = """() => { document.querySelectorAll('#mbm').forEach(m => m.remove()); const v = document.getElementById('viewer'); v && v.classList.remove('on'); }"""
PRIMARY = """() => [...document.querySelectorAll('.view.on .btn.primary')].filter(b => b.getClientRects().length && getComputedStyle(b).visibility !== 'hidden').length"""
SW = "() => document.documentElement.scrollWidth"
# an invented drawing, written to a temporary file outside the repo for the upload
SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"><rect width="400" height="300" fill="#fff"/>'
       '<rect x="20" y="20" width="360" height="200" fill="none" stroke="#000" stroke-width="3"/>'
       '<text x="200" y="130" text-anchor="middle" font-size="18">GARDEN KITCHEN - ISLAND RESTORED</text>'
       '<text x="300" y="270" font-size="20">A-201 REV C</text></svg>')


async def click(pg, sel, wait=300):
    await pg.evaluate("s => { const e = document.querySelector(s); if (!e) throw new Error('no ' + s); e.click(); }", sel)
    await pg.wait_for_timeout(wait)


async def register(c, pg, label):
    await sign_in(pg, 'u_sarah')
    await pg.evaluate("() => { setCurrent('p121'); plStatusF = 'current'; plSetF = ''; view = 'plans'; render(); }")
    await pg.wait_for_timeout(300)
    r = await pg.evaluate("""() => { const v = document.querySelector('.view.on');
      const cur = plSheets('p121', { current: true }), all = plSheets('p121');
      return { id: v.id, h2: (v.querySelector('h2') || {}).innerText || '', rows: v.querySelectorAll('[data-plrow]').length, cur: cur.length, all: all.length,
        sets: [...new Set(all.map(s => s.set))], sup: all.filter(s => s.status === 'superseded').length,
        kinds: [...new Set(all.map(plKind))], statuses: [...new Set(all.map(plStatus))],
        fields: cur.every(s => s.rev && s.issuedOn && s.issuer && plStatus(s) && s.set) }; }""")
    c.ok(r['id'] == 'v-plans' and r['h2'] == 'Plans — 121 State Street', f"{label}: the Plans page per job ({r['id']}, {r['h2']})")
    c.ok(r['rows'] == r['cur'] and r['cur'] < r['all'], f"{label}: the sheet index shows current sheets only by default ({r['rows']} of {r['all']})")
    c.ok(all(s in r['sets'] for s in ('deck', 'lpc', 'dob', 'cd', 'struct', 'shop')), f"{label}: the sets: presentation, LPC, DOB, construction documents, consultant, shop ({r['sets']})")
    c.ok(r['sup'] >= 3 and all(k in r['kinds'] for k in ('sheet', 'shop', 'rfi', 'spec', 'schedule')), f"{label}: superseded revisions and every kind ({r['sup']}, {r['kinds']})")
    c.ok(r['fields'], f"{label}: every current row has its revision, date, status, set and issuer")
    # filter by set and by status
    await pg.select_option('#pl-set', 'dob'); await pg.wait_for_timeout(200)
    f1 = await pg.evaluate("() => [...document.querySelectorAll('.view.on [data-plrow]')].map(e => plRow(e.dataset.plrow).set)")
    c.ok(f1 and all(x == 'dob' for x in f1), f"{label}: filter by set shows the DOB set only ({f1})")
    await pg.select_option('#pl-set', ''); await pg.select_option('#pl-status', 'superseded'); await pg.wait_for_timeout(200)
    f2 = await pg.evaluate("() => [...document.querySelectorAll('.view.on [data-plrow]')].map(e => plStatus(plRow(e.dataset.plrow)))")
    c.ok(f2 and all(x == 'superseded' for x in f2), f"{label}: filter by status shows superseded revisions ({len(f2)})")
    await pg.select_option('#pl-status', 'current'); await pg.wait_for_timeout(200)
    c.ok(await pg.evaluate(PRIMARY) == 1, f"{label}: one blue button on Plans")
    if label == 'phone':
        c.ok(await pg.evaluate(SW) <= 390, f"{label}: Plans does not scroll sideways ({await pg.evaluate(SW)})")


async def switch_job(c, pg, label):
    # the pilot (2026-10-18): Drawings' job switch said 121 State but kept 45 Cranberry's sheets
    await sign_in(pg, 'u_sarah')
    await pg.evaluate("() => { setCurrent('p45'); plStatusF = 'current'; plSetF = ''; view = 'sdraw'; render(); }"); await pg.wait_for_timeout(300)
    b0 = await pg.evaluate("() => ({ view, h2: (document.querySelector('.view.on h2') || {}).innerText || '', jobs: [...new Set([...document.querySelectorAll('.view.on [data-plrow]')].map(e => plRow(e.dataset.plrow).projectId))] })")
    c.ok(b0['view'] == 'plans' and b0['jobs'] == ['p45'], f"{label}: the Studio's Drawings opens the job's Plans page ({b0})")
    await pg.select_option('#pswitch', 'p121'); await pg.wait_for_timeout(500)
    b1 = await pg.evaluate("() => ({ view, cur: S.id, h2: (document.querySelector('.view.on h2') || {}).innerText || '', jobs: [...new Set([...document.querySelectorAll('.view.on [data-plrow]')].map(e => plRow(e.dataset.plrow).projectId))], s101: !!document.querySelector('.view.on [data-plopen=\"sh121s101\"]') })")
    c.ok(b1['cur'] == 'p121' and b1['h2'] == 'Plans — 121 State Street' and b1['jobs'] == ['p121'] and b1['s101'], f"{label}: switching job shows that job's sheets ({b1})")
    await click(pg, '.view.on [data-plopen="sh121s101"]', 500)
    v = await pg.evaluate("() => document.getElementById('v-name').textContent")
    c.ok('S-101' in v, f"{label}: the designer opens 121 State's S-101 ({v})")
    await pg.evaluate(CLOSE)


async def void_check(c, pg, label):
    await sign_in(pg, 'u_angel')
    await pg.evaluate("() => { setCurrent('p121'); }")
    v = await pg.evaluate("""async () => { await plOpen('sh121a201a'); await new Promise(r => setTimeout(r, 300));
      const V = document.getElementById('viewer');
      return { on: V.classList.contains('on'), stamp: !!V.querySelector('.pl-void-stamp'), bar: (V.querySelector('.pl-voidbar') || {}).innerText || '',
        name: document.getElementById('v-name').textContent, go: !!V.querySelector('.pl-voidbar [data-plopen="sh121a201b"]'),
        viewed: DB.studio.acks.some(a => a.kind === 'view' && a.sheetId === 'sh121a201a' && a.uid === 'u_angel') }; }""")
    c.ok(v['on'] and v['stamp'] and 'VOID' in v['bar'] and 'VOID' in v['name'], f"{label}: a superseded revision opens stamped VOID ({v['bar'][:60]})")
    c.ok(v['go'] and v['viewed'], f"{label}: with the way to the current revision, and the view is kept ({v})")
    await click(pg, '#viewer .pl-voidbar [data-plopen]', 500)
    v2 = await pg.evaluate("() => ({ stamp: !!document.querySelector('#viewer .pl-void-stamp'), name: document.getElementById('v-name').textContent })")
    c.ok(not v2['stamp'] and 'Rev B' in v2['name'], f"{label}: the link opens the current revision, not stamped ({v2['name']})")
    await pg.evaluate(CLOSE)
    # from Documents: the superseded file is marked VOID and opens stamped
    d = await pg.evaluate("""async () => { view = 'files'; render(); await new Promise(r => setTimeout(r, 200));
      const f = S.files.find(x => x.id === plRow('sh121a301a').fileId); openFile(f.id); await new Promise(r => setTimeout(r, 400));
      return { name: f.name, stamp: !!document.querySelector('#viewer .pl-void-stamp') }; }""")
    c.ok(d['name'].startswith('VOID') and d['stamp'], f"{label}: from Documents the old A-301 is named VOID and opens stamped ({d['name']})")
    await pg.evaluate(CLOSE)


async def designer_issue(c, pg, label, tmpfile):
    await sign_in(pg, 'u_sarah')
    await pg.evaluate("() => { setCurrent('p121'); plStatusF = 'current'; view = 'plans'; render(); }")
    await pg.wait_for_timeout(250)
    # In Revision: the garden kitchen is being redrawn
    await click(pg, '.view.on [data-plholdnew]')
    await pg.evaluate("() => { document.querySelector('#mbm [data-plrm=\"r121gk\"]').checked = true; }")
    await pg.fill('#mbm [data-f="why"]', 'The Kleins want the island back; layout being redrawn')
    await click(pg, '#mbm #mbm-ok', 400)
    h = await pg.evaluate("() => ({ holds: plHolds('p121').map(h => h.roomId), a201: plStatus(plCurrent('p121', 'A-201')), note: !!document.querySelector('.view.on .pl-hold'), t: (document.getElementById('toast') || {}).innerText || '' })")
    c.ok(h['holds'] == ['r121gk'] and h['a201'] == 'revision' and h['note'], f"{label}: the designer marks the garden kitchen In Revision ({h})")
    c.ok('Open' in h['t'], f"{label}: and the toast has Open ({h['t'][:80]})")
    # New Rev C from an uploaded file
    await click(pg, '.view.on [data-plnew="A-201"]')
    pre = await pg.evaluate("() => (document.getElementById('pl-preview') || {}).innerText || ''")
    c.ok('Rev B becomes VOID' in pre, f"{label}: the sheet says the old revision becomes VOID before issuing ({pre[:60]})")
    await pg.set_input_files('#pl-file', tmpfile); await pg.wait_for_timeout(300)
    await pg.fill('#mbm [data-f="changed"]', 'Island restored; base cabinet run back to 9 ft; sink stays centered on the window')
    await click(pg, '#mbm #mbm-ok', 600)
    r = await pg.evaluate("""() => { const s = plCurrent('p121', 'A-201'), old = plRow('sh121a201b'), p = plJob('p121');
      const el = document.querySelector(`[data-plrow="${s.id}"]`), r = el && el.getBoundingClientRect();
      const f = p.files.find(x => x.id === s.fileId);
      return { rev: s.rev, old: old.status, oldBy: old.supersededBy === s.id, flash: !!(el && el.classList.contains('tk-flash')), vis: !!(r && r.height && r.bottom > 0 && r.top < innerHeight),
        file: f ? [f.name, f.type, f.cat] : null, chat: (p.chat || []).some(m => m.plSheet === s.id && /VOID/.test(m.text)), need: s.ackNeed.map(n => n.name),
        toast: (document.getElementById('toast') || {}).innerText || '', origin: s.origin.kind, id: s.id }; }""")
    c.ok(r['rev'] == 'C' and r['old'] == 'superseded' and r['oldBy'], f"{label}: Rev C is current and Rev B is VOID ({r['rev']}, {r['old']})")
    c.ok(r['file'] and r['file'][1].startswith('image') and r['origin'] == 'upload', f"{label}: the uploaded file is stored with the revision ({r['file']})")
    c.ok(r['vis'] and r['flash'], f"{label}: the new revision is on the designer's screen right after saving, highlighted")
    c.ok(r['chat'] and 'Angel' in r['need'], f"{label}: the field is told in the job's thread and the foreman must acknowledge ({r['need']})")
    c.ok('VOID' in r['toast'], f"{label}: the toast says the old revision is VOID ({r['toast'][:90]})")
    await pg.evaluate("() => { view = 'sday'; render(); }")
    opened = await pg.evaluate(TOAST_OPEN); await pg.wait_for_timeout(400)
    o = await pg.evaluate("id => ({ view, el: !!document.querySelector(`.view.on [data-plrow=\"${id}\"]`) })", r['id'])
    c.ok(opened and o['view'] == 'plans' and o['el'], f"{label}: the toast's Open lands on the new revision ({o})")
    return r['id']


async def order_flag(c, pg, label):
    await sign_in(pg, 'u_chen')
    r = await pg.evaluate("""() => { setCurrent('p121');
      const po = { id: 'poPL' + Math.random().toString(36).slice(2, 6), number: 'PO-2026-PL1', vendor: 'Carlos Millwork', projectId: 'p121', status: 'draft', type: 'materials', date: today(), needBy: '2026-10-09',
        lines: [{ id: 'l1', item: 'Garden kitchen base cabinets, rift oak', qty: 1, unit: 'ls', price: 6400, line: '' }] };
      DB.pos.push(po); window.__plpo = po.id;
      const reasons = poValid(po); poAction(po, 'issue');
      return { reasons, status: po.status, toast: (document.getElementById('toast') || {}).innerText || '' }; }""")
    c.ok(any('Garden kitchen' in x and 'order anyway with a reason' in x for x in r['reasons']), f"{label}: procurement's PO for garden kitchen cabinets carries the hold as a reason ({r['reasons'][-1:]})")
    c.ok(r['status'] == 'draft' and 'Garden kitchen' in r['toast'], f"{label}: and is refused at Issue, with the reason ({r['toast'][:100]})")
    w = await pg.evaluate("""() => { poOpen = window.__plpo; view = 'po'; render();
      const w = document.querySelector('.view.on .pl-warn'); return w ? { t: w.innerText, ov: !!w.querySelector('[data-ploverride]') } : null; }""")
    c.ok(w and 'Garden kitchen' in w['t'] and w['ov'], f"{label}: the PO page says it, with Order Anyway for procurement ({(w or {}).get('t', '')[:80]})")
    q = await pg.evaluate("""() => { const r = { id: 'rqPL1', number: 'RFQ-2026-PL1', projectId: 'p121', status: 'purchasing', title: 'Garden kitchen base cabinets', lines: [{ id: 'q1', item: 'Garden kitchen base cabinets', qty: 1, unit: 'ls' }], quotes: [], history: [], sent: [] };
      (DB.rfqs = DB.rfqs || []).push(r); const ok = rfqSend(r, [], today()); return { ok, status: r.status, toast: (document.getElementById('toast') || {}).innerText || '' }; }""")
    c.ok(q['ok'] is False and q['status'] == 'purchasing' and 'Garden kitchen' in q['toast'], f"{label}: an RFQ for the area is not sent ({q['toast'][:90]})")
    # a field request for the area is flagged for procurement before anyone orders it
    await sign_in(pg, 'u_angel')
    rq = await pg.evaluate("""() => { setCurrent('p121'); const r = addRequest({ what: 'Garden kitchen cabinet pulls', qty: 12, unit: 'ea', neededBy: '2026-09-10' }, 'Angel'); return r && r.plFlag ? r.plFlag.rooms : null; }""")
    c.ok(rq == ['Garden kitchen'], f"{label}: a request for the area is flagged ({rq})")
    await sign_in(pg, 'u_chen')
    n = await pg.evaluate("() => nyhRows().filter(r => /^plreq:/.test(r.key)).map(r => r.title)")
    c.ok(any('cabinet pulls' in x for x in n), f"{label}: and is on procurement's Needs Your Hand before ordering ({n})")
    # only procurement or the owner override, with a reason recorded
    await sign_in(pg, 'u_alan')
    pm = await pg.evaluate("() => plOverride({ kind: 'po', id: window.__plpo, projectId: 'p121', roomId: 'r121gk', why: 'boxes do not change' })")
    c.ok(pm is None, f"{label}: the PM cannot override the order flag")
    await sign_in(pg, 'u_chen')
    await pg.evaluate("() => { poOpen = window.__plpo; view = 'po'; render(); }"); await pg.wait_for_timeout(200)
    await click(pg, '.view.on .pl-warn [data-ploverride]')
    await click(pg, '#mbm #mbm-ok', 250)
    still = await pg.evaluate("() => !!document.querySelector('#mbm')")
    c.ok(still, f"{label}: an override with no reason is refused")
    await pg.fill('#mbm [data-f="why"]', 'The cabinet boxes are the same in the redraw; only the island moves')
    await click(pg, '#mbm #mbm-ok', 400)
    ov = await pg.evaluate("""() => { const po = DB.pos.find(x => x.id === window.__plpo); const o = DB.studio.overrides.find(x => x.refId === po.id);
      return { o: o ? [o.by, o.role, o.why] : null, valid: poValid(po).filter(x => /revision/.test(x)), eq: erpQuery({ entity: 'planoverrides' }).rows.length }; }""")
    c.ok(ov['o'] and ov['o'][1] == 'coord' and 'island' in ov['o'][2] and not ov['valid'], f"{label}: Chen orders anyway with the reason recorded ({ov['o']})")
    c.ok(ov['eq'] >= 1, f"{label}: the override is queryable ({ov['eq']})")


async def field_ack(c, pg, label, rid):
    await sign_in(pg, 'u_angel')
    await pg.evaluate("() => { setCurrent('p121'); view = 'ftoday'; render(); }"); await pg.wait_for_timeout(300)
    t = await pg.evaluate("""id => { const card = document.querySelector('.view.on .pl-fyou'); const p = plJob('p121'), t = p.tasks.find(x => x.id === 'millgk');
      return { card: card ? card.innerText : '', wait: plTaskReasons(p, t).map(x => x.text), needs: fTaskNeeds(t).filter(n => n.k === 'plan').map(n => n.t) }; }""", rid)
    c.ok('A-201 Rev C' in t['card'] and 'Island restored' in t['card'], f"{label}: the foreman sees the new revision and what changed on Today ({t['card'][:80]})")
    c.ok(any('Waiting for acknowledgment' in x for x in t['wait']) and t['needs'], f"{label}: tasks in the area wait for his acknowledgment ({t['wait']})")
    if label == 'phone':
        c.ok(await pg.evaluate(SW) <= 390, f"{label}: Today does not scroll sideways at 390px")
    await click(pg, '.view.on .pl-fyou [data-plopen]', 600)
    v = await pg.evaluate("() => ({ on: document.getElementById('viewer').classList.contains('on'), stamp: !!document.querySelector('#viewer .pl-void-stamp'), ack: !!document.querySelector('#viewer [data-plack]') })")
    c.ok(v['on'] and not v['stamp'] and v['ack'], f"{label}: he opens it, current, with Acknowledge in the viewer ({v})")
    await click(pg, '#viewer [data-plack]', 500)
    a = await pg.evaluate("""id => { const s = plRow(id), p = plJob('p121'), t = p.tasks.find(x => x.id === 'millgk');
      const rec = DB.studio.acks.find(x => x.kind === 'ack' && x.sheetId === id && x.uid === 'u_angel');
      return { rec: rec ? [rec.name, rec.at] : null, pending: plAckState(s).pending.length, wait: plTaskReasons(p, t).map(x => x.text), holds: plHolds('p121').length,
        toast: (document.getElementById('toast') || {}).innerText || '', eq: erpQuery({ entity: 'sheetacks' }).rows.some(r => r.who === 'Angel' && r.rev === 'C' && r.action === 'acknowledged') }; }""", rid)
    c.ok(a['rec'] and a['rec'][1].startswith('2026-09-03'), f"{label}: Angel's acknowledgment is kept with its time on the app clock ({a['rec']})")
    c.ok(a['pending'] == 0 and not a['wait'] and a['holds'] == 0, f"{label}: the wait and the hold lift after the acknowledgment ({a})")
    c.ok('acknowledged' in a['toast'] and a['eq'], f"{label}: the toast says it and who viewed which revision is queryable ({a['toast'][:70]})")
    await pg.evaluate(CLOSE)


async def field_hold(c, pg, label):
    # design reworks the facade: the foreman's exterior task shows the hold and warns before Started
    await sign_in(pg, 'u_sarah')
    await pg.evaluate("() => { setCurrent('p121'); plMarkInRevision({ projectId: 'p121', roomIds: ['r121ext'], why: 'LPC asked for a new brick mold profile' }); save(); }")
    await sign_in(pg, 'u_angel')
    await pg.evaluate("() => { setCurrent('p121'); view = 'ftoday'; render(); }"); await pg.wait_for_timeout(300)
    h = await pg.evaluate("() => { const b = document.querySelector('.view.on [data-fstart=\"ext\"]'); const row = b && b.closest('.f-row'); return row ? (row.querySelector('.pl-hold') || {}).innerText || '' : null; }")
    c.ok(h and 'On hold' in h, f"{label}: the exterior task shows the hold on Today ({h})")
    await click(pg, '.view.on [data-fstart="ext"]', 400)
    m = await pg.evaluate("() => { const m = document.querySelector('#mbm'); return m ? m.innerText : ''; }")
    st = await pg.evaluate("() => plJob('p121').tasks.find(t => t.id === 'ext').status")
    c.ok('On Hold' in m and 'brick mold' in m and st != 'in-progress', f"{label}: Started warns before starting and does not start ({st})")
    await click(pg, '#mbm #mbm-alt', 500)
    st2 = await pg.evaluate("() => plJob('p121').tasks.find(t => t.id === 'ext').status")
    c.ok(st2 == 'in-progress', f"{label}: Start Anyway starts it, on the record ({st2})")
    await pg.evaluate("() => { const t = plJob('p121').tasks.find(t => t.id === 'ext'); t.status = 'planned'; delete t.actualStart; }")
    await sign_in(pg, 'u_alan')
    s = await pg.evaluate("() => { setCurrent('p121'); view = 'sched'; render(); return { note: (document.getElementById('pl-sched') || {}).innerText || '', bars: document.querySelectorAll('#v-sched .pl-held').length }; }")
    c.ok('Exterior' in s['note'] and (s['bars'] >= 1 or label == 'phone'), f"{label}: the schedule shows the hold ({s['note'][:60]}, {s['bars']} bars)")
    tk = await pg.evaluate("() => t2RowHtml({ kind: 'sched', id: 'ext', projectId: 'p121', title: 'Exterior', project: '121 State Street' }, {})")
    c.ok('On hold' in tk, f"{label}: the task list row shows the hold")
    await sign_in(pg, 'u_sarah')
    await pg.evaluate("() => { plHolds('p121').filter(h => h.roomId === 'r121ext').forEach(h => plLift(h.id, 'test done')); save(); }")


async def mail_meeting_message(c, pg, label):
    await sign_in(pg, 'u_alan')
    r = await pg.evaluate("""() => { cmImport([{ from: { name: 'Maya Natarajan', email: 'maya@natarajan-arch.example' }, to: ['alan@smartdesign.nyc'], subject: '121 State Street — updated A-301, rev 3',
        text: 'Hi Alan, attached is the updated A-301 rev 3. The landing moved 2 in north and the flitch header is now an LVL per the engineer.',
        attachments: [{ name: '121 State - A-301 Stair Section Rev 3.pdf', mimeType: 'application/pdf', text: 'A-301 STAIR SECTION REV 3 - landing moved 2 in north; LVL header' }] }]);
      const c = DB.comms[DB.comms.length - 1]; return { kinds: c.proposals.map(p => p.kind), row: (nyhRows().find(r => /^plrev:mail/.test(r.key)) || {}).verb || '' }; }""")
    c.ok('revision' in r['kinds'], f"{label}: the architect's mail with a PDF proposes a new revision ({r['kinds']})")
    c.ok(r['row'] == 'Confirm Rev 3', f"{label}: on the PM's Needs Your Hand with one verb ({r['row']})")
    await pg.evaluate("() => { setCurrent('p121'); view = 'plans'; render(); }"); await pg.wait_for_timeout(250)
    await click(pg, '.view.on .pl-prop [data-plrev]', 600)
    m = await pg.evaluate("""() => { const s = plCurrent('p121', 'A-301'), c = DB.comms[DB.comms.length - 1], f = plJob('p121').files.find(x => x.id === s.fileId);
      return { rev: s.rev, old: plRow('sh121a301b').status, origin: s.origin.kind, file: f ? f.type : '', applied: c.proposals.find(p => p.kind === 'revision').status, nyh: nyhRows().some(r => /^plrev:mail/.test(r.key)),
        toast: (document.getElementById('toast') || {}).innerText || '' }; }""")
    c.ok(m['rev'] == '3' and m['old'] == 'superseded' and m['origin'] == 'mail', f"{label}: one tap: A-301 Rev 3 is current, Rev 2 VOID ({m})")
    c.ok(m['file'] == 'application/pdf' and m['applied'] == 'applied' and not m['nyh'], f"{label}: the PDF is the stored file and the proposal leaves the queue")
    c.ok('Open' in m['toast'], f"{label}: toast with Open ({m['toast'][:80]})")
    # meeting notes and a job message propose the same way
    mt = await pg.evaluate("""() => { const c = { id: 'cmPLmt', msgId: 'cmPLmt', subject: 'Notes from “121 State coordination”', from: { name: 'Meeting notes', email: 'notes@example.com' },
        text: 'Notes from “121 State coordination”\\n\\nSummary\\nSarah sent the revised A-202 rev D: laundry counter raised back to 36 in.\\n\\nSuggested next steps\\n\\n[Angel] Check the laundry counter height against A-202 rev D', date: today() + 'T15:00:00', attachments: [], route: { projectId: 'p121' } };
      const m = mtIngest(c); if (m && !m.projectId) m.projectId = 'p121';
      const props = plProposals('p121').filter(x => x.src === 'meeting').map(x => x.pr.number + ' ' + x.pr.rev); return { m: !!m, props }; }""")
    c.ok(mt['props'] == ['A-202 D'], f"{label}: meeting notes naming A-202 rev D propose it ({mt})")
    ch = await pg.evaluate("""async () => { setCurrent('p121'); view = 'chat'; render(); document.getElementById('chat-text').value = 'Updated plans: A-401 rev B is up, the niche moved to the tub wall';
      await sendChat([]); await new Promise(r => setTimeout(r, 300)); render();
      const props = plProposals('p121').filter(x => x.src === 'message').map(x => x.pr.number + ' ' + x.pr.rev);
      return { props, chip: [...document.querySelectorAll('#chat-list .pl-chip [data-plrev]')].map(b => b.innerText) }; }""")
    c.ok(ch['props'] == ['A-401 B'] and 'Confirm Rev B' in ch['chip'], f"{label}: a job message saying updated plans proposes it, with Confirm on the message ({ch})")
    await pg.evaluate("() => plProposals('p121').filter(x => x.src !== 'mail').forEach(plDecline)")


async def filed(c, pg, label):
    await sign_in(pg, 'u_sarah')
    r = await pg.evaluate("""() => { setCurrent('p121'); const row = plIssue({ projectId: 'p121', number: 'A-100', changed: 'Garden bath wall moved 8 in east for the shower bench' }); save(); render();
      const p = plJob('p121'), t = p.tasks.find(x => x.id === 'tileg');
      return { amend: row.amend, wait: plTaskReasons(p, t).map(x => x.text), follow: row.impact.follow.map(f => f.kind), id: row.id }; }""")
    c.ok(r['amend'] and r['amend']['agency'] == 'DOB' and r['amend']['status'] == 'needed', f"{label}: a revision of a sheet filed with DOB is flagged ({r['amend']})")
    c.ok(any('amendment' in x for x in r['wait']), f"{label}: the garden bath tile work is held until the filing is approved ({r['wait']})")
    c.ok('amend' in r['follow'], f"{label}: the follow-ups say to file the amendment first ({r['follow']})")
    await sign_in(pg, 'u_chen')
    po = await pg.evaluate("""() => { const po = { id: 'poPL2', number: 'PO-2026-PL2', vendor: 'Nemo Tile', projectId: 'p121', status: 'draft', needBy: '2026-10-15', lines: [{ id: 'l1', item: 'Garden bath wall tile', qty: 80, unit: 'sf', price: 14 }] };
      DB.pos.push(po); return poValid(po).filter(x => /amendment/.test(x)); }""")
    c.ok(po, f"{label}: an order for the garden bath is flagged for the amendment ({po})")
    await sign_in(pg, 'u_owner')
    k = await pg.evaluate("() => CATCH.find(x => x.name === 'plansAmendment').rows().map(r => r.what)")
    c.ok(any('A-100 Rev C' in x for x in k), f"{label}: Caught for You names it for the owner ({k})")
    await sign_in(pg, 'u_alan')
    await pg.evaluate("() => { setCurrent('p121'); view = 'plans'; render(); }"); await pg.wait_for_timeout(250)
    note = await pg.evaluate("() => (document.querySelector('.view.on .pl-amend') || {}).innerText || ''")
    c.ok('DOB Amendment Needed' in note and 'held until the filing is approved' in note, f"{label}: the Plans page shows the amendment ({note[:70]})")
    await click(pg, '.view.on .pl-amend [data-plamendset$="|approved"]')
    await pg.fill('#mbm [data-f="ref"]', 'B00912345-I1 PAA 2')
    await click(pg, '#mbm #mbm-ok', 400)
    a = await pg.evaluate("id => { const p = plJob('p121'), t = p.tasks.find(x => x.id === 'tileg'); return { st: plRow(id).amend.status, by: plRow(id).amend.approvedBy, wait: plTaskReasons(p, t).filter(x => /amendment/.test(x.text)).length }; }", r['id'])
    c.ok(a['st'] == 'approved' and a['by'] == 'Alan' and a['wait'] == 0, f"{label}: the PM records the approval and the work is released ({a})")


async def impact(c, pg, label):
    r = await pg.evaluate("""() => { const s = plCurrent('p121', 'A-202'); const I = plImpact(Object.assign({}, s, { changed: 'Laundry counter moved 6 in left; pantry added' }), s);
      return { tasks: I.tasks.map(t => t.name), pos: I.pos.map(p => p.number), lines: I.lines.length, follow: I.follow.map(f => f.kind), mats: I.mats.length, dec: I.decisions.length }; }""")
    c.ok(r['tasks'] and r['pos'], f"{label}: what a change to A-202 touches: tasks {r['tasks'][:2]}, POs {r['pos']}")
    c.ok('po' in r['follow'] and 'seq' in r['follow'], f"{label}: and the follow-ups it proposes ({r['follow']})")


async def thread(c, pg, label):
    await sign_in(pg, 'u_alan')
    r = await pg.evaluate("""() => { setCurrent('p121'); view = 'chat'; render(); const pin = document.getElementById('pl-pinned');
      const btns = pin ? [...pin.querySelectorAll('[data-plopen]')].map(b => plRow(b.dataset.plopen)) : [];
      view = 'dash'; render(); const dash = document.querySelector('#v-dash #pl-pinned');
      return { n: btns.length, allCur: btns.every(s => plIsCurrent(s)), noOld: !btns.some(s => s.id === 'sh121a201a' || s.id === 'sh121a301b'), dash: !!dash }; }""")
    c.ok(r['n'] and r['allCur'] and r['noOld'], f"{label}: the job thread pins current sheets only ({r['n']})")
    c.ok(r['dash'], f"{label}: and so does the job's page")
    if label == 'phone':
        c.ok(await pg.evaluate(SW) <= 390, f"{label}: the job page does not scroll sideways")


async def question(c, pg, label):
    await sign_in(pg, 'u_sarah')
    await pg.evaluate("() => { setCurrent('p45'); view = 'sday'; render(); }"); await pg.wait_for_timeout(300)
    b = await pg.evaluate("() => { const b = document.querySelector('.view.on [data-plsheet=\"p121|A-301\"]'); return b ? b.innerText : ''; }")
    c.ok(b.startswith('Open A-301 Rev'), f"{label}: the field question on My Day links straight to the current A-301 ({b})")
    await click(pg, '.view.on [data-plsheet="p121|A-301"]', 600)
    v = await pg.evaluate("() => ({ on: document.getElementById('viewer').classList.contains('on'), name: document.getElementById('v-name').textContent, stamp: !!document.querySelector('#viewer .pl-void-stamp'), cur: S.id })")
    c.ok(v['on'] and 'A-301' in v['name'] and not v['stamp'] and v['cur'] == 'p121', f"{label}: one tap opens the current sheet in 121 State's register ({v['name']})")
    await pg.evaluate(CLOSE)
    if label == 'phone':
        c.ok(await pg.evaluate(SW) <= 390, f"{label}: My Day does not scroll sideways")
    else:
        j = await pg.evaluate("""() => DB.projects.map(p => { setCurrent(p.id); view = 'plans'; render(); return [p.id, ((document.querySelector('.view.on h2') || {}).innerText || '').includes(plJobName(p.id))]; })""")
        c.ok(all(x[1] for x in j), f"{label}: the designer reaches every job's Plans page ({j})")
        a = await pg.evaluate("() => paAsk('which revision of A-301 is current on 121 State?').headline")
        c.ok('A-301 Rev' in a and 'current' in a, f"{label}: her assistant answers which A-301 is current ({a[:80]})")


async def findable(c, pg, label, rid):
    await sign_in(pg, 'u_owner')
    r = await pg.evaluate("""id => { const q = erpQuery({ entity: 'sheets', q: 'A-201 121 State' }); const k = palIndex().filter(i => i.k === 'Plans');
      const keys = ['plansNotAcked', 'plansOrderedInRevision', 'plansAmendment'];
      return { q: q.rows.some(x => x._id === id), k: k.some(i => /A-201 Rev C/.test(i.t)), noVoidInK: !k.some(i => /A-201 Rev B/.test(i.t)),
        mapped: keys.filter(k0 => !(standardMapOf(k0).exact && /^Because: .+ \\(.+\\)$/.test(standardWhy(k0)))), inCatch: keys.every(k0 => CATCH.some(x => x.name === k0)),
        pred: ['plansToAck', 'plansOnHold', 'plansAmendments'].every(n => PRED[n] && PRED[n].count() === PRED[n].rows().length) }; }""", rid)
    c.ok(r['q'], f"{label}: the register is in erpQuery")
    c.ok(r['k'] and r['noVoidInK'], f"{label}: ⌘K finds current sheets, not void ones")
    c.ok(not r['mapped'] and r['inCatch'], f"{label}: every new CATCH id is mapped to a line of the Standard ({r['mapped']})")
    c.ok(r['pred'], f"{label}: each predicate's count is its rows")


async def after_reload(c, pg, label, rid):
    await pg.evaluate("async () => { await saveNow(); }")
    await pg.reload(); await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
    await sign_in(pg, 'u_sarah')
    await pg.evaluate("() => { setCurrent('p121'); plStatusF = 'current'; plSetF = ''; view = 'plans'; render(); }"); await pg.wait_for_timeout(300)
    r = await pg.evaluate("id => ({ el: !!document.querySelector(`.view.on [data-plrow=\"${id}\"]`), rev: (plRow(id) || {}).rev, acks: DB.studio.acks.filter(a => a.sheetId === id).length, seeded: DB.studio.sheets.filter(s => s.id === 'sh121a201b').length })", rid)
    c.ok(r['el'] and r['rev'] == 'C' and r['acks'] >= 1 and r['seeded'] == 1, f"{label}: after a reload the revision and its acknowledgment are in the register, the seed not repeated ({r})")


async def run(c, p, phone):
    label = 'phone' if phone else 'desktop'
    b, pg, errs = await open_app(p, phone=phone)
    fd, tmp = tempfile.mkstemp(suffix='-A-201 Rev C.svg'); os.write(fd, SVG.encode()); os.close(fd)
    try:
        await register(c, pg, label)
        await switch_job(c, pg, label)
        await void_check(c, pg, label)
        rid = await designer_issue(c, pg, label, tmp)
        await order_flag(c, pg, label)
        await field_ack(c, pg, label, rid)
        await field_hold(c, pg, label)
        await mail_meeting_message(c, pg, label)
        await filed(c, pg, label)
        await impact(c, pg, label)
        await thread(c, pg, label)
        await question(c, pg, label)
        await findable(c, pg, label, rid)
        await after_reload(c, pg, label, rid)
    finally:
        os.unlink(tmp)
    c.ok(not errs, f'{label}: no page errors {errs[:3]}')
    await b.close()


async def main():
    c = Checks()
    async with async_playwright() as p:
        for phone in (False, True):
            await run(c, p, phone)
    return c.done()


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
