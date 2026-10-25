"""phone_cover_test: no layer covers a control on a phone editor (Pilot 2, lane p2fix1, 2026-10-25).

What the pilot saw (u_alan, 390x844, touch): Clients > Sarah & David Klein > New Estimate > Start Estimate, then Add
Line Item. After that every tap on the estimate (the line row, Title, Scope, Inclusions, Exclusions, Template) hit
another element; Escape and leaving and coming back did not clear it; the line count went from 1 to 0 on return.
The line sheet (#ct-sheet, a full-screen layer on <body>) outlived the screen it belonged to: only its own Done closed
it. The blank template line was drawn and counted as "1 line" and pruned on leave (lkPrune), so the count flipped.

This suite walks the estimate, invoice, change order and purchase order editors on the phone as the PM, the
coordinator, billing and the owner, the way each opens them, and fails when:
  COVERED   elementFromPoint at the centre of a visible control (the visible part of it, scrolled through the page)
            is not that control or inside it: some layer sits on it. The toast is dismissed first, as a tap does.
  STALE     a sheet is still on screen after Escape, Back, or a move to another page
  WIDE      a table wider than its box, or the page wider than the phone (a sideways scroll)
  COUNT     the line count shown is not the number of lines kept after leaving and coming back
  START     the job's Estimates tab, reached from Projects, has no New Estimate, or it does not start for that job
  MENU      the PM's phone menu does not reach Estimates in two taps from the open menu
  ASK       the header's Ask is not on screen and named at 390px for an office role
Usage: python3 phone_cover_test.py
"""
import asyncio, re
from harness import *

# The visible part of a control, its centre, and what the finger would hit there. A control is checked when its
# visible centre lies between the header and the bottom bar (the page scrolls under those by design).
COVER = r"""(scope) => {
  const W = innerWidth, H = innerHeight;
  const root = document.querySelector(scope); if (!root) return { err: 'no ' + scope };
  document.querySelectorAll('.toast').forEach(t => t.classList.remove('on', 'act', 'toast-up'));
  const fixedTop = () => { const h = [...document.querySelectorAll('header.topbar, #subnav')].filter(e => e.getClientRects().length && /fixed|sticky/.test(getComputedStyle(e).position)); return h.length ? Math.max(...h.map(e => e.getBoundingClientRect().bottom)) : 0; };
  const fixedBot = () => { const b = [...document.querySelectorAll('#mtabs, #tabbar, #fsay, .dl-nav, [data-fixedbar]')].filter(e => e.getClientRects().length && getComputedStyle(e).position === 'fixed' && e.getBoundingClientRect().top > H / 2); return b.length ? Math.min(...b.map(e => e.getBoundingClientRect().top)) : H; };
  const inSheet = scope !== '.view.on';
  const top = inSheet ? 0 : fixedTop(), bot = inSheet ? H : fixedBot();
  const out = [];
  const els = [...root.querySelectorAll('button, a[href], input:not([type=hidden]), textarea, select, summary, [role=button]')];
  for (const e of els) {
    if (e.disabled) continue;
    const s = getComputedStyle(e); if (s.visibility === 'hidden' || s.display === 'none' || +s.opacity === 0 || s.pointerEvents === 'none') continue;
    if (e.closest('details:not([open])') && !e.matches('details > summary')) continue;
    let r = e.getBoundingClientRect(); if (r.width < 2 || r.height < 2) continue;
    let L = Math.max(0, r.left), R = Math.min(W, r.right), T = Math.max(top, r.top), B = Math.min(bot, r.bottom);
    for (let a = e.parentElement; a && a !== document.body; a = a.parentElement) { const st = getComputedStyle(a);
      if (st.overflowX !== 'visible' || st.overflowY !== 'visible') { const b = a.getBoundingClientRect(); if (st.overflowX !== 'visible') { L = Math.max(L, b.left); R = Math.min(R, b.right); } if (st.overflowY !== 'visible') { T = Math.max(T, b.top); B = Math.min(B, b.bottom); } } }
    if (R - L < 6 || B - T < 6) continue;
    // the whole control must be on screen in the band to be judged (a half-scrolled one is judged on the next step)
    if (r.top < top - 1 || r.bottom > bot + 1) continue;
    const x = (L + R) / 2, y = (T + B) / 2, h = document.elementFromPoint(x, y);
    if (!h || h === e || e.contains(h)) continue;
    const lab = e.closest('label'); if (lab && lab.contains(h)) continue;
    if (e.id && h.closest && h.closest(`label[for="${CSS.escape(e.id)}"]`)) continue;
    let layer = h; for (let a = h; a && a !== document.body; a = a.parentElement) if (/fixed|absolute|sticky/.test(getComputedStyle(a).position)) { layer = a; break; }
    const d = el => el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (typeof el.className === 'string' && el.className.trim() ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : '');
    out.push(`${d(e)} "${((e.innerText || e.placeholder || e.getAttribute('aria-label') || e.value || '') + '').replace(/\s+/g, ' ').trim().slice(0, 30)}" under ${d(layer)} "${(layer.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30)}"`);
  }
  out.toast = [...document.querySelectorAll('.toast')].map(t => t.id + ':' + t.className);
  return { out, toast: out.toast, band: [Math.round(top), Math.round(bot)], sh: document.documentElement.scrollHeight };
}"""

