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


async def main():
    c = Checks()
    async with async_playwright() as p:
        for name, fn in (('fin', sec_fin), ('pct', sec_pct), ('screens', sec_screens), ('ask', sec_ask)):
            if want(name):
                print('--', name)
                await fn(p, c)
    sys.exit(c.done())

asyncio.run(main())
