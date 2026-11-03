"""Shared reading of the 11-03 menu pages (docs/mockups/QUESTIONS.md; purchasing and design specs): a page opens on
Needs You (rows whose next tap is the person's, with a count equal to its rows), then Waiting on Someone Else (each row
names who, no number), then the rest one tap down; no tab rows; job, vendor, trade and room are filters.
The markup the checks read (src/purchasing.js and src/design.js draw it):
  [data-pupage="<view>"]                      the page
  [data-pusec="mine|others|route|later|..."]  a section; its heading's .n is the section's count, when it has one
  [data-purow="<id>"]                         a row (a card on the phone); .pu-who names who it waits on
Used by purchasing_test.py (sections pages, picks, receive, leaks, clock) and design_test.py."""
from harness import *
from menu_order_test import tap, open_menu, ensure_open, MENU_JS

PAGE_JS = r"""() => {
  const v = document.querySelector('.view.on'); if (!v) return null;
  const vis = e => !!e && e.getClientRects().length > 0 && !e.closest('[hidden]');
  const txt = e => (e ? e.innerText : '').replace(/\s+/g, ' ').trim();
  const page = v.querySelector('[data-pupage]');
  const sec = k => [...v.querySelectorAll(`[data-pusec="${k}"]`)].find(vis) || null;
  const rows = k => { const s = sec(k); return s ? [...s.querySelectorAll('[data-purow]')].filter(vis).map(r => ({ id: r.dataset.purow, t: txt(r),
      who: txt(r.querySelector('.pu-who')), nums: [...r.querySelectorAll('.n')].filter(vis).length, blue: [...r.querySelectorAll('.btn.primary')].filter(vis).length })) : null; };
  const hn = k => { const s = sec(k); const n = s && [...s.querySelectorAll('.pu-sh .n')].find(vis); return n ? (/^\d+$/.test(n.textContent.trim()) ? +n.textContent.trim() : n.textContent.trim()) : null; };
  const secs = [...v.querySelectorAll('[data-pusec]')].filter(vis).map(s => s.dataset.pusec);
  return { page: page ? page.dataset.pupage : '', h2: txt([...v.querySelectorAll('h2')].find(vis)), secs,
    tabs: [...v.querySelectorAll('[role=tablist], .ctabs, .bb-tabs, .tabs')].filter(vis).length,
    mineN: hn('mine'), mine: rows('mine'), othersN: hn('others'), others: rows('others'), routeN: hn('route'), route: rows('route'),
    later: rows('later'), blues: [...v.querySelectorAll('.btn.primary')].filter(vis).map(b => txt(b)),
    sw: document.documentElement.scrollWidth, w: innerWidth, text: txt(v) };
}"""


async def page(pg):
    return await pg.evaluate(PAGE_JS)


async def menu(pg):
    return await pg.evaluate(MENU_JS)


async def kids(pg, phone, gid):
    """the entries a group lists, as the person sees them once its name is tapped: [(label, view, number)]"""
    if not await ensure_open(pg, gid, phone): return []
    return [(e['label'], e['v'], e['n']) for e in await menu(pg) if e['kind'] == 'kid' and e['grp'] == gid and e['vis']]


async def open_entry(pg, phone, gid, label):
    """open a page from the menu as the person: the menu (phone), the group by its name, then the entry by its words"""
    if not await ensure_open(pg, gid, phone): return False
    loc = pg.locator(f'#nav-groups [data-mngr="{gid}"] button[data-v]').filter(has_text=label).first
    if not await loc.count(): return False
    await tap(pg, loc, phone)
    await pg.wait_for_timeout(350)
    return True


async def groups(pg, phone):
    await open_menu(pg, phone)
    return [e['label'] for e in await menu(pg) if e['kind'] == 'head' and e['vis']]
