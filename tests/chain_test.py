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


# ================================================================ 3. receive, bill, mail bills, approvals, payments
def ws_thread(tid, frm, subject, text, fname, pdf, when):
    return {'id': tid, 'messages': [{'id': tid + '-1', 'date': when, 'from': frm, 'to': ['Chen Biron <chen@smartdesign.nyc>'], 'cc': [],
            'subject': subject, 'text': text, 'labelIds': ['INBOX', 'UNREAD'],
            'attachments': [{'filename': fname, 'mimeType': 'application/pdf', 'text': pdf}]}]}


async def approvals_yes(C, uid, needle, why=None, dispute=None):
    """The person's Approvals: the card naming `needle`, its yes button; an override asks for a reason, an over-PO
    bill opens Approve PO Amount / Dispute Difference."""
    await C.as_(uid, 'mapprove', "window.mApprKind = 'all';")
    verb = await C.js("""n => { const e = [...document.querySelectorAll('.m-appr')].find(x => x.getClientRects().length && x.innerText.includes(n));
        const b = e && e.querySelector('[data-myes]'); b && b.click(); return b ? b.innerText.trim() : ''; }""", needle)
    await C.wait(600)
    m = await C.modal()
    said = ''
    if m and m['title'].startswith('Override'):
        said = f" > Override ({'; '.join(l for l in m['text'].splitlines()[1:-3] if l)}) > reason > {m['buttons'][-1]}"
        await C.fill('#mbm [data-f=why]', why or 'Checked against the order')
        await C.modal_ok(600)
    elif m and m['title'].startswith('Approve PO Amount'):
        said = f" > {m['title']} > reason > Approve and Dispute"
        await C.fill('#mbm [data-f=why]', dispute or 'Disputed with the vendor')
        await C.modal_ok(600)
    return verb, said


async def pay_bill(C, number, acct, date, amount, method, ref):
    """Bills & Payroll > the bill > Pay… > Record Payment (from the account, date, amount, method, reference)."""
    await C.as_('u_controller', 'ap')
    await C.js("n => openBill(DB.bills.find(b => b.number === n).id)", number)
    await C.wait(400)
    await C.pg.locator('#drawer.on button', has_text=re.compile(r'^Pay')).first.click(timeout=6000)
    await C.wait(400)
    m = await C.modal()
    await C.pg.select_option('#mbm [data-f=acct]', acct)
    await C.fill('#mbm [data-f=date]', date); await C.fill('#mbm [data-f=amount]', amount)
    await C.pg.select_option('#mbm [data-f=method]', method); await C.fill('#mbm [data-f=ref]', ref)
    await C.modal_ok(600)
    try: await C.js("() => { if (document.querySelector('#drawer.on')) closeEditor(); }")
    except Exception: pass
    st = await C.js("""n => { const b = DB.bills.find(b => b.number === n); const P = (DB.billPayments || DB.payments || []).filter(p => p.billId === b.id);
        return {status: b.status, paid: P.map(p => ({id: p.id, amount: p.amount, date: p.date, acct: p.acct || p.account, ref: p.ref}))}; }""", number)
    return m, st


