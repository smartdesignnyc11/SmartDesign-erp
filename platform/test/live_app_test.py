"""The hosted app, as two people on two devices (BACKLOG §5 item 1): the owner at a desk and the foreman on a phone sign
in through the real sign-in screen, the first upload fills the QA workspace, the phone never holds money, and edits made
on each device reach the other without overwriting anything. QA accounts as in live_db_test.py (SD_QA_USERS).
Run: SD_QA_USERS=… python3 test/live_app_test.py"""
import asyncio, json, os, sys
from playwright.async_api import async_playwright
SITE = os.environ.get('SDP_SITE', 'https://smartdesigns-erp.netlify.app')
QA = json.load(open(os.environ.get('SD_QA_USERS') or sys.exit('set SD_QA_USERS')))
n = 0; fails = []
def ok(c, msg):
    global n; n += 1
    print(('ok  ' if c else 'FAIL'), msg)
    if not c: fails.append(msg)

async def person(b, who, phone):
    vp = {'width': 390, 'height': 844} if phone else {'width': 1440, 'height': 900}
    ctx = await b.new_context(viewport=vp, is_mobile=phone, has_touch=phone)
    pg = await ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto(SITE)
    await pg.wait_for_selector('#cl-email', timeout=60000)
    await pg.fill('#cl-email', QA[who]['email']); await pg.fill('#cl-pass', QA[who]['password'])
    await pg.click('#cl-form button[type=submit]')
    await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=120000)
    await pg.wait_for_timeout(1500)
    return pg, errs

async def before_sign_in(b):
    """The sign-in screen waits with no records loaded. A phone switching apps, rotating, losing signal or going
    back fires handlers then; none may crash (Alan's iPhone showed a startup error from the Google sync handler)."""
    ctx = await b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
    pg = await ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto(SITE); await pg.wait_for_selector('#cl-email', timeout=60000)
    for state in ['hidden', 'visible']:
        await pg.evaluate(f"Object.defineProperty(document,'visibilityState',{{configurable:true,get:()=>'{state}'}}); Object.defineProperty(document,'hidden',{{configurable:true,get:()=>{'true' if state == 'hidden' else 'false'}}}); document.dispatchEvent(new Event('visibilitychange'))")
    for ev in ['online', 'offline', 'focus', 'pageshow', 'pagehide']: await pg.evaluate(f"window.dispatchEvent(new Event('{ev}'))")
    await pg.set_viewport_size({'width': 844, 'height': 390}); await pg.wait_for_timeout(600); await pg.set_viewport_size({'width': 390, 'height': 844})
    await pg.evaluate("history.pushState({rx:{}},''); history.back()")
    await pg.wait_for_timeout(3000)
    await ctx.close()
    return errs

async def until(pg, js, secs=40):
    for _ in range(secs * 2):
        if await pg.evaluate(js): return True
        await pg.wait_for_timeout(500)
    return False

def reset_qa():
    """Empty the QA workspace (never the firm's) through the Supabase management API, so each run starts clean."""
    import urllib.request as u, json as j
    ref = os.environ.get('SDP_SUPABASE_REF', 'eenpabyrmiltfqvzirhw')
    q = "delete from public.collections where workspace_id = 'qa'"
    u.urlopen(u.Request(f'https://api.supabase.com/v1/projects/{ref}/database/query', method='POST', data=j.dumps({'query': q}).encode(), headers={'content-type': 'application/json'}))

