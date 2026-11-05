"""The billing person's path to a new invoice, counted in taps (BACKLOG 1.36, journeys J8 and J9; 11-05).

What was wrong. On the 11-03 Sales pages billing reached a new invoice through Clients' All, the client, Contract and
Billing and the old Billing Record, then typed the signed contract's deposit by hand: J8 took 28 taps on the desktop and
30 on the phone (24 and 26 before), J9 27 and 28 (23 and 24 before), though the Billing queue already knew what was due.

DEP  The Ashbys sign (the owner records it, the hand-off before billing). Billing: Clients opens on Need You, which names
     the Ashbys with the deposit due (the Billing queue's own rule, readyToBill); the client opens on Contract and
     Billing; its blue New Invoice opens the queue's own Deposit Invoice sheet at the contract's 25%; Create makes one
     line of $22,780, no retainage, due on receipt, tied to the contract and the job, a draft, opened, with a toast
     that names it with Open. At most 4 taps from sign-in (the menu entry, the row, New Invoice, Create). In the same
     turn the deposit leaves the Billing queue, Need You and the client's Ready to Bill (one function, billingRows),
     each naming the draft instead ("draft ready: INV-..."); a second New Invoice reopens that draft with a toast.
PRO  The Kleins (121 State, the seeded job with measured work ready to bill and CO-2026-001 approved): Need You names
     the measured work; New Invoice opens the job's application (the queue's own draft: the field's measures, the
     contract's retainage, every approved change order as a line), opened with its toast. At most 3 taps. Pinned
     after: Need You keeps the Kleins and names the draft ("draft ready: INV-..., not sent"), and the measured work
     leaves "ready to bill" (the queue drops the application once its draft is written); a second New Invoice reopens
     the draft with a toast; the queue's draft row opens the same invoice.
MEMO The queue's memo answers what a fresh read does on Clients, a client and Billing (no wrapper decorates its cached rows).
ROW  A row opens, a button acts: the Ashbys' deposit row opens the signed contract, the Kleins' application row opens
     the job's Progress Billing; neither drafts anything.
TODAY Billing's Today shows the deposit due within 2 business days (ctDepositDue's by); its blue Draft opens the same
     prefilled Deposit Invoice sheet as New Invoice (slBillRun on the queue's row); drafted, it leaves Today.
BLANK A client with nothing due: New Invoice is the blank invoice it always was (crNewInvoice), never an application.
     The phone never scrolls sideways on the client's Contract and Billing.

    python3 tests/billing_path_test.py            (through tests/slot.sh)
"""
import asyncio, re, sys
from harness import async_playwright, open_app, sign_in, go, Checks

LINES = [  # the Ashbys' 12 lines, $91,120 (as billing_truth_test.py)
    ('Demolition and protection', 9200), ('Framing', 11400), ('Plumbing rough and finish', 12600), ('Electrical rough and finish', 10800),
    ('Drywall and cement board', 6400), ('Tile: floors and walls', 9800), ('Cabinetry install', 7200), ('Doors and trim', 5600),
    ('Paint', 4800), ('Plumbing fixture allowance', 6500), ('Lighting allowance', 3820), ('Supervision and fee', 3000),
]
CONTRACT = sum(a for _, a in LINES)
DEPOSIT = round(CONTRACT * 0.25, 2)
PIN = {'DEP': 4, 'PRO': 3}   # taps from sign-in to the drafted invoice, menu entry included

SIGNED_SETUP = """
  const c = blankClient('Wren & Julian Ashby'); c.propertyAddr = '214 Lincoln Place, Brooklyn';
  c.contacts = [{ id: uid('ct'), name: 'Wren Ashby', email: 'wren.ashby@example.com', role: 'Owner', primary: true }];
  DB.clients.push(c);
  const p = blankProject('214 Lincoln Place', '214 Lincoln Place, Brooklyn', today(), ''); p.clientId = c.id; DB.projects.push(p);
  const e = newDoc(c, 'estimate', { template: 'construction', fields: { title: '214 Lincoln Place — renovation', projectId: p.id } });
  e.lines = arg.map(([item, amt]) => ({ id: uid('l'), item, desc: '', qty: 1, unit: 'ls', rate: amt, cost: Math.round(amt * 0.7), taxable: false }));
  e.status = 'sent'; e.sentAt = today(); e.sentTo = 'wren.ashby@example.com'; docMark(e); save();
  return { cid: c.id, pid: p.id, eid: e.id, number: e.number };
"""

