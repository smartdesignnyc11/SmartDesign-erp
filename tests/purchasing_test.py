"""Purchasing: the coordinator's PO chain, from the round-5 coordinator review (review/r5_coord/report.md,
findings 1-9, 11-13, 15; BACKLOG §1.4 #1, §1.5 #4, §1.7 #4/#5). Each section runs in a fresh browser (fresh
seeded DB, app day 2026-09-03) and drives the real buttons; the phone sections lay out at 390px.

  release   S1  Release Order from a submittal makes a real PO: the supplier is asked for (never the sub who
                sent the cut sheets), the lines carry item, quantity, price, on-site date, task, spec and job,
                and one house validator (poValid) refuses Issue on every path with no vendor, no line, a $0
                line or no need-by; a refused issue never marks a material ordered; a boot migration un-marks
                materials ordered on a PO with no vendor or $0 and returns them to the board.
  bill      S1  A bill the reader makes from a vendor's mail carries the PO, job and line it names
                (CM-0102 -> PO-2026-048, 121 State, estimate:es1:l9) and the PO line's category, never
                "office"; Bill Remaining counts it; a bill that takes the PO over its amount is flagged.
  behalf    S1  A response recorded on a reviewer's behalf names who clicked ("recorded by Chen Biron on
                behalf of ..."); a client response needs the client's own portal approval or a stamped copy;
                the reviewer gets a Messages notice and a task to confirm; the register and the PO show it.
  approve   S1  A PO submitted for owner approval toasts with Open, lands in the owner's Approvals and Do Now
                with Approve / Reject / Open (DELEGATION po -> owner), and never on the foreman's Arriving Today.
  budget    S2  The over-budget confirmation is awaited: "Yes, Continue" creates the PO and the message
                states the amount over ("$2,500 over the $32,500 line").
  reader    S2  Apply finishes the job: a quote prices the Buy Board line and links the PDF; a receipt codes
                the card line to the job; a delivery date proposes the PO's ETA; "ready for pickup" proposes a
                driver stop; a vendor credit memo proposes the return and matches the statement credit.
  chase     S2  Chase COI asks for the vendor's email when missing, writes a draft into the connected mailbox
                (Demo Workspace Drafts), logs an expectation with a three-working-day follow-up, and says only
                what it does; Draft Email to Vendor is a template first, instantly, into the mailbox with the
                job's drawings named.
  dates     S2  COI expiry carries the year when not this year, on every surface; Vendor Promised is never
                prefilled; one need-by per request; follow-ups land on working days.
  polish    S2  The receiving toast shows the record's amount and names retainage; Acknowledge and Chase are
                buttons; Escape closes modals; New Buy Run is not disabled; design phases are not things to buy;
                an ordered line with no vendor offers Expedite / Set Vendor; Vendors "Blocked" equals Home's
                count through PRED.vendorsBlocked, and vendors with no certificate show as such.

    python3 purchasing_test.py [--section release,bill,...]
"""
import asyncio, re, sys, argparse, base64
from harness import *

MODAL = """() => { const m = document.querySelector('#mbm'); if (!m || !m.getClientRects().length) return null;
  return { title: (m.querySelector('.mbm-hd h3') || {}).innerText || '', text: m.innerText,
           buttons: [...m.querySelectorAll('button')].filter(b => b.getClientRects().length).map(b => b.innerText.trim()).filter(Boolean),
           fields: [...m.querySelectorAll('[data-f]')].map(i => ({ f: i.dataset.f, tag: i.tagName, type: i.type || '', val: String(i.value || '').slice(0, 80),
                     opts: i.tagName === 'SELECT' ? [...i.options].map(o => o.text) : undefined })) }; }"""
TOAST = """() => { const t = document.getElementById('toast'); if (!t) return { text: '', open: false, on: false };
  return { text: t.innerText.trim(), open: !!t.querySelector('.toast-open'), on: t.classList.contains('on'),
           links: [...t.querySelectorAll('.toast-open')].map(a => a.innerText.trim()) }; }"""
PDF = base64.b64decode(b'JVBERi0xLjQKMSAwIG9iajw8L1R5cGUvQ2F0YWxvZy9QYWdlcyAyIDAgUj4+ZW5kb2JqCjIgMCBvYmo8PC9UeXBlL1BhZ2VzL0tpZHNbXS9Db3VudCAwPj5lbmRvYmoKdHJhaWxlcjw8L1Jvb3QgMSAwIFI+Pg==')

async def modal(pg): return await pg.evaluate(MODAL)
async def refusal(pg):
    """What a refused submit said: the toast, or the inline field message the modal layer turned it into."""
    return await pg.evaluate("() => [((document.getElementById('toast') || {}).innerText || ''), ...[...document.querySelectorAll('#mbm .f-msg')].map(e => e.innerText)].join(' | ')")
async def toast(pg): return await pg.evaluate(TOAST)
async def click_rx(pg, rx, scope='body', timeout=5000, wait=600):
    loc = pg.locator(f'{scope} button:visible, {scope} a.btn:visible').filter(has_text=re.compile(rx)).first
    await loc.click(timeout=timeout); await pg.wait_for_timeout(wait)
async def modal_ok(pg, wait=700):
    await pg.locator('#mbm #mbm-ok').click(timeout=4000); await pg.wait_for_timeout(wait)
async def fresh(p, phone=False):
    b, pg, errs = await open_app(p, phone)
    return b, pg, errs
async def open_subm(pg, number):
    await go(pg, 'subm'); await pg.wait_for_timeout(200)
    await pg.locator('#v-subm table tbody tr').filter(has_text=number).first.click(timeout=6000); await pg.wait_for_timeout(500)
async def record_response(pg, stamp='approved', file=None, by=None):
    """Record Response through the real modal; returns the toast and whether the modal stayed open."""
    await click_rx(pg, r'^Record Response$', '#v-subm')
    m = await modal(pg)
    if not m: return None
    sel = pg.locator('#mbm select[data-f="stamp"]')
    if await sel.count(): await sel.select_option(stamp)
    if by is not None:
        inp = pg.locator('#mbm [data-f="by"]')
        if await inp.count(): await inp.fill(by)
    if file:
        await pg.locator('#mbm input[type=file]').first.set_input_files({'name': file, 'mimeType': 'application/pdf', 'buffer': PDF})
    await modal_ok(pg)
    return { 'toast': await toast(pg), 'stayed': bool(await modal(pg)) }
async def connect_demo(pg):
    d = await pg.evaluate("async () => { const d = await gcDemoConnect(); return d && { mail: d.mail.length, errors: d.errors }; }")
    await pg.wait_for_timeout(300); return d
async def proposal(pg, subject_part, kind):
    return await pg.evaluate("""([s, k]) => { const c = (DB.comms || []).find(c => (c.subject || '').includes(s) && c.owner === paMe().id) || (DB.comms || []).find(c => (c.subject || '').includes(s));
      if (!c) return null; const p = (c.proposals || []).find(p => p.kind === k); return { cid: c.id, pid: p ? p.id : '', kinds: (c.proposals || []).map(p => p.kind), p: p || null }; }""", [subject_part, kind])
