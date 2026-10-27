"""Money leaks are caught (BACKLOG.md §0 item 6, the north star in CLAUDE.md).

Each scenario starts from a fresh browser (fresh seeded DB, app day 2026-09-03), injects one leak through the
app's OWN paths — the statement import dialog (a real OFX/CSV file through the file input), the transaction
and bill drawers, docAction, prgSet, cmImport — never by editing totals, and then asks:
  (a) does it surface on the screen the responsible person works from, with a link to the record and a
      proposed action, and
  (b) does Ask answer a natural question about it.
Each scenario prints CAUGHT / PARTIAL (what is missing) / MISSED. The last line is `N flags` (PARTIAL + MISSED);
exit 1 when N > 0.

    python3 leak_test.py                 # all six
    python3 leak_test.py --scenario 1,3  # a subset (numbers or names: reimb, unbilled, overspend, refund, trace, slip)
    python3 leak_test.py --json          # machine-readable result on the last line

All demo data here is invented (vendors, amounts, references)."""
import asyncio, sys, json, argparse
from harness import *

TODAY = '2026-09-03'
JOB = 'p121'          # 121 State Street (client cl121, Sarah & David Klein)

# ---------------------------------------------------------------- page helpers (installed once per page)
PAGE_HELPERS = r"""
() => {
  // Money needles in every format the app might print an amount in.
  window.__lkNeedles = (vals, words) => {
    const out = new Set(words || []);
    (vals || []).forEach(v => {
      v = Math.abs(+v);
      out.add(money(v));
      out.add('$' + v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
    });
    return [...out].filter(Boolean);
  };
  // Scan the visible view for the smallest block that mentions a needle AND matches the keyword pattern
  // (in itself or within 3 ancestors). Report whether that block links somewhere and offers an action.
  window.__lkScan = (needles, kwSrc, actSrc) => {
    const kw = kwSrc ? new RegExp(kwSrc, 'i') : null;
    const ACT = new RegExp(actSrc || 'bill|invoice|draft|credit|match|confirm|approve|assign|remind|chase|dispute|hold|apply|code|review|resolve|reject', 'i');
    const roots = [...document.querySelectorAll('section.view.on')];
    if (!roots.length) roots.push(document.body);
    const CLICK = 'a,button,[role=button],[data-go],[onclick],.click,[data-open],[data-txn],[data-tx],[data-bill],[data-rtb],[data-act],[data-rem],[data-id]';
    const hits = [];
    // visible words only: drop <select>/<option> lists (a category dropdown in a row is not a flag)
    const words = (el) => { if (!el.querySelector('select,datalist')) return el.textContent || '';
      const c = el.cloneNode(true); c.querySelectorAll('select,datalist,script,style').forEach(x => x.remove()); return c.textContent || ''; };
    roots.forEach(root => root.querySelectorAll('li,tr,.card,.note,.row,div,p,span,td').forEach(el => {
      const t0 = el.textContent || '';
      if (t0.length > 900 || !needles.some(n => t0.includes(n))) return;
      const t = words(el);
      if (!needles.some(n => t.includes(n))) return;
      let ok = !kw || kw.test(t), ctx = el;
      for (let i = 0; !ok && i < 3 && ctx.parentElement; i++) {
        ctx = ctx.parentElement;
        if ((ctx.textContent || '').length < 1500 && kw.test(words(ctx))) ok = true;
      }
      if (ok) hits.push(el);
    }));
    if (!hits.length) return { hit: false };
    hits.sort((a, b) => a.textContent.length - b.textContent.length);
    const el = hits[0];
    let box = el.closest('tr,li,.card,.note,[data-mid]') || el;
    for (let i = 0, x = box; i < 4 && x; i++, x = x.parentElement) {   // widen to the row/card that holds its buttons
      if ((x.textContent || '').length > 1500) break;
      if (x.querySelector(CLICK) || x.matches(CLICK)) { box = x; break; }
    }
    const cl = [...box.querySelectorAll(CLICK)];
    if (el.matches(CLICK)) cl.push(el);
    if (box.closest(CLICK)) cl.push(box.closest(CLICK));
    if (box.matches && box.matches('tr') && (box.classList.contains('click') || box.onclick)) cl.push(box);
    return {
      hit: true, text: words(box).replace(/\s+/g, ' ').trim().slice(0, 220), link: cl.length > 0,
      action: cl.some(c => ACT.test(c.textContent || '') || ACT.test(c.title || '')),
    };
  };
  // Ask: the same entry point the Ask box calls. Flatten the answer to text (bounded walk; DB objects are cyclic).
  window.__lkAsk = (q) => {
    let r;
    try { r = paAsk(q); } catch (e) { return { headline: 'ERROR ' + e, text: '', go: false, offers: 0 }; }
    if (!r || typeof r !== 'object') return { headline: String(r || ''), text: String(r || ''), go: false, offers: 0 };
    const seen = new Set(), bits = [];
    const walk = (v, d) => {
      if (v == null || d > 4 || bits.length > 4000) return;
      if (typeof v === 'string') { bits.push(v.replace(/<[^>]+>/g, ' ')); return; }
      if (typeof v === 'number') { bits.push(String(v)); return; }
      if (typeof v !== 'object' || seen.has(v)) return;
      seen.add(v);
      if (Array.isArray(v)) { v.slice(0, 60).forEach(x => walk(x, d + 1)); return; }
      Object.entries(v).forEach(([k, x]) => { if (!['p', 'c', 'S', 'J', 'ref', 'doc'].includes(k)) walk(x, d + 1); });
    };
    walk(r, 0);
    return { headline: r.headline || '', text: bits.join(' \u00b7 ').replace(/\s+/g, ' ').slice(0, 6000),
             go: !!(r.go || (r.rows && r.rows.length)), offers: (r.offers || []).length };
  };
  window.__lkText = (o) => { try { return JSON.stringify(o, (k, v) => (['p','c','J','d','doc','S'].includes(k) && v && typeof v === 'object') ? (v.id || '') : v); } catch (e) { return String(o); } };
  return true;
}
"""


async def boot(p, uid='u_owner'):
    b, pg, errs = await open_app(p)
    await sign_in(pg, uid)
    await pg.evaluate(PAGE_HELPERS)
    return b, pg, errs


async def as_user(pg, uid, view, setup_js=None):
    await sign_in(pg, uid)
    if setup_js:
        await pg.evaluate(setup_js)
    await go(pg, view)
    await pg.wait_for_timeout(150)


