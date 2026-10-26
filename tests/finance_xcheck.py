"""Finance cross-check (BACKLOG §0 item 5).

For the owner and the controller, open every surface that shows a headline money figure, read the figure off
the rendered screen (innerText, after navigating by the rail and tab buttons), parse it and compare it with
the pinned value. A surface that rounds ($184K, $2.6k) is compared within its rounding.

Each disagreement prints one line:  FIGURE | surface | value seen | expected
The run ends with `N flags` and exits 1 when N > 0.

  python3 finance_xcheck.py                 all figures, owner and controller
  python3 finance_xcheck.py --figure cash   only one figure family (cash, ar, unmatched, ap, wip, backlog,
                                            net, safe, rtb, job121, ledger, stock); repeatable or comma-separated
  python3 finance_xcheck.py --figure invariants   only the ledger invariants (below)
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
    'safe':            -4151,    # safe to spend (-$4,150.74; -$2,618.27 before truthpct)
    'rtb':             19680,    # ready to bill (lane 1, round one, 2026-10-26: TRIAGE class 2's accept, nothing proposed on a job billed ahead: 121 State's application $12,651 and the windows' stored materials, now $10,170, are held with the reason; $46,301 / 4 rows before)
                                 # (before that: $47,601 until pilotfix2 removed the seed's 6.5 designer hours dated 9/4, a day not yet worked, billed as ready; $20,980 / 2 rows before leaks)
    'rtb_n':           2,
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
                    'inv_dep': 'invariants', 'inv_bank': 'invariants', 'inv_edit': 'invariants', 'inv_one': 'invariants'}.get(
                        k, 'wip' if k.startswith('wip_job') else k)
LABEL = {'cash': 'CASH', 'ar': 'AR', 'unmatched_n': 'UNMATCHED (count)', 'unmatched_amt': 'UNMATCHED ($)',
         'ap_bills': 'AP OWED (bills)', 'ap_payroll_due': 'AP PAYROLL PAST DUE', 'ap_paid_unappr': 'AP PAID BEFORE APPROVAL', 'ap_maybe_paid': 'AP POSSIBLY ALREADY PAID',
         'wip_over': 'WIP OVER-BILLED', 'backlog': 'BACKLOG', 'net': 'NET YTD', 'income': 'INCOME YTD', 'safe': 'SAFE TO SPEND',
         'rtb': 'READY TO BILL', 'rtb_n': 'READY TO BILL (rows)', 'pct121': '121 STATE % COMPLETE', 'eac121': '121 STATE EAC',
         'drift': 'DRIFT', 'tb': 'TRIAL BALANCE', 'bridge': 'LEDGER BRIDGE', 'wiptie': 'WIP TIE 2500/1200',
         'inv_dep': 'INV DEPOSIT HELD', 'inv_bank': 'INV BANK BACKS', 'inv_edit': 'INV SENT FROZEN', 'inv_one': 'INV ONE ANSWER'}
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
    target = sub or grp
    ok = await click_js(pg, f'#nav [data-grp="{grp}"]')
    if sub and ok:
        cur = await pg.evaluate('view')
        if cur != sub: ok = await click_js(pg, f'[data-sub="{sub}"]')
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
        R.money('safe', S('Home brief › Cash sentence'), t, r'but ' + MONEY + r' short', sign=-1)
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

    # Accounting overview tiles
    if gate('ovmoney', 'Accounting overview'):
        await nav(pg, 'money', 'ovmoney'); t = await text_of(pg, 'ovmoney')
        R.count('unmatched_n', S('Accounting overview › tile "No Record Behind"'), t, r'No Record Behind\s*\n\s*(\d+)')
        R.money('unmatched_amt', S('Accounting overview › Today\'s Review'), t, r'bank lines with no receipt, bill or payroll behind them · ' + MONEY)
        for k in ('cash', 'ar', 'ap_bills', 'safe', 'wip_over', 'net'):
            R.note(k, S('Accounting overview'), 'not shown on the overview tiles')

    # Banking
    if gate('bank', 'Banking'):
        await nav(pg, 'money', 'bank'); t = await text_of(pg, 'bank')
        R.money('cash', S('Banking › tile "Cash in Bank"'), t, r'Cash in Bank\s*\n\s*' + MONEY)
        R.count('unmatched_n', S('Banking › tile "To Review"'), t, r'To Review\s*\n\s*(\d+)')
        R.money('unmatched_amt', S('Banking › tile "To Review"'), t, r'To Review\s*\n\s*\d+\s*\n\s*' + MONEY)
        R.money('ap_payroll_due', S('Banking › tile "Cash in Bank"'), t, r'Cash in Bank\s*\n[^\n]*\n[^\n]*?' + MONEY + r' past due', required=False)

    # Bills & Payroll
    if gate('ap', 'Bills & Payroll'):
        await nav(pg, 'money', 'ap'); t = await text_of(pg, 'ap')
        R.money('ap_payroll_due', S('Bills & Payroll › tile "Overdue to Pay"'), t, r'Overdue to Pay\s*\n\s*\d+\s*\n\s*' + MONEY)
        R.money('ap_paid_unappr', S('Bills & Payroll › tile "Flagged Bills"'), t, r'paid from the bank before approval \(' + MONEY + r'\)')
        # owed bills: approved and unpaid. The page counts them as "Due This Week" + overdue bills; nothing else is owed.
        R.money('ap_bills', S('Bills & Payroll › "Approved · To Pay"'), t, r'Approved bills to pay[^\n]*' + MONEY, required=False)

    # Billing
    if gate('billing', 'Billing'):
        await nav(pg, 'billing', 'billing'); t = await text_of(pg, 'billing')
        R.money('rtb', S('Billing › tile "Ready to Bill"'), t, r'Ready to Bill\s*\n\s*' + MONEY)
        R.count('rtb_n', S('Billing › tile "Ready to Bill"'), t, r'Ready to Bill\s*\n[^\n]*\n\s*(\d+) items? earned')
        R.money('ar', S('Billing › tile "Sent and Unpaid"'), t, r'Sent and Unpaid\s*\n\s*' + MONEY)

    # Ledger: Overview, Statements, Accounts, Close
    if gate('gl', 'Ledger'):
        await nav(pg, 'money', 'gl', ['#v-gl [data-gltab="overview"]']); t = await text_of(pg, 'gl')
        R.count('drift', S('Ledger › Overview tile "Drift"'), t, r'Drift(?: check)?\s*\n\s*(\d+)')
        R.count('unmatched_n', S('Ledger › Overview bridge'), t, r'(\d+) bank items? not yet matched')
        R.money('unmatched_amt', S('Ledger › Overview bridge'), t, r'bank items? not yet matched — ' + MONEY)
        R.money('net', S('Ledger › Overview bridge "Net income in the management view"'), t, r'Net income in the management view[^\t\n]*\t\s*' + MONEY)
        R.money('wip_over', S('Ledger › Overview bridge "WIP adjustment not yet posted"'), t, r'WIP over/under-billing adjustment not yet posted[^\t\n]*\t\s*' + MONEY, absval=True)
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
        # the Chief of Staff is the assistant's Findings › Every Chain now (lane assistant): 'cos' redirects to 'pa'
        await nav(pg, 'ask', 'cos'); t = await text_of(pg, 'pa')
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


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--figure', action='append', default=[], help='cash, ar, unmatched, ap, wip, backlog, net, safe, rtb, job121, ledger, stock, invariants')
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
