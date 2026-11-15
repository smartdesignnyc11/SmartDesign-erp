"""Every money path checks what exists first (billing review 11-15, the five S1 findings). Invented demo data only.
Driven as billing (u_billing) through the screens, on the desktop and the phone.

1  A billed-ahead reason covers what it was given for. Billing gave a reason for Demolition at 10% this period on
   INV-2026-039, cancelled the send sheet, raised Demolition to 40% and it went out with no new ask ($8,400 more ahead
   than the reason covered: 30 points of the $28,000 line). The reason records each line, how far it is billed and its
   dollars; billing a line further, or a new line going ahead, asks again; the earlier reason stays in the history.
2  "Credit on account" pays only with credit the client has. The Jessop family holds $0 on account, yet INV-2026-D140-R
   ($24,000) went to paid. The method is not offered with no credit, and the write refuses it (a stale sheet, the
   editor drawer, the credit write itself).
3  One reading of a client's credit (clientCredit). A credit on the Kleins' account proposed for refund was also applied
   to an open invoice: approved, the client would have been paid twice. Available = on account less what is applied
   less refunds proposed; every use reads it.
4  The signed contract billed by progress application (EST-2026-014, three applications) offers its next application,
   never a blue Convert to Invoice for the whole $485,000; the write refuses a whole-estimate invoice too.
5  A revision keeps the original's accounting: for every kind of sent invoice in the demo (progress application,
   retainer, milestone drawing on a retainer) the revision posts to the same accounts (INV-2026-D140-R-R1 posted its
   $24,000 to design revenue, 4000, instead of customer deposits, 2400).
"""
import asyncio, sys
from harness import *

SLEEP = "ms => new Promise(r => setTimeout(r, ms))"


async def js(pg, body, arg=None):
    return await pg.evaluate("async (arg) => { const sleep = " + SLEEP + "; " + body + " }", arg)


INV = """
  const C = DB.clients.find(c => (c.invoices || []).some(i => i.id === window.__bxInv));
  const D = C && C.invoices.find(i => i.id === window.__bxInv);
"""


async def open_039(pg):
    """Billing's blue Draft for 121 State makes the next application (INV-2026-039) and opens it."""
    await js(pg, "try { mbCloseModal(); } catch (e) {} view = 'billing'; billTab = 'billable'; docOpen = null; render(); await sleep(400);")
    return await js(pg, """
      const row = (x) => { let e = x; for (let k = 0; k < 6 && e; k++, e = e.parentElement) { if (e.querySelectorAll('button[data-blact]').length > 1) return null; if (/12,651/.test(e.textContent)) return e; } return null; };
      const b = [...document.querySelectorAll('button[data-blact]')].find(x => x.offsetParent && /^Draft/.test(x.textContent.trim()) && row(x));
      if (b) { b.click(); await sleep(700); }
      return docOpen && docOpen.id;
    """)


async def set_pct(pg, item, v, phone):
    """Type This Period % on the line named item, as billing does (the phone's editor is driven the same way when its
    field is on screen; otherwise the value is written as the field writes it)."""
    lid = await js(pg, INV + "return (D.lines.find(l => l.item === arg) || {}).id;", item)
    loc = pg.locator(f'tr[data-line="{lid}"] [data-f="pct"]').first
    if await loc.count() and await loc.is_visible():
        await loc.fill(str(v)); await loc.press('Tab'); await pg.wait_for_timeout(300)
    else:
        await js(pg, INV + "D.lines.find(l => l.id === arg[0]).pct = arg[1]; save(); render(); await sleep(300);", [lid, v])


async def press_send(pg):
    await js(pg, "try { mbCloseModal(); } catch (e) {} await sleep(150);")
    btn = pg.locator('[data-docact="sendclient"]:visible').first
    if await btn.count():
        await btn.click()
    else:
        await js(pg, INV + "docAction(C, D, 'sendclient');")
    await pg.wait_for_timeout(600)
    return await js(pg, "const m = document.getElementById('mbm'); return m ? { h: m.querySelector('h3').textContent, t: m.textContent, ok: (m.querySelector('#mbm-ok') || {}).textContent || '' } : null;")


