"""The three-day pilot's batch-2 findings (lane pilotfix2), each reproduced as the person hit it, on the phone where
the person is on the phone, then held. Invented data only: the seed plus the records each check adds.

1  Hours. A clock-in is stamped at the app's own time whatever anyone else's punch reads (the app clock jumped to
   23:59:59 when another phone's open punch read later: "Clocked in · 11:59 PM", and the boot sweep then closed the
   foreman's 7:34 punch as 16 h old); a clock-out that would read before its clock-in asks when they left; a stored
   punch that ends before it starts is held at no hours and flagged, never stretched to midnight. The split sheet
   ticks only the work the person was on. The crew enters a missed day with a reason; the designer's Day Sheet has a
   day field and every active job, and its "hrs logged today" equals today's entries.
2  Mail. A sync that brings new mail rebuilds the assistant's "In your mail" digest; a replied thread leaves New.
3  Money. A vendor invoice naming a PO (or from a vendor with an open PO) is a bill against that PO, not rent; Matches
   Waiting never offers an estimate line; a deposit is proposed against the payer's open invoice; a client payment
   carries method, reference, deposit account and who recorded it.
4  Agency mail. DOB, LPC and inspection mail that moves an inspection proposes the new date and its schedule effect.
5  Driver. A ready pickup (vendor mail or a PO marked ready) is on the Route with its order number; field roles see
   crew and site messages only, and can message the coordinator by name.
6  Banking. A card statement mail can create its card account, last 4 digits only."""
import asyncio, re, sys
from harness import *

SLEEP = "ms => new Promise(r => setTimeout(r, ms))"


async def js(pg, body, arg=None):
    return await pg.evaluate("async (arg) => { const sleep = " + SLEEP + "; " + body + " }", arg)


async def fresh(p, uid, phone=False):
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, uid)
    await pg.evaluate("() => { getGeo = () => Promise.resolve(null); }")
    return b, pg, errs


# ------------------------------------------------------------------------------------------------ 1: hours
async def t_clock(c, p):
    b, pg, errs = await fresh(p, 'u_alberto', phone=True)
    r = await js(pg, """
      setCurrent('p121');
      // another phone's punch reads later than this phone's clock (the pilot: the foreman at 10:34, the crew at 10:32)
      DB.time = DB.time.filter(t => !(t.date === today() && ['em1', 'em2', 'em3'].includes(t.empId)));
      const later = today() + 'T17:29:59';
      DB.time.push({ id: 'tpz1', empId: 'em1', date: today(), in: later, out: '', breakMin: 0, projectId: 'p121', status: 'open', source: 'phone', work: [] });
      const before = appNowIso();
      view = 'time'; render(); await sleep(150);
      await clockEvent('in'); await sleep(300);
      const e = DB.time.find(t => t.empId === 'em2' && !t.out);
      const banner = (document.querySelector('#clock-card .big') || {}).innerText || '';
      return { before, now: appNowIso(), in: e && e.in, banner, audit: (DB.audit || []).slice(-3).map(a => a.ts) };""")
    c.ok(r['in'] and '23:59:59' not in r['in'] and r['in'][:13] == r['before'][:13],
         f"clock: the crew's clock-in is stamped at the app's time, not 11:59 PM ({r['in']} vs {r['before']})")
    c.ok('23:59:59' not in r['now'], f"clock: another phone's later punch never moves the app clock ({r['now']})")
    c.ok('11:59 PM' not in r['banner'] and 'Clocked in' in r['banner'], f"clock: the banner reads the real clock-in time ({r['banner']!r})")
    c.ok(not any('23:59:59' in (t or '') for t in r['audit']), f"clock: audit lines keep the real time ({r['audit']})")
    # a clock-out that would read before its own clock-in asks when they left, and refuses a time before the clock-in
    r = await js(pg, """
      const e = DB.time.find(t => t.empId === 'em2' && !t.out); e.in = today() + 'T17:29:00';
      clockEvent('out'); await sleep(300);
      const m = document.getElementById('mbm'), txt = m ? m.innerText : '';
      const t = m && m.querySelector('[data-f="t"]');
      t && (t.value = '17:00'); m && m.querySelector('#mbm-ok, .btn.primary').click(); await sleep(150);
      const still = !e.out;
      t && (t.value = '17:45'); m && document.getElementById('mbm') && m.querySelector('#mbm-ok, .btn.primary').click(); await sleep(300);
      document.getElementById('mbm') && document.getElementById('mbm').remove();
      return { asked: /When did you actually leave/.test(txt), still, out: e.out, h: hoursOf(e) };""")
    c.ok(r['asked'], 'clock: a clock-out before the clock-in asks when they left')
    c.ok(r['still'], 'clock: a leave time before the clock-in is refused')
    c.ok(r['out'] and r['out'].endswith('T17:45:00') and r['h'] > 0, f"clock: the day closes at the time given ({r['out']}, {r['h']} h)")
    # a stored punch that ends before it starts: no hours, flagged; never stretched to midnight
    r = await js(pg, """
      DB.time.push({ id: 'tpz2', empId: 'em3', date: today(), in: today() + 'T15:00:00', out: today() + 'T08:00:00', breakMin: 0, projectId: 'p121', status: 'open', source: 'phone', work: [] });
      save(); const t = DB.time.find(x => x.id === 'tpz2');
      return { out: t.out, h: hoursOf(t), flags: timeFlags(t) };""")
    c.ok(r['out'] and '23:59' not in r['out'] and r['h'] == 0, f"clock: a punch ending before it starts holds no hours ({r['out']}, {r['h']} h)")
    c.ok(any('before the clock-in' in f for f in r['flags']), f"clock: and is flagged for the person to confirm ({r['flags']})")
    c.ok(not errs, f'clock: no page errors ({errs[:2]})')
    await b.close()


