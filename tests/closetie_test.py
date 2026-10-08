"""closetie (BACKLOG §1.1): the WIP ties to the GL on close day, and every number the close touches agrees.

Drives the finance lens's month-end (docs/REVIEW_PROTOCOL.md) as the Owner, through the app's own functions
and screens, and checks the figures the lane produced before it was lost:
  1. short-pay WW-2026-118 (approve $29,700 at PO-2026-044, dispute $3,800) and Approve as Billed AMP-311;
  2. import the Amex August CSV (the bank's file has one dumpster charge, the register two), reconcile Amex
     August, Chase July and Chase August;
  3. code the rest (Needs Category suggestions, which accept TINO $8,000 against PO-2026-047; the Amazon line
     to 121 State materials) and close August;
  4. post late changes while August is closed (a late card line, a bill re-dated, the payroll run approved),
     reopen August, let the Demo Feed bring its August lines and recode one line, and re-close.
Each part opens a fresh page (fresh IndexedDB, so the demo seeds load again).

  python3 closetie_test.py            all parts
  python3 closetie_test.py -k close   only parts whose name contains "close"
"""
import asyncio, sys, re
from harness import *

AUG = ['2026-08-01', '2026-08-31']
SEP = ['2026-09-01', '2026-09-30']

# In-page helpers for the month-end. They call the app's own functions, the ones the buttons call.
LIB = r"""
() => {
  const bill = n => DB.bills.find(b => b.number === n);
  const tx = id => DB.txns.find(t => t.id === id);
  const p = id => DB.projects.find(x => x.id === id);
  const csvOf = L => 'Date,Description,Amount\n' + L.map(t => `${t.date.slice(5, 7)}/${t.date.slice(8)}/${t.date.slice(0, 4)},"${t.desc}",${(-t.amt).toFixed(2)}`).join('\n');
  async function importCsv(acct, name, lines, from, to, ending) {
    bfImportDialog(acct);
    await bfImportRead(name, csvOf(lines));
    bfImportState.flip = true;
    bfImportState.from = from; bfImportState.to = to;
    bfImportState.ending = ending == null ? '' : String(ending);
    const ok = bfImportRun();
    try { mbCloseModal(); } catch (e) {}
    return ok ? DB.bankImports.slice(-1)[0] : null;
  }
  function reconcile(acct, end, impId) {
    const I = DB.bankImports.find(i => i.id === impId);
    bfReconOpen(acct, end, I.ending, impId);
    return bfReconFinish();
  }
  async function connectDemo(inst) {
    // The Connect a Bank dialog, Demo Feed: the same steps its Connect button runs.
    bfConnect();
    const sel = document.querySelector('#bfc-inst');
    sel.value = inst; sel.dispatchEvent(new Event('change'));
    document.querySelector('#mbm-ok').click();
    for (let i = 0; i < 50 && !(DB.bankFeeds || []).some(f => f.sandbox === inst && f.lastSync); i++) await new Promise(r => setTimeout(r, 100));
    return (DB.bankFeeds || []).find(f => f.sandbox === inst);
  }
  function augCost() {
    const M = companyPL(['2026-08-01', '2026-08-31']).cogsT, G = glPL('all', '2026-08-01', '2026-08-31').cogsT;
    return [M, G];
  }
  function sepCost() {
    const M = companyPL(['2026-09-01', '2026-09-30']).cogsT, G = glPL('all', '2026-09-01', '2026-09-30').cogsT;
    return [M, G];
  }
  async function monthEnd() {
    const out = {};
    out.short = pay3ShortPay(bill('WW-2026-118'), 29700, 'credit memo requested for the 10th unit');
    out.amp = fin2ApproveAsBilled(bill('AMP-311'), 'COI renewal received by email, W-9 requested');
    // The bank's August file: every Amex line in the register but the second dumpster charge (ta7).
    const amex = DB.txns.filter(t => t.acct === 'ac2' && t.date >= '2026-08-01' && t.date <= '2026-08-31' && t.id !== 'ta7');
    const a2 = DB.accounts.find(a => a.id === 'ac2');
    const owed = r2(-((+a2.opening || 0) + DB.txns.filter(t => t.acct === 'ac2' && t.date <= '2026-08-31' && t.id !== 'ta7').reduce((s, t) => s + t.amt, 0)));
    const imp = await importCsv('ac2', 'Amex_Activity_Aug2026.csv', amex, '2026-08-01', '2026-08-31', owed);
    out.imported = imp && imp.confirmed;
    out.recAmex = reconcile('ac2', '2026-08-31', imp.id).ok;
    out.recJul = reconcile('ac1', '2026-07-31', 'imp_ac1_202607').ok;
    out.recAug = reconcile('ac1', '2026-08-31', 'imp_ac1_202608').ok;
    out.committedBefore = jobFin(p('p121')).committed;
    out.accepted = pay3AcceptAll();
    out.committedAfter = jobFin(p('p121')).committed;
    out.tinoPO = (tx('t13') || {}).poId;
    const t = tx('tsp1'); t.cat = 'materials'; t.projectId = 'p121'; t.code = '03'; t.status = 'categorized'; t.actor = 'Alan';
    save();
    return out;
  }
  window.CT = {bill, tx, p, csvOf, importCsv, reconcile, connectDemo, augCost, sepCost, monthEnd};
  return true;
}
"""

