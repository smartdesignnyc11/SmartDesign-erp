"""pu_table_test: the item table on Purchasing (Alan, 11-06: "the purchasing modules should have columns: Invoice ie: FM1 /
Lead Time / Item # / Description / Qnty / Room ie:Primary Bathroom/Powder Room/Kitchen, etc / Budget Price / Purchased Price
/ Vendor / Status ie:purchased/pricing/delivered / Delivery Date"). Done as the coordinator through the screens, on the
desktop (1440x900) and the phone (390x844, touch). The table is a view of buyList's opt-in rows (src/puschedule.js), not a
store.

  TOGGLE   the Buy Board has a Needs / Table switch; Table shows Alan's eleven columns in his order; the job's Purchasing
           tab has the same switch and shows that job only
  FILL     every column fills from the records where the record has it: each FF&E item's FM number, SKU, room, vendor,
           lead; each order line's vendor, price and date; a contract line's ERP invoice and its estimate line below
  INVOICE  Alan, 11-06: "FM 1 is an invoice #": the client invoice that bills the item, a link that opens it; else the FM
           number as entered, not yet invoiced in the app; else Not invoiced, counted as bought and not billed only
           when the item was bought for the client
  STATUS   plain words: an issued order is purchased, a received one delivered, an approved selection needed, an
           installed one installed, a back-order backordered; nothing in the table body can be typed into
  SORT     each column header sorts its column up, then down, empties last both ways
  FILTER   the room filter's number equals the rows it shows, and each shown row is in that room; status and vendor too
  TIE      grouped by Invoice, each estimate line's header reads lineCommitment's budget and spent-and-on-order, and the
           items under it never add up to more; a single item on a line carries the line's budget; the money leaks show
           (Millwork's order $1,000 over its line, the windows billed $3,800 over their order); the totals strip equals
           the rows it sums; buyList with no options is buyList as it was
  OPEN     a row opens its record: an order row the order, a need row its sheet
  PICK     two needs picked show Request Quotes and Order, one blue between them; Request Quotes opens the request sheet
  EXPORT   CSV has the header and one row per row shown; the client FF&E schedule has no cost, the internal one does
  IMPORT   an invented sheet in Chen's shape ("FM1 - 1.Accessories and Hardware" section rows) imports into the job's
           FF&E items once (a second import adds nothing), with a toast that opens them
  PHONE    one card per item (description and room, status, vendor, delivery date, budget against purchased), no sideways
           scroll, every control 44px, the status chips wrap
  SCAN     the desktop at 1440: Invoice and Item # on one line, every sub-line one line, nothing scrolls sideways
Usage: python3 pu_table_test.py [--desktop|--phone] [--only TOGGLE,FILL,...] [--shots]
"""
import asyncio, os, re, sys
# this suite tests the Buy Board's own default and the remembered choice: no pinned view (tests/harness.py)
os.environ['SD_PU_VIEW'] = 'default'
from harness import *

ONLY = set(sys.argv[sys.argv.index('--only') + 1].split(',')) if '--only' in sys.argv else None
DEVS = [False] if '--desktop' in sys.argv else [True] if '--phone' in sys.argv else [False, True]
SHOTS = '--shots' in sys.argv
on = lambda k: not ONLY or k in ONLY
COLS = ['Invoice', 'Lead Time', 'Item #', 'Description', 'Qty', 'Room', 'Budget Price', 'Purchased Price', 'Vendor', 'Status', 'Delivery Date']
SHOT_DIR = os.path.join(ROOT, 'review', 'pu_table')

# invented demo data in the shape of the coordinator's sheet: a section row per FM package and category, then items
SHEET = '''Invoice,Lead Time,Item #,Description,Qnty,Room,Budget Price,Purchased Price,Vendor,Status,Delivery Date
FM1 - 1.Accessories and Hardware,,,,,,,,,,
FM1,3 weeks,TB-2210-SN,Towel bar 24in satin nickel,2,Powder Room,145,139,Atlantic Bath Supply,purchased,2026-09-24
FM1,21,RH-118-SN,Robe hook double,3,Primary Bathroom,38,,Atlantic Bath Supply,pricing,
FM1,21,RH-118-SN,Robe hook double,3,Primary Bathroom,38,,Atlantic Bath Supply,pricing,
FM1,21,RH-118-SN,Robe hook double,1,Guest Bath,38,,Atlantic Bath Supply,pricing,
FM1 - 2.Lighting,,,,,,,,,,
,6 wks,PL-4402,Pendant over island 14in,2,Kitchen,620,655,Lumen Row,delivered,2026-08-28
'''

VIS_TEXT = """(sel) => [...document.querySelectorAll(sel)].filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; }).map(e => (e.innerText || '').replace(/\\s+/g, ' ').trim())"""

TAPS = r"""(scope) => {
  const W = innerWidth, vis = e => { const r = e.getBoundingClientRect(); if (r.width < 1 || r.height < 1) return false;
    if (r.right <= 0 || r.left >= W) return false; const s = getComputedStyle(e);
    return s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity !== 0 && !e.closest('[hidden]'); };
  const root = document.querySelector(scope); if (!root) return { n: 0, small: ['no ' + scope], side: 0 };
  const T = [];
  root.querySelectorAll('button, a[href], input:not([type=hidden]), select, textarea, [role=button]').forEach(e => {
    if (!vis(e)) return;
    let r = e.getBoundingClientRect();
    if (e.type === 'checkbox' || e.type === 'radio') { const lab = e.closest('label'); if (lab && vis(lab)) r = lab.getBoundingClientRect(); }
    T.push({ e, r, d: e.tagName.toLowerCase() + ' "' + (e.getAttribute('aria-label') || e.innerText || e.value || '').replace(/\s+/g, ' ').trim().slice(0, 30) + '"' });
  });
  const small = T.filter(t => t.r.width < 43.5 || t.r.height < 43.5).map(t => `${t.d} ${Math.round(t.r.width)}x${Math.round(t.r.height)}`);
  const close = [];
  for (let i = 0; i < T.length; i++) for (let j = i + 1; j < T.length; j++) {
    const a = T[i], b = T[j]; if (a.e.contains(b.e) || b.e.contains(a.e)) continue;
    const dx = Math.max(0, Math.max(a.r.left, b.r.left) - Math.min(a.r.right, b.r.right)), dy = Math.max(0, Math.max(a.r.top, b.r.top) - Math.min(a.r.bottom, b.r.bottom));
    if ((dx < 8 && dy === 0) || (dy < 8 && dx === 0)) close.push(`${a.d} | ${b.d}`);
  }
  const se = document.scrollingElement;
  return { n: T.length, small, close: close.slice(0, 8), side: se.scrollWidth - se.clientWidth };
}"""


