"""p2nav_test: Alan's navigation calls after Pilot 2 (docs/DECISIONS.md 2026-10-25, docs/pilot/pilot2/nav_workshop.md),
done as each person, on the desktop (1440) and the phone (390), every office role plus foreman, crew and driver.
  ASK       a labelled Ask (the sparkle and the word, readable) on every screen the menu or the bar opens, for every
            role with an assistant; it opens Ask. A screen with its own header (the phone's Tasks, Meeting Mode)
            carries it there. From a sheet: Ask sets the sheet aside with its typing, Back puts it back as it was.
  TASKS     Today's Tasks tile or chip, the Tasks page's Due Soon and the phone bar's Tasks read one number, tkTasksN()
            (the designer's Today tile included).
  MESSAGES  one menu entry and one bar entry named Messages; the header, rail and bar carry one number (p2nMsgN);
            the page has Team, Mail and Field tabs (as the role may open them), headed Messages; Mail is the inbox,
            Field is the site questions waiting on me (Approvals' Site Questions, the same rows); a direct line to me
            is on Today with Reply; a team thread shows Seen by whom.
  DIRECTORY one Clients entry: Clients, People and Companies are tabs of it (no People or Companies in Sales); Team
            lists every staff member with phone and email; Message starts a chat; a mail To finds a colleague by
            name; New Email saves a draft to the named colleague's address.
  FIELD     the foreman's bar: Today, Daily Log, Requests, Messages (four, Alan's cap); Site leads the rest, Crew under it.
  OWNER     the owner's Today opens on Approvals when anything waits on him.
  PAYROLL   the coordinator's Time & Crew shows the run's status read-only and no Build Payroll; the controller's keeps it.
  PHONE     no sideways scroll on any screen visited at 390.
Run: python3 p2nav_test.py [--desktop|--phone] [--user u_owner,...]   Screenshots: review/p2nav/ (not committed)."""
import asyncio, os, sys
from harness import *

SHOTS = os.path.join(ROOT, 'review', 'p2nav')
OFFICE = ['u_owner', 'u_alan', 'u_chen', 'u_sarah', 'u_billing', 'u_controller']
FIELD = ['u_angel', 'u_alberto', 'u_alex']

VIS = r"""const vis = el => { if (!el) return false; const r = el.getBoundingClientRect(), s = getComputedStyle(el);
  return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && r.bottom > 0 && r.top < innerHeight; };"""
# the Ask on screen: the header's, or the one a screen's own header carries; its word must be readable
ASK_JS = "() => { " + VIS + r"""
  const L = [document.getElementById('tb-ask'), ...document.querySelectorAll('.p2n-ask.p2n-own')].filter(vis);
  const a = L[0]; if (!a) return { ok: false };
  const sp = a.querySelector('span'), r = a.getBoundingClientRect();
  return { ok: true, word: !!sp && vis(sp) && sp.textContent.trim() === 'Ask', w: Math.round(r.width), h: Math.round(r.height), svg: !!a.querySelector('svg'),
    own: a.classList.contains('p2n-own'), right: Math.round(r.right) }; }"""
# the pages a role reaches from its menu and its bar (the menu's own map)
PAGES_JS = r"""() => { const m = mnMap(); const it = s => s.split('=')[0].split(':')[0];
  const L = (m.field ? m.bar.concat(m.rest) : m.groups.flatMap(g => g.items)).map(it).concat((m.phone || []).map(it));
  return [...new Set(L)].filter(v => (ROLE_VIEWS[role()] || []).includes(v)); }"""
SW = "() => document.documentElement.scrollWidth - innerWidth"

async def shot(pg, name):
    try:
        os.makedirs(SHOTS, exist_ok=True)
        await pg.screenshot(path=os.path.join(SHOTS, name + '.png'))
    except Exception as e:
        print('shot', name, e)

