"""Finance cross-check (BACKLOG §0 item 5).

For the owner and the controller, open every surface that shows a headline money figure, read the figure off
the rendered screen (innerText, after navigating by the rail and tab buttons), parse it and compare it with
the pinned value. A surface that rounds ($184K, $2.6k) is compared within its rounding.

Each disagreement prints one line:  FIGURE | surface | value seen | expected
The run ends with `N flags` and exits 1 when N > 0.

  python3 finance_xcheck.py                 all figures, owner and controller
  python3 finance_xcheck.py --figure cash   only one figure family (cash, ar, unmatched, ap, wip, backlog,
                                            net, safe, rtb, job121, ledger, stock); repeatable or comma-separated
  python3 finance_xcheck.py --figure onejob       only one job, one EAC and one margin (below)
  python3 finance_xcheck.py --figure invariants   only the ledger invariants (below)
  python3 finance_xcheck.py --figure money        only the money definitions (BACKLOG §1.35, below)
  python3 finance_xcheck.py --figure reports      only the Reports pages against their twins (below)
  python3 finance_xcheck.py --json          machine-readable result (flags, every reading, not-shown notes)
  python3 finance_xcheck.py -v              also print every reading that agreed

Ledger invariants (lane 1, 2026-10-26). These hold for every record, not for one seed figure, so they guard every
later lane: each one walks all clients and every invoice and payment, the Live Jobs demo switched on.
  INV DEPOSIT HELD  every deposit nets to $0 in deposits held (2400) once its job's applications are billed:
                    the test bills every remaining line to 100% (per payer on a two-payer job) and sums 2400
  INV BANK BACKS    collected never exceeds what the bank backs: no bank line backs more than its amount, only a
                    line the bank sent backs a payment, and the total backed is within the bank lines
  INV SENT FROZEN   no edit to a sent or paid document (title, retainage, a line) changes what was posted
  INV ONE ANSWER    one record's "is it a deposit" has one answer across the ledger (2400 vs 4xxx), the line
                    figures (sovBilled, lineFin's deposit share), the printout (cxKind) and invIsDeposit; a sent
                    document whose print and books differ is allowed only when a Controller finding names it
  INV STAMP BACKED  every approval stamp on every bill, payroll run, card spend, PO, change order and payment has an
                    audit row by the same person on the same record at or before it, as seeded and after the PM
                    recommends and the owner approves a bill, a payroll run and a PO (BACKLOG §1.36); a held bill takes
                    no stamp by any path; an unbacked stamp reads "no record of this action" on the trail; journals,
                    rule changes and client credits name the person who approved, with that person's audit row
  INV AUDIT CHAIN   the audit trail is hash-chained and keeps every row: an edited, removed or newest-removed row fails
                    auditVerify, naming the row; 5,100 more rows drop none

The money definitions (the Accounting lane, 11-03; BACKLOG §1.35). Each figure is recomputed from the records by its
definition and compared with what prints it (--figure money):
  INV SAFE TO SPEND       the set-aside is cash received with a bank line less earned, job by job, never below $0, and
                          each forecast week carries it; Safe to Spend is the lower of ours today and that low; sending
                          an unpaid invoice moves it by $0; a payment moves it by the cash less what it sets aside
  INV ONE JOB COST        jobCostPosted's posted cost is the P&L by project row; posted plus not yet posted is the job's own
                          figure; its parts add up; jobs posted plus no job is the P&L's job cost
  INV ONE BILLED AHEAD    Billed Ahead of the Work is the lines above zero; every row and finding prints that, never a net
  INV ONE TO BILL         every finding that says bill names the job's or line's to-bill figure (toBill)
  INV ONE DATE            a vendor's bank-detail change reads as its record's date wherever named, never "N days ago"
  INV CLOSE POSTS THE SCHEDULE  the ledger bridge's "the close posts" is wipAtClose; after the close 2500/1200 by job
                          equal the WIP schedule at the month end as read before it

The Reports pages (the Reports lane, 11-04; docs/mockups/reports/SPEC.md), read off their screens (--figure reports):
  INV REPORTS TWIN        every Reports figure equals its Accounting or job-page twin: Safe to Spend (Cash, Today's
                          Pulse, the Statements' week), cash in the bank (Banking's Accounts card), payroll due (Bills
                          and Payroll), receivables (Billing's Collections), each job's cost to date (jobCostPosted, the
                          job's Budget), Over-Billed (WIP) and Billed Ahead of the Work (billedAhead), what the close
                          posts (Books' close row), the management net (Books' ledger bridge)
  INV REPORTS TIE         the statements tie to the ledger to the cent: what stands behind the numbers adds to the P&L's
                          cost; the Balance Sheet is glBS's and balances; the Cash Flow ends on the bank register; every
                          entry not from a document, a manual journal planted here among them, is listed and flagged
  INV REPORTS WIP         each job's earned follows from its own printed cost-to-cost numbers (cost for progress over
                          projected cost, times the contract), and the WIP Schedule's note says what it leaves out
  INV REPORTS READ        opening every Reports page and chip leaves the data byte for byte as it was

One job, one estimate at completion and one margin (lane F, 11-12, a PM review: 121 State read $393,986 on its Budget
table, 21% on its tile and $388,888 on Projects). As the PM and the owner, for every demo job, read off the screens
(--figure onejob):
  INV ONE EAC             the EAC and the margin at completion on the job's Overview tile, its Budget (the margin tile,
                          the Total row's Forecast and the rows' own sum), Projects and Ask are the job's one figure
                          (jobFin); cost on no estimate line is in it; the lines, the unlined cost and what is billed
                          back add up to the job's cost to date and committed; the PM's phone reads the same
  INV NO CONTRACT JOB     a job with no contract says "No contract yet" on Projects and shows its cost, never blanks; an
                          hour clocked to it is cost on its row; crew hours on its daily logs that no time entry
                          carries are named with their size
"""
import asyncio, sys, re, json, time, argparse
from harness import *

# Pinned values. They mirror baseline_test.py (income, net, ready to bill, AP owed) and the key-figures table in
# HANDOFF.md (app day 2026-09-03, owner). If a change moves one, update baseline_test.py, HANDOFF.md and this dict
# together and say why in the commit. The 121 State % complete (14%, physical, tpJobPct) and EAC are BACKLOG §1.2.
# truthpct (BACKLOG §1.2) moved these on purpose: the EAC now rolls up by estimate line, each line at
# max(budget, actual + committed), so 121 State's EAC is $388,887.50 (Windows +$3,800 billed over its PO budget,
# Millwork +$1,000 committed past its budget), its cost basis falls and it earns $1,532.47 less: WIP over-billed,
# backlog and 121's over-billing rise by $1,532.47; YTD income and net fall by it; safe to spend (cash after
# over-billing) falls by it. August and closed months are unchanged (a change in estimate is recognised in the
# period it is made).
# leaks (BACKLOG 1.5 #2) moved Ready to Bill: hold per line, never per job, so 121 State's measured framing and
# electrical ($12,651.25), held before because the job is billed ahead on the WIP schedule, now propose an
# application: $20,980 on 2 rows -> $33,631 on 3. And (BACKLOG 1.5 #1) the windows line's $13,968.74 of materials
# bought and delivered beyond what the Kleins were billed for it is a row to bill: $47,600 on 4 rows.
PINNED = {
    'cash':            184231,   # Chase Business Checking, ledger balance
    'ar':              92265,    # open invoices, ex retainage
    'unmatched_n':     15,       # bank lines not yet matched (16 · $75,272 until procurement P0, 2026-10-25, linked
    'unmatched_amt':   67272,    # TINO's $8,000 card charge to PO-2026-047 as a prepayment, to confirm on Today)
    'ap_bills':        0,        # vendor bills owed
    'ap_payroll_due':  16040,    # payroll 8/17-8/28, past due
    'ap_paid_unappr':  33500,    # paid from the bank before approval: NOT owed. $43,300 until 2026-10-24, when AMP-311
                                 # ($9,800, 9/2) stopped reading paid by the earlier 8/15 check 2205: it is held as
                                 # possibly already paid (ap_maybe_paid) until a person confirms it with a reason
    'ap_maybe_paid':   9800,     # possibly already paid by an earlier bank line: held, not owed, not paid before approval
    'wip_over':        156274,   # net over-billing on the WIP schedule ($156,274.27; $154,741.80 before truthpct)
    'backlog':         582941,   # contract - earned ($582,940.76; $581,408.29 before truthpct)
    'net':             -5330,    # YTD net, management view (-$5,329.88; -$3,797.41 before truthpct)
    'income':          142759,   # YTD earned revenue ($142,759.24; $144,291.71 before truthpct)
    'safe':            104999,   # safe to spend ($104,999.32: the Accounting lane, 11-03, BACKLOG §1.35 item 1, an approved
                                 # definition: the set-aside is cash received with a bank line less earned, job by job,
                                 # 121 State's $169,750 less $122,626 = $47,124, not all of Over-Billed (WIP) $156,274, which
                                 # set aside $92,265 billed and never paid; -$4,150.74 before, -$2,618.27 before truthpct)
    'rtb':             32331,    # ready to bill (lane 1, round three, 2026-10-26, the month walk's E248: a job billed ahead on the whole still bills every line behind its measure and holds only the lines ahead, so 121 State's application, $12,651 on framing and electrical, is ready again with the reason; the windows' stored materials, on a line itself ahead, stay held; $19,680 / 2 rows before)
                                 # (lane 1, round one, 2026-10-26: TRIAGE class 2's accept, nothing proposed on a job billed ahead: 121 State's application $12,651 and the windows' stored materials, now $10,170, are held with the reason; $46,301 / 4 rows before)
                                 # (before that: $47,601 until pilotfix2 removed the seed's 6.5 designer hours dated 9/4, a day not yet worked, billed as ready; $20,980 / 2 rows before leaks)
    'rtb_n':           3,
    'wip_job:121 State Street':   131058,   # $131,057.72; $129,525.25 before truthpct
    'wip_job:45 Cranberry St':    2705,
    'wip_job:140 Prospect Place': 22512,
    'pct121':          14,       # 121 State % complete, one number (tpJobPct, BACKLOG §1.2)
    'eac121':          388888,   # 121 State estimate at completion ($388,887.50; $384,087.50 before truthpct)
    'drift':           0,
}
FAMILY = lambda k: {'unmatched_n': 'unmatched', 'unmatched_amt': 'unmatched', 'ap_bills': 'ap', 'ap_payroll_due': 'ap',
                    'ap_paid_unappr': 'ap', 'ap_maybe_paid': 'ap', 'wip_over': 'wip', 'income': 'net', 'rtb_n': 'rtb', 'pct121': 'job121',
                    'eac121': 'job121', 'drift': 'ledger', 'tb': 'ledger', 'bridge': 'ledger', 'wiptie': 'wip',
                    'inv_dep': 'invariants', 'inv_bank': 'invariants', 'inv_edit': 'invariants', 'inv_one': 'invariants', 'inv_stamp': 'invariants', 'inv_chain': 'invariants',
                    'inv_safe': 'money', 'inv_jobcost': 'money', 'inv_ahead': 'money', 'inv_tobill': 'money', 'inv_bankdate': 'money', 'inv_close': 'money',
                    'inv_readonly': 'money', 'inv_closeinc': 'money', 'inv_oldword': 'money',
                    'inv_rptwin': 'reports', 'inv_rptie': 'reports', 'inv_rpwip': 'reports', 'inv_rpread': 'reports',
                    'inv_oneeac': 'onejob', 'inv_nocontract': 'onejob'}.get(
                        k, 'wip' if k.startswith('wip_job') else k)
LABEL = {'cash': 'CASH', 'ar': 'AR', 'unmatched_n': 'UNMATCHED (count)', 'unmatched_amt': 'UNMATCHED ($)',
         'ap_bills': 'AP OWED (bills)', 'ap_payroll_due': 'AP PAYROLL PAST DUE', 'ap_paid_unappr': 'AP PAID BEFORE APPROVAL', 'ap_maybe_paid': 'AP POSSIBLY ALREADY PAID',
         'wip_over': 'WIP OVER-BILLED', 'backlog': 'BACKLOG', 'net': 'NET YTD', 'income': 'INCOME YTD', 'safe': 'SAFE TO SPEND',
         'rtb': 'READY TO BILL', 'rtb_n': 'READY TO BILL (rows)', 'pct121': '121 STATE % COMPLETE', 'eac121': '121 STATE EAC',
         'drift': 'DRIFT', 'tb': 'TRIAL BALANCE', 'bridge': 'LEDGER BRIDGE', 'wiptie': 'WIP TIE 2500/1200',
         'inv_dep': 'INV DEPOSIT HELD', 'inv_bank': 'INV BANK BACKS', 'inv_edit': 'INV SENT FROZEN', 'inv_one': 'INV ONE ANSWER', 'inv_stamp': 'INV STAMP BACKED', 'inv_chain': 'INV AUDIT CHAIN',
         'inv_safe': 'INV SAFE TO SPEND', 'inv_jobcost': 'INV ONE JOB COST', 'inv_ahead': 'INV ONE BILLED AHEAD', 'inv_tobill': 'INV ONE TO BILL',
         'inv_bankdate': 'INV ONE DATE', 'inv_close': 'INV CLOSE POSTS THE SCHEDULE',
         'inv_readonly': 'INV READING NEVER WRITES', 'inv_closeinc': 'INV CLOSE KEEPS INCOME', 'inv_oldword': 'INV NO OLD FIGURE',
         'inv_rptwin': 'INV REPORTS TWIN', 'inv_rptie': 'INV REPORTS TIE', 'inv_rpwip': 'INV REPORTS WIP', 'inv_rpread': 'INV REPORTS READ',
         'inv_oneeac': 'INV ONE EAC', 'inv_nocontract': 'INV NO CONTRACT JOB'}
def label(k): return LABEL.get(k) or ('WIP OVER ' + k.split(':', 1)[1] if k.startswith('wip_job:') else k.upper())

MONEY = r'([−\-–]?\(?\$\s?[\d,]+(?:\.\d+)?[kKmM]?\)?)'
def parse_money(s):
    """'−$2,618' -> (-2618, tol). '$184K' -> (184000, 500). '$2.6k' -> (2600, 50). Returns (value, tolerance)."""
    s = s.strip()
    neg = s[:1] in '−-–' or s.startswith('(')
    m = re.search(r'\$\s?([\d,]+(?:\.(\d+))?)\s*([kKmM])?', s)
    if not m: return None, 0
    v = float(m.group(1).replace(',', ''))
    tol = 1.0
    if m.group(3):
        mult = 1000 if m.group(3) in 'kK' else 1_000_000
        dec = len(m.group(2) or '')
        tol = mult / (10 ** dec) / 2 + 1
        v *= mult
    return (-v if neg else v), tol

class Run:
    def __init__(self, figs, verbose, quiet=False):
        self.figs = figs; self.verbose = verbose and not quiet; self.quiet = quiet
        self.flags = []; self.readings = []; self.notes = []
    def want(self, key): return not self.figs or FAMILY(key) in self.figs
    def flag(self, key, surface, seen, expected):
        line = f'{label(key)} | {surface} | {seen} | {expected}'
        self.flags.append({'figure': key, 'surface': surface, 'seen': seen, 'expected': expected})
        if not self.quiet: print('FLAG', line)
    def note(self, key, surface, why):
        if self.want(key): self.notes.append({'figure': key, 'surface': surface, 'note': why})
    def money(self, key, surface, text, pattern, sign=1, required=True, expected=None, absval=False):
        """Read one money figure from text with a regex whose group 1 is the money string."""
        if not self.want(key): return None
        exp = PINNED[key] if expected is None else expected
        m = re.search(pattern, text or '', re.S)
        if not m:
            if required: self.flag(key, surface, 'not shown', fmt(exp, key))
            else: self.note(key, surface, 'not shown')
            return None
        raw = m.group(1).strip()
        v, tol = parse_money(raw)
        if v is None:
            self.flag(key, surface, f'unparsed "{raw}"', fmt(exp, key)); return None
        v *= sign
        if absval: v = abs(v)
        ok = abs(v - exp) <= max(tol, 1.0)
        self.readings.append({'figure': key, 'surface': surface, 'raw': raw, 'value': v, 'expected': exp, 'ok': ok})
        if not ok: self.flag(key, surface, raw, fmt(exp, key))
        elif self.verbose: print('  ok', label(key), '|', surface, '|', raw)
        return v
    def count(self, key, surface, text, pattern, required=True, expected=None, unit=''):
        if not self.want(key): return None
        exp = PINNED[key] if expected is None else expected
        m = re.search(pattern, text or '', re.S)
        if not m:
            if required: self.flag(key, surface, 'not shown', f'{exp}{unit}')
            else: self.note(key, surface, 'not shown')
            return None
        v = float(m.group(1).replace(',', ''))
        ok = abs(v - exp) < 0.5
        self.readings.append({'figure': key, 'surface': surface, 'raw': m.group(0)[:80], 'value': v, 'expected': exp, 'ok': ok})
        if not ok: self.flag(key, surface, f'{m.group(1)}{unit}', f'{exp}{unit}')
        elif self.verbose: print('  ok', label(key), '|', surface, '|', m.group(1) + unit)
        return v

def fmt(v, key=''):
    if key in ('unmatched_n', 'rtb_n', 'drift'): return str(v)
    if key == 'pct121': return f'{v}%'
    return ('−' if v < 0 else '') + '${:,.0f}'.format(abs(v))

# ---------------------------------------------------------------- navigation: the rail, the sub-nav, the tabs
async def text_of(pg, view):
    return await pg.evaluate("v => { const e = document.getElementById('v-' + v); return e ? e.innerText : '' }", view)

async def click_js(pg, sel):
    # Some tab rows render at 0x0 (the Reports sub-tabs), so a Playwright click would wait for visibility forever.
    # Click through the DOM, as a person's click would land on the same handler.
    ok = await pg.evaluate("s => { const e = [...document.querySelectorAll(s)].find(x => x.offsetParent) || document.querySelector(s); if (!e) return false; e.click(); return true }", sel)
    await pg.wait_for_timeout(200)
    return ok

async def nav(pg, grp, sub=None, tabs=()):
    """Open a view the way a person does: rail button, then the sub-nav button, then each tab in turn."""
    # the 11-03 menu lists each page under its group, which opens on its name (no sub-nav strip): the group, then the page
    target = sub or {'jobs': 'ovjobs'}.get(grp, grp)
    await pg.evaluate("""v => { const b = document.querySelector(`#nav-groups button[data-v="${v}"]:not([data-tab]):not([data-pid])`); if (!b) return false;
      const k = b.closest('[data-mngr]'), h = k && document.querySelector(`#nav-groups [data-mnchev="${k.dataset.mngr}"]`);
      h && h.getAttribute('aria-expanded') !== 'true' && h.click();
      document.querySelector(`#nav-groups button[data-v="${v}"]:not([data-tab]):not([data-pid])`).click(); return true; }""", target)
    await pg.wait_for_timeout(200)
    cur = await pg.evaluate('view')
    if cur != target:   # fall back to the app's own navigation when there is no button for it
        await go(pg, target)
    for t in tabs:
        if not await click_js(pg, t): return None
    return await pg.evaluate('view')

