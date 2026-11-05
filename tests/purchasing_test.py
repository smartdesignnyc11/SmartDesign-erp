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
  budget    S2  A vendor not on file stops New PO first; then the over-budget confirmation is awaited: "Yes, Continue" creates the PO and the message
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
# New PO refuses a name that is not a vendor on file (faabf8f: no vendor is created silently), so the priced-PO
# path buys from a vetted seeded vendor; the unknown-name stop itself is checked in s_budget.
VENDOR_ON_FILE = 'Carlos Millwork'
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
    await pg.evaluate("() => { setCurrent('p121'); procMode = 'lines'; bbTab = 'buy'; bbFilter = 'all'; bbProj = ''; view = 'proc'; render(); }"); await pg.wait_for_timeout(500)

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
            # Apply on a vendor invoice opens the bill, filled in; the person presses Enter the Bill (Pilot 2)
            if m and m['title'].startswith('Enter the Bill'): await modal_ok(pg, 600)
            elif m: await pg.keyboard.press('Escape')
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
                  cmApply(c, p2); const mm = document.getElementById('mbm'); mm && /^Enter the Bill/.test(mm.querySelector('h3').innerText) && mm.querySelector('#mbm-ok').click(); const b = DB.bills.find(x => x.number === 'CM-0199'); const it = mApprovals({ everyone: true }).find(it => it.kind === 'bill' && it.id === b.id) || {}; return b ? { poId: b.poId, flags: billFlags(b), sev: it.sev || '', detail: it.detail || '' } : null; }""")
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
        await picker_po(pg, 30000, VENDOR_ON_FILE)
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
        # Approvals is Today's Approvals chip (the Your Day lane, 11-03; the old page forwards there): the card, its
        # Approve, the side panel's Open the Record; Reject is on the PO's own record
        await sign_in(pg, 'u_owner'); await go(pg, 'mapprove'); await pg.wait_for_timeout(500)
        row = await pg.evaluate("""async n => { const vis = e => !!e && e.getClientRects().length > 0;
          const el = [...document.querySelectorAll('.view.on .td-do .td-card')].find(x => vis(x) && x.dataset.kind === 'po' && x.innerText.includes(n)); if (!el) return null;
          const own = [...el.querySelectorAll('button')].filter(vis).map(b => b.innerText.trim()); el.click(); await new Promise(r => setTimeout(r, 250));
          const side = [...document.querySelectorAll('.view.on .td2-aside button')].filter(vis).map(b => b.innerText.trim().replace(/,\\s*[\u2212-]?\\$[\\d,.]+$/, ''));
          return { btns: own.concat(side), text: el.innerText.slice(0, 200) }; }""", po['number'])
        c.ok(bool(row), f"approve: {po['number']} appears in the owner's Approvals")
        if row:
            for lbl in ('Approve', 'Open the Record'): c.ok(lbl in row['btns'], f"approve: the row offers {lbl} ({row['btns']})")
            await pg.evaluate("id => { poOpen = id; view = 'po'; render(); }", po['id']); await pg.wait_for_timeout(400)
            rj = await pg.evaluate("() => [...document.querySelectorAll('#v-po [data-poact=\"reject\"]')].filter(b => b.getClientRects().length).map(b => b.innerText.trim())")
            c.ok(bool(rj), f"approve: the PO's record offers its Reject (Send Back to Draft): {rj}")
        pred = await pg.evaluate("n => ({ q: PRED.waitingOnMe.rows().some(it => it.kind === 'po' && it.title.includes(n)), who: (mApprovals({ everyone: true }).find(it => it.kind === 'po' && it.title.includes(n)) || {}).who || '', deleg: (DELEGATION.po || {}).role || '' })", po['number'])
        c.ok(pred['q'] and pred['who'] == 'owner' and pred['deleg'] == 'owner', f'approve: DELEGATION hands a PO to the owner and Do Now counts it ({pred})')
        await go(pg, 'home'); await pg.wait_for_timeout(400)
        home = await pg.evaluate("n => [...document.querySelectorAll('.td-do .td-card')].some(x => x.innerText.includes(n))", po['number'])
        c.ok(home, "approve: the PO is on the owner's Do Now")
        if row:
            await go(pg, 'mapprove'); await pg.wait_for_timeout(400)
            # the card's Approve (on the desktop the selected card's verb is the side panel's button)
            await pg.evaluate("""async n => { const vis = e => !!e && e.getClientRects().length > 0;
              const el = [...document.querySelectorAll('.view.on .td-do .td-card')].find(x => vis(x) && x.dataset.kind === 'po' && x.innerText.includes(n));
              let b = el && el.querySelector('[data-tdverb]'); if (!vis(b)) { el.click(); await new Promise(r => setTimeout(r, 250)); b = document.querySelector('.view.on .td2-aside [data-td2lead]'); }
              b && /^Approve/.test(b.innerText.trim()) && b.click(); }""", po['number'])
            await pg.wait_for_timeout(900)
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
        # a name not on file stops first (no PO, no vendor made silently), and the over-budget guard still runs after it
        await picker_po(pg, 35000, 'Brooklyn Lumber')
        m = await modal(pg)
        c.ok(bool(m) and 'Brooklyn Lumber is not a vendor on file' in m['text'] and await pg.evaluate("() => DB.pos.length") == n0
             and not await pg.evaluate("() => (DB.vendors || []).some(v => v.name === 'Brooklyn Lumber')"), f'budget: an unknown vendor stops New PO first, nothing made ({m and m["text"][:120]!r})')
        v = pg.locator('#mbm table tr').filter(has_text='10. Trim, doors').first.locator('input[placeholder="vendor / sub"]').first
        await v.fill(VENDOR_ON_FILE); await v.press('Tab'); await pg.wait_for_timeout(300)
        await modal_ok(pg, 900)
        m = await modal(pg)
        c.ok(bool(m) and re.search(r'over', m['text'], re.I), f'budget: the over-budget confirmation shows ({m and m["text"][:160]!r})')
        if m:
            c.ok(re.search(r'\$2,500 over the \$32,500', m['text']), f'budget: the message states the amount over ({m["text"][:200]!r})')
            c.ok('Yes, Continue' in m['buttons'], f'budget: Yes, Continue is offered ({m["buttons"]})')
            await pg.locator('#mbm button').filter(has_text='Yes, Continue').first.click(); await pg.wait_for_timeout(1200)
        n1 = await pg.evaluate("() => DB.pos.length"); t = await toast(pg)
        c.ok(n1 == n0 + 1, f'budget: Yes, Continue creates the PO ({n0} -> {n1})')
        po = await pg.evaluate("() => { const o = DB.pos[DB.pos.length - 1]; return { vendor: o.vendor, total: poTotal(o).total, status: o.status }; }")
        c.ok(po['total'] == 35000 and po['vendor'] == VENDOR_ON_FILE and po['status'] == 'draft', f'budget: the PO is the one asked for ({po})')
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
            # an older mail's date never moves the PO back (the month: a 9/8 date undid the 9/15 slip on PO-2026-048)
            st = await pg.evaluate("""([cid, pid]) => { const c = DB.comms.find(x => x.id === cid), p = c.proposals.find(x => x.id === pid),
                old = Object.assign({}, c, { id: 'cm_old_eta', date: '2026-08-20T09:00:00', proposals: [] }),
                op = Object.assign({}, p, { id: 'cp_old_eta', date: '2026-10-09', applied: '', status: '' });
              old.proposals = [op]; DB.comms.push(old);
              const hidden = !nyhRowsAll().some(r => r.commId === 'cm_old_eta'), said = cmApplyEta(old, op, 'test'), po = DB.pos.find(x => x.id === 'po3');
              DB.comms = DB.comms.filter(x => x.id !== 'cm_old_eta'); save();
              return { hidden: hidden, said: said, expected: po.expected }; }""", [et['cid'], et['pid']])
            c.ok(st['hidden'] and st['expected'] == '2026-09-18' and 'older' in st['said'], f'reader: a vendor date from an older mail is not offered and does not move the PO back ({st})')
        # a quote from someone not on file: the Order sheet offers the sender, and Issue PO puts them on file only when
        # the sheet's checks pass (the month: the radiant mats waited a day for the vendor's own card and missed 9/18)
        qs = await pg.evaluate("""async () => {
          const R = buyList('p121').filter(r => r.m && !r.dec && !(r.po && !['draft', 'cancelled'].includes(r.po.status)));
          const out = {};
          const tryLine = async (r, nm) => {
            const m = r.m, keep = { vendor: m.vendor, q: m.quoteCommId, cost: m.cost };
            const c = { id: 'cm_qs_' + m.id, owner: 'u_chen', date: today() + 'T09:00:00', direction: 'in', subject: 'Quote QS-1 — ' + m.name,
              from: { name: nm, email: 'sales@' + m.id + '.example' }, to: [], text: 'Quote attached.', route: { projectId: 'p121' },
              proposals: [{ id: 'cp_qs_' + m.id, kind: 'unrouted', as: 'vendor', name: nm, email: 'sales@' + m.id + '.example', summary: 'not on file', on: true }] };
            DB.comms.push(c); m.vendor = 'TBD'; m.quoteCommId = c.id; m.cost = m.cost || '1000';
            buyOrderDialog({ pid: 'p121', mid: m.id }); await new Promise(res => setTimeout(res, 60));
            const box = document.getElementById('mbm'), sel = box && box.querySelector('[data-f="vendor"]');
            const res = { line: m.id, sel: sel ? sel.value : null };
            if (box) { const nb = box.querySelector('[data-f="needBy"]'); nb && !nb.value && (nb.value = iso(addDays(today(), 10)));
              const pr = box.querySelector('[data-f="price"]'); pr && !(+pr.value > 0) && (pr.value = '100');
              flSheetChecks(box); const ov = box.querySelector('.fl-over'); res.over = !!(ov && !ov.hidden);
              ov && !ov.hidden && (box.querySelector('[data-f="overWhy"]').value = 'over the line on purpose: a change order follows');
              const n0 = DB.pos.length; [...box.querySelectorAll('button')].find(b => /^Issue PO$/.test(b.innerText.trim())).click();
              await new Promise(res => setTimeout(res, 900));
              res.vendor = !!DB.vendors.find(v => v.name === nm); res.po = DB.pos.slice(n0).map(x => x.vendor + ':' + x.status);
              try { mbCloseModal(); } catch (e) {} }
            Object.assign(m, { vendor: keep.vendor, quoteCommId: keep.q, cost: keep.cost });
            return res; };
          const gated = R.find(r => r.m.id === 'm24'), open = R.find(r => r.m.id !== 'm24');
          if (gated) out.gated = await tryLine(gated, 'Held Test Supply');
          if (open) out.open = await tryLine(open, 'Quote Test Supply');
          return out; }""")
        op, gt = qs.get('open') or {}, qs.get('gated') or {}
        c.ok(op.get('sel') == '__quote__' and op.get('vendor') and 'Quote Test Supply:issued' in (op.get('po') or []), f"reader: the Order sheet offers a quote's sender not on file, and Issue PO puts them on file and issues ({op})")
        c.ok(not gt or (gt.get('sel') == '__quote__' and not gt.get('vendor') and not gt.get('po')), f"reader: a sheet stopped by its own checks puts nobody on file ({gt})")
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
        # Approvals is Today's Approvals chip (the Your Day lane, 11-03): the request's card there
        card = await pg.evaluate("() => { const el = [...document.querySelectorAll('.view.on .td-do .td-card, #v-mapprove .m-appr')].find(x => x.getClientRects().length && /Insulation for 3rd fl/.test(x.innerText)); return el ? el.innerText : ''; }")
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
        # The phone's Deliveries lists each order under Arriving with Receive, which opens the receive sheet (the Purchasing
        # pages, src/purchasing.js puDeliveries/puReceive: "the phone receives from the sheet"); the old line cards are behind
        # "Receive Line by Line". This check tapped a Received on those hidden cards and relied on the count pre-filled at the
        # full order (BACKLOG 1.36). The person taps Receive on the Carlos row, counts what came (the whole millwork order) and
        # taps Receive; an untouched sheet records nothing.
        card = pg.locator('.view.on .pu-row').filter(has_text='PO-2026-048').filter(has=pg.locator('[data-purecv]')).first
        c.ok(await card.count() > 0, 'polish: the Carlos PO is on Deliveries')
        if await card.count():
            await card.locator('[data-purecv]').first.click(); await pg.wait_for_timeout(500)
            q = pg.locator('#mbm input[data-purq]').first
            c.ok(await q.count() > 0 and await q.input_value() == '', f"polish: the received count starts empty on the phone ({await q.input_value() if await q.count() else 'no sheet'!r})")
            rec0 = await pg.evaluate("() => JSON.stringify(DB.pos.find(x => x.number === 'PO-2026-048').lines.map(l => +l.received || 0))")
            await modal_ok(pg, 400)
            rec1 = await pg.evaluate("() => JSON.stringify(DB.pos.find(x => x.number === 'PO-2026-048').lines.map(l => +l.received || 0))")
            c.ok(rec0 == rec1 and bool(await modal(pg)), f'polish: Receive with no count typed records nothing and keeps the sheet open ({rec0} -> {rec1})')
            if await q.count(): await q.fill('1')
            await modal_ok(pg, 900)
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
        # the FF&E buy run lives in the Buy Board's FF&E Buying Tools (procurement P1)
        await pg.evaluate("() => { setCurrent('p121'); view = 'proc'; procMode = 'finish'; render(); }"); await pg.wait_for_timeout(500)
        run = await pg.evaluate("() => { const b = document.getElementById('proc-run'); return b && { text: b.innerText.trim(), disabled: b.disabled, aria: b.getAttribute('aria-disabled') || '' }; }")
        c.ok(run and not run['disabled'] and run['aria'] != 'true', f'polish: New Buy Run is not disabled ({run})')
        # design phases are not things to buy
        rows = await pg.evaluate("() => buyList('p140').filter(r => r.kind === 'line' && r.d && r.d.template === 'design').map(r => r.name)")
        c.ok(not rows, f"polish: 140 Prospect's design phases are not on the buy list ({rows})")
        # an ordered line with no vendor or PO offers Expedite / Set Vendor
        await buy_board(pg)
        # the need's panel (procurement P1): a late promise with no order behind it offers Expedite (the sheet asks the vendor)
        ins = await pg.evaluate("() => { const r = buyList('').find(x => /Insulation/.test(x.name)); if (!r) return null; bbSel = r.id; render(); return [...document.querySelectorAll('#buy-board .bb-panel [data-bbstep]')].map(b => b.innerText.trim()); }")
        c.ok(ins is not None and any(x.startswith('Expedite') for x in ins) and 'Other Vendor' in ins, f'polish: the Insulation need (ordered, no vendor, no PO) offers Expedite and Other Vendor ({ins})')
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

async def s_selftest(p, c):
    """The agent-month harness's selftest findings (2026-10-11): our own sent mail never comes back as a proposal;
    the coordinator's Requests list open requests with Order and RFQ; a narrow inbox shows the message in place."""
    b, pg, errs = await fresh(p)
    try:
        await sign_in(pg, 'u_chen')
        own = await pg.evaluate("""() => { cmImport([{ msgId: 'own-po-1', from: { name: 'Chen Biron', email: 'chen@smartdesign.nyc' }, to: ['sales@nemotile.example'], subject: 'PO-2026-048 purchase order', text: 'Attached is PO-2026-048 for $4,250.00, due on delivery. Total $4,250.00.', date: today() + 'T10:00:00Z', labels: ['SENT'] }]);
            const x = DB.comms.find(y => y.msgId === 'own-po-1'); return [x.direction, x.proposals.length, cmListFor('decide').some(y => y.id === x.id)]; }""")
        c.ok(own == ['out', 0, False], f'selftest: our own sent PO email is filed, never proposed back to us ({own})')
        await go(pg, 'req'); await pg.wait_for_timeout(400)
        rq = await pg.evaluate("() => [...document.querySelectorAll('#req-co [data-reqco]')].map(r => [r.dataset.reqco, !!r.querySelector('[data-reqorder]'), !!r.querySelector('[data-reqrfq]')])")
        c.ok(len(rq) >= 2 and all(x[1] and x[2] for x in rq), f'selftest: the coordinator\'s Requests list open requests, each with Order and RFQ ({rq})')
        await pg.locator('#req-co [data-reqco="rq1"] [data-reqorder]').click(); await pg.wait_for_timeout(500)
        o = await pg.evaluate("() => { const r = DB.projects.find(p => p.id === 'p121').requests.find(x => x.id === 'rq1'), po = DB.pos.find(x => x.id === r.poId); return { view, po: !!po, linked: po ? po.lines.every(l => l.requestId === 'rq1') : false, item: po ? po.lines[0].item : '' }; }")
        c.ok(o['view'] == 'po' and o['po'] and o['linked'] and 'studs' in o['item'], f'selftest: Order drafts a PO from the request, linked ({o})')
        await go(pg, 'req'); await pg.wait_for_timeout(400)
        await pg.locator('#req-co [data-reqco="rq2"] [data-reqrfq]').click(); await pg.wait_for_timeout(500)
        q = await pg.evaluate("() => { const r = DB.projects.find(p => p.id === 'p121').requests.find(x => x.id === 'rq2'), x = r.rfqId && rfqById(r.rfqId); return { view, rfq: !!x, req: x && x.requestId, lines: x ? x.lines.length : 0 }; }")
        c.ok(q['view'] == 'rfq' and q['rfq'] and q['req'] == 'rq2' and q['lines'] >= 1, f'selftest: RFQ starts a request for quote from the request, linked ({q})')
        c.ok(not errs, f'selftest: page errors {errs[:2]}')
    finally:
        await b.close()
    for w in (390, 800):
        b = await p.chromium.launch(); ctx = await b.new_context(viewport={'width': w, 'height': 844}, is_mobile=w < 500, has_touch=w < 500); pg = await ctx.new_page()
        try:
            await pg.goto(URL); await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
            # the Inbox is Messages (the Your Day lane, 11-03): All, a message opened from its row
            await sign_in(pg, 'u_chen'); await go(pg, 'comms'); await pg.wait_for_timeout(400)
            await pg.locator('#yd-chat [data-ydchip="all"]').click(); await pg.wait_for_timeout(300)
            await pg.locator('#yd-chat [data-ydmrow]:not([data-ydmrow^="th:"]) [data-ydact]').first.click(); await pg.wait_for_timeout(400)
            r = await pg.evaluate("() => { const m = document.querySelector('.ib-msg'), l = document.querySelector('.ib-list'); return [!!m && m.getBoundingClientRect().top < innerHeight, !!(l && l.getClientRects().length), (document.querySelector('[data-ibback]') || {}).innerText] }")
            c.ok(r[0] and not r[1] and r[2] == 'Back', f'selftest: at {w}px an opened message replaces the list, with Back ({r})')
            await pg.locator('[data-ibback]').click(); await pg.wait_for_timeout(300)
            c.ok(await pg.evaluate("() => view === 'chat' && !!document.querySelector('#yd-chat [data-ydmrow]') && !document.querySelector('.view.on .ib-msg')"), f'selftest: at {w}px Back returns to the list (Messages)')
        finally:
            await b.close()

