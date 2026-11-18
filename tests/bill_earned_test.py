"""No invoice bills more than is earned and not billed, by any route (billing review 11-17, the third walk).
Invented demo data only. Driven as billing (u_billing) through the screens, on the desktop and the phone.

1  The cap at send, by every route. The $17,080 "At filing" draft of EST-2026-D45 with one line raised went out at
   $42,280 ($63,630 billed on a $42,700 fee); a Duplicate of the paid INV-2026-D45-1 sent the signing bill again; the
   10% sign-off went out before it was reached. Now the one gate every send passes through (pbAheadGate, reading
   pbEarnedOver) shows the dollars over and the choices: Lower It (blue, the safe step) or bill ahead with a reason,
   at the editor's Send, the viewer's Send and Mark as Sent alike. A draft within what is earned goes straight on.
2  What is billed is read from invoices that exist and are not void: deleting or voiding the milestone draft puts its
   $17,080 back on Ready to Bill with the blue Bill the Milestone; design hours and a change order the same.
3  A paid invoice revised down: what was received past what the revision bills is credit on account, on the client
   and in the viewer, with Refund and Apply as the next step; the revision of a paid invoice is not overdue.
4  A second estimate on a job whose contract is billed against asks what it is before anything changes: change order,
   replacement or separate contract; the copy of a signed estimate is asked the same.
5  Bill It then Draft and Draft then Bill It give the same application; a change order line starts at its measured 0%.
7-9  A credit application reads as applied credit, not "In the bank"; the revision editor says the date it carries;
   billing reverses an applied credit from the invoice it is on.
"""
import asyncio, sys
from harness import *

SLEEP = "ms => new Promise(r => setTimeout(r, ms))"


async def js(pg, body, arg=None):
    return await pg.evaluate("async (arg) => { const sleep = " + SLEEP + "; " + body + " }", arg)


FIND = """
  const fi = (n) => { for (const c of DB.clients) for (const i of (c.invoices || [])) if (i.number === n) return [c, i]; return [null, null]; };
  const fe = (n) => { for (const c of DB.clients) for (const e of (c.estimates || [])) if (e.number === n) return [c, e]; return [null, null]; };
  const cur = () => { for (const c of DB.clients) for (const i of (c.invoices || [])) if (docOpen && i.id === docOpen.id) return [c, i]; return [null, null]; };
"""
MODAL = "const m = document.getElementById('mbm'); return m ? { h: (m.querySelector('h3') || {}).textContent || '', t: m.textContent, ok: (m.querySelector('#mbm-ok') || {}).textContent || '', alt: (m.querySelector('#mbm-alt') || {}).textContent || '', sw: document.documentElement.scrollWidth } : null;"


async def modal(pg):
    await pg.wait_for_timeout(250)
    return await js(pg, MODAL)


async def reset(pg):
    await js(pg, "try { dvClose(); } catch (e) {} try { mbCloseModal(); } catch (e) {} docOpen = null; view = 'billing'; render(); await sleep(300);")


async def open_doc(pg, kind, n):
    await js(pg, FIND + "const [c, d] = arg[0] === 'estimate' ? fe(arg[1]) : fi(arg[1]); try { dvClose(); } catch (e) {} dvOpen(arg[0], d.id, c.id); await sleep(700);", [kind, n])


async def dv_do(pg, label):
    b = pg.locator('#dv .dv-bar button, #dv .dv-menu button').filter(has_text=label)
    if await b.count() == 0:
        await pg.locator('#dv [data-dvact="more"]').click(); await pg.wait_for_timeout(250)
        b = pg.locator('#dv .dv-menu button').filter(has_text=label)
    await b.first.click(); await pg.wait_for_timeout(700)


async def milestone_draft(pg, idx=None):
    """The blue Bill the Milestone on EST-2026-D45 and the sheet's Create; returns the draft's number."""
    await open_doc(pg, 'estimate', 'EST-2026-D45')
    await pg.locator('#dv .dv-bar button.primary').first.click(); await pg.wait_for_timeout(900)
    if idx is not None:
        await pg.locator(f'#mbm [name=dms][value="{idx}"]').check()
    await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(900)
    return await js(pg, FIND + "const [c, i] = cur(); return i && i.number;")


async def send_editor(pg):
    b = pg.locator('[data-docact="sendclient"]:visible').first
    if await b.count():
        await b.click()
    else:
        await js(pg, FIND + "const [c, i] = cur(); docAction(c, i, 'sendclient');")
    await pg.wait_for_timeout(500)
    return await modal(pg)


