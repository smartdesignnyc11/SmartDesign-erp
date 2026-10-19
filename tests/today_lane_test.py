"""Today: one queue per person, one task shape (BACKLOG §1.11 item 1, §1.14; docs/MENU_DRAFT.md shared finding 1).

What each person owes sat in five to eight places and the counts never agreed. Today (view "home") is now the one
list for every office role (owner, PM, coordinator, billing, controller): Approvals (PRED.waitingOnMe), Inbox
(messages with a decision waiting) and Tasks (tkAll(), the five task sources in one shape), each item in exactly one,
All their union in the Standard's order, and Team for a manager. This suite performs it as each person:
  1. each office role's Today holds the union of what they owe, with no item in two filters; the Tasks filter holds
     every open task they own (or that is offered to them) that Approvals or Inbox does not already hold;
  2. counts: each filter's number equals the rows it shows once opened in full; Approvals equals PRED.waitingOnMe,
     the Approvals page's Everything chip and the phone's Approvals tab badge;
  3. a task from each of the five sources (schedule, office, sales, obligation, the assistant) appears once, with
     its source named and a link that opens the record; every task has a person as its owner, never "Office";
  4. hand-offs: offered, the assigner still owns it and both lists show it; a decline needs a reason and comes
     back; an accept moves it;
  5. the Standard's recurring duties are created once, with the right owner, across sweeps, day turns and reloads;
  6. done means done: the inspection, the photos before a wall closes and the signed change order are asked for;
  7. Ask "what does Angel owe this week" and erpQuery's tasks entity read the same accessor;
  8. phone 390: no sideways scroll, filters and verbs big enough and 8px apart.
Invented data only."""
import asyncio, re, sys
from harness import *

OFFICE = [('u_owner', 'owner'), ('u_alan', 'pm'), ('u_chen', 'coord'), ('u_billing', 'billing'), ('u_controller', 'controller')]

MODEL = """() => { const M = tdyModel(), k = (it) => it.kind + ':' + it.id;
  return { appr: M.appr.map(k), inbox: M.inbox.map(k), tasks: M.tasks.map(k), all: M.all.map(k), team: M.team ? M.team.length : null,
           pred: PRED.waitingOnMe.count(), me: currentUser().id,
           taskOwners: M.tasks.map(it => [it.t.ownerUid, it.t.offeredToUid]),
           mine: tkAll({ open: true, uid: currentUser().id }).filter(t => !t.approval).map(t => ({ key: 'tdyTask:' + t.key, refs: t.refs })),
           held: [].concat(...M.appr.map(tdyApprRefs)).concat(M.inbox.map(i => 'comm:' + i.id)) }; }"""

# every row of the current filter, opened in full ("N more" expands in place, or names the full page)
ROWS = """async () => { const v = document.querySelector('.view.on'); const sec = v.querySelector('.td-do');
  let more = sec.querySelector('[data-tdyopen]'); if (more && /more/.test(more.innerText)) { more.click(); await new Promise(r => setTimeout(r, 250)); }
  const s2 = document.querySelector('.view.on .td-do');
  const link = s2.querySelector('.td-more'); const m = link ? (link.innerText.match(/^(\\d+) more in/) || []) : [];
  return { cards: s2.querySelectorAll('.td-card').length, moreIn: m[1] ? +m[1] : 0, count: +s2.querySelector('[data-tdcount]').dataset.tdcount,
           tab: s2.dataset.tdytab }; }"""


async def tabs_of(pg):
    return await pg.evaluate("() => [...document.querySelectorAll('.view.on [data-tdytabbtn]')].map(b => ({ k: b.dataset.tdytabbtn, n: (b.querySelector('.n') || {}).innerText || '' }))")