async def scan(pg, uid, view, needles, kw, act=None, setup_js=None):
    """Sign in as `uid`, open `view`, scan it. Returns {hit, text, link, action}."""
    await as_user(pg, uid, view, setup_js)
    return await pg.evaluate('([n,k,a]) => __lkScan(n,k,a)', [needles, kw, act])


async def ask(pg, q, uid='u_owner'):
    await sign_in(pg, uid)
    return await pg.evaluate('q => __lkAsk(q)', q)


async def import_statement(pg, acct, name, text):
    """The real Import Statement dialog: open it, hand the file to its file input, press Import."""
    await pg.evaluate("a => { view = 'bank'; render(); bfImportDialog(a); }", acct)
    await pg.wait_for_selector('#bfi-file', state='attached', timeout=10000)
    await pg.set_input_files('#bfi-file', files=[{'name': name, 'mimeType': 'text/plain', 'buffer': text.encode()}])
    await pg.wait_for_function("() => { const b = document.querySelector('#mbm-ok'); return b && !b.disabled && /Import \\d/.test(b.textContent); }", timeout=10000)
    await pg.click('#mbm-ok')
    await pg.wait_for_timeout(250)
    return await pg.evaluate("n => (DB.bankImports || []).filter(i => i.fileName === n).map(i => ({added: i.added, dup: i.dup, ruled: i.ruled}))", name)


async def find_txn(pg, desc, amt):
    return await pg.evaluate("([d,a]) => { const t = DB.txns.find(t => t.desc === d && Math.abs(t.amt - a) < 0.005); return t ? t.id : null; }", [desc, amt])


async def code_txn(pg, tid, cat, proj, code, memo, vendor=''):
    """The transaction drawer the Banking list opens: choose category, job and cost code, write the memo, Save."""
    await pg.evaluate("id => { if (document.querySelector('#drawer.on') && typeof closeEditor === 'function') closeEditor(); txnDialog(id); }", tid)
    await pg.wait_for_selector('#e-cat', state='attached')
    await pg.select_option('#e-cat', cat)
    await pg.select_option('#e-proj', proj)
    await pg.dispatch_event('#e-proj', 'change')
    await pg.select_option('#e-code', code)
    await pg.fill('#e-memo', memo)
    if vendor and not (await pg.input_value('#e-vendor')).strip():
        # NB: after a New Bill drawer has been open, its required-Vendor gate (vfGate on the shared #d-save) still
        # blocks this drawer's Save until Vendor is filled; a person is shown "required" on Vendor and fills it.
        await pg.fill('#e-vendor', vendor)
    await save_drawer(pg)
    await pg.wait_for_timeout(150)
    return await pg.evaluate("id => { const t = DB.txns.find(x => x.id === id); return t && {cat: t.cat, projectId: t.projectId, code: t.code, status: t.status}; }", tid)


async def save_drawer(pg):
    """Press the drawer's Save as a person would (a real pointer click on #d-save)."""
    await pg.click('#d-save', timeout=5000)
    await pg.wait_for_timeout(150)


def csv(rows):
    return 'Date,Description,Amount,Reference\n' + '\n'.join(f'{d},{desc},{amt:.2f},{ref}' for d, desc, amt, ref in rows) + '\n'


def ofx(mask, rows, card=True):
    """rows: (yyyymmdd, amount, fitid, name, memo). A minimal OFX 1 SGML statement, the shape banks export."""
    tr = ''.join(f"<STMTTRN><TRNTYPE>{'DEBIT' if a < 0 else 'CREDIT'}<DTPOSTED>{d}120000<TRNAMT>{a:.2f}<FITID>{f}<NAME>{n}<MEMO>{m}</STMTTRN>\n"
                 for d, a, f, n, m in rows)
    acct = f"<CCACCTFROM><ACCTID>XXXXXXXXXXX{mask}</CCACCTFROM>" if card else f"<BANKACCTFROM><BANKID>021000021<ACCTID>XXXXXX{mask}<ACCTTYPE>CHECKING</BANKACCTFROM>"
    rs = 'CCSTMTRS' if card else 'STMTRS'
    wrap = 'CREDITCARDMSGSRSV1><CCSTMTTRNRS' if card else 'BANKMSGSRSV1><STMTTRNRS'
    o1, o2 = wrap.split('><')
    return ("OFXHEADER:100\nDATA:OFXSGML\nVERSION:102\n\n<OFX><SIGNONMSGSRSV1><SONRS><STATUS><CODE>0</STATUS><FI><ORG>DEMO</FI></SONRS></SIGNONMSGSRSV1>"
            f"<{o1}><{o2}><TRNUID>1<{rs}><CURDEF>USD{acct}<BANKTRANLIST><DTSTART>{rows[0][0]}<DTEND>{rows[-1][0]}\n{tr}</BANKTRANLIST></{rs}></{o2}></{o1}></OFX>\n")


# ---------------------------------------------------------------- result bookkeeping
class Scenario:
    def __init__(self, num, key, title):
        self.num, self.key, self.title = num, key, title
        self.checks, self.facts, self.setup_ok, self.errors = [], [], True, []

    def check(self, ok, what, detail=''):
        self.checks.append({'ok': bool(ok), 'what': what, 'detail': detail})

    def fact(self, s):
        self.facts.append(s)

    def verdict(self):
        if not self.setup_ok:
            return 'MISSED'
        n = sum(c['ok'] for c in self.checks)
        return 'CAUGHT' if n == len(self.checks) else ('MISSED' if n == 0 else 'PARTIAL')

    def report(self):
        v = self.verdict()
        print(f"\n[{self.num}] {self.title}: {v}")
        for c in self.checks:
            print(f"   {'ok  ' if c['ok'] else 'MISS'} {c['what']}" + (f"  — {c['detail']}" if c['detail'] else ''))
        for f in self.facts:
            print(f"   info {f}")
        for e in self.errors:
            print(f"   ERR  {e}")
        return v

    def as_dict(self):
        return {'n': self.num, 'key': self.key, 'title': self.title, 'verdict': self.verdict(),
                'missing': [c['what'] for c in self.checks if not c['ok']], 'checks': self.checks,
                'facts': self.facts, 'errors': self.errors}


def surf(S, res, where, need_action=True):
    """Record one screen check: it must mention the leak, link to the record, and (usually) propose an action."""
    if not res.get('hit'):
        S.check(False, f'{where}: shows it', 'nothing on the screen names it')
        return
    S.check(True, f'{where}: shows it', res['text'][:120])
    S.check(res['link'], f'{where}: links to the record')
    if need_action:
        S.check(res['action'], f'{where}: proposes an action')