async def ask_checks(c, pg, uid, tag, phone):
    has = await pg.evaluate("() => (ROLE_VIEWS[role()] || []).includes('pa')")
    pages = await pg.evaluate(PAGES_JS)
    miss, words, wide = [], [], []
    for v in pages:
        await go(pg, v)
        a = await pg.evaluate(ASK_JS)
        if has and not a['ok']: miss.append(v)
        elif has and not a['word']: words.append(v)
        if phone:
            sw = await pg.evaluate(SW)
            if sw > 1: wide.append(f'{v} +{sw}px')
    c.ok(not miss, f'{tag}: Ask is on every screen the menu opens (missing on {miss})')
    c.ok(not words, f'{tag}: Ask carries its word on every screen (icon only on {words})')
    if phone: c.ok(not wide, f'{tag}: no sideways scroll at 390 ({wide})')
    if not has: return
    # pressing it opens Ask
    await go(pg, pages[0])
    await pg.evaluate("() => { const a = [document.getElementById('tb-ask'), ...document.querySelectorAll('.p2n-ask.p2n-own')].find(x => x && x.getClientRects().length); a && a.click(); }")
    await pg.wait_for_timeout(250)
    c.ok(await pg.evaluate("view") == 'pa', f'{tag}: the header Ask opens the assistant')
    a = await pg.evaluate(ASK_JS)
    if phone: c.ok(a['ok'] and a['h'] >= 44, f'{tag}: Ask is a 44px target on the phone ({a})')
    # from a sheet: Ask sets it aside with its typing; Back puts it back
    await go(pg, pages[0])
    await pg.evaluate("() => { mbModal('New Note', '<div class=\"f\"><label>Note</label><input data-f=\"note\" id=\"p2nt-in\"></div>', { submit: 'Save', onSubmit: () => true }); }")
    await pg.fill('#p2nt-in', 'half typed')
    sb = await pg.evaluate("() => { const b = document.querySelector('#mbm .p2n-ask.p2n-sheet'); return b && b.getClientRects().length ? b.textContent.trim() : null; }")
    c.ok(sb == 'Ask', f'{tag}: a sheet carries Ask in its header ({sb})')
    if sb:
        await pg.click('#mbm .p2n-ask.p2n-sheet'); await pg.wait_for_timeout(300)
        st = await pg.evaluate("() => ({ view, open: !!document.getElementById('mbm'), held: !!document.getElementById('mbm-held') && !document.getElementById('mbm-held').getClientRects().length, back: (document.getElementById('p2n-resume') || {}).textContent || '' })")
        c.ok(st['view'] == 'pa' and not st['open'] and st['held'] and 'New Note' in st['back'], f'{tag}: Ask from a sheet opens Ask and holds the sheet ({st})')
        if uid in ('u_owner', 'u_alberto'): await shot(pg, f'{uid}_{"phone" if phone else "desktop"}_ask_from_sheet')
        await pg.click('#p2n-resume'); await pg.wait_for_timeout(300)
        back = await pg.evaluate("() => ({ view, open: !!document.querySelector('#mbm:not([hidden])'), val: (document.getElementById('p2nt-in') || {}).value || '' })")
        c.ok(back['open'] and back['val'] == 'half typed' and back['view'] == pages[0], f'{tag}: Back to the sheet puts it back with the typing ({back})')
        await pg.evaluate("() => mbCloseModal()")

