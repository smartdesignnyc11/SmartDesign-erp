"""The cap reads every dollar; a replacement replaces (billing re-walk 4, 11-18). Invented demo data only.
Driven as billing (u_billing) through the screens, on the desktop and the phone.

1  S1-1, a typed line escapes the cap. The $17,080 "At filing" draft of EST-2026-D45 from the Billing Queue, Add Line,
   "Additional design services" $25,200 typed in the editor, Send to Client: it went out with no question and the fee
   was billed $63,630 of $42,700. The gate now reads the whole invoice (typed lines, deposits, retainers, linked lines)
   against the contract in force less everything billed on the job, and against what is earned: More Than Is Earned,
   $25,200, said in the editor while it is typed. Lower It lowers the typed line (the total goes back to $17,080);
   billing ahead with a reason sends it, and the reason shows on the invoice viewer and on the billed-ahead row of
   billing's Home, with the one figure the gate said ($25,200; Home read $2,100 at boot and $34,489 after).
2  S1-2 and S2-1, after a replacement the queue offered the old contract's deposit and milestones. A copy of the signed
   EST-2026-D45 keeps its template and milestones and the "What Is" sheet says it is the same as the signed contract;
   approved as the replacement, the queue offers only the new contract's next milestone, the old one's Bill the
   Milestone is stopped at send, and a deposit drafted past the contract (the walker's Simple copy) is stopped too.
3  S1-3, a replacement added its schedule to the old one (121 State $1,316,352, the same as a separate contract). The
   sheet shows before and after; after, the contract is EST-13881 plus the approved change order ($831,352), the 13 old
   lines are retired to history with what was billed on them, and that billing is carried onto the new lines as
   billed to date, so Ready to Bill does not bill the same work twice.
4  S2-3, Receivables ties with a credit on account unapplied (ledger 1100 = open invoices less unapplied credits), and
   the Collections panel shows the credit.
5  S2-4, Apply Credit defaults to the invoice that owes the most, never to a $0 one, and says the cents.
6  S3, Mark Sent's Sent On is today; a paid revision's send sheet does not say "for payment"; a revision's Date field
   and its note agree and change while an amount is typed; a locked month says so on the revision.
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
  const cure = () => { for (const c of DB.clients) for (const e of (c.estimates || [])) if (docOpen && e.id === docOpen.id) return [c, e]; return [null, null]; };
"""
MODAL = "const m = document.getElementById('mbm'); return m && m.isConnected && getComputedStyle(m).display !== 'none' ? { h: (m.querySelector('h3') || {}).textContent || '', t: m.textContent, ok: (m.querySelector('#mbm-ok') || {}).textContent || '', alt: (m.querySelector('#mbm-alt') || {}).textContent || '', sw: document.documentElement.scrollWidth } : null;"
TOAST = "return [...document.querySelectorAll('.toast, #toast')].map(e => e.textContent).join(' || ');"


async def modal(pg):
    await pg.wait_for_timeout(250)
    return await js(pg, MODAL)


async def reset(pg):
    await js(pg, "try { dvClose(); } catch (e) {} try { mbCloseModal(); } catch (e) {} docOpen = null; clientOpen = null; view = 'billing'; render(); await sleep(300);")


async def open_doc(pg, kind, n):
    await js(pg, FIND + "const [c, d] = arg[0] === 'estimate' ? fe(arg[1]) : fi(arg[1]); try { dvClose(); } catch (e) {} dvOpen(arg[0], d.id, c.id); await sleep(700);", [kind, n])


async def dv_do(pg, label):
    b = pg.locator('#dv .dv-bar button:visible, #dv .dv-menu button:visible').filter(has_text=label)
    if await b.count() == 0:
        await pg.locator('#dv [data-dvact="more"]').click(); await pg.wait_for_timeout(250)
        b = pg.locator('#dv .dv-menu button').filter(has_text=label)
    if await b.count() == 0:
        return False
    await b.first.click(); await pg.wait_for_timeout(800)
    return True


async def send_editor(pg):
    await pg.locator('button:visible', has_text='Send to Client').first.click()
    await pg.wait_for_timeout(700)
    return await modal(pg)


async def finish_send(pg):
    m = await modal(pg)
    if m and m['h'].startswith('Send to Client'):
        to = pg.locator('#mbm [data-f="to"]')
        if await to.count() and not await to.input_value():
            await to.fill('client@example.com')
        await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(1000)
        return True
    return False


