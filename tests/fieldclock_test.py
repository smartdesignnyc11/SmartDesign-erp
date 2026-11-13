"""fieldclock: the automatic clock is safe to pay from (the foreman and crew review of the live phone build, 11-12).
Each check is the reviewer's own steps, at 390x844 with touch, on invented data.

  switch    S1-1  One switch for automatic clock-in. From every place it can be turned on (the crew's, the driver's and
                  the coordinator's Clock page, the foreman's Today) there is one control, it shows the notice, I Agree records
                  who and when (the person and the audit trail), and an arrival makes a punch. The old checkbox is
                  gone. With the browser reporting a position at the site, the app's own watch makes the punch.
  list      S1-2  A punch made by location is on the person's own list ("Clocked in automatically at 7:02 AM", the
                  job) and, once it closes, in the foreman's Hours to Approve, the same as a hand punch; one record,
                  not a copy. A day whose work was logged is sent when the app clocks out.
  overlap   S1-3  Two punches that overlap show Pick One on the Crew row and in Hours to Approve from the moment the
                  overlap exists. Approve refuses while it is open and says why (the Crew page, the time drawer,
                  Approve All Shown). Payroll holds both punches, in a run built from time and in a run typed by
                  hand, even when both were approved. Picking one releases the other for approval.
  handoff   S2-4  The foreman hands a task that is not a schedule line to the crew on that job: they are listed, and
                  first; the offer lands on the crew member's Clock with Accept.
  receive   S2-5  The foreman's Site opens the one receive sheet from its Deliveries card: a count per line, Good /
                  Short / Damaged / Wrong, the slip's photo. A material with an open order behind it opens the same
                  sheet.
The crew and driver review (11-12):
  today     S1    No punch ends after the app's clock: a fresh demo has no closed day for today for anyone who clocks.
                  A first Clock In is one clean punch. With today's day already closed and sent, Clock In says so and
                  offers Start Another Shift before anything is punched, by hand and by location; a lunch break is
                  not asked about.
  driver    S2    The driver has Deliveries: Receive a Delivery on Route, every job's orders, and Receive opens the one
                  receive sheet (counts, Good / Short / Damaged / Wrong, the slip's photo).
  donephoto S2    Done stays one tap and then offers a photo: Add a Photo opens the camera and the photo lands on the
                  task; ignoring it skips it; a task that needs proof still stops for the photo first.

Arrivals and leaves are fed to the app's own location function (tkGeoTick) with a position and a time, and in one
check through the browser's mocked geolocation. Real GPS on a real phone is not tested here.
Run: python3 fieldclock_test.py [section ...]   (SD_DIST names another build, e.g. the one before the fix)"""
import asyncio, os, re, sys
from harness import async_playwright, open_app, sign_in, go, Checks, ROOT, PHONE

SHOTS = os.environ.get('T1_SHOTS') or os.path.join(ROOT, 'review', 'fieldclock')
os.makedirs(SHOTS, exist_ok=True)
CLOSE = "() => { try { mbCloseModal(); } catch (e) {} document.querySelectorAll('#mbm').forEach(e => e.remove()); }"
TOAST = "() => (document.getElementById('toast') || {}).innerText || ''"
SITE = "(() => { const g = DB.projects.find(p => p.id === 'p121').project.geo; return { lat: g.lat, lng: g.lng, acc: 12 }; })()"
FAR = "(() => { const g = DB.projects.find(p => p.id === 'p121').project.geo; return { lat: g.lat + 0.03, lng: g.lng, acc: 12 }; })()"
# every visible control on the page that could switch automatic clock-in on: a checkbox, switch or button whose own
# words (or its label's) say so
ON_CONTROLS = """() => [...document.querySelectorAll('.view.on input[type=checkbox], .view.on [role=switch], .view.on button, .view.on a.btn')]
  .filter(e => e.getClientRects().length || (e.closest('label') && e.closest('label').getClientRects().length))
  .map(e => ({ tag: e.tagName, id: e.id || '', text: ((e.closest('label') || e).innerText || '').replace(/\\s+/g, ' ').trim() }))
  .filter(x => /automatic/i.test(x.text) && !/turn off/i.test(x.text))"""
AGREED = """() => { const u = currentUser(), a = (DB.audit || DB.auditLog || []).slice(-40).filter(x => JSON.stringify(x).includes('auto-clock-by-location'));
  return { at: (u.geoAck || {}).at || '', off: (u.geoAck || {}).off || '', audit: a.some(x => JSON.stringify(x).includes(u.id)), auditWho: a.some(x => JSON.stringify(x).includes(u.name)) }; }"""


async def shot(pg, name):
    try:
        await pg.screenshot(path=os.path.join(SHOTS, name + '.png'))
    except Exception:
        pass


async def mbm_text(pg):
    return await pg.evaluate("() => (document.querySelector('#mbm') || {}).innerText || ''")


async def tap(pg, sel, text=None):
    """a real tap on the first visible element matching sel (and holding text)"""
    h = await pg.evaluate_handle("([s, t]) => [...document.querySelectorAll(s)].find(e => e.getClientRects().length && (!t || (e.innerText || '').includes(t))) || null", [sel, text])
    el = h.as_element()
    if not el: return False
    await el.scroll_into_view_if_needed()
    await el.tap()
    await pg.wait_for_timeout(350)
    return True


async def clear_today(pg):
    await pg.evaluate("() => { const e = myEmp(); DB.time = DB.time.filter(t => !(t.empId === e.id && t.date === today())); save(); render(); }")


