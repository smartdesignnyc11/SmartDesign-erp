"""Messages, phase 1 (BACKLOG §1.21): one noun, the message thread, checked as the people who use it.

  1. Migration: the job chat's existing lines stay where they are (p.chat), split into the team's thread and the
     client's thread by audience, and the history counts as read for everyone; it survives a reload.
  2. A direct message between two people is read by those two only: every one of the ten users is signed in and
     looks at Chat, at the thread list and through Ask (the query layer).
  3. The field reads a PO card with no money in it, on the thread and when it opens the card; a money record's
     card never reaches the field.
  4. @assistant answers in the thread through the person's own Ask path, for that person only: nothing is posted to
     the shared thread, another member never sees it, and the field's assistant gives no money.
  5. One tap makes a message a task through the one task creator; it lands on the owner's own Tasks list, the toast
     opens it and the line links to it.
  6. Unread: one number per thread and per person, the same on the nav badge, the thread list and the back bar; a
     mention is marked; opening the thread reads it.
  7. Phone 390: typing and sending with the keyboard's Enter, big targets, nothing covers the box, no sideways scroll.
  8. A client reads only their own job's client thread; the PM's reply there answers the client's open question.

  python3 messages_lane_test.py        # prints ALL PASS (n checks) or each failure
"""
import asyncio, re
from harness import *


async def fresh(p, uid, phone=False):
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, uid)
    return b, pg, errs


async def js(pg, body, arg=None):
    return await pg.evaluate("async (arg) => { const sleep = (ms) => new Promise(r => setTimeout(r, ms)); " + body + " }", arg)


async def open_thread(pg, key):
    await pg.evaluate("k => msgOpen(k)", key)
    await pg.wait_for_timeout(200)


async def send(pg, text):
    await pg.fill('#chat-text', text)
    await pg.press('#chat-text', 'Enter')
    await pg.wait_for_timeout(500)


async def chat_text(pg):
    return await pg.evaluate("() => (document.querySelector('#v-chat') || {}).innerText || ''")


# ------------------------------------------------------------------------------------------------ 1. migration
async def t_migrate(c, p):
    b, pg, errs = await fresh(p, 'u_owner')
    r = await js(pg, """
      const P = DB.projects.find(x => x.id === 'p121'), cl = DB.clients.find(x => x.id === P.clientId);
      P.chat = [
        { id: 'leg1', by: 'Alberto', text: 'Framing in the garden bedroom is done, plumber can start', t: '9/2, 4:10 PM', files: [] },
        { id: 'leg2', by: 'Sarah Klein', text: 'Can we see the tile before it goes in?', t: '9/2, 6:02 PM', files: [], clq: 'q_leg' },
        { id: 'leg3', by: 'System', text: 'INV-2026-099 - Progress billing is ready for you under Account.', t: '9/2, 6:30 PM', files: [], system: true },
        { id: 'leg4', by: 'Alex', fromUid: 'u_alex', to: 'u_chen', dm: true, text: 'To Chen Biron: What time is the yard pickup?', t: '9/2, 7:00 PM', files: [] },
        { id: 'leg5', by: 'System', text: 'Alex is at Home Depot until 3:15 PM. Add anything you need now from Requests.', t: '9/3, 9:00 AM', files: [], system: true },
      ];
      delete P.chatSeen; delete DB.__msgV;
      const ran = msgMigrate();
      const ids = P.chat.map(m => m.id).join(',');
      const team = msgThread('job:p121').all().map(m => m.id), client = msgThread('client:p121').all().map(m => m.id);
      const unread = DB.users.filter(u => ['u_owner','u_alan','u_chen','u_angel','u_alberto','u_alex','u_klein','u_sarah','u_billing','u_controller'].includes(u.id)).map(u => [u.id, msgUnreadTotal(u).n]);
      await saveNow();
      return { ran, ids, team, client, unread, v: DB.__msgV };""")
    c.ok(r['ran'] and r['v'] == 1, 'migrate: the migration ran once and recorded it')
    c.ok(r['ids'] == 'leg1,leg2,leg3,leg4,leg5', f"migrate: every line stays in p.chat, in order ({r['ids']})")
    c.ok(r['team'] == ['leg1', 'leg4', 'leg5'], f"migrate: the team's thread holds the crew line, the addressed line and the store run ({r['team']})")
    c.ok(r['client'] == ['leg2', 'leg3'], f"migrate: the client's thread holds the client's question and the document sent to them ({r['client']})")
    c.ok(all(n == 0 for _, n in r['unread']), f"migrate: the history counts as read for everyone ({r['unread']})")
    await pg.reload()
    await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
    await sign_in(pg, 'u_owner')
    r2 = await pg.evaluate("() => { const P = DB.projects.find(x => x.id === 'p121'); return { ids: P.chat.map(m => m.id).join(','), v: DB.__msgV, threads: (DB.threads || []).length } }")
    c.ok(r2['ids'] == 'leg1,leg2,leg3,leg4,leg5' and r2['v'] == 1, f"migrate: after a reload the lines are all there ({r2})")
    c.ok(r2['threads'] >= 2, f"migrate: the demo's direct and group threads are in DB.threads ({r2['threads']})")
    # the legacy addressed line: Alex and Chen only
    for u, sees in (('u_alex', True), ('u_chen', True), ('u_owner', False), ('u_angel', False)):
        await sign_in(pg, u)
        await pg.evaluate("() => { setCurrent('p121'); view = 'chat'; render(); }")
        await pg.wait_for_timeout(150)
        t = await pg.evaluate("() => document.getElementById('chat-list').innerText")
        c.ok(('yard pickup' in t) == sees, f"migrate: the line Alex addressed to Chen is {'read' if sees else 'not read'} by {u}")
    c.ok(not errs, f'migrate: no page errors {errs[:2]}')
    await b.close()


