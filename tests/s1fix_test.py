"""The S1 and S2 bugs the role experts found on 2026-10-21 (review/experts/owner/owner.md, review/experts/pm/pm.md),
each checked as the class it belongs to, desktop and phone where a person would meet it.
1. A chase never asks for a date already gone, names the choice in the client's words and says what waits on it.
2. "Mine" matches a person by id, never by a first name the owner shares; one person, one name; one late count.
3. A bank line never settles a bill dated after it unless a person said why; one truth per bank line; a held bill
   reads Held with who and why wherever it is listed.
4. Controls counts the lines matched to nothing, and says "not yet verified" when verification never ran.
5. A COI that has lapsed, or lapses within 30 days, for a sub or vendor booked on site reaches the owner and coordinator.
6. The headline counts the jobs with a delay on the way (PRED.jobsAtRisk) and names the worst.
7. A bill already paid at the bank, or held, is never in a Payment Run.
8. The client portal says what was billed and what is complete on site in plain words, and why they differ.
Run: python3 s1fix_test.py"""
import asyncio, re
from harness import async_playwright, open_app, sign_in, go, Checks

# every date a draft names, read back as ISO dates on the app's year
DATES = r"""(txt) => { const M = {Jan:1,Feb:2,Mar:3,Apr:4,May:5,Jun:6,Jul:7,Aug:8,Sep:9,Oct:10,Nov:11,Dec:12}, out = [];
  String(txt).replace(/\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun), (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{1,2})\b/g, (m, d, mo, day) => {
    out.push(today().slice(0, 4) + '-' + String(M[mo]).padStart(2, '0') + '-' + String(day).padStart(2, '0')); return m; });
  return out; }"""

async def chase_checks(c, pg, tag):
    # 1. the PM's first Chase on Today: the overdue bathroom decision
    await sign_in(pg, 'u_alan'); await go(pg, 'home'); await pg.wait_for_timeout(300)
    r = await pg.evaluate("""async () => { const b = [...document.querySelectorAll('button')].find(x => x.offsetParent && x.innerText.trim() === 'Chase');
      if (!b) return null; b.click(); await new Promise(r => setTimeout(r, 500));
      const t = [...document.querySelectorAll('#mbm textarea, #mbm input')].map(e => e.value).join('\\n');
      try { mbCloseModal(); } catch (e) {} return t; }""")
    c.ok(r is not None, f'{tag}: the PM has a Chase on Today')
    if r:
        ds = await pg.evaluate(f"({DATES})({repr(r)})")
        td = await pg.evaluate("today()")
        c.ok(ds and all(d >= td for d in ds), f'{tag}: the chase asks for a date on or after today ({ds} vs {td}): {r[-200:]}')
        c.ok('re-review with client' not in r and 'bathroom finishes' in r, f'{tag}: the chase names the choice in the client\'s words, not our record name ({r[-200:]})')
        c.ok(re.search(r'starts (Mon|Tue|Wed|Thu|Fri), Sep \d+', r) is not None, f'{tag}: the chase says what waits on the answer and when ({r[-200:]})')
    # every decision chase the app can draft, on every job: Caught's message, Ask's draft, the Send to Client ask
    r = await pg.evaluate(f"""() => {{ const D = {DATES}, td = today(), bad = [];
      DB.projects.forEach(p => (p.decisions || []).filter(d => d.status === 'open').forEach(d => {{
        const A = chaseAsk(d, p), n = clNeed(d, p),
          g = agChaseDraft({{ kind: 'decision', to: {{ name: 'Sarah Klein' }}, decision: d, job: p }});
        if (!(A.by >= td) || !isWork(A.by)) bad.push('by ' + d.name + ' ' + A.by);
        [n.ask, g.body, A.sentence].forEach(t => D(t).forEach(x => x < td && bad.push(d.name + ': ' + t.slice(0, 120))));
        if (/re-review with client/.test(g.body)) bad.push('record name in ' + d.name);
      }}));
      const X = tdFacts().X; X && eaChase(tdFacts().F, X, 'pm').filter(x => x.msg).forEach(x => D(x.msg).forEach(y => y < td && bad.push('caught: ' + x.msg.slice(0, 120))));
      return bad; }}""")
    c.ok(not r, f'{tag}: no decision chase on any job asks for a past date or quotes the record name ({r[:4]})')
    r = await pg.evaluate("""() => { const td = today(); return [chaseBy('2026-09-02', '2026-09-10'), chaseBy('2026-09-05', ''), chaseBy('', '2026-09-04'), chaseBy('2026-09-12', '')].map(d => [d, d >= td && isWork(d)]) }""")
    c.ok(all(x[1] for x in r), f'{tag}: chaseBy always lands on a working day on or after today ({r})')

