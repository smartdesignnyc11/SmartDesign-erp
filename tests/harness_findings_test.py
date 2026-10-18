"""Agent-month pilot, harness findings 6-8 (PLAN v11.1), reproduced as the person would hit them, then held.

6. A new change order defaults to the client of the job it is created from. On a job's own screens that is the
   job's client and the job; on a client's page that client; anywhere else (Home, Approvals, Billing with no client
   picked) it asks: the Client field starts empty and Start Change Order waits for it. The same holds for New Invoice
   and New Estimate from the New menu, which used to create the document for whichever job was opened last, without
   asking. Desktop (the header New menu) and the phone at 390px (the client page and Billing, the phone's paths).
7. The PM's main pages are on his phone's bottom bar at 390px, not under More: Home, Approvals, Projects, Tasks and
   Field, with More still there for the rest. Each tab is at least 44px tall and wide enough for its label, the bar
   does not scroll sideways, and each tab opens its page.
8. Every document the client portal lists opens when the client presses View: the proposals and change orders
   waiting on them, the invoices due, and every invoice and change order on Account (which listed them with no way
   to open them). Phone at 390px and desktop."""
import asyncio, sys
from harness import *

CO_STATE = """() => { const m = document.getElementById('mbm'); if (!m) return null;
  const c = m.querySelector('[data-f="clientId"]'), p = m.querySelector('[data-f="projectId"]'), ok = m.querySelector('#mbm-ok');
  return { title: (m.querySelector('h3, .mbm-hd') || {}).innerText || '', client: c ? c.value : null,
           clientText: c && c.selectedIndex >= 0 ? c.options[c.selectedIndex].text : '', project: p ? p.value : null,
           waits: !!(ok && (ok.classList.contains('vf-wait') || ok.getAttribute('aria-disabled') === 'true')) }; }"""

async def new_menu(pg, key):
    """The header's New menu, then one of its items (desktop)."""
    await pg.evaluate("() => { try { mbCloseModal(); } catch (e) {} }")
    await pg.click('#tb-new'); await pg.wait_for_timeout(250)
    await pg.click(f'#tb-newmenu [data-k="{key}"]'); await pg.wait_for_timeout(400)

async def close(pg):
    await pg.evaluate("() => { try { mbCloseModal(); } catch (e) {} document.querySelectorAll('.drawer.on').forEach(d => d.classList.remove('on')); }")
    await pg.wait_for_timeout(120)

