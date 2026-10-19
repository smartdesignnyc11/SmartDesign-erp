"""Messages, phase 2 (BACKLOG §1.21): checked as the people who use it.

  1. The crew on a job: the PM puts a person on a job from the job's team thread (Change Crew), the toast opens the
     thread, and from then on that person reads the job's thread and nobody else in the field does. The foreman cannot
     change a crew. Project Settings shows the same line. A field person's local build lists only their jobs' threads.
  2. Read markers are each person's own (DB.msgSeen): phase 1's markers move out of the shared job and thread with the
     same counts, reading writes only the reader's record, a new crew member's history is not unread, and it all
     survives a reload.
  3. Notifications: on the hosted copy a direct message, or a job line that @mentions someone, asks /api/notify;
     a line naming nobody asks nothing; with no signal the ask waits for the phone to be back; a tapped
     notification opens its conversation, and only one the person may read.
  4. Reactions: four plainly named line icons, one per person, kept on the line; a second tap takes it back; a
     non-member cannot react; big targets on the phone.
  5. Voice notes: the record button (inside the text box's end on the field's phone, none for a client), a real
     recording with the browser's test microphone, kept like a photo and played in the line, on a direct thread and
     on a job's thread.

  python3 messages2_test.py        # prints ALL PASS (n checks) or each failure
"""
import asyncio, re
from harness import *


async def fresh(p, uid, phone=False):
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, uid)
    return b, pg, errs


async def keys_for(pg, uid):
    return await pg.evaluate("u => { signIn(u); render(); return msgThreadsFor().map(T => T.key); }", uid)


# ------------------------------------------------------------------------------------------------ 1. the crew
async def t_crew(c, p):
    b, pg, errs = await fresh(p, 'u_alan')
    first = await pg.evaluate("() => Object.fromEntries(DB.projects.map(p => [p.id, p.team]))")
    c.ok(first.get('p121') and set(first['p121']) == {'u_angel', 'u_alberto', 'u_satish', 'u_alex'}, f"crew: 121 State's first crew is the people who clocked, logged and asked there ({first.get('p121')})")
    c.ok(first.get('p206') == ['u_alberto', 'u_alex'] and first.get('p140') == [], f"crew: 206 Lenox has its two, the design job nobody ({first})")
    for u, want in (('u_angel', {'job:p121'}), ('u_satish', {'job:p121'}), ('u_alberto', {'job:p121', 'job:p206'})):
        k = await keys_for(pg, u)
        jobs = {x for x in k if x.startswith('job:') or x.startswith('client:')}
        c.ok(jobs == want, f"crew: {u}'s local build lists only the threads of the jobs they are on ({sorted(jobs)})")
    # the PM opens 206 Lenox's thread: the crew line and Change Crew
    await sign_in(pg, 'u_alan')
    await pg.evaluate("() => { setCurrent('p206'); msgOpen('job:p206'); }")
    await pg.wait_for_timeout(200)
    head = await pg.evaluate("() => { const h = document.getElementById('msg-head'), b = h.querySelector('[data-msgcrew]'); return h.innerText + ' | ' + (b ? b.getAttribute('aria-label') : '') }")
    c.ok('Crew:' in head and 'Alberto, Alex' in head and 'Change Crew' in head, f"crew: the job's thread names its crew, with Change Crew for the PM ({head!r})")
    await pg.click('[data-msgcrew="p206"]')
    await pg.wait_for_timeout(200)
    modal = await pg.evaluate("() => (document.getElementById('mbm') || {}).innerText || ''")
    c.ok('Crew on' in modal and 'Angel' in modal and 'Satish' in modal and 'Chen' not in modal, f'crew: the picker lists the people in the field only ({modal[:200]!r})')
    await pg.check('#mbm [data-f="c_u_angel"]')
    await pg.uncheck('#mbm [data-f="c_u_alex"]')
    await pg.click('#mbm #mbm-ok')
    await pg.wait_for_timeout(300)
    r = await pg.evaluate("() => ({ team: DB.projects.find(p => p.id === 'p206').team, toast: document.getElementById('toast').innerText, head: document.getElementById('msg-head').innerText })")
    c.ok(r['team'] == ['u_angel', 'u_alberto'], f"crew: Save Crew puts Angel on and takes Alex off ({r['team']})")
    c.ok('Crew on' in r['toast'] and 'Angel' in r['toast'] and 'Open' in r['toast'], f"crew: the toast says who is on it, with Open ({r['toast']!r})")
    c.ok('Angel, Alberto' in r['head'], f"crew: the thread's crew line reads the new crew ({r['head']!r})")
    k = await keys_for(pg, 'u_angel')
    c.ok('job:p206' in k, f'crew: Angel now has the 206 Lenox thread ({k})')
    k = await keys_for(pg, 'u_alex')
    c.ok('job:p206' not in k and 'job:p121' in k, f'crew: Alex no longer has it, and keeps 121 State ({k})')
    ok_open = await pg.evaluate("() => { signIn('u_alex'); render(); return !!msgThread('job:p206'); }")
    c.ok(not ok_open, 'crew: Alex cannot open the thread by its key either')
    # the foreman sees the crew but cannot change it
    await sign_in(pg, 'u_angel')
    await pg.evaluate("() => { setCurrent('p206'); msgOpen('job:p206'); }")
    await pg.wait_for_timeout(200)
    r = await pg.evaluate("() => { const h = document.getElementById('msg-head').innerText + (document.querySelector('#msg-head [data-msgcrew]') ? ' Change Crew' : ''); msgTeamEdit('p206'); return { h, modal: !!document.getElementById('mbm'), toast: document.getElementById('toast').innerText, team: DB.projects.find(p => p.id === 'p206').team } }")
    c.ok('Crew:' in r['h'] and 'Change Crew' not in r['h'], f"crew: the foreman reads who is on his job, with no Change Crew ({r['h']!r})")
    c.ok(not r['modal'] and 'PM or the owner' in r['toast'], f"crew: and cannot change it ({r['toast']!r})")
    # Project Settings: the same line, the same door
    await sign_in(pg, 'u_alan')
    await pg.evaluate("() => { setCurrent('p121'); view = 'proj'; render(); }")
    await pg.wait_for_timeout(200)
    t = await pg.evaluate("() => (document.getElementById('p-crew') || {}).innerText || ''")
    c.ok('Crew on This Job' in t and 'Satish' in t and 'Change Crew' in t, f'crew: Project Settings shows the crew with Change Crew ({t!r})')
    # the audit trail records who changed a crew
    a = await pg.evaluate("() => (DB.audit || []).filter(x => x.action === 'crew' || x.field === 'crew' || JSON.stringify(x).includes('set the crew')).length")
    c.ok(a >= 1, f'crew: the change is on the audit trail ({a})')
    c.ok(not errs, f'crew: no page errors {errs[:2]}')
    await b.close()
    # the phone: the crew line fits, no sideways scroll
    b, pg, errs = await fresh(p, 'u_alan', phone=True)
    await pg.evaluate("() => { setCurrent('p121'); msgOpen('job:p121'); }")
    await pg.wait_for_timeout(250)
    r = await pg.evaluate("() => { const b = document.querySelector('[data-msgcrew]'); const r = b ? b.getBoundingClientRect() : {}; return { sw: document.documentElement.scrollWidth, h: r.height || 0, right: r.right || 0 } }")
    c.ok(r['sw'] <= 390 and r['h'] >= 30 and r['right'] <= 390, f'crew: on the phone the line fits and Change Crew is on screen ({r})')
    c.ok(not errs, f'crew phone: no page errors {errs[:2]}')
    await b.close()