async def js(pg, code, arg=None, wait=300):
    r = await (pg.evaluate(code, arg) if arg is not None else pg.evaluate(code))
    await pg.wait_for_timeout(wait)
    return r


async def reset(pg):
    await js(pg, """() => { try { for (let i = 0; i < 4; i++) if (document.querySelector('#mbm .mbm-box')) mbCloseModal(); } catch (e) {}
      try { poOpen = null; } catch (e) {} try { bbProj = ''; bbVendor = ''; bbTrade = ''; bbPick.clear(); } catch (e) {}
      try { psReset(); } catch (e) {} }""", None, 120)


async def board(pg, table=True):
    await reset(pg)
    await js(pg, "() => { view = 'proc'; render(); document.scrollingElement.scrollTop = 0; }", None, 450)
    b = pg.locator('.ps-modes [data-psmode="%s"]' % ('table' if table else 'needs'))
    if await b.count() and await b.first.get_attribute('aria-pressed') != 'true':
        await b.first.click()
        await pg.wait_for_timeout(500)


async def rows(pg):
    """the rows on screen, each as {id, cells: {col: text}, sv: {col: sort value}}"""
    return await js(pg, """() => [...document.querySelectorAll('#pu-table [data-psrow]')].filter(e => e.getBoundingClientRect().height > 0).map(tr => ({
      id: tr.dataset.psrow, cells: Object.fromEntries([...tr.querySelectorAll('[data-pscol]')].map(td => [td.dataset.pscol, (td.innerText || '').replace(/\\s+/g, ' ').trim()])),
      sv: Object.fromEntries([...tr.querySelectorAll('[data-pscol]')].map(td => [td.dataset.pscol, td.dataset.sv])) }))""", None, 0)


def cmp_key(v):
    """numbers as numbers; text as a person reads it (FM8 before FM12), as the task list's sort does"""
    if v is None or v == '': return None
    try: return (0, float(v))
    except ValueError: return (1, tuple((0, int(t), '') if t.isdigit() else (1, 0, t) for t in re.split(r'(\d+)', v.lower()) if t))


def monotone(vals, desc=False):
    keys = [cmp_key(v) for v in vals]
    full = [k for k in keys if k is not None]
    # empties last, both ways
    if None in keys and any(k is not None for k in keys[keys.index(None):]): return False
    if any(a[0] != b[0] for a, b in zip(full, full[1:])): return all(a[0] <= b[0] for a, b in zip(full, full[1:]))
    return all((a >= b) if desc else (a <= b) for a, b in zip(full, full[1:]))


async def s_toggle(pg, c, dev):
    # the default: the Table on the desktop, Needs on the phone (CoS 11-06)
    await reset(pg)
    await js(pg, "() => { view = 'proc'; render(); }", None, 450)
    shown = await js(pg, "() => document.querySelector('#pu-table') ? 'table' : document.querySelector('#buy-board') ? 'needs' : ''", None, 0)
    c.ok(shown == ('table' if dev == 'desktop' else 'needs'), f'TOGGLE {dev}: the Buy Board opens on {"the Table" if dev == "desktop" else "Needs"} ({shown})')
    modes = await js(pg, VIS_TEXT, '.ps-modes [data-psmode]', 0)
    c.ok(len(modes) == 2 and modes[0].startswith('Needs') and modes[1] == 'Table', f'TOGGLE {dev}: the Buy Board has Needs and Table ({modes})')
    # Needs carries the Buy Board's number: the menu's (Needs You)
    nb = await js(pg, """() => ({ sw: +((document.querySelector('.ps-modes [data-psmode=needs] .n') || {}).textContent || 0), badge: puCount('proc'),
      marked: !!document.querySelector('.ps-modes [data-ocbadge=proc]') })""", None, 0)
    c.ok(nb['sw'] == nb['badge'] and (nb['badge'] == 0 or nb['marked']), f'TOGGLE {dev}: the Needs switch shows the menu\'s number, Needs You ({nb})')
    # the last choice is remembered on this layout, across a reload
    other = 'needs' if dev == 'desktop' else 'table'
    await pg.locator(f'.ps-modes [data-psmode="{other}"]').first.click()
    await pg.wait_for_timeout(400)
    await pg.reload(); await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
    await sign_in(pg, 'u_chen')
    await js(pg, "() => { view = 'proc'; render(); }", None, 450)
    kept = await js(pg, "() => document.querySelector('#pu-table') ? 'table' : document.querySelector('#buy-board') ? 'needs' : ''", None, 0)
    c.ok(kept == other, f'TOGGLE {dev}: the choice is remembered after a reload ({kept}, chose {other})')
    await board(pg)
    if dev == 'desktop':
        heads = await js(pg, VIS_TEXT, '#pu-table thead th[data-pscol]', 0)
        c.ok(heads == COLS, f'TOGGLE {dev}: the Table carries Alan\'s columns in his order ({heads})')
    else:
        heads = await js(pg, "() => [...document.querySelectorAll('#pu-table [data-pssort]')].map(b => b.dataset.pssort)", None, 0)
        c.ok(len(heads) >= 6, f'TOGGLE {dev}: the phone has a Sort control over the same columns ({heads})')
    n = len(await rows(pg))
    want = await js(pg, "() => psItems('').length", None, 0)
    c.ok(n > 0 and n == want, f'TOGGLE {dev}: one row per item ({n} shown, {want} items)')
    h = await js(pg, VIS_TEXT, '#v-proc h2', 0)
    c.ok(dev == 'phone' or (h and h[0] == 'Buy Board'), f'TOGGLE {dev}: the page heading stays Buy Board ({h[:1]})')
    # the job's Purchasing tab: the same switch, that job only
    await reset(pg)
    await js(pg, "() => { jpOpenJob('p121', 'proc'); }", None, 600)
    b = pg.locator('.ps-modes [data-psmode="table"]')
    has = await b.count()
    c.ok(has > 0, f'TOGGLE {dev}: the job\'s Purchasing tab has the Table switch')
    if has:
        await b.first.click(); await pg.wait_for_timeout(500)
        R = await rows(pg)
        jobs = await js(pg, "ids => ids.map(id => (psItems('').find(x => x.id === id) || {}).pid)", [r['id'] for r in R], 0)
        c.ok(R and set(jobs) == {'p121'}, f'TOGGLE {dev}: inside 121 State the table shows that job only ({set(jobs)})')
    await js(pg, "() => { try { jpClose && jpClose(); } catch (e) {} }", None, 100)
    # the controller reads the table and buys nothing from it: no pick box, no import
    await sign_in(pg, 'u_controller')
    await board(pg)
    ro = await js(pg, "() => ({ rows: document.querySelectorAll('#pu-table [data-psrow]').length, picks: document.querySelectorAll('#pu-table [data-pspick]').length, imp: document.querySelectorAll('#pu-table [data-psx=import]').length })", None, 0)
    c.ok(ro['rows'] > 0 and ro['picks'] == 0 and ro['imp'] == 0, f'TOGGLE {dev}: the controller reads the table with no pick box and no import ({ro})')
    await sign_in(pg, 'u_chen')


