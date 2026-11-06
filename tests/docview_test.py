#!/usr/bin/env python3
"""tests/docview_test.py: open the document first (Alan, 11-06; src/docview.js).

"On the control and billing when you click an invoice, CO, estimate, etc - it should take you to a pdf and from the pdf,
you should have options to edit, create credit, refund, etc."

As billing (u_billing) and the controller (u_controller), on the desktop (1440) and the phone (390):
  - every list that opens a document opens the document as its recipient reads it (the Billing page, the job's
    Contract and Billing, Cmd-K, Ask's Open link, a bill on Accounting), never the editor; a document made this turn
    (Draft from the Billing queue) still opens in the editor;
  - the action set per type and status: one blue at most, a safe next step, never money out or destructive;
  - Edit on a sent invoice starts a linked revision with a required reason; the original is unchanged, and when the
    revision goes out the original is voided (its posting reversed in the ledger) and the money on it follows;
  - Create Credit: a credit memo in c.invoices, applied to its invoice; it reverses the invoice's sales tax and
    retainage, lowers an SOV line's billed to date, and AR ties out (the subledger and the ledger move together);
  - Refund: a proposal until the owner approves it (billing cannot), back to the account that paid, "approved, not in
    the bank" until a bank line on that account is matched; money the bank does not have is never refunded;
  - the phone: nothing scrolls sideways, the bar's targets are 44px or more and 8px apart; Download PDF gives a .pdf;
  - the client's portal opens the same document with the client's own actions.
Screenshots (deviceScaleFactor 2) go to review/docview/.
"""
import asyncio, os, re, sys, json
from harness import *

SHOTS = os.path.join(ROOT, 'review', 'docview')
os.makedirs(SHOTS, exist_ok=True)
C = Checks()
REC = "() => { const d = document.getElementById('dv'); return d ? d.dataset.rec : (docOpen ? 'editor:' + docOpen.kind + ':' + docOpen.id : 'none') }"
MONEY_OUT = {'refund', 'void', 'credit', 'bpay', 'bdispute', 'bcredit', 'pay'}


async def boot(p, phone, uid):
    b = await p.chromium.launch()
    vp = PHONE if phone else DESKTOP
    ctx = await b.new_context(viewport=vp, is_mobile=phone, has_touch=phone, device_scale_factor=2, accept_downloads=True)
    pg = await ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto(URL)
    await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
    await sign_in(pg, uid)
    return b, pg, errs


async def rec(pg):
    await pg.wait_for_timeout(250)
    return await pg.evaluate(REC)


async def dv_tap(pg, label):
    """a button in the viewer by its words; under More when the bar does not show it (the phone)"""
    loc = pg.locator('#dv .dv-hd [data-dvact], #dv .dv-bar [data-dvact], #dv .dv-menu [data-dvact], #dv .dv-notes [data-dvact]').filter(has_text=re.compile('^\\s*' + re.escape(label) + '\\s*$'))
    if not await loc.count():
        await pg.locator('#dv [data-dvact="more"]').click()
        await pg.wait_for_timeout(150)
        loc = pg.locator('#dv .dv-menu [data-dvact]').filter(has_text=re.compile('^\\s*' + re.escape(label) + '\\s*$'))
    await loc.first.click()
    await pg.wait_for_timeout(250)


async def shot(pg, name):
    await pg.screenshot(path=os.path.join(SHOTS, name + '.png'))


async def phone_layout(pg, tag):
    L = await pg.evaluate("""() => {
      const d = document.getElementById('dv'), body = d && d.querySelector('.dv-body');
      const B = [...d.querySelectorAll('.dv-bar button, .dv-menu button')].filter(b => b.offsetParent).map(b => b.getBoundingClientRect());
      const bar = [...d.querySelectorAll('.dv-bar button')].filter(b => b.offsetParent).map(b => b.getBoundingClientRect()).sort((a, b) => a.left - b.left);
      let gap = 99; for (let i = 1; i < bar.length; i++) gap = Math.min(gap, bar[i].left - bar[i - 1].right);
      return { sw: document.documentElement.scrollWidth, bw: body ? body.scrollWidth - body.clientWidth : 0, minH: Math.min(...B.map(r => r.height)), gap: gap,
               barBottom: Math.max(...bar.map(r => r.bottom)), vh: innerHeight };
    }""")
    C.ok(L['sw'] <= 390, f'{tag}: the page does not scroll sideways with the document open ({L["sw"]}px)')
    C.ok(L['bw'] <= 1, f'{tag}: the document reflows to the width, nothing in it scrolls sideways ({L["bw"]}px over)')
    C.ok(L['minH'] >= 44, f'{tag}: every target in the action bar and More is 44px or more ({L["minH"]:.0f}px)')
    C.ok(L['gap'] >= 8, f'{tag}: the bar\'s targets are 8px or more apart ({L["gap"]:.0f}px)')
    C.ok(L['vh'] - L['barBottom'] < 40, f'{tag}: the action bar sits at the bottom of the screen')


