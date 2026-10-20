# Reporting audit (BACKLOG §1.13), 2026-10-20

The Reporting lane's starting point. App day 2026-09-03, demo seed, signed in as the owner. Every figure below was read
from the running build (`dist/smartdesigns_projects.html`, master at 8d3b54a) through the app's own readers and its
screens, and recomputed by hand from the records (bank lines, invoices, payments, bills, payroll, time, the GL
journals). Where the two disagree, the cause is named.

## What exists today

Reports (rail › Reports) has five groups and nineteen tabs:

| Group | Tabs |
|---|---|
| Financials | P&L Detail (`company`), Statements (`financials`), Budget vs Actual, Monthly Pack, Three-Way Tie-Out |
| Projects | All Projects, Project Profitability (`profit`), WIP Schedule, Studio, Cost Library, Submittal Log, Daily Log Summary, Progress vs Plan |
| Cash & Receivables | Receivables (`ar`), Payables, Client Statement |
| Review | Analyst, Weekly Flash |
| Build a Report | Report Builder (`searches`) |

The report bar already carries the period (this month, last month, quarter, YTD, last 12 months, all time, custom),
the comparison (prior period, same period last year, budget), the entity (consolidated or one of four) and the basis
(accrual or cash). Readers: `companyPL(range)`, `ledger(range)`, `jobFin(p, range)`, `lineFin(key)`,
`companyBalance()`, `clientFin(c)`, `apAging(asOf)`, `cashForecast()`, `ohMonth`/`ohNow`, `entityPL(range)`,
`glPL`/`glBalances`. Ask reads `EQ_TABLES.financials` (six periods), `araging`, `apaging`, `wiptie`, `closes`.

Already proven by other suites: the headline figures on every surface (`finance_xcheck.py`, 0 flags today);
bank/card coverage, manual journals flagged, append-only postings, line matching and the QuickBooks tie-out
(`truth_test.py`); the August close, late lines landing in September and the WIP tie to 2500/1200
(`closetie_test.py`).

## Item by item

### 1. Income and expenses, accrual and cash, labelled

- **Exists.** Accrual P&L: revenue earned ($142,759.24 YTD = invoiced $299,033.51 − WIP adjustment $156,274.27),
  collected ($191,100) shown beside it; expenses by category; bank/card coverage strip; manual entries listed
  ("Entries not from a document"). Cash basis toggle on the report bar.
- **Wrong: the cash basis counts payroll that has not been paid.** Cash basis YTD net is $26,970.88. It includes
  the payroll run of 8/17–8/28 ($16,040.00: Labor $1,968.28 + Unallocated Labor $14,071.72), which is *submitted*,
  not approved and not paid; no bank line pays it. The Statements' own cash flow says "Paid: payroll $0". Cause: the
  cash-basis `ledger` (app.js, the `ledgerBase_cash` wrapper) takes every run by pay date, and the accrual filter that
  drops unposted runs (`FIN_RUN_POSTED`) returns early on cash basis.
- **Unlabelled: cash-basis income is payments recorded, not money at the bank.** $191,100 collected; the bank
  received $169,750; $21,350 is undeposited (1050). Defensible (constructive receipt), but the screen does not say
  so, and the cash-basis P&L ($26,970.88) and the cash flow statement ($21,660.88 net) disagree by exactly
  +$21,350 − $16,040 with no tie shown.
- **Recomputed and agreeing:** cash-basis job cost $100,493.94 = the ten bank and card lines coded to job cost
  (t3, t4, t5, t6, t7, t8, ta7, t9, t10, ta8); overhead $47,595.18 = coded overhead lines $24,753.87 + Needs
  Category $22,841.31.

### 2. Job costing

- **Exists.** Project Profitability by cost code: contract, budget, committed, bills and bank, labor, actual,
  remaining; EAC by line (truthpct); earned, over/under, projected margin.
- **Recomputed and agreeing:** 121 State actual $97,083.95 = bills $75,750.00 + bank lines $17,943.94 + labor
  $3,390.01 + stock $0. Earned $122,625.79 = $491,200 × ($97,083.95 ÷ EAC $388,887.50).
- **Rounding:** the by-code rows sum to $97,083.96 against the job's $97,083.95 (one cent; each row rounds on its
  own). The total row must equal the job.
- **Not tied on screen:** the by-code table, the by-line table and the job total are three numbers with no tie row.

### 3. Line-item income to cost

