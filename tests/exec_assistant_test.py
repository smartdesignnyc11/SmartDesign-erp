"""The assistant leads (lane "exec", 2026-10-19). Alan: "It's a personal assistant not just a bot that responds to your
questions. It needs to think and act like a Fortune 500 executive assistant, an assistant project manager."

  1. brief     Ask opens on the briefing, not an empty box, for the owner, the PM, the coordinator and billing: a
               headline sentence, then Today, I Did, Needs You and I'm Chasing; no intro bubble; every Needs You row
               carries its reason and Standard value; the card's count is its rows; suggested asks come from the
               briefing (not the old fixed chips); one blue button on the screen; Got It folds it to its headline and
               it stays folded today. The PM and the owner see their jobs' late schedule work, the Friday update and
               what the field waits on (RFIs, submittals, client decisions); the coordinator does not.
  2. runs      a fake server run through gsIngestServer({asst}): the briefing is filed and its headline used, its
               drafts wait in the outbox for approval (deduped by key across runs), another person's run is never
               filed, nothing is sent; a type set to Act Alone is sent through the follow-up path and logged; a
               client update is never sent on its own, whatever the rule.
  3. approve   a draft approved from Needs You is sent by the person (bnSend), with a toast naming who it went to.
  4. follow    "I'll get back to Chen Friday" with Tasks for Me on Act Alone is a task under I'm Chasing and a line in
               I Did with Undo; Undo removes the task. On Ask First (the PM's default) it is a one-tap offer. "Chen will
               send the window lead time Friday" goes on the wait ledger, under I'm Chasing.
  5. memory    a correction ("don't book me before 9") is a standing instruction, fed into the prompt, listed under
               Activity > How You Work, edited and deleted there, and added from there; three Not Nows on one kind
               propose a memory the person keeps; another person never sees it.
  6. voice     the microphone shows only where the browser has speech recognition; what it hears lands in the box.
  7. phone     390 px: the screen standard (lint.py's own collector) on the briefing open and folded, no sideways
               scroll, the box docked above the tab bar and inside the screen. Screenshots in review/exec_assistant/.
"""
import asyncio, os, re, sys, time
from harness import *

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(ROOT, 'review', 'exec_assistant')
ROLES = ('u_owner', 'u_alan', 'u_chen', 'u_billing')

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

BRIEF_STATE = """() => {
  const d = document.querySelector('#v-pa details[data-pabrief]');
  const secs = [...document.querySelectorAll('#v-pa .pa-bf-card')].map(s => ({ k: s.dataset.pabfsec, h: s.querySelector('h3').textContent.trim(), n: +s.querySelector('[data-pabfn]').dataset.pabfn, rows: s.querySelectorAll('.pa-bf-row').length }));
  const needRows = [...document.querySelectorAll('#v-pa .pa-bf-card[data-pabfsec="needs"] .pa-bf-row')];
  const vis = el => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  return {
    open: !!(d && d.open), head: (document.querySelector('#v-pa [data-pabfhead]') || {}).textContent || '', secs,
    whyAll: needRows.every(r => !!r.querySelector('.pa-bf-why')), needKeys: needRows.map(r => r.dataset.pabfkey),
    intro: document.querySelectorAll('#pa-thread .pa-m').length, threadShown: (() => { const t = document.getElementById('pa-thread'); return !!t && vis(t); })(),
    chips: [...document.querySelectorAll('#v-pa .pa-chips [data-pachip]')].map(b => b.textContent.trim()),
    primary: [...document.querySelectorAll('.btn.primary')].filter(vis).map(b => b.textContent.trim()),
    model: (() => { const B = paBriefModel(true); return { needs: B.needs.length, did: B.did.length, chasing: B.chasing.length, today: B.today.length, needKeys: B.needs.map(x => x.key), chaseKeys: B.chasing.map(x => x.key), chaseKinds: B.chasing.map(x => x.k) }; })(),
  };
}"""

