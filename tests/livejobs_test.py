"""Live jobs (BACKLOG §1.25, §1.26; Alan, 2026-10-17), walked as each person who touches them, desktop and phone.

The capabilities run on invented demo jobs behind the owner's switch (Settings), off by default:
 1. Two payers on one contract (88 Atlantic Ave: a landlord's base building, a tenant's bakery fit-out). Every SOV
    line, invoice, payment and change order knows its payer; aging, the Receivables report, statements and
    collections are per payer; each payer's portal shows only their share; a proposal is approved by each payer
    for their part; a progress invoice that holds two payers' lines is split, and a mixed invoice cannot be sent.
 2. Range estimates with allowances, and a paid exploratory phase (17 Rugby Road): phase 1 is the contract,
    discovery findings narrow the ranges, the client approves the construction phase and the contract grows by
    exactly its lines; an allowance over its budget raises a change order, an unused one a credit.
 3. A normal estimate end to end (214 Macon Street): the client approves in the portal, the contract and SOV are
    set, a deposit is invoiced and paid, a bill is coded to a line, and job cost, AR and Ask agree to the cent.
 4. The hard / soft / contingency estimate and the historic tax credit budget (Grace Chapel and Rectory): 20%
    federal plus the state rate (20% church, 30% rectory) on 98.5% of hard and soft costs; finish materials per SF
    per property; the job is also a Mercer & Bond deal.
 5. The contractor (Dana Reyes): approved hours become her bill, never payroll; the job cost counts them once;
    converting her to an employee keeps her contractor history and sends later hours to payroll.
And: turning the demo off removes exactly what it added (the pinned figures come back to the cent).

  python3 livejobs_test.py      # ALL PASS (n checks) or each failure; screenshots in review/livejobs/
"""
import asyncio, os, re
from harness import *

SHOTS = os.path.join(ROOT, 'review', 'livejobs')
os.makedirs(SHOTS, exist_ok=True)
C = Checks()

CLICK_JS = r"""
([text, css, within]) => {
  const vis = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  let els = [...document.querySelectorAll(css || 'button')].filter(vis).filter(e => !text || norm(e.innerText) === text);
  if (within) els = els.filter(e => e.closest(within));
  if (!els.length) return null;
  const e = els[0]; e.scrollIntoView({block: 'center'});
  const r = e.getBoundingClientRect(), x = r.x + r.width / 2, y = r.y + r.height / 2, top = document.elementFromPoint(x, y);
  // a toast over the button would take a real finger's tap first: dismiss it the way a person would, then tap
  if (top && !e.contains(top) && top.closest && top.closest('#toast')) { document.getElementById('toast').classList.remove('on'); top.closest('#toast').style.display = 'none'; setTimeout(() => document.getElementById('toast').style.display = '', 1500); }
  return {x, y};
}
"""
TOAST_HOOK = r"""
() => { if (window.__ljT) return; window.__ljT = []; const t = document.getElementById('toast'); if (!t) return;
  new MutationObserver(() => { const s = (t.innerText || '').replace(/\s+/g, ' ').trim(); if (s && window.__ljT[window.__ljT.length - 1] !== s) window.__ljT.push(s); })
    .observe(t, {childList: true, subtree: true, characterData: true}); }
"""
# The screen standard on the screens this lane adds: one blue button at most, no sideways scroll on a phone, no
# emoji or glyph icons, Title Case on our own buttons and headings.
SCREEN_JS = r"""
(sel) => {
  const out = [], W = innerWidth, vis = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden' && getComputedStyle(e).display !== 'none'; };
  const prim = [...document.querySelectorAll('.btn.primary')].filter(vis).filter(e => !e.closest('#mbm'));
  if (prim.length > 1) out.push('primary x' + prim.length + ': ' + prim.map(e => e.innerText.trim()).join(' | '));
  if (document.documentElement.scrollWidth > W + 1) out.push('page scrolls sideways: ' + document.documentElement.scrollWidth);
  const scope = [...document.querySelectorAll(sel)].filter(vis);
  const small = new Set(['a','an','the','and','or','of','to','in','on','at','by','for','with','from','as','per','vs']);
  scope.forEach(root => {
    if (/[\u{1F300}-\u{1FAFF}☀-➿]/u.test(root.innerText)) out.push('emoji in ' + root.className);
    root.querySelectorAll('button, h3, h4, .lj-kv span, label.lj-field').forEach(b => {
      if (!vis(b)) return;
      const own = [...b.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join(' ').replace(/\$[\d,.]+/g, '').trim();
      if (!own) return;
      if (/[›→✓▾×]/.test(own)) out.push('glyph: ' + own);
      const words = own.split(/\s+/).filter(w => /^[A-Za-z]/.test(w));
      words.forEach((w, i) => { if (i > 0 && small.has(w.toLowerCase())) return; if (/^[a-z]/.test(w) && !/^(sf|h|ft)$/.test(w)) out.push('not Title Case: "' + own + '"'); });
      if (W <= 400 && b.tagName === 'BUTTON' && b.getBoundingClientRect().right > W + 1) out.push('off screen: ' + own);
    });
  });
  return [...new Set(out)];
}
"""


async def tap(pg, text, css='button', within=None, wait=350):
    hit = await pg.evaluate(CLICK_JS, [text, css, within])
    if not hit: return False
    await pg.mouse.click(hit['x'], hit['y'])
    await pg.wait_for_timeout(wait)
    return True


async def ev(pg, js, arg=None):
    return await pg.evaluate(js, arg) if arg is not None else await pg.evaluate(js)


async def shot(pg, name, sel=None):
    await pg.evaluate("() => document.querySelectorAll('#toast').forEach(e => e.style.visibility = 'hidden')")
    path = os.path.join(SHOTS, name + '.png')
    # the app scrolls inside its main pane: bring the card to the top and take the screen as a person sees it
    if sel and await pg.locator(sel).count():
        await pg.evaluate("s => document.querySelector(s).scrollIntoView({block: 'start'})", sel)
        await pg.wait_for_timeout(150)
    await pg.screenshot(path=path)
    await pg.evaluate("() => document.querySelectorAll('#toast').forEach(e => e.style.visibility = '')")


async def screen_ok(pg, where, sel='.lj-card, .lj-note, .lj-billto'):
    bad = await pg.evaluate(SCREEN_JS, sel)
    C.ok(not bad, f'{where}: screen standard: {bad}')


async def boot(p, phone=False, uid='u_owner', demo=True):
    b, pg, errs = await open_app(p, phone=phone)
    await pg.set_viewport_size({'width': 390 if phone else 1440, 'height': 1800})
    await sign_in(pg, uid)
    await pg.evaluate(TOAST_HOOK)
    if demo:
        await go(pg, 'setup')
        C.ok(await tap(pg, 'Turn the Demo On'), 'Settings: the owner turns the Live Jobs demo on from its card')
        await pg.wait_for_timeout(900)
    return b, pg, errs