def ask_check(S, a, q, needles, kw=None, label=None):
    txt = (a['headline'] + ' ' + a['text'])
    import re
    hit = any(n.lower() in txt.lower() for n in needles) and (not kw or re.search(kw, txt, re.I))
    S.check(hit, f'Ask "{q}"' if not label else label, a['headline'][:140])


# ---------------------------------------------------------------- 1. unbilled reimbursable
UNBILLED_KW = r'unbill|not (yet )?billed|not invoiced|bill (it )?back|rebill|re-bill|reimburs|billable|on no invoice|bill the client|bill it'

async def s1_reimbursable(p, S):
    b, pg, errs = await boot(p)
    try:
        hd = ('2026-08-11', 'THE HOME DEPOT #6177 BROOKLYN NY', -487.36, 'HD7720-260811-01')
        out = await import_statement(pg, 'ac3', 'HomeDepot_ProXtra_7720_Aug2026.csv', csv([hd]))
        rh = ('20260814', -1268.40, 'AMX1009260814077', 'RESTORATION HARDWARE 0412', 'NEW YORK NY')
        out2 = await import_statement(pg, 'ac2', 'Amex_1009_Aug2026.ofx', ofx('1009', [rh]))
        t1 = await find_txn(pg, hd[1], hd[2]); t2 = await find_txn(pg, rh[3], rh[1])
        if not (t1 and t2):
            S.setup_ok = False; S.errors.append(f'import did not land: {out} {out2}'); return
        J0 = await pg.evaluate("() => jobFin(DB.projects.find(p => p.id === 'p121')).actual")
        await code_txn(pg, t1, 'materials', JOB, '03', 'Extra blocking lumber the Kleins asked for on site — bill back to client')
        await code_txn(pg, t2, 'materials', JOB, '11', 'Client purchase for the Kleins: 3 kitchen pendants — rebill at cost plus 10%')
        J1 = await pg.evaluate("() => jobFin(DB.projects.find(p => p.id === 'p121')).actual")
        S.fact(f'both card lines land on 121 State job cost (+{J1 - J0:,.2f}); the txn has no billable/rebill flag field '
               f"(keys: {await pg.evaluate('id => Object.keys(DB.txns.find(t=>t.id===id)).join(\",\")', t2)})")
        needles = await pg.evaluate("v => __lkNeedles(v, ['HOME DEPOT', 'Home Depot', 'RESTORATION HARDWARE', 'Restoration Hardware'])", [487.36, 1268.40])
        data = await pg.evaluate("""() => {
          const R = readyToBill(), A = analystFindings(), M = reminders();
          const txt = __lkText({rtb: R.rows, held: R.held, af: A, rem: M});
          return { rtb: /HOME DEPOT|Home Depot|RESTORATION|\\$487|\\$1,268/i.test(__lkText(R)), any: /HOME DEPOT|RESTORATION|\\$487|\\$1,268/i.test(txt) };
        }""")
        S.check(data['rtb'], 'Ready to Bill (readyToBill) carries the unbilled card purchases',
                'readyToBill() is SOV/progress/design-milestone only')
        surf(S, await scan(pg, 'u_billing', 'billing', needles, UNBILLED_KW), 'Billing Queue (billing user)')
        surf(S, await scan(pg, 'u_billing', 'home', needles, UNBILLED_KW), 'Home (billing user)')
        surf(S, await scan(pg, 'u_owner', 'bank', needles, UNBILLED_KW), 'Banking (owner): line flagged unbilled')
        seen = await pg.evaluate("n => __lkScan(n, null)", needles)   # sanity: the scanner does see the line itself
        S.fact(f"Banking lists the line (no keyword): {seen.get('hit')} {seen.get('text', '')[:90]}")
        for q in ["what have we bought for clients that we haven't billed",
                  "any Home Depot purchases on 121 State we haven't billed the Kleins for"]:
            ask_check(S, await ask(pg, q), q, needles, UNBILLED_KW)
    finally:
        if errs: S.errors.append(f'page errors: {errs[:2]}')
        await b.close()


