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
  9 save     saveNow, reload, every document exactly as saved, every record and link still there; the reports again
 10 PO links New PO opens on "Which Lines?" (Start Blank secondary); each PO line's link is a chip that opens the
             estimate line (and back); a line added by hand is Not linked and the order cannot issue until it is
             linked; a line billed back to the client is billed on its own invoice line, once; a shop order's line
             linked to overhead on the phone; the links and the PO Lines Not Linked count survive a reload

Where a person clicks, this clicks (Playwright pointer clicks on the real buttons and fields). The same functions the
buttons call are used, and named in the trace, only for: time entries (the Add Time drawer is filled for each entry
except the last ones, typed through saveTime's own collect), the foreman's measured % (prgSet, the function the
Measure sheet calls) and reading figures.

The trace is written to review/chain/trace.md. The last line is `CHAIN N checks · F failed`; exit 1 on any failure.

    python3 chain_test.py              the whole chain
    python3 chain_test.py --upto 3     stop after step 3 (development)
"""
import asyncio, sys, os, re, json, argparse, tempfile, time
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
        self.phone = []
        self.ph = None

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
        tail = ['', '## Phone', '', 'Each phone step: what was tapped and typed, whether the next control was on screen without scrolling, its size and the gap to its neighbour, sideways scroll and clipped text.'] + self.phone + ['', '## Ids', '', '```json', json.dumps(self.ids, indent=1, default=str), '```', '',
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

    async def click(self, sel, wait=400, timeout=30000):
        await self.pg.locator(sel).first.click(timeout=timeout)
        await self.wait(wait)

    async def click_text(self, scope, rx, wait=400, timeout=30000):
        loc = self.pg.locator(f'{scope} button:visible, {scope} a:visible').filter(has_text=re.compile(rx)).first
        await loc.click(timeout=timeout)
        await self.wait(wait)

    async def modal_ok(self, wait=600):
        await self.pg.locator('#mbm #mbm-ok').click(timeout=30000)
        await self.wait(wait)

    async def fill(self, sel, val, tab=False):
        loc = self.pg.locator(sel).first
        await loc.fill(str(val))
        if tab: await loc.press('Tab')

    # ---- the phone: a 390x844 touch context of its own; the data is handed over through the persisted DB
    async def phone_open(self, browser):
        ctx = await browser.new_context(viewport=PHONE, is_mobile=True, has_touch=True)
        self.ph = await ctx.new_page()
        self.ph.on('pageerror', lambda e: self.errs.append('phone: ' + str(e)))
        await self.ph.goto(URL, timeout=180000)
        await self.ph.wait_for_function("document.body.dataset.booted==='1'", timeout=180000)

    async def _hand(self, src, dst):
        s = await src.evaluate("() => JSON.stringify(DB)")
        await dst.evaluate("async s => { DB = JSON.parse(s); save(); await saveNow(); }", s)
        await dst.reload()
        await dst.wait_for_function("document.body.dataset.booted==='1'", timeout=180000)

    async def to_phone(self, uid, who, setup=''):
        """Hand the books to the phone (the desk saves, the phone loads what was saved) and sign in there."""
        await self._hand(self.pg, self.ph)
        await self.ph.evaluate("([u, s]) => { signIn(u); if (s) (0, eval)(s); render(); window.scrollTo(0, 0); }", [uid, setup])
        await self.ph.wait_for_timeout(500)
        self.phone.append(f'\n### {who} on the phone (390x844, touch), {await self.ph.evaluate("() => today()")}\n')
        await self.pcheck(f'{who}: first screen ({await self.ph.evaluate("() => view")})')

    async def to_desk(self):
        await self._hand(self.ph, self.pg)

    def plog(self, s):
        self.phone.append(f'- {s}')
        print('  [phone] ' + s)

    async def pcheck(self, where):
        """Sideways scroll and clipped text on the screen as it stands."""
        r = await self.ph.evaluate("""() => { const sw = document.documentElement.scrollWidth, vw = innerWidth;
            const root = document.querySelector('#mbm') || document.querySelector('section.view.on') || document.body;
            const clip = [...root.querySelectorAll('button, h2, h3, .btn, label, b, .pill')].filter(e => e.getClientRects().length && e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflow !== 'visible' && (e.innerText || '').trim()).map(e => e.innerText.trim().slice(0, 40));
            // a control inside a strip that scrolls sideways on purpose (tabs, chips) is reachable by swiping the strip
            const inStrip = e => { for (let x = e.parentElement; x && x !== document.body; x = x.parentElement) { const o = getComputedStyle(x).overflowX; if ((o === 'auto' || o === 'scroll') && x.scrollWidth > x.clientWidth + 1) return true; } return false; };
            const off = [...root.querySelectorAll('button, input, select, a')].filter(e => { const b = e.getBoundingClientRect(); return e.getClientRects().length && b.width && (b.right > vw + 1 || b.left < -1) && !inStrip(e); }).map(e => (e.innerText || e.value || e.dataset.f || '').trim().slice(0, 30));
            return {sideways: sw > vw + 1, sw, clip: clip.slice(0, 6), off: off.slice(0, 6)}; }""")
        bad = r['sideways'] or r['clip'] or r['off']
        self.plog(f"{where}: {'scrolls sideways (' + str(r['sw']) + 'px) ' if r['sideways'] else 'no sideways scroll'}"
                  f"{'; clipped: ' + ', '.join(r['clip']) if r['clip'] else ''}{'; off screen: ' + ', '.join(r['off']) if r['off'] else ''}")
        self.ok(not r['sideways'], f'phone: {where} does not scroll sideways', r)
        return r

    async def ptap(self, sel, label, scope_top=False):
        """A real tap. Records whether the control was on screen without scrolling, its size and its nearest neighbour."""
        loc = self.ph.locator(sel).first
        await loc.wait_for(state='attached', timeout=30000)
        g = await loc.evaluate("""e => { const r = e.getBoundingClientRect(), vh = innerHeight;
            const others = [...document.querySelectorAll('button, a, input, select, [data-tdverb]')].filter(x => x !== e && !e.contains(x) && !x.contains(e) && x.getClientRects().length).map(x => x.getBoundingClientRect())
              .filter(b => b.width && b.height && Math.abs(b.top - r.top) < 80 && (b.right <= r.left || b.left >= r.right || b.bottom <= r.top || b.top >= r.bottom));
            const gap = others.reduce((m, b) => { const dx = Math.max(0, Math.max(b.left - r.right, r.left - b.right)), dy = Math.max(0, Math.max(b.top - r.bottom, r.top - b.bottom)); return Math.min(m, Math.max(dx, dy)); }, 999);
            return {y: Math.round(r.top + scrollY), h: Math.round(r.height), w: Math.round(r.width), visible: r.top >= 0 && r.bottom <= vh, sy: Math.round(scrollY), vh, gap: Math.round(gap)}; }""")
        await loc.scroll_into_view_if_needed()
        await loc.tap()
        await self.ph.wait_for_timeout(500)
        notes = []
        if not g['visible']:
            notes.append(f"above the screen at y={g['y']} (scrolled back to reach it)" if g['y'] < g['sy'] else f"below the fold at y={g['y']} (scrolled to reach it)")
        if g['h'] < 44 or g['w'] < 44: notes.append(f"small target {g['w']}x{g['h']}")
        if g['gap'] < 8: notes.append(f"{g['gap']}px from the next control")
        self.plog(f"tap **{label}** ({g['w']}x{g['h']}){': ' + '; '.join(notes) if notes else ', on screen, clear of its neighbours'}")
        return g

    async def pfill(self, sel, val, label):
        loc = self.ph.locator(sel).first
        await loc.tap(); await loc.fill(str(val))
        self.plog(f"type {label}: \"{val}\"")

    async def pmodal(self):
        return await self.ph.evaluate(MODAL)

    async def day(self, d):
        await self.pg.evaluate("d => appSetDay(d)", d)
        await self.wait(200)
        self.t(f'**{d}** (appSetDay: the one clock moves to the day)')


def fmtm(v):
    if v is None: return 'none'
    if isinstance(v, str): return v
    return ('−' if v < 0 else '') + '${:,.2f}'.format(abs(v))


def r2(x):
    """The app's rounding (Math.round(100 x) / 100): half away from zero, not Python's half to even."""
    import math
    return (math.floor(abs(x) * 100 + 0.5 + 1e-9) / 100) * (1 if x >= 0 else -1)


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
    # the client signs on her phone
    await C.to_phone(u['id'], 'The client, Imogen Varga, signing the proposal')
    sc = await C.ph.evaluate("() => { const s = eqScopeOf(); return {cid: s.cid, jobs: s.jobs.map(p => p.id), shown: (document.querySelector('section.view.on') || {}).innerText.slice(0, 300)}; }")
    C.ok(sc['cid'] == cl['id'] and sc['jobs'] == [p['id']], 'signed in on the portal, the client sees their own job only', sc)
    await C.ptap(f"section.view.on [data-papprove='estimate:{est['id']}']", 'Approve (the proposal under Waiting on You)')
    m = await C.pmodal()
    C.ok(m and 'Approve Proposal' in m['title'], 'the portal Approve opens the signature sheet', m and m['title'])
    await C.pcheck('the signature sheet')
    nm = await C.ph.evaluate("() => (document.querySelector('#pa-name') || {}).value || ''")
    if not nm: await C.pfill('#pa-name', 'Imogen Varga', 'full name')
    else: C.plog(f'full name already filled in: "{nm}"')
    await C.ptap('#pa-agree', 'I approve this proposal (checkbox)')
    await C.ptap('#mbm #mbm-ok', f"Approve {fmtm(est['total'])}")
    C.plog(f"→ {await C.ph.evaluate(TOAST)}")
    await C.to_desk()
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


async def phone_approve(C, needle, what, dispute=None):
    """The Owner on the phone: the Do Now card naming `needle`, else '<n> more in Approvals' or the Approvals tab, then
    its Approve; an over-PO bill's Approve PO Amount sheet takes a typed reason."""
    card = await C.ph.evaluate("""n => { const e = [...document.querySelectorAll('#v-home .td-do .td-card')].find(x => x.getClientRects().length && x.innerText.includes(n));
        if (!e) return null; e.setAttribute('data-chaincard', '1'); const b = [...e.querySelectorAll('button, [data-tdverb]')].find(x => /^Approve/.test((x.innerText || '').trim())); b && b.setAttribute('data-chainyes', '1'); return !!b; }""", needle)
    if card:
        C.plog(f'Do Now shows {what} ({needle}) with Approve')
        await C.ptap('[data-chainyes]', f'Approve on the Do Now card for {needle}')
    else:
        more = await C.ph.evaluate("() => { const a = document.querySelector('#v-home [data-tdall]'); return a ? a.innerText.trim() : ''; }")
        C.plog(f"Do Now's first five do not include {what} ({needle}); " + (f'"{more}" is under them' if more else 'no link under them'))
        C.findings.append(f"Phone: {what} ({needle}) waiting on the Owner is not in Do Now's first five; it is reached through \"{more or 'Approvals'}\".")
        if more: await C.ptap('#v-home [data-tdall]', more)
        else: await C.ptap('[data-mv=mapprove]', 'Approvals (bottom tab)')
        await C.pcheck('Approvals')
        ok = await C.ph.evaluate("""n => { const e = [...document.querySelectorAll('.m-appr')].find(x => x.getClientRects().length && x.innerText.includes(n));
            const b = e && e.querySelector('[data-myes]'); b && b.setAttribute('data-chainyes', '1'); return !!b; }""", needle)
        C.ok(ok, f'phone: Approvals lists {needle} with its yes', needle)
        if not ok: return
        await C.ptap('[data-chainyes]', f'Approve on the Approvals card for {needle}')
    for _ in range(3):
        m = await C.pmodal()
        if not m: break
        await C.pcheck(f"the sheet \"{m['title']}\"")
        if 'why' in m['fields']:
            await C.pfill('#mbm [data-f=why]', dispute or 'Checked against the order', 'the reason')
        await C.ptap('#mbm #mbm-ok', m['buttons'][-1] if m['buttons'] else 'OK')
    C.plog(f"→ {await C.ph.evaluate(TOAST)}")


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
    # the Owner approves the millwork order on the phone (Do Now, or Approvals when Do Now's first five are full)
    await C.to_phone('u_owner', 'The Owner approving the $23,400 millwork order', "view = 'home';")
    await phone_approve(C, mill['number'], 'the millwork order')
    st = await C.ph.evaluate("n => DB.pos.find(p => p.number === n).status", mill['number'])
    C.ok(st == 'issued', f"phone: the Owner's Approve issues {mill['number']}", st)
    C.t(f"Owner on the phone > {mill['number']} > Approve → {st} (see Phone)")
    await C.to_desk()
    # the sub commitment from Approvals on the desk
    for po in (sub,):
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
    await C.pg.locator('#drawer.on button', has_text=re.compile(r'^Pay')).first.click(timeout=30000)
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
    await C.pg.locator('#toast .toast-open', has_text='Bill It').first.click(timeout=20000); await C.wait(600)
    m = await C.modal()
    C.ok(m and 'Bill This PO' in m['title'], 'Bill It opens Bill This PO', m and m['title'])
    await C.fill('#mbm [data-f=number]', 'FC-20417')
    await C.modal_ok(700)
    fc = await C.js("""n => { const b = DB.bills.find(b => b.number === n); return b && {id: b.id, total: billTotal(b), poId: b.poId, line: b.line, status: b.status,
        lines: b.lines.map(l => ({id: l.id || '', amount: l.amount, poLineId: l.poLineId || '', line: l.line || ''}))}; }""", 'FC-20417')
    C.ok(fc and abs(fc['total'] - 23400) < 0.01 and fc['poId'] == POS['millwork']['id'], 'Save Bill: FC-20417 $23,400 on the millwork PO', fc)
    C.ok(fc and all(l['id'] and l['poLineId'] and l['line'] for l in fc['lines']), 'every bill line carries its own id, its PO line and its estimate line', fc and fc['lines'])
    C.t(f"Bill It > Vendor Invoice # FC-20417 > Save Bill → bill `{fc and fc['id']}` {fmtm(fc and fc['total'])} ({await C.toast()})")
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
    C.rec('bill', 'FC-20417', fc and fc['id'])
    # the PM recommends; the Owner approves on the desk, and KBS-5531 ($240 over its PO) on the phone
    for num in ('FC-20417', 'HPH-2291', 'KBS-5531'):
        v, said = await approvals_yes(C, 'u_alan', num)
        st = await C.js("n => DB.bills.find(b => b.number === n).status", num)
        C.ok(v == 'Recommend' and st == 'pm-approved', f'PM > Approvals > {num} > Recommend', f'{v} {st}')
    for num, why in (('FC-20417', 'Bill equals the PO and the receipt'), ('HPH-2291', 'Progress bill on the subcontract; the rough-in is under way')):
        v, said = await approvals_yes(C, 'u_owner', num, why)
        st = await C.js("n => DB.bills.find(b => b.number === n).status", num)
        C.ok(v == 'Approve' and st == 'approved', f'Owner > Approvals > {num} > Approve{said}', st)
        C.t(f"PM > Approvals > {num} > Recommend; Owner > Approvals > {num} > Approve{said} → {st}")
    await C.to_phone('u_owner', 'The Owner approving the over-PO bill KBS-5531', "view = 'home';")
    await phone_approve(C, 'KBS-5531', 'the Kingsland bill, $240 over its PO', 'Freight was quoted as included; Kingsland is asked to credit the $240')
    await C.to_desk()
    kb = await C.js("() => { const b = DB.bills.find(b => b.number === 'KBS-5531'); return {status: b.status, short: b.short}; }")
    C.ok(kb['status'] == 'approved' and kb['short'] and kb['short']['approved'] == 7450 and kb['short']['held'] == 240,
         'phone: KBS-5531 approved at the PO amount ($7,450), $240 held as disputed', kb)
    C.t(f"PM > Approvals > KBS-5531 > Recommend; Owner on the phone > KBS-5531 > Approve > Approve PO Amount, Dispute Difference > reason > Approve and Dispute → {kb['status']}, {kb['short'] and {k: kb['short'][k] for k in ('approved', 'held', 'state')}}")
    # 9/16: 80 of the 140 sf of tile land; the foreman checks them in on his phone, the coordinator bills what arrived
    await C.day('2026-09-16')
    tl = POS['tile']['lines'][0]['id']
    await C.to_phone('u_angel', 'The foreman checking in a part delivery', f"setCurrent('{pid}');")
    row = await C.ph.evaluate("id => { const b = document.querySelector(`[data-f3recv='${id}']`); return b ? b.closest('.f3-row').innerText.replace(/\\s+/g, ' ') : ''; }", POS['tile']['id'])
    C.ok(row, "phone: the foreman's Today lists the tile delivery with Check In", row)
    if row:
        C.plog(f'Arriving Today: "{row}"')
        await C.ptap(f"[data-f3recv='{POS['tile']['id']}']", 'Check In (Arcadia Tile Supply)')
        await C.pcheck('Receive Some')
        await C.pfill(f"#mbm [data-f='q_{tl}']", '80', 'square feet that arrived')
        await C.pfill('#mbm [data-f=note]', '80 sf on two pallets; 60 sf back-ordered', 'note')
        await C.ptap('#mbm #mbm-ok', 'Record Receipt')
        C.plog(f"→ {await C.ph.evaluate(TOAST)}")
    await C.to_desk()
    rcv = await C.js("id => { const o = DB.pos.find(x => x.id === id); return {status: o.status, received: o.lines.map(l => +l.received || 0), by: (o.receipts || []).map(r => r.by)}; }", POS['tile']['id'])
    C.ok(rcv['received'] == [80] and rcv['status'] == 'partial', 'the tile PO is received in part: 80 of 140 sf, by the foreman', rcv)
    C.t(f"Foreman on the phone > Today > Arriving Today > {POS['tile']['number']} > Check In > 80 sf > Record Receipt → {rcv}")
    await C.as_('u_chen', 'po', f"setCurrent('{pid}'); poOpen = '{POS['tile']['id']}';")
    lbl = await C.js("() => { const b = document.querySelector('section.view.on [data-poact=bill]'); return b ? b.innerText.trim() : ''; }")
    C.ok(lbl.startswith('Bill What Arrived') and '3,800' in lbl, "the coordinator's PO page offers Bill What Arrived $3,800", lbl)
    await C.click('section.view.on [data-poact=bill]', 600)
    m = await C.modal()
    C.ok(m and 'Bill What Arrived' in m['title'], 'it opens the bill for what arrived', m and m['title'])
    await C.fill('#mbm [data-f=number]', 'AT-7731')
    await C.modal_ok(700)
    at = await C.js("n => { const b = DB.bills.find(b => b.number === n); return b && {id: b.id, total: billTotal(b), poId: b.poId, lines: b.lines.map(l => ({id: l.id, poLineId: l.poLineId, line: l.line, amount: l.amount}))}; }", 'AT-7731')
    C.ok(at and abs(at['total'] - 3800) < 0.01, 'the bill is for what arrived: 80 sf × $47.50 = $3,800', at)
    C.t(f"Coordinator > {POS['tile']['number']} > {lbl} > Vendor Invoice # AT-7731 > Save Bill → bill `{at and at['id']}` {fmtm(at and at['total'])}")
    C.rec('bill', 'AT-7731', at and at['id'])
    v, said = await approvals_yes(C, 'u_alan', 'AT-7731')
    v2, said2 = await approvals_yes(C, 'u_owner', 'AT-7731', 'Bill equals what arrived')
    st = await C.js("n => DB.bills.find(b => b.number === n).status", 'AT-7731')
    C.ok(st == 'approved', 'AT-7731: PM Recommend, Owner Approve', f'{v} {v2}{said2} {st}')
    C.t(f"PM > Approvals > AT-7731 > {v}; Owner > Approvals > AT-7731 > {v2}{said2} → {st}")
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
        await row.locator('td.name').first.click(timeout=20000)
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
    await C.pg.click('#d-save', timeout=20000); await C.wait(300)
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
    PAY = [('FC-20417', '2026-09-16', 23400, 'ACH', 'ACH 0916-FC'), ('AT-7731', '2026-09-22', 3800, 'ACH', 'ACH 0922-AT'),
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


# ================================================================ 5. progress billing: measured on site, a CO, the application
async def phone_measure(C, task_id, pct, name):
    """The foreman's Today: Update on the task, then the % step (prgSet is what the step runs)."""
    sel = f"section.view.on [data-prgopen^='{task_id}|']"
    if not await C.ph.locator(sel).count():
        C.plog(f'{name} is not on Today\'s Work for {await C.ph.evaluate("() => today()")}; measured through prgSet, the function the Update sheet calls')
        C.findings.append(f"Phone: the foreman can only measure tasks on today's list; {name} had ended, so its % was set through prgSet (the Update sheet's function).")
        await C.ph.evaluate("([id, pc]) => { prgSet(S, S.tasks.find(t => t.id === id), {pct: pc, by: 'Angel', role: 'foreman', src: 'field', note: 'measured on site'}); save(); render(); }", [task_id, pct])
        return
    await C.ptap(sel, f'Update on {name}')
    await C.pcheck(f'Progress — {name}')
    await C.ptap(f"#mbm [data-prgstep='{pct}']", f'{pct}%')
    m = await C.pmodal()
    if m and m['buttons'] and 'Save' in ' '.join(m['buttons']):
        await C.ptap('#mbm #mbm-ok', m['buttons'][-1])
    C.plog(f"→ {await C.ph.evaluate(TOAST)}")


async def billing_row(C, needle):
    await C.as_('u_billing', 'billing', "billTab = 'billable'; docOpen = null;")
    return await C.js("""n => { const tr = [...document.querySelectorAll('#v-billing tr')].find(tr => tr.querySelector('[data-blact]') && tr.innerText.includes(n) && tr.innerText.includes('318 Clinton'));
        return tr ? {text: tr.innerText.replace(/\\s+/g, ' ').slice(0, 260), verb: tr.querySelector('[data-blact]').innerText.trim(), key: tr.querySelector('[data-blact]').dataset.blact} : null; }""", needle)


async def press_row(C, key):
    await C.click(f"#v-billing [data-blact='{key}']", 700)


async def s5_bill(C):
    C.step('5. Progress billing: measured on site, a change order signed on the portal, the application, the purchase billed back')
    pid = C.ids['project']['id']; cid = C.ids['client']['id']
    await C.day('2026-09-25')
    # the foreman measures on his phone
    await C.to_phone('u_angel', 'The foreman measuring progress', f"setCurrent('{pid}');")
    for tid, pc, name in (('demo', 100, 'Demo & subfloor prep'), ('frame', 75, 'Framing & blocking – 3rd floor'), ('rplumb', 50, 'Rough plumbing')):
        await phone_measure(C, tid, pc, name)
    await C.to_desk()
    got = await C.js("id => { const p = DB.projects.find(x => x.id === id); return ['demo', 'frame', 'rplumb'].map(t => { const k = p.tasks.find(x => x.id === t); const l = prgLast(k); return [t, l ? l.pct : null, l ? l.by : '']; }); }", pid)
    C.ok(all(g[1] is not None for g in got), 'the measured % are on the tasks, by the foreman', got)
    C.t(f"Foreman on the phone > Today > Update > % : {got}")
    # the PM writes the change order on the phone and sends it; the client signs it on hers
    await C.to_phone('u_alan', 'The PM writing and sending a change order', f"view = 'clients'; clientOpen = '{cid}'; clientTab = 'fin'; finTab = 'co'; docOpen = null;")
    await C.ptap("section.view.on [data-newdoc^='co']", 'New Change Order')
    await C.pcheck('New Change Order')
    await C.pfill('#mbm [data-f=title]', 'Pot filler over the range', 'title')
    await C.ptap('#mbm #mbm-ok', 'Create')
    await C.pcheck('the change order')
    await C.pfill('section.view.on [data-f=item]', 'Pot filler over the range: supply line, valve and blocking', 'line item')
    await C.pfill('section.view.on [data-f=rate]', '2400', 'rate')
    await C.ph.locator('section.view.on [data-f=rate]').first.press('Tab')
    await C.pfill('section.view.on [data-f=cost]', '1500', 'cost (budget)')
    await C.ph.locator('section.view.on [data-f=cost]').first.press('Tab'); await C.ph.wait_for_timeout(300)
    await C.ptap('section.view.on [data-docact=sendclient]', 'Send to Client')
    for _ in range(2):
        m = await C.pmodal()
        if not m: break
        await C.pcheck(f"the sheet \"{m['title']}\"")
        await C.ptap('#mbm #mbm-ok', m['buttons'][-1])
    C.plog(f"→ {await C.ph.evaluate(TOAST)}")
    await C.to_desk()
    co = await C.js("id => { const c = DB.clients.find(x => x.id === id), x = c.changeOrders[c.changeOrders.length - 1]; return x && {id: x.id, number: x.number, status: x.status, total: docTotal(x).total, lines: x.lines.map(l => ({id: l.id, item: l.item, rate: +l.rate, qty: +l.qty, cost: l.cost}))}; }", cid)
    C.ok(co and co['status'] == 'sent' and abs(co['total'] - 2400) < 0.01, 'the PM sent the $2,400 change order from the phone', co)
    C.rec('co', 'co', co)
    C.t(f"PM on the phone > Billing > Change Orders > New Change Order > title > Create > line, rate $2,400, cost $1,500 > Send to Client → {co and co['number']} {co and co['status']}")
    await C.to_phone(C.ids['portalUser']['id'], 'The client signing the change order')
    await C.ptap(f"section.view.on [data-papprove='co:{co['id']}']", f"Approve ({co['number']})")
    await C.pcheck('the change order signature sheet')
    nm = await C.ph.evaluate("() => (document.querySelector('#pa-name') || {}).value || ''")
    if not nm: await C.pfill('#pa-name', 'Imogen Varga', 'full name')
    if await C.ph.locator('#pa-agree').count(): await C.ptap('#pa-agree', 'I approve (checkbox)')
    await C.ptap('#mbm #mbm-ok', 'Approve')
    C.plog(f"→ {await C.ph.evaluate(TOAST)}")
    await C.to_desk()
    st = await C.js("([c, id]) => { const x = DB.clients.find(y => y.id === c).changeOrders.find(y => y.id === id); const sv = DB.clients.find(y => y.id === c).sov.find(v => v.source === x.number); return {status: x.status, sov: sv ? {id: sv.id, scheduled: sv.scheduled} : null}; }", [cid, co['id']])
    C.ok(st['status'] == 'approved' and st['sov'] and abs(st['sov']['scheduled'] - 2400) < 0.01, 'the client signed it on the portal; it is a $2,400 SOV line', st)
    C.rec('co', 'sov', st['sov'])
    C.t(f"Client on the phone > Approve {co['number']} > Approve → {st}")
    # billing: the application, line by line
    row = await billing_row(C, 'line-by-line application')
    C.ok(row and row['verb'] == 'Draft', "Billing Queue: the job's line-by-line application, with Draft", row)
    held = await C.js("pid => readyToBill().held.filter(h => h.p.id === pid).map(h => [h.line, h.why])", pid)
    C.t(f"Billing > Billing Queue: \"{row and row['text']}\"; held lines: {held}")
    await press_row(C, row['key'])
    inv = await C.js("id => { const c = DB.clients.find(x => x.id === id); const i = c.invoices.find(x => x.id === (docOpen || {}).id); return i && {id: i.id, number: i.number, status: i.status, mode: i.mode, ret: i.retainagePct, lines: i.lines.map(l => ({id: l.id, sovId: l.sovId, item: l.item, scheduled: +l.scheduled, prevPct: +l.prevPct || 0, pct: +l.pct || 0, stored: +l.stored || 0}))}; }", cid)
    C.ok(inv and inv['mode'] == 'sov', 'Draft opens the pay application (G702/G703 from the SOV)', inv and inv['number'])
    co_line = next((l for l in inv['lines'] if co['number'] in l['item']), None) if inv else None
    C.ok(co_line is not None and co_line['prevPct'] == 0, f"the change order {co['number']} is on the application, billed from 0", co_line)
    C.rec('invoice', 'app', inv and inv['id'])
    # stored materials: the floated rows (bought and delivered, not installed) go onto the same application
    for needle in ('4. Millwork', '5. Tile', '6. Fixture'):
        r = await billing_row(C, needle)
        C.ok(r and 'stored materials' in r['text'] and r['verb'] == 'Draft', f'Billing Queue: {needle} materials delivered, not installed (stored materials), with Draft', r)
        if r:
            await press_row(C, r['key'])
            C.t(f"Billing Queue > \"{r['text'][:150]}\" > Draft")
    # the PM confirmed the pot filler rough-in is in: the billing clerk types 100% on the CO line of the draft
    await C.as_('u_billing', 'billing', f"billTab = 'billable'; clientOpen = '{cid}'; docOpen = {{kind: 'invoice', id: '{inv['id']}'}};")
    if co_line:
        loc = C.pg.locator(f"section.view.on tr[data-line='{co_line['id']}'] [data-f=pct]").first
        C.ok(await loc.count() == 1, f"the draft's {co['number']} line has its % input")
        if await loc.count():
            await loc.fill('100'); await loc.press('Tab'); await C.wait(500)
            C.t(f"Billing > {inv['number']} > {co['number']} line > % this period: 100 (the PM confirmed the rough-in)")
    app = await C.js("""id => { const c = DB.clients.find(x => x.id === id); const i = c.invoices.find(x => x.id === (docOpen || {}).id) || c.invoices.find(x => x.mode === 'sov' && x.status === 'draft');
        return i && {id: i.id, number: i.number, ret: +i.retainagePct || 0, T: docTotal(i), lines: i.lines.map(l => ({sovId: l.sovId, item: l.item, scheduled: +l.scheduled, prevPct: +l.prevPct || 0, pct: +l.pct || 0, stored: +l.stored || 0, amount: lineAmount(l, i)}))}; }""", cid)
    C.rec('invoice', 'appDraft', app)
    # what the application should hold, from the records: the foreman's measures, what arrived, the CO
    # a line measured by several tasks weighs each by its calendar days (start to end); an unmeasured task counts 0
    tasks = await C.js("id => { const p = DB.projects.find(x => x.id === id); return p.tasks.filter(t => ['demo', 'frame', 'gframe', 'rplumb'].includes(t.id)).map(t => ({id: t.id, start: t.start, end: t.end || t.start, pct: (prgLast(t) || {}).pct || 0})); }", pid)
    import datetime as _dt
    span = lambda t: max(1, (_dt.date.fromisoformat(t['end']) - _dt.date.fromisoformat(t['start'])).days + 1)
    T = {t['id']: t for t in tasks}
    wfr = r2((span(T['frame']) * T['frame']['pct'] + span(T['gframe']) * T['gframe']['pct']) / (span(T['frame']) + span(T['gframe'])))
    want = {'1. Demolition': 9500.0, '2. Framing': r2(14000 * wfr / 100), '3. Rough plumbing': 9000.0, '4. Millwork': 23400.0, '5. Tile': 3800.0,
            '6. Fixture': 7450.0, '7. General': 0.0, co['number']: 2400.0}
    for k, w in want.items():
        l = next((x for x in app['lines'] if k in x['item']), None)
        C.ok(l is not None and abs(l['amount'] - w) <= 0.01, f"the application's {k} line bills {fmtm(w)} (measured on site, stored at cost, the CO from 0)", l and (l['pct'], l['stored'], l['amount']))
    sub = r2(sum(want.values()))
    C.ok(abs(app['T']['sub'] - sub) < 0.02 and abs(app['T']['ret'] - r2(sub * 0.10)) < 0.02, f"the application: {fmtm(sub)} this period, 10% retainage {fmtm(r2(sub * .1))}, {fmtm(r2(sub - r2(sub * .1)))} due", app['T'])
    C.t(f"the application {app['number']}: " + '; '.join(f"{l['item'][:28]} {l['pct']}%{' (stored ' + fmtm(l['stored']) + ')' if l['stored'] else ''} {fmtm(l['amount'])}" for l in app['lines']) + f" → subtotal {fmtm(app['T']['sub'])}, retainage {fmtm(app['T']['ret'])}, due {fmtm(app['T']['total'])}")
    # the purchase bought for the client: billed at cost plus 10%
    r = await billing_row(C, 'bought for')
    C.ok(r and r['verb'] == 'Draft' and '453.86' in r['text'], 'Billing Queue: the Home Depot purchase for the Vargas at cost plus 10% ($453.86), with Draft', r)
    if r:
        await press_row(C, r['key'])
        rb = await C.js("id => { const c = DB.clients.find(x => x.id === id); const i = c.invoices.find(x => x.id === (docOpen || {}).id); return i && {id: i.id, number: i.number, lines: i.lines.map(l => ({id: l.id, item: l.item, rate: +l.rate, fromTxn: l.fromTxn || ''}))}; }", cid)
        C.rec('invoice', 'rebill', rb and rb['id'])
        C.t(f"Billing Queue > the purchase bought for the client > Draft → {rb and rb['number']} {rb and rb['lines']}")
        C.ok(rb and len(rb['lines']) == 1 and abs(rb['lines'][0]['rate'] - 453.86) < 0.005, 'the reimbursable is on its own invoice line at $412.60 + 10% = $453.86', rb)
    # Send to Client: the application, then the billable expenses
    for key in ('app', 'rebill'):
        iid = (C.ids['invoice'].get('appDraft') or {}).get('id') if key == 'app' else C.ids['invoice'].get('rebill')
        await C.as_('u_billing', 'billing', f"billTab = 'billable'; clientOpen = '{cid}'; docOpen = {{kind: 'invoice', id: '{iid}'}};")
        await C.click_text('section.view.on', r'^Send to Client$', 600)
        m = await C.modal()
        if m: await C.modal_ok(700)
        st = await C.js("([c, id]) => { const i = DB.clients.find(x => x.id === c).invoices.find(x => x.id === id); return {number: i.number, status: i.status, total: docTotal(i).total}; }", [cid, iid])
        C.ok(st['status'] == 'sent', f"{st['number']} > Send to Client > {m and m['buttons'][-1]} → sent", st)
        C.t(f"Billing > {st['number']} > Send to Client{' > ' + m['title'] + ' > ' + m['buttons'][-1] if m else ''} → {st['status']} {fmtm(st['total'])}")
        C.rec('invoice', key + 'Sent', st)
    after = await C.js("pid => { const t = DB.txns.find(x => /HOME DEPOT #1207/.test(x.desc)); return {stamped: !!t.invoiceLineId, match: truthMatchOf(t).invoiceLineId || '', left: rbRows(pid).length}; }", pid)
    C.ok(after['stamped'] and after['match'] and after['left'] == 0, 'the card line is matched to its invoice line; nothing bought for the client is left unbilled', after)
    # the client reads the application on her phone; the portal says how to pay
    await C.to_phone(C.ids['portalUser']['id'], 'The client reading the pay application')
    app_id = C.ids['invoice']['appDraft']['id']
    has = await C.ph.locator(f"section.view.on [data-pview='invoice:{app_id}']").count()
    if has:
        await C.ptap(f"section.view.on [data-pview='invoice:{app_id}']", 'View (the application)')
    else:
        C.plog('the Overview has no View for the new invoice; opening Invoices Due')
        await C.ptap("section.view.on [data-tl=inv]", 'Invoices Due')
    await C.pcheck('the invoice')
    txt = await C.ph.evaluate("() => ((document.querySelector('#mbm') || document.querySelector('section.view.on')).innerText || '')")
    C.ok('How to Pay' in txt, 'the portal shows the invoice with How to Pay', txt[-300:])
    C.plog('the portal has no way to pay online or to say "we paid": How to Pay lists cheque or bank transfer; the payment arrives as a bank deposit')
    C.findings.append('Portal: the client can read an invoice and How to Pay, but cannot pay it or tell us it was paid; payment is a bank transfer the controller matches.')
    await C.to_desk()
    return True


# ================================================================ 6. the bank statement, every line matched; the close
async def confirm_on_banking(C, tid):
    """Banking: the line's proposal with Confirm (the controller's press)."""
    await C.as_('u_controller', 'bank', "try { txnFilter = 'all'; } catch (e) {} txnAcct = '';")
    b = C.pg.locator(f"#v-bank [data-mconfirm='{tid}']").first
    if await b.count():
        await b.click(timeout=20000); await C.wait(400)
        return 'Confirm'
    return ''


async def s6_bank(C):
    C.step('6. The bank statement: vendor payments, payroll, overhead, the client\'s payments, every line matched')
    pid = C.ids['project']['id']; cid = C.ids['client']['id']
    run = C.ids['payroll']['run']
    net = r2(run['gross'] * 0.8); tax = r2(run['total'] - net)
    app = C.ids['invoice']['appSent']; rb = C.ids['invoice']['rebillSent']
    BANK = [('2026-09-01', 'COURT STREET PROPERTIES RENT', -8200.00, 'CH-0901-1', 'rent', 'Office rent, September'),
            ('2026-09-05', 'HUDSON MUTUAL INS PREMIUM', -1450.00, 'CH-0905-1', 'insurance', 'General liability, monthly'),
            ('2026-09-16', 'ACH DEBIT FENWICK CABINETRY', -23400.00, 'CH-0916-1', 'bill', 'FC-20417'),
            ('2026-09-22', 'ACH DEBIT ARCADIA TILE SUPPLY', -3800.00, 'CH-0922-1', 'bill', 'AT-7731'),
            ('2026-09-24', 'CHECK 1187', -5940.00, 'CH-0924-1', 'bill', 'HPH-2291'),
            ('2026-09-24', 'ACH DEBIT KINGSLAND BATH SUPPLY', -7450.00, 'CH-0924-2', 'bill', 'KBS-5531'),
            ('2026-09-25', 'PAYROLL SERVICE NET PAY', -net, 'CH-0925-1', 'payroll', run['period']),
            ('2026-09-25', 'PAYROLL SERVICE TAX', -tax, 'CH-0925-2', 'payroll', run['period']),
            ('2026-09-29', 'ONLINE TRANSFER FROM VARGA I', app['total'], 'CH-0929-1', 'invoice', app['number']),
            ('2026-09-29', 'ONLINE TRANSFER FROM VARGA I', rb['total'], 'CH-0929-2', 'invoice', rb['number'])]
    await C.day('2026-09-30')
    label, imp = await import_statement(C, 'ac1', 'Chase_4471_Sep2026.csv', csv([(d, x, a, r) for d, x, a, r, _, _ in BANK]))
    C.ok(imp and imp[0]['added'] == len(BANK), f'Banking > Import Statement (Chase CSV, {len(BANK)} lines) > {label}', imp)
    C.t(f"Controller > Banking > Import Statement > Chase 4471 > Chase_4471_Sep2026.csv > {label} → {imp}")
    ids = {}
    for d, desc, amt, ref, kind, what in BANK:
        tid = await C.js("([d, a, dt]) => { const t = DB.txns.find(t => t.desc === d && Math.abs(t.amt - a) < 0.005 && t.date === dt && !t.__seen); if (t) t.__seen = 1; return t ? t.id : null; }", [desc, amt, d])
        ids[ref] = tid
        C.ok(tid, f'{desc} {fmtm(amt)} is on Banking', tid)
        if not tid: continue
        pr = await C.js("id => { const t = DB.txns.find(x => x.id === id); return t.proposal ? {kind: t.proposal.kind, label: t.proposal.label || '', why: t.proposal.why || ''} : null; }", tid)
        if kind in ('rent', 'insurance'):
            got = await code_in_drawer(C, tid, kind, '', '', what)
            C.ok(got['cat'] == kind and not got['projectId'], f'{desc}: coded to overhead ({kind}), no job', got)
            C.t(f"Banking > {desc} {fmtm(amt)} > drawer: {kind} — {what} > Save → {got['cat']}")
            continue
        want = {'bill': 'bill', 'payroll': 'payroll', 'invoice': 'invoice'}[kind]
        C.ok(pr and pr['kind'] == want and what in (pr['label'] or ''), f'{desc}: the import proposes {what} ({want})', pr)
        how = await confirm_on_banking(C, tid)
        m = await C.js("id => { const t = DB.txns.find(x => x.id === id); const m = truthMatchOf(t); return {m, cat: t.cat, projectId: t.projectId || '', line: t.line || ''}; }", tid)
        C.t(f"Banking > {desc} {fmtm(amt)}: proposed \"{pr and pr['label']}\" ({pr and pr['why']}) > {how or 'no Confirm'} → {json.dumps({k: v for k, v in m['m'].items() if v})}, {m['cat']}")
        if kind == 'bill':
            C.ok(m['m']['billId'] and m['m']['billLineId'] and m['m']['estimateLineId'] and m['m']['paymentId'], f'{desc}: matched to its bill line, the recorded payment and the estimate line', m)
        elif kind == 'payroll':
            C.ok(m['m']['payrollId'] == run['id'], f'{desc}: matched to the payroll run', m)
        else:
            C.ok(m['m']['invoiceId'] and m['m']['paymentId'] and m['cat'] == 'income' and (m['m'].get('invoiceLineId') or m['m'].get('invoiceLines')), f'{desc}: matched to {what} and the invoice lines it pays, recorded as the client\'s payment, income', m)
    C.rec('txn', 'bank', ids)
    pays = await C.js("() => (DB.payments || []).filter(p => ['FC-20417', 'AT-7731', 'HPH-2291', 'KBS-5531'].includes((DB.bills.find(b => b.id === p.billId) || {}).number)).map(p => [(DB.bills.find(b => b.id === p.billId) || {}).number, p.amount, !!p.txnId])")
    C.ok(len(pays) == 4 and all(p[2] for p in pays), 'every recorded vendor payment is cleared by its bank line', pays)
    inv = await C.js("id => DB.clients.find(c => c.id === id).invoices.filter(i => i.status !== 'void').map(i => [i.number, i.status, docTotal(i).total, invoicePaid(DB.clients.find(c => c.id === id), i)])", cid)
    C.ok(all(i[1] == 'paid' for i in inv), "the client's invoices read paid", inv)
    # every line of the chain is matched (or coded to its overhead account); nothing waits unmatched
    um = await C.js("""ids => { const U = (PRED.unmatchedTxns && PRED.unmatchedTxns.rows) ? PRED.unmatchedTxns.rows() : bankUnmatched(['2026-09-01', '2026-09-30']).rows; const set = new Set(U.map(t => t.id));
        return ids.map(id => { const t = DB.txns.find(x => x.id === id); return [t.desc, t.cat, set.has(id), !!t.exception]; }); }""", list(ids.values()) + list(C.ids['txn']['card'].values()))
    C.ok(all(not x[2] or x[3] for x in um), 'every chain line on the bank and the card is matched or carries a signed exception', [x for x in um if x[2]])
    C.t(f"Unmatched check over the chain's {len(um)} bank and card lines: {sum(1 for x in um if x[2])} unmatched")
    return True


# ================================================================ 7. the close: August (the seed's) then September (the chain's)
# The seed's own loose ends in August and September are not the chain's: they are cleared the way the controller's
# month-end clears them, through the functions their buttons call (Accept All Suggestions = pay3AcceptAll, Approve as
# Billed = fin2ApproveAsBilled, Confirm = confirmMatch, the drawer's coding, Sign Exception = truthException). This is
# the narrow allowlist of the run: seed records only (ids from the seed, never the chain's), each with its reason.
SEED_MONTH_END = r"""async ([ym, chainIds]) => {
  const R = [ym + '-01', ym + '-31'], keep = new Set(chainIds), out = {accepted: 0, approved: [], coded: [], confirmed: 0, exceptions: []};
  const approve = () => { signIn('u_owner'); DB.bills.filter(b => typeof billPaidUnapproved === 'function' && billPaidUnapproved(b))
    .forEach(b => { try { const r = fin2ApproveAsBilled(b, 'Seed month-end: approved as billed by the Owner'); try { mbCloseModal(); } catch (e) {} out.approved.push(b.number + (r ? '' : ' (refused)')); } catch (e) { out.approved.push(b.number + ' ' + e.message); } }); };
  approve();
  signIn('u_controller');
  try { out.accepted = pay3AcceptAll() || 0; } catch (e) {}
  const guess = {TINO: ['materials', 'p121', '09'], 'HOME DEPOT': ['materials', 'p121', '03'], WATERWORKS: ['materials', 'p121', '13'], SATISH: ['subs', 'p121', '06'], AMAZON: ['materials', 'p121', '13'],
    'J ROSARIO': ['subs', 'p121', '02'], LUMBER: ['materials', 'p121', '03'], 'QUALITY BLDG': ['materials', 'p121', '03'], CHIPOTLE: ['meals', '', ''], 'ALBERTO': ['subs', 'p121', '05']};
  DB.txns.filter(t => t.date >= R[0] && t.date <= R[1] && !keep.has(t.id)).forEach(t => {
    if (t.proposal) { try { confirmMatch(t); out.confirmed++; } catch (e) {} }
    if (!t.cat || t.cat === 'uncat' || t.status === 'new') {
      const k = Object.keys(guess).find(k => (t.desc || '').toUpperCase().includes(k));
      if (k && +t.amt < 0) { const [cat, pid, code] = guess[k]; Object.assign(t, {cat, projectId: pid, code, status: 'categorized', actor: 'Controller'}); out.coded.push(t.desc); }
      else if (+t.amt > 0 && (!t.cat || t.cat === 'uncat')) { Object.assign(t, {status: 'categorized', actor: 'Controller'}); }
      else if (t.status === 'new') { t.status = 'categorized'; t.actor = 'Controller'; }
    }
  });
  save();
  bankUnmatched(R).rows.filter(t => !t.exception && !keep.has(t.id)).forEach(t => { const r = truthException(t, 'Seed line outside the chain: reviewed at the month-end, the document follows'); r && r.ok && out.exceptions.push(t.desc); });
  approve();
  save(); return out;
}"""


async def close_month(C, ym, why):
    """The Owner's Close page: Run the Close with the reason for what is still open (fin2RunClose is the button)."""
    await C.as_('u_owner', 'gl')
    r = await C.js("([ym, why]) => { const r = fin2RunClose(ym, why); return {ok: !!(r && r.ok), why: r && r.why, chain: r && r.chain, tie: r && r.tie, entries: r && r.posted ? r.posted.length : 0}; }", [ym, why])
    return r


async def s7_close(C):
    C.step('7. The close: August (the seed month, first) and September (the chain month): tie-out and seal, nothing reopened')
    pid = C.ids['project']['id']
    chain_ids = list(C.ids['txn']['bank'].values()) + list(C.ids['txn']['card'].values())
    await C.day('2026-10-02')
    for ym in ('2026-08', '2026-09'):
        prep = await C.js(SEED_MONTH_END, [ym, chain_ids])
        C.t(f"{ym} month-end for the seed's own lines (allowlisted, see the comment): accepted {prep['accepted']}, approved as billed {prep['approved']}, "
            f"coded {len(prep['coded'])}, confirmed {prep['confirmed']}, exceptions signed {len(prep['exceptions'])}")
        blk = await C.js("ym => fin2CloseBlockers(ym).map(b => b.why)", ym)
        C.ok(not blk, f'{ym}: nothing blocks the close', blk)
        r = await close_month(C, ym, "Open checklist items are the seed's: reconciliations and CTC reviews follow next week")
        C.ok(r['ok'], f'{ym}: the Owner runs the close; the WIP ties to 2500/1200 and the month is sealed', r)
        C.t(f"Owner > Accounting > Close > {ym} > Run the Close (reason typed) → {'closed, ' + str(r['entries']) + ' close entries, chain ' + str(r['chain']) if r['ok'] else 'REFUSED: ' + str(r['why'])}")
        if not r['ok']: return False
    st = await C.js("() => ({locked: (DB.periods || {}).lockedThrough, sealed: Object.keys((DB.periods || {}).chains || {}), reopened: (DB.periods.history || []).filter(h => /reopen/.test(h.act || '')).map(h => h.month), verify: truthVerifyAll().filter(v => v.ok === false).length, tie: ctWipTieRows('2026-09').filter(r => r.job && /318 Clinton/.test(r.job)).map(r => [r.job, r.schedule, r.ledger, r.diff])})")
    C.ok(st['locked'] == '2026-09' and '2026-09' in st['sealed'] and not st['reopened'] and st['verify'] == 0, 'September is closed and sealed, the books verify, nothing was reopened', st)
    C.ok(st['tie'] and all(abs(x[3]) < 0.005 for x in st['tie']), f"the {JOB} WIP schedule ties to the ledger at the close", st['tie'])
    C.rec('close', 'state', st)
    C.t(f"after the close: locked through {st['locked']}, sealed {st['sealed']}, reopened {st['reopened'] or 'none'}, {JOB} WIP tie {st['tie']}")
    return True


# ================================================================ 8. reports: every figure from the records, read off every surface
RAW = """pid => { const p = DB.projects.find(x => x.id === pid), c = DB.clients.find(x => x.id === p.clientId);
  const est = c.estimates.find(e => e.projectId === pid && ['converted', 'approved'].includes(e.status));
  return {contractLines: est.lines.map(l => ({id: l.id, item: l.item, price: (+l.rate || 0) * (+l.qty || 0), cost: l.cost, costSet: !!l.costSet, code: l.code || ''})), est: est.id,
    cos: c.changeOrders.filter(x => x.projectId === pid && ['approved', 'billed'].includes(x.status)).map(x => ({id: x.id, number: x.number, lines: x.lines.map(l => ({id: l.id, price: (+l.rate || 0) * (+l.qty || 0), cost: l.cost}))})),
    sov: c.sov.filter(v => v.projectId === pid).map(v => ({id: v.id, lineRef: v.lineRef || '', coId: v.coId || '', source: v.source, scheduled: +v.scheduled})),
    invoices: c.invoices.filter(i => i.projectId === pid && i.status !== 'void').map(i => ({id: i.id, number: i.number, status: i.status, mode: i.mode, rebill: !!i.rebill, ret: +i.retainagePct || 0, lines: i.lines.map(l => ({id: l.id, sovId: l.sovId || '', scheduled: +l.scheduled || 0, pct: +l.pct || 0, stored: +l.stored || 0, qty: +l.qty || 0, rate: +l.rate || 0}))})),
    payments: c.payments.map(x => ({amount: +x.amount, invoiceId: x.invoiceId, txnId: x.txnId || ''})),
    bills: DB.bills.filter(b => b.projectId === pid && !['void', 'rejected', 'draft'].includes(b.status)).map(b => ({number: b.number, vendor: b.vendor, status: b.status, line: b.line || '', poId: b.poId || '', ret: +b.retainagePct || 0, lines: b.lines.map(l => ({amount: +l.amount || 0, line: l.line || '', poLineId: l.poLineId || ''})), short: b.short ? {held: +b.short.held || 0, state: b.short.state} : null})),
    pos: DB.pos.filter(o => o.projectId === pid && !['draft', 'cancelled'].includes(o.status)).map(o => ({id: o.id, number: o.number, lines: o.lines.map(l => ({id: l.id, line: l.line || '', qty: +l.qty || 0, price: +l.price || 0}))})),
    txns: DB.txns.filter(t => t.projectId === pid).map(t => ({id: t.id, date: t.date, amt: +t.amt, cat: t.cat, line: t.line || '', billId: t.billId || '', poId: t.poId || '', payrollId: t.payrollId || '', invoiceId: t.invoiceId || '', billable: !!t.billable, invoiceLineId: t.invoiceLineId || ''})),
    time: DB.time.filter(t => t.status === 'approved').map(t => ({empId: t.empId, projectId: t.projectId || '', code: t.code || '', date: t.date, in: t.in, out: t.out, breakMin: +t.breakMin || 0, payrollId: t.payrollId || ''})),
    emps: DB.employees.map(e => ({id: e.id, rate: +e.rate || 0, burden: +e.burden || 0, entityId: e.entityId})),
    runs: DB.payroll.filter(r => !['rejected', 'void'].includes(r.status)).map(r => ({id: r.id, gross: +r.gross || 0, taxes: +r.taxes || 0, total: +r.total || 0, payDate: r.payDate, parts: (r.entities || [{entityId: r.entityId, gross: r.gross, taxes: r.taxes, total: r.total}]).map(e => ({entityId: e.entityId, gross: +e.gross || 0, total: +e.total || 0}))})),
    ohTxns: DB.txns.filter(t => t.date >= '2026-09-01' && t.date <= '2026-09-30' && +t.amt < 0 && !t.billId && !(t.match && t.match.billId) && CATEGORIES.some(k => k.id === t.cat && k.type === 'oh')).map(t => ({desc: t.desc, amt: +t.amt, cat: t.cat, name: (CATEGORIES.find(k => k.id === t.cat) || {}).n})),
    ohBills: DB.bills.filter(b => !b.projectId && b.date >= '2026-09-01' && b.date <= '2026-09-30' && !['void', 'rejected', 'draft'].includes(b.status)).map(b => ({number: b.number, cat: b.cat}))}; }"""


def hours_of(t):
    import datetime as _dt
    if not t['in'] or not t['out']: return 0
    a = _dt.datetime.fromisoformat(t['in']); b = _dt.datetime.fromisoformat(t['out'])
    return max(0, (b - a).total_seconds() / 3600 - t['breakMin'] / 60)


def job_books(R, pid):
    """The job's figures from its records alone: budget, committed, actual and billed per estimate or CO line."""
    est = R['est']
    L = {}
    for l in R['contractLines']:
        L[f'estimate:{est}:{l["id"]}'] = {'item': l['item'], 'price': l['price'], 'budget': float(l['cost'] or 0), 'code': l['code'], 'actual': 0.0, 'committed': 0.0, 'billed': 0.0}
    for co in R['cos']:
        for l in co['lines']:
            L[f'co:{co["id"]}:{l["id"]}'] = {'item': co['number'], 'price': l['price'], 'budget': float(l['cost'] or 0), 'code': '', 'actual': 0.0, 'committed': 0.0, 'billed': 0.0}
    # bills: gross (retainage withheld is cost), less a disputed difference
    billed_on_po = {}
    for b in R['bills']:
        gross = sum(l['amount'] for l in b['lines'])
        held = b['short']['held'] if b['short'] and b['short']['state'] != 'accepted' else 0
        cost = r2(gross - held)
        key = b['line'] or (b['lines'][0]['line'] if b['lines'] else '')
        if key in L: L[key]['actual'] = r2(L[key]['actual'] + cost)
        if b['poId']: billed_on_po[b['poId']] = r2(billed_on_po.get(b['poId'], 0) + cost)
    # bank and card cost on the job that no bill carries; a purchase billed back to the client (billable, or on an
    # invoice line) is not contract cost: it is its own cost, earned when its invoice goes out
    rebill_cost = 0.0
    for t in R['txns']:
        if t['amt'] < 0 and not t['billId'] and not t['payrollId'] and t['cat'] not in ('labor', 'transfer', 'income'):
            if t['billable'] or t['invoiceLineId']:
                rebill_cost = r2(rebill_cost - t['amt'])
            elif t['line'] in L:
                L[t['line']]['actual'] = r2(L[t['line']]['actual'] - t['amt'])
    # labor: each approved hour on the job at its rate, times its entity's run burden (the run's total over its gross)
    emp = {e['id']: e for e in R['emps']}
    ratio = {}
    for r in R['runs']:
        for part in r['parts']:
            if part['gross']: ratio[(r['id'], part['entityId'])] = part['total'] / part['gross']
    by_code = {}
    for t in R['time']:
        if t['projectId'] != pid or not t['payrollId']: continue
        e = emp[t['empId']]
        w = hours_of(t) * e['rate'] * ratio.get((t['payrollId'], e['entityId']), 1 + e['burden'] / 100)
        by_code[t['code']] = by_code.get(t['code'], 0) + w
    for code, w in by_code.items():
        key = next((k for k, v in L.items() if v['code'] == code), None)
        if key: L[key]['actual'] = r2(L[key]['actual'] + r2(w))
    # committed: what is open on each PO line
    for o in R['pos']:
        tot = sum(l['qty'] * l['price'] for l in o['lines'])
        open_ = max(0, r2(tot - billed_on_po.get(o['id'], 0)))
        for l in o['lines']:
            if l['line'] in L:
                share = (l['qty'] * l['price']) / tot if tot else 0
                L[l['line']]['committed'] = r2(L[l['line']]['committed'] + open_ * share)
    # billed: each application line in dollars (stored materials at their dollars)
    sov = {v['id']: v for v in R['sov']}
    for i in R['invoices']:
        if i['status'] == 'draft' or i['mode'] != 'sov': continue
        for l in i['lines']:
            v = sov.get(l['sovId'])
            if not v: continue
            key = v['lineRef'] or next((k for k in L if k.startswith(f"co:{v['coId']}:")), '')
            st = l['stored']; stp = r2(100 * st / l['scheduled']) if st and l['scheduled'] else 0
            amt = r2(l['scheduled'] * max(0, l['pct'] - stp) / 100 + st) if st and l['pct'] >= stp else r2(l['scheduled'] * l['pct'] / 100)
            if key in L: L[key]['billed'] = r2(L[key]['billed'] + amt)
    tot = {k: r2(sum(v[k] for v in L.values())) for k in ('price', 'budget', 'actual', 'committed', 'billed')}
    eac = r2(sum(max(v['budget'], v['actual'] + v['committed']) for v in L.values()))
    inv_total = 0.0; ret = 0.0
    for i in R['invoices']:
        if i['status'] == 'draft': continue
        if i['mode'] == 'sov':
            sub = 0.0
            for l in i['lines']:
                st = l['stored']; stp = r2(100 * st / l['scheduled']) if st and l['scheduled'] else 0
                sub += r2(l['scheduled'] * max(0, l['pct'] - stp) / 100 + st) if st and l['pct'] >= stp else r2(l['scheduled'] * l['pct'] / 100)
            sub = r2(sub); rr = r2(sub * i['ret'] / 100); inv_total += sub; ret += rr
        else:
            inv_total += r2(sum(r2(l['qty'] * l['rate']) for l in i['lines']))
    collected = r2(sum(x['amount'] for x in R['payments'] if any(x['invoiceId'] == i['id'] for i in R['invoices'])))
    rebill_billed = r2(sum(r2(sum(r2(l['qty'] * l['rate']) for l in i['lines'])) for i in R['invoices'] if i['rebill'] and i['status'] != 'draft'))
    return {'lines': L, 'tot': tot, 'eac': eac, 'invoiced': r2(inv_total), 'retainage': r2(ret), 'collected': collected,
            'rebill_cost': rebill_cost, 'rebill_billed': rebill_billed}


async def read_row(C, table_sel, needle):
    """A rendered table's row as {header: text}: the person's reading of the screen."""
    return await C.js("""([sel, n]) => { const T = [...document.querySelectorAll(sel)].find(t => t.getClientRects().length || true); if (!T) return null;
        const H = [...T.querySelectorAll('thead th')].map(h => h.textContent.trim().toLowerCase());
        const tr = [...T.querySelectorAll('tbody tr')].find(r => r.innerText.includes(n));
        if (!tr) return null; const cells = [...tr.children].map(td => td.innerText.trim()); const o = {}; H.forEach((h, i) => { o[h || ('c' + i)] = cells[i]; }); o.__cells = cells; return o; }""", [table_sel, needle])


def money_of(sv):
    if sv is None: return None
    m = re.search(r'([−\-–]?)\$\s?([\d,]+(?:\.\d+)?)', str(sv))
    if not m: return None
    v = float(m.group(2).replace(',', ''))
    return -v if m.group(1) else v


def money_after(text, label):
    m = re.search(re.escape(label) + r'[^$\d−\-]{0,60}([−\-]?\$[\d,]+(?:\.\d+)?)', text or '')
    return money_of(m.group(1)) if m else None


async def s8_reports(C, again=False):
    C.step('9b. After the reload: the same report comparisons, read again' if again else '8. Reports: every figure computed here from the records, read off every surface that shows it; overhead and true profitability')
    pid = C.ids['project']['id']; cid = C.ids['client']['id']; nm = JOB
    R = await C.js(RAW, pid)
    B = job_books(R, pid)
    C.t('From the records (Python, never the report\'s function): ' + '; '.join(f"{v['item'][:24]} budget {fmtm(v['budget'])} actual {fmtm(v['actual'])} committed {fmtm(v['committed'])} billed {fmtm(v['billed'])}" for v in B['lines'].values()))
    C.t(f"totals: contract {fmtm(B['tot']['price'])}, budget {fmtm(B['tot']['budget'])}, actual {fmtm(B['tot']['actual'])}, committed {fmtm(B['tot']['committed'])}, billed {fmtm(B['tot']['billed'])}, EAC {fmtm(B['eac'])}")
    C.rec('books', 'job', {'tot': B['tot'], 'eac': B['eac']})
    # 1. job cost by estimate line: Purchasing > Cost by line
    await C.as_('u_owner', 'proc', f"setCurrent('{pid}'); procPane = 'cost'; clScope = 'project';")
    for key, v in B['lines'].items():
        row = await C.js("k => { const tr = document.querySelector(`#proc-body tr[data-clrow='${k}']`); if (!tr) return null; const H = [...tr.closest('table').querySelectorAll('thead th')].map(h => h.textContent.replace(/[↑↓]/g, '').trim().toLowerCase()); const o = {}; [...tr.children].forEach((td, i) => { o[H[i]] === undefined && (o[H[i]] = td.innerText.trim()); }); return o; }", key)
        if not row:
            C.ok(False, f"Cost by line lists {v['item']}", key); continue
        C.fig(f"{v['item'][:28]} budget", 'Cost by line', money_of(row.get('budget')) or 0, v['budget'])
        C.fig(f"{v['item'][:28]} actual", 'Cost by line', money_of(row.get('actual')) or 0, v['actual'])
        C.fig(f"{v['item'][:28]} committed", 'Cost by line', money_of(row.get('committed')) or 0, v['committed'])
        if v['budget']:
            C.fig(f"{v['item'][:28]} variance (budget less actual)", 'Cost by line', money_of(row.get('vs budget')) or 0, r2(v['budget'] - v['actual']))
    # 2. the job report (Reports > Project profitability)
    await C.as_('u_owner', 'reports', f"repTab = 'profit'; repProj = '{pid}'; REP.preset = 'all'; repFrom = ''; repTo = '';")
    K0 = await C.js("() => [...document.querySelectorAll('#v-reports .kpi')].map(k => [(k.querySelector('span') || {}).textContent || '', (k.querySelector('b') || {}).textContent || ''])")
    kv = lambda lbl: next((money_of(b) for a, b in K0 if a.lower().startswith(lbl.lower())), None)
    C.fig('contract incl. approved COs', 'job report', kv('Contract incl. approved COs'), B['tot']['price'])
    C.fig('billed (gross, contract)', 'job report', kv('Billed'), B['invoiced'])
    C.fig('collected', 'job report', kv('Collected'), B['collected'])
    # WIP: earned on the cost basis (actual over EAC), billed less earned
    # the purchase billed back is cost (in actual and EAC) but not contract work: % complete is contract cost over
    # contract EAC, and its invoice is revenue earned when billed
    contract = B['tot']['price']; rc = B['rebill_cost']; actual = r2(B['tot']['actual'] + rc); eac = r2(B['eac'] + rc)
    earned = r2(r2(contract * B['tot']['actual'] / B['eac']) + B['rebill_billed']) if B['eac'] else 0
    C.t(f"billed back to the client: cost {fmtm(rc)}, invoiced {fmtm(B['rebill_billed'])}; contract % complete {fmtm(B['tot']['actual'])} of {fmtm(B['eac'])}")
    over = r2(B['invoiced'] - earned)
    T = await C.js("pid => { const p = DB.projects.find(x => x.id === pid); const J = jobFin(p); return {eac: J.eac, actual: J.actual, earned: J.earned, billed: J.billed, overUnder: J.overUnder, pct: tpJobPct(p), held: J.pctHeld || null}; }", pid)
    C.t(f"the app's jobFin for reference (not the expectation): {T}")
    await C.as_('u_owner', 'reports', "repTab = 'wip'; REP.preset = 'all'; repFrom = ''; repTo = '';")
    w = await read_row(C, '#v-reports table', nm)
    C.fig('EAC (estimate at completion)', 'from jobFin vs records', T['eac'], eac)
    C.fig('job cost to date', 'jobFin', T['actual'], actual)
    C.fig('earned revenue (cost basis)', 'jobFin', T['earned'], earned, tol=1.0 if not T['held'] else 1e9)
    if w:
        vals = [money_of(x) for x in w['__cells'] if money_of(x) is not None]
        # the schedule shows over billing and under billing in their own columns, each as a positive amount
        hit = any(abs(abs(v) - abs(over)) <= 1 for v in vals)
        C.ok(hit, f"WIP schedule: {nm} {'over' if over >= 0 else 'under'} billing {fmtm(abs(over))} (billed {fmtm(B['invoiced'])} less earned {fmtm(earned)})", w['__cells'])
        C.figs.append(('WIP over/under', 'WIP schedule', next((v for v in vals if abs(abs(v) - abs(over)) <= 1), None), abs(over), hit))
    else:
        C.ok(False, f'the WIP schedule lists {nm}')
    # % complete: one number on every surface
    pct = T['pct']
    await C.as_('u_owner', 'reports', "repTab = 'portfolio'; REP.preset = 'all'; repFrom = ''; repTo = '';")
    pf = await read_row(C, '#v-reports table', nm)
    a = await C.js("q => { signIn('u_owner'); const a = paAsk(q); return a.headline + ' ' + (a.note || ''); }", f'how far along is {nm}')
    C.ok(f'{pct}%' in a, f'% complete: Ask "how far along" says {pct}%', a[:200])
    C.ok(pf and any(f'{pct}%' in x for x in pf['__cells']), f'% complete: the Portfolio row says {pct}%', pf and pf['__cells'])
    # 3. overhead and true profitability, from the records: September's pool and this job's share
    oh_lines = {}
    for t in R['ohTxns']:
        oh_lines[t['name']] = r2(oh_lines.get(t['name'], 0) - t['amt'])
    run = C.ids['payroll']['run']
    office = 0.0
    emp = {e['id']: e for e in R['emps']}
    runs = {r['id']: r for r in R['runs']}
    for t in R['time']:
        if t['projectId'] or t['payrollId'] != run['id']: continue
        e = emp[t['empId']]; r = runs[t['payrollId']]
        part = next(x for x in r['parts'] if x['entityId'] == e['entityId'])
        office += hours_of(t) * e['rate'] * part['total'] / part['gross']
    oh_lines['Payroll — office & overhead'] = r2(office)
    pool = r2(sum(oh_lines.values()))
    C.t(f"September's overhead from the records: {oh_lines} = {fmtm(pool)}")
    M = await C.js("() => { const m = ohMonth('2026-09'); return {pool: m.pool, lines: m.lines, base: m.base, T: m.baseTotal, alloc: m.alloc, uncoded: m.uncoded}; }")
    C.fig('September overhead pool', 'ohMonth (the P&L less uncoded)', M['pool'], pool)
    for k in ('Rent & occupancy', 'Insurance', 'Office & software', 'Vehicle & fuel', 'Marketing', 'Design software (CAD, rendering)', 'Payroll — office & overhead'):
        C.fig(f'September overhead line {k}', 'ohMonth', M['lines'].get(k, 0), oh_lines.get(k, 0))
    C.ok(abs(sum(M['alloc'].values()) - M['pool']) < 0.011, 'the jobs\' shares add up to the pool to the cent', M)
    sep_base = r2(sum(v['actual'] for v in B['lines'].values()) + B['rebill_cost'])  # every cost of the job landed in September, the purchase billed back included
    C.fig(f'{nm} September base (direct cost)', 'ohMonth', M['base'].get(pid, 0), sep_base)
    share = r2(pool * sep_base / M['T']) if M['T'] else 0
    C.t(f"the other jobs' September bases are read from the app ({ {k: v for k, v in M['base'].items() if k != pid} }); this job's share = pool × its base / all bases = {fmtm(share)}")
    jgross = r2(earned - actual); jnet = r2(jgross - share)
    C.rec('books', 'profit', {'earned': earned, 'actual': actual, 'gross': jgross, 'overhead': share, 'net': jnet, 'pool': pool})
    # the job report's Profit After Overhead, the Portfolio's and the Pack's tables, Ask
    await C.as_('u_owner', 'reports', f"repTab = 'profit'; repProj = '{pid}'; REP.preset = 'all'; repFrom = ''; repTo = '';")
    jt = await C.js("() => { const k = [...document.querySelectorAll('#v-reports .oh-job .kpi')].map(x => [x.querySelector('span').innerText, x.querySelector('b').innerText]); const m = (document.querySelector('#v-reports .oh-method') || {}).innerText || ''; return {k, m}; }")
    K = {a.split(' ·')[0].strip().lower(): money_of(b) for a, b in jt['k']}
    C.fig('gross profit to date', 'job report', K.get('gross profit'), jgross, tol=1.0)
    C.fig('overhead allocated', 'job report', K.get('overhead allocated'), share, tol=1.0)
    C.fig('net profit after overhead', 'job report', K.get('net profit'), jnet, tol=1.0)
    C.ok('shared among the jobs by total direct cost' in jt['m'], 'the job report states the allocation method', jt['m'][:160])
    method = jt['m'].split(' The burden rate')[0].strip()
    await C.as_('u_owner', 'reports', "repTab = 'portfolio'; REP.preset = 'all'; repFrom = ''; repTo = '';")
    pr = await C.js("pid => { const tr = document.querySelector(`#v-reports table.oh-jobs tr[data-ohjob='${pid}']`); return tr ? [...tr.children].map(td => td.innerText) : null; }", pid)
    pm = await C.js("() => (document.querySelector('#v-reports .oh-method') || {}).innerText || ''")
    C.ok(pr, 'the Portfolio has Profit After Overhead for the job', pr)
    if pr:
        C.fig('gross profit', 'Portfolio', money_of(pr[3]), jgross, tol=1.0)
        C.fig('overhead', 'Portfolio', money_of(pr[5]), share, tol=1.0)  # the tables show whole dollars
        C.fig('net profit', 'Portfolio', money_of(pr[6]), jnet, tol=1.0)
    C.ok(method and method in pm, 'the Portfolio states the same method', pm[:200])
    await C.as_('u_owner', 'reports', "repTab = 'pack'; REP.preset = 'custom'; REP.from = '2026-09-01'; REP.to = '2026-09-30'; repFrom = '2026-09-01'; repTo = '2026-09-30';")
    pk = await C.js("pid => { const tr = document.querySelector(`#v-reports table.oh-jobs tr[data-ohjob='${pid}']`); return {row: tr ? [...tr.children].map(td => td.innerText) : null, rate: (document.querySelector('#v-reports .oh-pack') || {}).innerText || '', m: (document.querySelector('#v-reports .oh-method') || {}).innerText || ''}; }", pid)
    C.ok(pk['row'], 'the September Pack has Profit After Overhead for the job', pk)
    if pk['row']:
        C.fig('overhead (September)', 'Pack', money_of(pk['row'][5]), share, tol=1.0)  # the tables show whole dollars
        C.fig('net profit (September)', 'Pack', money_of(pk['row'][6]), jnet, tol=1.0)
    rate_pct = round(100 * pool / M['T'], 1) if M['T'] else 0
    C.ok(f'{rate_pct:g}%' in pk['rate'], f'the Pack states September\'s overhead rate {rate_pct:g}% of direct cost', pk['rate'])
    C.ok(method and method in pk['m'], 'the Pack states the same method', pk['m'][:200])
    for q, need in ((f'what is the margin on {nm}', [jgross, jnet]), ('how much overhead did we spend in September', [pool]), (f"what is {nm}'s profit after overhead", [share, jnet])):
        a = await C.js("q => { signIn('u_owner'); const a = paAsk(q); return (a.headline || '') + ' ' + (a.note || '') + ' ' + (a.work || []).join(' '); }", q)
        nums = [float(x.replace(',', '')) for x in re.findall(r'\$([\d,]+(?:\.\d+)?)', a)]
        for v in need:
            hit = any(abs(n - v) <= 1 for n in nums)
            C.figs.append((f'Ask: {q}', 'Ask', v if hit else None, v, hit))
            C.ok(hit, f'Ask "{q}" says {fmtm(v)}', a[:240])
        C.t(f'Ask "{q}" → "{a[:220]}"')
    # 4. the P&L (September) shows the overhead in operating expenses; nothing is left "Needs Category"
    await C.as_('u_owner', 'reports', "repTab = 'company'; cfoPeriod = 'custom'; REP.preset = 'custom'; REP.from = '2026-09-01'; REP.to = '2026-09-30'; repFrom = '2026-09-01'; repTo = '2026-09-30';")
    pl = await C.js("() => document.querySelector('#v-reports').innerText")
    for k in ('Rent & occupancy', 'Insurance', 'Marketing', 'Vehicle & fuel'):
        C.fig(f'P&L September overhead: {k}', 'P&L detail', money_after(pl, k), oh_lines.get(k, 0))
    nc = re.findall(r'(?m)^\s*Needs Category\t[^\n]*', pl)
    C.ok(not nc, 'the September P&L has no line left "Needs Category"', nc[:2])
    # 5. AR and AP aging: the client owes nothing; the four vendors are paid, the sub's retainage is what is left
    await C.as_('u_owner', 'reports', "repTab = 'ar';")
    ar = await C.js("() => document.querySelector('#v-reports').innerText")
    arow = re.search(re.escape(CLIENT) + r'[^\n]*', ar)
    C.ok(not arow or all((money_of(x) or 0) == 0 for x in re.findall(r'\$[\d,.]+', arow.group(0))), 'AR aging: the Vargas owe nothing (both invoices paid from the bank)', arow and arow.group(0))
    await C.as_('u_owner', 'reports', "repTab = 'payables';")
    ap = await C.js("() => document.querySelector('#v-reports').innerText")
    for vname, _, _ in VENDORS:
        row = re.search(re.escape(vname) + r'[^\n]*', ap)
        amts = [money_of(x) for x in re.findall(r'\$[\d,.]+', row.group(0))] if row else []
        ok = not row or all(a in (0, 660, 240) for a in amts)
        C.ok(ok, f'AP aging: {vname} is owed nothing open (retainage $660 and the disputed $240 are held, not due)', row and row.group(0))
    # 6. coverage: the job's cost and income are backed by the bank and the card
    await C.as_('u_owner', 'reports', f"repTab = 'profit'; repProj = '{pid}'; REP.preset = 'all'; repFrom = ''; repTo = '';")
    cov = await C.js("() => (document.querySelector('#v-reports .tr-cov-line') || {}).innerText || ''")
    parts = [money_of(x) for x in re.findall(r'\$[\d,]+(?:\.\d+)?', cov)]
    # cost: all of it backed by a bank or card line; income: what was collected is backed, the retainage still held is
    # the only accrual (it is not due until the job is done), nothing by hand
    want_cost = r2(sum(v['actual'] for v in B['lines'].values()) + B['rebill_cost'])
    C.ok(len(parts) >= 6 and abs(parts[0] - want_cost) <= 1 and parts[1] == 0 and parts[2] == 0, f"coverage: all {fmtm(want_cost)} of the job's cost is backed by a bank or card line, none by a document only or by hand", cov)
    C.ok(len(parts) >= 6 and abs(parts[3] - B['collected']) <= 1 and abs(parts[4] - B['retainage']) <= 1 and parts[5] == 0, f"coverage: income {fmtm(B['collected'])} backed by the bank; the {fmtm(B['retainage'])} retainage held is the only accrual", cov)
    C.t(f'coverage line: "{cov}"')
    # 7. the Three-Way Tie-Out for September: the bank column carries the chain's deposits and payments
    await C.as_('u_owner', 'reports', "repTab = 'tieout'; REP.preset = 'custom'; REP.from = '2026-09-01'; REP.to = '2026-09-30'; repFrom = '2026-09-01'; repTo = '2026-09-30';")
    tie = await C.js("() => { const T = truthTieOut('2026-09'); return {rows: (T.rows || []).map(r => [r.group || r.label || r.acct, r.bank, r.erp, r.qbo]), headline: T.headline || ''}; }")
    bank_in = r2(sum(t['amt'] for t in R['txns'] if t['amt'] > 0 and t['date'].startswith('2026-09')))
    C.t(f"Three-Way Tie-Out September: {tie['rows'][:8]}")
    C.ok(tie['rows'], 'the Three-Way Tie-Out has September rows (bank and ERP columns)', tie)
    # 8. Report Builder: a saved search over the new bills
    await C.as_('u_owner', 'reports', "repTab = 'searches'; ssOpen = null;")
    have = await C.js("n => !!searchList().find(x => x.name === n)", f'{JOB} bills')
    if not (again and have):
        await C.click('#ss-new', 500)
        await C.fill('#ss-name', f'{JOB} bills', tab=True)
        await C.pg.select_option('#ss-ds', 'bills'); await C.pg.dispatch_event('#ss-ds', 'change'); await C.wait(300)
        crit = C.pg.locator('#v-reports .ss-crit').last
        await crit.locator('[data-cf=field]').select_option('project'); await C.wait(200)
        crit = C.pg.locator('#v-reports .ss-crit').first
        await crit.locator('[data-cf=op]').select_option('eq')
        vin = crit.locator('[data-cf=value]')
        if await vin.count():
            await vin.fill(JOB); await vin.press('Tab'); await C.wait(300)
    ss = await C.js("n => { const s = searchList().find(x => x.name === n); if (!s) return null; const r = searchRun(s); return {n: r.rows.length, total: Math.round(r.rows.reduce((a, x) => a + (+x.total || 0), 0) * 100) / 100, criteria: s.criteria}; }", f'{JOB} bills')
    want_n = len(R['bills']); want_total = r2(sum(r2(sum(l['amount'] for l in b['lines']) * (1 - b['ret'] / 100)) for b in R['bills']))
    C.ok(ss and ss['n'] == want_n, f"Report Builder: '{JOB} bills' lists the {want_n} bills", ss)
    C.fig('saved search: bills total (net of retainage, as the dataset defines it)', 'Report Builder', ss and ss['total'], want_total)
    C.rec('search', 'bills', ss)
    return True


# ================================================================ 9. save, reload, every record and link, the reports again
# The documents a reload must leave exactly as saved: each client's estimates, change orders, invoices, payments and
# schedule of values, the POs, bills, bank and card lines, payroll runs, time, the closed periods and the journals.
DOC_SNAP = """() => { const out = {};
  (DB.clients || []).forEach(c => ['estimates', 'changeOrders', 'invoices', 'payments', 'sov'].forEach(k => (c[k] || []).forEach(d => { out[`${k}:${d.id}`] = JSON.stringify(d); })));
  ['pos', 'bills', 'txns', 'payroll', 'time', 'journal', 'journals', 'payments'].forEach(k => Array.isArray(DB[k]) && DB[k].forEach((d, i) => { out[`${k}:${d.id || i}`] = JSON.stringify(d); }));
  out['periods'] = JSON.stringify(DB.periods || {});
  return out; }"""

LINKS = """I => { const c = DB.clients.find(x => x.id === I.client.id), p = DB.projects.find(x => x.id === I.project.id);
  const est = c && c.estimates.find(e => e.id === I.estimate.id);
  const U = new Set(((PRED.unmatchedTxns && PRED.unmatchedTxns.rows) ? PRED.unmatchedTxns.rows() : []).map(t => t.id));
  const inv = id => c && c.invoices.find(i => i.id === id);
  return {
    client: !!c, project: !!p && p.clientId === (c || {}).id, estimate: est && est.status, estOnJob: !!est && est.projectId === (p || {}).id,
    portal: ((DB.users || []).find(u => u.id === I.portalUser.id) || {}).clientId === (c || {}).id,
    sov: Object.values(I.sov.lines).every(id => c && c.sov.some(v => v.id === id && v.projectId === p.id)),
    pos: Object.entries(I.po).map(([k, v]) => { const po = DB.pos.find(x => x.id === v.id); return [k, po && po.status, !!po && po.lines.every(l => polLinked(l))]; }),
    bills: Object.entries(I.bill).map(([n, id]) => { const b = DB.bills.find(x => x.id === id); return [n, b && b.status, !!b && !!b.poId && DB.pos.some(o => o.id === b.poId), !!b && (b.lines || []).every(l => l.poLineId), !!b && billIsPaid(b)]; }),
    txns: [...Object.entries(I.txn.card || {}), ...Object.entries(I.txn.bank || {})].map(([k, id]) => { const t = DB.txns.find(x => x.id === id); return [k, !!t, !!t && (!U.has(id) || !!t.exception)]; }),
    invoices: ['appSent', 'rebillSent'].map(k => { const i = inv((I.invoice[k] || {}).id || I.invoice[k === 'appSent' ? 'app' : 'rebill']); return [k, i && i.status, i && docTotal(i).total, !!i && c.payments.some(py => py.invoiceId === i.id)]; }),
    payroll: (() => { const r = DB.payroll.find(x => x.id === I.payroll.run.id); return r && {status: r.status, txn: DB.txns.some(t => t.payrollId === r.id || (t.match && t.match.payrollId === r.id)), entries: DB.time.filter(t => t.payrollId === r.id).length}; })(),
    co: (() => { const x = c && c.changeOrders.find(x => x.id === I.co.co.id); return x && {status: x.status, sov: c.sov.some(v => v.coId === x.id)}; })(),
    close: {locked: lockedThrough(), sealed: Object.keys((DB.periods && DB.periods.chains) || {}).sort()},
  }; }"""


async def s9_save(C):
    C.step('9. Save, reload, and every record and link is there; no document changed on the way')
    await C.as_('u_owner', 'home')
    a = await C.js(DOC_SNAP)
    await C.js("async () => { save(); await saveNow(); }")
    t0 = time.time()
    await C.pg.reload(); await C.pg.wait_for_function("document.body.dataset.booted==='1'", timeout=90000)
    C.t(f'saveNow, then reload: booted again in {time.time() - t0:.1f}s')
    await C.as_('u_owner', 'home')
    b = await C.js(DOC_SNAP)
    changed = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
    C.ok(not changed, f'saveNow and reload: all {len(a)} documents (estimates, COs, invoices, payments, SOV, POs, bills, bank and card lines, payroll, time, periods) are exactly as saved', changed[:12])
    C.t(f'{len(a)} documents compared before the save and after the reload: {len(changed)} changed' + (f' ({changed[:6]})' if changed else ''))
    L = await C.js(LINKS, C.ids)
    C.t(f'after the reload: {json.dumps(L, default=str)[:900]}')
    C.ok(L['client'] and L['project'] and L['estimate'] == 'converted' and L['estOnJob'] and L['portal'] and L['sov'], 'the client, the job, the signed estimate on its job, the portal user on the client, the schedule of values', L)
    C.ok(all(x[2] for x in L['pos']), 'every PO is there with each line linked', L['pos'])
    C.ok(all(x[2] and x[3] and x[4] for x in L['bills']), 'every bill is there on its PO, each line on its PO line, paid', L['bills'])
    C.ok(all(x[1] and x[2] for x in L['txns']), 'every bank and card line of the chain is there, matched or with a signed exception', [x for x in L['txns'] if not (x[1] and x[2])])
    C.ok(all(x[1] == 'paid' and x[3] for x in L['invoices']), 'the application and the billable expenses are paid, each with its payment', L['invoices'])
    C.ok(L['payroll'] and L['payroll']['status'] in ('paid', 'verified') and L['payroll']['txn'] and L['payroll']['entries'] == len(C.ids['time']['ids']), 'the payroll run is paid from the bank, with its time entries', L['payroll'])
    C.ok(L['co'] and L['co']['status'] in ('approved', 'billed') and L['co']['sov'], 'the change order is approved and on the schedule of values', L['co'])
    C.ok(L['close']['locked'] >= '2026-09' and '2026-09' in L['close']['sealed'], 'September stays closed and sealed', L['close'])
    return await s8_reports(C, again=True)


# ================================================================ 10. PO lines linked to their estimate and invoice lines
async def s10_polinks(C):
    C.step('10. PO lines link to estimate and invoice lines: Which Lines?, the chips both ways, Not Linked blocks approval, billed back, overhead on the phone, after a reload')
    pid = C.ids['project']['id']; est = C.ids['estimate']['id']; L = C.ids['estimate']['lines']
    tile_id = L['Tile – primary bath']; tile_key = f'estimate:{est}:{tile_id}'
    await C.day('2026-10-02')
    # the coordinator's New PO opens on the job's lines
    await C.as_('u_chen', 'po', f"setCurrent('{pid}'); poOpen = null;")
    await C.click('#btn-newpo', 700)
    m = await C.modal()
    cls = await C.js("() => { const b = document.querySelector('#mbm-blank'); return b ? b.className : null; }")
    C.ok(m and m['title'] == 'Which Lines?', 'Purchasing > New PO opens on "Which Lines?" (the estimate, change-order and invoice lines of the job)', m and m['title'])
    C.ok(cls is not None and 'primary' not in cls, 'Start Blank is there, secondary (not blue); Create the Purchase Orders is the blue button', cls)
    C.t(f"Coordinator > Purchasing > New PO → \"{m and m['title']}\" with {m and m['buttons']}")
    await C.pg.locator(f"#mbm [data-ctpsel='{tile_id}']").check()
    await C.fill(f"#mbm [data-ctpq='{tile_id}']", '1')
    await C.fill(f"#mbm [data-ctpc='{tile_id}']", '640')
    await C.fill(f"#mbm [data-ctpv='{tile_id}']", 'Arcadia Tile Supply')
    n0 = await C.js("() => DB.pos.length")
    await C.modal_ok(900)
    po = await C.js("n0 => { const po = DB.pos.slice(n0)[0]; return po && {id: po.id, number: po.number, status: po.status, vendor: po.vendor, lines: po.lines.map(l => ({id: l.id, item: l.item, line: l.line || '', code: l.code || ''}))}; }", n0)
    C.ok(po and po['lines'] and po['lines'][0]['line'] == tile_key, 'tick the tile line > Create the Purchase Orders: the PO line carries its estimate line from the start', po)
    C.t(f"tick \"Tile – primary bath\", 1 ls at $640, Arcadia Tile Supply > Create the Purchase Orders → {po and po['number']} ({await C.toast()})")
    if not po: return False
    C.rec('polinks', 'po', po)
    await C.as_('u_chen', 'po', f"setCurrent('{pid}'); poOpen = '{po['id']}';")
    chip = await C.js("() => [...document.querySelectorAll('#po-doc .pol-cell')].map(c => c.innerText.replace(/\\s+/g, ' '))")
    C.ok(chip and 'Tile – primary bath' in chip[0], 'the PO line shows its estimate line as a chip', chip)
    # PO line > estimate line > back to the PO
    await C.click('#po-doc [data-polopen]', 600)
    m = await C.modal()
    C.ok(m and 'Tile – primary bath' in m['title'] and po['number'] in m['text'] and 'Purchase Order Lines' in m['text'], 'the chip opens the estimate line: budget, committed, spent, its PO lines, bills and bank lines', m and (m['title'], m['text'][:300]))
    await C.click(f"#mbm [data-polrow='{po['lines'][0]['id']}']", 600)
    back = await C.js("() => ({view, poOpen})")
    C.ok(back['view'] == 'po' and back['poOpen'] == po['id'], 'the estimate line\'s PO line opens the PO', back)
    C.t(f"PO > chip \"{chip[0][:60]}\" → the line's drill-down \"{m and m['title']}\" > {po['number']} row → back on the PO")
    # a line added by hand has no link: Not linked, and the order cannot go out
    await C.click('#po-doc [data-addline]', 500)
    rows = C.pg.locator('#po-doc tr[data-line]')
    last = rows.last
    await last.locator('input[data-f=item]').fill('Heated towel bar, brushed nickel (client upgrade)'); await last.locator('input[data-f=item]').press('Tab'); await C.wait(400)
    last = C.pg.locator('#po-doc tr[data-line]').last
    await last.locator('input[data-f=price]').fill('385'); await last.locator('input[data-f=price]').press('Tab'); await C.wait(400)
    nl = await C.js("id => { const po = DB.pos.find(x => x.id === id); const l = po.lines[po.lines.length - 1]; return {id: l.id, linked: polLinked(l), chip: (document.querySelector(`#po-doc tr[data-line='${l.id}'] .pol-cell`) || {}).innerText || ''}; }", po['id'])
    C.ok(not nl['linked'] and 'Not linked' in nl['chip'], 'Add line > "Heated towel bar…" $385: the new line shows Not linked', nl)
    cnt = await C.js("pid => [PRED.poLinesUnlinked.count(pid), PRED.poLinesUnlinked.rows(pid).length, EQ_TABLES.polines().filter(r => r.projectId === pid && !r.linked && r.poStatus !== 'cancelled').length, erpQuery ? (() => { try { return erpQuery({table: 'polines', where: {projectId: pid, linked: false}}).rows.length; } catch (e) { return 'n/a'; } })() : 'n/a']", pid)
    C.ok(cnt[0] == cnt[1] == cnt[2] == 1, 'PO Lines Not Linked: the count equals its rows and the query table (1)', cnt)
    await C.click('#po-doc [data-poact=issue]', 600)
    t = await C.toast(); st = await C.js("id => DB.pos.find(x => x.id === id).status", po['id'])
    C.ok('not linked' in t and st == 'draft', 'Issue PO is refused while a line is not linked; the toast says which', f'{st} · {t}')
    C.t(f"Issue PO → \"{t}\" ({st})")
    # Link > search > Reimbursable: billed back to the client
    await C.click(f"#po-doc [data-polpick='{nl['id']}']", 500)
    await C.fill('#mbm #pol-q', 'reimb'); await C.wait(200)
    vis = await C.js("() => [...document.querySelectorAll('#mbm .pol-opt')].filter(b => b.getClientRects().length).map(b => b.dataset.polk)")
    C.ok(vis == ['rebill'], 'the picker\'s search narrows to Reimbursable', vis)
    await C.click("#mbm [data-polk='rebill']", 600)
    t = await C.toast()
    C.ok('Billed back to the client' in t and 'Open' in t, 'Link > "reimb" > Reimbursable: the toast says what was linked, with Open', t)
    await C.click('#po-doc [data-poact=issue]', 700)
    m = await C.modal()
    if m: await C.modal_ok(700)
    st = await C.js("id => DB.pos.find(x => x.id === id).status", po['id'])
    C.ok(st == 'issued', 'with every line linked, Issue PO issues it', f'{st} {await C.toast()}')
    # it arrives; the bill from the receipt; the reimbursable is waiting to be billed back, once
    await C.as_('u_chen', 'recv', f"setCurrent('{pid}');")
    await C.click(f"section.view.on [data-rall='{po['id']}']", 700)
    await C.pg.locator('#toast .toast-open', has_text='Bill It').first.click(timeout=20000); await C.wait(600)
    await C.fill('#mbm [data-f=number]', 'AT-7802')
    await C.modal_ok(700)
    rb = await C.js("([pid, lid]) => { const R = rbRows(pid).filter(x => x.pl && x.pl.id === lid); const S = spUnbilled(pid).filter(x => x.key === 'rbpl:' + lid); return {rows: R.length, cost: R[0] && R[0].cost, amount: R[0] && R[0].amount, spend: S.length}; }", [pid, nl['id']])
    C.ok(rb['rows'] == 1 and rb['spend'] == 1 and abs((rb['amount'] or 0) - r2(385 * 1.1)) < 0.01, 'billed by its vendor, the billed-back line waits once in Purchases Not Billed Back, at cost plus 10% ($423.50)', rb)
    C.t(f"Receiving > Everything Arrived > Bill It > AT-7802 > Save Bill → the towel bar waits to be billed back: {rb}")
    r = await billing_row(C, 'bought for')
    C.ok(r and r['verb'] == 'Draft' and '423.50' in r['text'], 'Billing Queue: the PO line bought for the Vargas, with Draft', r)
    if r:
        await press_row(C, r['key'])
    il = await C.js("id => { for (const po of DB.pos) { const l = po.lines.find(x => x.id === id); if (l) { const h = l.invoiceLineId && rbInvLine(l.invoiceLineId); return {invoiceId: l.invoiceId || '', invoiceLineId: l.invoiceLineId || '', number: h && h.inv.number, rate: h && h.l.rate, left: rbRows(po.projectId).filter(x => x.pl && x.pl.id === id).length}; } } return null; }", nl['id'])
    C.ok(il and il['invoiceLineId'] and abs((il['rate'] or 0) - 423.5) < 0.01 and il['left'] == 0, 'Draft: the PO line is billed on its own invoice line, and the link is on the PO line', il)
    C.rec('polinks', 'rebill', il)
    await C.as_('u_chen', 'po', f"setCurrent('{pid}'); poOpen = '{po['id']}';")
    await C.click(f"#po-doc [data-polinv='{nl['id']}']", 600)
    m = await C.modal()
    C.ok(m and po['number'] in m['text'] and 'AT-7802' in m['text'], 'the chip "Billed on …" opens the invoice line: its PO line and its bill', m and m['text'][:300])
    C.t(f"PO > \"Billed on {il and il['number']}\" → {m and m['title']}: {m and m['text'][:160]!r}")
    # an order for the shop, no job: Start Blank, then the line linked to overhead on the phone
    await C.js("() => mbCloseModal()")
    await C.as_('u_chen', 'po', f"setCurrent('{pid}'); poOpen = null;")
    await C.click('#btn-newpo', 600)
    await C.click('#mbm #mbm-blank', 600)
    d = await C.js("() => (document.querySelector('#d-title') || {}).textContent")
    C.ok(d and 'purchase order' in d.lower(), 'Start Blank opens the blank purchase order', d)
    await C.pg.select_option('#e-vendorsel', 'Arcadia Tile Supply')
    if await C.pg.locator('#e-poproj').count(): await C.pg.select_option('#e-poproj', '')
    n0 = await C.js("() => DB.pos.length")
    await C.click('#d-save', 900)
    shop = await C.js("n0 => { const po = DB.pos.slice(n0)[0]; return po && {id: po.id, number: po.number, projectId: po.projectId || ''}; }", n0)
    C.ok(shop and not shop['projectId'], 'Start Blank > Arcadia Tile Supply > No job > Create draft: a draft for the shop', shop)
    if not shop: return False
    await C.as_('u_chen', 'po', f"poOpen = '{shop['id']}';")
    if not await C.js("id => DB.pos.find(x => x.id === id).lines.length", shop['id']):
        await C.click('#po-doc [data-addline]', 500)
    last = C.pg.locator('#po-doc tr[data-line]').last
    await last.locator('input[data-f=item]').fill('Grout sponges and mixing buckets (shop stock)'); await last.locator('input[data-f=item]').press('Tab'); await C.wait(400)
    last = C.pg.locator('#po-doc tr[data-line]').last
    await last.locator('input[data-f=price]').fill('86'); await last.locator('input[data-f=price]').press('Tab'); await C.wait(400)
    sl = await C.js("id => { const l = DB.pos.find(x => x.id === id).lines.slice(-1)[0]; return {id: l.id, linked: polLinked(l)}; }", shop['id'])
    C.ok(not sl['linked'], 'the shop line starts Not linked (no job, no line to guess)', sl)
    await C.to_phone('u_chen', 'The coordinator linking a shop order to overhead', f"view = 'po'; poOpen = '{shop['id']}';")
    await C.ptap(f"#po-doc [data-polpick='{sl['id']}']", 'Link')
    await C.pcheck('the link picker (a sheet)')
    await C.pfill('#mbm #pol-q', 'office', 'Search')
    await C.ptap("#mbm [data-polk='oh:office']", 'Overhead · Office & software')
    C.plog(f"→ {await C.ph.evaluate(TOAST)}")
    await C.pcheck('the PO after linking')
    await C.to_desk()
    oh = await C.js("id => { const po = DB.pos.find(x => x.id === id); const l = po.lines.slice(-1)[0]; return {ohCat: l.ohCat || '', linked: polLinked(l), cat: poCat(po)}; }", shop['id'])
    C.ok(oh['ohCat'] == 'office' and oh['linked'] and oh['cat'] == 'office', 'on the phone: Link > "office" > Office & software: the shop line is overhead, and its bill will post to that account', oh)
    # reload: the links are all there; the counts still equal the rows
    before = await C.js("ids => ids.map(id => { const po = DB.pos.find(x => x.id === id); return po.lines.map(l => [l.id, l.line || '', l.ohCat || '', !!l.billable, l.invoiceLineId || '']); })", [po['id'], shop['id']])
    await C.js("async () => { save(); await saveNow(); }")
    await C.pg.reload(); await C.pg.wait_for_function("document.body.dataset.booted==='1'", timeout=90000)
    await C.as_('u_owner', 'home')
    after = await C.js("ids => ids.map(id => { const po = DB.pos.find(x => x.id === id); return po.lines.map(l => [l.id, l.line || '', l.ohCat || '', !!l.billable, l.invoiceLineId || '']); })", [po['id'], shop['id']])
    C.ok(before == after, 'after saveNow and a reload every PO line keeps its estimate line, overhead category, billed-back mark and invoice line', after)
    cnt = await C.js("() => [PRED.poLinesUnlinked.count(), PRED.poLinesUnlinked.rows().length, EQ_TABLES.polines().filter(r => !r.linked && r.poStatus !== 'cancelled').length]")
    C.ok(cnt[0] == cnt[1] == cnt[2], 'PO Lines Not Linked: the count equals its rows and the query table, firm-wide', cnt)
    C.t(f'after the reload: PO lines {after}; PO Lines Not Linked {cnt}')
    return True


# ================================================================ main
STEPS = [s1_client, s2_buy, s3_receive, s4_pay, s5_bill, s6_bank, s7_close, s8_reports, s9_save, s10_polinks]


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--upto', type=int, default=99)
    ap.add_argument('--dump', default='', help='development: write the DB as JSON here after the steps run')
    ap.add_argument('--resume', default='', help='development: load a --dump file and start at --start')
    ap.add_argument('--start', type=int, default=1)
    a = ap.parse_args()
    async with async_playwright() as p:
        b, pg, errs = await open_app(p)
        C = Chain(pg, errs)
        await C.phone_open(b)
        try:
            if a.resume:
                with open(a.resume) as f: src = f.read()
                await pg.evaluate("async s => { DB = JSON.parse(s).DB; save(); await saveNow(); }", src)
                await pg.reload(); await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=180000)
                with open(a.resume + '.ids.json') as f: C.ids = json.load(f)
                C.t(f'(development) resumed from {a.resume} at step {a.start}')
            for i, fn in enumerate(STEPS, 1):
                if i < a.start: continue
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
