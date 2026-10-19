"""The assistant leads, and its conversation looks like the Claude app (lane "exec", 2026-10-19). Alan: "It's a personal
assistant not just a bot that responds to your questions. It needs to think and act like a Fortune 500 executive
assistant, an assistant project manager." And: "the ai assistant chat needs to feel like our chat on here and or Dot by
chatgpt" (here: the Claude app).

  1. brief     Ask opens on the briefing, the first message of the day, for the owner, the PM, the coordinator and
               billing: prose, not a dashboard (no cards, no section headers): one headline sentence, then the three
               things that matter, each a sentence with its record linked in place, no "·" and no sentence starting in
               lower case or with a record number; at most three small buttons under it, the last "Show the Other N";
               a record link opens the record; "Show the Other N" answers in the conversation with each thing as a
               sentence, its link and its one verb. The PM's Friday update opens as a draft in the conversation (no
               sheet). A new chat opens like Claude's: a greeting, the box centred under it on a desk, at most four
               suggestions; Brief Me says the briefing again. One blue button on the screen (Send).
  2. runs      a fake server run through gsIngestServer({asst}): the briefing is filed and its headline used, its
               drafts wait in the outbox for approval (deduped by key across runs), another person's run is never
               filed, nothing is sent, not even a type set to Act Alone.
  3. approve   a draft approved from the briefing is sent by the person (bnSend), with a toast naming who it went to
               and a short reply in the conversation; Not Now puts a thing off to the next working day, with a reply
               that carries Undo, and Undo brings it back.
  4. follow    "I'll get back to Chen Friday" with Tasks for Me on Act Alone is a task under I'm Chasing; the reply
               carries Undo and the briefing says it did it, with Undo; Undo removes the task. On Ask First (the PM's
               default) it is a one-tap offer whose reply carries Undo. "Chen will send the window lead time Friday"
               goes on the wait ledger. "Walk me through the first one" and "and the one after that?" keep the context.
  5. memory    a correction is a standing instruction, fed into the prompt, listed under Activity > How You Work,
               edited and deleted there, and added from there; three Not Nows on one kind propose a memory the person
               keeps; another person never sees it.
  6. voice     the microphone shows only where the browser has speech recognition; what it hears lands in the box.
  7. compose   the box: a growing text area; Enter sends, Shift+Enter is a new line; the person's message is a right-hand
               bubble and the answer is not a bubble; Copy and Retry under the last answer, Edit on the last question;
               Retry and Edit ask again without a second copy; an offer that writes a draft shows it under the answer
               with Approve and Edit, and Approve sends it with a toast.
  8. convos    New Chat files the conversation in the side panel, titled by its first question, newest first;
               search filters it; pressing one continues it; a new day files yesterday's conversation and opens on the
               briefing; on the phone the panel is a drawer.
  9. stream    served over http with a door that streams: while words arrive the round Send is a Stop and no blue
               button shows; Escape stops it: what came stays, marked Stopped, nothing arrives after, and the next
               question is answered; an answer whose tool wrote a draft carries it with Approve and Edit.
 10. phone     390 px and desk: the screen standard (lint.py's own collector) on the briefing open and folded and on a
               conversation; no sideways scroll; on the phone the box sits on the tab bar, 16px text. Screenshots in
               review/exec_assistant/.
"""
import asyncio, json, os, re, sys, threading, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from harness import *

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(ROOT, 'review', 'exec_assistant')
ROLES = ('u_owner', 'u_alan', 'u_chen', 'u_billing')
DIST = os.environ.get('SD_DIST') or os.path.join(ROOT, 'dist', 'smartdesigns_projects.html')

async def open_pa(pg, u):
    await sign_in(pg, u)
    await go(pg, 'pa')
    await pg.wait_for_timeout(150)

async def ask(pg, q, timeout=15000):
    n = await pg.evaluate("() => paInit().thread.filter(m => m.who === 'a').length")
    await pg.fill('#pa-in', q)
    await pg.evaluate("() => document.querySelector('#pa-ask').requestSubmit()")
    await pg.wait_for_function("n => !paBusy && paInit().thread.filter(m => m.who === 'a').length > n", arg=n, timeout=timeout)
    await pg.wait_for_timeout(150)
    return await pg.evaluate("() => paInit().thread.filter(m => m.who === 'a').slice(-1)[0].text")

async def toast_text(pg):
    return await pg.evaluate("() => (document.getElementById('toast') || {}).textContent || ''")

VIS = "const vis = el => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity !== 0; };"
BRIEF_STATE = """() => {
  """ + VIS + """
  const b = document.querySelector('#v-pa #pa-thread .pa-brief'), prose = b ? b.querySelector('[data-pabfhead]').innerText : '';
  return {
    brief: !!b, first: !!b && b === document.querySelector('#pa-thread .pa-m'), prose,
    cards: document.querySelectorAll('#v-pa .pa-bf-card, #v-pa .pa-bf-hd').length,
    links: b ? [...b.querySelectorAll('a.pa-rec[data-pabfgo]')].map(a => a.textContent) : [],
    acts: b ? [...b.querySelectorAll('.pa-bf-acts button')].map(x => x.textContent.trim()) : [],
    chips: [...document.querySelectorAll('#v-pa .pa-chips [data-pachip]')].map(x => x.textContent.trim()),
    lead: [...document.querySelectorAll('#v-pa .ph .lead')].filter(vis).length,
    primary: [...document.querySelectorAll('.btn.primary')].filter(vis).map(x => x.textContent.trim()),
    model: (() => { const B = paBriefModel(true); return { head: B.headline, needs: B.needs.length, did: B.did.length, chasing: B.chasing.length, today: B.today.length, needKeys: B.needs.map(x => x.key), chaseKeys: B.chasing.map(x => x.key), chaseKinds: B.chasing.map(x => x.k), first: B.needs[0] ? paPhrase(B.needs[0]).subj : '' }; })(),
  };
}"""
# run a thing's verb from the conversation: its button under the briefing, or in the rest's list
DO_VERB = """async k => { let b = document.querySelector(`#v-pa [data-pabfdo="${k}"]`);
  if (!b) { const r = document.querySelector('#v-pa [data-pabfrest]'); r && r.click(); await new Promise(z => setTimeout(z, 150)); b = document.querySelector(`#v-pa [data-pabfdo="${k}"]`); }
  if (!b) return null; const l = b.textContent.trim(); b.click(); return l }"""

