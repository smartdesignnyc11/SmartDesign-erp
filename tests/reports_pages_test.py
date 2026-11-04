"""reports_pages_test: the four Reports pages (Alan, 11-03: docs/mockups/reports/SPEC.md), done as the person.

Each seat signs in, opens Reports from the menu (the phone's menu button, then the group by its name, then the page),
and reads the page the way the review read it, on the desktop (1440x900) and the phone (390x844, touch):

  MENU      the Reports group lists the seat's pages (owner and controller: Job Profitability, Cash, Financial
            Statements, Report Builder; billing: Job Profitability, Cash, Report Builder; the PM: Job Profitability,
            Report Builder; the coordinator and the designer: Report Builder). Each opens, its heading is its name,
            one blue button at most, nothing sideways at 390, no page errors
  JOBS      At Risk first, its number its rows, each row naming whose it is; one card per job; Margin and Work in
            Progress are two views of the same jobs; on Work in Progress each job's earned follows from its own
            printed cost-to-cost numbers (the review: 121 State earned 25% beside 27% on the same page); the company
            card explains the P&L-vs-jobs job cost gap with jobCostTie's reason, never a placeholder; a card opens
            that job's Budget. The PM sees his jobs and no company card
  CASH      one Safe to Spend, whole dollars, safeToSpend()'s; its parts to the cent add to Ours Today; no second
            "ours" figure ("Available Cash (Ours)") on the page or its views; At Risk's number is its rows; the
            $33,500 paid-before-approval row opens the bill, never Banking; the 13 weeks are tappable (on the phone
            one 44px row each); Client Funds, Receivables and Payables are views, Receivables' total is Billing's
  STMT      the period chips (This Week, August 2026, September to Date, Year to Date); August's Pack is a Draft and
            says how many close checks are open, and its Pack opens on August; the P&L reads companyPL to the dollar;
            what stands behind the numbers adds to the P&L's cost to the cent (the review: $14,841 short); the
            opening entry and any manual journal are listed and flagged; the week shows Safe to Spend as Cash does;
            the Balance Sheet balances
  BUILDER   Saved, Standard (the WIP Schedule and the Client Statement among them), Pinned; Start From reaches every
            EQ_TABLES entity (NetSuite's differentiator); a source tapped opens a new report on it with a toast and
            an Open link; "Invoices due this week" lists only invoices due this week
  FORWARD   the old pages land on their new homes: the WIP Schedule on Job Profitability, Work in Progress;
            Receivables on Cash; the Monthly Pack on Financial Statements; Build a Report on the Report Builder;
            the Dashboard on the Report Builder, Pinned; Billing's Client Funds on Cash, Client Funds
  READ      opening every page and every chip leaves the data byte for byte as it was

  python3 reports_pages_test.py [--user u_owner,...] [--desktop|--phone] [part ...]
"""
import asyncio, re, sys, json
from harness import *

MENU = {
    'u_owner': ['Job Profitability', 'Cash', 'Financial Statements', 'Report Builder'],
    'u_controller': ['Job Profitability', 'Cash', 'Financial Statements', 'Report Builder'],
    'u_billing': ['Job Profitability', 'Cash', 'Report Builder'],
    'u_alan': ['Job Profitability', 'Report Builder'],
    'u_chen': ['Report Builder'],
    'u_sarah': ['Report Builder'],
}
PERSONS = ['u_owner', 'u_controller', 'u_alan', 'u_billing']
MONEY = r'([−\-]?\$[\d,]+(?:\.\d\d)?)'

def m2f(s):
    s = (s or '').strip()
    neg = s[:1] in '−-'
    m = re.search(r'\$([\d,]+(?:\.\d+)?)', s)
    if not m: return None
    v = float(m.group(1).replace(',', ''))
    return -v if neg else v

STATE = r"""() => { const vis = e => !!e && e.getClientRects().length > 0 && getComputedStyle(e).visibility !== 'hidden';
  const v = document.querySelector('.view.on'); const h = v && ([...v.querySelectorAll('h1')].find(vis) || [...v.querySelectorAll('h2')].find(vis));
  return { view, heading: h ? h.textContent.replace(/\s+/g, ' ').trim() : '', page: (v && v.querySelector(':scope > .rw-front') || {dataset: {}}).dataset.rwpage || '',
    prim: [...(v ? v.querySelectorAll('.btn.primary') : [])].filter(vis).map(b => b.textContent.trim()),
    sw: document.documentElement.scrollWidth, w: innerWidth, text: v ? v.innerText : '' }; }"""
