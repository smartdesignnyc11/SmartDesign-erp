"""Your Day: Today, Tasks and Messages as the approved mock-up draws them (docs/mockups/today/SPEC.md, the chief of
staff's must-fix list in section 8, BACKLOG section 10 items 6 and 7). Done as the person, on the phone and the desktop:
the owner, the PM, the coordinator and billing open each page from the menu and read what it says.

Today    the brief at the top (Safe to Spend read through safeToSpend(), the job slipping, the client waiting), then
         Approvals (the owner's: exceptions only, AMP-311 among them, no lessons), then Now; chips Today, Approvals,
         Coming Up; one number on the menu, the date line, the Today chip and the rows; Where the Firm Stands one tap.
         Every message Messages counts as the person's, every late or today task of theirs, and every deal the
         Pipeline says needs them is a row on their Today (section 10 item 7).
Tasks    one list opening on Mine; chips Mine, Waiting On and Team (grouped by person, no load figures, everyone else
         named at the foot); List, Table, Board and Calendar as one switch; the desktop opens on Table with the nine
         10-26 columns and click-to-sort; the old Calendar page is the Calendar view.
Messages one list opening on Needs an Answer, oldest first; All and Meetings one tap; it replaces the Inbox and
         Meetings; the menu's Messages number equals the chip and the rows.
Old pages forward to their new homes: Approvals, the Inbox, Meetings, the Calendar."""
import asyncio, re, sys
from playwright.async_api import async_playwright
from harness import open_app, sign_in, go, Checks
from ydcheck import MENU_N, CHIPS, phone_fit

c = Checks()
ROLES = ['u_owner', 'u_alan', 'u_chen', 'u_billing']

TODAY = """() => {
  const chips = [...document.querySelectorAll('.view.on [data-tdytabbtn]')].filter(b => b.getClientRects().length).map(b => ({ k: b.dataset.tdytabbtn,
     label: b.childNodes[0].textContent.trim(), n: +((b.querySelector('.n') || {}).textContent || 0), on: b.classList.contains('on') }));
  const rows = [...document.querySelectorAll('.view.on .td-do .td-card')].filter(e => e.getClientRects().length).map(e => ({ kind: e.dataset.kind, id: e.dataset.id, text: e.innerText }));
  const more = document.querySelector('.view.on .td2-more'), mm = more && /^(\\d+) more$/.exec(more.textContent.trim());
  const secs = [...document.querySelectorAll('.view.on .td2-sh h2')].map(h => h.textContent.trim());
  const date = (document.querySelector('.view.on .td2-date') || document.getElementById('td2-hdate') || {}).textContent || '';
  const cash = document.querySelector('.view.on [data-ydsafe]');
  const firm = document.querySelector('.view.on [data-ydfirm]');
  return { chips, rows, more: mm ? +mm[1] : 0, secs, date: date.trim(), cash: cash ? cash.dataset.ydsafe : null, firm: !!firm,
    brief: ((document.querySelector('.view.on .td2-brief') || {}).innerText || '') }; }"""


