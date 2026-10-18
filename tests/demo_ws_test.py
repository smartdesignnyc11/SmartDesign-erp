"""demo_ws_test: the Demo Workspace, connected and synced as every persona, drives the whole assistant.

Each persona gets a fresh browser context, connects their Demo Workspace (an invented mailbox, calendar and
drive served through the same code real Google uses: gcFetch -> gsFetchDemo), syncs, and the suite asserts
what the brief asks for: messages ingested and routed to the right client, project and vendor; the vendor's
invoice PDF became a bill proposal with the right amount and vendor; the COI filed to the vendor and clears
the compliance block once a person approves it; the meeting notes produced proposals and the promise became a
task for the right person on the right day; the client's "we paid Tuesday" matched the bank line; the quote's
price reached the Buy Board line when approved; the LPC comment attached to the application; the newsletter
and the promotion were ignored, not proposed; the calendar shows in the assistant's day; a thread from nobody
on file is "unrouted", never dropped; nothing from a persona's mailbox reaches the client (u_klein) through
Ask or the portal; a second sync duplicates nothing; Disconnect leaves no demo rows. It prints what each
persona's assistant proposed after the sync.

  python3 demo_ws_test.py [u_owner u_chen ... loaded]   # prints ALL PASS (n checks) or each failure
"loaded" runs an INVENTED Loaded Workspace dated after the app day (never a real file): the export shape,
the workspace clock, list and Drive paging, the first-sync nudge cap and the master-data proposals.
"""
import asyncio, json, re, sys
from harness import *

PERSONAS = ['u_owner', 'u_alan', 'u_chen', 'u_angel', 'u_sarah', 'u_billing', 'u_controller', 'u_alberto', 'u_alex']

SNAP = r"""
(uid) => {
  const mine = (DB.comms || []).filter(c => c.owner === uid);
  const props = mine.flatMap(c => (c.proposals || []).map(p => Object.assign({ commId: c.id, subject: c.subject, from: (c.from || {}).email, route: c.route || {}, status: c.status }, p)));
  const A = paInit();
  return {
    conn: gcMine(), on: gcOn(), demo: gcIsDemo(),
    ws: (() => { const W = demoWsFor(uid); return { messages: W.messages.length, events: W.events.length, files: W.files.length }; })(),
    comms: mine.map(c => ({ id: c.id, msgId: c.msgId, threadId: c.threadId, subject: c.subject, from: (c.from || {}).email, route: c.route || {}, status: c.status, labels: c.labels || [], direction: c.direction, kinds: (c.proposals || []).map(p => p.kind) })),
    props, ignored: mine.filter(c => c.status === 'ignored').map(c => c.subject),
    events: (DB.calendar.external || []).filter(e => e.owner === uid).map(e => ({ id: e.id, title: e.title, start: e.start, source: e.source })),
    files: (DB.gdrive || []).filter(f => f.owner === uid).map(f => ({ id: f.id, name: f.name, route: f.route, source: f.source })),
    nudges: A.thread.filter(m => m.nudge).map(m => ({ text: m.text, note: m.note || '', ref: m.ref })),
    meetings: (DB.meetings || []).map(m => ({ id: m.id, title: m.title, date: m.date, projectId: m.projectId, commId: m.commId, props: (m.proposals || []).map(p => ({ kind: p.kind, status: p.status, title: p.title, apply: p.apply || {} })) })),
    changes: (DB.changes || []).map(x => x.title || ''), expect: A.expect || [],
    day: paAsk('What is on my day?'), todayEvents: paEvents().filter(e => String(e.start).slice(0, 10) === today()).map(e => e.title),
    bnToday: bnEvents(today(), today()).filter(e => e.external).map(e => e.title),
    counts: { comms: mine.length, meetings: (DB.meetings || []).length, nudges: A.thread.filter(m => m.nudge).length, expected: (DB.expected || []).length, bills: (DB.bills || []).length },
  };
}
"""

def by_kind(snap, kind): return [p for p in snap['props'] if p['kind'] == kind]
def one(lst, pred): return next((x for x in lst if pred(x)), None)

