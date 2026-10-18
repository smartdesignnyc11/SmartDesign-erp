"""The three-day pilot's day-1 findings (lane pilotfix1), each reproduced as the person hit it, on the phone where
the person is on the phone, then held. Invented data only: the seed plus the records each check adds.

1  The foreman's Daily Log fills crew hours from today's clock (overlapping entries once, an open one to now), not
   from a stale draft; a line that disagrees with the clock shows both numbers and Sign and Send refuses with the
   reason until the clock's hours are used or a reason is given; still clocked in, he clocks out beside the button.
2  The controller sees every purchase order whatever job he last opened; the New Vendor Bill offers the vendor's
   open POs on every job and pre-selects the one that matches; a mailed invoice offers Enter the Bill.
3  A colleague's note about a client's check against "invoice 2" is not "billed someone not a client on file".
4  A vendor's paid order in mail connects to the open request and Buy Board line for the same goods (Bought), and
   a new PO for those goods warns of the double order.
5  New Change Order on the job's page and on the field answer; back returns to the previous screen; a CO line's
   price comes from past work or says it found none.
6  Clock Out on Crew and beside Sign and Send; hours waiting on approval on Today and on the log.
7  "by Monday" is a date, not an item; a need-by on Labor Day warns and offers the working day before; a removed
   line stays removed; a request card on the coordinator's Home opens the request.
8  A statement already imported reads "already here" and is not offered.
9  Make It a Task takes its due date from the record (the LPC hearing), not a default.
10 A stored-materials bill and a progress line for the same scope warn of the double bill, naming both."""
import asyncio, re, sys
from harness import *

SLEEP = "ms => new Promise(r => setTimeout(r, ms))"

async def js(pg, body, arg=None):
    return await pg.evaluate("async (arg) => { const sleep = " + SLEEP + "; " + body + " }", arg)

async def fresh(p, uid, phone=False):
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, uid)
    return b, pg, errs

# ------------------------------------------------------------------------------------------------ 1 + 6: the log
async def t_daily_log(c, p):
    b, pg, errs = await fresh(p, 'u_angel', phone=True)
    r = await js(pg, """
      const p = DB.projects.find(x => x.id === 'p121');
      // the pilot: the seed has him 07:00-15:30, he clocked in again (an open entry) and a stale draft carried 14 h
      DB.time.push({ id: 'tpx1', empId: 'em1', date: today(), in: today() + 'T06:00:00', out: '', breakMin: 0, projectId: 'p121', code: '12', status: 'open', source: 'phone', work: [] });
      const d0 = dlDraft(p, today()); d0.crew[0].hours = 14; delete d0.crew[0].edited;
      view = 'flog'; render(); await sleep(250);
      const dr = DB.field.dlDraft['p121|' + today()], clock = dlClockFor(p, today());
      const head = document.querySelector('.dl-card .hd').innerText;
      return { angel: dr.crew.find(x => x.empId === 'em1').hours, clock: clock.find(x => x.empId === 'em1').hours,
               overlap: clock.find(x => x.empId === 'em1').overlap, head };""")
    c.ok(r['angel'] == r['clock'], f"log: a stale 14 h draft re-reads the clock ({r['angel']} h on the log, {r['clock']} h on the clock)")
    c.ok(r['overlap'], 'log: two overlapping entries are counted once and said so')
    c.ok('carried from' not in r['head'] and "today's clock" in r['head'], f"log: the header says the crew is from today's clock, not \"carried from\" ({r['head']!r})")
    # he types 14 h: the sign step names both numbers and refuses
    r = await js(pg, """
      const dr = DB.field.dlDraft['p121|' + today()]; dr.weather = 'Clear'; dr.step = 1; render(); await sleep(200);
      const i = document.querySelector('[data-dl="crew.hours"][data-i="0"]'); i.value = '14'; i.dispatchEvent(new Event('input'));
      dr.step = 6; dr.signed = true; render(); await sleep(200);
      for (let k = 0; k < 4; k++) { const st = document.querySelector('.dl-gaps [data-dlstill$=":0"]'); if (!st) break; st.click(); await sleep(120); }
      const nav = [...document.querySelectorAll('.dl-nav button')].map(b => b.innerText.trim());
      document.querySelector('#dl-next').click(); await sleep(250);
      return { gaps: (document.querySelector('.dl-gaps') || {}).innerText || '', msg: (document.querySelector('.dl-msg') || {}).innerText || '',
               nav, filed: dlLogs('p121').some(l => l.date === today()) };""")
    c.ok('the log says 14 h, the clock says' in r['gaps'], f"log: the mismatch shows both numbers ({r['gaps'][:160]!r})")
    c.ok(not r['filed'] and 'clock' in r['msg'], f"log: Sign and Send refuses with the reason ({r['msg']!r})")
    c.ok('Clock Out' in r['nav'] and 'Sign and Send' in r['nav'], f"log: Clock Out sits beside Sign and Send while he is clocked in ({r['nav']})")
    # Use the Clock, clock out: signs
    r = await js(pg, """
      const dr = DB.field.dlDraft['p121|' + today()]; dr.step = 1; render(); await sleep(150);
      const u = document.querySelector('[data-dlclock="0"]'); u && u.click(); await sleep(150);
      const fixed = dr.crew[0].hours === dr.crew[0].clockH;
      dr.step = 6; render(); await sleep(150);
      const co = [...document.querySelectorAll('.dl-nav [data-dlclockout]')][0]; co && co.click(); await sleep(900);
      const open = DB.time.some(t => t.empId === 'em1' && !t.out);
      const dr2 = DB.field.dlDraft['p121|' + today()]; dr2.signed = true; render(); await sleep(150);
      document.querySelector('#dl-next') && document.querySelector('#dl-next').click(); await sleep(400);
      const l = dlLogs('p121').find(x => x.date === today());
      return { fixed, open, filed: !!l, hours: l && l.crew.find(x => x.empId === 'em1'), clock: dlClockFor(DB.projects.find(x => x.id === 'p121'), today()).find(x => x.empId === 'em1').hours };""")
    c.ok(r['fixed'], 'log: Use the Clock puts the clock\'s hours back')
    c.ok(not r['open'], 'log: Clock Out beside Sign and Send clocks the foreman out')
    c.ok(r['filed'] and r['hours'] and abs(r['hours']['hours'] - r['clock']) < 0.01, f"log: once it agrees with the clock it signs, carrying the clock's hours ({r['hours']}, clock {r['clock']})")
    # a reason is the other way out: kept on the record
    r = await js(pg, """
      const p = DB.projects.find(x => x.id === 'p206'); setCurrent('p206');
      const d = dlDraft(p, today()); d.weather = 'Clear';
      d.crew.push({ name: 'Day labor', trade: 'Helper', hours: 4, manual: true });
      const g1 = dlClockGaps(d, p).length; d.crew[d.crew.length - 1].why = 'Paid cash helper, no phone';
      return { g1, g2: dlClockGaps(d, p).length };""")
    c.ok(r['g1'] == 1 and r['g2'] == 0, f"log: someone not on the clock needs a reason, and the reason clears it ({r})")
    c.ok(not errs, f'log: no page errors {errs[:2]}')
    await b.close()
    # 6: Crew and Today, on a fresh day
    b, pg, errs = await fresh(p, 'u_angel', phone=True)
    r = await js(pg, """
      setCurrent('p121');
      DB.time.push({ id: 'tpx2', empId: 'em1', date: today(), in: today() + 'T06:30:00', out: '', breakMin: 0, projectId: 'p121', code: '12', status: 'open', source: 'phone', work: [] });
      view = 'fcrew'; render(); await sleep(250);
      const crew = document.querySelector('.view.on').innerText;
      const btn = document.querySelector('#fcrew-body [data-fclock="out"]');
      view = 'ftoday'; render(); await sleep(250);
      const td = document.querySelector('.view.on .dl-appr');
      view = 'flog'; DB.field.dlDraft = {}; render(); await sleep(200);
      const dr = DB.field.dlDraft['p121|' + today()]; dr.step = 1; render(); await sleep(150);
      const lg = document.querySelector('.dl-body .dl-appr');
      btn && btn.click(); await sleep(900);
      return { soFar: (crew.match(/Angel\\n[^\\n]*?([\\d.]+) h so far/) || [])[1], btn: !!btn, today: td ? td.innerText : '', log: lg ? lg.innerText : '',
               out: !DB.time.some(t => t.id === 'tpx2' && !t.out) };""")
    c.ok(r['btn'] and r['out'], f"crew: Clock Out for the foreman himself on Crew, and it clocks him out ({r['btn']}, {r['out']})")
    c.ok(r['soFar'] and float(r['soFar']) > 0, f"crew: an open entry shows its hours so far, not 0.0 ({r['soFar']})")
    c.ok('Satish' in r['today'] and 'flagged' in r['today'], f"today: hours waiting on his approval, Satish's flagged entry named ({r['today'][:120]!r})")
    c.ok('Satish' in r['log'], f"log: the same hours to approve on the Daily Log ({r['log'][:80]!r})")
    c.ok(not errs, f'log: no page errors {errs[:2]}')
    await b.close()