async def finish_send(pg):
    """The Send to Client sheet's Send, with an address when it has none."""
    m = await modal(pg)
    if m and m['h'].startswith('Send to Client'):
        to = pg.locator('#mbm [data-f="to"]')
        if await to.count() and not await to.input_value():
            await to.fill('client@example.com')
        await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(900)


async def inv_state(pg, n):
    return await js(pg, FIND + "const [c, i] = fi(arg); return i && { st: i.status, total: docTotal(i).total, why: i.aheadWhy && i.aheadWhy.why, over: i.aheadWhy && i.aheadWhy.over };", n)


async def t1_cap(p, c, phone):
    tag = 'phone' if phone else 'desktop'
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, 'u_billing')
    # a draft within what is earned goes straight to the send sheet
    n = await milestone_draft(pg)
    m = await send_editor(pg)
    c.ok(m and m['h'].startswith('Send to Client'), f"[{tag}] 1: the $17,080 filing draft goes straight to Send to Client ({m and m['h']})")
    await js(pg, "try { mbCloseModal(); } catch (e) {}")
    # the expert's case: one line raised to $28,000, $42,280 in all
    await js(pg, FIND + "const [c, i] = cur(); i.lines[0].rate = 28000; save(); render(); await sleep(300);")
    tot = await js(pg, FIND + "const [c, i] = cur(); return docTotal(i).total;")
    c.ok(abs(tot - 42280) < 0.01, f"[{tag}] 1: the raised draft is $42,280 ({tot})")
    ban = await js(pg, "const e = document.getElementById('pb-ahead-total'); return e ? e.textContent : '';")
    c.ok('$25,200' in ban, f"[{tag}] 1: the editor says $25,200 over what is earned before Send ({ban[:160]})")
    m = await send_editor(pg)
    c.ok(m and 'More Than Is Earned' in m['h'] and '$17,080' in m['t'] and '$25,200' in m['t'],
         f"[{tag}] 1: editor Send asks: $17,080 earned and not billed, $25,200 over ({m and m['t'][:240]})")
    c.ok(m and m['ok'] == 'Lower It' and 'Reason' in m['alt'] and m['sw'] <= (390 if phone else 1440),
         f"[{tag}] 1: Lower It is the blue, billing ahead takes a reason, no sideways scroll ({m and (m['ok'], m['alt'], m['sw'])})")
    await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(700)
    s = await inv_state(pg, n)
    ed = await js(pg, FIND + "const [c, i] = cur(); return !!(i && document.getElementById('doc-' + i.id));")
    c.ok(s['st'] == 'draft' and ed, f"[{tag}] 1: Lower It leaves it a draft, open in the editor ({s}, {ed})")
    # Lower It lowers (billing re-walk 4, S2-2: it only opened the editor): the raised line back to its share, $17,080
    c.ok(abs(s['total'] - 17080) < 0.01, f"[{tag}] 1: Lower It brings the draft back to $17,080 ({s})")
    # raised again for the other doors
    await js(pg, FIND + "const [c, i] = cur(); i.lines[0].rate = 28000; save(); render(); await sleep(300);")
    # the editor's More > Mark as Sent meets the same gate
    more = pg.locator('details.doc-more > summary:visible').last
    if await more.count():
        await more.click(); await pg.wait_for_timeout(250)
    ms = pg.locator('.doc-more-menu [data-docact="send"]:visible')
    if await ms.count():
        await ms.first.click()
    else:
        await js(pg, FIND + "const [c, i] = cur(); docAction(c, i, 'send');")
    m = await modal(pg)
    c.ok(m and 'More Than Is Earned' in m['h'] and 'Mark as Sent' in m['alt'], f"[{tag}] 1: Mark as Sent asks the same, its button says Mark as Sent ({m and (m['h'], m['alt'])})")
    await js(pg, "try { mbCloseModal(); } catch (e) {}")
    c.ok((await inv_state(pg, n))['st'] == 'draft', f"[{tag}] 1: Mark as Sent did not send it")
    # the viewer's Send asks the same; with a reason it goes, the reason on its record with what it covers
    await open_doc(pg, 'invoice', n)
    await dv_do(pg, 'Send to Client')
    m = await modal(pg)
    c.ok(m and 'More Than Is Earned' in m['h'], f"[{tag}] 1: the viewer's Send asks the same ({m and m['h']})")
    await pg.locator('#mbm #mbm-alt').click(); await pg.wait_for_timeout(400)
    m = await modal(pg)
    c.ok(m and 'More Than Is Earned' in m['h'], f"[{tag}] 1: billing ahead with no reason is refused, the sheet stays")
    await pg.locator('#mbm [data-f="why"]').fill('the client asked to be billed the documents now')
    await pg.locator('#mbm #mbm-alt').click(); await pg.wait_for_timeout(900)
    await finish_send(pg)
    s = await inv_state(pg, n)
    c.ok(s['st'] == 'sent' and s['over'] == 'earned' and 'documents' in (s['why'] or ''), f"[{tag}] 1: with the reason it goes out, recorded ({s})")
    c.ok(not errs, f'[{tag}] 1: page errors: {errs[:2]}')
    await b.close()


