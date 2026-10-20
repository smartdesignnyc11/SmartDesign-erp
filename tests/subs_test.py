"""subs: subcontractors and the Payment Check (BACKLOG §1.10 item 1, §1.12; Alan, 2026-10-11).

Every payment of a bill is checked before it leaves. Each scenario plants one problem the way it happens, through the
app's own screens as the person who meets it, and proves the money to the cent:

  1 subcontract  the subcontract on its PO page: scope, schedule of values, papers, retainage, work in place
  2 overbilled   a pay application claiming 60% when the foreman measured 40%: the PM approves at measured from
                 Approvals; the owner approves; the payment passes the check and is stamped with it
  3 waiver       the next application with no waiver: held for a conditional waiver on it and an unconditional one
                 on the payment before; recording both from the bill releases it
  4 coi          an expired COI holds the payment and the next subcontract's issue; only the owner releases it,
                 with a reason; the controller cannot
  5 bank         a bank change entered by the coordinator holds every payment; the requester cannot verify it; a
                 wrong read-back is refused; the owner's call-back applies it and the payment goes
  6 duplicate    the same invoice number entered twice, and a card charge that already paid a bill, are held
  7 contract     billed beyond the subcontract and its approved changes is held for the owner; an approved change
                 makes room
  8 retainage    a sub bill at 0% on a 10% subcontract is held until the retainage is held
  9 credit       an open vendor credit is taken before new money goes out
 10 run          the payment run pays only the bills that pass, and says why the others are held
 11 books        what was paid flows to AP, job cost, retainage payable (2050), the 1099 register, the vendor
                 ledger and Ask; field roles read none of it
 12 phone        the owner on a phone: the held payment on Approvals, the check sheet, no sideways scroll

All data is invented. Screenshots go to review/subs/. The last line is `N flags`; exit 1 when N > 0.
    python3 subs_test.py                 # every scenario
    python3 subs_test.py --scenario bank # one or more by name or number"""
import asyncio, sys, os, argparse, json
from harness import *

SHOTS = os.path.join(ROOT, 'review', 'subs')
os.makedirs(SHOTS, exist_ok=True)

# An invented sub, an invented subcontract on 121 State and an invented stair task the foreman measures at 40%.
PLANT = r"""() => {
  const p = DB.projects.find(x => x.id === 'p121');
  if (!p.tasks.some(t => t.id === 'tstair')) {
    const t = {id: 'tstair', name: 'Stair rebuild – parlor to 3rd', start: '2026-08-24', end: '2026-09-18', status: 'in-progress', trade: 'Carpentry', type: 'task', pctLog: [], deps: []};
    p.tasks.push(t);
    prgSet(p, t, {pct: 40, by: 'Angel', role: 'foreman', src: 'field', note: 'Stringers and treads set to the 2nd floor'});
  }
  DB.vendors.some(v => v.id === 'vbsw') || DB.vendors.push({id: 'vbsw', name: 'Brooklyn Stair Works', trade: 'Stairs', kind: 'sub', contact: 'Dana Ruiz',
    email: 'dana@bsw.example', phone: '718-555-0142', w9: true, ein: '', insuranceExp: '2027-06-30', insuranceCarrier: 'Invented Mutual',
    licenseNo: 'HIC-000000', licenseExp: '2027-06-30', terms: 'Net 30', bank: {name: 'Invented Savings', last4: '4471'}, bankPending: null,
    bankChangedAt: '', createdBy: 'Chen Biron', notes: '', payMethod: 'ACH'});
  const po4 = DB.pos.find(x => x.id === 'po4');
  if (!DB.pos.some(x => x.id === 'pobsw')) {
    const po = JSON.parse(JSON.stringify(po4));
    Object.assign(po, {id: 'pobsw', number: 'PO-2026-090', vendor: 'Brooklyn Stair Works', vendorId: 'vbsw', date: '2026-08-20', expected: '2026-09-18',
      needBy: '2026-09-18', status: 'issued', type: 'subcontract', retainagePct: 10, matchedTxns: [], receipts: [], srcDocs: [],
      lines: [{id: 'plbsw', item: 'Stair rebuild – parlor to 3rd', desc: '', qty: 1, unit: 'ls', price: 50000, line: po4.lines[0].line, code: po4.lines[0].code, taskIds: ['tstair'], received: 0}],
      sc: {scope: 'Rebuild the main stair, parlor to the 3rd floor, to the drawings.', inclusions: ['Stringers, treads and risers'], exclusions: ['Finish paint'],
           signedOn: '2026-08-20', signedBy: 'Owner', retainageAt: 'substantial completion', changes: []}});
    DB.pos.push(po);
  }
  save(); return true;
}"""

BILL = "n => DB.bills.find(b => b.number === n)"


async def boot(p, phone=False, user='u_owner'):
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, user)
    await pg.evaluate(PLANT)
    return b, pg, errs


async def as_user(pg, uid):
    await pg.evaluate("u => { mbCloseModal(); try { closeEditor(); } catch (e) {} signIn(u); render(); }", uid)
    await pg.wait_for_timeout(120)


async def modal(pg):
    """The open sheet's title, primary label, alt label and text (or None)."""
    return await pg.evaluate("""() => { const m = document.querySelector('#mbm'); if (!m) return null;
        const t = s => (m.querySelector(s) || {}).innerText || '';
        return {title: t('h3'), ok: t('#mbm-ok'), alt: t('#mbm-alt'), text: m.innerText.replace(/\\s+/g, ' ')}; }""")


async def fill(pg, fields):
    await pg.evaluate("""f => { const m = document.querySelector('#mbm'); Object.entries(f).forEach(([k, v]) => {
        const i = m.querySelector(`[data-f="${k}"]`); if (!i) return; if (i.type === 'checkbox') i.checked = !!v; else i.value = v;
        i.dispatchEvent(new Event('input', {bubbles: true})); i.dispatchEvent(new Event('change', {bubbles: true})); }); }""", fields)


async def press(pg, sel='#mbm-ok'):
    await pg.evaluate("s => { const b = document.querySelector(s); b && b.click(); }", sel)
    await pg.wait_for_timeout(160)


async def toast_text(pg):
    return await pg.evaluate("() => (document.getElementById('toast') || {}).innerText || ''")


async def new_payapp(pg, number, pct, waiver=False, as_uid='u_chen'):
    """The coordinator opens the subcontract and presses New Pay Application on its card."""
    await as_user(pg, as_uid)
    await pg.evaluate("() => { poOpen = 'pobsw'; view = 'po'; render(); }")
    await pg.wait_for_timeout(150)
    await pg.evaluate("() => { const b = document.querySelector('.sc-card [data-sc=\"payapp\"]'); b && b.click(); }")
    await pg.wait_for_timeout(150)
    m = await modal(pg)
    if not m or 'New Pay Application' not in m['title']: return None, m
    await fill(pg, {'number': number, 'pct0': str(pct), 'waiver': waiver})
    pre = await modal(pg)
    await press(pg)
    return await pg.evaluate(BILL, number), pre


async def approve_via_approvals(pg, uid, bill_id):
    """The person's Approvals: the bill's card, its yes. Returns the sheet it opens, if any."""
    await as_user(pg, uid)
    await go(pg, 'mapprove')
    found = await pg.evaluate("""id => { const el = document.querySelector(`.m-appr[data-mk="bill"][data-mid="${id}"]`);
        if (!el) return null; const t = el.innerText.replace(/\\s+/g, ' '); const y = el.querySelector('[data-myes]'); y && y.click(); return {text: t, yes: y ? y.innerText : ''}; }""", bill_id)
    await pg.wait_for_timeout(180)
    return found, await modal(pg)