async def page(p):
    b, pg, errs = await open_app(p)
    await sign_in(pg, 'u_owner')
    await pg.evaluate(LIB)
    return b, pg, errs

async def text(pg):
    return await pg.evaluate("() => document.body.innerText")

async def view_text(pg, v, tab=None, extra=''):
    await pg.evaluate("([v, tab, extra]) => { if (tab) { try { glTab = tab } catch (e) {} } if (extra) (0, eval)(extra); view = v; render(); }", [v, tab, extra])
    await pg.wait_for_timeout(250)
    return await pg.evaluate("v => { const el = document.getElementById('v-' + v); return el ? el.innerText : document.body.innerText }", v)

money_re = lambda v: re.escape('$' + f'{v:,.0f}')

# ---------------------------------------------------------------- parts
async def part_feed(p, c):
    """#5 Honest Demo Feed: a fixed bank file, not an echo of the register; Demo Feed lines are not bank evidence."""
    b, pg, errs = await page(p)
    r0 = await pg.evaluate("() => { const C = bfCoverage('2026-08'); return [C.pct, C.backed, C.n] }")
    c.ok(r0[0] == 54, f"#5 August coverage before the Demo Feed {r0} (want 54%)")
    r = await pg.evaluate("""async () => {
      const ids0 = new Set(DB.txns.map(t => t.id));
      const f = await CT.connectDemo('amex');
      const C = bfCoverage('2026-08');
      const added = DB.txns.filter(t => !ids0.has(t.id));
      const fixed = BF_SANDBOX.amex.lines.filter(l => l.step === 0 && !l.pending && !l.removed).map(l => l.ref);
      const words = DB.txns.filter(t => t.acct === 'ac2' && t.date >= '2026-08-01' && t.date <= '2026-08-31').map(t => bfSourceWords(t).text);
      const demoConfirmed = DB.txns.filter(t => { const pv = bfProv(t); return pv.confirmedBy && pv.confirmedBy.demo; }).length;
      const backedDemo = DB.txns.filter(t => bfIsDemoOnly(t) && bfBacked(t)).length;
      bfReconOpen('ac2', '2026-08-31', -10000, '');
      const ticksDemo = DB.txns.filter(t => bfIsDemoOnly(t) && bfRec.ticks.has(t.id)).length;
      bfRec = null;
      const close = closeChecklist('2026-08').map(i => i.label).find(l => /backed by a bank record/.test(l)) || '';
      return {pct: C.pct, backed: C.backed, n: C.n, demo: C.demo, added: added.map(t => [t.date, t.amt, t.desc, (bfProv(t).feedTxnId || '')]),
              fixed, words, demoConfirmed, backedDemo, ticksDemo, close, feed: !!f,
              sub: bfCoverSub(C)};
    }""")
    c.ok(r['feed'], '#5 Demo Feed did not connect through the Connect a Bank dialog')
    c.ok(r['pct'] == 51 and r['n'] == 33, f"#5 August coverage after the Demo Feed {r['pct']}% ({r['backed']} of {r['n']}), want 51% (17 of 33), never 96%")
    c.ok(r['demoConfirmed'] == 0, f"#5 the Demo Feed confirmed {r['demoConfirmed']} typed lines: it echoed the register instead of serving its fixed file")
    c.ok(not [a for a in r['added'] if abs(a[1] + 1650) < 0.01], f"#5 the Demo Feed added a duplicate dumpster charge {r['added']}")
    c.ok(sorted(a[3] for a in r['added']) == sorted(r['fixed']), f"#5 the Demo Feed added {r['added']}, want exactly its fixed file {r['fixed']}")
    c.ok(r['words'].count('Demo Feed') == 2, f"#5 August Amex lines from the Demo Feed should read 'Demo Feed': {r['words']}")
    c.ok(r['backedDemo'] == 0 and r['ticksDemo'] == 0, f"#5 Demo Feed lines counted as backed ({r['backedDemo']}) or ticked at reconcile ({r['ticksDemo']})")
    c.ok('Demo Feed' in r['sub'], f"#5 coverage line does not name the Demo Feed lines: {r['sub']}")
    c.ok('51%' in r['close'], f"#5 close checklist coverage line: {r['close']}")
    t = await view_text(pg, 'bank')
    c.ok('Demo Feed' in t and '96%' not in t, '#5 Banking does not show the Demo Feed lines as such, or shows 96%')
    c.ok(not errs, f'#5 errors {errs[:3]}')
    await b.close()