# ------------------------------------------------------------------------------------------------ 2. read markers
async def send(pg, text):
    await pg.fill('#chat-text', text)
    await pg.press('#chat-text', 'Enter')
    await pg.wait_for_timeout(400)


async def t_seen(c, p):
    b, pg, errs = await fresh(p, 'u_owner')
    # phase 1's markers, in the shared rows, move to each person's own record with the same counts
    r = await pg.evaluate("""() => {
      const chen = DB.users.find(u => u.id === 'u_chen'), before = msgUnreadTotal(chen).n, mine = JSON.parse(JSON.stringify(DB.msgSeen.u_chen || {}));
      const P = DB.projects.find(x => x.id === 'p121'), t = DB.threads.find(x => x.id === 'th_seed_dm');
      P.chatSeen = {}; t.seen = {};
      DB.threads.forEach(x => { x.seen = {}; });
      Object.entries(mine).forEach(([k, v]) => { const [kind, id] = k.split(':'), Q = DB.projects.find(x => x.id === id);
        if (kind === 'job' || kind === 'client') (Q.chatSeen = Q.chatSeen || {})['u_chen|' + (kind === 'job' ? 'team' : 'client')] = v;
        if (kind === 'dm') DB.threads.find(x => x.id === id).seen.u_chen = v; });
      P.chatSeen['u_zed|team'] = { id: 'x', n: 1 };                 // someone this device does not hold stays put
      delete DB.msgSeen.u_chen; delete DB.msgSeen.u_zed;
      const moved = msgSeenMove();
      const out = { before, after: msgUnreadTotal(chen).n, moved, keys: Object.keys(DB.msgSeen.u_chen || {}).sort(), shared: P.chatSeen || null, tseen: DB.threads.some(x => 'seen' in x) || null, had: Object.keys(mine).sort() };
      delete P.chatSeen; return out;
    }""")
    c.ok(r['moved'] >= 1 and r['had'] and r['keys'] == r['had'], f"seen: the markers moved to Chen's own record ({r['keys']} from {r['had']})")
    c.ok(r['before'] == r['after'], f"seen: and his unread count did not move ({r['before']} -> {r['after']})")
    c.ok(r['tseen'] is None and r['shared'] in (None, {'u_zed|team': {'id': 'x', 'n': 1}}), f"seen: nothing of his is left in the shared job or thread ({r['shared']} {r['tseen']})")
    # reading writes only the reader's own record: never the shared job or thread
    await sign_in(pg, 'u_alberto')
    await pg.evaluate("() => { setCurrent('p121'); msgOpen('job:p121'); }")
    await send(pg, 'Subfloor is down in the parlor')
    await sign_in(pg, 'u_chen')
    n = await pg.evaluate("() => msgUnread(msgThread('job:p121')).n")
    c.ok(n == 1, f'seen: Chen has the new line unread ({n})')
    await pg.evaluate("() => msgOpen('job:p121')")
    await pg.wait_for_timeout(200)
    r = await pg.evaluate("""() => { const P = DB.projects.find(x => x.id === 'p121');
      return { chen: msgUnread(msgThread('job:p121')).n, mark: (DB.msgSeen.u_chen || {})['job:p121'], last: P.chat.slice(-1)[0].id,
        sharedJob: JSON.stringify(DB.projects).includes('chatSeen'), sharedThreads: DB.threads.some(t => 'seen' in t),
        angel: msgUnread(msgThread('job:p121', DB.users.find(u => u.id === 'u_angel')), DB.users.find(u => u.id === 'u_angel')).n } }""")
    c.ok(r['chen'] == 0 and r['mark'] and r['mark']['id'] == r['last'], f"seen: opening it marks Chen's own record at the last line ({r['mark']})")
    c.ok(not r['sharedJob'] and not r['sharedThreads'], 'seen: no job and no thread carries anyone\'s read marker')
    c.ok(r['angel'] == 1, f"seen: Angel's count is his own: still 1 ({r['angel']})")
    # someone put on a crew starts from the day they joined, not from the job's first line
    await sign_in(pg, 'u_alan')
    await pg.evaluate("() => { setCurrent('p206'); msgOpen('job:p206'); }")
    await send(pg, 'Turnover walk with the super at 2')
    await pg.wait_for_timeout(2700)                      # the pinned demo clock runs at 1 app second per 2.4 real ones
    await pg.evaluate("() => { const P = DB.projects.find(x => x.id === 'p206'); P.team = P.team.filter(x => x !== 'u_satish'); delete (P.teamAt || {}).u_satish; delete (DB.msgSeen.u_satish || {})['job:p206']; }")
    await pg.click('[data-msgcrew="p206"]')
    await pg.wait_for_timeout(200)
    await pg.check('#mbm [data-f="c_u_satish"]')
    await pg.click('#mbm #mbm-ok')
    await pg.wait_for_timeout(1100)
    n0 = await pg.evaluate("() => { const s = DB.users.find(u => u.id === 'u_satish'); return msgUnread(msgThread('job:p206', s), s).n }")
    await send(pg, 'Satish, the punch list is on the counter')
    n1 = await pg.evaluate("() => { const s = DB.users.find(u => u.id === 'u_satish'); return msgUnread(msgThread('job:p206', s), s).n }")
    c.ok(n0 == 0 and n1 == 1, f"seen: Satish, just put on 206 Lenox, has none of its history unread, then the new line ({n0}, {n1})")
    # the markers survive a reload
    await pg.evaluate("() => saveNow()")
    await pg.reload()
    await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
    await sign_in(pg, 'u_chen')
    r = await pg.evaluate("() => ({ n: msgUnread(msgThread('job:p121')).n, mark: !!(DB.msgSeen.u_chen || {})['job:p121'] })")
    c.ok(r['n'] == 0 and r['mark'], f"seen: after a reload Chen's marker and his count stand ({r})")
    c.ok(not errs, f'seen: no page errors {errs[:2]}')
    await b.close()


