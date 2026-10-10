"""Today: the Owner's and the PM's Home (BACKLOG §3.3), on a 390x844 phone and on desktop.

Budgets (phone): at most 180 words on Home as it opens (what sits behind "N more" and "Read the Full Brief" is
not on screen), at most 12 buttons, and the top Do Now card and its verb on the first screen, above the bottom
tab bar. Chrome (phone): one header, no sub-tab strip repeating the bottom bar, no page lead, no "Signed in as"
toast, and New in the header rather than floating over the content.
Truth: each Pulse number equals the rows (or the figure) its sheet lists, read from its one predicate; Do Now's
count equals the Approvals queue (PRED.waitingOnMe) and the Approvals page's Everything chip; Caught for You's
count equals the rows it lists once expanded; one blue button per screen.
Flows: the Owner's top verb (WW-2026-118, billed $3,800 over PO-2026-044) opens the short-pay sheet through the
one bill-approval gate; the PM's top verb is Answer and opens the answer to the field.
Header (phone): the slim header carries the page title, so the page spends no line on an in-page heading; its four
icon buttons are each 44px tall and 8px apart; "N more in Approvals" opens Approvals at the top.
Delegation: one item sits in exactly one person's queue (DELEGATION: kind -> the role that owns it), nothing is
orphaned, and the owner's Everyone view still lists what waits on the others.
Pulse: "Jobs Late" and "Jobs at Risk" count jobs, and their sheets list each job with its late items underneath."""
import asyncio, re, sys
from harness import *

VIS = """el => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
  return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none'; }"""

MEASURE = r"""() => {
  const vis = el => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none'; };
  const v = document.querySelector('.view.on'), home = v && v.querySelector('.td-home');
  if (!home) return null;
  const words = ((home.innerText || '').match(/\S+/g) || []).filter(w => /[A-Za-z0-9$]/.test(w)).length;
  const btns = [...v.querySelectorAll('button, .btn')].filter(vis).length;
  const tabTop = (document.getElementById('mtabs') || { getBoundingClientRect: () => ({ top: innerHeight }) }).getBoundingClientRect().top;
  const card = home.querySelector('.td-do .td-card'), verb = card && card.querySelector('[data-tdverb]');
  const inView = el => { if (!el) return false; const r = el.getBoundingClientRect(); return r.top >= 0 && r.bottom <= tabTop; };
  const prim = [...v.querySelectorAll('.btn.primary')].filter(vis);
  const sub = document.getElementById('subnav');
  const leads = [...v.querySelectorAll('.ph .lead')].filter(vis).length;
  const fab = document.getElementById('fab');
  return { words, btns, topCard: inView(card), topVerb: inView(verb), verbText: verb ? verb.innerText.trim() : '',
    topText: card ? card.innerText.replace(/\s+/g, ' ') : '', prim: prim.map(b => b.innerText.trim()),
    primIsTopVerb: prim.length === 1 && prim[0] === verb,
    subnav: !!(sub && vis(sub)), leads, toast: (document.getElementById('toast') || {}).innerText || '',
    fabFixed: !!(fab && vis(fab) && getComputedStyle(fab).position === 'fixed'),
    menu: !!(document.getElementById('menu-btn') && vis(document.getElementById('menu-btn'))),
    ask: !!(document.getElementById('tb-ask') && vis(document.getElementById('tb-ask'))),
    sections: [...home.querySelectorAll('.td-sec')].filter(vis).length };
}"""

