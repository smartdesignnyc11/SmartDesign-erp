"""Shared Playwright helpers. Every suite opens the build next to it (dist/), never a hardcoded path.
The app's day is pinned to 2026-09-03 (today()); seeded demo data loads on first boot."""
import os, asyncio, json
from playwright.async_api import async_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = 'file://' + os.path.join(ROOT, 'dist', 'smartdesigns_projects.html')
USERS = ['u_owner', 'u_alan', 'u_chen', 'u_angel', 'u_alberto', 'u_alex', 'u_klein', 'u_sarah', 'u_billing', 'u_controller']
DESKTOP = {'width': 1440, 'height': 900}
PHONE = {'width': 390, 'height': 844}

async def open_app(p, phone=False):
    b = await p.chromium.launch()
    ctx = await b.new_context(viewport=PHONE if phone else DESKTOP, is_mobile=phone, has_touch=phone)
    pg = await ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('console', lambda m: m.type == 'error' and 'fonts.g' not in m.text and 'ERR_' not in m.text and errs.append('console: ' + m.text))
    await pg.goto(URL)
    await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
    return b, pg, errs

async def sign_in(pg, uid):
    await pg.evaluate("u => { signIn(u); render(); }", uid)
    await pg.wait_for_timeout(150)

async def go(pg, view):
    await pg.evaluate("v => { view = v; render(); }", view)
    await pg.wait_for_timeout(120)

class Checks:
    def __init__(self): self.n = 0; self.fail = []
    def ok(self, cond, msg):
        self.n += 1
        if not cond: self.fail.append(msg); print('FAIL', msg)
    def done(self):
        print('ALL PASS' if not self.fail else f'{len(self.fail)} FAILED', f'({self.n} checks)')
        return 0 if not self.fail else 1
