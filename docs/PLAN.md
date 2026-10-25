# The plan: everything we said we'd do

This is the one list. The chief of staff keeps it current on every ask, lane report and merge. Details live in the BACKLOG sections named. Status words: **Running** · **Next** · **Queued** · **Waiting on Alan** · **Later** (deferred by Alan) · **Done**.

Last updated 2026-10-21, later the same day. The information map merged (42cf9fd) and the four role experts are done. The consolidation plan (`docs/CONSOLIDATION.md`) waits on Alan's yes. A fix lane is running on the bugs that are wrong today, and the PO gates are built. Week 4 is merged on master (af76462); the full net and the deploy are pending.

## 0. Usage rule (Alan)
- Warn before any heavy step.
- Don't start a big round when weekly usage is above about 60%.
- One build lane is roughly 6–10% of a week's allowance. The lean pilot is about 2–5%.

## Pilot 3: the business cycle (Alan, 10-25: "I don't know how much I trust the pilots")
Pilot 2 created about 77 records in three days, no delivery, no report, no check of spend against an estimate line. Pilot 3 is rebuilt so that cannot happen again:
- **Required work per role, verified by the referee in the data:** one new job from lead to estimate (8+ real lines) to contract and SOV; RFQs from estimate lines to three vendors; POs from the lines; delivery short and damaged; bills matched three-way; bank and card lines matched; deposit, progress invoice with retainage, a billed CO, payment matched; payroll; the PM's weekly job review in Projects.
- **Planted leaks:** a PO over its estimate line, a bill over its PO, an item already in stock, a price higher than last time, a client purchase on the card not billed back. Each is reported as caught by the app, caught by the person, or missed, with the dollars.
- **Reports:** the PM, controller and owner answer job-cost-per-line, over-budget lines, unbilled work, unbilled reimbursables, cash and AR from the app's reports; answers graded against the referee's figures from the raw records.
- **Routine and coverage:** each role's standing work in its main module; a role that opens under 60% of its module's pages gets "not a valid grade".
- **The live assistant** through `/api/`, multi-recipient mail, document measures of what reached the person.
- **Status:** harness lane building (sim/ only). The run needs the Projects census and Alan's go on usage (estimate in the lane's report).

## Module census (Alan, 10-25: "did the role experts check each module and its sub pages?")
Not yet. Pilot 2 judged the pages used for the work, not every module page by page. Recommended, Projects first to measure:
1. **Machine census** (no model usage, about 25 minutes): `tests/ia_map.py` on the current build, extended to the job page's own sub-pages. Per module, role and device it lists every page and sub-page, its sections, the records each shows and where the same record shows twice.
2. **Expert walk per module:** the role expert who lives in it plus the information-architecture reviewer, with the census in hand, open every page and sub-page on the phone and the desktop and judge layout, what is on it, what is missing, what is duplicated, what should merge.
3. **Module map** in `docs/modules/<module>.md`: pages, sub-pages, what lives where, the recommended structure, and a mockup for Alan's yes where the structure changes.
Modules: Projects (the job page and its sub-pages), Sales and clients, Estimates, Billing, Purchasing, Accounting (Banking, Bills, Ledger, Reports, Controls), Field and Site, Time and Payroll, Design, Today/Tasks/Messages, Company and Settings, the client portal.
**10-25: Alan said start with Projects.** The machine pass is running on its own branch.
**Pilot 3 harness, from this:** each role gets its routine (the standing daily and weekly work in its main module: for the PM, every job's look-ahead, budget against actual, open COs, RFIs and submittals, decisions and the weekly client update) on top of the events; longer PM and owner turns; a coverage measure per role (pages of its main module opened, out of the census's list) that fails the pilot below a floor.
Cost: not measured. On Pilot 2's 82k tokens a turn, about 0.5–0.8M a module, 6–9M for all twelve, the size of one pilot. Projects goes first and its measured cost is reported before the rest.

## Pilot 2 (Alan, 10-25: "run Pilot 2 after the phone lanes"; UI/UX on phone and desktop)
- **Harness ready** (e47fbd4, selftest 55/55): Pilot 1's 3 days plus 30 events across the firm (prospect to client, estimate, contract, deposit and progress invoices; two COs; a PO received short and its bill held; clock in and out to payroll; the portal; hand-offs; Meeting Mode). Every office role works on the phone at least once a day; the referee checks every tap; each expert grades phone and desktop separately; cost recorded per turn.
- **Runs** when the taskfix and phonerows lanes merge: day 1 alone, its measured cost reported, then days 2 and 3 and both workshops. About 20 agent turns a day; the estimate of about 20M processed tokens rests on an assumption day 1 will measure.
- **Watch:** winning a lead may create a duplicate client named after the opportunity (unconfirmed); a lumber yard is still not a vendor on file.

## Procurement: the next module the team adopts (Alan, 10-24)
"It needs a full review and major changes." Steps, one lane at a time after the mockup-match lane:
1. **Review** (running, no browser): the last three meeting transcripts for what goes wrong in buying (kept outside the repo); a code inventory of the chain from estimate line to bank line; the coordinator expert's 24 findings (`review/experts/coordinator.md`); the leaders (Procore Materials and Commitments, NetSuite procure-to-pay, Buildertrend POs and bids).
2. **Plan and mockup** for Alan's yes: `docs/PROCUREMENT_PLAN.md` and phone-first screens on the mockup canvas.
**10-25: Alan said yes** to the plan, the mockup and the recommended calls. **P1 (One Buy Board) is building**; the procurement expert's buying day runs beside it and its P1 findings fold in.
**10-25: P0 (money first) built on its lane branch, waiting to merge** (`src/p0money.js`, tests/p0money_test.py): a deposit or a card payment made ahead is a prepayment on its order, taken off the vendor's bill once ($4,400 deposit and $8,800 invoice: $4,400 due, $8,800 job cost); a payment to a vendor before any bill (Tino's $8,000) is linked to the order and waits on the coordinator's and controller's Today with the vendor's papers; the order's "paid" and Vendors' "paid" are one number; one purchase-tax rule on every order path (materials pay the vendor's NY tax or accrue use tax; the ST-124 only exempts the client's invoice), the three orders issued as "Exempt — capital improvement" repaired with a note for the controller. To confirm with the firm's accountant: the tax rule, and whether equipment rental is taxed like materials.

3. **Build lanes**, each deploying when green: one Buy Board and one "late"; the order and quote path; receiving and reconfirm; vendor credits and claims; then the phone.

## Tasks replace Asana (Alan, 10-23): Monday 10-26 build, merged
All four lanes of `docs/TASKS_PLAN.md` Phase 1, plus the transcript layer, are on master at 13421e3 and pass on the merged build:
- the task record (keys, one internal owner, Waiting On, follow-up, comments, links) and Meeting Mode: meeting_mode_test 265, two-person sync 12;
- the views rebuilt to the mockup: task_views_test 271;
- the team workspace (real date, no demo data, tasks-only pilot, invites) and the Asana import: team_ws_test 65, asana_import_test 81;
- the transcript to Meeting Review (reader, speakers, time matching, reconcile, Drive watcher): meeting_review_test 70;
- smoke 2443, today 128, counts_lint 0, menu 3081; the month holds at 262/292, $1,937, 0 days.

**Waiting on Alan before Monday 10am:**
1. The Asana CSV export.
2. His go to deploy, apply the schema live, open the team workspace and send the invites (Chen, Jeanette). The deploy needs his approval in the session.
3. In the app, Meetings › Settings: the Drive folder of the recurring meeting, and Keep Watching on.
4. Everyone joins the Meet on their own Google account (Companion mode in the room).