async def open_client(pg, cid, tab='invoices', doc=None):
    await ev(pg, "([c, t, d]) => { clientOpen = c; clientTab = 'fin'; finTab = t; docOpen = d; view = 'clients'; render(); }", [cid, tab, doc])
    await pg.wait_for_timeout(200)


# ---------------------------------------------------------------------------------------------------------- 0
async def s0_off_by_default(p):
    """The demo is off by default and the firm's pinned figures are untouched; on and off leaves them to the cent."""
    b, pg, errs = await boot(p, demo=False)
    base = await ev(pg, """() => ({ clients: DB.clients.length, ar: arRows().reduce((a, r) => a + r.bal, 0), users: DB.users.length,
        bills: DB.bills.length, time: DB.time.length, emps: DB.employees.length, vendors: DB.vendors.length,
        cash: (typeof companyBalance === 'function') ? JSON.stringify(companyBalance()).length : 0 })""")
    C.ok(not await ev(pg, "() => DB.clients.some(c => /^cl_lj_/.test(c.id))"), 'off by default: no demo job in the firm')
    C.ok(abs(base['ar'] - 92265) < 1, f"pinned AR is $92,265 with the demo off (got {base['ar']})")
    await go(pg, 'setup')
    C.ok(await ev(pg, "() => !!document.querySelector('#lj-demo-card')"), 'Settings shows the Live Jobs Demo card to the owner')
    await screen_ok(pg, 'setup card')
    await tap(pg, 'Turn the Demo On'); await pg.wait_for_timeout(900)
    on = await ev(pg, "() => ({ n: DB.clients.filter(c => /^cl_lj_/.test(c.id)).length, flag: DB.company.liveJobsDemo })")
    C.ok(on['n'] == 4 and on['flag'], f'the switch loads the four demo jobs: {on}')
    toasts = await ev(pg, '() => window.__ljT || []')
    C.ok(any('Live Jobs demo is on' in t and 'Open' in t for t in toasts), f'turning it on toasts with an Open link: {toasts[-2:]}')
    await go(pg, 'setup')
    await tap(pg, 'Turn the Demo Off'); await pg.wait_for_timeout(600)
    after = await ev(pg, """() => ({ clients: DB.clients.length, ar: arRows().reduce((a, r) => a + r.bal, 0), users: DB.users.length,
        bills: DB.bills.length, time: DB.time.length, emps: DB.employees.length, vendors: DB.vendors.length,
        cash: (typeof companyBalance === 'function') ? JSON.stringify(companyBalance()).length : 0 })""")
    C.ok(after == base, f'turning it off removes exactly what it added: {base} vs {after}')
    C.ok(not errs, f'no page errors: {errs[:3]}')
    await b.close()