async def apply_real(pg, cid, pid):
    """The Apply button's function, through its wrappers (no __cmBulk shortcut)."""
    return await pg.evaluate("([cid, pid]) => { const c = DB.comms.find(x => x.id === cid), p = c.proposals.find(x => x.id === pid); const did = cmApply(c, p); save(); return did; }", [cid, pid])
async def picker_po(pg, cost, vendor):
    """The reviewer's priced-PO path: Purchase Orders > Client Funds row 'Trim, doors, paint' > New PO > tick line 10 > cost > vendor > Create."""
    await pg.evaluate("() => { setCurrent('p121'); poOpen = null; view = 'po'; render(); }"); await pg.wait_for_timeout(400)
    row = pg.locator('#po-funds tr').filter(has_text='Trim, doors, paint').first
    await row.locator('button').filter(has_text=re.compile(r'^New PO$')).first.click(timeout=6000); await pg.wait_for_timeout(800)
    r = pg.locator('#mbm table tr').filter(has_text='10. Trim, doors').first
    cb = r.locator('input[type=checkbox]').first
    if not await cb.is_checked(): await cb.check()
    c = r.locator('input[placeholder=cost]').first; await c.fill(str(cost)); await c.press('Tab')
    v = r.locator('input[placeholder="vendor / sub"]').first; await v.fill(vendor); await v.press('Tab'); await pg.wait_for_timeout(300)
    await modal_ok(pg, 900)
async def buy_board(pg):
    """The Buy Board as the coordinator reaches it: Purchasing > Buy Board (the proc view, Contract Lines & Requests)."""
    await pg.evaluate("() => { setCurrent('p121'); procMode = 'lines'; buyScope = ''; buyOpen = true; view = 'proc'; render(); }"); await pg.wait_for_timeout(500)