# ---------------------------------------------------------------- 2. work done, not billed
async def s2_done_not_billed(p, S):
    b, pg, errs = await boot(p)
    try:
        before = await pg.evaluate("() => { const R = readyToBill(); return {amt: R.amount, n: R.n, held: R.held.map(h => [h.p.id, h.amount])}; }")
        # the foreman measures Rough electrical at 100% (the field progress sheet calls prgSet)
        await pg.evaluate("""() => { const p = DB.projects.find(x => x.id === 'p121'); const t = p.tasks.find(t => t.id === 'relec');
                              prgSet(p, t, {pct: 100, by: 'Angel', role: 'foreman', src: 'field', note: 'Rough electrical complete, ready for inspection'}); save(); }""")
        # the client approves CO-2026-002 (owner records it: the CO's Approve button calls docAction) and the crew finishes it
        await pg.evaluate("""async () => { const c = DB.clients.find(x => x.id === 'cl121'); const d = c.changeOrders.find(x => x.number === 'CO-2026-002');
                              await docAction(c, d, 'approve');
                              const p = DB.projects.find(x => x.id === 'p121'); prgSet(p, p.tasks.find(t => t.id === 'sand'), {pct: 100, by: 'Angel', role: 'foreman', src: 'field', note: 'Treads sanded and stained (CO-2026-002)'}); save(); }""")
        st = await pg.evaluate("""() => { const c = DB.clients.find(x => x.id === 'cl121'); const co = c.changeOrders.find(x => x.number === 'CO-2026-002');
               const rows = pgRows('p121'); const el = rows.find(r => /Electrical/.test(r.sv.desc)); const cr = rows.find(r => r.sv.source === 'CO-2026-002');
               const R = readyToBill();
               return { co: co.status, sov: !!c.sov.find(v => v.source === 'CO-2026-002'),
                        elec: el && {billed: el.ev.billedPct, measured: el.pr.pct, period: el.pr.period, amt: Math.round(el.ev.scheduled * (el.pr.period||0) / 100)},
                        coRow: cr && {billed: cr.ev.billedPct, measured: cr.pr.pct, basis: cr.pr.basis},
                        rtb: {amt: R.amount, n: R.n, rows: R.rows.map(r => r.p && r.p.id + ':' + r.kind + ':' + r.amount), held: R.held.map(h => [h.p.id, h.amount, h.why])} }; }""")
        S.fact(f"before: Ready to Bill {before}; after: {st['rtb']}")
        S.fact(f"electrical SOV line: {st['elec']}; CO-2026-002 status {st['co']}, on SOV {st['sov']}, its line {st['coRow']}")
        el_amt = (st['elec'] or {}).get('amt', 0)
        S.check(st['elec'] and (st['elec']['measured'] or 0) >= 99, 'measured 100% reaches the pay-app line (pgRows)')
        S.check(st['coRow'] and (st['coRow']['measured'] or 0) >= 99, 'approved CO line knows its work is done', f"{st['coRow']}")
        rtb121 = sum(float(r.split(':')[2]) for r in st['rtb']['rows'] if r and r.startswith('p121:'))
        # the hold design (lane 1, round one, 2026-10-26; TRIAGE class 2's accept): 121 State is billed ahead on the whole, so
        # the work done and the approved CO wait in the Billing Queue as a held row with the reason, never dropped
        held121 = sum(float(h[1]) for h in st['rtb']['held'] if h[0] == 'p121' and 'ahead of the work' in str(h[2]))
        S.check(rtb121 + held121 >= el_amt + 1850 - 1, 'the Billing Queue carries the measured electrical gap + the approved CO (ready, or held because the job is billed ahead)',
                f'121 State ready ${rtb121:,.0f} + held ${held121:,.0f} (expected >= ${el_amt + 1850:,.0f}); held: {st["rtb"]["held"]}')
        needles = await pg.evaluate("v => __lkNeedles(v, ['CO-2026-002', 'Sand & stain', 'Electrical', '121 State'])", [1850, el_amt])
        kw = r'ready to bill|not (yet )?billed|unbilled|bill it|draft the|application'
        surf(S, await scan(pg, 'u_billing', 'billing', await pg.evaluate("v => __lkNeedles(v, ['CO-2026-002','Sand & stain'])", [1850]), kw), 'Billing Queue: approved CO-2026-002 done and unbilled')
        surf(S, await scan(pg, 'u_alan', 'dash', needles, kw, setup_js="() => setCurrent('p121')"), 'Job page (PM, 121 State)')
        for q in ["what work is done but not billed on 121 State", "has CO-2026-002 been billed"]:
            ask_check(S, await ask(pg, q), q, await pg.evaluate("v => __lkNeedles(v, ['CO-2026-002','Electrical','electrical'])", [1850, el_amt]),
                      r'not (yet )?billed|unbilled|ready|bill')
    finally:
        if errs: S.errors.append(f'page errors: {errs[:2]}')
        await b.close()


# ---------------------------------------------------------------- 3. overspend
OVER_KW = r'over (the |its )?budget|over budget|over the PO|more than the PO|vs PO|exceed|overrun|over-committed|above (the )?budget'

async def s3_overspend(p, S):
    b, pg, errs = await boot(p)
    try:
        # (a) a vendor bill through the New Bill drawer: Carlos Millwork's second draw on PO-2026-048 (PO $76,000, $38,000 billed;
        #     code 10 budget $75,000). $46,000 takes the PO to $84,000 (+10.5%) and the cost code to $84,000 (112% of budget).
        await pg.evaluate("() => { setCurrent('p121'); view = 'ap'; render(); openBill(); }")
        await pg.wait_for_selector('#e-vendor', state='attached')
        await pg.fill('#e-vendor', 'Carlos Millwork')
        await pg.fill('#e-number', 'CM-0107')
        await pg.fill('#e-date', '2026-09-02')
        await pg.select_option('#e-proj', JOB)
        await pg.select_option('#e-po', 'po4')
        await pg.select_option('#e-cat', 'subs')
        await pg.select_option('#e-code', '10')
        await pg.evaluate("""() => { const tr = document.querySelector('tr[data-bl]'); tr.querySelector('[data-f="desc"]').value = 'Parlor kitchen + laundry cabinets, second draw';
                              tr.querySelector('[data-f="amount"]').value = '46000'; }""")
        await save_drawer(pg)
        await pg.wait_for_timeout(200)
        bid = await pg.evaluate("() => (DB.bills.find(b => b.number === 'CM-0107') || {}).id || null")
        if not bid:
            S.setup_ok = False; S.errors.append('the bill drawer did not save CM-0107'); return
        await pg.evaluate("id => { openBill(id); const s = document.querySelector('[data-bact=\"submit\"]'); s && s.click(); }", bid)
        await pg.wait_for_timeout(150)
        await pg.evaluate("() => { if (typeof closeEditor === 'function' && document.querySelector('#drawer.on')) closeEditor(); }")
        flags = await pg.evaluate("id => { const b = DB.bills.find(x => x.id === id); return {status: b.status, flags: billFlags(b)}; }", bid)
        S.fact(f"bill CM-0107 {flags['status']}; billFlags at landing: {flags['flags']}")
        import re
        S.check(any(re.search(r'vs PO|over the PO|PO-2026-048', f) for f in flags['flags']), 'bill flagged over its PO the moment it lands')
        S.check(any(re.search(r'budget|estimate|cost code|Millwork', f, re.I) for f in flags['flags']), 'bill flagged over the cost-code budget / estimate line the moment it lands')
        # (b) a card line: scaffold rental on the Amex, coded to 121 State general conditions (code 01 budget $5,200)
        sc = ('20260901', -6350.00, 'AMX1009260901112', 'ACME SCAFFOLD AND HOIST RENTAL', 'BROOKLYN NY')
        await import_statement(pg, 'ac2', 'Amex_1009_Sep2026.ofx', ofx('1009', [sc]))
        tid = await find_txn(pg, sc[3], sc[1])
        if tid:
            S.fact(f"card line coded: {await code_txn(pg, tid, 'equipment', JOB, '01', 'Rear facade scaffold, 4 weeks', 'Acme Scaffold')}")
            st = await pg.evaluate("id => { const t = DB.txns.find(x => x.id === id); return txnState(t); }", tid)
            S.fact(f'card line txnState after coding: {st}')
            S.check(bool(st.get('msg')) and re.search(OVER_KW, st.get('msg', ''), re.I), 'card line flagged over the cost-code budget when it is coded', str(st))
        else:
            S.check(False, 'card line imported', 'not found after import')
        byc = await pg.evaluate("() => jobFin(DB.projects.find(p => p.id === 'p121')).byCode.filter(r => ['01','10'].includes(r.code)).map(r => `${r.code} budget ${r.budget} actual ${r.actual}`)")
        S.fact(f'job cost by code now: {byc}')
        needles = await pg.evaluate("v => __lkNeedles(v, ['CM-0107', 'Carlos Millwork', 'Millwork', 'General conditions', 'PO-2026-048'])", [46000, 84000])
        surf(S, await scan(pg, 'u_owner', 'mapprove', needles, OVER_KW), 'Approvals (owner): the bill shows the overrun')
        surf(S, await scan(pg, 'u_owner', 'home', needles, OVER_KW), 'Home (owner)')
        surf(S, await scan(pg, 'u_alan', 'home', needles, OVER_KW), 'Home (PM)')
        surf(S, await scan(pg, 'u_alan', 'dash', needles, OVER_KW, setup_js="() => setCurrent('p121')"), 'Job page (PM, 121 State)')
        af = await pg.evaluate("() => analystFindings().filter(f => /over budget|more than the PO/i.test(f.title)).map(f => f.title)")
        S.fact(f'analyst findings on overspend (Reports > Analyst, end-of-period style list): {af}')
        ask_check(S, await ask(pg, 'which cost codes are over budget on 121 State'), 'which cost codes are over budget on 121 State',
                  ['Millwork', 'millwork', 'General conditions', 'general conditions'], OVER_KW)
        ask_check(S, await ask(pg, 'is any PO overbilled'), 'is any PO overbilled', ['PO-2026-048', 'Carlos'], None)
    finally:
        if errs: S.errors.append(f'page errors: {errs[:2]}')
        await b.close()


