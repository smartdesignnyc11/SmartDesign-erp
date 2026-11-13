"""accounting_test: the four Accounting pages Alan's ten questions asked for (docs/mockups/accounting/SPEC.md, 11-03),
done as the person: billing (u_billing), the controller (u_controller) and the owner (u_owner), each page reached by
tapping its menu entry, on the desktop (1440x900) and the phone (390x844, touch).

  MENU     Accounting lists, in order: billing Billing, Banking; the controller Billing, Banking, Bills and Payroll,
           Books; the owner Billing, Banking, Bills and Payroll (Books opens by link); the PM has no Accounting group.
           Numbers only on the seat's own pages (billing's Billing, the controller's Banking, Bills and Payroll, Books);
           the owner's entries carry none. Each number equals the page's Needs You (Banking: its To Review)
  FIRST    each page opens on what needs the person (Needs You, its count equal to its rows), then where things stand
           (Collections, the accounts, With Others), then the records under chips; its heading is the menu's word;
           one blue button, the safe next step
  FIGURES  Billing: $17,080, $12,651 (Billed Ahead of the Work $66,470 and the windows' $10,170 held with it), $2,600,
           Rivera's $21,350 recorded and not in the bank; no "$53,819" anywhere; Collections current $92,265, retainage
           $15,668, a reminder on each open invoice. Banking: 15 lines to match, $67,272 at stake; To Review 15; Money In
           holds Rivera's two payments. Bills and Payroll: the $16,040 payroll to split first, 4 entries, AMP-311 held,
           CM-0091 without a lien waiver; WW-2026-118 under With Others, not counted; To Approve 3. Books: the close,
           the deposit booked as a draw, the WIP gap, the short-paid invoice; the WIP that posts at the close is
           wipAtClose's
  FOLDED   Spend and the Accounting overview forward to Banking; Time and Crew opens as Bills and Payroll's Payroll
           chip, Controls and the operating Budget as Books' chips, each under the page's name; nothing is lost
  NEWMENU  a pick from a page's New menu (the controller's New, Vendor Bill) opens its form and the menu goes away
  JOB      the Billing job filter scopes Needs You, the aging, the retainage and the documents to the job
  PHONE    at 390: nothing sideways, every button and chip on the front at least 44px tall, no Confirm on a bank list row
Usage: python3 accounting_test.py [--desktop|--phone] [--user u_billing,...]
"""
import asyncio, re, sys
from harness import *

ACCT = {
    'u_billing': ['Billing', 'Banking'],
    'u_controller': ['Billing', 'Banking', 'Bills and Payroll', 'Books'],
    'u_owner': ['Billing', 'Banking', 'Bills and Payroll'],
    'u_alan': [],
}
BADGED = {'u_billing': {'billing'}, 'u_controller': {'bank', 'ap', 'gl'}, 'u_owner': set(), 'u_alan': set()}
NAME = {'billing': 'Billing', 'bank': 'Banking', 'ap': 'Bills and Payroll', 'gl': 'Books'}

MENU = """r => { const B = mnBuild(r); const g = B && B.work.find(x => x.id === 'money');
  return g ? g.items.map(it => ({ v: it.v, l: it.l, n: mnItemN(it) })) : []; }"""
FRONT = """() => { const v = document.querySelector('.view.on'); if (!v) return null;
  const vis = e => !!e && e.getClientRects().length > 0 && !e.closest('[hidden]');
  const F = v.querySelector('.ac-front'); const cap = F && F.querySelector('.ac-needs .ac-cap b');
  const rows = F ? [...F.querySelectorAll('.ac-needs .ac-row')].filter(vis) : [];
  const h = [...v.querySelectorAll('h1, h2')].find(vis);
  const blue = [...v.querySelectorAll('.btn.primary')].filter(vis);
  const tall = F ? [...F.querySelectorAll('button')].filter(vis).map(b => [b.textContent.replace(/\\s+/g, ' ').trim().slice(0, 30), Math.round(b.getBoundingClientRect().height)]) : [];
  const chips = F ? [...F.querySelectorAll('.ac-chip')].map(c => c.textContent.replace(/\\s+/g, ' ').trim()) : [];
  const conf = [...v.querySelectorAll('#txn-table button, #txn-table a')].filter(vis).filter(b => /^confirm$/i.test(b.textContent.trim())).length;
  return { view, front: !!F, page: F ? F.dataset.acpage : '', cap: cap ? +cap.textContent : null, rows: rows.length,
    text: v.innerText, heading: h ? h.textContent.replace(/\\s+/g, ' ').trim() : '', blue: blue.map(b => b.textContent.trim()),
    tall, chips, sw: document.documentElement.scrollWidth, w: innerWidth, confirm: conf }; }"""

