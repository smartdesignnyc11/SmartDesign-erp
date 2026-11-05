"""The billing person's path to a new invoice, counted in taps (BACKLOG 1.36, journeys J8 and J9; 11-05).

What was wrong. On the 11-03 Sales pages billing reached a new invoice through Clients' All, the client, Contract and
Billing and the old Billing Record, then typed the signed contract's deposit by hand: J8 took 28 taps on the desktop and
30 on the phone (24 and 26 before), J9 27 and 28 (23 and 24 before), though the Billing queue already knew what was due.

DEP  The Ashbys sign (the owner records it, the hand-off before billing). Billing: Clients opens on Need You, which names
     the Ashbys with the deposit due (the Billing queue's own rule, readyToBill); the client opens on Contract and
     Billing; its blue New Invoice opens the queue's own Deposit Invoice sheet at the contract's 25%; Create makes one
     line of $22,780, no retainage, due on receipt, tied to the contract and the job, a draft, opened, with a toast
     that names it with Open. At most 4 taps from sign-in (the menu entry, the row, New Invoice, Create).
PRO  The Kleins (121 State, the seeded job with measured work ready to bill and CO-2026-001 approved): Need You names
     the measured work; New Invoice opens the job's application (the queue's own draft: the field's measures, the
     contract's retainage, every approved change order as a line), opened with its toast. At most 3 taps.
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


async def js(pg, body, arg=None):
    return await pg.evaluate("async (arg) => { const sleep = ms => new Promise(r => setTimeout(r, ms)); " + body + " }", arg)


class Taps:
    """the person's taps: every click this suite makes on the page, and the menu entry (one tap, reached by go())"""
    def __init__(self, pg): self.pg, self.n = pg, 0

    async def menu(self, v):
        self.n += 1; await go(self.pg, v); await self.pg.wait_for_timeout(300)

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
    # drafted, the deposit leaves Need You's reason and the page's fill
    await go(pg, 'clients')
    row, _ = await need_row(pg, 'Wren & Julian Ashby')
    C.ok('ready to bill' not in row['text'], f'DEP {dev}: drafted, the deposit is no longer "ready to bill" on Need You: {row["text"][:160]!r}')
    C.ok(not errs, f'DEP {dev}: no page errors: {errs[:3]}')
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
               open: !!(docOpen && docOpen.id === i.id), toast: t ? t.innerText : '' };""")
    C.ok(bool(r) and r['ret'] > 0 and r['dep'] and r['billed'] > 0, f'PRO {dev}: New Invoice drafts the job\'s application: the measured work billed, the contract\'s retainage, its deposit named: {r}')
    C.ok(bool(r) and any('CO-2026-001' in x for x in r['co']), f'PRO {dev}: the approved change order is a line on it: {r and r["co"]}')
    C.ok(bool(r) and r['open'] and (r['number'] in r['toast']) and 'Open' in r['toast'], f'PRO {dev}: the application opens, and the toast names it with Open: {r}')
    C.ok(T.n <= PIN['PRO'], f'PRO {dev}: {T.n} taps from sign-in to the drafted application, at most {PIN["PRO"]}')
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


async def main():
    C = Checks()
    only = sys.argv[1:] or ['DEP', 'PRO', 'BLANK']
    async with async_playwright() as p:
        for phone in (False, True):
            if 'DEP' in only: await t_deposit(C, p, phone)
            if 'PRO' in only: await t_progress(C, p, phone)
            if 'BLANK' in only: await t_blank(C, p, phone)
    sys.exit(C.done())

asyncio.run(main())