async def t_split(c, p):
    b, pg, errs = await fresh(p, 'u_angel', phone=True)
    r = await js(pg, """
      setCurrent('p121');
      const e = { id: 'tpz3', empId: 'em1', date: today(), in: today() + 'T07:36:00', out: today() + 'T16:34:00', breakMin: 0, projectId: 'p121', status: 'open', source: 'phone', work: [] };
      DB.time = DB.time.filter(t => !(t.empId === 'em1' && t.date === today())); DB.time.push(e);
      f3DaySheet(e); await sleep(300);
      const m = document.getElementById('mbm');
      const rows = [...m.querySelectorAll('.f3-dayrow')].map(l => ({ name: l.querySelector('b').innerText, on: l.querySelector('[data-f3t2]').checked }));
      const title = (m.querySelector('h2, h3, .mbm-title, .hd') || {}).innerText || m.innerText.slice(0, 60);
      m.remove();
      return { rows, title };""")
    on = [x['name'] for x in r['rows'] if x['on']]
    c.ok('8.97' in r['title'] or '8.96' in r['title'] or '9 hours' in r['title'], f"split: the 7:36-16:34 day reads its own hours ({r['title']!r})")
    c.ok('Restoration' not in on, f'split: a trade that did not show is not ticked ({on})')
    c.ok('Rough electrical' not in on, f"split: another person's task is not ticked ({on})")
    c.ok(any('Windows' in n for n in on), f"split: the crew's started work is ticked ({on})")
    await b.close()


async def t_missing(c, p):
    b, pg, errs = await fresh(p, 'u_alberto', phone=True)
    r = await js(pg, """
      setCurrent('p121');
      const d = prevWork(iso(addDays(today(), -1)));
      DB.time = DB.time.filter(t => !(t.empId === 'em2' && t.date === d));
      view = 'time'; render(); await sleep(200);
      const card = document.getElementById('tm-missing');
      const btn = card && card.querySelector(`[data-tmlate="${d}"]`);
      btn && btn.click(); await sleep(200);
      let m = document.getElementById('mbm');
      const has = !!m, dayv = m && m.querySelector('[data-f="d"]').value;
      const jobs = m ? [...m.querySelectorAll('[data-f="pid"] option')].length : 0;
      m.querySelector('[data-f="n"]').value = 'framing garden bedroom';
      m.querySelector('#mbm-ok, .btn.primary').click(); await sleep(150);
      const refused = !DB.time.some(t => t.empId === 'em2' && t.date === d);
      m = document.getElementById('mbm');
      m.querySelector('[data-f="why"]').value = 'phone died, did not clock';
      m.querySelector('#mbm-ok, .btn.primary').click(); await sleep(250);
      const e = DB.time.find(t => t.empId === 'em2' && t.date === d);
      render(); await sleep(150);
      return { d, card: card ? card.innerText : '', has, dayv, jobs, active: DB.projects.filter(p => !p.archived).length, refused,
               e: e && { status: e.status, late: e.lateEntry, h: hoursOf(e), work: e.work }, flags: e ? timeFlags(e) : [],
               toast: [...document.querySelectorAll('.toast, #toast')].map(x => x.innerText).join(' | '),
               after: (document.getElementById('tm-missing') || {}).innerText || '' };""")
    c.ok('Missing Hours' in r['card'], f"missing: the crew's Clock shows the days with no time ({r['card'][:120]!r})")
    c.ok(r['has'] and r['dayv'] == r['d'], f"missing: the sheet opens on the missed day ({r['dayv']} vs {r['d']})")
    c.ok(r['jobs'] == r['active'], f"missing: every active job is offered ({r['jobs']} of {r['active']})")
    c.ok(r['refused'], 'missing: no reason, no entry')
    c.ok(r['e'] and r['e']['status'] == 'submitted' and r['e']['late'] and r['e']['late'].get('reason'),
         f"missing: the late day goes for approval with its reason ({r['e']})")
    c.ok(any('Entered late' in f for f in r['flags']), f"missing: approval sees it was entered late ({r['flags']})")
    c.ok(r['d'] not in r['after'] or 'Enter Missing Hours' in r['after'], 'missing: the day leaves the missing list')
    await b.close()


