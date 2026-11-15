"""punch_safe: no punch can overpay (the crew and foreman expert's phone walk of the live build, 11-15, and Alan's
decisions the same day: automatic clock-in and clock-out stay, "based on geo location"; the window is 7am to 5pm; "after
8 hours and 15 minutes it should send them a notification to ask if they are still working").
Before this fix: he left at 4:30 PM and opened the app at home at 7:05 PM and was clocked out at 7:05 (11.55 h); he never
opened it and the punch ran 33.0 h, was approved with one tap and payroll paid about ,020 too much; a weak reading
never clocked him out; the Daily Log sent "Alberto 9 h" for a voided punch; the foreman approved his own 8 h.
Each check is the person's own steps at 390x844 with touch, on invented data.

  limit       The switch says what the app can and cannot see (English, Spanish).
  home        Last reading on site 4:30 PM, next heard at home 7:05 PM: ends at 4:30, held, he confirms (who, when,
              before and after).
  day33       Next heard the next morning on site: yesterday's punch ends at its last reading on site, held; nothing runs
              past 16 h; an automatic punch open from a past day is closed and held when anyone looks.
  weak        30 minutes of readings too weak to act on: closed at the last good reading on site, held; the switch says
              location is not reliable.
  window      No automatic punch before 7:00; on site from before and still on site, it starts at 7:00 and says so; a
              50-minute gap starts it at the reading; a Saturday says clock in by hand; the switch says when it is not
              watching.
  autoend     At 5:00 PM nothing clocks him out by the clock: he is asked, and silence closes at his last reading on site,
              held; 8 h 15 the same.
  autoswitch  Changing jobs at lunch: the first punch ends when he was seen leaving it.
  autosent    The automatic path asks Today Is Already Sent on the Clock page until answered, with Those Hours Aren't Mine.
  hand        A hand Clock In far from the site is taken and flagged with the distance; refused location is flagged
              "Location not confirmed"; before 7:00 is flagged outside the window.
  still       8 h 15 on a hand punch: asked once, Still Working recorded (who, when) and shown to the foreman, asked again
              an hour later, 30 minutes of silence closes and holds it: 0 h, not approvable, not in payroll.
  workday     The owner changes the window in Company Settings; the switch, the flag and the end question follow.
  nextday     A hand punch open on a later day is closed and held; he says when he left.
  routes      No route approves or pays a held, open, voided or over-16-hour punch (the one door for every role, the PM's
              drawer, Approve All Shown, the foreman's row, Approve N Clean, Fix's Save & Approve, the pay run built from
              time and a run typed by hand, even with the status forced to approved).
  void        This Week counts overlaps once; the voided 9.1 h punch is out of the Daily Log (4.25 h) and every total;
              Pick One says how each punch was made and where it stands.
  own, unsent, notmine, spanish   items 4, 5, 6 and the Spanish of the question and the hold.

Readings are fed to the app's own location function (tkGeoTick) with a position and a time; the time of day is set
with Playwright's clock. Background location with the app closed, and a notification to a closed phone, are not
tested: a web app has neither.
Run: python3 punch_safe_test.py [section ...]   (SD_DIST names another build, e.g. the one before the fix)"""
import asyncio, datetime, os, sys
from harness import async_playwright, open_app, sign_in, go, Checks, ROOT, URL

SHOTS = os.environ.get('T1_SHOTS') or os.path.join(ROOT, 'review', 'punch_safe')
os.makedirs(SHOTS, exist_ok=True)
CLOSE = "() => { try { mbCloseModal(); } catch (e) {} document.querySelectorAll('#mbm').forEach(e => e.remove()); }"
TOAST = "() => (document.getElementById('toast') || {}).innerText || ''"
E = "id => { const t = DB.time.find(x => x.id === id); return t ? { id: t.id, date: t.date, inn: t.in, out: t.out, st: t.status, held: timeHeld(t), h: hoursOf(t), still: t.still || null, hold: t.hold || null, pay: timePayBlock(t), flags: timeFlags(t), payrollId: t.payrollId || '', approveWhy: t.approveWhy || '' } : null; }"
# a hand punch for Alberto (em2), nothing else of his from today on
PUNCH = """([id, inn, out]) => { const e = DB.employees.find(x => x.id === 'em2'); DB.time = DB.time.filter(t => !(t.empId === 'em2' && t.date >= today()) && t.id !== id);
  DB.time.push({ id, empId: e.id, date: inn.slice(0, 10), in: inn, out: out || '', breakMin: 0, projectId: 'p121', code: '', notes: '', status: 'open', approvedBy: '', geoIn: { lat: 0, lng: 0, acc: 10, dist: 5 }, geoOut: null, source: 'phone', work: [] }); save(); render(); return id; }"""


async def shot(pg, name):
    try:
        await pg.screenshot(path=os.path.join(SHOTS, name + '.png'))
    except Exception:
        pass


async def pin(pg, hm):
    """the app's time of day: the pinned demo day maps the wall clock onto 07:30-17:30"""
    h, m = map(int, hm.split(':')); t = h * 3600 + m * 60
    assert 27000 <= t < 63000, hm
    wall = int((t - 27000) * 2.4) + 1
    await pg.clock.set_fixed_time(datetime.datetime(2026, 11, 15, 5, 0, 0, tzinfo=datetime.timezone.utc) + datetime.timedelta(seconds=wall))
    await pg.wait_for_timeout(60)
    await pg.evaluate("() => render()")
    await pg.wait_for_timeout(80)


async def tap(pg, sel, text=None):
    h = await pg.evaluate_handle("([s, t]) => [...document.querySelectorAll(s)].find(e => e.getClientRects().length && (!t || (e.innerText || '').includes(t))) || null", [sel, text])
    el = h.as_element()
    if not el: return False
    await el.scroll_into_view_if_needed()
    await el.tap()
    await pg.wait_for_timeout(350)
    return True


async def text(pg, sel):
    return await pg.evaluate("s => [...document.querySelectorAll(s)].filter(e => e.getClientRects().length).map(e => e.innerText).join('\\n')", sel)


async def side(pg):
    return await pg.evaluate("() => document.documentElement.scrollWidth - innerWidth")


