"""PU-Safe 2 (the coordinator's re-walk of Ron's jobs, 11-18): one strict vendor reader everywhere; the vendor's paper
is right. As Chen (and the controller where the money is theirs), through the screens, desktop and phone, from the
seeded data (the app day 2026-09-03):
  LINT    no name-to-vendor match exists in src/ outside the vendor reader (a shared word, a first word, a prefix or
          a substring); the one wording source for why money matters names charity
  READER  names are one vendor only when they are the same name (Garden State Lumber is not Garden Supply, Kent
          Avenue Lumber is not Kent Plumbing, Tino is not Tino Flooring); a bank line names a vendor by its whole
          name, its card's descriptors or its name without the trade words, never a place or a prefix (HOME DEPOT
          STATEN ISLAND is not Garden State Lumber); "the lumber yard" links nobody in a meeting
  DESK    the RFQ from three Buy Board lines: no vendor without an email ticked (Add Email on its row), quotes due in
          three working days, sent in 8 taps or fewer; PO-2026-049's paper and mail to the cent, "lump sum" for a
          lump-sum line, and only current, issued drawings that belong to the order (PO-2026-048 too); Ask's chase
          by PO number goes to the order's own vendor; accepting a differing confirmation becomes the order's lines
          (was-values kept), Receive asks only for what is still to come and the bill at the accepted price is not
          flagged again; an invoice from Garden Supply Co citing PO-2026-049 is held and never billed to Garden
          State; the bank line from Home Depot Staten Island offers no Garden State order; a vendor's email saved on
          its card clears Needs Address at once, and Save says so
  PHONE   the RFQ from three lines with no refusal; short and damaged on the same line in one receipt, each claimed,
          the toast naming charity; the reply to a confirmation says Needs Address when there is no email

    python3 pu_safe2_test.py [--section lint,reader,desk,phone]
"""
import asyncio, re, sys, os, glob, argparse
from harness import *

MODAL = """() => { const m = document.querySelector('#mbm'); if (!m || !m.getClientRects().length) return null;
  return { title: (m.querySelector('.mbm-hd h3') || {}).innerText || '', text: m.innerText,
           buttons: [...m.querySelectorAll('button')].filter(b => b.getClientRects().length).map(b => b.innerText.trim()).filter(Boolean),
           primary: [...m.querySelectorAll('button.primary')].filter(b => b.getClientRects().length).map(b => b.innerText.trim()) }; }"""
TOAST = "() => { const t = document.getElementById('toast'); return t ? t.innerText.trim() : ''; }"
TXT = "s => (document.querySelector(s) || {}).innerText || ''"
NOSIDE = "() => document.documentElement.scrollWidth - innerWidth"
SRC = os.environ.get('SD_SRC') or os.path.join(ROOT, 'src')  # SD_SRC: lint another tree (the base, to see it fail)

async def modal(pg): return await pg.evaluate(MODAL)
async def toast(pg): return await pg.evaluate(TOAST)
async def view_text(pg): return await pg.evaluate(TXT, '.view.on')

# ---- LINT: every name-to-vendor match goes through the vendor reader ------------------------------------------------
# The shapes a hand-made vendor match takes. Each pattern names what was wrong with it the last time it was found.
LINT = [
    ('a vendor list searched by a part of a name (substring, prefix)',
     re.compile(r'vendors\b[^;\n]*\.(?:find|filter|some|findIndex|every)\(\s*\(?\s*\w+\s*\)?\s*=>[^\n]*?(?:\.name\b[^\n]{0,60}?\.(?:includes|startsWith|endsWith|indexOf)\(|\.(?:includes|startsWith|endsWith|indexOf)\([^)\n]{0,60}\.name\b)')),
    ('a vendor name cut to its first word and looked for in a text',
     re.compile(r'(?:includes|startsWith|indexOf|===)\s*\(?[^\n]{0,80}vendor[^\n]{0,40}\.split\([^)]*\)\[0\]|vendor[^\n]{0,40}\.split\([^)]*\)\[0\][^\n]{0,30}(?:includes|startsWith|indexOf|===)')),
    ('vendor name words compared by hand outside the reader',
     re.compile(r'\bvendorNameWords\(|\btruthNorm\(\s*vendor\b')),
    ('a vendor name matched by a prefix',
     re.compile(r'(?=.*vendor)(?:vendor\w*|\.name)\s*(?:\|\|\s*"")?\)?\s*(?:\.toLowerCase\(\))?\.startsWith\([^)\n]*\b(?:n|name|nm|who|vendor\w*)\b|\.startsWith\([^)\n]*vendor')),
    ('a text tested for a vendor\'s name by substring',
     re.compile(r'vendors\b[^\n]*\.(?:includes|indexOf)\(\s*(?:\w+\.)?name\b|\.includes\(\s*(?:\w+\.)?vendor(?:Name)?\s*(?:\.toLowerCase\(\))?\s*\)')),
    ('a vendor\'s first word looked for in a bank line',
     re.compile(r'(?:desc|vendor)\w*[^\n]{0,40}\.includes\([^)\n]*\.split\([^)]*\)\[0\]')),
]
# what the reader's own block and the order's own record may do
READER_OPEN, READER_CLOSE = '// ---- the vendor reader', '// ---- end of the vendor reader'

