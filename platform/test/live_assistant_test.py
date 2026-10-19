"""The executive assistant's run, live (QA workspace): the owner asks for a briefing now (/api/assistant), the server
reads their day, one model call writes the briefing and drafts into their private inbox, and the app files it as the
day's briefing (paIngestServer). Costs one assistant-tier call. QA accounts as in live_db_test.py (SD_QA_USERS).
Run: SD_QA_USERS=… python3 test/live_assistant_test.py"""
import asyncio, json, os, sys
from playwright.async_api import async_playwright
SITE = os.environ.get('SDP_SITE', 'https://smartdesigns-erp.netlify.app')
QA = json.load(open(os.environ.get('SD_QA_USERS') or sys.exit('set SD_QA_USERS')))
n = 0; fails = []
def ok(c, msg):
    global n; n += 1
    print(('ok  ' if c else 'FAIL'), msg)
    if not c: fails.append(msg)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={'width': 1440, 'height': 900}); pg = await ctx.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(SITE); await pg.wait_for_selector('#cl-email', timeout=60000)
        await pg.fill('#cl-email', QA['owner']['email']); await pg.fill('#cl-pass', QA['owner']['password']); await pg.click('#cl-form button[type=submit]')
        await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=120000)
        before = await pg.evaluate("(paInit().briefs || []).length")
        r = await pg.evaluate("fetch('/api/assistant', {method: 'POST'}).then(r => r.json().then(j => ({s: r.status, j})))")
        ok(r['s'] == 200 and r['j'].get('started'), f'the owner asks for a briefing now: {r}')
        got = None
        for _ in range(36):                      # up to 3 minutes: the run, then the next poll files the inbox
            await pg.wait_for_timeout(5000)
            try: await pg.evaluate("Cloud.pollOnce()")
            except Exception: pass
            got = await pg.evaluate(f"(() => {{ const B = paInit().briefs || []; return B.length > {before} ? B[0] : null; }})()")
            if got: break
        ok(bool(got), 'the run came back and was filed as a briefing')
        if got:
            s = json.dumps(got)
            ok(len(str(got.get('headline') or (got.get('brief') or {}).get('headline') or '')) > 20, f"it has a written headline: {str(got.get('headline') or (got.get('brief') or {}).get('headline'))[:160]!r}")
            ok('<' not in s and '>' not in s, 'no markup in what the server wrote')
            sent = await pg.evaluate("(DB.outbox || []).filter(x => x.fromServerRun && x.status !== 'draft').length")
            ok(sent == 0, f'nothing from the run was sent ({sent})')
        ok(not errs, f'no page errors {errs[:3]}')
        await b.close()
    print('ALL PASS' if not fails else f'{len(fails)} FAILED', f'({n} checks)')
    sys.exit(1 if fails else 0)
asyncio.run(main())