MINE = "() => DB.time.filter(t => t.empId === myEmp().id && t.date >= '2026-09-03').map(t => t.id)"
SITE = "(() => { const g = DB.projects.find(p => p.id === 'p121').project.geo; return { lat: g.lat, lng: g.lng, acc: 12 }; })()"
FAR = "(() => { const g = DB.projects.find(p => p.id === 'p121').project.geo; return { lat: g.lat + 0.03, lng: g.lng, acc: 12 }; })()"
WEAK = "(() => { const g = DB.projects.find(p => p.id === 'p121').project.geo; return { lat: g.lat + 0.03, lng: g.lng, acc: 400 }; })()"
L206 = "(() => { const g = DB.projects.find(p => p.id === 'p206').project.geo; return { lat: g.lat, lng: g.lng, acc: 12 }; })()"
# clear Alberto's punches from 9/3 on, reset the in-memory reading state, turn automatic clock-in on for him
CLEAR = """() => { const e = myEmp(); DB.time = DB.time.filter(t => !(t.empId === e.id && t.date >= '2026-09-03'));
  try { Object.assign(tkGeo, { outSince: '', outFor: '', asked: '', again: '', weak: false, sentAsk: null, early: null }); } catch (x) {}
  if (!(currentUser().geoAck && currentUser().geoAck.at && !currentUser().geoAck.off)) tkGeoAgree(currentUser()); save(); render(); }"""


async def tick(pg, pos, at):
    r = await pg.evaluate(f"() => tkGeoTick({pos}, {at!r})")
    await pg.wait_for_timeout(120)
    return r


async def s_limit(pg, c):
    """the switch says what the app can and cannot see, in English and Spanish"""
    await pin(pg, '07:40')
    for lang, want in (('en', 'Automatic clock-in works while this app is open. With the app closed it cannot see you arrive or leave: clock in by hand, and confirm when you left.'),
                       ('es', 'La entrada automática funciona mientras esta app está abierta. Con la app cerrada no puede ver cuándo llegas ni cuándo te vas')):
        await pg.evaluate("l => { DB.users.find(u => u.id === 'u_alberto').lang = l; save(); }", lang)
        await sign_in(pg, 'u_alberto'); await go(pg, 'time')
        await pg.evaluate(CLEAR)
        await go(pg, 'time')
        t = await text(pg, '.view.on .tkg-card')
        await shot(pg, f'limit_{lang}')
        c.ok(want in t, f'limit: the switch says what the app can and cannot see ({lang}: {t[:200]!r})')
    await pg.evaluate("() => { DB.users.find(u => u.id === 'u_alberto').lang = 'en'; save(); }")


async def s_home(pg, c):
    """he left at 4:30 PM (last reading on site) and the app next hears him at home at 7:05 PM"""
    await pin(pg, '07:40')
    await sign_in(pg, 'u_alberto'); await go(pg, 'time')
    await pg.evaluate(CLEAR)
    r = await tick(pg, SITE, '2026-09-03T07:02:00')
    pid = r.get('id')
    await tick(pg, SITE, '2026-09-03T16:30:00')
    r = await tick(pg, FAR, '2026-09-03T19:05:00')
    e = await pg.evaluate(E, pid)
    c.ok(r.get('did') == 'held' and e and e['out'] == '2026-09-03T16:30:00', f"home: opened at home at 7:05 PM, the punch ends at 4:30 PM, his last reading on site, not 7:05 ({r}, {e and e['out']})")
    c.ok(e and e['held'] and e['h'] == 0 and e['pay'], f"home: the punch is held: it counts 0 h and cannot be paid until he confirms ({e and e['h']}, {e and e['pay']})")
    t = await pg.evaluate(TOAST)
    c.ok('Clocked out automatically at 4:30 PM, your last reading on site. Confirm when you left.' in t, f'home: he is told, in those words ({t[:120]!r})')
    await go(pg, 'time')
    card = await text(pg, '.view.on [data-tkhold]')
    await shot(pg, 'home_held_card')
    c.ok('Clocked out automatically at 4:30 PM, your last reading on site. Confirm when you left.' in card, f'home: his Clock page asks until he answers ({card[:120]!r})')
    c.ok(await side(pg) <= 0, 'home: the Clock page does not scroll sideways')
    ok = await tap(pg, '.view.on [data-tkhok]')
    m = await pg.evaluate("() => (document.querySelector('#mbm') || {}).innerText || ''")
    c.ok(ok and 'When Did You Leave' in m, f'home: Confirm When I Left opens one sheet ({m[:80]!r})')
    await tap(pg, '#mbm #mbm-ok')
    e = await pg.evaluate(E, pid)
    t = await pg.evaluate(TOAST)
    c.ok(e and not e['held'] and e['out'] == '2026-09-03T16:30:00' and abs(e['h'] - 8.97) < 0.02, f"home: confirmed, the day is 7:02 AM to 4:30 PM, 8.97 h with the break, not 11.55 h ({e and e['h']})")
    hd = (e or {}).get('hold') or {}
    c.ok(hd.get('doneBy') == 'Alberto' and hd.get('doneAt') and hd.get('before') == '2026-09-03T16:30:00' and hd.get('after') == '2026-09-03T16:30:00', f'home: the confirmation records who, when, the time before and after ({hd})')
    c.ok('7:02 AM to 4:30 PM' in t and 'Open' in t, f'home: the confirmation toasts what happened, with Open ({t[:100]!r})')


async def s_day33(pg, c):
    """he never opens the app after 7:02 AM; the next reading is the next morning on site (the 33.0 h punch)"""
    await pin(pg, '07:40')
    await sign_in(pg, 'u_alberto'); await go(pg, 'time')
    await pg.evaluate(CLEAR)
    r = await tick(pg, SITE, '2026-09-03T07:02:00')
    pid = r.get('id')
    r2 = await tick(pg, SITE, '2026-09-04T07:05:00')
    e = await pg.evaluate(E, pid)
    c.ok(e and e['held'] and e['out'] == '2026-09-03T07:02:00' and r2.get('held') == pid, f'day33: the 9/3 punch is closed at its last reading on site and held when he next reads on site on 9/4 ({r2}, {e and e["out"]})')
    c.ok(r2.get('did') == 'in' and r2.get('id') != pid, f'day33: 9/4 starts its own punch ({r2})')
    long = await pg.evaluate("() => DB.time.filter(t => t.out && t.in && (new Date(t.out) - new Date(t.in)) / 36e5 > 16).map(t => t.id)")
    c.ok(not long, f'day33: no punch runs past 16 hours ({long})')
    # an automatic punch still open from a past day, found by whoever looks
    await pg.evaluate("""() => { DB.time = DB.time.filter(x => x.id !== 'te_sweep'); DB.time.push({ id: 'te_sweep', empId: 'em4', date: '2026-09-02', in: '2026-09-02T07:10:00', out: '', breakMin: 0, projectId: 'p121', code: '', notes: '', status: 'open', approvedBy: '', geoIn: { lat: 0, lng: 0, acc: 10, dist: 5 }, geoOut: null, source: 'geo', auto: { how: 'automatic, by location' }, lastOnSite: '2026-09-02T15:55:00', work: [] }); save(); }""")
    await sign_in(pg, 'u_angel'); await go(pg, 'fcrew')
    e = await pg.evaluate(E, 'te_sweep')
    c.ok(e and e['held'] and e['out'] == '2026-09-02T15:55:00', f'day33: an automatic punch open since 9/2 is closed at its last reading on site (3:55 PM) and held when the foreman looks ({e and e["out"]})')
    await pg.evaluate("() => { DB.time = DB.time.filter(x => x.id !== 'te_sweep'); save(); }")