# ------------------------------------------------------------------------------------------------ release (1)
async def s_release(p, c):
    b, pg, errs = await fresh(p)
    try:
        await sign_in(pg, 'u_chen')
        m17 = "() => { const p = DB.projects.find(x => x.id === 'p121'), m = p.materials.find(x => x.id === 'm17'); return { status: m.status, po: m.po || '', vendor: m.vendor || '', cost: m.cost || '' }; }"
        badge0 = await pg.evaluate("() => needs('buy')")
        await open_subm(pg, '26 51 00-001')
        for i in range(3):
            role_ = await pg.evaluate("() => { const s = smFind('sb121lite').s, st = smStepOf(s); return st ? st.role : ''; }")
            r = await record_response(pg, 'approved', file='Klein-approval-stamped.pdf' if role_ == 'client' else None)
            if not r: break
        st = await pg.evaluate("() => { const s = smFind('sb121lite'); return s ? s.s.status : ''; }")
        c.ok(st in ('approved', 'noted'), f'release: the submittal is {st!r} after three responses, want approved')
        # Release Order asks for the supplier and carries the submittal's facts.
        await click_rx(pg, r'^Release Order$', '#v-subm', wait=800)
        m = await modal(pg)
        c.ok(bool(m) and re.search(r'Release Order', m['title']), f'release: Release Order opens a picker, got {m and m["title"]!r}')
        if m:
            vend = next((f for f in m['fields'] if f['f'] == 'vendor'), None)
            c.ok(bool(vend) and vend['tag'] == 'SELECT', 'release: the picker asks for the supplier with a vendor select')
            if vend:
                c.ok(not any('Satish' in o for o in vend['opts']), f'release: the sub who sent the cut sheets is not offered as the supplier ({[o for o in vend["opts"] if "Satish" in o]})')
                c.ok(len([o for o in vend['opts'] if o and not o.startswith('—')]) >= 1, 'release: at least one real vendor is offered')
            need = await pg.evaluate("() => { const p = DB.projects.find(x => x.id === 'p121'); return withProject(p, () => matDates(p.materials.find(m => m.id === 'm17')).needBy); }")
            nb = next((f for f in m['fields'] if f['f'] == 'needBy'), None)
            c.ok(bool(nb) and nb['val'] == need, f"release: Needed on Site prefilled {nb and nb['val']!r}, the material needs it {need!r}")
            item = next((f for f in m['fields'] if f['f'] == 'item'), None)
            c.ok('26 51 00' in m['text'] and '121 State' in m['text'] and bool(item) and 'Light fixtures' in item['val'], f"release: the picker names the spec section, the job and the item ({item and item['val']!r})")
            qty = next((f for f in m['fields'] if f['f'] == 'qty'), None)
            c.ok(bool(qty) and float(qty['val'] or 0) >= 1, 'release: a quantity is carried')
            # no supplier: refused
            n0 = await pg.evaluate("() => DB.pos.length")
            await modal_ok(pg)
            m2 = await modal(pg); why = await refusal(pg)
            c.ok(bool(m2) and await pg.evaluate("() => DB.pos.length") == n0, f'release: Draft with no supplier is refused ({why!r})')
            c.ok(re.search(r'supplier|vendor', why, re.I), f'release: the refusal says why ({why!r})')
            if m2:
                opts = vend['opts'] if vend else []
                pick = next((o for o in opts if o and not o.startswith('—')), None)
                await pg.locator('#mbm select[data-f="vendor"]').select_option(label=pick)
                await modal_ok(pg, 900)
        po = await pg.evaluate("() => { const o = DB.pos.find(x => x.lines.some(l => l.materialId === 'm17')); return o && { id: o.id, number: o.number, vendor: o.vendor, status: o.status, projectId: o.projectId, needBy: o.needBy || '', needTask: o.needTask || '', spec: o.spec || '', submittalId: o.submittalId || '', price: o.lines[0].price, qty: o.lines[0].qty, item: o.lines[0].item }; }")
        c.ok(bool(po), 'release: a PO was drafted for the lighting')
        if po:
            c.ok(po['status'] == 'draft' and po['vendor'] and 'Satish' not in po['vendor'], f"release: drafted PO {po['number']} to {po['vendor']!r}, status {po['status']}")
            c.ok(po['projectId'] == 'p121' and po['needBy'] and po['needTask'] and po['spec'] == '26 51 00' and po['submittalId'] == 'sb121lite', f'release: the PO carries job, on-site date, task, spec and the submittal ({po})')
            c.ok(await pg.evaluate("() => view") == 'po' and await pg.evaluate("() => poOpen") == po['id'], 'release: the drafted PO opens')
            t = await toast(pg)
            c.ok(t['open'], f'release: the draft toast has an Open link ({t["text"]!r})')
            # Issue with a $0 line: refused, nothing marked ordered.
            await click_rx(pg, r'^Issue PO$', '#v-po', wait=800)
            m3 = await modal(pg)
            if m3 and 'Without an Approved Submittal' in m3['title']: c.ok(False, 'release: the approved submittal is read as holding the PO'); await pg.keyboard.press('Escape')
            t = await toast(pg); st2 = await pg.evaluate("id => DB.pos.find(x => x.id === id).status", po['id']); mm = await pg.evaluate(m17)
            c.ok(st2 == 'draft', f'release: Issue PO with a $0 line is refused (status {st2})')
            c.ok(re.search(r'\$0|price', t['text'], re.I), f'release: the refusal names the $0 line ({t["text"]!r})')
            c.ok(mm['status'] != 'ordered' and not mm['po'], f'release: the material is not marked ordered on a refused issue ({mm})')
            # price it, then issue: goes through, toasts with Open, marks the material ordered.
            ed = pg.locator('#v-po [data-rxedit]:visible')
            if await ed.count(): await ed.first.click(); await pg.wait_for_timeout(400)
            price = pg.locator('#v-po tr[data-line] [data-f="price"]').first
            await price.fill('4200'); await price.dispatch_event('change'); await pg.wait_for_timeout(500)
            await click_rx(pg, r'^Issue PO$', '#v-po', wait=900)
            m4 = await modal(pg)
            if m4 and re.search(r'Why It Is Safe', m4['text']): await pg.keyboard.press('Escape')
            st3 = await pg.evaluate("id => DB.pos.find(x => x.id === id).status", po['id']); mm = await pg.evaluate(m17); t = await toast(pg)
            c.ok(st3 == 'issued', f'release: a priced PO with a vendor issues (status {st3}, toast {t["text"]!r})')
            c.ok(mm['status'] == 'ordered' and mm['po'] == po['number'], f'release: the lighting is marked ordered on the issued PO ({mm})')
            c.ok(t['open'], f'release: the issue toast has an Open link ({t["text"]!r})')
        # The class: every creation path's draft meets the same validator before it issues.
        R = await pg.evaluate("""() => {
          const out = {}, mk = o => Object.assign({ id: uid('po'), number: nextPO(), projectId: 'p121', date: today(), status: 'draft', lines: [{ id: uid('pl'), item: 'Test item', qty: 1, unit: 'ea', price: 100, materialId: '', line: '', received: 0 }], tax: 0, shipping: 0, matchedTxns: [], needBy: '2026-09-20' }, o);
          const cases = { tbd: mk({ vendor: 'Vendor TBD' }), unassigned: mk({ vendor: 'Unassigned vendor' }), novendor: mk({ vendor: '' }), zero: mk({ vendor: 'Tino', lines: [{ id: uid('pl'), item: 'x', qty: 1, unit: 'ea', price: 0, received: 0 }] }), nolines: mk({ vendor: 'Tino', lines: [] }), noneed: mk({ vendor: 'Tino', needBy: '' }) };
          const valid = typeof poValid === 'function';
          for (const [k, po] of Object.entries(cases)) { DB.pos.push(po); const t = document.getElementById('toast'); t.textContent = ''; poAction(po, 'issue'); out[k] = { status: po.status, toast: (t.querySelector('.toast-msg') || t).textContent.trim(), reasons: valid ? poValid(po) : null }; }
          const sub = mk({ vendor: '' }); DB.pos.push(sub); poAction(sub, 'submit'); out.submit = { status: sub.status };
          DB.pos = DB.pos.filter(p => !Object.values(cases).includes(p) && p !== sub); save();
          return Object.assign(out, { valid }); }""")
        c.ok(R['valid'], 'release: one house validator poValid(po) exists')
        for k, why in (('tbd', 'vendor'), ('unassigned', 'vendor'), ('novendor', 'vendor'), ('zero', r'\$0|price'), ('nolines', 'line'), ('noneed', 'need')):
            r = R[k]
            c.ok(r['status'] == 'draft', f"release: a {k} PO is refused on issue (status {r['status']})")
            c.ok(re.search(why, r['toast'], re.I), f"release: the {k} refusal names the reason ({r['toast']!r})")
        c.ok(R['submit']['status'] == 'draft', f"release: Submit for approval with no vendor is refused ({R['submit']})")
        # Boot migration: a PO issued with no vendor at $0 that marked its material ordered is undone on boot.
        await pg.evaluate("""() => { const p = DB.projects.find(x => x.id === 'p121'), m = p.materials.find(x => x.id === 'm12');
          DB.pos.push({ id: 'po_bad049', number: 'PO-2026-949', projectId: 'p121', vendor: '', date: today(), status: 'issued', shipTo: 'site', notes: 'x', lines: [{ id: 'pl_bad', item: m.name, qty: 1, unit: 'lot', price: 0, materialId: 'm12', line: '', received: 0 }], tax: 0, shipping: 0, matchedTxns: [] });
          m.status = 'ordered'; m.po = 'PO-2026-949'; m.orderedOn = today(); saveNow ? saveNow() : save(); }""")
        await pg.wait_for_timeout(600)
        await pg.reload(); await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
        await sign_in(pg, 'u_chen')
        rep = await pg.evaluate("() => { const p = DB.projects.find(x => x.id === 'p121'), m = p.materials.find(x => x.id === 'm12'), po = DB.pos.find(x => x.id === 'po_bad049'); return { m: { status: m.status, po: m.po || '' }, po: po && { status: po.status, repaired: !!po.repaired }, onBoard: buyList('p121').some(r => r.m && r.m.id === 'm12' && !r.ordered) }; }")
        c.ok(rep['m']['status'] != 'ordered' and not rep['m']['po'], f"release: boot un-marks a material ordered on a PO with no vendor at $0 ({rep['m']})")
        c.ok(rep['po'] and rep['po']['status'] != 'issued' and rep['po']['repaired'], f"release: the invalid PO is taken back to draft and says so ({rep['po']})")
        c.ok(rep['onBoard'], 'release: the material is back on the Buy Board')
        c.ok(not errs, f'release: page errors {errs[:2]}')
    finally:
        await b.close()