async def t1_reason_covers(p, c, phone):
    tag = 'phone' if phone else 'desktop'
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, 'u_billing')
    o = await open_039(pg)
    c.ok(bool(o), f"[{tag}] 1: Billing's Draft opens the 121 State application ({o})")
    if not o:
        await b.close(); return
    await js(pg, "window.__bxInv = arg;", o)
    # the reviewer's percentages: 10 on Demolition, nothing ahead on the others
    for i, l in enumerate(await js(pg, INV + "return D.lines.map(l => l.item);")):
        await set_pct(pg, l, 10 if l.startswith('Demolition') else 0, phone)
    m = await press_send(pg)
    c.ok(m and 'Billed Ahead of the Work' in m['h'] and 'Demolition' in m['t'] and '$2,800' in m['t'],
         f"[{tag}] 1: Send to Client asks for a reason, naming Demolition and its $2,800 this period ({m and m['t'][:220]})")
    await pg.locator('#mbm [data-f="why"]').fill('the contract bills disposal on mobilisation')
    await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(700)
    nxt = await js(pg, "const m = document.getElementById('mbm'); return m ? m.querySelector('h3').textContent : 'none';")
    c.ok('Send to Client' in nxt, f"[{tag}] 1: the reason resumes the send ({nxt})")
    await js(pg, "try { mbCloseModal(); } catch (e) {} await sleep(200);")   # the person cancels the send sheet
    s = await js(pg, INV + "return { st: D.status, w: D.aheadWhy && D.aheadWhy.covers };")
    c.ok(s['st'] == 'draft' and s['w'] and any(x['item'].startswith('Demolition') and abs(x['amount'] - 2800) < 0.01 for x in s['w']),
         f"[{tag}] 1: the reason records what it covered, Demolition and $2,800 ({s})")
    # raised to 40%: $8,400 more than the reason covered
    await set_pct(pg, 'Demolition & disposal', 40, phone)
    m = await press_send(pg)
    c.ok(m and 'Billed Ahead of the Work' in m['h'] and '$11,200' in m['t'],
         f"[{tag}] 1: raised to 40%, Send to Client asks again, for $11,200 this period ({m and m['t'][:260]})")
    c.ok(m and 'earlier reason' in m['t'], f"[{tag}] 1: the sheet says an earlier reason covered less")
    c.ok(m and m['ok'].lower() == 'send with the reason', f"[{tag}] 1: its button matches Send to Client ({m and m['ok']})")
    st = await js(pg, INV + "return D.status;")
    c.ok(st == 'draft', f"[{tag}] 1: and it stays a draft until the new reason ({st})")
    await pg.locator('#mbm [data-f="why"]').fill('the owner agreed the dumpsters for the whole job bill now')
    await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(700)
    to = pg.locator('#mbm [data-f="to"]')
    if await to.count():
        if not await to.input_value():
            await to.fill('client@example.com')
        await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(900)
    s = await js(pg, INV + """
      const A = (DB.audit || []).filter(a => a.refId === D.id && a.action === 'billed-ahead');
      return { st: D.status, why: D.aheadWhy && D.aheadWhy.why, log: (D.aheadWhyLog || []).map(w => w.why), audit: A.length };""")
    c.ok(s['st'] == 'sent' and 'dumpsters' in (s['why'] or ''), f"[{tag}] 1: with the new reason it goes out ({s})")
    c.ok(len(s['log']) == 1 and 'mobilisation' in s['log'][0] and s['audit'] >= 2, f"[{tag}] 1: the first reason stays in the history and the audit ({s})")
    c.ok(not errs, f'[{tag}] 1: page errors: {errs[:2]}')
    await b.close()