async def s_weak(pg, c):
    await pin(pg, '07:40')
    await sign_in(pg, 'u_alberto'); await go(pg, 'time')
    await pg.evaluate(CLEAR)
    r = await tick(pg, SITE, '2026-09-03T07:31:00')
    pid = r.get('id')
    await tick(pg, SITE, '2026-09-03T11:50:00')
    r1 = await tick(pg, WEAK, '2026-09-03T12:00:00')
    await go(pg, 'time')
    card = await text(pg, '.view.on .tkg-card')
    c.ok('not reliable right now' in card and 'clock out by hand' in card, f'weak: the Clock page says location is not reliable and to clock out by hand ({card[-200:]!r})')
    r2 = await tick(pg, WEAK, '2026-09-03T12:31:00')
    e = await pg.evaluate(E, pid)
    c.ok(r1.get('did') != 'held' and r2.get('did') == 'held' and e['held'] and e['out'] == '2026-09-03T11:50:00', f'weak: after 30 minutes of weak readings the punch ends at the last good reading on site, held ({r1}, {r2}, {e["out"]})')
    t = await pg.evaluate(TOAST)
    c.ok('Confirm when you left' in t, f'weak: he is asked ({t[:100]!r})')


async def s_window(pg, c):
    """7:00 AM to 5:00 PM, Monday to Friday: no automatic punch before 7:00; on site from before, it starts at 7:00 on a
    current reading; a Saturday says to clock in by hand"""
    await pin(pg, '07:40')
    await sign_in(pg, 'u_alberto'); await go(pg, 'time')
    await pg.evaluate(CLEAR)
    r = await tick(pg, SITE, '2026-09-03T06:40:00')
    t = await pg.evaluate(TOAST)
    n = await pg.evaluate(MINE)
    c.ok(r.get('did') == 'none' and not n and 'before automatic clock-in starts at 7:00 AM' in t and 'Clock in by hand for time before 7' in t, f'window: on site at 6:40 nothing punches, and he is told to clock in by hand for the time before 7 ({r}, {t[:120]!r})')
    await tick(pg, SITE, '2026-09-03T06:55:00')
    r = await tick(pg, SITE, '2026-09-03T07:05:00')
    e = await pg.evaluate(E, r.get('id'))
    t = await pg.evaluate(TOAST)
    c.ok(r.get('did') == 'in' and e['inn'] == '2026-09-03T07:00:00', f'window: on site at 6:40 and still on site at 7:05, the punch is from 7:00 ({r}, {e and e["inn"]})')
    c.ok('Clocked in at 7:00 AM, when automatic clock-in starts. You arrived earlier: clock in by hand for time before 7' in t, f'window: and says so ({t[:140]!r})')
    await pg.evaluate(CLEAR)
    await tick(pg, SITE, '2026-09-03T06:40:00')
    r = await tick(pg, SITE, '2026-09-03T07:30:00')
    e = await pg.evaluate(E, r.get('id'))
    c.ok(r.get('did') == 'in' and e['inn'] == '2026-09-03T07:30:00', f'window: with no reading for 50 minutes the window opening does not start the punch: it starts at the 7:30 reading ({e and e["inn"]})')
    await pg.evaluate(CLEAR)
    r = await tick(pg, SITE, '2026-09-05T08:00:00')
    t = await pg.evaluate(TOAST)
    c.ok(r.get('did') == 'none' and 'Automatic clock-in runs 7:00 AM to 5:00 PM, Monday to Friday. Clock in by hand now.' in t, f'window: a Saturday arrival says to clock in by hand ({r}, {t[:120]!r})')
    sw = await pg.evaluate("() => { const keep = DB.company.autoClock; DB.company.autoClock = { days: [6], start: '07:00', end: '17:00' }; render(); const x = (document.querySelector('.view.on .tkg-card') || {}).innerText || ''; keep ? (DB.company.autoClock = keep) : delete DB.company.autoClock; render(); return x; }")
    c.ok('not watching now' in sw and 'clock in by hand' in sw, f'window: outside its days the switch says it is not watching ({sw[-220:]!r})')


async def s_autoend(pg, c):
    """5:00 PM asks, it does not clock out; silence closes at his last reading on site. 8 h 15 the same."""
    await pin(pg, '07:40')
    await sign_in(pg, 'u_alberto'); await go(pg, 'time')
    await pg.evaluate(CLEAR)
    r = await tick(pg, SITE, '2026-09-03T12:00:00')
    pid = r.get('id')
    await tick(pg, SITE, '2026-09-03T16:40:00')
    await pin(pg, '17:02')
    await go(pg, 'time')
    e = await pg.evaluate(E, pid)
    card = await text(pg, '.view.on [data-tkstill]')
    c.ok(not e['out'] and 'It is 5:00 PM, when automatic clock-in stops. Are you still working?' in card, f'autoend: at 5:00 PM nothing clocks him out; he is asked ({e["out"]!r}, {card[:100]!r})')
    await pg.evaluate("() => tkStillCheck('2026-09-03T17:33:00')")
    e = await pg.evaluate(E, pid)
    c.ok(e['held'] and e['out'] == '2026-09-03T16:40:00' and e['h'] == 0, f'autoend: no answer in 30 minutes closes it at his last reading on site (4:40 PM), held ({e["out"]}, {e["held"]})')
    # 8 h 15 on an automatic punch: silence closes at the last reading on site, not at the mark
    await pin(pg, '07:40')
    await pg.evaluate(CLEAR)
    r = await tick(pg, SITE, '2026-09-03T07:00:00')
    pid = r.get('id')
    await tick(pg, SITE, '2026-09-03T14:50:00')
    await pin(pg, '15:16')
    e = await pg.evaluate(E, pid)
    c.ok((e['still'] or {}).get('askedAt'), f'autoend: at 8 h 15 the automatic punch is asked ({e["still"]})')
    await pg.evaluate("() => tkStillCheck('2026-09-03T15:47:00')")
    e = await pg.evaluate(E, pid)
    c.ok(e['held'] and e['out'] == '2026-09-03T14:50:00', f'autoend: silence closes it at his last reading on site (2:50 PM), held ({e["out"]})')