# ---------------------------------------------------------------- the 11-03 Purchasing pages (docs/mockups/purchasing/SPEC.md)
# Six pages, no tab rows; each opens on Needs You (the rows whose next tap is yours, its count equal to its rows), then
# Waiting on Someone Else (each row names who, no number). The figures are the demo company's on 9/3, as the spec read them.
from pd_pages import page as pd_page, kids as pd_kids, open_entry as pd_open, groups as pd_groups, press as pd_press
PU_FIVE = ['Buy Board', 'Orders', 'Quotes', 'Deliveries', 'Vendors']
# what waits on Chen on 9/3 (spec section 2): Buy Board 8, Orders 8, Quotes 0, Deliveries 3, Vendors 4, Stock 1
PU_CHEN = {'Buy Board': 8, 'Orders': 8, 'Quotes': 0, 'Deliveries': 3, 'Vendors': 4, 'Stock': 1}

async def s_pages(p, c):
    for phone in (False, True):
        dev = 'phone' if phone else 'desktop'
        b, pg, errs = await fresh(p, phone)
        try:
            await sign_in(pg, 'u_chen')
            K = await pd_kids(pg, phone, 'buy')
            c.ok([k[0] for k in K] == PU_FIVE + ['Stock'], f'pages {dev}: the coordinator\'s Purchasing lists Buy Board, Orders, Quotes, Deliveries, Vendors, Stock {[k[0] for k in K]}')
            G = await pd_groups(pg, phone)
            c.ok('Design' not in G, f'pages {dev}: no Design menu for the coordinator {G}')
            for label, want in PU_CHEN.items():
                if not await pd_open(pg, phone, 'buy', label):
                    c.ok(False, f'pages {dev}: {label} cannot be opened from the menu'); continue
                P = await pd_page(pg)
                c.ok(P and P['h2'] == label and P['page'], f'pages {dev}: {label} opens its page under its own heading ({P and P["h2"]}, {P and P["page"]})')
                if not P or not P['page']: continue
                c.ok(P['tabs'] == 0, f'pages {dev}: {label} has no tab row ({P["tabs"]})')
                c.ok(P['secs'][:1] == ['mine'], f'pages {dev}: {label} opens on Needs You {P["secs"]}')
                mine = P['mine'] or []
                c.ok((P['mineN'] or 0) == len(mine) == want and (want or P['mineN'] is None), f'pages {dev}: {label} Needs You {P["mineN"]} equals its {len(mine)} rows, {want} on 9/3')
                n = next((k[2] for k in await pd_kids(pg, phone, 'buy') if k[0] == label), None)
                c.ok((n or 0) == want, f'pages {dev}: the menu\'s {label} reads {n}, the page\'s Needs You {want}')
                oth = P['others'] or []
                c.ok(all(r['who'].startswith('Waiting on ') and r['nums'] == 0 for r in oth), f'pages {dev}: {label} rows waiting on others name who, with no number {[(r["t"][:40], r["who"]) for r in oth if not r["who"].startswith("Waiting on ")][:3]}')
                c.ok(P['othersN'] is None, f'pages {dev}: {label} Waiting on Someone Else carries no count ({P["othersN"]})')
                c.ok(len(P['blues']) <= 1, f'pages {dev}: {label} has one blue at most {P["blues"]}')
                c.ok(P['sw'] <= P['w'], f'pages {dev}: {label} never scrolls sideways ({P["sw"]} > {P["w"]})')
                if label == 'Buy Board':
                    t = ' '.join(r['t'] for r in mine)
                    c.ok(all(x in t for x in ('studs', 'Demolition', 'Exterior', 'Appliances', 'Insulation', 'Paint', 'countertop slab', 'Bath faucet')), f'pages {dev}: Buy Board Needs You holds the eight of the spec ({[r["t"][:30] for r in mine]})')
                    c.ok(not any('PO-2026-047' in r['t'] or 'PO-2026-048' in r['t'] or 'White oak' in r['t'] for r in mine + oth), f'pages {dev}: an ordered need with a late promise left the Buy Board for Deliveries')
                    c.ok(bool(P['route']) and any('Blue tape' in r['t'] for r in P['route']) and P['routeN'] is None, f'pages {dev}: the blue tape sits under On Today\'s Route with no count ({P["route"]}, {P["routeN"]})')
                    # every need names its estimate or change-order line, or says it has none
                    nol = [r['t'][:40] for r in mine + oth if not re.search(r'EST-\d|CO-\d|No estimate line|FF&E|[Rr]equest from', r['t'])]
                    c.ok(not nol, f'pages {dev}: every need names its line, or says it has none {nol}')
                    whos = {r['who'] for r in oth}
                    c.ok({'Waiting on Alberto M Plumbing', 'Waiting on the PM'} <= whos, f'pages {dev}: the submittal waits on Alberto, the material split on the PM {whos}')
                if label == 'Orders':
                    t = P['text']
                    c.ok('Owed Back' in t and '$2,419' in t and 'Over the Order' in t and '$3,800' in t, f'pages {dev}: Orders shows Owed Back $2,419 and Over the Order $3,800')
                if label == 'Deliveries':
                    t = ' '.join(r['t'] for r in mine)
                    c.ok('PO-2026-048' in t and 'PO-2026-047' in t and 'oute' in t, f'pages {dev}: Deliveries Needs You holds the two late promises and the route ({[r["t"][:40] for r in mine]})')
                    c.ok('Radiator valves' not in P['text'] and 'Appliances \u2013 parlor' not in P['text'], f'pages {dev}: needs marked ordered with no order are never arriving')
                if label == 'Vendors':
                    t = ' '.join(r['t'] for r in mine)
                    c.ok(all(x in t for x in ('Window Works', 'Alberto M Plumbing', 'Tino', 'Diamond')), f'pages {dev}: Vendors Needs You: Window Works, Alberto, Tino, Diamond ({[r["t"][:40] for r in mine]})')
                if label == 'Stock':
                    c.ok(any('PEX fittings' in r['t'] for r in mine), f'pages {dev}: Stock Needs You is PEX fittings at their reorder point')
                    c.ok('Blue tape' in P['text'] and 'Wanted by a Need' in P['text'], f'pages {dev}: Stock shows what a need could use, with no count')
            # the owner and the PM see Alan's five; the PM's Buy Board counts his material splits
            # the PM's: the line whose material portion is not set (Additional tile prep, CO-2026-001); the 11-03 review linked the
            # demo's materials to their lines, so the tile, trim and radiant lines are bought through their materials
            for uid, want_buy in (('u_owner', 0), ('u_alan', 1)):
                await sign_in(pg, uid)
                K = await pd_kids(pg, phone, 'buy')
                c.ok([k[0] for k in K] == PU_FIVE, f'pages {dev}: {uid} sees Alan\'s five in his order {[k[0] for k in K]}')
                await pd_open(pg, phone, 'buy', 'Buy Board')
                P = await pd_page(pg)
                c.ok(P and (P['mineN'] or 0) == len(P['mine'] or []) == want_buy, f'pages {dev}: {uid}\'s Buy Board Needs You is {want_buy} ({P and P["mineN"]}, {P and len(P["mine"] or [])})')
                G = await pd_groups(pg, phone)
                if uid == 'u_owner':
                    c.ok(not any(k[2] for k in K), f'pages {dev}: the owner\'s Purchasing carries no numbers {K}')
                    c.ok('Design' in G, f'pages {dev}: the owner keeps the Design menu {G}')
                else:
                    c.ok('Design' not in G, f'pages {dev}: no Design menu for the PM {G}')
            # an old page forwards to its new home
            await sign_in(pg, 'u_controller')
            await go(pg, 'ovbuy'); v = await pg.evaluate('view')
            c.ok(v == 'po', f'pages {dev}: the controller\'s Purchasing opens on Orders ({v})')
            c.ok(not errs, f'pages {dev}: page errors {errs[:2]}')
        finally:
            await b.close()

