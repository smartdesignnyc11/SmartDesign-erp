"""feedback_session_test: Record a Feedback Session (Alan, 2026-10-26), done as the person does it, on the desktop
(1440x900, the owner) and the phone (390x844 with touch, the coordinator).

"One of the best ways to improve this site is for me to record my screen and talk about what is working and what
isn't. Create the same start meeting feature to record exactly where in the site I am and what I'm clicking and looking
at, with a time stamp that matches my transcript time stamp."

  WAYS IN    every staff role has Record a Feedback Session at the foot of the menu and in Report a Problem, phone and
             desktop; a client has neither
  RECORD     start from the menu, the bar shows the time, Mark, Pause and Finish and says "Start your recording now, then
             tap Mark and say 'mark one' so the two line up"; Mark; go to Tasks by the menu; tap New Task (a sheet);
             type a secret into its Title; close it; go to a second page; scroll; Pause (nothing logged), Resume; a page
             error and a failed save; Mark again; RELOAD mid-session and see it carry on; one more page; Finish with a
             title; the toast's Open lands on the session's page
  THE LOG    every step is there (start, pages with their heading and tab, the sheet on top, taps with their label, kind,
             section and what followed, typing as label and length, the scroll, the marks, the reload, the error, the
             failed save, the finish); times rise; every stamp is the device's ISO time with zone and milliseconds; the
             typed value is nowhere (the session, the downloads)
  TRANSCRIPT four invented transcripts (WebVTT uploaded as a file, SRT, a Google Meet doc, plain "[m:ss]" lines),
             written from the session's own marks, pages and taps; each lines up by Mark and by offset; each line sits
             on the right page with the right taps; a clock-time transcript lines up by the clock; nudge moves it
  TIMELINE   one screen of groups by page, every line shown, a finding flag sticks; Export Timeline gives a Markdown and
             a JSON file that parse; Download Session gives one JSON file that parses
  PROBLEMS   the finished session is a Problem Report of kind "session" on Problem Reports (the owner), private to its
             person; nothing new in the menu
  PHONE      the bar fits at 390 (no sideways scroll, targets 44px and 8px apart), the page reads at 390
Screenshots: review/feedback_session/. Usage: python3 feedback_session_test.py [--desktop|--phone]
"""
import asyncio, json, math, os, re, sys
from datetime import datetime
from harness import *

SHOTS = os.path.join(ROOT, 'review', 'feedback_session')
os.makedirs(SHOTS, exist_ok=True)
SECRET = 'Zebra-778899 $12,345.67'
HINT = "Start your recording now, then tap Mark and say 'mark one' so the two line up."
STAFF = ['u_owner', 'u_alan', 'u_chen', 'u_angel', 'u_alberto', 'u_alex', 'u_sarah', 'u_billing', 'u_controller']
ISO = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}[+-]\d{2}:\d{2}$')
WORDS = ['zero', 'one', 'two', 'three', 'four', 'five']

async def wait(pg, ms=300): await pg.wait_for_timeout(ms)

async def live(pg):
    return await pg.evaluate("() => fbsLive ? JSON.parse(JSON.stringify(fbsLive)) : null")

async def tap(pg, sel, phone):
    loc = pg.locator(sel).first
    try:
        await loc.scroll_into_view_if_needed(timeout=8000)
        if phone: await loc.tap(timeout=8000)
        else: await loc.click(timeout=8000)
    except Exception as e:
        await pg.screenshot(path=os.path.join(SHOTS, f'{"phone" if phone else "desktop"}_FAILED_tap.png'))
        raise SystemExit(f'could not tap {sel}: {str(e).splitlines()[0]}')
    await wait(pg, 250)

async def nav_to(pg, grp, phone):
    """By the menu, as a person: the rail on the desktop; the menu button, then the group, on the phone."""
    if phone:
        # the menu button: the header's, or the Tasks page's own header on the phone
        await tap(pg, '#menu-btn:visible, .tv-phmenu:visible', phone)
        await wait(pg, 300)
    await tap(pg, f'#nav-groups button[data-grp="{grp}"]', phone)
    await wait(pg, 900)
    # a group that opens to its pages on the phone: its first page
    if phone and await pg.evaluate("() => document.querySelector('.rail.open, .rail.on') !== null"):
        await pg.evaluate("() => { document.querySelector('.rail')?.classList.remove('open'); document.getElementById('railscrim')?.classList.remove('on'); }")
        await wait(pg, 200)

