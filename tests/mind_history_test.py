"""The assistant sends the conversation as question-and-answer pairs (2026-10-19). Live, a question whose answer was not
in the history (a reader's answer, a slow one) was glued onto the next question, and the model answered the old one
first: "A morning site huddle is..." before every answer. A question is now sent only with its answer.
Run: python3 mind_history_test.py"""
import asyncio
from harness import async_playwright, open_app, sign_in, Checks

async def main():
    c = Checks()
    async with async_playwright() as p:
        b, pg, errs = await open_app(p, False)
        await sign_in(pg, 'u_owner')
        r = await pg.evaluate("""async () => {
          const A = paInit(); A.thread = [];
          paSay('me', 'Write two plain sentences on what a morning site huddle is for.');
          paSay('a', 'A huddle aligns the crew.', { md: true, kind: 'mind' });
          paSay('me', 'Reply with the word ready.');
          paSay('a', 'Ready', { kind: 'query', readAs: 'reader' });
          paSay('me', 'A question that never got its answer');
          paSay('a', 'Still working on that one.', { kind: 'slow' });
          paSay('me', 'Are we overpaying for tile?');
          const sent = []; const base = mindPost;
          mindPost = async (body) => { sent.push(JSON.parse(JSON.stringify(body.messages))); return { content: [{ type: 'text', text: 'ok' }], stop_reason: 'end_turn', usage: {} }; };
          try { await mindAsk('Are we overpaying for tile?', () => {}); } finally { mindPost = base; }
          return sent[0]; }""")
        roles = [m['role'] for m in r]
        users = [m['content'] for m in r if m['role'] == 'user']
        c.ok(all(roles[i] != roles[i + 1] for i in range(len(roles) - 1)) and roles[0] == 'user' and roles[-1] == 'user', f'turns alternate, person first and last: {roles}')
        c.ok(users[-1] == 'Are we overpaying for tile?', f'the last turn is the question alone, nothing glued to it: {users[-1]!r}')
        c.ok('A question that never got its answer' not in ' '.join(users), 'a question without its answer is not sent')
        c.ok(any('Ready' == m['content'] for m in r if m['role'] == 'assistant'), "a reader's answer stays with its question")
        c.ok(not errs, f'page errors {errs[:2]}')
        await b.close()
    print(f'{len(c.fail)} FAILED ({c.n} checks)' if c.fail else f'ALL PASS ({c.n} checks)')
    raise SystemExit(1 if c.fail else 0)

asyncio.run(main())
