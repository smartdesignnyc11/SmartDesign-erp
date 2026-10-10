"""ops (round-5 PM review, findings 1-5, 8, 11-14): the ops thread on 121 State Street as the PM would click it.

Each section starts from a fresh boot. Real buttons where the finding is about a click; helpers for set-up.

  python3 ops_test.py                 all sections
  python3 ops_test.py sched co        only the named sections
                                      (sched, co, fieldco, noshow, insp, lenox, labels, polish)

sched   One schedule truth. After Pull In, the forecast tile, the Changes note and the publish preview read the
        same live history: the give-back closes on pull-in and stays closed when the PM leaves the approved CO
        (leaving used to revert the record to a snapshot and reopen it); a second Pull In is impossible (button
        gone, function refuses); the cause named is the live one (the no-show +5 after the give-back is taken);
        a publish after a second Pull In attempt sends the same finish as the first.
co      A client's approved overage (+$1,850, 2nd floor bathroom finishes) becomes a change order from the task:
        Raise Change Order opens the CO editor prefilled with the chosen option's line and amount; a decided
        decision keeps Raise Change Order until a CO references it; the task closes when the CO is sent; Ask
        "what still needs a change order" lists it until then.
fieldco A CO from a field issue: the client memo is the item's title and note; the PM's answer to the foreman
        stays in Internal Notes and never prints on the approval dialog, the email or the PDF; the item's photos
        attach as exhibits shared with the client and the CO editor shows them.
noshow  Answering a sub no-show offers, inline, Slip N Days (reason no-show, into the history), Rebook + Confirm
        by Text the Day Before (a dated reminder and an outbound draft), Chase the Sub; the brain proposes the
        "confirm every sub the day before" rule from it, as a proposed lesson with a trigger.
insp    Book on an inspection holds the window on the calendar, tells the foreman and the licensed trade, closes
        the open "Book Rough Inspection" task; a DOB NOW notice in mail proposes the booking with the window.
lenox   206 Lenox is its own small job: the template no longer copies another job's decisions, materials,
        submittals or field items; a boot migration strips clone copies; PM Home, Approvals, Purchasing and Ask
        show none of 121 State's items under 206 Lenox.
labels  One label, one number: Home "Jobs With Late Items" vs Projects "Finish Dates Late" (different rules,
        different names, each stating its rule); Home "Site Questions" equals Approvals "Site Questions"; Pulse
        tiles open their list; one person, one name among assignees; "The Lindqvists" once in New Task > For.
polish  Leaving an approved read-only CO asks nothing; toasts and the portal finish headline cut on a word; the
        foreman's card says "Proceed as an extra" once; the first Acknowledge click works; Chen's Home link for
        a field question lands on the question; "Sent" stamps sit in site hours on the demo clock; the daily log
        record shows the photos it lists and takes the PM's acknowledgement; the committed-deliverable-dates
        rule proposes only where a deliverable is undated; Workload counts the approvals a person holds."""
import asyncio, re, sys
from harness import *
from truthpct_test import THREAD

ONLY = set(sys.argv[1:])
want = lambda s: not ONLY or s in ONLY
J121 = "DB.projects.find(p => /121 State/.test(p.project.name))"
KLEIN = "DB.clients.find(x => /Klein/.test(x.name))"


async def fresh(p, uid='u_alan', phone=False):
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, uid)
    return b, pg, errs


async def text(pg, sel='.view.on'):
    return await pg.evaluate("s => { const e = document.querySelector(s); return e ? e.innerText : '' }", sel)


async def modal(pg):
    return await pg.evaluate("() => { const m = document.getElementById('mbm'); return m && getComputedStyle(m).display !== 'none' && m.innerText.trim() ? m.innerText : '' }")


async def toast(pg):
    return await pg.evaluate("() => (document.getElementById('toast') || {}).innerText || ''")


async def ask(pg, q):
    return await pg.evaluate("""async q => { let a = paAsk(q); if (a && a.then) a = await a;
        return [a.headline || '', a.note || '', (a.work || []).map(w => typeof w === 'string' ? w : (w.t || w.text || JSON.stringify(w))).join('\\n')].join('\\n') }""", q)


SLIP = """([id, n, key]) => { const p = S, t = p.tasks.find(x => x.id === id), was = { start: t.start, end: t.end };
    t.end = addWork(t.end, n, t.weekendOk); t._moveReason = opsReasonLabel(key); t._moveReasonKey = key;
    pushDependents(t.id, []); recordMove(t, was, 'edit'); save(); render(); return t.end }"""


async def publish(pg, c, note, tag):
    """Schedule > Changes > Publish to Client > note > Publish, by the real buttons. Returns the published finish."""
    await pg.evaluate("() => { view = 'sched'; schedView = 'changes'; render() }"); await pg.wait_for_timeout(300)
    c.ok(await pg.locator('#ops-publish').count() == 1, f'{tag}: no Publish to Client button on Changes')
    await pg.click('#ops-publish'); await pg.wait_for_timeout(300)
    dlg = await modal(pg)
    await pg.fill('#mbm [data-f="note"]', note)
    await pg.click('#mbm-ok'); await pg.wait_for_timeout(400)
    fin = await pg.evaluate("() => (S.published || {}).finish || ''")
    return fin, dlg