# ---------------------------------------------------------------------------------------------- 1: the briefing
async def sec_brief(p, c):
    b, pg, errs = await open_app(p)
    for u in ROLES:
        await open_pa(pg, u)
        s = await pg.evaluate(BRIEF_STATE)
        c.ok(s['brief'] and s['first'], f'{u}: Ask opens on the briefing, the first message of the conversation')
        c.ok(s['cards'] == 0, f'{u}: a message, not a dashboard: no cards or section headers ({s["cards"]})')
        head = s['model']['head']
        c.ok(s['prose'].startswith(head) and head[0].isupper() and head.endswith('.') and head.count('. ') == 0, f"{u}: one headline sentence first: {head!r}")
        c.ok('·' not in s['prose'], f'{u}: no "·" in the prose: {s["prose"][:200]!r}')
        low = re.findall(r'(?:^|[.!?]\s+)([a-z]\w*)', s['prose'])
        c.ok(not low, f'{u}: no sentence starts in lower case: {low[:3]}')
        recfirst = re.findall(r'(?:^|[.!?]\s+)([A-Z]{2,}-\d[\w-]*)', s['prose'])
        c.ok(not recfirst, f'{u}: no sentence starts with a record number: {recfirst}')
        if s['model']['needs']:
            c.ok(s['model']['first'] and s['model']['first'] in s['prose'] and len(s['links']) >= 1, f"{u}: the first thing is named in words, its record linked: {s['model']['first']!r} links {s['links'][:3]}")
        c.ok(1 <= len(s['acts']) <= 3 if s['model']['needs'] else len(s['acts']) <= 3, f"{u}: at most three small buttons under it: {s['acts']}")
        if s['model']['needs'] > 3:
            c.ok(s['acts'][-1] == f"Show the Other {s['model']['needs'] - 3}", f"{u}: the last button shows the rest: {s['acts']}")
        c.ok(s['lead'] == 0, f'{u}: no explanatory paragraph over the conversation')
        c.ok(s['primary'] == ['Send'], f"{u}: one blue button, the safe next step: {s['primary']}")
        pm = u in ('u_owner', 'u_alan')
        kinds = set(s['model']['chaseKinds'])
        if pm:
            c.ok(any(k.startswith('late:') for k in s['model']['needKeys']) and any(k.startswith('fri:') for k in s['model']['needKeys']), f"{u}: the jobs' late schedule work and the Friday update are among what needs them: {s['model']['needKeys'][:8]}")
            c.ok(kinds & {'RFI', 'Submittal', 'Client Decision', 'Delivery'}, f"{u}: it follows what the jobs wait on: {sorted(kinds)}")
        else:
            c.ok(not any(k.startswith('fri:') or k.startswith('late:') for k in s['model']['needKeys']), f'{u}: no project-manager items for this role')
    # the rest answers in the conversation, each thing a sentence with its link and one verb
    await open_pa(pg, 'u_owner')
    n = await pg.evaluate("() => paBriefModel(true).needs.length")
    await pg.click('#v-pa [data-pabfrest]')
    await pg.wait_for_timeout(200)
    st = await pg.evaluate("""() => { const ms = [...document.querySelectorAll('#pa-thread .pa-m')]; const me = ms[ms.length - 2], a = ms[ms.length - 1];
        return { me: me && me.classList.contains('me') ? me.innerText.trim() : '', rows: a ? a.querySelectorAll('.pa-bf-li').length : 0,
          linked: a ? [...a.querySelectorAll('.pa-bf-li')].filter(r => r.querySelector('a.pa-rec')).length : 0, dots: a ? /·/.test(a.querySelector('.pa-bf-ul').innerText) : true,
          verbs: a ? [...a.querySelectorAll('.pa-bf-li')].every(r => r.querySelectorAll('.btn').length <= 1) : false } }""")
    c.ok(st['me'].startswith('Show me the other') and st['rows'] == n - 3 and st['linked'] >= st['rows'] - 2 and not st['dots'] and st['verbs'], f'"Show the Other" answers in the conversation, one sentence and one verb each: {st} of {n}')
    # a record link opens the record
    v0 = await pg.evaluate("() => { const a = document.querySelector('#v-pa .pa-brief a.pa-rec[data-pabfgo]'); a.click(); return view }")
    await pg.wait_for_timeout(200)
    c.ok(await pg.evaluate("view") != 'pa' or await pg.evaluate("() => !!document.getElementById('mbm') || !!document.querySelector('.sheet.on, .drawer.on')"), f'a record link in the briefing opens the record ({await pg.evaluate("view")})')
    # the Friday update: drafted in the conversation, not a sheet over it
    await open_pa(pg, 'u_alan')
    key = await pg.evaluate("() => paBriefModel(true).needs.find(x => x.key.startsWith('fri:') && /Review and Send/.test(paVerbLabel(x))).key")
    label = await pg.evaluate(DO_VERB, key)
    await pg.wait_for_timeout(250)
    m = await pg.evaluate("() => { const d = [...document.querySelectorAll('#pa-thread .pc-draft')].pop(); return { modal: !!document.getElementById('mbm'), body: d ? (d.querySelector('.pc-draft-body') || {}).innerText || '' : '', btns: d ? [...d.querySelectorAll('button')].map(x => x.textContent.trim()) : [] } }")
    c.ok(label == 'Review and Send' and not m['modal'] and 'this week' in m['body'] and not re.search(r'\$\d', m['body']) and m['btns'] == ['Approve and Send', 'Edit'], f'the Friday update is a draft in the conversation, to read, change and approve: {label} {m}')
    held = await pg.evaluate("() => (DB.outbox || []).filter(o => /^asst\\|friday\\|/.test(o.aboutKey) && o.status === 'draft').length")
    c.ok(held == 1, f'it waits in the outbox as one draft until sent ({held})')
    # a new chat opens like Claude's; Brief Me says the briefing again
    await pg.click('.view.on [data-panew]'); await pg.wait_for_timeout(200)
    await pg.click('.view.on [data-panew]'); await pg.wait_for_timeout(200)
    st = await pg.evaluate("() => { const h = document.querySelector('#v-pa .pc-hello'), d = document.getElementById('pc-dock').getBoundingClientRect(); return { hello: h ? h.innerText : '', top: Math.round(d.top), h: innerHeight, chips: [...document.querySelectorAll('#v-pa .pc-sugg [data-pachip]')].map(b => b.textContent.trim()), msgs: document.querySelectorAll('#pa-thread .pa-m').length } }")
    c.ok(re.match(r'Good (morning|afternoon|evening), \w+', st['hello']) and st['msgs'] == 0, f'a new chat opens on a greeting: {st}')
    c.ok(st['h'] * 0.2 < st['top'] < st['h'] * 0.75, f'on a desk the box sits centred under it: {st["top"]} of {st["h"]}')
    c.ok(0 < len(st['chips']) <= 4 and 'Brief Me' in st['chips'], f'at most four suggestions, Brief Me among them: {st["chips"]}')
    await pg.evaluate("() => [...document.querySelectorAll('#v-pa .pc-sugg [data-pachip]')].find(b => b.textContent.trim() === 'Brief Me').click()")
    await pg.wait_for_timeout(250)
    c.ok(await pg.evaluate("() => !!document.querySelector('#pa-thread .pa-brief') && !document.querySelector('#v-pa .pc-hello')"), 'Brief Me says the briefing again, and the box moves to the bottom')
    c.ok(not errs, f'brief: page errors {errs[:3]}')
    await b.close()

# ---------------------------------------------------------------------------------------------- 2: server runs
def run(person, key, drafts, headline='Two things need you before 10; the tile delivery slipped to Thursday and I have told the PM.'):
    return {'key': f'asst:{person}:{key}', 'at': f'2026-09-03T{key}', 'person': person,
            'brief': {'headline': headline, 'today': [{'title': 'Site walk at 121 State, 2:00', 'why': 'on your calendar', 'value': '', 'due': '2026-09-03', 'refs': [{'kind': 'job', 'id': 'p1'}]}],
                      'needs': [{'title': 'Tile delivery slipped to Thursday', 'why': 'Nemo Tile wrote at 6:40', 'value': 'Think ahead', 'due': '2026-09-03', 'refs': [{'kind': 'mail', 'id': 'nomail'}]}],
                      'chasing': [{'title': 'Carlos Millwork owes the shop drawings', 'why': 'promised for Tuesday', 'value': 'Own it', 'due': '2026-09-01', 'refs': []}]},
            'drafts': drafts, 'notes': ['Read 14 messages and 3 calendar changes.']}

# (subjects name no PO: a draft about a PO that already has an item on Approvals is folded into that item)
def draft(k, typ, to, email, subj):
    return {'key': f'ad:{k}', 'type': typ, 'to': {'name': to, 'email': email}, 'subject': subj, 'body': f'Hi,\n\n{subj}.\n\nThank you', 'because': f'{to} has not confirmed', 'value': 'Own it', 'refs': [{'kind': 'po', 'id': 'po1'}]}

