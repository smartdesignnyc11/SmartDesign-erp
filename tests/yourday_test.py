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
    # a message is on Today as its own row, or as the row that holds it (the bill to enter from it, a hold read from it)
    held = set(await pg.evaluate("""() => { const rows = (td2Cur && td2Cur.T.rows) || [];
      return rows.flatMap(x => { try { return tdyApprRefs(x.it).concat(x.it.nyh && x.it.nyh.commId ? ['comm:' + x.it.nyh.commId] : []); } catch (e) { return []; } })
        .filter(r => /^comm:/.test(r)).map(r => r.slice(5)); }"""))
    miss = [i for k, i in need if (k, i) not in ids and not (k == 'tdyMail' and i in held)]
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
        shown = await pg.evaluate("() => ydMoney0(safeToSpend().safe)")
        c.ok(shown in m['brief'] or shown in (await pg.evaluate("() => (document.querySelector('.view.on [data-ydsafe]') || {}).innerText || ''")), f'{who}: the brief prints Safe to Spend as {shown}, it reads {m["brief"][:60]!r}')
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
    c.ok(labels == ['Needs an Answer', 'To Decide', 'All', 'Meetings'], f'{who}: Messages chips {labels}')
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
    # To Decide is the Inbox's own list (mail with something read from it to apply); a row opens it with its Apply
    await pg.evaluate("() => document.querySelector('#yd-chat [data-ydchip=\"decide\"]').click()")
    await pg.wait_for_timeout(150)
    mk = await pg.evaluate(MSGS)
    dn = await pg.evaluate("() => cmListFor('decide').length")
    n = next((x['n'] for x in mk['chips'] if x['k'] == 'decide'), '')
    c.ok(len(mk['rows']) == dn and (n or '0') == str(dn), f'{who}: To Decide chip {n!r}, rows {len(mk["rows"])}, the Inbox {dn}')
    if dn:
        ap = await pg.evaluate("""async () => { const r = document.querySelector('#yd-chat [data-ydmrow] [data-ydact]'); r.click(); await new Promise(x => setTimeout(x, 200));
          return [view, document.querySelectorAll('.view.on [data-cmapply]').length]; }""")
        c.ok(ap[0] == 'comms' and ap[1] > 0, f'{who}: a To Decide row opens the message with its Apply buttons ({ap})')
        await go(pg, 'chat')
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


APPR_N = """() => { const vis = e => !!e && e.getClientRects().length > 0; const b = [...document.querySelectorAll('.view.on [data-tdytabbtn="appr"] .n')].find(vis); return b ? +b.textContent : null; }"""


# planting a bill as the coordinator enters one: its own PO (received or not, pending or issued), a vendor on file
PLANT = """() => { window.ydPlant = (id, vendor, amt, o) => { o = o || {};
    if (!DB.vendors.some(v => v.name === vendor)) DB.vendors.push(Object.assign({ id: 'v_' + id, name: vendor, email: id + '@example.com', insuranceExp: '2027-06-30', w9: true }, o.vendor || {}));
    const V = DB.vendors.find(v => v.name === vendor); V && !V.w9 && (V.w9 = true);  // its papers are on file
    let po = o.poNumber ? DB.pos.find(x => x.number === o.poNumber) : null;
    if (!po && o.po) { po = { id: 'po_' + id, number: 'PO-T-' + id.toUpperCase(), vendor: vendor, projectId: 'p121', entityId: 'ent1', status: o.poStatus || (o.recv ? 'received' : 'issued'), date: today(),
        lines: [{ id: 'pol_' + id, desc: 'test materials', qty: 1, price: o.po, unit: 'ea', received: o.recv ? 1 : 0 }], tax: 0, shipping: 0, approvals: [] }; DB.pos.push(po); }
    const b = { id: id, vendor: vendor, number: o.number || ('T-' + id.toUpperCase()), date: today(), due: iso(addDays(parse(today()), 14)), entityId: 'ent1', projectId: 'p121', poId: po ? po.id : '',
      cat: 'materials', code: '', lines: [{ id: 'bl_' + id, desc: 'test materials', amount: amt, poLineId: po && po.lines[0] ? po.lines[0].id : '' }], payMethod: 'Check', notes: '',
      status: 'submitted', approvals: [{ t: nowStamp(), by: 'Chen', role: 'coord', action: 'submitted' }], createdBy: 'Chen', terms: 'NET 14' };
    Object.assign(b, o.bill || {}); DB.bills.push(b); save(); return b.id; }; }"""