async def t_designer_day(c, p):
    b, pg, errs = await fresh(p, 'u_sarah')
    r = await js(pg, """
      view = 'sday'; render(); await sleep(250);
      const root = document.getElementById('sday-body');
      const head = root.querySelector('.ph .small').innerText;
      const td = today(), emp = myEmp();
      const today_h = Math.round(DB.time.filter(t => t.empId === emp.id && t.date === td).reduce((a, t) => a + hoursOf(t), 0) * 100) / 100;
      const future = DB.time.filter(t => t.empId === emp.id && t.date >= td && t.source === 'seed').length;
      const dayEl = root.querySelector('#st-addd'), opts = [...root.querySelectorAll('#st-addp option')].map(o => o.textContent);
      const y = prevWork(iso(addDays(td, -1)));
      dayEl.value = y; root.querySelector('#st-addp').value = 'p121'; root.querySelector('#st-addp').dispatchEvent(new Event('change'));
      root.querySelector('#st-addh').value = '3'; root.querySelector('#st-addn').value = 'A-301 stair section';
      root.querySelector('#st-addgo').click(); await sleep(300);
      document.getElementById('mbm') && document.getElementById('mbm').querySelector('.btn.primary').click(); await sleep(200);
      const e = DB.time.filter(t => t.empId === emp.id && t.date === y && t.projectId === 'p121').pop();
      view = 'sday'; render(); await sleep(200);
      const head2 = document.querySelector('#sday-body .ph .small').innerText;
      return { head, today_h, future, day: !!dayEl, opts, e: e && { date: e.date, h: hoursOf(e), late: e.lateEntry }, head2 };""")
    m = re.search(r'([\d.]+) hrs logged today', r['head'])
    c.ok(m and abs(float(m.group(1)) - r['today_h']) < 0.01, f"day sheet: the header equals today's entries ({r['head']!r} vs {r['today_h']})")
    c.ok(r['future'] == 0, f"day sheet: the seed writes no hours for today or later ({r['future']})")
    c.ok(r['day'], 'day sheet: there is a day field')
    c.ok(any('121 State' in o for o in r['opts']), f"day sheet: every active job is in the list, 121 State too ({r['opts'][:6]})")
    c.ok(r['e'] and r['e']['h'] == 3 and r['e']['late'], f"day sheet: hours land on the day picked, marked late ({r['e']})")
    c.ok(r['head2'] == r['head'], f"day sheet: a past day's hours leave today's header alone ({r['head2']!r})")
    await b.close()


async def main():
    only = sys.argv[1:]
    c = Checks()
    async with async_playwright() as p:
        for name, fn in [('clock', t_clock), ('split', t_split), ('missing', t_missing), ('day', t_designer_day)] + EXTRA:
            if only and name not in only: continue
            try:
                await fn(c, p)
            except Exception as e:
                c.ok(False, f'{name}: crashed {str(e)[:300]}')
    return c.done()


# ------------------------------------------------------------------------------------------------ 2: mail
MAIL_JS = """
  const W = demoWsFor(arg.uid), at = appNowMs() + (arg.dt || 60000);
  W.messages.push({ id: arg.id, threadId: arg.thread, labelIds: arg.sent ? ['SENT'] : ['INBOX', 'UNREAD'], internalDate: at, historyId: ++W.historyId,
    headers: { From: arg.from, To: arg.to, Cc: '', Subject: arg.subject, Date: new Date(at).toUTCString() }, body: arg.text, attachments: [] });
  W.now = at + 60000;
  const d = await gsRun({ quiet: true });
  return { mail: d ? d.mail.length : -1 };"""


