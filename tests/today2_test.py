"""Today to the mockups Alan approved on 2026-10-25 (TodayOwner, TodayPM, TodayCoord, TodayForeman, TodayBilling,
TodayController at 390px; Main and DeskController at 1440px), and the AI update at its top.

Phone, every office role: the header (the menu, Today over its date line "Thu, Sep 3 · N for you, L late", Search,
Ask as a labelled button, nothing else), the chips (All, Late, Approvals or All, Late, Waiting; All pressed; each
chip's count is the rows it shows), the sections in the board's order (Now first), one blue button and it is on the
first row, one action on every other row, the quiet line at the foot (it opens the Pulse and Caught for You), the bar
(the board's entries; Today's badge is the Late chip), no sideways scroll, 44px targets, the word and button budget.
Desktop, owner and controller: the update (at most three lines), Today with its date line and filters, the What /
Amount / When list, the selected row in a side panel with the page's one blue button; selecting another row moves it.
The foreman: Today over his job and the day, Ask, no Search; the clock card's Clock In is the one blue button.
The AI update: facts only from the records (each checked against its source), ranked by the live Standard's decision
principles, every link opens its record, no line repeats a row's title, a stubbed model that invents a number is
thrown away (the plain lines stand), a valid re-wording is used, the cache (no second call for the same facts, a new
call when a fact changes), "Since <time>" on the app clock, "Nothing new since", Ask About This.
Screenshots: review/today2/."""
import asyncio, os, re, sys
from harness import *

SHOTS = os.path.join(ROOT, 'review', 'today2')
os.makedirs(SHOTS, exist_ok=True)
BOARD = {  # the mockups' chips, sections (in order) and bars
    'u_owner': (['All', 'Late', 'Approvals'], ['Now', 'Approvals', 'You Promised', 'This Week'], ['Today', 'Projects', 'Sales', 'Messages']),
    'u_alan': (['All', 'Late', 'Waiting'], ['Now', 'For You', 'You Promised'], ['Today', 'Projects', 'Clients', 'Tasks', 'Messages']),
    'u_chen': (['All', 'Late', 'Waiting'], ['Now', 'For You', 'You Promised'], ['Today', 'Messages', 'Tasks', 'Buy Board']),
    'u_billing': (['All', 'Late', 'Waiting'], ['Now', 'Waiting on Others', 'This Week'], ['Today', 'Billing', 'Clients', 'Messages']),
    'u_controller': (['All', 'Late', 'Approvals'], ['Now', 'Approvals', 'Waiting on Others', 'This Week'], ['Today', 'Banking', 'Bills & Payroll', 'Messages']),
}
VIS = "el => !!el && el.getClientRects().length > 0 && getComputedStyle(el).visibility !== 'hidden'"

