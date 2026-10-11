"""learn: the brain learns from what happened (BACKLOG §1.7 #2 and #10; the round-5 brain findings, all five roles).

Five role experts graded the brain 4-6: its lessons were a fixed menu the owner had taught, every one "fired 0×",
and nothing was learned from the day's events. Every event here is driven through the app's own functions (the
seed, a Demo Workspace sync, appSetDay, the bank import shape, pay3ShortPay, payrollFromTime) and each check reads
what a person would see or the record their tap wrote.

  python3 learn_test.py                all sections
  python3 learn_test.py loop nyh       only the named sections

loop      LEARN_EVENTS is data (event kind -> lesson, who it is for, what it changes, a trigger, the evidence).
          The seed day's events are seen and proposed, never applied; approving one from The Brain creates the
          rule, which fires once per record that matches ("fired N×" with the records), again on a later day,
          never twice on one record; its firing is a card in the coordinator's Needs Your Hand and one tap makes
          the task. The loop runs from APP_DAY_HOOKS, after a sync, after a dispute (not only when The Brain
          renders).
today     "what did you learn today" and The Brain's Today tab answer from the loop with the same four numbers:
          events seen, lessons proposed, rules fired, changes drafted.
meet      Meeting tasks are proposals by default (company.meetAuto.task false); The Brain says what applies on
          its own; a synced meeting leaves its tasks proposed.
nyh       Needs Your Hand: every proposal the reader made from mail reaches the right person's Do Now (Approvals)
          as one card with one tap, routed by DELEGATION (Controller: statements and bills with no PO;
          coordinator: bills against a PO, quotes, receipts, certificates; Billing: payment claims, deposits,
          payments the bank never saw; Owner: master data and payroll); Ask "what needs my hand" lists the same
          rows (one count); a tap applies it once (the copies in other mailboxes are done too); a deposit in the
          bank becomes "Record payment" for Billing; a payment the bank never saw gets Resolve; a Zelle someone
          explained becomes a coding proposal; payroll reaches the Owner (never the person who built the run) and
          payrollFromTime builds the right pay period; a bill at the PM's turn has Recommend on the PM's Do Now;
          no Home line says "X wrote about Y" without a button.
standing  "remember: always copy Chen on vendor COIs" is a standing order with a scope; standingFor(uid, scope)
          returns it (the Owner's apply firm-wide) and a COI draft built anywhere carries the cc.
rule      A rule fires once per record that matches, never once per job: one outside consultant on three jobs
          gets one "committed deliverable dates" proposal; The Brain's Proposed tab counts by evidence.
cal       Calendar events are on each person's day: the Owner's Home, the Controller's Coming Up, the designer's
          My Day; the designer has an Inbox."""
import asyncio, re, sys, json, base64
from harness import *

ROLES_STAFF = ['u_owner', 'u_alan', 'u_chen', 'u_billing', 'u_controller', 'u_sarah']


async def fresh(p, uid='u_owner'):
    b, pg, errs = await open_app(p)
    await sign_in(pg, uid)
    return b, pg, errs


async def text(pg, sel='.view.on'):
    return await pg.evaluate("s => { const e = document.querySelector(s); return e ? e.innerText : '' }", sel)


async def drive(pg, say):
    """A sheet the tap opened: fill the blanks with a plain sentence and press its blue button (the safe next step)."""
    for _ in range(3):
        done = await pg.evaluate("""s => { const m = document.getElementById('mbm'); if (!m) return true;
            m.querySelectorAll('textarea, input[type=text], input:not([type])').forEach(f => { if (!f.value && f.offsetParent) { f.value = s; f.dispatchEvent(new Event('input', { bubbles: true })); } });
            m.querySelectorAll('input[type=checkbox]').forEach(x => x.checked || x.click());
            const b = [...m.querySelectorAll('.btn.primary')].find(x => x.offsetParent && !x.disabled); if (!b) return true; b.click(); return false; }""", say)
        await pg.wait_for_timeout(150)
        if done: break


async def connect(pg, uids):
    for u in uids:
        await pg.evaluate("async u => { signIn(u); render(); await gcDemoConnect(); }", u)
    await pg.wait_for_timeout(100)