async def union_and_counts(c, pg, uid, tag):
    await sign_in(pg, uid); await go(pg, 'home'); await pg.wait_for_timeout(300)
    on = await pg.evaluate("() => !!document.querySelector('.view.on .td-home .td-tabs')")
    c.ok(on, f'{tag}: Home is Today, with its filters')
    if not on: return
    m = await pg.evaluate(MODEL)
    parts = m['appr'] + m['inbox'] + m['tasks']
    c.ok(len(parts) == len(set(parts)), f'{tag}: an item sits in two filters: {[k for k in set(parts) if parts.count(k) > 1][:4]}')
    c.ok(sorted(m['all']) == sorted(parts), f"{tag}: All ({len(m['all'])}) is the union of Approvals, Inbox and Tasks ({len(parts)})")
    c.ok(len(m['appr']) == m['pred'], f"{tag}: Approvals {len(m['appr'])} vs PRED.waitingOnMe {m['pred']}")
    bad = [o for o in m['taskOwners'] if m['me'] not in o]
    c.ok(not bad, f'{tag}: Tasks holds {len(bad)} task(s) neither owned by nor offered to them')
    held = set(m['held'])
    missing = [t['key'] for t in m['mine'] if t['key'] not in m['tasks'] and not any(r in held for r in t['refs'])]
    c.ok(not missing, f'{tag}: {len(missing)} open task(s) they own are on no filter: {missing[:3]}')
    # each filter's badge equals the rows it shows once opened
    for t in await tabs_of(pg):
        if t['k'] == 'team': continue
        await pg.click(f'.view.on [data-tdytabbtn="{t["k"]}"]'); await pg.wait_for_timeout(300)
        r = await pg.evaluate(ROWS)
        shown = r['cards'] + r['moreIn']
        c.ok(r['tab'] == t['k'] and str(r['count']) == t['n'] and shown == r['count'], f"{tag}: filter {t['k']} says {t['n']}, heading {r['count']}, shows {r['cards']} cards + {r['moreIn']} on the full page")
    await pg.click('.view.on [data-tdytabbtn="all"]'); await pg.wait_for_timeout(200)
    ev = None
    if uid in ('u_owner', 'u_alan', 'u_chen', 'u_billing', 'u_controller'):
        await go(pg, 'mapprove'); await pg.wait_for_timeout(250)
        ev = await pg.evaluate("() => { const b = document.querySelector('#mappr-tabs [data-mak=\"all\"] .n'); return b ? +b.innerText : null; }")
        c.ok(ev is None or ev == len(m['appr']), f"{tag}: the Approvals page's Everything {ev} vs Today's Approvals {len(m['appr'])}")
    if tag in ('owner', 'pm'):
        c.ok(m['team'] is not None, f'{tag}: a manager has Team')
    else:
        c.ok(m['team'] is None, f'{tag}: Team is for managers only')
    print(f"{tag}: approvals {len(m['appr'])}, inbox {len(m['inbox'])}, tasks {len(m['tasks'])}, all {len(m['all'])}")


SOURCES = """() => {
  const td = today(), a = [];
  // schedule: a job to-do on 121 State Street
  a.push(['schedule', crCreateTask({ title: 'Lane src schedule: confirm the stair layout', for: 'p:p121', assignee: 'Alan', due: td })]);
  // office: a firm to-do
  a.push(['office', crCreateTask({ title: 'Lane src office: renew the parking permit', for: 'firm', assignee: 'Alan', due: td })]);
  // sales: a sales to-do
  a.push(['sales', crCreateTask({ title: 'Lane src sales: call the Ortiz referral', for: 'sales', assignee: 'Alan', due: td })]);
  // the assistant: a reminder it keeps for Alan, and a follow-up it drafted for him (an approval)
  const n = eaAddNote('Alan: Lane src assistant: send the lighting cut sheets', td, 'Alan');
  DB.outbox = DB.outbox || [];
  DB.outbox.push({ id: 'oxLane1', kind: 'order-followup', to: { name: 'Nemo Tile', email: '' }, subject: 'Lane src draft: confirm the tile ship date', body: 'Hi', about: { label: 'PO-2026-041 · Confirm' }, aboutKey: 'tk|x|confirm', forName: 'Alan', status: 'draft', at: td, by: 'assistant' });
  // an obligation owned by Alan, inside its renewal lead (it is the PM's renewal to file)
  DB.obligations.push({ id: 'obLane1', kind: 'license', name: 'Lane src obligation: home improvement license', party: 'DCWP', number: 'HIC-1', covers: ['company'], starts: '2024-10-01', expires: iso(addDays(td, 12)), renewLead: 30, owner: 'Alan', amount: 0, notes: '', docs: [], status: 'active', at: td });
  save(); return a.map(([s, m]) => [s, m && m.id]).concat([['note', n.id]]); }"""