# ------------------------------------------------------------------------------------------------ 2. direct message
async def t_dm(c, p):
    b, pg, errs = await fresh(p, 'u_chen')
    await go(pg, 'chat')
    await pg.click('#msg-new')
    await pg.wait_for_timeout(200)
    await pg.check('#mbm [data-f="p_u:u_alberto"]')   # New Chat (2026-10-19): people keyed by kind
    await pg.click('#mbm #mbm-ok')
    await pg.wait_for_timeout(400)
    key = await pg.evaluate("() => (msgCur() || {}).key")
    c.ok(key and key.startswith('dm:'), f'dm: New Message opens the direct thread ({key})')
    secret = 'The rebar ties are in the blue van, not the shop'
    await send(pg, secret)
    shown = await pg.evaluate("() => document.getElementById('chat-list').innerText")
    c.ok(secret in shown, 'dm: the sender sees the line in the thread')
    toast = await pg.evaluate("() => document.getElementById('toast').innerText")
    c.ok('Sent to' in toast and 'Open' in toast, f'dm: the send toasts with Open ({toast!r})')
    members = {'u_chen', 'u_alberto'}
    for u in USERS:
        await sign_in(pg, u)
        await go(pg, 'chat')
        await pg.wait_for_timeout(150)
        r = await pg.evaluate("""([k, s]) => ({ list: msgThreadsFor().some(T => T.key === k), screen: document.body.innerText.includes(s),
             ask: (EQ_TABLES.chat ? EQ_TABLES.chat() : []).some(x => (x.text || '').includes(s)),
             open: (() => { const T = msgThread(k); return !!T; })() })""", [key, secret[:30]])
        m = u in members
        # the owner reads every chat (Alan, 2026-10-19: "I should always have admin privileges"), from All Chats; it is
        # not in his own list and he writes in it only after joining
        c.ok(r['list'] == m and r['open'] == (m or u == 'u_owner'), f"dm: {u} {'has' if m else 'has not'} the thread in their list ({r})")
        c.ok(r['screen'] == (m and u != 'u_chen' or u == 'u_chen'), f"dm: {u} {'reads' if m else 'does not read'} the line on Chat ({r['screen']})")
        c.ok(r['ask'] == m, f"dm: Ask's query layer gives the line to {u} only if a member ({r['ask']})")
    # Alberto reads it: one unread, then none
    await sign_in(pg, 'u_alberto')
    n = await pg.evaluate("() => msgUnreadTotal().n")
    c.ok(n == 1, f'dm: Alberto has one unread message ({n})')
    await open_thread(pg, key)
    n = await pg.evaluate("() => msgUnreadTotal().n")
    c.ok(n == 0, f'dm: opening the thread reads it ({n})')
    c.ok(not errs, f'dm: no page errors {errs[:2]}')
    await b.close()


