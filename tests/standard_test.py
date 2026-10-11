"""The SmartDesign Standard, live in the app (docs/STANDARD.md; Settings › The SmartDesign Standard).

Record: version 1 is seeded from the document word for word (every section round-trips to its markdown), the hash
chain verifies; the owner's edit makes version 2 with who, when and why and the chain still verifies; tampering with
a stored version breaks Verify; a PM cannot edit.
Assistant: mindSystem() carries the live Standard (an edited value shows at once), the AI section, and only the
signed-in role's playbook (the PM's prompt has the PM playbook, not the foreman's); the untrusted-data rule holds.
Because and ranking: every CATCH id, DELEGATION kind and LEARN_EVENTS kind is mapped to a line of the Standard;
Do Now and Caught for You are ordered by decision principle and keep their counts; a money-leak catch carries
Alan's line on wasted money; the escalation format has its five parts and the table row.
Guard: the local Ask answers the values question and will not pay, send to a client or delete a transaction on
its own (it cites the AI playbook), refuses to skip a change order; mindTool refuses a "Never" and turns money
into a proposal; sending alone needs a delegated message type; a brain lesson that would act alone is dropped.
Client: the portal routes scope and price to the PM and never opens the Standard.
Standard Watch: each rule's count equals the rows it opens; the not-measured list is shown.
Procurement: a PO's sourcing choice and a vendor's region persist after a reload.
Screen: no sideways scroll at 390px; one blue button while editing."""
import asyncio, os, re
from harness import *

HERE = os.path.dirname(os.path.abspath(__file__))
MD = open(os.path.join(HERE, '..', 'docs', 'STANDARD.md'), encoding='utf-8').read()


def norm(s):
    return '\n'.join(l.rstrip() for l in s.split('\n') if l.strip())


