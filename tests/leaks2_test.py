"""leaks2: the month's most expensive cracks, each reproduced on a fresh seed (review/month/ledger.md, BACKLOG 1.5, 8).

The month (tests/month_sim.py) left $137,278 behind on master db8d418. Each scenario here injects one crack through
the app's own paths (the statement import dialog, the transaction drawer, docAction, prgSet, payrollFromTime,
cmImport) and checks that the person who should act gets a proposal they can confirm, and that confirming it
closes the crack. AI proposes, people approve: nothing here is written without a person's press.

    python3 leaks2_test.py                    # every scenario
    python3 leaks2_test.py --scenario earned  # one or more by name or number

Scenarios
  1 earned    earned-not-billed: hold per line, never per job; CO lines bill from 0; a draft says Send
  2 reimb     card purchases bought for a client become reimbursable rows, billed with the job's markup
  3 credit    a refund on a purchase billed to the client proposes a client credit that reaches an invoice
  4 match     payroll debits match their run, card charges their PO, a check with no bill proposes the bill,
              a hand-typed cost is flagged "no bank line"
  5 dup       a duplicate charge at import is a proposed dispute on the controller's Needs Your Hand
  6 stmt      a statement in mail proposes the import and the reconcile, not a task
  7 payroll   one payroll run per pay period across entities, built from every hour approved by its date
  8 dispute   a vendor credit memo closes the held difference with one approval

All data is invented. The last line is `N flags`; exit 1 when N > 0."""
import asyncio, sys, json, argparse, re
from harness import *
from leak_test import boot, import_statement, find_txn, code_txn, csv, ofx, Scenario, scan, ask, surf, PAGE_HELPERS

JOB = 'p121'


async def billing_row(pg, needle):
    """The Billing Queue row (as billing sees it) whose text holds `needle`: its text and its button's label."""
    await pg.evaluate("() => { signIn('u_billing'); view = 'billing'; billTab = 'billable'; docOpen = null; render(); }")
    return await pg.evaluate("""n => { const tr = [...document.querySelectorAll('#v-billing tr')].find(tr => tr.querySelector('[data-blact]') && tr.innerText.includes(n));
        return tr ? {text: tr.innerText.replace(/\\s+/g, ' ').slice(0, 220), verb: tr.querySelector('[data-blact]').innerText.trim()} : null; }""", needle)


async def press_row(pg, needle, verb):
    """Press the row's button, then the sheet's blue button (the house rule: the primary is the safe next step)."""
    return await pg.evaluate("""async ([n, v]) => { const tr = [...document.querySelectorAll('#v-billing tr')].find(tr => tr.querySelector('[data-blact]') && tr.innerText.includes(n));
        const b = tr && tr.querySelector('[data-blact]'); if (!b || b.innerText.trim() !== v) return 'no ' + v;
        b.click(); await new Promise(r => setTimeout(r, 60)); const m = document.querySelector('#mbm');
        const title = m ? (m.querySelector('h3') || {}).innerText : '';
        const ok = m && m.querySelector('#mbm-ok'); ok && ok.click(); await new Promise(r => setTimeout(r, 120));
        return 'pressed ' + v + (title ? ' > ' + title : '') + (ok ? ' > ' + ok.innerText : ''); }""", [needle, verb])