# ---------------------------------------------------------------- 4. return / refund
async def s4_refund(p, S):
    b, pg, errs = await boot(p)
    try:
        buy = ('2026-08-18', 'THE HOME DEPOT #6177 BROOKLYN NY', -612.48, 'HD7720-260818-02')
        await import_statement(pg, 'ac3', 'HomeDepot_ProXtra_7720_wk34.csv', csv([buy]))
        t0 = await find_txn(pg, buy[1], buy[2])
        if not t0:
            S.setup_ok = False; S.errors.append('purchase did not import'); return
        await code_txn(pg, t0, 'materials', JOB, '11', 'Four interior door slabs, 3rd floor')
        J0 = await pg.evaluate("() => jobFin(DB.projects.find(p => p.id === 'p121')).actual")
        ret = ('2026-08-27', 'THE HOME DEPOT #6177 RETURN BROOKLYN NY', 612.48, 'HD7720-260827-03')
        await import_statement(pg, 'ac3', 'HomeDepot_ProXtra_7720_wk35.csv', csv([ret]))
        t1 = await find_txn(pg, ret[1], ret[2])
        # a vendor credit on checking against a bill that was paid and billed through to the client (Nemo Tile NT-88412, PO-2026-041, tile line)
        nemo = ('20260902', 850.00, '202609020031', 'NEMO TILE SUPPLY CREDIT RTN 88412', 'CREDIT MEMO')
        await import_statement(pg, 'ac1', 'Chase_Checking_4471_Sep2026.qfx', ofx('4471', [nemo], card=False))
        t2 = await find_txn(pg, nemo[3], nemo[1])
        if not (t1 and t2):
            S.setup_ok = False; S.errors.append(f'credits did not import: {t1} {t2}'); return
        st = await pg.evaluate("""([a,b,o]) => { const T = id => DB.txns.find(x => x.id === id);
            const f = t => ({cat: t.cat, projectId: t.projectId, code: t.code, status: t.status, state: txnState(t), sug: (typeof pay3Suggest === 'function' ? pay3Suggest(t) : null),
                             links: Object.entries(t).filter(([k,v]) => typeof v === 'string' && (v === o || /^b\\d|^po\\d/.test(v)) && !['id','acct','projectId','code','cat'].includes(k)).map(([k,v]) => k+'='+v),
                             retId: t.retId || '', billId: t.billId || '', poId: t.poId || ''});
            return {hd: f(T(a)), nemo: f(T(b))}; }""", [t1, t2, t0])
        S.fact(f"HD refund after import: {st['hd']}")
        S.fact(f"Nemo credit after import: {st['nemo']}")
        hd_linked = any(t0 in l for l in st['hd']['links'])
        S.check(hd_linked, 'refund matched to the original card purchase (a link from the credit to the purchase)',
                f"refund has {st['hd']['links'] or 'no link'}; state {st['hd']['state']}")
        S.check(bool(st['nemo']['billId'] or st['nemo']['poId'] or any(('b1' in l or 'po1' in l) for l in st['nemo']['links'])),
                'vendor credit matched to the bill / PO it relieves (NT-88412 / PO-2026-041)', str(st['nemo']['state']))
        # The person accepts whatever the app proposes for the refund; if it proposes nothing, they code it the obvious way.
        how = await pg.evaluate("""([id]) => { const t = DB.txns.find(x => x.id === id);
             if (typeof pay3Suggest === 'function' && pay3Suggest(t)) { pay3Accept(id, true); return 'accepted the app suggestion ' + JSON.stringify({cat: t.cat, projectId: t.projectId, code: t.code}); }
             return 'no suggestion (rule set cat=' + t.cat + ', project=' + (t.projectId || 'none') + ')'; }""", [t1])
        tx = await pg.evaluate("id => { const t = DB.txns.find(x => x.id === id); return {cat: t.cat, projectId: t.projectId}; }", t1)
        if tx['projectId'] != JOB:
            await code_txn(pg, t1, 'refund', JOB, '11', 'Return of two door slabs')
            how += '; coded by hand to 121 State / refund / 11'
        J1 = await pg.evaluate("() => jobFin(DB.projects.find(p => p.id === 'p121')).actual")
        S.fact(f'refund handling: {how}; job actual {J0:,.2f} -> {J1:,.2f}')
        S.check(J1 <= J0 - 612.0, 'refund relieves 121 State job cost', f'job actual moved {J1 - J0:+,.2f} (expected -612.48)')
        # client credit: the tile line was invoiced to the Kleins (SOV, 51.67% billed); a vendor credit on it should propose a client credit
        needles = await pg.evaluate("v => __lkNeedles(v, ['NEMO', 'Nemo'])", [850])
        surf(S, await scan(pg, 'u_billing', 'billing', needles, r'credit'), 'Billing Queue: credit to the client proposed for the Nemo credit')
        surf(S, await scan(pg, 'u_controller', 'bank', await pg.evaluate("v => __lkNeedles(v, ['RETURN', 'NEMO'])", [612.48, 850]), r'vendor credit|no return|against a return|confirm it against|matched to|refund (of|for)|credit (for|against)'),
             'Banking (controller): credits shown as returns with a match to confirm')
        ask_check(S, await ask(pg, 'which refunds or vendor credits have not been matched or credited to the client'),
                  'Ask: unmatched refunds / credits', await pg.evaluate("v => __lkNeedles(v, ['NEMO','Nemo','HOME DEPOT','Home Depot'])", [612.48, 850]), r'credit|refund|return')
    finally:
        if errs: S.errors.append(f'page errors: {errs[:2]}')
        await b.close()