async def part_outside(p, c):
    """#8 Outside the P&L counts only the bank leg of a card payment or transfer."""
    b, pg, errs = await page(p)
    r = await pg.evaluate("() => { const P = companyPL(['2026-01-01', today()]); return [P.nonT, P.non] }")
    c.ok(abs(r[0] - 42012.80) < 0.01, f"#8 Outside the P&L YTD {r[0]} {r[1]} (want $42,012.80, not $84,025.60)")
    t = await pg.evaluate("() => { cfoPeriod = 'ytd'; repTab = 'company'; view = 'reports'; render(); return document.getElementById('v-reports').innerText }")
    m = re.search(r'Outside the P&L:[^\n]*', t)
    c.ok(m and '$42,013' in m.group(0) and '84,026' not in m.group(0), f"#8 Reports > Company reads: {m.group(0) if m else 'no Outside the P&L line'}")
    c.ok(not errs, f'#8 errors {errs[:3]}')
    await b.close()

async def part_budget(p, c):
    """#6 Budget governance in the functions, and CSV export / import with a column-mapping preview."""
    b, pg, errs = await page(p)
    r = await pg.evaluate("""() => {
      const v = budActiveVer(), out = {};
      const a0 = budPlan().audit.length;
      const acct = Object.keys(v.lines)[0].split('|'), ent = acct[0], ac = acct[1];
      const cell = () => budMonth(v, ent, ac, 3);
      const before = cell();
      signIn('u_alan');
      out.pmSet = budSetCell(v, ent, ac, 3, before + 999);
      out.pmSpread = budSpreadApply(v, ent, ac, 12000, 'even');
      out.pmCopy = budCopyApply(v, 'actuals', ent);
      out.pmRefresh = budRefreshJobs(v);
      out.pmNew = budNewVersion('PM draft', v.id);
      out.pmLock = budLock(v, 'no');
      out.pmActive = budMakeActive(v);
      out.unchanged = cell() === before;
      signIn('u_controller');
      const d = budNewVersion('Reforecast Q4', v.id);
      out.ctrlNew = !!(d && d.id);
      out.ctrlSet = budSetCell(d, ent, ac, 3, before + 1);
      out.ctrlActive = budMakeActive(d);
      out.ctrlLock = budLock(d, 'board copy');
      out.lockedSet = budSetCell(d, ent, ac, 3, before + 2);
      out.lockedSpread = budSpreadApply(d, ent, ac, 5000, 'even');
      out.lockedCopy = budCopyApply(d, 'actuals', ent);
      out.lockedRefresh = budRefreshJobs(d);
      signIn('u_owner');
      out.ownerActive = budMakeActive(d);
      out.active = budActiveVer().id === d.id;
      const A = budPlan().audit.slice(a0);
      out.refusals = A.filter(x => x.act === 'refused').length;
      out.csv = budExportCsv(v);
      return out;
    }""")
    refused = lambda x: x is not None and not (x is True) and (x is False or (isinstance(x, dict) and x.get('ok') is False) or x == 0 or x == -1)
    for k in ['pmSet', 'pmSpread', 'pmCopy', 'pmRefresh', 'pmLock', 'pmActive', 'ctrlActive', 'lockedSet', 'lockedSpread', 'lockedCopy', 'lockedRefresh']:
        c.ok(refused(r[k]), f"#6 budget {k} was not refused: {r[k]}")
    c.ok(not r['pmNew'], f"#6 a PM created a budget version: {r['pmNew']}")
    c.ok(r['unchanged'], '#6 a refused edit changed the budget')
    c.ok(r['ctrlNew'] and isinstance(r['ctrlSet'], dict) and r['ctrlSet'].get('ok'), f"#6 the controller could not edit an open draft: {r['ctrlSet']}")
    c.ok(isinstance(r['ownerActive'], dict) and r['ownerActive'].get('ok') and r['active'], '#6 the Owner could not make a version active')
    c.ok(r['refusals'] >= 12, f"#6 each refusal writes an audit row: {r['refusals']} refusal rows")
    csv = r['csv'] or ''
    c.ok(csv.startswith('Entity,Account,Name,Jan') and csv.count('\n') >= 5, f"#6 CSV export: {csv[:120]!r}")
    # The toast for a refusal, and the import dialog with its column-mapping preview.
    t = await pg.evaluate("""() => { signIn('u_alan'); const v = budActiveVer(); const k = Object.keys(v.lines)[0].split('|');
      budSetCell(v, k[0], k[1], 2, 1); const tt = (document.getElementById('toast') || {}).innerText || ''; signIn('u_owner'); return tt; }""")
    c.ok(re.search(r'Owner or the controller|locked', t or ''), f"#6 refusal toast: {t!r}")
    r = await pg.evaluate("""() => {
      const v = budNewVersion('Import test', budActiveVer().id);
      const csv = 'Acct No,Description,Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec,Company\\n7100,Rent,1300,1300,1300,1300,1300,1300,1300,1300,1300,1300,1300,1300,ent1\\n';
      budImportDialog(v);
      budImportRead('reforecast.csv', csv);
      const m = document.getElementById('mbm');
      const preview = m ? m.innerText : '';
      const selects = m ? m.querySelectorAll('[data-budmap]').length : 0;
      document.querySelector('#mbm-ok').click();
      return {preview, selects, after: budMonth(v, 'ent1', '7100', 4), audit: budPlan().audit.slice(-1)[0].act};
    }""")
    c.ok(r['selects'] >= 3 and 'Acct No' in r['preview'], f"#6 CSV import shows no column mapping: {r['preview'][:200]!r}")
    c.ok(re.search(r'1 account line', r['preview']) is not None, f"#6 CSV import preview does not say what will change: {r['preview'][:300]!r}")
    c.ok(abs((r['after'] or 0) - 1300) < 0.01 and r['audit'] == 'imported', f"#6 CSV import did not apply: {r}")
    c.ok(not errs, f'#6 errors {errs[:3]}')
    await b.close()