- **Exists.** Project Profitability › By Line: contract, billed, collected, budget, committed, actual, margin.
- **Wrong: by-line actual double counts.** On 121 State the lines total $102,670 while the job and the by-code
  table say $97,084, on the same screen. Plumbing reads $19,755: bill AMP-311 ($9,800, *submitted*, not yet cost)
  plus check 2205 ($9,800, the bank line that pays it). Demolition reads $1,650 against the code's $3,300 (the
  second dumpster charge has no line). Cause: `lineFin` counts every non-void bill on the line, approved or not,
  and every bank line not linked to a bill; the job counts a bill only once it is approved or paid. The truthpct EAC
  lines (`J.eacLines`) already carry the job's own actual by line ($95,617.91 + $1,466.04 on code 12, which has no
  line = $97,083.95).
- **Missing:** earned per line, margin at completion per line, approved CO lines beside the estimate lines with one
  total, and the estimate-versus-actual view at close-out that proposes price-book changes.

### 4. P&L by company, entity, client, project, period; comparatives; the tie

- **Exists.** Company, by entity (side by side with eliminations), by project (job to date, after overhead), by
  month; comparatives (prior period, same period last year, budget).
- **Missing: P&L by client.** Ask "P&L by client" returns the client list.
- **Not shown: the tie.** The project table (Reports › All Projects, "Profit After Overhead") nets $28,395; the
  company nets −$5,330. The pieces that bridge them are on three different screens: overhead in months with no job
  cost ($15,473, a note under the table), bank lines not yet coded ($22,841, the same note), job cost on no project
  ($6,800) and the labor variance (clocked labor at burdened rates on the jobs, $11,389, against approved payroll
  $0) on Statements › Ties. $28,395 − $15,473 − $22,841 − $6,800 + $11,389 = −$5,330. It ties; nothing shows it.
- **Intercompany:** the eliminations column exists; there are no intercompany bills in the seed, so it reads $0.
  Not yet proven with one.

### 5. Overhead analysis

- **Exists.** Pool, rate this month and YTD, burden rate (three full months), absorbed against actual, each job's
  share, a six-month trend of pool and rate; allocation basis selectable.
- **Missing:** the pool by category over the months, overhead as a % of revenue per month, and the break-even
  monthly revenue. A KPI called "Break-even revenue (month)" exists in the KPI library, but it divides the
  *period's* overhead by the gross margin, so over YTD it is eight months of overhead, not a month's. Ask
  "break-even revenue" answers YTD revenue.

### 6. WIP, cash, AR/AP, backlog, retainage

- **Exists.** WIP schedule (over $156,274.27 = Σ billed gross − earned), backlog by job ($582,940.76), AR aging
  (Receivables), AP aging and retainage held from subs (Payables), client retainage ($15,668.35), a 13-week cash
  forecast (`cashForecast()`, on the Dashboard and the Brief).
- **Missing from Reports:** the 13-week cash flow has no report (print or export). Retainage receivable and payable
  are on two different tabs and never side by side.
- **Ask misses:** "13-week cash low" answers the bank balance; "retainage receivable" answers AR ($92,265, not
  $15,668); "retainage payable" answers AP $0.

### 7. Closed periods don't move

- **Exists and proven for cost** (closetie): August cost holds while August is closed; a late line is stamped into
  September (`postOn`) and lands there.
- **Wrong: the ledger and the management view disagree on closed August by $5,000.** After the month-end and the
  close, August management revenue is $129,664.77, the ledger's $124,664.77; costs agree to the cent. Cause: the
  45 Cranberry design retainer. INV-2026-D45-R ($5,000, July) posts to Customer deposits (2400), as it should. The
  August invoice INV-2026-D45-1 applies it with a "Less retainer applied" line of −$5,000, which `glInvoiceLines`
  posts as *negative revenue* (Dr 4000) instead of relieving the deposit (Dr 2400). So 2400 keeps $5,000 that was
  applied (the balance sheet shows Customer deposits $29,000; $24,000 is right), revenue is $5,000 short, and the
  WIP posting at close cannot make it up. This is a root bug in the books, not the report.
- **Not proven:** that the whole closed P&L (income, overhead, net), not only cost, shows the same figures after a
  later correction, and that the current period shows the correction with a link.

### 8. Choices for Alan and the accountant

None is surfaced as a setting: Mercer & Bond development costs (206 Lenox costs are expensed today), revenue
recognition for tax (the management view earns cost-to-cost), and the overhead allocation basis (selectable, total
direct cost by default, no note that it is a choice to settle).