async def ask(pg, q):
    """Type the question into Ask and return the answer's rendered text (headline first)."""
    # Ask's box lives on the assistant's Chat tab (lane assistant): open Ask when it is not on screen
    # Ask is a button in the header on every screen (lane menu); it opens the assistant on Chat
    if await pg.evaluate('view') != 'pa' or not await pg.evaluate("() => !!document.getElementById('pa-in')"):
        if not await click_js(pg, '#tb-ask'): await nav(pg, 'ask', 'pa')
    n = await pg.evaluate("() => document.querySelectorAll('#v-pa .pa-m.me').length")
    await pg.fill('#pa-in', q)
    await pg.press('#pa-in', 'Enter')
    try:
        # the answer lands as a placeholder ("Reading the records") first; wait for the real one
        # (count the questions, not the answers: the empty thread carries a placeholder answer node)
        await pg.wait_for_function("""n => { const Q = document.querySelectorAll('#v-pa .pa-m.me');
            if (Q.length <= n) return false; const a = Q[Q.length - 1].nextElementSibling;
            const b = a && a.matches('.pa-m.a') && a.querySelector('.pa-b');
            return b && b.innerText.trim() && !/Reading the records/i.test(b.innerText) }""", arg=n, timeout=20000)
    except Exception:
        return ''
    await pg.wait_for_timeout(100)
    return await pg.evaluate("() => { const Q = [...document.querySelectorAll('#v-pa .pa-m.me')].pop(); const a = Q && Q.nextElementSibling; const b = a && a.querySelector('.pa-b'); return b ? b.innerText.trim() : '' }")

# ---------------------------------------------------------------- the surfaces
async def check_role(pg, R, uid):
    await sign_in(pg, uid)
    who = 'owner' if uid == 'u_owner' else 'controller'
    can = set(await pg.evaluate('ROLE_VIEWS[role()] || []'))
    S = lambda name: f'{who} · {name}'
    def gate(view, name):
        if view in can: return True
        R.notes.append({'figure': '*', 'surface': S(name), 'note': f'view "{view}" not open to {who}'})
        return False

    # Home › Brief: the Accounting card and the brief's sentences
    if gate('home', 'Home brief'):
        await nav(pg, 'home', 'home')
        # the approved Today mockup (2026-10-25): the Pulse and the full brief sit behind the quiet line at the foot
        if await pg.evaluate("() => { const q = document.querySelector('.view.on .td2-quiet'); return !!q && q.getAttribute('aria-expanded') === 'false'; }"):
            await pg.click('.view.on .td2-quiet'); await pg.wait_for_timeout(300)
        # Today Home (Owner, PM): the brief is 3 lines with the full brief one tap away, and Safe to Spend is a
        # Pulse number. Read the Pulse as its own surface, then open the full brief and read it as before.
        pulse = await pg.evaluate("() => [...document.querySelectorAll('.view.on button, .view.on a')].map(e => e.innerText).filter(x => /Safe to Spend/i.test(x)).join('\\n')")
        if pulse: R.money('safe', S('Home › Pulse "Safe to Spend"'), pulse, MONEY + r'\s*\n\s*Safe to Spend')
        full = pg.locator('.view.on').get_by_text('Read the Full Brief', exact=True)
        if await full.count(): await full.first.click(); await pg.wait_for_timeout(400)
        t = await text_of(pg, 'home')
        R.money('cash', S('Home brief › Accounting card "Cash on the Books"'), t, r'Cash on the books\s*\n\s*' + MONEY, required=not pulse)
        R.money('cash', S('Home brief › Cash sentence'), t, r'Cash: ' + MONEY + r' in the bank')
        R.money('safe', S('Home brief › Accounting card "Safe to Spend"'), t, r'Safe to spend\s*\n\s*' + MONEY, required=not pulse)
        # the sentence reads "but $X short" when Safe to Spend is negative, "$X safe to spend" when it is not
        if re.search(r'but ' + MONEY + r' short', t or ''): R.money('safe', S('Home brief › Cash sentence'), t, r'but ' + MONEY + r' short', sign=-1)
        else: R.money('safe', S('Home brief › Cash sentence'), t, r'in the bank, ' + MONEY + r' safe to spend', required=False)
        R.money('ar', S('Home brief › Accounting card "Receivables"'), t, r'Receivables\s*\n\s*' + MONEY, required=not pulse)
        R.money('ap_bills', S('Home brief › Accounting card "Payables"'), t, r'Payables\s*\n\s*' + MONEY, required=not pulse)
        R.money('ap_payroll_due', S('Home brief › Accounting card'), t, MONEY + r'[^\n]{0,20}past due', required=False)
        if who == 'owner':
            R.money('rtb', S('Home brief › handled line'), t, r'earned and not billed — ' + MONEY)
            R.count('rtb_n', S('Home brief › handled line'), t, r'earned and not billed — \$[\d,]+ across (\d+) invoice')
        else:
            R.money('rtb', S('Home brief'), t, r'earned and not billed — ' + MONEY, required=False)
        R.money('rtb', S('Home brief › short-after-payables item'), t, MONEY + r' is earned and unbilled', required=False)
        R.count('unmatched_n', S('Home brief'), t, r'(\d+) bank (?:items?|lines?) (?:not yet matched|with no)', required=False)
        R.money('wip_over', S('Home brief'), t, r'over-billed[^\n$]*' + MONEY, required=False)
        R.money('backlog', S('Home brief'), t, r'[Bb]acklog[^\n$]*' + MONEY, required=False)
        R.money('net', S('Home brief'), t, r'[Nn]et (?:profit|income)[^\n$]*' + MONEY, required=False)

    # Home › Dashboard
    if gate('dashboard', 'Dashboard'):
        await nav(pg, 'home', 'dashboard'); t = await text_of(pg, 'dashboard')
        R.money('safe', S('Dashboard › Cash Runway'), t, r'Cash Runway\s*\n\s*' + MONEY, required=False)
        R.money('wip_over', S('Dashboard › WIP Over / Under Billing'), t, r'WIP · Over / Under Billing\s*\n\s*' + MONEY, required=False)
        for j in ('121 State Street', '45 Cranberry St', '140 Prospect Place'):
            R.money('wip_job:' + j, S('Dashboard › WIP widget'), t, re.escape(j) + r'\t\$[\d,]+\t\$[\d,]+\t' + MONEY, required=False)
        R.money('ar', S('Dashboard › Receivables · DSO'), t, MONEY + r'\s*\n\s*(?:receivables open|Open Receivables)', required=False)
        R.money('backlog', S('Dashboard › Backlog & Pipeline'), t, MONEY + r'\s*\n\s*(?i:remaining contract on signed work)', required=False)
        R.count('pct121', S('Dashboard › Margin at Completion'), t, r'121 State Street · bid[^\n]*· (\d+)% complete', required=False, unit='%')

    # The 11-03 Accounting pages (docs/mockups/accounting/): the Accounting overview forwards to Banking, and each page
    # states its figures once on its front (Needs You, then where things stand); the old tiles are gone.
    # Banking: To Review is the one money-in-and-out queue; the Accounts card carries each account's balance
    if gate('bank', 'Banking'):
        await nav(pg, 'money', 'bank'); t = await text_of(pg, 'bank')
        R.money('cash', S('Banking › Accounts "Chase Business Checking"'), t, r'Chase Business Checking[^\n]*\n[^\n]*?\s*' + MONEY)
        R.count('unmatched_n', S('Banking › Needs You "lines to match"'), t, r'(\d+) lines? to match')
        R.count('unmatched_n', S('Banking › chip "To Review"'), t, r'To Review\s*(\d+)')
        R.money('unmatched_amt', S('Banking › Needs You "at stake"'), t, MONEY + r' at stake')

    # Bills and Payroll: the payroll past pay day on Needs You; the bill the bank paid before approval under With Others
    if gate('ap', 'Bills and Payroll'):
        await nav(pg, 'money', 'ap'); t = await text_of(pg, 'ap')
        R.money('ap_payroll_due', S('Bills and Payroll › Needs You "Payroll"'), t, r'Payroll [^\n]*?· ' + MONEY + r' · \d+ days? past pay day')
        R.money('ap_paid_unappr', S('Bills and Payroll › With Others'), t, r'(?i:with others)[\s\S]*?WW-2026-118[^\n]*\n(?:[^\n]*\n)?\s*' + MONEY)
        R.money('ap_bills', S('Bills and Payroll › "Approved · To Pay"'), t, r'Approved bills to pay[^\n]*' + MONEY, required=False)

    # Billing: what is ready to bill is Needs You's rows (their sum and count); what is owed is Collections' aging
    if gate('billing', 'Billing'):
        await nav(pg, 'billing', 'billing'); t = await text_of(pg, 'billing')
        tl = (t or '').lower()
        need = t[tl.find('needs you'):tl.find('collections')] if 'collections' in tl else ''
        rows = [parse_money(m)[0] for m in re.findall(MONEY + r' ready to bill', need)]
        if R.want('rtb'):
            v = round(sum(rows)); ok = abs(v - PINNED['rtb']) <= len(rows)
            R.readings.append({'figure': 'rtb', 'surface': S('Billing › Needs You (ready rows, summed)'), 'raw': str(rows), 'value': v, 'expected': PINNED['rtb'], 'ok': ok})
            if not ok: R.flag('rtb', S('Billing › Needs You (ready rows, summed)'), fmt(v), fmt(PINNED['rtb']))
            ok = len(rows) == PINNED['rtb_n']
            R.readings.append({'figure': 'rtb_n', 'surface': S('Billing › Needs You (ready rows)'), 'raw': str(len(rows)), 'value': len(rows), 'expected': PINNED['rtb_n'], 'ok': ok})
            if not ok: R.flag('rtb_n', S('Billing › Needs You (ready rows)'), str(len(rows)), str(PINNED['rtb_n']))
        aging = [parse_money(m)[0] for m in re.findall(r'(?:Current|1 to 30 Days|31 to 60 Days|Over 60 Days)\s*\n\s*' + MONEY, t)]
        if R.want('ar'):
            v = round(sum(aging)); ok = abs(v - PINNED['ar']) <= 2 and len(aging) == 4
            R.readings.append({'figure': 'ar', 'surface': S('Billing › Collections (the aging, summed)'), 'raw': str(aging), 'value': v, 'expected': PINNED['ar'], 'ok': ok})
            if not ok: R.flag('ar', S('Billing › Collections (the aging, summed)'), fmt(v), fmt(PINNED['ar']))

    # Ledger: Overview, Statements, Accounts, Close
    if gate('gl', 'Ledger'):
        await nav(pg, 'money', 'gl', ['#v-gl [data-gltab="overview"]']); t = await text_of(pg, 'gl')
        R.count('drift', S('Ledger › Overview tile "Drift"'), t, r'Drift(?: check)?\s*\n\s*(\d+)')
        R.count('unmatched_n', S('Ledger › Overview bridge'), t, r'(\d+) bank items? not yet matched')
        R.money('unmatched_amt', S('Ledger › Overview bridge'), t, r'bank items? not yet matched — ' + MONEY)
        R.money('net', S('Ledger › Overview bridge "Net income in the management view"'), t, r'Net income in the management view[^\t\n]*\t\s*' + MONEY)
        # the WIP not yet on the ledger is split by the close that posts it (BACKLOG §1.35 item 3): the next close posts
        # the schedule at its month end, the movement after it posts at the close after; together they are Over-Billed
        if R.want('wip_over'):
            parts = [abs(parse_money(m)[0]) for m in re.findall(r'(?:WIP adjustment the [^\t\n]*close posts|WIP movement since|WIP over/under-billing adjustment not yet posted)[^\t\n]*\t\s*' + MONEY, t)]
            v = round(sum(parts)); ok = bool(parts) and abs(v - PINNED['wip_over']) <= len(parts)
            R.readings.append({'figure': 'wip_over', 'surface': S('Ledger › Overview bridge (WIP rows, summed)'), 'raw': str(parts), 'value': v, 'expected': PINNED['wip_over'], 'ok': ok})
            if not ok: R.flag('wip_over', S('Ledger › Overview bridge (WIP rows, summed)'), fmt(v) if parts else 'not shown', fmt(PINNED['wip_over']))
        R.money('ap_payroll_due', S('Ledger › Overview bridge'), t, MONEY + r' of payroll await approval', required=False)
        ledger_net = None
        m = re.search(r'Net income on the ledger\t\s*' + MONEY, t)
        if m: ledger_net = parse_money(m.group(1))[0]
        # the bridge itself must foot: ledger net + each adjustment = management net
        blk = re.search(r'Net income on the ledger\t.*?\nNet income in the management view[^\t\n]*\t\s*' + MONEY, t, re.S)
        if R.want('bridge'):
            if not blk: R.flag('bridge', S('Ledger › Overview bridge'), 'not shown', 'ledger net + adjustments = management net')
            else:
                vals = [parse_money(x)[0] for x in re.findall(r'\t\s*' + MONEY + r'[ \t]*(?:\n|$)', blk.group(0))]
                foot = sum(vals[:-1]); mgmt = vals[-1]
                R.readings.append({'figure': 'bridge', 'surface': S('Ledger › Overview bridge'), 'raw': f'{len(vals) - 1} lines foot to {foot:,.2f}', 'value': foot, 'expected': mgmt, 'ok': abs(foot - mgmt) < 1})
                if abs(foot - mgmt) >= 1: R.flag('bridge', S('Ledger › Overview bridge (lines do not foot)'), f'{foot:,.2f}', f'{mgmt:,.2f}')

        await nav(pg, 'money', 'gl', ['#v-gl [data-gltab="statements"]', '#v-gl [data-glstmt="pl"]']); t = await text_of(pg, 'gl')
        if R.want('bridge') and ledger_net is not None:
            m = re.search(r'Net income\t\s*' + MONEY, t)
            v = parse_money(m.group(1))[0] if m else None
            if v is None or abs(v - ledger_net) > 1:
                R.flag('bridge', S('Ledger › Statements › P&L net vs Overview "Net income on the ledger"'), m.group(1) if m else 'not shown', fmt(ledger_net))
            R.notes.append({'figure': 'net', 'surface': S('Ledger › Statements › P&L'), 'note': f'ledger basis net {fmt(ledger_net)} (WIP unposted); the Overview bridge explains it to the management {fmt(PINNED["net"])}'})
        R.money('wip_over', S('Ledger › Statements › WIP-not-posted note'), t, r'Net over-billing on the WIP schedule is ' + MONEY)
        await nav(pg, 'money', 'gl', ['#v-gl [data-gltab="statements"]', '#v-gl [data-glstmt="bs"]']); t = await text_of(pg, 'gl')
        R.money('cash', S('Ledger › Statements › Balance Sheet (Chase)'), t, r'Chase Business Checking[^\t\n]*\t\s*' + MONEY)
        R.money('ar', S('Ledger › Statements › Balance Sheet'), t, r'Accounts receivable\t\s*' + MONEY)
        R.money('ap_bills', S('Ledger › Statements › Balance Sheet'), t, r'Accounts payable\t\s*' + MONEY, required=False)
        await nav(pg, 'money', 'gl', ['#v-gl [data-gltab="statements"]', '#v-gl [data-glstmt="tb"]']); t = await text_of(pg, 'gl')
        if R.want('tb'):
            m = re.search(r'\nTotal\t\s*' + MONEY + r'\t\s*' + MONEY, t)
            if not m: R.flag('tb', S('Ledger › Statements › Trial Balance'), 'no Total row', 'debits = credits')
            else:
                d, c = parse_money(m.group(1))[0], parse_money(m.group(2))[0]
                R.readings.append({'figure': 'tb', 'surface': S('Ledger › Trial Balance'), 'raw': f'{m.group(1)} / {m.group(2)}', 'value': d - c, 'expected': 0, 'ok': abs(d - c) < 0.01})
                if abs(d - c) >= 0.01: R.flag('tb', S('Ledger › Statements › Trial Balance'), f'Dr {m.group(1)} Cr {m.group(2)}', 'debits = credits')
                # every TB row: debit and credit columns sum to the Total row
                rows = re.findall(r'\n\d{4} [^\t\n]*\t\s*' + MONEY + r'\t\s*' + MONEY, t)
                sd = sum(parse_money(a)[0] for a, _ in rows); sc = sum(parse_money(b)[0] for _, b in rows)
                if abs(sd - d) > 0.05 or abs(sc - c) > 0.05:
                    R.flag('tb', S('Ledger › Trial Balance rows vs Total'), f'rows Dr {sd:,.2f} Cr {sc:,.2f}', f'Total Dr {d:,.2f} Cr {c:,.2f}')
        await nav(pg, 'money', 'gl', ['#v-gl [data-gltab="accounts"]']); t = await text_of(pg, 'gl')
        R.money('cash', S('Ledger › Accounts 1010'), t, r'\n1010\t[^\n]*\t\s*' + MONEY + r'\s*(?:\n|$)')
        R.money('ar', S('Ledger › Accounts 1100'), t, r'\n1100\t[^\n]*\t\s*' + MONEY + r'\s*(?:\n|$)')
        R.money('ap_bills', S('Ledger › Accounts 2000'), t, r'\n2000\t[^\n]*\t\s*' + MONEY + r'\s*(?:\n|$)')
        def bal(acct):
            m = re.search(r'\n' + acct + r'\t[^\n]*\t([^\t\n]+)\s*(?:\n|$)', t)
            if not m: return None
            v = parse_money(m.group(1))[0]
            return 0.0 if v is None else v
        gl2500, gl1200 = bal('2500'), bal('1200')
        await nav(pg, 'money', 'gl', ['#v-gl [data-gltab="periods"]']); t = await text_of(pg, 'gl')
        if R.want('wiptie'):
            closed = 'No month has been closed yet' not in t
            rows = re.findall(r'\n([^\t\n]+)\t\s*' + MONEY + r'\t\s*' + MONEY + r'\t\s*' + MONEY + r'\t\s*' + MONEY + r'\s*(?=\n)', t.split('ACCRUED WAGES')[0].split('WIP ADJUSTMENT')[-1] + '\n')
            hdr = re.search(r'WIP ADJUSTMENT ' + MONEY + r' TO POST · OVER/UNDER-BILLING ON THE MONTH-END SCHEDULE ' + MONEY + r', ON THE LEDGER ' + MONEY, t)
            on_ledger = 0.0
            for name, over, under, onl, entry in rows:
                o, u, l, e = (parse_money(x)[0] for x in (over, under, onl, entry))
                on_ledger += l
                if abs((o - u) - l - e) > 1:
                    R.flag('wiptie', S(f'Ledger › Close › WIP adjustment row {name}'), f'over {over} − under {under} − ledger {onl} ≠ entry {entry}', 'entry = schedule − ledger')
                if closed and abs((o - u) - l) > 1:
                    R.flag('wiptie', S(f'Ledger › Close › WIP Tie-Out {name}'), f'schedule {fmt(o - u)} vs 2500/1200 {fmt(l)}', 'equal after a close')
            if gl2500 is not None and abs((gl2500 - (gl1200 or 0)) - on_ledger) > 1:
                R.flag('wiptie', S('Ledger › Accounts 2500−1200 vs Close "On Ledger" column'), fmt(gl2500 - (gl1200 or 0)), fmt(on_ledger))
            if not rows: R.flag('wiptie', S('Ledger › Close › WIP adjustment table'), 'not shown', 'per-job WIP vs ledger')
            if not closed:
                R.notes.append({'figure': 'wip', 'surface': S('Ledger › Close'), 'note': 'no month closed: 2500/1200 hold ' + fmt(on_ledger) + ' per job; month-end schedule ' + (', '.join(f'{n.strip()} {o}' for n, o, *_ in rows)) + (f'; header to post {hdr.group(1)}' if hdr else '') + '; the per-job tie is only enforceable after a close (BACKLOG §1.1)'})
            R.readings.append({'figure': 'wiptie', 'surface': S('Ledger › Close'), 'raw': f'{len(rows)} rows, on ledger {on_ledger}', 'value': on_ledger, 'expected': None, 'ok': True})

    # Reports
    if gate('reports', 'Reports'):
        # P&L Detail (Financials)
        await nav(pg, 'reports', None, ['#v-reports [data-reptab="company"]', '#v-reports [data-repp="ty"]']); t = await text_of(pg, 'reports')
        s = 'Reports › P&L Detail (YTD)'
        R.money('income', S(s + ' headline'), t, MONEY + r'\s*\n\s*Revenue \(earned\)')
        R.money('net', S(s + ' headline'), t, MONEY + r'\s*\n\s*Net Profit')
        R.money('net', S(s + ' vs Budget table'), t, r'\nNet Profit\t\s*' + MONEY)
        R.money('cash', S(s + ' "Cash in bank"'), t, MONEY + r'\s*\n\s*Cash in bank')
        R.money('ar', S(s + ' "Receivables"'), t, MONEY + r'\s*\n\s*Receivables')
        R.money('ap_bills', S(s + ' "Payables"'), t, MONEY + r'\s*\n\s*Payables')
        R.money('ap_payroll_due', S(s + ' "Payables"'), t, r'Payables · ' + MONEY + r' past due')
        R.money('ap_paid_unappr', S(s + ' "Payables"'), t, r'Payables ·[^\n]*?' + MONEY + r' paid before approval')
        R.money('backlog', S(s + ' "Backlog"'), t, MONEY + r'\s*\n\s*Backlog')
        for j in ('121 State Street', '45 Cranberry St', '140 Prospect Place'):
            R.money('wip_job:' + j, S(s + ' › Projects table'), t, r'\n' + re.escape(j) + r'[^\n]*over-billed ' + MONEY)
        if R.want('wip_over'):
            vs = [parse_money(x)[0] for x in re.findall(r'over-billed ' + MONEY, t)]
            if vs and abs(sum(vs) - PINNED['wip_over']) > 1 + len(vs): R.flag('wip_over', S(s + ' › Projects table (sum)'), fmt(sum(vs)), fmt(PINNED['wip_over']))

        # Statements (management view)
        await nav(pg, 'reports', None, ['#v-reports [data-reptab="company"]', '#v-reports [data-reptab="financials"]']); t = await text_of(pg, 'reports')
        s = 'Reports › Statements'
        R.money('income', S(s + ' › Income Statement'), t, r'Revenue \(earned\)\t\s*' + MONEY)
        R.money('net', S(s + ' › Income Statement'), t, r'\nNet profit\t\s*' + MONEY)
        R.money('cash', S(s + ' › Balance Sheet'), t, r'Chase Business Checking[^\t\n]*\t\s*' + MONEY)
        R.money('ar', S(s + ' › Balance Sheet'), t, r'Accounts receivable\t\s*' + MONEY)
        R.money('ar', S(s + ' › Ties "Receivables"'), t, r'\nReceivables\t\s*' + MONEY)
        R.money('wip_over', S(s + ' › Ties "WIP adjustment"'), t, r'WIP adjustment ' + MONEY)
        R.money('wip_over', S(s + ' › WIP-not-posted note'), t, r'Net over-billing on the WIP schedule is ' + MONEY)
        R.count('unmatched_n', S(s + ' › Income Statement note'), t, r'(\d+) in all are not yet matched')
        ent = t.split('ENTITIES SIDE BY SIDE', 1)[1] if 'ENTITIES SIDE BY SIDE' in t else ''
        R.money('net', S(s + ' › Entities side by side (Consolidated)'), ent, r'\nNet profit\t[^\n]*\t\s*' + MONEY + r'[ \t]*\n')

        # Monthly Pack (current month; carries YTD)
        await nav(pg, 'reports', None, ['#v-reports [data-reptab="company"]', '#v-reports [data-reptab="pack"]']); t = await text_of(pg, 'reports')
        s = 'Reports › Monthly Pack'
        R.money('net', S(s + ' › Executive Summary'), t, r'net profit · YTD ' + MONEY)
        R.money('income', S(s + ' › P&L vs Budget YTD'), t, r'\nRevenue\t(?:[^\t]*\t){4}\s*' + MONEY)
        R.money('net', S(s + ' › P&L vs Budget YTD'), t, r'\nNet Profit\t(?:[^\t]*\t){4}\s*' + MONEY)
        R.money('cash', S(s + ' › Executive Summary'), t, MONEY + r'\s*\n\s*cash · AR')
        R.money('ar', S(s + ' › Executive Summary'), t, r'cash · AR ' + MONEY)
        R.money('ap_bills', S(s + ' › Executive Summary'), t, r'\(bills ' + MONEY)
        R.money('ap_payroll_due', S(s + ' › Executive Summary'), t, r'payroll ' + MONEY + r'\)')
        R.money('ar', S(s + ' › Receivables row'), t, r'\nReceivables[^\t\n]*\t(?:[^\t]*\t){4}\s*' + MONEY)
        R.money('ap_paid_unappr', S(s + ' › Payables row'), t, r'Payables — bills and payroll \(' + MONEY + r' paid before approval')
        R.money('backlog', S(s + ' › Backlog'), t, MONEY + r'\s*\n\s*backlog \(contract')
        for j in ('121 State Street', '45 Cranberry St', '140 Prospect Place'):
            R.money('wip_job:' + j, S(s + ' › WIP & Profit Fade'), t, r'\n' + re.escape(j) + r'[^\t\n]*\t(?:[^\t]*\t){5}\s*' + MONEY)
        R.count('pct121', S(s + ' › WIP & Profit Fade "% Complete"'), t, r'\n121 State Street\t[^\t]*\t(\d+)%', unit='%')
        R.money('wip_over', S(s), t, r'(?:over-billed|billings in excess)[^\n$]*' + MONEY, required=False)
        R.money('safe', S(s), t, r'[Ss]afe to spend[^\n$]*' + MONEY, required=False)
        R.count('unmatched_n', S(s), t, r'(\d+) (?:bank items|bank lines)[^\n]* not yet matched(?! or coded)', required=False)

        # Projects › All Projects (Portfolio) and WIP Schedule
        await nav(pg, 'reports', None, ['#v-reports [data-reptab="portfolio"]', '#v-reports [data-reptab="portfolio"]']); t = await text_of(pg, 'reports')
        s = 'Reports › Projects › All Projects'
        R.money('ar', S(s + ' "Outstanding"'), t, MONEY + r'\s*\n\s*Outstanding')
        R.money('eac121', S(s + ' "Proj. Cost"'), t, r'\n121 State Street\t(?:[^\t]*\t){8}\s*' + MONEY)
        R.count('pct121', S(s + ' "Complete"'), t, r'\n121 State Street\t[^\n]*\n[^\n]*\n\s*(\d+)%', unit='%')
        await nav(pg, 'reports', None, ['#v-reports [data-reptab="portfolio"]', '#v-reports [data-reptab="wip"]']); t = await text_of(pg, 'reports')
        s = 'Reports › Projects › WIP Schedule'
        R.money('wip_over', S(s + ' headline'), t, MONEY + r'\s*\n\s*billings in excess of earnings')
        R.money('wip_over', S(s + ' Total row'), t, r'\nTotal · \d+ contracts?\t(?:[^\t]*\t){5}\s*' + MONEY)
        R.money('backlog', S(s + ' Total row'), t, r'\nTotal · \d+ contracts?\t(?:[^\t]*\t){7}\s*' + MONEY)
        R.money('backlog', S(s + ' backlog line'), t, MONEY + r'\s*\n\s*backlog ·')
        R.money('income', S(s + ' Total "Earned"'), t, r'\nTotal · \d+ contracts?\t(?:[^\t]*\t){3}\s*' + MONEY)
        for j in ('121 State Street', '45 Cranberry St', '140 Prospect Place'):
            R.money('wip_job:' + j, S(s), t, r'\n' + re.escape(j) + r'[^\n]*\n[^\n]*\n\t(?:[^\t]*\t){5}\s*' + MONEY)
        R.count('pct121', S(s + ' "% Complete"'), t, r'\n121 State Street\n[^\n]*\n\t[^\t]*\t[^\t]*\t(\d+)%', unit='%')
        R.count('pct121', S(s + ' "Physical %"'), t, r'\n121 State Street\t(\d+)%\t', unit='%', required=False)

        # Cash & Receivables › Receivables, Payables
        await nav(pg, 'reports', None, ['#v-reports [data-reptab="ar"]', '#v-reports [data-reptab="ar"]']); t = await text_of(pg, 'reports')
        R.money('ar', S('Reports › Cash & Receivables › Receivables'), t, MONEY + r'\s*\n\s*Open ·')
        if await click_js(pg, '#v-reports [data-reptab="payables"]'):
            t = await text_of(pg, 'reports')
            s = 'Reports › Cash & Receivables › Payables › AP Aging'
            R.money('ap_payroll_due', S(s + ' "Payroll" row'), t, r'\nPayroll\t(?:[^\t]*\t){4}\s*' + MONEY)
            R.money('ap_payroll_due', S(s + ' "Total" row, bills + payroll (bills owed = $0)'), t, r'AP AGING BY VENDOR.*?\nTotal\t(?:[^\t]*\t){4}\s*' + MONEY,
                    expected=PINNED['ap_bills'] + PINNED['ap_payroll_due'])
            if R.want('ap_paid_unappr'):
                m = re.search(r'Not due, and not in the aging:([^\n]*)', t)
                if m:
                    tot = sum(parse_money(x)[0] for x in re.findall(MONEY, m.group(1)))
                    ok = abs(tot - PINNED['ap_paid_unappr']) <= 1
                    R.readings.append({'figure': 'ap_paid_unappr', 'surface': S(s + ' note'), 'raw': m.group(1)[:80], 'value': tot, 'expected': PINNED['ap_paid_unappr'], 'ok': ok})
                    if not ok: R.flag('ap_paid_unappr', S(s + ' "not in the aging" note'), fmt(tot), fmt(PINNED['ap_paid_unappr']))
                else: R.flag('ap_paid_unappr', S(s), 'not shown', fmt(PINNED['ap_paid_unappr']))
            if R.want('ap_maybe_paid'):
                m = re.search(r'Held, possibly already paid:([^\n]*)', t)
                tot = sum(parse_money(x)[0] for x in re.findall(r'(?:^|; )[^;(]*?' + MONEY + r' \(', m.group(1))) if m else None
                ok = tot is not None and abs(tot - PINNED['ap_maybe_paid']) <= 1
                R.readings.append({'figure': 'ap_maybe_paid', 'surface': S(s + ' "possibly already paid" note'), 'raw': (m.group(1)[:80] if m else ''), 'value': tot, 'expected': PINNED['ap_maybe_paid'], 'ok': ok})
                if not ok: R.flag('ap_maybe_paid', S(s + ' "possibly already paid" note'), fmt(tot) if tot is not None else 'not shown', fmt(PINNED['ap_maybe_paid']))

        # Review › Weekly Flash
        await nav(pg, 'reports', None, ['#v-reports [data-reptab="analyst"]', '#v-reports [data-reptab="flash"]']); t = await text_of(pg, 'reports')
        s = 'Reports › Weekly Flash'
        R.money('cash', S(s + ' "Cash today"'), t, r'Cash today\s*\n\s*' + MONEY)
        R.money('safe', S(s + ' "Safe to spend"'), t, r'Safe to spend\s*\n\s*' + MONEY)
        R.money('ap_payroll_due', S(s + ' "Payables past due"'), t, r'Payables past due\s*\n\s*' + MONEY)
        R.money('backlog', S(s + ' "Backlog"'), t, r'Backlog \(contract − earned\)\s*\n\s*' + MONEY)
        R.money('wip_over', S(s + ' "Over / under billed"'), t, r'Over / under billed\s*\n\s*' + MONEY)
        R.money('net', S(s + ' "Net vs budget"'), t, r'\n' + MONEY + r' against \$')
        R.money('ar', S(s), t, r'\n(?:AR|Receivables|Accounts receivable|AR open)\s*\n\s*' + MONEY, required=False)
        R.count('unmatched_n', S(s), t, r'(\d+) bank (?:items|lines)', required=False)

    # Projects (overview table)
    if gate('ovjobs', 'Projects'):
        await nav(pg, 'jobs', 'ovjobs'); t = await text_of(pg, 'ovjobs')
        # the cost-to-cost figure is "Over-Billed (WIP)" (lane 1, 2026-10-26: "Billed Ahead of the Work" is the line-by-line control)
        R.money('wip_over', S('Projects › tile "Over-Billed (WIP)"'), t, r'Over-Billed \(WIP\)\s*\n\s*\+?' + MONEY)
        if R.want('ar'):
            owed = re.findall(r'\n[^\t\n]+\t[^\t\n]*\t\d+\t[^\t]*\t[^\t]*\t[^\t]*\t[^\t]*\t[^\t]*\t(\$[\d,]+)\t', t)
            tot = sum(parse_money(x)[0] for x in owed)
            ok = abs(tot - PINNED['ar']) <= 1
            R.readings.append({'figure': 'ar', 'surface': S('Projects › table "Owed" (sum)'), 'raw': str(owed), 'value': tot, 'expected': PINNED['ar'], 'ok': ok})
            if not ok: R.flag('ar', S('Projects › table "Owed" (sum)'), fmt(tot), fmt(PINNED['ar']))
        hdr = (re.search(r'\nPROJECT\t[^\n]*', t) or re.search(r'PROJECT[^\n]*', t))
        hdr = hdr.group(0) if hdr else ''
        if R.want('pct121'):
            if not re.search(r'% COMPLETE|PERCENT', hdr, re.I):
                R.flag('pct121', S('Projects › table (no "% Complete" column, BACKLOG §1.2)'), 'not shown', '14%')
            else:
                R.count('pct121', S('Projects › table "% Complete"'), t, r'\n121 State Street\t[^\n]*?(\d+)%', unit='%')
        if R.want('eac121') and not re.search(r'EAC|AT COMPLETION|PROJ\. COST', hdr, re.I):
            R.note('eac121', S('Projects › table'), 'no EAC column')

    # Chief of Staff
    if gate('cos', 'Chief of Staff'):
        # the Chief of Staff's pass is Ask's Findings › Every Chain (lane assistant); its old link lands on Today since the
        # Your Day mock-up (11-03), so the reading opens the pass where it lives, as a person does from Ask
        await nav(pg, 'ask', 'pa')
        await pg.evaluate("() => paOpen('findings', 'chains')"); await pg.wait_for_timeout(300)
        t = await text_of(pg, 'pa')
        s = 'Chief of Staff'
        R.count('unmatched_n', S(s), t, r'(\d+) bank items? not yet matched')
        R.money('unmatched_amt', S(s), t, r'bank items? not yet matched — ' + MONEY)
        for j in ('121 State Street', '45 Cranberry St', '140 Prospect Place'):
            R.money('wip_job:' + j, S(s), t, re.escape(j) + r'[^\n]* — ' + MONEY + r' invoiced ahead of the work', required=False)
        for k, pat in (('cash', r'[Cc]ash[^\n$]*' + MONEY), ('ar', r'[Rr]eceivable[^\n$]*' + MONEY), ('backlog', r'[Bb]acklog[^\n$]*' + MONEY),
                       ('net', r'[Nn]et (?:profit|income)[^\n$]*' + MONEY), ('safe', r'[Ss]afe to spend[^\n$]*' + MONEY),
                       ('rtb', r'(?:[Rr]eady to bill|earned and not billed|not yet invoiced)[^\n$]*' + MONEY),
                       ('ap_payroll_due', r'[Pp]ayroll[^\n$]*' + MONEY + r'[^\n]*past due')):
            R.money(k, S(s), t, pat, required=False)

    # Ask: the obvious question for each figure, typed into the box
    if gate('pa', 'Ask'):
        s = lambda q: S(f'Ask "{q}"')
        Q = [
            ('how much cash do we have', [('cash', MONEY + r' in the bank')]),
            ('what is our AR', [('ar', MONEY)]),
            ('how much are we owed', [('ar', MONEY)]),
            ('how many bank lines are unmatched', [('unmatched_n#', r'(\d+) bank (?:items?|lines?)'), ('unmatched_amt', MONEY)]),
            ('how much do we owe vendors', [('ap_bills', MONEY)]),
            ('what is our AP', [('ap_bills', MONEY)]),
            ('how much payroll is past due', [('ap_payroll_due', MONEY)]),
            ('how much are we over-billed', [('wip_over', MONEY)]),
            ('what is our backlog', [('backlog', MONEY)]),
            ('what is our net profit year to date', [('net', MONEY), ('income', r'of ' + MONEY + r' revenue')]),
            ('how much is safe to spend', [('safe', r'(?:Short by |safe to spend[^$]*?)' + MONEY)]),
            ('what is ready to bill', [('rtb', MONEY), ('rtb_n#', r'on (\d+) items?')]),
            ('how far along is 121 State Street', [('pct121#', r'(\d+)% complete')]),
            ('what is the EAC on 121 State Street', [('eac121', r'(?:EAC|[Ee]stimate at completion|[Ff]orecast at completion|[Pp]rojected cost)[^$\n]*' + MONEY)]),
        ]
        for q, reads in Q:
            if not any(R.want(k.rstrip('#')) for k, _ in reads): continue
            a = await ask(pg, q)
            head = a.split('\n', 1)[0] if a else ''
            for k, pat in reads:
                key = k.rstrip('#')
                if key == 'safe' and head.startswith('Short by'):
                    R.money(key, s(q), head, pat, sign=-1); continue
                if k.endswith('#'): R.count(key, s(q), head, pat, unit='%' if key == 'pct121' else '')
                else: R.money(key, s(q), head, pat)
            if R.verbose: print('   Ask:', q, '->', head[:140])

