# Company and Settings: mock-up and spec

Mock-up only; nothing in `src/` changes until Alan says yes. Figures are the demo company's, read from the running build
(master a5b0a82, demo day Thu 9/3) as the owner; `[PLACEHOLDER]` marks what the records do not hold. Rarely visited by
design: Today says when something here needs you (the LLC filing, lessons to approve), so the owner "almost never" has to come.

## 1. Today's pages and tabs (census build bd3180c27e33, owner, desktop)

| Page | Where | Tabs and figures today | Screens |
|---|---|---|---|
| Company (`ovoffice`) | Company | Renewals Due 1, Meetings to Review 2, Not Matched 0, Changes to Approve 3; 6 rows | 1 |
| Calendar (`calendar`) | Company › Calendar | All / Task 10 / Decision 8 / Inspection 1 / Milestone 5 / Delivery 1 / Expiry 1 | 7 |
| Team (`team`) | Company › Team | 13 people; no PM; 5 with no phone or email | 1 |
| Meetings (`meetings`) | Company › Meetings | Meetings / What We Are Learning / Changes 3 / Settings | 4 |
| The Brain (`pa`, also Chief of Staff) | Company › The Brain | Chat / Findings 38 / Activity / Brain Settings (Lessons, Proposed 6, Workload, Hands, Watching, Plugins); 14 rule rows before the lessons; Lessons to Approve 9 | 12 |
| Obligations (`obligations`) | Company › Obligations | Lapsed 1, Renew Now 1, Active 10, Premiums $10,550; dates print "1/10/2027/27" | 1 |
| Settings (`setup`) | Settings | A hub of links, and "Turn the Demo On" | 1 |
| Connections (`conn`) | Settings › Connections | Bank feeds; Google (not connected); firm setup; "What My Assistant May Do" (the 14 rules again) | 3 |
| The SmartDesign Standard (`standard`) | Settings › The Standard | Standard Watch, then 59 sections, 11 desktop screens (25 on the phone) | 1 |
| Problem Reports (`rpbox`) | Settings › Problem Reports | Open / New / Accepted / Fixed / Everything; all 0 | 4 |
| Your Own Data (`rdata`) | Settings › Your Own Data | Projects 4 / Clients 6 / Vendors and Subs 12 / People 9 | 4 |
| Sales Settings (`hbsettings`) | Settings › Sales Settings | Pipelines / Properties / Record Customization / Products / Users & Teams | 1 |
| Company Settings (`proj`) | Settings › a link | 16 sections, 8.7 desktop screens: clock ("As Of", editable), users, entities, approval rules ("owner approval for payments above $0"), item library (99), developer backlog, schedule-logic help | 1 |

13 pages, 41 desktop screens, two menu groups (Company, Settings). The assistant's rules sit in four places (The Brain's
Approval Rules, Connections, Company Settings, Plugins); "changes" in three (Company, Meetings, The Brain); the brief the owner
wants is five taps deep under Chief of Staff, which is this same page.

## 2. Proposed: a hub and six sub-pages, one home each

The hub (`Company.dc.html`) is the menu entry at the foot of the approved menu: six rows, a count only where something waits.

| Thing | Its one home | Why there |
|---|---|---|
| The assistant's settings | Team › the person › Your Assistant (`Person.dc.html`) | Inside a person, everything is that person: their work, their limits, what their assistant may do, what it did |
| The Standard | The SmartDesign Standard (`Standard.dc.html`) | Alan's document, versioned; its defaults feed every assistant |
| Lessons | The Brain (`Brain.dc.html`) | What the firm learned and proposes to change; only the owner approves |
| Connections | Connections (`Connections.dc.html`) | Your account first, then the firm's banks, mail and books, then the one-time setup |
| Team | Team (`Team.dc.html`) | Every person, most loaded first |
| Company settings | Company Settings (`Settings.dc.html`) | The firm, money and buying, sales stages, data |
| The firm's insurance, licenses, filings | Insurance and Licenses (`Insurance.dc.html`) | Records that renew, not settings |