# ------------------------------------------------------------------------------------------------ 2: POs and bills
async def t_controller_pos(c, p):
    b, pg, errs = await fresh(p, 'u_controller')
    r = await js(pg, """
      setCurrent('p45'); view = 'po'; render(); await sleep(250);
      const t = document.querySelector('#po-table').innerText;
      const tile = [...document.querySelectorAll('.view.on [data-tlk], .view.on .tl')].map(x => x.innerText).join(' | ');
      openBill(null); await sleep(200);
      const v = document.getElementById('e-vendor'); v.value = 'Carlos Millwork'; v.dispatchEvent(new Event('input')); v.dispatchEvent(new Event('change')); await sleep(100);
      const sel = document.getElementById('e-po');
      const opts = [...sel.options].map(o => o.text), picked = sel.selectedOptions[0] ? sel.selectedOptions[0].text : '', proj = document.getElementById('e-proj').value;
      closeEditor && closeEditor();
      return { t, opts, picked, proj };""")
    c.ok('PO-2026-048' in r['t'] and 'No purchase orders yet' not in r['t'], f"controller: Purchase Orders lists PO-2026-048 though the last job opened was 45 Cranberry ({r['t'][:120]!r})")
    c.ok(any('PO-2026-048' in o for o in r['opts']), f"controller: the New Vendor Bill offers Carlos Millwork's open PO ({r['opts']})")
    c.ok('PO-2026-048' in r['picked'] and r['proj'] == 'p121', f"controller: the one open PO is pre-selected and sets the job ({r['picked']!r}, {r['proj']})")
    r = await js(pg, """
      await gcDemoConnect(); await sleep(400);
      const rows = nyhRows().filter(x => /CM-0102/.test(x.title));
      const cm = DB.comms.find(x => /CM-0102/.test(x.subject) && x.owner === 'u_controller');
      const box = document.createElement('div'); box.innerHTML = cmMsgHtml(cm);
      const btn = [...box.querySelectorAll('[data-cmapply]')].map(b => b.innerText.trim());
      return { rows: rows.map(x => [x.verb, x.route]), btn };""")
    c.ok(any(v == 'Enter the Bill' and rt == 'controller' for v, rt in r['rows']), f"controller: the mailed CM-0102 reaches his Home's queue as Enter the Bill ({r['rows']})")
    c.ok('Enter the Bill' in r['btn'], f"controller: the Inbox offers Enter the Bill on the mail itself ({sorted(set(r['btn']))})")
    # the tile counts follow the same scope as the rows
    r = await js(pg, """poScope = ''; view = 'po'; render(); await sleep(200);
      const all = poScopeList().length; poScope = 'p45'; render(); await sleep(200);
      const t = document.querySelector('#po-table').innerText; poScope = ''; return { all, t };""")
    c.ok(r['all'] == 4 and 'pick All Jobs' in r['t'], f"controller: a job with no orders says so and points to All Jobs ({r})")
    c.ok(not errs, f'controller: no page errors {errs[:2]}')
    await b.close()

