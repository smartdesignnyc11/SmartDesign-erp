"""pu_p3_test: Purchasing lane P3 (Alan, 11-05 evening, "go full force on the purchasing module"; the 11-05 screen capture,
the coordinator expert's day and the field expert's pass; docs/mockups/purchasing/SPEC.md). Done as the person through
the screens, on the desktop (1440x900) and the phone (390x844, touch).

  NEW        Orders has one New and one menu (no "New PO" beside it): New Purchase Order From Lines first, opening the
             Which Lines? sheet; the blank order sits behind More and opens the blank form. Only one creates.
  RECORD     an order opened from its Orders row shows the order first: no documents panel and no list heading above it;
             vendor, job, state, each line with its estimate line, received against ordered, billed, paid; one blue on
             the page, inside the order, the safe next step (an order paid past its total is never "Close PO"); the
             way back says Orders with a line icon, no glyph; on the phone nothing is cut or wider than the screen.
  MENU       the controller's Purchasing is Alan's five (Buy Board, Orders, Quotes, Deliveries, Vendors), read only: no
             New, no pick box, no Receive; billing's is Orders and Vendors; the controller's old overview opens Orders;
             the coordinator's phone bar is Today, Buy Board, Deliveries, Messages, Deliveries' number equal to the page's.
  TAPS       on Purchasing's phone screens (the six pages, an order, a vendor, a stock item, the New PO sheets), every
             visible control is at least 44px both ways (a box inside a 44px label counts as the label), and no two
             controls sit closer than 8px.
  CHIP       the job's Purchasing > Materials: the Order This Week chip's number equals the rows of the card under it.
  OWED       Orders' Owed Back tile equals the money its rows name, and a claim on arrival is one of its rows.
  VENDORS    the list shows open orders, owed back, insurance, W-9 and paid; every row opens its record; the record's
             first card answers open orders, owed back, insurance, W-9 and price history (last, best, trend).
  STOCK      every row says what is on hand, what a need wants of it, and opens its record.
  STATES     an order in each state (draft, pending, issued, partly received on a materials order, received, paid over,
             closed, cancelled): as the controller and as billing nothing on the order writes (no write control, every
             field shut, no blue) and the action functions refuse when called; as the coordinator a pending order has
             no blue and says it waits on the owner, a paid-over order offers no Close PO, a partly received materials
             order has one blue, and a cancelled order is under All. Orders shows no Client Funds New PO.
  FIELD      the field expert's pass: the foreman's Arriving Today says what, when, where and the order's note (no
             money); the header flag reads Report an App Problem and is 44px; the receipt's split is one labelled
             column on the phone with one blue; leaving an estimate after opening Purchase Orders from Lines, with
             nothing typed, toasts nothing; a toned row's stripe never covers its first letter.
Usage: python3 pu_p3_test.py [--desktop|--phone] [--only NEW,RECORD,...]
"""
import asyncio, re, sys
from harness import *

ONLY = set(sys.argv[sys.argv.index('--only') + 1].split(',')) if '--only' in sys.argv else None
DEVS = [False] if '--desktop' in sys.argv else [True] if '--phone' in sys.argv else [False, True]
on = lambda k: not ONLY or k in ONLY

VIS = r"""(sel) => { const vis = e => { const r = e.getBoundingClientRect(); if (r.width < 1 || r.height < 1) return false;
  const s = getComputedStyle(e); return s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity !== 0 && !e.closest('[hidden]'); };
  return [...document.querySelectorAll(sel)].filter(vis).map(e => (e.innerText || e.textContent || e.value || '').replace(/\s+/g, ' ').trim()); }"""

