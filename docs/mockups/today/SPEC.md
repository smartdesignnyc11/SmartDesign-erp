# Your Day (Today, Tasks, Messages): mock-up and spec

Mock-up only; nothing in `src/` changes until Alan says yes. Figures are the demo company's, read from the running build
(master a5b0a82, demo day Thu 9/3) as the owner unless a role is named; `[PLACEHOLDER]` marks a figure the build does not
settle. Alan on 10-27: Today on the phone "is pretty good. It looks good. It's easy to read, easy to take action." Kept as is:
the brief card at the top, one row per thing with one plain action, red lateness, the chips, the "more" fold. Changed only
where the ten questions (`../QUESTIONS.md`) show it is weak.

## 1. Today's pages and tabs (census build bd3180c27e33, owner, desktop)

| Page | Where | Tabs and counts today | Screens |
|---|---|---|---|
| Today (`home`) | Today | All 34 / Late 6 / Approvals 22; sections Now 9, Approvals 19, This Week 6; footer "33 caught for you" | 3 |
| Approvals (`mapprove`) | Today › Approvals | Everything 22 / Bills 1 / Changes 3 / Lessons 6 / Other 12, then "Also on Your List" 11 | 5 |
| Chief of Staff (`pa`) | More › Chief of Staff (also Company › The Brain) | Chat / Findings 38 (For You: Caught 37, Waiting 1; Checklist: 7 seats; Every Chain; Morning Brief) / Activity (6) / Brain Settings (6) | 26 |
| Tasks (`tkall`) | Tasks (and Today › Tasks) | List, Table, Board, Calendar × All Open 15 / My Week 12 / Waiting on Others 2 / Everything 55; phone: Due Soon 12 / Waiting 0 | 16 |
| Messages (`chat`) | Messages | Team / Mail 1 / Field; My Chats / All Chats; 8 job threads, all "No messages yet" | 11 |
| Inbox (`comms`) | Messages › Mail | Needs an Answer 1 / To Decide 7 / Everything 10 / Calls 1 / Done | (in Messages) |
| Meetings (`meetings`) | Company › Meetings | Meetings / What We Are Learning / Changes 3 / Settings; tiles 2, 0, 2, 3 | 4 |
| Calendar (`calendar`) | Company › Calendar | All / Task 10 / Decision 8 / Inspection 1 / Milestone 5 / Delivery 1 / Expiry 1 | 7 |

8 pages, 74 desktop screens. One label, many numbers: the rail's Today badge 6 is the Late count while Today opens on 34;
Approvals reads 22 on the chip and 19 on the section; lessons read 9 (The Brain), 6 (Approvals) and 8 (Today rows); caught
reads 33 (Today), 37 and 38 (Chief of Staff); Waiting reads 0 on the phone and 2 on the desktop. The owner's brief sits five
taps deep (More › Chief of Staff › Findings › Checklist › Founder); the only cash figure is a grey footer line.

## 2. Proposed: three sub-pages

**Today** (`Today.dc.html` phone, `DeskToday.dc.html` desktop; `DeskTasks.dc.html` and `DeskMessages.dc.html` added 11-03 for the must-fixes). Opens on what needs you today, in the Standard's order.
1. What: everything that needs you today, and the one brief that says where the firm stands.
2. Label: "Today" (unchanged; every seat says it).
3. Holds rows that live elsewhere (bills, payroll, mail, tasks, deals); each row opens its home. Approvals is a chip, not a page.
4. Every office role, first thing; the owner's question "what only I can act on, and is there cash?".
5. Not a record page; every row names its job, client or deal.
6. Your Brief (Safe to Spend with its parts, the job slipping, the client waiting), then Approvals, then Now; Coming Up and
   Where the Firm Stands one tap down on the same page.
