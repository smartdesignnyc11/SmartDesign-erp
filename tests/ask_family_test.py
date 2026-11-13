"""The Ask families: one question, one answer, however it is phrased (founder review, wave 3; BACKLOG section 11,
rows 20 to 23; src/askfamily.js).

The founder asked the owner's Ask four plain questions and got wrong answers, each because a phrasing fell past the
reader that answers it: "where is money leaking" listed the inventory; "what haven't we billed" listed the invoices
that HAVE been billed; "what did we promise the Kleins" said none while "what do we owe the Kleins" listed three; and
the unbilled-work answer read 45 Cranberry's design phases as billed 0% though INV-2026-D45-1 billed half of each.

  screen   the four questions typed into Ask through the screen as the owner, on the desktop and on the phone (390px):
           the answer's first line and its number, no sideways scroll, and an Open link that lands on the record.
  family   each family asked every way as the person (paAsk, a fresh thread each time): every phrasing is answered by
           the family's one function (`family`), gets the same count and total (`fam`) and headline, and the count
           equals the screen that owns it (Today's "N caught for you"; the Billing tile, Ready to Bill).
  tie      45 Cranberry: the billed-to-date on each schedule line ties to the invoices on the job (jobFin's billed).
  near     neighbours a family must not take (a tool's location, a roof leak, a vendor's balance).

    python3 ask_family_test.py [-v]

All demo data is the invented seed (app day 2026-09-03)."""
import asyncio, json, re, sys
from harness import *
from ask_bank import HELPERS, RESET

VERBOSE = '-v' in sys.argv

# ---- what each screen says --------------------------------------------------------------------------------------------
SCREEN = {
    # Today as the person sees it: the quiet line's "N caught for you", then Caught for You opened and "N more" tapped
    'leaks': r"""async () => {
      view = 'home'; render();
      const q = document.querySelector('[data-td2quiet]');
      const quiet = ((q && q.innerText) || '').match(/(\d+) caught for you/i);
      if (q && q.getAttribute('aria-expanded') !== 'true') q.click();
      const more = document.querySelector('[data-tdcatchall]');
      if (more && !/Show Fewer/.test(more.innerText)) more.click();
      const el = document.querySelector('.td-catch [data-tdcaught]');
      const rows = document.querySelectorAll('.td-catch .td-c').length;
      return { how: "Today, Caught for You", n: el ? +el.dataset.tdcaught : null, quiet: quiet ? +quiet[1] : null, rows };
    }""",
    # the Billing tile Ready to Bill renders readyToBill(); the rows are the Billing Queue's
    'unbilled': r"""async () => {
      const R = readyToBill();
      return { how: 'Ready to Bill (readyToBill, the Billing tile)', n: R.rows.length, total: Math.round(R.amount * 100) / 100,
               held: R.held.length, heldTotal: H.sum(R.held, h => h.amount), items: R.rows.map(r => H.short(r.p)) };
    }""",
    # Tasks, filter Owed to the Client, for the Kleins (the list the answer's Open lands on)
    'promises': r"""async () => {
      const c = H.C('Klein');
      const T = openTasks('all').filter(x => tkOwedBy(x, 'client') && (tkClientOfTask(x) || {}).id === c.id);
      return { how: 'Tasks, Owed to the Client', tasks: T.length, items: T.map(x => x.code).filter(Boolean) };
    }""",
}