# ------------------------------------------------------------------------------------------------ 3: false catch
async def t_own_mail_client(c, p):
    b, pg, errs = await fresh(p, 'u_billing')
    r = await js(pg, """
      await gcDemoConnect(); await sleep(400);
      const cm = DB.comms.find(x => /check 2214/i.test(x.subject) && x.owner === 'u_billing');
      const props = cm ? (cm.proposals || []).map(p => [p.kind, p.summary]) : null;
      // the same note with a client and an invoice ordinal, invented, read fresh
      const mk = (text) => cmRead({ id: 'tx' + Math.random(), owner: 'u_billing', channel: 'email', from: { name: 'Controller', email: 'controller@smartdesign.nyc' }, to: ['billing@smartdesign.nyc'], subject: 'Check note', text, date: today() + 'T09:00:00', labels: [] }).map(p => p.kind + ': ' + p.summary);
      const kl = DB.clients.find(x => /Klein/.test(x.name));
      return { props, named: mk('The Kleins’ check 2001 for $5,000.00 posted and is recorded against invoice 2.'),
               ordinal: kl ? (cmInvoiceByOrdinal('invoice 2', kl) || {}).number : null,
               stranger: mk('Please send the invoice for $4,000.00 to the Ortegas at 12 Main.') };""")
    c.ok(r['props'] is not None and not any('not a client on file' in s for k, s in r['props']), f"billing: the controller's note on the Kleins' check is not \"billed someone not a client on file\" ({r['props']})")
    c.ok(not any('not a client on file' in s for s in r['named']), f"billing: a client named in a colleague's note counts as on file ({r['named']})")
    c.ok(r['ordinal'] == 'INV-2026-035', f"billing: \"invoice 2\" is the Kleins' second invoice ({r['ordinal']})")
    c.ok(any('not a client on file' in s for s in r['stranger']), f"billing: a bill to somebody not on file is still said ({r['stranger']})")
    c.ok(not errs, f'billing: no page errors {errs[:2]}')
    await b.close()

# ------------------------------------------------------------------------------------------------ 4: bought in mail
async def t_bought_from_mail(c, p):
    b, pg, errs = await fresh(p, 'u_chen', phone=True)
    r = await js(pg, """
      await gcDemoConnect(); await sleep(400);
      const ask = DB.comms.find(x => /need 25 boards GWB/.test(x.subject) && x.owner === 'u_chen');
      cmApply(ask, ask.proposals.find(p => p.kind === 'request'));
      const pr = DB.projects.find(x => x.id === 'p121'), rq = pr.requests[pr.requests.length - 1];
      const bl = DB.comms.find(x => /88412/.test(x.subject) && x.owner === 'u_chen'), pk = bl.proposals.find(x => x.kind === 'pickup');
      const row = nyhRows({ everyone: true }).find(x => x.commId === bl.id && x.pkind === 'pickup');
      const n0 = pr.requests.length, did = String(cmApply(bl, pk));
      const m5 = pr.materials.find(m => m.id === 'm5');
      const po = { id: 'pdx', number: 'PO-T', vendor: 'Home Depot', projectId: 'p121', status: 'draft', lines: [{ id: 'l1', item: '5/8 GWB 4x8', qty: 25, unit: 'sheets', price: 15 }] };
      return { title: row ? row.title : '', did, n: pr.requests.length - n0, st: rq.status, ref: rq.orderRef, eta: rq.eta, pick: (rq.items || []).map(i => i.pickupFrom),
               m5: [m5.status, m5.vendor, m5.cost], dup: poDoubleOrder(po) };""")
    c.ok(r['title'].startswith('Bought') and 'request' in r['title'], f"coord: the paid order reads Bought and names the open request ({r['title'][:160]!r})")
    c.ok(r['n'] == 0 and r['st'] == 'ordered' and r['ref'] == '88412' and r['eta'] == '2026-09-04', f"coord: applying marks Angel's request ordered with the order and pickup, no second request ({r})")
    c.ok(any(x and x.startswith('v:Brooklyn') for x in r['pick']), f"coord: the pickup stays on the driver's route ({r['pick']})")
    c.ok(r['m5'][0] == 'ordered' and r['m5'][1] == 'Brooklyn Lumber' and r['m5'][2], f"coord: the Buy Board line has vendor, cost and ordered ({r['m5']})")
    c.ok(r['dup'] and '88412' in r['dup'][0], f"coord: a new PO for the same goods names the purchase ({r['dup']})")
    c.ok('card' in r['did'], f"coord: the card purchase is recorded or matched ({r['did']!r})")
    c.ok(not errs, f'coord: no page errors {errs[:2]}')
    await b.close()