async def s_fill(pg, c, dev):
    await board(pg)
    R = await rows(pg)
    by = {r['id']: r for r in R}
    model = await js(pg, """() => psItems('').map(x => ({ id: x.id, src: x.src }))""", None, 0)
    # every column fills where its record has the value
    blanks = []
    for m in model:
        r = by.get(m['id'])
        if not r: blanks.append(f"{m['id']} not shown"); continue
        for col, has in m['src'].items():
            if has and not r['cells'].get(col): blanks.append(f"{m['id']}.{col}")
    c.ok(not blanks, f'FILL {dev}: no blank cell where the record has the value ({blanks[:8]})')
    # independent of the model: the FF&E items
    S = await js(pg, "() => DB.sel.items.map(i => ({ id: i.id, name: i.name, fm: i.fm || '', sku: i.sku || '', room: i.room || '', vendor: i.vendor || '', lead: +i.leadDays || 0 }))", None, 0)
    miss = []
    for s in S:
        r = next((x for x in R if s['name'] in x['cells'].get('desc', '')), None)
        if not r: miss.append(f"{s['name']}: no row"); continue
        cl = r['cells']
        if s['fm'] and not cl.get('inv', '').startswith(s['fm']): miss.append(f"{s['name']}: invoice {cl.get('inv')!r} not {s['fm']}")
        if s['sku'] and s['sku'] not in cl.get('sku', ''): miss.append(f"{s['name']}: item # {cl.get('sku')!r}")
        if s['room'] and s['room'].lower() not in cl.get('room', '').lower(): miss.append(f"{s['name']}: room {cl.get('room')!r}")
        if s['vendor'] and s['vendor'] not in cl.get('vendor', ''): miss.append(f"{s['name']}: vendor {cl.get('vendor')!r}")
        if s['lead'] and not re.search(r'\d', cl.get('lead', '')): miss.append(f"{s['name']}: lead {cl.get('lead')!r}")
    c.ok(not miss, f'FILL {dev}: every FF&E item shows its FM package, item #, room, vendor and lead ({miss[:6]})')
    # every order line, at its order's price, vendor and date
    P = await js(pg, """() => DB.pos.filter(p => p.status !== 'cancelled').flatMap(p => (p.lines || []).map(l => ({ n: p.number, item: l.item || l.desc || '', vendor: p.vendor || '',
      // the order line on the budget's basis: before tax, its share of the order's freight in
      ext: Math.round((+l.qty || 0) * (+l.price || 0) * (1 + (+p.shipping || 0) / Math.max(1, poTotal(p).sub))), date: p.receivedOn || p.expected || '' })))""", None, 0)
    miss = []
    for l in P:
        r = next((x for x in R if l['item'][:24] in x['cells'].get('desc', '')), None)
        if not r: miss.append(f"{l['n']} {l['item']}: no row"); continue
        cl = r['cells']
        if l['vendor'] not in cl.get('vendor', ''): miss.append(f"{l['n']}: vendor {cl.get('vendor')!r}")
        if f"${l['ext']:,}" not in cl.get('bought', ''): miss.append(f"{l['n']}: purchased {cl.get('bought')!r} lacks ${l['ext']:,}")
        if l['date'] and not re.search(r'\d+/\d+', cl.get('deliv', '')): miss.append(f"{l['n']}: delivery {cl.get('deliv')!r}")
        if l['n'] not in r['cells'].get('bought', '') + r['cells'].get('status', ''): miss.append(f"{l['n']}: the order number is not on its row")
    c.ok(not miss and P, f'FILL {dev}: every order line shows its vendor, price, order number and date ({miss[:6]})')
    # a contract line's ERP invoice (no FM package) and its estimate line under it
    mill = next((x for x in R if 'Parlor kitchen + laundry millwork' in x['cells'].get('desc', '')), None)
    inv = await js(pg, "() => (lineFin('estimate:es1:l9').invoices || []).slice(-1)[0] || ''", None, 0)
    c.ok(mill and inv and inv in mill['cells'].get('inv', '') and 'EST-2026-014 line 9' in mill['cells'].get('inv', ''),
         f'FILL {dev}: the millwork order reads its ERP invoice ({inv}) with EST-2026-014 line 9 under it ({mill and mill["cells"].get("inv")!r})')


