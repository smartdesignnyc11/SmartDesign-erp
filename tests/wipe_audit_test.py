"""Clear Everything keeps the audit trail whole (Settings, Take the Demo Out, Clear Everything; src/app.js rdWipeAudit).

Before: rdWipe('all') emptied DB.audit but kept DB.auditHead and each month close's recorded head, so auditVerify read
"the trail ends at 0, its head says N" on every device, as if the books had been tampered with.
Now, done as the owner through the screen (type CLEAR, press Clear Everything), on desktop and the 390px phone:
- auditVerify() reports no break, right after and after a reload;
- the trail's first row records the wipe: who (the owner's name), when, how many rows went and which closes lost their
  anchor; it is sealed from genesis and the head names it;
- no month close still records a head into the removed rows."""
import asyncio, sys
from harness import *

STATE = r"""() => { const V = auditVerify(), a = (DB.audit || [])[0] || {};
  return { ok: V.ok, broken: V.broken, rows: DB.audit.length, head: DB.auditHead || null,
    first: { kind: a.kind, refId: a.refId, action: a.action, by: a.by, ts: a.ts, n: a.n, prev: a.prev, sealed: !!a.h, before: a.before, note: a.note },
    anchors: ((DB.periods || {}).closes || []).filter(c => c && c.auditHead).length,
    owner: (DB.users.find(u => u.id === 'u_owner') || {}).name }; }"""


async def main():
    c = Checks()
    async with async_playwright() as p:
        for phone in (False, True):
            dev = 'phone' if phone else 'desktop'
            b, pg, errs = await open_app(p, phone)
            await sign_in(pg, 'u_owner')
            # a sealed trail and a month close that recorded its head (the case that read as tampering)
            pre = await pg.evaluate("""() => { auditSeal(); DB.periods = DB.periods || {}; DB.periods.closes = DB.periods.closes || [];
              if (!DB.periods.closes.some(c => c && c.auditHead)) DB.periods.closes.push({ month: '2026-07', at: appNowIso(), auditHead: { n: DB.auditHead.n, h: DB.auditHead.h } });
              save(); return { ok: auditVerify().ok, rows: DB.audit.length, head: DB.auditHead.n, anchors: DB.periods.closes.filter(c => c.auditHead).map(c => c.month), now: appNowIso().slice(0, 10) }; }""")
            c.ok(pre['ok'] and pre['rows'] > 0 and pre['anchors'], f'{dev}: before, the trail verifies and a close holds an anchor: {pre}')
            # the owner clears everything through the screen
            await go(pg, 'cosettings')
            btn = pg.locator('[data-ydwipe]').first
            c.ok(await btn.count() == 1, f'{dev}: Settings shows Clear Everything to the owner')
            await btn.scroll_into_view_if_needed(); await btn.click(); await pg.wait_for_timeout(200)
            await pg.fill('#mbm [data-f=confirm], [data-f=confirm]', 'CLEAR'); await pg.wait_for_timeout(100)
            await pg.click('#mbm-ok'); await pg.wait_for_timeout(500)
            s = await pg.evaluate(STATE)
            c.ok(s['ok'] and not s['broken'], f"{dev}: after Clear Everything the trail verifies: {s['broken']}")
            f = s['first']
            c.ok(s['rows'] >= 1 and f['action'] == 'cleared-everything' and f['refId'] == 'wipe', f"{dev}: the trail's first row records the wipe: {f}")
            c.ok(f['by'] == s['owner'] and f['ts'] and f['ts'][:10] == pre['now'], f"{dev}: it names who and when (the app's day at the wipe): by={f['by']!r} owner={s['owner']!r} ts={f['ts']!r} day={pre['now']!r}")
            c.ok(f['before'] and f['before'].get('auditRows') == pre['rows'] and f['before'].get('auditHead', {}).get('n') == pre['head'] and pre['anchors'][0] in f['before'].get('closeAnchors', []),
                 f"{dev}: it records what went: {pre['rows']} rows, head {pre['head']}, the anchors {pre['anchors']}: {f['before']}")
            c.ok(f['sealed'] and f['n'] == 1 and f['prev'] == 'genesis' and s['head'] and s['head']['n'] >= 1, f"{dev}: sealed from genesis and the head moved on: n={f['n']} prev={f['prev']} head={s['head']}")
            c.ok(s['anchors'] == 0, f"{dev}: no close still points into the removed rows ({s['anchors']})")
            # the same on the next open
            await pg.wait_for_timeout(300)
            await pg.reload(); await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
            await sign_in(pg, 'u_owner')
            s2 = await pg.evaluate(STATE)
            c.ok(s2['ok'] and s2['first']['action'] == 'cleared-everything', f"{dev}: after a reload the trail still verifies from the wipe row: {s2['broken']} first={s2['first']['action']}")
            sw = await pg.evaluate('[document.scrollingElement.scrollWidth, innerWidth]')
            c.ok(sw[0] <= sw[1], f'{dev}: no sideways scroll ({sw})')
            c.ok(not errs, f'{dev}: no page errors: {errs[:3]}')
            await b.close()
    return c.done()

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