async def s_autoswitch(pg, c):
    """changing jobs at lunch: the first job's punch ends when he was seen leaving it"""
    await pin(pg, '07:40')
    await sign_in(pg, 'u_alberto'); await go(pg, 'time')
    await pg.evaluate(CLEAR)
    await pg.evaluate("() => { const g = DB.projects.find(p => p.id === 'p121').project.geo; DB.projects.find(p => p.id === 'p206').project.geo = { lat: g.lat + 0.05, lng: g.lng, radius: 250 }; save(); }")
    r = await tick(pg, SITE, '2026-09-03T07:31:00')
    first = r.get('id')
    await tick(pg, SITE, '2026-09-03T11:55:00')
    await tick(pg, FAR, '2026-09-03T12:00:00')
    r = await tick(pg, L206, '2026-09-03T13:10:00')
    e = await pg.evaluate(E, first)
    c.ok(r.get('did') == 'switch' and e['out'] == '2026-09-03T12:00:00' and abs(e['h'] - 4.48) < 0.02, f"autoswitch: the first job's punch ends when he was seen leaving it (12:00), not on arrival at 206 Lenox (13:10): 4.48 h, not 5.65 ({r}, {e['out']}, {e['h']})")
    await pg.evaluate("() => { delete DB.projects.find(p => p.id === 'p206').project.geo; save(); }")


async def s_autosent(pg, c):
    """the automatic path asks Today Is Already Sent on the Clock page until answered, with the third answer"""
    await pin(pg, '07:40')
    await sign_in(pg, 'u_alberto'); await go(pg, 'time')
    await pg.evaluate("() => { const e = myEmp(); DB.time = DB.time.filter(t => !(t.empId === e.id && t.date === '2026-09-03' && t.id !== 'te8')); const t = DB.time.find(t => t.id === 'te8'); t.status = 'submitted'; delete t.notMine; try { Object.assign(tkGeo, { asked: '', again: '', sentAsk: null }); } catch (x) {} if (!(currentUser().geoAck && currentUser().geoAck.at && !currentUser().geoAck.off)) tkGeoAgree(currentUser()); save(); render(); }")
    r = await tick(pg, SITE, '2026-09-03T07:40:00')
    await go(pg, 'time')
    card = await text(pg, '.view.on [data-tkhsent]')
    await shot(pg, 'autosent_ask')
    c.ok(r.get('did') == 'asked' and "Those Hours Aren't Mine" in card and 'Start Another Shift' in card, f'autosent: the automatic path asks on the Clock page, with three answers ({r}, {card[:160]!r})')
    await go(pg, 'time')
    c.ok(bool(await text(pg, '.view.on [data-tkhsent]')), 'autosent: the question stays on the Clock page until answered')
    await tap(pg, '.view.on [data-tkhsa=notmine]')
    r = await pg.evaluate("() => ({ open: DB.time.filter(t => t.empId === myEmp().id && !t.out).length, flag: !!(DB.time.find(t => t.id === 'te8').notMine), block: timeApproveBlock(DB.time.find(t => t.id === 'te8'), 'Angel') })")
    c.ok(r['open'] == 1 and r['flag'] and 'not his' in r['block'], f'autosent: he is clocked in, the earlier punch is flagged and refused until the foreman checks it ({r})')


async def s_hand(pg, c):
    await pin(pg, '08:10')
    await sign_in(pg, 'u_alberto'); await go(pg, 'time')
    await pg.evaluate("() => { DB.time = DB.time.filter(t => !(t.empId === 'em2' && t.date === today())); const g = DB.projects.find(p => p.id === 'p121').project.geo; window.getGeo = async () => ({ lat: g.lat + 0.05, lng: g.lng, acc: 15 }); setCurrent('p121'); save(); render(); }")
    await tap(pg, '#clock-in')
    await pg.wait_for_timeout(600)
    # far from every site the clock-in sheet asks which job; he picks 121 State and clocks in
    await pg.evaluate("() => { const s = document.querySelector('#mbm select'); if (s) { const o = [...s.options].find(o => /121 State/.test(o.text)); o && (s.value = o.value); s.dispatchEvent(new Event('change', { bubbles: true })); } }")
    await tap(pg, '#mbm #mbm-ok')
    await pg.wait_for_timeout(600)
    await pg.evaluate(CLOSE)
    r = await pg.evaluate("() => { const t = DB.time.find(x => x.empId === 'em2' && x.date === today()); return t ? { id: t.id, flags: timeFlags(t), out: t.out } : null; }")
    c.ok(r and not r['out'] and any('from the site' in f for f in r['flags']), f'hand: a Clock In 5 km from the site is taken and flagged with the distance ({r})')
    await pg.evaluate("() => { DB.time = DB.time.filter(t => !(t.empId === 'em2' && t.date === today())); window.getGeo = async () => null; save(); render(); }")
    await tap(pg, '#clock-in')
    await pg.wait_for_timeout(600)
    await pg.evaluate(CLOSE)
    r = await pg.evaluate("() => { const t = DB.time.find(x => x.empId === 'em2' && x.date === today()); return t ? { flags: timeFlags(t), out: t.out } : null; }")
    c.ok(r and 'Location not confirmed at clock-in' in r['flags'], f'hand: with the location refused it is taken and flagged "Location not confirmed" ({r})')
    await pg.evaluate(PUNCH, ['te_early', '2026-09-03T06:40:00', '2026-09-03T15:00:00'])
    e = await pg.evaluate(E, 'te_early')
    c.ok(any('outside the work day' in f for f in e['flags']), f"hand: a clock-in at 6:40 AM is taken and flagged outside the work day ({e['flags']})")
    await pg.evaluate("() => { tkGeoAgree(currentUser()); }")
    await go(pg, 'time')
    t = await text(pg, '.view.on .tkg-card')
    c.ok('Automatic clock-in runs 7:00 AM to 5:00 PM, Monday to Friday.' in t, f'hand: the Clock page says the window ({t[:160]!r})')