# ---------------------------------------------------------------- 5. no manual entries
async def s5_trace(p, S):
    b, pg, errs = await boot(p)
    try:
        # inject the thing the north star forbids: a cost typed by hand (Banking > Add Transaction), with no bank line behind it
        await pg.evaluate("() => { setCurrent('p121'); view = 'bank'; render(); txnDialog(); }")
        await pg.wait_for_selector('#e-desc', state='attached')
        await pg.fill('#e-date', '2026-09-02')
        await pg.select_option('#e-acct', 'ac1')
        await pg.fill('#e-desc', 'Cash at lumber yard (receipt lost)')
        await pg.fill('#e-amt', '-300')
        await pg.select_option('#e-cat', 'materials')
        await pg.select_option('#e-proj', JOB)
        await pg.select_option('#e-code', '03')
        await save_drawer(pg)
        await pg.wait_for_timeout(150)
        r = await pg.evaluate("""() => {
          const p = DB.projects.find(x => x.id === 'p121'), J = jobFin(p), bills = DB.bills.filter(b => b.projectId === p.id);
          const keysByCode = [...new Set(J.byCode.flatMap(x => Object.keys(x)))];
          const srcKeys = keysByCode.filter(k => /src|source|ids|refs|txns|bills|docs/i.test(k) && Array.isArray(J.byCode[0][k]));
          const jobTx = DB.txns.filter(t => t.projectId === p.id && t.amt < 0 && isJobCat(t.cat) && t.cat !== 'labor' && !txnViaBill(t, bills));
          // The rule is "a figure with no bank or card line behind it is not truth and is shown as such", not "every
          // typed line is confirmed": this test's own hand-typed line can never be confirmed (no bank will ever list it),
          // so requiring it to be backed (or prov.confirmedBy) could never pass. A hand-typed line nobody's bank or card
          // record has confirmed must read as not truth (truthBacking "hand") with its flag on the line; the only such
          // lines allowed are this test's own and a typed duplicate the duplicate check proposes to void (the seed's
          // 8/22 dumpster). Every other bank/card cost on the job must be backed by a bank or card line.
          lkDupScan();
          const backed = (t) => typeof bfBacked === 'function' ? bfBacked(t) : !!(t.prov && (['feed','statement'].includes(t.prov.kind) || t.prov.confirmedBy));
          // and the seed's typed TINO card charge, on the job since procurement P0 linked it to PO-2026-047 as a prepayment:
          // it reads by hand (not truth) until the card statement confirms it
          const allowedTyped = (t) => /Cash at lumber yard/.test(t.desc) || t.dupState === 'proposed' || (!!t.prepay && /TINO FLOORING/.test(t.desc));
          const notTruth = (t) => truthBacking(t).kind === 'hand' && /No bank line|Charged twice/.test(txnFlagsHtml(t));
          const unbacked = jobTx.filter(t => !backed(t) && !allowedTyped(t));
          const typedShown = jobTx.filter(t => !backed(t) && allowedTyped(t)).map(t => [t.desc + ' ' + t.amt, notTruth(t)]);
          const costed = bills.filter(b => BILL_COSTED.includes(b.status) || BILL_ACCRUED.includes(b.status));
          const noDoc = costed.filter(b => !b.fileId && !(b.files || []).length && !b.attachment);
          // the attached document is a stored file (the job's Documents), not a bare id
          const docGone = costed.filter(b => b.fileId && !DB.projects.some(q => (q.files || []).some(f => f.id === b.fileId))).map(b => b.number);
          const unpaidNoTxn = costed.filter(b => !DB.txns.some(t => t.billId === b.id) && !(b.payments || []).length);
          const time = DB.time.filter(e => e.projectId === p.id && e.status !== 'rejected');
          // A payroll run holds approved hours of a pay period whose run has been built (payrollFromTime, or a run
          // typed by hand for its dates). Each such entry carries its run's id and the run lists it (r.timeIds): the
          // tie runs both ways, firm-wide. Hours of the open pay period before its run is built, and hours waiting for
          // approval, are labor at the burdened rate and must carry no run id; the real path ties them (checked below).
          const tied = (e) => (DB.payroll || []).some(r => r.id === e.payrollId && (r.timeIds || []).includes(e.id));
          const runOf = (e) => (DB.payroll || []).find(r => !['rejected', 'void'].includes(r.status) && prInRun(r, e)) || null;
          const covered = DB.time.filter(e => e.status === 'approved' && (e.payrollId || runOf(e)));
          const noRun = covered.filter(e => !tied(e));
          const open = time.filter(e => !e.payrollId && !runOf(e));
          const appr = covered.filter(e => e.projectId === p.id);
          const waiting = open.length;
          return { J: {actual: J.actual, bills: J.billsAmt, txns: J.txnAmt, labor: J.laborCost, billed: J.billed},
                   jKeys: Object.keys(J).filter(k => Array.isArray(J[k])), srcKeys, byCodeKeys: keysByCode,
                   jobTx: jobTx.length, unbacked: unbacked.map(t => `${t.desc} ${t.amt} (${t.source || ''}/${(t.prov||{}).kind || 'no prov'})`), typedShown,
                   bills: costed.length, noDoc: noDoc.map(b => b.number), docGone, billsNoBankLine: unpaidNoTxn.map(b => b.number + ':' + b.status),
                   time: time.length, appr: appr.length, waiting, noRun: noRun.length, invs: J.invs.length };
        }""")
        S.fact(f"121 State job report: actual {r['J']['actual']:,.2f} = bills {r['J']['bills']:,.2f} + bank/card {r['J']['txns']:,.2f} + labor {r['J']['labor']:,.2f}; billed {r['J']['billed']:,.2f}")
        S.fact(f"jobFin arrays: {r['jKeys']}; byCode keys: {r['byCodeKeys']}")
        S.check(bool(r['srcKeys']), 'every job-cost-by-code figure carries the ids of its source records', 'byCode rows are bare numbers')
        S.check(not r['unbacked'], 'every bank/card cost on the job is backed by a bank or card line', f"{len(r['unbacked'])} of {r['jobTx']} not backed: {r['unbacked'][:4]}")
        S.check(bool(r['typedShown']) and all(x[1] for x in r['typedShown']), 'a hand-typed cost no bank or card line confirms reads as not truth (by hand, flagged) until confirmed', str(r['typedShown']))
        S.check(not r['noDoc'] and not r['docGone'], 'every bill on the job has its source document attached', f"{len(r['noDoc'])} of {r['bills']} without a document: {r['noDoc']}; attached but not on file: {r['docGone']}")
        S.check(r['noRun'] == 0, 'labor cost traces to a payroll run (each hour a run paid carries its run id; the run lists it)', f"{r['noRun']} time entries inside a payroll run's dates with no run tied both ways")
        S.fact(f"time entries on the job: {r['time']}, {r['appr']} in a built run, {r['waiting']} in the open pay period or waiting for approval (burdened rate until the run)")
        S.check(r['invs'] > 0, 'billed traces to invoices (J.invs)')
        needles = ['Cash at lumber yard']
        surf(S, await scan(pg, 'u_controller', 'bank', needles, r'typed by hand|by hand|no bank|not backed|manual|unbacked|no statement', act=r'match|confirm|attach|review|delete|code'),
             'Banking (controller): the hand-typed line is flagged as having no bank record')
        surf(S, await scan(pg, 'u_alan', 'costs', needles + ['$300'], r'typed by hand|by hand|no bank|not backed|manual|unbacked'), 'Job costs (PM): the hand-typed cost is marked', need_action=False)
        ask_check(S, await ask(pg, 'which costs on 121 State are not backed by a bank or card transaction'),
                  'Ask: costs on 121 State not backed by a bank line', ['Cash at lumber yard', 'lumber yard', '$300'])
        # the real "run payroll" path ties the open period's approved hours on the job both ways; waiting hours stay out
        pr = await pg.evaluate("""() => { const run = payrollFromTime({quiet: true}); if (!run) return null;
              const T = DB.time.filter(e => e.projectId === 'p121' && e.date >= run.from && e.date <= run.to);
              return {run: run.id, appr: T.filter(e => e.status === 'approved').map(e => [e.id, e.payrollId === run.id && (run.timeIds || []).includes(e.id)]),
                      waiting: T.filter(e => e.status !== 'approved').map(e => [e.id, !e.payrollId])}; }""")
        S.check(bool(pr) and pr['appr'] and all(x[1] for x in pr['appr']) and all(x[1] for x in pr['waiting']),
                'Run Payroll from Time: each approved hour on the job carries the run id and the run lists it; hours waiting for approval stay out', str(pr))
    finally:
        if errs: S.errors.append(f'page errors: {errs[:2]}')
        await b.close()