async def queue_draft(pg, text):
    """The Billing Queue row that says `text`, its Draft."""
    await reset(pg)
    row = pg.locator('text=' + text).locator('xpath=ancestor::*[.//button][1]')
    if not await row.count():
        return False
    await row.locator('button:visible', has_text='Draft').first.click(); await pg.wait_for_timeout(1200)
    return True


async def type_line(pg, item, amount, tab=True):
    """Add Line in the editor and type the item and its rate, as a person does."""
    await pg.locator('button:visible', has_text='Add Line').first.click(); await pg.wait_for_timeout(700)
    last = pg.locator('tr[data-line]').last
    await last.locator('input[data-f="item"]').fill(item)
    rate = last.locator('input[data-f="rate"]')
    await rate.click(); await rate.fill('')
    await rate.type(str(amount), delay=20)
    if tab:
        await rate.press('Tab')
    await pg.wait_for_timeout(700)


async def banner(pg):
    return await js(pg, "const e = document.getElementById('pb-ahead-total'); return e ? e.textContent : '';")


async def t0_boot(p, c):
    b, pg, errs = await open_app(p)
    await sign_in(pg, 'u_billing')
    A = await js(pg, "const A = pbAhead('p45'); return { total: A.total, n: A.lines.length };")
    c.ok(A['total'] == 0, f"5: 45 Cranberry's paid signing milestone is not billed ahead at boot ({A}; it read $2,100 on one schedule line)")
    await js(pg, "view = 'home'; render(); await sleep(400);")
    t = await js(pg, "return document.body.innerText;")
    c.ok('Billed ahead: 45 Cranberry' not in t, "5: billing's Home has no billed-ahead row for 45 Cranberry at boot")
    c.ok(not errs, f'0: page errors: {errs[:2]}')
    await b.close()