async def s_switch(pg, c):
    """S1-1: one switch, the notice, consent recorded, and "on" means an arrival makes a punch"""
    for uid, view, who in (('u_alberto', 'time', 'crew'), ('u_alex', 'time', 'driver'), ('u_angel', 'ftoday', 'foreman'), ('u_chen', 'time', 'coordinator')):
        await sign_in(pg, uid); await go(pg, view)
        if not await pg.evaluate("() => !!myEmp()"):
            c.ok(False, f'switch: {who} has an employee record'); continue
        await clear_today(pg)
        await pg.evaluate("() => { delete currentUser().geoAck; delete DB.autoClock; save(); render(); }")
        ctl = await pg.evaluate(ON_CONTROLS)
        await shot(pg, f'switch_{who}_off')
        c.ok(len(ctl) == 1 and ctl[0]['tag'] == 'BUTTON', f"switch: {who}'s {view} has one control that turns automatic clock-in on ({ctl})")
        c.ok(await pg.evaluate("() => !document.getElementById('geo-auto')"), f'switch: {who}: the old checkbox is gone')
        # turn it on from here: the first control found, whatever it is
        n0 = await pg.evaluate("() => DB.time.length")
        sel = ('#' + ctl[0]['id']) if ctl and ctl[0]['id'] else '.view.on [data-tkgon]'
        if ctl and ctl[0]['tag'] == 'INPUT':
            await pg.evaluate("s => document.querySelector(s).click()", sel); await pg.wait_for_timeout(300)
        else:
            await tap(pg, sel)
        t = await mbm_text(pg)
        c.ok('never saved as a track' in t and 'I Agree' in t, f'switch: {who}: turning it on shows the notice first ({t[:60]!r})')
        r = await pg.evaluate(AGREED)
        c.ok(not r['at'], f'switch: {who}: nothing is recorded, and nothing is on, before I Agree ({r})')
        await tap(pg, '#mbm #mbm-ok')
        r = await pg.evaluate(AGREED)
        c.ok(bool(r['at']) and r['audit'] and r['auditWho'], f'switch: {who}: I Agree records who and when, on the person and in the audit trail ({r})')
        # an arrival makes a punch
        res = await pg.evaluate(f"() => tkGeoTick({SITE}, today() + 'T07:02:00')")
        e = await pg.evaluate("id => { const e = DB.time.find(t => t.id === id); return e ? { emp: e.empId === myEmp().id, pid: e.projectId, src: e.source, inn: e.in } : null; }", res.get('id'))
        c.ok(res.get('did') == 'in' and e and e['emp'] and e['pid'] == 'p121' and e['inn'].endswith('T07:02:00') and await pg.evaluate("() => DB.time.length") == n0 + 1,
             f'switch: {who}: after turning it on, arriving at the site makes a punch ({res}, {e})')
        await go(pg, view)
        card = await pg.evaluate("() => (document.querySelector('.view.on .tkg-card') || {}).innerText || ''")
        await shot(pg, f'switch_{who}_on')
        c.ok('Automatic clock-in is on' in card and 'Turn Off' in card, f'switch: {who}: the same place says it is on, with Turn Off ({card[:70]!r})')
        r = await pg.evaluate("() => { const b = document.querySelector('.view.on .tkg-card .btn'); const x = b ? b.getBoundingClientRect() : null; return { h: x ? Math.round(x.height) : 0, side: document.documentElement.scrollWidth - innerWidth }; }")
        c.ok(r['h'] >= 44 and r['side'] <= 0, f'switch: {who}: Turn Off is a 44px target and nothing scrolls sideways ({r})')
        # Turn Off: manual again, said, and recorded
        await tap(pg, '.view.on [data-tkgoff]')
        await clear_today(pg)
        res = await pg.evaluate(f"() => tkGeoTick({SITE}, today() + 'T07:05:00')")
        c.ok(res.get('did') == 'none' and await pg.evaluate("() => !!currentUser().geoAck.off"), f'switch: {who}: Turn Off makes the clock manual again ({res})')


async def s_watch(p, c):
    """S1-1, through the device: the browser reports a position at the site; turning it on is enough for a punch"""
    b = await p.chromium.launch()
    ctx = await b.new_context(viewport=PHONE, is_mobile=True, has_touch=True, permissions=['geolocation'], geolocation={'latitude': 40.6907, 'longitude': -73.9929, 'accuracy': 12})
    pg = await ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    from harness import URL
    await pg.goto(URL)
    await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
    await sign_in(pg, 'u_alberto'); await go(pg, 'time')
    g = await pg.evaluate("() => { const g = DB.projects.find(p => p.id === 'p121').project.geo; return [g.lat, g.lng]; }")
    await ctx.set_geolocation({'latitude': g[0], 'longitude': g[1], 'accuracy': 12})
    await clear_today(pg)
    await pg.evaluate("() => { delete currentUser().geoAck; delete DB.autoClock; save(); render(); }")
    ctl = await pg.evaluate(ON_CONTROLS)
    for x in ctl:   # whatever says it turns automatic clock-in on: use it, and agree if it asks
        if x['tag'] == 'INPUT': await pg.evaluate("i => { const e = document.getElementById(i); e && e.click(); }", x['id'])
        else: await tap(pg, '.view.on [data-tkgon]')
        await pg.wait_for_timeout(300)
        if 'I Agree' in await mbm_text(pg): await tap(pg, '#mbm #mbm-ok')
        said = await pg.evaluate(TOAST)
        punched = False
        for _ in range(12):
            await pg.wait_for_timeout(300)
            punched = await pg.evaluate("() => DB.time.some(t => t.empId === myEmp().id && t.date === today() && !t.out)")
            if punched: break
        c.ok(punched, f"watch: {x['tag'].lower()} \"{x['text'][:40]}\" said {said[:45]!r}, and standing on the site made a punch")
        r = await pg.evaluate(AGREED)
        c.ok(bool(r['at']) and r['audit'], f"watch: turning it on that way recorded the consent ({r})")
        await clear_today(pg)
        await pg.evaluate("() => { delete currentUser().geoAck; delete DB.autoClock; try { stopGeofence(); } catch (e) {} save(); render(); }")
    c.ok(len(ctl) >= 1, 'watch: the Clock page has a control to turn it on')
    c.ok(not errs, f'watch: no page errors ({errs[:2]})')
    await b.close()