async def owner_checks(c, pg, tag):
    # 2. people: by id, never a shared first name; one person, one name
    r = await pg.evaluate("""() => ({ pmIsOwner: tkOwnerMatch('Alan', 'Owner'), ownerIsPm: tkOwnerMatch('Owner', 'Alan'),
      chen: tkOwnerMatch('Chen', 'Chen Biron'), byId: tkOwnerMatch('u_alan', 'Alan'), pair: tkOwnerMatch('Alberto / Satish', 'Satish') === false && tkOwnerMatch('Alberto / Satish', 'Alberto') })""")
    c.ok(not r['pmIsOwner'] and not r['ownerIsPm'], f'{tag}: the PM named Alan is not the owner, either way ({r})')
    c.ok(r['chen'] and r['byId'] and r['pair'], f'{tag}: a unique first name and a user id still match ({r})')
    r = await pg.evaluate("""() => { DB.users.push({ id: 'u_tmp_owner2', name: 'Alan Mishali', role: 'owner' }); tkPeople._c = null;
      const out = { shared: tkOwnerMatch('Alan M', 'Alan Mishali'), full: tkOwnerMatch('Alan', 'Alan Mishali'), pm: tkOwnerMatch('Alan', 'Alan') };
      DB.users = DB.users.filter(u => u.id !== 'u_tmp_owner2'); tkPeople._c = null; return out; }""")
    c.ok(not r['shared'] and not r['full'] and r['pm'], f'{tag}: with two Alans, a bare or shared first name names neither the other one ({r})')
    r = await pg.evaluate("""() => { const N = (DB.users || []).map(u => u.name).concat((DB.employees || []).filter(e => e.active !== false).map(e => e.name))
        .map(s => String(s || '').trim().toLowerCase().split(/[\\s(]/)[0]).filter(s => s.length > 2);
      const U = [...new Set(N)], near = [];
      const d1 = (a, b) => { if (a === b || Math.abs(a.length - b.length) > 1) return false; let i = 0, j = 0, e = 0;
        while (i < a.length && j < b.length) { if (a[i] === b[j]) { i++; j++; continue; } if (++e > 1) return false;
          if (a.length > b.length) i++; else if (b.length > a.length) j++; else { i++; j++; } } return e + (a.length - i) + (b.length - j) <= 1; };
      U.forEach((a, i) => U.slice(i + 1).forEach(b => d1(a, b) && near.push(a + '/' + b))); return near; }""")
    c.ok(not r, f'{tag}: no two people carry names one letter apart (Maya and Maja read as one person typed twice): {r}')
    # one late count for the PM: Mine, Ask's two phrasings, the Today chip's late tasks
    for uid in ('u_alan', 'u_owner'):
        await sign_in(pg, uid)
        r = await pg.evaluate("""async () => { const me = tkMe(), mine = tkItems().filter(x => !x.done && tkOwnerMatch(x.assignee, me)), late = mine.filter(x => x.late).length, lateNs = mine.filter(x => x.late && x.kind !== 'sched').length;
          const M = paMine(); const h = []; for (const q of ['which of my tasks are late', 'which tasks are overdue for me']) { const a = await Promise.resolve(paAsk(q)); h.push(a.headline || ''); }
          const caught = tkAll({ open: true, uid: currentUser().id }).filter(t => !t.approval && t.late).length;
          return { me, mine: mine.length, late, lateNs, paMine: M.open.length, paLate: M.late.length, h, caught }; }""")
        nums = [int(m.group(1)) if m else -1 for m in [re.search(r'(\d+) late', x) or re.search(r'^(\d+) tasks? (?:are )?(?:late|overdue)', x) or re.search(r'(\d+)', x) for x in r['h']]]
        c.ok(r['paMine'] == r['mine'] and r['paLate'] == r['late'], f'{tag}: {uid} Mine and Ask read the same items ({r})')
        c.ok(all(n == r['late'] or (r['late'] == 0 and re.search(r'\b(no|nothing|none|0)\b', h, re.I)) for n, h in zip(nums, r['h'])), f'{tag}: {uid} Ask gives one late number however it is asked ({r["h"]}, Mine {r["late"]})')
        c.ok(r['caught'] == r['late'], f'{tag}: {uid} Today\'s Tasks (by user id) count the same late tasks as Mine ({r["caught"]} vs {r["late"]})')