# every target the page's own front draws: chips, rows that open, buttons, links (the phone's 44px rule)
SMALL = r"""() => { const F = document.querySelector('.view.on > .rw-front'); if (!F) return ['no front'];
  return [...F.querySelectorAll('button, a, [role=button], input')].filter(e => e.getClientRects().length).map(e => { const r = e.getBoundingClientRect();
    return r.height < 44 ? `${(e.innerText || e.getAttribute('aria-label') || e.tagName).replace(/\s+/g, ' ').slice(0, 40)} ${Math.round(r.height)}px` : ''; }).filter(Boolean); }"""

async def tap(pg, loc, phone):
    await loc.scroll_into_view_if_needed(timeout=4000)
    if phone: await loc.tap(timeout=4000)
    else: await loc.click(timeout=4000)
    await pg.wait_for_timeout(250)

async def open_reports(pg, phone, label):
    """the menu as the person: the phone's menu button, the Reports group by its name, then the page"""
    if phone and not await pg.evaluate("() => !!document.querySelector('.rail.open')"):
        await tap(pg, pg.locator('#menu-btn:visible').first, phone)
    h = pg.locator('#nav-groups [data-mnhead="reports"]').first
    if not await h.count(): return None
    if await h.get_attribute('aria-expanded') != 'true': await tap(pg, h, phone)
    kids = await pg.evaluate("""() => [...document.querySelectorAll('#nav-groups [data-mngr="reports"] button')].map(b => { const c = b.cloneNode(true); c.querySelectorAll('.n, svg').forEach(x => x.remove()); return c.textContent.replace(/\\s+/g, ' ').trim(); })""")
    if label is None: return kids
    if label not in kids: return kids
    i = kids.index(label)
    await tap(pg, pg.locator('#nav-groups [data-mngr="reports"] button').nth(i), phone)
    await pg.wait_for_timeout(300)
    return kids

async def chip(pg, phone, key):
    loc = pg.locator(f'.view.on > .rw-front [data-rwchip="{key}"]').first
    if not await loc.count(): return False
    await tap(pg, loc, phone)
    return True

def screen_ok(c, tag, st, phone, errs, want=None):
    if want: c.ok(st['heading'] == want, f'{tag}: heading "{st["heading"]}", want "{want}"')
    c.ok(len(st['prim']) <= 1, f'{tag}: {len(st["prim"])} blue buttons {st["prim"][:3]}')
    if phone: c.ok(st['sw'] <= st['w'], f'{tag}: scrolls sideways ({st["sw"]}px at {st["w"]})')
    c.ok(not errs, f'{tag}: page errors {errs[:2]}')
    del errs[:]

async def front_text(pg):
    return await pg.evaluate("() => { const F = document.querySelector('.view.on > .rw-front'); return F ? F.innerText : ''; }")

# ---------------------------------------------------------------------------------------------------------------- parts
async def part_menu(c, pg, uid, phone, errs, dev):
    kids = await open_reports(pg, phone, None)
    c.ok(kids == MENU[uid], f'{uid} {dev}: Reports lists {kids}, want {MENU[uid]}')
    for label in MENU[uid]:
        await open_reports(pg, phone, label)
        st = await pg.evaluate(STATE)
        screen_ok(c, f'{uid} {dev} Reports > {label}', st, phone, errs, label)
        c.ok(st['page'] in ('jobs', 'cash', 'stmt', 'builder'), f'{uid} {dev} {label}: no Reports page front ({st["view"]})')
        if phone:
            small = await pg.evaluate(SMALL)
            c.ok(not small, f'{uid} {dev} {label}: targets under 44px {small[:4]}')

