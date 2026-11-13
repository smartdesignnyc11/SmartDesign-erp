"""job_structure_test: the job page Alan approved on 11-03 (docs/mockups/job-structure/, docs/DECISIONS.md 11-03 row),
done as the person through the screens, on the desktop (1440) and the phone (390).

Alan, 10-27: "If we're in the projects page, anything we click within that project should take us to information
regarding that particular project." The checks, each on both devices:
  OPEN     tapping a job in the Projects list (and the switcher) opens that job's page, never All Projects > Overview
  HEADER   the job's name with its switcher, the client, "Day N of M"; Ask About This Job (desktop); one + button
  TABS     eight tabs in order: Overview, Schedule, Contract and Billing, Budget, Purchasing, Decisions, Site, Documents
           (desktop: the strip; phone: the Overview's This Job list), each opening a page headed by its name
  SCOPE    two jobs seeded with marked records: every tab and tile of one job shows nothing of the other
  COUNTS   every tile's number equals the rows it opens (At Risk, Approvals, Materials)
  NEW      the + opens "New for <job>" with its eight kinds; each creates the record tied to this job and its client,
           with no job or client to pick (the client from the project, never a billing filter)
  LOST     every page the old ~18 tabs reached is reachable from the new tabs (the table is printed)
  BUDGET   Budget's figures per estimate line equal the Costs page's figures of master (lineProfit, jobFin)
  SITE     a job's Site shows only its own daily logs; one person logged on two jobs over a day's hours is warned
  RFI      an RFI is a record with who owes it, by when and what it blocks, listed on Decisions, answered off the list
  PHONE    no sideways scroll, tap targets of 44px on the job's own controls, one blue primary per screen; on every
           job tab, nothing past the right edge and no button or tile whose words run past its own edges
  HIDDEN   no job page carries hidden text: the job's own blocks carry none at all; elsewhere on a job tab a hidden
           block is only the other device's twin of something on screen (the check is shown to catch a planted one)
  ROLES    the + offers each role only the kinds it can open where they live, and each opens a sheet it can save
  TIES     Contract and Billing: in the bank + recorded, not yet in the bank = the payments recorded on the job;
           Budget: the rows (with Not on an Estimate Line) sum to Cost to Date; "13% over", never "113%"
Screenshots of every new page land in review/job_structure/.
Usage: python3 job_structure_test.py [--desktop|--phone]
"""
import asyncio, os, re, sys
from harness import *

OUT = os.path.join(ROOT, 'review', 'job_structure')
TABS = ['Overview', 'Schedule', 'Contract and Billing', 'Budget', 'Purchasing', 'Decisions', 'Site', 'Documents']
TAB_VIEW = {'Overview': 'dash', 'Schedule': 'sched', 'Contract and Billing': 'jbill', 'Budget': 'costs', 'Purchasing': 'proc',
            'Decisions': 'jdec', 'Site': 'jsite', 'Documents': 'files'}
# Every page the old job strip reached (MN_JOBS before 11-03), and where it lives now: the tab it sits under and the
# control on that tab that opens it. Nothing is lost.
OLD = [
    ('Projects', 'ovjobs', 'the job header: All Projects in the switcher, and the back arrow on the phone'),
    ('Overview', 'dash', 'Overview'),
    ('Project Settings', 'proj', 'Overview > Job Settings'),
    ('Schedule', 'sched', 'Schedule'),
    ('Tasks', 'tasks', 'Schedule > Tasks on This Job; Overview > Next Up'),
    ('Decisions', 'dec', 'Decisions > the Decisions Log, and each decision row'),
    ('Submittals', 'subm', 'Decisions > the Submittals Log, and each submittal row'),
    ('Permits', 'insp', 'Documents > Permits and Inspections'),
    ('Field', 'field', 'Site > Daily Logs and Open Items'),
    ('Photos', 'photos', 'Documents > Photos'),
    ('Deliveries', 'recv', 'Purchasing > Deliveries'),
    ('Materials', 'mat', 'Purchasing > Materials'),
    ('Costs', 'costs', 'Budget (the same page, reshaped)'),
    ('Change Orders', 'billing:co', 'Contract and Billing > Change Orders chip, each row opens the change order'),
    ('Estimates', 'billing:estimates', 'Contract and Billing > Estimates chip, each row opens the estimate'),
    ('Billing', 'billing', 'Contract and Billing > Billing Queue for This Job'),
    ('Documents', 'files', 'Documents'),
    ('Drawings', 'plans', 'Documents > Drawings'),
    ('Mail', 'inbox', 'Documents > Mail'),
]
MARK = 'ZQX'   # marked records on the other job: none may appear on this job's pages

VIS = "el => { if (!el) return false; const r = el.getBoundingClientRect(), s = getComputedStyle(el); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; }"
TXT = r"""() => { const v = document.querySelector('.view.on'); if (!v) return '';
  // what a person reads: the page's text, without a picker's options or the crew-hours warning that names both jobs on purpose
  const skip = new Set([...v.querySelectorAll('select option')].map(o => o.textContent.trim()));
  const clash = (document.getElementById('js-clash') || {}).innerText || '';
  return (v.innerText || '').split('\n').filter(l => !skip.has(l.trim()) && !(clash && clash.includes(l.trim()) && l.trim())).join('\n'); }"""
STATE = r"""() => { const vis = """ + VIS + """;
  const v = document.querySelector('.view.on'), H = document.getElementById('jp-head');
  const txt = el => el ? (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim() : '';
  const head = H && vis(H);
  const tabs = [...document.querySelectorAll('#subnav .sub-tabs button[data-sub]')].filter(vis).map(b => txt(b).replace(/\s*\d+$/, ''));
  const on = document.querySelector('#subnav .sub-tabs button.on');
  const h = v ? [...v.querySelectorAll('h1, h2')].find(vis) : null;
  const prim = v ? [...v.querySelectorAll('.btn.primary')].filter(vis).map(txt) : [];
  return { view, sid: S && S.id, head, headTxt: head ? txt(H) : '', tabs, on: on && vis(on) ? txt(on).replace(/\s*\d+$/, '') : '',
    heading: txt(h), crumbs: txt(document.querySelector('#crumbs b')), prim, sw: document.documentElement.scrollWidth, w: innerWidth,
    sw2: document.getElementById('pswitch') ? document.getElementById('pswitch').value : null,
    swIn: !!(H && H.querySelector('#pswitch')), all: typeof dashAll !== 'undefined' && !!dashAll }; }"""


