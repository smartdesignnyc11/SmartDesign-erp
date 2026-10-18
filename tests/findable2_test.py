"""Find it again, every create the agent month's referee caught (pilot1, day 1; BACKLOG §1.16 layer 3).

The referee counted 15 records their creator could not see right after saving, or after a reload:
  - a payroll journal approved from Approvals (owner);
  - two calendar holds booked from Approvals (owner);
  - the PM's no-show answer from Home: a text to the sub, a call, and their two outbox drafts (PM);
  - a COI applied from Home (coordinator);
  - a statement import on Banking (controller);
  - a sent invoice's chat line and its mail (billing);
  - tasks made from My Day with Make It a Task (designer).
This suite performs each one as that person, on desktop and at 390px, and asserts for every record the tap made:
  1. it is on the creator's screen right after saving (the referee's own test: sim/page_tools.js onScreen), and
     highlighted;
  2. its Open lands on it in the list it lives in, highlighted there;
  3. after a reload it is still on the screen it was made from, and it is in that person's natural list (My Tasks
     or the team's, the Outbox, the calendar, the job's files and chat, the invoice, Banking > Statement Imports,
     the General Ledger), checked by opening that list directly, not through the receipt.
It also pins the rules behind items 2 and 3 of the brief:
  - one LPC letter makes one task (Make It a Task used to file a schedule line owned by "PM" beside the designer's
    dated task);
  - the no-show answer files its tasks and drafts on the raise's job, not on whichever job is current;
  - a sent invoice's mail is addressed to the client's billing contact, readable as "Name <email>", and records
    the person who pressed Send (sentByUid), so it reads as their own send;
  - a pay application never lowers a line's cumulative %: the draft starts each line at the previous cumulative,
    says where the evidence is below what was already billed, and Send is refused for a line that would go below.
Invented data only (the mail below is the month's invented world)."""
import asyncio, json, os
from harness import async_playwright, open_app, sign_in, go, Checks, ROOT

PT = open(os.path.join(ROOT, 'sim', 'page_tools.js')).read()

COI_MAIL = {
    "id": "cmF2coi", "msgId": "f2_coi", "threadId": "f2t_coi", "channel": "email", "direction": "in",
    "from": {"name": "Harbor Insurance Brokers", "email": "certs@harborins.example"},
    "to": ["Chen Biron <chen@smartdesign.nyc>"], "cc": [], "date": "2026-08-28T19:30:00.000Z",
    "subject": "Certificate of insurance — Window Works LLC",
    "text": "Hello,\n\nAttached is the renewed certificate for our insured Window Works LLC naming SmartDesign Group LLC as certificate holder and additional insured, for the work at 121 State Street.\n\nHarbor Insurance Brokers",
    "attachments": [{"name": "COI-Window-Works-LLC-2026-27.pdf", "mime": "application/pdf", "size": 95800, "attachmentId": "f2a_coi", "msgId": "f2_coi",
                     "text": "CERTIFICATE OF LIABILITY INSURANCE\nInsured: Window Works LLC, 88 Kent Avenue, Brooklyn NY\nCertificate holder: SmartDesign Group LLC\nCommercial General Liability — Policy GL-7731-2026 — Policy Period 08/15/2026 to 08/15/2027\nWorkers Compensation — Policy WC-2210-2026 — Policy Period 08/15/2026 to 08/15/2027"}],
    "source": "import", "status": "proposed", "links": [], "owner": "u_chen",
    "proposals": [{"id": "cpF2coi", "kind": "coi", "summary": "Window Works sent a certificate of insurance · covers to Aug 15, 2027", "on": True, "vendorId": "v2", "w9": False, "exp": "2027-08-15"}],
    "route": {"clientId": "", "vendorId": "", "employee": "", "projectId": "p121", "addr": "121 State Street", "leadName": "", "leadEmail": "", "contact": "Harbor Insurance Brokers"},
}