**Team.** 1 Every person and their load. 2 "Team". 3 A person lives once; tasks and approvals link to them. 4 Owner and
managers: "who is overloaded, who is missing?". 5 Inside a person, all theirs. 6 Needs You (the PM is not on the page; five
with no phone or email), then most loaded first. 7 Counts are per person and open their tasks. 8 One + (New Person).
9 One row per person, 60px. 10 One page; the person page holds limits, assistant and activity.

**A person (you).** Open tasks 15 (3 late), room to hand off; What Reaches You for Approval (the exceptions of 10-26); Your
Assistant (14 rules, Act Alone / Ask First / Hand It to Me; money, client commitments, messages to clients and the books cannot be set
to Act Alone); What
It Did on Its Own; Your Accounts. Every count is this person's.

**The Brain.** 1 What the firm learned and wants to change. 2 "The Brain" (Alan's word). 3 Each lesson once; Today shows
one line with the count. 4 The owner, a few times a week: "what should change?". 5 n/a. 6 To Approve: Lessons for the Firm 9,
Changes to the ERP 2, Job Checklist Steps 6; What It Read one tap. 7 To Approve 17 equals its rows, the hub badge and
Today's line. 8 None: lessons come from what happened. 9 Approve and Decline, 44px each. 10 One page, two chips.

**Insurance and Licenses.** 1 The firm's own policies, licenses and filings, and what lapses. 2 The words in the seat
(the app says "Obligations"). 3 Vendor certificates live on the vendor; permits and warranties on the job; this page links.
4 Owner and controller, at renewal. 6 Needs You 4 (the LLC filing, the blank license number, workers' comp and disability, the trade licenses: a
required record not on file is law, the second decision principle), On File 2, Kept With Their Record.
7 4 equals its rows and the hub. 8 One + (policy, license or filing). 9 One column. 10 One page.

**Connections.** 1 What the ERP reads and how fresh it is. 3 Each account once. 4 Everyone once; owner and controller when
a statement is stale. 6 Your Google account first (blue), then banks with their reconciled-through dates, mail and books,
setup. 7 No badge. 8 None. 9 Rows 60px. 10 One page.

**The SmartDesign Standard.** 1 Alan's operating document and how the firm measures against it. 3 The live versioned copy;
code reads it. 4 Everyone to read; the owner to edit. 6 Open Today (14 measured lines with rows, the 2-hour client acknowledgement among them: Aliya Chen and Sarah
Klein) then The Document. 7 14 equals its rows and the hub. 8 Edit, owner only, recorded. 10 One page, two chips; the Sales playbook folds in as a role.

**Company Settings.** 1 How the firm is set up. 4 Owner and controller, rarely. 6 Four groups of rows, each opening in
place. 7 Text, no badge. 9 Rows 56px. 10 One page; Sales Settings, Your Own Data and Problem Reports fold in as rows.

## 3. Old page or tab, and its new home (nothing lost)

| Old | New home |
|---|---|
| Company (overview: renewals, meetings, changes) | Gone: each item is a row on its owner's Today; the hub carries the counts |
| Calendar | Your Day › Tasks › Calendar view |
| Meetings › Meetings, Settings | Your Day › Messages › Meetings; reading settings in Connections |
| Meetings › Changes, What We Are Learning | The Brain › To Approve; The Brain › What It Read |
| The Brain › Chat, Findings, Activity | Ask button; Today; the person's What It Did on Its Own |
| The Brain › Approval Rules; Connections › What My Assistant May Do; Company Settings › What the Assistant May Do; Plugins | The person › Your Assistant (one place) |
| The Brain › Lessons, Proposed, Watching | The Brain › To Approve, What It Read |
| The Brain › Workload, Hands | Team (load per person); the person's rules |
| Obligations (firm rows) | Insurance and Licenses |
| Obligations (vendor certificates, permits, warranties) | The vendor (Purchasing); the job's Documents |
| Settings hub; Live Jobs Demo switch | The Company and Settings hub; the demo switch under Your Data, owner and typed confirm |
| Connections › bank feeds, Reconcile buttons | Connections shows each account's date; reconciling is Accounting › Banking |
| Problem Reports, Your Own Data, Sales Settings | Company Settings › Data and Sales rows |
| Company Settings › users and roles, approval rules | Team (roles, per-person limits) |
| Company Settings › backlog, schedule-logic help | `docs/BACKLOG.md` and the help; off the screen |

Old 13 pages and 41 desktop screens; new hub plus 6 pages (about 10 screens), the person page inside Team.

## 4. What each role sees
| Role | Hub rows |
|---|---|
| Owner | All six; edits everything; sees anyone's assistant rules |
| Controller | Team (read), Insurance and Licenses, Connections, the Standard, Company Settings (money rows) |
| PM, coordinator | Team (read, their own page), Connections, the Standard |
| Billing, designer | Their own page, Connections, the Standard |
| Foreman, crew, driver | Their own page and the Standard (Spanish once reviewed) |

## 5. Decisions made, and why
- **The assistant's rules live on each person** (four places today). Alan's finding 13 asked for one page; inside a person is
  that page, and the owner opens anyone's from Team. The hub's note says so, so nobody hunts for "Assistant Settings".
- **Approval limits move from one firm number to the person**: "payments above $0" becomes the exceptions decided 10-26.
- **The Brain counts 17, not 18:** "A step carried twice becomes a dated task" is drafted as a lesson and as a rule; shown once.
- **Insurance and Licenses replaces Obligations**, the firm's own only; the blank license number is a row there (the
  documents print it), so the fault shows in one place.