TAPS = r"""(scope) => {
  const W = innerWidth, vis = e => { const r = e.getBoundingClientRect(); if (r.width < 1 || r.height < 1) return false;
    if (r.right <= 0 || r.left >= W) return false; const s = getComputedStyle(e);
    if (s.visibility === 'hidden' || s.display === 'none' || +s.opacity === 0) return false; return !e.closest('[hidden]'); };
  const roots = [...document.querySelectorAll(scope)].filter(vis);
  const sel = 'button, a[href], a[data-go], input:not([type=hidden]), select, textarea, [role=button], [role=tab], summary';
  const T = [];
  roots.forEach(root => root.querySelectorAll(sel).forEach(e => {
    if (!vis(e) || T.some(t => t.e === e)) return;
    if (e.closest('#mtabs, #tabbar, .topbar, #topbar, .rail, #nav-groups')) return;
    let r = e.getBoundingClientRect();
    // a box or radio counts as the label it sits in; a link inside a sentence is not a target
    if (e.type === 'checkbox' || e.type === 'radio') { const lab = e.closest('label'); if (lab && vis(lab)) r = lab.getBoundingClientRect(); }
    if (e.tagName === 'A' && e.parentElement && /^(P|SPAN|LI)$/.test(e.parentElement.tagName) && (e.parentElement.innerText || '').trim().length > (e.innerText || '').trim().length + 20) return;
    T.push({ e, r, d: e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + (typeof e.className === 'string' && e.className ? '.' + e.className.trim().split(/\s+/)[0] : '') + ' "' + (e.getAttribute('aria-label') || e.innerText || e.value || '').replace(/\s+/g, ' ').trim().slice(0, 30) + '"' });
  }));
  const small = T.filter(t => t.r.width < 44 - 0.5 || t.r.height < 44 - 0.5).map(t => `${t.d} ${Math.round(t.r.width)}x${Math.round(t.r.height)}`);
  const close = [];
  for (let i = 0; i < T.length; i++) for (let j = i + 1; j < T.length; j++) {
    const a = T[i], b = T[j];
    if (a.e.contains(b.e) || b.e.contains(a.e)) continue;
    const dx = Math.max(0, Math.max(a.r.left, b.r.left) - Math.min(a.r.right, b.r.right)),
      dy = Math.max(0, Math.max(a.r.top, b.r.top) - Math.min(a.r.bottom, b.r.bottom));
    // two targets side by side (they share a band) or stacked (they share a column) closer than 8px
    if ((dx < 8 && dy === 0) || (dy < 8 && dx === 0)) { if (!(dx === 0 && dy === 0) || true) close.push(`${a.d} | ${b.d} (${Math.round(dx)}px, ${Math.round(dy)}px)`); }
  }
  const se = document.scrollingElement;
  return { n: T.length, small, close: close.slice(0, 12), nclose: close.length, side: se.scrollWidth - se.clientWidth };
}"""


async def js(pg, code, arg=None, wait=350):
    r = await (pg.evaluate(code, arg) if arg is not None else pg.evaluate(code))
    await pg.wait_for_timeout(wait)
    return r


async def reset(pg):
    await js(pg, """() => { try { for (let i = 0; i < 4; i++) if (document.querySelector('#mbm .mbm-box')) mbCloseModal(); } catch (e) {}
      try { if (document.querySelector('#drawer.on') && typeof closeEditor === 'function') closeEditor(); } catch (e) {}
      try { puPlusOpen = ''; puPlusMore = ''; } catch (e) {} try { poOpen = null; vendOpen = null; } catch (e) {}
      document.body.classList.remove('rail-open', 'menu-open'); }""", None, 150)


async def page(pg, v):
    await reset(pg)
    await js(pg, "v => { view = v; render(); document.scrollingElement.scrollTop = 0; }", v, 450)


async def tap(pg, sel, wait=600, nth=0):
    loc = pg.locator(sel).nth(nth)
    await loc.scroll_into_view_if_needed(timeout=5000)
    await loc.click(timeout=6000)
    await pg.wait_for_timeout(wait)


async def s_new(pg, c, dev):
    await page(pg, 'po')
    heads = await js(pg, VIS, '#v-po .pu-ph .acts button')
    c.ok(heads == ['New'], f'NEW {dev}: Orders has one New in its head, nothing beside it ({heads})')
    await tap(pg, '[data-puplus="po"]', 400)
    items = await js(pg, VIS, '.pu-menu [role=menuitem] b')
    c.ok(items[:1] == ['New Purchase Order From Lines'] and 'Blank Purchase Order' not in items and 'More' in items, f'NEW {dev}: the menu leads with New Purchase Order From Lines; the blank order sits behind More ({items})')
    await tap(pg, '.pu-menu [data-pumi="0"]', 900)
    t = await js(pg, "() => { const h = document.querySelector('#mbm .mbm-hd h3'); return h ? h.textContent.trim() : ''; }")
    job = await js(pg, "() => !!document.querySelector('#mbm #pu-pojob')")
    c.ok(t == 'Which Lines?' and job, f'NEW {dev}: From Lines opens Which Lines? with a Job switch ({t!r}, job {job})')
    await reset(pg)
    await page(pg, 'po')
    await tap(pg, '[data-puplus="po"]', 400)
    await tap(pg, '.pu-menu [data-pumore]', 400)
    items = await js(pg, VIS, '.pu-menu [role=menuitem] b')
    c.ok('Blank Purchase Order' in items, f'NEW {dev}: More shows Blank Purchase Order ({items})')
    n0 = await js(pg, "() => DB.pos.length")
    await tap(pg, '.pu-menu [role=menuitem]:has-text("Blank Purchase Order")', 900)
    d = await js(pg, "() => { const d = document.getElementById('drawer'); return d && d.classList.contains('on') ? (document.getElementById('d-title') || {}).textContent : ''; }")
    n1 = await js(pg, "() => DB.pos.length")
    c.ok('purchase order' in (d or '').lower() and n1 == n0, f'NEW {dev}: More > Blank Purchase Order opens the blank form and creates nothing until saved ({d!r}, {n0}->{n1})')
    await reset(pg)