# ------------------------------------------------------------------------------------------------ 7: request quirks
async def t_request_quirks(c, p):
    b, pg, errs = await fresh(p, 'u_angel', phone=True)
    r = await js(pg, """
      comp.lines = []; comp.when = '';
      const L = parseLocal('4 rolls blue tape and 4 rolls rosin paper, needed by Mon 9/7 for the floor crew');
      return { items: L.map(l => l.what), when: comp.when, note: comp.dateNote || '' };""")
    c.ok(r['items'] == ['blue tape', 'rosin paper'], f"field: \"needed by Mon 9/7\" is not an item ({r['items']})")
    c.ok(r['when'] == '2026-09-07', f"field: it is the need-by date ({r['when']})")
    r = await js(pg, """
      view = 'req'; render(); await sleep(250);
      comp.when = '2026-09-07'; renderComposer(); await sleep(100);
      const w = document.querySelector('#composer .req-dayoff'); const t = w ? w.innerText : '';
      const bt = w && w.querySelector('[data-reqb4]'); bt && bt.click(); await sleep(100);
      return { t, when: comp.when };""")
    c.ok('Labor Day' in r['t'], f"field: a need-by on Labor Day warns ({r['t']!r})")
    c.ok(r['when'] == '2026-09-04', f"field: one tap makes it the working day before, Fri 9/4 ({r['when']})")
    # a line removed while the slower read is still out stays removed
    r = await js(pg, """
      comp.lines = []; comp.removed = [];
      const box = document.querySelector('#cp-text'); box.value = '4 rolls blue tape, 4 rolls rosin paper, 2 tubes caulk';
      const run = compRead(); await sleep(30);
      const x = [...document.querySelectorAll('#composer [data-cx]')].find(e => (comp.lines[+e.dataset.cx] || {}).what === 'caulk');
      x && x.click(); await run; await sleep(100);
      return comp.lines.map(l => l.what);""")
    c.ok('caulk' not in r and 'blue tape' in r and 'rosin paper' in r, f"field: the removed line does not come back, the others stay ({r})")
    await b.close()
    b, pg, errs2 = await fresh(p, 'u_chen', phone=True)
    r = await js(pg, """
      view = 'home'; render(); await sleep(350);
      const card = [...document.querySelectorAll('#v-home [data-ea]')].find(e => { try { return JSON.parse(e.dataset.ea).ack; } catch (x) { return false; } });
      if (!card) return { card: false };
      const body = card.querySelector('.grow') || card; body.click(); await sleep(200);
      const m = document.getElementById('mbm'), btns = m ? [...m.querySelectorAll('button')].map(b => b.innerText.trim()) : [];
      const ack = m && m.querySelector('[data-rqs="ack"]'); ack && ack.click(); await sleep(200);
      return { card: true, title: m ? m.querySelector('h3').innerText : '', btns, st: DB.projects.find(x => x.id === 'p121').requests.find(x => x.id === 'rq1').status };""")
    c.ok(r['card'] and r['title'].startswith('Request'), f"coord: tapping a request card on Home opens the request ({r.get('title')!r})")
    c.ok('Acknowledge' in r.get('btns', []) and 'Order' in r.get('btns', []), f"coord: the request offers Acknowledge and Order ({r.get('btns')})")
    c.ok(r.get('st') == 'ack', f"coord: Acknowledge from the sheet acknowledges ({r.get('st')})")
    c.ok(not errs and not errs2, f'field/coord: no page errors {(errs + errs2)[:2]}')
    await b.close()

# ------------------------------------------------------------------------------------------------ 18: payment check
async def t_payment_check(c, p):
    b, pg, errs = await fresh(p, 'u_controller')
    r = await js(pg, """
      const b = DB.bills.find(x => x.number === 'WW-2026-118'), t = DB.txns.find(x => x.id === 't9');
      t.proposal = { t: nowStamp(), by: 'auto', kind: 'bill', billId: b.id, why: 'amount and vendor agree' };
      view = 'bank'; render(); await sleep(350);
      const row = [...document.querySelectorAll('.prop-row')].find(r => /WW-2026-118/.test(r.innerText));
      const txt = row ? row.innerText : '', btns = row ? [...row.querySelectorAll('button')].map(x => x.innerText.trim()) : [];
      confirmMatch(t); await sleep(100);
      return { txt, btns, linked: t.billId === b.id, toast: (document.getElementById('toast') || {}).innerText || '' };""")
    c.ok('approved $29,700' in r['txt'] and '$3,800 over' in r['txt'], f"controller: the match shows the approved amount beside the paid one and the $3,800 over ({r['txt'][:220]!r})")
    c.ok('Confirm' not in r['btns'] and any('Review' in x for x in r['btns']), f"controller: it cannot be confirmed above what was approved ({r['btns']})")
    c.ok(not r['linked'] and 'Not confirmed' in r['toast'], f"controller: confirmMatch refuses the overpayment, with the numbers ({r['toast'][:140]!r})")
    r = await js(pg, """
      view = 'bank'; render(); await sleep(350);
      const head = bankUnmatched().n;
      const rows = [...document.querySelectorAll('#bf-imports [data-bfimp]')];
      const un = rows.map(x => +((x.innerText.match(/(\\d+) unmatched/) || [])[1] || 0));
      const sum = un.reduce((a, x) => a + x, 0), any = rows.map(x => x.innerText).join(' | ');
      rows[0] && rows[0].querySelector('.grow').click(); await sleep(200);
      const m = document.getElementById('mbm');
      return { head, sum, rows: rows.length, any: any.slice(0, 200), sheet: m ? m.querySelectorAll('[data-bfimpline]').length : 0 };""")
    c.ok(r['sum'] > 0 and r['sum'] <= r['head'], f"controller: Statement Imports count unmatched lines by the header's own predicate ({r['sum']} on the rows, {r['head']} in the header)")
    c.ok(r['sheet'] > 0, f"controller: tapping an import row opens its lines ({r['sheet']} lines)")
    r = await js(pg, """
      const t = { id: 'tpx9', date: '2026-09-02', acct: 'ac1', desc: 'ZELLE TO NEMO TILE', amt: -640, cat: 'uncat' };
      DB.txns.push(t); const C = truthCandidates(t).filter(x => x.kind === 'newbill').map(x => x.label);
      return C;""")
    c.ok(not any('Enter the bill' in x for x in r) and (not r or 'Paid before approval' in r[0]), f"controller: a payment with no bill goes to the paid-before-approval review, not Enter the bill ({r})")
    c.ok(not errs, f'controller: no page errors {errs[:2]}')
    await b.close()
    # the owner's approval of part confirms the payment at the amount approved
    b, pg, errs = await fresh(p, 'u_owner')
    r = await js(pg, """
      const b = DB.bills.find(x => x.number === 'WW-2026-118');
      const ok = pay3ShortPay(b, 29700, 'billed 10 windows, the PO is 9; credit requested');
      const t = DB.txns.find(x => x.id === 't9');
      return { ok, st: b.status, short: b.short && b.short.approved, linked: t.billId === b.id, word: payCheckWord(b) };""")
    c.ok(r['ok'] and r['short'] == 29700 and r['linked'], f"owner: approving the PO amount and disputing the rest still confirms the payment ({r})")
    c.ok('approved at $29,700' in r['word'] and '$3,800 disputed' in r['word'], f"owner: the bill reads approved at $29,700 with $3,800 disputed ({r['word']!r})")
    await b.close()

