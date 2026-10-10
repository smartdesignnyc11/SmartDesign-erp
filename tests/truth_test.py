"""truth (BACKLOG §1.6, CLAUDE.md "Financial truth"): the ERP's financials are the single source of truth.

Every item is proven by driving the real flows from a fresh boot (fresh seed, app day 2026-09-03): a bank CSV
through the Import Statement dialog, a bill through the New Bill drawer, a manual journal through the Ledger's
entry form, an amendment of a posted invoice, a delete attempt on posted records, a month close. Each section
starts from a fresh browser.

  python3 truth_test.py                  all sections
  python3 truth_test.py cov manual       only the named sections (cov, manual, tamper, match, qbo, guard)

Sections:
  cov     every cost and income figure carries its coverage: bank/card-backed, document-backed (accrual), by hand;
          the same three amounts on Statements, the Pack, the job report, the Ledger overview and Ask; the Demo
          Feed never counts as bank evidence
  manual  a manual journal is drafted by the Controller, posted by the Owner with a typed reason, and flagged on
          ledger rows, statement lines (count and amount, with a drill-down), the Pack, the Flash, the close
          checklist and Ask
  tamper  posted records are append-only: an amendment is a linked reversal and re-post with who/when/why and a
          History strip; delete is refused; void is a reversal with a reason; a per-period hash chain is sealed
          at close and Verify the Books names a changed or missing posting
  match   one link model for every transaction (bill/PO line and its estimate line, invoice line, payroll run),
          PRED.unmatchedTxns per month and total on Banking, Home (Caught for You), the close checklist and Ask;
          automatic proposals where amount, vendor and date agree, confirmed by a person; a close refuses while
          unmatched lines carry no signed exception
  qbo     a QuickBooks snapshot loads through the app's own import paths (idempotent, source: quickbooks), then
          the Three-Way Tie-Out (QuickBooks says / the bank says / the ERP says) per month and account group
  guard   *.qbo.json is ignored by git; the harness refuses a snapshot path inside the repo

All demo data here is invented."""
import asyncio, json, os, re, sys, tempfile
from harness import *

ONLY = set(sys.argv[1:])
want = lambda s: not ONLY or s in ONLY
AUG = "['2026-08-01', '2026-08-31']"
MONEY = r'[−\-]?\$[\d,]+(?:\.\d{2})?'


async def fresh(p, uid='u_owner'):
    b, pg, errs = await open_app(p)
    await sign_in(pg, uid)
    return b, pg, errs


async def text_of(pg, view):
    return await pg.evaluate("v => { const e = document.getElementById('v-' + v); return e ? e.innerText : '' }", view)


async def click_js(pg, sel):
    ok = await pg.evaluate("s => { const e = [...document.querySelectorAll(s)].find(x => x.offsetParent) || document.querySelector(s); if (!e) return false; e.click(); return true }", sel)
    await pg.wait_for_timeout(200)
    return ok


async def report(pg, tab, extra=None):
    """Open Reports on one tab (through the app's own tab state) and return the view's text."""
    await pg.evaluate("([t, x]) => { repTab = t; if (x && x.proj) repProj = x.proj; view = 'reports'; render(); }", [tab, extra or {}])
    await pg.wait_for_timeout(150)
    return await text_of(pg, 'reports')


async def ledger(pg, tab, stmt=None):
    await pg.evaluate("([t, s]) => { glTab = t; if (s) glStmt = s; glEnt = 'all'; view = 'gl'; render(); }", [tab, stmt])
    await pg.wait_for_timeout(150)
    return await text_of(pg, 'gl')


async def ask(pg, q):
    return await pg.evaluate("""async q => { let a = paAsk(q); if (a && a.then) a = await a; a = a || {};
        return { headline: a.headline || '', text: [a.headline || '', a.note || '', (a.work || []).map(w => typeof w === 'string' ? w : (w.t || w.text || JSON.stringify(w))).join('\\n')].join('\\n') } }""", q)


def csv(rows):
    return 'Date,Description,Amount,Reference\n' + '\n'.join(f'{d},{desc},{amt:.2f},{ref}' for d, desc, amt, ref in rows) + '\n'


async def import_statement(pg, acct, name, text):
    """The real Import Statement dialog: open it, hand the file to its file input, press Import."""
    await pg.evaluate("a => { view = 'bank'; render(); bfImportDialog(a); }", acct)
    await pg.wait_for_selector('#bfi-file', state='attached', timeout=10000)
    await pg.set_input_files('#bfi-file', files=[{'name': name, 'mimeType': 'text/plain', 'buffer': text.encode()}])
    await pg.wait_for_function("() => { const b = document.querySelector('#mbm-ok'); return b && !b.disabled && /Import \\d/.test(b.textContent); }", timeout=10000)
    await pg.click('#mbm-ok')
    await pg.wait_for_timeout(250)
    return await pg.evaluate("n => (DB.bankImports || []).filter(i => i.fileName === n).map(i => ({added: i.added, confirmed: i.confirmed, dup: i.dup}))", name)


async def code_txn(pg, tid, cat, proj, code, memo, vendor=''):
    """The transaction drawer the Banking list opens: category, job, cost code, memo, Save."""
    await pg.evaluate("id => { if (document.querySelector('#drawer.on') && typeof closeEditor === 'function') closeEditor(); view = 'bank'; render(); txnDialog(id); }", tid)
    await pg.wait_for_selector('#e-cat', state='attached')
    await pg.select_option('#e-cat', cat)
    if proj: await pg.select_option('#e-proj', proj)
    if code: await pg.select_option('#e-code', code)
    await pg.fill('#e-memo', memo)
    if vendor: await pg.fill('#e-vendor', vendor)
    await pg.evaluate("() => { const g = document.querySelector('#d-save'); g && g.removeAttribute('disabled'); }")
    await pg.click('#d-save', timeout=5000)
    await pg.wait_for_timeout(200)