async def open_po(pg, num):
    await page(pg, 'po')
    pid = await js(pg, "n => DB.pos.find(p => p.number === n).id", num, 0)
    await js(pg, "() => { puFilter.po = 'all'; render(); }", None, 300)
    await tap(pg, f'[data-puopen="po:{pid}"]', 900)
    await js(pg, "() => { document.scrollingElement.scrollTop = 0; }", None, 200)


async def s_record(pg, c, dev, phone):
    for num in ['PO-2026-047', 'PO-2026-044', 'PO-2026-041']:
        await open_po(pg, num)
        r = await js(pg, r"""() => {
          const vis = e => { if (!e) return false; const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
          const v = document.getElementById('v-po'), head = document.getElementById('pu-poh');
          const kids = [...v.querySelectorAll('.card, .note, h2, h3')].filter(vis);
          const blues = [...document.querySelectorAll('.view.on .btn.primary')].filter(vis);
          const W = innerWidth, wide = [...document.querySelectorAll('#po-doc *')].filter(e => vis(e) && e.getBoundingClientRect().right > W + 1 && !e.closest('.tw, table')).map(e => e.tagName + '.' + e.className).slice(0, 4);
          const cut = head ? [...head.querySelectorAll('b, span, h2')].filter(e => vis(e) && e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflow !== 'visible').map(e => e.textContent.trim()).slice(0, 4) : [];
          const crumb = document.querySelector('#po-doc .crumb');
          return { head: !!(head && vis(head)), firstCard: kids[0] ? (kids[0].id || kids[0].className || kids[0].tagName) : '',
            panel: vis(document.getElementById('trk-panel')), listHead: [...v.querySelectorAll(':scope > .row h3')].some(vis),
            text: head ? head.innerText.replace(/\s+/g, ' ') : '', blues: blues.map(b => [b.textContent.trim(), !!b.closest('#pu-poh')]),
            wide, cut, crumb: crumb ? crumb.innerText.replace(/\s+/g, ' ').trim() : '', glyph: crumb ? /[›→]/.test(crumb.textContent) : true,
            flowGlyph: /[›→]/.test((document.querySelector('#po-doc .status-flow') || {}).textContent || ''),
            side: document.scrollingElement.scrollWidth - document.scrollingElement.clientWidth };
        }""")
        c.ok(r['head'] and r['firstCard'] in ('pu-poh card', 'card pu-poh') or 'pu-poh' in r['firstCard'], f'RECORD {dev} {num}: the order is the first card on its page ({r["firstCard"]})')
        c.ok(not r['panel'] and not r['listHead'], f'RECORD {dev} {num}: no documents panel and no list heading above the order (panel {r["panel"]}, heading {r["listHead"]})')
        po = await js(pg, "n => { const po = DB.pos.find(p => p.number === n); return { vendor: po.vendor, lines: po.lines.map(l => ({ qty: l.qty, rec: l.received || 0 })) }; }", num, 0)
        t = r['text']
        c.ok(po['vendor'] in t and '121 State Street' in t and 'Estimate line:' in t and all(f'Received {str(l["rec"]).rstrip("0").rstrip(".") if isinstance(l["rec"], float) else l["rec"]} of {l["qty"]}' in t for l in po['lines']) and 'Billed' in t and 'Paid' in t,
             f'RECORD {dev} {num}: the order reads vendor, job, estimate line, received of ordered, billed, paid ({t[:240]!r})')
        c.ok(len(r['blues']) == 1 and r['blues'][0][1], f'RECORD {dev} {num}: one blue on the page, inside the order ({r["blues"]})')
        if num == 'PO-2026-044':
            c.ok(r['blues'] and r['blues'][0][0] != 'Close PO' and 'over' in t.lower(), f'RECORD {dev} {num}: an order paid $3,800 past its total is not closed; its next step settles the bill ({r["blues"]})')
        c.ok(r['crumb'].startswith('Orders') and not r['glyph'] and not r['flowGlyph'], f'RECORD {dev} {num}: the way back reads Orders with a line icon, no glyphs ({r["crumb"]!r})')
        if phone:
            c.ok(r['side'] <= 0 and not r['wide'] and not r['cut'], f'RECORD {dev} {num}: one column, nothing wider than the screen or cut ({r["side"]}, {r["wide"]}, {r["cut"]})')
    await reset(pg)