async def money_checks(c, pg, tag):
    await sign_in(pg, 'u_owner')
    # 3. AMP-311 (dated 9/2) is not paid by the 8/15 check; the check reads Not Matched everywhere
    r = await pg.evaluate("""() => { const b = DB.bills.find(x => x.number === 'AMP-311'), t = DB.txns.find(x => x.id === 't5');
      const caught = tdCaught([]).filter(x => x.key === 'um:' + t.id).map(x => x.what);
      return { paid: !!billPaidTxn(b), pbu: billPaidUnapproved(b), state: billState(b).text, unm: txnUnmatched(t), caught, linked: t.billId || '' }; }""")
    c.ok(not r['paid'] and not r['pbu'] and 'Paid' not in r['state'], f'{tag}: AMP-311 is not paid by a bank line dated before it ({r})')
    c.ok(not r['linked'] and bool(r['unm']) == bool(r['caught']) and (not r['caught'] or r['caught'][0].startswith('Not matched')), f'{tag}: the 8/15 check is linked to no bill, and Caught says what Controls says about it ({r})')
    r = await pg.evaluate("""() => { const ex = new Set(openExceptions().map(t => t.id)), C = new Set(tdCaught([]).filter(x => /^um:/.test(x.key)).map(x => x.key.slice(3)));
      const U = bankUnmatched().rows.filter(t => !t.exception).map(t => t.id); return { missingCtl: U.filter(id => !ex.has(id)), missingCaught: U.filter(id => !C.has(id)) }; }""")
    c.ok(not r['missingCtl'] and not r['missingCaught'], f'{tag}: every unmatched bank line is the same line in Caught for You and in Controls ({r})')
    r = await pg.evaluate("""() => { const b = DB.bills.find(x => x.number === 'WW-2026-118'), t = billPaidTxn(b);
      const row = t ? tdCaught([]).find(x => x.key === 'um:' + t.id) : null; return { t: t && t.id, pbu: billPaidUnapproved(b), row: row && row.what }; }""")
    c.ok(r['t'] and r['pbu'] and r['row'] and r['row'].startswith('Paid before approval'), f'{tag}: the Amex line that paid WW-2026-118 says so in Caught, as the bill does ({r})')
    # a person may match an earlier line to a bill only with a reason
    r = await pg.evaluate("""() => { const b = DB.bills.find(x => x.number === 'AMP-311'), t = DB.txns.find(x => x.id === 't5');
      const a = truthSetMatch(t, { billId: b.id }, {}); const linked1 = t.billId === b.id;
      const z = truthSetMatch(t, { billId: b.id }, { earlyWhy: 'test: the check was post-dated by the vendor' });
      const out = { refused: !a.ok && !!a.early, linked1, ok: z.ok, paid: !!billPaidTxn(b), why: (b.earlyMatch || {}).why || '' };
      return out; }""")
    c.ok(r['refused'] and not r['linked1'], f'{tag}: matching a bank line to a later bill is refused without a reason ({r})')
    c.ok(r['ok'] and r['paid'] and r['why'], f'{tag}: with a reason it matches, and the reason is kept ({r})')