async def s_still(pg, c):
    await pin(pg, '08:00')
    await sign_in(pg, 'u_alberto'); await go(pg, 'time')
    await pg.evaluate(PUNCH, ['te_still', '2026-09-03T07:00:00', ''])
    await pin(pg, '15:10')
    e = await pg.evaluate(E, 'te_still')
    c.ok(not (e['still'] or {}).get('askedAt'), f'still: at 8 h 10 min nothing is asked ({e["still"]})')
    await pin(pg, '15:16')
    await go(pg, 'time')
    card = await text(pg, '.view.on [data-tkstill]')
    await shot(pg, 'still_question')
    e = await pg.evaluate(E, 'te_still')
    c.ok('Are you still working?' in card and 'You have been clocked in 8 h' in card and (e['still'] or {}).get('n') == 1, f'still: at 8 h 15 the Clock page asks, once ({card[:100]!r}, {e["still"]})')
    blue = await pg.evaluate("() => { const b = document.querySelector('.view.on [data-tksa=yes]'); return b ? [b.classList.contains('primary'), Math.round(b.getBoundingClientRect().height)] : null; }")
    c.ok(blue and blue[0] and blue[1] >= 44, f'still: Still Working is the blue 44px button ({blue})')
    await pin(pg, '15:20')
    e = await pg.evaluate(E, 'te_still')
    c.ok((e['still'] or {}).get('n') == 1, f'still: asked once, not again four minutes later ({e["still"]})')
    await go(pg, 'time')
    await tap(pg, '.view.on [data-tksa=yes]')
    e = await pg.evaluate(E, 'te_still')
    a = (e['still'] or {}).get('answers') or []
    c.ok(a and a[-1]['by'] == 'Alberto' and a[-1]['at'].startswith('2026-09-03T15:2') and not e['still']['askedAt'], f'still: Still Working is recorded with who and when ({e["still"]})')
    t = await pg.evaluate(TOAST)
    c.ok('Still working, recorded at' in t and 'Open' in t, f'still: it toasts what was recorded ({t[:90]!r})')
    await sign_in(pg, 'u_angel'); await go(pg, 'fcrew')
    t = await text(pg, '#fcrew-body [data-fstill]')
    c.ok('still working' in t, f"still: the foreman's crew list shows who is past 8 h 15 and what they said ({t!r})")
    await sign_in(pg, 'u_alberto')
    await pin(pg, '16:00')
    e = await pg.evaluate(E, 'te_still')
    c.ok(not e['still']['askedAt'], 'still: not asked again inside the hour')
    await pin(pg, '16:22')
    e = await pg.evaluate(E, 'te_still')
    c.ok(e['still']['askedAt'] and e['still']['n'] == 2, f'still: asked again an hour after Still Working ({e["still"]})')
    await pin(pg, '16:55')
    e = await pg.evaluate(E, 'te_still')
    last = a[-1]['at'] if a else ''
    c.ok(e['held'] and e['out'] == last and e['h'] == 0 and e['pay'], f'still: 30 minutes of silence closes it at his last Still Working ({last}) and holds it: 0 h, not payable ({e})')
    r = await pg.evaluate("() => { const t = DB.time.find(x => x.id === 'te_still'); const no = timeApprove(t, 'Angel', true); t.status = 'approved'; const run = payrollFromTime({ quiet: true }); return { no, inRun: !!run && (run.timeIds || []).includes('te_still') }; }")
    c.ok(r['no'] and not r['inRun'], f'still: the held punch is not approvable and not in payroll, even forced to approved ({r})')
    await pg.evaluate("() => { const t = DB.time.find(x => x.id === 'te_still'); t.status = 'open'; delete t.payrollId; save(); }")
    # the 8 h 15 mark, when he never answered
    await pin(pg, '08:00')
    await pg.evaluate(PUNCH, ['te_still2', '2026-09-03T07:00:00', ''])
    await pg.evaluate("() => tkStillCheck('2026-09-03T15:20:00')")
    await pg.evaluate("() => tkStillCheck('2026-09-03T15:51:00')")
    e = await pg.evaluate(E, 'te_still2')
    c.ok(e['held'] and e['out'] == '2026-09-03T15:15:00', f'still: never answered, it closes at the 8 h 15 mark (3:15 PM), held ({e["out"]}, {e["held"]})')
    await go(pg, 'time')
    t = await text(pg, '.view.on [data-tkhold]')
    c.ok('Say when you left' in t and 'not approved or paid' in t, f'still: his Clock page asks when he left ({t[:120]!r})')


async def s_workday(pg, c):
    await pin(pg, '08:00')
    await sign_in(pg, 'u_owner'); await go(pg, 'cosettings')
    ok = await pg.evaluate("() => { const r = [...document.querySelectorAll('.view.on [data-ydact]')].find(x => x.dataset.ydact === 'workday'); if (r) { r.click(); return true; } const b = [...document.querySelectorAll('.view.on button, .view.on a')].find(x => /Automatic Clock-In Hours|The Work Day/.test(((x.closest('[data-ydrow], .yd-row, li') || x.parentNode || x).innerText) || '')); if (b) { b.click(); return true; } return false; }")
    await pg.wait_for_timeout(300)
    m = await pg.evaluate("() => (document.querySelector('#mbm') || {}).innerText || ''")
    await shot(pg, 'workday_setting')
    c.ok(ok and 'Automatic Clock-In Hours' in m, f'workday: Company Settings has the window, and Change opens it ({ok}, {m[:60]!r})')
    await pg.evaluate("() => { const f = (k, v) => { const i = document.querySelector(`#mbm [data-f=${k}]`); if (i) i.value = v; }; f('start', '06:00'); f('end', '16:00'); }")
    await tap(pg, '#mbm #mbm-ok')
    w = await pg.evaluate("() => ({ w: tkgWindow(), audit: (DB.audit || DB.auditLog || []).some(a => JSON.stringify(a).includes('work-day-changed')) })")
    c.ok(w['w']['start'] == '06:00' and w['w']['end'] == '16:00' and w['audit'], f'workday: the owner saves 6:00 AM to 4:00 PM, recorded in the audit trail ({w})')
    await sign_in(pg, 'u_alberto'); await go(pg, 'time')
    await pg.evaluate("() => { tkGeoAgree(currentUser()); }")
    await go(pg, 'time')
    t = await text(pg, '.view.on .tkg-card')
    c.ok('6:00 AM to 4:00 PM' in t, f'workday: the Clock page says the new hours ({t[:100]!r})')
    await pg.evaluate(PUNCH, ['te_wd', '2026-09-03T06:40:00', ''])
    await pg.evaluate("() => { const t = DB.time.find(x => x.id === 'te_wd'); t.source = 'geo'; t.auto = { how: 'automatic, by location' }; t.lastOnSite = '2026-09-03T15:50:00'; save(); }")
    e = await pg.evaluate(E, 'te_wd')
    c.ok(not any('outside the work day' in f for f in e['flags']), f'workday: 6:40 AM is inside it now, not flagged ({e["flags"]})')
    await pin(pg, '16:03')
    e = await pg.evaluate(E, 'te_wd')
    c.ok((e['still'] or {}).get('why') == 'end', f'workday: the end question comes at 4:00 PM now ({e["still"]})')
    await pg.evaluate("() => { delete DB.company.autoClock; save(); }")