# ------------------------------------------------------------------------------------------------ 3. notifications
STUB_CLOUD = """() => {
  window.__calls = []; window.__net = true;
  window.Cloud = { on: () => true, user: () => ({ id: 'auth-x' }), push: async () => ({ ok: true }), state: {}, putBlob: async () => true, getBlob: async () => null };
  const f0 = window.__f0 = window.__f0 || window.fetch;
  window.fetch = async (url, o) => { if (String(url) !== '/api/notify') return f0(url, o); if (!window.__net) throw new TypeError('Failed to fetch'); window.__calls.push([String(url), JSON.parse(o.body)]); return new Response('{}', { status: 200 }); };
}"""


async def t_notify(c, p):
    b, pg, errs = await fresh(p, 'u_chen')
    # the one-device demo has no server: nothing is asked
    await pg.evaluate("() => msgOpen('dm:th_seed_dm')")
    await send(pg, 'Is the tile in yet')
    q = await pg.evaluate("() => msgNotifyQ.length")
    c.ok(q == 0, f'notify: with no server nothing is queued ({q})')
    await pg.evaluate(STUB_CLOUD)
    await send(pg, 'The tile is at the yard, Alex picks it up at 7')
    await pg.wait_for_timeout(600)
    r = await pg.evaluate("() => ({ calls: window.__calls, last: DB.threads.find(t => t.id === 'th_seed_dm').msgs.slice(-1)[0].id })")
    c.ok(len(r['calls']) == 1 and r['calls'][0][0] == '/api/notify' and r['calls'][0][1] == {'threadKey': 'dm:th_seed_dm', 'msgId': r['last']}, f"notify: a direct message asks the server to tell the other member ({r['calls']})")
    # a job's thread: only a line that @mentions someone
    await sign_in(pg, 'u_alan')
    await pg.evaluate("() => { window.__calls = []; setCurrent('p121'); msgOpen('job:p121'); }")
    await send(pg, 'Panel cover is off')
    await pg.wait_for_timeout(500)
    n = await pg.evaluate("() => window.__calls.length")
    c.ok(n == 0, f'notify: a job line naming nobody asks nothing ({n})')
    await send(pg, '@Angel the inspector moved to 11')
    await pg.wait_for_timeout(600)
    r = await pg.evaluate("() => ({ calls: window.__calls, m: DB.projects.find(p => p.id === 'p121').chat.slice(-1)[0] })")
    c.ok(len(r['calls']) == 1 and r['calls'][0][1] == {'threadKey': 'job:p121', 'msgId': r['m']['id']} and r['m'].get('mentions') == ['u_angel'], f"notify: a job line that @mentions Angel asks for him ({r['calls']}, {r['m'].get('mentions')})")
    # no signal: the ask waits and goes when the phone is back
    await pg.evaluate("() => { window.__calls = []; window.__net = false; msgOpen('dm:th_seed_leads'); }")
    await send(pg, 'Walk is still at 10')
    await pg.wait_for_timeout(600)
    q = await pg.evaluate("() => ({ q: msgNotifyQ.length, calls: window.__calls.length })")
    c.ok(q['q'] == 1 and q['calls'] == 0, f'notify: with no signal the ask is kept ({q})')
    await pg.evaluate("() => { window.__net = true; window.dispatchEvent(new Event('online')); }")
    await pg.wait_for_timeout(2300)
    q = await pg.evaluate("() => ({ q: msgNotifyQ.length, calls: window.__calls.map(c => c[1].threadKey) })")
    c.ok(q['q'] == 0 and q['calls'] == ['dm:th_seed_leads'], f'notify: and goes when the phone is back online ({q})')
    # a tapped notification opens its conversation
    r = await pg.evaluate("() => { msgOpen('job:p121'); view = 'dash'; render(); const ok = msgOpenFromUrl('https://smartdesigns-erp.netlify.app/?msg=dm%3Ath_seed_leads'); return { ok, key: (msgCur() || {}).key, view } }")
    c.ok(r['ok'] and r['key'] == 'dm:th_seed_leads' and r['view'] == 'chat', f'notify: a tapped notification opens its conversation ({r})')
    r = await pg.evaluate("() => { signIn('u_alberto'); render(); return msgOpenFromUrl('https://x/?msg=dm%3Ath_seed_dm'); }")
    c.ok(r is False, 'notify: a link to a conversation the person is not in opens nothing')
    await pg.evaluate("() => { delete window.Cloud; }")
    c.ok(not errs, f'notify: no page errors {errs[:2]}')
    await b.close()


