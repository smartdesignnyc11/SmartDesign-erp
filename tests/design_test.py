"""design_test: the 11-03 Design pages (docs/mockups/design/SPEC.md, its must-fix list, BACKLOG section 9), as the person.

Done as the designer (u_sarah), the PM (u_alan), the coordinator (u_chen) and the owner, on the phone (390x844, touch)
and the desktop (1440x900), from the menu:
  MENU       Design lists Selections and Drawings (the designer, the owner); no Design menu for the PM or the coordinator;
             the owner's entries carry no number.
  SELECTIONS no tab rows; opens on Needs You with a count equal to its rows (six on 9/3, every one missing the spec sheet
             the field needs), then With Someone Else naming who (the faucet: Alberto's resubmittal; the knob set: the
             Kleins); the room filter; every card names its estimate line or allowance and what is left, or says it has
             none (must-fix 1); the picture light cannot go to the Kleins at $385 while the page says $412 (must-fix 3);
             the shower drain, bought on no approved estimate line, drafts the bill-back as a change order for the PM
             (must-fix 2, BACKLOG 9.6), and the toast says why the money matters.
  DRAWINGS   no tab rows; Needs You 3 in one unit (Angel's question on A-301; one re-issue naming its 6 sheets; one survey
             naming its 11 rooms), equal to the menu's number; By Sheet or By Room; At the Agency links the permit record.
  IN DESIGN  Projects > All Projects has an In Design filter; the old Design overview forwards there; 121 State Street is
             not in it; Hours Not Logged at its foot reads the same number as the designer's Today.
  CLOCK      relative ages are read from today(): the faucet and the shower set, with one order-by, are equally late; the
             sink, due 9/18, is not "passed".
Usage: python3 design_test.py [--phone|--desktop]"""
import asyncio, re, sys
from harness import *
from pd_pages import page, kids, open_entry, groups


async def modal(pg):
    return await pg.evaluate("() => { const m = document.querySelector('#mbm'); if (!m || !m.getClientRects().length) return null; return { title: (m.querySelector('.mbm-hd h3') || {}).innerText || '', text: m.innerText }; }")


async def toast_text(pg):
    return await pg.evaluate("() => { const t = document.getElementById('toast'); return t ? { text: t.innerText.trim(), open: !!t.querySelector('.toast-open') } : { text: '', open: false }; }")