async def sec_runs(p, c):
    b, pg, errs = await open_app(p)
    await open_pa(pg, 'u_owner')
    box = {'asst': [run('u_owner', '07:02:00', [draft('0000000000000001', 'orderFollowups', 'Window Works', 'orders@windowworks.example', 'Confirming the ship date for the windows'),
                                                draft('0000000000000002', 'clientUpdate', 'Sarah Klein', 'sarah@klein.example', '121 State Street this week')]),
                    run('u_alan', '07:03:00', [draft('0000000000000003', 'reply', 'Someone', 'x@y.example', 'Not for the owner')])]}
    n = await pg.evaluate("b => gsIngestServer(b)", box)
    st = await pg.evaluate("""() => ({ briefs: (paInit().briefs || []).length, alan: ((DB.asst.u_alan || {}).briefs || []).length,
        drafts: DB.outbox.filter(o => /^asst\\|ad:/.test(o.aboutKey)).map(o => ({ k: o.aboutKey, s: o.status, appr: o.approval, for: o.forName, t: o.asstType })),
        sent: DB.outbox.filter(o => /^asst\\|/.test(o.aboutKey) && o.status === 'sent').length,
        head: paBriefModel(true).headline, did: paBriefModel(true).did.map(x => x.title) })""")
    c.ok(n >= 1 and st['briefs'] == 1, f"the owner's run is filed: {n}, {st['briefs']} briefing")
    c.ok(st['alan'] == 0 and not any('Not for the owner' in str(d) for d in st['drafts']) and len(st['drafts']) == 2, f"another person's run is never filed here: alan {st['alan']}, drafts {st['drafts']}")
    c.ok(all(d['s'] == 'draft' and d['appr'] for d in st['drafts']) and st['sent'] == 0, f"nothing from a run is sent; each draft waits for approval: {st['drafts']}")
    c.ok(st['head'].startswith('Two things need you before 10'), f"the server's written headline is used: {st['head'][:80]}")
    c.ok(any(t.startswith('Read your day between your visits and drafted two notes') for t in st['did']), f"I Did says what it did between visits: {st['did'][:3]}")
    await go(pg, 'pa')
    s = await pg.evaluate(BRIEF_STATE)
    drows = [k for k in s['model']['needKeys'] if k.startswith('q:draft:')]
    c.ok(len(drows) >= 2, f'both drafts are on Needs You: {drows}')
    c.ok(any(k.startswith('srv:') for k in s['model']['needKeys']) and any(k.startswith('srv:') for k in s['model']['chaseKeys']), "what the run found that the records do not show is on Needs You and I'm Chasing")
    appr = await pg.evaluate("() => PRED.waitingOnMe.rows().filter(r => r.kind === 'draft' && /^asst/.test((DB.outbox.find(o => o.id === r.id) || {}).aboutKey || '')).length")
    c.ok(appr == 2, f'the same drafts wait on Approvals (one queue): {appr}')
    act = await pg.evaluate("() => paActivity().filter(e => /Drafted for you/.test(e.what)).map(e => e.type)")
    c.ok('orderFollowups' in act, f'Activity shows the drafts with their type: {act}')
    # the same run again, and a later run carrying the same draft: no duplicates
    n2 = await pg.evaluate("b => gsIngestServer(b)", box)
    later = {'asst': [run('u_owner', '11:02:00', [draft('0000000000000001', 'orderFollowups', 'Window Works', 'orders@windowworks.example', 'Confirming the ship date for the windows')], headline='Later run.')]}
    await pg.evaluate("b => gsIngestServer(b)", later)
    dup = await pg.evaluate("() => ({ d: DB.outbox.filter(o => o.aboutKey === 'asst|ad:0000000000000001').length, briefs: paInit().briefs.length, head: paBriefModel(true).headline })")
    c.ok(n2 == 0 and dup['d'] == 1 and dup['briefs'] == 2 and dup['head'] == 'Later run.', f'deduped by key across runs; the newest briefing wins: {n2}, {dup}')
    # Act Alone does not reach a run: whatever the person's rule, nothing a run wrote is sent; it waits for them
    await pg.evaluate("() => { paRuleSet('u_owner', 'orderFollowups', 'alone'); paRuleSet('u_owner', 'clientMessages', 'alone'); }")
    box3 = {'asst': [run('u_owner', '15:02:00', [draft('0000000000000004', 'orderFollowups', 'Window Works', 'orders@windowworks.example', 'Tracking for the windows'),
                                                 draft('0000000000000005', 'clientUpdate', 'Sarah Klein', 'sarah@klein.example', 'Friday note'),
                                                 draft('0000000000000006', 'orderFollowups', 'Sarah Klein', 'sarah@klein.example', 'To a client address')])]}
    await pg.evaluate("b => gsIngestServer(b)", box3)
    st3 = await pg.evaluate("""() => { const f = k => DB.outbox.find(o => o.aboutKey === 'asst|ad:' + k) || {};
        return { s: ['0000000000000004', '0000000000000005', '0000000000000006'].map(k => f(k).status), note: f('0000000000000004').ruleNote || '',
          sent: DB.outbox.filter(o => /^asst\\|/.test(o.aboutKey) && o.status === 'sent').length, did: (paInit().log || []).some(e => /Sent on its own/.test(e.what)),
          need: (() => { const x = paBriefModel(true).needs.find(n => n.id === f('0000000000000004').id); return x ? x.sub : '' })() } }""")
    c.ok(st3['s'] == ['draft', 'draft', 'draft'] and st3['sent'] == 0 and not st3['did'], f'nothing a server run wrote is sent, even a type set to Act Alone: {st3}')
    c.ok('always waits for you' in st3['note'] and 'always waits for you' in st3['need'], f"the draft, and its row on Needs You, say why it waits although the rule is Act Alone: {st3['need']!r}")
    c.ok(not errs, f'runs: page errors {errs[:3]}')
    await b.close()

# ---------------------------------------------------------------------------------------------- 3: approve from Needs You
async def sec_approve(p, c):
    b, pg, errs = await open_app(p)
    await open_pa(pg, 'u_owner')
    await pg.evaluate("b => gsIngestServer(b)", {'asst': [run('u_owner', '08:00:00', [draft('00000000000000a1', 'orderFollowups', 'Window Works', 'orders@windowworks.example', 'Confirming the ship date for the windows')])]})
    await go(pg, 'home'); await go(pg, 'pa')
    oid = await pg.evaluate("() => DB.outbox.find(o => o.aboutKey === 'asst|ad:00000000000000a1').id")
    label = await pg.evaluate(DO_VERB, f'q:draft:{oid}')
    c.ok(label and label.startswith('Approve'), f'the draft leads with Approve: {label}')
    await pg.wait_for_function("id => (DB.outbox.find(o => o.id === id) || {}).status === 'sent'", arg=oid, timeout=8000)
    await pg.wait_for_timeout(200)
    t = await toast_text(pg)
    o = await pg.evaluate("id => { const o = DB.outbox.find(x => x.id === id); return { by: o.approvedBy } }", oid)
    reply = await pg.evaluate("() => { const m = paInit().thread.slice(-1)[0]; return m.confirm ? m.text : '' }")
    c.ok('Sent to Window Works' in t and 'Open' in t, f'a toast says who it went to, with Open: {t!r}')
    c.ok(reply.startswith('Sent to Window Works'), f'and a short reply in the conversation says so: {reply!r}')
    c.ok(o['by'] == 'Owner', f'the person approved and sent it: {o}')
    gone = await pg.evaluate("id => !paBriefModel(true).needs.some(x => x.key === 'q:draft:' + id)", oid)
    c.ok(gone, 'once sent it is off the briefing')
    # Not Now: off the briefing until the next working day, with a reply that carries Undo
    k2 = await pg.evaluate("() => paBriefModel(true).needs.slice(-1)[0].key")
    await pg.evaluate("async () => { const r = document.querySelector('#v-pa [data-pabfrest]'); r && r.click(); }")
    await pg.wait_for_timeout(150)
    await pg.evaluate("k => document.querySelector(`#v-pa [data-pabfsnooze=\"${k}\"]`).click()", k2)
    await pg.wait_for_timeout(200)
    st = await pg.evaluate("k => ({ off: !paBriefModel(true).needs.some(x => x.key === k), until: paInit().snooze[k], t: document.getElementById('toast').textContent, reply: paInit().thread.slice(-1)[0].text, undo: !!document.querySelector('#pa-thread .pc-confirm:last-of-type [data-pcact^=\"undo\"], #pa-thread .pa-m:last-child [data-pcact^=\"undo\"]') })", k2)
    c.ok(st['off'] and st['until'] == '2026-09-04' and 'Not now' in st['t'] and st['reply'].startswith('Put off until') and st['undo'], f'Not Now puts it off to the next working day, with a reply that carries Undo: {st}')
    await pg.evaluate("() => document.querySelector('#pa-thread .pa-m:last-child [data-pcact^=\"undo\"]').click()")
    await pg.wait_for_timeout(200)
    c.ok(await pg.evaluate("k => paBriefModel(true).needs.some(x => x.key === k)", k2), 'Undo brings it back')
    c.ok(not errs, f'approve: page errors {errs[:3]}')
    await b.close()