# ---- shop stock is held as inventory until used on a job (BACKLOG §1.8 item 12; the accountant to confirm):
# buy 10 sheets for the shop's stock, issue 12 to 121 State Street, return 2. Each step's expected movement is
# computed here from the raw inventory record (quantity x carried cost), never from the app's own totals: the
# purchase moves only the asset (1250 Inventory, outside the P&L), an issue moves cost from the asset to the job,
# a return moves it back, and the company P&L counts the material once, when it is used. The opening count is
# checked against the raw inventory rows too.
STOCK_SURFACES = ('jobFin actual', 'jobFin cost by code (stock)', 'lineFin actual (the estimate line)', 'Cost by Line',
                  'Overhead basis (direct cost)', 'GL 5100 Materials on the job', 'GL 1250 Inventory',
                  'GL 5100 Materials (company)', 'Company P&L cost of work', 'Company P&L outside the P&L')
STOCK_JS = """(key) => { const p = DB.projects.find(x => x.id === 'p121'), J = jobFin(p), f = lineFin(key);
  const row = (typeof clRows === 'function' ? (clScope = 'all', clRows()) : []).find(r => r.key === key || (r.f && r.f.key === key)) || {};
  try { glSync(); } catch (e) {}
  const gl = (acct, job) => (DB.gl.journals || []).filter(j => j.status === 'posted').flatMap(j => j.lines).filter(l => l.acct === acct && (!job || l.projectId === 'p121')).reduce((a, l) => a + (+l.dr || 0) - (+l.cr || 0), 0);
  DB.company.ohBasis = 'cost'; const ym = today().slice(0, 7); __ohMemo = { key: '', m: {} };
  const oh = (ohMonth(ym).base || {})['p121'] || 0, P = companyPL([ym + '-01', today()]);
  return { 'jobFin actual': J.actual, 'jobFin cost by code (stock)': (J.byCode || []).reduce((a, b) => a + (+b.stock || 0), 0), 'lineFin actual (the estimate line)': f ? f.actual : null,
    'Cost by Line': row.actual != null ? row.actual : null, 'Overhead basis (direct cost)': oh, 'GL 5100 Materials on the job': gl('5100', true), 'GL 1250 Inventory': gl('1250'),
    'GL 5100 Materials (company)': gl('5100'), 'Company P&L cost of work': P.cogsT, 'Company P&L outside the P&L': P.nonT,
    eac: J.eac, journals: (DB.gl.journals || []).filter(j => j.key && j.key.startsWith('stk:')).map(j => [j.key, j.memo, j.status]),
    opening: (DB.gl.journals || []).filter(j => j.key === 'stkopen' && j.status === 'posted').map(j => j.lines.map(l => [l.acct, +l.dr || 0, +l.cr || 0])) }; }"""

