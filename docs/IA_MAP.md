# The Information Map: Who Sees What, Where, and Before It Is Late

**Asked by Alan, 2026-10-21:** "We need to make sure that the desktop and mobile versions give each role the information they need to do their job, see what priorities there are before they become delays in the project. We need to make sure the pages are clean and the information is easy to understand. The task module is one of the most important and it isn't great on mobile... We also need to make sure there aren't 12 different sections to see similar information."

**What this is.** A measurement, not a fix. No app code changed. `tests/ia_map.py` (reader in `tests/ia_js.js`) signs in as each of the ten seats, at 1440 and at 390, opens every page the role may open (`ROLE_VIEWS`, less Mercer & Bond and the Ask page) and every filter of the queue pages (Today's Do Now tabs, the task list's views), and reads each screen: heading, tabs, sections, the count each shows, and which records each section lists. 830 screens in all (415 per screen size). The tables behind every number here are in `review/ia/tables.md`; the raw read is `review/ia/data.json`; screenshots of every task screen and every role's first screen at 390 are beside them.

Run it: `python3 build.py && cd tests && ./slot.sh python3 ia_map.py` (about 20 minutes on this machine), then `python3 ia_map.py --check` for the checks in section 7. The checks fail today by design: 276 of 469.

## Headline

1. **The same work sits in many places.** The PM's open to-dos show on 14 screens, on the phone as on the desktop; his decisions on 10; materials to buy on 19; schedule lines on 25. The question "what do I owe today?" is answered, in part, by 17 different screens for the PM, 16 for the owner and the coordinator, and 11 for billing. "What is late or at risk on my jobs?" is spread over 27 screens for the owner and the PM.
2. **The phone is the desktop, narrower.** Every role reaches the same pages on the phone as on the desktop (PM 74, owner 77, coordinator 57). The four-button bar is right, but behind the hamburger sits the whole office.
3. **Most delay precursors never reach the person who must act.** Of 42 things that become a delay in the next 10 working days if nobody acts (68 person-item pairs), 14 pairs (21%) are on that person's first phone screen without scrolling, 9 are below the fold, and 45 (66%) are not on the first screen at all. None of the 8 inspection pairs, none of the 13 submittal pairs and none of the 4 crew-request pairs reach a first screen. What does reach it is mostly already late: the first screen fills with what has passed its date, so what will pass its date next week is pushed off.
4. **The task module on the phone is not ready.** There are five task lists, three different counts for "Next 7 Days", a Tasks page that opens empty for five roles while work is due this week, rows 130 to 185 pixels tall (two and a half to a screen), and a tap that opens an edit form with the keyboard up and "Assigned To" as free text.
5. **Pages are long.** A quarter to a half of each role's pages are taller than three phone screens. The foreman's Today is 4.9 screens, and tomorrow's "5 tasks not ready" sits at the bottom of the fourth.

## 1. How Many Places Show the Same Thing

Screens per noun, per role, desktop / phone. A screen counts when it lists at least one record of the noun (records are found by their own words; section 8 says where that is weak). The page's own filters count as the page. Reference pages (the Standard, Connections, Settings, documents and photos) are left out.