async def s_picks(p, c):
    """The Buy Board's picks: working check boxes, a bar with the count and the total, one blue by the Standard's rule."""
    for phone in (False, True):
        dev = 'phone' if phone else 'desktop'
        b, pg, errs = await fresh(p, phone)
        try:
            await sign_in(pg, 'u_chen')
            await pd_open(pg, phone, 'buy', 'Buy Board')
            # every Needs You row that can be bought has a check box (a need marked ordered with no order is found, not bought)
            n = await pg.evaluate("() => { const R = [...document.querySelectorAll('.view.on [data-pusec=\"mine\"] [data-purow]')]; return [R.filter(r => !/Find the Order/.test(r.innerText)).length, R.filter(r => r.querySelector('[data-bbpick]')).length]; }")
            c.ok(n[0] >= 6 and n[0] == n[1], f'picks {dev}: every Needs You row that can be bought has a check box ({n})')
            if n[0] < 2: continue
            # Paint has no price: a line with no price makes Ask for Quotes the blue
            pick = lambda nm: pg.locator('.view.on [data-pusec="mine"] [data-purow]').filter(has_text=nm).first.locator('[data-bbpick]')
            for nm in ('Paint', 'Bath faucet'):
                await pd_press(pick(nm))
            BAR = "() => { const b = [...document.querySelectorAll('.view.on .bb-bar')].find(x => x.getClientRects().length); if (!b) return null; return { t: b.innerText.replace(/\\s+/g, ' '), blue: [...b.querySelectorAll('.btn.primary')].map(x => x.innerText.trim()), other: [...b.querySelectorAll('.btn:not(.primary)')].map(x => x.innerText.trim()) }; }"
            bar = await pg.evaluate(BAR)
            c.ok(bar and '2 lines picked' in bar['t'] and 'no price' in bar['t'], f'picks {dev}: the bar says 2 lines picked and the lines with no price ({bar})')
            c.ok(bar and bar['blue'] == ['Ask for Quotes'] and 'order, with a reason' in [x.lower() for x in bar['other']], f'picks {dev}: a line with no price: Ask for Quotes is the blue, Order, With a Reason the other ({bar})')
            blues = await pg.evaluate("() => [...document.querySelectorAll('.view.on .btn.primary')].filter(x => x.getClientRects().length).length")
            c.ok(blues == 1, f'picks {dev}: one blue on the screen while the bar shows ({blues})')
            await pd_press(pg.locator('.view.on .bb-bar button').filter(has_text='Clear').first)
            c.ok(not await pg.evaluate(BAR), f'picks {dev}: Clear empties the picks')
            # a priced line under $2,500 makes Order the blue: price the slab need, then pick it alone
            await pg.evaluate("() => { const p = DB.projects.find(x => x.id === 'p121'); const m = p.materials.find(x => /countertop slab/i.test(x.name) && /parlor/i.test(x.name)); m.cost = 1200; save(); render(); }")
            await pg.wait_for_timeout(300)
            await pd_press(pick('countertop slab'))
            bar = await pg.evaluate(BAR)
            c.ok(bar and '1 line picked' in bar['t'] and '$1,200' in bar['t'] and bar['blue'][:1] and bar['blue'][0].startswith('Order'), f'picks {dev}: one priced line under $2,500: the total, and Order is the blue ({bar})')
            c.ok(not errs, f'picks {dev}: page errors {errs[:2]}')
        finally:
            await b.close()

