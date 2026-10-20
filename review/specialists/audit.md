# Role specialists: the audit (BACKLOG §1.28, §1.29–1.32 where they touch it)

Lane: role specialists, 2026-10-20. Read with `src/specialists.js` (RS_CHECKS, RS_SRC) and `tests/specialists_test.py`.

## What was asked, and the rule this audit holds the build to
§1.28 asks for a standing auditor per role: each line of the role's checklist is worked all the time, and every
finding is handled in six steps (the rule and the evidence; the root cause; options, a recommendation and the fix
drafted; a task for the right person; follow-up until the record is fixed; learning). §1.16 forbids a second count of
anything: "a specialist organises existing findings per role and adds the six-step handling; it never adds a second
list of the same thing."

So, before building, each checklist line was matched to the detector that already checks it, and to where it surfaces
today. The result is the table below, and it is also the code: `RS_CHECKS` names, for every line, the detector it
reads (`RS_SRC`). A line's count is that detector's rows, read at the moment; the suite checks that the checklist line
for Bills Over Their PO, Earned Not Billed, Unmatched Bank Lines, Early-Pay Discounts and Accounts Not Reconciled each
equals its source's count.

## Where the detectors were, before this lane
| Registry | What it holds | Surfaces |
|---|---|---|
| `CATCH` (36 detectors) | Caught for You: earned not billed, cost not billed, over PO, over budget, compliance, credits, follow-ups, late tasks, unmatched lines, RFQs, the nine price-watch detectors, plans, set check, daily logs, client drafts, CO needed, subs ahead, overpaid vendors, bills on hold, bought while in stock, the Standard Watch's "catch" rules | the Owner's and PM's Home (Caught for You); the assistant's Findings |
| `PRED` (64 predicates) | every counted question: waiting on me, late material/decision/submittal, inspections, CO needed, unsigned, uncoded cost, safe to spend, jobs at risk, unmatched, vendors blocked, track's seven, stock | badges, tiles, Home pulse, Ask |
| `STANDARD_RULES` (22 rules) | the Standard Watch: each measurable standard, its owner and today's breaches; "do", "catch", "nyh", "watch", "existing" surfaces | Settings › The SmartDesign Standard; Caught for You; Needs Your Hand |
| Needs Your Hand (`nyhRows`) | mail proposals, deposits, payroll, duplicates (`lkDupScan`), rebill, the Watch's "nyh" rules, lessons firing | each role's Home (the office roles) |
| The Payment Check (`pcCheck`, `pcHeldBills`) | approval, separation of duties, bank change, papers (COI/licence), W-9, duplicates, prior payments, contract, retainage, waivers, three-way, work ahead, credits | the payment sheet, the payment run, Approvals (payhold) |
| Price watch (`PW_DET`) | paid more, quantity over, duplicate charge, split, fee spike, rare vendor, not delivered, card with no job, use tax | CATCH + PRED |
| The brain (`LEARN_EVENTS`, `lnLoop`) | 22 event kinds that propose lessons | The Brain; Needs Your Hand (learn) |