def mk_vtt(lines):
    out = ['WEBVTT', '', 'NOTE invented for the test', '']
    for i, (sec, spk, text) in enumerate(lines):
        out += [str(i + 1), f'{hms(sec, ".")} --> {hms(sec + 1.5, ".")}', f'<v {spk}>{text}</v>', '']
    return '\n'.join(out)

def mk_srt(lines):
    out = []
    for i, (sec, spk, text) in enumerate(lines):
        out += [str(i + 1), f'{hms(sec, ",")} --> {hms(sec + 1.5, ",")}', f'{spk}: {text}', '']
    return '\n'.join(out)

def mk_meet(lines):
    out = ['Feedback walk - Transcript', '', 'Attendees', 'Invented Person', '', 'Transcript', '']
    for sec, spk, text in lines:
        out += [hms(sec), f'{spk}: {text}']
    out += ['', 'Transcription ended after 00:10:00']
    return '\n'.join(out)

def mk_plain(lines):
    return '\n'.join(f'[{int(sec // 60)}:{int(sec % 60):02d}] {text}' for sec, spk, text in lines)

def hms(sec, ms_sep=None):
    s = int(math.floor(sec)); ms = int(round((sec - s) * 1000))
    if ms == 1000: s += 1; ms = 0
    base = f'{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}'
    return base + (f'{ms_sep}{ms:03d}' if ms_sep else '')

def script_from(sess, t0, whole):
    """The words a person would have said, at the recording's own times: "mark one" at t0 and "mark two" as the second
    mark is tapped, then a line just after each page and each tap, from the session's own log. whole: the format writes
    whole seconds (rounded up). Returns the lines, what each is about, and the session second each was truly said."""
    E = sess['events']
    m1 = next(e for e in E if e['k'] == 'mark' and e['no'] == 1)
    rec = lambda t: t0 + (t - m1['t'])
    lines, want, true = [(t0, 'Invented Person', 'Okay. Mark one.')], [None], [m1['t']]
    for e in E:
        if e['t'] <= m1['t'] + 0.05: continue
        if e['k'] == 'mark':
            lines.append((rec(e['t']), 'Invented Person', f'Mark {WORDS[e["no"]]}.')); want.append(None); true.append(e['t'])
        elif e['k'] == 'nav':
            lines.append((rec(e['t']) + 0.8, 'Invented Person', f'Now this page, {e["heading"]}, line {len(lines) + 1}.')); want.append(('nav', e)); true.append(e['t'] + 0.8)
        elif e['k'] == 'tap':
            lines.append((rec(e['t']) + 0.3, 'Invented Person', f'I tapped {e["label"]} here, line {len(lines) + 1}.')); want.append(('tap', e)); true.append(e['t'] + 0.3)
    if whole: lines = [(float(math.ceil(round(s, 3))), p, t) for s, p, t in lines]
    order = sorted(range(len(lines)), key=lambda i: lines[i][0])
    return [lines[i] for i in order], [want[i] for i in order], [true[i] for i in order]

def mark_rule(sess, lines):
    """The documented rule for By Mark: each "mark N" said pairs with Mark N tapped; marks within 1.5 s of each other
    are one shift (their mean), otherwise each mark sets the shift for the lines after it."""
    marks = {e['no']: e['t'] for e in sess['events'] if e['k'] == 'mark'}
    A = []
    for sec, _, text in lines:
        m = re.search(r'\bmark (one|two|three|four|five)\b', text, re.I)
        if m:
            no = WORDS.index(m.group(1).lower())
            if no in marks and all(a[0] != no for a in A): A.append((no, sec, marks[no] - sec))
    A.sort(key=lambda a: a[1])
    O = [a[2] for a in A]
    if max(O) - min(O) <= 1.5:
        mean = sum(O) / len(O)
        return lambda sec: sec + mean
    def f(sec):
        o = A[0][2]
        for a in A:
            if a[1] <= sec: o = a[2]
        return sec + o
    return f

