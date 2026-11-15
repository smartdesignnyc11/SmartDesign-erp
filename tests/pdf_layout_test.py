"""The PDF a client gets is the document on screen, laid out for paper (owner, 11-15). Invented data only.

The owner downloaded a proposal on his phone: section titles printed on top of their subtotals ("GENE$19,850NDITIONS"),
each item ran into its description, page 1 stopped a third of the way down, the client's name printed twice, and it
did not look like the firm's document. Printing the same proposal from the phone split rows across pages, dropped
the column header after page 1 and left the signature alone on the last page.

For every kind of client document, on the desktop (1440) and the phone (390), the Download PDF button's file is read
with pdfplumber and must hold:
  1  no two words' boxes overlap on any page (the "GENE$19,850NDITIONS" class);
  2  a section title starts where the "#" column starts, and its subtotal ends on the Amount column's right edge;
  3  every amount in the Amount column ends on one x, under the header's label;
  4  an item is its own line, in a larger size than its description below it;
  5  no page ends on a section band; no page but the last leaves more than 12% of the page blank unless the row that
     follows is taller than the gap; the column header heads every page the table continues onto; a row shorter
     than a third of a page never splits;
  6  the words are the on-screen document's words (nothing dropped or doubled), the Amount column reads in the same
     order, and the document's total (docTotal) is printed to the cent;
  7  the client's name prints once under Prepared For when the contact is the client; a lump-sum line leaves Rate blank.
The print (cxDocHtml with print on, through Chromium's page.pdf at Letter) is held to 1, 5, 6 and 7, and the
signature never stands on a page with less than one block above it. Chromium is the only print engine this can run;
Safari's print on an iPhone is not tested here.
Samples go to SD_PDF_OUT when it is set (one of each kind), for a person to look at.
"""
import asyncio, base64, collections, io, os, re, sys
import pdfplumber
from harness import *

C = Checks()
OUT = os.environ.get('SD_PDF_OUT', '')
OUT and os.makedirs(OUT, exist_ok=True)
MONEY = re.compile(r'^[–−-]?\$[\d,]+(\.\d\d)?$')

