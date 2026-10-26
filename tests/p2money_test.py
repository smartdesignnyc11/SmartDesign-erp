"""Pilot 2's money findings (lane p2fix2), each reproduced the way the controller and billing hit it, on the desktop and
the phone, and proven to the cent. Invented data only: the seed, its demo mailboxes and the records each check adds.

1  S1 One vendor invoice booked twice. Satish SE-0922 ($7,400, paid by the 9/2 ACH): Today's Enter the Bill, then
   Banking's "no bill on file" Confirm, made SE-0922 and PAY-260902 on one ACH. Every bill path now asks one finder
   (vbFind: vendor + invoice number, or the same bank line, or vendor + amount inside ten days) before it adds a bill,
   in both orders, on the bill form, and the warning comes before the save.
2  S1 Blind one-tap posting. Enter the Bill opens the bill, filled in (vendor, number, amount, job, cost code,
   estimate line, bank line, approval route), enters nothing until Enter the Bill, and toasts its true status with an
   Open link that opens the bill.
3  S1 Cash with no bank line. Apply on a client's "money is sent" mail opens Record Payment on the bank line when the
   bank has it, else records an expectation (never a payment, never a task); the recorded receipt leaves Needs
   Category, and no bank-line posting shows in Made Today as a journal someone made.
4  S2 Record Payment takes the bank line's amount ($12,000), not the invoice's ($24,000), and the person picks the line.
5  S2 Two Tino invoices on PO-2026-047 a day apart are flagged together on Today, on the PO and in Approvals.
6  S3 A grid's subline is its own words ("Payroll 8/31 - 9/4 6 employees", never "9/46 employees").
7  Billed ahead of the work, line by line (INV-2026-038 at 51.67% on lines 0-20% complete, CO-2026-001 50% at 0%):
   on the pay application, the Billing Queue row and Today, with the dollar amount; billing further needs a reason."""
import asyncio, re, sys
from harness import *

SLEEP = "ms => new Promise(r => setTimeout(r, ms))"


async def js(pg, body, arg=None):
    return await pg.evaluate("async (arg) => { const sleep = " + SLEEP + "; " + body + " }", arg)


async def fresh(p, uid, phone=False):
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, uid)
    return b, pg, errs


# the ledger's cash in the Chase account, from every posted journal (postings and reversals)
CASH = "(() => { glSync(); return r2((DB.gl.journals || []).reduce((a, j) => a + (j.lines || []).filter(l => l.acct === 'acct:ac1').reduce((s, l) => s + (+l.dr || 0) - (+l.cr || 0), 0), 0)); })()"
SATISH = """
  const sat = () => DB.bills.filter(b => /satish/i.test(b.vendor) && !['void', 'rejected'].includes(b.status));
  const satPays = () => r2((DB.payments || []).filter(p => !p.void && sat().some(b => b.id === p.billId)).reduce((a, p) => a + (+p.amount || 0), 0));
  const t16 = DB.txns.find(x => x.id === 't16');
"""