async def tasks_checks(c, pg, uid, tag, phone):
    if not await pg.evaluate("() => (ROLE_VIEWS[role()] || []).includes('tkall')"): return
    home = 'sday' if uid == 'u_sarah' else 'home'
    await go(pg, home)
    r = await pg.evaluate("() => { " + VIS + r"""
      const n = s => { const e = [...document.querySelectorAll(s)].find(vis); return e ? +(e.textContent.replace(/\D+/g, '') || 0) : null; };
      return { want: tkTasksN(), tile: n('.view.on .gl[data-tl="due"] .gl-v'), tileK: (([...document.querySelectorAll('.view.on .gl[data-tl="due"] .gl-k')].find(vis) || {}).textContent || ''),
        chip: n('.view.on .td-tabs [data-tdytabbtn="tasks"] .n'), bar: n('#mtabs [data-mv="tkall"] .n'), barShown: vis(document.querySelector('#mtabs [data-mv="tkall"]')),
        rail: n('#nav-groups button[data-grp="mytasks"] .n') }; }""")
    W = r['want']
    seen = {k: r[k] for k in ('tile', 'chip', 'bar', 'rail') if r[k] is not None}
    if r['barShown'] and r['bar'] is None and W: seen['bar (no badge)'] = 0
    await go(pg, 'tkall')
    q = await pg.evaluate("() => { " + VIS + " const e = [...document.querySelectorAll('.view.on .tv-qchips [data-tvqv=\"week\"] .n')].find(vis); return e ? +e.textContent : null; }")
    if q is not None: seen['Tasks Due Soon'] = q
    c.ok(all(v == W for v in seen.values()), f'{tag}: Tasks reads one number, {W} (tkTasksN) on {seen}')
    if uid == 'u_sarah':
        c.ok(r['tile'] == W and r['tileK'].strip() == 'Due Soon', f"{tag}: the designer's Today tile is Due Soon {W} ({r['tileK']} {r['tile']})")
        await go(pg, 'sday')
        await pg.evaluate("() => { const t = document.querySelector('.view.on .gl[data-tl=\"due\"]'); t && t.click(); }"); await pg.wait_for_timeout(300)
        o = await pg.evaluate("() => ({ view, who: tkWho, v: t2View })")
        c.ok(o == {'view': 'tkall', 'who': 'me', 'v': 'week'}, f"{tag}: the tile opens Tasks on Mine, Due Soon ({o})")

MSG_JS = "() => { " + VIS + r"""
  const n = el => el ? +(((el.querySelector('.n') || {}).textContent || '0').replace(/\D+/g, '') || 0) : null;
  const rail = [...document.querySelectorAll('#nav-groups button[data-grp]')].find(b => b.dataset.v === 'chat');
  const bar = [...document.querySelectorAll('#mtabs [data-mv="chat"], #tabbar [data-tab="chat"]')].find(vis);
  const hd = document.getElementById('tb-chat');
  return { N: p2nMsgN(), rail: rail ? { label: rail.innerText.replace(/\s*\d+$/, '').trim(), n: n(rail) } : null,
    bar: bar ? { label: (bar.querySelector('span') || bar).textContent.trim(), n: n(bar) } : null,
    head: hd && vis(hd) ? { label: hd.querySelector('span').textContent.trim(), n: +(hd.querySelector('.msg-n').textContent || 0) } : null,
    tabs: [...document.querySelectorAll('.view.on .p2n-mtabs [data-p2nmt]')].filter(vis).map(b => b.dataset.p2nmt),
    heading: (() => { const v = document.querySelector('.view.on'); const h = v && [...v.querySelectorAll('h1, h2')].find(vis); const cr = document.querySelector('#crumbs b');
      return (h ? h.textContent.trim() : '') + '|' + (cr && vis(cr) ? cr.textContent.trim() : ''); })() }; }"""