# ---------------------------------------------------------------------------------------------------------- 1
async def s1_two_payers(p):
    b, pg, errs = await boot(p)
    A = "DB.clients.find(c => c.id === 'cl_lj_atl')"
    # the books: every record carries its payer, and the two payers add up to the contract to the cent
    f = await ev(pg, f"""() => {{ const c = {A};
        return {{ sov: c.sov.map(v => [v.payer, v.scheduled]), inv: c.invoices.map(i => [i.number, i.payer, docTotal(i).total, invoiceStatus(c, i)]),
          pays: c.payments.map(p => p.payer), byP: ljByPayer(c), all: clientFin(c) }}; }}""")
    L = [x for x in f['byP'] if x['pid'] == 'pay_lj_l'][0]; T = [x for x in f['byP'] if x['pid'] == 'pay_lj_t'][0]
    C.ok(all(s[0] in ('pay_lj_l', 'pay_lj_t') for s in f['sov']), 'every SOV line names its payer')
    C.ok(sum(s[1] for s in f['sov'] if s[0] == 'pay_lj_l') == 138500 and sum(s[1] for s in f['sov'] if s[0] == 'pay_lj_t') == 158500, 'the landlord carries $138,500 of the contract, the tenant $158,500 (the shared general conditions split 50/50)')
    C.ok(L['revised'] == 138500 and T['revised'] == 158500, f"each payer's contract: {L['revised']} / {T['revised']}")
    C.ok(abs(L['invoiced'] - 63295) < 0.01 and abs(T['invoiced'] - 56607.5) < 0.01, f"billed: landlord $63,295.00, tenant $56,607.50 ({L['invoiced']}, {T['invoiced']})")
    C.ok(abs(L['paid'] - 63295) < 0.01 and abs(T['paid'] - 31700) < 0.01, f"paid: landlord $63,295, tenant $31,700 ({L['paid']}, {T['paid']})")
    C.ok(L['outstanding'] == 0 and abs(T['outstanding'] - 24907.5) < 0.01 and abs(T['overdue'] - 24907.5) < 0.01, 'open: the tenant owes $24,907.50, two days overdue; the landlord owes nothing')
    C.ok(abs(L['invoiced'] + T['invoiced'] - f['all']['invoiced']) < 0.01 and abs(L['paid'] + T['paid'] - f['all']['paid']) < 0.01 and abs(L['outstanding'] + T['outstanding'] - f['all']['outstanding']) < 0.01, 'the payers add up to the contract: billed, paid and open tie to the client to the cent')
    C.ok(all(i[1] in ('pay_lj_l', 'pay_lj_t') for i in f['inv']) and all(x in ('pay_lj_l', 'pay_lj_t') for x in f['pays']), 'every invoice and payment names its payer')
    # AR: one list, with the payer on each row; the Receivables report has the By Payer table
    ar = await ev(pg, "() => arRows().filter(r => r.c.id === 'cl_lj_atl').map(r => [r.payerName, r.i.number, r.bal, r.age, r.bucket])")
    C.ok(len(ar) == 1 and ar[0][0] == 'Morning Loaf Bakery Inc.' and ar[0][3] == 2 and ar[0][4] == '1–30', f'AR aging names the tenant on the overdue row: {ar}')
    await ev(pg, "() => { repTab = 'ar'; view = 'reports'; render(); }")
    await pg.wait_for_timeout(250)
    byp = await ev(pg, "() => [...document.querySelectorAll('.lj-ar-payer tbody tr')].map(r => r.innerText.replace(/\\s+/g, ' '))")
    C.ok(len(byp) == 2 and any('Morning Loaf' in r and '$24,908' in r for r in byp), f'Receivables: By Payer shows both payers, the tenant $24,908 open: {byp}')
    await shot(pg, 'desktop_receivables_by_payer', '.lj-ar-payer')
    # a statement per payer
    st = await ev(pg, f"() => {{ const c = {A}; return [ljStatementHtml(c, 'pay_lj_t'), ljStatementHtml(c, 'pay_lj_l')]; }}")
    inv = await ev(pg, f"() => {{ const c = {A}; const n = p => c.invoices.filter(i => i.payer === p).map(i => i.number); return [n('pay_lj_t'), n('pay_lj_l')]; }}")
    C.ok(all(n in st[0] for n in inv[0]) and not any(n in st[0] for n in inv[1]) and 'Morning Loaf Bakery Inc.' in st[0] and '$24,908' in st[0], "the tenant's statement holds only the tenant's invoices, addressed to the tenant, balance $24,908")
    C.ok(all(n in st[1] for n in inv[1]) and not any(n in st[1] for n in inv[0]), "the landlord's statement holds only the landlord's invoices")
    # the client's Billing tab: the payers card, then a progress invoice for the tenant only, by tapping it
    await open_client(pg, 'cl_lj_atl')
    card = await ev(pg, "() => (document.querySelector('.lj-payers') || {}).innerText || ''")
    C.ok('Atlantic Row Holdings LLC' in card and 'Morning Loaf Bakery Inc.' in card and '$138,500' in card and '$158,500' in card, 'the client page shows the payers card with each contract share')
    await screen_ok(pg, 'payers card desktop')
    await shot(pg, 'desktop_payers_card', '.lj-payers')
    ok = await tap(pg, 'Statement', within='[data-ljpayer="cl_lj_atl|pay_lj_t"]')
    m = await ev(pg, "() => (document.querySelector('#mbm') || {}).innerText || ''")
    C.ok(ok and 'Statement: Morning Loaf Bakery Inc.' in m and '24,908' in m, "Statement on the tenant's row opens the tenant's statement")
    await ev(pg, '() => mbCloseModal()')
    await tap(pg, 'New Progress Invoice', within='[data-ljpayer="cl_lj_atl|pay_lj_t"]')
    nv = await ev(pg, f"""() => {{ const c = {A}, d = docOpen && findDoc(c, docOpen.kind, docOpen.id);
        return d ? {{ n: d.number, title: d.title, payer: ljInvPayer(c, d), lines: d.lines.map(l => c.sov.find(v => v.id === l.sovId).payer), billto: (document.querySelector('.lj-billto') || {{}}).innerText || '' }} : null; }}""")
    C.ok(nv and nv['payer'] == 'pay_lj_t' and set(nv['lines']) == {'pay_lj_t'} and len(nv['lines']) == 4, f"New Progress Invoice for the tenant holds the tenant's four SOV lines only: {nv}")
    C.ok(nv and 'Progress billing #2' in nv['title'] and 'Morning Loaf' in nv['title'] and 'Morning Loaf' in nv['billto'], "it is the tenant's second progress billing, billed to the tenant")
    toasts = await ev(pg, '() => window.__ljT || []')
    C.ok(any('for Morning Loaf Bakery Inc.' in t and 'Open' in t for t in toasts), 'the new invoice toasts with an Open link')
    await ev(pg, f"() => {{ const c = {A}; const d = findDoc(c, docOpen.kind, docOpen.id); c.invoices = c.invoices.filter(x => x !== d); docOpen = null; }}")
    # a progress invoice made the generic way (no payer named) holds both payers' lines: it is split at save
    sp = await ev(pg, f"""async () => {{ const c = {A}; clientOpen = c.id; const d = newDoc(c, 'invoice', {{ mode: 'sov' }});
        d.lines.forEach(l => l.pct = 5); const before = ljInvPayer(c, d); await saveNow();
        const mine = c.invoices.filter(i => i === d || (i.status === 'draft' && i.mode === 'sov'));
        return {{ before, after: mine.map(i => [i.number, ljInvPayer(c, i), i.lines.length, docTotal(i).total]) }}; }}""")
    C.ok(sp['before'] == 'mixed' and len(sp['after']) == 2 and {x[1] for x in sp['after']} == {'pay_lj_l', 'pay_lj_t'}, f'a progress invoice with both payers\' lines is split into one per payer when it is saved: {sp}')
    C.ok(abs(sum(x[3] for x in sp['after']) - round(297000 * 0.05 * 0.9, 2)) < 0.02, 'the split keeps every dollar: 5% of $297,000 less 10% retainage across the two')
    # an items invoice with lines from both payers cannot be sent until it is split, by tapping Split by Payer
    mx = await ev(pg, f"""async () => {{ const c = {A}, e = c.estimates[0]; const d = newDoc(c, 'invoice', {{ mode: 'items' }});
        d.lines = [e.lines[0], e.lines[3]].map(l => ({{ id: uid('l'), item: l.item, desc: '', qty: 1, unit: 'ls', rate: 1000, taxable: false, fromLine: `estimate:${{e.id}}:${{l.id}}` }}));
        docMark(d); await docAction(c, d, 'send'); clientOpen = c.id; clientTab = 'fin'; docOpen = {{ kind: 'invoice', id: d.id }}; view = 'clients'; render();
        return {{ id: d.id, status: d.status, payer: ljInvPayer(c, d), banner: !!document.querySelector('.lj-mixed') }}; }}""")
    toasts = await ev(pg, '() => window.__ljT || []')
    C.ok(mx['status'] == 'draft' and mx['payer'] == 'mixed' and mx['banner'], f'a mixed invoice is refused at Send and the editor says why: {mx}')
    C.ok(any('Split by Payer first' in t for t in toasts), 'the refusal names the next step: Split by Payer')
    await shot(pg, 'desktop_mixed_invoice_banner', '.lj-mixed')
    await tap(pg, 'Split by Payer')
    sp2 = await ev(pg, f"() => {{ const c = {A}; const d = c.invoices.find(i => i.id === '{mx['id']}'); const o = c.invoices[c.invoices.length - 1]; return [ljInvPayer(c, d), d.lines.length, ljInvPayer(c, o), o.lines.length, o.id !== d.id]; }}")
    C.ok(sp2 == ['pay_lj_l', 1, 'pay_lj_t', 1, True], f'Split by Payer leaves one invoice per payer: {sp2}')
    # collections: the reminder for the tenant's invoice is written to the tenant
    em = await ev(pg, f"""async () => {{ const c = {A}; const d = c.invoices.find(i => i.number && i.payer === 'pay_lj_t' && invoiceStatus(c, i) === 'overdue');
        await draftDocEmail(c, d); for (let i = 0; i < 70 && !document.querySelector('#drawer.on #em-subj'); i++) await new Promise(r => setTimeout(r, 200));
        const m = document.querySelector('#d-body');
        return {{ modal: m ? m.innerText : '', inputs: m ? [...m.querySelectorAll('input,textarea')].map(i => i.value).join(' | ') : '', out: '' }}; }}""")
    blob = em['modal'] + em['inputs'] + em['out']
    C.ok('owen@morningloaf.example' in blob and 'rosa@atlanticrow.example' not in blob, f"the overdue reminder goes to the tenant's contact, not the landlord's: {blob[:240]}")
    await ev(pg, '() => closeEditor()')
    # a payment on the tenant's invoice moves the tenant's AR and nobody else's
    pay = await ev(pg, f"""async () => {{ const c = {A}; const d = c.invoices.find(i => i.payer === 'pay_lj_t' && invoiceStatus(c, i) === 'overdue');
        paymentAllocate(c, d.id); await new Promise(r => setTimeout(r, 200));
        const m = document.getElementById('mbm'); m.querySelector('#py-amt').value = '10000';
        m.querySelector('#py-method').value = 'Check'; m.querySelector('#py-ref').value = '1088';
        const a = m.querySelector('#py-acct'); a.value = a.options[1] ? a.options[1].value : '';
        m.querySelectorAll('[data-pyalloc]').forEach(i => i.value = i.dataset.pyalloc === d.id ? '10000' : '0');
        m.querySelector('#mbm-ok').click(); await new Promise(r => setTimeout(r, 300)); await saveNow();
        const py = c.payments[c.payments.length - 1]; return {{ amt: py.amount, payer: py.payer, T: ljPayerFin(c, 'pay_lj_t').outstanding, L: ljPayerFin(c, 'pay_lj_l').outstanding }}; }}""")
    C.ok(pay['amt'] == 10000 and pay['payer'] == 'pay_lj_t' and abs(pay['T'] - 14907.5) < 0.01 and pay['L'] == 0, f"a $10,000 check on the tenant's invoice is the tenant's: they owe $14,907.50 now, the landlord still nothing ({pay})")
    # job cost and Ask read the same contract
    J = await ev(pg, "() => { const J = jobFin(DB.projects.find(p => p.id === 'p_lj_atl')); return [J.contract, J.budget]; }")
    C.ok(J == [297000, 229000], f'job cost: contract $297,000, budget $229,000 ({J})')
    q = await ev(pg, "() => eqRows('payers').filter(r => r.clientId === 'cl_lj_atl').map(r => [r.payer, r.outstanding])")
    C.ok(len(q) == 2 and any(r[0] == 'Morning Loaf Bakery Inc.' and abs(r[1] - 14907.5) < 0.01 for r in q), f'Ask and the Report Builder read the payers table: {q}')
    C.ok(not errs, f'two payers: no page errors {errs[:3]}')
    await b.close()


