"""Lane 1, round one: billing and cash tell the truth (docs/loop/round1/TRIAGE.md classes 1, 2, and the money parts of
3, 7 and 8; journeys J8, J9 and J10). Each check is done as the person, through the screens, on the desktop (1440)
and the phone (390), and the outcome is read in the records. Invented data only (the Ashbys' 214 Lincoln Place job is
the walk's own invented client).

DEP  The deposit is its own invoice (decision 5, adopted as a reversible default). The owner records the Ashbys'
     signature; billing opens Billing and the deposit is in the queue (Ready to Bill), with the 2-business-day date.
     Draft opens the Deposit Invoice sheet at the contract's 25%; Create makes one line of $22,780 (25% of $91,120),
     no retainage, due on receipt, tied to the contract, and nothing on the schedule of values moves.
PRO  Each progress application credits the deposit pro rata: 10% on a $20,000 line takes $500 (25%) of the deposit
     off what is due, on the screen and in the record; the SOV lines' % complete never carries the deposit.
CASH No bank line, not collected: Rivera's $21,350 (7/30, 8/14), never seen at the bank, is outside Cash Today, the
     P&L's collected and cash-basis revenue, and its invoices do not read Paid; each screen says "recorded, not yet
     in the bank". Safe to Spend reads one value on every screen that names it, with what is set aside.
Q    The Billing Queue never offers a one-tap Send on an unfinished draft row, and proposes no billing on a job
     billed ahead without the reason on the row.
TYPED A payment typed by hand is never offered as a bank line to match.

    python3 tests/billing_truth_test.py            (through tests/slot.sh)
"""
import asyncio, re, sys
from harness import *

LINES = [  # the Ashbys' 12 lines, $91,120 (sim/cycle_book.json's takeoff, rounded to the walk's contract)
    ('Demolition and protection', 9200), ('Framing', 11400), ('Plumbing rough and finish', 12600), ('Electrical rough and finish', 10800),
    ('Drywall and cement board', 6400), ('Tile: floors and walls', 9800), ('Cabinetry install', 7200), ('Doors and trim', 5600),
    ('Paint', 4800), ('Plumbing fixture allowance', 6500), ('Lighting allowance', 3820), ('Supervision and fee', 3000),
]
CONTRACT = sum(a for _, a in LINES)   # 91,120
DEPOSIT = round(CONTRACT * 0.25, 2)   # 22,780


async def js(pg, body, arg=None):
    return await pg.evaluate("async (arg) => { const sleep = ms => new Promise(r => setTimeout(r, ms)); " + body + " }", arg)


async def fresh(p, uid, phone=False):
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, uid)
    return b, pg, errs


async def nav(pg, phone, grp):
    """the person's own tap on the menu: the phone's bar, or the desktop's rail"""
    sel = f'#mtabs button[data-mv="{grp}"]' if phone else f'#nav-groups button[data-grp="{grp}"]'
    await pg.locator(sel).first.click()
    await pg.wait_for_timeout(400)


async def tap_text(pg, sel, text):
    """tap the first visible control matching sel whose own label is text"""
    loc = pg.locator(sel).filter(has_text=re.compile('^\\s*' + re.escape(text) + '\\s*$'))
    n = await loc.count()
    for i in range(n):
        if await loc.nth(i).is_visible():
            await loc.nth(i).click(); await pg.wait_for_timeout(400); return True
    return False


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


async def owner_signs(pg, S):
    """the owner records the Ashbys' signed copy on the estimate (the J4 step before this journey), through its sheet"""
    await js(pg, "view = 'clients'; clientOpen = arg.cid; clientTab = 'fin'; finTab = 'estimates'; docOpen = { kind: 'estimate', id: arg.eid }; render(); await sleep(300);", S)
    if not await tap_text(pg, f'#doc-{S["eid"]} [data-docact="lkapprove"], #doc-{S["eid"]} button', 'Record Client Approval'):
        await tap_text(pg, f'#doc-{S["eid"]} summary', 'More')
        await pg.locator(f'#doc-{S["eid"]} [data-docact="lkapprove"]').first.click(); await pg.wait_for_timeout(400)
    await pg.locator('#mbm [data-f="why"]').fill('Signed copy by email from Wren Ashby, 9/3 (signed PDF on file)')
    await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(700)
    return await js(pg, "const c = DB.clients.find(x => x.id === arg.cid), e = c.estimates.find(x => x.id === arg.eid); return [e.status, e.projectId];", S)