PHONE = r"""() => {
  const vis = el => !!el && el.getClientRects().length > 0 && getComputedStyle(el).visibility !== 'hidden';
  const v = document.querySelector('.view.on'), home = v && v.querySelector('.td-home.td2');
  if (!home) return null;
  const tb = [...document.querySelectorAll('header.topbar > *')].filter(vis).map(e => e.id || e.className);
  const chips = [...home.querySelectorAll('.td2-chips button')].map(b => ({ k: b.dataset.tdytabbtn, label: b.firstChild.textContent.trim(), n: +b.querySelector('.n').textContent, on: b.getAttribute('aria-pressed') === 'true' }));
  const tabs = home.querySelector('.td-tabs'), tabWords = tabs ? ((tabs.innerText || '').match(/\S+/g) || []).length : 0;
  const words = ((home.innerText || '').match(/\S+/g) || []).filter(w => /[A-Za-z0-9$]/.test(w)).length - tabWords;
  const btns = [...v.querySelectorAll('button, .btn')].filter(vis).filter(b => !b.closest('.td-tabs'));
  const prim = [...v.querySelectorAll('.btn.primary')].filter(vis);
  const cards = [...home.querySelectorAll('.td-do .td-card')];
  const first = cards[0];
  const more = home.querySelector('.td-do .td-more'), mm = more ? (more.textContent.match(/^(\d+) more/) || []) : [];
  const small = btns.concat([...home.querySelectorAll('.td2-chips button')]).filter(b => b.getBoundingClientRect().height < 44 && !b.closest('#mtabs')).map(b => b.innerText.trim());
  const brief = home.querySelector('.td2-brief');
  return { tb, crumbs: (document.getElementById('crumbs') || {}).innerText, hdate: (document.getElementById('td2-hdate') || {}).innerText || '',
    chips, words, btns: btns.length, prim: prim.map(b => b.innerText.trim()), primInFirst: prim.length === 1 && !!first && first.contains(prim[0]),
    others: cards.slice(1).map(c => c.querySelectorAll('button').length), cardsN: cards.length, more: mm[1] ? +mm[1] : 0,
    secs: [...home.querySelectorAll('.td2-sh h2')].map(h => h.textContent.trim()),
    quietAfter: !!home.querySelector('.td-do ~ .td2-quiet'), quiet: (home.querySelector('.td2-quiet') || {}).innerText || '',
    bar: [...document.querySelectorAll('#mtabs button')].filter(vis).map(b => (b.querySelector('span') || b).innerText.trim()),
    badge: (document.querySelector('#mtabs [data-mv="home"] i.n') || {}).textContent || '',
    sw: document.scrollingElement.scrollWidth, w: innerWidth, small,
    brief: brief ? { head: brief.querySelector('.td2-bhead').innerText, lines: [...brief.querySelectorAll('.td2-bl')].map(p => ({ t: p.innerText, links: p.querySelectorAll('a').length })) } : null,
    titles: cards.map(c => (c.querySelector('[data-tdrec]') || {}).innerText || '') };
}"""

async def chip_rows(pg, k):
    await pg.click(f'.view.on .td2-chips [data-tdytabbtn="{k}"]'); await pg.wait_for_timeout(200)
    return await pg.evaluate("""() => { const h = document.querySelector('.view.on .td2'); const m = h.querySelector('.td-do .td-more');
      const k = m ? (m.textContent.match(/^(\\d+) more/) || []) : []; return h.querySelectorAll('.td-do .td-card').length + (k[1] ? +k[1] : 0); }""")