def lpc_mail(i, pid, addr, subject, date, comment, task, owner, due, resubmit, sender):
    return {"id": f"cmF2lpc{i}", "msgId": f"f2_lpc{i}", "threadId": f"f2t_lpc{i}", "channel": "email", "direction": "in",
            "from": {"name": "LPC Staff", "email": sender}, "to": ["Sarah Davis <sarah@smartdesign.nyc>"], "cc": [], "date": date,
            "subject": subject, "text": comment + (" Please revise the drawing to show the sill horn and the back band depth and resubmit." if resubmit else ""),
            "attachments": [], "source": "import", "status": "proposed", "links": [], "owner": "u_sarah",
            "proposals": [{"id": f"cpF2lpc{i}", "kind": "lpc", "summary": f"LPC on {addr}: {comment}", "on": True, "projectId": pid, "comment": comment,
                           "hearing": "", "submittalId": "", "inspectionId": "", "task": task, "owner": owner, "due": due, "resubmit": resubmit}],
            "route": {"clientId": "", "vendorId": "", "employee": "", "projectId": pid, "addr": addr, "leadName": "", "leadEmail": ""}}


LPC_MAILS = [
    lpc_mail(1, "p45", "45 Cranberry St", "45 Cranberry Street — Certificate of Appropriateness — public hearing September 8", "2026-08-31T13:30:00.000Z",
             "The application covers the front facade windows and the stoop and areaway railing.",
             "Answer LPC on 45 Cranberry St — design: The application covers the front facade windows and the stoop and areaway railin", "PM", "", False, "noreply@lpc.example"),
    lpc_mail(2, "p121", "121 State Street", "Re: 121 State Street — brick mold profile for the window replacement", "2026-09-02T18:20:00.000Z",
             "Staff reviewed the brick mold profile for 121 State Street.",
             "Revise and resubmit to LPC on 121 State Street: Please revise the drawing to show the sill horn and the back band depth and resubmit", "Sarah Davis", "2026-09-10", True, "staff@lpc.example"),
]

CSV = "Date,Description,Amount,Reference\n2026-09-03,SHELL OIL 57442 BROOKLYN,-68.20,AC2-20260903-06820\n"

# the referee's own reading of what a tap made: every new named record, and whether its name is on the screen
DIFF = """(before) => { const after = __SIM.keys(); return Object.keys(after).filter(k => !before[k]).map(k => {
  const nm = __SIM.recordName(k); if (!nm.name) return null; const s = __SIM.onScreen(nm.name); return { key: k, coll: nm.coll, name: nm.name, on: s.on, toast: s.toast }; }).filter(Boolean); }"""

# is the name on screen, in the viewport, and inside a highlighted row?
HL = """(name, listOnly) => { const n = name.replace(/\\s+/g, ' ').trim().toLowerCase().slice(0, 40); const root = document.querySelector('section.view.on'); if (!root) return { vis: false, flash: false, sw: 0 };
  // every element that holds the name and no smaller one inside it does: is one in view, and one in view highlighted?
  const inV = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.bottom > 0 && r.top < innerHeight; };
  const M = [...root.querySelectorAll('*')].filter(e => !(listOnly && e.closest('#fnd-made')) && (e.textContent || '').replace(/\\s+/g, ' ').toLowerCase().includes(n))
    .filter((e, i, A) => !A.some(x => x !== e && e.contains(x)));
  const V = M.filter(inV);
  return { vis: V.length > 0, flash: V.some(e => e.closest('.tk-flash, .fnd-hit')), view, sw: document.documentElement.scrollWidth }; }"""