async def owner_approve(pg, bill_id, why='checked the pay application against the site'):
    """The owner's yes on a bill; an override question is answered with a reason (it is part of the record)."""
    found, m = await approve_via_approvals(pg, 'u_owner', bill_id)
    if m and ('Override' in m['title'] or 'Approve Anyway' in m['ok']):
        await fill(pg, {'why': why}); await press(pg)
    return found, m


async def check(pg, bill_id, amount=None, method=None):
    return await pg.evaluate("""([id, a, m]) => { const b = DB.bills.find(x => x.id === id); const R = pcCheck(b, {amount: a, method: m});
        return {pass: R.pass, amount: R.amount, holds: R.holds.map(h => ({key: h.key, what: h.what, money: h.money, who: h.who, fixed: h.fixed, why: h.why})),
                ok: R.ok.map(k => k.text), released: R.released.map(h => h.key)}; }""", [bill_id, amount, method])


async def pay_sheet(pg, bill_id, fields=None):
    """Open the bill's pay sheet (the bill's Pay button goes here) and record the payment."""
    await pg.evaluate("id => pcPaySheet(id)", bill_id)
    await pg.wait_for_timeout(150)
    m = await modal(pg)
    if fields: await fill(pg, fields)
    await press(pg)
    return m, await toast_text(pg)


async def no_hscroll(pg):
    return await pg.evaluate("() => document.documentElement.scrollWidth <= innerWidth + 1")


async def shot(pg, name):
    try: await pg.screenshot(path=os.path.join(SHOTS, name + '.png'), full_page=False)
    except Exception as e: print('screenshot failed', name, e)


# ---------------------------------------------------------------- 1. the subcontract on its PO page
async def s1_subcontract(p, C):
    for phone in (False, True):
        b, pg, errs = await boot(p, phone=phone, user='u_chen')
        try:
            await pg.evaluate("() => { poOpen = 'po4'; view = 'po'; render(); }")
            await pg.wait_for_timeout(200)
            card = await pg.evaluate("""() => { const c = document.querySelector('.view.on .sc-card'); if (!c) return null;
                return {text: c.innerText.replace(/\\s+/g, ' '), btns: [...c.querySelectorAll('button')].map(b => b.innerText.trim()),
                        primary: c.querySelectorAll('.btn.primary').length,
                        bill: [...document.querySelectorAll('.view.on [data-poact="bill"]')].map(b => b.innerText.trim())}; }""")
            tag = 'phone' if phone else 'desktop'
            C.ok(card is not None, f'[1 {tag}] PO-2026-048 shows its Subcontract card')
            if card:
                C.ok('Fabricate, deliver and install' in card['text'] and 'Countertops' in card['text'], f'[1 {tag}] the scope, inclusions and exclusions read on the card: {card["text"][:160]}')
                C.ok('$76,000' in card['text'] and '10% retainage' in card['text'], f'[1 {tag}] the contract and its retainage are on the card')
                C.ok('10% in place, measured by Angel' in card['text'], f'[1 {tag}] work in place is the site\'s measure of the parlor kitchen task (10%), not the whole millwork line')
                C.ok('Deposit' in card['text'] and '$38,000' in card['text'] and 'billed ahead' not in card['text'], f'[1 {tag}] CM-0091 reads as the 50% deposit the terms allow, applied as the work is billed, not as work billed ahead: {card["text"][-420:]}')
                C.ok('without an unconditional waiver' in card['text'], f'[1 {tag}] the card says the deposit was paid with no unconditional lien waiver back')
                C.ok('New Pay Application' in card['btns'] and card['primary'] == 0, f'[1 {tag}] New Pay Application is on the card and nothing on it is blue: {card["btns"]}')
                C.ok(all(x == 'New Pay Application' for x in card['bill']), f'[1 {tag}] the PO\'s own bill button reads New Pay Application on a subcontract: {card["bill"]}')
            if phone: C.ok(await no_hscroll(pg), '[1 phone] the PO page with its subcontract card does not scroll sideways')
            await shot(pg, f'subcontract_{tag}')
            # the catch: a deposit is not a leak; a sub paid ahead of the work measured is (planted: BSW paid at 80%, 0% held)
            await as_user(pg, 'u_owner')
            rows0 = await pg.evaluate("() => CATCH.find(c => c.name === 'subsAhead').rows().map(r => r.what)")
            C.ok(not any('Carlos' in r for r in rows0), f'[1 {tag}] Carlos Millwork\'s deposit is not a catch: {rows0}')
            await pg.evaluate("""() => { DB.bills.push({id: 'bahead', vendor: 'Brooklyn Stair Works', number: 'BSW-099', date: '2026-08-28', due: '2026-08-28', entityId: 'ent1', projectId: 'p121', poId: 'pobsw', cat: 'subs', code: '',
                lines: [{id: 'bla', desc: 'Stair rebuild, to 80%', amount: 40000, poLineId: 'plbsw'}], payMethod: 'Check', status: 'paid', paidAt: '2026-08-29', approvals: [], createdBy: 'Billing', retainagePct: 0}); save(); }""")
            rows = await pg.evaluate("() => CATCH.find(c => c.name === 'subsAhead').rows().map(r => [r.what, r.sub, r.amount, standardWhy('subsAhead')])")
            C.ok(len(rows) == 1 and rows[0][2] == 24000 and '$20,000 in place' in rows[0][1] and '$4,000 of retainage not held' in rows[0][1] and 'Because:' in rows[0][3],
                 f'[1 {tag}] Caught for You: a sub paid at 80% with 40% measured ($20,000 ahead) and no retainage ($4,000), with its Standard line: {rows}')
            C.ok(not errs, f'[1 {tag}] no page errors {errs[:2]}')
        finally:
            await b.close()