async def part_jobs(c, pg, uid, phone, errs, dev):
    tag = f'{uid} {dev} Job Profitability'
    if 'Job Profitability' not in (await open_reports(pg, phone, 'Job Profitability') or []): return c.ok(False, f'{tag}: not on the menu')
    F = await pg.evaluate("""() => { const F = document.querySelector('.view.on > .rw-front'); if (!F) return null;
      const kids = [...F.children].map(e => e.className);
      const risk = F.querySelector('.rw-risk'); const n = risk && risk.querySelector('[data-rwrisk]');
      return { kids, first: kids.findIndex(k => /rw-risk/.test(k)), tiles: kids.findIndex(k => /rw-tiles/.test(k)), n: n ? +n.textContent : -1, rows: risk ? [...risk.querySelectorAll('.rw-rrow')].map(r => r.innerText) : [],
        jobs: [...F.querySelectorAll('.rw-job[data-rwjob]:not([data-rwjob=""])')].map(e => e.dataset.rwjob), company: !!F.querySelector('.rw-company'),
        tie: (F.querySelector('[data-rwtie]') || {}).innerText || '' }; }""")
    if not F: return c.ok(False, f'{tag}: no page front')
    c.ok(0 <= F['first'] < F['tiles'], f'{tag}: At Risk is not first, before where things stand ({F["kids"]})')
    c.ok(F['n'] == len(F['rows']), f'{tag}: At Risk says {F["n"]}, lists {len(F["rows"])}')
    c.ok(all(re.search(r'\bWith (you|Alan|the controller|the PM|billing)\b', r) for r in F['rows']), f'{tag}: an At Risk row does not name whose it is {F["rows"]}')
    want = await pg.evaluate("""() => (role() === 'pm' ? ovRows('jobs').map(x => x.p) : DB.projects).filter(p => { const J = jobFin(p); return J.contract > 0 || J.actual > 0.005 || J.committed > 0.005 || J.billed > 0.005; }).map(p => p.id)""")
    c.ok(sorted(F['jobs']) == sorted(want), f'{tag}: one card per job {F["jobs"]}, want {want}')
    if uid == 'u_alan': c.ok(not F['company'], f'{tag}: the PM sees the company card')
    else:
        c.ok(F['company'], f'{tag}: no company card')
        T = await pg.evaluate("() => { const T = jobCostTie(['2026-01-01', today()]); return { why: T.why, pl: T.plCost, jobs: T.jobs }; }")
        c.ok(T['why'] in F['tie'] and '[' not in F['tie'], f'{tag}: the P&L-vs-jobs gap is not jobCostTie\'s reason: "{F["tie"][:200]}"')
    # Work in Progress: the same jobs; each earned follows from its own printed numbers
    c.ok(await chip(pg, phone, 'jobs:wip'), f'{tag}: no Work in Progress chip')
    W = await pg.evaluate("""() => [...document.querySelectorAll('.view.on > .rw-front .rw-job[data-rwjob]:not([data-rwjob=""])')].map(e => { const f = {};
      e.querySelectorAll('.rw-fact').forEach(x => f[x.dataset.k] = (x.querySelector('b') || {}).textContent || ''); return { id: e.dataset.rwjob, f }; })""")
    c.ok(sorted(x['id'] for x in W) == sorted(want), f'{tag} WIP: not the same jobs {[x["id"] for x in W]}')
    for x in W:
        f = x['f']
        if 'earned' not in f: continue
        con, earned, proj = m2f(f.get('contract')), m2f(f.get('earned')), m2f(f.get('proj'))
        cost = m2f(f.get('ctc') or f.get('cost'))
        pct = float(re.sub(r'[^\d.]', '', f.get('pct', '')) or 'nan')
        ok = None not in (con, earned, proj, cost) and proj > 0
        c.ok(ok and abs(pct - 100 * cost / proj) <= 0.01 + 50 / proj, f'{tag} WIP {x["id"]}: {f.get("pct")} complete does not follow from {f.get("ctc") or f.get("cost")} of {f.get("proj")}')
        c.ok(ok and abs(earned - con * cost / proj) <= 3, f'{tag} WIP {x["id"]}: earned {f.get("earned")} does not follow from {f.get("contract")} × {f.get("ctc") or f.get("cost")} / {f.get("proj")}')
        J = await pg.evaluate("id => { const J = jobFin(DB.projects.find(p => p.id === id)); return { earned: J.earned, over: J.over, under: J.under, ahead: billedAhead(id).total }; }", x['id'])
        c.ok(ok and abs(earned - J['earned']) <= 0.5, f'{tag} WIP {x["id"]}: earned {f.get("earned")} is not the job\'s {J["earned"]}')
        if J['ahead'] > 0.005: c.ok(abs((m2f(f.get('ahead')) or 0) - J['ahead']) <= 0.5, f'{tag} WIP {x["id"]}: Billed Ahead {f.get("ahead")} is not billedAhead\'s {J["ahead"]}')
    # a card opens that job's Budget
    await chip(pg, phone, 'jobs:margin')
    first = await pg.evaluate("() => (document.querySelector('.view.on > .rw-front .rw-job[data-rwjob]:not([data-rwjob=\"\"])') || {dataset: {}}).dataset.rwjob")
    if first:
        await tap(pg, pg.locator(f'.view.on > .rw-front .rw-job[data-rwjob="{first}"]').first, phone)
        # the job's Budget; a seat with no Budget its Contract and Billing; the controller, who opens no job page, that
        # job's own profitability report
        st = await pg.evaluate("() => ({ view, pid: S && S.id, tab: repTab, proj: typeof repProj !== 'undefined' ? repProj : '', may: (ROLE_VIEWS[role()] || []).includes('costs') ? 'costs' : (ROLE_VIEWS[role()] || []).includes('jbill') ? 'jbill' : 'profit' })")
        ok = (st['view'] == st['may'] and st['pid'] == first) if st['may'] != 'profit' else (st['view'] == 'reports' and st['tab'] == 'profit' and st['proj'] == first)
        c.ok(ok, f'{tag}: the job card opens {st}, want that job\'s own page ({first})')
    del errs[:]