async def check_stock(p, R):
    if not R.want('stock'): return
    b, pg, errs = await open_app(p)
    await sign_in(pg, 'u_owner')
    raw = await pg.evaluate("() => { const iv = DB.inventory.find(i => i.id === 'iv16'), p = DB.projects.find(x => x.id === 'p121'); return { cost: iv.cost, qty: iv.qty, unit: iv.unit, key: stockLineKey(p, iv), owned: stockClientOwned(p), inv: DB.inventory.map(i => [i.id, i.type, +i.qty || 0, +i.cost || 0]), use: (DB.stock.use || []).map(u => [u.invId, u.kind, Math.abs(+u.qty || 0)]) }; }")
    cost, key = float(raw['cost']), raw['key']
    if not key:
        R.flag('stock', 'the estimate line', 'none', 'the drywall line on 121 State Street'); await b.close(); return
    # the opening count at carried cost, from the raw rows: on hand plus what has moved out since (less returns)
    moved = {}
    for inv_id, kind, q in raw['use']: moved[inv_id] = moved.get(inv_id, 0) + (-q if kind == 'return' else q)
    opening = round(sum((q + moved.get(i, 0)) * c for i, t, q, c in raw['inv'] if t != 'tool' and c > 0 and q + moved.get(i, 0) > 0), 2)
    before = await pg.evaluate(STOCK_JS, key)
    O = before['opening']
    ok = len(O) == 1 and sorted(O[0]) == sorted([['1250', opening, 0], ['3900', 0, opening]])
    R.readings.append({'figure': 'stock', 'surface': 'opening count (Dr 1250, Cr 3900)', 'raw': str(O), 'value': O and O[0][0][1], 'expected': opening, 'ok': ok})
    if not ok: R.flag('stock', 'opening count posted at carried cost', str(O), f'Dr 1250 / Cr 3900 {opening:,.2f}')
    # 1. buy 10 sheets for the shop's stock: a bill coded Shop stock, no job
    await pg.evaluate("""(c) => { DB.bills.push({ id: 'bxstk1', vendor: 'Mercer Lumber', number: 'XS-STOCK-1', date: today(), due: today(), entityId: 'ent1', projectId: '', cat: 'stock', code: '', line: '',
        lines: [{ id: 'xsl1', desc: '5/8" Type X drywall 4x8 for the shop: 10 sheets', amount: Math.round(10 * c * 100) / 100 }], status: 'approved', approvals: [], createdBy: 'finance_xcheck' });
        DB.inventory.find(i => i.id === 'iv16').qty += 10; }""", cost)
    bought = await pg.evaluate(STOCK_JS, key)
    await pg.evaluate("() => { invMove(DB.inventory.find(i => i.id === 'iv16'), 'p:p121', 12, 'finance_xcheck: issue to the job'); }")
    issued = await pg.evaluate(STOCK_JS, key)
    await pg.evaluate("() => stockReturn({ projectId: 'p121', invId: 'iv16', qty: 2, loc: 'wh', reason: 'finance_xcheck: two sheets left over', force: true })")
    back = await pg.evaluate(STOCK_JS, key)
    buy, up, down = round(10 * cost, 2), round(12 * cost, 2), round(-2 * cost, 2)   # computed here, from the inventory record
    want = {k: (0, up, down) for k in STOCK_SURFACES}
    want['GL 1250 Inventory'] = (buy, -up, -down)        # the purchase is the asset; an issue credits it, a return debits it
    want['Company P&L outside the P&L'] = (buy, 0, 0)    # the purchase sits outside the P&L, never as cost
    for k in STOCK_SURFACES:
        for (a0, a1, w, step) in ((before, bought, want[k][0], 'buy 10 for stock'), (bought, issued, want[k][1], 'issue 12'), (issued, back, want[k][2], 'return 2')):
            seen = None if a0[k] is None or a1[k] is None else round(a1[k] - a0[k], 2)
            ok = seen is not None and abs(seen - w) <= 0.01
            R.readings.append({'figure': 'stock', 'surface': f'{k} ({step})', 'raw': str(seen), 'value': seen, 'expected': w, 'ok': ok})
            if not ok: R.flag('stock', f'{k} ({step})', str(seen), f'{w:+,.2f}')
            elif R.verbose: print('  ok STOCK |', k, step, seen)
    # counted once: over the three steps the company's cost of work moved by what the job used, not by purchase plus use
    pl = round(back['Company P&L cost of work'] - before['Company P&L cost of work'], 2)
    job = round(back['jobFin actual'] - before['jobFin actual'], 2)
    ok = abs(pl - (up + down)) <= 0.01 and abs(pl - job) <= 0.01
    R.readings.append({'figure': 'stock', 'surface': 'P&L counts the material once (buy, issue, return)', 'raw': str(pl), 'value': pl, 'expected': up + down, 'ok': ok})
    if not ok: R.flag('stock', 'P&L counts the material once', f'P&L {pl:+,.2f}, job {job:+,.2f}', f'{up + down:+,.2f} (not {buy + up + down:+,.2f})')
    J = back['journals']
    if len(J) != 2 or not any('finance_xcheck: two sheets left over' in m for _, m, _ in J):
        R.flag('stock', 'GL journals (append-only, the return carries its reason)', str(J), 'one issue and one return journal, the return naming its reason')
    for e in errs[:3]: R.flag('stock', 'page', e[:200], 'no page errors')
    await b.close()

# ---- ledger invariants ------------------------------------------------------------------------------------------
INV_SUM = "const S = (L) => { const o = {}; (L || []).forEach(l => o[l.acct] = r2((o[l.acct] || 0) + (+l.dr || 0) - (+l.cr || 0))); return o; };"
# every journal, summed by the record it posts for (a reversal and re-post nets to the change)
INV_POSTED = INV_SUM + """ const P = () => { glSync(); const o = {}; (DB.gl.journals || []).filter(j => j.sourceId).forEach(j => { const m = o[j.sourceId] = o[j.sourceId] || {};
  (j.lines || []).forEach(l => m[l.acct] = r2((m[l.acct] || 0) + (+l.dr || 0) - (+l.cr || 0))); }); Object.values(o).forEach(m => Object.keys(m).forEach(k => Math.abs(m[k]) < 0.005 && delete m[k])); return o; };"""

INV_ONE_JS = INV_SUM + """
  const ctl = analystFindings().filter(x => x.area === 'Controller').map(x => (x.title || '') + ' ' + (x.detail || '')).join('\\n');
  const out = [];
  DB.clients.forEach(c => (c.invoices || []).forEach(i => {
    if (['draft', 'void'].includes(i.status) || i.retainerOf || i.retainageRelease) return;
    const L = S(glInvoiceLines(c, i)), rev = -Object.keys(L).filter(a => /^4/.test(a)).reduce((a, k) => a + L[k], 0), held = -(L['2400'] || 0);
    const A = { ledger: rev > 0.005 ? 'work' : held > 0.005 ? 'deposit' : null,
      print: typeof cxKind === 'function' ? (cxKind(i) === 'deposit' ? 'deposit' : 'work') : null,
      invIsDeposit: typeof invIsDeposit === 'function' ? (invIsDeposit(i) ? 'deposit' : 'work') : null, sovBilled: null, lineFin: null };
    const l = i.mode === 'sov' && (i.lines || []).find(x => x.sovId && +x.pct > 0);
    if (l) {
      A.sovBilled = sovBilled(c, l.sovId) - sovBilled(c, l.sovId, i.id) > 0.001 ? 'work' : 'deposit';
      const sv = (c.sov || []).find(v => v.id === l.sovId);
      if (sv && sv.lineRef && typeof lineFin === 'function') {
        const a = lineFin(sv.lineRef), st = i.status; i.status = 'void';
        let b; try { b = lineFin(sv.lineRef); } finally { i.status = st; }
        if (a && b && a.billedPct - b.billedPct > 0.001) A.lineFin = a.depositPct - b.depositPct > 0.001 ? 'deposit' : 'work';
      }
    }
    const v = [...new Set(Object.values(A).filter(Boolean))];
    if (v.length > 1) {
      // the one disagreement allowed: a sent document reprints as it was sent while its books say otherwise, and a
      // Controller finding names it (never re-classed silently); the books, line figures and predicate still agree
      const books = [...new Set([A.ledger, A.sovBilled, A.lineFin, A.invIsDeposit].filter(Boolean))];
      const named = books.length === 1 && ctl.includes(i.number);
      out.push({ n: i.number, client: c.name, A: A, named: named });
    }
  }));
  return out;"""

INV_BANK_JS = """
  // a fixture that has fooled the matcher before: two equal payments a day apart and one bank line between them;
  // a payment typed against a line smaller than itself; a payment typed against a line edited after it arrived
  const c = DB.clients.find(x => (x.payments || []).length) || DB.clients[0], acct = ((DB.accounts || []).find(a => a.type === 'bank') || {}).id || 'ac1';
  const mk = (id, amt, d, desc) => { const t = txnStamp({ id: id, date: d, acct: acct, desc: desc, amt: amt, cat: 'income', source: 'ofx', status: 'categorized' }, 'stmt:finx', id); DB.txns.push(t); return t; };
  mk('fx_one', 4321.09, '2026-09-02', 'MOBILE DEPOSIT');
  const small = mk('fx_small', 1000, '2026-09-02', 'DEPOSIT ' + String(c.name || '').toUpperCase());
  const edited = mk('fx_edit', 2500, '2026-09-02', 'DEPOSIT ' + String(c.name || '').toUpperCase()); edited.amt = 2600;
  c.payments.push({ id: 'fxp1', date: '2026-09-01', amount: 4321.09, method: 'check', ref: 'FX-1' }, { id: 'fxp2', date: '2026-09-03', amount: 4321.09, method: 'check', ref: 'FX-2' },
    { id: 'fxp3', date: '2026-09-02', amount: 1500, method: 'ach', ref: 'FX-3', txnId: small.id }, { id: 'fxp4', date: '2026-09-02', amount: 2600, method: 'ach', ref: 'FX-4', txnId: edited.id });
  if (typeof payBackReset === 'function') payBackReset();
  render(); await sleep(150);
  const amtOf = (cl, p) => typeof payBankedAmt === 'function' ? payBankedAmt(cl, p) : (typeof payBanked === 'function' && payBanked(cl, p) ? +p.amount : 0);
  const map = typeof payBacking === 'function' ? payBacking() : null, per = {}, bad = [];
  let backed = 0;
  DB.clients.forEach(cl => (cl.payments || []).forEach(p => {
    if (p.reverses || !(+p.amount > 0)) return;
    const a = amtOf(cl, p); if (!(a > 0.005)) return;
    backed = r2(backed + a);
    const t = map && map.get(p) ? map.get(p).t : (p.txnId ? (DB.txns || []).find(x => x.id === p.txnId) : null);
    if (!t) { bad.push(`${cl.name} ${p.ref || p.id} ${a}: counted in the bank with no bank line`); return; }
    if (typeof bfBacked === 'function' && !bfBacked(t)) bad.push(`${cl.name} ${p.ref || p.id} ${a}: backed by ${t.id}, a line the bank did not send as it stands`);
    per[t.id] = per[t.id] || { amt: +t.amt, by: [], sum: 0 };
    per[t.id].by.push((p.ref || p.id) + ' ' + a); per[t.id].sum = r2(per[t.id].sum + a);
  }));
  Object.entries(per).forEach(([id, x]) => x.sum > x.amt + 0.005 && bad.push(`bank line ${id} ($${x.amt}) backs $${x.sum}: ${x.by.join(', ')}`));
  const lines = r2((DB.txns || []).filter(t => +t.amt > 0 && t.status !== 'void' && (typeof bfBacked !== 'function' || bfBacked(t))).reduce((a, t) => a + +t.amt, 0));
  const fx = ['fxp1', 'fxp2', 'fxp3', 'fxp4'].map(id => r2(amtOf(c, c.payments.find(x => x.id === id))));
  return { bad: bad, backed: backed, lines: lines, fx: fx };"""

INV_EDIT_JS = INV_POSTED + """
  const before = P(), docs = [];
  DB.clients.forEach(c => (c.invoices || []).forEach(i => {
    if (['draft', 'void'].includes(i.status) || !(i.lines || []).length) return;
    docs.push([i.id, i.number, c.name, i.status]);
    i.title = String(i.title || '') + ' (less deposit)';
    i.retainagePct = +i.retainagePct > 0 ? 0 : 10;
    const l = i.lines[0];
    if ('pct' in l) l.pct = r2((+l.pct || 0) + 5); else l.qty = (+l.qty || 1) + 1;
    l.desc = 'Deposit ' + String(l.desc || '');
  }));
  save(); render(); await sleep(200);
  const after = P(), moved = [];
  docs.forEach(([id, n, cn, st]) => { const a = JSON.stringify(before[id] || {}), b = JSON.stringify(after[id] || {}); a !== b && moved.push(`${cn} ${n} (${st}): ${a} -> ${b}`); });
  // and nothing else moved because of them
  Object.keys(Object.assign({}, before, after)).forEach(k => !docs.some(d => d[0] === k) && JSON.stringify(before[k] || {}) !== JSON.stringify(after[k] || {}) && moved.push(`${k}: ${JSON.stringify(before[k] || {})} -> ${JSON.stringify(after[k] || {})}`));
  return { n: docs.length, moved: moved };"""

INV_DEP_JS = INV_SUM + """
  const out = [];
  DB.clients.forEach(c => {
    const deps = (c.invoices || []).filter(i => typeof invIsDeposit === 'function' && invIsDeposit(i) && i.depositOf && !['draft', 'void'].includes(i.status));
    [...new Set(deps.map(i => i.depositOf))].forEach(eid => {
      const est = (c.estimates || []).find(e => e.id === eid);
      const payers = (c.payers || []).length > 1 ? c.payers.map(p => p.id) : [''];
      payers.forEach(pid => {
        const lj = pid && typeof LJ !== 'undefined';
        let inv; if (lj) LJ.pick = pid;
        try { inv = newDoc(c, 'invoice', pid ? { mode: 'sov', payer: pid } : { mode: 'sov' }); } finally { if (lj) LJ.pick = ''; }
        if (!c.invoices.includes(inv)) c.invoices.push(inv);
        inv.depositOf = eid;
        inv.lines.forEach(l => { l.prevPct = r2(sovBilled(c, l.sovId, inv.id)); l.pct = r2(Math.max(0, 100 - l.prevPct)); });
        inv.lines = inv.lines.filter(l => l.pct > 0);
        if (!inv.lines.length) { c.invoices = c.invoices.filter(x => x !== inv); return; }
        docTotal(inv); inv.status = 'sent'; docMark(inv);
      });
      const all = c.invoices.filter(i => !['void', 'draft'].includes(i.status) && (i.depositOf === eid));
      const held = r2(all.reduce((a, i) => a + (S(glInvoiceLines(c, i))['2400'] || 0), 0));
      const open = (c.sov || []).filter(v => !v.coId && String(v.lineRef || '').startsWith('estimate:' + eid)).map(v => r2(sovBilled(c, v.id))).filter(x => x < 99.99).length;
      out.push({ client: c.name, est: est ? est.number : eid, deposits: deps.filter(i => i.depositOf === eid).map(i => i.number), held: held, open: open });
    });
  });
  return out;"""

# ---- INV STAMP BACKED (BACKLOG §1.36, 11-04): every approval stamp on every bill, payroll run, card spend, PO, change
# order and payment ("recommended by PM", "approved for payment by Owner", a routing step, a short-pay, approvedBy) has an
# audit row by the same person, on the same record, at or before the stamp. A stamp with no person or no moment fails
# too. "built from approved hours" names where a figure came from, not an approval, and is not a stamp.
INV_STAMP_FN = """
  const STAMP = /\\b(recommended|approved|verified|signed off)\\b/i, NOT = /\\bfrom approved\\b/i, lc = s => String(s || '').trim().toLowerCase();
  const stampsUnbacked = () => {
    const out = [];
    const name = r => r.number || r.period || r.title || r.id;
    const backed = (kind, r, by, ts, what) => {
      if (!lc(by)) return out.push({ kind, rec: name(r), what, why: 'a stamp with no person' });
      const A = (DB.audit || []).filter(a => a.refId === r.id && lc(a.by) === lc(by) && (!ts || (a.ts && a.ts <= ts)));
      if (!A.length) out.push({ kind, rec: name(r), what, by, ts: ts || '', why: `no audit row by ${by} on it at or before the stamp` });
    };
    const walk = (kind, L) => (L || []).forEach(r => {
      if (!r || typeof r !== 'object') return;
      (r.approvals || []).forEach(a => {
        const w = String(a.action || '');
        if (!STAMP.test(w) || NOT.test(w)) return;
        if (!a.ts) return out.push({ kind, rec: name(r), what: w, by: a.by, why: 'a stamp with no moment (ts)' });
        backed(kind, r, a.by, a.ts, w);
      });
      if (r.approvedBy && ['po', 'co', 'spend', 'change', 'client-credit', 'ledger', 'subchange'].includes(kind)) {
        // a record that names its approver names a person who acted, never a role (glApprove wrote "owner")
        // (the demo's owner is a person named "Owner": a name of a user is a person; a lowercase role key is not)
        if (!(DB.users || []).some(u => u.name === r.approvedBy) && /^(owner|pm|coord|controller|billing|foreman|crew|designer)$/.test(String(r.approvedBy).trim())) out.push({ kind, rec: name(r), what: 'approvedBy ' + r.approvedBy, why: 'names a role, not the person who approved' });
        else backed(kind, r, r.approvedBy, '', 'approvedBy ' + r.approvedBy);
      }
    });
    walk('bill', DB.bills); walk('payroll', DB.payroll); walk('spend', DB.spend); walk('po', DB.pos);
    (DB.clients || []).forEach(c => { walk('co', c.changeOrders); walk('payment', c.payments); });
    // the stamps outside bills and payroll (BACKLOG §1.36): rule and setting changes, client credits, journals, a
    // subcontract's change orders
    walk('change', DB.changes); walk('client-credit', DB.clientCredits); walk('ledger', ((DB.gl || {}).journals || []).filter(j => j.status === 'posted'));
    (DB.pos || []).forEach(po => walk('subchange', (po.sc || {}).changes));
    return out;
  };"""