# ---------------------------------------------------------------- 2. the overbilled pay application
async def s2_overbilled(p, C):
    b, pg, errs = await boot(p)
    try:
        bill, pre = await new_payapp(pg, 'BSW-101', 60, waiver=True)
        C.ok(pre and '$10,000 ahead of the site' in pre['text'], f'[2] the pay application sheet shows the 60% claim is $10,000 ahead of the 40% measured, as it is typed: {pre and pre["text"][-300:]}')
        C.ok(bill is not None, '[2] the coordinator submitted pay application 1 as a bill on the subcontract')
        if not bill: return
        money = await pg.evaluate("n => { const b = DB.bills.find(x => x.number === n); return [billGross(b), billTotal(b), b.retainagePct, b.status, b.projectId, b.poId, b.cat, b.payApp.lines[0].pct, b.payApp.lines[0].measured, b.lines[0].poLineId, b.lines[0].line, b.entityId, wvList(b).length]; }", 'BSW-101')
        C.ok(money[:3] == [30000, 27000, 10], f'[2] gross $30,000.00, $27,000.00 payable after 10% retainage: {money[:3]}')
        C.ok(money[3] == 'submitted' and money[4] == 'p121' and money[5] == 'pobsw' and money[6] == 'subs', f'[2] it carries its job, subcontract and category: {money[3:7]}')
        C.ok(money[7] == 60 and money[8] == 40 and money[9] == 'plbsw' and money[10] and money[11], f'[2] each line keeps its claim, the measure, its SOV line, estimate line and entity: {money[7:12]}')
        C.ok(money[12] == 1, '[2] the conditional waiver that came with it is on the bill')
        t = await toast_text(pg)
        C.ok('Open' in t and 'ahead' in t, f'[2] the toast says what happened, with Open: {t[:160]}')
        # the PM's Approvals: the card says it claims ahead; yes opens the review at measured
        found, m = await approve_via_approvals(pg, 'u_alan', bill['id'])
        C.ok(found and '$10,000 claimed ahead of the work measured' in found['text'], f'[2] the PM\'s Approvals card says $10,000 is claimed ahead of the site: {found and found["text"][:200]}')
        C.ok(m and m['ok'] == 'Approve at Measured' and m['alt'] == 'Approve as Claimed', f'[2] the PM\'s yes opens the review with Approve at Measured as the safe primary: {m and (m["title"], m["ok"], m["alt"])}')
        await shot(pg, 'payapp_review_desktop')
        await press(pg)
        after = await pg.evaluate("n => { const b = DB.bills.find(x => x.number === n); return [billGross(b), billTotal(b), b.status, b.payApp.revised && b.payApp.revised.diff, b.payApp.lines[0].pct, b.payApp.lines[0].claimedPct]; }", 'BSW-101')
        C.ok(after[:2] == [20000, 18000] and after[3] == 10000 and after[4] == 40 and after[5] == 60, f'[2] approved at measured: $20,000.00 gross, $18,000.00 payable, $10,000 to the next application: {after}')
        C.ok(after[2] in ('pm-approved', 'approved'), f'[2] the PM\'s approval moved it on: {after[2]}')
        # the owner approves; the check then passes and the payment is stamped with it
        await owner_approve(pg, bill['id'])
        st = await pg.evaluate("n => DB.bills.find(x => x.number === n).status", 'BSW-101')
        C.ok(st == 'approved', f'[2] the owner approved it: {st}')
        k = await check(pg, bill['id'])
        C.ok(k['pass'] and k['amount'] == 18000, f'[2] the Payment Check passes on $18,000.00: {[h["what"] for h in k["holds"]]}')
        C.ok(any('Work in place supports' in x for x in k['ok']) and any('Retainage 10% held' in x for x in k['ok']) and any('waiver on file' in x for x in k['ok']), f'[2] the ticks say what was checked: {k["ok"]}')
        await as_user(pg, 'u_controller')
        m, t = await pay_sheet(pg, bill['id'], {'method': 'ACH'})
        C.ok(m and 'payment check' in m['text'].lower() and 'checked' in m['text'].lower(), f'[2] the pay sheet opens on the check: {m and m["text"][:160]}')
        pay = await pg.evaluate("n => { const b = DB.bills.find(x => x.number === n); const P = DB.payments.filter(p => p.billId === b.id); return {st: b.status, n: P.length, amt: P[0] && P[0].amount, chk: P[0] && P[0].check && P[0].check.pass, pts: P[0] && P[0].check && P[0].check.checked.length, by: P[0] && P[0].check && P[0].check.by}; }", 'BSW-101')
        C.ok(pay['st'] == 'paid' and pay['n'] == 1 and pay['amt'] == 18000 and pay['chk'] and pay['pts'] >= 8, f'[2] paid $18,000.00, the payment stamped with the check it passed: {pay}')
        C.ok('Open' in t and '$18,000' in t, f'[2] the toast names the payment, with Open: {t[:140]}')
        C.ok(not errs, f'[2] no page errors {errs[:2]}')
    finally:
        await b.close()


async def paid_app1(pg):
    """Pay application 1 at 40%, approved and paid (the state scenarios 3 to 11 start from)."""
    bill, _ = await new_payapp(pg, 'BSW-101', 40, waiver=True)
    await pg.evaluate("""n => { const b = DB.bills.find(x => x.number === n); signIn('u_alan'); billAction(b, 'pmok'); signIn('u_owner'); billAction(b, 'approve', 'ok');
        signIn('u_controller'); const a = entAccountsOf(b.entityId || entDefault())[0]; pcRecord(b, {acct: a.id, date: today(), amount: pcOpen(b), method: 'ACH'}); save(); }""", 'BSW-101')
    return bill


async def approved_app(pg, number, pct, waiver=False):
    """A further pay application, measured to its claim, approved by the PM and the owner."""
    await pg.evaluate("pct => { const p = DB.projects.find(x => x.id === 'p121'); prgSet(p, p.tasks.find(t => t.id === 'tstair'), {pct: pct, by: 'Angel', role: 'foreman', src: 'field'}); save(); }", pct)
    bill, _ = await new_payapp(pg, number, pct, waiver=waiver)
    await pg.evaluate("n => { const b = DB.bills.find(x => x.number === n); signIn('u_alan'); billAction(b, 'pmok'); signIn('u_owner'); billAction(b, 'approve', 'ok'); save(); }", number)
    return await pg.evaluate(BILL, number)


# ---------------------------------------------------------------- 3. the missing waiver
async def s3_waiver(p, C):
    b, pg, errs = await boot(p)
    try:
        await paid_app1(pg)
        bill = await approved_app(pg, 'BSW-102', 70, waiver=False)
        C.ok(bill and bill['status'] == 'approved', f'[3] pay application 2 is approved: {bill and bill["status"]}')
        k = await check(pg, bill['id'])
        keys = [h['key'] for h in k['holds']]
        whats = ' | '.join(h['what'] for h in k['holds'])
        C.ok(not k['pass'] and keys.count('waiver') == 2, f'[3] held for two waivers: {whats}')
        C.ok('No unconditional lien waiver for the payment before: BSW-101 ($18,000' in whats and 'No conditional lien waiver for this payment of $13,500' in whats, f'[3] each says which payment and how much: {whats}')
        C.ok(all(h['why'].startswith('Because:') for h in k['holds']), f'[3] each hold names its Standard line: {[h["why"] for h in k["holds"]]}')
        # the run refuses it, and so does Mark Paid
        await as_user(pg, 'u_controller')
        r = await pg.evaluate("n => { const b = DB.bills.find(x => x.number === n); const a = entAccountsOf(b.entityId || entDefault())[0]; return pcRecord(b, {acct: a.id, date: today(), amount: pcOpen(b), method: 'ACH'}).err || 'paid'; }", 'BSW-102')
        C.ok(r.startswith('Held:') and 'waiver' in r, f'[3] recording the payment is refused with the reason: {r[:120]}')
        await pg.evaluate("n => billAction(DB.bills.find(x => x.number === n), 'paid')", 'BSW-102')
        st = await pg.evaluate("n => DB.bills.find(x => x.number === n).status", 'BSW-102')
        C.ok(st == 'approved', f'[3] Mark Paid is refused too: {st}')
        # the bill's sheet: the check card, Record the Waiver on each hold
        await pg.evaluate("n => { view = 'ap'; render(); openBill(DB.bills.find(x => x.number === n).id); }", 'BSW-102')
        await pg.wait_for_timeout(200)
        card = await pg.evaluate("() => { const c = document.querySelector('#d-body .pc-card'); return c ? {text: c.innerText.replace(/\\s+/g, ' '), acts: [...c.querySelectorAll('[data-pcact]')].map(b => b.innerText)} : null; }")
        C.ok(card and 'Held · 2' in card['text'] and card['acts'].count('Record the Waiver') == 2, f'[3] the bill shows the check held, each hold with Record the Waiver: {card}')
        await shot(pg, 'waiver_held_desktop')
        # prior payment's unconditional waiver, then this payment's conditional one, from the hold buttons
        await pg.evaluate("() => document.querySelectorAll('#d-body [data-pcact=\"waiver-prior\"]')[0].click()")
        await pg.wait_for_timeout(150)
        m = await modal(pg)
        C.ok(m and 'BSW-101' in m['title'], f'[3] the first hold opens the waiver for BSW-101: {m and m["title"]}')
        await fill(pg, {'type': 'unconditional', 'amount': '18000'}); await press(pg)
        await pg.wait_for_timeout(200)
        await pg.evaluate("() => { const b = document.querySelector('#d-body [data-pcact=\"waiver\"]'); b && b.click(); }")
        await pg.wait_for_timeout(150)
        m = await modal(pg)
        C.ok(m and 'BSW-102' in m['title'], f'[3] the second opens the conditional waiver for this payment: {m and m["title"]}')
        await press(pg)
        k = await check(pg, bill['id'])
        C.ok(k['pass'], f'[3] with both waivers the payment passes: {[h["what"] for h in k["holds"]]}')
        reg = await pg.evaluate("() => { const r = eqRows('waiverrows').filter(x => x.vendor === 'Brooklyn Stair Works'); return r.map(x => [x.bill, x.type, x.scope, x.amount]); }")
        C.ok(['BSW-101', 'unconditional', 'progress', 18000] in reg and any(x[0] == 'BSW-102' and x[1] == 'conditional' for x in reg), f'[3] the waivers are tracked per payment and per job: {reg}')
        m, t = await pay_sheet(pg, bill['id'])
        st = await pg.evaluate("n => DB.bills.find(x => x.number === n).status", 'BSW-102')
        C.ok(st == 'paid', f'[3] then it pays: {st} · {t[:100]}')
        C.ok(not errs, f'[3] no page errors {errs[:2]}')
    finally:
        await b.close()