async def sec_sched(p, c):
    b, pg, errs = await fresh(p)
    r = await pg.evaluate(THREAD)
    c.ok(r['give'] and r['give']['days'] == 4, f"R2 gives back 4 working days on Framing: {r}")
    # the PM pulls in from the approved R2's own record (Billing > Change Orders > the record)
    await pg.evaluate(f"n => {{ const c = {KLEIN}; const d = c.changeOrders.find(x => x.number === n); flowGo.doc(c, 'co', d)() }}", r['d2'])
    await pg.wait_for_timeout(400)
    c.ok(await pg.locator('.view.on [data-czpull]').count() == 1, 'the approved R2 record offers Pull In 4 Days')
    await pg.click('.view.on [data-czpull]'); await pg.wait_for_timeout(300)
    c.ok((await modal(pg)).lower().startswith('pull in'), f'Pull In opens its dialog: {(await modal(pg))[:60]!r}')
    await pg.click('#mbm-ok'); await pg.wait_for_timeout(400)
    st = await pg.evaluate(f"() => {{ const c = {KLEIN}, d = c.changeOrders.find(x => x.czGive); return {{ open: d.czGive.open, pulled: d.czGive.pulled, end: S.tasks.find(t => t.id === 'frame').end, live: typeof czGiveOpen === 'function' ? czGiveOpen(c, d) : null }} }}")
    c.ok(st['open'] is False and st['end'] == '2026-09-10', f'after Pull In the give-back is closed and Framing ends 9/10: {st}')
    # leaving the approved, read-only record by the rail asks nothing and changes nothing (it used to prompt
    # "Save changes?" and, through the modal's first answer, revert the record to its snapshot, reopening the give-back)
    await pg.click('#nav-groups button:has-text("Projects")'); await pg.wait_for_timeout(400)
    m = await modal(pg)
    c.ok('save changes' not in m.lower() and 'confirm' not in m.lower(), f'leaving the approved CO asks nothing: {m[:80]!r}')
    st = await pg.evaluate(f"() => {{ const c = {KLEIN}, d = c.changeOrders.find(x => x.czGive); return {{ open: d.czGive.open, pulled: d.czGive.pulled, end: S.tasks.find(t => t.id === 'frame').end, live: typeof czGiveOpen === 'function' ? czGiveOpen(c, d) : null }} }}")
    c.ok(st['open'] is False and st['live'] is False and st['end'] == '2026-09-10', f'after leaving the record the give-back stays closed: {st}')
    # the three readers agree: no give-back note on Changes, no Pull In on the forecast card or the Today tile
    await pg.evaluate("() => { view = 'sched'; schedView = 'changes'; render() }"); await pg.wait_for_timeout(400)
    note = await pg.evaluate("() => [...document.querySelectorAll('.cz-givenote')].map(x => x.innerText)")
    card = await pg.evaluate("() => { const t = document.querySelector('#track-cards .ops-fc'); return t ? t.innerText.replace(/\\n/g, ' | ') : '' }")
    c.ok(not note, f'the Changes list carries no give-back note after Pull In: {note}')
    c.ok('Pull In' not in card, f'the forecast card offers no Pull In after Pull In: {card!r}')
    c.ok(await pg.locator('[data-czpull]').count() == 0, 'no Pull In button anywhere on Schedule after Pull In')
    await go(pg, 'dash'); await pg.wait_for_timeout(300)
    tile = await pg.evaluate("() => { const t = document.querySelector('#kpis .gl[data-gl=\"sched\"]'); return t ? t.innerText.replace(/\\n/g, ' | ') : '' }")
    c.ok('Pull In' not in tile and 'still on' not in tile, f'the Today forecast tile reads the live history: {tile!r}')
    # the no-show slip: +5 on Framing, reason no-show
    end = await pg.evaluate(SLIP, ['frame', 5, 'noshow'])
    why = await pg.evaluate("() => tpForecastWhy(S)")
    c.ok(why['late'] == 5 and re.search(r'no-show|could not be on site', why['text'], re.I) and 'Framing' in why['text'] and '+5' in why['text'],
         f"the forecast names the live cause (the no-show +5 on Framing): {why['text']!r}")
    await go(pg, 'dash'); await pg.wait_for_timeout(300)
    tile = await pg.evaluate("() => { const t = document.querySelector('#kpis .gl[data-gl=\"sched\"]'); return t ? t.innerText.replace(/\\n/g, ' | ') : '' }")
    await go(pg, 'sched'); await pg.wait_for_timeout(300)
    card = await pg.evaluate("() => { const t = document.querySelector('#track-cards .ops-fc'); return t ? t.innerText.replace(/\\n/g, ' | ') : '' }")
    c.ok(why['text'] in tile and why['text'] in card, f"the tile and the card read the same cause: tile {tile!r} card {card!r}")
    # a second Pull In is impossible: the button is gone everywhere and the function refuses
    sec = await pg.evaluate(f"""() => {{ const c = {KLEIN}, d = c.changeOrders.find(x => x.czGive); const end0 = S.tasks.find(t => t.id === 'frame').end;
        const ok = czDoPull(c, d, 'again'); czGiveBackDialog(c, d);
        const m = document.getElementById('mbm'); const open = m && getComputedStyle(m).display !== 'none' ? m.innerText : '';
        return {{ ok, end0, end1: S.tasks.find(t => t.id === 'frame').end, dialog: open, btns: document.querySelectorAll('[data-czpull]').length,
                 pulls: (S.tasks.find(t => t.id === 'frame').history || []).filter(h => h.coId === d.id && h.days < 0).length }} }}""")
    c.ok(sec['ok'] is False and sec['end0'] == sec['end1'] and sec['pulls'] == 1, f'a second Pull In pulls nothing: {sec}')
    c.ok(not sec['dialog'].lower().startswith('pull in') and sec['btns'] == 0, f'a second Pull In has no dialog and no button: {sec["dialog"][:60]!r}, {sec["btns"]} buttons')
    await pg.evaluate("() => { try { mbCloseModal() } catch (e) {} }")
    # publish: the preview splits the cause the same way, the client gets the forecast finish
    fin1, dlg = await publish(pg, c, 'Framing slipped a week: the restoration sub did not show.', 'publish 1')
    sc = await pg.evaluate("() => czPlan().sc")
    c.ok(fin1 == sc, f'the first publish sends the forecast finish {sc}: published {fin1}')
    c.ok(re.search(r'could not be on site', dlg) and '+5' in dlg, f'the publish preview names the no-show as the cause: {dlg[:400]!r}')
    c.ok(not re.search(r'given back', dlg, re.I), f'the publish preview carries no stale give-back: {dlg[:300]!r}')
    # a second Pull In attempt, then a second publish: the same finish
    again = await pg.evaluate(f"() => {{ const c = {KLEIN}, d = c.changeOrders.find(x => x.czGive); return czDoPull(c, d, 'again') }}")
    c.ok(again is False, 'the second Pull In attempt before the second publish is refused')
    fin2, _ = await publish(pg, c, 'No change this week.', 'publish 2')
    c.ok(fin2 == fin1, f'the second publish sends the same finish: {fin1} then {fin2}')
    await sign_in(pg, 'u_klein'); await go(pg, 'sched'); await pg.wait_for_timeout(300)
    t = await text(pg)
    want = await pg.evaluate("f => fmtL(f)", fin1)
    c.ok(want in t, f'the client reads finish {want}')
    c.ok(not errs, f'sched: page errors {errs[:3]}')
    await b.close()