async def sec_loop(p, c):
    b, pg, errs = await fresh(p)
    reg = await pg.evaluate("""() => LEARN_EVENTS.map(E => ({ kind: E.kind, label: E.label, for: E.for, change: E.change && E.change.type,
        text: E.change && E.change.text, trig: E.trigger && E.trigger.label, scan: typeof E.scan, rows: typeof (E.trigger || {}).rows, lesson: typeof E.lesson }))""")
    kinds = [r['kind'] for r in reg]
    c.ok(len(reg) >= 16, f'LEARN_EVENTS holds the event kinds the experts named: {kinds}')
    for need in ['noshow', 'coafter', 'lpcrevise', 'wrongreturn', 'poinvalid', 'nocoi', 'overpo', 'dupcharge', 'credit', 'wipmiss', 'dispute', 'void', 'exception', 'reopen', 'carried', 'promise']:
        c.ok(need in kinds, f'LEARN_EVENTS has {need}')
    bad = [r['kind'] for r in reg if r['change'] not in ('rule', 'reminder', 'checklist', 'process') or not r['for'] or not r['trig'] or r['scan'] != 'function' or r['rows'] != 'function' or r['lesson'] != 'function']
    c.ok(not bad, f'every event kind names who it is for, what it changes (rule, reminder, checklist, process), a trigger and a scan: {bad}')
    st = await pg.evaluate("""() => { const P = DB.learn && DB.learn.props || {}, E = DB.learn && DB.learn.events || {};
        return { props: Object.values(P).map(p => ({ kind: p.kind, status: p.status, title: p.title, n: p.events.length, ev: p.events.map(k => E[k] && E[k].what), ref: p.events.map(k => E[k] && E[k].ref) })),
          learned: DB.lessons.filter(l => l.learn).length, runs: (DB.learn.runs || []).map(r => r.src) } }""")
    P = {x['kind']: x for x in st['props']}
    for k in ['noshow', 'coafter', 'wrongreturn', 'nocoi', 'overpo', 'dupcharge', 'credit', 'carried']:
        c.ok(k in P and P[k]['status'] == 'proposed' and P[k]['n'] >= 1, f'the seed day proposes the {k} lesson from its events: {P.get(k)}')
    c.ok(all(all(e for e in x['ev']) and all(r for r in x['ref']) for x in st['props']), 'every proposal shows its evidence: the event and the record it points at')
    c.ok(st['learned'] == 0, f'nothing is applied on its own: {st["learned"]} learned lessons before anyone approved one')
    c.ok('boot' in st['runs'], f'the loop ran at boot, not only when The Brain renders: {st["runs"]}')
    c.ok(re.search(r'Restoration|Tomas', ' '.join(P['noshow']['ev'])), f'the no-show lesson names the sub that did not show: {P["noshow"]["ev"]}')
    sug = await pg.evaluate("() => bnSuggestLessons().filter(s => /day before/i.test(s.title)).map(s => [s.title, s.trigger, s.learn])")
    c.ok(len(sug) == 1 and sug[0][1], f'bnSuggestLessons reads the loop (one "confirm the day before" with its trigger): {sug}')
    # The Brain opens on Today; approve the no-show lesson with its button
    await go(pg, 'brain'); await pg.wait_for_timeout(300)
    t = await text(pg)
    c.ok('day before' in t and await pg.locator('.view.on [data-lnok="noshow"]').count() == 1, 'The Brain shows the proposed lesson with its evidence and an Approve button')
    c.ok(re.search(r'Restoration|Tomas', t) is not None, 'The Brain shows the evidence (the sub that did not show)')
    await pg.locator('.view.on [data-lnok="noshow"]').click(); await pg.wait_for_timeout(300)
    L = await pg.evaluate("""() => { const l = DB.lessons.find(x => x.learn === 'noshow'); return l && { title: l.title, fired: l.fired.map(f => f.what), keys: l.fired.map(f => f.key), status: DB.learn.props.noshow.status, then: l.then } }""")
    c.ok(L and L['status'] == 'approved' and L['then']['owner'] == 'coord', f'approving creates the rule, for the coordinator: {L}')
    c.ok(L and len(L['fired']) == 1 and 'Restoration' in L['fired'][0], f'it fires on the record that matches today (Restoration crew 9/4 unconfirmed): {L and L["fired"]}')
    n2 = await pg.evaluate("() => { lnLoop('test'); lnLoop('test'); return DB.lessons.find(x => x.learn === 'noshow').fired.length }")
    c.ok(n2 == 1, f'a rule fires once per record, never twice on one: {n2}')
    day = await pg.evaluate("() => { const r = appSetDay('2026-09-08'); const l = DB.lessons.find(x => x.learn === 'noshow'); return { ran: r.ran, fired: l.fired.map(f => f.what) } }")
    c.ok('lnLoop' in day['ran'], f'the loop runs on every new day (APP_DAY_HOOKS): {day["ran"]}')
    c.ok(len(day['fired']) == 2 and any('Window Works' in f for f in day['fired']), f'on 9/8 it fires on Window Works 9/9, unconfirmed: {day["fired"]}')
    await go(pg, 'brain'); await pg.evaluate("() => { bnTab = 'lessons'; renderBrain() }"); await pg.wait_for_timeout(200)
    t = await text(pg)
    c.ok(re.search(r'fired 2×', t) and 'Window Works' in t, 'The Brain shows "fired 2×" with the records it fired on')
    # the firing is the coordinator's card; one tap makes the task
    await sign_in(pg, 'u_chen')
    rows = await pg.evaluate("() => nyhRows().filter(r => r.kind === 'rule').map(r => ({ key: r.key, title: r.title, verb: r.verb }))")
    c.ok(len(rows) == 2 and all(r['verb'] == 'Make It a Task' for r in rows), f"the rule's firings are the coordinator's cards: {rows}")
    inq = await pg.evaluate("() => PRED.waitingOnMe.rows().filter(x => x.nyh && x.nyh.kind === 'rule').length")
    c.ok(inq == 2, f"the same cards are in the coordinator's Approvals (one queue): {inq}")
    await go(pg, 'home'); await pg.wait_for_timeout(300)
    k = rows[0]['key'] if rows else ''
    if k:
        await pg.locator(f'.view.on [data-nyhrow="{k}"] .h4-act').click(); await pg.wait_for_timeout(300)
        tk = await pg.evaluate("""k => { const a = DB.projects.flatMap(p => p.actions || []).find(a => a.source && a.source.kind === 'lesson' && /Text .* confirm/i.test(a.title)); return { a: a && [a.title, a.assignee, a.due], left: nyhRows().filter(r => r.key === k).length, toast: document.getElementById('toast').innerText } }""", k)
        c.ok(tk['a'] and tk['a'][1] == 'Chen Biron' and tk['left'] == 0, f'one tap on Home makes the dated task for Chen with the lesson as its source: {tk}')
        c.ok('Open' in tk['toast'], f'the tap toasts what happened with Open: {tk["toast"]!r}')
    # the loop runs after a sync and after a dispute
    await sign_in(pg, 'u_owner')
    await connect(pg, ['u_sarah'])
    sy = await pg.evaluate("() => ({ srcs: (DB.learn.runs || []).map(r => r.src), lpc: DB.learn.props.lpcrevise && { t: DB.learn.props.lpcrevise.title, ev: DB.learn.props.lpcrevise.events.map(k => DB.learn.events[k].what) } })")
    c.ok('sync' in sy['srcs'], f'the loop runs on every sync: {sy["srcs"][-5:]}')
    c.ok(sy['lpc'] and re.search(r'brick mold', ' '.join(sy['lpc']['ev']) + sy['lpc']['t'], re.I), f"LPC's revise-and-resubmit becomes a proposed lesson naming the item: {sy['lpc']}")
    await sign_in(pg, 'u_owner')
    dp = await pg.evaluate("""() => { const b = DB.bills.find(x => x.number === 'WW-2026-118'); const r = pay3ShortPay(b, 29700, 'Approved at the PO amount; the difference is disputed'); return { r: !!r, short: b.short, srcs: (DB.learn.runs || []).map(x => x.src).slice(-3), d: !!DB.learn.props.dispute } }""")
    c.ok('dispute' in dp['srcs'] and dp['d'], f'a bill dispute runs the loop and proposes the dispute lesson: {dp}')
    c.ok(not errs, f'loop: page errors {errs[:3]}')
    await b.close()


