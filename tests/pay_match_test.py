"""One bank line backs client payments only up to its amount (lane R, S1 money, found by a billing reviewer 11-12).

The bug, as billing in the demo: open INV-2026-038 (Klein, sent, $68,265 due) and press Record Payment. The sheet came
up on the Aug 29 $72,750 check deposit, the bank line that already stands behind INV-2026-035's payment. One press of
Record "paid" INV-038 $68,265 and invented a $4,485 credit on account: Klein's receivable went to $0 with no new cash,
and INV-035's payment lost its bank line.

The class: every matcher had its own idea of whether a deposit was spoken for. What a line still has to give is one
reading now (payLineUse, beside payBacking in src/app.js), and every path that offers a deposit or writes a payment
against one reads it. Invented data only: the seed and the bank lines each check adds.

1  The scenario, through the screens, desktop and phone: nothing is pre-selected, the used deposits are not offered,
   and the receivable and INV-035's bank line are as they were. Forcing the used line through the sheet, through the
   matcher (truthSetMatch) and through Today's Record Payment row is refused each time.
2  A fresh deposit whose amount and date fit the invoice is pre-selected (the help stays where it is right); one
   dated before the invoice, or for another amount, is offered and not pre-selected.
3  One deposit, two invoices: the first payment takes its part, the line is then offered at what is left of it and
   says so, the second payment takes the rest, both keep their bank line, the ledger counts the cash once, and a
   third payment against it is refused.
4  A reversed payment gives its bank line back: the deposit is offered again and the next payment is in the bank.
5  The same check is not recorded twice: a deposit whose check number is already on a payment typed for the client
   is offered with the reason, never pre-selected, and Record refuses it until that payment is matched or reversed.
6  The other matchers read the same thing: Banking's Match to a Line offers the Aug 29 deposit only the invoice its
   payment is on; In the Bank, Not Applied and Today's Record Payment row show a part-used deposit at what is left
   of it, for the client the rest fits; and a bank debit that already pays one bill in full is not offered, and
   cannot be matched to, a second bill (the money-out twin, apLineUse).
7  A reload does not bring Record Payment back by itself (S3, same sheet): what was typed is kept as a draft and is
   there when the person opens the sheet again, but a money sheet never reopens armed.
8  No bank line anywhere stands behind more client money than it holds, before and after everything above
   (payLinesOver, the list to read on books the old sheet may have written on: it finds what one press left)."""
import asyncio, sys
from harness import *

SLEEP = "ms => new Promise(r => setTimeout(r, ms))"


async def js(pg, body, arg=None):
    return await pg.evaluate("async (arg) => { const sleep = " + SLEEP + "; " + body + " }", arg)


async def fresh(p, uid, phone=False):
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, uid)
    return b, pg, errs


KLEIN = """
  const K = DB.clients.find(c => (c.invoices || []).some(i => i.number === 'INV-2026-038'));
  const i38 = K.invoices.find(i => i.number === 'INV-2026-038'), i35 = K.invoices.find(i => i.number === 'INV-2026-035');
  const py35 = K.payments.find(p => p.invoiceId === i35.id), t2 = DB.txns.find(t => t.id === 't2');
  const J = DB.clients.find(c => /Jessop/.test(c.name)), iJ = J.invoices.find(i => i.number === 'INV-2026-D140-R');
  const ar = (c) => r2((clientFin(c).open || []).reduce((a, o) => a + o.bal, 0));
  const lineOf = (py) => (payBankLine(py) || {}).id || '';
  const snap = () => ({ ar: ar(K), n: K.payments.length, back35: lineOf(py35), banked35: payBankedAmt(K, py35), st38: invoiceStatus(K, i38), st35: invoiceStatus(K, i35),
    credit: r2(K.payments.filter(p => p.unapplied).reduce((a, p) => a + (+p.amount || 0), 0)), t2: JSON.stringify(t2.match || null) + '|' + (t2.invoiceId || '') });
  // the person's way in: Billing, the invoice, its Record Payment button
  const openPay = async (c, inv) => {
    try { mbCloseModal(); } catch (e) {}
    view = 'billing'; clientOpen = c.id; docOpen = { kind: 'invoice', id: inv.id }; render(); await sleep(450);
    const b = [...document.querySelectorAll('[data-docact="pay"]')].find(x => x.offsetParent) || document.querySelector('[data-docact="pay"]');
    const seen = !!(b && b.offsetParent);
    b && b.click(); await sleep(400);
    return seen;
  };
  const sheet = () => { const m = document.getElementById('mbm'); if (!m || !m.querySelector('#py-amt')) return null;
    const s = m.querySelector('#py-txn');
    return { txn: s ? s.value : null, opts: s ? [...s.options].map(o => o.value) : [], text: s ? [...s.options].map(o => o.text) : [], amt: +m.querySelector('#py-amt').value,
      alloc: [...m.querySelectorAll('[data-pyalloc]')].map(i => +i.value), note: (m.querySelector('#py-txn-note') || {}).innerText || '', sw: document.documentElement.scrollWidth,
      wide: [...m.querySelectorAll('select, input, button')].filter(x => x.offsetParent && x.getBoundingClientRect().right > innerWidth + 1).length }; };
  const Q = (q) => { const m = document.getElementById('mbm'); return m ? m.querySelector(q) : null; };
  const pick = (id) => { const s = Q('#py-txn'); if (!s) return; s.value = id; s.dispatchEvent(new Event('change', { bubbles: true })); };
  const setv = (q, v) => { const el = Q(q); if (!el) return; el.value = v; el.dispatchEvent(new Event('input', { bubbles: true })); };
  const how = (method, ref) => { const a = Q('#py-method'), b = Q('#py-ref'); a && (a.value = method); b && (b.value = ref); };
  const press = async () => { const ok = Q('#mbm-ok'); ok && ok.click(); await sleep(450); return (document.getElementById('toast') || {}).innerText || ''; };
  const dep = (id, amt, desc, date) => { DB.txns.push(txnStamp({ id: id, date: date || today(), acct: 'ac1', desc: desc, amt: amt, cat: 'uncat', status: 'new', source: 'ofx' }, 'stmt:paymatch', id)); save(); return DB.txns.find(t => t.id === id); };
  // what of a bank line stands behind client payments (src/app.js, beside payBacking); a build without it fails each check that reads it
  const use = (t) => 'function' == typeof payLineUse ? payLineUse(t) : { amt: +t.amt, used: -1, left: -1, pays: [] };
  // no bank line stands behind more client money than it holds
  const over = () => 'function' != typeof payLinesOver ? ['payLinesOver is missing'] : payLinesOver().map(x => x.id + ' ' + x.behind + '>' + x.amount + (x.pushedOut ? ' pushed out ' + x.pushedOut : ''));
"""