async def part_void(p, c):
    """#11 A typed line the bank's statement lacks: Not at the Bank — Void, with a reason; the ledger reverses it."""
    b, pg, errs = await page(p)
    r = await pg.evaluate("""async () => {
      const amex = DB.txns.filter(t => t.acct === 'ac2' && t.date >= '2026-08-01' && t.date <= '2026-08-31' && t.id !== 'ta7');
      const a2 = DB.accounts.find(a => a.id === 'ac2');
      const owed = r2(-((+a2.opening || 0) + DB.txns.filter(t => t.acct === 'ac2' && t.date <= '2026-08-31' && t.id !== 'ta7').reduce((s, t) => s + t.amt, 0)));
      const imp = await CT.importCsv('ac2', 'Amex_Activity_Aug2026.csv', amex, '2026-08-01', '2026-08-31', owed);
      glSync();
      const before = glPL('all', '2026-08-01', '2026-08-31').cogsT;
      bfReconOpen('ac2', '2026-08-31', imp.ending, imp.id);
      const host = document.getElementById('bf-recon');
      const btn = host && [...host.querySelectorAll('button')].find(x => /Not at the Bank/.test(x.innerText) && x.closest('[data-bfrow="ta7"]'));
      const label = btn ? btn.innerText : '';
      const noWhy = bfVoidNotAtBank('ta7', '');
      const ok = bfVoidNotAtBank('ta7', 'Amex charged the dumpster once; the second line was typed twice');
      glSync();
      const after = glPL('all', '2026-08-01', '2026-08-31').cogsT;
      const t = DB.txns.find(x => x.id === 'ta7') || (DB.txnsVoid || []).find(x => x.id === 'ta7');
      const rev = DB.gl.journals.filter(j => j.key === 'txn:ta7');
      const list = closeChecklist('2026-08').find(i => /not at the bank/i.test(i.label));
      const fin = bfReconFinish();
      return {label, noWhy, ok, before, after, status: t && t.status, why: t && t.voidWhy, rev: rev.map(j => j.status), list: list && [list.label, list.n], fin: fin.ok};
    }""")
    c.ok(re.search(r'Not at the Bank', r['label']), f"#11 the reconcile row for the duplicate dumpster has no 'Not at the Bank — Void' button: {r['label']!r}")
    c.ok(not (r['noWhy'] or {}).get('ok'), '#11 Void went through without a reason')
    c.ok((r['ok'] or {}).get('ok') and r['status'] == 'void' and r['why'], f"#11 void: {r['ok']} status {r['status']}")
    c.ok(abs(r['before'] - r['after'] - 1650) < 0.01, f"#11 the ledger did not reverse the $1,650: {r['before']} -> {r['after']}")
    c.ok(r['list'] and r['list'][1] == 0, f"#11 close checklist item for lines the statement lacks: {r['list']}")
    c.ok(r['fin'], '#11 the reconciliation did not finish after the void')
    c.ok(not errs, f'#11 errors {errs[:3]}')
    await b.close()