def lint_src(src=SRC):
    out = []
    for f in sorted(glob.glob(os.path.join(src, '*.js'))):
        inside = False
        for i, line in enumerate(open(f, encoding='utf-8'), 1):
            if READER_OPEN in line: inside = True
            if READER_CLOSE in line: inside = False; continue
            if inside: continue
            for name, rx in LINT:
                if rx.search(line): out.append(f'{os.path.basename(f)}:{i} {name}: {line.strip()[:140]}')
    return out

def s_lint(c):
    hits = lint_src()
    c.ok(not hits, f'LINT: no name-to-vendor match outside the vendor reader ({len(hits)}: {hits[:6]})')
    # the lint sees the shapes it is for (a self-test, so a pattern that rots fails loudly)
    probe = ['const v = DB.vendors.find((x) => text.includes(x.name));',
             '(t.desc || "").toLowerCase().includes(po.vendor.toLowerCase().split(" ")[0])',
             'const M = (DB.vendors || []).filter((x) => vendorNameWords(x.name).includes(n));',
             'const v = (DB.vendors || []).find((x) => (x.name || "").toLowerCase().includes(name));']
    miss = [p for p in probe if not any(rx.search(p) for _, rx in LINT)]
    c.ok(not miss, f'LINT: the lint catches each shape it was written for ({miss})')
    # one wording source for why money matters, and it names charity
    allsrc = ''.join(open(f, encoding='utf-8').read() for f in glob.glob(os.path.join(SRC, '*.js')))
    copies = len(re.findall(r'raises, bonuses', allsrc))
    m = re.search(r'const MONEY_WHY = "([^"]+)"', allsrc)
    c.ok(m and 'charity' in m.group(1) and copies == 1, f'LINT: one wording for why money matters, naming charity ({copies} copies; {m and m.group(1)})')

# ---- READER: the class, through the one reader --------------------------------------------------------------------
async def s_reader(p, c):
    b, pg, errs = await open_app(p, phone=False)
    await sign_in(pg, 'u_chen')
    r = await pg.evaluate("""() => {
        rfqDemoSuppliers();
        DB.vendors.push({ id: 'ps2a', name: 'Garden Supply Co' }, { id: 'ps2b', name: 'Kent Plumbing' }, { id: 'ps2c', name: 'Avenue Builders' }, { id: 'ps2d', name: 'Harlem Tile' }, { id: 'ps2e', name: 'Tino Flooring' });
        const pairs = [['Garden State Lumber','Garden Supply'], ['Kent Avenue Lumber','Kent Plumbing'], ['Kent Avenue Lumber','Avenue Builders'], ['Harlem River Building Supply','Harlem Tile'], ['Tino','Tino Flooring'], ['Garden State Lumber','State Line Supply'], ['Nemo Tile','Nemo']];
        const same = pairs.filter(([a, b]) => vendorNameSame(a, b));
        const yes = [['Garden State Lumber', 'GARDEN STATE LUMBER CO.'], ['Harlem River Bldg Supply', 'Harlem River Building Supply']].filter(([a, b]) => !vendorNameSame(a, b));
        const bank = [['HOME DEPOT #1209 STATEN ISLAND NY','Garden State Lumber'], ['SHELL OIL 4TH AVE BROOKLYN','Kent Avenue Lumber'], ['NYS DMV EMPIRE STATE','Garden State Lumber'], ['HARLEM SHAKE 124TH','Harlem River Building Supply'], ['GARDEN SUPPLY CO #12','Garden State Lumber']].filter(([d, v]) => truthVendorHit({ desc: d }, v));
        const bankYes = [['GARDEN STATE LUMBER LINDEN NJ','Garden State Lumber'], ['HOME DEPOT #1209','Home Depot'], ['KENT AVE LUMBER BKLYN','Kent Avenue Lumber']].filter(([d, v]) => !truthVendorHit({ desc: d }, v));
        const tk = ['the lumber yard', 'Lumber', 'Building Supply', 'Garden', 'Kent'].map((n) => [n, tkContactRef(n)]).filter((x) => x[1]);
        const cm = (cmVendorFor('billing@gardensupply.example', 'Garden Supply Co') || {}).name || '';
        return { same: same, yes: yes, bank: bank, bankYes: bankYes, tk: tk, cm: cm, gs: (vendorByName('Garden Supply Co') || {}).id || '' };
    }""")
    c.ok(not r['same'], f'READER: names sharing a word are not one vendor ({r["same"]})')
    c.ok(not r['yes'], f'READER: the same name in capitals, with a suffix or an abbreviation, is ({r["yes"]})')
    c.ok(not r['bank'], f'READER: a bank line names no vendor by a place, a shared word or a prefix ({r["bank"]})')
    c.ok(not r['bankYes'], f'READER: a bank line names the vendor by its name or its name without the trade words ({r["bankYes"]})')
    c.ok(not r['tk'], f'READER: a meeting\'s "the lumber yard" (or a shared word) links nobody ({r["tk"]})')
    c.ok(r['cm'] == 'Garden Supply Co' and r['gs'] == 'ps2a', f'READER: mail from Garden Supply Co is Garden Supply Co\'s ({r})')
    c.ok(not errs, f'READER: no page errors ({errs[:3]})')
    await b.close()

