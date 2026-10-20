"""Who releases the Payment Run (Alan, 2026-10-20: "Go" on the recommendation). The controller keys every bill and the
person who keyed a bill can never release its payment, so the controller prepares the weekly run and the owner
releases it in one tap; billing releases it while the owner is away. Desktop and phone.
Run: python3 payrun_test.py"""
import asyncio
from harness import async_playwright, open_app, sign_in, Checks

# two approved bills from a vendor with its papers on file, keyed by the coordinator (the demo has none approved)
SETUP = """() => { const v = DB.vendors.find(x => x.name === 'Nemo Tile'); v.w9 = true; v.w9On = today();
  const src = DB.bills.find(b => b.vendor === 'Nemo Tile');
  [['bill_pr1', 'NT-9001', 0.37], ['bill_pr2', 'NT-9002', 0.21]].forEach(([id, no, f]) => { const b = JSON.parse(JSON.stringify(src));
    Object.assign(b, { id: id, number: no, status: 'approved', createdBy: 'Chen', approvedAt: today(), date: today(), poId: '' });
    (b.lines || []).forEach(l => { if (l.rate) l.rate = Math.round(l.rate * f * 100) / 100; if (l.amount) l.amount = Math.round(l.amount * f * 100) / 100; });
    ['paidAt', 'txnId'].forEach(k => delete b[k]); DB.bills.push(b); });
  save(); return ['bill_pr1', 'bill_pr2'].map(id => pcCheck(DB.bills.find(b => b.id === id)).pass) }"""
PASSING = """() => (DB.bills || []).filter(b => b.status === 'approved' && billTotal(b) > 0 && pcOpen(b) > 0.005 && !b.ic)
  .map(b => ({ id: b.id, pass: pcCheck(b).pass, open: pcOpen(b) }))"""

