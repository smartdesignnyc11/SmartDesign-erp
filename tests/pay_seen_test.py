"""pay_seen: one rule for hours the app did not see, and overtime counted once (the crew and payroll re-walk 4, 11-18).
Before this fix, on the walker's own steps:
  still      Still Working's Clock Out recorded no seen end: the foreman's Fix to 11:00 PM with "ok" paid 15.5 h (+$285).
  added      Enter Missing Hours added 3:35 to 11:00 PM to a day the app clocked to 3:35, reason "abc"; the foreman
             approved it in one tap with no reason and the PM was not shown it (+$281.96).
  split      Rebuilding the open 8/17 run after the 8/31 run took a Saturday of the same week counted the later run's
             4 h as prior: the week's overtime was paid twice (13 h for 9).
  runscreen  The run read "45.0" with an OT pill: no regular and overtime per week.
  tworuns    The seeded 8/17 to 8/28 run typed by hand and a run built from time for the same period both held Alex,
             with no warning.
  logdraft   The quick Daily Log (fLogDraft) added two overlapping punches (12.1 h) while the Daily Log read 9.1.
  s3         The run's label ended on the pay date (8/31 to 9/11 for a period to 9/13); the toast said "the Owner
             approves it" while Bills and Payroll said "Alan"; Crew showed "Not in today" in red on a Sunday; a run built
             from time said "until time tracking is added".
Also:
  paths      Every route in the source that writes a punch's end is listed here as a close (it must record the app's
             sight of the end: timeSeen or a hold) or an edit (timeWordOf catches a later end from the seen end); a new
             route that is neither fails, so it cannot ship without a seen end.
  stillauto  Still Working's Clock Out on a punch made by location: a time later than the last reading on site is said.
  crewclock  The foreman's Clock the Crew: the end he taps is the seen end; a later Fix needs a reason.
  splitpaid  The later run already approved: the rebuild of the earlier one does not change it and both runs say so.
Each check does the person's steps on the phone (390x844, touch) unless it is the controller's desktop work, on invented
data. Not covered: a phone with the app closed (a web app hears nothing), and Alan's open call on the reason for a time
inside the normal day after the phone slept (today's behaviour is kept).
Run: python3 pay_seen_test.py [section ...]   (SD_DIST names another build, e.g. the one before the fix)"""
import asyncio, datetime, glob, os, re, sys
from zoneinfo import ZoneInfo
from harness import async_playwright, open_app, sign_in, go, Checks, ROOT, OWNER

SHOTS = os.environ.get('T1_SHOTS') or os.path.join(ROOT, 'review', 'pay_seen')
os.makedirs(SHOTS, exist_ok=True)
NY = ZoneInfo('America/New_York')
E = """d => DB.time.filter(t => t.empId === 'em2' && t.date === d && !/void/.test(t.status)).map(t => ({ id: t.id, src: t.source, in: (t.in || '').slice(11, 16),
  out: (t.out || '').slice(11, 16), st: t.status, h: hoursOf(t), seen: (timeSeenEnd(t) || '').slice(11, 16), how: t.seenHow || '', pay: timePayBlock(t),
  word: timeWordOf(t) ? { say: timeWordSay(t), okBy: timeWordOf(t).okBy || '', okWhy: timeWordOf(t).okWhy || '' } : null }))"""
RUNS = """who => DB.payroll.filter(r => r.fromTime).map(r => { const d = (r.detail || []).find(x => x.name === who) || {};
  return { id: r.id, period: r.period, from: r.from, to: r.to, st: r.status, ot: d.ot, hours: d.hours, weeks: d.weeks || [], trail: (r.approvals || []).map(a => a.action).join(' | '),
    otAdjust: r.otAdjust || [], covered: r.covered || [], ids: DB.time.filter(t => t.payrollId === r.id).map(t => t.empId + ':' + t.date) }; })"""


# ---------------------------------------------------------------- the person's steps
async def shot(pg, name):
    try:
        await pg.screenshot(path=os.path.join(SHOTS, name + '.png'))
    except Exception:
        pass


async def tap(pg, sel, text=None, exact=False):
    h = await pg.evaluate_handle("([s, t, x]) => [...document.querySelectorAll(s)].find(e => e.getClientRects().length && (!t || (x ? (e.innerText || '').trim() === t : (e.innerText || '').includes(t)))) || null", [sel, text, exact])
    el = h.as_element()
    if not el: return False
    await el.scroll_into_view_if_needed()
    await el.tap() if (await pg.evaluate('innerWidth')) < 500 else await el.click()
    await pg.wait_for_timeout(350)
    return True


async def must(pg, sel, text=None, exact=False):
    if not await tap(pg, sel, text, exact):
        await shot(pg, 'zz_fail')
        raise AssertionError(f'no {sel} {text!r} on {await pg.evaluate("view")}')


async def fill(pg, sel, val):
    await pg.locator(sel).first.fill(val)


async def toast(pg):
    return (await pg.evaluate("() => (document.getElementById('toast') || {}).innerText || ''")).replace('\n', ' ')


async def mtext(pg):
    return await pg.evaluate("() => (document.getElementById('mbm') || {}).innerText || ''")


async def close_sheet(pg):
    await pg.evaluate("() => { try { mbCloseModal(); } catch (e) {} document.querySelectorAll('#mbm').forEach(e => e.remove()); }")