async def new_bill(pg, vendor, number, date, proj, cat, code, desc, amount, line=''):
    """A vendor bill through the New Bill drawer; returns the bill id."""
    await pg.evaluate("() => { if (document.querySelector('#drawer.on') && typeof closeEditor === 'function') closeEditor(); setCurrent('p121'); view = 'ap'; render(); openBill(); }")
    await pg.wait_for_selector('#e-vendor', state='attached')
    await pg.fill('#e-vendor', vendor)
    await pg.fill('#e-number', number)
    await pg.fill('#e-date', date)
    await pg.select_option('#e-proj', proj)
    await pg.select_option('#e-cat', cat)
    await pg.select_option('#e-code', code)
    if line:
        await pg.evaluate("l => { const s = document.querySelector('#e-line'); if (s && [...s.options].some(o => o.value === l)) s.value = l; }", line)
    await pg.evaluate("([d, a]) => { const tr = document.querySelector('tr[data-bl]'); tr.querySelector('[data-f=\"desc\"]').value = d; tr.querySelector('[data-f=\"amount\"]').value = String(a); }", [desc, amount])
    await pg.click('#d-save', timeout=5000)
    await pg.wait_for_timeout(200)
    bid = await pg.evaluate("n => (DB.bills.find(b => b.number === n) || {}).id || null", number)
    await pg.evaluate("() => { if (typeof closeEditor === 'function' && document.querySelector('#drawer.on')) closeEditor(); }")
    return bid


def has_money(text, v):
    """True when the text prints v as money ($1,234 or $1,234.56)."""
    v = abs(float(v))
    a = '${:,.0f}'.format(round(v)); b = '${:,.2f}'.format(v)
    return a in text or b in text


# ---------------------------------------------------------------- 1. coverage
async def sec_cov(p, c):
    b, pg, errs = await fresh(p)
    have = await pg.evaluate("() => typeof truthCoverage === 'function' && typeof truthBacking === 'function'")
    c.ok(have, 'truthCoverage / truthBacking exist (one function is the source of every coverage figure)')
    if not have: await b.close(); return
    C0 = await pg.evaluate(f"() => {{ const C = truthCoverage({AUG}), P = companyPL({AUG}); return {{ C, pl: r2(P.cogsT + P.ohT) }} }}")
    cost = C0['C']['cost']
    c.ok(abs(cost['bank'] + cost['document'] + cost['hand'] + (cost.get('adjust') or 0) - cost['total']) < 0.01,
         f"August cost coverage adds up: bank {cost['bank']} + document {cost['document']} + hand {cost['hand']} + adjust {cost.get('adjust')} = {cost['total']}")
    c.ok(abs(cost['total'] - C0['pl']) < 0.01, f"the coverage total {cost['total']} is the P&L cost {C0['pl']} (one figure)")
    inc = C0['C']['income']
    c.ok(abs(inc['bank'] + inc['document'] + inc['hand'] + (inc.get('adjust') or 0) - inc['total']) < 0.01 and inc['document'] >= 0,
         f"August income coverage adds up, the documents never negative: bank {inc['bank']} + document {inc['document']} + hand {inc['hand']} + adjustment {inc.get('adjust')} = {inc['total']}")
    # import a real statement: it confirms the typed Window Works card line and brings one new line
    out = await import_statement(pg, 'ac2', 'Amex_1009_Aug2026_truth.csv', csv([
        ('2026-08-25', 'SQ *WINDOW WORKS BKLYN', -33500.00, 'AMX-260825-01'),
        ('2026-08-26', 'ACME SCAFFOLD RENTAL', -1200.00, 'AMX-260826-02')]))
    c.ok(out and out[0]['confirmed'] == 1 and out[0]['added'] == 1, f'statement import: {out}')
    tid = await pg.evaluate("() => (DB.txns.find(t => t.desc === 'ACME SCAFFOLD RENTAL') || {}).id || null")
    c.ok(bool(tid), 'the new line is on the register')
    if tid:
        await code_txn(pg, tid, 'equipment', 'p121', '01', 'Rear facade scaffold, 4 weeks', 'Acme Scaffold')
        bk = await pg.evaluate("id => truthBacking(DB.txns.find(x => x.id === id))", tid)
        c.ok(bk['kind'] == 'bank', f'an imported, coded line is bank-backed: {bk}')
    C1 = await pg.evaluate(f"() => truthCoverage({AUG})")
    # the coded ACME line is new bank-backed cost; the Window Works card line pays bill WW-2026-118 ($33,500) through its PO,
    # so the bill's evidence moves from the document (accrual) to the bank; the typed-by-hand figure does not move
    c.ok(abs(C1['cost']['bank'] - cost['bank'] - 34700) < 0.01, f"bank-backed August cost rose by $1,200 + $33,500: {cost['bank']} -> {C1['cost']['bank']}")
    c.ok(abs(cost['document'] - C1['cost']['document'] - 33500) < 0.01, f"document-backed August cost fell by the bill now paid at the bank: {cost['document']} -> {C1['cost']['document']}")
    c.ok(abs(C1['cost']['hand'] - cost['hand']) < 0.01, f"by-hand August cost unchanged {cost['hand']} -> {C1['cost']['hand']}")
    rows = C1['cost']['rows']
    c.ok(all(r.get('why') for r in rows), 'every coverage row says why it is backed the way it is')
    # the Demo Feed never counts as bank evidence
    demo = await pg.evaluate("""() => { const o = bfIngest({kind: 'feed', acctId: 'ac2', feed: {id: 'f_demo_t', mode: 'demo'}, institution: 'Demo Bank'},
        [{ref: 'demo-t-1', date: '2026-08-20', amt: -500, desc: 'DEMO FEED SAW BLADES'}], []);
        const t = DB.txns.find(x => x.desc === 'DEMO FEED SAW BLADES'); return t ? t.id : null; }""")
    c.ok(bool(demo), 'a Demo Feed line arrived through bfIngest')
    if demo:
        await code_txn(pg, demo, 'materials', 'p121', '03', 'demo feed line, for the coverage test')
        bk = await pg.evaluate("id => truthBacking(DB.txns.find(x => x.id === id))", demo)
        c.ok(bk['kind'] != 'bank' and re.search('demo', bk['why'], re.I), f'a Demo Feed line is not bank evidence: {bk}')
        C2 = await pg.evaluate(f"() => truthCoverage({AUG})")
        c.ok(abs(C2['cost']['hand'] - C1['cost']['hand'] - 500) < 0.01 and abs(C2['cost']['bank'] - C1['cost']['bank']) < 0.01,
             f"the Demo Feed line counts as by hand: hand {C1['cost']['hand']} -> {C2['cost']['hand']}, bank unchanged")
        C1 = C2
    # the three amounts on every surface, each read for August
    k = C1['cost']
    await pg.evaluate("() => { REP.preset = 'lm'; }")   # the Reports period control: Last Month = August
    t = await report(pg, 'financials')
    rng = await pg.evaluate("() => { const e = document.querySelector('#v-reports .tr-cov'); return e ? e.dataset.trrange.split('|') : null; }")
    c.ok(rng == ['2026-08-01', '2026-08-31'], f'the Statements coverage card follows the report period: {rng}')
    c.ok(re.search(r'backed by a bank or card line', t, re.I) and has_money(t, k['bank']) and has_money(t, k['document']) and has_money(t, k['hand']),
         f"Reports > Statements shows cost coverage with the three amounts (bank {k['bank']}, document {k['document']}, hand {k['hand']})")
    t = await report(pg, 'pack')
    rng = await pg.evaluate("() => { const e = document.querySelector('#v-reports .tr-cov'); return e ? e.dataset.trrange.split('|') : null; }")
    kp = await pg.evaluate("R => R && truthCoverage(R).cost", rng)
    c.ok(rng and re.search(r'backed by a bank or card line', t, re.I) and has_money(t, kp['bank']) and has_money(t, kp['hand']), f"the Monthly Pack shows coverage for its month {rng} with the amounts")
    await pg.evaluate("() => { REP.preset = 'ty'; }")
    J = await pg.evaluate("() => truthCoverage(['', today()], {projectId: 'p121'}).cost")
    t = await report(pg, 'profit', {'proj': 'p121'})
    c.ok(re.search(r'backed by a bank or card line', t, re.I) and has_money(t, J['bank']) and has_money(t, J['hand']), f"the job report shows 121 State's coverage (bank {J['bank']}, hand {J['hand']})")
    await pg.evaluate("() => { glFrom = '2026-08-01'; glTo = '2026-08-31'; }")
    t = await ledger(pg, 'overview')
    c.ok(re.search(r'backed by a bank or card line', t, re.I) and has_money(t, k['bank']) and has_money(t, k['hand']), 'the Ledger overview shows coverage for its range')
    await pg.evaluate("() => { glFrom = ''; glTo = ''; }")
    a = await ask(pg, "how much of August's cost is backed by the bank")
    c.ok(has_money(a['headline'], k['bank']) and has_money(a['headline'], k['document']) and has_money(a['headline'], k['hand']),
         f"Ask answers with the three amounts: {a['headline'][:200]}")
    c.ok(not errs, f'no page errors {errs[:2]}')
    await b.close()