# the three places a deposit due is read, in one turn (the Billing queue's billingRows, Clients' Need You, the client's
# Ready to Bill), as data: a ready deposit row for the client, and its words on Need You
THREE = """const c = DB.clients.find(x => x.id === arg.cid);
  const q = billingRows().filter(r => r.client && r.client.id === c.id), keep = slClChip; slClChip = 'need';
  let need; try { need = slClientsRows().find(r => r.id === c.id); } finally { slClChip = keep; }
  const slice = slBillDue(c);
  return { queue: q.filter(r => r.kind === 'ready' && r.rtb && r.rtb.kind === 'deposit').length, queueDraft: q.filter(r => r.kind === 'draft').map(r => r.inv.number),
           need: need ? need.meta : '', slice: slice.filter(r => r.kind === 'ready' && r.rtb.kind === 'deposit').length, sliceDraft: slice.filter(r => r.kind === 'draft').map(r => r.inv.number) };"""


async def menu(pg, v):
    """a menu entry, as the person taps it: the page's list, nothing left open on it"""
    await pg.evaluate("v => { clientOpen = null; docOpen = null; setView(v); }", v)
    await pg.wait_for_timeout(300)

# a row whose words read like code: a function rendered as text (11-05, integ13: a row field the shared row kit reads as
# a label, act2, carried a function, and the row printed "() => slBillRun(c, r)" as a button)
CODEISH = r"=>|\bfunction\b|\[object |\bundefined\b|\bNaN\b"
ROWS_TEXT = """return [...document.querySelectorAll(arg)].filter(e => e.getClientRects().length).map(e => e.innerText.replace(/\\s+/g, ' '));"""


async def code_rows(pg, sel):
    """the rows matched by sel whose words read like code"""
    return [t[:160] for t in await js(pg, ROWS_TEXT, sel) if re.search(CODEISH, t)]


async def js(pg, body, arg=None):
    return await pg.evaluate("async (arg) => { const sleep = ms => new Promise(r => setTimeout(r, ms)); " + body + " }", arg)


class Taps:
    """the person's taps: every click this suite makes on the page, and the menu entry (one tap, reached by setView)"""
    def __init__(self, pg): self.pg, self.n = pg, 0

    async def menu(self, v):
        self.n += 1; await menu(self.pg, v)

    async def click(self, loc, wait=500):
        self.n += 1; await loc.click(); await self.pg.wait_for_timeout(wait)


async def owner_signs(pg, S):
    """the owner records the Ashbys' signed copy (the hand-off before billing's journey; not billing's taps)"""
    await js(pg, "view = 'clients'; clientOpen = arg.cid; clientTab = 'fin'; finTab = 'estimates'; docOpen = { kind: 'estimate', id: arg.eid }; render(); await sleep(300);", S)
    b = pg.locator(f'#doc-{S["eid"]} [data-docact="lkapprove"]').first
    if not await b.is_visible():
        await pg.locator(f'#doc-{S["eid"]} summary').filter(has_text='More').first.click(); await pg.wait_for_timeout(300)
    await b.click(); await pg.wait_for_timeout(400)
    await pg.locator('#mbm [data-f="why"]').fill('Signed copy by email from Wren Ashby, 9/3 (signed PDF on file)')
    await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(700)
    await js(pg, "docOpen = null; clientOpen = null; save();")


async def need_row(pg, name):
    """the client's row on Clients' Need You: its words, and a locator on the row's own words (not its button)"""
    t = await js(pg, """const r = [...document.querySelectorAll('.view.on [data-ydrow]')].find(e => e.getClientRects().length && e.innerText.includes(arg));
      const on = [...document.querySelectorAll('.view.on [data-ydchip]')].find(b => b.classList.contains('on'));
      return { text: r ? r.innerText.replace(/\\s+/g, ' ') : '', id: r ? r.dataset.ydrow : '', chip: on ? on.dataset.ydchip : '' };""", name)
    return t, (pg.locator(f'.view.on [data-ydrow="{t["id"]}"] .yd-t').first if t['id'] else None)


async def client_page(pg):
    return await js(pg, """const v = document.querySelector('.view.on'), b = v && v.querySelector('[data-ydclnewinv]');
      const tab = v && v.querySelector('[data-ydtab].on');
      return { tab: tab ? tab.textContent.trim() : '', btn: !!(b && b.getClientRects().length), blue: !!(b && b.classList.contains('primary')),
               blues: v ? [...v.querySelectorAll('.btn.primary')].filter(x => x.getClientRects().length).map(x => x.textContent.trim()) : [],
               sw: document.documentElement.scrollWidth, iw: innerWidth, text: v ? v.innerText : '' };""")