async def s_receive(p, c):
    """Deliveries on the phone: the Receive sheet starts empty; Short or Damaged opens a claim on the order; a photo of the slip."""
    b, pg, errs = await fresh(p, True)
    try:
        await sign_in(pg, 'u_chen')
        await pd_open(pg, True, 'buy', 'Deliveries')
        btn = pg.locator('.view.on [data-purecv]').first
        c.ok(await btn.count() > 0, 'receive: Deliveries has Receive on an order on its way')
        if await btn.count():
            po = await btn.get_attribute('data-purecv')
            await btn.click(); await pg.wait_for_timeout(500)
            m = await modal(pg)
            c.ok(m and 'Receive' in m['title'], f'receive: Receive opens a sheet ({m and m["title"]})')
            qs = await pg.evaluate("() => [...document.querySelectorAll('#mbm input[data-purq]')].map(i => i.value)")
            c.ok(qs and all(q == '' for q in qs), f'receive: the count starts empty ({qs})')
            c.ok(await pg.locator('#mbm input[type=file][data-puslip]').count() == 1, 'receive: the sheet asks for a photo of the slip')
            conds = await pg.evaluate("() => [...document.querySelectorAll('#mbm [data-pucond]')].map(b => b.innerText.trim())")
            c.ok({'Good', 'Short', 'Damaged', 'Wrong'} <= set(conds), f'receive: Good, Short, Damaged, Wrong ({conds})')
            await pg.locator('#mbm input[data-purq]').first.fill('1')
            await pg.locator('#mbm [data-pucond="short"]').first.click(); await pg.wait_for_timeout(200)
            await modal_ok(pg, 900)
            r = await pg.evaluate("po => { const o = DB.pos.find(x => x.id === po); return { claims: (o.issues || []).filter(i => i.claim).length, rec: (o.lines || []).map(l => +l.received || 0) }; }", po)
            t = await toast(pg)
            c.ok(r['claims'] >= 1, f'receive: Short opens a claim on the order ({r})')
            c.ok(t['open'] and 'claim' in t['text'].lower(), f'receive: the toast says the claim opened, with Open ({t})')
        c.ok(not errs, f'receive: page errors {errs[:2]}')
    finally:
        await b.close()