# ------------------------------------------------------------------------------------------------ 5: documents
async def t_documents(c, p):
    b, pg, errs = await fresh(p, 'u_alan', phone=True)
    r = await js(pg, """
      setCurrent('p121'); view = 'dash'; render(); await sleep(300);
      const btns = [...document.querySelectorAll('#v-dash .doc-jobacts button')].map(b => b.innerText.trim());
      document.querySelector('#v-dash [data-jobnew="co"]').click(); await sleep(250);
      const co = { title: (document.querySelector('#mbm h3') || {}).innerText || '', client: (document.querySelector('#mbm [data-f="clientId"]') || {}).value, proj: (document.querySelector('#mbm [data-f="projectId"]') || {}).value };
      mbCloseModal();
      document.querySelector('#v-dash [data-jobnew="est"]').click(); await sleep(250);
      const pick = document.querySelector('#mbm input[name="ne-t"][value=""]'); pick && (pick.checked = true); document.querySelector('#mbm-ok').click(); await sleep(400);
      const cl = DB.clients.find(x => x.id === S.clientId), d = cl.estimates[cl.estimates.length - 1];
      return { btns, co, est: { lines: d.lines.length, pid: d.projectId, status: d.status, total: docTotal(d).total }, scope: ['scope', 'inclusions', 'exclusions'].every(k => !!document.querySelector('[data-d="' + k + '"]')) };""")
    c.ok(r['btns'] == ['New Change Order', 'New Estimate'], f"pm: the job's page offers New Change Order and New Estimate ({r['btns']})")
    c.ok(r['co']['title'] == 'New Change Order' and r['co']['client'] == 'cl121' and r['co']['proj'] == 'p121', f"pm: New Change Order from the job starts for its client and job ({r['co']})")
    c.ok(r['est']['pid'] == 'p121' and r['est']['lines'] <= 1 and r['est']['total'] == 0, f"pm: New Estimate starts blank on the job, not a copy of the contract ({r['est']})")
    c.ok(r['scope'], 'pm: the new estimate has Scope, Inclusions and Exclusions')
    r = await js(pg, """
      const cl = DB.clients.find(x => x.id === 'cl121'), d = cl.estimates[cl.estimates.length - 1];
      // the item library prices by the unit; a contract line's lump total never does
      const lib = itemLib().find(x => x.active !== false && +x.rate > 0), known = { item: lib.name };
      d.lines = [{ id: 'lx1', item: known.item, qty: 1, unit: 'ls', rate: 0 }, { id: 'lx2', item: 'Zzqx parlor widget', qty: 1, unit: 'ls', rate: 0 }, { id: 'lx3', item: 'Stair runner', qty: 1, unit: 'ls', rate: 500 }];
      render(); await sleep(300);
      const priced = d.lines.find(l => l.id === 'lx1'), note = (document.querySelector('.doc-noprice') || {}).innerText || '';
      const keep = document.querySelector('tr[data-line="lx3"] input');
      document.querySelector('[data-rmline="lx2"]').click(); await sleep(150);
      const stable = keep === document.querySelector('tr[data-line="lx3"] input') && document.body.contains(keep);
      return { known: known.item, rate: priced.rate, from: priced.priceFrom || '', note, stable, ids: d.lines.map(l => l.id), sel: document.querySelectorAll('[data-lsel]').length };""")
    c.ok(r['rate'] > 0 and r['from'], f"pm: a line named like past work is priced from it ({r['known']!r} at {r['rate']} from {r['from']!r})")
    c.ok('Zzqx parlor widget' in r['note'] and 'No price found' in r['note'], f"pm: a line nothing matches says so, not a silent $0 ({r['note'][:120]!r})")
    c.ok(r['stable'] and r['ids'] == ['lx1', 'lx3'], f"pm: removing a line keeps the other lines' controls ({r})")
    c.ok(r['sel'] >= 2, f"pm: lines can be selected to remove several at once ({r['sel']})")
    r = await js(pg, """
      const cl = DB.clients.find(x => x.id === 'cl121'), sig = cl.estimates.find(e => e.status === 'converted') || cl.estimates[0];
      const n0 = cl.estimates.length; await docAction(cl, sig, 'dup'); await sleep(200);
      const m = document.getElementById('mbm'), title = m ? m.querySelector('h3').innerText : '';
      const boxes = m ? [...m.querySelectorAll('[data-dupl]')] : []; boxes[0] && (boxes[0].checked = true);
      m && m.querySelector('#mbm-ok').click(); await sleep(300);
      const n = cl.estimates[cl.estimates.length - 1];
      return { title, made: cl.estimates.length - n0, lines: n.lines.length, of: sig.lines.length };""")
    c.ok(r['title'].startswith('Copy Lines') and r['made'] == 1 and r['lines'] == 1, f"pm: Duplicate copies the lines picked, not the whole contract ({r})")
    r = await js(pg, """
      docOpen = null; view = 'home'; render(); await sleep(200);
      view = 'billing'; billTab = 'co'; render(); await sleep(250);
      const cl = DB.clients.find(x => x.id === 'cl121'), co = cl.changeOrders[0];
      docOpen = { kind: 'co', id: co.id }; render(); await sleep(250);
      const went = appBack(); await sleep(400);
      return { went, view, doc: docOpen, tab: billTab };""")
    c.ok(r['went'] and r['view'] == 'billing' and not r['doc'] and r['tab'] == 'co', f"pm: back from a change order returns to Billing › Change Orders, not Today ({r})")
    r = await js(pg, """
      docOpen = null; view = 'billing'; billTab = 'est'; render(); await sleep(250);
      const a = !!document.getElementById('bill-newest');
      view = 'clients'; clientOpen = 'cl121'; render(); await sleep(250);
      const cp = [...document.querySelectorAll('#v-clients .doc-jobacts button')].map(b => b.innerText.trim());
      const raise = (DB.field.raises || [])[0]; let fb = false;
      if (raise) { fAnswerRaise(raise); await sleep(200); fb = !!document.querySelector('#mbm [data-jobnew="co"]'); mbCloseModal(); }
      return { a, fb, raise: !!raise, cp };""")
    c.ok(r['a'], 'pm: Billing › Estimates has New Estimate')
    c.ok('New Estimate' in r['cp'], f"pm: the client's page has New Estimate ({r['cp']})")
    c.ok(r['fb'] or not r['raise'], f"pm: the field answer sheet offers New Change Order ({r})")
    c.ok(not errs, f'pm: no page errors {errs[:2]}')
    await b.close()