async def action_sets(pg, who):
    """the actions per type and status, read from the one decider (dvActions) the viewer draws"""
    A = await pg.evaluate("""() => {
      const out = {}, ids = r => dvActions(r).map(a => (a.blue ? '*' : '') + a.id + (a.more ? '+' : ''));
      const c121 = DB.clients.find(c => c.id === 'cl121');
      const draft = newDoc(c121, 'invoice', { mode: 'items', fields: { projectId: 'p121', title: 'fixture draft', lines: [{ id: 'lfx', item: 'Fixture', qty: 1, rate: 100, taxable: false }] } });
      dvFresh.delete(draft.id);
      const R = (k, id) => dvFind(k, id);
      out.inv_draft = ids(R('invoice', draft.id));
      out.inv_sent = ids(R('invoice', 'in3'));
      out.inv_paid = ids(R('invoice', 'in2'));
      out.inv_paid_unbanked = ids(R('invoice', 'inD45r'));
      out.est_draft = ids(R('estimate', 'es13881'));
      out.est_converted = ids(R('estimate', 'es1'));
      out.co_sent = ids(R('co', 'co2'));
      out.co_approved = ids(R('co', 'co1'));
      out.bill_pmok = ids(R('bill', 'b2'));
      out.bill_paid = ids(R('bill', 'b1'));
      out.bill_sub = ids(R('bill', 'b4'));
      c121.invoices.splice(c121.invoices.indexOf(draft), 1);
      return out;
    }""")
    for k, v in A.items():
        blue = [x for x in v if x.startswith('*')]
        C.ok(len(blue) <= 1, f'{who} {k}: one blue at most ({v})')
        C.ok(not any(x.strip('*+') in MONEY_OUT for x in blue), f'{who} {k}: the blue is never money out or destructive ({blue})')
        C.ok(all(x.endswith('+') for x in v if x.strip('*+') in MONEY_OUT), f'{who} {k}: money out and destructive actions sit under More ({v})')
    n = lambda k: [x.strip('*+') for x in A[k]]
    b = lambda k: next((x.strip('*+') for x in A[k] if x.startswith('*')), '')
    C.ok(b('inv_draft') == 'send' and 'edit' in n('inv_draft') and 'void' in n('inv_draft') and not {'credit', 'refund', 'pay'} & set(n('inv_draft')),
         f'{who} draft invoice: Send to Client blue, Edit in place, Void; no credit, refund or payment ({A["inv_draft"]})')
    C.ok(b('inv_sent') == 'findbank' and {'edit', 'email', 'pdf', 'pay', 'credit', 'print', 'history'} <= set(n('inv_sent')) and 'refund' not in n('inv_sent') and 'void' not in n('inv_sent'),
         f'{who} sent invoice: Find in Bank blue; Edit, Send, Download PDF, Record Payment, Create Credit, Print, View History; no Refund (nothing received), no Void ({A["inv_sent"]})')
    C.ok(not b('inv_paid') and {'edit', 'credit', 'refund', 'pdf', 'history'} <= set(n('inv_paid')) and 'pay' not in n('inv_paid'),
         f'{who} paid invoice: Edit, Create Credit, Refund, Download PDF; no Record Payment, no blue ({A["inv_paid"]})')
    C.ok('refund' not in n('inv_paid_unbanked'), f'{who} an invoice paid by money not in the bank offers no Refund ({A["inv_paid_unbanked"]})')
    C.ok(b('est_draft') == 'send' and 'edit' in n('est_draft') and 'dup' in n('est_draft'), f'{who} draft estimate: Send to Client blue, Edit, Duplicate ({A["est_draft"]})')
    C.ok('edit' not in n('est_converted') and 'newco' in n('est_converted'), f'{who} signed estimate: no Edit; New Change Order instead ({A["est_converted"]})')
    C.ok(b('co_sent') == 'approve' and 'edit' in n('co_sent'), f'{who} sent change order: Record Approval blue, Edit (a revision) ({A["co_sent"]})')
    C.ok(b('co_approved') == 'billco' and 'edit' not in n('co_approved'), f'{who} approved change order: Bill It blue, no Edit ({A["co_approved"]})')
    owner = who.startswith('owner')
    C.ok((('bapprove' in n('bill_pmok') and b('bill_pmok') == 'bapprove') if owner else 'bapprove' not in n('bill_pmok')) and 'bfile' in n('bill_pmok') and 'bdispute' in n('bill_pmok') and 'bcredit' in n('bill_pmok'),
         f'{who} a bill waiting on the owner: Approve only for the owner (blue); Vendor\'s Document, Dispute, Request Credit ({A["bill_pmok"]})')
    C.ok('bdispute' not in n('bill_paid') and 'bedit' not in n('bill_paid') and 'bpay' not in n('bill_paid'), f'{who} a paid bill: no Dispute, Edit or Pay ({A["bill_paid"]})')