async def main():
    c = Checks()
    async with async_playwright() as p:
        b, pg, errs = await open_app(p)
        await sign_in(pg, 'u_owner')
        # ---- the record, seeded word for word
        r = await pg.evaluate("""() => { const B = standard(), v = DB.company.standard;
          return { emb: STANDARD_MD(), v: v.version, ver: standardVerify(), values: B.values.map(x => x.id), pr: B.principles.map(x => x.id),
            areas: B.standards.areas.map(a => a.id), pbs: Object.keys(B.playbooks), esc: B.escalation.length,
            md: standardSectionKeys(B).map(k => [k, standardSectionMd(B, k)]) }; }""")
        c.ok(norm(r['emb']) == norm(MD), 'the page carries docs/STANDARD.md as written')
        c.ok(r['v'] == 1 and r['ver']['ok'], f"seed: version {r['v']}, chain {r['ver']['text']}")
        c.ok(r['values'] == ['own', 'client', 'craft', 'ahead', 'dollar', 'truth', 'team'], f"values {r['values']}")
        c.ok(r['pr'] == ['safety', 'law', 'integrity', 'quality', 'client', 'schedule', 'cost'], f"principles {r['pr']}")
        c.ok(r['areas'] == ['communication', 'documentation', 'jobsite', 'quality', 'money', 'conduct'], f"standards {r['areas']}")
        c.ok(sorted(r['pbs']) == sorted(['client', 'pm', 'procurement', 'foreman', 'crew', 'designer', 'estimating', 'office', 'ai']), f"playbooks {r['pbs']}")
        c.ok(r['esc'] == 10, f"escalation rows {r['esc']}")
        bad = [k for k, m in r['md'] if norm(m) not in norm(MD)]
        c.ok(not bad, f'sections that do not round-trip to the document word for word: {bad}')
        # ---- the owner edits through the page: version 2 with who, when and why
        await go(pg, 'standard'); await pg.wait_for_timeout(300)
        await pg.click('#standard-body [data-chedit]'); await pg.wait_for_timeout(200)
        prim = await pg.evaluate("() => [...document.querySelectorAll('.view.on .btn.primary')].filter(b => b.getClientRects().length).map(b => b.innerText)")
        c.ok(prim == ['Publish Version 2'], f'edit mode: one blue button, Publish Version 2 ({prim})')
        await pg.evaluate("""() => { const t = document.querySelector('[data-chsec="values"]'); t.value = t.value.replace('### 1. Own it', '### 1. Own it, always'); }""")
        await pg.click('#standard-body [data-chpublish]'); await pg.wait_for_timeout(200)
        v1 = await pg.evaluate("() => DB.company.standard.version")
        c.ok(v1 == 1, 'Publish without a why is refused')
        await pg.fill('#standard-body [data-chf="why"]', 'test: the first value reads stronger')
        await pg.click('#standard-body [data-chpublish]'); await pg.wait_for_timeout(300)
        r = await pg.evaluate("""() => { const v = DB.company.standard; return { v: v.version, by: v.by, at: v.at, why: v.why, prev: v.prev, h1: DB.company.standardVersions[0].hash,
          name: standard().values[0].name, id: standard().values[0].id, ok: standardVerify().ok, toast: (document.getElementById('toast') || {}).innerText || '',
          sys: mindSystem() }; }""")
        c.ok(r['v'] == 2 and r['by'] == 'Owner' and r['why'].startswith('test:') and r['at'].startswith('2026-09-03') and r['prev'] == r['h1'], f"version 2: {r['v']} {r['by']} {r['at']} {r['why']}")
        c.ok(r['name'] == 'Own it, always' and r['id'] == 'own', f"the edited value keeps its id: {r['id']} {r['name']}")
        c.ok(r['ok'], 'the chain verifies after the edit')
        c.ok('version 2' in r['toast'] and 'Open' in r['toast'], f"toast with Open: {r['toast']!r}")
        c.ok('Own it, always' in r['sys'], 'mindSystem reads the live Standard (the edited value is in the prompt)')
        # tamper with a stored version: Verify fails
        t = await pg.evaluate("""() => { const V = DB.company.standardVersions[0], keep = V.body.values[0].line; V.body.values[0].line = 'Do whatever is fastest.';
          const a = standardVerify(); V.body.values[0].line = keep; return { bad: a.ok, text: a.text, after: standardVerify().ok }; }""")
        c.ok(not t['bad'] and 'version 1' in t['text'] and t['after'], f"tampering breaks Verify: {t['text']}")
        await pg.click('#standard-body [data-chverify]'); await pg.wait_for_timeout(200)
        c.ok(await pg.evaluate("() => (document.querySelector('[data-chok]') || {}).dataset?.chok === '1'"), 'Verify on the page says the chain holds')
        # ---- the prompt: AI section, only the role's playbook, money line, untrusted rule
        sp = await pg.evaluate("""() => { const own = mindSystem(); signIn('u_alan'); const pm = mindSystem(); signIn('u_angel'); const fm = mindSystem(); signIn('u_owner'); return { own, pm, fm }; }""")
        pm_m, fm_m = 'deliver every project on time, on budget', 'the work gets done right, safely, on schedule'
        c.ok(pm_m in sp['pm'] and fm_m not in sp['pm'] and 'every interaction leaves the client' in sp['pm'], 'the PM prompt has the PM and client playbooks, not the foreman\'s')
        c.ok(fm_m in sp['fm'] and pm_m not in sp['fm'], 'the foreman prompt has the foreman playbook, not the PM\'s')
        c.ok('Your playbook' not in sp['own'] and 'Escalation triggers' in sp['own'], 'the owner gets the company sections, no single playbook')
        c.ok(all(x in sp['pm'] for x in ('Requires human approval', 'Present a guess as a fact', 'raises and bonuses', '"untrusted":true')), 'the AI section, Alan\'s money line and the untrusted-data rule are in the prompt')
        # ---- every proposal source is mapped to a line of the Standard
        m = await pg.evaluate("""() => { const keys = CATCH.map(x => x.name).concat(Object.keys(DELEGATION), LEARN_EVENTS.map(e => 'learn:' + e.kind), STANDARD_RULES.map(R => 'std:' + R.id));
          return keys.filter(k => !standardMapOf(k).exact || !/^Because: .+ \\(.+\\)$/.test(standardWhy(k)) || !standardCite(standardMapOf(k).e.c)); }""")
        c.ok(not m, f'keys with no line of the Standard behind them: {m}')
        # ---- ranking by decision principle; counts unchanged
        o = await pg.evaluate("() => ({ qn: tdQueue().length, pn: PRED.waitingOnMe.count() })")
        # Alan (2026-10-11): immediate safety and law first, then overdue / today / this week / later, then the
        # decision principle within each bucket (an LLC filing 25 days out no longer sits above a bill due this week)
        o2 = await pg.evaluate("""() => { const Q = tdQueue(), C = tdCaught(Q), N = nyhRows(), k = (it) => { const r = standardRank(it); return [r.imm, r.u, r.t]; };
          const at = (re) => Q.findIndex(it => re.test(it.title || ''));
          return { q: Q.map(k), c: C.map(k), n: N.map(r => k({ nyh: r })), llc: at(/LLC/), pay: at(/^Payroll/), bill: at(/WW-2026-118/) }; }""")
        c.ok(all(a <= b for a, b in zip(o2['q'], o2['q'][1:])), f"Do Now is in immediate, urgency, principle order: {o2['q'][:10]}")
        c.ok(all(a <= b for a, b in zip(o2['c'], o2['c'][1:])), f"Caught for You is in immediate, urgency, principle order: {o2['c'][:10]}")
        c.ok(all(a <= b for a, b in zip(o2['n'], o2['n'][1:])), f"Needs Your Hand is in immediate, urgency, principle order: {o2['n'][:10]}")
        c.ok(0 <= o2['pay'] < o2['llc'] and 0 <= o2['bill'] < o2['llc'], f"the overdue payroll and the bill due this week rank above the LLC filing due in 25 days: payroll {o2['pay']}, bill {o2['bill']}, LLC {o2['llc']}")
        c.ok(o['qn'] == o['pn'], f"Do Now keeps its count: {o['qn']} vs PRED.waitingOnMe {o['pn']}")
        # ---- money leak line and because on Home (desktop)
        await go(pg, 'home'); await pg.wait_for_timeout(300)
        await pg.evaluate("() => { tdCatchAll = true; render(); }"); await pg.wait_for_timeout(300)
        h = await pg.evaluate("""() => { const cards = [...document.querySelectorAll('.view.on .td-catch .td-card')];
          return { n: cards.length, why: cards.filter(x => x.querySelector('.ch-why')).length, leak: cards.filter(x => ['earnedNotBilled', 'costNotBilled', 'overPO', 'budgetOverrun', 'unmatchedCredit'].includes(x.dataset.src)).map(x => (x.querySelector('.std-waste') || {}).innerText || ''),
            doWhy: [...document.querySelectorAll('.view.on .td-do .td-card')].every(x => /^Because: /.test((x.querySelector('.ch-why') || {}).innerText || '')) }; }""")
        c.ok(h['n'] and h['why'] == h['n'] and h['doWhy'], f"every Do Now and Caught for You card says why: {h['why']}/{h['n']}")
        c.ok(h['leak'] and all('raises, bonuses' in x for x in h['leak']), f"money-leak catches carry the wasted-money line: {h['leak'][:2]}")
        await pg.evaluate("() => { tdCatchAll = false; }")
        # ---- escalation format
        e = await pg.evaluate("""() => { const E = standardEscalation({ src: 'budgetOverrun', what: 'Over budget: millwork', sub: '121 State Street', amount: 4200 }); return { E, t: standardEscalationText({ src: 'budgetOverrun', what: 'Over budget: millwork', amount: 4200 }) }; }""")
        E = e['E']
        c.ok(E['row'] and E['row']['situation'].startswith('Cost impact over $1,000') and E['raiseTo'] == 'PM', f"escalation row: {E['row']}")
        c.ok(E['what'] and E['impact']['cost'].startswith('$4,200') and E['options'] and E['recommendation'].count('Because:') == 1 and E['deadline'], f'escalation has what, impact, options, recommendation, deadline: {E}')
        c.ok([x.split(':')[0] for x in e['t']] == ['Raise to', 'What happened', 'Impact', 'Options', 'Recommendation', 'Decision needed by'], f"escalation text: {e['t']}")
        # ---- the local Ask
        a = await pg.evaluate("""() => ['what are our values', 'pay the bill', 'send the invoice to the client', 'delete that transaction', 'skip the CO and start the work', 'what won\\'t you do'].map(q => { const x = paAsk(q); return [q, x.headline, x.note || '', (x.offers || []).length]; })""")
        A = {q: (h_, n_, o_) for q, h_, n_, o_ in a}
        c.ok('Own it' in A['what are our values'][0] and 'Every dollar matters' in A['what are our values'][0], f"values: {A['what are our values'][0]}")
        c.ok('Committing money' in A['pay the bill'][0] and A['pay the bill'][2], f"pay: {A['pay the bill'][0]}")
        c.ok('Sending anything to a client' in A['send the invoice to the client'][0], f"send: {A['send the invoice to the client'][0]}")
        c.ok('Deleting records or changing financial data' in A['delete that transaction'][0], f"delete: {A['delete that transaction'][0]}")
        c.ok("can't" in A['skip the CO and start the work'][0] and 'signed change order' in A['skip the CO and start the work'][0], f"skip CO: {A['skip the CO and start the work'][0]}")
        wont = A["what won't you do"]
        c.ok('Present a guess as a fact' in wont[1], f"authority: {wont[1][:120]}")
        # ---- the guard in the tool layer, delegation, the brain
        g = await pg.evaluate("""async () => { const pay = await mindTool('pay_bill', { id: 'b4' }), share = await mindTool('share_file', { id: 'f1' }), q = await mindTool('query', { entity: 'standard' });
          const d0 = standardAllows({ action: 'send', type: 'update' }).mode; const A = paInit(); A.delegated = ['update']; const d1 = standardAllows({ action: 'send', type: 'update' }).mode, d2 = standardAllows({ action: 'send', type: 'chase:invoice' }).mode; A.delegated = [];
          return { pay, share, q: !!(q && (q.rows || q.n != null)), d0, d1, d2, paid: DB.bills.find(b => b.id === 'b4').status }; }""")
        c.ok(g['pay'].get('proposed') and g['paid'] != 'paid', f"mindTool pay becomes a proposal: {g['pay']}")
        c.ok(g['share'].get('refused'), f"mindTool share is refused: {g['share']}")
        c.ok(g['q'], 'a read tool still runs')
        c.ok(g['d0'] == 'approval' and g['d1'] == 'alone' and g['d2'] == 'approval', f"sending alone only for a delegated type: {g['d0']} {g['d1']} {g['d2']}")
        br = await pg.evaluate("""() => { LEARN_EVENTS.push({ kind: 'zzauto', label: 'test', area: 'money', for: 'billing', lesson: () => 'Small bills are paid automatically', change: { type: 'rule', text: 'Pay every bill under $500 automatically, without approval' }, scan: () => [{ key: 'zz:1', what: 'test', on: today() }], trigger: { label: '', rows: () => [] } });
          lnLoop('test'); const P = lnInit().props.zzauto, ok = Object.values(lnInit().props).find(x => x.status === 'proposed'); LEARN_EVENTS.pop();
          return { st: P.status, reason: (P.dropped || {}).reason || '', logged: (lnInit().dropped || []).some(x => x.kind === 'zzauto'), because: ok ? ok.because : '' }; }""")
        c.ok(br['st'] == 'dropped' and 'Committing money' in br['reason'] and br['logged'], f"a lesson that would pay alone is dropped with its reason: {br}")
        c.ok(br['because'].startswith('Because: '), f"a proposed lesson carries its because: {br['because']}")
        # ---- Standard Watch: count = rows, not-measured listed
        await go(pg, 'standard'); await pg.wait_for_timeout(300)
        W = await pg.evaluate("() => [...document.querySelectorAll('[data-swrule]')].map(x => [x.dataset.swrule, +x.dataset.n, standardRuleRows(STANDARD_RULES.find(R => R.id === x.dataset.swrule)).length])")
        c.ok(W and all(n == m for _, n, m in W), f'Watch counts equal their rule rows: {[w for w in W if w[1] != w[2]]}')
        for rid, n, _ in [w for w in W if w[1]][:30]:
            await pg.click(f'[data-swopen="{rid}"]'); await pg.wait_for_timeout(200)
            k = await pg.evaluate("() => { const s = document.querySelector('#mbm [data-swsheet]'); return s ? [+s.dataset.n, s.querySelectorAll('.sw-sh-row').length] : null; }")
            c.ok(k and k[0] == n == k[1], f'Watch {rid}: says {n}, opens {k}')
            await pg.evaluate("() => mbCloseModal()"); await pg.wait_for_timeout(100)
        nm = await pg.evaluate("() => [...document.querySelectorAll('[data-swnotrule]')].map(x => x.dataset.swnotrule)")
        c.ok(nm == [R for R in await pg.evaluate("() => STANDARD_RULES.filter(R => R.measured === false).map(R => R.id)")] and nm, f'not measured yet, shown: {nm}')
        # ---- procurement: sourcing and region persist; the sourcing Watch drops by one
        n0 = await pg.evaluate("() => standardRuleRows(STANDARD_RULES.find(R => R.id === 'sourcingChoice')).length")
        await pg.evaluate("() => stdSourcingSheet(DB.pos.find(p => p.number === 'PO-2026-047'))"); await pg.wait_for_timeout(200)
        await pg.select_option('#mbm [data-f="sourcing"]', 'middleman'); await pg.fill('#mbm [data-f="sourcingWhy"]', 'one-off; the distributor holds stock')
        await pg.click('#mbm .btn.primary'); await pg.wait_for_timeout(300)
        await pg.evaluate("() => { const v = DB.vendors.find(x => x.name === 'Carlos Millwork'); openVendor(v.id); }"); await pg.wait_for_timeout(200)
        await pg.select_option('#e-region', 'tristate'); await pg.evaluate("() => saveVendor()"); await pg.wait_for_timeout(200)
        n1 = await pg.evaluate("() => standardRuleRows(STANDARD_RULES.find(R => R.id === 'sourcingChoice')).length")
        c.ok(n1 == n0 - 1, f'recording a choice takes the PO off the Watch: {n0} -> {n1}')
        await pg.evaluate("() => saveNow ? saveNow() : save()"); await pg.wait_for_timeout(600)
        await pg.reload(); await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
        await sign_in(pg, 'u_chen')
        pr = await pg.evaluate("() => ({ s: (DB.pos.find(p => p.number === 'PO-2026-047').sourcing || {}), r: DB.vendors.find(x => x.name === 'Carlos Millwork').region, v: DB.company.standard.version, eq: eqRows('vendors').find(x => x.name === 'Carlos Millwork').region, po: eqRows('purchaseorders').find(x => x.number === 'PO-2026-047').sourcing })")
        c.ok(pr['s'].get('choice') == 'middleman' and pr['s'].get('why', '').startswith('one-off'), f"sourcing persists after a reload: {pr['s']}")
        c.ok(pr['r'] == 'tristate' and pr['eq'] == 'NY-NJ-CT' and pr['po'] == 'Distributor or middleman', f"region persists and is queryable: {pr}")
        c.ok(pr['v'] == 2, f"the published version persists: {pr['v']}")
        # ---- a PM cannot edit
        await sign_in(pg, 'u_alan'); await go(pg, 'standard'); await pg.wait_for_timeout(300)
        ne = await pg.evaluate("() => { const btn = !!document.querySelector('#standard-body [data-chedit]'); const r = standardSave(Object.assign({}, standard(), { purpose: 'x' }), 'pm edit'); return { btn, r: !!r, v: DB.company.standard.version }; }")
        c.ok(not ne['btn'] and not ne['r'] and ne['v'] == 2, f'a PM cannot edit: {ne}')
        # ---- the client: no Standard, scope and price go to the PM
        await sign_in(pg, 'u_klein')
        cl = await pg.evaluate("() => ({ view: (ROLE_VIEWS.client || []).includes('standard'), rows: eqRows('standard').length, a: paAsk('can you add a closet to the guest bedroom').headline, d: paAsk('why is this so expensive').headline })")
        c.ok(not cl['view'] and cl['rows'] == 0, f"the client never opens the Standard: {cl}")
        c.ok('project manager' in cl['a'] and 'project manager' in cl['d'], f"the client's scope and price questions go to the PM: {cl['a']} / {cl['d']}")
        c.ok(not errs, f'page errors: {errs[:3]}')
        await b.close()
        # ---- phone: no sideways scroll, one blue button while editing
        for uid in ('u_owner', 'u_angel', 'u_chen'):
            b, pg, errs = await open_app(p, True)
            await sign_in(pg, uid); await go(pg, 'standard'); await pg.wait_for_timeout(400)
            ph = await pg.evaluate("() => ({ v: view, sw: document.documentElement.scrollWidth, h2: (document.querySelector('.view.on h2') || {}).innerText, prim: [...document.querySelectorAll('.view.on .btn.primary')].filter(b => b.getClientRects().length).length })")
            c.ok(ph['v'] == 'standard' and ph['sw'] <= 390 and ph['prim'] <= 1, f'{uid} phone: {ph}')
            if uid == 'u_owner':
                await pg.click('#standard-body [data-chedit]'); await pg.wait_for_timeout(300)
                ph = await pg.evaluate("() => ({ sw: document.documentElement.scrollWidth, prim: [...document.querySelectorAll('.view.on .btn.primary')].filter(b => b.getClientRects().length).length })")
                c.ok(ph['sw'] <= 390 and ph['prim'] == 1, f'owner phone, editing: {ph}')
            if uid == 'u_chen':
                await pg.evaluate("() => stdSourcingSheet(DB.pos[0])"); await pg.wait_for_timeout(300)
                ph = await pg.evaluate("() => document.documentElement.scrollWidth")
                c.ok(ph <= 390, f'the sourcing field fits at 390px ({ph})')
            c.ok(not errs, f'{uid} phone errors: {errs[:3]}')
            await b.close()
    return c.done()

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