# ------------------------------------------------------------------------------------------ 1: the reviewer's steps
async def t_scenario(c, p, phone):
    dev = 'phone' if phone else 'desktop'
    b, pg, errs = await fresh(p, 'u_billing', phone)
    r = await js(pg, KLEIN + """
      const s0 = snap(), over0 = over();
      const seen = await openPay(K, i38);
      const f = sheet();
      try { mbCloseModal(); } catch (e) {}
      const s1 = snap();
      return { s0, s1, f, seen, over0, use2: use(t2), who: (use(t2).pays || []).map(x => x.p.id) };""")
    f = r['f'] or {}
    s0 = r['s0']
    c.ok(s0['ar'] == 68265 and s0['back35'] == 't2' and s0['banked35'] == 72750, f"{dev} seed: Klein owes $68,265 on INV-2026-038 and the Aug 29 deposit stands behind INV-2026-035 ({s0})")
    c.ok(r['over0'] == [], f"{dev} seed: no bank line backs more than it holds ({r['over0']})")
    c.ok(r['use2']['left'] == 0 and r['use2']['used'] == 72750, f"{dev} the Aug 29 $72,750 deposit has nothing left to give ({r['use2'].get('used')}, {r['use2'].get('left')}, {r['who']})")
    c.ok(r['seen'] and r['f'] is not None, f"{dev} Record Payment opens from the invoice ({r['seen']})")
    c.ok(f.get('txn') == '', f"{dev} Record Payment pre-selects no bank line for INV-2026-038 ({f.get('txn')!r})")
    c.ok('t2' not in f.get('opts', ['t2']) and 't1' not in f.get('opts', ['t1']), f"{dev} the deposits that already back INV-2026-035 and INV-2026-031 are not offered ({f.get('opts')})")
    c.ok(f.get('amt') == 68265 and f.get('alloc') == [68265], f"{dev} the sheet shows what the invoice is owed, not a bank amount ({f.get('amt')}, {f.get('alloc')})")
    c.ok(r['s1'] == s0, f"{dev} opening and closing the sheet changes nothing ({r['s1']})")
    if phone:
        c.ok(f.get('sw', 999) <= 390 and f.get('wide') == 0, f"phone: Record Payment fits 390px ({f.get('sw')}, {f.get('wide')} controls past the edge)")
    # the used line forced through the sheet (a stale sheet, another tab): the writer refuses, not only the picker
    r = await js(pg, KLEIN + """
      const s0 = snap();
      await openPay(K, i38);
      const m = document.getElementById('mbm'), s = m.querySelector('#py-txn');
      const o = document.createElement('option'); o.value = 't2'; o.text = 'forced'; s.appendChild(o);
      pick('t2');
      const filled = sheet();
      m.querySelector('#py-method').value = 'Check'; m.querySelector('#py-ref').value = '2214'; m.querySelector('#py-acct').value = 'ac1';
      setv('#py-amt', 68265); setv('[data-pyalloc]', 68265);
      const toast1 = await press();
      const open = !!document.getElementById('mbm');
      try { mbCloseModal(); } catch (e) {}
      const s1 = snap();
      // the matcher itself (Banking's match, Today's Record Payment row, Find in Bank all write through it)
      const m2 = truthSetMatch(t2, { invoiceId: i38.id }, { why: 'forced' });
      const s2 = snap();
      nyhRecordDeposit({ t: t2, c: K, inv: i38 }); await sleep(250);
      const s3 = snap();
      nyhRecordDeposit({ t: t2, c: K, inv: null }); await sleep(250);
      const s4 = snap();
      try { mbCloseModal(); } catch (e) {}
      // Find in Bank on the invoice: nothing is recorded, and the used deposit is not put forward
      view = 'billing'; clientOpen = K.id; docOpen = { kind: 'invoice', id: i38.id }; render(); await sleep(400);
      const fb = [...document.querySelectorAll('[data-docact="findbank"]')].find(x => x.offsetParent) || document.querySelector('[data-docact="findbank"]');
      fb && fb.click(); await sleep(450);
      const toast2 = (document.getElementById('toast') || {}).innerText || '', verify = document.body.innerText.includes('DEPOSIT CHECK 2214 KLEIN') && !!document.querySelector('#mbm, .drawer.on, #drawer.on');
      try { mbCloseModal(); } catch (e) {}
      const s5 = snap();
      return { s0, s1, s2, s3, s4, s5, filled, toast1, open, m2: m2 && { ok: m2.ok, why: m2.why || '' }, toast2, verify, fb: !!fb, over: over() };""")
    s0 = r['s0']
    c.ok(r['s1'] == s0, f"{dev} guard: the used deposit forced through the sheet records nothing (before {s0}, after {r['s1']})")
    c.ok('INV-2026-035' in r['toast1'] and 'recorded from' not in r['toast1'], f"{dev} guard: the sheet says the line already stands behind INV-2026-035 ({r['toast1']!r})")
    c.ok(r['m2'] and r['m2']['ok'] is False and 'INV-2026-035' in r['m2']['why'] and r['s2'] == s0, f"{dev} guard: the matcher refuses the used deposit for INV-2026-038 and says why ({r['m2']}, {r['s2']})")
    c.ok(r['s3'] == s0 and r['s4'] == s0, f"{dev} guard: Today's Record Payment row cannot record the used deposit, on the invoice or on account ({r['s3']}, {r['s4']})")
    c.ok(r['fb'] and r['s5'] == s0 and 'No deposit' in r['toast2'] and not r['verify'], f"{dev} Find in Bank finds no deposit for INV-2026-038 and records nothing ({r['toast2']!r}, {r['s5']})")
    c.ok(r['over'] == [], f"{dev} after every forced attempt no bank line backs more than it holds ({r['over']})")
    c.ok(not errs, f'{dev} scenario: no page errors ({errs[:2]})')
    await b.close()