# ---------------------------------------------------------------------------------------------- 4: follow-through
async def sec_follow(p, c):
    b, pg, errs = await open_app(p)
    await open_pa(pg, 'u_owner')
    await pg.evaluate("() => paRuleSet('u_owner', 'makeTasks', 'alone')")
    a = await ask(pg, "I'll get back to Chen Friday")
    st = await pg.evaluate("""() => { const t = (DB.tasks || []).find(x => x.source && x.source.commit && /get back to chen/i.test(x.title)); const B = paBriefModel(true);
        return { t: t && { id: t.id, due: t.due, title: t.title }, chase: B.chasing.filter(x => x.k === 'You Promised').map(x => x.title), did: B.did.map(x => ({ title: x.title, acts: x.acts.map(a => a.label) })) } }""")
    c.ok(st['t'] and st['t']['due'] == '2026-09-04', f"a promise typed in Chat is a task on the person, due Friday: {a!r} {st['t']}")
    c.ok(any('Get back to Chen' in x for x in st['chase']), f"it is under I'm Chasing: {st['chase']}")
    found = await pg.evaluate("id => tkAll({ open: true, uid: paMe().id }).some(t => t.id === id)", st['t']['id'] if st['t'] else '')
    c.ok(found, 'it is on the one task accessor (tkAll), so Today and All Tasks show it')
    row = next((x for x in st['did'] if x['title'].startswith('Put on your list')), None)
    c.ok(row and 'Undo' in row['acts'], f'I Did shows it, with Undo: {st["did"][:3]}')
    undo = await pg.evaluate("() => { const ms = [...document.querySelectorAll('#pa-thread .pa-m.a')]; return !!ms[ms.length - 1].querySelector('[data-pcact^=\"undo\"]') }")
    c.ok(undo, 'the reply that put it on the list carries Undo')
    # Undo from the briefing's "since you last looked"
    await go(pg, 'home'); await go(pg, 'pa')
    clicked = await pg.evaluate("""() => { const b = document.querySelector('#pa-thread .pa-brief [data-pabfundo]'); b && b.click(); return !!b }""")
    await pg.wait_for_timeout(200)
    st2 = await pg.evaluate("id => ({ gone: !(DB.tasks || []).some(t => t.id === id), t: document.getElementById('toast').textContent, undone: (paInit().log || []).some(e => e.undo && e.undo.id === id && e.undone), reply: paInit().thread.slice(-1)[0].text })", st['t']['id'] if st['t'] else '')
    c.ok(clicked and st2['gone'] and st2['undone'] and st2['t'].startswith('Undone') and st2['reply'].startswith('Undone'), f'the briefing says what it did, and Undo takes it back, with a toast and a reply: {st2}')
    # the PM's default is Ask First: a one-tap offer, then the task
    await open_pa(pg, 'u_alan')
    a = await ask(pg, "I'll call the inspector tomorrow")
    before = await pg.evaluate("() => (DB.tasks || []).filter(t => t.source && t.source.commit && /inspector/i.test(t.title)).length")
    c.ok('Shall I hold you to it' in a and before == 0, f'Ask First: it offers, and makes nothing until the person says so: {a!r}')
    clicked = await pg.evaluate("() => { const b = [...document.querySelectorAll('#pa-thread [data-csdo]')].find(b => /Put It on My List/.test(b.textContent)); b && b.click(); return !!b }")
    await pg.wait_for_timeout(250)
    st3 = await pg.evaluate("() => ({ n: (DB.tasks || []).filter(t => t.source && t.source.commit && /inspector/i.test(t.title)).length, chase: paBriefModel(true).chasing.some(x => x.k === 'You Promised' && /inspector/i.test(x.title)), props: (paInit().props || []).filter(e => e.type === 'makeTasks').map(e => e.outcome), reply: (paInit().thread.slice(-1)[0] || {}).text, undo: !!(paInit().thread.slice(-1)[0] || {}).undoLog })")
    c.ok(clicked and st3['n'] == 1 and st3['chase'] and 'approved' in st3['props'], f'one tap (a small button under the answer) puts it on the list and under I\'m Chasing, logged as approved: {st3}')
    c.ok(str(st3['reply']).startswith('On your list') and st3['undo'], f'and the reply says so, with Undo: {st3["reply"]!r}')
    # what someone else owes goes on the wait ledger
    a = await ask(pg, 'Chen will send the window lead time Friday')
    st4 = await pg.evaluate("() => { const e = paExpectLedger().find(x => /window lead time/i.test(x.about)); return { e: e && { who: e.who, by: e.by }, chase: paBriefModel(true).chasing.filter(x => x.k === 'Owes You').map(x => x.title) } }")
    c.ok(st4['e'] and 'Chen' in st4['e']['who'] and st4['e']['by'] == '2026-09-04', f'a promise someone made goes on the wait ledger: {a!r} {st4["e"]}')
    c.ok(any('window lead time' in x for x in st4['chase']), f"and under I'm Chasing: {st4['chase']}")
    # the briefing's own follow-ups keep the context
    a1 = await ask(pg, 'walk me through the first one')
    a2 = await ask(pg, 'and the one after that?')
    want = await pg.evaluate("() => { const B = paBriefModel(true); return [paPhrase(B.needs[0]).subj, paPhrase(B.needs[1]).subj] }")
    c.ok(a1.startswith('The first is ' + want[0]) and a2.startswith('The second is ' + want[1]), f'"walk me through the first one", then "and the one after that?": {a1[:90]!r} / {a2[:90]!r}')
    # a question is still a question
    a = await ask(pg, 'I need to see the open POs')
    c.ok(not await pg.evaluate("() => (DB.tasks || []).some(t => /see the open pos/i.test(t.title))"), f'"I need to see…" is a question, not a promise: {a[:80]!r}')
    c.ok(not errs, f'follow: page errors {errs[:3]}')
    await b.close()

# ---------------------------------------------------------------------------------------------- 5: memory
async def sec_memory(p, c):
    b, pg, errs = await open_app(p)
    await open_pa(pg, 'u_owner')
    a = await ask(pg, "don't book me before 9")
    st = await pg.evaluate("() => ({ stand: paInit().standing.map(s => s.text), prompt: mindSystem().includes(\"don't book me before 9\") })")
    c.ok("don't book me before 9" in st['stand'], f'a correction is kept as a standing instruction: {a!r} {st}')
    c.ok(st['prompt'], 'and it is fed into every prompt for this person')
    a = await ask(pg, 'the Kleins prefer calls')
    c.ok(await pg.evaluate("() => paInit().standing.some(s => s.text === 'the Kleins prefer calls')"), f'a preference is kept too: {a!r}')
    await pg.evaluate("() => paOpen('activity')")
    await pg.wait_for_timeout(150)
    L = await pg.evaluate("() => [...document.querySelectorAll('#pa-memo .pa-memo-list .pa-memo-row')].map(r => r.textContent)")
    c.ok(any('before 9' in x for x in L) and any('prefer calls' in x for x in L), f'Activity > How You Work lists them: {L}')
    mid = await pg.evaluate("() => paInit().memo.find(m => m.text === \"don't book me before 9\").id")
    await pg.click(f'[data-pamemoedit="{mid}"]')
    await pg.fill('#mbm [data-f=text]', "don't book me before 9:30")
    await pg.click('#mbm-ok')
    await pg.wait_for_timeout(150)
    st = await pg.evaluate("id => ({ m: paInit().memo.find(m => m.id === id).text, s: paInit().standing.find(s => s.id === id).text, t: document.getElementById('toast').textContent })", mid)
    c.ok(st['m'] == st['s'] == "don't book me before 9:30" and st['t'].startswith('Changed'), f'edited in place, memory and standing alike, with a toast: {st}')
    await pg.click(f'[data-pamemodel="{mid}"]')
    await pg.wait_for_timeout(150)
    st = await pg.evaluate("id => ({ gone: !paInit().memo.some(m => m.id === id) && !paInit().standing.some(s => s.id === id), prompt: mindSystem().includes('before 9:30'), t: document.getElementById('toast').textContent })", mid)
    c.ok(st['gone'] and not st['prompt'] and st['t'].startswith('Deleted'), f'deleted, out of the prompt, with a toast: {st}')
    await pg.fill('#pa-memo [data-pamemoin]', 'Copy Sarah on anything about tile')
    await pg.click('#pa-memo .pa-memo-add button')
    await pg.wait_for_timeout(150)
    c.ok(await pg.evaluate("() => paInit().standing.some(s => s.text === 'Copy Sarah on anything about tile')"), 'added from How You Work')
    # a pattern: three Not Nows on one kind propose a memory; keeping it applies it
    await go(pg, 'home'); await go(pg, 'pa')
    kind = await pg.evaluate("""() => { const B = paBriefModel(true); const by = {}; B.needs.forEach(x => { const k = x.it && x.it.kind; (by[k] = by[k] || []).push(x) }); const k = Object.keys(by).find(k => by[k].length >= 3 && k !== 'pa:memory'); by[k].slice(0, 3).forEach(x => paSnooze(x)); return k }""")
    sug = await pg.evaluate("() => paBriefModel(true).needs.filter(x => x.k === 'Suggested Memory').map(x => ({ key: x.key, t: x.title }))")
    c.ok(kind and sug, f'three Not Nows on one kind ({kind}) propose a memory, on Needs You: {sug}')
    if sug:
        await pg.evaluate(DO_VERB, sug[0]['key'])
        await pg.wait_for_timeout(150)
        st = await pg.evaluate("k => ({ rule: paInit().memo.some(m => m.rule && m.rule.hideKind === k), left: paBriefModel(true).needs.filter(x => x.it && x.it.kind === k).every(x => standardUrgency(x.it) === 0), hidden: paBriefModel(true).hidden })", kind)
        c.ok(st['rule'] and st['left'] and st['hidden'] > 0, f'kept, it shapes the briefing (only overdue ones of that kind stay; the rest are counted as left out): {st}')
    # private: another person never sees it
    await open_pa(pg, 'u_billing')
    st = await pg.evaluate("() => ({ mine: paMemoryRows().map(m => m.text), prompt: mindSystem().includes('Kleins prefer calls') })")
    c.ok(not any('Kleins' in x or 'tile' in x for x in st['mine']) and not st['prompt'], f"another person's assistant never holds it: {st}")
    c.ok(not errs, f'memory: page errors {errs[:3]}')
    await b.close()

