"""truthpct (BACKLOG §1.2 and §1.4 item 5): one completion number, an EAC that moves, portal truth.

Every target figure in the backlog is asserted here, read from the app (and from the rendered screens where
the backlog names a screen). Each section starts from a fresh boot so the seeded demo data is the baseline.

  python3 truthpct_test.py            all sections
  python3 truthpct_test.py fin pct    only the named sections (fin, pct, screens, ask, pay, portal, thread, studio)
"""
import asyncio, re, sys
from harness import *

ONLY = set(sys.argv[1:])
want = lambda s: not ONLY or s in ONLY
J121 = "DB.projects.find(p => /121 State/.test(p.project.name))"


async def fresh(p, uid='u_owner', phone=False):
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, uid)
    return b, pg, errs


async def text(pg, v):
    return await pg.evaluate("v => { const e = document.getElementById('v-' + v); return e ? e.innerText : '' }", v)


async def ask(pg, q):
    return await pg.evaluate("""async q => { let a = paAsk(q); if (a && a.then) a = await a;
        return [a.headline || '', a.note || '', (a.work || []).map(w => typeof w === 'string' ? w : (w.t || w.text || JSON.stringify(w))).join('\\n')].join('\\n') }""", q)


async def sec_fin(p, c):
    """EAC = actual + committed + cost to complete, by estimate and approved-CO line (BACKLOG §1.2)."""
    b, pg, errs = await fresh(p)
    r = await pg.evaluate(f"""() => {{ const p = {J121}, J = jobFin(p), L = J.eacLines || [];
        const line = n => L.find(x => x.name.startsWith(n)) || {{}};
        const other = DB.projects.filter(x => x !== p).map(x => {{ const K = jobFin(x); return [x.project.name, K.eac, K.earned] }});
        return {{ eac: J.eac, gp: J.estGPPct, earned: J.earned, ou: J.overUnder, backlog: J.backlog, pct: J.pct,
          win: line('Windows').over, mill: line('Millwork').over, millDep: line('Millwork').deposit,
          ytd: companyPL(['2026-01-01', today()]).income, aug: companyPL(['2026-08-01', '2026-08-31']).income,
          over: DB.projects.map(wipRow).reduce((a, w) => a + w.over, 0), other: other,
          aug31: jobFin(p, ['', '2026-08-31']).eac }} }}""")
    c.ok(r['eac'] == 388887.5, f"121 State EAC {r['eac']} (target $388,887.50, was $384,087.50)")
    c.ok(r['win'] == 3800 and r['mill'] == 1000, f"line overruns Windows {r['win']} (+3,800) Millwork {r['mill']} (+1,000)")
    c.ok(r['millDep'] == 38000, f"Millwork deposit read {r['millDep']} (38,000)")
    c.ok(r['gp'] == 20.83, f"margin at completion {r['gp']}% (target 20.83%, was 21.81%)")
    c.ok(r['earned'] == 122625.79, f"121 State earned {r['earned']} (target $122,625.79, was $124,158.26)")
    c.ok(r['ou'] == 131057.72, f"121 State over-billing {r['ou']} (target $131,057.72, was $129,525.25)")
    c.ok(r['backlog'] == 368574.21, f"121 State backlog {r['backlog']} (target $368,574.21, was $367,041.74)")
    c.ok(abs(r['ytd'] - (144291.71 - 1532.47)) < 0.01, f"YTD revenue {r['ytd']} (target 144,291.71 - 1,532.47 = 142,759.24)")
    c.ok(r['aug'] == 135175.13, f"August revenue {r['aug']} unchanged (135,175.13)")
    c.ok(r['aug31'] == 384087.5, f"the August 31 read keeps the estimate it was reported on: {r['aug31']}")
    c.ok(abs(r['over'] - 156274.27) < 0.01, f"firm WIP over-billing {r['over']} (154,741.80 + 1,532.47)")
    c.ok(r['other'] == [['45 Cranberry St — design', 16104, 18645.45], ['206 Lenox — 3rd floor turnover', 0, 0],
                        ['140 Prospect Place — design', 124670, 1488]], f"other jobs unchanged {r['other']}")
    # A short-pay counts only the amount approved: Approve PO Amount on WW-2026-118 ($29,700; $3,800 disputed)
    r = await pg.evaluate(f"""() => {{ const b = DB.bills.find(x => x.number === 'WW-2026-118');
        pay3ShortPay(b, 29700, 'Invoice is for 10 units; PO was 9');
        const J = jobFin({J121}); return {{ eac: J.eac, win: (J.eacLines.find(x => x.name.startsWith('Windows')) || {{}}).over, held: b.short && b.short.held }} }}""")
    c.ok(r['held'] == 3800 and r['eac'] == 385087.5 and r['win'] == 0,
         f"short-paid WW-2026-118 counts only $29,700: EAC {r['eac']} (385,087.50), Windows over {r['win']}, held {r['held']}")
    # A PM-reviewed cost to complete wins
    r = await pg.evaluate(f"""() => {{ const p = {J121}; p.ctc = 300000; p.ctcReviewed = '2026-09-03';
        const J = jobFin(p); const out = {{ eac: J.eac, actual: J.actual, lines: !!J.eacFromLines }}; delete p.ctc; delete p.ctcReviewed; return out }}""")
    c.ok(abs(r['eac'] - (r['actual'] + 300000)) < 0.01 and not r['lines'], f"PM-reviewed CTC wins: EAC {r['eac']} = actual {r['actual']} + 300,000")
    # No recursion: lineFin (overhead burden reads the P&L, which reads jobFin) and jobFin read each other safely
    r = await pg.evaluate(f"""() => {{ const p = {J121}, J = jobFin(p); const k = J.eacLines[0].key;
        const f = lineFin(k); return {{ ok: !!f && typeof f.trueMargin === 'number', busy: jobFinEacBusy, pl: companyPL(['2026-01-01', today()]).income }} }}""")
    c.ok(r['ok'] and r['busy'] is False, f"lineFin with burden and jobFin by line do not recurse ({r})")
    c.ok(not errs, f"fin: page errors {errs[:3]}")
    await b.close()


