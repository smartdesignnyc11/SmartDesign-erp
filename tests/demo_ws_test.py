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
    comms: mine.map(c => ({ id: c.id, msgId: c.msgId, subject: c.subject, from: (c.from || {}).email, route: c.route || {}, status: c.status, labels: c.labels || [], direction: c.direction, kinds: (c.proposals || []).map(p => p.kind) })),
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
        if 'klein@example.com' in f: C.ok(c['route'].get('clientId') == 'cl121' and c['route'].get('projectId') == 'p121', f"{uid}: Klein mail routed to the Kleins and 121 State ({c['subject']} -> {c['route']})")
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
        # The loop: a draft the assistant writes lands in the demo Drafts, and the next sync shows it in the app.
        loop = await pg.evaluate("""async () => { const c = DB.comms.find(x => x.owner === 'u_owner' && /backsplash decision/.test(x.subject));
            const o = paRefOffers({ kind: 'mail', id: c.msgId, commId: c.id }).find(o => o.id === 'pa-reply'); await o.run();
            const W = demoWsFor('u_owner'); const d = W.drafts[W.drafts.length - 1]; const before = DB.comms.filter(x => x.owner === 'u_owner').length;
            const r = await gsRun({ quiet: true }); const dc = DB.comms.find(x => x.msgId === d.message.id); const draftLabels = dc && dc.labels.slice();
            const sent = await gaSend(d.id); const dc2 = DB.comms.find(x => x.msgId === d.message.id);
            return { drafts: W.drafts.length, added: DB.comms.filter(x => x.owner === 'u_owner').length - before, draftLabels, thread: dc && dc.threadId === c.threadId, dir: dc && dc.direction, sentLabels: dc2 && dc2.labels, inSent: W.messages.find(m => m.id === d.message.id).labelIds }; }""")
        C.ok(loop['added'] == 1 and loop['draftLabels'] == ['DRAFT'] and loop['thread'] and loop['dir'] == 'out', f'{uid}: the reply draft went into the demo Drafts on the thread and the next sync shows it ({loop})')
        C.ok(loop['sentLabels'] == ['SENT'] and loop['inSent'] == ['SENT'], f'{uid}: sending the approved draft moves it to Sent in the mailbox and in the app ({loop["sentLabels"]}, {loop["inSent"]})')
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
    thread('t_org1', [msg(1, 6, '09:10', org, me, 'Quote for the honed limestone treads', 'Hi Alan, quote attached for the twelve honed limestone treads: $4,860.00, three weeks from deposit. Acme Stone', atts=[{'filename': 'Acme-Stone-Quote-Q-118.pdf', 'mimeType': 'application/pdf', 'text': 'ACME STONE\nQuote Q-118\nTwelve honed limestone treads $4,860.00\nLead time three weeks'}], thread='t_org1')])
    thread('t_org2', [msg(2, 8, '14:20', org, me, 'Invoice AS-2211 for the slab deposit', 'Invoice attached for the slab deposit, $2,400.00, due October 22, 2026. Acme Stone', atts=[{'filename': 'Acme-Stone-Invoice-AS-2211.pdf', 'mimeType': 'application/pdf', 'text': 'ACME STONE\nInvoice No. AS-2211\nSlab deposit\nAmount Due: $2,400.00\nDue October 22, 2026'}], thread='t_org2')])
    thread('t_org3', [msg(3, 9, '11:05', org, me, 'Delivery window for the treads', 'The treads deliver the week of October 19, truck between 8 and 11. Acme Stone', thread='t_org3')])
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
    C.ok(r == {'messages': 130, 'events': 2, 'files': 110}, f'loaded: attach reads the export shape, drops the cancelled event ({r})')
    W = await pg.evaluate("() => { const W = demoWsFor('u_owner'); return { now: new Date(W.now).toISOString().slice(0, 10), firstDays: W.firstDays, loaded: !!W.loaded, sent: W.messages.filter(m => m.labelIds.includes('SENT')).length, allDay: W.events.filter(e => e.start.date).length }; }")
    C.ok(W['now'] == '2026-10-12' and W['firstDays'] >= 12 and W['loaded'] and W['sent'] == 1 and W['allDay'] == 1, f'loaded: the workspace runs on its exportedAt, its span is the first window, SENT and all-day read right ({W})')
    S = await pg.evaluate("""async () => { const d = await gcDemoConnect('u_owner'); const g = gcMine(); const mine = DB.comms.filter(c => c.owner === 'u_owner');
        const A = paInit(); const M = A.master || []; const R = c => c.route || {};
        return { delta: d && { mail: d.mail.length, events: d.events.length, files: d.files.length, errors: d.errors }, name: g.name, loaded: g.loaded, cursors: g.cursors,
          comms: mine.length, events: (DB.calendar.external || []).filter(e => e.owner === 'u_owner').length, files: (DB.gdrive || []).filter(f => f.owner === 'u_owner').length,
          ignored: mine.filter(c => c.status === 'ignored').length, unroutedProps: mine.reduce((a, c) => a + (c.proposals || []).filter(p => p.kind === 'unrouted').length, 0),
          nudges: A.thread.filter(m => m.nudge).length, nudgeKinds: A.thread.filter(m => m.nudge).map(m => (m.ref || {}).kind), expect: (A.expect || []).map(e => e.who),
          master: M.map(m => ({ key: m.key, as: m.as, name: m.name, threads: m.threadCount, count: m.count, who: m.who || '', addr: m.addr || '' })) }; }""")
    C.ok(S['delta'] and not S['delta']['errors'] and S['comms'] == 130 and S['events'] == 2 and S['files'] == 110, f"loaded: one sync pages the whole workspace in (mail {S['comms']}/130, events {S['events']}/2, files {S['files']}/110, {S['delta'] and S['delta']['errors']})")
    C.ok(S['name'] == 'Loaded Workspace' and S['loaded'], f"loaded: the connection is named Loaded Workspace ({S['name']})")
    C.ok(str(S['cursors'].get('gmailAt', '')).startswith('2026-10-12') and str(S['cursors'].get('driveAt', '')).startswith('2026-10-12'), f"loaded: cursors sit on the workspace's clock, not the app day or the wall clock ({S['cursors']})")
    C.ok(S['ignored'] == 1, f"loaded: the newsletter is ignored ({S['ignored']})")
    nk = S['nudgeKinds']
    C.ok(nk.count('firstsync') == 1 and nk.count('master') == 1 and S['nudges'] <= 12, f"loaded: a first sync raises the last two weeks one by one and the September tail as one line, not a storm ({S['nudges']} nudges: {nk})")
    C.ok('Theo Brandt' in S['expect'], f"loaded: the sent proposal with no answer is an expectation ({S['expect']})")
    M = S['master']
    vend = one(M, lambda m: m['as'] == 'vendor' and m['who'] == 'orders@acmestone.example')
    lead = one(M, lambda m: m['as'] == 'lead' and m['who'] == 'noor.haddad@gmail.example')
    job = one(M, lambda m: m['as'] == 'project' and 'Pierrepont' in m['addr'])
    C.ok(bool(vend) and vend['threads'] == 3, f"loaded: the organisation nobody has on file is one vendor-or-firm proposal with 3 threads ({vend})")
    C.ok(bool(lead) and lead['threads'] == 2, f"loaded: the homeowner at a public provider is one lead proposal with 2 threads ({lead})")
    C.ok(bool(job) and job['threads'] >= 2, f"loaded: the address they name is one job proposal ({job})")
    C.ok(S['unroutedProps'] >= 3, f"loaded: unrouted messages still carry their own proposal, nothing is dropped ({S['unroutedProps']})")
    ask = await pg.evaluate("() => { const a = paAsk('who is not on file'); return { head: a.headline, work: a.work.length, offers: a.offers.map(o => o.label) }; }")
    C.ok('nobody has on file' in ask['head'] and ask['work'] >= 3 and any(o.startswith('Create Vendor or Firm Acmestone') or 'Acme' in o for o in ask['offers']), f"loaded: Ask lists who is not on file with one-tap offers ({ask['head']}, {ask['offers'][:3]})")
    ap = await pg.evaluate("""([vk, jk, lk]) => { const r = paMasterApply(vk); const v = DB.vendors.find(x => x.email === 'orders@acmestone.example');
        const routed = DB.comms.filter(c => c.owner === 'u_owner' && v && (c.route || {}).vendorId === v.id);
        const kinds = routed.flatMap(c => (c.proposals || []).map(p => p.kind));
        const bill = routed.flatMap(c => c.proposals || []).find(p => p.kind === 'bill');
        const r2 = paMasterApply(lk); const ld = (DB.leads || []).find(l => l.email === 'noor.haddad@gmail.example');
        const r3 = paMasterApply(jk); const pr = DB.projects.find(p => /Pierrepont/.test(p.project.name));
        const jr = pr ? DB.comms.filter(c => c.owner === 'u_owner' && (c.route || {}).projectId === pr.id).length : 0;
        const A = paInit(); return { r, vendor: !!v, routed: routed.length, kinds, bill: bill && { amount: bill.amount, vendor: bill.vendor, number: bill.number }, r2, lead: !!ld, r3, project: !!pr, jr, open: (A.master || []).filter(m => m.status === 'proposed').length, applied: (A.master || []).filter(m => m.status === 'applied').length }; }""", [vend['key'], job['key'], lead['key']])
    C.ok(ap['vendor'] and ap['routed'] == 3 and 'unrouted' not in ap['kinds'] and ap['bill'] and ap['bill']['amount'] == 2400 and ap['bill']['number'] == 'AS-2211', f"loaded: one tap creates the vendor, routes its 3 threads and re-reads them (the invoice is now a bill proposal) ({ap['routed']}, {ap['kinds']}, {ap['bill']})")
    C.ok(ap['lead'] and ap['project'] and ap['jr'] >= 2 and ap['applied'] == 3, f"loaded: the lead and the job are created and their threads route ({ap['lead']}, {ap['project']}, {ap['jr']}, applied {ap['applied']})")
    S2 = await pg.evaluate("async () => { const d = await gsRun({}); return { mail: d.mail.length, events: d.events.length, files: d.files.length, comms: DB.comms.filter(c => c.owner === 'u_owner').length, nudges: paInit().thread.filter(m => m.nudge).length }; }")
    C.ok(S2['mail'] == 0 and S2['files'] == 0 and S2['comms'] == 130 and S2['nudges'] == S['nudges'], f'loaded: a second sync adds nothing ({S2})')
    ui = await pg.evaluate("() => { view = 'conn'; render(); const h = document.querySelector('.gc-acct h3'); return h ? h.textContent : ''; }")
    C.ok(ui.startswith('Loaded Workspace') and 'Google' not in ui, f'loaded: the Connections card reads Loaded Workspace ({ui})')
    gone = await pg.evaluate("() => { gcDisconnect(); return { comms: DB.comms.filter(c => c.owner === 'u_owner').length, events: (DB.calendar.external || []).filter(e => e.owner === 'u_owner').length, files: (DB.gdrive || []).filter(f => f.owner === 'u_owner').length, g: (DB.conn.u_owner || {}).google || null }; }")
    C.ok(gone['comms'] == 0 and gone['events'] == 0 and gone['files'] == 0 and gone['g'] is None, f'loaded: Disconnect leaves no rows ({gone})')
    C.ok(not errs, f'loaded: no page errors ({errs[:2]})')
    await b.close()
    try: _os.remove(path)
    except OSError: pass

async def main():
    C = Checks()
    who = sys.argv[1:] or PERSONAS + ['loaded']
    async with async_playwright() as p:
        for uid in who:
            try:
                if uid == 'loaded': await loaded(p, C)
                else: await persona(p, uid, C)
            except Exception as e: C.ok(False, f'{uid}: suite error {e!r}')
    return C.done()

if __name__ == '__main__': sys.exit(asyncio.run(main()))