async def t1_new_line(p, c):
    """A reason given for one line does not cover another line going ahead; Mark as Sent's button says Mark as Sent."""
    b, pg, errs = await open_app(p)
    await sign_in(pg, 'u_billing')
    o = await open_039(pg)
    await js(pg, "window.__bxInv = arg;", o)
    r = await js(pg, INV + """
      D.lines.forEach(l => l.pct = /^Demolition/.test(l.item) ? 10 : 0); save();
      const F = pbFurther(C, D);
      D.aheadWhy = { why: 'demolition only', by: 'test', at: appNowIso(), covers: F.map(x => ({ sovId: x.l.sovId, item: x.l.item, to: x.to, amount: x.amount })) };
      const covered = pbUncovered(C, D).length;
      // every other line that has a measure, billed well past it
      D.lines.forEach(l => { if (!/^Demolition/.test(l.item)) l.pct = 60; }); save();
      const more = pbUncovered(C, D).map(x => x.l.item);
      await docAction(C, D, 'send'); await sleep(300);
      const m = document.getElementById('mbm');
      return { covered, more, sheet: m ? m.querySelector('h3').textContent : '', ok: m ? m.querySelector('#mbm-ok').textContent : '', st: D.status };""")
    c.ok(r['covered'] == 0, f"1: the reason covers the line and percentage it was given for ({r})")
    c.ok(r['more'] and not any(x.startswith('Demolition') for x in r['more']), f"1: other lines going ahead are not covered by it ({r['more']})")
    c.ok('Billed Ahead' in r['sheet'] and r['ok'].lower() == 'mark as sent with the reason' and r['st'] == 'draft',
         f"1: Mark as Sent asks again and its button says Mark as Sent With the Reason ({r})")
    c.ok(not errs, f'1: page errors: {errs[:2]}')
    await b.close()


async def t2_phantom_credit(p, c, phone):
    tag = 'phone' if phone else 'desktop'
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, 'u_billing')
    r = await js(pg, """
      const c = DB.clients.find(c => /Jessop/.test(c.name)), d = c.invoices.find(i => i.number === 'INV-2026-D140-R');
      window.__j = [c.id, d.id];
      dvOpen('invoice', d.id, c.id); await sleep(400);
      const b = [...document.querySelectorAll('#dv button')].find(x => /Record Payment/.test(x.textContent));
      if (!b) { const m = document.querySelector('#dv [data-dvact="more"]'); m && m.click(); await sleep(200); }
      const bb = [...document.querySelectorAll('#dv button')].find(x => /Record Payment/.test(x.textContent));
      bb && bb.click(); await sleep(500);
      const sel = document.querySelector('#mbm #py-method');
      return { credit: clientCredit(c), opened: !!sel, opts: sel ? [...sel.options].map(o => o.textContent) : [] };""")
    c.ok(r['credit']['onAccount'] == 0 and r['opened'], f"[{tag}] 2: Jessop holds no credit; Record Payment opens ({r['credit']})")
    c.ok('Credit on account' not in r['opts'], f"[{tag}] 2: the sheet does not offer Credit on account ({r['opts']})")
    # a stale sheet (or a second tab) that still holds the method: the write refuses it
    r = await js(pg, """
      const c = DB.clients.find(x => x.id === window.__j[0]), d = c.invoices.find(i => i.id === window.__j[1]), n0 = c.payments.length;
      const m = document.getElementById('mbm'), sel = m.querySelector('#py-method');
      const o = document.createElement('option'); o.textContent = 'Credit on account'; sel.appendChild(o); sel.value = 'Credit on account'; sel.dispatchEvent(new Event('change', { bubbles: true }));
      const t = m.querySelector('#py-txn'); if (t) { t.value = ''; t.dispatchEvent(new Event('change', { bubbles: true })); }
      m.querySelector('#py-amt').value = '24000';
      m.querySelectorAll('[data-pyalloc]').forEach(i => i.value = i.dataset.pyalloc === d.id ? '24000' : '0');
      m.querySelector('#mbm-ok').click(); await sleep(500);
      const toast = (document.getElementById('toast') || {}).textContent || '';
      try { mbCloseModal(); } catch (e) {}
      const R = clientCreditApply(c, d, 24000);
      return { st: d.status, paid: invoicePaid(c, d), made: c.payments.length - n0, toast, write: R, coll: clientFin(c).open.some(o => o.x.id === d.id) };""")
    c.ok(r['st'] == 'sent' and r['paid'] == 0 and r['made'] == 0, f"[{tag}] 2: Record by credit with none on account writes nothing; INV-2026-D140-R stays sent, $0 paid ({r})")
    c.ok('no credit on account' in r['toast'], f"[{tag}] 2: and says why ({r['toast']})")
    c.ok(not r['write']['ok'] and r['coll'], f"[{tag}] 2: the credit write refuses it too, and it stays in Collections ({r['write']})")
    c.ok(not errs, f'[{tag}] 2: page errors: {errs[:2]}')
    await b.close()