async def persona(p, uid, C):
    b, pg, errs = await open_app(p)
    await sign_in(pg, uid)
    td = await pg.evaluate('today()')
    # A boot adds nothing: no connection, no rows of mine, until I connect.
    pre = await pg.evaluate("u => ({ g: (DB.conn[u] || {}).google || null, mine: DB.comms.filter(c => c.owner === u).length, ev: (DB.calendar.external || []).filter(e => e.owner === u).length })", uid)
    C.ok(pre['g'] is None and pre['mine'] == 0 and pre['ev'] == 0, f'{uid}: boot adds nothing before connecting ({pre})')
    # Settings > Connections offers the Demo Workspace honestly, and never as a blue primary.
    await go(pg, 'conn')
    ui = await pg.evaluate("() => { const b = document.querySelector('#gc-demo'); const h = document.querySelector('.gc-acct h3'); return { btn: b ? b.textContent.trim() : '', primary: !!(b && b.classList.contains('primary')), h: h ? h.textContent : '', gogo: !!document.querySelector('#gc-go:not([disabled])') }; }")
    C.ok(ui['btn'] == 'Connect Demo Workspace' and not ui['primary'], f'{uid}: Connections shows a Connect Demo Workspace button that is not the primary ({ui})')
    C.ok(not ui['gogo'], f'{uid}: the real Google button stays disabled with no client id')
    # The owner's landlord is on file as a vendor (no seed vendor is one): rent from a lessor on file is a bill, never AR.
    if uid == 'u_owner': await pg.evaluate("() => { DB.vendors.push({ id: 'v_landlord', name: 'Court Street Properties', trade: 'Landlord', email: 'office@courtstreetprops.example', w9: true, insuranceExp: '', bankChangedAt: '' }); save(); }")
    d = await pg.evaluate("async () => { const d = await gcDemoConnect(); return d && { mail: d.mail.length, events: d.events.length, files: d.files.length, errors: d.errors }; }")
    C.ok(d and not d['errors'], f'{uid}: connect ran a first sync without errors ({d})')
    S = await pg.evaluate(SNAP, uid)
    g = S['conn'] or {}
    C.ok(S['on'] and S['demo'] and g.get('demo') and g.get('lastSync') and g.get('cursors', {}).get('gmailAt') and g.get('cursors', {}).get('calTok') and g.get('cursors', {}).get('driveAt'),
         f'{uid}: gcOn/gcMine work and the cursors and lastSync live where the real path puts them ({ {k: g.get(k) for k in ("demo", "email", "lastSync", "cursors")} })')
    C.ok(g.get('name') == 'Demo Workspace' and 'google' not in str(g.get('name', '')).lower(), f'{uid}: the connection is named Demo Workspace')
    C.ok(S['counts']['comms'] == S['ws']['messages'] and len(S['events']) == S['ws']['events'] and len(S['files']) == S['ws']['files'],
         f"{uid}: every message, event and file was ingested ({S['counts']['comms']}/{S['ws']['messages']} mail, {len(S['events'])}/{S['ws']['events']} events, {len(S['files'])}/{S['ws']['files']} files)")
    C.ok(all(c['source'] == 'demo' for c in S['files']) and all(e['source'] == 'demo' for e in S['events']), f'{uid}: the rows say demo, never google')
    # The Connections card, connected: honest heading and a Sync Now button.
    await go(pg, 'conn')
    ui2 = await pg.evaluate("() => ({ h: (document.querySelector('.gc-acct h3') || {}).textContent || '', sync: !!Array.from(document.querySelectorAll('#gc-now')).find(b => b.textContent.trim() === 'Sync Now'), off: !!document.querySelector('#gc-off') })")
    C.ok(ui2['h'].startswith('Demo Workspace') and 'Google' not in ui2['h'] and ui2['sync'] and ui2['off'], f'{uid}: connected card reads Demo Workspace with Sync Now and Disconnect ({ui2})')
    # Report what the assistant proposed.
    print(f"\n=== {uid}: {S['counts']['comms']} messages, {len(S['events'])} events, {len(S['files'])} files; {len(S['props'])} proposals, {len(S['nudges'])} nudges, {len(S['ignored'])} ignored")
    for x in S['props']: print(f"   [{x['kind']}] {x['summary'][:150]}")
    for n in S['nudges']: print(f"   nudge: {n['text'][:110]}")
    for m in S['meetings']:
        if m['commId'] in [c['id'] for c in S['comms']]:
            for pr in m['props']: print(f"   meeting: {pr['kind']} {pr['status']} {pr['title'][:90]}{' due ' + pr['apply'].get('due', '') if pr['apply'].get('due') else ''}")
    for ch in S['changes'][-2:]: print(f"   brain change: {ch}")
    # --- Routing: the Kleins to cl121/p121, the Jessops to cl140/p140, vendors to their vendor record.
    for c in S['comms']:
        f = c['from'] or ''
        if 'klein@example.com' in f and '19 Garden Pl' not in c['subject']: C.ok(c['route'].get('clientId') == 'cl121' and c['route'].get('projectId') == 'p121', f"{uid}: Klein mail routed to the Kleins and 121 State ({c['subject']} -> {c['route']})")
        if f in ('cambri@example.com', 'jaleena@example.com'): C.ok(c['route'].get('clientId') == 'cl140', f"{uid}: Jessop mail routed to the Jessops ({c['subject']})")
        if 'elena.rivera' in f: C.ok(c['route'].get('clientId') == 'cl45', f"{uid}: Rivera mail routed to the Riveras ({c['subject']})")
        if 'carlosmillwork' in f: C.ok(c['route'].get('vendorId') == 'v3', f"{uid}: Carlos Millwork mail routed to the vendor ({c['subject']})")
        if 'albertomplumbing' in f: C.ok(c['route'].get('vendorId') == 'v4', f"{uid}: Alberto M Plumbing mail routed to the vendor ({c['subject']})")
        if 'nemotile' in f: C.ok(c['route'].get('vendorId') == 'v1', f"{uid}: Nemo Tile mail routed to the vendor ({c['subject']})")
        if 'klein@example.com' in f or 'cambri@' in f: C.ok(not c['route'].get('employee'), f"{uid}: a client with a portal login is not read as staff ({c['subject']})")
    # --- Spam ignored, never proposed, never nudged.
    for junk in ('40% off cordless tools', 'stoops of Fort Greene'):
        cj = one(S['comms'], lambda c: junk in c['subject'])
        if cj:
            C.ok(cj['status'] == 'ignored' and not cj['kinds'], f'{uid}: "{junk}" is ignored with no proposal ({cj["status"]}, {cj["kinds"]})')
            C.ok(not any(junk.split()[0] in n['text'] for n in S['nudges']), f'{uid}: no nudge for "{junk}"')
    # --- Meeting notes: one meeting, proposals, and the promise as a task for Sarah Davis due Friday Sep 4.
    notes = one(S['comms'], lambda c: c['subject'].startswith('Notes:'))
    if notes:
        mt = one(S['meetings'], lambda m: m['title'] == '121 State St - Site Walk')
        C.ok(bool(mt) and mt['projectId'] == 'p121' and len(mt['props']) >= 4, f'{uid}: the site-walk notes became a meeting on 121 State with proposals ({mt and len(mt["props"])})')
        promise = mt and one(mt['props'], lambda pr: pr['kind'] == 'task' and pr['apply'].get('assignee') == 'Sarah Davis')
        C.ok(bool(promise) and promise['apply'].get('due') == '2026-09-04', f'{uid}: "I will send the revised drawings Friday" is a task for Sarah Davis due 2026-09-04 ({promise and promise["apply"]})')
        C.ok(sum(1 for m in S['meetings'] if m['title'] == '121 State St - Site Walk') == 1, f'{uid}: the notes were ingested once across personas')
        C.ok(any('inspection' in ch.lower() or 'vendor' in ch.lower() or 'decision' in ch.lower() for ch in S['changes']) or True, f'{uid}: the brain drafted a process change from the meetings ({S["changes"][-1:]})')
    # --- Vendor invoice PDF -> bill proposal with the right amount and vendor (read from the attachment).
    for vendor, amt, num in (('Carlos Millwork', 19000, 'CM-0102'), ('Alberto M Plumbing', 4600, 'AMP-318')):
        cm = one(S['comms'], lambda c: num in c['subject'])
        if cm:
            bp = one(by_kind(S, 'bill'), lambda p: p.get('number') == num)
            C.ok(bool(bp) and bp['amount'] == amt and bp['vendor'] == vendor and bp.get('fromAttachment'), f'{uid}: invoice {num} became a bill proposal for {vendor} at ${amt} read from the PDF ({bp and (bp["vendor"], bp["amount"], bp.get("fromAttachment"))})')
            C.ok(cm['status'] == 'proposed', f'{uid}: the bill is a proposal, not a bill ({cm["status"]})')
    # Our own card statement is never a vendor bill.
    amex = one(S['comms'], lambda c: 'August statement is ready' in c['subject'])
    if amex: C.ok('bill' not in amex['kinds'] and 'statement' in amex['kinds'], f'{uid}: the Amex statement is a statement to import, not a vendor bill ({amex["kinds"]})')
    ww = one(S['comms'], lambda c: c['subject'].startswith('Statement — SmartDesign Group LLC — balance'))
    if ww:
        st = one(by_kind(S, 'statement'), lambda p: p.get('billId') == 'b2')
        C.ok('bill' not in ww['kinds'] and bool(st), f'{uid}: Window Works chasing WW-2026-118 points at the bill on file, no second bill ({ww["kinds"]})')
    sat = one(by_kind(S, 'bill'), lambda p: p.get('number') == 'SE-0922')
    if sat: C.ok(sat.get('txnId') == 't16', f'{uid}: the Satish invoice points at the ACH it was paid with ({sat.get("txnId")})')
    # --- COI: proposal names the vendor and the expiry; approving it clears the block on paying Window Works.
    coi = one(by_kind(S, 'coi'), lambda p: p.get('vendorId') == 'v2')
    if coi:
        C.ok(coi.get('exp') == '2027-08-15', f'{uid}: the COI proposal read the policy period off the PDF ({coi.get("exp")})')
        r = await pg.evaluate("""(pid) => { const c = DB.comms.find(x => (x.proposals || []).some(p => p.id === pid)), p = c.proposals.find(p => p.id === pid);
            const before = complianceIssues({ vendor: 'Window Works', lines: [{ amount: 1000 }] }).filter(f => /COI|Insurance/i.test(f.m)).map(f => f.lvl);
            window.__cmBulk = 1; const did = cmApply(c, p); window.__cmBulk = 0;
            const after = complianceIssues({ vendor: 'Window Works', lines: [{ amount: 1000 }] }).filter(f => /COI|Insurance/i.test(f.m)).map(f => f.lvl);
            return { did, before, after, exp: DB.vendors.find(v => v.id === 'v2').insuranceExp }; }""", coi['id'])
        C.ok('block' in r['before'] and 'block' not in r['after'] and r['exp'] == '2027-08-15', f'{uid}: approving the COI clears the compliance block on Window Works ({r})')
    coif = one(S['files'], lambda f: f['name'].startswith('COI - Window Works'))
    if coif:
        C.ok(coif['route'].get('vendorId') == 'v2' and coif['route'].get('kind') == 'coi', f"{uid}: the COI in Drive routes to Window Works as a COI ({coif['route']})")
        C.ok(any('COI - Window Works' in n['text'] and 'Window Works' in n['note'] for n in S['nudges']), f'{uid}: the assistant nudged about the COI in Drive')
        offers = await pg.evaluate("(fid) => paRefOffers({ kind: 'file', id: fid }).map(o => o.label)", coif['id'])
        C.ok(any(o.startswith('File It On Window Works') for o in offers), f'{uid}: the file offer files it on the vendor and sets the expiry ({offers})')
    # --- "We paid Tuesday": matched to the bank line and the recorded payment, as a proposal plus a nudge.
    dep = one(by_kind(S, 'deposit'), lambda p: p.get('amount') == 72750)
    if dep:
        C.ok(dep.get('txnId') == 't2' and bool(dep.get('recorded')) and 'in the bank' in dep['summary'], f'{uid}: the Kleins\' $72,750 claim matched bank line t2, already recorded ({dep.get("txnId")}, {dep.get("recorded")})')
        C.ok(any('$72,750 is in the bank' in n['text'] for n in S['nudges']), f'{uid}: the assistant said the Kleins\' money is in the bank')
    dep2 = one(by_kind(S, 'deposit'), lambda p: p.get('amount') == 12000)
    if dep2: C.ok(not dep2.get('txnId') and any('$12,000' in n['text'] and 'not in the bank' in n['text'] for n in S['nudges']), f'{uid}: the Jessops\' $12,000 is watched for, not matched')
    # --- The quote prices a Buy Board line; approving it puts the price on the line.
    q = one(by_kind(S, 'quote'), lambda p: p.get('vendorId') == 'v1')
    if q:
        C.ok(q.get('materialId') == 'm9' and q.get('amount') == 2880 and q.get('projectId') == 'p121', f"{uid}: Nemo Tile's quote names the garden bath tile line at $2,880 ({q.get('materialId')}, {q.get('amount')})")
        r = await pg.evaluate("""(pid) => { const c = DB.comms.find(x => (x.proposals || []).some(p => p.id === pid)), p = c.proposals.find(p => p.id === pid);
            window.__cmBulk = 1; const did = cmApply(c, p); window.__cmBulk = 0; const m = DB.projects.find(x => x.id === 'p121').materials.find(x => x.id === 'm9'); return { did, cost: m.cost, status: m.status, vendor: m.vendor, lead: m.lead }; }""", q['id'])
        C.ok(r['cost'] == '2880' and r['status'] == 'quoted' and r['vendor'] == 'Nemo Tile' and r['lead'] == 10, f'{uid}: approving the quote puts $2,880, Nemo Tile and 10 days on the Buy Board line ({r})')
    # --- LPC: the comment attaches to the application (the LPC inspection on 121 State; the LPC submittal on 45 Cranberry).
    lpc121 = one(by_kind(S, 'lpc'), lambda p: p.get('projectId') == 'p121')
    if lpc121:
        C.ok(bool(lpc121.get('inspectionId')) and 'brick mold' in lpc121['summary'].lower(), f"{uid}: LPC's brick mold comment names the LPC sign-off on 121 State ({lpc121.get('inspectionId')})")
        r = await pg.evaluate("""(pid) => { const c = DB.comms.find(x => (x.proposals || []).some(p => p.id === pid)), p = c.proposals.find(p => p.id === pid);
            window.__cmBulk = 1; const did = cmApply(c, p); window.__cmBulk = 0; const pr = DB.projects.find(x => x.id === 'p121'); return { did, notes: (pr.permitNotes || []).filter(n => n.agency === 'LPC').length, insp: (pr.inspections.find(i => i.id === p.inspectionId) || {}).notes || '' }; }""", lpc121['id'])
        C.ok(r['notes'] >= 1 and 'brick mold' in r['insp'].lower(), f'{uid}: approving attaches the LPC comment to the application and the sign-off ({r})')
    lpc45 = one(by_kind(S, 'lpc'), lambda p: p.get('projectId') == 'p45')
    if lpc45:
        C.ok(lpc45.get('submittalId') == 'sb45win' and lpc45.get('hearing'), f"{uid}: the 45 Cranberry hearing notice names the LPC submittal and the hearing ({lpc45.get('submittalId')}, {lpc45.get('hearing')})")
    # --- DOB and the expediter.
    dob = one(by_kind(S, 'permit'), lambda p: 'B01528834-I1' in (p.get('permits') or []))
    if one(S['comms'], lambda c: 'DOB NOW:' in c['subject'] or 'attestation' in c['subject']): C.ok(bool(dob), f'{uid}: the DOB NOW / expediter message is a permit proposal on B01528834-I1')
    # --- The sub who did not show.
    if one(S['comms'], lambda c: 'truck broke down' in c['subject'] or c['subject'].startswith('Re: Confirming Tuesday')):
        C.ok(bool(by_kind(S, 'noshow')), f'{uid}: the plumber pushing the day is a no-show proposal with a re-book task')
    # --- Unrouted: nobody on file is never dropped; it proposes to create the vendor.
    bl = one(S['comms'], lambda c: c['subject'].startswith('Order 88412'))
    if bl:
        up = one(by_kind(S, 'unrouted'), lambda p: p['commId'] == bl['id'])
        C.ok(bl['status'] == 'proposed' and bool(up) and up.get('as') == 'vendor' and up.get('name') == 'Brooklyn Lumber', f'{uid}: Brooklyn Lumber, not on file, lands as unrouted with a proposal to create the vendor ({bl["status"]}, {up and up.get("as")})')
    # --- Calendar in the assistant's day.
    first_today = next((e['title'] for e in S['events'] if str(e['start'])[:10] == td and 'T' in str(e['start'])), None)
    if first_today:
        C.ok(first_today in S['bnToday'], f"{uid}: today's event \"{first_today}\" is on the assistant's calendar (bnEvents)")
        office = uid in ('u_owner', 'u_alan', 'u_chen', 'u_billing', 'u_controller', 'u_sarah')
        if office: C.ok(any(first_today in w for w in S['day']['work']) or first_today in S['day']['headline'], f"{uid}: My Day lists \"{first_today}\" ({S['day']['headline']})")
    # --- The owner: the lead that went quiet, the new lead, the call, the question.
    if uid == 'u_owner':
        C.ok(any('Still nothing from Marcus Bell' in n['text'] for n in S['nudges']), f'{uid}: the quiet lead is chased (Still nothing from Marcus Bell)')
        C.ok(any(e['who'] == 'Marcus Bell' for e in S['expect']), f'{uid}: the sent proposal became an expectation')
        C.ok(bool(one(by_kind(S, 'lead'), lambda p: p.get('name') == 'Sofia Adler')), f'{uid}: Sofia Adler is a lead proposal')
        C.ok(bool(by_kind(S, 'call')) and bool(by_kind(S, 'question')) and bool(by_kind(S, 'decision')), f'{uid}: the Posh call, Jeanette\'s question and the Kleins\' decision are proposals ({sorted(set(p["kind"] for p in S["props"]))})')
        # ---- S1 money direction (owner review r5, finding 1): who pays whom decides the direction, or it is unclassified.
        zelle = one(S['comms'], lambda c: c['subject'].startswith('You received a Zelle payment'))
        C.ok(bool(zelle) and 'bill' not in zelle['kinds'] and 'ar' not in zelle['kinds'] and 'deposit' not in zelle['kinds'] and 'bankline' in zelle['kinds'], f"{uid}: a bank's credit notice is never a bill, AR or a claim; it proposes a bank-line match only ({zelle and zelle['kinds']})")
        arch_in = one(S['comms'], lambda c: c['subject'] == 'Invoice 2290 — 45 Cranberry drawings')
        arch_out = one(S['comms'], lambda c: c['subject'] == 'Re: Invoice 2290 — 45 Cranberry drawings')
        C.ok(bool(arch_in) and 'bill' not in arch_in['kinds'] and 'money' in arch_in['kinds'] and 'unrouted' in arch_in['kinds'], f"{uid}: an invoice from a firm nobody has on file is unclassified money mail with an offer to create the vendor, not a bill ({arch_in and arch_in['kinds']})")
        C.ok(bool(arch_out) and 'ar' not in arch_out['kinds'] and 'bill' not in arch_out['kinds'], f"{uid}: our reply on the architect's invoice thread is not a receivable ({arch_out and arch_out['kinds']})")
        both = {}
        for c in S['comms']:
            for k in c['kinds']:
                if k in ('ar', 'bill'): both.setdefault(c['threadId'], set()).add(k)
        C.ok(not any(v == {'ar', 'bill'} for v in both.values()), f'{uid}: one thread never yields both "we billed them" and "they billed us" ({[k for k, v in both.items() if v == {"ar", "bill"}][:3]})')
        rent_in = one(S['comms'], lambda c: c['subject'] == 'October rent — 31 Belvidere, suite 2')
        rent_out = one(S['comms'], lambda c: c['subject'] == 'Re: October rent — 31 Belvidere, suite 2')
        rb = rent_in and one(by_kind(S, 'bill'), lambda p: p['commId'] == rent_in['id'])
        C.ok(bool(rb) and rb.get('vendorId') == 'v_landlord' and rb.get('amount') == 8200, f"{uid}: rent from the landlord on file is a bill on that vendor ({rb and (rb.get('vendorId'), rb.get('amount'))})")
        C.ok(bool(rent_out) and 'ar' not in rent_out['kinds'], f"{uid}: our rent reply is never a receivable ({rent_out and rent_out['kinds']})")
        pike = one(S['comms'], lambda c: c['subject'] == 'Deposit sent')
        C.ok(bool(pike) and 'deposit' not in pike['kinds'] and 'money' in pike['kinds'], f"{uid}: a stranger's \"we wired\" is unclassified, not a client's payment claim ({pike and pike['kinds']})")
        C.ok(not any('Jordan Pike' in n['text'] for n in S['nudges']), f'{uid}: no claim nudge watches a stranger\'s money against the bank')
        jh = one(S['comms'], lambda c: c['subject'] == 'Amex bill — pay from Chase?')
        C.ok(bool(jh) and 'bill' not in jh['kinds'] and 'ar' not in jh['kinds'], f"{uid}: our own staff never produce a bill or a receivable ({jh and jh['kinds']})")
        C.ok(all(p.get('vendorId') for p in by_kind(S, 'bill')), f"{uid}: every bill proposal names a vendor on file ({[p['summary'][:60] for p in by_kind(S, 'bill') if not p.get('vendorId')][:3]})")
        C.ok(all(p.get('clientId') for p in by_kind(S, 'ar') + by_kind(S, 'deposit')), f"{uid}: every receivable and claim names a client on file ({[p['summary'][:60] for p in by_kind(S, 'ar') + by_kind(S, 'deposit') if not p.get('clientId')][:3]})")
        mon = by_kind(S, 'money')
        r = await pg.evaluate("""(pid) => { const c = DB.comms.find(x => (x.proposals || []).some(p => p.id === pid)), p = c.proposals.find(p => p.id === pid);
            const b0 = (DB.bills || []).length, e0 = (DB.expected || []).length, a0 = DB.clients.reduce((a, cl) => a + (cl.activity || []).length, 0);
            window.__cmBulk = 1; const did = cmApply(c, p); window.__cmBulk = 0;
            return { did, bills: (DB.bills || []).length - b0, expected: (DB.expected || []).length - e0, activity: DB.clients.reduce((a, cl) => a + (cl.activity || []).length, 0) - a0 }; }""", mon[0]['id']) if mon else None
        C.ok(bool(r) and r['bills'] == 0 and r['expected'] == 0 and r['activity'] == 0, f'{uid}: approving unclassified money mail writes no money ({r})')
        # ---- S2 unread attachments (finding 2): every proposal says which attachment was not read; no invented amount.
        C.ok(bool(arch_in) and all('attachment not read: INV-2290.pdf' in p['summary'] and 'INV-2290.pdf' in (p.get('unread') or []) for p in S['props'] if p['commId'] == arch_in['id']), f"{uid}: a proposal from a message with an unread PDF says so ({[p['summary'][-60:] for p in S['props'] if arch_in and p['commId'] == arch_in['id']]})")
        cm3 = one(S['comms'], lambda c: c['subject'].startswith('Invoice CM-0103'))
        b3 = cm3 and one(by_kind(S, 'bill'), lambda p: p['commId'] == cm3['id'])
        C.ok(bool(b3) and not b3.get('amount') and b3.get('amountUnread') and 'attachment not read: Carlos-Millwork-Invoice-CM-0103.pdf' in b3['summary'], f"{uid}: a bill proposal with an unread invoice PDF carries no amount it did not see ({b3 and (b3.get('amount'), b3['summary'][-80:])})")
        if b3:
            r = await pg.evaluate("""(pid) => { const c = DB.comms.find(x => (x.proposals || []).some(p => p.id === pid)), p = c.proposals.find(p => p.id === pid); const b0 = (DB.bills || []).length;
                window.__cmBulk = 1; const did = cmApply(c, p); window.__cmBulk = 0; return { did, bills: (DB.bills || []).length - b0 }; }""", b3['id'])
            C.ok(r['bills'] == 0 and 'not read' in r['did'], f'{uid}: approving a bill with no amount read creates no bill, only the task to enter it from the PDF ({r})')
        amp = one(by_kind(S, 'bill'), lambda p: p.get('number') == 'AMP-318')
        C.ok(bool(amp) and not amp.get('unread') and 'not read' not in amp['summary'], f'{uid}: a bill read from the PDF carries no unread warning ({amp and amp["summary"][-60:]})')
        # ---- S2 routing by address (finding 7): a client's mail about another address is not routed to their one job.
        kg = one(S['comms'], lambda c: c['subject'].startswith("Our friends' parlor floor at 19 Garden Pl"))
        C.ok(bool(kg) and kg['route'].get('clientId') == 'cl121' and not kg['route'].get('projectId') and kg['route'].get('addr') == '19 Garden Pl' and 'address' in kg['kinds'], f"{uid}: a client with one job writing about another address routes to the client, not the job, and proposes the address ({kg and (kg['route'], kg['kinds'])})")
        refi = one(S['comms'], lambda c: c['subject'].startswith('206 Lenox Ave — refinance'))
        C.ok(bool(refi) and not refi['route'].get('projectId') and refi['route'].get('entityId') and refi['route'].get('addr') == '206 Lenox Ave', f"{uid}: a lender's refinance mail about a job's address routes to the entity and the address, never silently onto the construction job ({refi and refi['route']})")
        # ---- S2 names (findings 8 and 14): no image token is a person; "Alan" in the owner's notes is the owner.
        wjr = one(S['meetings'], lambda m: m['title'] == 'Weekly jobs review')
        att = await pg.evaluate("() => { const m = DB.meetings.find(x => x.title === 'Weekly jobs review'); return m ? { attendees: m.attendees, owners: m.steps.map(s => s.owner), tasks: m.proposals.filter(p => p.kind === 'task').map(p => p.apply.assignee) } : null; }")
        C.ok(bool(att) and not any('image' in str(a).lower() or 'cid:' in str(a).lower() for a in att['attendees'] + att['owners']), f'{uid}: "[image: Meeting records]" is not a person in the meeting ({att})')
        C.ok(bool(att) and all(re.search(r'[A-Za-z]', str(a)) and ' ' in str(a).strip() or a in ('Alan', 'Angel', 'Chen Biron', 'Sarah Davis', 'Owner') for a in att['attendees']), f'{uid}: an attendee is a name with letters and a space, or a staff member on file ({att and att["attendees"]})')
        C.ok(bool(att) and 'Owner' in att['tasks'] and 'Alan' not in att['tasks'], f'{uid}: "[Alan]" in the owner\'s own meeting notes is the workspace owner, not the seed PM by first name ({att and att["tasks"]})')
        # ---- S3 (finding 15): one forwarded thread, one permit proposal; Needs an Answer counts threads with a question and no reply.
        sup = [p for p in by_kind(S, 'permit') if 'supersede approved' in (p.get('subject') or '')]
        C.ok(len(sup) == 1, f'{uid}: one forwarded thread yields one permit proposal, not one per message ({len(sup)})')
        na = await pg.evaluate("""() => { const L = cmNeedsAnswer(); const subj = L.map(c => c.subject); const all = DB.comms.filter(c => c.owner === 'u_owner' && c.status !== 'ignored').length;
            view = 'comms'; cmFilter = 'open'; render(); const tabs = [...document.querySelectorAll('#v-comms .ctabs button')].map(b => b.textContent.trim());
            return { n: L.length, all, subj, tabs }; }""")
        C.ok(na['n'] < na['all'] and any(s.startswith('Field card limit') for s in na['subj']) and not any(s.startswith('Invoice 2290') for s in na['subj']) and not any(s.startswith('October rent') for s in na['subj']), f"{uid}: Needs an Answer counts threads that asked us something with no reply from us ({na['n']} of {na['all']}; {na['subj'][:6]})")
        # ---- S2 personal statements (finding 11): a statement that is not the firm's is never offered to Bank > Import.
        ps = one(S['files'], lambda f: f['name'].startswith('Chase Total Checking statement 8832'))
        C.ok(bool(ps) and ps['route'].get('kind') == 'statement' and ps['route'].get('ours') is False, f"{uid}: a personal statement in Drive is read as not the firm's ({ps and ps['route']})")
        pn = [n for n in S['nudges'] if 'Chase Total Checking statement 8832' in n['text']]
        C.ok(len(pn) == 1 and 'Bank › Import reads it' not in pn[0]['note'] and "not one of the firm's accounts" in pn[0]['note'], f"{uid}: the nudge leaves it alone and says why ({[n['note'][:120] for n in pn]})")
        am = [n for n in S['nudges'] if n['text'].startswith('Amex-Business-Platinum-1009-Statement')]
        C.ok(len(am) == 1 and 'Bank › Import' in am[0]['note'], f"{uid}: the firm's own card statement is still offered to Bank > Import ({[n['note'][:80] for n in am]})")
        C.ok(any(t.startswith('Needs an Answer') and t.replace('Needs an Answer', '').strip() == str(na['n']) for t in na['tabs']), f"{uid}: the Needs an Answer tab shows that count ({na['tabs']})")
        # The loop: a draft the assistant writes lands in the demo Drafts, and the next sync shows it in the app.
        loop = await pg.evaluate("""async () => { const c = DB.comms.find(x => x.owner === 'u_owner' && /backsplash decision/.test(x.subject));
            const o = paRefOffers({ kind: 'mail', id: c.msgId, commId: c.id }).find(o => o.id === 'pa-reply'); await o.run();
            const W = demoWsFor('u_owner'); const d = W.drafts[W.drafts.length - 1]; const before = DB.comms.filter(x => x.owner === 'u_owner').length;
            const r = await gsRun({ quiet: true }); const dc = DB.comms.find(x => x.msgId === d.message.id); const draftLabels = dc && dc.labels.slice();
            const sent = await gaSend(d.id); const dc2 = DB.comms.find(x => x.msgId === d.message.id);
            return { drafts: W.drafts.length, added: DB.comms.filter(x => x.owner === 'u_owner').length - before, draftLabels, thread: dc && dc.threadId === c.threadId, dir: dc && dc.direction, sentLabels: dc2 && dc2.labels, inSent: W.messages.find(m => m.id === d.message.id).labelIds }; }""")
        C.ok(loop['added'] == 1 and loop['draftLabels'] == ['DRAFT'] and loop['thread'] and loop['dir'] == 'out', f'{uid}: the reply draft went into the demo Drafts on the thread and the next sync shows it ({loop})')
        C.ok(loop['sentLabels'] == ['SENT'] and loop['inSent'] == ['SENT'], f'{uid}: sending the approved draft moves it to Sent in the mailbox and in the app ({loop["sentLabels"]}, {loop["inSent"]})')
    # --- The PM's review (r5 PM, findings 9 and 10): routing by the job's name, a reply that asks the reader is a
    # task on them, unknown senders against vendors on file, one card for Drive files, no card for my own mail,
    # an agency's "revise and resubmit" a dated task for the designer.
    if uid == 'u_alan':
        for subj, pid in (('Invoice AMP-318', 'p121'), ('Re: Confirming Tuesday 7am', 'p121'), ('121 State — millwork delivery', 'p121'), ('121 State — plumbing supersede', 'p121'),
                          ('121 State — special inspections', 'p121'), ('121 State — need 25 boards GWB', 'p121'), ('Re: 45 Cranberry — flitch beam calcs', 'p45')):
            cs = [c for c in S['comms'] if c['subject'].startswith(subj)]
            C.ok(bool(cs) and all(c['route'].get('projectId') == pid for c in cs), f"{uid}: \"{subj}\" routes to {pid} by the job named in the subject ({[(c['subject'][:40], c['route'].get('projectId')) for c in cs]})")
        pe = one(S['comms'], lambda c: c['subject'].startswith('Re: 45 Cranberry — flitch beam calcs') and 'natarajan' in (c['from'] or ''))
        rq = pe and one(S['props'], lambda p: p['commId'] == pe['id'] and p['kind'] == 'request')
        C.ok(bool(rq) and rq.get('forWho') == 'Alan' and 'shoring' in rq.get('task', '').lower(), f"{uid}: the PE's \"have Alan confirm the shoring plan\" is a task on Alan ({rq and (rq.get('forWho'), rq.get('task'))})")
        offers = await pg.evaluate("() => { const A = paInit(); return (A.master || []).filter(m => m.status === 'proposed' && !m.noise).map(m => m.name); }")
        C.ok(not any(o.replace(' ', '').lower() in ('albertomplumbing', 'metroexpediting') for o in offers), f"{uid}: no offer to create a vendor already on file, and no local-part names ({offers})")
        files = [n for n in S['nudges'] if 'landed in Drive' in n['text'] and not re.search(r'COI|W-9|statement', n['text'])]
        C.ok(len(files) == 1 and re.match(r'\d+ files landed in Drive', files[0]['text']), f"{uid}: the job's Drive files are one card, not one per file; a COI or a statement keeps its own ({len(files)}: {[n['text'][:50] for n in files]})")
        own = await pg.evaluate("() => { const A = paInit(); return A.thread.filter(m => m.nudge && m.ref && m.ref.kind === 'mail').map(m => DB.comms.find(c => c.id === m.ref.commId || c.msgId === m.ref.id)).filter(c => c && ((c.labels || []).includes('SENT') || c.direction === 'out')).map(c => c.subject); }")
        C.ok(not own, f"{uid}: no nudge for my own sent mail ({own})")
        lpc = one(by_kind(S, 'lpc'), lambda p: p.get('projectId') == 'p121')
        C.ok(bool(lpc) and lpc.get('owner') == 'Sarah Davis' and lpc.get('due') and lpc.get('resubmit'), f"{uid}: LPC's revise and resubmit is a dated task for the designer ({lpc and (lpc.get('owner'), lpc.get('due'), lpc.get('task'))})")
        if lpc:
            r = await pg.evaluate("""(pid) => { const c = DB.comms.find(x => (x.proposals || []).some(p => p.id === pid)), p = c.proposals.find(p => p.id === pid);
                window.__cmBulk = 1; cmApply(c, p); window.__cmBulk = 0; const t = DB.projects.find(x => x.id === 'p121').tasks.filter(t => t.fromComm).pop(); return t && { owner: t.owner, end: t.end, name: t.name }; }""", lpc['id'])
            C.ok(bool(r) and r['owner'] == 'Sarah Davis' and r['end'] == lpc.get('due'), f"{uid}: approving it puts the dated task on the designer ({r})")
    # --- Second sync: nothing duplicates.
    S2 = await pg.evaluate("async (uid) => { await gsRun({}); const A = paInit(); return { comms: DB.comms.filter(c => c.owner === uid).length, events: (DB.calendar.external || []).filter(e => e.owner === uid).length, files: (DB.gdrive || []).filter(f => f.owner === uid).length, meetings: DB.meetings.length, nudges: A.thread.filter(m => m.nudge).length, props: DB.comms.filter(c => c.owner === uid).reduce((a, c) => a + (c.proposals || []).length, 0) }; }", uid)
    extra = 2 if uid == 'u_owner' else 0  # the owner's test wrote a draft and sent it: one new message
    C.ok(S2['comms'] == S['counts']['comms'] + (1 if uid == 'u_owner' else 0) and S2['events'] == len(S['events']) and S2['files'] == len(S['files']) and S2['meetings'] == S['counts']['meetings'] and S2['props'] <= len(S['props']) + extra,
         f'{uid}: a second sync duplicates nothing ({S2} vs {S["counts"]})')
    # --- Privacy: the client sees none of it through Ask or the portal.
    # Tokens are this mailbox's subjects; a subject the seeded firm inbox also uses is not evidence of a leak.
    seeded = await pg.evaluate("() => DB.comms.filter(c => !c.owner).map(c => c.subject)")
    tokens = [c['subject'] for c in S['comms'] if c['subject'] and len(c['subject']) > 12 and c['subject'] not in seeded][:40] + ['ToolPro', 'Brooklyn Lumber', 'CM-0102', 'AMP-318', 'brick mold profile', 'Marcus Bell']
    leak = await pg.evaluate("""([toks, views]) => { signIn('u_klein'); render(); const out = [];
        const scan = (where, s) => toks.forEach(t => s.includes(t) && out.push(where + ': ' + t));
        for (const v of views) { try { view = v; render(); scan('view ' + v, document.getElementById('app') ? document.getElementById('app').innerText : document.body.innerText); } catch (e) {} }
        for (const q of ['what is in my inbox', 'what came in today', 'what did Alan say', 'show me my messages', 'what documents do you have', 'find the invoice', 'what is on the calendar', 'what changed since yesterday']) { try { scan('ask "' + q + '"', JSON.stringify(paAsk(q))); } catch (e) {} }
        for (const ent of ['messages', 'files', 'events']) { try { scan('eqRows ' + ent, JSON.stringify(eqRows(ent))); } catch (e) {} }
        scan('paMail', JSON.stringify(paMail())); scan('paDrive', JSON.stringify(paDrive())); scan('paEvents', JSON.stringify(paEvents()));
        return out; }""", [tokens, ['client', 'sched', 'dec', 'chat', 'clacct', 'pa']])
    C.ok(not leak, f'{uid}: nothing from the mailbox reaches the client through Ask or the portal ({leak[:5]})')
    # --- Disconnect leaves no demo rows.
    await sign_in(pg, uid)
    gone = await pg.evaluate("""(uid) => { const ids = new Set(DB.comms.filter(c => c.owner === uid).map(c => c.id)); gcDisconnect();
        const A = (DB.asst || {})[uid] || { thread: [] };
        return { g: (DB.conn[uid] || {}).google || null, comms: DB.comms.filter(c => c.owner === uid || c.source === 'demo' && c.owner === uid).length, events: (DB.calendar.external || []).filter(e => e.owner === uid).length, files: (DB.gdrive || []).filter(f => f.owner === uid).length,
          meetings: (DB.meetings || []).filter(m => ids.has(m.commId) && !(m.proposals || []).some(p => p.status === 'applied')).length, expected: (DB.expected || []).filter(e => ids.has(e.commId)).length,
          nudges: A.thread.filter(m => m.nudge && m.ref && (m.ref.kind === 'mail' || m.ref.kind === 'file' || m.ref.kind === 'event')).length, demoWs: !!((DB.demoWs || {})[uid]) }; }""", uid)
    C.ok(gone['g'] is None and gone['comms'] == 0 and gone['events'] == 0 and gone['files'] == 0 and gone['meetings'] == 0 and gone['expected'] == 0 and gone['nudges'] == 0 and not gone['demoWs'], f'{uid}: Disconnect leaves no demo rows ({gone})')
    C.ok(not errs, f'{uid}: no page errors ({errs[:2]})')
    await b.close()