# ------------------------------------------------------------------------------------------------ 1 and 2: Satish
async def t_satish_today_first(c, p, phone):
    dev = 'phone' if phone else 'desktop'
    b, pg, errs = await fresh(p, 'u_controller', phone)
    r = await js(pg, SATISH + """
      await gcDemoConnect(); try { clearInterval(gsTimerId); } catch (e) {}
      truthProposeAll();                                   // the evening's proposals, as the pilot had them
      const cash0 = """ + CASH + """, prop0 = t16.proposal && t16.proposal.kind;
      view = 'home'; render(); await sleep(250);
      nyhInvalidate();
      const row = nyhRows({ role: 'controller' }).find(r => r.key === 'mail:bill:se-0922');
      const n0 = sat().length;
      row.run(); await sleep(350);
      const m = document.getElementById('mbm');
      const vals = m ? Object.fromEntries([...m.querySelectorAll('[data-f]')].map(i => [i.dataset.f, i.value])) : {};
      const sheet = m && { title: m.querySelector('h3').innerText, vals, ok: m.querySelector('#mbm-ok').innerText,
        route: m.querySelector('#vb-route').innerText, line: (m.querySelector('[data-f="line"]').selectedOptions[0] || {}).text || '',
        bank: (m.querySelector('[data-f="txnId"]').selectedOptions[0] || {}).text || '',
        sw: document.documentElement.scrollWidth, okH: m.querySelector('#mbm-ok').getBoundingClientRect().height };
      const n1 = sat().length, applied1 = !!(DB.comms.find(x => /SE-0922/.test(x.subject)).proposals[0].applied);
      m.querySelector('#mbm-ok').click(); await sleep(400);
      const toastEl = document.getElementById('toast'), toastT = (toastEl || {}).innerText || '';
      const B = sat()[0] || {};
      const bill = { n: sat().length, number: B.number, status: B.status, txn: B.txnId, pba: billPaidUnapproved(B), code: B.code, line: B.line, pid: B.projectId, tot: billTotal(B) };
      const tl = { billId: t16.billId, prop: t16.proposal, inPBA: billsPaidUnapproved().some(x => x.id === B.id) };
      // the toast's Open opens that bill
      const open = toastEl && [...toastEl.querySelectorAll('a, button')].find(a => /Open/.test(a.textContent));
      open && open.click(); await sleep(400);
      const opened = !!(editing && editing.id === B.id);
      try { closeEditor(); } catch (e) {}
      // Banking: the stale "no bill on file" card is gone; put it back the way the pilot saw it, and press Confirm
      view = 'bank'; render(); await sleep(300);
      const card = [...document.querySelectorAll('.prop-card .prop-row')].map(x => x.innerText).filter(x => /SATISH/i.test(x));
      t16.proposal = { t: nowStamp(), by: 'auto', kind: 'newbill', m: { newBill: { vendor: 'Satish Electric Inc', vendorId: 'v5', amount: 7400, number: '', cat: 'subs' } }, why: 'paid to Satish Electric Inc', label: 'Paid before approval: Satish Electric Inc $7,400, no bill on file' };
      const conf = confirmMatch(t16); await sleep(150);
      // and the payment path a bank line takes with no proposal at all (truthSetMatch newBill)
      const viaSet = truthSetMatch(t16, { newBill: { vendor: 'Satish Electric Inc', vendorId: 'v5', amount: 7400, number: '' } });
      return { prop0, n0, n1, applied1, sheet, toastT, bill, tl, opened, card, nAfter: sat().length, pays: satPays(), cash0, cash1: """ + CASH + """, viaSet: viaSet && viaSet.ok };""")
    s = r['sheet'] or {}
    v = s.get('vals', {})
    c.ok(r['prop0'] == 'newbill', f"{dev} satish: the evening's proposal is the pilot's 'no bill on file' ({r['prop0']})")
    c.ok(s and r['n1'] == r['n0'] == 0 and not r['applied1'], f"{dev} satish: Enter the Bill opens the review and enters nothing ({r['n0']}->{r['n1']}, applied {r['applied1']})")
    c.ok(v.get('vendor') == 'Satish Electric Inc' and v.get('number') == 'SE-0922' and v.get('amount') == '7400' and v.get('projectId') == 'p121'
         and v.get('code') == '06' and 'Electrical' in s.get('line', '') and v.get('txnId') == 't16',
         f"{dev} satish: the review is filled in: vendor, number, amount, job, cost code, estimate line, bank line ({v}, {s.get('line')!r})")
    c.ok('SATISH' in s.get('bank', '') and '$7,400' in s.get('bank', ''), f"{dev} satish: the bank match names the 9/2 ACH ({s.get('bank')!r})")
    c.ok('Paid Before Approval' in s.get('route', '') and 'approv' in s.get('route', ''), f"{dev} satish: the review says who approves and that it was paid first ({s.get('route')!r})")
    c.ok(s.get('ok') == 'Enter the Bill', f"{dev} satish: one primary, Enter the Bill ({s.get('ok')!r})")
    if phone:
        c.ok(s.get('sw', 999) <= 390 and s.get('okH', 0) >= 40, f"phone satish: the review fits 390px and its button is a thumb target ({s.get('sw')}, {s.get('okH')})")
    B = r['bill']
    c.ok(B['n'] == 1 and B['number'] == 'SE-0922' and B['status'] == 'submitted' and B['txn'] == 't16' and B['tot'] == 7400,
         f"{dev} satish: one bill, SE-0922, $7,400.00, waiting for approval, paid by t16 ({B})")
    c.ok(B['pba'] and r['tl']['inPBA'] and B['code'] == '06' and B['pid'] == 'p121' and B['line'],
         f"{dev} satish: it is under Paid Before Approval with its job, code and line ({B}, {r['tl']})")
    c.ok('SE-0922' in r['toastT'] and 'Paid Before Approval' in r['toastT'] and 'submitted for approval' not in r['toastT'] and 'Open' in r['toastT'],
         f"{dev} satish: the toast says the true status, with Open ({r['toastT']!r})")
    c.ok(r['opened'], f"{dev} satish: the toast's Open opens the bill")
    c.ok(not r['card'], f"{dev} satish: Banking shows no 'no bill on file' card for the paid ACH ({r['card']})")
    c.ok(r['nAfter'] == 1 and r['pays'] == 7400 and r['viaSet'], f"{dev} satish: Confirm on the stale card adds no second bill; payments total $7,400.00 ({r['nAfter']}, {r['pays']})")
    c.ok(r['cash1'] == r['cash0'], f"{dev} satish: ledger cash in Chase is unchanged to the cent: the ACH counts once ({r['cash0']} -> {r['cash1']})")
    c.ok(not errs, f'{dev} satish: no page errors ({errs[:2]})')
    await b.close()