async def s1b_portal_per_payer(p, phone):
    tag = 'phone' if phone else 'desktop'
    b, pg, errs = await boot(p, phone=phone)
    nums = await ev(pg, "() => { const c = DB.clients.find(c => c.id === 'cl_lj_atl'); const n = p => c.invoices.filter(i => i.payer === p).map(i => i.number); return { t: n('pay_lj_t'), l: n('pay_lj_l'), all: c.invoices.length }; }")
    await sign_in(pg, 'u_lj_owen'); await go(pg, 'clacct')
    txt = await ev(pg, "() => document.querySelector('.view.on').innerText")
    C.ok(all(n in txt for n in nums['t']) and not any(n in txt for n in nums['l']), f'{tag}: the tenant\'s portal lists only the tenant\'s invoices')
    C.ok('$24,908' in txt and '$63,295' not in txt and '$94,995' not in txt, f'{tag}: the tenant sees their own balance ($24,908) and never the contract\'s totals')
    await screen_ok(pg, f'{tag} tenant portal', '.view.on')
    await shot(pg, f'{tag}_portal_tenant_account')
    st = await ev(pg, "async () => { const c = DB.clients.find(c => c.id === 'cl_lj_atl'); portalStatement(c); await new Promise(r => setTimeout(r, 150)); const t = (document.querySelector('#mbm') || {}).innerText || ''; mbCloseModal(); return t; }")
    C.ok('Morning Loaf Bakery Inc.' in st and not any(n in st for n in nums['l']), f'{tag}: the tenant\'s portal statement is the tenant\'s')
    ask = await ev(pg, "() => eqRows('invoices').map(r => r.number)")
    C.ok(sorted(ask) == sorted(nums['t']), f'{tag}: Ask reads only the tenant\'s invoices for the tenant ({ask})')
    jc = await ev(pg, "() => ljAsUser(() => jobFin(DB.projects.find(p => p.id === 'p_lj_atl')).contract)")
    C.ok(jc == 158500, f'{tag}: the job\'s contract, read in the tenant\'s portal, is the tenant\'s share: $158,500 ({jc})')
    pr = await ev(pg, "() => eqRows('payers').map(r => r.payer)")
    C.ok(pr == ['Morning Loaf Bakery Inc.'], f'{tag}: the tenant reads their own payer row only ({pr})')
    # nothing the portal swapped in for the draw is ever saved: the record is whole after a save and a reload
    await ev(pg, '() => saveNow()'); await pg.wait_for_timeout(300)
    whole = await ev(pg, "() => { const c = DB.clients.find(c => c.id === 'cl_lj_atl'); return [c.invoices.length, c.sov.length, c.contract, c.name]; }")
    C.ok(whole == [nums['all'], 8, 297000, 'Atlantic Row Holdings LLC'], f'{tag}: the stored record stays whole while a payer views it ({whole})')
    await sign_in(pg, 'u_lj_rosa'); await go(pg, 'clacct')
    txt = await ev(pg, "() => document.querySelector('.view.on').innerText")
    C.ok(all(n in txt for n in nums['l']) and not any(n in txt for n in nums['t']), f'{tag}: the landlord\'s portal lists only the landlord\'s invoices')
    await shot(pg, f'{tag}_portal_landlord_account')
    C.ok(not errs, f'{tag} portal: no page errors {errs[:3]}')
    await b.close()