async def part_cash(c, pg, uid, phone, errs, dev):
    tag = f'{uid} {dev} Cash'
    if 'Cash' not in (await open_reports(pg, phone, 'Cash') or []): return
    X = await pg.evaluate("""() => { const F = document.querySelector('.view.on > .rw-front'); if (!F) return null;
      const fig = F.querySelectorAll('[data-rwfig="safe"]'); const risk = F.querySelector('.rw-risk');
      return { figs: [...fig].map(e => e.textContent.trim()), safe: safeToSpend().safe,
        parts: [...F.querySelectorAll('.rw-parts .rw-lrow')].map(r => [r.dataset.k || '', (r.querySelector('.rw-lv') || {}).textContent || '', (r.querySelector('.rw-lk b') || {}).textContent || '']),
        n: risk ? +(risk.querySelector('[data-rwrisk]') || {}).textContent : -1, rows: risk ? [...risk.querySelectorAll('.rw-rrow')].map(r => r.innerText) : [],
        weeks: F.querySelectorAll('[data-rwwk]').length }; }""")
    if not X: return c.ok(False, f'{tag}: no page front')
    whole = ('−' if X['safe'] < 0 else '') + '${:,.0f}'.format(abs(round(X['safe'])))
    c.ok(X['figs'] == [whole], f'{tag}: Safe to Spend reads {X["figs"]}, want one figure {whole} (safeToSpend)')
    cents = [p for p in X['parts'] if re.search(r'\.\d\d$', p[1])]
    c.ok(len(cents) == len(X['parts']) and len(X['parts']) >= 4, f'{tag}: the build-up is not to the cent {X["parts"]}')
    above = [m2f(p[1]) for p in X['parts'][:[p[0] for p in X['parts']].index('ours')]] if 'ours' in [p[0] for p in X['parts']] else []
    ours = next((m2f(p[1]) for p in X['parts'] if p[0] == 'ours'), None)
    c.ok(ours is not None and abs(sum(above) - ours) < 0.01, f'{tag}: the parts {above} do not add to Ours Today {ours}')
    c.ok(X['n'] == len(X['rows']), f'{tag}: At Risk says {X["n"]}, lists {len(X["rows"])}')
    c.ok(X['weeks'] == 13, f'{tag}: {X["weeks"]} weeks to tap, want 13')
    if phone:
        small = await pg.evaluate(SMALL)
        c.ok(not small, f'{tag}: targets under 44px {small[:4]}')
    # the $33,500 that left the bank before approval opens the bill, where Alan decides; never Banking
    i = next((k for k, r in enumerate(X['rows']) if 'before approval' in r), None)
    c.ok(i is not None, f'{tag}: no At Risk row for the bill paid before approval {X["rows"]}')
    if i is not None:
        await tap(pg, pg.locator('.view.on > .rw-front .rw-rrow').nth(i), phone)
        st = await pg.evaluate("() => ({ view, bill: /WW-2026-118/.test((document.querySelector('#drawer.on') || {}).innerText || '') || [...document.querySelectorAll('#drawer.on input')].some(i => i.value === 'WW-2026-118') })")
        c.ok(st['view'] != 'bank' and st['bill'], f'{tag}: the $33,500 row opens {st}, want the bill WW-2026-118')
        await pg.evaluate("() => { if (typeof closeEditor === 'function') closeEditor(); if (typeof mbCloseModal === 'function') try { mbCloseModal(); } catch (e) {} }")
        await open_reports(pg, phone, 'Cash')
    # the views, and no second "ours" figure anywhere on them
    for k, label in (('funds', 'Client Funds'), ('ar', 'Receivables'), ('ap', 'Payables'), ('weeks', 'Next 13 Weeks')):
        c.ok(await chip(pg, phone, f'cash:{k}'), f'{tag}: no {label} chip')
        st = await pg.evaluate(STATE)
        c.ok(not re.search(r'available cash \(ours\)|available \(ours\)|\bavailable \$[\d,]+', st['text'], re.I), f'{tag} {label}: a second "ours" figure: ' + (re.search(r'.{0,60}available.{0,60}', st['text'], re.I) or [''])[0])
        screen_ok(c, f'{tag} {label}', st, phone, errs, 'Cash')
        if k == 'ar':
            got = await pg.evaluate("() => (document.querySelector('.view.on > .rw-front [data-k=artotal] .rw-lv') || {}).textContent || ''")
            want = await pg.evaluate("() => acCollections('').open")
            c.ok(abs((m2f(got) or -1) - want) < 0.5, f'{tag} Receivables: open {got}, Billing\'s Collections {want}')

