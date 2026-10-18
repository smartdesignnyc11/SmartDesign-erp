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

TESTS = [t_daily_log]

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