# ---------------------------------------------------------------------------------------------- 6: voice
async def sec_voice(p, c):
    b, pg, errs = await open_app(p)
    await open_pa(pg, 'u_owner')
    has = await pg.evaluate("() => !!(window.SpeechRecognition || window.webkitSpeechRecognition)")
    mic = await pg.evaluate("() => !!document.querySelector('#v-pa [data-pamic]')")
    c.ok(mic == has, f'the microphone shows exactly where the browser can hear ({has}, shown {mic})')
    await pg.evaluate("""() => { window.SpeechRecognition = class { start() { setTimeout(() => { this.onresult({ results: [[{ transcript: 'what is on my day' }]] }); this.onend(); }, 20); } stop() {} }; renderPa(); }""")
    st = await pg.evaluate("() => { const m = document.querySelector('#v-pa [data-pamic]'); return { left: !!m && !!m.closest('.pc-tools') && m.getBoundingClientRect().left < document.querySelector('#v-pa .pc-send').getBoundingClientRect().left } }")
    c.ok(st['left'], 'the microphone sits in the box, on the left, Send on the right')
    await pg.click('#v-pa [data-pamic]')
    await pg.wait_for_timeout(200)
    st = await pg.evaluate("() => ({ v: document.getElementById('pa-in').value, send: !document.querySelector('#pa-ask [type=submit]').disabled })")
    c.ok(st['v'] == 'what is on my day' and st['send'], f'what it hears lands in the box, ready to send: {st}')
    await pg.evaluate("() => { delete window.SpeechRecognition; delete window.webkitSpeechRecognition; window.webkitSpeechRecognition = undefined; renderPa(); }")
    c.ok(not await pg.evaluate("() => !!document.querySelector('#v-pa [data-pamic]')"), 'with no speech recognition, no microphone')
    await pg.evaluate("() => paOpen('activity')")
    speak = await pg.evaluate("() => !!document.querySelector('[data-paspeak]') === ('speechSynthesis' in window)")
    c.ok(speak, 'Read my answers aloud is a setting where the browser can speak')
    c.ok(not errs, f'voice: page errors {errs[:3]}')
    await b.close()

# ---------------------------------------------------------------------------------------------- 7: the box and the messages
LAST = """() => { const as = [...document.querySelectorAll('#pa-thread .pa-m.a:not(.pa-brief):not(.pc-confirm)')], ms = [...document.querySelectorAll('#pa-thread .pa-m.me')];
  const a = as[as.length - 1], m = ms[ms.length - 1];
  return { nA: as.length, nMe: ms.length, aActs: a ? [...a.querySelectorAll(':scope > .pc-acts [data-pcact]')].map(b => b.getAttribute('aria-label')) : [], meActs: m ? [...m.querySelectorAll('[data-pcact]')].map(b => b.getAttribute('aria-label')) : [],
    meBg: m ? getComputedStyle(m.querySelector('.pa-b')).backgroundColor : '', meRight: m ? Math.round(innerWidth - m.querySelector('.pa-b').getBoundingClientRect().right) : 0,
    aBg: a ? getComputedStyle(a.querySelector('.pa-b')).backgroundColor : '', aBorder: a ? getComputedStyle(a.querySelector('.pa-b')).borderTopWidth : '',
    col: Math.round(document.querySelector('#v-pa .pc-col').getBoundingClientRect().width), talk: paTalk(paInit()).filter(x => !x.brief && !x.confirm).map(x => x.who + ':' + x.text.slice(0, 40)) } }"""

async def sec_compose(p, c):
    b, pg, errs = await open_app(p)
    await open_pa(pg, 'u_owner')
    st = await pg.evaluate("() => ({ tag: document.getElementById('pa-in').tagName, send: document.querySelector('#pa-ask .btn.primary') && document.querySelector('#pa-ask .btn.primary').getAttribute('aria-label'), dis: document.querySelector('#pa-ask [type=submit]').disabled })")
    c.ok(st['tag'] == 'TEXTAREA' and st['send'] == 'Send' and st['dis'], f'the box is a text area with one round Send, resting while it is empty: {st}')
    # Shift+Enter is a new line; Enter sends
    await pg.click('#pa-in')
    await pg.keyboard.type('what is on my day')
    await pg.keyboard.press('Shift+Enter')
    await pg.keyboard.type('and my week')
    st = await pg.evaluate("() => ({ v: document.getElementById('pa-in').value, me: paTalk(paInit()).filter(m => m.who === 'me').length, h: document.getElementById('pa-in').getBoundingClientRect().height })")
    c.ok(st['v'] == 'what is on my day\nand my week' and st['me'] == 0, f'Shift+Enter starts a new line and sends nothing: {st}')
    await pg.fill('#pa-in', '')
    await pg.keyboard.type('what is on my day')
    n = await pg.evaluate("() => paInit().thread.filter(m => m.who === 'a').length")
    await pg.keyboard.press('Enter')
    await pg.wait_for_function("n => !paBusy && paInit().thread.filter(m => m.who === 'a').length > n", arg=n, timeout=15000)
    await pg.wait_for_timeout(200)
    L = await pg.evaluate(LAST)
    c.ok(L['nMe'] == 1 and L['nA'] == 1 and await pg.evaluate("() => document.getElementById('pa-in').value") == '', f'Enter sends: one question, one answer, the box cleared: {L["talk"]}')
    c.ok(L['meBg'] not in ('rgba(0, 0, 0, 0)', 'transparent') and L['aBg'] in ('rgba(0, 0, 0, 0)', 'transparent') and L['aBorder'] == '0px', f"the person's message is a bubble, the answer is not: {L['meBg']} / {L['aBg']} {L['aBorder']}")
    c.ok(700 <= L['col'] <= 720, f"the conversation is a centred reading column about 720px wide: {L['col']}")
    c.ok(L['aActs'] == ['Copy', 'Retry'] and L['meActs'] == ['Copy', 'Edit and Send Again'], f"Copy and Retry under the last answer, Edit on the last question: {L['aActs']} {L['meActs']}")
    # Copy
    await pg.evaluate("() => { const as = [...document.querySelectorAll('#pa-thread .pa-m.a:not(.pa-brief)')]; as[as.length - 1].querySelector('[data-pcact^=\"copy\"]').click(); }")
    await pg.wait_for_timeout(250)
    c.ok('Copied' in await toast_text(pg), 'Copy copies the answer and says so')
    # Retry: the same question again, no second copy of it
    first = await pg.evaluate("() => paInit().thread.filter(m => m.who === 'a').slice(-1)[0].id")
    await pg.evaluate("() => { const as = [...document.querySelectorAll('#pa-thread .pa-m.a:not(.pa-brief)')]; as[as.length - 1].querySelector('[data-pcact^=\"retry\"]').click(); }")
    await pg.wait_for_function("id => !paBusy && paInit().thread.filter(m => m.who === 'a').slice(-1)[0].id !== id", arg=first, timeout=15000)
    await pg.wait_for_timeout(150)
    L = await pg.evaluate(LAST)
    c.ok(L['nMe'] == 1 and L['nA'] == 1 and L['talk'][0] == 'me:what is on my day', f'Retry asks the same question again, with no second copy: {L["talk"]}')
    # Edit the last question and send it again
    await pg.evaluate("() => { const ms = [...document.querySelectorAll('#pa-thread .pa-m.me')]; ms[ms.length - 1].querySelector('[data-pcact^=\"edit\"]').click(); }")
    await pg.wait_for_timeout(100)
    ed = await pg.evaluate("() => { const t = document.querySelector('#pa-thread .pc-edit-in'); return t ? t.value : null }")
    c.ok(ed == 'what is on my day', f'Edit opens the question in place: {ed!r}')
    await pg.fill('#pa-thread .pc-edit-in', 'what does my week look like')
    await pg.press('#pa-thread .pc-edit-in', 'Enter')
    await pg.wait_for_function("() => !paBusy && paTalk(paInit()).some(m => m.who === 'me' && /my week look like/.test(m.text)) && paTalk(paInit()).slice(-1)[0].who === 'a' && !paTalk(paInit()).slice(-1)[0].brief", timeout=15000)
    await pg.wait_for_timeout(150)
    L = await pg.evaluate(LAST)
    c.ok(L['nMe'] == 1 and L['talk'][0] == 'me:what does my week look like', f'the edited question replaces the old one and is answered: {L["talk"]}')
    # an offer that writes a draft: the draft shows under the answer with Approve and Edit
    await ask(pg, 'Draft a follow-up to Window Works about the ship date')
    clicked = await pg.evaluate("() => { const b = [...document.querySelectorAll('#pa-thread [data-csdo]')].find(b => /Outbox|Mailbox/.test(b.textContent)); b && b.click(); return !!b }")
    await pg.wait_for_timeout(300)
    if await pg.evaluate("() => !!document.getElementById('mbm')"):   # no address on file: the sheet asks for one first
        await pg.fill('#mbm [data-f=email]', 'orders@windowworks.example')
        await pg.click('#mbm-ok')
    await pg.wait_for_timeout(900)
    st = await pg.evaluate("() => { const d = [...document.querySelectorAll('#pa-thread .pc-draft')].pop(); const m = paInit().thread.filter(m => m.who === 'a').slice(-1)[0]; return { clicked: true, ids: m.drafts || [], text: d ? d.textContent : '', btns: d ? [...d.querySelectorAll('button')].map(b => b.textContent.trim()) : [] } }")
    c.ok(clicked and st['ids'] and st['btns'] == ['Approve and Send', 'Edit'] and 'Window Works' in st['text'], f'the draft it wrote shows under the answer, to read, with Approve and Send and Edit: {st}')
    if st['ids']:
        oid = st['ids'][0]
        await pg.evaluate("id => document.querySelector(`[data-pcdraft=\"edit|${id}\"]`).click()", oid)
        await pg.wait_for_timeout(150)
        md = await pg.evaluate("() => { const f = document.querySelector('#pa-thread [data-pcdraftform]'); return { modal: !!document.getElementById('mbm'), subj: f ? f.querySelector('[data-f=subject]').value : '' } }")
        c.ok(md['subj'] and not md['modal'], f'Edit opens the draft in place, in the conversation: {md}')
        await pg.fill('#pa-thread [data-pcdraftform] [data-f=subject]', 'When do the windows ship?')
        await pg.click('#pa-thread [data-pcdraftform] button[type=submit]'); await pg.wait_for_timeout(200)
        c.ok(await pg.evaluate("id => DB.outbox.find(o => o.id === id).subject", oid) == 'When do the windows ship?', 'the change is saved on the draft')
        await pg.evaluate("id => document.querySelector(`[data-pcdraft=\"approve|${id}\"]`).click()", oid)
        await pg.wait_for_function("id => (DB.outbox.find(o => o.id === id) || {}).status === 'sent'", arg=oid, timeout=8000)
        await pg.wait_for_timeout(200)
        st = await pg.evaluate("id => ({ t: document.getElementById('toast').textContent, row: ([...document.querySelectorAll('#pa-thread .pc-draft')].pop() || {}).textContent || '' })", oid)
        c.ok('Sent to' in st['t'] and 'Open' in st['t'] and (st['row'].startswith('Sent to') or 'Sent to' in str(await pg.evaluate("() => paInit().thread.slice(-1)[0].text"))), f'Approve sends it, with a toast and a reply: {st}')
    c.ok(not errs, f'compose: page errors {errs[:3]}')
    await b.close()