async def s1c_two_party_approval(p):
    """A new shared contract set up from the screen: the payers dialog, a proposal, each payer approves their part."""
    b, pg, errs = await boot(p)
    cid = await ev(pg, """() => { const c = blankClient('Fulton Mews Owners LLC'); c.ljDemo = 1; c.contacts = [{ id: 'ctf', name: 'Ines Duarte', email: 'ines@fultonmews.example', primary: true }];
        DB.clients.push(c); const pj = blankProject('9 Fulton Mews — lobby and cafe', '9 Fulton Mews', '2026-09-14', ''); pj.clientId = c.id; pj.ljDemo = 1; DB.projects.push(pj); return c.id; }""")
    await open_client(pg, cid, 'estimates')
    C.ok(await tap(pg, 'Add a Second Payer'), 'the Estimates tab offers Add a Second Payer')
    await ev(pg, """() => { const r = document.querySelectorAll('#mbm [data-ljpi]')[1]; r.querySelector('[data-ljpe=name]').value = 'Cafe Lumen LLC';
        r.querySelector('[data-ljpe=contact]').value = 'Sam Ortiz'; r.querySelector('[data-ljpe=email]').value = 'sam@cafelumen.example'; }""")
    await tap(pg, 'Save Payers', within='#mbm')
    py = await ev(pg, f"() => DB.clients.find(c => c.id === '{cid}').payers.map(p => [p.name, p.role])")
    C.ok(py == [['Fulton Mews Owners LLC', 'Owner'], ['Cafe Lumen LLC', 'Tenant']], f'the payers dialog sets both payers: {py}')
    est = await ev(pg, f"""async () => {{ const c = DB.clients.find(c => c.id === '{cid}'); clientOpen = c.id; const pj = DB.projects.find(p => p.clientId === c.id);
        const d = newDoc(c, 'estimate', {{ template: 'construction', fields: {{ projectId: pj.id, title: 'Lobby and cafe' }} }});
        d.lines = [{{ id: 'f1', item: 'Lobby finishes', desc: '', qty: 1, unit: 'ls', rate: 40000, cost: 30000 }}, {{ id: 'f2', item: 'Cafe fit-out', desc: '', qty: 1, unit: 'ls', rate: 60000, cost: 46000, payer: c.payers[1].id }}];
        docMark(d); await docAction(c, d, 'send'); DB.users.push({{ id: 'u_lj_sam', name: 'Sam Ortiz', role: 'client', contact: 'sam@cafelumen.example', clientId: c.id, payerId: c.payers[1].id, ljDemo: 1 }},
          {{ id: 'u_lj_ines', name: 'Ines Duarte', role: 'client', contact: 'ines@fultonmews.example', clientId: c.id, payerId: c.payers[0].id, ljDemo: 1 }}); await saveNow(); return d.id; }}""")
    await sign_in(pg, 'u_lj_sam')
    ap = await ev(pg, f"async () => {{ const c = DB.clients.find(c => c.id === '{cid}'), d = c.estimates.find(x => x.id === '{est}'); portalApprove(c, d); await new Promise(r => setTimeout(r, 150)); return (document.querySelector('#mbm') || {{}}).innerText || ''; }}")
    C.ok('Approve Your Part' in ap and '$60,000' in ap and 'Lobby finishes' not in ap, f'the tenant approves their own part: the sheet shows the cafe line and $60,000, not the owner\'s lines')
    await shot(pg, 'desktop_portal_approve_your_part', '#mbm .mbm-box')
    await ev(pg, "() => { document.querySelector('#lj-pa-agree').checked = true; }")
    await tap(pg, 'Approve $60,000', within='#mbm', wait=600)
    s1 = await ev(pg, f"() => {{ const d = DB.clients.find(c => c.id === '{cid}').estimates.find(x => x.id === '{est}'); return [d.status, Object.keys(d.payerApprovals || {{}}).length]; }}")
    C.ok(s1 == ['sent', 1], f'one payer signed: the proposal waits for the other ({s1})')
    await sign_in(pg, 'u_lj_ines')
    await ev(pg, f"async () => {{ const c = DB.clients.find(c => c.id === '{cid}'), d = c.estimates.find(x => x.id === '{est}'); portalApprove(c, d); await new Promise(r => setTimeout(r, 150)); document.querySelector('#lj-pa-agree').checked = true; }}")
    await tap(pg, 'Approve $40,000', within='#mbm', wait=900)
    s2 = await ev(pg, f"() => {{ const c = DB.clients.find(c => c.id === '{cid}'), d = c.estimates.find(x => x.id === '{est}'); return [d.status, c.contract, c.sov.map(v => v.payer === c.payers[1].id ? 'T' : 'O').join('')]; }}")
    C.ok(s2[0] == 'converted' and s2[1] == 100000 and s2[2] == 'OT', f'both signed: the proposal is the contract, $100,000, and each SOV line is its payer\'s ({s2})')
    C.ok(not errs, f'two-party approval: no page errors {errs[:3]}')
    await b.close()