async def part_close(p, c):
    """#1, #3, #7, #9, #10, #12, #2 and the Ask functions: the month-end, the close, the late changes, the re-close."""
    b, pg, errs = await page(p)
    r = await pg.evaluate("() => CT.monthEnd()")
    c.ok(r['short'] and r['amp'] and r['recAmex'] and r['recJul'] and r['recAug'], f"month-end setup {r}")
    # #3 PO relief: TINO $8,000 accepted against PO-2026-047 relieves the PO in committed.
    c.ok(r['tinoPO'] == 'po3', f"#3 TINO was not matched to PO-2026-047: {r['tinoPO']}")
    c.ok(r['committedBefore'] == 46010 and r['committedAfter'] == 38010, f"#3 121 State committed {r['committedBefore']} -> {r['committedAfter']} (want 46,010 -> 38,010)")
    r = await pg.evaluate("""() => { const J = jobFin(CT.p('p121')); const row = J.byCode.find(x => x.code === '09') || {}; return [J.committed, row.committed] }""")
    c.ok(r[0] == 38010 and abs(r[1] or 0) < 10.01, f"#3 by-code committed for 09 still carries the relieved PO: {r}")

    # #1 the close: wages post, then the WIP is planned; the tie-out passes; the frozen read ties to 2500.
    r = await pg.evaluate("""() => {
      const r = fin2RunClose('2026-08', 'September lines are coded next month; budget commentary follows');
      if (!r.ok) return {why: r.why};
      const kinds = r.posted.map(j => j.kind + ':' + (j.accrues || ''));
      const tie = ctWipTie('2026-08');
      const J = id => jobFin(CT.p(id), ['', '2026-08-31']);
      const bal = (acct, pid) => { const B = glBalances({entityId: 'all', to: '2026-08-31', acct, projectId: pid}); return B[acct] ? B[acct].bal : 0; };
      return {kinds, tie, j121: J('p121').overUnder, j45: J('p45').overUnder, l121: bal('2500', 'p121') - bal('1200', 'p121'), l45: bal('2500', 'p45') - bal('1200', 'p45'),
              lab45: J('p45').laborCost, status: ctCloseStatus('2026-08'), acc: ctAccrualAtClose('2026-08'), hist: ctCloseHistory(), cost: CT.augCost()};
    }""")
    c.ok('why' not in r, f"#1 the August close refused: {r.get('why')}")
    if 'why' in r:
        await b.close(); return
    k = r['kinds']
    c.ok(k.index('close:wip') > max(i for i, x in enumerate(k) if x.startswith('accrual')), f"#1 the WIP was planned before the wages posted: {k}")
    c.ok(abs(r['j121'] - 62466.02) < 0.005 and abs(r['l121'] - 62466.02) < 0.005, f"#1 121 State WIP schedule {r['j121']} / 2500 {r['l121']} (want 62,466.02 both)")
    c.ok(abs(r['j45'] - 6323.09) < 0.005 and abs(r['l45'] - 6323.09) < 0.005, f"#1 45 Cranberry WIP schedule {r['j45']} / 2500 {r['l45']} (want 6,323.09 both)")
    c.ok(r['tie'] and r['tie']['ok'] and all(abs(x['diff']) < 0.005 for x in r['tie']['rows']), f"#1 ctWipTie {r['tie']}")
    c.ok(abs(r['lab45'] - 5667.29) < 0.01, f"#10 45 Cranberry labor at run burden {r['lab45']} (want 5,667.29, not 5,790 standard)")
    c.ok(r['status']['closed'] and r['status']['month'] == '2026-08' and 'closed' in r['status']['headline'].lower(), f"Ask ctCloseStatus {r['status']}")
    c.ok(abs(r['acc']['total'] - 19739) < 0.01 and any(abs(x['amt'] - 3699) < 0.01 for x in r['acc']['time']), f"Ask ctAccrualAtClose {r['acc']}")
    c.ok(len(r['hist']) == 1 and r['hist'][0]['act'] == 'closed', f"Ask ctCloseHistory {r['hist']}")
    c.ok(abs(r['cost'][0] - r['cost'][1]) < 0.01, f"#2 August cost at the first close: management {r['cost'][0]} vs ledger {r['cost'][1]}")
    first_aug = r['cost'][0]

    # The Pack for August reads the ledger; the Close page shows the WIP Tie-Out.
    t = await pg.evaluate("() => { packMonth = '2026-08'; repTab = 'pack'; view = 'reports'; render(); const h = document.getElementById('v-reports').innerText; packMonth = ''; return h }")
    c.ok('$62,466' in t and '$6,323' in t and '$67,326' not in t, f"#1 the August Pack WIP: 121 State $62,466 and 45 Cranberry $6,323 expected (Pack equals the ledger)")
    c.ok('$5,667' in t and '$5,790' not in t, '#10 the August Pack labor is not at run burden ($5,667, not $5,790)')
    t = await view_text(pg, 'gl', 'periods')
    c.ok('wip tie-out' in t.lower() and '62,466.02' in t and '6,323.09' in t, '#1 the Close page has no WIP Tie-Out table for closed August')
    c.ok('unallocated labor' in t.lower(), '#10 the Close page does not say Unallocated Labor')
    # #9 orphan accrual: $3,699 for 8/4-8/13, flagged once the next pay date (9/1) passed.
    r = await pg.evaluate("() => ctOrphanAccruals()")
    c.ok(len(r) == 1 and abs(r[0]['amt'] - 3699) < 0.01 and r[0]['from'] == '2026-08-04' and r[0]['to'] == '2026-08-13' and r[0]['flagged'], f"#9 ctOrphanAccruals {r}")
    c.ok(re.search(r'no payroll run', t) and '3,699' in t and 'Record the Run' in t and 'Reverse' in t, '#9 the orphan accrual is not flagged on the Close page with Record the Run and Reverse')
    t2 = await view_text(pg, 'ap')
    c.ok('3,699' in t2 and 'Record the Run' in t2, '#9 the orphan accrual is not on Bills & Payroll')
    r = await pg.evaluate("() => closeChecklist('2026-09').map(i => [i.label, i.n])")
    c.ok(any(re.search(r'no payroll run', x[0]) and x[1] == 1 for x in r), f"#9 the close checklist does not list the orphan accrual: {r}")
    r = await pg.evaluate("() => { const j = ctOrphanAccruals()[0]; return ctOrphanReverse(j.id, '') }")
    c.ok(not (r or {}).get('ok'), '#9 Reverse went through without a reason')
    # Ask functions are entities in erpQuery.
    r = await pg.evaluate("() => [erpQuery({entity: 'closes'}).rows.length, erpQuery({entity: 'wiptie'}).rows.length, erpQuery({entity: 'orphanaccruals'}).rows.length]")
    c.ok(r[0] >= 1 and r[1] >= 2 and r[2] == 1, f"Ask: erpQuery closes / wiptie / orphanaccruals rows {r}")
    # #7 the bridge after the close.
    t = await view_text(pg, 'gl', 'overview')
    c.ok('await approval and are in neither' not in t, '#7 the bridge still says the payroll awaits approval and is in neither, after the close accrued it')
    c.ok('WIP over/under-billing adjustment not yet posted' not in t, '#7 the bridge still reads "not yet posted (posts at the month close)" after the close')
    if re.search(r'WIP movement', t):
        c.ok('WIP movement since the August 2026 close' in t, '#7 WIP bridge wording')

    # #2 late changes while August is closed.
    r = await pg.evaluate("""async () => {
      const out = {};
      // a late card line: the Amex file for early September carries an August charge the bank posted late
      const late = [{date: '2026-08-28', desc: 'NEMO TILE SUPPLY LATE POST', amt: -1000}];
      const imp = await CT.importCsv('ac2', 'Amex_Activity_Sep2026.csv', late, '2026-08-28', '2026-09-03', null);
      const t = DB.txns.find(x => x.desc === 'NEMO TILE SUPPLY LATE POST');
      out.postOn = t && t.postOn; out.postOnWhy = t && t.postOnWhy;
      t.cat = 'materials'; t.projectId = 'p121'; t.code = '08'; t.status = 'categorized'; save();
      out.postOn2 = t.postOn;
      // a bill edit: re-dating into the closed month is refused; within open months it needs a reason and keeps history
      const amp = CT.bill('AMP-311');
      out.intoClosed = billChangeDate(amp, '2026-08-30', 'paid in August');
      out.noWhy = billChangeDate(amp, '2026-09-01', '');
      out.moved = billChangeDate(amp, '2026-09-01', 'the invoice is dated the 1st; the 2nd was the scan date');
      out.hist = amp.dateHistory;
      // the payroll run approved (review of the split, coverage under 80%)
      const pr = DB.payroll.find(x => x.id === 'pr1');
      payrollAction(pr, 'approve', 'office staff are salaried; the crew hours for that fortnight are in');
      out.pr = pr.status;
      out.aug = CT.augCost(); out.sep = CT.sepCost();
      out.closedRead = !!companyPL(['2026-08-01', '2026-08-31']).closedRead;
      return out;
    }""")
    c.ok(r['postOn'] == '2026-09-01' and r['postOnWhy'], f"#2 the late card line is not stamped postOn 2026-09-01: {r['postOn']} {r['postOnWhy']}")
    c.ok(r['postOn2'] == '2026-09-01', f"#2 recoding the late line lost its posting period {r['postOn2']}")
    c.ok(not (r['intoClosed'] or {}).get('ok') and not (r['noWhy'] or {}).get('ok'), f"#12 Change Date into a closed month or without a reason went through: {r['intoClosed']} {r['noWhy']}")
    c.ok((r['moved'] or {}).get('ok') and r['hist'] and r['hist'][-1]['from'] == '2026-09-02' and r['hist'][-1]['to'] == '2026-09-01' and r['hist'][-1]['why'], f"#12 Change Date history {r['hist']}")
    c.ok(r['pr'] in ('approved', 'verified', 'paid'), f"payroll approval {r['pr']}")
    c.ok(abs(r['aug'][0] - first_aug) < 0.01 and abs(r['aug'][1] - first_aug) < 0.01, f"#2 August moved while closed: {r['aug']} (was {first_aug})")
    c.ok(abs(r['sep'][0] - r['sep'][1]) < 0.01, f"#2 September management {r['sep'][0]} vs ledger {r['sep'][1]} while August is closed")
    # #12 the Change Date dialog on the bill
    t = await pg.evaluate("() => { openBill(CT.bill('AMP-311').id); const h = document.getElementById('d-body').innerText; const btn = [...document.querySelectorAll('#d-body button, #drawer button')].find(b => /^Change Date/.test(b.innerText)); if (btn) btn.click(); const m = document.getElementById('mbm'); const r = [h, m ? m.innerText : '']; try { mbCloseModal(); } catch (e) {} try { closeEditor(); } catch (e) {} return r }")
    c.ok(re.search(r'Change Date', t[1] or '') and re.search(r'Reason', t[1] or ''), f"#12 no Change Date… dialog with a reason on the bill: {t[1][:200]!r}")
    c.ok('scan date' in (t[0] or ''), '#12 the bill does not show its date history')

    # Reopen August, the Demo Feed brings its August lines, one line is recoded, re-close.
    r = await pg.evaluate("""async () => {
      const out = {};
      out.reopen = fin2ReopenClose('2026-08', 'the Amex feed carries August lines not yet in the books').ok;
      out.status = ctCloseStatus('2026-08');
      const ids0 = new Set(DB.txns.map(t => t.id));
      await CT.connectDemo('amex');
      const added = DB.txns.filter(t => !ids0.has(t.id));
      added.forEach(t => { if (t.date <= '2026-08-31') { t.cat = 'materials'; t.status = 'categorized'; if (/FERGUSON/.test(t.desc)) { t.projectId = 'p121'; t.code = '05'; } else { t.projectId = ''; } } });
      out.added = added.map(t => [t.date, t.amt, t.desc, t.postOn || '']);
      const a = CT.tx('tsp1'); a.cat = 'office'; a.projectId = ''; a.code = ''; save();
      const late = DB.txns.find(x => x.desc === 'NEMO TILE SUPPLY LATE POST');
      out.latePostOn = late.postOn;
      const r = fin2RunClose('2026-08', 'September lines are coded next month');
      out.reclose = r.ok || r.why;
      out.tie = ctWipTie('2026-08').ok;
      out.aug = CT.augCost(); out.sep = CT.sepCost();
      const rows = companyPL(['2026-09-01', '2026-09-30']).L.filter(x => x.ref && x.ref.desc === 'NEMO TILE SUPPLY LATE POST');
      out.lateInSepM = rows.reduce((s, x) => s + x.amt, 0);
      out.lateInSepL = glLines({entityId: 'all', from: '2026-09-01', to: '2026-09-30'}).filter(l => l.j.sourceId === late.id && /^5/.test(l.acct)).reduce((s, l) => s + l.dr - l.cr, 0);
      out.hist = ctCloseHistory().map(h => h.act + (h.again ? ' again' : ''));
      return out;
    }""")
    c.ok(r['reopen'] and not r['status']['closed'], f"reopen August {r['reopen']} {r['status']}")
    c.ok(r['reclose'] is True and r['tie'], f"re-close {r['reclose']} tie {r['tie']}")
    c.ok(r['latePostOn'] == '2026-09-01', f"#2 reopening August dropped the late line's posting period: {r['latePostOn']}")
    c.ok(abs(r['aug'][0] - 103305.11) < 0.005 and abs(r['aug'][1] - 103305.11) < 0.005, f"#2 August cost after reopen and re-close: management {r['aug'][0]} / ledger {r['aug'][1]} (want 103,305.11 both)")
    c.ok(abs(r['sep'][0] - r['sep'][1]) < 0.01, f"#2 September cost: management {r['sep'][0]} / ledger {r['sep'][1]}")
    c.ok(abs(r['lateInSepM'] - 1000) < 0.01 and abs(r['lateInSepL'] - 1000) < 0.01, f"#2 September carries the late $1,000: management {r['lateInSepM']} / ledger {r['lateInSepL']}")
    c.ok(r['hist'] == ['closed', 'reopened', 'closed again'], f"Ask ctCloseHistory after re-close {r['hist']}")
    c.ok(not errs, f'close errors {errs[:3]}')
    await b.close()