# ---------------------------------------------------------------------------------------------- 1: the briefing
async def sec_brief(p, c):
    b, pg, errs = await open_app(p)
    for u in ROLES:
        await open_pa(pg, u)
        s = await pg.evaluate(BRIEF_STATE)
        c.ok(s['open'], f'{u}: Ask opens on the briefing, open')
        c.ok([x['h'] for x in s['secs']] == ['Today', 'I Did', 'Needs You', "I'm Chasing"], f"{u}: four cards in order: {[x['h'] for x in s['secs']]}")
        c.ok(len(s['head']) > 20 and s['head'][0].isupper() and s['head'].rstrip().endswith('.'), f"{u}: one headline sentence first: {s['head'][:120]!r}")
        c.ok(s['intro'] == 0 and not s['threadShown'], f"{u}: no empty conversation box and no intro bubble (bubbles {s['intro']}, thread shown {s['threadShown']})")
        n = {x['k']: x for x in s['secs']}
        c.ok(n['needs']['n'] == s['model']['needs'] and n['chasing']['n'] == s['model']['chasing'] and n['did']['n'] == s['model']['did'], f"{u}: each card's count is its rows: {[(x['k'], x['n']) for x in s['secs']]} vs {s['model']}")
        c.ok(s['whyAll'], f'{u}: every Needs You row says why, with the Standard value')
        c.ok(s['chips'] and not set(s['chips']) & {'My Day', 'My List', 'Waiting on Me', 'I Am Waiting On', 'What You Hold'}, f"{u}: suggested asks come from the briefing, not the fixed chips: {s['chips']}")
        c.ok(s['primary'] == ['Send'], f"{u}: one blue button, the safe next step: {s['primary']}")
        if s['model']['needs']:
            first = await pg.evaluate("() => paBriefModel(true).needs[0].title")
            c.ok(first in s['head'] or bool(await pg.evaluate("() => !!paLatestRun()")), f'{u}: the headline names the first thing that needs them')
            c.ok(s['chips'][0] == 'Walk Me Through the First', f"{u}: the first suggested ask is about the first thing: {s['chips'][:1]}")
        pm = u in ('u_owner', 'u_alan')
        kinds = set(s['model']['chaseKinds'])
        if pm:
            c.ok(any(k.startswith('late:') or k.startswith('fri:') for k in s['model']['needKeys']), f"{u}: Needs You holds the jobs' late schedule work or the Friday update: {s['model']['needKeys'][:8]}")
            c.ok(any(k.startswith('fri:') for k in s['model']['needKeys']), f'{u}: the Friday client update is on Needs You on a Thursday')
            c.ok(kinds & {'RFI', 'Submittal', 'Client Decision', 'Delivery'}, f"{u}: I'm Chasing follows what the jobs wait on: {sorted(kinds)}")
        else:
            c.ok(not any(k.startswith('fri:') or k.startswith('late:') for k in s['model']['needKeys']), f'{u}: no project-manager items for this role')
    # the Friday update: Review and Send opens the draft, written from the client-safe schedule, for the person to send
    await open_pa(pg, 'u_alan')
    key = await pg.evaluate("() => paBriefModel(true).needs.find(x => x.key.startsWith('fri:')).key")
    await pg.evaluate("k => { paBfAll.needs = true; renderPa(); document.querySelector(`[data-pabfkey=\"${k}\"] [data-pabf]`).click(); }", key)
    await pg.wait_for_timeout(200)
    m = await pg.evaluate("() => { const m = document.getElementById('mbm'); return m ? { t: m.querySelector('h3').textContent, body: m.querySelector('[data-f=body]').value, ok: m.querySelector('#mbm-ok').textContent } : null }")
    c.ok(m and m['ok'] == 'Send' and 'this week' in m['body'] and not re.search(r'\$\d', m['body']), f'the Friday update opens as a draft to review, with no money in it: {m and m["body"][:120]}')
    held = await pg.evaluate("() => (DB.outbox || []).filter(o => /^asst\\|friday\\|/.test(o.aboutKey) && o.status === 'draft').length")
    c.ok(held == 1, f'the Friday update waits in the outbox as one draft until sent ({held})')
    await pg.evaluate("() => mbCloseModal()")
    # Got It folds the briefing to its headline, and it stays folded today
    await open_pa(pg, 'u_owner')
    await pg.click('#v-pa [data-pabfread]')
    await pg.wait_for_timeout(150)
    st = await pg.evaluate("() => ({ open: document.querySelector('#v-pa details[data-pabrief]').open, read: paInit().briefRead, head: document.querySelector('#v-pa [data-pabfhead]').getBoundingClientRect().height })")
    c.ok(not st['open'] and st['read'] == '2026-09-03' and st['head'] > 0, f'Got It folds the briefing to its headline: {st}')
    await go(pg, 'home'); await go(pg, 'pa')
    c.ok(not await pg.evaluate("() => document.querySelector('#v-pa details[data-pabrief]').open"), 'read today, it stays folded on the next visit')
    c.ok(not errs, f'brief: page errors {errs[:3]}')
    await b.close()