# ---------------------------------------------------------------------------------------------- 8: conversations
async def sec_convos(p, c):
    b, pg, errs = await open_app(p)
    await open_pa(pg, 'u_alan')
    await ask(pg, 'what is on my day')
    await pg.click('.view.on [data-panew]'); await pg.wait_for_timeout(200)
    t = await toast_text(pg)
    await ask(pg, 'which invoices are open')
    await pg.click('.view.on [data-panew]'); await pg.wait_for_timeout(200)
    await ask(pg, 'what am I waiting on')
    rows = await pg.evaluate("() => [...document.querySelectorAll('#pc-list .pc-row')].map(r => ({ t: r.querySelector('.pc-row-t').textContent, now: r.classList.contains('on'), id: r.dataset.paconvo || '' }))")
    c.ok([r['t'] for r in rows] == ['what am I waiting on', 'which invoices are open', 'what is on my day'] and rows[0]['now'], f'the side panel lists each conversation by its first question, newest first, the current one marked: {rows}')
    c.ok('New chat' in t and 'Open' in t, f'New Chat says where the last one went, with Open: {t!r}')
    vis = await pg.evaluate("() => { const s = document.getElementById('pc-side'); const r = s.getBoundingClientRect(); return r.width > 150 && getComputedStyle(s).visibility !== 'hidden' }")
    c.ok(vis, 'on a desk the conversations are a side panel beside the conversation')
    await pg.fill('#v-pa [data-pcsearch]', 'invoices')
    await pg.wait_for_timeout(100)
    found = await pg.evaluate("() => [...document.querySelectorAll('#pc-list .pc-row-t')].map(e => e.textContent)")
    c.ok(found == ['which invoices are open'], f'search filters the conversations: {found}')
    await pg.click('#pc-list [data-paconvo]'); await pg.wait_for_timeout(250)
    st = await pg.evaluate("() => ({ talk: paTalk(paInit()).map(m => m.text).slice(0, 1), convos: paConvos().map(c => c.title), box: !!document.getElementById('pa-in') })")
    c.ok(st['talk'] == ['which invoices are open'] and 'what am I waiting on' in st['convos'] and st['box'], f'pressing one continues it; the one you were in is filed: {st}')
    # a new day: yesterday's conversation is filed and the day opens on the briefing
    await pg.evaluate("() => { paInit().thread.forEach(m => { m.day = '2026-09-02'; }); paInit().briefShown = '2026-09-02'; }")
    await go(pg, 'home'); await go(pg, 'pa')
    st = await pg.evaluate("() => ({ talk: paTalk(paInit()).map(m => !!m.brief), first: (paConvos()[0] || {}).title, brief: !!document.querySelector('#pa-thread .pa-brief') })")
    c.ok(st['talk'] == [True] and st['first'] == 'which invoices are open' and st['brief'], f"a new day files yesterday's conversation and opens on the briefing: {st}")
    c.ok(not errs, f'convos: page errors {errs[:3]}')
    await b.close()
    # the phone: the panel is a drawer, closed until asked for
    b, pg, errs = await open_app(p, phone=True)
    await open_pa(pg, 'u_alan')
    await ask(pg, 'what is on my day')
    await pg.click('.view.on [data-panew]'); await pg.wait_for_timeout(200)
    shut = await pg.evaluate("() => getComputedStyle(document.getElementById('pc-side')).visibility")
    await pg.click('.view.on [data-pahist]'); await pg.wait_for_timeout(300)
    st = await pg.evaluate("() => { const s = document.getElementById('pc-side'); const r = s.getBoundingClientRect(); return { vis: getComputedStyle(s).visibility, left: Math.round(r.left), w: Math.round(r.width), rows: [...s.querySelectorAll('.pc-row-t')].map(e => e.textContent), over: document.documentElement.scrollWidth - innerWidth } }")
    c.ok(shut == 'hidden' and st['vis'] == 'visible' and st['left'] == 0 and st['w'] <= 340 and st['rows'] == ['what is on my day'] and st['over'] <= 1, f'on the phone the conversations are a drawer, shut until opened: {shut} {st}')
    await pg.click('#pc-side .pc-side-x'); await pg.wait_for_timeout(300)
    c.ok(await pg.evaluate("() => getComputedStyle(document.getElementById('pc-side')).visibility") == 'hidden', 'and it closes')
    c.ok(not errs, f'convos phone: page errors {errs[:3]}')
    await b.close()

# ---------------------------------------------------------------------------------------------- 9: streaming: Stop
def ev(name, data): return f"event: {name}\ndata: {json.dumps(data)}\n\n"
def msg_start(i='msg_1'): return ev('message_start', {'type': 'message_start', 'message': {'id': i, 'type': 'message', 'role': 'assistant', 'content': [], 'stop_reason': None, 'usage': {'input_tokens': 12, 'output_tokens': 1}}})
def text_events(pieces, index=0):
    out = ev('content_block_start', {'type': 'content_block_start', 'index': index, 'content_block': {'type': 'text', 'text': ''}})
    out += ''.join(ev('content_block_delta', {'type': 'content_block_delta', 'index': index, 'delta': {'type': 'text_delta', 'text': p}}) for p in pieces)
    return out + ev('content_block_stop', {'type': 'content_block_stop', 'index': index})
def msg_end(reason='end_turn'):
    return (ev('message_delta', {'type': 'message_delta', 'delta': {'stop_reason': reason, 'stop_sequence': None}, 'usage': {'output_tokens': 40}}) +
            ev('message_stop', {'type': 'message_stop'}) + ev('sd_done', {'usage': {'input_tokens': 12, 'output_tokens': 40}, 'cut': False}))