async def s_menu(pg, c, dev, phone):
    for uid, want in [('u_controller', ['Buy Board', 'Orders', 'Quotes', 'Deliveries', 'Vendors']), ('u_billing', ['Orders', 'Vendors']), ('u_chen', ['Buy Board', 'Orders', 'Quotes', 'Deliveries', 'Vendors', 'Stock'])]:
        await sign_in(pg, uid)
        got = await js(pg, "() => { const B = mnBuild(role()); const g = B.work.find(x => x.id === 'buy'); return g ? g.items.map(i => i.l) : []; }")
        c.ok(got == want, f'MENU {dev} {uid}: Purchasing reads {want} ({got})')
    await sign_in(pg, 'u_controller')
    for v in ['proc', 'rfq', 'recv']:
        await page(pg, v)
        r = await js(pg, r"""() => { const vis = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
          const V = document.querySelector('.view.on');
          return { view, plus: [...V.querySelectorAll('[data-puplus]')].filter(vis).length, pick: [...V.querySelectorAll('.bb-pick, [data-purecv], .pu-bar')].filter(vis).length,
            recv: [...V.querySelectorAll('button')].filter(b => vis(b) && /^Receive/.test(b.textContent.trim())).length,
            note: [...V.querySelectorAll('.pu-ro-note')].some(vis) }; }""")
        c.ok(r['view'] == v and r['plus'] == 0 and r['pick'] == 0 and r['recv'] == 0 and r['note'], f'MENU {dev} controller: {v} opens read only (no New, no pick, no Receive, says so) ({r})')
    await page(pg, 'ovbuy')
    c.ok(await js(pg, "() => view") == 'po', f'MENU {dev} controller: the old Purchasing overview opens Orders')
    await sign_in(pg, 'u_chen')
    if phone:
        await page(pg, 'po')
        bar = await js(pg, "() => [...document.querySelectorAll('#mtabs button')].filter(b => b.offsetParent).map(b => (b.querySelector('span') || b).textContent.trim())")
        c.ok(bar == ['Today', 'Buy Board', 'Deliveries', 'Tasks', 'Messages'], f'MENU {dev} coordinator: the phone bar is Today, Buy Board, Deliveries, Tasks, Messages ({bar})')
        gaps = await js(pg, "() => { const B = [...document.querySelectorAll('#mtabs button')].filter(b => b.offsetParent).map(b => b.getBoundingClientRect()); return { w: B.map(r => Math.round(r.width)), gap: B.slice(1).map((r, i) => Math.round(r.left - B[i].right)), right: Math.round(Math.max(...B.map(r => r.right))) }; }")
        c.ok(all(w >= 44 for w in gaps['w']) and gaps['right'] <= 390, f'MENU {dev} coordinator: the five fit at 390, each 44px or more ({gaps})')
        n = await js(pg, "() => { const i = document.querySelector('#mtabs [data-mv=recv] i.n'); return i ? +i.textContent : 0; }")
        await tap(pg, '#mtabs [data-mv="recv"]', 700)
        m = await js(pg, "() => { const n = document.querySelector('.view.on [data-pusec=mine] .n'); return [view, n ? +n.textContent : 0, puCount('recv')]; }")
        c.ok(m[0] == 'recv' and n == m[1] == m[2] and n > 0, f'MENU {dev} coordinator: Deliveries on the bar opens Deliveries and its number is the page\'s Needs You ({n} vs {m})')
    await reset(pg)


async def s_taps(pg, c, dev):
    screens = []
    async def measure(name, scope='.view.on'):
        r = await js(pg, TAPS, scope, 0)
        screens.append((name, r))
    for v in ['po', 'vendors', 'inv', 'recv', 'proc', 'rfq']:
        await page(pg, v); await measure('page ' + v)
    await open_po(pg, 'PO-2026-047'); await measure('order PO-2026-047')
    await open_po(pg, 'PO-2026-044'); await measure('order PO-2026-044')
    await page(pg, 'vendors')
    await tap(pg, '[data-puopen="vend:v2"]', 800); await measure('vendor Window Works')
    await page(pg, 'inv')
    await tap(pg, '[data-puopen="item:iv13"]', 800); await measure('stock item', '#drawer')
    await page(pg, 'po')
    await tap(pg, '[data-puplus="po"]', 400); await measure('Orders New menu', '.pu-menu')
    await tap(pg, '.pu-menu [data-pumi="0"]', 900); await measure('Which Lines? sheet', '#mbm .mbm-hd, #mbm .mbm-ft')
    await reset(pg)
    for name, r in screens:
        c.ok(not r['small'], f'TAPS {dev} {name}: every control is 44px or more ({len(r["small"])}: {r["small"][:6]})')
        c.ok(r['nclose'] == 0, f'TAPS {dev} {name}: no two controls closer than 8px ({r["nclose"]}: {r["close"][:4]})')
        c.ok(r['side'] <= 0, f'TAPS {dev} {name}: no sideways scroll ({r["side"]})')