async def sec_pct(p, c):
    b, pg, errs = await fresh(p)
    r = await pg.evaluate(f"""() => {{ const p = {J121}, d = tpJobPctDetail(p);
        const win = p.tasks.find(t => t.id === 'win'), ext = p.tasks.find(t => t.id === 'ext');
        const line = n => d.lines.find(r => r.x.sv.desc.startsWith(n)) || {{}};
        return {{ pct: tpJobPct(p), win: (tpTaskLine(p, win) || {{sv: {{}}}}).sv.desc, ext: (tpTaskLine(p, ext) || {{sv: {{}}}}).sv.desc,
          wl: line('Windows').pct, permits: [line('Permits').basis, line('Permits').pct], mill: line('Millwork').basis,
          cost: Math.round(100 * jobFin(p).pct) }} }}""")
    c.ok(r['pct'] == 14, f"tpJobPct(121 State) {r['pct']}% (target 14%)")
    c.ok(r['cost'] == 25, f"the cost basis stays cost-to-cost: {r['cost']}% (25%)")
    c.ok(str(r['win']).startswith('Windows'), f"task 'Windows & interior trim' measures the Windows line: {r['win']}")
    c.ok(str(r['ext']).startswith('Exterior'), f"task 'Exterior – scaffold…' measures the Exterior line: {r['ext']}")
    c.ok(r['wl'] == 20, f"Windows line measured {r['wl']}% (20%)")
    c.ok(r['permits'] == ['cost', 15], f"a line with no task is cost-to-cost: Permits {r['permits']}")
    c.ok(not errs, f"pct: page errors {errs[:3]}")
    await b.close()