FAMILIES = [
    dict(id='leaks', roles=['u_owner', 'u_alan', 'u_billing', 'u_controller'], nums=['n'], says='n', qs=[
        'where is money leaking', 'money leaks', 'what are the money leaks', 'where are we losing money',
        'where are we leaking money', 'any leaks', 'what did you catch', 'Where is the money leaking?']),
    dict(id='unbilled', roles=['u_owner', 'u_billing'], nums=['n', 'total', 'held', 'heldTotal'], says='total', qs=[
        "what haven't we billed", 'what have we not billed', "what's not billed", 'what is not invoiced',
        "what haven't we invoiced yet", 'work done not billed', 'unbilled work', 'what is unbilled',
        'what work is done but not billed', "what hasn't been billed", 'what should we invoice today', 'what is ready to bill']),
    dict(id='promises', roles=['u_owner', 'u_alan'], nums=['tasks'], says='n', qs=[
        'what did we promise the Kleins', 'what have we promised the Kleins', 'what do we owe the Kleins',
        'what have we committed to the Kleins', 'what do I owe the Kleins', 'what are we still owing the Kleins']),
]
# (who, question, the family it must land in, or None for "not a family")
NEIGHBOURS = [
    ('u_owner', 'where is the table saw', None),
    ('u_owner', 'is there a leak in the roof at 121 State', None),
    ('u_owner', 'what do the Kleins owe us', None),
    ('u_owner', 'what do we owe vendors', None),
    ('u_billing', 'which change orders are approved but not billed', None),
    ('u_owner', "what have we bought for clients that we haven't billed", None),
    ('u_billing', 'which invoices are not paid', None),
    ('u_klein', 'what is not billed', None),
    ('u_angel', 'where is money leaking', None),
]

ASK = r"""
async ({ q, reset }) => {
  const R = eval(reset); R();
  let a = null, err = '';
  try { a = await Promise.resolve(paAsk(q)); } catch (e) { err = String(e && e.message || e); }
  R();
  a = a || {};
  const str = x => typeof x === 'string' ? x : x == null ? '' : JSON.stringify(x);
  return { err, family: a.family || null, fam: a.fam || null, headline: str(a.headline), work: (a.work || []).map(str), interp: str(a.interp), go: !!a.go };
}
"""
SAY = r"""async ({ q }) => {
  const n = paInit().thread.filter(m => m.who === 'a').length;
  document.querySelector('#pa-in').value = q;
  document.querySelector('#pa-ask').requestSubmit();
  const t0 = Date.now();
  while ((paBusy || paInit().thread.filter(m => m.who === 'a').length <= n) && Date.now() - t0 < 20000) await new Promise(r => setTimeout(r, 50));
  await new Promise(r => setTimeout(r, 150));
  const m = paInit().thread.filter(m => m.who === 'a').slice(-1)[0];
  const els = [...document.querySelectorAll('#pa-thread .pa-m.a')], el = els[els.length - 1];
  return { text: m.text, links: el ? el.querySelectorAll('a.pa-rec[data-pclink]').length : 0, shown: el ? el.innerText : '',
           sideways: document.documentElement.scrollWidth - innerWidth };
}"""


def near(a, b, tol=0.011):
    return a is not None and b is not None and abs(float(a) - float(b)) <= tol