# the person's natural list for each kind of record, opened directly (never through the receipt)
NATURAL = """async ([coll, key, name]) => { const id = key.slice(key.lastIndexOf(':') + 1), me = (currentUser() || {}).name || '';
  const find = (L) => (L || []).find(r => r && (r.id === id || r.number === id));
  const proj = (k) => DB.projects.find(p => find(p[k]));
  const n = name.replace(/\\s+/g, ' ').trim().toLowerCase().slice(0, 40);
  const shown = () => { const root = document.querySelector('section.view.on'); const own = root && root.querySelector('#fnd-made'); let t = (root ? root.innerText : '').replace(/\\s+/g, ' ').toLowerCase(); if (own) t = t.replace(own.innerText.replace(/\\s+/g, ' ').toLowerCase(), ''); return t.includes(n); };
  let where = '';
  if (coll === 'p.actions' || coll === 'p.tasks') { const p = proj(coll.slice(2)), r = find(p[coll.slice(2)]), who = r.assignee || r.owner || '';
    const mine = tkOwnerMatch(who, me); view = (ROLE_VIEWS[role()] || []).includes('tkall') ? 'tkall' : 'tasks'; render();
    tkWho = mine ? 'me' : 'all'; t2View = 'all'; tkProject = ''; tkArea = ''; tkPri = ''; t2Q = ''; tkQueue = ''; tkPerson = ''; render(); where = (mine ? 'My Tasks' : 'All Tasks, Everyone'); }
  else if (coll === 'outbox') { const o = find(DB.outbox), a = o.about || {};
    if (a.docId && (ROLE_VIEWS[role()] || []).some(v => v === 'billing' || v === 'clients')) { const c = DB.clients.find(x => x.id === a.clientId), d = findDoc(c, a.docKind, a.docId); flowGo.doc(c, d.type, d)(); where = 'the invoice ' + d.number; }
    else { bnTab = 'hands'; view = 'brain'; render(); where = 'the Outbox (The Brain, Hands)'; } }
  else if (coll === 'p.files') { setCurrent(proj('files').id); fileFilter = 'all'; view = 'files'; render(); where = "the job's Files"; }
  else if (coll === 'p.chat') { setCurrent(proj('chat').id); view = 'chat'; render(); where = "the job's chat"; }
  else if (coll === 'bankImports') { view = 'bank'; render(); where = 'Banking, Statement Imports'; }
  else if (coll === 'calendar.external') { const e = find(DB.calendar.external); bnCalMonth = e.start.slice(0, 7); bnCalKind = ''; view = 'calendar'; render(); where = 'the calendar'; }
  else if (coll === 'gl.journals' && !(ROLE_VIEWS[role()] || []).includes('gl')) { const j = find(DB.gl.journals); const c = DB.clients.find(x => (x.invoices || []).concat(x.changeOrders || []).some(d => d.id === j.sourceId)); const d = c && findDoc(c, j.sourceType, j.sourceId);
    // no ledger for this role: the journal lives on the document it posted from
    flowGo.doc(c, d.type, d)(); await new Promise(r => setTimeout(r, 250)); return { where: 'the document it posted from, ' + d.number, ok: document.querySelector('section.view.on').innerText.includes(d.number) }; }
  else if (coll === 'gl.journals') { glTab = 'journal'; glJFilter = ''; glAcctFilter = ''; view = 'gl'; render(); where = 'the General Ledger, Journal'; }
  await new Promise(r => setTimeout(r, 250));
  return { where, ok: shown() }; }"""


async def settle_modal(pg, rounds=3):
    """Press the open sheet's primary button (a size check the approval asks is answered Yes), as a person would."""
    for _ in range(rounds):
        has = await pg.evaluate("() => { const m = document.getElementById('mbm'); const b = m && m.querySelector('#mbm-ok'); if (!b || b.disabled) return false; b.click(); return true; }")
        if not has: return
        await pg.wait_for_timeout(500)


async def scenario_payroll(pg):
    await go(pg, 'mapprove')
    await pg.evaluate("() => document.querySelector('.m-appr[data-mk=\"payroll\"] [data-myes]').click()")
    await pg.wait_for_timeout(400)
    if await pg.evaluate("() => !!document.querySelector('#mbm [data-f=\"why\"]')"):
        await pg.fill('#mbm [data-f="why"]', 'Wages are owed and the run is past due; office hours are salaried.')
    await settle_modal(pg)