async def t1_dup_signoff(p, c, phone):
    tag = 'phone' if phone else 'desktop'
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, 'u_billing')
    # Duplicate of the paid at-signing invoice: it bills the signing milestone again
    await open_doc(pg, 'invoice', 'INV-2026-D45-1')
    await dv_do(pg, 'Duplicate')
    await pg.locator('#mbm [data-dupall]').check(); await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(900)
    d = await js(pg, FIND + "const [c, i] = cur(); return { n: i.number, from: i.fromDoc, ms: i.milestone, ret: i.lines.some(l => l.retainerLine), total: docTotal(i).total };")
    c.ok(d['from'] == 'esD45' and d['ms'] == 0 and not d['ret'], f"[{tag}] 1: the copy keeps what it bills from and does not apply the retainer again ({d})")
    m = await send_editor(pg)
    c.ok(m and 'More Than Is Earned' in m['h'] and 'INV-2026-D45-1' in m['t'] and '$21,350' in m['t'], f"[{tag}] 1: sending the copy asks: the signing milestone is billed on INV-2026-D45-1 ({m and m['t'][:220]})")
    await js(pg, "try { mbCloseModal(); } catch (e) {}")
    await js(pg, FIND + "const [c, i] = cur(); docOpen = null; c.invoices.splice(c.invoices.indexOf(i), 1); save();")
    await reset(pg)
    # the sign-off milestone is not reached: the sheet says so, and its send asks
    await open_doc(pg, 'estimate', 'EST-2026-D45')
    await pg.locator('#dv .dv-bar button.primary').first.click(); await pg.wait_for_timeout(800)
    rows = await js(pg, "return [...document.querySelectorAll('#mbm .ms-row')].map(r => r.textContent);")
    c.ok(len(rows) == 3 and 'Not Reached' in rows[2] and 'Not Reached' not in rows[1], f"[{tag}] 1: the milestone sheet marks the sign-off Not Reached ({rows})")
    await pg.locator('#mbm [name=dms][value="2"]').check(); await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(900)
    n = await js(pg, FIND + "const [c, i] = cur(); return i.number;")
    await open_doc(pg, 'invoice', n)
    await dv_do(pg, 'Send to Client')
    m = await modal(pg)
    c.ok(m and 'More Than Is Earned' in m['h'] and 'not reached' in m['t'] and '$4,270' in m['t'], f"[{tag}] 1: sending the sign-off asks: not reached, $4,270 ({m and m['t'][:200]})")
    c.ok(not errs, f'[{tag}] 1: page errors: {errs[:2]}')
    await b.close()