# ---------------------------------------------------------------- 1. earned, not billed
async def s1_earned(p, S):
    b, pg, errs = await boot(p)
    try:
        st = await pg.evaluate("""() => { const p = DB.projects.find(x => x.id === 'p121'), w = wipRow(p), R = readyToBill();
            return {over: Math.round(w.over), app: R.rows.filter(r => r.p && r.p.id === 'p121' && r.kind === 'application').map(r => r.amount),
                    why: R.rows.filter(r => r.p && r.p.id === 'p121' && r.kind === 'application').map(r => r.why || ''), ahead: pbAhead('p121').lines.length,
                    jobHeld: R.held.filter(h => !h.sv).map(h => [h.p.id, h.why]), held: R.held.map(h => [h.p.id, h.line, h.amount])}; }""")
        S.fact(f"seed: 121 State billed ${st['over']:,} ahead on the WIP schedule; application {st['app']}; held {st['held']}")
        # The hold design (lane 1, round three, 2026-10-26, the month walk's E248): a job billed ahead on the whole is
        # never billed further ahead and never leaves measured work unbilled. Its application bills the lines behind their
        # measure and holds the lines ahead at 0, and the row says both. Round one held the whole application, which left
        # rough electrical measured 100% and billed 85% at month end; this replaces it.
        want = r'^bills \$12,651 of measured work on 2 lines; holds %d lines billed ahead, net \$[\d,]+, not counting the 20%% deposit$' % st['ahead']
        S.check(st['app'] == [12651.25] and st['why'] and re.search(want, st['why'][0]) and all('ahead of the work' in w for _, w in st['jobHeld']),
                'a job billed ahead on the whole bills its measured lines and holds only the lines ahead, with the reason', f"application {st['app']} {st['why']}; job-level holds {st['jobHeld']}")
        # the foreman measures rough electrical at 100%; the client approves CO-2026-002 and the treads are done
        await pg.evaluate("""async () => { const p = DB.projects.find(x => x.id === 'p121');
            prgSet(p, p.tasks.find(t => t.id === 'relec'), {pct: 100, by: 'Angel', role: 'foreman', src: 'field', note: 'Rough electrical complete'});
            const c = DB.clients.find(x => x.id === 'cl121'); await docAction(c, c.changeOrders.find(x => x.number === 'CO-2026-002'), 'approve');
            prgSet(p, p.tasks.find(t => t.id === 'sand'), {pct: 100, by: 'Angel', role: 'foreman', src: 'field', note: 'Treads sanded and stained'}); save(); }""")
        row = await billing_row(pg, '121 State')
        S.check(row and row['verb'] == 'Draft' and 'CO-2026-002' in row['text'] and 'of measured work' in row['text'] and 'billed ahead' in row['text'],
                'Billing Queue: the 121 State application is ready to draft, with CO-2026-002 on it and what it holds', str(row))
        # Draft: the application fills a draft with every approved change order's line beside the contract's
        # Draft on the queue's row fills the job's draft from every line and opens it, with Send to Client next
        # drafted on purpose (the held application's Draft is Progress Billing's, blDraftApplication)
        d = await pg.evaluate("""async () => { blDraftApplication('p121'); await new Promise(r => setTimeout(r, 80));
              const c = DB.clients.find(x => x.id === 'cl121'), inv = c.invoices.find(i => i.id === (docOpen || {}).id);
              return inv && {num: inv.number, co: inv.lines.filter(l => /CO-2026-002/.test(l.item)).map(l => l.pct),
                             send: [...document.querySelectorAll('section.view.on button')].some(b => b.innerText.trim() === 'Send to Client')}; }""")
        S.check(d and d['co'] == [100] and d['send'], 'Draft fills the application (CO-2026-002 billed from 0 to 100%) and opens it with Send to Client', str(d))
        again = await pg.evaluate("""() => { const p = DB.projects.find(x => x.id === 'p121'); prgSet(p, p.tasks.find(t => t.id === 'frame'), {pct: 100, by: 'Angel', role: 'foreman', src: 'field', note: 'Framing complete'}); save(); render();
              blDraftApplication('p121');
              const c = DB.clients.find(x => x.id === 'cl121'); return {open: (docOpen || {}).id, drafts: c.invoices.filter(i => i.status === 'draft' && i.mode === 'sov').map(i => i.number)}; }""")
        S.check(isinstance(again, dict) and len(again['drafts']) == 1, 'measured later, Draft refreshes the same open draft (never a second)', str(again))
        # lane 1 (TRIAGE class 8): a draft row's next step is Review, which opens it; Send is pressed from the invoice
        row = await billing_row(pg, d['num'] if d else 'INV-')
        S.check(row and row['verb'] == 'Review', 'Billing Queue: the drafted application says Review (never a one-tap Send)', str(row))
        did = await press_row(pg, d['num'] if d else 'INV-', 'Review')
        did += ' > ' + await pg.evaluate("""async () => { const b = [...document.querySelectorAll('section.view.on button')].find(b => b.innerText.trim() === 'Send to Client'); if (!b) return 'no Send to Client';
            b.click(); await new Promise(r => setTimeout(r, 80)); const ok = document.querySelector('#mbm #mbm-ok'); ok && ok.click(); await new Promise(r => setTimeout(r, 150)); return 'Send to Client'; }""")
        sent = await pg.evaluate("n => { const c = DB.clients.find(x => x.id === 'cl121'); const i = c.invoices.find(x => x.number === n); return i ? i.status : 'none'; }", d['num'] if d else '')
        S.check(sent == 'sent', 'Send opens one sheet; Send to Client sends the application', f"{did}; status {sent}")
        held = await pg.evaluate("""() => { const p = DB.projects.find(x => x.id === 'p121'); const r = pgRows('p121').find(r => /Insulation/.test(r.sv.desc));
            p.tasks.filter(t => /insul|drywall|tape/i.test(t.name)).forEach(t => { t.status = 'not-started'; t.pct = 0; });
            return r ? {basis: r.pr.basis} : null; }""")
        hs = await pg.evaluate("""() => { const R = pgRows('p121'); const h = R.filter(r => pgLineHold(r));
            const co = R.filter(r => pgIsCO(r.sv) && pgLineHold(r)); return {held: h.map(r => [r.sv.desc, r.pr.basis, pgLineHold(r)]), co: co.length}; }""")
        S.fact(f'held lines now: {hs}')
        S.check(hs['co'] == 0, 'a change order line is never held')
        unit = await pg.evaluate("""() => [pgLineHold({sv: {source: 'Contract', desc: 'x'}, pr: {period: 12, basis: 'cost', extra: '$4,000 spent'}}),
            pgLineHold({sv: {source: 'CO-2026-009', desc: 'x'}, pr: {period: 12, basis: 'cost', extra: ''}}),
            pgLineHold({sv: {source: 'Contract', desc: 'x'}, pr: {period: 12, basis: 'schedule', extra: ''}})]""")
        S.check(bool(unit[0]) and not unit[1] and not unit[2], 'held per line: a contract line measured only by cost is held with its reason; a CO line or a measured line is not', str(unit))
    finally:
        if errs: S.errors.append(f'page errors: {errs[:2]}')
        await b.close()


