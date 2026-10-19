"""What only the shared system (the hosted copy, several devices) can break, checked on one page (2026-10-19).
1. The owner's assistant rules for someone else reach that person.
On the hosted copy each person's assistant (DB.asst[uid]) is a private row only their sign-in reads and writes, so the
owner's device never holds it and cannot write it. The rule travels on the firm's delegation log (DB.company), the
person's device applies it when it is newer than their own last choice, and the owner's screen reads it back from the log.
Simulated here on one page by removing the other person's row the way the shared system would.
2. Two devices opening on the same day make the same recurring duties (same ids), so the record merge keeps one.
Run: python3 shared_system_test.py"""
import asyncio
from harness import async_playwright, open_app, sign_in, Checks

TYPE = 'orderFollowups'   # Chen's (coordinator) message type; the owner may set it to Hand It to Me, never Act Alone

async def main():
    c = Checks()
    async with async_playwright() as p:
        b, pg, errs = await open_app(p)
        await sign_in(pg, 'u_chen')
        # Chen's own row as his phone holds it, before the owner changes anything
        chen = await pg.evaluate("t => { paRuleSet('u_chen', t, 'ask'); return JSON.stringify(DB.asst.u_chen); }", TYPE)
        await pg.wait_for_timeout(2600)   # the clock moves on (the pinned demo clock runs at 0.42 s a second), as between two people's taps
        await sign_in(pg, 'u_owner')
        ok = await pg.evaluate("t => paRuleSet('u_chen', t, 'hand')", TYPE)
        c.ok(ok, 'the owner sets Chen\'s order follow-ups to Hand It to Me')
        # the owner's device after a reload on the shared system: it never holds Chen's private row
        lv = await pg.evaluate("t => { delete DB.asst.u_chen; return paRule(t, 'u_chen'); }", TYPE)
        c.ok(lv == 'hand', f'the owner still sees the rule they set, from the firm\'s log: {lv}')
        # Chen's phone: his own row as it was (the owner could not write it), the firm's log as the server holds it
        await pg.evaluate("s => { DB.asst.u_chen = JSON.parse(s); }", chen)
        await sign_in(pg, 'u_chen')
        r = await pg.evaluate("t => ({ lv: paRule(t), hand: (DB.asst.u_chen.handIt || []).includes(t), alone: (DB.asst.u_chen.delegated || []).includes(t) })", TYPE)
        c.ok(r['lv'] == 'hand' and r['hand'] and not r['alone'], f'Chen\'s phone applies the owner\'s rule to his own row: {r}')
        # Chen changes it back later: his later choice wins, and a re-render does not undo it
        await pg.wait_for_timeout(2600)
        r = await pg.evaluate("t => { paRuleSet('u_chen', t, 'ask'); render(); render(); return { lv: paRule(t), hand: (DB.asst.u_chen.handIt || []).includes(t) }; }", TYPE)
        c.ok(r['lv'] == 'ask' and not r['hand'], f'Chen\'s later choice wins: {r}')
        # the Standard still holds: nobody can make a person's outgoing message send alone for them
        await sign_in(pg, 'u_owner')
        ok = await pg.evaluate("t => paRuleSet('u_chen', t, 'alone')", TYPE)
        c.ok(not ok, 'the owner cannot set Chen\'s outgoing messages to Act Alone')
        # 2. two devices, the same morning: each starts from the same records without this week's duties
        r = await pg.evaluate("""() => {
          const strip = () => { (DB.projects || []).forEach(p => p.actions = (p.actions || []).filter(a => !a.recur)); DB.tasks = (DB.tasks || []).filter(a => !(a && a.recur)); };
          strip(); const A = tdyRecurSweep().map(x => x.id).sort();
          strip(); const B = tdyRecurSweep().map(x => x.id).sort();
          return { n: A.length, same: JSON.stringify(A) === JSON.stringify(B), uniq: new Set(A).size === A.length }; }""")
        c.ok(r['n'] > 0 and r['same'] and r['uniq'], f'two devices make the same recurring duties, one id each: {r}')
        c.ok(not errs, f'page errors {errs[:2]}')
        await b.close()
    print(f'{len(c.fail)} FAILED ({c.n} checks)' if c.fail else f'ALL PASS ({c.n} checks)')
    raise SystemExit(1 if c.fail else 0)

asyncio.run(main())