async def t1_typed(p, c, phone):
    tag = 'phone' if phone else 'desktop'
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, 'u_billing')
    ok = await queue_draft(pg, '$17,080 ready to bill · 45 Cranberry St')
    c.ok(ok, f"[{tag}] 1: the queue offers the $17,080 filing milestone with Draft")
    await pg.locator('button.primary:visible', has_text='New Invoice').first.click(); await pg.wait_for_timeout(1500)
    n = await js(pg, FIND + "const [c, i] = cur(); return i && i.number;")
    # typed, not yet tabbed out: the editor already says it (S3: the banner showed only after a redraw)
    await type_line(pg, 'Additional design services', 25200, tab=False)
    await pg.wait_for_timeout(600)
    ban = await banner(pg)
    c.ok('$25,200' in ban and 'typed lines' in ban, f"[{tag}] 1/8: while the rate is typed the editor says $25,200 over, on typed lines ({ban[:200]})")
    await pg.locator('tr[data-line]').last.locator('input[data-f="rate"]').press('Tab'); await pg.wait_for_timeout(600)
    s = await js(pg, FIND + "const [c, i] = fi(arg); return { total: docTotal(i).total, typed: i.lines.filter(l => !l.fromLine).map(l => [l.item, l.rate]) };", n)
    c.ok(abs(s['total'] - 42280) < 0.01 and ['Additional design services', 25200] in s['typed'], f"[{tag}] 1: the line is typed through the editor, $42,280 in all ({s})")
    m = await send_editor(pg)
    c.ok(m and 'More Than Is Earned' in m['h'] and '$25,200' in m['t'] and 'typed lines' in m['t'] and '$63,630' not in m['t'],
         f"[{tag}] 1: Send asks: $25,200 over what is earned, on typed lines ({m and m['h']} | {m and m['t'][:300]})")
    c.ok(m and m['ok'] == 'Lower It' and m['sw'] <= (390 if phone else 1440), f"[{tag}] 1: Lower It is the blue; no sideways scroll ({m and (m['ok'], m['sw'])})")
    # Lower It lowers: the typed line goes to what is earned on it ($0), the total back to $17,080
    await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(1200)
    s = await js(pg, FIND + "const [c, i] = fi(arg); return { st: i.status, total: docTotal(i).total, typed: i.lines.filter(l => !l.fromLine).map(l => [l.item, l.rate]) };", n)
    tt = await js(pg, TOAST)
    c.ok(s['st'] == 'draft' and abs(s['total'] - 17080) < 0.01 and ['Additional design services', 0] in s['typed'], f"[{tag}] 5: Lower It lowers the typed line, $17,080 left ({s})")
    c.ok('lowered' in tt and '$25,200' in tt, f"[{tag}] 5: the toast says what was lowered ({tt[:200]})")
    c.ok(not await banner(pg), f"[{tag}] 1: lowered, the editor no longer says over")
    # raise it again, and bill ahead with a reason
    rate = pg.locator('tr[data-line]').last.locator('input[data-f="rate"]')
    await rate.click(); await rate.fill(''); await rate.type('25200', delay=20); await rate.press('Tab'); await pg.wait_for_timeout(700)
    m = await send_editor(pg)
    c.ok(m and 'More Than Is Earned' in m['h'], f"[{tag}] 1: raised again, Send asks again")
    await pg.locator('#mbm #mbm-alt').click(); await pg.wait_for_timeout(400)
    m = await modal(pg)
    c.ok(m and 'More Than Is Earned' in m['h'], f"[{tag}] 1: billing ahead with no reason is refused")
    await pg.locator('#mbm [data-f="why"]').fill('the client asked for the extra design work on one invoice')
    await pg.locator('#mbm #mbm-alt').click(); await pg.wait_for_timeout(900)
    await finish_send(pg)
    s = await js(pg, FIND + "const [c, i] = fi(arg); return { st: i.status, over: i.aheadWhy && i.aheadWhy.over, amt: i.aheadWhy && i.aheadWhy.amount };", n)
    c.ok(s['st'] == 'sent' and s['over'] == 'earned' and abs((s['amt'] or 0) - 25200) < 0.01, f"[{tag}] 1: with the reason it goes out, the reason recorded with $25,200 ({s})")
    # one figure: the gate's $25,200 is the job's billed ahead on Home, with the reason
    A = await js(pg, "const A = pbAhead('p45'); return { total: A.total, n: A.lines.length };")
    c.ok(abs(A['total'] - 25200) < 0.01, f"[{tag}] 5: the job's billed ahead is the gate's figure, $25,200 ({A}; Home read $34,489 on 3 lines)")
    await js(pg, "try { dvClose(); } catch (e) {} docOpen = null; clientOpen = null; view = 'home'; render(); await sleep(500);")
    t = await js(pg, "return document.body.innerText;")
    line = [x for x in t.split('\n') if '45 Cranberry' in x and 'ahead' in x.lower()]
    c.ok(any('$25,200' in x for x in line) and 'Reason: the client asked' in t, f"[{tag}] 5: billing's Home row says $25,200 and leads with the reason ({line[:3]})")
    await open_doc(pg, 'invoice', n)
    dv = await js(pg, "const d = document.getElementById('dv'); return d ? d.textContent : '';")
    c.ok('extra design work' in dv and '$25,200' in dv, f"[{tag}] 5: the invoice viewer shows the reason to bill ahead (not only View History)")
    await sign_in(pg, 'u_alan')
    await js(pg, "try { dvClose(); } catch (e) {} view = 'home'; render(); await sleep(500);")
    t = await js(pg, "return document.body.innerText;")
    c.ok('$34,489' not in t and '$2,100' not in t, f"[{tag}] 5: the PM's Home says no other billed-ahead figure for 45 Cranberry")
    c.ok(not errs, f'[{tag}] 1: page errors: {errs[:2]}')
    await b.close()


async def approve_as(pg, est, choice, why='as the client asked'):
    """Mark Sent, Record Client Approval, the What Is sheet: choose and continue. Returns the sheet's text."""
    await open_doc(pg, 'estimate', est)
    await js(pg, FIND + "const [c, e] = fe(arg); if (e.status === 'draft') { docAction(c, e, 'marksent'); } await sleep(400);", est)
    m = await modal(pg)
    if m and m['h'].startswith('Mark Sent'):
        await pg.locator('#mbm select').first.select_option(index=1)
        await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(1200)
    await open_doc(pg, 'estimate', est)
    await dv_do(pg, 'Record Client Approval')
    await pg.locator('#mbm [data-f="why"]').fill('signed PDF by email'); await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(1200)
    m = await modal(pg)
    sheet = m and m['t'] or ''
    if m and m['h'].startswith('What Is'):
        await pg.locator(f'#mbm [data-f2="{choice}"]').check()
        await pg.locator('#mbm [data-f="why"]').fill(why); await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(1800)
        m2 = await modal(pg)
        if m2 and 'Confirm' in m2['h']:
            await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(1000)
    return sheet, m