async def sec_screens(p, c):
    """Every surface that printed cost-to-cost as % complete shows tpJobPct or says Cost Basis %."""
    b, pg, errs = await fresh(p)
    await go(pg, 'ovjobs'); t = await text(pg, 'ovjobs')
    hdr = (re.search(r'PROJECT\t[^\n]*', t) or re.search(r'Project\t[^\n]*', t))
    hdr = hdr.group(0) if hdr else ''
    c.ok(re.search(r'% COMPLETE', hdr, re.I) and re.search(r'\bEAC\b', hdr), f"Projects table has % Complete and EAC columns: {hdr[:200]}")
    row = re.search(r'\n121 State Street\t[^\n]*', t)
    row = row.group(0) if row else ''
    c.ok('\t14%\t' in row and '$388,888' in row, f"Projects row 121 State: 14% and EAC $388,888: {row[:220]}")
    await go(pg, 'dashboard'); t = await text(pg, 'dashboard')
    c.ok(re.search(r'121 State Street · bid 21\.81% → forecast 20\.83% \([^)]*\) · 14% complete', t),
         "Dashboard Margin at Completion: 121 State bid 21.81% -> forecast 20.83% · 14% complete")
    await pg.evaluate("() => { view = 'reports'; repTab = 'portfolio'; render() }"); await pg.wait_for_timeout(200)
    t = await text(pg, 'reports')
    m = re.search(r'\n121 State Street\t(?:[^\t]*\t){8}\s*(\$[\d,]+)[^\n]*\n[^\n]*\n\s*(\d+)%', t)
    c.ok(m and m.group(1) == '$388,888' and m.group(2) == '14', f"Portfolio: Proj. Cost and % Complete {m.groups() if m else None}")
    await pg.evaluate("() => { view = 'reports'; repTab = 'wip'; wipTab = 'schedule'; render() }"); await pg.wait_for_timeout(200)
    t = await text(pg, 'reports')
    m = re.search(r'\n121 State Street\n[^\n]*\n\t[^\t]*\t[^\t]*\t(\d+)%\n(\d+)% cost basis', t)
    c.ok(m and m.groups() == ('14', '25'), f"WIP Schedule: % Complete 14% with 25% cost basis {m.groups() if m else None}")
    c.ok('COST BASIS %' in t.upper(), "WIP Schedule labels the revenue basis Cost Basis %")
    c.ok('Variance Flag: Measured on Site vs Cost Basis'.upper() in t.upper(), "WIP has the Variance Flag: Measured on Site vs Cost Basis table")
    m = re.search(r'\n121 State Street\t(\d+)%\t(\d+)%', t)
    c.ok(m and m.groups() == ('14', '25'), f"Variance flag row: measured 14% vs cost basis 25% {m.groups() if m else None}")
    await pg.evaluate("() => { view = 'reports'; repTab = 'pack'; render() }"); await pg.wait_for_timeout(300)
    t = await text(pg, 'reports')
    m = re.search(r'\n121 State Street\t[^\t]*\t(\d+)%\n(\d+)% cost basis', t)
    c.ok(m and m.groups() == ('14', '25'), f"Pack WIP & Profit Fade: 14% with 25% cost basis {m.groups() if m else None}")
    # nothing on these screens prints the cost ratio as "N% complete" for 121 State
    bad = []
    for v in ('dashboard', 'ovjobs', 'reports', 'home', 'cos'):
        await go(pg, v); t = await text(pg, v)
        bad += [v + ': ' + x for x in re.findall(r'121 State Street[^\n]{0,160}?\b25% complete[^\n]{0,40}', t)]
    c.ok(not bad, f"no screen prints 121 State's cost ratio as % complete: {bad[:3]}")
    c.ok(not errs, f"screens: page errors {errs[:3]}")
    await b.close()