PAGES = ['dash', 'sched', 'jbill', 'costs', 'proc', 'jdec', 'jsite', 'files']
# the job's own blocks (src/jobpage.js): no hidden text in them at all
OWN = '#jp-head, #jp-ov, #v-dash, #jp-budget, #jbill-body, #jdec-body, #jsite-body'
# The other device's controls, declared by class (a phone's Take Photo on the desktop, the desktop's Print and
# dependency lines on the phone, a segment the picker beside it replaces), and the phone's own layout of the lists
# other lanes draw (a phone row drops a table's header and some columns; a tile's sub-line; Schedule's track
# sub-lines). Each is counted and printed, never silent; anything else hidden with words in it fails.
DEVICE = '.phone-only, .desk-only, .desk-only2, .gantt-only, .os-print, .os-hidden'
PHONE_LAYOUT = 'table.pr-tbl > thead, tr.pr-tr > td, table.dg-t > thead, .glance .gl-s, #track-cards .track:not(.ops-fc) > .s'
HIDDEN = r"""async (arg) => { const sleep = ms => new Promise(r => setTimeout(r, ms)); const [OWN, DEVICE, PHONE_LAYOUT, PAGES, plant] = arg;
  const norm = t => String(t || '').replace(/\s+/g, ' ').trim(), phone = innerWidth <= 760, bad = [], known = {};
  const hidden = e => { const s = getComputedStyle(e); return s.display === 'none' || s.visibility === 'hidden' || e.hidden; };
  const walk = (el, acc) => { for (const e of el.children) { if (e.matches('select, option, datalist, template, script, style, .jp-vh')) continue;
    if (hidden(e)) { norm(e.textContent).length > 2 && acc.push(e); } else walk(e, acc); } };
  for (const v of PAGES) { view = v; jpSub = ''; jpMenuOpen = false; if (v === 'proc') bbProj = S.id; render(); await sleep(150);
    if (plant && v === 'dash') { const d = document.createElement('div'); d.style.display = 'none'; d.textContent = 'Planted hidden tile 999 at risk'; (document.getElementById('jp-ov') || document.querySelector('.view.on')).appendChild(d); }
    const R = [document.querySelector('.view.on'), document.getElementById('jp-head')].filter(Boolean);
    const seen = norm(R.map(r => r.innerText).join(' '));
    const H = []; R.forEach(r => walk(r, H));
    H.forEach(e => { const say = v + ': ' + (e.id ? '#' + e.id : e.tagName.toLowerCase() + '.' + String(e.className).trim().split(/\s+/)[0]) + ' "' + norm(e.textContent).slice(0, 50) + '"';
      if (e.closest(OWN.split(', ').filter(x => x !== '#v-dash' || v === 'dash').join(', '))) return bad.push('own ' + say);
      if (e.matches(DEVICE) || e.closest(DEVICE)) return (known.device = (known.device || 0) + 1);
      if (phone && (e.matches(PHONE_LAYOUT) || e.closest(PHONE_LAYOUT))) return (known.phone = (known.phone || 0) + 1);
      // a twin: every piece of its text is on the screen already
      const tw = document.createTreeWalker(e, NodeFilter.SHOW_TEXT); let n, miss = 0;
      while ((n = tw.nextNode())) { const t = norm(n.nodeValue); if (t.length > 1 && !n.parentElement.closest('select, script, style') && !seen.includes(t)) miss++; }
      if (miss) bad.push(say); else known.twin = (known.twin || 0) + 1; }); }
  return { bad, known }; }"""
# every element of a job tab inside the screen; a button's, tile's or chip's words inside its own edges
OVERFLOW = r"""async (arg) => { const sleep = ms => new Promise(r => setTimeout(r, ms)); const [OWN, PAGES] = arg; const out = [], words = [];
  // a strip that scrolls on its own and sits on the screen clips what is in it (strips nest: any one on the screen does)
  const strip = e => { for (let x = e.parentElement; x && x !== document.body; x = x.parentElement) { const o = getComputedStyle(x).overflowX; if ((o === 'auto' || o === 'scroll') && x.getBoundingClientRect().right <= innerWidth + 1) return x; } return null; };
  for (const v of PAGES) { view = v; jpSub = ''; jpMenuOpen = false; if (v === 'proc') bbProj = S.id; render(); await sleep(150);
    const R = [document.querySelector('.view.on'), document.getElementById('jp-head')].filter(Boolean);
    R.forEach(root => root.querySelectorAll('*').forEach(e => { const r = e.getBoundingClientRect(); if (!r.width || !r.height || e.closest('select')) return;
      if (r.right > innerWidth + 1 || r.left < -1) { const own = e.closest(OWN), st = strip(e);
        // the job's own blocks never run off the screen; elsewhere only inside a strip that scrolls on its own and sits on the screen
        if (own || !st) out.push(v + ': ' + (e.id || String(e.className).trim().split(/\s+/)[0] || e.tagName) + ' ' + Math.round(r.right)); } }));
    R.forEach(root => root.querySelectorAll('button, .btn, label.btn, a.btn, .gl, .jp-tile, .jp-kpi, .pill, .chip, [role=button]').forEach(e => { if (!e.getClientRects().length) return; const s = getComputedStyle(e);
      if (s.overflowX === 'auto' || s.overflowX === 'scroll') return;
      if (e.scrollWidth > e.clientWidth + 1 || e.scrollHeight > e.clientHeight + 2 && s.overflowY === 'hidden') words.push(v + ': "' + (e.innerText || e.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ').slice(0, 40) + '" ' + e.scrollWidth + '>' + e.clientWidth); })); }
  return { edge: [...new Set(out)].slice(0, 10), words: [...new Set(words)].slice(0, 10) }; }"""


async def js(pg, body, arg=None):
    try:
        return await pg.evaluate("async (arg) => { const sleep = ms => new Promise(r => setTimeout(r, ms)); " + body + " }", arg)
    except Exception as e:   # a missing page or control is a failed check, never a crashed suite
        print('  (page script failed:', str(e).split('\n')[0][:160] + ')')
        return {}


async def tap(pg, sel, wait=350):
    ok = await pg.evaluate("s => { const e = [...document.querySelectorAll(s)].find(x => x.getClientRects().length); if (!e) return false; e.scrollIntoView({block: 'center'}); e.click(); return true; }", sel)
    await pg.wait_for_timeout(wait)
    return ok


async def shot(pg, name):
    os.makedirs(OUT, exist_ok=True)
    # the page scrolls inside <body>, so the viewport grows to the page for the picture, then comes back
    vp = pg.viewport_size
    h = await pg.evaluate("() => Math.min(6000, Math.max(document.body.scrollHeight, document.documentElement.scrollHeight))")
    await pg.set_viewport_size({'width': vp['width'], 'height': max(vp['height'], h)})
    await pg.wait_for_timeout(150)
    await pg.screenshot(path=os.path.join(OUT, name + '.png'), full_page=True)
    await pg.set_viewport_size(vp)
    await pg.wait_for_timeout(100)


async def seed_other(pg):
    """marked records on 206 Lenox: a decision, a change order, an RFI, a question from the crew, a material late to
    order, a task due today. None may appear on 121 State Street's pages; each must on 206 Lenox's."""
    return await js(pg, """
      const p = DB.projects.find(x => x.id === 'p206'), c = DB.clients.find(x => x.id === p.clientId), td = today();
      const t0 = p.tasks.find(t => t.status !== 'done') || p.tasks[0];
      p.decisions.push({ id: 'zqd1', name: 'ZQX hallway sconce decision', owner: 'Client', kind: 'task', ref: t0.id, status: 'open', due: addWork(td, -2), notes: '', scope: { kind: 'task', id: t0.id }, options: [], impactDays: 0, impactCost: 0, timeline: [] });
      (p.issues = p.issues || []).push({ id: 'zqi1', title: 'ZQX RFI on the stair stringer', type: 'rfi', status: 'open', owner: 'Architect / designer', taskId: t0.id, due: addWork(td, 2), notes: '', scope: { kind: 'task', id: t0.id } });
      DB.field.raises.push({ id: 'zqr1', projectId: 'p206', type: 'rfi', title: 'ZQX which way does the door swing', note: '', to: 'pm', cc: [], dueBy: addWork(td, 1), by: 'Angel', at: td + 'T08:00:00', status: 'sent', escalated: false, photos: [], calls: [] });
      const co = newDoc(c, 'co', {}); co.projectId = 'p206'; co.title = 'ZQX change for the tub'; co.status = 'sent'; co.lines = [{ id: 'zql1', item: 'ZQX tub', desc: '', qty: 1, unit: 'ea', rate: 999, cost: 500, taxable: false }]; c.changeOrders.push(co);
      p.actions = p.actions || []; p.actions.push({ id: 'zqa1', title: 'ZQX call the super', assignee: 'Alan', due: td, priority: 'med', status: 'todo', link: null, notes: '', createdAt: td, completedAt: '', createdBy: 'Alan' });
      save(); return { co: co.number };""")