WIDE = r"""() => { const W = innerWidth, v = document.querySelector('.view.on'), out = [];
  if (!v) return ['no page'];
  v.querySelectorAll('table').forEach(t => { if (!t.getClientRects().length) return; const r = t.getBoundingClientRect(); let L = 0, R = W;
    for (let a = t.parentElement; a && a !== document.body; a = a.parentElement) { const s = getComputedStyle(a); if (s.overflowX !== 'visible') { const b = a.getBoundingClientRect(); L = Math.max(L, b.left); R = Math.min(R, b.right); } }
    if (r.width > W + 1 || r.right > R + 1 || r.left < L - 1) out.push(`table ${Math.round(r.width)}px in ${Math.round(R - L)}px: ` + (t.innerText || '').replace(/\s+/g, ' ').slice(0, 50)); });
  v.querySelectorAll('*').forEach(e => { const s = getComputedStyle(e); if (!/auto|scroll/.test(s.overflowX) || e.scrollWidth <= e.clientWidth + 2 || !e.getClientRects().length) return;
    if (e.closest('.ctabs, .sub-tabs, .chips, .tk2-strip, .gantt-wrap, .gantt, [data-chart], .chart') || e.matches('.ctabs, .sub-tabs, .chips, textarea, input, select')) return;
    if (e.querySelector('table')) out.push(`sideways scroll ${e.scrollWidth}px in ${e.clientWidth}px: ` + (e.className || e.tagName)); });
  if (document.documentElement.scrollWidth > W) out.push(`page ${document.documentElement.scrollWidth}px wide`);
  return out; }"""

async def walk(pg, c, who, scope='.view.on'):
    """Scroll the page through, a screen at a time, and judge every control on each screen."""
    seen = set()
    if scope != '.view.on':
        # a person reading a sheet has no field focused: the item list a focused field opens is that field's own layer
        await pg.evaluate("() => document.activeElement && document.activeElement.blur && document.activeElement.blur()"); await pg.wait_for_timeout(300)
    await pg.evaluate("window.scrollTo(0, 0)"); await pg.wait_for_timeout(120)
    y = 0
    for _ in range(40):
        m = await pg.evaluate(COVER, scope)
        if m.get('err'): c.ok(False, f'{who}: {m["err"]}'); return
        if m['out']: print('toasts', m.get('toast'))
        for x in m['out']:
            if x not in seen: seen.add(x); c.ok(False, f'COVERED {who} at y={y}: {x}')
        if scope != '.view.on': break
        step = max(200, m['band'][1] - m['band'][0] - 60)
        y += step
        if y >= m['sh']: break
        await pg.evaluate("y => window.scrollTo(0, y)", y); await pg.wait_for_timeout(90)
    c.ok(True, who)
    await pg.evaluate("window.scrollTo(0, 0)")