INV_STAMP_JS = INV_STAMP_FN + """
  const seeded = stampsUnbacked();
  // each approval path, done by its person through the app's own action: the PM recommends AMP-311, the owner approves
  // it (with the reason its flags ask for), the owner approves the payroll run, the owner approves a PO waiting on him
  const as = u => { signIn(u); render(); };
  const amp = DB.bills.find(b => b.number === 'AMP-311'), pr = (DB.payroll || []).find(r => r.status === 'submitted');
  const did = [], held = [], same = {};
  // one safe next step on every surface that offers a bill a verb (review item 4): the bill page's one blue button
  // leads the bill's Approvals row, and no Approve, Pay or Release is blue there
  const surfaces = async (num) => {
    const b = DB.bills.find(x => x.number === num); if (!b) return null;
    as('u_owner'); openBill(b.id); await sleep(200);
    const page = [...document.querySelectorAll('#drawer button.primary')].filter(x => x.getClientRects().length).map(x => x.innerText.trim());
    try { closeEditor(); } catch (e) {}
    // the owner's approvals are Today's Approvals tab (the Your Day batch, 11-05; the old Approvals page opens Today):
    // the bill's row, selected, and its side panel's buttons, the lead first (its amount after a comma is not its words)
    const vis = e => !!e && e.getClientRects().length > 0;
    let appr = null;
    try { tdyTabSet('appr'); tdyAllOpen = true; } catch (e) {}
    view = 'home'; render(); await sleep(250);
    const card = [...document.querySelectorAll('.view.on .td-do .td-card')].find(x => vis(x) && x.innerText.includes(num));
    if (card) {
      const own = [...card.querySelectorAll('button')].filter(vis);
      if (!own.length) { card.click(); await sleep(250); }
      const aside = document.querySelector('.view.on .td2-aside');
      const B = own.length ? own : aside ? [...aside.querySelectorAll('button')].filter(vis) : [];
      appr = B.map(x => ({ l: x.innerText.trim().replace(/,\\s*[\\u2212-]?\\$[\\d,.]+$/, ''), blue: x.classList.contains('primary') }));
    }
    // a bill not on Today's Approvals at all offers nothing there to get wrong
    const ok = page.length === 1 && !/^(approve|pay|release)/i.test(page[0]) && (!appr || (appr[0] && appr[0].l === page[0] && !appr.some(x => x.blue && /^(approve|pay|release|recommend)/i.test(x.l))));
    return { ok, page, appr };
  };
  same.pba = await surfaces('WW-2026-118');
  // a held bill takes no stamp by any path (chief-of-staff review, 11-04): AMP-311 held, then the PM recommends it
  // (billAction, and the routing step rtApprove) and the owner approves it (rtApprove, and billAction); its status and
  // its trail must not move, and nothing is skipped on it
  if (amp) {
    amp.onHold = { why: 'the stamp check: held', by: 'Owner', at: appNowIso(), for: 'Chen Biron', state: 'open' };
    same.held = await surfaces('AMP-311');
    const s0 = amp.status, n0 = (amp.approvals || []).length;
    const tryAs = (u, what, f) => { try { as(u); f(); } catch (e) { held.push(what + ' threw ' + e.message); } if (amp.status !== s0 || (amp.approvals || []).length !== n0) held.push(`${what} moved the held bill: ${amp.status}, ${(amp.approvals || []).slice(n0).map(a => a.action).join('; ')}`); };
    tryAs('u_alan', 'PM recommend (billAction pmok)', () => billAction(amp, 'pmok'));
    tryAs('u_alan', 'PM step (rtApprove)', () => rtApprove(amp, 'the stamp check'));
    tryAs('u_owner', 'owner step (rtApprove)', () => rtApprove(amp, 'the stamp check'));
    tryAs('u_owner', 'owner approve (billAction approve)', () => billAction(amp, 'approve', 'the stamp check: approved with its flags read'));
    did.push(`held ${amp.number}: ${held.length ? 'moved' : 'unmoved'} by 4 paths`);
    amp.onHold.state = 'released';
  }
  // a stamp with no audit row reads as such where it is shown (the bill's Approval Trail), never as a clean approval
  const nt = DB.bills.find(b => b.number === 'NT-88412'), ui = { planted: '', clean: '' };
  if (nt) {
    nt.approvals.push({ t: '8/12 9:00 AM', ts: '2026-08-12T09:00:00', by: 'Nobody Real', role: 'owner', action: 'approved for payment by Owner' });
    as('u_owner'); openBill(nt.id); await sleep(200);
    const lines = [...document.querySelectorAll('#d-body .trail > div')].map(d => d.innerText.replace(/\\s+/g, ' '));
    ui.planted = lines.find(l => /Nobody Real/.test(l)) || 'not shown';
    ui.clean = lines.filter(l => !/Nobody Real/.test(l) && /no record of this action/i.test(l)).join(' | ');
    try { closeEditor(); } catch (e) {}
    nt.approvals.pop();
  }
  try { as('u_alan'); if (amp) { billAction(amp, 'pmok'); did.push('pmok ' + amp.status); } } catch (e) { did.push('pmok threw ' + e.message); }
  try { as('u_owner'); if (amp) { billAction(amp, 'approve', 'the stamp check: approved with its flags read'); did.push('approve ' + amp.status); } } catch (e) { did.push('approve threw ' + e.message); }
  try { if (pr) { const k = appConfirm; appConfirm = () => true; try { payrollAction(pr, 'approve'); } finally { appConfirm = k; } did.push('payroll ' + pr.status); } } catch (e) { did.push('payroll threw ' + e.message); }
  try { const po = (DB.pos || []).find(p => p.status === 'pending'); if (po) { poAction(po, 'approve'); did.push('po ' + po.number + ' ' + (po.approvedBy || '')); } } catch (e) { did.push('po threw ' + e.message); }
  // the stamps outside bills and payroll (BACKLOG §1.36), each by its person through the app's own action:
  // the owner posts a manual journal (glApprove recorded the role "owner", not the person)
  try {
    as('u_owner');
    const jid = uid('je');
    DB.gl.journals.push({ id: jid, kind: 'manual', status: 'pending', entityId: 'ent1', date: '2026-09-02', memo: 'The stamp check: van depreciation, August', createdBy: 'Jeanette', createdAt: appNowIso(), lines: [glL('7100', 1200, 0), glL('1500', 0, 1200)] });
    glApprove(jid, 'the stamp check: straight-line on the van');
    const j = DB.gl.journals.find(x => x.id === jid);
    did.push('journal ' + (j && j.status) + ' by ' + (j && j.approvedBy));
  } catch (e) { did.push('journal threw ' + e.message); }
  // the owner approves a drafted rule change from Meetings > Changes (it wrote no audit row)
  try {
    as('u_owner');
    const ch = (DB.changes || []).find(c => c.status === 'draft' && c.kind !== 'code' && c.source !== 'loop');
    if (ch) {
      mtTab = 'changes'; mtOpen = ''; view = 'meetings'; render(); await sleep(150);
      const b = document.querySelector(`[data-chok="${ch.id}"]`);
      b ? b.click() : 0;
      did.push('change ' + (b ? ch.status + ' by ' + ch.approvedBy : 'no Approve shown'));
    } else did.push('change: none drafted');
  } catch (e) { did.push('change threw ' + e.message); }
  // billing approves a credit the client is owed (its approval wrote no audit row)
  try {
    as('u_billing');
    const p = DB.projects.find(x => x.id === 'p121'), cc = { id: uid('cc'), projectId: p.id, clientId: p.clientId, amount: 140, txnId: '', why: 'The stamp check: Nemo Tile credited $140 for cracked tile billed to the client', status: 'proposed', at: today(), by: 'Chen Biron' };
    (DB.clientCredits = DB.clientCredits || []).push(cc);
    const row = blCreditRows().find(r => r.cc && r.cc.id === cc.id);
    row && blCreditAct(row);
    did.push('client credit ' + cc.status + ' by ' + cc.approvedBy);
  } catch (e) { did.push('client credit threw ' + e.message); }
  as('u_owner');
  await sleep(100);
  const after = stampsUnbacked();
  const stamps = (DB.bills || []).concat(DB.payroll || []).flatMap(r => (r.approvals || []).filter(a => STAMP.test(a.action || '') && !NOT.test(a.action || ''))).length;
  return { seeded, after, did, stamps, held, ui, same };"""

# ---- INV AUDIT CHAIN (BACKLOG §1.36, S1): the audit trail is hash-chained and append-only. As seeded and after a write
# it verifies; editing a sealed row's words or its person, removing a row from the middle and removing the newest row
# each fail verify, naming the row; put back, it verifies again; 5,100 more rows drop none (the store dropped its
# oldest past 5,000, so a true approval later read as unbacked).
INV_CHAIN_JS = """
  if (typeof auditVerify !== 'function') return { missing: true };
  await sleep(50);
  const out = {}, A = DB.audit, sum = v => ({ ok: v.ok, rows: v.rows, pending: v.pending, at: v.broken[0] ? v.broken[0].at : -1, why: v.broken[0] ? v.broken[0].why : '' });
  out.seeded = sum(auditVerify());
  audit('note', 'chaincheck', 'checked', '', '', 'the chain check');
  await sleep(30);
  out.afterWrite = sum(auditVerify());
  const k = Math.floor(A.length / 2);
  const was = A[k].note; A[k].note = String(was || '') + ' (edited)'; out.edited = sum(auditVerify()); A[k].note = was;
  const wb = A[k].by; A[k].by = 'Someone Else'; out.editedBy = sum(auditVerify()); A[k].by = wb;
  const [rm] = A.splice(k, 1); out.removed = sum(auditVerify()); A.splice(k, 0, rm);
  const last = A.pop(); out.removedLast = sum(auditVerify()); A.push(last);
  out.k = k; out.restored = sum(auditVerify());
  const n0 = A.length, first = A[0].id;
  for (let i = 0; i < 5100; i++) audit('note', 'chaincheck', 'bulk', '', '', '');
  await sleep(80);
  out.bulk = { added: A.length - n0, firstKept: A[0].id === first, v: sum(auditVerify()) };
  return out;"""

# ---- the money definitions (BACKLOG §1.35, the Accounting lane, 11-03): one question, one number, from the records ----
# Each is recomputed here from the records by its own definition, never by calling the function that prints it, and
# then compared with every place that prints it.
INV_MONEY_JS = """
  const out = { safe: [], jobcost: [] };
  const say = (k, ok, seen, want) => out[k].push([!!ok, String(seen).slice(0, 400), String(want).slice(0, 200)]);
  const near = (a, b, t) => Math.abs((+a || 0) - (+b || 0)) <= (t == null ? 0.01 : t);
  const fresh = async () => { if (typeof payBackReset === 'function') payBackReset(); render(); await sleep(120); };
  const strip = h => String(h || '').replace(/<[^>]+>/g, ' ').replace(/\\s+/g, ' ');
  // 1. Safe to Spend. The set-aside, job by job: cash received on the job's invoices that a bank line backs, less earned
  const banked = (c, py) => typeof payBankedAmt === 'function' ? payBankedAmt(c, py) : (payBanked(c, py) ? +py.amount : 0);
  const setAsideFromRecords = () => {
    let tot = 0; const by = {};
    DB.projects.forEach(p => {
      const c = DB.clients.find(x => x.id === p.clientId); if (!c) return;
      const ids = new Set((c.invoices || []).filter(i => i.projectId === p.id && !['void', 'draft'].includes(i.status)).map(i => i.id));
      const got = r2((c.payments || []).filter(py => !py.unapplied && ids.has(py.invoiceId)).reduce((a, py) => a + banked(c, py), 0));
      const amt = r2(Math.max(0, got - jobFin(p).earned)); by[p.id] = amt; tot = r2(tot + amt);
    });
    return { tot, by };
  };
  const read = () => { const X = safeToSpend(); return { safe: X.safe, ours: X.B.trulyOurs, cash: X.B.cash, cashToday: X.B.cashToday, sa: X.B.setAside, low: X.low, lowOurs: X.F.lowOurs, weeks: X.F.weeks }; };
  await fresh();
  let A = setAsideFromRecords(), X = read();
  say('safe', near(X.sa, A.tot), `companyBalance set-aside ${X.sa}`, `${A.tot} from the payments with a bank line, less earned, job by job`);
  say('safe', near(X.ours, r2(X.cashToday - A.tot)), `ours today ${X.ours}`, `cash today ${X.cashToday} less ${A.tot}`);
  const lowW = X.weeks && X.weeks.length ? r2(Math.min(...X.weeks.map(w => w.balance - (w.setAside == null ? NaN : w.setAside)))) : NaN;
  say('safe', near(X.low, lowW), `13-week low after the set-aside ${X.low}`, `${lowW}: each week's balance less its set-aside`);
  say('safe', near(X.safe, Math.min(X.ours, lowW)), `Safe to Spend ${X.safe}`, `the lower of ${X.ours} and ${lowW}`);
  say('safe', X.weeks && X.weeks.every(w => w.setAside != null && w.setAside >= 0), 'every forecast week carries its set-aside', 'w.setAside >= 0 on all 13 weeks');
  say('safe', near(stsSafe(), X.safe) && near(PRED.safeToSpend.figure(), X.safe), `stsSafe ${stsSafe()} · PRED ${PRED.safeToSpend.figure()}`, `${X.safe} everywhere`);
  out.safeNow = X.safe;
  // sending an invoice nobody has paid moves Safe to Spend by $0 (billed and unpaid is never set aside)
  const c121 = DB.clients.find(c => (c.invoices || []).some(i => i.projectId === 'p121'));
  const inv = newDoc(c121, 'invoice', { mode: 'items' });
  inv.projectId = 'p121'; inv.lines = [{ id: uid('l'), item: 'Invariant check: billed, not paid', qty: 1, unit: 'ls', rate: 25000 }];
  if (!c121.invoices.includes(inv)) c121.invoices.push(inv);
  docTotal(inv); inv.status = 'sent'; inv.date = today(); inv.due = iso(addDays(parse(today()), 30)); docMark(inv);
  await fresh();
  let Y = read();
  say('safe', near(Y.ours, X.ours) && near(Y.safe, X.safe), `sent $25,000 unpaid: ours ${X.ours} -> ${Y.ours}, safe ${X.safe} -> ${Y.safe}`, 'both unchanged');
  // a payment with a bank line on a job already collected ahead of its work: Safe to Spend moves by the cash less what
  // it sets aside, which is the whole payment (it is all collected ahead)
  const pay = (c, i, amt, id) => {
    DB.txns.push(txnStamp({ id: id, date: today(), acct: ((DB.accounts || []).find(a => a.type === 'bank') || {}).id || 'ac1', desc: 'DEPOSIT ' + id, amt: amt, cat: 'income', source: 'ofx', status: 'categorized' }, 'stmt:finx', id));
    c.payments.push({ id: 'p_' + id, date: today(), amount: amt, invoiceId: i.id, txnId: id, method: 'ACH' });
  };
  X = Y; pay(c121, inv, 25000, 'fx_sa121'); await fresh(); Y = read(); A = setAsideFromRecords();
  say('safe', near(Y.sa - X.sa, 25000) && near(Y.ours - X.ours, (Y.cash - X.cash) - 25000), `paid $25,000 on 121 State (collected ahead): cash ${r2(Y.cash - X.cash)}, set-aside ${r2(Y.sa - X.sa)}, ours ${r2(Y.ours - X.ours)}`, 'set-aside +25,000; ours moves by cash less 25,000');
  // on a job not yet collected ahead: only the part beyond what the job has earned is set aside
  const p140 = DB.projects.find(p => p.id === 'p140'), c140 = p140 && DB.clients.find(c => c.id === p140.clientId);
  const i140 = c140 && (c140.invoices || []).find(i => i.projectId === 'p140' && !['void', 'draft', 'paid'].includes(i.status));
  if (i140) {
    const before = setAsideFromRecords().by.p140 || 0, earned = jobFin(p140).earned, bal = r2(docTotal(i140).total);
    X = read(); pay(c140, i140, bal, 'fx_sa140'); await fresh(); Y = read();
    const want = r2(Math.max(0, bal - earned) - before);
    say('safe', near(Y.sa - X.sa, want) && near(Y.ours - X.ours, (Y.cash - X.cash) - want), `paid ${bal} on 140 Prospect (earned ${earned}): set-aside ${r2(Y.sa - X.sa)}, ours ${r2(Y.ours - X.ours)}, cash ${r2(Y.cash - X.cash)}`, `set-aside +${want}`);
  } else say('safe', false, 'no open invoice on 140 Prospect', 'the seed has INV-2026-D140-R open');
  // 2. one job cost: the posted cost is the P&L by project row; posted plus not yet posted is the job's own figure
  if (typeof jobCostPosted !== 'function' || typeof jobCostTie !== 'function') { say('jobcost', false, 'no one job-cost function (jobCostPosted, jobCostTie)', 'one function every screen reads'); return out; }
  DB.projects.forEach(p => {
    const C = jobCostPosted(p), J = jobFin(p);
    const S = rpPL(['2000-01-01', today()]), row = (S.rows || []).find(x => x.id === p.id);
    if (!row && !(J.actual > 0)) return;
    say('jobcost', near(C.posted, row ? row.cost : 0), `${p.project.name}: jobCost posted ${C.posted}`, `P&L by project ${row ? row.cost : 0}`);
    say('jobcost', near(r2(C.posted + C.notPosted), J.actual), `${p.project.name}: posted ${C.posted} + not yet posted ${C.notPosted}`, `the job's ${J.actual}`);
    say('jobcost', near(C.parts.reduce((a, x) => a + x.amt, 0), C.posted), `${p.project.name}: parts ${C.parts.map(x => x.id + ' ' + x.amt).join(', ')}`, `sum to ${C.posted}`);
    say('jobcost', Math.abs(C.notPosted) < 0.005 || !!C.notPostedLabel, `${p.project.name}: ${C.notPosted} not yet posted`, 'a labelled line');
  });
  const T = jobCostTie(['2026-01-01', today()]), P = companyPL(['2026-01-01', today()]);
  say('jobcost', near(T.posted + T.noJob, P.cogsT) && near(T.diff, r2(T.noJob - T.notPosted)), `jobs posted ${T.posted} + no job ${T.noJob}; jobs' own ${T.jobs}`, `the P&L's job cost ${P.cogsT}; the gap is ${r2(T.noJob - T.notPosted)}: ${T.why}`);
  return out;"""