- **"As Of", Clear Everything and Turn the Demo On** go behind the owner and a typed confirm (owner finding 21).
- **Bank reconciling leaves Connections** for Accounting › Banking, per the owner's verdict and CX5.

## 6. Unsure, or for Alan
- The purchasing mailbox's state and the mail-check interval were not read (`[PLACEHOLDER]`); workers' comp and the trade
  licenses are not in the records at all.
- Alan, the PM, is missing from Team in the demo; is he the same person as the owner (alan@smartdesign.nyc)?

## 7. Self-review against the ten questions
| Page | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Hub | pass | pass | pass | pass | n/a | pass | pass | n/a | pass | pass |
| Team, a person | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| The Brain | pass | pass | pass | pass | n/a | pass | pass | n/a | pass | pass |
| Insurance and Licenses | pass | pass, see below | pass | pass | n/a | pass | pass | pass | pass | pass |
| Connections, Standard, Settings | pass | pass | pass | pass | n/a | pass | pass | n/a | pass | pass |
- Revised in review: The Brain first read 18, counting one item twice; the Standard's hub line read 14 lines against 13
  rows (two "Direct to the source" lines are one row); both now agree. Company Settings printed "License # missing" as well as
  Insurance and Licenses; it now shows once.
- The person page is long (14 rules). Kept: it is visited rarely, and each rule is one 52px row that opens in place.
- "Licenses": decided by the chief of staff 11-03: the app's house spelling is American ("License" 46 times in the
  build, "license" in the Standard), so the label is "Insurance and Licenses".

## 8. Chief of staff review (11-03, overnight)
Verdict: **build after the must-fix list below.**

| Page | Gaps against the ten questions | Grade |
|---|---|---|
| Hub | none | 9 |
| Team | 7: the headcount reads 13, 14 and "4 of 9"; the PM is missing; two pairs of people share a phone number | 7.5 |
| A person | fixed: Messages to Clients can no longer be set to Act Alone; only the owner changes a limit | 9 |
| The Brain | none (17 = 9 + 2 + 6, one item shown once) | 9 |
| Insurance and Licenses | fixed: workers' comp and the trade licenses not on file are Needs You (law ranks second), 4 | 9 |
| Connections | fixed: the blue button was Connect My Google Account, which cannot work before the firm's setup | 9 |
| The Standard | fixed: the 2-hour client acknowledgement read 0 while Messages shows two clients past it; 14 lines | 9 |
| Company Settings | "people 9" under Your Data is a third headcount; the clock read "the admin" (now the owner) | 8.5 |