| Noun | Owner | PM | Coordinator | Foreman | Crew | Driver | Designer | Billing | Controller | Client |
|---|---|---|---|---|---|---|---|---|---|---|
| tasks (to-dos) | 12 / 12 | 14 / 14 | 11 / 11 | 1 / 1 | 1 / 1 | - | 2 / 2 | 8 / 8 | 5 / 5 | - |
| schedule tasks | 25 / 23 | 25 / 23 | 18 / 17 | 7 / 7 | 5 / 5 | 2 / 1 | 9 / 8 | 6 / 6 | 8 / 7 | 3 / 3 |
| approvals (not otherwise named) | 4 / 4 | 3 / 3 | 3 / 3 | - | - | - | - | 2 / 2 | 3 / 3 | - |
| inbox mail | 2 / 2 | 2 / 2 | 2 / 2 | - | - | - | 1 / 1 | 2 / 2 | 2 / 2 | - |
| decisions | 9 / 9 | 10 / 10 | 9 / 9 | 1 / 1 | 1 / 1 | - | 4 / 4 | 3 / 3 | 3 / 3 | 3 / 3 |
| materials to buy | 18 / 18 | 19 / 19 | 19 / 19 | 4 / 3 | 3 / 2 | - | 6 / 6 | 3 / 3 | 5 / 5 | 3 / 3 |
| field requests | 3 / 2 | 3 / 2 | 5 / 4 | 2 / 2 | 1 / 2 | 2 / 2 | - | 1 / 0 | - | - |
| submittals | 1 / 1 | 3 / 3 | 1 / 1 | - | - | - | - | - | - | 2 / 2 |
| inspections | 3 / 2 | 3 / 2 | 3 / 2 | 1 / 1 | - | - | - | 1 / 0 | 1 / 1 | - |
| site questions / RFIs | 6 / 5 | 7 / 6 | 7 / 6 | 2 / 2 | 1 / 1 | - | 3 / 3 | 1 / 0 | 1 / 1 | - |
| COI lapses | 6 / 6 | 5 / 5 | 6 / 6 | - | - | - | - | 3 / 3 | 6 / 6 | - |
| bills | 6 / 6 | 4 / 4 | 3 / 3 | - | - | - | - | 3 / 3 | 3 / 3 | - |
| purchase orders | 8 / 8 | 6 / 6 | 7 / 7 | 1 / 1 | 1 / 1 | - | - | 2 / 2 | 7 / 7 | - |
| money flags | 1 / 1 | 1 / 1 | 1 / 1 | - | - | - | - | 1 / 1 | 1 / 1 | - |
| subs to confirm | 3 / 3 | 3 / 3 | 1 / 1 | 3 / 3 | 1 / 1 | - | 2 / 2 | 1 / 1 | 1 / 1 | - |

An approval about a decision, request, bill, submittal or site question is counted as that record (the same thing shown again), so "approvals" here is only what has no other name (payroll, hours, lessons, meeting proposals).

### The clusters: screens (sections) that answer the same question, desktop / phone

| Role | What do I owe today? | What is late or at risk on my jobs? | What has to be bought or ordered? | Where is money leaking or owed? |
|---|---|---|---|---|
| Owner | 16 (18) / 16 (18) | 27 (36) / 26 (35) | 24 (25) / 24 (25) | 10 (12) / 10 (12) |
| PM | 17 (18) / 17 (18) | 27 (36) / 26 (35) | 23 (24) / 23 (24) | 10 (11) / 10 (11) |
| Coordinator | 16 (17) / 16 (17) | 20 (25) / 20 (25) | 22 (24) / 22 (24) | 7 (8) / 7 (8) |
| Foreman | 2 (2) / 2 (2) | 7 (13) / 7 (13) | 5 (7) / 4 (6) | 0 |
| Crew | 1 (1) / 1 (1) | 5 (7) / 5 (10) | 4 (4) / 4 (4) | 0 |
| Driver | 0 | 2 (3) / 1 (2) | 2 (2) / 2 (2) | 0 |
| Designer | 4 (4) / 4 (4) | 9 (14) / 9 (14) | 6 (6) / 6 (6) | 1 (1) / 1 (1) |
| Billing | 11 (11) / 11 (11) | 6 (7) / 6 (7) | 4 (4) / 4 (4) | 8 (9) / 8 (9) |
| Controller | 8 (8) / 8 (8) | 9 (10) / 8 (9) | 9 (10) / 9 (10) | 9 (11) / 9 (11) |
| Client | 0 | 3 (10) / 3 (10) | 3 (4) / 3 (4) | 2 (2) / 2 (2) |

Target: two per question for an office role (Today and the one list behind it), one for a field role.

