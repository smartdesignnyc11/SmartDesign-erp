"""Finance cross-check (BACKLOG §0 item 5).

For the owner and the controller, open every surface that shows a headline money figure, read the figure off
the rendered screen (innerText, after navigating by the rail and tab buttons), parse it and compare it with
the pinned value. A surface that rounds ($184K, $2.6k) is compared within its rounding.

Each disagreement prints one line:  FIGURE | surface | value seen | expected
The run ends with `N flags` and exits 1 when N > 0.

  python3 finance_xcheck.py                 all figures, owner and controller
  python3 finance_xcheck.py --figure cash   only one figure family (cash, ar, unmatched, ap, wip, backlog,
                                            net, safe, rtb, job121, ledger); repeatable or comma-separated
  python3 finance_xcheck.py --json          machine-readable result (flags, every reading, not-shown notes)
  python3 finance_xcheck.py -v              also print every reading that agreed
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
PINNED = {
    'cash':            184231,   # Chase Business Checking, ledger balance
    'ar':              92265,    # open invoices, ex retainage
    'unmatched_n':     16,       # bank lines not yet matched
    'unmatched_amt':   75272,
    'ap_bills':        0,        # vendor bills owed
    'ap_payroll_due':  16040,    # payroll 8/17-8/28, past due
    'ap_paid_unappr':  43300,    # paid from the bank before approval: NOT owed
    'wip_over':        156274,   # net over-billing on the WIP schedule ($156,274.27; $154,741.80 before truthpct)
    'backlog':         582941,   # contract - earned ($582,940.76; $581,408.29 before truthpct)
    'net':             -5330,    # YTD net, management view (-$5,329.88; -$3,797.41 before truthpct)
    'income':          142759,   # YTD earned revenue ($142,759.24; $144,291.71 before truthpct)
    'safe':            -4151,    # safe to spend (-$4,150.74; -$2,618.27 before truthpct)
    'rtb':             20980,    # ready to bill
    'rtb_n':           2,
    'wip_job:121 State Street':   131058,   # $131,057.72; $129,525.25 before truthpct
    'wip_job:45 Cranberry St':    2705,
    'wip_job:140 Prospect Place': 22512,
    'pct121':          14,       # 121 State % complete, one number (tpJobPct, BACKLOG §1.2)
    'eac121':          388888,   # 121 State estimate at completion ($388,887.50; $384,087.50 before truthpct)
    'drift':           0,
}
FAMILY = lambda k: {'unmatched_n': 'unmatched', 'unmatched_amt': 'unmatched', 'ap_bills': 'ap', 'ap_payroll_due': 'ap',
                    'ap_paid_unappr': 'ap', 'wip_over': 'wip', 'income': 'net', 'rtb_n': 'rtb', 'pct121': 'job121',
                    'eac121': 'job121', 'drift': 'ledger', 'tb': 'ledger', 'bridge': 'ledger', 'wiptie': 'wip'}.get(
                        k, 'wip' if k.startswith('wip_job') else k)
LABEL = {'cash': 'CASH', 'ar': 'AR', 'unmatched_n': 'UNMATCHED (count)', 'unmatched_amt': 'UNMATCHED ($)',
         'ap_bills': 'AP OWED (bills)', 'ap_payroll_due': 'AP PAYROLL PAST DUE', 'ap_paid_unappr': 'AP PAID BEFORE APPROVAL',
         'wip_over': 'WIP OVER-BILLED', 'backlog': 'BACKLOG', 'net': 'NET YTD', 'income': 'INCOME YTD', 'safe': 'SAFE TO SPEND',
         'rtb': 'READY TO BILL', 'rtb_n': 'READY TO BILL (rows)', 'pct121': '121 STATE % COMPLETE', 'eac121': '121 STATE EAC',
         'drift': 'DRIFT', 'tb': 'TRIAL BALANCE', 'bridge': 'LEDGER BRIDGE', 'wiptie': 'WIP TIE 2500/1200'}
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
    if await pg.evaluate('view') != 'pa': await nav(pg, 'ask', 'pa')
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
        R.money('wip_over', S('Projects › tile "Billed Ahead"'), t, r'Billed Ahead\s*\n\s*\+?' + MONEY)
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
        await nav(pg, 'ask', 'cos'); t = await text_of(pg, 'cos')
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

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--figure', action='append', default=[], help='cash, ar, unmatched, ap, wip, backlog, net, safe, rtb, job121, ledger')
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
