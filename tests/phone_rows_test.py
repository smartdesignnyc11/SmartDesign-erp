"""phone_rows_test: the mobile designer's findings, done as the person on a 390x844 phone (lane phonerows, 2026-10-25).

  #6  Projects   one row per job (name, health dot, what needs me, next milestone), a tap opens the job, no job picker
  #8  Bills      the paid-before-approval Review is the one blue button, the first bill is on the first screen, the
                 filter segment rides with the chips and still filters
  #9  Decisions  late first; the action reads Decide and opens the Record It sheet Today uses; recording it decides
  #22 Clients    rows (name, who, owed, last contact), what is owed is the same number Owed to Us adds up; no stray
                 Billing button
  #10 Foreman    Clock In is the one blue button, then Today's Work, Arriving Today, For You, the rest under More for
                 Today; the title once; text 15px or more; the Say It bar covers no button at the bottom
  #12 Search     a full-height sheet, input on top, results grouped as two-line rows, no keyboard hints; a bill and a
                 delivery found by a few letters, a tap opens it
  and the lists the menus open: Invoices, Estimates, Change Orders, Vendors, Deliveries, Approvals are rows.
Desktop (1440x900) keeps its tables, its blue buttons and its palette.
"""
import asyncio
from harness import *

ROWS = "() => [...document.querySelectorAll('.view.on .pr-row')].filter(r => r.getClientRects().length).map(r => ({ t: (r.querySelector('.pr-t') || {}).textContent || '', m: (r.querySelector('.pr-m') || {}).textContent || '', dot: !!r.querySelector('.pr-dot'), act: (r.querySelector('.pr-act-slot') || {}).textContent || '', top: Math.round(r.getBoundingClientRect().top), h: Math.round(r.getBoundingClientRect().height) }))"
BLUE = "() => [...document.querySelectorAll('.view.on .btn.primary')].filter(e => { if (!e.getClientRects().length) return false; const s = getComputedStyle(e); return s.color === 'rgb(255, 255, 255)' && !/rgba?\\(255, 255, 255|rgba\\(0, 0, 0, 0\\)|transparent/.test(s.backgroundColor) && s.visibility !== 'hidden'; }).map(e => e.textContent.trim())"
WIDE = "() => [...document.querySelectorAll('.view.on table')].filter(t => t.getClientRects().length && t.getBoundingClientRect().right > innerWidth + 1).length"