async def sec_ask(p, c):
    for uid in ('u_owner', 'u_controller'):
        b, pg, errs = await fresh(p, uid)
        a = await ask(pg, 'how far along is 121 State Street')
        c.ok(re.match(r'121 State Street is 14% complete', a), f"{uid} Ask how far along: {a[:90]}")
        a = await ask(pg, 'which job is bleeding?')
        c.ok('121 State Street — health' in a and '14% complete' in a and '25% complete' not in a, f"{uid} Ask which job is bleeding: {a[:200]}")
        a = await ask(pg, 'what is our backlog')
        c.ok('$582,941' in a and '121 State Street · $368,574 backlog' in a and '14% complete' in a and '25% complete' not in a, f"{uid} Ask backlog: {a[:240]}")
        a = await ask(pg, 'what is the margin on 121 State Street')
        c.ok(a.startswith('20.83% estimated gross margin') and '25% through its estimated cost (cost-to-cost)' in a and 'complete cost-to-cost' not in a,
             f"{uid} Ask margin: {a[:300]}")
        a = await ask(pg, 'margin by job')
        c.ok('121 State Street · 20.83%' in a and '14% complete' in a and '25% complete' not in a, f"{uid} Ask margin by job: {a[:300]}")
        a = await ask(pg, 'what is the EAC on 121 State Street')
        c.ok(a.startswith('Estimate at completion on 121 State Street is $388,888'), f"{uid} Ask EAC: {a[:120]}")
        a = await ask(pg, 'how is 121 State doing')
        c.ok('25% through its estimated cost (cost-to-cost)' in a and '14% complete' in a, f"{uid} Ask job profile: {a[:400]}")
        # the cost ratio is never printed as "% complete"
        leaks = []
        for q in ('how far along is 121 State Street', 'which job is bleeding?', 'what is our backlog', 'margin by job',
                  'what is the margin on 121 State Street', 'how is 121 State doing', 'what is the EAC on 121 State Street',
                  'is any job over budget', 'how much are we over-billed', 'what is the WIP'):
            a = await ask(pg, q)
            if re.search(r'\b25% complete\b', a): leaks.append(q)
        c.ok(not leaks, f"{uid}: Ask never prints the cost ratio as % complete: {leaks}")
        c.ok(not errs, f"ask {uid}: page errors {errs[:3]}")
        await b.close()


async def sec_pay(p, c):
    """The measured pay application: tasks mapped to SOV lines, measured % wins, cost never lifts a measured line."""
    b, pg, errs = await fresh(p, 'u_billing')
    r = await pg.evaluate(f"""() => {{ const p = {J121}; const R = pgRows(p.id);
        const row = n => R.find(r => r.sv.desc.startsWith(n));
        const w = row('Windows'), m = row('Millwork'), pm = row('Permits');
        return {{ win: [w.pr.pct, w.pr.basis, w.pr.period], mill: m.findings.map(f => f.msg),
          cost: R.filter(r => r.pr.basis === 'cost').map(r => r.sv.desc), confirm: R.filter(r => r.findings.some(f => f.kind === 'confirm')).map(r => r.sv.desc),
          frame: row('Framing').pr.period, elec: row('Electrical').pr.period }} }}""")
    c.ok(r['win'][0] == 20 and r['win'][1] == 'schedule' and r['win'][2] == 0, f"Windows proposes 20% measured, nothing this period (not 100% from cost): {r['win']}")
    c.ok(r['frame'] == 27.08 and r['elec'] == 3.33, f"Framing and Electrical keep their measured proposals: {r['frame']}, {r['elec']}")
    c.ok(any('$38,000 of it a deposit, not progress — heading over by about $1,000' in x for x in r['mill']) and not any('35,768' in x for x in r['mill']),
         f"Millwork finding reads the deposit and the line EAC: {r['mill']}")
    c.ok(r['cost'] and sorted(r['cost']) == sorted(r['confirm']), f"every cost-only line carries a confirm finding: cost {r['cost']} confirm {r['confirm']}")
    await pg.evaluate("() => { view = 'billing'; billTab = 'progress'; render() }"); await pg.wait_for_timeout(400)
    t = await text(pg, 'billing')
    c.ok('No Field Measure' in t, "cost-only lines show the No Field Measure pill")
    hdr = await pg.evaluate("() => [...document.querySelectorAll('#v-billing th')].map(x => x.innerText.trim())")
    c.ok(any(re.search(r'Materials Stored', h, re.I) for h in hdr), f"pay application has a Materials Stored column (G703 F): {hdr}")
    c.ok('earned · 25% complete' not in t and 'cost basis' in t.lower(), "the pay application header calls the WIP figure a cost basis, not % complete")
    await pg.click('#pg-apply[data-blheld]'); await pg.wait_for_timeout(300)
    await pg.click('#mbm-ok'); await pg.wait_for_timeout(600)
    toast = await pg.evaluate("() => (document.getElementById('toast') || {}).innerText || ''")
    c.ok('it totals $11,386' in toast, f"Fill the Draft Anyway totals $11,386 (was $29,449): {toast[:160]}")
    c.ok(not errs, f"pay: page errors {errs[:3]}")
    await b.close()