# ---------------------------------------------------------------------------------------------------------- 2
async def s2_ranges_and_phases(p, phone):
    tag = 'phone' if phone else 'desktop'
    b, pg, errs = await boot(p, phone=phone)
    B = "DB.clients.find(c => c.id === 'cl_lj_rug')"
    st = await ev(pg, f"() => {{ const c = {B}, d = c.estimates[0]; return {{ c: c.contract, sov: c.sov.length, R: ljRange(d), J: jobFin(DB.projects.find(p => p.id === 'p_lj_rug')).contract, inv: c.invoices.map(i => [docTotal(i).total, invoiceStatus(c, i)]) }}; }}")
    C.ok(st['c'] == 24000 and st['sov'] == 4 and st['J'] == 24000, f'{tag}: the exploratory phase is the contract, $24,000, four SOV lines; construction is not in it yet ({st["c"]}, {st["sov"]})')
    C.ok(st['R']['p2']['lo'] == 529000 and st['R']['p2']['hi'] == 718000 and st['R']['p2']['carried'] == 624000, f'{tag}: construction reads $529,000 to $718,000, carried $624,000')
    C.ok(st['inv'] == [[12000, 'paid']], f'{tag}: the exploratory phase is billed 50% at the start and paid ({st["inv"]})')
    await open_client(pg, 'cl_lj_rug', 'invoices')
    C.ok(await ev(pg, "() => !!document.querySelector('.lj-phase')"), f'{tag}: the client page shows the construction phase waiting on discovery')
    await tap(pg, 'Open Discovery')
    C.ok(await ev(pg, "() => !!document.querySelector('.lj-est')"), f'{tag}: Open Discovery lands on the estimate\'s panel')
    # a finding recorded on the screen: Structure at $41,000
    row = '[data-ljline]'
    lid = await ev(pg, f"() => {B}.estimates[0].lines.find(l => l.item.startsWith('Structure')).id")
    await pg.fill(f'[data-ljline="{lid}"] [data-ljfound="amt"]', '41000')
    await pg.fill(f'[data-ljline="{lid}"] [data-ljfound="note"]', 'Two joists sistered, one beam replaced')
    C.ok(await tap(pg, 'Record Finding', within=f'[data-ljline="{lid}"]'), f'{tag}: the Record Finding button is there to tap')
    f1 = await ev(pg, f"() => {{ const d = {B}.estimates[0], l = d.lines.find(x => x.id === '{lid}'); return [l.found && l.found.amount, l.found && l.found.outside, docDirty(d)]; }}")
    C.ok(f1 == [41000, False, False], f'{tag}: Record Finding keeps $41,000 on the line, within its range, and the converted estimate stays clean ({f1})')
    out = await ev(pg, f"() => {B}.estimates[0].lines.filter(l => l.found && l.found.outside).map(l => l.item)")
    C.ok(out == ['Storm and sewer to the street'], f'{tag}: the sewer finding ($31,000 against $9,000–$26,000) is flagged outside the range the client saw ({out})')
    await screen_ok(pg, f'{tag} discovery panel')
    await shot(pg, f'{tag}_discovery_panel', '.lj-est')
    summ = await ev(pg, f"() => docSummaryHtml({B}, {B}.estimates[0])")
    C.ok('Two Phases' in summ and 'The Unknowns, as Ranges' in summ and 'Allowances' in summ, f'{tag}: the client\'s view of the proposal explains the phases, the ranges and the allowances')
    # the client approves the construction phase (recorded by the PM)
    await tap(pg, 'Client Approved Construction Phase')
    a2 = await ev(pg, f"""() => {{ const c = {B}, d = c.estimates[0]; const J = jobFin(DB.projects.find(p => p.id === 'p_lj_rug'));
        return {{ c: c.contract, net: c.contractNet, sov: c.sov.length, sovSum: c.sov.reduce((a, v) => a + v.scheduled, 0), J: J.contract, budget: J.budget, p2: d.phase2,
          allow: ljAllowanceRows(c).map(r => [r.item, r.price, r.budget]), code: d.lines.find(l => l.item.startsWith('Code')).allowance, mep: [d.lines.find(l => l.item === 'MEP rerouting').rate, d.lines.find(l => l.item === 'MEP rerouting').cost] }}; }}""")
    C.ok(a2['c'] == 690500 and a2['net'] == 690500 and a2['J'] == 690500, f'{tag}: the construction phase joins the contract: $24,000 + $666,500 = $690,500 everywhere ({a2["c"]}, {a2["J"]})')
    C.ok(a2['sov'] == 13 and a2['sovSum'] == 690500, f'{tag}: the schedule of values gains the nine construction lines and adds up to the contract ({a2["sov"]}, {a2["sovSum"]})')
    C.ok(a2['mep'] == [46500, 36037.5], f'{tag}: a discovery figure moves price and budget together (MEP $46,500 against $36,037.50, the margin it was priced at): {a2["mep"]}')
    C.ok(a2['code'] is True and ['Code upgrades: egress and fire separation', 21000, 16500] in a2['allow'], f'{tag}: the unresolved range (code upgrades) is carried as an allowance at $21,000')
    C.ok(a2['p2'] and a2['p2']['total'] == 666500 and a2['p2']['allowances'] == 1, f'{tag}: the approval is recorded with who, when and what it added ({a2["p2"]})')
    # an allowance runs over: the bill on the tile line, the reminder, the change order drafted from the card
    over = await ev(pg, f"""() => {{ const c = {B}, d = c.estimates[0], l = d.lines.find(x => x.item === 'Tile allowance'), key = `estimate:${{d.id}}:${{l.id}}`;
        DB.bills.push({{ id: 'b_lj_tile', vendor: 'Nemo Tile', number: 'NT-LJ-1', date: '2026-09-02', due: '2026-09-16', entityId: 'ent1', projectId: 'p_lj_rug', poId: '', cat: 'materials', code: '08', line: key,
          lines: [{{ id: 'bl_lj1', desc: 'Zellige and porcelain', amount: 14500, line: key }}], status: 'approved', approvals: [], createdBy: 'Chen', ljDemo: 1 }});
        const r = ljAllowanceRows(c).find(x => x.key === key); return {{ key, st: r.status, over: r.over, toCO: r.toCO, rem: reminders().some(x => /allowance/.test(x.label) && /Tile allowance/.test(x.label)) }}; }}""")
    C.ok(over['st'] == 'over' and over['over'] == 2500 and over['toCO'] == 2500 and over['rem'], f'{tag}: $14,500 of tile against a $12,000 allowance is $2,500 over; Today raises it until a change order covers it ({over})')
    await open_client(pg, 'cl_lj_rug', 'invoices')
    await screen_ok(pg, f'{tag} allowances card')
    await shot(pg, f'{tag}_allowances_card', '.lj-allow')
    await tap(pg, 'Draft Change Order $2,500')
    co = await ev(pg, f"() => {{ const c = {B}, x = c.changeOrders.find(y => y.allowanceOf === '{over['key']}'); return x ? [x.status, docTotal(x).total, ljAllowanceRows(c).find(r => r.key === '{over['key']}').status, reminders().some(r => /Tile allowance/.test(r.label))] : null; }}")
    C.ok(co == ['draft', 2500, 'covered', False], f'{tag}: Draft Change Order makes a $2,500 draft for a person to send; the allowance reads covered and the reminder clears ({co})')
    # closing an unused allowance drafts the credit
    cr = await ev(pg, f"""() => {{ const c = {B}, d = c.estimates[0], l = d.lines.find(x => x.item === 'Kitchen appliances allowance'), key = `estimate:${{d.id}}:${{l.id}}`;
        DB.bills.push({{ id: 'b_lj_app', vendor: 'Diamond Appliances', number: 'DA-LJ-1', date: '2026-09-02', due: '2026-09-16', entityId: 'ent1', projectId: 'p_lj_rug', poId: '', cat: 'materials', code: '13', line: key,
          lines: [{{ id: 'bl_lj2', desc: 'Range, fridge, dishwasher', amount: 15000, line: key }}], status: 'approved', approvals: [], createdBy: 'Chen', ljDemo: 1 }});
        const r = ljAllowanceClose(c, key); return r.ok ? [r.co.number, docTotal(r.co).total, r.co.status, !!l.allowanceClosed] : r.why; }}""")
    C.ok(isinstance(cr, list) and cr[1] == -3000 and cr[2] == 'draft' and cr[3], f'{tag}: closing the appliance allowance at $15,000 of $18,000 drafts a $3,000 credit for the client ({cr})')
    q = await ev(pg, "() => eqRows('allowances').filter(r => r.clientId === 'cl_lj_rug').map(r => [r.item, r.status])")
    C.ok(len(q) == 3, f'{tag}: Ask reads the allowances ({q})')
    C.ok(not errs, f'{tag} ranges and phases: no page errors {errs[:3]}')
    await b.close()


