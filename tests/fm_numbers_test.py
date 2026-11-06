#!/usr/bin/env python3
"""tests/fm_numbers_test.py: finished-material documents numbered per job (Alan, 11-06; src/fmnumbers.js).

A materials-template invoice is numbered in its job's FM series with a prefix from the job's address ("121State-FM14");
a materials estimate takes the same prefix and its own series ("121State-FME1"); every other document keeps the firm's
INV/EST number. Checked:
  - two jobs each produce FM1, with different prefixes;
  - a non-materials invoice keeps its INV number, and the INV sequence keeps no gap when a draft becomes FM;
  - the series continues after the job's highest FM (Selections' FM13 on 121 State; an imported FM3 on a job);
  - a void burns the number; a sent number never changes;
  - every number is 21 characters or fewer, a revision's too; no address falls back to the client's last name;
  - the number shown is the full number: the document viewer, the PDF and Cmd-K.
"""
import asyncio, os, re, sys
from harness import *

C = Checks()
MK = """([cid, pid, kind, tpl]) => { const c = DB.clients.find(x => x.id === cid);
  const d = newDoc(c, kind, { mode: 'items', template: tpl, fields: { projectId: pid, title: 'Finishes', lines: [{ id: uid('l'), item: 'Vanity', qty: 1, rate: 1200, taxable: true }] } });
  d.projectId = pid; if (tpl) d.template = tpl; docMark(d); render(); return { id: d.id, number: d.number }; }"""