async def screen(p, c, phone):
    """The four founder questions typed into Ask through the screen as the owner."""
    dev = 'phone' if phone else 'desktop'
    b, pg, errs = await open_app(p, phone=phone)
    await pg.evaluate(HELPERS)
    await sign_in(pg, 'u_owner')
    S = await pg.evaluate("async () => { const H = window.__AB; return await (" + SCREEN['leaks'] + ")(); }")
    c.ok(S['n'] is not None and S['n'] == S['rows'] and S['quiet'] == S['n'], f"{dev}: Today agrees with itself: header {S['n']}, rows {S['rows']}, quiet line {S['quiet']}")
    U = await pg.evaluate("async () => { const H = window.__AB; return await (" + SCREEN['unbilled'] + ")(); }")
    rtb = await pg.evaluate("v => money(v)", U['total'])
    await go(pg, 'pa')
    a = await pg.evaluate(SAY, {'q': 'where is money leaking'})
    if VERBOSE: print(f"  [{dev}] leaking -> {a['text'][:160]}")
    c.ok(a['text'].startswith(f"{S['n']} things caught for you"), f"{dev}: \"where is money leaking\" opens with Today's {S['n']} caught ({a['text'][:90]})")
    c.ok('items' not in a['text'][:40] and 'table saw' not in a['shown'].lower(), f"{dev}: \"where is money leaking\" is not the inventory ({a['text'][:60]})")
    c.ok(re.search(r'\$[\d,]+', a['text']) is not None and a['links'] >= 5, f"{dev}: the leak answer names dollars and each row opens its record ({a['links']} links)")
    c.ok(a['sideways'] <= 0, f"{dev}: the leak answer does not scroll sideways ({a['sideways']}px)")
    # a row's name opens its record: the first link that names a bank line lands on Banking
    hit = await pg.evaluate("""() => { const el = [...document.querySelectorAll('#pa-thread .pa-m.a')].pop();
        const L = [...el.querySelectorAll('a.pa-rec[data-pclink]')].find(x => /^Not matched/.test(x.textContent)); if (!L) return null;
        L.click(); return view; }""")
    c.ok(hit == 'bank', f"{dev}: a leak row's link opens its record (Not matched lands on {hit})")
    await go(pg, 'pa')
    for q in ["what haven't we billed", "what's not billed", 'work done not billed', 'unbilled work']:
        a = await pg.evaluate(SAY, {'q': q})
        if VERBOSE: print(f"  [{dev}] {q} -> {a['text'][:160]}")
        c.ok(a['text'].startswith(rtb) and 'invoices' not in a['text'][:30], f"{dev}: \"{q}\" opens with Ready to Bill's {rtb} ({a['text'][:90]})")
        c.ok(a['sideways'] <= 0, f"{dev}: \"{q}\" does not scroll sideways ({a['sideways']}px)")
    P = await pg.evaluate("async () => { const H = window.__AB; return await (" + SCREEN['promises'] + ")(); }")
    for q in ['what did we promise the Kleins', 'what do we owe the Kleins']:
        a = await pg.evaluate(SAY, {'q': q})
        if VERBOSE: print(f"  [{dev}] {q} -> {a['text'][:160]}")
        c.ok(a['text'].startswith('We owe Sarah & David Klein') and not re.search(r': none\b', a['text']) and f"{P['tasks']} open task" in a['text'],
             f"{dev}: \"{q}\" lists the {P['tasks']} open tasks the Kleins wait for ({a['text'][:110]})")
    c.ok(not errs, f'{dev}: page errors: {errs[:3]}')
    await b.close()