# ---------------------------------------------------------------- 4. the expired COI
async def s4_coi(p, C):
    b, pg, errs = await boot(p)
    try:
        await paid_app1(pg)
        bill = await approved_app(pg, 'BSW-102', 70, waiver=True)
        await pg.evaluate("() => { const v = DB.vendors.find(x => x.id === 'vbsw'); v.insuranceExp = '2026-08-31'; const b = DB.bills.find(x => x.number === 'BSW-101'); wvAdd(b, {type: 'unconditional', amount: 18000}); save(); }")
        k = await check(pg, bill['id'])
        coi = [h for h in k['holds'] if h['key'] == 'papers']
        C.ok(not k['pass'] and coi and 'expired Mon, Aug 31' in coi[0]['what'] and coi[0]['who'] == 'owner', f'[4] held: the COI expired Aug 31, the owner\'s to release: {coi}')
        # the controller sees no release; the owner's Approvals has it
        await as_user(pg, 'u_controller')
        rel = await pg.evaluate("n => { const b = DB.bills.find(x => x.number === n); const R = pcCheck(b); return R.holds.map(h => pcCanRelease(b, h, R.amount)); }", 'BSW-102')
        C.ok(not any(rel), f'[4] the controller cannot release it: {rel}')
        await as_user(pg, 'u_owner')
        await go(pg, 'mapprove')
        card = await pg.evaluate("""() => { const el = [...document.querySelectorAll('.m-appr[data-mk="payhold"]')].find(e => /BSW-102/.test(e.innerText));
            return el ? {text: el.innerText.replace(/\\s+/g, ' '), yes: (el.querySelector('[data-myes]') || {}).innerText,
                          chip: [...document.querySelectorAll('#mappr-tabs button')].map(b => b.innerText.replace(/\\s+/g, ' '))} : null; }""")
        C.ok(card and 'certificate of insurance expired' in card['text'] and card['yes'] == 'Review', f'[4] the owner\'s Approvals holds it under Payment Holds: {card}')
        C.ok(card and any(c.startswith('Payment Holds') for c in card['chip']), f'[4] the Payment Holds chip is on Approvals: {card and card["chip"]}')
        await shot(pg, 'coi_held_approvals_desktop')
        await pg.evaluate("() => { const el = [...document.querySelectorAll('.m-appr[data-mk=\"payhold\"]')].find(e => /BSW-102/.test(e.innerText)); el.querySelector('[data-myes]').click(); }")
        await pg.wait_for_timeout(200)
        m = await modal(pg)
        C.ok(m and m['title'] == 'Pay Bill' and 'BSW-102' in m['text'] and 'Release with a Reason' in m['text'], f'[4] Review opens the pay sheet on the check, with Release with a Reason: {m and m["title"]}')
        await shot(pg, 'pay_sheet_held_desktop')
        await pg.evaluate("() => document.querySelector('#mbm [data-pcrel]').click()")
        await pg.wait_for_timeout(150)
        await fill(pg, {'why': 'renewal binder from the carrier in hand, certificate to follow this week'})
        await press(pg)
        k = await check(pg, bill['id'])
        C.ok(k['pass'] and 'papers' in k['released'], f'[4] released by the owner with a reason, it passes: {k["released"]}')
        log = await pg.evaluate("n => { const b = DB.bills.find(x => x.number === n); return [(b.pcRel || []).map(r => [r.key, r.by, r.why]), (DB.audit || []).filter(a => a.refId === b.id && a.action === 'pay-hold-released').length]; }", 'BSW-102')
        C.ok(log[0] and log[0][0][1] == 'Owner' and log[1] == 1, f'[4] the release is logged with who and why: {log}')
        # mobilisation: the next subcontract to this sub does not issue
        res = await pg.evaluate("""() => { const po = JSON.parse(JSON.stringify(DB.pos.find(x => x.id === 'pobsw'))); Object.assign(po, {id: 'pobsw2', number: 'PO-2026-091', status: 'draft', sc: null});
            DB.pos.push(po); poAction(po, 'issue'); return [po.status, (document.getElementById('toast') || {}).innerText || '']; }""")
        C.ok(res[0] == 'draft' and 'certificate of insurance expired' in res[1], f'[4] a new subcontract to a sub with an expired COI does not issue: {res}')
        C.ok(not errs, f'[4] no page errors {errs[:2]}')
    finally:
        await b.close()