# ------------------------------------------------------------------------------------------ 2: when it does pre-select
async def t_preselect(c, p, phone):
    dev = 'phone' if phone else 'desktop'
    b, pg, errs = await fresh(p, 'u_billing', phone)
    r = await js(pg, KLEIN + """
      // dated before the invoice went out, and for another amount: offered (it names the client), never pre-selected
      dep('tpmA', 68265, 'DEPOSIT CHECK 2290 KLEIN', iso(addDays(i38.date, -6)));
      dep('tpmB', 50000, 'DEPOSIT CHECK 2291 KLEIN');
      await openPay(K, i38);
      const f1 = sheet();
      // the invoice's own money: the amount it is owed, dated after it went out, on no payment
      dep('tpmC', 68265, 'DEPOSIT CHECK 2301 KLEIN');
      await openPay(K, i38);
      const f2 = sheet(), s0 = snap();
      const m = document.getElementById('mbm');
      const meth = m.querySelector('#py-method').value, ref = m.querySelector('#py-ref').value;
      const toast = await press();
      const py = K.payments.filter(x => x.txnId === 'tpmC');
      return { f1, f2, meth, ref, toast, py: py.map(x => [x.amount, x.invoiceId === i38.id, !!x.unapplied]), s1: snap(), back: py.map(x => [lineOf(x), payBankedAmt(K, x)]), use: use(DB.txns.find(t => t.id === 'tpmC')).left, date: i38.date, over: over() };""")
    f1, f2 = r['f1'] or {}, r['f2'] or {}
    c.ok(f1.get('txn') == '' and 'tpmA' in f1.get('opts', []) and 'tpmB' in f1.get('opts', []), f"{dev} a deposit dated before the invoice ({r['date']}) or for another amount is offered and not pre-selected ({f1.get('txn')!r}, {f1.get('opts')})")
    c.ok(f2.get('txn') == 'tpmC' and f2.get('amt') == 68265 and f2.get('alloc') == [68265], f"{dev} a free deposit for the invoice's amount, dated after it, is pre-selected at the bank's amount ({f2.get('txn')!r}, {f2.get('amt')})")
    c.ok(r['meth'] == 'Check' and r['ref'] == '2301', f"{dev} the bank line fills the method and the check number ({r['meth']}, {r['ref']})")
    c.ok(r['py'] == [[68265, True, False]] and r['s1']['ar'] == 0 and r['s1']['credit'] == 0 and r['s1']['st38'] == 'paid', f"{dev} Record pays INV-2026-038 from its own deposit, with no credit on account ({r['py']}, {r['s1']})")
    c.ok(r['back'] == [['tpmC', 68265]] and r['s1']['back35'] == 't2' and r['s1']['banked35'] == 72750 and r['use'] == 0, f"{dev} both payments are in the bank, each on its own line ({r['back']}, INV-035 on {r['s1']['back35']})")
    c.ok('matched to the' in r['toast'] and 'Open' in r['toast'] and r['over'] == [], f"{dev} the toast says what was matched, with Open ({r['toast']!r})")
    if phone:
        c.ok(f2.get('sw', 999) <= 390 and f2.get('wide') == 0, f"phone: Record Payment with its bank line fits 390px ({f2.get('sw')}, {f2.get('wide')})")
    c.ok(not errs, f'{dev} preselect: no page errors ({errs[:2]})')
    await b.close()


