"""Phone at 390px: the tap targets the chain lane's field walk found short, checked as a class (integration pass).

The walk (review/chain/trace.md, Phone) measured Approve on Do Now 88x36, the client's proposal and change-order
Approve 96x36, New Change Order 155x36, Send to Client 206x36 and above the screen, View on the pay application
308x36, the client's "I approve" checkbox 24x24, and the foreman's Update below the fold (y 1275). The fix is the
shared .btn / .btn.sm class (44px at phone width), the checkbox's label as a 44px row, a document opening at its top,
and Today's Work first on the foreman's Today.

Each target: at least 44px tall; at least 8px from its nearest neighbour that a finger could actually hit (controls
under the open sheet or behind the bottom tabs are not neighbours: elementFromPoint decides); no sideways scroll.
"""
import asyncio
from harness import *

MEASURE = """(sel) => { const e = [...document.querySelectorAll(sel)].find(x => x.getClientRects().length); if (!e) return null;
  const r = e.getBoundingClientRect(), hittable = (x) => { const b = x.getBoundingClientRect(); if (!b.width || !b.height) return false;
    const t = document.elementFromPoint(Math.min(innerWidth - 1, Math.max(0, b.left + b.width / 2)), Math.min(innerHeight - 1, Math.max(0, b.top + b.height / 2))); return !!t && (t === x || x.contains(t)); };
  const lab = e.closest('label'), box = lab ? lab.getBoundingClientRect() : r;
  let gap = 999;
  [...document.querySelectorAll('button, a, input, select, textarea')].filter(x => x !== e && !e.contains(x) && !x.contains(e) && !(lab && lab.contains(x)) && x.getClientRects().length && hittable(x)).forEach(x => {
    const b = x.getBoundingClientRect(); if (Math.abs(b.top - box.top) > 80) return;
    const dx = Math.max(0, b.left - box.right, box.left - b.right), dy = Math.max(0, b.top - box.bottom, box.top - b.bottom);
    if (dx || dy) gap = Math.min(gap, Math.max(dx, dy)); });
  return { h: Math.round(box.height), w: Math.round(box.width), top: Math.round(r.top), bottom: Math.round(r.bottom), vh: innerHeight, gap: Math.round(gap), sw: document.documentElement.scrollWidth }; }"""


async def check(pg, c, sel, what, fold=False):
    await pg.wait_for_timeout(250)
    m = await pg.evaluate(MEASURE, sel)
    c.ok(m is not None, f'{what}: on the screen ({sel})')
    if not m: return
    c.ok(m['h'] >= 44, f"{what}: {m['w']}x{m['h']}, want at least 44px tall")
    c.ok(m['gap'] >= 8, f"{what}: {m['gap']}px from the nearest control, want at least 8")
    c.ok(m['sw'] <= 390, f"{what}: the page scrolls sideways ({m['sw']}px)")
    if fold: c.ok(m['top'] >= 0 and m['bottom'] <= m['vh'] - 56, f"{what}: on the first screen without scrolling (y {m['top']}..{m['bottom']} of {m['vh']})")


async def main():
    c = Checks()
    async with async_playwright() as p:
        b, pg, errs = await open_app(p, True)
        # the Owner's Do Now and Caught for You verbs
        await sign_in(pg, 'u_owner'); await go(pg, 'home')
        await check(pg, c, '.view.on .td-do [data-tdverb="0"]', 'Owner Home: the first Do Now verb (Approve)')
        await check(pg, c, '.view.on .td-catch .td-verb', 'Owner Home: a Caught for You verb')
        # the PM's change order: New Change Order, Create in the sheet, then Send to Client on the new document
        await sign_in(pg, 'u_alan')
        await pg.evaluate("() => { const c = DB.clients.find(x => x.id === DB.projects.find(p => p.id === 'p121').clientId); view = 'clients'; clientOpen = c.id; clientTab = 'fin'; finTab = 'co'; docOpen = null; render(); const b = [...document.querySelectorAll('section.view.on [data-newdoc^=co]')].find(x => x.getClientRects().length); b ? b.scrollIntoView({ block: 'center' }) : window.scrollTo(0, 600); }")
        # measured where a finger meets it, in view above the bottom tabs (at a fixed scroll it sat half behind the
        # tab bar, so the gap was read to a tab in front of it)
        await check(pg, c, "section.view.on [data-newdoc^='co']", 'PM: New Change Order')
        await pg.locator("section.view.on [data-newdoc^='co']").first.click()
        await check(pg, c, '#mbm #mbm-ok', 'PM: the sheet\'s Create')
        await pg.evaluate("() => { const m = document.getElementById('mbm'); m.querySelectorAll('input:not([type=checkbox]), textarea').forEach(f => { if (!f.value) { f.value = f.type === 'number' ? '1' : 'Phone check'; f.dispatchEvent(new Event('input', { bubbles: true })); } }); }")
        await pg.click('#mbm #mbm-ok'); await pg.wait_for_timeout(500)
        if await pg.locator('#mbm #mbm-ok').count():
            await pg.click('#mbm #mbm-ok'); await pg.wait_for_timeout(500)
        has = await pg.evaluate("() => !!docOpen")
        c.ok(has, 'PM: the change order opened as a document')
        if has: await check(pg, c, 'section.view.on [data-docact=sendclient]', 'PM: Send to Client on the new change order', fold=True)
        # the client: a proposal to approve, its checkbox, and View on an invoice or pay application
        await sign_in(pg, 'u_klein')
        await pg.evaluate("""() => { const u = DB.users.find(x => x.id === 'u_klein'), c = DB.clients.find(x => x.id === u.clientId) || DB.clients[0];
          const e = c.estimates.find(x => x.status !== 'converted') || c.estimates[0]; if (e && !['sent'].includes(e.status)) e.status = 'sent'; }""")
        await sign_in(pg, 'u_klein')
        await pg.wait_for_timeout(300)
        if await pg.locator('section.view.on [data-papprove]').count():
            await check(pg, c, 'section.view.on [data-papprove]', 'Client: Approve on Waiting on You')
            await pg.locator('section.view.on [data-papprove]').first.click(); await pg.wait_for_timeout(400)
            if await pg.locator('#pa-agree').count(): await check(pg, c, '#pa-agree', 'Client: the "I approve" checkbox (its label is the target)')
            await pg.evaluate("() => mbCloseModal()")
        else:
            c.ok(False, 'Client: Approve on Waiting on You is on the screen')
        if await pg.locator('section.view.on [data-pview]').count(): await check(pg, c, 'section.view.on [data-pview]', 'Client: View on an invoice or pay application')
        # the foreman: Today's Work and its Update on the first screen
        await sign_in(pg, 'u_angel'); await go(pg, 'ftoday'); await pg.evaluate("() => window.scrollTo(0, 0)")
        await check(pg, c, '#ftoday-body [data-prgopen]', "Foreman Today: Update on the first task", fold=True)
        c.ok(not errs, f'page errors: {errs[:3]}')
        await b.close()
    return c.done()

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
