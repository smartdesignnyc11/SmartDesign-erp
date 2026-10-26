# Round one: triage

Chief of staff, 2026-10-26. Sources: the four expert reports (`owner.md`, `pm.md`, `procurement.md`, `accounting.md`), the conductor's turn notes (`turns/`), `docs/JOURNEYS.md`, `docs/PROCESS.md`, `docs/CONSOLIDATION.md` and `docs/IMPROVEMENT_LOOP.md`. App findings are in section 1; harness findings are kept apart in section 3.

**What this rests on, and what is unsure**
- **The build.** The experts worked the build with the estimate lane (180af0b; live d13b78b2) in local worlds resumed from the walk's checkpoints, plus one live turn each. The estimate follow-ups (9b1bd79) merged after their turns.
- **Two built lanes are not on master.** CONSOLIDATION's Coming Up lane (`worktree-agent-a0204da138d2230af`, 23 commits, last 10-23) and one-place lane (`worktree-agent-a56253bb391c1bedf`, 23 commits, last 10-24) are built but unmerged, so the experts judged a build without them. Findings those branches claim to fix are marked; the claims are unverified.
- **Local Ask never called the model** (instrument test, 10-26). Its rules answered, so local assistant findings are about the rules; the live turns used the live assistant.
- **Gaps.** The client expert (the portal) did not run, and no realism-judge verdict appears in the reports, so no turn was discounted.
- **Checks green beside the findings.** On this build the last full walk failed 53 of 81 checks, and the counts lint read 0 flags beside the twenty-odd count pairs below (class 16).

**Journey steps** are the clauses of each journey in JOURNEYS.md, in order, as the experts read them:
- **J1:** .1 lead from the mail; .2 walk-through noted; .3 won into one client; .4 a project under it, with notes and the next step's owner.
- **J2:** .1 estimate on the project, right client; .2 twelve full lines with allowance, sub and fee; .3 margin reviewed; .4 sent, in mail and portal.
- **J3:** .1 field issue to a CO with cost, margin and days; .2 sent within 48 h; .3 approved on the portal; .4 on the next invoice.
- **J4:** .1 three weeks of schedule; .2 budget, committed and actual per line; .3 open COs, RFIs, submittals, decisions; .4 client update sent.
- **J5:** .1 one RFQ from several lines; .2 three vendors reached; .3 quotes recorded and levelled; .4 award.
- **J6:** .1 a PO of several linked lines; .2 a repeat buy on a line; .3 stock check; .4 price against last time and the quote rule; .5 COI, W-9, sent and confirmed.
- **J7:** .1 receipt with quantity and condition; .2 bill matched three ways, held at what arrived; .3 claim open; .4 credit closes it.
- **J8:** .1 deposit invoice from the signed contract; .2 sent; .3 payment matched to its bank line.
- **J9:** .1 from the SOV with retainage; .2 the CO and client purchases on it; .3 sent; .4 chase set.
- **J10:** .1 bank and card lines matched; .2 payroll approved; .3 job cost per line, AR, two-week cash; .4 the owner approves only his.
- **Day:** the start of the day.

## 1. App findings by class

**Severity.** S1 is wrong money, client truth or privacy; S2 is hit by a pro in a normal day; S3 is polish. **Experts:** O owner, P PM, C procurement (Chen), A accounting.

### S1