async def t_deposit(C, p, phone):
    dev = 'phone' if phone else 'desktop'
    b, pg, errs = await fresh(p, 'u_owner', phone)
    S = await js(pg, SIGNED_SETUP, LINES)
    st = await owner_signs(pg, S)
    C.ok(st == ['converted', S['pid']], f'DEP {dev}: the owner records the signature and the contract is on 214 Lincoln ({st})')
    await sign_in(pg, 'u_billing')
    await nav(pg, phone, 'billing')
    # the deposit waits in Billing's queue (Ready to Bill) from the hour it is signed, with its 2-business-day date
    q = await js(pg, """const v = document.getElementById('v-billing'); const txt = v ? v.innerText : '';
      const btn = [...document.querySelectorAll('#v-billing [data-blact]')].find(b => /deposit/i.test(b.dataset.blact) && b.getClientRects().length);
      const row = btn && (btn.closest('tr, .gcard, .card, [data-edit]') || btn.parentElement);
      return { has: /214 Lincoln/.test(txt) && /deposit/i.test(txt), id: btn ? btn.dataset.blact : '', label: btn ? btn.innerText.trim() : '',
               row: row ? row.innerText.replace(/\\s+/g, ' ') : '' };""")
    C.ok(q['has'] and q['id'], f'DEP {dev}: the signed contract\'s deposit waits in Billing\'s queue (Ready to Bill): {q}')
    C.ok(bool(re.search(r'invoice by 9/(4|7|8)', q['row'])) and 'no retainage' in q['row'], f'DEP {dev}: the row says no retainage and the 2-business-day date: {q["row"][:200]!r}')
    if not q['id']:
        await b.close(); return
    await pg.locator(f'[data-blact="{q["id"]}"]').first.click(); await pg.wait_for_timeout(500)
    m = await js(pg, "const m = document.getElementById('mbm'); return m ? { title: m.querySelector('h3') ? m.querySelector('h3').innerText : '', pct: (m.querySelector('#dep-pct') || {}).value, amt: (m.querySelector('#dep-amt') || {}).value, ok: (m.querySelector('#mbm-ok') || {}).innerText } : null;")
    C.ok(bool(m) and 'Deposit Invoice' in m['title'] and m['pct'] == '25' and abs(float(m['amt'] or 0) - DEPOSIT) < 0.01 and m['ok'] == 'Create Deposit Invoice',
         f'DEP {dev}: Draft opens the Deposit Invoice sheet at the contract\'s 25%, ${DEPOSIT:,.2f}: {m}')
    if not m:
        await b.close(); return
    await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(700)
    r = await js(pg, """const c = DB.clients.find(x => x.id === arg.cid);
      const I = (c.invoices || []).filter(i => i.status !== 'void');
      const dep = I.find(i => i.depositOf === arg.eid && i.mode !== 'sov');
      const t = document.getElementById('toast');
      return { n: I.length, sov: I.filter(i => i.mode === 'sov').length, dep: dep && { lines: dep.lines.length, total: docTotal(dep).total, ret: +dep.retainagePct || 0,
               due: dep.due, date: dep.date, terms: dep.terms, status: dep.status, project: dep.projectId, number: dep.number },
               open: !!(docOpen && dep && docOpen.id === dep.id), toast: t ? t.innerText : '',
               sovPct: (c.sov || []).map(v => sovBilled(c, v.id)).reduce((a, x) => a + x, 0),
               queue: billingRows().filter(r => r.kind === 'ready' && r.rtb && r.rtb.kind === 'deposit').length,
               print: dep && typeof docPrintHtml === 'function' ? docPrintHtml(c, dep).replace(/<[^>]+>/g, ' ') : '' };""", S)
    C.ok('Deposit Invoice' in r['print'] and 'deposit is credited against the progress applications' in r['print'] and 'Retainage is held' not in r['print'],
         f'DEP {dev}: it prints as a Deposit Invoice with its own footer, not the construction one: {r["print"][-300:]!r}')
    d = r['dep'] or {}
    C.ok(bool(d) and d['lines'] == 1 and abs(d['total'] - DEPOSIT) < 0.01 and d['ret'] == 0 and d['due'] == d['date'] and d['project'] == S['pid'] and d['status'] == 'draft',
         f'DEP {dev}: one line of ${DEPOSIT:,.2f}, no retainage, due on receipt, on 214 Lincoln, a draft for review: {r}')
    C.ok(r['sov'] == 0 and r['sovPct'] == 0, f'DEP {dev}: nothing on the schedule of values moves (no SOV invoice, 0% billed on every line): {r["sov"]} {r["sovPct"]}')
    C.ok(r['open'] and 'Open' in r['toast'] and (d.get('number') or '#') in r['toast'], f'DEP {dev}: the deposit opens, and the toast names it with Open: {r["toast"]!r}')
    C.ok(r['queue'] == 0, f'DEP {dev}: the deposit leaves Ready to Bill once drafted ({r["queue"]} left)')
    C.ok(not errs, f'DEP {dev}: no page errors: {errs[:3]}')
    await b.close()