async def t_mail(c, p):
    b, pg, errs = await fresh(p, 'u_chen')
    await js(pg, "await gcDemoConnect(); try { clearInterval(gsTimerId); } catch (e) {} return 1;")
    me = await js(pg, "return gcMine().email;")
    r = await js(pg, MAIL_JS, {'uid': 'u_chen', 'id': 'pf2m1', 'thread': 'pf2t1', 'from': 'Gowanus Plaster Works <office@gowanusplaster.example>', 'to': me,
                               'subject': 'Invoice GPW-118 - 121 State garden level skim coat', 'text': 'Attached our invoice GPW-118 for the skim coat at 121 State, $3,240. Thank you.'})
    r = await js(pg, """
      const A = paInit(), n = A.thread.find(m => m.nudge && m.ref && m.ref.kind === 'mail' && (DB.comms.find(c => c.msgId === m.ref.id) || {}).subject === 'Invoice GPW-118 - 121 State garden level skim coat');
      return { n: n && { text: n.text, unread: n.unread, day: n.day } };""")
    c.ok(r['n'] and r['n']['unread'], f"mail: a vendor invoice naming the job the way people write it ('121 State') becomes a New card on the sync ({r['n']})")
    # the foreman's agency mail is his: his jobs are the ones he works on
    b2, pg2, errs2 = await fresh(p, 'u_angel', phone=True)
    r2 = await js(pg2, "return { jobs: paMine().projects.map(p => p.id), s: paScoreItem('DOB NOW: inspection window 09/22/2026 - 121 STATE STREET', 'noreply@dob.example').score };")
    c.ok('p121' in r2['jobs'] and r2['s'] >= 6, f"mail: the foreman's jobs include the one he works on, so its agency mail is his ({r2})")
    await b2.close()
    # Chen replies on the thread: the card leaves New
    await js(pg, MAIL_JS, {'uid': 'u_chen', 'id': 'pf2m2', 'thread': 'pf2t1', 'sent': True, 'from': 'Chen Biron <' + me + '>', 'to': 'office@gowanusplaster.example',
                           'subject': 'Re: Invoice GPW-118 - 121 State garden level skim coat', 'text': 'Received, we will match it to the work.', 'dt': 120000})
    r = await js(pg, """
      const A = paInit(), n = A.thread.find(m => m.nudge && m.ref && m.ref.kind === 'mail' && (DB.comms.find(c => c.msgId === m.ref.id) || {}).subject === 'Invoice GPW-118 - 121 State garden level skim coat');
      // yesterday's seen cards fold away so today's are what the assistant shows
      A.thread.filter(m => m.nudge && m !== n).forEach(m => { m.day = iso(addDays(today(), -3)); m.unread = false; });
      view = 'pa'; render(); await sleep(300);
      const v = document.querySelector('#v-pa') || document.querySelector('.view.on') || document.body;
      return { unread: n && n.unread, answered: n && n.answered, fold: (v.querySelector('.pa-earlier') || {}).innerText || '',
               old: v.innerText.includes('landed in Drive') };""")
    c.ok(r['unread'] is False and r['answered'] == 'replied', f"mail: a replied thread leaves New ({r})")
    c.ok('earlier item' in r['fold'] and not r['old'], f"mail: seen cards of earlier days fold into one line ({r['fold']!r})")
    c.ok(not errs, f'mail: no page errors ({errs[:2]})')
    await b.close()


# ------------------------------------------------------------------------------------------------ 3: money
async def import_csv(pg, acct, name, text):
    await js(pg, "view = 'bank'; render(); bfImportDialog(arg); return 1;", acct)
    await pg.wait_for_selector('#bfi-file', state='attached')
    await pg.set_input_files('#bfi-file', files=[{'name': name, 'mimeType': 'text/csv', 'buffer': text.encode()}])
    await pg.wait_for_function("() => { const b = document.querySelector('#mbm-ok'); return b && !b.disabled && /Import \\d/.test(b.textContent); }", timeout=10000)
    await js(pg, "document.querySelector('#mbm-ok').click(); await sleep(600); document.querySelectorAll('#mbm').forEach(m => m.remove()); return 1;")