# ------------------------------------------------------------------------------------------ 3: one deposit, two invoices
CASH = "(() => { glSync(); return r2((DB.gl.journals || []).reduce((a, j) => a + (j.lines || []).filter(l => l.acct === 'acct:ac1').reduce((s, l) => s + (+l.dr || 0) - (+l.cr || 0), 0), 0)); })()"


async def t_split(c, p, phone):
    dev = 'phone' if phone else 'desktop'
    b, pg, errs = await fresh(p, 'u_billing', phone)
    r = await js(pg, KLEIN + """
      // one deposit slip, two clients' checks: $68,265 from the Kleins and $24,000 from the Jessops
      const t = dep('tpmS', 92265, 'DEPOSIT CHECKS KLEIN 2302 JESSOP 884');
      const cash0 = """ + CASH + """, arJ0 = ar(J);
      await openPay(K, i38);
      const f1 = sheet();
      pick('tpmS');
      const f1b = sheet();
      // the Kleins' check is $68,265 of it
      setv('#py-amt', 68265); setv('[data-pyalloc]', 68265); how('Check', '2302');
      const toast1 = await press();
      const pA = K.payments.find(x => x.txnId === 'tpmS');
      const use1 = use(t), sK = snap(), matchA = truthMatchOf(t).invoiceId;
      // between the two payments: $24,000 of the deposit is on no invoice, and every list that shows deposits says so
      nyhInvalidate();
      const todayRow = nyhRows({ role: 'billing' }).find(x => x.key === 'dep:tpmS') || {};
      view = 'billing'; clientOpen = null; docOpen = null; billTab = 'payments'; render(); await sleep(350);
      const inBank = (document.getElementById('pay-inbank') || {}).innerText || '';
      const matchSheet = truthCandidates(t).map(x => x.label);
      // the Jessops' sheet: the same line, at what is left of it
      await openPay(J, iJ);
      const f2 = sheet();
      const row = (f2 ? f2.text : [])[f2 ? f2.opts.indexOf('tpmS') : -1] || '';
      pick('tpmS');
      const f2b = sheet();
      // more than is left of it is refused
      setv('#py-amt', 30000); how('Check', '884');
      const nJ = J.payments.length, toastOver = await press(), refused = J.payments.length === nJ;
      if (!sheet()) { await openPay(J, iJ); pick('tpmS'); }
      setv('#py-amt', 24000); setv('[data-pyalloc]', 24000); how('Check', '884');
      const toast2 = await press();
      const pB = J.payments.find(x => x.txnId === 'tpmS');
      const use2 = use(t), cash1 = """ + CASH + """;
      const ids = [t.id, pA && pA.id, pB && pB.id];
      const L = (a) => r2(DB.gl.journals.filter(j => ids.includes(j.sourceId)).reduce((s, j) => s + j.lines.filter(l => l.acct === a).reduce((x, l) => x + l.dr - l.cr, 0), 0));
      const out = { f1, f1b, toast1, use1: [use1.used, use1.left], sK, matchA: matchA === i38.id, f2, row, f2b, toastOver, refused, toast2, todayRow: [todayRow.title || '', todayRow.why || '', todayRow.amount || 0], inBank, matchSheet,
        words: truthMatchWords(truthMatchOf(t)),
        pA: pA && [pA.amount, pA.invoiceId === i38.id, lineOf(pA), payBankedAmt(K, pA)], pB: pB && [pB.amount, pB.invoiceId === iJ.id, lineOf(pB), payBankedAmt(J, pB)],
        use2: [use2.used, use2.left], who: use2.pays.length, matchB: truthMatchOf(t).invoiceId === i38.id, arK: ar(K), arJ: ar(J), arJ0, stJ: invoiceStatus(J, iJ), creditK: sK.credit, creditJ: r2(J.payments.filter(x => x.unapplied).reduce((a, x) => a + (+x.amount || 0), 0)),
        cash0, cash1, s1100: L('1100'), s1090: L('1090'), s1050: L('1050'), unm: bankUnmatched().rows.some(x => x.id === 'tpmS') || bankUnmatched().uncat.some(x => x.id === 'tpmS') };
      // a third payment against it: not offered, and refused by the matcher
      await openPay(K, i38); const f3k = sheet(); try { mbCloseModal(); } catch (e) {}
      await openPay(J, iJ); const f3 = sheet(); try { mbCloseModal(); } catch (e) {}
      const s0 = snap(), nJ2 = J.payments.length;
      const m3 = truthSetMatch(t, { invoiceId: iJ.id }, { why: 'forced' });
      out.third = { offered: !!((f3 && f3.opts.includes('tpmS')) || (f3k && f3k.opts.includes('tpmS'))), m3: m3 && { ok: m3.ok, why: m3.why || '' }, same: JSON.stringify(snap()) === JSON.stringify(s0) && J.payments.length === nJ2 };
      out.over = over(); out.back35 = snap().back35;
      return out;""")
    f1, f1b, f2, f2b = r['f1'] or {}, r['f1b'] or {}, r['f2'] or {}, r['f2b'] or {}
    c.ok('tpmS' in f1.get('opts', []) and f1.get('txn') == '', f"{dev} split: a deposit larger than the invoice is offered, not pre-selected ({f1.get('txn')!r}, {f1.get('opts')})")
    c.ok(f1b.get('amt') == 92265 and f1b.get('alloc') == [68265], f"{dev} split: picked, it shows the bank's $92,265 with $68,265 on the invoice ({f1b.get('amt')}, {f1b.get('alloc')})")
    c.ok(r['pA'] == [68265, True, 'tpmS', 68265] and r['use1'] == [68265, 24000] and r['sK']['credit'] == 0 and r['sK']['ar'] == 0, f"{dev} split: the Kleins' $68,265 is recorded from the line, $24,000 of it left, no credit invented ({r['pA']}, {r['use1']}, {r['sK']})")
    c.ok('$24,000' in r['toast1'] and 'on no invoice yet' in r['toast1'], f"{dev} split: the toast says $24,000 of the deposit is on no invoice yet ({r['toast1']!r})")
    c.ok('$24,000 left of $92,265' in r['inBank'], f"{dev} split: In the Bank, Not Applied lists the deposit at the $24,000 left of it ({r['inBank'][:200]!r})")
    c.ok('Jessop' in r['todayRow'][0] and '$24,000' in r['todayRow'][0] and 'INV-2026-D140-R' in r['todayRow'][0] and r['todayRow'][2] == 24000 and 'left of' in r['todayRow'][1],
         f"{dev} split: Today's Record Payment row is the Jessops' $24,000 against their invoice, and says it is what is left ({r['todayRow']})")
    c.ok(any('INV-2026-D140-R' in x and '$24,000 left' in x for x in r['matchSheet']) and not any('INV-2026-038' in x for x in r['matchSheet']), f"{dev} split: Banking's Match offers the deposit for what is left of it ({r['matchSheet']})")
    c.ok('tpmS' in f2.get('opts', []) and f2.get('txn') == '', f"{dev} split: the part-used deposit is offered to the Jessops, never pre-selected ({f2.get('txn')!r}, {f2.get('opts')})")
    c.ok('$24,000 left of $92,265' in r['row'], f"{dev} split: its row says what is left of it ({r['row']!r})")
    c.ok(f2b.get('amt') == 24000 and f2b.get('alloc') == [24000] and '$24,000' in f2b.get('note', '') and 'INV-2026-038' in f2b.get('note', ''), f"{dev} split: picked, it fills the $24,000 left and says the rest is on INV-2026-038 ({f2b.get('amt')}, {f2b.get('note')!r})")
    c.ok(r['refused'] and '$24,000' in r['toastOver'], f"{dev} split: $30,000 against the $24,000 left is refused ({r['toastOver']!r})")
    c.ok(r['pB'] == [24000, True, 'tpmS', 24000] and r['use2'] == [92265, 0] and r['who'] == 2, f"{dev} split: the Jessops' $24,000 is recorded from the same line, now used in full by two payments ({r['pB']}, {r['use2']}, {r['who']})")
    c.ok(r['pA'] == [68265, True, 'tpmS', 68265] and r['matchA'] and r['matchB'] and r['back35'] == 't2', f"{dev} split: the first payment keeps its bank line when the second is recorded ({r['pA']}, match kept {r['matchB']})")
    c.ok(r['arK'] == 0 and r['arJ'] == r2(r['arJ0'] - 24000) and r['stJ'] == 'paid' and r['creditJ'] == 0, f"{dev} split: both invoices are paid, no credit on account ({r['arK']}, {r['arJ0']}->{r['arJ']}, {r['stJ']})")
    c.ok(r['cash1'] == r['cash0'] and r['s1100'] == -92265 and r['s1090'] == 0 and r['s1050'] == 0, f"{dev} split: the ledger counts the $92,265 once; receivables down $92,265; suspense and undeposited $0 ({r['cash0']}->{r['cash1']}, 1100 {r['s1100']}, 1090 {r['s1090']}, 1050 {r['s1050']})")
    c.ok(not r['unm'], f"{dev} split: the deposit leaves Needs Category and Not Matched")
    c.ok('INV-2026-038' in r['words'] and 'INV-2026-D140-R' in r['words'], f"{dev} split: the bank line names both invoices it stands behind ({r['words']!r})")
    c.ok('still open' not in r['toast2'] and 'INV-2026-D140-R' in r['toast2'] and '$24,000' in r['toast2'] and 'Open' in r['toast2'], f"{dev} split: the toast says $24,000 on the Jessops' invoice, with Open ({r['toast2']!r})")
    t3 = r['third']
    c.ok(not t3['offered'] and t3['m3'] and t3['m3']['ok'] is False and t3['same'], f"{dev} split: used in full, the deposit is not offered again and the matcher refuses a third payment ({t3})")
    c.ok(r['over'] == [], f"{dev} split: no bank line backs more than it holds ({r['over']})")
    c.ok(not errs, f'{dev} split: no page errors ({errs[:2]})')
    await b.close()