async def s_chip(pg, c, dev):
    await sign_in(pg, 'u_alan')
    await reset(pg)
    await js(pg, "() => { jpOpenJob('p121', 'proc'); }", None, 700)
    b = pg.locator('[data-jpgo]', has_text='Materials')
    if await b.count():
        await b.first.scroll_into_view_if_needed(); await b.first.click(); await pg.wait_for_timeout(800)
    r = await js(pg, r"""() => { const chip = [...document.querySelectorAll('.view.on .gl, .view.on [data-tl]')].find(b => /Order This Week/.test(b.textContent));
      const m = chip ? chip.textContent.replace(/\s+/g, ' ').match(/Order This Week\s*(\d+)/) : null;
      const card = document.querySelector('#mat-week .week'); const h = card ? card.querySelector('h3').textContent : '';
      const hm = h.match(/(\d+)/);
      return { view, chip: m ? +m[1] : null, rows: card ? card.querySelectorAll('.it').length : 0, head: h, headN: hm ? +hm[1] : 0 }; }""")
    c.ok(r['chip'] is not None and r['chip'] == r['rows'] == r['headN'], f'CHIP {dev}: Order This Week on the chip equals the rows under it and the card\'s heading ({r})')
    await sign_in(pg, 'u_chen')


async def s_owed(pg, c, dev):
    await page(pg, 'po')
    await tap(pg, '[data-putile="owed"]', 500)
    r = await js(pg, r"""() => { const t = document.querySelector('[data-putile=owed] b').textContent;
      const rows = [...document.querySelectorAll('.view.on [data-pusec=tile] .pu-row b')].map(b => b.textContent);
      const sum = rows.map(x => (x.match(/\$([\d,]+(?:\.\d+)?)\s+(owed back|credit to confirm)/) || [0, '0'])[1]).reduce((a, x) => a + +String(x).replace(/,/g, ''), 0);
      return { tile: +t.replace(/[$,]/g, ''), sum, rows, claim: rows.some(x => /damaged on arrival|short on arrival|wrong on arrival/.test(x)) }; }""")
    c.ok(abs(r['tile'] - r['sum']) < 1.01 and r['claim'], f'OWED {dev}: Owed Back ${r["tile"]} equals the money its rows name (${r["sum"]}), and the claim on arrival is a row ({r["rows"]})')
    await js(pg, "() => { puShowAll.tile = ''; render(); }", None, 200)


async def s_vendors(pg, c, dev, phone):
    await page(pg, 'vendors')
    if not phone:
        th = await js(pg, "() => [...document.querySelectorAll('#v-vendors table.pu-vt thead th')].map(t => t.textContent.trim())")
        c.ok(th == ['Vendor', 'Open Orders', 'Owed Back', 'Insurance', 'W-9', 'Paid', 'On Time'], f'VENDORS {dev}: the list answers open orders, owed back, papers and paid ({th})')
    else:
        t = ' '.join(await js(pg, VIS, '#v-vendors [data-pusec=list] .pu-row'))
        c.ok('open order' in t and 'Owed back' in t and 'Insurance' in t and 'W-9' in t and 'Paid' in t, f'VENDORS {dev}: each phone row says open orders, owed back, insurance, W-9 and paid ({t[:200]!r})')
    ids = await js(pg, "() => DB.vendors.map(v => v.id)")
    bad = []
    for vid in ids:
        await page(pg, 'vendors')
        await tap(pg, f'[data-puopen="vend:{vid}"]' if phone else f'tr[data-puvend="{vid}"]', 500)
        ok = await js(pg, "id => ({ open: typeof vendOpen !== 'undefined' && vendOpen === id, name: (document.querySelector('#v-vendors .vr') || {}).innerText || '' })", vid, 0)
        nm = await js(pg, "id => DB.vendors.find(v => v.id === id).name", vid, 0)
        if not (ok['open'] and nm in ok['name']): bad.append(nm)
    c.ok(not bad, f'VENDORS {dev}: every row opens its record ({bad})')
    await page(pg, 'vendors')
    await tap(pg, '[data-puopen="vend:v2"]' if phone else 'tr[data-puvend="v2"]', 700)
    g = await js(pg, r"""() => { const g = document.getElementById('pu-vg'); if (!g) return null; const vr = document.querySelector('#v-vendors .vr');
      const cards = [...vr.querySelectorAll(':scope > .card')]; return { text: g.innerText.replace(/\s+/g, ' '), firstCard: cards[0] === g,
      th: [...g.querySelectorAll('thead th')].map(t => t.textContent.trim()) }; }""")
    c.ok(g and g['firstCard'] and all(k in g['text'] for k in ['Open Orders', 'Owed Back', 'Insurance', 'W-9', 'Price History']) and '$3,800 paid over PO-2026-044' in g['text'],
         f'VENDORS {dev}: the record opens on open orders, owed back (with what was paid over an order), insurance, W-9 and price history ({g and g["text"][:260]!r})')
    if not phone:
        c.ok(g and g['th'] == ['Item', 'Last', 'Best', 'Trend'], f'VENDORS {dev}: price history reads last, best and trend per item ({g and g["th"]})')
    await reset(pg)