async def t_deposit(C, p, phone):
    dev = 'phone' if phone else 'desktop'
    b, pg, errs = await open_app(p, phone)
    await sign_in(pg, 'u_owner')
    S = await js(pg, SIGNED_SETUP, LINES)
    await owner_signs(pg, S)
    await sign_in(pg, 'u_billing')
    T = Taps(pg)
    await T.menu('clients')
    row, loc = await need_row(pg, 'Wren & Julian Ashby')
    C.ok(row['chip'] == 'need', f'DEP {dev}: Clients opens on Need You ({row["chip"]!r})')
    C.ok(bool(re.search(r'ready to bill: .*25% deposit \(\$22,780(\.00)?\).*invoice by 9/8', row['text'])),
         f"DEP {dev}: Need You names the Ashbys with the signed contract's deposit due (25%, $22,780, by 9/8): {row['text'][:200]!r}")
    if not loc:
        await b.close(); return
    await T.click(loc)
    pgc = await client_page(pg)
    C.ok(pgc['tab'] == 'Contract and Billing' and pgc['btn'] and pgc['blue'], f'DEP {dev}: the Ashbys open on Contract and Billing with a blue New Invoice: {pgc["tab"]!r} {pgc["btn"]} {pgc["blue"]}')
    C.ok(pgc['blues'] == ['New Invoice'], f'DEP {dev}: one blue button on the page, New Invoice: {pgc["blues"]}')
    C.ok('filled from' in pgc['text'] and '25% deposit' in pgc['text'], f'DEP {dev}: the page says what New Invoice is filled from: {pgc["text"][:300]!r}')
    C.ok(pgc['sw'] <= pgc['iw'], f'DEP {dev}: Contract and Billing does not scroll sideways ({pgc["sw"]} > {pgc["iw"]})')
    if not pgc['btn']:
        await b.close(); return
    await T.click(pg.locator('.view.on [data-ydclnewinv]').first)
    m = await js(pg, "const m = document.getElementById('mbm'); return m ? { title: (m.querySelector('h3') || {}).innerText || '', pct: (m.querySelector('#dep-pct') || {}).value, amt: (m.querySelector('#dep-amt') || {}).value } : null;")
    C.ok(bool(m) and 'Deposit Invoice' in m['title'] and m['pct'] == '25' and abs(float(m['amt'] or 0) - DEPOSIT) < 0.01,
         f"DEP {dev}: New Invoice opens the Deposit Invoice sheet at the contract's 25%, ${DEPOSIT:,.2f}: {m}")
    if not m:
        await b.close(); return
    await T.click(pg.locator('#mbm #mbm-ok').first, 800)
    r = await js(pg, """const c = DB.clients.find(x => x.id === arg.cid), I = (c.invoices || []).filter(i => i.status !== 'void');
      const d = I.find(i => i.depositOf === arg.eid && i.mode !== 'sov'), t = document.getElementById('toast');
      return { n: I.length, dep: d && { lines: d.lines.length, total: docTotal(d).total, ret: +d.retainagePct || 0, due: d.due, date: d.date, status: d.status,
               project: d.projectId, isDep: invIsDeposit(d), number: d.number }, open: !!(d && docOpen && docOpen.id === d.id),
               shown: !!(d && document.querySelector('#doc-' + d.id)), toast: t ? t.innerText : '' };""", S)
    d = r['dep'] or {}
    C.ok(r['n'] == 1 and d and d['lines'] == 1 and abs(d['total'] - DEPOSIT) < 0.01 and d['ret'] == 0 and d['due'] == d['date'] and d['project'] == S['pid'] and d['status'] == 'draft' and d['isDep'],
         f'DEP {dev}: one deposit invoice, one line of ${DEPOSIT:,.2f}, no retainage, due on receipt, on 214 Lincoln, a draft: {r}')
    C.ok(r['open'] and r['shown'], f'DEP {dev}: the deposit invoice opens on the screen: {r["open"]} {r["shown"]}')
    C.ok((d.get('number') or '#') in r['toast'] and 'Open' in r['toast'], f'DEP {dev}: the toast names it with Open: {r["toast"]!r}')
    C.ok(T.n <= PIN['DEP'], f'DEP {dev}: {T.n} taps from sign-in to the drafted deposit, at most {PIN["DEP"]}')
    # drafted, the deposit leaves all three places in the same turn (no stale memo): the Billing queue, Need You and the
    # client's Ready to Bill each read the client's slice of billingRows; each now holds the draft instead
    x = await js(pg, THREE, S)
    num = d.get('number') or '#'
    C.ok(x['queue'] == 0 and x['slice'] == 0 and '25% deposit' not in x['need'],
         f'DEP {dev}: drafted, the deposit is gone from the queue, Need You and Ready to Bill in the same turn: {x}')
    C.ok(x['queueDraft'] == [num] and x['sliceDraft'] == [num] and f'draft ready: {num}' in x['need'],
         f'DEP {dev}: the three places name the draft {num} instead (Need You: "draft ready: {num}"): {x}')
    # and as the person sees them: Billing's queue and Need You on the screen
    await menu(pg, 'billing')
    bt = await js(pg, "const v = document.getElementById('v-billing'); return v ? v.innerText : '';")
    C.ok('the 25% deposit ($22,780)' not in bt and num in bt, f'DEP {dev}: Billing\'s queue shows the draft {num}, not the deposit to bill: {bt[:200]!r}')
    await menu(pg, 'clients')
    row, loc = await need_row(pg, 'Wren & Julian Ashby')
    C.ok('ready to bill' not in row['text'] and f'draft ready: {num}' in row['text'], f'DEP {dev}: Need You says "draft ready: {num}", not "ready to bill": {row["text"][:200]!r}')
    # a second New Invoice reuses the draft: the same invoice reopened, with a toast that names it with Open
    if loc:
        await loc.click(); await pg.wait_for_timeout(500)
        await pg.locator('.view.on [data-ydclnewinv]').first.click(); await pg.wait_for_timeout(700)
        y = await js(pg, """const c = DB.clients.find(x => x.id === arg.cid), t = document.getElementById('toast');
          return { n: (c.invoices || []).filter(i => i.status !== 'void').length, open: docOpen ? docOpen.id : '', id: (c.invoices.find(i => i.depositOf === arg.eid) || {}).id, toast: t ? t.innerText : '', modal: !!document.getElementById('mbm') };""", S)
        C.ok(y['n'] == 1 and y['open'] == y['id'] and not y['modal'], f'DEP {dev}: a second New Invoice reopens {num}, no second invoice: {y}')
        C.ok(num in y['toast'] and 'Open' in y['toast'] and 'drafted already' in y['toast'], f'DEP {dev}: its toast says {num} is drafted already, with Open: {y["toast"]!r}')
    C.ok(not errs, f'DEP {dev}: no page errors: {errs[:3]}')
    await b.close()


