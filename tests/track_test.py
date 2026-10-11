"""track_test: BACKLOG §1.9, order documents on the PO and the bill, the line-up check, the promise ledger,
tracking against the schedule, vendor follow-ups within delegation, missing documents, learning, Ask.

Every document here is invented. The line-up math is checked independently in Python (expected cases are
computed here from the invented figures, not read back from the app).
  python3 track_test.py      # prints ALL PASS (n checks) or each failure
"""
import asyncio, re, base64, json
from harness import *

TOL = 1.0          # the owner's rounding tolerance (DB.company.track.tol default)
RATE = 0.08875     # NYC sales / use tax

def inv(number, lines, po='PO-2026-990', vendor='NEMO TILE', job='121 State Street', tax=None, freight=100.0,
        subtotal=None, total=None, terms='2/10 NET 30', extra=''):
    """An invented invoice's text. lines: (item, qty, unit, price, ext or None for qty*price)."""
    L, s = [], 0.0
    for it, q, u, p, e in lines:
        e = round(q * p, 2) if e is None else e
        s += e
        L.append(f'{it}   {q} {u} @ ${p:,.2f}   ${e:,.2f}')
    sub = round(s, 2) if subtotal is None else subtotal
    tx = round(sub * RATE, 2) if tax is None else tax
    tot = round(sub + tx + freight, 2) if total is None else total
    return (f'{vendor}\nInvoice No. {number}\nDate: 09/03/2026\nJob: {job}\nAgainst {po}\n\n' + '\n'.join(L) +
            f'\n\nSubtotal ${sub:,.2f}\nSales tax 8.875%   ${tx:,.2f}\nFreight   ${freight:,.2f}\nTotal due ${tot:,.2f}\nTerms: {terms}\n{extra}')

CLEAN = [('Carrara mosaic 2x2', 48, 'sf', 18.0, None), ('White subway tile 3x6', 192, 'sf', 8.0, None)]
# the clean invoice, by hand: 48 x 18 = 864, 192 x 8 = 1,536, subtotal 2,400, tax 213.00, freight 100, total 2,713.00
assert round(48 * 18 + 192 * 8, 2) == 2400.0 and round(2400 * RATE, 2) == 213.0 and round(2400 + 213 + 100, 2) == 2713.0

# each mismatch type: (code, PO key, invoice text) — the figures differ from the clean case in one place
def cases():
    C = [
        ('vendor',    't1', inv('NT-9201', CLEAN, vendor='WINDOW WORKS')),
        ('job',       't1', inv('NT-9202', CLEAN, job='45 Cranberry St')),
        ('poRef',     't1', inv('NT-9203', CLEAN, po='PO-2026-041')),
        ('qty',       't1', inv('NT-9204', [('Carrara mosaic 2x2', 50, 'sf', 18.0, None), CLEAN[1]])),
        ('price',     't1', inv('NT-9205', [('Carrara mosaic 2x2', 48, 'sf', 19.0, None), CLEAN[1]])),
        ('ext',       't1', inv('NT-9206', [('Carrara mosaic 2x2', 48, 'sf', 18.0, 900.0), CLEAN[1]])),
        ('subtotal',  't1', inv('NT-9207', CLEAN, subtotal=2500.0, tax=213.0, total=2813.0)),
        ('taxRate',   't1', inv('NT-9208', CLEAN, tax=180.0)),
        ('freight',   't1', inv('NT-9209', CLEAN, freight=250.0)),
        ('total',     't1', inv('NT-9210', CLEAN, total=2800.0)),
        ('notOnPO',   't1', inv('NT-9211', CLEAN + [('Schluter edge trim', 10, 'ea', 12.0, None)])),
        ('terms',     't1', inv('NT-9212', CLEAN, terms='NET 10')),
        ('remit',     't1', inv('NT-9213', CLEAN, extra='We have changed our bank. Remit to: Nemo Tile, new account ending 9931')),
        ('beforeDelivery', 't3', inv('NT-9214', [('Glass mosaic accent', 30, 'sf', 22.0, None)], po='PO-2026-992', tax=0.0, freight=0.0, terms='')),
        ('taxExempt', 't2', inv('NT-9215', [('Marble threshold 36in', 4, 'ea', 10.5, None)], po='PO-2026-991', freight=0.0, terms='')),
        ('priceQuote', 't2', inv('NT-9216', [('Marble threshold 36in', 4, 'ea', 10.5, None)], po='PO-2026-991', tax=0.0, freight=0.0, terms='')),
        ('useTax',    't4', inv('NT-9217', [('Porcelain plank 8x48', 100, 'sf', 6.0, None)], po='PO-2026-993', tax=0.0, freight=0.0, terms='')),
    ]
    return C

