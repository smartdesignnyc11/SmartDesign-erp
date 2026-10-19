import asyncio, os, json, time
"""Phone speed, live: a mid-range phone (CPU 4x slower, 1.5 MB/s, 80 ms) opens the hosted app, then reopens it twice.
Prints the time to the first screen and where it went (connect, profile, pull). Run: SD_QA_USERS=… python3 test/live_speed.py"""
import os
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'live_app_test.py')).read().split('async def main():')[0]; exec(src)
async def run(label, first):
    reset_qa()
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        await ctx.add_init_script('''(() => { window.__t = {start: performance.now()}; let C; Object.defineProperty(window, 'Cloud', {configurable: true, get() { return C; }, set(v) {
            C = v; const w = (n) => { const f = v[n]; v[n] = async function () { const a = performance.now(); try { return await f.apply(this, arguments); } finally { window.__t[n] = Math.round(performance.now() - a); } }; };
            ['init', 'profile', 'pullAll', 'pushPending'].forEach(w); } });
          document.addEventListener('DOMContentLoaded', () => window.__t.dcl = Math.round(performance.now())); })()''')
        pg = await ctx.new_page()
        cdp = await ctx.new_cdp_session(pg)
        await cdp.send('Emulation.setCPUThrottlingRate', {'rate': 4})
        await cdp.send('Network.enable')
        await cdp.send('Network.emulateNetworkConditions', {'offline': False, 'latency': 80, 'downloadThroughput': 1.5e6, 'uploadThroughput': 0.75e6})
        t00 = time.time()
        await pg.goto(SITE); await pg.wait_for_selector('#cl-email', timeout=120000)
        await pg.fill('#cl-email', QA['owner']['email']); await pg.fill('#cl-pass', QA['owner']['password']); await pg.click('#cl-form button[type=submit]')
        await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=400000)
        print(label, f'first open, including download and the first upload: {time.time() - t00:.1f}s')
        await pg.wait_for_timeout(8000)
        for k in ('reopen 1', 'reopen 2'):
            t0 = time.time(); await pg.reload(); await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=240000)
            t = time.time() - t0
            nav = await pg.evaluate("JSON.stringify((() => { const n = performance.getEntriesByType('navigation')[0]; return {transfer: n.transferSize, dcl: Math.round(n.domContentLoadedEventEnd), sw: !!navigator.serviceWorker.controller}; })())")
            print(label, k, f'{t:.1f}s to the first screen', nav, await pg.evaluate("JSON.stringify(Object.assign({booted: Math.round(performance.now())}, window.__t))"))
        await b.close()
asyncio.run(run('mid-range phone', True))