async def sec_today(p, c):
    b, pg, errs = await fresh(p)
    await connect(pg, ['u_controller', 'u_chen'])
    await sign_in(pg, 'u_owner')
    a = await pg.evaluate("() => { const r = paAsk('what did you learn today'); const T = lnToday(); return { h: r.headline, n: [T.events.length, T.proposed.length, T.fired.length, T.changes.length], work: r.work.length, offers: (r.offers || []).length } }")
    nums = [int(x) for x in re.findall(r'\b(\d+)\b', a['h'])[:4]]
    c.ok(nums == a['n'], f'"what did you learn today" answers from the loop: {a["h"]!r} vs {a["n"]}')
    c.ok(a['n'][0] > 0 and a['n'][1] > 0 and a['work'] > 0, f'the answer lists events and lessons: {a}')
    c.ok(a['offers'] >= 1, f'the answer offers the lessons to approve: {a["offers"]}')
    await go(pg, 'brain'); await pg.wait_for_timeout(300)
    tiles = await pg.evaluate("() => [...document.querySelectorAll('.view.on [data-lntile]')].map(x => [x.dataset.lntile, +x.dataset.n])")
    want = dict(zip(['events', 'proposed', 'fired', 'changes'], a['n']))
    c.ok(dict(tiles) == want, f"The Brain's Today shows the same four numbers: {tiles} vs {want}")
    c.ok(not errs, f'today: page errors {errs[:3]}')
    await b.close()