# ---- invented documents: a long sectioned proposal and the plain kinds the demo lacks -----------------------------
MAKE = r"""() => {
  const c = DB.clients.find(x => x.id === 'cl121');
  c.contacts = c.contacts || [];
  // the contact is the client: the name must print once
  const pc = c.contacts.find(x => x.primary) || c.contacts[0];
  window.__pdfKeep = { name: pc ? pc.name : null };
  pc && (pc.name = c.name);
  const L = (id, item, qty, rate, x) => Object.assign({ id, item, desc: '', qty, unit: 'ls', rate, taxable: false, cat: 'construction', code: '01' }, x || {});
  const put = (list, d) => { c[list] = (c[list] || []).filter(e => e.id !== d.id); c[list].push(d); docMark && docMark(d); return d; };
  const base = { status: 'sent', date: today(), projectId: 'p121', taxRate: 0, discount: { type: 'pct', value: 0 }, terms: 'Net 15', memo: '' };
  const words = ['Protect existing finishes throughout the work', 'Remove and cart debris to an approved transfer station', 'Coordinate access with the building super',
    'Patch and prime all disturbed surfaces', 'Allowance reconciled against actual quantities at unit prices', 'Owner supplies fixtures; we set and connect'];
  const secs = ['General Conditions', 'Demolition', 'Carpentry', 'Plumbing', 'Electrical', 'Finishes'];
  const lines = [];
  let k = 0;
  secs.forEach((g, si) => {
    const n = si === 1 ? 1 : 11;
    for (let i = 0; i < n; i++, k++) {
      const ds = words.slice(0, 1 + (k % 3)).map((w, j) => '- ' + words[(k + j) % words.length]).join('\n');
      lines.push(L('pl' + k, ['Temporary protection', 'Selective demolition', 'Framing and blocking', 'Rough plumbing', 'Panel and feeders', 'Paint'][si] + ' ' + (i + 1), 1, 1500 + 37 * k, { group: g, desc: ds }));
    }
  });
  lines[3].item = 'Temporary protection of the stair hall, the parlor floor and the garden level, with daily cleaning and a final clean at completion';
  lines[5].desc = Array.from({ length: 9 }, (_, i) => '- ' + words[i % words.length] + ', item ' + (i + 1)).join('\n');
  lines[14].rate = 148250;
  lines[20] = Object.assign(lines[20], { excluded: true, desc: 'By others' });
  lines[22] = Object.assign(lines[22], { tbd: true });
  lines[25] = Object.assign(lines[25], { qty: 120, unit: 'sf', rate: 14.5 });
  lines[30] = Object.assign(lines[30], { item: 'Credit for owner-supplied tile', rate: -1850, desc: '' });
  const est = put('estimates', Object.assign({ id: 'pdfE1', type: 'estimate', number: 'EST-PDF-001', template: 'construction', title: 'Invented proposal', validUntil: today(), lines }, base, { status: 'sent' }));
  const flat = put('estimates', Object.assign({ id: 'pdfE2', type: 'estimate', number: 'EST-PDF-002', template: 'materials', title: 'Invented materials quote', lines: [
    L('f1', 'Wide plank oak flooring', 640, 11.25, { unit: 'sf', desc: 'Rift and quartered, 7 inch' }), L('f2', 'Stair nosing', 14, 85, { unit: 'ea' }), L('f3', 'Delivery', 1, 350)] }, base));
  const inv = put('invoices', Object.assign({ id: 'pdfI1', type: 'invoice', number: 'INV-PDF-001', mode: 'items', title: 'Invented invoice', due: today(), lines: [
    L('i1', 'Kitchen cabinets', 1, 18400, { desc: 'Supply and install, per the approved shop drawings' }), L('i2', 'Countertop template and install', 42, 165, { unit: 'sf' }), L('i3', 'Hardware', 36, 22.5, { unit: 'ea' })] }, base));
  // a progress invoice billed line by line against the proposal, with its quantities
  const pinv = put('invoices', Object.assign({ id: 'pdfI2', type: 'invoice', number: 'INV-PDF-002', mode: 'items', title: 'Progress on the invented proposal', due: today(),
    lines: lines.slice(24, 30).filter(l => !l.excluded && !l.tbd).map((l, i) => Object.assign({}, l, { id: 'pp' + i, estId: 'pdfE1', estLineId: l.id, qty: 1, unit: 'ls', rate: r2(l.qty * l.rate / 2), group: '' })) }, base));
  const cm = dvCreditCreate(c, inv, [{ lineId: 'i1', amount: 1200 }], 'Damaged door replaced by the maker');
  return { cm: cm && cm.memo ? cm.memo.id : (cm && cm.cm ? cm.cm.id : (c.invoices.find(x => x.creditMemo && x.creditOf === 'pdfI1') || {}).id) };
}"""

DOCS = [  # (label, kind, id, client)
    ('proposal-sections', 'estimate', 'pdfE1', 'cl121'),
    ('proposal-flat-qty', 'estimate', 'pdfE2', 'cl121'),
    ('proposal-construction-demo', 'estimate', 'es13881', 'cl121'),
    ('proposal-design', 'estimate', 'esD45', 'cl45'),
    ('invoice', 'invoice', 'pdfI1', 'cl121'),
    ('invoice-progress-qty', 'invoice', 'pdfI2', 'cl121'),
    ('invoice-deposit', 'invoice', 'in1', 'cl121'),
    ('pay-application', 'invoice', 'in3', 'cl121'),
    ('design-fee-milestone', 'invoice', 'inD45m1', 'cl45'),
    ('design-retainer', 'invoice', 'inD45r', 'cl45'),
    ('change-order', 'co', 'co1', 'cl121'),
    ('vendor-bill', 'bill', 'b1', ''),
]