async def s_list(pg, c):
    """S1-2: the automatic punch is on the person's own list and in the foreman's Hours to Approve, like a hand punch"""
    await sign_in(pg, 'u_alberto'); await go(pg, 'time')
    await clear_today(pg)
    await pg.evaluate("() => { tkGeoAgree(currentUser()); }")
    res = await pg.evaluate(f"() => tkGeoTick({SITE}, today() + 'T07:02:00')")
    await go(pg, 'time')
    rows = await pg.evaluate("() => [...document.querySelectorAll('#time-table tr[data-edit]')].filter(r => r.getClientRects().length).map(r => [r.dataset.edit, r.innerText.replace(/\\s+/g, ' ').trim()])")
    mine = [r for r in rows if r[0] == 'time:' + str(res.get('id'))]
    await shot(pg, 'list_crew_on_clock')
    c.ok(len(mine) == 1 and 'Clocked in automatically at 7:02 AM' in mine[0][1] and '121 State' in mine[0][1], f"list: the punch the app made is on Alberto's own list, with when and where ({mine or rows})")
    # he logs his work while on the clock; leaving the site clocks him out and sends the day
    await pg.evaluate("id => { const e = DB.time.find(t => t.id === id); e.work = [{ projectId: 'p121', code: '05', hours: 5.5, note: 'Rough plumbing' }]; save(); }", res.get('id'))
    await pg.evaluate(f"() => tkGeoTick({FAR}, today() + 'T12:32:00')")
    out = await pg.evaluate(f"() => tkGeoTick({FAR}, today() + 'T12:48:00')")
    e = await pg.evaluate("id => { const e = DB.time.find(t => t.id === id); return { out: e.out, st: e.status, n: DB.time.filter(t => t.empId === e.empId && t.date === e.date).length }; }", res.get('id'))
    c.ok(out.get('did') == 'out' and e['st'] == 'submitted', f'list: clocked out by location with the work logged, the day is sent like a hand punch ({out}, {e})')
    await go(pg, 'time')
    rows = await pg.evaluate("() => [...document.querySelectorAll('#time-table tr[data-edit]')].filter(r => r.getClientRects().length).map(r => [r.dataset.edit, r.innerText.replace(/\\s+/g, ' ').trim()])")
    mine = [r for r in rows if r[0] == 'time:' + str(res.get('id'))]
    await shot(pg, 'list_crew_sent')
    c.ok(len(mine) == 1 and '7:02 AM to 12:32 PM' in mine[0][1] and 'automatic' in mine[0][1] and '121 State' in mine[0][1] and e['n'] == 1, f"list: closed, it stays on his list, marked automatic; one record, not a copy ({mine}, {e['n']})")
    side = await pg.evaluate("() => document.documentElement.scrollWidth - innerWidth")
    c.ok(side <= 0, f"list: the crew's Clock does not scroll sideways ({side})")
    # a second automatic day with nothing logged: closed and not sent. The foreman still has it.
    ids = await pg.evaluate("""() => { const e = myEmp(), d = '2026-09-02'; DB.time = DB.time.filter(t => !(t.empId === e.id && t.date === d));
      const a = { id: 'te_auto2', empId: e.id, date: d, in: d + 'T07:04:00', out: d + 'T15:30:00', breakMin: 30, projectId: 'p121', code: '', notes: 'Automatic, by location (8 m from the site, accurate to 12 m)', status: 'open', approvedBy: '', geoIn: { lat: 0, lng: 0, acc: 12, dist: 8 }, geoOut: null, source: 'geo', auto: { how: 'automatic, by location', dist: 8, acc: 12 }, autoOut: true, work: [] };
      const h = { id: 'te_hand2', empId: 'em3', date: d, in: d + 'T07:30:00', out: d + 'T15:30:00', breakMin: 30, projectId: 'p121', code: '', notes: '', status: 'open', approvedBy: '', geoIn: null, geoOut: null, source: 'phone', work: [] };
      DB.time = DB.time.filter(t => !(t.empId === 'em3' && t.date === d)); DB.time.push(a, h); save(); return [a.id, h.id]; }""")
    await go(pg, 'time')
    own = await pg.evaluate("() => [...document.querySelectorAll('#time-table tr[data-edit]')].filter(r => r.getClientRects().length).map(r => r.dataset.edit)")
    c.ok('time:te_auto2' in own, f"list: a punch the app closed with nothing logged is on his list too ({own})")
    await sign_in(pg, 'u_angel'); await go(pg, 'fcrew')
    r = await pg.evaluate("""id => { const card = [...document.querySelectorAll('#fcrew-body .card')].find(c => /Hours to Approve/i.test((c.querySelector('h3') || {}).innerText || ''));
      const rows = card ? [...card.querySelectorAll('[data-fappr]')].map(b => [b.dataset.fappr, b.closest('.f-row').innerText.replace(/\\s+/g, ' ')]) : [];
      return { rows, sent: rows.find(x => x[0] === id) || null, auto: rows.find(x => x[0] === 'te_auto2') || null, hand: rows.find(x => x[0] === 'te_hand2') || null,
               today: (() => { const n = (document.querySelector('.dl-appr') || {}).innerText || ''; return n; })(), want: fHoursToApprove ? fHoursToApprove(S).entries.length : -1 }; }""", res.get('id'))
    await shot(pg, 'list_foreman_hours')
    c.ok(bool(r['sent']) and 'automatic, by location' in r['sent'][1], f"list: the day the app clocked is in the foreman's Hours to Approve, marked automatic ({r['sent']})")
    c.ok(bool(r['auto']) and 'Not sent yet' in r['auto'][1], f"list: the automatic day nobody sent is there too, and says it was not sent ({r['auto']})")
    c.ok(bool(r['hand']) and 'Not sent yet' in r['hand'][1], f"list: a hand punch nobody sent reads the same ({r['hand']})")
    c.ok(len(r['rows']) == r['want'], f"list: Hours to Approve draws the rows of its one reader ({len(r['rows'])} rows, {r['want']} entries)")
    await go(pg, 'ftoday')
    n = await pg.evaluate("() => { const t = (document.querySelector('#ftoday-body .dl-appr') || {}).textContent || ''; const m = t.match(/(\\d+) entr/); return m ? +m[1] : -1; }")
    c.ok(n == r['want'], f"list: Today's \"waiting on your approval\" counts the same rows ({n} vs {r['want']})")
    # he approves the automatic day from the row
    await go(pg, 'fcrew')
    await tap(pg, '#fcrew-body [data-fappr="te_auto2"]')
    st = await pg.evaluate("() => { const e = DB.time.find(t => t.id === 'te_auto2'); return [e.status, e.approvedBy]; }")
    c.ok(st[0] == 'approved' and 'Angel' in st[1], f'list: the foreman approves it from the row ({st})')


