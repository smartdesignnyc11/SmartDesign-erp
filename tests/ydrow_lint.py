"""ydrow_lint: every row the shared row helper draws (ydRowHtml, src/yourday.js) carries each field in the helper's own
meaning (BACKLOG §1.36, 11-05).

What was wrong. The client's Ready to Bill passed act2 holding a function (its own second action), the helper read act2
as a label, and the row printed "() => slBillRun(c, r)" as a button. The helper now draws only string labels, but a
caller can still pass a field that means something else to it: a selector in sel (every row reads selected), a date in
late (every row reads late), a function in act. This lint walks every page of every role on the desktop and the
390px phone with the helper wrapped, and fails on any row whose fields break the contract:
  id                string or number, present
  title meta when amt sec at   string (or absent)
  act act2          a non-empty string label, or absent ('' / null / undefined)
  run run2          a function, or absent
  primary late sel  true / false (or absent)
  n                 a number or a numeric string (or absent: '' reads as no count)
A row with act and no run, or run and no act, is listed too (a button with nothing behind it, or an action with no
button). The last line reads `YDROW <rows> rows on <pages> pages, <bad> clashes`.

    python3 tests/ydrow_lint.py [--user u_owner]
"""
import asyncio, sys, argparse
from harness import *

WRAP = r"""() => {
  if (window.__ydLint) return true;
  window.__ydLint = { rows: 0, bad: [], seen: new Set() };
  const L = window.__ydLint, base = ydRowHtml;
  const S = v => v == null || typeof v === 'string', B = v => v == null || typeof v === 'boolean',
        LBL = v => v == null || v === '' || (typeof v === 'string' && v.trim().length > 0), F = v => v == null || typeof v === 'function';
  ydRowHtml = function (r) {
    try {
      L.rows++;
      const why = [];
      if (!r || (typeof r.id !== 'string' && typeof r.id !== 'number')) why.push('id ' + typeof (r && r.id));
      for (const k of ['title', 'meta', 'when', 'amt', 'sec', 'at']) if (!S(r[k])) why.push(k + ' is ' + (typeof r[k] === 'function' ? 'a function' : typeof r[k]));
      for (const k of ['act', 'act2']) if (!LBL(r[k])) why.push(k + ' is ' + (typeof r[k] === 'function' ? 'a function' : typeof r[k]) + ', not a label');
      for (const k of ['run', 'run2']) if (!F(r[k])) why.push(k + ' is ' + typeof r[k] + ', not a function');
      for (const k of ['primary', 'late', 'sel']) if (!B(r[k])) why.push(k + ' is ' + typeof r[k] + ' (' + String(r[k]).slice(0, 30) + '), not true or false');
      if (r.n != null && r.n !== '' && !(typeof r.n === 'number' || /^\d+$/.test(String(r.n)))) why.push('n is ' + typeof r.n + ' (' + String(r.n).slice(0, 30) + ')');
      if (typeof r.act2 === 'string' && r.act2 && r.run2 === undefined && r.run === undefined) why.push('act2 with no run2');
      if (why.length) { const key = view + '|' + String(r.title).slice(0, 40) + '|' + why.join(';'); if (!L.seen.has(key)) { L.seen.add(key); L.bad.push({ view, role: role(), title: String(r && r.title).slice(0, 80), why }); } }
    } catch (e) { L.bad.push({ view, title: 'lint error', why: [String(e.message)] }); }
    return base.apply(this, arguments);
  };
  return true; }"""


async def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--user'); a = ap.parse_args()
    c = Checks()
    total, pages, bad = 0, 0, []
    async with async_playwright() as p:
        for phone in (False, True):
            dev = 'phone' if phone else 'desktop'
            b, pg, errs = await open_app(p, phone)
            await pg.evaluate(WRAP)
            # the instrument: a planted row with a function in act2 (the 11-05 clash) and a date in late is caught
            plant = await pg.evaluate("""() => { ydRowHtml({ id: '__plant', title: 'planted', act2: () => 1, late: '2026-09-01' });
              const L = window.__ydLint, hit = L.bad.filter(x => x.title === 'planted'); L.bad = L.bad.filter(x => x.title !== 'planted'); L.rows--; return hit.map(x => x.why); }""")
            c.ok(plant and any('act2 is a function' in w for w in plant[0]) and any('late is string' in w for w in plant[0]), f'{dev}: instrument: a planted clash is caught ({plant})')
            for uid in ([a.user] if a.user else USERS):
                await sign_in(pg, uid)
                views = await pg.evaluate("() => [...new Set((ROLE_VIEWS[role()] || []).concat(['home']))]")
                for v in views:
                    try:
                        await pg.evaluate("v => { try { mbCloseModal(); } catch (e) {} clientOpen = null; docOpen = null; view = v; render(); }", v)
                        await pg.wait_for_timeout(60)
                        pages += 1
                    except Exception as e:
                        pass
                # a client page and a deal page, where the helper draws most of its rows
                await pg.evaluate("""() => { try { if ((ROLE_VIEWS[role()] || []).includes('clients') && typeof slOpenClient === 'function') { for (const c of DB.clients.slice(0, 4)) { slOpenClient(c.id); render(); } } } catch (e) {}
                  try { if (typeof slOpenDeal === 'function' && (ROLE_VIEWS[role()] || []).includes('ovsales')) for (const l of (DB.leads || []).slice(0, 4)) slOpenDeal(l.id); } catch (e) {} }""")
            L = await pg.evaluate("() => ({ rows: window.__ydLint.rows, bad: window.__ydLint.bad })")
            total += L['rows']; bad += [dict(x, dev=dev) for x in L['bad']]
            c.ok(L['rows'] > 50, f'{dev}: the walk drew rows through the helper ({L["rows"]})')
            c.ok(not errs, f'{dev}: no page errors: {errs[:3]}')
            await b.close()
    for x in bad:
        c.ok(False, f"{x['dev']} {x['role']} {x['view']}: \"{x['title']}\": {'; '.join(x['why'])}")
    print(f'YDROW {total} rows on {pages} pages, {len(bad)} clashes')
    return c.done()

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