# ---------------------------------------------------------------- 5. the changed bank account
async def s5_bank(p, C):
    b, pg, errs = await boot(p)
    try:
        await paid_app1(pg)
        bill = await approved_app(pg, 'BSW-102', 70, waiver=True)
        await pg.evaluate("() => { wvAdd(DB.bills.find(x => x.number === 'BSW-101'), {type: 'unconditional', amount: 18000}); save(); }")
        k = await check(pg, bill['id'])
        C.ok(k['pass'], f'[5] before the change the payment passes: {[h["what"] for h in k["holds"]]}')
        # the coordinator enters the new account the vendor "emailed"
        await as_user(pg, 'u_chen')
        await pg.evaluate("() => { view = 'vendors'; render(); openVendor('vbsw'); }")
        await pg.wait_for_timeout(200)
        await pg.evaluate("() => { document.getElementById('e-bankname').value = 'Other Bank'; document.getElementById('e-banklast4').value = '9902'; document.getElementById('bank-request').click(); }")
        await pg.wait_for_timeout(200)
        v = await pg.evaluate("() => { const v = DB.vendors.find(x => x.id === 'vbsw'); return [v.bankPending && v.bankPending.by, v.bankPending && v.bankPending.last4, v.bank.last4]; }")
        C.ok(v == ['Chen Biron', '9902', '4471'], f'[5] the change waits with who asked; the account on file stays: {v}')
        k = await check(pg, bill['id'])
        bank = [h for h in k['holds'] if h['key'] == 'bank']
        C.ok(not k['pass'] and bank and bank[0]['fixed'] and 'someone other than Chen Biron' in bank[0]['what'], f'[5] every payment is held, and no reason releases it: {bank}')
        C.ok(bank and 'integrity' in (await pg.evaluate("() => standardPrincipleOf('pc:bank') && standardPrincipleOf('pc:bank').id")), '[5] the bank hold ranks under Integrity')
        # the requester cannot verify
        await as_user(pg, 'u_owner')
        await pg.evaluate("() => { DB.vendors.find(x => x.id === 'vbsw').bankPending.by = 'Owner'; }")
        await pg.evaluate("() => scCallBackSheet(DB.vendors.find(x => x.id === 'vbsw'))")
        await pg.wait_for_timeout(120)
        t = await toast_text(pg)
        C.ok(await modal(pg) is None and 'someone else makes the call-back' in t, f'[5] the person who asked cannot verify it: {t[:120]}')
        await pg.evaluate("() => { DB.vendors.find(x => x.id === 'vbsw').bankPending.by = 'Chen Biron'; save(); }")
        # the owner's Approvals: Verify by Phone
        await go(pg, 'mapprove')
        card = await pg.evaluate("""() => { const el = document.querySelector('.m-appr[data-mk="payhold"][data-mid="bank:vbsw"]');
            return el ? {text: el.innerText.replace(/\\s+/g, ' '), yes: (el.querySelector('[data-myes]') || {}).innerText, no: (el.querySelector('[data-mno]') || {}).innerText} : null; }""")
        C.ok(card and card['yes'] == 'Verify by Phone' and card['no'] == 'Reject', f'[5] the owner\'s Approvals: Verify by Phone or Reject: {card}')
        await pg.evaluate("() => document.querySelector('.m-appr[data-mk=\"payhold\"][data-mid=\"bank:vbsw\"] [data-myes]').click()")
        await pg.wait_for_timeout(150)
        m = await modal(pg)
        C.ok(m and '718-555-0142' in m['text'] and 'Never a number from the email' in m['text'], f'[5] the call-back names the number on file, never the request\'s: {m and m["text"][:200]}')
        await shot(pg, 'bank_callback_desktop')
        await fill(pg, {'spoke': 'Dana Ruiz, owner', 'last4': '1111'}); await press(pg)
        v = await pg.evaluate("() => DB.vendors.find(x => x.id === 'vbsw').bank.last4")
        C.ok(v == '4471' and await modal(pg) is not None, f'[5] a read-back that does not match is refused: on file ····{v}')
        await fill(pg, {'last4': '9902'}); await press(pg)
        v = await pg.evaluate("() => { const v = DB.vendors.find(x => x.id === 'vbsw'); return [v.bank.last4, !!v.bankPending, v.bankVerified && v.bankVerified.by, v.bankVerified && v.bankVerified.phone, (v.bankLog || []).length]; }")
        C.ok(v == ['9902', False, 'Owner', '718-555-0142', 1], f'[5] the owner\'s call-back applies it, logged: {v}')
        k = await check(pg, bill['id'])
        C.ok(k['pass'] and any('confirmed by phone by Owner' in x for x in k['ok']), f'[5] the payment passes, saying the account was confirmed by phone: {k["ok"][:3]}')
        # a change not verified (set straight on the record) still holds an ACH for 30 days
        await pg.evaluate("() => { const v = DB.vendors.find(x => x.id === 'vbsw'); v.bankVerified = null; v.bankChangedAt = today(); save(); }")
        k = await check(pg, bill['id'], None, 'ACH')
        C.ok(not k['pass'] and any(h['key'] == 'bank' and 'no call-back on record' in h['what'] for h in k['holds']), f'[5] a change with no call-back on record holds an ACH: {[h["what"] for h in k["holds"]]}')
        C.ok(not errs, f'[5] no page errors {errs[:2]}')
    finally:
        await b.close()


# ---------------------------------------------------------------- 6. the duplicate invoice, and the bill a card already paid
async def s6_duplicate(p, C):
    b, pg, errs = await boot(p)
    try:
        await paid_app1(pg)
        # the same invoice number entered again (the sub's email arrived twice)
        dup = await pg.evaluate("""() => { const o = DB.bills.find(x => x.number === 'BSW-101'); const d = JSON.parse(JSON.stringify(o));
            Object.assign(d, {id: 'bdup', status: 'approved', paidAt: '', payApp: null, waivers: [], waiver: null, createdBy: 'Billing', approvals: [], pcRel: []}); DB.bills.push(d); save();
            const R = pcCheck(d); return R.holds.map(h => [h.key, h.what]); }""")
        C.ok(any(k == 'dup' and 'Same invoice number as BSW-101' in w for k, w in dup), f'[6] the same invoice number is held: {dup}')
        C.ok(any(k in ('contract', 'work') for k, w in dup), f'[6] and billing it again would bill ahead of the work in place: {[w for k, w in dup if k in ("contract", "work")]}')
        # a supplier's bill the card already paid
        r = await pg.evaluate("""() => { const amex = DB.accounts.find(a => a.type === 'card') || DB.accounts[0];
            DB.vendors.push({id: 'vlum', name: 'Invented Lumber Yard', trade: '', w9: true, insuranceExp: '', bank: {name: '', last4: ''}, createdBy: 'Chen Biron'});
            const b = {id: 'blum', vendor: 'Invented Lumber Yard', number: 'ILY-5512', date: '2026-08-28', due: '2026-09-27', entityId: 'ent1', projectId: '', poId: '', cat: 'office', code: '',
                       lines: [{id: 'bl1', desc: 'Shop supplies', amount: 812.4}], payMethod: 'Check', status: 'approved', approvals: [], createdBy: 'Billing'};
            DB.bills.push(b);
            DB.txns.push({id: 'tlum', date: '2026-08-29', amt: -812.4, desc: 'INVENTED LUMBER YARD BROOKLYN', vendor: 'Invented Lumber Yard', acct: amex.id, status: 'new'});
            save(); const R = pcCheck(b); return {holds: R.holds.map(h => [h.key, h.what, h.money]), card: amex.type}; }""")
        prior = [h for h in r['holds'] if h[0] == 'prior']
        C.ok(prior and '$812.40' in prior[0][1] and 'may already have paid this bill' in prior[0][1] and prior[0][2] == 812.4, f'[6] a {r["card"]} charge of the same amount to the same vendor holds the check: {r["holds"]}')
        # it slips through anyway (paid by check here, and the card line is later tied to the same bill): the overpayment
        # becomes a credit request the coordinator approves, on Caught for You until the vendor's credit lands
        await pg.evaluate("""() => { const b = DB.bills.find(x => x.id === 'blum'); const bank = DB.accounts.find(a => a.type !== 'card') || DB.accounts[0];
            DB.txns.push({id: 'tchk', date: '2026-09-02', amt: -812.4, desc: 'CHECK 2201', acct: bank.id, status: 'new'});
            DB.payments.push({id: 'pchk', billId: b.id, entityId: 'ent1', vendor: b.vendor, date: '2026-09-01', amount: 812.4, acctId: bank.id, method: 'Check', ref: '2201', txnId: 'tchk', by: 'Controller', at: appNowIso()});
            b.status = 'paid'; b.paidAt = '2026-09-01'; DB.txns.find(t => t.id === 'tlum').billId = b.id; save(); }""")
        rows = await pg.evaluate("() => CATCH.find(c => c.name === 'vendorOverpaid').rows().map(r => [r.what, r.sub, r.amount, r.verb])")
        C.ok(rows == [['Invented Lumber Yard overpaid on ILY-5512', '$812.40 paid past the bill', 812.4, 'Request Credit']], f'[6] paid twice, by check and by card: Caught for You says $812.40 overpaid: {rows}')
        await pg.evaluate("() => CATCH.find(c => c.name === 'vendorOverpaid').rows()[0].run()")
        d = await pg.evaluate("() => { const o = (DB.outbox || []).find(x => x.kind === 'overpay-credit'); return o && [o.status, o.forName, o.subject, /Waste nothing/.test(o.because || '')]; }")
        C.ok(d and d[0] == 'draft' and d[1] == 'Chen Biron' and '$812.40' in d[2] and d[3], f'[6] Request Credit drafts the request for the coordinator to send, with its Standard line: {d}')
        rows = await pg.evaluate("() => CATCH.find(c => c.name === 'vendorOverpaid').rows().map(r => [r.sub, r.verb])")
        C.ok(rows == [['$812.40 paid past the bill; credit requested', 'Open']], f'[6] it stays caught, requested, until the money comes back: {rows}')
        await pg.evaluate("""() => { DB.bills.push({id: 'blumcm', vendor: 'Invented Lumber Yard', number: 'ILY-CM-12', date: '2026-09-03', due: '2026-09-03', entityId: 'ent1', projectId: '', poId: '', cat: 'office', code: '',
            lines: [{id: 'blcm', desc: 'Credit for duplicate payment', amount: -812.4}], payMethod: 'Check', status: 'approved', approvals: [], createdBy: 'Billing', recovers: 'blum'}); save(); }""")
        rows = await pg.evaluate("() => CATCH.find(c => c.name === 'vendorOverpaid').rows().length")
        C.ok(rows == 0, f'[6] the vendor\'s credit memo closes it: {rows} rows')
        C.ok(not errs, f'[6] no page errors {errs[:2]}')
    finally:
        await b.close()


