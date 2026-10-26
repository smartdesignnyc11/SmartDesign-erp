# Round one: accounting (Billing seat, with the books part of J10)

Sources: my diaries (`sim/runs/r1_acct/diary/u_billing.md`, `sim/runs/r1_live_acct/diary/u_billing.md`) and the conductor's notes (`docs/loop/round1/turns/acct_t1.md`, `acct_t2.md`).

Four turns: local turn 1 on the demo day, Fri 9/4 (phone then desktop, 40 actions); local turn 2 (desktop, about 120 actions over 150 minutes); the page walk (both devices, about 75 actions); one live turn on the hosted site (about 33 actions: phone, desktop, phone).

Switch User did nothing, so I could not sign in as the controller. The books part of J10 was done from the Billing seat, which reaches Banking, Bills & Payroll, Spend and Reports, but not Ledger, Controls, Budget or Time & Crew.

## 1. The journeys

**J8, bill the deposit (desktop): FAIL. The invoice is right; the payment is not matched.**
- Result: INV-2026-039 was sent for $22,780 (25% of the $91,120 Ashby contract), no retainage, due on receipt, one business day after signing. It reached the portal and the client chat. No payment has landed, so the referee's "payment matched to the bank line" is open.
- Budget: about 32 taps over two turns against 12; about 25 minutes against 6.
- Where it broke:
  - The signed contract was on neither Today nor the Billing Queue. The contract does not carry its deposit %: its terms say only "Deposit due at signing"; the 25% came from the huddle.
  - There is no deposit invoice. New Progress Invoice creates a record on one tap. I typed 25% into each of 12 SOV lines and zeroed the default 10% retainage by hand.
  - The list row's Send showed $9,702, the half-finished amount.
  - Send reported the mail as "in your mail app", and my Sent box was empty.
- What I checked: the total against the contract, retainage $0, status Sent, the portal line, and that nothing internal printed.
- Phone (turn 1): fail. The cap hit with the draft half filled, and Ask turned "draft the deposit invoice" into a client email that quoted my internal question.
- Grade 4. To reach 9: a Deposit Invoice action on the signed contract that reads the % from the contract, with the deposit credited back on each progress application.

**J9, bill the progress (desktop): FAIL. Not sent, by my call.**
- Result: INV-2026-040 drafted from the SOV: $12,651 less 10% retainage = $11,386. Framing and electrical are on the foreman's and the PM's measure, each line with its "how we know". CO-2026-001 is SOV line 14.
- Why I held it: 121 State is billed $66,470 ahead on 7 lines ($131,058 cost-to-cost). INV-038 was a flat 15% on every line, and the deposit booked as percent complete on every line inflates it.
- Missing: the progress editor has no Billable Expenses and no Add Approved Change Order (the plain invoice editor has both). There is no chase control; Ask drafted a mail addressed to "INV-2026-038".
- Budget: about 20 taps against 25, but not sent.
- Also done, and good: the 45 Cranberry design milestone INV-2026-041 ($17,080) took 2 taps from the Bill a Milestone sheet. But Send reset my 9/19 due date to 9/21.
- Grade 3. To reach 9: a G703 with line names, stored and retainage columns; the CO and reimbursables on the application; the cadence set on Send.

**J10, the week's money, books part (desktop, from the Billing seat): FAIL.**
- Bank lines: none matched; none of the 5 proposals was safe. Window Works was paid before approval and waits on the owner; Alberto check 2205 matches AMP-311 only on vendor and amount; the Satish ACH was typed by hand but is queued as a bank line; two Zelles to individuals may be payroll.
- Payroll 8/17-8/28 ($16,040, due 9/1) is not approved and is 88% Unallocated Labor. I escalated to the owner.
- Job cost per line on 121 State: the total row says $75,750; the column adds to $101,694.
- AR $132,125 ties to 1100, and retainage $15,668 ties to 1150. Two-week cash counts $21,350 of Rivera money that never reached the bank.
- Budget: about 30 taps against 30. Grade 3.

**Live turn (hosted site).**
- On the phone I drafted the 45 Cranberry at-filing milestone INV-2026-039 ($17,080) and its memo: 8 taps, 2 wasted (a dead Draft tap and a Save that did not land the first time).
- It was on the desktop about 28 seconds after the phone's save, memo included, with "Synced" showing. The phone never shows its sync status.
- I added an internal note on the desktop; it reached the phone at once. Nothing was lost.
- I could not type into the line descriptions on the live desktop: each try returned "no longer on the screen". Print / PDF showed nothing.
- I held it unsent: Rivera has $21,350 of payments the bank never saw.

## 2. The questions, answered for my day