async def pulse_checks(c, pg, tag):
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
                c.ok(t['label'] == 'Jobs Late' and t['n'] == j['late'], f"{tag}: Pulse \"{t['label']} {t['n']}\": {j['late']} jobs have late items ({j['items']} items); want \"Jobs Late {j['late']}\"")
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
            c.ok(m['topCard'] and m['topVerb'], f"{tag} phone: the top Do Now card or its verb is below the first screen")
            c.ok(m['primIsTopVerb'], f"{tag} phone: blue buttons {m['prim']}; want only the top card's verb")
            c.ok(not m['subnav'], f'{tag} phone: the sub-tab strip repeats the bottom tab bar')
            c.ok(not m['leads'], f'{tag} phone: a page lead sentence shows')
            c.ok('Signed in as' not in m['toast'], f"{tag} phone: sign-in toast \"{m['toast']}\"")
            c.ok(not m['fabFixed'], f'{tag} phone: New floats over the content')
            c.ok(not m['menu'], f'{tag} phone: a second navigation button (menu) in the header')
            c.ok(m['ask'], f'{tag} phone: no Ask in the header')
            # the slim header carries the title; the page does not spend a line repeating it. Its icon buttons: 44px tall, 8px apart.
            hd = await pg.evaluate("""() => { const vis = el => !!el && el.getClientRects().length > 0 && getComputedStyle(el).visibility !== 'hidden';
              const h = document.querySelector('.view.on .td-home .td-ph h2'), cr = document.getElementById('crumbs');
              const btns = [...document.querySelectorAll('header.topbar button')].filter(vis).map(b => { const r = b.getBoundingClientRect(); return { id: b.id, l: r.left, r: r.right, h: r.height }; }).sort((a, b) => a.l - b.l);
              return { h2: vis(h), crumb: vis(cr) ? cr.innerText.trim() : '', btns: btns.map(b => b.id + ' ' + Math.round(b.h) + 'px'),
                       short: btns.filter(b => b.h < 44).map(b => b.id), gaps: btns.slice(1).map((b, i) => Math.round(b.l - btns[i].r)) }; }""")
            c.ok(not hd['h2'] and hd['crumb'] == 'Home', f"{tag} phone: in-page heading shown {hd['h2']}, header title {hd['crumb']!r}; want the title in the header only")
            c.ok(len(hd['btns']) == 4 and not hd['short'], f"{tag} phone: header buttons {hd['btns']}; want four, each 44px tall")
            c.ok(all(g >= 8 for g in hd['gaps']), f"{tag} phone: header button gaps {hd['gaps']}px; want 8px or more")
            await pulse_checks(c, pg, f'{tag} phone')
            # Do Now count = its source = the Approvals page's Everything chip
            n = await pg.evaluate("() => +document.querySelector('.view.on [data-tdcount]').dataset.tdcount")
            src = await pg.evaluate("() => PRED.waitingOnMe.count()")
            more = await pg.evaluate("() => { const a = document.querySelector('.view.on [data-tdall]'); return a ? +a.innerText.match(/\\d+/)[0] : 0; }")
            cards = await pg.evaluate("() => document.querySelectorAll('.view.on .td-do .td-card').length")
            c.ok(n == src, f'{tag} phone: Do Now {n} vs PRED.waitingOnMe {src}')
            c.ok(cards <= 5 and cards + more == n, f'{tag} phone: {cards} cards + {more} more vs Do Now {n}')
            # Caught for You: the count is the rows, once expanded
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
            c.ok(y1 == [0, 'mapprove'], f'{tag} phone: "N more in Approvals" from scroll {y0} lands on {y1[1]} scrolled {y1[0]}px; want Approvals at the top')
            ev = await pg.evaluate("() => { const b = document.querySelector('#mappr-tabs [data-mak=\"all\"] .n'); return b ? +b.innerText : null; }")
            c.ok(ev == n, f'{tag} phone: Approvals Everything {ev} vs Do Now {n}')
            chips = await pg.evaluate("() => [...document.querySelectorAll('#mappr-tabs [data-mak]:not([data-mak=\"all\"]) .n')].map(b => +b.innerText)")
            c.ok(sum(chips) == ev, f'{tag} phone: Approvals chips {chips} sum to {sum(chips)}, Everything says {ev}')
            # the brief: three short lines, the full brief one tap away
            await go(pg, 'home'); await pg.wait_for_timeout(250)
            bl = await pg.evaluate("() => [...document.querySelectorAll('.view.on .td-bl li')].map(l => l.innerText)")
            c.ok(len(bl) <= 3 and all(len(x.split()) <= 11 for x in bl), f'{tag} phone: brief lines {bl}')
            await pg.click('.view.on [data-tdbrief]'); await pg.wait_for_timeout(300)
            full = await pg.evaluate("() => document.querySelectorAll('.view.on #jv .jv-body p').length")
            c.ok(full >= 3, f'{tag} phone: Read the Full Brief shows {full} paragraphs')
            await pg.click('.view.on [data-tdbrief]'); await pg.wait_for_timeout(250)
            # the top verb opens the right flow
            if tag == 'owner':
                c.ok('WW-2026-118' in m['topText'], f"owner phone: top card is \"{m['topText'][:60]}\", want WW-2026-118")
                await pg.click('.view.on .td-do .td-card [data-tdverb="0"]'); await pg.wait_for_timeout(400)
                dlg = await pg.evaluate("() => (document.getElementById('mbm') || document.querySelector('.drawer.on') || {}).innerText || ''")
                c.ok('Approve PO Amount' in dlg, f'owner phone: Approve on WW-2026-118 opens "{dlg[:80]}", want the short-pay sheet')
                st = await pg.evaluate("() => DB.bills.find(b => b.number === 'WW-2026-118').status")
                c.ok(st == 'pm-approved', f'owner phone: opening the sheet changed WW-2026-118 to {st}')
            else:
                c.ok(m['verbText'] == 'Answer', f"pm phone: top verb {m['verbText']!r}, want Answer")
                await pg.click('.view.on .td-do .td-card [data-tdverb="0"]'); await pg.wait_for_timeout(400)
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
                c.ok(m['primIsTopVerb'], f"{tag} desktop: blue buttons {m['prim']}")
                c.ok(m['ask'], f'{tag} desktop: no Ask in the header')
                await pulse_checks(c, pg, f'{tag} desktop')
            c.ok(not errs, f'{tag} desktop: errors {errs[:2]}')
            await b.close()
        # ---- delegation: one item sits in exactly one person's queue; nothing is orphaned; the owner can still see it all
        b, pg, errs = await open_app(p, False)
        await sign_in(pg, 'u_owner')
        KEY = "x => x.kind + '|' + x.id + ('lesson' === x.kind ? '|' + String(x.detail || '').slice(0, 24) : '')"
        every = await pg.evaluate(f"() => mApprovals({{everyone: true}}).map({KEY})")
        c.ok(len(every) >= 26, f'owner: everyone\'s queue holds {len(every)} items (was 26 before delegation)')
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
        # ---- the other roles keep their Home
        b, pg, errs = await open_app(p, False)
        for uid in ('u_chen', 'u_billing', 'u_controller'):
            await sign_in(pg, uid); await go(pg, 'home')
            t = await pg.evaluate("() => view === 'home' ? !!document.querySelector('.view.on .td-home') : null")
            c.ok(t is not True, f'{uid}: got the Owner/PM Today home')
        c.ok(not errs, f'other roles: errors {errs[:2]}')
        await b.close()
    sys.exit(c.done())

asyncio.run(main())