async def s_invoice(pg, c, dev):
    """Alan, 11-06: "FM 1 is an invoice #". The client invoice that bills the item, opened from the cell; else the FM
    number as entered, not yet invoiced in the app; else Not invoiced, which flags a bought-for-the-client item."""
    await board(pg)
    R = await rows(pg)
    cell = lambda frag: next((x['cells'].get('inv', '') for x in R if frag in x['cells'].get('desc', '')), None)
    fm = cell('Range, 36')
    c.ok(fm and fm.startswith('FM12') and 'not yet invoiced' in fm.lower(), f'INVOICE {dev}: a selection with an FM number and no invoice line reads FM12, not yet invoiced in the app ({fm!r})')
    # an invoice line naming the selection: that invoice's number, as a link that opens it
    await js(pg, """() => { const it = DB.sel.items.find(i => i.name.startsWith('Range, 36')), c = DB.clients.find(x => x.invoices.some(i => i.number === 'INV-2026-038'));
      const inv = c.invoices.find(i => i.number === 'INV-2026-038'); inv.lines.push({ id: 'l_pstest', item: 'Range, 36in dual fuel', qty: 1, unit: 'ea', rate: 9889, selId: it.id }); render(); }""", None, 400)
    R = await rows(pg)
    rid = next((x['id'] for x in R if 'Range, 36' in x['cells'].get('desc', '')), '')
    v = next((x['cells'].get('inv', '') for x in R if x['id'] == rid), '')
    c.ok(v.startswith('INV-2026-038'), f'INVOICE {dev}: once an invoice line names the selection, the cell reads that invoice\'s number ({v!r})')
    link = pg.locator(f'#pu-table [data-psrow="{rid}"] [data-psinv]')
    has = await link.count()
    if has:
        await link.first.click(); await pg.wait_for_timeout(700)
        # flowGo.doc: a seat with Billing or Clients opens the document; any other seat (the coordinator) its summary
        st = await js(pg, """() => ({ view, doc: typeof docOpen !== 'undefined' && docOpen ? docOpen.id : '',
          sheet: ((document.querySelector('#mbm .mbm-hd h3') || {}).textContent || '').trim() })""", None, 0)
        inv_id = await js(pg, "() => DB.clients.flatMap(c => c.invoices).find(i => i.number === 'INV-2026-038').id", None, 0)
        c.ok(st['doc'] == inv_id or 'INV-2026-038' in st['sheet'], f'INVOICE {dev}: the number opens INV-2026-038 ({st})')
        await reset(pg)
    else: c.ok(False, f'INVOICE {dev}: the invoice number is a link')
    await js(pg, """() => { const inv = DB.clients.flatMap(c => c.invoices).find(i => i.number === 'INV-2026-038'); inv.lines = inv.lines.filter(l => l.id !== 'l_pstest'); }""", None, 0)
    # neither an invoice nor an FM number: Not invoiced
    await board(pg)
    await js(pg, "() => { const it = DB.sel.items.find(i => i.name.startsWith('Range, 36')); it.__fm = it.fm; it.fm = ''; render(); }", None, 400)
    R = await rows(pg)
    v = next((x['cells'].get('inv', '') for x in R if 'Range, 36' in x['cells'].get('desc', '')), '')
    c.ok(v.startswith('Not invoiced'), f'INVOICE {dev}: with neither, the cell reads Not invoiced ({v!r})')
    await js(pg, "() => { const it = DB.sel.items.find(i => i.name.startsWith('Range, 36')); it.fm = it.__fm; delete it.__fm; render(); }", None, 300)
    # bought for the client and not billed back is the one bill-back reading (rbRows): an order line marked billed back,
    # with its bill on file and on no invoice, is flagged on its row and counted once, as Billing counts it
    n0 = await js(pg, "() => rbRows('').filter(r => r.kind === 'reimbursable').length", None, 0)
    await js(pg, """() => { const po = DB.pos.find(p => p.number === 'PO-2026-041'), b = DB.bills.find(x => x.poId === po.id);
      po.lines[0].billable = true; b.lines[0].__pl = b.lines[0].poLineId; b.lines[0].poLineId = po.lines[0].id; render(); }""", None, 500)
    R = await rows(pg)
    v = next((x['cells'].get('inv', '') for x in R if 'Calacatta' in x['cells'].get('desc', '') or 'Tile – primary bath' in x['cells'].get('desc', '')), '')
    st = await js(pg, "() => ({ strip: +((document.querySelector('[data-pstot=notbilled]') || {}).dataset || {}).v || 0, rb: rbRows('').filter(r => r.kind === 'reimbursable').length })", None, 0)
    c.ok('not billed back' in v.lower() and st['strip'] == st['rb'] == n0 + 1, f'INVOICE {dev}: a billed-back order line not on an invoice is flagged, and the strip is rbRows\'s count ({v!r}; {st}, was {n0})')
    await js(pg, """() => { const po = DB.pos.find(p => p.number === 'PO-2026-041'), b = DB.bills.find(x => x.poId === po.id);
      delete po.lines[0].billable; b.lines[0].poLineId = b.lines[0].__pl; delete b.lines[0].__pl; render(); }""", None, 300)


async def s_status(pg, c, dev):
    await board(pg)
    R = await rows(pg)
    st = lambda frag: next((x['cells'].get('status', '') for x in R if frag in x['cells'].get('desc', '')), None)
    inst = await js(pg, "() => (DB.sel.items.find(i => i.stage === 'inst' && !(DB.sel.returns || []).some(r => r.itemId === i.id)) || {}).name || ''", None, 0)
    ret = await js(pg, "() => (DB.sel.items.find(i => (DB.sel.returns || []).some(r => r.itemId === i.id && !['cancelled', 'rejected'].includes(r.status))) || {}).name || ''", None, 0)
    want = [('Parlor kitchen + laundry millwork', 'purchased'), ('Double-hung windows', 'delivered'), ('Wall-mount lavatory faucet', 'needed'),
            (inst, 'installed'), (ret, 'returned'), ('Picture light', 'selecting')]
    bad = [(f, st(f)) for f, w in want if not (st(f) or '').lower().startswith(w)]
    c.ok(not bad, f'STATUS {dev}: plain-word status on each kind of item ({bad})')
    lead = next((x['cells'].get('lead', '') for x in R if 'Wall-mount lavatory faucet' in x['cells'].get('desc', '')), '')
    c.ok('passed' in lead, f'STATUS {dev}: a lead time whose order-by date has passed says so, in red ({lead!r})')
    tape = next((x['cells'].get('status', '') for x in R if 'Blue tape' in x['cells'].get('desc', '')), '')
    c.ok('At the warehouse' in tape, f'STATUS {dev}: a need the shop holds says what is on the shelf, as the Buy Board does ({tape!r})')
    # a second buy of the tile at $14.50 against the $12.50 paid on PO-2026-041: the PO page's price check, on the row
    await js(pg, """() => { DB.pos.push({ id: 'po_pstest', number: 'PO-2026-099', projectId: 'p121', vendor: 'Nemo Tile', date: '2026-09-02', expected: '2026-09-10', status: 'issued',
      lines: [{ id: 'pl_pstest', item: 'Calacatta porcelain 12x24', qty: 100, unit: 'sf', price: 14.5, line: 'estimate:es1:l7', received: 0 }], receipts: [] }); save(); render(); }""", None, 600)
    R2 = await rows(pg)
    up = next((x['cells'].get('bought', '') for x in R2 if x['id'] and 'Calacatta' in x['cells'].get('desc', '') and 'PO-2026-099' in x['cells'].get('bought', '')), '')
    c.ok('Up from $12.50' in up, f'STATUS {dev}: a price above what was paid before says so, as the order\'s price check does ({up!r})')
    await js(pg, "() => { DB.pos = DB.pos.filter(p => p.id !== 'po_pstest'); save(); render(); }", None, 400)
    typed = await js(pg, "() => [...document.querySelectorAll('#pu-table tbody input:not([type=checkbox]), #pu-table tbody select, #pu-table tbody textarea, #pu-table [contenteditable=true]')].length", None, 0)
    c.ok(typed == 0, f'STATUS {dev}: nothing in the table can be typed into: price and status change through Order and Receive ({typed})')
    # a back-order reported on an order reads backordered
    await js(pg, """() => { const po = DB.pos.find(p => p.number === 'PO-2026-047'); po.lines[0].backordered = 900; po.lines[0].issue = 'backorder'; render(); }""", None, 400)
    R = await rows(pg)
    b = next((x['cells'].get('status', '') for x in R if 'oak flooring' in x['cells'].get('desc', '').lower()), '')
    c.ok(b.lower().startswith('backordered'), f'STATUS {dev}: a back-ordered line reads backordered ({b!r})')
    await js(pg, """() => { const po = DB.pos.find(p => p.number === 'PO-2026-047'); delete po.lines[0].backordered; delete po.lines[0].issue; render(); }""", None, 200)