async def s3_receive(C):
    C.step('3. Receiving, bills from the toast, bills by mail on their POs, the over-PO dispute, approvals, payments')
    pid = C.ids['project']['id']; POS = C.ids['po']
    await C.day('2026-09-10')
    # the millwork arrives whole
    await C.as_('u_chen', 'recv', f"setCurrent('{pid}');")
    await C.click(f"section.view.on [data-rall='{POS['millwork']['id']}']", 700)
    t = await C.toast()
    C.ok('received in full' in t and 'Bill It' in t, 'Everything Arrived: the millwork PO is received in full, the toast offers Bill It', t)
    C.t(f"Coordinator > Receiving > {POS['millwork']['number']} > Everything Arrived → \"{t}\"")
    await C.pg.locator('#toast .toast-open', has_text='Bill It').first.click(timeout=5000); await C.wait(600)
    m = await C.modal()
    C.ok(m and 'Bill This PO' in m['title'], 'Bill It opens Bill This PO', m and m['title'])
    await C.fill('#mbm [data-f=number]', 'FC-20417')
    await C.modal_ok(700)
    fc = await C.js("""n => { const b = DB.bills.find(b => b.number === n); return b && {id: b.id, total: billTotal(b), poId: b.poId, line: b.line, status: b.status,
        lines: b.lines.map(l => ({id: l.id || '', amount: l.amount, poLineId: l.poLineId || '', line: l.line || ''}))}; }""", 'FC-20417')
    C.ok(fc and abs(fc['total'] - 23400) < 0.01 and fc['poId'] == POS['millwork']['id'], 'Save Bill: FC-20417 $23,400 on the millwork PO', fc)
    C.ok(fc and all(l['id'] and l['poLineId'] and l['line'] for l in fc['lines']), 'every bill line carries its own id, its PO line and its estimate line', fc and fc['lines'])
    C.t(f"Bill It > Vendor Invoice # FC-20417 > Save Bill → bill `{fc and fc['id']}` {fmtm(fc and fc['total'])} ({await C.toast()})")
    # 80 of the 140 sf of tile arrive
    await C.as_('u_chen', 'recv', f"setCurrent('{pid}');")
    tl = POS['tile']['lines'][0]['id']
    await C.fill(f"section.view.on [data-rq='{POS['tile']['id']}:{tl}']", '80')
    await C.click(f"section.view.on [data-rin='{POS['tile']['id']}:{tl}']", 700)
    t = await C.toast()
    rcv = await C.js("id => { const o = DB.pos.find(x => x.id === id); return {status: o.status, received: o.lines.map(l => +l.received || 0)}; }", POS['tile']['id'])
    C.ok(rcv['received'] == [80] and rcv['status'] in ('partial', 'issued'), 'the tile PO is received in part: 80 of 140 sf', rcv)
    C.t(f"Receiving > {POS['tile']['number']} > 80 sf > Received → \"{t}\" ({rcv})")
    await C.pg.locator('#toast .toast-open', has_text='Bill It').first.click(timeout=5000); await C.wait(600)
    m = await C.modal()
    C.ok(m and 'Bill' in m['title'], 'Bill It on the partial receipt opens the bill', m and m['title'])
    await C.fill('#mbm [data-f=number]', 'AT-7731')
    await C.modal_ok(700)
    at = await C.js("n => { const b = DB.bills.find(b => b.number === n); return b && {id: b.id, total: billTotal(b), poId: b.poId}; }", 'AT-7731')
    C.ok(at and abs(at['total'] - 3800) < 0.01, 'the bill from the partial receipt is for what arrived: 80 sf × $47.50 = $3,800', at)
    C.t(f"Bill It > AT-7731 > Save Bill → bill `{at and at['id']}` {fmtm(at and at['total'])}")
    await C.day('2026-09-11')
    await C.as_('u_chen', 'recv', f"setCurrent('{pid}');")
    await C.click(f"section.view.on [data-rall='{POS['fixtures']['id']}']", 700)
    C.t(f"Receiving > {POS['fixtures']['number']} > Everything Arrived → \"{await C.toast()}\"")
    # two vendor bills by mail: the coordinator's mailbox (a Loaded Workspace of invented threads), synced
    ws = {'email': 'chen@smartdesign.nyc', 'name': 'Chen Biron', 'exportedAt': '2026-09-11T18:00:00Z',
          'mail': {'threads': [
              ws_thread('cx-hph', 'Halvorsen Plumbing & Heating <office@halvorsenph.example>',
                        f"Invoice HPH-2291 - {JOB} rough plumbing ({POS['sub']['number']})",
                        f"Hi Chen, attached is our first progress invoice for the rough plumbing at {JOB}, {POS['sub']['number']}. Thanks, Erik Halvorsen",
                        'HPH-2291.pdf', f"HALVORSEN PLUMBING & HEATING\nInvoice HPH-2291\nDate 2026-09-11\nBill to SmartDesign Group LLC\nJob {JOB}\n{POS['sub']['number']}\nRough plumbing, progress billing 50%\nAmount due $6,600.00\nDue 2026-10-11",
                        '2026-09-11T09:12:00'),
              ws_thread('cx-kbs', 'Kingsland Bath Supply <counter@kingslandbath.example>',
                        f"Invoice KBS-5531 for {POS['fixtures']['number']}, {JOB}",
                        'Invoice attached for the primary bath fixtures. Freight added. Kingsland Bath Supply',
                        'KBS-5531.pdf', f"KINGSLAND BATH SUPPLY\nInvoice KBS-5531\n{POS['fixtures']['number']}\n{JOB}\nPrimary bath fixtures $7,450.00\nFreight $240.00\nTotal due $7,690.00\nDue 2026-10-11",
                        '2026-09-11T10:20:00')]},
          'calendar': {'events': []}, 'drive': {'files': []}}
    tmp = tempfile.mkdtemp(prefix='chain_ws_')
    path = os.path.join(tmp, 'chen.workspace.json')
    with open(path, 'w') as f: json.dump(ws, f)
    await C.as_('u_chen')
    got = await attach_workspace(C.pg, 'u_chen', path)
    d = await C.js("async () => { const d = await gcDemoConnect(); return d && {mail: d.mail.length, errors: d.errors}; }")
    await C.wait(600)
    C.ok(d and not d['errors'], 'the Loaded Workspace connects and syncs', d)
    C.t(f"Loaded Workspace for Chen (2 invented threads, tests/harness attach_workspace from {tmp}) > Connect (gcDemoConnect, the Connect button's function) → {d}")
    for num, po in (('HPH-2291', POS['sub']), ('KBS-5531', POS['fixtures'])):
        row = await C.js("n => { const r = nyhRows().find(r => r.title.includes(n)); return r && {key: r.key, verb: r.verb, title: r.title, route: r.route}; }", num)
        C.ok(row and row['verb'] == 'Apply', f"Chen's Needs Your Hand: the bill {num} read from the PDF, with Apply", row)
        if not row: continue
        # Home > Needs Your Hand > Apply (the row's verb; nyhRun is what the row's button runs)
        await C.as_('u_chen', 'home')
        pressed = await C.js("""k => { const b = [...document.querySelectorAll('#v-home [data-nyh], #v-home [data-nyhrun], #v-home button')].find(x => x.getClientRects().length && ((x.dataset.nyh || x.dataset.nyhrun || '') === k));
            if (b) { b.click(); return 'Home button'; } nyhRun(k); return 'nyhRun'; }""", row['key'])
        await C.wait(600)
        b = await C.js("""n => { const b = DB.bills.find(b => b.number === n); return b && {id: b.id, total: billTotal(b), poId: b.poId, status: b.status, retainagePct: +b.retainagePct || 0,
            due: b.due || '', file: b.fileId || '', lines: b.lines.map(l => ({id: l.id || '', poLineId: l.poLineId || '', line: l.line || ''})), flags: billFlags(b)}; }""", num)
        C.ok(b and b['poId'] == po['id'], f'{num} lands on its PO {po["number"]}', b)
        C.rec('bill', num, b and b['id'])
        C.t(f"Home > Needs Your Hand > \"{row['title'][:90]}\" > Apply ({pressed}) → bill `{b and b['id']}` {fmtm(b and b['total'])} on {po['number']} ({await C.toast()})")
    hph = await C.js("n => { const b = DB.bills.find(b => b.number === n); return b && {ret: +b.retainagePct || 0, due: b.due || ''}; }", 'HPH-2291')
    C.ok(hph and hph['ret'] == 10, 'the mailed sub bill carries its subcontract\'s 10% retainage', hph)
    C.ok(hph and hph['due'] == '2026-10-11', 'the mailed bill keeps the due date printed on the invoice', hph)
    C.rec('bill', 'FC-20417', fc and fc['id']); C.rec('bill', 'AT-7731', at and at['id'])
    # the PM recommends, the Owner approves; KBS-5531 is $240 over its PO: approve the PO amount, dispute the rest
    for num in ('FC-20417', 'AT-7731', 'HPH-2291', 'KBS-5531'):
        v, said = await approvals_yes(C, 'u_alan', num)
        st = await C.js("n => DB.bills.find(b => b.number === n).status", num)
        C.ok(v == 'Recommend' and st == 'pm-approved', f'PM > Approvals > {num} > Recommend', f'{v} {st}')
    for num, why, disp in (('FC-20417', 'Bill equals the PO and the receipt', None), ('AT-7731', 'Bill equals what arrived', None),
                           ('HPH-2291', 'Progress bill on the subcontract; the rough-in is under way', None),
                           ('KBS-5531', None, 'Freight was quoted as included; Kingsland is asked to credit the $240')):
        v, said = await approvals_yes(C, 'u_owner', num, why, disp)
        st = await C.js("n => { const b = DB.bills.find(b => b.number === n); return {status: b.status, short: b.short ? {approved: b.short.approved, held: b.short.held, state: b.short.state} : null}; }", num)
        C.ok(v == 'Approve' and st['status'] == 'approved', f'Owner > Approvals > {num} > Approve{said}', st)
        C.t(f"PM > Approvals > {num} > Recommend; Owner > Approvals > {num} > Approve{said} → {st}")
    kb = await C.js("() => DB.bills.find(b => b.number === 'KBS-5531').short")
    C.ok(kb and kb['approved'] == 7450 and kb['held'] == 240, 'KBS-5531: $7,450 approved at the PO, $240 held as disputed', kb)
    return True