async def wide(pg, c, who):
    for x in await pg.evaluate(WIDE): c.ok(False, f'WIDE {who}: {x}')

async def reopen(pg, cid, est):
    await pg.evaluate("([c, id]) => { clientOpen = c; clientTab = 'fin'; docOpen = { kind: 'estimate', id }; setView('clients'); }", [cid, est])
    await pg.wait_for_timeout(300)

async def tap(pg, c, sel, who):
    try:
        await pg.locator(sel).first.tap(timeout=5000); await pg.wait_for_timeout(300); return True
    except Exception as ex:
        c.ok(False, f'COVERED {who}: a real tap on {sel} did not land: ' + str(ex).split('Call log')[-1].replace(chr(10), ' ')[:300]); return False

async def sheet_on(pg):
    return await pg.evaluate("() => !!document.getElementById('ct-sheet')")

async def open_doc(pg, kind, pick):
    """Open a client document the way its list does: the client's page, the document open on it."""
    return await pg.evaluate("""([kind, pick]) => {
      for (const c of DB.clients) { const L = kind === 'estimate' ? c.estimates : kind === 'co' ? c.changeOrders : c.invoices;
        const d = (L || []).find(x => pick === 'draft' ? x.status === 'draft' : x.status !== 'draft');
        if (d) { view = 'clients'; clientOpen = c.id; clientTab = 'fin'; docOpen = { kind, id: d.id }; render(); scrollTo(0, 0); return d.number + ' ' + d.status; } }
      return ''; }""", [kind, pick])