async def t3_one_credit(p, c, phone):
    tag = 'phone' if phone else 'desktop'
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, 'u_billing')
    # the fixture: a credit on the Kleins' paid INV-2026-035 goes on their account, as a credit on a paid invoice does
    f = await js(pg, """
      const c = DB.clients.find(c => c.id === 'cl121'), d = c.invoices.find(i => i.number === 'INV-2026-035');
      const R = dvCreditCreate(c, d, [{ lineId: d.lines[0].id, amount: 1000 }], 'tile allowance credited');
      return { ok: R.ok, why: R.why || '', C: clientCredit(c) };""")
    c.ok(f['ok'] and f['C']['available'] > 500, f"[{tag}] 3: the fixture: the Kleins hold credit on account ({f})")
    held = f['C']['available']
    # Refund: its amount is what the account can give; propose all of it from the sheet
    r = await js(pg, """
      const c = DB.clients.find(c => c.id === 'cl121'), d = c.invoices.find(i => i.number === 'INV-2026-031');
      dvOpen('invoice', d.id, c.id); await sleep(300);
      dvAct('refund'); await sleep(400);
      const v = +((document.querySelector('#mbm [data-f=amount]') || {}).value || 0);
      return { v };""")
    c.ok(abs(r['v'] - held) < 0.01, f"[{tag}] 3: the Refund sheet holds the ${held:,.2f} available ({r})")
    await pg.locator('#mbm [data-f="why"]').fill('the client asked for the tile credit back')
    await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(500)
    r = await js(pg, """
      const c = DB.clients.find(c => c.id === 'cl121'), d = c.invoices.find(i => i.number === 'INV-2026-038');
      const f = dvRefunds(c).filter(x => x.status === 'proposed');
      dvClose(); clientOpen = c.id; docOpen = null;
      dvOpen('invoice', d.id, c.id); await sleep(300);
      const bar = [...document.querySelectorAll('#dv button')].map(b => b.textContent.trim());
      const n0 = c.payments.length, paid0 = invoicePaid(c, d);
      applyCredits(c, d); await sleep(200);
      const toast = (document.getElementById('toast') || {}).textContent || '';
      // Record Payment on INV-2026-038 does not offer Credit on account
      dvClose(); clientOpen = c.id; paymentAllocate(c, d.id); await sleep(300);
      const sel = document.querySelector('#mbm #py-method'), opts = sel ? [...sel.options].map(o => o.textContent) : [];
      try { mbCloseModal(); } catch (e) {}
      const again = dvRefundPropose(c, c.invoices.find(i => i.number === 'INV-2026-031'), f[0] && f[0].paymentId, 1, 'twice', false);
      return { proposed: f.map(x => x.amount), C: clientCredit(c), applied: r2(invoicePaid(c, d) - paid0), made: c.payments.length - n0, toast, opts, bar, again: again.ok };""")
    c.ok(r['proposed'] and abs(r['proposed'][0] - held) < 0.01, f"[{tag}] 3: the refund is proposed for the whole credit ({r['proposed']})")
    c.ok(r['C']['available'] == 0 and abs(r['C']['reserved'] - held) < 0.01, f"[{tag}] 3: clientCredit reads it reserved, none available ({r['C']})")
    c.ok(r['applied'] == 0 and r['made'] == 0 and 'refund' in r['toast'], f"[{tag}] 3: applying that credit to INV-2026-038 is refused and says why ({r['toast']})")
    c.ok('Credit on account' not in r['opts'], f"[{tag}] 3: Record Payment does not offer it ({r['opts']})")
    c.ok(not any('Apply credit' in x for x in r['bar']), f"[{tag}] 3: no Apply Credit button on the invoice ({r['bar']})")
    c.ok(not r['again'], f"[{tag}] 3: a second refund of the same credit is refused")
    # the other way round: applied first, then the refund can only take what is left
    r = await js(pg, """
      const c = DB.clients.find(c => c.id === 'cl121'), d = c.invoices.find(i => i.number === 'INV-2026-038');
      const f = dvRefunds(c).find(x => x.status === 'proposed');
      Object.assign(f, { status: 'declined', declineWhy: 'test' });
      const R = clientCreditApply(c, d, 300), C = clientCredit(c);
      const L = dvRefundLimit(c, c.invoices.find(i => i.number === 'INV-2026-031'), dvRefundable(c, c.invoices.find(i => i.number === 'INV-2026-031')).find(x => x.banked), false);
      return { R, C, max: L.max };""")
    c.ok(r['R']['ok'] and abs(r['C']['available'] - (held - 300)) < 0.01 and abs(r['max'] - (held - 300)) < 0.01,
         f"[{tag}] 3: with $300 applied, a refund can take only the rest ({r})")
    c.ok(not errs, f'[{tag}] 3: page errors: {errs[:2]}')
    await b.close()