async def t_money(c, p):
    b, pg, errs = await fresh(p, 'u_chen')
    # a vendor invoice naming a PO is a bill against it, never rent: "Please" holds "lease"
    r = await js(pg, """
      const v = DB.vendors.find(x => x.name === 'Tino'); v.email = 'billing@tino-floors.example';
      cmImport([{ msgId: 'pf2tino', threadId: 'pf2tino', channel: 'email', from: { name: 'Tino', email: 'billing@tino-floors.example' }, to: ['chen@smartdesign.nyc'], cc: [],
        date: appNowIso(), subject: 'Invoice TIN-9001 for PO-2026-047', text: 'Please find invoice TIN-9001 for PO-2026-047 attached, $4,120.00, due net 30.', attachments: [], source: 'demo', owner: 'u_chen', labels: ['INBOX'] }]);
      const cm = DB.comms.find(x => x.msgId === 'pf2tino'), pr = (cm.proposals || []).find(x => x.kind === 'bill');
      // a real lease still reads as rent
      cmImport([{ msgId: 'pf2rent', threadId: 'pf2rent', channel: 'email', from: { name: 'Tino', email: 'billing@tino-floors.example' }, to: ['chen@smartdesign.nyc'], cc: [],
        date: appNowIso(), subject: 'October rent - yard lease', text: 'Rent for October under the yard lease: $3,000.00 due 10/1/2026.', attachments: [], source: 'demo', owner: 'u_chen', labels: ['INBOX'] }]);
      return { pr: pr && { summary: pr.summary, rent: pr.rent, poId: pr.poId, projectId: pr.projectId } };""")
    pr = r['pr'] or {}
    c.ok(pr and not pr.get('rent') and 'rent' not in (pr.get('summary') or ''), f"money: a flooring invoice naming its PO is not rent ({pr.get('summary')!r})")
    c.ok(pr.get('poId') == 'po3' and pr.get('projectId') == 'p121' and 'PO-2026-047' in pr.get('summary', ''), f"money: it is a bill against PO-2026-047 on the job ({pr})")
    await b.close()
    b, pg, errs = await fresh(p, 'u_controller')
    # Matches Waiting never offers an estimate line
    r = await js(pg, """
      const T = DB.txns.filter(t => /DUMPSTER/.test(t.desc)); T.forEach(t => { t.proposal = null; delete t.match; t.line = ''; });
      truthProposeAll(T.map(t => t.id));
      // an old line proposal from before is cleared too
      T[0].proposal = { kind: 'line', m: { estimateLineId: 'x' }, label: 'Estimate line' }; truthProposeAll(T.map(t => t.id));
      view = 'bank'; render(); await sleep(250);
      return { kinds: T.map(t => t.proposal && t.proposal.kind), shown: proposals().filter(t => /DUMPSTER/.test(t.desc)).length,
               text: [...document.querySelectorAll('.prop-card')].map(x => x.innerText).join(' ') };""")
    c.ok(all(k in (None, 'bill', 'po') for k in r['kinds']) and r['shown'] == 0 or all(k != 'line' for k in r['kinds']),
         f"money: the dumpster charge waits for no estimate-line match ({r['kinds']})")
    c.ok('Estimate line' not in r['text'], 'money: Matches Waiting shows no estimate line')
    # a wire from the Jessops is proposed against their open invoice by payer name and amount (part of it)
    await import_csv(pg, 'ac1', 'pf2_chase.csv', 'Date,Description,Amount,Reference\n' + await js(pg, "return today().slice(5,7) + '/' + today().slice(8) + '/' + today().slice(0,4);") + ',WIRE IN JESSOP J,12000.00,PF2W1\n')
    r = await js(pg, """
      const t = DB.txns.find(x => x.desc === 'WIRE IN JESSOP J' && +x.amt === 12000);
      return { p: t && t.proposal && { kind: t.proposal.kind, label: t.proposal.label, inv: (t.proposal.m || {}).invoiceId } };""")
    c.ok(r['p'] and r['p']['kind'] == 'invoice' and 'D140' in (r['p']['label'] or ''), f"money: the Jessop wire is proposed against their open invoice ({r['p']})")
    await b.close()
    # billing: the deposit is In the Bank, Not Applied with its proposal; Record It; the payment carries its trace
    b, pg, errs = await fresh(p, 'u_billing')
    await import_csv(pg, 'ac1', 'pf2_chase2.csv', 'Date,Description,Amount,Reference\n' + await js(pg, "return today().slice(5,7) + '/' + today().slice(8) + '/' + today().slice(0,4);") + ',WIRE IN JESSOP J,12000.00,PF2W2\n')
    r = await js(pg, """
      billTab = 'payments'; view = 'billing'; render(); await sleep(250);
      const card = document.getElementById('pay-inbank'), txt = card ? card.innerText : '';
      const i = [...card.querySelectorAll('.row')].findIndex(x => /JESSOP/.test(x.innerText));
      const btn = card.querySelectorAll('.row')[i].querySelector('[data-pibrec]'); btn && btn.click(); await sleep(250);
      const c = DB.clients.find(x => /Jessop/.test(x.name)), py = c.payments.find(x => +x.amount === 12000);
      const list = document.querySelector('#v-billing').innerText;
      return { txt, py, inv: c.invoices.find(x => x.number === 'INV-2026-D140-R').status, left: !!(document.getElementById('pay-inbank') || {innerText: ''}).innerText.match(/JESSOP/) };""")
    c.ok('In the Bank, Not Applied' in r['txt'] and 'D140' in r['txt'], f"money: Billing > Payments lists the deposit with its proposed invoice ({r['txt'][:200]!r})")
    py = r['py'] or {}
    c.ok(py.get('method') == 'Wire' and py.get('acctId') == 'ac1' and py.get('recordedBy') and py.get('txnId'), f"money: the payment carries method, deposit account, who recorded it and its bank line ({py})")
    c.ok(r['inv'] == 'partial' and not r['left'], f"money: the invoice reads part paid and the deposit leaves the list ({r['inv']}, {r['left']})")
    # the payment form chooses no method for the person, and a check needs its number
    r = await js(pg, """
      const c = DB.clients.find(x => /Jessop/.test(x.name)); paymentAllocate(c); await sleep(200);
      const m = document.getElementById('mbm'), sel = m.querySelector('#py-method');
      const first = sel.value; m.querySelector('#py-amt').value = '100';
      const n0 = c.payments.length; m.querySelector('#mbm-ok').click(); await sleep(150);
      const refused1 = c.payments.length === n0;
      sel.value = 'Check'; m.querySelector('#mbm-ok').click(); await sleep(150);
      const refused2 = c.payments.length === n0;
      m.querySelector('#py-ref').value = '1187'; m.querySelector('#py-acct').value = 'ac1';
      m.querySelector('[data-pyalloc]').value = '100'; m.querySelector('#mbm-ok').click(); await sleep(200);
      const py = c.payments[c.payments.length - 1];
      return { first, refused1, refused2, py };""")
    c.ok(r['first'] == '', f"money: the payment form picks no method for the person ({r['first']!r})")
    c.ok(r['refused1'] and r['refused2'], 'money: no method, or a check with no number, is not recorded')
    c.ok(r['py'] and r['py'].get('ref') == '1187' and r['py'].get('acctId') == 'ac1' and r['py'].get('recordedBy'), f"money: the recorded check carries number, account, who ({r['py']})")
    # a payment with no method reads "not recorded"; Reverse Payment is a linked reversal that re-opens the invoice
    r = await js(pg, """
      const c = DB.clients.find(x => /Jessop/.test(x.name)), inv = c.invoices.find(x => x.number === 'INV-2026-D140-R');
      c.payments.push({ id: 'pf2py', date: today(), amount: 500, invoiceId: inv.id });
      billTab = 'payments'; view = 'billing'; render(); await sleep(250);
      const row = [...document.querySelectorAll('#v-billing tr[data-edit="billpay:' + c.id + ':pf2py"]')][0];
      const cells = row ? row.innerText : '';
      row.querySelector('td').click(); await sleep(200);
      const m = document.getElementById('mbm'), has = !!(m && m.querySelector('#mbm-ok') && /Reverse Payment/.test(m.querySelector('#mbm-ok').innerText));
      m.querySelector('#mbm-ok').click(); await sleep(150);
      const refused = !c.payments.some(x => x.reverses === 'pf2py');
      m.querySelector('[data-f="why"]').value = 'recorded twice'; m.querySelector('#mbm-ok').click(); await sleep(250);
      const rv = c.payments.find(x => x.reverses === 'pf2py'), orig = c.payments.find(x => x.id === 'pf2py');
      return { cells, has, refused, rv, orig, st: inv.status, toast: [...document.querySelectorAll('.toast, #toast, .rc-toast')].map(x => x.innerText).join(' | ') };""")
    c.ok('ACH' not in r['cells'] and 'not recorded' in r['cells'], f"money: a payment with no method reads 'not recorded', never ACH ({r['cells']!r})")
    c.ok(r['has'] and r['refused'], 'money: the payment opens its own sheet with Reverse Payment, which needs a reason')
    c.ok(r['rv'] and r['rv']['amount'] == -500 and r['orig']['amount'] == 500 and r['orig'].get('reversalId') == r['rv']['id'], f"money: the reversal is a linked record; the payment is untouched ({r['rv']}, {r['orig']})")
    c.ok('reversed' in r['toast'] and 'Open' in r['toast'], f"money: it toasts with Open ({r['toast'][:120]!r})")
    await b.close()
    b, pg, errs = await fresh(p, 'u_chen')
    r = await js(pg, "return typeof payCanReverse === 'function' && payCanReverse();")
    c.ok(r is False, 'money: only billing and the controller reverse a payment')
    await b.close()


