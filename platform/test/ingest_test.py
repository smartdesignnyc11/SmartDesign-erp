"""What the hosted watcher leaves in a person's inbox is filed by the app exactly as a sync run would: mail through
routing and proposals, calendar changes (a cancellation removes), Drive files with their job route, nothing twice.
Runs on the local build. Run: python3 platform/test/ingest_test.py"""
import asyncio, base64, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'tests'))
from harness import *
b64 = lambda s: base64.urlsafe_b64encode(s.encode()).decode().rstrip('=')
def mail(i, subj, frm, body):
    return {'id': 'srv' + i, 'threadId': 'th' + i, 'labelIds': ['INBOX', 'UNREAD'], 'internalDate': '1788000000000',
            'payload': {'mimeType': 'text/plain', 'headers': [{'name': 'Subject', 'value': subj}, {'name': 'From', 'value': frm},
                        {'name': 'To', 'value': 'Alan <alan@smartdesign.nyc>'}, {'name': 'Date', 'value': 'Wed, 2 Sep 2026 14:00:00 -0400'}],
                        'body': {'data': b64(body)}}}
BOX = {'gmail': [mail('1', 'Windows for 121 State: revised quote', 'Ray Pella <ray@pellawindows.example>', 'Revised quote for the 121 State windows attached, $14,200, lead time 6 weeks.'),
                 mail('2', 'Lunch Friday?', 'Friend <friend@example.com>', 'Are you free?'),
                 mail('3', 'Water in the basement at 121 State?', 'Neighbor <n@example.com>', 'Is someone coming to look at it today?')],
       'cal': [{'id': 'ev9', 'summary': 'Inspection 121 State', 'start': {'dateTime': '2026-09-08T10:00:00-04:00'}, 'end': {'dateTime': '2026-09-08T11:00:00-04:00'}}],
       'drive': [{'id': 'dr9', 'name': '121 State - framing plan rev C.pdf', 'mimeType': 'application/pdf', 'modifiedTime': '2026-09-02T12:00:00Z'}]}
async def main():
    c = Checks()
    async with async_playwright() as p:
        b, pg, errs = await open_app(p)
        await sign_in(pg, 'u_owner')
        before = await pg.evaluate("(DB.comms||[]).length")
        n = await pg.evaluate("box => gsIngestServer(box)", BOX)
        c.ok(n == 5, f'five things filed ({n})')
        r = await pg.evaluate("""() => { const m = DB.comms.find(x => x.msgId === 'srv1');
            return {owner: m && m.owner, source: m && m.source, unread: m && m.unread, subject: m && m.subject, text: m && m.text, link: m && m.links && m.links[0] && m.links[0].url,
                    routed: !!(m && (m.projectId || m.route)), proposals: m && (m.proposals || []).length, total: DB.comms.length}; }""")
        c.ok(r['owner'] == 'u_owner' and r['source'] == 'google' and r['unread'], f"the mail is the owner's, from Google, unread: {r}")
        c.ok('14,200' in (r['text'] or '') and r['subject'].startswith('Windows'), 'subject and body read from the raw message')
        c.ok((r['link'] or '').startswith('https://mail.google.com/'), 'it links back to Gmail')
        c.ok(r['routed'], 'the vendor mail went through routing, as a sync run would')
        c.ok(r['total'] == before + 3, f'three new messages ({r["total"] - before})')
        nudges = await pg.evaluate("paInit().thread.filter(m => m.nudge && m.ref && m.ref.kind === 'mail').map(m => m.ref.id)")
        c.ok('srv1' in nudges, f"the vendor's quote reached the assistant's conversation as a nudge: {nudges}")
        why = await pg.evaluate("paInit().thread.filter(m => m.nudge && m.ref && m.ref.kind === 'mail').every(m => (m.note || '').length > 10)")
        c.ok(why, 'every nudge says why it was brought')
        c.ok('srv2' not in nudges, 'a personal question from someone not on file stays in the inbox')
        c.ok('srv3' in nudges, 'someone not on file who names a job is brought')
        again = await pg.evaluate("box => gsIngestServer(box)", BOX)
        c.ok(await pg.evaluate("paInit().thread.filter(m => m.ref && m.ref.id === 'srv1').length") == 1, 'filing twice does not nudge twice')
        c.ok(await pg.evaluate("DB.comms.filter(x => x.msgId === 'srv1').length") == 1, 'filing the same inbox twice adds no mail twice')
        ev = await pg.evaluate("(DB.calendar.external||[]).find(e => e.id === 'g_ev9')")
        c.ok(ev and ev['owner'] == 'u_owner' and ev['title'] == 'Inspection 121 State', 'the calendar change is filed')
        await pg.evaluate("gsIngestServer({cal: [{id: 'ev9', status: 'cancelled'}]})")
        c.ok(not await pg.evaluate("(DB.calendar.external||[]).some(e => e.id === 'g_ev9')"), 'a cancellation removes it')
        f = await pg.evaluate("(DB.gdrive||[]).find(x => x.id === 'g_dr9')")
        c.ok(f and f['owner'] == 'u_owner' and f['source'] == 'google' and 'route' in f, 'the Drive file is filed with its route')
        BR = [{'key': 'bn:abc', 'title': 'Order windows twelve weeks ahead on landmark jobs', 'because': 'Windows landed late on 121 State.', 'value': 'Schedule', 'evidence': ['PO-12 expected 2026-08-27'], 'kind': 'process', 'night': '2026-09-03'}]
        nb = await pg.evaluate("b => gsIngestServer({brain: b})", BR)
        ch = await pg.evaluate("DB.changes.filter(c => c.key === 'bn:abc')")
        c.ok(nb == 1 and len(ch) == 1 and ch[0]['status'] == 'draft' and ch[0]['kind'] == 'code' and 'Windows landed late' in ch[0]['why'], "the Brain's proposal is a drafted change for the owner to approve")
        c.ok(await pg.evaluate("paInit().thread.some(m => m.ref && m.ref.kind === 'brain')"), 'and the assistant says so once')
        await pg.evaluate("b => gsIngestServer({brain: b})", BR)
        c.ok(await pg.evaluate("DB.changes.filter(c => c.key === 'bn:abc').length") == 1, 'the same proposal twice is filed once')
        c.ok(not errs, f'no page errors {errs[:3]}')
        await b.close()
    return c.done()
sys.exit(asyncio.run(main()))
