# Reports: the pages, by Alan's ten questions

Mock-up and spec, 2026-11-03. Not built. Read with `docs/mockups/QUESTIONS.md`, the approved job pages in `docs/mockups/job-structure/` (the approved menu in `Main.dc.html` names Reports: Job Profitability, Cash, Report Builder) and the Accounting spec (`docs/mockups/accounting/SPEC.md`). Figures are the demo company's on Thu 9/3, read from master 8eeb990's build; bracketed marks are figures the build did not give.

**Reports is where money is read, by the question a person asks.** Each page opens on what needs you (each line links to the page where it is acted on), then the answer, then the detail one tap down with chips. A report never holds a queue: acting happens in Accounting or on the job.

## 1. Today: 2 pages (+ Billing's Client Funds tab), 30 screens

| Page (view) | Reached by | Tabs | First screen |
|---|---|---|---|
| Reports (`reports`) | owner, PM, billing, controller; one way in for every role | Financials (P&L Detail, Statements, Budget vs Actual + By Month, Monthly Pack, Three-Way Tie-Out; Accrual / Cash), Projects (All Projects, Project Profitability, Cost Intelligence, WIP Schedule, Studio, Cost Library, Submittal Log, Daily Log Summary, Progress vs Plan), Cash & Receivables (Receivables, Payables, Client Statement, Cash Forecast), Review (Analyst: All 23, Act Now 2, This Week 12, Housekeeping 9; Weekly Flash), Build a Report | P&L year to date: revenue $142,759, job cost $108,494, gross $34,265, net −$5,330; 3.9 desktop / 7 phone screens tall |
| Dashboard (`dashboard`) | owner, PM, coordinator, designer, billing, controller | My Dashboard, Owner, Projects | Decide 6, Approve 5, Watch 34 |
| Billing > Client Funds | all four | (Billing's tab) | Bank $184,231, client funds $25,375, "Available Cash (Ours)" $158,856 |

What the experts found (`docs/loop/round1/accounting.md`, `owner.md`, `TRIAGE.md` CX2, CX6, classes 1, 3): four "ours" figures (Safe to Spend −$4,151; Client Funds' $158,856; the Flash's "available $158,856"; live Ask); Collections three levels down; the Monthly Pack offers only "Sep 26 (open)", so August cannot be packed; Cost Library, Submittal Log and Daily Log Summary filed under Reports; the Tie-Out says "agrees" with nothing compared.

## 2. Proposed: 4 pages, 12 chip views

Mock-ups: `JobProfit` + `DeskJobProfit`, `Cash` + `DeskCash`, `Statements`, `Builder` (`.dc.html`).

**Job Profitability**.
1. What: every job, what it will make and where its billing stands.
2. Label: "Job Profitability", the approved menu's word; the owner and PM say it.
3. Holds one row per job (the job's own Budget and Contract and Billing roll up here); Margin and Work in Progress are two views of the same rows. The per-line detail stays on the job's Budget.
4. Owner: "which job is making or losing money?" PM: his jobs. Controller: the WIP schedule and its tie.
5. A job row opens that job's Budget, never a firm list.
6. Needs You 3 (121 State 20.83% at completion against 21.81% bid, windows $3,800 over; $14,072 of payroll on no job; Over-Billed (WIP) $156,274), tiles (contracts $725,700, margin $196,039 at 27%, billed $299,034, collected $169,750 with a bank line), the jobs, then the company after overhead (net −$5,330).
7. Needs You 3 = its rows; tiles are where things stand, labelled.
8. No +: nothing is created on a report.
9. Phone: each job a card with labelled figures; no table.
10. One page; WIP folds in as a view (same jobs, one list), and stays a named standard report for the bank and surety.

**Cash** (with Client Funds, Receivables and Payables).
1. What: what is ours to spend, what is the client's, and the next 13 weeks.
2. Label: "Cash", the owner's word ("cash for two weeks").
3. Holds Safe to Spend with its parts, the 13-week forecast, client funds by line, the receivables and payables aging with their ledger ties. The invoices' home is Billing; the bills' is Bills and Payroll; this reads them.
4. Owner: "can I spend, and when is the low?" Controller: the forecast and ties. Billing: what comes in.
5. A week, a client or a line opens that record.
6. Safe to Spend −$4,151 = bank $184,231 (statement through 8/31) − cards $16,067 − payroll due $16,040 − Over-Billed (WIP) $156,274; the 13-week low $135,583 (11/26); "not counted: $21,350 recorded, not in the bank". Then Needs You 3, then the views.
7. One "ours" figure. Needs You 3 = its rows.
8. No +.
9. Phone: the bars are 13 tappable weeks with the selected week labelled; scale written.
10. One page; Client Funds, Receivables, Payables and the Cash Forecast become its four views.

**Financial Statements** (with the Pack).
1. What: the firm's statements and the Pack, for any week or month.
2. Label: "Financial Statements", the controller's and the bank's word.
3. Holds the P&L (management view, accrual or cash), Balance Sheet, Cash Flow, Budget vs Actual, the Pack and the Weekly Flash. The Ledger's statement tab folds in; the trial balance stays on Books.
4. Owner: the monthly Pack and the week. Controller: produces and ties them. CPA and bank: the statements.
5. An entity filter scopes all of it; a line drills to its entries.
6. Period chips first (This Week, August 2026, September to Date, Year to Date); the Pack's state ("Draft: August is not closed, 15 of 24 checks open"); the statement; then what stands behind the numbers (income with a bank line $169,750; cost by hand $9,650 flagged; 1 opening entry $172,503 flagged; manual journals 0).
7. No counts; the Pack's state says what waits.
8. No +.
9. Phone: each line labelled; 44px chips.
10. One page; P&L Detail, Statements, Budget vs Actual, Monthly Pack, Three-Way Tie-Out, the Weekly Flash and Ledger > Statements (7 screens) fold in.

**Report Builder**.
1. What: any record in the system, filtered, grouped and totalled, then saved, pinned or sent to Excel.
2. Label: "Report Builder", as today and in the approved menu.
3. Holds saved reports (9 today) and the standard reports that moved to the role that acts, kept here too so nothing is lost and Cmd-K finds them.
4. Controller and owner: "a question no page answers". Everyone: their pinned reports.
5. n/a: not inside a record.
6. Search (or ask), then Saved, Standard, Pinned, then Start From (every queryable table, NetSuite's differentiator).
7. Row counts only, no badges.
8. One + (New Report).
9. Phone: saved reports open and read on the phone; building is a desktop job.
10. One page; Build a Report and the Dashboard's My Dashboard (as Pinned) fold in.

## 3. Old page or tab, new home (2 pages, 30 screens and Client Funds, each placed)

| Old | New home |
|---|---|
| P&L Detail (Accrual / Cash), by project, by client | Financial Statements P&L (basis on the page, not sticky across pages); by job on Job Profitability |
| Statements; Ledger > Statements | Financial Statements Balance Sheet, Cash Flow (trial balance on Books) |
| Budget vs Actual, By Month | Financial Statements Budget vs Actual |
| Monthly Pack | Financial Statements, any period, closed months final, open ones marked Draft |
| Three-Way Tie-Out | "What stands behind these numbers" and Books Close; says "nothing to compare" when nothing is |
| All Projects, Project Profitability | Job Profitability, Margin |
| WIP Schedule | Job Profitability, Work in Progress; Standard report |
| Cost Intelligence | the job's Budget and Purchasing's price history; Standard report |
| Studio | Design; design jobs on Job Profitability; Standard report |
| Cost Library | Purchasing (the price book); Standard report |
| Submittal Log | Decisions, every job; Standard report |
| Daily Log Summary | the job's Site; Standard report |
| Progress vs Plan | the job's Contract and Billing (the measure billing bills on) |
| Receivables | Cash, Receivables (read); Billing, Collections (the chase) |
| Payables (aging, retainage) | Cash, Payables; lien waivers on Bills and Payroll; 1099 and sales tax on Books |
| Client Statement | the client record and the job's Contract and Billing (Statement) |
| Cash Forecast | Cash, Next 13 Weeks |
| Review: Analyst (All, Act Now, This Week, Housekeeping), Ask AI to Review, Brief | each finding on the page whose role acts: duplicate and uncoded lines on Banking; over-PO and payroll split on Bills and Payroll; floated purchases on Billing; WIP gaps and the deposit on Books; owner exceptions on Today. The review itself is Ask; the brief is Today |
| Weekly Flash | Financial Statements, This Week |
| Build a Report | Report Builder |
| Dashboard: My Dashboard; Owner; Projects | Report Builder Pinned (shown on the person's Today); Today, Cash and Job Profitability; Projects > All Projects. The page goes; its link forwards to Today |
| Billing > Client Funds | Cash, Client Funds (its "Available Cash (Ours)" figure removed) |

## 4. Who sees what

| Role | Reports menu | Lands on |
|---|---|---|
| Owner | Job Profitability, Cash, Financial Statements, Report Builder | Cash |
| Controller | all four | Financial Statements |
| Billing | Job Profitability, Cash, Report Builder | Cash |
| PM | Job Profitability (his jobs only, no company card), Report Builder | Job Profitability |

## 5. Decisions made here, and why

1. **Work in Progress is a view of Job Profitability**, not a page: the same job rows, one list per noun (Q3). It stays named in Report Builder and Cmd-K.
2. **Financial Statements is added** to the approved three: the P&L, the balance sheet and the Pack need one home the owner can find, and the Ledger's copy folds into it. Recommend Alan says yes; the alternative (statements under Books) hides the P&L from the owner's menu.
3. **Receivables and Payables join Cash** as views; the chase is Billing's (CX6: with the role that acts).
4. **The Pack for any period**, closed months final and the open one marked Draft; the Weekly Flash is the Pack for a week.
5. **One "ours"**: Safe to Spend. Client funds and spend ahead of payment are its parts, never a second figure (CX2).
6. **The P&L is the management view**; the ledger's own P&L before the close ($175,285.70) lives on Books with the bridge to −$5,329.88.
7. **Reports hold no queue and at most one blue** (Open the Pack); Needs You lines link to the acting page.

## 6. Unsure, and what the checks would miss

- **Safe to Spend sets aside all of Over-Billed (WIP), $156,274**, though $92,265 of what was billed is not yet paid by the client; the cash it guards against may never have arrived. The lane 1 default says WIP is the set-aside; recommend the controller confirm whether only collected over-billing should come off. It moves Safe to Spend by tens of thousands.
- **Job cost has three numbers for 121 State**: $105,084 (the job), $101,694 (P&L by project), $75,750 (bills). The P&L's job cost $108,494 against the jobs' $113,083 needs its one-line reason (`[REASON]`). Each pair joins the counts lint.
- Whether client funds ($25,375) sit inside the WIP set-aside: `[CONTROLLER TO CONFIRM]`.
- 206 Lenox reads $0 cost while hours and a scaffold are on site (triage class 9): `[NOT IN JOB COST YET]`.
- Not read: balance-sheet totals, cash flow from operations, 45 Cranberry's Billed Ahead of the Work. Placeholders.
- The Flash's "available $158,856" beside Safe to Spend −$4,151 is today's live contradiction; the mock drops it.

## 7. Self-review against QUESTIONS.md

| Page | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Job Profitability | pass ("and" is one row's two views) | pass | pass | pass | pass: row opens the job | pass | pass | pass | pass | pass |
| Cash | pass | pass | pass: reads, never owns | pass | pass | pass | pass: one "ours" | pass | pass | pass |
| Financial Statements | pass | pass | pass | pass: owner reads the Pack monthly | pass | pass | pass | pass | pass | pass |
| Report Builder | pass | pass | pass | pass | n/a | pass | pass | pass | partial: building is desktop | pass |

Revised during review: WIP folded into Job Profitability (Q10); Receivables and Payables folded into Cash; "Open the P&L" made a 48px row; the chart's scale written; the client-funds claim made a placeholder. Phone screens rendered at 390px: nothing sideways, every target 44px or more.