async def five_sources(c, pg):
    await sign_in(pg, 'u_alan')
    await pg.evaluate(SOURCES)
    await go(pg, 'home'); await pg.wait_for_timeout(300)
    r = await pg.evaluate("""() => { const M = tdyModel(), find = (re) => M.all.filter(it => re.test(String(it.title || ''))).map(it => ({ kind: it.kind, src: it.t ? it.t.sourceLabel : it.kind, owner: it.t ? it.t.owner : '' }));
      return { schedule: find(/Lane src schedule/), office: find(/Lane src office/), sales: find(/Lane src sales/), assistant: find(/Lane src assistant/),
               draft: find(/Lane src draft/), obligation: find(/Lane src obligation|home improvement license/i),
               owners: [...new Set(tkAll({ open: true }).map(t => t.owner))], noOwner: tkAll({ open: true }).filter(t => !t.owner || /^(office|smartdesigns?|studio)$/i.test(t.owner)).map(t => t.title) }; }""")
    want = {'schedule': 'Project', 'office': 'Office', 'sales': 'Sales', 'assistant': 'Assistant'}
    for k, lab in want.items():
        c.ok(len(r[k]) == 1 and r[k][0]['src'].startswith(lab) and r[k][0]['owner'] == 'Alan', f'source {k}: on Alan\'s Today once, from {lab}: {r[k]}')
    c.ok(len(r['draft']) == 1 and r['draft'][0]['kind'] == 'draft', f"source assistant draft: once, as the approval it is: {r['draft']}")
    c.ok(len(r['obligation']) == 1, f"source obligation: once on Alan's Today (its renewal and its task are one item): {r['obligation']}")
    c.ok(not r['noOwner'], f"every task has a person as its owner: {r['noOwner'][:4]}")
    # the source link opens the record
    for k, view_re in (('schedule', r'^(tasks|sched|proj)$|editor'), ('sales', r'^tkall$'), ('office', r'^(home|tkall)$')):
        got = await pg.evaluate("""re => { const t = tkAll({ open: true }).find(x => new RegExp(re).test(x.title)); if (!t) return null;
          view = 'home'; render(); try { editing = null; } catch (e) {} tdyOpenSource(t); return [view, !!document.querySelector('.drawer.on, #editor.on, .editor.on'), (S || {}).id || '']; }""", f'Lane src {k}')
        c.ok(got and (re.search(view_re, got[0]) or got[1]), f'source {k}: its link opens the record ({got})')
    # the task's sheet names where it came from
    await go(pg, 'home'); await pg.wait_for_timeout(200)
    sh = await pg.evaluate("""() => { const t = tkAll({ open: true }).find(x => /Lane src schedule/.test(x.title)); tdyTaskSheet(t);
      const m = document.getElementById('mbm'); const s = m ? m.innerText : ''; mbCloseModal(); return s; }""")
    c.ok('From' in sh and '121 State Street' in sh and 'Owner' in sh, f'the task sheet names its source and owner: {sh[:160]!r}')