async def phone_role(c, p, uid):
    chipsW, secsW, barW = BOARD[uid]
    b, pg, errs = await open_app(p, True)
    await sign_in(pg, uid); await pg.wait_for_timeout(200)
    land = await pg.evaluate('view')
    c.ok(land == 'home', f'{uid} phone: lands on {land}, want Today (the board lights Today first)')
    await go(pg, 'home'); await pg.wait_for_timeout(300)
    m = await pg.evaluate(PHONE)
    if not m: c.ok(False, f'{uid} phone: Today is not drawn'); await b.close(); return
    await pg.screenshot(path=os.path.join(SHOTS, f'{uid[2:]}_phone.png'))
    print(f"{uid} phone: {m['words']} words, {m['btns']} buttons, chips {[(x['label'], x['n']) for x in m['chips']]}, sections {m['secs']}, bar {m['bar']}")
    # header: the menu, Today over its date line, Search, Ask; nothing else
    c.ok(m['tb'] == ['menu-btn', 'crumbs', 'td2-hdate', 'btn-search', 'tb-ask'], f"{uid} phone: header holds {m['tb']}")
    c.ok(m['crumbs'].strip() == 'Today', f"{uid} phone: header title {m['crumbs']!r}")
    allN = next((x['n'] for x in m['chips'] if x['label'] == 'All'), -1); lateN = next((x['n'] for x in m['chips'] if x['label'] == 'Late'), -1)
    c.ok(re.match(r'^[A-Z][a-z]{2}, [A-Z][a-z]{2} \d{1,2} · \d+ for you, \d+ late$', m['hdate']) and m['hdate'].endswith(f'{allN} for you, {lateN} late'), f"{uid} phone: date line {m['hdate']!r}, want '... · {allN} for you, {lateN} late'")
    # chips: the board's, All pressed, each count its rows
    c.ok([x['label'] for x in m['chips']] == chipsW, f"{uid} phone: chips {[x['label'] for x in m['chips']]}, want {chipsW}")
    c.ok([x['on'] for x in m['chips']] == [True] + [False] * (len(chipsW) - 1), f"{uid} phone: Today opens on {[x['label'] for x in m['chips'] if x['on']]}, want All (the mockup; p2nav's Approvals landing is superseded)")
    c.ok(m['cardsN'] + m['more'] == allN, f"{uid} phone: All {allN} vs {m['cardsN']} rows + {m['more']} more")
    # sections in the board's order, Now first
    order = [s for s in secsW if s in m['secs']]
    c.ok(m['secs'] == order and m['secs'] and (m['secs'][0] == 'Now' or 'Now' not in secsW), f"{uid} phone: sections {m['secs']}, want the order {secsW}")
    # one blue button, the first row's; one action on every other row
    c.ok(m['primInFirst'], f"{uid} phone: blue buttons {m['prim']}; want one, on the first row")
    c.ok(all(n == 1 for n in m['others']), f"{uid} phone: actions per row after the first {m['others']}, want one each")
    c.ok(m['quietAfter'] and m['quiet'].strip(), f"{uid} phone: no quiet line at the foot ({m['quiet']!r})")
    # the bar and its Today badge
    c.ok(m['bar'] == barW, f"{uid} phone: bar {m['bar']}, want {barW}")
    c.ok((m['badge'] or '0') == str(lateN), f"{uid} phone: Today badge {m['badge']!r} vs Late {lateN}")
    # the phone: no sideways scroll, 44px targets, the budget
    c.ok(m['sw'] <= m['w'], f"{uid} phone: scrolls sideways ({m['sw']}px)")
    c.ok(not m['small'], f"{uid} phone: buttons under 44px: {m['small'][:4]}")
    c.ok(m['words'] <= 180 and m['btns'] <= 12, f"{uid} phone: {m['words']} words, {m['btns']} buttons (budget 180 and 12)")
    gaps = await pg.evaluate("""() => { const B = [...document.querySelectorAll('.view.on .td2 button')].filter(b => b.getClientRects().length).map(b => b.getBoundingClientRect());
      let bad = 0; B.forEach((a, i) => B.forEach((x, j) => { if (j <= i) return; const dx = Math.max(x.left - a.right, a.left - x.right), dy = Math.max(x.top - a.bottom, a.top - x.bottom); if (Math.max(dx, dy) < 8) bad++; })); return bad; }""")
    c.ok(gaps == 0, f'{uid} phone: {gaps} pairs of buttons closer than 8px')
    # the update: at most two lines on the phone, each with one link, headed "Since ..."
    if m['brief']:
        c.ok(len(m['brief']['lines']) <= 2 and all(x['links'] <= 1 for x in m['brief']['lines']), f"{uid} phone: update lines {m['brief']['lines']}")
        c.ok(m['brief']['head'].startswith('Since '), f"{uid} phone: update head {m['brief']['head']!r}")
    c.ok(uid not in ('u_owner', 'u_alan') or m['brief'] and m['brief']['lines'], f'{uid} phone: no AI update on the board that shows one')
    # each chip shows its count in rows
    for x in m['chips'][1:]:
        n = await chip_rows(pg, x['k'])
        c.ok(n == x['n'], f"{uid} phone: chip {x['label']} says {x['n']}, shows {n}")
    await chip_rows(pg, 'all')
    # the quiet line opens the Pulse and Caught for You (their counts are today_test's)
    await pg.click('.view.on .td2-quiet'); await pg.wait_for_timeout(250)
    opened = await pg.evaluate("() => [document.querySelector('.view.on .td2-quiet').getAttribute('aria-expanded'), !!document.querySelector('.view.on .td2-quietbox .td-catch')]")
    c.ok(opened == ['true', True], f'{uid} phone: the quiet line opens {opened}')
    await pg.click('.view.on .td2-quiet'); await pg.wait_for_timeout(150)
    c.ok(not errs, f'{uid} phone: errors {errs[:2]}')
    await b.close()