7. One number: the rail badge, the header, the Today chip and the rows are all 16 (4 approvals + 12 now), computed from the
   rows. Now holds every message Messages counts as the owner's (5) and the Pipeline's signed-with-no-job deal (the
   Nakamuras); Approvals 4 equals its rows; Coming Up 6 is not counted in the badge, because nothing in it is due today.
8. One + (Task, Lead, Lead from a Mail, Message, Note or Call), all tied to you.
9. Rows one column, 44px buttons, every figure labelled; the cash parts fold under the figure; no strip scrolls sideways.
10. One page, three chips (Today, Approvals, Coming Up), replacing Today, Approvals and Chief of Staff.

**Tasks** (`Tasks.dc.html` phone, `DeskTasks.dc.html` desktop). Opens on Mine, grouped Late, Today, Tomorrow, Later This Week, Later.
1. What: the one list of to-dos, yours first. 2. "Tasks". 3. Every to-do lives here; Today, a job and a deal show it filtered.
4. Everyone with a login; "what did I promise, and what am I waiting on?". 5. Filters by person; a job's tasks open from the job.
6. Late first; done circle, title, where, who. 7. Mine 15 (every open task of yours: 12 this week and 3 renewals under Later)
and Waiting On 2 equal their rows; Mine is the same 15 the person page and Team show; the rail shows no badge (Today
already counts what is due), as in the approved menu. 8. One + makes a task for you; inside a job the job's + ties it.
9. 44px done circle, one line per fact. 10. One page. The desktop opens on Table (the view Alan uses: the 10-26 lane's nine
columns Key, Task, Project, Owner, Due, Priority, New or Carried, Status, Waiting On; header click sorts ascending, descending,
then back; empties last; natural keys; a Columns control), with List, Board and Calendar one tap away. The Board's columns
are by Status, Project or Person (the Monday and Thursday meeting walks it by person). The phone has List and Calendar; Table
is the list's Sort By there, as built 10-26. Team is a chip: the team's tasks grouped by person, late first, with no load
figures (load lives once, on Team); people with nothing open are named at the foot, so the 14 on Team are all accounted for.

**Messages** (`Messages.dc.html` phone, `DeskMessages.dc.html` desktop: the list and the open conversation side by side). Opens on Needs an Answer.
1. What: every conversation (mail, texts, calls, team and client chats, meeting notes) and which ones wait on you.
2. "Messages". 3. Each message lives once; a client's or job's messages show inside that client or job.
4. Everyone; "who is waiting for an answer from me?". 5. A thread names its client or job; open it from there too.
6. Needs an Answer oldest first; All (one list across mail, texts, calls, chats and meeting notes) and Meetings one tap.
7. Needs an Answer 5 equals its rows, the rail badge and the 5 message rows on Today. Meetings carries no count for the owner:
both notes are on 121 State Street, so the job's PM (Alan) reviews them and they count on his Today, not the owner's.
8. One + (a message to a person, a client or a vendor). 9. One row per thread, 44px reply, no sideways strip.
10. One page, three chips, replacing Messages, the Inbox and Meetings.

**Ask** is not a page: it is the button in every header ("Ask About My Day", "Ask About This Job"), with its conversations
inside it. Its activity log and what it may do live under Company and Settings (see `../company/SPEC.md`).

## 3. Old page or tab, and its new home (nothing lost)