async def lists_open(p, phone, uid):
    dev = 'phone' if phone else 'desktop'
    who = f'{uid[2:]} on the {dev}'
    b, pg, errs = await boot(p, phone, uid)
    # the Billing page: Collections and the document rows
    await go(pg, 'billing')
    await pg.locator('#v-billing tr[data-acopen="invoice:cl121:in3"]').first.click()
    r = await rec(pg)
    C.ok(r == 'invoice:in3', f'{who}: Billing\'s INV-2026-038 row opens the document, not the editor ({r})')
    t = await pg.evaluate("() => (document.querySelector('#dv .dv-doc') || {}).innerText || ''")
    C.ok('INV-2026-038' in t and re.search(r'bill to', t, re.I) and 'Application for Payment' in t and not await pg.locator('#dv input, #dv textarea').count(),
         f'{who}: the document is the client\'s render (letterhead, Bill to, the application), with nothing to type into')
    n = await pg.evaluate("() => (document.querySelector('#dv .dv-notes') || {}).innerText || ''")
    C.ok('billed ahead of the work' in n, f'{who}: the office sees the job billed ahead of the work above the document, not on the client\'s copy ({n[:100]})')
    st = await pg.evaluate("() => { dvOpen('invoice', 'inD45r', 'cl45'); return (document.querySelector('#dv .dv-st') || {}).textContent || '' }")
    C.ok('$5,000 recorded, not yet in the bank' in st, f'{who}: an invoice paid by money the bank has not seen says how much, never Paid ({st})')
    await pg.evaluate("() => dvOpen('invoice', 'in3', 'cl121')")
    await shot(pg, f'{uid}_{dev}_invoice')
    if phone:
        await phone_layout(pg, who + ' invoice')
        await pg.locator('#dv [data-dvact="more"]').click()
        await pg.wait_for_timeout(150)
        await phone_layout(pg, who + ' invoice with More open')
        await shot(pg, f'{uid}_{dev}_invoice_more')
        await pg.locator('#dv [data-dvact="more"]').click()
    # Download PDF: a real .pdf of the same document
    async with pg.expect_download() as dl:
        await dv_tap(pg, 'Download PDF')
    d = await dl.value
    path = await d.path()
    raw = open(path, 'rb').read()
    C.ok(raw.startswith(b'%PDF') and b'INV-2026-038' in raw and d.suggested_filename.endswith('.pdf'), f'{who}: Download PDF gives {d.suggested_filename}, a PDF with the invoice in it')
    await dv_tap(pg, 'Close')
    C.ok(await rec(pg) == 'none', f'{who}: Close puts the person back on the list')
    await pg.evaluate("() => { dvOpen('invoice', 'in3', 'cl121'); setView('bank'); }")
    C.ok(await rec(pg) == 'none', f'{who}: a move to another page (a link, a toast) closes the document over the old one')
    await go(pg, 'billing')
    for row, want in (('estimate:cl121:es1', 'estimate:es1'), ('co:cl121:co2', 'co:co2')):
        loc = pg.locator(f'#v-billing tr[data-acopen="{row}"]')
        if await loc.count():
            await loc.first.click()
            r = await rec(pg)
            C.ok(r == want, f'{who}: Billing\'s {row} row opens its document ({r})')
            if want == 'co:co2':
                await shot(pg, f'{uid}_{dev}_co')
            await pg.evaluate('dvClose()')
    # a bill (Accounting's bill rows, Ask's bill links: flowGo.bill)
    await pg.evaluate("() => flowGo.bill(DB.bills.find(b => b.id === 'b2'))()")
    r = await rec(pg)
    if uid == 'u_controller':
        C.ok(r == 'bill:b2', f'{who}: a bill opens as its document ({r})')
        t = await pg.evaluate("() => (document.querySelector('#dv .dv-doc') || {}).innerText || ''")
        C.ok('WW-2026-118' in t and 'Window Works' in t and 'vendor\'s own invoice is attached' in t.lower(), f'{who}: the bill reads as the vendor\'s invoice on file, with its attachment named')
        await shot(pg, f'{uid}_{dev}_bill')
        if phone: await phone_layout(pg, who + ' bill')
        await pg.evaluate('dvClose()')
    else:
        C.ok(r != 'bill:b2', f'{who}: billing keeps the bill sheet, where it enters and codes bills ({r})')
    await pg.evaluate("() => { dvClose(); try { closeEditor(); } catch (e) {} }")
    await action_sets(pg, who)
    if uid == 'u_billing':
        # the job's Contract and Billing
        await pg.evaluate("() => jpOpenJob('p121', 'jbill')")
        await pg.wait_for_timeout(300)
        loc = pg.locator('[data-jbdoc^="co:"]')
        C.ok(await loc.count() > 0, f'{who}: the job\'s Contract and Billing lists its change orders')
        if await loc.count():
            await loc.first.click()
            r = await rec(pg)
            C.ok(r.startswith('co:'), f'{who}: the job\'s change order row opens the document ({r})')
            await pg.evaluate('dvClose()')
        # a document made this turn opens in the editor: the queue's Draft
        await go(pg, 'billing')
        n0 = await pg.evaluate("() => DB.clients.reduce((a, c) => a + c.invoices.length, 0)")
        dr = pg.locator('#v-billing [data-blact^="rtb:"]')
        if await dr.count():
            await dr.first.click()
            await pg.wait_for_timeout(400)
            if await pg.locator('#mbm #mbm-ok').count(): await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(300)
            n1 = await pg.evaluate("() => DB.clients.reduce((a, c) => a + c.invoices.length, 0)")
            r = await rec(pg)
            C.ok(n1 > n0 and r.startswith('editor:'), f'{who}: Draft from the queue makes the invoice and opens its editor ({r})')
    if not phone:
        await pg.evaluate("() => { docOpen = null; dvClose(); view = 'billing'; render(); }")
        # Cmd-K
        await pg.keyboard.press('Control+k')
        await pg.wait_for_selector('#pal.on', timeout=5000)
        await pg.keyboard.type('INV-2026-038')
        await pg.wait_for_timeout(500)
        await pg.keyboard.press('Enter')
        await pg.wait_for_timeout(400)
        r = await rec(pg)
        C.ok(r == 'invoice:in3', f'{who}: Cmd-K\'s INV-2026-038 opens the document ({r})')
        await pg.evaluate('dvClose()')
        # Ask's Open link
        await go(pg, 'pa')
        await pg.locator('#pa-in').fill('what is the balance on INV-2026-038')
        await pg.keyboard.press('Enter')
        try:
            await pg.get_by_text('Open INV-2026-038').first.click(timeout=8000)
            r = await rec(pg)
        except Exception as e:
            r = 'no Open link: ' + str(e)[:80]
        C.ok(r == 'invoice:in3', f'{who}: Ask\'s Open INV-2026-038 opens the document ({r})')
    C.ok(not errs, f'{who}: no page errors ({errs[:2]})')
    await b.close()