async def set_clock(pg, day, hm):
    """the device clock (New York time); on a firm day equal to it the app reads the real time of day"""
    y, mo, d = map(int, day.split('-')); h, m = map(int, hm.split(':'))
    await pg.clock.set_fixed_time(datetime.datetime(y, mo, d, h, m, 0, tzinfo=NY))
    await pg.wait_for_timeout(60)


async def firm_day(pg, day):
    """the owner moves the firm's day on the Firm's Clock card (Project settings), the screen's own control"""
    await sign_in(pg, 'u_owner'); await go(pg, 'proj')
    ok = await pg.evaluate("d => { const i = document.getElementById('asof-date'); if (!i) return false; i.value = d; i.dispatchEvent(new Event('change', {bubbles: true})); return true; }", day)
    await pg.wait_for_timeout(300)
    assert ok, 'no Firm Clock control'


async def day_at(pg, day, hm):
    await set_clock(pg, day, hm)
    await pg.evaluate("() => render()"); await pg.wait_for_timeout(200)


async def at_site(pg):
    g = await pg.evaluate("() => { const g = DB.projects.find(p => p.id === 'p121').project.geo; return { lat: g.lat, lng: g.lng }; }")
    await pg.context.grant_permissions(['geolocation'])
    await pg.context.set_geolocation({'latitude': g['lat'], 'longitude': g['lng'], 'accuracy': 12})


async def missing(pg, day, a, b, brk, note, why):
    """the man's Enter Missing Hours, on his Clock page"""
    await go(pg, 'time')
    await must(pg, '[data-tmlate]')
    await pg.wait_for_timeout(200)
    await pg.evaluate("d => { document.querySelector('#mbm [data-f=d]').value = d; }", day)
    await fill(pg, '#mbm [data-f=a]', a); await fill(pg, '#mbm [data-f=b]', b)
    await fill(pg, '#mbm [data-f=brk]', brk); await fill(pg, '#mbm [data-f=n]', note); await fill(pg, '#mbm [data-f=why]', why)
    await must(pg, '#mbm-ok')
    t = await toast(pg)
    still = await pg.evaluate("() => !!document.getElementById('mbm')")
    still and await close_sheet(pg)
    return t, still


async def send_day(pg):
    """his Clock page: the remaining hours on the line, the material question, Send"""
    await go(pg, 'time')
    await tap(pg, 'button', 'Put the remaining')
    await tap(pg, '.view.on button', 'Nothing needed')
    await tap(pg, '#work-submit')


async def fix(pg, tid, out, why):
    """the foreman's Fix on Crew: Out and the reason, Save & Approve"""
    await sign_in(pg, 'u_angel'); await go(pg, 'fcrew')
    await must(pg, f'[data-ffix="{tid}"]')
    out and await fill(pg, '#mbm [data-f=out]', out)
    await fill(pg, '#mbm [data-f=note]', why)
    await must(pg, '#mbm-ok')
    t = await toast(pg) + ' | ' + await mtext(pg)
    await close_sheet(pg)
    return t


async def approve_all(pg, who):
    """the foreman approves the man's rows on Crew, one tap each; a row that opens a sheet is left"""
    await sign_in(pg, 'u_angel'); await go(pg, 'fcrew')
    for _ in range(12):
        ids = await pg.evaluate("w => [...document.querySelectorAll('[data-fhrs]')].filter(r => r.innerText.startsWith(w) && r.querySelector('[data-fappr]')).map(r => r.dataset.fhrs)", who)
        if not ids: break
        await must(pg, f'[data-fappr="{ids[0]}"]')
        if await pg.evaluate("() => !!document.getElementById('mbm')"):
            await close_sheet(pg); break


async def build(pg):
    """the controller's Build Payroll from Time, on the desktop"""
    await pg.set_viewport_size({'width': 1440, 'height': 900})
    await sign_in(pg, 'u_controller'); await go(pg, 'time')
    await must(pg, '#btn-payrollfromtime')
    t = await toast(pg)
    await pg.set_viewport_size({'width': 390, 'height': 844})
    return t


async def clock_day(pg, day, out_hm):
    """Alberto clocks in at 7:00 and out at out_hm by hand, That Is My Day"""
    await set_clock(pg, day, '06:50'); await firm_day(pg, day); await at_site(pg)
    await sign_in(pg, 'u_alberto'); await day_at(pg, day, '07:00'); await go(pg, 'time'); await must(pg, '#clock-in')
    await pg.wait_for_timeout(500)
    await day_at(pg, day, out_hm); await go(pg, 'time'); await must(pg, '#clock-out'); await pg.wait_for_timeout(600)
    await tap(pg, 'button', 'That Is My Day')
    await close_sheet(pg)


# ---------------------------------------------------------------- paths (static: every route that writes a punch's end)
W_OUT = re.compile(r'\b([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)\.out\s*=(?!=)')
W_FN = re.compile(r'^\s*(?:async\s+)?function\s+([\w$]+)|^\s*([\w$]+)\s*=\s*(?:async\s+)?function\b')
# a close records the app's sight of the end in the same statement: timeSeen, or a hold (timeHold's e.hold is the seen end)
CLOSE = {('app.js', 'clockEvent', 'e'): "his own Clock Out (tap)", ('app.js', 'fmCrewClock', 't'): "the foreman's Clock the Crew",
         ('fieldclock.js', 'tkgPunchOut', 'e'): 'the automatic clock-out by location', ('app.js', 'timeCloseGiven', 'e'): "Still Working's Clock Out and a shift past 16 h",
         ('app.js', 'timeHold', 'e'): 'the app closes and holds it (sweep, Still Working unanswered, boot, location)'}
