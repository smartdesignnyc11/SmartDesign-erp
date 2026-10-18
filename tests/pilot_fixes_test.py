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

TESTS = [t_daily_log, t_controller_pos, t_payment_check, t_own_mail_client, t_bought_from_mail, t_request_quirks]

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