async def revise(p, phone):
    dev = 'phone' if phone else 'desktop'
    b, pg, errs = await boot(p, phone, 'u_billing')
    await pg.evaluate("() => { const c = DB.clients.find(c => c.id === 'cl121'); clientOpen = c.id; docOpen = { kind: 'invoice', id: 'in3' }; view = 'billing'; render(); }")
    snap = "() => { const c = DB.clients.find(c => c.id === 'cl121'), d = c.invoices.find(i => i.id === 'in3'); return JSON.stringify({ n: d.number, l: d.lines, t: docTotal(d), date: d.date, due: d.due }) }"
    before = await pg.evaluate(snap)
    sb0 = await pg.evaluate("() => { const c = DB.clients.find(c => c.id === 'cl121'), d = c.invoices.find(i => i.id === 'in3'); return d.lines.map(l => r2(sovBilled(c, l.sovId))) }")
    C.ok(await rec(pg) == 'invoice:in3', f'billing on the {dev}: a set docOpen opens the document first')
    await dv_tap(pg, 'Edit')
    C.ok(await pg.locator('#mbm').count() == 1, f'billing on the {dev}: Edit on the sent INV-2026-038 asks why before anything changes')
    await pg.locator('#mbm #mbm-ok').click()
    await pg.wait_for_timeout(200)
    C.ok(await pg.evaluate("() => DB.clients.find(c => c.id === 'cl121').invoices.length") == 3, f'billing on the {dev}: no revision without a reason')
    await pg.locator('#mbm [data-f="why"]').fill('wrong percentage on the tile line')
    await pg.locator('#mbm #mbm-ok').click()
    r = await rec(pg)
    n = await pg.evaluate("() => { const c = DB.clients.find(c => c.id === 'cl121'), n = c.invoices.find(i => i.revisionOf === 'INV-2026-038'); return n ? { id: n.id, number: n.number, why: n.reviseReason, st: n.status } : null }")
    C.ok(n and n['why'] == 'wrong percentage on the tile line' and n['st'] == 'draft', f'billing on the {dev}: Edit starts {n and n["number"]}, a draft revision carrying the reason')
    C.ok(n and r == 'editor:invoice:' + n['id'], f'billing on the {dev}: the revision opens in the editor ({r})')
    C.ok(await pg.evaluate(snap) == before and await pg.evaluate("() => DB.clients.find(c => c.id === 'cl121').invoices.find(i => i.id === 'in3').status") == 'sent',
         f'billing on the {dev}: INV-2026-038 is unchanged and still sent while the revision is a draft')
    sb = await pg.evaluate("() => { const c = DB.clients.find(c => c.id === 'cl121'), d = c.invoices.find(i => i.id === 'in3'); return d.lines.map(l => r2(sovBilled(c, l.sovId))) }")
    C.ok(sb == sb0, f'billing on the {dev}: while the revision is a draft, billed to date counts INV-2026-038 once, not twice ({sb0[:3]} / {sb[:3]})')
    C.ok(await pg.evaluate("() => DB.audit.some(a => a.refId === 'in3' && a.action === 'revise-reason' && /wrong percentage/.test(a.note))"), f'billing on the {dev}: the reason is in the audit trail with who and when')
    if n:
        # the revision goes out: the original is voided (its posting reversed), the revision is posted
        pre = await pg.evaluate("""async (nid) => {
          const c = DB.clients.find(c => c.id === 'cl121'), n = c.invoices.find(i => i.id === nid);
          glSync();
          window.__dvPre = { had: glLive().some(j => j.key === 'inv:in3'), revs: (DB.gl.journals || []).filter(j => j.kind === 'reversal' && j.key === 'inv:in3').length };
          await docAction(c, n, 'send');
          return n.status;
        }""", n['id'])
        await pg.wait_for_timeout(300)
        if pre == 'draft' and await pg.locator('#mbm').count():
            # the job is billed ahead of the work (the seed's own state): the gate asks why, as it does for any progress invoice
            await pg.locator('#mbm input, #mbm textarea').first.fill('re-issue of INV-2026-038 at the same percentages')
            await pg.locator('#mbm #mbm-ok').click()
            await pg.wait_for_timeout(600)
        out = await pg.evaluate("""(nid) => {
          const c = DB.clients.find(c => c.id === 'cl121'), n = c.invoices.find(i => i.id === nid), o = c.invoices.find(i => i.id === 'in3');
          glSync();
          return { o: o.status, by: o.supersededBy, n: n.status, had: window.__dvPre.had, live: glLive().some(j => j.key === 'inv:in3'),
                   rev: (DB.gl.journals || []).filter(j => j.kind === 'reversal' && j.key === 'inv:in3').length > window.__dvPre.revs, posted: glLive().some(j => j.key === 'inv:' + nid) };
        }""", n['id'])
        C.ok(out['o'] == 'void' and out['by'] == n['number'] and out['n'] == 'sent', f'billing on the {dev}: sent, {n["number"]} replaces INV-2026-038, which is voided and names it ({out})')
        C.ok(out['had'] and not out['live'] and out['rev'] and out['posted'], f'billing on the {dev}: the ledger reverses INV-2026-038\'s posting and posts the revision; nothing is edited in place ({out})')
        C.ok(await pg.evaluate(snap) == before, f'billing on the {dev}: the voided INV-2026-038 still reads as it was sent')
    C.ok(not errs, f'revise on the {dev}: no page errors ({errs[:2]})')
    await b.close()


GATE = "(why) => { const m = document.getElementById('mbm'); if (!m) return false; const w = m.querySelector('textarea, input[data-f], input'); w && (w.value = why); m.querySelector('#mbm-ok').click(); return true; }"


