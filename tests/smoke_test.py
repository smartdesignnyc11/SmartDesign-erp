"""Boots every role on desktop and phone, opens every view that role may open, and checks:
no page errors, at most one visible blue primary button, no sideways scroll on phone, no emoji.
This is a floor, not the screen standard: see docs/REVIEW_PROTOCOL.md for the full lint to rebuild."""
import asyncio, re, sys
from harness import *
EMOJI = re.compile('[\U0001F300-\U0001FAFF☀-➿]')
async def main():
    c = Checks()
    async with async_playwright() as p:
        for phone in (False, True):
            b, pg, errs = await open_app(p, phone)
            for u in USERS:
                await sign_in(pg, u)
                views = await pg.evaluate("() => (ROLE_VIEWS[role()] || []).slice()")
                for v in views:
                    del errs[:]
                    try: await go(pg, v)
                    except Exception as e: errs.append(str(e))
                    tag = f"{'phone' if phone else 'desktop'} {u} {v}"
                    c.ok(not errs, f'{tag}: errors {errs[:2]}')
                    r = await pg.evaluate("""() => {
                      const vis = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== 'hidden'; };
                      const prim = [...document.querySelectorAll('.view.on .btn.primary')].filter(vis).length;
                      const over = document.documentElement.scrollWidth - innerWidth;
                      const txt = document.querySelector('.view.on')?.innerText || '';
                      return {prim, over, txt};
                    }""")
                    c.ok(r['prim'] <= 1, f"{tag}: {r['prim']} blue primary buttons")
                    if phone: c.ok(r['over'] <= 2, f"{tag}: scrolls sideways by {r['over']}px")
                    c.ok(not EMOJI.search(r['txt']), f'{tag}: emoji on screen')
            await b.close()
    sys.exit(c.done())
asyncio.run(main())