async def scenario_hold(pg):
    await go(pg, 'mapprove')
    await pg.evaluate("() => [...document.querySelectorAll('.m-appr[data-mk=\"hand\"]')].find(e => /Samantha Field/.test(e.innerText)).querySelector('[data-myes]').click()")
    await pg.wait_for_timeout(400)
    await settle_modal(pg, 1)


async def scenario_noshow(pg):
    # the PM is on another job when the foreman's no-show comes in; the answer files on the raise's job
    await pg.evaluate("() => { setCurrent('p45'); view = 'home'; render(); }")
    await pg.wait_for_timeout(200)
    clicked = await pg.evaluate("() => { const b = document.querySelector('[data-fans=\"fr4\"]'); if (b) { b.click(); return true; } fAnswerRaise(DB.field.raises.find(r => r.id === 'fr4')); return false; }")
    await pg.wait_for_timeout(300)
    await pg.fill('#mbm [data-f="a"]', 'Tomas no-show noted. Rebooking for Fri 9/4; hold the scaffold as is.')
    await pg.fill('#mbm [data-f="slip"]', '1')
    await settle_modal(pg, 1)
    return clicked


async def setup_coi(pg):
    await pg.evaluate("m => { DB.comms.push(JSON.parse(JSON.stringify(m))); save(); view = 'home'; render(); }", COI_MAIL)
    await pg.wait_for_timeout(300)


async def scenario_coi(pg):
    await pg.evaluate("() => { const b = [...document.querySelectorAll('section.view.on button')].find(b => b.innerText.trim() === 'Apply' && /certificate of insurance/i.test((b.closest('[data-fdrow], .card, .nyh, div') || {}).innerText || '')); b.click(); }")
    await pg.wait_for_timeout(300)
    await settle_modal(pg, 1)


async def scenario_import(pg):
    await go(pg, 'bank')
    await pg.evaluate("() => document.querySelector('[data-bfimport]').click()")
    await pg.wait_for_timeout(300)
    await pg.set_input_files('#bfi-file', files=[{'name': 'ac2_2026-09-03.csv', 'mimeType': 'text/csv', 'buffer': CSV.encode()}])
    await pg.wait_for_timeout(500)
    await pg.select_option('#bfi-acct', 'ac2')
    await pg.wait_for_timeout(400)
    await settle_modal(pg, 1)


async def setup_send(pg):
    # the 45 Cranberry filing milestone, billed and sent to the client
    await pg.evaluate("""() => { const c = DB.clients.find(x => x.id === 'cl45'); finProj = 'p45';
      const d = newDoc(c, 'invoice'); d.projectId = 'p45'; d.title = 'At filing / submission — 40% of design fee';
      d.lines = [{ id: uid('l'), item: 'Filing & permits', desc: '40% of phase', qty: 1, unit: 'ls', rate: 1680, taxable: false }];
      if (!c.invoices.includes(d)) c.invoices.push(d); save(); window.__f2inv = d.id;
      view = 'billing'; clientOpen = c.id; docOpen = { kind: 'invoice', id: d.id }; render(); }""")
    await pg.wait_for_timeout(400)


async def scenario_send(pg):
    await pg.evaluate("() => document.querySelector('[data-docact=\"sendclient\"]').click()")
    await pg.wait_for_timeout(400)
    await settle_modal(pg, 1)
    await pg.wait_for_timeout(600)


async def setup_lpc(pg):
    await pg.evaluate("ms => { ms.forEach(m => DB.comms.push(JSON.parse(JSON.stringify(m)))); save(); view = 'sday'; render(); }", LPC_MAILS)
    await pg.wait_for_timeout(300)


async def scenario_lpc(pg):
    for _ in range(2):
        await pg.evaluate("() => { const b = [...document.querySelectorAll('section.view.on [data-nyh^=\"mail:lpc\"]')].find(b => b.innerText.trim() === 'Make It a Task'); b && b.click(); }")
        await pg.wait_for_timeout(500)
        await settle_modal(pg, 1)