async def s_stock(pg, c, dev):
    await page(pg, 'inv')
    rows = await js(pg, r"""() => [...document.querySelectorAll('.view.on [data-pusec=list] .pu-row')].map(r => ({ id: r.dataset.purow, t: r.innerText.replace(/\s+/g, ' ') }))""")
    c.ok(rows and all('on hand' in r['t'] for r in rows), f'STOCK {dev}: every row says what is on hand ({[r["t"] for r in rows if "on hand" not in r["t"]][:3]})')
    tape = next((r for r in rows if r['id'] == 'item:iv13'), None)
    c.ok(tape and 'Needed by' in tape['t'], f'STOCK {dev}: blue tape says the need that wants it ({tape})')
    bad = []
    for r in rows:
        await page(pg, 'inv')
        await tap(pg, f'[data-puopen="{r["id"]}"]', 500)
        nm = await js(pg, "id => { const i = DB.inventory.find(x => 'item:' + x.id === id); const d = document.getElementById('drawer'); return [i.name, d && d.classList.contains('on') ? d.innerText : '']; }", r['id'], 0)
        if nm[0] not in nm[1] and not await js(pg, "n => [...document.querySelectorAll('#drawer input')].some(i => i.value === n)", nm[0], 0): bad.append(nm[0])
        await reset(pg)
    c.ok(not bad, f'STOCK {dev}: every row opens its record ({bad})')
    # Deliveries: an item under an open claim on arrival is held at the office, not sent with the route
    await page(pg, 'recv')
    rng = await js(pg, r"""() => { const r = [...document.querySelectorAll('.view.on [data-pusec=office] .pu-row')].find(x => /Range, 36/.test(x.innerText)); return r ? r.innerText.replace(/\s+/g, ' ') : ''; }""")
    c.ok('Held' in rng and 'claim' in rng and 'deliver it with the route' not in rng, f'STOCK {dev}: Deliveries holds the damaged range at the office under its claim ({rng!r})')