async def msg_checks(c, pg, uid, tag, phone):
    if not await pg.evaluate("() => (ROLE_VIEWS[role()] || []).includes('chat')"): return
    field = uid in FIELD
    await go(pg, await pg.evaluate("() => mnMap().home"))
    m = await pg.evaluate(MSG_JS)
    N = m['N']['n']
    if not field and not phone:
        c.ok(m['rail'] and m['rail']['label'] == 'Messages' and m['rail']['n'] == N, f'{tag}: the menu has Messages with the one number {N} ({m["rail"]})')
    if phone:
        c.ok(m['bar'] and m['bar']['label'] == 'Messages' and m['bar']['n'] == N, f'{tag}: the bar has Messages with the one number {N} ({m["bar"]})')
    if m['head']: c.ok(m['head']['label'] == 'Messages' and m['head']['n'] == N, f'{tag}: the header Messages carries {N} ({m["head"]})')
    # the page and its tabs
    await pg.evaluate("() => { msgEnter(); setView('chat'); }"); await pg.wait_for_timeout(250)
    m = await pg.evaluate(MSG_JS)
    want = await pg.evaluate("() => p2nTabsFor().map(x => x[0])")
    if len(want) > 1:
        c.ok(m['tabs'] == want, f'{tag}: Messages has its tabs {want} ({m["tabs"]})')
    c.ok('Messages' in m['heading'] and 'Chat' not in m['heading'].split('|'), f'{tag}: the page is headed Messages ({m["heading"]})')
    if uid in ('u_owner', 'u_angel', 'u_chen'): await shot(pg, f'{uid}_{"phone" if phone else "desktop"}_messages_team')
    if 'mail' in want:
        await pg.click('.view.on .p2n-mtabs [data-p2nmt="mail"]'); await pg.wait_for_timeout(300)
        m2 = await pg.evaluate(MSG_JS)
        st = await pg.evaluate("() => ({ view, chip: +((document.querySelector('#v-comms [data-cmf=\"open\"] .n') || {}).textContent || 0), mail: p2nMsgN().mail, newMail: !!document.querySelector('#v-comms [data-p2nnewmail]') })")
        c.ok(st['view'] == 'comms' and 'Messages' in m2['heading'] and m2['tabs'] == want, f'{tag}: Mail is the inbox under Messages ({st["view"]}, {m2["heading"]}, {m2["tabs"]})')
        c.ok(st['chip'] == st['mail'], f"{tag}: the Mail tab's count is the inbox's Needs an Answer ({st})")
        c.ok(st['newMail'], f'{tag}: Mail has New Email')
        if uid == 'u_owner': await shot(pg, f'{uid}_{"phone" if phone else "desktop"}_messages_mail')
    if 'field' in want:
        await pg.evaluate("() => document.querySelector('.view.on .p2n-mtabs [data-p2nmt=\"field\"]').click()"); await pg.wait_for_timeout(300)
        f = await pg.evaluate("() => ({ view, rows: document.querySelectorAll('#v-chat .p2n-fieldwrap .p2n-frow').length, want: p2nFieldRows().length, n: p2nMsgN().field })")
        c.ok(f['view'] == 'chat' and f['rows'] == f['want'], f'{tag}: Field lists the questions from the site ({f})')
        if not field:
            s = await pg.evaluate("() => PRED.siteQuestionsMine.rows().length")
            c.ok(f['n'] == s == f['rows'], f"{tag}: Field's number is Approvals' Site Questions ({f['n']}, {s}, {f['rows']} rows)")
        if uid in ('u_alan', 'u_angel'): await shot(pg, f'{uid}_{"phone" if phone else "desktop"}_messages_field')
    if phone:
        sw = await pg.evaluate(SW)
        c.ok(sw <= 1, f'{tag}: Messages has no sideways scroll (+{sw}px)')