# ---------------------------------------------------------------------------------------------------------- 3
async def s3_normal_estimate(p):
    b, pg, errs = await boot(p)
    K = "DB.clients.find(c => c.id === 'cl_lj_mac')"
    tot = await ev(pg, f"() => docTotal({K}.estimates[0]).total")
    C.ok(tot == 337000, f'the Macon estimate is $337,000 ({tot})')
    await sign_in(pg, 'u_lj_shah'); await go(pg, 'client')
    await ev(pg, f"async () => {{ const c = {K}; portalApprove(c, c.estimates[0]); await new Promise(r => setTimeout(r, 150)); document.querySelector('#pa-agree').checked = true; }}")
    C.ok(await tap(pg, 'Approve $337,000', within='#mbm', wait=900), 'the client approves the proposal in the portal')
    a = await ev(pg, f"() => {{ const c = {K}; return [c.estimates[0].status, c.contract, c.sov.length, c.sov.reduce((x, v) => x + v.scheduled, 0)]; }}")
    C.ok(a == ['converted', 337000, 9, 337000], f'the approval sets the contract and nine SOV lines that add to it ({a})')
    await sign_in(pg, 'u_owner')
    dep = await ev(pg, f"""async () => {{ const c = {K}; clientOpen = c.id; ctDepositInvoice(c, c.estimates[0]); await new Promise(r => setTimeout(r, 150));
        const m = document.getElementById('mbm'), i = m.querySelector('#dep-pct'); i.value = '20'; i.dispatchEvent(new Event('input')); i.dispatchEvent(new Event('change')); return true; }}""")
    await tap(pg, 'Create Deposit Invoice', within='#mbm', wait=600)
    di = await ev(pg, f"async () => {{ const c = {K}, d = c.invoices[c.invoices.length - 1]; await docAction(c, d, 'send'); return [d.number, docTotal(d).total, d.status]; }}")
    C.ok(di[1] == 67400 and di[2] == 'sent', f'the deposit invoice is 20% of the contract, $67,400, and sent ({di})')
    pay = await ev(pg, f"""async () => {{ const c = {K}, d = c.invoices[c.invoices.length - 1]; paymentAllocate(c, d.id); await new Promise(r => setTimeout(r, 200));
        const m = document.getElementById('mbm'); m.querySelector('#py-method').value = 'Wire'; m.querySelector('#py-ref').value = 'SHAH-0903';
        const a = m.querySelector('#py-acct'); a.value = a.options[1] ? a.options[1].value : ''; m.querySelector('#py-auto').click();
        m.querySelector('#mbm-ok').click(); await new Promise(r => setTimeout(r, 300)); return [invoiceStatus(c, d), clientFin(c).paid, clientFin(c).outstanding]; }}""")
    C.ok(pay == ['paid', 67400, 0], f'the deposit is paid in full ({pay})')
    # a bill coded to an estimate line lands in job cost, on that line
    jc = await ev(pg, f"""() => {{ const c = {K}, e = c.estimates[0], l = e.lines[0], key = `estimate:${{e.id}}:${{l.id}}`;
        DB.bills.push({{ id: 'b_lj_demo', vendor: 'Tino', number: 'TD-LJ-1', date: '2026-09-03', due: '2026-09-17', entityId: 'ent1', projectId: 'p_lj_mac', poId: '', cat: 'subs', code: '02', line: key,
          lines: [{{ id: 'bl_lj3', desc: 'Demolition, first half', amount: 12000, line: key }}], status: 'approved', approvals: [], createdBy: 'Chen', ljDemo: 1 }});
        const J = jobFin(DB.projects.find(p => p.id === 'p_lj_mac')), F = lineFin(key);
        return [J.contract, J.budget, J.actual, J.billed, J.collected, F.actual, F.budget, eqRows('estimates').some(r => r.number === e.number && r.amount === 337000)]; }}""")
    C.ok(jc == [337000, 263000, 12000, 67400, 67400, 12000, 26000, True], f'job cost ties: contract $337,000, budget $263,000, actual $12,000 on the demolition line, billed and collected $67,400; Ask reads the estimate ({jc})')
    C.ok(not errs, f'normal estimate: no page errors {errs[:3]}')
    await b.close()


# ---------------------------------------------------------------------------------------------------------- 4
async def s4_cost_model_htc(p, phone):
    tag = 'phone' if phone else 'desktop'
    b, pg, errs = await boot(p, phone=phone)
    G = "DB.clients.find(c => c.id === 'cl_lj_grace')"
    h = await ev(pg, f"() => {{ const d = {G}.estimates[0]; return {{ M: ljCostModel(d), H: ljHtc(d) }}; }}")
    M, H = h['M'], h['H']
    C.ok(M['B']['hard']['price'] == 1617600 and M['B']['soft']['price'] == 254000 and M['B']['contingency']['price'] == 160000 and M['total'] == 2031600, f'{tag}: hard $1,617,600 (with finish materials), soft $254,000, contingency $160,000, total $2,031,600')
    T = H['T']
    C.ok(T['basis'] == 1843526 and T['fedCredit'] == 368705.2 and T['stateCredit'] == 438340.6 and T['credits'] == 807045.8 and T['net'] == 1224554.2,
         f'{tag}: the tax credit budget to the cent: basis $1,843,526 (98.5% of hard and soft), federal $368,705.20, state $438,340.60, net after credits $1,224,554.20 ({T})')
    ch = [r for r in H['rows'] if r['name'] == 'Church'][0]; re_ = [r for r in H['rows'] if r['name'] == 'Rectory'][0]
    C.ok(ch['state'] == 20 and re_['state'] == 30 and abs(ch['stateCredit'] - 229434.41) < 0.01 and abs(re_['stateCredit'] - 208906.19) < 0.01, f'{tag}: the church takes 20% state, the rectory 30%')
    fin = await ev(pg, f"() => {G}.estimates[0].lines.filter(l => l.ljFinish).map(l => [l.item, l.qty, l.rate, lineAmount(l, {G}.estimates[0])])")
    C.ok(fin == [['Finish materials: Church', 6200, 38, 235600], ['Finish materials: Rectory', 3400, 55, 187000]], f'{tag}: finish materials are priced per SF per property ({fin})')
    await open_client(pg, 'cl_lj_grace', 'estimates', {'kind': 'estimate', 'id': await ev(pg, f"() => {G}.estimates[0].id")})
    await screen_ok(pg, f'{tag} cost model panel')
    await shot(pg, f'{tag}_cost_model_htc', '.lj-est')
    # the estimator changes the rectory's finish price on the screen and re-prices: the budget and credits follow
    pid = 'pr_lj_re'
    await pg.fill(f'[data-ljprop="{pid}"] [data-ljpf="finishPerSf"]', '60')
    await pg.press(f'[data-ljprop="{pid}"] [data-ljpf="finishPerSf"]', 'Tab')
    await pg.wait_for_timeout(300)
    await tap(pg, 'Price Finish Materials')
    h2 = await ev(pg, f"() => {{ const d = {G}.estimates[0]; return [d.lines.find(l => l.ljFinish === 'pr_lj_re').rate, ljCostModel(d).B.hard.price, ljHtc(d).T.basis]; }}")
    C.ok(h2 == [60, 1634600, round((1634600 + 254000) * 0.985, 2)], f'{tag}: $60/SF on the rectory re-prices its finish line (+$17,000) and the basis follows ({h2})')
    mb = await ev(pg, "() => [!!(DB.projects.find(p => p.id === 'p_lj_grace').mbDeal || {}).clientPaysAll, (document.querySelector('.lj-est') || {}).innerText.includes('Mercer & Bond deal: the client pays all costs')]")
    C.ok(mb == [True, True], f'{tag}: the job is marked a Mercer & Bond deal and the estimate says the client pays all costs and an all-cash LOI is being prepared ({mb})')
    cs = await ev(pg, f"() => docSummaryHtml({G}, {G}.estimates[0])")
    C.ok('Budget and Tax Credits' in cs and 'Church' in cs and 'Rectory' in cs, f'{tag}: the client\'s view of the budget shows each property\'s budget, credits and net')
    q = await ev(pg, "() => eqRows('estimateranges').filter(r => r.clientId === 'cl_lj_grace').map(r => [r.hard, r.soft, r.contingency, r.taxCredits])")
    C.ok(len(q) == 1 and q[0][1] == 254000, f'{tag}: Ask reads the cost model and the credits ({q})')
    C.ok(not errs, f'{tag} cost model: no page errors {errs[:3]}')
    await b.close()