SHEET = "const m = document.getElementById('mbm'); return m ? { title: (m.querySelector('h3') || {}).innerText || '', pct: (m.querySelector('#dep-pct') || {}).value, amt: (m.querySelector('#dep-amt') || {}).value } : null;"
TODAY_ROW = """const sl = ms => new Promise(r => setTimeout(r, ms)), vis = e => !!e && e.getClientRects().length > 0;
  try { tdyTabSet('today'); tdyAllOpen = true; } catch (e) {} view = 'home'; render(); await sl(300);
  const e = [...document.querySelectorAll('.view.on .td-do .td-card')].filter(vis).find(x => x.innerText.includes('Deposit due: ' + arg));
  const chip = [...document.querySelectorAll('.view.on [data-tdytabbtn]')].find(b => b.classList.contains('on'));
  if (!e) return { found: false, chip: chip && chip.dataset.tdytabbtn };
  // the desk selects the row and acts from its side panel (the blue button); the phone acts from the row
  let b = null;
  if (document.querySelector('.view.on .td2-aside')) { e.click(); await sl(250); b = document.querySelector('.view.on .td2-aside [data-td2lead]'); }
  else b = e.querySelector('[data-tdverb]');
  document.querySelectorAll('[data-deptoday]').forEach(x => x.removeAttribute('data-deptoday')); b && b.setAttribute('data-deptoday', '1');
  return { found: true, chip: chip && chip.dataset.tdytabbtn, text: e.innerText.replace(/\\s+/g, ' '), verb: vis(b) ? b.innerText.trim().replace(/,\\s*[\\u2212-]?\\$[\\d,.]+$/, '') : '',
           blue: !!(b && b.classList.contains('primary')), sw: document.scrollingElement.scrollWidth, w: innerWidth };"""