# ---------------------------------------------------------------- 2. manual journals
async def sec_manual(p, c):
    b, pg, errs = await fresh(p, 'u_controller')
    await ledger(pg, 'entry')
    await pg.fill('#gle-date', '2026-08-31')
    await pg.fill('#gle-memo', 'August depreciation on the van')
    await pg.evaluate("""() => { const rows = document.querySelectorAll('#gle-lines tbody tr');
        rows[0].querySelector('[data-l=acct]').value = '8000'; rows[0].querySelector('[data-l=dr]').value = '1200';
        rows[1].querySelector('[data-l=acct]').value = '1590'; rows[1].querySelector('[data-l=cr]').value = '1200'; }""")
    await pg.click('#gle-save')
    await pg.wait_for_timeout(200)
    j = await pg.evaluate("() => { const j = DB.gl.journals.find(x => x.kind === 'manual' && /van/.test(x.memo)); return j ? {id: j.id, status: j.status, by: j.createdBy} : null; }")
    c.ok(j and j['status'] == 'pending', f'the Controller drafts: {j}')
    if not j: await b.close(); return
    jid = j['id']
    st = await pg.evaluate("id => { glApprove(id); return DB.gl.journals.find(x => x.id === id).status; }", jid)
    c.ok(st == 'pending', f'the Controller cannot post it ({st})')
    await sign_in(pg, 'u_owner')
    st = await pg.evaluate("id => { try { mbCloseModal(); } catch (e) {} glApprove(id); const j = DB.gl.journals.find(x => x.id === id); return {status: j.status, modal: !!document.querySelector('#mbm')}; }", jid)
    c.ok(st['status'] == 'pending', f'the Owner is refused without a typed reason ({st})')
    await pg.evaluate("() => { try { mbCloseModal(); } catch (e) {} }")
    r = await pg.evaluate("id => { glApprove(id, 'Straight-line on the van, August'); const j = DB.gl.journals.find(x => x.id === id); return {status: j.status, why: j.why, by: j.approvedBy, flag: typeof truthFlagOf === 'function' ? truthFlagOf(j) : null}; }", jid)
    c.ok(r['status'] == 'posted' and r['why'] == 'Straight-line on the van, August', f'the Owner posts with a typed reason: {r}')
    c.ok(r['flag'] and re.match(r'^Manual · by .+ · .+ · Straight-line on the van', r['flag'].get('text', '')), f"the flag reads Manual · by who · when · why: {r['flag']}")
    # ledger rows
    t = await ledger(pg, 'journal')
    c.ok('Manual · by' in t and 'Straight-line on the van' in t, 'the Journal rows carry the flag')
    svg = await pg.evaluate("id => { const tr = document.querySelector('#v-gl tr[data-glopen=\"' + id + '\"]'); return !!(tr && tr.querySelector('.tr-flag svg')); }", jid)
    c.ok(svg, 'the flag has a line icon on the row')
    # statement lines: count and amount per line, with a drill-down
    await pg.evaluate("() => { glFrom = '2026-08-01'; glTo = '2026-08-31'; }")
    t = await ledger(pg, 'statements', 'pl')
    c.ok(re.search(r'Depreciation\s*\n?\s*1 manual[^\n]*\$1,200', t), 'the P&L statement line shows 1 manual · $1,200')
    ok = await click_js(pg, '#v-gl [data-trdrill]')
    t2 = await text_of(pg, 'gl')
    c.ok(ok and 'Straight-line on the van' in t2, 'the drill-down opens the entries behind the line')
    await pg.evaluate("() => { glFrom = ''; glTo = ''; }")
    # the Pack, the Flash, the close checklist
    t = await report(pg, 'pack')
    c.ok(re.search(r'Manual (journal )?entries', t, re.I) and 'Straight-line on the van' in t, 'the Pack names the manual entry with its reason')
    t = await report(pg, 'flash')
    c.ok(re.search(r'Manual (journal )?entries', t, re.I) and re.search(r'1 in August', t), 'the Flash counts manual entries by month')
    cl = await pg.evaluate("() => closeChecklist('2026-08').filter(i => /manual/i.test(i.label)).map(i => i.label)")
    c.ok(cl and re.search(r'1 .*\$1,200', cl[0]), f'the close checklist lists manual entries with count and amount: {cl}')
    a = await ask(pg, 'were there any manual entries in August')
    c.ok(re.search(r'1 manual (journal )?entr', a['headline']) and 'Straight-line on the van' in a['text'] and 'Owner' in a['text'], f"Ask: {a['headline'][:200]}")
    # a posting that did not derive from a document (the close's WIP entry) is flagged too, as a close entry
    k = await pg.evaluate("() => truthFlagOf({kind: 'close', accrues: 'wip', memo: 'WIP adjustment', approvedBy: 'Owner', approvedAt: '2026-09-01T10:00:00', date: '2026-08-31', lines: []})")
    c.ok(bool(k and k['text'].startswith('Close')), f'a close entry is flagged as a close entry: {k}')
    c.ok(not errs, f'no page errors {errs[:2]}')
    await b.close()