async def handoffs(c, pg):
    await sign_in(pg, 'u_owner')
    await pg.evaluate("() => { crCreateTask({ title: 'Lane handoff: collect the DOB filing receipt', for: 'me', assignee: 'Owner', due: today() }); save(); }")
    t = "() => tkAll({ open: true }).find(x => /Lane handoff/.test(x.title))"
    await pg.evaluate(f"() => {{ const t = ({t})(); tdyHandOff(t, 'Chen Biron', 'you have the DOB login'); }}")
    toast = await pg.evaluate("() => { const t = document.getElementById('toast'); return { text: t.innerText, open: !!t.querySelector('a') }; }")
    c.ok('Offered to Chen' in toast['text'] and toast['open'], f'hand-off: the toast says what happened, with Open: {toast}')
    x = await pg.evaluate(t)
    c.ok(x['owner'] == 'Owner' and x['offeredTo'] == 'Chen Biron' and x['status'] == 'offered', f"hand-off: until Chen accepts, the Owner still owns it ({x['owner']}, offered to {x['offeredTo']}, {x['status']})")
    await go(pg, 'home'); await pg.wait_for_timeout(250)
    on_owner = await pg.evaluate("() => tdyModel().tasks.some(it => /Lane handoff/.test(it.title))")
    await sign_in(pg, 'u_chen'); await go(pg, 'home'); await pg.wait_for_timeout(250)
    card = await pg.evaluate("""() => { const i = tdyModel().tasks.findIndex(it => /Lane handoff/.test(it.title)); if (i < 0) return null;
      const c = tdCard(tdyModel().tasks[i]); return { verb: c.verb, why: c.why }; }""")
    c.ok(on_owner and card and card['verb'] == 'Accept', f'hand-off: on both lists (Owner {on_owner}; Chen {card})')
    no = await pg.evaluate(f"() => tdyDecline(({t})(), '')")
    c.ok(no is False, 'hand-off: a decline with no reason is refused')
    await pg.evaluate(f"() => tdyDecline(({t})(), 'Not mine: Alan files with DOB')")
    x = await pg.evaluate(t)
    c.ok(x['owner'] == 'Owner' and x['handoff']['state'] == 'declined' and 'Alan files' in x['handoff']['reason'], f"hand-off: a decline comes back with its reason ({x['owner']}, {x['handoff']})")
    on_chen = await pg.evaluate("() => tdyModel().tasks.some(it => /Lane handoff/.test(it.title))")
    c.ok(not on_chen, 'hand-off: a declined task leaves the decliner\'s list')
    await sign_in(pg, 'u_owner'); await go(pg, 'home'); await pg.wait_for_timeout(200)
    card = await pg.evaluate("() => { const it = tdyModel().tasks.find(it => /Lane handoff/.test(it.title)); return it ? tdCard(it) : null; }")
    c.ok(card and 'declined' in card['why'] and card['verb'] == 'Hand Off', f"hand-off: the Owner sees the decline and its reason, with Hand Off: {card and (card['why'], card['verb'])}")
    await pg.evaluate(f"() => tdyHandOff(({t})(), 'Chen Biron', 'second try')")
    await sign_in(pg, 'u_chen')
    await pg.evaluate(f"() => tdyAccept(({t})())")
    x = await pg.evaluate(t)
    c.ok(x['owner'] == 'Chen Biron' and x['handoff']['state'] == 'accepted', f"hand-off: once accepted, it is Chen's ({x['owner']}, {x['handoff']['state']})")
    log = await pg.evaluate(f"() => (tdyRec(({t})().row).handoffs || []).map(e => e.ev)")
    c.ok(log == ['offered', 'declined', 'offered', 'accepted'], f'hand-off: the log keeps every step: {log}')
    await sign_in(pg, 'u_owner')
    gone = await pg.evaluate("() => !tdyModel().tasks.some(it => /Lane handoff/.test(it.title))")
    c.ok(gone, "hand-off: accepted, it leaves the Owner's list")
    # a new task assigned to someone else is a hand-off from the start (New Task, the one creation path)
    await go(pg, 'home'); await pg.wait_for_timeout(200)
    await pg.evaluate("() => newTaskDialog({ title: 'Lane new: order the stair runner samples' })"); await pg.wait_for_timeout(200)
    await pg.evaluate("() => { const s = document.querySelector('#mbm [data-f=\"assignee\"]'); s.value = [...s.options].find(o => /Chen/.test(o.value)).value; document.querySelector('#mbm #mbm-ok').click(); }")
    await pg.wait_for_timeout(400)
    toast = await pg.evaluate("() => document.getElementById('toast').innerText")
    x = await pg.evaluate("() => tkAll({ open: true }).find(x => /Lane new: order the stair/.test(x.title))")
    c.ok(x and x['owner'] == 'Owner' and x['offeredTo'] == 'Chen Biron' and 'Offered to Chen' in toast, f"hand-off: New Task for Chen is offered, the Owner owns it until he accepts ({x and (x['owner'], x['offeredTo'])}; {toast[:90]!r})")