# ---------------------------------------------------------------- 2. bought for a client, never billed back
async def s2_reimb(p, S):
    b, pg, errs = await boot(p, 'u_controller')
    try:
        # the controller codes the 9/2 Waterworks line (the seed's Amex) to 121 State, as he would from Banking
        await code_txn(pg, 't15', 'materials', JOB, '11', '')
        # the pendants come in on the Amex statement and are coded with the memo the person writes
        rh = ('20260901', -1268.40, 'AMX1009260901026', 'RESTORATION HARDWARE 0412', 'NEW YORK NY')
        await import_statement(pg, 'ac2', 'Amex_1009_Sep2026.ofx', ofx('1009', [rh]))
        t2 = await find_txn(pg, rh[3], rh[1])
        if not t2:
            S.setup_ok = False; S.errors.append('the pendants did not import'); return
        await code_txn(pg, t2, 'materials', JOB, '11', 'Pendants for the Kleins at cost plus 10%')
        R = await pg.evaluate("""() => { const X = rbRows(); const R = readyToBill();
            return {rows: X.map(x => [x.kind, x.label, x.amount]), rtb: R.rows.filter(r => ['reimbursable', 'floated'].includes(r.kind)).map(r => [r.kind, r.amount, r.title]),
                    sp: r2(spUnbilled().reduce((a, r) => a + r.gap, 0)), rb: r2(X.reduce((a, x) => a + x.amount, 0)),
                    nyh: nyhRows({everyone: true}).filter(r => r.kind === 'rebill').map(r => [r.route, r.verb, r.title])}; }""")
        S.fact(f"reimbursable and floated rows: {R['rows']}")
        amts = {x[1][:22]: x[2] for x in R['rows']}
        S.check(any(abs(a - 2090) < 0.01 for a in amts.values()), 'the Waterworks faucet (a client selection) is a reimbursable row at cost plus the job markup ($1,900 -> $2,090)', str(amts))
        S.check(any(abs(a - 1395.24) < 0.01 for a in amts.values()), 'the pendants are billed at cost plus 10% ($1,268.40 -> $1,395.24)', str(amts))
        # lane 1 (TRIAGE class 3): the windows float is what was delivered less what was billed ($29,700 - $19,530 = $10,170); the
        # $3,800 over what was delivered never bills to the client
        S.check(any(x[0] == 'floated' and 'Windows' in x[1] and abs(x[2] - 10170) < 1 for x in R['rows']), 'the $10,170 floated on the windows line is a row (stored materials, delivered less billed)', str(R['rows']))
        S.check(abs(R['sp'] - R['rb']) < 0.01 and R['rb'] > 0, 'spUnbilled reads the same rows: one number', f"spUnbilled {R['sp']} vs rows {R['rb']}")
        S.check(any(r[0] == 'billing' and r[1] == 'Draft' for r in R['nyh']), "billing's Needs Your Hand: Draft the purchases bought for the client", str(R['nyh']))
        row = await billing_row(pg, 'bought for Sarah')
        S.check(row and row['verb'] == 'Draft', 'Billing Queue: the purchases bought for the Kleins, with Draft', str(row))
        await pg.evaluate("""async () => { const tr = [...document.querySelectorAll('#v-billing tr')].find(tr => tr.querySelector('[data-blact]') && /bought for Sarah/.test(tr.innerText));
            tr.querySelector('[data-blact]').click(); await new Promise(r => setTimeout(r, 80)); }""")
        d = await pg.evaluate("""() => { const c = DB.clients.find(x => x.id === 'cl121'), inv = c.invoices.find(i => i.id === (docOpen || {}).id);
            const T = DB.txns.filter(t => /WATERWORKS|RESTORATION/.test(t.desc));
            return inv && {num: inv.number, status: inv.status, lines: inv.lines.map(l => [l.item, l.rate]), stamped: T.map(t => !!t.invoiceLineId),
                           send: [...document.querySelectorAll('section.view.on button')].some(b => b.innerText.trim() === 'Send to Client')}; }""")
        S.check(d and len(d['lines']) == 2 and all(d['stamped']), 'Draft puts both purchases on one invoice and stamps each bank line with its invoice line', str(d))
        S.check(d and d['send'], 'the draft opens with Send to Client', str(d))
        await pg.evaluate("""async () => { const b = [...document.querySelectorAll('section.view.on button')].find(b => b.innerText.trim() === 'Send to Client'); b.click();
            await new Promise(r => setTimeout(r, 60)); document.querySelector('#mbm #mbm-ok').click(); await new Promise(r => setTimeout(r, 150)); }""")
        after = await pg.evaluate("""n => { const c = DB.clients.find(x => x.id === 'cl121'); return {status: c.invoices.find(i => i.number === n).status,
            left: rbRows().filter(x => x.kind === 'reimbursable').length, matched: DB.txns.filter(t => /WATERWORKS|RESTORATION/.test(t.desc)).map(t => !!(truthMatchOf(t).invoiceLineId))}; }""", d['num'] if d else '')
        S.check(after['status'] == 'sent' and after['left'] == 0 and all(after['matched']), 'sent: the rows are gone and each bank line is matched to its invoice line', str(after))
        # the invoice editor's Billable Expenses pull, and the stamp that follows the line
        pull = await pg.evaluate("""async () => { const t = DB.txns.find(x => /HOME DEPOT PRO SCREWS/.test(x.desc)); Object.assign(t, {projectId: 'p121', cat: 'materials', code: '03', status: 'categorized', memo: 'Extra blocking the Kleins asked for: bill back to client'}); save();
            const c = DB.clients.find(x => x.id === 'cl121'); const inv = newDoc(c, 'invoice', {mode: 'items', fields: {projectId: 'p121', title: 'Invoice'}}); save();
            signIn('u_billing'); view = 'billing'; billTab = 'billable'; clientOpen = c.id; docOpen = {kind: 'invoice', id: inv.id}; render(); await new Promise(r => setTimeout(r, 50));
            const b = document.querySelector('[data-lkrbpull]'); const label = b ? b.innerText : 'no button'; b && b.click(); await new Promise(r => setTimeout(r, 60));
            const l = inv.lines.find(x => x.fromTxn === t.id); const stamped = t.invoiceLineId === (l || {}).id;
            inv.lines = inv.lines.filter(x => x !== l); save(); const back = rbRows().some(x => x.t && x.t.id === t.id);
            return {label, added: !!l, rate: l && l.rate, stamped, back}; }""")
        S.check(pull['added'] and pull['stamped'] and abs((pull['rate'] or 0) - 315.37) < 0.01, 'the invoice editor pulls Billable Expenses and stamps invoiceLineId ($286.70 + 10%)', str(pull))
        S.check(pull['back'], 'a billable line taken off a draft is unbilled again (the stamp follows the invoice line)', str(pull))
        # 121 State is billed ahead, so its stored materials wait held (lane 1, the hold design); billing bills them on purpose
        fl = await pg.evaluate("""async () => { const r = rbReady().find(x => x.kind === 'floated'); if (!r) return null; r.run(); await new Promise(r => setTimeout(r, 60));
            const c = DB.clients.find(x => x.id === 'cl121'), inv = c.invoices.find(i => i.id === (docOpen || {}).id);
            return {num: inv && inv.number, win: inv && inv.lines.filter(l => /Windows/.test(l.item)).map(l => [l.pct, l.stored]), left: spUnbilled().filter(r => /Windows/.test(r.label)).length}; }""")
        S.check(fl and fl['win'] and fl['win'][0][1] and fl['left'] == 0, 'Draft on the floated windows row puts the stored materials on the application; spUnbilled no longer lists it', str(fl))
        surf(S, await scan(pg, 'u_owner', 'bank', ['HOME DEPOT PRO SCREWS'], r'bill(ed)? back|bought for the client'), 'Banking: a billable line says it is not billed back, with Bill It')
    finally:
        if errs: S.errors.append(f'page errors: {errs[:2]}')
        await b.close()


