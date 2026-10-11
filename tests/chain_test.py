"""chain: one new job, end to end, in one browser, then every report read against the raw records (Alan, 2026-10-11).

"Have we run the whole chain: estimates, invoices, purchasing from the estimate, progress billing, matching transactions
and POs to line items, then the reports on it; did everything save; was the reporting accurate? Make sure overhead
transactions are recorded properly and show in reporting for true project profitability."

One fresh browser, the seeded firm as the backdrop, and a NEW invented client and job (never the seeded ones):
  1 client   a lead becomes a client; a project; a 7-line estimate (labor, materials, a sub, an allowance, a fee);
             sent; the client signs on the portal; the contract and SOV come from the estimate
  2 buy      Order from the Buy Board (buyOrderDialog > poAction issue) for three lines with three vendors; one over
             the owner's threshold; a sub commitment for the plumbing line; the Owner approves in Approvals
  3 receive  two POs received (one partial) and billed from the receiving toast; vendor bills by mail (a Loaded
             Workspace with invented threads) land on their POs; one bill over its PO is approved at the PO amount
             with the difference disputed; the PM recommends and the Owner approves; the bills are paid
  4 pay      hours on the job and office hours; a payroll run; bank and card statements through Import Statement
             (CSV): vendor payments, a card purchase for the client, payroll debits, overhead (rent, insurance,
             software, office supplies, vehicle, a line the controller codes to overhead); every line matched to its
             bill/PO line (and the estimate line), payroll to its run, the reimbursable to billing, overhead to its
             overhead account
  5 bill     measured % on site; a change order approved on the portal; the pay application from the SOV (per-line
             holds, retainage, stored materials, the CO from 0); the purchase bought for the client billed at cost
             plus markup; sent; the client pays; the deposit matched to the invoice
  6 close    August and September closed by the Owner (tie-out, seal); nothing reopened
  7 reports  every figure computed here from the records this run created, never by the function the report uses,
             and read off every surface that shows it
  8 overhead overhead posts to overhead accounts, shows in the P&L and coverage; the job's gross and net margin
             after the overhead allocation, the method stated the same everywhere
  9 save     saveNow, reload, every record and link still there; the reports again

Where a person clicks, this clicks (Playwright pointer clicks on the real buttons and fields). The same functions the
buttons call are used, and named in the trace, only for: time entries (the Add Time drawer is filled for each entry
except the last ones, typed through saveTime's own collect), the foreman's measured % (prgSet, the function the
Measure sheet calls) and reading figures.

The trace is written to review/chain/trace.md. The last line is `CHAIN N checks · F failed`; exit 1 on any failure.

    python3 chain_test.py              the whole chain
    python3 chain_test.py --upto 3     stop after step 3 (development)
"""
import asyncio, sys, os, re, json, argparse, tempfile
from harness import *

TRACE_DIR = os.path.join(ROOT, 'review', 'chain')

# ---------------------------------------------------------------- the invented job
CLIENT = 'Imogen & Theo Varga'
EMAIL = 'imogen.varga@example.com'
JOB = '318 Clinton Street'
ADDR = '318 Clinton Street, Brooklyn — parlor kitchen and primary bath'
# item, price, budget (cost), vendor (who does it), kind
LINES = [
    ('Demolition & protection', 9500, 6000, '', 'labor'),
    ('Framing & blocking', 14000, 9000, '', 'labor'),
    ('Rough plumbing', 18000, 13500, 'Halvorsen Plumbing & Heating', 'sub'),
    ('Millwork – parlor kitchen cabinets', 32000, 24000, 'Fenwick Cabinetry', 'materials'),
    ('Tile – primary bath', 9800, 6800, 'Arcadia Tile Supply', 'materials'),
    ('Fixture allowance – primary bath', 8000, 8000, 'Kingsland Bath Supply', 'allowance'),
    ("General conditions & builder's fee", 9130, 0, '', 'fee'),
]
VENDORS = [('Fenwick Cabinetry', 'millwork', 'orders@fenwickcabinetry.example'),
           ('Arcadia Tile Supply', 'tile', 'sales@arcadiatile.example'),
           ('Kingsland Bath Supply', 'plumbing fixtures', 'counter@kingslandbath.example'),
           ('Halvorsen Plumbing & Heating', 'plumbing', 'office@halvorsenph.example')]