DESK = r"""() => {
  const vis = el => !!el && el.getClientRects().length > 0 && getComputedStyle(el).visibility !== 'hidden';
  const v = document.querySelector('.view.on'), home = v && v.querySelector('.td2.td2-desk');
  if (!home) return null;
  const prim = [...v.querySelectorAll('.btn.primary')].filter(vis);
  const aside = home.querySelector('.td2-aside'), sel = home.querySelector('.td2-row.sel');
  return { brief: [...home.querySelectorAll('.td2-bl')].map(p => p.innerText), order: [...home.children].map(e => e.className.split(' ')[0]),
    title: (home.querySelector('.td2-title h2') || {}).innerText, date: (home.querySelector('.td2-date') || {}).innerText,
    tabs: [...home.querySelectorAll('.td2-chips[role=tablist] [role=tab]')].map(b => b.firstChild.textContent.trim() + ' ' + b.querySelector('.n').textContent),
    cols: [...home.querySelectorAll('.td2-cols span')].map(s => s.innerText.trim()).filter(Boolean),
    prim: prim.map(b => b.innerText), primInAside: prim.length === 1 && !!aside && aside.contains(prim[0]),
    asideTitle: aside ? aside.querySelector('.td2-ah').innerText : '', selTitle: sel ? sel.querySelector('[data-tdrec]').innerText : '', selBtns: sel ? sel.querySelectorAll('button').length : -1,
    rows: home.querySelectorAll('.td2-row').length, quiet: !!home.querySelector('.td2-quiet') };
}"""

async def desktop_role(c, p, uid):
    b, pg, errs = await open_app(p, False)
    await sign_in(pg, uid); await go(pg, 'home'); await pg.wait_for_timeout(300)
    m = await pg.evaluate(DESK)
    if not m: c.ok(False, f'{uid} desktop: Today is not drawn'); await b.close(); return
    await pg.screenshot(path=os.path.join(SHOTS, f'{uid[2:]}_desktop.png'))
    print(f"{uid} desktop: tabs {m['tabs']}, {m['rows']} rows, aside {m['asideTitle'][:40]!r}")
    c.ok(m['order'][:2] == ['td2-brief', 'ph'] or uid != 'u_owner', f"{uid} desktop: the update leads the page ({m['order']})")
    c.ok(len(m['brief']) <= 3, f"{uid} desktop: {len(m['brief'])} update lines (at most three)")
    c.ok(m['title'] == 'Today' and re.match(r'^[A-Z][a-z]+day, [A-Z][a-z]+ \d{1,2} · \d+ for you, \d+ late$', m['date'] or ''), f"{uid} desktop: title {m['title']!r}, date line {m['date']!r}")
    c.ok([t.rsplit(' ', 1)[0] for t in m['tabs']] == BOARD[uid][0], f"{uid} desktop: filters {m['tabs']}")
    c.ok(m['cols'] == ['What', 'Amount', 'When'], f"{uid} desktop: columns {m['cols']}")
    c.ok(m['primInAside'], f"{uid} desktop: blue buttons {m['prim']}; want one, in the selected row's panel")
    c.ok(m['asideTitle'] and m['selBtns'] == 0, f"{uid} desktop: the selected row {m['selTitle']!r} (buttons {m['selBtns']}) and its panel {m['asideTitle']!r}")
    c.ok(m['quiet'], f'{uid} desktop: no quiet line')
    # select the second row: the panel follows
    await pg.click('.view.on .td2-row:nth-child(2) .td2-meta'); await pg.wait_for_timeout(250)
    m2 = await pg.evaluate(DESK)
    c.ok(m2['selTitle'] != m['selTitle'] and m2['asideTitle'] != m['asideTitle'], f"{uid} desktop: selecting the second row left the panel on {m2['asideTitle'][:40]!r}")
    c.ok(not errs, f'{uid} desktop: errors {errs[:2]}')
    await b.close()