async def t2_copy_replace(p, c, phone):
    tag = 'phone' if phone else 'desktop'
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, 'u_billing')
    await open_doc(pg, 'estimate', 'EST-2026-D45')
    await dv_do(pg, 'Duplicate')
    await pg.locator('#mbm [data-dupall]').check(); await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(1000)
    e = await js(pg, FIND + "const [c, e] = cure(); return e && { n: e.number, tmpl: e.template || null, billing: e.billing || null, ms: (e.milestones || []).length, copyOf: e.copyOf };")
    c.ok(e and e['tmpl'] == 'design' and e['billing'] == 'milestones' and e['ms'] == 3 and e['copyOf'] == 'EST-2026-D45', f"[{tag}] 4: the copy of the signed design estimate keeps its template and milestones ({e})")
    sheet, m = await approve_as(pg, e['n'], 'replace')
    c.ok('is the same as the signed EST-2026-D45' in sheet, f"[{tag}] 4: the What Is sheet says the copy is the same as the signed contract ({sheet[:400]})")
    c.ok('Before:' in sheet and 'After:' in sheet, f"[{tag}] 3: the sheet shows the before and the after")
    c.ok(m and m['sw'] <= (390 if phone else 1440), f"[{tag}] 3: the sheet does not scroll sideways ({m and m['sw']})")
    st = await js(pg, FIND + "const [c, e] = fe(arg); const [c0, o] = fe('EST-2026-D45'); return { st: e.status, as: e.contractAs && e.contractAs.as, old: o.replacedBy || '' };", e['n'])
    c.ok(st['as'] == 'replace' and st['old'] == e['n'], f"[{tag}] 2: approved as the replacement, the old contract is marked replaced ({st})")
    # the queue reads the contract in force: only the new contract's next milestone, no deposit, nothing of the old
    rows = await js(pg, "return jobReadyToBill('p45').rows.map(r => [r.kind, Math.round(r.amount), r.d && r.d.number]);")
    c.ok(rows == [['dmilestone', 17080, e['n']]], f"[{tag}] 2: Ready to Bill offers the new contract's filing milestone only ({rows})")
    await reset(pg)
    t = await js(pg, "return document.body.innerText;")
    c.ok('$10,675' not in t, f"[{tag}] 2: the Billing Queue offers no old 25% deposit")
    # the old contract's Bill the Milestone, if pressed, is stopped at send
    await open_doc(pg, 'estimate', 'EST-2026-D45')
    bar = await js(pg, "return [...document.querySelectorAll('#dv .dv-bar button')].map(b => b.textContent.trim());")
    if 'Bill the Milestone' in bar:
        await pg.locator('#dv .dv-bar button', has_text='Bill the Milestone').first.click(); await pg.wait_for_timeout(900)
        await pg.locator('#mbm [name=dms][value="2"]').check(); await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(1200)
        m = await send_editor(pg)
        c.ok(m and 'More Than Is Earned' in m['h'], f"[{tag}] 2: the replaced contract's sign-off milestone is stopped at send ({m and m['h']})")
        await js(pg, "try { mbCloseModal(); } catch (e) {}")
    else:
        c.ok(True, '')
    c.ok(not errs, f'[{tag}] 2: page errors: {errs[:2]}')
    await b.close()