# ---------------------------------------------------------------------------------------------- 2: server runs
def run(person, key, drafts, headline='Two things need you before 10; the tile delivery slipped to Thursday and I have told the PM.'):
    return {'key': f'asst:{person}:{key}', 'at': f'2026-09-03T{key}', 'person': person,
            'brief': {'headline': headline, 'today': [{'title': 'Site walk at 121 State, 2:00', 'why': 'on your calendar', 'value': '', 'due': '2026-09-03', 'refs': [{'kind': 'job', 'id': 'p1'}]}],
                      'needs': [{'title': 'Tile delivery slipped to Thursday', 'why': 'Nemo Tile wrote at 6:40', 'value': 'Think ahead', 'due': '2026-09-03', 'refs': [{'kind': 'mail', 'id': 'nomail'}]}],
                      'chasing': [{'title': 'Carlos Millwork owes the shop drawings', 'why': 'promised for Tuesday', 'value': 'Own it', 'due': '2026-09-01', 'refs': []}]},
            'drafts': drafts, 'notes': ['Read 14 messages and 3 calendar changes.']}

def draft(k, typ, to, email, subj):
    return {'key': f'ad:{k}', 'type': typ, 'to': {'name': to, 'email': email}, 'subject': subj, 'body': f'Hi,\n\n{subj}.\n\nThank you', 'because': f'{to} has not confirmed', 'value': 'Own it', 'refs': [{'kind': 'po', 'id': 'po1'}]}