# ------------------------------------------------------------------------------------------------ 4. reactions
async def long_press(pg, sel):
    # a finger held half a second on the line (Playwright's touchscreen only taps)
    await pg.evaluate("""s => { const el = document.querySelector(s), r = el.getBoundingClientRect(), x = r.left + r.width / 2, y = r.top + r.height / 2;
        const t = new Touch({ identifier: 1, target: el, clientX: x, clientY: y });
        el.dispatchEvent(new TouchEvent('touchstart', { touches: [t], targetTouches: [t], changedTouches: [t], bubbles: true, cancelable: true })); }""", sel)
    await pg.wait_for_timeout(650)
    await pg.evaluate("s => { const el = document.querySelector(s); el.dispatchEvent(new TouchEvent('touchend', { touches: [], changedTouches: [], bubbles: true })); }", sel)
    await pg.wait_for_timeout(150)


async def t_react(c, p):
    b, pg, errs = await fresh(p, 'u_chen')
    await pg.evaluate("() => msgOpen('dm:th_seed_dm')")
    await pg.wait_for_timeout(200)
    mid = await pg.evaluate("() => DB.threads.find(t => t.id === 'th_seed_dm').msgs[0].id")
    await pg.click(f'[data-mid="{mid}"] [data-msgreact]')
    await pg.wait_for_timeout(150)
    pick = await pg.evaluate(f"() => [...document.querySelectorAll('[data-mid=\"{mid}\"] .msg-rpick button')].map(b => b.innerText.trim())")
    c.ok(pick == ['Done', 'Good', 'On It', 'Question'], f'react: React opens four plainly named choices ({pick})')
    icons = await pg.evaluate(f"() => [...document.querySelectorAll('[data-mid=\"{mid}\"] .msg-rpick button')].every(b => b.querySelector('svg') && !/[\\u2600-\\u27BF\\u{{1F300}}-\\u{{1FAFF}}]/u.test(b.innerText))")
    c.ok(icons, 'react: each is a line icon, no emoji')
    await pg.click(f'[data-mid="{mid}"] .msg-rpick [data-msgrx$="|ok"]')
    await pg.wait_for_timeout(200)
    r = await pg.evaluate(f"""() => {{ const m = DB.threads.find(t => t.id === 'th_seed_dm').msgs[0], chip = document.querySelector('[data-mid="{mid}"] .msg-rxc');
        return {{ react: m.react, chip: chip ? [chip.innerText.trim(), chip.className, chip.title] : null, open: !!document.querySelector('.msg-rpick'), toast: document.getElementById('toast').innerText }} }}""")
    c.ok(r['react'] == {'u_chen': 'ok'}, f"react: Done is kept on the line, as Chen's ({r['react']})")
    c.ok(r['chip'] and r['chip'][0] == '1' and ' on' in ' ' + r['chip'][1] and 'Chen' in r['chip'][2] and not r['open'], f"react: the line shows Done 1, marked as his, and the picker closes ({r['chip']})")
    c.ok("Done on Angel's message" in r['toast'] and 'Open' in r['toast'], f"react: it toasts what happened, with Open ({r['toast']!r})")
    # the other member reads it; a second person's adds to the count; a tap on your own chip takes it back
    await sign_in(pg, 'u_angel')
    await pg.evaluate("() => msgOpen('dm:th_seed_dm')")
    await pg.wait_for_timeout(150)
    await pg.click(f'[data-mid="{mid}"] .msg-rxc')
    await pg.wait_for_timeout(150)
    r = await pg.evaluate(f"() => ({{ react: DB.threads.find(t => t.id === 'th_seed_dm').msgs[0].react, chip: (document.querySelector('[data-mid=\"{mid}\"] .msg-rxc') || {{}}).innerText }})")
    c.ok(r['react'] == {'u_chen': 'ok', 'u_angel': 'ok'} and r['chip'].strip() == '2', f"react: Angel adds his Done from the chip: 2 ({r})")
    await pg.click(f'[data-mid="{mid}"] .msg-rxc')
    await pg.wait_for_timeout(150)
    r = await pg.evaluate("() => DB.threads.find(t => t.id === 'th_seed_dm').msgs[0].react")
    c.ok(r == {'u_chen': 'ok'}, f'react: and a second tap takes his back ({r})')
    # someone not in the thread cannot react to it
    x = await pg.evaluate(f"() => {{ signIn('u_alberto'); render(); return msgReact('dm:th_seed_dm', '{mid}', 'like'); }}")
    c.ok(x is None, 'react: a person not in the thread cannot react to it')
    # the field on its job's thread, on the phone
    await b.close()
    b, pg, errs2 = await fresh(p, 'u_alberto', phone=True)
    await pg.evaluate("() => { const P = DB.projects.find(p => p.id === 'p121'); P.chat.push(Object.assign(msgLine('Inspector passed the framing'), { by: 'Angel', fromUid: 'u_angel' })); setCurrent('p121'); msgOpen('job:p121'); }")
    await pg.wait_for_timeout(250)
    mid = await pg.evaluate("() => DB.projects.find(p => p.id === 'p121').chat.slice(-1)[0].id")
    await long_press(pg, f'[data-mid="{mid}"] .msg-bub')
    sheet = await pg.evaluate("() => { const s = document.getElementById('msg-sheet'); return s ? [...s.querySelectorAll('button')].map(b => [b.innerText.trim(), Math.round(b.getBoundingClientRect().height)]) : null }")
    c.ok(sheet and [x[0] for x in sheet] == ['Done', 'Good', 'On It', 'Question', 'Reply', 'Make a Task', 'Copy', 'Cancel'] and min(x[1] for x in sheet) >= 48, f'react: a long press on the phone opens Reply, the reactions, Make a Task and Copy, big targets ({sheet})')
    await pg.tap('#msg-sheet [data-msgrx$="|like"]')
    await pg.wait_for_timeout(250)
    r = await pg.evaluate(f"""() => {{ const chip = document.querySelector('[data-mid="{mid}"] .msg-rxc'), r = chip.getBoundingClientRect(), acts = [...document.querySelectorAll('[data-mid="{mid}"] .msg-below > *')].map(b => b.getBoundingClientRect());
        return {{ react: DB.projects.find(p => p.id === 'p121').chat.slice(-1)[0].react, h: r.height, right: r.right, sw: document.documentElement.scrollWidth, gap: acts.length > 1 ? Math.max(acts[1].left - acts[0].right, acts[0].left - acts[1].right, acts[1].top - acts[0].bottom, acts[0].top - acts[1].bottom) : 99 }} }}""")
    c.ok(r['react'] == {'u_alberto': 'like'}, f"react: Alberto's Good is on the job's line ({r['react']})")
    c.ok(r['h'] >= 36 and r['right'] <= 390 and r['sw'] <= 390 and r['gap'] >= 8, f'react: on the phone the chip is a big target, 8px from the next, no sideways scroll ({r})')
    c.ok(not errs and not errs2, f'react: no page errors {errs[:2]} {errs2[:2]}')
    await b.close()