async def t4_contract(p, c, phone):
    tag = 'phone' if phone else 'desktop'
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, 'u_billing')
    r = await js(pg, """
      const c = DB.clients.find(c => c.id === 'cl121'), e = c.estimates.find(x => x.number === 'EST-2026-014');
      dvOpen('estimate', e.id, c.id); await sleep(400);
      const vis = [...document.querySelectorAll('#dv .dv-bar button')].filter(b => b.offsetParent).map(b => (b.className.includes('primary') ? '*' : '') + b.textContent.trim());
      const m = document.querySelector('#dv [data-dvact="more"]'); m && m.click(); await sleep(200);
      const all = [...document.querySelectorAll('#dv button')].map(b => (b.className.includes('primary') ? '*' : '') + b.textContent.trim());
      dvClose();
      const n0 = c.invoices.length;
      await docAction(c, e, 'invoice'); await sleep(300);
      const sheet = !!document.querySelector('#mbm [data-ife]');
      const toast = (document.getElementById('toast') || {}).textContent || '';
      return { vis, all, made: c.invoices.length - n0, sheet, toast };""")
    c.ok(not any('Convert to Invoice' in x for x in r['all']), f"[{tag}] 4: EST-2026-014, the billed contract, offers no Convert to Invoice ({r['all']})")
    c.ok(any(x.startswith('*') and ('Progress Invoice' in x or 'Open INV' in x) for x in r['vis']), f"[{tag}] 4: its blue is the next progress application ({r['vis']})")
    c.ok(r['made'] == 0 and not r['sheet'] and 'progress application' in r['toast'], f"[{tag}] 4: the write refuses a whole-contract invoice and says why ({r})")
    # the class still works: an approved estimate that is not yet a contract converts
    c.ok(not errs, f'[{tag}] 4: page errors: {errs[:2]}')
    await b.close()