# ---------------------------------------------------------------- 3. a refund on a purchase billed to the client
async def s3_credit(p, S):
    b, pg, errs = await boot(p, 'u_controller')
    try:
        nemo = ('20260902', 850.00, '202609020031', 'NEMO TILE SUPPLY CREDIT RTN 88412', 'CREDIT MEMO')
        await import_statement(pg, 'ac1', 'Chase_Checking_4471_Sep2026.qfx', ofx('4471', [nemo], card=False))
        t = await find_txn(pg, nemo[3], nemo[1])
        if not t:
            S.setup_ok = False; S.errors.append('the credit did not import'); return
        row = await billing_row(pg, 'Credit the client')
        S.check(row and row['verb'] == 'Draft' and '850' in row['text'], 'Billing Queue: the client is owed the $850 credit, with Draft', str(row))
        nyh = await pg.evaluate("() => nyhRows({everyone: true}).filter(r => r.kind === 'clientcredit').map(r => [r.route, r.verb, r.title])")
        S.check(any(r[0] == 'billing' and r[1] == 'Draft' for r in nyh), "billing's Needs Your Hand: credit the Kleins", str(nyh))
        await pg.evaluate("""async () => { const tr = [...document.querySelectorAll('#v-billing tr')].find(tr => tr.querySelector('[data-blact]') && /Credit the client/.test(tr.innerText));
            tr.querySelector('[data-blact]').click(); await new Promise(r => setTimeout(r, 80)); }""")
        d = await pg.evaluate("""() => { const c = DB.clients.find(x => x.id === 'cl121'); const inv = c.invoices.find(i => i.id === (docOpen || {}).id);
            const cc = (DB.clientCredits || [])[0] || {};
            return {inv: inv && [inv.number, inv.status, inv.date, inv.lines.map(l => [l.item, l.rate])], cc: [cc.status, !!cc.invoiceLineId],
                    left: billingRows().filter(r => r.kind === 'credit').length, shape: c.invoices.concat(c.creditMemos || []).some(i => (i.date || '') >= today() && (i.lines || []).some(l => +l.rate < 0 || /credit/i.test((l.desc || '') + ' ' + (l.item || ''))))}; }""")
        S.check(d['inv'] and any(l[1] == -850 for l in d['inv'][3]), 'Draft puts a -$850 credit line on an invoice to the Kleins, stamped on the credit', str(d))
        S.check(d['left'] == 0 and d['cc'] == ['approved', True] and d['shape'], 'the credit leaves the queue once it is on an invoice (billing drafted it: approved)', str(d))
    finally:
        if errs: S.errors.append(f'page errors: {errs[:2]}')
        await b.close()