async def t_satish_bank_first(c, p):
    # the other order: Banking's Confirm enters the bill from the payment first, then the invoice mail arrives
    b, pg, errs = await fresh(p, 'u_controller')
    r = await js(pg, SATISH + """
      await gcDemoConnect(); try { clearInterval(gsTimerId); } catch (e) {}
      truthProposeAll(); const cash0 = """ + CASH + """;
      confirmMatch(t16); await sleep(150);
      const first = sat().map(b => b.number);
      nyhInvalidate();
      const row = nyhRows({ role: 'controller' }).find(r => r.key === 'mail:bill:se-0922');
      row.run(); await sleep(350);
      const m = document.getElementById('mbm'), warn = m.querySelector('#vb-warn').innerText, ok = m.querySelector('#mbm-ok').innerText;
      m.querySelector('#mbm-ok').click(); await sleep(350);
      const t = (document.getElementById('toast') || {}).innerText || '';
      return { first, warn, ok, after: sat().map(b => [b.number, b.txnId, b.commId ? 1 : 0]), pays: satPays(), t, cash0, cash1: """ + CASH + """ };""")
    c.ok(r['first'] and r['first'][0].startswith('PAY-'), f"bank first: Confirm entered the bill from the payment ({r['first']})")
    c.ok('Already on file' in r['warn'] and 'PAY-' in r['ok'], f"bank first: the review says the payment's bill is on file, before anything is entered ({r['warn'][:120]!r}, {r['ok']!r})")
    c.ok(len(r['after']) == 1 and r['after'][0][0] == 'SE-0922' and r['after'][0][1] == 't16' and r['after'][0][2] == 1,
         f"bank first: still one bill; the invoice's number and mail go on it ({r['after']})")
    c.ok(r['pays'] == 7400 and r['cash1'] == r['cash0'], f"bank first: one $7,400.00 payment, cash unchanged ({r['pays']}, {r['cash0']} -> {r['cash1']})")
    c.ok('no second bill' in r['t'] and 'Open' in r['t'], f"bank first: the toast says so, with Open ({r['t']!r})")
    c.ok(not errs, f'bank first: no page errors ({errs[:2]})')
    await b.close()


async def t_bill_form(c, p):
    # the bill form: the same invoice typed again stops before the save; a near one asks the person
    b, pg, errs = await fresh(p, 'u_controller')
    r = await js(pg, SATISH + """
      setCurrent('p121');
      const B = { id: uid('b'), vendor: 'Satish Electric Inc', number: 'SE-0922', date: '2026-08-31', due: '2026-09-30', entityId: 'ent1', projectId: 'p121', cat: 'subs', code: '06', line: '',
        lines: [{ id: uid('bl'), desc: 'rough electric', amount: 7400 }], status: 'submitted', approvals: [], createdBy: 'test' };
      vbAdd(B);
      view = 'ap'; render(); await sleep(200);
      const fill = (num, amt) => { openBill(); document.querySelector('#e-vendor').value = 'Satish Electric Inc'; document.querySelector('#e-number').value = num; document.querySelector('#e-date').value = '2026-09-01';
        const tr = document.querySelector('tr[data-bl] [data-f="amount"]'); tr && (tr.value = amt); };
      fill('se 0922', 7400); const n0 = sat().length;
      saveBill(); await sleep(200);
      const w1 = (document.querySelector('#drawer .vb-dup') || {}).innerText || '', n1 = sat().length;
      try { closeEditor(); } catch (e) {}
      fill('SE-0931', 7400); saveBill(); await sleep(200);
      const w2 = (document.querySelector('#drawer .vb-dup') || {}).innerText || '', n2 = sat().length;
      const ack = document.querySelector('#drawer [data-vback]'); ack && ack.click(); await sleep(300);
      const n3 = sat().length, nb = sat().find(x => x.number === 'SE-0931');
      const flags = nb ? billFlags(nb) : [];
      // the programmatic paths: the inbox, a pay application, the mail reader, a filed invoice all link instead
      const again = vbAdd({ id: uid('b'), vendor: 'SATISH ELECTRIC', number: 'SE0922', date: '2026-09-02', lines: [{ amount: 7400 }], status: 'submitted' });
      return { n0, w1, n1, w2, n2, n3, flags, sameBack: again === B, n4: sat().length };""")
    c.ok(r['n1'] == r['n0'] == 1 and 'Already on file' in r['w1'] and 'SE-0922' in r['w1'], f"bill form: SE-0922 typed again stops before the save ({r['n0']}->{r['n1']}, {r['w1'][:100]!r})")
    c.ok(r['n2'] == 1 and 'Possible duplicate' in r['w2'] and 'Different Invoice' in r['w2'], f"bill form: the same amount within ten days asks first ({r['w2'][:100]!r})")
    c.ok(r['n3'] == 2 and any('duplicate' in f.lower() and 'different invoice' in f for f in r['flags']), f"bill form: said different, it is entered and flagged for Approvals ({r['n3']}, {r['flags']})")
    c.ok(r['sameBack'] and r['n4'] == 2, f"bill form: another path entering SE 0922 gets the bill on file, not a new one ({r['sameBack']}, {r['n4']})")
    c.ok(not errs, f'bill form: no page errors ({errs[:2]})')
    await b.close()