async def part_tieblock(p, c):
    """#1 The blocking tie-out: when the posted WIP does not equal the schedule, the close refuses, reverses
    what it posted and locks nothing."""
    b, pg, errs = await page(p)
    r = await pg.evaluate("""async () => {
      await CT.monthEnd();
      const keep = fin2WipLines;
      fin2WipLines = (plan, ent) => keep(plan, ent).filter(l => l.projectId !== 'p45');
      let r;
      try { r = fin2RunClose('2026-08', 'testing the tie-out'); } finally { fin2WipLines = keep; }
      const live = DB.gl.journals.filter(j => j.periodYm === '2026-08' && ['close', 'accrual'].includes(j.kind) && j.status === 'posted');
      const bal = (acct, pid) => { const B = glBalances({entityId: 'all', to: '2026-08-31', acct, projectId: pid}); return B[acct] ? B[acct].bal : 0; };
      return {ok: r.ok, why: r.why || '', locked: lockedThrough(), anyLock: isLocked('2026-08-15'), live: live.length, w121: bal('2500', 'p121'), acc: bal('2200', '')};
    }""")
    c.ok(not r['ok'] and re.search(r'tie|WIP', r['why'] or ''), f"#1 the close did not refuse on a tie-out difference: {r}")
    c.ok(r['locked'] == '' and not r['anyLock'], f"#1 a refused close locked something: {r}")
    c.ok(r['live'] == 0 and abs(r['w121']) < 0.005, f"#1 a refused close left entries posted: {r}")
    c.ok(not errs, f'#1 tie-out errors {errs[:3]}')
    await b.close()