async def today_as(p, uid, phone):
    who = f'{uid} {"phone" if phone else "desktop"}'
    b, pg, errs = await open_app(p, phone)
    await sign_in(pg, uid)
    await go(pg, 'home')
    m = await pg.evaluate(TODAY)
    labels = [x['label'] for x in m['chips']]
    c.ok(labels == ['Today', 'Approvals', 'Coming Up'], f'{who}: Today chips {labels}, want Today, Approvals, Coming Up')
    on = [x['label'] for x in m['chips'] if x['on']]
    c.ok(on == ['Today'], f'{who}: Today opens on {on}, want Today')
    today_n = next((x['n'] for x in m['chips'] if x['label'] == 'Today'), None)
    shown = len(m['rows']) + m['more']
    c.ok(today_n == shown, f'{who}: the Today chip says {today_n}, the page shows {shown} rows')
    badge = await pg.evaluate(MENU_N, 'home')
    c.ok((badge or '0') == str(today_n), f'{who}: the menu says Today {badge!r}, the chip {today_n}')
    c.ok(re.search(rf'\b{today_n} need you today\b', m['date'] or ''), f'{who}: the date line {m["date"]!r} does not say {today_n} need you today')
    secs = [s for s in m['secs'] if s in ('Approvals', 'Now')]
    c.ok(secs and secs[0] == ('Approvals' if 'Approvals' in secs else 'Now'), f'{who}: sections {m["secs"]}, want Approvals first, then Now')
    c.ok(m['firm'], f'{who}: no Where the Firm Stands one tap down')
    # each chip says the rows it opens
    for k in ('appr', 'coming'):
        await pg.evaluate("k => { const b = document.querySelector('.view.on [data-tdytabbtn=\"' + k + '\"]'); b && b.click(); }", k)
        await pg.wait_for_timeout(150)
        mk = await pg.evaluate(TODAY)
        ch = next((x for x in mk['chips'] if x['k'] == k), None)
        c.ok(ch and ch['on'] and ch['n'] == len(mk['rows']) + mk['more'], f'{who}: chip {k} says {ch and ch["n"]}, shows {len(mk["rows"]) + mk["more"]}')
    await pg.evaluate("() => { const b = document.querySelector('.view.on [data-tdytabbtn=\"today\"]'); b && b.click(); }")
    await pg.wait_for_timeout(120)
    # open the fold so every row is read
    await pg.evaluate("() => { const a = document.querySelector('.view.on .td2-more'); a && /more$/.test(a.textContent) && a.click(); }")
    await pg.wait_for_timeout(150)
    m = await pg.evaluate(TODAY)
    ids = {(x['kind'], x['id']) for x in m['rows']}
    text = ' '.join(x['text'] for x in m['rows'])
    # section 10 item 7: everything that waits on this person elsewhere is a row here
    need = await pg.evaluate("() => (typeof ydMsgNeeds === 'function' ? ydMsgNeeds() : (typeof cmNeedsAnswer === 'function' ? cmNeedsAnswer().map(c => ({kind: 'tdyMail', id: c.id})) : [])).map(x => [x.kind, String(x.id)])")
    miss = [i for k, i in need if (k, i) not in ids]
    c.ok(not miss, f'{who}: {len(miss)} of the {len(need)} messages Messages counts as yours are not on Today')
    # a late or today task is on Today as its own row, or as the row that stands for it (an obligation's renewal)
    tmiss = await pg.evaluate("""() => { const td = today(); const rows = (td2Cur && td2Cur.T.rows) || [];
      const keys = new Set(rows.filter(x => x.it.kind === 'tdyTask').map(x => x.it.id)), held = new Set(rows.flatMap(x => { try { return tdyApprRefs(x.it); } catch (e) { return []; } }));
      try { return openTasks('me').filter(t => t.due && t.due <= td).map(t => tdyShape(t)).filter(s => !keys.has(s.key) && !(s.refs || []).some(r => held.has(r))).map(s => s.key); } catch (e) { return ['error ' + e]; } }""")
    c.ok(not tmiss, f'{who}: late or today tasks not on Today: {tmiss[:3]}')
    if uid == 'u_owner':
        deals = await pg.evaluate("() => typeof slNeedYou === 'function' ? slNeedYou().map(x => x.l.id) : null")
        c.ok(deals is not None, f'{who}: the Pipeline has no Need You reader (slNeedYou)')
        for d in deals or []:
            lead_task = any(k == 'tdyTask' and (i.endswith(':' + d) or d in i) for k, i in ids)
            c.ok(('ydDeal', d) in ids or lead_task or await pg.evaluate("d => slNeedYou().find(x => x.l.id === d).taskKeys.some(k => document.querySelector('.view.on .td-card[data-id=\"' + k + '\"]'))", d),
                 f'{who}: the Pipeline deal {d} that needs you is not on Today')
        c.ok('Nakamura' in text and 'Set Up the Job' in text, f'{who}: the Nakamuras (signed, no job) are not a Set Up the Job row on Today')
        # section 10 item 6: the owner's Approvals is the 10-26 exceptions, AMP-311 among them, and no lessons
        await pg.evaluate("() => { const b = document.querySelector('.view.on [data-tdytabbtn=\"appr\"]'); b && b.click(); }")
        await pg.wait_for_timeout(150)
        ma = await pg.evaluate(TODAY)
        at = ' '.join(x['text'] for x in ma['rows'])
        c.ok('AMP-311' in at, f'{who}: AMP-311 ($9,800, no PO) is not on the owner\'s Approvals')
        c.ok(not re.search(r'Lesson:|rule the brain proposes', at) and not any(x['kind'] in ('lesson', 'learn', 'change') for x in ma['rows']),
             f'{who}: lessons or rule changes still on Approvals (they belong to The Brain)')
        c.ok(len(ma['rows']) + ma['more'] <= 8, f'{who}: {len(ma["rows"]) + ma["more"]} approvals; exceptions only should be a handful')
        await pg.evaluate("() => { const b = document.querySelector('.view.on [data-tdytabbtn=\"today\"]'); b && b.click(); }")
        await pg.wait_for_timeout(120)
        # the brief: Safe to Spend read through the app's one function
        want = await pg.evaluate("() => String(Math.round(safeToSpend().safe))")
        c.ok(m['cash'] is not None and str(round(float(m['cash']))) == want, f'{who}: the brief\'s Safe to Spend {m["cash"]!r}, the app\'s one function says {want}')
        c.ok('slipping' in m['brief'], f'{who}: the brief does not name the job that is slipping: {m["brief"][:200]!r}')
    if phone:
        await phone_fit(c, pg, f'{who} Today')
    c.ok(not errs, f'{who} Today: errors {errs[:2]}')
    await b.close()