# ------------------------------------------------------------------------------------------------ 3. field money
async def t_field_money(c, p):
    b, pg, errs = await fresh(p, 'u_chen')
    po = await pg.evaluate("() => { const po = DB.pos.find(x => x.projectId === 'p121'); return [po.number, po.id, money(poTotal(po).total)] }")
    await pg.evaluate("() => { setCurrent('p121'); msgOpen('job:p121'); }")
    await send(pg, f'{po[0]} lands Friday, check the count when it comes')
    office = await pg.evaluate("() => [...document.querySelectorAll('#chat-list .msg-card')].map(e => e.innerText)")
    c.ok(any(po[0] in x for x in office), f'field: the PO number in a line becomes its card ({office})')
    c.ok(any('$' in x for x in office), f'field: the office reads the order total on the card ({office})')
    inv = await pg.evaluate("() => { const c = DB.clients.find(x => x.id === 'cl121'); return (c.invoices || [])[0].number }")
    await pg.evaluate("n => { const P = DB.projects.find(x => x.id === 'p121'); P.chat.push(msgLine('Sharing the bill for the file', { cards: msgCardsIn(n), aud: 'team' })); save(); }", inv)
    for u in ('u_angel', 'u_alberto', 'u_alex'):
        await sign_in(pg, u)
        await pg.evaluate("() => { setCurrent('p121'); msgOpen('job:p121'); }")
        await pg.wait_for_timeout(200)
        t = await pg.evaluate("() => document.getElementById('chat-list').innerText")
        c.ok(po[0] in t, f'field: {u} reads the order card ({po[0]})')
        c.ok('$' not in t and po[2] not in t, f'field: {u} reads no amount on the thread ({t[-200:]!r})')
        c.ok('Sharing the bill' not in t and inv not in t, f'field: {u} never receives the invoice card')
    await pg.click('#chat-list .msg-card')
    await pg.wait_for_timeout(300)
    mt = await pg.evaluate("() => (document.getElementById('mbm') || {}).innerText || ''")
    c.ok(po[0] in mt and '$' not in mt, f'field: the card opens as a summary with no money ({mt[:200]!r})')
    c.ok(not errs, f'field: no page errors {errs[:2]}')
    await b.close()