CLIENT_LEAK = re.compile(r'\$124,158|\$122,626|\bearned\b|work completed|daily log|last update from|\b25% complete', re.I)


async def sec_portal(p, c):
    """The client never sees internal earned revenue; the Overview shows progress and the last 3 shared photos."""
    # the PM shares a photo: the app asks for the caption the client reads
    b, pg, errs = await fresh(p, 'u_alan')
    pid = await pg.evaluate(f"() => {J121}.id")
    r = await pg.evaluate("""pid => { const x = DB.photos.find(x => x.projectId === pid && !x.share); window.__tpPh = x.id;
        pstShare(x, true); const m = document.getElementById('mbm'); return { modal: m ? m.innerText : '', shared: !!x.share } }""", pid)
    c.ok('Caption the Client Reads' in r['modal'] and not r['shared'], f"sharing a photo asks the PM for the client's caption first: {r['modal'][:80]}")
    await pg.fill('#mbm [data-f="cap"]', 'Rear windows trimmed out')
    await pg.click('#mbm-ok'); await pg.wait_for_timeout(300)
    r = await pg.evaluate("() => { const x = DB.photos.find(x => x.id === window.__tpPh); return [x.share, x.clientCaption] }")
    c.ok(r == [True, 'Rear windows trimmed out'], f"shared with the PM's caption: {r}")
    await pg.evaluate("() => saveNow ? saveNow() : save()"); await pg.wait_for_timeout(300)
    await sign_in(pg, 'u_klein')
    views = await pg.evaluate("ROLE_VIEWS[role()]")
    leaks, texts = [], {}
    for v in views:
        await go(pg, v); await pg.wait_for_timeout(150)
        texts[v] = await text(pg, v)
        for m in CLIENT_LEAK.finditer(texts[v]): leaks.append(f"{v}: {texts[v][max(0, m.start() - 40):m.end() + 30]!r}")
    c.ok(not leaks, f"no client view shows internal earned revenue, a daily-log tag or the stale update line: {leaks[:4]}")
    t = texts.get('client', '')
    c.ok('Completed to Date $253,684 · 51.65% certified on INV-2026-038 · 14% measured on site' in t,
         "client Overview card: Completed to Date $253,684 · 51.65% certified on INV-2026-038 · 14% measured on site")
    n = await pg.evaluate("() => { view = 'client'; render(); return document.querySelectorAll('#tp-clprog .pst-tile').length }")
    c.ok(n == 3, f"client Overview shows the last 3 shared photos: {n}")
    cap = await pg.evaluate("() => [...document.querySelectorAll('#tp-clprog .pst-tile')].map(x => x.innerText).join(' | ')")
    c.ok('Rear windows trimmed out' in cap, f"the client reads the PM's caption: {cap}")
    await pg.click('#tp-clprog .pst-tile'); await pg.wait_for_timeout(300)
    lb = await pg.evaluate("() => (document.getElementById('pst-lb') || {}).innerText || ''")
    c.ok(lb and not re.search(r'daily log|progress\b.*\n.*angel|\bAngel\b|Windows & interior trim', lb, re.I), f"the client's photo viewer carries no internal tag, task or crew name: {lb[:160]!r}")
    await pg.evaluate("() => document.getElementById('pst-lb') && document.getElementById('pst-lb').remove()")
    # the client's Ask and the emails a client receives
    out = []
    for q in ('how far along is my project', 'how much is done', 'what have we paid', 'what is the schedule'):
        a = await ask(pg, q)
        if CLIENT_LEAK.search(a): out.append((q, a[:120]))
    c.ok(not out, f"the client's Ask carries no earned revenue: {out}")
    mails = await pg.evaluate("""() => { const c = DB.clients.find(x => /Klein/.test(x.name));
        return [...c.invoices, ...c.changeOrders].map(d => crDocEmail(c, d).body).join('\\n') }""")
    c.ok(not CLIENT_LEAK.search(mails), "client document emails carry no earned revenue")
    nsh = await pg.evaluate(f"() => pstRows({{ projectId: {J121}.id, shared: true }}).length")
    m = re.search(r'Photos of the Job\n\s*(\d+)', texts.get('clacct', ''), re.I)
    c.ok(m and int(m.group(1)) == nsh, f"the Account page counts the photos shared with the client ({nsh}): {m.group(0) if m else None}")
    # the other client portal (140 Prospect)
    await sign_in(pg, 'u_cambri')
    leaks = []
    for v in await pg.evaluate("ROLE_VIEWS[role()]"):
        await go(pg, v); t = await text(pg, v)
        for m in CLIENT_LEAK.finditer(t): leaks.append(f"{v}: {t[max(0, m.start() - 40):m.end() + 30]!r}")
    c.ok(not leaks, f"140 Prospect portal: no internal earned revenue or tags: {leaks[:3]}")
    c.ok(not errs, f"portal: page errors {errs[:3]}")
    await b.close()