async def hold_run_checks(c, pg, tag):
    await sign_in(pg, 'u_owner')
    # 3 and 7: a held bill reads Held wherever it is listed and never sits in a Payment Run; a paid bill neither
    r = await pg.evaluate("""() => { const W = DB.bills.find(x => x.number === 'WW-2026-118');
      const n = JSON.parse(JSON.stringify(DB.bills.find(x => x.vendor === 'Carlos Millwork')));
      Object.assign(n, { id: 'b_s1run', number: 'CM-S1', status: 'approved', date: today(), approvedAt: today(), createdBy: 'Chen', poId: '' });
      delete n.txnId; delete n.paidAt; DB.bills.push(n);
      const before = pcRunnable(n);
      n.onHold = { why: 'waiting on the signed delivery ticket', by: 'Owner', at: appNowIso(), for: 'Chen Biron', state: 'open' };
      W.onHold = { why: 'check the extra window CO', by: 'Owner', at: appNowIso(), for: 'Alan', state: 'open' };
      save(); return { before, held: pcRunnable(n), paidRun: pcRunnable(W), state: billState(n).text, check: pcCheck(n).holds.map(h => h.key) }; }""")
    c.ok(r['before'] and not r['held'] and not r['paidRun'], f'{tag}: an approved bill is runnable until it is held; a bill the bank paid never is ({r})')
    c.ok(r['state'].startswith('Held by Owner') and 'held' in r['check'], f'{tag}: a held bill reads Held with who, and the Payment Check holds it ({r})')
    await go(pg, 'ap'); await pg.wait_for_timeout(400)
    r = await pg.evaluate("""() => { const v = document.getElementById('v-ap'), run = v.querySelector('#pc-run'), pbu = v.querySelector('#fin-pbu');
      return { run: run ? run.innerText : '', pbu: pbu ? pbu.innerText : '', all: v.innerText }; }""")
    c.ok('CM-S1' not in r['run'] and 'WW-2026-118' not in r['run'] and 'AMP-311' not in r['run'], f'{tag}: the Payment Run holds no held or already-paid bill ({r["run"][:300]})')
    c.ok('Held by Owner' in r['pbu'], f'{tag}: the paid-before-approval list shows the owner\'s hold on its row ({r["pbu"][:300]})')
    c.ok(await pg.evaluate("() => !document.documentElement.scrollWidth || document.documentElement.scrollWidth <= innerWidth + 1"), f'{tag}: Bills & Payroll does not scroll sideways')
    await pg.evaluate("() => { DB.bills = DB.bills.filter(b => b.id !== 'b_s1run'); const W = DB.bills.find(x => x.number === 'WW-2026-118'); delete W.onHold; save(); }")