# an edit moves the end of a punch the app already saw end: timeWordOf compares it with that seen end
EDIT = {('app.js', 'timeHoldConfirm', 'e'): 'the answer to a hold', ('app.js', 'fixOpen', 't'): "the foreman's Fix",
        ('app.js', 'igClampPunches', 't'): 'a clock-out read before the clock-in, set to the clock-in to confirm',
        ('fieldclock.js', 'labApprove', 'te'): 'hours from a daily log changed after approval', ('fieldclock.js', 'tkgUndoOut', 'e'): 'Undo of an automatic clock-out (reopens it)'}
NOT_PUNCH = {'p.project', 'pj.project'}
NOT_PUNCH_AT = {('app.js', 'wire', 'p')}   # the project form's Out date


def s_paths(c):
    seen = {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'src', '*.js'))):
        L = open(f, encoding='utf-8').read().split('\n')
        base = os.path.basename(f)
        for i, l in enumerate(L):
            if l.strip().startswith('//'): continue
            for m in W_OUT.finditer(l):
                obj = m.group(1)
                if obj in NOT_PUNCH: continue
                fn = ''
                for j in range(i, -1, -1):
                    g = W_FN.match(L[j])
                    if g:
                        fn = next(x for x in g.groups() if x); break
                k = (base, fn, obj)
                if k in NOT_PUNCH_AT: continue
                seen.setdefault(k, []).append(i)
                if k in CLOSE:
                    near = '\n'.join(L[i:i + 4])
                    c.ok('timeSeen(' in near or '.hold = {' in l, f'paths: {CLOSE[k]} ({base} {fn}, line {i + 1}) records the seen end where it writes the end ({near[:200]!r})')
                else:
                    c.ok(k in EDIT, f'paths: a route nobody listed writes a punch end: {base} {fn} line {i + 1} ({l.strip()[:100]!r}). Record the seen end (timeSeen), or list it as an edit with why timeWordOf covers it')
    for k, why in list(CLOSE.items()) + list(EDIT.items()):
        c.ok(k in seen, f'paths: the listed route is still there: {why} ({k})')
    # the close by the Still Working sheet goes through timeCloseGiven (the walk's S1), and the long shift too
    fc = open(os.path.join(ROOT, 'src', 'fieldclock.js'), encoding='utf-8').read()
    app = open(os.path.join(ROOT, 'src', 'app.js'), encoding='utf-8').read()
    still = fc[fc.find('function tkStillAnswer'):fc.find('function tkStillHtml')]
    c.ok('timeCloseGiven(' in still and '.out =' not in still, "paths: Still Working's Clock Out closes through timeCloseGiven")
    longs = app[app.find('const clockLongBase_f3'):app.find('function f3AskWhenLeft')]
    c.ok('timeCloseGiven(' in longs, 'paths: a shift past 16 hours closes through timeCloseGiven')


# ---------------------------------------------------------------- runtime: every punch the app clocked carries a seen end
async def all_seen(pg, c, tag):
    r = await pg.evaluate("() => DB.time.filter(t => /^(phone|geo|foreman)$/.test(t.source || '') && t.out && t.date >= '2026-09-03' && !/void/.test(t.status)).map(t => [t.id, t.source, t.seenHow || '', !!timeSeenEnd(t)])")
    c.ok(r and all(x[3] for x in r), f'{tag}: every punch the app clocked and closed carries the app\'s sight of its end ({r})')


# ---------------------------------------------------------------- S1-a: Still Working's Clock Out
async def s_still(pg, c):
    day = '2026-09-04'
    await set_clock(pg, day, '06:50'); await firm_day(pg, day); await at_site(pg)
    await sign_in(pg, 'u_alberto'); await day_at(pg, day, '07:00'); await go(pg, 'time'); await must(pg, '#clock-in')
    await day_at(pg, day, '15:50'); await go(pg, 'time')
    await must(pg, '[data-tksa="out"]')
    await fill(pg, '#mbm [data-f=out]', '15:30'); await must(pg, '#mbm-ok')
    e = (await pg.evaluate(E, day))[0]
    c.ok(e['out'] == '15:30' and e['seen'] == '15:30' and e['how'] == 'asked' and not e['word'], f"still: Still Working's Clock Out at 3:30 PM records the app's sight of the end, 3:30 PM ({e})")
    await send_day(pg)
    e = (await pg.evaluate(E, day))[0]
    c.ok(e['st'] == 'submitted', f'still: the day is sent with its work ({e["st"]})')
    await shot(pg, 'still_sent')
    for why in ('', 'ok', 'ok fine'):
        t = await fix(pg, e['id'], '23:00', why)
        e2 = (await pg.evaluate(E, day))[0]
        c.ok(e2['st'] != 'approved' and e2['out'] == '15:30', f'still: Fix to 11:00 PM with {why!r} is refused and changes nothing ({e2["st"]} {e2["out"]} {t[:140]!r})')
    t = await fix(pg, e['id'], '23:00', 'Stayed to finish the tub deck blocking with me')
    e2 = (await pg.evaluate(E, day))[0]
    c.ok(e2['st'] == 'approved' and e2['h'] == 15.5 and e2['word'] and e2['word']['okBy'] == 'Angel' and 'tub deck' in e2['word']['okWhy'] and '3:30 PM' in e2['word']['say'],
         f'still: with a reason in words it is approved, both times and the reason on the entry ({e2})')
    await sign_in(pg, 'u_alan')
    r = await pg.evaluate("id => mApprovals().filter(x => x.kind === 'timeword' && x.id === id).map(x => [x.who, x.detail])", e['id'])
    c.ok(len(r) == 1 and 'tub deck' in r[0][1], f'still: the PM is shown it on Approvals ({r})')
    await all_seen(pg, c, 'still')