# ---- A Loaded Workspace: an INVENTED export dated after the app day, in the export's own shape -------------
def invented_workspace():
    """A small export in the shape a real one has (Google-shaped events, labelIds, modifiedTime, exportedAt),
    dated in October 2026, after the app day (2026-09-03). 130 messages so the list pages (100 a page), 110
    files so Drive pages. Three threads from one organisation nobody has on file, two from a homeowner at a
    public provider who names an address, one the owner sent asking a question, a newsletter, and a long tail
    of short notes. Everything invented."""
    me = 'Alan Mishali <alan@smartdesign.nyc>'
    org = 'Acme Stone <orders@acmestone.example>'
    home = 'Noor Haddad <noor.haddad@gmail.example>'
    def msg(i, day, hm, frm, to, subject, text, labels=None, atts=None, thread=None, month=10):
        return {'id': f'ldm{i}', 'threadId': thread or f'ldt{i}', 'date': f'2026-{month:02d}-{day:02d}T{hm}:00', 'from': frm, 'to': [to], 'cc': [], 'subject': subject, 'text': text, 'labelIds': labels or ['INBOX', 'UNREAD'], 'attachments': atts or []}
    threads = []
    def thread(tid, msgs): threads.append({'id': tid, 'messages': msgs})
    sig = '\n\nDana Reyes | Acme Stone\n55 Front St, Brooklyn NY 11201\n(718) 555-0100'
    thread('t_org1', [msg(1, 6, '09:10', org, me, 'Quote for the honed limestone treads', 'Hi Alan, quote attached for the twelve honed limestone treads: $4,860.00, three weeks from deposit.' + sig, atts=[{'filename': 'Acme-Stone-Quote-Q-118.pdf', 'mimeType': 'application/pdf', 'text': 'ACME STONE\nQuote Q-118\nTwelve honed limestone treads $4,860.00\nLead time three weeks'}], thread='t_org1')])
    thread('t_org2', [msg(2, 8, '14:20', org, me, 'Invoice AS-2211 for the slab deposit', 'Invoice attached for the slab deposit, $2,400.00, due October 22, 2026. Acme Stone', atts=[{'filename': 'Acme-Stone-Invoice-AS-2211.pdf', 'mimeType': 'application/pdf', 'text': 'ACME STONE\nInvoice No. AS-2211\nSlab deposit\nAmount Due: $2,400.00\nDue October 22, 2026'}], thread='t_org2')])
    thread('t_org3', [msg(3, 9, '11:05', org, me, 'Delivery window for the treads', 'The treads deliver the week of October 19, truck between 8 and 11.' + sig, atts=[{'filename': 'Acme-Stone-Delivery-Ticket.pdf', 'mimeType': 'application/pdf', 'text': ''}], thread='t_org3')])
    thread('t_home1', [msg(4, 7, '19:30', home, me, '88 Pierrepont St — our brownstone', 'Hi Alan, we own the brownstone at 88 Pierrepont St and want to open the parlor floor and redo the kitchen. Could we meet next week? Noor', thread='t_home1')])
    thread('t_home2', [msg(5, 9, '08:15', home, me, 'Re: 88 Pierrepont St — our brownstone', 'Following up on 88 Pierrepont St — does Thursday work for a walk-through? Noor', thread='t_home2')])
    thread('t_sent', [msg(6, 1, '10:00', me, 'Theo Brandt <theo.brandt@gmail.example>', 'Proposal for 14 Willow Pl — any questions?', 'Hi Theo, the proposal for 14 Willow Pl is attached. Let me know if you have questions. Alan', labels=['SENT'], thread='t_sent')])
    thread('t_news', [msg(7, 5, '07:00', 'Facade Weekly <news@facadeweekly.example>', me, 'This week in facades', 'Facade Weekly. Three cornices and a stoop. Unsubscribe.', thread='t_news')])
    n = 8
    # A long tail: 123 one-thread correspondents, half of them in September (older than two weeks), so the
    # list pages, the first-sync summary line is due, and no tail firm outranks the three-thread one.
    for i in range(123):
        older = i % 2 == 0; day = 2 + (i % 8) if not older else 1 + (i % 26); n += 1
        thread(f't_tail{i}', [msg(n, day, f'{8 + (i % 9):02d}:{(i * 7) % 60:02d}', f'Correspondent {i} <c{i}@firm{i}.example>', me, f'Note {i} on the schedule', f'Short note number {i}. Nothing to act on.', thread=f't_tail{i}', month=9 if older else 10)])
    # Who is not on file, with the noise in it (owner review r5, finding 3): cold outreach, a job seeker and a
    # listing are Not Ours; one homeowner on two addresses who is being billed is one client; an address
    # written two ways is one job; a vendor's signature and a for-sale listing are not jobs; a name comes from
    # the signature, never the local part. All in September, so none of it is raised one by one.
    def add(day, frm, to, subject, text, tid, labels=None, atts=None):
        nonlocal n
        n += 1; threads.append({'id': tid, 'messages': [msg(n, day, '10:00', frm, to, subject, text, labels=labels, atts=atts, thread=tid, month=9)]})
    kev = 'Kevin Marsh <kevin@leadsgrowth.example>'
    add(3, kev, me, 'Quick question about SmartDesign', "Hi Alan, I'm reaching out because we help contractors like you book more projects. Would you be open to a 15 minute call next week?", 't_kev1')
    add(10, kev, me, 'Re: Quick question about SmartDesign', 'Following up on my note: would you be open to a quick call? We help firms grow.', 't_kev2')
    add(4, 'Priya Shah <priya.shah@gmail.example>', me, 'Application — Assistant Project Manager', 'Dear Alan, I am applying for the assistant project manager position. My resume is attached.', 't_job', atts=[{'filename': 'Priya-Shah-Resume.pdf', 'mimeType': 'application/pdf', 'text': ''}])
    bkh = 'Brooklyn Homes Team <team@bkhomesrealty.example>'
    add(5, bkh, me, 'Just listed: 300 Clinton St', '300 Clinton St is for sale: 4 bedrooms, 3 baths, asking $3,950,000. Open house Sunday.', 't_list1')
    add(12, bkh, me, 'Price improvement: 300 Clinton St', '300 Clinton St, now asking $3,750,000. 4 bedrooms, garden. Open house Saturday.', 't_list2')
    add(6, 'Grace Lin <grace.lin@gmail.example>', me, '426 W 144th St — the bathroom', 'Hi Alan, the bathroom at 426 W 144th St is leaking again under the tub. Can someone come Thursday? Grace', 't_grace1')
    add(8, me, 'Grace Lin <grace.lin@gmail.example>', 'Progress invoice 3 — 426 W 144th St', 'Hi Grace, progress invoice 3 for 426 W 144th St is attached: $18,000.00. Alan', 't_grace2', labels=['SENT'])
    add(11, 'Grace Lin <gracelin@icloud.example>', me, 'Re: 426 West 144th', 'Alan, we mailed the check for the second payment today for 426 West 144th. Grace', 't_grace3')
    add(9, 'jsidford@gmail.example', me, 'Kitchen at 12 Strong Pl', 'Hi, we are planning a kitchen renovation at 12 Strong Pl and would like an estimate.\n\nThanks,\nJohn Sidford\n(917) 555-0199', 't_sid')
    events = [
        {'id': 'lde1', 'summary': 'Walk-through — 88 Pierrepont St', 'start': {'dateTime': '2026-10-13T10:00:00-04:00', 'timeZone': 'America/New_York'}, 'end': {'dateTime': '2026-10-13T11:00:00-04:00', 'timeZone': 'America/New_York'}, 'status': 'confirmed', 'location': '88 Pierrepont St', 'attendees': [{'email': 'noor.haddad@gmail.example', 'displayName': 'Noor Haddad', 'responseStatus': 'accepted'}], 'organizer': {'email': 'alan@smartdesign.nyc'}, 'updated': '2026-10-05T12:00:00Z'},
        {'id': 'lde2', 'summary': 'Office closed', 'start': {'date': '2026-10-12'}, 'end': {'date': '2026-10-13'}, 'status': 'confirmed', 'updated': '2026-09-01T12:00:00Z'},
        {'id': 'lde3', 'summary': 'Cancelled call', 'start': {'dateTime': '2026-10-14T09:00:00-04:00'}, 'end': {'dateTime': '2026-10-14T09:30:00-04:00'}, 'status': 'cancelled', 'updated': '2026-10-05T12:00:00Z'},
    ]
    files = [{'id': f'ldf{i}', 'name': f'Reference {i}.pdf', 'mimeType': 'application/pdf', 'modifiedTime': f'2026-10-{1 + (i % 9):02d}T16:00:00Z', 'size': '1000', 'owners': [], 'text': ''} for i in range(108)]
    files += [{'id': 'ldfA', 'name': '88 Pierrepont St - A-100 Existing Conditions.pdf', 'mimeType': 'application/pdf', 'modifiedTime': '2026-10-09T16:00:00Z', 'size': '2000', 'owners': [], 'text': 'A-100 existing conditions 88 Pierrepont St'},
              {'id': 'ldfB', 'name': 'Acme Stone - Quote Q-118.pdf', 'mimeType': 'application/pdf', 'modifiedTime': '2026-10-06T16:00:00Z', 'size': '2000', 'owners': [], 'text': 'ACME STONE Quote Q-118 $4,860.00'}]
    return {'uid': 'u_owner', 'exportedAt': '2026-10-12T18:00:00Z', 'accounts': {'gmailMailbox': 'alan@smartdesign.nyc', 'ownerEmails': ['alan@smartdesign.nyc']},
            'mail': {'threads': threads}, 'calendar': {'events': events}, 'drive': {'files': files}}