FACTS = r"""() => {
  const B = td2Cur.B, T = td2Cur.T, td = today(), r = role();
  const out = { lines: B.lines.map(l => l.pre + l.link + l.post), plain: B.plain, cats: B.all.map(f => f.cat), tiers: B.all.map(f => f.tier), bad: [] };
  const P = (standard().principles || []).map(p => p.id);
  out.tierOk = ['law', 'client', 'schedule', 'cost'].every(id => td2Tier(id) === P.indexOf(id) + 1);
  for (let i = 1; i < B.all.length; i++) if (B.all[i].tier < B.all[i - 1].tier) out.bad.push('order ' + i);
  B.all.forEach(f => {
    const t = td2Plain(f);
    if (f.cat === 'decide') { const n = T.rows.filter(x => x.appr && x.due && x.due < td).length; if (!t.startsWith(n + ' decision')) out.bad.push('decide ' + n + ': ' + t); }
    if (f.cat === 'cash') { const s = td2Money(PRED.safeToSpend.figure()); if (!t.includes(s)) out.bad.push('cash ' + s + ': ' + t); }
    if (f.cat === 'leak') { let sum = 0; (TD2_LEAK_ROLE[r] || []).forEach(nm => { const C = CATCH.find(x => x.name === nm); C && (C.rows() || []).forEach(x => (sum += +x.amount > 0 ? +x.amount : 0)); });
      if (!t.includes(td2Money(sum))) out.bad.push('leak ' + td2Money(sum) + ': ' + t); if (!td2MoneyWhy().why || !f.why.includes('raises')) out.bad.push('leak why ' + f.why); }
    if (f.cat === 'people') { const v = PRED.vendorsCoiLapsing.rows().filter(x => x.next)[0]; if (!v || !t.includes(v.v.name)) out.bad.push('people: ' + t); }
    if (f.cat === 'slip') { const j = PRED.jobsAtRisk.rows()[0]; if (!j || !t.includes(shortName(j.p))) out.bad.push('slip: ' + t); }
  });
  const titles = T.shown.map(x => x.title.replace(/…$/, '').toLowerCase()).filter(x => x.length >= 12);
  out.repeat = out.lines.filter(l => titles.some(x => l.toLowerCase().includes(x)));
  return out;
}"""