MSGS = """() => { const h = document.getElementById('yd-chat');
  const chips = [...document.querySelectorAll('#yd-chat [data-ydchip]')].map(b => ({ k: b.dataset.ydchip, label: b.childNodes[0].textContent.trim(), n: ((b.querySelector('.n') || {}).textContent || '').trim(), on: b.classList.contains('on') }));
  const rows = [...document.querySelectorAll('#yd-chat [data-ydmrow]')].filter(e => e.getClientRects().length).map(e => ({ id: e.dataset.ydmrow, at: e.dataset.at || '', text: e.innerText }));
  return { on: !!(h && h.getClientRects().length), chips, rows }; }"""


async def messages_as(p, uid, phone):
    who = f'{uid} {"phone" if phone else "desktop"}'
    b, pg, errs = await open_app(p, phone)
    await sign_in(pg, uid)
    await go(pg, 'chat')
    m = await pg.evaluate(MSGS)
    c.ok(m['on'], f'{who}: Messages is not the one list (#yd-chat)')
    labels = [x['label'] for x in m['chips']]
    c.ok(labels == ['Needs an Answer', 'All', 'Meetings'], f'{who}: Messages chips {labels}')
    on = [x['label'] for x in m['chips'] if x['on']]
    c.ok(on == ['Needs an Answer'], f'{who}: Messages opens on {on}')
    need = await pg.evaluate("() => typeof ydMsgNeeds === 'function' ? ydMsgNeeds().length : cmNeedsAnswer().length")
    n = next((x['n'] for x in m['chips'] if x['k'] == 'need'), '')
    c.ok(str(need) == (n or '0') and len(m['rows']) == need, f'{who}: Needs an Answer chip {n!r}, rows {len(m["rows"])}, the rule {need}')
    badge = await pg.evaluate(MENU_N, 'chat')
    c.ok((badge or '0') == str(need), f'{who}: the menu says Messages {badge!r}, Needs an Answer {need}')
    ats = [x['at'] for x in m['rows']]
    c.ok(ats == sorted(ats), f'{who}: Needs an Answer is not oldest first: {ats}')
    if uid == 'u_owner':
        text = ' '.join(x['text'] for x in m['rows'])
        for name in ('Torres', 'Aliya Chen', 'Sarah Klein', 'Jeanette', 'Samantha Field'):
            c.ok(name in text, f'{who}: {name} waits on the owner and is not in Needs an Answer')
        for k in ('all', 'meet'):
            await pg.evaluate("k => document.querySelector('#yd-chat [data-ydchip=\"' + k + '\"]').click()", k)
            await pg.wait_for_timeout(150)
            mk = await pg.evaluate(MSGS)
            c.ok(mk['rows'], f'{who}: Messages {k} shows no rows')
        mk = await pg.evaluate(MSGS)
        c.ok(any('Notes' in x['text'] or 'Meeting' in x['text'] or 'Schedule Review' in x['text'] for x in mk['rows']), f'{who}: Meetings shows no meeting notes')
    # the old pages forward here
    for old, chip in (('comms', 'need'), ('meetings', 'meet')):
        await pg.evaluate("v => { cmOpen = null; setView(v); }", old)
        await pg.wait_for_timeout(150)
        st = await pg.evaluate("() => [view, (document.querySelector('#yd-chat [data-ydchip].on') || {}).dataset ? document.querySelector('#yd-chat [data-ydchip].on').dataset.ydchip : '']")
        c.ok(st == ['chat', chip], f'{who}: {old} lands on {st}, want Messages {chip}')
    if phone:
        await go(pg, 'chat')
        await phone_fit(c, pg, f'{who} Messages')
    c.ok(not errs, f'{who} Messages: errors {errs[:2]}')
    await b.close()