async def t2_simple_copy_deposit(p, c):
    """The walker's case: a copy made before copies kept their template (a Simple estimate), approved as the
    replacement and converted at 50%; then a deposit draft. Any deposit past the contract stops at send."""
    b, pg, errs = await open_app(p)
    await sign_in(pg, 'u_billing')
    await open_doc(pg, 'estimate', 'EST-2026-D45')
    await dv_do(pg, 'Duplicate')
    await pg.locator('#mbm [data-dupall]').check(); await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(1000)
    n = await js(pg, FIND + "const [c, e] = cure(); delete e.template; delete e.billing; delete e.milestones; save(); return e.number;")
    await approve_as(pg, n, 'replace')
    await open_doc(pg, 'estimate', n)
    await pg.locator('#dv .dv-bar button.primary').first.click(); await pg.wait_for_timeout(1000)
    pct = pg.locator('#mbm input[type=number], #mbm input.num').first
    await pct.fill('50'); await pct.press('Tab'); await pg.wait_for_timeout(300)
    await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(1500)
    inv = await js(pg, FIND + "const [c, i] = cur(); return i && { n: i.number, total: docTotal(i).total };")
    c.ok(inv and abs(inv['total'] - 21350) < 0.01, f"2: the replacement converted at 50% is $21,350 ({inv})")
    m = await send_editor(pg)
    c.ok(m and m['h'].startswith('Send to Client'), f"2: within the contract it sends ({m and m['h']})")
    await finish_send(pg)
    rows = await js(pg, "return jobReadyToBill('p45').rows.map(r => [r.kind, Math.round(r.amount)]);")
    c.ok(not any(r[0] == 'deposit' for r in rows), f"2: with the contract billed in full the queue offers no deposit ({rows})")
    # a deposit draft on the replacement, as the queue drafted it on the walk: stopped at send, $10,675 over the contract
    await js(pg, FIND + """const [c, e] = fe(arg); const inv = newDoc(c, 'invoice', { mode: 'items', fields: { projectId: e.projectId, title: 'Deposit', lines: [{ id: uid('l'), item: 'Deposit at signing', qty: 1, unit: 'ls', rate: 10675, taxable: false }], retainagePct: 0 } });
      inv.depositOf = e.id; inv.isDeposit = true; inv.projectId = e.projectId; save(); return inv.number;""", n)
    dn = await js(pg, FIND + "for (const c of DB.clients) for (const i of c.invoices) if (i.isDeposit && i.status === 'draft' && i.projectId === 'p45') return i.number; return null;")
    await open_doc(pg, 'invoice', dn)
    await dv_do(pg, 'Send to Client')
    m = await modal(pg)
    c.ok(m and 'More Than Is Earned' in m['h'] and '$10,675' in m['t'] and 'the contract' in m['t'], f"2: a deposit past the contract stops at send, $10,675 over ({m and m['t'][:300]})")
    await js(pg, "try { mbCloseModal(); } catch (e) {}")
    c.ok(not errs, f'2: page errors: {errs[:2]}')
    await b.close()


async def t3_replace(p, c, phone):
    tag = 'phone' if phone else 'desktop'
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, 'u_billing')
    ST = """const c = DB.clients.find(x => x.id === 'cl121'); const sv = c.sov.filter(v => v.projectId === 'p121');
      return { n: sv.length, amt: Math.round(sv.reduce((a, v) => a + (+v.scheduled || 0), 0)), billed: Math.round(sv.reduce((a, v) => a + (+v.scheduled || 0) * sovBilled(c, v.id) / 100, 0)),
        retired: (c.sovRetired || []).filter(v => v.projectId === 'p121').map(v => v.retired && v.retired.by), rtb: Math.round(jobReadyToBill('p121').amt), contract: Math.round(jobFin(DB.projects.find(p => p.id === 'p121')).contract),
        billedJob: Math.round(jobFin(DB.projects.find(p => p.id === 'p121')).billed) };"""
    before = await js(pg, ST)
    sheet, m = await approve_as(pg, 'EST-13881', 'replace')
    c.ok('Before: contract $491,200' in sheet and 'After: contract $831,352' in sheet and '13 lines leave the schedule' in sheet,
         f"[{tag}] 3: the sheet shows before ($491,200) and after ($831,352, the 13 old lines retired) ({sheet[sheet.find('A Replacement'):][:600]})")
    c.ok(m and m['sw'] <= (390 if phone else 1440), f"[{tag}] 3: no sideways scroll ({m and m['sw']})")
    after = await js(pg, ST)
    c.ok(after['contract'] == 831352, f"[{tag}] 3: the contract is EST-13881 plus the approved change order, $831,352 ({before['contract']} -> {after['contract']}; was $1,316,352)")
    c.ok(after['n'] == 46 and after['amt'] == 831352, f"[{tag}] 3: the schedule is the new estimate's 45 lines and the change order's ({after['n']} lines, {after['amt']})")
    c.ok(len(after['retired']) == 13 and set(after['retired']) == {'EST-13881'}, f"[{tag}] 3: the 13 old lines are kept in history, retired by EST-13881 ({after['retired'][:3]})")
    c.ok(abs(after['billed'] - before['billed']) <= 2 and after['billedJob'] == before['billedJob'], f"[{tag}] 3: what was billed stays billed and is carried onto the new lines ({before['billed']} -> {after['billed']}; job {after['billedJob']})")
    c.ok(after['rtb'] <= before['rtb'], f"[{tag}] 3: Ready to Bill reads the new schedule less what was billed, never the same work twice ({before['rtb']} -> {after['rtb']}; was 56,862)")
    # the old invoices still read as sent
    old = await js(pg, FIND + "const [c, i] = fi('INV-2026-038'); return { st: i.status, total: docTotal(i).total };")
    c.ok(old['st'] == 'sent' and abs(old['total'] - 68265) < 0.01, f"[{tag}] 3: the old contract's invoices stand as sent ({old})")
    c.ok(not errs, f'[{tag}] 3: page errors: {errs[:2]}')
    await b.close()