## What was missing, and what was added (each added once, as a predicate or a Watch rule, so it has one rule and one count)
| Check | Before | Added |
|---|---|---|
| Missed early-pay discounts (controller) | the Terms pane (`tmRows`) computed it, but nothing raised it | `PRED.discountsAtRisk`: window closing within 3 working days, or closed while unpaid |
| Jobs spending more than they bring in (founder) | not measured (the cost-intelligence lane, §1.29 item 1, owns the fuller rule) | `PRED.jobsCashNegative`: bank and card lines out on a job over the client money in. **Merge note:** if cost intelligence registers its own "cash out over cash in" predicate, `RS_SRC.cashNeg` should read it and this one goes. |
| Lines forecast over budget (controller, PM) | `CATCH budgetOverrun` reads the analyst's "over budget" findings and was 0 while two lines forecast over | `PRED.linesOverBudget` from `jobFin(p).eacLines` (eac above budget) |
| Duplicate vendor invoices (controller) | only the Payment Check, at payment time, on approved bills | `PRED.billsDuplicate` reads the Payment Check's own `dup` hold (`pcCheck`) on every unpaid bill, from the day it is entered: the same rule, earlier |
| Unbudgeted cost over $1,000 (owner) | not measured | Standard Watch rule `unbudgeted1k` (surface nyh, owner): a bill or bank line on a live job on no estimate or CO line, over the owner's figure |
| Milestone slip over 2 working days (owner) | not measured | Standard Watch rule `slip2days` (surface nyh, owner) |
| Overloaded people (founder, §1.32 #2) | not measured | `PRED.peopleOverloaded` (tkAll, overdue, hours in 7 days from the clock, answer times on field questions) |

Changed, as a class: the three-quote rule reads the owner's threshold (it was a fixed $2,500); the Friday-update rule no
longer counts a draft as an update the client received (only a sent one); client acknowledgement is 2 business hours,
on portal questions and on client mail in the reader's own mailbox (it was "after the business day", portal only).

## The checklists, line by line
"Missing" lines are shown in the app as Not Checked with the reason, and never counted. "Same rows" lines point at the
line that already counts them, so no number appears twice.

### Controller and finance

| Line | Detector it reads (count = its rows) | Where it already surfaces | Fix drafted | Task to |
|---|---|---|---|---|
| Unmatched Bank Lines | CATCH unmatchedTxns (= PRED.unmatchedTxns) | Caught for You · Bank | open | controller |
| Typed by Hand, Not at the Bank | PRED.notAtBank; Needs Your Hand kind undeposited | Needs Your Hand · Bank | open | controller |
| Duplicate Charges | Needs Your Hand kind dup (lkDupScan) + CATCH pwDupCharge (price watch) | Needs Your Hand · price watch | dispute | controller |
| Card Charges With No Receipt or Job | PRED.cardNoReceipt (track) + CATCH pwCardNoJob | order tracking · price watch | receipt | controller |
| Accounts Not Reconciled | Standard Watch rule books10 | Needs Your Hand (Standard Watch) | open | controller |
| Bills Paid Before Approval | **Missing.** The Payment Check refuses a payment before approval; a bill marked paid outside it (by hand, in the bank) is not detected yet. |  |  |  |
| Bills Over Their PO | CATCH overPO | Caught for You · Approvals | shortpay | owner |
| Bills With No PO | Standard Watch rule poBeforeOrder | Needs Your Hand (Standard Watch) | open | coord |
| No W-9 or Expired COI at Payment | PRED.vendorsBlocked; Payment Check holds papers/w9 (pcHeldBills) | Vendors (Blocked) · the Payment Check | coiRequest | coord |
| 1099 Payees Not Set Up | 1099 register (fin2Register1099().missing) | the 1099 register | w9Request | controller |
| Early-Pay Discounts | NEW PRED.discountsAtRisk (reads tmRows, the Terms pane) | Bills · Terms | payEarly | controller |
| Duplicate Vendor Invoices | NEW PRED.billsDuplicate (reads the Payment Check dup hold, pcCheck) | Bills | open | controller |
| Earned, Not Billed | CATCH earnedNotBilled (readyToBill) | Caught for You · Billing Queue | invoice | billing |
| Drafts Never Sent | CATCH clientDrafts | Caught for You · Billing | open | billing |
| Overdue Invoices Not Chased | Standard Watch rule collections | Billing (Standard Watch) | chaseInvoice | billing |
| Retainage Due | **Missing.** Retainage held is on every invoice; nothing marks it due (substantial completion, the final walk) yet. |  |  |  |
| Deposits Not Applied | Needs Your Hand kinds deposit + undeposited | Needs Your Hand | open | billing |
| WIP Over or Under Billing Moving | **Missing.** The WIP ties to the ledger on close day (closetie); a move from one week to the next is not measured yet. |  |  |  |
| Lines Forecasting Over Budget | CATCH budgetOverrun + NEW PRED.linesOverBudget (jobFin eacLines) | Caught for You · Job Costs | overBudget | pm |
| Committed Cost Not Relieved | **Missing.** A PO's committed cost falls as its bills land; one left open after the work is done is not detected yet. |  |  |  |
| Change Orders Approved, Not Billed | Same rows as "Earned, Not Billed": An approved change order's lines join the next progress bill from zero, so they show under Earned, Not Billed. |  |  |  |
| Job Spend Coded to Overhead | PRED.uncodedCost | the Ledger | open | controller |
| Close Blockers | ctCloseStatus(last month).blockers | Close | open | controller |
| Payroll Accrual Against the Run | PRED.orphanAccruals | Close | open | controller |
| Sales and Use Tax | CATCH pwUseTax | Caught for You (price watch) | open | controller |
| Unexplained Budget Variances | **Missing.** A budget-vs-actual review is not logged with a date and a reviewer (the Standard Watch says the same). |  |  |  |
| Changed After the Month Closed | truthVerifyAll (sealed month chains) | Verify the Books | open | controller |

### Founder

| Line | Detector it reads (count = its rows) | Where it already surfaces | Fix drafted | Task to |
|---|---|---|---|---|
| Overdue Invoices Not Chased | Standard Watch rule collections | Billing (Standard Watch) | chaseInvoice | billing |
| Changed After the Month Closed | truthVerifyAll (sealed month chains) | Verify the Books | open | controller |
| Cash Runway and the 13-Week Low | TD_PULSE owner safe-to-spend (tdPulseValue) | Home (Safe to Spend) · cash forecast | open | owner |
| Jobs Losing Money, and Why | PRED.jobsAtRisk; NEW PRED.jobsCashNegative (bank lines by job) | Home (Jobs at Risk) | cashNeg | pm |
| Margin Slipping | **Missing.** The margin trend by job and trade is the cost-intelligence lane's (benchmarks, §1.29); not measured here. |  |  |  |
| Collections Risk | Same rows as "Overdue Invoices Not Chased": The same rows as the controller's Overdue Invoices Not Chased. |  |  |  |
| Pipeline Gone Quiet | CATCH chasePeople (leads gone quiet) | Caught for You (Gone Quiet) | open | owner |
| Overloaded People | NEW PRED.peopleOverloaded (tkAll, time, raises) | this checklist (Workload) | moveWork | owner |
| Client Relationships at Risk | Standard Watch rule clientAck (now 2 business hours, portal and own-mailbox client mail); CATCH notBack | Do Now · Caught for You | clientAck | pm |
| Licences, Insurance, Filings | PRED.vendorsBlocked; Standard Watch rule coi30; Needs Your Hand kind oblig | Vendors · Needs Your Hand | coiRequest | coord |
| Escalated to You | NEW Standard Watch rule unbudgeted1k; NEW Standard Watch rule slip2days | Needs Your Hand | escalation | owner |

### PM (three weeks out)

| Line | Detector it reads (count = its rows) | Where it already surfaces | Fix drafted | Task to |
|---|---|---|---|---|
| Lines Forecasting Over Budget | CATCH budgetOverrun + NEW PRED.linesOverBudget (jobFin eacLines) | Caught for You · Job Costs | overBudget | pm |
| Decisions Past Due | PRED.lateDecision | Home (Jobs With Late Items) | decisionChase | pm |
| Materials Not Ordered by Their Order-By Date | PRED.lateMaterial (Buy Board) | Buy Board · Home | order | coord |
| Late Submittals | PRED.lateSubmittal | Submittals · Home | subChase | pm |
| Inspections to Book | PRED.inspToBook | Inspections | open | pm |
| Subs Not Confirmed | CATCH subsAhead | Caught for You | open | pm |
| Tasks Behind | CATCH lateTasks; NEW Standard Watch rule slip2days | Caught for You · Needs Your Hand | open | pm |
| Change Orders Unpriced or Unsigned | PRED.needsChangeOrder + CATCH coNeeded; PRED.unsignedDocs | Do Now · Caught for You | open | pm |
| Unbudgeted Cost Over the Limit | NEW Standard Watch rule unbudgeted1k | Needs Your Hand (the owner's) | escalation | pm |
| Client Messages Unanswered | Standard Watch rule clientAck (now 2 business hours, portal and own-mailbox client mail) | Do Now · Inbox | clientAck | pm |
| The Friday Update | Standard Watch rule fridayUpdate (a draft no longer counts as sent) | Caught for You (Standard Watch) | friday | pm |

### Operations and procurement

| Line | Detector it reads (count = its rows) | Where it already surfaces | Fix drafted | Task to |
|---|---|---|---|---|
| Materials Not Ordered by Their Order-By Date | PRED.lateMaterial (Buy Board) | Buy Board · Home | order | coord |
| Late Submittals | PRED.lateSubmittal | Submittals · Home | subChase | pm |
| Lead Times and Promised Dates | PRED.promisesBroken (track) | order tracking | open | coord |
| Three Quotes | Standard Watch rule threeQuotes (now the owner's threshold) + CATCH rfqUnderQuoted | Standard Watch · RFQs | quotes | coord |
| The Submittal Gate | Same rows as "Late Submittals": The gate refuses a PO at issue; a line waiting on its submittal shows under Late Submittals. |  |  |  |
| Paid, Not Delivered | CATCH pwNotDelivered | Caught for You (price watch) | open | coord |
| Credits Not Received | returns awaiting credit past chaseDays (retList, the Returns page rule) + CATCH unmatchedCredit | Returns · Caught for You | creditChase | coord |
| Bought More Than Ordered | CATCH pwQtyOver | Caught for You (price watch) | open | coord |
| Bought While in Stock | CATCH boughtWhileInStock | Caught for You (stock) | open | coord |
| Paid More Than the Best Price | CATCH pwPaidMore | Caught for You (price watch) | open | coord |

### Billing

| Line | Detector it reads (count = its rows) | Where it already surfaces | Fix drafted | Task to |
|---|---|---|---|---|
| Earned, Not Billed | CATCH earnedNotBilled (readyToBill) | Caught for You · Billing Queue | invoice | billing |
| Drafts Never Sent | CATCH clientDrafts | Caught for You · Billing | open | billing |
| Overdue Invoices Not Chased | Standard Watch rule collections | Billing (Standard Watch) | chaseInvoice | billing |
| Deposits Not Applied | Needs Your Hand kinds deposit + undeposited | Needs Your Hand | open | billing |
| Cost Not Billed Back | CATCH costNotBilled (spUnbilled); Needs Your Hand kind rebill (rbRows) | Caught for You · Needs Your Hand | invoice | billing |

### Foreman

| Line | Detector it reads (count = its rows) | Where it already surfaces | Fix drafted | Task to |
|---|---|---|---|---|
| Inspections to Book | PRED.inspToBook | Inspections | open | pm |
| Subs Not Confirmed | CATCH subsAhead | Caught for You | open | pm |
| Daily Log With Photos | Standard Watch rule dailyLog | Daily Log | open | foreman |
| Material Requests Five Days Ahead | Standard Watch rule request5days | Requests | open | foreman |
| Current Drawings Acknowledged | CATCH plansNotAcked | Drawings | open | foreman |
| Site Questions Open | PRED.siteQuestions | Raise · Approvals | open | pm |
| Quality Checkpoints | **Missing.** Layout, rough-in, pre-close, finish and punch checkpoints are not recorded as steps with photos yet. |  |  |  |

### Designer

| Line | Detector it reads (count = its rows) | Where it already surfaces | Fix drafted | Task to |
|---|---|---|---|---|
| Decisions Past Due | PRED.lateDecision | Home (Jobs With Late Items) | decisionChase | pm |
| Field Questions Past Two Days | Standard Watch rule designer2days | Do Now (Standard Watch) | open | designer |
| Drawings Waiting on an Amendment | CATCH plansAmendment | Caught for You (plans) | open | designer |
| Selections Schedule Complete | **Missing.** Each selection's spec, supplier, price, lead time and approval date is not checked for gaps as one rule yet (the verifier checks each item). |  |  |  |


### Crew and driver
No checklist: their playbooks' measurable lines (photograph before covering, tests documented, the store run) have no
detector yet, and a field person never reads money. Their Home carries the one-liner only (the crew playbook's mission,
in Spanish when their setting says so).

## The six steps, as built (`rsSix(key)` returns all six; the sheet draws them; the bank test reads them)
1. **The rule and the evidence.** `standardWhy` of the line's Standard key (live text, never copied), Alan's line on
   why money matters on every money leak, and the records linked (bill, PO, bank line and its twin, vendor, job,
   submittal, decision, portal question, Buy Board line, budget line), each opening the record.
2. **Root cause.** From the records: the bill against what is left on its PO, the bill's own note, the last approvals
   with who and what they said, the terms and why the discount window was missed, the twin charge, the vendor's
   certificate and open orders, the material's lead time and need-by, who holds the submittal and for how long, the
   hours a client has waited, the job's cash in and out and what is ready to bill on it. Then mail the reader may read
   (their own mailbox and the firm's shared one, never another person's; none for a field role) and the order
   documents filed on the record.
3. **Options and a recommendation, the fix drafted.** `RS_FIX` per line: the short-pay to the PO with a credit-memo
   request drafted to the vendor; the duplicate dispute; a COI or W-9 request; the invoice drafted from the earned
   lines; pay early, or ask the vendor to honour a missed discount; the order sheet filled from the line; a submittal
   chase; the reply to the client; the Friday update drafted from the week's logs, progress and photos; an escalation
   in the Standard's format; offering work to a person with room. Every drafted message is a `DB.outbox` draft (it
   waits on the named person's Approvals; nothing is sent by the checklist); every record fix opens the app's own
   sheet, where the person commits it.
4. **A task for the right person, with a due date and why.** `rsTask` through `crCreateTask` (the one creator),
   `source.specialist` naming the finding; the person comes from the line (`RS_WHO`: the controller keeps the books,
   only the owner approves part of a bill, procurement owns orders, the PM owns the job, with the job's lead for a PM
   line); the due date from the Standard's principle (safety and law today, money leaks and escalations the next
   working day, the rest two). A drafted message is itself the task (it sits on the person's Approvals), so no second
   item is made.
5. **Follow-up until the record is fixed.** `rsSweep` re-reads each open finding's detector at most once a minute
   while the app is used, and on the app day: when the record no longer shows the problem the case closes, its task
   closes with the note "the record is fixed", and a money line adds a row to the savings ledger. A task ticked while
   the record still shows the problem reopens, with the reason written on it.
6. **Learning.** A dismissal needs a reason; it is kept by form (line, record, amount), so it never returns in that
   form and does return if the amount changes. An approved fix that drafts a message proposes itself as the default in
   Company › Changes (`DB.changes`, kind rule, `company.spDefaults.<line>`); once the owner approves it, the checklist
   drafts that message the moment the finding appears, still as a draft a person sends.

## Thresholds (adjustable, enforced)
Owner: Ask › Brain Settings › Thresholds the Checklists Enforce. Changing one drafts a change in Company › Changes;
`mtChangeApply` writes `DB.company.spThresholds` when it is approved. Three quotes ($2,500, and every subcontract at
any amount; an issued PO under three quotes records `po.q3` with who, when and the count, and an audit line); the
unbudgeted-cost escalation ($1,000, to the owner's Needs Your Hand, in the escalation format); the milestone slip (2
working days, same); client acknowledgement (2 business hours); the Friday update (drafted for the PM on Fridays,
`rsFridaySweep`, and on demand from the finding).

## Savings ledger (§1.30)
`svRows()` reads `window.SV_SOURCES`: short-pays held to the PO (Payment Check / over PO), duplicates disputed or
voided, discounts taken (paid inside the terms), RFQ awards under the first quote, and findings the checklist raised
that were fixed on the record. Another lane pushes a function returning `{key, kind, amount, date, by, what,
evidence}`. Monthly, year to date, by source, by person; the owner's shares to the wage, bonus and charity pools; a
bonus credit per row only the owner approves. Ask reads it (`EQ_TABLES.savings`, a money table: owner and controller).

## Workload (§1.32 #2)
`wlRows()`: open and overdue tasks per person (tkAll), hours in the last 7 days (the clock), median hours to answer a
field question. Overloaded: three or more overdue, or eight or more open and twice the firm's median. The proposal names
the person with room in the same role group (the office for the owner); the manager (owner, PM for the field, design
director for design) approves, and the tasks are offered as hand-offs that stay with their owner until accepted.

## Proof (§1.31): `tests/specialists_test.py`
The planted bank, the six steps as the people do them, thresholds, savings, workload, privacy (mail and money, through
findings and Ask), and the screens on desktop and phone. Numbers are in the lane report.

## What is not done (said plainly)
- Lines with no detector stay Not Checked: bills paid before approval outside the Payment Check, retainage due, WIP
  movement week to week, committed cost not relieved, unexplained budget variances, quality checkpoints, the
  selections schedule's completeness, margin slipping (cost intelligence), and the crew's and driver's lines.
- The journal-entry fix (a reclass of job spend coded to overhead) is not drafted: the line opens the Ledger.
- The revised-PO fix is an option in the sheet, not drafted.
- The three-quote rule is enforced as a recorded exception and a checklist finding, not a block at issue: urgent orders
  still go out. Recommendation for Alan: keep it a record, not a block, below $10,000.
- The client acknowledgement timer is measured (portal questions and client mail in your own mailbox) and shown on the
  checklist and the Standard Watch; there is no countdown drawn on the Inbox rows yet.
- Who approves a Company › Changes item is the existing rule (owner, PM, coordinator, design manager can approve
  there); the checklist's defaults and thresholds should be owner-only. Recommended next: an owner-only flag on
  `DB.changes` items with `source: specialist`.
- The checklist runs in the browser. The always-on server half (§1.32 #5) is the platform's.
- Bonus attribution is per saving row; there is no payroll export of the bonus pool.
- Response time in workload is measured on field questions only; mail response times need per-person mail on the
  hosted copy.