RECUR = """() => { const all = (DB.projects || []).flatMap(p => p.actions || []).concat(DB.tasks || []).filter(a => a && a.recur);
  const keys = all.map(a => a.recur.key); return { n: all.length, uniq: new Set(keys).size, keys: keys,
    owners: Object.fromEntries(all.map(a => [a.recur.key, a.assignee])) }; }"""


async def recurring(c, pg):
    await sign_in(pg, 'u_owner')
    r0 = await pg.evaluate(RECUR)
    duties = set(k.split(':')[0] for k in r0['keys'])
    c.ok({'friday', 'walk', 'huddle', 'books'} <= duties, f'recurring: the duties due this week were created at boot: {sorted(duties)}')
    own = r0['owners']
    fr = [v for k, v in own.items() if k.startswith('friday:p121')]
    c.ok(fr == ['Alan'], f"recurring: 121 State's Friday client update is the PM's: {fr}")
    c.ok(all(v == 'Angel' for k, v in own.items() if k.startswith('huddle:')), f"recurring: the morning huddle is the foreman's: {[v for k, v in own.items() if k.startswith('huddle:')]}")
    c.ok([v for k, v in own.items() if k.startswith('books:')] == ['Controller'], f"recurring: the books by the 10th are the controller's: {[v for k, v in own.items() if k.startswith('books:')]}")
    # a delivery five working days out and a certificate expiring in 20 days
    await pg.evaluate("""() => { const po = DB.pos.find(p => p.number === 'PO-2026-048'); po.expected = addWork(today(), 3);
      const v = DB.vendors.find(x => x.name === 'Nemo Tile'); v.insuranceExp = iso(addDays(today(), 20)); save(); }""")
    await pg.evaluate("() => { tdyRecurSweep(); tdyRecurSweep(); }")
    r1 = await pg.evaluate(RECUR)
    c.ok(r1['n'] == r1['uniq'], f"recurring: two sweeps made no duplicate ({r1['n']} tasks, {r1['uniq']} keys)")
    dl = [v for k, v in r1['owners'].items() if k.startswith('delivery:')]
    ci = [v for k, v in r1['owners'].items() if k.startswith('coi:')]
    c.ok(dl == ['Chen Biron'], f"recurring: the delivery is reconfirmed 48 hours ahead by the coordinator: {dl}")
    c.ok(ci == ['Chen Biron'], f"recurring: the insurance renewal 30 days ahead is the coordinator's: {ci}")
    due = await pg.evaluate("() => { const a = DB.tasks.find(x => x.recur && x.recur.duty === 'delivery'); const po = DB.pos.find(p => p.number === 'PO-2026-048'); return [a && a.due, addWork(po.expected, -2)]; }")
    c.ok(due[0] == due[1], f'recurring: the reconfirm is due two working days before the delivery: {due}')
    # the next day: a new huddle, the same Friday update; and back
    await pg.evaluate("() => appSetDay('2026-09-04')")
    r2 = await pg.evaluate(RECUR)
    c.ok(r2['n'] == r2['uniq'] and any(k.startswith('huddle:') and k.endswith('2026-09-04') for k in r2['keys']) and sum(k.startswith('friday:p121') for k in r2['keys']) == 1,
         f"recurring: a day turn adds the day's huddle and keeps one Friday update ({r2['n']} tasks)")
    await pg.evaluate("() => appSetDay('2026-09-03')")
    # a reload does not make them again
    await pg.evaluate("async () => { await saveNow(); }")
    await pg.reload(); await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
    r3 = await pg.evaluate(RECUR)
    c.ok(r3['n'] == r3['uniq'] and r3['n'] >= r2['n'], f"recurring: after a reload, {r3['n']} tasks, {r3['uniq']} keys")
    # the Standard line it rests on
    why = await pg.evaluate("() => { const t = tkAll({ open: true }).find(x => x.recur && x.recur.duty === 'friday'); return t ? standardWhy(tdyTaskItem(t)) : ''; }")
    c.ok('Friday' in why, f'recurring: the Friday update names the Standard line behind it: {why!r}')