async def sec_co(p, c):
    b, pg, errs = await fresh(p, 'u_klein')
    # the client chooses Zellige (+$1,850) on the portal
    await pg.evaluate(f"() => {{ const p = {J121}; setCurrent(p.id); const d = p.decisions.find(x => x.id === 'd8'); d.sentOn = today(); portalDecide(d) }}")
    await pg.wait_for_timeout(300)
    await pg.click('#mbm label.sel-opt:has-text("Zellige")'); await pg.wait_for_timeout(100)
    await pg.click('#mbm-ok'); await pg.wait_for_timeout(500)
    r = await pg.evaluate(f"() => {{ const p = {J121}, d = p.decisions.find(x => x.id === 'd8'); const a = (p.actions || []).find(x => x.next === 'raise-co' && x.source && x.source.id === 'd8'); return {{ status: d.status, delta: d.chosen && d.chosen.delta, task: a ? [a.id, a.title, a.status] : null }} }}")
    c.ok(r['status'] == 'made' and r['delta'] == 1850 and r['task'] and r['task'][2] == 'todo', f'the choice is recorded and a task to raise the $1,850 CO opens: {r}')
    # before any CO: Ask lists it, the decided decision keeps Raise Change Order
    await sign_in(pg, 'u_alan')
    a = await ask(pg, 'what still needs a change order')
    c.ok('2nd floor bathroom finishes' in a and '1,850' in a, f'Ask "what still needs a change order" lists the decision: {a[:300]!r}')
    await pg.evaluate(f"() => {{ setCurrent({J121}.id); view = 'dec'; render(); thDecOpen('d8') }}"); await pg.wait_for_timeout(300)
    btns = await pg.evaluate("() => [...document.querySelectorAll('#th-dec button')].map(b => b.innerText)")
    c.ok(any(x.startswith('Raise Change Order') for x in btns), f'the decided decision keeps Raise Change Order: {btns}')
    # the task's Raise Change Order opens the CO editor prefilled with the option line and amount
    await go(pg, 'tkall'); await pg.wait_for_timeout(400)
    n = await pg.locator(f'.view.on [data-clraise="{r["task"][0]}"]').count()
    c.ok(n >= 1, 'the task row carries Raise Change Order')
    if n:
        await pg.click(f'.view.on [data-clraise="{r["task"][0]}"]'); await pg.wait_for_timeout(500)
    co = await pg.evaluate(f"() => {{ const p = {J121}, d = p.decisions.find(x => x.id === 'd8'); const x = d.coId && clCoOf(d.coId); return x ? {{ number: x.d.number, status: x.d.status, lines: x.d.lines.map(l => [l.item, l.rate]), open: docOpen && docOpen.id === x.d.id, view: view, title: x.d.title }} : null }}")
    c.ok(co and co['open'] and co['view'] in ('clients', 'billing'), f'Raise Change Order opens the CO editor: {co}')
    c.ok(co and co['lines'] and re.search(r'Zellige', co['lines'][0][0]) and co['lines'][0][1] == 1850, f'the CO line is the chosen option at +$1,850: {co and co["lines"]}')
    ed = await text(pg)
    c.ok(co and co['number'] in ed and '$1,850' in ed, f'the editor shows {co and co["number"]} for $1,850')
    # the task stays open until the CO is sent; the decision now shows the CO instead of the button
    st = await pg.evaluate(f"() => {{ const p = {J121}; clTaskSweep(); const a = p.actions.find(x => x.id === '{r['task'][0]}'); return [a.status, a.closedWhy || ''] }}")
    c.ok(st[0] != 'done', f'the task stays open while the CO is a draft: {st}')
    await pg.evaluate(f"() => {{ setCurrent({J121}.id); view = 'dec'; render(); thDecOpen('d8') }}"); await pg.wait_for_timeout(300)
    btns = await pg.evaluate("() => [...document.querySelectorAll('#th-dec button')].map(b => b.innerText)")
    chip = await pg.evaluate("() => [...document.querySelectorAll('#th-dec .ops-chip')].map(b => b.innerText.replace(/\\s+/g, ' '))")
    c.ok(not any(x.startswith('Raise Change Order') for x in btns) and any(co['number'] in x for x in chip), f'once a CO references it the decision shows the CO: {btns} {chip}')
    a = await ask(pg, 'what still needs a change order')
    c.ok('2nd floor bathroom finishes' in a and co['number'] in a, f'until it is sent, Ask still lists it with the draft: {a[:300]!r}')
    # send it: the task closes
    sent = await pg.evaluate(f"""async n => {{ const c = {KLEIN}, d = c.changeOrders.find(x => x.number === n); d.lines[0].rate = 1850;
        const r = docAction(c, d, 'send'); if (r && r.then) await r; await new Promise(z => setTimeout(z, 150)); clTaskSweep();
        const p = {J121}, a = p.actions.find(x => x.id === '{r['task'][0]}'); return {{ status: d.status, task: a.status, why: a.closedWhy || '' }} }}""", co['number'])
    c.ok(sent['status'] == 'sent' and sent['task'] == 'done' and co['number'] in sent['why'], f'the task closes when the CO is sent: {sent}')
    a = await ask(pg, 'what still needs a change order')
    c.ok('2nd floor bathroom finishes' not in a, f'after sending, Ask no longer lists it: {a[:200]!r}')
    c.ok(not errs, f'co: page errors {errs[:3]}')
    await b.close()


LEAK = re.compile(r'Proceed as an extra|I will write the CO|photograph both joists', re.I)