INFO = r"""([kind, id, cid]) => {
  const r = dvFind(kind, id, cid);
  if (!r) return null;
  const host = document.createElement('div');
  host.style.cssText = 'position:absolute;left:-30000px;top:0;width:860px';
  host.innerHTML = `<style>${CX_CSS}</style>` + dvDocHtml(r);
  document.body.appendChild(host);
  const root = host.querySelector('.cxd'), dr = root.querySelector('.cxd-draft'); dr && dr.remove();
  const text = root.innerText;
  const amounts = [...root.querySelectorAll('table')].slice(0, 1).flatMap(t => [...t.querySelectorAll('tbody tr')].map(tr => { const td = tr.lastElementChild; return td && td.firstChild ? (td.firstChild.textContent || '').trim() : ''; })).filter(s => /\$/.test(s));
  const secs = [...root.querySelectorAll('tr.cx-sec')].map(tr => [tr.children[0].innerText.trim(), tr.lastElementChild.innerText.trim()]);
  const items = [...root.querySelectorAll('table')].slice(0, 1).flatMap(t => [...t.querySelectorAll('tbody tr:not(.cx-sec)')].map(tr => { const td = tr.children[1]; if (!td) return null; const ds = td.querySelector('.ds'); return { item: (td.firstChild && td.firstChild.nodeType === 3 ? td.firstChild.textContent : '').trim(), ds: ds ? ds.innerText.trim() : '', lump: /^Lump sum$/.test((tr.children[2] || {}).innerText || ''), rate: ((tr.children[3] || {}).innerText || '').trim(), cols: tr.children.length }; })).filter(Boolean);
  const heads = [...root.querySelectorAll('table')].slice(0, 1).flatMap(t => [...t.querySelectorAll('thead th')].map(th => th.innerText.trim()));
  host.remove();
  const total0 = kind === 'bill' ? billTotal(r.b) : (r.d.mode === 'sov' && typeof payAppData === 'function' && cxKind(r.d) === 'progress' ? payAppData(r.c, r.d).due : docTotal(r.d).total);
  const total = r.kind === 'credit' ? Math.abs(total0) : total0;
  return { text, amounts, secs, items, heads, total: money(total), client: r.c ? r.c.name : '', number: kind === 'bill' ? r.b.number : r.d.number };
}"""


def toks(s):
    s = s.replace('−', '-').replace('–', '-').replace('—', '-').replace(' ', ' ')
    return [t for t in re.split(r'[\s\-]+', s) if t]


def doc_words(pdf):
    """the words of each page, upright only (a DRAFT stamp is turned), with the page's footer cut off"""
    P = []
    for pg in pdf.pages:
        # a turned word (the DRAFT stamp) is not part of the text: keep the chars set straight
        flat = pg.filter(lambda o: o.get('object_type') != 'char' or (abs(o['matrix'][1]) < 0.01 and abs(o['matrix'][2]) < 0.01))
        ws = flat.extract_words(extra_attrs=['fontname', 'size'], keep_blank_chars=False, use_text_flow=False)
        P.append({'h': pg.height, 'w': pg.width, 'words': [w for w in ws if w['bottom'] < pg.height - 40], 'foot': [w for w in ws if w['bottom'] >= pg.height - 40]})
    return P


def lines_of(words, tol=2.5):
    L = []
    for w in sorted(words, key=lambda w: (round(w['top']), w['x0'])):
        if L and abs(L[-1][0]['top'] - w['top']) < tol: L[-1].append(w)
        else: L.append([w])
    return [sorted(l, key=lambda w: w['x0']) for l in L]


def overlaps(words):
    bad = []
    for i, a in enumerate(words):
        for b in words[i + 1:]:
            ox = min(a['x1'], b['x1']) - max(a['x0'], b['x0'])
            oy = min(a['bottom'], b['bottom']) - max(a['top'], b['top'])
            if ox > 0.6 and oy > 1.0: bad.append(f"{a['text']!r} on {b['text']!r}")
    return bad


# Chromium's print writes some punctuation of its embedded fonts as private-use characters: read them back
PUA = {'\ue081': '(', '\ue082': ')', '\ue088': '-', '\ue09e': '-'}


def norm(s):
    s = ''.join(PUA.get(c, c) for c in s)
    return [c for c in s.replace('\u2212', '-').replace('\u2013', '-').replace('\u2014', '-') if not c.isspace() and not '\ue000' <= c <= '\uf8ff']


def dash(s):
    return s.replace('\u2013', '-').replace('\u2212', '-').replace(' ', '')