async def revise_settled(p, phone):
    """a paid invoice re-issued: its payment and its credit follow the revision by linked transfers; no posted row changes"""
    dev = 'phone' if phone else 'desktop'
    who = f'billing on the {dev}'
    b, pg, errs = await boot(p, phone, 'u_billing')
    a = await pg.evaluate("""() => { const c = DB.clients.find(c => c.id === 'cl121'), f = clientFin(c);
      window.__rows = JSON.stringify(c.payments.filter(p => p.invoiceId === 'in2'));
      const n = dvRevise(c, c.invoices.find(i => i.id === 'in2'), 'retainage line misread');
      window.__n = n.id; docAction(c, n, 'send'); return { paid: r2(f.paid), n: n.number }; }""")
    await pg.wait_for_timeout(400)
    await pg.evaluate(GATE, 're-issue of INV-2026-035')
    await pg.wait_for_timeout(500)
    z = await pg.evaluate("""() => { const c = DB.clients.find(c => c.id === 'cl121'), n = c.invoices.find(i => i.id === window.__n), o = c.invoices.find(i => i.id === 'in2'),
        ids = JSON.parse(window.__rows).map(p => p.id), X = c.payments.filter(p => p.xferOf);
      return { same: JSON.stringify(c.payments.filter(p => ids.includes(p.id))) === window.__rows, o: o.status, n: n.status, onO: r2(invoicePaid(c, o)), onN: r2(invoicePaid(c, n)),
        pairs: X.length, net: r2(X.reduce((a, p) => a + p.amount, 0)), unbanked: r2(invoiceUnbanked(c, n)), paid: r2(clientFin(c).paid),
        gl: glDerive().some(j => j.sourceType === 'pay' && X.some(p => p.id === j.sourceId)), audit: DB.audit.some(r => r.action === 'transferred-to-revision') }; }""")
    C.ok(z['o'] == 'void' and z['n'] in ('sent', 'paid', 'partial'), f'{who}: {a["n"]} goes out and INV-2026-035 is voided ({z})')
    C.ok(z['same'], f'{who}: the original\'s payment rows are byte-identical before and after the re-issue')
    C.ok(z['pairs'] >= 2 and z['net'] == 0 and z['onO'] == 0 and z['onN'] == 72750, f'{who}: a linked transfer pair moves the $72,750 to the revision and nets to zero ({z})')
    C.ok(z['unbanked'] == 0 and z['paid'] == a['paid'] and not z['gl'] and z['audit'], f'{who}: the moved money stays bank-backed, collected is unchanged, no cash posts, and an audit row says so ({z})')
    # a credit given on the original is not given twice on its revision
    q = await pg.evaluate("""() => { const c = DB.clients.find(c => c.id === 'cl121'), o = c.invoices.find(i => i.id === 'in3'), l0 = o.lines[0], amt = lineAmount(l0, o);
      const R = dvCreditCreate(c, o, [{ lineId: l0.id, amount: 1000 }], 'demolition billed ahead');
      const n = dvRevise(c, o, 'one line re-measured'); window.__n3 = n.id; window.__amt = amt; window.__bal = r2(docTotal(n).total);
      docAction(c, n, 'send'); return { ok: R.ok }; }""")
    await pg.wait_for_timeout(400)
    await pg.evaluate(GATE, 're-issue of INV-2026-038')
    await pg.wait_for_timeout(500)
    y = await pg.evaluate("""() => { const c = DB.clients.find(c => c.id === 'cl121'), n = c.invoices.find(i => i.id === window.__n3), x = dvCreditable(c, n).find(v => v.l.id === n.lines[0].id);
      const again = dvCreditCreate(c, n, [{ lineId: n.lines[0].id, amount: window.__amt }], 'twice?');
      return { st: n.status, left: x ? x.left : 0, amt: window.__amt, bal: r2(docTotal(n).total - invoicePaid(c, n)), total: window.__bal, again: again.ok, credits: dvCreditsOn(c, n).length }; }""")
    C.ok(q['ok'] and y['st'] != 'draft' and abs(y['bal'] - (y['total'] - 900)) < 0.01, f'{who}: the $900 credit on INV-2026-038 carries to its revision\'s balance ({y})')
    C.ok(abs(y['left'] - (y['amt'] - 1000)) < 0.01 and not y['again'] and y['credits'] == 1, f'{who}: the revision\'s line can be credited only what is left after the original\'s credit; the full line again is refused ({y})')
    C.ok(not errs, f'revise settled on the {dev}: no page errors ({errs[:2]})')
    await b.close()