async def t_today(C, p, phone):
    """TODAY: billing's Today shows the signed contract's deposit, due within 2 business days (ctDepositDue's by), on the
    Today chip; its blue button opens the same prefilled Deposit Invoice sheet as the client's New Invoice (one path,
    slBillRun on the queue's own row); Create drafts one invoice, toasts it with Open, and the row leaves Today."""
    dev = 'phone' if phone else 'desktop'
    b, pg, errs = await open_app(p, phone)
    await sign_in(pg, 'u_owner')
    S = await js(pg, SIGNED_SETUP, LINES)
    await owner_signs(pg, S)
    await sign_in(pg, 'u_billing')
    # what the client's New Invoice opens: the reference
    await js(pg, "slOpenClient(arg.cid); render(); await sleep(300);", S)
    ref = None
    if await pg.locator('.view.on [data-ydclnewinv]').first.is_visible():
        await pg.locator('.view.on [data-ydclnewinv]').first.click(); await pg.wait_for_timeout(500)
        ref = await js(pg, SHEET)
    await js(pg, "try { mbCloseModal(); } catch (e) {} clientOpen = null; docOpen = null;")
    r = await js(pg, TODAY_ROW, 'Wren & Julian Ashby')
    C.ok(r['found'] and r['chip'] == 'today', f"TODAY {dev}: billing's Today shows the Ashbys' deposit due on the Today chip: {r}")
    if not r['found']:
        await b.close(); return
    C.ok('$22,780' in r['text'] and '25% of' in r['text'] and re.search(r'(invoice by 9/8|Tue)', r['text']), f"TODAY {dev}: the row names the 25%, $22,780 and the by date (9/8, two business days after signing): {r['text'][:200]!r}")
    C.ok(r['verb'] == 'Draft', f'TODAY {dev}: its button reads Draft: {r}')
    if not phone: C.ok(r['blue'], f'TODAY {dev}: selected, its Draft is the blue button: {r}')
    C.ok(r['sw'] <= r['w'], f"TODAY {dev}: Today does not scroll sideways ({r['sw']} > {r['w']})")
    await pg.locator('[data-deptoday]').first.click(); await pg.wait_for_timeout(500)
    m = await js(pg, SHEET)
    C.ok(m and ref and m == ref and 'Deposit Invoice' in m['title'] and m['pct'] == '25' and abs(float(m['amt'] or 0) - DEPOSIT) < 0.01,
         f"TODAY {dev}: Draft opens the same prefilled Deposit Invoice sheet as New Invoice: {m} (New Invoice: {ref})")
    if not m:
        await b.close(); return
    await pg.locator('#mbm #mbm-ok').first.click(); await pg.wait_for_timeout(800)
    x = await js(pg, """const c = DB.clients.find(x => x.id === arg.cid), I = (c.invoices || []).filter(i => i.status !== 'void' && i.depositOf === arg.eid), t = document.getElementById('toast');
      return { n: I.length, number: I[0] && I[0].number, total: I[0] && docTotal(I[0]).total, toast: t ? t.innerText : '' };""", S)
    C.ok(x['n'] == 1 and abs((x['total'] or 0) - DEPOSIT) < 0.01 and (x['number'] or '#') in x['toast'] and 'Open' in x['toast'], f'TODAY {dev}: one deposit invoice drafted, toasted with Open: {x}')
    r2 = await js(pg, TODAY_ROW, 'Wren & Julian Ashby')
    C.ok(not r2['found'], f'TODAY {dev}: drafted, the deposit leaves billing\'s Today: {r2}')
    C.ok(not errs, f'TODAY {dev}: no page errors: {errs[:3]}')
    await b.close()