# ---- the RFQ from the Buy Board, counting taps ----------------------------------------------------------------------
async def rfq_from_board(pg, c, dev, phone=False):
    taps = 0
    async def tap(loc, wait=400):
        nonlocal taps
        taps += 1
        await loc.first.click(); await pg.wait_for_timeout(wait)
    picks = ['GWB boards', 'Waterproofing membrane', 'Base molding']
    await go(pg, 'proc'); await pg.wait_for_timeout(500)
    if phone:
        later = pg.locator('#v-proc button').filter(has_text='Show the Later Needs')
        if await later.count(): await tap(later, 600)
        rows = await pg.evaluate("() => [...document.querySelectorAll('#v-proc [data-bbpick]')].filter(i => i.getClientRects().length).map(i => [i.dataset.bbpick, (i.closest('[data-psrow], .bb-row, .card, li, tr, label') || i.parentElement).innerText.replace(/\\s+/g, ' ')])")
        for w in picks:
            h = [r for r in rows if w.lower() in r[1].lower()]
            c.ok(h, f'{dev}: the Buy Board has {w} to pick')
            if h: await tap(pg.locator(f'#v-proc [data-bbpick="{h[0][0]}"]'), 300)
        q = pg.locator('#v-proc button:visible, .bb-bar button:visible, body > div button:visible').filter(has_text=re.compile(r'^(Ask for Quotes|Request Quotes)'))
        await tap(q.last, 800)
    else:
        tb = pg.locator('#v-proc [data-psmode="table"]')
        if await tb.count(): await tap(tb, 600)
        rows = await pg.evaluate("() => [...document.querySelectorAll('#v-proc [data-psrow]')].map(r => [r.dataset.psrow, !!r.querySelector('[data-pspick]'), r.innerText.replace(/\\s+/g, ' ')])")
        for w in picks:
            h = [r for r in rows if r[1] and w.lower() in r[2].lower()]
            c.ok(h, f'{dev}: the Buy Board has {w} to pick')
            if h: await tap(pg.locator(f'#v-proc [data-pspick="{h[0][0]}"]'), 300)
        await tap(pg.locator('#v-proc [data-psdo="quote"]'), 800)
    stock = 0
    for _ in range(2):
        m = await modal(pg)
        if m and 'Stock' in m['title']:
            stock += 1
            await tap(pg.locator('#mbm button').filter(has_text='Buy It Anyway'), 700)
    m = await modal(pg)
    c.ok(m and 'Request for Quote' in m['title'], f'{dev}: the RFQ sheet opens ({m and m["title"]})')
    V = await pg.evaluate("""() => [...document.querySelectorAll('#mbm [data-rsv]')].map(i => { const v = rfqVendor(i.dataset.rsv) || {};
        return { id: i.dataset.rsv, on: i.checked, email: v.email || '', name: v.name || '', add: !!(i.closest('label') || i.parentElement).querySelector('[data-rfqnoem]') && /Add Email/.test((i.closest('label') || i.parentElement).textContent) }; })""")
    bad = [v['name'] for v in V if v['on'] and not v['email']]
    c.ok(V and not bad, f'{dev}: no vendor without an email comes ticked ({bad})')
    noem = [v for v in V if not v['email']]
    c.ok(noem and all(v['add'] for v in noem), f'{dev}: a vendor with no email shows Add Email on its row ({[v["name"] for v in noem if not v["add"]][:4]})')
    due, want = await pg.locator('#mbm #rsq-due').input_value(), await pg.evaluate("() => addWork(today(), 3)")
    c.ok(due == want, f'{dev}: quotes are due in three working days by default ({due}, want {want})')
    ticked = [v['name'] for v in V if v['on']]
    ob0 = await pg.evaluate("() => (DB.outbox || []).length")
    await tap(pg.locator('#mbm #mbm-ok'), 900)
    t = await toast(pg)
    m = await modal(pg)
    c.ok('sent to' in t and not (m and 'Request for Quote' in m['title']), f'{dev}: the RFQ is sent on the first Send, nothing refused ({t[:140]})')
    if m and 'Request for Quote' in m['title']:
        # refused (the walk's way through it): untick the vendors with no email, and Send again; the taps count
        for v in V:
            if v['on'] and not v['email']: await tap(pg.locator(f'#mbm [data-rsv="{v["id"]}"]'), 200)
        await tap(pg.locator('#mbm #mbm-ok'), 900)
        ticked = [v['name'] for v in V if v['on'] and v['email']]
    r = await pg.evaluate("() => { const r = DB.rfqs.slice(-1)[0]; return { id: r.id, number: r.number, status: r.status }; }")
    return r, taps, stock, ticked