async def run(c, p, phone):
    dev = 'phone' if phone else 'desktop'
    b, pg, errs = await open_app(p, phone)
    try:
        # ---- MENU
        await sign_in(pg, 'u_sarah')
        K = await kids(pg, phone, 'studio')
        c.ok([k[0] for k in K] == ['Selections', 'Drawings'], f'{dev} MENU: the designer\'s Design lists Selections and Drawings {[k[0] for k in K]}')
        for uid in ('u_alan', 'u_chen'):
            await sign_in(pg, uid)
            G = await groups(pg, phone)
            c.ok('Design' not in G, f'{dev} MENU: no Design menu for {uid} {G}')
        await sign_in(pg, 'u_owner')
        K = await kids(pg, phone, 'studio')
        c.ok([k[0] for k in K] == ['Selections', 'Drawings'] and not any(k[2] for k in K), f'{dev} MENU: the owner\'s Design, no numbers {K}')

        # ---- SELECTIONS
        await sign_in(pg, 'u_sarah')
        await open_entry(pg, phone, 'studio', 'Selections')
        P = await page(pg)
        c.ok(P and P['page'] == 'sel' and P['h2'] == 'Selections', f'{dev} SELECTIONS: the page opens under its own heading ({P and P["h2"]})')
        if P and P['page']:
            c.ok(P['tabs'] == 0, f'{dev} SELECTIONS: no tab rows ({P["tabs"]})')
            c.ok(P['secs'][:1] == ['mine'], f'{dev} SELECTIONS: opens on Needs You {P["secs"]}')
            mine = P['mine'] or []
            c.ok(P['mineN'] == len(mine) == 6, f'{dev} SELECTIONS: Needs You {P["mineN"]} equals its {len(mine)} rows, six on 9/3')
            n = next((k[2] for k in await kids(pg, phone, 'studio') if k[0] == 'Selections'), None)
            c.ok(n == P['mineN'], f'{dev} SELECTIONS: the menu reads {n}, the page {P["mineN"]}')
            c.ok(all('spec sheet' in r['t'].lower() for r in mine), f'{dev} SELECTIONS: every row to fix names the missing spec sheet {[r["t"][:40] for r in mine if "spec sheet" not in r["t"].lower()]}')
            oth = P['others'] or []
            who = {r['who'] for r in oth}
            c.ok(any('Alberto' in w for w in who) and any('Klein' in w for w in who), f'{dev} SELECTIONS: the faucet waits on Alberto, the knob set on the Kleins {who}')
            nol = [r['t'][:40] for r in mine + oth if not re.search(r'EST-\d|CO-\d|[Aa]llowance|No estimate line', r['t'])]
            c.ok(not nol, f'{dev} SELECTIONS: every card names its estimate line or allowance, or says it has none {nol}')
            c.ok(not re.search(r'To Check|Red Flags|Still to Buy', P['text']), f'{dev} SELECTIONS: the old tiles became reasons on rows')
            c.ok(await pg.locator('.view.on [data-puroom]').count() >= 3, f'{dev} SELECTIONS: the room filter is there')
            c.ok(len(P['blues']) <= 1 and P['sw'] <= P['w'], f'{dev} SELECTIONS: one blue at most, no sideways scroll ({P["blues"]}, {P["sw"]})')
            # must-fix 3: the picture light's price is stale
            pl = next((r for r in mine if 'Picture light' in r['t']), None)
            c.ok(pl and '$412' in pl['t'], f'{dev} SELECTIONS: the picture light names the page price $412 ({pl and pl["t"][:160]})')
            blocked = await pg.evaluate("() => { const it = DB.sel.items.find(i => /Picture light/.test(i.name)); return typeof selClientPriceStale === 'function' ? selClientPriceStale(it) : null; }")
            c.ok(blocked and '412' in str(blocked), f'{dev} SELECTIONS: the picture light cannot go to the Kleins until the price is updated ({blocked})')
            sent = await pg.evaluate("() => { const it = DB.sel.items.find(i => /Picture light/.test(i.name)); const st0 = it.stage; try { typeof selSendForApproval === 'function' && selSendForApproval(it); } catch (e) {} return [st0, it.stage]; }")
            c.ok(sent[0] == sent[1], f'{dev} SELECTIONS: sending it for approval is refused while the price is stale ({sent})')
            # must-fix 2: the drain bought on no approved estimate line drafts the bill-back for the PM
            dr = pg.locator('.view.on [data-purow]').filter(has_text='Shower drain').first
            if await dr.count():
                bb = dr.locator('button').filter(has_text=re.compile('Bill-Back'))
                c.ok(await bb.count() > 0, f'{dev} SELECTIONS: the drain carries Draft the Bill-Back for the PM')
                if await bb.count():
                    n0 = await pg.evaluate("() => DB.clients.flatMap(c => c.changeOrders || []).length")
                    await bb.first.click(); await pg.wait_for_timeout(600)
                    r = await pg.evaluate("""n0 => { const all = DB.clients.flatMap(c => (c.changeOrders || []).map(co => ({ co, c })));
                      const x = all.slice(-1)[0]; return { n: all.length, n0, status: x && x.co.status, pid: x && x.co.projectId,
                        lines: x ? x.co.lines.map(l => [l.item, +l.cost || 0]) : [], forPm: !!(x && x.co.billBack) }; }""", n0)
                    c.ok(r['n'] == n0 + 1 and r['status'] == 'draft' and r['pid'] == 'p121' and any('drain' in (l[0] or '').lower() for l in r['lines']), f'{dev} SELECTIONS: a drafted change order on 121 State Street holds the drain ({r})')
                    t = await toast_text(pg)
                    c.ok(t['open'] and re.search(r'raises|bonuses|charity', t['text']), f'{dev} SELECTIONS: the toast says why, with Open ({t})')
            else:
                c.ok(False, f'{dev} SELECTIONS: the shower drain is not on the page')

        # ---- DRAWINGS
        await open_entry(pg, phone, 'studio', 'Drawings')
        P = await page(pg)
        c.ok(P and P['page'] == 'plans' and P['h2'] == 'Drawings', f'{dev} DRAWINGS: the page opens under its own heading ({P and P["h2"]})')
        if P and P['page']:
            c.ok(P['tabs'] == 0, f'{dev} DRAWINGS: no tab rows ({P["tabs"]})')
            mine = P['mine'] or []
            c.ok(P['mineN'] == len(mine) == 3, f'{dev} DRAWINGS: Needs You {P["mineN"]} equals its {len(mine)} rows, three on 9/3')
            t = ' | '.join(r['t'] for r in mine)
            c.ok('A-301' in t and '6 sheets' in t and '11 rooms' in t, f'{dev} DRAWINGS: Angel\'s question, the re-issue of 6 sheets, the survey of 11 rooms ({t[:300]})')
            n = next((k[2] for k in await kids(pg, phone, 'studio') if k[0] == 'Drawings'), None)
            c.ok(n == 3, f'{dev} DRAWINGS: the menu reads {n}')
            c.ok('At the Agency' in P['text'] and 'Certificate of Appropriateness' in P['text'], f'{dev} DRAWINGS: At the Agency shows the LPC filing')
            c.ok(await pg.locator('.view.on [data-pugroup="room"]').count() == 1, f'{dev} DRAWINGS: By Sheet or By Room')
            c.ok(len(P['blues']) <= 1 and P['sw'] <= P['w'], f'{dev} DRAWINGS: one blue at most, no sideways scroll ({P["blues"]}, {P["sw"]})')

        # ---- BILL BACK: every item bought on no approved line is one card in the PM's Approvals, the same day (BACKLOG 9.6);
        # the drain, drafted above, has left it
        await sign_in(pg, 'u_alan')
        bb = await pg.evaluate("() => mApprovals().filter(i => i.kind === 'billback').map(i => [i.title, tdCard(i).verb])")
        c.ok(bb and any('Range' in t for t, _ in bb) and all(v == 'Draft the Change Order' for _, v in bb), f'{dev} BILL BACK: the PM\'s Approvals hold each item bought on no line, with Draft the Change Order {bb}')
        c.ok(not any('Shower drain, square' in t for t, _ in bb), f'{dev} BILL BACK: the drain, drafted already, is not asked twice {bb}')
        await sign_in(pg, 'u_sarah')

        # ---- IN DESIGN
        await go(pg, 'ovstudio')
        st = await pg.evaluate("() => ({ view, f: typeof pdInDesign !== 'undefined' ? pdInDesign : null })")
        c.ok(st['view'] == 'ovjobs' and st['f'], f'{dev} IN DESIGN: the old Design overview forwards to All Projects, In Design ({st})')
        txt = await pg.evaluate("() => document.querySelector('.view.on').innerText")
        c.ok('45 Cranberry' in txt and '140 Prospect' in txt and '121 State Street' not in txt.split('Hours Not Logged')[0], f'{dev} IN DESIGN: the design jobs, not 121 State Street')
        m = re.search(r'Hours Not Logged\D{0,40}(\d+)', txt)
        await go(pg, 'sday')
        t2 = await pg.evaluate("() => document.querySelector('.view.on').innerText")
        m2 = re.search(r'Hours Not Logged\s*(\d+)', t2)
        c.ok(m and m2 and m.group(1) == m2.group(1), f'{dev} IN DESIGN: Hours Not Logged reads one number ({m and m.group(1)} vs Today {m2 and m2.group(1)})')

        # ---- CLOCK
        ages = await pg.evaluate("""() => DB.sel.items.filter(i => i.projectId === 'p121').map(i => [i.name, (selOpenChecks(i).find(c => c.key === 'past-order-by') || {}).msg || '']).filter(x => x[1])""")
        fa = [a for n, a in ages if 'lavatory faucet' in n.lower() or 'shower set' in n.lower()]
        sink = [a for n, a in ages if 'fireclay sink' in n.lower()]
        c.ok(len(fa) == 2 and fa[0] == fa[1], f'{dev} CLOCK: the faucet and the shower set read the same age ({fa})')
        c.ok(not sink, f'{dev} CLOCK: the sink, due 9/18, is not passed ({sink})')
        c.ok(not errs, f'{dev}: page errors {errs[:3]}')
    finally:
        await b.close()


async def main():
    devs = [False, True]
    if '--phone' in sys.argv: devs = [True]
    if '--desktop' in sys.argv: devs = [False]
    c = Checks()
    async with async_playwright() as p:
        for ph in devs:
            n0, f0 = c.n, len(c.fail)
            try:
                await run(c, p, ph)
            except Exception as e:
                c.ok(False, f'{"phone" if ph else "desktop"}: crashed: {str(e)[:300]}')
            print(f'-- {"phone" if ph else "desktop"}: {c.n - n0} checks, {len(c.fail) - f0} failed')
    sys.exit(c.done())

if __name__ == '__main__':
    asyncio.run(main())