async def credit(p, phone):
    dev = 'phone' if phone else 'desktop'
    who = f'billing on the {dev}'
    b, pg, errs = await boot(p, phone, 'u_billing')
    F = """() => { const c = DB.clients.find(c => c.id === 'cl121'), d = c.invoices.find(i => i.id === 'in3'), f = clientFin(c), l = d.lines[0];
      let ar = 0; glDerive().filter(j => j.clientId === c.id).forEach(j => j.lines.forEach(x => x.acct === '1100' && (ar += (+x.dr || 0) - (+x.cr || 0))));
      return { bal: r2(docTotal(d).total - invoicePaid(c, d)), out: f.outstanding, inv: r2(f.invoiced), paid: r2(f.paid), cr: f.credits, ret: f.retHeld, sov: sovBilled(c, l.sovId), sched: +l.scheduled, gl1100: r2(ar), seq: (DB.company.seq || {}).inv } }"""
    a = await pg.evaluate(F)
    await pg.evaluate("() => { clientOpen = 'cl121'; docOpen = { kind: 'invoice', id: 'in3' }; view = 'billing'; render(); }")
    await dv_tap(pg, 'Create Credit')
    C.ok(await pg.locator('#mbm [data-crpick]').count() > 0, f'{who}: Create Credit lists the invoice\'s lines to credit')
    await pg.locator('#mbm [data-crpick]').first.check()
    await pg.locator('#mbm [data-cramt]').first.fill('1000')
    await pg.locator('#mbm [data-f="why"]').fill('demolition billed ahead of the work')
    await shot(pg, f'u_billing_{dev}_credit_sheet')
    await pg.locator('#mbm #mbm-ok').click()
    r = await rec(pg)
    z = await pg.evaluate(F)
    cm = await pg.evaluate("""() => { const c = DB.clients.find(c => c.id === 'cl121'), m = c.invoices.find(i => i.creditMemo); if (!m) return null; const t = docTotal(m);
      const j = glDerive().find(x => x.key === 'inv:' + m.id), sum = (a, k) => r2((j ? j.lines : []).filter(x => x.acct === a).reduce((s, x) => s + (+x[k] || 0), 0));
      return { id: m.id, number: m.number, of: m.creditOf, total: t.total, ret: t.ret, tax: t.tax, mode: m.mode, inList: c.invoices.includes(m),
        dr: r2((j ? j.lines : []).reduce((s, x) => s + (+x.dr || 0), 0)), crs: r2((j ? j.lines : []).reduce((s, x) => s + (+x.cr || 0), 0)), ar: sum('1100', 'cr'), rt: sum('1150', 'cr'),
        payGl: glDerive().some(x => x.sourceType === 'pay' && c.payments.some(p => p.cmApply && x.sourceId === p.id)),
        reg: (DB.clientCredits || []).some(cc => cc.creditMemoId === m.id && cc.status === 'approved' && cc.approvedBy),
        queue: blCreditRows().some(x => x.cc && x.cc.creditMemoId === m.id), shown: invoiceStatusShown(c, m).text,
        unbanked: invoiceUnbanked(c, c.invoices.find(i => i.id === 'in3')) } }""")
    C.ok(cm and r == 'credit:' + cm['id'], f'{who}: the credit memo opens as its document ({r})')
    t = await pg.evaluate("() => (document.querySelector('#dv .dv-doc') || {}).innerText || ''")
    C.ok('Credit Memo' in t and 'INV-2026-038' in t and 'retainage' in t.lower(), f'{who}: the memo reads as a Credit Memo naming INV-2026-038 and the retainage it reverses')
    await shot(pg, f'u_billing_{dev}_credit_memo')
    if phone: await phone_layout(pg, who + ' credit memo')
    if cm:
        C.ok(cm['inList'] and cm['of'] == 'in3' and cm['number'].startswith('CM-') and z['seq'] == a['seq'], f'{who}: {cm["number"]} lives in the client\'s invoices, linked to INV-2026-038, and takes no invoice number')
        C.ok(abs(cm['ret'] + 100) < 0.01 and abs(cm['total'] + 900) < 0.01, f'{who}: crediting $1,000 at 10% retainage reverses $100 of retainage: $900 off ({cm["total"]}, ret {cm["ret"]})')
        C.ok(abs((a['bal'] - z['bal']) - 900) < 0.01, f'{who}: the invoice\'s balance falls by the $900 credited ({a["bal"]} to {z["bal"]})')
        C.ok(abs((a['out'] - z['out']) - 900) < 0.01 and abs((a['inv'] - z['inv']) - 900) < 0.01 and abs(a['paid'] - z['paid']) < 0.01 and abs(a['cr'] - z['cr']) < 0.01,
             f'{who}: AR falls $900 and billed to date $900; no cash moves (paid {a["paid"]} to {z["paid"]})')
        C.ok(abs((a['gl1100'] - z['gl1100']) - (a['out'] - z['out'])) < 0.01, f'{who}: the ledger\'s AR (1100) moves with the subledger ({a["gl1100"]} to {z["gl1100"]})')
        C.ok(abs(cm['dr'] - cm['crs']) < 0.01 and abs(cm['ar'] - 900) < 0.01 and abs(cm['rt'] - 100) < 0.01, f'{who}: the memo\'s journal balances: Cr AR $900, Cr retainage $100, Dr revenue $1,000 ({cm})')
        C.ok(not cm['payGl'], f'{who}: the credit\'s application posts no cash (nothing to Undeposited Funds)')
        C.ok(abs((a['sov'] - z['sov']) - 1000 / a['sched'] * 100) < 0.001,
             f'{who}: the SOV line\'s billed to date falls by the share credited ({a["sov"]:.3f}% to {z["sov"]:.3f}%)')
        C.ok(cm['reg'] and not cm['queue'], f'{who}: the memo is in the client-credit register, approved with a name, and not left in the Billing Queue')
        C.ok(cm['shown'] == 'credit applied' and cm['unbanked'] < 0.01, f'{who}: the memo reads "credit applied"; the credit never reads as money not in the bank ({cm["shown"]}, {cm["unbanked"]})')
    # a credit with sales tax, on an item invoice
    tx = await pg.evaluate("""() => { const c = DB.clients.find(c => c.id === 'cl121');
      const d = newDoc(c, 'invoice', { mode: 'items', fields: { projectId: 'p121', title: 'Fixture: fixtures and finishes', taxRate: 8.875, retainagePct: 0, lines: [
        { id: 'ltA', item: 'Vanity, supplied', qty: 1, rate: 2000, taxable: true }, { id: 'ltB', item: 'Install labor', qty: 1, rate: 1000, taxable: false }] } });
      dvFresh.delete(d.id); d.status = 'sent'; d.sentAt = today(); docMark(d); save();
      const before = r2(docTotal(d).total - invoicePaid(c, d));
      const R = dvCreditCreate(c, d, [{ lineId: 'ltA', amount: 500 }], 'vanity price agreed lower');
      const t = docTotal(R.cm), j = glDerive().find(x => x.key === 'inv:' + R.cm.id), tax = r2(j.lines.filter(x => x.acct === '2300').reduce((s, x) => s + (+x.dr || 0) - (+x.cr || 0), 0));
      return { ok: R.ok, tax: t.tax, total: t.total, drop: r2(before - (docTotal(d).total - invoicePaid(c, d))), gltax: tax, over: dvCreditCreate(c, d, [{ lineId: 'ltA', amount: 1600 }], 'x').ok } }""")
    C.ok(tx['ok'] and abs(tx['tax'] + 44.38) < 0.011 and abs(tx['total'] + 544.38) < 0.011 and abs(tx['drop'] - 544.38) < 0.011,
         f'{who}: crediting $500 of a taxable line reverses its 8.875% sales tax: $544.38 off the balance ({tx})')
    C.ok(abs(tx['gltax'] - 44.38) < 0.011, f'{who}: the ledger takes the $44.38 back out of sales tax payable (Dr 2300)')
    C.ok(not tx['over'], f'{who}: a line is never credited past what is left of it ($1,500 left; $1,600 refused)')
    # over the company's limit ($1,000 unless Settings say otherwise) a credit waits on the owner; the asker never decides it
    lim = await pg.evaluate("""() => { const c = DB.clients.find(c => c.id === 'cl121'), d = c.invoices.find(i => /fixtures and finishes/.test(i.title || ''));
      const n0 = c.invoices.filter(i => i.creditMemo).length, R = dvCreditCreate(c, d, [{ lineId: 'ltA', amount: 1200 }], 'vanity replaced at our cost');
      window.__ask = R.ask && R.ask.id;
      return { ask: !!R.ask, total: R.total, made: c.invoices.filter(i => i.creditMemo).length - n0, self: dvCreditDecide(c, R.ask.id, true) === null,
               reg: (DB.clientCredits || []).some(x => x.id === R.ask.id && x.kind === 'credit-ask' && x.status === 'proposed'), queue: blCreditRows().some(r => r.cc && r.cc.id === R.ask.id) }; }""")
    C.ok(lim['ask'] and lim['made'] == 0 and lim['reg'] and not lim['queue'], f'{who}: a ${lim["total"]:,.2f} credit (over $1,000) is asked for in the register, nothing is credited, and it is not a Billing Queue row ({lim})')
    C.ok(lim['self'], f'{who}: billing cannot approve the credit it asked for')
    await sign_in(pg, 'u_owner')
    ow = await pg.evaluate("""() => { const c = DB.clients.find(c => c.id === 'cl121'), inApp = mApprovals().some(x => x.kind === 'creditmemo' && x.id === window.__ask);
      const cm = dvCreditDecide(c, window.__ask, true), a = (DB.clientCredits || []).find(x => x.id === window.__ask);
      return { inApp: inApp, cm: cm ? cm.number : '', prep: cm && cm.preparedBy, issued: cm && cm.issuedBy, st: a.status, by: a.approvedBy }; }""")
    C.ok(ow['inApp'] and ow['cm'].startswith('CM-') and ow['st'] == 'approved' and ow['by'] == OWNER and ow['issued'] == OWNER and ow['prep'] and ow['prep'] != OWNER,
         f'the owner on the {dev}: the credit waits in the owner\'s Approvals; approved, it is issued with who asked and who approved ({ow})')
    await sign_in(pg, 'u_billing')
    sm = await pg.evaluate("""() => { DB.company.creditApprovalOver = 5000; const c = DB.clients.find(c => c.id === 'cl121'), d = c.invoices.find(i => /fixtures and finishes/.test(i.title || ''));
      const R = dvCreditCreate(c, d, [{ lineId: 'ltB', amount: 1000 }], 'install done by the client'); return { cm: !!R.cm, ask: !!R.ask, by: R.cm && R.cm.issuedBy }; }""")
    C.ok(sm['cm'] and not sm['ask'] and sm['by'], f'{who}: with the limit set to $5,000 in Settings, a $1,000 credit issues at once with the issuer\'s name ({sm})')
    C.ok(not errs, f'credit on the {dev}: no page errors ({errs[:2]})')
    await b.close()