# ------------------------------------------------------------------------------------------------ 5. voice notes
async def t_voice(c, p):
    # the round button at the right of the box: the microphone while the box is empty, Send once there is text (as on
    # WhatsApp); the box keeps a usable width; a client has Send only
    b, pg, errs = await fresh(p, 'u_alberto', phone=True)
    await pg.evaluate("() => { setCurrent('p121'); msgOpen('job:p121'); }")
    await pg.wait_for_timeout(250)
    r = await pg.evaluate("""() => { const v = document.getElementById('msg-voice'), t = document.getElementById('chat-text'), a = v.getBoundingClientRect(), x = t.getBoundingClientRect(),
        mid = document.elementFromPoint(x.left + x.width / 2, x.top + x.height / 2);
        const send = document.getElementById('chat-send');
        return { shown: !v.hidden && a.width >= 44 && a.height >= 44, inside: a.left >= x.right && !send.getClientRects().length, round: getComputedStyle(v).borderRadius, box: x.width, hit: mid === t, sw: document.documentElement.scrollWidth, label: v.getAttribute('aria-label'), svg: !!v.querySelector('svg') } }""")
    c.ok(r['shown'] and r['svg'] and 'voice note' in (r['label'] or ''), f'voice: the field phone has a 44px microphone button with a line icon ({r})')
    c.ok(r['inside'] and r['round'] == '50%' and r['box'] >= 140 and r['hit'] and r['sw'] <= 390, f'voice: with the box empty the round button is the microphone, Send is away, the box keeps its width ({r})')
    await pg.fill('#chat-text', 'On my way')
    r = await pg.evaluate("() => ({ send: !!document.getElementById('chat-send').getClientRects().length, mic: !!document.getElementById('msg-voice').getClientRects().length })")
    c.ok(r['send'] and not r['mic'], f'voice: once there is text the round button is Send ({r})')
    await pg.fill('#chat-text', '')
    await sign_in(pg, 'u_klein')
    await go(pg, 'chat')
    hid = await pg.evaluate("() => { const v = document.getElementById('msg-voice'); return (!v || v.hidden || !v.getClientRects().length) && !!document.getElementById('chat-send').getClientRects().length }")
    c.ok(hid, 'voice: a client has no record button, and Send stays')
    c.ok(not errs, f'voice: no page errors {errs[:2]}')
    await b.close()
    # record for real with the browser's test microphone
    br = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])
    ctx = await br.new_context(viewport=PHONE, is_mobile=True, has_touch=True)
    pg = await ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto(URL)
    await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
    await sign_in(pg, 'u_angel')
    await pg.evaluate("() => msgOpen('dm:th_seed_dm')")
    await pg.wait_for_timeout(250)
    await pg.tap('#msg-voice')
    await pg.wait_for_timeout(1800)
    r = await pg.evaluate("() => { const v = document.getElementById('msg-voice'); return { rec: v.classList.contains('rec'), pressed: v.getAttribute('aria-pressed'), time: v.innerText.trim() } }")
    c.ok(r['rec'] and r['pressed'] == 'true' and re.match(r'0:0[1-9]', r['time'] or ''), f'voice: recording shows as a stop button with the time ({r})')
    await pg.tap('#msg-voice')
    await pg.wait_for_timeout(1500)
    r = await pg.evaluate("""() => { const m = DB.threads.find(t => t.id === 'th_seed_dm').msgs.slice(-1)[0], a = document.querySelector(`[data-mid="${m.id}"] audio`);
        return { voice: m.voice || null, by: m.fromUid, src: a ? (a.getAttribute('src') || '').slice(0, 11) : null, toast: document.getElementById('toast').innerText, rec: document.getElementById('msg-voice').classList.contains('rec') } }""")
    c.ok(r['voice'] and r['voice']['id'].startswith('vn') and r['voice']['dur'] >= 1 and r['by'] == 'u_angel', f"voice: Stop sends it as Angel's line with its length ({r['voice']})")
    c.ok(r['src'] == 'data:audio/', f"voice: it plays in the line ({r['src']})")
    c.ok('Voice note sent' in r['toast'] and 'Open' in r['toast'] and not r['rec'], f"voice: it toasts, with Open, and the button is a microphone again ({r['toast']!r})")
    stored = await pg.evaluate("async () => { const m = DB.threads.find(t => t.id === 'th_seed_dm').msgs.slice(-1)[0]; const d = await getBlob(m.voice.id); return (d || '').slice(0, 11) }")
    c.ok(stored == 'data:audio/', f'voice: the recording is kept like a photo, in the device store ({stored})')
    # the other member hears it, and the thread list reads it as a voice note
    await sign_in(pg, 'u_chen')
    await pg.evaluate("() => msgOpen('dm:th_seed_dm')")
    await pg.wait_for_timeout(600)
    r = await pg.evaluate("""() => { const m = DB.threads.find(t => t.id === 'th_seed_dm').msgs.slice(-1)[0], a = document.querySelector(`[data-mid="${m.id}"] audio`);
        return { src: a ? (a.getAttribute('src') || '').slice(0, 11) : null, unread: 0, preview: msgListHtml(msgThreadsFor(), null, msgMe()).includes('Voice note (0:0') } }""")
    c.ok(r['src'] == 'data:audio/' and r['preview'], f'voice: Chen plays it, and his list reads "Voice note (0:0x)" ({r})')
    # a job's thread takes one too, posted on the job's own chat
    m = await pg.evaluate("async () => { setCurrent('p121'); msgOpen('job:p121'); const m = await msgVoicePost(msgThread('job:p121'), 'data:audio/webm;base64,GkXfo0AgQoaBAUL3gQFC8oEEQvOBCEKChHdlYm1Ch4EEQoWBAhhTgGcB', 3.2, 'audio/webm;codecs=opus'); const P = DB.projects.find(p => p.id === 'p121'); return [m && m.id, P.chat.slice(-1)[0].id, P.chat.slice(-1)[0].voice, P.chat.slice(-1)[0].aud] }")
    c.ok(m[0] and m[0] == m[1] and m[2]['dur'] == 3 and m[2]['mime'] == 'audio/webm' and m[3] == 'team', f"voice: on a job's thread it is the team's line on the job ({m})")
    c.ok(not errs, f'voice record: no page errors {errs[:2]}')
    await br.close()