async def s_overlap(pg, c):
    """S1-3: Pick One where the foreman sees the overlap, Approve refuses, payroll holds"""
    await sign_in(pg, 'u_alberto'); await go(pg, 'time')
    base = await pg.evaluate("""() => { const e = myEmp(), td = today(); DB.time = DB.time.filter(t => !(t.empId === e.id && t.date === td));
      const d = { id: 'te_day', empId: e.id, date: td, in: td + 'T07:12:00', out: td + 'T16:48:00', breakMin: 30, projectId: 'p121', code: '05', notes: '', status: 'submitted', approvedBy: '', geoIn: null, geoOut: null, source: 'manual',
        work: [{ projectId: 'p121', code: '05', hours: 9.1, note: 'Rough plumbing garden bath' }] };
      DB.time.push(d); save(); tkGeoAgree(currentUser()); return { id: d.id, st: d.status, inn: d.in, out: d.out }; }""")
    c.ok(bool(base) and base['st'] == 'submitted', f"overlap: Alberto's 9/3 is on the clock and sent ({base})")
    res = await pg.evaluate(f"() => tkGeoTick({SITE}, today() + 'T12:00:00')")
    asked = await pg.evaluate(TOAST)
    n = await pg.evaluate("() => DB.time.filter(t => t.empId === myEmp().id && !t.out).length")
    c.ok(res.get('did') == 'asked' and n == 0 and 'already sent for approval' in asked and 'Start Another Shift' in asked, f'overlap: arriving on a day already sent asks first and punches nothing ({res}, {asked[:90]!r})')
    await tap(pg, '#toast a, #toast button', 'Start Another Shift')
    toast = await pg.evaluate(TOAST)
    auto = await pg.evaluate("() => (DB.time.find(t => t.empId === myEmp().id && !t.out) || {}).id || ''")
    c.ok(bool(auto) and 'already runs' in toast and 'not counted twice' in toast, f'overlap: Start Another Shift inside a day already on the clock says it overlaps ({toast[:110]!r})')
    PAIR = """([a, b]) => { const q = s => [...document.querySelectorAll(s)].filter(e => e.getClientRects().length);
      const hours = [...document.querySelectorAll('#fcrew-body .card')].find(c => /Hours to Approve/i.test((c.querySelector('h3') || {}).innerText || ''));
      const week = [...document.querySelectorAll('#fcrew-body .card')].find(c => /This Week/i.test((c.querySelector('h3') || {}).innerText || ''));
      const wrow = week ? [...week.querySelectorAll('[data-fwk]')].find(r => /Alberto/.test(r.innerText)) : null;
      const hov = hours ? [...hours.querySelectorAll('.tkg-ov')] : [];
      return { week: wrow ? wrow.innerText.replace(/\\s+/g, ' ') : '', weekPick: !!(wrow && wrow.querySelector('[data-tkgpick]')),
               hours: hov.map(r => r.innerText.replace(/\\s+/g, ' ')), hoursPick: hov.some(r => r.querySelector('[data-tkgpick]')),
               approve: q('#fcrew-body [data-fappr]').map(b => b.dataset.fappr).filter(id => id === a || id === b),
               pickH: Math.min(...q('#fcrew-body [data-tkgpick]').map(b => Math.round(b.getBoundingClientRect().height)), 999), side: document.documentElement.scrollWidth - innerWidth }; }"""
    # from the moment it exists: he is still on the clock
    await sign_in(pg, 'u_angel'); await go(pg, 'fcrew')
    r = await pg.evaluate(PAIR, [base['id'], auto])
    await shot(pg, 'overlap_crew_open')
    c.ok(r['weekPick'] and 'overlap' in r['week'], f"overlap: the Crew row has Pick One the moment the overlap exists ({r['week'][:120]!r})")
    c.ok(r['hoursPick'] and r['hours'] and '12:00 PM' in r['hours'][0] and '7:12 AM' in r['hours'][0], f"overlap: Hours to Approve has the pair with Pick One, both punches named ({r['hours']})")
    c.ok(not r['approve'], f"overlap: neither punch offers Approve while the overlap is open ({r['approve']})")
    c.ok(r['pickH'] >= 44 and r['side'] <= 0, f"overlap: Pick One is a 44px target, no sideways scroll ({r['pickH']}, {r['side']})")
    await go(pg, 'ftoday')
    t = await pg.evaluate("() => (document.querySelector('#ftoday-body .tkg-remind') || {}).innerText || ''")
    c.ok('overlap' in t and 'Pick One' in t, f"overlap: Today says it the same day, not only before the cutoff ({t[:80]!r})")
    # he leaves; the pair is closed
    await sign_in(pg, 'u_alberto')
    await pg.evaluate(f"() => tkGeoTick({FAR}, today() + 'T13:00:00')")
    await pg.evaluate(f"() => tkGeoTick({FAR}, today() + 'T13:20:00')")
    await sign_in(pg, 'u_angel'); await go(pg, 'fcrew')
    r = await pg.evaluate(PAIR, [base['id'], auto])
    await shot(pg, 'overlap_crew_closed')
    c.ok(r['weekPick'] and r['hoursPick'] and not r['approve'] and '1:00 PM' in ' '.join(r['hours']), f"overlap: closed, the pair still reads Pick One and not Approve ({r['hours']}, {r['approve']})")
    c.ok('4 days' in r['week'], f"overlap: two punches on one day are one day worked (8/31, 9/1, 9/2 and today) ({r['week'][:80]!r})")
    # Approve refuses, wherever it is pressed, and says why
    ST = "([a, b]) => [a, b].map(id => DB.time.find(t => t.id === id).status)"
    said = await pg.evaluate("id => { const why = timeApprove(DB.time.find(t => t.id === id), 'Angel'); return [why, (document.getElementById('toast') || {}).innerText || '']; }", base['id'])
    c.ok('overlap' in said[0] and 'overlap' in said[1] and 'Pick One' in said[1] and await pg.evaluate(ST, [base['id'], auto]) == ['submitted', 'open'], f"overlap: the foreman's Approve refuses and says why, with Pick One ({said[1][:100]!r})")
    await sign_in(pg, 'u_owner')
    await pg.evaluate("id => { setCurrent('p121'); view = 'time'; timeFilter = 'pending'; render(); openTime(id); }", base['id'])
    await pg.wait_for_timeout(300)
    await pg.evaluate("() => { const b = document.querySelector('[data-tact=\"approve\"]'); b && b.click(); }")
    await pg.wait_for_timeout(300)
    toast = await pg.evaluate(TOAST)
    st = await pg.evaluate(ST, [base['id'], auto])
    c.ok(st[0] == 'submitted' and 'overlap' in toast, f"overlap: the time drawer's Approve refuses and says why ({st}, {toast[:90]!r})")
    await pg.evaluate("() => { try { closeEditor(); } catch (e) {} view = 'time'; timeFilter = 'pending'; render(); }")
    await pg.wait_for_timeout(200)
    await pg.evaluate("() => { const b = document.getElementById('time-approve-all'); b && b.click(); }")
    await pg.wait_for_timeout(300)
    await pg.evaluate("() => { const b = document.querySelector('#mbm #mbm-ok'); b && b.click(); }")
    await pg.wait_for_timeout(300)
    toast = await pg.evaluate(TOAST)
    st = await pg.evaluate(ST, [base['id'], auto])
    c.ok(st[0] == 'submitted' and 'held' in toast and 'overlap' in toast, f"overlap: Approve All Shown leaves it and says it held one ({st}, {toast[:90]!r})")
    await pg.evaluate(CLOSE)
    # payroll: both punches stay out of a run, even approved behind the door; built from time, and typed by hand
    pay = await pg.evaluate("""([a, b]) => { DB.company.payAnchor = '2026-08-28'; const P = payPeriodOf(today());
      const A = DB.time.find(t => t.id === a), B = DB.time.find(t => t.id === b), was = [A.status, B.status];
      DB.time.filter(t => t.date >= P.from && t.date <= today() && t.out && !t.payrollId).forEach(t => (t.status = 'approved'));
      const run = payrollFromTime({ quiet: true });
      const one = { built: !!run, a: A.payrollId || '', b: B.payrollId || '', held: (run && run.held || []).map(x => [x.name, x.hours]), paid: DB.time.filter(t => run && t.payrollId === run.id).length };
      const hand = { id: 'pr_hand', period: 'typed by hand', from: P.from, to: today(), payDate: today(), entityId: entOfEmpId(A.empId), status: 'approved', approvals: [], gross: 1, taxes: 0, total: 1 };
      DB.payroll.push(hand); const L = prLinkTime(hand);
      const two = { linked: L.map(t => t.id).filter(id => id === a || id === b), a: A.payrollId || '', b: B.payrollId || '' };
      DB.payroll = DB.payroll.filter(r => r.id !== 'pr_hand'); DB.time.forEach(t => t.payrollId === 'pr_hand' && delete t.payrollId);
      [A.status, B.status] = was; save(); return { one, two }; }""", [base['id'], auto])
    c.ok(pay['one']['built'] and not pay['one']['a'] and not pay['one']['b'] and pay['one']['held'] and pay['one']['paid'] > 0, f"overlap: a run built from time holds both punches and pays the rest ({pay['one']})")
    c.ok(not pay['two']['linked'] and not pay['two']['a'] and not pay['two']['b'], f"overlap: a run typed by hand does not take them either ({pay['two']})")
    # the foreman picks from the Crew row: the kept punch can be approved, the other is never paid
    await sign_in(pg, 'u_angel'); await go(pg, 'fcrew')
    await tap(pg, '#fcrew-body [data-fwk] [data-tkgpick]')
    t = await mbm_text(pg)
    await shot(pg, 'overlap_pick_sheet')
    c.ok('Keep 7:12 AM to 4:48 PM' in t and 'Keep 12:00 PM to 1:00 PM' in t, f"overlap: Pick One on the Crew row opens the pick, both punches offered ({t[:120]!r})")
    await tap(pg, '#mbm [data-tkgk]', 'Keep 7:12 AM')
    await tap(pg, '#mbm #mbm-ok')
    await go(pg, 'fcrew')
    r = await pg.evaluate(PAIR, [base['id'], auto])
    st = await pg.evaluate(ST, [base['id'], auto])
    c.ok(st[1] == 'void' and not r['weekPick'] and not r['hoursPick'] and r['approve'] == [base['id']], f"overlap: picked, the other is voided and the kept punch offers Approve again ({st}, {r['approve']})")
    await tap(pg, f"#fcrew-body [data-fappr=\"{base['id']}\"]")
    st = await pg.evaluate(ST, [base['id'], auto])
    c.ok(st == ['approved', 'void'], f'overlap: and Approve goes through ({st})')