async def main():
    c = Checks()
    async with async_playwright() as p:
        b, pg, errs = await open_app(p, True)
        # ---- #6 Projects, as the PM
        await sign_in(pg, 'u_alan'); await go(pg, 'ovjobs')
        rows = await pg.evaluate(ROWS)
        n = await pg.evaluate("() => DB.projects.filter(p => !p.archived && p.project && p.project.status !== 'closed').length")
        c.ok(len(rows) >= 4, f'Projects: a row per job ({len(rows)} rows, {n} jobs)')
        c.ok(all(r['dot'] for r in rows), 'Projects: every row has its health dot')
        c.ok(all(r['h'] >= 64 for r in rows), f"Projects: rows are 64px or taller ({[r['h'] for r in rows]})")
        c.ok(any('need' in r['m'] for r in rows) and any('Next ' in r['m'] for r in rows), f"Projects: the meta says what needs me and the next milestone ({rows[:2]})")
        c.ok(sum(1 for r in rows if r['top'] + r['h'] <= 844 - 64) >= 4, 'Projects: four jobs on the first screen')
        c.ok(await pg.evaluate(WIDE) == 0, 'Projects: no table runs past the screen')
        pick = await pg.evaluate("() => { const e = document.querySelector('#subnav .sub-proj'); return !!e && e.getClientRects().length > 0; }")
        c.ok(not pick, 'Projects: the job picker is hidden on the list of every job')
        await pg.locator('.view.on .pr-row').first.click(); await pg.wait_for_timeout(400)
        c.ok(await pg.evaluate("() => view") != 'ovjobs', 'Projects: a tap on a row opens the job')
        # ---- #8 Bills & Payroll, as the controller
        await sign_in(pg, 'u_controller'); await go(pg, 'ap'); await pg.evaluate("() => scrollTo(0, 0)")
        blue = await pg.evaluate(BLUE)
        c.ok(blue == ['Review'], f'Bills: the one blue button is the paid-before-approval Review ({blue})')
        rows = await pg.evaluate(ROWS)
        bills = [r for r in rows if r['top'] > 0]
        c.ok(len(rows) >= 3 and rows[1]['top'] + rows[1]['h'] <= 844 - 64, f"Bills: the first bill is on the first screen (rows at {[r['top'] for r in rows][:4]})")
        seg = await pg.evaluate("() => [...document.querySelectorAll('#ap-kpis .pr-segchip')].map(e => e.textContent.trim())")
        c.ok(len(seg) == 4, f'Bills: the filter segment rides with the chips ({seg})')
        c.ok(not await pg.evaluate("() => { const r = document.querySelector('#ap-filter'); return !!r && r.getClientRects().length > 0; }"), 'Bills: the separate segment row is gone')
        await pg.locator('#ap-kpis .pr-segchip', has_text='Paid').first.click(); await pg.wait_for_timeout(400)
        c.ok(await pg.evaluate("() => (document.querySelector('#ap-filter button.on') || {dataset: {}}).dataset.f") == 'paid', 'Bills: the Paid chip filters the list')
        await pg.evaluate("() => { const b = document.querySelector('#ap-filter [data-f=queue]'); b && b.click(); }")
        # ---- #9 Decisions, as the PM
        await sign_in(pg, 'u_alan'); await go(pg, 'dec'); await pg.evaluate("() => scrollTo(0, 0)")
        rows = await pg.evaluate(ROWS)
        late = [('late' in r['m']) for r in rows]
        c.ok(rows and late[0] and late == sorted(late, reverse=True), f'Decisions: late ones first ({late})')
        c.ok(all(r['act'].strip() == 'Decide' for r in rows), f"Decisions: the action reads Decide ({set(r['act'] for r in rows)})")
        c.ok(any('Owed by' in r['m'] and 'holds up' in r['m'] for r in rows), 'Decisions: who owes it and what it holds up')
        c.ok(await pg.evaluate(BLUE) == ['Decide'], f'Decisions: Decide on the top late one is the one blue button ({await pg.evaluate(BLUE)})')
        did = await pg.evaluate("() => document.querySelector('.view.on .pr-row [data-decided]').dataset.decided")
        await pg.locator('.view.on .pr-row [data-decided]').first.click(); await pg.wait_for_timeout(400)
        sheet = await pg.evaluate("() => { const m = document.getElementById('mbm'); return m ? { h: (m.querySelector('.mbm-hd') || m).textContent.trim().slice(0, 60), ok: (m.querySelector('#mbm-ok') || {}).textContent || '' } : null; }")
        c.ok(sheet and sheet['h'].startswith('Decide') and 'Record It' in sheet['ok'], f'Decisions: Decide opens the Record It sheet Today uses ({sheet})')
        if sheet:
            await pg.fill('#mbm [data-f=ans]', 'Going with the stacked unit'); await pg.click('#mbm #mbm-ok'); await pg.wait_for_timeout(500)
            st = await pg.evaluate("id => (S.decisions.find(d => d.id === id) || {}).status", did)
            c.ok(st == 'made', f'Decisions: recording it decides it ({st})')
            t = await pg.evaluate("() => { const t = document.getElementById('toast'); return t ? t.textContent : ''; }")
            c.ok('Decided' in t, f'Decisions: it toasts what happened ({t[:60]})')
        # ---- #22 Clients, as billing
        await sign_in(pg, 'u_billing'); await go(pg, 'clients'); await pg.evaluate("() => scrollTo(0, 0)")
        rows = await pg.evaluate(ROWS)
        owed = await pg.evaluate("() => { const m = {}; arRows().forEach(r => m[r.c.name] = (m[r.c.name] || 0) + r.bal); return m; }")
        cnt = await pg.evaluate("() => parseInt((document.querySelector('.view.on .dg .cnt') || {}).textContent || '0')")
        c.ok(len(rows) == cnt and cnt >= 5, f'Clients: a row per client the list counts ({len(rows)} rows, {cnt} counted)')
        for name, amt in owed.items():
            r = next((x for x in rows if x['t'].strip() == name), None)
            want = '${:,.0f}'.format(amt)
            c.ok(r and ('owes ' + want) in r['m'], f'Clients: {name} owes {want}, the number Owed to Us adds ({r and r["m"]})')
        c.ok(all('contact' in r['m'] for r in rows), 'Clients: every row says the last contact')
        c.ok(not await pg.evaluate("() => { const b = document.getElementById('btn-gobilling'); return !!b && b.getClientRects().length > 0; }"), 'Clients: no stray Billing button')
        c.ok(sum(1 for r in rows if r['top'] + r['h'] <= 844 - 64) >= 4, 'Clients: four clients on the first screen')
        # ---- the other lists the menus open are rows
        for u, v, pre in [('u_billing', 'billing', "billTab = 'invoices'"), ('u_owner', 'billing', "billTab = 'estimates'"), ('u_owner', 'billing', "billTab = 'co'"),
                          ('u_owner', 'vendors', ''), ('u_owner', 'recv', ''), ('u_owner', 'mapprove', ''), ('u_chen', 'insp', ''), ('u_owner', 'bank', '')]:
            await sign_in(pg, u)
            await pg.evaluate("([v, pre]) => { view = v; " + (pre or '') + "; render(); scrollTo(0, 0); }", [v, pre]); await pg.wait_for_timeout(250)
            rows = await pg.evaluate(ROWS)
            lv = await pg.evaluate("() => document.querySelectorAll('.view.on table.m-cards, .view.on table.rx-cards').length")
            c.ok(len(rows) >= 1 and lv == 0 and await pg.evaluate(WIDE) == 0, f'{u} {v} {pre}: phone rows, no label/value cards, no wide table ({len(rows)} rows)')
        # a delivery row opens its lines, Receive among them
        await sign_in(pg, 'u_owner'); await go(pg, 'recv')
        await pg.locator('.view.on .pr-card .pr-act-slot button').first.click(); await pg.wait_for_timeout(200)
        c.ok(await pg.evaluate("() => { const c = document.querySelector('.view.on .pr-card.pr-open'); return !!c && !!c.querySelector('[data-rin]') && c.querySelector('[data-rin]').getClientRects().length > 0; }"), 'Deliveries: Receive opens the order\'s lines with their Received buttons')
        # ---- #10 the foreman's Today
        await sign_in(pg, 'u_angel'); await go(pg, 'ftoday'); await pg.evaluate("() => scrollTo(0, 0)")
        blue = await pg.evaluate(BLUE)
        c.ok(blue in (['Clock In'], ['Clock Out']), f'Foreman: the clock is the one blue button ({blue})')
        order = await pg.evaluate("() => [...document.querySelectorAll('#ftoday-body > *')].filter(e => e.getClientRects().length).map(e => e.classList.contains('f-hero') ? 'clock' : e.classList.contains('f-work') ? 'work' : e.classList.contains('f3-arriving') ? 'arriving' : e.classList.contains('f-you') ? 'for you' : e.matches('details.pr-more') ? 'more' : e.className)")
        c.ok(order[:2] == ['clock', 'work'] and order[-1] == 'more' and 'arriving' in order and len(order) <= 5, f'Foreman: Clock In, Today\'s Work, Arriving Today, For You, then More for Today ({order})')
        c.ok(not await pg.evaluate("() => !!document.querySelector('#details.pr-more[open]')"), 'Foreman: More for Today starts closed')
        c.ok(await pg.evaluate("() => [...document.querySelectorAll('#v-ftoday h2')].filter(h => h.getClientRects().length && /^Today$/.test(h.textContent.trim())).length") == 0, 'Foreman: the title once (the header\'s)')
        fs = await pg.evaluate("() => { const out = []; document.querySelectorAll('#ftoday-body .f-work .f-row b, #ftoday-body .f-work .f-row .small').forEach(e => e.getClientRects().length && out.push(parseFloat(getComputedStyle(e).fontSize))); return [Math.min(...out), out.length]; }")
        c.ok(fs[0] >= 15, f'Foreman: Today\'s Work reads at 15px or more (smallest {fs[0]}px over {fs[1]} lines)')
        h = await pg.evaluate("() => document.getElementById('v-ftoday').scrollHeight")
        c.ok(h <= 2 * 844 + 200, f'Foreman: Today fits on about two screens ({h}px, was 4,073)')
        cover = await pg.evaluate("""() => { for (let e = document.getElementById('v-ftoday'); e; e = e.parentElement) if (e.scrollHeight > e.clientHeight + 2) e.scrollTop = e.scrollHeight; document.scrollingElement.scrollTop = 1e6; const say = document.getElementById('fsay'); if (!say || !say.getClientRects().length) return 'no bar';
          const s = say.getBoundingClientRect(); return [...document.querySelectorAll('#v-ftoday button, #v-ftoday summary')].filter(b => { const r = b.getBoundingClientRect(); return b.getClientRects().length && (!b.checkVisibility || b.checkVisibility()) && r.bottom > s.top && r.top < s.bottom && r.right > s.left && r.left < s.right; }).map(b => b.textContent.trim()); }""")
        await pg.wait_for_timeout(150)
        c.ok(cover == [] or cover == 'no bar', f'Foreman: at the bottom the Say It bar covers no button ({cover})')
        await pg.locator('#ftoday-body details.pr-more > summary').click(); await pg.wait_for_timeout(200)
        c.ok(await pg.evaluate("() => !!document.querySelector('#ftoday-body details.pr-more[open] #trk-capture')"), 'Foreman: the packing slip camera is one tap away under More for Today')
        # ---- #12 search, as the coordinator
        await sign_in(pg, 'u_chen'); await go(pg, 'home')
        await pg.evaluate("() => openPal()"); await pg.fill('#pal-q', 'tile'); await pg.wait_for_timeout(300)
        s = await pg.evaluate("""() => { const p = document.getElementById('pal'), box = p.querySelector('.box'), hint = p.querySelector('.hint'), q = document.getElementById('pal-q');
          return { sheet: p.classList.contains('pr-pal'), h: Math.round(box.getBoundingClientRect().height), qtop: Math.round(q.getBoundingClientRect().top), hint: !!hint && hint.getClientRects().length > 0,
            groups: [...p.querySelectorAll('.pr-pal-g')].map(g => g.textContent), lines: [...p.querySelectorAll('.pr-pal-r')].map(r => r.children.length), close: !!p.querySelector('.pr-pal-close'),
            rowsH: Math.min(...[...p.querySelectorAll('.pr-pal-r')].map(r => r.getBoundingClientRect().height)) }; }""")
        c.ok(s['sheet'] and s['h'] >= 840 and s['qtop'] <= 4, f"Search: a full-height sheet, the input at the top ({s['h']}px, input at {s['qtop']})")
        c.ok(not s['hint'], 'Search: no keyboard hints on the phone')
        c.ok('Bills' in s['groups'] and all(n == 2 for n in s['lines']) and s['rowsH'] >= 44, f"Search: results grouped as two-line rows ({s['groups']})")
        c.ok(s['close'], 'Search: a close button for a phone with no Esc key')
        bill = await pg.evaluate("() => [...document.querySelectorAll('#pal .pr-pal-r')].findIndex(r => /NT-88412|Nemo/.test(r.textContent))")
        c.ok(bill >= 0, 'Search: the tile bill is found by four letters')
        if bill >= 0:
            await pg.locator('#pal .pr-pal-r').nth(bill).click(); await pg.wait_for_timeout(400)
            c.ok(not await pg.evaluate("() => document.getElementById('pal').classList.contains('on')"), 'Search: a tap opens the result and closes the sheet')
        await pg.evaluate("() => { try { mbCloseModal(); } catch (e) {} document.querySelectorAll('.drawer.on, .drawer.open').forEach(d => d.classList.remove('on', 'open')); openPal(); }")
        await pg.fill('#pal-q', 'PO-2026-048'); await pg.wait_for_timeout(300)
        g = await pg.evaluate("() => [...document.querySelectorAll('#pal .pr-pal-g')].map(g => g.textContent)")
        c.ok('Deliveries' in g, f'Search: an order on its way is under Deliveries ({g})')
        await pg.evaluate("() => closePal()")
        c.ok(not errs, f'page errors: {errs[:3]}')
        await b.close()
        # ---- desktop stays as it is
        b, pg, errs = await open_app(p, False)
        await sign_in(pg, 'u_alan'); await go(pg, 'ovjobs')
        c.ok(await pg.evaluate("() => document.querySelectorAll('.view.on .pr-row, .view.on .pr-tbl').length") == 0, 'Desktop: Projects keeps its table')
        await sign_in(pg, 'u_controller'); await go(pg, 'ap')
        c.ok('New Vendor Bill' in await pg.evaluate(BLUE), 'Desktop: Bills & Payroll keeps its own blue button')
        c.ok(await pg.evaluate("() => { const r = document.querySelector('#ap-filter'); return !!r && r.getClientRects().length > 0; }"), 'Desktop: the filter segment stays')
        await pg.evaluate("() => openPal()"); await pg.fill('#pal-q', 'tile'); await pg.wait_for_timeout(200)
        c.ok(not await pg.evaluate("() => document.getElementById('pal').classList.contains('pr-pal')") and await pg.evaluate("() => document.querySelectorAll('#pal .pr-pal-g').length") == 0, 'Desktop: the palette stays the palette')
        c.ok(not errs, f'desktop page errors: {errs[:3]}')
        await b.close()
    return c.done()

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