**10-25: the match lane merged (a6e843c).** Every task screen is laid out as the approved mockup: the table, panel, board, desktop and phone Meeting Mode (Follow by default for anyone not driving), the phone list (one search, one add line with a mic, 64px rows, the swipe tip), the phone sheet and voice quick add. Tasks is in the phone bar for owner, PM, coordinator and billing, with the late and due-today badge; there is no phone Board. Deliberate differences are listed in `review/match/compare.md`. Suites: task_views 310, meeting_mode 272, tasks_phone 204, meeting_review 70, menu 3153, smoke 2443, reports 450, baseline 9, today 128, counts_lint 0.

Not done for Monday: push notifications (Phase 2); the one-place and Coming Up lanes are still open; speed was not re-measured on the merged build.

## Overnight 10-21 to 10-22 (Alan: "keep working without asking until 9am")
**Merged and pushed to master:**
- **PO gates** (68066ba and the follow-ups):
  - an order stops when the vendor has no current COI and an order open with them, or when it puts them on site;
  - an order over what is left on its estimate line needs a reason, and over $1,000 the owner approves it, with the overage and the reason on his card;
  - a missing W-9 is a warning;
  - po_gates_test passes 36 checks.
- **The tasks lane** (b178140): one task list with chips, opening on Due Soon; 64–72px rows; one task sheet a tap opens, everywhere; a hand-off with Accept; Make It a Task offers the match first; the crew's list is Clock.
  - The map's task failures went from 26 to 0.
  - tasks_phone_test passes 201 checks, and the month holds at 262/292, $1,937, 0 days.
  - `ia_map --check` is in the net as a ratchet (`tests/ia_ratchet.json`).
- **The field's Documents tiles** count what the field sees (419bd29).

**Built, not merged yet** (each on its branch, with the gap named):
- **Fix lane**: all 8 S1 and S2 bugs, with s1fix_test at 90 checks:
  - chase dates;
  - the PM no longer read as the owner;
  - a bank line dated before its bill;
  - held and paid bills kept out of the Payment Run;
  - Controls' count;
  - expired COIs;
  - "2 of 4 at risk";
  - the portal's two percentages.

  Gap: the month fell to 260/292 and $9,537, because the new COI row pushed a $3,800 credit dispute out of the owner's top five. The COI now routes to the coordinator (decision logged); the month is re-running on that.
- **Coming Up lane**:
  - warnings too late went from 40 to 11;
  - warnings missing from the first screen, 54 to 49;
  - page cleanliness, 5 to 0;
  - the band, the missing dates and every first phone screen are built;
  - coming_up_test passes 60, today 134, tasks_phone 201.

  Gaps: ranking_test fails 2 checks on the foreman's desktop, the month is still running, and several net suites haven't re-run.
- **One-place lane**:
  - one-place failures went from 142 to 36, and one-number failures from 8 to 0;
  - Caught for You shows one card per record;
  - the Chief of Staff menu entry is gone, and old names forward;
  - Approvals carries the System Changes and Lessons filters;
  - the Buy Board is one list;
  - Today's card counts dropped: the owner from 34 to 29, the PM from 54 to 23.

  Gaps:
  - two warning checks rose against the ratchet (57 vs 54, and 41 vs 40);
  - one month event slipped from late to missed when the owner reads only his top five;
  - suites are still running.

**Merge order from here:** fix lane, then Coming Up, then one place, each on a green net and the month held both ways.

**Waiting on Alan:** the deploy. The session's permission check refused the production deploy, so he approves it, or adds a rule allowing the Netlify and Supabase deploy.

## 2026-10-21: every role sees what it needs, early, in one place (Alan)
**His ask.** Desktop and phone give each role what it needs and show priorities before they become project delays. Pages are clean and easy to read. The task module "is one of the most important and it isn't great on mobile". He has not seen the latest task update yet. And no "12 different sections to see similar information". Spec: BACKLOG §1.34. It extends §1.11 item 1 (one queue per person), §1.14 (one task system), §1.15 (the menu) and §1.16 (the design gate), and audits what the merged today and menu lanes left open.

| # | Step | Who | Status | Usage |
|---|---|---|---|---|
| 1 | Deploy the merged week-4 build once the full net is green, so Alan sees the current task work; ask him for ten minutes on his phone with the task module | main session | **Waiting on Alan**: the net is green on 8423900+ (every PO suite, smoke 2485, lint 0, counts 0, the month 262/292, $1,937, 0 days). The deploy was refused by this session's permission check; he approves it, or adds a rule allowing the Netlify and Supabase deploy | in week 4 |
| 2 | The information map: every role at 1440 and 390, places per noun, one number per label, delay warnings ahead of time or late, the phone task screens; `tests/ia_map.py --check` | map lane, read only | **Done** (merged 42cf9fd): to-dos on 14 of the PM's screens, materials on 19; 8 labels with two numbers; 45 of 68 warnings never on the first phone screen; the task list opens empty for five roles; 276 of 469 checks fail by design | 8–12% with step 3 |
| 3 | Four role experts (owner, PM, coordinator, foreman) work a full day, phone first | runs | **Done**: owner 4/4/4/3, PM 5/4/5/3, coordinator 5/4/4/3, foreman 5/6/5/4 (priorities before delays, tasks on the phone, clean, one place) | (in step 2) |
| 4 | The consolidation plan: one list per kind of work, the "Coming Up" band of Today, the phone task module, each role's first phone screen, the ratchet | chief of staff | **Done**: taken as yes under his 23:31 "keep working without asking until 9am" (reversible) | small |
| 5 | The build round: three lanes (tasks, Coming Up, one place), the ratchet in the net, the month both ways after each merge, then a half-day phone re-walk by five roles | three lanes | **Running** since 23:40: tasks and Coming Up side by side; one place started at once on every noun but tasks (his later ask: nothing scattered over pages and sub pages; find, read, understand, act) | about 30% (26–36%) |
| — | Fix lane, beside the redesign: the chase email's past date; the PM "Alan" matched as the owner; AMP-311's pre-dated bank line and the hold missing from its Payment Run row; Controls showing 0 exceptions with 16 lines unmatched; expired COIs not flagged; "4 of 4 on time" beside blockers. Chief of staff: add the client portal's two progress numbers and paid bills still in the Payment Run | main session | **Running** | small |
| — | PO gates: vendor papers and estimate-line overage at issue; a missing W-9 is a warning (68066ba, a315e7f, e7be0fe; po_gates_test 36) | main session | **Done**, not deployed. W-9 as a warning waits on Alan (§5) | — |

**What Alan is not thinking about (chief of staff):**
- **Early needs a date.** A warning can come early only if the record has a date to count back from: the date material is needed on site, a vendor lead time, the task a decision blocks, an inspection's booking window, a COI's expiry. The map counts missing dates as well as duplicate places. Part of the fix may be data, not screens.
- **Many delays start with the client, the engineer, DOB and LPC, or vendors.** The client's portal should say what the client owes, by when, and what moves if it is late.
- **A cleaner page can hide work.** The last fold dropped a $68,265 client check to 13th and cost the scripted month $195,142 and 9 days. Every cut shows the counts before and after, and the month must hold at 261/292, $1,937 and 0 days or better.
- **Early warnings can become noise.** In the pilot, the coordinator's Buy Board was all red "order-by passed". An item shown after its date is a late alarm, not a warning. Early items stay few, ranked by the Standard, each with days left and a "because".
- **"Think ahead (three weeks)" is already his value.** Precursors become a "Coming Up" band of each person's Today and a filter of the job's Plan, not a new page. A new Risks page would be the 13th place.
- **The experts are AI role experts, not his team.** His own ten minutes on the phone, then the team in the pilot, decide.

**Waiting on Alan (§5):** yes to `docs/CONSOLIDATION.md`; Today's order for every office person; W-9 as a warning on purchase orders; ten minutes with the task module on his phone once it is live.

**Usage.** The map and experts: 8–12%, spent. The build round: about 30% (26–36%), not the 15–20% planned. The reasons: the map found three seams, not one or two; the early warnings need dates on the records; the map's walk takes about 20 minutes per run; and the proof needs a phone re-walk. Skipping the re-walk would bring it to 20–25%, which is not recommended. On the planning numbers this week stands near 50–55% (check the real meter), so the round starts after the weekly reset under the 60% rule.