# ---------------------------------------------------------------- 6. nothing slips
async def s6_slip(p, S):
    b, pg, errs = await boot(p)
    try:
        # (a) an overdue follow-up with no owner, through the New Task drawer
        await pg.evaluate("() => { setCurrent('p121'); view = 'tasks'; render(); openEditor('action'); }")
        await pg.wait_for_selector('#e-name', state='attached')
        await pg.fill('#e-name', 'Follow up with DOB examiner on the plan-exam objection response')
        await pg.evaluate("() => { const a = document.querySelector('#e-assignee'); if (a) { a.value = ''; a.dispatchEvent(new Event('change', {bubbles: true})); } }")
        S.fact('assignee options offered: ' + str(await pg.evaluate("() => [...(document.querySelector('#e-assignee') || {options: []}).options].map(o => o.value || '(none)').slice(0, 12)")))
        await pg.fill('#e-due', '2026-08-26')
        await save_drawer(pg)
        await pg.wait_for_timeout(150)
        task = await pg.evaluate("() => { const p = DB.projects.find(x => x.id === 'p121'); const a = (p.actions || []).find(a => /DOB examiner/.test(a.title)); return a ? {id: a.id, assignee: a.assignee, due: a.due, status: a.status} : null; }")
        if not task:
            S.errors.append('the task drawer did not create the follow-up')
        S.fact(f'unowned overdue task: {task}')
        tn = ['DOB examiner', 'plan-exam objection']
        kw = r'overdue|late|past due|no owner|unassigned|nobody|assign'
        surf(S, await scan(pg, 'u_alan', 'home', tn, kw, act=r'assign|remind|chase|open|done|take'), 'Home (PM): overdue unowned follow-up, with Assign')
        surf(S, await scan(pg, 'u_owner', 'home', tn, kw, act=r'assign|remind|chase|take'), 'Home (owner)')
        await as_user(pg, 'u_alan', 'tkall')
        for lab in ['Overdue', 'Everyone']:
            await pg.evaluate("l => { const b = [...document.querySelectorAll('section.view.on button')].find(x => x.textContent.trim().replace(/\\d+$/, '') === l); b && b.click(); }", lab)
            await pg.wait_for_timeout(120)
        tk = await pg.evaluate("n => __lkScan(n, null)", tn)
        S.fact(f"Tasks › Overdue › Everyone (PM) lists it: {tk.get('hit')} {tk.get('text', '')[:100]}")
        owned = await pg.evaluate("() => { const p = DB.projects.find(x => x.id === 'p121'); const a = (p.actions || []).find(a => /DOB examiner/.test(a.title)); return a ? (a.assignee || '') : ''; }")
        S.check(bool(owned), 'the agent names a person for the unowned task (auto-route or proposal)', f'assignee still "{owned}"')
        ask_check(S, await ask(pg, 'which follow-ups are overdue and have no owner'), 'Ask: overdue follow-ups with no owner', tn)
        # (b) a promise in an outbound email (Gmail sync calls cmImport)
        n = await pg.evaluate("""() => cmImport([{ msgId: 'leaktest-promise-1', threadId: 'lt-th-1', from: 'Sarah Davis <sarah.davis@smartdesign.nyc>',
              to: ['Sarah Klein <sarah.klein@example.com>'], date: '2026-09-02T16:10:00', subject: 'Re: 121 State kitchen elevations',
              text: "Hi Sarah,\\n\\nThanks for walking the parlor floor with us today. I'll send the revised drawings Friday, with the pantry moved to the left wall.\\n\\nBest,\\nSarah Davis\\nSmartDesign" }])""")
        em = await pg.evaluate("""() => { const c = DB.comms.find(x => x.msgId === 'leaktest-promise-1'); if (!c) return null;
              const tasks = DB.projects.flatMap(p => (p.actions || []).filter(a => /revised drawings/i.test(a.title + ' ' + (a.notes || ''))).map(a => ({p: p.id, assignee: a.assignee, due: a.due})));
              const watches = (DB.watches || []).filter(w => /revised drawings/i.test(JSON.stringify(w))).map(w => ({owner: w.owner, due: w.due || w.by || ''}));
              const prom = ((DB.studio || {}).promises || []).filter(x => /revised drawings/i.test(x.text)).map(x => ({owner: x.owner, due: x.due}));
              return {route: c.route && (c.route.projectId || c.route.clientId || ''), proposals: (c.proposals || []).map(p => p.kind + ': ' + (p.summary || '').slice(0, 80)), tasks, watches, prom}; }""")
        S.fact(f'email promise: imported {n}; {em}')
        named = bool(em) and (any(t['assignee'] for t in em['tasks']) or any(w.get('owner') for w in em['watches']) or any(x.get('owner') for x in em['prom'])
                              or any(re.search(r'promise|task|follow', x, re.I) for x in em['proposals']))
        S.check(named, 'email promise "I\'ll send the revised drawings Friday" becomes a reminder/proposal for Sarah Davis', f"proposals {em and em['proposals']}")
        surf(S, await scan(pg, 'u_sarah', 'home', ['revised drawings'], r'promise|friday|due|send|owe', act=r'done|draft|send|open|remind|snooze'), 'Home (designer Sarah Davis): her promise, due Friday')
        # (c) meeting notes (Gemini notes email): next step with an owner and a day
        await pg.evaluate("""() => cmImport([{ msgId: 'leaktest-notes-1', from: 'Google Meet <meetings-noreply@google.com>', to: ['alan@smartdesign.nyc'],
              date: '2026-09-02T18:00:00', subject: 'Notes: \u201c121 State site meeting\u201d Sep 2, 2026',
              text: "Notes from \u201c121 State site meeting\u201d\\n\\nSummary\\nThe team walked 121 State Street with Sarah Klein; the parlor kitchen pantry moves to the left wall.\\n\\nSuggested next steps\\n[Sarah Davis] Revised kitchen drawings: Sarah Davis will send the revised drawings to the Kleins on Friday.\\n[Chen Biron] Pantry hardware quote: Chen Biron will get the pantry hardware quote by Tuesday.\\n" }])""")
        mt = await pg.evaluate("""() => { const m = (DB.meetings || []).find(x => x.msgId === 'leaktest-notes-1'); if (!m) return null;
              return {projectId: m.projectId, proposals: (m.proposals || []).map(p => ({kind: p.kind, status: p.status, title: p.title.slice(0, 70), owner: (p.apply || {}).owner || (p.apply || {}).assignee || '', due: (p.apply || {}).due || ''}))}; }""")
        S.fact(f'meeting notes: {mt}')
        step = [x for x in (mt or {}).get('proposals', []) if re.search(r'revised|drawings', x['title'], re.I)]
        S.check(bool(step) and step[0]['owner'] and step[0]['due'] == '2026-09-04', 'meeting next step becomes a dated task proposal for Sarah Davis (Friday = 9/4)', f'{step}')
        S.fact('meeting task record: ' + str(await pg.evaluate("""() => DB.projects.flatMap(p => (p.actions || []).filter(a => /Revised kitchen drawings/i.test(a.title)).map(a => ({p: p.id, assignee: a.assignee, due: a.due, status: a.status})))
                                                               .concat((DB.notes || DB.eaNotes || []).filter ? [] : [])""")))
        surf(S, await scan(pg, 'u_sarah', 'home', ['Revised kitchen drawings', 'revised drawings'], r'due|fri|9/4|sep 4|today|tomorrow|promise', act=r'done|draft|send|open|remind|snooze|start'),
             'Home (designer Sarah Davis): the meeting task, due Friday')
        await as_user(pg, 'u_sarah', 'tkall')
        await pg.evaluate("() => { const b = [...document.querySelectorAll('section.view.on button')].find(x => /^Next 7 Days/.test(x.textContent.trim())); b && b.click(); }")
        await pg.wait_for_timeout(120)
        tk = await pg.evaluate("n => __lkScan(n, null)", ['Revised kitchen drawings', 'revised drawings'])
        S.fact(f"Tasks › Next 7 Days (Sarah Davis) lists it: {tk.get('hit')} {tk.get('text', '')[:80]}")
        ask_check(S, await ask(pg, 'what did we promise the Kleins'), 'Ask "what did we promise the Kleins"', ['revised drawings', 'Revised kitchen drawings'])
        ask_check(S, await ask(pg, 'what does Sarah Davis owe this week', 'u_owner'), 'Ask "what does Sarah Davis owe this week"', ['revised drawings', 'Revised kitchen drawings'])
    finally:
        if errs: S.errors.append(f'page errors: {errs[:2]}')
        await b.close()