async def t5_revise(p, c, phone):
    tag = 'phone' if phone else 'desktop'
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, 'u_billing')
    # the reviewer's case through the screens: the viewer's Edit on INV-2026-D140-R, a reason, the revision sent
    r = await js(pg, """
      const c = DB.clients.find(c => /Jessop/.test(c.name)), d = c.invoices.find(i => i.number === 'INV-2026-D140-R');
      dvOpen('invoice', d.id, c.id); await sleep(300); dvAct('edit'); await sleep(300);
      const w = document.querySelector('#mbm [data-f="why"]'); w.value = 'the address goes on the description'; w.dispatchEvent(new Event('input', { bubbles: true }));
      document.querySelector('#mbm #mbm-ok').click(); await sleep(600);
      const n = c.invoices.find(i => i.revisionOf === d.number);
      try { mbCloseModal(); } catch (e) {}
      if (n) { await docAction(c, n, 'send'); await sleep(400); try { mbCloseModal(); } catch (e) {} }
      const sum = (L) => { const o = {}; (L || []).forEach(l => o[l.acct] = r2((o[l.acct] || 0) + (+l.dr || 0) - (+l.cr || 0))); Object.keys(o).forEach(k => Math.abs(o[k]) < 0.005 && delete o[k]); return o; };
      return { n: n && n.number, st: n && n.status, ret: n && n.retainerOf, gl: n ? sum(glInvoiceLines(c, n)) : null, was: sum(glInvoiceLines(c, d)) };""")
    c.ok(r['n'] and r['ret'] == 'esD140', f"[{tag}] 5: the revision {r['n']} keeps its retainer link ({r['ret']})")
    c.ok(r['gl'] and r['gl'].get('2400') == -24000 and '4000' not in r['gl'], f"[{tag}] 5: it posts $24,000 to customer deposits (2400), not design revenue ({r['gl']}, {r['st']})")
    if not phone:
        # every kind of sent invoice in the demo: the revision posts to the same accounts, for the same amounts
        r = await js(pg, """
          const sum = (L) => { const o = {}; (L || []).forEach(l => o[l.acct] = r2((o[l.acct] || 0) + (+l.dr || 0) - (+l.cr || 0))); Object.keys(o).forEach(k => Math.abs(o[k]) < 0.005 && delete o[k]); return o; };
          const out = [];
          for (const c of DB.clients) for (const d of (c.invoices || []).slice()) {
            if (['void', 'draft'].includes(d.status) || d.creditMemo || d.revisedBy || d.revisionOf) continue;
            const a = sum(glInvoiceLines(c, d)), n = lkRevise(c, d), bb = sum(glInvoiceLinesLive(c, n));
            const keys = ['retainerOf', 'fromDoc', 'milestone', 'retainerApplied', 'billFrom', 'depositOf', 'entityId', 'projectId', 'taxRate', 'retainagePct', 'mode', 'template'].filter(k => JSON.stringify(d[k]) !== JSON.stringify(n[k]));
            const lines = (d.lines || []).every((l, i) => ['sovId', 'fromLine', 'retainerLine', 'code', 'cat', 'taxable'].every(k => JSON.stringify(l[k]) === JSON.stringify((n.lines[i] || {})[k])));
            out.push({ num: d.number, same: JSON.stringify(a) === JSON.stringify(bb), a, b: bb, keys, lines });
          }
          return out;""")
        kinds = [x['num'] for x in r]
        c.ok(len(r) >= 5, f"5: every sent invoice kind in the demo is revised ({kinds})")
        for x in r:
            c.ok(x['same'] and not x['keys'] and x['lines'], f"5: {x['num']}: the revision posts as the original and keeps its links ({x})")
    c.ok(not errs, f'[{tag}] 5: page errors: {errs[:2]}')
    await b.close()