# ------------------------------------------------------------------------------------------------ 6. the screen
VISIBLE = "s => { const e = document.querySelector(s); return !!(e && e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden') }"


async def t_screen(c, p):
    # the phone: Chat in the bottom bar opens the list, no job chrome
    b, pg, errs = await fresh(p, 'u_alan', phone=True)
    await pg.evaluate("() => { setCurrent('p121'); view = 'dash'; render(); }")
    await pg.click('.mtabs [data-mv="chat"]')
    await pg.wait_for_timeout(300)
    r = await pg.evaluate(f"""() => {{ const vis = {VISIBLE};
        return {{ view, list: vis('#msg-side'), thread: vis('.msg-main'), sub: vis('#subnav'), hdr: vis('#projhdr'), h2: (document.querySelector('#msg-side h2') || {{}}).innerText,
          rows: [...document.querySelectorAll('#msg-side .msg-row')].map(e => [Math.round(e.getBoundingClientRect().height), !!e.querySelector('.msg-av')]), search: vis('#msg-q'), compose: vis('#msg-new'), sw: document.documentElement.scrollWidth,
          order: msgRowsOf(msgThreadsFor(), msgMe()).map(x => x.un.n) }} }}""")
    c.ok(r['view'] == 'chat' and r['list'] and not r['thread'], f'screen: the bottom bar\'s Chat opens the list of conversations, not a job ({r["view"]}, list {r["list"]}, thread {r["thread"]})')
    c.ok(not r['sub'] and not r['hdr'], f"screen: no job switcher, job tabs or job dates on Chat ({r['sub']}, {r['hdr']})")
    c.ok(r['h2'] == 'Chat' and r['search'] and r['compose'], f"screen: the list has its heading, search and New Message ({r['h2']})")
    c.ok(r['rows'] and all(h >= 56 and av for h, av in r['rows']) and r['sw'] <= 390, f"screen: each row has an avatar and is a big target; no sideways scroll ({r['rows'][:3]}, {r['sw']})")
    c.ok(r['order'] == sorted(r['order'], key=lambda n: 0 if n else 1), f"screen: unread conversations come first ({r['order']})")
    await pg.fill('#msg-q', 'lenox')
    await pg.wait_for_timeout(200)
    t = await pg.evaluate("() => [...document.querySelectorAll('#msg-side .msg-row .msg-t')].map(e => e.innerText)")
    c.ok(t and all('Lenox' in x for x in t), f'screen: search narrows the list as you type ({t})')
    await pg.fill('#msg-q', '')
    await pg.wait_for_timeout(150)
    # a conversation: full screen, the composer pinned at the bottom, one blue button, 16px text so iOS does not zoom
    await pg.tap('#msg-side [data-msgopen="job:p121"]')
    await pg.wait_for_timeout(300)
    r = await pg.evaluate("""() => { const m = document.querySelector('.msg-main').getBoundingClientRect(), c = document.querySelector('#v-chat .chat-compose').getBoundingClientRect(), rb = [document.getElementById('chat-send'), document.getElementById('msg-voice')].find(e => e && e.getClientRects().length), s = rb.getBoundingClientRect(), t = document.getElementById('chat-text');
        const prim = [...document.querySelectorAll('.btn.primary')].filter(e => e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden');
        return { top: Math.round(m.top), bottom: Math.round(m.bottom), cbottom: Math.round(c.bottom), vh: innerHeight, send: [Math.round(s.width), Math.round(s.height), getComputedStyle(rb).borderRadius, rb.id],
          font: getComputedStyle(t).fontSize, tag: t.tagName, prim: prim.map(e => e.id || e.className), back: !!document.querySelector('#msg-head [data-msgback]'), pinned: !!document.getElementById('pl-pinned'), sw: document.documentElement.scrollWidth } }""")
    c.ok(r['top'] == 0 and r['bottom'] == r['vh'] and r['vh'] - r['cbottom'] <= 2, f'screen: the conversation is full screen and the composer sits at the bottom ({r})')
    c.ok(r['send'][0] >= 44 and r['send'][1] >= 44 and r['send'][2] == '50%', f"screen: the round button at the right (the microphone while the box is empty) is 44px ({r['send']})")
    c.ok(r['font'] == '16px' and r['tag'] == 'TEXTAREA', f"screen: the box is a growing text area at 16px, so an iPhone does not zoom ({r['font']}, {r['tag']})")
    c.ok(r['prim'] == ['msg-voice'], f"screen: one blue button on the screen: the microphone while the box is empty ({r['prim']})")
    await pg.fill('#chat-text', 'Panel cover is off')
    prim = await pg.evaluate("() => [...document.querySelectorAll('.btn.primary')].filter(e => e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden').map(e => e.id)")
    c.ok(prim == ['chat-send'], f"screen: and Send once there is text ({prim})")
    await pg.fill('#chat-text', '')
    c.ok(r['back'] and not r['pinned'] and r['sw'] <= 390, f"screen: a back arrow, no Pinned Plans under the composer, no sideways scroll ({r})")
    await pg.fill('#chat-text', 'Line one\nLine two\nLine three')
    await pg.wait_for_timeout(100)
    h = await pg.evaluate("() => document.getElementById('chat-text').getBoundingClientRect().height")
    c.ok(h > 60, f'screen: the box grows with what is typed ({h})')
    await pg.fill('#chat-text', '')
    await pg.tap('[data-msgback]')
    await pg.wait_for_timeout(200)
    c.ok(await pg.evaluate(f"() => ({VISIBLE})('#msg-side') && !({VISIBLE})('.msg-main')"), 'screen: back returns to the list')
    # the header's Plans button: the job's current drawings, where Pinned Plans now lives
    await pg.evaluate("() => msgOpen('job:p121')")
    await pg.wait_for_timeout(200)
    await pg.tap('#msg-head [data-msgplans]')
    await pg.wait_for_timeout(300)
    v = await pg.evaluate("() => view")
    c.ok(v == 'plans', f"screen: the conversation's Plans button opens the job's drawings ({v})")
    c.ok(not errs, f'screen phone: no page errors {errs[:2]}')
    await b.close()
    # the field's bar
    b, pg, errs = await fresh(p, 'u_alberto', phone=True)
    await pg.click('.tabbar [data-tab="chat"]')
    await pg.wait_for_timeout(300)
    r = await pg.evaluate(f"() => ({{ list: ({VISIBLE})('#msg-side'), thread: ({VISIBLE})('.msg-main') }})")
    c.ok(r['list'] and not r['thread'], f"screen: the field's Chat opens the list too ({r})")
    await b.close()
    # the desktop: two panes, the list beside the conversation; no job chrome; the trail reads Chat
    b, pg, errs = await fresh(p, 'u_alan')
    await pg.evaluate("() => { setCurrent('p121'); view = 'dash'; render(); }")
    await pg.click('#tb-chat')
    await pg.wait_for_timeout(300)
    r = await pg.evaluate(f"""() => {{ const vis = {VISIBLE}, a = document.querySelector('#msg-side').getBoundingClientRect(), m = document.querySelector('.msg-main').getBoundingClientRect(), c = document.querySelector('#v-chat .chat-compose').getBoundingClientRect();
        return {{ side: vis('#msg-side'), main: vis('.msg-main'), beside: a.right <= m.left + 1 && Math.abs(a.top - m.top) < 4, sub: vis('#subnav'), hdr: vis('#projhdr'), crumbs: document.getElementById('crumbs').innerText.trim(),
          cur: (msgCur() || {{}}).key, top: msgRowsOf(msgThreadsFor(), msgMe())[0].T.key, pinned: c.bottom <= innerHeight && innerHeight - c.bottom < 40 }} }}""")
    c.ok(r['side'] and r['main'] and r['beside'], f'screen: on a desktop the list and the conversation are two panes side by side ({r})')
    c.ok(not r['sub'] and not r['hdr'] and r['crumbs'] == 'Chat', f"screen: no job chrome, and the trail reads Chat ({r['crumbs']!r})")
    c.ok(r['cur'] == r['top'] and r['pinned'], f"screen: it opens on the top conversation, the composer at the pane's foot ({r})")
    # a line: bubbles, a day separator, a run of one person's lines grouped; Reply quotes it; Copy copies it
    await pg.evaluate("""() => { const P = DB.projects.find(p => p.id === 'p121'); const L = (id, uid, text, at) => Object.assign(msgLine(text), { id, by: DB.users.find(u => u.id === uid).name, fromUid: uid, at, t: stampText(at) });
        P.chat.push(L('s1', 'u_angel', 'Framing is done in the garden bedroom', '2026-09-02T16:10:00'), L('s2', 'u_angel', 'Plumber starts tomorrow', '2026-09-02T16:11:00'), L('s3', 'u_chen', 'Tile lands Friday', '2026-09-03T08:05:00')); msgOpen('job:p121'); }""")
    await pg.wait_for_timeout(250)
    r = await pg.evaluate("""() => ({ days: [...document.querySelectorAll('#chat-list .msg-day')].map(e => e.innerText.trim()), s1: !!document.querySelector('[data-mid="s1"] .msg-av:not(.sp)'), s2: !!document.querySelector('[data-mid="s2"] .msg-av:not(.sp)'),
        who2: !!document.querySelector('[data-mid="s2"] .who'), them: document.querySelector('[data-mid="s1"]').classList.contains('them'), time: (document.querySelector('[data-mid="s1"] .msg-time') || {}).innerText })""")
    c.ok('Yesterday' in r['days'] and 'Today' in r['days'], f"screen: day separators ({r['days']})")
    c.ok(r['them'] and r['s1'] and not r['s2'] and not r['who2'], f'screen: the second of two lines from Angel is grouped under the first ({r})')
    c.ok(r['time'] == '4:10 PM', f"screen: the time sits quietly in the bubble ({r['time']})")
    await pg.hover('[data-mid="s1"] .msg-bub')
    await pg.click('[data-mid="s1"] [data-msgreply]')
    await pg.wait_for_timeout(150)
    bar = await pg.evaluate("() => document.getElementById('msg-reply').innerText")
    c.ok('Replying to Angel' in bar, f'screen: Reply names the line above the box ({bar!r})')
    await pg.fill('#chat-text', 'Good, I will tell the plumber')
    await pg.press('#chat-text', 'Enter')
    await pg.wait_for_timeout(400)
    r = await pg.evaluate("() => { const m = DB.projects.find(p => p.id === 'p121').chat.slice(-1)[0]; return { reply: m.reply, quote: !!document.querySelector(`[data-mid='${m.id}'] .msg-quote`), bar: document.getElementById('msg-reply').hidden, box: document.getElementById('chat-text').value } }")
    c.ok(r['reply'] and r['reply']['id'] == 's1' and r['quote'] and r['bar'] and r['box'] == '', f"screen: the sent line quotes the one it answers, and the bar clears ({r})")
    await pg.hover('[data-mid="s3"] .msg-bub')
    await pg.click('[data-mid="s3"] [data-msgcopy]')
    await pg.wait_for_timeout(200)
    t = await pg.evaluate("() => document.getElementById('toast').innerText")
    c.ok('Copied' in t or 'would not copy' in t, f'screen: Copy copies it, and says so ({t!r})')
    # the job's own tabs: Mail and Chat, never two that read as chat
    await pg.evaluate("() => { setCurrent('p121'); view = 'dash'; render(); }")
    await pg.wait_for_timeout(200)
    tabs = await pg.evaluate("() => [...document.querySelectorAll('#subnav [data-sub]')].map(e => e.innerText.trim())")
    c.ok('Mail' in tabs and 'Chat' not in tabs and 'Messages' not in tabs, f"screen: the job's tabs read Mail; Chat is the header's and the bar's, never a second chat tab ({[x for x in tabs if x in ('Mail', 'Chat', 'Messages')]})")
    c.ok(not errs, f'screen desktop: no page errors {errs[:2]}')
    await b.close()


TESTS = [t_crew, t_seen, t_notify, t_react, t_voice, t_screen]


async def main():
    c = Checks()
    async with async_playwright() as p:
        for t in TESTS:
            try:
                await t(c, p)
            except Exception as e:
                c.ok(False, f'{t.__name__}: {type(e).__name__}: {str(e)[:300]}')
    return c.done()

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