# ---------------------------------------------------------------- 3. tamper-evident, append-only
async def sec_tamper(p, c):
    b, pg, errs = await fresh(p)
    have = await pg.evaluate("() => ['truthEdit', 'truthSeal', 'truthVerify', 'truthHistory', 'truthVoidTxn'].every(f => typeof window[f] === 'function')")
    c.ok(have, 'truthEdit / truthSeal / truthVerify / truthHistory / truthVoidTxn exist')
    if not have: await b.close(); return
    # amend a posted invoice: refused without a reason; with one it is a linked reversal and re-post
    inv = await pg.evaluate("() => { const c = DB.clients.find(x => x.id === 'cl121'), d = c.invoices.find(i => i.status === 'sent') || c.invoices.find(i => i.status !== 'draft'); return {cid: c.id, id: d.id, number: d.number, status: d.status, before: DB.gl.journals.filter(j => j.key === 'inv:' + d.id).length}; }")
    r0 = await pg.evaluate("x => truthEdit('invoice', x, '', d => { d.discount = {type: 'amt', value: 100}; })", inv)
    c.ok(r0 and r0.get('ok') is False, f'an amendment without a reason is refused: {r0}')
    r1 = await pg.evaluate("x => truthEdit('invoice', x, 'Client was promised a $100 courtesy credit on the call of 9/2', d => { d.discount = {type: 'amt', value: 100}; })", inv)
    c.ok(r1 and r1.get('ok'), f'with a reason it goes through: {r1}')
    J = await pg.evaluate("x => DB.gl.journals.filter(j => j.key === 'inv:' + x.id).sort((a, b) => a.n - b.n).map(j => ({n: j.n, kind: j.kind, status: j.status, memo: j.memo, by: j.by || '', why: j.why || '', reversalOf: !!j.reversalOf, amends: j.amends || ''}))", inv)
    kinds = [x['kind'] + ':' + x['status'] for x in J]
    c.ok(kinds.count('posting:reversed') >= 1 and kinds.count('reversal:posted') >= 1 and kinds.count('posting:posted') >= 1, f'reversed posting + reversal + re-post: {kinds}')
    rev = [x for x in J if x['kind'] == 'reversal']
    c.ok(rev and 'courtesy credit' in rev[-1]['memo'] and rev[-1]['by'], f"the reversal carries who and why: {rev[-1] if rev else None}")
    rp = [x for x in J if x['kind'] == 'posting' and x['status'] == 'posted']
    c.ok(rp and rp[-1]['amends'], f'the re-post links back to what it amends: {rp[-1] if rp else None}')
    H = await pg.evaluate("x => truthHistory('inv:' + x.id)", inv)
    c.ok(len(H) >= 3 and any('courtesy credit' in (h.get('why') or '') for h in H), f'truthHistory lists the chain ({len(H)} events)')
    # the History strip on the record
    await pg.evaluate("x => { clientOpen = x.cid; docOpen = {kind: 'invoice', id: x.id}; view = 'billing'; render(); }", inv)
    await pg.wait_for_timeout(200)
    strip = await pg.evaluate("() => { const s = document.querySelector('.view.on .tr-hist'); return s ? s.innerText : ''; }")
    c.ok('History' in strip and 'courtesy credit' in strip and re.search(r'reversed|re-posted|amended', strip, re.I), f'the invoice page shows a History strip: {strip[:160]!r}')
    # delete is refused on posted records
    n0 = await pg.evaluate("x => DB.clients.find(c => c.id === x.cid).invoices.length", inv)
    await pg.evaluate("async x => { const c = DB.clients.find(y => y.id === x.cid), d = c.invoices.find(i => i.id === x.id); await docAction(c, d, 'del'); }", inv)
    await pg.wait_for_timeout(150)
    n1 = await pg.evaluate("x => DB.clients.find(c => c.id === x.cid).invoices.length", inv)
    toast = await pg.evaluate("() => (document.getElementById('toast') || {}).innerText || ''")
    c.ok(n0 == n1 and re.search(r'posted|void', toast, re.I), f'deleting a posted invoice is refused ({n0} -> {n1}; toast {toast!r})')
    # a reconciled bank line: the drawer's Delete is refused
    await pg.evaluate("() => { view = 'bank'; render(); txnDialog('t1'); }")
    await pg.wait_for_timeout(150)
    await pg.evaluate("() => { const d = document.getElementById('d-delete'); d && d.click(); }")
    await pg.wait_for_timeout(150)
    still = await pg.evaluate("() => !!DB.txns.find(t => t.id === 't1')")
    c.ok(still, 'a reconciled bank line cannot be deleted')
    await pg.evaluate("() => { if (typeof closeEditor === 'function' && document.querySelector('#drawer.on')) closeEditor(); try { mbCloseModal(); } catch (e) {} }")
    # a typed, coded line: Void is a reversal with a reason
    v0 = await pg.evaluate("() => truthVoidTxn(DB.txns.find(t => t.id === 't12'), '')")
    c.ok(v0 and v0.get('ok') is False, f'void without a reason is refused: {v0}')
    vb = await pg.evaluate("() => truthVoidTxn(DB.txns.find(t => t.id === 't11'), 'trying on a statement-confirmed line')")
    c.ok(vb and vb.get('ok') is False and re.search(r'has this line', vb.get('why', '')), f'a line the bank holds is never voided: {vb}')
    v1 = await pg.evaluate("() => truthVoidTxn(DB.txns.find(t => t.id === 't12'), 'Typed twice; the bank shows one premium')")
    gone = await pg.evaluate("() => ({ onReg: !!DB.txns.find(t => t.id === 't12'), voided: (DB.voided || []).some(v => v.id === 't12'),"
                             " rev: DB.gl.journals.filter(j => j.key === 'txn:t12' && j.kind === 'reversal').map(j => j.memo) })")
    c.ok(v1 and v1.get('ok') and not gone['onReg'] and gone['voided'], f'void moves the line to the voided register: {gone}')
    c.ok(gone['rev'] and 'Typed twice' in gone['rev'][-1], f"the ledger reversal carries the reason: {gone['rev']}")
    # the hash chain: sealed per period, re-verified, names a changed or missing posting
    s = await pg.evaluate("() => truthSeal('2026-08')")
    c.ok(s and s.get('head') and s.get('n', 0) > 5, f'August sealed: {s and {k: s[k] for k in ("n", "head", "scheme") if k in s}}')
    c.ok(s and re.match(r'^[0-9a-f]{8}$', s.get('head', '')), 'the head is an 8-hex FNV-1a hash')
    v = await pg.evaluate("() => truthVerify('2026-08')")
    c.ok(v and v.get('ok') is True, f'verify is clean after sealing: {v and {k: v[k] for k in ("ok", "changed", "missing", "added")}}')
    r = await pg.evaluate("""() => { const J = DB.gl.journals.filter(j => j.status === 'posted' && j.date.slice(0, 7) === '2026-08' && j.lines.some(l => l.dr > 0));
        const j = J[Math.floor(J.length / 2)], l = j.lines.find(l => l.dr > 0); l.dr = r2(l.dr + 1);
        const v = truthVerify('2026-08'); l.dr = r2(l.dr - 1); return {n: j.n, memo: j.memo, ok: v.ok, changed: v.changed, missing: v.missing}; }""")
    c.ok(r['ok'] is False and any(f"#{r['n']}" in str(x) for x in r['changed']), f"a changed posting is named: #{r['n']} -> {r['changed']}")
    r = await pg.evaluate("""() => { const i = DB.gl.journals.findIndex(j => j.status === 'posted' && j.date.slice(0, 7) === '2026-08'); const j = DB.gl.journals[i];
        DB.gl.journals.splice(i, 1); const v = truthVerify('2026-08'); DB.gl.journals.splice(i, 0, j); return {n: j.n, ok: v.ok, missing: v.missing}; }""")
    c.ok(r['ok'] is False and any(f"#{r['n']}" in str(x) for x in r['missing']), f"a missing posting is named: #{r['n']} -> {r['missing']}")
    v = await pg.evaluate("() => truthVerify('2026-08').ok")
    c.ok(v is True, 'restored, the chain verifies again')
    t = await ledger(pg, 'overview')
    c.ok('Verify the Books' in t, 'the Ledger overview offers Verify the Books')
    prim = await pg.evaluate("() => [...document.querySelectorAll('#v-gl .btn.primary')].filter(b => b.offsetParent).length")
    c.ok(prim <= 1, f'one blue primary on the Ledger ({prim})')
    await click_js(pg, '#v-gl [data-trverify]')
    m = await pg.evaluate("() => { const m = document.querySelector('#mbm'); return m ? m.innerText : ''; }")
    c.ok('2026-08' in m or 'August' in m, f'Verify the Books reports per sealed month: {m[:120]!r}')
    await pg.evaluate("() => { try { mbCloseModal(); } catch (e) {} }")
    # a real close seals the month and verifies the earlier ones
    r = await pg.evaluate("() => fin2RunClose('2026-07', 'the setup month: nothing posted, closing to seal it')")
    c.ok(r and r.get('ok'), f"July closes: {r and (r.get('why') or 'ok')}")
    ch = await pg.evaluate("() => ({ chain: ((DB.periods || {}).chains || {})['2026-07'] || null, rec: (DB.periods.closes || []).filter(x => x.month === '2026-07').pop() })")
    c.ok(ch['chain'] and ch['rec'] and ch['rec'].get('chain') == ch['chain']['head'], f"the close stores the chain head with the period: {ch['chain'] and ch['chain']['head']}")
    v = await pg.evaluate("() => truthVerify('2026-07').ok")
    c.ok(v is True, 'the closed month verifies')
    c.ok(not errs, f'no page errors {errs[:2]}')
    await b.close()