async def revise_031(pg, pct=None):
    await open_doc(pg, 'invoice', 'INV-2026-031')
    await dv_do(pg, 'Edit')
    await pg.locator('#mbm [data-f="why"]').fill('wrong percent on demolition'); await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(1200)


async def t4_credit(p, c, phone):
    tag = 'phone' if phone else 'desktop'
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, 'u_billing')
    await revise_031(pg)
    # S3: the Date field and the note agree while no amount changes
    dt = await js(pg, "const i = document.querySelector('input[data-d=\"date\"]'); const w = document.querySelector('[data-revdate]'); return { v: i && i.value, ro: i && i.readOnly, w: w ? w.textContent : '' };")
    c.ok(dt['v'] == '2026-08-01' and dt['ro'] and 'Aug 1' in dt['w'], f"[{tag}] 8: no amount changed: the Date field reads 8/1, as the note says ({dt})")
    pct = pg.locator('input[data-f="pct"]').first
    await pct.click(); await pct.fill(''); await pct.type('18', delay=30); await pg.wait_for_timeout(700)
    dt = await js(pg, "const i = document.querySelector('input[data-d=\"date\"]'); const w = document.querySelector('[data-revdate]'); return { v: i && i.value, ro: i && i.readOnly, w: w ? w.textContent : '' };")
    c.ok(dt['v'] == '2026-09-03' and not dt['ro'] and 'changes an amount' in dt['w'] and 'Sep 3' in dt['w'], f"[{tag}] 8: an amount typed, the field and the note change to 9/3 while it is typed ({dt})")
    await pct.press('Tab'); await pg.wait_for_timeout(500)
    m = await send_editor(pg)
    c.ok(m and m['h'].startswith('Send to Client') and 'for payment' not in m['t'] and 'as paid' in m['t'], f"[{tag}] 8: the paid revision's send sheet says it goes as paid, not for payment ({m and m['t'][-260:]})")
    body = await js(pg, "const t = document.querySelector('#mbm [data-f=\"body\"]'); return t ? t.value : '';")
    c.ok('pay it from your portal' not in body and 'nothing is due' in body, f"[{tag}] 8: the email says nothing is due ({body[:200]})")
    await finish_send(pg)
    cr = await js(pg, FIND + "const [c, i] = fi('INV-2026-031-R1'); return clientCredit(c).onAccount;")
    c.ok(abs(cr - 560) < 0.01, f"[{tag}] 6: $560 is credit on account ({cr})")
    # S2-3: the Receivables tie reads the credit
    await js(pg, "try { dvClose(); } catch (e) {} docOpen = null; clientOpen = null; view = 'reports'; repTab = 'ar'; render(); await sleep(900);")
    t = await js(pg, "const e = document.getElementById('rep-print-area') || document.body; return e.innerText;")
    i0 = t.find('Receivables agree with the ledger')
    seg = t[i0:i0 + 700]
    c.ok(i0 >= 0 and 'Off by' not in seg and 'credits on account' in seg.lower() and '560' in seg, f"[{tag}] 6: the ledger tie has a credits-on-account line and ties ({seg[:400]})")
    # the Collections panel shows the credit
    await js(pg, "view = 'acbilling'; render(); await sleep(300);")
    h = await js(pg, "return typeof acBillingHtml === 'function' ? acBillingHtml() : '';")
    c.ok('Credit on account, not yet applied' in h and '$560' in h, f"[{tag}] 6: Collections shows the $560 credit")
    # S2-4: Apply Credit defaults to the invoice that owes the most; nothing reads $0
    await open_doc(pg, 'invoice', 'INV-2026-031-R1')
    await pg.locator('#dv [data-dvact="applycredit"]').first.click(); await pg.wait_for_timeout(600)
    opts = await js(pg, "const s = document.querySelector('#mbm [data-f=\"inv\"]'); return s ? { v: s.options[s.selectedIndex].textContent, all: [...s.options].map(o => o.textContent) } : null;")
    c.ok(opts and opts['v'].startswith('INV-2026-038') and not any('$0 owed' in o for o in opts['all']), f"[{tag}] 7: Apply Credit defaults to INV-2026-038 and says the cents ({opts})")
    await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(800)
    tt = await js(pg, TOAST)
    c.ok('$560.00 credit on account applied to INV-2026-038' in tt and '$0 credit' not in tt, f"[{tag}] 7: the toast says $560.00 applied ({tt[:160]})")
    c.ok(not errs, f'[{tag}] 6: page errors: {errs[:2]}')
    await b.close()