# ---------------------------------------------------------------- 7. beyond the contract, and an approved change
async def s7_contract(p, C):
    b, pg, errs = await boot(p)
    try:
        await paid_app1(pg)
        await pg.evaluate("() => { wvAdd(DB.bills.find(x => x.number === 'BSW-101'), {type: 'unconditional', amount: 18000}); save(); }")
        # a bill for extra work the sub was never contracted for, approved by the PM and owner
        await pg.evaluate("""() => { const o = DB.bills.find(x => x.number === 'BSW-101'); const d = JSON.parse(JSON.stringify(o));
            Object.assign(d, {id: 'bext', number: 'BSW-EXTRA', date: '2026-09-02', status: 'approved', paidAt: '', payApp: null, waivers: [], waiver: null, pcRel: [], approvals: [{role: 'owner', action: 'approved for payment by Owner', by: 'Owner'}],
              lines: [{id: 'blx', desc: 'Extra landing and handrail', amount: 34000, poLineId: 'plbsw'}]});
            DB.bills.push(d); wvAdd(d, {type: 'conditional', amount: 30600}); const p = DB.projects.find(x => x.id === 'p121'); prgSet(p, p.tasks.find(t => t.id === 'tstair'), {pct: 100, by: 'Angel', role: 'foreman', src: 'field'}); save(); }""")
        k = await check(pg, 'bext')
        con = [h for h in k['holds'] if h['key'] == 'contract']
        C.ok(con and 'Billed $54,000 to date' in con[0]['what'] and '$4,000 over' in con[0]['what'] and con[0]['who'] == 'owner', f'[7] billed $54,000 against the $50,000 subcontract is held for the owner: {con}')
        # the PM adds an approved change for the landing: the contract makes room
        await as_user(pg, 'u_alan')
        await pg.evaluate("() => { poOpen = 'pobsw'; view = 'po'; render(); }")
        await pg.wait_for_timeout(150)
        await pg.evaluate("() => document.querySelector('.sc-card [data-sc=\"change\"]').click()")
        await pg.wait_for_timeout(120)
        await fill(pg, {'desc': 'Extra landing and handrail', 'amount': '4000', 'why': 'client asked on site; CO to follow'}); await press(pg)
        c = await pg.evaluate("() => { const po = DB.pos.find(x => x.id === 'pobsw'); return [scContract(po), po.sc.changes.map(x => [x.number, x.status, x.by])]; }")
        C.ok(c[0] == 54000 and c[1] == [['SCO-1', 'approved', 'Alan']], f'[7] the PM\'s change is approved as added: the subcontract is $54,000.00: {c}')
        k = await check(pg, 'bext')
        C.ok(not any(h['key'] == 'contract' for h in k['holds']), f'[7] with the change, it is within the contract: {[h["what"] for h in k["holds"]]}')
        card = await pg.evaluate("() => document.querySelector('.view.on .sc-card').innerText.replace(/\\s+/g, ' ')")
        C.ok('SCO-1' in card and '$54,000' in card, '[7] the card lists the change and the new contract')
        C.ok(not errs, f'[7] no page errors {errs[:2]}')
    finally:
        await b.close()


