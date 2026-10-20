"""A toast's Open link pressed while an editor is open (BACKLOG gap, 2026-10-20). The editor closes before the record
opens; if something was typed in it, the person is asked first (Keep Editing is the safe, blue step and brings the
editor back as it was; Leave Without Saving opens the record). Desktop and phone, the side drawer and a sheet.
Run: python3 toast_leave_test.py"""
import asyncio
from harness import async_playwright, open_app, sign_in, Checks

TOAST = "() => { window.__opened = window.__opened || 0; toast('Saved PO-1', () => { window.__opened++; }); }"
async def press_open(pg):
    await pg.evaluate(TOAST); await pg.wait_for_timeout(150)
    await pg.click('#toast .toast-open'); await pg.wait_for_timeout(300)

async def main():
    c = Checks()
    async with async_playwright() as p:
        for phone in (False, True):
            tag = 'phone' if phone else 'desktop'
            b, pg, errs = await open_app(p, phone)
            await sign_in(pg, 'u_owner')
            # the drawer, nothing typed: it closes and the record opens
            await pg.evaluate("() => { setView('vendors'); openEditor('vendor', null); }"); await pg.wait_for_timeout(300)
            c.ok(await pg.evaluate("() => document.getElementById('drawer').classList.contains('on')"), f'{tag}: the vendor editor is open')
            await press_open(pg)
            r = await pg.evaluate("() => ({ on: document.getElementById('drawer').classList.contains('on'), opened: window.__opened, ask: !!document.getElementById('mbm') })")
            c.ok(r == {'on': False, 'opened': 1, 'ask': False}, f'{tag}: nothing typed: the editor closes and the record opens, no question ({r})')
            # the drawer, something typed: asked; Keep Editing keeps it
            await pg.evaluate("() => { setView('vendors'); openEditor('vendor', null); }"); await pg.wait_for_timeout(300)
            inp = pg.locator('#drawer input:visible').first
            await inp.fill('Halsey Millwork'); await pg.wait_for_timeout(100)
            await press_open(pg)
            r = await pg.evaluate("() => ({ on: document.getElementById('drawer').classList.contains('on'), opened: window.__opened, ask: (document.querySelector('#mbm h3') || {}).textContent, blue: (document.querySelector('#mbm .btn.primary') || {}).textContent })")
            c.ok(r['ask'] == 'Unsaved Changes' and r['blue'] == 'Keep Editing' and r['opened'] == 1 and r['on'], f'{tag}: typed: asked first, Keep Editing is the blue step, nothing opened yet ({r})')
            await pg.click('#mbm .btn.primary'); await pg.wait_for_timeout(300)
            r = await pg.evaluate("() => ({ on: document.getElementById('drawer').classList.contains('on'), opened: window.__opened, v: [...document.querySelectorAll('#drawer input')].some(i => i.value === 'Halsey Millwork') })")
            c.ok(r == {'on': True, 'opened': 1, 'v': True}, f'{tag}: Keep Editing: the editor stays with what was typed ({r})')
            await press_open(pg)
            await pg.click('#mbm-alt'); await pg.wait_for_timeout(300)
            r = await pg.evaluate("() => ({ on: document.getElementById('drawer').classList.contains('on'), opened: window.__opened })")
            c.ok(r == {'on': False, 'opened': 2}, f'{tag}: Leave Without Saving: the editor closes and the record opens ({r})')
            # a fresh editor starts clean
            await pg.evaluate("() => { setView('vendors'); openEditor('vendor', null); }"); await pg.wait_for_timeout(300)
            await press_open(pg)
            c.ok(await pg.evaluate("() => !document.getElementById('mbm') && window.__opened === 3"), f'{tag}: a new editor is not marked by the last one')
            # a sheet with something typed: held aside and back on Keep Editing
            await pg.evaluate("() => mbModal('New Note', '<div class=\"f\"><input data-f=\"n\" id=\"tl-n\"></div>', { submit: 'Save' })"); await pg.wait_for_timeout(200)
            await pg.fill('#tl-n', 'Call the examiner'); await pg.wait_for_timeout(100)
            await press_open(pg)
            c.ok(await pg.evaluate("() => (document.querySelector('#mbm h3') || {}).textContent === 'Unsaved Changes' && window.__opened === 3"), f'{tag}: a sheet with typing: asked first')
            await pg.click('#mbm .btn.primary'); await pg.wait_for_timeout(400)
            r = await pg.evaluate("() => ({ t: (document.querySelector('#mbm h3') || {}).textContent, v: (document.getElementById('tl-n') || {}).value })")
            c.ok(r == {'t': 'New Note', 'v': 'Call the examiner'}, f'{tag}: Keep Editing brings the sheet back as it was ({r})')
            await pg.evaluate("() => mbCloseModal()")
            c.ok(not errs, f'{tag}: page errors {errs[:2]}')
            await b.close()
    print(f'{len(c.fail)} FAILED ({c.n} checks)' if c.fail else f'ALL PASS ({c.n} checks)')
    raise SystemExit(1 if c.fail else 0)

asyncio.run(main())