**1. Cash and "collected" count money the bank never saw.** O, A. Blocks J8.3, J10.3.
- **Where.** Safe to Spend reads −$4,218.94 (local Today), −$27,486 and −$44,566 (accounting's world), $14,724 (live Ask, from parts that subtract to $126,749) and $18,361.27 (live Today ten minutes earlier). The brief says "$184k in the bank, $4.2k short", and Client Funds says $158,856 is ours. Rivera's $21,350 (7/30, 8/14), never seen at the bank, counts in the P&L's "collected $191,100", cash-basis revenue, Budget vs Actual, the Cash Forecast's "Cash Today $205,581", Project Profitability, and invoices marked Paid. Typed lines (Satish $7,400, Waterworks, the heat mat) sit in Matches Waiting for Your Confirmation, every payment reads "Recorded By: not recorded", and the blue on a sent invoice is Record Payment.
- **Why the checks missed it.** Today reads `PRED.safeToSpend`, Client Funds reads `B.trulyOurs`, and the brief and Ask compute their own. The money lane's "no cash without a bank line" (31557d7) never reached the headlines, and the finance cross-check compares ledgers, not a headline against its bank-backed lines.
- **Accept.** As the controller on the desktop and the owner on the phone, open Today, the Cash Forecast, the P&L and Ask "cash for two weeks". All four give one Safe to Spend, with its parts and each account's statement date. Rivera's $21,350 reads "recorded, not in the bank", outside cash and collected. A sent invoice's blue is Find in Bank. A typed line is never offered as a match, and it shows who typed it, when and why.

**2. The deposit and the progress application.** O, P, A. Blocks J8.1, J9.1–2, J4.2, J10.3.
- **The cause is our own code.** A September wrapper strips Create Deposit Invoice from the contract (`docActions`/`docAction` "b3" in `src/app.js`; toast "Deposits are billed as the first progress invoice"). `ctDepositInvoice` and `depositPctOf` still exist behind it.
- **So the deposit becomes progress.** Billing typed 25% into each of 12 SOV lines and zeroed 10% retainage by hand. That books the deposit as work done: 121 State reads billed ahead $66,470 on 7 lines ($131,058 cost-to-cost), INV-038 was a flat 15%, every line stands at 51.67%, and the queue still proposes $12,651 + $13,970 more.
- **Also.** The signed contract reaches neither Today nor the queue, and has no deposit %. The SOV's Line column is blank, with no G703 columns. The progress editor lacks Add Approved Change Order and Billable Expenses. The queue's blue is a stored-materials draft the contract forbids. Card buys on client jobs are not flagged billable (Waterworks $1,900; the $390 heat mat for CO-001).
- **Accept.** As billing on the desktop, the signed Ashby contract is on Today and in the queue the hour it is approved. Deposit Invoice makes one line at 25% of $91,120 with no retainage; the next application credits it, and it never moves billed-ahead. The SOV shows named lines with this period, stored, retainage and balance. CO-001 and the heat mat go onto the application, and the queue proposes nothing on a job billed ahead. Waits on decision 5.

**3. One money question, many numbers.** O, P, C, A. Blocks J4.2, J9.2, J10.3.

| Figure | Values seen | Where |
|---|---|---|
| Windows bought for the client, not billed back | $13,970 / $20,270 / $24,683 / $13,969; true $10,170 (billing $13,970 charges the client the disputed $3,800) | Billing Queue / Analyst / Client Funds / Progress Billing |
| Billed ahead, 121 State | $131,058 / $66,470 / +$156K / $135K and $137K live | Overview, Costs, Chief of Staff / Billing / Projects / live |
| 121 State job cost | row $75,750 against column $101,694; line $100,044 against cost code $101,284 | Reports > Projects; live Costs |
| CO "Additional tile prep" margin | $650 (100%) on $488 cost; true $162; the total is right | Costs |
| Phone Costs, third figure | unlabelled; actual on some rows, margin on others | Costs, phone |
| Others | margin $102K against $103,313; WW over PO $3,800 against $3,300; Payables $0 beside $16,040 past due; the Analyst's "invoiced" is collected; Won This Quarter $511K under every pipeline; funnel 400% | tiles, Reports, brief, Sales > Numbers |

- **Accept.** Every pair joins the counts lint and the finance cross-check. As the PM on both devices, 121 State Costs labels every column, a CO line's margin is its price less its cost, and the total equals its column. Billed ahead is one figure on Overview, Costs, Billing, WIP and Today. As billing, windows not billed back reads $10,170, with $3,800 marked disputed.

**4. Leak flags never reach the lists, and the checks contradict each other.** O, C, A. Blocks J6.4, J7.2, J10.1, J10.4.
- **Three checks call a fraud pattern clean.** WW-2026-118 was paid $33,500 before approval, is $3,800 over its PO, has an expired COI and no W-9, and its bank details changed. Yet the brief says "nothing to hold", Every Chain says "clean", the bill sheet says "three-way match agrees", and live Payments lists it twice.
- **Flags stay on one page.** AMP-311 is missing from Approvals > Bills. Tino's two invoices over PO-2026-047, with $8,000 paid ahead, show on the PO page only. $67,000 paid on a $29,700 PO (live) is a row note, not a hold. Brooklyn Lumber 88412 ($2,140.50, about 5x the price book; a statement shows 88431 unpaid, a possible double pay) is not tied to its need, while Price Watch says $0 above best. Bring It In comes first on bills flagged as duplicates, and the duplicate dumpster ($1,650 twice) shows only on Reports > Review.
- **Accept.** As the owner on the phone, Today and Approvals > Bills list WW-2026-118 and AMP-311 as paid before approval, in the escalation format. As the coordinator, Flagged Orders and Bills on Hold list PO-2026-047. 88412 sits on its Buy Board need with the price check, and Payments lists WW-2026-118 once. A duplicate offers Hold first, and one detector feeds every list and sheet. The one-place branch claims the Approvals part.

**5. Receiving on the phone, and the match.** C, with A on the credit. Blocks J7.1–4.
- **Where.** Phone Deliveries lists Tino and Carlos as "0 lines", and Receive has no quantity, short, damaged or slip photo. On the desktop the quantity starts at the full order and Received is blue, so one tap receives everything and the bill matches clean. A 1 ls PO cannot record one short cabinet, and Report a Problem sits apart from the line. Apply matched the Bedrosians $214.50 memo (8/31) to a card credit dated 8/25; the fix lane refused a bank line dated before its bill, and credits are the same class. Returns ($2,419) and credits hide in FF&E Buying Tools. Partial receiving exists (`rcReceiveSome`, "Save received quantities"), but the phone row never reaches it.
- **Accept.** As the coordinator on the phone, receive one short and one damaged item in 15 taps. Quantities start empty; short and damaged go on the line with a photo, and the claim opens from the line. The bill is held at what arrived. A credit dated before its memo is refused, and the credit closes the claim on Orders.

**6. Records land on the wrong client, job or person.** P, O, C. Blocks J2.1, J1.4, J3.1, J4.3, J10.2.
- **Where.** A job's Estimates, Change Orders and Billing open the firm's Billing page with a hidden `bill-client` filter: New Estimate on 214 Lincoln opened for the Kleins, and both jobs' blue reads "Draft $17,080 - 45 Cranberry St". Every win files "Write the proposal" on 121 State, due after the promised Friday or on Labor Day, and its job cannot be changed. Lenox Field shows 121 State's 9/2 log, Lenox's log books to a 121 State task, and Alberto (16 h) and Alex (14.75 h) are on both jobs on 9/2. Tasks handed to Chen show Alan as owner, and Make a Task made Sarah's question the PM's. On the phone, PO-2026-048 opened PO-2026-041; Today cards land on Messages, and menu entries reopen the last record.
- **Accept.** As the PM on the phone, 214 Lincoln's Estimates shows only its own, and New Estimate is the Ashbys'. A won lead's task sits on the new job, owned by its PM, due on the promised date, and it can be moved. Lenox Field shows only Lenox logs, and over a day's hours across jobs is flagged before payroll.

**7. What the client receives is wrong.** P, O, A. Blocks J2.4, J8.2, J9.3.
- **Where.** The estimate prints "due within 15 days" against our 30-day terms. License # is blank but prints, and a NYC home-improvement contract needs it. The construction footer prints on design and deposit invoices. The cover email goes to Wren only. Send reset a saved due date (9/19 became 9/21). Print / PDF shows no preview. Ask's deposit draft quoted the internal question to the client.
- **Accept.** As the PM, Review and Send previews 30-day terms and the licence number, and refuses while it is blank; both clients are addressed, and nothing internal prints. As billing, a deposit and a design invoice each print their own footer and keep their due date.

**8. One tap from a wrong commit.** A, C, O, P. Blocks J7.1, J8.2–3, J10.1, J10.4.
- **Money (S1).** Send on a half-filled draft's list row ($9,702 of $22,780). A blue Send to Client as the first control of a new phone invoice. Phone Banking's Confirm hides its target and the "possibly already paid" warning. A blue Reverse Payment on a read-only payment. Received with the full quantity (class 5). Approve past "blocks approval" with no override named. A blue payroll Approve that cannot pass.
- **The same class (S2).** "Passed" on unbooked inspections; "Decide" on the client's decisions; "On Site" on every material row; "Confirm Rev 3" from a meeting-note sentence; the blue "Review All New" on 77 messages; the blue "Draft the Renewal" first on the owner's Today; Clear Everything and Turn the Demo On one tap away; the editable "As Of"; a red Delete beside nameless stages.
- **Accept.** Each joins the walk's danger walk (`button_findings` in `tests/cycle_walk.py`). On each device the safe next step is blue, and every commit names what it commits.

**9. "All clear" with nothing behind it.** P, C, A, O. Blocks J3.1, J4.1–3, J10.1, J10.3.
- **S1.** Lenox Costs reads $0 on a running job: 15.5 crew hours and a scaffold never reach job cost, and an owner's own job has no budget path except a client estimate. The Three-Way Tie-Out says "agrees" with nothing compared. Price Watch says "$0 above best" beside a 5x buy. Bills say "awaiting bank verification" while Payments says Cleared.
- **S2.** Materials reads "Ordered" with no PO, and "All on site, Needs You: Nothing" with nothing bought. Lenox Permits says "All clear" while demo waits on ACP-5, a box on Filings that names no job. Overview says "At risk" while Schedule says "on target". A shortened duration shows a 2-day slip as "−3 working days". "We owe the client 0" shows with five decisions out, and "CO within 48 hours: 0" while two extras have no CO.
- **Accept.** As the PM, Lenox Costs shows the labour and the scaffold, and Permits shows ACP-5 holding demo. A shortened duration warns and names who absorbs it, and Overview and Schedule give one verdict. As the controller, the Tie-Out says "nothing to compare" when nothing is compared.

**Privacy.** No leak was found. One to check (A): billing sees Zelle payments to individuals that may be wages. If they are, billing should see a payroll line, not the person's pay.

### S2

**10. The coordinator cannot finish her own RFQ or PO.** C. Blocks J5.1–4, J6.1, J6.3–5.
- **Where.** Ask for Quotes commits with no form and locks the RFQ in Foreman Review: no Edit, Send, Cancel or Chase, a duplicate cannot be killed, and Angel gets no nudge. Lines are "1 ls" with no item quantities, need dates are assumed (9/11 against 9/8), and the RFQ says "No material budget" while Cost by Line shows one. The Order sheet takes one item. The line link is lost from the board, and "not covered" stays stale. A $2,548 PO went out with no three-quote prompt and no price against last time. Ship to reads Office in the header and Job site in the field. The board reads "At the shop: none" while the warehouse holds the items, and 214 Lincoln is half on it with no order-by dates. New Vendor takes 7 steps, three times.
- **Accept.** On the desktop, one RFQ from three lines, with quantities and schedule need dates, reaches three vendors while Angel's check runs beside it, and she can cancel her own duplicate. On the phone, one multi-line PO keeps every link and shows the stock, the last three prices and the three-quote prompt before Issue. Decision 4.

**11. The road from inquiry to job.** O, with P on Project Settings. Blocks J1.3–4.
- **Where.** With no Set Up the Job before Won, two unsigned deals had to be called won ($301K). Won makes no project, and the project form starts empty. Project Settings has no PM, notes, address, BIN or LPC fields. There is no un-win. It took 18 actions and 45 minutes from the Won sheet to a project with notes.
- **Accept.** As the owner on the phone, Set Up the Job makes one client and one project, with the address, notes and PM, inside 15 taps. The deal stays out of Won until signed. Decision 2.

**12. Mail and calls are not linked to people, and forms start blank.** O, A, P, C. Blocks J1.1, J5.2, Day.
- **Where.** New Lead starts blank after the inquiry was read: 13 of 19 actions were typing. Leads say "no first contact" after the reply went out. Today offers "Add Wren Ashby as a lead" after she became a client. Last Touch reads "—" on every client. Sarah still shows past 2 hours after billing replied. The Lenox tenant complaint is only in Mail, and the vendors Alan named are not on file.
- **Accept.** As the owner on the phone, New Lead from the mail is filled, with the duplicate check shown. After the reply the lead shows first contact, and Today drops the 2-hour item.

**13. Send does not send.** P, A, C, O. Blocks J2.4, J5.2, J6.5, J8.2, J9.4.
- **Where.** The estimate offers only Open in Mail App, with "print to PDF". The invoice "is in your mail app", and the Sent box is empty. RFQs read "not sent yet" after six went out by mailbox. The PO email has no To and no Send. The COI and W-9 requests sit unsent, opening "Hi Window,". An SMS reads "Sent" while texting is not set up.
- **Accept.** Send records sent, to whom and with the attachment, and the portal holds the document. A channel not set up says so. Decision 1.

**14. Save status, dead taps and redraws.** All four. Blocks J2.2, J10.4.
- **Where.** The phone shows no save or sync status, and the desktop shows "Synced" beside "Unsaved Changes". "Had not saved is back" appears after "All changes saved". A library match changed a unit from ls to ea, and sync redraws ate three taps. First taps went dead on Approve, Ask for Quotes, Draft, Save, More, and Review and Send. Commits held by the COI and W-9 gave no toast. Sync itself took under a minute and lost nothing in four live turns.
- **Accept.** On each device, edit and lose the signal: one status reads unsaved, saving, or saved to the team with the time. Every commit toasts its result with Open, and a match never changes a typed unit.

**15. Too much reaches the owner, and what he needs is buried.** O. Blocks J10.4, Day.
- **Where.** "Payments above $0" sits against "POs above $10,000". Crew hours, a $17,080 design invoice, vendor creation and brain builds (a tab named "Changes") reach him. The assistant's rules sit in five places, and Plugins and Connections disagree on Gmail. Payroll arrives after pay day, blocked, with no hours register. Today opens on the LLC renewal, while the bank balance, quiet deals and clients waiting are five taps deep.
- **Accept.** As the owner on the phone, Today holds only what only he acts on, with cash on one line. Limits are set in one place. Payroll arrives before pay day, already split. Decision 3. The Coming Up and one-place branches claim the Today order and the Chief of Staff fold.

**16. One label, many counts, and filters that stick.** All four. Blocks Day, and J6 on the phone.
- **Where.** Approvals 33 against 32 (live 39 against 36). The owner's workload 4, 19 or 37; findings 79, 19 or 21. The PM's Today 16, 40 or 19 + 21; Today live 42, 50 or 43. Late on 121 State 15, 5 or 17. Buy Board chips recount inside the active chip. Receipts 2 against 6; cardholders 16, 18 or 19; "Missing Receipts 0" beside 17 with no record. One pipeline filter is shared by three pages, so Sales read "All clear" with six deals open. A desktop chip strands the phone Buy Board at "2 of 41".
- **Why the checks missed it.** The counts lint passed with 0 flags on this build.
- **Accept.** Every pair joins the lint. As each role on the phone, the rail, tab, tile and Ask agree, and no filter carries to another page. The one-place branch's "one number 8 to 0" covers the map's pairs, not these.

**17. The PM's missing records.** P, O. Blocks J3.1–3, J4.3–4.
- **Where.** There is no RFI record or log, and no designer route from the Answer sheet. No client update is drafted from the week's logs and photos. The CO list has no days, margin, signed date or "work started before signature", and the CO clock does not start when the extra is found.
- **Accept.** As the PM on the phone, Write Change Order from the joist item makes a priced CO with days in 20 taps. The Friday review opens an RFI log and drafts the update.

**18. Ask reads the record back instead of answering.** All four. Blocks J1, J2.2, J5, J8.1, J9.4, J10.3.
- **Where.** It drafted no lines from a pasted takeoff. It did not act on "notes to the project, a task to Alan". It answered one of four parts. An invoice number in a question returns the invoice, and "how do I cancel" returns the record. The chase went to "INV-2026-038". Locally the rules answered and the model was never reached (the fifth gap, DECISIONS 10-26); the live misses (cash $14,724; RFQ-2026-001 left out) were the model's.
- **Accept.** Each journey's question bank goes to Ask. What the rules cannot answer reaches the model, and an instruction becomes proposals with buttons.

**19. The phone and the screen standard.** All four.
- **S2.** The opportunity page scrolls sideways. New Opportunity overlaps the attention line. Stages read "None, None, Value". The phone Banking toolbar is unreadable. Receivables cuts off balances ("$22,..."). The phone job Tasks page loses the job strip. Phone rows drop insurance, location, amount and ETA. Permits and Invoices scroll sideways at 1440.
- **S3.** Obligations prints "1/10/2027/27". Raw ids and raw HTML show (Spend > To Settle). Events and mails are duplicated. Role pickers are labelled "Timezone". "Every dollar matters" leaves out charity.
- **Accept.** The screen-standard lint at 390 and 1440 on each page named, and a person reads each one on the phone without sideways scroll.

## 2. Page verdicts, tallied

| Page | Owner | PM | Procurement | Accounting | Item |
|---|---|---|---|---|---|
| Estimates (Sales, Billing, the job) | remove from Sales; Proposals | keep, as the job's own page | - | move out of Billing | CX1 |
| Change Orders | move to the PM | keep, as the job's own page | - | keep in Billing (approved, unbilled) | CX1 |
| Billing Queue, Progress, Invoices, SOV under Sales and each job | move to billing | move to billing, or scope to the job | - | keep in Billing | CX1 |
| Client Funds | move to the controller | - | - | move to Reports > Cash | CX2 |
| Deliveries and Arriving | - | off the PM's menu | one page; Arriving folds in | - | CX3 |
| Materials, Buy Board, FF&E Buying Tools | - | Materials is the coordinator's | merge into the Buy Board | - | CX4 |
| Money-out queues: Banking, Spend, Today's Review, Reports > Review, Every Chain, Connections' reconcile | Every Chain and reconcile to the controller | - | - | merge into Banking | CX5 |
| Reports under the wrong role: Cost by Line and Analysis (Purchasing); Cost Library, Submittal Log, Daily Log Summary (Reports) | - | - | move out | move out | CX6 (one class, different pages) |

**Each item, against CONSOLIDATION.md**
- **CX1. One home for each money document, scoped by job.** Estimates and Change Orders become the job's own pages, with the client from the project; Billing lives under Billing with a job filter; Sales keeps Proposals. **Not planned** (2.1 covers Sales, Projects, Drawings and Design). It is lane 3, and it removes class 6's root.
- **CX2. Client Funds folds into the controller's cash report,** with one cash line on the owner's Today. **Not planned.** It goes to lane 1.
- **CX3. Deliveries is one page.** **Planned** (2.1), and partly built on the unmerged one-place branch.
- **CX4. The Buy Board is one list, with Materials as its job filter.** **Planned** (2.1), and the branch claims it. **New:** returns and credits move to Orders (lane 2).
- **CX5. Banking is the one money-out queue.** **Planned in part** (2.1 moves bank matching to Banking). **New:** Spend, Today's Review and Reports > Review fold in.
- **CX6. Each report lives with the role that acts on it.** **Not planned.** It waits until the journeys pass (rule 3).

**One expert only** (re-walked next round, not items yet):
- **Owner:** Approvals into Today; Chief of Staff split (planned); Company > Company removed; Meetings to the PM.
- **PM:** Filings into Permits; Selections into Decisions; Route, Project Board and Design off his menu.
- **Procurement:** Prospects, Sourcing Research and Performance into Vendors; Price Watch split.
- **Accounting:** Receivables into Billing as Collections; Progress vs Plan into Progress Billing; Hours & Payroll to Time & Crew; Spend > Everything removed.

## 3. Instrument findings (the harness, not the app)

1. **The walk is not JOURNEYS.md's.** Walk J1 is J1, and J1b is an extra. Walk J2 and J3 are J2's lines and send, and walk J4 (the signature and SOV) is no journey. Walk J5 and J6 together are J5, walk J7 is J6, and walk J8 is J8. Not walked: J3, J4, J7, J9 and J10. Step caps are not JOURNEYS.md's budgets (J1: 40 against 15 taps). `sim/cycle.py` already has C20–C24, C32–C34, C40–C42 and C50–C53, but the walk never drives them through the screens. So N of 10 cannot be measured today; this round's 0 of 10 rests on the experts.
2. **The worlds lacked the events.** Nothing was delivered (J7 unreachable), the joist extra sat answered with no CO, and the signed contract made no queue event. Stage each journey's event at its checkpoint.
3. **The action cap counts each step inside a do.** 40 actions cannot hold J1 on the phone (two 8-step forms take 16). The prompts now say so (3bb430b), but the cap stands. Set it from the journeys' tap budgets.
4. **The 8-picture cap ran out in page walks** (owner, turn 2, 10:29). Page walks should use the census shots where unchanged, with the cap applied to journey turns only. Measure first: a desktop picture is 1.7k tokens.
5. **A sheet the reader could not see.** The Skills sheet stayed on top for about an hour: unlisted, `back` did not close it, and taps went through. It is the same class as Pilot 2 and 3's "Add Line Item does nothing". The reader should list every open sheet and overlay top-down and refuse taps under one.
6. **Taps by number did nothing; by label they worked** (Note, Meeting, Convert, Closed Won). Toolkit or app is unconfirmed; replay on an idle machine.
7. **Label matching hit a prefix family.** "This Period % — 1" also matched lines 10 to 12, and one label matched 12 fields. Match the exact label first.
8. **Control numbers shift mid-batch.** The app side is class 14. In the toolkit, number by a stable key, not by position.
9. **Controls the toolkit could not reach.** The top-bar + New cannot be tapped; the live line Description fields read "no longer on the screen"; Print / PDF and the G702 preview give one sentence. Toolkit or app is unconfirmed.
10. **Switch User did nothing,** so accounting never sat as the controller. J10's books (Ledger, Controls, Budget, Time & Crew) are unwalked. A controller world and account are needed.
11. **The shared QA workspace** told the owner he "just created INV-2026-039", another expert's draft. Attribute records by creator, or give each live expert a workspace.
12. **Unconfirmed.** The owner's live "desktop unusable" ran at load average 17; re-check idle redraws on an idle machine. Live figures come from another dataset. The PM's turn 1 followed his role file, not JOURNEYS.md (fixed in turn 2).
13. **The cost.** About 3.3M tokens for the expert turns: 0.8M per expert, against the runbook's 0.6M and IMPROVEMENT_LOOP's 0.4M. Plan the next round at this measured rate.

## 4. The lanes to run first

At most two at a time. `src/app.js` (about 200k lines) is in every app lane, so "never sharing files" holds for the module files only. Inside app.js each lane keeps to the functions named, and I check the hunks for overlap before the second lane starts. Each lane starts from its failing walk step and ends with the walk on both devices, the fast tier and the month on its final head.

| Order | Lane | Starts from (failing steps) | Classes | Files, as far as the reports show | Beside |
|---|---|---|---|---|---|
| 0 | **The walk becomes JOURNEYS.md's** | Instrument 1: N of 10 cannot be measured | Instrument 1–11 | `tests/cycle_walk.py`, `sim/cycle.py`, `sim/page_tools.js`, `sim/server.py`, `sim/turn_prompt*.md`, `sim/world_book.json` and the day plan, `tests/harness.py`; no `src/` | Lane 1 |
| 1 | **Billing and cash truth** | Walk J8 (the deposit is not in Ready to Bill); J8.1, J8.3; then J9.1–2 and J10.3 once lane 0 adds them | 1, 2, 3's money rows, 7's invoice parts, 8's billing taps, 5's credit-date rule, CX2 | `src/p2money.js`, `src/reports.js`, `src/clientdocs.js`, `src/livejobs.js`. In app.js: the b3 `docActions`/`docAction` wrappers, `ctDepositInvoice`, `depositPctOf`, `sovLinesFor`, `ctProgressInvoice`, `iaSovHtml`, `billingRows`/`billingNeeds`/`billingSuggestions`, `safeToSpend`/`PRED.safeToSpend`, `B.cashToday`/`B.trulyOurs`, `bfRecon*`, payments. Not `today2.js` (Today reads `PRED.safeToSpend`) | Lane 0 |
| 2 | **Receive, match and the flags** | J7.1–4 (after lane 0); walk J6 (no price check against PO-2026-041) | 5, 4, 8's purchasing taps, stock and price on the row (part of 10), CX4's returns | `src/buyboard.js`, `src/p0money.js`, `src/subs.js`, `src/phonerows.js`. In app.js: `procReceiveModal`, `rcReceiveSome`, `fReceive`, `dlDeliveriesFor`, `deliveryProblem`, the PO page, Flagged Orders, Bills on Hold | Lane 3 |
| 3 | **The job's money pages and the right record** | J2.1 (wrong client), J3.1–3, J4.2–3 | 6, 17's CO fields and clock, 9's job parts, CX1 | In app.js: the `renderBilling` shell and `bill-client` filter, the Estimates list and New Estimate, the Change Orders page, the job's Costs, the task sheet's job. After lane 1 (both touch `renderBilling`) | Lane 2 |
| 4 | **Inquiry to job** | Walk J1 (over budget), J1.3–4 | 11, 12 | In app.js: the lead, the opportunity, Close as Won, Project Settings; `src/specialists.js` for mail to contacts | After decision 2 |
| 5 | **The coordinator's RFQ and PO** | Walk J5 (60 taps against 30), J6.1, J6.4–5 | 10, 13's RFQ and PO send | In app.js: `rfq*` and the PO page; `src/buyboard.js`. After lane 2 | After decisions 1 and 4 |

**Why lane 0 goes first.** Progress is the walk (rule 10), and a lane starts from a failing walk step (rule 2). Five of the ten journeys have no walk step, so lanes 2 and 3 cannot start honestly without lane 0. Lane 0 touches no `src/` file, so it runs beside lane 1, whose J8 steps already fail in the walk.

**After these.** Class 14 becomes one save-status component (`src/w1trust.js` and the save path). Class 18 (Ask reaching the model) is in `src/assistant.js` and `src/specialists.js`, after lane 1. Class 19 folds into each lane's screens.

**The two built branches** (the main session's call, not Alan's).
- **Measure first.** Once lane 0 lands, run the new walk on master and on master merged with each branch: machine time only, under rule 6.
- **Merge or drop.** Merge each one that holds or moves journey steps and keeps the month, in the slot after lane 1, because both touch Today and the counts (classes 15 and 16). Drop any that does not, and fold its ideas into later lanes.
- **The dry merge.** Its conflicts are in `build.py`, `menu_test`, `seed_guard_test`, `speed_test` and `baseline_test`, plus `styles.css` and `docs/ARCHITECTURE.md` for Coming Up. `app.js` merges cleanly, but `today2.js` (10-25) came after both branches, so a person re-checks each role's Today on the phone.

**Usage.** A lane is 0.5 to 1M tokens, so lanes 0 and 1 are about 1 to 2M. The next expert round is about 3.3M at this round's rate: warn Alan before it.

## 5. What Alan must decide

1. **Send from the app.** Recommend: when a person presses Send, the mail goes from their own Google account through the app and is recorded as sent, with the attachment and a portal copy. Vendor RFQs and POs go from one purchasing address on the firm's domain; which address is still his to name (BACKLOG §5 item 7). Nothing goes without a person pressing Send. Blocks J2.4, J5.2, J6.5, J8.2.
2. **Won means signed.** Recommend: Set Up the Job from the opportunity makes the client and the project before signature. Won comes only with the signature, and Won This Quarter counts signed deals only. Blocks J1.
3. **What reaches him.** Recommend: payments that match their PO and receipt go to the controller. He gets the exceptions (bills paid before approval or over their PO, a bank-detail change, a first payment to a new vendor), POs over $10,000, overages over $1,000 (already set), and payroll, split by job, before pay day. Hours and billing drafts go to the PM and the controller. It is set in one place, replacing "payments above $0".
4. **The foreman's RFQ check runs beside the RFQ, not as a lock.** Recommend yes: the coordinator sends, Angel's notes arrive before the award, and she can cancel her own duplicate. Blocks J5.
5. **The deposit is its own invoice.** Recommend: the estimate's terms carry the deposit %, 25% by default (billing's reading of the firm's practice), billed at no retainage and credited pro rata on each progress application. This reverses the September design ("no deposit invoice; the first progress bill is the deposit"), which is why 121 State reads $66,470 billed ahead. Blocks J8 and J9.

## 6. For the other docs (text only; not edited here)

**The scoreboard row for `docs/IMPROVEMENT_LOOP.md`.** Grades are phone / desktop. Journeys are by the experts, because the walk does not yet measure JOURNEYS.md (instrument 1).

| Iteration | Date | Phone | Desktop | Owner | PM | Procurement | Accounting | S1 / S2 open | Cost |
|---|---|---|---|---|---|---|---|---|---|
| 1 (round one; build 180af0b, live d13b78b2) | 10-26 | 0 of 10 | 0 of 10 | 5 / 4 | 5 / 6 | 4 / 5 | 4 / 5 | 9 S1 classes / 10 S2 classes | about 3.3M (expert turns) |

Live turns, for reference only: the owner 6 / 3 (the desktop is unconfirmed, on an overloaded machine), the PM 6 / 7, accounting 6 / 7.

**The retro line for `docs/PROCESS.md`.**
- **10-26, round one.** What cost time without a result: five journeys the walk does not check and the worlds could not stage (no delivery for J7, no controller seat for J10); caps that cut the journeys (40 actions, 8 pictures); an hour behind a sheet the reader could not see; and experts re-finding what two built, unmerged lanes claim to fix. The rule that changes (rule 4): the dry run tests the instrument against the whole round, not one turn. Before a round, the walk covers every journey the experts are graded on, each world holds the event and the seat its journey needs, and no built lane sits unmerged.

## 7. Added by the main session after the deploy
- **S1 candidate, sync: simultaneous edits not merged.** `platform/test/live_app_test.py` 'simultaneous edits: the office has both' and 'the phone has both' failed in 2 of 5 runs on 10-26 (an edit on each device at once; one did not reach the other within 60 seconds). Intermittent is still real (PROCESS.md: flake is not a root cause). Owner: a sync lane (public/cloud.js), after lanes 0 and 1. Acceptance: the two-device edit check passes 20 runs in a row.
- **Instrument:** the screen walk under heavy load gives false failures (J4 phone failed with load average 17 and passed alone). The walk never runs while expert worlds are up.