SETUP = r"""() => {
  const P = (id, num, st, lines, o) => DB.pos.push(Object.assign({ id, number: num, projectId: 'p121', vendor: 'Nemo Tile', vendorId: 'v1', date: '2026-09-01',
    expected: '2026-09-10', status: st, shipTo: 'site', notes: '', lines, tax: 0, shipping: 0, taxStatus: 'taxable', type: 'materials', entityId: 'ent1', receipts: [], srcDocs: [] }, o || {}));
  P('tpo1', 'PO-2026-990', 'received', [{ id: 'tl1', item: 'Carrara mosaic 2x2', desc: '', qty: 48, unit: 'sf', price: 18, received: 48, line: '' },
    { id: 'tl2', item: 'White subway tile 3x6', desc: '', qty: 192, unit: 'sf', price: 8, received: 192, line: '' }], { shipping: 100, tax: 8.875, receipts: [{ date: '2026-09-03', t: '', by: 'Alex', lines: [], slip: '', note: '' }] });
  P('tpo2', 'PO-2026-991', 'received', [{ id: 'tl3', item: 'Marble threshold 36in', desc: '', qty: 4, unit: 'ea', price: 10.5, quotePrice: 10, received: 4, line: '' }], { taxStatus: 'exempt-ci' });
  P('tpo3', 'PO-2026-992', 'issued', [{ id: 'tl4', item: 'Glass mosaic accent', desc: '', qty: 30, unit: 'sf', price: 22, received: 0, line: '' }], { taxStatus: 'exempt-ci' });
  P('tpo4', 'PO-2026-993', 'received', [{ id: 'tl5', item: 'Porcelain plank 8x48', desc: '', qty: 100, unit: 'sf', price: 6, received: 100, line: '' }], { useTax: true });
  const B = (id, number, poId, amt, o) => DB.bills.push(Object.assign({ id, vendor: 'Nemo Tile', number, date: '2026-09-03', due: '2026-09-30', entityId: 'ent1', projectId: 'p121', poId,
    cat: 'materials', code: '08', line: '', lines: [{ id: id + 'l', desc: 'Tile', amount: amt }], payMethod: 'ACH', fileId: '', notes: '', status: 'submitted',
    approvals: [{ t: '', by: 'Chen', role: 'coord', action: 'submitted' }], createdBy: 'Chen', terms: '2/10 NET 30' }, o || {}));
  B('tb1', 'NT-9100', 'tpo1', 2713);
  B('tb2', 'NT-9300', '', 1040.68);
  B('tbd1', 'NT-7777', '', 500); B('tbd2', 'NT-7777', '', 500);
  save(); return true;
}"""

async def upload(pg, sel, name, text, mime='text/plain'):
    await pg.locator(sel).set_input_files({'name': name, 'mimeType': mime, 'buffer': text.encode('utf-8') if isinstance(text, str) else text})
    await pg.wait_for_function("() => !document.querySelector('#toast') || true")
    await pg.wait_for_timeout(500)