async def t_progress(C, p, phone):
    dev = 'phone' if phone else 'desktop'
    b, pg, errs = await open_app(p, phone)
    await sign_in(pg, 'u_billing')
    pre = await js(pg, """const c = DB.clients.find(x => x.id === 'cl121'); const r = readyToBill().rows.find(x => x.c && x.c.id === 'cl121' && x.kind === 'application');
      return { app: r ? r.amount : 0, cos: (c.changeOrders || []).filter(x => x.status === 'approved' && x.projectId === 'p121').map(x => x.number), drafts: (c.invoices || []).filter(i => i.status === 'draft').length };""")
    C.ok(pre['app'] > 0 and pre['cos'], f'PRO {dev}: the seed has 121 State\'s measured work ready to bill and an approved change order: {pre}')
    T = Taps(pg)
    await T.menu('clients')
    row, loc = await need_row(pg, 'Sarah & David Klein')
    C.ok('ready to bill: line-by-line application ready' in row['text'], f'PRO {dev}: Need You names the Kleins with the measured work ready to bill: {row["text"][:240]!r}')
    if not loc:
        await b.close(); return
    await T.click(loc)
    pgc = await client_page(pg)
    C.ok(pgc['tab'] == 'Contract and Billing' and pgc['btn'] and pgc['blues'] == ['New Invoice'], f'PRO {dev}: the Kleins open on Contract and Billing, New Invoice the one blue button: {pgc["tab"]!r} {pgc["blues"]}')
    C.ok(pgc['sw'] <= pgc['iw'], f'PRO {dev}: Contract and Billing does not scroll sideways ({pgc["sw"]} > {pgc["iw"]})')
    if not pgc['btn']:
        await b.close(); return
    await T.click(pg.locator('.view.on [data-ydclnewinv]').first, 900)
    if await pg.locator('#mbm #mbm-ok').count():   # a picker or a confirmation is a tap the person makes
        await T.click(pg.locator('#mbm #mbm-ok').first, 800)
    r = await js(pg, """const c = DB.clients.find(x => x.id === 'cl121'), i = (c.invoices || []).find(x => x.mode === 'sov' && x.status === 'draft' && x.projectId === 'p121');
      if (!i) return null; const t = document.getElementById('toast');
      const co = i.lines.filter(l => { const v = (c.sov || []).find(s => s.id === l.sovId); return v && pgIsCO(v); });
      return { number: i.number, ret: +i.retainagePct || 0, dep: i.depositOf || '', co: co.map(l => l.item), billed: r2(i.lines.reduce((a, l) => a + (+l.scheduled || 0) * (+l.pct || 0) / 100, 0)),
               open: !!(docOpen && docOpen.id === i.id), view: view, shown: !!document.querySelector('.view.on #doc-' + i.id), toast: t ? t.innerText : '' };""")
    C.ok(bool(r) and r['ret'] > 0 and r['dep'] and r['billed'] > 0, f'PRO {dev}: New Invoice drafts the job\'s application: the measured work billed, the contract\'s retainage, its deposit named: {r}')
    C.ok(bool(r) and any('CO-2026-001' in x for x in r['co']), f'PRO {dev}: the approved change order is a line on it: {r and r["co"]}')
    C.ok(bool(r) and r['open'] and (r['number'] in r['toast']) and 'Open' in r['toast'], f'PRO {dev}: the application opens, and the toast names it with Open: {r}')
    C.ok(bool(r) and r['view'] == 'billing' and r['shown'], f'PRO {dev}: the application is on the screen in Billing, not forwarded to the Pipeline (the old Estimates link only): {r and (r["view"], r["shown"])}')
    C.ok(T.n <= PIN['PRO'], f'PRO {dev}: {T.n} taps from sign-in to the drafted application, at most {PIN["PRO"]}')
    if not r:
        await b.close(); return
    num = r['number']
    # Need You once the application is drafted (pinned, 11-05, as the code does it): the Kleins stay in Need You, and
    # the row names the draft ("draft ready: INV-..., not sent"); the measured work leaves "ready to bill", because
    # the Billing queue drops a job's application once its draft is written (the draft carries it)
    await menu(pg, 'clients')
    row, loc = await need_row(pg, 'Sarah & David Klein')
    C.ok(f'draft ready: {num}, not sent' in row['text'], f'PRO {dev}: drafted, Need You keeps the Kleins and names the draft ("draft ready: {num}, not sent"): {row["text"][:300]!r}')
    C.ok('ready to bill: line-by-line application' not in row['text'], f'PRO {dev}: drafted, the measured work no longer reads "ready to bill" (the draft carries it): {row["text"][:300]!r}')
    COUNT = """const c = DB.clients.find(x => x.id === 'cl121'), t = document.getElementById('toast');
      return { n: (c.invoices || []).filter(i => i.mode === 'sov' && i.status === 'draft' && i.projectId === 'p121').map(i => i.number), open: docOpen ? docOpen.id : '',
               id: ((c.invoices || []).find(i => i.number === arg) || {}).id, toast: t ? t.innerText : '' };"""
    # a second New Invoice, from Need You's client, reopens the job's draft and toasts it with Open
    if loc:
        await loc.click(); await pg.wait_for_timeout(500)
        await pg.locator('.view.on [data-ydclnewinv]').first.click(); await pg.wait_for_timeout(900)
        y = await js(pg, COUNT, num)
        C.ok(y['n'] == [num] and y['open'] == y['id'] and num in y['toast'] and 'Open' in y['toast'] and 'drafted already' in y['toast'],
             f'PRO {dev}: a second New Invoice from Need You reopens {num} (no second draft), toasted with Open: {y}')
    # and from the Billing queue: the application is no longer a row to draft; the draft's own row opens the same invoice
    await menu(pg, 'billing')
    q = await js(pg, """const R = billingRows().filter(x => x.job && x.job.id === 'p121');
      const d = R.find(x => x.kind === 'draft' && x.inv && x.inv.number === arg);
      const b = d && [...document.querySelectorAll('[data-blact]')].find(x => x.dataset.blact === d.id && x.getClientRects().length);
      return { app: R.filter(x => x.kind === 'ready' && x.rtb && x.rtb.kind === 'application').length, draft: d ? d.id : '', btn: b ? b.innerText.trim() : '' };""", num)
    C.ok(q['app'] == 0 and q['draft'] and q['btn'], f'PRO {dev}: the Billing queue holds {num} as a draft to send with its button, and no second application to draft: {q}')
    if q['btn']:
        await pg.locator(f'[data-blact="{q["draft"]}"]').filter(has_text=q['btn']).first.click(); await pg.wait_for_timeout(900)
        y = await js(pg, COUNT, num)
        C.ok(y['n'] == [num] and y['open'] == y['id'], f'PRO {dev}: the queue\'s draft row opens {num} itself, no second draft: {y}')
    C.ok(not errs, f'PRO {dev}: no page errors: {errs[:3]}')
    await b.close()