async def sec_fieldco(p, c):
    b, pg, errs = await fresh(p)
    await pg.evaluate(f"() => {{ setCurrent({J121}.id); view = 'field'; render() }}"); await pg.wait_for_timeout(400)
    c.ok(await pg.locator('.view.on [data-opsraise="fr2"]').count() >= 1, 'the answered extra offers Write Change Order')
    await pg.click('.view.on [data-opsraise="fr2"]'); await pg.wait_for_timeout(500)
    co = await pg.evaluate(f"""() => {{ const c = {KLEIN}, r = DB.field.raises.find(x => x.id === 'fr2'), d = r.coId && c.changeOrders.find(x => x.id === r.coId);
        if (!d) return null; const ph = DB.photos.filter(x => x.ref && x.ref.kind === 'raise' && x.ref.id === 'fr2');
        return {{ number: d.number, memo: d.memo || '', notes: d.notes || d.internalNotes || '', exhibits: (d.exhibits || []).map(e => e.photoId || e), shared: ph.map(x => !!x.share),
                 tiles: document.querySelectorAll('.view.on .co-exhibits .pst-tile').length, summary: docSummaryHtml(c, d), mail: crDocEmail(c, d).body,
                 pdf: typeof docPrintHtml === 'function' ? docPrintHtml(c, d) : '', task: d.scope }} }}""")
    c.ok(co is not None, 'Write Change Order drafts a CO on the field item')
    if co:
        c.ok('joist' in co['memo'].lower() and 'Two joists cut' in co['memo'], f"the client memo is the item's title and note: {co['memo']!r}")
        c.ok(not LEAK.search(co['memo']), f"the PM's answer to the foreman is not in the memo: {co['memo']!r}")
        c.ok('photograph both joists' in co['notes'].lower(), f"the PM's answer is in Internal Notes: {co['notes']!r}")
        c.ok(not LEAK.search(co['summary']) and not LEAK.search(co['mail']) and not LEAK.search(co['pdf']), 'the approval dialog, the email and the PDF carry no internal answer')
        c.ok(len(co['exhibits']) == 2 and all(co['shared']), f"the item's 2 photos attach as exhibits shared with the client: {co['exhibits']} shared {co['shared']}")
        c.ok(co['tiles'] == 2, f"the CO editor shows the 2 exhibits: {co['tiles']} tiles")
        c.ok('photo' in co['summary'].lower() and co['summary'].count('pst-tile') == 2, 'the client approval dialog shows the exhibits')
    await sign_in(pg, 'u_klein'); await go(pg, 'client'); await pg.wait_for_timeout(300)
    for v in ('client', 'cldec', 'clacct'):
        await go(pg, v); t = await text(pg)
        c.ok(not LEAK.search(t), f'client view {v} carries no internal answer')
    c.ok(not errs, f'fieldco: page errors {errs[:3]}')
    await b.close()


async def sec_noshow(p, c):
    b, pg, errs = await fresh(p, 'u_angel')
    # the foreman marks the restoration sub a no-show on the phone (the Site screen); it reaches the PM
    r = await pg.evaluate(f"""() => {{ setCurrent({J121}.id); const s = DB.field.subs.find(x => x.projectId === S.id && x.date === today() && x.status !== 'onsite') || DB.field.subs.find(x => x.projectId === S.id);
        s.date = today(); fSubStatus(s.id, 'noshow'); const q = DB.field.raises.filter(x => x.type === 'noshow').pop(); return {{ sub: s.id, vendor: s.vendor, lead: s.lead, taskId: s.taskId, raise: q && q.id, to: q && q.to }} }}""")
    c.ok(r['raise'] and r['to'] == 'pm', f'the no-show reaches the PM as a question: {r}')
    await sign_in(pg, 'u_alan')
    await pg.evaluate("id => { setCurrent('p121'); fAnswerRaise(DB.field.raises.find(x => x.id === id)) }", r['raise']); await pg.wait_for_timeout(300)
    m = await modal(pg)
    c.ok(re.search(r'Slip', m) and re.search(r'Rebook', m) and re.search(r'Confirm by Text the Day Before', m) and re.search(r'Chase the Sub', m),
         f'answering a no-show offers slip, rebook + confirm by text, chase: {m[:300]!r}')
    nxt = await pg.evaluate("() => nextWork(addWork(today(), 1))")
    await pg.fill('#mbm [data-f="a"]', 'Rebooked Tomas for Friday; framing crew covers the scaffold day.')
    await pg.fill('#mbm [data-f="slip"]', '1')
    await pg.fill('#mbm [data-f="rebook"]', nxt)
    await pg.check('#mbm [data-f="confirmText"]')
    await pg.check('#mbm [data-f="chase"]')
    await pg.click('#mbm-ok'); await pg.wait_for_timeout(500)
    out = await pg.evaluate(f"""([tid, vendor, lead, nxt]) => {{ const p = {J121}, t = p.tasks.find(x => x.id === tid), h = (t.history || []).slice(-1)[0] || {{}};
        const subs = DB.field.subs.filter(s => s.projectId === p.id && s.vendor === vendor && s.date === nxt);
        const dayBefore = addWork(nxt, -1);
        const rem = DB.projects.flatMap(x => x.actions || []).filter(a => a.status !== 'done' && /confirm|text/i.test(a.title) && a.title.includes(lead) && a.due === dayBefore);
        const drafts = (DB.outbox || []).filter(o => o.status !== 'sent' && /confirm/i.test(o.body || '') && (o.to && (o.to.name || '').includes(lead)));
        const chase = DB.projects.flatMap(x => x.actions || []).filter(a => a.status !== 'done' && /chase|call/i.test(a.title) && a.title.includes(vendor));
        return {{ reasonKey: h.reasonKey, days: h.days, reason: h.reason, rebooked: subs.map(s => s.status), reminders: rem.map(a => [a.title, a.due, a.assignee]), drafts: drafts.length, chase: chase.map(a => a.title) }} }}""", [r['taskId'], r['vendor'], r['lead'], nxt])
    c.ok(out['reasonKey'] == 'noshow' and out['days'] == 1, f"Slip 1 day lands in the history with the no-show cause: {out}")
    c.ok(out['rebooked'] == ['unconfirmed'], f"the sub is rebooked for {nxt}: {out['rebooked']}")
    c.ok(len(out['reminders']) == 1, f"a dated reminder to text the day before: {out['reminders']}")
    c.ok(out['drafts'] >= 1, f"an outbound draft to the sub waits for approval: {out['drafts']}")
    c.ok(len(out['chase']) >= 1, f"a chase on the sub: {out['chase']}")
    # the forecast and the Changes note carry the cause
    why = await pg.evaluate("() => tpForecastWhy(S).text")
    c.ok(re.search(r'no-show|could not be on site', why, re.I), f'the forecast names the no-show: {why!r}')
    # the brain proposes the rule, as a proposal with a trigger, not applied
    les = await pg.evaluate("() => ({ sug: bnSuggestLessons().filter(l => /confirm/i.test(l.title) && /day before/i.test(l.title)).map(l => [l.title, l.trigger, l.then && l.then.kind]), have: DB.lessons.filter(l => /confirm/i.test(l.title) && /day before/i.test(l.title)).length })")
    c.ok(len(les['sug']) == 1 and les['sug'][0][1] and les['have'] == 0, f'the brain proposes "confirm every sub the day before" with a trigger and does not apply it: {les}')
    await go(pg, 'brain'); await pg.wait_for_timeout(400)
    t = await text(pg)
    c.ok(re.search(r'day before', t, re.I) and await pg.locator('.view.on [data-bnsug]').count() >= 1, 'The Brain shows the proposed lesson with a button')
    c.ok(not errs, f'noshow: page errors {errs[:3]}')
    await b.close()