def r2(x):
    return round(x + 0.0, 2)


# ------------------------------------------------------------------------------------------ 4: a reversal frees the line
async def t_reversal(c, p):
    b, pg, errs = await fresh(p, 'u_billing')
    r = await js(pg, KLEIN + """
      const t = dep('tpmR', 24000, 'DEPOSIT CHECK 885 JESSOP');
      await openPay(J, iJ);
      const f1 = sheet();
      await press();
      const p1 = J.payments.find(x => x.txnId === 'tpmR');
      const rv = payReverse(J, p1, 'recorded twice by mistake; recording it again');
      render(); await sleep(200);
      const use1 = use(t), ar1 = ar(J);
      await openPay(J, iJ);
      const f2 = sheet();
      pick('tpmR');
      await press();
      const p2 = J.payments.find(x => x.txnId === 'tpmR' && x.id !== p1.id && !x.reverses);
      return { f1: f1 && f1.txn, rv: rv && rv.ok, use1: [use1.used, use1.left], ar1, f2: f2 && f2.opts, p2: p2 && [p2.amount, lineOf(p2), payBankedAmt(J, p2)], ar2: ar(J), banked: paysBanked(J, J.payments.filter(x => x.invoiceId === iJ.id)), unb: invoiceUnbanked(J, iJ), over: over() };""")
    c.ok(r['f1'] == 'tpmR' and r['rv'], f"reversal: the Jessops' $24,000 deposit is recorded, then reversed ({r['f1']}, {r['rv']})")
    c.ok(r['use1'] == [0, 24000] and r['ar1'] == 24000, f"reversal: the reversed payment gives the bank line back and the invoice is open again ({r['use1']}, {r['ar1']})")
    c.ok('tpmR' in (r['f2'] or []), f"reversal: the deposit is offered again ({r['f2']})")
    c.ok(r['p2'] == [24000, 'tpmR', 24000] and r['ar2'] == 0 and r['banked'] == 24000 and r['unb'] == 0, f"reversal: recorded again, the payment is in the bank and the invoice counts $24,000 once ({r['p2']}, banked {r['banked']}, not in bank {r['unb']})")
    c.ok(r['over'] == [] and not errs, f"reversal: no line over its amount, no page errors ({r['over']}, {errs[:2]})")
    await b.close()


