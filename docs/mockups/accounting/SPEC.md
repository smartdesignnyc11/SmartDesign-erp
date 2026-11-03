# Accounting: the pages, by Alan's ten questions

Mock-up and spec, 2026-11-03. Not built. Read with `docs/mockups/QUESTIONS.md`, the approved job pages in `docs/mockups/job-structure/` (the menu in `Main.dc.html` already names Accounting: Billing, Banking, Bills and Payroll) and the Reports spec beside this one (`docs/mockups/reports/SPEC.md`). Figures are the demo company's on Thu 9/3, read from master 8eeb990's build as each role; `[PLACEHOLDER]`-style marks are figures the build did not give.

**Accounting is where money is acted on; Reports is where it is read.** Every Accounting page is a queue first ("Needs You"), then where things stand, then the records one tap down with chips. Firm-wide pages hold the same records as the job's own pages (Contract and Billing, Budget), across all jobs with a job filter; they are never a second home.

## 1. Today: 9 pages, 45 screens (owner's menu; census build bd3180c, counts re-read on 8eeb990)

| Page (view) | Reached by | Tabs | First-screen counts |
|---|---|---|---|
| Accounting (`ovmoney`, Today's Review) | owner; PM, billing, controller under More | none | No Record Behind 15 · Receipts to Approve 6 · Hours to Approve 4 · Cards and Bills 16 |
| Billing (`billing`) | all four; billing's and the controller's own entry | Billing Queue, Progress Billing, Estimates 4, Change Orders 2, Invoices 6, Schedule of Values, Payments 4, Client Funds | Ready to Bill $32K · Drafts 0 · Sent and Unpaid $92K · Overdue $0 |
| Banking (`bank`) | all four | Needs Review / All / Unreconciled x All Accounts / Chase / Amex / Home Depot; Reconcile; Bank Rules; 7 toolbar buttons | To Review 15 · Oldest 19 days · Cash in Bank $184K · Unexplained 0 |
| Spend (`spend`) | all four | 4 tile-tabs; The Day 2, Where Cost Starts (Cards and Who Spent, Hours and Payroll, Vendor Bills Arriving), To Approve 2, To Settle, Cost Not Billed 1, Everything | Missing Receipts 0 · Uncoded 0 · To Approve 2 · No Record Behind 15 |
| Bills & Payroll (`ap`) | all four | Awaiting Approval, Approved · To Pay, Paid, All | Needs Approval 2 · Overdue to Pay 1 · Due This Week 0 · Flagged 2 |
| Time & Crew (`time`) | owner, PM, coordinator, controller | Awaiting Approval, This Week, Approved · Unpaid, All | Entries to Approve 4 · Missing Time 1 · On Site 0 · Overtime 0.0 h |
| Ledger (`gl`) | owner, controller | Overview, Journal, Accounts, Statements (P&L, Balance Sheet, Cash Flow, Trial Balance), Close, New Entry | Journals 0 · Period Open August · Drift 0 · Uncoded Cost 1 |
| Controls (`verify`) | owner, PM, controller | Verification, Approvals, Terms and Early Payment, Reconciled Through, Unassigned Cost x Open / Verified / All Transactions | Exceptions Open 15 · Aged 1 · Not Yet Checked 36 · Verified 0% |
| Budget (`budget`) | owner, controller | none | the 2026 operating budget |

What the experts found (`docs/loop/round1/accounting.md`, `TRIAGE.md` CX5, classes 1, 3, 8): the same money-out lines in five queues (Banking, Spend, Today's Review, Reports > Review, Controls; WW-2026-118 on 7 pages); "No Record Behind 15" beside "Missing Receipts 0"; Receipts to Approve 6 and 2; collections three levels down in Reports; a phone Confirm that hides its target.

## 2. Proposed: 4 pages, 18 chip views

Mock-ups: `Menu` (by role), `Billing` + `DeskBilling`, `Banking` + `DeskBanking`, `BillsPayroll`, `Books` + `DeskBooks` (`.dc.html`).

**Billing** (billing's home).
1. What: the client's documents for every job, what to bill next and what is still owed.
2. Label: "Billing", the billing person's word; Collections is a card, not a page.
3. Holds signed estimates (the contracts billed against), change orders, invoices, payments, the same records as each job's Contract and Billing, filtered by job; home stays the job. Estimates still being priced or sent live only in Sales and Clients, Estimates, linked at the foot of the list, so the firm has one estimates list. Collections reads the same open invoices as Cash > Receivables.
4. Billing: "what do I bill and chase today?" Controller: deposits and recorded-not-banked. Owner: almost never (his signal is the Cash line on Today).
5. With a job picked, every row, count, the aging, the retainage and the + are that job's.
6. Needs You (4: $17,080 Cranberry milestone; $12,651 measured on 121 State with $66,470 Billed Ahead of the Work and the $10,170 windows billback held; $2,600 Prospect hours; $21,350 Rivera not in the bank), Collections (aging $92,265 current, retainage $15,668 its own bucket, reminders at due/7/15/30), then Documents.
7. Needs You 4 = the rail's 4 = its rows. Chips carry no counts: nothing in them waits.
8. One + (Progress Application, Deposit Invoice, Invoice, Change Order), tied to the job filter or asking the job first.
9. Phone: labelled figures, 44px chips and rows, job filter as a sheet.
10. One page; Progress Billing and the SOV are the job's own page, opened from the Needs You row.

**Banking** (the controller's home; the one queue for money in and out, CX5).
1. What: every bank and card line, matched to the line it pays or explained.
2. Label: "Banking", as today and in the approved menu.
3. Holds bank and card lines, receipts, and recorded client payments with no bank line. Spend, Today's Review, Controls' exceptions and Unassigned Cost fold in; one detector feeds every flag (duplicate, typed, paid before approval).
4. Controller: "what left or reached the bank that nothing explains?" Billing: Money In. Owner: never; exceptions reach his Today.
5. A line opened is that line: what it would link to, why, and the safe step.
6. Needs You: 15 lines, $67,272 at stake, oldest 19 days, August's 7 lines that block the close; then To Review sorted by risk; then Accounts with statement and reconciled-through dates.
7. To Review 15 = the rail's 15. Money In and Receipts carry no count: Money In is billing's chase (Billing's Needs You row), and a crew receipt is approved by the job's PM on his Approvals, never by the person who bought.
8. One + (Import a Statement, Connect a Bank, Bank Rule, Receipt, Typed Line flagged as not from the bank).
9. Phone: no Confirm on a list row; the line's sheet names the target and the warning first (S1). Typed lines say so on the row.
10. One page; the account tabs become the Accounts card and a filter.

**Bills and Payroll**.
1. What: what the firm owes vendors and its own people, from arrival to approved to paid.
2. Label: "Bills and Payroll", the approved menu's word.
3. Holds vendor bills (including arriving ones), time entries, payroll runs, payments and lien waivers. Approvals > Bills reads the same query.
4. Controller: "what do I approve, split and pay?" Owner: what waits on him (WW-2026-118).
5. A bill opened shows its PO, receipt and bank line.
6. Needs You 4 (payroll 8/17-8/28, $16,040, 2 days late, 88% unallocated: split it first; 4 time entries, 30.1 h, 2 flagged; AMP-311 held as possibly paid; CM-0091 paid with no lien waiver), With Others (WW-2026-118 with Alan), then chips.
7. Needs You 4; To Approve 3 = its rows (the payroll run, the 4 time entries, AMP-311): what waits on the controller. WW-2026-118 sits under With Others, not in his count. The payroll run he builds is approved by Alan. "Due This Week 0" is not shown.
8. One + (Vendor Bill, Payroll Run, Time Entry).
9. Phone: the owner's approve-with-dispute stays the bill sheet; 44px.
10. One page: payroll and time join bills (one approval, one pay run, the split checked before pay day, Alan 10-26 decision 3).

**Books** (the controller's; not on the owner's menu).
1. What: the ledger, the month's close and the controls behind the numbers.
2. Label: "Books", the controller's word ("books by the 10th").
3. Holds journals, accounts, trial balance, the close checklist and its postings, the control rules, the operating budget, 1099 and sales tax. Statements move to Reports > Financial Statements.
4. Controller: "can I close August, and is anything posted wrong?" Owner: almost never: journals to post and the close sign-off reach his Approvals.
5. Inside an entity filter, everything is that entity.
6. Needs You 4 (close 15 of 24 open, with Amex's $365.64 inside it as a close check, not a second row; INV-2026-031's $97,000 deposit booked as a draw; Over-Billed (WIP) against Billed Ahead of the Work, $64,587 apart on 121 State; $0.16 short-paid), then Close, Ledger, Controls, Operating Budget, Tax and 1099. The WIP adjustment that posts at the close is the WIP schedule's Over-Billed (WIP), job by job: one figure with Job Profitability (BACKLOG §1.35.3).
7. Needs You 4 = the rail's 4.
8. One + (Journal Entry, drafted by the controller and posted by Alan).
9. Phone: readable; the close is done on the desktop.
10. One page with five chips, down from Ledger, Controls and Budget (3 pages, 15 screens).

## 3. Old page or tab, new home (9 pages and 45 screens, each placed; nothing lost)

| Old | New home |
|---|---|
| Accounting (Today's Review) page | removed; its link forwards to Banking. Its six counts: No Record Behind and Unassigned Cost to Banking To Review; Receipts to Banking Receipts; Hours to Bills and Payroll; Cards with no holder to the "whose card" field on each line and Accounts > Cards; orders received with no bill to Bills and Payroll; lines over budget to Job Profitability |
| Billing Queue | Billing, Needs You |
| Progress Billing; Schedule of Values | the job's Contract and Billing (application and G703), opened from Needs You |
| Estimates, Change Orders, Invoices, Payments tabs | Billing Documents chips (same records as the job's page) |
| Client Funds | Reports > Cash > Client Funds |
| Reports > Receivables (the chase) | Billing, Collections; the aging also reads on Cash > Receivables |
| Banking Needs Review / All / Unreconciled | Banking To Review / Matched |
| Banking account tabs, Reconcile, Statement Imports, Bank Rules, toolbar | Banking Accounts card; Reconcile August; the + |
| Spend The Day, To Approve, New Receipt | Banking Receipts; the + and the crew's camera |
| Spend To Settle, No Record Behind, Missing Receipts, Uncoded | Banking To Review (the match and the flag on each line) |
| Spend Cost Not Billed | Billing Needs You (its own text: "the same rows as Ready to Bill") |
| Spend Everything | Banking Matched and Report Builder |
| Spend Cards and Who Spent | Banking Accounts > Cards |
| Spend Hours and Payroll | Bills and Payroll, Payroll chip |
| Spend Vendor Bills Arriving | Bills and Payroll, To Approve (arriving first) |
| Bills & Payroll tabs; Paid Before Approval; Payments | Bills and Payroll chips; With Others; Paid |
| Time & Crew: entries, missing time, Build Payroll | Bills and Payroll Needs You and Payroll chip |
| Time & Crew: On Site Now; Employees | the job's Site; Company > Team |
| Ledger Overview, Journal, Accounts, Trial Balance, New Entry | Books Ledger; the + |
| Ledger Statements (P&L, Balance Sheet, Cash Flow) | Reports > Financial Statements |
| Ledger Close | Books Close |
| Controls Verification, Open Exceptions, All Transactions | the lines: Banking; the check and "never run": Books Controls |
| Controls Approvals (the ladder), Terms and Early Payment | Books Controls; the discount also on the bill in To Pay |
| Controls Reconciled Through; Unassigned Cost | Books Close and Banking Accounts; Banking To Review |
| Budget (operating) | Books Operating Budget (renamed: the job's Budget is a different noun) |
| Payables' lien-waiver and 1099 registers | Bills and Payroll (waiver on the sub's bill); Books Tax and 1099 |

## 4. Who sees what

| Role | Accounting menu | Lands on |
|---|---|---|
| Billing | Billing 4, Banking (Money In first) | Billing |
| Controller | Billing, Banking 15, Bills and Payroll 4, Books 4 | Banking |
| Owner | Billing, Banking, Bills and Payroll, with no badges (approved menu, unchanged) | Today; what waits on him (WW-2026-118, the payroll run, journals, the close sign-off) is on Today, counted once |
| PM | none: he works the job's Contract and Billing and Budget; bills he recommends sit on his Approvals | the job |

## 5. Decisions made here, and why

1. **Four pages, not five.** Payroll and Time fold into Bills and Payroll: the approved menu names it, one sentence holds it, and the split must be checked before pay day on the same run.
2. **Books is the controller's only.** The owner's menu stays the approved three; what Books needs from him (post a journal, sign the close, read the Pack) reaches Today and Approvals. Access by link and Cmd-K stays.
3. **Banking is the one queue (CX5).** Five queues fold into it; Analyst findings go to the page of the role that acts (Reports spec).
4. **Collected only with a bank line** shows on the row: Money In holds recorded payments the bank has not shown; typed lines say "typed by hand, not yet at the bank" and are never offered as matches.
5. **Billed Ahead of the Work** (billing's field check) on Billing; **Over-Billed (WIP)** (the accounting number) on Books and Reports; the gap is a Books finding (lane 1 default).
6. **The deposit is its own invoice**: the + offers Deposit Invoice; INV-2026-031 booked as a draw is the controller's finding.
7. **One blue**: the safe next step (draft, start the review, split, continue the close). No commit is blue on a list.

## 6. Unsure, and what the checks would miss

- Billing's queue row today prints two billed-ahead figures for 121 State ($53,819 net "not counting the deposit", and $66,470); the mock uses $66,470, the adopted label. One must go.
- The Analyst says windows "$20,270, bill it"; Billing says $10,170 (lane 1's figure). $20,270 is spend beyond what the client paid, a different question; the Analyst must stop saying "bill it".
- Window Works' bank-detail change: 8/20 on the Analyst, "4 days ago" (8/30) on Controls. Shown as `[DATE]`.
- "$67,272 at stake" adds the two credits ($215, $126) as dollars; label it "at stake", not "out".
- The Billing count goes from 3 to 4 (the Rivera chase joins Needs You).
- Not read: last-touch dates on invoices, the next payroll period, sales tax. Placeholders.
- The counts lint must learn the new pairs: rail = Needs You rows, chip = its rows.

## 7. Self-review against QUESTIONS.md

| Page | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Billing | pass | pass | pass: job's records, filtered | pass | pass: job filter scopes all | pass | pass | pass | pass | pass |
| Banking | pass | pass | pass: 5 queues to 1 | pass | pass | pass | pass: 15 = 15 | pass | pass: no Confirm on rows | pass |
| Bills and Payroll | pass ("and" joins one noun: what we owe) | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Books | pass | pass | pass | pass: owner's signal moved to Today | pass | pass | pass | pass | partial: the close is a desktop job; phone reads it | pass |

Revised during review: Payroll and Time folded in (Q10); Receipt added to Banking's +; the client-funds claim and the Window Works date made placeholders instead of guesses. Desktop chips are 34 to 36px, as in the approved desktop mock-ups; the phone screens measure 44px or more on every target and 390px wide with nothing sideways (rendered and measured).

## 8. Chief of staff review, 11-03 (night)

Decided, reversible, logged in `docs/DECISIONS.md`: Books stays off the owner's menu (his sign-offs reach Today and Approvals; read access by link and Cmd-K stays). Fixed in the mock-ups: the owner's menu and rails match the approved menu (no Tasks 12, no Bills and Payroll badge); Billing's aging and retainage follow the job filter and the firm keeps one estimates list (Sales); the billing role's desktop rail no longer shows Bills and Payroll; Banking's Money In and Receipts carry no count; Bills and Payroll's To Approve holds what waits on the controller and names Alan as the payroll approver; Books' Needs You is 4 (Amex folded into the close), its budget chip is Operating Budget, and the WIP adjustment row reads the WIP schedule's figure.

Must fix before build: the four money definitions in BACKLOG §1.35 (Safe to Spend's set-aside, one job cost, one WIP figure at the close, one billed-ahead and one to-bill), and the bank-detail change's date from its own record. Not rendered by the reviewer (no support.js in the folder); the logic blocks were syntax-checked and run.