async def s_stillauto(pg, c):
    day = '2026-09-04'
    await set_clock(pg, day, '06:30'); await firm_day(pg, day); await at_site(pg)
    await sign_in(pg, 'u_alberto'); await day_at(pg, day, '06:40'); await go(pg, 'time')
    await must(pg, 'button', 'Turn On Automatic Clock-In'); await must(pg, '#mbm-ok')
    pos = "(() => { const g = DB.projects.find(p => p.id === 'p121').project.geo; return { lat: g.lat, lng: g.lng, acc: 12 }; })()"
    for hm in ('07:00', '09:00', '11:00', '13:00', '15:00', '15:30'):
        await set_clock(pg, day, hm); await pg.evaluate(f"() => tkGeoTick({pos})")
    await day_at(pg, day, '15:50'); await go(pg, 'time')
    await must(pg, '[data-tksa="out"]')
    await fill(pg, '#mbm [data-f=out]', '15:50'); await must(pg, '#mbm-ok')
    e = (await pg.evaluate(E, day))[0]
    c.ok(e['out'] == '15:50' and e['seen'] == '15:30' and e['word'] and 'Last reading on site 3:30 PM' in e['word']['say'] and e['pay'],
         f'stillauto: a time 20 minutes after his last reading on site is said, and needs the approver\'s reason before it is paid ({e})')
    await all_seen(pg, c, 'stillauto')


async def s_crewclock(pg, c):
    day = '2026-09-04'
    await set_clock(pg, day, '06:50'); await firm_day(pg, day); await at_site(pg)
    await sign_in(pg, 'u_alberto'); await day_at(pg, day, '07:00'); await go(pg, 'time'); await must(pg, '#clock-in')
    await day_at(pg, day, '15:30')
    await sign_in(pg, 'u_angel'); await go(pg, 'fcrew')
    if not await tap(pg, 'button', 'Clock the crew'):
        await pg.evaluate("() => fmCrewClock()")
    await pg.wait_for_timeout(300)
    await pg.evaluate("() => { const i = document.querySelector('#mbm [data-f=\"out:em2\"]'); i && (i.checked = true); }")
    await must(pg, '#mbm-ok')
    e = (await pg.evaluate(E, day))[0]
    c.ok(e['out'] == '15:30' and e['seen'] == '15:30' and e['how'] == 'foreman', f"crewclock: the foreman's Clock the Crew records his tap as the seen end ({e})")
    await sign_in(pg, 'u_alan'); await go(pg, 'time')
    await pg.evaluate("id => { openTime(id); document.getElementById('e-out').value = '22:00'; saveTime(); }", e['id'])
    e2 = (await pg.evaluate(E, day))[0]
    c.ok(e2['out'] == '22:00' and e2['pay'] and 'foreman at 3:30 PM' in e2['pay'], f'crewclock: moved to 10:00 PM in the drawer, it needs the approver\'s reason, naming the foreman\'s clock-out ({e2["pay"][:160]!r})')
    await all_seen(pg, c, 'crewclock')