# the same, on a fresh page: one billed-ahead, one to-bill, the bank change's date, the close
INV_MONEY2_JS = """
  const out = { ahead: [], tobill: [], bankdate: [], close: [] };
  const say = (k, ok, seen, want) => out[k].push([!!ok, String(seen).slice(0, 400), String(want).slice(0, 200)]);
  const strip = h => String(h || '').replace(/<[^>]+>/g, ' ').replace(/\\s+/g, ' ');
  const money_ = s => +String(s).replace(/[$,]/g, '');
  const rtb = readyToBill(), F = analystFindings();
  if (typeof billedAhead !== 'function') window.billedAhead = () => ({ total: NaN });
  if (typeof toBill !== 'function') window.toBill = () => ({ total: NaN, ready: NaN, held: NaN, rows: [], heldRows: [] });
  if (typeof wipAtClose !== 'function') window.wipAtClose = (ym) => { const P = fin2WipPlan(ym); return { toPost: P.toPost, rows: P.rows.map(r => ({ p: r.p, schedule: r2(r.over - r.under) })) }; };
  // 3. Billed Ahead of the Work: the lines' own billed less measured value, above zero (from pgRows, not pbAhead)
  DB.projects.forEach(p => {
    let rows = []; try { rows = pgRows(p.id) || []; } catch (e) {}
    const A = typeof pbAhead === 'function' ? pbAhead(p.id) : { lines: [], total: 0 };
    const lines = A.lines || [];
    const sum = r2(lines.reduce((a, l) => a + r2((+l.scheduled || 0) * (+l.net || 0) / 100), 0));
    const one = typeof billedAhead === 'function' ? billedAhead(p.id).total : null;
    if (!lines.length && !one) return;
    say('ahead', one != null && Math.abs(one - sum) < 0.02, `${p.project.name}: billedAhead ${one}`, `the ${lines.length} lines above zero add to ${sum}`);
    // every row, held row and finding that names billing ahead on this job prints that figure, and no net variant
    const texts = rtb.rows.concat(rtb.held).filter(r => r.p && r.p.id === p.id).map(r => strip(r.why) + ' ' + strip(r.title))
      .concat(F.filter(f => (f.title || '').includes(shortName(p))).map(f => strip(f.title) + ' ' + strip(f.detail)));
    texts.forEach(t => {
      if (!/billed ahead/i.test(t)) return;
      const bad = /\\bnet \\$[\\d,]+/i.test(t);
      const figs = [...t.matchAll(/Billed Ahead of the Work \\$([\\d,]+)/g)].map(m => money_(m[1]));
      say('ahead', !bad && figs.every(v => Math.abs(v - Math.round(sum)) <= 1), `${p.project.name}: "${t.slice(0, 220)}"`, `Billed Ahead of the Work ${Math.round(sum)}, no net figure`);
    });
  });
  // 4. to bill: every finding that tells someone to bill names the job's or the line's to-bill figure
  F.forEach(f => {
    const t = strip(f.title) + '. ' + strip(f.detail);
    t.split(/[;.]/).forEach(part => {
      if (!/\\bbill (it|them)\\b|\\bto bill\\b/i.test(part) || /ready to bill/i.test(part)) return;
      const m = part.match(/\\$([\\d,]+)/); if (!m) return;
      const v = money_(m[1]);
      const pid = (DB.projects.find(p => t.includes(shortName(p)) || t.includes(p.project.name)) || {}).id;
      const figs = pid ? [toBill(pid).total, toBill(pid).ready, toBill(pid).held].concat(toBill(pid).rows.concat(toBill(pid).heldRows).map(r => r.amount)) : [];
      say('tobill', figs.some(x => Math.abs(Math.round(x) - v) <= 1), `${f.area}: "${part.trim().slice(0, 200)}"`, `one of the to-bill figures ${figs.map(x => Math.round(x)).join(', ') || '(no job)'}`);
    });
  });
  // 5. one event, one date: a bank-detail change reads as its own record's date wherever it is named
  const vs = (DB.vendors || []).filter(v => v.bankChangedAt);
  const surfaces = [];
  for (const v of ['verify', 'bank', 'home', 'ap']) { try { view = v; render(); await sleep(150); surfaces.push([v, document.querySelector('.view.on') ? document.querySelector('.view.on').innerText : '']); } catch (e) {} }
  surfaces.push(['analyst', F.map(f => strip(f.title) + '. ' + strip(f.detail)).join('\\n')]);
  try { const pays = (typeof verifyAll === 'function' ? verifyAll() : null); } catch (e) {}
  vs.forEach(v => surfaces.forEach(([w, t]) => t.split('\\n').forEach(line => {
    if (!line.includes(v.name) || !/bank(ing)? (details )?changed|changed its bank/i.test(line)) return;
    say('bankdate', line.includes(fmt(v.bankChangedAt)) && !/\\b\\d+ days? ago\\b/.test(line), `${w}: "${line.trim().slice(0, 220)}"`, `${v.name}'s change dated ${fmt(v.bankChangedAt)}, never "N days ago"`);
  })));
  // 6. what the close posts is the WIP schedule at the month end, job by job; after the close 2500/1200 equal it
  const ym = fin2CloseYm();
  if (ym) {
    const W = wipAtClose(ym);
    view = 'gl'; render(); await sleep(200);
    const gl = document.querySelector('.view.on') ? document.querySelector('.view.on').innerText : '';
    const posts = gl.split('\\n').filter(l => /posts at the|close posts/i.test(l) && /\\$[\\d,]/.test(l));
    posts.forEach(l => {
      const m = l.match(/close posts[^\\t]*\\t\\s*([\\u2212\\-]?\\$[\\d,.]+)/);
      if (!m) return;
      say('close', Math.abs(Math.abs(money_(m[1].replace(/[\\u2212\\-]/, ''))) - W.toPost) < 0.01, `Ledger bridge: "${l.trim().slice(0, 200)}"`, `the ${ym} close posts ${W.toPost}`);
    });
    say('close', posts.some(l => /close posts/i.test(l)), `Ledger bridge rows: ${posts.map(l => l.slice(0, 80)).join(' | ') || 'none'}`, `a row naming what the ${ym} close posts`);
    signIn('u_owner'); render(); await sleep(100);
    // the blockers are the close's own gate (closetie_test works them); this check is what the close posts once it runs
    const keepB = fin2CloseBlockers; fin2CloseBlockers = () => [];
    let r; try { r = fin2RunClose(ym, 'finance_xcheck: the close posts the WIP schedule'); } finally { fin2CloseBlockers = keepB; }
    if (!r.ok) say('close', false, `the close refused: ${r.why}`, 'the close runs');
    else {
      const end = fin2End(ym);
      W.rows.forEach(x => {
        const B = (a) => { const G = glBalances({ entityId: 'all', to: end, acct: a, projectId: x.p.id }); return G[a] ? G[a].bal : 0; };
        const J = jobFin(x.p, ['', end]);
        say('close', Math.abs(r2(B('2500') - B('1200')) - x.schedule) < 0.01 && Math.abs(r2((J.over || 0) - (J.under || 0)) - x.schedule) < 0.01, `${x.p.project.name}: 2500/1200 ${r2(B('2500') - B('1200'))}, schedule ${r2((J.over || 0) - (J.under || 0))}`, `${x.schedule}, as read before the close`);
      });
    }
  }
  return out;"""

# the chief of staff's review (11-03): reading never writes; a deposit has one home at the close; the old figure is gone
INV_MONEY3_JS = """
  const out = { readonly: [], closeinc: [], oldword: [] };
  const say = (k, ok, seen, want) => out[k].push([!!ok, String(seen).slice(0, 400), String(want).slice(0, 200)]);
  // 1. reading any money figure leaves the data, the audit trail included, byte for byte as it was: below the audit
  // trail's 5,000-row cap and at it (where a splice-back once dropped a real row and left a preview row)
  const reads = () => { safeToSpend(); stsSafe(); companyBalance(); cashForecast(); setAside(); jobCostTie(['2026-01-01', today()]);
    DB.projects.forEach(p => { jobCostPosted(p); billedAhead(p.id); toBill(p.id); }); wipAtClose(); wipPlanAtClose(fin2CloseYm());
    acBillNeeds(''); acApNeeds(); acBooksNeeds(); acBankReview(); acCollections(''); PRED.safeToSpend.rows(); stsWhy(); };
  for (const cap of [false, true]) {
    if (cap) { DB.audit = DB.audit || []; while (DB.audit.length < 5000) DB.audit.push({ id: 'fx' + DB.audit.length, kind: 'fixture', action: 'fill', note: 'finance_xcheck: the audit cap' }); }
    reads();   // once, so anything a first read derives (the ledger's own sync) is in place
    const before = JSON.stringify(DB);
    reads();
    const after = JSON.stringify(DB);
    let at = -1; if (before !== after) { at = [...before].findIndex((ch, i) => ch !== after[i]); }
    say('readonly', before === after, `${cap ? 'at' : 'below'} the audit cap (${DB.audit.length} rows): ${before === after ? 'unchanged' : 'changed near ' + before.slice(Math.max(0, at - 80), at + 80)}`, 'the data byte for byte as it was');
  }
  // 2. after a close, ledger income by job equals the management view (one home for a deposit: 140 Prospect's $24,000
  // retainer sits in 2400; the close never posts it again into 2500)
  appSetDay('2026-10-02'); signIn('u_owner'); render(); await sleep(150);
  const keepB = fin2CloseBlockers; fin2CloseBlockers = () => [];
  const runs = [];
  try { for (const ym of ['2026-08', '2026-09']) { const r = fin2RunClose(ym, 'finance_xcheck: a deposit has one home at the close'); runs.push([ym, r.ok, r.why || '']); } }
  finally { fin2CloseBlockers = keepB; }
  say('closeinc', runs.every(x => x[1]), `the August and September closes: ${JSON.stringify(runs)}`, 'both run');
  const end = '2026-09-30', T = {}; glAccounts().forEach(a => T[a.id] = a.type);
  const S = rpPL(['2026-01-01', end]);
  DB.projects.forEach(p => {
    const led = r2(glLines({ entityId: 'all', projectId: p.id, to: end }).filter(l => T[l.acct] === 'revenue').reduce((a, l) => a + (+l.cr || 0) - (+l.dr || 0), 0));
    const row = (S.rows || []).find(x => x.id === p.id), mg = r2(row ? row.income : 0);
    if (!led && !mg) return;
    say('closeinc', Math.abs(led - mg) < 1, `${p.project.name}: ledger income ${led}`, `the management view's ${mg}`);
  });
  // 3. the old Safe to Spend wording and figure are gone from every screen and Ask answer that names cash
  appSetDay('2026-09-03'); render(); await sleep(100);
  const OLD = /Truly ours =|billed ahead of work \\$|over-billed \\(WIP, cost-to-cost: client money|lower of truly ours|[\\u2212-]\\$4,151\\b|[\\u2212-]\\$4,150\\.74/;
  for (const u of ['u_owner', 'u_controller']) {
    signIn(u); render(); await sleep(100);
    for (const v of ['home', 'dashboard', 'bank', 'ap', 'gl', 'billing', 'reports']) {
      try { setView(v); await sleep(200); } catch (e) { continue; }
      const t = (document.querySelector('.view.on') || {}).innerText || '';
      const m = t.match(OLD);
      say('oldword', !m, `${u} ${v}: ${m ? '"' + t.slice(Math.max(0, m.index - 80), m.index + 80) + '"' : 'clear'}`, 'no old Safe to Spend wording or figure');
    }
    for (const q of ['how much is safe to spend', 'what is our cash position', 'how much cash do we have', 'what is our runway']) {
      let a = ''; try { const r = await paAsk(q); a = typeof r === 'string' ? r : JSON.stringify(r); } catch (e) { a = String(e); }
      const m = a.match(OLD);
      say('oldword', !m, `${u} Ask "${q}": ${m ? a.slice(Math.max(0, m.index - 80), m.index + 80) : 'clear'}`, 'no old Safe to Spend wording or figure');
    }
  }
  return out;"""

async def check_money(p, R):
    """BACKLOG §1.35: one figure per question, recomputed from the records, the same everywhere."""
    keys = ['inv_safe', 'inv_jobcost', 'inv_ahead', 'inv_tobill', 'inv_bankdate', 'inv_close', 'inv_readonly', 'inv_closeinc', 'inv_oldword']
    if not any(R.want(k) for k in keys): return
    js = lambda body: "async () => { const sleep = ms => new Promise(r => setTimeout(r, ms)); try { " + body + " } catch (e) { return { error: String(e && e.stack || e) }; } }"
    for body in (INV_MONEY_JS, INV_MONEY2_JS, INV_MONEY3_JS):
        b, pg, errs = await open_app(p)
        await sign_in(pg, 'u_controller')
        res = await pg.evaluate(js(body))
        if 'error' in res:
            R.flag('inv_safe', 'the money invariants could not run', res['error'][:300], 'they run'); await b.close(); continue
        for k, rows in res.items():
            if not isinstance(rows, list): continue
            key = 'inv_' + k
            if not R.want(key): continue
            if not rows and k in ('ahead', 'close', 'safe', 'jobcost', 'readonly', 'closeinc', 'oldword'):
                R.flag(key, 'nothing read', 'no rows', 'at least one reading'); continue
            for ok, seen, want in rows:
                R.readings.append({'figure': key, 'surface': seen[:120], 'raw': seen, 'value': None, 'expected': want, 'ok': ok})
                if not ok: R.flag(key, 'records', seen, want)
                elif R.verbose: print('  ok', label(key), '|', seen[:140])
        if 'safeNow' in res and R.want('safe') and abs(res['safeNow'] - PINNED['safe']) > 1:
            R.flag('safe', 'safeToSpend() on the seed', res['safeNow'], PINNED['safe'])
        for e in errs[:3]: R.flag('inv_safe', 'page', e[:200], 'no page errors')
        await b.close()