async def sec_runs(p, c):
    b, pg, errs = await open_app(p)
    await open_pa(pg, 'u_owner')
    o0 = await pg.evaluate("() => (DB.outbox || []).length")
    box = {'asst': [run('u_owner', '07:02:00', [draft('0000000000000001', 'orderFollowups', 'Window Works', 'orders@windowworks.example', 'Confirming the ship date for PO-2026-044'),
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
    later = {'asst': [run('u_owner', '11:02:00', [draft('0000000000000001', 'orderFollowups', 'Window Works', 'orders@windowworks.example', 'Confirming the ship date for PO-2026-044')], headline='Later run.')]}
    await pg.evaluate("b => gsIngestServer(b)", later)
    dup = await pg.evaluate("() => ({ d: DB.outbox.filter(o => o.aboutKey === 'asst|ad:0000000000000001').length, briefs: paInit().briefs.length, head: paBriefModel(true).headline })")
    c.ok(n2 == 0 and dup['d'] == 1 and dup['briefs'] == 2 and dup['head'] == 'Later run.', f'deduped by key across runs; the newest briefing wins: {n2}, {dup}')
    # Act Alone: the person handed over order follow-ups; a client update is never sent on its own
    await pg.evaluate("() => { paRuleSet('u_owner', 'orderFollowups', 'alone'); paRuleSet('u_owner', 'clientMessages', 'alone'); }")
    box3 = {'asst': [run('u_owner', '15:02:00', [draft('0000000000000004', 'orderFollowups', 'Window Works', 'orders@windowworks.example', 'Tracking for PO-2026-044'),
                                                 draft('0000000000000005', 'clientUpdate', 'Sarah Klein', 'sarah@klein.example', 'Friday note'),
                                                 draft('0000000000000006', 'orderFollowups', 'Sarah Klein', 'sarah@klein.example', 'To a client address')])]}
    await pg.evaluate("b => gsIngestServer(b)", box3)
    st3 = await pg.evaluate("""() => { const f = k => DB.outbox.find(o => o.aboutKey === 'asst|ad:' + k) || {}; return { a: [f('0000000000000004').status, f('0000000000000004').approvedBy], cu: f('0000000000000005').status, cl: f('0000000000000006').status,
        did: (paInit().log || []).some(e => e.type === 'orderFollowups' && /Sent on its own/.test(e.what)), std: (DB.company.standardLog || []).some(x => /delegated: orderFollowups/.test(JSON.stringify(x))) } }""")
    c.ok(st3['a'][0] == 'sent' and str(st3['a'][1]).startswith('delegated'), f'a type set to Act Alone is sent through the follow-up path: {st3}')
    c.ok(st3['cu'] == 'draft' and st3['cl'] == 'draft', f'a client update, or anything to a client address, stays a draft whatever the rule: {st3}')
    c.ok(st3['did'], 'what it sent on its own is in its log')
    c.ok(not errs, f'runs: page errors {errs[:3]}')
    await b.close()

# ---------------------------------------------------------------------------------------------- 3: approve from Needs You
async def sec_approve(p, c):
    b, pg, errs = await open_app(p)
    await open_pa(pg, 'u_owner')
    await pg.evaluate("b => gsIngestServer(b)", {'asst': [run('u_owner', '08:00:00', [draft('00000000000000a1', 'orderFollowups', 'Window Works', 'orders@windowworks.example', 'Confirming the ship date for PO-2026-044')])]})
    await go(pg, 'home'); await go(pg, 'pa')
    oid = await pg.evaluate("() => DB.outbox.find(o => o.aboutKey === 'asst|ad:00000000000000a1').id")
    await pg.evaluate("() => { paBfAll.needs = true; renderPa(); }")
    btn = f'[data-pabfkey="q:draft:{oid}"] [data-pabf]'
    label = await pg.evaluate("s => (document.querySelector(s) || {}).textContent", btn)
    c.ok(label == 'Approve', f'the draft on Needs You leads with Approve: {label}')
    await pg.evaluate("s => document.querySelector(s).click()", btn)
    await pg.wait_for_function("id => (DB.outbox.find(o => o.id === id) || {}).status === 'sent'", arg=oid, timeout=8000)
    t = await toast_text(pg)
    o = await pg.evaluate("id => { const o = DB.outbox.find(x => x.id === id); return { by: o.approvedBy, sentBy: o.sentBy } }", oid)
    c.ok('Sent to Window Works' in t, f'a toast says who it went to: {t!r}')
    c.ok(o['by'] == 'Owner' or o['by'], f'the person approved and sent it: {o}')
    gone = await pg.evaluate("id => !paBriefModel(true).needs.some(x => x.key === 'q:draft:' + id)", oid)
    c.ok(gone, 'once sent it is off Needs You')
    # Not Now: off the briefing until the next working day, still on Approvals
    k2 = await pg.evaluate("() => paBriefModel(true).needs[0].key")
    await pg.evaluate("k => document.querySelector(`[data-pabfkey=\"${k}\"] .pa-bf-act button:last-child`).click()", k2)
    await pg.wait_for_timeout(150)
    st = await pg.evaluate("k => ({ off: !paBriefModel(true).needs.some(x => x.key === k), until: paInit().snooze[k], t: document.getElementById('toast').textContent })", k2)
    c.ok(st['off'] and st['until'] == '2026-09-04' and 'Not now' in st['t'], f'Not Now puts it off to the next working day: {st}')
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
    # Undo from I Did
    await go(pg, 'home'); await go(pg, 'pa')
    await pg.evaluate("() => { paBfOpen = true; paBfAll.did = true; renderPa(); }")
    clicked = await pg.evaluate("""() => { const r = [...document.querySelectorAll('[data-pabfsec="did"] .pa-bf-row')].find(r => /Put on your list/.test(r.textContent)); const u = r && [...r.querySelectorAll('button')].find(b => b.textContent === 'Undo'); u && u.click(); return !!u }""")
    await pg.wait_for_timeout(200)
    st2 = await pg.evaluate("id => ({ gone: !(DB.tasks || []).some(t => t.id === id), t: document.getElementById('toast').textContent, undone: (paInit().log || []).some(e => e.undo && e.undo.id === id && e.undone) })", st['t']['id'] if st['t'] else '')
    c.ok(clicked and st2['gone'] and st2['undone'] and st2['t'].startswith('Undone'), f'Undo takes the task back, with a toast: {st2}')
    # the PM's default is Ask First: a one-tap offer, then the task
    await open_pa(pg, 'u_alan')
    a = await ask(pg, "I'll call the inspector tomorrow")
    before = await pg.evaluate("() => (DB.tasks || []).filter(t => t.source && t.source.commit).length")
    c.ok('Shall I hold you to it' in a and before == 0, f'Ask First: it offers, and makes nothing until the person says so: {a!r}')
    clicked = await pg.evaluate("() => { const b = [...document.querySelectorAll('#pa-thread button')].find(b => /Put It on My List/.test(b.textContent)); b && b.click(); return !!b }")
    await pg.wait_for_timeout(200)
    st3 = await pg.evaluate("() => ({ n: (DB.tasks || []).filter(t => t.source && t.source.commit && /inspector/i.test(t.title)).length, chase: paBriefModel(true).chasing.some(x => x.k === 'You Promised' && /inspector/i.test(x.title)), props: (paInit().props || []).filter(e => e.type === 'makeTasks').map(e => e.outcome) })")
    c.ok(clicked and st3['n'] == 1 and st3['chase'] and 'approved' in st3['props'], f'one tap puts it on the list and under I\'m Chasing, logged as approved: {st3}')
    # what someone else owes goes on the wait ledger
    a = await ask(pg, 'Chen will send the window lead time Friday')
    st4 = await pg.evaluate("() => { const e = paExpectLedger().find(x => /window lead time/i.test(x.about)); return { e: e && { who: e.who, by: e.by }, chase: paBriefModel(true).chasing.filter(x => x.k === 'Owes You').map(x => x.title) } }")
    c.ok(st4['e'] and 'Chen' in st4['e']['who'] and st4['e']['by'] == '2026-09-04', f'a promise someone made goes on the wait ledger: {a!r} {st4["e"]}')
    c.ok(any('window lead time' in x for x in st4['chase']), f"and under I'm Chasing: {st4['chase']}")
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
    st = await pg.evaluate("id => ({ gone: !paInit().memo.some(m => m.id === id) && !paInit().standing.some(s => s.id === id), prompt: mindSystem().includes('before 9:30') })", mid)
    c.ok(st['gone'] and not st['prompt'], f'deleted, and out of the prompt: {st}')
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
        await pg.evaluate("k => { paBfAll.needs = true; renderPa(); const r = document.querySelector(`[data-pabfkey=\"${k}\"]`); [...r.querySelectorAll('button')].find(b => b.textContent === 'Keep It').click(); }", sug[0]['key'])
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
    await pg.click('#v-pa [data-pamic]')
    await pg.wait_for_timeout(200)
    st = await pg.evaluate("() => ({ v: document.getElementById('pa-in').value, send: !document.querySelector('#pa-ask [type=submit]').disabled, big: document.querySelector('[data-pamic]').getBoundingClientRect().width })")
    c.ok(st['v'] == 'what is on my day' and st['send'], f'what it hears lands in the box, ready to send: {st}')
    await pg.evaluate("() => { delete window.SpeechRecognition; delete window.webkitSpeechRecognition; window.webkitSpeechRecognition = undefined; renderPa(); }")
    c.ok(not await pg.evaluate("() => !!document.querySelector('#v-pa [data-pamic]')"), 'with no speech recognition, no microphone')
    await pg.evaluate("() => paOpen('activity')")
    speak = await pg.evaluate("() => !!document.querySelector('[data-paspeak]') === ('speechSynthesis' in window)")
    c.ok(speak, 'Read my answers aloud is a setting where the browser can speak')
    c.ok(not errs, f'voice: page errors {errs[:3]}')
    await b.close()

# ---------------------------------------------------------------------------------------------- 7: phone and the screen standard
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
                await pg.evaluate("b => gsIngestServer(b)", {'asst': [run('u_owner', '07:02:00', [draft('00000000000000b1', 'orderFollowups', 'Window Works', 'orders@windowworks.example', 'Confirming the ship date for PO-2026-044')])]})
                await go(pg, 'home'); await go(pg, 'pa')
            for state in ('open', 'all', 'folded'):
                await pg.evaluate("s => { paBfOpen = s !== 'folded'; paBfAll = s === 'all' ? { today: 1, did: 1, needs: 1, chasing: 1 } : {}; renderPa(); document.querySelectorAll('.toast.on, #toast.on').forEach(t => t.classList.remove('on')); document.body.scrollTop = 0; scrollTo(0, 0); }", state)
                await pg.wait_for_timeout(120)
                r = await pg.evaluate(L['COLLECT'], args)
                fl = [f for f in r['flags'] if not f.get('chrome')]
                c.ok(not fl, f"{vp} {u} briefing {state}: the screen standard holds: {[(f['rule'], f['detail'][:90]) for f in fl[:3]]}")
                over = await pg.evaluate("() => document.documentElement.scrollWidth - innerWidth")
                if phone: c.ok(over <= 1, f'{vp} {u} {state}: no sideways scroll ({over}px)')
            if phone:
                d = await pg.evaluate("() => { const d = document.querySelector('#v-pa .pa-dock').getBoundingClientRect(), t = document.getElementById('mtabs'), tr = t && t.getBoundingClientRect(); return { top: d.top, bottom: d.bottom, h: innerHeight, tabTop: tr && tr.height ? tr.top : innerHeight, pos: getComputedStyle(document.querySelector('#v-pa .pa-dock')).position, inp: document.getElementById('pa-in').getBoundingClientRect().height } }")
                c.ok(d['pos'] == 'fixed' and d['bottom'] <= d['tabTop'] + 1 and d['top'] > d['h'] / 2 and d['inp'] >= 44, f'{u} phone: the box is docked at the bottom, above the tab bar, thumb-sized: {d}')
            await pg.evaluate("() => { paBfOpen = true; paBfAll = {}; renderPa(); document.body.scrollTop = 0; }")
            await pg.wait_for_timeout(100)
            await pg.screenshot(path=os.path.join(SHOTS, f'{u}_{vp}.png'), full_page=not phone)
        c.ok(not errs, f'{vp}: page errors {errs[:3]}')
        await b.close()

async def main():
    c = Checks()
    async with async_playwright() as p:
        for name, f in (('brief', sec_brief), ('runs', sec_runs), ('approve', sec_approve), ('follow', sec_follow), ('memory', sec_memory), ('voice', sec_voice), ('phone', sec_phone)):
            if len(sys.argv) > 1 and name not in sys.argv[1:]: continue
            t0 = time.time()
            try:
                await f(p, c)
            except Exception as e:
                c.ok(False, f'{name}: {type(e).__name__}: {str(e).splitlines()[0][:300]}')
            print(f'-- {name} done in {time.time() - t0:.0f}s, {len(c.fail)} failing so far')
    sys.exit(c.done())

asyncio.run(main())