async def t_blank(C, p, phone):
    dev = 'phone' if phone else 'desktop'
    b, pg, errs = await open_app(p, phone)
    await sign_in(pg, 'u_billing')
    cid = await js(pg, """const c = DB.clients.find(x => !readyToBill().rows.some(r => r.c && r.c.id === x.id) && (DB.projects || []).some(p => p.clientId === x.id));
      if (!c) return null; slOpenClient(c.id); await sleep(300); return c.id;""")
    C.ok(bool(cid), f'BLANK {dev}: a client with a job and nothing due')
    if not cid:
        await b.close(); return
    pgc = await client_page(pg)
    C.ok(pgc['btn'] and 'nothing is due to bill' in pgc['text'], f'BLANK {dev}: New Invoice says it starts a blank one: {pgc["text"][:300]!r}')
    if not pgc['btn']:
        await b.close(); return
    n0 = await js(pg, "const c = DB.clients.find(x => x.id === arg); return (c.invoices || []).length;", cid)
    await pg.locator('.view.on [data-ydclnewinv]').first.click(); await pg.wait_for_timeout(600)
    r = await js(pg, "const c = DB.clients.find(x => x.id === arg), i = (c.invoices || [])[(c.invoices || []).length - 1]; return { n: (c.invoices || []).length, mode: i && i.mode, status: i && i.status, open: !!(i && docOpen && docOpen.id === i.id) };", cid)
    C.ok(r['n'] == n0 + 1 and r['mode'] == 'items' and r['status'] == 'draft' and r['open'], f'BLANK {dev}: a blank invoice, opened (not an application): {r}')
    C.ok(not errs, f'BLANK {dev}: no page errors: {errs[:3]}')
    await b.close()