async def part_stmt(c, pg, uid, phone, errs, dev):
    tag = f'{uid} {dev} Financial Statements'
    if 'Financial Statements' not in (await open_reports(pg, phone, 'Financial Statements') or []): return
    pers = await pg.evaluate("() => [...document.querySelectorAll('.view.on > .rw-front [data-rwchip^=\"per:\"]')].map(b => b.textContent.trim())")
    c.ok(pers == ['This Week', 'August 2026', 'September to Date', 'Year to Date'], f'{tag}: the periods read {pers}')
    # August: a Draft, its open checks, and its Pack opens on August
    c.ok(await chip(pg, phone, 'per:last'), f'{tag}: no August chip')
    pk = await pg.evaluate("() => { const P = document.querySelector('.view.on > .rw-front .rw-pack'); return P ? P.innerText : ''; }")
    want = await pg.evaluate("() => { const L = closeChecklist('2026-08'); return [L.length, L.filter(i => !i.ok).length]; }")
    c.ok('Draft' in pk and f'{want[1]} of {want[0]}' in pk, f'{tag}: August\'s Pack does not say Draft and {want[1]} of {want[0]} checks open: "{pk[:160]}"')
    await tap(pg, pg.locator('.view.on > .rw-front [data-rwpack]').first, phone)
    t = await pg.evaluate("() => (document.getElementById('rep-print-area') || {}).innerText || ''")
    c.ok(re.search(r'August 2026', t) and 'Draft' in t, f'{tag}: the August Pack opens on "{t[:160]}"')
    st = await pg.evaluate(STATE)
    screen_ok(c, f'{tag} August Pack', st, phone, errs, 'Financial Statements')
    # Year to Date: the P&L reads companyPL; what stands behind the numbers adds to its cost to the cent
    c.ok(await chip(pg, phone, 'per:ytd'), f'{tag}: no Year to Date chip')
    c.ok(await chip(pg, phone, 'kind:pl'), f'{tag}: no Profit and Loss chip')
    S = await pg.evaluate("""() => { const F = document.querySelector('.view.on > .rw-front'); const g = (sel, k) => ((F.querySelector(`${sel} [data-k="${k}"] .rw-lv`) || {}).textContent || '');
      const P = companyPL(['2026-01-01', today()]); const M = truthManual(['2026-01-01', today()], { entityId: 'all' });
      return { pl: ['income', 'cogs', 'gross', 'oh', 'net'].map(k => g('.rw-stmt', k)), want: [P.income, P.cogsT, P.gross, P.ohT, P.net], cost: r2(P.cogsT + P.ohT),
        behind: ['bank', 'document', 'hand', 'uncoded', 'other'].map(k => g('.rw-behind', k)), total: g('.rw-behind', 'total'), income: g('.rw-behind', 'income'), collected: P.collected,
        mj: [...F.querySelectorAll('.rw-behind [data-rwmj]')].map(e => e.dataset.rwmj), manual: M.rows.map(m => m.j.id), mtext: [...F.querySelectorAll('.rw-behind .rw-mj')].map(e => e.innerText) }; }""")
    c.ok(all(m2f(a) is not None and abs(m2f(a) - b) <= 0.5 for a, b in zip(S['pl'], S['want'])), f'{tag}: the P&L reads {S["pl"]}, companyPL {S["want"]}')
    parts = [m2f(x) for x in S['behind'] if x]
    c.ok(all(re.search(r'\.\d\d$', x) for x in S['behind'] if x) and abs(sum(parts) - S['cost']) < 0.005 and abs((m2f(S['total']) or 0) - S['cost']) < 0.005,
         f'{tag}: behind the numbers {S["behind"]} add to {round(sum(parts), 2)}, the P&L\'s cost is {S["cost"]} (shown {S["total"]})')
    c.ok(abs((m2f(S['income']) or -1) - S['collected']) < 0.005, f'{tag}: client payments backed by a bank line {S["income"]}, collected {S["collected"]}')
    c.ok(set(S['manual']) <= set(S['mj']) and all(re.search(r'(Opening|Manual)', t) for t in S['mtext']), f'{tag}: entries not from a document {S["manual"]} not all flagged on the page {S["mj"]} {S["mtext"]}')
    # the Balance Sheet balances
    c.ok(await chip(pg, phone, 'kind:bs'), f'{tag}: no Balance Sheet chip')
    bs = await pg.evaluate("() => ['A', 'L', 'E'].map(k => (document.querySelector(`.view.on > .rw-front .rw-stmt [data-k='${k}'] .rw-lv`) || {}).textContent || '')")
    v = [m2f(x) for x in bs]
    c.ok(None not in v and abs(v[0] - v[1] - v[2]) < 0.01, f'{tag}: the Balance Sheet {bs} does not balance')
    # This Week: Safe to Spend is Cash's, never "available"
    c.ok(await chip(pg, phone, 'per:week'), f'{tag}: no This Week chip')
    await chip(pg, phone, 'kind:pl')
    wk = await pg.evaluate("() => ({ safe: (document.querySelector('.view.on > .rw-front .rw-stmt [data-k=safe] .rw-lv') || {}).textContent || '', want: safeToSpend().safe })")
    c.ok(abs((m2f(wk['safe']) or 1e9) - round(wk['want'])) < 1, f'{tag} This Week: Safe to Spend {wk["safe"]}, Cash {wk["want"]}')
    await tap(pg, pg.locator('.view.on > .rw-front [data-rwpack]').first, phone)
    st = await pg.evaluate(STATE)
    c.ok('Weekly Flash' in st['text'] or 'weekly flash' in st['text'].lower(), f'{tag}: This Week\'s Pack is not the Weekly Flash')
    c.ok(not re.search(r'\bavailable \$[\d,]+', st['text'], re.I), f'{tag} Weekly Flash: a second "ours" figure: ' + (re.search(r'.{0,60}available \$.{0,40}', st['text'], re.I) or [''])[0])
    screen_ok(c, f'{tag} Weekly Flash', st, phone, errs, 'Financial Statements')