async def s_leaks(p, c):
    """The money leaks the review found (BACKLOG section 9, items 4, 5 and 7), each caught where the person works."""
    b, pg, errs = await fresh(p)
    try:
        await sign_in(pg, 'u_chen')
        # 4. stock before buying: the route buys blue tape with 18 rolls at the warehouse; the GWB need has 12 sheets there
        await pd_open(pg, False, 'buy', 'Deliveries')
        P = await pd_page(pg)
        rt = next((r for r in (P['mine'] or []) if 'oute' in r['t']), None)
        c.ok(rt and '18' in rt['t'] and 'tape' in rt['t'].lower() and 'warehouse' in rt['t'].lower(), f'leaks: the route approval proposes the 18 rolls of tape at the warehouse ({rt and rt["t"][:160]})')
        await pd_open(pg, False, 'buy', 'Buy Board')
        await pg.evaluate("() => { const b = document.querySelector('.view.on [data-pulater]'); b && b.click(); }"); await pg.wait_for_timeout(300)
        P = await pd_page(pg)
        gwb = next((r for r in (P['later'] or []) if 'GWB' in r['t']), None)
        c.ok(gwb and '12' in gwb['t'] and 'warehouse' in gwb['t'].lower(), f'leaks: the GWB need says 12 sheets sit at the warehouse ({gwb and gwb["t"][:160]})')
        # 5. marked ordered with no order behind it: never counted as arriving; the need stays as Find the Order
        inv = await pg.evaluate("() => buyList('').filter(r => r.ordered && !r.po && !r.received).map(r => [r.name, r.tab])")
        c.ok(inv and all(t == 'buy' for _, t in inv), f'leaks: every need marked ordered with no order stays on the Buy Board ({inv})')
        t = ' '.join(r['t'] for r in (P['mine'] or []) + (P['later'] or []))
        c.ok(t.count('Find the Order') >= 3, f'leaks: Appliances, Insulation and Radiator valves read Find the Order ({t.count("Find the Order")})')
        # 7. paid with no W-9: the controller's Vendors
        await sign_in(pg, 'u_controller')
        await pd_open(pg, False, 'buy', 'Vendors')
        P = await pd_page(pg)
        w9 = next((r for r in (P['mine'] or []) if 'W-9' in r['t']), None)
        # the mock read $53,150 (Window Works, Tino, Nemo Tile, Satish); the bank also shows AMP-311's $9,800 left by
        # check 2205, so the figure is what the bank says left for every vendor with no W-9 (spec must-fix 4: re-read)
        paid = await pg.evaluate("() => Math.round(DB.vendors.filter(v => !v.w9).reduce((a, v) => a + vendorSpend(v), 0))")
        c.ok(paid >= 53150 and w9 and ('$' + format(paid, ',')) in w9['t'], f'leaks: the controller\'s Vendors holds the ${paid:,} the bank paid to vendors with no W-9 ({w9 and w9["t"][:200]})')
        c.ok(w9 and re.search(r'raises|bonuses|charity', w9['t']), f'leaks: the flag says why the money matters, in plain words ({w9 and w9["t"][:200]})')
        ww = await pg.evaluate("""() => { const v = document.querySelector('.view.on'); const m = v.innerText.match(/(\\d+) of (\\d+) have no W-9/);
          const cells = [...v.querySelectorAll('[data-puw9]')].filter(e => e.getClientRects().length).map(e => e.dataset.puw9);
          return { m: m ? [+m[1], +m[2]] : null, none: cells.filter(x => x === 'none').length, all: cells.length }; }""")
        c.ok(ww['m'] and ww['m'][0] == ww['none'] and ww['m'][1] == ww['all'], f'leaks: "N of M have no W-9" equals the W-9 column ({ww})')
        # 5b. Committed is one number (jobFin: open orders net of their bills and of payments with no bill), read the same on
        # Orders and on the job's Budget; the $8,000 paid to Tino before a bill is its own line under the figure on both
        # (review, 11-03: Orders read $46,721 against Budget's $38,721)
        await pd_open(pg, False, 'buy', 'Orders')
        cnb = await pg.evaluate("() => { const t = document.querySelector('.view.on [data-putile=\"cnb\"]'); return t ? t.innerText.replace(/\\s+/g, ' ') : ''; }")
        want = await pg.evaluate("() => Math.round(DB.projects.filter(p => DB.pos.some(po => po.projectId === p.id && ['issued', 'partial', 'pending'].includes(po.status))).reduce((a, p) => a + jobFin(p).committed, 0))")
        c.ok(cnb and ('$' + format(want, ',')) in cnb and 'Paid before a bill: $8,000' in cnb, f'leaks: Orders reads committed ${want:,} (jobFin) with the $8,000 paid before a bill on its own line ({cnb})')
        await sign_in(pg, 'u_alan')
        bud = await pg.evaluate("() => { jpOpenJob('p121', 'costs'); const e = document.querySelector('#jp-prepaid'); return e ? { c: Math.round(+e.dataset.committed), t: e.innerText, jf: Math.round(jobFin(S).committed) } : null; }")
        c.ok(bud and bud['c'] == bud['jf'] == want and 'Paid before a bill: $8,000' in bud['t'], f'leaks: 121 State Street\'s Budget committed ties to Orders ${want:,}, with the same $8,000 line ({bud})')
        c.ok(not errs, f'leaks: page errors {errs[:2]}')
    finally:
        await b.close()