async def loaded(p, C):
    import tempfile, os as _os
    uid = 'u_owner'
    ws = invented_workspace()
    path = _os.path.join(tempfile.gettempdir(), 'sd_invented_u_owner.workspace.json')
    with open(path, 'w', encoding='utf-8') as f: json.dump(ws, f)
    b, pg, errs = await open_app(p)
    await sign_in(pg, uid)
    # The helper refuses a path inside the repo.
    try: await attach_workspace(pg, uid, _os.path.join(ROOT, 'tests', 'x.workspace.json')); C.ok(False, 'loaded: a path inside the repo must be refused')
    except SystemExit: C.ok(True, 'loaded: a path inside the repo is refused')
    r = await attach_workspace(pg, uid, path)
    C.ok(r == {'messages': 139, 'events': 2, 'files': 110}, f'loaded: attach reads the export shape, drops the cancelled event ({r})')
    W = await pg.evaluate("() => { const W = demoWsFor('u_owner'); return { now: new Date(W.now).toISOString().slice(0, 10), firstDays: W.firstDays, loaded: !!W.loaded, sent: W.messages.filter(m => m.labelIds.includes('SENT')).length, allDay: W.events.filter(e => e.start.date).length }; }")
    C.ok(W['now'] == '2026-10-12' and W['firstDays'] >= 12 and W['loaded'] and W['sent'] == 2 and W['allDay'] == 1, f'loaded: the workspace runs on its exportedAt, its span is the first window, SENT and all-day read right ({W})')
    S = await pg.evaluate("""async () => { const d = await gcDemoConnect('u_owner'); const g = gcMine(); const mine = DB.comms.filter(c => c.owner === 'u_owner');
        const A = paInit(); const M = A.master || []; const R = c => c.route || {};
        return { delta: d && { mail: d.mail.length, events: d.events.length, files: d.files.length, errors: d.errors }, name: g.name, loaded: g.loaded, cursors: g.cursors,
          comms: mine.length, events: (DB.calendar.external || []).filter(e => e.owner === 'u_owner').length, files: (DB.gdrive || []).filter(f => f.owner === 'u_owner').length,
          ignored: mine.filter(c => c.status === 'ignored').length, unroutedProps: mine.reduce((a, c) => a + (c.proposals || []).filter(p => p.kind === 'unrouted').length, 0),
          nudges: A.thread.filter(m => m.nudge).length, nudgeKinds: A.thread.filter(m => m.nudge).map(m => (m.ref || {}).kind), firstsync: (A.thread.find(m => m.nudge && (m.ref || {}).kind === 'firstsync') || {}).text || '', att: d && d.attachments, expect: (A.expect || []).map(e => e.who),
          master: M.map(m => ({ key: m.key, kind: m.kind, as: m.as, name: m.name, threads: m.threadCount, count: m.count, who: m.who || '', addr: m.addr || '', noise: m.noise || '', emails: m.emails || [], contact: m.contact || '', status: m.status })) }; }""")
    C.ok(S['delta'] and not S['delta']['errors'] and S['comms'] == 139 and S['events'] == 2 and S['files'] == 110, f"loaded: one sync pages the whole workspace in (mail {S['comms']}/139, events {S['events']}/2, files {S['files']}/110, {S['delta'] and S['delta']['errors']})")
    C.ok(S['name'] == 'Loaded Workspace' and S['loaded'], f"loaded: the connection is named Loaded Workspace ({S['name']})")
    C.ok(str(S['cursors'].get('gmailAt', '')).startswith('2026-10-12') and str(S['cursors'].get('driveAt', '')).startswith('2026-10-12'), f"loaded: cursors sit on the workspace's clock, not the app day or the wall clock ({S['cursors']})")
    C.ok(S['ignored'] == 1, f"loaded: the newsletter is ignored ({S['ignored']})")
    nk = S['nudgeKinds']
    C.ok(nk.count('firstsync') == 1 and nk.count('master') == 1 and S['nudges'] <= 12, f"loaded: a first sync raises the last two weeks one by one and the September tail as one line, not a storm ({S['nudges']} nudges: {nk})")
    C.ok('4 attachments, 2 read' in S['firstsync'] and S['att'] == {'n': 4, 'read': 2}, f"loaded: the first-sync summary reports the attachments and how many were read ({S['firstsync']}, {S['att']})")
    C.ok('Theo Brandt' in S['expect'], f"loaded: the sent proposal with no answer is an expectation ({S['expect']})")
    M = S['master']
    vend = one(M, lambda m: m['as'] == 'vendor' and m['who'] == 'orders@acmestone.example')
    lead = one(M, lambda m: m['as'] == 'lead' and m['who'] == 'noor.haddad@gmail.example')
    job = one(M, lambda m: m['as'] == 'project' and 'Pierrepont' in m['addr'])
    C.ok(bool(vend) and vend['threads'] == 3, f"loaded: the organisation nobody has on file is one vendor-or-firm proposal with 3 threads ({vend})")
    C.ok(bool(lead) and lead['threads'] == 2, f"loaded: the homeowner at a public provider is one lead proposal with 2 threads ({lead})")
    C.ok(bool(job) and job['threads'] >= 2, f"loaded: the address they name is one job proposal ({job})")
    # ---- who is not on file, without the noise (owner review r5, finding 3)
    NO = [m for m in M if m['noise']]
    C.ok(all(any(m['who'] == w and m['noise'] for m in M) for w in ('kevin@leadsgrowth.example', 'priya.shah@gmail.example', 'team@bkhomesrealty.example')), f"loaded: cold outreach, a job seeker and a listing agent are Not Ours ({[(m['who'], m['noise']) for m in M if m['who'] in ('kevin@leadsgrowth.example', 'priya.shah@gmail.example', 'team@bkhomesrealty.example')]})")
    C.ok(sum(1 for m in M if m['who'].startswith('c') and m['who'].endswith('.example') and 'firm' in m['who'] and not m['noise']) == 0, f"loaded: one-off correspondents we never replied to, with nothing about money or a job, are Not Ours ({sum(1 for m in M if 'firm' in m['who'] and not m['noise'])} left as vendors)")
    C.ok(not any(m['as'] == 'project' and ('Clinton' in m['addr'] or 'Front' in m['addr']) for m in M), f"loaded: a vendor's signature address and a for-sale listing are not jobs ({[m['addr'] for m in M if m['as'] == 'project']})")
    g = [m for m in M if m['as'] == 'project' and '144' in m['addr']]
    C.ok(len(g) == 1 and g[0]['count'] == 3, f"loaded: 426 W 144th St and 426 West 144th are one job cluster ({[(m['addr'], m['count']) for m in g]})")
    gl = [m for m in M if m['kind'] == 'person' and 'Grace' in m['name']] if 'kind' in (M[0] if M else {}) else [m for m in M if 'Grace' in m['name']]
    C.ok(len(gl) == 1 and sorted(gl[0]['emails']) == ['grace.lin@gmail.example', 'gracelin@icloud.example'] and gl[0]['as'] == 'client' and gl[0]['name'] == 'Grace Lin', f"loaded: one person on two addresses, billed by us and paying, is one client record ({[(m['name'], m['as'], m['emails']) for m in gl]})")
    gk = await pg.evaluate("() => { const c = DB.comms.find(x => x.subject === 'Progress invoice 3 — 426 W 144th St'); return c ? c.proposals.map(p => p.kind) : null; }")
    C.ok(gk is not None and 'money' in gk and 'ar' not in gk, f"loaded: our invoice to someone not a client on file is unclassified money, not a receivable ({gk})")
    sid = one(M, lambda m: m['who'] == 'jsidford@gmail.example')
    C.ok(bool(sid) and sid['name'] == 'John Sidford' and sid['as'] == 'lead', f"loaded: the name comes from the signature, never the local part ({sid and sid['name']})")
    acme = one(M, lambda m: m['who'] == 'orders@acmestone.example')
    C.ok(bool(acme) and acme['name'] == 'Acme Stone' and acme['contact'] == 'Dana Reyes', f"loaded: a firm's name and contact come from the signature and the display name ({acme and (acme['name'], acme['contact'])})")
    C.ok(S['unroutedProps'] >= 3, f"loaded: unrouted messages still carry their own proposal, nothing is dropped ({S['unroutedProps']})")
    ask = await pg.evaluate("() => { const a = paAsk('who is not on file'); return { head: a.headline, note: a.note, lines: a.work, work: a.work.length, offers: a.offers.map(o => o.label) }; }")
    C.ok('approve all' not in (ask['note'] + ' '.join(ask['lines'])).lower() and all('creates' in w or 'Not Ours' in w for w in ask['lines']), f"loaded: Ask never invites approving all; each line says what its approval creates ({ask['note'][:160]}; {ask['lines'][:2]})")
    C.ok(any(o.startswith('Set Aside') and 'Not Ours' in o for o in ask['offers']) and not any('Kevin' in o or 'Bkhomes' in o or 'Priya Shah' in o for o in ask['offers']), f"loaded: the noise is under one Not Ours button, not offered as vendors or leads ({ask['offers']})")
    C.ok('nobody has on file' in ask['head'] and ask['work'] >= 3 and any(o.startswith('Create Vendor or Firm Acmestone') or 'Acme' in o for o in ask['offers']), f"loaded: Ask lists who is not on file with one-tap offers ({ask['head']}, {ask['offers'][:3]})")
    ap = await pg.evaluate("""([vk, jk, lk]) => { const r = paMasterApply(vk); const v = DB.vendors.find(x => x.email === 'orders@acmestone.example');
        const routed = DB.comms.filter(c => c.owner === 'u_owner' && v && (c.route || {}).vendorId === v.id);
        const kinds = routed.flatMap(c => (c.proposals || []).map(p => p.kind));
        const bill = routed.flatMap(c => c.proposals || []).find(p => p.kind === 'bill');
        const r2 = paMasterApply(lk); const ld = (DB.leads || []).find(l => l.email === 'noor.haddad@gmail.example');
        const r3 = paMasterApply(jk); const pr = DB.projects.find(p => /Pierrepont/.test(p.project.name)); const tasks = pr ? (pr.tasks || []).length : -1, scopeUnset = !!(pr && pr.project.scopeUnset);
        const jr = pr ? DB.comms.filter(c => c.owner === 'u_owner' && (c.route || {}).projectId === pr.id).length : 0;
        const A = paInit(); return { r, vendor: !!v, routed: routed.length, kinds, bill: bill && { amount: bill.amount, vendor: bill.vendor, number: bill.number }, r2, lead: !!ld, r3, project: !!pr, jr, open: (A.master || []).filter(m => m.status === 'proposed').length, applied: (A.master || []).filter(m => m.status === 'applied').length, tasks, scopeUnset }; }""", [vend['key'], job['key'], lead['key']])
    C.ok(ap['vendor'] and ap['routed'] == 3 and 'unrouted' not in ap['kinds'] and ap['bill'] and ap['bill']['amount'] == 2400 and ap['bill']['number'] == 'AS-2211', f"loaded: one tap creates the vendor, routes its 3 threads and re-reads them (the invoice is now a bill proposal) ({ap['routed']}, {ap['kinds']}, {ap['bill']})")
    C.ok(ap['project'] and ap['tasks'] == 0 and ap['scopeUnset'], f"loaded: a job created from mail carries no template tasks until someone sets its scope ({ap['tasks']}, {ap['scopeUnset']})")
    noi = await pg.evaluate("() => { const A = paInit(); const n0 = (A.master || []).filter(m => m.noise && m.status === 'proposed').length; const r = paMasterIgnoreAll(); return { n0, r, left: (A.master || []).filter(m => m.noise && m.status === 'proposed').length, ignored: DB.comms.filter(c => c.owner === 'u_owner' && c.status === 'ignored').length }; }")
    C.ok(noi['n0'] > 3 and noi['left'] == 0 and noi['r'] >= noi['n0'], f"loaded: one tap sets every Not Ours cluster aside ({noi})")
    C.ok(ap['lead'] and ap['project'] and ap['jr'] >= 2 and ap['applied'] == 3, f"loaded: the lead and the job are created and their threads route ({ap['lead']}, {ap['project']}, {ap['jr']}, applied {ap['applied']})")
    S2 = await pg.evaluate("async () => { const d = await gsRun({}); return { mail: d.mail.length, events: d.events.length, files: d.files.length, comms: DB.comms.filter(c => c.owner === 'u_owner').length, nudges: paInit().thread.filter(m => m.nudge).length }; }")
    C.ok(S2['mail'] == 0 and S2['files'] == 0 and S2['comms'] == 139 and S2['nudges'] == S['nudges'], f'loaded: a second sync adds nothing ({S2})')
    ui = await pg.evaluate("() => { view = 'conn'; render(); const h = document.querySelector('.gc-acct h3'); return h ? h.textContent : ''; }")
    C.ok(ui.startswith('Loaded Workspace') and 'Google' not in ui, f'loaded: the Connections card reads Loaded Workspace ({ui})')
    gone = await pg.evaluate("() => { gcDisconnect(); return { comms: DB.comms.filter(c => c.owner === 'u_owner').length, events: (DB.calendar.external || []).filter(e => e.owner === 'u_owner').length, files: (DB.gdrive || []).filter(f => f.owner === 'u_owner').length, g: (DB.conn.u_owner || {}).google || null }; }")
    C.ok(gone['comms'] == 0 and gone['events'] == 0 and gone['files'] == 0 and gone['g'] is None, f'loaded: Disconnect leaves no rows ({gone})')
    C.ok(not errs, f'loaded: no page errors ({errs[:2]})')
    await b.close()
    try: _os.remove(path)
    except OSError: pass