# each exception, and each thing the Payment Check would hold, with the words its reason carries
CASES = [
    ('xpaid', 'Nemo Tile', 500, {'po': 1000, 'recv': True, 'bill': {'paidBeforeApproval': True}}, 'paid before approval'),
    ('xover', 'Nemo Tile', 120, {'poNumber': 'PO-2026-041'}, 'over its PO'),
    ('xbank', 'Harbor Glass Co', 700, {'po': 1000, 'recv': True, 'vendor': {'bankChangedAt': '2026-08-30'}}, 'bank details changed'),
    ('xnew', 'Kings Stone Supply', 800, {'po': 1000, 'recv': True}, 'first payment'),
    ('xheld', 'Nemo Tile', 300, {'po': 1000, 'recv': True, 'bill': {'onHold': {'state': 'open', 'by': 'Chen', 'why': 'two boxes arrived broken'}}}, 'Held by'),
    ('xdup', 'Nemo Tile', 250, {'po': 1000, 'recv': True, 'number': 'NT-88412'}, ''),
    ('xnorecv', 'Nemo Tile', 400, {'po': 1000, 'recv': False}, 'received'),
]


async def exceptions(p):
    """The chief of staff's probe (11-04), planted as Chen enters bills, approved by the PM as he would: a clean bill is
    Approved, To Pay on the controller's Today; each exception (paid before approval, over its PO, a bank change, a first
    payment to a new vendor) and each bill the Payment Check would hold (held, a duplicate invoice number, a PO that has
    received nothing) is recommended, not approved, and lands on the owner's Approvals with its reason. A pending PO over
    $10,000, and every PO poNeedsApproval sends him, is his; payroll is his."""
    b, pg, errs = await open_app(p, False)
    await sign_in(pg, 'u_chen')
    await pg.evaluate(PLANT)
    await pg.evaluate("() => ydPlant('xclean', 'Nemo Tile', 600, { po: 1000, recv: true })")
    for cid, v, amt, o, _ in CASES:
        await pg.evaluate("([i, v, a, o]) => ydPlant(i, v, a, o)", [cid, v, amt, o])
    # two pending orders: one over $10,000, one under it
    await pg.evaluate("""() => { DB.pos.push({ id: 'po_big', number: 'PO-T-BIG', vendor: 'Nemo Tile', projectId: 'p121', entityId: 'ent1', status: 'pending', date: today(), lines: [{ id: 'pob1', desc: 'stone slabs', qty: 1, price: 12000, unit: 'ea' }], tax: 0, shipping: 0, submittedBy: 'Chen', submittedAt: today(), approvals: [] });
      DB.pos.push({ id: 'po_small', number: 'PO-T-SMALL', vendor: 'Nemo Tile', projectId: 'p121', entityId: 'ent1', status: 'pending', date: today(), lines: [{ id: 'pos1', desc: 'grout', qty: 1, price: 3000, unit: 'ea' }], tax: 0, shipping: 0, submittedBy: 'Chen', submittedAt: today(), approvals: [] }); save(); }""")
    tot = await pg.evaluate("() => DB.bills.filter(b => /^x/.test(b.id)).map(b => [b.id, billTotal(b), ydBillExc(b)])")
    c.ok(all(t[1] > 0 for t in tot), f'every planted bill carries an amount: {[t[:2] for t in tot]}')
    c.ok(not tot[0][2], f'the clean bill is no exception: {tot[0][2]}')
    for (cid, _, _, _, word), t in zip(CASES, tot[1:]):
        c.ok(t[2] and (not word or any(word in w for w in t[2])), f'{cid}: an exception, saying "{word}": {t[2]}')
    # the PM's yes on each, from where he works (the clean one from his Today; the rest through the one bill gate)
    await sign_in(pg, 'u_alan'); await go(pg, 'home')
    await pg.evaluate("() => openBill('xclean')"); await pg.wait_for_timeout(200)
    lbl = await pg.evaluate("() => [...document.querySelectorAll('#d-body [data-bact=\"pmok\"]')].map(b => b.innerText.trim())")
    c.ok(lbl == ['Approve'], f'the bill page reads Approve on a clean bill, not PM: recommend ({lbl})')
    await pg.evaluate("() => { typeof closeAll === 'function' && closeAll(); }")
    st = await pg.evaluate("""async () => { tdyTabSet('appr'); tdyAllOpen = true; render(); await new Promise(r => setTimeout(r, 150));
      const row = [...document.querySelectorAll('.view.on .td-do .td-card')].find(e => e.dataset.id === 'xclean'); if (!row) return 'no row on the PM\\'s Approvals';
      const v = row.querySelector('[data-tdverb]'); if (!v) return 'no button'; const label = v.innerText.trim(); v.click(); await new Promise(r => setTimeout(r, 200));
      const ok = document.querySelector('#mbm #mbm-ok'); ok && ok.click(); await new Promise(r => setTimeout(r, 200)); return label; }""")
    c.ok(st == 'Approve', f'pm: the clean bill on his Approvals reads Approve ({st})')
    pmq = await pg.evaluate("() => mApprovals().filter(x => x.kind === 'bill').map(x => x.id)")
    c.ok(all(x[0] in pmq for x in CASES), f'pm: every exception bill is on his Approvals first (his review): {[x[0] for x in CASES if x[0] not in pmq]}')
    await pg.evaluate("() => { const b = DB.bills.find(x => x.id === 'xnew'); openBill(b.id); }")
    await pg.wait_for_timeout(200)
    lbl = await pg.evaluate("() => [...document.querySelectorAll('#d-body [data-bact=\"pmok\"]')].map(b => b.innerText.trim())")
    c.ok(lbl and all(x == 'Recommend to the Owner' for x in lbl), f'the bill page reads Recommend to the Owner on an exception ({lbl})')
    await pg.evaluate("() => { typeof closeAll === 'function' && closeAll(); }")
    for cid, *_ in CASES:
        await pg.evaluate("i => { const b = DB.bills.find(x => x.id === i); billAction(b, 'pmok'); document.querySelectorAll('#mbm').forEach(m => m.remove()); }", cid)
    S = await pg.evaluate("() => Object.fromEntries(DB.bills.filter(b => /^x/.test(b.id)).map(b => [b.id, b.status]))")
    c.ok(S['xclean'] == 'approved', f'the clean bill is Approved, To Pay ({S["xclean"]})')
    c.ok(all(S[x[0]] != 'approved' for x in CASES), f'no exception or held bill is approved by the PM yes: {S}')
    # the owner: each one on his Approvals with its reason, on his Today; the clean one is not his
    await sign_in(pg, 'u_owner'); await go(pg, 'home')
    oq = await pg.evaluate("() => Object.fromEntries(mApprovals().map(x => [x.kind + ':' + x.id, (x.ydWhy || []).join('; ')]))")
    for cid, *_ in CASES:
        c.ok(('bill:' + cid) in oq and oq['bill:' + cid], f'owner: {cid} on his Approvals with its reason ({oq.get("bill:" + cid)!r})')
    c.ok('bill:xclean' not in oq, 'owner: the clean bill is not his')
    c.ok('po:po_big' in oq, 'owner: the pending PO over $10,000 is his')
    nap = await pg.evaluate("() => DB.pos.filter(po => po.status === 'pending' && poNeedsApproval(po)).map(po => po.id)")
    c.ok(all(('po:' + x) in oq for x in nap), f'owner: every PO poNeedsApproval sends him is his: {[x for x in nap if "po:" + x not in oq]}')
    every = await pg.evaluate("() => mApprovals({ everyone: true }).map(x => x.kind + ':' + x.id)")
    c.ok(all(('po:' + x) in every for x in await pg.evaluate("() => DB.pos.filter(po => po.status === 'pending').map(po => po.id)")), 'every pending PO is in a queue')
    c.ok(any(k.startswith('payroll:') for k in oq), 'owner: payroll is his')
    rows = await pg.evaluate("() => td2Model().rows.map(x => x.it.kind + ':' + x.it.id)")
    c.ok(all(('bill:' + x[0]) in rows for x in CASES), f'owner: every exception is a row of his Today: {[x[0] for x in CASES if "bill:" + x[0] not in rows]}')
    # the controller: the clean one is his to pay, and nothing else planted is
    await sign_in(pg, 'u_controller'); await go(pg, 'home')
    pay = await pg.evaluate("() => td2Model().rows.filter(x => x.it.kind === 'ydPay').map(x => x.it.id)")
    c.ok('xclean' in pay, f'controller: the clean bill is on his Ready to Pay ({pay})')
    c.ok(not [x for x in pay if x in [y[0] for y in CASES]], f'controller: nothing unapproved is on his Ready to Pay ({pay})')
    c.ok(not errs, f'exceptions: errors {errs[:2]}')
    await b.close()