async def t_daily_log_day2(c, p):
    b, pg, errs = await fresh(p, 'u_angel', phone=True)
    r = await js(pg, """
      const fs = DB.field.subs.find(x => x.id === 'fs1'); fs.status = 'confirmed';
      setCurrent('p121'); view = 'flog'; render(); await sleep(250);
      const dr = DB.field.dlDraft['p121|' + today()]; dr.step = 6; dr.signed = true; render(); await sleep(200);
      document.querySelector('#dl-next').click(); await sleep(250);
      const t1 = (document.getElementById('toast') || {}).innerText || '', step1 = dr.step;
      const gaps = (document.querySelector('.dl-gaps') || {}).innerText || '';
      const wx = document.querySelector('.dl-gaps [data-dlwx="Clear"]'); wx && wx.click(); await sleep(150);
      const came = document.querySelector('.dl-gaps [data-dlsubq="0:1"]'); came && came.click(); await sleep(150);
      for (let k = 0; k < 4; k++) { const st = document.querySelector('.dl-gaps [data-dlstill$=":0"]'); if (!st) break; st.click(); await sleep(120); }
      const sg = document.querySelector('[data-dlsign]'); sg && !sg.checked && sg.click();
      DB.field.dlDraft['p121|' + today()].signed = true;
      document.querySelector('#dl-next').click(); await sleep(400);
      const l = dlLogs('p121').find(x => x.date === today());
      const card = (document.querySelector('.dl-card') || {}).innerText || '';
      return { t1, step1, gaps, filed: !!l, subs: l && l.subsOn.map(x => x.vendor), weather: l && l.weather, toast: (document.getElementById('toast') || {}).innerText || '', sent: /Sent/.test(card) };""")
    c.ok(r['step1'] == 6 and 'Not signed yet' in r['t1'] and 'weather' in r['t1'], f"log day 2: Sign and Send without weather stays on Sign Off and says why ({r['t1']!r}, step {r['step1']})")
    c.ok('Carlos Millwork was booked today' in r['gaps'], f"log day 2: a booked sub nobody ticked is asked about ({r['gaps'][:160]!r})")
    c.ok(r['filed'] and r['subs'] == ['Carlos Millwork'] and r['weather'] == 'Clear', f"log day 2: once answered it signs, with the sub and the weather ({r})")
    c.ok('Open' in r['toast'] and r['sent'], f"log day 2: the toast has Open and the log shows Sent ({r['toast']!r})")
    r = await js(pg, """
      view = 'ftoday'; render(); await sleep(250);
      const n = (document.querySelector('#ftoday-body .dl-missnote') || {}).innerText || '';
      view = 'flog'; render(); await sleep(200);
      const late = document.querySelector('[data-dllate]'); const date = late && late.dataset.dllate; late && late.click(); await sleep(150);
      const w = document.querySelector('#mbm [data-f="why"]'); w && (w.value = 'the app sent me back to Weather');
      document.querySelector('#mbm-ok') && document.querySelector('#mbm-ok').click(); await sleep(250);
      const head = (document.querySelector('.dl-card .hd') || {}).innerText || '';
      const dr = DB.field.dlDraft['p121|' + date]; if (dr) { dr.weather = 'Cloudy'; dr.step = 6; dr.signed = true; (dr.delays || []).forEach(x => x.carried && (x.still = false)); (dr.subsOn || []).forEach(x => x.touched = true); render(); await sleep(150);
        document.querySelector('#dl-next').click(); await sleep(400); }
      const l = dlLogs('p121').find(x => x.date === date);
      return { n, date, head, late: l && l.late, gaps: (document.querySelector('.dl-gaps') || {}).innerText || '' };""")
    c.ok('No daily log for' in r['n'], f"today: a working day with no log flags on the foreman's Today ({r['n'][:80]!r})")
    c.ok(r['head'].startswith('Late Log'), f"log: File Late Log opens that day's log ({r['head'][:60]!r})")
    c.ok(r['late'] and r['late'].get('why'), f"log: the late log is filed with its reason ({r['late']}, {r['gaps'][:120]!r})")
    await b.close()
    b, pg, errs2 = await fresh(p, 'u_alan', phone=True)
    r = await js(pg, """
      const rows = CATCH.find(x => x.name === 'dailyLogs').rows();
      view = 'home'; render(); await sleep(300);
      const sq = document.querySelector('.view.on [data-tdpulse="site"]');
      return { rows: rows.map(x => x.what), site: sq ? +sq.dataset.n : null, mine: PRED.siteQuestionsMine.rows().length,
               field: (DB.field.raises || []).filter(x => ['sent', 'seen'].includes(x.status) && DELEGATION.raise.who({ id: x.id }) === 'pm').length };""")
    c.ok(any('No daily log' in x for x in r['rows']), f"pm: a missing log flags on the PM's Home ({r['rows']})")
    c.ok(r['site'] == r['field'] and r['mine'] == r['field'], f"pm: Home's Site Questions counts the Field questions waiting on him ({r})")
    r = await js(pg, """
      const x = DB.field.raises.find(r => r.id === 'fr4'); x.escalated = true;
      return { who: DELEGATION.raise.who({ id: 'fr4' }), n: PRED.siteQuestionsMine.rows().length };""")
    c.ok(r['who'] == 'pm' and r['n'] >= 1, f"pm: an escalated question still waits on the PM it was sent to ({r})")
    c.ok(not errs and not errs2, f'log day 2: no page errors {(errs + errs2)[:2]}')
    await b.close()