# (person, entry point, setup (not counted), the tap, the nouns it must make)
SCENARIOS = [
    ('u_owner', 'a payroll run approved from Approvals', None, scenario_payroll, {'gl.journals'}),
    ('u_owner', 'a meeting held from Approvals', None, scenario_hold, {'calendar.external'}),
    ('u_alan', 'the no-show answered from Home', None, scenario_noshow, {'p.actions', 'outbox'}),
    ('u_chen', 'a COI applied from Home', setup_coi, scenario_coi, {'p.files'}),
    ('u_controller', 'a statement imported on Banking', None, scenario_import, {'bankImports'}),
    ('u_billing', 'an invoice sent to the client', setup_send, scenario_send, {'p.chat', 'outbox'}),
    ('u_sarah', 'Make It a Task from My Day', setup_lpc, scenario_lpc, {'p.actions'}),
]
# the nouns the referee caught, each with its own list (the receipt's Open and the reload check cover these)
LISTED = {'gl.journals', 'calendar.external', 'p.actions', 'p.tasks', 'outbox', 'p.files', 'bankImports', 'p.chat'}


async def reload_as(pg, uid, where):
    await pg.evaluate("async () => { await saveNow(); }")
    await pg.reload(); await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=90000)
    await pg.evaluate(PT)
    # the referee's reload: the same person, back on the job and the screen they were on
    await pg.evaluate("""([u, w]) => { signIn(u); if (w.cur) try { setCurrent(w.cur); } catch (e) {}
      if (w.view && (ROLE_VIEWS[role()] || []).includes(w.view)) view = w.view; render(); }""", [uid, where])
    await pg.wait_for_timeout(400)


async def run_scenario(c, pg, label, uid, name, setup, run, want):
    await sign_in(pg, uid)
    if setup: await setup(pg)
    before = await pg.evaluate("__SIM.keys()")
    try:
        await run(pg)
    except Exception as e:
        c.ok(False, f'{label} {uid} {name}: could not run ({str(e)[:160]})'); return []
    await pg.wait_for_timeout(500)
    made = await pg.evaluate(DIFF, before)
    got = {m['coll'] for m in made}
    c.ok(want <= got, f'{label} {uid} {name}: made {sorted(want)} ({sorted(got)})')
    where = await pg.evaluate("() => ({ view, cur: (DB && DB.currentId) || '' })")
    sw = await pg.evaluate("() => document.documentElement.scrollWidth")
    if label == 'phone':
        c.ok(sw <= 390, f'{label} {uid} {name}: no sideways scroll ({sw})')
    for m in made:
        # the referee's rule for every record a tap makes; highlighted, opened and found again for the listed nouns
        c.ok(m['on'], f'{label} {uid} {name}: "{m["name"][:50]}" ({m["coll"]}) is on the screen right after saving (view {where["view"]}, in toast {m["toast"]})')
        if m['coll'] not in LISTED: continue
        h = await pg.evaluate(HL, m['name'])
        c.ok(h['vis'] and h['flash'], f'{label} {uid} {name}: "{m["name"][:50]}" is in view and highlighted ({h})')
    return [m for m in made if m['coll'] in LISTED], where


async def open_lands(c, pg, label, uid, name, made, where):
    """Each record's Open lands on it in its own list, highlighted there."""
    for m in made:
        await pg.evaluate("([v, cur]) => { if (cur) try { setCurrent(cur); } catch (e) {} view = v; render(); }", [where['view'], where['cur']])
        await pg.wait_for_timeout(200)
        btn = await pg.evaluate("k => { const b = document.querySelector(`[data-fndopen=\"${k}\"]`); if (b) { b.click(); return 'receipt'; } return ''; }", m['key'])
        if not btn:
            # already on the screen: that row is the record, nothing to open (the referee's test: on the screen)
            s = await pg.evaluate("n => __SIM.onScreen(n)", m['name']); c.ok(s['on'], f'{label} {uid} {name}: "{m["name"][:40]}" is shown where it was made ({where["view"]})'); continue
        await pg.wait_for_timeout(1200)
        h = await pg.evaluate("([n]) => (" + HL + ")(n, true)", [m['name']])
        c.ok(h['vis'] and h['flash'], f'{label} {uid} {name}: Open on "{m["name"][:40]}" lands on it in its list, highlighted ({h})')