def expect_rows(sess, lines, want, true, rule, c, tag, rows):
    """Each line's time by the rule, then its page and taps from the raw log by the person's own sense (the page they
    were on when they said it; the taps a few seconds around it), compared with what the app's timeline paired. A line
    whose rounded time crosses a page change (or sits within half a second of one) is ambiguous by nature: not graded."""
    navs = [e for e in sess['events'] if e['k'] == 'nav']
    page_at = lambda x: ([n for n in navs if n['t'] <= x] or [None])[-1]
    c.ok(len(rows) == len(lines), f'{tag}: {len(rows)} timeline rows for {len(lines)} lines')
    checked = 0
    for i, ((sec, spk, text), w) in enumerate(zip(lines, want)):
        if i >= len(rows): break
        r = rows[i]
        t = rule(sec)
        c.ok(abs(r['t'] - t) < 0.01, f'{tag}: line {i + 1} at {r["t"]} s in the session, expected {t:.3f}')
        c.ok(r['said'].strip() == text.strip(), f'{tag}: line {i + 1} reads "{r["said"]}", expected "{text}"')
        if not w: continue
        page = page_at(t)
        if page is None or page is not page_at(true[i]) or any(abs(n['t'] - t) < 0.5 for n in navs): continue
        got = (r.get('page') or {})
        c.ok(got.get('heading') == page['heading'] and (got.get('over') or {}).get('title') == ((page.get('over') or {}).get('title')),
             f'{tag}: line {i + 1} "{text}" paired with page {got.get("heading")!r}/{(got.get("over") or {}).get("title")!r}, expected {page["heading"]!r}/{(page.get("over") or {}).get("title")!r}')
        if w[0] == 'tap':
            labels = [x.get('label') for x in r['taps']]
            c.ok(w[1]['label'] in labels, f'{tag}: line {i + 1} should show the tap "{w[1]["label"]}" (got {labels})')
        checked += 1
    c.ok(checked >= 4, f'{tag}: only {checked} lines could be graded against a page')

async def add_transcript(pg, phone, text=None, file=None, start=None):
    await tap(pg, '[data-fbstx]', phone)
    await wait(pg, 300)
    if file:
        await pg.set_input_files('#fbs-file', files=[file])
        await pg.wait_for_function("() => (document.getElementById('fbs-text') || {}).value", timeout=5000)
    else:
        await pg.fill('#fbs-text', text)
    if start: await pg.fill('#fbs-start', start)
    await tap(pg, '#mbm-ok', phone)
    await wait(pg, 500)

async def timeline(pg, sid):
    return await pg.evaluate("id => { const T = fbsTimeline(fbsGet(id)); return {how: T.align.how, say: T.align.say, nudge: T.align.nudge, rows: T.rows.map(r => ({t: r.t, said: r.said, page: r.page, taps: r.taps.map(e => ({label: e.label, k: e.k}))})), groups: T.groups.length}; }", sid)