async def sec_insp(p, c):
    b, pg, errs = await fresh(p)
    await pg.evaluate(f"() => {{ setCurrent({J121}.id); const p = S; (p.actions = p.actions || []).some(a => /book rough inspection/i.test(a.title)) || p.actions.push({{ id: uid('a'), title: 'Book Rough Inspection', assignee: 'Alan', due: '2026-09-14', priority: 'med', status: 'todo', source: {{ kind: 'meeting', label: 'site walk' }} }}); view = 'insp'; render() }}")
    await pg.wait_for_timeout(400)
    c.ok(await pg.locator('.view.on [data-book="i3"]').count() == 1, 'the DOB rough plumbing inspection row offers Book')
    await pg.click('.view.on [data-book="i3"]'); await pg.wait_for_timeout(300)
    m = await modal(pg)
    c.ok(m.lower().startswith('book'), f'Book opens its dialog: {m[:60]!r}')
    await pg.fill('#mbm [data-f="date"]', '2026-09-08')
    await pg.fill('#mbm [data-f="from"]', '08:00')
    await pg.fill('#mbm [data-f="to"]', '12:00')
    await pg.fill('#mbm [data-f="docket"]', 'B01528834-I1')
    await pg.click('#mbm-ok'); await pg.wait_for_timeout(500)
    out = await pg.evaluate(f"""() => {{ const p = {J121}, i = p.inspections.find(x => x.id === 'i3');
        const hold = ((DB.calendar || {{}}).external || []).filter(e => e.inspId === 'i3');
        const notes = (DB.field.notes || []).filter(n => n.projectId === p.id && /inspection/i.test(n.text));
        const chat = (p.chat || []).filter(x => /inspection/i.test(x.text || ''));
        const drafts = (DB.outbox || []).filter(o => o.status !== 'sent' && /inspection/i.test((o.subject || '') + (o.body || '')));
        const task = p.actions.find(a => /book rough inspection/i.test(a.title));
        return {{ status: i.status, date: i.date, win: i.window, hold: hold.map(h => [h.start, h.end, h.title]), notes: notes.length, chat: chat.length, drafts: drafts.map(d => d.to && (d.to.name || d.to.email)), task: [task.status, task.closedWhy || ''] }} }}""")
    c.ok(out['status'] == 'scheduled' and out['date'] == '2026-09-08' and out['win'] and out['win']['from'] == '08:00' and out['win']['to'] == '12:00', f'the inspection is booked for 9/8 8-12: {out}')
    c.ok(len(out['hold']) == 1 and out['hold'][0][0].startswith('2026-09-08T08:00'), f"the window is held on the calendar: {out['hold']}")
    c.ok(out['notes'] >= 1 and out['chat'] >= 1, f"the foreman is told (a field note and a Chat message): notes {out['notes']} chat {out['chat']}")
    c.ok(len(out['drafts']) >= 1, f"a draft to the licensed trade waits for approval: {out['drafts']}")
    c.ok(out['task'][0] == 'done' and '9/8' in out['task'][1] or 'Sep 8' in out['task'][1], f"the Book Rough Inspection task closes: {out['task']}")
    tst = await toast(pg)
    c.ok('Open' in tst or 'booked' in tst.lower(), f'the booking toasts with Open: {tst!r}')
    await sign_in(pg, 'u_angel'); await go(pg, 'ftoday'); await pg.wait_for_timeout(300)
    t = await text(pg)
    c.ok(re.search(r'inspection', t, re.I) and re.search(r'Sep 8|9/8', t), f"the foreman's Today carries the booking")
    # a DOB NOW notice in mail proposes the booking with its window; nothing is booked until approved
    await sign_in(pg, 'u_alan')
    pr = await pg.evaluate(f"""() => {{ const p = {J121}; const i = p.inspections.find(x => x.id === 'i3'); Object.assign(i, {{ status: 'not-scheduled', date: '', window: null }});
        const c = {{ id: 'cm_dob', subject: 'DOB NOW: Job B01528834-I1 — inspection scheduled 09/08/2026 — 121 STATE STREET', from: 'DOB NOW <donotreply@dobnow.example>',
          text: 'DOB NOW Inspections\\nJob B01528834-I1, 121 STATE STREET, BROOKLYN\\nInspection type: Plumbing — rough\\nScheduled: 09/08/2026, window 8:00 AM – 12:00 PM\\nThe licensed master plumber or a representative must be on site with the approved drawings.', route: {{ projectId: p.id }} }};
        const P = cmRead(c); const q = P.find(x => x.kind === 'inspection'); return {{ kinds: P.map(x => x.kind), q: q && {{ inspId: q.inspId, date: q.date, from: q.from, to: q.to, summary: q.summary }}, booked: i.status }} }}""")
    c.ok(pr['q'] and pr['q']['inspId'] == 'i3' and pr['q']['date'] == '2026-09-08' and pr['q']['from'] == '08:00' and pr['q']['to'] == '12:00', f'the DOB NOW notice proposes booking i3 for 9/8 8-12: {pr}')
    c.ok(pr['booked'] == 'not-scheduled', 'the proposal books nothing on its own')
    c.ok(not errs, f'insp: page errors {errs[:3]}')
    await b.close()