async def s_handoff(pg, c):
    """S2-4: the foreman hands a task that is not a schedule line to the crew on that job"""
    await sign_in(pg, 'u_angel'); await go(pg, 'ftoday')
    ok = await tap(pg, '#ftoday-body .f-mine .f-row .grow > b', 'Morning huddle') or await tap(pg, '#ftoday-body .f-mine [data-tkopen]', 'Morning huddle')
    t = await mbm_text(pg)
    c.ok(ok and 'Hand Off' in t, f"handoff: the foreman's Put on You task opens its sheet with Hand Off ({t[:60]!r})")
    kind = await pg.evaluate("() => { const R = tkResolve(tkSheetKey); return R ? R.x.kind : ''; }")
    c.ok(kind != 'sched', f'handoff: the task is not a schedule line ({kind!r})')
    await tap(pg, '#mbm [data-tkshandopen]')
    P = await pg.evaluate("() => [...document.querySelectorAll('#mbm [data-tkhto]')].map(b => [b.dataset.tkhto, Math.round(b.getBoundingClientRect().height)])")
    names = [x[0] for x in P]
    await shot(pg, 'handoff_people')
    crew = await pg.evaluate("() => DB.users.filter(u => /^(crew|driver)$/.test(u.role)).map(u => u.name)")
    c.ok(bool(crew) and all(n in names for n in crew), f"handoff: the crew and the driver are on the foreman's Hand Off ({names})")
    c.ok(names[:len(crew)] and set(names[:len(crew)]) == set(crew), f'handoff: they come first, before the office ({names[:4]})')
    c.ok(all(x[1] >= 44 for x in P), f'handoff: each person is a 44px target ({[x[1] for x in P][:4]})')
    title = await pg.evaluate("() => { const R = tkResolve(tkSheetKey); return R ? (R.x.title || '') : ''; }")
    await tap(pg, '#mbm [data-tkhto]', 'Alberto')
    await tap(pg, '#mbm #mbm-ok')
    toast = await pg.evaluate(TOAST)
    c.ok('Alberto' in toast, f'handoff: the toast says who it was offered to ({toast[:80]!r})')
    await sign_in(pg, 'u_alberto'); await go(pg, 'time')
    card = await pg.evaluate("() => { const c = document.querySelector('#v-time .tkr-offers'); return c ? c.innerText : ''; }")
    await shot(pg, 'handoff_crew_clock')
    c.ok('Morning huddle' in card and 'Accept' in card, f"handoff: the offer is on Alberto's Clock with Accept ({card[:90]!r})")
    if await tap(pg, '#v-time .tkr-offers [data-tkoffacc]'):
        mine = await pg.evaluate("() => (document.querySelector('#v-time .tkr-mine') || {}).innerText || ''")
        c.ok('Morning huddle' in mine, f'handoff: accepted, it is his ({mine[:80]!r})')
    # an office person's own task still lists the office only
    await sign_in(pg, 'u_alan')
    r = await pg.evaluate("""() => { const p = DB.projects.find(x => x.id === 'p121'); p.actions = p.actions || [];
      const a = { id: 'act_fc1', title: 'Call the architect about the stair', assignee: currentUser().name, status: 'open', due: today(), createdBy: currentUser().name, createdAt: appNowIso() };
      p.actions.push(a); save(); const R = tkResolve('action:act_fc1:p121') || tkResolve('act:act_fc1:p121'); return R ? tkPeopleFor(R).map(u => u.role) : null; }""")
    c.ok(r is None or not any(x in ('crew', 'driver') for x in r), f"handoff: a PM's own task still offers the office, not the crew ({r})")