async def main():
    async with async_playwright() as p:
        b, pg, errs = await open_app(p)
        await sign_in(pg, 'u_billing')
        await pg.evaluate("""() => { const src = DB.projects.find(p => p.id === 'p206'); window.fmJob = (id, cid, name, addr) => Object.assign(JSON.parse(JSON.stringify(src)), { id: id, clientId: cid, project: Object.assign({}, JSON.parse(JSON.stringify(src.project)), { name: name, addr: addr }) }); }""")
        seq0 = await pg.evaluate("() => DB.company.seq.inv")
        a = await pg.evaluate(MK, ['cl140', 'p140', 'invoice', 'materials'])
        z = await pg.evaluate(MK, ['cl206', 'p206', 'invoice', 'materials'])
        C.ok(a['number'] == '140Prospect-FM1' and z['number'] == '206Lenox-FM1', f'two jobs each start at FM1 with their own prefix ({a["number"]}, {z["number"]})')
        C.ok(await pg.evaluate("() => DB.company.seq.inv") == seq0, 'the INV sequence keeps no gap: the number a draft held before it became FM is given back')
        plain = await pg.evaluate(MK, ['cl140', 'p140', 'invoice', ''])
        C.ok(re.match(r'^INV-2026-\d{3}$', plain['number']) and plain['number'] == f'INV-2026-{seq0 + 1:03d}', f'a non-materials invoice keeps the firm\'s number, the next one ({plain["number"]})')
        k = await pg.evaluate(MK, ['cl121', 'p121', 'invoice', 'materials'])
        C.ok(k['number'] == '121State-FM14', f'121 State continues after its Selections\' FM13 ({k["number"]})')
        # an imported FM3 on a job: the series continues after it
        await pg.evaluate("""() => { const c = DB.clients.find(x => x.name === 'The Lindqvists'); DB.projects.push(fmJob('pfmx', c.id, 'The Lindqvists', ''));
          c.invoices.push({ id: 'imp3', type: 'invoice', number: 'FM3', status: 'paid', projectId: 'pfmx', date: '2026-08-01', lines: [{ id: 'li', item: 'Imported', qty: 1, rate: 500 }], discount: { type: 'pct', value: 0 }, taxRate: 0, mode: 'items', template: 'materials' }); }""")
        cidL = await pg.evaluate("() => DB.clients.find(x => x.name === 'The Lindqvists').id")
        imp = await pg.evaluate(MK, [cidL, 'pfmx', 'invoice', 'materials'])
        C.ok(imp['number'] == '145Hicks-FM4', f'after an imported FM3 the job\'s next is FM4, the prefix from the client\'s address when the job has none ({imp["number"]})')
        # void burns; sent never changes
        r = await pg.evaluate("""async (id) => { const c = DB.clients.find(x => x.id === 'cl140'), d = c.invoices.find(i => i.id === id);
          d.status = 'sent'; d.sentAt = today(); render(); const sent = d.number; d.status = 'void'; d.voidReason = 'test'; render();
          const n = newDoc(c, 'invoice', { mode: 'items', fields: { projectId: 'p140', lines: [] } }); n.projectId = 'p140'; n.template = 'materials'; docMark(n); render();
          return { sent: sent, after: d.number, next: n.number }; }""", a['id'])
        C.ok(r['after'] == r['sent'] == '140Prospect-FM1', f'a sent, then voided, number never changes ({r})')
        C.ok(r['next'] == '140Prospect-FM2', f'a void burns its number: the next is FM2 ({r["next"]})')
        # a deleted unsent FM draft burns too (never re-handed); a draft moved off materials takes an INV number
        q = await pg.evaluate("""() => { const c = DB.clients.find(x => x.id === 'cl206'), d = c.invoices.find(i => /^206Lenox-FM1$/.test(i.number));
          d.template = 'simple'; render(); return d.number; }""")
        C.ok(q.startswith('INV-2026-'), f'a draft moved off the materials template before it is sent takes the firm\'s number ({q})')
        z2 = await pg.evaluate(MK, ['cl206', 'p206', 'invoice', 'materials'])
        C.ok(z2['number'] == '206Lenox-FM2', f'its FM1 stays burned: the next is FM2 ({z2["number"]})')
        # estimates: the same prefix, their own series
        e = await pg.evaluate("""() => { const c = DB.clients.find(x => x.id === 'cl140'); const d = newDoc(c, 'estimate', { template: 'materials', fields: { projectId: 'p140' } }); d.projectId = 'p140'; render(); return d.number; }""")
        C.ok(e == '140Prospect-FME1', f'a materials estimate takes the job\'s prefix and its own series ({e})')
        est = await pg.evaluate("() => { const c = DB.clients.find(x => x.id === 'cl140'); return newDoc(c, 'estimate', { template: 'construction' }).number }")
        C.ok(est.startswith('EST-2026-'), f'a construction estimate keeps the EST number ({est})')
        # a revision keeps the number with -R1 and draws no new FM number
        rv = await pg.evaluate("""(id) => { const c = DB.clients.find(x => x.id === 'cl121'), d = c.invoices.find(i => i.id === id); d.status = 'sent'; d.sentAt = today();
          const n = lkRevise(c, d); render(); const nx = newDoc(c, 'invoice', { mode: 'items', fields: { projectId: 'p121' } }); nx.projectId = 'p121'; nx.template = 'materials'; docMark(nx); render();
          return { rev: n.number, next: nx.number }; }""", k['id'])
        C.ok(rv['rev'] == '121State-FM14-R1' and rv['next'] == '121State-FM15', f'a revision is FM14-R1 and the series goes on at FM15 ({rv})')
        # 21 characters, the longest street and the fallback
        L = await pg.evaluate("""() => { const c = DB.clients.find(x => x.name === 'Tom & Lily Nakamura'); c.propertyAddr = '12345 Kingsbridge Terrace East, Bronx';
          DB.projects.push(fmJob('pfml', c.id, 'Nakamura apartment', ''));
          const d = newDoc(c, 'invoice', { mode: 'items', fields: { projectId: 'pfml' } }); d.projectId = 'pfml'; d.template = 'materials'; docMark(d); render();
          const c2 = DB.clients.find(x => x.id === 'cl45'); const keep = c2.propertyAddr; c2.propertyAddr = '';
          DB.projects.push(fmJob('pfmn', c2.id, 'Rivera loft', 'Loft, DUMBO'));
          const f = newDoc(c2, 'invoice', { mode: 'items', fields: { projectId: 'pfmn' } }); f.projectId = 'pfmn'; f.template = 'materials'; docMark(f); render(); c2.propertyAddr = keep;
          const all = DB.clients.flatMap(x => [...x.invoices, ...x.estimates]).map(x => x.number);
          return { long: d.number, fallback: f.number, over: all.filter(n => /FM/.test(n) && (n + '-R9').length > 21) }; }""")
        C.ok(len(L['long']) <= 21 and L['long'].startswith('12345Kings'), f'a long street is cut so the number is 21 characters or fewer, with room for -R9 ({L["long"]}, {len(L["long"])})')
        C.ok(L['fallback'] == 'Rivera-FM1', f'no house number anywhere: the client\'s last name ({L["fallback"]})')
        C.ok(not L['over'], f'every FM number has room for a revision inside 21 characters ({L["over"]})')
        # the full number everywhere: the viewer, the PDF, Cmd-K
        await pg.evaluate("(id) => { clientOpen = 'cl121'; docOpen = { kind: 'invoice', id: id }; view = 'billing'; render(); }", k['id'])
        await pg.wait_for_timeout(300)
        h = await pg.evaluate("() => ((document.querySelector('#dv h2') || {}).textContent || '') + ' | ' + ((document.querySelector('#dv .dv-doc') || {}).innerText || '')")
        C.ok('121State-FM14' in h.split(' | ')[0] and '121State-FM14' in h.split(' | ')[1], f'the document viewer and the document read 121State-FM14 ({h[:60]})')
        async with pg.expect_download() as dl:
            await pg.locator('#dv [data-dvact="pdf"]').click()
        raw = open(await (await dl.value).path(), 'rb').read()
        C.ok(b'121State-FM14' in raw, 'the PDF carries the full number')
        await pg.evaluate('dvClose()')
        await pg.keyboard.press('Control+k')
        await pg.wait_for_selector('#pal.on', timeout=5000)
        await pg.keyboard.type('121State-FM14')
        await pg.wait_for_timeout(500)
        t = await pg.evaluate("() => (document.querySelector('#pal') || {}).innerText || ''")
        C.ok('121State-FM14' in t, 'Cmd-K finds it by the full number')
        C.ok(await pg.evaluate("() => DB.audit.some(a => a.action === 'numbered' && /140Prospect-FM1/.test(a.note))"), 'each FM number is written to the audit trail with what it replaced')
        # a draft deleted before it is sent gives its number back (no FM3 then FM5); a void keeps its number burned
        g = await pg.evaluate("""async () => { const c = DB.clients.find(x => x.id === 'cl140'), mk = () => { const d = newDoc(c, 'invoice', { mode: 'items', fields: { projectId: 'p140', lines: [] } }); d.projectId = 'p140'; d.template = 'materials'; docMark(d); render(); return d; };
          const a = mk(), b2 = mk(), keep = appConfirm; appConfirm = () => true;
          try { await docAction(c, b2, 'del'); await docAction(c, a, 'del'); } finally { appConfirm = keep; }
          const n1 = mk(), n2 = mk(); return { a: a.number, b: b2.number, n1: n1.number, n2: n2.number, audit: DB.audit.some(r => r.action === 'number-given-back') }; }""")
        C.ok(g['n1'] == g['a'] and g['n2'] == g['b'] and g['a'] == '140Prospect-FM3', f'two drafts deleted before they were sent give FM3 and FM4 back; the next drafts take them, in order ({g})')
        C.ok(g['audit'], 'giving a number back writes an audit row')
        # a sent invoice is never written on a draw; the one-time backfill links the ones already sent, each with an audit row
        bf = await pg.evaluate("""() => { const c = DB.clients.find(x => x.id === 'cl121'), it = DB.sel.items.find(i => i.projectId === 'p121');
          const e = newDoc(c, 'estimate', { template: 'materials', fields: { projectId: 'p121' } }); e.projectId = 'p121'; e.lines = [{ id: 'lbf1', selId: it.id, item: it.name, qty: 1, rate: 90 }];
          const s = newDoc(c, 'invoice', { mode: 'items' }); s.template = 'materials'; s.projectId = 'p121'; s.status = 'sent'; s.sentAt = today();
          s.lines = [{ id: uid('l'), item: it.name, qty: 1, rate: 90, fromLine: ctKey(e, e.lines[0]) }]; render();
          const drawn = !!s.lines[0].selId;
          delete DB.company.fmLinkBackfill; render();
          return { drawn: drawn, linked: s.lines[0].selId === it.id, audit: DB.audit.some(r => r.action === 'line-linked' && r.refId === s.id), once: !!DB.company.fmLinkBackfill }; }""")
        C.ok(not bf['drawn'], 'a sent finished-material invoice is not written to on a draw (drafts only)')
        C.ok(bf['linked'] and bf['audit'] and bf['once'], f'the one-time backfill links a sent invoice\'s line to its selection, with an audit row ({bf})')
        # the invoice's lines name their selection and the order line that bought it (lane P5's item table reads them)
        await pg.keyboard.press('Escape')
        L = await pg.evaluate("""() => { const c = DB.clients.find(x => x.id === 'cl121'), it = DB.sel.items.find(i => i.projectId === 'p121');
          let po = (DB.pos || []).find(p => p.projectId === 'p121' && (p.lines || []).some(l => l.selId === it.id) && !['void', 'cancelled', 'draft'].includes(p.status));
          if (!po) { po = { id: 'pofm', number: 'PO-2026-990', projectId: 'p121', vendor: it.vendor || 'Ferguson', status: 'sent', lines: [{ id: 'plfm', selId: it.id, item: it.name, qty: 1, price: 100 }] }; DB.pos.push(po); }
          const pl = po.lines.find(l => l.selId === it.id);
          const e = newDoc(c, 'estimate', { template: 'materials', fields: { projectId: 'p121' } }); e.projectId = 'p121'; e.status = 'approved';
          e.lines = [{ id: 'lfe1', selId: it.id, item: it.name, qty: 1, rate: 250, taxable: true }, { id: 'lfe2', item: 'Delivery', qty: 1, rate: 75 }];
          const inv = newDoc(c, 'invoice', { mode: 'items' }); inv.template = e.template; inv.projectId = 'p121'; inv.fromDoc = e.id;
          inv.lines = e.lines.map(l => ({ id: uid('l'), item: l.item, qty: l.qty, rate: l.rate, taxable: l.taxable, fromLine: ctKey(e, l), pct: 100 })); docMark(inv); render();
          return { est: e.number, inv: inv.number, sel: inv.lines[0].selId === it.id, po: inv.lines[0].poLineId === pl.id && inv.lines[0].poId === po.id, plain: !inv.lines[1].selId && !inv.lines[1].poLineId, amt: docTotal(inv).sub }; }""")
        C.ok(L['sel'] and L['po'] and L['plain'] and L['amt'] == 325, f'a materials invoice from the estimate carries each line\'s selId and the PO line that bought it; links only, the amounts unchanged ({L})')
        C.ok(re.match(r'^121State-FME\d+$', L['est']) and re.match(r'^121State-FM\d+$', L['inv']), f'the materials estimate and its invoice share the job\'s prefix ({L["est"]}, {L["inv"]})')
        C.ok(not errs, f'no page errors ({errs[:2]})')
        await b.close()
    sys.exit(C.done())

asyncio.run(main())