Calls made (DECISIONS 11-03): the label is "Insurance and Licenses" (the build's own spelling); the PM gets his own Team entry
and login; client mail to someone with no login goes to the job's PM.

**Must fix before build** (11-03 overnight pass: done in the mock-up or left for the build lane)
1. **Done in mock-up, 11-03.** One headcount, 14, read from the demo (13 on the build's Team page plus Alan, the PM, who has a
   login and 10 tasks but no Team record): Team's header, the hub row, Your Data in Company Settings and the foot of Tasks ›
   Team ("14 people with Alan; 10 have open tasks", the other 4 named) all say 14. "4 of 9" is gone with the load column on
   Tasks. Build: every headcount reads the one people list (BACKLOG §10 item 8).
2. **Left for the build lane, recorded as a data defect below.** Every login has a Team record; phone and email unique.
3. **Left open.** The desktop Team and person page are not drawn yet (limits and rules are edited at a desk). Draw before the
   Company lane starts, or the lane draws them first and the chief of staff reviews.
4. **Done in the spec, 11-03** (section 9 below); the lane confirms each entry against `tests/ia_map.py` before it starts.

**Data defects in the demo (shown as the records hold them; not fixed in the mock):**

| Defect | Records | Why it matters | Class fix and check |
|---|---|---|---|
| Two people share a phone number | Controller and Alberto both (917) 555-0105; Billing and Angel both (917) 555-0104 | A text to the crew reaches the books, and a call from the controller's phone is matched to Alberto | BACKLOG §10 item 8: phone and email unique across the one people list; a data lint fails on a duplicate |
| A login with no person | `u_alan` (the PM): login, 10 open tasks, no Team record | Nobody can pick him as an owner or see his phone; the headcount reads 13 or 14 | §10 item 8: every login points at a person |
| A person with no contact | Design director, Jeanette, Maya, Lena: no phone or email; Satish no email | Client mail to Jeanette reaches the owner; nobody can text four of them | Team's Needs You row (drawn); the build adds Jeanette's login or routes her mail to the PM (DECISIONS 11-03) |

## 9. Registry (BACKLOG §1.16): what each page extends
The registry is `ONE_PLACE`, `QUEUE` and `CONTEXT_OK` in `tests/ia_map.py`, with counts named in `PRED`. No new store.

| Page | Noun (registry key) | Its one list | Queue and counts | New? |
|---|---|---|---|---|
| Hub | none: rows link to the pages below | the Company and Settings menu entry (`MENU`, `ROLE_VIEWS`) | each row's count is its page's Needs You | No. `ovoffice` folds into the hub; `setup` too |
| Team, a person | person (`DB.users` and `DB.employees` read as one list; add `person: {'team'}`) | `team`; the person page is a record page | load per person shows here only (Tasks › Team carries none) | No. Assistant rules (four places today: The Brain, `conn`, `proj`, Plugins) fold into the person, read from `DB.asst[uid]` |
| The Brain | lesson and system change (`DB.lessons`, `DB.changes`, `DB.brainQueue`; add `lesson: {'pa'}`) | `pa`, as The Brain | To Approve 17 equals its rows, the hub and Today's line; a proposal keyed by its events (BACKLOG §10 item 2) | No. Meetings' Changes and What We Are Learning fold in |
| Insurance and Licenses | obligation (`DB.obligations`), firm-only | `obligations`, renamed | Needs You 4; vendor certificates stay `coi: {'vendors', ...}` | No: a rename and a filter |
| Connections | integration (`DB.integrations`, `DB.conn`, `DB.bankFeeds`) | `conn` | no badge; reconciling stays in `bank` | No |
| The SmartDesign Standard | the Standard (`DB.company.standard`) | `standard` | Open Today 14 equals its rows | No. The Sales playbook folds in as a role section |
| Company Settings | company settings (`DB.company`) | `proj` | none | No. `hbsettings`, `rdata`, `rpbox` fold in as rows |

Reasons recorded: none needed. The lint should add `person`, `lesson` and `obligation` to `ONE_PLACE` so a second people list
or lessons list fails.
