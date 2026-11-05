"""Shared reads for the Your Day, Sales and Clients, and Company and Settings suites (docs/mockups/today, sales,
company SPEC.md). Each read is what the person sees on the screen: the menu's number, a chip's number, the rows under
it, sideways scroll, small buttons. Suites: yourday_test.py, sales_test.py, company_test.py."""
import asyncio

# the menu entry's number (the rail on the desktop; the phone's menu is the same markup, drawn closed)
MENU_N = """v => { const b = [...document.querySelectorAll('#nav-groups button[data-v="' + v + '"]')][0];
  return b ? ((b.querySelector('.n') || {}).textContent || '').trim() : null; }"""

# the menu's entries under a group, by its name (the 11-03 menu: a group opens on its name)
MENU_ITEMS = """g => { const k = document.querySelector('#nav-groups [data-mngr="' + g + '"]');
  return k ? [...k.querySelectorAll('button[data-v]')].map(b => (b.querySelector('.mn-l') || b).textContent.trim()) : null; }"""

# the page on screen: no sideways scroll, every visible button at least 44px tall on the phone
PHONE_FIT = """() => { const v = document.querySelector('.view.on'); if (!v) return {sw: 0, small: []};
  const small = [...v.querySelectorAll('button, a.btn, [role=button]')].filter(b => { const r = b.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && r.height < 43.5 && getComputedStyle(b).visibility !== 'hidden'; })
    .map(b => (b.innerText || b.getAttribute('aria-label') || '').trim().slice(0, 30) + ' ' + Math.round(b.getBoundingClientRect().height));
  return { sw: document.documentElement.scrollWidth, small: small }; }"""

# chips drawn by the lane's pages: [{k, label, n, on}]
CHIPS = """sel => [...document.querySelectorAll(sel)].filter(b => b.getClientRects().length).map(b => ({ k: b.dataset.ydchip || b.dataset.tdytabbtn || '',
  label: (b.querySelector('.l') || b).childNodes[0].textContent.trim(), n: ((b.querySelector('.n') || {}).textContent || '').trim(),
  on: b.classList.contains('on') || b.getAttribute('aria-pressed') === 'true' || b.getAttribute('aria-selected') === 'true' }))"""

VISIBLE_TEXT = "() => (document.querySelector('.view.on') || document.body).innerText"


async def phone_fit(c, pg, who, w=390):
    m = await pg.evaluate(PHONE_FIT)
    c.ok(m['sw'] <= w, f'{who}: scrolls sideways ({m["sw"]}px)')
    c.ok(not m['small'], f'{who}: buttons under 44px: {m["small"][:4]}')


async def settle(pg, ms=150):
    await pg.wait_for_timeout(ms)