async def controls_checks(c, pg, tag):
    await sign_in(pg, 'u_owner')
    # 4. Controls counts the lines matched to nothing; never a green 0 before verification has run
    r = await pg.evaluate("""() => { delete DB.lastVerify; const T = TL_SETS.verify(), e = T.find(x => x.key === 'exc'), U = bankUnmatched();
      // the tile's filter runs on the grid's rows ({t, v, worst}), as a tap on it does
      const shown = DB.txns.filter(t => e.pred({ t: t, v: { ex: [] }, worst: 0 })).length;
      return { v: e.v, s: e.s, n: openExceptions().length, shown, unm: U.rows.filter(t => !t.exception).length, amt: U.amt }; }""")
    c.ok(r['shown'] == r['v'], f'{tag}: tapping Exceptions Open shows as many lines as it counts ({r["shown"]} vs {r["v"]})')
    c.ok(r['v'] == r['n'] and r['v'] >= r['unm'] and r['unm'] > 0, f'{tag}: Exceptions Open counts every line matched to nothing ({r})')
    c.ok('not yet verified' in r['s'] and 'every cleared line is explained' not in r['s'], f'{tag}: before verification runs it says so ({r["s"]})')
    await go(pg, 'verify'); await pg.wait_for_timeout(400)
    r = await pg.evaluate("""() => { const v = document.getElementById('v-verify'); return { t: v ? v.innerText : '', rows: v ? v.querySelectorAll('#vf-table [data-vfrespond]').length : -1, n: openExceptions().length } }""")
    c.ok('every cleared line is explained' not in r['t'] and 'Not yet verified' in r['t'], f'{tag}: Controls never reads all clear while lines are unmatched ({r["t"][:300]})')
    c.ok(r['rows'] == r['n'], f'{tag}: the open list shows as many lines as the tile counts ({r["rows"]} vs {r["n"]})')

async def coi_checks(c, pg, tag):
    # 5. Window Works' COI lapsed 8/15 and they are booked on site 9/9: owner and coordinator see it first thing
    r = await pg.evaluate("""() => PRED.vendorsCoiLapsing.rows().map(r => [r.v.name, r.state, r.next.date, r.soon])""")
    ww = [x for x in r if x[0] == 'Window Works']
    c.ok(ww and ww[0][1] == 'expired' and ww[0][3], f'{tag}: Window Works is flagged: COI expired, on site within 10 working days ({r})')
    for uid in ('u_owner', 'u_chen'):
        await sign_in(pg, uid); await go(pg, 'home'); await pg.wait_for_timeout(300)
        r = await pg.evaluate("""() => tdCaught([]).filter(x => x.src === 'compliance').map(x => x.what)""")
        c.ok(any('Window Works' in x and 'COI expired' in x for x in r), f'{tag}: {uid} Caught for You has Window Works\' lapsed COI ({r})')
    # within 30 days counts; a vendor with nothing booked does not
    r = await pg.evaluate("""() => { const v = DB.vendors.find(x => x.name === 'Carlos Millwork'), was = v.insuranceExp; v.insuranceExp = iso(addDays(today(), 20));
      const hit = !!PRED.vendorsCoiLapsing.row(v), st = (PRED.vendorsCoiLapsing.row(v) || {}).state;
      const n = DB.vendors.find(x => x.name === 'Nemo Tile'), was2 = n.insuranceExp; n.insuranceExp = iso(addDays(today(), 10));
      const pos = (DB.pos || []).filter(p => p.vendor === 'Nemo Tile' && ['issued', 'partial', 'pending'].includes(p.status)).length, sub = ((DB.field || {}).subs || []).filter(s => s.vendor === 'Nemo Tile' && s.date >= today()).length;
      const nemo = !!PRED.vendorsCoiLapsing.row(n); v.insuranceExp = was; n.insuranceExp = was2; return { hit, st, nemo, booked: pos + sub }; }""")
    c.ok(r['hit'] and r['st'] == 'lapsing', f'{tag}: a COI lapsing in 20 days for a sub on site is flagged ({r})')
    c.ok(r['nemo'] == (r['booked'] > 0), f'{tag}: a vendor is flagged only with a booking or an order ahead ({r})')
    # the owner chases it; the follow-up waits on the coordinator (the office keeps certificates current), not the owner
    await sign_in(pg, 'u_owner')
    r = await pg.evaluate("""async () => { const c = tdChase().find(x => x.kind === 'coi' && /Window Works/.test(x.t)); if (!c) return null;
      eaNudge(c); await new Promise(r => setTimeout(r, 300)); document.getElementById('mbm-ok').click(); await new Promise(r => setTimeout(r, 400));
      const mine = (uid) => tkAll({ open: true, uid }).filter(t => t.kind === 'note' && /Window Works/.test(t.title)).length;
      return { owner: mine('u_owner'), coord: mine('u_chen') }; }""")
    c.ok(r and r['coord'] == 1 and r['owner'] == 0, f'{tag}: the COI chase\'s follow-up is on the coordinator\'s list, not the owner\'s ({r})')