async def run(p, phone, c, only_ways=False):
    dev = 'phone' if phone else 'desktop'
    b, pg, errs = await open_app(p, phone)
    # ---- WAYS IN: every staff role, both places; a client has none
    for u in STAFF + ['u_klein']:
        await sign_in(pg, u)
        r = await pg.evaluate("""() => { const rail = document.getElementById('fbs-rail'); rpOpen(); const inRp = !!document.querySelector('#rp-panel [data-fbsstart]'); rpClose();
          return {rail: !!rail, label: rail ? rail.textContent.trim() : '', inRp, views: (ROLE_VIEWS[role()] || []).includes('fbs')}; }""")
        if u == 'u_klein':
            c.ok(not r['rail'] and not r['inRp'] and not r['views'], f'{dev} client: no feedback session ({r})')
        else:
            c.ok(r['rail'] and r['label'] == 'Record a Feedback Session', f'{dev} {u}: Record a Feedback Session at the foot of the menu ({r})')
            c.ok(r['inRp'], f'{dev} {u}: Record a Feedback Session in Report a Problem')
            c.ok(r['views'], f'{dev} {u}: the session page opens for this role')
    if only_ways:
        await b.close(); return
    # nothing new in the menu: the rail reads as before for the person below
    uid = 'u_chen' if phone else 'u_owner'
    await sign_in(pg, uid)
    await pg.evaluate("() => { localStorage.removeItem('sdp:reports'); DB.rpSessions = []; save(); }")
    del errs[:]
    rail_before = await pg.evaluate("() => [...document.querySelectorAll('#nav-groups button[data-grp]')].map(b => b.dataset.grp)")
    c.ok('fbs' not in json.dumps(rail_before), f'{dev}: no menu entry for sessions')

    # ---- RECORD: start from the menu's foot, as a person
    if phone: await tap(pg, '#menu-btn', phone); await wait(pg, 300)
    await tap(pg, '#fbs-rail', phone)
    await wait(pg, 400)
    bar = await pg.evaluate("""() => { const b = document.getElementById('fbs-bar'); if (!b) return null; const r = b.getBoundingClientRect();
      const btns = [...b.querySelectorAll('button')].map(x => { const q = x.getBoundingClientRect(); return {l: x.getAttribute('aria-label'), h: q.height, x: q.left, r: q.right, y: q.top}; });
      return {text: b.innerText, top: r.top, bottom: r.bottom, left: r.left, right: r.right, btns, sw: document.documentElement.scrollWidth, w: innerWidth}; }""")
    c.ok(bar is not None, f'{dev}: the bar shows once the session starts')
    if bar:
        c.ok(HINT in bar['text'], f'{dev}: the bar says how to line it up: {bar["text"][:160]!r}')
        c.ok([x['l'] for x in bar['btns']] == ['Mark', 'Pause', 'Finish'], f'{dev}: the bar holds Mark, Pause and Finish ({[x["l"] for x in bar["btns"]]})')
        c.ok(re.search(r'\b00:0\d\b', bar['text']) is not None, f'{dev}: the bar shows the time recorded')
        c.ok(all(x['h'] >= 44 for x in bar['btns']), f'{dev}: the bar\'s buttons are 44px tall ({[x["h"] for x in bar["btns"]]})')
        gaps = [bar['btns'][i + 1]['x'] - bar['btns'][i]['r'] for i in range(len(bar['btns']) - 1)]
        c.ok(all(g >= 8 for g in gaps), f'{dev}: the bar\'s buttons are 8px apart ({gaps})')
        c.ok(bar['right'] <= bar['w'] and bar['left'] >= 0 and bar['sw'] <= bar['w'], f'{dev}: the bar fits the screen ({bar["left"]}-{bar["right"]} of {bar["w"]}, page {bar["sw"]})')
    await pg.screenshot(path=os.path.join(SHOTS, f'{dev}_1_started.png'))
    await tap(pg, '[data-fbsmark]', phone)
    await wait(pg, 600)
    flash = await pg.evaluate("() => document.getElementById('fbs-bar').innerText")
    c.ok('Mark 1' in flash and 'mark one' in flash, f'{dev}: Mark says which mark to say aloud ({flash[:120]!r})')

    # a page by the menu, a tap that opens a sheet, typing into it
    await nav_to(pg, 'mytasks', phone)
    st = await pg.evaluate("() => view")
    c.ok(st == 'tkall', f'{dev}: the menu took us to Tasks ({st})')
    new_sel = '#tk-new' if not phone else '.tv-qa-plus'
    has_new = await pg.evaluate("s => !!document.querySelector(s)", new_sel)
    if has_new:
        await tap(pg, new_sel, phone)
    else:
        await pg.evaluate("() => mbModal('New Task', '<div class=\"f\"><label>Title</label><input data-f=\"title\"></div>', {submit: 'Save'})")
    await wait(pg, 500)
    title_sel = '#mbm textarea[data-tvqatext]' if phone else '#mbm input[data-f="title"]'
    field_label = 'Say or type the task' if phone else 'Title'
    c.ok(await pg.evaluate("s => !!document.querySelector(s)", title_sel), f'{dev}: New Task opened its sheet')
    await pg.locator(title_sel).click()
    await pg.locator(title_sel).press_sequentially(SECRET, delay=15)
    await wait(pg, 300)
    await pg.screenshot(path=os.path.join(SHOTS, f'{dev}_2_sheet.png'))
    await pg.keyboard.press('Escape')
    await wait(pg, 600)
    c.ok(not await pg.evaluate("() => !!document.getElementById('mbm')"), f'{dev}: the sheet closed')
    # a second page, and a scroll that changes what is in view
    await nav_to(pg, 'buy', phone)
    await wait(pg, 400)
    if not phone: await pg.mouse.move(820, 520)
    for _ in range(4):
        # the wheel on a wide screen; on the phone the page's own scroller (the body) moves, as a swipe moves it
        await pg.mouse.wheel(0, 700) if not phone else await pg.evaluate("() => { const b = document.body; (b.scrollHeight > b.clientHeight + 2 ? b : document.scrollingElement).scrollTop += 700; }")
        await wait(pg, 250)
    await wait(pg, 900)
    # Pause: nothing is logged; Resume
    await tap(pg, '[data-fbspause]', phone)
    n_paused = len((await live(pg))['events'])
    await nav_to(pg, 'home', phone)
    await wait(pg, 600)
    s_ = await live(pg)
    c.ok(s_['paused'] and len(s_['events']) == n_paused, f'{dev}: nothing is recorded while paused ({len(s_["events"])} vs {n_paused})')
    await tap(pg, '[data-fbspause]', phone)
    await wait(pg, 500)
    # a page error and a failed save are in the log
    await pg.evaluate("() => setTimeout(() => { throw new Error('Invented failure 42 for the test'); }, 0)")
    await wait(pg, 400)
    cover = await pg.evaluate("""() => { const t = document.getElementById('toast'), b = document.getElementById('fbs-bar'); if (!t.classList.contains('on')) return 'no toast';
      const r = t.getBoundingClientRect(), q = b.getBoundingClientRect(); return r.bottom > q.top && r.top < q.bottom && r.right > q.left && r.left < q.right ? `toast ${Math.round(r.top)}-${Math.round(r.bottom)} over bar ${Math.round(q.top)}-${Math.round(q.bottom)}` : ''; }""")
    c.ok(cover == '', f'{dev}: a toast never sits on the bar ({cover})')
    await pg.evaluate("() => { saveState.ok = false; saveState.msg = 'Invented: storage refused the save'; saveStatus(); saveState.ok = true; saveState.msg = ''; saveStatus(); }")
    await wait(pg, 200)
    errs[:] = [e for e in errs if 'Invented failure 42' not in e]
    await tap(pg, '[data-fbsmark]', phone)
    await wait(pg, 800)
    before = await live(pg)
    sid = before['id']
    # ---- RELOAD mid-session: it carries on
    await pg.reload()
    await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
    await pg.wait_for_function("() => !!document.getElementById('fbs-bar')", timeout=10000)
    await wait(pg, 600)
    after = await live(pg)
    c.ok(after and after['id'] == sid and len(after['events']) > len(before['events']) and any(e['k'] == 'reload' for e in after['events']),
         f'{dev}: after a reload the same session carries on with its log ({after and after["id"]}, {after and len(after["events"])} events, was {len(before["events"])})')
    c.ok(after and after['events'][:len(before['events'])] == before['events'], f'{dev}: the log written before the reload is kept whole')
    # one more page and a tap after the reload
    await nav_to(pg, 'mytasks', phone)
    await wait(pg, 700)
    # ---- FINISH with a title; the toast's Open lands on the session
    await tap(pg, '[data-fbsfinish]', phone)
    await wait(pg, 300)
    await pg.fill('#fbs-title', f'Tasks and purchasing on the {dev}')
    await tap(pg, '#mbm-ok', phone)
    await wait(pg, 400)
    toast = await pg.evaluate("() => document.getElementById('toast').innerText")
    c.ok(f'Feedback session {sid} saved' in toast and 'Open' in toast, f'{dev}: Finish toasts what was saved with Open ({toast!r})')
    await pg.locator('#toast .toast-open').first.click()
    await wait(pg, 600)
    st = await pg.evaluate("() => ({view, h: document.querySelector('#v-fbs h2')?.innerText, bar: !!document.getElementById('fbs-bar'), idb: null})")
    c.ok(st['view'] == 'fbs' and st['h'] == 'Feedback Session', f'{dev}: Open lands on the session\'s page ({st})')
    c.ok(not st['bar'], f'{dev}: the bar goes once the session is finished')
    left = await pg.evaluate("async () => await idbGet('fbs:live')")
    c.ok(left is None, f'{dev}: nothing is left recording on the device')
    await pg.screenshot(path=os.path.join(SHOTS, f'{dev}_3_session_log.png'), full_page=False)

    # ---- THE LOG
    sess = await pg.evaluate("id => JSON.parse(JSON.stringify(fbsGet(id)))", sid)
    c.ok(sess and sess['kind'] == 'session' and sess['owner'] == uid and sess['title'] == f'Tasks and purchasing on the {dev}', f'{dev}: a Problem Report of kind session, owned by its person, with the title typed')
    E = sess['events']
    kinds = [e['k'] for e in E]
    for k in ['start', 'nav', 'tap', 'type', 'scroll', 'mark', 'reload', 'error', 'finish']:
        c.ok(k in kinds, f'{dev}: the log has a {k} step ({sorted(set(kinds))})')
    c.ok(kinds.count('mark') == 2 and [e['no'] for e in E if e['k'] == 'mark'] == [1, 2], f'{dev}: two marks, numbered')
    c.ok(all(E[i]['t'] <= E[i + 1]['t'] for i in range(len(E) - 1)), f'{dev}: the times rise')
    c.ok(all(ISO.match(e['at']) for e in E), f'{dev}: every step carries the device time with its zone and milliseconds ({E[0]["at"]})')
    ats = [datetime.fromisoformat(e['at']) for e in E]
    c.ok(all(ats[i] <= ats[i + 1] for i in range(len(ats) - 1)), f'{dev}: the wall-clock times rise')
    c.ok(all(abs((ats[i] - ats[0]).total_seconds() - (E[i]['t'] - E[0]['t'])) < 0.01 for i in range(len(E))), f'{dev}: seconds since the start match the wall clock')
    navs = [e for e in E if e['k'] == 'nav']
    heads = [e['heading'] for e in navs]
    c.ok('Tasks' in heads, f'{dev}: the Tasks page is in the log ({heads})')
    c.ok(any(e.get('over') and e['over']['title'] == 'New Task' for e in navs), f'{dev}: the New Task sheet on top is in the log')
    c.ok(all(e.get('role') and e.get('device') == dev for e in navs), f'{dev}: every page carries the role and the device')
    c.ok(any(e.get('tab') for e in navs), f'{dev}: the tab is in the log')
    taps = [e for e in E if e['k'] == 'tap']
    c.ok(any(e['label'] == 'Tasks' and e['ctl'] == 'menu' for e in taps), f'{dev}: the menu tap is logged with its label and kind ({[(e["label"], e["ctl"]) for e in taps][:8]})')
    nt = [e for e in taps if (e.get('then') or {}).get('screen', '').endswith('New Task') and (e.get('then') or {}).get('moved')]
    c.ok(nt and re.search(r'new task', nt[0]['label'], re.I), f'{dev}: the tap that opened New Task is logged with its label and the sheet it opened ({nt[:1]})')
    c.ok(all('where' in e for e in taps), f'{dev}: every tap says where it sat')
    ty = [e for e in E if e['k'] == 'type']
    c.ok(ty and ty[0]['field'] == field_label and ty[0]['len'] == len(SECRET), f'{dev}: typing is the field and the length ({ty[:1]})')
    c.ok(any(e['k'] == 'error' and e.get('what') == 'page' and 'Invented failure 42' in e['msg'] for e in E), f'{dev}: the page error is in the log')
    c.ok(any(e['k'] == 'error' and e.get('what') == 'save' for e in E), f'{dev}: the failed save is in the log')
    c.ok(any(e['k'] == 'scroll' and e.get('inView') for e in E), f'{dev}: the scroll names the headings in view')
    raw = json.dumps(sess)
    c.ok('Zebra' not in raw and '778899' not in raw and '12,345' not in raw, f'{dev}: the typed value is nowhere in the session')
    c.ok(sess['at'].startswith('2026-09-03'), f'{dev}: the report itself is stamped on the app clock ({sess["at"]})')

    # ---- PROBLEMS: one list, the person's own
    if not phone:
        await go(pg, 'rpbox')
        await wait(pg, 300)
        card = await pg.evaluate("id => { const c = document.querySelector(`.rp-card[data-rpid='${id}']`); return c ? c.innerText : null; }", sid)
        c.ok(card is not None and 'Feedback Session' in card and 'Open Session' in card, f'{dev}: the session is on Problem Reports ({(card or "")[:120]!r})')
        c.ok(await pg.evaluate("() => !!document.querySelector('#v-rpbox [data-fbsstart]')"), f'{dev}: Problem Reports offers Record a Feedback Session')
        await pg.screenshot(path=os.path.join(SHOTS, f'{dev}_4_problem_reports.png'))
        await sign_in(pg, 'u_alan')
        mine = await pg.evaluate("id => rpAll().some(r => r.id === id)", sid)
        c.ok(not mine, f'{dev}: another person never sees the session')
        await sign_in(pg, uid)
        await pg.locator(f".rp-card[data-rpid='{sid}'] [data-fbsopen]").first.click() if await pg.evaluate("() => view") == 'rpbox' else await pg.evaluate("id => fbsOpen(id)", sid)
        await wait(pg, 400)
        c.ok(await pg.evaluate("() => view") == 'fbs', f'{dev}: Open Session opens it')

    # ---- DOWNLOAD SESSION
    async with pg.expect_download() as dl:
        await tap(pg, '[data-fbsdlnow]', phone)
    d = await dl.value
    path = os.path.join(SHOTS, f'{dev}_{d.suggested_filename}')
    await d.save_as(path)
    data = json.load(open(path, encoding='utf-8'))
    c.ok(data.get('format') == 'smartdesigns-feedback-session' and data['id'] == sid and len(data['events']) == len(E), f'{dev}: Download Session saves one JSON file of the session ({d.suggested_filename})')
    c.ok('Zebra' not in open(path, encoding='utf-8').read(), f'{dev}: the typed value is not in the download')

    # ---- TRANSCRIPTS: four shapes, each by Mark and by offset
    m1 = next(e for e in E if e['k'] == 'mark' and e['no'] == 1)
    T0 = 4.0
    forms = [('WebVTT', mk_vtt, False, 'file'), ('SRT', mk_srt, False, 'paste'), ('Google Meet doc', mk_meet, True, 'paste'), ('timed lines', mk_plain, True, 'paste')]
    for fmt, maker, whole, how in forms:
        lines, want, true = script_from(sess, T0, whole)
        text = maker(lines)
        tag = f'{dev} {fmt}'
        if how == 'file':
            fp = os.path.join(SHOTS, f'{dev}_invented.vtt')
            open(fp, 'w', encoding='utf-8').write(text)
            await add_transcript(pg, phone, file=fp)
        else:
            await add_transcript(pg, phone, text=text)
        got = await pg.evaluate("id => { const t = fbsGet(id).transcript; return t && {format: t.format, n: t.lines.length}; }", sid)
        c.ok(got and got['format'] == fmt and got['n'] == len(lines), f'{tag}: read as {got} ({len(lines)} lines written)')
        T = await timeline(pg, sid)
        c.ok(T['how'] == 'mark', f'{tag}: lined up by Mark by itself ({T["how"]}: {T["say"]})')
        expect_rows(sess, lines, want, true, mark_rule(sess, lines), c, tag + ' by Mark', T['rows'])
        # by offset: the transcript's 00:00:00 is (mark 1's time - 4 s) into the session
        off = round(m1['t'] - T0, 3)
        await pg.fill('#fbs-off', str(off))
        await pg.locator('#fbs-off').dispatch_event('change')
        await wait(pg, 300)
        T = await timeline(pg, sid)
        c.ok(T['how'] == 'offset', f'{tag}: By Offset applied ({T["say"]})')
        expect_rows(sess, lines, want, true, lambda sec: sec + off, c, tag + ' by offset', T['rows'])
        # the screen: one group per page, every line shown
        ui = await pg.evaluate("() => ({rows: document.querySelectorAll('#v-fbs .fbs-tl').length, groups: [...document.querySelectorAll('#v-fbs .fbs-tg h3')].map(h => h.innerText), say: document.querySelector('[data-fbssay]')?.innerText || ''})")
        c.ok(ui['rows'] == len(lines) and len(ui['groups']) == T['groups'] and len(ui['groups']) >= 3, f'{tag}: the timeline shows {ui["rows"]} lines in {len(ui["groups"])} page groups ({ui["groups"][:6]})')
        c.ok('Applied:' in ui['say'], f'{tag}: the page says how it is lined up ({ui["say"][:100]!r})')
        # back to Mark for the next one
        await tap(pg, '[data-fbshow="mark"]', phone)
        await wait(pg, 300)
    # nudge: +1 s moves every line, the page says so; -1 s puts it back
    T1 = await timeline(pg, sid)
    await tap(pg, '[data-fbsnudge="1"]', phone)
    await wait(pg, 300)
    T2 = await timeline(pg, sid)
    c.ok(T2['nudge'] == 1 and all(abs(b_['t'] - a_['t'] - 1) < 0.01 for a_, b_ in zip(T1['rows'], T2['rows'])) and 'nudged +1 s' in T2['say'], f'{dev}: nudge +1 s moves every line by a second ({T2["say"][-40:]!r})')
    await tap(pg, '[data-fbsnudge="-1"]', phone)
    await wait(pg, 300)
    c.ok((await timeline(pg, sid))['nudge'] == 0, f'{dev}: nudge -1 s puts it back')
    # a finding flag sticks
    await tap(pg, '[data-fbsflag="problem"][data-fbsline="1"]', phone)
    await wait(pg, 300)
    fl = await pg.evaluate("id => fbsGet(id).findings", sid)
    c.ok(fl.get('1') == 'problem', f'{dev}: a line flagged as a problem stays flagged ({fl})')
    await pg.screenshot(path=os.path.join(SHOTS, f'{dev}_5_timeline.png'))
    if phone:
        sw = await pg.evaluate("() => document.documentElement.scrollWidth - innerWidth")
        c.ok(sw <= 1, f'{dev}: the timeline does not scroll sideways ({sw}px)')

    # ---- EXPORT TIMELINE: Markdown and JSON, both parse
    async with pg.expect_download() as dl:
        await tap(pg, '[data-fbsexport]', phone)
        await wait(pg, 300)
        await tap(pg, '#mbm-ok', phone)
    d = await dl.value
    mdp = os.path.join(SHOTS, f'{dev}_{d.suggested_filename}')
    await d.save_as(mdp)
    md = open(mdp, encoding='utf-8').read()
    c.ok(d.suggested_filename.endswith('.md') and md.startswith('# Feedback session: ') and '## 1. ' in md and '[problem]' in md, f'{dev}: Export Timeline saves the Markdown ({d.suggested_filename})')
    async with pg.expect_download() as dl:
        await tap(pg, '[data-fbsexport]', phone)
        await wait(pg, 300)
        await tap(pg, '#mbm-alt', phone)
    d = await dl.value
    jp = os.path.join(SHOTS, f'{dev}_{d.suggested_filename}')
    await d.save_as(jp)
    tj = json.load(open(jp, encoding='utf-8'))
    c.ok(tj.get('format') == 'smartdesigns-feedback-timeline' and len(tj['lines']) == len(lines) and all('said' in x and 'page' in x and 'taps' in x and 'recent' in x for x in tj['lines']) and tj['lines'][1]['finding'] == 'problem',
         f'{dev}: Export Timeline saves the JSON: {len(tj.get("lines", []))} lines with page, taps and recent')
    c.ok(all(x['said'] in md for x in tj['lines']), f'{dev}: every line said is in the Markdown')
    c.ok('Zebra' not in md and 'Zebra' not in json.dumps(tj), f'{dev}: the typed value is not in the exports')

    # ---- a clock-time transcript lines up by the clock (no "mark one" in it)
    clock_lines = await pg.evaluate("""id => { const s = fbsGet(id), out = [];
      s.events.filter(e => e.k === 'nav' && e.t > 2).forEach(e => { const ms = Math.floor((s.startMs + (e.t + 1.2) * 1000) / 1000) * 1000; out.push([new Date(ms).toLocaleTimeString('en-US', {hour: 'numeric', minute: '2-digit', second: '2-digit'}), 'On ' + e.heading, e.heading, (ms - s.startMs) / 1000]); });
      return out; }""", sid)
    await add_transcript(pg, phone, text='\n'.join(f'{a} Invented Person: {b}' for a, b, _, _ in clock_lines))
    T = await timeline(pg, sid)
    c.ok(T['how'] == 'clock', f'{dev}: a transcript in clock times lines up by the clock ({T["how"]}: {T["say"]})')
    navs_t = [(e['t'], e['heading']) for e in navs]
    ok_n = 0
    for (a, said, h, t), r in zip(clock_lines, T['rows']):
        if any(abs(nt - t) < 0.5 for nt, _ in navs_t): continue
        exp = [hh for nt, hh in navs_t if nt <= t][-1]
        c.ok(abs(r['t'] - t) < 0.01 and (r['page'] or {}).get('heading') == exp, f'{dev} clock: "{said}" at {r["t"]} on {(r["page"] or {}).get("heading")!r}, expected {t} on {exp!r}')
        ok_n += 1
    c.ok(ok_n >= 2, f'{dev} clock: {ok_n} lines graded')
    # the phone's and the desktop's session page has one blue button
    prim = await pg.evaluate("() => [...document.querySelectorAll('#v-fbs .btn.primary')].filter(b => b.getClientRects().length).length")
    c.ok(prim == 1, f'{dev}: one blue button on the session page ({prim})')
    c.ok(not errs, f'{dev}: page errors {errs[:3]}')
    await b.close()

async def main():
    c = Checks()
    devs = [False, True]
    if '--desktop' in sys.argv: devs = [False]
    if '--phone' in sys.argv: devs = [True]
    for f in os.listdir(SHOTS):
        if any(f.startswith(('phone_' if d else 'desktop_')) for d in devs): os.remove(os.path.join(SHOTS, f))
    async with async_playwright() as p:
        for phone in devs:
            await run(p, phone, c)
    sys.exit(c.done())

asyncio.run(main())