async def update_rules(c, p):
    b, pg, errs = await open_app(p, True)
    for uid in ('u_owner', 'u_alan', 'u_chen', 'u_billing', 'u_controller'):
        await sign_in(pg, uid); await go(pg, 'home'); await pg.wait_for_timeout(250)
        f = await pg.evaluate(FACTS)
        print(f'{uid} update: {f["lines"]}')
        c.ok(f['tierOk'] and not f['bad'], f"{uid} update: facts not from their records or out of the Standard's order: {f['bad']}")
        c.ok(not f['repeat'], f"{uid} update: repeats a row: {f['repeat']}")
    # every link opens its record
    await sign_in(pg, 'u_owner'); await go(pg, 'home'); await pg.wait_for_timeout(250)
    n = await pg.evaluate("() => document.querySelectorAll('.view.on [data-td2go]').length")
    for i in range(n):
        await go(pg, 'home'); await pg.wait_for_timeout(200)
        link = await pg.evaluate(f"() => document.querySelectorAll('.view.on [data-td2go]')[{i}].innerText")
        await pg.click(f'.view.on [data-td2go="{i}"]'); await pg.wait_for_timeout(350)
        st = await pg.evaluate("() => [view, !!document.querySelector('#mbm:not([hidden])'), !!document.querySelector('.drawer.on')]")
        c.ok(st[0] != 'home' or st[1] or st[2], f'owner update: the link "{link}" opened nothing ({st})')
        await pg.evaluate("() => { try { mbCloseModal(); } catch (e) {} document.querySelectorAll('.drawer.on').forEach(d => d.classList.remove('on')); }")
    # (the link walk above left Today and came back: the update is read fresh from here)
    # the model may only re-word: one that invents a number is thrown away and the plain lines stand
    await go(pg, 'home'); await pg.wait_for_timeout(200)
    r = await pg.evaluate("""async () => { const L = td2Look(); L.cache = null; L.seen = ''; L.seenKey = ''; td2Calls = 0;
      window.aiReady = () => true;
      window.ai = async (p) => p.split('\\n').filter(l => l.includes('[')).map((l, i) => i === 0 ? l.replace(/\\d+/, '99,999') : l).join('\\n');
      render(); await new Promise(r => setTimeout(r, 300));
      const B = td2Cur.B; return { calls: td2Calls, model: B.lines.map(l => l.model), lines: B.lines.map(l => l.pre + l.link + l.post), plain: B.plain, kept: (td2Look().cache || {}).kept }; }""")
    c.ok(r['calls'] == 1 and r['kept'] is False and not any(r['model']) and r['lines'] == r['plain'], f"model guard: an invented number was used or not thrown away {r}")
    c.ok(not any('99,999' in l for l in r['lines']), f"model guard: the invented number shows {r['lines']}")
    # an invented name is thrown away too
    r = await pg.evaluate("""async () => { td2Look().cache = null; td2Calls = 0;
      window.ai = async (p) => p.split('\\n').filter(l => l.includes('[')).map((l, i) => i === 0 ? 'Jessop says: ' + l : l).join('\\n');
      render(); await new Promise(r => setTimeout(r, 300)); const B = td2Cur.B; return { model: B.lines.map(l => l.model), lines: B.lines.map(l => l.pre + l.link + l.post) }; }""")
    c.ok(not any(r['model']) and not any('Jessop' in l for l in r['lines']), f"model guard: an invented name shows {r}")
    # a faithful re-wording is used, once; the same facts are not sent again; a changed fact is
    r = await pg.evaluate("""async () => { td2Look().cache = null; td2Calls = 0;
      window.ai = async (p) => p.split('\\n').filter(l => l.includes('[')).map(l => l.replace(/^/, 'Now: ').replace(/\\.$/, '; worth a look.')).join('\\n');
      render(); await new Promise(r => setTimeout(r, 300)); render(); render(); await new Promise(r => setTimeout(r, 200));
      const B = td2Cur.B; return { calls: td2Calls, model: B.lines.map(l => l.model), lines: B.lines.map(l => l.pre + l.link + l.post), html: [...document.querySelectorAll('.view.on .td2-bl')].map(p => p.innerText) }; }""")
    c.ok(r['calls'] == 1 and all(r['model']) and all(l.startswith('Now: ') for l in r['html']), f"model: a faithful re-wording is not used, or sent twice {r}")
    r2 = await pg.evaluate("""async () => { const v = (DB.vendors || []).find(x => x.id === 'v2'); v.insuranceExp = '2026-08-20';
      render(); await new Promise(r => setTimeout(r, 300)); return { calls: td2Calls, lines: td2Cur.B.lines.map(l => l.pre + l.link + l.post) }; }""")
    c.ok(r2['calls'] == 2 and any('8/20' in l for l in r2['lines']), f"cache: a changed fact did not write the update again {r2}")
    # the model down: the plain sentences (facts, not filler)
    r = await pg.evaluate("""async () => { td2Look().cache = null; window.ai = async () => '__ERR 503'; render(); await new Promise(r => setTimeout(r, 300));
      const B = td2Cur.B; return { lines: B.lines.map(l => l.pre + l.link + l.post), plain: B.plain }; }""")
    c.ok(r['lines'] == r['plain'] and r['lines'], f'model down: {r}')
    await pg.evaluate("() => { window.aiReady = () => false; }")
    # "Since <time>" is the last look, on the app's clock; nothing changed: "Nothing new since <time>"
    await go(pg, 'home'); await pg.wait_for_timeout(1400)
    await go(pg, 'tkall'); await pg.wait_for_timeout(200)
    await go(pg, 'home'); await pg.wait_for_timeout(250)
    s = await pg.evaluate("() => { const L = td2Look(); return { seen: L.seen, head: document.querySelector('.view.on .td2-bhead').innerText, body: [...document.querySelectorAll('.view.on .td2-bl')].map(p => p.innerText), app: today(), clock: td2Clock(L.seen) }; }")
    c.ok(s['seen'] and s['seen'].startswith(s['app']) and s['head'] == f"Since {s['clock']}", f"since: the last look {s['seen']} on the app's day {s['app']}, head {s['head']!r}")
    c.ok(s['body'] == [f"Nothing new since {s['clock']}."], f"nothing new: {s['body']}")
    # Ask About This: Ask opens with the facts
    await pg.evaluate("() => { const v = DB.vendors.find(x => x.id === 'v2'); v.insuranceExp = '2026-08-15'; render(); }"); await pg.wait_for_timeout(200)
    plain = await pg.evaluate("() => td2Cur.B.plain")
    await pg.click('.view.on [data-td2ask]'); await pg.wait_for_timeout(400)
    a = await pg.evaluate("() => [view, (document.getElementById('pa-in') || {}).value || '', (paCtx().today || {}).facts || '']")
    c.ok(a[0] == 'pa' and plain and plain[0] in a[1] and plain[0] in a[2], f'Ask About This: {a}')
    c.ok(not errs, f'update: errors {errs[:2]}')
    await b.close()