# ------------------------------------------------------------------------------------------------ bill (2)
async def s_bill(p, c):
    b, pg, errs = await fresh(p)
    try:
        await sign_in(pg, 'u_chen')
        d = await connect_demo(pg)
        c.ok(d and not d['errors'], f'bill: the Demo Workspace connected ({d})')
        pr = await proposal(pg, 'CM-0102', 'bill')
        c.ok(pr and pr['pid'], f'bill: the reader proposed a bill for CM-0102 ({pr and pr["kinds"]})')
        if pr and pr['pid']:
            before = await pg.evaluate("() => ({ billed: poBilled(DB.pos.find(x => x.id === 'po4')), n: DB.bills.length })")
            did = await apply_real(pg, pr['cid'], pr['pid'])
            m = await modal(pg)
            if m: await pg.keyboard.press('Escape')
            bl = await pg.evaluate("""() => { const b = DB.bills.find(x => x.number === 'CM-0102'); if (!b) return null;
              const po = DB.pos.find(x => x.id === 'po4'); return { poId: b.poId || '', projectId: b.projectId || '', cat: b.cat, code: b.code || '', line: b.line || (b.lines[0] || {}).line || '', poLineId: (b.lines[0] || {}).poLineId || '', amount: billTotal(b), billed: poBilled(po), st: lkPOBillState(po), flags: billFlags(b) }; }""")
            c.ok(bool(bl), f'bill: CM-0102 was created ({did!r})')
            if bl:
                c.ok(bl['poId'] == 'po4', f"bill: the bill carries the PO the reader found (poId {bl['poId']!r}, want po4 = PO-2026-048)")
                c.ok(bl['projectId'] == 'p121', f"bill: the bill carries the job (projectId {bl['projectId']!r})")
                c.ok(bl['line'] == 'estimate:es1:l9' and bl['poLineId'] == 'pl4', f"bill: the bill line points at the PO line and its estimate line ({bl['line']!r}, {bl['poLineId']!r})")
                c.ok(bl['cat'] != 'office' and bl['cat'], f"bill: the category comes from the PO line, not office ({bl['cat']!r})")
                c.ok(abs(bl['billed'] - before['billed'] - 19000) < 0.01, f"bill: Bill Remaining counts it (PO billed {before['billed']} -> {bl['billed']})")
                c.ok(abs(bl['st']['remaining'] - (76000 - bl['billed'])) < 0.01, f"bill: remaining {bl['st']['remaining']} on a $76,000 order")
                # Over the PO: a second bill that takes the total past $76,000 is flagged at landing.
                ov = await pg.evaluate("""() => { const c = DB.comms.find(x => (x.subject || '').includes('CM-0102')), p = c.proposals.find(x => x.kind === 'bill');
                  const p2 = Object.assign({}, p, { id: uid('cp'), number: 'CM-0199', amount: 60000, applied: '', appliedAt: '' }); c.proposals.push(p2);
                  cmApply(c, p2); const b = DB.bills.find(x => x.number === 'CM-0199'); const it = mApprovals({ everyone: true }).find(it => it.kind === 'bill' && it.id === b.id) || {}; return b ? { poId: b.poId, flags: billFlags(b), sev: it.sev || '', detail: it.detail || '' } : null; }""")
                m = await modal(pg)
                if m: await pg.keyboard.press('Escape')
                c.ok(ov and any('vs PO' in f for f in ov['flags']), f'bill: a bill over the PO is flagged when it lands ({ov})')
                c.ok(ov and ov['sev'] in ('warn', 'bad') and 'vs PO' in ov['detail'], f"bill: the Approvals row carries the flag ({ov and (ov['sev'], ov['detail'][:120])})")
        c.ok(not errs, f'bill: page errors {errs[:2]}')
    finally:
        await b.close()

# ------------------------------------------------------------------------------------------------ behalf (3)
async def s_behalf(p, c):
    b, pg, errs = await fresh(p)
    try:
        await sign_in(pg, 'u_chen')
        await open_subm(pg, '26 51 00-001')
        step = await pg.evaluate("() => { const s = smFind('sb121lite').s, st = smStepOf(s); return { role: st.role, name: st.name }; }")
        c.ok(step['role'] == 'pm', f'behalf: the first step is the PM review ({step})')
        n_tasks = await pg.evaluate("() => DB.projects.find(x => x.id === 'p121').tasks.length")
        r = await record_response(pg, 'approved')
        st = await pg.evaluate("() => { const s = smFind('sb121lite').s, r = smRev(s), x = r.steps[0]; return { by: x.by, recordedBy: x.recordedBy || '', onBehalf: !!x.onBehalf, evidence: x.evidence || '' }; }")
        c.ok(st['recordedBy'] == 'Chen Biron', f"behalf: the PM's response records who clicked ({st})")
        c.ok(st['by'] == step['name'], f"behalf: the reviewer stays the reviewer ({st['by']!r} is {step['name']!r})")
        reg = await pg.evaluate("() => (document.querySelector('#sm-rec') || {}).innerText || ''")
        c.ok(re.search(r'recorded by Chen Biron on behalf of ' + re.escape(step['name']), reg), 'behalf: the register says "recorded by Chen Biron on behalf of <the PM>"')
        notice = await pg.evaluate("""n => { const p = DB.projects.find(x => x.id === 'p121'); const first = n.split(' ')[0];
          return { chat: (p.chat || []).some(ch => /26 51 00-001/.test(ch.text) && /on behalf|recorded/i.test(ch.text) && ch.text.includes(first)),
                   task: (p.tasks || []).concat(DB.tasks || []).some(t => /26 51 00-001/.test(t.name || t.title || '') && /confirm/i.test(t.name || t.title || '') && String(t.owner || t.assignee || '').includes(first)) }; }""", step['name'])
        c.ok(notice['chat'], 'behalf: the reviewer gets a Messages activity line')
        c.ok(notice['task'], 'behalf: the reviewer gets a task to confirm the response recorded for them')
        # the architect's step, then the client's: a client response needs the portal or a stamped copy
        await record_response(pg, 'approved')
        cs = await pg.evaluate("() => { const s = smFind('sb121lite').s, st = smStepOf(s); return st ? { role: st.role, name: st.name } : null; }")
        c.ok(cs and cs['role'] == 'client', f'behalf: the third step is the client ({cs})')
        if cs and cs['role'] == 'client':
            r = await record_response(pg, 'approved'); why = await refusal(pg)
            c.ok(r and r['stayed'] and re.search(r'portal|stamped', why, re.I), f"behalf: a client response with no stamped copy is refused ({why!r})")
            if r and r['stayed']: await pg.keyboard.press('Escape'); await pg.wait_for_timeout(200)
            r2 = await record_response(pg, 'approved', file='Klein-approval-stamped.pdf')
            st2 = await pg.evaluate("() => { const s = smFind('sb121lite').s, r = smRev(s), x = r.steps.find(z => z.role === 'client'); return { by: x.by, recordedBy: x.recordedBy || '', evidence: x.evidence || '', portal: !!x.portal, status: s.status }; }")
            c.ok(st2['status'] in ('approved', 'noted') and st2['recordedBy'] == 'Chen Biron' and st2['evidence'], f'behalf: with the stamped copy attached the client response records on behalf with evidence ({st2})')
            reg = await pg.evaluate("() => (document.querySelector('#sm-rec') || {}).innerText || ''")
            c.ok(re.search(r'on behalf of Sarah Klein \(Client\)', reg) and re.search(r'stamped copy', reg, re.I), 'behalf: the register shows the client response was recorded on their behalf with the stamped copy')
            # the PO gate shows the distinction
            await click_rx(pg, r'^Release Order$', '#v-subm', wait=800)
            m = await modal(pg)
            if m and m['fields']:
                sel = pg.locator('#mbm select[data-f="vendor"]')
                if await sel.count():
                    opts = await sel.evaluate("s => [...s.options].map(o => o.text)")
                    pick = next((o for o in opts if o and not o.startswith('—')), None)
                    if pick: await sel.select_option(label=pick)
                await modal_ok(pg, 900)
            txt = await pg.evaluate("() => (document.querySelector('#v-po') || {}).innerText || ''")
            c.ok(re.search(r'on behalf of Sarah Klein', txt), 'behalf: the PO record says the client approval was recorded on their behalf')
        c.ok(not errs, f'behalf: page errors {errs[:2]}')
    finally:
        await b.close()
    # the client's own portal approval reads as the client's, not on behalf
    b, pg, errs = await fresh(p)
    try:
        await sign_in(pg, 'u_chen')
        # the PM and the architect have answered; the set was sent to the client (Send to Client stamps sentOn)
        await pg.evaluate("() => { const { s, p } = smFind('sb121lite'); smRespond(s, p, { stamp: 'approved', comments: '' }, true); smRespond(s, p, { stamp: 'approved', comments: '' }, true); const st = smStepOf(s); st && (st.sentOn = today()); save(); }")
        await sign_in(pg, 'u_klein'); await go(pg, 'dec'); await pg.wait_for_timeout(300)
        btn = pg.locator('[data-smcl="ok|sb121lite"]:visible').first
        if not await btn.count():
            await go(pg, 'client'); await pg.wait_for_timeout(300)
            btn = pg.locator('[data-smcl="ok|sb121lite"]:visible').first
        c.ok(await btn.count() > 0, 'behalf: the client sees Approve on the lighting submittal')
        if await btn.count():
            await btn.click(); await pg.wait_for_timeout(500)
            if await modal(pg): await modal_ok(pg, 900)
            st = await pg.evaluate("() => { const s = smFind('sb121lite').s, x = smRev(s).steps.find(z => z.role === 'client'); return { by: x.by, portal: !!x.portal, recordedBy: x.recordedBy || '', status: s.status }; }")
            c.ok(st['portal'] and st['by'] == 'Sarah Klein' and not st['recordedBy'], f"behalf: the portal approval is the client's own ({st})")
            await sign_in(pg, 'u_chen'); await open_subm(pg, '26 51 00-001')
            reg = await pg.evaluate("() => (document.querySelector('#sm-rec') || {}).innerText || ''")
            c.ok(re.search(r'approved on the portal', reg, re.I) and not re.search(r'on behalf of Sarah', reg), 'behalf: the register says the client approved on the portal')
        c.ok(not errs, f'behalf (portal): page errors {errs[:2]}')
    finally:
        await b.close()