# ---------------------------------------------------------------- 8. retainage not held
async def s8_retainage(p, C):
    b, pg, errs = await boot(p)
    try:
        await paid_app1(pg)
        await pg.evaluate("""() => { wvAdd(DB.bills.find(x => x.number === 'BSW-101'), {type: 'unconditional', amount: 18000});
            const p = DB.projects.find(x => x.id === 'p121'); prgSet(p, p.tasks.find(t => t.id === 'tstair'), {pct: 70, by: 'Angel', role: 'foreman', src: 'field'});
            const o = DB.bills.find(x => x.number === 'BSW-101'); const d = JSON.parse(JSON.stringify(o));
            Object.assign(d, {id: 'bret', number: 'BSW-0RET', date: '2026-09-02', status: 'approved', paidAt: '', payApp: null, waivers: [], waiver: null, pcRel: [], retainagePct: 0,
              lines: [{id: 'blr', desc: 'Stair, 40% to 70%', amount: 15000, poLineId: 'plbsw'}]});
            DB.bills.push(d); wvAdd(d, {type: 'conditional', amount: 15000}); save(); }""")
        k = await check(pg, 'bret')
        ret = [h for h in k['holds'] if h['key'] == 'retainage']
        C.ok(ret and '$1,500' in ret[0]['what'] and ret[0]['money'] == 1500, f'[8] a 0% bill on a 10% subcontract is held: $1,500 should stay back: {ret}')
        await pg.evaluate("() => { view = 'ap'; render(); openBill('bret'); }")
        await pg.wait_for_timeout(200)
        await pg.evaluate("() => { const b = document.querySelector('#d-body [data-pcact=\"retain\"]'); b && b.click(); }")
        await pg.wait_for_timeout(200)
        r = await pg.evaluate("() => { const b = DB.bills.find(x => x.id === 'bret'); return [b.retainagePct, billGross(b), billTotal(b)]; }")
        C.ok(r == [10, 15000, 13500], f'[8] Hold 10% sets the subcontract\'s rate: $13,500.00 payable, $1,500.00 held: {r}')
        k = await check(pg, 'bret', 13500)
        C.ok(not any(h['key'] == 'retainage' for h in k['holds']), f'[8] the retainage hold clears: {[h["what"] for h in k["holds"]]}')
        # retainage is released only at the milestone, with a final waiver
        await pg.evaluate("() => { signIn('u_owner'); releaseRetainage(DB.vendors.find(v => v.id === 'vbsw'), 'p121', 1); const b = DB.bills.filter(x => x.retainageRelease && x.vendor === 'Brooklyn Stair Works').pop(); b.status = 'approved'; save(); }")
        rel = await pg.evaluate("() => { const b = DB.bills.filter(x => x.retainageRelease && x.vendor === 'Brooklyn Stair Works').pop(); const R = pcCheck(b); return {amt: billTotal(b), holds: R.holds.map(h => [h.key, h.what])}; }")
        C.ok(rel['amt'] == 3500 and any(k == 'retainage' and 'released at substantial completion' in w for k, w in rel['holds']) and any(k == 'waiver' and 'final' in w for k, w in rel['holds']),
             f'[8] the $3,500 release waits for substantial completion and a final waiver: {rel}')
        C.ok(not errs, f'[8] no page errors {errs[:2]}')
    finally:
        await b.close()


# ---------------------------------------------------------------- 9. an open vendor credit is taken first
async def s9_credit(p, C):
    b, pg, errs = await boot(p)
    try:
        await paid_app1(pg)
        bill = await approved_app(pg, 'BSW-102', 70, waiver=True)
        await pg.evaluate("""() => { wvAdd(DB.bills.find(x => x.number === 'BSW-101'), {type: 'unconditional', amount: 18000});
            DB.bills.push({id: 'bcm', vendor: 'Brooklyn Stair Works', number: 'BSW-CM-7', date: '2026-08-30', due: '2026-08-30', entityId: 'ent1', projectId: 'p121', poId: '', cat: 'subs', code: '',
              lines: [{id: 'blc', desc: 'Credit: damaged treads replaced by the sub', amount: -750}], payMethod: 'ACH', status: 'approved', approvals: [], createdBy: 'Billing'}); save(); }""")
        k = await check(pg, bill['id'])
        cr = [h for h in k['holds'] if h['key'] == 'credits']
        C.ok(cr and '$750' in cr[0]['what'] and 'BSW-CM-7' in cr[0]['what'], f'[9] the open $750 credit holds new money: {cr}')
        await as_user(pg, 'u_controller')
        await pg.evaluate("id => pcPaySheet(id)", bill['id'])
        await pg.wait_for_timeout(150)
        await pg.evaluate("() => document.querySelector('#mbm [data-pcact=\"credit\"]').click()")
        await pg.wait_for_timeout(250)
        r = await pg.evaluate("id => { const b = DB.bills.find(x => x.id === id); const c = DB.bills.find(x => x.id === 'bcm'); return [pcOpen(b), scCreditsTaken(b), c.status]; }", bill['id'])
        C.ok(r == [12750, 750, 'paid'], f'[9] the credit is taken: $12,750.00 left to pay of $13,500.00, the credit used up: {r}')
        m, t = await pay_sheet(pg, bill['id'])
        r = await pg.evaluate("id => { const b = DB.bills.find(x => x.id === id); return [b.status, DB.payments.filter(p => p.billId === id).map(p => p.amount)]; }", bill['id'])
        C.ok(r == ['paid', [12750]], f'[9] then $12,750.00 goes out and the bill is paid: {r}')
        L = await pg.evaluate("() => { const L = scLedger('Brooklyn Stair Works', 'p121'); return [L.paid, L.creditsOpen]; }")
        C.ok(L == [30750, 0], f'[9] the ledger: $30,750.00 paid, no credit open: {L}')
        C.ok(not errs, f'[9] no page errors {errs[:2]}')
    finally:
        await b.close()


# ---------------------------------------------------------------- 10. the payment run
async def s10_run(p, C):
    b, pg, errs = await boot(p)
    try:
        await paid_app1(pg)
        await approved_app(pg, 'BSW-102', 70, waiver=True)
        await pg.evaluate("() => { wvAdd(DB.bills.find(x => x.number === 'BSW-101'), {type: 'unconditional', amount: 18000}); save(); }")
        # a second approved bill that is held (a supplier with no W-9)
        await pg.evaluate("""() => { DB.vendors.push({id: 'vnow9', name: 'Invented Hardware Co', trade: '', w9: false, insuranceExp: '', bank: {name: '', last4: ''}});
            DB.bills.push({id: 'bnow9', vendor: 'Invented Hardware Co', number: 'IHC-77', date: '2026-08-31', due: '2026-09-30', entityId: 'ent1', projectId: '', poId: '', cat: 'office', code: '',
              lines: [{id: 'bl9', desc: 'Door hardware samples', amount: 1240}], payMethod: 'Check', status: 'approved', approvals: [], createdBy: 'Billing'}); save(); }""")
        await as_user(pg, 'u_controller')
        await go(pg, 'ap')
        run = await pg.evaluate("""() => { const c = document.getElementById('pc-run'); if (!c) return null;
            return {text: c.innerText.replace(/\\s+/g, ' '), boxes: [...c.querySelectorAll('[data-pcrun]')].map(x => [x.dataset.pcrun, x.checked, x.disabled])}; }""")
        C.ok(run and 'Payment Run' in run['text'] and 'Held · 1' in run['text'] and 'No W-9 on file for Invented Hardware Co' in run['text'], f'[10] the run lists both, the held one with why: {run and run["text"][:300]}')
        C.ok(run and ['bnow9', False, True] in run['boxes'], f'[10] the held bill cannot be ticked: {run and run["boxes"]}')
        await shot(pg, 'payment_run_desktop')
        await pg.evaluate("() => document.getElementById('pc-run-go').click()")
        await pg.wait_for_timeout(150)
        m = await modal(pg)
        C.ok(m and m['title'] == 'Pay the Checked Bills', f'[10] Pay the Checked Bills opens its sheet: {m and m["title"]}')
        await press(pg)
        r = await pg.evaluate("() => [DB.bills.find(x => x.number === 'BSW-102').status, DB.bills.find(x => x.id === 'bnow9').status, DB.payments.filter(p => p.run).map(p => [p.vendor, p.amount, p.check.pass])]")
        C.ok(r[0] == 'paid' and r[1] == 'approved' and r[2] == [['Brooklyn Stair Works', 13500, True]], f'[10] only the checked bill is paid, stamped with its check: {r}')
        t = await toast_text(pg)
        C.ok('1 payment recorded' in t and '$13,500' in t and 'Open' in t, f'[10] the toast says what was paid, with Open: {t[:160]}')
        C.ok(not errs, f'[10] no page errors {errs[:2]}')
    finally:
        await b.close()