# ------------------------------------------------------------------------------------------------ 4. @assistant
async def t_assistant(c, p):
    b, pg, errs = await fresh(p, 'u_alan')
    await pg.evaluate("() => { setCurrent('p121'); msgOpen('job:p121'); }")
    n0 = await pg.evaluate("() => DB.projects.find(x => x.id === 'p121').chat.length")
    await send(pg, '@assistant what is late on 121 State Street')
    await pg.wait_for_timeout(1200)
    r = await pg.evaluate("""() => { const a = [...document.querySelectorAll('#chat-list .msg-ai')].map(e => e.innerText);
       return { a, n: DB.projects.find(x => x.id === 'p121').chat.length, mine: (DB.asst.u_alan.inThread || []).length, busy: (DB.asst.u_alan.inThread || []).some(x => x.busy) } }""")
    c.ok(len(r['a']) == 1 and 'only you see this' in r['a'][0], f"assistant: the answer shows in the thread, marked as the asker's own ({r['a']})")
    c.ok(r['a'] and 'You asked' in r['a'][0] and not r['busy'], 'assistant: the answer came back from the records')
    hl = await pg.evaluate("() => (DB.asst.u_alan.inThread.slice(-1)[0] || {}).headline || ''")
    c.ok(len(hl) > 10 and not hl.startswith('I could not answer'), f'assistant: it answers through Ask ({hl[:120]!r})')
    c.ok(r['n'] == n0, f"assistant: nothing was posted to the shared thread ({n0} -> {r['n']})")
    c.ok(r['mine'] == 1, "assistant: the answer is kept with Alan's own assistant")
    await sign_in(pg, 'u_chen')
    await pg.evaluate("() => { setCurrent('p121'); msgOpen('job:p121'); }")
    t = await pg.evaluate("() => document.getElementById('chat-list').innerText")
    c.ok('only you see this' not in t and hl[:30] not in t, 'assistant: another member of the thread never sees it')
    # the field's assistant, asked about money in the thread
    await sign_in(pg, 'u_angel')
    await pg.evaluate("() => { setCurrent('p121'); msgOpen('job:p121'); }")
    await send(pg, '@assistant how much cash do we have')
    await pg.wait_for_timeout(1200)
    a = await pg.evaluate("() => [...document.querySelectorAll('#chat-list .msg-ai')].map(e => e.innerText).join(' | ')")
    c.ok(a and not re.search(r'\$\s?\d', a), f"assistant: the foreman's answer carries no money ({a[:200]!r})")
    # a line that mentions the assistant mid-sentence is posted, and answered privately
    await send(pg, 'Drywall is up on 3 @assistant when is the next inspection')
    await pg.wait_for_timeout(1000)
    r = await pg.evaluate("() => { const P = DB.projects.find(x => x.id === 'p121'); return { last: P.chat.slice(-1)[0].text, ai: (DB.asst.u_angel.inThread || []).length } }")
    c.ok('Drywall is up on 3' in r['last'] and r['ai'] == 2, f'assistant: the line is posted and the question answered ({r})')
    c.ok(not errs, f'assistant: no page errors {errs[:2]}')
    await b.close()


# ------------------------------------------------------------------------------------------------ 5. message to task
async def t_task(c, p):
    b, pg, errs = await fresh(p, 'u_owner')
    await pg.evaluate("() => { setCurrent('p121'); msgOpen('job:p121'); }")
    await send(pg, 'Order the brass hinges for the parlor doors')
    await pg.click('#chat-list .cm.me:last-of-type [data-msgtask]')
    await pg.wait_for_timeout(400)
    r = await pg.evaluate("""() => { const P = DB.projects.find(x => x.id === 'p121'), m = P.chat.slice(-1)[0], a = (P.actions || []).find(x => x.id === m.taskId);
       return { link: !!m.taskId, a: a && [a.title, a.assignee, a.due, a.status, (a.source || {}).chat ? 1 : 0], toast: document.getElementById('toast').innerText } }""")
    c.ok(r['link'] and r['a'] and r['a'][0] == 'Order the brass hinges for the parlor doors', f"task: one tap makes the task, linked from the line ({r['a']})")
    c.ok(r['a'] and r['a'][1] == 'Owner' and r['a'][2] == '2026-09-03' and r['a'][4] == 1, f"task: on the owner, due today, pointing back at the message ({r['a']})")
    c.ok('Open' in r['toast'], f"task: the toast has Open ({r['toast']!r})")
    # the owner's own Tasks list shows it (findable, not just saved)
    await pg.evaluate("() => { view = 'tkall'; render(); tkWho = 'me'; t2View = 'all'; tkProject = ''; tkArea = ''; tkPri = ''; t2Q = ''; tkQueue = ''; tkPerson = ''; render(); }")
    await pg.wait_for_timeout(300)
    t = await pg.evaluate("() => document.querySelector('.view.on').innerText")
    c.ok('Order the brass hinges for the parlor doors' in t, "task: it is on the owner's own Tasks list")
    # (Do Now's ranked queue holds no plain tasks on this build; the "today" lane unifies tasks into it tonight.)
    await pg.evaluate("() => msgOpen('job:p121')")
    btn = await pg.evaluate("() => [...document.querySelectorAll('#chat-list [data-msgtaskopen]')].map(e => e.innerText.trim())")
    c.ok('Open Task' in btn, f'task: the line now reads Open Task ({btn})')
    c.ok(not errs, f'task: no page errors {errs[:2]}')
    await b.close()