# ------------------------------------------------------------------------------------------------ 3 and 4: Jessop
JESSOP = """
  const cl = DB.clients.find(c => /Jessop/.test(c.name)), inv = cl.invoices.find(i => i.number === 'INV-2026-D140-R');
  const bal = () => r2(docTotal(inv).total - invoicePaid(cl, inv));
"""


async def t_jessop(c, p, phone):
    dev = 'phone' if phone else 'desktop'
    b, pg, errs = await fresh(p, 'u_billing', phone)
    # before the wire is in the bank: Apply records an expectation, never a payment and never a task
    r = await js(pg, JESSOP + """
      await gcDemoConnect(); try { clearInterval(gsTimerId); } catch (e) {}
      const tasks0 = (DB.projects || []).reduce((a, p) => a + (p.actions || []).length, 0) + (DB.tasks || []).length, pays0 = cl.payments.length, bal0 = bal();
      nyhInvalidate();
      const row = nyhRows({ role: 'billing' }).find(r => r.pkind === 'deposit' && /12,000/.test(r.title));
      row.run(); await sleep(300);
      const t = (document.getElementById('toast') || {}).innerText || '';
      const tasks1 = (DB.projects || []).reduce((a, p) => a + (p.actions || []).length, 0) + (DB.tasks || []).length;
      view = 'billing'; billTab = 'payments'; render(); await sleep(300);
      const ex = (document.getElementById('vb-expected') || {}).innerText || '';
      return { t, pays: cl.payments.length - pays0, bal0, bal1: bal(), tasks: tasks1 - tasks0, exp: (DB.expected || []).filter(e => e.clientId === cl.id && !e.txnId).map(e => e.amount), ex, mbm: !!document.getElementById('mbm') };""")
    c.ok(r['pays'] == 0 and r['bal1'] == r['bal0'] == 24000 and not r['mbm'], f"{dev} jessop: with no bank line, Apply records no payment (balance ${r['bal1']})")
    c.ok(r['exp'] == [12000] and r['tasks'] == 0, f"{dev} jessop: it is an expectation of $12,000, not a task ({r['exp']}, tasks +{r['tasks']})")
    c.ok('expected, not cash' in r['t'] and 'Open' in r['t'], f"{dev} jessop: the toast says it is expected, not cash ({r['t']!r})")
    c.ok('Expected, Not in the Bank' in r['ex'] and '$12,000' in r['ex'], f"{dev} jessop: Billing > Payments lists it ({r['ex'][:100]!r})")
    await b.close()
    # the wire is in the feed (the pilot: in since 10:50, unmatched): Apply opens Record Payment on it at $12,000
    b, pg, errs = await fresh(p, 'u_billing', phone)
    r = await js(pg, JESSOP + """
      await gcDemoConnect(); try { clearInterval(gsTimerId); } catch (e) {}
      DB.txns.push({ id: 'tjw1', date: today(), acct: 'ac1', desc: 'WIRE IN JESSOP J', amt: 12000, cat: 'uncat', status: 'new', source: 'import' });
      save(); const cash0 = """ + CASH + """, uncat0 = bankUnmatched().uncat.some(x => x.id === 'tjw1');
      const J0 = new Set(DB.gl.journals.map(j => j.id));
      nyhInvalidate();
      const R = nyhRows({ role: 'billing' }), mailRow = R.find(r => r.pkind === 'deposit'), depRow = R.find(r => r.key === 'dep:tjw1');
      const rows = { mail: !!mailRow, dep: depRow && depRow.why };
      // the pilot's path: the mail's Apply (put the mail row back as it was offered before the bank line)
      const cm = DB.comms.find(x => (x.proposals || []).some(p => p.kind === 'deposit' && p.clientId === cl.id));
      nyhApplyMail(cm, cm.proposals.find(p => p.kind === 'deposit')); await sleep(400);
      const t1 = (document.getElementById('toast') || {}).innerText || '';
      const m = document.getElementById('mbm');
      const form = m && { amt: m.querySelector('#py-amt').value, txn: m.querySelector('#py-txn').value, alloc: [...m.querySelectorAll('[data-pyalloc]')].map(i => +i.value),
        opts: [...m.querySelectorAll('#py-txn option')].map(o => o.value), method: m.querySelector('#py-method').value, sw: document.documentElement.scrollWidth };
      m.querySelector('#mbm-ok').click(); await sleep(400);
      const t2 = (document.getElementById('toast') || {}).innerText || '';
      const t = DB.txns.find(x => x.id === 'tjw1'), U = bankUnmatched(), py = cl.payments.filter(p => p.txnId === 'tjw1');
      const cash1 = """ + CASH + """;
      const L = (a) => r2(DB.gl.journals.filter(j => j.sourceId === 'tjw1' || py.some(p => p.id === j.sourceId)).reduce((s, j) => s + j.lines.filter(l => l.acct === a).reduce((x, l) => x + l.dr - l.cr, 0), 0));
      const newJ = DB.gl.journals.filter(j => !J0.has(j.id));
      view = 'bank'; render(); await sleep(300);
      const made = (document.getElementById('fnd-made') || {}).innerText || '';
      return { rows, t1, form, t2, py: py.map(p => [p.amount, p.invoiceId === inv.id]), bal: bal(), st: inv.status, tcat: t.cat, inUnm: U.rows.some(x => x.id === 'tjw1'), inUncat: U.uncat.some(x => x.id === 'tjw1'), uncat0,
               cash0, cash1, s1090: L('1090'), s1050: L('1050'), s1100: L('1100'), made, exp: (DB.expected || []).filter(e => e.clientId === cl.id).map(e => !!e.txnId) };""")
    f = r['form'] or {}
    c.ok(not r['rows']['mail'] and r['rows']['dep'] and 'said it was sent' in r['rows']['dep'], f"{dev} jessop: once the wire is in, Today has one row for it, the bank line's, saying what the client said ({r['rows']})")
    c.ok('the bank has it' in r['t1'] and f.get('txn') == 'tjw1', f"{dev} jessop: Apply opens Record Payment on the bank line ({r['t1']!r}, {f.get('txn')})")
    c.ok(f.get('amt') == '12000' and f.get('alloc') == [12000] and f.get('method') == 'Wire', f"{dev} jessop: Record Payment takes the bank's $12,000.00, not the invoice's $24,000 ({f})")
    c.ok('' in f.get('opts', []) and 'tjw1' in f.get('opts', []), f"{dev} jessop: the person can pick the bank line, or none ({f.get('opts')})")
    if phone:
        c.ok(f.get('sw', 999) <= 390, f"phone jessop: Record Payment fits 390px ({f.get('sw')})")
    c.ok(r['py'] == [[12000, True]] and r['bal'] == 12000 and r['st'] == 'partial', f"{dev} jessop: $12,000.00 on INV-2026-D140-R, $12,000.00 still open, partial ({r['py']}, {r['bal']}, {r['st']})")
    c.ok(r['uncat0'] and not r['inUnm'] and not r['inUncat'] and r['tcat'] == 'income', f"{dev} jessop: the wire leaves Needs Category and Not Matched once recorded ({r['inUnm']}, {r['inUncat']}, {r['tcat']})")
    c.ok(r['cash1'] == r['cash0'] and r['s1090'] == 0 and r['s1050'] == 0 and r['s1100'] == -12000,
         f"{dev} jessop: cash counts the wire once; suspense and undeposited net $0.00; AR down $12,000.00 ({r['cash0']}->{r['cash1']}, 1090 {r['s1090']}, 1050 {r['s1050']}, 1100 {r['s1100']})")
    c.ok('WIRE IN JESSOP' not in r['made'] and 'Reversal' not in r['made'], f"{dev} jessop: Made Today lists no bank-line posting as a journal someone made ({r['made'][:160]!r})")
    c.ok(r['exp'] and all(r['exp']), f"{dev} jessop: the client's claim is answered by the bank line ({r['exp']})")
    c.ok('matched to the' in r['t2'] and '$12,000 still open' in r['t2'] and 'Open' in r['t2'], f"{dev} jessop: the toast says it was matched and what is left ({r['t2']!r})")
    # a wire is never recorded without its bank line; Banking's card shows a deposit as money in
    r = await js(pg, JESSOP + """
      DB.txns.push({ id: 'tjw2', date: today(), acct: 'ac1', desc: 'WIRE IN JESSOP J', amt: 5000, cat: 'uncat', status: 'new', source: 'import' });
      const n0 = cl.payments.length;
      paymentAllocate(cl, inv.id); await sleep(200);
      const m = document.getElementById('mbm');
      m.querySelector('#py-txn').value = ''; m.querySelector('#py-txn').dispatchEvent(new Event('change'));
      m.querySelector('#py-method').value = 'Wire'; m.querySelector('#py-amt').value = 5000;
      m.querySelector('#mbm-ok').click(); await sleep(200);
      const t = (document.getElementById('toast') || {}).innerText || '', n1 = cl.payments.length;
      try { mbCloseModal(); } catch (e) {}
      const tt = DB.txns.find(x => x.id === 'tjw2'); tt.proposal = { kind: 'invoice', invoiceId: inv.id, m: { invoiceId: inv.id }, why: 'payer name agrees', label: 'Invoice INV-2026-D140-R' };
      signIn('u_controller'); view = 'bank'; render(); await sleep(300);
      const card = [...document.querySelectorAll('.prop-card .prop-row')].map(x => x.innerText).find(x => /JESSOP/.test(x)) || '';
      return { t, n: n1 - n0, card };""")
    c.ok(r['n'] == 0 and 'bank line' in r['t'], f"{dev} jessop: a wire with no bank line is not recorded ({r['n']}, {r['t']!r})")
    c.ok('$5,000 received' in r['card'] and '-$5,000' not in r['card'] and '−$5,000' not in r['card'], f"{dev} jessop: the match card shows a deposit as money in ({r['card'][:120]!r})")
    c.ok(not errs, f'{dev} jessop: no page errors ({errs[:2]})')
    await b.close()