async def sec_meet(p, c):
    b, pg, errs = await fresh(p)
    auto = await pg.evaluate("() => DB.company.meetAuto")
    c.ok(auto and auto.get('task') is False, f'meeting tasks are proposals by default (meetAuto.task false): {auto}')
    await go(pg, 'brain'); await pg.wait_for_timeout(300)
    t = await text(pg)
    c.ok(re.search(r'Tasks from meeting steps:? proposed', t, re.I) and re.search(r'applies without asking', t, re.I), 'The Brain says meeting tasks are proposed and what applies without asking')
    await connect(pg, ['u_chen', 'u_alan'])
    m = await pg.evaluate("""() => (DB.meetings || []).filter(m => /site walk/i.test(m.title)).map(m => ({ t: m.title, tasks: (m.proposals || []).filter(x => x.kind === 'task').map(x => x.status) }))""")
    c.ok(m and all(all(s == 'proposed' for s in x['tasks']) and x['tasks'] for x in m), f"the synced site-walk notes leave their tasks proposed: {m}")
    c.ok(not errs, f'meet: page errors {errs[:3]}')
    await b.close()


async def sec_nyh(p, c):
    b, pg, errs = await fresh(p)
    await connect(pg, ['u_controller', 'u_chen', 'u_billing', 'u_owner', 'u_sarah', 'u_alan'])
    want = {'u_controller': [r'Satish', r'Amex|American Express|statement'], 'u_chen': [r'Carlos Millwork', r'Nemo Tile.*quote|quote', r'Home Depot'],
            'u_billing': [r'Jessop', r'Rivera'], 'u_owner': [r'Payroll'], 'u_sarah': [r'LPC']}
    for u in ROLES_STAFF:
        await sign_in(pg, u)
        R = await pg.evaluate("""() => { const R = role() === 'designer' ? nyhRows({ role: 'designer' }) : nyhRows(); const Q = PRED.waitingOnMe.rows();
            const a = paAsk('what needs my hand');
            return { rows: R.map(r => r.title), keys: R.map(r => r.key), verbs: R.map(r => r.verb), inQ: R.filter(r => Q.some(x => x.id === r.key)).length, ask: a.rows, head: a.headline } }""")
        c.ok(R['ask'] == len(R['rows']) and str(len(R['rows'])) in R['head'] if R['rows'] else 'Nothing' in R['head'], f'{u}: Ask "what needs my hand" lists the same rows, one count: {R["head"]!r} vs {len(R["rows"])}')
        if u != 'u_sarah':
            c.ok(R['inQ'] == len(R['rows']), f'{u}: every Needs Your Hand row is in their Do Now / Approvals: {R["inQ"]} of {len(R["rows"])}')
        for rx in want.get(u, []):
            c.ok(any(re.search(rx, x, re.I) for x in R['rows']), f'{u}: Needs Your Hand has /{rx}/: {R["rows"]}')
        c.ok(all(v for v in R['verbs']), f'{u}: every row has one verb')
        await go(pg, 'home' if u != 'u_sarah' else 'sday'); await pg.wait_for_timeout(250)
        bare = await pg.evaluate("""() => [...document.querySelectorAll('.view.on *')].filter(el => el.children.length === 0 && /wrote about|landed in Drive/.test(el.textContent))
            .filter(el => { let r = el; for (let i = 0; i < 4 && r; i++, r = r.parentElement) if (r.querySelector('button')) return false; return true; }).map(el => el.textContent.slice(0, 80))""")
        c.ok(not bare, f'{u}: no Home line says "X wrote about Y" without a button: {bare}')
    # one key across all routes: a proposal in three mailboxes is one row
    allr = await pg.evaluate("() => { const R = nyhRows({ everyone: true }); return { n: R.length, keys: new Set(R.map(r => r.key)).size, carlos: R.filter(r => /CM-0102/.test(r.title) || /CM-0102/.test(r.key)).map(r => r.route) } }")
    c.ok(allr['n'] == allr['keys'] and allr['carlos'] == ['coord'], f'one proposal, one row, one person (CM-0102 names PO-2026-048: the coordinator): {allr}')
    # Controller: one tap on Home applies the Satish bill; the row leaves
    await sign_in(pg, 'u_controller'); await go(pg, 'home'); await pg.wait_for_timeout(250)
    k = await pg.evaluate("() => (nyhRows().find(r => /Satish/.test(r.title)) || {}).key || ''")
    n0 = await pg.evaluate("() => +document.querySelector('.view.on .nyh-card').dataset.nyhn")
    c.ok(n0 == await pg.evaluate("() => nyhRows().length"), f"the Controller's Needs Your Hand card counts its rows: {n0}")
    n0p = await pg.evaluate("() => nyhRows().filter(r => r.kind !== 'standard').length")
    if k:
        await pg.locator(f'.view.on [data-nyhrow="{k}"] .h4-act').click(); await pg.wait_for_timeout(300)
        await pg.evaluate("() => { const m = document.getElementById('mbm'); const b = m && [...m.querySelectorAll('.btn.primary')].find(x => x.offsetParent); b && b.click(); }")
        await pg.wait_for_timeout(200)
        # Standard Watch rows (kind "standard") may change with the books: a bill paid with no PO is a three-way-match
        # breach for the Controller. The proposals themselves go down by one.
        s = await pg.evaluate("k => ({ bill: (DB.bills || []).filter(b => /SE-0922/.test(b.number || '')).length, left: nyhRows().some(r => r.key === k), n: nyhRows().filter(r => r.kind !== 'standard').length, card: +document.querySelector('.view.on .nyh-card').dataset.nyhn, all: nyhRows().length })", k)
        c.ok(s['bill'] == 1 and not s['left'] and s['n'] == n0p - 1 and s['card'] == s['all'], f'one tap applies the Satish bill once and the row leaves: {s}')
    z = await pg.evaluate("() => { const r = nyhRows().find(r => r.kind === 'code'); if (!r) return null; nyhRun(r.key); const t = DB.txns.find(t => /ZELLE/i.test(t.desc) && Math.abs(Math.abs(t.amt) - 2400) < 1); return { title: r.title, cat: t && t.cat, job: t && t.projectId } }")
    c.ok(z and z['cat'] and z['cat'] != 'uncat' and z['job'] == 'p121', f"Jeanette's Zelle explanation becomes a coding proposal; Apply codes the line to the job: {z}")
    # Billing: a deposit in the bank becomes Record Payment; a payment the bank never saw gets Resolve
    await sign_in(pg, 'u_billing')
    await pg.evaluate("() => { DB.txns.push({ id: 'tdepk', date: today(), acct: 'ac1', desc: 'MOBILE DEPOSIT CHK 2291 KLEIN', amt: 68265, cat: 'uncat', status: 'new', source: 'import', prov: { kind: 'import' } }); render(); }")
    d = await pg.evaluate("() => nyhRows().filter(r => r.kind === 'deposit').map(r => ({ key: r.key, title: r.title, verb: r.verb }))")
    kd = next((x for x in d if '68,265' in x['title']), None)
    c.ok(kd and 'INV-2026-038' in kd['title'] and kd['verb'] == 'Record Payment', f'a deposit in the bank is "Record payment: Kleins $68,265 against INV-2026-038": {d}')
    if kd:
        await go(pg, 'home'); await pg.wait_for_timeout(250)
        await pg.locator(f'.view.on [data-nyhrow="{kd["key"]}"] .h4-act').click(); await pg.wait_for_timeout(300)
        rec = await pg.evaluate("() => { const c = DB.clients.find(c => (c.payments || []).some(p => p.txnId === 'tdepk')); return { paid: !!c, left: nyhRows().some(r => r.key === 'dep:tdepk') } }")
        c.ok(rec['paid'] and not rec['left'], f'one tap records the payment against the invoice, linked to the bank line: {rec}')
    rv = await pg.evaluate("() => nyhRows().filter(r => r.kind === 'undeposited').map(r => r.key)")
    c.ok(len(rv) >= 2, f"the two Rivera payments the bank never saw each have Resolve: {rv}")
    if rv:
        await pg.evaluate("k => nyhRun(k)", rv[0]); await pg.wait_for_timeout(200)
        await pg.fill('#mbm input[data-f="why"]', 'never deposited; the client paid by wire, recorded twice')
        await pg.locator('#mbm .btn.primary').click(); await pg.wait_for_timeout(250)
        st = await pg.evaluate("k => ({ left: nyhRows().some(r => r.key === k), audit: (DB.audit || []).some(a => a.action === 'reversed') })", rv[0])
        c.ok(not st['left'] and st['audit'], f'Resolve reverses it with the reason on the record: {st}')
    # Owner: payroll on Do Now with Approve; never the person who built it
    await sign_in(pg, 'u_owner'); await go(pg, 'home'); await pg.wait_for_timeout(300)
    pr = await pg.evaluate("() => [...document.querySelectorAll('.view.on .td-do .td-card')].filter(c => c.dataset.kind === 'payroll').map(c => c.innerText.replace(/\\s+/g, ' '))")
    q = await pg.evaluate("() => PRED.waitingOnMe.rows().filter(x => x.kind === 'payroll').map(x => [x.title, x.yes])")
    c.ok(q and q[0][1] == 'Approve', f"the submitted payroll run is in the Owner's Do Now with Approve: {q} {pr}")
    await pg.evaluate("() => { const it = PRED.waitingOnMe.rows().find(x => x.kind === 'payroll'); it && nyhRun(it.id); }"); await pg.wait_for_timeout(200)
    await drive(pg, 'Hours cover the field crew only; office time is overhead.')
    ps = await pg.evaluate("() => DB.payroll.find(r => r.id === 'pr1').status")
    c.ok(ps == 'approved', f'the Owner approves the run from the card (through the split review it asks for): {ps}')
    await sign_in(pg, 'u_controller')
    mk = await pg.evaluate("""() => { appSetDay('2026-09-09'); DB.time.filter(t => t.status === 'submitted').forEach(t => t.status = 'approved'); const n0 = DB.payroll.length; payrollFromTime(); const R = DB.payroll.slice(n0);
        const r = R[0]; if (r) payrollAction(r, 'approve'); return R.map(x => ({ from: x.from, to: x.to, pay: x.payDate, status: x.status, by: x.createdBy, period: x.period })) }""")
    # leaks (month crack: runs approved at $329 and $2,653 against $18,100 and $18,680): one run per pay period
    # across entities, each entity's share inside it (r.entities)
    c.ok(mk and len(mk) == 1 and all(r['from'] == '2026-08-31' and r['to'] in ('2026-09-11', '2026-09-13') for r in mk), f'payrollFromTime builds one run for the pay period it is in (8/31 – 9/11, across entities), not 8/4 – 9/4: {mk}')
    c.ok(mk and all(r['status'] == 'submitted' for r in mk), f'the Controller who built it cannot approve it (separation of duties): {mk}')
    await sign_in(pg, 'u_owner')
    q2 = await pg.evaluate("() => PRED.waitingOnMe.rows().filter(x => x.kind === 'payroll').map(x => x.title)")
    c.ok(any('8/31' in x or 'Aug 31' in x for x in q2), f"the new run reaches the Owner's Do Now: {q2}")
    # PM: a bill at the PM's turn has Recommend on the PM's Do Now (a compliance block stops the payment, not the review)
    await sign_in(pg, 'u_alan'); await go(pg, 'home'); await pg.wait_for_timeout(300)
    # Do Now ranks by urgency, then the Standard's decision principles (a bill is Cost, the last of seven), so AMP-311 may sit
    # past the five cards shown; it is still in the PM's Do Now queue, and its card's verb is Recommend
    amp = await pg.evaluate("() => tdQueue().filter(it => it.kind === 'bill' && it.id === 'b4').map(it => tdCard(it).verb)")
    c.ok(amp == ['Recommend'], f"AMP-311 is on the PM's Do Now with Recommend: {amp}")
    await pg.evaluate("() => { const it = PRED.waitingOnMe.rows().find(x => x.id === 'b4'); apprBillYes(it); }"); await pg.wait_for_timeout(250)
    await pg.evaluate("() => { const m = document.getElementById('mbm'); if (!m) return; m.querySelectorAll('textarea, input:not([type=checkbox])').forEach(f => { if (!f.value) { f.value = 'Checked against the work on site.'; f.dispatchEvent(new Event('input', { bubbles: true })); } }); m.querySelectorAll('input[type=checkbox]').forEach(x => x.checked || x.click()); const b = m.querySelector('.btn.primary'); b && b.click(); }")
    await pg.wait_for_timeout(250)
    bs = await pg.evaluate("() => DB.bills.find(b => b.id === 'b4').status")
    c.ok(bs == 'pm-approved', f"the PM's Recommend sends it to the Owner: {bs}")
    c.ok(not errs, f'nyh: page errors {errs[:3]}')
    await b.close()