# ---------------------------------------------------------------- 4. every bank line matched to a line
async def s4_match(p, S):
    b, pg, errs = await boot(p, 'u_controller')
    try:
        # payroll: the controller builds the 8/31 run from approved time on 9/9; the owner approves it
        mk = await pg.evaluate("""() => { appSetDay('2026-09-09'); DB.time.filter(t => t.status === 'submitted').forEach(t => t.status = 'approved'); save();
            signIn('u_controller'); const n0 = DB.payroll.length; payrollFromTime(); const R = DB.payroll.slice(n0); return R.map(r => [r.id, r.period, r.total, r.payDate]); }""")
        S.fact(f'runs built: {mk}')
        await pg.evaluate("() => appSetDay('2026-09-11')")
        out = await import_statement(pg, 'ac1', 'chase_0911.csv', csv([('2026-09-11', 'PAYROLL SERVICE NET PAY', -14980, 'AC1-0911-1'), ('2026-09-11', 'PAYROLL SERVICE TAX', -3120, 'AC1-0911-2')]))
        P = await pg.evaluate("""() => DB.txns.filter(t => /PAYROLL SERVICE/.test(t.desc)).map(t => [t.desc, t.proposal && t.proposal.kind, t.proposal && t.proposal.label])""")
        S.check(len(P) == 2 and all(x[1] == 'payroll' for x in P), 'the payroll net pay and tax debits are proposed against their run', str(P))
        conf = await pg.evaluate("""async () => { signIn('u_controller'); view = 'bank'; render(); await new Promise(r => setTimeout(r, 50));
            const B = [...document.querySelectorAll('#v-bank [data-mconfirm]')].filter(b => /PAYROLL/.test((b.closest('.prop-row') || {}).innerText || ''));
            for (const b of B) { b.click(); await new Promise(r => setTimeout(r, 30)); }
            return DB.txns.filter(t => /PAYROLL SERVICE/.test(t.desc)).map(t => [t.desc, truthMatchOf(t).payrollId || '']); }""")
        S.check(conf and all(x[1] for x in conf), 'Confirm on Banking matches each debit to the payroll run', str(conf))
        # card charges and an ACH deposit against their orders
        await pg.evaluate("""() => { const mkPO = (id, num, vendor, item, amt, date, exp) => DB.pos.push({id, number: num, projectId: 'p121', vendor, date, expected: exp, status: 'issued', shipTo: 'Site', notes: '',
                // priced with no NY tax charged on them (the one purchase-tax rule accrues use tax and keeps the order total)
                lines: [{id: id + 'l', item, desc: '', qty: 1, unit: 'ls', price: amt, received: 0, line: ''}], useTax: true});
            mkPO('lkpo1', 'PO-2026-090', 'Ferguson', 'Plumbing fixtures (both baths, kitchens)', 11980, '2026-09-14', '2026-10-05');
            mkPO('lkpo2', 'PO-2026-091', 'Gowanus Stone Yard', 'Parlor kitchen countertop slab', 7450, '2026-09-10', '2026-09-24');
            DB.vendors.push({id: 'vlkt', name: 'Tomas Restoration', insuranceExp: '2026-09-15', w9: true}); save(); appSetDay('2026-09-28'); }""")
        await import_statement(pg, 'ac2', 'amex_0928.csv', csv([('2026-09-23', 'FERGUSON #1124 BROOKLYN', -11980, 'AC2-0923-1')]))
        await import_statement(pg, 'ac1', 'chase_0928.csv', csv([('2026-09-28', 'ACH DEBIT GOWANUS STONE YARD', -3725, 'AC1-0928-1'), ('2026-09-15', 'CHECK 2216 TOMAS RESTORATION', -2750, 'AC1-0915-1')]))
        P2 = await pg.evaluate("""() => ['FERGUSON', 'GOWANUS', 'CHECK 2216'].map(k => { const t = DB.txns.find(x => x.desc.includes(k)); return [k, t && t.proposal && t.proposal.kind, t && t.proposal && t.proposal.label]; })""")
        S.check(P2[0][1] == 'po' and P2[1][1] == 'po', 'the Ferguson card charge and the stone yard deposit are proposed against their POs', str(P2))
        S.check(P2[2][1] == 'newbill' and 'Insurance' in (P2[2][2] or ''), 'check 2216 with no bill proposes entering the bill, and names the expiring COI', str(P2[2]))
        done = await pg.evaluate("""() => { const T = DB.txns.filter(t => /FERGUSON|GOWANUS|CHECK 2216/.test(t.desc)); T.forEach(t => confirmMatch(t)); save();
            return T.map(t => { const m = truthMatchOf(t), b = DB.bills.find(x => x.id === m.billId); return [t.desc, m.poId || '', m.billId ? (b.vendor + ' ' + b.status + (b.paidBeforeApproval ? ' paid-before-approval' : '')) : '']; }); }""")
        S.check(all(x[1] or x[2] for x in done) and any('Tomas' in x[2] and 'paid-before-approval' in x[2] for x in done), 'confirmed: each charge reaches its PO; the check reaches a bill entered from it, flagged paid before approval', str(done))
        # a cost typed by hand with no bank line
        await pg.evaluate("() => { setCurrent('p121'); view = 'bank'; render(); txnDialog(); }")
        await pg.wait_for_selector('#e-desc', state='attached')
        await pg.fill('#e-date', '2026-09-21'); await pg.select_option('#e-acct', 'ac1'); await pg.fill('#e-desc', 'Cash at lumber yard (receipt lost)')
        await pg.fill('#e-amt', '-300'); await pg.select_option('#e-cat', 'materials'); await pg.select_option('#e-proj', JOB); await pg.select_option('#e-code', '03')
        await pg.click('#d-save'); await pg.wait_for_timeout(150)
        surf(S, await scan(pg, 'u_controller', 'bank', ['Cash at lumber yard'], r'no bank line'), 'Banking: the hand-typed cost is flagged "no bank line", with Match to a Line')
        ty = await pg.evaluate("""() => { const t = DB.txns.find(x => /Cash at lumber yard/.test(x.desc)); const C = truthCandidates(t); const best = C[0];
            best && best.auto && truthSetMatch(t, best.m, {why: best.why}); return {best: best && [best.kind, best.label, best.auto], matched: !!txnMatch(t), flag: txnFlagsHtml(t).includes('No bank line')}; }""")
        S.check(ty['best'] and ty['best'][2] and ty['matched'] and ty['flag'], 'the typed cost is matched to its estimate line by its job and code, and still says no bank line', str(ty))
    finally:
        if errs: S.errors.append(f'page errors: {errs[:2]}')
        await b.close()