# ---------------------------------------------------------------- S1-b: hours added by hand to a clocked day
async def s_added(pg, c):
    await clock_day(pg, '2026-09-04', '15:35')
    e0 = (await pg.evaluate(E, '2026-09-04'))
    c.ok(len(e0) == 1 and e0[0]['out'] == '15:35' and e0[0]['seen'] == '15:35', f'added: his day clocked 7:00 to 3:35 PM ({e0})')
    await firm_day(pg, '2026-09-08')
    await sign_in(pg, 'u_alberto')
    t, still = await missing(pg, '2026-09-04', '15:35', '23:00', '0', 'tub deck', 'abc')
    n = len(await pg.evaluate(E, '2026-09-04'))
    c.ok(n == 1 and still and 'in words' in t, f'added: his own reason "abc" is refused, the same bar as every reason ({n}, {t!r})')
    t, still = await missing(pg, '2026-09-04', '15:35', '23:00', '0', 'tub deck', 'Stayed late to finish the tub deck')
    L = await pg.evaluate(E, '2026-09-04')
    late = [x for x in L if x['src'] == 'late']
    c.ok(len(late) == 1 and late[0]['word'] and late[0]['pay'] and '3:35 PM' in late[0]['word']['say'] and 'foreman says why' in t,
         f'added: 3:35 to 11:00 PM on a day the app clocked to 3:35 is hours it did not see: said, and not paid without the approver\'s reason ({late}, {t!r})')
    tid = late[0]['id']
    await sign_in(pg, 'u_angel'); await go(pg, 'fcrew')
    row = await pg.evaluate("id => { const r = document.querySelector(`[data-fhrs=\"${id}\"]`); return r ? r.innerText.replace(/\\s+/g, ' ') : '' }", tid)
    c.ok('added by hand' in row and '3:35 PM' in row, f'added: the foreman\'s row says so ({row[:220]!r})')
    await must(pg, f'[data-fappr="{tid}"]')
    m = await mtext(pg)
    e = [x for x in await pg.evaluate(E, '2026-09-04') if x['id'] == tid][0]
    await shot(pg, 'added_approve_sheet')
    c.ok(e['st'] == 'submitted' and 'why (required)' in m.lower() and 'added by hand' in m, f'added: Approve is not one tap: it opens Fix with the reason asked ({e["st"]}, {m[:200]!r})')
    for why, ok in (('ok', False), ('He stayed with me to finish the tub deck', True)):
        await fill(pg, '#mbm [data-f=note]', why); await must(pg, '#mbm-ok')
        e = [x for x in await pg.evaluate(E, '2026-09-04') if x['id'] == tid][0]
        c.ok((e['st'] == 'approved') == ok, f'added: the foreman\'s reason {why!r}: {"approved" if ok else "refused"} ({e["st"]}, {e["word"]})')
        if not ok and not await pg.evaluate("() => !!document.getElementById('mbm')"):
            await must(pg, f'[data-fappr="{tid}"]')
    await close_sheet(pg)
    c.ok(e['word'] and e['word']['okBy'] == 'Angel' and 'tub deck' in e['word']['okWhy'], f'added: who and why on the entry ({e["word"]})')
    await sign_in(pg, 'u_alan')
    r = await pg.evaluate("id => mApprovals().filter(x => x.kind === 'timeword' && x.id === id).map(x => [x.who, x.detail])", tid)
    c.ok(len(r) == 1 and 'tub deck' in r[0][1], f'added: the PM is shown it on Approvals ({r})')
    # the office's Add Time Entry on the same day: the same rule
    await pg.set_viewport_size({'width': 1440, 'height': 900})
    await sign_in(pg, 'u_controller'); await go(pg, 'time')
    await pg.evaluate("""() => { openTime(); document.getElementById('e-emp').value = 'em2'; document.getElementById('e-date').value = '2026-09-04';
      document.getElementById('e-in').value = '05:00'; document.getElementById('e-out').value = '06:30'; document.getElementById('e-break').value = '0'; saveTime(); }""")
    o = [x for x in await pg.evaluate(E, '2026-09-04') if x['src'] == 'manual']
    c.ok(len(o) == 1 and o[0]['pay'] and 'added by hand' in o[0]['pay'], f"added: the office's Add Time Entry on a clocked day needs the approver's reason too ({o})")
    # a designer's two blocks in one day are not punches: nothing to say
    r = await pg.evaluate("() => DB.time.filter(t => t.empId === 'em8' && timeWordOf(t)).length")
    c.ok(r == 0, f'added: a designer\'s hours with no clock are not touched ({r})')
    # a day with no punch: missing hours need only the foreman's tap, as before
    await pg.set_viewport_size({'width': 390, 'height': 844})
    await sign_in(pg, 'u_alberto')
    free = '2026-09-05'   # a Saturday: nothing of his on it
    t, still = await missing(pg, free, '07:00', '15:30', '30', 'framing', 'Forgot to clock in that morning')
    lone = [x for x in await pg.evaluate(E, free) if x['src'] == 'late']
    c.ok(free and len(lone) == 1 and not lone[0]['word'] and not lone[0]['pay'], f'added: missing hours for a day with no punch ({free}) are not hours added to a clocked day ({lone}, {t!r})')


# ---------------------------------------------------------------- S1-c: a split week's overtime once across runs
async def split_setup(pg, c, approve_b=False):
    await set_clock(pg, '2026-08-30', '10:00'); await firm_day(pg, '2026-08-30')
    await sign_in(pg, 'u_alberto')
    for d in ('2026-08-24', '2026-08-25', '2026-08-26', '2026-08-27'):
        await missing(pg, d, '07:00', '16:30', '30', 'framing', 'Forgot to clock in that day')
    await approve_all(pg, 'Alberto')
    t = await build(pg)
    await firm_day(pg, '2026-09-03')
    await sign_in(pg, 'u_alberto')
    await missing(pg, '2026-08-29', '07:00', '11:00', '0', 'cleanup', 'Came in Saturday to finish')
    await approve_all(pg, 'Alberto')
    t = await build(pg)
    return t


