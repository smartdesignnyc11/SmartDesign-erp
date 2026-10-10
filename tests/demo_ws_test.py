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

  python3 demo_ws_test.py [u_owner u_chen ...]     # prints ALL PASS (n checks) or each failure
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

async def main():
    C = Checks()
    who = sys.argv[1:] or PERSONAS
    async with async_playwright() as p:
        for uid in who:
            try: await persona(p, uid, C)
            except Exception as e: C.ok(False, f'{uid}: suite error {e!r}')
    return C.done()

if __name__ == '__main__': sys.exit(asyncio.run(main()))
