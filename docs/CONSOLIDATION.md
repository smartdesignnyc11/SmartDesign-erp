# One Place per Thing: The Consolidation Plan

For Alan's yes or no before any screen is rebuilt. Written by the chief of staff, 2026-10-21, from the information map (`docs/IA_MAP.md`, `tests/ia_map.py`) and four role experts who each worked a full day phone first (owner, PM, coordinator, foreman). Spec: BACKLOG §1.34.

**The answer in four lines.**
- Every kind of work gets one list. Every person gets one Today that also shows what will delay a job before it does.
- Tasks become one list on the phone that opens on what is due soon. A tap opens the task, not an edit form.
- About 30 places fold into filters or go away. No new page, list or queue is added.
- The build is three lanes, about 30% of a week, starting after the weekly reset. That is more than the 15–20% we planned; the reason is in section 4.

## 1. What the Map and the Experts Found

**The same work sits in many places.**

| What | Places on the PM's phone | Target |
|---|---|---|
| His to-dos | 14 screens | 2 (Today and Tasks) |
| Decisions | 10 | 2 |
| Materials to buy | 19 | 2 |
| Schedule lines | 25 | 2 (Schedule and the job's look-ahead) |
| "What do I owe today?" | 17 (owner 16, coordinator 16, billing 11) | 2 |
| "What is late or at risk on my jobs?" | 27 (owner 27) | 2 |

The phone reaches the same pages as the desktop: owner 77, PM 74, coordinator 57. Two pages appear under two or more names: The Brain and Chief of Staff are the same seven tabs, and Sales appears under four names. The experts counted the same picture by hand. The owner found tasks in 11 places, approvals in 10, findings in 10 and decisions in 7. The coordinator found "late to order" in 6. The foreman found one sub no-show shown in 8.

**The counts disagree.**
- The map found 8 labels with more than one number. "Next 7 Days" reads 16, 10 and 11 for the owner, and 4, 10 and 11 for the PM.
- The experts found more:
  - The rail's Today badge does not match Do Now: 22 vs 34 for the owner, 15 vs 20 for the PM, 11 vs 20 for the coordinator.
  - Open decisions read 3, 5, 7, 8, 11 and 12.
  - "Late to order" reads 3, 4, 5 and 7.
  - Ask says the PM has 5 open tasks; the Team tab says 9.
  - Money: the Kleins invoiced $238,015 on one screen and billed $253,684 on another. Windows not billed reads $13,970 and $20,270. Receipts to approve reads 6 and 2. Hours to approve reads 4 and 2.

**Warnings arrive late or never.**
- Over the next 10 working days there are 42 things that delay a job if nobody acts. Counted per person who must act, that is 68 items.
  - 14 of the 68 (21%) are on that person's first phone screen without scrolling.
  - 9 are below the fold.
  - 45 (66%) are not on the first screen at all.
- Over a 21-day scan:
  - 40 of the 68 never reached the person's first screen;
  - 6 were on none of that person's screens;
  - 4 appeared only once already late.
- No inspection to book, no submittal and no crew request reached a first screen.
- What does reach Today is mostly already late, so it pushes next week's items off the screen.
- The one real delay in the data was flagged as late nowhere: the insulation arrives 9/16 and is needed 9/11 (the foreman says 9/14).

**The task module on the phone is not fit yet.** All four experts say so (owner 4, PM 4, coordinator 4, foreman 6).
- There are five task lists with three different counts.
- The Tasks page opens on "Nothing due today" for five roles, and four of them have work due this week.
- Rows are 130–185px tall, so three fit on a screen. Most of the text is 11–13px. The done circle is 30px.
- Tapping a task opens an edit form with the keyboard up.
- Handing a task to someone means typing their name, and that person gets no notice.
- The foreman's own work rows are the best of them.

**Grades** (out of 10): (a) priorities before delays, (b) tasks on the phone, (c) clean, (d) one place.

| Expert | (a) | (b) | (c) | (d) |
|---|---|---|---|---|
| Owner | 4 | 4 | 4 | 3 |
| PM | 5 | 4 | 5 | 3 |
| Coordinator | 5 | 4 | 4 | 3 |
| Foreman | 5 | 6 | 5 | 4 |

The experts are AI role experts, not his team. His own ten minutes on the phone outrank them.

## 2. The Recommendation

### 2.1 One list per kind of work

Each kind of work has one list. Today shows only the part that needs you. Every other place either shows a count that opens the list, or nothing.

| Kind | The one list that stays | What Today holds | Becomes a filter of the list | Folds in or goes away |
|---|---|---|---|---|
| To-dos | **Tasks** | Mine: overdue, due soon, offered to me | Projects › Tasks (a job chip), Sales (a chip), Team (for managers) | The Sales Tasks page. My Day for the owner and PM (the designer keeps it as her Today). Task rows on Overview, Dashboard, Chief of Staff and Field |
| Schedule lines | **Schedule** and the job's look-ahead | Lines that will slip: a late predecessor, or a start in 2 days with something missing | Tasks shows a line only when it is assigned to me; it opens as a card, with Edit Schedule second | Schedule rows on Projects › Tasks, Materials, Permits, Costs, Design, Approvals |
| Decisions | **Decisions**, per job and All Jobs | Due by the date the work it holds needs it | Approvals › Decisions | Rows on Dashboard, My Day, Chief of Staff, Projects › Tasks and Inbox "To Decide". One count everywhere, showing who it waits on and what it holds |
| Materials and selections | **Buy Board**: estimate lines and selections in one list, one meaning of "late" | Order-by within its lead time, and anything arriving after it is needed | Materials (the job's chip) | The Purchasing overview's own list (it keeps counts). Rows on Overview, Dashboard, Decisions, Schedule, Costs, Field, My Day |
| Deliveries | **Deliveries** | To reconfirm 48 hours ahead | The job's Deliveries | "Late to Site" on Purchase Orders and "In Transit" on the Buy Board become counts that open it |
| Field requests | **Requests**: one form (Raise › Materials and Requests merge) | Needed within 2 working days, not ordered | The driver's Route | Overview rows |
| Submittals | **Submittals**, opening on All Jobs | Submit-by or approve-by inside its window | Approvals › Submittals | Rows on Documents (the files stay) |
| Inspections | **Permits**, with "book by" on the row | Book-by inside the booking window | none | Rows on Overview |
| Site questions | **Approvals › Site Questions**; the job's Field › Open Items | Unanswered, addressed to me | none | Rows on Projects › Tasks and The Brain |
| Subs to confirm | the job's **Site** (foreman) and Schedule | Not confirmed for the next 4 working days | none | none |
| Insurance (COI) | **Vendors** | Expired, or lapsing within 30 days with an order or a booking ahead | none | Obligations (keeps the company's own insurance only), Dashboard, The Brain |
| Approvals | **Approvals** (the full list behind Today's filter) | Mine to approve | Company › Changes becomes its "System Changes" filter. Proposals from mail live here only | Inbox's "To Decide" copy. Tab names fixed: "System Changes", Lessons under Lessons, a Change Orders filter |
| Bills | **Bills & Payroll** | Mine to approve, including any paid before approval | Approvals › Bills reads the same query | Overview, The Brain. Billing's landing page gains one count of vendor bills, the same number as Approvals |
| Findings and money flags | **Caught for You**, one card per record with every finding about that record inside it | The owner sees what only the owner acts on. Bank matching becomes one line with its count and dollars; the rows go to the controller's Banking | Controls (the controller's), Brain › Findings | Chief of Staff's Findings. The duplicates inside the list (the dumpster shows four times) |
| The assistant | **Ask** (the button on every screen); **The Brain** under Company for the owner's rules and lessons | none | none | The Chief of Staff menu entry |
| Pages under two names | Sales, Projects, Drawings, Design: one page each | none | none | The old names forward to the one page with its filter, so bookmarks and links still land |
| Daily logs to read | Field › Daily Log | One line, "Logs to read (6)", that opens the first log with Next | none | Six separate rows |

The field: the foreman's Today is his queue and Site is his job's register. Raise is where he starts something and shows only what he raised. Crew lists people, not schedule lines. The crew's Clock is their task list, so the separate Tasks page leaves the crew's menu.

### 2.2 Today's "Coming Up" band

Coming Up is a band on each person's Today: the things that will delay a job if nobody acts, shown before they are late. The rules that already know what is coming feed it. It is not a new page.

- **What feeds it.** The existing rules:
  - order-by dates, now including anything arriving after it is needed (the insulation);
  - inspections to book, using the real booking window instead of a fixed 5 days;
  - submittals on all jobs;
  - decisions, dated by when the work they hold needs them;
  - the foreman's "tomorrow not ready";
  - subs not confirmed;
  - insurance lapsing with a booking ahead;
  - the one at-risk rule the fix lane is building. Projects, Health, Ask and Coming Up all read that one rule.
- **The window.** Three weeks, the Standard's "Think ahead".
- **The order.** Days left before it delays the job. When two items have the same days left, law and landmarks rank above schedule, and schedule above cost.
- **What a row says.** The thing, the job, the date it must happen by, the days left, who it waits on, what it holds ("holds rough plumbing 9/10"), and one action (Book, Order, Chase, Confirm). Opening it shows the Standard's escalation format and the "because".
- **Overdue doesn't crowd it out.** Late items fold into one line per kind, for example "5 late to order, $X". Each line opens its list and still counts. Anything blocking the crew today stays at the top of Do Now. Five Coming Up rows show, then "N more".
- **One number.** Today's badge is the Do Now count, the same on the rail, the bar, the tab and in Ask. Coming Up shows its own count on its header.
- **The assistant acts first, for approval.** It drafts the chase for a client selection due in five days. Nothing reaches a client or vendor unless a person sends it.
- The job's Plan gets the same items as a filter. The client's portal keeps "Waiting on You", which the map found already works best (9–19 working days ahead). We add only plain words saying what moves if it is late.

### 2.3 The task module on the phone

1. **One list.** Tasks, with chips: Mine (the default), Team (for managers), a job, Sales. Projects › Tasks and Sales Tasks are this same screen with a chip set. "Next 7 Days" is one number everywhere.
2. **It opens on Due Soon:** overdue, today and the next 7 days, grouped by day. It never opens empty while work is coming.
3. **Rows 64–72px tall:** a 44px check circle, a 16px title on up to two lines, the due date and job on one line, and the owner's first name (not initials). Swipe for Later or Hand Off. The same actions are also in the task sheet for anyone who doesn't swipe.
4. **One header line:** a search icon and one filter chip. New Task is a round + button above the bar, bottom right.
5. **A tap opens the task sheet,** and the keyboard stays down. The sheet holds:
   - the title;
   - quick dates (Today, Tomorrow, Next Week, Pick);
   - a person picker that sends the hand-off: the person sees it on their Today with Accept or Decline, and the sender owns it until they accept;
   - where it came from, one tap away;
   - the checklist;
   - comments and photos, with history kept (a note is never overwritten);
   - the blue button: the task's next step where it has one (Draft the Update, Order, Book), otherwise Done.

   Edit is secondary. A schedule line opens the card first, with Edit Schedule second.
6. **The same sheet everywhere:** Today, Tasks, the job, Sales, and Ask's answers.
7. **No duplicate tasks.** Make It a Task offers to attach to the matching decision or task instead of creating a third copy.
8. **Other fixes:**
   - one priority scale;
   - a "waiting for signal" mark when offline;
   - the crew sees Mine only, with the foreman's Started, % and Done rows;
   - Done asks for a photo where the Standard needs proof.

### 2.4 Each role's first phone screen, top to bottom

Every first screen fits in no more than three phone screens, with no empty card above the fold.

| Role | Top to bottom |
|---|---|
| Owner | Three pulse numbers. Do Now (5): only what only the owner can do (law and permits, signatures, money over his line, client escalations, a bank-detail change, a payment hold). Coming Up: job delays inside their lead time, which rank above a sales follow-up due today. One line: "Caught for You: N, $X". Morning Brief, folded |
| PM | Do Now: crew blocked today, client money and messages, site questions to him. Coming Up: inspections to book, submittals, subs to confirm, decisions by need date, materials arriving after they are needed, each with its days left. Overdue as one line per kind. "Tasks due soon: N", which opens Tasks |
| Coordinator | Do Now: the driver's route to approve before the van leaves, crew requests needed within 2 days, site questions. Coming Up: order-bys inside their lead time, late arrivals against need dates, insurance lapsing with a booking ahead, deliveries to reconfirm. One line: "5 late to order, $X" |
| Foreman | A big Clock In. Blocking the Crew: blockers, tomorrow not ready, subs to confirm, an inspection today, materials late against need. Then Today's Work at 64px or more. The packing slip moves to the camera button and the slogan goes. A Raise button sits on Blocking the Crew; the bar stays as decided, with Chat |
| Crew | Clock In, then today's work (Mine) |
| Driver | The store run first. The stock card shows only when something is reserved. Clock In no longer sits over the heading |
| Designer | From the Field, then decisions and drawings due by need date. No empty card |
| Billing | Unchanged, plus one count of vendor bills |
| Controller | Banking's to-review list first, now holding the bank matching that leaves the owner's Today. The six action buttons fold behind one |
| Client | Waiting on You first, without "retainage", and never two progress numbers that contradict each other |

### 2.5 One number, checked every build

- `tests/ia_map.py --check` joins the full net (`run_all.sh`) as a ratchet.
- A small file in `tests/` records today's failures per check: one place 142, one number 8, warnings not on the first screen 54, warnings too late 40, tasks 26, clean 5, words 1.
- A number may go down, never up. Each merge lowers the file in the same commit.
- End-of-round targets on the demo:
  - one number 0, tasks 0, clean 0, words 0;
  - warnings too late 0: every warning reaches its person's first screen at least 3 working days ahead;
  - warnings not on today's first screen: under 15, each one behind "N more" because something with fewer days left outranks it;
  - one place 0: each remaining place is either removed, or named as context in the registry with a reason the chief of staff signs off.
- The counts lint gains every disagreement the experts found:
  - the rail vs Do Now;
  - decisions;
  - late to order;
  - receipts and hours;
  - Ask's task counts;
  - the four money pairs.
- The check matches records by their words, so its counts are a floor. It catches what it can see; it does not replace the people walk.

### 2.6 Design gate (BACKLOG §1.16)

No new store, list, queue, page or menu item. New fields are allowed only where a date is missing on an existing record: a need date on a line, book-by on an inspection, confirmed-at on a sub's booking.

| Change | Registry entry it extends |
|---|---|
| One task list, chips, the sheet, hand-off | Task: `tkItems()` / `tkAll()` over `DB.tasks`, `p.tasks`, `hbtasks`, `DB.obligations` (stores unchanged); list `tkall`; owner matched by user id (the fix lane's `tkOwnerMatch`) |
| Coming Up | The one queue, Today (`home`, `tdyModel`), ranked by `standardRank` plus days left; fed by `PRED.orderThisWeek`, `PRED.lateMaterial` (extended to "arrives after it is needed"), `PRED.inspToBook` (booking window), `PRED.lateSubmittal`, `decDue` / `PRED.clientDecisionsDue` / `PRED.heldByDecision`, `fTaskNeeds`, the sub's confirmation on its schedule line, `PRED.vendorsBlocked`, and the fix lane's at-risk rule (`PRED.jobsAtRisk`) |
| Approvals and mail proposals | Approval: `PRED.waitingOnMe`, list `mapprove`; `DB.changes` shown as its System Changes filter; inbox item `cmListFor`, list `comms`, without the proposals |
| Buy Board as one list | Material: `PRED.toBuy` / `buyNeeds` rows; list `proc`; `mat` is its job filter |
| Findings | `CATCH` / Caught for You, one card per source record; the Brain's Findings and the Chief of Staff read it |
| Folded and renamed pages | The declared `MENU` and `ROLE_VIEWS`, pinned by menu_test; old view ids forward to the one page with its filter |
| The registry itself | Not built yet: the structure lint of §1.16 never was. `ONE_PLACE` in `tests/ia_map.py` becomes the one registry (noun, its one list per role, the queue, context pages), read by ia_map's check and menu_test. No second registry |

## 3. Think Past the Ask

**What he isn't thinking about.**
- **Removing a place someone relies on.**
  - The PM found the insulation only on Overview's "Needs Attention".
  - The owner calls the Team tab his best screen.
  - Every place that goes is listed with what each expert found there and where it now lands. Overview and Dashboard keep counts that open the list.
  - The Team tab stays, with a nudge, and never ranks people.
- **Links and bookmarks.** Old page names live in more places than the menu:
  - toast Open links and push notifications;
  - the server's briefings and the assistant's answers;
  - the specialists' "go to" targets;
  - saved reports;
  - links in mail.

  Every old name forwards to its new place with the right filter. The click crawl proves each one lands.
- **The counts change under people.** The owner's Caught for You loses about half its 34 rows (17 are bank lines). The controller's list grows when bank matching moves there. Each person sees one line on first open saying what moved and where. The month must hold at 261/292, $1,937 and 0 days, both reading the whole list and reading only the first five.
- **The folds move work onto roles the experts didn't walk.** Bank matching goes to the controller, vendor bills to billing. The map covers all ten roles. The re-walk adds the controller.
- **The client portal.**
  - It is still closed on the hosted copy until each client's own rows exist, so this round changes it on the demo only.
  - It keeps "Waiting on You".
  - It loses "retainage".
  - It never shows two progress numbers that contradict each other. That is an S1 the fix lane's list misses (below).
- **Early needs a date.** The inspection rows show "—", and the insulation has three dates. Part of the fix is one need date per line, taken from the schedule, not a new screen.
- **Hiding isn't security.** The crew seeing only their own tasks is a screen rule. The hosted copy still sends a field phone other jobs' tasks, so the server rule must follow before real jobs load. This is the same blocker as the field money files.

**How to make it better.**
- One card per record, with every finding about it inside. The dumpster becomes one card instead of four.
- The assistant drafts the chase before the date, for approval.
- Coming Up's rows read in the Standard's escalation format, so the ranking and the "because" are the same thing.
- New field words (Blocking the Crew, Coming Up) go into the Spanish file marked not yet reviewed.

**What goes wrong if it isn't thought through.**
- **Money.** A fold can bury money, as it did when the Kleins' $68,265 check fell to 13th. The owner's one-line rollup never swallows a bank-detail change, a payment hold or a client payment waiting. Those stay as their own rows.
- **Noise.** If everything is "coming up", nothing is. Coming Up shows five rows, each with its days left, and only what is inside its lead time.
- **Law.** DOB, LPC and insurance items rank above schedule and cost when their days left are equal.
- **The books.** The Standard's money duties (books by the 10th, collections at due, 7, 15 and 30 days) stay tasks with a named owner.
- **The phone.** Nothing scrolls sideways at 390px. Targets are 44px, 8px apart. Swipe actions also have a tap path.
- **Data.** Tasks stay in their stores behind one accessor, so nothing moves and nothing is lost. Every fold shows the counts per person before and after.

## 4. The Build Round

It starts after the fix lane merges, because the fix lane owns the at-risk rule and "Mine". It also starts after the weekly reset.

| Order | Lane | Builds | What must pass (measured) | Usage |
|---|---|---|---|---|
| 1 | Tasks | 2.3, and the task rows of 2.1 (Sales Tasks, Projects › Tasks, My Day become chips; the crew sees Mine only) | ia_map tasks 26 to 0; "Next 7 Days", "Today" and "Overdue" one number each; find it again at 390px for every task create; a hand-off reaches the receiver's Today with Accept (the coordinator's case); the month holds | 6–9% |
| 2 | Coming Up | 2.2 and 2.4, plus the missing dates (need date per line, book-by per inspection, confirmed-at per sub) | Warnings too late 40 to 0. A planted bank of the kinds the demo lacks: a late predecessor, arriving after needed, insurance lapsing with a booking, a consultant's answer due, an LPC filing, a delivery to reconfirm. Each must show on its owner's first phone screen before its date, and the test fails if it shows on or after. Clean 5 to 0. The month holds both ways | 8–10% |
| 3 | One place | The rest of 2.1, the forwards for old page names, the counts in 2.5, Caught for You one card per record, bank matching to the controller | One place 142 to 0 (removed, or named as context and signed off); one number 8 to 0 plus the experts' pairs in the counts lint; menu_test re-pinned; every old page name lands; per-person counts before and after with nothing lost | 7–9% |
| | Merges and the full net | Merge 1, then 2, then 3. The ratchet goes into the net with lane 1 and tightens at each merge. The month runs both ways after each | The full net plus ia_map green on the merged build | 2–3% |
| | Proof | The owner, PM, coordinator, foreman and controller each work a half day on the phone on the merged build. Then Alan's ten minutes | Every grade at 7 or better on (a) to (d); no S1 or S2 left on what this round touched | 3–5% |

Lanes 1 and 2 can run side by side: tasks owns the list and the sheet; Coming Up owns Today's page and calls the sheet. Lane 3 runs after lane 1, because it folds task pages into lane 1's list.

**Usage: about 30% of a week (26–36%), not 15–20%.**
- The 15–20% assumed one or two lanes. The map found three seams: tasks, Today, and one place.
- The warnings need data (dates on records), not only screens.
- The map's walk takes about 20 minutes per run, and every lane runs it.
- The proof needs people on the phone again.

On the planning numbers this week already stands near 50–55%: week 4 at about 40%, the map and experts at 8–12%, plus the fix lane. Check the real meter. A 30% round fits the next week under the 60% rule; it doesn't fit this one.

It can drop to about 20–25% by skipping the expert re-walk and relying on the checks and his ten minutes. I don't recommend it: every miss this month was a check that didn't look the way a person looks.

## 5. What He Must Decide

1. **Yes to this plan and the build round, about 30% of a week, starting after the weekly reset.** Recommended: yes. The pages listed in 2.1 fold or go, and every old link forwards.
2. **Today's order for every office person.**
   1. Safety and law.
   2. Crew blocked today.
   3. Client money and client messages (his 10-20 confirmation, still waiting).
   4. What will delay a job inside its lead time, by days left.
   5. Overdue, one line per kind.
   6. Sales follow-ups.

   On the owner's Today, bank matching becomes one line and moves to the controller. Recommended: yes. It is the Standard's order and its "think three weeks ahead". The month must hold before it ships, and it is reversible.
3. **A vendor's missing W-9 is a warning on a purchase order, not a stop.** The order gates are built:
   - an order stops when the vendor's insurance is missing or expired and they already have an order open, or the order puts them on site (a subcontract or a service);
   - an overage on the estimate line needs a reason, and the owner approves anything over $1,000;
   - no W-9 on an order of $600 or more is a warning.

   Recommended: keep W-9 as a warning, because the Payment Check already holds every payment until the W-9 is on file. No money can leave without it, and stopping the order would only delay material over a paper needed to pay. Insurance stays a stop, because an uninsured vendor on site is a law and safety risk the day they arrive. Add a W-9 request draft on the warning, for approval.

**For the main session, not for Alan.** The fix lane's list misses two S1s the experts found:
- the client portal shows "51.65% certified" beside "14% measured on site";
- bills already paid (AMP-311, WW-2026-118) still sit in the Payment Run, which risks paying them twice at the bank.

Recommended: add both to the fix lane. The foreman's S1 (insulation arriving after it is needed) is lane 2's first planted case.