async def t6_sheets(p, c):
    b, pg, errs = await open_app(p)
    await sign_in(pg, 'u_billing')
    # Mark Sent's Sent On is today
    await js(pg, FIND + "const [c, e] = fe('EST-13881'); clientOpen = c.id; docOpen = { kind: 'estimate', id: e.id }; view = 'clients'; render(); await sleep(500); docAction(c, e, 'marksent'); await sleep(400);")
    v = await js(pg, "const i = document.querySelector('#mbm [data-f=\"on\"]'); return i ? i.value : null;")
    c.ok(v == '2026-09-03', f"8: Mark Sent's Sent On defaults to today, 9/3 ({v})")
    await js(pg, "try { mbCloseModal(); } catch (e) {}")
    # a locked month says so on the revision
    await sign_in(pg, 'u_controller')
    await js(pg, "glTab = 'periods'; view = 'gl'; render(); await sleep(600);")
    for sub in ('bank', 'ar'):
        bt = pg.locator(f'button[data-gllock="ent1|2026-07|{sub}"]')
        if await bt.count():
            await bt.first.click(); await pg.wait_for_timeout(500)
            if await modal(pg):
                f = pg.locator('#mbm input, #mbm textarea')
                if await f.count():
                    await f.first.fill('July is closed for the test')
                await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(500)
    lk = await js(pg, "return glLocked('2026-07-28', 'ent1', 'ar');")
    c.ok(lk, "8: July is locked for receivables")
    await sign_in(pg, 'u_billing')
    await open_doc(pg, 'invoice', 'INV-2026-D45-R')
    await dv_do(pg, 'Edit')
    await pg.locator('#mbm [data-f="why"]').fill('wrong amount'); await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(1200)
    rt = pg.locator('tr[data-line]').first.locator('input[data-f="rate"]')
    await rt.click(); await rt.fill(''); await rt.type('4500', delay=30); await rt.press('Tab'); await pg.wait_for_timeout(700)
    w = await js(pg, "const w = document.querySelector('[data-revdate]'); return w ? w.textContent : '';")
    c.ok('July is locked; this posts on Thu, Sep 3' in w, f"8: the revision says July is locked and it posts on 9/3 ({w})")
    c.ok(not errs, f'8: page errors: {errs[:2]}')
    await b.close()


async def main():
    only = sys.argv[1] if len(sys.argv) > 1 else ''
    c = Checks()
    async with async_playwright() as p:
        if only in ('', '0'):
            print('-- 0. boot')
            await t0_boot(p, c)
        for phone in (False, True):
            tag = 'phone' if phone else 'desktop'
            if only in ('', '1'):
                print(f'-- 1. a typed line, {tag}')
                await t1_typed(p, c, phone)
            if only in ('', '2'):
                print(f'-- 2. a copy approved as the replacement, {tag}')
                await t2_copy_replace(p, c, phone)
            if only in ('', '3'):
                print(f'-- 3. a replacement replaces, {tag}')
                await t3_replace(p, c, phone)
            if only in ('', '4'):
                print(f'-- 4. credit on account, {tag}')
                await t4_credit(p, c, phone)
        if only in ('', '2', '2s'):
            print('-- 2. the Simple copy and a deposit')
            await t2_simple_copy_deposit(p, c)
        if only in ('', '6'):
            print('-- 6. the sheets')
            await t6_sheets(p, c)
    raise SystemExit(c.done())

if __name__ == '__main__':
    asyncio.run(main())