# ------------------------------------------------------------------------------------------------ 8, 9, 10
async def t_statements_tasks_billing(c, p):
    b, pg, errs = await fresh(p, 'u_controller')
    r = await js(pg, """
      await gcDemoConnect(); await sleep(400);
      const rows = nyhRows().filter(x => x.pkind === 'statement' || x.kind === 'statement').map(x => x.title);
      const props = DB.comms.filter(x => x.owner === 'u_controller').flatMap(x => (x.proposals || []).filter(p => p.kind === 'statement' && p.acctId).map(p => p.summary));
      return { rows, props };""")
    c.ok(not any(('Amex' in x or 'Chase' in x) and 'statement' in x for x in r['rows']), f"controller: the imported Amex and Chase August statements are not offered again ({r['rows']})")
    c.ok(r['props'] and all('already here' in x for x in r['props']), f"controller: the mail reads already here ({r['props']})")
    await b.close()
    b, pg, errs2 = await fresh(p, 'u_sarah')
    r = await js(pg, """
      await gcDemoConnect(); await sleep(400);
      const cm = DB.comms.find(x => /public hearing September 8/.test(x.subject) && x.owner === 'u_sarah');
      const row = nyhRows().find(x => x.commId === cm.id); row && row.run(); await sleep(150);
      const t = (DB.projects.find(x => x.id === 'p45').actions || []).slice(-1)[0];
      return { verb: row && row.verb, due: t && t.due, notes: t && t.notes.slice(-90) };""")
    c.ok(r['verb'] == 'Make It a Task' and r['due'] and r['due'] < '2026-09-08' and r['due'] != '2026-09-10', f"designer: the task is due before the LPC hearing on 9/8, not a default 9/10 ({r})")
    c.ok(r['due'] == '2026-09-04', f"designer: the working day before the hearing skips Labor Day ({r['due']})")
    await b.close()
    b, pg, errs3 = await fresh(p, 'u_billing')
    r = await js(pg, """
      const c = DB.clients.find(x => x.id === 'cl121'), out = pgApply('p121'), inv = out && out.inv;
      const sv = c.sov.find(v => /Windows/.test(v.desc)), l = inv && inv.lines.find(x => x.sovId === sv.id); l && (l.pct = Math.max(+l.pct || 0, 10));
      const st = newDoc(c, 'invoice', { mode: 'items' }); st.title = 'Stored materials — windows'; st.lines = [{ id: 'lz', item: 'Windows — front & rear façade, stored on site', qty: 1, unit: 'ls', rate: 13970 }];
      view = 'billing'; clientOpen = c.id; docOpen = { kind: 'invoice', id: st.id }; render(); await sleep(300);
      const note = (document.querySelector('.doc-double') || {}).innerText || '';
      await docAction(c, st, 'send'); await sleep(150);
      return { note, inv: inv && inv.number, st: st.number, status: st.status, toast: (document.getElementById('toast') || {}).innerText || '' };""")
    c.ok('Possible double bill' in r['note'] and r['inv'] in r['note'], f"billing: the stored-materials invoice warns, naming the application ({r['note'][:200]!r})")
    c.ok(r['status'] == 'draft' and 'Not sent' in r['toast'], f"billing: sending it asks first ({r['status']}, {r['toast'][:120]!r})")
    c.ok(not errs and not errs2 and not errs3, f'8-10: no page errors {(errs + errs2 + errs3)[:2]}')
    await b.close()

