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

**Today** (`Today.dc.html` phone, `DeskToday.dc.html` desktop). Opens on what needs you today, in the Standard's order.
1. What: everything that needs you today, and the one brief that says where the firm stands.
2. Label: "Today" (unchanged; every seat says it).
3. Holds rows that live elsewhere (bills, payroll, mail, tasks, deals); each row opens its home. Approvals is a chip, not a page.
4. Every office role, first thing; the owner's question "what only I can act on, and is there cash?".
5. Not a record page; every row names its job, client or deal.
6. Your Brief (Safe to Spend with its parts, the job slipping, the client waiting), then Approvals, then Now; Coming Up and
   Where the Firm Stands one tap down on the same page.
7. One number: the rail badge, the header, the Today chip and the rows are all 12 (4 approvals + 8 now). Approvals 4 equals
   its rows; Coming Up 6 is not counted in the badge, because nothing in it is due today.
8. One + (Task, Lead, Lead from a Mail, Message, Note or Call), all tied to you.
9. Rows one column, 44px buttons, every figure labelled; the cash parts fold under the figure; no strip scrolls sideways.
10. One page, three chips (Today, Approvals, Coming Up), replacing Today, Approvals and Chief of Staff.

**Tasks** (`Tasks.dc.html`). Opens on Mine, grouped Late, Today, Tomorrow, Later This Week.
1. What: the one list of to-dos, yours first. 2. "Tasks". 3. Every to-do lives here; Today, a job and a deal show it filtered.
4. Everyone with a login; "what did I promise, and what am I waiting on?". 5. Filters by person; a job's tasks open from the job.
6. Late first; done circle, title, where, who. 7. Mine 12 and Waiting On 2 equal their rows; the rail shows no badge (Today
already counts what is due), as in the approved menu. 8. One + makes a task for you; inside a job the job's + ties it.
9. 44px done circle, one line per fact. 10. One page; List, Board, Calendar is a view switch; Team is a chip for managers.

**Messages** (`Messages.dc.html`). Opens on Needs an Answer.
1. What: every conversation (mail, texts, calls, team and client chats, meeting notes) and which ones wait on you.
2. "Messages". 3. Each message lives once; a client's or job's messages show inside that client or job.
4. Everyone; "who is waiting for an answer from me?". 5. A thread names its client or job; open it from there too.
6. Needs an Answer oldest first; All and Meetings one tap. 7. Needs an Answer 5 equals its rows and the rail badge.
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
  they gather in The Brain with one count; the count is `[PLACEHOLDER]` because the build reads 9, 8 and 6 today.
- **Rank by when the consequence lands, then by the Standard's order.** The LLC filing (lapses 9/28) stays in Now because it
  is late, but below wages, money paid before approval and a client waiting; it no longer takes the blue button.
- **Cash is one figure with its parts**, from `safeToSpend()`, with each account's reconciled date. The Rivera $21,350 shows
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
- Revised in review: the first draft counted Coming Up in the badge (18), which broke question 7 against the rows Today opens
  on; the badge is now 12. The first draft kept a "Team" chip on Messages; it was the same threads as All, so it went.
- Today question 1 needs two clauses (what needs you, and the brief). Kept: the brief is three lines that explain the rows,
  and Alan asked for the brief on Today (owner finding 19). Where the Firm Stands carries a `[PLACEHOLDER]` until The Brain's
  count is one number. Tasks' Team chip has no count, by design (it waits on nobody in particular).