# ---------------------------------------------------------------- 4. every transaction matched to a line
async def sec_match(p, c):
    b, pg, errs = await fresh(p)
    have = await pg.evaluate("() => ['truthMatchOf', 'truthSetMatch', 'truthCandidates', 'truthException'].every(f => typeof window[f] === 'function') && !!PRED.unmatchedTxns && CATCH.some(x => x.name === 'unmatchedTxns')")
    c.ok(have, 'the link model (truthMatchOf/truthSetMatch), PRED.unmatchedTxns and the CATCH entry exist')
    if not have: await b.close(); return
    m = await pg.evaluate("() => truthMatchOf(DB.txns.find(t => t.id === 't3'))")
    c.ok(m.get('poId') == 'po1' and m.get('poLineId') == 'pl1' and m.get('estimateLineId') == 'estimate:es1:l7' and m.get('billId') == 'b1' and m.get('kind') == 'cost',
         f'the Nemo Tile line resolves to PO line, bill and estimate line: {m}')
    m = await pg.evaluate("() => truthMatchOf(DB.txns.find(t => t.id === 't1'))")
    c.ok(m.get('kind') == 'income' and m.get('invoiceId') == 'in1', f'the Klein wire resolves to its invoice: {m}')
    keys = await pg.evaluate("() => Object.keys(truthMatchOf(DB.txns.find(t => t.id === 't13'))).sort()")
    for k in ('billId', 'billLineId', 'poId', 'poLineId', 'estimateLineId', 'invoiceId', 'invoiceLineId', 'payrollId'):
        c.ok(k in keys, f'the model carries {k}')
    # one number: PRED, bankUnmatched, the CATCH rows, by month
    U = await pg.evaluate("() => ({ pred: PRED.unmatchedTxns.count(), bank: bankUnmatched().n, amt: bankUnmatched().amt, by: PRED.unmatchedTxns.byMonth(), catch: CATCH.find(x => x.name === 'unmatchedTxns').rows().length })")
    c.ok(U['pred'] == U['bank'] == U['catch'] == 16, f"one number: PRED {U['pred']} · bankUnmatched {U['bank']} · Caught for You {U['catch']}")
    c.ok(sum(v['n'] for v in U['by'].values()) == U['pred'] and '2026-08' in U['by'] and '2026-09' in U['by'], f"by month adds up: {U['by']}")
    # a bank line matched to a PO line: the estimate line follows
    r = await pg.evaluate("""() => { const t = DB.txns.find(x => x.id === 't13'); const r = truthSetMatch(t, {poId: 'po3', poLineId: 'pl3'}, {why: 'Tino white oak, PO-2026-047'});
        return {ok: r && r.ok, m: truthMatchOf(t), unmatched: txnUnmatched(t), n: bankUnmatched().n, proj: t.projectId, by: t.matchedBy}; }""")
    c.ok(r['ok'] and r['m'].get('estimateLineId') == 'estimate:es1:l8' and r['m'].get('poLineId') == 'pl3' and not r['unmatched'] and r['n'] == 15,
         f"matched to the PO line, estimate line follows, count 16 -> 15: {r}")
    # Banking shows the count per month; Home catches it; Ask answers per month and in total
    await go(pg, 'bank')
    t = await text_of(pg, 'bank')
    c.ok(re.search(r'Not Matched to a Line', t) and re.search(r'August[^\n]*\d', t) and re.search(r'September[^\n]*\d', t), 'Banking shows unmatched lines by month')
    await go(pg, 'home')
    t = await pg.evaluate("() => { const h = document.querySelector('.view.on .td-catch'); return h ? h.innerText : ''; }")
    if not t:
        await pg.evaluate("() => { tdCatchAll = true; render(); }")
    cnt = await pg.evaluate("() => { const e = document.querySelector('.view.on [data-tdcaught]'); return e ? +e.dataset.tdcaught : -1; }")
    rows = await pg.evaluate("() => CATCH.find(x => x.name === 'unmatchedTxns').rows().map(r => r.what)")
    c.ok(cnt >= 15 and rows and all(r.startswith('Not matched') for r in rows), f'Home Caught for You counts {cnt} and names the lines ({rows[:2]})')
    a = await ask(pg, 'how many bank lines are unmatched in August')
    aug = U['by']['2026-08']['n']
    c.ok(re.search(rf'\b{aug}\b', a['headline']) and 'August' in a['headline'], f"Ask per month: {a['headline'][:160]}")
    a = await ask(pg, 'how many bank lines are unmatched')
    c.ok(re.search(r'\b15\b', a['headline']), f"Ask total: {a['headline'][:160]}")
    # the close checklist and the close itself
    cl = await pg.evaluate("() => closeChecklist('2026-08').filter(i => /not matched to a line/i.test(i.label)).map(i => ({label: i.label, n: i.n, ok: i.ok}))")
    c.ok(cl and cl[0]['n'] == aug and not cl[0]['ok'], f'the close checklist counts them: {cl}')
    r = await pg.evaluate("() => fin2RunClose('2026-08', 'trying with unmatched lines')")
    c.ok(r and not r.get('ok') and re.search(r'not matched to a line', r.get('why', ''), re.I), f"the close refuses: {r and r.get('why', '')[:200]}")
    ex0 = await pg.evaluate("() => { const t = bankUnmatched().rows.find(x => x.date.slice(0, 7) === '2026-08'); return truthException(t, ''); }")
    c.ok(ex0 and ex0.get('ok') is False, f'an exception needs a typed reason: {ex0}')
    await sign_in(pg, 'u_chen')
    ex1 = await pg.evaluate("() => { const t = bankUnmatched().rows.find(x => x.date.slice(0, 7) === '2026-08'); return truthException(t, 'coordinator trying'); }")
    c.ok(ex1 and ex1.get('ok') is False, f'only the Owner or the Controller signs an exception: {ex1}')
    await sign_in(pg, 'u_controller')
    n = await pg.evaluate("() => { let n = 0; bankUnmatched().rows.filter(x => x.date.slice(0, 7) === '2026-08').forEach(t => { if (truthException(t, 'August line, reviewed; the vendor record arrives next month').ok) n++; }); return n; }")
    c.ok(n == aug, f'the Controller signs {n} exceptions')
    bl = await pg.evaluate("() => fin2CloseBlockers('2026-08').map(b => b.why).filter(w => /not matched to a line/i.test(w))")
    c.ok(not bl, f'with every line excepted the unmatched blocker is gone: {bl}')
    # proposals: a statement line that agrees with a bill on amount, vendor and date is proposed, and a person confirms
    await sign_in(pg, 'u_owner')
    bid = await new_bill(pg, 'Satish Electric', 'SE-2208', '2026-09-01', 'p121', 'subs', '06', 'Rough electric, garden unit', 7400, 'estimate:es1:l5')
    c.ok(bool(bid), 'a bill through the New Bill drawer')
    out = await import_statement(pg, 'ac1', 'Chase_4471_Sep2026_truth.csv', csv([('2026-09-02', 'ACH DEBIT SATISH ELECTRIC INC', -7400.00, 'CHS-260902-11')]))
    pr = await pg.evaluate("() => { const t = DB.txns.find(x => x.id === 't16'); return {prop: t.proposal, backed: bfBacked(t)}; }")
    c.ok(pr['backed'], f'the typed Satish line is confirmed by the statement: {out}')
    c.ok(pr['prop'] and pr['prop'].get('billId') == bid and pr['prop'].get('m') and pr['prop']['m'].get('billLineId'), f'a match to the bill line is proposed, not posted: {pr["prop"]}')
    st = await pg.evaluate("() => ({ unmatched: txnUnmatched(DB.txns.find(x => x.id === 't16')), status: DB.bills.find(b => b.number === 'SE-2208').status })")
    c.ok(st['unmatched'], 'until a person confirms, the line stays unmatched (a proposal is not a match)')
    r = await pg.evaluate("() => { const t = DB.txns.find(x => x.id === 't16'); confirmMatch(t); return {m: truthMatchOf(t), unmatched: txnUnmatched(t)}; }")
    c.ok(r['m'].get('billId') == bid and r['m'].get('billLineId') and r['m'].get('estimateLineId') == 'estimate:es1:l5' and not r['unmatched'],
         f'confirmed: bill line and its estimate line: {r}')
    c.ok(not errs, f'no page errors {errs[:2]}')
    await b.close()