async def s_field(pg, c, dev, phone):
    # an order due on site today, with a window and the office's note (planted on the seed's PO-2026-047)
    await js(pg, "() => { const po = DB.pos.find(p => p.number === 'PO-2026-047'); po.expected = today(); po.deliveryWindow = '7:00 AM - 9:00 AM'; po.notes = 'Curb drop, call Angel'; save(); }", None, 100)
    await sign_in(pg, 'u_angel')
    await page(pg, 'ftoday')
    row = await js(pg, r"""() => { const r = [...document.querySelectorAll('.f3-arriving .f3-row')].find(x => /PO-2026-047/.test(x.innerText)); return r ? r.innerText.replace(/\s+/g, ' ') : ''; }""")
    c.ok('900 sf' in row and 'flooring' in row and '7:00 AM' in row and 'job site' in row and 'Curb drop, call Angel' in row and '$' not in row,
         f'FIELD {dev}: the foreman\'s Arriving Today says what, when, where and the note, and no money ({row!r})')
    pad = await js(pg, r"""() => { const r = [...document.querySelectorAll('.view.on .f3-row.late')].filter(x => x.offsetParent);
      return r.map(x => { const t = x.querySelector('b'); return t ? Math.round(t.getBoundingClientRect().left - x.getBoundingClientRect().left) : 99; }); }""")
    c.ok(all(p >= 8 for p in pad), f'FIELD {dev}: a late row on Arriving Today keeps its title clear of the edge; the .f-row stripe is lane T1\'s (title offsets {pad})')
    # Today's header carries no flag by design (today_test); the site page does
    await page(pg, 'fsite')
    fl = await js(pg, "() => { const b = document.getElementById('rp-btn'); if (!b) return null; const r = b.getBoundingClientRect(); return [b.getAttribute('aria-label'), Math.round(r.width), Math.round(r.height)]; }")
    # its words ("Report an App Problem") are lane T1's; this lane checks its size
    c.ok(fl and fl[1] >= 44 and fl[2] >= 44, f'FIELD {dev}: the header flag is a 44px target ({fl})')
    if phone:
        await js(pg, "() => spCaptureModal({})", None, 600)
        sp = await js(pg, r"""() => { const m = document.getElementById('mbm'); const sel = m.querySelector('table.sp-lines [data-slf=key]');
          const td = sel && sel.closest('td'); const vis = e => e.getBoundingClientRect().width > 0;
          return { w: sel ? Math.round(sel.getBoundingClientRect().width) : 0, k: td ? td.dataset.k : '', blues: [...m.querySelectorAll('.btn.primary')].filter(vis).map(b => b.textContent.trim()) }; }""")
        c.ok(sp['w'] >= 300 and sp['k'] and sp['blues'] == ['Submit'], f'FIELD {dev}: the receipt split is one labelled column with one blue ({sp})')
        await reset(pg)
    # New Task on the order: the one task sheet, with the order, its vendor and its job
    await sign_in(pg, 'u_chen')
    await open_po(pg, 'PO-2026-047')
    await tap(pg, '#pu-potask', 700)
    nt = await js(pg, r"""() => { const m = document.getElementById('mbm'); if (!m) return null; const t = m.querySelector('[data-f=title]'), f = m.querySelector('[data-f=for]');
      return { h: (m.querySelector('.mbm-hd h3') || {}).textContent, title: t ? t.value : '', forText: f ? (f.selectedOptions[0] || {}).textContent : '', blues: [...document.querySelectorAll('.view.on .btn.primary')].filter(b => b.offsetParent).length }; }""")
    c.ok(nt and nt['h'] == 'New Task' and 'PO-2026-047' in nt['title'] and 'Tino' in nt['title'] and '121 State' in (nt['forText'] or ''), f'FIELD {dev}: New Task on the order opens the task sheet with the order, its vendor and its job ({nt})')
    await reset(pg)
    await sign_in(pg, 'u_alan')
    await reset(pg)
    await js(pg, "() => { let e, c; for (const cc of DB.clients) for (const x of cc.estimates || []) if (x.id === 'es1') { e = x; c = cc; } flowGo.doc(c, 'estimate', e)(); }", None, 800)
    await tap(pg, '.view.on [data-docact="pos"]', 900)
    await js(pg, "() => { try { mbCloseModal(); } catch (e) {} const t = document.getElementById('toast'); t && t.classList.remove('on'); }", None, 300)
    back = pg.locator('.view.on [data-docback]')
    if await back.count():
        await back.first.click(); await pg.wait_for_timeout(500)
    t = await js(pg, "() => { const t = document.getElementById('toast'); return t && t.classList.contains('on') ? t.textContent : ''; }")
    c.ok('Kept your changes' not in t, f'FIELD {dev}: leaving the estimate with nothing typed toasts nothing ({t!r})')
    await sign_in(pg, 'u_chen')


PLANT = r"""() => { const base = DB.pos.find(p => p.number === 'PO-2026-047'), out = {};
  const mk = (st, n, f) => { const po = JSON.parse(JSON.stringify(base)); po.id = 'pt' + n; po.number = 'PO-2026-9' + n; po.status = st;
    po.matchedTxns = []; po.issues = []; po.lines.forEach(l => { l.id = l.id + n; }); f && f(po); DB.pos.push(po); out[st] = po.id; };
  mk('draft', '01'); mk('pending', '02'); mk('partial', '03', po => po.lines.forEach(l => l.received = 300));
  mk('closed', '04', po => po.lines.forEach(l => l.received = l.qty)); mk('cancelled', '05');
  out.issued = base.id; out.received = DB.pos.find(p => p.number === 'PO-2026-041').id; out.over = DB.pos.find(p => p.number === 'PO-2026-044').id;
  save(); return out; }"""
SNAP = "() => JSON.stringify([DB.pos, DB.txns, DB.vendors, DB.bills || []])"
WRITES = r"""() => { const vis = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
  const d = document.getElementById('po-doc');
  return { btns: [...d.querySelectorAll('button')].filter(vis).map(b => b.textContent.trim()),
    fields: [...d.querySelectorAll('input, select, textarea')].filter(f => vis(f) && !f.disabled && !f.readOnly).map(f => f.dataset.p || f.dataset.f || f.dataset.lsp || f.name || f.type),
    links: [...d.querySelectorAll('a[data-match], a[data-unmatch], [data-rmline]')].filter(vis).length,
    blues: [...document.querySelectorAll('.view.on .btn.primary')].filter(vis).length,
    says: (document.getElementById('pu-ponext') || {}).innerText || '' }; }"""