async def msg_flow(c, p, phone):
    """a direct line to the owner is on his Today with Reply; a team thread line shows who has seen it"""
    tag = 'phone' if phone else 'desktop'
    b, pg, errs = await open_app(p, phone)
    await sign_in(pg, 'u_chen')
    key = await pg.evaluate("() => { const T = msgDirectWith('u_owner', true); msgPostDm(T, 'Can you sign the Nemo Tile PO today?'); save(); return T.key; }")
    await sign_in(pg, 'u_owner')
    await go(pg, 'home')
    t = await pg.evaluate("k => { const M = tdyModel(); const it = M.inbox.find(x => x.kind === 'tdyChat' && x.key === k); return { inbox: !!it, all: M.all.some(x => x.kind === 'tdyChat' && x.key === k), title: it && it.title }; }", key)
    c.ok(t['inbox'] and t['all'] and 'Chen' in (t['title'] or ''), f"{tag}: Chen's direct line is on the owner's Today, Inbox and All ({t})")
    await pg.evaluate("() => { tdyTabSet('inbox'); render(); }"); await pg.wait_for_timeout(200)
    v = await pg.evaluate("k => { const row = [...document.querySelectorAll('.view.on .td-do *')].find(e => /Nemo Tile PO/.test(e.textContent) && e.children.length < 6); return !!row; }", key)
    c.ok(v, f'{tag}: the line is drawn in Do Now')
    await pg.evaluate("k => { const it = tdyModel().inbox.find(x => x.key === k); tdCard(it).run(); }", key); await pg.wait_for_timeout(300)
    o = await pg.evaluate("k => ({ view, key: msgCur(msgMe()).key, left: tdyModel().inbox.some(x => x.key === k) })", key)
    c.ok(o['view'] == 'chat' and o['key'] == key and not o['left'], f'{tag}: Reply opens the conversation, and once read it leaves Today ({o})')
    # Seen by on a job's team thread
    await pg.evaluate("() => { setCurrent('p121'); msgOpen('job:p121'); }"); await pg.wait_for_timeout(200)
    await pg.evaluate("() => { const t = document.getElementById('chat-text'); t.value = 'Tile lands Thursday at 8'; document.getElementById('chat-send') ? document.getElementById('chat-send').click() : null; }")
    await pg.wait_for_timeout(300)
    posted = await pg.evaluate("() => (DB.projects.find(p => p.id === 'p121').chat || []).some(m => /Tile lands Thursday/.test(m.text || ''))")
    if not posted:
        await pg.evaluate("() => { const T = msgThread('job:p121'); const p = DB.projects.find(p => p.id === 'p121'); p.chat.push({ id: uid('c'), by: msgMe().name, fromUid: msgMe().id, text: 'Tile lands Thursday at 8', at: appNowIso(), aud: 'team' }); save(); msgOpen('job:p121'); }")
    await pg.wait_for_timeout(200)
    s0 = await pg.evaluate("() => (document.querySelector('#chat-list .p2n-seen') || {}).textContent || ''")
    c.ok(s0 == 'Sent', f'{tag}: my line on the team thread reads Sent before anyone reads it ({s0})')
    await sign_in(pg, 'u_chen')
    await pg.evaluate("() => { setCurrent('p121'); msgOpen('job:p121'); }"); await pg.wait_for_timeout(300)
    await sign_in(pg, 'u_owner')
    await pg.evaluate("() => { setCurrent('p121'); msgOpen('job:p121'); }"); await pg.wait_for_timeout(300)
    s1 = await pg.evaluate("() => (document.querySelector('#chat-list .p2n-seen') || {}).textContent || ''")
    c.ok('Seen by' in s1 and 'Chen' in s1, f'{tag}: once Chen has read it, it reads Seen by Chen ({s1})')
    await shot(pg, f'owner_{tag}_seen_by')
    c.ok(not errs, f'{tag}: no page errors ({errs[:2]})')
    await b.close()

async def directory_checks(c, pg, uid, tag, phone):
    if uid == 'u_owner':
        m = await pg.evaluate("() => mnMap()")
        sales = next((g for g in m['groups'] if g['id'] == 'sales'), None)
        c.ok(sales and not any(i.startswith(('hbcontacts', 'hbcompanies')) for i in sales['items']), f'{tag}: People and Companies are no longer separate Sales entries')
        c.ok(not any(i.startswith(('hbcontacts', 'hbcompanies')) for i in m['more']), f'{tag}: nor under More')
    if not await pg.evaluate("() => (ROLE_VIEWS[role()] || []).includes('clients')"): return
    await go(pg, 'clients')
    t = await pg.evaluate("() => [...document.querySelectorAll('.view.on .p2n-dtabs [data-p2ndir]')].map(b => b.textContent.trim())")
    want = await pg.evaluate("() => [['clients','Clients'],['hbcontacts','People'],['hbcompanies','Companies']].filter(([k]) => (ROLE_VIEWS[role()] || []).includes(k)).map(x => x[1])")
    if len(want) > 1:
        c.ok(t == want, f'{tag}: Clients has the tabs {want} ({t})')
        await pg.evaluate("() => document.querySelector('.view.on .p2n-dtabs [data-p2ndir=\"hbcontacts\"]').click()"); await pg.wait_for_timeout(300)
        st = await pg.evaluate("() => ({ view, tabs: [...document.querySelectorAll('.view.on .p2n-dtabs [data-p2ndir]')].length, lit: (document.querySelector('#nav-groups button.on') || {}).dataset ? document.querySelector('#nav-groups button.on').dataset.grp : '' })")
        home = await pg.evaluate("() => mnMap().groups.some(g => g.items.some(i => i.startsWith('clients=')))")
        c.ok(st['view'] == 'hbcontacts' and st['tabs'] == len(want) and (phone or st['lit'] == ('clients' if home else 'more')), f'{tag}: People opens as a tab of Clients and lights where Clients sits ({st})')
        if uid == 'u_owner': await shot(pg, f'{uid}_{"phone" if phone else "desktop"}_clients_people')
        if phone:
            sw = await pg.evaluate(SW)
            c.ok(sw <= 1, f'{tag}: People has no sideways scroll (+{sw}px)')