THREAD = """async () => {
  const c = DB.clients.find(x => /Klein/.test(x.name)), p = DB.projects.find(x => /121 State/.test(x.project.name));
  setCurrent ? setCurrent(p.id) : (S = p); clientOpen = c.id;
  const est = c.estimates.find(e => e.status === 'converted'), fl = est.lines.find(l => l.code === '03');
  const mk = (rate, days, prev) => {
    let d;
    if (!prev) {
      d = newDoc(c, 'co', { fields: { title: 'Extra blocking for the garden wall cabinets', projectId: p.id, scheduleDays: days,
        lines: [{ id: uid('l'), item: fl.item || 'Framing, blocking & rough carpentry', desc: 'Extra blocking', qty: 1, unit: 'ls', rate: rate, taxable: false }] } });
      d.taskId = 'frame';
    } else { lkRevise(c, prev); d = c.changeOrders.find(x => x.id === docOpen.id); d.lines[0].rate = rate; d.scheduleDays = days; }
    return d;
  };
  const approve = async d => { d.status = 'sent'; d.sentOn = today(); const r = docAction(c, d, 'approve'); if (r && r.then) await r;
    await new Promise(r => setTimeout(r, 80)); document.querySelectorAll('#mbm-ok').forEach(b => b.click()); await new Promise(r => setTimeout(r, 80)); };
  const d0 = mk(6400, 5); await approve(d0);
  const d1 = mk(7200, 7, d0); await approve(d1);
  const d2 = mk(5000, 3, d1); await approve(d2);
  docOpen = null; view = 'dash'; render();
  return { d0: d0.number, d1: d1.number, d2: d2.number, give: d2.czGive };
}"""