# ================================================================ 4. pay: bills paid, hours, payroll, the card statement
def csv(rows):
    return 'Date,Description,Amount,Reference\n' + '\n'.join(f'{d},{desc},{amt:.2f},{ref}' for d, desc, amt, ref in rows) + '\n'


async def import_statement(C, acct, name, text):
    """Banking > Import Statement: the real dialog, the file handed to its file input, then Import."""
    await C.as_('u_controller', 'bank')
    await C.click('#bf-import', 500)
    sel = C.pg.locator('#mbm select').first
    try:
        await C.pg.select_option('#bfi-acct', acct)
    except Exception:
        await C.js("a => { const s = document.querySelector('#mbm select'); if (s) { s.value = a; s.dispatchEvent(new Event('change')); } }", acct)
    await C.pg.set_input_files('#bfi-file', files=[{'name': name, 'mimeType': 'text/csv', 'buffer': text.encode()}])
    await C.pg.wait_for_function("() => { const b = document.querySelector('#mbm-ok'); return b && !b.disabled && /Import \\d/.test(b.textContent); }", timeout=10000)
    label = await C.js("() => document.querySelector('#mbm-ok').textContent.trim()")
    await C.modal_ok(900)
    m = await C.modal()
    if m and 'Reconcile' in (m['title'] or ''):
        await C.pg.keyboard.press('Escape'); await C.wait(300)
    return label, await C.js("n => (DB.bankImports || []).filter(i => i.fileName === n).map(i => ({id: i.id, added: i.added, dup: i.dup, ruled: i.ruled, confirmed: i.confirmed}))", name)