async def main():
    c = Checks()
    async with async_playwright() as p:
        for phone in (False, True):
            tag = 'phone' if phone else 'desktop'
            b, pg, errs = await open_app(p, phone)
            # the controller sees Prepare the Run, not Pay
            c.ok(await pg.evaluate(SETUP) == [True, True], f'{tag}: two approved bills that pass the check')
            await sign_in(pg, 'u_controller')
            await pg.evaluate("() => { view = 'ap'; render(); }"); await pg.wait_for_timeout(300)
            r = await pg.evaluate("() => { const g = document.getElementById('pc-run-go'); return { txt: g && g.textContent, n: document.querySelectorAll('[data-pcrun]:checked').length } }")
            c.ok(r['txt'] == 'Prepare the Run' and r['n'] >= 1, f'{tag}: the controller prepares the run ({r})')
            ids = await pg.evaluate("() => [...document.querySelectorAll('[data-pcrun]:checked')].map(x => x.dataset.pcrun)")
            paid0 = await pg.evaluate("() => (DB.payments || []).length")
            await pg.click('#pc-run-go'); await pg.wait_for_timeout(300)
            await pg.click('#mbm-ok'); await pg.wait_for_timeout(500)
            r = await pg.evaluate("() => { const R = (DB.payRuns || []).filter(x => x.status === 'prepared'); return { n: R.length, total: R[0] && R[0].total, by: R[0] && R[0].preparedBy, bills: R[0] && R[0].bills.length, toast: document.getElementById('toast').innerText } }")
            c.ok(r['n'] == 1 and r['bills'] == len(ids) and 'sent to the owner' in r['toast'], f'{tag}: prepared, sent to the owner, nothing paid yet ({r})')
            c.ok(await pg.evaluate("() => (DB.payments || []).length") == paid0, f'{tag}: preparing pays nothing')
            # the owner: one card in Approvals, released in one tap; every bill checked again and recorded by the owner
            await sign_in(pg, 'u_owner')
            r = await pg.evaluate("() => mApprovals().filter(x => x.kind === 'payrun').map(x => [x.title, x.n, x.who])")
            c.ok(len(r) == 1 and r[0][2] == 'owner', f'{tag}: one Payment Run card in the owner Approvals ({r})')
            c.ok(await pg.evaluate("() => { signIn('u_controller'); const n = mApprovals().filter(x => x.kind === 'payrun').length; signIn('u_owner'); return n }") == 0, f'{tag}: not in the controller Approvals')
            await pg.evaluate("() => { view = 'mapprove'; render(); }"); await pg.wait_for_timeout(300)
            hit = await pg.evaluate("() => { const el = document.querySelector('.m-appr[data-mk=\"payrun\"] [data-myes]'); if (el) el.click(); return !!el }")
            await pg.wait_for_timeout(600)
            r = await pg.evaluate("""() => { const run = (DB.payRuns || [])[0]; const P = (DB.payments || []).filter(x => x.run === run.id);
              return { st: run.status, by: run.releasedBy, me: currentUser().name, n: P.length, payBy: [...new Set(P.map(x => x.by))], paid: run.paid, total: run.total, checked: P.every(x => x.check && x.check.pass), toast: document.getElementById('toast').innerText } }""")
            c.ok(hit and r['st'] == 'released' and r['n'] >= 1 and r['payBy'] == [r['me']] and r['by'] == r['me'], f'{tag}: released in one tap from Approvals, recorded by the owner ({r})')
            c.ok(r['checked'] and abs(r['paid'] - r['total']) < 0.01 and 'Payment Run released' in r['toast'], f'{tag}: every bill checked again and paid to the cent ({r})')
            # away: billing releases; back: the owner again
            await pg.evaluate("() => { DB.company.ownerAway = { from: today(), to: '2026-09-10', by: 'Alan' }; DB.payRuns.push({ id: 'prun_t2', status: 'prepared', bills: [], date: today(), method: '', total: 0, preparedBy: 'Chen Biron', preparedAt: appNowIso() }); save(); }")
            r = await pg.evaluate("() => { signIn('u_billing'); const b = mApprovals().filter(x => x.kind === 'payrun').length; signIn('u_owner'); const o = mApprovals().filter(x => x.kind === 'payrun').length; return [b, o] }")
            c.ok(r == [1, 0], f'{tag}: while the owner is away, billing releases the run, not the owner ({r})')
            # a returned run says why, to the person who prepared it
            await pg.evaluate("() => { delete DB.company.ownerAway; save(); signIn('u_owner'); prReturn('prun_t2'); }"); await pg.wait_for_timeout(200)
            await pg.fill('#mbm [data-f="why"]', 'Hold Window Works until the credit lands'); await pg.click('#mbm-ok'); await pg.wait_for_timeout(300)
            r = await pg.evaluate("() => { const x = DB.payRuns.find(r => r.id === 'prun_t2'); return [x.status, x.why] }")
            c.ok(r == ['returned', 'Hold Window Works until the credit lands'], f'{tag}: returned with the reason ({r})')
            # "what we owe" is approved bills (the ledger's 2000); bills awaiting approval are their own line (Alan, 2026-10-20)
            r = await pg.evaluate("""() => { signIn('u_owner'); const O = apOpenBills(), I = ASK_INTENTS.find(x => x.id === 'payables').answer();
              view = 'reports'; try { repTab = 'statements'; } catch (e) {} render(); const t = document.querySelector('section.view.on').innerText;
              return { appr: O.approved, wait: O.awaiting, head: I.headline, total: I.total, bsAppr: /Accounts payable \(approved bills\)/.test(t), bsWait: O.awaiting > 0 ? /Bills awaiting approval \(accrued\)/.test(t) : true } }""")
            c.ok(r['total'] == r['appr'] and ('awaits approval' in r['head']) == (r['wait'] > 0), f'{tag}: Ask says we owe the approved bills, and names the bills awaiting approval apart ({r})')
            sw = await pg.evaluate("() => document.documentElement.scrollWidth")
            if phone: c.ok(sw <= 390, f'{tag}: no sideways scroll ({sw})')
            c.ok(not errs, f'{tag}: page errors {errs[:2]}')
            await b.close()
    print(f'{len(c.fail)} FAILED ({c.n} checks)' if c.fail else f'ALL PASS ({c.n} checks)')
    raise SystemExit(1 if c.fail else 0)

asyncio.run(main())