async def sec_thread(p, c):
    """The ops thread on 121 State: CO 5 days, R1 7 days, R2 3 days (4 given back, not pulled in)."""
    b, pg, errs = await fresh(p, 'u_alan')
    r = await pg.evaluate(THREAD)
    c.ok(r['give'] and r['give']['days'] == 4, f"R2 gives back 4 working days on Framing: {r}")
    await pg.wait_for_timeout(200)
    tile = await pg.evaluate("() => { const t = document.querySelector('#kpis .gl[data-gl=\"sched\"]'); return t ? t.innerText.replace(/\\n/g, ' | ') : '' }")
    want = f"4 working days late · 4 days still on Framing & blocking – 3rd floor from {r['d1']} — Pull In"
    c.ok(want in tile, f"Today forecast tile: {want!r} in {tile!r}")
    await pg.click('#kpis .gl[data-gl="sched"]'); await pg.wait_for_timeout(300)
    m = await pg.evaluate("() => { const m = document.getElementById('mbm'); return m && getComputedStyle(m).display !== 'none' ? m.innerText.trim() : '' }")
    c.ok(m.lower().startswith('pull in'), f"clicking the tile opens Pull In: {m[:60]!r}")
    await pg.evaluate("() => { const x = document.getElementById('mbm-cancel'); x && document.getElementById('mbm').querySelector('.x, [data-close]') }")
    await pg.evaluate("() => { const m = document.getElementById('mbm'); if (m) { m.classList.remove('on'); m.style.display = ''; } view = 'sched'; render() }")
    await pg.wait_for_timeout(200)
    card = await pg.evaluate("() => { const t = document.querySelector('#track-cards .ops-fc'); return t ? t.innerText.replace(/\\n/g, ' | ') : '' }")
    c.ok(want in card and 'Pull In' in card, f"Schedule forecast card names the cause: {card!r}")
    # superseded copies are marked in the task editor's Linked list
    await pg.evaluate("() => { view = 'sched'; render(); openEditor('task', 'frame') }"); await pg.wait_for_timeout(300)
    linked = await pg.evaluate("() => [...document.querySelectorAll('#d-body .ops-chip')].filter(a => /CO-/.test(a.innerText)).map(a => a.innerText.replace(/\\n/g, ' '))")
    sup = [x for x in linked if 'superseded by' in x]
    live = [x for x in linked if r['d2'] in x and 'superseded' not in x]
    c.ok(len(sup) == 2 and len(live) == 1, f"the task editor lists the CO and both revisions, the two superseded copies marked: {linked}")
    if ONLY: print('   linked:', linked)
    await pg.evaluate("() => { typeof closeEditor === 'function' && closeEditor() }")
    # Pull In from the card, a no-show slip on Framing (+5), Publish
    await pg.evaluate("""() => { view = 'sched'; render(); const b = document.querySelector('#track-cards [data-tppull]'); b && b.click() }"""); await pg.wait_for_timeout(300)
    await pg.click('#mbm-ok'); await pg.wait_for_timeout(300)
    r2 = await pg.evaluate("""() => { const p = S, t = p.tasks.find(x => x.id === 'frame'), was = { start: t.start, end: t.end };
        t.end = addWork(t.end, 5, t.weekendOk); t._moveReason = 'A trade could not be on site when planned'; t._moveReasonKey = 'noshow';
        pushDependents(t.id, []); recordMove(t, was, 'edit'); opsPublish(p, 'Framing slipped a week: the framer did not show.'); save();
        return { pulled: (p.tasks.find(x => x.id === 'frame').history || []).length } }""")
    await sign_in(pg, 'u_klein')
    await go(pg, 'sched'); await pg.wait_for_timeout(200)
    t = await text(pg, 'sched')
    m = re.search(r'Your change order (CO-\d{4}-\d{3}) \(as revised, R2\)\n?\s*\+?(\d+)', t)
    c.ok(m and m.group(1) == r['d0'] and m.group(2) == '3', f"client What Changed nets the revisions: 'Your change order {r['d0']} (as revised, R2) +3' in {t[t.find('What Changed'):t.find('What Changed') + 400]!r}")
    c.ok(not re.search(r'Your change order CO-\d{4}-\d{3}-R\d', t), "no client row names a superseded copy")
    ms = t[t.find('Milestones'):t.find('Milestones') + 300]
    c.ok('Ahead' not in ms and re.search(r'Upcoming|Working Days? Past Agreement', ms), f"milestone pills are Done / Upcoming / Past Agreement, never Ahead: {ms!r}")
    c.ok(re.search(r'\d+ Working Days? Past Agreement', ms, re.I), f"a milestone past the agreed date says how many working days: {ms!r}")
    if ONLY: print('   client schedule:', t[t.find('What Changed'):t.find('What Changed') + 700])
    c.ok(not errs, f"thread: page errors {errs[:3]}")
    await b.close()