async def s_sort(pg, c, dev):
    await board(pg)
    await js(pg, "() => psSet({ group: 'none' })", None, 400)   # grouped, a sort orders the rows inside each group
    keys = await js(pg, "() => PS_COLS.map(x => x.k)", None, 0)
    bad = []
    for k in keys:
        for d in ('asc', 'desc'):
            await js(pg, "([k, d]) => psSortBy(k, d)", [k, d], 350) if dev == 'phone' else None
            if dev == 'desktop':
                await pg.locator(f'#pu-table thead [data-pssort="{k}"]').first.click()
                await pg.wait_for_timeout(350)
            vals = [r['sv'].get(k) for r in await rows(pg)]
            if not monotone(vals, d == 'desc'): bad.append(f'{k} {d}: {vals[:6]}')
    c.ok(not bad, f'SORT {dev}: each of the {len(keys)} columns sorts up and down, empties last ({bad[:4]})')
    if dev == 'desktop':
        aria = await js(pg, "() => (document.querySelector('#pu-table thead th[aria-sort=descending]') || {}).dataset", None, 0)
        c.ok(aria is not None, 'SORT desktop: the sorted header says so (aria-sort)')


async def s_filter(pg, c, dev):
    await board(pg)
    if dev == 'phone':   # the phone keeps the filters behind one button; the status chips stay out
        await pg.locator('[data-pstools]').first.click()
        await pg.wait_for_timeout(400)
    for sel, col in (('#ps-room', 'room'), ('#ps-status', 'status'), ('#ps-vendor', 'vendor')):
        chips = dev == 'phone' and sel == '#ps-status'   # the phone's status filter is a row of chips
        q = '[data-psst]' if chips else f'{sel} option'
        opts = await js(pg, f"() => [...document.querySelectorAll('{q}')].map(o => [o.value !== undefined && o.tagName === 'OPTION' ? o.value : o.dataset.psst, o.textContent]).filter(o => o[0])", None, 0)
        bad = []
        for v, label in opts:
            if chips: await pg.locator(f'[data-psst="{v}"]').first.click()
            else: await pg.select_option(sel, v)
            await pg.wait_for_timeout(350)
            R = await rows(pg)
            n = await js(pg, "() => +(document.querySelector('[data-pscount]') || {}).dataset.pscount", None, 0)
            m = re.search(r'\((\d+)\)', label)
            word = re.sub(r'\s*\(\d+\)\s*$', '', label).strip()
            cell = lambda r: (r['cells'].get(col) or '').lower()
            wrong = [r['cells'].get(col) for r in R if not ((cell(r) == '') if word in ('No room', 'No vendor') else cell(r).startswith(word.lower()) if col == 'status' else word.lower() in cell(r))]
            if n != len(R) or (m and int(m.group(1)) != len(R)) or wrong: bad.append(f'{v}: count {n}, option {label!r}, rows {len(R)}, off {wrong[:2]}')
        if chips: await pg.locator('[data-psst=""]').first.click()
        else: await pg.select_option(sel, '')
        await pg.wait_for_timeout(250)
        c.ok(opts and not bad, f'FILTER {dev}: {sel[4:]}: the count equals the rows it shows, every row in it ({len(opts)} options; {bad[:3]})')