# ------------------------------------------------------------------------------------------------ 6. unread
async def t_unread(c, p):
    b, pg, errs = await fresh(p, 'u_alberto')
    await pg.evaluate("() => { setCurrent('p121'); msgOpen('job:p121'); }")
    await send(pg, 'Plumber is here early')
    await send(pg, '@Chen can you check when the vanity ships')
    await sign_in(pg, 'u_chen')
    await pg.evaluate("() => { setCurrent('p121'); view = 'dash'; render(); }")
    await pg.wait_for_timeout(200)
    r = await pg.evaluate("""() => { const T = msgThread('job:p121'), u = msgUnread(T), tot = msgUnreadTotal();
       return { u, tot, badges: [...document.querySelectorAll('#tb-chat, [data-v="chat"], [data-mv="chat"], [data-tab="chat"], [data-sub="chat"]')].filter(e => e.getClientRects().length).map(e => (e.querySelector('.n') || {}).textContent || '') } }""")
    c.ok(r['u']['n'] == 2 and r['u']['at'] == 1, f"unread: Chen has 2 unread on the job's thread, one naming him ({r['u']})")
    c.ok(r['badges'] and all(x == str(r['tot']['n']) for x in r['badges']), f"unread: every Chat entry on screen shows the same number ({r['badges']} vs {r['tot']['n']})")
    # the thread list (desktop): row and total agree with the badge; open a different thread so 121's row stays unread
    await open_thread(pg, 'dm:th_seed_dm')
    r = await pg.evaluate("""() => { const row = document.querySelector('#msg-side [data-msgopen="job:p121"]'), tot = document.querySelector('#msg-side .msg-tot');
       return { row: row ? (row.querySelector('.n') || {}).textContent : null, at: row ? !!row.querySelector('.msg-atn') : false, tot: tot ? tot.textContent : '', total: msgUnreadTotal().n,
         badges: [...document.querySelectorAll('#tb-chat, [data-v="chat"], [data-mv="chat"], [data-tab="chat"], [data-sub="chat"]')].filter(e => e.getClientRects().length).map(e => (e.querySelector('.n') || {}).textContent || '') } }""")
    c.ok(r['row'] == '2' and r['at'], f"unread: the thread's row reads 2 and marks the mention ({r})")
    c.ok(r['tot'] == str(r['total']) and all(x == r['tot'] for x in r['badges']), f"unread: the list's total equals the badge ({r})")
    await open_thread(pg, 'job:p121')
    r = await pg.evaluate("() => ({ total: msgUnreadTotal().n, badges: [...document.querySelectorAll('#tb-chat, [data-sub=\"chat\"], [data-v=\"chat\"]')].filter(e => e.getClientRects().length).map(e => (e.querySelector('.n') || {}).textContent || '') })")
    c.ok(r['total'] == 0 and all(x == '' for x in r['badges']), f'unread: reading the thread clears the count everywhere ({r})')
    # the phone: the back bar carries the same number as the tab
    b2, pg2, errs2 = await fresh(p, 'u_alberto', phone=True)
    await pg2.evaluate("() => { const t = msgDirectWith('u_chen', true); t.t.msgs.push({ id: 'pm1', by: 'Chen Biron', fromUid: 'u_chen', text: 'Can you bring the ladder back to the shop?', t: '9/3, 10:00 AM', at: '2026-09-03T10:00:00', files: [] }); setCurrent('p121'); msgOpen('job:p121'); }")
    await pg2.wait_for_timeout(200)
    r = await pg2.evaluate("""() => ({ back: (document.querySelector('[data-msgback] .n') || {}).textContent || '', tab: [...document.querySelectorAll('[data-tab="chat"], [data-mv="chat"], [data-v="chat"]')].filter(e => e.getClientRects().length).map(e => (e.querySelector('.n') || {}).textContent || ''), total: msgUnreadTotal().n })""")
    c.ok(r['total'] == 1 and r['back'] == '1' and r['tab'] and all(x == '1' for x in r['tab']), f'unread: on the phone the back bar and the tab read the same 1 ({r})')
    c.ok(not errs and not errs2, f'unread: no page errors {errs[:2]} {errs2[:2]}')
    await b2.close()
    await b.close()