async def team_checks(c, pg, uid, tag, phone):
    if not await pg.evaluate("() => (ROLE_VIEWS[role()] || []).includes('team')"): return
    reach = await pg.evaluate("() => { const m = mnMap(); const L = (m.field ? m.bar.concat(m.rest) : m.groups.flatMap(g => g.items)).concat(m.more).map(s => s.split('=')[0]); return L.includes('team'); }")
    c.ok(reach, f'{tag}: Team is reachable from the menu')
    await go(pg, 'team')
    r = await pg.evaluate("() => { const rows = [...document.querySelectorAll('#v-team .p2n-person')]; const chen = rows.find(x => /Chen Biron/.test(x.textContent));"
                          " return { n: rows.length, staff: p2nTeam().length, chen: chen ? chen.textContent : '', msg: !!(chen && chen.querySelector('[data-p2nmsg]')), heading: (document.querySelector('#v-team h2') || {}).textContent }; }")
    c.ok(r['n'] == r['staff'] and r['n'] >= 8, f"{tag}: Team lists every staff member ({r['n']} of {r['staff']})")
    if uid != 'u_chen':
        c.ok('chen@' in r['chen'] and '555-01' in r['chen'], f"{tag}: Chen's row has his phone and email ({r['chen'][:120]})")
        if await pg.evaluate("() => (ROLE_VIEWS[role()] || []).includes('chat')"):
            c.ok(r['msg'], f"{tag}: Chen's row has Message")
            await pg.evaluate("() => [...document.querySelectorAll('#v-team .p2n-person')].find(x => /Chen Biron/.test(x.textContent)).querySelector('[data-p2nmsg]').click()")
            await pg.wait_for_timeout(300)
            o = await pg.evaluate("() => { const T = msgCur(msgMe()); return { view, direct: !!(T && T.t && T.kind === 'direct' && T.t.members.includes('u_chen')), toast: document.getElementById('toast').textContent }; }")
            c.ok(o['view'] == 'chat' and o['direct'] and 'Chen' in o['toast'], f'{tag}: Message opens a direct chat with Chen and toasts it ({o})')
    if uid == 'u_owner':
        await go(pg, 'team')
        await shot(pg, f'{uid}_{"phone" if phone else "desktop"}_team')
        if phone:
            sw = await pg.evaluate(SW)
            c.ok(sw <= 1, f'{tag}: Team has no sideways scroll (+{sw}px)')
        # New Email to "Chen, Billing": the colleagues are found by name, the draft carries their addresses
        await pg.evaluate("() => p2nCompose()")
        dl = await pg.evaluate("() => { const i = document.querySelector('#mbm [data-f=\"to\"]'); const l = i && i.list; return l ? [...l.options].map(o => o.value) : []; }")
        c.ok(any('Chen Biron <chen@' in x for x in dl) and any('Billing <billing@' in x for x in dl), f'{tag}: the To field offers the team by name ({dl[:3]})')
        await pg.fill('#mbm [data-f="to"]', 'Chen'); await pg.fill('#mbm [data-f="cc"]', 'Billing'); await pg.fill('#mbm [data-f="subject"]', 'Nemo Tile PO'); await pg.fill('#mbm [data-f="body"]', 'Please send the signed PO.')
        n0 = await pg.evaluate("() => (DB.outbox || []).length")
        await pg.click('#mbm #mbm-ok'); await pg.wait_for_timeout(300)
        o = await pg.evaluate("n0 => { const o = (DB.outbox || []).slice(n0)[0]; return o && { to: o.to.email, cc: o.cc, status: o.status, toast: document.getElementById('toast').textContent, appr: mApprovals().some(x => x.kind === 'draft' && x.id === o.id) }; }", n0)
        c.ok(o and o['to'].startswith('chen@') and any(x.startswith('Billing <billing@') for x in o['cc']) and o['status'] == 'draft', f'{tag}: New Email to "Chen" cc "Billing" is a draft to their addresses ({o})')
        c.ok(o and 'Draft to Chen' in o['toast'] and o['appr'], f'{tag}: it toasts and waits on Today to send ({o and o["toast"]})')
        # any other mail To field in a sheet offers the team too
        await pg.evaluate("() => mbModal('Email the Vendor', '<div class=\"f\"><label>To</label><input data-f=\"to\"></div>', { submit: 'Send', onSubmit: () => true })")
        c.ok(await pg.evaluate("() => (document.querySelector('#mbm [data-f=\"to\"]') || {}).getAttribute('list') === 'p2n-colleagues'"), f'{tag}: every mail To field offers the team')
        await pg.evaluate("() => mbCloseModal()")