# ---- the Reports pages (the Reports lane, 11-04): every figure read off the page equals its twin --------------------
INV_REPORTS_JS = """
  const out = { rptwin: [], rptie: [], rpwip: [], rpread: [] };
  const say = (k, ok, seen, want) => out[k].push([!!ok, String(seen).slice(0, 400), String(want).slice(0, 200)]);
  const num = s => { s = String(s || '').trim(); const m = s.match(/\\$([\\d,]+(?:\\.\\d+)?)/); if (!m) return null; const v = +m[1].replace(/,/g, ''); return /^[\\u2212-]/.test(s) ? -v : v; };
  const near = (a, b, t) => a != null && b != null && Math.abs(a - b) <= (t == null ? 0.005 : t);
  const F = () => document.querySelector('.view.on > .rw-front');
  const open = async (pg, chip) => { if (typeof rwGo !== 'function') return null; rwGo(pg); setView('reports'); await sleep(150); if (chip) { const [g, k] = chip.split(':'); rwChipGo(g, k); await sleep(120); } return F(); };
  const val = (root, sel) => root ? num((root.querySelector(sel) || {}).textContent) : null;
  const page = async v => { setView(v); await sleep(200); return (document.querySelector('.view.on') || {}).innerText || ''; };
  // ---- reading never writes, measured on the very first read (no warm-up: a first read that writes is a write). The
  // boot's own jobs settle first (the improvement loop's first run stamps company.loopLast), from a page that is not a
  // report; then every Reports page and chip (the old tabs where there are no pages), then the August Pack
  for (let i = 0; i < 40 && !(DB.company || {}).loopLast; i++) await sleep(200);
  setView('team'); await sleep(400);
  const OLD = ['company', 'financials', 'budget', 'pack', 'tieout', 'portfolio', 'profit', 'wip', 'ar', 'payables', 'cash13', 'flash', 'searches', 'statement', 'costintel', 'submittals', 'dlsum', 'progvp', 'studio', 'library', 'analyst'];
  const first = JSON.stringify(DB);
  if (typeof rwGo === 'function') {
    for (const pg of ['jobs', 'cash', 'stmt', 'builder']) { rwGo(pg); setView('reports'); await sleep(60);
      for (const b of [...document.querySelectorAll('.view.on > .rw-front [data-rwchip]')].map(b => b.dataset.rwchip)) { if (/^(page|builder:pinned)/.test(b)) continue; const [g, k] = b.split(':'); rwChipGo(g, k); await sleep(40); } }
    rwGo('stmt'); setView('reports'); rwChipGo('per', 'last'); await sleep(60); (document.querySelector('.view.on [data-rwpack]') || { click() {} }).click(); await sleep(150);
    rwChipGo('per', 'ytd'); await sleep(40);
  }
  for (const t of OLD) { repTab = t; view = 'reports'; render(); await sleep(40); }
  const second = JSON.stringify(DB);
  let at = -1; if (first !== second) at = [...first].findIndex((ch, i) => ch !== second[i]);
  say('rpread', first === second, first === second ? 'the first read of every page, chip and old tab: unchanged' : 'the first read changed the data near ' + first.slice(Math.max(0, at - 100), at + 100), 'the data byte for byte as it was');
  // ---- Ask's as-of figures never read the Reports period: each answer is the same whichever period a person picked,
  // and the over-billed headline is its own rows' sum (it read $90,787 beside rows adding to $156,274 after This Week)
  const QS = ['how much are we over-billed', 'how much is safe to spend', 'how much cash do we have', 'what is our AR'];
  const ask = async () => { const o = {}; for (const q of QS) { const r = await paAsk(q); o[q] = (r && r.headline) || ''; if (/over-billed/.test(q)) o.rows = r2(DB.projects.reduce((a, p) => a + Math.max(0, jobFin(p).over || 0), 0)); } return o; };
  const keepREP = JSON.stringify(REP);
  const base = await ask();
  const ob = num((base[QS[0]].match(/\\$[\\d,]+/) || [''])[0]);
  say('rptwin', near(ob, Math.round(base.rows), 0.5), `Ask "${QS[0]}": ${base[QS[0]].slice(0, 80)}`, `its rows add to ${base.rows}`);
  const weekStart = (() => { const d = parse(today()); return iso(addDays(d, -((d.getDay() + 6) % 7))); })();
  for (const [per, set] of [['week', () => { REP.preset = 'custom'; REP.from = weekStart; REP.to = today(); }], ['last', () => { REP.preset = 'lm'; }], ['month', () => { REP.preset = 'tm'; }], ['ytd', () => { REP.preset = 'ty'; }]]) {
    if (typeof rwGo === 'function') { rwGo('stmt'); setView('reports'); await sleep(60); rwChipGo('per', per); await sleep(80); }
    else { set(); repTab = 'company'; view = 'reports'; render(); await sleep(80); }
    const A = await ask();
    QS.forEach(q => say('rptwin', A[q] === base[q], `period ${per}: Ask "${q}": ${A[q].slice(0, 90)}`, `the same as before any period was picked: ${base[q].slice(0, 90)}`));
  }
  Object.assign(REP, JSON.parse(keepREP)); setView('home'); await sleep(60);
  // the WIP Schedule (the named standard report for the bank and the surety): each row's % complete follows from the
  // figures it prints, or its note names what the cost-to-cost basis leaves out (the review: 121 State at 25% beside
  // $105,084 of $388,888, which is 27%)
  view = 'reports'; repTab = 'wip'; render(); await sleep(200);
  const wsched = (document.getElementById('rep-print-area') || {}).innerText || '';
  const T = document.querySelector('#rep-print-area table.wip');
  // the schedule's rows: job, contract, cost to date, % complete over its cost basis %, earned; the projected cost is
  // the Margin view's (jobFin's eac, the same job). A cost basis that is not cost to date over it is named in the note.
  [...(T ? T.tBodies[0].rows : [])].forEach(tr => {
    const c = [...tr.cells].map(x => x.innerText.trim()), name = (c[0] || '').split('\\n')[0];
    const p = DB.projects.find(x => x.project.name === name); if (!p || /^Total/.test(name)) return;
    const J = jobFin(p), con = num(c[1]), cost = num(c[2]), earned = num(c[4]), bm = (c[3] || '').match(/([\\d.]+)% cost basis/);
    if (!(J.eac > 0) || con == null || !bm) return;
    const pct = parseFloat(bm[1]), at = wsched.indexOf(name + ': '), seg = at < 0 ? '' : wsched.slice(at, at + 300).split(/[;)]/)[0];
    const m = seg.match(/ is (\\$[\\d,]+) of (\\$[\\d,]+), ([\\d.]+)%/);
    const basis = m ? num(m[1]) : cost, why = m ? `the note: ${m[0]}` : `${c[2]} cost to date of ${money(J.eac)} projected`;
    say('rpwip', Math.abs(Math.round(100 * basis / J.eac) - pct) < 0.5 && near(earned, con * basis / J.eac, 3), `WIP Schedule ${name}: ${pct}% cost basis, earned ${c[4]}, on ${why}`, `the cost basis % and earned follow from the printed cost (${Math.round(100 * basis / J.eac)}%)`);
  });

  if (typeof rwGo !== 'function') { ['rptwin', 'rptie'].forEach(k => say(k, false, 'no Reports pages (rwGo)', 'the four Reports pages')); return out; }
  // ---- twins
  const X = safeToSpend(), B = X.B;
  let f = await open('cash');
  const safe = f && (f.querySelector('[data-rwfig=safe]') || {}).textContent;
  say('rptwin', safe && near(num(safe), Math.round(X.safe), 0) && near(num(safe), Math.round(PRED.safeToSpend.figure()), 0), `Cash: Safe to Spend ${safe}`, `safeToSpend ${X.safe}, Today's Pulse ${PRED.safeToSpend.figure()}, whole dollars`);
  const bank = val(f, '.rw-parts [data-k=bank] .rw-lv'), pay = val(f, '.rw-parts [data-k=payroll] .rw-lv'), sa = val(f, '.rw-parts [data-k=setaside] .rw-lv');
  const acc = r2((typeof acAccounts === 'function' ? acAccounts() : []).filter(x => x.a.type === 'bank').reduce((a, x) => a + x.bal, 0));
  say('rptwin', near(bank, acc) && near(bank, B.cash), `Cash: in the bank ${bank}`, `Banking's Accounts card ${acc}, companyBalance ${B.cash}`);
  const ap = (typeof acApNeeds === 'function' ? acApNeeds() : []).filter(x => x.kind === 'payroll').map(x => num((x.title.match(/\\$[\\d,.]+/) || [''])[0]));
  say('rptwin', near(-pay, B.payrollAccrued) && ap.some(v => near(v, B.payrollAccrued, 0.5)), `Cash: payroll due ${pay}`, `Bills and Payroll's payroll row ${ap.join(', ')}, payroll accrued ${B.payrollAccrued}`);
  say('rptwin', near(-sa, setAside().total), `Cash: set aside ${sa}`, `setAside ${setAside().total}`);
  f = await open('cash', 'cash:ar');
  const ar = val(f, '[data-k=artotal] .rw-lv');
  const bt = await page('billing');
  const aging = [...bt.matchAll(/(?:Current|1 to 30 Days|31 to 60 Days|Over 60 Days)\\s*\\n\\s*(\\$[\\d,]+(?:\\.\\d+)?)/g)].reduce((a, m) => a + num(m[1]), 0);
  say('rptwin', near(ar, acCollections('').open) && near(ar, aging, 0.5), `Cash, Receivables: open ${ar}`, `Billing's Collections ${acCollections('').open} (its aging on screen ${aging})`);
  // the jobs: cost to date is the job's own (jobCostPosted), the WIP over and billed ahead are the job's
  f = await open('jobs');
  for (const c of [...(f ? f.querySelectorAll('.rw-job[data-rwjob]:not([data-rwjob=""])') : [])]) {
    const p = DB.projects.find(x => x.id === c.dataset.rwjob), C = jobCostPosted(p), got = val(c, '[data-k=cost] b');
    say('rptwin', near(got, Math.round(C.onJob), 0.5) && near(C.onJob, jobFin(p).actual), `Job Profitability ${p.project.name}: cost to date ${got}`, `jobCostPosted ${C.onJob} (posted ${C.posted} + not yet posted ${C.notPosted})`);
  }
  f = await open('jobs', 'jobs:wip');
  const all = f && f.querySelector('.rw-alljobs');
  say('rptwin', all && near(num((all.querySelector('.rw-jv') || {}).textContent), Math.round(B.wip), 0.5), `Job Profitability, Work in Progress: all jobs ${(all && all.querySelector('.rw-jv') || {}).textContent}`, `Over-Billed (WIP) ${B.wip}`);
  const W = typeof wipAtClose === 'function' ? wipAtClose() : null;
  const posts = val(f, '[data-k=posts] b');
  W && say('rptwin', near(posts, W.toPost, 0.5), `Job Profitability, Work in Progress: the ${W.label} close posts ${posts}`, `wipAtClose ${W.toPost}, Books' close row`);
  for (const c of [...(f ? f.querySelectorAll('.rw-job[data-rwjob]:not([data-rwjob=""])') : [])]) {
    const id = c.dataset.rwjob, A = billedAhead(id), J = jobFin(DB.projects.find(x => x.id === id));
    if (A.total > 0.005) say('rptwin', near(val(c, '[data-k=ahead] b'), A.total, 0.5), `${id}: Billed Ahead ${(c.querySelector('[data-k=ahead] b') || {}).textContent}`, `billedAhead ${A.total}`);
    if (J.contract) say('rptwin', near(val(c, '[data-k=over] b'), J.over > 0.005 ? J.over : J.under, 0.5), `${id}: ${(c.querySelector('[data-k=over] span') || {}).textContent} ${(c.querySelector('[data-k=over] b') || {}).textContent}`, `jobFin ${J.over || J.under}`);
  }
  // the closing figure on Books and on Financial Statements
  if (W && (ROLE_VIEWS[role()] || []).includes('gl')) {
    acChip.gl = 'close'; glTab = 'periods'; await page('gl');
    const bk = (document.querySelector('.view.on .ac-front [aria-label="Posts at the close"] .ac-amt b') || {}).textContent;
    say('rptwin', near(num(bk), W.toPost, 0.5) && near(posts, num(bk), 0.5), `Books' close row ${bk}`, `Job Profitability ${posts}, wipAtClose ${W.toPost}`);
  }
  // the management net: Financial Statements' P&L and Books' ledger bridge
  f = await open('stmt', 'per:ytd'); rwChipGo('kind', 'pl'); await sleep(120); f = F();
  const net = val(f, '.rw-stmt [data-k=net] .rw-lv');
  say('rptwin', near(net, Math.round(companyPL(['2026-01-01', today()]).net), 0.5), `Financial Statements: net ${net}`, `companyPL ${companyPL(['2026-01-01', today()]).net}`);
  if ((ROLE_VIEWS[role()] || []).includes('gl')) {
    acChip.gl = 'ledger'; glTab = 'overview'; const gt = await page('gl');
    const m = gt.match(/Net income in the management view[^\\t\\n]*\\t\\s*([\\u2212-]?\\$[\\d,]+(?:\\.\\d+)?)/);
    m && say('rptwin', near(num(m[1]), net, 1), `Books' ledger bridge: management net ${m[1]}`, `Financial Statements ${net}`);
  }
  f = await open('stmt', 'per:week'); rwChipGo('kind', 'pl'); await sleep(120); f = F();
  say('rptwin', near(val(f, '.rw-stmt [data-k=safe] .rw-lv'), Math.round(X.safe), 0), `Financial Statements, This Week: Safe to Spend ${(f && f.querySelector('.rw-stmt [data-k=safe] .rw-lv') || {}).textContent}`, `Cash's ${Math.round(X.safe)}`);
  // ---- the statements tie to the ledger, to the cent
  for (const per of ['ytd', 'last', 'month']) {
    f = await open('stmt', 'per:' + per); rwChipGo('kind', 'pl'); await sleep(120); f = F();
    const R = repRangeOf().range, P = companyPL(R), C = truthCoverage(R);
    const parts = ['bank', 'document', 'hand', 'uncoded', 'other'].map(k => val(f, `.rw-behind [data-k=${k}] .rw-lv`)).filter(v => v != null);
    const sum = r2(parts.reduce((a, v) => a + v, 0)), tot = val(f, '.rw-behind [data-k=total] .rw-lv');
    say('rptie', near(sum, r2(P.cogsT + P.ohT)) && near(tot, r2(P.cogsT + P.ohT)) && near(tot, C.cost.total), `${per}: behind the numbers ${parts.join(' + ')} = ${sum}, total ${tot}`, `the P&L's cost ${r2(P.cogsT + P.ohT)} to the cent`);
    say('rptie', near(val(f, '.rw-behind [data-k=income] .rw-lv'), P.collected), `${per}: payments with a bank line ${(f.querySelector('.rw-behind [data-k=income] .rw-lv') || {}).textContent}`, `collected ${P.collected}`);
    rwChipGo('kind', 'bs'); await sleep(120); f = F();
    const S = glBS('all', R[1] > today() ? today() : R[1]), [A, L, E] = ['A', 'L', 'E'].map(k => val(f, `.rw-stmt [data-k=${k}] .rw-lv`));
    say('rptie', near(A, S.A) && near(L, S.L) && near(E, S.E) && near(A, r2(L + E)), `${per}: Balance Sheet ${A} = ${L} + ${E}`, `glBS ${S.A} = ${S.L} + ${S.E}`);
    rwChipGo('kind', 'cf'); await sleep(120); f = F();
    const end = val(f, '.rw-stmt [data-k=end] .rw-lv'), at = R[1] > today() ? today() : R[1];
    const G = glBalances({ entityId: 'all', to: at }), a1 = (DB.accounts || []).find(a => a.type === 'bank');
    say('rptie', a1 && near(end, G['acct:' + a1.id] ? G['acct:' + a1.id].bal : null), `${per}: Cash Flow ends on ${end}`, `the ledger's ${a1 && a1.name} at ${at}: ${a1 && G['acct:' + a1.id] && G['acct:' + a1.id].bal}`);
  }
  // a manual journal, drafted by the controller and posted by the owner with a reason, is listed and flagged
  const me = role() === 'owner' ? 'u_owner' : 'u_controller';
  signIn('u_controller'); setView('gl'); await sleep(150); glTab = 'entry'; glEnt = 'all'; render(); await sleep(200);
  const dt = document.getElementById('gle-date'), mm = document.getElementById('gle-memo'), rows = document.querySelectorAll('#gle-lines tbody tr');
  if (dt && mm && rows.length >= 2) {
    dt.value = '2026-08-31'; mm.value = 'finance_xcheck: a manual journal on the van';
    rows[0].querySelector('[data-l=acct]').value = '8000'; rows[0].querySelector('[data-l=dr]').value = '1200';
    rows[1].querySelector('[data-l=acct]').value = '1590'; rows[1].querySelector('[data-l=cr]').value = '1200';
    document.getElementById('gle-save').click(); await sleep(200);
    signIn('u_owner'); render(); await sleep(100);
    const j = DB.gl.journals.find(x => x.kind === 'manual' && /a manual journal on the van/.test(x.memo));
    try { mbCloseModal(); } catch (e) {}
    j && glApprove(j.id, 'finance_xcheck: straight-line on the van');
    signIn(me); render(); await sleep(100);
    for (const per of ['ytd', 'last']) {
      f = await open('stmt', 'per:' + per); rwChipGo('kind', 'pl'); await sleep(120); f = F();
      const M = truthManual(repRangeOf().range, { entityId: 'all' }).rows.map(m => m.j.id);
      const shown = [...(f ? f.querySelectorAll('.rw-behind [data-rwmj]') : [])].map(e => e.dataset.rwmj);
      const flagged = [...(f ? f.querySelectorAll('.rw-behind .rw-mj') : [])].map(e => e.innerText);
      say('rptie', j && j.status === 'posted' && M.includes(j.id) && M.every(id => shown.includes(id)) && flagged.some(t => /Manual/.test(t) && /van/.test(t)), `${per}: entries not from a document on the page ${shown.join(', ')} (${flagged.map(t => t.slice(0, 60)).join(' | ')})`, `every truthManual row ${M.join(', ')} flagged, the planted van journal among them`);
    }
  } else say('rptie', false, 'the journal entry form is not there', 'a manual journal to plant');
  // ---- WIP: earned follows from the page's own numbers
  f = await open('jobs', 'jobs:wip');
  for (const c of [...(f ? f.querySelectorAll('.rw-job[data-rwjob]:not([data-rwjob=""])') : [])]) {
    const g = k => val(c, `[data-k=${k}] b`), pct = parseFloat(((c.querySelector('[data-k=pct] b') || {}).textContent || '').replace(/[^\\d.]/g, ''));
    const con = g('contract'), cost = g('ctc') != null ? g('ctc') : g('cost'), proj = g('proj'), earned = g('earned');
    if (earned == null) continue;
    const J = jobFin(DB.projects.find(x => x.id === c.dataset.rwjob));
    say('rpwip', proj > 0 && near(earned, con * cost / proj, 3) && near(pct, 100 * cost / proj, 0.01 + 50 / proj) && near(earned, Math.round(J.earned), 0.5), `${c.dataset.rwjob}: earned ${earned} at ${pct}% on ${cost} of ${proj}, contract ${con}`, `contract × cost ÷ projected = ${proj > 0 ? r2(con * cost / proj) : '?'}; jobFin ${J.earned}`);
  }
  rwGo('jobs'); rwChipGo('jobs', 'wip'); await sleep(150);
  const sched = (document.getElementById('rep-print-area') || {}).innerText || '';
  const pre = DB.projects.filter(p => jobFin(p).contract && (jobFin(p).prepaidNotProgress || 0) > 0.005);
  say('rpwip', pre.every(p => sched.includes(p.project.name + ': ') && /paid ahead/.test(sched)), `the WIP Schedule's note: ${(sched.match(/% complete = [^\\n]*/) || [''])[0].slice(0, 220)}`, `names the money paid ahead it leaves out for ${pre.map(p => p.project.name).join(', ')}`);
  return out;"""

async def check_reports(p, R):
    """The Reports pages (11-04): each figure read off the page equals its Accounting or job-page twin."""
    keys = ['inv_rptwin', 'inv_rptie', 'inv_rpwip', 'inv_rpread']
    if not any(R.want(k) for k in keys): return
    js = "async () => { const sleep = ms => new Promise(r => setTimeout(r, ms)); try { " + INV_REPORTS_JS + " } catch (e) { return { error: String(e && e.stack || e) }; } }"
    for uid in ('u_owner', 'u_controller'):
        b, pg, errs = await open_app(p)
        await sign_in(pg, uid)
        res = await pg.evaluate(js)
        if 'error' in res:
            R.flag('inv_rptwin', f'{uid}: the Reports invariants could not run', res['error'][:300], 'they run'); await b.close(); continue
        for k, rows in res.items():
            key = 'inv_' + k
            if not R.want(key): continue
            if not rows: R.flag(key, f'{uid}: nothing read', 'no rows', 'at least one reading'); continue
            for ok, seen, want in rows:
                R.readings.append({'figure': key, 'surface': f'{uid} · {seen[:110]}', 'raw': seen, 'value': None, 'expected': want, 'ok': ok})
                if not ok: R.flag(key, uid, seen, want)
                elif R.verbose: print('  ok', label(key), '|', uid, seen[:140])
        for e in errs[:3]: R.flag('inv_rptwin', f'{uid}: page', e[:200], 'no page errors')
        await b.close()