SLOW = ['The first line of a long answer. ', 'A second line, ', 'a third, ', 'a fourth, ', 'a fifth, ', 'a sixth, ', 'a seventh, ', 'and the end.']
CALLS = []

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
        if not self.path.startswith('/api/ai'):
            self.send_response(404); self.end_headers(); return
        CALLS.append(body)
        self.send_response(200); self.send_header('content-type', 'text/event-stream'); self.send_header('cache-control', 'no-store'); self.send_header('connection', 'close'); self.end_headers()
        try:
            self.wfile.write(msg_start().encode()); self.wfile.flush()
            self.wfile.write(ev('content_block_start', {'type': 'content_block_start', 'index': 0, 'content_block': {'type': 'text', 'text': ''}}).encode()); self.wfile.flush()
            for p in SLOW:
                time.sleep(0.5)
                self.wfile.write(ev('content_block_delta', {'type': 'content_block_delta', 'index': 0, 'delta': {'type': 'text_delta', 'text': p}}).encode()); self.wfile.flush()
            self.wfile.write((ev('content_block_stop', {'type': 'content_block_stop', 'index': 0}) + msg_end()).encode()); self.wfile.flush()
        except Exception:
            pass

def serve():
    s = ThreadingHTTPServer(('127.0.0.1', 0), Door)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, f'http://127.0.0.1:{s.server_address[1]}/'

async def open_http(p, url):
    b = await p.chromium.launch()
    ctx = await b.new_context(viewport=DESKTOP)
    pg = await ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('console', lambda m: m.type == 'error' and 'fonts.g' not in m.text and 'ERR_' not in m.text and 'Failed to load resource' not in m.text and errs.append('console: ' + m.text))
    await pg.goto(url)
    await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
    return b, pg, errs

async def sec_stream(p, c):
    srv, url = serve()
    b, pg, errs = await open_http(p, url)
    try:
        await open_pa(pg, 'u_owner')
        c.ok(await pg.evaluate("() => mindCan() && paStreamOn()"), 'served over http with a door, the assistant streams')
        await pg.fill('#pa-in', 'Write a haiku about brownstones')
        await pg.evaluate("() => document.querySelector('#pa-ask').requestSubmit()")
        await pg.wait_for_function("() => paLive && paLive.text && paLive.text.length > 10", timeout=15000)
        await pg.wait_for_timeout(150)   # the live answer redraws a few times a second
        st = await pg.evaluate("() => { " + VIS + " return { stop: !!document.querySelector('#pa-ask [data-pastop]') && vis(document.querySelector('#pa-ask [data-pastop]')), primary: [...document.querySelectorAll('.btn.primary')].filter(vis).length, caret: !!document.querySelector('#pa-live-md .pa-caret') } }")
        c.ok(st['stop'] and st['primary'] == 0 and st['caret'], f'while words arrive, Send is a Stop, no blue button shows, and a soft cursor follows the words: {st}')
        await pg.press('#pa-in', 'Escape')
        await pg.wait_for_function("() => !paBusy", timeout=5000)
        part = await pg.evaluate("() => { const m = paInit().thread.filter(m => m.who === 'a').slice(-1)[0]; return { text: m.text, stopped: !!m.stopped, n: paInit().thread.filter(m => m.who === 'a').length } }")
        await pg.wait_for_timeout(4500)
        after = await pg.evaluate("() => ({ n: paInit().thread.filter(m => m.who === 'a').length, last: paInit().thread.filter(m => m.who === 'a').slice(-1)[0].text, label: ([...document.querySelectorAll('#pa-thread .pa-m.a')].pop().querySelector('.pc-stopped') || {}).textContent, send: !!document.querySelector('#pa-ask .btn.primary[type=submit]') })")
        c.ok(part['stopped'] and part['text'].startswith('The first line') and 'and the end' not in part['text'], f'Escape stops it: what came stays, marked stopped: {part}')
        c.ok(after['n'] == part['n'] and after['last'] == part['text'] and after['label'] == 'Stopped' and after['send'], f'nothing arrives after Stop, the answer says Stopped, and Send is back: {after}')
        c.ok(await pg.evaluate("() => mindState.ok !== false"), 'stopping is not counted as the model failing')
        # the next question is answered in full
        n = len(CALLS)
        await pg.fill('#pa-in', 'Narrate the brownstone saga')
        await pg.evaluate("() => document.querySelector('#pa-ask').requestSubmit()")
        await pg.wait_for_function("() => !paBusy && /and the end/.test(paInit().thread.filter(m => m.who === 'a').slice(-1)[0].text)", timeout=20000)
        c.ok(len(CALLS) == n + 1, f'the next question is answered in full, in one call: {len(CALLS) - n}')
        # the Stop button, pressed
        await pg.fill('#pa-in', 'Opine on the cornice')
        await pg.evaluate("() => document.querySelector('#pa-ask').requestSubmit()")
        await pg.wait_for_function("() => paLive && paLive.text && paLive.text.length > 10", timeout=15000)
        await pg.click('#pa-ask [data-pastop]')
        await pg.wait_for_function("() => !paBusy", timeout=5000)
        c.ok(await pg.evaluate("() => !!paInit().thread.filter(m => m.who === 'a').slice(-1)[0].stopped"), 'the Stop button stops it too')
        # a tool that writes a draft (Drafts in My Mailbox is Act Alone by default): the draft is under the answer
        async def route_tool(route):
            body = json.loads(route.request.post_data or '{}')
            second = any(isinstance(m.get('content'), list) and any(x.get('type') == 'tool_result' for x in m['content']) for m in body.get('messages', []))
            sse = (msg_start('m2') + text_events(['I drafted the note to Window Works; it waits for you.']) + msg_end()) if second else (
                msg_start('m1') + ev('content_block_start', {'type': 'content_block_start', 'index': 0, 'content_block': {'type': 'tool_use', 'id': 'toolu_1', 'name': 'draft_email', 'input': {}}}) +
                ev('content_block_delta', {'type': 'content_block_delta', 'index': 0, 'delta': {'type': 'input_json_delta', 'partial_json': json.dumps({'to': 'Window Works', 'subject': 'Ship date for the windows', 'body': 'Hi, when do the windows ship? Thank you.', 'why': 'you asked'})}}) +
                ev('content_block_stop', {'type': 'content_block_stop', 'index': 0}) + msg_end('tool_use'))
            await route.fulfill(status=200, headers={'content-type': 'text/event-stream'}, body=sse)
        await pg.route('**/api/ai', route_tool)
        await pg.fill('#pa-in', 'Compose a note to Window Works asking when the windows ship')
        await pg.evaluate("() => document.querySelector('#pa-ask').requestSubmit()")
        await pg.wait_for_function("() => !paBusy && /drafted the note/.test(paInit().thread.filter(m => m.who === 'a').slice(-1)[0].text)", timeout=20000)
        await pg.wait_for_timeout(200)
        st = await pg.evaluate("() => { const m = paInit().thread.filter(m => m.who === 'a').slice(-1)[0]; const d = [...document.querySelectorAll('#pa-thread .pa-m.a')].pop().querySelector('.pc-draft'); return { ids: m.drafts || [], btns: d ? [...d.querySelectorAll('button')].map(b => b.textContent.trim()) : [], text: d ? d.textContent : '' } }")
        c.ok(st['ids'] and st['btns'] == ['Approve and Send', 'Edit'] and 'Ship date for the windows' in st['text'], f"a draft the answer's tool wrote is under the answer, with Approve and Edit: {st}")
        await pg.unroute('**/api/ai')
        c.ok(not errs, f'stream: page errors {errs[:3]}')
    finally:
        await b.close()
        srv.shutdown()