# ------------------------------------------------------------------------------------------------ 4: agency mail
async def t_agency(c, p):
    b, pg, errs = await fresh(p, 'u_alan')
    r = await js(pg, """
      const p = DB.projects.find(x => x.id === 'p121'), g = p.tasks.find(t => t.id === 'gwb'), i3 = p.inspections.find(i => i.id === 'i3');
      const us = (d) => d.slice(5, 7) + '/' + d.slice(8) + '/' + d.slice(0, 4);
      const d1 = prevWork(iso(addDays(g.start, -6))), d2 = g.start;
      i3.status = 'not-scheduled'; i3.date = '';
      DB.field.subs.push({ id: 'pf2sub', projectId: 'p121', vendor: 'Gowanus Plumbing Co', trade: 'Plumbing', date: d1, status: 'confirmed', taskId: 'rplumb' });
      const mk = (id, day, sub) => ({ msgId: id, threadId: id, channel: 'email', from: { name: 'DOB NOW', email: 'noreply@dobnow.example' }, to: ['alan@smartdesign.nyc'], cc: [],
        date: day + 'T08:00:00', subject: sub, text: ['DOB NOW Inspections', 'Job B09990001-I1, 121 STATE STREET, BROOKLYN', 'Inspection type: Plumbing rough', sub].join(' / '), attachments: [], source: 'demo', owner: 'u_alan', labels: ['INBOX'] });
      cmImport([mk('pf2dob1', iso(addDays(today(), -1)), 'DOB NOW: Job B09990001-I1 - rough plumbing inspection scheduled ' + us(d1) + ' window 8:00 AM - 12:00 PM - 121 STATE STREET')]);
      cmImport([mk('pf2dob2', today(), 'DOB NOW: Job B09990001-I1 - rough plumbing inspection window ' + us(d2) + ' 8:00 AM - 12:00 PM - 121 STATE STREET')]);
      const cm = DB.comms.find(x => x.msgId === 'pf2dob2'), pr = (cm.proposals || []).find(x => x.kind === 'inspection');
      return { d1, d2, gstart: g.start, pr: pr && { summary: pr.summary, moveFrom: pr.moveFrom, subs: pr.subMoves, gate: pr.gate } };""")
    pr = r['pr'] or {}
    c.ok(pr.get('moveFrom') == r['d1'], f"agency: the second notice on the docket proposes the move from the first date ({pr.get('moveFrom')} vs {r['d1']})")
    c.ok(any(x['id'] == 'pf2sub' for x in (pr.get('subs') or [])), f"agency: the plumber booked for the old day moves with it ({pr.get('subs')})")
    c.ok(pr.get('gate') and pr['gate']['taskId'] == 'gwb' and pr['gate']['to'] > r['d2'], f"agency: the task it gates moves past the new date ({pr.get('gate')})")
    c.ok('moves it from' in (pr.get('summary') or ''), f"agency: the proposal says what it moves ({pr.get('summary')!r})")
    # the foreman sees it on Site before anyone applies it
    r2 = await js(pg, """
      signIn('u_angel'); setCurrent('p121'); view = 'fsite'; render(); await sleep(250);
      const t = (document.querySelector('.ag-move') || {}).innerText || '';
      signIn('u_alan'); render(); await sleep(100);
      const cm = DB.comms.find(x => x.msgId === 'pf2dob2'), pr = cm.proposals.find(x => x.kind === 'inspection');
      cmApply(cm, pr); await sleep(100);
      const p = DB.projects.find(x => x.id === 'p121'), i3 = p.inspections.find(i => i.id === 'i3'), g = p.tasks.find(t => t.id === 'gwb'), sb = DB.field.subs.find(s => s.id === 'pf2sub');
      return { site: t, i3: [i3.status, i3.date], g: [g.start, (g.history || []).slice(-1)[0]], sb: [sb.date, sb.status], applied: pr.applied };""")
    c.ok('Agency Notice' in r2['site'], f"agency: Site shows the move before it is booked ({r2['site'][:160]!r})")
    c.ok(r2['i3'] == ['scheduled', r['d2']], f"agency: applying books the new date ({r2['i3']})")
    c.ok(r2['g'][0] > r['d2'] and r2['g'][1] and r2['g'][1].get('source') == 'inspection', f"agency: the gated task moves with its history ({r2['g']})")
    c.ok(r2['sb'] == [r['d2'], 'unconfirmed'], f"agency: the booking moves to the new day, to confirm ({r2['sb']}; {r2['applied']})")
    c.ok(not errs, f'agency: no page errors ({errs[:2]})')
    await b.close()