TPL_NAMES = ['Garden bedroom framing layout', 'Laundry layout with new washer/dryer sizes', 'Interior door design & sizes', 'GWB boards', 'Rough plumbing pipe & fittings']


async def sec_lenox(p, c):
    b, pg, errs = await fresh(p, 'u_owner')
    r = await pg.evaluate("""() => { const p = DB.projects.find(x => x.id === 'p206'); const t = projectFromTemplate('X test', '1 Main St', today(), '');
        return { tasks: p.tasks.length, decs: p.decisions.map(d => d.name), mats: p.materials.map(m => m.name), insp: p.inspections.length, issues: (p.issues || []).length, subm: (p.submittals || []).length,
                 tpl: { decs: t.decisions.length, mats: t.materials.length, issues: (t.issues || []).length, subm: (t.submittals || []).length, tasks: t.tasks.length, insp: t.inspections.length } } }""")
    c.ok(2 <= r['tasks'] <= 10 and len(r['decs']) == 1 and len(r['mats']) == 2, f"206 Lenox has its own small turnover scope: {r['tasks']} tasks, decisions {r['decs']}, materials {r['mats']}")
    c.ok(not any(n in x for n in TPL_NAMES for x in r['decs'] + r['mats']), f"none of 121 State's decisions or materials under 206 Lenox: {r['decs']} {r['mats']}")
    c.ok(r['tpl']['decs'] == 0 and r['tpl']['mats'] == 0 and r['tpl']['issues'] == 0 and r['tpl']['subm'] == 0 and r['tpl']['tasks'] > 10, f"the project template copies phases and inspections only: {r['tpl']}")
    # a boot migration strips clone copies already present on a saved database
    await pg.evaluate("""() => { const p = DB.projects.find(x => x.id === 'p206'), t = template121();
        p.decisions.push(...t.decisions.slice(0, 3).map(d => Object.assign({}, d, { status: 'open' }))); p.materials.push(...t.materials.slice(0, 4).map(m => Object.assign({}, m, { status: 'not-ordered' })));
        saveNow ? saveNow() : save() }""")
    await pg.wait_for_timeout(400)
    await pg.reload(); await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
    await sign_in(pg, 'u_owner')
    r2 = await pg.evaluate("() => { const p = DB.projects.find(x => x.id === 'p206'); return { decs: p.decisions.map(d => d.name), mats: p.materials.map(m => m.name) } }")
    c.ok(len(r2['decs']) == 1 and len(r2['mats']) == 2 and not any(n in x for n in TPL_NAMES for x in r2['decs'] + r2['mats']), f"after a reload the clone copies are stripped: {r2}")
    # nothing of 121 State's shows under 206 Lenox on PM Home, Approvals, Purchasing or Ask
    await sign_in(pg, 'u_alan')
    bad = []
    for v in ('home', 'mapprove'):
        await go(pg, v); await pg.wait_for_timeout(300); t = await text(pg)
        for n in TPL_NAMES:
            for m in re.finditer(re.escape(n), t):
                ctx = t[max(0, m.start() - 160):m.end() + 160]
                if '206 Lenox' in ctx: bad.append((v, n))
    await sign_in(pg, 'u_chen'); await go(pg, 'po'); await pg.wait_for_timeout(300); t = await text(pg)
    for n in TPL_NAMES:
        for m in re.finditer(re.escape(n), t):
            ctx = t[max(0, m.start() - 160):m.end() + 160]
            if '206 Lenox' in ctx: bad.append(('po', n))
    c.ok(not bad, f"121 State's items under 206 Lenox on: {bad}")
    rows = await pg.evaluate("() => ({ late: PRED.jobLate.rows('p206').length, buy: (typeof eqRows === 'function' ? eqRows('materials') : []).filter(m => m.projectId === 'p206' || m.project === '206 Lenox').map(m => m.name || m.item) })")
    c.ok(not any(n in x for n in TPL_NAMES for x in rows['buy']), f"Purchasing rows for 206 Lenox: {rows['buy']}")
    await sign_in(pg, 'u_owner')
    a = await ask(pg, 'which decisions are waiting on the client')
    i = a.find('206 Lenox')
    c.ok(i < 0 or not any(n in a[i:i + 300] for n in TPL_NAMES), f"Ask shows no clone decisions under 206 Lenox: {a[i:i + 300] if i >= 0 else 'none'!r}")
    c.ok(not errs, f'lenox: page errors {errs[:3]}')
    await b.close()


