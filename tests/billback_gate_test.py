"""Bill-back and the billed-ahead reason gate (BACKLOG section 11, rows 24 and 25; review/round_1112/wave3/billing2.md,
findings S1-1 and S1-2, both marked unverified by the billing reviewer). Invented demo data only.

1  S1-1, "two Home Depot card purchases coded to 121 State are not offered for bill-back". The two card lines (t4 on
   8/14, t10 on 8/27) are coded by the person to estimate line es1:l2, "Framing, blocking & rough carpentry", a lump
   sum of $41,000 on the signed contract (EST-2026-014, converted; progress billing, 10% retainage). The job is not
   cost-plus or reimbursable anywhere (stockClientOwned reads the job's and the client's contract type). Lumber for the
   framing on a fixed-price framing line is the firm's cost inside the price: billing it back would bill the client
   twice. The app's rule (rbWhy) offers a card purchase for bill-back only when a person or the line says it was
   bought for the client, a client selection's maker, or a showroom; a purchase on a contract line is not one. The
   finding is false. The guard: those two stay off the bill-back lists, the line is within its cost budget (no
   overrun to raise a change order for), and the class still works: a purchase on the same job a person marks as
   bought for the client shows on the invoice editor's Billable Expenses pull and on Billing.
2  S1-2, "a line billed ahead takes another 10% with no reason asked at entry". The firm's rule: billing a line
   further ahead of its work needs a typed reason before the invoice goes to the client, recorded on the invoice.
   Driven as billing: open INV-2026-039, type This Period % as the reviewer did (0 on lines 2 and 5, 10 on lines 1,
   4 and 6), then try every way out: Send to Client (and its Send), More > Mark as Sent, Draft Cover Email, and the
   portal. Each must hold the invoice in draft until a reason is typed; the reason goes on the invoice and the audit.
3  Hold, then complete, from every door on both devices: the editor's Send to Client, the editor's Mark as Sent and
   the document viewer's Send to Client (documents first). The reason sheet comes first, an empty reason is refused,
   and the reason resumes the door pressed, so a Send to Client still mails it and posts it to the portal. (11-14: the
   viewer's Send opened the send sheet first and the reason sheet died with it; the draft could never go out.)
"""
import asyncio, sys
from harness import *

SLEEP = "ms => new Promise(r => setTimeout(r, ms))"


async def js(pg, body, arg=None):
    return await pg.evaluate("async (arg) => { const sleep = " + SLEEP + "; " + body + " }", arg)


INV = """
  const C = DB.clients.find(c => (c.invoices || []).some(i => i.id === window.__bbInv));
  const D = C && C.invoices.find(i => i.id === window.__bbInv);
"""