async def t_prorata(C, p, phone):
    """a progress application credits the deposit pro rata, and the SOV never carries it"""
    dev = 'phone' if phone else 'desktop'
    b, pg, errs = await fresh(p, 'u_owner', phone)
    S = await js(pg, SIGNED_SETUP, LINES)
    await owner_signs(pg, S)
    # the deposit invoiced, sent and paid, its payment matched to the bank's line (J8 done)
    await js(pg, """const c = DB.clients.find(x => x.id === arg.cid), e = c.estimates.find(x => x.id === arg.eid);
      const inv = newDoc(c, 'invoice', { mode: 'items' }); Object.assign(inv, { template: 'construction', projectId: arg.pid, depositOf: e.id, title: 'Deposit — 25% of the contract', terms: 'Due on receipt', retainagePct: 0, status: 'sent', sentAt: today() });
      inv.due = inv.date; inv.lines = [{ id: uid('l'), item: 'Deposit on the contract', qty: 1, unit: 'ls', rate: """ + str(DEPOSIT) + """, taxable: false }]; docMark(inv);
      const t = { id: uid('t'), acct: 'ac1', date: today(), amt: """ + str(DEPOSIT) + """, desc: 'DEPOSIT ASHBY WREN 214 LINCOLN', cat: 'income', source: 'ofx', status: 'categorized' };
      DB.txns.push(t); c.payments.push({ id: uid('py'), invoiceId: inv.id, date: today(), amount: """ + str(DEPOSIT) + """, method: 'ACH', ref: 'deposit', txnId: t.id }); inv.status = 'paid'; save();""", S)
    await sign_in(pg, 'u_billing')
    # billing starts the application from the contract and bills 10% of framing ($11,400) this period
    await js(pg, "view = 'clients'; clientOpen = arg.cid; clientTab = 'fin'; finTab = 'estimates'; docOpen = { kind: 'estimate', id: arg.eid }; render(); await sleep(300);", S)
    ok = await tap_text(pg, f'#doc-{S["eid"]} [data-docact="progress"]', 'New Progress Invoice')
    if not ok:
        await pg.locator(f'#doc-{S["eid"]} [data-docact="progress"]').first.click(); await pg.wait_for_timeout(500)
    if await pg.locator('#mbm #mbm-ok').count():
        await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(600)
    inv = await js(pg, "const c = DB.clients.find(x => x.id === arg.cid); const i = c.invoices.find(i => i.mode === 'sov' && i.status === 'draft'); return i ? { id: i.id, line: (i.lines.find(l => /Framing/.test(((c.sov.find(v => v.id === l.sovId) || {}).desc) || '')) || {}).id } : null;", S)
    C.ok(bool(inv and inv['line']), f'PRO {dev}: New Progress Invoice opens a draft application with the framing line: {inv}')
    if not inv or not inv['line']:
        await b.close(); return
    box = pg.locator(f'#doc-{inv["id"]} tr[data-line="{inv["line"]}"] [data-f="pct"]').first
    await box.fill('10'); await box.dispatch_event('change'); await pg.wait_for_timeout(500)
    r = await js(pg, """const c = DB.clients.find(x => x.id === arg.cid), i = c.invoices.find(x => x.id === arg.id), t = docTotal(i);
      const v = document.getElementById('doc-' + i.id); const txt = v ? v.innerText : '';
      return { gross: r2(t.sub - t.disc), dep: t.dep || 0, total: t.total, applied: +i.depositApplied || 0, screen: /Less deposit applied/.test(txt),
               line: i.lines.find(l => l.id === arg.line).pct, others: i.lines.filter(l => l.id !== arg.line).reduce((a, l) => a + (+l.pct || 0), 0) };""", inv | {'cid': S['cid']})
    C.ok(abs(r['gross'] - 1140) < 0.01 and abs(r['dep'] - 285) < 0.01 and r['screen'],
         f'PRO {dev}: 10% of framing ($1,140) takes 25% of it ($285) off the deposit, shown as Less deposit applied: {r}')
    C.ok(r['line'] == 10 and r['others'] == 0, f'PRO {dev}: the SOV lines carry only the work (10% on framing, 0 elsewhere): {r}')
    C.ok(not errs, f'PRO {dev}: no page errors: {errs[:3]}')
    await b.close()