async def s_receive(pg, c):
    """S2-5: the foreman's Site opens the one receive sheet"""
    await sign_in(pg, 'u_angel')
    await pg.evaluate("() => { setCurrent('p121'); view = 'fsite'; render(); }"); await pg.wait_for_timeout(400)
    r = await pg.evaluate("""() => { const cards = [...document.querySelectorAll('#fsite-body .card')], del = cards.filter(c => /^Deliveries/i.test((c.querySelector('h3') || {}).innerText || ''));
      const card = del[0], btn = card ? [...card.querySelectorAll('button')].find(b => b.getClientRects().length && /^Receive/.test(b.innerText.trim())) : null;
      const x = btn ? btn.getBoundingClientRect() : null;
      return { cards: del.length, text: card ? card.innerText.replace(/\\s+/g, ' ') : '', btn: btn ? btn.innerText.trim() : '', h: x ? Math.round(x.height) : 0,
               other: cards.filter(c => !del.includes(c) && /PO-2026-047/.test(c.innerText)).length, side: document.documentElement.scrollWidth - innerWidth,
               blue: [...document.querySelectorAll('#fsite-body .btn.primary')].filter(b => b.getClientRects().length).length }; }""")
    await shot(pg, 'receive_site')
    c.ok(r['cards'] == 1 and 'PO-2026-047' in r['text'] and '0 of 900 sf received' in r['text'] and r['btn'] == 'Receive', f"receive: Site's Deliveries card lists the order with Receive ({r['btn']!r}, {r['text'][:120]!r})")
    c.ok(r['other'] == 0, f"receive: the order is in one list on Site, not two ({r['other']})")
    c.ok(r['h'] >= 44 and r['side'] <= 0 and r['blue'] <= 1, f"receive: Receive is a 44px target, no sideways scroll, at most one blue button ({r})")
    await tap(pg, '#fsite-body .card button', 'Receive')
    s = await pg.evaluate("""() => { const m = document.getElementById('mbm'); if (!m) return null;
      return { title: (m.querySelector('h3, .mbm-hd') || {}).innerText || '', counts: [...m.querySelectorAll('[data-purq]')].map(i => i.value),
               conds: [...new Set([...m.querySelectorAll('.pu-conds [data-pucond], .pu-conds .pu-chip')].map(b => b.innerText.trim()))], slip: !!m.querySelector('[data-puslip]'), n: document.querySelectorAll('#mbm').length }; }""")
    await shot(pg, 'receive_sheet')
    c.ok(bool(s) and s['counts'] and s['slip'] and all(k in ' '.join(s['conds']) for k in ('Good', 'Short', 'Damaged', 'Wrong')), f"receive: it is the one receive sheet: a count per line, Good / Short / Damaged / Wrong, the slip's photo ({s})")
    if s:
        # the foreman counts 600 of the 900 sf, marks the line Short, photographs the slip
        await pg.fill('#mbm [data-purq]', '600')
        await tap(pg, '#mbm .pu-conds button', 'Short')
        await pg.evaluate("() => { const b = document.querySelector('#mbm #mbm-ok'); b && b.click(); }"); await pg.wait_for_timeout(300)
        c.ok(await pg.evaluate("() => !!document.getElementById('mbm') && !DB.pos.find(x => x.number === 'PO-2026-047').lines[0].received"), 'receive: it waits for the photo of the slip')
        await pg.locator('#mbm [data-puslip]').set_input_files(files=[{'name': 'slip.jpg', 'mimeType': 'image/jpeg', 'buffer': b'\xff\xd8\xff\xe0' + b'\x00' * 64 + b'\xff\xd9'}])
        await pg.evaluate("() => { const b = document.querySelector('#mbm #mbm-ok'); b && b.click(); }"); await pg.wait_for_timeout(700)
        po = await pg.evaluate("() => { const po = DB.pos.find(x => x.number === 'PO-2026-047'); return { rec: po.lines[0].received, st: po.status, claims: (po.issues || []).filter(i => i.claim).map(i => [i.type, i.qty]), slip: ((po.receipts || []).slice(-1)[0] || {}).slip || '' }; }")
        c.ok(po['rec'] == 600 and po['claims'] == [['short', 300]] and po['slip'], f"receive: 600 sf received, 300 claimed short, the slip on the receipt ({po})")
        await pg.evaluate("() => { view = 'fsite'; render(); }"); await pg.wait_for_timeout(300)
        b = await pg.evaluate("() => [...document.querySelectorAll('#fsite-body .f3-dels button')].filter(b => b.getClientRects().length).map(b => b.innerText.trim())")
        c.ok('Receive the Rest' in b, f'receive: the order now reads Receive the Rest ({b})')
    await pg.evaluate(CLOSE)
    # a material on the schedule with an open order behind it is received on the order's sheet, not ticked off
    m = await pg.evaluate("""() => { const p = DB.projects.find(x => x.id === 'p121'), po = DB.pos.find(x => x.number === 'PO-2026-047');
      const m = p.materials.find(x => x.status !== 'on-site' && x.when !== 'end' && x.eta) || p.materials[0]; m.po = po.number; m.eta = m.eta || today(); m.status = 'ordered'; save(); view = 'fsite'; render(); return m.id; }""")
    await pg.wait_for_timeout(300)
    ok = await tap(pg, f'#fsite-body [data-frecv="mat:{m}"]')
    s = await pg.evaluate("() => { const m = document.getElementById('mbm'); return m ? { counts: m.querySelectorAll('[data-purq]').length, slip: !!m.querySelector('[data-puslip]'), text: m.innerText.slice(0, 60) } : null; }")
    c.ok(ok and bool(s) and s['counts'] >= 1 and s['slip'], f"receive: a material with an open order behind it opens the order's receive sheet ({s})")
    await pg.evaluate(CLOSE)