# ------------------------------------------------------------------------------------------ 5: the same check, once
async def t_check_twice(c, p):
    b, pg, errs = await fresh(p, 'u_billing')
    r = await js(pg, KLEIN + """
      // billing typed the Jessops' check 890 as $23,000 with no bank line (a check in hand)
      await openPay(J, iJ);
      setv('#py-amt', 23000); setv('[data-pyalloc]', 23000); how('Check', '890'); Q('#py-acct').value = 'ac1';
      await press();
      const typed = J.payments.find(x => x.ref === '890');
      // the bank shows the deposit at $24,000: the same check, mistyped. It is not the invoice's last $1,000.
      const t = dep('tpmK', 24000, 'DEPOSIT CHECK 890 JESSOP');
      await openPay(J, iJ);
      const f = sheet();
      pick('tpmK');
      const f2 = sheet(), n0 = J.payments.length, toast = await press(), n1 = J.payments.length;
      try { mbCloseModal(); } catch (e) {}
      return { typed: typed && [typed.amount, typed.txnId || ''], f, note: f2 && f2.note, toast, same: n0 === n1, ar: ar(J), use: use(t).left, over: over() };""")
    f = r['f'] or {}
    c.ok(r['typed'] == [23000, ''], f"check twice: check 890 is typed as $23,000, not yet in the bank ({r['typed']})")
    c.ok('tpmK' in f.get('opts', []) and f.get('txn') == '', f"check twice: the bank's deposit of check 890 is offered, not pre-selected ({f.get('txn')!r}, {f.get('opts')})")
    c.ok('check number is already on' in (r['note'] or '') and '$23,000' in (r['note'] or ''), f"check twice: picked, the sheet says the check is already on the $23,000 payment ({r['note']!r})")
    c.ok(r['same'] and 'not recorded again' in r['toast'] and r['ar'] == 1000 and r['use'] == 24000, f"check twice: Record refuses to record the check a second time ({r['toast']!r}, owed {r['ar']})")
    c.ok(r['over'] == [] and not errs, f"check twice: no line over its amount, no page errors ({r['over']}, {errs[:2]})")
    await b.close()