async def field_and_others(c, p):
    b, pg, errs = await open_app(p, True)
    await sign_in(pg, 'u_angel'); await pg.wait_for_timeout(300)
    m = await pg.evaluate("""() => { const vis = el => !!el && el.getClientRects().length > 0 && getComputedStyle(el).visibility !== 'hidden';
      return { view, tb: [...document.querySelectorAll('header.topbar > *')].filter(vis).map(e => e.id || e.className), hdate: (document.getElementById('td2-hdate') || {}).innerText || '',
        prim: [...document.querySelectorAll('.view.on .btn.primary')].filter(vis).map(b => b.innerText.trim()), clock: !!document.querySelector('.view.on .f-hero.td2-clock'),
        bar: [...document.querySelectorAll('#tabbar button, #mtabs button')].filter(vis).map(b => (b.querySelector('span') || b).innerText.trim()), sw: document.scrollingElement.scrollWidth }; }""")
    await pg.screenshot(path=os.path.join(SHOTS, 'foreman_phone.png'))
    print('foreman phone:', m)
    c.ok(m['view'] == 'ftoday' and m['tb'] == ['menu-btn', 'crumbs', 'td2-hdate', 'tb-ask'], f"foreman phone: header {m['tb']}")
    c.ok(m['hdate'].endswith('Thu, Sep 3') and '121 State' in m['hdate'], f"foreman phone: date line {m['hdate']!r}")
    c.ok(m['clock'] and m['prim'] == ['Clock In'], f"foreman phone: the clock card's Clock In is the one blue button ({m['prim']})")
    c.ok(m['bar'] == ['Today', 'Daily Log', 'Site', 'Requests', 'Messages'], f"foreman phone: bar {m['bar']}")
    c.ok(m['sw'] <= 390, f"foreman phone: scrolls sideways ({m['sw']})")
    # the designer, the crew and the driver keep their own Today; it still draws without errors at 390px
    for uid in ('u_sarah', 'u_alberto', 'u_alex'):
        await sign_in(pg, uid); await pg.wait_for_timeout(300)
        sw = await pg.evaluate('document.scrollingElement.scrollWidth')
        await pg.screenshot(path=os.path.join(SHOTS, f'{uid[2:]}_phone.png'))
        c.ok(sw <= 390, f'{uid} phone: scrolls sideways ({sw})')
    c.ok(not errs, f'field and others: errors {errs[:2]}')
    await b.close()

async def main():
    c = Checks()
    async with async_playwright() as p:
        for uid in BOARD: await phone_role(c, p, uid)
        for uid in ('u_owner', 'u_controller'): await desktop_role(c, p, uid)
        await update_rules(c, p)
        await field_and_others(c, p)
    sys.exit(c.done())

asyncio.run(main())
