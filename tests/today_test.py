"""Today: the Owner's and the PM's Home (BACKLOG §3.3), on a 390x844 phone and on desktop.

Budgets (phone): at most 180 words on Home as it opens (what sits behind "N more" and "Read the Full Brief" is
not on screen), at most 12 buttons, and the top Do Now card and its verb on the first screen, above the bottom
tab bar. Chrome (phone): one header, no sub-tab strip repeating the bottom bar, no page lead, no "Signed in as"
toast, and New in the header rather than floating over the content.
Truth: each Pulse number equals the rows (or the figure) its sheet lists, read from its one predicate; Do Now's
count equals the Approvals queue (PRED.waitingOnMe) and the Approvals page's Everything chip; Caught for You's
count equals the rows it lists once expanded; one blue button per screen.
Flows: Do Now is ranked by the Standard's decision principles (the Owner's top card is the highest principle on
the list); WW-2026-118's verb (billed $3,800 over PO-2026-044) opens the short-pay sheet through the one
bill-approval gate; the PM's top verb is Answer and opens the answer to the field.
Header (phone): the slim header carries the page title, so the page spends no line on an in-page heading; its four
icon buttons are each 44px tall and 8px apart; the Approvals filter's link opens the Approvals page at the top.
Delegation: one item sits in exactly one person's queue (DELEGATION: kind -> the role that owns it), nothing is
orphaned, and the owner's Everyone view still lists what waits on the others.
Pulse: "Jobs Late" and "Jobs at Risk" count jobs, and their sheets list each job with its late items underneath.
One queue (lane "today", 2026-10-19): Do Now has filters (All, Approvals, Inbox, Tasks, Team); All is the union of
the other three, and the Approvals filter is what Do Now was (PRED.waitingOnMe). The filter strip has its own phone
budget (5 filters, 10 words). The coordinator, billing and the controller get Today too (billing: Overdue AR; the
controller: Safe to Spend and Overdue AR).
tests/today_lane_test.py proves the rest (no item in two filters, the five sources, hand-offs, recurring duties,
proof).
The approved Today mockups (2026-10-25, tests/today2_test.py checks them) moved four pins: the phone header is the
menu, Search and Ask (New and Report a Problem leave Today's header); the Pulse, Caught for You and the full brief sit
behind the quiet line at the foot (opened before they are read); the three brief lines are the AI update (two on the
phone); the PM's chips are All, Late and Waiting (no Approvals chip), and on the desktop the one blue button is the
selected row's, in its side panel."""
import asyncio, re, sys
from harness import *

VIS = """el => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
  return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none'; }"""

MEASURE = r"""() => {
  const vis = el => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none'; };
  const v = document.querySelector('.view.on'), home = v && v.querySelector('.td-home');
  if (!home) return null;
  // the filter strip (All, Approvals, Inbox, Tasks, Team; lane "today", 2026-10-19) is navigation inside the page, not
  // reading or a decision: it has its own budget (at most five filters, at most ten words); the rest keeps 180 and 12
  const tabs = home.querySelector('.td-tabs'), tabWords = tabs ? ((tabs.innerText || '').match(/\S+/g) || []).length : 0;
  const words = ((home.innerText || '').match(/\S+/g) || []).filter(w => /[A-Za-z0-9$]/.test(w)).length - tabWords;
  const filters = [...v.querySelectorAll('.td-tabs button')].filter(vis).length;
  const btns = [...v.querySelectorAll('button, .btn')].filter(vis).filter(b => !b.closest('.td-tabs')).length;
  const tabTop = (document.getElementById('mtabs') || { getBoundingClientRect: () => ({ top: innerHeight }) }).getBoundingClientRect().top;
  const card = home.querySelector('.td-do .td-card'), verb = card && card.querySelector('[data-tdverb]');
  const inView = el => { if (!el) return false; const r = el.getBoundingClientRect(); return r.top >= 0 && r.bottom <= tabTop; };
  const prim = [...v.querySelectorAll('.btn.primary')].filter(vis);
  const sub = document.getElementById('subnav');
  const leads = [...v.querySelectorAll('.ph .lead')].filter(vis).length;
  const fab = document.getElementById('fab');
  return { words, btns, filters, tabWords, topCard: inView(card), topVerb: inView(verb), verbText: verb ? verb.innerText.trim() : '',
    topText: card ? card.innerText.replace(/\s+/g, ' ') : '', prim: prim.map(b => b.innerText.trim()),
    primIsTopVerb: prim.length === 1 && prim[0] === verb,
    subnav: !!(sub && vis(sub)), leads, toast: (document.getElementById('toast') || {}).innerText || '',
    fabFixed: !!(fab && vis(fab) && getComputedStyle(fab).position === 'fixed'),
    menu: !!(document.getElementById('menu-btn') && vis(document.getElementById('menu-btn'))),
    ask: !!(document.getElementById('tb-ask') && vis(document.getElementById('tb-ask'))),
    sections: [...home.querySelectorAll('.td-sec')].filter(vis).length };
}"""