# ------------------------------------------------------------------------------------------------ 5: Tino
async def t_tino(c, p):
    b, pg, errs = await fresh(p, 'u_controller')
    r = await js(pg, """
      const v = DB.vendors.find(x => x.name === 'Tino'); v.email = 'billing@tino-floors.example';
      const mail = (id, day, num, amt) => ({ msgId: id, threadId: id, channel: 'email', from: { name: 'Tino', email: 'billing@tino-floors.example' }, to: ['chen@smartdesign.nyc'], cc: [],
        date: day + 'T14:40:00', subject: `Invoice ${num} for PO-2026-047`, text: `Please find invoice ${num} for PO-2026-047 attached, ${amt}, due net 30.`, attachments: [], source: 'demo', owner: 'u_chen', labels: ['INBOX'] });
      cmImport([mail('p2t1', '2026-09-02', 'TIN-7194', '$8,490.60'), mail('p2t2', '2026-09-03', 'TIN-3277', '$8,650.80')]);
      nyhInvalidate();
      const R = nyhRows({ role: 'controller' }).filter(r => r.pkind === 'bill' && /TIN-/.test(r.title)).map(r => ({ title: r.title, why: r.why, sev: r.sev }));
      const po = DB.pos.find(x => x.number === 'PO-2026-047');
      const doc = renderPODoc(po);
      // entered, both carry the flag into Approvals
      const cms = DB.comms.filter(x => /TIN-(7194|3277)/.test(x.subject));
      cms.forEach(cm => { nyhApplyMail(cm, cm.proposals.find(p => p.kind === 'bill')); const m = document.getElementById('mbm'); m && m.querySelector('#mbm-ok').click(); });
      await sleep(300);
      const B = DB.bills.filter(x => /^TIN-(7194|3277)$/.test(x.number));
      const A = mApprovals({ everyone: true }).filter(a => a.kind === 'bill' && B.some(b => b.id === a.id)).map(a => ({ id: a.id, text: JSON.stringify(a) }));
      return { R, po: { tot: poTotal(po).total }, docNote: (doc.match(/vb-posib[^>]*>([^<]*)/) || [])[1] || '', B: B.map(x => [x.number, billTotal(x), x.poId === po.id]), flags: B.map(x => billFlags(x)), A };""")
    c.ok(len(r['R']) == 2 and all('2 invoices on PO-2026-047' in x['why'] and 'TIN-7194' in x['why'] and 'TIN-3277' in x['why'] for x in r['R']),
         f"tino: each of the two Today rows names the other ({[x['why'][:140] for x in r['R']]})")
    tot = r['po']['tot']; over = round(8490.60 + 8650.80 - tot, 2)
    c.ok(all('$17,141' in x['why'] and f"${tot:,.0f}" in x['why'] and f"${over:,.0f}" in x['why'] for x in r['R']),
         f"tino: $17,141.40 against the ${tot:,.2f} order (with its tax), ${over:,.2f} over ({[x['why'][:200] for x in r['R']]})")
    c.ok('TIN-7194' in r['docNote'] and 'TIN-3277' in r['docNote'], f"tino: the PO says it too ({r['docNote'][:160]!r})")
    c.ok(sorted(x[0] for x in r['B']) == ['TIN-3277', 'TIN-7194'] and all(x[2] for x in r['B']), f"tino: entered after review, both on the PO ({r['B']})")
    c.ok(all(any('2 invoices on PO-2026-047' in f for f in F) for F in r['flags']) and all(any('vs PO' in f for f in F) for F in r['flags']),
         f"tino: in Approvals each bill is flagged with the other and over the PO ({r['flags']})")
    c.ok(len(r['A']) == 2 and all('2 invoices on PO-2026-047' in a['text'] for a in r['A']), f"tino: the Approvals rows carry the flag ({[a['text'][:200] for a in r['A']]})")
    c.ok(not errs, f'tino: no page errors ({errs[:2]})')
    await b.close()