| Old | New home |
|---|---|
| Today › All, Late | Today › Today chip (late shows on each row in red) |
| Today › Approvals tab; Approvals page › Everything, Bills, Other | Today › Approvals chip, exceptions only (decision 3, 10-26) |
| Approvals › Changes, Lessons; Today's 17 brain rows | Company and Settings › The Brain; one line on Where the Firm Stands |
| Approvals › hours, design invoice, "bill it" rows, vendor creation | Their owner's Today (PM, billing, coordinator); the owner sees them only as exceptions |
| Chief of Staff › Chat | The Ask button, every page |
| Chief of Staff › Findings › For You, Caught, Waiting for You, Morning Brief | Today: the brief and the rows (each finding is a row for the person who acts) |
| Chief of Staff › Checklist › Founder and each seat | Today › Where the Firm Stands (each role sees its own seat's checklist) |
| Chief of Staff › Every Chain | Accounting (the controller's); out of this menu |
| Chief of Staff › Activity (6 tabs) | Company and Settings › Team › the person › Their Assistant |
| Chief of Staff › Brain Settings (Lessons, Proposed, Watching) | Company and Settings › The Brain |
| Brain Settings › Workload; Hands; Plugins | Team (workload); the person's assistant rules; Connections |
| Today's footer (Safe to Spend, Overdue AR, Jobs at Risk) | Your Brief (cash with its parts) and Where the Firm Stands |
| Tasks › List, Table, Board, Calendar; My Week, All Open, Waiting on Others, Everything | Tasks: List/Board/Calendar view; Mine, Waiting On, Team chips; Everything is the Team chip with "all" |
| Messages › Team, Field, My Chats, All Chats, the 8 empty job threads | Messages › All (a thread appears once it has a message) |
| Messages › Mail; Inbox › Needs an Answer, Everything, Calls, Done | Messages › Needs an Answer, All (calls and texts are rows) |
| Inbox › To Decide 7 | Each proposal is a row on its person's Today, with its button |
| Company › Meetings (Meetings, Changes, What We Are Learning, Settings) | Messages › Meetings; changes to The Brain; settings to Connections |
| Company › Calendar (7 tabs) | Tasks › Calendar view: everything dated, one list; Google sync in Connections |

Old 8 pages and 74 desktop screens; new 3 pages, 3 chips each, about 9 screens (a view switch on Tasks).

## 4. What each role sees

| Role | Today | Tasks | Messages |
|---|---|---|---|
| Owner | Brief with cash; Approvals (exceptions only); Now; Where the Firm Stands (founder) | Mine, Waiting On, Team | All threads he may read |
| PM | Brief (billed ahead, decisions past due); crew blocked first (Tomas no-show), decisions, client mail; the PM seat checklist | Mine, Waiting On, Team for his jobs | His jobs, his clients |
| Coordinator | COI, late orders, sub confirmations first; purchasing checklist | Mine, Waiting On | Vendors, his jobs |
| Billing, Controller | Unmatched money, billing due, books; their seat's checklist; cash brief | Mine | Routed mail (statements, payments) |
| Designer | Her Today stays as built (due soon, to re-issue, field questions) | Mine | Her jobs |
| Foreman, crew, driver | Unchanged: the job's work, clock in, route | none (their work is the schedule) | Their job's team thread |
The badge on Today is always the rows Today opens on, for every role.

## 5. Decisions made, and why
- **Approvals is a chip on Today, exceptions only.** Alan decided 10-26 that only exceptions reach him (paid before approval,
  over the PO, no PO, bank-detail change, first payment to a new vendor, POs over $10,000, payroll split by job). In the demo
  that is 4 rows, $60,990, against 22 today. AMP-311 ($9,800, no PO), missing from Approvals › Bills today, is on it.
- **Payroll is first, and its button is Review Payroll, not Approve.** 88% of the $16,040 is not split by job, so Approve
  cannot work (owner finding 16). The build should send it back to Chen to split before it reaches the owner.
- **Brain rows leave Today.** Lessons and rule changes are owner approvals of a different kind (they change the system), so
  they gather in The Brain with one count, 17 (9 lessons, 2 changes, 6 job steps). The build reads 9, 8 and 6 today because
  each screen counts a different part, and one item is drafted twice.
- **Rank by when the consequence lands, then by the Standard's order.** The LLC filing (lapses 9/28) stays in Now because it
  is late, but below wages, money paid before approval and a client waiting; it no longer takes the blue button.
- **Cash is one figure with its parts**, from `safeToSpend()`, with each account's reconciled date. The $156,274 part
  is labelled "Over-Billed (WIP), cost to cost", never "billed ahead of the work" (that label is the field measure,
  $66,470; DECISIONS 10-25). The set-aside itself follows BACKLOG §1.35 item 1, so the figure will move. The Rivera $21,350 shows
  as "not counted". Every place that prints Safe to Spend reads the same function (triage class 1).
- **Messages opens on Needs an Answer.** Today's Messages opens on an empty job thread. The count rises from 1 to 5 because
  mail to the owner with a question and no reply (Sarah Klein 9/2, Samantha Field 8/31, Jeanette 8/31, the Torres call 9/2)
  counts, not only Aliya Chen's: a rule change Alan should see.
- **Meetings and Calendar leave Company.** Meetings are conversations; Calendar is a view of everything dated, so it is a Tasks view.

## 6. Unsure, or for Alan
- Ana Petrova's next step reads due 9/2 on the Pipeline and 9/4 on the task: one record should hold one date.
- Jeanette has no login, so client mail to her reaches the owner. Give her a login or route her mail to the PM.
- The bottom bar on the phone is not drawn; the approved menu (`../job-structure/Main.dc.html`) is the way in.

## 7. Self-review against the ten questions
| Page | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Today | pass | pass | pass | pass | n/a | pass | pass, see below | pass | pass | pass |
| Tasks | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Messages | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass |
- Revised in review: Where the Firm Stands first carried a placeholder for the lessons count; reading The Brain showed 9
  lessons, 3 changes (one the same as a lesson) and 6 job steps, so it reads 17. Coming Up is kept out of the badge so that
  the badge equals the rows Today opens on (question 7).
- Today question 1 needs two clauses (what needs you, and the brief). Kept: the brief is three lines that explain the rows,
  and Alan asked for the brief on Today (owner finding 19). Tasks' Team chip has no count, by design (it waits on nobody in
  particular). Where the Firm Stands' "Deals That Need You 3" was 4 in the first draft; it now uses the Pipeline's one rule.

## 8. Chief of staff review (11-03, overnight)
Verdict: **build after the must-fix list below**; the shape (3 pages, Approvals as a chip, Ask as a button) is right.

| Page | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | Grade |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Today | pass | pass | pass | pass | n/a | pass | **gap**: 3 of the 5 messages waiting on you are not on Today | pass | pass | pass | 8 |
| Tasks | pass | pass | **gap**: Team chip lists people by load, a second list beside Team | pass | pass | pass | **gap**: Mine 12 vs "15 open" on the person page and Team | pass | pass | **gap**: Board not drawn, Table dropped silently | 7 |
| Messages | pass | pass | pass | pass | fixed: the Torres call now names 121 State | fixed: oldest first | pass (new rule, below) | pass | pass | pass; desktop not drawn | 8.5 |

Fixed in the mock tonight: the $156,274 part reads Over-Billed (WIP), not "billed ahead of the work"; Compliance reads 6 (Window
Works on site 9/9 with lapsed insurance, Tino, and the 4 firm records now in Insurance and Licenses), and the phone brief carries
the Window Works line the desktop had; Needs an Answer is oldest first; R. Torres is the Kleins' managing agent calling about
Friday's elevator booking, not a client.

Calls made (DECISIONS 11-03): the Needs an Answer rule stands (5 is the truth; the old 1 hid two clients past the 2-hour
acknowledgement). A bill with no PO counts as "over the PO"; a card charge made twice counts as "paid before approval".

**Must fix before build** (11-03 overnight pass: done in the mock-up or left for the build lane)
1. **Done in mock-up, 11-03.** Today shows every message Messages counts for the owner: R. Torres, Aliya Chen, Sarah Klein,
   Jeanette and Samantha Field are Now rows, ranked by the 10-21 order (client messages and client money, then law, sales
   last). With the Nakamuras (Sales must-fix 1) the badge, header, chip and tile read 16 (4 + 12), computed from the rows. The
   owner's rail on the Sales, Reports and Accounting mock-ups now reads Today 16, Messages 5. Build: Today is the union of the
   person's waits-on-you lists (BACKLOG §10 item 7) and the counts lint checks it.
2. **Done in mock-up, 11-03.** Mine is every open task of yours, 15 (3 renewals under Later), on the phone, the desktop, the
   person page and Team.
3. **Done in mock-up, 11-03.** `DeskTasks.dc.html`: Table (default), List, Board and Calendar; the Table has the nine 10-26
   columns, click-to-sort, a Columns control and no cell cut without an ellipsis.
4. **Done in mock-up, 11-03.** Tasks › Team groups the team's tasks by person (phone and desktop), no load figures; a link
   to Team, where load lives once.
5. **Done in mock-up, 11-03.** `DeskMessages.dc.html`: the one list (Needs an Answer oldest first, All, Meetings) beside the
   open conversation; the assistant's draft shows with "nothing is sent until you press Send"; one blue, on the reply to what
   waits on you.
6. **Left for the build lane.** One cause for 121 State slipping, read from the schedule's blocker, on the brief and the client
   page. The mock cannot settle which blocker holds rough plumbing (a late material, the overdue bathroom finishes, or both).
7. **Done in the spec, 11-03** (section 9 below); the lane confirms each entry against `tests/ia_map.py` before it starts.

Found while drawing (for the build lane):
- The build's Table prints Priority "—" on the SAL tasks although each record holds one (SAL-1 is high); the mock shows P1-P3
  from the records. A column that reads blank over a filled field is the class to check.
- "Renew: Window units, 121 State Street" (a warranty ending 8/3/2036) is an owner task today; renewals should become tasks
  inside their lead time, not ten years ahead. Shown under Later for now.
- The Board by Status: every task of the owner's is To Do; tasks with a Waiting On party are drawn in Waiting On. The build
  keys that column on status only, so the walk sees nobody waiting.
- The approved job-structure canvas (`../job-structure/`) prints the build's rail badges of the day (Today 6, Messages 1); it
  was not changed. Built, every rail reads the one function, so it will read 16 and 5 on the demo.

## 9. Registry (BACKLOG §1.16): what each page extends
The registry is `ONE_PLACE`, `QUEUE` and `CONTEXT_OK` in `tests/ia_map.py`, with counts named in `PRED`. No new noun, store,
list or queue.

| Page | Noun (registry key) | Its one list | Queue and counts | New? |
|---|---|---|---|---|
| Today | none of its own: a view over approval, task, inbox, material, finding | `home`, each role's `QUEUE` entry | `PRED.waitingOnMe` ranked by `standardRank`; Approvals is `PRED.waitingOnMe` filtered to the 10-26 exceptions; Coming Up is the CONSOLIDATION §2.6 feed | No. `mapprove` and `pa` fold into `home` (chips); `pa` Chat becomes the Ask button |
| Tasks | `task` | `tkall` (`tkItems()` / `tkAll()` over `DB.tasks`, `p.tasks`, `hbtasks`, `DB.obligations`) | Mine and Waiting On are filters of `tkAll()`; no badge | No. `calendar` folds in as the Calendar view (it is in `CONTEXT_OK` today; it leaves the menu) |
| Messages | `inbox` (mail, calls, texts) and the message thread (`p.chat`, `DB.threads`, §1.21) | `chat`, with `comms` folded in as its Needs an Answer chip | Needs an Answer is `cmListFor("open")` widened to any question to you with no reply | No. `comms` and `meetings` fold in; a meeting's notes are a row of the one list (`DB.meetings` unchanged) |

Reasons recorded: none needed, nothing new. The structure lint should add `inbox: {'chat'}` once `comms` folds in, and drop
`mapprove` from `approval` once Approvals is Today's chip.