async def s_lines(p, c):
    """Every need carries its estimate line (CLAUDE.md "How purchasing starts"; review 11-03): one picker for a material,
    a selection and a request; a blank need asks for its line; the demo's materials are linked to their real lines."""
    b, pg, errs = await fresh(p)
    try:
        await sign_in(pg, 'u_chen')
        await go(pg, 'proc')
        seed = await pg.evaluate("() => { const p = DB.projects.find(x => x.id === 'p121'); const m = id => (p.materials.find(x => x.id === id) || {}).line || ''; return { oak: m('m10'), tile: m('m9'), appl: m('m24') }; }")
        c.ok(seed['oak'] == 'estimate:es1:l8' and seed['tile'] == 'estimate:es1:l7' and seed['appl'] == '', f'lines: the demo materials name their lines; the appliances, on no line, say so ({seed})')
        for kind, rx in (('material', 'Appliances'), ('ffe', 'fireclay sink')):
            r = await pg.evaluate("""([kind, rx]) => { const r = buyList('').find(x => x.kind === kind && new RegExp(rx).test(x.name)); if (!r) return null;
              bbLinkLine(r); const m = document.querySelector('#mbm'); const o = m && m.querySelector('[data-bbl^="estimate:"]'); if (!o) return { picker: false, text: m ? m.innerText.slice(0, 120) : '' };
              o.checked = true; const key = o.dataset.bbl; m.querySelector('#mbm-ok').click();
              const back = buyList('').find(x => x.kind === kind && new RegExp(rx).test(x.name));
              return { picker: true, key, line: back && back.lineKey }; }""", [kind, rx])
            c.ok(r and r.get('picker') and r['line'] == r['key'], f'lines: one picker links a {kind} need to its estimate line ({r})')
        bn = await pg.evaluate("""() => { const n0 = DB.projects.find(x => x.id === 'p121').materials.length; puNewNeed(); const m = document.querySelector('#mbm');
          m.querySelector('#pu-nj').value = 'p121'; m.querySelector('#pu-nj').dispatchEvent(new Event('change')); m.querySelector('#pu-nw').value = 'Shims, 2 bundles';
          m.querySelector('#mbm-ok').click(); const refused = !!document.querySelector('#mbm') && DB.projects.find(x => x.id === 'p121').materials.length === n0;
          const sel = document.querySelector('#mbm #pu-nl'); sel.value = [...sel.options].find(o => o.value.startsWith('estimate:')).value;
          document.querySelector('#mbm #mbm-ok').click(); const m2 = DB.projects.find(x => x.id === 'p121').materials.slice(-1)[0];
          return { refused, name: m2.name, line: m2.line }; }""")
        c.ok(bn['refused'] and bn['name'] == 'Shims, 2 bundles' and bn['line'].startswith('estimate:'), f'lines: a blank need is refused until it names its line ({bn})')
        c.ok(not errs, f'lines: page errors {errs[:2]}')
    finally:
        await b.close()