async def nyh_press(pg, key_re):
    """Run a Needs Your Hand row as its person would (nyhRun, the row's verb), then press the sheet's blue button."""
    return await pg.evaluate("""async (k) => { const r = nyhRows().find(x => new RegExp(k).test(x.key)); if (!r) return 'no row';
        nyhRun(r.key); await new Promise(z => setTimeout(z, 80)); const m = document.querySelector('#mbm');
        const t = m ? (m.querySelector('h3') || {}).innerText : ''; const ok = m && m.querySelector('#mbm-ok'); ok && ok.click(); await new Promise(z => setTimeout(z, 120));
        return 'ran ' + r.verb + (t ? ' > ' + t : '') + (ok ? ' > ' + ok.innerText : ''); }""", key_re)


# ---------------------------------------------------------------- 5. a duplicate charge at import
async def s5_dup(p, S):
    b, pg, errs = await boot(p, 'u_controller')
    try:
        await import_statement(pg, 'ac2', 'amex_dup.csv', csv([('2026-09-01', 'ROLL OFF DUMPSTER SVC BKLYN', -1650, 'AC2-0901-D1'), ('2026-09-02', 'ROLL OFF DUMPSTER SVC BKLYN', -1650, 'AC2-0902-D2')]))
        st = await pg.evaluate("""() => DB.txns.filter(t => /ROLL OFF DUMPSTER SVC BKLYN/.test(t.desc)).map(t => [t.date, t.dupState || '', bfBacked(t)])""")
        S.check(any(x[1] == 'proposed' for x in st) and sum(1 for x in st if x[1]) == 1, 'the import flags the second charge (same payee and amount, next day) as a proposed duplicate', str(st))
        rows = await pg.evaluate("() => nyhRows().filter(r => r.kind === 'dup').map(r => [r.verb, r.title])")
        S.check(any('Charged twice' in r[1] and r[0] == 'Confirm' for r in rows), "the controller's Needs Your Hand: Charged twice, Confirm", str(rows))
        did = await nyh_press(pg, 'lk:dup:' + (await pg.evaluate("() => (DB.txns.find(t => t.dupState === 'proposed' && /BKLYN/.test(t.desc)) || {}).id || ''")))
        d = await pg.evaluate("() => DB.txns.filter(t => /ROLL OFF DUMPSTER SVC BKLYN/.test(t.desc)).map(t => [t.date, t.dupState || '', !!t.dispute, !!t.exception, t.memo || ''])")
        S.check(any(x[2] and x[3] and 'Disputed' in x[4] for x in d), 'Confirm disputes the bank-held copy with the issuer, with a reason, and it closes with that exception', f'{did}; {d}')
        # the seed's typed pair (8/21 and 8/22): the typed copy is voided, not disputed
        seed = await pg.evaluate("() => { lkDupScan(); return DB.txns.filter(t => t.desc === 'ROLL OFF DUMPSTER SVC').map(t => [t.id, t.date, t.dupState || '']); }")
        did2 = await nyh_press(pg, 'lk:dup:ta7')
        v = await pg.evaluate("() => (DB.voided || []).filter(t => /DUMPSTER/.test(t.desc)).map(t => [t.date, t.voidWhy])")
        S.check(v and 'Void' in did2, 'the typed duplicate of the seed (8/22) is voided with the reason', f'{seed}; {did2}; {v}')
    finally:
        if errs: S.errors.append(f'page errors: {errs[:2]}')
        await b.close()