async def sec_standing(p, c):
    b, pg, errs = await fresh(p)
    await connect(pg, ['u_chen', 'u_owner'])
    await sign_in(pg, 'u_owner')
    s = await pg.evaluate("""() => { paAsk('remember: always copy Chen on vendor COIs'); paStand('remember: always copy Chen on vendor COIs');
        const a = standingFor('u_owner', 'coi'), b = standingFor('u_chen', 'coi'), n = standingFor('u_owner', 'invoice');
        return { a: a.map(x => [x.text, x.scope, x.cc.map(c => c.name)]), chen: b.length, other: n.length } }""")
    c.ok(s['a'] and 'coi' in s['a'][0][1] and 'vendor' in s['a'][0][1] and s['a'][0][2] == ['Chen Biron'], f'the standing order has a scope (vendor mail, COI) and the cc it asks for: {s}')
    c.ok(s['chen'] >= 1 and s['other'] == 0, f"the Owner's order applies firm-wide, and only to its scope: {s}")
    raw = await pg.evaluate("""async () => { const keep = gcFetch; let sent = null; gcFetch = async (...a) => { const [u, o] = a; if (/drafts/.test(u) && o && o.body) sent = JSON.parse(o.body); return keep(...a); };
        try { await gaDraft({ to: 'Tino <tino@tino.example>', subject: 'Certificate of insurance — Tino', body: 'Please send a current certificate of insurance.', why: 'Tino owes a COI' }); } finally { gcFetch = keep; }
        return sent && sent.message && sent.message.raw }""")
    hdr = base64.urlsafe_b64decode(raw + '=' * (-len(raw) % 4)).decode('utf-8', 'replace') if raw else ''
    c.ok(re.search(r'^Cc: .*Chen Biron', hdr, re.M), f'a COI draft built anywhere carries the cc the standing order asks for: {hdr[:160]!r}')
    c.ok(not errs, f'standing: page errors {errs[:3]}')
    await b.close()