async def t_rows(C, p, phone):
    """the client's Ready to Bill: a row opens its source, a button acts (the Partners rule). The Ashbys' deposit row
    opens the signed contract; the Kleins' application row opens the job's Progress Billing; neither drafts anything"""
    dev = 'phone' if phone else 'desktop'
    b, pg, errs = await open_app(p, phone)
    await sign_in(pg, 'u_owner')
    S = await js(pg, SIGNED_SETUP, LINES)
    await owner_signs(pg, S)
    await sign_in(pg, 'u_billing')
    await js(pg, "slOpenClient(arg.cid); await sleep(300);", S)
    rows = await js(pg, """return [...document.querySelectorAll('.view.on [data-sec="due"]')].filter(e => e.getClientRects().length).map(e => ({ id: e.dataset.ydrow, btn: !!e.querySelector('button'), text: e.innerText.replace(/\\s+/g, ' ') }));""")
    C.ok(len(rows) == 1 and '25% deposit' in rows[0]['text'] and not rows[0]['btn'], f'ROW {dev}: the Ashbys\' Ready to Bill is the deposit, one row with no button of its own (New Invoice acts): {rows}')
    bad = await code_rows(pg, '.view.on [data-ydrow], .view.on button')
    C.ok(not bad, f'ROW {dev}: no row or button on the Ashbys\' Contract and Billing reads like code: {bad[:3]}')
    if rows:
        await pg.locator(f'.view.on [data-ydrow="{rows[0]["id"]}"] .yd-t').first.click(); await pg.wait_for_timeout(600)
        r = await js(pg, "const c = DB.clients.find(x => x.id === arg.cid); return { doc: docOpen, n: (c.invoices || []).length, modal: !!document.getElementById('mbm') };", S)
        C.ok(r['doc'] and r['doc']['kind'] == 'estimate' and r['doc']['id'] == S['eid'] and r['n'] == 0 and not r['modal'],
             f'ROW {dev}: tapping the deposit row opens the signed contract {S["number"]}, drafts nothing, opens no sheet: {r}')
    await js(pg, "docOpen = null; slOpenClient('cl121'); await sleep(300);")
    rows = await js(pg, """return [...document.querySelectorAll('.view.on [data-sec="due"]')].filter(e => e.getClientRects().length).map(e => ({ id: e.dataset.ydrow, btn: (e.querySelector('button') || {}).innerText || '', text: e.innerText.replace(/\\s+/g, ' ') }));""")
    app = next((x for x in rows if 'Progress application' in x['text']), None)
    bad = await code_rows(pg, '.view.on [data-ydrow], .view.on button')
    C.ok(not bad, f'ROW {dev}: no row or button on the Kleins\' Contract and Billing reads like code: {bad[:3]}')
    C.ok(app is not None and (len(rows) == 1 or app['btn'] == 'New Invoice'), f'ROW {dev}: the Kleins\' application row, with its own New Invoice when there are several rows: {rows}')
    if app:
        n0 = await js(pg, "return (DB.clients.find(x => x.id === 'cl121').invoices || []).filter(i => i.status === 'draft').length;")
        await pg.locator(f'.view.on [data-ydrow="{app["id"]}"] .yd-t').first.click(); await pg.wait_for_timeout(700)
        r = await js(pg, "return { view, billTab: typeof billTab !== 'undefined' ? billTab : '', job: typeof blProgJob !== 'undefined' ? blProgJob : '', n: (DB.clients.find(x => x.id === 'cl121').invoices || []).filter(i => i.status === 'draft').length };")
        C.ok(r['view'] == 'billing' and r['billTab'] == 'progress' and r['job'] == 'p121' and r['n'] == n0,
             f'ROW {dev}: tapping the application row opens 121 State\'s Progress Billing (the application\'s lines), drafts nothing: {r} (drafts before {n0})')
    await menu(pg, 'billing')
    bad = await code_rows(pg, '#v-billing tr, #v-billing [data-blact], #v-billing .card, #v-billing .gcard, .view.on [data-ydrow], .view.on button')
    n = len(await js(pg, ROWS_TEXT, '#v-billing tr, #v-billing [data-blact], .view.on [data-ydrow], .view.on button'))
    C.ok(n > 0 and not bad, f'ROW {dev}: no row or button in the Billing queue reads like code ({n} read): {bad[:3]}')
    await menu(pg, 'clients')
    bad = await code_rows(pg, '.view.on [data-ydrow], .view.on button')
    C.ok(not bad, f'ROW {dev}: no row on Clients\' Need You reads like code: {bad[:3]}')
    C.ok(not errs, f'ROW {dev}: no page errors: {errs[:3]}')
    await b.close()


async def t_memo(C, p):
    """the queue's memo answers what a fresh read answers (speed_test's memo check, on the readers this page uses): the
    wrappers that decorate readyToBill's and billingRows' rows decorate copies, never the cached rows"""
    b, pg, errs = await open_app(p)
    await sign_in(pg, 'u_billing')
    r = await pg.evaluate("""() => { SPD.check = true; SPD.bad = [];
      for (const v of ['clients', 'billing', 'clients']) { clientOpen = null; docOpen = null; view = v; render(); }
      for (const id of ['cl121', 'cl45']) { slOpenClient(id); render(); }
      SPD.check = false; return SPD.bad.filter(x => /readyToBill|billingRows|rbReady/.test(x.fn)).map(x => x.fn + ': ' + String(x.had).slice(0, 120)); }""")
    C.ok(not r, f'MEMO: the Billing queue\'s memo answers as a fresh read on Clients, a client and Billing: {r[:2]}')
    C.ok(not errs, f'MEMO: no page errors: {errs[:3]}')
    await b.close()


async def main():
    C = Checks()
    only = sys.argv[1:] or ['DEP', 'TODAY', 'PRO', 'ROW', 'BLANK', 'MEMO']
    async with async_playwright() as p:
        for phone in (False, True):
            if 'DEP' in only: await t_deposit(C, p, phone)
            if 'TODAY' in only: await t_today(C, p, phone)
            if 'PRO' in only: await t_progress(C, p, phone)
            if 'ROW' in only: await t_rows(C, p, phone)
            if 'BLANK' in only: await t_blank(C, p, phone)
        if 'MEMO' in only: await t_memo(C, p)
    sys.exit(C.done())

asyncio.run(main())