# ------------------------------------------------------------------------------------------------ 7. phone 390
async def t_phone(c, p):
    b, pg, errs = await fresh(p, 'u_alberto', phone=True)
    await pg.evaluate("() => { setCurrent('p121'); view = 'chat'; render(); }")
    await pg.wait_for_timeout(300)
    hit = await pg.evaluate("() => { const t = document.getElementById('chat-text'), r = t.getBoundingClientRect(), e = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2); return { hit: e === t, w: r.width, h: r.height, bottom: r.bottom, vh: innerHeight } }")
    c.ok(hit['hit'] and hit['w'] >= 140 and hit['h'] >= 44 and hit['bottom'] <= hit['vh'], f'phone: the box is on screen, wide enough and not covered ({hit})')
    await pg.tap('#chat-text')
    await pg.keyboard.type('Drywall delivered to the 3rd floor')
    await pg.keyboard.press('Enter')
    await pg.wait_for_timeout(500)
    # the round button at the right is Send while there is text and the microphone once the box is empty (2026-10-19)
    r = await pg.evaluate("""() => { const b = [document.getElementById('chat-send'), document.getElementById('msg-voice')].find(e => e && e.getClientRects().length), s = b.getBoundingClientRect(); return { list: document.getElementById('chat-list').innerText, box: document.getElementById('chat-text').value, sw: document.documentElement.scrollWidth,
        send: [s.width, s.height, s.right] } }""")
    c.ok('Drywall delivered to the 3rd floor' in r['list'] and r['box'] == '', f"phone: Enter sends and clears the box ({r['box']!r})")
    c.ok(r['sw'] <= 390, f"phone: no sideways scroll ({r['sw']})")
    c.ok(r['send'][1] >= 44 and r['send'][2] <= 390, f"phone: the round Send (or microphone) is a big target, on the screen ({r['send']})")
    # the list: back, then a thread
    await pg.tap('[data-msgback]')
    await pg.wait_for_timeout(250)
    r = await pg.evaluate("() => ({ side: !!document.querySelector('#msg-side').getClientRects().length, main: !!document.querySelector('.msg-main').getClientRects().length, rows: [...document.querySelectorAll('#msg-side .msg-row')].map(e => Math.round(e.getBoundingClientRect().height)), sw: document.documentElement.scrollWidth })")
    c.ok(r['side'] and not r['main'], f'phone: All Messages shows the list on its own ({r})')
    c.ok(r['rows'] and min(r['rows']) >= 44 and r['sw'] <= 390, f'phone: each row is a big target, no sideways scroll ({r})')
    # a job conversation with nothing in it yet sits under "Start a Chat on a Job" (2026-10-20): one tap opens that row
    if not await pg.evaluate("() => { const r = document.querySelector('#msg-side [data-msgopen=\"job:p206\"]'); return !!(r && r.offsetParent); }"):
        await pg.tap('#msg-side [data-msgquiet]'); await pg.wait_for_timeout(250)
    await pg.tap('#msg-side [data-msgopen="job:p206"]')
    await pg.wait_for_timeout(250)
    r = await pg.evaluate("() => ({ key: msgCur().key, main: !!document.querySelector('.msg-main').getClientRects().length, head: document.getElementById('msg-head').innerText })")
    c.ok(r['key'] == 'job:p206' and r['main'] and '206 Lenox' in r['head'], f'phone: a tap opens the thread ({r})')
    # a photo from the existing pipeline: a posted image becomes a photo card and joins the job's photo stream
    n0 = await pg.evaluate("() => (DB.photos || []).length")
    await pg.set_input_files('#chat-file', files=[{'name': 'wall.png', 'mimeType': 'image/png', 'buffer': bytes.fromhex(
        '89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d4944415478da63f8cfc0f01f0005000201a1e7d6a20000000049454e44ae426082')}])
    await pg.wait_for_timeout(1500)
    r = await pg.evaluate("() => { const P = DB.projects.find(x => x.id === 'p206'), m = P.chat.slice(-1)[0]; return { cards: (m && m.cards || []).map(c => c.kind), photos: (DB.photos || []).length, src: ((DB.photos || []).slice(-1)[0] || {}).source } }")
    c.ok('photo' in r['cards'] and r['photos'] == n0 + 1, f'phone: a posted photo is a photo card and in the photo stream ({r}, {n0})')
    c.ok(not errs, f'phone: no page errors {errs[:2]}')
    await b.close()