MODAL = """() => { const m = document.querySelector('#mbm'); if (!m || !m.getClientRects().length) return null;
  return { title: (m.querySelector('h3') || {}).innerText || '', text: m.innerText.slice(0, 1500),
           buttons: [...m.querySelectorAll('button')].filter(b => b.getClientRects().length).map(b => b.innerText.trim()).filter(Boolean),
           fields: Object.fromEntries([...m.querySelectorAll('[data-f]')].map(i => [i.dataset.f, i.type === 'checkbox' ? i.checked : i.value])) }; }"""
TOAST = "() => { const t = document.getElementById('toast'); return t ? t.innerText.replace(/\\s+/g, ' ').trim() : ''; }"
DRAWER = "() => { const d = document.querySelector('#drawer.on'); return d ? d.innerText.slice(0, 1500) : null; }"


class Chain:
    def __init__(self, pg, errs):
        self.pg, self.errs = pg, errs
        self.n = 0; self.fail = []; self.lines = []; self.ids = {}; self.figs = []; self.findings = []
        self.step_name = ''

    # ---- bookkeeping
    def step(self, title):
        self.step_name = title
        self.lines.append(f'\n## {title}\n')
        print(f'\n== {title}')

    def t(self, s):
        self.lines.append(f'- {s}')
        print('  ' + s)

    def ok(self, cond, msg, detail=''):
        self.n += 1
        if not cond:
            self.fail.append(f'[{self.step_name}] {msg}' + (f' — {detail}' if detail else ''))
            self.lines.append(f'  - FAIL {msg}' + (f' — `{str(detail)[:300]}`' if detail else ''))
            print('  FAIL', msg, ('— ' + str(detail)[:300]) if detail else '')
        return bool(cond)

    def fig(self, name, surface, seen, want, tol=1.0):
        """One report figure read off one surface, compared with the figure computed from the records."""
        good = seen is not None and want is not None and abs(seen - want) <= tol
        self.figs.append((name, surface, seen, want, good))
        self.ok(good, f'{name} on {surface}: {fmtm(seen)} (from the records {fmtm(want)})')
        self.lines.append(f'  - {"ok" if good else "MISMATCH"} {name} · {surface} · {fmtm(seen)} · records {fmtm(want)}')
        return good

    def rec(self, kind, key, val):
        self.ids.setdefault(kind, {})[key] = val

    def write(self):
        os.makedirs(TRACE_DIR, exist_ok=True)
        head = [f'# Chain trace: {JOB} for {CLIENT}', '',
                'Every step as a person did it, what was clicked, what was created (ids and links), and each figure read off',
                'each surface against the figure computed from the records this run created.', '']
        tail = ['', '## Ids', '', '```json', json.dumps(self.ids, indent=1, default=str), '```', '',
                f'CHAIN {self.n} checks · {len(self.fail)} failed']
        with open(os.path.join(TRACE_DIR, 'trace.md'), 'w', encoding='utf-8') as f:
            f.write('\n'.join(head + self.lines + tail) + '\n')

    # ---- the page
    async def js(self, src, arg=None):
        return await self.pg.evaluate(src, arg) if arg is not None else await self.pg.evaluate(src)

    async def wait(self, ms=250):
        await self.pg.wait_for_timeout(ms)

    async def as_(self, uid, view=None, setup=''):
        await self.pg.evaluate("([u, v, s]) => { signIn(u); if (s) (0, eval)(s); if (v) { view = v; } render(); }", [uid, view or '', setup])
        await self.wait(300)

    async def modal(self):
        return await self.pg.evaluate(MODAL)

    async def toast(self):
        return await self.pg.evaluate(TOAST)

    async def click(self, sel, wait=400, timeout=8000):
        await self.pg.locator(sel).first.click(timeout=timeout)
        await self.wait(wait)

    async def click_text(self, scope, rx, wait=400, timeout=8000):
        loc = self.pg.locator(f'{scope} button:visible, {scope} a:visible').filter(has_text=re.compile(rx)).first
        await loc.click(timeout=timeout)
        await self.wait(wait)

    async def modal_ok(self, wait=600):
        await self.pg.locator('#mbm #mbm-ok').click(timeout=6000)
        await self.wait(wait)

    async def fill(self, sel, val, tab=False):
        loc = self.pg.locator(sel).first
        await loc.fill(str(val))
        if tab: await loc.press('Tab')

    async def day(self, d):
        await self.pg.evaluate("d => appSetDay(d)", d)
        await self.wait(200)
        self.t(f'**{d}** (appSetDay: the one clock moves to the day)')