async def main():
    c = Checks()
    async with async_playwright() as p:
        b, pg, errs = await open_app(p)
        await sign_in(pg, 'u_chen')
        await pg.evaluate(SETUP)

        # ---- 1. upload on a PO (the real Add Document input), then on a bill: one invoice on both ----------
        await pg.evaluate("() => { flowGo.po(DB.pos.find(p => p.id === 'tpo1'))(); }"); await pg.wait_for_timeout(300)
        c.ok(await pg.locator('#trk-docs').count() == 1, 'the PO shows a Documents card')
        await upload(pg, '#trk-docs #trk-file', 'NT-9001.txt', inv('NT-9001', CLEAN))
        clean = await pg.evaluate("() => { const d = DB.docs.find(x => x.fields.number === 'NT-9001'); return d && { kind: d.kind, po: d.links.poId, ok: d.check.ok, cases: d.check.cases.map(x => x.code), checked: d.check.checked, hash: d.hash, verify: trkVerify(d) } }")
        c.ok(clean and clean['kind'] == 'invoice' and clean['po'] == 'tpo1', f'invoice uploaded on the PO is filed on it: {clean}')
        c.ok(clean and clean['ok'] and not clean['cases'], f'the clean invoice lines up with no case: {clean and clean["cases"]}')
        c.ok(clean and 'total' in clean['checked'] and 'subtotal' in clean['checked'], f'"Lines up" lists what was checked: {clean and clean["checked"]}')
        await pg.wait_for_timeout(200)
        tick = await pg.evaluate("() => (document.querySelector('#trk-docs') || {}).innerText || ''")
        c.ok('Lines up' in tick, 'the PO card shows the quiet Lines Up tick')
        # the bill: sign in as the owner (bills live under Accounting), add the same vendor's invoice for the bill
        await sign_in(pg, 'u_owner')
        await pg.evaluate("() => openBill('tb1')"); await pg.wait_for_timeout(400)
        c.ok(await pg.locator('#d-body #trk-docs').count() == 1, 'the bill shows a Documents card')
        await upload(pg, '#d-body #trk-docs #trk-file', 'NT-9100.txt', inv('NT-9100', [('Carrara mosaic 2x2', 48, 'sf', 19.0, None), CLEAN[1]], total=2713.0 + 48))
        both = await pg.evaluate("() => { const d = DB.docs.find(x => x.fields.number === 'NT-9100'); return d && { bill: d.links.billId, po: d.links.poId, cases: d.check.cases.map(x => x.code) } }")
        c.ok(both and both['bill'] == 'tb1' and both['po'] == 'tpo1', f'one invoice attaches to both its bill and its PO: {both}')

        # ---- 2. the original is sealed: a correction never overwrites it -------------------------------------
        h = await pg.evaluate("""() => { const d = DB.docs.find(x => x.fields.number === 'NT-9001'), h0 = d.hash, t0 = d.orig.fields.total;
            trkCorrect(d, 'total', 1, 'test edit'); try { d.orig = d.orig; } catch (e) {}
            return { same: d.hash === h0, verify: trkVerify(d), origTotal: d.orig.fields.total, t0, now: d.fields.total, corr: d.corrections.length } }""")
        c.ok(h['same'] and h['verify'] and h['origTotal'] == h['t0'] == 2713 and h['now'] == 1 and h['corr'] == 1, f'hash unchanged and original kept after an edit; the correction is appended: {h}')
        tam = await pg.evaluate("""() => { const d = DB.docs.find(x => x.fields.number === 'NT-9001'); const keep = d.orig.fields.total; d.orig.fields.total = 1; const v = trkVerify(d); d.orig.fields.total = keep; trkCorrect(d, 'total', 2713, 'undo test'); trkCheck(d); return [v, trkVerify(d)] }""")
        c.ok(tam == [False, True], f'a silent change to the original is caught by its hash: {tam}')

        # ---- 3. every mismatch type fires on its invented case, and not on the clean invoice -----------------
        pomap = {'t1': 'tpo1', 't2': 'tpo2', 't3': 'tpo3', 't4': 'tpo4'}
        for code, pk, text in cases():
            got = await pg.evaluate("""([t, po]) => { const r = trkIngest(t, { source: { type: 'upload', fileName: 'case.txt' }, links: { poId: po } }); const d = r.doc || r.docs[0];
                return d.check.cases.map(x => [x.code, x.money]) }""", [text, pomap[pk]])
            codes = [x[0] for x in got]
            c.ok(code in codes, f'mismatch {code} fires on its case: {got}')
            c.ok(code not in (clean['cases'] if clean else []), f'mismatch {code} does not fire on the clean invoice')
        # money at stake, checked independently: price 48 x (19 - 18) = 48; freight 250 - 100 = 150; ext 900 - 864 = 36;
        # tax 213 - 180 = 33 (under); before delivery 30 x 22 = 660; tax on exempt 4 x 10.5 x 8.875% = 3.73; use tax 600 x 8.875% = 53.25
        want = {'NT-9205': ('price', 48.0), 'NT-9209': ('freight', 150.0), 'NT-9206': ('ext', 36.0), 'NT-9208': ('taxRate', -33.0),
                'NT-9214': ('beforeDelivery', 660.0), 'NT-9215': ('taxExempt', round(42 * RATE, 2)), 'NT-9217': ('useTax', round(600 * RATE, 2))}
        for num, (code, amt) in want.items():
            m = await pg.evaluate("([n, k]) => { const d = DB.docs.find(x => x.fields.number === n); const cs = d && d.check.cases.find(x => x.code === k); return cs ? cs.money : null }", [num, code])
            c.ok(m is not None and abs(m - amt) < 0.01, f'{num} {code}: money at stake {m}, computed here {amt}')
        nx = await pg.evaluate("() => { const d = DB.docs.find(x => x.fields.number === 'NT-9213'); const k = d.check.cases.find(x => x.code === 'remit'); return k && [k.next, trkCaseAct(d.id, k.key, 'accept', 'looks fine') === null] }")
        c.ok(nx == ['callback', True], f'a changed bank is never accepted alone; it takes two people and a call-back: {nx}')
        cb = await pg.evaluate("""() => { const d = DB.docs.find(x => x.fields.number === 'NT-9213'); const k = d.check.cases.find(x => x.code === 'remit');
            trkCaseAct(d.id, k.key, 'callback', 'Called Nemo on file 718-555-0100'); const one = k.state; const again = trkCaseAct(d.id, k.key, 'callback', 'same person');
            signIn('u_controller'); trkCaseAct(d.id, k.key, 'callback', 'Second call, confirmed no change'); signIn('u_owner'); return [one, again === null, k.state] }""")
        c.ok(cb == ['open', True, 'verified'], f'the call-back needs a second person: {cb}')
        dup = await pg.evaluate("""() => { const r = trkIngest(%s, { source: { type: 'upload' }, links: { billId: 'tbd2' } }); const d = r.doc; return d.check.cases.map(x => x.code) }""" % json.dumps(inv('NT-7777', [('Grout', 10, 'bg', 50.0, None)], po='', tax=0.0, freight=0.0, terms='')))
        c.ok('dupNumber' in dup, f'a duplicate invoice number (another bill NT-7777 on file) fires: {dup}')
        dupa = await pg.evaluate("() => { const r = trkIngest(%s, { source: { type: 'upload' }, links: { poId: 'tpo1' } }); return r.doc.check.cases.map(x => x.code) }" % json.dumps(inv('NT-9002', CLEAN)))
        c.ok('dupAmount' in dupa, f'the same amount as another invoice within 45 days fires: {dupa}')
        same = await pg.evaluate("() => { const n = DB.docs.length; const r = trkIngest(%s, { source: { type: 'upload' }, links: { poId: 'tpo1' } }); return [r.dup === true, DB.docs.length === n] }" % json.dumps(inv('NT-9001', CLEAN)))
        c.ok(same == [True, True], f'the same document twice is a duplicate, not a second copy: {same}')
        # card receipts: no job purpose, a tip, a store far from the jobs; a clean one in Brooklyn has none of them
        rc = await pg.evaluate("""() => { const bad = trkIngest("ACE HARDWARE\\nStore: Ace Hardware #88, Route 4, Hackensack NJ 07601\\nReceipt # A-1\\n\\nWOOD SCREWS 2IN   12.00\\nENERGY DRINK 4PK   9.00\\nSUBTOTAL   21.00\\nSALES TAX   0.00\\nTIP   5.00\\nTOTAL   26.00", { source: { type: 'photo' }, links: { jobId: 'p121' } }).doc;
            const good = trkIngest("ACE HARDWARE\\nStore: Ace Hardware #12, Court St, Brooklyn NY 11201\\nReceipt # A-2\\n\\nWOOD SCREWS 2IN   12.00\\nSUBTOTAL   12.00\\nSALES TAX   1.07\\nTOTAL   13.07", { source: { type: 'photo' }, links: { jobId: 'p121' } }).doc;
            return [bad.kind, bad.check.cases.map(x => x.code), good.check.cases.map(x => x.code)] }""")
        c.ok(rc[0] == 'receipt' and {'noPurpose', 'tip', 'farStore'} <= set(rc[1]), f'card receipt cases fire: {rc[1]}')
        c.ok(not ({'noPurpose', 'tip', 'farStore'} & set(rc[2])), f'a clean receipt near the job raises none of them: {rc[2]}')

        # ---- 4. low confidence blocks until a person confirms; a held bill can't be approved ----------------
        await pg.evaluate("() => trkIngest(%s, { source: { type: 'upload' }, links: { billId: 'tb2' } })" % json.dumps(inv('NT-9300', CLEAN[:1]).replace('Freight   $100.00', 'Freight   $1?0.00')))
        lo = await pg.evaluate("() => { const b = DB.bills.find(x => x.id === 'tb2'), H = trkBillHold(b); return H && { low: H.low.map(x => x.field), cases: H.cases.map(x => x.code) } }")
        c.ok(lo and 'freight' in lo['low'], f'a figure read under the confidence threshold holds the bill: {lo}')
        st = await pg.evaluate("() => { const b = DB.bills.find(x => x.id === 'tb2'); billAction(b, 'approve', 'test'); return b.status }")
        c.ok(st == 'submitted', f'a bill with an unconfirmed figure is not approved: {st}')
        st = await pg.evaluate("() => { const b = DB.bills.find(x => x.id === 'tb2'), d = DB.docs.find(x => x.links.billId === 'tb2'); trkConfirm(d, 'freight', 100); return [trkBillHold(b), (billAction(b, 'approve', 'test'), b.status)] }")
        c.ok(st[0] is None and st[1] == 'approved', f'confirmed by a person, it approves: {st}')
        st = await pg.evaluate("() => { const b = DB.bills.find(x => x.id === 'tb1'); const H = trkBillHold(b); billAction(b, 'approve', 'test'); const s1 = b.status; const r2 = typeof pay3ShortPay === 'function' ? pay3ShortPay(b, 2713, 'test') : false; return [!!H, H && H.cases.map(x => x.code), s1, r2, b.status] }")
        c.ok(st[0] and 'price' in st[1] and st[2] == 'submitted' and st[3] is False and st[4] == 'submitted', f'a held bill cannot be approved by any path: {st}')
        t = await pg.evaluate("() => (document.querySelector('#toast') || {}).textContent || ''")
        c.ok('on hold' in t, f'the refusal says why: {t!r}')
        st = await pg.evaluate("() => { const b = DB.bills.find(x => x.id === 'tb1'), d = DB.docs.find(x => x.links.billId === 'tb1'); d.check.cases.filter(trkCaseOpen).forEach(k => trkCaseAct(d.id, k.key, 'accept', 'price agreed by phone, Chen, quote revision on file')); billAction(b, 'approve', 'test'); return [trkBillHold(b), b.status] }")
        c.ok(st[0] is None and st[1] == 'approved', f'after the cases are accepted with a reason, it approves: {st}')
        await pg.evaluate("() => mbCloseModal()")
        st = await pg.evaluate("() => { const b = DB.bills.find(x => x.number === 'AMP-311'); billAction(b, 'approve', 'COI renewal on file'); return b.status }")
        c.ok(st in ('approved', 'verified'), f'an existing bill with no documents still approves through the same gate: {st}')

        # ---- 5. filing from mail and photos ------------------------------------------------------------------
        await sign_in(pg, 'u_chen')
        r = await pg.evaluate("() => trkConnectMailbox()")
        m = await pg.evaluate("""() => { const D = DB.docs.filter(d => d.source.type === 'mail');
            return { kinds: D.map(d => d.kind), ack: (D.find(d => d.kind === 'ack') || {}).links, ackCases: ((D.find(d => d.kind === 'ack') || {}).check || {}).cases.map(x => x.code),
              ups: D.filter(d => d.fields.carrier === 'UPS').map(d => d.status), tn: D.filter(d => d.fields.number === 'TN-2291').length,
              rcpt: (D.find(d => d.kind === 'receipt') || {}).links, ads: D.filter(d => /toolpro/i.test(d.source.from || '')).length,
              read: DB.company.track.mailbox.read.length } }""")
        c.ok(m['ack'] and m['ack']['poId'] == 'po3' and {'qtyShort', 'price'} <= set(m['ackCases']), f'the acknowledgment that differs from its PO is filed on it with its differences: {m["ackCases"]}')
        c.ok(m['ups'] == ['proposed'], f'a tracking notice that names no order becomes a proposal, not a guess: {m["ups"]}')
        c.ok(m['tn'] == 1, f'the invoice sent twice is filed once: {m["tn"]}')
        c.ok(m['rcpt'] and m['rcpt']['txnId'] == 't14', f'the card receipt lands on its card line: {m["rcpt"]}')
        c.ok(m['ads'] == 0 and m['read'] == 9, f'marketing mail is ignored: {m}')
        pr = await pg.evaluate("() => trkRows('docsToConfirm').map(r => r.what)")
        c.ok(any('Build.com' in x or 'Tracking' in x for x in pr), f'the uncertain one waits on the coordinator: {pr}')
        # the driver's packing-slip photo (an invented delivery ticket, read as a photo)
        await sign_in(pg, 'u_alex')
        sl = await pg.evaluate("async () => { const f = trkDemoSlipPhoto(); const r = await trkAddFile(f, { source: 'photo' }); const d = r.doc || r.docs[0]; return [d.kind, d.source.type, d.links.poId] }")
        c.ok(sl == ['slip', 'photo', 'po4'], f'the driver\'s packing-slip photo is filed on PO-2026-048: {sl}')
        await sign_in(pg, 'u_chen')
        again = await pg.evaluate("() => trkFileMail()")
        c.ok(again['filed'] == 0 and again['dup'] == 0, f'a second run reads nothing twice: {again}')

        # ---- 6. a slip that threatens the schedule goes to the coordinator and the PM, in the Standard's format
        esc = await pg.evaluate("""() => { const s = DB.shipments.find(x => x.poId === 'po3'); const nyh = nyhRows({ everyone: true }).filter(r => r.kind === 'slip');
            return { risk: s.risk, eta: s.eta, need: trkNeedBy(DB.pos.find(p => p.id === 'po3')), routes: nyh.map(r => r.route).sort(), esc: s.esc && Object.keys(s.esc), day: s.esc && s.esc.day } }""")
        c.ok(esc['risk'] == 'late' and esc['eta'] > esc['need'], f'the freight ETA is after the need-by: {esc}')
        c.ok(esc['routes'] == ['coord', 'pm'], f'the slip goes to the coordinator and the PM: {esc["routes"]}')
        c.ok(all(k in (esc['esc'] or []) for k in ['what', 'impact', 'options', 'rec', 'deadline']) and esc['day'] == '2026-09-03', f'in the escalation format, the same day: {esc}')

        # ---- 7. follow-ups: sent when delegated, drafted when not; the guard ---------------------------------
        f = await pg.evaluate("() => DB.outbox.filter(o => o.kind === 'order-followup').map(o => o.status)")
        c.ok(f and all(s == 'sent' for s in f), f'with order follow-ups delegated, the assistant sends: {f}')
        lg = await pg.evaluate("() => (DB.pos.find(p => p.id === 'po4').followups || []).map(x => [x.type, x.status, !!x.outboxId])")
        c.ok(['confirm', 'sent', True] in lg, f'every send is logged on the PO: {lg}')
        await sign_in(pg, 'u_owner')
        off = await pg.evaluate("""() => { trkSetDelegated('u_chen', 'orderFollowups', false);
            DB.pos.push({ id: 'tpo5', number: 'PO-2026-994', projectId: 'p121', vendor: 'Nemo Tile', vendorId: 'v1', date: today(), expected: '2026-09-20', status: 'issued', lines: [{ id: 'tl9', item: 'Grout, warm gray', qty: 10, unit: 'bg', price: 30, received: 0 }], receipts: [], tax: 0, shipping: 0 });
            trkFollowSweep(); const o = DB.outbox.find(x => x.about && x.about.poId === 'tpo5');
            return [o && o.status, o && o.forName, DB.asst.u_chen.delegated.includes('orderFollowups'), DB.company.delegationLog.slice(-1)[0].by, mApprovals({ everyone: true }).some(i => i.kind === 'draft' && i.id === (o || {}).id)] }""")
        c.ok(off[0] == 'draft' and off[1] == 'Chen Biron' and off[2] is False, f'switched off by the owner, follow-ups are drafts for the coordinator: {off}')
        c.ok(off[3] == 'Owner', f'who switched it is logged: {off[3]}')
        g = await pg.evaluate("""() => [trkSendGuard('confirm', { subject: 'PO-2026-047', body: 'Your invoice will be paid next week, sorry for the delay.' }, 'u_chen'),
            trkSendGuard('confirm', { subject: 'PO-2026-047', body: 'The new date of the 30th works for us.' }, 'u_chen'),
            trkSendGuard('discount', { subject: 'x', body: 'Please confirm.' }, 'u_chen'),
            trkSendGuard('tracking', { subject: 'PO-2026-047 tracking', body: 'Could you reply with the tracking number?' }, 'u_chen')]""")
        c.ok(not g[0]['ok'] and 'money' in g[0]['why'], f'the guard refuses a template that discusses payment: {g[0]}')
        c.ok(not g[1]['ok'] and not g[2]['ok'] and g[3]['ok'], f'and one that accepts a date, and a type nobody delegated; a plain ask passes: {g}')
        # one delegation model: the owner can switch anyone's off, never on; only the person hands it over
        own = await pg.evaluate("() => [trkSetDelegated('u_chen', 'orderFollowups', true), DB.asst.u_chen.delegated.includes('orderFollowups')]")
        c.ok(own == [False, False], f'the owner cannot switch the coordinator\'s follow-ups on: {own}')
        sg = await pg.evaluate("""() => { const keep = standardAllows; let asked = 0; standardAllows = function () { asked++; return keep.apply(this, arguments); };
            try { trkSendGuard('tracking', { subject: 'PO-2026-047 tracking', body: 'Could you reply with the tracking number?' }, 'u_chen'); } finally { standardAllows = keep; } return asked; }""")
        c.ok(sg == 1, f'trkSendGuard asks standardAllows: {sg}')
        await sign_in(pg, 'u_chen')
        await pg.evaluate("() => trkSetDelegated('u_chen', 'orderFollowups', true)")
        await sign_in(pg, 'u_owner')
        one = await pg.evaluate("""async () => { view = 'standard'; render(); await new Promise(r => setTimeout(r, 300)); const std = !!document.querySelector('[data-dlgcard], #trk-deleg');
            view = 'rfq'; window.rfqTab = 'requests'; render(); await new Promise(r => setTimeout(r, 300)); const rfq = !!document.querySelector('#rfq-deleg');
            view = 'conn'; render(); await new Promise(r => setTimeout(r, 300)); const n = document.querySelectorAll('#trk-deleg').length;
            return [std, rfq, n, STD_SEND_TYPES.map(t => t.id).sort().join(','), DB.asst.u_chen.delegated.includes('orderFollowups')]; }""")
        c.ok(one == [False, False, 1, 'orderFollowups,rfqChases', True], f'one card, in Settings › Connections, on the one list of types: {one}')

        # ---- the Standard Watch rules this lane's records now measure ---------------------------------------
        wr = await pg.evaluate("""() => { const R = (id) => STANDARD_RULES.find(x => x.id === id), n = (id) => R(id).rows().map(r => r.key);
            DB.pos.push({ id: 'wpo1', number: 'PO-2026-981', projectId: 'p121', vendor: 'Mercer Lumber', vendorId: '', date: '2026-08-28', expected: iso(addDays(today(), 1)), status: 'issued', lines: [{ id: 'wl1', item: 'LVL 1-3/4 x 11-7/8', qty: 4, unit: 'ea', price: 120, received: 0 }], receipts: [], tax: 0, shipping: 0, followups: [] });
            const a = n('reconfirm48').includes('rc48:wpo1');
            DB.pos.find(p => p.id === 'wpo1').followups.push({ key: 'x', type: 'reconfirm', at: appNowIso(), status: 'sent' });
            const b = n('reconfirm48').includes('rc48:wpo1');
            const pm = trkPromiseAdd({ vendor: 'Mercer Lumber', poId: 'wpo1', kind: 'deliver', due: iso(addDays(today(), 1)), what: 'deliver the LVLs', at: iso(addDays(today(), -3)) + 'T10:00:00', source: { kind: 'call' } });
            DB.pos.find(p => p.id === 'wpo1').followups = [];
            const c = n('verbalWritten').includes('vw:' + pm.id);
            DB.pos.find(p => p.id === 'wpo1').followups.push({ key: 'y', type: 'confirm', at: appNowIso(), status: 'sent' });
            const d = n('verbalWritten').includes('vw:' + pm.id);
            const m = ['reconfirm48', 'deliveryCheck', 'verbalWritten'].map(id => R(id).measured !== false && typeof R(id).rows === 'function');
            DB.pos = DB.pos.filter(p => p.id !== 'wpo1'); DB.promises = DB.promises.filter(p => p.id !== pm.id);
            return { a, b, c, d, m }; }""")
        c.ok(wr['a'] and not wr['b'], f'reconfirmed 48 hours ahead is measured from the follow-ups log: {wr}')
        c.ok(wr['c'] and not wr['d'], f'a promise taken by phone is counted until it is confirmed in writing: {wr}')
        c.ok(wr['m'] == [True, True, True], f'the three rules are measured, not "not measured yet": {wr["m"]}')

        # ---- an invoice filed on a PO with no bill: billing's Needs Your Hand row, Enter the Bill -----------
        txt = inv('NT-9555', [('Carrara mosaic 2x2', 48, 'sf', 18.0, None), ('White subway tile 3x6', 192, 'sf', 8.0, None)], po='PO-2026-982').replace('@ $8.00', '@ $8.0?')
        eb = await pg.evaluate("""async (t) => { DB.pos.push({ id: 'epo1', number: 'PO-2026-982', projectId: 'p121', vendor: 'Nemo Tile', vendorId: 'v1', date: '2026-08-25', expected: '2026-09-02', status: 'received', lines: [{ id: 'el1', item: 'Carrara mosaic 2x2', qty: 48, unit: 'sf', price: 18, received: 48 }, { id: 'el2', item: 'White subway tile 3x6', qty: 192, unit: 'sf', price: 8, received: 192 }], receipts: [{ date: '2026-09-02', by: 'Angel', lines: [] }], tax: 8.875, shipping: 100 });
            const d = (trkIngest(t, { source: { type: 'upload', fileName: 'nt9555.txt' }, links: { poId: 'epo1' } }).doc);
            const row = nyhRowsAll().find(r => r.key === 'tk:enterbill:' + d.id);
            const b = row && row.run(); const again = nyhRowsAll().some(r => r.key === 'tk:enterbill:' + d.id);
            await new Promise(r => setTimeout(r, 150)); try { closeDrawer(); } catch (e) {}
            return { route: row && row.route, verb: row && row.verb, low: trkUnconfirmed(d), bill: b && [b.vendor, b.number, b.poId, b.lines.filter(l => l.poLineId).length, d.links.billId === b.id], unconf: b && b.unconfirmed, held: b && !!trkBillHold(b), onHold: trkRows('billsOnHold').some(r => r.key === 'hold:' + (b && b.id)), again }; }""", txt)
        c.ok(eb['route'] == 'billing' and eb['verb'] == 'Enter the Bill', f'a filed invoice on a PO with no bill is a Needs Your Hand row for billing: {eb}')
        c.ok(eb['bill'] and eb['bill'][:3] == ['Nemo Tile', 'NT-9555', 'epo1'] and eb['bill'][3] == 2 and eb['bill'][4], f'Enter the Bill drafts the bill from the read invoice, lines matched to the PO and linked: {eb}')
        c.ok(eb['low'] and eb['unconf'] == eb['low'] and eb['held'] and eb['onHold'] and not eb['again'], f'figures read with low confidence stay unconfirmed and hold the bill: {eb}')

        # ---- 8. the promise ledger: kept and broken; the vendor's record; the brain's lesson --------------
        await pg.evaluate("""() => { trkPromiseAdd({ vendor: 'Nemo Tile', poId: 'tpo3', kind: 'ship', due: '2026-09-05', what: 'ship the glass mosaic by Sep 5', loggedBy: 'Chen', source: { kind: 'text' } }); trkPromiseAdd({ vendor: 'Nemo Tile', poId: 'tpo1', kind: 'deliver', due: '2026-09-05', what: 'deliver the tile by Sep 5', loggedBy: 'Chen', source: { kind: 'call' } }); save(); }""")
        d = await pg.evaluate("() => { const r = appSetDay('2026-09-09'); return r.ran.includes('trkDay') }")
        c.ok(d, 'the day hook runs the tracker')
        pl = await pg.evaluate("() => DB.promises.map(p => [p.vendor, p.kind, p.due, p.status])")
        c.ok(['Nemo Tile', 'deliver', '2026-09-05', 'kept'] in pl, f'a delivery promise received in time is kept: {pl}')
        c.ok(any(x[0] == 'Mercer Lumber' and x[1] == 'callback' and x[3] == 'broken' for x in pl), f'a call-back that never came is broken: {pl}')
        c.ok(any(x[1] == 'ship' and x[3] == 'open' for x in pl), f'a promise not yet due stays open: {pl}')
        vs = await pg.evaluate("() => [trkVendorStat('Mercer Lumber'), eqRows('vendorontime').find(r => r.vendor === 'Mercer Lumber')]")
        c.ok(vs[0]['broken'] >= 1 and vs[1] and vs[1]['broken'] == vs[0]['broken'], f'the vendor\'s on-time record is queryable: {vs}')
        bf = await pg.evaluate("() => (DB.pos.find(p => p.id === 'tpo3').followups || []).filter(f => f.type === 'broken').map(f => f.status)")
        c.ok(bf == ['sent'], f'a broken promise is chased on its own when delegated: {bf}')
        ln = await pg.evaluate("() => { lnLoop('day'); const P = lnInit().props; return [!!P.trkBroken, (P.trkBroken || {}).title || '', !!P.trkAckDiff] }")
        c.ok(ln[0] and 'Pad' in ln[1] and ln[2], f'the brain proposes the lessons: {ln}')

        # ---- 9. counts: one per label, count = rows; queryable, searchable ----------------------------------
        cnt = await pg.evaluate("() => TRK_PRED.map(([k, label]) => [k, label, PRED[k].count(), PRED[k].rows().length, trkRows(k).length])")
        for k, label, n, rows, rows2 in cnt:
            c.ok(n == rows == rows2, f'PRED.{k} "{label}": count {n} = rows {rows}')
        c.ok(len({x[1] for x in cnt}) == len(cnt), 'one label per count')
        await pg.evaluate("() => { setCurrent('p121'); poOpen = null; view = 'po'; render(); }"); await pg.wait_for_timeout(300)
        shown = await pg.evaluate("() => [...document.querySelectorAll('#trk-panel [data-trkpanel] b')].map(b => +b.textContent)")
        c.ok(shown == [x[2] for x in cnt], f'the panel shows the same numbers: {shown} vs {[x[2] for x in cnt]}')
        await pg.locator('#trk-panel [data-trkpanel="billsOnHold"]').click(); await pg.wait_for_timeout(300)
        rows = await pg.evaluate("() => document.querySelectorAll('#mbm .trk-row').length")
        c.ok(rows == max(1, cnt[-1][2]) or (cnt[-1][2] == 0 and rows == 0), f'a count opens its rows: {rows} for {cnt[-1][2]}')
        await pg.evaluate("() => mbCloseModal()")
        q = await pg.evaluate("() => [eqRows('orderdocs').length, DB.docs.filter(d => !['ignored','dup'].includes(d.status) && !d.splitInto).length, palIndex().filter(i => i.k === 'Document').length, palIndex().filter(i => i.k === 'Promise').length]")
        c.ok(q[0] == q[1] == q[2] and q[3] > 0, f'documents are queryable (EQ_TABLES) and searchable (palette): {q}')

        # ---- 10. Ask ----------------------------------------------------------------------------------------
        await pg.evaluate("() => appSetDay('2026-09-03')")
        asks = {
            "where's the tile order for 121 State": r'PO-2026-041|Nemo Tile',
            'what did Mercer Lumber promise': r'call you back|hold this price',
            'which bills are on hold and why': r'on hold|No bill is on hold',
            'show the invoice for PO-2026-047': r'TN-2291',
            'receipts missing this week': r'card line',
        }
        for qq, rx in asks.items():
            a = await pg.evaluate("q => { const a = paAsk(q); return [a.headline || '', a.reader || ''] }", qq)
            c.ok(re.search(rx, a[0]) and a[1] == 'track', f'Ask "{qq}": {a}')

        # ---- 11. split, retake, offline queue ------------------------------------------------------------------
        sp = await pg.evaluate("() => { const t = %s + '\\f' + %s; const r = trkIngest(t, { source: { type: 'upload', fileName: 'two.pdf' }, links: {} }); return [r.split, r.docs.map(d => d.fields.number)] }" % (json.dumps(inv('NT-9401', CLEAN)), json.dumps(inv('NT-9402', CLEAN[:1]))))
        c.ok(sp[0] == 2 and sp[1] == ['NT-9401', 'NT-9402'], f'a multi-invoice PDF is split: {sp}')
        bl = await pg.evaluate("""async () => { const cv = document.createElement('canvas'); cv.width = 600; cv.height = 800; const g = cv.getContext('2d'); g.fillStyle = '#888'; g.fillRect(0, 0, 600, 800);
            const blurry = await trkAddFile({ dataUrl: cv.toDataURL('image/png'), name: 'slip.png', mime: 'image/png' }, { source: 'photo' });
            g.fillStyle = '#fff'; g.fillRect(0, 0, 600, 800); g.fillStyle = '#000'; g.font = '22px sans-serif'; for (let i = 0; i < 30; i++) g.fillText('PACKING SLIP 8 OF 14 BOXES DT-5521', 10, 26 * (i + 1));
            const sharp = await trkAddFile({ dataUrl: cv.toDataURL('image/png'), name: 'slip2.png', mime: 'image/png' }, { source: 'photo', poId: 'po4' });
            return [!!blurry.retake, blurry.why, !!sharp.retake, (sharp.doc || {}).status] }""")
        c.ok(bl[0] and 'retake' not in str(bl[1]).lower() and bl[2] is False and bl[3] == 'unread', f'a blurry photo gets a retake request; a sharp one is kept for a person to read: {bl}')

        # ---- 12. reload: everything persisted ----------------------------------------------------------------
        before = await pg.evaluate("async () => { await saveNow(); return [DB.docs.length, DB.promises.length, DB.shipments.length, DB.asst.u_chen.delegated.slice(), DB.docs[0].hash] }")
        await pg.reload(); await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000); await pg.wait_for_timeout(500)
        after = await pg.evaluate("() => [DB.docs.length, DB.promises.length, DB.shipments.length, DB.asst.u_chen.delegated.slice(), DB.docs[0].hash, trkVerify(DB.docs[0])]")
        c.ok(after[:5] == before and after[5], f'reload keeps documents, promises, shipments and delegation: {before} -> {after}')
        c.ok(not errs, f'no page errors: {errs[:3]}')
        await b.close()

        # ---- 13. the phone at 390px: the driver's capture, offline queue, no sideways scroll ------------------
        b2, ph, errs2 = await open_app(p, phone=True)
        await sign_in(ph, 'u_alex')
        await go(ph, 'route'); await ph.wait_for_timeout(300)
        c.ok(await ph.locator('#trk-capture').is_visible(), 'the driver sees Packing Slip or Receipt on the route')
        await ph.context.set_offline(True)
        svg = (await ph.evaluate("() => decodeURIComponent(trkDemoSlipPhoto().dataUrl.split(',')[1])")).encode('utf-8')
        await ph.locator('#trk-capture #trk-cap').set_input_files({'name': 'slip.svg', 'mimeType': 'image/svg+xml', 'buffer': svg})
        await ph.wait_for_timeout(800)
        qd = await ph.evaluate("() => DB.docs.filter(d => d.status === 'queued').length")
        c.ok(qd == 1, f'a capture with no signal is queued on the phone: {qd}')
        await ph.context.set_offline(False); await ph.wait_for_timeout(800)
        qd2 = await ph.evaluate("() => [DB.docs.filter(d => d.status === 'queued').length, (DB.docs.slice(-1)[0] || {}).kind, (DB.docs.slice(-1)[0] || {}).links.poId, trkVerify(DB.docs.slice(-1)[0])]")
        c.ok(qd2 == [0, 'slip', 'po4', True], f'back online it is read and filed, its seal intact: {qd2}')
        sw = await ph.evaluate("() => document.documentElement.scrollWidth")
        c.ok(sw <= 390, f'route at 390px: no sideways scroll ({sw})')
        await sign_in(ph, 'u_chen')
        await ph.evaluate("() => { setCurrent('p121'); flowGo.po(DB.pos.find(p => p.id === 'po3'))(); }"); await ph.wait_for_timeout(400)
        await ph.evaluate("() => trkLogPromiseDialog({ poId: 'po3', vendor: 'Tino' })"); await ph.wait_for_timeout(300)
        sw2 = await ph.evaluate("() => [document.documentElement.scrollWidth, !!document.querySelector('#mbm')]")
        c.ok(sw2[0] <= 390 and sw2[1], f'Log a Promise at 390px: no sideways scroll ({sw2})')
        await ph.locator('#mbm [data-f="what"]').fill('Tino on the phone: will deliver the 9th')
        await ph.locator('#mbm [data-f="kind"]').select_option('deliver')
        await ph.locator('#mbm #mbm-ok').click(); await ph.wait_for_timeout(300)
        lp = await ph.evaluate("() => DB.promises.filter(p => p.source.kind === 'call').map(p => [p.vendor, p.kind, p.poId])")
        c.ok(['Tino', 'deliver', 'po3'] in lp, f'a promise from a call is logged from the phone: {lp}')
        await sign_in(ph, 'u_owner')
        await go(ph, 'conn'); await ph.wait_for_timeout(400)
        dg = await ph.evaluate("() => [!!document.querySelector('#trk-deleg'), document.documentElement.scrollWidth, document.querySelectorAll('#trk-deleg [data-trkdeleg]').length]")
        c.ok(dg[0] and dg[1] <= 390 and dg[2] >= 2, f'What My Assistant May Send for Me fits the phone: {dg}')
        c.ok(not errs2, f'no page errors on the phone: {errs2[:3]}')
        await b2.close()
    return c.done()

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