async def txn_of(C, desc, amt):
    return await C.js("([d, a]) => { const t = DB.txns.find(t => t.desc === d && Math.abs(t.amt - a) < 0.005); return t ? t.id : null; }", [desc, amt])


async def code_in_drawer(C, tid, cat, proj='', code='', memo='', vendor='', billable=None, line=None):
    """Banking: click the line's description (the transaction drawer opens), choose category, job, estimate line
    and code, write the memo, Save."""
    await C.as_('u_controller', 'bank', "try { txnFilter = 'all'; } catch (e) {} txnAcct = '';")
    desc = await C.js("id => DB.txns.find(t => t.id === id).desc", tid)
    row = C.pg.locator('#v-bank tr').filter(has_text=desc).first
    if await row.count():
        await row.locator('td.name').first.click(timeout=5000)
    else:
        await C.js("id => txnDialog(id)", tid)
    await C.pg.wait_for_selector('#e-cat', state='attached')
    await C.wait(200)
    await C.pg.select_option('#e-cat', cat)
    await C.pg.dispatch_event('#e-cat', 'change')
    if proj:
        await C.pg.select_option('#e-proj', proj); await C.pg.dispatch_event('#e-proj', 'change'); await C.wait(150)
    if line:
        await C.pg.select_option('#e-line', line); await C.pg.dispatch_event('#e-line', 'change'); await C.wait(150)
    if code:
        await C.pg.select_option('#e-code', code)
    if memo: await C.fill('#e-memo', memo)
    if vendor and not (await C.pg.input_value('#e-vendor')).strip(): await C.fill('#e-vendor', vendor)
    if billable is not None:
        if billable != await C.pg.is_checked('#e-billable'):
            await C.pg.click('#e-billable')
    await C.pg.click('#d-save', timeout=5000); await C.wait(300)
    return await C.js("id => { const t = DB.txns.find(x => x.id === id); return t && {cat: t.cat, projectId: t.projectId || '', code: t.code || '', line: t.line || '', status: t.status, billable: !!t.billable}; }", tid)