async def award_gsl(pg, c, r):
    """Harlem River declines, the others reply (the demo's world), Chen levels, confirms and awards Garden State."""
    await pg.evaluate("""n => { DB.comms.push({ id: 'ps2_nobid', from: { email: 'desk@harlemriverbuilding.example', name: 'Lou Grant' }, subject: 'Re: ' + n + ' request for quote',
        text: 'Hi Chen, regarding ' + n + ', we do not carry cement board or membrane. Thanks, Lou', date: today(), direction: 'in', proposals: [], channel: 'email' }); save(); }""", r['number'])
    await pg.evaluate("() => appSetDay('2026-09-04')")
    await pg.evaluate("id => rfqOpenFor(id)", r['id']); await pg.wait_for_timeout(500)
    if await pg.locator('#rfq-check').count(): await pg.locator('#rfq-check').first.click(); await pg.wait_for_timeout(700)
    if await pg.locator('#rfq-level').count(): await pg.locator('#rfq-level').click(); await pg.wait_for_timeout(700)
    n = 0
    while await pg.locator('[data-rfqconf]').count() and n < 6:
        await pg.locator('[data-rfqconf]').first.click(); await pg.wait_for_timeout(300)
        if await modal(pg): await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(400)
        n += 1
    if await pg.locator('#rfq-skipneg').count(): await pg.locator('#rfq-skipneg').click(); await pg.wait_for_timeout(600)
    sel = pg.locator('#rfq-award-all')
    if await sel.count():
        vid = await pg.evaluate("() => (DB.vendors.find(v => v.name === 'Garden State Lumber') || {}).id")
        await sel.select_option(vid); await pg.wait_for_timeout(300)
    if await pg.locator('#rfq-award-reason').count(): await pg.locator('#rfq-award-reason').fill('Garden State lands in time at the best price')
    po0 = await pg.evaluate("() => DB.pos.length")
    await pg.locator('#rfq-award').click(); await pg.wait_for_timeout(900)
    po = await pg.evaluate("n => { const p = DB.pos.slice(n)[0]; return p && { id: p.id, n: p.number, v: p.vendor, total: poTotal(p).total }; }", po0)
    c.ok(po and po['v'] == 'Garden State Lumber', f'the award makes a PO to Garden State Lumber ({po})')
    return po

async def open_po(pg, num):
    await pg.evaluate("n => { const p = DB.pos.find(x => x.number === n); poOpen = p.id; view = 'po'; render(); }", num); await pg.wait_for_timeout(600)

async def po_mail(pg, num):
    await open_po(pg, num)
    await pg.locator('.view.on button').filter(has_text=re.compile('Draft Email to Vendor|Draft email to vendor')).first.click(); await pg.wait_for_timeout(600)
    body = await pg.evaluate("() => (document.querySelector('#em-body') || {}).value || ''")
    await pg.evaluate("() => { try { closeEditor(); } catch (e) {} }")
    return body

DRAWINGS_OK = """([body, pid]) => { const i = body.indexOf('Drawings for this order:'); if (i < 0) return { listed: [], bad: [] };
    const listed = body.slice(i).split('\\n').slice(1).filter(l => l.startsWith('- ')).map(l => l.slice(2).split(' \\u2014 ')[0].trim());
    const S = plSheets(pid), files = (DB.projects.find(p => p.id === pid) || {}).files || [];
    const bad = listed.filter(n => { const f = files.find(x => x.name === n), s = f && S.find(x => x.fileId === f.id);
        return /^VOID|DECK-|superseded/i.test(n) || !s || !plIsCurrent(s) || !['ifc', 'permit'].includes(plStatus(s)) || s.set === 'deck'; });
    return { listed: listed, bad: bad }; }"""