async def s_today(pg, c):
    """S1 (crew review): no punch ends after the app's clock; Clock In looks at today before it punches"""
    r = await pg.evaluate("""() => { const now = appNowIso(), td = today(), first = td + 'T07:30:00';
      const field = new Set(DB.users.filter(u => /^(foreman|crew|driver)$/.test(u.role) || ['u_angel', 'u_alberto', 'u_alex', 'u_satish'].includes(u.id)).map(u => u.employeeId).filter(Boolean));
      const T = DB.time.filter(t => field.has(t.empId));
      const say = t => [t.id, empName(t.empId), t.in, t.out, t.status];
      return { now, n: T.length, ahead: T.filter(t => (t.out && t.out > now) || (t.in && t.in > now)).map(say),
               // the demo's clock reads 7:30 AM at the earliest: a closed punch for today would end after it at some hour
               today: T.filter(t => t.date === td && t.out && t.out > first).map(say), waiting: T.filter(t => t.status === 'submitted').length }; }""")
    c.ok(r['n'] > 0 and not r['ahead'], f"today: no punch of anyone who clocks ends (or starts) after the app's clock, {r['now'][11:16]} ({r['ahead']})")
    c.ok(not r['today'], f"today: a fresh demo has no closed day for today, at whatever hour it is opened ({r['today']})")
    c.ok(r['waiting'] >= 3, f"today: the foreman still has days waiting on approval ({r['waiting']})")
    for uid, view, sel in (('u_alberto', 'time', '#clock-in'), ('u_alex', 'time', '#clock-in')):
        await sign_in(pg, uid); await go(pg, view)
        await pg.evaluate("() => { window.getGeo = async () => null; delete currentUser().geoAck; }")
        r = await pg.evaluate("() => { const e = myEmp(); return { btn: (document.querySelector('#clock-in') || {}).innerText || '', rows: [...document.querySelectorAll('#time-table tr[data-edit]')].filter(x => x.getClientRects().length).length, mine: DB.time.filter(t => t.empId === e.id && t.date === today()).length }; }")
        c.ok(r['btn'] == 'Clock In' and r['mine'] == 0, f"today: {uid} starts the day not clocked in, with no entry for today ({r})")
        await tap(pg, sel)
        await pg.wait_for_timeout(500)
        r = await pg.evaluate("() => { const e = myEmp(), L = DB.time.filter(t => t.empId === e.id && t.date === today()); return { n: L.length, open: L.filter(t => !t.out).length, of: L.map(t => t.overlapOf || '').join(''), ov: tkTimeOverlaps(e.id).length, modal: !!document.getElementById('mbm'), toast: (document.getElementById('toast') || {}).innerText || '' }; }")
        await shot(pg, f'today_first_clockin_{uid}')
        c.ok(r['n'] == 1 and r['open'] == 1 and not r['of'] and r['ov'] == 0 and not r['modal'] and 'already' not in r['toast'], f"today: {uid}'s first Clock In is one clean punch, nothing for the foreman to sort out ({r})")
    # Alberto's day closes and is sent; Clock In again says so before it punches
    await sign_in(pg, 'u_alberto'); await go(pg, 'time')
    await pg.evaluate("""() => { const e = myEmp(), t = DB.time.find(x => x.empId === e.id && !x.out), td = today();
      t.in = td + 'T07:30:00'; t.out = td + 'T07:31:00'; t.status = 'submitted'; t.work = [{ projectId: t.projectId, code: '05', hours: 0.02, note: '' }]; save(); render(); }""")
    n0 = await pg.evaluate("() => DB.time.length")
    await tap(pg, '#clock-in')
    await pg.wait_for_timeout(300)
    t = await mbm_text(pg)
    await shot(pg, 'today_already_sent')
    c.ok('already sent for approval' in t and '7:30 AM to 7:31 AM' in t and 'Start Another Shift' in t and await pg.evaluate("() => DB.time.length") == n0, f'today: with the day closed and sent, Clock In says so and punches nothing ({t[:120]!r})')
    r = await pg.evaluate("() => { const b = document.querySelector('#mbm #mbm-ok'), k = document.querySelector('#mbm #mbm-cancel'); const h = e => e ? Math.round(e.getBoundingClientRect().height) : 0; return { ok: h(b), no: h(k), noText: k ? k.innerText : '', side: document.documentElement.scrollWidth - innerWidth }; }")
    c.ok(r['ok'] >= 44 and r['no'] >= 44 and r['noText'] == 'Not Now' and r['side'] <= 0, f'today: Start Another Shift and Not Now are 44px targets ({r})')
    await tap(pg, '#mbm #mbm-cancel')
    c.ok(await pg.evaluate("() => DB.time.length") == n0, 'today: Not Now punches nothing')
    await tap(pg, '#clock-in')
    await tap(pg, '#mbm #mbm-ok')
    await pg.wait_for_timeout(500)
    r = await pg.evaluate("n0 => { const e = myEmp(), nw = DB.time.find(t => t.empId === e.id && !t.out); return { n: DB.time.length - n0, of: nw ? nw.overlapOf || '' : 'none', ov: tkTimeOverlaps(e.id).length }; }", n0)
    c.ok(r['n'] == 1 and r['of'] == '' and r['ov'] == 0, f'today: Start Another Shift starts a second shift that overlaps nothing ({r})')
    # the automatic clock asks the same way
    await pg.evaluate("() => { const e = myEmp(); DB.time = DB.time.filter(t => !(t.empId === e.id && !t.out)); tkGeoAgree(currentUser()); }")
    n0 = await pg.evaluate("() => DB.time.length")
    res = await pg.evaluate(f"() => tkGeoTick({SITE}, today() + 'T09:00:00')")
    toast = await pg.evaluate(TOAST)
    c.ok(res.get('did') == 'asked' and await pg.evaluate("() => DB.time.length") == n0 and 'already sent for approval' in toast and 'Start Another Shift' in toast, f'today: the automatic clock asks too, and punches nothing ({res}, {toast[:80]!r})')
    await tap(pg, '#toast a, #toast button', 'Start Another Shift')
    r = await pg.evaluate("n0 => { const e = myEmp(), nw = DB.time.find(t => t.empId === e.id && !t.out); return { n: DB.time.length - n0, src: nw && nw.source, ov: tkTimeOverlaps(e.id).length }; }", n0)
    c.ok(r['n'] == 1 and r['src'] == 'geo' and r['ov'] == 0, f'today: Start Another Shift there makes the automatic punch ({r})')
    # a lunch break (closed, not sent) is not asked about
    await sign_in(pg, 'u_alex'); await go(pg, 'time')
    await pg.evaluate("() => { window.getGeo = async () => null; const e = myEmp(), t = DB.time.find(x => x.empId === e.id && !x.out), td = today(); t.in = td + 'T07:30:00'; t.out = td + 'T07:31:00'; t.status = 'open'; save(); render(); }")
    n0 = await pg.evaluate("() => DB.time.length")
    await tap(pg, '#clock-in')
    await pg.wait_for_timeout(500)
    r = await pg.evaluate("n0 => ({ n: DB.time.length - n0, modal: !!document.getElementById('mbm') })", n0)
    c.ok(r['n'] == 1 and not r['modal'], f'today: back from a break, Clock In just clocks in ({r})')


async def s_driver(pg, c):
    """S2 (crew review): the driver receives at the curb on the one receive sheet"""
    await sign_in(pg, 'u_alex'); await go(pg, 'route')
    r = await pg.evaluate("() => { const b = document.querySelector('#v-route [data-drvrecv]'); const x = b ? b.getBoundingClientRect() : null; return { views: (ROLE_VIEWS.driver || []).includes('recv'), btn: b ? b.innerText.trim() : '', h: x ? Math.round(x.height) : 0, side: document.documentElement.scrollWidth - innerWidth, blue: [...document.querySelectorAll('#v-route .btn.primary')].filter(e => e.getClientRects().length).length }; }")
    await shot(pg, 'driver_route')
    c.ok(r['views'] and r['btn'] == 'Receive a Delivery' and r['h'] >= 44 and r['side'] <= 0, f"driver: Route has Receive a Delivery, a 44px target ({r})")
    await tap(pg, '#v-route [data-drvrecv]')
    r = await pg.evaluate("() => { const row = [...document.querySelectorAll('#v-recv .recv-po')].find(e => /PO-2026-047/.test(e.innerText)); const b = row && [...row.querySelectorAll('button')].find(x => x.getClientRects().length && /^Receive/.test(x.innerText.trim())); const x = b ? b.getBoundingClientRect() : null; return { view, row: row ? row.innerText.replace(/\\s+/g, ' ').slice(0, 90) : '', btn: b ? b.innerText.trim() : '', h: x ? Math.round(x.height) : 0, sub: [...document.querySelectorAll('#v-recv .recv-po')].filter(e => /PO-2026-048/.test(e.innerText) && [...e.querySelectorAll('button')].some(x => /^Receive/.test(x.innerText.trim()))).length, side: document.documentElement.scrollWidth - innerWidth }; }")
    await shot(pg, 'driver_deliveries')
    c.ok(r['view'] == 'recv' and r['btn'] == 'Receive' and r['h'] >= 44 and r['side'] <= 0, f"driver: it opens Deliveries on every job, each order with Receive ({r})")
    c.ok(r['sub'] == 0, f"driver: a subcontract has no Receive ({r['sub']})")
    await pg.evaluate("() => { const row = [...document.querySelectorAll('#v-recv .recv-po')].find(e => /PO-2026-047/.test(e.innerText)); const b = row && [...row.querySelectorAll('button')].find(x => x.getClientRects().length && /^Receive/.test(x.innerText.trim())); b && b.setAttribute('data-fc-go', '1'); }")
    await tap(pg, '[data-fc-go]')
    s = await pg.evaluate("""() => { const m = document.getElementById('mbm'); if (!m) return null;
      return { counts: [...m.querySelectorAll('[data-purq]')].map(i => i.value), conds: [...new Set([...m.querySelectorAll('.pu-conds button')].map(b => b.innerText.trim()))].join(' '), slip: !!m.querySelector('[data-puslip]'), n: document.querySelectorAll('#mbm').length }; }""")
    await shot(pg, 'driver_sheet')
    c.ok(bool(s) and s['counts'] and s['slip'] and s['n'] == 1 and all(k in s['conds'] for k in ('Good', 'Short', 'Damaged', 'Wrong')), f"driver: Receive is the one receive sheet: counts, Good / Short / Damaged / Wrong, the slip's photo ({s})")
    if s:
        await pg.fill('#mbm [data-purq]', '900')
        await tap(pg, '#mbm .pu-conds button', 'Damaged')
        await pg.fill('#mbm [data-pubad]', '40')
        await pg.locator('#mbm [data-puslip]').set_input_files(files=[{'name': 'slip.jpg', 'mimeType': 'image/jpeg', 'buffer': b'\xff\xd8\xff\xe0' + b'\x00' * 64 + b'\xff\xd9'}])
        await pg.evaluate("() => { const b = document.querySelector('#mbm #mbm-ok'); b && b.click(); }"); await pg.wait_for_timeout(700)
        po = await pg.evaluate("() => { const po = DB.pos.find(x => x.number === 'PO-2026-047'); return { rec: po.lines[0].received, claims: (po.issues || []).filter(i => i.claim).map(i => [i.type, i.qty]), slip: ((po.receipts || []).slice(-1)[0] || {}).slip || '', by: ((po.issues || []).slice(-1)[0] || {}).by || '' }; }")
        c.ok(po['rec'] == 860 and po['claims'] == [['damaged', 40]] and po['slip'] and 'Alex' in po['by'], f"driver: 860 sf received good, 40 claimed damaged, the slip on the receipt, by the driver ({po})")
    await pg.evaluate(CLOSE)