async def sec_labels(p, c):
    b, pg, errs = await fresh(p)
    await go(pg, 'home'); await pg.wait_for_timeout(300)
    tiles = await pg.evaluate("() => [...document.querySelectorAll('.view.on [data-tdpulse]')].map(a => ({ k: a.dataset.tdpulse, n: +a.dataset.n, label: a.querySelector('span').innerText }))")
    late = next((t for t in tiles if t['k'] == 'late'), None)
    site = next((t for t in tiles if t['k'] == 'site'), None)
    c.ok(late and late['label'] == 'Jobs With Late Items', f'the Home tile names what it counts (jobs with late items): {late}')
    await go(pg, 'ovjobs'); await pg.wait_for_timeout(300)
    ov = await pg.evaluate("() => [...document.querySelectorAll('.view.on .kpi, .view.on .gl, .view.on [data-tl]')].map(x => x.innerText.replace(/\\s+/g, ' ')).filter(x => /Late/.test(x))")
    c.ok(any('Finish Dates Late' in x for x in ov) and not any('Running Late' in x for x in ov) and not any('Jobs Late' in x for x in ov), f'the Projects tile is Finish Dates Late (the finish past its target): {ov}')
    rule = await pg.evaluate("() => { const x = [...document.querySelectorAll('.view.on .kpi, .view.on .gl, .view.on [data-tl]')].find(x => /Finish Dates Late/.test(x.innerText)); return x ? (x.title || x.innerText) : '' }")
    c.ok(re.search(r'target', rule, re.I), f'the Finish Dates Late tile states its rule: {rule!r}')
    # Site Questions: Home = Approvals chip
    await go(pg, 'mapprove'); await pg.wait_for_timeout(300)
    chip = await pg.evaluate("() => { const b = document.querySelector('#mappr-tabs [data-mak=\"raise\"] .n'); return b ? +b.innerText : 0 }")
    c.ok(site and site['n'] == chip, f'Home Site Questions {site and site["n"]} = Approvals Site Questions {chip}')
    # the Pulse tiles open their list, by a real click on the number
    await go(pg, 'home'); await pg.wait_for_timeout(300)
    for t in tiles:
        await pg.click(f'.view.on [data-tdpulse="{t["k"]}"] b'); await pg.wait_for_timeout(250)
        n = await pg.evaluate("k => { const s = document.querySelector('#mbm [data-tdsheet=\"' + k + '\"]'); return s ? +s.dataset.n : null }", t['k'])
        c.ok(n == t['n'], f'Pulse {t["label"]} opens its list of {t["n"]}: sheet {n}')
        await pg.evaluate("() => mbCloseModal()"); await pg.wait_for_timeout(100)
    # one person, one name
    await pg.evaluate("() => { const p = DB.projects[0]; p.actions.push({ id: uid('a'), title: 'Ops test: a task for Chen', assignee: 'Chen', due: today(), priority: 'med', status: 'todo' }, { id: uid('a'), title: 'Ops test: a task for the crew', assignee: 'Alberto / Satish', due: today(), priority: 'med', status: 'todo' }); if (typeof crCanonTasks === 'function') crCanonTasks() }")
    await pg.evaluate("() => { tkWho = 'all'; view = 'tkall'; render() }"); await pg.wait_for_timeout(400)
    opts = await pg.evaluate("() => [...document.querySelectorAll('.view.on select option')].map(o => o.innerText.trim())")
    c.ok('Chen Biron' in opts and 'Chen' not in opts, f'one Chen in the person filter: {[o for o in opts if "Chen" in o]}')
    c.ok('Alberto / Satish' not in opts and 'Alberto' in opts and 'Satish' in opts, f'Alberto and Satish are two people, not one: {[o for o in opts if "Alberto" in o or "Satish" in o]}')
    names = await pg.evaluate("() => [...new Set(DB.projects.flatMap(p => p.actions || []).map(a => a.assignee))].filter(n => /^Chen$|Alberto \\/ Satish/.test(n))")
    c.ok(not names, f'task assignees resolve to the people record: {names}')
    await pg.evaluate("() => newTaskDialog({})"); await pg.wait_for_timeout(300)
    lists = await pg.evaluate("() => ({ who: [...document.querySelectorAll('#mbm [data-f=assignee] option')].map(o => o.innerText), fr: [...document.querySelectorAll('#mbm [data-f=for] option')].map(o => o.innerText) })")
    c.ok(lists['fr'].count('The Lindqvists') == 1, f"New Task > For lists The Lindqvists once: {lists['fr'].count('The Lindqvists')}")
    c.ok('Chen Biron' in lists['who'] and 'Chen' not in lists['who'], f"New Task > Assigned To: {lists['who']}")
    await pg.evaluate("() => mbCloseModal()")
    c.ok(not errs, f'labels: page errors {errs[:3]}')
    await b.close()


def cut_ok(full, shown):
    """shown is the full text, or a prefix of it cut at a word boundary and ended with an ellipsis."""
    if full in shown: return True
    m = re.search(r'(.+?)…', shown)
    if not m: return False
    pre = m.group(1).rstrip()
    return full.startswith(pre) and (len(pre) == len(full) or full[len(pre)] in ' ,.;:—-')