async def click_js(pg, sel):
    ok = await pg.evaluate("s => { const e = [...document.querySelectorAll(s)].find(x => x.offsetParent) || document.querySelector(s); if (!e) return false; e.click(); return true }", sel)
    await pg.wait_for_timeout(300)
    return ok


async def nav_to(pg, grp, sub=None, tabs=()):
    """the rail button, the sub-nav button, then each tab (finance_xcheck's way); the app's own navigation only when
    there is no button for it"""
    target = sub or grp
    ok = await click_js(pg, f'#nav [data-grp="{grp}"]')
    if sub and ok and await pg.evaluate('view') != sub: await click_js(pg, f'[data-sub="{sub}"]')
    if await pg.evaluate('view') != target: await go(pg, target)
    for t in tabs: await click_js(pg, t)


MONEY = r'(−|-)?\$([\d,]+(?:\.\d\d)?)'


def money_after(text, label):
    m = re.search(label + r'[^\n$]{0,40}\n?\s*' + MONEY, text)
    if not m: return None
    v = float(m.group(2).replace(',', ''))
    return -v if m.group(1) else v


async def t_cash(C, p, phone):
    """Rivera's $21,350 (7/30 and 8/14) never reached the bank: it is not cash, not collected and not Paid"""
    dev = 'phone' if phone else 'desktop'
    b, pg, errs = await fresh(p, 'u_controller', phone)
    # Reports > Cash Forecast: the figure the forecast starts from is the bank's own
    await nav_to(pg, 'reports', None, ['#v-reports [data-repgrp="cash"]', '#v-reports [data-reptab="cash13"]'])
    if await pg.evaluate('repTab') != 'cash13':   # no visible tab for it on this device: the app's own navigation
        await js(pg, "repTab = 'cash13'; render(); await sleep(300);")
    t = await pg.evaluate("() => (document.getElementById('v-reports') || {}).innerText || ''")
    bank = await js(pg, "return companyBalance().cash;")
    fc = await js(pg, "return cashForecast().cash;")
    C.ok(abs(fc - bank) < 0.01, f'CASH {dev}: the forecast starts from the bank ({fc} against the bank {bank}), not the bank plus the $21,350 recorded')
    C.ok('recorded, not yet in the bank' in t and 'Rivera' in t and '205,58' not in t, f'CASH {dev}: the Cash Forecast names $21,350 recorded, not yet in the bank, outside the figure: {t[t.find("13-Week") - 300:t.find("13-Week")][:300]!r}')
    # the P&L's collected and cash-basis revenue
    pl = await js(pg, "const P = companyPL(['2026-01-01', today()]); const k = DB.company.basis; DB.company.basis = 'cash'; const Q = companyPL(['2026-01-01', today()]); DB.company.basis = k; return { collected: P.collected, unbanked: P.unbanked, cashIncome: Q.income };")
    C.ok(abs(pl['collected'] - 169750) < 0.01 and abs((pl.get('unbanked') or 0) - 21350) < 0.01 and abs(pl['cashIncome'] - 169750) < 0.01,
         f'CASH {dev}: collected and cash-basis revenue are $169,750 (bank-backed), $21,350 apart: {pl}')
    # Rivera's invoices on Billing > Invoices do not read Paid
    await sign_in(pg, 'u_billing')
    await nav(pg, phone, 'billing')
    await click_js(pg, '#v-billing [data-billtab="invoices"]')
    inv = await pg.evaluate("""() => { const v = document.getElementById('v-billing'); const rows = [...v.querySelectorAll('tr, .gcard, [data-edit]')].filter(r => /INV-2026-D45/.test(r.innerText));
        return rows.map(r => r.innerText.replace(/\\s+/g, ' ')).slice(0, 4); }""")
    C.ok(len(inv) >= 2 and all('recorded, not yet in the bank' in r for r in inv) and not any(re.search(r'\bpaid\b', r) for r in inv),
         f'CASH {dev}: Rivera\'s two invoices read "recorded, not yet in the bank", never Paid: {inv}')
    # the invoice itself: Paid is not reached, and the pill says how much the bank has not seen
    await js(pg, "const c = DB.clients.find(x => x.id === 'cl45'); clientOpen = c.id; docOpen = { kind: 'invoice', id: 'inD45r' }; view = 'clients'; clientTab = 'fin'; render(); await sleep(300);")
    d = await js(pg, "const v = document.getElementById('doc-inD45r'); if (!v) return null; const on = v.querySelector('.status-flow .on'); const blue = v.querySelector('.docacts .btn.primary'); return { on: on ? on.innerText : '', pill: (v.querySelector('[data-unbanked]') || {}).innerText || '', blue: blue ? blue.innerText : '' };")
    C.ok(bool(d) and d['on'].lower() != 'paid' and '5,000' in d['pill'], f'CASH {dev}: INV-2026-D45-R stops short of Paid and says $5,000 recorded, not yet in the bank: {d}')
    C.ok(not errs, f'CASH {dev}: no page errors: {errs[:3]}')
    await b.close()