async def s_tie(pg, c, dev):
    await board(pg)
    await js(pg, "() => psSet({ group: 'inv' })", None, 450)
    G = await js(pg, """() => [...document.querySelectorAll('#pu-table [data-psgroup][data-pskey]')].map(g => ({ key: g.dataset.pskey, b: +g.dataset.psbudget, u: +g.dataset.psused,
      items: +g.dataset.psitems }))""", None, 0)
    bad = []
    for g in G:
        lc = await js(pg, "k => { const c = lineCommitment(k); return c ? { b: c.budget, u: c.used } : null; }", g['key'], 0)
        if not lc or abs(lc['b'] - g['b']) > 0.5 or abs(lc['u'] - g['u']) > 0.5: bad.append(f"{g['key']}: header {g['b']}/{g['u']} vs lineCommitment {lc}")
        if g['items'] > g['u'] + 1: bad.append(f"{g['key']}: items {g['items']} over spent-and-on-order {g['u']}")
    c.ok(G and not bad, f'TIE {dev}: each estimate line\'s header is lineCommitment\'s budget and spent-and-on-order; its items never add up to more ({len(G)} lines; {bad[:3]})')
    sole = await js(pg, """() => psItems('').filter(x => x.budgetFrom === 'line').map(x => ({ id: x.id, k: x.lineKey, b: x.budget, c: (lineCommitment(x.lineKey) || {}).budget }))""", None, 0)
    off = [s for s in sole if abs((s['b'] or 0) - (s['c'] or 0)) > 0.5]
    c.ok(sole and not off, f'TIE {dev}: an item alone on its line carries the line\'s budget ({len(sole)} items; {off[:3]})')
    await js(pg, "() => psSet({ group: 'room' })", None, 400)
    R = await rows(pg)
    cellof = lambda frag: next((x['cells'].get('bought', '') for x in R if frag in x['cells'].get('desc', '')), '')
    ov = await js(pg, "() => puOverOrder('').map(o => ({ n: o.po.number, over: Math.round(o.over) }))", None, 0)
    lc9 = await js(pg, "() => Math.round(lineCommitment('estimate:es1:l9').over)", None, 0)
    win = cellof('Double-hung windows')
    c.ok(any(o['n'] == 'PO-2026-044' for o in ov) and all(f"${o['over']:,} over {o['n']}" in ' '.join(x['cells'].get('bought', '') for x in R) for o in ov),
         f'TIE {dev}: every order over its total reads the Orders page\'s Over the Order, the same dollars ({ov}; windows {win!r})')
    mill = cellof('Parlor kitchen + laundry millwork')
    c.ok(lc9 == 1000 and re.search(r'\$%s over( budget| its budget)' % f'{lc9:,}', mill), f'TIE {dev}: the millwork reads Over the Line, ${lc9:,} ({mill!r})')
    tile = cellof('Tile – primary bath') or cellof('Calacatta')
    c.ok(tile and 'over' not in tile.lower(), f'TIE {dev}: the tile order and its bill are on one basis, freight in: not over ({tile!r})')
    t = await js(pg, """() => { const T = {}; document.querySelectorAll('[data-pstot]').forEach(e => T[e.dataset.pstot] = +e.dataset.v); return T; }""", None, 0)
    sums = await js(pg, """() => { const R = psView().rows, lines = new Map(), pos = new Map(); let b = 0, p = 0, o = 0;
      // a line's budget and its Over the Line once (lineCommitment's), a selection's own budget and gap each, an order's
      // Over the Order once (puOverOrder's)
      R.forEach(x => { if (x.budgetFrom === 'line' || x.shared) lines.set(x.lineKey, lineCommitment(x.lineKey)); else if (x.budget != null) { b += x.budget; o += x.over || 0; }
        if (x.bought != null) p += x.bought; });
      const OV = new Map(puOverOrder('').map(v => [v.po.id, v.over]));
      R.forEach(x => (x.pos || []).forEach(po => OV.has(po.id) && pos.set(po.id, OV.get(po.id))));
      lines.forEach(cc => { b += cc.budget; o += cc.over > 0.5 ? cc.over : 0; });
      return { budget: Math.round(b), bought: Math.round(p), over: Math.round(o), poover: Math.round([...pos.values()].reduce((a, v) => a + v, 0)),
        notbilled: rbRows('').filter(r => r.kind === 'reimbursable').length }; }""", None, 0)
    off = [k for k in ('budget', 'bought', 'over', 'poover', 'notbilled') if abs(round(t.get(k, 0)) - sums[k]) > 1]
    c.ok(not off, f'TIE {dev}: the totals strip is the rows it sums, on the shared rules ({ {k: (t.get(k, 0), sums[k]) for k in off} })')
    same = await js(pg, "() => JSON.stringify(buyList('').map(r => r.id)) === JSON.stringify(psBuyListBase('').map(r => r.id)) && buyList('').length === psBuyListBase('').length", None, 0)
    c.ok(same, f'TIE {dev}: buyList with no options is unchanged (the opt-in adds rows only when asked)')


async def s_open(pg, c, dev):
    await board(pg)
    po = await js(pg, "() => DB.pos.find(p => p.number === 'PO-2026-048').id", None, 0)
    rid = await js(pg, "() => (psItems('').find(x => x.po && x.po.number === 'PO-2026-048') || {}).id", None, 0)
    await pg.locator(f'#pu-table [data-psrow="{rid}"] [data-psopen]').first.click()
    await pg.wait_for_timeout(700)
    st = await js(pg, "() => ({ view, poOpen })", None, 0)
    c.ok(st['view'] == 'po' and st['poOpen'] == po, f'OPEN {dev}: the millwork row opens PO-2026-048 ({st})')
    await board(pg)
    nid = await js(pg, "() => (psItems('').find(x => x.r && !x.r.ordered && x.r.kind === 'material') || {}).id", None, 0)
    await pg.locator(f'#pu-table [data-psrow="{nid}"] [data-psopen]').first.click()
    await pg.wait_for_timeout(600)
    m = await js(pg, "() => !!document.querySelector('#mbm .bb-sheet')", None, 0)
    c.ok(m, f'OPEN {dev}: a need row opens the need\'s sheet')
    await reset(pg)


async def s_pick(pg, c, dev):
    await board(pg)
    ids = await js(pg, """() => psItems('').filter(x => x.pickable && x.pid === 'p121' && x.r.kind === 'material' && x.lineKey && !x.r.dec).slice(0, 2).map(x => x.id)""", None, 0)
    for i in ids:
        await pg.locator(f'#pu-table [data-psrow="{i}"] [data-pspick]').first.click()
        await pg.wait_for_timeout(350)
    bar = await js(pg, VIS_TEXT, '#pu-table .ps-bar button', 0)
    blue = await js(pg, "() => [...document.querySelectorAll('.view.on .btn.primary')].filter(e => e.getBoundingClientRect().width > 0).map(e => e.innerText.trim())", None, 0)
    c.ok(len(ids) == 2 and any(b.startswith('Request Quotes') for b in bar) and any(b.startswith('Order') for b in bar) and len(blue) == 1,
         f'PICK {dev}: two needs picked show Request Quotes and Order, one blue ({bar}, blue {blue})')
    q = pg.locator('#pu-table .ps-bar [data-psdo="quote"]')
    if await q.count():
        await q.first.click(); await pg.wait_for_timeout(900)
        t = await js(pg, "() => { const h = document.querySelector('#mbm .mbm-hd h3'); return h ? h.textContent.trim() : ''; }", None, 0)
        c.ok(bool(t), f'PICK {dev}: Request Quotes opens the request sheet on those lines ({t!r})')
    await reset(pg)


async def s_export(pg, c, dev):
    await board(pg)
    n = len(await rows(pg))
    async with pg.expect_download() as d:
        await pg.locator('#pu-table [data-psx="csv"]').first.click()
    dl = await d.value
    path = await dl.path()
    text = open(path, encoding='utf-8').read().strip().split('\n')
    head = text[0].split(',')
    c.ok(head[:11] == COLS and len(text) - 1 == n, f'EXPORT {dev}: the CSV has the columns and one row per row shown ({head[:11]}, {len(text) - 1} of {n})')
    client = await js(pg, "() => psScheduleHtml(true)", None, 0)
    inner = await js(pg, "() => psScheduleHtml(false)", None, 0)
    c.ok('$' not in re.sub(r'<style[\s\S]*?</style>', '', client) and 'Budget' not in client and 'Purchased Price' not in client,
         f'EXPORT {dev}: the client FF&E schedule shows no cost')
    c.ok('Budget' in inner and 'Purchased' in inner and '$' in inner, f'EXPORT {dev}: the internal schedule shows budget and purchased')
    async with pg.context.expect_page() as pp:
        await pg.locator('#pu-table [data-psx="client"]').first.click()
    w = await pp.value
    await w.wait_for_load_state()
    body = await w.inner_text('body')
    c.ok('FF&E Schedule' in body and '$' not in body, f'EXPORT {dev}: Client FF&E Schedule opens a printable page with no cost')
    await w.close()