async def main():
    c = Checks()
    async with async_playwright() as p:
        b, pg, errs = await open_app(p, True)

        # ---------------------------------------------------------------- 1. the pilot's walk, as the PM
        await sign_in(pg, 'u_alan')
        await go(pg, 'clients')
        cid = await pg.evaluate("(DB.clients.find(c => /Klein/.test(c.name)) || {}).id")
        await pg.evaluate("c => { clientOpen = c; docOpen = null; render(); scrollTo(0, 0) }", cid); await pg.wait_for_timeout(250)
        await pg.locator('#v-clients [data-newest]').first.tap(); await pg.wait_for_timeout(400)
        await pg.locator('#mbm button', has_text=re.compile('Start', re.I)).first.tap(); await pg.wait_for_timeout(700)
        est = await pg.evaluate("() => docOpen && docOpen.id")
        c.ok(bool(est), f'1: Start Estimate opened the new draft ({est})')
        await walk(pg, c, '1: the new estimate as the PM')
        await wide(pg, c, '1: the new estimate')
        shown = await pg.evaluate("() => (document.querySelector('.ct-m-hd span') || {}).textContent || ''")
        await pg.locator('#v-clients .ct-m-add').tap(); await pg.wait_for_timeout(500)
        c.ok(await sheet_on(pg), '1: Add Line Item opens the line sheet')
        await walk(pg, c, '1: the line sheet', '#ct-sheet')
        await pg.locator('#ct-sheet [data-csf=item]').fill('Demolition and protection'); await pg.locator('#ct-sheet [data-csf=rate]').fill('1200')
        await pg.locator('#ct-sheet [data-csf=rate]').press('Tab'); await pg.wait_for_timeout(200)
        await pg.keyboard.press('Escape'); await pg.wait_for_timeout(300)
        c.ok(not await sheet_on(pg), '1: Escape closes the line sheet')
        n = await pg.evaluate("id => { const c = DB.clients.find(c => c.estimates.some(e => e.id === id)); const e = c.estimates.find(e => e.id === id); return { n: e.lines.length, item: (e.lines.find(l => l.item) || {}).item || '' } }", est)
        c.ok(n['item'] == 'Demolition and protection', f'1: what was typed before Escape is kept: {n}')
        await walk(pg, c, '1: the estimate after Escape')
        for tap in ['.ct-m-row', '.est-scope textarea']:
            try:
                await pg.locator('#v-clients ' + tap).first.tap(timeout=4000); ok = True
            except Exception as ex:
                ok = False
            c.ok(ok, f'1: a real tap reaches {tap} after the sheet closed')
            if await sheet_on(pg): await pg.locator('#ct-sheet [data-cts=done]').first.tap(); await pg.wait_for_timeout(300)
        # the sheet open, then Back (the phone's back), then away and back
        await tap(pg, c, '#v-clients .ct-m-row', '1: a line row')
        c.ok(await sheet_on(pg), '1: a line row opens its sheet')
        await pg.evaluate("() => history.back()"); await pg.wait_for_timeout(500)
        c.ok(not await sheet_on(pg), f'STALE 1: Back closes the line sheet (view {await pg.evaluate("view")})')
        await reopen(pg, cid, est)
        await tap(pg, c, '#v-clients .ct-m-row', '1: a line row, again')
        c.ok(await sheet_on(pg), '1: the line sheet is open before leaving')
        await pg.evaluate("() => setView('home')"); await pg.wait_for_timeout(300)
        c.ok(not await sheet_on(pg), '1: moving to another page closes the line sheet')
        await walk(pg, c, '1: Today after leaving the estimate with its sheet open')
        # the count: what the list says is what is kept
        await reopen(pg, cid, est)
        before = await pg.evaluate("() => (document.querySelector('.ct-m-hd span') || {}).textContent || ''")
        await pg.evaluate("() => setView('home')"); await pg.wait_for_timeout(250)
        await reopen(pg, cid, est)
        after = await pg.evaluate("() => (document.querySelector('.ct-m-hd span') || {}).textContent || ''")
        c.ok(before == after == '1 line', f'COUNT 1: the line count holds across leaving and coming back: started {shown!r}, then {before!r}, then {after!r}')
        c.ok(shown == '0 lines', f'COUNT 1: a new estimate does not count its blank starter row as a line: {shown!r}')

        # ---------------------------------------------------------------- 2. every editor, as each role that opens it
        EDITORS = {'u_alan': ['estimate', 'co', 'invoice', 'po'], 'u_owner': ['estimate', 'co', 'invoice', 'po'],
                   'u_billing': ['estimate', 'co', 'invoice'], 'u_chen': ['po']}
        for u, kinds in EDITORS.items():
            await sign_in(pg, u)
            rv = await pg.evaluate("() => ROLE_VIEWS[role()]")
            for k in kinds:
                if k == 'po':
                    if 'po' not in rv: continue
                    for pick in ['draft', 'sent']:
                        num = await pg.evaluate("""pick => { const po = DB.pos.find(x => pick === 'draft' ? x.status === 'draft' : x.status !== 'draft' && x.status !== 'cancelled'); if (!po) return '';
                          poOpen = po.id; setView('po'); return po.number + ' ' + po.status; }""", pick)
                        if not num: continue
                        await pg.wait_for_timeout(300)
                        await walk(pg, c, f'2: {u} PO {num}'); await wide(pg, c, f'2: {u} PO {num}')
                    continue
                if 'clients' not in rv: continue
                for pick in ['draft', 'sent']:
                    num = await open_doc(pg, k, pick)
                    if not num: continue
                    await pg.wait_for_timeout(300)
                    await walk(pg, c, f'2: {u} {k} {num}'); await wide(pg, c, f'2: {u} {k} {num}')
                    if await pg.locator('.view.on .ct-m-row').count():
                        await pg.locator('.view.on .ct-m-row').first.tap(); await pg.wait_for_timeout(300)
                        if await sheet_on(pg):
                            await walk(pg, c, f'2: {u} {k} {num} line sheet', '#ct-sheet')
                            await pg.keyboard.press('Escape'); await pg.wait_for_timeout(200)
                    await pg.evaluate("() => { docOpen = null; }")

        # ---------------------------------------------------------------- 3. New Estimate on the job's Estimates tab
        await sign_in(pg, 'u_alan')
        await pg.evaluate("() => { try { mbCloseModal() } catch (e) {} }")
        await pg.locator('#menu-btn').tap(); await pg.wait_for_timeout(300)
        await pg.locator('#nav-groups button[data-grp=jobs]').first.tap(); await pg.wait_for_timeout(400)
        job = await pg.evaluate("() => (DB.projects.find(p => p.clientId && /State/.test(p.name || p.address || '')) || DB.projects.find(p => p.clientId)).id")
        await pg.evaluate("j => { setCurrent(j); setView('dash'); }", job); await pg.wait_for_timeout(400)
        await pg.locator('#subnav button[data-subtab=estimates]').first.tap(); await pg.wait_for_timeout(500)
        c.ok(await pg.evaluate("() => view === 'billing' && billTab === 'estimates'"), '3: the job strip opens Billing > Estimates')
        nb = pg.locator('#v-billing #bill-newest')
        c.ok(await nb.count() == 1 and await nb.is_visible(), '3: the job\'s Estimates tab carries New Estimate')
        if await nb.count():
            await nb.tap(); await pg.wait_for_timeout(400)
            await pg.locator('#mbm button', has_text=re.compile('Start', re.I)).first.tap(); await pg.wait_for_timeout(600)
            got = await pg.evaluate("() => { if (!docOpen) return null; for (const c of DB.clients) { const d = c.estimates.find(e => e.id === docOpen.id); if (d) return { c: c.id, p: d.projectId }; } return null; }")
            want = await pg.evaluate("j => { const p = DB.projects.find(x => x.id === j); return { c: p.clientId, p: p.id }; }", job)
            c.ok(got == want, f'3: the estimate starts for that client and that job: {got} vs {want}')
            await walk(pg, c, '3: the estimate started from the job')

        # ---------------------------------------------------------------- 4. the PM's menu reaches Estimates in two taps
        await pg.evaluate("() => { docOpen = null; setView('home'); }"); await pg.wait_for_timeout(300)
        await pg.locator('#menu-btn').tap(); await pg.wait_for_timeout(300)
        taps = 0
        exp = pg.locator('#nav-groups [data-mnexp=jobs]')
        if await exp.count():
            await exp.first.tap(); taps += 1; await pg.wait_for_timeout(250)
        kid = pg.locator('#nav-groups [data-mnkid]', has_text=re.compile('^Estimates$'))
        if await kid.count() and await kid.first.is_visible():
            await kid.first.tap(); taps += 1; await pg.wait_for_timeout(500)
        c.ok(taps == 2 and await pg.evaluate("() => view === 'billing' && billTab === 'estimates'"), f'MENU 4: the open menu reaches Estimates in two taps ({taps})')
        c.ok(await pg.evaluate("() => !document.querySelector('.rail.open')"), '4: the menu closes when a page opens')

        # ---------------------------------------------------------------- 5. Ask on every office role's phone header
        for u in ['u_owner', 'u_alan', 'u_chen', 'u_billing', 'u_controller', 'u_sarah']:
            await sign_in(pg, u)
            a = await pg.evaluate("""() => { const a = document.getElementById('tb-ask'); if (!a) return null; const r = a.getBoundingClientRect();
              const h = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
              return { vis: !a.hidden && r.width >= 40 && r.height >= 40 && r.right <= innerWidth, name: a.getAttribute('aria-label') || a.innerText.trim(), top: !!h && a.contains(h) }; }""")
            c.ok(bool(a) and a['vis'] and a['name'] == 'Ask' and a['top'], f'ASK 5: {u} has Ask on the phone header, named and tappable: {a}')

        for x in errs[:5]: c.ok(False, 'page error: ' + x[:200])
        await b.close()
    return c.done()

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
