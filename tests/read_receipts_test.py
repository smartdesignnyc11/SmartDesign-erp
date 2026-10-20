"""Read receipts in one-to-one chats only (Alan, 2026-10-20: "Okay for now"). The last line I sent in a direct chat
shows Read once the other person has opened it; a group or a job thread never shows Read.
Run: python3 read_receipts_test.py"""
import asyncio
from harness import async_playwright, open_app, sign_in, Checks

READ = "() => !!document.querySelector('#v-chat .cm.me .msg-read')"
async def main():
    c = Checks()
    async with async_playwright() as p:
        for phone in (False, True):
            tag = 'phone' if phone else 'desktop'
            b, pg, errs = await open_app(p, phone)
            await sign_in(pg, 'u_owner')
            key = await pg.evaluate("() => { const T = msgDirectWith('u_chen', true); msgPostDm(T, 'Can you confirm the tile delivery for Thursday?'); save(); setView('chat'); msgOpen(T.key); return T.key; }")
            await pg.wait_for_timeout(300)
            c.ok(not await pg.evaluate(READ), f'{tag}: before Chen opens it, my line is not marked Read')
            await sign_in(pg, 'u_chen')
            await pg.evaluate("k => { setView('chat'); msgOpen(k); }", key); await pg.wait_for_timeout(300)
            await sign_in(pg, 'u_owner')
            await pg.evaluate("k => { setView('chat'); msgOpen(k); }", key); await pg.wait_for_timeout(300)
            c.ok(await pg.evaluate(READ), f'{tag}: after Chen opened the chat, my last line shows Read')
            # a group of three: never Read
            gk = await pg.evaluate("""() => { const t = { id: uid('th'), kind: 'group', title: 'Site Leads Test', members: ['u_owner', 'u_chen', 'u_angel'], createdBy: 'u_owner', createdAt: appNowIso(), msgs: [], seen: {} };
              msgStore().push(t); const T = msgDmT(t); msgPostDm(T, 'Huddle at 7'); save(); return T.key; }""")
            await sign_in(pg, 'u_chen'); await pg.evaluate("k => { setView('chat'); msgOpen(k); }", gk); await pg.wait_for_timeout(200)
            await sign_in(pg, 'u_owner'); await pg.evaluate("k => { setView('chat'); msgOpen(k); }", gk); await pg.wait_for_timeout(300)
            c.ok(not await pg.evaluate(READ), f'{tag}: a group chat never shows Read')
            c.ok(not errs, f'{tag}: page errors {errs[:2]}')
            await b.close()
    print(f'{len(c.fail)} FAILED ({c.n} checks)' if c.fail else f'ALL PASS ({c.n} checks)')
    raise SystemExit(1 if c.fail else 0)

asyncio.run(main())