async def refund(p, phone):
    dev = 'phone' if phone else 'desktop'
    who = f'on the {dev}'
    b, pg, errs = await boot(p, phone, 'u_billing')
    S0 = """() => { const c = DB.clients.find(c => c.id === 'cl121'), d = c.invoices.find(i => i.id === 'in2'), f = clientFin(c);
      return { st: invoiceStatus(c, d), paid: r2(f.paid), cr: r2(f.credits), n: c.payments.length, out: f.outstanding } }"""
    a = await pg.evaluate(S0)
    no = await pg.evaluate("() => { const c = DB.clients.find(c => c.id === 'cl45'), d = c.invoices.find(i => i.id === 'inD45r'); return dvRefundPropose(c, d, c.payments.find(p => p.invoiceId === d.id).id, 100, 'test', false) }")
    C.ok(not no['ok'] and 'bank' in no['why'], f'billing {who}: money the bank does not have is never refunded ({no["why"]})')
    await pg.evaluate("() => { clientOpen = 'cl121'; docOpen = { kind: 'invoice', id: 'in2' }; view = 'billing'; render(); }")
    await dv_tap(pg, 'Refund')
    C.ok(await pg.locator('#mbm').count() == 1, f'billing {who}: Refund opens its sheet')
    to = await pg.evaluate("() => (document.querySelector('#mbm [data-f=pay]') || {}).selectedOptions ? document.querySelector('#mbm [data-f=pay]').selectedOptions[0].textContent : ''")
    await pg.locator('#mbm [data-f="amount"]').fill('500')
    await pg.locator('#mbm [data-f="why"]').fill('the client paid for the stair runner twice')
    await shot(pg, f'u_billing_{dev}_refund_sheet')
    await pg.locator('#mbm #mbm-ok').click()
    await pg.wait_for_timeout(300)
    f = await pg.evaluate("() => dvRefunds(DB.clients.find(c => c.id === 'cl121'))[0] || null")
    z = await pg.evaluate(S0)
    C.ok(f and f['status'] == 'proposed' and f['amount'] == 500, f'billing {who}: the refund is a proposal ({f and f["status"]})')
    reg = await pg.evaluate("() => { const c = DB.clients.find(c => c.id === 'cl121'); return { inReg: (DB.clientCredits || []).some(x => x.kind === 'refund' && x.clientId === c.id), own: c.refunds === undefined, queue: blCreditRows().some(r => r.cc && r.cc.kind === 'refund'), cap: dvRefundPropose(c, c.invoices.find(i => i.id === 'in2'), c.payments.find(p => p.invoiceId === 'in2' && p.amount > 0).id, 1e6, 'x', false).ok } }")
    C.ok(reg['inReg'] and reg['own'] and not reg['queue'], f'billing {who}: the refund lives in the one client-credit register, no store of its own, and is not a Billing Queue row ({reg})')
    C.ok(not reg['cap'], f'billing {who}: a refund is capped at the cash the bank has of that payment ($1,000,000 refused)')
    C.ok(z['n'] == a['n'] and z['paid'] == a['paid'] and z['st'] == a['st'], f'billing {who}: a proposal moves no money ({a} / {z})')
    C.ok(f and f['acctId'], f'billing {who}: the refund names the account the payment came into ({f and f["to"]}; the sheet: {to})')
    C.ok(await pg.evaluate("() => { const c = DB.clients.find(c => c.id === 'cl121'); return dvRefundDecide(c, dvRefunds(c)[0].id, true) === null && dvRefunds(c)[0].status === 'proposed' }"),
         f'billing {who}: billing cannot approve the refund it proposed')
    t = await pg.evaluate("() => (document.querySelector('#dv .dv-notes') || {}).innerText || ''")
    C.ok('proposed, not approved' in t, f'billing {who}: the document says the refund waits for approval ({t[:120]})')
    C.ok(await pg.evaluate("() => !mApprovals().some(x => x.kind === 'refund')"), f'billing {who}: the refund is not in billing\'s own Approvals')
    # the owner approves it from Approvals
    await sign_in(pg, 'u_owner')
    await pg.evaluate('dvClose()')
    C.ok(await pg.evaluate("() => mApprovals().some(x => x.kind === 'refund')"), f'the owner {who}: the refund waits in the owner\'s Approvals')
    await go(pg, 'mapprove')
    loc = pg.get_by_text('Review the Refund')
    if await loc.count():
        await loc.first.click()
    else:
        await pg.evaluate("() => mGo(mApprovals().find(x => x.kind === 'refund').open)")
    r = await rec(pg)
    C.ok(r == 'invoice:in2', f'the owner {who}: Review the Refund opens the invoice\'s document ({r})')
    await shot(pg, f'u_owner_{dev}_refund_review')
    await pg.locator('#dv [data-dvact^="rfapprove:"]').click()
    await pg.wait_for_timeout(300)
    g = await pg.evaluate("""() => { const c = DB.clients.find(c => c.id === 'cl121'), f = dvRefunds(c)[0], py = c.payments.find(p => p.id === f.paymentRecId), d = c.invoices.find(i => i.id === 'in2'), src = c.payments.find(p => p.id === f.paymentId);
      return { st: f.status, by: f.approvedBy, rec: py ? { amt: py.amount, of: py.refundOf, acct: py.acctId, un: !!py.unapplied } : null, src: src.id, word: dvRefundWord(c, f), banked: py ? payBankedAmt(c, py) : null,
        inv: invoiceStatus(c, d), cr: r2(clientFin(c).credits), paid: r2(clientFin(c).paid), cm: !!f.creditMemoId, out: clientFin(c).outstanding } }""")
    C.ok(g['st'] == 'approved' and g['by'], f'the owner {who}: approved, with the owner\'s name on it ({g["by"]})')
    C.ok(g['rec'] and g['rec']['amt'] == -500 and g['rec']['of'] == g['src'] and g['rec']['acct'] == f['acctId'], f'the owner {who}: the refund posts against the payment it returns, back to that account ({g["rec"]})')
    C.ok(g['word'] == 'approved, not in the bank' and g['banked'] == 0, f'the owner {who}: it reads "approved, not in the bank" and is not bank money yet ({g["word"]})')
    C.ok(g['cm'] and g['inv'] == 'paid' and abs(g['cr'] - z['cr']) < 0.06 and abs(g['out'] - z['out']) < 0.06, f'the owner {who}: with its credit memo, INV-2026-035 stays paid and nothing is owed again ({g})')
    # the bank line: only money out of that account, of that amount, is this refund
    m = await pg.evaluate("""() => { const c = DB.clients.find(c => c.id === 'cl121'), f = dvRefunds(c)[0], other = (DB.accounts || []).find(a => a.id !== f.acctId);
      DB.txns.push({ id: 'tRFok', date: today(), amt: -500, acct: f.acctId, desc: 'ONLINE TRANSFER TO KLEIN S', cat: '', status: 'new', origin: 'feed' });
      other && DB.txns.push({ id: 'tRFno', date: today(), amt: -500, acct: other.id, desc: 'CHECK 1201', cat: '', status: 'new', origin: 'feed' });
      return { lines: dvRefundLines(f).map(t => t.id), wrong: other ? dvRefundMatch(c, f.id, 'tRFno').ok : false } }""")
    C.ok(m['lines'] == ['tRFok'] and not m['wrong'], f'the owner {who}: only a line out of the account that paid can be the refund ({m})')
    await pg.evaluate("() => render()")
    await pg.locator('#dv [data-dvact^="rfmatch:"]').click()
    await pg.wait_for_timeout(200)
    await pg.locator('#mbm #mbm-ok').click()
    await pg.wait_for_timeout(300)
    h = await pg.evaluate("() => { const c = DB.clients.find(c => c.id === 'cl121'), f = dvRefunds(c)[0], py = c.payments.find(p => p.id === f.paymentRecId); return { w: dvRefundWord(c, f), b: payBankedAmt(c, py) } }")
    C.ok(h['w'].startswith('refunded, in the bank') and h['b'] == -500, f'the owner {who}: matched, the refund reads in the bank ({h})')
    C.ok(not errs, f'refund {who}: no page errors ({errs[:2]})')
    await b.close()