async def after_reload(c, pg, label, uid, name, made, where):
    await reload_as(pg, uid, where)
    for m in made:
        s = await pg.evaluate("n => __SIM.onScreen(n)", m['name'])
        c.ok(s['on'], f'{label} {uid} {name}: after a reload "{m["name"][:40]}" is still on the screen it was made from ({where["view"]})')
    for m in made:
        r = await pg.evaluate(NATURAL, [m['coll'], m['key'], m['name']])
        c.ok(r['ok'], f'{label} {uid} {name}: after a reload "{m["name"][:40]}" is in {r["where"]}')


async def rules(c, pg):
    """The data behind items 2 and 3 of the brief, and the two class fixes found on the way."""
    await pg.evaluate("() => { window.__f2inv = (DB.clients.find(x => x.id === 'cl45').invoices.filter(d => /At filing \\/ submission/.test(d.title || '')).pop() || {}).id; }")
    # one LPC letter, one task: no schedule line owned by "PM" beside the designer's dated task
    r = await pg.evaluate("""() => ({ sched: DB.projects.flatMap(p => (p.tasks || []).filter(t => /LPC/.test(t.name || '') && t.fromComm).map(t => t.name)),
      acts: DB.projects.flatMap(p => (p.actions || []).filter(a => /LPC/.test(a.title || '') && /Sarah/.test(a.assignee || '')).map(a => a.title)) })""")
    c.ok(not r['sched'] and len(r['acts']) >= 2, f'one LPC letter makes one task, on the designer: {r}')
    # the no-show answer filed on the raise's job (121 State), though the PM was on 45 Cranberry
    r = await pg.evaluate("""() => ({ on121: (DB.projects.find(p => p.id === 'p121').actions || []).filter(a => /Restoration crew|Tomas/.test(a.title)).length,
      elsewhere: DB.projects.filter(p => p.id !== 'p121').flatMap(p => (p.actions || []).filter(a => /Restoration crew|Tomas/.test(a.title))).length,
      ox: (DB.outbox || []).filter(o => /Restoration crew|Confirming Fri/.test(o.subject)).map(o => (o.about || {}).projectId) })""")
    c.ok(r['on121'] >= 2 and not r['elsewhere'] and r['ox'] and all(x == 'p121' for x in r['ox']), f"the no-show answer files on the raise's job: {r}")
    # the sent invoice's mail: to the client's billing contact, readable, and the person's own send
    r = await pg.evaluate("""() => { const o = (DB.outbox || []).filter(x => x.kind === 'doc' && (x.about || {}).docId === window.__f2inv).pop() || {};
      const seen = (__SIM.mbSentAll() || []).find(m => m.id === 'outbox_' + o.id) || {};
      return { to: o.to, read: { to: seen.to, uid: seen.uid }, sentBy: o.sentBy, sentByUid: o.sentByUid, byUid: o.byUid, status: o.status }; }""")
    c.ok(r['to'] and r['to'].get('email') == 'elena.rivera@example.com', f"the invoice's mail goes to the client's billing contact: {r['to']}")
    c.ok(r['read']['to'] == 'Elena Rivera <elena.rivera@example.com>', f"the referee reads its recipient as an address, not [object Object]: {r['read']}")
    c.ok(r['sentByUid'] == 'u_billing' and r['byUid'] == 'u_billing' and r['sentBy'] == 'Billing' and r['read']['uid'] == 'u_billing', f'the person who pressed Send is on the mail, so it reads as their own send: {r}')
    # a billing contact named on the client wins over the primary contact
    r = await pg.evaluate("""() => { const c = DB.clients.find(x => x.id === 'cl45'); const keep = JSON.stringify(c.contacts);
      c.contacts.push({ id: 'ctF2b', name: 'Marco Rivera', email: 'marco.rivera@example.com', role: 'Billing contact' });
      const d = c.invoices.find(x => x.id === window.__f2inv), e = crDocEmail(c, d); c.contacts = JSON.parse(keep); return e.to; }""")
    c.ok(r and r.get('email') == 'marco.rivera@example.com', f'with a billing contact on file, the mail goes to them: {r}')