async def s_rows(p, c):
    """A row tapped lands on the record it names, as the person taps it (the walk's J6 opened PO-2026-049 from Orders and
    stayed on the list: the page's unhide put back a display saved before the order opened, 11-04). A draft order opens
    with its lines' Buy From lists (the award's tile moves to the tile house from there)."""
    for phone in (False, True):
        dev = 'phone' if phone else 'desktop'
        b, pg, errs = await fresh(p, phone)
        try:
            await sign_in(pg, 'u_chen')
            # one draft with three lines, made through the app's own record (the demo's drafts were issued by 9/3)
            num = await pg.evaluate("() => { const po = DB.pos.find(x => x.number === 'PO-2026-047'); po.status = 'draft'; save(); return po.number; }")
            for st, n in (('draft', num), ('received', 'PO-2026-041')):
                await pd_open(pg, phone, 'buy', 'Orders')
                row = pg.locator('.view.on [data-pusec="orders"] [data-puopen]').filter(has_text=n).first
                if not await row.count():
                    c.ok(False, f'rows {dev}: {n} has a row under Orders'); continue
                await pd_press(row, 500)
                S = await pg.evaluate("""n => { const vis = el => !!el && el.getClientRects().length > 0, on = document.querySelector('.view.on');
                  return { open: typeof poOpen !== 'undefined' ? poOpen : null, doc: vis(document.getElementById('po-doc')), list: vis(document.getElementById('po-table')),
                    pu: vis(on && on.querySelector(':scope > .pu')), named: vis(document.getElementById('po-doc')) && document.getElementById('po-doc').innerText.includes(n),
                    moves: [...document.querySelectorAll('#po-doc [data-pomove]')].filter(vis).length,
                    lines: (DB.pos.find(x => x.number === n).lines || []).length }; }""", n)
                c.ok(S['doc'] and S['named'] and not S['list'] and not S['pu'], f'rows {dev}: tapping the {st} {n} row opens {n}, the list gone ({S})')
                if st == 'draft' and not phone:
                    c.ok(S['moves'] == S['lines'] > 0, f'rows {dev}: the draft {n} opens with a Buy From list on each of its lines ({S["moves"]} of {S["lines"]})')
                await pg.evaluate("() => { poOpen = null; render(); }")
            # a vendor's row opens the vendor
            await pd_open(pg, phone, 'buy', 'Vendors')
            row = pg.locator('.view.on [data-pusec] [data-puopen^="vend:"]').first
            if await row.count():
                nm = (await row.locator('b').first.inner_text()).strip()
                await pd_press(row, 500)
                V = await pg.evaluate("nm => { const on = document.querySelector('.view.on'), m = document.querySelector('.modal.on, .sheet.on, .m-sheet.on, dialog[open]');"
                                      " return { open: typeof vendOpen !== 'undefined' ? vendOpen : null, pu: !!on && !!on.querySelector(':scope > .pu') && on.querySelector(':scope > .pu').getClientRects().length > 0,"
                                      " text: ((m && m.innerText) || (on && on.innerText) || '').slice(0, 600) }; }", nm)
                c.ok(nm in V['text'] and (V['open'] or not V['pu']), f'rows {dev}: tapping {nm} on Vendors opens {nm} ({V["open"]}, {V["text"][:120]!r})')
            c.ok(not errs, f'rows {dev}: page errors {errs[:2]}')
        finally:
            await b.close()