async def t_safe(C, p, phone):
    """Safe to Spend is one figure on every screen that names it, with what is set aside. A $200,000 order due this
    week puts the 13-week low under truly ours, so a screen that prints truly ours under the label shows a second value."""
    dev = 'phone' if phone else 'desktop'
    b, pg, errs = await fresh(p, 'u_owner', phone)
    await js(pg, """const p = DB.projects.find(x => x.id === 'p121');
      DB.pos.push({ id: uid('po'), number: 'PO-2026-990', vendor: 'Invented Steel Co', projectId: p.id, status: 'issued', date: today(), expected: today(),
                    lines: [{ id: uid('pl'), item: 'Structural steel package', qty: 1, unit: 'ls', price: 200000 }], tax: 0, shipping: 0 }); save(); render();""")
    want = await js(pg, "return PRED.safeToSpend.figure();")
    truly = await js(pg, "return companyBalance().trulyOurs;")
    seen = []
    # Home: the brief's Accounting card and its cash sentence (behind the quiet line and Read the Full Brief)
    await nav_to(pg, 'home')
    await click_js(pg, '.view.on .td2-quiet')
    t = await pg.evaluate("() => document.body.innerText")
    m = re.search(MONEY + r'\s*\n\s*Safe to Spend', t)
    m and seen.append(('Today Pulse', (-1 if m.group(1) else 1) * float(m.group(2).replace(',', ''))))
    full = pg.get_by_text('Read the Full Brief', exact=True)
    if await full.count(): await full.first.click(); await pg.wait_for_timeout(500)
    t = await pg.evaluate("() => document.body.innerText")
    v = money_after(t, r'Safe to spend')
    v is not None and seen.append(('Home brief', v))
    m = re.search(r'but ' + MONEY + r' short', t)
    m and seen.append(('Home brief sentence', -float(m.group(2).replace(',', ''))))
    # the Dashboard's cash tile
    await nav_to(pg, 'home', 'dashboard')
    t = await pg.evaluate("() => (document.getElementById('v-dashboard') || {}).innerText || ''")
    m = re.search(MONEY + r'\s*\n\s*Safe to Spend', t)
    m and seen.append(('Dashboard tile', (-1 if m.group(1) else 1) * float(m.group(2).replace(',', ''))))
    C.ok(abs(want - truly) > 1000, f'SAFE {dev}: the setup puts the 13-week low under truly ours ({want} against {truly})')
    C.ok(len(seen) >= 2 and all(abs(v - want) < 1 for _, v in seen), f'SAFE {dev}: every screen that names Safe to Spend reads {want}: {seen}')
    why = await js(pg, "return typeof PRED.safeToSpend.setAside === 'function' ? PRED.safeToSpend.setAside() : '';")
    C.ok('in the bank' in why and 'billed ahead' in why and 'not counted' in why, f'SAFE {dev}: one line says what is set aside and what is not counted: {why!r}')
    C.ok(not errs, f'SAFE {dev}: no page errors: {errs[:3]}')
    await b.close()