async def finding6(c, pg, phone):
    w = 'phone' if phone else 'desktop'
    await sign_in(pg, 'u_alan')
    n0 = await pg.evaluate("() => DB.clients.reduce((a, c) => a + (c.changeOrders || []).length + (c.invoices || []).length, 0)")
    if not phone:
        # on a job: the job's client and the job
        await pg.evaluate("() => { setCurrent('p206'); view = 'dash'; render(); }"); await pg.wait_for_timeout(250)
        await new_menu(pg, 'co')
        s = await pg.evaluate(CO_STATE)
        c.ok(s and s['client'] == 'cl206' and s['project'] == 'p206', f'6 {w}: New Change Order on 206 Lenox\'s page defaults to {s and (s["clientText"], s["project"])}, want 206 Lenox LLC on 206 Lenox')
        await close(pg)
        # on another client's page (the last job opened was 121 State Street): that client
        await pg.evaluate("() => { setCurrent('p121'); view = 'clients'; clientOpen = 'cl45'; clientTab = 'fin'; docOpen = null; render(); }"); await pg.wait_for_timeout(250)
        await new_menu(pg, 'co')
        s = await pg.evaluate(CO_STATE)
        c.ok(s and s['client'] == 'cl45', f'6 {w}: New Change Order on the Rivera family\'s page defaults to {s and s["clientText"]}, want the Rivera family')
        await close(pg)
        # on Home, after looking at 206 Lenox: ask
        await pg.evaluate("() => { setCurrent('p206'); view = 'home'; render(); }"); await pg.wait_for_timeout(250)
        await new_menu(pg, 'co')
        s = await pg.evaluate(CO_STATE)
        c.ok(s and s['client'] == '' and s['waits'], f'6 {w}: New Change Order from Home asks for the client: {s}')
        if s and s['client'] == '':
            await pg.select_option('#mbm [data-f="clientId"]', 'cl140'); await pg.wait_for_timeout(250)
            s2 = await pg.evaluate(CO_STATE)
            c.ok(s2['project'] == 'p140', f'6 {w}: choosing the Jessop family fills their job: {s2}')
        await close(pg)
        # the same class: New Invoice and New Estimate from Home ask instead of making one for the last job's client
        for key, label in (('invoice', 'New Invoice'), ('estimate', 'New Estimate')):
            await pg.evaluate("() => { setCurrent('p206'); view = 'home'; render(); }"); await pg.wait_for_timeout(200)
            await new_menu(pg, key)
            s = await pg.evaluate(CO_STATE)
            made = await pg.evaluate("() => DB.clients.reduce((a, c) => a + (c.changeOrders || []).length + (c.invoices || []).length, 0)")
            c.ok(s and s['client'] == '' and made == n0, f'6 {w}: {label} from Home asks for the client (sheet {s}, documents {n0} -> {made})')
            await close(pg)
        # on a job, New Invoice goes straight to that job's client
        await pg.evaluate("() => { setCurrent('p206'); view = 'costs'; render(); }"); await pg.wait_for_timeout(200)
        await new_menu(pg, 'invoice')
        inv = await pg.evaluate("() => docOpen && docOpen.kind === 'invoice' ? (DB.clients.find(c => (c.invoices || []).some(d => d.id === docOpen.id)) || {}).id : null")
        c.ok(inv == 'cl206', f'6 {w}: New Invoice on 206 Lenox\'s costs page is made for {inv}, want cl206')
        await close(pg)
    # Billing with no client picked (desktop and phone): ask; with a client picked: that client
    await pg.evaluate("() => { setCurrent('p206'); billClient = ''; billTab = 'co'; docOpen = null; view = 'billing'; render(); }"); await pg.wait_for_timeout(300)
    if await pg.locator('#bill-newco').count():
        await pg.click('#bill-newco'); await pg.wait_for_timeout(400)
        s = await pg.evaluate(CO_STATE)
        c.ok(s and s['client'] == '' and s['project'] in ('', None) and s['waits'], f'6 {w}: Billing\'s New Change Order with no client picked asks: {s}')
        await close(pg)
        await pg.evaluate("() => { billClient = 'cl45'; render(); }"); await pg.wait_for_timeout(300)
        await pg.click('#bill-newco'); await pg.wait_for_timeout(400)
        s = await pg.evaluate(CO_STATE)
        c.ok(s and s['client'] == 'cl45', f'6 {w}: Billing\'s New Change Order with the Rivera family picked defaults to {s and s["clientText"]}')
        await close(pg)
        await pg.evaluate("() => { billClient = ''; }")
    else:
        c.ok(False, f'6 {w}: Billing shows New Change Order')
    # the client's page on the phone (the PM in the client's kitchen): that client, even after another job was open
    await pg.evaluate("() => { setCurrent('p121'); view = 'clients'; clientOpen = 'cl206'; clientTab = 'fin'; finTab = 'co'; docOpen = null; render(); }"); await pg.wait_for_timeout(300)
    await pg.locator("section.view.on [data-newdoc^='co']").first.click(); await pg.wait_for_timeout(400)
    s = await pg.evaluate(CO_STATE)
    c.ok(s and s['client'] == 'cl206' and s['project'] == 'p206', f'6 {w}: New Change Order on 206 Lenox LLC\'s page defaults to {s and (s["clientText"], s["project"])}')
    await close(pg)

PM_MAIN = [('home', 'Home'), ('mapprove', 'Approvals'), ('ovjobs', 'Projects'), ('tkall', 'Tasks'), ('field', 'Field')]