def check_pdf(tag, raw, info, printed=False):
    pdf = pdfplumber.open(io.BytesIO(raw))
    P = doc_words(pdf)
    n = len(P)
    # 1 overlaps
    for i, p in enumerate(P):
        bad = overlaps(p['words'])
        C.ok(not bad, f'{tag} p{i + 1}: no two words on top of each other ({bad[:3]})')
    heads = [h.upper() for h in info['heads'] if h]
    def head_line(p, anywhere=False):
        # the header row: a "#" with the second column's label in the same type beside it (labels may wrap to
        # two or three lines); on a continuation page it is the first thing on the page
        if len(heads) < 2: return None
        top = min((w['top'] for w in p['words']), default=0)
        for h in p['words']:
            if h['text'] != '#' or (not anywhere and h['top'] - top > 26): continue
            H = [w for w in p['words'] if w['fontname'] == h['fontname'] and abs(w['size'] - h['size']) < 0.2 and abs(w['top'] - h['top']) < 26 and w['x0'] >= h['x0'] - 1]
            if heads[1].split()[0] in [w['text'] for w in H]: return sorted(H, key=lambda w: w['x0'])
        return None
    first = next((i for i, p in enumerate(P) if head_line(p, True)), None)
    hl = head_line(P[first], True) if first is not None else None
    amt_x1 = max(w['x1'] for w in hl) if hl else None
    num_x0 = hl[0]['x0'] if hl else None
    # 2 sections: the title where "#" starts, the subtotal on the Amount edge, on one line
    def rowlines(p):
        out = []
        for l in lines_of(p['words']):
            t = ' '.join(w['text'] for w in l)
            if num_x0 is not None and abs(l[0]['x0'] - num_x0) < 3 and re.match(r'^\d+(-\d+)?$', l[0]['text']) or any(t.startswith(nm.upper()) for nm, _ in info['secs']): out.append(l)
        return out
    sec_tops = []
    for name, sub in info['secs']:
        found = False
        for pi, p in enumerate(P):
            for l in lines_of(p['words']):
                t = ' '.join(w['text'] for w in l)
                if t.startswith(name.upper()) and l[-1]['text'] == sub:
                    found = True
                    sec_tops.append((pi, l[0]['top']))
                    if not printed:
                        C.ok(num_x0 is not None and abs(l[0]['x0'] - num_x0) < 2.5, f'{tag}: section {name} starts at the "#" column ({l[0]["x0"]:.1f} vs {num_x0})')
                        C.ok(amt_x1 is not None and abs(l[-1]['x1'] - amt_x1) < 2.5, f'{tag}: section {name} subtotal ends on the Amount edge ({l[-1]["x1"]:.1f} vs {amt_x1})')
        C.ok(found, f'{tag}: section {name} reads "{name.upper()} ... {sub}" on one line, title and subtotal apart')
    # 3 the Amount column: every figure ends on one x
    if amt_x1 is not None and info['amounts'] and not printed:
        right = [l[-1] for p in P for l in rowlines(p) if MONEY.match(l[-1]['text']) and abs(l[-1]['x1'] - amt_x1) < 30]
        off = [(w['text'], round(w['x1'], 1)) for w in right if abs(w['x1'] - amt_x1) > 1.5]
        C.ok(right and not off, f'{tag}: the Amount column ends on one x under its label ({off[:4]})')
    # 4 an item is its own line, larger than its description
    sizes = {}
    for it in info['items'][:40]:
        if not it['item'] or not it['ds']: continue
        a = toks(it['item'])[0]
        d = toks(it['ds'])[0]
        for p in P:
            ls = lines_of(p['words'])
            for li, l in enumerate(ls):
                t = [w['text'] for w in l]
                if a in t and li + 1 < len(ls) and ls[li + 1][0]['text'].lstrip('-') == d.lstrip('-') or (a in t and li + 1 < len(ls) and d in [w['text'] for w in ls[li + 1]]):
                    wi = l[t.index(a)]
                    wd = next(w for w in ls[li + 1] if w['text'] == d or w['text'].lstrip('-') == d.lstrip('-'))
                    sizes[it['item']] = (wi['size'], wd['size'], 'Bold' in wi['fontname'], 'Bold' in wd['fontname'])
                    break
            if it['item'] in sizes: break
    with_ds = [it for it in info['items'] if it['item'] and it['ds']]
    if with_ds:
        bad = [k for k, v in sizes.items() if not (v[0] > v[1] + 0.3 or (v[2] and not v[3]))]
        C.ok(len(sizes) >= min(3, len(with_ds)) and not bad, f'{tag}: each item is its own line above a smaller description ({len(sizes)} of {len(with_ds)} found; wrong {bad[:2]})')
    # 5 pages: no band last, little blank, the header on each continuation, rows whole
    for pi, p in enumerate(P[:-1]):
        ls = lines_of(p['words'])
        if not ls: continue
        last = ' '.join(w['text'] for w in ls[-1])
        C.ok(not any(last.startswith(nm.upper()) for nm, _ in info['secs']), f'{tag} p{pi + 1}: the page does not end on a section band ({last[:40]})')
        bottom = max(w['bottom'] for w in p['words'])
        gap = (p['h'] - 50 - 30) - bottom
        nl = lines_of(P[pi + 1]['words'])
        start = 1 if nl and head_line(P[pi + 1]) is not None else 0
        # the block that did not fit: the next page's first row (to the next row number or band)
        blk_top = nl[start][0]['top'] if len(nl) > start else 0
        blk_end = next((l[0]['top'] for l in nl[start + 1:] if (num_x0 is not None and abs(l[0]['x0'] - num_x0) < 3 and re.match(r'^\d', l[0]['text'])) or any(' '.join(w['text'] for w in l).startswith(nm.upper()) for nm, _ in info['secs'])), None)
        blk = (blk_end or (nl[-1][-1]['bottom'] if nl else 0)) - blk_top
        C.ok(gap < 0.12 * p['h'] or blk > gap - 4, f'{tag} p{pi + 1}: the page runs to its bottom margin ({gap:.0f}pt blank; the next block is {blk:.0f}pt)')
    if first is not None:
        for pi in range(first + 1, n):
            p = P[pi]
            has_rows = any(num_x0 is not None and abs(w['x0'] - num_x0) < 3 and re.match(r'^\d+(-\d+)?$', w['text']) for w in p['words'])
            if has_rows:
                C.ok(head_line(p) is not None, f'{tag} p{pi + 1}: the column header heads the page the table continues onto')
    # rows whole: an item shorter than a third of a page has its title and its last description words on one page
    allpages = [' '.join(w['text'] for w in p['words']) for p in P]
    for it in info['items']:
        if not it['item'] or not it['ds'] or it['ds'].count('\n') > 7: continue
        a = ' '.join(toks(it['item'])[:3])
        z = ' '.join(toks(it['ds'])[-3:])
        pa = [i for i, s in enumerate(allpages) if a in ' '.join(toks(s))]
        pz = [i for i, s in enumerate(allpages) if z in ' '.join(toks(s))]
        if pa and pz:
            C.ok(bool(set(pa) & set(pz)), f'{tag}: row "{it["item"][:30]}" is on one page (title on {pa}, last words on {pz})')
    # 6 the words are the document's words; the totals print
    # compared letter by letter, so a line the render broke differently (after a hyphen) still counts as the same text
    got = collections.Counter(c for p in P for w in p['words'] for c in norm(w['text']))
    # the repeated header lines are not the document's words a second time
    for pi in range(n):
        if first is not None and pi > first:
            for w in head_line(P[pi]) or []:
                for c in norm(w['text']): got[c] -= 1
    got = +got
    want = collections.Counter(norm(info['text']))
    miss = list((want - got).elements())
    extra = list((got - want).elements())
    C.ok(not miss and not extra, f'{tag}: the PDF has the on-screen words, nothing dropped or doubled (missing {miss[:8]}, extra {extra[:8]})')
    if info['amounts'] and amt_x1 is not None and not printed:
        seq = [dash(l[-1]['text']) for p in P for l in rowlines(p) if MONEY.match(l[-1]['text']) and abs(l[-1]['x1'] - amt_x1) < 1.5]
        dom = [dash(a) for a in info['amounts']]
        C.ok(seq == dom, f'{tag}: the Amount column reads in the document\'s order ({seq[:5]} vs {dom[:5]})')
    flat = ' '.join(allpages)
    C.ok(info['total'] in flat, f'{tag}: the total {info["total"]} is printed')
    # 7 the client's name once under Prepared For; a lump sum has no Rate
    if info['client']:
        alone = flat.count(info['client']) - flat.count('Accepted by ' + info['client'])
        C.ok(alone == 1, f'{tag}: the client\'s name prints once as its own line ({alone})')
    lumps = [it for it in info['items'] if it['lump']]
    C.ok(all(not it['rate'] for it in lumps), f'{tag}: a lump-sum line leaves Rate blank ({[it["rate"] for it in lumps if it["rate"]][:3]})')
    if printed:
        # the signature is never alone: something more than one line stands above it on its page
        for pi, p in enumerate(P):
            ls = lines_of(p['words'])
            for li, l in enumerate(ls):
                if ' '.join(w['text'] for w in l).startswith('Accepted by'):
                    C.ok(li >= 3, f'{tag} p{pi + 1}: the signature keeps the text above it on its page ({li} lines above)')
    return n