# ------------------------------------------------------------------------------------------ 6: the other matchers
async def t_other_matchers(c, p):
    b, pg, errs = await fresh(p, 'u_controller')
    r = await js(pg, KLEIN + """
      const s0 = snap();
      // Banking's Match to a Line, on the Aug 29 deposit
      const cands = truthCandidates(t2).map(x => [x.label, (x.m || {}).paymentId || '']);
      // matching it to the invoice its payment is on writes the link the seed never had, and moves no money
      const own = truthSetMatch(t2, cands[0] ? { invoiceId: i35.id, paymentId: cands[0][1] } : { invoiceId: i35.id }, { why: 'the payment it is' });
      const s1 = snap();
      // money out: the Nemo Tile ACH already pays NT-88412 in full
      const t3 = DB.txns.find(t => +t.amt < 0 && (t.billId || (t.match || {}).billId));
      const A = DB.bills.find(x => x.id === (t3.billId || t3.match.billId));
      const B = DB.bills.find(x => x.id !== A.id && !['void', 'rejected'].includes(x.status) && !x.txnId && !x.ic);
      const before = JSON.stringify([A.txnId, A.status, B.txnId || '', B.status, t3.billId, (DB.payments || []).filter(x => !x.void).length]);
      const ap = truthSetMatch(t3, { billId: B.id }, { why: 'forced', earlyWhy: 'forced' });
      const after = JSON.stringify([A.txnId, A.status, B.txnId || '', B.status, t3.billId, (DB.payments || []).filter(x => !x.void).length]);
      // a second bill from the same vendor is the one the old list would put forward: it is not offered
      const twin = Object.assign(JSON.parse(JSON.stringify(A)), { id: 'b_pm_twin', number: 'NT-PM-TWIN', txnId: '', status: 'approved', paidAt: '' });
      (twin.lines || []).forEach((l, i) => (l.id = 'bl_pm_' + i)); DB.bills.push(twin);
      const offered = truthCandidates(t3).map(x => x.label);
      const ap2 = truthSetMatch(t3, { billId: twin.id }, { why: 'forced', earlyWhy: 'forced' });
      return { s0, s1, cands, own: own && own.ok, link: py35.txnId || '', ap: ap && { ok: ap.ok, why: ap.why || '' }, same: before === after, A: A.number, B: B.number,
        offered, ap2: ap2 && ap2.ok, twinTxn: twin.txnId || '', use: apLineUse(t3), over: over() };""")
    c.ok(len(r['cands']) == 1 and 'INV-2026-035' in r['cands'][0][0] and r['cands'][0][1], f"matchers: Banking's Match offers the Aug 29 deposit only INV-2026-035, the invoice its payment is on ({r['cands']})")
    s0, s1 = r['s0'], r['s1']
    c.ok(r['own'] and r['link'] == 't2' and s1['ar'] == s0['ar'] and s1['n'] == s0['n'] and s1['back35'] == 't2' and s1['banked35'] == 72750 and s1['credit'] == 0,
         f"matchers: matching it there links the payment to its line and moves no money ({r['own']}, {r['link']}, {s1})")
    c.ok(r['ap'] and r['ap']['ok'] is False and r['A'] in r['ap']['why'] and r['same'], f"matchers: the ACH that pays {r['A']} in full cannot be matched to {r['B']} ({r['ap']})")
    c.ok(not any('NT-PM-TWIN' in x for x in r['offered']) and r['ap2'] is False and r['twinTxn'] == '', f"matchers: it is not offered a second bill from the same vendor, and the match is refused ({r['offered']}, {r['ap2']})")
    c.ok(r['use']['left'] == 0 and len(r['use']['held']) == 1, f"matchers: the debit pays one bill and has nothing left ({r['use']['used']}, {r['use']['left']})")
    c.ok(r['over'] == [] and not errs, f"matchers: no line over its amount, no page errors ({r['over']}, {errs[:2]})")
    await b.close()