async def part_orphan(p, c):
    """#9 Record the Run and Reverse… on the orphan accrual."""
    b, pg, errs = await page(p)
    r = await pg.evaluate("""async () => {
      await CT.monthEnd();
      fin2RunClose('2026-08', 'September lines are coded next month');
      const j = ctOrphanAccruals()[0];
      const run = ctOrphanRecordRun(j.id);
      const out = {run: run && [run.from, run.to, run.status, (run.alloc || []).map(a => a.projectId)]};
      const rv = ctOrphanReverse(j.id, 'the 8/4-8/13 hours were paid by the studio retainer, not payroll');
      out.rev = rv;
      out.left = ctOrphanAccruals().length;
      out.journal = DB.gl.journals.filter(x => x.reversalOf === j.id).map(x => [x.date, x.memo]);
      return out;
    }""")
    c.ok(r['run'] and r['run'][0] == '2026-08-04' and r['run'][1] == '2026-08-13' and 'p45' in r['run'][3], f"#9 Record the Run {r['run']}")
    c.ok((r['rev'] or {}).get('ok') and r['left'] == 0 and r['journal'] and r['journal'][0][0] >= '2026-09-01', f"#9 Reverse {r}")
    c.ok(not errs, f'#9 errors {errs[:3]}')
    await b.close()

PARTS = [('feed', part_feed), ('outside', part_outside), ('budget', part_budget), ('void', part_void),
         ('close', part_close), ('tieblock', part_tieblock), ('orphan', part_orphan)]

async def main():
    only = sys.argv[sys.argv.index('-k') + 1] if '-k' in sys.argv else ''
    c = Checks()
    async with async_playwright() as p:
        for name, fn in PARTS:
            if only and only not in name: continue
            n0, f0 = c.n, len(c.fail)
            try:
                await fn(p, c)
            except Exception as e:
                c.ok(False, f'{name}: {type(e).__name__}: {str(e)[:300]}')
            print(f'-- {name}: {c.n - n0} checks, {len(c.fail) - f0} failed')
    sys.exit(c.done())
if __name__ == '__main__':
    asyncio.run(main())