async def s1_billback(p, c):
    b, pg, errs = await open_app(p)
    await sign_in(pg, 'u_billing')
    r = await js(pg, """
      const p = DB.projects.find(x => x.id === 'p121');
      const T = ['t4', 't10'].map(id => DB.txns.find(t => t.id === id));
      const ref = findLine('estimate:es1:l2');
      const f = lineFin('estimate:es1:l2') || {};
      const rb = rbRows('p121');
      return {
        found: T.map(t => !!t), amts: T.map(t => t && t.amt), lines: T.map(t => t && t.line), pids: T.map(t => t && t.projectId),
        why: T.map(t => t ? rbWhy(t) : 'missing'), onRb: rb.filter(x => x.t && ['t4', 't10'].includes(x.t.id)).length,
        lineItem: ref && ref.line.item, unit: ref && ref.line.unit, estStatus: ref && ref.doc.status, price: ref && lineAmount(ref.line, ref.doc),
        costPlus: stockClientOwned(p), actual: f.actual, budget: f.budget, flags: f.flags || [],
      };
    """)
    c.ok(all(r['found']), f"the two Home Depot card lines are in the bank feed: {r['found']}")
    c.ok(r['pids'] == ['p121', 'p121'] and r['lines'] == ['estimate:es1:l2', 'estimate:es1:l2'],
         f"both are coded to 121 State's contract line es1:l2: {r['pids']} {r['lines']}")
    c.ok(r['amts'] == [-1287.44, -2131.5], f"the amounts are $1,287.44 and $2,131.50: {r['amts']}")
    c.ok(r['estStatus'] == 'converted' and r['unit'] == 'ls' and r['price'] == 41000,
         f"es1:l2 is a lump sum on the signed contract ({r['lineItem']}, {r['unit']}, {r['price']}, {r['estStatus']})")
    c.ok(r['costPlus'] is False, '121 State is not a cost-plus or reimbursable job')
    c.ok(r['why'] == ['', ''] and r['onRb'] == 0,
         f"a purchase inside a fixed-price contract line is not offered for bill-back (rbWhy {r['why']}, on rbRows {r['onRb']})")
    c.ok(r['budget'] and r['actual'] <= r['budget'] and 'over budget' not in r['flags'],
         f"the framing line is within its cost budget (actual {r['actual']} of {r['budget']}, flags {r['flags']}): no overrun for a change order")

    # the class still works: a purchase on the same job a person marks as bought for the client is offered to billing
    r2 = await js(pg, """
      const t = { id: 'tbb1', date: '2026-09-02', acct: 'ac2', desc: 'HOME DEPOT #6166 BROOKLYN NY', amt: -412.18, cat: 'materials',
        projectId: 'p121', vendor: 'Home Depot', status: 'categorized', actor: 'Billing test', memo: 'bought for the client: closet rods they chose' };
      DB.txns.push(t);
      const rb = rbRows('p121').filter(x => x.t && x.t.id === 'tbb1');
      const ready = rbReady().filter(x => x.kind === 'reimbursable' && x.p.id === 'p121');
      return { n: rb.length, amt: rb[0] && rb[0].amount, ready: ready.map(x => x.title) };
    """)
    c.ok(r2['n'] == 1, f"a 121 State purchase marked bought for the client is on the bill-back rows: {r2}")
    c.ok(any('HOME DEPOT' in t for t in r2['ready']), f"and on Billing's Ready to Bill: {r2['ready']}")
    c.ok(not errs, f'page errors: {errs[:2]}')
    await b.close()


async def open_039(pg):
    """Billing, the 121 State draft, opened from its row as the reviewer did (Review/Draft opens the invoice)."""
    await js(pg, "try { mbCloseModal(); } catch (e) {} view = 'billing'; billTab = 'billable'; docOpen = null; render(); await sleep(400);")
    # Billing's blue button, "Draft $12,651 — 121 State", makes the application (it becomes INV-2026-039)
    clicked = await js(pg, """
      const row = (x) => { let e = x; for (let k = 0; k < 6 && e; k++, e = e.parentElement) { if (e.querySelectorAll('button[data-blact]').length > 1) return null; if (/12,651/.test(e.textContent)) return e; } return null; };
      const b = [...document.querySelectorAll('button[data-blact]')].find(x => x.offsetParent && /^Draft/.test(x.textContent.trim()) && row(x));
      const label = b ? row(b).textContent.replace(/\\s+/g, ' ').trim().slice(0, 120) : '';
      if (b) { b.click(); await sleep(700); }
      return { label, open: docOpen && docOpen.id };
    """)
    return clicked


async def type_pct(pg, idx_val):
    """Type This Period % into the lines by their position, as the reviewer did."""
    for i, v in idx_val:
        lid = await js(pg, INV + "return (D.lines[arg] || {}).id;", i)
        loc = pg.locator(f'tr[data-line="{lid}"] [data-f="pct"]').first
        await loc.fill(str(v))
        await loc.press('Tab')
        await pg.wait_for_timeout(250)