# ------------------------------------------------------------------------------------------------ 5: driver
async def t_driver(c, p):
    b, pg, errs = await fresh(p, 'u_chen')
    r = await js(pg, """
      await gcDemoConnect(); try { clearInterval(gsTimerId); } catch (e) {}
      const ready = drvReadyPickups();
      // a "we pick up" PO marked ready is a stop too
      const po = DB.pos.find(x => x.projectId === 'p121' && ['issued', 'partial'].includes(x.status));
      po.readyForPickup = { at: appNowIso(), by: 'Chen Biron' };
      signIn('u_alex'); setCurrent('p121'); view = 'route'; render(); await sleep(300);
      const v = (document.querySelector('#v-route') || document.body).innerText;
      return { ready: ready.map(x => [x.vendor, x.orderRef, x.projectId]), v, po: po.number, vendor: po.vendor };""")
    c.ok(any(x[1] == '88412' for x in r['ready']), f"driver: the vendor's ready mail is a ready pickup ({r['ready']})")
    c.ok('order 88412' in r['v'] and 'Brooklyn Lumber' in r['v'], "driver: the Route has the Brooklyn Lumber stop with its order number")
    c.ok(r['po'] in r['v'], f"driver: a PO marked ready for pickup is on the Route ({r['po']})")
    c.ok('Buy 25 boards GWB' not in r['v'], 'driver: the boards already paid at the yard are not bought again at the store')
    # the job chat: crew and site only, no client money; a message to the coordinator by name
    r = await js(pg, """
      const p = DB.projects.find(x => x.id === 'p121'), cl = DB.clients.find(x => x.id === p.clientId);
      p.chat.push({ id: 'pf2c1', by: (cl.contacts[0] || {}).name || cl.name, text: 'Before we sign the change order, how many days does it add?', t: nowStamp(), files: [] },
                  { id: 'pf2c2', by: 'System', text: 'INV-2026-099 - Progress billing ($11,386) is ready for you on your Overview', t: nowStamp(), files: [] },
                  { id: 'pf2c3', by: 'Alberto', text: 'Framing in the garden bedroom is done, plumber can start', t: nowStamp(), files: [] });
      view = 'chat'; render(); await sleep(250);
      const list = document.getElementById('chat-list').innerText;
      const to = document.getElementById('chat-to'), opts = to ? [...to.options].map(o => o.textContent) : [];
      to.value = 'u_chen'; document.getElementById('chat-text').value = 'What time is the yard pickup for 88412?'; sendChat(); await sleep(300);
      const a = (p.actions || []).find(x => /Answer Alex/.test(x.title));
      return { list, opts, a: a && [a.assignee, a.title] };""")
    c.ok('how many days' not in r['list'] and 'INV-2026-099' not in r['list'], f"driver: the job chat shows no client question and no client money ({r['list'][-300:]!r})")
    c.ok('Framing in the garden bedroom' in r['list'], 'driver: crew messages show')
    c.ok(any('Chen Biron' in o for o in r['opts']), f"driver: the coordinator can be messaged by name ({r['opts']})")
    c.ok(r['a'] and r['a'][0] == 'Chen Biron', f"driver: the message is on Chen's list ({r['a']})")
    c.ok(not errs, f'driver: no page errors ({errs[:2]})')
    await b.close()

EXTRA = [('mail', t_mail), ('money', t_money), ('agency', t_agency), ('driver', t_driver)]

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