async def owner_today(c, pg, tag):
    await sign_in(pg, 'u_owner'); await go(pg, 'home')
    n = await pg.evaluate("() => tdyModel().appr.length")
    t = await pg.evaluate("() => tdyTabOf()")
    c.ok(n > 0 and t == 'appr', f"{tag}: the owner's Today opens on Approvals when {n} wait on him ({t})")
    on = await pg.evaluate("() => (document.querySelector('.view.on .td-tabs button.on') || {}).dataset ? document.querySelector('.view.on .td-tabs button.on').dataset.tdytabbtn : ''")
    c.ok(on == 'appr', f'{tag}: the Approvals filter is lit ({on})')
    await pg.evaluate("() => { tdyTabSet('all'); render(); }")
    c.ok(await pg.evaluate("() => tdyTabOf()") == 'all', f'{tag}: his own pick holds while he is on Today')
    await go(pg, 'ovjobs'); await go(pg, 'home')
    c.ok(await pg.evaluate("() => tdyTabOf()") == 'appr', f'{tag}: coming back to Today, it opens on Approvals again')
    await shot(pg, f'owner_{tag}_today_approvals')

async def payroll_checks(c, pg, tag):
    await sign_in(pg, 'u_chen')
    if await pg.evaluate("() => (ROLE_VIEWS.coord || []).includes('time')"):
        await go(pg, 'time')
        r = await pg.evaluate("() => { const b = document.getElementById('btn-payrollfromtime'); const c = document.getElementById('p2n-payrun'); return { btn: !!b && b.getClientRects().length > 0, card: c ? c.innerText : '' }; }")
        c.ok(not r['btn'], f"{tag}: the coordinator's Time & Crew has no Build Payroll")
        c.ok('Payroll Run' in r['card'] and 'Bills & Payroll' in r['card'] and '$' not in r['card'], f"{tag}: it shows the run's status read-only, no amounts ({r['card'][:140]})")
        await shot(pg, f'coord_{tag}_time_payroll')
    await sign_in(pg, 'u_controller'); await go(pg, 'time')
    c.ok(await pg.evaluate("() => { const b = document.getElementById('btn-payrollfromtime'); return !!b && b.getClientRects().length > 0; }"), f"{tag}: the controller keeps Build Payroll")