async def s_nextday(pg, c):
    await pin(pg, '08:00')
    await sign_in(pg, 'u_alberto'); await go(pg, 'time')
    await pg.evaluate("() => { DB.time = DB.time.filter(t => t.id !== 'te_nd'); DB.time.push({ id: 'te_nd', empId: 'em4', date: '2026-09-02', in: '2026-09-02T07:10:00', out: '', breakMin: 0, projectId: 'p121', code: '', notes: '', status: 'open', approvedBy: '', geoIn: { lat: 0, lng: 0, acc: 10, dist: 5 }, geoOut: null, source: 'phone', work: [] }); save(); }")
    await sign_in(pg, 'u_angel'); await go(pg, 'fcrew')
    e = await pg.evaluate(E, 'te_nd')
    c.ok(e['held'] and e['out'] == '2026-09-02T15:25:00' and e['h'] == 0, f'nextday: a hand punch open since yesterday is closed at its 8 h 15 mark and held when the foreman looks ({e["out"]}, {e["held"]})')
    row = await pg.evaluate("() => { const r = document.querySelector('#fcrew-body [data-fhrs=te_nd]'); return r ? { text: r.innerText.replace(/\\s+/g, ' '), appr: !!r.querySelector('[data-fappr]'), fix: (r.querySelector('[data-ffix]') || {}).innerText || '' } : null; }")
    await shot(pg, 'nextday_foreman_held')
    c.ok(row and 'Held' in row['text'] and not row['appr'] and row['fix'] == 'Correct Time', f"nextday: the foreman's row says Held, has no Approve, offers Correct Time ({row})")
    # the person says when he left, from his Clock page
    await pg.evaluate("() => { DB.users.find(u => u.id === 'u_satish') || DB.users.push({ id: 'u_satish', name: 'Satish', role: 'crew', employeeId: 'em4' }); save(); }")
    await sign_in(pg, 'u_satish'); await go(pg, 'time')
    t = await text(pg, '.view.on [data-tkhold]')
    c.ok('Say when you left' in t, f'nextday: his Clock page asks when he left ({t[:100]!r})')
    await tap(pg, '.view.on [data-tkhok]')
    await pg.evaluate("() => { const i = document.querySelector('#mbm [data-f=out]'); i.value = '15:40'; }")
    await tap(pg, '#mbm #mbm-ok')
    e = await pg.evaluate(E, 'te_nd')
    hd = e['hold'] or {}
    c.ok(not e['held'] and e['out'] == '2026-09-02T15:40:00' and hd.get('doneBy') == 'Satish' and hd.get('before') == '2026-09-02T15:25:00' and hd.get('after') == '2026-09-02T15:40:00' and hd.get('doneAt'),
         f'nextday: he says 3:40 PM; who, when, the time before and after are recorded ({e["out"]}, {hd})')
    t = await pg.evaluate(TOAST)
    c.ok('7:10 AM to 3:40 PM' in t and 'Open' in t, f'nextday: it toasts the day, with Open ({t[:100]!r})')
    c.ok(await side(pg) <= 0, 'nextday: the Clock page does not scroll sideways')
    await pg.evaluate("() => { DB.time = DB.time.filter(t => t.id !== 'te_nd'); save(); }")


async def s_routes(pg, c):
    await pin(pg, '08:00')
    mk = """() => { const mk = (id, inn, out, st, extra) => Object.assign({ id, empId: 'em4', date: inn.slice(0, 10), in: inn, out, breakMin: 0, projectId: 'p121', code: '05', notes: '', status: st, approvedBy: '', geoIn: null, geoOut: null, source: 'manual', work: out ? [{ projectId: 'p121', code: '05', hours: Math.round((new Date(out) - new Date(inn)) / 36e5 * 100) / 100, note: 'x' }] : [] }, extra || {});
      DB.time = DB.time.filter(t => !/^te_r/.test(t.id));
      DB.time.push(mk('te_r33', '2026-08-30T07:02:00', '2026-08-31T16:01:00', 'submitted'),
                   mk('te_rheld', '2026-09-02T07:02:00', '2026-09-02T15:17:00', 'submitted', { source: 'phone', hold: { at: '2026-09-03T08:00:00', out: '2026-09-02T15:17:00', why: 'nobody clocked out' } }),
                   mk('te_ropen', '2026-09-03T06:40:00', '', 'submitted'),
                   mk('te_rvoid', '2026-09-01T16:30:00', '2026-09-01T18:30:00', 'void'));
      save(); render(); }"""
    await pg.evaluate(mk)
    BAD = ['te_r33', 'te_rheld', 'te_ropen', 'te_rvoid']
    h0 = await pg.evaluate("ids => ids.map(id => hoursOf(DB.time.find(x => x.id === id)))", BAD)
    c.ok(all(h == 0 for h in h0), f'routes: a held, open, voided or over-16-hour punch counts 0 h for job cost and every total ({h0})')
    for who in ('Angel', 'Alan', 'Maren Holloway'):
        r = await pg.evaluate("([ids, by]) => ids.map(id => [id, !!timeApprove(DB.time.find(t => t.id === id), by, true), DB.time.find(t => t.id === id).status])", [BAD, who])
        c.ok(all(x[1] and x[2] != 'approved' for x in r), f'routes: the one door refuses all four for {who} ({r})')
    await sign_in(pg, 'u_alan'); await go(pg, 'time')
    r = await pg.evaluate("ids => ids.map(id => { const t = DB.time.find(x => x.id === id); try { timeAction(t, 'approve'); } catch (e) {} try { mbCloseModal(); } catch (e) {} return [id, t.status]; })", BAD)
    c.ok(all(x[1] != 'approved' for x in r), f"routes: the PM's drawer Approve refuses them ({r})")
    await pg.evaluate("() => { timeFilter = 'all'; render(); }")
    await pg.evaluate("() => { const b = document.getElementById('time-approve-all'); b && b.click(); }")
    await pg.wait_for_timeout(300)
    await pg.evaluate("() => { const ok = document.querySelector('#mbm #mbm-ok'); ok && ok.click(); }")
    await pg.wait_for_timeout(300)
    r = await pg.evaluate("ids => ids.map(id => [id, DB.time.find(x => x.id === id).status])", BAD)
    c.ok(all(x[1] != 'approved' for x in r), f'routes: Approve All Shown leaves them unapproved ({r})')
    await pg.evaluate(CLOSE)
    await sign_in(pg, 'u_angel'); await go(pg, 'fcrew')
    r = await pg.evaluate("ids => ids.filter(id => document.querySelector(`#fcrew-body [data-fappr=${id}]`))", BAD)
    c.ok(not r, f"routes: the foreman's Hours to Approve offers no Approve on any of them ({r})")
    await pg.evaluate("() => { const b = document.getElementById('fappr-all'); b && b.click(); }")
    await pg.wait_for_timeout(300)
    r = await pg.evaluate("ids => ids.map(id => [id, DB.time.find(x => x.id === id).status])", BAD)
    c.ok(all(x[1] != 'approved' for x in r), f'routes: Approve N Clean leaves them unapproved ({r})')
    await pg.evaluate(CLOSE)
    ok = await tap(pg, '#fcrew-body [data-ffix=te_rheld]')
    m = await pg.evaluate("() => (document.querySelector('#mbm') || {}).innerText || ''")
    c.ok(ok and 'why (required)' in m.lower() and 'really left' in m, f'routes: Correct Time on a held punch asks when he left and why ({m[:120]!r})')
    await tap(pg, '#mbm #mbm-ok')
    st = await pg.evaluate(E, 'te_rheld')
    c.ok(st['held'] and st['st'] != 'approved', f"routes: Fix's Save & Approve without a reason does nothing ({st['st']}, held {st['held']})")
    await pg.evaluate("() => { const f = (k, v) => { const i = document.querySelector(`#mbm [data-f=${k}]`); i.value = v; }; f('out', '15:30'); f('note', 'Called him: left at 3:30'); }")
    await tap(pg, '#mbm #mbm-ok')
    st = await pg.evaluate(E, 'te_rheld')
    c.ok(not st['held'] and st['st'] == 'approved' and st['out'] == '2026-09-02T15:30:00' and (st['hold'] or {}).get('doneBy') == 'Angel' and 'Called him' in (st['hold'] or {}).get('why', ''),
         f"routes: with the time and a reason, Fix confirms it (who, why) and approves it ({st['st']}, {st['out']}, {st['hold']})")
    await pg.evaluate(CLOSE)
    r = await pg.evaluate("""() => { ['te_r33', 'te_ropen'].forEach(id => { const t = DB.time.find(x => x.id === id); t.status = 'approved'; });
      const t2 = DB.time.find(x => x.id === 'te_rheld'); t2.hold = { at: '2026-09-03T08:00:00', out: t2.out, why: 'x' };
      const run = payrollFromTime({ quiet: true }); const ids = run ? (run.timeIds || []) : [];
      const linked = prLinkTime({ id: 'pr_hand', from: '2026-08-30', to: '2026-09-04', status: 'approved', entityId: 'ent1' }).map(t => t.id);
      return { run: ids.filter(id => /^te_r/.test(id)), linked: linked.filter(id => /^te_r/.test(id)) }; }""")
    c.ok(not r['run'] and not r['linked'], f'routes: the pay run built from time and a run typed by hand pay none of them, even forced to approved ({r})')
    await pg.evaluate("() => { DB.time = DB.time.filter(t => !/^te_r/.test(t.id)); save(); }")