async def t_queue(C, p, phone):
    """the Billing Queue: no one-tap Send on a draft row; nothing proposed on a job billed ahead without the reason"""
    dev = 'phone' if phone else 'desktop'
    b, pg, errs = await fresh(p, 'u_billing', phone)
    # a half-filled progress draft on 121 State, as billing left it
    await js(pg, """const c = DB.clients.find(x => x.id === 'cl121'), e = c.estimates.find(x => x.status === 'converted');
      const inv = ctProgressInvoice(c, e); inv.projectId = 'p121'; inv.lines.slice(0, 2).forEach(l => l.pct = 5); save(); render();""")
    await nav(pg, phone, 'billing')
    q = await js(pg, """const v = document.getElementById('v-billing');
      const btns = [...v.querySelectorAll('[data-blact]')].filter(b => b.getClientRects().length).map(b => ({ id: b.dataset.blact, label: b.innerText.trim() }));
      const rows = billingRows();
      const draft = rows.filter(r => r.kind === 'draft').map(r => r.id);
      const ahead = rows.filter(r => r.kind === 'ready' && r.job && r.job.id === 'p121' && r.rtb && ['application', 'floated', 'progress'].includes(r.rtb.kind));
      const held = rows.filter(r => r.kind === 'held' && r.job && r.job.id === 'p121');
      return { draftBtns: btns.filter(b => draft.includes(b.id)).map(b => b.label), ahead: ahead.map(r => r.what), held: held.map(r => r.why),
               win: rows.filter(r => /Windows/.test(r.what + ' ' + r.why)).map(r => r.amount) };""")
    C.ok(q['draftBtns'] and not any(l.lower() == 'send' for l in q['draftBtns']), f'Q {dev}: a draft row offers Review, never a one-tap Send: {q["draftBtns"]}')
    C.ok(not q['ahead'] and q['held'] and all('ahead of the work' in w for w in q['held']), f'Q {dev}: 121 State, billed ahead, has nothing ready to bill; what waits says why: {q}')
    C.ok(q['win'] and all(abs(a - 10170) < 1 for a in q['win']), f'Q {dev}: the windows bought and delivered, not billed, read $10,170 (the disputed $3,800 never bills): {q["win"]}')
    C.ok(not errs, f'Q {dev}: no page errors: {errs[:3]}')
    await b.close()


async def t_typed(C, p, phone):
    """a payment typed by hand (Satish's $7,400 ACH, the Rosario Zelle) is never offered as a bank line to confirm"""
    dev = 'phone' if phone else 'desktop'
    b, pg, errs = await fresh(p, 'u_controller', phone)
    await js(pg, "try { truthProposeAll(); } catch (e) {} save(); render();")
    await nav_to(pg, 'bank')
    sec = await pg.evaluate("() => [...document.querySelectorAll('#v-bank .prop-card')].map(e => e.innerText).join('\\n')")
    typed = await js(pg, "return proposals().filter(t => !bfBacked(t)).map(t => t.desc);")
    C.ok(not typed and 'SATISH' not in sec.upper() and 'ROSARIO' not in sec.upper(), f'TYPED {dev}: no line typed by hand waits as a match to confirm: {typed} {sec[:200]!r}')
    # each Confirm the person can see has what it links, and the "possibly already paid" warning, beside it
    rows = await pg.evaluate("""() => [...document.querySelectorAll('#v-bank .prop-card button')].filter(b => /^Confirm$/.test(b.innerText.trim()) && b.getClientRects().length)
        .map(b => { let r = b; while (r && !(r.innerText || '').includes('·')) r = r.parentElement; const x = b.closest('.prop-row, .pr-card, .pr-row') || r; return x ? x.innerText : ''; })""")
    alb = [r for r in rows if 'ALBERTO' in r.upper()]
    C.ok(rows and all('→' in r for r in rows) and alb and all('Possibly already paid' in r for r in alb),
         f'TYPED {dev}: every visible Confirm shows what it links and the possibly-paid warning: {[r[:160] for r in rows]}')
    C.ok(not errs, f'TYPED {dev}: no page errors: {errs[:3]}')
    await b.close()


async def main():
    C = Checks()
    only = sys.argv[1:] or ['DEP', 'PRO', 'CASH', 'SAFE', 'Q', 'TYPED']
    async with async_playwright() as p:
        for phone in (False, True):
            if 'DEP' in only: await t_deposit(C, p, phone)
            if 'PRO' in only: await t_prorata(C, p, phone)
            if 'CASH' in only: await t_cash(C, p, phone)
            if 'SAFE' in only: await t_safe(C, p, phone)
            if 'Q' in only: await t_queue(C, p, phone)
            if 'TYPED' in only: await t_typed(C, p, phone)
    sys.exit(C.done())

asyncio.run(main())