async def foreman_bar(c, pg, tag, phone):
    await sign_in(pg, 'u_angel')
    m = await pg.evaluate("() => mnMap()")
    bar = [x.split('=')[1] for x in m['bar']]
    c.ok(bar == ['Today', 'Daily Log', 'Requests', 'Messages'], f"{tag}: the foreman's bar ({bar})")
    c.ok(any(x.startswith('fcrew=') for x in m['rest']) and m['rest'][0].startswith('fsite='), f'{tag}: Site leads the rest, Crew is under it ({m["rest"][:3]})')
    if phone:
        await go(pg, 'ftoday')
        tb = await pg.evaluate("() => [...document.querySelectorAll('#tabbar button, #mtabs button')].filter(b => b.getClientRects().length).map(b => ({ l: (b.querySelector('span') || b).textContent.trim(), w: Math.round(b.getBoundingClientRect().width) }))")
        c.ok([x['l'] for x in tb] == bar and all(x['w'] >= 44 for x in tb), f'{tag}: the phone bar reads the same, every tab 44px or wider ({tb})')
        await pg.evaluate("() => document.querySelector('#tabbar [data-tab=\"req\"], #mtabs [data-mv=\"req\"]').click()"); await pg.wait_for_timeout(300)
        c.ok(await pg.evaluate("view") == 'req', f'{tag}: Requests opens from the bar')
        await shot(pg, f'foreman_{tag}_bar')

async def meeting_ask(c, pg, tag):
    await sign_in(pg, 'u_owner')
    await go(pg, 'tkall')
    await pg.evaluate("() => { mtStart({ title: 'Team Meeting', attendees: ['Chen Biron'] }); render(); }"); await pg.wait_for_timeout(400)
    a = await pg.evaluate(ASK_JS)
    c.ok(a['ok'] and a['word'], f'{tag}: Meeting Mode carries Ask ({a})')
    await shot(pg, f'owner_{tag}_meeting_ask')
    await pg.evaluate("() => { const a = [document.getElementById('tb-ask'), ...document.querySelectorAll('.p2n-ask.p2n-own')].find(x => x && x.getClientRects().length); a && a.click(); }"); await pg.wait_for_timeout(300)
    st = await pg.evaluate("() => ({ view, on: !!mtCurrent(), back: (document.getElementById('p2n-resume') || {}).textContent || '' })")
    await shot(pg, f'owner_{tag}_meeting_ask_open')
    c.ok(st['view'] == 'pa' and st['on'] and 'Back to the Meeting' in st['back'], f'{tag}: Ask opens from the meeting, the meeting stays on, Back returns ({st})')
    await pg.evaluate("() => document.getElementById('p2n-resume') && document.getElementById('p2n-resume').click()"); await pg.wait_for_timeout(300)
    c.ok(await pg.evaluate("() => mmActive()"), f'{tag}: Back to the Meeting puts the meeting on screen')

async def main():
    args = sys.argv[1:]
    devs = [False] if '--desktop' in args else [True] if '--phone' in args else [False, True]
    users = next((a.split('=', 1)[1].split(',') for a in args if a.startswith('--user=')), OFFICE + FIELD)
    c = Checks()
    async with async_playwright() as p:
        for phone in devs:
            tag0 = 'phone' if phone else 'desktop'
            b, pg, errs = await open_app(p, phone)
            for uid in users:
                tag = f'{uid}@{tag0}'
                try:
                    await sign_in(pg, uid)
                    await ask_checks(c, pg, uid, tag, phone)
                    await tasks_checks(c, pg, uid, tag, phone)
                    await msg_checks(c, pg, uid, tag, phone)
                    await directory_checks(c, pg, uid, tag, phone)
                    await team_checks(c, pg, uid, tag, phone)
                except Exception as e:
                    c.ok(False, f'{tag}: {str(e)[:300]}')
            try:
                await owner_today(c, pg, tag0)
                await payroll_checks(c, pg, tag0)
                await foreman_bar(c, pg, tag0, phone)
                await meeting_ask(c, pg, tag0)
            except Exception as e:
                c.ok(False, f'{tag0}: {str(e)[:300]}')
            c.ok(not errs, f'{tag0}: no page errors ({errs[:3]})')
            await b.close()
            await msg_flow(c, p, phone)
    sys.exit(c.done())

asyncio.run(main())