async def sec_rule(p, c):
    b, pg, errs = await fresh(p)
    q = await pg.evaluate("""() => { const L = DB.lessons.find(l => /outside designer or consultant commits to dates/i.test(l.title));
        const p121 = DB.projects.find(p => p.id === 'p121'); const con = parseContacts(p121.project.contacts).find(x => /architect|designer|consultant|engineer/i.test((x.role || '') + ' ' + (x.company || '')));
        if (!con) return { err: 'no consultant on 121 State' };
        DB.brainQueue = DB.brainQueue.filter(x => x.lessonId !== L.id);
        ['p45', 'p140'].forEach(id => { const p = DB.projects.find(x => x.id === id); p.project.contacts = (p.project.contacts ? p.project.contacts + '\\n' : '') + `${con.name} | ${con.role || 'Architect'} | ${con.company || ''} | ${con.email || ''}`;
          (p.decisions = p.decisions || []).push({ id: uid('d'), name: 'Drawings from ' + con.name, owner: 'Architect / designer', status: 'open', due: '' }); });
        bnRun(); return { con: con.name, q: DB.brainQueue.filter(x => x.lessonId === L.id && x.status === 'proposed').map(x => x.projectId) } }""")
    c.ok(q.get('q') is not None and len(q['q']) == 1, f'one outside consultant on three jobs: the rule fires once per record, not per job: {q}')
    await go(pg, 'brain'); await pg.evaluate("() => { bnTab = 'queue'; renderBrain() }"); await pg.wait_for_timeout(200)
    t = await text(pg)
    c.ok(re.search(r'by evidence', t, re.I) and re.search(r'\d+ from ', t), f"The Brain's Proposed tab counts by evidence: {t[:300]!r}")
    c.ok(not errs, f'rule: page errors {errs[:3]}')
    await b.close()