async def s_void(pg, c):
    await pin(pg, '12:30')
    await sign_in(pg, 'u_alberto'); await go(pg, 'time')
    await pg.evaluate("""() => { const e = myEmp(); DB.time = DB.time.filter(t => !(t.empId === e.id && t.date === '2026-09-03' && t.id !== 'te8'));
      DB.time.push({ id: 'te_ov', empId: e.id, date: '2026-09-03', in: '2026-09-03T07:40:00', out: '2026-09-03T12:00:00', breakMin: 0, projectId: 'p121', code: '', notes: '', status: 'open', approvedBy: '', geoIn: { lat: 0, lng: 0, acc: 10, dist: 4 }, geoOut: null, source: 'phone', overlapOf: 'te8', work: [] }); save(); }""")
    await sign_in(pg, 'u_angel'); await go(pg, 'fcrew')
    wk = await pg.evaluate("() => { const r = document.querySelector('#fcrew-body [data-fwk=em2]'); return r ? r.innerText.replace(/\\s+/g, ' ') : ''; }")
    want = await pg.evaluate("() => { const td = today(), mon = iso(addDays(td, -(parse(td).getDay() + 6) % 7)); const L = DB.time.filter(t => t.empId === 'em2' && t.date >= mon && t.date <= td && !/void|rejected/.test(t.status)); return { merged: timeHoursOf(L), summed: Math.round(L.reduce((a, t) => a + hoursClock(t), 0) * 100) / 100 }; }")
    c.ok(f"{want['merged']:.1f} h" in wk and want['summed'] - want['merged'] > 4, f"void: while the overlap is open, This Week counts the overlapping time once ({wk!r}, {want})")
    await pg.evaluate("() => { const o = tkOverlapsOpen().find(o => o.a.id === 'te8' || o.b.id === 'te8'); tkOverlapPick(o); }")
    m = await pg.evaluate("() => [...document.querySelectorAll('#mbm [data-tkgwhich]')].map(p => p.innerText)")
    c.ok(len(m) == 2 and any('sent for approval' in x for x in m) and any('not sent yet' in x for x in m), f'void: the Pick One sheet says how each punch was made and where it stands ({m})')
    await pg.evaluate(CLOSE)
    await pg.evaluate("() => { const o = tkOverlapsOpen().find(o => o.a.id === 'te8' || o.b.id === 'te8'); tkOverlapResolve(o, o.a.id === 'te_ov' ? 'a' : 'b'); }")
    st = await pg.evaluate("() => DB.time.find(t => t.id === 'te8').status")
    log = await pg.evaluate("() => { const x = dlClockFor(DB.projects.find(p => p.id === 'p121'), '2026-09-03').find(c => c.empId === 'em2'); return x ? x.hours : null; }")
    c.ok(st == 'void' and log == 4.25, f'void: after the 9.1 h punch is voided the Daily Log carries 4.25 h for Alberto, not 9 ({st}, {log})')
    h = await pg.evaluate("() => hoursOf(DB.time.find(t => t.id === 'te8'))")
    c.ok(h == 0, f'void: the voided punch counts 0 h wherever hours are read (job cost, payroll, Ask) ({h})')
    await go(pg, 'fcrew')
    wk = await pg.evaluate("() => { const r = document.querySelector('#fcrew-body [data-fwk=em2]'); return r ? r.innerText.replace(/\\s+/g, ' ') : ''; }")
    want2 = await pg.evaluate("() => { const td = today(), mon = iso(addDays(td, -(parse(td).getDay() + 6) % 7)); return timeHoursOf(DB.time.filter(t => t.empId === 'em2' && t.date >= mon && t.date <= td)); }")
    c.ok(f"{want2:.1f} h" in wk, f'void: This Week after the pick reads the same reader ({wk!r}, {want2})')