# ------------------------------------------------------------------------------------------------ approve (4)
async def s_approve(p, c):
    b, pg, errs = await fresh(p)
    try:
        await sign_in(pg, 'u_chen')
        n0 = await pg.evaluate("() => DB.pos.length")
        await picker_po(pg, 30000, 'Brooklyn Lumber')
        po = await pg.evaluate("() => { const o = DB.pos[DB.pos.length - 1]; return { id: o.id, number: o.number, status: o.status, vendor: o.vendor, expected: o.expected || '', needBy: o.needBy || '', total: poTotal(o).total }; }")
        c.ok(await pg.evaluate("() => DB.pos.length") == n0 + 1 and po['total'] == 30000, f'approve: the picker drafted {po}')
        if await pg.evaluate("() => view") != 'po' or await pg.evaluate("() => poOpen") != po['id']:
            await pg.evaluate("id => { poOpen = id; view = 'po'; render(); }", po['id']); await pg.wait_for_timeout(400)
        c.ok(po['expected'] == '', f"approve: Vendor Promised is not prefilled with a date no vendor gave (expected {po['expected']!r})")
        await click_rx(pg, r'^Submit for Approval', '#v-po', wait=900)
        m = await modal(pg)
        if m and re.search(r'Without an Approved Submittal', m['title']): await pg.keyboard.press('Escape')
        t = await toast(pg); st = await pg.evaluate("id => DB.pos.find(x => x.id === id).status", po['id'])
        c.ok(st == 'pending', f'approve: the PO is pending the owner ({st})')
        c.ok(re.search(r'approval', t['text'], re.I) and t['open'], f"approve: Submit toasts with an Open link ({t['text']!r}, open {t['open']})")
        # the foreman's Arriving Today never lists an unissued PO
        await sign_in(pg, 'u_angel'); await go(pg, 'field'); await pg.wait_for_timeout(400)
        arr = await pg.evaluate("() => (document.querySelector('.f3-arriving') || {}).innerText || ''")
        c.ok(po['number'] not in arr, f"approve: Arriving Today does not list the pending {po['number']}")
        # the owner's Approvals and Do Now
        await sign_in(pg, 'u_owner'); await go(pg, 'mapprove'); await pg.wait_for_timeout(500)
        row = await pg.evaluate("""n => { const el = [...document.querySelectorAll('#v-mapprove .m-appr[data-mk="po"]')].find(x => x.innerText.includes(n)); if (!el) return null;
          return { btns: [...el.querySelectorAll('button')].map(b => b.innerText.trim()), text: el.innerText.slice(0, 200) }; }""", po['number'])
        c.ok(bool(row), f"approve: {po['number']} appears in the owner's Approvals")
        if row:
            for lbl in ('Approve', 'Reject', 'Open'): c.ok(lbl in row['btns'], f"approve: the row offers {lbl} ({row['btns']})")
        pred = await pg.evaluate("n => ({ q: PRED.waitingOnMe.rows().some(it => it.kind === 'po' && it.title.includes(n)), who: (mApprovals({ everyone: true }).find(it => it.kind === 'po' && it.title.includes(n)) || {}).who || '', deleg: (DELEGATION.po || {}).role || '' })", po['number'])
        c.ok(pred['q'] and pred['who'] == 'owner' and pred['deleg'] == 'owner', f'approve: DELEGATION hands a PO to the owner and Do Now counts it ({pred})')
        await go(pg, 'home'); await pg.wait_for_timeout(400)
        home = await pg.evaluate("n => [...document.querySelectorAll('.td-do .td-card')].some(x => x.innerText.includes(n))", po['number'])
        c.ok(home, "approve: the PO is on the owner's Do Now")
        if row:
            await go(pg, 'mapprove'); await pg.wait_for_timeout(400)
            el = pg.locator('#v-mapprove .m-appr[data-mk="po"]').filter(has_text=po['number']).first
            await el.locator('button').filter(has_text=re.compile(r'^Approve$')).first.click(); await pg.wait_for_timeout(900)
            m = await modal(pg)
            if m and re.search(r'Without an Approved Submittal', m['title']): await pg.keyboard.press('Escape')
            st = await pg.evaluate("id => DB.pos.find(x => x.id === id).status", po['id']); t = await toast(pg)
            c.ok(st == 'issued', f'approve: Approve issues the PO ({st}; toast {t["text"]!r})')
            c.ok(t['open'], f'approve: the approval toasts with Open ({t["text"]!r})')
        c.ok(not errs, f'approve: page errors {errs[:2]}')
    finally:
        await b.close()