async def s_split(pg, c):
    """the walker's own run: A holds 45 h of the week of 8/24, B takes the Saturday (4 h) late; A rebuilt next morning"""
    await set_clock(pg, '2026-08-30', '10:00'); await firm_day(pg, '2026-08-30')
    await sign_in(pg, 'u_alberto')
    for d in ('2026-08-24', '2026-08-25', '2026-08-26', '2026-08-27', '2026-08-28'):
        await missing(pg, d, '07:00', '16:30', '30', 'framing', 'Forgot to clock in that day')
    await approve_all(pg, 'Alberto')
    await build(pg)
    await firm_day(pg, '2026-09-03')
    await sign_in(pg, 'u_alberto')
    await missing(pg, '2026-08-29', '07:00', '11:00', '0', 'cleanup', 'Came in Saturday to finish')
    await approve_all(pg, 'Alberto')
    await build(pg)
    R = await pg.evaluate(RUNS, 'Alberto')
    c.ok(len(R) == 2 and R[0]['ot'] == 5 and R[1]['ot'] == 4, f'split: A pays 5 h over 40, B the Saturday 4 h ({[(x["period"], x["ot"]) for x in R]})')
    # Alex's missing day in A's period, approved: A takes it in on the next morning (rebuilt)
    await sign_in(pg, 'u_alex')
    await missing(pg, '2026-08-27', '07:00', '15:30', '30', 'deliveries', 'Phone died that day')
    await approve_all(pg, 'Alex')
    await firm_day(pg, '2026-09-04')
    R = await pg.evaluate(RUNS, 'Alberto')
    c.ok(R[0]['ot'] == 5 and R[1]['ot'] == 4 and R[0]['ot'] + R[1]['ot'] == 9, f'split: after A is rebuilt the week of 8/24 still pays 9 h over 40 once, A 5 and B 4 ({[(x["period"], x["ot"], x["weeks"]) for x in R]})')
    c.ok(R[0]['weeks'][0]['prior'] == 0 and R[1]['weeks'][0]['prior'] == 45, f'split: A counts nothing of B as prior; B counts A\'s 45 h ({R[0]["weeks"]}, {R[1]["weeks"]})')
    await s_runscreen(pg, c, R)


async def s_runscreen(pg, c, R=None):
    if R is None:
        return
    await pg.set_viewport_size({'width': 1440, 'height': 900})
    await sign_in(pg, 'u_controller')
    await pg.evaluate("id => openPayroll(id)", R[0]['id']); await pg.wait_for_timeout(300)
    r = await pg.evaluate("""() => { const tr = document.querySelector('#d-body tr[data-prman="Alberto"]'), wk = document.querySelector('#d-body tr[data-prwk="Alberto|2026-08-24"]');
      return { man: tr ? [...tr.cells].map(x => x.innerText.trim()) : null, wk: wk ? [...wk.cells].map(x => x.innerText.trim()) : null, body: document.getElementById('d-body').innerText } }""")
    await shot(pg, 'runscreen_A')
    c.ok(r['man'] and r['man'][1:4] == ['40.00', '5.00', '45.00'], f'runscreen: Alberto on run A: 40.00 regular, 5.00 overtime, 45.00 h ({r["man"]})')
    c.ok(r['wk'] and 'Week of' in r['wk'][0] and r['wk'][1:4] == ['40.00', '5.00', '45.00'], f'runscreen: the week of 8/24, Monday to Sunday, to the hundredth ({r["wk"]})')
    c.ok('time tracking is added' not in r['body'], 'runscreen: a run built from time no longer says "until time tracking is added"')
    await pg.evaluate("() => closeEditor()")
    await pg.evaluate("id => openPayroll(id)", R[1]['id']); await pg.wait_for_timeout(300)
    r = await pg.evaluate("""() => { const wk = document.querySelector('#d-body tr[data-prwk="Alberto|2026-08-24"]'); return wk ? [...wk.cells].map(x => x.innerText.trim()) : null }""")
    c.ok(r and '45.00 h on an earlier run' in r[0] and r[1:4] == ['0.00', '4.00', '4.00'], f'runscreen: on run B the Saturday is 4.00 h overtime after 45.00 h on an earlier run ({r})')
    await pg.evaluate("() => closeEditor()")
    # the phone: the same report, nothing sideways
    await pg.set_viewport_size({'width': 390, 'height': 844})
    await pg.evaluate("id => openPayroll(id)", R[0]['id']); await pg.wait_for_timeout(300)
    side = await pg.evaluate("() => document.documentElement.scrollWidth - innerWidth")
    vis = await pg.evaluate("() => !!document.querySelector('#d-body tr[data-prman=\"Alberto\"]')")
    await shot(pg, 'runscreen_phone')
    c.ok(vis and side <= 0, f'runscreen: on the phone the report shows and the page does not scroll sideways ({vis}, {side})')
    await pg.evaluate("() => closeEditor()")


async def s_splitlater(pg, c):
    """A holds 36 h of the week of 8/24, B the Saturday (4 h, no overtime then); 8/28 approved late goes to A: B's 4 h
    become overtime. B still open is rebuilt and both trails say so."""
    await split_setup(pg, c)
    R = await pg.evaluate(RUNS, 'Alberto')
    c.ok(len(R) == 2 and R[0]['ot'] == 0 and R[1]['ot'] == 0, f'splitlater: 36 h on A and 4 h on B: no overtime yet ({[(x["period"], x["ot"]) for x in R]})')
    await sign_in(pg, 'u_alberto')
    await missing(pg, '2026-08-28', '07:00', '16:30', '30', 'framing', 'Forgot to clock in that day')
    await approve_all(pg, 'Alberto')
    await firm_day(pg, '2026-09-04')
    R = await pg.evaluate(RUNS, 'Alberto')
    c.ok(R[0]['ot'] == 5 and R[1]['ot'] == 4, f'splitlater: A now 45 h of the week pays 5; B, still open, is rebuilt to 4 h over 40 ({[(x["period"], x["ot"]) for x in R]})')
    c.ok('rebuilt because run' in R[1]['trail'] and 'overtime' in R[1]['trail'] and 'was rebuilt' in R[0]['trail'], f'splitlater: both trails say it ({R[0]["trail"][-200:]!r} / {R[1]["trail"][-200:]!r})')