import re
SCENARIOS = [
    (1, 'reimb', 'Unbilled reimbursable (card purchases coded to 121 State, on no invoice)', s1_reimbursable),
    (2, 'unbilled', 'Work done, not billed (measured % and an approved CO above billed)', s2_done_not_billed),
    (3, 'overspend', 'Overspend flagged when the bill / card line lands', s3_overspend),
    (4, 'refund', 'Return / refund matched, relieves cost, credits the client', s4_refund),
    (5, 'trace', 'No manual entries: every job figure traces to a source document', s5_trace),
    (6, 'slip', 'Nothing slips: unowned overdue follow-up, email and meeting promises', s6_slip),
]


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scenario', default='')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    want = {x.strip() for x in a.scenario.split(',') if x.strip()}
    todo = [s for s in SCENARIOS if not want or str(s[0]) in want or s[1] in want]
    results = []
    async with async_playwright() as p:
        for num, key, title, fn in todo:
            S = Scenario(num, key, title)
            try:
                await fn(p, S)
            except Exception as e:
                S.setup_ok = False
                S.errors.append(f'{type(e).__name__}: {str(e)[:300]}')
            S.report()
            results.append(S)
    flags = sum(1 for S in results if S.verdict() != 'CAUGHT')
    print(f"\n{' · '.join(f'{S.num} {S.verdict()}' for S in results)}")
    print(f'{flags} flags')
    if a.json:
        print(json.dumps({'flags': flags, 'scenarios': [S.as_dict() for S in results]}))
    sys.exit(1 if flags else 0)


if __name__ == '__main__':
    asyncio.run(main())