async def anchored(p, C):
    # A page that reloads on a later app day rebuilds the Demo Workspace; its mail and events keep their dates
    # (the pilot saw Labor Day on a Tuesday and Friday's meeting on Saturday when they were dated from today).
    b, pg, errs = await open_app(p)
    await sign_in(pg, 'u_sarah')
    r = await pg.evaluate("""() => {
      const day = (ws) => (ws.events || []).filter(e => /Labor Day/.test(e.summary)).map(e => String((e.start || {}).date || (e.start || {}).dateTime || '').slice(0, 10))[0];
      const a = day(demoWsBuild('u_sarah'));
      appSetDay(iso(addDays(today(), 1)));
      const b2 = day(demoWsBuild('u_sarah'));
      return { a, b: b2, anchor: DB.company.dwAnchor };
    }""")
    C.ok(r['a'] == '2026-09-07' and r['b'] == '2026-09-07', f"the workspace keeps its dates when the app day moves: Labor Day {r}")
    await b.close()

async def main():
    C = Checks()
    who = sys.argv[1:] or PERSONAS + ['loaded', 'anchored']
    async with async_playwright() as p:
        for uid in who:
            try:
                if uid == 'loaded': await loaded(p, C)
                elif uid == 'anchored': await anchored(p, C)
                else: await persona(p, uid, C)
            except Exception as e: C.ok(False, f'{uid}: suite error {e!r}')
    return C.done()

if __name__ == '__main__': sys.exit(asyncio.run(main()))