# ------------------------------------------------------------------------------------------ the books the hole touched
async def t_damage(c, p):
    b, pg, errs = await fresh(p, 'u_billing')
    r = await js(pg, KLEIN + """
      const clean = payLinesOver();
      // what one press of Record wrote before the fix: $68,265 on INV-038 and a $4,485 credit, both on the Aug 29 line
      K.payments.push({ id: 'py_dmg1', invoiceId: i38.id, date: '2026-08-29', amount: 68265, method: 'Check', ref: '2214', acctId: 'ac1', txnId: 't2' });
      K.payments.push({ id: 'py_dmg2', invoiceId: '', date: '2026-08-29', amount: 4485, unapplied: true, method: 'Check', ref: '2214', acctId: 'ac1', txnId: 't2' });
      const found = payLinesOver();
      return { clean: clean.length, found: found.map(x => [x.id, x.pushedOut]), back35: lineOf(py35) };""")
    c.ok(r['clean'] == 0, f"damage: the demo books hold no over-used deposit ({r['clean']})")
    c.ok(len(r['found']) == 1 and r['found'][0][0] == 't2' and 'INV-2026-035' in r['found'][0][1] and r['back35'] == '', f"damage: books the old sheet wrote on are found, with the payment it pushed out ({r['found']})")
    c.ok(not errs, f'damage: no page errors ({errs[:2]})')
    await b.close()


# ------------------------------------------------------------------------------------------ 7: a reload
async def t_reload(c, p, phone):
    dev = 'phone' if phone else 'desktop'
    b, pg, errs = await fresh(p, 'u_billing', phone)
    await js(pg, KLEIN + "dep('tpmC', 68265, 'DEPOSIT CHECK 2301 KLEIN'); await saveNow(); await openPay(K, i38); return 1;")
    await pg.fill('#mbm #py-ref', '2301 typed before the reload')
    await pg.wait_for_timeout(600)
    r0 = await js(pg, KLEIN + "await saveNow(); return { n: K.payments.length, drafts: w1Drafts().filter(d => /record payment/i.test(d.title || '')).map(d => [d.open, !!d.money]), armed: (sheet() || {}).txn };")
    await pg.reload()
    await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
    await sign_in(pg, 'u_billing')
    r = await js(pg, KLEIN + """
      // the person is put back where they were: Billing, the invoice
      view = 'billing'; clientOpen = K.id; docOpen = { kind: 'invoice', id: i38.id }; render(); await sleep(1200);
      const back = !!sheet(), n = K.payments.length, line = !!DB.txns.find(t => t.id === 'tpmC');
      // they open it again themselves: what they typed is there
      await openPay(K, i38); await sleep(400);
      const ref = (Q('#py-ref') || {}).value || '', dr = !!document.querySelector('#mbm .w1-dr');
      try { mbCloseModal(); } catch (e) {}
      return { back, n, line, ref, dr };""")
    c.ok(r0['drafts'] == [[True, True]] and r0['armed'] == 'tpmC', f"{dev} reload: the typed reference is kept as a draft of a money sheet, the sheet open on its deposit ({r0})")
    c.ok(r['line'] and not r['back'] and r['n'] == r0['n'], f"{dev} reload: Record Payment does not come back by itself, and nothing is recorded ({r})")
    c.ok('2301 typed before the reload' in r['ref'], f"{dev} reload: opened again by the person, what they typed is there ({r['ref']!r})")
    c.ok(not errs, f'{dev} reload: no page errors ({errs[:2]})')
    await b.close()


async def main():
    # python3 pay_match_test.py [name ...]: only the checks named (scenario, preselect, split, reversal, check, matchers, damage, reload)
    only = [a for a in sys.argv[1:] if not a.startswith('-')]
    want = lambda name: not only or name in only
    c = Checks()
    async with async_playwright() as p:
        for name, fn, both in (('scenario', t_scenario, True), ('preselect', t_preselect, True), ('split', t_split, True), ('reversal', t_reversal, False),
                               ('check', t_check_twice, False), ('matchers', t_other_matchers, False), ('damage', t_damage, False), ('reload', t_reload, True)):
            if not want(name): continue
            if both:
                for phone in (False, True):
                    await fn(c, p, phone)
            else:
                await fn(c, p)
    sys.exit(c.done())


asyncio.run(main())