async def download(pg, kind, id, cid):
    # the viewer's own Download PDF (a draft opens in the editor, so the writer is called as the button calls it)
    async with pg.expect_download() as dl:
        await pg.evaluate("([k, id, cid]) => { dvPdf(dvFind(k, id, cid)); }", [kind, id, cid])
    d = await dl.value
    raw = open(await d.path(), 'rb').read()
    await pg.evaluate("() => typeof dvClose === 'function' && dvClose()")
    return raw, d.suggested_filename


async def main():
    async with async_playwright() as p:
        for phone in (False, True):
            dev = 'phone' if phone else 'desktop'
            b = await p.chromium.launch()
            ctx = await b.new_context(viewport=PHONE if phone else DESKTOP, is_mobile=phone, has_touch=phone, accept_downloads=True)
            pg = await ctx.new_page()
            errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.goto(URL)
            await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
            await sign_in(pg, 'u_owner')
            made = await pg.evaluate(MAKE)
            docs = DOCS + ([('credit-memo', 'invoice', made['cm'], 'cl121')] if made.get('cm') else [])
            C.ok(bool(made.get('cm')), f'{dev}: a credit memo was issued to download')
            for label, kind, id, cid in docs:
                info = await pg.evaluate(INFO, [kind, id, cid])
                if not info:
                    C.ok(False, f'{dev} {label}: {kind} {id} is in the demo'); continue
                raw, fname = await download(pg, kind, id, cid)
                C.ok(raw.startswith(b'%PDF') and fname.endswith('.pdf'), f'{dev} {label}: Download PDF gives a .pdf ({fname})')
                if OUT and not phone: open(os.path.join(OUT, f'{label}.pdf'), 'wb').write(raw)
                pages = check_pdf(f'{dev} {label}', raw, info)
                print(f'  {dev} {label}: {pages} page(s)')
            # print: the same document through Chromium's print, at Letter
            if not phone:
                for label, kind, id, cid in [('proposal-sections', 'estimate', 'pdfE1', 'cl121'), ('pay-application', 'invoice', 'in3', 'cl121'), ('change-order', 'co', 'co1', 'cl121')]:
                    info = await pg.evaluate(INFO, [kind, id, cid])
                    html = await pg.evaluate("([k, id, cid]) => { const r = dvFind(k, id, cid); return cxDocHtml(r.c, r.d, { print: false }); }", [kind, id, cid])
                    pp = await ctx.new_page()
                    await pp.set_content(html)
                    raw = await pp.pdf(format='Letter', prefer_css_page_size=True)
                    await pp.close()
                    if OUT: open(os.path.join(OUT, f'print-{label}.pdf'), 'wb').write(raw)
                    pages = check_pdf(f'print {label}', raw, info, printed=True)
                    print(f'  print {label}: {pages} page(s)')
            C.ok(not errs, f'{dev}: no page errors ({errs[:2]})')
            await b.close()
    sys.exit(C.done())


asyncio.run(main())