async def s_desk(p, c):
    b, pg, errs = await open_app(p, phone=False)
    await sign_in(pg, 'u_chen')
    r, taps, stock, ticked = await rfq_from_board(pg, c, 'desk')
    c.ok(taps <= 8, f'desk: three Buy Board lines to a sent RFQ in 8 taps or fewer ({taps}, {stock} stock sheet; asked {ticked})')
    c.ok('Garden State Lumber' in ticked, f'desk: Garden State Lumber is asked by default ({ticked})')
    po = await award_gsl(pg, c, r)
    if not po: return await b.close()
    num = po['n']
    cents = await pg.evaluate("t => unitMoney(t)", po['total'])
    # ---- the order on the screen, to the cent
    await open_po(pg, num)
    t = await view_text(pg)
    whole = await pg.evaluate("t => money(t)", po['total'])
    c.ok(cents in t and (whole == cents or whole not in t.replace(cents, '')), f'desk: the PO screen shows the order to the cent ({cents}; whole-dollar {whole} not shown)')
    # ---- the paper and the mail: lump sum, to the cent, only the drawings that belong
    try:
        async with pg.context.expect_page(timeout=4000) as pi:
            await pg.locator('.view.on button').filter(has_text='Print / PDF').first.click()
        pop = await pi.value; await pop.wait_for_timeout(600)
        pt = await pop.evaluate("() => document.body.innerText"); await pop.close()
    except Exception as e:
        pt = ''
    c.ok('lump sum' in pt and not re.search(r'\b1 ls\b', pt) and '$4.50' in pt, f'desk: the PO print reads "lump sum", never "1 ls", and prices to the cent ({pt[pt.find("ITEM"):][:240]!r})')
    body = await po_mail(pg, num)
    c.ok('lump sum' in body and not re.search(r'\b1 ls\b', body) and '@ $4.50' in body, f'desk: the PO mail reads "lump sum" for a lump-sum line ({body[:300]!r})')
    d = await pg.evaluate(DRAWINGS_OK, [body, 'p121'])
    c.ok(not d['bad'], f'desk: {num}\'s mail lists only current, issued drawings that belong to it ({d})')
    body48 = await po_mail(pg, 'PO-2026-048')
    d48 = await pg.evaluate(DRAWINGS_OK, [body48, 'p121'])
    c.ok(d48['listed'] and not d48['bad'] and any('A-202' in n and 'Rev C' in n for n in d48['listed']), f'desk: PO-2026-048 lists the current millwork sheets only ({d48})')
    # ---- Ask: chase by the order's number goes to the order's own vendor
    await go(pg, 'pa'); await pg.wait_for_timeout(300)
    ob0 = await pg.evaluate("() => DB.outbox.length")
    await pg.locator('#pa-in').fill(f'chase the lumber yard on {num}'); await pg.locator('#pa-in').press('Enter'); await pg.wait_for_timeout(2500)
    ans = await pg.evaluate("() => (document.querySelector('#pa-thread') || { innerText: '' }).innerText")
    ans = ans[ans.rfind('chase the lumber yard'):]
    btn = pg.locator('#pa-thread button:visible').filter(has_text=re.compile(r'^(Save|Draft|Put|Add|Send)'))
    if await btn.count(): await btn.last.click(); await pg.wait_for_timeout(600)
    ob = await pg.evaluate("n => DB.outbox.slice(n).map(o => o.to)", ob0)
    c.ok(('Garden State Lumber' in ans or 'Pat' in ans) and f'To: {num}' not in ans and 'Kent' not in ans, f'desk: Ask\'s chase on {num} is to Garden State Lumber, the order\'s own vendor ({ans[:260]!r})')
    c.ok(not ob or all(o.get('email') == 'sales@gardenstatelumber.example' for o in ob), f'desk: the chase draft is addressed to Garden State ({ob})')
    # Ask's answer about the order: to the cent, as the paper prints it
    n0 = await pg.evaluate("() => (document.querySelector('#pa-thread') || { innerText: '' }).innerText.length")
    await pg.locator('#pa-in').fill(f'how much is {num}'); await pg.locator('#pa-in').press('Enter'); await pg.wait_for_timeout(2000)
    a2 = (await pg.evaluate("() => (document.querySelector('#pa-thread') || { innerText: '' }).innerText"))[n0:]
    c.ok(cents in a2 and not re.search(r'\$\d[\d,]*(?![\d,.])', a2.split('Open ' + num)[0]), f'desk: Ask\'s answer about {num} is to the cent ({a2[:300]!r})')
    # ---- a confirmation that differs, accepted: the order's lines change, the was-values kept
    await pg.evaluate("() => appSetDay('2026-09-05')")
    await pg.evaluate("""n => { const t = 'GARDEN STATE LUMBER\\nOrder Acknowledgment No. ACK-5512\\nDate: Sep 5, 2026\\nAgainst ' + n + '\\n\\nGWB boards (~25) & cement board   20 bd @ $4.86   $97.20\\nWaterproofing membrane   1 ls @ $4.50   $4.50\\nBase molding & casing   1 ls @ $4.50   $4.50\\n\\nShip date: Sep 8, 2026\\nTerms: NET 30';
        trkFileMail([{ id: 'ps2_ack', date: today() + 'T09:12:00', from: 'Garden State Lumber <orders@gardenstatelumber.example>', subject: 'Order acknowledgment ' + n, text: 'Acknowledgment attached.', attachments: [{ name: 'ACK-5512.pdf', text: t }] }]); }""", num)
    await pg.evaluate("() => { try { mbCloseModal(); closeEditor(); } catch (e) {} poOpen = null; view = 'po'; render(); }"); await pg.wait_for_timeout(500)
    act = pg.locator('[data-puact^="ack:"]')
    c.ok(await act.count() == 1, 'desk: the confirmation that differs is one Needs You row on Orders')
    if await act.count():
        await act.first.click(force=True); await pg.wait_for_timeout(500)
        await pg.locator('#mbm [data-f="why"]').fill('Twenty boards cover the third floor; the rest comes from stock')
        await pg.locator('#mbm #mbm-alt').click(); await pg.wait_for_timeout(600)
        ta = await toast(pg)
        P = await pg.evaluate("n => { const p = DB.pos.find(x => x.number === n); const l = p.lines[0]; return { q: l.qty, pr: l.price, was: l.was || null, others: p.lines.slice(1).map(x => [x.qty, x.price]), audit: (DB.audit || []).filter(a => a.id === p.id && /accepted/.test(a.action || a.what || '')).length }; }", num)
        c.ok(P['q'] == 20 and abs(P['pr'] - 4.86) < 1e-9, f'desk: accepted, the order\'s line is the confirmed 20 bd at $4.86 ({P})')
        c.ok(P['was'] and P['was'].get('qty') == 25 and abs(P['was'].get('price') - 4.5) < 1e-9 and 'Twenty boards' in (P['was'].get('why') or ''), f'desk: the line keeps what it was and why it changed ({P["was"]})')
        c.ok(P['others'] == [[1, 4.5], [1, 4.5]], f'desk: lines that matched are untouched ({P["others"]})')
        c.ok('now reads' in ta and 'Open' in ta, f'desk: the acceptance toast says what the order now reads, with Open ({ta[:200]})')
        # Receive asks only for what is still to come
        await open_po(pg, num)
        rs = pg.locator('.view.on button').filter(has_text=re.compile(r'^Receive Some$'))
        if not await rs.count(): rs = pg.locator('.view.on button').filter(has_text=re.compile(r'^Receive'))
        await rs.first.click(); await pg.wait_for_timeout(500)
        m = await modal(pg)
        c.ok(m and re.search(r'0 of 20 bd in · 20 to come', m['text']), f'desk: Receive says 20 bd are still to come, not 25 ({m and m["text"][:240]!r})')
        # 20 arrive
        await pg.locator('#mbm [data-purq]').nth(0).fill('20')
        for i in (1, 2): await pg.locator('#mbm [data-purq]').nth(i).fill('1')
        await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(700)
        if await modal(pg): await pg.evaluate("() => { try { mbCloseModal(); } catch (e) {} }")
        st = await pg.evaluate("n => DB.pos.find(x => x.number === n).status", num)
        c.ok(st == 'received', f'desk: the confirmed quantity received is the order received in full ({st})')
    # ---- the vendor's invoice at the accepted price is not flagged again; Garden Supply's is held
    await pg.evaluate("() => appSetDay('2026-09-14')")
    INV = lambda vend, no, frm: [vend, no, frm]
    for vend, no, frm in [('GARDEN STATE LUMBER', 'GSL-30117', 'Garden State Lumber <ar@gardenstatelumber.example>'), ('GARDEN SUPPLY CO', 'GS-8841', 'Garden Supply Co <billing@gardensupply.example>')]:
        await pg.evaluate("""([v, no, frm, n]) => { const t = v + '\\nINVOICE No. ' + no + '\\nDate: Sep 14, 2026\\nBill to: SmartDesign Group LLC\\nPO: ' + n + '   Job: 121 State Street\\n\\nGWB boards (~25) & cement board   20 bd @ $4.86   $97.20\\nWaterproofing membrane   1 ls @ $4.50   $4.50\\nBase molding & casing   1 ls @ $4.50   $4.50\\n\\nTotal due: $106.20\\nTerms: NET 30';
            trkFileMail([{ id: 'ps2_' + no, date: today() + 'T15:00:00', from: frm, subject: 'Invoice ' + n, text: 'Invoice attached.', attachments: [{ name: no + '.pdf', text: t }] }]); }""", [vend, no, frm, num])
    chk = await pg.evaluate("""() => ['GSL-30117', 'GS-8841'].map(no => { const d = trkDocs().find(x => (x.fields || {}).number === no); if (!d) return null; const k = trkCheck(d);
        return { no: no, po: (trkPO(d.links.poId) || {}).number, cases: k.cases.map(x => x.code), toBill: trkInvoicesToBill().includes(d), id: d.id }; })""")
    g, s2 = chk[0], chk[1]
    c.ok(g and not set(g['cases']) & {'price', 'priceQuote', 'qty', 'vendor'}, f'desk: the invoice at the accepted price is not flagged again ({g})')
    c.ok(s2 and s2['po'] == num and 'vendor' in s2['cases'] and not s2['toBill'], f'desk: Garden Supply Co\'s invoice citing {num} is held on the vendor and not offered as its bill ({s2})')
    await sign_in(pg, 'u_controller'); await go(pg, 'home'); await pg.wait_for_timeout(500)
    tx = await view_text(pg)
    c.ok('GS-8841' not in ' '.join(ln for ln in tx.split('\n') if 'Enter the bill' in ln), 'desk: the controller is not asked to enter Garden Supply\'s invoice as the order\'s bill')
    nb0 = await pg.evaluate("() => DB.bills.length")
    await pg.evaluate("id => trkBillFromDoc(id)", s2['id'] if s2 else '')
    tb = await toast(pg)
    nb = await pg.evaluate("() => DB.bills.filter(b => b.number === 'GS-8841').length")
    c.ok(nb == 0 and 'Held' in tb and 'Open' in tb, f'desk: Enter the Bill refuses it: nothing billed to Garden State ({nb}; {tb[:160]})')
    # ---- the bank line from Home Depot Staten Island: no Garden State order offered
    amt = po['total']
    await pg.evaluate("a => { const s = (DB.txns.find(t => t.amt < 0) || {}); DB.txns.push(Object.assign({}, s, { id: 'ps2_hd', date: '2026-09-08', desc: 'HOME DEPOT #1209 STATEN ISLAND NY', vendor: '', amt: -a, match: null, matched: null, poId: null, billId: null, projectId: null, proposal: null, prov: { src: 'demo' } })); save(); }", amt)
    await go(pg, 'bank'); await pg.wait_for_timeout(600)
    await pg.evaluate("() => truthMatchSheet(DB.txns.find(t => t.id === 'ps2_hd'))"); await pg.wait_for_timeout(600)
    m = await modal(pg)
    c.ok(m and num not in m['text'] and 'Garden State' not in m['text'], f'desk: the Home Depot Staten Island line is offered no Garden State order ({m and m["text"][:300]!r})')
    c.ok(m and re.search(r'\$\d[\d,]*\.\d\d', m['text']) and not re.search(r'−\$\d[\d,]*\s·', m['text']), f'desk: the match sheet shows the line\'s money to the cent ({m and m["text"][:120]!r})')
    await pg.evaluate("() => { try { mbCloseModal(); } catch (e) {} }")
    # ---- Needs Address clears the moment the vendor gets an email; Save says so
    await sign_in(pg, 'u_chen')
    for d in ['2026-09-15', '2026-09-16']: await pg.evaluate("d => appSetDay(d)", d)
    before = await pg.evaluate("() => mApprovals().filter(i => i.kind === 'draft' && /PO-2026-048/.test(i.title)).map(i => i.title)")
    c.ok(any(x.startswith('Needs Address') for x in before), f'desk: before, Today asks for Carlos\'s address ({before[:3]})')
    await pg.evaluate("() => openVendor('v3')"); await pg.wait_for_timeout(500)
    await pg.locator('#e-email').fill('shop@carlosmillwork.example'); await pg.locator('#d-save').click(); await pg.wait_for_timeout(600)
    ts = await toast(pg)
    c.ok('Carlos Millwork saved' in ts and 'ready to send' in ts and 'Open' in ts, f'desk: the vendor card\'s Save toasts, saying the waiting drafts can go ({ts[:200]})')
    after = await pg.evaluate("() => mApprovals().filter(i => i.kind === 'draft' && /PO-2026-048/.test(i.title)).map(i => i.title)")
    ox = await pg.evaluate("() => DB.outbox.filter(o => (DB.pos.find(p => p.id === (o.about || {}).poId) || {}).number === 'PO-2026-048' && o.status === 'draft').map(o => [!!o.needsAddress, o.to.email])")
    fu = await pg.evaluate("() => (DB.pos.find(p => p.number === 'PO-2026-048').followups || []).map(f => f.status)")
    c.ok(after and all(x.startswith('Send:') for x in after) and ox and all(not x[0] and x[1] == 'shop@carlosmillwork.example' for x in ox) and 'needs-address' not in fu, f'desk: with the email saved, Needs Address clears and the draft can be sent ({after[:2]}; {ox}; {fu})')
    c.ok(not errs, f'desk: no page errors ({errs[:3]})')
    await b.close()