async def proof(c, pg):
    await sign_in(pg, 'u_chen'); await go(pg, 'home'); await pg.wait_for_timeout(200)
    # an inspection: completing asks for the result, and only a pass closes it
    r = await pg.evaluate("""async () => { const t = tkAll({ open: true }).find(x => /Rough inspection/.test(x.title)); tkToggle(t.kind, t.id, t.projectId);
      await new Promise(r => setTimeout(r, 120)); const m = document.getElementById('mbm');
      return { sheet: m ? m.innerText : '', done: (tdyRec(t.row) || {}).status }; }""")
    c.ok('Proof Needed' in r['sheet'] and 'Inspect before you close' in r['sheet'] and r['done'] != 'done', f"proof: closing the rough inspection asks for the result ({r['done']}; {r['sheet'][:120]!r})")
    await pg.evaluate("() => { document.querySelector('#mbm [data-f=\"result\"]').value = 'passed'; document.querySelector('#mbm #mbm-ok').click(); }")
    await pg.wait_for_timeout(250)
    st = await pg.evaluate("() => { const p = DB.projects.find(x => x.id === 'p121'); return [p.tasks.find(t => t.id === 'rinsp').status, (p.tasks.find(t => t.id === 'rinsp').proof || {}).what || '']; }")
    c.ok(st[0] == 'done' and 'passed' in st[1], f'proof: a pass closes it, with the proof on the task: {st}')
    # photos before a wall closes: refused without, done with
    await sign_in(pg, 'u_alan')
    await pg.evaluate("() => { crCreateTask({ title: 'Lane proof: close the garden bedroom walls', for: 'p:p121', assignee: 'Alan', due: today() }); save(); }")
    r = await pg.evaluate("""async () => { const t = tkAll({ open: true }).find(x => /Lane proof: close/.test(x.title)); tkToggle(t.kind, t.id, t.projectId);
      await new Promise(r => setTimeout(r, 120)); const m = document.getElementById('mbm'); const s = m ? m.innerText : '';
      document.querySelector('#mbm #mbm-ok').click(); await new Promise(r => setTimeout(r, 120));
      return { sheet: s, still: !!document.getElementById('mbm'), status: tdyRec(t.row).status, toast: document.getElementById('toast').innerText }; }""")
    c.ok('Photograph before you cover' in r['sheet'] and r['still'] and r['status'] != 'done', f"proof: a wall closing asks for photos, and Mark Done without one is refused ({r['status']}; {r['toast'][:80]!r})")
    r = await pg.evaluate("""async () => { const keep = mReadPhoto; mReadPhoto = (cb) => cb('data:image/jpeg;base64,/9j/4AAQSkZJRgABAQ');
      document.querySelector('#mbm [data-tdycam]').click(); mReadPhoto = keep; document.querySelector('#mbm #mbm-ok').click(); await new Promise(r => setTimeout(r, 150));
      const p = DB.projects.find(x => x.id === 'p121'), a = p.actions.find(x => /Lane proof: close/.test(x.title));
      return { status: a.status, photos: p.files.filter(f => f.link && f.link.id === a.id).length, toast: document.getElementById('toast').innerText }; }""")
    c.ok(r['status'] == 'done' and r['photos'] == 1 and 'Done' in r['toast'], f'proof: with the photo it is done, the photo on the job: {r}')
    # extra work: no signed change order, no done
    await pg.evaluate("() => { crCreateTask({ title: 'Lane proof: extra work, reframe the stair opening', for: 'p:p121', assignee: 'Alan', due: today() }); save(); }")
    r = await pg.evaluate("""async () => { const t = tkAll({ open: true }).find(x => /Lane proof: extra/.test(x.title)); tkToggle(t.kind, t.id, t.projectId);
      await new Promise(r => setTimeout(r, 120)); const m = document.getElementById('mbm'); const s = m ? m.innerText : '';
      document.querySelector('#mbm #mbm-ok').click(); await new Promise(r => setTimeout(r, 120));
      return { sheet: s, still: !!document.getElementById('mbm'), status: tdyRec(t.row).status }; }""")
    c.ok('No extra work without a signed change order' in r['sheet'] and 'CO-2026-002 is sent' in r['sheet'] and r['still'] and r['status'] != 'done', f"proof: extra work waits for the signed change order that covers it ({r['status']}; {r['sheet'][:160]!r})")
    r = await pg.evaluate("""async () => { const s = document.querySelector('#mbm [data-f="co"]'); s.value = [...s.options].find(o => /CO-2026-001/.test(o.text)).value;
      document.querySelector('#mbm #mbm-ok').click(); await new Promise(r => setTimeout(r, 150));
      const a = DB.projects.find(x => x.id === 'p121').actions.find(x => /Lane proof: extra/.test(x.title)); return [a.status, (a.proof || {}).what || '']; }""")
    c.ok(r[0] == 'done' and 'CO-2026-001' in r[1], f'proof: named, the signed change order closes it: {r}')
    # a task with no proof in the Standard closes at once
    await pg.evaluate("() => { crCreateTask({ title: 'Lane proof: send the meeting recap', for: 'me', assignee: 'Alan', due: today() }); save(); }")
    r = await pg.evaluate("""async () => { const t = tkAll({ open: true }).find(x => /Lane proof: send/.test(x.title)); tdyDone(t); await new Promise(r => setTimeout(r, 100));
      return { status: tdyRec(t.row).status, sheet: !!document.getElementById('mbm') }; }""")
    c.ok(r['status'] == 'done' and not r['sheet'], f'proof: an ordinary task closes in one tap: {r}')