### Where the duplicates come from (PM, the worst; the owner and coordinator follow the same pattern)
- **Tasks:** Today's Do Now, Today › Tasks (the task page), Projects › Tasks, Sales Tasks, My Day, the job's Overview, Calendar, Dashboard, Chief of Staff, the Sales pipeline (three routes to it), Field. Sales Tasks alone holds 11 of the 22 to-dos he can see.
- **Decisions:** Decisions, Today (Approvals), Approvals, Dashboard, Calendar, My Day, the job's Overview, Chief of Staff, Projects › Tasks.
- **Materials:** Purchasing, Buy Board, Selections, Materials, Overview, Dashboard, Decisions, Schedule, Costs, Purchase Orders, Deliveries, Field, My Day, Today.
- **Schedule lines:** Schedule, Overview, Projects › Tasks (19 schedule lines among its 25 rows), Materials, Dashboard, Permits, Field, Design, Approvals.
- **Pages that are the same page under two names:** The Brain and Chief of Staff (the same seven tabs: Chat, Findings, Activity, For You, Checklist, The Brain, Every Chain); Sales four times (`leads`, `hbdeals`, `ovsales`, `scleads`); Projects twice (`port`, `ovjobs`); Drawings twice (`plans`, `sdraw`); Design twice (`studio`, `ovstudio`); and My Day, the designer's Today, open to the owner and PM as a second Today.
- **Field roles are close to clean.** The foreman's duplicates are schedule lines on Crew, Drawings, Raise and Requests, and materials on Site, Schedule and Raise. The crew has two task lists (Clock's Today and Tasks). The driver is clean.

## 2. One Question, One Number

The same label with different counts on different screens of one role:
- **"Next 7 Days":** owner 16 (Today › Tasks), 10 (Projects › Tasks), 11 (Sales Tasks); PM 4, 10, 11; coordinator 2, 10, 11; designer 1, 10.
- **"Today":** owner 6, 1, 5; PM: Projects › Tasks 1, Sales Tasks 5, while Today's Tasks filter shows 4 and the Tasks page's own Today shows nothing.
- **"From the Field":** coordinator 2 on Requests, 3 on Field.
- **The designer's Today** shows a "Due or Late 7" chip and, below it, "Due This Week: Nothing due this week."
- **Purchasing and the Buy Board** open with the same tiles ("Late to Order 5, Order This Week 0, No Price 19"). Under them, Purchasing lists the 27 estimate and material lines; the Buy Board's table lists the selections (fixtures, hardware, lighting), whose first two rows are 21 days late to order and are not in the "5". The tile does not count the rows under it.

Each list is right about its own scope (mine, the job's, sales). The person sees one word with three numbers.

## 3. Delay Precursors

As of the demo day (Thu 2026-09-03), window to 2026-09-18 (10 working days). 42 items, each with the person who must act (68 pairs). Each was looked for on that person's first screen on the phone and the desktop, and on each of 21 working days from 2026-08-20 to 2026-09-18 (the app's day moved; no day hooks run, so nothing is created or escalated by the scan). Full table: tables.md section 5.

| Kind | Items | Pairs | On first phone screen, above the fold | Below the fold | Not on first screen |
|---|---|---|---|---|---|
| Order-by date (lines and selections) | 13 | 16 | 4 (all already late) | 0 | 12 |
| Decision due | 7 | 14 | 6 | 3 | 5 |
| Inspection to book | 4 | 8 | 0 | 0 | 8 |
| Submittal | 8 | 13 | 0 | 1 | 12 |
| Crew request needed within 2 days | 2 | 4 | 0 | 0 | 4 |
| Sub to confirm within 4 days | 3 | 6 | 0 | 3 | 3 |
| Site question | 3 | 3 | 3 | 0 | 0 |
| COI lapsed or missing | 2 | 4 | 1 | 2 | 1 |