async def part_builder(c, pg, uid, phone, errs, dev):
    tag = f'{uid} {dev} Report Builder'
    if 'Report Builder' not in (await open_reports(pg, phone, 'Report Builder') or []): return c.ok(False, f'{tag}: not on the menu')
    st = await pg.evaluate(STATE)
    screen_ok(c, tag, st, phone, errs, 'Report Builder')
    if uid in ('u_chen', 'u_sarah'):
        c.ok(st['view'] == 'dashboard', f'{tag}: opens {st["view"]}, want their pinned reports')
        return
    ch = await pg.evaluate("() => [...document.querySelectorAll('.view.on > .rw-front [data-rwchip^=\"builder:\"]')].map(b => b.textContent.trim())")
    c.ok(ch == ['Saved', 'Standard', 'Pinned'], f'{tag}: chips {ch}')
    n = await pg.evaluate("() => ({ rows: [...document.querySelectorAll('.view.on #rep-print-area tr[data-ssopen]')].filter(r => r.getClientRects().length).length, list: searchList().length })")
    c.ok(n['rows'] == n['list'] and n['list'] >= 9, f'{tag} Saved: {n["rows"]} rows on screen, {n["list"]} saved reports')
    due = await pg.evaluate("""() => { const s = searchList().find(x => x.name === 'Invoices due this week'); if (!s) return null;
      const d = parse(today()); const end = iso(addDays(d, 6 - ((d.getDay() + 6) % 7)));
      return { got: searchRun(s).rows.map(r => r.number).sort(), want: REP_DS.invoices.rows().filter(r => +r.balance > 0.005 && r.due && r.due <= end).map(r => r.number).sort() }; }""")
    c.ok(due and due['got'] == due['want'], f'{tag}: "Invoices due this week" lists {due and due["got"]}, want {due and due["want"]}')
    c.ok(await chip(pg, phone, 'builder:standard'), f'{tag}: no Standard chip')
    std = await pg.evaluate("() => [...document.querySelectorAll('.view.on > .rw-front .rw-lrow[data-rwopen]')].map(r => (r.querySelector('.rw-lk b') || {}).textContent || '')")
    for name in ('Work in Progress Schedule', 'Client Statement'):
        c.ok(name in std, f'{tag} Standard: no {name} ({std})')
    if 'Work in Progress Schedule' in std:
        await tap(pg, pg.locator('.view.on > .rw-front .rw-lrow[data-rwopen]').nth(std.index('Work in Progress Schedule')), phone)
        st = await pg.evaluate("() => ({ page: (document.querySelector('.view.on > .rw-front') || {dataset: {}}).dataset.rwpage, wip: (document.querySelector('.view.on > .rw-front [data-rwchip=\"jobs:wip\"]') || {}).getAttribute?.('aria-pressed'), repTab })")
        c.ok(st['page'] == 'jobs' and st['wip'] == 'true', f'{tag}: the WIP Schedule opens {st}, want Job Profitability, Work in Progress')
        await open_reports(pg, phone, 'Report Builder')
    # Start From: every queryable table
    S = await pg.evaluate("() => { const eq = Object.keys(EQ_TABLES); const got = new Set([...document.querySelectorAll('.view.on > .rw-front [data-rwsrc]')].flatMap(b => (b.dataset.rweq || '').split(' ').filter(Boolean))); return { missing: eq.filter(k => !got.has(k)), n: eq.length }; }")
    c.ok(not S['missing'], f'{tag} Start From: {len(S["missing"])} of {S["n"]} EQ_TABLES entities not reachable {S["missing"][:12]}')
    if not phone:
        b = pg.locator('.view.on > .rw-front [data-rwsrc][data-rweq~="tasks"]').first
        if await b.count():
            if not await b.is_visible():   # every other table is one tap down
                await tap(pg, pg.locator('.view.on > .rw-front .rw-more summary').first, phone)
            n0 = await pg.evaluate("() => searchList().length")
            await tap(pg, b, phone)
            r = await pg.evaluate("() => { const s = searchList().find(x => x.id === ssOpen); const t = [...document.querySelectorAll('.toast, #toast, .toasts > *')].map(e => e.innerText).join(' | '); return s && { ds: s.ds, rows: searchRun(s).rows.length, n: searchList().length, toast: t, open: !!document.querySelector('.toast a, #toast a, .toasts a, .toast button, #toast button') }; }")
            c.ok(r and r['ds'] == 'eq_tasks' and r['rows'] > 0 and r['n'] == n0 + 1, f'{tag}: Start From Tasks made {r}')
            c.ok(r and 'New report' in r['toast'] and r['open'], f'{tag}: no toast with an Open link: {r and r["toast"]}')
            await pg.evaluate("() => { const s = searchList().find(x => x.id === ssOpen); if (s) DB.searches = DB.searches.filter(x => x !== s); ssOpen = null; save(); render(); }")
    del errs[:]