# ---------------------------------------------------------------- 6. a statement in mail
async def s6_stmt(p, S):
    b, pg, errs = await boot(p, 'u_controller')
    try:
        await pg.evaluate("""() => cmImport([{ msgId: 'lk-amex-aug', threadId: 'lk-amex', from: 'American Express <noreply@amex-statements.example>', to: ['controller@smartdesign.nyc'],
              date: '2026-09-02T07:00:00', subject: 'Your August statement is ready — account ending 1009', text: 'Your Business Platinum statement is ready.',
              attachments: [{ name: 'Amex-Aug-2026.pdf', type: 'application/pdf', text: DW_DOCS.amexStatement() }] }])""")
        pr = await pg.evaluate("() => { const c = DB.comms.find(x => x.msgId === 'lk-amex-aug'); return c ? (c.proposals || []).map(p => [p.kind, p.acctId || '', p.summary]) : null; }")
        # August is imported for the Amex (Jeanette's activity file, 9/1), but four of the statement's lines (9/1-9/2)
        # are on the books only as typed by hand, so the statement is not "already here": importing it backs them
        # (cmStmtImport: every line from the bank, not the month). The summary says so, so it does not read as a duplicate.
        S.check(pr and any(x[0] == 'statement' and x[1] and 'no bank line on the books' in x[2] for x in pr), 'the Amex statement is read as our card statement, with the lines the books hold only by hand', str(pr))
        tasks0 = await pg.evaluate("() => DB.projects.flatMap(p => p.actions || []).concat(DB.tasks || []).filter(a => /Import the/.test(a.title || '')).length")
        dlg = await pg.evaluate("""async () => { const r = nyhRows().find(x => x.kind === 'mail' && x.pkind === 'statement'); if (!r) return {err: 'no row'}; nyhRun(r.key); await new Promise(z => setTimeout(z, 150));
            const m = document.querySelector('#mbm'); return {verb: r.verb, title: m && (m.querySelector('h3') || {}).innerText, ok: m && m.querySelector('#mbm-ok').innerText, plan: m && (m.querySelector('.bf-plan') || {}).innerText}; }""")
        S.check(dlg.get('title') == 'Import Statement' and 'Line' in (dlg.get('ok') or ''), "one tap on the controller's Needs Your Hand opens Import Statement with the statement's lines", str(dlg))
        tasks1 = await pg.evaluate("() => DB.projects.flatMap(p => p.actions || []).concat(DB.tasks || []).filter(a => /Import the/.test(a.title || '')).length")
        S.check(tasks1 == tasks0, 'no task to import it later', f'{tasks0} -> {tasks1}')
        rec = await pg.evaluate("""async () => { document.querySelector('#mbm #mbm-ok').click(); await new Promise(z => setTimeout(z, 200));
            const m = document.querySelector('#mbm'); return {imports: (DB.bankImports || []).filter(i => i.acctId === 'ac2').map(i => [i.fileName, i.period, i.ending, i.added, i.confirmed, i.dup]), sheet: m && (m.querySelector('h3') || {}).innerText, body: m && m.innerText.slice(0, 200)}; }""")
        S.check(rec['imports'] and rec['sheet'] and 'Reconcile' in rec['sheet'], 'Import is followed by the reconcile', str(rec))
        # the same statement again, once its lines are in from the bank: already here, and no one's row (pilot day 1:
        # the controller's Approvals offered statements already imported, which read as duplicates)
        await pg.evaluate("() => mbCloseModal()")
        await pg.evaluate("""() => cmImport([{ msgId: 'lk-amex-aug2', threadId: 'lk-amex2', from: 'American Express <noreply@amex-statements.example>', to: ['controller@smartdesign.nyc'],
              date: '2026-09-02T09:00:00', subject: 'Reminder: your August statement — account ending 1009', text: 'Your Business Platinum statement is ready.',
              attachments: [{ name: 'Amex-Aug-2026.pdf', type: 'application/pdf', text: DW_DOCS.amexStatement() }] }])""")
        again = await pg.evaluate("() => { const c = DB.comms.find(x => x.msgId === 'lk-amex-aug2'); const p = c && (c.proposals || []).find(p => p.kind === 'statement'); return { here: !!(p && p.alreadyHere), row: nyhRows().some(r => r.commId === (c && c.id)), sum: p && p.summary }; }")
        S.check(again['here'] and not again['row'], 'once imported, the same statement reads already here and is no one\'s row', str(again))
    finally:
        if errs: S.errors.append(f'page errors: {errs[:2]}')
        await b.close()


# ---------------------------------------------------------------- 7. one payroll run per pay period
async def s7_payroll(p, S):
    b, pg, errs = await boot(p, 'u_controller')
    try:
        r = await pg.evaluate("""() => { appSetDay('2026-09-09'); DB.time.filter(t => t.status === 'submitted').forEach(t => t.status = 'approved'); signIn('u_controller');
            const n0 = DB.payroll.length; payrollFromTime(); payrollFromTime(); const R = DB.payroll.slice(n0); const run = R[0];
            const hrs = DB.time.filter(t => t.payrollId === run.id); payrollAction(run, 'approve');
            return {n: R.length, total: run.total, ents: (run.entities || []).map(e => [e.entityId, e.total]), sum: hrs.length, status: run.status,
                    same: Math.abs((run.entities || []).reduce((a, e) => a + e.total, 0) - run.total) < 0.02}; }""")
        S.check(r['n'] == 1 and len(r['ents']) == 3 and r['same'], 'one run for the pay period across the three entities, each share inside it and adding to the total', str(r))
        S.check(r['status'] == 'submitted', 'the controller who built it cannot approve it (separation of duties)', r['status'])
        g = await pg.evaluate("""async () => { const run = DB.payroll.slice(-1)[0]; const t0 = run.total;
            DB.time.push({id: 'telk1', empId: 'em2', date: '2026-09-09', in: '2026-09-09T07:00:00', out: '2026-09-09T15:30:00', breakMin: 30, projectId: 'p121', code: '05', notes: '', status: 'approved', approvedBy: 'Alan', source: 'manual', work: [{projectId: 'p121', code: '05', hours: 8, note: ''}]});
            appSetDay('2026-09-10'); const t1 = run.total; signIn('u_owner'); const why = 'Hours cover the field crew; office time is overhead.'; payrollAction(run, 'approve', why);
            // the Owner answers the size check (this run is smaller than the past runs' average) and approves
            const m = document.querySelector('#mbm'); if (m && run.status !== 'approved') { m.querySelector('#mbm-ok').click(); await new Promise(z => setTimeout(z, 60)); run.status !== 'approved' && payrollAction(run, 'approve', why); }
            const L = glPayrollLines(run), by = {}; L.forEach(l => { const k = l.entityId || '?'; by[k] = r2((by[k] || 0) + (l.dr || 0) - (l.cr || 0)); });
            return {t0, t1, status: run.status, inRun: DB.time.find(t => t.id === 'telk1').payrollId === run.id, balanced: Object.values(by).every(v => Math.abs(v) < 0.02), ents: Object.keys(by)}; }""")
        S.check(g['inRun'] and g['t1'] > g['t0'], 'hours approved after the run was built join it the next morning, until it is approved', str(g))
        S.check(g['status'] == 'approved' and g['balanced'] and len(g['ents']) == 3, "the Owner approves it; each entity's share posts to its own books, balanced", str(g))
    finally:
        if errs: S.errors.append(f'page errors: {errs[:2]}')
        await b.close()