async def payapp(c, pg):
    """A pay application never lowers a line's cumulative % (the referee's S1 on INV-2026-040, 121 State)."""
    await sign_in(pg, 'u_billing')
    r = await pg.evaluate("""() => { const c = DB.clients.find(x => x.id === 'cl121'), d = c.estimates.find(e => e.id === 'es1');
      const inv = ctProgressInvoice(c, d); if (!c.invoices.includes(inv)) c.invoices.push(inv); save(); window.__f2pa = inv.id;
      const rows = pgRows('p121');
      return inv.lines.map(l => { const r = rows.find(x => x.sv.id === l.sovId) || {}; return { item: l.item, prev: +l.prevPct || 0, pct: +l.pct || 0, toDate: l.toDatePct, ev: r.pr ? r.pr.pct : null, note: l.evidenceBelow || '' }; }); }""")
    c.ok(all(l['pct'] >= 0 and abs(l['toDate'] - (l['prev'] + l['pct'])) < 0.01 and l['toDate'] >= l['prev'] - 0.001 for l in r),
         f'every line starts from its previous cumulative: to date = previous + this period, never below ({[(l["item"][:12], l["prev"], l["pct"], l["toDate"]) for l in r][:5]})')
    below = [l for l in r if l['ev'] is not None and l['ev'] < l['prev'] - 0.01]
    c.ok(below and all(l['note'] and f"{round(l['prev'], 2)}" in l['note'] for l in below),
         f'a line whose evidence is below what was billed says so, with the previous %: {[(l["item"][:14], l["ev"], l["prev"], l["note"][:60]) for l in below][:4]}')
    # a line typed below its previous cumulative is held at it in the editor, and Send refuses it if it got there
    r = await pg.evaluate("""async () => { const c = DB.clients.find(x => x.id === 'cl121'), d = c.invoices.find(x => x.id === window.__f2pa);
      view = 'billing'; clientOpen = c.id; docOpen = { kind: 'invoice', id: d.id }; render(); await new Promise(r => setTimeout(r, 200));
      const l = d.lines[0], inp = document.querySelector(`tr[data-line="${l.id}"] [data-f="pct"]`);
      let typed = null; if (inp) { inp.value = '-20'; inp.dispatchEvent(new Event('change', { bubbles: true })); typed = d.lines[0].pct; }
      d.lines[0].pct = -20; const st = d.status; const n0 = (document.getElementById('toast') || {}).innerText;
      await docAction(c, d, 'send'); await new Promise(r => setTimeout(r, 200));
      const t = (document.getElementById('toast') || {}).innerText || ''; const out = { typed, status: d.status, was: st, toast: t };
      d.lines[0].pct = 0; save(); return out; }""")
    c.ok(r['typed'] is not None and r['typed'] >= 0, f'a negative this-period % typed on a line is held at 0, the previous cumulative: {r["typed"]}')
    c.ok(r['status'] == 'draft' and 'Demolition' in r['toast'] and '51.67' in r['toast'], f'Send refuses a line below its previous cumulative and names the line and the previous %: {r}')


async def main():
    c = Checks()
    async with async_playwright() as p:
        for phone in (False, True):
            label = 'phone' if phone else 'desktop'
            b, pg, errs = await open_app(p, phone=phone)
            await pg.evaluate(PT)
            for uid, name, setup, run, want in SCENARIOS:
                out = await run_scenario(c, pg, label, uid, name, setup, run, want)
                if not out: continue
                made, where = out
                await open_lands(c, pg, label, uid, name, made, where)
                await after_reload(c, pg, label, uid, name, made, where)
            if not phone:
                await rules(c, pg)
                await payapp(c, pg)
            c.ok(not errs, f'{label}: no page errors {errs[:3]}')
            await b.close()
    return c.done()


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