# ---- INV ONE EAC and INV NO CONTRACT JOB (lane F, 11-12). Read off the screens a person opens: the job's Overview tile,
# its Budget, Projects, and Ask typed into its box. Nothing here calls a figure's function to compare it with itself: the
# job's one figure (jobFin) is read once and every screen's printed text is held against it.
INV_ONEJOB_JS = r"""
  const phone = innerWidth < 600, out = [];
  const num = s => { const m = String(s == null ? '' : s).replace(/[−–]/g, '-').match(/-?\$\s?([\d,]+(?:\.\d+)?)/); return m ? +m[1].replace(/,/g, '') : NaN; };
  const pct = s => { const m = String(s == null ? '' : s).match(/(-?\d+(?:\.\d+)?)\s*%/); return m ? +m[1] : NaN; };
  for (const p of DB.projects.filter(x => !x.archived)) {
    const J = jobFin(p), nm = String(p.project.name).replace(/ —.*$/, '');
    const L = J.eacLines || [], U = J.eacUnlined || { actual: 0, committed: 0, total: 0, rows: [] }, rb = (J.byCode || []).find(x => x.code === 'RB') || {};
    const o = { id: p.id, job: nm, contract: J.contract, eac: J.eac, gp: J.estGPPct, actual: J.actual, committed: J.committed, lines: L.length,
      reviewed: !!p.ctcReviewed, unlined: U.total, unlinedRows: (U.rows || []).map(r => r.name),
      tieA: Math.round((L.reduce((a, x) => a + x.actual, 0) + U.actual + (+rb.actual || 0)) * 100) / 100,
      tieC: Math.round((L.reduce((a, x) => a + x.committed, 0) + U.committed + (+rb.committed || 0)) * 100) / 100,
      lineEac: Math.round(L.reduce((a, x) => a + x.eac, 0) * 100) / 100, rebill: +J.rebillCost || 0,
      codesA: Math.round((J.byCode || []).reduce((a, x) => a + (+x.actual || 0), 0) * 100) / 100,
      codesC: Math.round((J.byCode || []).reduce((a, x) => a + (+x.committed || 0), 0) * 100) / 100 };
    // the job's Overview tile
    setCurrent(p.id); view = 'dash'; if (typeof jpSub !== 'undefined') jpSub = ''; render(); await sleep(200);
    const tile = document.querySelector('.view.on [data-tl="margin"] .gl-v');
    o.tile = tile ? pct(tile.innerText) : null;
    // its Budget
    view = 'costs'; render(); await sleep(250);
    const host = document.getElementById('jp-budget');
    const mg = host && host.querySelector('#jp-margin b');
    o.budgetMargin = mg ? pct(mg.innerText) : null;
    const rows = host ? [...host.querySelectorAll('[data-jpline]')].filter(e => e.getClientRects().length) : [];
    o.rows = rows.length;
    o.rowsForecast = Math.round(rows.reduce((a, e) => a + (+e.dataset.forecast || 0), 0) * 100) / 100;
    o.rowsActual = Math.round(rows.reduce((a, e) => a + (+e.dataset.actual || 0), 0) * 100) / 100;
    o.rowsCommitted = Math.round(rows.reduce((a, e) => a + (+e.dataset.committed || 0), 0) * 100) / 100;
    // each row as printed: Forecast is never under Actual + Committed on the same row
    o.rowBad = rows.filter(e => (+e.dataset.forecast || 0) + 0.5 < (+e.dataset.actual || 0) + (+e.dataset.committed || 0)).map(e => e.dataset.jpline);
    const tot = host && host.querySelector('#jp-eac');
    o.totalForecast = tot ? num(tot.innerText) : null;
    const nl = rows.find(e => e.dataset.jpline === '__noline');
    o.noline = nl ? Math.round(((+nl.dataset.actual || 0) + (+nl.dataset.committed || 0)) * 100) / 100 : 0;
    // Projects
    if (!phone) {
      view = 'ovjobs'; render(); await sleep(250);
      const v = document.getElementById('v-ovjobs') || document.querySelector('.view.on');
      const ths = [...v.querySelectorAll('.dg-t thead th')].map(t => t.innerText.trim().toUpperCase());
      const tr = v.querySelector(`.dg-t tr[data-edit="ov:jobs:${p.id}"]`) || [...v.querySelectorAll('.dg-t tbody tr')].find(r => r.innerText.includes(nm));
      const cell = k => { const i = ths.indexOf(k); return tr && i > -1 ? tr.children[i].innerText.replace(/\s+/g, ' ').trim() : null; };
      o.pjContract = cell('CONTRACT'); o.pjEac = cell('EAC'); o.pjBilled = cell('BILLED');
    }
    out.push(o);
  }
  return out;
"""
INV_NOCONTRACT_JS = r"""
  // an invented hour on the job with no contract: 4 h clocked today by the first crew member on its team
  const p = DB.projects.find(x => !jobFin(x).contract && !x.archived);
  if (!p) return { none: true };
  const emp = DB.employees.find(e => /Alberto/.test(e.name)) || DB.employees[0];
  const read = async () => { view = 'ovjobs'; render(); await sleep(250);
    const v = document.getElementById('v-ovjobs') || document.querySelector('.view.on');
    const ths = [...v.querySelectorAll('.dg-t thead th')].map(t => t.innerText.trim().toUpperCase());
    const tr = v.querySelector(`.dg-t tr[data-edit="ov:jobs:${p.id}"]`);
    const cell = k => { const i = ths.indexOf(k); return tr && i > -1 ? tr.children[i].innerText.replace(/\s+/g, ' ').trim() : null; };
    return { contract: cell('CONTRACT'), eac: cell('EAC'), actual: jobFin(p).actual }; };
  const before = await read();
  const logged = ((DB.field && DB.field.logs) || []).filter(l => l.projectId === p.id).reduce((a, l) => a + (l.crew || []).reduce((b, c) => b + (+c.hours || 0), 0), 0);
  const day = today();
  DB.time.push({ id: 'te_xcheck_nc', empId: emp.id, date: day, in: day + 'T08:00:00', out: day + 'T12:00:00', breakMin: 0, projectId: p.id, code: '02', notes: '', status: 'approved', approvedBy: 'Alan', source: 'test', work: [{ projectId: p.id, code: '02', hours: 4, note: '' }] });
  const after = await read();
  DB.time = DB.time.filter(e => e.id !== 'te_xcheck_nc');
  return { job: p.project.name, before, after, logged, rate: laborRate(emp) };
"""
async def check_onejob(p, R):
    if not (R.want('inv_oneeac') or R.want('inv_nocontract')): return
    js = lambda body: "async () => { const sleep = ms => new Promise(r => setTimeout(r, ms)); try { " + body + " } catch (e) { return { error: String(e && e.stack || e) }; } }"
    def read(key, surface, ok, seen, expected):
        if not R.want(key): return
        R.readings.append({'figure': key, 'surface': surface, 'raw': str(seen)[:300], 'value': None, 'expected': expected, 'ok': bool(ok)})
        if not ok: R.flag(key, surface, str(seen)[:400], expected)
        elif R.verbose: print('  ok', label(key), '|', surface, '|', str(seen)[:100])
    money0 = lambda v: '${:,.0f}'.format(round(v + 1e-9))
    for uid, phone in (('u_alan', False), ('u_owner', False), ('u_alan', True)):
        b, pg, errs = await open_app(p, phone)
        await sign_in(pg, uid)
        who = uid + (' phone' if phone else '')
        res = await pg.evaluate(js(INV_ONEJOB_JS))
        if isinstance(res, dict) and 'error' in res:
            R.flag('inv_oneeac', f'{who}: the one-job check could not run', res['error'][:300], 'it runs'); await b.close(); continue
        read('inv_oneeac', f'{who}: the instrument reads every demo job', len(res) >= 4 and any(x['unlined'] > 0 for x in res) and any(x['rows'] > 5 for x in res),
             [(x['job'], x['rows'], x['unlined']) for x in res], 'four jobs, one with cost on no estimate line, the Budget rows read')
        for x in res:
            S = lambda name: f"{who} · {x['job']} · {name}"
            eac, gp = x['eac'], x['gp']
            # the records: the lines, the unlined cost and what is billed back are the job's cost and committed, to the cent
            if x['lines']:
                read('inv_oneeac', S('lines + cost on no estimate line + billed back = cost to date and committed'),
                     abs(x['tieA'] - x['actual']) < 0.05 and abs(x['tieC'] - x['committed']) < 0.05,
                     f"actual {x['tieA']:,.2f} of {x['actual']:,.2f}, committed {x['tieC']:,.2f} of {x['committed']:,.2f}", 'they add up')
                read('inv_oneeac', S('the cost codes add up to the job'), abs(x['codesA'] - x['actual']) < 0.05 and abs(x['codesC'] - x['committed']) < 0.05,
                     f"codes actual {x['codesA']:,.2f} of {x['actual']:,.2f}, committed {x['codesC']:,.2f} of {x['committed']:,.2f}", 'they add up')
                if not x['reviewed']:
                    want = max(x['lineEac'] + x['unlined'] + x['rebill'], x['actual'] + x['committed'])
                    read('inv_oneeac', S('EAC = each line at the greater of budget and actual + committed, plus cost on no line, plus billed back'),
                         abs(eac - want) < 0.05, f"{eac:,.2f}", f"{want:,.2f}")
            if x['contract']:
                # one margin: the Overview tile and the Budget's margin print the job's margin at completion
                read('inv_oneeac', S('Overview tile, Margin at Completion'), x['tile'] is not None and abs(x['tile'] - round(gp)) < 0.01, f"{x['tile']}%", f"{round(gp)}% ({gp}%)")
                read('inv_oneeac', S('Budget, Margin at Completion'), x['budgetMargin'] is not None and abs(x['budgetMargin'] - round(gp)) < 0.01, f"{x['budgetMargin']}%", f"{round(gp)}% ({gp}%)")
                # and it is the margin of the EAC the same screens print: (contract - EAC) / contract
                read('inv_oneeac', S('the margin printed is the margin of the EAC printed'), abs(round(100 * (x['contract'] - eac) / x['contract'] * 100) / 100 - gp) < 0.011 or x['rebill'] > 0,
                     f"{gp}%", f"(contract {x['contract']:,.0f} - EAC {eac:,.0f}) / contract")
            if x['rows']:
                read('inv_oneeac', S("Budget rows' Forecast add up to the EAC"), abs(x['rowsForecast'] - eac) < 0.5, f"{x['rowsForecast']:,.2f}", f"{eac:,.2f}")
                read('inv_oneeac', S("Budget rows' Actual and Committed add up to the job's"), abs(x['rowsActual'] - x['actual']) < 0.05 and abs(x['rowsCommitted'] - x['committed']) < 0.05,
                     f"actual {x['rowsActual']:,.2f}, committed {x['rowsCommitted']:,.2f}", f"{x['actual']:,.2f} and {x['committed']:,.2f}")
                read('inv_oneeac', S('no Budget row forecasts less than its own actual + committed'), not x['rowBad'], x['rowBad'], 'none')
                read('inv_oneeac', S('Not on an Estimate Line is the cost the EAC adds'), abs(x['noline'] - x['unlined']) < 0.5 or x['reviewed'], f"{x['noline']:,.2f}", f"{x['unlined']:,.2f}")
                if not phone:
                    read('inv_oneeac', S('Budget table, Total row Forecast'), x['totalForecast'] is not None and abs(x['totalForecast'] - round(eac)) <= 1, x['totalForecast'], money0(eac))
            if not phone and x['contract']:
                read('inv_oneeac', S('Projects, EAC'), x['pjEac'] == money0(eac), x['pjEac'], money0(eac))
            if not phone and not x['contract']:
                read('inv_nocontract', S('Projects, Contract'), 'No contract yet' in (x['pjContract'] or ''), x['pjContract'], 'No contract yet')
                read('inv_nocontract', S('Projects, the cost'), bool(re.search(r'\$[\d,]+', x['pjEac'] or '')) and money0(x['actual'] + x['committed']) in (x['pjEac'] or ''), x['pjEac'], money0(x['actual'] + x['committed']) + ', never blank')
        # Ask, typed into its box, for each job with a contract
        if not phone and R.want('inv_oneeac'):
            for x in res:
                if not x['contract']: continue
                a = await ask(pg, f"what is the EAC on {x['job']}")
                m = re.search(r'Estimate at completion on .*? is ' + MONEY, a or '')
                read('inv_oneeac', f"{who} · {x['job']} · Ask, EAC", bool(m) and abs(parse_money(m.group(1))[0] - round(x['eac'])) <= 1, (a or 'no answer')[:120], money0(x['eac']))
                m = re.search(r'(-?\d+(?:\.\d+)?)% margin at completion', a or '')
                read('inv_oneeac', f"{who} · {x['job']} · Ask, margin at completion", bool(m) and abs(float(m.group(1)) - x['gp']) < 0.011, (m.group(0) if m else (a or 'no answer')[:160]), f"{x['gp']}%")
                a = await ask(pg, f"what is the margin on {x['job']}")
                m = re.match(r'\s*(-?\d+(?:\.\d+)?)% estimated gross margin', a or '')
                read('inv_oneeac', f"{who} · {x['job']} · Ask, margin", bool(m) and abs(float(m.group(1)) - x['gp']) < 0.011, (a or 'no answer')[:120], f"{x['gp']}% estimated gross margin")
        # the job with no contract: an hour clocked to it is cost on its row; hours on its logs with no time entry are named
        if not phone and uid == 'u_alan' and R.want('inv_nocontract'):
            nc = await pg.evaluate(js(INV_NOCONTRACT_JS))
            if nc.get('error') or nc.get('none'):
                R.flag('inv_nocontract', f'{who}: the job with no contract', str(nc)[:300], 'a demo job with no contract is read')
            else:
                want = round(4 * nc['rate'] * 100) / 100
                got = nc['after']['actual'] - nc['before']['actual']
                read('inv_nocontract', f"{who} · {nc['job']} · 4 h clocked to the job is its cost", abs(got - want) < 0.5 and money0(nc['after']['actual']) in (nc['after']['eac'] or ''),
                     f"cost {nc['before']['actual']:,.2f} -> {nc['after']['actual']:,.2f}; Projects reads {nc['after']['eac']}", f"+{want:,.2f}, on the row")
                if nc['logged'] > 0:
                    read('inv_nocontract', f"{who} · {nc['job']} · hours on its daily logs that no time entry carries are named", re.search(r'[\d.]+ h on daily logs, not clocked', nc['before']['eac'] or '') is not None,
                         nc['before']['eac'], f"{nc['logged']:g} h on daily logs, not clocked")
        for e in errs[:3]: R.flag('inv_oneeac', f'{who}: page', e[:200], 'no page errors')
        await b.close()

async def check_invariants(p, R):
    if not R.want('inv_dep'): return
    def read(key, surface, ok, seen, expected):
        R.readings.append({'figure': key, 'surface': surface, 'raw': str(seen)[:300], 'value': None, 'expected': expected, 'ok': ok})
        if not ok: R.flag(key, surface, str(seen)[:600], expected)
        elif R.verbose: print('  ok', label(key), '|', surface)
    async def page():
        b, pg, errs = await open_app(p)
        await sign_in(pg, 'u_owner')
        await pg.evaluate("async () => { if (typeof ljDemoSwitch === 'function') { await ljDemoSwitch(true); await new Promise(r => setTimeout(r, 200)); } }")
        return b, pg, errs
    js = lambda body: "async () => { const sleep = ms => new Promise(r => setTimeout(r, ms)); " + body + " }"

    # one answer, on the books as they stand
    b, pg, errs = await page()
    one = await pg.evaluate(js(INV_ONE_JS))
    bad = [x for x in one if not x['named']]
    read('inv_one', 'every sent invoice, as seeded', not bad, bad, 'ledger, sovBilled, lineFin, cxKind and invIsDeposit give one answer')
    # collected never exceeds what the bank backs
    bank = await pg.evaluate(js(INV_BANK_JS))
    read('inv_bank', 'each payment counted in the bank has a bank line, within its amount', not bank['bad'], bank['bad'], 'no line backs more than its amount; only lines the bank sent')
    # the instrument: the fixture's bank-sent lines back $4,321.09 once and $1,000 of the $1,500; the edited line nothing
    read('inv_bank', 'the fixture is read (one of the two equal payments, $1,000 of $1,500, nothing on the edited line)', bank['fx'][0] + bank['fx'][1] > 0 and bank['fx'][3] == 0, bank['fx'], 'some backing seen, none on the edited line')
    read('inv_bank', 'total counted in the bank', bank['backed'] <= bank['lines'] + 0.005, f"backed {bank['backed']:,.2f} of bank lines {bank['lines']:,.2f}", 'backed <= bank lines')
    # no edit to a sent or paid document changes what was posted; and after the edits, still one answer
    ed = await pg.evaluate(js(INV_EDIT_JS))
    read('inv_edit', f"retitle, retainage and a line on each of {ed['n']} sent or paid invoices", ed['n'] > 0 and not ed['moved'], ed['moved'] or ed['n'], 'posted amounts unchanged')
    one2 = await pg.evaluate(js(INV_ONE_JS))
    bad2 = [x for x in one2 if not x['named']]
    read('inv_one', 'every sent invoice, after those edits', not bad2, bad2, 'one answer, unchanged by the edits')
    for e in errs[:3]: R.flag('inv_one', 'page', e[:200], 'no page errors')
    await b.close()

    # every deposit nets to zero in 2400 once its job's applications are billed (a fresh page: the edits above are not on it)
    b, pg, errs = await page()
    dep = await pg.evaluate(js(INV_DEP_JS))
    read('inv_dep', 'deposits found', len(dep) > 0, dep, 'at least one stamped deposit (the Live Jobs demo has two)')
    for x in dep:
        ok = abs(x['held']) < 0.01 and x['open'] == 0
        read('inv_dep', f"{x['client']} {x['est']} ({', '.join(x['deposits'])}), every line billed", ok, f"2400 {x['held']:+,.2f}, {x['open']} lines open", '2400 nets to $0.00')
    for e in errs[:3]: R.flag('inv_dep', 'page', e[:200], 'no page errors')
    await b.close()

    # every approval stamp has its person's own action in the audit trail: as seeded, and after each approval path runs
    b, pg, errs = await page()
    st = await pg.evaluate(js(INV_STAMP_JS))
    read('inv_stamp', 'every approval stamp on bills, payroll, card spend, POs, change orders and payments, as seeded', not st['seeded'], st['seeded'][:6],
         'an audit row by the same person on the same record at or before each stamp')
    read('inv_stamp', f"after the PM recommends, the owner approves a bill, a payroll run and a PO ({'; '.join(st['did'])})", not st['after'] and len(st['did']) >= 2, st['after'][:6] or st['did'],
         'each new stamp written with its audit row')
    read('inv_stamp', 'the instrument: stamps were read', st['stamps'] >= 5, st['stamps'], 'the seeded trails and the new ones are found')
    for k, what in (('pba', 'WW-2026-118, paid before approval'), ('held', 'AMP-311, held')):
        s = (st.get('same') or {}).get(k) or {}
        read('inv_stamp', f'{what}: the bill page and its Approvals row', bool(s.get('ok')), s or 'not read',
             "the page's one blue button (not Approve, Pay or Release) leads the Approvals row; nothing there that approves or pays is blue")
    outside = [d for d in st['did'] if re.match(r'^(journal|change|client credit) ', d)]
    read('inv_stamp', 'the instrument: the owner posts a journal and approves a rule change, billing approves a client credit',
         any(d.startswith('journal posted') for d in outside) and any(re.match(r'change (live|approved) by', d) for d in outside) and any(d.startswith('client credit approved') for d in outside),
         outside, 'each path ran and its record names who approved')
    read('inv_stamp', 'a held bill (AMP-311 planted on hold): the PM recommends (billAction, rtApprove), the owner approves (rtApprove, billAction)',
         not st['held'] and any(d.startswith('held ') for d in st['did']), st['held'] or st['did'], 'no path stamps it, skips a review on it or moves its status')
    read('inv_stamp', 'the screen: a stamp planted on NT-88412 with no audit row, on its Approval Trail', 'no record of this action' in st['ui']['planted'].lower() and not st['ui']['clean'],
         st['ui'], 'the planted stamp reads "no record of this action"; the backed ones do not')
    for e in errs[:3]: R.flag('inv_stamp', 'page', e[:200], 'no page errors')
    await b.close()

    # the audit trail is hash-chained and append-only (a fresh page)
    b, pg, errs = await page()
    ch = await pg.evaluate(js(INV_CHAIN_JS))
    if ch.get('missing'):
        read('inv_chain', 'auditVerify', False, 'no auditVerify in this build', 'the audit trail can be verified')
    else:
        read('inv_chain', 'as seeded', ch['seeded']['ok'] and ch['seeded']['pending'] == 0, ch['seeded'], 'every row sealed and the chain verifies')
        read('inv_chain', 'after a write (sealed at the end of its turn)', ch['afterWrite']['ok'] and ch['afterWrite']['pending'] == 0, ch['afterWrite'], 'verifies')
        for key, what in (('edited', "a sealed row's note edited"), ('editedBy', "a sealed row's person changed"), ('removed', 'a row removed from the middle'), ('removedLast', 'the newest row removed')):
            v = ch[key]
            read('inv_chain', what, not v['ok'] and (key == 'removedLast' or v['at'] == ch['k']), v, f"verify fails, naming row {ch['k']}" if key != 'removedLast' else 'verify fails')
        read('inv_chain', 'put back as it was', ch['restored']['ok'], ch['restored'], 'verifies again')
        read('inv_chain', '5,100 more rows', ch['bulk']['added'] == 5100 and ch['bulk']['firstKept'] and ch['bulk']['v']['ok'], ch['bulk'], 'none dropped, the first row kept, the chain verifies')
    for e in errs[:3]: R.flag('inv_chain', 'page', e[:200], 'no page errors')
    await b.close()


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--figure', action='append', default=[], help='cash, ar, unmatched, ap, wip, backlog, net, safe, rtb, job121, ledger, stock, invariants, money, reports, onejob')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('-v', '--verbose', action='store_true')
    ap.add_argument('--role', action='append', default=[], help='owner or controller (default both)')
    a = ap.parse_args()
    figs = {f.strip() for x in a.figure for f in x.split(',') if f.strip()}
    R = Run(figs, a.verbose, quiet=a.json)
    t0 = time.time()
    roles = [{'owner': 'u_owner', 'controller': 'u_controller'}[r] for r in a.role] or ['u_owner', 'u_controller']
    async with async_playwright() as p:
        b, pg, errs = await open_app(p)
        for uid in roles:
            await check_role(pg, R, uid)
        await b.close()
        await check_stock(p, R)
        await check_invariants(p, R)
        await check_money(p, R)
        await check_reports(p, R)
        await check_onejob(p, R)
    for e in errs[:5]:
        R.flags.append({'figure': 'errors', 'surface': 'page', 'seen': e[:200], 'expected': 'no page errors'})
        if not a.json: print('FLAG ERRORS | page |', e[:200], '| no page errors')
    secs = round(time.time() - t0, 1)
    if a.json:
        print(json.dumps({'n_flags': len(R.flags), 'flags': R.flags, 'readings': R.readings, 'notes': R.notes, 'pinned': PINNED, 'seconds': secs}, indent=1, ensure_ascii=False))
    else:
        if R.notes:
            print('\nNot shown / information (not flags):')
            for n in R.notes: print(f"  {label(n['figure']) if n['figure'] != '*' else '-'} | {n['surface']} | {n['note']}")
        print(f'\n{len(R.readings)} readings · {secs}s')
        print(f'{len(R.flags)} flags')
    sys.exit(1 if R.flags else 0)

asyncio.run(main())