# ---------------------------------------------------------------- 5. QuickBooks as a bridge
SNAPSHOT = {
    "source": "quickbooks",
    "company": {"CompanyName": "Harbor Demo Builders LLC", "Country": "US"},
    "customers": [{"Id": "58", "DisplayName": "Harbor View LLC", "CompanyName": "Harbor View LLC",
                   "PrimaryEmailAddr": {"Address": "ap@harborview.example"}, "PrimaryPhone": {"FreeFormNumber": "(718) 555-0100"},
                   "BillAddr": {"Line1": "12 Pier Rd", "City": "Brooklyn", "CountrySubDivisionCode": "NY", "PostalCode": "11231"}}],
    "products": [{"Id": "7", "Name": "Construction services", "Type": "Service"}],
    "estimates": [{"Id": "301", "DocNumber": "1041", "TxnDate": "2026-08-03", "TxnStatus": "Accepted", "TotalAmt": 42000,
                   "CustomerRef": {"value": "58", "name": "Harbor View LLC"},
                   "Line": [{"Id": "1", "DetailType": "SalesItemLineDetail", "Amount": 30000, "Description": "Rooftop deck framing",
                             "SalesItemLineDetail": {"ItemRef": {"value": "7", "name": "Construction services"}, "Qty": 1, "UnitPrice": 30000}},
                            {"Id": "2", "DetailType": "SalesItemLineDetail", "Amount": 12000, "Description": "Railings and decking",
                             "SalesItemLineDetail": {"ItemRef": {"value": "7", "name": "Construction services"}, "Qty": 1, "UnitPrice": 12000}},
                            {"Id": "3", "DetailType": "SubTotalLineDetail", "Amount": 42000}]}],
    "invoices": [{"Id": "402", "DocNumber": "1042", "TxnDate": "2026-08-20", "DueDate": "2026-09-04", "TotalAmt": 21000, "Balance": 6000,
                  "CustomerRef": {"value": "58", "name": "Harbor View LLC"},
                  "Line": [{"Id": "1", "DetailType": "SalesItemLineDetail", "Amount": 21000, "Description": "Deck framing, 50%",
                            "SalesItemLineDetail": {"ItemRef": {"value": "7", "name": "Construction services"}, "Qty": 1, "UnitPrice": 21000}}]}],
    "arAging": {"summary": {"asOf": "2026-08-31", "total": 6000},
                "detail": [{"TxnId": "402", "DocNumber": "1042", "CustomerRef": {"value": "58"}, "DueDate": "2026-09-04", "Balance": 6000}]},
    "apAging": {"summary": {"asOf": "2026-08-31", "total": 2500},
                "bills": [{"Id": "901", "DocNumber": "LB-77", "VendorRef": {"name": "Lumber Barn"}, "TxnDate": "2026-08-22", "DueDate": "2026-09-21",
                           "TotalAmt": 2500, "Balance": 2500,
                           "Line": [{"Id": "1", "Amount": 2500, "Description": "PT lumber for the deck", "DetailType": "AccountBasedExpenseLineDetail",
                                     "AccountBasedExpenseLineDetail": {"AccountRef": {"name": "Cost of Goods Sold:Materials"}}}]}],
                "detail": []},
    "pl": {"period": {"from": "2026-08-01", "to": "2026-08-31"},
           "months": [{"month": "2026-08", "report": {"Header": {"ReportName": "ProfitAndLoss"}, "Rows": {"Row": [
               {"type": "Section", "Header": {"ColData": [{"value": "Income"}, {"value": ""}]},
                "Rows": {"Row": [{"type": "Data", "ColData": [{"value": "Construction income"}, {"value": "21000.00"}]}]},
                "Summary": {"ColData": [{"value": "Total Income"}, {"value": "21000.00"}]}},
               {"type": "Section", "Header": {"ColData": [{"value": "Cost of Goods Sold"}, {"value": ""}]},
                "Rows": {"Row": [{"type": "Data", "ColData": [{"value": "Materials"}, {"value": "2500.00"}]}]},
                "Summary": {"ColData": [{"value": "Total Cost of Goods Sold"}, {"value": "2500.00"}]}},
               {"type": "Section", "Header": {"ColData": [{"value": "Expenses"}, {"value": ""}]},
                "Rows": {"Row": [{"type": "Data", "ColData": [{"value": "Insurance"}, {"value": "1800.00"}]}]},
                "Summary": {"ColData": [{"value": "Total Expenses"}, {"value": "1800.00"}]}}]}}}]},
    "cashFlow": {},
    "balanceSheet": [{"asOf": "2026-08-31", "rows": [{"group": "cash", "label": "Checking", "amount": 150000},
                                                     {"group": "ar", "label": "Accounts Receivable (A/R)", "amount": 6000},
                                                     {"group": "ap", "label": "Accounts Payable (A/P)", "amount": 2500}]}],
    "sales": {"byCustomer": [], "byProduct": []},
    "payroll": {"employees": [{"id": "e1", "name": "Pat Doe"}], "schedules": [],
                "runs": [{"id": "pr-77", "payPeriodStart": "2026-08-03", "payPeriodEnd": "2026-08-14", "payDate": "2026-08-19",
                          "grossPay": 9000, "employerTaxes": 900, "totalCost": 9900, "employeeCount": 3}], "payslips": []},
}