def fmtm(v):
    if v is None: return 'none'
    if isinstance(v, str): return v
    return ('−' if v < 0 else '') + '${:,.2f}'.format(abs(v))


def r2(x): return round(x + 1e-9, 2)


# ================================================================ 1. lead > client > project > estimate > signed
async def s1_client(C):
    C.step('1. Lead, client, project, estimate, signed on the portal, contract and SOV')
    await C.day('2026-09-03')
    # the PM takes the inquiry on the Lead Board
    await C.as_('u_alan', 'leads', "slOpen = '';")
    C.t(f"PM signs in; Sales > Lead Board opens on {await C.js('() => view')}")
    await C.click_text('section.view.on', r'^New Lead$')
    m = await C.modal()
    C.ok(m and m['title'] == 'New Lead', 'Lead Board > New Lead opens the lead sheet', m and m['title'])
    await C.fill('#mbm [data-f=name]', CLIENT)
    await C.fill('#mbm [data-f=phone]', '(718) 555-0142')
    await C.fill('#mbm [data-f=email]', EMAIL)
    await C.pg.select_option('#mbm [data-f=source]', 'Website / Google')
    await C.fill('#mbm [data-f=addr]', '318 Clinton Street, Brooklyn')
    await C.pg.select_option('#mbm [data-f=buildingType]', 'Townhouse')
    await C.fill('#mbm [data-f=value]', '100000')
    await C.fill('#mbm [data-f=notes]', 'Parlor floor kitchen and primary bath; the owners want to start before the holidays.')
    await C.modal_ok()
    lead = await C.js("n => { const l = (DB.leads || []).find(l => l.name === n); return l && {id: l.id, stage: l.stage}; }", CLIENT)
    C.ok(lead, 'the lead is on file', lead)
    C.rec('lead', 'id', lead and lead['id'])
    C.t(f"Lead Board > New Lead: name, phone, email, source, property, building, value, notes > New Lead → lead `{lead and lead['id']}`")
    # Won: the lead record has Won — Agreement Signed; the money decider is not marked met, so it asks
    on = await C.js("() => !!document.querySelector('section.view.on [data-slwon]')")
    if not on:
        await C.as_('u_alan', 'leads', f"slOpen = '{lead['id']}';")
    await C.click('section.view.on [data-slwon]')
    m = await C.modal()
    if m and m['title'] == 'Please Confirm':
        C.t(f"Won — Agreement Signed asks: \"{m['text'].splitlines()[1] if len(m['text'].splitlines()) > 1 else m['text']}\" > Yes, Continue")
        await C.modal_ok()
    cl = await C.js("n => { const l = DB.leads.find(l => l.name === n), c = DB.clients.find(c => c.id === l.clientId); return c && {id: c.id, stage: l.stage, contacts: c.contacts.map(x => x.email)}; }", CLIENT)
    C.ok(cl and cl['stage'] == 'won', 'Won turns the lead into a client', cl)
    if not cl: return False
    C.rec('client', 'id', cl['id'])
    C.t(f"Won — Agreement Signed → client `{cl['id']}` ({await C.toast()})")
    # a project for the client, from the client record
    await C.js("id => { view = 'clients'; clientOpen = id; clientTab = 'projects'; docOpen = null; render(); }", cl['id'])
    await C.wait(300)
    await C.click('section.view.on [data-newproj-for]')
    await C.fill('#e-name', JOB)
    await C.fill('#e-addr', ADDR)
    await C.fill('#e-start', '2026-09-08')
    await C.fill('#e-target', '2026-12-18')
    await C.pg.select_option('#e-tpl', 'tpl')
    await C.click('#d-save', 800)
    p = await C.js("n => { const p = DB.projects.find(p => p.project.name === n); return p && {id: p.id, client: p.clientId, tasks: p.tasks.length}; }", JOB)
    C.ok(p and p['client'] == cl['id'] and p['tasks'] > 10, 'New Project for This Client: the job belongs to the client, from the brownstone template', p)
    if not p: return False
    C.rec('project', 'id', p['id'])
    C.t(f"Client > Projects > New Project for This Client: name, address, start 9/8, target 12/18, template > Add Project → project `{p['id']}` ({p['tasks']} tasks)")
    # the estimate: Construction template, seven lines typed in the line editor
    await C.js("id => { view = 'clients'; clientOpen = id; clientTab = 'overview'; docOpen = null; render(); }", cl['id'])
    await C.wait(300)
    await C.click('section.view.on [data-newest]')
    await C.pg.check('#mbm input[value=construction]')
    await C.modal_ok(800)
    await C.fill('section.view.on [data-d=title]', 'Parlor kitchen and primary bath', tab=True)
    for i, (item, rate, cost, vendor, kind) in enumerate(LINES):
        if i > 0:
            await C.click('section.view.on [data-ctadd]', 300)
        await C.fill(f'section.view.on [data-ctf=item] >> nth={i}', item, tab=True)
        await C.fill(f'section.view.on [data-ctf=rate] >> nth={i}', rate, tab=True)
        await C.fill(f'section.view.on [data-ctf=cost] >> nth={i}', cost, tab=True)
        if vendor:
            await C.fill(f'section.view.on [data-ctf=vendor] >> nth={i}', vendor, tab=True)
        await C.wait(150)
    est = await C.js("""id => { const c = DB.clients.find(c => c.id === id), e = c.estimates[c.estimates.length - 1];
        return {id: e.id, number: e.number, total: docTotal(e).total, template: e.template, projectId: e.projectId,
                lines: e.lines.map(l => ({id: l.id, item: l.item, rate: +l.rate, qty: +l.qty, cost: l.cost, code: lineCode(l, e), vendor: l.vendor || ''}))}; }""", cl['id'])
    C.ok(est and len(est['lines']) == 7 and abs(est['total'] - sum(x[1] for x in LINES)) < 0.01, f"the estimate holds 7 lines for {fmtm(sum(x[1] for x in LINES))}", est and est['total'])
    C.ok(est and est['projectId'] == p['id'], 'the estimate is on the job', est and est['projectId'])
    codes = [x['code'] for x in est['lines']] if est else []
    C.ok(len(set(codes)) >= 6, f'the lines span cost codes {codes}', codes)
    C.rec('estimate', 'id', est['id']); C.rec('estimate', 'number', est['number'])
    C.rec('estimate', 'lines', {x['item']: x['id'] for x in est['lines']})
    C.t(f"Client > New Estimate > Construction > Start Estimate; title; 7 lines typed (item, rate, cost, vendor) → `{est['number']}` "
        f"{fmtm(est['total'])}, codes {', '.join(codes)}")
    await C.click('section.view.on [data-docact=send]', 600)
    st = await C.js("([c, e]) => DB.clients.find(x => x.id === c).estimates.find(x => x.id === e).status", [cl['id'], est['id']])
    C.ok(st == 'sent', 'Mark Sent sends the estimate', st)
    C.t(f"Mark Sent → {st} ({await C.toast()})")
    # the client's portal user (Settings > Company Settings > Users), then the client signs on the portal
    await C.as_('u_owner', 'setup')
    await C.click('section.view.on [data-tl=proj]', 500)
    await C.fill('#u-name', 'Imogen Varga')
    await C.pg.select_option('#u-role', 'client')
    await C.fill('#u-contact', EMAIL)
    await C.click('#u-add', 400)
    u = await C.js("e => { const u = DB.users.find(u => u.contact === e); return u && {id: u.id, clientId: u.clientId || ''}; }", EMAIL)
    C.ok(u and u['clientId'] == cl['id'], "Settings > Users > Add user (role Client, the client's email) links the portal user to the client", u)
    if not u: return False
    C.rec('portalUser', 'id', u['id'])
    C.t(f"Settings > Company Settings > Users: Imogen Varga, Client, {EMAIL} > Add user → `{u['id']}` linked to `{u['clientId']}`")
    await C.as_(u['id'])
    sc = await C.js("() => { const s = eqScopeOf(); return {cid: s.cid, jobs: s.jobs.map(p => p.id), shown: (document.querySelector('section.view.on') || {}).innerText.slice(0, 300)}; }")
    C.ok(sc['cid'] == cl['id'] and sc['jobs'] == [p['id']], 'signed in on the portal, the client sees their own job only', sc)
    await C.click(f"section.view.on [data-papprove='estimate:{est['id']}']", 600)
    m = await C.modal()
    C.ok(m and 'Approve Proposal' in m['title'], 'the portal Approve opens the signature sheet', m and m['title'])
    await C.pg.check('#pa-agree')
    await C.modal_ok(900)
    sig = await C.js("""([c, e]) => { const cl = DB.clients.find(x => x.id === c), es = cl.estimates.find(x => x.id === e);
        return {status: es.status, approval: es.clientApproval || null, contract: cl.contract,
                sov: (cl.sov || []).filter(s => s.projectId === es.projectId).map(s => ({id: s.id, desc: s.desc, scheduled: +s.scheduled, lineRef: s.lineRef}))}; }""", [cl['id'], est['id']])
    C.ok(sig['status'] in ('approved', 'converted') and sig['approval'] and sig['approval'].get('via') == 'portal', 'the client signs on the portal (name typed, agreed)', sig['approval'])
    C.ok(abs((sig['contract'] or 0) - est['total']) < 0.01, f"the contract is the estimate total {fmtm(est['total'])}", sig['contract'])
    C.ok(len(sig['sov']) == 7 and all(s['lineRef'] for s in sig['sov']), 'the schedule of values has a line for each estimate line, linked back', sig['sov'])
    C.rec('sov', 'lines', {s['desc']: s['id'] for s in sig['sov']})
    C.t(f"Portal (signed in as `{u['id']}`): Approve > typed name, I approve > Approve {fmtm(est['total'])} → {sig['status']}; contract "
        f"{fmtm(sig['contract'])}; SOV {len(sig['sov'])} lines linked to the estimate lines")
    return True