async def part_forward(c, pg, uid, phone, errs, dev):
    tag = f'{uid} {dev} forward'
    for t, page, chip_k in (('wip', 'jobs', 'jobs:wip'), ('ar', 'cash', 'cash:ar'), ('pack', 'stmt', None), ('searches', 'builder', 'builder:saved'), ('funds', 'cash', 'cash:funds')):
        await pg.evaluate("t => { repTab = t; setView('reports'); }", t)
        await pg.wait_for_timeout(250)
        st = await pg.evaluate("k => ({ page: (document.querySelector('.view.on > .rw-front') || {dataset: {}}).dataset.rwpage || '', on: k ? (document.querySelector(`.view.on > .rw-front [data-rwchip='${k}']`) || {getAttribute: () => ''}).getAttribute('aria-pressed') : 'true', view })", chip_k)
        c.ok(st['view'] == 'reports' and st['page'] == page and st['on'] == 'true', f'{tag}: the old {t} lands on {st}, want {page} {chip_k}')
    # Billing's Client Funds tab and the Dashboard
    await pg.evaluate("() => { billTab = 'funds'; setView('billing'); }"); await pg.wait_for_timeout(250)
    st = await pg.evaluate(STATE)
    c.ok(st['view'] == 'reports' and st['page'] == 'cash' and not re.search(r'available cash \(ours\)', st['text'], re.I), f'{tag}: Billing\'s Client Funds lands on {st["view"]} {st["page"]}')
    await pg.evaluate("() => setView('dashboard')"); await pg.wait_for_timeout(250)
    st = await pg.evaluate(STATE)
    c.ok(st['heading'] == 'Report Builder' and st['page'] == 'builder', f'{tag}: the Dashboard lands on "{st["heading"]}" {st["page"]}')
    screen_ok(c, f'{tag} Dashboard', st, phone, errs, 'Report Builder')