1. **Information I could act on quickly.** Yes for the Billing Queue's "ready and why", the billed-ahead banner, Payments' "Recorded, Not Yet in the Bank" box and AR's tie-out. No for cash: collected, Cash Today and safe to spend all include money the bank never saw.
2. **Right place, wrong place, missing.** Wrong place: collections (the Receivables aging) is in Reports, not Billing. Cost Not Billed, the AP inbox and Hours & Payroll are in Spend. Progress vs Plan, the measure I bill on, is in Reports.
   Missing: a deposit invoice; the deposit % on the contract; a due/7/15/30 cadence in the local build (the live desktop Today has a Chase button); SOV line names.
3. **Too much, or not mine.** Billing's "Made Today" panel above the page; Billing > Estimates with stale drafts; Reports > Submittal Log, Daily Log Summary and Cost Library; a dashboard that defaults to the schedule; Banking's seven toolbar buttons.
4. **Sub-pages per job.** The deposit took Estimates, the contract and New Progress Invoice, plus an old invoice to copy the firm's practice. J10 took Banking, three Spend tabs, Accounting, Bills & Payroll and four Reports tabs. The money-out queues should be one page.
5. **Outside the app.** In my head: the 25% deposit, the client's own invoice numbering (their "invoice 2" is our INV-035) and the reminder dates. In my diary: the collections cadence. By hand: my own cover mails, because Send went to a mail app.
6. **Numbers I would act on.** Yes: invoice math, AR and its aging, the Payments bank status, the Bill a Milestone amounts. No: Cash in Bank (Chase lines end 8/31; 14 of 16 September lines were typed); Collected and Cash Today (both include unbanked money); the windows "not billed" figure (four values); Safe to Spend (−$27,486, −$44,566, and $14,724 live); the job cost total row.
7. **Mistakes, and the taps I fear.** My own cover mail dropped digits; I caught it only by rereading. Taps I fear: the list-row Send on a half-finished draft; the blue Send to Client as the first control of a new phone draft; phone Banking's Confirm, which hides what it links; the blue Reverse Payment on a read-only payment sheet; Bring It In on a bill the app itself calls a duplicate.
8. **Hand-offs.** Mails to Alan, Chen and the clients went out. Today did not clear what I had answered: Sarah still showed as past 2 hours after my reply. The signed Ashby contract never told me a deposit was owed.
9. **A new hire.** Could not bill a deposit or set a chase. Could bill a design milestone (the sheet is excellent) and read AR.
10. **Saw what I should not, or missed what I need.** Saw: every vendor payment, including Zelles to individuals that look like payroll. Missed: the Ledger, to drill a figure to its journal; and approved hours for T&M and design billing (only through Spend > Hours & Payroll).
11. **Would I switch tomorrow?** No. Cash the bank never saw shows as collected, and a deposit is not one action.
12. **The AI.** Should have: drafted the deposit from the contract; set the chase; answered all four parts of my Tuesday pack question (it answered one); flagged card buys on client jobs as billable. Should not have: drafted a client email that quoted my internal question, or a mail addressed to an invoice number. It answered 0 of my 4 billing questions well. It stayed inside approval: nothing went without me.

## 3. Findings, by class

**A. Cash with no bank line behind it counts as cash (S1). J8 payment step, J10 cash.**
1. Rivera's $5,000 (7/30) and $16,350 (8/14) were never seen at the bank, yet they count in:
   - the P&L's "collected $191,100" and Cash-basis revenue;
   - Budget vs Actual design revenue ($21,350 exactly);
   - the Cash Forecast's "Cash Today $205,581";
   - Project Profitability's Collected, and the invoices marked Paid.

   Only the Statements coverage line is right ($169,750 of $191,100 bank-backed). Fix: no bank line means not collected and not cash, and the headline carries the flag.
2. Typed lines are treated as bank lines. Satish $7,400, Waterworks and the heat mat are "typed by hand, never seen at the bank", yet they sit in Matches Waiting for Your Confirmation. Every payment reads "Recorded By: not recorded". The blue on a sent invoice is Record Payment; on a payment sheet it is Reverse Payment. Fix: "Find in Bank" instead of a typed payment; who, when and why on every manual entry; typed lines never offered as matches.

**B. One question, many numbers (S1 where it is money someone acts on). J9, J10.**

| Figure | Values | Where |
|---|---|---|
| Windows, bought for the client, not billed back | $13,970 / $20,270 / $24,683 / $13,969 | Billing Queue / Analyst / Client Funds / Progress Billing |
| Billed ahead, 121 State | $66,470 / $131,058 | Billing / WIP |
| Window Works over the PO | $3,800 / $3,300 | Banking and Bills / Vendor Bills Arriving |
| Payables | $0 tile / $16,040 past due | side by side on Reports |
| Card charges with no cardholder | 16 / 18 / 19 | census / Accounting / Spend |
| Receipts to approve | 2 / 6 | Spend / Accounting |
| Receipts | "Missing Receipts 0" beside "No Record Behind 17" | one Spend screen |
| 121 State job cost total | $75,750 row / $101,694 column sum | Reports > Projects |