async def s_own(pg, c):
    await pin(pg, '12:00')
    await sign_in(pg, 'u_angel'); await go(pg, 'fcrew')
    r = await pg.evaluate("""() => { const t = DB.time.find(x => x.empId === 'em1' && x.date === today()); if (t) { t.status = 'submitted'; t.approvedBy = ''; } save(); render();
      const b = document.getElementById('fappr-all'); const row = t && document.querySelector(`#fcrew-body [data-fhrs=${t.id}]`);
      return { id: t && t.id, btn: b ? b.innerText : '', rowAppr: !!(row && row.querySelector('[data-fappr]')), say: row ? row.innerText.replace(/\\s+/g, ' ') : '' }; }""")
    await shot(pg, 'own_foreman')
    await pg.evaluate("() => { const b = document.getElementById('fappr-all'); b && b.click(); }")
    st = await pg.evaluate("id => DB.time.find(t => t.id === id).status", r['id'])
    c.ok(r['id'] and st != 'approved', f"own: Approve N Clean does not approve the foreman's own hours ({r['btn']!r}, {st})")
    c.ok(not r['rowAppr'] and 'go to the PM' in r['say'], f"own: his own row has no Approve and says his hours go to the PM ({r})")


async def s_unsent(pg, c):
    await pin(pg, '12:00')
    await sign_in(pg, 'u_angel'); await go(pg, 'fcrew')
    await pg.evaluate("""() => { DB.time = DB.time.filter(t => t.id !== 'te_un');
      DB.time.push({ id: 'te_un', empId: 'em4', date: '2026-09-02', in: '2026-09-02T07:30:00', out: '2026-09-02T15:30:00', breakMin: 30, projectId: 'p121', code: '', notes: '', status: 'open', approvedBy: '', geoIn: null, geoOut: null, source: 'phone', work: [] }); save(); render(); }""")
    await tap(pg, '#fcrew-body [data-fappr=te_un]')
    m = await pg.evaluate("() => (document.querySelector('#mbm') || {}).innerText || ''")
    st = await pg.evaluate("() => DB.time.find(t => t.id === 'te_un').status")
    c.ok(st != 'approved' and 'why (required)' in m.lower(), f'unsent: Approve on a day not sent asks why first ({st}, {m[:80]!r})')
    await pg.evaluate("() => { document.querySelector('#mbm [data-f=note]').value = 'He told me the work: framing'; }")
    await tap(pg, '#mbm #mbm-ok')
    r = await pg.evaluate("() => { const t = DB.time.find(t => t.id === 'te_un'); return [t.status, t.approveWhy || '']; }")
    c.ok(r[0] == 'approved' and 'framing' in r[1], f"unsent: with the foreman's reason it is approved, and the reason is kept ({r})")
    await pg.evaluate("() => { DB.time = DB.time.filter(t => t.id !== 'te_un'); save(); }")


async def s_notmine(pg, c):
    await pin(pg, '07:45')
    await sign_in(pg, 'u_alberto'); await go(pg, 'time')
    await pg.evaluate("() => { const e = myEmp(); DB.time = DB.time.filter(t => !(t.empId === e.id && t.date === '2026-09-03' && t.id !== 'te8')); const t = DB.time.find(t => t.id === 'te8'); t.status = 'submitted'; delete t.notMine; save(); render(); }")
    await tap(pg, '#clock-in')
    m = await pg.evaluate("() => (document.querySelector('#mbm') || {}).innerText || ''")
    await shot(pg, 'notmine_sheet')
    c.ok("Those Hours Aren't Mine" in m and 'Start Another Shift' in m and 'Not Now' in m, f'notmine: Clock In on a day already sent offers three answers ({m[-140:]!r})')
    await tap(pg, '#mbm #mbm-alt')
    await pg.wait_for_timeout(900)
    await pg.evaluate(CLOSE)
    r = await pg.evaluate("() => ({ open: DB.time.filter(t => t.empId === myEmp().id && !t.out).length, flag: !!(DB.time.find(t => t.id === 'te8').notMine), block: timeApproveBlock(DB.time.find(t => t.id === 'te8'), 'Angel'), flags: timeFlags(DB.time.find(t => t.id === 'te8')) })")
    c.ok(r['flag'] and 'not his' in r['block'] and any('not his' in f for f in r['flags']), f"notmine: the earlier punch is flagged to the foreman and refused until he checks it ({r})")
    c.ok(r['open'] == 1, f'notmine: he is clocked in ({r["open"]})')


async def s_spanish(pg, c):
    await pin(pg, '15:20')
    await pg.evaluate("() => { DB.users.find(u => u.id === 'u_alberto').lang = 'es'; save(); }")
    await sign_in(pg, 'u_alberto')
    await pg.evaluate(PUNCH, ['te_es', '2026-09-03T07:00:00', ''])
    await go(pg, 'time')
    t = await text(pg, '.view.on [data-tkstill]')
    await shot(pg, 'spanish_still')
    c.ok('¿Sigues trabajando?' in t and 'Sigo Trabajando' in t and 'Marcar Salida' in t, f'spanish: the question and its buttons read in Spanish ({t[:160]!r})')
    await pg.evaluate("() => { tkStillCheck('2026-09-03T15:51:00'); render(); }")
    await go(pg, 'time')
    t = await text(pg, '.view.on [data-tkhold]')
    c.ok('Di a qué hora saliste' in t and 'no se aprueban ni se pagan' in t, f'spanish: the hold card reads in Spanish ({t[:160]!r})')
    await pg.evaluate("() => { DB.users.find(u => u.id === 'u_alberto').lang = 'en'; save(); }")


SECTIONS = {'limit': s_limit, 'home': s_home, 'day33': s_day33, 'weak': s_weak, 'window': s_window, 'autoend': s_autoend, 'autoswitch': s_autoswitch, 'autosent': s_autosent, 'hand': s_hand, 'still': s_still, 'workday': s_workday, 'nextday': s_nextday, 'routes': s_routes, 'void': s_void, 'own': s_own, 'unsent': s_unsent, 'notmine': s_notmine, 'spanish': s_spanish}


async def main():
    c = Checks()
    want = [a for a in sys.argv[1:] if a in SECTIONS] or list(SECTIONS)
    async with async_playwright() as p:
        for name in want:
            b, pg, errs = await open_app(p, phone=True)
            try:
                await SECTIONS[name](pg, c)
            except Exception as e:
                c.ok(False, f'{name}: stopped: {str(e)[:200]}')
            c.ok(not errs, f'{name}: no page errors ({errs[:2]})')
            await b.close()
    return c.done()

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