async def s2_gate(p, c, phone=False):
    tag = 'phone' if phone else 'desktop'
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, 'u_billing')
    o = await open_039(pg)
    c.ok(o['label'] and o['open'], f"[{tag}] Billing's Draft for 121 State opens the new application: {o}")
    if not o['open']:
        await b.close(); return
    await js(pg, "window.__bbInv = arg;", o['open'])
    base = await js(pg, INV + """
      return { num: D.number, st: D.status, mode: D.mode, pid: D.projectId, n: D.lines.length, items: D.lines.map(l => l.item.slice(0, 14) + ' ' + l.pct + '/' + l.prevPct), ahead: pbAhead(D.projectId).lines.map(l => l.item) };
    """)
    print(f"[{tag}]", base)
    c.ok(base['st'] == 'draft' and base['mode'] == 'sov' and base['n'] >= 6, f"[{tag}] {base['num']} is a draft pay application: {base}")
    if not phone:
        await type_pct(pg, [(1, 0), (4, 0), (0, 10), (3, 10), (5, 10)])
    else:
        await js(pg, INV + "[[1,0],[4,0],[0,10],[3,10],[5,10]].forEach(([i, v]) => D.lines[i].pct = v); save(); render(); await sleep(300);")
    st = await js(pg, INV + """
      const F = pbFurther(C, D);
      return { pcts: D.lines.map(l => +l.pct || 0), further: F.map(x => [x.l.item, x.to, x.pct]), st: D.status, banner: !!document.getElementById('pb-ahead-total') };
    """)
    c.ok(st['pcts'][0] == 10 and st['pcts'][1] == 0, f"[{tag}] the typed percentages are on the invoice: {st['pcts']}")
    c.ok(len(st['further']) >= 1 and any('Demolition' in x[0] for x in st['further']),
         f"[{tag}] Demolition is billed further ahead of its work: {st['further']}")

    async def no_reason_then_status(how):
        """Press a way out; the reason sheet must be up and the invoice still a draft."""
        s = await js(pg, INV + """
          await sleep(500);
          const m = document.getElementById('mbm');
          const txt = m ? m.textContent : '';
          return { st: D.status, sheet: /Billed Ahead of the Work/.test(txt), demo: /Demolition[^:]*: 61.67% billed to date against 7.67% complete by cost/.test(txt), sent: !!D.sentAt, why: !!D.aheadWhy };
        """)
        c.ok(s['st'] == 'draft' and not s['sent'], f"[{tag}] {how}: the invoice stays a draft with no reason ({s})")
        c.ok(s['sheet'], f"[{tag}] {how}: the Billed Ahead of the Work reason sheet is up ({s})")
        c.ok(s['demo'], f"[{tag}] {how}: the sheet names Demolition, 61.67% billed against 7.67% complete by cost ({s})")
        return s

    # 1. Send to Client, then its Send
    await js(pg, "try { mbCloseModal(); } catch (e) {} await sleep(150);")
    btn = pg.locator('[data-docact="sendclient"]:visible').first
    c.ok(await btn.count() == 1, f"[{tag}] the draft has Send to Client")
    if await btn.count():
        await btn.click()
        await pg.wait_for_timeout(400)
        send = await js(pg, """
          const m = document.getElementById('mbm'); if (!m) return 'no sheet';
          if (/Billed Ahead of the Work/.test(m.textContent)) return 'gate';
          const to = m.querySelector('[data-f="to"]'); if (to && !to.value) { to.value = 'client@example.com'; to.dispatchEvent(new Event('input', {bubbles: true})); }
          const ok = m.querySelector('#mbm-ok'); ok && ok.click(); return 'sent';
        """)
        await no_reason_then_status(f'Send to Client ({send})')
    # an empty reason is refused
    await js(pg, "const m = document.getElementById('mbm'); m && m.querySelector('#mbm-ok') && m.querySelector('#mbm-ok').click(); await sleep(300);")
    s = await js(pg, INV + "return { st: D.status, why: !!D.aheadWhy };")
    c.ok(s['st'] == 'draft' and not s['why'], f"[{tag}] an empty reason does not send it ({s})")

    # 2. More > Mark as Sent
    await js(pg, "try { mbCloseModal(); } catch (e) {} await sleep(200);")
    await js(pg, INV + "const b = document.querySelector('.doc-more-menu [data-docact=\"send\"]'); b && b.click();")
    await no_reason_then_status('Mark as Sent')

    # 3. Draft Cover Email does not move it out of draft
    await js(pg, "try { mbCloseModal(); } catch (e) {} await sleep(200);")
    await js(pg, INV + "await docAction(C, D, 'email'); await sleep(300); try { mbCloseModal(); } catch (e) {}")
    s = await js(pg, INV + "return { st: D.status, sent: !!D.sentAt };")
    c.ok(s['st'] == 'draft' and not s['sent'], f"[{tag}] Draft Cover Email leaves it a draft ({s})")

    # 4. the portal does not show a draft
    s = await js(pg, INV + """
      // documents first: what is open in the document viewer is state too, and a sign-in clears it
      const back = [view, clientOpen, docOpen], dvBack = typeof dvCur === 'undefined' ? undefined : dvCur;
      signIn('u_klein'); render(); await sleep(400);
      const isC = DB.projects.some(p => p.id === 'p121' && p.clientId === C.id);
      const txt = document.body.innerText;
      signIn('u_billing'); [view, clientOpen, docOpen] = back; if (dvBack !== undefined) dvCur = dvBack; render(); await sleep(300);
      return { isC, shows: txt.includes('INV-2026-039') };
    """)
    c.ok(s['isC'] and not s['shows'], f"[{tag}] the client's portal (u_klein) does not show the draft ({s})")

    c.ok(not errs, f'[{tag}] page errors: {errs[:2]}')
    await b.close()