async def s_import(pg, c, dev):
    await board(pg)
    n0 = await js(pg, "() => DB.sel.items.filter(i => i.projectId === 'p121').length", None, 0)
    a0 = await js(pg, "() => DB.audit.length", None, 0)
    await pg.locator('#pu-table [data-psx="import"]').first.click()
    await pg.wait_for_timeout(500)
    await pg.select_option('#ps-imp-job', 'p121')
    await pg.fill('#ps-imp-text', SHEET)
    await pg.wait_for_timeout(500)
    prev = await js(pg, VIS_TEXT, '#mbm .ps-imp-row', 0)
    summ = await js(pg, "() => (document.querySelector('#mbm .ps-imp-sum') || {}).innerText || ''", None, 0)
    c.ok(len(prev) == 5 and 'FM1' in prev[0] and 'Accessories and Hardware' in prev[0] and '$145.00 each, $290' in prev[0] and '$139.00 each, $278' in prev[0],
         f'IMPORT {dev}: the preview reads each row under its FM number and category, with its money per unit and for the line ({prev[:2]})')
    c.ok('4 items to import' in summ and '1 repeats a row above' in summ and 'repeats a row above' in prev[2], f'IMPORT {dev}: a row the sheet repeats is caught; the same item in another room is not ({summ!r})')
    # the line-total reading halves nothing twice: $290 as the line is $145.00 each
    await pg.select_option('#ps-imp-basis', 'line')
    await pg.wait_for_timeout(300)
    prev2 = await js(pg, VIS_TEXT, '#mbm .ps-imp-row', 0)
    c.ok('$145 for the line, $72.50 each' in prev2[0], f'IMPORT {dev}: read as line totals, the preview says so ({prev2[0][-90:]!r})')
    await pg.select_option('#ps-imp-basis', 'unit')
    await pg.wait_for_timeout(300)
    await pg.locator('#mbm #mbm-ok').click()
    await pg.wait_for_timeout(700)
    toast = await js(pg, "() => (document.getElementById('toast') || {}).innerText || ''", None, 0)
    it = await js(pg, """() => DB.sel.items.filter(i => i.projectId === 'p121' && i.fm === 'FM1').map(i => ({ name: i.name, room: i.room, sku: i.sku, cost: i.cost, qty: i.qty, stage: i.stage, lead: i.leadDays,
      cat: i.category, actual: i.actual, imp: i.imported && i.imported.bought }))""", None, 0)
    bar = next((x for x in it if x['sku'] == 'TB-2210-SN'), {})
    pend = next((x for x in it if x['sku'] == 'PL-4402'), {})
    c.ok(len(it) == 4 and bar.get('stage') == 'ord' and bar.get('lead') == 21 and bar.get('cost') == 145 and bar.get('imp') == 278 and bar.get('actual') is None and pend.get('stage') == 'site' and pend.get('lead') == 42
         and 'Imported 4' in toast and 'Open' in toast, f'IMPORT {dev}: four items land on the job as FF&E items, the purchased price kept as imported, not as the actual ({it}; {toast!r})')
    au = await js(pg, "a0 => DB.audit.slice(a0).filter(x => x.action === 'imported from a sheet').map(x => x.after)", a0, 0)
    c.ok(len(au) == 1 and '4 items' in str(au[0]), f'IMPORT {dev}: the import writes one audit entry ({au})')
    R = await rows(pg)
    towel = next((r for r in R if 'Towel bar' in r['cells'].get('desc', '')), {'cells': {}})
    imp = await js(pg, "() => +((document.querySelector('[data-pstot=imported]') || {}).dataset || {}).v || 0", None, 0)
    c.ok(towel['cells'].get('inv', '').startswith('FM1') and 'imported' in towel['cells'].get('bought', '').lower() and imp >= 278,
         f'IMPORT {dev}: on the table under FM1, its purchased price marked imported and kept out of Purchased ({towel["cells"].get("bought")!r}; imported {imp})')
    await pg.locator('#pu-table [data-psx="import"]').first.click()
    await pg.wait_for_timeout(400)
    await pg.select_option('#ps-imp-job', 'p121')
    await pg.fill('#ps-imp-text', SHEET)
    await pg.wait_for_timeout(400)
    again = await js(pg, "() => (document.querySelector('#mbm .ps-imp-sum') || {}).innerText || ''", None, 0)
    await reset(pg)
    n1 = await js(pg, "() => DB.sel.items.filter(i => i.projectId === 'p121').length", None, 0)
    c.ok(n1 == n0 + 4 and re.search(r'already', again, re.I), f'IMPORT {dev}: a second import of the same sheet adds nothing ({n0} -> {n1}; {again!r})')


async def s_scan(pg, c, dev):
    """the desktop at 1440 scans: Invoice and Item # on one line, every sub-line one line, nothing scrolls sideways"""
    await board(pg)
    r = await js(pg, """() => { const w = document.querySelector('#pu-table .ps-wrap'), one = (e) => e.getBoundingClientRect().height <= 19;
      const cells = [...document.querySelectorAll('#pu-table td[data-pscol=inv] .ps-inv, #pu-table td[data-pscol=inv] > .ps-main, #pu-table td[data-pscol=sku] .ps-main')].filter(e => e.getBoundingClientRect().height > 0);
      const subs = [...document.querySelectorAll('#pu-table td .ps-sub')].filter(e => e.getBoundingClientRect().height > 0);
      const tb = w && w.querySelector('table'), rr = (e) => e.getBoundingClientRect();
      // every cell inside the table's box, and the table inside the page's content width
      const past = w ? [...w.querySelectorAll('th, td')].filter(e => rr(e).right > rr(w).right + 0.5).length : -1;
      return { side: w ? Math.max(past, Math.round(rr(tb).right - rr(w).right)) : -1, page: document.scrollingElement.scrollWidth - innerWidth, tall: cells.filter(e => !one(e)).map(e => e.textContent).slice(0, 4),
        wrap: subs.filter(e => !one(e)).map(e => e.textContent).slice(0, 4), n: subs.length }; }""", None, 0)
    c.ok(r['side'] <= 1 and r['page'] <= 0, f'SCAN {dev}: the table fits 1440 with nothing scrolling sideways ({r["side"]}, page {r["page"]})')
    c.ok(not r['tall'], f'SCAN {dev}: Invoice and Item # each on one line ({r["tall"]})')
    c.ok(r['n'] > 0 and not r['wrap'], f'SCAN {dev}: every sub-line is one line ({r["wrap"]})')