## Week 4 (2026-10-20, Alan: "Go")
Alan's "Go" approved the week-4 live AI round (about 40% of a week's usage) and the three recommendations below. Each call is reversible; `docs/DECISIONS.md` logs them.

**What this round builds.** Row 7 of the order of work (role specialists, cost intelligence, the savings ledger) was never built, so this round builds row 7 and the parts of row 12 that depend on it.

**Status (2026-10-20, late): merged on master (af76462). Not yet deployed.** The full net has not run on the merged build. The deploy waits on it. Board, merge order and the chief of staff's verdict are in `docs/LANES.md`.

**Merged** (in merge order):
| Work | What it does now | Spec | Not done (§4 "From week 4") |
|---|---|---|---|
| improvement loop (206da28) | **Report a Problem works again.** It had been broken on master and on the hosted copy since the reports merge: a second function with the same name hid it. On the hosted copy, a report sent from a phone never reached the owner before this round. A new check now fails the build when any name is declared twice. Every signal goes into one queue, Company › Changes. The signals themselves are stored once, synced, with private details stripped. The Brain ranks each problem by the Standard's order, and the owner approves. An approved rule applies at once with an Undo; an approved change to the ERP becomes a ticket (IMP-n). The reporter is told, and the fix is checked a month later. Renewals (insurance, licences) are chased under each person's own rules. The server's nightly run exists but is off until it is switched on. The whole-meeting reader is built (§1.33) | §1.19, §1.32 items 1, 3, 4, 5, §1.33 | The agent does not yet build a ticket on a branch. Its proposals are not in the owner's Approvals. The meeting reader has not run on the real model yet; that needs the platform |
| role specialists (2c34b36) | Each role has a checklist built over the detectors that already exist: no second count, and every finding goes through the six steps. On the planted bank: recall 20/20, precision 43/43, the right fix 20/20. The savings ledger is one store that every lane writes to; the owner sets the pool shares. Workload proposes moving work, and the manager approves. Thresholds are approved by the owner. The three-quote rule now covers every subcontract: an exception is recorded and raised as a finding, but does not block. The main session added that only the owner approves a change, checked again at the click (d9f186b) | §1.28, §1.30, §1.31, §1.32 item 2 | Lines with no detector stay Not Checked (retainage due, WIP movement week to week, committed cost not relieved, quality checkpoints, the crew's and driver's lines). The reclass journal and the revised PO are not drafted. Inbox rows have no countdown for a client's 2-hour reply. Workload's response time covers field questions only |
| cost intelligence (9073799) | One rule for jobs spending more than they bring in, shared with the specialists. Benchmarks come from close-outs and need three comparable jobs, or they say so. They feed estimating through one price book (`costBook`), on the owner's approval; this closes the "one price book" follow-up. Store receipts join price watch's one history. The driver's route: phase 1, and phase 2 with drive times when the key is set, otherwise an estimate. The Brain's weekly review is drafted into Company › Changes | §1.29, §1.31 | Routes phase 2 waits on the Google Maps key. Receipt prices are read from the firm's own receipts only (no store scraping) |
| month regression (af76462) | **The month is better than v11.2 again: 261/292 on time, $1,937 left behind, 0 schedule days lost** (v11.2: 258/292, $9,537, 1 day). Mid-round it had fallen to 243/292, $195,142 and 9 days, all from the one-queue-per-person change. Do Now shows five cards, so items below the fold were lost (the Kleins' $68,265 check ranked 13th on billing's list). The fix is at the root: Do Now now ranks client money waiting, and a client message due today, right after "crew blocked today". Every message is due the day it arrives. Four record bugs were also fixed | month_sim | **Measured on a base that did not include the other three lanes.** The month must run again on af76462. Remaining cracks: the joist CO (drafted at $0, $1,450); blocking lumber not billed back ($487); 26 events with no dollar value (the controller's reconciliations and close, Tomas's COI, two lines to price, a submittal and a PO, permit and LPC tasks, an inspection) |

