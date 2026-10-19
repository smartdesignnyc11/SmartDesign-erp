"""The one assistant per person (BACKLOG §1.27, §1.24 page side; lane "assistant", 2026-10-19).

  1. fold      Assistant, Chief of Staff, The Brain and the morning brief are one view ('pa') with four tabs: Chat,
               Findings, Activity, Brain Settings (owner only). 'cos' and 'brain' redirect to the right tab; the nav
               has no entries of their own; one #brain-body and one #cos-body; Ask from anywhere opens Chat.
  2. findings  every row carries the "because" and the Standard value; the tab's count is the rows it lists; Caught
               holds the same rows as Today's Caught for You.
  3. rules     each action type is Act Alone, Ask First or Hand It to Me; defaults from the Standard (money,
               commitments and changes to the books never Act Alone; nothing that reaches a client or vendor Act Alone
               by default); the person changes their own on Activity; the owner sees and changes anyone's on Brain
               Settings, except handing over someone's outgoing messages; one store (DB.asst[uid].delegated/handIt),
               one log; the Connections card is the same control.
  4. acts      a type set to Act Alone runs and is logged in Activity with its evidence and reason; Ask First is a
               proposal whose approval is logged; Hand It to Me hands it back as a Finding; a "remember" the person
               did not say waits; a Never is refused.
  5. stream    served over http with a door that streams: the answer renders as it arrives and ends equal to the final
               message; a tool round inside a stream; a cut stream shows the note; a broken stream falls back to the
               one-JSON call; a markdown table and links render; file:// never streams.
  6. history   New Chat files the conversation in the side panel; pressing a past one continues it.
  7. attach    a PDF goes to the document reader (/api/doctext, mocked) and rides with the question as untrusted data;
               on file:// the reader is out of reach and says so.
  8. phone     390 px: every tab and part passes the screen standard (lint.py's own collector), no sideways scroll.
"""
import asyncio, json, os, re, sys, threading, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from harness import *

HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.environ.get('SD_DIST') or os.path.join(ROOT, 'dist', 'smartdesigns_projects.html')

# ---------------------------------------------------------------------------------------------- SSE helpers
def ev(name, data): return f"event: {name}\ndata: {json.dumps(data)}\n\n"
def msg_start(i='msg_1'): return ev('message_start', {'type': 'message_start', 'message': {'id': i, 'type': 'message', 'role': 'assistant', 'model': 'claude-sonnet-5-5', 'content': [], 'stop_reason': None, 'usage': {'input_tokens': 12, 'output_tokens': 1}}})
def text_events(pieces, index=0):
    out = ev('content_block_start', {'type': 'content_block_start', 'index': index, 'content_block': {'type': 'text', 'text': ''}})
    out += ''.join(ev('content_block_delta', {'type': 'content_block_delta', 'index': index, 'delta': {'type': 'text_delta', 'text': p}}) for p in pieces)
    return out + ev('content_block_stop', {'type': 'content_block_stop', 'index': index})
def msg_end(reason='end_turn', cut=False):
    return (ev('message_delta', {'type': 'message_delta', 'delta': {'stop_reason': reason, 'stop_sequence': None}, 'usage': {'output_tokens': 40}}) +
            ev('message_stop', {'type': 'message_stop'}) + ev('sd_done', {'usage': {'input_tokens': 12, 'output_tokens': 40}, 'cut': cut}))

STREAM_TEXT = ['Here is ', 'where the jobs ', 'stand today.\n\n', '| Job | Status |\n', '|---|---|\n', '| 121 State | On track |\n',
               '| 45 Cranberry | Waiting on tile |\n\n', 'The full plan is on ', '[the schedule](https://example.com/schedule).']
SEEN = []   # what the page sent the AI door

