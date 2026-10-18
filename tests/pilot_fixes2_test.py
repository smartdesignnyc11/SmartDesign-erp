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

EXTRA = []

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