async def quiet_open(pg):
    if await pg.evaluate("() => (document.querySelector('.view.on .td2-quiet') || {}).getAttribute && document.querySelector('.view.on .td2-quiet').getAttribute('aria-expanded') === 'false'"):
        await pg.click('.view.on .td2-quiet'); await pg.wait_for_timeout(250)

async def pulse_checks(c, pg, tag):
    await quiet_open(pg)
    tiles = await pg.evaluate("() => [...document.querySelectorAll('.view.on [data-tdpulse]')].map(a => ({k: a.dataset.tdpulse, n: +a.dataset.n, label: a.querySelector('span').innerText, shown: a.querySelector('b').innerText}))")
    c.ok(len(tiles) == 3, f'{tag}: {len(tiles)} Pulse numbers, want 3')
    for t in tiles:
        await pg.click(f'.view.on [data-tdpulse="{t["k"]}"]'); await pg.wait_for_timeout(250)
        sh = await pg.evaluate("""k => { const s = document.querySelector('#mbm [data-tdsheet="' + k + '"]'); if (!s) return null;
          const rows = [...document.querySelectorAll('#mbm .td-sh-row')];
          const fig = rows.find(r => r.classList.contains('figure'));
          return { n: +s.dataset.n, rows: rows.length, figure: fig ? fig.querySelector('.money').innerText : null }; }""", t['k'])
        if not sh: c.ok(False, f'{tag}: Pulse {t["label"]} opens no sheet'); continue
        c.ok(abs(sh['n'] - t['n']) < 0.005, f'{tag}: Pulse {t["label"]} {t["n"]} vs its sheet {sh["n"]}')
        if t['k'] in ('safe',):
            want = await pg.evaluate("() => safeToSpend().safe")
            c.ok(abs(t['n'] - want) < 0.005, f'{tag}: Safe to Spend {t["n"]} vs safeToSpend() {want}')
            c.ok(sh['figure'] == t['shown'], f'{tag}: Safe to Spend shows {t["shown"]}, its sheet ends {sh["figure"]}')
            add = await pg.evaluate("() => { const R = PRED.safeToSpend.rows(); const sum = R.filter(r => !r[2]).reduce((a, r) => a + r[1], 0); return [Math.round(sum * 100) / 100, R.find(r => r[0] === 'Truly ours')[1]]; }")
            c.ok(abs(add[0] - add[1]) < 0.01, f'{tag}: the Safe to Spend lines add to {add[0]}, truly ours is {add[1]}')
        elif t['k'] == 'ar':
            want = await pg.evaluate("() => PRED.overdueAR.figure()")
            c.ok(abs(t['n'] - want) < 0.005, f'{tag}: Overdue AR {t["n"]} vs PRED.overdueAR {want}')
        else:
            c.ok(sh['rows'] == t['n'], f'{tag}: Pulse {t["label"]} {t["n"]} vs {sh["rows"]} rows listed')
        if t['k'] in ('late', 'risk'):
            # jobs, not items: one row per job, the job's late items listed under it
            j = await pg.evaluate("""k => { const jobs = k === 'late' ? tdMyJobs() : DB.projects.filter(p => !p.archived && (p.project || {}).status !== 'closed');
              const late = jobs.filter(p => PRED.jobLate.count(p.id)).length, items = jobs.reduce((a, p) => a + PRED.jobLate.count(p.id), 0);
              return { late, items, shownItems: document.querySelectorAll('#mbm .td-sh-item').length,
                       head: (document.querySelector('#mbm .td-sh-n') || {}).innerText || '' }; }""", t['k'])
            if t['k'] == 'late':
                c.ok(t['label'] == 'Jobs With Late Items' and t['n'] == j['late'], f"{tag}: Pulse \"{t['label']} {t['n']}\": {j['late']} jobs have late items ({j['items']} items); want \"Jobs With Late Items {j['late']}\"")
                c.ok(j['shownItems'] == j['items'], f"{tag}: the Jobs Late sheet lists {j['shownItems']} late items under its jobs, PRED.jobLate has {j['items']}")
            c.ok(re.search(r'\bjobs?\b', j['head']), f"{tag}: the {t['label']} sheet is headed \"{j['head']}\", want jobs")
            if t['k'] == 'risk' and j['items']:
                c.ok(j['shownItems'] == j['items'], f"{tag}: the Jobs at Risk sheet lists {j['shownItems']} late items under its jobs, PRED.jobLate has {j['items']}")
        await pg.evaluate("() => mbCloseModal()"); await pg.wait_for_timeout(150)
    return tiles