READ_JS = """async () => { const sleep = ms => new Promise(r => setTimeout(r, ms));
  const walk = async () => { for (const pg of ['jobs', 'cash', 'stmt', 'builder']) { rwGo(pg); setView('reports'); await sleep(80);
      for (const b of [...document.querySelectorAll('.view.on > .rw-front [data-rwchip]')].map(b => b.dataset.rwchip)) { if (/^(page|builder:pinned)/.test(b)) continue;
        const [g, k] = b.split(':'); rwChipGo(g, k); await sleep(60); } } };
  // the boot's own jobs (the improvement loop's first run stamps company.loopLast) settle first: they are not a read
  for (let i = 0; i < 40 && !(DB.company || {}).loopLast; i++) await sleep(200);
  await walk();
  const before = JSON.stringify(DB);
  await walk();
  const after = JSON.stringify(DB);
  let at = -1; if (before !== after) at = [...before].findIndex((ch, i) => ch !== after[i]);
  return before === after ? '' : before.slice(Math.max(0, at - 100), at + 100); }"""

async def part_read(c, pg, uid, phone, errs, dev):
    d = await pg.evaluate(READ_JS)
    c.ok(d == '', f'{uid} {dev}: reading the Reports pages changed the data near: {d}')

PARTS = {'menu': part_menu, 'jobs': part_jobs, 'cash': part_cash, 'stmt': part_stmt, 'builder': part_builder, 'forward': part_forward, 'read': part_read}
WHO = {'menu': list(MENU), 'jobs': PERSONS, 'cash': PERSONS, 'stmt': PERSONS, 'builder': PERSONS + ['u_chen', 'u_sarah'], 'forward': ['u_owner', 'u_controller'], 'read': ['u_owner', 'u_controller']}

async def main():
    args = sys.argv[1:]
    users = args[args.index('--user') + 1].split(',') if '--user' in args else None
    parts = [a for a in args if a in PARTS] or list(PARTS)
    devs = [False] if '--desktop' in args else [True] if '--phone' in args else [False, True]
    c = Checks()
    async with async_playwright() as p:
        for phone in devs:
            dev = 'phone' if phone else 'desktop'
            for part in parts:
                for uid in WHO[part]:
                    if users and uid not in users: continue
                    b, pg, errs = await open_app(p, phone)
                    await sign_in(pg, uid)
                    try:
                        await PARTS[part](c, pg, uid, phone, errs, dev)
                    except Exception as e:
                        c.ok(False, f'{uid} {dev} {part}: {str(e).splitlines()[0][:200]}')
                    await b.close()
    return c.done()

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