**The three decisions (Alan's "Go", 2026-10-20): built and merged.**
1. **Who releases vendor payments.** The controller prepares the Payment Run, and the owner releases it in one tap. Billing is the backup and cannot release a bill it keyed. The controller's power over holds does not reach a bill the controller keyed (4ad197e, 3d59216, 767d393). Still waiting on Alan: the bank's own dual control (§5).
2. **What "we owe" means.** Approved bills, equal to the books; bills awaiting approval on their own line (c7a97c4).
3. **Spanish.** Crews keep English until the owner records Jeanette's review on the Team list (c79fc47). Push notifications now go out in Spanish for a field person whose setting is Spanish (f499b0f). Not built: the per-word reviewed mark. The gate is all or nothing, so words added after her review would not show as unreviewed.

**The merge follow-ups (main session):**
- Done: payNormalise no longer hides a double payment; a payment takes a bill's bank or card line only when it is the same money (99c5ddf).
- Done: separation of duties tested with a bill the controller keyed (767d393).
- Done: three quotes checked when a subcontract issues, with the exception recorded (role specialists).
- Done: one blue button with a drawer open, and the lint now opens drawers (cde0717).
- Done: the accounting-choices card says the choices are recorded, not yet applied; owned-property jobs are found by entity (7980afb).
- Done: one price book (cost intelligence folded the close-out factor and the benchmarks into `costBook`, read by estimating and the item library's fill).
- Done: the field's Send To picker, lost in the chat redesign, is back (8c1990d, ebefe9a). A false alarm in the covered-button lint is fixed (c6e339a).
- **Open:** scope a payer's Ask on the hosted AI by payer. It blocks the portal for any two-payer client.

**Before deploy (chief of staff, 2026-10-20), on af76462, one suite at a time through `tests/slot.sh`:**
1. The scripted month, both ways (the whole list, and the first five). It is the first check, because the role specialists add findings to Today, the very queue whose fold caused the regression. The bar is 261/292, $1,937, 0 days, with no new misses.
2. The full net (`tests/run_all.sh`, 58 suites including loop, meetread, dupnames, specialists and costintel). The loop lane reported three suites red on master under load, with the same failures as master: exec_assistant_test (5 phone taps landing under a pinned bar), assistant_lane_test (1, billing's "Run It Again" under the sub-nav) and speed_test. Each must be green or explained before anything ships. A red net does not ship.
3. Apply `schema.sql` (the synced signals) on the hosted database before the app that writes them goes up. Otherwise Report a Problem breaks again on the hosted copy.
4. Then deploy. Check Report a Problem live, from a field phone to the owner. Leave the nightly loop off (`LOOP_RUNS`) until a week of reports has come in by hand. When it is turned on, it sends nothing and spends no AI unless `LOOP_AI` is on.

**Not in this round:**
- **The live jobs load** waits on Alan handing over his file in a private session (§5).
- **Driver routes phase 2** waits on the Google Maps key in Netlify, which only Alan can add (§5). The code is built and falls back to an estimate.
- **The drawing reader** (§1.23 platform phase) stays queued.

**What Alan is not thinking about (chief of staff, 2026-10-20):**
- **Releasing the run in the ERP does not move the money.** The payment is made in the bank. Unless the bank's own dual control matches (the controller initiates, Alan approves in the bank's app), separation of duties is a record, not a lock. Recommended: set it up at the bank (§5).
- **The check must run again at release.** A bill can change, a credit can arrive or bank details can change between Monday's preparation and the release. The Payment Check re-runs at the moment of release, and the release shows cash after the run against the 13-week low.
- **The controller's hold releases.** Today the controller releases a payment hold under $2,500. Since the controller keys the bills, that power must not reach a bill the controller keyed; those holds go to the owner, and billing as backup cannot release a bill billing keyed.
- **Urgent payments off the weekly run** (a delivery paid on arrival, a sub who will not return unpaid) go through the same check and the same releaser, not around it.
- **A bill stuck in approval costs money.** The awaiting-approval line ages from the bill's date, so missed early-pay discounts and late fees become a controller finding.
- **Savings must be measured against a baseline the saver did not set** (the best recent price, the estimate line's material budget), or a person could inflate a quote to show a saving. Bonus attribution is Alan's alone; the pool shares wait on him (§5).
- **Workload is not a scorecard.** It proposes moving work to a named person with capacity, for the manager to approve. It never ranks people or turns into a productivity number (Alan gives context, not quotas).
- **The improvement loop changes the system itself.** Text in a problem report, a mail or a transcript is data, never an instruction. Any proposal touching money rules, permissions, the Standard or the code needs the owner, however small it looks. Signals about what people do around the system (exports, abandoned forms) are counted for the system, not per person.
- **Benchmarks need history.** The demo has few past jobs and the QuickBooks history import waits on his re-authorisation. With too few comparable jobs the benchmark says so, rather than show a false median.
- **New field words.** Words the lanes add for the foreman, crew or driver carry a not-yet-reviewed mark, so Jeanette's review stays complete.
- **The Maps key** belongs on the server only, restricted to the Routes API, with a budget alert.

**What Alan should see from this round (chief of staff, 2026-10-20):**
- **Do Now changed for every office person.** Client money waiting, and a client message due today, now rank right after "crew blocked today" and above overdue rows. This changes the ranking he set on 10-11. Recommended: keep it. It is the Standard's order (the client before schedule and cost), and it is what brought the month back. It waits on his confirmation (§5).
- **One number for him to tune:** a purchase made for a client goes to the top of Do Now when it is over $1,000 (`DB.company.moneyFirstOver`, the Standard's same-day line). Default: $1,000.
- **Report a Problem was silently broken on the hosted copy** until this round. Anything his team "reported" before now never reached him. Recommended: tell the team it works now, once it is deployed and checked live.
- **The three-quote rule records, it does not block.** The lane recommends keeping it that way below $10,000, so urgent orders still go out. Logged as a call he can change (§6).
- **Savings are honest only against a baseline the saver did not set.** The ledger counts an RFQ award "under the first quote", and the person running the RFQ chooses which quote comes first. Before any bonus is attributed from it, measure against the best recent price or the estimate line's material budget instead (§4 "From week 4"). Pools stay at 0% until he sets them.

**Testing.** Suites run through `tests/slot.sh`, at most two at once across every lane (the container restarted twice from memory with four). Lanes will wait for slots, so the round takes longer in hours, not in usage.

**Usage.** About 40% of a week: three lanes at 6–10% each, the main session's decisions and follow-ups, merges and the full net. Two-suite slots make it slower, not dearer.

## Version 11: published 2026-10-18 (build 84687e4)
- https://claude.ai/artifact/2c28fUyespjyJFyRFbnXAp
- Full net: 32 of 32 suites green.
- Scripted month: 258 of 292 on time, 29 missed, $9,537 left behind, 1 schedule day lost. The previous best was 239/291, 46 missed, $109,613.
- The 29 misses remaining are queued below ("From the scripted month").

## Overnight 2026-10-19 (Alan asleep: "do not wait for my approvals")
- **Built and merged (four lanes, all on master 2026-10-19):**
  - **Today:** one Today page per office role (owner, PM, coordinator, billing, controller) over one task shape; filters All, Approvals, Inbox, Tasks, Team; hand-offs that need acceptance; the Standard's recurring duties made automatically; proof asked when closing an inspection, a wall or extra work (BACKLOG §1.11 item 1, §1.14).
  - **Menu:** one declared menu per role from the workshop, every recommendation adopted; Ask is a button in the header on every screen (§1.15).
  - **Assistant:** one assistant (Chat, Findings, Activity, Brain Settings); Act Alone / Ask First / Hand It to Me per action type; answers stream in, show their work and read attachments (§1.27, §1.24).
  - **Messages:** one message-thread noun: each job's team and client threads, direct and group messages (members only, also on the server), record cards, @assistant, message to task (§1.21 phase 1).
- **Live on the hosted copy (2026-10-19, afternoon):** all four lanes, the fixes, and Chat in the header. Full net 44/44 on the merged build; live checks 73/73 (database rules) and 33/33 (two devices: an assistant answer streamed through the real AI door, a direct message office to phone and back).
- **Live (2026-10-19 evening): the new Ask and its mind, and phone speed.** Ask looks and works like the Claude app; the day opens on a briefing written as a message; it reads every line, looks in more than one place, checks every figure and learns (rules through the owner); the server writes each office person a briefing three times a weekday (first run tomorrow 7:20). Reopen on a phone under 3 s. Net 22/22 before deploy, the rest running; live: briefing run end to end 6/6.
- **Live (2026-10-20): the team chat, phase 2.** WhatsApp/iMessage-style chat, New Chat with anyone, the owner's All Chats, field roles only on their crew's jobs (schema applied), private read markers, notifications. Net green on the merged build; live: database rules 74/74, field jobs 28/28, two devices 33/33. Found live and fixed: a field person on no job could not open the app.
- **Done (was waiting on Alan's go): the executive assistant (Alan, 2026-10-19: "a Fortune 500 executive assistant, an assistant project manager, not a bot that answers questions").** Ask opens on what it has done and what it needs from you, not an empty box: a briefing it wrote (today, what it did since you last looked, decisions with one-tap approve, what it is chasing for you); it works between your visits (the server runs it on a schedule for each person, from the watcher and the records), drafts replies, prepares meetings, chases vendors and subs within each person's rules, keeps a ledger of what it did; it remembers how you work (people, preferences, standing instructions) in memory only you can see; you can talk to it on the phone; for a PM it runs the job like an assistant PM (late tasks, open RFIs and submittals, the weekly update drafted). One lane, about 6–10% of a week's usage; the AI caps need raising for the scheduled runs (the owner's $8 a month will not cover them).
- **Found and fixed while merging, each with a check that failed first:** the menu and the assistant disagreed on The Brain and the Chief of Staff (now entries that open the assistant on their tab); after sending one invoice the next draft had no Send to Client (the Made Today card swallowed the header); on a phone, Open on a sent invoice's mail left the line below the screen; the demo's message threads could have seeded into the live workspace; the owner's assistant rules for someone never reached that person on the hosted copy; two phones would each make the Friday update.
- **Done by the main session tonight:** the AI door streams to the page; the nightly Brain on the server (first live run on QA data proposed five grounded changes for 5 cents); the books' seals; the document reader with spreadsheets; Sign Out Everywhere and invites; the watcher's nudges; faster phone start-up (part).

## Platform: first slice live (2026-10-18)
- **Where:** https://smartdesigns-erp.netlify.app (new Netlify site; the 12 old sites untouched) on a new Supabase project in us-east-1. Alan is invited as owner by email. How it works: `platform/README.md`.
- **Built and checked live:** invited sign-in only; roles set by the owner on the server; field roles never receive the books, bank, payroll or bills and get money stripped from jobs, and their saves cannot touch money; clients refused until per-client rows; edits sync between two devices both ways, simultaneous edits on the same job both kept; `/api/ai` refuses anyone not signed in or without a role, answers members on the model the server picks, and logs each call's cost (live checks 27/27 and 17/17).
- **Supabase is on Pro** (daily backups, no pausing), so real data can go in once the import (§6) is built.
- **Sign In with Google is on** (2026-10-19), invited addresses only; the consent screen reads SmartDesigns Projects.
- **Mail, calendar and Drive are private to each person** (2026-10-19): own rows only that sign-in can read, the owner included; live checks 37/37 and 25/25. Fixed on the way: device settings (who is on the phone, the open job) were syncing, so one phone's save switched other devices to that person.
- **Alan's Google is connected** (2026-10-19, signed in as alan@smartdesign.nyc): first sync 40 mails, 55 calendar entries, 500 Drive files, all in his private rows, none in shared rows, no Google tokens stored. Both sign-ins now share one private store (server-set link).
- **The watcher is live** (2026-10-19): every 15 minutes, weekdays 7am to 7pm New York, new mail, calendar changes and Drive files go into each watching person's private inbox; the app files them on opening. Alan turns it on with Settings › Connections › Keep Watching When It Is Closed. The watcher's key reads only (it cannot send mail). Push notifications are live: at most one per run, for vendors, clients, jobs, agencies and meetings in the next two days. Alan turns them on in Settings › notifications (iPhone: add to Home Screen first). The watcher's finds now become nudges in the assistant's conversation. The owner invites people and signs any account out everywhere from Settings › Team Accounts; a signed-out phone loses access at once and erases its copy.
- **Long AI answers no longer vanish** (2026-10-19): the door streams, so answers past 30 s arrive (4,000 tokens in 41 s), and anything past 52 s comes back cut short with its cost logged. Before, a long answer was lost at 30 s and its cost escaped the caps. Longer work belongs to the scheduled agents.
- **The books' seals are held by the server** (2026-10-19): each closed month is sealed with SHA-256 from the server's own copy of the books, add-only; Verify the Books checks against it and names any changed, missing or added posting.
- **The document reader is live** (2026-10-19): text PDFs and Word read free on the server; scanned PDFs and photos read by the small Claude model within the caps (a receipt photo read exactly in the live test). Spreadsheets are read since the same night; HEIC photos get a note for now.
- **Alan signed in** (2026-10-19, email link); the firm workspace holds the first upload (84 collections, demo data).
- **Next platform lane (recommended):** the client package for the portal (BACKLOG §5 note): clients stay refused until a client's phone can receive only its own figures, proven by a planted-secret test.
- **Not built yet:** HEIC photos in the reader, per-client portal rows (clients stay refused), Plaid, the agents beyond the nightly Brain. Field roles still receive every job.

## Overnight 2026-10-18: where things stand (for Alan at 10am)
- **Published:** version 11 (v11.1 folded in). Build 84687e4: 32/32 suites green; scripted month 258/292 on time.
- **Pilot:** 3 days, 9 role experts, both workshops. Reports are in `docs/pilot/pilot1/`, and the menu result is in `docs/MENU_DRAFT.md`.
- **Merged on master since v11:**
  - plans control phase 1;
  - cross-set consistency, demo phase (xset_test 66/66);
  - find it again after every save: the new record is highlighted, or listed in a "Made Today" card with Open (15 cases, findable2_test 185/185); the pay app starts each line at its billed cumulative and refuses to go below it; outbox mail shows Name <email>, and invoice mail goes to the billing contact;
  - pilot fixes batch 2 (pilot_fixes2_test 72/72): real clock times, mail cards on every sync, money matching, Reverse Payment, In the Bank Not Applied, agency notices move bookings, the driver's pickups, card accounts from statements;
  - pilot fixes batch 1 (19 items and follow-ups);
  - the calendar date fix.
- **Still building:**
- **v11.2 published (2026-10-18, artifact Version 3, build 379182f):**
  - full net 37/37 green;
  - scripted month 258/292 on time, 29 missed, $9,537 left behind, 1 schedule day: identical to v11 event by event;
  - the merges first dropped the month to 251/291. Lane monthfix found 2 app bugs (a template-to-install order held for its own template; a client credit read as a double bill) and 2 month actors still acting on old screens (the foreman's Daily Log, the driver's route drop).
- **Batch 3, queued from the Documents Workshop:**
  - a send gate on every client document: strip internal notes, require cost codes, bill-to and true titles, print how to pay, one letterhead;
  - progress billing tells the truth: one pay app per period, stop when billed exceeds measured, no $0 apps, one "Amount due";
  - every record keeps its line link;
  - the item library (§1.18): done 2026-10-20 (merged with Spanish).

## v11.1 (first thing after the reset)
- **Fix the v11 net regressions** (2026-10-11 run):
  - client questions are missing from the PM's Home (likely the own-sent-mail filter);
  - emailed asks and calls no longer become proposals;
  - the short-pay path on Do Now;
  - purchasing, client and flow tests that predate the vendor-on-file rule;
  - track_test crashes on a click timeout;
  - pricewatch "why is this flagged".
- **Ranking (Alan):** anyone blocked today, such as crew waiting, ranks above older overdue items, and both stay visible.
- **Harness findings 6–8:**
  - a new CO defaults to the wrong client;
  - the PM's phone menu is hidden under More;
  - the client portal's View doesn't open.
- **Review:** integrate's three held commits.

Then the full net, the scripted month and the final crawl; then publish v11.

## 1. Running now
| What | Where | Status |
|---|---|---|
| Second integration pass | lane integrate2 | Running |
| Agent-month harness: the shared world, the screen-only toolkit, the outside world, the referee, role briefings | lane agentsim, BACKLOG §1.17 | Running |

The integration pass covers:
- price watch and order tracking alerts linked to the Standard;
- one "What My Assistant May Send for Me" card;
- Enter the Bill;
- tasks findable after save, plus find-it-again tests for every create;
- stock held as inventory.

## 2. Version 11 release (next)
1. Merge integrate2 (crawl merged; smoke 2,436 pass on the merged build).
2. Run the full test set, one suite at a time.
3. Run the scripted month simulation.
4. Run the phone check at 390px.
5. Publish, push, and send Alan the link.

## 3. The order of work (updated 2026-10-18, folding in the Oct 17 Cowork session)
The Cowork plan's first steps are already done in this repo:
- the code is on GitHub;
- the test net was rebuilt (screen lint, counts lint, the Ask bank with held-out sets, the day walk, the finance cross-check);
- round 5 was redone (closetie, truthpct, askgen, clientpo).

What remains, in order. Usage is a share of one week's allowance.

| # | Work | Spec | Lanes | Usage |
|---|---|---|---|---|
| **Week 1** | | | | |
| 1 | v11.1: fix the merge regressions, crew-waiting-first ranking, harness findings 6–8; full net; publish v11 | PLAN v11.1 | 1–2 | 10–15% |
| 2 | Lean expert pilot (3 days) + the Navigation, Pages and Documents workshops, with the visual review | §1.17 | runs | 3–6% |
| 3 | Plans control + the cross-set consistency workflow (demo phase) | §1.22, §1.23 | 2 | 15% |
| 4 | Simplify: the menu (from the workshop), one task system, one queue per person, the alert budget, the structure lint and completeness tests | §1.14–1.16, §1.11 | 3 | 25% |
| | Integration and merges | | | 10% |
| **Week 2** | | | | |
| 5 | **Done 2026-10-20 (merged fa3337d).** Live-job capabilities on invented equivalents: two payers per contract, range estimates with allowances and a paid exploratory phase, the HTC calculator and hard/soft/contingency estimate, the contractor-to-employee user. Follow-ups in §4 | §1.25, §1.26 | 1 | 15% |
| 6 | One assistant per person (four screens into one), approval rules, activity log | §1.27 | 1–2 | 12% |
| 7 | **Merged 2026-10-20 (2c34b36, 9073799); full net and deploy pending.** Role specialists on the demo + planted-problem banks; cost intelligence (cash-negative jobs, benchmarks, receipt price book, driver store list phase 1); savings ledger | §1.28–1.31 | 3 | 25% |
| 8 | **Done 2026-10-20 (items and Spanish merged 8d9c1f7; Messages phase 1 merged 2026-10-19).** Item library, Messages phase 1 (with record cards and @assistant), Spanish for the field. Follow-ups in §4 | §1.18, §1.21, §1.20 | 3 | 25% |
| | Integration and merges | | | 10% |
| **Week 3** | | | | |
| 9 | **Done 2026-10-20 (merged 3fc848f).** Subcontractors, lien waivers and the Payment Check before every vendor payment. Follow-ups in §4 | §1.10 item 1, §1.12 | 1 | 15% |
| 10 | **Done 2026-10-20 (merged 560057d), pending the full net on the merged build.** Reporting proven end to end. Follow-ups in §4 | §1.13 | 2 | 15% |
| 11 | Platform foundation: database, sign-in, permissions, sync, AI connection with caps (**first slice live 2026-10-18**); next: watchers, document reader, push, Google sign-in, per-client rows | §5 | 3–4 | 35% |
| | Integration and merges | | | 10% |
| **Week 4** | | | | |
| 12 | **Merged 2026-10-20 with row 7 (af76462); full net and deploy pending.** Ask like Claude and the always-on assistant were done on 2026-10-19. This round added the role specialists, the Brain's timers (the nightly loop stays off until switched on), the improvement loop and the whole-meeting reader. The live jobs load waits on Alan's file. Routes phase 2 waits on the Maps key. The drawing reader is queued.<br>The live AI on Claude:<br>- Ask like Claude;<br>- the always-on assistant per person;<br>- role specialists and Brain timers;<br>- the documents and drawing reader;<br>- driver routes phase 2 (Maps);<br>- live jobs loaded into the private platform;<br>- the improvement loop | §1.24, §1.27–1.29, §1.19, §5.8 | 4 | 40% |
| 13 | Real-data pilot with the team; the full ten-expert regrade to 9+; go-live checklist | §6 | runs | 20% |

**Totals.** About four weekly allowances on the current plan, so roughly four weeks of calendar time. Each week fits under the 60% rule only if a week's round is split into two halves.

**Bought as extra usage at API prices,** the same work is about $1,500–3,000.

**Running costs once live:** about $150–700 a month, mostly AI, under a cap Alan sets.

## 4. Queued (built after the above, or folded in where they fit)
- **The transcript reader** (§1.33): Done 2026-10-20 in the improvement loop lane (`src/meetread.js`, meetread_test 31). Claude reads the whole meeting, corrects Gemini's notes, and turns lessons into changes for approval. Not yet run against the real model, which needs the platform.
- **From week 4 (merged 2026-10-20, af76462):**
  - before deploy: the scripted month and the full net on af76462, and `schema.sql` applied for the signals (see "Week 4");
  - a payer's Ask on the hosted AI is still not scoped by payer (it blocks the portal for two-payer clients);
  - improvement loop: the agent building an approved ticket on a branch; the loop's proposals in the owner's Approvals, with the counts lint (today they sit in Company › Changes only, so they can be missed); the meeting reader on the real model;
  - role specialists: detectors for the lines still Not Checked (retainage due, WIP movement week to week, committed cost not relieved, unexplained budget variances, quality checkpoints, selections completeness, the crew's and driver's lines); the reclass journal and the revised PO drafted as fixes; a countdown on Inbox rows for the client's 2-hour reply; mail response times in workload (needs per-person mail on the hosted copy); a payroll export of the bonus pool, only after Alan sets the pools;
  - savings ledger: measure RFQ savings against the best recent price or the estimate line's material budget, not "under the first quote", which the person running the RFQ controls;
  - Spanish: a reviewed mark per word, so words the lanes add after Jeanette's review (the driver's route card among them) show as unreviewed;
  - the month's remaining cracks: the joist CO drafted at $0 ($1,450) and the blocking lumber not billed back ($487). Both have been on this list since 2026-10-18 (below). Also 26 events with no dollar value: the controller's reconciliations and close, Tomas's COI, pricing two lines, a submittal and a PO, permit and LPC tasks, an inspection;
  - three suites the loop lane found red on master as well: exec_assistant_test (phone taps under a pinned bar), assistant_lane_test (billing's "Run It Again" under the sub-nav), speed_test.
- **Speed:** boot under 2 s, view switch under 100 ms on a phone (§1.11 item 5). Measured on the hosted copy 2026-10-19 with a mid-range phone (CPU 4x slower, 1.5 MB/s): reopening took about 20 s, against 7.5 s for the local copy on the same CPU. Fixed so far: the time-zone formatter (4.6 s of it, now 0.16 s) and the page download on every open (the shell now opens from the phone's copy: 0 bytes, page ready in 1.9 s). Left: about 10 s of start-up work in finishBoot and the first render (job financials, overhead allocation, and render wrapped about 40 deep), which is this lane's work. `platform/test/live_speed.py` measures it; numbers taken while the full net ran are noisy.
- **Notifications:** push notifications and morning and evening digests, on the platform (§1.11 item 6).
- **Office and field input:**
  - voice input for the field (§1.11 item 7);
  - bulk actions for the office (§1.11 item 8);
  - the first week for each role, and empty states (§1.11 item 10).
- **History and the agents:**
  - import 12–24 months of history from QuickBooks and the bank, so price watch and on-time records work on day one (§1.10 item 2);
  - agent heartbeats, an AI activity log, and a pause switch per agent (§1.10 item 3).
- **Money and controls:**
  - cost-plus honesty: credits and overpayments flow to the client's invoice (§1.10 item 4);
  - vendor creation and bank changes need two people; separation of duties (§1.10 item 5). Partly built by the subs lane (2026-10-20): a bank change holds every payment until someone other than the requester calls the number on file, and whoever entered a bill or set up the vendor cannot release its payment. Not built: a second person to create a vendor;
  - the right entity on every PO, bill and stock item, and intercompany transfers (§1.10 item 6).
- **Shared purchasing address** for the agents, with SPF and DKIM (§1.10 item 7).
- **Rollout and proof:**
  - rollout: each person acknowledges the Standard, and gets a first-week guide (§1.10 item 8);
  - the "AI pays for itself" scorecard (§1.10 item 9).
- **Records and accounting:**
  - seven-year retention, nightly backups, full export, offline plan (§1.10 item 10);
  - a read-only accountant role (§1.10 item 11).
- **Estimates and stock:**
  - material and labour split per estimate line, so savings and price checks have a material budget;
  - a trip-cost model for the "not worth the trip" stock override.
- **From the platform session (2026-10-19):**
  - iPhone HEIC photos in the document reader (spreadsheets are read since 2026-10-19);
  - a real push on Alan's phone and a real watcher run on his Gmail, not yet seen.
- **From the live jobs lane (merged 2026-10-20):**
  - Done 2026-10-20 (02746eb): a payment on account on a two-payer contract now waits as Not Assigned until billing assigns it to a payer, audited, raised on Today (livejobs_test);
  - Open (not built in week 4): a payer's Ask on the hosted AI is not scoped by payer (the screens and the query layer are); scope it before any two-payer client gets the portal;
  - contractor bills have no PO, so the no-PO checks name them, and her W-9 shows missing (recommendation waiting on Alan: a contractor agreement as her PO, no payment until the W-9 is on file, a 1099 total for year end). Since the subs merge the Payment Check holds her payments until the W-9 is on file;
  - demo payments have no bank lines, so the truth layer shows them as unbacked (demo only; real payments come from the bank);
  - Mercer & Bond on a job is a flag only, with no link to a deal record in the Mercer & Bond workspace;
  - the client's proposal shows a "Net" after tax credits (recommendation waiting on Alan: keep it internal until the tax-credit consultant confirms eligibility and timing);
  - the real jobs load into the private platform database through the import (§6), from the Cowork handoff's `docs/LIVE_JOBS.md`, which is not in this repo and must never be (joins row 12).
- **From the subs lane (merged 2026-10-20, 3fc848f):**
  - before deploy: the full net on the merged build (live jobs, the two-payer fix and subs together). The lane ran about 20 suites on its branch, not the 44-suite net on the merged result;
  - Done 2026-10-20 (99c5ddf; a payment takes a bill's bank or card line only when it is the same money): before any real bank or card data is loaded: when a check with no bank line is recorded, payNormalise ties it to whatever card line is on the bill, which can hide a double payment after the fact (pre-existing; financial truth). Fix it so an unmatched check stays unmatched and a second payment against one bill is flagged, with a planted double payment in the finance cross-check;
  - Done 2026-10-20 (767d393, payrun_test): separation of duties had no planted case (now also billing as the backup releaser): every subs_test bill is entered by "Billing", so no test proves the person who keyed a bill is held from paying it. Add the case (the controller keys a bill and tries to pay it; the coordinator sets up a vendor and tries to release its payment);
  - Done 2026-10-20 (role specialists: recorded exception and a finding, not a block): the Standard's "three quotes on every subcontract" was not checked when a subcontract issues; it should be checked there, with a written reason when fewer;
  - Done 2026-10-20 (cde0717): a bill's drawer open left New Vendor Bill blue beside Pay (two primaries, pre-existing). The screen lint judges the page without the drawer; fix the class so it judges what is on top;
  - not built: the monthly vendor statement reconciliation; a deposit taken off a sub's later pay applications line by line (today the contract check holds such a bill, so money does not leak, but a good bill can wait); sub bid leveling by scope and backcharges; a sub's emailed invoice read into a pay application; a Kind column (Subcontractor, Supplier) on the vendor list;
  - Done 2026-10-20: the reports lane took master with subs in (f9716df) and ties retainage payable (2050), cleared payments and bills awaiting approval to the cent (reports_test).
- **Before the next deploy (chief of staff, 2026-10-20):**
  - Done 2026-10-20: live jobs, subs, items and Spanish, and reporting went live after a net of 26 suites on the merged build (chain 367/0, reports 450, subs 139, livejobs 172, items 68, spanish 109) and three fixes it found (`docs/LANES.md`).
  - Done 2026-10-20: the full net ran on that build and found the scripted month's regression (fixed by the month regression lane, merged af76462) and two other failures (fixed). Original note: the other 28 of the 54 suites in `tests/run_all.sh`, and the scripted month (none recorded since v11.2). Run them through `tests/slot.sh` before the first week-4 merge, so a week-4 failure is not confused with an older one. Reporting moved ledger net YTD by $5,000, customer deposits, the 13-week low and cash-basis YTD, so the month's money figures are expected to move; each move needs its reason;
  - the books' seals: reporting's retainer fix changes how an August invoice posts (2400, not negative revenue). On the hosted copy the server holds August's seal, so Verify the Books will likely name a changed August posting. Check it on the QA workspace; if it does, it is recorded as an owner-approved correction with the reason, never re-sealed quietly.
- **From the items and Spanish lane (merged 2026-10-20, 8d9c1f7; items_test 68, spanish_test 109):**
  - the assistant drafting lines from notes, photos and takeoffs (§1.18 item 4);
  - income and expense accounts per item, so a line from the library carries its accounts into the books (today only "taxable" is on the form);
  - voice in the item picker (the request box keeps its own microphone);
  - the library's proposals in the owner's Approvals, with the counts lint (today they sit on the library's own card, so they can be missed);
  - automatic English beside a Spanish daily log or request, so the PM, the records and anything that reaches a client read English;
  - Done 2026-10-20 (f499b0f): push notifications in Spanish for a field person whose setting is Spanish;
  - offline assistant answers stay in English;
  - Jeanette has not reviewed the ~900 Spanish words; crews are not switched to Spanish until she has (safety words first). Decided 2026-10-20; Alan asks her (§5). Each word to carry a reviewed mark, so new field words show as not yet reviewed.
- **From the reports lane (merged 2026-10-20, 560057d; reports_test 450/450):**
  - Done 2026-10-20 (cost intelligence lane; benchmarks under `costBook.bench`, read by `ciCostGuide` and the item library's fill): one price book: close-out writes a cost factor per cost code to `DB.company.costBook`, and the item library keeps item costs in `DB.company.itemLib`. Fold the factor into the library's fill so estimating reads one place; today nothing reads the cost factor (BACKLOG §1.16);
  - Done 2026-10-20 (7980afb): the accounting choices are recorded with who, when and why but do not change the statements yet. Until they do, the card says so in plain words (a controller who picks "Capitalise" will expect the P&L to move);
  - Done 2026-10-20 (7980afb): the development-cost stake found owned-property jobs by client name; now found by entity;
  - the read-only accountant role (platform, §1.10 item 11);
  - QuickBooks comparison unchanged (the Three-Way Tie-Out);
  - "owed" in payables: decided 2026-10-20 (approved bills; awaiting approval on its own line); built 2026-10-20 (c7a97c4).
- **Gaps the build lanes found:**
  - Done 2026-10-20: a toast's Open link closes an open editor first and asks before dropping anything typed (Keep Editing is the blue step); toast_leave_test 18;
  - client portal: pay online, or "we paid";
  - the foreman can only measure today's tasks;
  - sub POs default to SD Plumbing;
  - a mailed bill's PDF is not attached to the bill.
- **From the scripted month:**
  - (2026-10-18 run) a vendor credit memo has no path to close a held dispute ($3,800);
  - an approved overage never becomes a priced CO (the joist, $1,450);
  - client purchases on a card have no reimbursable row ($487);
  - a statement in mail or Drive becomes a task, not an import and reconcile;
  - agency mail (DOB, LPC, inspections) closes no schedule task;
  - a quote's Apply opens a task instead of pricing the line;
  - a vendor date in mail never becomes the PO's expected date;
  - Chase writes a note instead of a draft to the party;
  - a COI for a sub not on file is only noted;
  - the designer's and PM's Home miss some items;
  - the lighting submittal never released;
  - the joist CO unpriced;
  - Tomas Restoration not on file;
  - the countertop and radiant mats ordered late;
  - payroll paid but hours not approved (show "hours paid but not approved").
- **Test gaps:**
  - leak_test's three partial catches (overspend at landing, per-figure source ids, nothing-slips edge cases);
  - Ask held-out 35 of 40;
  - 413 PDF attachments unread (needs the platform's document reader).
- **Go-live and the 10x scorecard** (§6).

## 5. Waiting on Alan
| Asked | Decision or action | Default until then |
|---|---|---|
| 2026-10-11 | Which email address the vendor follow-ups come from (recommend purchasing@ on the firm's domain) | Outbox only (demo) |
| 2026-10-11 | Who the accountant is. To confirm with them: use tax; the overhead method; Mercer & Bond development costs capitalised; revenue recognition for tax; stock held as inventory | The defaults in §1.13 item 8, labelled "confirm with your accountant" |
| 2026-10-11 | Leftover material on cost-plus jobs: back to the client, a credit on their invoice, or into firm stock | "Client-owned surplus, ask the PM" |
| 2026-10-11 | ChatGPT export, for `docs/ALAN.md` | Profile from the build sessions and the Standard |
| 2026-10-10 | Re-authorise QuickBooks (July to date, then the history import) | Bank and card lines and the bridge snapshot |
| 2026-10-20 | Tax credits on the client's proposal: show the "Net" after credits, or keep it internal | Internal until the tax-credit consultant confirms the church and rectory qualify and when the credits arrive; the client sees credits only as "subject to certification and your tax adviser" |
| 2026-10-21 | **Blocker before the live jobs load (main session):** the hosted copy still sends a field phone the job's money documents (contract, change order, purchase order, invoice files and their stored PDFs); the screens hide them since 2026-10-21 (tests/field_money_test.py), but hiding is not security. The server must drop money-category files from a field person's project rows and refuse those files in storage. | Demo and QA data only on the hosted copy until then |
| 2026-10-20 | Hand over the real live-jobs file (`docs/LIVE_JOBS.md` from the Cowork handoff) for loading on the private platform | Invented demo jobs only |
| 2026-10-20 | The contractor designer: a contractor agreement as her PO, W-9 before the first payment, classification confirmed with the accountant | Bills with no PO, flagged; payments held until the W-9 is on file |
| 2026-10-20 | Ask Jeanette to review the ~900 Spanish words (decided with his "Go"; the asking is his). Recommended: one sheet for her (English, Spanish, where it appears, safety words marked), her sign-off recorded word by word | Crews stay in English until she has reviewed, safety words first |
| 2026-10-20 | Add a Google Maps key in Netlify for driver routes phase 2. Recommended: Routes API only, server-side, with a budget alert | The driver's list names the cheapest store per item (phase 1), no route |
| 2026-10-20 | The savings ledger: the shares for the wage, bonus and charity pools; who sees savings by person; bonus attribution | Built 2026-10-20: the owner sets the shares in the ledger. Every saving recorded; pools shown at 0% until he sets them; by person for the owner only; nothing attributed or paid without him |
| 2026-10-20 | Confirm the new Do Now order for every office person: client money waiting and a client message due today rank right after "crew blocked today", above overdue rows (it changes his 10-11 ranking). Recommended: keep it; it follows the Standard's order and brought the month back to 261/292 | The new order stays (reversible) |
| 2026-10-20 | The one Do Now number: a client-billable purchase over $1,000 ranks first (`DB.company.moneyFirstOver`) | $1,000, the Standard's same-day line |
| 2026-10-20 | Set the bank's dual control to match the Payment Run: the controller initiates, Alan approves in the bank's app | The ERP records who released each run; the bank itself does not enforce it yet |
| 2026-10-21 | Yes to `docs/CONSOLIDATION.md` and its build round (about 30% of a week, three lanes) | Recommended: yes, after the weekly reset and the fix lane's merge. Nothing is rebuilt until he says yes |
| 2026-10-21 | Today's order for every office person: safety and law; crew blocked today; client money and messages; what will delay a job inside its lead time, by days left; overdue as one line per kind; sales follow-ups. The owner's bank matching becomes one line and the rows go to the controller (answers the 10-20 Do Now row too) | Recommended: yes, shipped only if the month holds at 261/292, $1,937, 0 days both ways; reversible |
| 2026-10-21 | A missing W-9 is a warning on a purchase order, not a stop | Recommended: keep. The Payment Check holds every payment until the W-9 is on file; insurance stays a stop. Add a W-9 request draft on the warning, for approval |
| 2026-10-21 | Ten minutes with the task module on his phone once the current build is live, and the two or three things that bother him most | The experts' phone day stands in; his notes outrank theirs |
| Later | Google sign-in consent screen (guided, about 5 minutes) | — |

## 6. Calls I made that Alan can change
- **Ranking:** overdue and today first, then the decision principles. Immediate safety and law always lead, and a missing insurance certificate counts as immediate.
- **Explanations:** a "this quarter" price explanation expires at the quarter's end.
- **Stock matching:** "5/8 sheetrock" with no type asks the procurement manager rather than guessing between Type X and moisture-resistant.
- **Phone home screen:** it hides the "because" lines to stay under 180 words; they show on Approvals and on desktop.
- **Quote rule:** "outside Manhattan and Brooklyn" means any other borough or out of state.

- **Mail nudges (2026-10-19):** a question from someone not on file (no vendor, client, staff or user with that address) becomes a nudge only when the mail names a job or money; "Lunch Friday? Are you free?" stays in the inbox. Alan can change this.
- **PM's phone bar (2026-10-18):** Home, Approvals, Projects, Tasks, Field, More.
- **New CO, Invoice or Estimate off a job's screen asks for the client** (it used to take the last job's).
- **A task saved with no owner goes to the job's PM** (or the design director on a design job), with who, when and why recorded; it can be switched off.
- **The owner's "Waiting on the Others" list** follows the one ranking order. Grouping it by person is proposed for the one-queue-per-person work.
- **Payment holds (subs lane, 2026-10-20):** the controller releases a hold under $2,500 (the same line as the Standard's three quotes); the owner above it, always with a logged reason. A bank-detail change cannot be released by a reason, the owner's included: only the call-back to the number on file, by someone other than the requester, clears it. A sub payment with no lien waiver no longer has "Release Without It": it needs the waiver recorded, or the owner's release with a reason. Whoever entered a bill or set up the vendor cannot release its payment.

- **Reporting (2026-10-20):** the accounting choices default to expensing Mercer & Bond development costs, percentage of completion for tax, and overhead shared by total direct cost, each labelled "confirm with your accountant"; group figures are consolidated at the subsidiary's cost (SD Plumbing and SD Electric markup to the firm eliminated); close-out starts at 85% of estimated cost, and a cost code off by 10% and $500 or more can be proposed to the price book, the owner approving each.
- **Item library (2026-10-20):** the owner or a PM approves or declines what the library proposes from use; a declined proposal never returns; a sent document never changes when the library does; the field sees items without prices.

- **Week 4 (2026-10-20), calls the lanes made that Alan can change:**
  - The three-quote rule records the exception and raises a finding; it does not block an order. Every subcontract is covered at any amount. The lane recommends keeping it non-blocking below $10,000.
  - Changes to the checklists' thresholds, and every Company › Changes approval, are the owner's only.
  - Workload proposes a named person with room, and the manager approves. Overloaded means three or more overdue, or eight or more open and twice the firm's median. It is never shown as a ranking of people.
  - A benchmark needs three comparable closed jobs. A job more than 15% above their median is flagged with its cause.
  - The server's nightly improvement loop is off until `LOOP_RUNS=on`; the AI rewording is off until `LOOP_AI=on`.
  - Every message is due the day it arrives.
- **Decided by Alan, 2026-10-20 ("Go"; reversible):** the controller prepares the weekly Payment Run and the owner releases it in one tap, billing the backup; "We Owe" is approved bills, equal to the books, with bills awaiting approval on their own line; crews stay in English until Jeanette has reviewed the Spanish.

## 7. Later (Alan deferred)
- NY rules (§7): "I need to better understand this."

## 8. Done recently
Full detail is in `docs/DECISIONS.md`.
- Week 4 (2026-10-20, merged af76462, pending the full net and deploy): the improvement loop (Report a Problem working again and synced, one queue, the owner approving, checked a month later), the whole-meeting reader, role specialists with planted-bank recall 20/20 and precision 43/43, the savings ledger, workload, cost intelligence (jobs spending more than they bring in, benchmarks into one price book, receipt prices, the driver's route), the scripted month back above v11.2 (261/292, $1,937, 0 days), and Alan's three calls built.
- Reporting proven end to end (2026-10-20, pending the full net): every report recomputed from the records to the cent in a test, the ties on screen, drill to the bank line, manual journals flagged, P&L by project and client, cash basis, intercompany eliminated, line income to cost, close-out estimate against actual proposing price-book changes for the owner, overhead and break-even, the 13-week cash forecast as a report, Excel on every tab, Ask reading the reports. Eight money errors found and fixed at the root.
- The item library and Spanish for the field (2026-10-20): one library fills every typed line (estimate, CO, invoice, PO, RFQ, bill, request, receipt), learns from use with the owner or PM approving; the foreman, crew and driver read every screen in Spanish by their setting, chat lines translated on request.
- Subcontractors and the Payment Check (2026-10-20): subcontracts on the PO with scope, changes and retainage; pay applications against what the site measured; lien waivers per payment and per job; every vendor payment and Payment Run checked against contract, prior payments, receipt, work in place, retainage, credits, duplicates, papers and the bank call-back; holds in Approvals; the per-vendor, per-job ledger in Ask.
- Live jobs on invented demo jobs (2026-10-20): two payers on one contract, ranges, allowances and a paid exploratory phase, the tax credit budget, the contractor who becomes an employee.
- The Standard in the app.
- Inventory before buying.
- The RFQ flow.
- The job chain and overhead model.
- Price watch.
- Order tracking.
- The first integration pass.
- The chief of staff.
- The prevention method (§1.16).
- Click crawler: 11,098 controls pressed, 544 flags fixed by class to 0.