async def portal(p, phone):
    dev = 'phone' if phone else 'desktop'
    b, pg, errs = await boot(p, phone, 'u_klein')
    await pg.evaluate("() => { const c = DB.clients.find(c => c.id === 'cl121'); portalView(c, 'invoice', c.invoices.find(i => i.id === 'in3')) }")
    r = await rec(pg)
    A = await pg.evaluate("() => [...document.querySelectorAll('#dv .dv-bar [data-dvact], #dv .dv-menu [data-dvact]')].map(b => (b.classList.contains('primary') ? '*' : '') + b.dataset.dvact)")
    t = await pg.evaluate("() => (document.querySelector('#dv .dv-doc') || {}).innerText || ''")
    C.ok(r == 'invoice:in3' and 'How to Pay' in t and '*howtopay' in A and not {'credit', 'refund', 'edit'} & {x.strip('*') for x in A},
         f'the client on the {dev}: the portal opens the same invoice, How to Pay the blue, no office actions ({A})')
    await shot(pg, f'u_klein_{dev}_portal_invoice')
    if phone: await phone_layout(pg, f'the client on the {dev}')
    await pg.evaluate("() => { dvClose(); const c = DB.clients.find(c => c.id === 'cl121'); portalView(c, 'co', c.changeOrders.find(x => x.id === 'co2')) }")
    A = await pg.evaluate("() => [...document.querySelectorAll('#dv .dv-bar [data-dvact]')].map(b => (b.classList.contains('primary') ? '*' : '') + b.dataset.dvact)")
    C.ok('*papprove' in A, f'the client on the {dev}: a change order waiting on them opens with Approve the blue ({A})')
    C.ok(not errs, f'portal on the {dev}: no page errors ({errs[:2]})')
    await b.close()


async def main():
    only = sys.argv[1:] or ['lists', 'revise', 'credit', 'refund', 'portal']
    async with async_playwright() as p:
        for phone in (False, True):
            if 'lists' in only:
                for uid in ('u_billing', 'u_controller', 'u_owner'):
                    await lists_open(p, phone, uid)
            if 'revise' in only: await revise(p, phone); await revise_settled(p, phone)
            if 'credit' in only: await credit(p, phone)
            if 'refund' in only: await refund(p, phone)
            if 'portal' in only: await portal(p, phone)
    sys.exit(C.done())

asyncio.run(main())