class Door(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path.split('?')[0] in ('/', '/index.html'):
            body = open(DIST, 'rb').read()
            self.send_response(200); self.send_header('content-type', 'text/html; charset=utf-8'); self.send_header('content-length', str(len(body))); self.end_headers(); self.wfile.write(body)
        else:
            self.send_response(404); self.end_headers()
    def do_POST(self):
        n = int(self.headers.get('content-length') or 0)
        raw = self.rfile.read(n) if n else b''
        try: body = json.loads(raw or b'{}')
        except Exception: body = {}
        if self.path.startswith('/api/ai'):
            SEEN.append(body)
            if body.get('stream') == 'client':
                self.send_response(200); self.send_header('content-type', 'text/event-stream'); self.send_header('cache-control', 'no-store'); self.send_header('connection', 'close'); self.end_headers()
                self.wfile.write(msg_start().encode()); self.wfile.flush()
                self.wfile.write(ev('content_block_start', {'type': 'content_block_start', 'index': 0, 'content_block': {'type': 'text', 'text': ''}}).encode()); self.wfile.flush()
                for p in STREAM_TEXT:
                    time.sleep(0.35)
                    self.wfile.write(ev('content_block_delta', {'type': 'content_block_delta', 'index': 0, 'delta': {'type': 'text_delta', 'text': p}}).encode()); self.wfile.flush()
                self.wfile.write((ev('content_block_stop', {'type': 'content_block_stop', 'index': 0}) + msg_end()).encode()); self.wfile.flush()
                return
            out = json.dumps({'id': 'msg_j', 'type': 'message', 'role': 'assistant', 'model': 'claude-sonnet-5-5', 'content': [{'type': 'text', 'text': 'One plain answer.'}], 'stop_reason': 'end_turn', 'usage': {'input_tokens': 5, 'output_tokens': 4}}).encode()
            self.send_response(200); self.send_header('content-type', 'application/json'); self.send_header('content-length', str(len(out))); self.end_headers(); self.wfile.write(out)
            return
        self.send_response(404); self.end_headers()

def serve():
    s = ThreadingHTTPServer(('127.0.0.1', 0), Door)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, f'http://127.0.0.1:{s.server_address[1]}/'

async def open_http(p, url, phone=False):
    b = await p.chromium.launch()
    ctx = await b.new_context(viewport=PHONE if phone else DESKTOP, is_mobile=phone, has_touch=phone)
    pg = await ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('console', lambda m: m.type == 'error' and 'fonts.g' not in m.text and 'ERR_' not in m.text and 'Failed to load resource' not in m.text and errs.append('console: ' + m.text))
    await pg.goto(url)
    await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
    return b, pg, errs

async def ask_and_wait(pg, q, timeout=20000):
    n = await pg.evaluate("() => paInit().thread.filter(m => m.who === 'a').length")
    await pg.fill('#pa-in', q)
    await pg.evaluate("() => document.querySelector('#pa-ask').requestSubmit()")
    await pg.wait_for_function("n => !paBusy && paInit().thread.filter(m => m.who === 'a').length > n", arg=n, timeout=timeout)
    await pg.wait_for_timeout(150)
    return await pg.evaluate("() => { const m = paInit().thread.filter(m => m.who === 'a').slice(-1)[0]; const els = [...document.querySelectorAll('#pa-thread .pa-m.a')]; const el = els[els.length - 1]; return { text: m.text, md: !!m.md, did: m.did || [], cut: !!m.cut, html: el ? el.innerHTML : '', shown: el ? el.innerText : '' } }")

norm = lambda s: re.sub(r'\s+', ' ', s or '').strip()

# ---------------------------------------------------------------------------------------------- 1, 2: fold, findings
async def sec_fold(p, c):
    b, pg, errs = await open_app(p)
    await sign_in(pg, 'u_owner')
    nav = await pg.evaluate("() => ({ ia: IA_GROUPS.flatMap(g => g.views), nav: (typeof NAV_GROUPS !== 'undefined' ? NAV_GROUPS : []).flatMap(g => g.views), rv: ['cos', 'brain', 'pa'].map(v => ROLE_VIEWS.owner.includes(v)) })")
    c.ok('cos' not in nav['ia'] and 'brain' not in nav['ia'] and 'cos' not in nav['nav'] and 'brain' not in nav['nav'], 'the nav has no Chief of Staff or The Brain entries of their own')
    c.ok(all(nav['rv']), f"the old ids stay openable (they redirect): {nav['rv']}")
    await go(pg, 'cos')
    r = await pg.evaluate("() => ({ view, tab: paTab, seg: paFindSeg, h: document.querySelector('.view.on h2').textContent, t: document.querySelector('.view.on').innerText, n: document.querySelectorAll('#cos-body').length, inPa: !!document.querySelector('#v-pa #cos-body') })")
    c.ok(r['view'] == 'pa' and r['tab'] == 'findings' and r['seg'] == 'chains', f"'cos' opens the assistant's Findings › Every Chain: {r['view']} {r['tab']} {r['seg']}")
    c.ok(r['n'] == 1 and r['inPa'] and 'bank items not yet matched' in r['t'], "the Chief of Staff's pass draws inside the tab, once")
    # the menu (lane "menu") keeps the Chief of Staff as its own entry and lights it on this tab; the heading reads as it
    want = await pg.evaluate("() => { const b = document.querySelector('#subnav .sub-tabs button.on') || document.querySelector('#nav-groups button.on'); return b ? (b.innerText || b.textContent).replace(/\\s+/g, ' ').replace(/\\s*\\d+$/, '').trim() : IA_LABELS.pa; }")
    c.ok(r['h'] == want == 'Chief of Staff', f"one page heading, the menu's lit entry: {r['h']!r} vs {want!r}")
    await go(pg, 'brain')
    r = await pg.evaluate("() => ({ view, tab: paTab, t: document.querySelector('.view.on').innerText, n: document.querySelectorAll('#brain-body').length, tabs: [...document.querySelectorAll('.view.on .pa-tabs [data-patab]')].map(b => b.dataset.patab), h2: [...document.querySelectorAll('.view.on h2')].length })")
    c.ok(r['view'] == 'pa' and r['tab'] == 'brain' and r['n'] == 1, f"'brain' opens Brain Settings for the owner: {r['view']} {r['tab']} {r['n']}")
    c.ok('Approval Rules, Everyone' in r['t'] and re.search(r'Lessons', r['t']), 'Brain Settings holds everyone\'s approval rules and The Brain')
    c.ok(r['tabs'] == ['chat', 'findings', 'activity', 'brain'] and r['h2'] == 1, f"four tabs, one heading: {r['tabs']} h2={r['h2']}")
    await go(pg, 'home'); await go(pg, 'pa')
    c.ok(await pg.evaluate("paTab") == 'chat', 'Ask from another screen opens the conversation')
    t = await pg.evaluate("() => { paOpen('findings'); const a = paTab; setView('pa'); return [a, paTab, !!document.getElementById('pa-in')] }")
    c.ok(t == ['findings', 'chat', True], f'Ask (the rail, the button) opens the conversation even from Findings: {t}')
    await pg.evaluate("() => openAI('brief')"); await pg.wait_for_timeout(200)
    r = await pg.evaluate("() => ({ view, tab: paTab, brief: !!document.querySelector('.view.on .paf-brief') })")
    c.ok(r['view'] == 'pa' and r['tab'] == 'findings' and r['brief'], f'the morning brief opens Findings, the brief on top: {r}')
    # findings: one number, every row with its because and value
    f = await pg.evaluate("""() => { const rows = [...document.querySelectorAll('.view.on .paf-row')]; const all = paFindings();
        return { tabN: +((document.querySelector('.view.on [data-patab="findings"] .pa-tabn') || {}).textContent || 0), listN: +document.querySelector('.view.on .paf-list').dataset.pafcount, all: all.length,
                 caught: all.filter(r => r.group === 'caught').length, td: tdCaught([]).length, why: rows.filter(r => /Because:/.test(r.innerText)).length, rows: rows.length,
                 vals: rows.filter(r => r.querySelector('.paf-val')).length } }""")
    c.ok(f['tabN'] == f['listN'] == f['all'] and f['all'] > 0, f"the Findings tab's count is the rows it lists: tab {f['tabN']}, list {f['listN']}, rows {f['all']}")
    c.ok(f['caught'] == f['td'], f"Caught holds the same rows as Today's Caught for You: {f['caught']} vs {f['td']}")
    c.ok(f['why'] == f['rows'] and f['vals'] >= f['rows'] - 2, f"every finding says why and names the value: because {f['why']}/{f['rows']}, value {f['vals']}")
    # the PM: Findings › The Brain, no Brain Settings
    await sign_in(pg, 'u_alan'); await go(pg, 'brain')
    r = await pg.evaluate("() => ({ view, tab: paTab, seg: paFindSeg, tabs: [...document.querySelectorAll('.view.on [data-patab]')].map(b => b.dataset.patab), hands: !!document.querySelector('.view.on #brain-body [data-bntab=\"hands\"]') })")
    c.ok(r['tab'] == 'findings' and r['seg'] == 'brain' and 'brain' not in r['tabs'] and r['hands'], f"for the PM, 'brain' opens Findings › The Brain, with Hands; no Brain Settings: {r}")
    # the client keeps their Ask surface; the old ids are not theirs to open
    await sign_in(pg, 'u_klein'); await go(pg, 'pa')
    r = await pg.evaluate("() => ({ tabs: document.querySelectorAll('.view.on .pa-tabs').length, inp: !!document.getElementById('pa-in') })")
    c.ok(r['tabs'] == 0 and r['inp'], f'the client keeps a plain Ask, no tabs: {r}')
    c.ok(not errs, f'fold: page errors {errs[:3]}')
    await b.close()

# ---------------------------------------------------------------------------------------------- 3, 4: rules, acts
async def sec_rules(p, c):
    b, pg, errs = await open_app(p)
    await sign_in(pg, 'u_owner')
    d = await pg.evaluate("""() => STD_SEND_TYPES.map(t => ({ id: t.id, kind: t.kind, def: t.def, lock: !!t.lock }))""")
    ids = [x['id'] for x in d]
    c.ok({'orderFollowups', 'rfqChases', 'followUps', 'draftEmail', 'makeTasks', 'holdTime', 'bookMeetings', 'fileDocuments', 'money', 'commitClient'} <= set(ids), f'every action type is on the one list: {ids}')
    c.ok(all(x['def'] != 'alone' for x in d if x['kind'] in ('send', 'money', 'commit')), 'nothing that sends, pays or commits is Act Alone by default')
    c.ok(all(x['lock'] for x in d if x['kind'] in ('money', 'commit')), 'money, commitments and changes to the books are locked: never Act Alone')
    dflt = await pg.evaluate("() => ['draftEmail', 'makeTasks', 'money', 'clientMessages', 'followUps'].map(t => paRule(t, 'u_alan'))")
    c.ok(dflt == ['alone', 'ask', 'ask', 'ask', 'ask'], f'the defaults from the Standard (drafting alone; tasks, money, client and vendor mail ask): {dflt}')
    c.ok(await pg.evaluate("() => paRule('orderFollowups', 'u_chen')") == 'alone', "the coordinator's order follow-ups stay Act Alone (the track lane's install default)")
    no = await pg.evaluate("() => [paRuleSet(paMe().id, 'money', 'alone'), paRule('money')]")
    c.ok(no == [False, 'ask'], f'nobody can set money to Act Alone: {no}')
    # the person sets their own, on Activity
    await sign_in(pg, 'u_alan'); await go(pg, 'pa')
    await pg.click('.view.on [data-patab="activity"]'); await pg.wait_for_timeout(200)
    await pg.click('.view.on [data-parule="u_alan|makeTasks|alone"]'); await pg.wait_for_timeout(300)
    r = await pg.evaluate("() => ({ lv: paRule('makeTasks'), del: DB.asst.u_alan.delegated.slice(), log: DB.company.delegationLog.slice(-1)[0], toast: document.getElementById('toast').innerText, on: !!document.querySelector('.view.on [data-parule=\"u_alan|makeTasks|alone\"].on') })")
    c.ok(r['lv'] == 'alone' and 'makeTasks' in r['del'] and r['on'], f'Alan sets Tasks for Me to Act Alone on Activity: {r["lv"]} {r["del"]}')
    c.ok(r['log']['by'] == 'Alan Mishali' or r['log']['byUid'] == 'u_alan', f"the change is logged with who: {r['log']}")
    c.ok(r['log']['level'] == 'alone' and 'Open' in r['toast'], f"the log says the level and the toast has Open: {r['log'].get('level')} {r['toast']!r}")
    # the owner sees and changes anyone's on Brain Settings
    await sign_in(pg, 'u_owner'); await go(pg, 'brain')
    await pg.select_option('.view.on [data-paruleswho]', 'u_alan'); await pg.wait_for_timeout(300)
    await pg.click('.view.on [data-parule="u_alan|holdTime|hand"]'); await pg.wait_for_timeout(300)
    r = await pg.evaluate("() => ({ lv: paRule('holdTime', 'u_alan'), hand: (DB.asst.u_alan.handIt || []).slice(), by: DB.company.delegationLog.slice(-1)[0].by, dis: document.querySelector('.view.on [data-parule=\"u_alan|followUps|alone\"]').disabled })")
    c.ok(r['lv'] == 'hand' and 'holdTime' in r['hand'] and r['by'] != 'Alan Mishali', f"the owner changes Alan's rule: {r}")
    c.ok(r['dis'], "only Alan can hand over his own outgoing messages: the owner's Act Alone on his follow-ups is disabled")
    c.ok(await pg.evaluate("() => paRuleSet('u_alan', 'followUps', 'alone')") is False, 'and refused if called')
    one = await pg.evaluate("""async () => { view = 'conn'; render(); await new Promise(r => setTimeout(r, 250)); return { n: document.querySelectorAll('#trk-deleg').length, rows: document.querySelectorAll('#trk-deleg [data-trkdeleg]').length, segs: document.querySelectorAll('#trk-deleg [data-parule]').length } }""")
    c.ok(one['n'] == 1 and one['rows'] >= 5 and one['segs'] == one['rows'] * 3, f'Settings › Connections shows the same control (one card): {one}')
    keys = await pg.evaluate("() => Object.keys(DB.asst.u_alan).sort()")
    c.ok('rules' not in keys and 'approval' not in keys, f'one store: the rules live on delegated/handIt: {keys}')
    c.ok(not errs, f'rules: page errors {errs[:3]}')
    await b.close()

async def sec_acts(p, c):
    b, pg, errs = await open_app(p)
    await sign_in(pg, 'u_alan')
    # Act Alone: the task is made, logged with evidence and reason, and findable
    r = await pg.evaluate("""async () => { paRuleSet(paMe().id, 'makeTasks', 'alone'); paLiveQ = 'remind me to call the tile supplier';
        const out = await mindTool('create_task', { title: 'Call the tile supplier about the grout', due: '2026-09-04' });
        const L = paInit().log[0]; const mine = openTasks('me').some(t => /tile supplier about the grout/.test(t.title));
        return { out, L, mine } }""")
    c.ok(r['out'].get('created') and r['out'].get('onItsOwn'), f"a type set to Act Alone runs at once: {r['out']}")
    c.ok(r['L']['kind'] == 'did' and r['L']['type'] == 'makeTasks' and r['L']['ev'] and 'Act Alone' in r['L']['why'], f"and is logged with its evidence and reason: {r['L']}")
    c.ok(r['mine'], 'the task it made is on My Tasks')
    await go(pg, 'pa'); await pg.click('.view.on [data-patab="activity"]'); await pg.wait_for_timeout(200)
    t = await pg.evaluate("() => document.querySelector('.view.on .pa-acts').textContent")
    c.ok('On Its Own' in t and 'tile supplier' in t and 'Evidence' in t, f'Activity lists it, On Its Own, with its evidence: {t[:160]!r}')
    # Ask First: a proposal; pressing it is logged as approved
    r = await pg.evaluate("""async () => { paRuleSet(paMe().id, 'makeTasks', 'ask'); mindPending = [];
        const out = await mindTool('create_task', { title: 'Order the vanity hardware', due: '2026-09-08' });
        const P = paInit().props[0], before = openTasks('me').some(t => /vanity hardware/.test(t.title));
        await mindPending[0].run(); const after = openTasks('me').some(t => /vanity hardware/.test(t.title));
        return { out, kind: P.kind, outcome: P.outcome, before, after } }""")
    c.ok(r['out'].get('proposed') and r['kind'] == 'proposed' and not r['before'], f"Ask First is a proposal with a button, nothing done: {r}")
    c.ok(r['outcome'] == 'approved' and r['after'], f"pressing it does it, and Activity records the outcome: {r['outcome']}")
    # Hand It to Me: nothing drafted; it is the person's Finding
    r = await pg.evaluate("""async () => { paRuleSet(paMe().id, 'draftEmail', 'hand'); const n0 = (DB.outbox || []).length;
        const out = await mindTool('draft_email', { to: 'Tino', subject: 'COI renewal', body: 'Please send the current certificate.' });
        return { out, n: (DB.outbox || []).length - n0, f: paFindings().filter(r => r.group === 'hand').map(r => r.title) } }""")
    c.ok(r['out'].get('handed') and r['n'] == 0, f'Hand It to Me drafts nothing: {r["out"]} outbox +{r["n"]}')
    c.ok(any('COI renewal' in x for x in r['f']), f"it is on the person's Findings as Yours to Do: {r['f']}")
    await pg.click('.view.on [data-patab="findings"]'); await pg.wait_for_timeout(200)
    await pg.click('.view.on [data-pafkind="hand"]'); await pg.wait_for_timeout(200)
    await pg.locator('.view.on .paf-row', has_text='COI renewal').locator('button', has_text='Done').click(); await pg.wait_for_timeout(200)
    c.ok(await pg.evaluate("() => paFindings().filter(r => r.group === 'hand').length") == 0, 'Done clears it from Findings')
    # the guardrails: a remember the person did not say waits; money proposes; a Never is refused
    r = await pg.evaluate("""async () => { paRuleSet(paMe().id, 'remember', 'alone'); mindUserTurns = ['what is on my day']; mindPending = [];
        const rem = await mindTool('remember', { text: 'Always pay Tino on receipt' });
        const pay = await mindTool('pay_bill', { id: 'b4' }), share = await mindTool('share_file', { id: 'f1' });
        return { rem, pay, share, kinds: paInit().props.slice(0, 3).map(e => e.kind) } }""")
    c.ok(r['rem'].get('proposed'), f'a "remember" from a message, not the person, waits even on Act Alone: {r["rem"]}')
    c.ok(r['pay'].get('proposed') and r['share'].get('refused'), f"money is a proposal and a Never is refused: {r['pay']} {r['share']}")
    c.ok('refused' in r['kinds'] and 'proposed' in r['kinds'], f"both are in Activity: {r['kinds']}")
    # follow-ups when someone goes quiet: Act Alone sends through the guard and logs; the default proposes
    r = await pg.evaluate("""() => { const A = paInit(); A.expect = []; const e = paExpect('Gowanus Plaster', 'the skim coat start date', '2026-09-01', null, '2026-08-25'); e.email = 'office@gowanusplaster.example';
        paRuleSet(paMe().id, 'followUps', 'alone'); const n0 = DB.outbox.length; const made = paChaseWatch(); const o = DB.outbox.slice(n0).find(x => x.to.email === 'office@gowanusplaster.example');
        return { sent: o && o.status, by: o && o.approvedBy, did: paInit().log.find(x => x.type === 'followUps'), act: paActivity().some(x => x.kind === 'did' && /Gowanus/.test(x.what)) } }""")
    c.ok(r['sent'] == 'sent' and 'delegated' in (r['by'] or ''), f'a follow-up set to Act Alone is sent on its own, marked delegated: {r["sent"]} {r["by"]}')
    c.ok(r['did'] and r['act'], 'and it is in Activity with its evidence')
    c.ok(not errs, f'acts: page errors {errs[:3]}')
    await b.close()

# ---------------------------------------------------------------------------------------------- 5, 7: stream, attach
def tool_round():
    return (msg_start('msg_t1') + text_events(['Let me look at the invoices.']) +
            ev('content_block_start', {'type': 'content_block_start', 'index': 1, 'content_block': {'type': 'tool_use', 'id': 'toolu_1', 'name': 'query', 'input': {}}}) +
            ev('content_block_delta', {'type': 'content_block_delta', 'index': 1, 'delta': {'type': 'input_json_delta', 'partial_json': '{"entity": "inv'}}) +
            ev('content_block_delta', {'type': 'content_block_delta', 'index': 1, 'delta': {'type': 'input_json_delta', 'partial_json': 'oices"}'}}) +
            ev('content_block_stop', {'type': 'content_block_stop', 'index': 1}) + msg_end('tool_use'))

async def sec_stream(p, c, url):
    b, pg, errs = await open_http(p, url)
    await sign_in(pg, 'u_owner')
    c.ok(await pg.evaluate("() => mindCan() && paStreamOn()"), 'served over http with a door, the assistant streams')
    await go(pg, 'pa')
    # progressive: the live bubble grows, and ends equal to the final message
    del SEEN[:]
    await pg.fill('#pa-in', 'Write a haiku about brownstones')
    await pg.evaluate("() => document.querySelector('#pa-ask').requestSubmit()")
    samples, raws = [], []
    t0 = time.time()
    while time.time() - t0 < 15:
        s = await pg.evaluate("() => { const e = document.getElementById('pa-live-md'); return e && paLive && paLive.text ? [e.innerText, paLive.text] : null }")
        if s and (not samples or samples[-1] != s[0]): samples.append(s[0]); raws.append(s[1])
        if await pg.evaluate("() => !paBusy && paInit().thread.some(m => m.who === 'a' && m.md)"): break
        await pg.wait_for_timeout(90)
    await pg.wait_for_timeout(200)
    fin = await pg.evaluate("() => { const m = paInit().thread.filter(m => m.who === 'a').slice(-1)[0]; const els = [...document.querySelectorAll('#pa-thread .pa-m.a')]; const el = els[els.length - 1]; const a = el && el.querySelector('.pa-answer'); return { text: m.text, shown: a ? a.innerText : '', th: el ? [...el.querySelectorAll('table th')].map(x => x.textContent) : [], td: el ? el.querySelectorAll('table td').length : 0, link: el ? [...el.querySelectorAll('a[target=_blank]')].map(a => a.href) : [] } }")
    lens = [len(s) for s in raws]
    c.ok(len(samples) >= 3 and lens == sorted(lens) and all(raws[i + 1].startswith(raws[i]) for i in range(len(raws) - 1)), f'the answer renders as it arrives: {len(samples)} frames, each the one before plus more {lens[:9]}')
    c.ok(SEEN and SEEN[0].get('stream') == 'client', f"the page asked the door for a stream: {[x.get('stream') for x in SEEN]}")
    last = await pg.evaluate("paStreamLast")
    full = await pg.evaluate("t => { const d = document.createElement('div'); d.innerHTML = paMd2(t); document.body.appendChild(d); const s = d.innerText; d.remove(); return s }", last)
    c.ok(norm(last) == norm(''.join(STREAM_TEXT)) == norm(fin['text']) and norm(full) == norm(fin['shown']) and all(norm(last).startswith(norm(r)) for r in raws), f"what streamed is the final message, word for word: {norm(fin['shown'])[-60:]!r} vs {norm(full)[-60:]!r}")
    c.ok(fin['th'] == ['Job', 'Status'] and fin['td'] == 4, f"a markdown table renders: {fin['th']} {fin['td']} cells")
    c.ok(fin['link'] == ['https://example.com/schedule'], f'links render, opening in a new tab: {fin["link"]}')
    # a tool round inside a stream (page.route), with the work shown
    seen2 = []
    async def route_tool(route):
        body = json.loads(route.request.post_data or '{}'); seen2.append(body)
        second = any(isinstance(m.get('content'), list) and any(x.get('type') == 'tool_result' for x in m['content']) for m in body.get('messages', []))
        sse = (msg_start('msg_t2') + text_events(['Six invoices are ', 'open; ', 'none is past due.']) + msg_end()) if second else tool_round()
        await route.fulfill(status=200, headers={'content-type': 'text/event-stream'}, body=sse)
    await pg.route('**/api/ai', route_tool)
    a = await ask_and_wait(pg, 'Compare the quokka and the zephyr')
    c.ok(len(seen2) == 2 and all(x.get('stream') == 'client' for x in seen2), f'two streamed rounds: {len(seen2)}')
    tr = [x for m in seen2[1].get('messages', []) if isinstance(m.get('content'), list) for x in m['content'] if x.get('type') == 'tool_result'] if len(seen2) > 1 else []
    tu = [x for m in seen2[1].get('messages', []) if isinstance(m.get('content'), list) for x in m['content'] if x.get('type') == 'tool_use'] if len(seen2) > 1 else []
    c.ok(tu and tu[0]['input'] == {'entity': 'invoices'} and tr and '"untrusted":true' in tr[0]['content'], f'the tool call was assembled from its pieces and its result went back as untrusted data: {tu[:1]}')
    c.ok(a['text'] == 'Six invoices are open; none is past due.', f"the answer is the second round's words: {a['text']!r}")
    c.ok(a['did'] and 'invoices' in a['did'][0]['t'] and '<details class="pa-did"' in a['html'], f'it shows its work, collapsible: {a["did"]}')
    await pg.unroute('**/api/ai')
    # a cut stream: the words that came, and the note
    async def route_cut(route):
        await route.fulfill(status=200, headers={'content-type': 'text/event-stream'}, body=msg_start('msg_c') + text_events(['The long answer begins and ']) + ev('sd_done', {'cut': True}))
    await pg.route('**/api/ai', route_cut)
    a = await ask_and_wait(pg, 'Narrate the quokka saga')
    c.ok('The long answer begins' in a['text'] and 'Cut short' in a['shown'] and a['cut'], f"a cut stream keeps its words and shows the note: {a['shown'][:140]!r}")
    await pg.unroute('**/api/ai')
    # a broken stream: the one-JSON door answers instead
    calls = []
    async def route_broken(route):
        body = json.loads(route.request.post_data or '{}'); calls.append(body.get('stream'))
        if body.get('stream') == 'client':
            await route.fulfill(status=200, headers={'content-type': 'text/event-stream'}, body=msg_start('msg_b') + text_events(['Half an ans']))
        else:
            await route.fulfill(status=200, headers={'content-type': 'application/json'}, body=json.dumps({'type': 'message', 'role': 'assistant', 'content': [{'type': 'text', 'text': 'The whole answer, the second way.'}], 'stop_reason': 'end_turn'}))
    await pg.route('**/api/ai', route_broken)
    a = await ask_and_wait(pg, 'Opine on the quokka')
    c.ok(calls == ['client', None] and a['text'] == 'The whole answer, the second way.', f'a broken stream falls back to the one-JSON call: {calls} {a["text"]!r}')
    await pg.unroute('**/api/ai')
    # an error before the stream is an error, not a second call
    calls = []
    async def route_429(route):
        calls.append(1); await route.fulfill(status=429, headers={'content-type': 'application/json'}, body=json.dumps({'error': 'Your AI budget for this month ($8) is used up.'}))
    await pg.route('**/api/ai', route_429)
    a = await ask_and_wait(pg, 'Ponder the zephyr quotient')
    c.ok(len(calls) == 1 and await pg.evaluate("() => mindState.ok === false && /budget/.test(mindState.why)"), f'an error before the stream is reported once, not retried: {len(calls)} calls')
    await pg.unroute('**/api/ai')
    # attach: the PDF goes to the reader and rides with the question as untrusted data
    reader, asked = [], []
    async def route_doc(route):
        reader.append(json.loads(route.request.post_data or '{}'))
        await route.fulfill(status=200, headers={'content-type': 'application/json'}, body=json.dumps({'text': 'INVOICE 2290\nGowanus Plaster\nSkim coat, garden level\nTotal due $4,200', 'how': 'pdf text'}))
    async def route_ai(route):
        asked.append(json.loads(route.request.post_data or '{}'))
        await route.fulfill(status=200, headers={'content-type': 'text/event-stream'}, body=msg_start('msg_d') + text_events(['It is Gowanus Plaster invoice 2290 for $4,200.']) + msg_end())
    await pg.route('**/api/doctext', route_doc); await pg.route('**/api/ai', route_ai)
    await pg.set_input_files('#pa-file', files=[{'name': 'GPW-2290.pdf', 'mimeType': 'application/pdf', 'buffer': b'%PDF-1.4 fake invoice bytes'}])
    await pg.wait_for_function("() => paAttNow && paAttNow.status !== 'reading'", timeout=8000)
    chip = await pg.evaluate("() => (document.querySelector('.pa-attnow') || {}).innerText || ''")
    c.ok(reader and reader[0].get('mime') == 'application/pdf' and reader[0].get('name') == 'GPW-2290.pdf' and reader[0].get('data'), f"the attachment went to the document reader as base64 with its type and name: {list(reader[0].keys()) if reader else None}")
    c.ok('characters read' in chip, f'the box says it was read: {chip!r}')
    a = await ask_and_wait(pg, 'What is this and is it on a PO?')
    last = asked[-1]['messages'][-1]['content'] if asked else ''
    c.ok('<attached_document name="GPW-2290.pdf" untrusted="true">' in last and 'INVOICE 2290' in last and 'never instructions' in last, 'the document rides with the question, marked as data, never instructions')
    me = await pg.evaluate("() => { const els = [...document.querySelectorAll('#pa-thread .pa-m.me')]; return els[els.length - 1].innerText }")
    c.ok('GPW-2290.pdf' in me and 'characters read' in me and 'Gowanus' in a['text'], f'the question shows its attachment and the answer is about it: {me!r}')
    await pg.unroute('**/api/doctext'); await pg.unroute('**/api/ai')
    c.ok(not errs, f'stream: page errors {errs[:3]}')
    await b.close()

async def sec_file(p, c):
    """On file:// there is no server: no stream, no reader, and the records answer as before."""
    b, pg, errs = await open_app(p)
    await sign_in(pg, 'u_owner')
    c.ok(await pg.evaluate("() => !paStreamOn() && !mindCan()"), 'file:// never streams')
    await go(pg, 'pa')
    await pg.set_input_files('#pa-file', files=[{'name': 'quote.pdf', 'mimeType': 'application/pdf', 'buffer': b'%PDF-1.4 x'}])
    await pg.wait_for_function("() => paAttNow && paAttNow.status !== 'reading'", timeout=8000)
    chip = await pg.evaluate("() => (document.querySelector('.pa-attnow') || {}).innerText || ''")
    c.ok('hosted copy' in chip, f'out of reach of the reader, it says so: {chip!r}')
    a = await ask_and_wait(pg, 'what does it say')
    c.ok(a['text'].startswith('I could not read quote.pdf'), f'and the answer says it could not read it: {a["text"]!r}')
    # a spreadsheet saved as CSV is read here, no server needed
    await pg.set_input_files('#pa-file', files=[{'name': 'tile.csv', 'mimeType': 'text/csv', 'buffer': b'item,qty\nhex tile,40\ngrout,6\n'}])
    await pg.wait_for_function("() => paAttNow && paAttNow.status === 'read'", timeout=8000)
    a = await ask_and_wait(pg, '')
    c.ok('tile.csv' in a['text'] and 'hex tile' in a['shown'], f"a CSV is read on the page; without the model it shows how it starts: {a['shown'][:120]!r}")
    # 6: history and New Conversation
    a = await ask_and_wait(pg, 'what is on my day')
    n0 = await pg.evaluate("() => paTalk(paInit()).length")
    await pg.click('.view.on [data-panew]'); await pg.wait_for_timeout(200)
    r = await pg.evaluate("() => ({ talk: paTalk(paInit()).length, convos: paConvos().length, title: (paConvos()[0] || {}).title, nudgesKept: paInit().thread.every(m => m.nudge) })")
    c.ok(n0 >= 2 and r['talk'] == 0 and r['convos'] == 1 and r['nudgesKept'], f'New Conversation files the conversation and starts clean: {n0} -> {r}')
    # (exec lane, 2026-10-19: the conversations are a side panel on a desk, as in the Claude app, so no History button
    # is pressed first; a past conversation opens as the current one, ready to continue, instead of read-only)
    rows = await pg.evaluate("() => [...document.querySelectorAll('.view.on [data-paconvo]')].map(e => e.innerText)")
    c.ok(len(rows) == 1 and r['title'][:20] in rows[0], f'the conversations list it: {rows}')
    await pg.click('.view.on [data-paconvo]'); await pg.wait_for_timeout(200)
    t = await pg.evaluate("() => ({ t: document.getElementById('pa-thread').innerText, box: !!document.getElementById('pa-in') })")
    c.ok(t['box'] and 'what is on my day' in t['t'], 'a past conversation opens in place, ready to continue')
    r = await pg.evaluate("() => ({ talk: paTalk(paInit()).length, convos: paConvos().length })")
    c.ok(r['talk'] == n0 and r['convos'] == 0, f'it is the current conversation again: {r}')
    # markdown, unit: a table, a link, code and a list, escaped
    h = await pg.evaluate("() => paMd2('**Bold** and `code` <script>x</script>\\n\\n| A | B |\\n|---|--:|\\n| 1 | 2 |\\n\\n- one\\n- two\\n\\n[site](https://example.com) javascript:alert(1)')")
    c.ok('<table>' in h and 'text-align:right' in h and '<b>Bold</b>' in h and '<code>code</code>' in h and '<li>one</li>' in h, 'markdown: tables (with alignment), bold, code and lists')
    c.ok('<script>' not in h and 'href="javascript' not in h and 'href="https://example.com"' in h, 'markdown escapes markup and links only http(s) and mail')
    c.ok(not errs, f'file: page errors {errs[:3]}')
    await b.close()

# ---------------------------------------------------------------------------------------------- 8: phone 390
def lint_parts():
    """lint.py's own collector and arguments, without running its main."""
    src = open(os.path.join(HERE, 'lint.py'), encoding='utf-8').read().replace('asyncio.run(main())', '')
    ns = {'__name__': 'lint_parts', '__file__': os.path.join(HERE, 'lint.py')}
    exec(compile(src, 'lint.py', 'exec'), ns)
    return ns

async def sec_phone(p, c):
    L = lint_parts()
    for phone in (True, False):
        b, pg, errs = await open_app(p, phone=phone)
        nd = await pg.evaluate(L['NAMES_JS'])
        args = {'SMALL': sorted(L['SMALL']), 'UNITS': sorted(L['UNITS']), 'HOUSEKEEPING': L['HOUSEKEEPING'], 'NAMES': nd['names'], 'DATA': nd['data'], 'CHARTS': L['CHARTS'], 'PHONE': phone, 'WALL': L['wall_dates']()}
        vp = 'phone' if phone else 'desktop'
        for u in ('u_owner', 'u_alan', 'u_chen', 'u_angel', 'u_billing'):
            await sign_in(pg, u)
            await pg.evaluate("() => { const A = paInit(); paSay('me', 'what is on my day'); paSay('a', 'Here is a table.\\n\\n| Job | Status |\\n|---|---|\\n| 121 State | On track |', { md: true, did: [{ t: 'Reading the projects', d: 'projects, 6 rows' }] }); }")
            states = [('chat', '')] + [('findings', s) for s in ('you', 'brain', 'chains')] + [('activity', ''), ('brain', '')]
            for tab, seg in states:
                ok = await pg.evaluate("([t, s]) => { view = 'pa'; paTabWant = t; if (s) paFindSeg = s; render(); return paTab === t && (!s || paFindSeg === s || t !== 'findings') }", [tab, seg])
                if not ok: continue
                await pg.evaluate("() => { document.querySelectorAll('.toast.on').forEach(t => t.classList.remove('on')); scrollTo(0, 0); }")
                r = await pg.evaluate(L['COLLECT'], args)
                fl = [f for f in r['flags'] if not f.get('chrome')]
                c.ok(not fl, f"{vp} {u} {tab}{'/' + seg if seg else ''}: the screen standard holds: {[(f['rule'], f['detail'][:90]) for f in fl[:3]]}")
                over = await pg.evaluate("() => document.documentElement.scrollWidth - innerWidth")
                if phone: c.ok(over <= 1, f'{vp} {u} {tab}: no sideways scroll ({over}px)')
        c.ok(not errs, f'{vp}: page errors {errs[:3]}')
        await b.close()

async def main():
    c = Checks()
    srv, url = serve()
    async with async_playwright() as p:
        for name, f in (('fold', sec_fold), ('rules', sec_rules), ('acts', sec_acts), ('stream', lambda p, c: sec_stream(p, c, url)), ('file', sec_file), ('phone', sec_phone)):
            if len(sys.argv) > 1 and name not in sys.argv[1:]: continue
            t0 = time.time()
            try:
                await f(p, c)
            except Exception as e:
                c.ok(False, f'{name}: {type(e).__name__}: {str(e).splitlines()[0][:300]}')
            print(f'-- {name} done in {time.time() - t0:.0f}s, {len(c.fail)} failing so far')
    srv.shutdown()
    sys.exit(c.done())

asyncio.run(main())