async def s_states(pg, c, dev):
    ids = await js(pg, PLANT)
    # the coordinator: pending waits on the owner; paid over offers no Close PO; partly received materials has one blue
    await sign_in(pg, 'u_chen')
    for st in ['pending', 'over', 'partial']:
        await page(pg, 'po')
        await js(pg, "id => { poOpen = id; render(); }", ids[st], 700)
        w = await js(pg, WRITES)
        if st == 'pending':
            c.ok(w['blues'] == 0 and "Waiting on the owner's approval" in w['says'], f'STATES {dev} coordinator: a pending order has no blue and says it waits on the owner ({w["says"]!r}, blues {w["blues"]})')
        if st == 'over':
            c.ok('Close PO' not in w['btns'] and w['blues'] == 1, f'STATES {dev} coordinator: a paid-over order offers no Close PO ({w["btns"]})')
        if st == 'partial':
            t = await js(pg, "() => document.getElementById('pu-poh').innerText")
            c.ok(w['blues'] == 1 and 'Received 300 of 900' in t and 'Partly Received' in t, f'STATES {dev} coordinator: a partly received materials order reads 300 of 900 with one blue ({w["blues"]}, {t[:120]!r})')
    await page(pg, 'po')
    await js(pg, "() => { puFilter.po = 'all'; render(); }", None, 300)
    rows = await js(pg, "() => [...document.querySelectorAll('.view.on [data-pusec=orders] .pu-row b')].map(b => b.textContent)")
    c.ok(any('PO-2026-905' in r for r in rows), f'STATES {dev} coordinator: a cancelled order is under All ({len(rows)} rows)')
    funds = await js(pg, "() => [...document.querySelectorAll('#v-po [data-fundpo]')].filter(b => b.offsetParent).length")
    c.ok(funds == 0, f'STATES {dev} coordinator: Orders shows no Client Funds New PO beside the one New ({funds})')
    # the read-only seats: nothing on any order writes, and the functions refuse
    for uid in ['u_controller', 'u_billing']:
        await sign_in(pg, uid)
        for st in ['draft', 'pending', 'issued', 'partial', 'received', 'over', 'closed', 'cancelled']:
            await page(pg, 'po')
            await js(pg, "id => { poOpen = id; render(); }", ids[st], 700)
            w = await js(pg, WRITES)
            bad = [b for b in w['btns'] if b not in ('Print / PDF', 'Open the Bill', 'Mark Reviewed') and not b.startswith('EST-')]
            c.ok(not bad and not w['fields'] and not w['links'] and w['blues'] == 0 and 'Read only' in w['says'],
                 f'STATES {dev} {uid} {st}: nothing on the order writes (buttons {bad}, fields {w["fields"]}, links {w["links"]}, blues {w["blues"]})')
        before = await js(pg, SNAP)
        r = await js(pg, """id => { const po = DB.pos.find(p => p.id === id); const out = [];
          for (const a of ['receive', 'receivepartial', 'bill', 'close', 'cancel', 'approve', 'submit', 'email']) out.push(poAction(po, a));
          out.push(matchPO(po), newPODialog(), openVendor(null), puReceive(po), puNewPOFromLines(), billFromPO(po));
          const open = !!document.querySelector('#mbm .mbm-box') || document.getElementById('drawer').classList.contains('on');
          try { mbCloseModal(); } catch (e) {} try { closeEditor(); } catch (e) {}
          return { open, out: out.map(x => x === false) }; }""", ids['issued'], 500)
        after = await js(pg, SNAP)
        c.ok(before == after and not r['open'], f'STATES {dev} {uid}: the order, payment, receiving and vendor functions refuse and change nothing (sheet opened {r["open"]})')
        nv = await js(pg, "() => { view = 'vendors'; vendOpen = null; render(); const b = document.getElementById('btn-newvendor'); return !!(b && b.offsetParent); }", None, 300)
        c.ok(not nv, f'STATES {dev} {uid}: no New Vendor')
    await sign_in(pg, 'u_chen')


async def main():
    c = Checks()
    async with async_playwright() as p:
        for phone in DEVS:
            dev = 'phone' if phone else 'desktop'
            b, pg, errs = await open_app(p, phone)
            await sign_in(pg, 'u_chen')
            for k, fn in [('NEW', lambda: s_new(pg, c, dev)), ('RECORD', lambda: s_record(pg, c, dev, phone)), ('OWED', lambda: s_owed(pg, c, dev)),
                          ('VENDORS', lambda: s_vendors(pg, c, dev, phone)), ('STOCK', lambda: s_stock(pg, c, dev)), ('CHIP', lambda: s_chip(pg, c, dev)),
                          ('MENU', lambda: s_menu(pg, c, dev, phone)), ('FIELD', lambda: s_field(pg, c, dev, phone)), ('TAPS', lambda: s_taps(pg, c, dev) if phone else asyncio.sleep(0)), ('STATES', lambda: s_states(pg, c, dev))]:
                if not on(k): continue
                try:
                    await fn()
                except Exception as e:
                    c.ok(False, f'{k} {dev}: the step could not be done as the person ({str(e)[:240]})')
                    try: await reset(pg)
                    except Exception: pass
            c.ok(not errs, f'{dev}: no page errors ({errs[:3]})')
            await b.close()
    sys.exit(c.done())

asyncio.run(main())