async def s_splitpaid(pg, c):
    """as splitlater, but B is approved before the late day comes: B is not changed and both runs say what it owes"""
    await split_setup(pg, c)
    await sign_in(pg, 'u_owner')
    pg.on('dialog', lambda d: asyncio.ensure_future(d.accept()))   # "differs from the recent average by more than 25%: approve anyway?"
    bid = (await pg.evaluate(RUNS, 'Alberto'))[1]['id']
    await pg.evaluate("id => { const r = DB.payroll.find(x => x.id === id); r.alloc = r.alloc && r.alloc.length ? r.alloc : [{ projectId: 'p121', pct: 100 }]; openPayroll(id); }", bid)
    await pg.wait_for_timeout(300)
    await tap(pg, '#d-body [data-pact=approve]') or await tap(pg, '#d-body [data-igpact=approve]')
    await pg.wait_for_timeout(300)
    for _ in range(3):   # "differs from the recent average by more than 25%: approve anyway?" and the split's review
        if not await pg.evaluate("() => !!document.getElementById('mbm')"): break
        await must(pg, '#mbm-ok'); await pg.wait_for_timeout(500)
    await close_sheet(pg)
    await pg.evaluate("() => { try { closeEditor(); } catch (e) {} }")
    st = (await pg.evaluate(RUNS, 'Alberto'))[1]['st']
    await sign_in(pg, 'u_alberto')
    await missing(pg, '2026-08-28', '07:00', '16:30', '30', 'framing', 'Forgot to clock in that day')
    await approve_all(pg, 'Alberto')
    await firm_day(pg, '2026-09-04')
    R = await pg.evaluate(RUNS, 'Alberto')
    c.ok(st == 'approved' and R[1]['st'] == 'approved' and R[1]['ot'] == 0, f'splitpaid: B, approved, is not changed ({st}, {R[1]["st"]}, {R[1]["ot"]})')
    adj = R[1]['otAdjust']
    c.ok(adj and adj[0]['now'] == 4 and adj[0]['was'] == 0 and 'Adjust it on the next run' in R[0]['trail'] + R[1]['trail'], f'splitpaid: both runs say B paid 0.00 h of overtime that should be 4.00 h ({adj}, {R[1]["trail"][-200:]!r})')
    await pg.set_viewport_size({'width': 1440, 'height': 900})
    await sign_in(pg, 'u_controller')
    await pg.evaluate("id => openPayroll(id)", R[1]['id']); await pg.wait_for_timeout(300)
    w = await pg.evaluate("() => (document.querySelector('#d-body .pr-warn') || {}).innerText || ''")
    c.ok('should be 4.00 h' in w, f'splitpaid: B\'s screen says it ({w!r})')


# ---------------------------------------------------------------- S2: a second run for the same men
async def s_tworuns(pg, c):
    await set_clock(pg, '2026-08-30', '10:00'); await firm_day(pg, '2026-08-30')
    await sign_in(pg, 'u_alex')
    await missing(pg, '2026-08-27', '07:00', '15:30', '30', 'deliveries', 'Phone died that day')
    await sign_in(pg, 'u_alberto')
    await missing(pg, '2026-08-26', '07:00', '15:30', '30', 'framing', 'Forgot to clock in that day')
    await approve_all(pg, 'Alex'); await approve_all(pg, 'Alberto')
    t = await build(pg)
    await shot(pg, 'tworuns_toast')
    R = await pg.evaluate("() => DB.payroll.filter(r => r.fromTime).map(r => ({ id: r.id, ids: DB.time.filter(t => t.payrollId === r.id).map(t => t.empId), covered: r.covered || [], notes: r.notes }))")
    c.ok(len(R) == 1 and 'em3' not in R[0]['ids'] and 'em2' in R[0]['ids'], f'tworuns: Alex is left out of the run from time, Alberto is in ({R and R[0]["ids"]})')
    c.ok('Alex is already on run 8/17 – 8/28' in t and 'typed by hand' in t and 'nobody is paid twice' in t, f'tworuns: the build says which man is already on the other run ({t!r})')
    r = await pg.evaluate("""() => { const live = r => !/^(void|rejected)$/.test(String(r.status || '')); const H = DB.payroll.filter(r => live(r) && !r.fromTime && r.from && r.to), T = DB.payroll.filter(r => live(r) && r.fromTime);
      return T.flatMap(r => DB.time.filter(t => t.payrollId === r.id && H.some(h => prInRun(h, t))).map(t => [r.id, t.empId, t.date])) }""")
    c.ok(r == [], f'tworuns: no hour is on a run built from time and a run typed by hand that covers it ({r})')
    await pg.set_viewport_size({'width': 1440, 'height': 900})
    await sign_in(pg, 'u_controller')
    await pg.evaluate("id => openPayroll(id)", R[0]['id']); await pg.wait_for_timeout(300)
    w = await pg.evaluate("() => (document.querySelector('#d-body .pr-warn') || {}).innerText || ''")
    c.ok('Alex is already on run' in w, f'tworuns: the run screen says it before anyone approves ({w!r})')