ROUTES = {
    # the editor's blue Send to Client, the editor's More > Mark as Sent, and the document viewer's Send to Client
    # (documents first, 11-13: the screen an invoice opens on). One gate, one continuation, from every door.
    'editor Send to Client': ('editor', '[data-docact="sendclient"]:visible', True),
    'editor Mark as Sent': ('editor', '.doc-more-menu [data-docact="send"]', False),
    'viewer Send to Client': ('viewer', '#dv [data-dvact="send"]:visible', True),
}


async def s2_complete(p, c, route, phone=False):
    """A fresh draft billed further ahead; the door holds it for a reason, then the reason lets it go out."""
    tag = f"{'phone' if phone else 'desktop'}, {route}"
    where, sel, mails = ROUTES[route]
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, 'u_billing')
    o = await open_039(pg)
    if not o['open']:
        c.ok(False, f"[{tag}] no draft to send: {o}"); await b.close(); return
    await js(pg, "window.__bbInv = arg;", o['open'])
    await js(pg, INV + "[[1,0],[4,0],[0,10],[3,10],[5,10]].forEach(([i, v]) => D.lines[i].pct = v); save(); render(); await sleep(300);")
    # stand the invoice where the route starts: the viewer, or the editor (the viewer's Edit)
    await js(pg, INV + """
      try { mbCloseModal(); } catch (e) {}
      const inDv = typeof dvCur !== 'undefined' && dvCur && dvCur.id === D.id;
      if (arg === 'viewer' && !inDv) { docOpen = null; clientOpen = C.id; dvOpen('invoice', D.id, C.id); render(); await sleep(400); }
      if (arg === 'editor' && !(docOpen && docOpen.id === D.id)) {
        const e = document.querySelector('#dv [data-dvact="edit"]');
        if (e) { e.click(); await sleep(500); }
        if (!(docOpen && docOpen.id === D.id)) { if (typeof dvClose === 'function' && typeof dvCur !== 'undefined' && dvCur) dvClose(); clientOpen = C.id; docOpen = { kind: 'invoice', id: D.id }; render(); await sleep(400); }
      }
    """, where)
    if where == 'viewer' and not await pg.locator(sel).count() and await pg.locator('#dv [data-dvact="more"]:visible').count():
        await pg.locator('#dv [data-dvact="more"]:visible').first.click(); await pg.wait_for_timeout(200)
    if 'Mark as Sent' in route:
        await js(pg, "const s = document.querySelector('.doc-more summary'); s && s.offsetParent && s.click(); await sleep(150);")
    btn = pg.locator(sel).first
    c.ok(await btn.count() == 1, f"[{tag}] the button is there")
    if not await btn.count():
        await b.close(); return
    if await btn.is_visible():
        await btn.click()
    else:  # More's menu item, pressed as step 2 presses it
        await btn.dispatch_event('click')
    await pg.wait_for_timeout(600)
    # the hold: the reason sheet comes first, and the draft stays a draft; an empty reason is refused
    s = await js(pg, INV + """
      const m = document.getElementById('mbm');
      return { st: D.status, sheet: m ? m.querySelector('h3').textContent : 'none', why: !!m && !!m.querySelector('[data-f="why"]') };
    """)
    c.ok(s['st'] == 'draft' and s['why'] and 'Billed Ahead of the Work' in s['sheet'], f"[{tag}] holds: the reason sheet first, still a draft ({s})")
    if not s['why']:
        await b.close(); return
    await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(300)
    s = await js(pg, INV + "return { st: D.status, why: !!D.aheadWhy, up: !!document.querySelector('#mbm [data-f=\"why\"]') };")
    c.ok(s['st'] == 'draft' and not s['why'] and s['up'], f"[{tag}] an empty reason is refused ({s})")
    # the completion: the reason, then the door's own sheet (Send to Client's To / Subject / Message), then out
    await pg.locator('#mbm [data-f="why"]').fill('the contract bills demolition on mobilization, per the owner')
    await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(700)
    nxt = await js(pg, "const m = document.getElementById('mbm'); return m ? m.querySelector('h3').textContent : 'none';")
    if mails:
        c.ok('Send to Client' in nxt, f"[{tag}] the reason resumes the send: its sheet comes next ({nxt})")
        to = pg.locator('#mbm [data-f="to"]')
        if await to.count():
            if not await to.input_value():
                await to.fill('client@example.com')
            await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(900)
    s = await js(pg, INV + """
      const A = (DB.audit || []).filter(a => a.refId === D.id && a.action === 'billed-ahead');
      return { st: D.status, why: D.aheadWhy && D.aheadWhy.why, by: D.aheadWhy && D.aheadWhy.by,
               audit: A.some(a => /mobilization/.test(a.note || '')), outbox: (DB.outbox || []).some(o => o.about && o.about.docId === D.id) };
    """)
    c.ok(s['st'] == 'sent', f"[{tag}] with the reason it goes out ({s})")
    c.ok(s['why'] and 'mobilization' in s['why'] and s['by'], f"[{tag}] the reason and who gave it are on the invoice ({s})")
    c.ok(s['audit'], f"[{tag}] the reason is in the audit ({s})")
    if mails:
        c.ok(s['outbox'], f"[{tag}] it is sent to the client (outbox, portal), not only marked sent ({s})")
    c.ok(not errs, f'[{tag}] page errors: {errs[:2]}')
    await b.close()


async def main():
    c = Checks()
    only = sys.argv[1] if len(sys.argv) > 1 else ''
    async with async_playwright() as p:
        if only in ('', '1'):
            print('-- 1. S1-1: bill-back of the two Home Depot card lines')
            await s1_billback(p, c)
        if only in ('', '2'):
            print('-- 2. S1-2: the billed-ahead reason gate, desktop')
            await s2_gate(p, c)
            print('-- 2. S1-2: the billed-ahead reason gate, phone')
            await s2_gate(p, c, phone=True)
        if only in ('', '2', '3'):
            for phone in (False, True):
                for route in ROUTES:
                    print(f"-- 3. hold, then complete with a reason: {route}, {'phone' if phone else 'desktop'}")
                    await s2_complete(p, c, route, phone)
    raise SystemExit(c.done())

asyncio.run(main())