async def sec_polish(p, c):
    b, pg, errs = await fresh(p)
    # leaving an approved, read-only CO asks nothing
    await pg.evaluate(f"() => {{ const c = {KLEIN}, d = c.changeOrders.find(x => x.status === 'approved'); flowGo.doc(c, 'co', d)() }}"); await pg.wait_for_timeout(400)
    await pg.click('#nav-groups button:has-text("Projects")'); await pg.wait_for_timeout(300)
    m = await modal(pg)
    c.ok('save changes' not in m.lower(), f'leaving an approved CO asks nothing: {m[:80]!r}')
    # the CO toast cuts on a word
    await pg.evaluate(f"() => {{ setCurrent({J121}.id); opsRaiseCO({{ kind: 'raise', id: 'fr2' }}) }}"); await pg.wait_for_timeout(200)
    tst = await toast(pg)
    title = await pg.evaluate("() => clRewrite(DB.field.raises.find(x => x.id === 'fr2').title)")
    c.ok(cut_ok(title, tst), f'the CO toast cuts the title on a word: {tst!r}')
    # the portal finish headline cuts the PM's note on a word
    note = 'Framing on the 3rd floor runs to 9/17: 3 days are your approved change order, 5 days are our restoration sub missing a day.'
    await pg.evaluate(SLIP, ['frame', 2, 'noshow'])
    await pg.evaluate("n => { opsPublish(S, n); save() }", note)
    await sign_in(pg, 'u_klein'); await go(pg, 'sched'); await pg.wait_for_timeout(300)
    t = await text(pg)
    q = re.search(r'“([^”]+)”|"([^"]+)"', t)
    c.ok(q and cut_ok(note, (q.group(1) or q.group(2))), f'the portal finish line cuts the note on a word: {q and (q.group(1) or q.group(2))!r}')
    # the foreman's card says the decision once
    await sign_in(pg, 'u_angel'); await go(pg, 'ftoday'); await pg.wait_for_timeout(300)
    t = await text(pg)
    c.ok('Proceed as an extra' in t and 'Proceed as an extra. Proceed as an extra' not in t, "the foreman's card reads the decision once")
    # the first Acknowledge click works (Chen's Approvals)
    await sign_in(pg, 'u_chen'); await go(pg, 'mapprove'); await pg.wait_for_timeout(400)
    await pg.evaluate("() => { window.mApprKind = 'req'; render() }"); await pg.wait_for_timeout(300)
    n = await pg.locator('.view.on .m-appr-a [data-myes]').count()
    c.ok(n >= 1, 'Chen has a request to acknowledge')
    if n:
        before = await pg.evaluate("() => DB.projects.flatMap(p => p.requests || []).filter(r => r.status === 'new').length")
        await pg.click('.view.on .m-appr-a [data-myes]'); await pg.wait_for_timeout(400)
        after = await pg.evaluate("() => DB.projects.flatMap(p => p.requests || []).filter(r => r.status === 'new').length")
        c.ok(after == before - 1, f'the first Acknowledge click acknowledges: new requests {before} -> {after}')
        c.ok(await toast(pg), 'Acknowledge toasts')
    # Chen's Home link for a field question lands on the question
    await go(pg, 'home'); await pg.wait_for_timeout(400)
    hit = await pg.evaluate("() => { const r = [...document.querySelectorAll('.view.on .h4r, .view.on [data-ea], .view.on [data-h4go]')].find(x => /Insulation/.test(x.innerText)); if (!r) return null; r.click(); return view }")
    c.ok(hit in ('mapprove', 'field'), f"Chen's Home link for the insulation question lands on {hit}")
    # stamps sit in site hours on the demo clock
    hhmm = await pg.evaluate("() => appNowIso().slice(11, 16)")
    c.ok('07:00' <= hhmm <= '18:30', f'the demo clock stamps inside site hours: {hhmm}')
    # the daily log record shows the photos it lists and takes the PM's acknowledgement
    await sign_in(pg, 'u_alan')
    await pg.evaluate(f"() => {{ setCurrent({J121}.id); view = 'field'; fxTab = 'log'; render() }}"); await pg.wait_for_timeout(400)
    await pg.evaluate("() => { const b = [...document.querySelectorAll('.view.on [data-dlopen]')].find(x => /Sep 2|9\\/2/.test(x.closest('.ops-log, .dl-past') ? x.closest('.ops-log, .dl-past').innerText : '')); b && b.click() }"); await pg.wait_for_timeout(400)
    rec = await pg.evaluate("() => { const l = DB.field.logs.find(x => x.projectId === 'p121' && x.date === '2026-09-02'); const el = document.querySelector('.view.on .dl-rec, #mbm .dl-rec'); return { listed: (l.photoIds || []).length, shown: el ? el.querySelectorAll('.pst-tile').length : -1, ack: el ? !!el.querySelector('[data-dlack]') : false, text: el ? el.innerText.slice(0, 120) : '' } }")
    c.ok(rec['shown'] == rec['listed'] and rec['listed'] >= 1, f"the 9/2 log shows the {rec['listed']} photos it lists: {rec['shown']} shown")
    c.ok(rec['ack'], 'the PM can acknowledge the log')
    if rec['ack']:
        await pg.click('[data-dlack]'); await pg.wait_for_timeout(300)
        ak = await pg.evaluate("() => { const l = DB.field.logs.find(x => x.projectId === 'p121' && x.date === '2026-09-02'); return l.ack && l.ack.by }")
        c.ok(ak == 'Alan', f'the acknowledgement is recorded with who: {ak}')
    # the committed-deliverable-dates rule proposes only where a deliverable is undated
    q = await pg.evaluate("""() => { bnRun(); const L = DB.lessons.find(l => /outside designer or consultant commits to dates/i.test(l.title));
        const Q = (DB.brainQueue || []).filter(x => x.lessonId === L.id && x.status === 'proposed');
        return Q.map(x => { const p = DB.projects.find(y => y.id === x.projectId); const rx = /architect|designer|consultant|engineer/i;
          const undated = (p.decisions || []).filter(d => d.status === 'open' && rx.test(d.owner || '') && !d.due).length; return [p.project.name, undated] }) }""")
    c.ok(q and all(u > 0 for _, u in q) and not any('206 Lenox' in n for n, _ in q), f'the deliverable-dates rule proposes only on jobs with an undated outside deliverable: {q}')
    # Workload counts the approvals the PM holds
    await go(pg, 'brain'); await pg.evaluate("() => { bnTab = 'workload'; renderBrain() }"); await pg.wait_for_timeout(300)
    t = await text(pg)
    appr = await pg.evaluate("() => PRED.waitingOnMe.count()")
    row = re.search(r'Alan[^\n]*\n[^\n]*', t)
    c.ok(row and re.search(r'\d+ approvals? waiting', row.group(0)), f"the PM's Workload row counts the {appr} approvals: {row and row.group(0)!r}")
    c.ok('everyone is inside their week' not in t, 'Workload does not say everyone is inside their week while the PM holds a queue')
    c.ok(not errs, f'polish: page errors {errs[:3]}')
    await b.close()


async def main():
    c = Checks()
    async with async_playwright() as p:
        for name, fn in (('sched', sec_sched), ('co', sec_co), ('fieldco', sec_fieldco), ('noshow', sec_noshow), ('insp', sec_insp),
                         ('lenox', sec_lenox), ('labels', sec_labels), ('polish', sec_polish)):
            if want(name):
                print('--', name)
                try:
                    await fn(p, c)
                except Exception as e:
                    c.ok(False, f'{name}: {type(e).__name__}: {str(e).splitlines()[0][:200]}')
    sys.exit(c.done())

if __name__ == "__main__": asyncio.run(main())