# ---------------------------------------------------------------- 11. the books: AP, job cost, retainage payable, 1099, ledger, Ask
async def s11_books(p, C):
    b, pg, errs = await boot(p)
    try:
        base = await pg.evaluate("""() => { const p = DB.projects.find(x => x.id === 'p121'); const J = jobFin(p);
            const g = glBalances({entityId: 'all', to: today()}); return {actual: J.actual, ret: (g[2050] || {}).bal || 0, ap: (g[2000] || {}).bal || 0}; }""")
        await paid_app1(pg)
        await approved_app(pg, 'BSW-102', 70, waiver=True)
        after = await pg.evaluate("""() => { const p = DB.projects.find(x => x.id === 'p121'); const J = jobFin(p);
            const g = glBalances({entityId: 'all', to: today()}); return {actual: J.actual, ret: (g[2050] || {}).bal || 0, ap: (g[2000] || {}).bal || 0,
              held: apRetainage('Brooklyn Stair Works', 'p121'), r1099: (fin2Register1099().rows.find(r => r.v.name === 'Brooklyn Stair Works') || {}).paid}; }""")
        C.ok(round(after['actual'] - base['actual'], 2) == 35000, f'[11] job cost carries both applications at gross, $35,000.00 (retainage is cost when billed): {after["actual"] - base["actual"]}')
        C.ok(round(abs(after['ret'] - base['ret']), 2) == 3500, f'[11] retainage payable (2050) moves $3,500.00: {after["ret"] - base["ret"]}')
        C.ok(after['held'] == 3500, f'[11] the retainage held from the sub reads $3,500.00: {after["held"]}')
        C.ok(after['r1099'] == 18000, f'[11] the 1099 register counts the $18,000.00 paid: {after["r1099"]}')
        L = await pg.evaluate("() => { const r = eqRows('vendorledger').find(x => x.vendor === 'Brooklyn Stair Works' && x.projectId === 'p121'); return r; }")
        C.ok(L and [L['contract'], L['billed'], L['paid'], L['payable'], L['retainageHeld'], L['balanceToFinish'], L['left']] == [50000, 35000, 18000, 13500, 3500, 15000, 32000],
             f'[11] the ledger: contract 50,000, billed 35,000, paid 18,000, 13,500 to pay, 3,500 retainage, 15,000 to bill, 32,000 left: {L}')
        a = await pg.evaluate("() => paAsk(\"what have we paid Brooklyn Stair Works on 121 State, and what's left?\")")
        C.ok('paid $18,000' in a['headline'] and '$32,000 left to pay' in a['headline'] and '$3,500 retainage held' in a['headline'], f'[11] Ask answers from the ledger: {a["headline"][:240]}')
        C.ok('vendor ledger' in (a.get('ran') or a.get('interp') or ''), f'[11] and says what it ran: {a.get("ran") or a.get("interp")}')
        a = await pg.evaluate("() => paAsk('which payments are held')")
        C.ok('Brooklyn Stair Works BSW-102' in a['headline'] and 'unconditional lien waiver' in a['headline'], f'[11] Ask names the held payment and why: {a["headline"][:200]}')
        # field roles read no money: the foreman's query of the ledger is empty
        await as_user(pg, 'u_angel')
        f = await pg.evaluate("() => [eqRows('vendorledger').length, eqRows('paymentholds').length, eqRows('waiverrows').length]")
        C.ok(f == [0, 0, 0], f'[11] the foreman reads none of the ledger, holds or waivers: {f}')
        C.ok(not errs, f'[11] no page errors {errs[:2]}')
    finally:
        await b.close()


# ---------------------------------------------------------------- 12. the owner on a phone
async def s12_phone(p, C):
    b, pg, errs = await boot(p, phone=True)
    try:
        await paid_app1(pg)
        bill = await approved_app(pg, 'BSW-102', 70, waiver=True)
        await as_user(pg, 'u_owner')
        await go(pg, 'mapprove')
        card = await pg.evaluate("""id => { const el = document.querySelector(`.m-appr[data-mk="payhold"][data-mid="${id}"]`); if (!el) return null;
            const y = el.querySelector('[data-myes]'); const r = y.getBoundingClientRect(); return {text: el.innerText.replace(/\\s+/g, ' '), h: r.height}; }""", bill['id'])
        C.ok(card and 'unconditional lien waiver' in card['text'], f'[12 phone] the held payment is on the owner\'s Approvals: {card and card["text"][:160]}')
        C.ok(card and card['h'] >= 40, f'[12 phone] its Review button is a thumb target: {card and card["h"]}')
        C.ok(await no_hscroll(pg), '[12 phone] Approvals does not scroll sideways')
        await shot(pg, 'approvals_payhold_phone')
        await pg.evaluate("id => document.querySelector(`.m-appr[data-mk=\"payhold\"][data-mid=\"${id}\"] [data-myes]`).click()", bill['id'])
        await pg.wait_for_timeout(200)
        m = await modal(pg)
        C.ok(m and m['title'] == 'Pay Bill' and 'payment check' in m['text'].lower(), f'[12 phone] Review opens the pay sheet on the check: {m and m["title"]}')
        wide = await pg.evaluate("() => { const b = document.querySelector('#mbm .mbm-box'); return b ? b.getBoundingClientRect().right <= innerWidth + 1 : false; }")
        C.ok(wide and await no_hscroll(pg), '[12 phone] the sheet fits the phone')
        await shot(pg, 'pay_sheet_held_phone')
        await pg.evaluate("() => { mbCloseModal(); view = 'ap'; render(); openBill(DB.bills.find(x => x.number === 'BSW-102').id); }")
        await pg.wait_for_timeout(250)
        C.ok(await no_hscroll(pg), '[12 phone] the bill with its check and waivers does not scroll sideways')
        await shot(pg, 'bill_check_phone')
        await pg.evaluate("() => { try { closeEditor(); } catch (e) {} signIn('u_alan'); poOpen = 'pobsw'; view = 'po'; render(); }")
        await pg.wait_for_timeout(200)
        await pg.evaluate("() => document.querySelector('.sc-card [data-sc=\"payapp\"]').click()")
        await pg.wait_for_timeout(200)
        C.ok(await no_hscroll(pg), '[12 phone] the New Pay Application sheet fits the phone')
        await shot(pg, 'payapp_sheet_phone')
        C.ok(not errs, f'[12 phone] no page errors {errs[:2]}')
    finally:
        await b.close()


SCEN = [('subcontract', s1_subcontract), ('overbilled', s2_overbilled), ('waiver', s3_waiver), ('coi', s4_coi), ('bank', s5_bank),
        ('duplicate', s6_duplicate), ('contract', s7_contract), ('retainage', s8_retainage), ('credit', s9_credit), ('run', s10_run),
        ('books', s11_books), ('phone', s12_phone)]


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scenario', nargs='*')
    a = ap.parse_args()
    want = set(a.scenario or [])
    C = Checks()
    async with async_playwright() as p:
        for i, (name, fn) in enumerate(SCEN, 1):
            if want and name not in want and str(i) not in want: continue
            print(f'-- {i} {name}')
            try:
                await fn(p, C)
            except Exception as e:
                C.ok(False, f'[{i} {name}] raised {type(e).__name__}: {e}')
    print(f'{len(C.fail)} flags')
    sys.exit(C.done())


asyncio.run(main())