# ================================================================ 2. purchasing from the estimate lines
async def s2_buy(C):
    C.step('2. Purchasing from the estimate: Buy Board orders, a sub commitment, the Owner approves')
    await C.day('2026-09-04')
    pid = C.ids['project']['id']; est = C.ids['estimate']['id']; L = C.ids['estimate']['lines']
    # the coordinator puts the four suppliers on file (Vendors > New Vendor), each with a certificate and a W-9
    await C.as_('u_chen', 'vendors')
    for name, trade, email in VENDORS:
        await C.as_('u_chen', 'vendors')
        await C.click('#btn-newvendor', 400)
        await C.fill('#e-name', name); await C.fill('#e-trade', trade); await C.fill('#e-email', email)
        await C.fill('#e-inscar', 'Hudson Mutual'); await C.fill('#e-insexp', '2027-06-30')
        if not await C.pg.is_checked('#e-w9'): await C.pg.check('#e-w9')
        await C.fill('#e-w9date', '2026-09-01')
        await C.click('#d-save', 400)
        v = await C.js("n => { const v = DB.vendors.find(v => v.name === n); return v && v.id; }", name)
        C.ok(v, f'vendor {name} is on file', v)
        C.rec('vendor', name, v)
    C.t(f"Vendors > New Vendor ×4 (name, trade, email, insurer, COI expiry 6/30/2027, W-9) → {', '.join(f'{k} `{v}`' for k, v in C.ids['vendor'].items())}")

    async def order(item, vendor, qty, unit, price):
        await C.as_('u_chen', 'proc', f"setCurrent('{pid}'); procMode = 'lines'; buyScope = ''; buyOpen = true;")
        key = f"order|{pid}|{est}|estimate:{est}:{L[item]}|"
        n = await C.js("k => [...document.querySelectorAll('#buy-board [data-buy]')].filter(b => b.dataset.buy === k && b.getClientRects().length).length", key)
        C.ok(n == 1, f'the Buy Board shows {item} with Order', key)
        if not n: return None
        await C.click(f'#buy-board [data-buy="{key}"]', 500)
        m = await C.modal()
        C.ok(m and m['title'].startswith('Order'), f'Order opens the order sheet for {item}', m and m['title'])
        opts = await C.js("() => [...document.querySelectorAll('#mbm [data-f=vendor] option')].map(o => [o.value, o.text])")
        val = next((o[0] for o in opts if o[1].startswith(vendor)), None)
        C.ok(val, f'{vendor} is offered as the supplier')
        await C.pg.select_option('#mbm [data-f=vendor]', val)
        await C.fill('#mbm [data-f=qty]', qty); await C.fill('#mbm [data-f=unit]', unit); await C.fill('#mbm [data-f=price]', price)
        n0 = await C.js("() => DB.pos.length")
        await C.modal_ok(800)
        po = await C.js("""([n0]) => { const o = DB.pos.slice(n0)[0]; return o && {id: o.id, number: o.number, vendor: o.vendor, status: o.status, total: poTotal(o).total,
               needBy: o.needBy, lines: o.lines.map(l => ({id: l.id, item: l.item, qty: +l.qty, price: +l.price, line: l.line}))}; }""", [n0])
        C.t(f"Buy Board > {item} > Order: supplier {vendor}, {qty} {unit} at {fmtm(float(price))} > Issue PO → {po and po['number']} {po and po['status']} ({await C.toast()})")
        return po

    mill = await order('Millwork – parlor kitchen cabinets', 'Fenwick Cabinetry', 1, 'ls', 23400)
    C.ok(mill and mill['status'] == 'pending', 'the $23,400 millwork order is over the $10,000 threshold and waits for the Owner', mill and mill['status'])
    tile = await order('Tile – primary bath', 'Arcadia Tile Supply', 140, 'sf', 47.5)
    C.ok(tile and tile['status'] == 'issued' and abs(tile['total'] - 6650) < 0.01, 'the tile order issues ($6,650, under the threshold)', tile)
    fix = await order('Fixture allowance – primary bath', 'Kingsland Bath Supply', 1, 'ls', 7450)
    C.ok(fix and fix['status'] == 'issued', 'the fixture order issues', fix)
    for po in (mill, tile, fix):
        if po:
            C.ok(all(l['line'] for l in po['lines']), f"{po['number']} lines point at their estimate line", po['lines'])
    # the sub commitment: Purchase Orders > Client Funds > Rough plumbing > New PO, ticked, priced, then submitted
    await C.as_('u_chen', 'po', f"setCurrent('{pid}'); poOpen = null;")
    await C.click(f"section.view.on [data-fundpo='estimate:{est}:{L['Rough plumbing']}']", 600)
    row = C.pg.locator('#mbm table tr').filter(has_text='3. Rough plumbing').first
    cb = row.locator('input[type=checkbox]').first
    if not await cb.is_checked(): await cb.check()
    c = row.locator('input[placeholder=cost]').first; await c.fill('13200'); await c.press('Tab')
    n0 = await C.js("() => DB.pos.length")
    await C.modal_ok(900)
    sub = await C.js("n0 => { const o = DB.pos.slice(n0)[0]; return o && {id: o.id, number: o.number, vendor: o.vendor, type: o.type, status: o.status, entityId: o.entityId, total: poTotal(o).total}; }", n0)
    C.ok(sub and sub['type'] == 'subcontract' and sub['vendor'].startswith('Halvorsen'), 'the plumbing line becomes a subcontract PO to Halvorsen', sub)
    ent = await C.js("id => entityOfProject(DB.projects.find(p => p.id === id))", pid)
    if sub and sub['entityId'] != ent:
        C.findings.append(f"The subcontract PO to an outside plumber defaults its buying entity to {sub['entityId']} (SD Plumbing, by the vendor's trade), not the job's entity {ent}; the coordinator has to change it.")
        await C.pg.select_option('section.view.on [data-p=entityId]', ent); await C.wait(300)
    r = C.pg.locator('section.view.on [data-p=retainagePct]'); await r.fill('10'); await r.dispatch_event('change'); await C.wait(300)
    await C.click('section.view.on [data-poact=submit]', 700)
    sub = await C.js("id => { const o = DB.pos.find(x => x.id === id); return {id: o.id, number: o.number, vendor: o.vendor, type: o.type, status: o.status, entityId: o.entityId, retainagePct: o.retainagePct, total: poTotal(o).total, lines: o.lines.map(l => ({id: l.id, item: l.item, qty: +l.qty, price: +l.price, line: l.line}))}; }", sub['id'])
    C.ok(sub['status'] == 'pending' and sub['retainagePct'] == 10, 'the sub commitment ($13,200, 10% retainage) waits for the Owner', sub)
    C.t(f"Purchase Orders > Client Funds > 3. Rough plumbing > New PO: ticked, cost $13,200, Halvorsen > Create the Purchase Orders → {sub['number']} draft; "
        f"entity {ent}, retainage 10% > Submit for Approval → {sub['status']}")
    # the Owner approves both from Approvals
    for po in (mill, sub):
        await C.as_('u_owner', 'mapprove', "window.mApprKind = 'all';")
        got = await C.js("""n => { const e = [...document.querySelectorAll('.m-appr')].find(x => x.getClientRects().length && x.innerText.includes(n));
            const b = e && e.querySelector('[data-myes]'); b && b.click(); return b ? b.innerText.trim() : ''; }""", po['number'])
        await C.wait(600)
        st = await C.js("n => DB.pos.find(p => p.number === n).status", po['number'])
        C.ok(got == 'Approve' and st == 'issued', f"the Owner's Approvals: {po['number']} > Approve issues it", f'{got} {st}')
        C.t(f"Owner > Approvals > {po['number']} > Approve → {st} ({await C.toast()})")
    C.rec('po', 'millwork', mill); C.rec('po', 'tile', tile); C.rec('po', 'fixtures', fix); C.rec('po', 'sub', sub)
    return True


# ================================================================ main
STEPS = [s1_client, s2_buy]


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--upto', type=int, default=99)
    a = ap.parse_args()
    async with async_playwright() as p:
        b, pg, errs = await open_app(p)
        C = Chain(pg, errs)
        try:
            for i, fn in enumerate(STEPS, 1):
                if i > a.upto: break
                go_on = await fn(C)
                if go_on is False:
                    C.ok(False, f'step {i} could not finish; the chain stops here')
                    break
        except Exception as e:
            import traceback
            C.ok(False, f'exception in {C.step_name}: {type(e).__name__}: {str(e)[:400]}', traceback.format_exc()[-1500:])
        finally:
            C.ok(not errs, 'no page errors', errs[:5])
            if C.findings:
                C.lines.append('\n## Findings noted on the way\n')
                C.lines += [f'- {f}' for f in C.findings]
            C.write()
            await b.close()
    print(f'\nCHAIN {C.n} checks · {len(C.fail)} failed')
    for f in C.fail: print('  -', f)
    sys.exit(1 if C.fail else 0)


if __name__ == '__main__':
    asyncio.run(main())