# hours on the job (Angel demolition, Alberto framing) and the office (Jeanette: overhead)
TIME = [('em1', d, '02', 'Demolition of the parlor kitchen') for d in ('2026-09-14', '2026-09-15', '2026-09-16')] + \
       [('em2', d, '03', 'Framing and blocking for the new kitchen wall') for d in ('2026-09-15', '2026-09-16', '2026-09-17', '2026-09-18')] + \
       [('em10', d, '', 'Office: purchasing and filing') for d in ('2026-09-14', '2026-09-15', '2026-09-16', '2026-09-17', '2026-09-18')]
# the Amex activity through 9/24: overhead, one purchase for the client, one line nobody coded
CARD = [('2026-09-08', 'STAPLES #0412 BROOKLYN NY', -186.40, 'CX-0908-1', 'office', 'Office supplies'),
        ('2026-09-12', 'ADOBE *CREATIVE CLOUD', -89.99, 'CX-0912-1', 'design-software', 'Design software'),
        ('2026-09-16', 'SHELL OIL 57441 BROOKLYN', -72.35, 'CX-0916-1', 'vehicle', 'Vehicle & fuel'),
        ('2026-09-18', 'THE HOME DEPOT #1207 BROOKLYN', -412.60, 'CX-0918-1', 'materials', 'bought for the client'),
        ('2026-09-21', 'SQ *BROOKLYN PRINT SHOP', -265.00, 'CX-0921-1', 'marketing', 'Marketing (coded by the controller)')]