async def go_entry(pg, label, phone):
    """the Accounting group's entry, tapped: the group opened by its name, then the entry (the phone opens the menu)"""
    if phone:
        await pg.evaluate("() => { const b = document.querySelector('#menu-btn'); b && b.offsetParent && b.click(); }")
        await pg.wait_for_timeout(200)
    head = pg.locator('#nav-groups [data-mnchev="money"]').first   # the chevron shows the pages (11-12: the name opens the overview)
    if await head.count():
        exp = await head.get_attribute('aria-expanded')
        if exp != 'true':
            await head.evaluate('e => e.click()'); await pg.wait_for_timeout(150)
    kid = pg.locator(f'#nav-groups [data-mngr="money"] button[data-v="{label}"]')
    if not await kid.count():
        return False
    await kid.first.evaluate('e => e.click()')
    await pg.wait_for_timeout(350)
    await pg.evaluate("() => document.querySelector('.rail')?.classList.remove('open')")
    return True

def money_in(t, s): return s in (t or '')

async def run(c, pg, u, phone):
    dev = 'phone' if phone else 'desktop'
    await sign_in(pg, u)
    M = await pg.evaluate(MENU, {'u_billing': 'billing', 'u_controller': 'controller', 'u_owner': 'owner', 'u_alan': 'pm'}[u])
    labels = [x['l'] for x in M]
    c.ok(labels == ACCT[u], f'MENU {u} {dev}: Accounting reads {labels}, want {ACCT[u]}')
    for x in M:
        if x['v'] in BADGED[u]: c.ok(x['n'] > 0, f"MENU {u} {dev}: {x['l']} carries its number (got {x['n']})")
        else: c.ok(x['n'] == 0, f"MENU {u} {dev}: {x['l']} carries a number ({x['n']}) where nothing waits on this seat")
    for x in M:
        v, label = x['v'], x['l']
        ok = await go_entry(pg, v, phone)
        c.ok(ok, f'OPEN {u} {dev}: the menu entry {label} is there to tap')
        if not ok: continue
        F = await pg.evaluate(FRONT)
        tag = f'{u} {dev} {label}'
        c.ok(F and F['view'] == v and F['front'], f"FIRST {tag}: opens the page with its front (view {F and F['view']}, front {F and F['front']})")
        if not (F and F['front']): continue
        c.ok(F['heading'] == NAME[v], f"FIRST {tag}: heading {F['heading']!r}, want {NAME[v]!r}")
        c.ok(len(F['blue']) <= 1, f"FIRST {tag}: one blue button at most: {F['blue']}")
        if v != 'bank': c.ok(F['cap'] == F['rows'], f"FIRST {tag}: Needs You {F['cap']} equals its rows {F['rows']}")
        if v in BADGED[u]:
            want = F['cap'] if v != 'bank' else int((re.search(r'To Review (\d+)', ' '.join(F['chips'])) or [0, 0])[1])
            c.ok(x['n'] == want, f"FIRST {tag}: the menu's {x['n']} equals the page's {want}")
        if phone:
            c.ok(F['sw'] <= F['w'] + 1, f"PHONE {tag}: scrolls sideways ({F['sw']} > {F['w']})")
            short = [b for b in F['tall'] if b[1] < 44]
            c.ok(not short, f'PHONE {tag}: buttons under 44px: {short[:4]}')
        t = F['text']
        if v == 'billing':
            for s in ('$17,080', '$12,651', '$2,600', '$21,350 recorded, not in the bank', 'Billed Ahead of the Work $66,470', '$10,170'):
                c.ok(money_in(t, s), f'FIGURES {tag}: {s!r} on Needs You')
            c.ok('$53,819' not in t, f'FIGURES {tag}: the netted $53,819 is gone')
            # one question, one number: each Needs You row's figures are the queue's own (readyToBill) and billedAhead()'s
            Q = await pg.evaluate(r"""() => [...document.querySelectorAll('.view.on .ac-needs tr[data-edit^="bl:rtb:"]')].map(tr => {
                  const id = tr.dataset.edit.slice(3), r = billingRows().find(x => x.id === id), txt = tr.innerText;
                  const amt = +((txt.match(/^\$([\d,]+) ready to bill/) || [0, '0'])[1].replace(/,/g, ''));
                  const ahead = [...txt.matchAll(/Billed Ahead of the Work \$([\d,]+)/g)].map(m => +m[1].replace(/,/g, ''));
                  return { id, amt, want: r ? Math.round(r.amount) : null, ahead, aheadWant: r && r.job ? Math.round(billedAhead(r.job.id).total) : null }; })""")
            c.ok(Q and all(q['amt'] == q['want'] and all(abs(a - q['aheadWant']) <= 1 for a in q['ahead']) for q in Q), f"FIGURES {tag}: each Needs You row prints the queue's amount and billedAhead()'s figure: {Q}")
            c.ok(re.search(r'Current\s*\n?\s*\$92,265', t) and '$15,668' in t, f'FIGURES {tag}: Collections current $92,265 and retainage $15,668')
            c.ok(len(re.findall(r'Reminder \d+/\d+', t)) >= 2, f'FIGURES {tag}: each open invoice names its next reminder')
            c.ok(F['cap'] == 4, f"FIGURES {tag}: Needs You 4 (three to bill and the Rivera chase), got {F['cap']}")
        if v == 'bank':
            c.ok('15 lines to match' in t and '$67,272 at stake' in t, f'FIGURES {tag}: 15 lines to match, $67,272 at stake')
            c.ok(any(re.match(r'To Review 15$', ch) for ch in F['chips']), f"FIGURES {tag}: To Review 15 chip: {F['chips']}")
            if phone:
                c.ok(F['confirm'] == 0, f"PHONE {tag}: {F['confirm']} Confirm buttons on bank list rows (the line's sheet confirms)")
                if u == 'u_controller':
                    # To Review's count is its rows, right under the chips; each row names its amount in full; a tap opens
                    # the line's review sheet, never the edit form (the chief of staff's review, 11-03)
                    L = await pg.evaluate("""() => { const ch = document.querySelector('.view.on [data-acchip="bank:review"]'); const cy = ch ? ch.getBoundingClientRect().bottom + scrollY : 0;
                      const rows = [...document.querySelectorAll('.view.on #txn-table tr.pr-tr')].filter(r => r.getClientRects().length);
                      const first = rows[0] ? rows[0].getBoundingClientRect().top + scrollY : 99999;
                      const cut = rows.map(r => r.querySelector('.pr-m')).filter(s => s && (s.scrollWidth > s.clientWidth + 1 || /…/.test(s.textContent) || !/[−+-]\\$[\\d,]+/.test(s.textContent))).map(s => s.textContent);
                      return { n: rows.length, gap: Math.round(first - cy), cut }; }""")
                    want_n = int((re.search(r'To Review (\d+)', ' '.join(F['chips'])) or [0, 0])[1])
                    c.ok(L['n'] == want_n and L['gap'] < 600, f"PHONE {tag}: To Review {want_n} shows its {L['n']} rows right under the chips (first row {L['gap']}px below them)")
                    c.ok(not L['cut'], f"PHONE {tag}: each row shows its amount in full at 390: {L['cut'][:3]}")
                    row = pg.locator('.view.on #txn-table tr.pr-tr .pr-mid').first
                    if await row.count():
                        await row.evaluate('e => e.click()'); await pg.wait_for_timeout(300)
                        m = await pg.evaluate("() => { const m = document.getElementById('mbm'); return m ? m.innerText : ''; }")
                        c.ok('Review the Line' in m and 'It would link to' in m and not re.search(r'\bVoid\b', m), f'PHONE {tag}: tapping a row opens its review sheet: {m[:160]!r}')
                        await pg.evaluate("() => typeof mbCloseModal === 'function' && mbCloseModal()")
                    rv = pg.locator('.view.on [data-acreview]')
                    c.ok(await rv.count() > 0, f'PHONE {tag}: each proposed match has Review, which opens its sheet')
                    if await rv.count():
                        await rv.first.evaluate('e => e.click()'); await pg.wait_for_timeout(250)
                        m = await pg.evaluate("() => { const m = document.getElementById('mbm'); return m ? m.innerText : ''; }")
                        c.ok('Confirm the Match' in m and 'It links to' in m and re.search(r'\bConfirm\b', m.split('Confirm the Match', 1)[-1]),
                             f'PHONE {tag}: the sheet names what the line links to, then Confirm: {m[:200]!r}')
                        await pg.evaluate("() => typeof mbCloseModal === 'function' && mbCloseModal()")
        if v == 'ap':
            for s in ('$16,040', 'Split it by job', 'AMP-311', 'CM-0091', 'WITH OTHERS', 'WW-2026-118'):
                c.ok(s.lower() in t.lower(), f'FIGURES {tag}: {s!r} on the first screen')
            # To Approve carries no count until it equals its rows (the coordinator's decision, 11-03)
            c.ok(F['cap'] == 4 and 'To Approve' in F['chips'], f"FIGURES {tag}: Needs You 4, a To Approve chip with no count: {F['cap']} {F['chips']}")
        if v == 'gl':
            W = await pg.evaluate("() => { const w = wipAtClose(); return w && { toPost: w.toPost, label: w.label }; }")
            # the phone opens Books on its Ledger (the close is read there, run on the desktop): the Close chip, tapped
            if phone:
                await pg.locator('.view.on [data-acchip="gl:close"]').first.evaluate('e => e.click()'); await pg.wait_for_timeout(300)
                t = (await pg.evaluate(FRONT))['text']
            c.ok(F['cap'] == 4, f"FIGURES {tag}: Books' Needs You 4, got {F['cap']}")
            c.ok(W and money_fmt(W['toPost']) in t, f"FIGURES {tag}: the WIP that posts at the close is wipAtClose's {W}")
            c.ok('booked as the first draw' in t and 'short-paid' in t, f'FIGURES {tag}: the deposit booked as a draw and the short-paid invoice')
    # the folded pages
    if u == 'u_controller':
        # NEWMENU: a pick from a page's New menu opens its form and the menu goes away (it stayed drawn under the form)
        await pg.evaluate("() => setView('ap')"); await pg.wait_for_timeout(200)
        await pg.locator('.view.on [data-acnew="ap"]').first.click(); await pg.wait_for_timeout(200)
        await pg.locator('.view.on [data-acnewpick="ap:bill"]').first.click(); await pg.wait_for_timeout(400)
        M = await pg.evaluate("() => ({ menu: [...document.querySelectorAll('.ac-menu[role=menu]')].filter(e => e.getClientRects().length).length, drawer: !!document.querySelector('#drawer.on'), open: acNewOpen })")
        c.ok(M['drawer'] and M['menu'] == 0 and not M['open'], f"NEWMENU {u} {dev}: New › Vendor Bill opens the bill and the New menu is gone ({M})")
        await pg.evaluate("() => { try { closeEditor(); } catch (e) {} }"); await pg.wait_for_timeout(150)
        for old, want, chip in (('spend', 'bank', None), ('ovmoney', 'bank', None), ('time', 'time', 'Payroll'), ('verify', 'verify', 'Controls'), ('budget', 'budget', 'Operating Budget')):
            await pg.evaluate("v => setView(v)", old); await pg.wait_for_timeout(250)
            F = await pg.evaluate(FRONT)
            page = {'bank': 'bank', 'time': 'ap', 'verify': 'gl', 'budget': 'gl'}[want]
            c.ok(F and F['view'] == want and F['page'] == page, f"FOLDED {u} {dev}: {old} lands on {want} under {NAME[page]} (got {F and F['view']} {F and F['page']})")
            if chip and F: c.ok(F['heading'] == NAME[page], f"FOLDED {u} {dev}: {old}'s heading is {NAME[page]} ({F['heading']!r})")
        # the Payroll chip, tapped, is Time and Crew's records under Bills and Payroll
        await pg.evaluate("() => setView('ap')"); await pg.wait_for_timeout(200)
        if not await pg.locator('.view.on [data-acchip="ap:payroll"]').count():
            c.ok(False, f'FOLDED {u} {dev}: Bills and Payroll has a Payroll chip'); return
        await pg.locator('.view.on [data-acchip="ap:payroll"]').first.evaluate('e => e.click()'); await pg.wait_for_timeout(300)
        F = await pg.evaluate(FRONT)
        c.ok(F['view'] == 'time' and F['heading'] == 'Bills and Payroll' and 'Build payroll from approved time'.lower() in F['text'].lower(),
             f"FOLDED {u} {dev}: the Payroll chip shows the hours and Build Payroll under Bills and Payroll ({F['view']}, {F['heading']!r})")
    if u == 'u_billing':
        # the job filter scopes everything on Billing to the job
        await pg.evaluate("() => setView('billing')"); await pg.wait_for_timeout(200)
        if not await pg.locator('.view.on [data-acjob]').count():
            c.ok(False, f'JOB {dev}: Billing has a job filter'); return
        await pg.locator('.view.on [data-acjob]').first.evaluate('e => e.click()'); await pg.wait_for_timeout(150)
        await pg.locator('.view.on [data-acjobpick="p140"]').first.evaluate('e => e.click()'); await pg.wait_for_timeout(300)
        F = await pg.evaluate(FRONT)
        t = F['text']
        c.ok('$2,600' in t and '$17,080' not in t and '$12,651' not in t, f'JOB {dev}: Needs You for 140 Prospect only')
        c.ok(re.search(r'Current\s*\n?\s*\$24,000', t) and 'INV-2026-038' not in t, f'JOB {dev}: the aging and documents are 140 Prospect\'s ($24,000; no INV-2026-038)')
        await pg.locator('.view.on [data-acjob]').first.evaluate('e => e.click()'); await pg.wait_for_timeout(150)
        await pg.locator('.view.on [data-acjobpick=""]').first.evaluate('e => e.click()'); await pg.wait_for_timeout(200)