### 9. Export and share

- **Exists.** Print / PDF on every tab; the Monthly Pack lays out at 390px with no sideways scroll; CSV exports for
  QuickBooks import and the budget.
- **Missing:** Excel. No report exports to .xlsx.
- **Read-only accountant access** is a platform role (hosted copy), out of this lane's single-file scope.

### 10. Compared with QuickBooks

Exists: Three-Way Tie-Out (QuickBooks says / the bank says / the ERP says, per month and account group), proven by
`truth_test.py` with a snapshot from outside the repo.

## What the checks didn't check, and why

- `finance_xcheck.py` pins headline figures; it never adds a report's rows up, so a table whose lines do not sum to
  its total (by line against by code) passes.
- No suite switches the basis; the cash-basis payroll error has been there since the toggle was added.
- `closetie_test.py` compares closed-month *cost* between ledger and management; the $5,000 is in *revenue*.
- Ask's question bank asks for headline figures, not "by client", "break-even", "13-week low" or "retainage
  payable", so the misses never surfaced.

## Plan, in priority order

1. A tie engine in `src/reports.js` (`rpTies(range)`): each report's tie computed from the records, with every part
   named and drillable, shown on the report it belongs to and all together on Statements and the Monthly Pack.
2. `tests/reports_test.py`: recompute each report from the raw records in Python, to the cent, and read the ties off
   the screen as the owner, the controller and billing, desktop and phone.
3. Root fixes: cash-basis payroll only when paid (and undeposited receipts labelled); the applied retainer relieves
   2400; by-line actual from the job's own lines.
4. P&L by client, the tie row on the project table, intercompany proven with a bill.
5. Line income to cost with earned and margin at completion; the close-out estimate-versus-actual proposing
   price-book changes.
6. Overhead by category and month, % of revenue, break-even monthly revenue; the 13-week cash flow, backlog and
   retainage both ways as one report.
7. Excel export of any report; the accounting choices as labelled settings with a default and a note.
8. Ask reads each report through EQ_TABLES with the same numbers as the screen.

## Where it stands after the lane (2026-10-20)

| Item | Built | Proven by `tests/reports_test.py` |
|---|---|---|
| 1. Income and expenses, accrual and cash | Cash basis takes payroll only once paid (root fix); the income tie shows at the bank and not yet deposited | books, cash |
| 2. Job costing | Job cost tie (bills + bank + labor + stock; codes and lines reconcile); the by-code "unlinked" row that repeated the bank total is gone | books, lines, screen |
| 3. Line income to cost | By Line is income to cost from the job's own lines; `lineFin` counts a bill once (root fix); Estimate Versus Actual at close-out proposes price-book changes into Company › Changes | lines, closeout |
| 4. P&L and the tie | P&L by Project and by Client on P&L Detail with the tie line; the months add up to the period; Job Reports and the P&L explains labor; intercompany: IC bills at cost when consolidated, profit in WIP eliminated (root fixes) | books, screen, entity |
| 5. Overhead | Overhead Analysis on Statements: by category by month, % of revenue, burden rate, absorption, break-even monthly revenue | overhead |
| 6. WIP, cash, aging, backlog, retainage | Ties on WIP, Receivables, Payables; Cash & Receivables › Cash Forecast (13 weeks, backlog, retainage both ways); the forecast no longer pays bills the bank paid and carries the owed payroll run and the card balances (root fix) | books, cash13, screen |
| 7. Closed periods | Sealed August reads the same (whole P&L and by project); the retainer applied now relieves 2400 so closed August ties to the ledger to the cent (root fix); September lists corrections to sealed months with Open | sealed |
| 8. Choices | Accounting Choices card on Statements: development costs, tax revenue recognition, overhead basis; default, what each moves, who/when/why | overhead (shown) |
| 9. Export and share | Excel on every Reports tab (one sheet per table, numbers as numbers); the Pack's ties on the phone | excel, phone |
| 10. QuickBooks | unchanged: the Three-Way Tie-Out (truth_test) | — |
| Ask | P&L by project and client, break-even, 13-week low, retainage both ways, do the reports tie; seven report tables, money, Reports roles only | ask |

Not done: read-only access for the accountant (a platform role on the hosted copy); the development-cost and tax
choices are shown with what they move, but choosing "capitalise" or "completed contract" does not yet change the
statements; the cost book (`DB.company.costBook`) is written on approval but no estimate screen reads it yet (the
item library lane's estimating should).
