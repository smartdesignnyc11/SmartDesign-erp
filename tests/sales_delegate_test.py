"""Delegated sales tasks (BACKLOG §1.36, CoS 11-05).

A sales task the owner or the PM hands to the coordinator or billing is theirs to act on: SAL-1 (send the site-visit
recap) handed to Chen reads Draft on his Pipeline row and on the deal's page, and opens the task; SAL-11 (call Daniel
Okafor back, the lead's own next step) handed to Billing reads Call. Before it is handed over, neither may act on it
(the 11-05 rule: moving a deal is the owner's and the PM's). A task the coordinator hands to herself is not delegation.
The deal itself stays the owner's and the PM's: no Open the Full Record, and Set Up the Job is refused. The lead's next
step takes the person it is handed to (tkSetOwner wrote the name on the lead and the task list kept reading the deal's
owner). Desktop and the 390px phone; no sideways scroll.
"""
import asyncio, sys
from harness import *

SETUP = r"""() => { const S = tkAll({ open: true }).filter(x => x.kind === 'hub' || x.kind === 'lead');
  S.forEach(x => { try { x.code = (tdyRec(x) || {}).code; } catch (e) {} });
  const k = c => { const x = S.find(y => y.code === c); return x ? t2Key(x) : ''; };
  window.__k = { 'SAL-1': k('SAL-1'), 'SAL-11': k('SAL-11') }; return window.__k; }"""

PIPE = r"""async (who) => { const sl = ms => new Promise(r => setTimeout(r, ms)), vis = e => !!e && e.getClientRects().length > 0;
  view = 'ovsales'; slChip = 'need'; render(); await sl(250);
  const row = [...document.querySelectorAll('.view.on .yd-row')].filter(vis).find(e => e.innerText.includes(who));
  const b = row && [...row.querySelectorAll('button')].filter(vis)[0];
  return { row: !!row, btn: b ? b.innerText.trim() : '', sw: document.scrollingElement.scrollWidth, w: innerWidth }; }"""

DEAL = r"""async (name) => { const sl = ms => new Promise(r => setTimeout(r, ms)), vis = e => !!e && e.getClientRects().length > 0;
  const l = DB.leads.find(x => x.name === name); slOpenDeal(l.id); await sl(250);
  const B = [...document.querySelectorAll('.view.on button')].filter(vis).map(b => b.innerText.trim() + (b.classList.contains('primary') ? '*' : ''));
  return { btns: B, sw: document.scrollingElement.scrollWidth, w: innerWidth }; }"""


async def main():
    c = Checks()
    async with async_playwright() as p:
        for phone in (False, True):
            dev = 'phone' if phone else 'desktop'
            b, pg, errs = await open_app(p, phone)
            await sign_in(pg, 'u_owner')
            K = await pg.evaluate(SETUP)
            c.ok(K['SAL-1'] and K['SAL-11'], f'{dev}: SAL-1 and SAL-11 are on the task list: {K}')
            # before the hand-off: read only
            for uid in ('u_chen', 'u_billing'):
                await sign_in(pg, uid)
                for who in ('Priya Raman', 'Daniel Okafor'):
                    r = await pg.evaluate(PIPE, who)
                    c.ok(r['row'] and not r['btn'], f'{dev} {uid}: before it is handed over, {who}\'s row is read only: {r}')
            # the coordinator hands SAL-1 to herself: not delegation
            await sign_in(pg, 'u_chen')
            await pg.evaluate("() => { tkSetOwner(tkResolve(window.__k['SAL-1']), 'Chen Biron'); save(); }")
            r = await pg.evaluate(PIPE, 'Priya Raman')
            c.ok(not r['btn'], f'{dev}: a sales task the coordinator hands herself is not delegation: {r}')
            # the owner hands SAL-1 to Chen and SAL-11 to Billing (the sheet's Owner field calls tkSetOwner)
            await sign_in(pg, 'u_owner')
            await pg.evaluate("() => { tkSetOwner(tkResolve(window.__k['SAL-1']), 'Chen Biron'); tkSetOwner(tkResolve(window.__k['SAL-11']), 'Billing'); save(); }")
            own = await pg.evaluate("() => [tkResolve(window.__k['SAL-1']).x.ownerUid || (tkAll().find(t => t.key === window.__k['SAL-1']) || {}).ownerUid, (tkAll().find(t => t.key === window.__k['SAL-11']) || {}).ownerUid]")
            c.ok(own[1] == 'u_billing', f"{dev}: the lead's next step is Billing's once handed to Billing: {own}")
            for uid, who, verb in (('u_chen', 'Priya Raman', 'Draft'), ('u_billing', 'Daniel Okafor', 'Call')):
                await sign_in(pg, uid)
                r = await pg.evaluate(PIPE, who)
                c.ok(r['btn'] == verb, f'{dev} {uid}: the handed-over task reads {verb} on the Pipeline: {r}')
                c.ok(r['sw'] <= r['w'], f'{dev} {uid}: no sideways scroll on the Pipeline ({r["sw"]} > {r["w"]})')
                other = 'Daniel Okafor' if who == 'Priya Raman' else 'Priya Raman'
                r2 = await pg.evaluate(PIPE, other)
                c.ok(not r2['btn'], f'{dev} {uid}: the deal not handed to them stays read only: {r2}')
                d = await pg.evaluate(DEAL, who)
                c.ok(f'{verb}*' in d['btns'] and not any(x.startswith('Open the Full Record') for x in d['btns']), f"{dev} {uid}: the deal's page offers {verb} and not its record: {d['btns']}")
                await pg.evaluate("() => { const b = [...document.querySelectorAll('.view.on [data-ydact=\"next\"]')].find(x => x.getClientRects().length); b && b.click(); }")
                await pg.wait_for_timeout(300)
                t = await pg.evaluate("() => { const m = document.querySelector('#mbm'); return m ? m.innerText.slice(0, 160) : ''; }")
                c.ok(('SAL-1' if who == 'Priya Raman' else 'SAL-11') in t, f'{dev} {uid}: {verb} opens the task: {t[:100]!r}')
                await pg.evaluate("() => { try { mbCloseModal(); } catch (e) {} }")
            # the deal stays the owner's and the PM's
            await sign_in(pg, 'u_chen')
            t = await pg.evaluate("() => { const l = DB.leads.find(x => x.stage === 'won'); const n = DB.projects.length; slSetUpJob(l); return [document.getElementById('toast').innerText, DB.projects.length - n]; }")
            c.ok('owner sets up' in t[0] and t[1] == 0, f'{dev}: Set Up the Job stays the owner\'s and the PM\'s: {t}')
            c.ok(not errs, f'{dev}: no page errors: {errs[:3]}')
            await b.close()
    return c.done()

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