async def approvals(p):
    """The 10-26 rule end to end (chief of staff review, 11-03): a clean bill the PM approves is Approved, To Pay, its record
    naming the rule, and a row of the controller's Today; the owner's Approvals count is one number in the queue, on
    Today and in Ask; every waiting item of the owner's is on his Approvals, his Today or The Brain; The Brain shows every
    proposal it holds (two drafted from the same events are two rows)."""
    b, pg, errs = await open_app(p, True)
    # the demo has no clean bill: Chen enters one, $600 on a received $1,000 order from Nemo Tile (paid before)
    await sign_in(pg, 'u_chen')
    await pg.evaluate(PLANT)
    await pg.evaluate("() => ydPlant('bclean', 'Nemo Tile', 600, { po: 1000, recv: true })")
    c.ok(await pg.evaluate("() => billTotal(DB.bills.find(x => x.id === 'bclean'))") == 600, 'the planted clean bill is $600, not $0')
    c.ok(await pg.evaluate("() => typeof ydBillExc !== 'function' || !ydBillExc(DB.bills.find(x => x.id === 'bclean')).length"), 'the planted bill is no exception (inside its PO)')
    # the PM approves it from his Today, as he would
    await sign_in(pg, 'u_alan'); await go(pg, 'home')
    st = await pg.evaluate("""async () => { tdyTabSet('appr'); tdyAllOpen = true; render(); await new Promise(r => setTimeout(r, 150));
      const row = [...document.querySelectorAll('.view.on .td-do .td-card')].find(e => e.dataset.id === 'bclean'); if (!row) return 'no row on the PM\\'s Approvals';
      const v = row.querySelector('[data-tdverb]'); if (!v) return 'no button'; v.click(); await new Promise(r => setTimeout(r, 200));
      const ok = document.querySelector('#mbm #mbm-ok'); ok && ok.click(); await new Promise(r => setTimeout(r, 200)); return 'clicked'; }""")
    c.ok(st == 'clicked', f'pm: the clean bill on his Approvals ({st})')
    r = await pg.evaluate("() => { const b = DB.bills.find(x => x.id === 'bclean'); const a = (b.approvals || []).slice(-1)[0] || {}; return { status: b.status, rule: a.rule || '', by: a.by || '', at: a.ts || a.t || '' }; }")
    c.ok(r['status'] == 'approved', f'a clean bill the PM approves is Approved, To Pay, not waiting on the owner ({r["status"]})')
    c.ok('10-26' in r['rule'] and r['by'] and r['at'], f'its approval names who, when and the rule ({r})')
    # the owner is not asked; the controller pays it from his Today
    await sign_in(pg, 'u_owner')
    c.ok(not await pg.evaluate("() => mApprovals().some(x => x.id === 'bclean')"), 'the owner is asked to approve a clean bill')
    await sign_in(pg, 'u_controller'); await go(pg, 'home')
    pay = await pg.evaluate("""async () => { tdyTabSet('today'); tdyAllOpen = true; render(); await new Promise(r => setTimeout(r, 150));
      for (const t of ['today', 'coming']) { tdyTabSet(t); render(); const row = [...document.querySelectorAll('.view.on .td-do .td-card')].find(e => e.dataset.id === 'bclean'); if (row) return row.innerText; } return ''; }""")
    c.ok('Ready to Pay' in pay and 'Pay' in pay, f'the controller\'s Today has the approved bill to pay ({pay[:80]!r})')
    c.ok(await pg.evaluate("() => DB.bills.find(x => x.id === 'bclean').status") == 'approved', 'nothing paid it by itself')
    await go(pg, 'ap')
    lead = await pg.evaluate("() => (document.querySelector('.view.on') || {}).innerText || ''")
    c.ok('the Owner approves them' not in lead and 'Alan approves them' not in lead, 'the Bills page still says the owner approves every bill')
    # the owner's Approvals is one number: the queue, Today's chip, Ask
    await sign_in(pg, 'u_owner'); await go(pg, 'home')
    q = await pg.evaluate("() => [mApprovals().length, PRED.waitingOnMe.count()]")
    chip = await pg.evaluate(APPR_N)
    a = await pg.evaluate("async () => { let x = paAsk('what is waiting on my approval'); if (x && x.then) x = await x; return (x && x.headline) || ''; }")
    import re as _re
    an = int((_re.findall(r'\d+', a) or ['-1'])[0])
    c.ok(q[0] == q[1] == chip == an, f'owner: approvals {q[0]} in the queue, {q[1]} in PRED, {chip} on Today, {an} in Ask ("{a[:70]}")')
    # nothing waiting is lost: every item of the owner's full queue is on his Approvals, his Today or in The Brain
    lost = await pg.evaluate("() => typeof ydOwnerPlaced === 'function' ? ydOwnerPlaced().lost : ['no ydOwnerPlaced']")
    c.ok(not lost, f'owner: waiting items on no Today and not in The Brain: {lost[:4]}')
    # The Brain shows every proposal it holds
    await go(pg, 'brain')
    br = await pg.evaluate("""() => [document.querySelectorAll('#yd-brain [data-ydrow][data-sec="need"]').length,
      (typeof ydQueueBase === 'function' ? ydQueueBase() : PRED.waitingOnMe.rows()).filter(x => ['change', 'lesson', 'learn'].includes(x.kind)).length]""")
    c.ok(br[0] == br[1], f'The Brain shows {br[0]} of the {br[1]} proposals waiting')
    c.ok(not errs, f'approvals: errors {errs[:2]}')
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
        if not only or 'exceptions' in only: await exceptions(p)
        if not only or 'approvals' in only: await approvals(p)
        if not only or 'forwards' in only: await forwards(p)
        for uid in ROLES:
            for phone in (False, True):
                if not only or 'today' in only: await today_as(p, uid, phone)
                if not only or 'messages' in only: await messages_as(p, uid, phone)
                if not only or 'tasks' in only: await tasks_as(p, uid, phone)
    sys.exit(c.done())

asyncio.run(main())