# ---------------------------------------------------------------- 8. a vendor credit memo closes the dispute
async def s8_dispute(p, S):
    b, pg, errs = await boot(p, 'u_owner')
    try:
        d = await pg.evaluate("""() => { const b = DB.bills.find(x => x.number === 'WW-2026-118'); const ok = pay3ShortPay(b, 29700, 'Approved at the PO amount; the difference is disputed');
            return {ok, short: b.short && [b.short.approved, b.short.held, b.short.state]}; }""")
        S.fact(f'WW-2026-118 short-paid: {d}')
        await pg.evaluate("""() => cmImport([{ msgId: 'lk-ww-cm', threadId: 'lk-ww', from: 'Window Works <quotes@windowworks.example>', to: ['alan@smartdesign.nyc', 'chen@smartdesign.nyc'],
              date: '2026-09-03T09:20:00', subject: 'Credit memo CM-WW-031 — PO-2026-044', text: 'Credit memo CM-WW-031 for $3,800 against WW-2026-118, as discussed. Window Works',
              attachments: [{ name: 'CM-WW-031.pdf', type: 'application/pdf', text: 'WINDOW WORKS LLC\\nCredit Memo CM-WW-031\\nAgainst invoice WW-2026-118, PO-2026-044\\nCredit $3,800.00' }] }])""")
        pr = await pg.evaluate("() => { const c = DB.comms.find(x => x.msgId === 'lk-ww-cm'); return c ? (c.proposals || []).map(p => [p.kind, p.summary]) : null; }")
        S.check(pr and any(x[0] == 'dispute-credit' for x in pr) and not any(x[0] in ('credit', 'bill') for x in pr), 'the credit memo is read as closing the held difference, not as a return or a bill', str(pr))
        await pg.evaluate("() => { signIn('u_owner'); view = 'home'; render(); }")
        rows = await pg.evaluate("() => PRED.waitingOnMe.rows().filter(x => /CM-WW-031|WW-2026-118/.test((x.title || '') + (x.detail || ''))).map(x => [x.kind, x.yes || x.verb || '', x.title])")
        S.check(rows and any(r[1] == 'Approve' for r in rows), "the Owner's Do Now: the credit memo, with Approve", str(rows))
        await pg.evaluate("async () => { const r = nyhRows().find(x => x.pkind === 'dispute-credit'); r && nyhRun(r.key); await new Promise(z => setTimeout(z, 80)); }")
        st = await pg.evaluate("() => { const b = DB.bills.find(x => x.number === 'WW-2026-118'); return b.short; }")
        S.check(st and st.get('state') == 'credited' and st.get('resolved') and st.get('credited'), 'one approval records the credit: the held $3,800 closes', str(st))
        # no credit memo: at month end the Owner settles it, accepting the difference with a reason
        acc = await pg.evaluate("""async () => { const b = DB.bills.find(x => x.number === 'WW-2026-118'); b.short.state = 'open'; delete b.short.resolved; save(); appSetDay('2026-09-29'); signIn('u_owner');
            const r = nyhRows().find(x => x.key === 'lk:disp:' + b.id); if (!r) return {err: 'no row'}; nyhRun(r.key); await new Promise(z => setTimeout(z, 60));
            const m = document.querySelector('#mbm'); const w = m && m.querySelector('[data-f="why"]'); w && (w.value = 'Field-added unit; the Kleins approved it'); m && m.querySelector('#mbm-ok').click(); await new Promise(z => setTimeout(z, 80));
            return {verb: r.verb, state: b.short.state, resolved: b.short.resolved}; }""")
        S.check(acc.get('state') == 'accepted' and acc.get('resolved'), "by month end the Owner's Do Now offers Accept the Difference, with a reason", str(acc))
    finally:
        if errs: S.errors.append(f'page errors: {errs[:2]}')
        await b.close()


SCENARIOS = [
    (1, 'earned', 'Earned, not billed: hold per line; CO lines from 0; a drafted application says Send', s1_earned),
    (2, 'reimb', 'Bought for a client: reimbursable rows billed at cost plus markup, one number with spUnbilled', s2_reimb),
    (3, 'credit', 'A refund on a purchase billed to the client: a client credit drafted onto an invoice', s3_credit),
    (4, 'match', 'Every bank line matched to a line: payroll runs, POs, a bill from a check, a typed cost', s4_match),
    (5, 'dup', 'A duplicate charge at import: a proposed dispute (or void) on the controller\'s Needs Your Hand', s5_dup),
    (6, 'stmt', 'A statement in mail: one tap opens Import Statement, then the reconcile; no task', s6_stmt),
    (7, 'payroll', 'One payroll run per pay period across entities, built from every hour approved by its date', s7_payroll),
    (8, 'dispute', 'A vendor credit memo closes the held difference with one approval; or the Owner accepts it', s8_dispute),
]


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scenario', default='')
    a = ap.parse_args()
    want = {x.strip() for x in a.scenario.split(',') if x.strip()}
    todo = [s for s in SCENARIOS if not want or str(s[0]) in want or s[1] in want]
    results = []
    async with async_playwright() as p:
        for num, key, title, fn in todo:
            S = Scenario(num, key, title)
            try:
                await fn(p, S)
            except Exception as e:
                S.setup_ok = False
                S.errors.append(f'{type(e).__name__}: {str(e)[:300]}')
            S.report()
            results.append(S)
    flags = sum(1 for S in results if S.verdict() != 'CAUGHT')
    print(f"\n{' · '.join(f'{S.num} {S.verdict()}' for S in results)}")
    print(f'{flags} flags')
    sys.exit(1 if flags else 0)


if __name__ == '__main__':
    asyncio.run(main())