async def families(p, c):
    b, pg, errs = await open_app(p)
    await pg.evaluate(HELPERS)
    for F in FAMILIES:
        for uid in F['roles']:
            await sign_in(pg, uid)
            S = await pg.evaluate("async () => { const H = window.__AB; return await (" + SCREEN[F['id']] + ")(); }")
            await sign_in(pg, uid)
            tag = f"{F['id']} · {uid}"
            first = None
            for q in F['qs']:
                r = await pg.evaluate(ASK, {'q': q, 'reset': RESET})
                if VERBOSE: print(f"  [{uid}] {q!r} -> {r['family']} | {r['headline'][:150]}")
                c.ok(not r['err'], f"{tag}: \"{q}\" threw {r['err']}")
                c.ok(r['family'] == F['id'], f"{tag}: \"{q}\" is answered by the {F['id']} family (got {r['family']}: {r['headline'][:110]})")
                if r['family'] != F['id']: continue
                fam = r['fam'] or {}
                for k in F['nums']:
                    c.ok(near(fam.get(k), S.get(k)), f"{tag}: \"{q}\" {k} = {fam.get(k)}; the screen ({S['how']}) says {S.get(k)}")
                v = fam.get(F['says'])
                shown = (await pg.evaluate("v => money(v)", v)) if F['says'] == 'total' else str(v)
                c.ok(shown in r['headline'], f"{tag}: \"{q}\" the headline shows {shown} ({r['headline'][:120]})")
                miss = [it for it in (S.get('items') or []) if it not in ' '.join([r['headline']] + r['work'])]
                c.ok(not miss, f"{tag}: \"{q}\" lists what the screen lists; missing {miss[:4]}")
                c.ok(r['go'], f"{tag}: \"{q}\" opens the screen that owns the number")
                if F['id'] == 'promises':
                    c.ok(fam.get('n') == fam.get('tasks', 0) + fam.get('ledger', 0) + fam.get('standard', 0) and fam.get('n', 0) >= S['tasks'],
                         f"{tag}: \"{q}\" the count is its parts and reads past an empty ledger ({fam})")
                if first is None: first = r
                else:
                    same = json.dumps(r['fam'], sort_keys=True) == json.dumps(first['fam'], sort_keys=True) and \
                        re.sub(r'^You and the firm owe', 'We owe', r['headline']) == re.sub(r'^You and the firm owe', 'We owe', first['headline'])
                    c.ok(same, f"{tag}: \"{q}\" gets the same answer as \"{F['qs'][0]}\" ({r['headline'][:80]} | {first['headline'][:80]})")
    for uid, q, want in NEIGHBOURS:
        await sign_in(pg, uid)
        r = await pg.evaluate(ASK, {'q': q, 'reset': RESET})
        if VERBOSE: print(f"  [{uid}] {q!r} -> {r['family']} | {r['headline'][:150]}")
        c.ok(r['family'] == want, f"neighbour · {uid}: \"{q}\" belongs to {want or 'another reader'} (got {r['family']}: {r['headline'][:110]})")
        c.ok(not r['err'] and bool(r['headline']), f"neighbour · {uid}: \"{q}\" is answered ({r['err']})")
    # the keyword table under the readers: a question it cannot read is not answered with a list of the wrong thing
    await sign_in(pg, 'u_owner')
    for q, bad in [('where is money going', 'inventory'), ('where is the Klein contract', 'inventory'), ('what did we not bill last month', 'invoices (')]:
        r = await pg.evaluate(ASK, {'q': q, 'reset': RESET})
        if VERBOSE: print(f"  [u_owner] {q!r} -> {r['headline'][:120]} | {r['interp'][:60]}")
        c.ok(bad not in r['interp'] and not re.match(r'^\d+ (items|invoices)\b', r['headline']), f"keyword table: \"{q}\" is not answered with the {bad.split(' ')[0]} list ({r['headline'][:90]} | {r['interp'][:60]})")
    # 45 Cranberry: each design phase's billed-to-date ties to the invoices on the job
    T = await pg.evaluate("""() => { const p = DB.projects.find(x => x.id === 'p45'), R = pgRows('p45');
        return { billed: jobFin(p).billed, lines: R.reduce((a, r) => a + r.ev.scheduled * r.ev.billedPct / 100, 0),
                 sd: (R.find(r => r.sv.desc === 'Schematic design') || { ev: {} }).ev.billedPct,
                 work: lkUnbilledWork('p45').map(w => [w.desc, Math.round(w.amount)]) }; }""")
    if VERBOSE: print('  45 Cranberry', T)
    c.ok(near(T['lines'], T['billed'], 0.5), f"tie: 45 Cranberry's schedule lines carry ${T['lines']:,.2f} billed; the job's invoices ${T['billed']:,.2f}")
    c.ok(near(T['sd'], 50), f"tie: Schematic design reads billed {T['sd']}%; INV-2026-D45-1 billed 50% of it")
    c.ok(dict(T['work']).get('Schematic design') == 3500 and 'Construction documents' not in dict(T['work']),
         f"tie: measured and not billed on 45 Cranberry is the work past what was invoiced ({T['work']})")
    c.ok(not errs, f'page errors: {errs[:3]}')
    await b.close()


async def main():
    c = Checks()
    async with async_playwright() as p:
        await screen(p, c, False)
        await screen(p, c, True)
        await families(p, c)
    return c.done()

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