# ------------------------------------------------------------------------------------------------ 8. client
async def t_client(c, p):
    b, pg, errs = await fresh(p, 'u_alberto')
    await pg.evaluate("() => { setCurrent('p121'); msgOpen('job:p121'); }")
    await send(pg, 'Garden bedroom framing is done, the plumber starts tomorrow')
    await sign_in(pg, 'u_klein')
    await go(pg, 'chat')
    r = await pg.evaluate("() => ({ threads: msgThreadsFor().map(t => t.key), list: document.getElementById('chat-list').innerText, side: !!document.querySelector('#msg-side').getClientRects().length })")
    c.ok(r['threads'] == ['client:p121'], f"client: Sarah Klein has only her job's client thread ({r['threads']})")
    c.ok('Garden bedroom framing' not in r['list'], 'client: the team thread is not hers to read')
    c.ok(not r['side'], 'client: one thread, no list to pick from')
    await send(pg, 'Will the tile be in before Thanksgiving?')
    t = await pg.evaluate("() => document.getElementById('chat-list').innerText")
    c.ok('Sent to Alan' in t, f'client: her question reads "Sent to Alan" ({t[-160:]!r})')
    # the PM answers in the client thread; the open question closes
    await sign_in(pg, 'u_alan')
    await pg.evaluate("() => { setCurrent('p121'); msgOpen('client:p121'); }")
    head = await pg.evaluate("() => document.getElementById('msg-head').innerText")
    c.ok('Client Sees This' in head and 'reads everything' in head, f'client: the office sees the client thread marked unmistakably ({head!r})')
    await send(pg, 'Yes, the tile lands Sep 18, well before Thanksgiving.')
    r = await pg.evaluate("() => { const P = DB.projects.find(x => x.id === 'p121'); return { open: (P.clientQs || []).filter(q => q.status === 'open').length, last: P.chat.slice(-1)[0] } }")
    c.ok(r['open'] == 0 and r['last'].get('answerOf'), f"client: the PM's reply answers her open question ({r['open']})")
    await sign_in(pg, 'u_klein')
    await go(pg, 'chat')
    t = await pg.evaluate("() => document.getElementById('chat-list').innerText")
    c.ok('Sep 18' in t and 'Garden bedroom framing' not in t, 'client: she reads the answer and nothing of the team')
    n = await pg.evaluate("() => msgUnreadTotal().n")
    c.ok(n == 0, f'client: reading it clears her count ({n})')
    # another client: their own job only
    await sign_in(pg, 'u_cambri')
    await go(pg, 'chat')
    r = await pg.evaluate("() => ({ threads: msgThreadsFor().map(t => t.key), text: document.getElementById('chat-list').innerText })")
    c.ok(r['threads'] == ['client:p140'] and 'Thanksgiving' not in r['text'], f"client: the Jessops read only their own thread ({r['threads']})")
    c.ok(not errs, f'client: no page errors {errs[:2]}')
    await b.close()


async def main():
    c = Checks()
    async with async_playwright() as p:
        for t in (t_migrate, t_dm, t_field_money, t_assistant, t_task, t_unread, t_phone, t_client):
            try:
                await t(c, p)
            except Exception as e:
                c.ok(False, f'{t.__name__}: {type(e).__name__}: {str(e)[:300]}')
    return c.done()

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