# ------------------------------------------------------------------------------------------------ 6: grid sublines
async def t_sublines(c, p):
    b, pg, errs = await fresh(p, 'u_controller')
    r = await js(pg, """
      const out = [], seen = [];
      for (const v of ['ap', 'bank', 'billing', 'pos']) {
        view = v; render(); await sleep(300);
        document.querySelectorAll('.view.on table.dg-t td').forEach(td => {
          const s = td.querySelector('span.sub'); if (!s) return;
          const before = td.innerText.slice(0, td.innerText.indexOf(s.innerText));
          seen.push(v); before && !/\\s$/.test(before) && out.push(v + ': ' + td.innerText.slice(0, 60));
        });
      }
      view = 'ap'; render(); await sleep(300);
      const pay = [...document.querySelectorAll('.view.on table.dg-t td')].map(td => td.innerText).filter(x => /^Payroll/.test(x));
      return { out, n: seen.length, pay };""")
    c.ok(r['n'] > 5 and not r['out'], f"sublines: every grid subline is its own words ({r['n']} checked; {r['out'][:4]})")
    c.ok(r['pay'] and all(re.search(r'\d employees', x) is None or re.search(r'\s\d+ employees', x) for x in r['pay']), f"sublines: the payroll row reads its period, then its people ({r['pay'][:3]})")
    await b.close()