async def main():
    c = Checks()
    async with async_playwright() as p:
        # ---- phone
        for uid, tag in (('u_owner', 'owner'), ('u_alan', 'pm')):
            b, pg, errs = await open_app(p, True)
            await sign_in(pg, uid)
            await go(pg, 'home'); await pg.wait_for_timeout(300)
            m = await pg.evaluate(MEASURE)
            if not m: c.ok(False, f'{tag} phone: Home is not Today'); await b.close(); continue
            print(f"{tag} phone: {m['words']} words, {m['btns']} buttons, {m['sections']} sections, top card on screen {m['topCard']}, verb {m['verbText']!r}")
            c.ok(m['words'] <= 180, f"{tag} phone: {m['words']} words on Home (budget 180)")
            c.ok(m['btns'] <= 12, f"{tag} phone: {m['btns']} buttons on Home (budget 12)")
            c.ok(m['filters'] <= 5 and m['tabWords'] <= 10, f"{tag} phone: {m['filters']} filters, {m['tabWords']} words in the filter strip (budget 5 and 10)")
            c.ok(m['topCard'] and m['topVerb'], f"{tag} phone: the top Do Now card or its verb is below the first screen")
            c.ok(m['primIsTopVerb'], f"{tag} phone: blue buttons {m['prim']}; want only the top card's verb")
            c.ok(not m['subnav'], f'{tag} phone: the sub-tab strip repeats the bottom tab bar')
            c.ok(not m['leads'], f'{tag} phone: a page lead sentence shows')
            c.ok('Signed in as' not in m['toast'], f"{tag} phone: sign-in toast \"{m['toast']}\"")
            c.ok(not m['fabFixed'], f'{tag} phone: New floats over the content')
            # Alan, 2026-10-19: "the hamburger menu should be on the top left of the page"; the bottom bar has no More, so the
            # header's menu button is the one way to the rest of the pages, not a second one
            c.ok(m['menu'], f'{tag} phone: the menu button at the top left is missing')
            c.ok(m['ask'], f'{tag} phone: no Ask in the header')
            # the slim header carries the title; the page does not spend a line repeating it. Its icon buttons: 44px tall, 8px apart.
            hd = await pg.evaluate("""() => { const vis = el => !!el && el.getClientRects().length > 0 && getComputedStyle(el).visibility !== 'hidden';
              const h = document.querySelector('.view.on .td-home .td-ph h2'), cr = document.getElementById('crumbs');
              const btns = [...document.querySelectorAll('header.topbar button')].filter(vis).map(b => { const r = b.getBoundingClientRect(); return { id: b.id, l: r.left, r: r.right, h: r.height }; }).sort((a, b) => a.l - b.l);
              return { h2: vis(h), crumb: vis(cr) ? cr.innerText.trim() : '', btns: btns.map(b => b.id + ' ' + Math.round(b.h) + 'px'),
                       short: btns.filter(b => b.h < 44).map(b => b.id), gaps: btns.slice(1).map((b, i) => Math.round(b.l - btns[i].r)) }; }""")
            # the menu (2026-10-19): Home is named Today for every office role
            c.ok(not hd['h2'] and hd['crumb'] == 'Today',f"{tag} phone: in-page heading shown {hd['h2']}, header title {hd['crumb']!r}; want the title in the header only")
            # the approved mockup's header (2026-10-25): the menu, then Search and Ask, each 44px tall
            c.ok(len(hd['btns']) == 3 and hd['btns'][0].startswith('menu-btn') and not hd['short'], f"{tag} phone: header buttons {hd['btns']}; want the menu first, then Search and Ask, each 44px tall")
            c.ok(all(g >= 8 for g in hd['gaps']), f"{tag} phone: header button gaps {hd['gaps']}px; want 8px or more")
            await pulse_checks(c, pg, f'{tag} phone')
            # (the owner's Today may open on Approvals when something waits on him, Alan 2026-10-25: All is read from its chip)
            # Today is one queue (lane "today"): All holds each thing once: Approvals, Inbox, what is offered, the tasks
            # no approval already stands for (an obligation's renewal is its approval there), the orders (taskfix #1)
            al = await pg.evaluate("""() => { const M = tdyModel(), k = it => it.kind + ':' + it.id, held = new Set([].concat(...M.appr.map(tdyApprRefs)).concat(M.inbox.map(i => 'comm:' + i.id)));
              const want = new Set(M.appr.map(k).concat(M.inbox.map(k), (M.offered || []).map(k), M.tasks.filter(it => !it.t || !it.t.refs.some(r => held.has(r))).map(k), (M.buy || []).map(k), M.all.filter(it => it.kind === 'tdyMinutes').map(k)));
              return [+document.querySelector('.view.on [data-tdytabbtn="all"] .n').textContent, want.size, M.all.length, new Set(M.all.map(k)).size]; }""")
            c.ok(al[0] == al[1] == al[2] == al[3], f'{tag} phone: All {al[0]} vs each thing once {al[1]} (model {al[2]}, distinct {al[3]})')
            # the Approvals filter's count = its source = the Approvals page's Everything chip (the owner's chip; the PM's
            # board has All, Late and Waiting, so his approvals are read through the same filter by hand)
            await pg.evaluate("() => { tdyTabSet('appr'); render(); }") if tag == 'pm' else await pg.click('.view.on [data-tdytabbtn="appr"]')
            await pg.wait_for_timeout(250)
            n = await pg.evaluate("() => +document.querySelector('.view.on [data-tdcount]').dataset.tdcount")
            src = await pg.evaluate("() => PRED.waitingOnMe.count()")
            more = 0  # a filter shows its whole list in place; its link opens the full Approvals page (lane "today")
            cards = await pg.evaluate("() => document.querySelectorAll('.view.on .td-do .td-card').length")
            c.ok(n == src, f'{tag} phone: Do Now {n} vs PRED.waitingOnMe {src}')
            c.ok(cards == n and await pg.locator('.view.on [data-tdall]').count() == 1, f'{tag} phone: the Approvals filter lists {cards} cards vs {n}, with a link to the Approvals page')
            # Caught for You: the count is the rows, once expanded (behind the quiet line)
            await quiet_open(pg)
            cn = await pg.evaluate("() => +document.querySelector('.view.on [data-tdcaught]').dataset.tdcaught")
            shown = await pg.evaluate("() => document.querySelectorAll('.view.on .td-catch .td-card').length")
            c.ok(shown <= 4, f'{tag} phone: {shown} catches shown before "more" (max 4)')
            if await pg.locator('.view.on [data-tdcatchall]').count():
                await pg.click('.view.on [data-tdcatchall]'); await pg.wait_for_timeout(250)
                shown = await pg.evaluate("() => document.querySelectorAll('.view.on .td-catch .td-card').length")
                await pg.click('.view.on [data-tdcatchall]'); await pg.wait_for_timeout(200)
            c.ok(shown == cn, f'{tag} phone: Caught for You says {cn}, lists {shown}')
            print(f'{tag} phone: Do Now {n}, Caught for You {cn}')
            # the Approvals page counts the same queue, and "N more" opens it at the top (the body is the phone's scroller)
            await pg.evaluate("() => document.querySelector('.view.on [data-tdall]').scrollIntoView()"); await pg.wait_for_timeout(100)
            y0 = await pg.evaluate("() => Math.round(Math.max(document.body.scrollTop, document.scrollingElement.scrollTop))")
            await pg.click('.view.on [data-tdall]'); await pg.wait_for_timeout(350)
            y1 = await pg.evaluate("() => [Math.round(Math.max(document.body.scrollTop, document.scrollingElement.scrollTop)), view]")
            c.ok(y1 == [0, 'mapprove'], f'{tag} phone: "Open the Approvals Page" from scroll {y0} lands on {y1[1]} scrolled {y1[0]}px; want Approvals at the top')
            ev = await pg.evaluate("() => { const b = document.querySelector('#mappr-tabs [data-mak=\"all\"] .n'); return b ? +b.innerText : null; }")
            c.ok(ev == n, f'{tag} phone: Approvals Everything {ev} vs Do Now {n}')
            chips = await pg.evaluate("() => [...document.querySelectorAll('#mappr-tabs [data-mak]:not([data-mak=\"all\"]) .n')].map(b => +b.innerText)")
            c.ok(sum(chips) == ev, f'{tag} phone: Approvals chips {chips} sum to {sum(chips)}, Everything says {ev}')
            # the brief: three short lines, the full brief one tap away
            await go(pg, 'home'); await pg.wait_for_timeout(250)
            await pg.evaluate("() => { tdyTabSet('appr'); render(); }"); await pg.wait_for_timeout(250)
            bl = await pg.evaluate("() => [...document.querySelectorAll('.view.on .td2-bl')].map(l => l.innerText)")
            c.ok(len(bl) <= 2, f'{tag} phone: the update has {len(bl)} lines (two on the phone): {bl}')
            await quiet_open(pg)
            await pg.click('.view.on [data-tdbrief]'); await pg.wait_for_timeout(300)
            full = await pg.evaluate("() => document.querySelectorAll('.view.on #jv .jv-body p').length")
            c.ok(full >= 3, f'{tag} phone: Read the Full Brief shows {full} paragraphs')
            await pg.click('.view.on [data-tdbrief]'); await pg.wait_for_timeout(250)
            # the top verb opens the right flow
            if tag == 'owner':
                # Do Now ranks immediate safety and law first, then overdue / today / this week / later, then the
                # decision principle (Alan, 2026-10-11): the top card is the first by that order, and WW-2026-118's verb
                # still opens the one bill-approval gate. The LLC filing used to rank by its expiry ("25 days out") while
                # its task said 5 days late; it now carries its filing date (taskfix #11), so it may lead, as law and
                # overdue, only when its card says the filing is late
                top = await pg.evaluate("() => { const Q = tdQueue(), k = (it) => standardRankKey(it); return [k(Q[0]), Q.map(k).sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2] || a[3] - b[3] || a[4] - b[4])[0], Q[0].title]; }")
                c.ok(top[0] == top[1] and ('LLC' not in top[2] or 'filing' in m['topText'] and 'late' in m['topText']), f"owner phone: top card is \"{m['topText'][:60]}\" at {top[0]}, want the first by immediate, blocked today, urgency, principle, {top[1]}")
                wi = await pg.evaluate("() => [...document.querySelectorAll('.view.on .td-do .td-card')].findIndex(x => x.innerText.includes('WW-2026-118'))")
                c.ok(wi >= 0, 'owner phone: WW-2026-118 is on Do Now')
                await pg.click(f'.view.on .td-do .td-card [data-tdverb="{max(wi, 0)}"]'); await pg.wait_for_timeout(400)
                dlg = await pg.evaluate("() => (document.getElementById('mbm') || document.querySelector('.drawer.on') || {}).innerText || ''")
                c.ok('Approve PO Amount' in dlg, f'owner phone: Approve on WW-2026-118 opens "{dlg[:80]}", want the short-pay sheet')
                st = await pg.evaluate("() => DB.bills.find(b => b.number === 'WW-2026-118').status")
                c.ok(st == 'pm-approved', f'owner phone: opening the sheet changed WW-2026-118 to {st}')
            else:
                # anyone blocked today first (Alan, 2026-10-11, v11.1): the restoration crew that did not show today
                # ranks above the PM's decisions past due since 8/26, which stay on Do Now's first cards; Answer opens it
                ai = await pg.evaluate("() => [...document.querySelectorAll('.view.on .td-do .td-card [data-tdverb]')].findIndex(x => x.innerText.trim() === 'Answer')")
                ci = await pg.evaluate("() => [...document.querySelectorAll('.view.on .td-do .td-card [data-tdverb]')].findIndex(x => x.innerText.trim() === 'Choose')")
                c.ok(m['verbText'] == 'Answer' and ai == 0 and 'did not show' in m['topText'], f"pm phone: top card {m['topText'][:60]!r} verb {m['verbText']!r}, want the crew no-show and Answer first")
                c.ok(ci > 0, f"pm phone: the overdue decisions are still on Do Now's first cards, below the crew waiting today (Choose at {ci})")
                await pg.click(f'.view.on .td-do .td-card [data-tdverb="{max(ai, 0)}"]'); await pg.wait_for_timeout(400)
                dlg = await pg.evaluate("() => (document.getElementById('mbm') || {}).innerText || ''")
                c.ok('send to the field' in dlg.lower() and bool(re.search(r'textarea', await pg.evaluate("() => (document.getElementById('mbm') || {}).innerHTML || ''"))),
                     f'pm phone: Answer opens "{dlg[:80]}"')
            await pg.evaluate("() => { mbCloseModal(); document.querySelectorAll('.drawer.on').forEach(d => d.classList.remove('on')); }"); await pg.wait_for_timeout(150)
            c.ok(not errs, f'{tag} phone: errors {errs[:2]}')
            await b.close()
        # ---- desktop: Today renders, one blue button, the Pulse holds
        for uid, tag in (('u_owner', 'owner'), ('u_alan', 'pm')):
            b, pg, errs = await open_app(p, False)
            await sign_in(pg, uid)
            await go(pg, 'home'); await pg.wait_for_timeout(300)
            m = await pg.evaluate(MEASURE)
            c.ok(bool(m), f'{tag} desktop: Home is not Today')
            if m:
                one = await pg.evaluate("() => { const P = [...document.querySelectorAll('.view.on .btn.primary')].filter(b => b.getClientRects().length); return P.length === 1 && !!P[0].closest('.td2-aside'); }")
                c.ok(one, f"{tag} desktop: blue buttons {m['prim']}; want one, the selected row's in its panel")
                c.ok(m['ask'], f'{tag} desktop: no Ask in the header')
                await pulse_checks(c, pg, f'{tag} desktop')
            c.ok(not errs, f'{tag} desktop: errors {errs[:2]}')
            await b.close()
        # ---- delegation: one item sits in exactly one person's queue; nothing is orphaned; the owner can still see it all
        b, pg, errs = await open_app(p, False)
        await sign_in(pg, 'u_owner')
        KEY = "x => x.kind + '|' + x.id + ('lesson' === x.kind ? '|' + String(x.detail || '').slice(0, 24) : '')"
        every = await pg.evaluate(f"() => mApprovals({{everyone: true}}).map({KEY})")
        # 25 since lane ops (2026-10-10): 206 Lenox no longer carries 121 State's three "we owe" decisions (its own paint
        # decision joined the PM's queue), and the deliverable-dates rule proposes only where an outside designer is on
        # the job, so the two design jobs' duplicate proposals left the owner's queue: 29 -> 25, owner 10 -> 8, PM 16 -> 14.
        c.ok(len(every) >= 25, f'owner: everyone\'s queue holds {len(every)} items (25 since lane ops; 26 before delegation)')
        c.ok(len(set(every)) == len(every), f'owner: everyone\'s queue repeats {len(every) - len(set(every))} key(s)')
        seen, counts = {}, {}
        for uid, r in (('u_owner', 'owner'), ('u_alan', 'pm'), ('u_chen', 'coord'), ('u_billing', 'billing'), ('u_controller', 'controller')):
            await sign_in(pg, uid)
            q = await pg.evaluate(f"() => PRED.waitingOnMe.rows().map(x => [{KEY.split('=> ')[1]}, x.who])")
            counts[r] = len(q)
            bad = sorted(set(w for k, w in q if w != r))
            c.ok(not bad, f'{r}: the queue holds items owned by {bad}')
            for k, w in q: seen.setdefault(k, []).append(r)
            if r == 'owner':
                kinds = sorted(set(k.split('|')[0] for k, w in q))
                c.ok(not set(kinds) & {'req', 'time', 'subm', 'meeting'}, f"owner: queue kinds {kinds}; field requests, hours, submittals and meetings belong to the PM and Chen")
            if r == 'coord':
                c.ok(any(k.startswith('req|') for k, w in q), 'coord: no material request to acknowledge in the queue')
            if r == 'pm':
                c.ok(sum(k.startswith('time|') for k, w in q) == 4, f"pm: {sum(k.startswith('time|') for k, w in q)} crew hours to approve, want 4")
        dup = {k: v for k, v in seen.items() if len(v) > 1}
        orphan = [k for k in every if k not in seen]
        c.ok(not dup, f'{len(dup)} item(s) in two queues: {list(dup.items())[:3]}')
        c.ok(not orphan, f'{len(orphan)} item(s) in nobody\'s queue: {orphan[:4]}')
        c.ok(sum(counts.values()) == len(every), f'queues {counts} add to {sum(counts.values())}, everyone\'s holds {len(every)}')
        print('delegation:', counts)
        # the owner's Approvals still shows what waits on the others
        await sign_in(pg, 'u_owner'); await go(pg, 'mapprove'); await pg.wait_for_timeout(250)
        oth = await pg.evaluate("() => { const a = document.querySelector('.view.on .m-appr-others'); return a ? a.innerText.replace(/\\s+/g, ' ') : null; }")
        c.ok(oth and str(len(every) - counts['owner']) in oth, f"owner: Approvals' Everyone line reads {oth!r}, want the {len(every) - counts['owner']} items on the others")
        if oth:
            vis = await pg.evaluate("() => { const b = document.querySelector('.view.on [data-mothers]'), r = b.getBoundingClientRect(); return r.top >= 0 && r.bottom <= innerHeight; }")
            c.ok(vis, 'owner: the "wait on the others" line is below the first screen of Approvals')
            await pg.click('.view.on [data-mothers]'); await pg.wait_for_timeout(250)
            rows = await pg.evaluate("() => document.querySelectorAll('#mbm .m-appr-o').length")
            c.ok(rows == len(every) - counts['owner'], f'owner: Waiting on the Others lists {rows} rows, want {len(every) - counts["owner"]}')
            await pg.evaluate("() => mbCloseModal()")
        c.ok(not errs, f'delegation: errors {errs[:2]}')
        await b.close()
        # ---- every office role's Home is Today (lane "today", 2026-10-19: one Today page per person, MENU_DRAFT
        # decision 2); the coordinator, billing and the controller get their own queue and only the Pulse numbers they answer for
        b, pg, errs = await open_app(p, False)
        for uid in ('u_chen', 'u_billing', 'u_controller'):
            await sign_in(pg, uid); await go(pg, 'home'); await quiet_open(pg)
            t = await pg.evaluate("() => view === 'home' ? [!!document.querySelector('.view.on .td-home .td-tabs'), document.querySelectorAll('.view.on [data-tdpulse]').length, +document.querySelector('.view.on [data-tdcount]').dataset.tdcount, tdyModel().all.length] : null")
            want = {'u_chen': 0, 'u_billing': 1, 'u_controller': 2}[uid]  # billing: Overdue AR; the controller: Safe to Spend and Overdue AR
            c.ok(t and t[0] and t[1] == want and t[2] == t[3], f'{uid}: Home is their Today, with {want} Pulse numbers and All = their queue ({t})')
        c.ok(not errs, f'other roles: errors {errs[:2]}')
        await b.close()
    sys.exit(c.done())

asyncio.run(main())