# ------------------------------------------------------------------------------------------------ budget (5)
async def s_budget(p, c):
    b, pg, errs = await fresh(p)
    try:
        await sign_in(pg, 'u_chen')
        n0 = await pg.evaluate("() => DB.pos.length")
        await picker_po(pg, 35000, 'Brooklyn Lumber')
        m = await modal(pg)
        c.ok(bool(m) and re.search(r'over', m['text'], re.I), f'budget: the over-budget confirmation shows ({m and m["text"][:160]!r})')
        if m:
            c.ok(re.search(r'\$2,500 over the \$32,500', m['text']), f'budget: the message states the amount over ({m["text"][:200]!r})')
            c.ok('Yes, Continue' in m['buttons'], f'budget: Yes, Continue is offered ({m["buttons"]})')
            await pg.locator('#mbm button').filter(has_text='Yes, Continue').first.click(); await pg.wait_for_timeout(1200)
        n1 = await pg.evaluate("() => DB.pos.length"); t = await toast(pg)
        c.ok(n1 == n0 + 1, f'budget: Yes, Continue creates the PO ({n0} -> {n1})')
        po = await pg.evaluate("() => { const o = DB.pos[DB.pos.length - 1]; return { vendor: o.vendor, total: poTotal(o).total, status: o.status }; }")
        c.ok(po['total'] == 35000 and po['vendor'] == 'Brooklyn Lumber' and po['status'] == 'draft', f'budget: the PO is the one asked for ({po})')
        c.ok(t['on'] and t['text'], f'budget: the result is toasted ({t["text"]!r})')
        c.ok(not errs, f'budget: page errors {errs[:2]}')
    finally:
        await b.close()

# ------------------------------------------------------------------------------------------------ reader (6)
async def s_reader(p, c):
    b, pg, errs = await fresh(p)
    try:
        await sign_in(pg, 'u_chen')
        d = await connect_demo(pg)
        c.ok(d and not d['errors'], f'reader: the Demo Workspace connected ({d})')
        # quote -> price on the line, PDF linked, no task dialog
        q = await proposal(pg, 'Q-2271', 'quote')
        c.ok(q and q['pid'], f'reader: Nemo quote proposal ({q and q["kinds"]})')
        if q and q['pid']:
            await apply_real(pg, q['cid'], q['pid']); await pg.wait_for_timeout(300)
            m = await modal(pg)
            # the order is the next step after a quote (flow lane): the Order sheet may follow, a task dialog never
            c.ok(not m or m['title'].startswith('Order'), f'reader: Apply on a quote does not open a task dialog ({m and m["title"]!r})')
            m and await pg.keyboard.press('Escape')
            if m: await pg.keyboard.press('Escape')
            r = await pg.evaluate("() => { const p = DB.projects.find(x => x.id === 'p121'), m = p.materials.find(x => x.id === 'm9'); return { cost: m.cost, status: m.status, vendor: m.vendor, lead: m.lead, file: !!(m.quoteFileId && (p.files || []).some(f => f.id === m.quoteFileId)) || (p.files || []).some(f => /Q2271|Quote/i.test(f.name) && f.materialId === 'm9') }; }")
            c.ok(r['cost'] == '2880' and r['status'] == 'quoted' and r['vendor'] == 'Nemo Tile' and r['lead'] == 10, f'reader: the quote put cost, vendor, lead and quoted on m9 ({r})')
            c.ok(r['file'], 'reader: the quote PDF is linked to the line')
        # receipt -> card line coded to the job and category, receipt attached
        rc = await proposal(pg, 'receipt — $286.70', 'receipt')
        c.ok(rc and rc['pid'] and rc['p'].get('txnId'), f"reader: the Home Depot receipt matched a card line ({rc and rc['p']})")
        if rc and rc['pid']:
            await apply_real(pg, rc['cid'], rc['pid']); await pg.wait_for_timeout(200)
            r = await pg.evaluate("id => { const t = DB.txns.find(x => x.id === id); return t && { projectId: t.projectId || '', cat: t.cat, status: t.status, receipt: !!t.receipt }; }", rc['p']['txnId'])
            c.ok(r and r['projectId'] == 'p121' and r['cat'] == 'materials' and r['receipt'], f'reader: the receipt codes the card line to 121 State / materials and attaches ({r})')
        # delivery date -> ETA proposal on the PO
        et = await proposal(pg, 'white oak delivery Friday Sept 18', 'eta')
        c.ok(et and et['pid'], f"reader: Tino's delivery date is proposed as an ETA update ({et and et['kinds']})")
        if et and et['pid']:
            c.ok(et['p'].get('poId') == 'po3' and et['p'].get('date') == '2026-09-18', f"reader: the ETA names PO-2026-047 and 2026-09-18 ({et['p']})")
            await apply_real(pg, et['cid'], et['pid'])
            r = await pg.evaluate("() => ({ expected: DB.pos.find(x => x.id === 'po3').expected, eta: DB.projects.find(x => x.id === 'p121').materials.find(m => m.id === 'm10').eta })")
            c.ok(r['expected'] == '2026-09-18' and r['eta'] == '2026-09-18', f'reader: applying sets the PO and the material ETA ({r})')
        # ready for pickup -> a stop on the driver's route
        pk = await proposal(pg, 'ready for pickup', 'pickup')
        c.ok(pk and pk['pid'], f"reader: Brooklyn Lumber's pickup is proposed as a driver stop ({pk and pk['kinds']})")
        if pk and pk['pid']:
            await apply_real(pg, pk['cid'], pk['pid'])
            await sign_in(pg, 'u_alex'); await go(pg, 'route'); await pg.wait_for_timeout(500)
            txt = await pg.evaluate("() => (document.querySelector('.view.on') || {}).innerText || ''")
            c.ok('Brooklyn Lumber' in txt, "reader: the driver's route lists the Brooklyn Lumber pickup")
            await sign_in(pg, 'u_chen')
        # credit memo -> a return matched to the statement credit
        cr = await proposal(pg, 'credit memo', 'credit')
        c.ok(cr and cr['pid'], f"reader: Bedrosians' credit memo is proposed as a return / credit match ({cr and cr['kinds']})")
        if cr and cr['pid']:
            c.ok(cr['p'].get('txnId') == 'tcr2', f"reader: the credit names the $214.50 statement credit ({cr['p'].get('txnId')!r})")
            await apply_real(pg, cr['cid'], cr['pid'])
            r = await pg.evaluate("() => { const t = DB.txns.find(x => x.id === 'tcr2'); const r = t && t.retId && retList().find(x => x.id === t.retId); return { retId: t.retId || '', cat: t.cat, ret: r && { vendor: r.vendor, name: r.name, status: r.status, recovered: r.recovered } }; }")
            c.ok(bool(r['retId'] and r['ret'] and r['ret']['vendor'] == 'Bedrosians' and 'Cloe' in (r['ret']['name'] or '')), f'reader: the credit is matched to a Bedrosians return for the Cloe tile ({r})')
        c.ok(not errs, f'reader: page errors {errs[:2]}')
    finally:
        await b.close()