async def s4_pay(C):
    C.step('4. Pay: bills paid, hours and payroll, the card statement coded and matched (overhead and a purchase for the client)')
    pid = C.ids['project']['id']; L = C.ids['estimate']['lines']; est = C.ids['estimate']['id']
    PAY = [('FC-20417', '2026-09-15', 23400, 'ACH', 'ACH 0915-FC'), ('AT-7731', '2026-09-22', 3800, 'ACH', 'ACH 0922-AT'),
           ('HPH-2291', '2026-09-24', 5940, 'Check', '1187'), ('KBS-5531', '2026-09-24', 7450, 'ACH', 'ACH 0924-KB')]
    for num, date, amt, meth, ref in PAY[:1]:
        await C.day(date)
        m, st = await pay_bill(C, num, 'ac1', date, amt, meth, ref)
        C.ok(m and m['title'] == 'Pay Bill' and st['status'] == 'paid', f'{num} > Pay… > Record Payment {fmtm(amt)} {meth} {ref}', st)
        C.t(f"Controller > Bills & Payroll > {num} > Pay… > Chase, {date}, {fmtm(amt)}, {meth} {ref} > Record Payment → {st['status']}")
    # Friday: the PM enters the week's hours (Time & Crew > New Time Entry) and approves them
    await C.day('2026-09-18')
    for emp, d, code, note in TIME:
        await C.as_('u_alan', 'time', f"setCurrent('{pid}');")
        await C.click('#btn-addtime', 400)
        await C.pg.select_option('#e-emp', emp); await C.fill('#e-date', d); await C.fill('#e-in', '07:00'); await C.fill('#e-out', '15:30'); await C.fill('#e-break', '30')
        await C.pg.select_option('#e-proj', pid if code else '')
        if code: await C.pg.select_option('#e-code', code)
        await C.fill('#e-notes', note)
        await C.click('#d-save', 300)
    te = await C.js("() => DB.time.filter(t => t.date >= '2026-09-14' && t.date <= '2026-09-18' && t.source === 'manual').map(t => ({id: t.id, empId: t.empId, date: t.date, projectId: t.projectId || '', code: t.code || '', status: t.status}))")
    C.ok(len(te) == len(TIME), f'Time & Crew > New Time Entry ×{len(TIME)}: the week is on file', te)
    C.t(f"PM > Time & Crew > New Time Entry ×{len(TIME)} (employee, date, 7:00–15:30, 30 min break, job or Overhead, cost code, notes) → "
        f"{sum(1 for x in te if x['projectId'])} on {JOB}, {sum(1 for x in te if not x['projectId'])} office (overhead)")
    await C.as_('u_alan', 'time', "")
    await C.click('section.view.on [data-f=pending]', 300)
    await C.click_text('section.view.on', r'^Approve All Shown$', 500)
    m = await C.modal()
    C.ok(not m, "the PM's hours (typed with job and code; office time on Overhead) approve without an override", m and (m['title'], m['text'][:300]))
    while m:
        C.t(f"Approve All Shown asks: {m['title']} \"{m['text'].splitlines()[1][:120] if len(m['text'].splitlines()) > 1 else ''}\" > {m['buttons'][-1]}")
        await C.modal_ok(500); m = await C.modal()
    st = await C.js("ids => DB.time.filter(t => ids.includes(t.id)).map(t => t.status)", [x['id'] for x in te])
    C.ok(st and all(x == 'approved' for x in st), "PM > Time > Awaiting Approval > Approve All Shown: the week's hours are approved", st)
    C.rec('time', 'ids', [x['id'] for x in te])
    for num, date, amt, meth, ref in PAY[1:]:
        await C.day(date)
        m, stp = await pay_bill(C, num, 'ac1', date, amt, meth, ref)
        C.ok(m and m['title'] == 'Pay Bill' and stp['status'] == 'paid', f'{num} > Pay… > Record Payment {fmtm(amt)} {meth} {ref}', stp)
        C.t(f"Controller > Bills & Payroll > {num} > Pay… > Chase, {date}, {fmtm(amt)}, {meth} {ref} > Record Payment → {stp['status']}")
    C.rec('payments', 'bills', PAY)
    # the card statement through 9/24: Import Statement (CSV), then code each line
    label, imp = await import_statement(C, 'ac2', 'Amex_1009_Sep2026_to0924.csv', csv([(d, desc, amt, ref) for d, desc, amt, ref, _, _ in CARD]))
    C.ok(imp and imp[0]['added'] == len(CARD), f'Banking > Import Statement (Amex CSV, {len(CARD)} lines) > {label}', imp)
    C.t(f"Controller > Banking > Import Statement > Amex 1009 > Amex_1009_Sep2026_to0924.csv > {label} → {imp}")
    ids = {}
    for d, desc, amt, ref, cat, why in CARD:
        tid = await txn_of(C, desc, amt)
        C.ok(tid, f'the card line {desc} is on Banking', tid)
        ids[desc] = tid
        auto = await C.js("id => { const t = DB.txns.find(x => x.id === id); return {cat: t.cat, status: t.status, projectId: t.projectId || ''}; }", tid)
        if cat == 'materials':
            got = await code_in_drawer(C, tid, 'materials', pid, '', 'Shelf brackets and cabinet hardware the Vargas picked at the store: bill back at cost plus 10%',
                                       'The Home Depot', billable=True, line=f"estimate:{est}:{L['Millwork – parlor kitchen cabinets']}")
            C.ok(got['projectId'] == pid and got['billable'], f'{desc}: coded to {JOB}, the millwork line, billable to the client', got)
            C.t(f"Banking > {desc} {fmtm(amt)} (rule said {auto['cat']}) > drawer: Materials, {JOB}, line Millwork, memo 'bill back at cost plus 10%', Billable > Save → {got}")
        else:
            got = await code_in_drawer(C, tid, cat, '', '', why)
            C.ok(got['cat'] == cat and not got['projectId'], f'{desc}: coded to overhead ({cat}), no job', got)
            C.t(f"Banking > {desc} {fmtm(amt)} (rule said {auto['cat']}{', uncoded' if auto['cat'] in ('uncat', '') else ''}) > drawer: {why} > Save → {got['cat']}, {got['status']}")
    C.rec('txn', 'card', ids)
    # the payroll run for 9/14 – 9/27: the controller builds it from approved time, the Owner approves it
    await C.day('2026-09-25')
    await C.as_('u_controller', 'time')
    n0 = await C.js("() => DB.payroll.length")
    await C.click('#btn-payrollfromtime', 700)
    run = await C.js("n0 => { const r = DB.payroll.slice(n0)[0]; return r && {id: r.id, period: r.period, from: r.from, to: r.to, payDate: r.payDate, status: r.status, gross: r.gross, taxes: r.taxes, total: r.total, alloc: r.alloc, entries: DB.time.filter(t => t.payrollId === r.id).length}; }", n0)
    C.ok(run and run['entries'] == len(TIME), f'Time & Crew > Build Payroll from Approved Time: one run holds the {len(TIME)} entries', run)
    C.t(f"Controller > Time & Crew > Build Payroll from Approved Time → run `{run and run['id']}` {run and run['period']} {fmtm(run and run['total'])} "
        f"(gross {fmtm(run and run['gross'])}, taxes {fmtm(run and run['taxes'])}), alloc {run and run['alloc']} ({await C.toast()})")
    v, said = await approvals_yes(C, 'u_owner', run['period'] if run else 'Payroll', 'Hours checked against the daily logs')
    m = await C.modal()
    for _ in range(4):
        if not m: break
        C.t(f"the Owner's approval asks: {m['title']} — \"{' '.join(m['text'].splitlines()[1:3])[:160]}\" > {m['buttons'][-1]}")
        if 'why' in m['fields']: await C.fill('#mbm [data-f=why]', 'Three crew days on demolition and four on framing; office time is overhead')
        await C.modal_ok(500); m = await C.modal()
    st = await C.js("id => DB.payroll.find(r => r.id === id).status", run['id'])
    C.ok(st == 'approved', f"Owner > Approvals > Payroll {run['period']} > Approve", f'{v} {said} {st}')
    al = await C.js("id => { const r = DB.payroll.find(r => r.id === id); return {alloc: r.alloc, cov: fin3Coverage(r), hours: r.allocHours}; }", run['id'])
    C.ok(al['cov'] >= 99.99 and not any(a.get('unallocated') for a in al['alloc']), 'every dollar of the run is explained by approved hours: the job and office payroll (overhead), no Unallocated Labor', al)
    C.t(f"the run's split at approval: {al['alloc']} (coverage {al['cov']}%)")
    C.t(f"Owner > Approvals > Payroll {run['period']} > {v}{said} → {st}")
    C.rec('payroll', 'run', run)
    return True


# ================================================================ main
STEPS = [s1_client, s2_buy, s3_receive, s4_pay]


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--upto', type=int, default=99)
    ap.add_argument('--dump', default='', help='development: write the DB as JSON here after the steps run')
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
            if a.dump:
                with open(a.dump, 'w') as f: f.write(await pg.evaluate("() => JSON.stringify({DB, ids: null})"))
                with open(a.dump + '.ids.json', 'w') as f: json.dump(C.ids, f, default=str)
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