async def t2_deleted(p, c, phone):
    tag = 'phone' if phone else 'desktop'
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, 'u_billing')
    rtb = "return jobReadyToBill(arg).rows.map(r => r.kind + ' ' + Math.round(r.amount));"
    before = await js(pg, rtb, 'p45')
    for how in ('del', 'void'):
        n = await milestone_draft(pg)
        mid = await js(pg, rtb, 'p45')
        c.ok(mid == [], f"[{tag}] 2: while the {n} draft is open the milestone is off Ready to Bill ({mid})")
        if how == 'del':
            await pg.locator('[data-docact="del"]:visible, button:visible').filter(has_text='Delete').first.click(); await pg.wait_for_timeout(500)
            await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(700)
        else:
            await js(pg, FIND + "const [c, i] = fi(arg); i.status = 'void'; i.voidReason = 'drafted twice'; save();", n)
        await reset(pg)
        after = await js(pg, rtb, 'p45')
        c.ok(after == before and after == ['dmilestone 17080'], f"[{tag}] 2: {how} of the draft puts $17,080 back on Ready to Bill ({after})")
        await open_doc(pg, 'estimate', 'EST-2026-D45')
        bar = await js(pg, "return [...document.querySelectorAll('#dv .dv-bar button.primary')].map(b => b.textContent.trim());")
        c.ok(bar == ['Bill the Milestone'], f"[{tag}] 2: and the blue Bill the Milestone is back ({bar})")
        await reset(pg)
    # design hours: a deleted hours draft gives its hours back
    hrs = await js(pg, FIND + """const [c, d] = fe('EST-2026-D140'); if (!d) return null;
      const before = designHoursUnbilled(c, d).length;
      const e = designHoursUnbilled(c, d)[0]; if (!e) return { before };
      const inv = newDoc(c, 'invoice', { mode: 'items' }); inv.hoursBilled = true; inv.fromDoc = d.id; e.invoiceId = inv.id;
      const mid = designHoursUnbilled(c, d).length;
      c.invoices.splice(c.invoices.indexOf(inv), 1);
      return { before, mid, after: designHoursUnbilled(c, d).length };""")
    c.ok(hrs and hrs.get('mid') == hrs['before'] - 1 and hrs.get('after') == hrs['before'], f"[{tag}] 2: an hour on a deleted draft is unbilled again ({hrs})")
    # a change order on the application: Bill It, delete the draft, it is back waiting
    co = await js(pg, FIND + """const c = DB.clients.find(x => (x.changeOrders || []).some(o => o.number === 'CO-2026-001')); const co = c.changeOrders.find(o => o.number === 'CO-2026-001');
      const held = () => readyToBill().held.filter(h => h.sv && h.sv.coId === co.id).length + readyToBill().rows.filter(r => r.p && r.p.id === 'p121').length;
      const before = held(); await docAction(c, co, 'progress'); await sleep(300);
      const inv = c.invoices.find(i => i.mode === 'sov' && i.status === 'draft'); const mid = held();
      c.invoices.splice(c.invoices.indexOf(inv), 1); save();
      return { before, mid, after: held() };""")
    c.ok(co['before'] > 0 and co['after'] == co['before'], f"[{tag}] 2: CO-2026-001's draft deleted, the job's billing is waiting again ({co})")
    c.ok(not errs, f'[{tag}] 2: page errors: {errs[:2]}')
    await b.close()