# ------------------------------------------------------------------------------------------------ 11: Ask
async def t_ask_typos(c, p):
    b, pg, errs = await fresh(p, 'u_alan', phone=True)
    r = await js(pg, """
      const out = {};
      for (const q of ["Please don't send the paint sheet to the Kleins yet", 'has Tomas rebooked in the app', "what do the Kleins' owe", 'zorbify the qwerty frobs']) {
        const P = agParse(q), a = await paAsk(q);
        out[q] = { l: P.l, fixes: P.fixes.map(f => f.join('>')), head: a && a.headline, kind: a && a.kind };
      }
      return out;""")
    a = r["Please don't send the paint sheet to the Kleins yet"]
    c.ok('do not' in a['l'] and 'sheet' in a['l'] and not a['fixes'], f"ask: \"don't\" and \"sheet\" are kept, never \"done\" and \"sheen\" ({a['l']!r}, {a['fixes']})")
    c.ok(a['kind'] == 'notUnderstood' and 'instruction' in a['head'] and 'Nothing was done' in a['head'], f"ask: a request not to act is said back, not answered as another question ({a['head']!r})")
    b2 = r['has Tomas rebooked in the app']
    c.ok('rebooked' in b2['l'] and ' app' in b2['l'] and not b2['fixes'], f"ask: \"rebooked\" and \"app\" are kept ({b2['l']!r}, {b2['fixes']})")
    c.ok('kleins' in r["what do the Kleins' owe"]['l'], f"ask: \"Kleins'\" stays the Kleins ({r["what do the Kleins' owe"]['l']!r})")
    z = r['zorbify the qwerty frobs']
    c.ok('did not understand' in (z['head'] or '') and 'zorbify' in z['head'], f"ask: words it does not know are named ({z['head']!r})")
    c.ok(not errs, f'ask: no page errors {errs[:2]}')
    await b.close()

# ------------------------------------------------------------------------------------------------ 12, 13, 14
async def t_designer_and_bill(c, p):
    b, pg, errs = await fresh(p, 'u_sarah', phone=True)
    r = await js(pg, """
      await gcDemoConnect(); await sleep(400);
      view = 'sday'; render(); await sleep(350);
      const btn = [...document.querySelectorAll('[data-nsopen]')].find(x => /Send Revised Drawings/.test(x.closest('[data-nsowed]').innerText));
      btn && btn.click(); await sleep(250);
      const title = (document.querySelector('#mbm h3') || {}).innerText || '', v1 = view;
      document.querySelector('#mbm-ok') && document.querySelector('#mbm-ok').click(); await sleep(250);
      const toast1 = (document.getElementById('toast') || {}).innerText || '';
      const t = document.querySelector('button.gl[data-tl="hrs"]'), oldest = stOldestUnlogged();
      t && t.click(); await sleep(250);
      const sheet = (document.querySelector('#mbm h3') || {}).innerText || '';
      const h = document.querySelector('#mbm [data-f="h"]'); h && (h.value = '5'); document.querySelector('#mbm-ok') && document.querySelector('#mbm-ok').click(); await sleep(250);
      return { btn: !!btn, title, v1, toast1, oldest, sheet, logged: DB.time.some(x => x.date === oldest && x.source === 'day sheet') };""")
    c.ok(r['btn'] and r['v1'] == 'sday' and r['title'] == 'Send Revised Drawings', f"designer: her My Day step opens where she can finish it, not Meetings ({r['v1']}, {r['title']!r})")
    c.ok('On your list' in r['toast1'], f"designer: confirming it puts it on her list ({r['toast1']!r})")
    c.ok(r['oldest'] and r['oldest'][5:].replace('-', '/').lstrip('0') in '' or ('Hours for' in r['sheet']), f"designer: Hours Not Logged opens the day sheet for the oldest unlogged day ({r['sheet']!r}, {r['oldest']})")
    c.ok(r['logged'], f"designer: the day sheet logs the hours on that day ({r['oldest']})")
    await b.close()
    b, pg, errs2 = await fresh(p, 'u_controller')
    r = await js(pg, """
      const b = DB.bills.find(x => x.status === 'submitted');
      openBill(b.id); await sleep(300);
      const d = document.getElementById('drawer'), ctl = (d.querySelector('.note.warn') || {}).innerText || '';
      d.querySelector('[data-billhold="hold"]').click(); await sleep(200);
      document.querySelector('#mbm [data-f="why"]').value = 'waiting on the signed delivery ticket'; document.querySelector('#mbm-ok').click(); await sleep(300);
      const toast1 = (document.getElementById('toast') || {}).innerText || '', p = DB.projects.find(x => x.id === b.projectId), t1 = (p.actions || []).slice(-1)[0];
      billAction(b, 'approve'); const st = b.status;
      const b2 = DB.bills.filter(x => x.status === 'submitted' || x.status === 'pm-approved').find(x => x.id !== b.id);
      openBill(b2.id); await sleep(300);
      document.querySelector('#drawer [data-billhold="back"]').click(); await sleep(200);
      document.querySelector('#mbm [data-f="why"]').value = 'invoice for 10 units, the PO is 9'; document.querySelector('#mbm-ok').click(); await sleep(300);
      const toast2 = (document.getElementById('toast') || {}).innerText || '';
      return { ctl, toast1, task: t1 && [t1.title, t1.assignee], st, b2: b2.status, toast2 };""")
    c.ok('W-9' in r['ctl'] and 'COI' in r['ctl'], f"bill: the COI expiry sits in Controls next to the W-9 ({r['ctl'][-120:]!r})")
    c.ok('held' in r['toast1'] and r['task'] and 'waiting on the signed delivery ticket' in r['task'][0], f"bill: Hold takes a reason, makes a task for the person named and toasts ({r['task']}, {r['toast1'][:80]!r})")
    c.ok(r['st'] == 'submitted', f"bill: a held bill is not approved ({r['st']})")
    c.ok(r['b2'] == 'draft' and 'sent back' in r['toast2'], f"bill: Send Back returns it to draft with the reason and a task ({r['b2']}, {r['toast2'][:80]!r})")
    c.ok(not errs and not errs2, f'12-14: no page errors {(errs + errs2)[:2]}')
    await b.close()

async def t_co_from_contract(c, p):
    b, pg, errs = await fresh(p, 'u_alan', phone=True)
    r = await js(pg, """
      setCurrent('p121'); view = 'dash'; render(); await sleep(250);
      newChangeOrderDialog({ clientId: 'cl121', projectId: 'p121' }); await sleep(250);
      const m = document.getElementById('mbm'); m.querySelector('[data-f="title"]').value = 'Sister the notched joist';
      const cb = [...m.querySelectorAll('[data-coline]')].find(i => /Framing/.test(i.closest('label').innerText)); cb && (cb.checked = true);
      m.querySelector('#mbm-ok').click(); await sleep(400);
      const cl = DB.clients.find(x => x.id === 'cl121'), d = cl.changeOrders[cl.changeOrders.length - 1], l = d.lines[0];
      const pr = DB.projects.find(x => x.id === 'p121'), done = pr.tasks.find(t => t.status === 'done');
      const co2 = { projectId: 'p121', scope: done ? { kind: 'task', id: done.id } : null };
      l.rate = 41000; await docAction(cl, d, 'send'); await sleep(150);
      const toast1 = (document.getElementById('toast') || {}).innerText || '', st = d.status;
      return { line: [l.item, l.qty, l.refAmount, l.noPrice], total0: 0, toast1, st, to: crDocEmail(cl, d).to.email,
               doneTask: done ? thCoTaskId(co2, pr) : 'n/a' };""")
    c.ok(r['line'][1] == 1 and r['line'][3] and r['line'][2] == 41000, f"pm: a contract line arrives at no price with its $41,000 kept as the reference, not the rate ({r['line']})")
    c.ok('Check before it goes' in r['toast1'] and r['st'] == 'draft', f"pm: a CO at 100% of the line it changes asks before Send ({r['toast1'][:120]!r}, {r['st']})")
    c.ok('sarah.klein' in r['to'] and 'david.klein' in r['to'], f"pm: the CO goes to every signer, Sarah and David ({r['to']})")
    c.ok(r['doneTask'] in ('', 'n/a'), f"pm: Extends Task is never a finished task by default ({r['doneTask']!r})")
    r = await js(pg, """view = 'field'; render(); await sleep(300); return document.querySelectorAll('#f-office [data-jobnew="co"]').length;""")
    c.ok(r > 0, f"pm: each question from the site in Field offers Write the Change Order ({r})")
    c.ok(not errs, f'co: no page errors {errs[:2]}')
    await b.close()

TESTS = [t_daily_log, t_daily_log_day2, t_documents, t_controller_pos, t_payment_check, t_own_mail_client, t_bought_from_mail, t_request_quirks, t_statements_tasks_billing, t_ask_typos, t_designer_and_bill, t_co_from_contract]

async def main():
    c = Checks()
    only = sys.argv[1:] 
    async with async_playwright() as p:
        for t in TESTS:
            if only and t.__name__ not in only: continue
            print('--', t.__name__)
            try: await t(c, p)
            except Exception as e: c.ok(False, f'{t.__name__} raised {e!r}'[:400])
    sys.exit(c.done())

if __name__ == '__main__':
    asyncio.run(main())