# ------------------------------------------------------------------------------------------------ chase (7)
async def s_chase(p, c):
    b, pg, errs = await fresh(p)
    try:
        await sign_in(pg, 'u_chen')
        d = await connect_demo(pg)
        c.ok(d and not d['errors'], f'chase: the Demo Workspace connected ({d})')
        await go(pg, 'home'); await pg.wait_for_timeout(500)
        drafts0 = await pg.evaluate("() => ((DB.demoWs || {})[paMe().id] || { drafts: [] }).drafts.length")
        tino = await pg.evaluate("() => { const v = DB.vendors.find(x => /^tino/i.test(x.name)); return { email: v.email || '', ins: v.insuranceExp || '' }; }")
        c.ok(tino['email'] == '', f'chase: Tino has no email on file in the seed ({tino})')
        ch = pg.locator('#v-home button:visible').filter(has_text=re.compile(r'^Chase( COI)?$')).first
        c.ok(await ch.count() > 0, 'chase: Chase is a button on Home')
        if await ch.count():
            await ch.click(); await pg.wait_for_timeout(700)
            m = await modal(pg)
            c.ok(bool(m), 'chase: the chase modal opens')
            if m:
                c.ok(not re.search(r'project chat|client.s activity', m['text'], re.I), f'chase: the modal does not claim chat or client activity ({m["text"][:200]!r})')
                em = pg.locator('#mbm input[type=email], #mbm [data-f="email"], #mbm #ea-email')
                c.ok(await em.count() > 0, 'chase: the modal asks for the vendor email when it is missing')
                if await em.count(): await em.first.fill('tino@tinofloors.example')
                c.ok(re.search(r'draft', m['text'], re.I), 'chase: the modal says a draft goes to the mailbox for approval')
                await modal_ok(pg, 1200)
            t = await toast(pg)
            c.ok(t['open'], f'chase: the toast has an Open link ({t["text"]!r})')
            ws = await pg.evaluate("""() => { const W = (DB.demoWs || {})[paMe().id] || { drafts: [], messages: [] }; const last = W.messages.filter(m => (m.labelIds || []).includes('DRAFT')).slice(-1)[0];
              return { drafts: W.drafts.length, to: last ? last.headers.To : '', subject: last ? last.headers.Subject : '' }; }""")
            c.ok(ws['drafts'] == drafts0 + 1, f"chase: one draft landed in the mailbox's Drafts ({drafts0} -> {ws['drafts']})")
            c.ok('tino@tinofloors.example' in ws['to'] and re.search(r'insurance|certificate', ws['subject'], re.I), f'chase: the draft is addressed to the vendor about the certificate ({ws})')
            ex = await pg.evaluate("() => { const e = paExpectLedger().find(x => /tino/i.test(x.who)); return e && { who: e.who, by: e.by, email: e.email, closed: e.closed, about: e.about }; }")
            c.ok(ex and not ex['closed'], f'chase: an expectation is on the ledger ({ex})')
            if ex:
                want = await pg.evaluate("() => addWork(today(), 3, false)")
                c.ok(ex['by'] == want, f"chase: the follow-up is three working days out ({ex['by']} vs {want})")
                c.ok(ex['email'] == 'tino@tinofloors.example', 'chase: the address given is saved with the expectation')
            vend = await pg.evaluate("() => (DB.vendors.find(x => /^tino/i.test(x.name)) || {}).email || ''")
            c.ok(vend == 'tino@tinofloors.example', f'chase: the vendor record keeps the address ({vend!r})')
        # Draft Email to Vendor: template first, instantly; into the mailbox with the drawings named
        await pg.evaluate("() => { setCurrent('p121'); poOpen = 'po3'; view = 'po'; render(); }"); await pg.wait_for_timeout(400)
        drafts1 = await pg.evaluate("() => ((DB.demoWs || {})[paMe().id] || { drafts: [] }).drafts.length")
        t0 = await pg.evaluate("() => Date.now()")
        await click_rx(pg, r'^Draft Email to Vendor$', '#v-po', wait=300)
        try:
            await pg.wait_for_function("() => document.getElementById('drawer') && document.getElementById('drawer').classList.contains('on') && document.getElementById('em-body')", timeout=2500)
            ok = True
        except Exception: ok = False
        dt = await pg.evaluate("t => Date.now() - t", t0)
        c.ok(ok, f'chase: the vendor email drawer opens at once with a template ({dt} ms)')
        if ok:
            dr = await pg.evaluate("() => ({ subj: document.getElementById('em-subj').value, body: document.getElementById('em-body').value, save: (document.getElementById('d-save') || {}).textContent || '' })")
            c.ok('PO-2026-047' in dr['subj'] + dr['body'], 'chase: the template names the PO')
            c.ok(re.search(r'A-301|S-101|drawing', dr['body'], re.I), f"chase: the job's drawings are named in the draft ({dr['body'][-160:]!r})")
            c.ok(re.search(r'draft', dr['save'], re.I) and not re.search(r'mail app', dr['save'], re.I), f"chase: the primary writes to the connected mailbox ({dr['save']!r})")
            await pg.locator('#d-save').click(); await pg.wait_for_timeout(1000)
            drafts2 = await pg.evaluate("() => ((DB.demoWs || {})[paMe().id] || { drafts: [] }).drafts.length")
            c.ok(drafts2 == drafts1 + 1, f'chase: the vendor email is a draft in the mailbox ({drafts1} -> {drafts2})')
            t = await toast(pg)
            c.ok(t['open'], f'chase: the draft toast has Open ({t["text"]!r})')
        c.ok(not errs, f'chase: page errors {errs[:2]}')
    finally:
        await b.close()

# ------------------------------------------------------------------------------------------------ dates (8)
async def s_dates(p, c):
    b, pg, errs = await fresh(p)
    try:
        await sign_in(pg, 'u_chen')
        d = await connect_demo(pg)
        coi = await proposal(pg, 'Certificate of insurance — Window Works', 'coi')
        c.ok(coi and coi['pid'], f'dates: the Window Works COI proposal ({coi and coi["kinds"]})')
        if coi and coi['pid']:
            did = await apply_real(pg, coi['cid'], coi['pid'])
            c.ok(re.search(r'Aug 15, 2027', did or ''), f'dates: the COI result shows the year when it is not this year ({did!r})')
            vs = await pg.evaluate("() => ({ state: vendorState(DB.vendors.find(v => v.id === 'v2')).map(f => f.m), page: (() => { vendOpen = 'v2'; view = 'vendors'; render(); return (document.querySelector('#v-vendors') || {}).innerText || ''; })() })")
            c.ok(re.search(r'2027', vs['page']), 'dates: the vendor page shows the certificate year')
            await pg.evaluate("() => { vendOpen = null; view = 'vendors'; render(); }"); await pg.wait_for_timeout(300)
            tbl = await pg.evaluate("() => { const tr = [...document.querySelectorAll('#v-vendors table tbody tr')].find(r => /Window Works/.test(r.innerText)); return tr ? tr.innerText : ''; }")
            c.ok(re.search(r'2027', tbl), f'dates: the Vendors table shows the year ({tbl[:120]!r})')
        # one need-by per request: the insulation raise says 9/14 in its words
        await go(pg, 'mapprove'); await pg.wait_for_timeout(400)
        card = await pg.evaluate("() => { const el = [...document.querySelectorAll('#v-mapprove .m-appr')].find(x => /Insulation for 3rd fl/.test(x.innerText)); return el ? el.innerText : ''; }")
        c.ok(card and '9/14' in card and not re.search(r'needs it by\s*9/4\b|by 9/4\b', card), f'dates: the insulation request shows one need-by, 9/14 ({card[:200]!r})')
        fr = await pg.evaluate("() => { const r = DB.field.raises.find(x => x.id === 'fr3'); return { dueBy: r.dueBy, needBy: r.needBy || '' }; }")
        c.ok(fr['needBy'] == '2026-09-14', f'dates: the raise carries the date the site needs it ({fr})')
        # follow-ups land on working days: today is Thu 9/3; three days out is Sun 9/6, so the due date is Tue 9/8
        wd = await pg.evaluate("() => { const d = addWork(today(), 3, false); return { d, dow: new Date(d + 'T12:00:00').getDay() }; }")
        c.ok(wd['dow'] not in (0, 6), f'dates: addWork lands on a weekday ({wd})')
        due = await pg.evaluate("() => { eaAddNote('Follow up: test', iso(addDays(today(), 3)), 'Chen'); const n = eaNotes().slice(-1)[0]; const dow = new Date(n.due + 'T12:00:00').getDay(); return { due: n.due, dow }; }")
        c.ok(due['dow'] not in (0, 6), f'dates: a follow-up note due three days out lands on a working day ({due})')
        c.ok(not errs, f'dates: page errors {errs[:2]}')
    finally:
        await b.close()