async def t3_revise_paid(p, c, phone):
    tag = 'phone' if phone else 'desktop'
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, 'u_billing')
    await open_doc(pg, 'invoice', 'INV-2026-031')
    await dv_do(pg, 'Edit')
    await pg.locator('#mbm [data-f="why"]').fill('wrong percent on demolition'); await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(900)
    r = await js(pg, FIND + "const [c, i] = cur(); return i && { n: i.number, due: i.due, date: i.date };")
    c.ok(r and r['n'] == 'INV-2026-031-R1' and r['due'] >= '2026-09-03', f"[{tag}] 6: the revision of a paid invoice is due on its own terms, not overdue the day it goes ({r})")
    word = await js(pg, "const e = document.querySelector('[data-revdate]'); return e ? e.textContent : '';")
    c.ok('Aug 1' in word or '8/1' in word or 'Aug' in word, f"[{tag}] 8: the editor says the date it carries while no amount changes ({word[:140]})")
    # $560 down: 20% of $28,000 on the first line becomes 18%
    await js(pg, FIND + "const [c, i] = cur(); i.lines[0].pct = 18; save(); render(); await sleep(300);")
    tot = await js(pg, FIND + "const [c, i] = cur(); return docTotal(i).total;")
    c.ok(abs(tot - 96440) < 0.01, f"[{tag}] 3: the revision is $96,440, $560 less ({tot})")
    await send_editor(pg)
    await finish_send(pg)
    s = await js(pg, FIND + "const [c, i] = fi('INV-2026-031-R1'); return { st: i.status, paid: invoicePaid(c, i), credit: clientCredit(c).onAccount };")
    c.ok(s['st'] == 'paid' and abs(s['paid'] - 96440) < 0.01 and abs(s['credit'] - 560) < 0.01, f"[{tag}] 3: it settles $96,440 and the $560 is the client's credit on account ({s})")
    await open_doc(pg, 'invoice', 'INV-2026-031-R1')
    note = await js(pg, "const d = document.getElementById('dv'); return d ? d.textContent : '';")
    c.ok('$560' in note and 'credit on account' in note and 'Refund' in note and 'Apply to an Open Invoice' in note, f"[{tag}] 3: the viewer says it, with Refund and Apply")
    # apply it, then reverse the application from the invoice it is on (billing's own screen)
    await pg.locator('#dv [data-dvact="applycredit"]').first.click(); await pg.wait_for_timeout(500)
    m = await modal(pg)
    c.ok(m and m['h'] == 'Apply Credit on Account', f"[{tag}] 3: Apply opens its sheet ({m and m['h']})")
    # the invoice that owes the most
    num = await js(pg, """const s = document.querySelector('#mbm [data-f="inv"]'); if (!s) return '';
      const o = [...s.options].map(o => ({ v: o.value, n: o.textContent.split(' ')[0], owed: +o.textContent.replace(/.*· \\$([\\d,.]+) owed.*/, '$1').replace(/,/g, '') })).sort((a, b) => b.owed - a.owed)[0];
      s.value = o.v; return o.n;""")
    await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(700)
    ap = await js(pg, FIND + "const [c, i] = fi(arg); const A = c.payments.filter(p => p.invoiceId === i.id && p.creditApply); return { credit: clientCredit(c).onAccount, app: A.map(p => p.id), used: A.reduce((a, p) => a + p.amount, 0) };", num)
    c.ok(len(ap['app']) == 1 and ap['used'] > 0 and abs(ap['credit'] + ap['used'] - 560) < 0.01, f"[{tag}] 3: the credit is applied to {num}, the account less by what it used ({ap})")
    rows = await js(pg, "return acDocs('', 'all').filter(x => x.kind === 'payment' && x.py && x.py.creditApply).map(x => x.status);")
    c.ok(rows and all(x.startswith('Applied credit') for x in rows), f"[{tag}] 7: a credit application reads as applied credit, never In the bank ({rows})")
    await open_doc(pg, 'invoice', num)
    rv = pg.locator('#dv [data-dvact^="payrev:"]')
    c.ok(await rv.count() == 1, f"[{tag}] 9: the invoice the credit is applied to offers Reverse to billing")
    if await rv.count():
        await rv.first.click(); await pg.wait_for_timeout(500)
        await pg.locator('#mbm [data-f="why"]').fill('applied to the wrong invoice'); await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(600)
        back = await js(pg, FIND + "const [c, i] = fi('INV-2026-031-R1'); return clientCredit(c).onAccount;")
        c.ok(abs(back - 560) < 0.01, f"[{tag}] 9: reversed, the $560 is on the account again ({back})")
    c.ok(not errs, f'[{tag}] 3: page errors: {errs[:2]}')
    await b.close()


async def t4_second(p, c, phone, choice, est='EST-13881'):
    tag = 'phone' if phone else 'desktop'
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, 'u_billing')
    ST = """const c = DB.clients.find(x => x.estimates.some(e => e.number === 'EST-2026-014')); const sv = c.sov.filter(v => v.source === 'Contract' && v.projectId === 'p121');
      return { n: sv.length, amt: Math.round(sv.reduce((a, v) => a + (+v.scheduled || 0), 0)), rtb: Math.round(jobReadyToBill('p121').amt), cos: c.changeOrders.length };"""
    if est == 'copy':
        await open_doc(pg, 'estimate', 'EST-2026-D45')
        await dv_do(pg, 'Duplicate')
        await pg.locator('#mbm [data-dupall]').check(); await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(900)
        est = await js(pg, "for (const c of DB.clients) for (const e of c.estimates) if (docOpen && e.id === docOpen.id) return e.number;")
    before = await js(pg, ST)
    await js(pg, FIND + "const [c, e] = fe(arg); e.status = 'sent'; e.sentAt = '2026-09-02'; save();", est)
    await open_doc(pg, 'estimate', est)
    await dv_do(pg, 'Record Client Approval')
    await pg.locator('#mbm [data-f="why"]').fill('signed PDF by email'); await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(900)
    m = await modal(pg)
    c.ok(m and m['h'] == f'What Is {est}?' and m['sw'] <= (390 if phone else 1440), f"[{tag}] 4: approving {est} asks what it is ({m and (m['h'], m['sw'])})")
    mid = await js(pg, ST)
    st = await js(pg, FIND + "const [c, e] = fe(arg); return e.status;", est)
    c.ok(mid == before and st == 'sent', f"[{tag}] 4: nothing changes until the person chooses ({mid}, {st})")
    await pg.locator(f'#mbm [data-f2="{choice}"]').check()
    await pg.locator('#mbm [data-f="why"]').fill('as the client asked'); await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(1500)
    m2 = await modal(pg)
    if m2 and 'Confirm' in m2['h']:
        await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(1000)
    after = await js(pg, ST)
    e = await js(pg, FIND + "const [c, e] = fe(arg); return { st: e.status, as: e.contractAs && e.contractAs.as, co: e.becameCo || '' };", est)
    if est == 'EST-13881':
        if choice == 'co':
            c.ok(e['st'] == 'sent' and e['co'] and after['n'] == before['n'] and after['cos'] == before['cos'] + 1, f"[{tag}] 4: as a change order: a CO is drafted, the contract is as it was ({e}, {after})")
        elif choice == 'separate':
            c.ok(e['st'] == 'converted' and after['n'] == before['n'] + 45, f"[{tag}] 4: as a separate contract its lines go beside the contract's ({before} -> {after})")
        else:
            c.ok(e['st'] == 'converted' and e['as'] == 'replace', f"[{tag}] 4: as a replacement it is recorded so ({e}, {after})")
    else:
        c.ok(e['as'] == choice, f"[{tag}] 4: the copy of the signed EST-2026-D45 is asked the same and recorded ({e})")
    c.ok(not errs, f'[{tag}] 4: page errors: {errs[:2]}')
    await b.close()