async def t_s2(p, c, phone):
    """The S2 and S3 steps a person gets wrong (6 to 12, 14)."""
    tag = 'phone' if phone else 'desktop'
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, 'u_billing')
    # 7. one leak figure: Today's headline is Billing's Ready to Bill, the held Windows line counted once
    r = await js(pg, """
      view = 'home'; render(); await sleep(300);
      const t = document.body.innerText, m = t.match(/\$([\d,]+) is leaking/);
      return { leak: m ? +m[1].replace(/,/g, '') : null, rtb: Math.round(readyToBill().amount) };""")
    c.ok(r['leak'] is None or abs(r['leak'] - r['rtb']) <= 1, f"[{tag}] 7: Today's leak headline is Billing's ${r['rtb']:,} ({r})")
    # 6. Bill It on a second change order opens the open draft application, never a second one
    r = await js(pg, """
      const c = DB.clients.find(c => c.id === 'cl121'), est = c.estimates.find(e => e.number === 'EST-2026-014');
      const n0 = c.invoices.filter(i => i.mode === 'sov' && i.status === 'draft').length;
      await docAction(c, est, 'progress'); await sleep(200);
      const n1 = c.invoices.filter(i => i.mode === 'sov' && i.status === 'draft').length;
      const co = c.changeOrders.find(x => x.status === 'approved');
      if (co) { dvOpen('co', co.id, c.id); await sleep(200); dvAct('billco'); await sleep(300); }
      const n2 = c.invoices.filter(i => i.mode === 'sov' && i.status === 'draft').length;
      return { n0, n1, n2, co: co && co.number, open: docOpen && docOpen.id, draft: (c.invoices.find(i => i.mode === 'sov' && i.status === 'draft') || {}).id };""")
    c.ok(r['n1'] == max(1, r['n0']) and r['n2'] == r['n1'] and r['open'] == r['draft'], f"[{tag}] 6: one open draft application on 121 State; Bill It opens it ({r})")
    # 8. the banner names the lines the gate stops, cost-measured ones included, with dollars
    r = await js(pg, """
      const c = DB.clients.find(c => c.id === 'cl121'), d = c.invoices.find(i => i.mode === 'sov' && i.status === 'draft');
      d.lines.forEach(l => l.pct = /^Demolition/.test(l.item) ? 10 : 0); save();
      dvClose(); clientOpen = c.id; docOpen = { kind: 'invoice', id: d.id }; view = 'billing'; dvEditing = d.id; render(); await sleep(300);
      const el = document.getElementById('pb-ahead-total');
      return el ? el.innerText : '';""")
    c.ok('Demolition' in r and '$2,800 this period' in r, f"[{tag}] 8: the banner names Demolition and its $2,800 ({r[:260]})")
    # 9. the client's portal never shows the firm's billed-ahead measure
    r = await js(pg, """
      signIn('u_klein'); view = 'home'; render(); await sleep(400);
      const t = document.body.innerText; signIn('u_billing'); render();
      return { ahead: /ahead of the work|points ahead|billed ahead/i.test(t), t: (t.match(/[^\\n]*ahead[^\\n]*/i) || [''])[0] };""")
    c.ok(not r['ahead'], f"[{tag}] 9: the Kleins' portal does not say billing is ahead of the work ({r['t'][:160]})")
    # 10. a document opened from the job's Contract and Billing closes back to the job
    r = await js(pg, """
      const c = DB.clients.find(c => c.id === 'cl121'), d = c.invoices.find(i => i.number === 'INV-2026-038');
      setCurrent('p121'); view = 'dash'; render(); await sleep(200);
      const v0 = view; jpOpenDoc(c, 'invoice', d.id); await sleep(300);
      const open = !!document.getElementById('dv'); dvAct('close'); render(); await sleep(200);
      return { v0, open, v1: view };""")
    c.ok(r['open'] and r['v1'] == r['v0'], f"[{tag}] 10: Close returns to the job the invoice was opened from ({r})")
    # 11. a draft never sent: its due date follows its date and terms
    r = await js(pg, """
      const c = DB.clients.find(c => c.id === 'cl121'), d = c.invoices.find(i => i.mode === 'sov' && i.status === 'draft');
      clientOpen = c.id; docOpen = { kind: 'invoice', id: d.id }; dvEditing = d.id; view = 'billing'; render(); await sleep(300);
      const el = document.querySelector('#doc-' + d.id + ' [data-d="date"]') || document.querySelector('[data-d="date"]');
      if (!el) return { none: true };
      el.value = '2026-09-10'; el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); await sleep(200);
      return { date: d.date, due: d.due, want: cxDueFor('2026-09-10', d.terms) };""")
    c.ok(r.get('due') == r.get('want') and r.get('date') == '2026-09-10', f"[{tag}] 11: a new date on the draft moves its due date by its terms ({r})")
    # 12. paid by a payment not yet in the bank: the next step is Find in Bank
    r = await js(pg, """
      const c = DB.clients.find(c => /Rivera/.test(c.name)), d = c.invoices.find(i => i.status === 'paid');
      dvOpen('invoice', d.id, c.id); await sleep(300);
      const bar = [...document.querySelectorAll('#dv .dv-bar button')].map(b => (b.className.includes('primary') ? '*' : '') + b.textContent.trim());
      const word = dvStatusWord({ kind: 'invoice', c, d }); dvClose();
      return { bar, word };""")
    c.ok(any(x == '*Find in Bank' for x in r['bar']) and 'not yet in the bank' in r['word'], f"[{tag}] 12: Rivera's paid invoice reads not in the bank, with Find in Bank as its step ({r})")
    # 14. Duplicate on a pay application works
    r = await js(pg, """
      const c = DB.clients.find(c => c.id === 'cl121'), d = c.invoices.find(i => i.number === 'INV-2026-038'), n0 = c.invoices.length;
      let err = ''; try { await docAction(c, d, 'dup'); } catch (e) { err = String(e.message || e); }
      const n = c.invoices[c.invoices.length - 1];
      return { err, made: c.invoices.length - n0, lines: n && (n.lines || []).length };""")
    c.ok(not r['err'] and r['made'] == 1 and r['lines'], f"[{tag}] 14: Duplicate on INV-2026-038 makes a draft with its schedule lines ({r})")
    c.ok(not errs, f'[{tag}] S2: page errors: {errs[:2]}')
    await b.close()