# ---------------------------------------------------------------- item 6: the quick Daily Log counts an overlap once
async def s_logdraft(pg, c):
    await at_site(pg)
    await sign_in(pg, 'u_alberto'); await day_at(pg, '2026-09-03', '10:00'); await go(pg, 'time')
    await must(pg, '#clock-in'); await pg.wait_for_timeout(800)
    if await pg.evaluate("() => !!document.getElementById('mbm')"): await must(pg, '#mbm-ok')
    await day_at(pg, '2026-09-03', '13:00'); await go(pg, 'time'); await must(pg, '#clock-out'); await pg.wait_for_timeout(500)
    await tap(pg, 'button', 'That Is My Day'); await close_sheet(pg)
    r = await pg.evaluate("""() => { const p = DB.projects.find(x => x.id === 'p121'); setCurrent(p.id); const L = DB.time.filter(t => t.empId === 'em2' && t.date === today() && t.projectId === p.id);
      return { n: L.length, sum: L.reduce((a, t) => a + hoursOf(t), 0), log: (dlClockFor(p, today()).find(x => x.empId === 'em2') || {}).hours, draft: (fLogDraft(today()).crew.find(x => x.name === 'Alberto') || {}).hours, once: timeHoursOf(L) } }""")
    c.ok(r['n'] >= 2 and r['sum'] > r['once'] and r['log'] == r['once'] and r['draft'] == r['once'], f'logdraft: two overlapping punches count once in the Daily Log, the quick log and his day ({r})')
    # the foreman's Send as Is (fLogQuick) sends that number
    await sign_in(pg, 'u_angel'); await day_at(pg, '2026-09-03', '15:40'); await go(pg, 'ftoday')
    try:
        ok = await pg.evaluate("() => { const b = [...document.querySelectorAll('#flog-quick')].find(b => b.getClientRects().length); b && b.click(); return !!b; }")
    except Exception:
        ok = False
    if not ok: await pg.evaluate("() => fLogQuick()")
    h = await pg.evaluate("() => { const l = DB.field.logs.find(l => l.projectId === S.id && l.date === today()); return l ? (l.crew.find(x => x.name === 'Alberto') || {}).hours : null }")
    c.ok(h == r['once'], f'logdraft: the log sent by Send as Is carries {r["once"]} h for Alberto ({h}, tapped {ok})')


# ---------------------------------------------------------------- S3s
async def s_s3(pg, c):
    await pg.set_viewport_size({'width': 1440, 'height': 900})
    await sign_in(pg, 'u_controller'); await go(pg, 'time')
    await pg.evaluate("() => { DB.time.filter(t => t.date >= '2026-08-31' && t.status === 'submitted' && !timeApproveBlock(t, 'Angel')).forEach(t => timeApprove(t, 'Angel', true)); save(); render(); }")
    t = await build(pg)
    await pg.set_viewport_size({'width': 1440, 'height': 900})
    r = await pg.evaluate("() => DB.payroll.filter(r => r.fromTime).map(r => [r.period, r.from, r.to, r.payDate, prApprover(r)])")
    c.ok(r and r[0][0] == '8/31 – 9/13' and r[0][2] == '2026-09-13', f's3: the run is labelled by its period, 8/31 to 9/13, not its pay date ({r})')
    c.ok(f'{OWNER} approves it' in t and 'the Owner approves' not in t, f's3: the toast names who approves it ({t!r})')
    await sign_in(pg, 'u_controller'); await go(pg, 'ap')
    body = await pg.evaluate("() => document.body.innerText")
    line = [l for l in body.split('\n') if 'to approve' in l and 'goes to' in l]
    c.ok(any(f'goes to {OWNER} to approve.' in l for l in line) and 'Alan to approve' not in body, f's3: Bills and Payroll names the same person as the toast ({line[:2]})')
    # a Sunday on Crew is not red
    await pg.set_viewport_size({'width': 390, 'height': 844})
    await set_clock(pg, '2026-09-06', '10:00'); await firm_day(pg, '2026-09-06')
    await sign_in(pg, 'u_angel'); await go(pg, 'fcrew')
    r = await pg.evaluate("() => ({ red: [...document.querySelectorAll('#fcrew-body .bad-t')].map(e => e.innerText).filter(s => /Not in/.test(s)), warn: !!document.querySelector('#fcrew-body .f-card.warn h3') && [...document.querySelectorAll('#fcrew-body .f-card.warn h3')].some(h => h.innerText === 'On Site Now'), off: (document.querySelector('#fcrew-body [data-offday]') || {}).innerText || '' })")
    await shot(pg, 's3_sunday_crew')
    c.ok(not r['red'] and not r['warn'] and 'Not a work day' in r['off'], f's3: Sunday on Crew says it is not a work day, nothing red ({r})')


SECTIONS = {'still': s_still, 'stillauto': s_stillauto, 'crewclock': s_crewclock, 'added': s_added, 'split': s_split, 'splitlater': s_splitlater,
            'splitpaid': s_splitpaid, 'tworuns': s_tworuns, 'logdraft': s_logdraft, 's3': s_s3}


async def main():
    c = Checks()
    args = sys.argv[1:]
    if not args or 'paths' in args:
        s_paths(c)
    want = [a for a in args if a in SECTIONS] or ([] if args == ['paths'] else list(SECTIONS))
    async with async_playwright() as p:
        for name in want:
            b, pg, errs = await open_app(p, phone=True)
            try:
                await SECTIONS[name](pg, c)
            except Exception as e:
                c.ok(False, f'{name}: stopped: {str(e)[:300]}')
            c.ok(not errs, f'{name}: no page errors ({errs[:2]})')
            await b.close()
    return c.done()

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