async def t5_order(p, c):
    out = {}
    for order in ('draftfirst', 'cofirst'):
        b, pg, errs = await open_app(p)
        await sign_in(pg, 'u_billing')
        r = await js(pg, """const c = DB.clients.find(x => (x.changeOrders || []).some(o => o.number === 'CO-2026-001')); const co = c.changeOrders.find(o => o.number === 'CO-2026-001');
          if (arg === 'draftfirst') { blDraftApplication('p121'); await sleep(300); await docAction(c, co, 'progress'); }
          else { await docAction(c, co, 'progress'); await sleep(300); blDraftApplication('p121'); }
          await sleep(300);
          const co2 = c.changeOrders.find(o => o.number === 'CO-2026-002'); co2.status = 'sent'; await docAction(c, co2, 'approve'); await sleep(200); await docAction(c, co2, 'progress'); await sleep(300);
          const i = c.invoices.find(x => x.mode === 'sov' && x.status === 'draft');
          return { total: docTotal(i).total, lines: i.lines.filter(l => +l.pct > 0).map(l => l.item.slice(0, 20) + ' ' + l.pct).sort(), co2: (i.lines.find(l => /CO-2026-002/.test(l.item)) || {}).pct, n: c.invoices.filter(x => x.mode === 'sov' && x.status === 'draft').length };""", order)
        out[order] = r
        c.ok(not errs, f'5 [{order}]: page errors: {errs[:2]}')
        await b.close()
    a, z = out['draftfirst'], out['cofirst']
    c.ok(abs(a['total'] - z['total']) < 0.01 and a['lines'] == z['lines'] and a['n'] == 1 and z['n'] == 1, f"5: either order gives the same one application ({a} / {z})")
    c.ok(a['co2'] == 0 and z['co2'] == 0, f"5: CO-2026-002 starts at its measured 0%, not the job's percent ({a['co2']}, {z['co2']})")


async def main():
    only = sys.argv[1] if len(sys.argv) > 1 else ''
    c = Checks()
    async with async_playwright() as p:
        for phone in (False, True):
            if only in ('', '1'):
                print(f"-- 1. the cap at send, {'phone' if phone else 'desktop'}")
                await t1_cap(p, c, phone)
                await t1_dup_signoff(p, c, phone)
            if only in ('', '2'):
                print(f"-- 2. billed is read from invoices that exist, {'phone' if phone else 'desktop'}")
                await t2_deleted(p, c, phone)
            if only in ('', '3'):
                print(f"-- 3, 6-9. a paid invoice revised down, {'phone' if phone else 'desktop'}")
                await t3_revise_paid(p, c, phone)
            if only in ('', '4'):
                print(f"-- 4. a second estimate on a billed job, {'phone' if phone else 'desktop'}")
                await t4_second(p, c, phone, 'separate')
                if not phone:
                    await t4_second(p, c, phone, 'co')
                    await t4_second(p, c, phone, 'replace')
                    await t4_second(p, c, phone, 'separate', 'copy')
        if only in ('', '5'):
            print('-- 5. Bill It and Draft in either order')
            await t5_order(p, c)
    raise SystemExit(c.done())

if __name__ == '__main__':
    asyncio.run(main())