async def sec_cal(p, c):
    b, pg, errs = await fresh(p)
    await connect(pg, ['u_owner', 'u_controller', 'u_sarah'])
    await sign_in(pg, 'u_owner'); await go(pg, 'home'); await pg.wait_for_timeout(300)
    t = await text(pg)
    c.ok(re.search(r'Your Calendar', t) and re.search(r'Site visit', t), f"the Owner's Home shows today's calendar: {t[:400]!r}")
    await sign_in(pg, 'u_controller'); await go(pg, 'home'); await pg.wait_for_timeout(300)
    t = await text(pg)
    c.ok(re.search(r'Period close — August|Bank reconciliation', t), "the Controller's Coming Up shows the calendar")
    await sign_in(pg, 'u_sarah'); await go(pg, 'sday'); await pg.wait_for_timeout(300)
    t = await text(pg)
    c.ok(re.search(r'Your Calendar', t), "the designer's My Day shows her calendar")
    c.ok(re.search(r'Needs Your Hand', t) and await pg.locator('.view.on [data-nyh]').count() >= 1, "the designer's My Day has Needs Your Hand with a button")
    k = await pg.evaluate("() => (nyhRows({ role: 'designer' }).find(r => /brick mold/i.test(r.title)) || {}).key || ''")
    if k:
        await pg.locator(f'.view.on [data-nyh="{k}"]').click(); await pg.wait_for_timeout(250)
        tk = await pg.evaluate("() => DB.projects.flatMap(p => p.actions || []).filter(a => /LPC/.test(a.title) && /Sarah/.test(a.assignee)).map(a => [a.title, a.due])")
        c.ok(tk and tk[0][1], f"LPC's comment becomes Sarah's dated revise-and-resubmit task: {tk}")
    else:
        c.ok(False, 'the brick mold comment from LPC is on the designer\'s Needs Your Hand')
    views = await pg.evaluate("() => ROLE_VIEWS.designer.includes('comms')")
    c.ok(views, 'the designer has an Inbox')
    await go(pg, 'comms'); await pg.wait_for_timeout(300)
    t = await text(pg)
    c.ok(re.search(r'LPC', t), 'her Inbox shows her mail (LPC)')
    c.ok(not errs, f'cal: page errors {errs[:3]}')
    await b.close()


SECTIONS = {'loop': sec_loop, 'today': sec_today, 'meet': sec_meet, 'nyh': sec_nyh, 'standing': sec_standing, 'rule': sec_rule, 'cal': sec_cal}


async def main():
    want = sys.argv[1:] or list(SECTIONS)
    c = Checks()
    async with async_playwright() as p:
        for k in want:
            print('--', k)
            try:
                await SECTIONS[k](p, c)
            except Exception as e:
                c.ok(False, f'{k}: {type(e).__name__}: {str(e)[:300]}')
    return c.done()

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
