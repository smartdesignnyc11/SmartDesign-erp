"""The owner's assistant rules for someone else reach that person on the shared system (2026-10-19).
On the hosted copy each person's assistant (DB.asst[uid]) is a private row only their sign-in reads and writes, so the
owner's device never holds it and cannot write it. The rule travels on the firm's delegation log (DB.company), the
person's device applies it when it is newer than their own last choice, and the owner's screen reads it back from the log.
Simulated here on one page by removing the other person's row the way the shared system would.
Run: python3 asst_rules_shared_test.py"""
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
        await pg.wait_for_timeout(1100)   # the clock moves on a second, as it would between two people's taps
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
        await pg.wait_for_timeout(1100)
        r = await pg.evaluate("t => { paRuleSet('u_chen', t, 'ask'); render(); render(); return { lv: paRule(t), hand: (DB.asst.u_chen.handIt || []).includes(t) }; }", TYPE)
        c.ok(r['lv'] == 'ask' and not r['hand'], f'Chen\'s later choice wins: {r}')
        # the Standard still holds: nobody can make a person's outgoing message send alone for them
        await sign_in(pg, 'u_owner')
        ok = await pg.evaluate("t => paRuleSet('u_chen', t, 'alone')", TYPE)
        c.ok(not ok, 'the owner cannot set Chen\'s outgoing messages to Act Alone')
        c.ok(not errs, f'page errors {errs[:2]}')
        await b.close()
    print(f'{len(c.fail)} FAILED ({c.n} checks)' if c.fail else f'ALL PASS ({c.n} checks)')
    raise SystemExit(1 if c.fail else 0)

asyncio.run(main())