async def sec_studio(p, c):
    """45 Cranberry: mark Design development done, reload, and CDs are current; DD reads Done."""
    b, pg, errs = await fresh(p, 'u_owner')
    r = await pg.evaluate("""() => { const p = DB.projects.find(x => /Cranberry/.test(x.project.name));
        const t = p.tasks.find(x => x.phaseLine && /Design development/i.test(x.name)); setCurrent ? setCurrent(p.id) : (S = p);
        prgSet(p, t, { pct: 100, note: 'DD set issued' }); save(); typeof saveNow === 'function' && saveNow(); return { id: t.id, st: t.status } }""")
    c.ok(r['st'] == 'done', f"Design development marked done: {r}")
    await pg.wait_for_timeout(400)
    await pg.reload(); await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
    await sign_in(pg, 'u_owner')
    st = await pg.evaluate("""() => { const p = DB.projects.find(x => /Cranberry/.test(x.project.name));
        return (p.tasks.find(x => x.phaseLine && /Design development/i.test(x.name)) || {}).status }""")
    c.ok(st == 'done', f"after reload Design development is still done: {st}")
    await go(pg, 'studio'); t = await pg.evaluate("() => (document.querySelector('.view.on') || {}).innerText || ''")
    row = re.search(r'45 Cranberry St — design\t[^\t]*\t([^\t]*)\t', t)
    c.ok(row and row.group(1).startswith('Construction documents'), f"Studio list: the current phase is Construction documents: {row.group(1) if row else None}")
    await pg.evaluate("() => { setCurrent(DB.projects.find(x => /Cranberry/.test(x.project.name)).id); view = 'sboard'; render() }"); await pg.wait_for_timeout(200)
    t = await text(pg, 'sboard')
    strip = t[t.find('Where It Stands'):t.find('Where It Stands') + 200]
    c.ok(re.search(r'DESIGN DEV\s*Done', strip, re.I) and re.search(r'CDS\s*Current', strip, re.I), f"board strip: DD Done, CDs Current: {strip!r}")
    h = await pg.evaluate("() => phaseStrip(DB.projects.find(x => /Cranberry/.test(x.project.name)))")
    c.ok(re.search(r'Design dev</div>.*?<span class="pill ok">Done</span>', h) and re.search(r'Construction doc[^<]*</div>.*?<span class="pill info">Current</span>', h),
         "phase strip: DD Done, CDs Current")
    c.ok(not errs, f"studio: page errors {errs[:3]}")
    await b.close()


async def main():
    c = Checks()
    async with async_playwright() as p:
        for name, fn in (('fin', sec_fin), ('pct', sec_pct), ('screens', sec_screens), ('ask', sec_ask), ('pay', sec_pay),
                         ('portal', sec_portal), ('thread', sec_thread), ('studio', sec_studio)):
            if want(name):
                print('--', name)
                await fn(p, c)
    sys.exit(c.done())

if __name__ == "__main__": asyncio.run(main())