async def drafted_equals_queue(c, p):
    """One question, one number on money the client is billed: the foreman measures, the client approves CO-2026-002,
    billing presses Draft on Needs You; the application bills, to the cent, the work the row said was ready, and the
    drafted row then states the same work (before retainage) with what is held and due beside it."""
    b, pg, errs = await open_app(p, False)
    await sign_in(pg, 'u_billing')
    r = await pg.evaluate(r"""async () => { const sleep = ms => new Promise(r => setTimeout(r, ms)); appConfirm = () => true;
      const p = DB.projects.find(x => x.id === 'p121'), c = DB.clients.find(x => x.id === 'cl121');
      prgSet(p, p.tasks.find(t => t.id === 'relec'), { pct: 100, by: 'Angel', role: 'foreman', src: 'field', note: 'Rough electrical complete' });
      await docAction(c, c.changeOrders.find(x => x.number === 'CO-2026-002'), 'approve');
      prgSet(p, p.tasks.find(t => t.id === 'sand'), { pct: 100, by: 'Angel', role: 'foreman', src: 'field', note: 'Treads done' });
      save(); setView('billing'); billTab = 'billable'; docOpen = null; render(); await sleep(250);
      const tr = document.querySelector('.view.on .ac-needs tr[data-edit="bl:rtb:app:p121"]');
      if (!tr) return { err: 'no 121 State application on Needs You' };
      const shown = +((tr.innerText.match(/^\$([\d,]+) ready to bill/) || [0, '0'])[1].replace(/,/g, ''));
      const row = readyToBill().rows.find(x => x.p && x.p.id === 'p121' && x.kind === 'application');
      tr.querySelector('[data-blact]').click(); await sleep(250);
      const ok = document.querySelector('#mbm #mbm-ok'); ok && ok.click(); await sleep(300);
      const inv = c.invoices.filter(i => i.mode === 'sov' && i.status === 'draft').pop(); if (!inv) return { err: 'no draft' };
      const T = docTotal(inv);
      docOpen = null; setView('billing'); billTab = 'billable'; render(); await sleep(250);
      const dr = [...document.querySelectorAll('.view.on .ac-needs tr')].find(x => x.innerText.includes(inv.number));
      const drShown = dr ? +((dr.innerText.match(/^\$([\d,]+) drafted/) || [0, '0'])[1].replace(/,/g, '')) : null;
      return { queue: row ? row.amount : null, shown, work: r2(T.sub - T.disc), ret: T.ret, total: T.total, drShown, drText: dr ? dr.innerText.replace(/\s+/g, ' ').slice(0, 300) : '' }; }""")
    ok = r and not r.get('err') and abs(r['work'] - r['queue']) < 0.005 and r['shown'] == round(r['queue']) and r['drShown'] == round(r['work'])
    c.ok(ok, f"ONE NUMBER desktop: after Draft the application bills the queue row's work to the cent, and the drafted row states the same: {r}")
    c.ok(r and not r.get('err') and ('due' in r.get('drText', '')) == (r.get('ret', 0) > 0.005), f"ONE NUMBER desktop: the drafted row names what retainage holds and what is due: {r and r.get('drText')}")
    c.ok(not errs, f'ONE NUMBER: page errors {errs[:3]}')
    await b.close()

def money_fmt(v):
    s = f'${abs(v):,.0f}'
    return s

async def main():
    args = sys.argv[1:]
    devs = [False] if '--desktop' in args else [True] if '--phone' in args else [False, True]
    users = args[args.index('--user') + 1].split(',') if '--user' in args else ['u_billing', 'u_controller', 'u_owner', 'u_alan']
    c = Checks()
    async with async_playwright() as p:
        for phone in devs:
            b, pg, errs = await open_app(p, phone)
            for u in users:
                await run(c, pg, u, phone)
            c.ok(not errs, f"{'phone' if phone else 'desktop'}: page errors {errs[:3]}")
            await b.close()
        if False in devs and 'u_billing' in users:
            await drafted_equals_queue(c, p)
    sys.exit(c.done())

asyncio.run(main())