async def risk_checks(c, pg, tag):
    await sign_in(pg, 'u_owner')
    # 6. the headline reads the at-risk rule
    r = await pg.evaluate("""() => PRED.jobsAtRisk.rows().map(r => ({ p: r.p.project.name, holds: r.holds, by: r.by, daysLeft: r.daysLeft, slip: r.slip, n: r.risks.length, kinds: r.risks.map(x => x.kind), worst: r.worst, test: PRED.jobsAtRisk.test(r.p) }))""")
    s121 = [x for x in r if x['p'].startswith('121 State')]
    c.ok(s121 and s121[0]['n'] >= 2 and 'decision' in s121[0]['kinds'] and s121[0]['test'], f'{tag}: 121 State is at risk: overdue decisions hold its trades ({s121})')
    c.ok(s121 and s121[0]['holds'] and s121[0]['by'] and s121[0]['daysLeft'] is not None, f'{tag}: the worst risk names the line it holds, when it starts and the days left ({s121})')
    for v in ('port', 'dash', 'home'):
        await pg.evaluate("v => { if (v === 'dash' && typeof dashAll !== 'undefined') dashAll = true; view = v; render(); }", v); await pg.wait_for_timeout(500)
        t = await pg.evaluate("() => document.querySelector('main') ? document.querySelector('main').innerText : document.body.innerText")
        c.ok('every finish date holds' not in t and not re.search(r'(\d+) of \1 on time', t), f'{tag}: {v} does not say every job is on time while one is at risk')
    t = await pg.evaluate("() => { const T = (typeof OV_TILES === 'object' && OV_TILES.jobs) ? OV_TILES.jobs((typeof ovRows === 'function' ? ovRows('jobs') : []) || []) : []; return T.map(x => x.k + ': ' + x.v + ' · ' + x.s).join(' | ') }")
    c.ok('every finish date holds its target' not in t, f'{tag}: Finish Dates Late says how many jobs are at risk ({t[:300]})')

async def portal_checks(c, pg, tag):
    # 8. the client reads what was billed and what is done on site, and why they differ, in plain words
    await sign_in(pg, 'u_klein'); await go(pg, 'home'); await pg.wait_for_timeout(500)
    t = await pg.evaluate("() => document.body.innerText")
    c.ok('certified' not in t.lower(), f'{tag}: the portal does not use "certified" for what was billed')
    m = re.search(r'\d+% of the contract[^\n]*', t)
    c.ok(m and re.search(r'\d+% (of the work )?complete on site', t), f'{tag}: the portal names what was billed and what is complete on site plainly ({m.group(0) if m else t[:300]})')
    c.ok(re.search(r'billing is ahead of the work', t, re.I), f'{tag}: a gap between billed and complete on site is explained on the portal')

async def main():
    c = Checks()
    async with async_playwright() as p:
        for phone in (False, True):
            tag = 'phone' if phone else 'desktop'
            # the phone runs the screens a person meets there; the rules behind them run once, on the desktop
            fns = (chase_checks, hold_run_checks, controls_checks, coi_checks, risk_checks, portal_checks) if phone else (chase_checks, owner_checks, money_checks, hold_run_checks, controls_checks, coi_checks, risk_checks, portal_checks)
            for fn in fns:
                b, pg, errs = await open_app(p, phone)
                try:
                    await fn(c, pg, tag)
                except Exception as e:
                    c.ok(False, f'{tag}: {fn.__name__} threw {str(e)[:300]}')
                c.ok(not errs, f'{tag}: {fn.__name__}: no page errors ({errs[:3]})')
                await b.close()
    return c.done()

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