async def s_donephoto(pg, c):
    """S2 (crew review): Done offers a photo; one tap opens the camera; skipped unless the task needs proof"""
    await sign_in(pg, 'u_alberto'); await go(pg, 'time')
    PH = "id => { const x = (tkResolve(`sched:${id}:p121`) || {}).x; return x ? tdyPhotosFor(x).length : -1; }"
    ST = "id => DB.projects.find(p => p.id === 'p121').tasks.find(t => t.id === id).status"
    await pg.evaluate("() => { window.__cam = 0; window.mReadPhoto = (cb) => { window.__cam++; cb('data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP'); }; }")
    p0 = {k: await pg.evaluate(PH, k) for k in ('frame', 'win', 'ext')}
    ok = await tap(pg, '#fm-today [data-fm-done="frame"]')
    await pg.wait_for_timeout(300)
    t = await pg.evaluate("() => ({ text: (document.getElementById('toast') || {}).innerText || '', acts: [...document.querySelectorAll('#toast a, #toast button')].filter(e => e.getClientRects().length).map(e => [e.innerText.trim(), Math.round(e.getBoundingClientRect().height), Math.round(e.getBoundingClientRect().width)]), side: document.documentElement.scrollWidth - innerWidth })")
    await shot(pg, 'donephoto_offer')
    c.ok(ok and await pg.evaluate(ST, 'frame') == 'done', 'donephoto: Done is still one tap')
    c.ok('marked done' in t['text'] and any(a[0] == 'Add a Photo' for a in t['acts']) and any(a[0] == 'Undo' for a in t['acts']), f"donephoto: the toast offers a photo, with Undo ({t['text'][:80]!r}, {t['acts']})")
    c.ok(all(a[1] >= 44 and a[2] >= 44 for a in t['acts']) and t['side'] <= 0, f"donephoto: Add a Photo and Undo are 44px targets ({t['acts']})")
    await tap(pg, '#toast a, #toast button', 'Add a Photo')
    await pg.wait_for_timeout(300)
    r = {'cam': await pg.evaluate("() => window.__cam"), 'n': await pg.evaluate(PH, 'frame'), 'toast': await pg.evaluate(TOAST)}
    c.ok(r['cam'] == 1 and r['n'] == p0['frame'] + 1 and 'Photo added' in r['toast'], f'donephoto: one tap opens the camera and the photo lands on the task ({r})')
    # skipping it: the next task is done with no photo, and that is allowed
    ok = await tap(pg, '#fm-today [data-fm-done="win"]')
    await pg.wait_for_timeout(300)
    c.ok(ok and await pg.evaluate(ST, 'win') == 'done' and await pg.evaluate(PH, 'win') == p0['win'], 'donephoto: the photo can be skipped: the task is done without one')
    await tap(pg, '#toast a, #toast button', 'Undo')
    c.ok(await pg.evaluate(ST, 'win') != 'done', 'donephoto: Undo on the offer puts the task back')
    # a task that needs proof still stops for the photo before it is done
    await pg.evaluate("() => { const t = DB.projects.find(p => p.id === 'p121').tasks.find(t => t.id === 'demo'); const R = tkResolve('sched:demo:p121'); R.rec.needsPhoto = true; save(); render(); }")
    await tap(pg, '#fm-today [data-fm-done="demo"]')
    await pg.wait_for_timeout(300)
    t = await mbm_text(pg)
    c.ok('Proof Needed' in t and await pg.evaluate(ST, 'demo') != 'done', f'donephoto: a task that needs a photo is not done until it has one ({t[:60]!r})')
    await pg.evaluate(CLOSE)
    # the task sheet's Done offers it too (the foreman, from a row's sheet)
    await sign_in(pg, 'u_angel'); await go(pg, 'ftoday')
    await pg.evaluate("() => { window.__cam = 0; window.mReadPhoto = (cb) => { window.__cam++; cb('data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP'); }; tkSheet('sched:ext:p121'); }")
    await pg.wait_for_timeout(300)
    ok = await tap(pg, '#mbm [data-tksdone]')
    await pg.wait_for_timeout(400)
    t = await pg.evaluate(TOAST)
    c.ok(ok and await pg.evaluate(ST, 'ext') == 'done' and 'Add a Photo' in t, f"donephoto: the task sheet's Done offers the photo too ({t[:80]!r})")
    await tap(pg, '#toast a, #toast button', 'Add a Photo')
    await pg.wait_for_timeout(300)
    c.ok(await pg.evaluate(PH, 'ext') == p0['ext'] + 1, 'donephoto: and the photo lands on that task')


SECTIONS = {'switch': s_switch, 'list': s_list, 'overlap': s_overlap, 'handoff': s_handoff, 'receive': s_receive, 'today': s_today, 'driver': s_driver, 'donephoto': s_donephoto}


async def main():
    c = Checks()
    want = [a for a in sys.argv[1:] if a in SECTIONS or a == 'watch'] or list(SECTIONS) + ['watch']
    async with async_playwright() as p:
        for name in want:
            if name == 'watch':
                try:
                    await s_watch(p, c)
                except Exception as e:
                    c.ok(False, f'watch: stopped: {str(e)[:200]}')
                continue
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
