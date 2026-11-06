"""signin_boot_test: every role signs in to the hosted copy through the real sign-in screen, as every new device and
every live check does, and the app boots with no page error, in the demo workspace and in the team's own.

Why it exists (2026-11-06): the integ15 release broke on the hosted copy only. The hosted page waits at its sign-in
screen with no records (DB is null until the server copy loads), and P3's read-only click guard (src/puorders.js
puReadOnly, a page-wide capture listener) asked role() -> currentUser() -> DB.users on the Sign In tap:
"Cannot read properties of null (reading 'users')" on every hosted sign-in. Every local suite opens the file:// demo or
a hosted mock that is already signed in, so DB always existed before the first tap, and none could see it.

The hosted page (dist/ with platform/public/cloud.js in its head) runs over tests/hosted_mock.py. On the sign-in screen
each device is tapped, typed into, keyed, scrolled, rotated, hidden and shown, taken offline and back, before it signs in.
People and records are invented. Run: python3 signin_boot_test.py"""
import asyncio, os, sys
from harness import *
from hosted_mock import Server, hosted_page, open_hosted

# demo workspace: the app's own people, so each sign-in is that seat (the QA accounts link the same way)
DEMO = [('owner', 'u_owner', False), ('owner', 'u_owner', True), ('pm', 'u_alan', False), ('coord', 'u_chen', True),
        ('coord', 'u_chen', False), ('foreman', 'u_angel', True), ('crew', 'u_alberto', True), ('driver', 'u_alex', True),
        ('designer', 'u_sarah', False), ('billing', 'u_billing', False), ('controller', 'u_controller', False)]
# the team's own workspace: invented people, no demo seeds (sdSeedsOff), added from their profile at sign-in
TEAM = [('owner', False), ('owner', True), ('coord', True), ('billing', False), ('controller', False), ('foreman', True)]


async def at_signin(pg):
    """What a person and a phone do on the sign-in screen before the Sign In tap: each fires the page-wide listeners
    while there are no records."""
    for sel in ('#signin .box', '#cl-email', '#cl-pass', '#signin .brand', 'body'):
        if await pg.locator(sel).count():
            await pg.locator(sel).first.click(force=True)
    await pg.locator('#cl-email').press('Tab')
    await pg.keyboard.press('Escape'); await pg.keyboard.press('Enter')
    await pg.evaluate("""() => {
      for (const st of ['hidden', 'visible']) {
        Object.defineProperty(document, 'visibilityState', {configurable: true, get: () => st});
        Object.defineProperty(document, 'hidden', {configurable: true, get: () => st === 'hidden'});
        document.dispatchEvent(new Event('visibilitychange'));
      }
      for (const ev of ['online', 'offline', 'online', 'focus', 'blur', 'pageshow', 'resize', 'scroll', 'hashchange', 'popstate']) window.dispatchEvent(new Event(ev));
      const b = document.querySelector('#signin .box') || document.body;
      for (const ev of ['pointerdown', 'pointerup', 'touchstart', 'touchend', 'mousedown', 'mouseup', 'input', 'change', 'keydown', 'keyup', 'focusin', 'paste']) b.dispatchEvent(new Event(ev, {bubbles: true}));
    }""")
    await pg.wait_for_timeout(300)


async def main():
    c = Checks()
    S = Server()
    S.ws['sd-team'] = {'kind': 'team', 'name': 'SmartDesign'}
    for i, (r, appu, _) in enumerate(DEMO):
        S.person(f'auth-d-{appu}', f'{appu.replace("u_", "")}@demo.example.com', appu.replace('u_', '').title(), r, 'demo-ws', app_user_id=appu)
    for r, _ in TEAM:
        S.person(f'auth-t-{r}', f'{r}@team.example.com', f'Team {r.title()}', r, 'sd-team')
    url = hosted_page()
    async with async_playwright() as p:
        b = await p.chromium.launch()
        # the first office sign-in on an empty demo workspace seeds and uploads, as the live QA workspace does after its reset
        for ws, people in (('demo', [(f'auth-d-{u}', r, ph) for r, u, ph in DEMO]), ('team', [(f'auth-t-{r}', r, ph) for r, ph in TEAM])):
            for uid, r, phone in people:
                dev = f'{ws} {r} on the {"phone" if phone else "desktop"}'
                try:
                    ctx, pg, errs = await open_hosted(b, S, url, uid, phone=phone, signed_out=True, at_signin=at_signin)
                except Exception as e:
                    c.ok(False, f'{dev}: signed in through the screen and booted ({str(e)[:160]})')
                    continue
                got = await pg.evaluate("() => ({role: role(), me: (currentUser() || {}).id || '', ws: (window.__sdWs || {}).kind || '', off: sdSeedsOff()})")
                c.ok(got['role'] == r and got['me'] and got['ws'] == ws, f'{dev}: signed in through the screen and booted as that seat: {got}')
                await go(pg, 'home')
                await pg.wait_for_timeout(400)
                c.ok(not errs, f'{dev}: no page errors from the sign-in screen to Home: {errs[:3]}')
                await ctx.close()
        await b.close()
    return c.done()

sys.exit(asyncio.run(main()))