3. The true windows figure is $10,170 by the app's own numbers ($29,700 delivered less $19,530 billed). The other $3,800 of the $13,970 is the Window Works overage held over the PO. Billing it charges the client for material not delivered and in dispute.
4. The Analyst brief says "$191,100 invoiced" (that is collected) and "$0 payable".

**C. No deposit path (S2, and the cause of an S1). J8 steps 1-3.**
5. There is no Deposit kind and no deposit % on the contract, and a signed contract never reaches the queue or Today. The deposit is billed as 25% complete on every SOV line, with 10% retainage by default; that is what makes 121 State read $66,470 billed ahead. Fix: Deposit Invoice on the signed contract, one line at 0 retainage, credited pro rata on each application, in the queue the hour the contract is approved.

**D. The progress application (S2). J9.**
6. The Schedule of Values' Line column is blank on every row, desktop and phone, and it has no G703 columns (this period, stored, retainage, balance to finish, totals).
7. Nothing client-billable reaches the application:
   - The SOV editor cannot add the approved CO or billable expenses.
   - Card buys on client jobs are not flagged as billable: Waterworks $1,900 on 121 State selections, the $390 heat mat for CO-001.
   - Cost Not Billed leaves out uncoded card lines.
   - The queue's blue is a stored-materials draft on a job where "contract allows billing stored materials" is off.

**E. Collections (S2). J9 last step.**
8. The local build has no cadence, no Draft Reminder and no Last Touch; Ask's chase is a mail to an invoice number. Receivables sits in Reports, not Billing, and retainage receivable has no bucket of its own. On the phone, Receivables cuts off the balances ("$22,...") and drops Promise.

**F. One-tap commits and Send (S1/S2). J8, J9, J10.**
9. These are one tap from going wrong:
   - Send on the list row of a draft (it showed $9,702, half filled).
   - The blue Send to Client as the first control of a new phone draft (live).
   - Phone Banking's match cards drop the target ("Bill AMP-311") and the "possibly already paid" warning, but keep Confirm. S1.
   - Bring It In is offered first on bills the app flags as duplicates: Nemo NT-88412, already paid; a second Window Works invoice for the same $33,500.
10. Send reset a saved due date (9/19 became 9/21); Send goes to a mail app and leaves the Sent box empty; Print / PDF shows no preview, locally and live; the construction footer (retainage, change orders) prints on design and deposit invoices.

**G. Too many queues for the same money (S2, system lens). J10.**
11. The same money-out lines are listed in five places: Banking (whose Needs Category cards repeat its own table), Spend (The Day, To Settle), Accounting's Today's Review, Reports > Review, and Controls (the census counts 94 shared lines).
    - On Banking, Satish $7,400 gets two different answers.
    - Quality Bldg $300 is "matches a record" on Spend and "No suggestion" on Banking.
    - The duplicate dumpster charge (8/21 and 8/22, $1,650 each) is caught only on Reports > Review.

**H. Closing the books (S2). Books by the 10th, J10.**
12. The August close is blocked: the Monthly Pack offers only "Sep 26 (open)"; Reconcile asks me to type an ending balance the imported statement already holds; the Three-Way Tie-Out says "agrees" on AR and AP with nothing to compare; payroll is $0 in the P&L all year and 88% unallocated; Bills say "awaiting bank verification" while Payments says Cleared "yes".

**I. Phone and screen defects (S2).**
13. On the phone: Banking's toolbar collapses into overlapping, unreadable text; "Made Today" fills Billing's whole first screen; Payments drops the In the Bank status; AR's "current" pill is unreadable; there is no sync status (live). Dead taps: the queue row's Draft and the first Save (live), the invoice's More (local, both devices).
14. Spend > To Settle prints raw HTML (`<span class="muted">—</span>`) in the Job column on 14 rows.

**J. The assistant (S2, S1 where it reaches a client). J8, J9.**
15. "Draft the deposit invoice" gave a client email that quoted my internal question, with no amount. "Set the chase" gave a mail addressed to "INV-2026-038". My Tuesday pack question got one of four parts, with the wrong windows figure. Any question with an invoice number in it got the invoice's lines back, not an answer.

**Harness findings (logged, not worked around):** typing by label matches a prefix family ("— 1" also hits "— 10" to "— 12"); control numbers shift mid-batch; the top-bar + New cannot be tapped; Switch User does nothing; the live desktop's line Description fields cannot be typed into; the G702 preview gives one sentence of text.

## 4. The page walk, page by page

I opened 55 of the 55 desktop screens the census lists for Billing (7 of 7 pages), and 12 phone screens across those pages. Ledger, Controls, Budget and Time & Crew belong to the controller and cannot be reached as Billing.