async def ask_and_query(c, pg):
    await sign_in(pg, 'u_owner')
    a = await pg.evaluate("""async () => { let a = paAsk('what does Angel owe this week'); if (a && a.then) a = await a;
      const to = appWeek().sun, L = tdyOwed('Angel', to); return { h: a.headline || '', n: L.length, titles: L.map(x => x.title) }; }""")
    c.ok(a['n'] > 0 and a['h'].startswith(str(a['n'])) and all(t[:20] in a['h'] for t in a['titles'][:2]), f"Ask: \"what does Angel owe this week\" -> {a['h'][:140]!r} ({a['n']} in the accessor)")
    q = await pg.evaluate("""() => { const R = erpQuery({ entity: 'tasks', limit: 200 }).rows; return { n: R.length, owners: [...new Set(R.filter(r => !r.done).map(r => r.owner))], hasShape: R.length && 'owner' in R[0] && 'sourceType' in R[0] && 'handoffState' in R[0],
      n2: tkItems().length }; }""")
    c.ok(q['hasShape'] and q['n'] == q['n2'], f"erpQuery tasks: the one shape (owner, source, hand-off), {q['n']} rows = tkItems {q['n2']}")
    c.ok(not [o for o in q['owners'] if not o or re.match(r'(?i)^(office|smartdesigns?|studio)$', o)], f"erpQuery tasks: every open task's owner is a person: {q['owners']}")
    f = await pg.evaluate("""async () => { let a = paAsk('what should I do first'); if (a && a.then) a = await a; const top = myQueueSay(myQueue()[0]).t; return [a.headline || '', top]; }""")
    c.ok(f[1][:24] in f[0], f'Ask "what should I do first" starts where Today does: {f}')