async def main():
    c = Checks()
    only = sys.argv[1] if len(sys.argv) > 1 else ''
    async with async_playwright() as p:
        for phone in (False, True):
            if only in ('', '1'):
                print(f"-- 1. the reason covers what it was given for, {'phone' if phone else 'desktop'}")
                await t1_reason_covers(p, c, phone)
            if only in ('', '2'):
                print(f"-- 2. credit on account that does not exist, {'phone' if phone else 'desktop'}")
                await t2_phantom_credit(p, c, phone)
            if only in ('', '3'):
                print(f"-- 3. one credit, one reading, {'phone' if phone else 'desktop'}")
                await t3_one_credit(p, c, phone)
            if only in ('', '4'):
                print(f"-- 4. the billed contract, {'phone' if phone else 'desktop'}")
                await t4_contract(p, c, phone)
            if only in ('', '5'):
                print(f"-- 5. a revision keeps the original's accounting, {'phone' if phone else 'desktop'}")
                await t5_revise(p, c, phone)
            if only in ('', 's2'):
                print(f"-- S2 and S3, {'phone' if phone else 'desktop'}")
                await t_s2(p, c, phone)
        if only in ('', '1'):
            print('-- 1. a reason does not cover another line')
            await t1_new_line(p, c)
    raise SystemExit(c.done())

asyncio.run(main())