async def main():
    reset_qa()
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pre = await before_sign_in(b)
        ok(not pre, f'the sign-in screen survives switching apps, rotating, signal changes and back: {pre[:3]}')
        A, ea = await person(b, 'owner', False)
        ok(await A.evaluate("Cloud.user() && DB.role === 'owner'"), 'owner signed in through the sign-in screen')
        ok(await until(A, "Cloud.state.err === '' && !Cloud.state.syncing && Object.keys(Cloud.shards(DB)).length > 20"), 'owner: synced')
        await A.evaluate("Cloud.push(DB)")
        await A.wait_for_timeout(3000)
        nrows = await A.evaluate("Cloud.pullAll().then(d => d ? d.projects.length : 0)")
        ok(nrows > 0, f'the first upload put the jobs on the server ({nrows})')
        pid = await A.evaluate("DB.projects.find(p => !p.id.startsWith('qa')).id")
        money_key = await A.evaluate(f"(() => {{ const p = DB.projects.find(x => x.id === '{pid}'); return ['budget','contract','price','total','amount'].find(k => k in p) || ''; }})()")

        F, ef = await person(b, 'foreman', True)
        ok(await F.evaluate("DB.role === 'foreman'"), 'foreman signed in on the phone')
        ok(await F.evaluate("(DB.projects||[]).length > 0"), 'the phone has the jobs')
        held = await F.evaluate("['txns','payroll','cards','investors'].filter(k => DB[k] && (Array.isArray(DB[k]) ? DB[k].length : Object.keys(DB[k]).length)).concat(((DB.gl||{}).journals||[]).length ? ['gl journals'] : [])")
        ok(held == [], f'the phone holds no books, bank, payroll or investors: {held}')
        ok(await F.evaluate("(DB.bills||[]).length === 0"), 'the phone holds no bills')
        if money_key:
            got = await F.evaluate(f"DB.projects.map(p => p['{money_key}']).filter(v => v != null && JSON.stringify(v).match(/\\d/))")
            ok(got == [], f'the phone holds no "{money_key}" figure on any job: {str(got)[:120]}')
        ok(await F.evaluate("innerWidth === 390 && document.documentElement.scrollWidth <= 391"), 'the phone does not scroll sideways')

        # office edit reaches the phone
        await A.evaluate(f"(() => {{ const p = DB.projects.find(x => x.id === '{pid}'); p.qaStamp = 'office-1'; saveNow ? saveNow() : save(); }})()")
        ok(await until(F, f"DB.projects.find(x => x.id === '{pid}').qaStamp === 'office-1'", 45), 'the office edit reached the phone (change feed or 30 s poll)')

        # field edit reaches the office; the money on that job is untouched
        before = await A.evaluate(f"JSON.stringify(DB.projects.find(x => x.id === '{pid}')['{money_key}'])") if money_key else None
        await F.evaluate(f"(() => {{ const p = DB.projects.find(x => x.id === '{pid}'); (p.qaNotes = p.qaNotes || []).push({{id: 'n1', note: 'rough-in inspected'}}); saveNow ? saveNow() : save(); }})()")
        ok(await until(A, f"(DB.projects.find(x => x.id === '{pid}').qaNotes||[]).some(n => n.id === 'n1')", 45), 'the field note reached the office')
        if money_key:
            after = await A.evaluate(f"JSON.stringify(DB.projects.find(x => x.id === '{pid}')['{money_key}'])")
            ok(before == after and after not in (None, 'null'), f'the job\'s {money_key} survived the field save ({after})')

        # both edit the same job at once, different fields: both edits stand on both devices
        await asyncio.gather(
            A.evaluate(f"(() => {{ const p = DB.projects.find(x => x.id === '{pid}'); p.qaStamp = 'office-2'; saveNow ? saveNow() : save(); }})()"),
            F.evaluate(f"(() => {{ const p = DB.projects.find(x => x.id === '{pid}'); p.qaNotes.push({{id: 'n2', note: 'insulation in'}}); saveNow ? saveNow() : save(); }})()"))
        both = f"(() => {{ const p = DB.projects.find(x => x.id === '{pid}'); return p.qaStamp === 'office-2' && (p.qaNotes||[]).some(n => n.id === 'n2'); }})()"
        ok(await until(A, both, 60), 'simultaneous edits: the office has both')
        who = await A.evaluate("[paMe().id, DB.role, DB.deviceUser].join()"), await F.evaluate("[paMe().id, DB.role, DB.deviceUser].join()")
        ok(who[0].startswith('u_owner,owner') and who[1].startswith('u_angel,foreman'), f'each device is still its own person after the other saves: {who}')
        ok(await until(F, both, 60), 'simultaneous edits: the phone has both')


        # personal mail: the owner connects the Demo Workspace (invented mail through the real Google code path)
        await A.evaluate("gcDemoConnect()")   # connecting starts the first sync itself
        await until(A, "!gsRunning && (DB.comms || []).some(c => c.owner === paMe().id && c.source === 'demo')", 60)
        n_mail = await A.evaluate("""(() => { saveNow ? saveNow() : save();
            return (DB.comms || []).filter(c => c.owner === paMe().id && (c.source === 'demo' || c.source === 'google')).length; })()""")
        ok(n_mail > 0, f'the owner\'s connected mailbox synced ({n_mail} messages)')
        ok(await until(A, "Cloud.state.err === '' && !Cloud.state.syncing && Object.keys(Cloud.shards(DB)).some(k => k.startsWith('own:'))", 40), 'the owner\'s own rows were written')
        await A.wait_for_timeout(2000); await A.evaluate("Cloud.push(DB)"); await A.wait_for_timeout(3000)
        srv = await A.evaluate("""(async () => { const sh = await Cloud.pullOne('comms'); const own = await Cloud.pullOne('own:' + Cloud.user().id + ':comms');
            return {shared: (sh && sh.data || []).filter(c => c.source === 'demo' || c.source === 'google').length, own: own ? own.data.length : -1,
                    localDemo: (DB.comms || []).filter(c => c.source === 'demo').length, localOwn: (Cloud.shards(DB)['own:' + Cloud.user().id + ':comms'] || []).length,
                    person: window.__cloudPerson, me: paMe().id, owners: [...new Set((DB.comms || []).filter(c => c.source === 'demo').map(c => c.owner))]}; })()""")
        ok(srv['shared'] == 0 and srv['own'] == n_mail, f'on the server the mail is only in the owner\'s own row: {srv}')
        await F.evaluate("Cloud.pollOnce()"); await F.wait_for_timeout(3000)
        leak = await F.evaluate("(DB.comms || []).filter(c => c.source === 'demo' || c.source === 'google').length + ((DB.calendar||{}).external||[]).filter(e => e.source === 'demo' || e.source === 'google').length + (DB.gdrive||[]).length")
        ok(leak == 0, f'the foreman\'s phone holds none of the owner\'s mail, events or files ({leak})')
        A2, ea2 = await person(b, 'owner', True)
        back = await A2.evaluate("(DB.comms || []).filter(c => c.owner === paMe().id && (c.source === 'demo' || c.source === 'google')).length")
        ok(back == n_mail, f'the owner\'s mail comes back on his other device ({back} of {n_mail})')
        ok(not ea2, f'owner, second device: no page errors {ea2[:3]}')
        # the AI door from the page itself carries the session
        r = await F.evaluate("fetch('/api/ai', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({tier:'small', max_tokens: 20, messages:[{role:'user', content:'Reply with the word ready.'}]})}).then(r => r.status)")
        ok(r == 200, f'the page reaches /api/ai signed in and is answered (status {r})')

        ok(not ea, f'owner: no page errors {ea[:3]}')
        ok(not ef, f'foreman: no page errors {ef[:3]}')
        await b.close()
    print('ALL PASS' if not fails else f'{len(fails)} FAILED', f'({n} checks)')
    sys.exit(1 if fails else 0)
asyncio.run(main())