TASKS = """() => {
  const chips = [...document.querySelectorAll('#tkall-body [data-tvview], #tkall-body [data-ydchip]')].filter(b => b.getClientRects().length).map(b => ({ k: b.dataset.tvview || b.dataset.ydchip,
     label: b.childNodes[0].textContent.trim(), n: ((b.querySelector('.n') || {}).textContent || '').trim(), on: b.classList.contains('on') }));
  const modes = [...document.querySelectorAll('#tkall-body [data-tkmode]')].filter(b => b.getClientRects().length).map(b => b.textContent.trim());
  const cols = [...document.querySelectorAll('#tkall-body [role=columnheader]')].filter(e => e.getClientRects().length).map(e => e.innerText.trim().toUpperCase()).filter(Boolean);
  return { chips, modes, mode: tkMode, cols }; }"""


async def tasks_as(p, uid, phone):
    who = f'{uid} {"phone" if phone else "desktop"}'
    b, pg, errs = await open_app(p, phone)
    await sign_in(pg, uid)
    await go(pg, 'tkall')
    m = await pg.evaluate(TASKS)
    labels = [x['label'] for x in m['chips']][:3]
    c.ok(labels == ['Mine', 'Waiting On', 'Team'], f'{who}: Tasks chips {labels}, want Mine, Waiting On, Team')
    on = [x['label'] for x in m['chips'] if x['on']]
    c.ok(on[:1] == ['Mine'], f'{who}: Tasks opens on {on}, want Mine')
    mine = await pg.evaluate("() => openTasks('me').length")
    mn = next((x['n'] for x in m['chips'] if x['label'] == 'Mine'), '')
    c.ok(mn == str(mine), f'{who}: Mine says {mn!r}, the person has {mine} open tasks (one Mine count)')
    if not phone:
        c.ok(m['modes'] == ['List', 'Table', 'Board', 'Calendar'], f'{who}: view switch {m["modes"]}')
        c.ok(m['mode'] == 'table', f'{who}: the desktop opens on {m["mode"]}, want Table')
    if not phone and mine:   # an empty Mine shows the empty line, not a table
        want = ['KEY', 'TASK', 'PROJECT', 'OWNER', 'DUE', 'PRIORITY', 'NEW OR CARRIED', 'STATUS', 'WAITING ON']
        c.ok(all(x in m['cols'] for x in want), f'{who}: Table columns {m["cols"]}')
        # click-to-sort: Due ascending, descending, back
        s = await pg.evaluate("""async () => { const th = document.querySelector('#tkall-body [data-tvsort="due"]');
          if (!th) return null; th.click(); await new Promise(r => setTimeout(r, 150));
          const a = (tvSorts()[0] || {}); return [a.k, a.dir]; }""")
        c.ok(s and s[0] == 'due', f'{who}: clicking Due does not sort by it ({s})')
    # Team: grouped by person, no load figures, everyone else named at the foot (the List's layout; the Table keeps its own)
    await pg.evaluate("() => tkSetMode('cards')"); await pg.wait_for_timeout(150)
    await pg.evaluate("() => { const b = [...document.querySelectorAll('#tkall-body [data-tvview], #tkall-body [data-ydchip]')].find(x => /^Team/.test(x.textContent.trim())); b && b.click(); }")
    await pg.wait_for_timeout(200)
    t = await pg.evaluate("""() => { const g = [...document.querySelectorAll('#tkall-body [data-ydteamwho]')].map(e => e.dataset.ydteamwho);
      const foot = (document.querySelector('#tkall-body [data-ydteamfoot]') || {}).innerText || ''; const heads = [...document.querySelectorAll('#tkall-body [data-ydteamwho] .yd-gh')].map(e => e.innerText);
      return { g, foot, heads, n: (typeof ydPeople === 'function' ? ydPeople().length : 0) }; }""")
    c.ok(len(t['g']) >= 2, f'{who}: Team is not grouped by person ({t["g"]})')
    c.ok(not any(re.search(r'\d+ (open|overdue|late)\b', h) for h in t['heads']), f'{who}: Team carries load figures {t["heads"][:3]} (load lives once, on Team)')
    c.ok(t['n'] and str(t['n']) in t['foot'], f'{who}: the Team chip\'s foot does not account for all {t["n"]} people: {t["foot"][:120]!r}')
    # the old Calendar page is the Calendar view
    await pg.evaluate("() => setView('calendar')")
    await pg.wait_for_timeout(200)
    st = await pg.evaluate("() => [view, tkMode]")
    c.ok(st == ['tkall', 'cal'], f'{who}: the old Calendar lands on {st}, want Tasks, Calendar')
    if phone:
        await go(pg, 'tkall')
        await phone_fit(c, pg, f'{who} Tasks')
    c.ok(not errs, f'{who} Tasks: errors {errs[:2]}')
    await b.close()