| Page (module > page > tab) | Verdict | Too much, or not mine | Missing |
|---|---|---|---|
| Billing > Billing Queue | keep, my home | Made Today above the page; unsafe blue | deposits due; today's reminders; billed-ahead as a gate |
| Billing > Progress Billing | keep | evidence essay before the lines | the field measure inline; reimbursables and CO |
| Billing > Estimates | move to Sales | stale $825K draft beside the contract | deposit % and terms |
| Billing > Change Orders | keep (approved-unbilled, sent-unsigned) | - | billed to date; days since sent |
| Billing > Invoices | keep | sideways scroll at 1440 | New Invoice; Deposit kind; days late; last reminder |
| Billing > Schedule of Values | keep, rebuild as a G703 | - | line names; this period; stored; retainage; totals |
| Billing > Payments | keep | - | who typed it; In the Bank on the phone |
| Billing > Client Funds | move to Reports > Cash | - | today's bank balance |
| Banking > Needs Review | keep (the books' home) | 7 toolbar buttons; repeats its own lines; Reconcile as the blue | duplicate-charge flag; billable flag; a working phone layout |
| Banking > All, Unreconciled, per account | keep; merge with Controls > All Transactions | the account chip filters inside the status filter without saying so | - |
| Banking > Reconcile | keep | - | ending balance from the statement |
| Bills & Payroll (4 tabs) | keep (controller); read-only for me | - | PO, received and billed columns |
| Spend > The Day, To Approve | merge into Banking | "Missing Receipts 0" beside 17 with no record | - |
| Spend > To Settle | merge into Banking's matches | raw HTML; credits shown as money out | - |
| Spend > Cost Not Billed | move to Billing | - | uncoded card buys for clients |
| Spend > Everything | remove | a $0 draft | - |
| Spend > Cards & Who Spent | keep (controller) | count disagrees: 19, 18, 16 | - |
| Spend > Vendor Bills Arriving | move to Bills & Payroll | Bring It In on duplicates | - |
| Spend > Hours & Payroll | move to Time & Crew | - | the payroll run it feeds |
| Accounting (Today's Review) | merge into Banking | a fourth queue | - |
| Reports > P&L Detail (Accrual, Cash) | keep (controller) | the Cash toggle is sticky across tabs | bank-backed flag on the headline; payroll |
| Reports > Statements; Budget vs Actual; By Month | keep (controller) | Prior Period $0 | - |
| Reports > Monthly Pack | keep | - | August |
| Reports > Three-Way Tie-Out | keep | "agrees" with nothing compared | - |
| Reports > Projects, Profitability, Cost Intelligence, WIP | keep | "pay what the PO allows" on a bill already paid | - |
| Reports > Studio | keep | - | retainers billed and on account |
| Reports > Cost Library, Submittal Log, Daily Log Summary | move to Purchasing and Projects | not for billing | - |
| Reports > Progress vs Plan | merge into Progress Billing | - | - |
| Reports > Receivables | move to Billing as Collections | Record Payment | cadence; retainage bucket; last touch; phone truncation |
| Reports > Payables; Client Statement | keep; link from Billing and Bills | - | - |
| Reports > Cash Forecast | keep (controller) | counts unbanked cash | progress billings after 10/2 |
| Reports > Review (4 tabs); Weekly Flash | merge Review into Today and Banking; Flash for the owner | wrong words in the brief; safe to spend unexplained | - |
| Reports > Build a Report | keep | "due this week" is not this week | - |
| Reports > Dashboard (3 tabs) | keep; make the Owner tab Billing's default | schedule widgets for billing | - |

The five pages I would change first: (1) Receivables, moved into Billing as Collections with the cadence; (2) Banking, made the one money-out queue and fixed on the phone; (3) the Schedule of Values, rebuilt as a G703; (4) every page that counts unbanked cash; (5) the Billing Queue: Made Today, the blue button, one windows number.

## 5. Retest

None this round. It is the first walk; nothing was fixed since.

## 6. Grades

Valid: I opened 55 of 55 screens (100%) of my main modules, Billing and Accounting, on the desktop, and all 7 pages on the phone.

- **Phone: 4/10.** Today, the milestone sheet and sync work. But Banking is unreadable and its Confirm hides what it links, AR balances are cut off, and the first control on a new invoice is a blue Send.
- **Desktop: 5/10.** The invoice editor, the AR tie-out and the billed-ahead checks beat QuickBooks. But there is no deposit path, the SOV has no line names, and the cash headlines count money the bank never saw.
- Live turn, for reference: phone 6, desktop 7. Sync was under 30 seconds both ways and nothing was lost; the phone's dead taps and missing sync status held it down.

DONE: report written