async def finding7(c, pg):
    await sign_in(pg, 'u_alan'); await go(pg, 'home'); await pg.wait_for_timeout(250)
    bar = await pg.evaluate("""() => { const tb = document.getElementById('mtabs'); if (!tb) return null;
      return { sw: tb.scrollWidth, cw: tb.clientWidth, doc: document.documentElement.scrollWidth,
        tabs: [...tb.querySelectorAll('button')].map(b => { const r = b.getBoundingClientRect(), s = b.querySelector('span');
          return { v: b.dataset.mv, label: s ? s.innerText.trim() : '', w: Math.round(r.width), h: Math.round(r.height), clip: s ? s.scrollWidth > s.clientWidth + 1 : false, right: Math.round(r.right) }; }) }; }""")
    c.ok(bar is not None, '7: the PM has a bottom bar at 390px')
    if not bar: return
    vs = [t['v'] for t in bar['tabs']]
    for v, label in PM_MAIN:
        c.ok(v in vs, f'7: {label} is on the PM\'s bottom bar, not under More: {vs}')
    c.ok('__more' in vs, f'7: More is still on the bar for the rest of his pages: {vs}')
    c.ok(all(t['h'] >= 44 for t in bar['tabs']), f'7: every tab is at least 44px tall: {[(t["label"], t["h"]) for t in bar["tabs"]]}')
    c.ok(all(t['w'] >= 56 and not t['clip'] for t in bar['tabs']), f'7: every tab is at least 56px wide and shows its whole label: {[(t["label"], t["w"], t["clip"]) for t in bar["tabs"]]}')
    c.ok(bar['sw'] <= bar['cw'] + 1 and bar['doc'] <= 390 and max(t['right'] for t in bar['tabs']) <= 390, f'7: the bar fits 390px ({bar["sw"]}/{bar["cw"]}, page {bar["doc"]})')
    for v, label in PM_MAIN:
        if v not in vs: continue
        await pg.click(f'#mtabs button[data-mv="{v}"]'); await pg.wait_for_timeout(300)
        now = await pg.evaluate("() => ({ view, on: (document.querySelector('#mtabs button.on') || {}).dataset ? document.querySelector('#mtabs button.on').dataset.mv : '' })")
        c.ok(now['view'] == v and now['on'] == v, f'7: the {label} tab opens {v} and is lit: {now}')

async def finding8(c, pg, phone):
    w = 'phone' if phone else 'desktop'
    await sign_in(pg, 'u_klein')
    docs = await pg.evaluate("""() => { const c = clientUserOf(); return { inv: (c.invoices || []).filter(d => !['draft', 'void'].includes(d.status)).map(d => d.id),
      co: (c.changeOrders || []).filter(d => !['draft', 'void'].includes(d.status)).map(d => d.id) }; }""")
    for v in ('client', 'clacct'):
        await go(pg, v); await pg.wait_for_timeout(300)
        btns = await pg.evaluate("() => [...document.querySelectorAll('.view.on [data-pview]')].filter(b => b.getClientRects().length).map(b => b.dataset.pview)")
        if v == 'clacct':
            want = [f'invoice:{i}' for i in docs['inv']] + [f'co:{i}' for i in docs['co']]
            c.ok(sorted(set(btns)) == sorted(want), f'8 {w}: Account offers View on every invoice and change order: {btns} vs {want}')
        else:
            c.ok(len(btns) >= 2, f'8 {w}: the Overview has View on what waits on the client: {btns}')
        for pv in btns:
            await go(pg, v); await pg.wait_for_timeout(200)
            await pg.locator(f'.view.on [data-pview="{pv}"]').first.click(); await pg.wait_for_timeout(400)
            m = await pg.evaluate("() => { const m = document.getElementById('mbm'); return m ? m.innerText.replace(/\\s+/g, ' ') : ''; }")
            k, i = pv.split(':')
            num = await pg.evaluate("([k, i]) => { const c = clientUserOf(), d = findDoc(c, k, i); return d ? d.number : ''; }", [k, i])
            c.ok(num and num in m and 'Total' in m, f'8 {w}: View on {pv} ({v}) opens {num}: {m[:80]!r}')
            await close(pg)

async def run(phone):
    c = Checks()
    async with async_playwright() as p:
        b, pg, errs = await open_app(p, phone)
        await finding6(c, pg, phone)
        if phone: await finding7(c, pg)
        await finding8(c, pg, phone)
        c.ok(not errs, f'page errors: {errs[:3]}')
        await b.close()
    return c

async def main():
    fails = 0
    for phone in (True, False):
        c = await run(phone)
        print('phone 390' if phone else 'desktop', end=': ')
        fails += c.done()
    sys.exit(1 if fails else 0)

asyncio.run(main())