**Who is served.** The client sees her own decisions (3 of 4 above the fold, from 9 to 19 working days ahead). Site questions reach the person they are addressed to. Everyone else is served late or not at all:
- **Coordinator (Chen):** a site question and four late order-bys fill Today's first five rows, so the next ones (GWB boards 9/11, radiant heat mats 9/15, interior doors 9/16, exterior paint 9/17) never reach her first screen in the whole scan; they sit behind "N more". The selections on the Buy Board (the wall-mount faucet and the shower set, 21 days past their order-by while their submittal is revised; the fireclay sink, 9/18) reach none of her first screens: Today's Buy Board lines are the estimate and material lines only. Field requests needed tomorrow (blue tape, 9/4; studs, 9/8) are on Requests, not Today. Window Works' insurance lapsed 8/15 and Window Works is booked on site 9/9: on her first screen at row 7, y 866, below the fold.
- **PM (Alan):** 21 of 26 pairs are not on his first screen. All four inspections (the plumbing permit was needed by 9/2; rough plumbing, rough electrical and the energy-code special inspection must be booked by 9/17), all six of his submittals (the plumbing fixtures resubmission is a month late), three subs not yet confirmed for 9/4, 9/8 and 9/9, and the decisions due 9/16 and 9/17. The decisions he does see are already past due. The 2nd-floor bathroom re-review (due 9/2) first reached his phone's first screen on 9/3, below the fold.
- **Foreman (Angel):** the three subs to confirm are on his Today, at y 1921, 3402 and 3668 (rows 18, 31 and 34 of the page), two to four screens down. The four inspections that gate his walls are not on his Today; the plumbing permit first appears on 9/9, four working days after it was due. "Tomorrow: 5 tasks not ready" starts at y 2997.
- **Designer (Sarah):** her decisions (interior doors, garden bedroom framing) are on her Today below the fold (y 1017, y 1158); the paint colour decision and the flitch-beam shop drawings are on none of her screens as they open.
- **Owner:** Window Works' lapsed COI is on none of the owner's first screens: the compliance detector flags Tino (no certificate on file, row 6, below the fold at y 871) but not a certificate that has expired. Three of the owner's five Do Now rows are sales follow-ups.
- **Submittals on other jobs** (45 Cranberry's LPC window shop drawings, the flitch beams) are on no screen of the PM or designer as it opens: Submittals opens on This Project.
- **Late predecessors:** none in the demo data (no task starting in the window has a dependency that is late or behind). The class is not exercised; section 8.

**Why.** Today holds approvals, inbox and to-dos. The predicates that know what is coming (`PRED.orderThisWeek`, `inspToBook`, `lateSubmittal`, `decDue` for decisions, `fTaskNeeds`, sub confirmations, insurance expiry) feed pages (Buy Board, Permits, Submittals, Decisions, Site) and the job's Look-Ahead, not the person's queue, except the coordinator's late Buy Board lines. And the queue ranks overdue first, so what is already late always outranks what will be late.

## 4. The Task Module on the Phone

Screens measured at 390 x 844 (`task_*.png`; `_full` is the whole page; `_open` is what one tap on the first row opens).

| Screen | What shows first | Rows (above fold) | First row y | Row height | One tap on a row |
|---|---|---|---|---|---|
| PM Today, All | three pulse numbers, five filter chips | 5 (5) | 262 | 89 | nothing; the only action is the verb (Answer, Choose, Done) |
| PM Today, Tasks filter | as above | 4 (4) | 262 | 89 to 108 | nothing; Done only |
| PM Tasks (`tkall`) | New Task bar, 7 view tabs, Mine / Everyone / Unassigned, search | 0: "Nothing due today and nothing late" while Next 7 Days holds 4 | - | - | - |
| PM Tasks, Next 7 Days | as above | 4 (3) | 320 | 132 to 185 | the full edit form |
| PM Projects › Tasks | job switcher, sub-tabs, finish strip, Process a Meeting, New Task, 7 view tabs, scope, search | 25 (3) | 433 | 132 to 166 | the full edit form |
| Coordinator Today, Tasks filter | filter chips | 8 (7) | 173 | 89 | the Order sheet (good: the next step) |
| Coordinator, Designer, Controller, Billing Tasks | header stack | 0; the first three have work due this week (2, 1, 1) | - | - | - |
| Designer Today | chips, From the Field | 1 (1) | 349 | 283 | nothing |
| Foreman Today, Today's Work | page intro, Packing Slip card, Clock In, For You | 17 (2) | 465 (first task 686) | 111 to 150 | nothing; Update, Started, Done on the row |
| Crew Tasks | header stack | 0: Today is empty; the crew's work is on Clock | - | - | - |

**Verdict: not fit for the phone yet.**
- **Five lists, three counts.** Today › Tasks filter, the Tasks page, Projects › Tasks, Sales Tasks and My Day are separate lists with separate filters and numbers (section 2). Each is a filter of `tkAll()` in the data; on screen they are five places.
- **It opens empty.** The Tasks page opens on "Today", which is empty this morning for the PM, coordinator, designer, billing, controller and crew; for four of them work is due in the next seven days (PM 4, coordinator 2, designer 1, controller 1). The first thing a person reads is "Nothing due today."
- **The work starts halfway down.** On Projects › Tasks the first row is at y 433; three of 25 rows are visible. Rows are 130 to 185 pixels tall because each carries a project bar, source tag, area, notes, a Later button and an avatar.
- **A tap opens an edit form, not the task.** Task, Code, Section, Assigned To (free text), Their Email, Starts, Due, Priority..., with the cursor in the title so the keyboard covers half the screen. There is no comment, photo, history or "where it came from" first. A hand-off is typing a name, not the offer, accept or decline that BACKLOG §1.14 #4 asks for.
- **On Today a task is a title and one verb.** Tapping the title opens nothing. There is no snooze, no hand-off and no open from Today.
- **Targets.** The Today filter chips and the task view tabs are 40 px tall (the house rule is 44); the view tabs scroll sideways off the screen.
- **The foreman's work list is the best of them** (Update, Started and Done on the row, 44 px), but it starts below a page introduction, a Packing Slip card, Clock In and a For You card, and the Say It button floats over the second row.

## 5. Clean Pages

Daily pages on the phone (full table: tables.md section 7).
- **Too long.** Pages taller than three phone screens: owner 24 of 77, PM 25 of 74, coordinator 20 of 57, foreman 6 of 13, crew 5 of 10, designer 9 of 20, billing 11 of 38, controller 9 of 31. Banking is 13.5 screens (the controller's first page), Reports 12.5, the job's Costs 8.5, Schedule 8.3, The Brain 9.6, the Standard 25.
- **The foreman's Today: 4.9 screens, 9 sections, 11 visual groups.** In order: a page introduction, Packing Slip or Receipt, the job and Clock In, For You, Today's Work (17 rows), Now (blockers and the huddle), Put on You, Arriving Today, Who's Here (folded), Tomorrow (5 tasks not ready), Next Two Weeks (folded). What can stop tomorrow is last.
- **The driver's Route** opens with "Picks from Stock: 0, nothing reserved" (an empty card), then Packing Slip, then the store run; the Clock In button sits over the page heading ("Rout").
- **The designer's Today** has an empty "Due This Week" card at the fold, under a "Due or Late 7" chip, and an empty Projects card further down.
- **The owner's Today is the cleanest office page** (two screens: pulse, Do Now, Caught for You, Morning Brief), but Caught for You starts at y 816, below the fold, with 34 rows behind five.
- **Words.** "EAC" on Projects for every office role and the designer; "WIP" on Reports, Ledger and Dashboard; "obligation" on Obligations, Chief of Staff and the owner's Tasks; "retainage" on the client's Overview; "RFI" and "submittal" on the field's Documents, Drawings and Receipts. Each is right for the controller and wrong for the person reading it elsewhere.

## 6. The Consolidation Proposal

The rule: **each noun has one list (its register), and each person has one queue (Today) that holds only what needs them, including what will be late if they wait.** Everything else shows a count that opens the list, never the rows again. This extends `tdyModel` (§1.14 gate record 2026-10-19); it adds no store, list or menu item.

### One place per noun (all office roles; the field rows follow)

| Noun | The one list | Today holds | Keep as a filter of the one list | Fold in or remove |
|---|---|---|---|---|
| To-dos | Tasks (`tkall`) | mine due within 10 working days, overdue, offered to me | Projects › Tasks (the job's filter, same rows and numbers); Sales (the sales filter) | Sales Tasks page; My Day for owner and PM; task rows on Overview, Dashboard, Calendar, Chief of Staff, Field |
| Schedule lines | Schedule, and the job's Look-Ahead (Overview) | lines whose predecessor is late, or that start in 2 days with something missing | - | schedule lines in Projects › Tasks, Materials, Permits, Costs, Design, Approvals |
| Decisions | Decisions (per job, with All Jobs) | due within 10 working days, by its need-by date (`decDue`), before it is late | Approvals' Decisions filter | Dashboard, My Day, Chief of Staff, Projects › Tasks |
| Materials to buy | Buy Board | order-by within 10 working days (coordinator; PM when a decision holds it) | Materials (the job's filter) | rows on Overview, Dashboard, Decisions, Schedule, Costs, Field, My Day: counts that open the Buy Board |
| Field requests | Requests | needed within 2 working days, not ordered | Route (the driver's) | Overview rows |
| Submittals | Submittals, opening on All Jobs | submit-by or approve-by within 10 working days, and every late one | Approvals' Submittals filter | Documents (files stay, rows go) |
| Inspections | Permits | book-by within 10 working days (`inspToBook` widened from the 5-day buffer) | - | Overview, Calendar rows |
| Site questions | Approvals › Site Questions; the job's Field › Open Items | unanswered, addressed to me | - | Projects › Tasks, The Brain |
| Subs to confirm | the job's Site | unconfirmed for the next 4 working days | - | - |
| COI | Vendors | lapsing within 30 days or lapsed, with a PO or a booking ahead | - | Obligations (company insurance only), Dashboard, The Brain |
| Bills | Bills & Payroll | mine to approve | Approvals' Bills filter | Overview, The Brain |
| Money flags and findings | Caught for You on Today | - | Controls for the controller | Chief of Staff's Findings (fold Chief of Staff into The Brain), Approvals |
| The Brain and Chief of Staff | The Brain | - | - | Chief of Staff (the same seven tabs) |
| Sales, Projects, Drawings, Design | one view each | - | - | the duplicate views (`hbdeals`, `scleads`, `leads` to `ovsales`; `port` to `ovjobs`; `sdraw` to `plans`; `studio` to `ovstudio`) |

Field roles: the foreman's Today is his queue and Site is his register for the job (materials, inspections, subs); Raise sends to the office and lists only what he raised; Crew lists people, not schedule lines. The crew's Clock is their task list: remove the separate Tasks page from the crew menu. The driver's Route is already one place.

### The phone bar and first screen, per role

The bars are right (decided 2026-10-19, four shortcuts with Chat). What changes is the first screen.

| Role | Bar (keep) | First screen, top to bottom, all above the fold |
|---|---|---|
| Owner | Today, Chat, Projects, Accounting | three pulse numbers; Do Now (5 rows) ranked so a job delay in the next 10 days outranks a sales follow-up due today; one line "Caught for You: 34, $X at stake" that opens the list |
| PM | Today, Chat, Projects, Field | Do Now with a "Coming Up" band: inspections to book, submittals due, subs to confirm, decisions due by need-by date, each with the days left before it delays the job |
| Coordinator | Today, Chat, Requests, Buy Board | order-bys in the next 10 days (late ones collapsed to one line, "5 late to order, $X"), crew requests needed in 2 days, COI lapses with a booking ahead |
| Foreman | Today, Site, Daily Log, Chat | Now (blockers, tomorrow not ready, subs to confirm, inspection today), then Today's Work as 60 px rows; Packing Slip moves to the camera button; For You folds into Now |
| Crew | Clock, Requests, Schedule, Chat | Clock In, then today's work rows (already there) |
| Driver | Route, Chat, Clock, Receipts | the store run first; the stock card only when something is reserved |
| Designer | Today, Chat, Drawings, Projects | From the Field, then decisions and drawings due by need-by date; no empty card |
| Billing | Billing, Today, Chat, Clients | unchanged (the queue is the page) |
| Controller | Banking, Today, Chat, Bills & Payroll | Banking's to-review list first; the six action buttons behind one; the bank-backing card below |
| Client | Overview, Schedule, Decisions, Account, Chat | Waiting on You first (already), without "retainage" in the words |

### What the task module on the phone should become
1. **One list.** "Tasks" is `tkAll()` with chips: Mine (default), Team, a job, Sales. Projects › Tasks and Sales Tasks are the same screen with a chip set. One "Next 7 Days" number everywhere.
2. **It opens on "Due Soon"**: overdue, today and the next 7 days in one list grouped by day, so it never opens empty while work is coming.
3. **Rows of 64 to 72 px:** a 44 px check circle, the title on two lines, one line with the due date and the job, the owner's initials. Notes, source and area go to the task. Later and hand-off are a swipe or a long press, not buttons on every row.
4. **The header is one line:** a search icon and a filter chip. New Task is a round + button above the bar, bottom right. The view tabs go into the filter sheet.
5. **A tap opens the task, not the form:** title, due with quick picks (Today, Tomorrow, Next Week), owner as a person picker that sends the hand-off (offer, accept, decline), where it came from, checklist, comments and photos, and Mark Done at the bottom. Edit opens the form. The keyboard stays down.
6. **On Today, a task card opens the same sheet** when its title is tapped.

## 7. The Checks

`python3 ia_map.py --check` reads `review/ia/data.json` and fails when (each encodes section 6, so it turns green as the proposal is built):

| Check | Fails when | Fails today |
|---|---|---|
| ONE PLACE | a noun's records are listed on a screen of a role other than its one list (`ONE_PLACE`), the role's first page or a context page (`CONTEXT_OK`: a bank line naming its vendor, the calendar) | 142 (role x screen size x noun) |
| ONE NUMBER | one label shows different counts on two screens of one role (filter words such as All or Done excluded) | 8 |
| PRECURSOR | a precursor is not on the first screen of the person who must act, or is below the fold on the phone | 54 |
| PRECURSOR LEAD | it first reaches that first screen fewer than 3 working days before it is due (or never) | 40 |
| TASKS | a task screen has under 3 rows above the fold, a target under 44 px above the fold, opens empty while work is due this week, or a tap does not open a sheet with done, due and hand-off | 26 |
| CLEAN | a role's first page on the phone has an empty card above the fold or is taller than 3 screens | 5 |
| WORDS | a role's first page uses an internal word, or a finance word for the field or the client | 1 |

They are not in `run_all.sh`: they would turn the net red until the proposal is built. Recommended: add `ia_map.py` to the net when Today's "Coming Up" band and the one task list land, with the counts as a ratchet (a number may go down, never up).

## 8. What This Measurement Did Not Check, and How Sure It Is

- **Records are found by their words.** A record counts on a section when its title (up to 34 characters, less a trailing job name) is in the section's text; a vendor's name counts as a COI or a sub confirmation only next to "insurance" or "confirm". A screen that shows a record in other words (a bank line, a chart, a count) is not counted, so the counts are a floor. A name that is only a job, client, vendor or person is never a needle. Spot checks against screenshots matched; a few near-misses remain (a vendor named in a bank line near the word "confirm").
- **What opens, not what is one tap away.** A screen is read as it first opens, with its default filters (the queue pages' filters are read too). "N more" rows, folded cards and other jobs (a page that opens on the current job) are not read.
- **The phone is read at 390 x 844 with the bottom bar's top as the fold** (y 786).
- **The precursor scan moves only the app's day.** It does not run the day's hooks, so no chase or escalation is created as days pass; a real morning might add a chase task that the scan did not see. Going back before 9/3 shows records that existed later; the scan reads what the rules would show, not history.
- **Late predecessors are not exercised:** the demo has no task in the window whose predecessor is late or behind. Seed one before trusting that row.
- **The client and the Mercer & Bond workspace** were walked as they are (the client) or left out (M&B), per MENU_DRAFT.
- **Not judged:** whether each page's content is right, speed, Spanish, and the desktop layout's visual quality. Section 6 is a proposal for Alan; the expert workshop has not seen it.

## Design Gate (BACKLOG §1.16)

This lane adds no store, list, queue or menu item: a test script, its reader and its output. The proposal extends the one queue (`tdyModel`: a "Coming Up" part fed by existing predicates) and the one task accessor (`tkAll`), and removes pages; it asks for no new noun.