async def open_from_list(pg, phone, name='121 State Street'):
    """Projects, then the job's row, tapped for real"""
    await go(pg, 'ovjobs')
    await pg.wait_for_timeout(300)
    ok = await pg.evaluate("n => { const r = [...document.querySelectorAll('.view.on tr[data-edit^=\"ov:jobs:\"]')].find(x => x.getClientRects().length && x.innerText.includes(n)); if (!r) return false; (r.querySelector('td') || r).click(); return true; }", name)
    await pg.wait_for_timeout(600)
    return ok


async def run(c, p, phone):
    dev = 'phone' if phone else 'desktop'
    b, pg, errs = await open_app(p, phone)
    await sign_in(pg, 'u_alan')
    # lane F (11-12, an approved design: one EAC for a job): a Budget row's budget, actual and committed are the job's own
    # by line (jobFin's eacLines, the lines its estimate at completion is added from), not lineProfit's (only what was
    # coded straight to the line), so the rows and the Total row are the job's one estimate at completion
    base = await js(pg, """setCurrent('p121'); return { lp: (jobFin(S).eacLines || []).map(r => ({ key: r.key, budget: r.budget, actual: r.actual, committed: r.committed })),
      est: jobFin(S).estGPPct, plan: jobFin(S).plannedGPPct };""")
    seeded = await seed_other(pg)

    # ---- OPEN: the Projects list, tapped
    c.ok(await open_from_list(pg, phone), f'{dev} OPEN: 121 State Street is a row on Projects')
    st = await pg.evaluate(STATE)
    c.ok(st['view'] == 'dash' and st['sid'] == 'p121', f'{dev} OPEN: tapping 121 State Street opens its page ({st["view"]}, {st["sid"]})')
    c.ok(st['head'] and '121 State Street' in st['headTxt'] or (st['head'] and st['sw2'] == 'p121'), f'{dev} OPEN: the job header names the job ({st["headTxt"][:80]})')
    c.ok(not st['all'] and st['sw2'] == 'p121', f'{dev} OPEN: never All Projects (switcher {st["sw2"]}, all {st["all"]})')
    t = await pg.evaluate("() => (document.querySelector('.view.on') || {}).innerText || ''")
    c.ok(not re.search(r'\d+ of \d+ at risk|across \d+ projects|all projects', t, re.I), f'{dev} OPEN: no firm-wide tile on the job page ({re.findall(r"[^\n]*(?:of \d+ at risk|across \d+ projects|all projects)[^\n]*", t, re.I)[:2]})')
    await shot(pg, f'overview_{dev}')

    # ---- HEADER
    h = await js(pg, """const H = document.getElementById('jp-head'); if (!H) return null; const vis = """ + VIS + """;
      const plus = document.getElementById('jp-new'), ask = document.getElementById('jp-ask');
      return { txt: H.innerText, sw: !!H.querySelector('#pswitch'), plus: vis(plus), ask: vis(ask), plusLabel: plus && plus.getAttribute('aria-label'),
        n: [...document.querySelectorAll('header.topbar, .main')].length };""")
    c.ok(h is not None, f'{dev} HEADER: the job header is drawn')
    if h:
        c.ok(h['sw'], f'{dev} HEADER: the job name is its switcher')
        c.ok('Klein' in h['txt'], f'{dev} HEADER: the client is named ({h["txt"][:90]})')
        c.ok(bool(re.search(r'Day \d+ of \d+', h['txt'])), f'{dev} HEADER: Day N of M ({h["txt"][:120]})')
        c.ok(h['plus'] and h['plusLabel'] == 'New for this job', f'{dev} HEADER: one + button, New for this job')
        if not phone: c.ok(h['ask'], f'{dev} HEADER: Ask About This Job')

    # ---- TABS
    if not phone:
        c.ok(st['tabs'] == TABS, f'{dev} TABS: the strip reads {st["tabs"]}')
        for i, lab in enumerate(TABS):
            await tap(pg, f'#subnav .sub-tabs button[data-sub="{TAB_VIEW[lab]}"]')
            s2 = await pg.evaluate(STATE)
            c.ok(s2['view'] == TAB_VIEW[lab] and s2['sid'] == 'p121', f'{dev} TABS: {lab} opens {TAB_VIEW[lab]} on the job ({s2["view"]})')
            c.ok(s2['on'] == lab, f'{dev} TABS: {lab} is lit ({s2["on"]})')
            c.ok(s2['heading'] == lab, f'{dev} TABS: {lab} is headed "{s2["heading"]}"')
            c.ok(s2['head'], f'{dev} TABS: {lab} keeps the job header')
            c.ok(len(s2['prim']) <= 1, f'{dev} TABS: {lab} has {len(s2["prim"])} blue buttons {s2["prim"]}')
            await shot(pg, f'tab_{i + 1}_{TAB_VIEW[lab]}_{dev}')
    else:
        await go(pg, 'dash')
        secs = await pg.evaluate("() => [...document.querySelectorAll('#jp-sections [data-jpsec]')].filter(e => e.getClientRects().length).map(e => [e.dataset.jpsec, e.querySelector('.jp-sl') ? e.querySelector('.jp-sl').innerText.trim() : ''])")
        c.ok([x[1] for x in secs] == TABS[1:], f'{dev} TABS: This Job lists {[x[1] for x in secs]}')
        for i, lab in enumerate(TABS[1:], 1):
            await go(pg, 'dash')
            await tap(pg, f'#jp-sections [data-jpsec="{TAB_VIEW[lab]}"]')
            s2 = await pg.evaluate(STATE)
            c.ok(s2['view'] == TAB_VIEW[lab] and s2['sid'] == 'p121', f'{dev} TABS: {lab} opens {TAB_VIEW[lab]} ({s2["view"]})')
            c.ok(lab in s2['headTxt'], f'{dev} TABS: the header names {lab} ({s2["headTxt"][:60]})')
            c.ok(s2['sw'] <= s2['w'], f'{dev} TABS: {lab} scrolls sideways ({s2["sw"]} at {s2["w"]})')
            c.ok(len(s2['prim']) <= 1, f'{dev} TABS: {lab} has {len(s2["prim"])} blue buttons {s2["prim"]}')
            await shot(pg, f'tab_{i + 1}_{TAB_VIEW[lab]}_{dev}')
            back = await tap(pg, '#jp-head [data-jpback]')
            s3 = await pg.evaluate(STATE)
            c.ok(back and s3['view'] == 'dash', f'{dev} TABS: back from {lab} lands on the job ({s3["view"]})')

    # ---- SCOPE: nothing of 206 Lenox on 121 State Street's pages; Lenox's own marked records on its pages
    for job, own in (('p121', False), ('p206', True)):
        await js(pg, "setCurrent(arg); mnLastGrp = 'jobs'; save();", job)
        for lab in TABS:
            v = TAB_VIEW[lab]
            await js(pg, "view = arg; if (arg === 'proc') { bbProj = S.id; } render(); await sleep(200);", v)
            txt = await pg.evaluate(TXT)
            if not own:
                c.ok(MARK not in txt, f'{dev} SCOPE: 121 State Street > {lab} shows 206 Lenox\'s records ({[l for l in txt.splitlines() if MARK in l][:2]})')
                c.ok('Lenox' not in txt, f'{dev} SCOPE: 121 State Street > {lab} names 206 Lenox ({[l for l in txt.splitlines() if "Lenox" in l][:2]})')
            else:
                want = {'Contract and Billing': f'{seeded["co"]}', 'Decisions': 'ZQX RFI on the stair', 'Site': 'ZQX which way'}.get(lab)
                if want: c.ok(want in txt, f'{dev} SCOPE: 206 Lenox > {lab} lists its own {want}')
                c.ok('121 State' not in txt, f'{dev} SCOPE: 206 Lenox > {lab} names 121 State Street ({[l for l in txt.splitlines() if "121 State" in l][:2]})')
        if own:
            dtxt = await js(pg, "view = 'jdec'; render(); await sleep(150); return (document.getElementById('jdec-body') || {}).innerText || '';")
            c.ok('ZQX hallway sconce' in dtxt, f'{dev} SCOPE: 206 Lenox > Decisions lists its client decision')

    # ---- COUNTS: each tile's number is the rows it opens (on this job)
    await js(pg, "setCurrent('p121'); mnLastGrp = 'jobs'; jpSub = ''; view = 'dash'; render(); await sleep(250);")
    tiles = await pg.evaluate("() => [...document.querySelectorAll('#jp-ov button.gl[data-tl]')].map(b => ({ tl: b.dataset.tl, k: b.querySelector('.gl-k').innerText.trim(), v: b.querySelector('.gl-v').innerText.trim() }))")
    c.ok([x['k'] for x in tiles] == ['At Risk', 'Margin at Completion', 'Approvals', 'Materials'], f'{dev} COUNTS: tiles {[x["k"] for x in tiles]}')
    for x in tiles:
        m = re.match(r'^(\d+)(?!\d*%)', x['v'])
        if not m or x['v'].endswith('%'): continue
        await js(pg, "jpSub = ''; view = 'dash'; render(); await sleep(150);")
        await tap(pg, f'#jp-ov button.gl[data-tl="{x["tl"]}"]')
        r = await pg.evaluate("() => { const P = document.getElementById('jp-panel'); return P ? { n: [...P.querySelectorAll('[data-jprow]')].filter(e => e.getClientRects().length).length, t: P.innerText.slice(0, 300) } : null; }")
        c.ok(r is not None and r['n'] == int(m.group(1)), f'{dev} COUNTS: {x["k"]} {m.group(1)} opens {r and r["n"]} rows')
        if r: c.ok(MARK not in r['t'] and 'Lenox' not in r['t'], f'{dev} COUNTS: {x["k"]} lists only this job')
        if phone and x['tl'] in ('risk', 'appr'): await shot(pg, f'overview_{x["tl"]}_{dev}')
    if not phone: await shot(pg, f'overview_panels_{dev}')
    # the finish forecast and its cause are on the Overview, drawn, whenever Schedule's forecast card has one (the old
    # dashboard's Schedule tile carried it, drawn hidden); a slip on the critical path makes one
    fc = (await js(pg, """const t = S.tasks.find(x => x.status !== 'done' && computeCPM().cpm[x.id] && computeCPM().cpm[x.id].critical);
      const P = S.project, t0 = P.target, e0 = t.end, d0 = t.dur; if (!P.target) P.target = addWork(today(), 20); t.end = addWork(t.end, 25); t.dur = (t.dur || 1) + 25;
      jpSub = ''; view = 'dash'; render(); await sleep(200); const W = tpForecastWhy(S), e = document.getElementById('jp-forecast');
      const out = { late: W.late, text: W.text, card: e && e.getClientRects().length ? e.innerText.replace(/\\s+/g, ' ') : '' };
      t.end = e0; t.dur = d0; P.target = t0; render(); await sleep(100); return out;""")) or {}
    c.ok(fc.get('late', 0) > 0 and fc.get('text') and fc['text'].replace(' — Pull In', '') in fc.get('card', ''), f'{dev} OVERVIEW: a late finish and its cause are on the Overview ({fc})')
    await js(pg, "jpSub = ''; render();")

    # ---- NEW: the + menu, each kind tied to the job and its client
    await js(pg, "setCurrent('p121'); mnLastGrp = 'jobs'; view = 'dash'; render(); await sleep(150);")
    await tap(pg, '#jp-new')
    menu = await pg.evaluate("() => { const m = document.getElementById('jp-newmenu'); return m ? { head: (m.querySelector('.jp-nh') || {}).innerText || '', items: [...m.querySelectorAll('[data-jpnew]')].map(b => b.innerText.trim()), tall: [...m.querySelectorAll('[data-jpnew]')].every(b => b.getBoundingClientRect().height >= 40) } : null; }")
    c.ok(menu and menu['head'] == 'New for 121 State Street', f'{dev} NEW: the menu is headed New for 121 State Street ({menu and menu["head"]})')
    c.ok(menu and menu['items'] == ['Estimate', 'Change Order', 'Invoice', 'Purchase Order', 'Task', 'Decision', 'Site Note or Photo', 'Document'], f'{dev} NEW: items {menu and menu["items"]}')
    if phone: c.ok(menu and menu['tall'], f'{dev} NEW: every item is a full tap target')
    await shot(pg, f'new_menu_{dev}')
    made = (await js(pg, """const out = {}; const c = DB.clients.find(x => x.id === 'cl121');
      // a client or job to pick is a field a person can see and change
      const pick = () => { const m = document.getElementById('mbm'); return !!(m && [...m.querySelectorAll('[data-f="clientId"], [data-f="projectId"]')].some(e => e.getClientRects().length)); };
      const run = async k => { jpMenuOpen = false; view = 'dash'; render(); await sleep(60); document.getElementById('jp-new').click(); await sleep(80); const b = document.querySelector('#jp-newmenu [data-jpnew="' + k + '"]'); if (!b) return false; b.click(); await sleep(350); return true; };
      // Estimate: the template picker, then Start
      let n0 = c.estimates.length; await run('est'); out.estPick = pick();
      const st = [...document.querySelectorAll('#mbm button, #mbm .btn')].find(x => /^Start Estimate/i.test(x.innerText.trim())); if (st) { st.click(); await sleep(450); }
      const e = c.estimates[c.estimates.length - 1]; out.est = c.estimates.length > n0 && e && e.projectId === 'p121';
      try { mbCloseModal(); } catch (x) {} docOpen = null;
      // Change Order: the dialog, typed and created
      n0 = c.changeOrders.length; await run('co'); out.coPick = pick();
      const ti = document.querySelector('#mbm [data-f="title"]'); if (ti) ti.value = 'Job page CO';
      const sb = document.querySelector('#mbm .mbm-ft .btn.primary, #mbm button[type="submit"]'); if (sb) { sb.click(); await sleep(350); }
      const co = c.changeOrders[c.changeOrders.length - 1]; out.co = c.changeOrders.length > n0 && co.projectId === 'p121';
      try { mbCloseModal(); } catch (x) {} docOpen = null;
      // Invoice: started for the job's client, on the job
      n0 = c.invoices.length; await run('inv');
      const iv = c.invoices[c.invoices.length - 1]; out.inv = c.invoices.length > n0 && iv.projectId === 'p121'; out.invView = view;
      try { mbCloseModal(); } catch (x) {} docOpen = null; setCurrent('p121');
      // Purchase Order: the drawer on this job
      await run('po'); out.poOpen = !!document.querySelector('#drawer.on') || !!document.getElementById('mbm'); out.poTitle = (document.getElementById('d-title') || {}).textContent || '';
      out.poJob = S.id;
      try { closeDrawer(); } catch (x) { document.getElementById('drawer')?.classList.remove('on'); document.getElementById('scrim')?.classList.remove('on'); } try { mbCloseModal(); } catch (x) {}
      // Task: preset to the job
      await run('task'); const fr = document.querySelector('#mbm [data-f="for"]'); out.taskFor = fr ? fr.value : ''; try { mbCloseModal(); } catch (x) {}
      // Decision, Site Note: the quick sheets on this job
      await run('dec'); out.decOpen = !!document.querySelector('#mbm, .msheet, .m-sheet, #msheet'); out.decTxt = (document.querySelector('#mbm, .msheet, .m-sheet, #msheet') || {}).innerText || ''; try { mbCloseModal(); } catch (x) {} document.querySelectorAll('.msheet, .m-sheet, #msheet, .m-scrim').forEach(e => e.remove());
      await run('note'); out.noteOpen = !!document.querySelector('#mbm, .msheet, .m-sheet, #msheet'); try { mbCloseModal(); } catch (x) {} document.querySelectorAll('.msheet, .m-sheet, #msheet, .m-scrim').forEach(e => e.remove());
      // Document: the job's Documents, the upload
      await run('doc'); out.docView = view; out.docJob = S.id;
      return out;""")) or {}
    c.ok(made.get('est') and not made.get('estPick'), f'{dev} NEW: Estimate is created on 121 State Street for the Kleins, no client to pick {made}')
    c.ok(made.get('co') and not made.get('coPick'), f'{dev} NEW: Change Order is created on 121 State Street, no client to pick')
    c.ok(made.get('inv'), f'{dev} NEW: Invoice is created on 121 State Street for the Kleins')
    c.ok(made.get('poOpen') and made.get('poJob') == 'p121', f'{dev} NEW: Purchase Order opens on this job ({made.get("poTitle")})')
    c.ok(made.get('taskFor') in ('p:p121', 'p121'), f'{dev} NEW: Task is preset to this job ({made.get("taskFor")})')
    c.ok(made.get('decOpen'), f'{dev} NEW: Decision opens its sheet on this job')
    c.ok(made.get('noteOpen'), f'{dev} NEW: Site Note or Photo opens its sheet on this job')
    c.ok(made.get('docView') == 'files' and made.get('docJob') == 'p121', f'{dev} NEW: Document opens this job\'s Documents to upload ({made.get("docView")})')

    # ---- ROLES: the + offers each role only what it can open where it lives, and each item opens a sheet it can save
    for uid, rl, never in (('u_owner', 'owner', []), ('u_chen', 'coord', ['Estimate', 'Change Order', 'Invoice']), ('u_billing', 'billing', ['Purchase Order', 'Decision', 'Site Note or Photo']),
                           ('u_sarah', 'designer', ['Estimate', 'Change Order', 'Invoice', 'Purchase Order']), ('u_alan', 'pm', [])):
        await sign_in(pg, uid)
        rr = (await js(pg, """const LIVES = { Estimate: ['billing'], 'Change Order': ['billing'], Invoice: ['billing'], 'Purchase Order': ['po', 'proc'], Task: ['tkall', 'tasks'], Decision: ['dec', 'jdec'], 'Site Note or Photo': ['field', 'jsite', 'photos'], Document: ['files'] };
          const RV = ROLE_VIEWS[role()] || [], vis = e => !!e && e.getClientRects().length > 0 && getComputedStyle(e).visibility !== 'hidden';
          const close = () => { try { mbCloseModal(); } catch (x) {} try { closeDrawer(); } catch (x) {} document.querySelectorAll('#mbm, .msheet, .m-sheet, #msheet, .m-scrim').forEach(e => e.remove()); docOpen = null; };
          setCurrent('p121'); mnLastGrp = 'jobs'; jpOpenJob('p121'); await sleep(200);
          if (!jpOn()) return { on: false, view };
          const home = view;
          jpMenuOpen = false; render(); document.getElementById('jp-new').click(); await sleep(100);
          const items = [...document.querySelectorAll('#jp-newmenu [data-jpnew]')].map(b => [b.dataset.jpnew, b.innerText.trim()]);
          const res = [];
          for (const [k, lab] of items) {
            close(); setCurrent('p121'); mnLastGrp = 'jobs'; view = home; jpSub = ''; jpMenuOpen = false; render(); await sleep(80);
            document.getElementById('jp-new').click(); await sleep(80);
            const b = document.querySelector('#jp-newmenu [data-jpnew="' + k + '"]'); if (!b) { res.push({ lab, ok: false, why: 'gone' }); continue; }
            b.click(); await sleep(400);
            // the sheet it opened, and a save in it the role can press
            const sheet = [...document.querySelectorAll('#mbm, .msheet, .m-sheet, #msheet, #drawer.on')].find(vis);
            const save = sheet && [...sheet.querySelectorAll('button, .btn')].find(x => vis(x) && !x.disabled && (x.classList.contains('primary') || /^(Save|Create|Start|Add|Send|Log|Post|Upload|Record|Done)/i.test((x.innerText || '').trim())));
            // or the record itself, opened where it lives (an invoice), or the page the upload lives on (a document)
            const landed = view, mayLand = landed === home || RV.includes(landed) || (jpUnder(landed) && RV.includes(jpUnder(landed)));
            const openedDoc = !!docOpen && RV.includes('billing');
            const upload = landed === 'files' && [...document.querySelectorAll('.view.on input[type=file], .view.on label.btn, .view.on [data-upload]')].some(x => x.type === 'file' || vis(x));
            res.push({ lab, ok: mayLand && (LIVES[lab] || []).some(x => RV.includes(x)) && (!!save || openedDoc || upload), sheet: !!sheet, save: save ? save.innerText.trim().slice(0, 24) : '', landed, mayLand });
            close();
          }
          return { on: true, role: role(), items: items.map(x => x[1]), res };""")) or {}
        if rl == 'pm' or not rr.get('on'):
            c.ok(rr.get('on'), f'{dev} ROLES: {rl} opens 121 State Street\'s page ({rr})')
        if not rr.get('on'): continue
        c.ok(not [x for x in never if x in rr['items']], f'{dev} ROLES: the {rl}\'s + offers nothing it cannot open where it lives ({[x for x in never if x in rr["items"]]} of {rr["items"]})')
        badr = [x for x in rr['res'] if not x['ok']]
        c.ok(rr['res'] and not badr, f'{dev} ROLES: every + item the {rl} sees opens a sheet it can save ({badr[:3]})')
    await sign_in(pg, 'u_alan')

    # ---- LOST: every old destination is reachable from the new tabs
    if not phone:
        print('  old tab              -> its home now')
    for name, target, home in OLD:
        v, _, tab = target.partition(':')
        r = await js(pg, """const [v, tab] = arg; setCurrent('p121'); mnLastGrp = 'jobs'; docOpen = null; const sleep2 = ms => new Promise(r => setTimeout(r, ms));
          const pages = ['dash', 'sched', 'jbill', 'costs', 'proc', 'jdec', 'jsite', 'files'];
          if (pages.includes(v) && !tab) { view = v; render(); await sleep2(100); return { ok: view === v, via: 'tab' }; }
          for (const pgv of pages) { view = pgv; if (pgv === 'proc') bbProj = S.id; render(); await sleep2(120);
            const el = [...document.querySelectorAll('[data-jpgo="' + v + (tab ? ':' + tab : '') + '"]')].find(e => e.getClientRects().length);
            if (el) { el.click(); await sleep2(250); const want = tab ? (view === 'billing' && billTab === tab) || (view === 'clients') : view === v; return { ok: want && S.id === 'p121', via: pgv, landed: view }; } }
          // the header (Projects)
          const hb = [...document.querySelectorAll('#jp-head [data-jpgo="' + v + '"], #jp-head [data-jpback]')].find(e => e.getClientRects().length);
          return { ok: false, via: 'none' };""", [v, tab])
        if tab in ('co', 'estimates'):
            chip = 'Change Orders' if tab == 'co' else 'Estimates'
            r = await js(pg, """const [chip, kind] = arg; setCurrent('p121'); mnLastGrp = 'jobs'; docOpen = null; view = 'jbill'; render(); await sleep(150);
              const b = document.querySelector('[data-jbchip="' + chip + '"]'); if (!b) return { ok: false, via: 'no chip' }; b.click(); await sleep(200);
              const rows = [...document.querySelectorAll('#jb-docs [data-jbdoc]')].filter(e => e.getClientRects().length);
              if (!rows.length || !rows.every(e => e.dataset.jbdoc.startsWith(kind + ':'))) return { ok: false, via: 'chip rows', n: rows.length };
              rows[0].click(); await sleep(300); return { ok: !!docOpen && docOpen.kind === kind && S.id === 'p121', via: 'Contract and Billing chip', landed: view, rows: rows.length };""", [chip, 'co' if tab == 'co' else 'estimate'])
        if v == 'ovjobs':
            r = await js(pg, "setCurrent('p121'); view = 'dash'; render(); await sleep(100); const ps = document.getElementById('pswitch'); const o = ps && [...ps.options].find(x => x.value === '__all'); if (!o) return { ok: false, via: 'no All Projects' }; ps.value = '__all'; ps.dispatchEvent(new Event('change', { bubbles: true })); await sleep(300); return { ok: view === 'ovjobs' || view === 'port', via: 'switcher', landed: view };")
        c.ok((r or {}).get('ok'), f'{dev} LOST: {name} ({target}) is reachable from the job ({r})')
        if not phone: print(f'  {name:20s} -> {home}')

    # ---- BUDGET = the Costs figures of master
    await js(pg, "setCurrent('p121'); mnLastGrp = 'jobs'; view = 'costs'; render(); await sleep(250);")
    bud = await pg.evaluate("""() => [...document.querySelectorAll('#jp-budget [data-jpline]')].filter(e => e.getClientRects().length).map(e => ({ key: e.dataset.jpline, budget: +e.dataset.budget, actual: +e.dataset.actual, committed: +e.dataset.committed, txt: e.innerText }))""")
    lp = {x['key']: x for x in base['lp']}
    lines = [x for x in bud if x['key'] != '__noline']
    c.ok(len(lines) == len(lp), f'{dev} BUDGET: one row per estimate and change-order line ({len(lines)} of {len(lp)})')
    bad = [x['key'] for x in lines if x['key'] not in lp or abs(x['budget'] - lp[x['key']]['budget']) > .01 or abs(x['actual'] - lp[x['key']]['actual']) > .01 or abs(x['committed'] - lp[x['key']]['committed']) > .01]
    c.ok(not bad, f"{dev} BUDGET: budget, actual and committed equal the job's own line figures ({bad[:3]})")
    win = next((x for x in bud if 'Windows' in x['txt']), None)
    c.ok(win and '$29,700' in win['txt'] and '$33,500' in win['txt'], f'{dev} BUDGET: Windows reads $29,700 budget and $33,500 actual, as Costs did ({win and win["txt"][:160]})')
    # $33,500 on $29,700 is 13% over its budget: "113%" read as 113% over (one wording, the row, the card, the Overview)
    c.ok(win and '13% over' in win['txt'] and '113%' not in win['txt'], f'{dev} BUDGET: Windows says 13% over, never 113% ({win and win["txt"][:160]})')
    # TIE: the rows, with the cost on no estimate line as a row of its own, sum to Cost to Date (jobFin's actual)
    tie = (await js(pg, """const J = jobFin(S), R = [...document.querySelectorAll('#jp-budget [data-jpline]')].filter(e => e.getClientRects().length);
      const k = [...document.querySelectorAll('#jp-budget .jp-kpi')].find(e => /Cost to Date/.test(e.innerText));
      const nl = R.find(e => e.dataset.jpline === '__noline');
      return { sum: Math.round(R.reduce((a, e) => a + (+e.dataset.actual || 0), 0) * 100) / 100, com: Math.round(R.reduce((a, e) => a + (+e.dataset.committed || 0), 0) * 100) / 100,
        actual: J.actual, committed: J.committed, tile: k ? k.querySelector('b').innerText : null, money: money(J.actual), nl: nl ? nl.innerText.replace(/\\s+/g, ' ') : '' };""")) or {}
    c.ok(tie and abs(tie['sum'] - tie['actual']) < 0.01 and abs(tie['com'] - tie['committed']) < 0.01, f'{dev} TIES: Budget rows sum to Cost to Date (actual {tie.get("sum")} of {tie.get("actual")}, committed {tie.get("com")} of {tie.get("committed")})')
    if not phone: c.ok(tie.get('tile') == tie.get('money'), f'{dev} TIES: the Cost to Date tile reads the rows\' sum ({tie.get("tile")} vs {tie.get("money")})')
    c.ok('Not on an Estimate Line' in tie.get('nl', '') and 'no estimate line' in tie.get('nl', '').lower().replace('not on an estimate line', ''), f'{dev} TIES: cost on no estimate line is its own row, flagged ({tie.get("nl", "")[:120]})')
    ov = await js(pg, "view = 'dash'; jpSub = ''; render(); await sleep(150); const t = (document.getElementById('jp-ov') || {}).innerText || ''; view = 'costs'; render(); await sleep(150); return t;")
    c.ok('113%' not in (ov or '') and '13% over' in (ov or ''), f'{dev} BUDGET: the Overview says Windows 13% over, the same words ({[l for l in (ov or "").splitlines() if "over" in l][:3]})')
    if phone:
        lab = await pg.evaluate("() => { const e = document.querySelector('#jp-budget [data-jpline]'); return e ? [...e.querySelectorAll('.jp-bk')].map(x => x.innerText.trim()) : []; }")
        c.ok(lab[:6] == ['Budget', 'Committed', 'Actual', 'Forecast', 'Variance', 'Done'] or set(['Budget', 'Committed', 'Actual', 'Forecast', 'Variance', 'Done', 'Billed']) <= set(lab), f'{dev} BUDGET: every figure on a line card is labelled ({lab})')
    mg = await pg.evaluate("() => (document.getElementById('jp-margin') || {}).innerText || ''")
    c.ok(f"{round(base['est'])}%" in mg and f"{round(base['plan'])}%" in mg, f'{dev} BUDGET: margin at completion {round(base["est"])}% vs plan {round(base["plan"])}% on top ({mg[:80]})')
    bb = await pg.evaluate("() => (document.getElementById('jp-billback') || {}).innerText || ''")
    c.ok('Bought for the Client, Not Billed Back' in bb and '$10,170' in bb, f'{dev} BUDGET: Bought for the Client, Not Billed Back names $10,170 ({bb[:120]})')
    opened = await js(pg, "const e = [...document.querySelectorAll('#jp-budget [data-jpline]')].find(x => /Windows/.test(x.innerText)); if (!e) return null; (e.querySelector('[data-jpopen]') || e).click(); await sleep(200); return (document.querySelector('.jp-detail') || {}).innerText || '';")
    c.ok(opened and ('WW-2026-118' in opened or 'Window Works' in opened), f'{dev} BUDGET: tapping Windows shows what is behind it ({(opened or "")[:120]})')
    await shot(pg, f'budget_{dev}')

    # ---- SITE: only this job's logs; one person on two jobs over a day is warned
    await js(pg, "setCurrent('p206'); mnLastGrp = 'jobs'; view = 'jsite'; render(); await sleep(200);")
    t206 = await pg.evaluate(TXT)
    c.ok('Framing on 3rd fl nearly complete' not in t206, f'{dev} SITE: 206 Lenox\'s Site does not show 121 State\'s 9/2 log')
    await js(pg, "view = 'field'; render(); await sleep(200);")
    f206 = await pg.evaluate("() => (document.getElementById('v-field') || {}).innerText || ''")
    c.ok('Framing on 3rd fl nearly complete' not in f206, f'{dev} SITE: 206 Lenox\'s Field page does not show 121 State\'s 9/2 log')
    clash = await js(pg, "setCurrent('p206'); view = 'jsite'; render(); await sleep(200); const e = document.getElementById('js-clash'); return e ? e.innerText : '';")
    c.ok('Alberto' in clash and ('121 State' in clash or 'other job' in clash), f'{dev} SITE: Alberto on two jobs\' 9/2 logs is flagged ({clash[:160]})')
    warned = await js(pg, """setCurrent('p206'); const td = today();
      DB.field.logs.push({ id: 'zqlog121', projectId: 'p121', date: td, crew: [{ name: 'Alex', empId: 'em3', trade: 'Helper', hours: 8 }], subs: [], deliveries: [], done: [], status: 'submitted', notes: '' });
      const rec = { id: 'zqlog206', projectId: 'p206', date: td, crew: [{ name: 'Alex', empId: 'em3', trade: 'Helper', hours: 7 }], subs: [], deliveries: [], done: [], status: 'submitted', notes: '' };
      DB.field.logs.push(rec); const w = jpCrewClashes('p206').filter(x => x.date === td); view = 'jsite'; render(); await sleep(150);
      return { n: w.length, who: w.map(x => x.name), txt: (document.getElementById('js-clash') || {}).innerText || '', warnAt: typeof jpLogWarn === 'function' ? jpLogWarn(rec) : '' };""")
    warned = warned or {}
    c.ok(warned.get('n', 0) >= 1 and 'Alex' in warned.get('who', []) and 'Alex' in warned.get('txt', ''), f'{dev} SITE: a new log putting Alex on two jobs today is warned {warned}')
    c.ok(bool(warned.get('warnAt')), f'{dev} SITE: signing such a log carries the warning ({str(warned.get("warnAt"))[:100]})')
    await js(pg, "setCurrent('p121'); view = 'jsite'; render(); await sleep(200);")
    q = await pg.evaluate("() => [...document.querySelectorAll('#js-q [data-jsq]')].map(e => ({ t: e.innerText, ans: !!e.querySelector('[data-jsans]') }))")
    c.ok(q and all(x['ans'] for x in q), f'{dev} SITE: Site opens on the crew\'s open questions, each with Answer ({len(q)})')
    order = await pg.evaluate("() => ['js-q', 'js-today', 'js-coming'].map(id => { const e = document.getElementById(id); return e ? Math.round(e.getBoundingClientRect().top + scrollY) : -1; })")
    c.ok(order[0] >= 0 and order[0] < order[1] < order[2], f'{dev} SITE: questions, then today on site, then coming to site ({order})')
    await shot(pg, f'site_{dev}')

    # ---- RFI: the minimum record and list
    await js(pg, "setCurrent('p121'); view = 'jdec'; render(); await sleep(200);")
    chips = await pg.evaluate("() => [...document.querySelectorAll('#jdec-body [data-jdchip]')].map(b => b.innerText.replace(/\\s*\\d+$/, '').trim())")
    c.ok(chips == ['All', 'Selections', 'Design', 'RFIs', 'Submittals'], f'{dev} RFI: Decisions chips {chips}')
    rows = await pg.evaluate("() => [...document.querySelectorAll('#jdec-body [data-jdrow]')].map(e => ({ k: e.dataset.kind, t: e.innerText, od: e.dataset.overdue === '1' }))")
    c.ok(rows and all(re.search(r'Waiting on', x['t']) for x in rows), f'{dev} RFI: each row says who owes it ({[x["t"][:40] for x in rows if "Waiting on" not in x["t"]][:2]})')
    ods = [x['od'] for x in rows]
    c.ok(ods == sorted(ods, reverse=True), f'{dev} RFI: overdue rows first')
    mk = await js(pg, """const n0 = (S.issues || []).length; const b = document.getElementById('jd-newrfi'); if (!b) return null; b.click(); await sleep(250);
      const m = document.getElementById('mbm'); if (!m) return { modal: false };
      const set = (k, v) => { const e = m.querySelector('[data-f="' + k + '"]'); if (e) { e.value = v; e.dispatchEvent(new Event('change', { bubbles: true })); } return !!e; };
      const f = { title: set('title', 'Joist depth at the garden stair'), owner: set('owner', 'Architect / designer'), due: set('due', addWork(today(), 2)) };
      const bl = m.querySelector('[data-f="taskId"]'); if (bl && bl.options.length > 1) bl.value = bl.options[1].value;
      (m.querySelector('.mbm-ft .btn.primary') || m.querySelector('button.primary')).click(); await sleep(300);
      const it = (S.issues || []).find(i => i.title === 'Joist depth at the garden stair');
      view = 'jdec'; render(); await sleep(150);
      const row = [...document.querySelectorAll('#jdec-body [data-jdrow]')].find(e => e.innerText.includes('Joist depth at the garden stair'));
      return { modal: true, f, made: !!it, type: it && it.type, blocks: it && it.taskId, row: row ? row.innerText : '', key: it && it.id };""")
    c.ok(mk and mk.get('made') and mk['type'] == 'rfi', f'{dev} RFI: New RFI makes an RFI record ({mk})')
    c.ok(mk and 'Waiting on' in mk.get('row', '') and 'RFI' in mk.get('row', '').upper(), f'{dev} RFI: the new RFI is listed with who owes it ({(mk or {}).get("row", "")[:120]})')
    if mk and mk.get('key'):
        ans = (await js(pg, """const k = arg; const row = document.querySelector('#jdec-body [data-jdrow="iss:' + k + '"]'); const b = row && row.querySelector('[data-jdact]'); if (!b) return { btn: false };
          b.click(); await sleep(250); const m = document.getElementById('mbm'); const a = m && m.querySelector('[data-f="answer"]'); if (!a) return { btn: true, field: false };
          a.value = 'Two inches, per SK-4'; (m.querySelector('.mbm-ft .btn.primary') || m.querySelector('button.primary')).click(); await sleep(300);
          const it = S.issues.find(i => i.id === k); view = 'jdec'; render(); await sleep(150);
          return { btn: true, field: true, status: it.status, answer: it.answer, listed: !!document.querySelector('#jdec-body [data-jdrow="iss:' + k + '"]') };""", mk['key'])) or {}
        c.ok(ans.get('answer') == 'Two inches, per SK-4' and not ans.get('listed'), f'{dev} RFI: answering it records the answer and takes it off the list ({ans})')
    await shot(pg, f'decisions_{dev}')
    await js(pg, "view = 'jbill'; render(); await sleep(200);")
    await shot(pg, f'billing_{dev}')
    bl = await pg.evaluate("""() => { const b = document.getElementById('jbill-body'); if (!b) return null; return { needs: [...b.querySelectorAll('#jb-needs [data-jprow]')].length,
      prim: [...b.querySelectorAll('.btn.primary')].filter(e => e.getClientRects().length).map(e => e.innerText.trim()),
      contract: [...b.querySelectorAll('#jb-contract [data-label]')].map(e => e.dataset.label), docs: [...b.querySelectorAll('#jb-docs [data-jbdoc]')].map(e => e.dataset.date),
      chips: [...b.querySelectorAll('[data-jbchip]')].map(e => e.innerText.trim()) }; }""")
    c.ok(bl and bl['contract'] == ['Original contract', 'Approved changes', 'Revised contract', 'Billed to date', 'Paid, in the bank', 'Recorded, not yet in the bank', 'Retainage held', 'Left to bill'], f'{dev} BILLING: The Contract lines {bl and bl["contract"]}')
    c.ok(bl and bl['chips'] == ['All', 'Estimates', 'Change Orders', 'Invoices', 'Payments'], f'{dev} BILLING: the documents chips {bl and bl["chips"]}')
    c.ok(bl and bl['docs'] == sorted(bl['docs'], reverse=True), f'{dev} BILLING: documents newest first')
    c.ok(bl and len(bl['prim']) == 1 and bl['prim'][0].startswith('Draft the Application'), f'{dev} BILLING: one blue safe next step ({bl and bl["prim"]})')
    money = (await js(pg, "const J = jobFin(S); const g = k => { const e = document.querySelector('#jb-contract [data-label=\"' + k + '\"]'); return e ? e.dataset.amt : null; }; return { base: J.base, co: J.coAmt, rev: J.contract, billed: J.billed, paid: J.collected, ret: J.retHeld, s: [g('Original contract'), g('Approved changes'), g('Revised contract'), g('Billed to date'), g('Paid, in the bank'), g('Retainage held')].map(Number) };")) or {'s': 0}
    c.ok(money.get('s') == [money.get('base'), money.get('co'), money.get('rev'), money.get('billed'), money.get('paid'), money.get('ret')], f'{dev} BILLING: The Contract reads jobFin\'s figures (bank-backed collected) {money}')
    # TIE: in the bank + recorded, not yet in the bank = every payment recorded on the job's invoices; the recorded line
    # is the invoices' own "recorded, not yet in the bank" (invoiceUnbanked, the pill Billing and the client page show).
    # The Riveras (45 Cranberry) paid $21,350 the bank has not shown yet: the page says so, beside $0 in the bank.
    for nm in ('121 State', '45 Cranberry'):
        t3 = (await js(pg, """const p = DB.projects.find(x => (x.name || '').includes(arg) || ((x.project || {}).name || '').includes(arg)); if (!p) return null;
          setCurrent(p.id); mnLastGrp = 'jobs'; view = 'jbill'; render(); await sleep(150); const J = jobFin(S), c = DB.clients.find(x => x.id === S.clientId);
          const g = k => { const e = document.querySelector('#jb-contract [data-label="' + k + '"]'); return e && e.getClientRects().length ? { amt: +e.dataset.amt, txt: e.innerText.replace(/\\s+/g, ' ') } : null; };
          const invs = c.invoices.filter(i => !['void', 'draft'].includes(i.status) && (i.projectId === S.id || (!i.projectId && DB.projects.filter(x => x.clientId === c.id).length === 1)));
          const rec = Math.round(c.payments.filter(py => !py.unapplied && invs.some(i => i.id === py.invoiceId)).reduce((a, py) => a + (+py.amount || 0), 0) * 100) / 100;
          const pill = Math.round(invs.reduce((a, i) => a + (typeof invoiceUnbanked === 'function' ? invoiceUnbanked(c, i) : 0), 0) * 100) / 100;
          return { job: S.id, bank: g('Paid, in the bank'), not: g('Recorded, not yet in the bank'), rec, pill, J: [J.collected, J.unbanked] };""", nm)) or {}
        bk, nt = (t3.get('bank') or {}).get('amt'), (t3.get('not') or {}).get('amt')
        c.ok(bk is not None and nt is not None and abs(bk + nt - t3.get('rec', -1)) < 0.01, f'{dev} TIES: {nm}: in the bank + recorded, not yet in the bank = the payments recorded on the job ({t3})')
        c.ok(nt is not None and abs(nt - t3.get('pill', -1)) < 0.01, f'{dev} TIES: {nm}: the recorded, not yet in the bank line is the invoices\' own figure ({nt} vs {t3.get("pill")})')
        if nm == '45 Cranberry':
            c.ok(nt == 21350 and '$21,350' in (t3.get('not') or {}).get('txt', ''), f'{dev} TIES: the Riveras\' $21,350 recorded, not yet in the bank is said ({t3.get("not")}, in the bank {t3.get("bank")})')
    await js(pg, "setCurrent('p121'); view = 'jbill'; render(); await sleep(100);")

    # ---- PHONE: tap targets on the job's own controls
    if phone:
        small = await js(pg, """const out = []; for (const v of ['dash', 'jbill', 'costs', 'jdec', 'jsite']) { view = v; jpSub = ''; render(); await sleep(150);
          document.querySelectorAll('#jp-head button, #jp-head select, #jp-head a, .view.on .jp-tap').forEach(e => { const r = e.getBoundingClientRect(); if (r.width && (r.height < 43.5 || r.width < 43.5)) out.push(v + ': ' + (e.innerText || e.getAttribute('aria-label') || e.id).trim().slice(0, 30) + ' ' + Math.round(r.width) + 'x' + Math.round(r.height)); }); } return out;""")
        c.ok(small == [], f'{dev} PHONE: tap targets under 44px {small}')
        # nothing of the job's own pages runs past the screen's right edge, even inside a strip that scrolls on its own
        # (the page itself never scrolls sideways, so the sideways check above cannot see a card cut off in a strip)
        cut = await js(pg, """const out = []; for (const v of ['dash', 'jbill', 'costs', 'jdec', 'jsite']) { view = v; jpSub = ''; render(); await sleep(150);
          document.querySelectorAll('#jp-head, #jp-ov *, #jp-budget *, #jbill-body *, #jdec-body *, #jsite-body *').forEach(e => { const r = e.getBoundingClientRect();
            if (r.width && r.height && r.right > innerWidth + 1 && !e.closest('select')) out.push(v + ': ' + (e.className || e.tagName) + ' ' + Math.round(r.right)); }); } return out.slice(0, 8);""")
        c.ok(cut == [], f'{dev} PHONE: parts of the job pages run past the right edge {cut}')
    if phone:
        ov = await pg.evaluate(OVERFLOW, [OWN, PAGES])
        c.ok(ov['edge'] == [], f'{dev} PHONE: parts of a job tab run past the screen\'s edge {ov["edge"]}')
        c.ok(ov['words'] == [], f'{dev} PHONE: a button\'s or tile\'s words run past its own edges {ov["words"]}')

    # ---- HIDDEN: no job page carries hidden text (a check reading textContent passed on the old Overview's hidden cards)
    await js(pg, "setCurrent('p121'); mnLastGrp = 'jobs'; jpSub = ''; view = 'dash'; render(); await sleep(150);")
    hd = await pg.evaluate(HIDDEN, [OWN, DEVICE, PHONE_LAYOUT, PAGES, False])
    c.ok(hd['bad'] == [], f'{dev} HIDDEN: hidden text on the job\'s pages {hd["bad"][:6]}')
    print(f'  {dev} HIDDEN: allowed, each the other device\'s or a phone row\'s twin: {hd["known"]}')
    # the instrument: a hidden block planted on the Overview is caught
    pl = await pg.evaluate(HIDDEN, [OWN, DEVICE, PHONE_LAYOUT, ['dash'], True])
    c.ok(any('Planted hidden tile' in x for x in pl['bad']), f'{dev} HIDDEN: the check catches a hidden block planted on the Overview ({pl["bad"][:2]})')
    await js(pg, "view = 'dash'; render(); await sleep(100);")
    c.ok(not errs, f'{dev}: page errors {errs[:3]}')
    await b.close()


async def main():
    args = sys.argv[1:]
    c = Checks()
    async with async_playwright() as p:
        if '--phone' not in args: await run(c, p, False)
        if '--desktop' not in args: await run(c, p, True)
    return c.done()

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