# ------------------------------------------------------------------------------------------------ 7: billed ahead
async def t_ahead(c, p, phone):
    dev = 'phone' if phone else 'desktop'
    b, pg, errs = await fresh(p, 'u_billing', phone)
    r = await js(pg, """
      const p = DB.projects.find(x => x.id === 'p121'), cl = DB.clients.find(x => x.id === p.clientId);
      // what the grid knows, computed here on its own: billed % and complete % per line, the deposit, the tolerance
      const R = pgRows('p121'), dep = tpCertified(cl, 'p121').depPct, tol = pgCfg().ahead;
      const want = R.filter(r => r.pr && r.pr.pct != null && !r.pr.stale && ['schedule', 'delivered'].includes(r.pr.basis)).map(r => {
        const co = r.sv.source && r.sv.source !== 'Contract', pts = r.ev.billedPct - r.pr.pct, net = pts - (co ? 0 : Math.min(dep, Math.max(0, pts)));
        return { item: r.sv.desc, net, amt: Math.round(r.ev.scheduled * net) / 100 };
      }).filter(x => x.net > tol);
      const A = pbAhead('p121');
      const inv = cl.invoices.find(i => i.number === 'INV-2026-038');
      clientOpen = cl.id; docOpen = { kind: 'invoice', id: inv.id }; view = 'billing'; render(); await sleep(400);
      const v = document.querySelector('.view.on') || document.body;
      const total = (v.querySelector('#pb-ahead-total') || {}).innerText || '', lines = [...v.querySelectorAll('tr.pb-ahead')].map(x => x.innerText);
      const sw = document.documentElement.scrollWidth;
      docOpen = null; clientOpen = null;
      const Q = billingRows().filter(x => x.ahead).map(x => x.why);
      view = 'home'; render(); await sleep(500);
      const home = (document.querySelector('.view.on') || document.body).innerText;
      const catchRows = CATCH.find(k => k.name === 'portalBilledAhead').rows().filter(x => x.key === 'ahead:p121').map(x => [x.what, x.amount]);
      // billing a line further ahead needs a reason; the reason goes on the invoice and the audit
      const tile = R.find(r => /Tile/.test(r.sv.desc));
      const d = { id: 'inv-p2a', type: 'invoice', mode: 'sov', status: 'draft', number: 'INV-2026-P2A', date: today(), projectId: 'p121', title: 'test', retainagePct: 10,
        lines: [{ id: 'lp2a', sovId: tile.sv.id, item: tile.sv.desc, scheduled: tile.ev.scheduled, prevPct: tile.ev.billedPct, pct: 10 }] };
      cl.invoices.push(d);
      await docAction(cl, d, 'send'); await sleep(250);
      const m = document.getElementById('mbm'), ask = m ? m.innerText : '', stillDraft = d.status === 'draft';
      if (m) { const w = m.querySelector('textarea, input[data-f], [data-f="why"]'); w && (w.value = 'The tile is stored in the shop under the contract'); m.querySelector('#mbm-ok').click(); }
      await sleep(300);
      try { mbCloseModal(); } catch (e) {}
      cl.invoices = cl.invoices.filter(x => x.id !== 'inv-p2a');
      return { want, A: { n: A.lines.length, total: A.total, items: A.lines.map(l => l.item), dep: A.depPct }, total, lines, sw, Q, home: /Billed ahead: 121 State/.test(home), homeAmt: home.includes(money(A.total)), catchRows,
               ask, stillDraft, why: d.aheadWhy && d.aheadWhy.why, audit: (DB.audit || []).some(a => a.action === 'billed-ahead' && a.refId === 'inv-p2a') };""")
    want = r['want']
    total = round(sum(x['amt'] for x in want), 2)
    c.ok(r['A']['n'] == len(want) == 7 and abs(r['A']['total'] - total) < 0.005, f"{dev} ahead: 7 lines billed ahead, ${r['A']['total']:,.2f} to the cent, net of the {r['A']['dep']}% deposit ({r['A']['items']}; want {total})")
    c.ok(all(any(k in i for i in r['A']['items']) for k in ['Windows', 'Tile', 'Millwork', 'Trim', 'Exterior', 'General conditions', 'Radiant']),
         f"{dev} ahead: the six lines the schedule puts at 0-20% and CO-2026-001 ({r['A']['items']})")
    c.ok(f"${r['A']['total']:,.0f}" in r['total'] or f"${round(r['A']['total']):,}" in r['total'], f"{dev} ahead: the pay application shows the total ({r['total'][:140]!r})")
    c.ok(len(r['lines']) >= 6 and any('Tile' in x and '51.67% billed' in x for x in r['lines']), f"{dev} ahead: and a line under each line billed ahead ({len(r['lines'])}: {r['lines'][:2]})")
    if phone:
        c.ok(r['sw'] <= 390, f"phone ahead: the pay application fits 390px ({r['sw']})")
    c.ok(r['Q'] and all('billed ahead of the work' in q for q in r['Q']), f"{dev} ahead: the Billing Queue row carries it ({r['Q'][:2]})")
    c.ok(r['catchRows'] and abs(r['catchRows'][0][1] - r['A']['total']) < 0.005 and len(r['catchRows']) == 1, f"{dev} ahead: Today has one row for the job, the same number ({r['catchRows']})")
    c.ok(r['home'] and r['homeAmt'], f"{dev} ahead: billing's Today shows it with the dollar amount ({r['home']}, {r['homeAmt']})")
    c.ok('Billed Ahead of the Work' in r['ask'] and r['stillDraft'], f"{dev} ahead: billing a line further ahead asks why first ({r['ask'][:120]!r})")
    c.ok(r['why'] and r['audit'], f"{dev} ahead: the reason is on the invoice and in the audit ({r['why']!r}, {r['audit']})")
    c.ok(not errs, f'{dev} ahead: no page errors ({errs[:2]})')
    await b.close()
    # the PM's Today has it too
    b, pg, errs = await fresh(p, 'u_alan', phone)
    r = await js(pg, "view = 'home'; render(); await sleep(500); return (document.querySelector('.view.on') || document.body).innerText.includes('Billed ahead: 121 State');")
    c.ok(r, f"{dev} ahead: the PM's Today shows it")
    await b.close()