async def phone(c, p):
    b, pg, errs = await open_app(p, True)
    for uid, tag in OFFICE:
        await sign_in(pg, uid); await go(pg, 'home'); await pg.wait_for_timeout(300)
        for k in ('all', 'tasks', 'appr'):
            if not await pg.locator(f'.view.on [data-tdytabbtn="{k}"]').count(): continue
            await pg.click(f'.view.on [data-tdytabbtn="{k}"]'); await pg.wait_for_timeout(250)
            m = await pg.evaluate("""() => { const vis = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
              const tabs = [...document.querySelectorAll('.view.on [data-tdytabbtn]')].filter(vis).map(b => b.getBoundingClientRect());
              const verbs = [...document.querySelectorAll('.view.on .td-do .td-verb')].filter(vis).map(b => b.getBoundingClientRect());
              const gaps = []; tabs.forEach((a, i) => tabs.forEach((b, j) => { if (j <= i) return;
                const dx = Math.max(b.left - a.right, a.left - b.right), dy = Math.max(b.top - a.bottom, a.top - b.bottom); gaps.push(Math.max(dx, dy)); }));
              const prim = [...document.querySelectorAll('.view.on .btn.primary')].filter(vis).length;
              return { sw: document.documentElement.scrollWidth, tabH: Math.min(...tabs.map(r => r.height)), verbH: verbs.length ? Math.min(...verbs.map(r => r.height)) : 99,
                       gap: gaps.length ? Math.min(...gaps) : 99, prim }; }""")
            c.ok(m['sw'] <= 390, f'{tag} phone {k}: no sideways scroll ({m["sw"]})')
            c.ok(m['tabH'] >= 40 and m['verbH'] >= 40, f'{tag} phone {k}: filters {m["tabH"]}px and verbs {m["verbH"]}px tall, want 40 or more')
            c.ok(m['gap'] >= 8, f'{tag} phone {k}: filters {m["gap"]}px apart, want 8 or more')
            c.ok(m['prim'] <= 1, f'{tag} phone {k}: {m["prim"]} blue buttons')
        await pg.click('.view.on [data-tdytabbtn="all"]'); await pg.wait_for_timeout(150)
        if tag == 'owner':
            rail = await pg.evaluate("() => { const b = document.querySelector('#mtabs button[data-mv=\"mapprove\"] .n, #mtabs button[data-mv=\"mapprove\"] i.n'); return b ? +b.innerText : null; }")
            n = await pg.evaluate("() => +(document.querySelector('.view.on [data-tdytabbtn=\"appr\"] .n') || {}).innerText")
            c.ok(rail is None or rail == n, f'owner phone: the Approvals tab badge {rail} = the Approvals filter {n}')
    c.ok(not errs, f'phone: page errors {errs[:3]}')
    await b.close()


async def main():
    c = Checks()
    async with async_playwright() as p:
        b, pg, errs = await open_app(p, False)
        for uid, tag in OFFICE:
            await union_and_counts(c, pg, uid, tag)
        await five_sources(c, pg)
        await handoffs(c, pg)
        await ask_and_query(c, pg)
        c.ok(not errs, f'desktop: page errors {errs[:3]}')
        await b.close()
        b, pg, errs = await open_app(p, False)
        await recurring(c, pg)
        await proof(c, pg)
        c.ok(not errs, f'recurring and proof: page errors {errs[:3]}')
        await b.close()
        await phone(c, p)
    sys.exit(c.done())

asyncio.run(main())