async def s_phone(pg, c, dev):
    await board(pg)
    t = await js(pg, TAPS, '#pu-table', 0)
    cards = await js(pg, "() => [...document.querySelectorAll('#pu-table .ps-card')].filter(e => e.getBoundingClientRect().height > 0).length", None, 0)
    n = await js(pg, "() => psView().rows.length", None, 0)
    c.ok(cards == n and n > 0, f'PHONE: one card per item ({cards} cards, {n} rows)')
    c.ok(t['side'] <= 0, f'PHONE: no sideways scroll ({t["side"]}px)')
    c.ok(not t['small'], f'PHONE: every control is 44px ({t["small"][:6]})')
    c.ok(not t['close'], f'PHONE: no two controls closer than 8px ({t["close"][:4]})')
    chips = await js(pg, "() => [...document.querySelectorAll('#pu-table .ps-chipb')].map(b => b.getBoundingClientRect()).filter(r => r.right > innerWidth + 0.5 || r.left < 0).length", None, 0)
    c.ok(chips == 0, f'PHONE: the status chips wrap inside the screen ({chips} past the edge)')
    cards = await js(pg, """() => { const M = new Map(psItems('').map(x => [x.id, x]));
      return [...document.querySelectorAll('#pu-table .ps-card')].map(e => { const x = M.get(e.dataset.psrow) || {};
        return { id: e.dataset.psrow, t: e.innerText, chip: !!e.querySelector('.ps-chip'), b: x.budget != null || !!x.shared, p: x.bought != null, v: !!x.vendor }; }); }""", None, 0)
    off = [k['t'][:60] for k in cards if not k['chip'] or (k['b'] and 'Budget' not in k['t']) or (k['p'] and 'Purchased' not in k['t']) or (k['v'] and 'Vendor' not in k['t'])]
    empty = await js(pg, """() => [...document.querySelectorAll('#pu-table .ps-card .ps-k')].filter(k => { const v = k.nextElementSibling;
      return !v || v.hidden || !(v.innerText || '').trim(); }).map(k => k.closest('.ps-card').dataset.psrow + ': ' + k.textContent).slice(0, 5)""", None, 0)
    c.ok(cards and not off, f'PHONE: each card shows its status chip, and budget, purchased and vendor where it has them ({len(cards)} cards; {off[:3]})')
    c.ok(not empty, f'PHONE: no label without its value on a card ({empty[:3]})')


async def run(dev):
    c = Checks()
    phone = dev == 'phone'
    async with async_playwright() as p:
        b, pg, errs = await open_app(p, phone=phone)
        if not phone:
            await pg.context.close(); await b.close()
            b = await p.chromium.launch()
            ctx = await b.new_context(viewport=DESKTOP, device_scale_factor=2 if SHOTS else 1, accept_downloads=True)
            pg = await ctx.new_page(); errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.goto(URL); await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
        elif SHOTS:
            await pg.context.close(); await b.close()
            b = await p.chromium.launch()
            ctx = await b.new_context(viewport=PHONE, is_mobile=True, has_touch=True, device_scale_factor=2)
            pg = await ctx.new_page(); errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.goto(URL); await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
        await sign_in(pg, 'u_chen')
        steps = [('TOGGLE', s_toggle), ('FILL', s_fill), ('INVOICE', s_invoice), ('STATUS', s_status), ('SORT', s_sort), ('FILTER', s_filter), ('TIE', s_tie), ('OPEN', s_open), ('PICK', s_pick)]
        steps += [('EXPORT', s_export), ('IMPORT', s_import), ('SCAN', s_scan)] if not phone else [('PHONE', s_phone)]
        for k, fn in steps:
            if not on(k): continue
            try: await fn(pg, c, dev)
            except Exception as e: c.ok(False, f'{k} {dev}: threw {str(e)[:300]}')
        if SHOTS:
            os.makedirs(SHOT_DIR, exist_ok=True)
            await board(pg)
            if not phone:
                # cropped to the table: the switch, the filters and totals, and the first rows, at 1440 (scale 2)
                for name, grp in (('desktop_table', 'room'), ('desktop_by_invoice', 'inv')):
                    await js(pg, "g => psSet({ group: g })", grp, 500)
                    # the page scrolls inside the app, not the window: bring the table's top to the top of the screen,
                    # then the clip is the screen from the switch down, the table's width
                    box = await js(pg, """() => { const m = document.querySelector('#pu-table .ps-modes'), tt = document.getElementById('toast'); tt && (tt.style.visibility = 'hidden');
                      let sc = m.parentElement; while (sc && !(sc.scrollHeight > sc.clientHeight + 4 && /auto|scroll/.test(getComputedStyle(sc).overflowY))) sc = sc.parentElement;
                      m.scrollIntoView({ block: 'start' }); const top = document.querySelector('.topbar, #topbar'); sc && sc.scrollBy(0, -((top ? top.getBoundingClientRect().height : 64) + 12));
                      const a = m.getBoundingClientRect(), t = document.querySelector('#pu-table .ps-wrap').getBoundingClientRect(), y = Math.max(0, a.top - 8);
                      return { x: Math.max(0, t.left - 8), y: y, width: Math.min(innerWidth, t.width + 16), height: innerHeight - y }; }""", None, 300)
                    await pg.screenshot(path=os.path.join(SHOT_DIR, f'{name}.png'), clip=box)
            else:
                await pg.screenshot(path=os.path.join(SHOT_DIR, f'{dev}_table.png'))
                await js(pg, "() => window.scrollTo(0, 900)", None, 300)
                await pg.screenshot(path=os.path.join(SHOT_DIR, f'{dev}_table_2.png'))
        c.ok(not errs, f'{dev}: no page errors ({errs[:3]})')
        await b.close()
    print(dev.upper(), end=' '); return c.done()


async def main():
    rc = 0
    for phone in DEVS:
        rc |= await run('phone' if phone else 'desktop')
    sys.exit(rc)

asyncio.run(main())
