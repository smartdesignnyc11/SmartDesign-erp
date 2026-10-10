"""appSetDay: the one way to move the app's day (src/app.js, next to iaOneClock).

Checks that moving the day moves every reader of the clock (today(), each project's today, appNowIso,
appWeek), runs the day's hooks once (APP_DAY_HOOKS: fTick, clTaskSweep, b4Sweep, smSweep, hbSeqTick, bnTick),
moves the built-in Demo Workspace's clock with it, persists across a reload, refuses a bad day without
touching the data, and that the Firm's Clock card goes through it. A boot that never calls it stays on
2026-09-03 (baseline_test pins the figures).

  python3 appday_test.py      # ALL PASS (n checks)
"""
import asyncio, sys
from harness import *


async def main():
    C = Checks()
    async with async_playwright() as p:
        b, pg, errs = await open_app(p)
        await sign_in(pg, 'u_owner')
        r0 = await pg.evaluate("() => ({ today: today(), asOf: DB.company.asOf, has: typeof appSetDay, hooks: APP_DAY_HOOKS.map(h => h[0]) })")
        C.ok(r0['today'] == '2026-09-03' and r0['asOf'] == '2026-09-03', f'a boot stays on the seed day ({r0})')
        C.ok(r0['has'] == 'function' and r0['hooks'][:6] == ['fTick', 'clTaskSweep', 'b4Sweep', 'smSweep', 'hbSeqTick', 'bnTick'] and len(set(r0['hooks'])) == len(r0['hooks']), f'appSetDay and its hooks exist ({r0})')

        # A field question sent on 9/3 with a 24-hour window escalates when the day turns (fTick runs on the new day).
        r1 = await pg.evaluate("""() => {
          setCurrent('p121');
          const q = fSend({ type: 'blocker', title: 'appday test: hinges for the 3rd floor doors', note: 'need them Monday' });
          const before = q.escalated;
          const r = appSetDay('2026-09-08');
          return { r, before, after: DB.field.raises.find(x => x.id === q.id).escalated, today: today(),
                   projs: [...new Set(DB.projects.map(p => p.project.today))], now: appNowIso().slice(0, 10),
                   week: appWeek().mon, tick: String(DB.company.brainTick || '').slice(0, 10) };
        }""")
        C.ok(r1['r']['from'] == '2026-09-03' and r1['r']['to'] == '2026-09-08' and not r1['r']['errors'], f"appSetDay moves 9/3 -> 9/8 with no hook errors ({r1['r']})")
        C.ok(r1['today'] == '2026-09-08' and r1['projs'] == ['2026-09-08'] and r1['now'] == '2026-09-08' and r1['week'] == '2026-09-07',
             f"today(), every project's today, appNowIso and appWeek read the new day ({r1})")
        C.ok(r1['r']['ran'] == r0['hooks'], f"the day's hooks ran once each ({r1['r']['ran']})")
        C.ok(r1['before'] is False and r1['after'] is True, f"a field question past its window escalated on the new day (fTick) ({r1['before']} -> {r1['after']})")
        C.ok(r1['tick'] == '2026-09-08', f"the brain's tick is stamped on the new day ({r1['tick']})")

        r2 = await pg.evaluate("() => appSetDay('2026-09-08')")
        C.ok(r2['ran'] == [] and r2['from'] == r2['to'] == '2026-09-08', f'the same day again runs no hooks ({r2})')
        r3 = await pg.evaluate("() => { const was = JSON.stringify(DB.company); try { appSetDay('9/9/2026'); return { threw: false }; } catch (e) { return { threw: true, msg: e.message, same: was === JSON.stringify(DB.company) }; } }")
        C.ok(r3['threw'] and r3['same'], f'a bad day is refused and nothing changes ({r3})')

        # The built-in Demo Workspace runs on the app clock: connect on 9/8, move to 9/9, its clock moves too.
        await sign_in(pg, 'u_chen')
        r4 = await pg.evaluate("""async () => { await gcDemoConnect(); const W = demoWsFor('u_chen'); const a = appIso(new Date(W.now)).slice(0, 10);
          appSetDay('2026-09-09'); const b = appIso(new Date(W.now)).slice(0, 10); return { a, b }; }""")
        C.ok(r4['a'] == '2026-09-08' and r4['b'] == '2026-09-09', f"the Demo Workspace's clock follows the app day ({r4})")

        # Persisted: a reload reads the same day.
        await pg.wait_for_timeout(1500)
        await pg.evaluate("() => (typeof trFlush === 'function' ? trFlush() : saveNow && saveNow())")
        await pg.wait_for_timeout(500)
        await pg.reload()
        await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
        r5 = await pg.evaluate("() => ({ today: today(), asOf: DB.company.asOf, manual: DB.company.asOfManual })")
        C.ok(r5['today'] == '2026-09-09' and r5['asOf'] == '2026-09-09' and r5['manual'], f'the day survives a reload ({r5})')

        # The Firm's Clock card (Projects settings) goes through appSetDay.
        await sign_in(pg, 'u_owner')
        r6 = await pg.evaluate("""() => { view = 'proj'; render(); const i = document.querySelector('#asof-date'); if (!i) return { card: false };
          i.value = '2026-09-10'; i.dispatchEvent(new Event('change')); const t = today();
          const i2 = document.querySelector('#asof-date'); i2.value = ''; i2.dispatchEvent(new Event('change'));
          return { card: true, t, cleared: today(), asOf: DB.company.asOf, manual: DB.company.asOfManual, tz: tzToday() }; }""")
        C.ok(r6['card'] and r6['t'] == '2026-09-10', f"the Firm's Clock card moves the day through appSetDay ({r6})")
        C.ok(r6.get('cleared') == r6.get('tz') and r6.get('asOf') == '' and r6.get('manual') is False, f"clearing the card unpins the day ({r6})")
        C.ok(not errs, f'no page errors ({errs[:3]})')
        await b.close()
    return C.done()


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