# ------------------------------------------------------------------------------------------------ polish (9)
async def s_polish(p, c):
    # phone: receiving the Carlos millwork, then Bill It; the toast shows the record's amount
    b, pg, errs = await fresh(p, True)
    try:
        await sign_in(pg, 'u_chen')
        await pg.evaluate("() => { setCurrent('p121'); view = 'recv'; render(); }"); await pg.wait_for_timeout(500)
        card = pg.locator('.recv-po').filter(has_text='PO-2026-048').first
        c.ok(await card.count() > 0, 'polish: the Carlos PO is on Deliveries')
        if await card.count():
            await card.locator('button').filter(has_text=re.compile(r'^Received$')).first.click(); await pg.wait_for_timeout(900)
            t = await toast(pg)
            c.ok('Bill It' in t.get('links', []), f'polish: the receiving toast offers Bill It ({t})')
            if 'Bill It' in t.get('links', []):
                await pg.locator('#toast .toast-open').filter(has_text='Bill It').first.click(); await pg.wait_for_timeout(700)
                m = await modal(pg)
                c.ok(bool(m) and re.search(r'Bill', m['title']), f'polish: the bill dialog opens ({m and m["title"]!r})')
                if m:
                    c.ok('$38,000' in m['text'], f'polish: the dialog says $38,000 ({m["text"][:200]!r})')
                    await pg.locator('#mbm [data-f="number"]').fill('CM-0103')
                    await modal_ok(pg, 1000)
                    t2 = await toast(pg)
                    # the record's amount leads; a netted figure may follow only as what is payable after retainage
                    c.ok(re.search(r'submitted — \$38,000', t2['text']) and not re.search(r'\$34,200(?! payable)', t2['text']), f"polish: the toast shows the record's amount ({t2['text']!r})")
                    c.ok(re.search(r'retainage', t2['text'], re.I), f"polish: the toast names the retainage netted ({t2['text']!r})")
        c.ok(not errs, f'polish (phone): page errors {errs[:2]}')
    finally:
        await b.close()
    b, pg, errs = await fresh(p)
    try:
        await sign_in(pg, 'u_chen'); await go(pg, 'home'); await pg.wait_for_timeout(500)
        ems = await pg.evaluate("() => [...document.querySelectorAll('#v-home em')].map(e => e.innerText.trim()).filter(t => /^(Acknowledge|Chase( COI)?)$/.test(t))")
        c.ok(not ems, f'polish: Acknowledge and Chase are not <em> ({ems})')
        btns = await pg.evaluate("() => [...document.querySelectorAll('#v-home button')].map(b => b.innerText.trim()).filter(t => /^(Acknowledge|Chase( COI)?)$/.test(t))")
        c.ok(btns, f'polish: Acknowledge and Chase are buttons ({btns})')
        # Escape closes a modal that has no input
        await pg.evaluate("() => appConfirm('Escape test: close me')"); await pg.wait_for_timeout(200)
        await pg.keyboard.press('Escape'); await pg.wait_for_timeout(200)
        c.ok(not await modal(pg), 'polish: Escape closes a modal with no input')
        # New Buy Run does not look disabled
        await pg.evaluate("() => { setCurrent('p121'); view = 'proc'; render(); }"); await pg.wait_for_timeout(500)
        run = await pg.evaluate("() => { const b = document.getElementById('proc-run'); return b && { text: b.innerText.trim(), disabled: b.disabled, aria: b.getAttribute('aria-disabled') || '' }; }")
        c.ok(run and not run['disabled'] and run['aria'] != 'true', f'polish: New Buy Run is not disabled ({run})')
        # design phases are not things to buy
        rows = await pg.evaluate("() => buyList('p140').filter(r => r.kind === 'line' && r.d && r.d.template === 'design').map(r => r.name)")
        c.ok(not rows, f"polish: 140 Prospect's design phases are not on the buy list ({rows})")
        # an ordered line with no vendor or PO offers Expedite / Set Vendor
        await buy_board(pg)
        ins = await pg.evaluate("() => { const tr = [...document.querySelectorAll('#buy-board tr.buy-row')].find(r => /Insulation/.test(r.innerText)); return tr ? [...tr.querySelectorAll('button')].map(b => b.innerText.trim()) : null; }")
        c.ok(ins is not None and 'Expedite' in ins and 'Set Vendor' in ins, f'polish: the Insulation row (ordered, no vendor, no PO) offers Expedite / Set Vendor ({ins})')
        # Vendors "Blocked" equals Home's blocked count: one predicate
        nums = await pg.evaluate("""() => { const T = TL_SETS.vendors(); const bl = T.find(t => t.key === 'blocked'), nc = T.find(t => /no certificate/i.test(t.k));
          let home = null; try { home = tdChase().filter(x => x.kind === 'coi').length; } catch (e) {}
          return { tile: bl && bl.v, pred: PRED.vendorsBlocked ? PRED.vendorsBlocked.count() : null, home, noCert: nc ? nc.v : null, noCertReal: DB.vendors.filter(v => !v.insuranceExp).length, nVend: DB.vendors.length }; }""")
        c.ok(nums['pred'] is not None, 'polish: PRED.vendorsBlocked exists')
        c.ok(nums['tile'] == nums['pred'] and nums['home'] == nums['pred'], f"polish: Vendors Blocked {nums['tile']} = Home {nums['home']} = PRED.vendorsBlocked {nums['pred']}")
        c.ok(nums['noCert'] == nums['noCertReal'] and nums['noCertReal'] >= 1, f"polish: vendors with no certificate show as such ({nums['noCert']} of {nums['nVend']}; {nums['noCertReal']} have none)")
        c.ok(not errs, f'polish: page errors {errs[:2]}')
    finally:
        await b.close()

SECTIONS = [('release', s_release), ('bill', s_bill), ('behalf', s_behalf), ('approve', s_approve), ('budget', s_budget),
            ('reader', s_reader), ('chase', s_chase), ('dates', s_dates), ('polish', s_polish)]

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