# ---------------------------------------------------------------------------------------------------------- 5
async def s5_contractor(p, phone):
    tag = 'phone' if phone else 'desktop'
    b, pg, errs = await boot(p, phone=phone)
    st = await ev(pg, """() => ({ bills: DB.bills.filter(b => b.fromTime).map(b => [b.number, b.projectId, b.hours, billGross(b), b.status, b.vendor, b.cat]),
        v: DB.vendors.find(v => v.contractorOf === 'em_lj_dana'), lab: jobFin(DB.projects.find(p => p.id === 'p140')).byCode })""")
    C.ok(st['bills'] == [['HRS-DR-0913', 'p140', 11, 935, 'submitted', 'Dana Reyes Interiors', 'design'], ['HRS-DR-0913-2', 'p_lj_grace', 7.5, 637.5, 'submitted', 'Dana Reyes Interiors', 'design']],
         f'{tag}: approved hours are bills to her business at $85/h, one per job and pay period, waiting for approval ({st["bills"]})')
    C.ok(st['v'] and st['v']['w9'] is False, f'{tag}: she is a vendor, with the W-9 not yet on file')
    # payroll never pays her
    pr = await ev(pg, """() => { const r = payrollFromTime({ quiet: true }); const ids = r ? r.timeIds : []; const d = DB.time.filter(e => e.empId === 'em_lj_dana');
        return { inRun: d.filter(e => ids.includes(e.id)).length, names: r ? r.detail.map(x => x.name) : [], left: d.filter(e => e.payrollId).length }; }""")
    C.ok(pr['inRun'] == 0 and 'Dana Reyes' not in pr['names'] and pr['left'] == 0, f'{tag}: a payroll run from approved time leaves her hours out, and leaves no mark on them ({pr})')
    # the PM approves her 9/3 hours: the bill takes them
    await sign_in(pg, 'u_alan')
    ap = await ev(pg, """async () => { const e = DB.time.find(x => x.empId === 'em_lj_dana' && x.status === 'submitted'); timeAction(e, 'approve'); await new Promise(r => setTimeout(r, 200));
        const b = DB.bills.find(x => x.id === e.billId); return [e.status, b && b.number, b && b.hours, b && billGross(b)]; }""")
    C.ok(ap == ['approved', 'HRS-DR-0913', 15, 1275], f'{tag}: approving her 4 h puts them on her open bill: 15 h, $1,275 ({ap})')
    toasts = await ev(pg, '() => window.__ljT || []')
    C.ok(any('are on bill HRS-DR-0913' in t for t in toasts), f'{tag}: the approval toasts where her hours went, with Open')
    jc = await ev(pg, """() => { const J = jobFin(DB.projects.find(p => p.id === 'p140')); const t = DB.time.filter(e => e.empId === 'em_lj_dana' && e.projectId === 'p140');
        return { laborFromHer: t.reduce((a, e) => a + hoursOf(e) * laborRate(DB.employees.find(x => x.id === e.empId)), 0), accrued: J.accrued }; }""")
    C.ok(jc['laborFromHer'] == 0 and jc['accrued'] >= 1275, f'{tag}: her hours cost the job once, through the bill (accrued $1,275), never again as labor ({jc})')
    # her own Today: how she is paid and her bills; she logs hours on the Day Sheet like anyone
    await sign_in(pg, 'u_lj_dana')
    await ev(pg, "() => { view = (MENU.designer || {}).home || 'sday'; render(); }")
    card = await ev(pg, "() => (document.querySelector('#lj-myhours') || {}).innerText || ''")
    C.ok('Paid as a Contractor' in card and '$85' in card and 'HRS-DR-0913' in card and '$1,275' in card, f'{tag}: her Today says she is paid as a contractor at $85/h and lists her bills')
    await screen_ok(pg, f'{tag} contractor card', '#lj-myhours')
    await shot(pg, f'{tag}_contractor_today', '#lj-myhours')
    n0 = await ev(pg, "() => DB.time.length")
    await ev(pg, "() => { const s = document.querySelector('#st-addp'); const o = [...s.options].find(o => o.value === 'p140'); if (o) s.value = 'p140'; s.dispatchEvent(new Event('change')); }")
    await pg.fill('#st-addh', '2')
    await pg.fill('#st-addn', 'Vanity drawings')
    await tap(pg, 'Log', css='#st-addgo', wait=500)
    lg = await ev(pg, f"() => DB.time.slice({n0}).map(e => [e.empId, e.status, hoursOf(e)])")
    C.ok(lg and lg[0][0] == 'em_lj_dana' and lg[0][1] != 'approved', f'{tag}: the Day Sheet logs her hours as hers, for approval ({lg})')
    # the owner converts her to an employee from the people list; her contractor history stays
    await sign_in(pg, 'u_owner')
    await ev(pg, "() => employeesDialog()")
    await pg.wait_for_timeout(200)
    C.ok(await ev(pg, "() => !!document.querySelector('#d-body #lj-contractors')"), f'{tag}: the Employees list shows her under Contractors')
    await tap(pg, 'Convert to Employee', within='#lj-contractors')
    await pg.fill('#lj-c-rate', '48')
    await tap(pg, 'Convert to Employee', within='#mbm', wait=500)
    cv = await ev(pg, """() => { const old = DB.employees.find(e => e.id === 'em_lj_dana'), n = DB.employees.find(e => e.convertedFrom === 'em_lj_dana'), u = DB.users.find(x => x.id === 'u_lj_dana');
        return { old: [old.active, old.workerType, old.convertedTo === (n && n.id)], n: n && [n.workerType, n.rate, n.since, n.history.length], user: u.employeeId === (n && n.id),
          billed: DB.time.filter(e => e.empId === 'em_lj_dana' && e.billId).length, moved: DB.time.filter(e => n && e.empId === n.id).length, bills: DB.bills.filter(b => b.fromTime).length }; }""")
    C.ok(cv['old'] == [False, 'contractor', True] and cv['n'] and cv['n'][0] == 'employee' and cv['n'][1] == 48 and cv['n'][2] == '2026-09-03' and cv['user'], f'{tag}: converted: a new employee record at $48/h from 9/3, her sign-in moves to it, the contractor record is closed ({cv})')
    C.ok(cv['billed'] == 4 and cv['bills'] == 2 and cv['moved'] == 1, f'{tag}: her four billed contractor entries and two bills stay as they were; the unbilled 9/3 Day Sheet entry is now an employee\'s ({cv})')
    await ev(pg, "() => { const e = DB.time[DB.time.length - 1]; e.status = 'approved'; e.approvedBy = 'Alan'; }")
    pr2 = await ev(pg, "() => { const r = payrollFromTime({ quiet: true }); return r ? r.detail.map(x => x.name) : []; }")
    C.ok('Dana Reyes' in pr2, f'{tag}: once she is an employee, her approved hours go to payroll ({pr2})')
    C.ok(not errs, f'{tag} contractor: no page errors {errs[:3]}')
    await b.close()


async def main():
    async with async_playwright() as p:
        await s0_off_by_default(p)
        await s1_two_payers(p)
        await s1b_portal_per_payer(p, False)
        await s1b_portal_per_payer(p, True)
        await s1c_two_party_approval(p)
        await s2_ranges_and_phases(p, False)
        await s2_ranges_and_phases(p, True)
        await s3_normal_estimate(p)
        await s4_cost_model_htc(p, False)
        await s4_cost_model_htc(p, True)
        await s5_contractor(p, False)
        await s5_contractor(p, True)
    return C.done()

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