async def sec_qbo(p, c):
    b, pg, errs = await fresh(p)
    have = await pg.evaluate("() => typeof qboLoad === 'function' && typeof truthTieOut === 'function'")
    c.ok(have, 'qboLoad and truthTieOut exist')
    if not have: await b.close(); return
    # the harness refuses a snapshot inside the repo
    inside = os.path.join(ROOT, 'tests', 'invented.qbo.json')
    try:
        await load_qbo_snapshot(pg, inside)
        c.ok(False, 'load_qbo_snapshot refuses a path inside the repo')
    except ValueError as e:
        c.ok('repo' in str(e).lower() or 'outside' in str(e).lower(), f'load_qbo_snapshot refuses a path inside the repo: {e}')
    except Exception as e:
        c.ok(False, f'load_qbo_snapshot raised {type(e).__name__}: {e}')
    d = tempfile.mkdtemp(prefix='sd_qbo_')
    path = os.path.join(d, 'invented.qbo.json')
    with open(path, 'w') as f: json.dump(SNAPSHOT, f)
    try:
        r = await load_qbo_snapshot(pg, path)
        c.ok(r and r.get('ok'), f'the snapshot loads: {r}')
        R = await pg.evaluate("""() => { const c = DB.clients.find(x => x.source === 'quickbooks' && x.qboId === '58');
            const e = c && c.estimates.find(x => x.source === 'quickbooks'), i = c && c.invoices.find(x => x.source === 'quickbooks');
            const bl = DB.bills.find(x => x.source === 'quickbooks' && x.qboId === '901'), pr = DB.payroll.find(x => x.source === 'quickbooks');
            return { client: c && c.name, est: e && {lines: e.lines.length, total: docTotal(e).total, status: e.status, number: e.number},
              inv: i && {lines: i.lines.length, total: docTotal(i).total, status: i.status, paid: invoicePaid(c, i), number: i.number},
              bill: bl && {vendor: bl.vendor, total: billTotal(bl), status: bl.status, cat: bl.cat}, run: pr && {total: pr.total, payDate: pr.payDate, status: pr.status},
              nClients: DB.clients.length, nBills: DB.bills.length, nRuns: DB.payroll.length, qbo: !!(DB.qbo && DB.qbo.pl) }; }""")
        c.ok(R['client'] == 'Harbor View LLC', f"the customer is a client: {R['client']}")
        c.ok(R['est'] and R['est']['lines'] == 2 and R['est']['total'] == 42000 and R['est']['status'] == 'approved', f"the estimate with its lines: {R['est']}")
        c.ok(R['inv'] and R['inv']['lines'] == 1 and R['inv']['total'] == 21000 and R['inv']['paid'] == 15000 and R['inv']['status'] == 'partial', f"the invoice with its lines and the payment behind its balance: {R['inv']}")
        c.ok(R['bill'] and R['bill']['total'] == 2500 and R['bill']['vendor'] == 'Lumber Barn' and R['bill']['cat'] == 'materials', f"the open AP bill: {R['bill']}")
        c.ok(R['run'] and R['run']['total'] == 9900 and R['run']['payDate'] == '2026-08-19', f"the payroll run: {R['run']}")
        r2_ = await load_qbo_snapshot(pg, path)
        R2 = await pg.evaluate("() => ({ nClients: DB.clients.length, nBills: DB.bills.length, nRuns: DB.payroll.length, nInv: DB.clients.flatMap(c => c.invoices).filter(i => i.source === 'quickbooks').length, nPay: DB.clients.flatMap(c => c.payments).filter(i => i.source === 'quickbooks').length })")
        c.ok(R2['nClients'] == R['nClients'] and R2['nBills'] == R['nBills'] and R2['nRuns'] == R['nRuns'] and R2['nInv'] == 1 and R2['nPay'] == 1, f'a re-load is idempotent: {R2}')
        # the Three-Way Tie-Out
        T = await pg.evaluate("() => truthTieOut('2026-08')")
        groups = [r['group'] for r in T['rows']]
        c.ok(all(g in groups for g in ('income', 'cogs', 'expenses', 'cash', 'ar', 'ap')), f'six account groups: {groups}')
        inc = next(r for r in T['rows'] if r['group'] == 'income')
        c.ok(inc['qbo'] == 21000, f"QuickBooks says income 21,000 (read from the QBO report rows): {inc['qbo']}")
        c.ok(inc['bank'] is not None and inc['erp'] is not None, f"the bank says {inc['bank']}, the ERP says {inc['erp']}")
        diffs = [r for r in T['rows'] if (r.get('diffQbo') or r.get('diffBank'))]
        c.ok(diffs and all(r.get('cause') for r in diffs), f'every difference carries a cause or a flag ({len(diffs)} differences)')
        t = await report(pg, 'tieout')
        c.ok(re.search(r'QuickBooks Says', t, re.I) and re.search(r'The Bank Says', t, re.I) and re.search(r'The ERP Says', t, re.I) and re.search('August', t, re.I), 'Reports shows the Three-Way Tie-Out with three columns')
        c.ok(has_money(t, 21000), 'the QuickBooks income figure prints on the report')
        a = await ask(pg, 'how does quickbooks tie out for august')
        c.ok('QuickBooks' in a['headline'] and re.search(MONEY, a['headline']), f"Ask: {a['headline'][:200]}")
        c.ok(not errs, f'no page errors {errs[:2]}')
    finally:
        try: os.remove(path); os.rmdir(d)
        except OSError: pass
    await b.close()


# ---------------------------------------------------------------- 6. guards outside the page
def sec_guard(c):
    gi = open(os.path.join(ROOT, '.gitignore')).read().split('\n')
    c.ok('*.qbo.json' in gi, '.gitignore holds *.qbo.json')
    c.ok(callable(globals().get('load_qbo_snapshot')), 'harness.load_qbo_snapshot exists')


async def main():
    c = Checks()
    async with async_playwright() as p:
        if want('cov'): await sec_cov(p, c)
        if want('manual'): await sec_manual(p, c)
        if want('tamper'): await sec_tamper(p, c)
        if want('match'): await sec_match(p, c)
        if want('qbo'): await sec_qbo(p, c)
    if want('guard'): sec_guard(c)
    sys.exit(c.done())

asyncio.run(main())