# ---------------------------------------------------------------------------------------------- 9b: the mind's hooks
async def sec_mind(p, c):
    """The mind lane's answer carries a summary of its steps (mindStepSummary), the records it names (r.links) and
    figures it could not trace marked "(not confirmed)"; the person's model is a card under Activity."""
    b, pg, errs = await open_app(p)
    await open_pa(pg, 'u_owner')
    st = await pg.evaluate("""() => { paSay('me', 'is the Window Works bill right?'); paSay('a', 'The **WW-2026-118** bill is $33,500 against a $29,700 PO, $1,200 of freight (not confirmed).',
        { md: true, did: [{ t: 'Reading the Window Works bill WW-2026-118', d: '' }, { t: 'Checking the answer against what I read', d: '2 figures traced, 1 marked not confirmed' }], summary: 'Read 1 record, checked 2 figures',
          links: [{ text: 'WW-2026-118', label: 'the Window Works bill WW-2026-118', go: { view: 'ap' } }] }); renderPa();
        const a = [...document.querySelectorAll('#pa-thread .pa-m.a')].pop();
        return { link: (a.querySelector('[data-pclink]') || {}).textContent || '', nc: (a.querySelector('.pa-nc') || {}).textContent || '', sum: (a.querySelector('.pa-did summary') || {}).textContent || '', steps: [...a.querySelectorAll('.pa-did li')].map(l => l.textContent) } }""")
    c.ok(st['link'] == 'WW-2026-118', f"a record the answer names is a link in its prose: {st['link']!r}")
    c.ok(st['nc'] == '(not confirmed)', 'a figure it could not trace reads as a quiet "(not confirmed)"')
    c.ok(st['sum'] == 'Read 1 record, checked 2 figures' and any('Checking the answer' in x for x in st['steps']), f"How I got there carries the mind's summary and the check: {st['sum']!r} {st['steps']}")
    await pg.evaluate("() => [...document.querySelectorAll('#pa-thread [data-pclink]')].pop().click()")
    await pg.wait_for_timeout(200)
    c.ok(await pg.evaluate("view") == 'ap', 'the link opens the record')
    await go(pg, 'pa')
    await pg.evaluate("() => paOpen('activity')"); await pg.wait_for_timeout(200)
    st = await pg.evaluate("() => { const k = document.querySelector('#v-pa [data-mdprof]'); return { card: !!k, blue: k ? k.querySelectorAll('.btn.primary').length : -1 } }")
    c.ok(st['card'] and st['blue'] == 0, f'what the assistant knows about the person is a card of their own under Activity, no blue buttons: {st}')
    c.ok(not errs, f'mind: page errors {errs[:3]}')
    await b.close()
    # the phone: history, the tabs and New Chat are one row
    b, pg, errs = await open_app(p, phone=True)
    await open_pa(pg, 'u_owner')
    st = await pg.evaluate("() => { const t = document.querySelector('#v-pa .pc-top').getBoundingClientRect(); return { h: Math.round(t.height), sel: !!document.querySelector('#v-pa .pc-top [data-pctab]'), link: getComputedStyle(document.querySelector('#v-pa a.pa-rec') || document.body).textDecorationLine } }")
    c.ok(st['h'] <= 52 and st['sel'] and st['link'] == 'none', f'on the phone history, the tabs and New Chat are one row, and links are not underlined: {st}')
    await pg.select_option('#v-pa [data-pctab]', 'activity'); await pg.wait_for_timeout(200)
    c.ok(await pg.evaluate("paTab") == 'activity', 'the tab menu changes the tab')
    c.ok(not errs, f'mind phone: page errors {errs[:3]}')
    await b.close()

# ---------------------------------------------------------------------------------------------- 10: phone and the screen standard
def lint_parts():
    src = open(os.path.join(HERE, 'lint.py'), encoding='utf-8').read().replace('asyncio.run(main())', '')
    ns = {'__name__': 'lint_parts', '__file__': os.path.join(HERE, 'lint.py')}
    exec(compile(src, 'lint.py', 'exec'), ns)
    return ns

async def sec_phone(p, c):
    L = lint_parts()
    os.makedirs(SHOTS, exist_ok=True)
    for phone in (True, False):
        b, pg, errs = await open_app(p, phone=phone)
        nd = await pg.evaluate(L['NAMES_JS'])
        args = {'SMALL': sorted(L['SMALL']), 'UNITS': sorted(L['UNITS']), 'HOUSEKEEPING': L['HOUSEKEEPING'], 'NAMES': nd['names'], 'DATA': nd['data'], 'CHARTS': L['CHARTS'], 'PHONE': phone, 'WALL': L['wall_dates']()}
        vp = 'phone' if phone else 'desktop'
        for u in ROLES:
            await open_pa(pg, u)
            if u == 'u_owner':
                await pg.evaluate("b => gsIngestServer(b)", {'asst': [run('u_owner', '07:02:00', [draft('00000000000000b1', 'orderFollowups', 'Window Works', 'orders@windowworks.example', 'Confirming the ship date for the windows')])]})
                await go(pg, 'home'); await go(pg, 'pa')
            LINT = """async () => { document.querySelectorAll('.toast.on, #toast.on').forEach(t => t.classList.remove('on')); }"""
            async def judge(state, top=True):
                await pg.evaluate(LINT)
                top and await pg.evaluate("() => { document.body.scrollTop = 0; scrollTo(0, 0); }")
                await pg.wait_for_timeout(150)
                r = await pg.evaluate(L['COLLECT'], args)
                fl = [f for f in r['flags'] if not f.get('chrome')]
                c.ok(not fl, f"{vp} {u} {state}: the screen standard holds: {[(f['rule'], f['detail'][:90]) for f in fl[:3]]}")
                if phone: c.ok(await pg.evaluate("() => document.documentElement.scrollWidth - innerWidth") <= 1, f'{vp} {u} {state}: no sideways scroll')
            await pg.evaluate("() => renderPa()")
            await judge('briefing')
            if phone:
                d = await pg.evaluate("() => { const d = document.querySelector('#v-pa .pa-dock').getBoundingClientRect(), t = document.getElementById('mtabs'), tr = t && t.getBoundingClientRect(); return { top: d.top, bottom: d.bottom, h: innerHeight, tabTop: tr && tr.height ? tr.top : innerHeight, pos: getComputedStyle(document.querySelector('#v-pa .pa-dock')).position, inp: document.getElementById('pa-ask').getBoundingClientRect().height, fs: getComputedStyle(document.getElementById('pa-in')).fontSize } }")
                c.ok(d['pos'] == 'sticky' and abs(d['bottom'] - d['tabTop']) <= 1 and d['top'] > d['h'] / 2 and d['inp'] >= 44 and d['fs'] == '16px', f'{u} phone: the box sits on the tab bar, thumb-sized, 16px text: {d}')
            await pg.screenshot(path=os.path.join(SHOTS, f'{u}_{vp}_briefing.png'), full_page=False)
            if await pg.evaluate("() => !!document.querySelector('#v-pa [data-pabfrest]')"):
                await pg.evaluate("() => { paBriefRest(); paScroll(); }")
                await judge('the rest', top=False)
                await pg.screenshot(path=os.path.join(SHOTS, f'{u}_{vp}_rest.png'), full_page=False)
            # a conversation: a table, a list, a link, the work shown, and the box at the foot
            await pg.evaluate("""() => { paSay('me', 'how do the jobs stand?'); paSay('a', 'Two of the four jobs are on track; **45 Cranberry** waits on tile.\\n\\n| Job | Status | Next |\\n|---|---|---|\\n| 121 State | On track | Rough inspection Tue |\\n| 45 Cranberry | Waiting on tile | Chase Nemo Tile |\\n\\n- The tile slipped to Thursday.\\n- The windows ship Monday.\\n\\nThe [schedule](https://example.com/schedule) has the rest. Shall I draft the tile chase?', { md: true, did: [{ t: 'Reading the projects', d: 'projects, 4 rows' }, { t: 'Searching your mail', d: '\\"Nemo Tile\\"' }] }); renderPa(); pcToBottom(); }""")
            await judge('conversation', top=False)
            await pg.evaluate("() => pcToBottom()"); await pg.wait_for_timeout(150)
            rest = await pg.evaluate("() => { const a = [...document.querySelectorAll('#pa-thread .pa-m.a')].pop().querySelector(':scope > .pc-acts').getBoundingClientRect(), d = document.getElementById('pc-dock').getBoundingClientRect(); return { acts: Math.round(a.bottom), dock: Math.round(d.top) } }")
            c.ok(rest['acts'] <= rest['dock'], f'{vp} {u}: scrolled to the newest, the last message and its actions rest above the box: {rest}')
            await pg.screenshot(path=os.path.join(SHOTS, f'{u}_{vp}_conversation.png'), full_page=False)
            if phone and u == 'u_owner':
                await pg.evaluate("() => { paHistOpen = true; renderPa(); }"); await pg.wait_for_timeout(300)
                await judge('drawer')
                await pg.screenshot(path=os.path.join(SHOTS, f'{u}_{vp}_drawer.png'), full_page=False)
                await pg.evaluate("() => { paHistOpen = false; renderPa(); }")
            # a new chat: the greeting, the box, the suggestions
            await pg.evaluate("() => { paNewConvo(true); paNewConvo(true); renderPa(); }")
            await judge('new chat')
            await pg.screenshot(path=os.path.join(SHOTS, f'{u}_{vp}_new_chat.png'), full_page=False)
        c.ok(not errs, f'{vp}: page errors {errs[:3]}')
        await b.close()

async def main():
    c = Checks()
    async with async_playwright() as p:
        for name, f in (('brief', sec_brief), ('runs', sec_runs), ('approve', sec_approve), ('follow', sec_follow), ('memory', sec_memory), ('voice', sec_voice),
                        ('compose', sec_compose), ('convos', sec_convos), ('stream', sec_stream), ('mind', sec_mind), ('phone', sec_phone)):
            if len(sys.argv) > 1 and name not in sys.argv[1:]: continue
            t0 = time.time()
            try:
                await f(p, c)
            except Exception as e:
                c.ok(False, f'{name}: {type(e).__name__}: {str(e).splitlines()[0][:300]}')
            print(f'-- {name} done in {time.time() - t0:.0f}s, {len(c.fail)} failing so far')
    sys.exit(c.done())

asyncio.run(main())