# ------------------------------------------------------------------------------------------------ the check that fails loudly next time
def t_one_door(c):
    # every bill is added through vbAdd: a new path that pushes onto DB.bills directly fails here
    import os
    allowed = {'src/app.js': 2}   # intercompany bills (glIntercompany) and the QuickBooks bridge import keep their own ids
    found = {}
    import glob
    for f in sorted(os.path.relpath(x, ROOT) for x in glob.glob(os.path.join(ROOT, 'src', '*.js'))):
        s = open(os.path.join(ROOT, f), encoding='utf-8').read()
        n = len(re.findall(r'DB\.bills\.push\(|\(DB\.bills = DB\.bills \|\| \[\]\)\.push\(', s)) - (1 if f == 'src/p2money.js' else 0)
        n and (found.__setitem__(f, n))
    c.ok(found == allowed, f"one door: no path adds a bill without vbAdd ({found}, allowed {allowed})")


async def t_shots(c, p):
    # what each person sees, desktop and phone, for the review (review/p2fix2/, never committed)
    import os
    out = os.path.join(ROOT, 'review', 'p2fix2'); os.makedirs(out, exist_ok=True)
    for phone in (False, True):
        dev = 'phone' if phone else 'desktop'
        b, pg, errs = await fresh(p, 'u_controller', phone)
        await js(pg, "await gcDemoConnect(); try { clearInterval(gsTimerId); } catch (e) {} nyhInvalidate(); nyhRows({ role: 'controller' }).find(r => r.key === 'mail:bill:se-0922').run(); await sleep(400); return 1;")
        await pg.screenshot(path=os.path.join(out, f'enter_the_bill_{dev}.png'))
        await b.close()
        b, pg, errs = await fresh(p, 'u_billing', phone)
        await js(pg, """await gcDemoConnect(); try { clearInterval(gsTimerId); } catch (e) {}
          DB.txns.push({ id: 'tjw1', date: today(), acct: 'ac1', desc: 'WIRE IN JESSOP J', amt: 12000, cat: 'uncat', status: 'new', source: 'import' });
          const cl = DB.clients.find(c => /Jessop/.test(c.name)); paymentAllocate(cl, cl.invoices.find(i => i.number === 'INV-2026-D140-R').id); await sleep(300); return 1;""")
        await pg.screenshot(path=os.path.join(out, f'record_payment_{dev}.png'))
        await js(pg, """mbCloseModal(); const cl = DB.clients.find(c => c.id === DB.projects.find(x => x.id === 'p121').clientId);
          clientOpen = cl.id; docOpen = { kind: 'invoice', id: cl.invoices.find(i => i.number === 'INV-2026-038').id }; view = 'billing'; render(); await sleep(400); window.scrollTo(0, 0); return 1;""")
        await pg.screenshot(path=os.path.join(out, f'billed_ahead_{dev}.png'))
        await b.close()
    c.ok(True, 'screenshots saved under review/p2fix2/')


async def main():
    c = Checks()
    t_one_door(c)
    async with async_playwright() as p:
        for phone in (False, True):
            await t_satish_today_first(c, p, phone)
        await t_satish_bank_first(c, p)
        await t_bill_form(c, p)
        for phone in (False, True):
            await t_jessop(c, p, phone)
        await t_tino(c, p)
        await t_sublines(c, p)
        for phone in (False, True):
            await t_ahead(c, p, phone)
        await t_shots(c, p)
    sys.exit(c.done())


asyncio.run(main())