async def s_phone(p, c):
    b, pg, errs = await open_app(p, phone=True)
    await sign_in(pg, 'u_chen')
    r, taps, stock, ticked = await rfq_from_board(pg, c, 'phone', phone=True)
    # 5 = three picks, Ask for Quotes and Send; Show the Later Needs (a view) and the stock check (a money gate) apart
    c.ok(taps - stock - 1 <= 5, f'phone: three lines to a sent RFQ: picks, request and send in 5 taps ({taps} in all, {stock} stock answer, 1 Show the Later Needs; asked {ticked})')
    c.ok(await pg.evaluate(NOSIDE) <= 0, 'phone: never scrolls sideways')
    # ---- short and damaged on the same line, one receipt (Tino's flooring, PO-2026-047)
    await open_po(pg, 'PO-2026-047')
    await pg.locator('.view.on button:visible').filter(has_text=re.compile('Receive Some')).first.click(); await pg.wait_for_timeout(600)
    L = await pg.evaluate("() => { const p = DB.pos.find(x => x.number === 'PO-2026-047'); const l = p.lines[0]; return { id: l.id, left: l.qty - (l.received || 0), unit: l.unit, price: l.price }; }")
    came = L['left'] - 30
    await pg.locator('#mbm [data-purq]').first.fill(str(came))
    await pg.locator('#mbm button:visible').filter(has_text=re.compile('^Short$')).first.click(); await pg.wait_for_timeout(200)
    await pg.locator('#mbm button:visible').filter(has_text=re.compile('^Damaged$')).first.click(); await pg.wait_for_timeout(200)
    on = await pg.evaluate("() => [...document.querySelectorAll('#mbm [data-pucond].on')].map(b => b.innerText.trim())")
    c.ok(on == ['Short', 'Damaged'], f'phone: Short and Damaged are both on for the line ({on})')
    await pg.locator('#mbm [data-pubad]').first.fill('30')
    await pg.locator('#mbm [data-punote]').fill('30 sf crushed corner, slip 4471')
    sl = pg.locator('#mbm [data-puslip]')
    await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(800)
    t = await toast(pg)
    P = await pg.evaluate("() => { const p = DB.pos.find(x => x.number === 'PO-2026-047'); return { rec: p.lines[0].received || 0, claims: (p.issues || []).filter(i => i.claim).map(i => [i.type, i.qty, i.amount]) }; }")
    kinds = sorted(x[0] for x in P['claims'])
    c.ok(kinds == ['damaged', 'short'] and all(x[1] == 30 for x in P['claims']), f'phone: one receipt claims 30 short and 30 damaged on the line ({P})')
    c.ok(abs(P['rec'] - (came - 30)) < 1e-9, f'phone: only the good ones are received ({P["rec"]}, want {came - 30})')
    c.ok('short' in t and 'damaged' in t and 'charity' in t and 'Open' in t, f'phone: the toast names both claims and why the money matters, charity included ({t[:260]})')
    c.ok(await pg.evaluate(NOSIDE) <= 0, 'phone: the receipt never scrolls sideways')
    # ---- the reply to a confirmation that differs, to a vendor with no email: the toast says Needs Address
    await pg.evaluate("""() => { const p = DB.pos.find(x => x.number === 'PO-2026-048'); const L = p.lines[0];
        const t = 'CARLOS MILLWORK\\nOrder Acknowledgment No. CM-311\\nAgainst PO-2026-048\\n\\n' + L.item + '   ' + L.qty + ' ' + L.unit + ' @ $' + (L.price * 1.05).toFixed(2) + '   $' + (L.qty * +(L.price * 1.05).toFixed(2)).toFixed(2) + '\\n\\nShip date: Sep 30, 2026';
        trkFileMail([{ id: 'ps2_ack2', date: today() + 'T09:00:00', from: 'Carlos Millwork <shop@carlosmillwork.example>', subject: 'Acknowledgment', text: 'See attached.', attachments: [{ name: 'CM-311.pdf', text: t }] }]); }""")
    await pg.evaluate("() => { poOpen = null; view = 'po'; render(); }"); await pg.wait_for_timeout(500)
    act = pg.locator('[data-puact^="ack:"]')
    if await act.count():
        await act.first.click(); await pg.wait_for_timeout(500)
        await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(600)
        t = await toast(pg)
        c.ok(t.startswith('Needs Address') and 'not sent' in t and 'Open' in t, f'phone: the reply toast says Needs Address, not sent ({t[:200]})')
    else:
        c.ok(False, 'phone: the confirmation that differs is a Needs You row on Orders')
    c.ok(not errs, f'phone: no page errors ({errs[:3]})')
    await b.close()

SECTIONS = ['lint', 'reader', 'desk', 'phone']

async def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--section', default=','.join(SECTIONS))
    a = ap.parse_args(); c = Checks()
    async with async_playwright() as p:
        for s in a.section.split(','):
            print(f'-- {s}', flush=True)
            if s == 'lint': s_lint(c)
            elif s == 'reader': await s_reader(p, c)
            elif s == 'desk': await s_desk(p, c)
            elif s == 'phone': await s_phone(p, c)
    sys.exit(c.done())

asyncio.run(main())