async def forwards(p):
    b, pg, errs = await open_app(p, False)
    await sign_in(pg, 'u_owner')
    await pg.evaluate("() => setView('mapprove')")
    await pg.wait_for_timeout(150)
    st = await pg.evaluate("() => [view, (document.querySelector('.view.on [data-tdytabbtn].on') || {dataset: {}}).dataset.tdytabbtn]")
    c.ok(st == ['home', 'appr'], f'owner: Approvals lands on {st}, want Today, Approvals chip')
    items = await pg.evaluate("() => (mnBuild('owner').groups || []).filter(g => g.day).map(g => g.n)")
    c.ok(items == ['Today', 'Tasks', 'Messages'], f'owner: Your Day {items}')
    ask = await pg.evaluate("() => !!document.getElementById('tb-ask') && !(mnBuild('owner').groups || []).some(g => g.items.some(i => i.v === 'pa'))")
    c.ok(ask, 'owner: Ask is a menu item or not a header button')
    c.ok(not errs, f'forwards: errors {errs[:2]}')
    await b.close()


async def main():
    only = sys.argv[1:]
    async with async_playwright() as p:
        if not only or 'forwards' in only: await forwards(p)
        for uid in ROLES:
            for phone in (False, True):
                if not only or 'today' in only: await today_as(p, uid, phone)
                if not only or 'messages' in only: await messages_as(p, uid, phone)
                if not only or 'tasks' in only: await tasks_as(p, uid, phone)
    sys.exit(c.done())

asyncio.run(main())