async def s_clock(p, c):
    """One clock: nothing is stamped later than the app's day (BACKLOG section 9 item 1)."""
    b, pg, errs = await fresh(p)
    try:
        await sign_in(pg, 'u_chen')
        late = await pg.evaluate("""() => { const td = today(), out = [], seen = new Set();
          const KEY = /^(at|ts|raisedAt|createdAt|created|updatedAt|ackAt|sentAt|stampedAt|checkedAt|receivedAt|loggedAt|doneAt|approvedAt|resolvedAt)$/;
          const walk = (o, path, d) => { if (!o || typeof o !== 'object' || d > 7 || seen.has(o)) return; seen.add(o);
            for (const k of Object.keys(o)) { const v = o[k];
              if (typeof v === 'string' && KEY.test(k) && /^\\d{4}-\\d{2}-\\d{2}/.test(v) && v.slice(0, 10) > td) out.push(path + '.' + k + '=' + v.slice(0, 10));
              else if (v && typeof v === 'object') walk(v, path + '.' + k, d + 1); } };
          ['sel', 'pos', 'projects', 'claims', 'field', 'bills'].forEach(k => walk(DB[k], k, 0)); return out.slice(0, 12); }""")
        c.ok(not late, f'clock: no stamp on any record is later than today() ({late})')
        same = await pg.evaluate("() => DB.sel.items.filter(i => /lavatory faucet, cross|shower set/i.test(i.name) && i.projectId === 'p121').map(i => selLate(i))")
        c.ok(len(same) == 2 and same[0] == same[1], f'clock: two items with the same order-by are equally late ({same})')
        c.ok(not errs, f'clock: page errors {errs[:2]}')
    finally:
        await b.close()

SECTIONS = [('release', s_release), ('bill', s_bill), ('behalf', s_behalf), ('approve', s_approve), ('budget', s_budget),
            ('reader', s_reader), ('chase', s_chase), ('dates', s_dates), ('polish', s_polish), ('selftest', s_selftest),
            ('pages', s_pages), ('picks', s_picks), ('receive', s_receive), ('leaks', s_leaks), ('lines', s_lines), ('rows', s_rows), ('clock', s_clock)]

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
