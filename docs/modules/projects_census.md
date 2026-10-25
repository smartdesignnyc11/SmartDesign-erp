# The Projects Module, Page by Page: the Census

**Asked by Alan, 2026-10-25:** "When you did the pilot did the role experts check each module and its sub pages and the layout of the page, for example the projects page, where all the data lives, how many sub pages, what information is on those sub pages?" They had not (in Pilot 2 the PM spent 9 seconds on Projects). "Start with Projects; that should be the main module used for the PM."

**What this is.** Step 1 of the module census (docs/PLAN.md): a machine inventory, not a judgment. No app code changed. `tests/projects_census.py` (its reader `tests/census_js.js` sits on the information map's `tests/ia_js.js`) signs in as each role at 1440 and at 390 and opens the Projects list the way the person does. Then, for two jobs, it opens the job page and every sub-page the job page reaches (the sub-tab strip, the job page's own links, and the job pages of the field roles' and the client's own menus), presses every tab of every tab group (and the tabs those reveal), and reads every screen. The two jobs are **121 State Street** (active construction) and **45 Cranberry St — design** (design stage, the design job with the most on it).

1166 screens in all. Built 2026-10-25 22:14 on the demo day (Thu 2026-09-03); the walk took 15.8 minutes. Raw read: `review/census/projects/data.json`. Every screen per role in tables: `review/census/projects/tables.md`. Screenshots of every PM page on both jobs and both devices: `review/census/projects/shots/` (`desktop_` and `phone_`, then the job and the page; the page as it opens, up to 3 desktop or 5 phone screens tall). The run also shoots every tab; those stay on the machine that ran it and are not committed.

Run it: `python3 build.py && cd tests && ./slot.sh python3 projects_census.py` (then `python3 projects_census.py --report` rewrites this page from data.json).

## Headline

- **The PM's job is 18 pages: the job page and 17 sub-pages, with 57 more screens behind their tabs** on the desktop (41 on the phone), about 26 desktop screens end to end. They hang off one sub-tab strip of 19 entries in four captioned groups (Plan, Field, Costs & Billing, Files & Mail).
- **Sub-pages each role reaches from the job, desktop:** PM 17, Owner 16, Coordinator 13, Foreman 7, Designer 5, Billing 1, Controller 0, Client 4, Crew 4, Driver 1.
- **Two office roles have no job page.** A tap on a job in the Projects list opens `sboard` for the designer; `gl` for the controller (`sboard` is the Design module's Project Board, `gl` the Ledger).
- **On a phone, a tap on a job in the Projects list opens the overview on All projects, not the job** (PM, Owner, Coordinator, Billing). The heading reads "All projects", the tiles and the Look-Ahead are every job's, and the strip under it holds the tapped job's pages. It stays that way until the person picks a job in the switcher (app.js: a phone with nothing stored defaults to All projects).
- **Change Orders, Estimates and Billing are one page (Billing) under three strip entries, and it is not the job's.** It shows the same tiles on both jobs (Ready to Bill $46K), while each job page says $12,651 (121 State Street) and $23,366 (45 Cranberry St — design). Its blue button on 121 State Street reads "Draft $17,080 — 45 Cranberry St".
- **91 of 121 State Street's records show on two or more of its pages** (31 schedule lines, 18 materials, 11 to-dos, 5 decisions). "Insulation" is on 8: Change Orders, Costs, Field, Job Page, Materials, Permits, Schedule, Tasks.
- **15 pairs of pages list largely the same records,** led by Job Page and Tasks (27 shared); Job Page and Schedule (22 shared); Schedule and Tasks (22 shared); Materials and Schedule (21 shared). The job page repeats most of Tasks and Schedule; Materials and Schedule repeat each other.
- **One label, different numbers:** "ready bill" $12,651 on Job Page against $46K on Billing (section 3).
- **On the phone** the PM's strip shows 3 of its 19 entries without a swipe; 5 of the 18 pages are taller than three screens (Job Page, Schedule, Costs, Documents, Drawings); 13 pages have no section heading above the fold. No page scrolls sideways.
- **Menu and job page:** Messages › Messages is in the PM's menu but not reached from the job page; Purchasing › Selections is in the PM's menu but not reached from the job page; `recv` sits in 2 menu places (Projects › Deliveries, Purchasing › Deliveries); `billing` sits in 3 menu places (Projects › Change Orders, Projects › Estimates, Projects › Billing).
- **Nothing crashed and no page raised an error**; every page opened.
- **1 screen(s) saved while the census only read and pressed filters** (PM (Alan) desktop, Materials). Not traced; most likely the task list remembering its view.

## 1. The Tree, Role by Role

**Sub-pages** are the pages reached from the job page (the job page itself not counted). **Tabs** are the screens behind each page's tab groups, and behind the tabs those reveal. **Sections** are the headed parts of each page as it opens. Each cell reads desktop / phone.

| Role | Reaches the Projects list by | Job page | 121 State Street: sub-pages / tabs / sections | 45 Cranberry St — design: sub-pages / tabs / sections |
|---|---|---|---|---|
| PM (Alan) | rail: Projects 2 / rail: Projects 2 | `dash` (the phone opens it on All projects) | 17 / 57 / 21 and 17 / 41 / 20 | 17 / 49 / 22 and 17 / 34 / 21 |
| Owner | rail: Projects 2 / rail: Projects 2 | `dash` (the phone opens it on All projects) | 16 / 57 / 21 and 16 / 39 / 20 | 16 / 49 / 22 and 16 / 34 / 21 |
| Coordinator (Chen) | rail: Projects 2 / rail:  | `dash` (the phone opens it on All projects) | 13 / 47 / 17 and 13 / 30 / 16 | 13 / 39 / 18 and 13 / 25 / 17 |
| Foreman (Angel) | cannot open it / cannot open it | `fsite` | 7 / 23 / 15 and 7 / 19 / 29 | 7 / 18 / 17 and 7 / 14 / 24 |
| Designer (Sarah) | rail: Projects 2 / rail: Projects 2 | none; the row opens `sboard` | 5 / 41 / 11 and 5 / 24 / 11 | 6 / 33 / 10 and 6 / 19 / 10 |
| Billing | rail: Projects 2 / rail:  | `dash` (the phone opens it on All projects) | 1 / 10 / 6 and 1 / 10 / 5 | 1 / 10 / 6 and 1 / 10 / 5 |
| Controller | no button: set view / no button: set view | none; the row opens `gl` | 0 / 6 / 3 and 0 / 6 / 3 | 0 / 6 / 3 and 0 / 6 / 3 |
| Client (Klein) | cannot open it / cannot open it | `client` | 4 / 1 / 20 and 4 / 1 / 20 | not theirs and not theirs |
| Crew (Alberto) | cannot open it / cannot open it | `sched` | 4 / 11 / 4 and 4 / 7 / 18 | 4 / 11 / 6 and 4 / 7 / 13 |
| Driver (Alex) | cannot open it / cannot open it | `files` | 1 / 7 / 1 and 1 / 7 / 1 | 1 / 7 / 1 and 1 / 7 / 1 |

### Which sub-pages each role reaches from the job page (desktop, 121 State Street)

Each cell is the number of screens the page has (the page and its tabs); "-" means the role does not reach it from the job page.

| Page | PM | Owner | Coordinator | Foreman | Designer | Billing | Controller | Client | Crew | Driver |
|---|---|---|---|---|---|---|---|---|---|---|
| Job page (or the page a tap on the job opens) | 1 | 1 | 1 | 1 | 4 | 1 | 7 | 1 | 5 | 8 |
| Project Settings | 1 | 1 | 1 | - | - | - | - | - | - | - |
| Schedule | 5 | 5 | 5 | 5 | 5 | - | - | 1 | - | - |
| Tasks | 19 | 19 | 18 | - | 18 | - | - | - | - | - |
| Decisions | 2 | 2 | 2 | - | 2 | - | - | 1 | - | - |
| Submittals | 3 | 3 | 3 | - | - | - | - | - | - | - |
| Permits | 1 | 1 | 1 | - | - | - | - | - | - | - |
| Field | 3 | 3 | 3 | - | - | - | - | - | - | - |
| Photos | 7 | 7 | 7 | 7 | 7 | - | - | - | 8 | - |
| Deliveries | 1 | 1 | 1 | - | - | - | - | - | 1 | - |
| Materials | 6 | 6 | 6 | - | - | - | - | - | - | - |
| Costs | 3 | 3 | - | - | - | - | - | - | - | - |
| Change Orders | 8 | 8 | - | - | - | - | - | - | - | - |
| Estimates | 1 | 1 | - | - | - | - | - | - | - | - |
| Billing | 1 | - | - | - | - | - | - | - | - | - |
| Documents | 11 | 11 | 11 | 8 | 11 | 11 | - | - | - | - |
| Drawings | 1 | 1 | 1 | 1 | - | - | - | - | 1 | - |
| Mail | 1 | 1 | 1 | - | - | - | - | - | - | - |
| Daily Log | - | - | - | 7 | - | - | - | - | - | - |
| Requests | - | - | - | 1 | - | - | - | - | 1 | 1 |
| Crew | - | - | - | 1 | - | - | - | - | - | - |
| Account | - | - | - | - | - | - | - | 1 | - | - |
| Chat | - | - | - | - | - | - | - | 2 | - | - |

### The PM's tree at a glance: 121 State Street

Tall is in screens, desktop / phone. Sections are the headed parts as the page opens; tabs are the screens behind its tab groups. "What it lists" counts the records found on the page as it opens.

| Page | Heading | Tall | Sections (phone above the fold) | Tabs | Tiles and figures | What it lists | Blue button |
|---|---|---|---|---|---|---|---|
| Job page | Overview | 3.7 / 4.6 | 6 (0) | 0 / 0 | Schedule At risk; Costs +$131,058 billed ahead; Needs You 12 now; Materials 5 at risk | 19 schedule lines, 11 materials, 10 to-dos, 5 decisions | none |
| Project Settings | Project Settings | 1.5 / 2.2 | 1 (1) | 0 / 0 | - | - | none |
| Schedule | Schedule | 1.9 / 3.9 | 0 (0) | 4 / 4 | - | 33 schedule lines, 4 materials, 1 decisions | New Task |
| Tasks | Tasks | 1.1 / 1.3 | 0 (0) | 18 / 2 | - | 10 to-dos, 6 schedule lines, 1 decisions, 1 site questions | New Task |
| Decisions | Decisions | 0.8 / 1.1 | 0 (0) | 1 / 1 | Blocking Work 3; Past Due 3; With Client 5; Ours to Make 3 | 8 decisions, 6 materials, 3 schedule lines | New Decision |
| Submittals | Submittals | 0.8 / 1.3 | 0 (0) | 2 / 2 | Late Submittals 2; With Reviewers 2; Revise and Resubmit 1; Ready to Order 0 | 6 submittals, 1 materials | New Submittal |
| Permits | Permits | 1.1 / 2.0 | 2 (0) | 0 / 0 | Failed 0; Book Now 1; This Week 1; Permits Expiring 1 | 10 inspections, 8 schedule lines, 2 materials | New Inspection |
| Field | Field | 1.1 / 1.4 | 2 (1) | 2 / 2 | - | 5 schedule lines, 4 site questions, 1 materials, 1 to-dos | New Item |
| Photos | Photos | 1.5 / 2.2 | 0 (0) | 6 / 6 | - | 2 schedule lines, 1 files | Add Photos |
| Deliveries | Deliveries | 0.5 / 0.4 | 0 (0) | 0 / 0 | - | 2 purchase orders, 2 files, 1 materials | Received |
| Materials | Materials | 1.3 / 2.9 | 1 (1) | 5 / 5 | Late to Order 3; Order This Week 0; At Risk 5; Not on Site 22 | 25 materials, 17 schedule lines | New Material |
| Costs | Costs | 2.8 / 4.1 | 4 (1) | 2 / 2 | Billed Ahead +$131K; Margin at Completion 21%; Committed $39K; Bills to Approve $34K | 4 materials, 1 schedule lines | none |
| Change Orders | Change Orders | 0.4 / 0.7 | 0 (0) | 7 / 7 | - | 2 change orders | New Change Order |
| Estimates | Estimates | 0.5 / 0.7 | 0 (0) | 0 / 0 | - | 2 estimates | New Estimate |
| Billing | Billing | 0.7 / 1.1 | 0 (0) | 0 / 0 | Ready to Bill $46K; Drafts 0; Sent and Unpaid $92K; Overdue $0 | 2 invoices | Draft $17,080 — 45 Cranberry S |
| Documents | Documents | 2.1 / 5.6 | 0 (0) | 10 / 10 | Added This Week 11; Unfiled 4; Drawings 24; Cards & Permits 0 | 40 files, 24 drawing sheets, 5 submittals, 2 purchase orders | Upload Files |
| Drawings | Drawings — 121 State Street | 3.1 / 5.8 | 3 (1) | 0 / 0 | Found Before Work 0; Found in the Field 1; Rework Avoided $0; Our Cost $0 | 1 schedule lines, 1 subs to confirm, 1 files | New Revision |
| Mail | Mail | 1.0 / 2.1 | 2 (0) | 0 / 0 | - | - | Review All New |

### The PM's tree at a glance: 45 Cranberry St — design

Tall is in screens, desktop / phone. Sections are the headed parts as the page opens; tabs are the screens behind its tab groups. "What it lists" counts the records found on the page as it opens.

| Page | Heading | Tall | Sections (phone above the fold) | Tabs | Tiles and figures | What it lists | Blue button |
|---|---|---|---|---|---|---|---|
| Job page | Overview | 1.8 / 2.5 | 6 (0) | 0 / 0 | Schedule On target; Costs +$2,705 billed ahead; Needs You Nothing; Materials All on site | 4 to-dos, 3 schedule lines | none |
| Project Settings | Project Settings | 1.5 / 2.2 | 1 (1) | 0 / 0 | - | - | none |
| Schedule | Schedule | 0.8 / 1.2 | 0 (0) | 4 / 4 | - | 5 schedule lines | New Task |
| Tasks | Tasks | 0.4 / 1.0 | 0 (0) | 15 / 0 | - | 4 to-dos, 1 schedule lines | New Task |
| Decisions | Decisions | 0.4 / 0.6 | 0 (0) | 1 / 1 | - | - | New Decision |
| Submittals | Submittals | 0.6 / 0.9 | 0 (0) | 2 / 2 | Late Submittals 0; With Reviewers 2; Revise and Resubmit 0; Ready to Order 0 | 3 submittals | New Submittal |
| Permits | Permits | 0.6 / 1.1 | 2 (2) | 0 / 0 | - | 1 schedule lines | New Inspection |
| Field | Field | 0.5 / 0.8 | 2 (2) | 2 / 2 | - | - | New Item |
| Photos | Photos | 0.9 / 1.5 | 0 (0) | 1 / 1 | - | - | Add Photos |
| Deliveries | Deliveries | 0.2 / 0.3 | 0 (0) | 0 / 0 | - | - | none |
| Materials | Materials | 0.4 / 0.7 | 0 (0) | 5 / 5 | - | - | New Material |
| Costs | Costs | 1.4 / 1.9 | 4 (1) | 2 / 2 | Billed Ahead +$3K; Margin at Completion 62%; Committed $0; Bills to Approve $0 | 4 schedule lines | none |
| Change Orders | Change Orders | 0.4 / 0.6 | 0 (0) | 7 / 7 | - | - | New Change Order |
| Estimates | Estimates | 0.4 / 0.6 | 0 (0) | 0 / 0 | - | 1 estimates | New Estimate |
| Billing | Billing | 0.7 / 1.1 | 0 (0) | 0 / 0 | Ready to Bill $46K; Drafts 0; Sent and Unpaid $92K; Overdue $0 | 2 invoices | Draft $17,080 — 45 Cranberry S |
| Documents | Documents | 0.7 / 1.0 | 0 (0) | 10 / 10 | Added This Week 1; Unfiled 0; Drawings 0; Cards & Permits 0 | 3 files, 2 submittals | Upload Files |
| Drawings | Drawings — 45 Cranberry St | 1.5 / 3.5 | 5 (1) | 0 / 0 | Found Before Work 2; Found in the Field 0; Rework Avoided $4,200; Our Cost $0 | 6 drawing sheets, 1 schedule lines | New Revision |
| Mail | Mail | 0.6 / 1.1 | 2 (2) | 0 / 0 | - | - | Review All New |

## 2. Where the Data Lives, and Where It Shows Twice

For the PM on the desktop: each kind of record on the job, how many of its records the job's pages list, and the pages that list them (how many each). A page's tabs count as the page. Records are found by their own words, so these are floors.

### 121 State Street

| Records | Found | Pages that list them |
|---|---|---|
| materials | 27 | 11: Materials 25, Job Page 11, Decisions 6, Schedule 4, Costs 4, Change Orders 4, Tasks 2, Permits 2, Field 2, Submittals 1, Deliveries 1 |
| schedule lines | 35 | 11: Schedule 33, Job Page 19, Tasks 19, Materials 17, Permits 8, Field 8, Change Orders 6, Decisions 3, Photos 2, Costs 1, Drawings 1 |
| files | 40 | 5: Documents 40, Job Page 3, Deliveries 2, Photos 1, Drawings 1 |
| decisions | 8 | 4: Decisions 8, Job Page 5, Schedule 1, Tasks 1 |
| to-dos | 11 | 3: Tasks 11, Job Page 10, Field 1 |
| purchase orders | 2 | 3: Deliveries 2, Documents 2, Job Page 1 |
| site questions | 5 | 3: Job Page 4, Field 4, Tasks 2 |
| inspections | 10 | 2: Permits 10, Job Page 2 |
| bills | 1 | 2: Job Page 1, Documents 1 |
| submittals | 10 | 2: Submittals 10, Documents 5 |
| invoices | 2 | 2: Change Orders 2, Billing 2 |
| estimates | 2 | 2: Change Orders 2, Estimates 2 |
| change orders | 2 | 2: Change Orders 2, Documents 2 |
| field requests | 2 | 1: Job Page 2 |
| drawing sheets | 24 | 1: Documents 24 |
| subs to confirm | 1 | 1: Drawings 1 |

### 45 Cranberry St — design

| Records | Found | Pages that list them |
|---|---|---|
| schedule lines | 10 | 7: Change Orders 10, Schedule 5, Tasks 5, Costs 4, Job Page 3, Permits 1, Drawings 1 |
| to-dos | 4 | 2: Job Page 4, Tasks 4 |
| submittals | 9 | 2: Submittals 9, Documents 2 |
| materials | 5 | 2: Change Orders 4, Submittals 1 |
| invoices | 2 | 2: Change Orders 2, Billing 2 |
| estimates | 1 | 2: Change Orders 1, Estimates 1 |
| change orders | 1 | 1: Change Orders 1 |
| files | 3 | 1: Documents 3 |
| drawing sheets | 6 | 1: Drawings 6 |

### Records on two or more pages, and lists that are the same list twice

**PM (Alan), desktop, 121 State Street:** 91 records on two or more pages: schedule lines 31 (up to 6 pages); materials 18 (up to 8 pages); to-dos 11 (up to 2 pages); decisions 5 (up to 4 pages); files 5 (up to 3 pages); site questions 5 (up to 2 pages); submittals 5 (up to 2 pages); purchase orders 2 (up to 3 pages); inspections 2 (up to 2 pages); change orders 2 (up to 2 pages); invoices 2 (up to 2 pages); estimates 2 (up to 2 pages); bills 1 (up to 2 pages).

- "Insulation" (materials) on 8 pages: Change Orders, Costs, Field, Job Page, Materials, Permits, Schedule, Tasks
- "Flooring" (materials) on 8 pages: Change Orders, Costs, Deliveries, Field, Job Page, Materials, Schedule, Tasks
- "Rough plumbing" (schedule lines) on 6 pages: Decisions, Job Page, Materials, Permits, Schedule, Tasks
- "Framing & blocking – 3rd floor" (schedule lines) on 6 pages: Change Orders, Field, Job Page, Materials, Schedule, Tasks
- "Rough inspection & insulation" (schedule lines) on 6 pages: Field, Job Page, Materials, Permits, Schedule, Tasks
- "Millwork – parlor kitchen & laundry" (schedule lines) on 6 pages: Change Orders, Field, Job Page, Materials, Schedule, Tasks
- the same list twice (3 or more shared records, at least half of the shorter list): Job Page and Tasks (27 shared, of 58 and 35: schedule lines, to-dos, materials); Job Page and Schedule (22 shared, of 58 and 38: schedule lines, materials, decisions); Schedule and Tasks (22 shared, of 38 and 35: schedule lines, materials, decisions); Materials and Schedule (21 shared, of 42 and 38: schedule lines, materials); Field and Job Page (12 shared, of 15 and 58: schedule lines, site questions, materials); Decisions and Job Page (11 shared, of 17 and 58: decisions, schedule lines, materials)

**PM (Alan), desktop, 45 Cranberry St — design:** 14 records on two or more pages: schedule lines 5 (up to 6 pages); to-dos 4 (up to 2 pages); submittals 2 (up to 2 pages); invoices 2 (up to 2 pages); estimates 1 (up to 2 pages).

- "Construction documents" (schedule lines) on 6 pages: Change Orders, Costs, Drawings, Job Page, Schedule, Tasks
- "Filing & permits" (schedule lines) on 5 pages: Change Orders, Costs, Job Page, Schedule, Tasks
- "Design development" (schedule lines) on 5 pages: Change Orders, Costs, Job Page, Schedule, Tasks
- "LPC Certificate of Appropriateness" (schedule lines) on 4 pages: Change Orders, Permits, Schedule, Tasks
- "Construction administration" (schedule lines) on 4 pages: Change Orders, Costs, Schedule, Tasks
- "Friday client update — 121 State Street" (to-dos) on 2 pages: Job Page, Tasks
- the same list twice (3 or more shared records, at least half of the shorter list): Job Page and Tasks (7 shared, of 7 and 9: to-dos, schedule lines); Change Orders and Schedule (5 shared, of 18 and 5: schedule lines); Change Orders and Tasks (5 shared, of 18 and 9: schedule lines); Schedule and Tasks (5 shared, of 5 and 9: schedule lines); Change Orders and Costs (4 shared, of 18 and 4: schedule lines); Costs and Schedule (4 shared, of 4 and 5: schedule lines)

**Owner, desktop, 121 State Street:** 86 records on two or more pages: schedule lines 31 (up to 6 pages); materials 18 (up to 8 pages); to-dos 11 (up to 2 pages); decisions 5 (up to 4 pages); files 5 (up to 3 pages); submittals 5 (up to 2 pages); purchase orders 2 (up to 3 pages); inspections 2 (up to 2 pages); site questions 2 (up to 2 pages); change orders 2 (up to 2 pages); estimates 2 (up to 2 pages); bills 1 (up to 2 pages).

- "Insulation" (materials) on 8 pages: Change Orders, Costs, Field, Job Page, Materials, Permits, Schedule, Tasks
- "Flooring" (materials) on 8 pages: Change Orders, Costs, Deliveries, Field, Job Page, Materials, Schedule, Tasks
- "Rough plumbing" (schedule lines) on 6 pages: Decisions, Job Page, Materials, Permits, Schedule, Tasks
- "Framing & blocking – 3rd floor" (schedule lines) on 6 pages: Change Orders, Field, Job Page, Materials, Schedule, Tasks
- "Rough inspection & insulation" (schedule lines) on 6 pages: Field, Job Page, Materials, Permits, Schedule, Tasks
- "Millwork – parlor kitchen & laundry" (schedule lines) on 6 pages: Change Orders, Field, Job Page, Materials, Schedule, Tasks
- the same list twice (3 or more shared records, at least half of the shorter list): Job Page and Tasks (27 shared, of 55 and 35: schedule lines, to-dos, materials); Job Page and Schedule (22 shared, of 55 and 38: schedule lines, materials, decisions); Schedule and Tasks (22 shared, of 38 and 35: schedule lines, materials, decisions); Materials and Schedule (21 shared, of 42 and 38: schedule lines, materials); Decisions and Job Page (11 shared, of 17 and 55: decisions, schedule lines, materials); Field and Schedule (10 shared, of 15 and 38: schedule lines, materials)

**Owner, desktop, 45 Cranberry St — design:** 12 records on two or more pages: schedule lines 5 (up to 6 pages); to-dos 4 (up to 2 pages); submittals 2 (up to 2 pages); estimates 1 (up to 2 pages).

- "Construction documents" (schedule lines) on 6 pages: Change Orders, Costs, Drawings, Job Page, Schedule, Tasks
- "Filing & permits" (schedule lines) on 5 pages: Change Orders, Costs, Job Page, Schedule, Tasks
- "Design development" (schedule lines) on 5 pages: Change Orders, Costs, Job Page, Schedule, Tasks
- "LPC Certificate of Appropriateness" (schedule lines) on 4 pages: Change Orders, Permits, Schedule, Tasks
- "Construction administration" (schedule lines) on 4 pages: Change Orders, Costs, Schedule, Tasks
- "Friday client update — 121 State Street" (to-dos) on 2 pages: Job Page, Tasks
- the same list twice (3 or more shared records, at least half of the shorter list): Job Page and Tasks (7 shared, of 7 and 9: to-dos, schedule lines); Change Orders and Schedule (5 shared, of 18 and 5: schedule lines); Change Orders and Tasks (5 shared, of 18 and 9: schedule lines); Schedule and Tasks (5 shared, of 5 and 9: schedule lines); Change Orders and Costs (4 shared, of 18 and 4: schedule lines); Costs and Schedule (4 shared, of 4 and 5: schedule lines)

**Coordinator (Chen), desktop, 121 State Street:** 82 records on two or more pages: schedule lines 32 (up to 6 pages); materials 16 (up to 6 pages); to-dos 11 (up to 2 pages); decisions 5 (up to 4 pages); files 5 (up to 3 pages); submittals 5 (up to 2 pages); site questions 4 (up to 2 pages); purchase orders 2 (up to 3 pages); inspections 2 (up to 2 pages).

- the same list twice (3 or more shared records, at least half of the shorter list): Job Page and Tasks (27 shared, of 58 and 35: schedule lines, to-dos, materials); Job Page and Schedule (22 shared, of 58 and 38: schedule lines, materials, decisions); Schedule and Tasks (22 shared, of 38 and 35: schedule lines, materials, decisions); Materials and Schedule (21 shared, of 42 and 38: schedule lines, materials); Decisions and Job Page (11 shared, of 17 and 58: decisions, schedule lines, materials); Field and Job Page (11 shared, of 15 and 58: schedule lines, site questions, materials)

**Coordinator (Chen), desktop, 45 Cranberry St — design:** 11 records on two or more pages: schedule lines 5 (up to 4 pages); to-dos 4 (up to 2 pages); submittals 2 (up to 2 pages).

- the same list twice (3 or more shared records, at least half of the shorter list): Job Page and Tasks (7 shared, of 7 and 9: to-dos, schedule lines); Schedule and Tasks (5 shared, of 5 and 9: schedule lines); Job Page and Schedule (3 shared, of 7 and 5: schedule lines)

**Foreman (Angel), desktop, 121 State Street:** 15 records on two or more pages: schedule lines 11 (up to 4 pages); materials 2 (up to 2 pages); subs to confirm 1 (up to 2 pages); files 1 (up to 2 pages).

- "Restoration" (schedule lines) on 4 pages: Daily Log, Job Page, Photos, Schedule
- "Rough electrical" (schedule lines) on 4 pages: Daily Log, Job Page, Photos, Schedule
- "Windows & interior trim" (schedule lines) on 3 pages: Daily Log, Job Page, Schedule
- "Millwork – parlor kitchen & laundry" (schedule lines) on 3 pages: Daily Log, Job Page, Schedule
- "Rough plumbing" (schedule lines) on 3 pages: Crew, Job Page, Schedule
- "Demo & subfloor prep" (schedule lines) on 3 pages: Daily Log, Requests, Schedule
- the same list twice (3 or more shared records, at least half of the shorter list): Daily Log and Schedule (8 shared, of 9 and 29: schedule lines); Requests and Schedule (3 shared, of 5 and 29: schedule lines)

**Designer (Sarah), desktop, 121 State Street:** 27 records on two or more pages: schedule lines 15 (up to 3 pages); decisions 8 (up to 3 pages); materials 3 (up to 2 pages); files 1 (up to 2 pages).

- the same list twice (3 or more shared records, at least half of the shorter list): Schedule and Tasks (15 shared, of 29 and 35: schedule lines, materials); Decisions and Job Page (9 shared, of 17 and 9: decisions, materials)

**Designer (Sarah), desktop, 45 Cranberry St — design:** 1 records on two or more pages: schedule lines 1 (up to 2 pages).


**Billing, desktop, 121 State Street:** 4 records on two or more pages: files 3 (up to 2 pages); purchase orders 1 (up to 2 pages).


**Client (Klein), desktop, 121 State Street:** 20 records on two or more pages: schedule lines 8 (up to 3 pages); decisions 5 (up to 3 pages); materials 4 (up to 3 pages); submittals 1 (up to 2 pages); invoices 1 (up to 2 pages); change orders 1 (up to 3 pages).

- "Rough plumbing" (schedule lines) on 3 pages: Decisions, Job Page, Schedule
- "Confirm new 3rd fl tile selection is in stock" (decisions) on 3 pages: Decisions, Job Page, Schedule
- "Exterior paint finish / sheen" (decisions) on 3 pages: Decisions, Job Page, Schedule
- "3rd fl lighting layout approval" (decisions) on 3 pages: Decisions, Job Page, Schedule
- "Garden kitchen backsplash: tile or stone?" (decisions) on 3 pages: Decisions, Job Page, Schedule
- "2nd fl bathroom finishes re-review with client" (decisions) on 3 pages: Decisions, Job Page, Schedule
- the same list twice (3 or more shared records, at least half of the shorter list): Job Page and Schedule (15 shared, of 21 and 16: schedule lines, decisions, materials); Decisions and Job Page (13 shared, of 17 and 21: decisions, materials, schedule lines); Decisions and Schedule (9 shared, of 17 and 16: decisions, materials, schedule lines)

**Crew (Alberto), desktop, 121 State Street:** 5 records on two or more pages: schedule lines 3 (up to 2 pages); materials 1 (up to 2 pages); files 1 (up to 2 pages).

- the same list twice (3 or more shared records, at least half of the shorter list): Job Page and Requests (3 shared, of 29 and 4: schedule lines)

**PM (Alan), phone, 121 State Street:** 71 records on two or more pages: schedule lines 26 (up to 6 pages); materials 14 (up to 8 pages); to-dos 8 (up to 3 pages); files 5 (up to 4 pages); submittals 5 (up to 2 pages); decisions 4 (up to 4 pages); purchase orders 2 (up to 4 pages); change orders 2 (up to 2 pages); invoices 2 (up to 2 pages); estimates 2 (up to 2 pages); bills 1 (up to 3 pages).

- "Insulation" (materials) on 8 pages: Change Orders, Costs, Field, Job Page, Job Page as it opens (All projects), Materials, Permits, Schedule
- "Flooring" (materials) on 7 pages: Change Orders, Costs, Field, Job Page, Job Page as it opens (All projects), Materials, Schedule
- "Framing & blocking – garden bedroom" (schedule lines) on 6 pages: Decisions, Field, Job Page, Job Page as it opens (All projects), Schedule, Tasks
- "Rough plumbing" (schedule lines) on 6 pages: Decisions, Job Page, Job Page as it opens (All projects), Materials, Permits, Schedule
- "Rough inspection & insulation" (schedule lines) on 6 pages: Field, Job Page, Job Page as it opens (All projects), Materials, Permits, Schedule
- "Framing & blocking – 3rd floor" (schedule lines) on 5 pages: Field, Job Page, Materials, Schedule, Tasks
- the same list twice (3 or more shared records, at least half of the shorter list): Job Page and Job Page as it opens (All projects) (26 shared, of 32 and 28: to-dos, schedule lines, materials); Materials and Schedule (21 shared, of 42 and 38: schedule lines, materials); Job Page and Tasks (15 shared, of 32 and 18: to-dos, schedule lines, decisions); Job Page as it opens (All projects) and Tasks (11 shared, of 28 and 18: to-dos, schedule lines); Field and Schedule (10 shared, of 15 and 38: schedule lines, materials); Permits and Schedule (10 shared, of 20 and 38: schedule lines, materials)

**PM (Alan), phone, 45 Cranberry St — design:** 14 records on two or more pages: schedule lines 5 (up to 5 pages); to-dos 4 (up to 2 pages); submittals 2 (up to 2 pages); invoices 2 (up to 2 pages); estimates 1 (up to 2 pages).

- "Design development" (schedule lines) on 5 pages: Change Orders, Costs, Job Page, Schedule, Tasks
- "Construction documents" (schedule lines) on 5 pages: Change Orders, Costs, Drawings, Job Page, Schedule
- "Filing & permits" (schedule lines) on 4 pages: Change Orders, Costs, Job Page, Schedule
- "LPC Certificate of Appropriateness" (schedule lines) on 3 pages: Change Orders, Permits, Schedule
- "Construction administration" (schedule lines) on 3 pages: Change Orders, Costs, Schedule
- "Friday client update — 121 State Street" (to-dos) on 2 pages: Job Page, Tasks
- the same list twice (3 or more shared records, at least half of the shorter list): Change Orders and Schedule (5 shared, of 13 and 5: schedule lines); Job Page and Tasks (5 shared, of 7 and 5: to-dos, schedule lines); Change Orders and Costs (4 shared, of 13 and 4: schedule lines); Costs and Schedule (4 shared, of 4 and 5: schedule lines); Costs and Job Page (3 shared, of 4 and 7: schedule lines); Job Page and Schedule (3 shared, of 7 and 5: schedule lines)

## 3. One Label, Different Numbers

The same label (a tile, a figure, a tab or section count, a strip badge) with numbers that share no value on two pages of one job, for one role. Some are right about different scopes ("Open" against "All"); the person still reads one word with two numbers. Each needs a person to judge.

**PM (Alan), desktop, 121 State Street** (1):
- ready bill: $12,651 on Job Page; $46K on Billing, Change Orders

**PM (Alan), desktop, 45 Cranberry St — design** (1):
- ready bill: $23,366 on Job Page; $46K on Billing, Change Orders

**Owner, desktop, 121 State Street** (1):
- ready bill: $12,651 on Job Page; $46K on Change Orders

**Owner, desktop, 45 Cranberry St — design** (1):
- ready bill: $23,366 on Job Page; $46K on Change Orders

**PM (Alan), phone, 121 State Street** (1):
- ready bill: $12,651 on Job Page; $46K on Billing, Change Orders

**PM (Alan), phone, 45 Cranberry St — design** (1):
- ready bill: $23,366 on Job Page; $46K on Billing, Change Orders

## 4. Empty, Dead and Broken Screens

| Device | Role | Job | Screen | What |
|---|---|---|---|---|
| desktop | PM (Alan) | 121 State Street | Materials | 1 save(s) while reading |
| desktop | PM (Alan) | 45 Cranberry St — design | Decisions | lists nothing: "All clear blocking work · past due · with client · ours to m" |
| desktop | PM (Alan) | 45 Cranberry St — design | Field | lists nothing: "nothing waiting on an answer" |
| desktop | PM (Alan) | 45 Cranberry St — design | Deliveries | 22 words; lists nothing: "Nothing on order for this job." |
| desktop | PM (Alan) | 45 Cranberry St — design | Materials | lists nothing: "All clear late to order · order this week · at risk · not on" |
| desktop | PM (Alan) | 45 Cranberry St — design | Change Orders | lists nothing: "No change orders yet." |
| desktop | PM (Alan) | 45 Cranberry St — design | Mail | lists nothing: "No messages routed to 45 Cranberry St — design yet. Mail, te" |
| desktop | Owner | 45 Cranberry St — design | Decisions | lists nothing: "All clear blocking work · past due · with client · ours to m" |
| desktop | Owner | 45 Cranberry St — design | Field | lists nothing: "nothing waiting on an answer" |
| desktop | Owner | 45 Cranberry St — design | Deliveries | 22 words; lists nothing: "Nothing on order for this job." |
| desktop | Owner | 45 Cranberry St — design | Materials | lists nothing: "All clear late to order · order this week · at risk · not on" |
| desktop | Owner | 45 Cranberry St — design | Change Orders | lists nothing: "No change orders yet." |
| desktop | Owner | 45 Cranberry St — design | Mail | lists nothing: "No messages routed to 45 Cranberry St — design yet. Mail, te" |
| desktop | Coordinator (Chen) | 45 Cranberry St — design | Decisions | lists nothing: "All clear blocking work · past due · with client · ours to m" |
| desktop | Coordinator (Chen) | 45 Cranberry St — design | Field | lists nothing: "nothing waiting on an answer" |
| desktop | Coordinator (Chen) | 45 Cranberry St — design | Deliveries | 22 words; lists nothing: "Nothing on order for this job." |
| desktop | Coordinator (Chen) | 45 Cranberry St — design | Materials | lists nothing: "All clear late to order · order this week · at risk · not on" |
| desktop | Coordinator (Chen) | 45 Cranberry St — design | Mail | lists nothing: "No messages routed to 45 Cranberry St — design yet. Mail, te" |
| desktop | Foreman (Angel) | 45 Cranberry St — design | Job page | lists nothing: "No sub days on the calendar. Add one so it can be confirmed." |
| desktop | Foreman (Angel) | 45 Cranberry St — design | Daily Log | lists nothing: "No earlier logs on this job." |
| desktop | Foreman (Angel) | 45 Cranberry St — design | Schedule | lists nothing: "No tasks on the construction track yet. Add one, or pick ano" |
| desktop | Designer (Sarah) | 121 State Street | Tasks[Overdue] | 24 words |
| desktop | Designer (Sarah) | 45 Cranberry St — design | Schedule | lists nothing: "No tasks on the construction track yet. Add one, or pick ano" |
| desktop | Designer (Sarah) | 45 Cranberry St — design | Decisions | lists nothing: "All clear blocking work · past due · with client · ours to m" |
| desktop | Designer (Sarah) | 45 Cranberry St — design | Drawings | opens plans when asked for sdraw |
| desktop | Client (Klein) | 121 State Street | Chat | lists nothing: "No messages yet Ask anything. Your project team answers here" |
| desktop | Crew (Alberto) | 45 Cranberry St — design | Job page | lists nothing: "No tasks on the construction track yet. Add one, or pick ano" |
| desktop | Crew (Alberto) | 45 Cranberry St — design | Deliveries | 22 words; lists nothing: "Nothing on order for this job." |
| desktop | Driver (Alex) | 45 Cranberry St — design | Requests | lists nothing: "Nothing yet." |
| phone | PM (Alan) | 45 Cranberry St — design | Decisions | lists nothing: "All clear blocking work · past due · with client · ours to m" |
| phone | PM (Alan) | 45 Cranberry St — design | Field | lists nothing: "nothing waiting on an answer" |
| phone | PM (Alan) | 45 Cranberry St — design | Deliveries | 8 words; lists nothing: "Nothing on order for this job." |
| phone | PM (Alan) | 45 Cranberry St — design | Materials | lists nothing: "All clear late to order · order this week · at risk · not on" |
| phone | PM (Alan) | 45 Cranberry St — design | Change Orders | lists nothing: "No change orders yet." |
| phone | PM (Alan) | 45 Cranberry St — design | Mail | lists nothing: "No messages routed to 45 Cranberry St — design yet. Mail, te" |
| phone | Owner | 45 Cranberry St — design | Decisions | lists nothing: "All clear blocking work · past due · with client · ours to m" |
| phone | Owner | 45 Cranberry St — design | Field | lists nothing: "nothing waiting on an answer" |
| phone | Owner | 45 Cranberry St — design | Deliveries | 8 words; lists nothing: "Nothing on order for this job." |
| phone | Owner | 45 Cranberry St — design | Materials | lists nothing: "All clear late to order · order this week · at risk · not on" |
| phone | Owner | 45 Cranberry St — design | Change Orders | lists nothing: "No change orders yet." |
| phone | Owner | 45 Cranberry St — design | Mail | lists nothing: "No messages routed to 45 Cranberry St — design yet. Mail, te" |
| phone | Coordinator (Chen) | 45 Cranberry St — design | Decisions | lists nothing: "All clear blocking work · past due · with client · ours to m" |
| phone | Coordinator (Chen) | 45 Cranberry St — design | Field | lists nothing: "nothing waiting on an answer" |
| phone | Coordinator (Chen) | 45 Cranberry St — design | Deliveries | 8 words; lists nothing: "Nothing on order for this job." |
| phone | Coordinator (Chen) | 45 Cranberry St — design | Materials | lists nothing: "All clear late to order · order this week · at risk · not on" |
| phone | Coordinator (Chen) | 45 Cranberry St — design | Mail | lists nothing: "No messages routed to 45 Cranberry St — design yet. Mail, te" |
| phone | Foreman (Angel) | 45 Cranberry St — design | Job page | lists nothing: "No sub days on the calendar. Add one so it can be confirmed." |
| phone | Foreman (Angel) | 45 Cranberry St — design | Daily Log | lists nothing: "No earlier logs on this job." |
| phone | Foreman (Angel) | 45 Cranberry St — design | Schedule | lists nothing: "Nothing with your name." |
| phone | Designer (Sarah) | 45 Cranberry St — design | Schedule | 20 words; lists nothing: "No tasks on the construction track yet. Add one, or pick ano" |
| phone | Designer (Sarah) | 45 Cranberry St — design | Schedule[Gantt] | 24 words |
| phone | Designer (Sarah) | 45 Cranberry St — design | Schedule[Gantt][Wide] | 24 words |
| phone | Designer (Sarah) | 45 Cranberry St — design | Schedule[Gantt][Day] | 24 words |
| phone | Designer (Sarah) | 45 Cranberry St — design | Decisions | lists nothing: "All clear blocking work · past due · with client · ours to m" |
| phone | Designer (Sarah) | 45 Cranberry St — design | Drawings | opens plans when asked for sdraw |
| phone | Client (Klein) | 121 State Street | Chat | 22 words; lists nothing: "No messages yet Ask anything. Your project team answers here" |
| phone | Crew (Alberto) | 45 Cranberry St — design | Job page | lists nothing: "Nothing with your name." |
| phone | Crew (Alberto) | 45 Cranberry St — design | Requests | 24 words |
| phone | Crew (Alberto) | 45 Cranberry St — design | Deliveries | 9 words; lists nothing: "Nothing on order for this job." |
| phone | Driver (Alex) | 45 Cranberry St — design | Requests | 23 words; lists nothing: "Nothing yet." |

## 5. The Phone at 390

"Cut off" is text the phone ends early (a row's second line clipped at the edge); "scrolls inside" is a strip of tiles or tabs that the person swipes sideways inside the page (the page itself does not move). Pages taller than 3 phone screens are listed with their height.

| Role | Screens | The page scrolls sideways | Text cut off at the edge | Strips that scroll inside the page | The sub-tab strip | Pages taller than 3 screens |
|---|---|---|---|---|---|---|
| PM (Alan) | 113 | 0 | 9: Change Orders, Decisions, Documents, Field, Materials, Permits, Projects, Schedule | 15: Billing, Change Orders, Costs, Decisions, Documents, Estimates, Field, Mail | shown: 3 of 19 entries on screen without a swipe | 5: Job page 4.6, Schedule 3.9, Costs 4.1, Documents 5.6, Drawings 5.8 |
| Owner | 109 | 0 | 9: Change Orders, Decisions, Documents, Field, Materials, Permits, Projects, Schedule | 14: Change Orders, Costs, Decisions, Documents, Estimates, Field, Mail, Materials | shown: 3 of 18 entries on screen without a swipe | 5: Job page 4.6, Schedule 3.9, Costs 4.1, Documents 5.5, Drawings 5.8 |
| Coordinator (Chen) | 85 | 0 | 8: Decisions, Documents, Field, Materials, Permits, Projects, Schedule, Tasks | 11: Decisions, Documents, Field, Mail, Materials, Permits, Photos, Project Settings | shown: 3 of 15 entries on screen without a swipe | 4: Job page 4.4, Schedule 3.9, Documents 5.5, Drawings 5.7 |
| Foreman (Angel) | 49 | 0 | 3: Documents, Drawings, Job Page | 2: Documents, Photos | none | 4: Job page 3.5, Drawings 5.5, Schedule 3.1, Documents 4.7 |
| Designer (Sarah) | 57 | 0 | 5: Decisions, Documents, Projects, Schedule, Tasks | 6: Decisions, Documents, Job Page, Photos, Projects, Schedule | shown: 4 of 4 entries on screen without a swipe | 1: Documents 5.5 |
| Billing | 26 | 0 | 2: Documents, Projects | 2: Documents, Projects | shown: 3 of 3 entries on screen without a swipe | 2: Job page 4.4, Documents 5.5 |
| Controller | 15 | 0 | 2: Job Page, Projects | 2: Job Page, Projects | shown: 3 of 3 entries on screen without a swipe | 0 |
| Client (Klein) | 6 | 0 | 0 | 1: Chat | none | 1: Job page 3.7 |
| Crew (Alberto) | 24 | 0 | 2: Drawings, Photos | 1: Photos | none | 3: Job page 3.6, Photos 4.7, Drawings 5.5 |
| Driver (Alex) | 18 | 0 | 1: Job Page | 1: Job Page | none | 1: Job page 4.7 |

## 6. What the Menu Opens That the Job Page Does Not, and the Reverse

Module pages only (the job's pages, Messages, Drawings, Selections). Desktop menu, then the phone's.

| Role | Device | In the menu, not reached from the job page | Reached from the job page, not in the menu | Module pages in two or more menu places |
|---|---|---|---|---|
| PM (Alan) | desktop | chat (Messages › Messages), sel (Purchasing › Selections) | - | chat (Messages › Messages; Bar › Messages); ovjobs (Projects › Projects; Bar › Projects); recv (Projects › Deliveries; Purchasing › Deliveries); billing (Projects › Change Orders; Projects › Estimates; Projects › Billing) |
| PM (Alan) | phone | chat (Messages › Messages), sel (Purchasing › Selections) | - | chat (Messages › Messages; Bar › Messages); ovjobs (Projects › Projects; Bar › Projects); recv (Projects › Deliveries; Purchasing › Deliveries); billing (Projects › Change Orders; Projects › Estimates; Projects › Billing) |
| Owner | desktop | chat (Messages › Messages), sel (Design › Selections) | - | chat (Messages › Messages; Bar › Messages); ovjobs (Projects › Projects; Bar › Projects); recv (Projects › Deliveries; Purchasing › Deliveries); billing (Projects › Change Orders; Projects › Estimates; Accounting › Billing; Sales › Estimates); plans (Projects › Drawings; Design › Drawings) |
| Owner | phone | chat (Messages › Messages), sel (Design › Selections) | - | chat (Messages › Messages; Bar › Messages); ovjobs (Projects › Projects; Bar › Projects); recv (Projects › Deliveries; Purchasing › Deliveries); billing (Projects › Change Orders; Projects › Estimates; Accounting › Billing; Sales › Estimates); plans (Projects › Drawings; Design › Drawings) |
| Coordinator (Chen) | desktop | chat (Messages › Messages), sel (Purchasing › Selections) | - | chat (Messages › Messages; Bar › Messages); recv (Purchasing › Deliveries; Projects › Deliveries) |
| Coordinator (Chen) | phone | chat (Messages › Messages), sel (Purchasing › Selections) | - | chat (Messages › Messages; Bar › Messages); recv (Purchasing › Deliveries; Projects › Deliveries) |
| Foreman (Angel) | desktop | chat (Bar › Messages) | - | - |
| Foreman (Angel) | phone | chat (Bar › Messages) | - | - |
| Designer (Sarah) | desktop | chat (Messages › Messages), plans (Drawings › Drawings), sel (Design › Selections) | - | chat (Messages › Messages; Bar › Messages); plans (Drawings › Drawings; Bar › Drawings); ovjobs (Projects › Projects; Bar › Projects) |
| Designer (Sarah) | phone | chat (Messages › Messages), plans (Drawings › Drawings), sel (Design › Selections) | - | chat (Messages › Messages; Bar › Messages); plans (Drawings › Drawings; Bar › Drawings); ovjobs (Projects › Projects; Bar › Projects) |
| Billing | desktop | billing (Billing › Billing), chat (Messages › Messages) | - | chat (Messages › Messages; Bar › Messages) |
| Billing | phone | billing (Billing › Billing), chat (Messages › Messages) | - | chat (Messages › Messages; Bar › Messages) |
| Controller | desktop | billing (Billing › Billing), chat (Messages › Messages) | - | chat (Messages › Messages; Bar › Messages) |
| Controller | phone | billing (Billing › Billing), chat (Messages › Messages) | - | chat (Messages › Messages; Bar › Messages) |
| Client (Klein) | desktop | - | chat, clacct, client, dec, sched | - |
| Client (Klein) | phone | - | chat, clacct, client, dec, sched | - |
| Crew (Alberto) | desktop | chat (Bar › Messages) | - | - |
| Crew (Alberto) | phone | chat (Bar › Messages) | - | - |
| Driver (Alex) | desktop | chat (Bar › Messages) | - | - |
| Driver (Alex) | phone | chat (Bar › Messages) | - | - |

## 7. What a Tap on a Job in the Projects List Opens

| Role | Device | Job | Tapped | Opens |
|---|---|---|---|---|
| PM (Alan) | desktop | 121 State Street | 121 State StreetSarah & David Klein541211/4on targ | dash (job p121) |
| PM (Alan) | desktop | 45 Cranberry St — design | 45 Cranberry St — designRivera family9811/11on tar | dash (job p45) |
| PM (Alan) | phone | 121 State Street | 121 State StreetSarah & David Klein541211/4on targ | dash (job p121), showing All projects |
| PM (Alan) | phone | 45 Cranberry St — design | 45 Cranberry St — designRivera family9811/11on tar | dash (job p45), showing All projects |
| Owner | desktop | 121 State Street | 121 State StreetSarah & David Klein481211/4on targ | dash (job p121) |
| Owner | desktop | 45 Cranberry St — design | 45 Cranberry St — designRivera family9011/11on tar | dash (job p45) |
| Owner | phone | 121 State Street | 121 State StreetSarah & David Klein481211/4on targ | dash (job p121), showing All projects |
| Owner | phone | 45 Cranberry St — design | 45 Cranberry St — designRivera family9011/11on tar | dash (job p45), showing All projects |
| Coordinator (Chen) | desktop | 121 State Street | 121 State StreetSarah & David Klein541211/4on targ | dash (job p121) |
| Coordinator (Chen) | desktop | 45 Cranberry St — design | 45 Cranberry St — designRivera family9811/11on tar | dash (job p45) |
| Coordinator (Chen) | phone | 121 State Street | 121 State StreetSarah & David Klein541211/4on targ | dash (job p121), showing All projects |
| Coordinator (Chen) | phone | 45 Cranberry St — design | 45 Cranberry St — designRivera family9811/11on tar | dash (job p45), showing All projects |
| Foreman (Angel) | desktop | - | cannot open the Projects list | - |
| Foreman (Angel) | phone | - | cannot open the Projects list | - |
| Designer (Sarah) | desktop | 121 State Street | 121 State StreetSarah & David Klein541211/4on targ | sboard (job p121) |
| Designer (Sarah) | desktop | 45 Cranberry St — design | 45 Cranberry St — designRivera family9811/11on tar | sboard (job p45) |
| Designer (Sarah) | phone | 121 State Street | 121 State StreetSarah & David Klein541211/4on targ | sboard (job p121) |
| Designer (Sarah) | phone | 45 Cranberry St — design | 45 Cranberry St — designRivera family9811/11on tar | sboard (job p45) |
| Billing | desktop | 121 State Street | 121 State StreetSarah & David Klein541211/4on targ | dash (job p121) |
| Billing | desktop | 45 Cranberry St — design | 45 Cranberry St — designRivera family9811/11on tar | dash (job p45) |
| Billing | phone | 121 State Street | 121 State StreetSarah & David Klein541211/4on targ | dash (job p121), showing All projects |
| Billing | phone | 45 Cranberry St — design | 45 Cranberry St — designRivera family9811/11on tar | dash (job p45), showing All projects |
| Controller | desktop | 121 State Street | 121 State StreetSarah & David Klein541211/4on targ | gl (job p121) |
| Controller | desktop | 45 Cranberry St — design | 45 Cranberry St — designRivera family9811/11on tar | gl (job p45) |
| Controller | phone | 121 State Street | 121 State StreetSarah & David Klein541211/4on targ | gl (job p121) |
| Controller | phone | 45 Cranberry St — design | 45 Cranberry St — designRivera family9811/11on tar | gl (job p45) |
| Client (Klein) | desktop | - | cannot open the Projects list | - |
| Client (Klein) | phone | - | cannot open the Projects list | - |
| Crew (Alberto) | desktop | - | cannot open the Projects list | - |
| Crew (Alberto) | phone | - | cannot open the Projects list | - |
| Driver (Alex) | desktop | - | cannot open the Projects list | - |
| Driver (Alex) | phone | - | cannot open the Projects list | - |

## 8. The PM's Projects, Page by Page, in Full

Every page the PM reaches from the job page, as it opens, then each of its tabs. Heights are in screens of that device (900px desktop, 844px phone); "above the fold" is above the bottom bar on the phone. Records are the information map's catalog plus the job's own nouns, found by their words.

### PM, desktop, 121 State Street

The Projects list (rail: Projects 2):
- **Projects** (`ovjobs`): heading "Projects", 0.8 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: New Project
  - lead: "Every job, ranked by how much attention it needs today. Open one for its overview."
  - sections: Email
  - figures: Finish Dates Late 0; Jobs Needing You 2; Materials at Risk 1; Billed Ahead +$156K
  - records: 6 schedule lines
  - columns: table: PROJECT, CLIENT, HEALTH (0–100), NEEDS YOU, COMPLETION, VS TARGET, CONTRACT, BILLED, OWED (4 rows)
  - fields: Search…
  - empty states: "Nothing checked yet."
  - a tap on the 121 State Street row opens `dash`

The sub-tab strip (shown on this screen size): Projects, Overview 12, Project Settings, Schedule, Tasks, Decisions 3, Submittals 2, Permits 1, Field 3, Photos, Deliveries, Materials 5, Costs, Change Orders, Estimates, Billing, Documents, Drawings, Mail.

- **Job Page** (`dash`): heading "Overview", 3.7 screens tall, 6 sections (1 above the fold), 0 tab screens; blue: none
  - lead: "121 State Street — what is happening on this job today and what is about to."
  - sections: Look-Ahead; Needs Attention (4); Pinned Plans (17); Daily Brief; Ahead of Schedule; Since Yesterday (6)
  - figures: Schedule At risk; Costs +$131,058 billed ahead; Needs You 12 now; Materials 5 at risk; Ready to bill on this job $12,651; Over budget on this job $3,800
  - records: 19 schedule lines, 11 materials, 10 to-dos, 5 decisions, 4 site questions, 3 files, 2 field requests, 2 inspections
  - tab groups: 10 Working Days / 
- **Project Settings** (`proj`): heading "Project Settings", 1.5 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: none
  - lead: "Dates, address, client, entity, holidays and site hours for this project."
  - sections: Project
  - fields: Name, Address, Target substantial completion, Crew Out (Hard Finish), BIN or job #, LPC-…, Milestone That Marks substantial complet, Holidays (one per line, YYYY-MM-DD, opti, Today (leave blank to use the real date), e.g. Chen, Automation, Site Working Hours
- **Schedule** (`sched`): heading "Schedule", 1.9 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: New Task
  - lead: "Site hours 07:30–16:30, Mon Tue Wed Thu Fri, 30 min lunch (8.5 h/day). All tracks — design, permitting, procurement, construction and closeout share one depende"
  - records: 33 schedule lines, 4 materials, 1 decisions
  - tab groups: Gantt / List / Changes; Fit / Wide / Day
  - tab **List**: heading "Schedule", 0 sections; 33 schedule lines, 4 materials, 1 decisions
  - tab **Changes**: heading "Schedule", 1 sections
  - tab **Wide**: heading "Schedule", 0 sections; 33 schedule lines, 4 materials, 1 decisions
  - tab **Day**: heading "Schedule", 0 sections; 33 schedule lines, 4 materials, 1 decisions
- **Tasks** (`tasks`): heading "Tasks", 1.1 screens tall, 0 sections (0 above the fold), 18 tab screens; blue: New Task
  - lead: "26 open on 121 State Street — to-dos, schedule lines and field items with a name on them"
  - records: 10 to-dos, 6 schedule lines, 1 decisions, 1 site questions
  - fields: Search tasks, How the list is grouped, Quick add a task
  - tab groups: List / Table / Board / Calendar; Mine / Team / Everyone / Unassigned; Due Soon / Today / Overdue / No Date / Waiting / Later / Done / All; Waiting on Carlos Millwork for the shop  / Owner: Chen Biron / Due Mon, Sep / Status: Waiting On
  - tab **Table**: heading "Tasks", 0 sections; 10 to-dos, 6 schedule lines, 1 decisions, 1 site questions
  - tab **Table › Owner**: heading "Tasks", 0 sections; 10 to-dos, 6 schedule lines, 1 decisions, 1 site questions
  - tab **Table › Status**: heading "Tasks", 0 sections; 10 to-dos, 6 schedule lines, 1 decisions, 1 site questions
  - tab **Board**: heading "Tasks", 0 sections; 10 to-dos, 6 schedule lines, 1 decisions, 1 site questions
  - tab **Calendar**: heading "Tasks", 0 sections; 10 to-dos, 6 schedule lines, 1 decisions, 1 site questions
  - tab **Calendar › Week**: heading "Tasks", 0 sections; 10 to-dos, 6 schedule lines, 1 decisions, 1 site questions
  - tab **Mine**: heading "Tasks", 0 sections; 6 to-dos
  - tab **Team**: heading "Tasks", 0 sections; 6 schedule lines, 4 to-dos, 1 decisions, 1 site questions
  - tab **Unassigned**: heading "Tasks", 0 sections
  - tab **Today**: heading "Tasks", 0 sections; 2 to-dos
  - tab **Overdue**: heading "Tasks", 0 sections
  - tab **No Date**: heading "Tasks", 0 sections
  - tab **Waiting**: heading "Tasks", 0 sections; 1 to-dos
  - tab **Later**: heading "Tasks", 0 sections
  - tab **All**: heading "Tasks", 0 sections; 19 schedule lines, 11 to-dos, 2 site questions, 2 materials
  - tab **Owner: Chen Biron**: heading "Tasks", 0 sections; 10 to-dos, 6 schedule lines, 1 decisions, 1 site questions
  - tab **Due Mon, Sep**: heading "Tasks", 0 sections; 10 to-dos, 6 schedule lines, 1 decisions, 1 site questions
  - tab **Status: Waiting On**: heading "Tasks", 0 sections; 10 to-dos, 6 schedule lines, 1 decisions, 1 site questions
- **Decisions** (`dec`): heading "Decisions", 0.8 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: New Decision
  - lead: "Selections, layouts and sign-offs that block an order or a task. Due dates come from what they block."
  - figures: Blocking Work 3; Past Due 3; With Client 5; Ours to Make 3
  - records: 8 decisions, 6 materials, 3 schedule lines
  - columns: table: DECISION NEEDED, OWED BY, BLOCKS, DUE, STATUS, Detail (8 rows)
  - fields: Search…
  - tab groups: Open / All
  - tab **All**: heading "Decisions", 0 sections; 8 decisions, 6 materials, 3 schedule lines
- **Submittals** (`subm`): heading "Submittals", 0.8 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: New Submittal
  - lead: "What 121 State Street is waiting to see before it orders — dates worked back from the schedule, reviewers in sequence, the order released on approval."
  - figures: Late Submittals 2; With Reviewers 2; Revise and Resubmit 1; Ready to Order 0
  - records: 6 submittals, 1 materials
  - columns: table: NUMBER, SUBMITTAL, SUB OR VENDOR, STATUS, BALL IN COURT, SUBMIT BY, APPROVE BY, ON SITE (6 rows)
  - fields: Search…
  - tab groups: This Project / All Projects; Open / All
  - tab **All Projects**: heading "Submittals", 0 sections; 9 submittals, 1 materials
  - tab **All**: heading "Submittals", 0 sections; 7 submittals, 1 materials
- **Permits** (`insp`): heading "Permits", 1.1 screens tall, 2 sections (1 above the fold), 0 tab screens; blue: New Inspection
  - lead: "Each inspection gates a task; permits carry expirations with a 30-day warning."
  - sections: Permits & Expirations (10); Pull Filings from NYC Open Data
  - figures: Failed 0; Book Now 1; This Week 1; Permits Expiring 1
  - records: 10 inspections, 8 schedule lines, 2 materials
  - columns: table: INSPECTION, AGENCY, REQUEST AFTER, GATES, DATE, STATUS, DETAIL (10 rows); table: PERMIT, AGENCY, NUMBER, ISSUED, EXPIRES, STATUS, DETAIL (2 rows)
  - fields: Search…, e.g. 3001234 or M00123456
  - empty states: "none"
- **Field** (`field`): heading "Field", 1.1 screens tall, 2 sections (1 above the fold), 2 tab screens; blue: New Item
  - lead: "Field questions, plan inconsistencies, revisions and sub coordination — each tied to the task it affects."
  - sections: From the Field (3); Open Items (1)
  - records: 5 schedule lines, 4 site questions, 1 materials, 1 to-dos
  - tab groups: Open Items / Daily Log / Takeoff
  - tab **Daily Log**: heading "Field", 1 sections; 4 schedule lines
  - tab **Takeoff**: heading "Field", 1 sections; 2 materials
- **Photos** (`photos`): heading "Photos", 1.5 screens tall, 0 sections (0 above the fold), 6 tab screens; blue: Add Photos
  - lead: "121 State Street — every photo from the site in one stream: daily logs, progress updates, hidden conditions, drawing questions, deliveries and receipts."
  - records: 2 schedule lines, 1 files
  - fields: Any Date, Any Task, Any Area, Any Trade
  - tab groups: All / Hidden Condition / Daily Log / Progress / Drawing Question / Receipt / Delivery
  - tab **Hidden Condition**: heading "Photos", 0 sections
  - tab **Daily Log**: heading "Photos", 0 sections; 2 schedule lines
  - tab **Progress**: heading "Photos", 0 sections
  - tab **Drawing Question**: heading "Photos", 0 sections
  - tab **Receipt**: heading "Photos", 0 sections
  - tab **Delivery**: heading "Photos", 0 sections; 1 files
- **Deliveries** (`recv`): heading "Deliveries", 0.5 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: Received
  - lead: "Check in what arrived, line by line. Materials on the schedule update themselves."
  - records: 2 purchase orders, 2 files, 1 materials
  - fields: input
- **Materials** (`mat`): heading "Materials", 1.3 screens tall, 1 sections (1 above the fold), 5 tab screens; blue: New Material; 1 save(s) while reading
  - lead: "Need-by and order-by dates follow the schedule. Click a row to edit."
  - sections: Order this week · 3 items · 2 already late
  - figures: Late to Order 3; Order This Week 0; At Risk 5; Not on Site 22
  - records: 25 materials, 17 schedule lines
  - columns: table: MATERIAL, FOR, ORDER BY, ON SITE BY, LEAD, VENDOR, STATUS, FLAG, ETA (24 rows)
  - fields: Search…
  - tab groups: All / Rough / Finish / Not on Site; Flat / By Vendor / By Task
  - tab **Rough**: heading "Materials", 1 sections; 7 schedule lines, 7 materials
  - tab **Finish**: heading "Materials", 1 sections; 21 materials, 14 schedule lines
  - tab **Not on Site**: heading "Materials", 1 sections; 23 materials, 15 schedule lines
  - tab **By Vendor**: heading "Materials", 1 sections; 25 materials, 17 schedule lines
  - tab **By Task**: heading "Materials", 1 sections; 25 materials, 17 schedule lines
- **Costs** (`costs`): heading "Costs", 2.8 screens tall, 4 sections (1 above the fold), 2 tab screens; blue: none
  - lead: "Budget → committed → actual → billed, by cost code. Earned vs. billed tells you whether you're ahead of the client or behind."
  - sections: Line Profitability; By Cost Code; Work in Progress; Recent Job Transactions
  - figures: Billed Ahead +$131K; Margin at Completion 21%; Committed $39K; Bills to Approve $34K
  - records: 4 materials, 1 schedule lines
  - columns: table: LINE, FLAGS, CLIENT PRICE, BUDGET COST, ACTUAL TO DATE, SPENT % OF BUDGET, PROJECTED MARGIN, MARGIN %, BILLED % (17 rows); table: CODE, COST CODE, BUDGET, COMMITTED, ACTUAL, REMAINING, USED (14 rows)
  - tab groups: All Lines / Flagged; Gross / After Overhead
  - tab **Flagged**: heading "Costs", 4 sections; 2 materials, 1 schedule lines
  - tab **After Overhead**: heading "Costs", 4 sections; 4 materials, 1 schedule lines
- **Change Orders** (`billing`): heading "Change Orders", 0.4 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: New Change Order
  - lead: "What is ready to bill, what is drafted, what is sent and what is still owed."
  - records: 2 change orders
  - columns: table: NUMBER, CLIENT, PROJECT, TITLE, DATE, SENT, TOTAL, STATUS (2 rows)
  - fields: bill-client, Search…
  - tab groups: Billing Queue / Progress Billing / Estimates 2 / Change Orders 2 / Invoices 3 / Schedule of Values / Payments 2 / Client Funds
  - tab **Billing Queue**: heading "Billing", 0 sections; 2 invoices
  - tab **Progress Billing**: heading "Billing", 6 sections; 6 schedule lines, 4 materials, 1 change orders
  - tab **Estimates**: heading "Estimates", 0 sections; 2 estimates
  - tab **Invoices**: heading "Billing", 0 sections; 1 invoices
  - tab **Schedule of Values**: heading "Billing", 1 sections
  - tab **Payments**: heading "Billing", 0 sections
  - tab **Client Funds**: heading "Billing", 3 sections; 3 materials
- **Estimates** (`billing`): heading "Estimates", 0.5 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Estimate
  - lead: "What is ready to bill, what is drafted, what is sent and what is still owed."
  - records: 2 estimates
  - columns: table: NUMBER, CLIENT, PROJECT, TITLE, DATE, VALID UNTIL, TOTAL, STATUS (2 rows)
  - fields: bill-client, Search…
  - tab groups: Billing Queue / Progress Billing / Estimates 2 / Change Orders 2 / Invoices 3 / Schedule of Values / Payments 2 / Client Funds
- **Billing** (`billing`): heading "Billing", 0.7 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: Draft $17,080 — 45 Cranberry St
  - lead: "What is ready to bill, what is drafted, what is sent and what is still owed."
  - figures: Ready to Bill $46K; Drafts 0; Sent and Unpaid $92K; Overdue $0
  - records: 2 invoices
  - columns: table: STAGE, WHAT, JOB, AMOUNT, WHERE IT STANDS, NEXT STEP (6 rows)
  - fields: Search…
  - tab groups: Billing Queue / Progress Billing / Estimates 2 / Change Orders 2 / Invoices 3 / Schedule of Values / Payments 2 / Client Funds
- **Documents** (`files`): heading "Documents", 2.1 screens tall, 0 sections (0 above the fold), 10 tab screens; blue: Upload Files
  - lead: "Photos, delivery tickets, inspection cards, receipts, drawings and permits — uploaded from the field or the office, kept with the project, and linked to what th"
  - figures: Added This Week 11; Unfiled 4; Drawings 24; Cards & Permits 0
  - records: 40 files, 24 drawing sheets, 5 submittals, 2 purchase orders, 2 change orders, 1 bills
  - tab groups: All / Photos / Delivery Tickets / Receipts / Inspections & Permits / Drawings & Plans / Other / Contracts / Change Orders / Purchase Orders; Grid / List
  - tab **Photos**: heading "Documents", 0 sections
  - tab **Delivery Tickets**: heading "Documents", 0 sections
  - tab **Receipts**: heading "Documents", 0 sections; 4 files, 1 bills
  - tab **Inspections & Permits**: heading "Documents", 0 sections
  - tab **Drawings & Plans**: heading "Documents", 0 sections; 25 files, 24 drawing sheets
  - tab **Other**: heading "Documents", 0 sections
  - tab **Contracts**: heading "Documents", 0 sections; 1 files
  - tab **Change Orders**: heading "Documents", 0 sections; 2 change orders, 2 files
  - tab **Purchase Orders**: heading "Documents", 0 sections; 4 files, 2 purchase orders
  - tab **List**: heading "Documents", 0 sections; 40 files, 24 drawing sheets, 5 submittals, 2 purchase orders
- **Drawings** (`plans`): heading "Drawings — 121 State Street", 3.1 screens tall, 3 sections (2 above the fold), 0 tab screens; blue: New Revision
  - lead: "The job's drawing register: current sheets only unless you ask for the history. A superseded revision is VOID and opens stamped VOID."
  - sections: Set Check; WHAT THE SETS TEACH; Field Acknowledgments
  - figures: Found Before Work 0; Found in the Field 1; Rework Avoided $0; Our Cost $0; Days to Resolve 3.8; Open Conflicts 0
  - records: 1 schedule lines, 1 subs to confirm, 1 files
  - columns: table: SHEET, TITLE, SET, REV, STATUS, DATE, ISSUED BY, WHAT CHANGED, FIELD (17 rows)
  - fields: Set All Sets Design Presentation LPC DOB, Status Current Sheets All Revisions For 
  - empty states: "No open conflicts between this job's sets."
- **Mail** (`inbox`): heading "Mail", 1.0 screens tall, 2 sections (1 above the fold), 0 tab screens; blue: Review All New
  - lead: "Messages about this project. The assistant classifies each one and proposes updates; a person approves."
  - sections: Documents; Add Messages
  - fields: 9/4/26, 7:41 AM - Alberto: need 20 more , e.g. Maya (architect), Channel
  - empty states: "No deliveries Saturday, board rule. Monday 9am is fine, use the service entrance."

### PM, phone, 121 State Street

The Projects list (rail: Projects 2):
- **Projects** (`ovjobs`): heading "Projects", 1.0 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: New Project; runs past the edge: cut off by pr-m (12 need you: Garden bedroom framing layo, 3 need you: Paint — 3rd floor walls, tri)
  - lead: "Every job, ranked by how much attention it needs today. Open one for its overview."
  - sections: Email
  - figures: Finish Dates Late 0; Jobs Needing You 2; Materials at Risk 1; Billed Ahead +$156K
  - records: 5 schedule lines, 1 decisions, 1 materials
  - columns: table: Project, Client, Health (0–100), Needs You, Completion, Vs Target, Contract, Billed, Owed (4 rows)
  - fields: Search…
  - empty states: "Nothing needs you · Next 9/29 Filing & permits"; "Nothing needs you · Next 9/8 Kitchen option 3 — antique island, sink under arched window"; "Nothing checked yet."
  - a tap on the 121 State Street row opens `dash` on **All projects**, not the job

The sub-tab strip (shown on this screen size): Projects, Overview 12, Project Settings, Schedule, Tasks, Decisions 3, Submittals 2, Permits 1, Field 3, Photos, Deliveries, Materials 5, Costs, Change Orders, Estimates, Billing, Documents, Drawings, Mail.

- **Job Page as it opens (All projects)** (`dash`): heading "Look-Ahead", 4.9 screens tall, 5 sections (0 above the fold), 0 tab screens; blue: none
  - lead: "All projects — what is happening across every job today and what is about to."
  - sections: Needs Attention (4); Pinned Plans (17); Daily Brief; Ahead of Schedule; Since Yesterday (11)
  - figures: Projects 2 of 4 at risk; Profitability 27% margin; Approvals 15 now; Materials 7 at risk; Ready to bill on this job $12,651; Over budget on this job $3,800
  - records: 8 to-dos, 7 schedule lines, 5 materials, 3 files, 3 decisions, 1 purchase orders, 1 bills
  - tab groups: 10 Working Days / 
- **Job Page** (`dash`): heading "Look-Ahead", 4.6 screens tall, 5 sections (0 above the fold), 0 tab screens; blue: none
  - lead: "121 State Street — what is happening on this job today and what is about to."
  - sections: Needs Attention (4); Pinned Plans (17); Daily Brief; Ahead of Schedule; Since Yesterday (6)
  - figures: Schedule At risk; Costs +$131,058 billed ahead; Needs You 12 now; Materials 5 at risk; Ready to bill on this job $12,651; Over budget on this job $3,800
  - records: 10 schedule lines, 8 to-dos, 5 materials, 4 decisions, 3 files, 1 purchase orders, 1 bills
  - tab groups: 10 Working Days / 
- **Project Settings** (`proj`): heading "Project Settings", 2.2 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: none
  - lead: "Dates, address, client, entity, holidays and site hours for this project."
  - sections: Project
  - fields: Name, Address, Target substantial completion, Crew Out (Hard Finish), BIN or job #, LPC-…, Milestone That Marks substantial complet, Holidays (one per line, YYYY-MM-DD, opti, Today (leave blank to use the real date), e.g. Chen, Automation, Site Working Hours
- **Schedule** (`sched`): heading "Schedule", 3.9 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: New Task
  - lead: "Site hours 07:30–16:30, Mon Tue Wed Thu Fri, 30 min lunch (8.5 h/day). All tracks — design, permitting, procurement, construction and closeout share one depende"
  - records: 33 schedule lines, 4 materials, 1 decisions
  - columns: table: Task, Owner, Start, Days (39 rows)
  - fields: Search…
  - tab groups: Gantt / List / Changes
  - tab **Gantt**: heading "Schedule", 0 sections; 18 schedule lines, 3 materials, 1 decisions (runs past the edge: cut off by [object (rect.[object, 9/14))
  - tab **Gantt › Wide**: heading "Schedule", 0 sections; 16 schedule lines, 3 materials, 1 decisions (runs past the edge: cut off by [object (rect.[object, 9/21))
  - tab **Gantt › Day**: heading "Schedule", 0 sections; 25 schedule lines, 3 materials, 1 decisions (runs past the edge: cut off by [object (rect.[object, T))
  - tab **Changes**: heading "Schedule", 1 sections
- **Tasks** (`tasks`): heading "Tasks", 1.3 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: none
  - records: 10 to-dos, 6 schedule lines, 1 decisions, 1 site questions
  - fields: Add a task, Quick add a task
  - tab groups: Due Soon / Waiting / By Status / By Project
  - tab **Waiting**: heading "Tasks", 0 sections; 1 to-dos
  - tab **By Status**: heading "Tasks", 0 sections; 10 to-dos, 6 schedule lines, 1 decisions, 1 site questions
- **Decisions** (`dec`): heading "Decisions", 1.1 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: Decide; runs past the edge: cut off by pr-m (8 days late · Owed by Architect / design, 3 days late · Owed by Architect / design)
  - lead: "Selections, layouts and sign-offs that block an order or a task. Due dates come from what they block."
  - figures: Blocking Work 3; Past Due 3; With Client 5; Ours to Make 3
  - records: 8 decisions, 6 materials, 3 schedule lines
  - columns: table: Decision Needed, Owed By, Blocks, Due, Status, Detail (8 rows)
  - fields: Search…
  - tab groups: Open / All
  - tab **All**: heading "Decisions", 0 sections; 8 decisions, 6 materials, 3 schedule lines (runs past the edge: cut off by pr-m (8 days late · Owed by Architect / design, 3 days late · Owed by Architect / design))
- **Submittals** (`subm`): heading "Submittals", 1.3 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: New Submittal
  - lead: "What 121 State Street is waiting to see before it orders — dates worked back from the schedule, reviewers in sequence, the order released on approval."
  - figures: Late Submittals 2; With Reviewers 2; Revise and Resubmit 1; Ready to Order 0
  - records: 6 submittals, 1 materials
  - tab groups: This Project / All Projects; Open / All
  - tab **All Projects**: heading "Submittals", 0 sections; 9 submittals, 1 materials
  - tab **All**: heading "Submittals", 0 sections; 7 submittals, 1 materials
- **Permits** (`insp`): heading "Permits", 2.0 screens tall, 2 sections (0 above the fold), 0 tab screens; blue: New Inspection; runs past the edge: cut off by pr-m (Rough plumbing · 9/10 · not scheduled · , Punch list, stair runner & final inspect)
  - lead: "Each inspection gates a task; permits carry expirations with a 30-day warning."
  - sections: Permits & Expirations (10); Pull Filings from NYC Open Data
  - figures: Failed 0; Book Now 1; This Week 1; Permits Expiring 1
  - records: 10 inspections, 8 schedule lines, 2 materials
  - columns: table: Inspection, Agency, Request After, Gates, Date, Status, Detail (10 rows); table: Permit, Agency, Number, Issued, Expires, Status, Detail (2 rows)
  - fields: Search…, e.g. 3001234 or M00123456
- **Field** (`field`): heading "Field", 1.4 screens tall, 2 sections (1 above the fold), 2 tab screens; blue: New Item; runs past the edge: cut off by pr-m (Sub No-Show · 121 State Street · Angel ·, Drawing Question · 121 State Street · An)
  - lead: "Field questions, plan inconsistencies, revisions and sub coordination — each tied to the task it affects."
  - sections: From the Field (3); Open Items (1)
  - records: 5 schedule lines, 4 site questions, 1 materials, 1 to-dos
  - tab groups: Open Items / Daily Log / Takeoff
  - tab **Daily Log**: heading "Field", 1 sections; 4 schedule lines
  - tab **Takeoff**: heading "Field", 1 sections; 2 materials (runs past the edge: cut off by [object (path.[object))
- **Photos** (`photos`): heading "Photos", 2.2 screens tall, 0 sections (0 above the fold), 6 tab screens; blue: Add Photos
  - lead: "121 State Street — every photo from the site in one stream: daily logs, progress updates, hidden conditions, drawing questions, deliveries and receipts."
  - records: 2 schedule lines, 1 files
  - fields: Any Date, Any Task, Any Area, Any Trade
  - tab groups: All / Hidden Condition / Daily Log / Progress / Drawing Question / Receipt / Delivery
  - tab **Hidden Condition**: heading "Photos", 0 sections
  - tab **Daily Log**: heading "Photos", 0 sections; 2 schedule lines
  - tab **Progress**: heading "Photos", 0 sections
  - tab **Drawing Question**: heading "Photos", 0 sections
  - tab **Receipt**: heading "Photos", 0 sections
  - tab **Delivery**: heading "Photos", 0 sections; 1 files
- **Deliveries** (`recv`): heading "Deliveries", 0.4 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
  - lead: "Check in what arrived, line by line. Materials on the schedule update themselves."
  - records: 2 purchase orders, 2 files
- **Materials** (`mat`): heading "Materials", 2.9 screens tall, 1 sections (1 above the fold), 5 tab screens; blue: New Material; runs past the edge: cut off by pr-m (Parlor kitchen countertop (template → in, Millwork – parlor kitchen & laundry · 8/)
  - lead: "Need-by and order-by dates follow the schedule. Click a row to edit."
  - sections: Order this week · 3 items · 2 already late
  - figures: Late to Order 3; Order This Week 0; At Risk 5; Not on Site 22
  - records: 25 materials, 17 schedule lines
  - columns: table: Material, For, Order By, On Site By, Lead, Vendor, Status, Flag, ETA (24 rows)
  - fields: Search…
  - tab groups: All / Rough / Finish / Not on Site; Flat / By Vendor / By Task
  - tab **Rough**: heading "Materials", 1 sections; 7 schedule lines, 7 materials
  - tab **Finish**: heading "Materials", 1 sections; 21 materials, 14 schedule lines (runs past the edge: cut off by pr-m (Parlor kitchen countertop (template → in, Millwork – parlor kitchen & laundry · 8/))
  - tab **Not on Site**: heading "Materials", 1 sections; 23 materials, 15 schedule lines (runs past the edge: cut off by pr-m (Parlor kitchen countertop (template → in, Millwork – parlor kitchen & laundry · 8/))
  - tab **By Vendor**: heading "Materials", 1 sections; 25 materials, 17 schedule lines (runs past the edge: cut off by pr-m (Parlor kitchen countertop (template → in, Millwork – parlor kitchen & laundry · 8/))
  - tab **By Task**: heading "Materials", 1 sections; 25 materials, 17 schedule lines (runs past the edge: cut off by pr-m (Parlor kitchen countertop (template → in, Millwork – parlor kitchen & laundry · 8/))
- **Costs** (`costs`): heading "Costs", 4.1 screens tall, 4 sections (1 above the fold), 2 tab screens; blue: none
  - lead: "Budget → committed → actual → billed, by cost code. Earned vs. billed tells you whether you're ahead of the client or behind."
  - sections: Line Profitability; By Cost Code; Work in Progress; Recent Job Transactions
  - figures: Billed Ahead +$131K; Margin at Completion 21%; Committed $39K; Bills to Approve $34K
  - records: 4 materials, 1 schedule lines
  - columns: table: Line, Flags, Client Price, Budget Cost, Actual to Date, Spent % of Budget, Projected Margin, Margin %, Billed % (17 rows); table: Code, Cost Code, Budget, Committed, Actual, Remaining, Used (14 rows)
  - tab groups: All Lines / Flagged; Gross / After Overhead
  - tab **Flagged**: heading "Costs", 4 sections; 2 materials, 1 schedule lines
  - tab **After Overhead**: heading "Costs", 4 sections; 4 materials, 1 schedule lines
- **Change Orders** (`billing`): heading "Change Orders", 0.7 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: New Change Order
  - lead: "What is ready to bill, what is drafted, what is sent and what is still owed."
  - records: 2 change orders
  - columns: table: Number, Client, Project, Title, Date, Sent, Total, Status (2 rows)
  - fields: bill-client, Search…
  - tab groups: Billing Queue / Progress Billing / Estimates 2 / Change Orders 2 / Invoices 3 / Schedule of Values / Payments 2 / Client Funds
  - tab **Billing Queue**: heading "Billing", 0 sections; 2 invoices
  - tab **Progress Billing**: heading "Billing", 6 sections; 4 materials, 1 change orders, 1 schedule lines (runs past the edge: cut off by pr-m (Demolition & disposalContract · 02 · $28, Framing, blocking & rough carpentryContr))
  - tab **Estimates**: heading "Estimates", 0 sections; 2 estimates
  - tab **Invoices**: heading "Billing", 0 sections; 1 invoices
  - tab **Schedule of Values**: heading "Billing", 1 sections
  - tab **Payments**: heading "Billing", 0 sections
  - tab **Client Funds**: heading "Client Funds & Purchasing Obligations", 2 sections; 3 materials
- **Estimates** (`billing`): heading "Estimates", 0.7 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Estimate
  - lead: "What is ready to bill, what is drafted, what is sent and what is still owed."
  - records: 2 estimates
  - columns: table: Number, Client, Project, Title, Date, Valid Until, Total, Status (2 rows)
  - fields: bill-client, Search…
  - tab groups: Billing Queue / Progress Billing / Estimates 2 / Change Orders 2 / Invoices 3 / Schedule of Values / Payments 2 / Client Funds
- **Billing** (`billing`): heading "Billing", 1.1 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: Draft $17,080 — 45 Cranberry St
  - lead: "What is ready to bill, what is drafted, what is sent and what is still owed."
  - figures: Ready to Bill $46K; Drafts 0; Sent and Unpaid $92K; Overdue $0
  - records: 2 invoices
  - columns: table: Stage, What, Job, Amount, Where It Stands, Next Step (6 rows)
  - fields: Search…
  - tab groups: Billing Queue / Progress Billing / Estimates 2 / Change Orders 2 / Invoices 3 / Schedule of Values / Payments 2 / Client Funds
- **Documents** (`files`): heading "Documents", 5.6 screens tall, 0 sections (0 above the fold), 10 tab screens; blue: Upload Files
  - lead: "Photos, delivery tickets, inspection cards, receipts, drawings and permits — uploaded from the field or the office, kept with the project, and linked to what th"
  - figures: Added This Week 11; Unfiled 4; Drawings 24; Cards & Permits 0
  - records: 40 files, 24 drawing sheets, 5 submittals, 2 purchase orders, 2 change orders, 1 bills
  - tab groups: All / Photos / Delivery Tickets / Receipts / Inspections & Permits / Drawings & Plans / Other / Contracts / Change Orders / Purchase Orders; Grid / List
  - tab **Photos**: heading "Documents", 0 sections
  - tab **Delivery Tickets**: heading "Documents", 0 sections
  - tab **Receipts**: heading "Documents", 0 sections; 4 files, 1 bills
  - tab **Inspections & Permits**: heading "Documents", 0 sections
  - tab **Drawings & Plans**: heading "Documents", 0 sections; 25 files, 24 drawing sheets
  - tab **Other**: heading "Documents", 0 sections
  - tab **Contracts**: heading "Documents", 0 sections; 1 files
  - tab **Change Orders**: heading "Documents", 0 sections; 2 change orders, 2 files
  - tab **Purchase Orders**: heading "Documents", 0 sections; 4 files, 2 purchase orders
  - tab **List**: heading "Documents", 0 sections; 40 files, 24 drawing sheets, 4 submittals, 2 purchase orders (runs past the edge: cut off by pr-m (Change order · CO-2026-002 Sand & stain , Submittal · 26 51 00-001 Lighting fixtur))
- **Drawings** (`plans`): heading "Drawings — 121 State Street", 5.8 screens tall, 3 sections (1 above the fold), 0 tab screens; blue: New Revision
  - lead: "The job's drawing register: current sheets only unless you ask for the history. A superseded revision is VOID and opens stamped VOID."
  - sections: Set Check; WHAT THE SETS TEACH; Field Acknowledgments
  - figures: Found Before Work 0; Found in the Field 1; Rework Avoided $0; Our Cost $0; Days to Resolve 3.8; Open Conflicts 0
  - records: 1 schedule lines, 1 subs to confirm, 1 files
  - fields: Set All Sets Design Presentation LPC DOB, Status Current Sheets All Revisions For 
  - empty states: "No open conflicts between this job's sets."
- **Mail** (`inbox`): heading "Mail", 2.1 screens tall, 2 sections (0 above the fold), 0 tab screens; blue: Review All New
  - lead: "Messages about this project. The assistant classifies each one and proposes updates; a person approves."
  - sections: Documents; Add Messages
  - fields: 9/4/26, 7:41 AM - Alberto: need 20 more , e.g. Maya (architect), Channel
  - empty states: "No deliveries Saturday, board rule. Monday 9am is fine, use the service entrance."

### PM, desktop, 45 Cranberry St — design

The sub-tab strip (shown on this screen size): Projects, Overview, Project Settings, Schedule, Tasks 1, Decisions, Submittals, Permits, Field, Photos, Deliveries, Materials, Costs, Change Orders, Estimates, Billing, Documents, Drawings, Mail.

- **Job Page** (`dash`): heading "Overview", 1.8 screens tall, 6 sections (1 above the fold), 0 tab screens; blue: none
  - lead: "45 Cranberry St — what is happening on this job today and what is about to."
  - sections: Look-Ahead; Needs Attention (0); Pinned Plans (6); Daily Brief; Ahead of Schedule; Since Yesterday (2)
  - figures: Schedule On target; Costs +$2,705 billed ahead; Needs You Nothing; Materials All on site; Ready to bill on this job $23,366
  - records: 4 to-dos, 3 schedule lines
  - tab groups: 10 Working Days / 
- **Project Settings** (`proj`): heading "Project Settings", 1.5 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: none
  - lead: "Dates, address, client, entity, holidays and site hours for this project."
  - sections: Project
  - fields: Name, Address, Target substantial completion, Crew Out (Hard Finish), BIN or job #, LPC-…, Milestone That Marks substantial complet, Holidays (one per line, YYYY-MM-DD, opti, Today (leave blank to use the real date), e.g. Chen, Automation, Site Working Hours
- **Schedule** (`sched`): heading "Schedule", 0.8 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: New Task
  - lead: "Site hours 07:30–16:30, Mon Tue Wed Thu Fri, 30 min lunch (8.5 h/day). All tracks — design, permitting, procurement, construction and closeout share one depende"
  - records: 5 schedule lines
  - tab groups: Gantt / List / Changes; Fit / Wide / Day
  - tab **List**: heading "Schedule", 0 sections; 5 schedule lines
  - tab **Changes**: heading "Schedule", 1 sections
  - tab **Wide**: heading "Schedule", 0 sections; 5 schedule lines
  - tab **Day**: heading "Schedule", 0 sections; 5 schedule lines
- **Tasks** (`tasks`): heading "Tasks", 0.4 screens tall, 0 sections (0 above the fold), 15 tab screens; blue: New Task
  - lead: "6 open on 45 Cranberry St · 1 overdue — to-dos, schedule lines and field items with a name on them"
  - records: 4 to-dos, 1 schedule lines
  - fields: Search tasks, How the list is grouped, Quick add a task
  - tab groups: List / Table / Board / Calendar; Mine / Team / Everyone / Unassigned; Due Soon / Today / Overdue / No Date / Waiting / Later / Done / All
  - tab **Table**: heading "Tasks", 0 sections; 4 to-dos, 1 schedule lines
  - tab **Table › Owner**: heading "Tasks", 0 sections; 4 to-dos, 1 schedule lines
  - tab **Table › Status**: heading "Tasks", 0 sections; 4 to-dos, 1 schedule lines
  - tab **Board**: heading "Tasks", 0 sections; 4 to-dos, 1 schedule lines
  - tab **Calendar**: heading "Tasks", 0 sections; 4 to-dos, 1 schedule lines
  - tab **Calendar › Week**: heading "Tasks", 0 sections; 4 to-dos, 1 schedule lines
  - tab **Mine**: heading "Tasks", 0 sections
  - tab **Team**: heading "Tasks", 0 sections; 4 to-dos, 1 schedule lines
  - tab **Unassigned**: heading "Tasks", 0 sections
  - tab **Today**: heading "Tasks", 0 sections; 1 schedule lines
  - tab **Overdue**: heading "Tasks", 0 sections; 1 schedule lines
  - tab **No Date**: heading "Tasks", 0 sections
  - tab **Waiting**: heading "Tasks", 0 sections
  - tab **Later**: heading "Tasks", 0 sections
  - tab **All**: heading "Tasks", 0 sections; 5 schedule lines, 4 to-dos
- **Decisions** (`dec`): heading "Decisions", 0.4 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: New Decision
  - lead: "Selections, layouts and sign-offs that block an order or a task. Due dates come from what they block."
  - fields: Search…
  - empty states: "All clear blocking work · past due · with client · ours to make — nothing needs you here"; "No open decisions. Every order and task has what it needs."
  - tab groups: Open / All
  - tab **All**: heading "Decisions", 0 sections
- **Submittals** (`subm`): heading "Submittals", 0.6 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: New Submittal
  - lead: "What 45 Cranberry St is waiting to see before it orders — dates worked back from the schedule, reviewers in sequence, the order released on approval."
  - figures: Late Submittals 0; With Reviewers 2; Revise and Resubmit 0; Ready to Order 0
  - records: 3 submittals
  - columns: table: NUMBER, SUBMITTAL, SUB OR VENDOR, STATUS, BALL IN COURT, SUBMIT BY, APPROVE BY, ON SITE (3 rows)
  - fields: Search…
  - tab groups: This Project / All Projects; Open / All
  - tab **All Projects**: heading "Submittals", 0 sections; 9 submittals, 1 materials
  - tab **All**: heading "Submittals", 0 sections; 3 submittals
- **Permits** (`insp`): heading "Permits", 0.6 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: New Inspection
  - lead: "Each inspection gates a task; permits carry expirations with a 30-day warning."
  - sections: Permits & Expirations (0); Pull Filings from NYC Open Data
  - records: 1 schedule lines
  - columns: table: PERMIT, AGENCY, NUMBER, ISSUED, EXPIRES, STATUS, DETAIL (1 rows)
  - fields: Search…, e.g. 3001234 or M00123456
  - empty states: "All clear failed · book now · this week · permits expiring — nothing needs you here"; "No inspections yet."
- **Field** (`field`): heading "Field", 0.5 screens tall, 2 sections (2 above the fold), 2 tab screens; blue: New Item
  - lead: "Field questions, plan inconsistencies, revisions and sub coordination — each tied to the task it affects."
  - sections: From the Field; Open Items (0)
  - empty states: "nothing waiting on an answer"; "No open field items. Add one when the plans and the building disagree, and it is tied to the task it"
  - tab groups: Open Items / Daily Log / Takeoff
  - tab **Daily Log**: heading "Field", 1 sections
  - tab **Takeoff**: heading "Field", 1 sections
- **Photos** (`photos`): heading "Photos", 0.9 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: Add Photos
  - lead: "45 Cranberry St — every photo from the site in one stream: daily logs, progress updates, hidden conditions, drawing questions, deliveries and receipts."
  - fields: Any Date, Any Task, Any Area, Any Trade
  - tab groups: All / Site Visit
  - tab **Site Visit**: heading "Photos", 0 sections
- **Deliveries** (`recv`): heading "Deliveries", 0.2 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none; nearly empty (22 words)
  - lead: "Check in what arrived, line by line. Materials on the schedule update themselves."
  - empty states: "Nothing on order for this job."
- **Materials** (`mat`): heading "Materials", 0.4 screens tall, 0 sections (0 above the fold), 5 tab screens; blue: New Material
  - lead: "Need-by and order-by dates follow the schedule. Click a row to edit."
  - fields: Search…
  - empty states: "All clear late to order · order this week · at risk · not on site — nothing needs you here"; "No materials match this filter."
  - tab groups: All / Rough / Finish / Not on Site; Flat / By Vendor / By Task
  - tab **Rough**: heading "Materials", 0 sections
  - tab **Finish**: heading "Materials", 0 sections
  - tab **Not on Site**: heading "Materials", 0 sections
  - tab **By Vendor**: heading "Materials", 0 sections
  - tab **By Task**: heading "Materials", 0 sections
- **Costs** (`costs`): heading "Costs", 1.4 screens tall, 4 sections (1 above the fold), 2 tab screens; blue: none
  - lead: "Budget → committed → actual → billed, by cost code. Earned vs. billed tells you whether you're ahead of the client or behind."
  - sections: Line Profitability; By Cost Code; Work in Progress; Recent Job Transactions
  - figures: Billed Ahead +$3K; Margin at Completion 62%; Committed $0; Bills to Approve $0
  - records: 4 schedule lines
  - columns: table: LINE, FLAGS, CLIENT PRICE, BUDGET COST, ACTUAL TO DATE, SPENT % OF BUDGET, PROJECTED MARGIN, MARGIN %, BILLED % (6 rows); table: CODE, COST CODE, BUDGET, COMMITTED, ACTUAL, REMAINING, USED (3 rows)
  - empty states: "No transactions assigned to this job yet."
  - tab groups: All Lines / Flagged; Gross / After Overhead
  - tab **Flagged**: heading "Costs", 4 sections
  - tab **After Overhead**: heading "Costs", 4 sections; 4 schedule lines
- **Change Orders** (`billing`): heading "Change Orders", 0.4 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: New Change Order
  - lead: "What is ready to bill, what is drafted, what is sent and what is still owed."
  - fields: bill-client, Search…
  - empty states: "No change orders yet."
  - tab groups: Billing Queue / Progress Billing / Estimates 1 / Change Orders / Invoices 2 / Schedule of Values / Payments 2 / Client Funds
  - tab **Billing Queue**: heading "Billing", 0 sections; 2 invoices
  - tab **Progress Billing**: heading "Billing", 6 sections; 10 schedule lines, 4 materials, 1 change orders
  - tab **Estimates**: heading "Estimates", 0 sections; 1 estimates
  - tab **Invoices**: heading "Billing", 0 sections
  - tab **Schedule of Values**: heading "Billing", 1 sections
  - tab **Payments**: heading "Billing", 1 sections
  - tab **Client Funds**: heading "Billing", 3 sections; 3 materials
- **Estimates** (`billing`): heading "Estimates", 0.4 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Estimate
  - lead: "What is ready to bill, what is drafted, what is sent and what is still owed."
  - records: 1 estimates
  - columns: table: NUMBER, CLIENT, PROJECT, TITLE, DATE, VALID UNTIL, TOTAL, STATUS (1 rows)
  - fields: bill-client, Search…
  - tab groups: Billing Queue / Progress Billing / Estimates 1 / Change Orders / Invoices 2 / Schedule of Values / Payments 2 / Client Funds
- **Billing** (`billing`): heading "Billing", 0.7 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: Draft $17,080 — 45 Cranberry St
  - lead: "What is ready to bill, what is drafted, what is sent and what is still owed."
  - figures: Ready to Bill $46K; Drafts 0; Sent and Unpaid $92K; Overdue $0
  - records: 2 invoices
  - columns: table: STAGE, WHAT, JOB, AMOUNT, WHERE IT STANDS, NEXT STEP (6 rows)
  - fields: Search…
  - tab groups: Billing Queue / Progress Billing / Estimates 1 / Change Orders / Invoices 2 / Schedule of Values / Payments 2 / Client Funds
- **Documents** (`files`): heading "Documents", 0.7 screens tall, 0 sections (0 above the fold), 10 tab screens; blue: Upload Files
  - lead: "Photos, delivery tickets, inspection cards, receipts, drawings and permits — uploaded from the field or the office, kept with the project, and linked to what th"
  - figures: Added This Week 1; Unfiled 0; Drawings 0; Cards & Permits 0
  - records: 3 files, 2 submittals
  - tab groups: All / Photos / Delivery Tickets / Receipts / Inspections & Permits / Drawings & Plans / Other / Contracts / Change Orders / Purchase Orders; Grid / List
  - tab **Photos**: heading "Documents", 0 sections
  - tab **Delivery Tickets**: heading "Documents", 0 sections
  - tab **Receipts**: heading "Documents", 0 sections
  - tab **Inspections & Permits**: heading "Documents", 0 sections
  - tab **Drawings & Plans**: heading "Documents", 0 sections
  - tab **Other**: heading "Documents", 0 sections
  - tab **Contracts**: heading "Documents", 0 sections; 1 files
  - tab **Change Orders**: heading "Documents", 0 sections
  - tab **Purchase Orders**: heading "Documents", 0 sections
  - tab **List**: heading "Documents", 0 sections; 3 files, 2 submittals
- **Drawings** (`plans`): heading "Drawings — 45 Cranberry St", 1.5 screens tall, 5 sections (2 above the fold), 0 tab screens; blue: New Revision
  - lead: "The job's drawing register: current sheets only unless you ask for the history. A superseded revision is VOID and opens stamped VOID."
  - sections: Set Check; WHAT THE SETS TEACH; Field Acknowledgments; Change Records (9); Transmittals (9)
  - figures: Found Before Work 2; Found in the Field 0; Rework Avoided $4,200; Our Cost $0; Days to Resolve 1.6; Open Conflicts 0
  - records: 6 drawing sheets, 1 schedule lines
  - columns: table: SHEET, TITLE, SET, REV, STATUS, DATE, ISSUED BY, WHAT CHANGED, FIELD (6 rows)
  - fields: Set All Sets LPC DOB Construction Docume, Status Current Sheets All Revisions For 
  - empty states: "No open conflicts between this job's sets."
- **Mail** (`inbox`): heading "Mail", 0.6 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: Review All New
  - lead: "Messages about this project. The assistant classifies each one and proposes updates; a person approves."
  - sections: Documents; Add Messages
  - fields: 9/4/26, 7:41 AM - Alberto: need 20 more , e.g. Maya (architect), Channel
  - empty states: "No messages routed to 45 Cranberry St — design yet. Mail, texts and calls that name this job land he"; "No messages routed to 45 Cranberry St — design yet. Mail, texts and calls that name this job land he"

### PM, phone, 45 Cranberry St — design

The sub-tab strip (shown on this screen size): Projects, Overview, Project Settings, Schedule, Tasks 1, Decisions, Submittals, Permits, Field, Photos, Deliveries, Materials, Costs, Change Orders, Estimates, Billing, Documents, Drawings, Mail.

- **Job Page** (`dash`): heading "Look-Ahead", 2.5 screens tall, 5 sections (0 above the fold), 0 tab screens; blue: none
- **Project Settings** (`proj`): heading "Project Settings", 2.2 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: none
- **Schedule** (`sched`): heading "Schedule", 1.2 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: New Task
- **Tasks** (`tasks`): heading "Tasks", 1.0 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none; runs past the edge: cut off by tk2-sub (Tomorrow)
- **Decisions** (`dec`): heading "Decisions", 0.6 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: none
- **Submittals** (`subm`): heading "Submittals", 0.9 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: New Submittal
- **Permits** (`insp`): heading "Permits", 1.1 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: New Inspection
- **Field** (`field`): heading "Field", 0.8 screens tall, 2 sections (2 above the fold), 2 tab screens; blue: New Item
- **Photos** (`photos`): heading "Photos", 1.5 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: Add Photos
- **Deliveries** (`recv`): heading "Deliveries", 0.3 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none; nearly empty (8 words)
- **Materials** (`mat`): heading "Materials", 0.7 screens tall, 0 sections (0 above the fold), 5 tab screens; blue: New Material
- **Costs** (`costs`): heading "Costs", 1.9 screens tall, 4 sections (1 above the fold), 2 tab screens; blue: none
- **Change Orders** (`billing`): heading "Change Orders", 0.6 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: New Change Order
- **Estimates** (`billing`): heading "Estimates", 0.6 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Estimate
- **Billing** (`billing`): heading "Billing", 1.1 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: Draft $17,080 — 45 Cranberry St
- **Documents** (`files`): heading "Documents", 1.0 screens tall, 0 sections (0 above the fold), 10 tab screens; blue: Upload Files
- **Drawings** (`plans`): heading "Drawings — 45 Cranberry St", 3.5 screens tall, 5 sections (1 above the fold), 0 tab screens; blue: New Revision
- **Mail** (`inbox`): heading "Mail", 1.1 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: Review All New

## 9. The Other Roles, One Line a Page

### Owner, desktop, 121 State Street

Strip (shown): Projects, Overview 12, Project Settings, Schedule, Tasks, Decisions 3, Submittals 2, Permits 1, Field 3, Photos, Deliveries, Materials 5, Costs, Change Orders, Estimates, Documents, Drawings, Mail.

- **Job Page** (`dash`): heading "Overview", 3.7 screens tall, 6 sections (1 above the fold), 0 tab screens; blue: none
- **Project Settings** (`proj`): heading "Project Settings", 1.5 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: none
- **Schedule** (`sched`): heading "Schedule", 1.9 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: New Task
- **Tasks** (`tasks`): heading "Tasks", 1.1 screens tall, 0 sections (0 above the fold), 18 tab screens; blue: New Task
- **Decisions** (`dec`): heading "Decisions", 0.8 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: New Decision
- **Submittals** (`subm`): heading "Submittals", 0.8 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: New Submittal
- **Permits** (`insp`): heading "Permits", 1.1 screens tall, 2 sections (1 above the fold), 0 tab screens; blue: New Inspection
- **Field** (`field`): heading "Field", 1.1 screens tall, 2 sections (1 above the fold), 2 tab screens; blue: New Item
- **Photos** (`photos`): heading "Photos", 1.5 screens tall, 0 sections (0 above the fold), 6 tab screens; blue: Add Photos
- **Deliveries** (`recv`): heading "Deliveries", 0.5 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: Received
- **Materials** (`mat`): heading "Materials", 1.3 screens tall, 1 sections (1 above the fold), 5 tab screens; blue: New Material
- **Costs** (`costs`): heading "Costs", 2.8 screens tall, 4 sections (1 above the fold), 2 tab screens; blue: none
- **Change Orders** (`billing`): heading "Change Orders", 0.4 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: New Change Order
- **Estimates** (`billing`): heading "Estimates", 0.5 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Estimate
- **Documents** (`files`): heading "Documents", 2.1 screens tall, 0 sections (0 above the fold), 10 tab screens; blue: Upload Files
- **Drawings** (`plans`): heading "Drawings — 121 State Street", 3.1 screens tall, 3 sections (2 above the fold), 0 tab screens; blue: New Revision
- **Mail** (`inbox`): heading "Mail", 1.0 screens tall, 2 sections (1 above the fold), 0 tab screens; blue: Review All New

### Owner, desktop, 45 Cranberry St — design

Strip (shown): Projects, Overview, Project Settings, Schedule, Tasks 1, Decisions, Submittals, Permits, Field, Photos, Deliveries, Materials, Costs, Change Orders, Estimates, Documents, Drawings, Mail.

- **Job Page** (`dash`): heading "Overview", 1.8 screens tall, 6 sections (1 above the fold), 0 tab screens; blue: none
- **Project Settings** (`proj`): heading "Project Settings", 1.5 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: none
- **Schedule** (`sched`): heading "Schedule", 0.8 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: New Task
- **Tasks** (`tasks`): heading "Tasks", 0.4 screens tall, 0 sections (0 above the fold), 15 tab screens; blue: New Task
- **Decisions** (`dec`): heading "Decisions", 0.4 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: New Decision
- **Submittals** (`subm`): heading "Submittals", 0.6 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: New Submittal
- **Permits** (`insp`): heading "Permits", 0.6 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: New Inspection
- **Field** (`field`): heading "Field", 0.5 screens tall, 2 sections (2 above the fold), 2 tab screens; blue: New Item
- **Photos** (`photos`): heading "Photos", 0.9 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: Add Photos
- **Deliveries** (`recv`): heading "Deliveries", 0.2 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none; nearly empty (22 words)
- **Materials** (`mat`): heading "Materials", 0.4 screens tall, 0 sections (0 above the fold), 5 tab screens; blue: New Material
- **Costs** (`costs`): heading "Costs", 1.4 screens tall, 4 sections (1 above the fold), 2 tab screens; blue: none
- **Change Orders** (`billing`): heading "Change Orders", 0.4 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: New Change Order
- **Estimates** (`billing`): heading "Estimates", 0.4 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Estimate
- **Documents** (`files`): heading "Documents", 0.7 screens tall, 0 sections (0 above the fold), 10 tab screens; blue: Upload Files
- **Drawings** (`plans`): heading "Drawings — 45 Cranberry St", 1.5 screens tall, 5 sections (2 above the fold), 0 tab screens; blue: New Revision
- **Mail** (`inbox`): heading "Mail", 0.6 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: Review All New

### Owner, phone, 121 State Street

Strip (shown): Projects, Overview 12, Project Settings, Schedule, Tasks, Decisions 3, Submittals 2, Permits 1, Field 3, Photos, Deliveries, Materials 5, Costs, Change Orders, Estimates, Documents, Drawings, Mail.

- **Job Page as it opens (All projects)** (`dash`): heading "Look-Ahead", 5.2 screens tall, 5 sections (0 above the fold), 0 tab screens; blue: none
- **Job Page** (`dash`): heading "Look-Ahead", 4.6 screens tall, 5 sections (0 above the fold), 0 tab screens; blue: none
- **Project Settings** (`proj`): heading "Project Settings", 2.2 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: none
- **Schedule** (`sched`): heading "Schedule", 3.9 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: New Task
- **Tasks** (`tasks`): heading "Tasks", 1.3 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- **Decisions** (`dec`): heading "Decisions", 1.1 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: Decide; runs past the edge: cut off by pr-m (8 days late · Owed by Architect / design, 3 days late · Owed by Architect / design)
- **Submittals** (`subm`): heading "Submittals", 1.3 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: New Submittal
- **Permits** (`insp`): heading "Permits", 2.0 screens tall, 2 sections (0 above the fold), 0 tab screens; blue: New Inspection; runs past the edge: cut off by pr-m (Rough plumbing · 9/10 · not scheduled · , Punch list, stair runner & final inspect)
- **Field** (`field`): heading "Field", 1.4 screens tall, 2 sections (1 above the fold), 2 tab screens; blue: New Item; runs past the edge: cut off by pr-m (Drawing Question · 121 State Street · An, I Need Something · 121 State Street · An)
- **Photos** (`photos`): heading "Photos", 2.2 screens tall, 0 sections (0 above the fold), 6 tab screens; blue: Add Photos
- **Deliveries** (`recv`): heading "Deliveries", 0.4 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- **Materials** (`mat`): heading "Materials", 2.9 screens tall, 1 sections (1 above the fold), 5 tab screens; blue: New Material; runs past the edge: cut off by pr-m (Parlor kitchen countertop (template → in, Millwork – parlor kitchen & laundry · 8/)
- **Costs** (`costs`): heading "Costs", 4.1 screens tall, 4 sections (1 above the fold), 2 tab screens; blue: none
- **Change Orders** (`billing`): heading "Change Orders", 0.7 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: New Change Order
- **Estimates** (`billing`): heading "Estimates", 0.7 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Estimate
- **Documents** (`files`): heading "Documents", 5.5 screens tall, 0 sections (0 above the fold), 10 tab screens; blue: Upload Files
- **Drawings** (`plans`): heading "Drawings — 121 State Street", 5.8 screens tall, 3 sections (1 above the fold), 0 tab screens; blue: New Revision
- **Mail** (`inbox`): heading "Mail", 2.1 screens tall, 2 sections (0 above the fold), 0 tab screens; blue: Review All New

### Owner, phone, 45 Cranberry St — design

Strip (shown): Projects, Overview, Project Settings, Schedule, Tasks 1, Decisions, Submittals, Permits, Field, Photos, Deliveries, Materials, Costs, Change Orders, Estimates, Documents, Drawings, Mail.

- **Job Page** (`dash`): heading "Look-Ahead", 2.8 screens tall, 5 sections (0 above the fold), 0 tab screens; blue: none
- **Project Settings** (`proj`): heading "Project Settings", 2.2 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: none
- **Schedule** (`sched`): heading "Schedule", 1.2 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: New Task
- **Tasks** (`tasks`): heading "Tasks", 1.0 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none; runs past the edge: cut off by tk2-sub (Tomorrow)
- **Decisions** (`dec`): heading "Decisions", 0.6 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: none
- **Submittals** (`subm`): heading "Submittals", 0.9 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: New Submittal
- **Permits** (`insp`): heading "Permits", 1.1 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: New Inspection
- **Field** (`field`): heading "Field", 0.8 screens tall, 2 sections (2 above the fold), 2 tab screens; blue: New Item
- **Photos** (`photos`): heading "Photos", 1.5 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: Add Photos
- **Deliveries** (`recv`): heading "Deliveries", 0.3 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none; nearly empty (8 words)
- **Materials** (`mat`): heading "Materials", 0.7 screens tall, 0 sections (0 above the fold), 5 tab screens; blue: New Material
- **Costs** (`costs`): heading "Costs", 1.9 screens tall, 4 sections (1 above the fold), 2 tab screens; blue: none
- **Change Orders** (`billing`): heading "Change Orders", 0.6 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: New Change Order
- **Estimates** (`billing`): heading "Estimates", 0.6 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Estimate
- **Documents** (`files`): heading "Documents", 1.0 screens tall, 0 sections (0 above the fold), 10 tab screens; blue: Upload Files
- **Drawings** (`plans`): heading "Drawings — 45 Cranberry St", 3.5 screens tall, 5 sections (1 above the fold), 0 tab screens; blue: New Revision
- **Mail** (`inbox`): heading "Mail", 1.1 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: Review All New

### Coordinator (Chen), desktop, 121 State Street

Strip (shown): Projects, Overview 12, Project Settings, Schedule, Tasks, Decisions 3, Submittals 2, Permits 1, Field 3, Photos, Deliveries, Materials 5, Documents, Drawings, Mail.

- **Job Page** (`dash`): heading "Overview", 3.6 screens tall, 6 sections (1 above the fold), 0 tab screens; blue: none
- **Project Settings** (`proj`): heading "Project Settings", 1.5 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: none
- **Schedule** (`sched`): heading "Schedule", 1.9 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: New Task
- **Tasks** (`tasks`): heading "Tasks", 1.1 screens tall, 0 sections (0 above the fold), 17 tab screens; blue: New Task
- **Decisions** (`dec`): heading "Decisions", 0.8 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: New Decision
- **Submittals** (`subm`): heading "Submittals", 0.8 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: New Submittal
- **Permits** (`insp`): heading "Permits", 1.1 screens tall, 2 sections (1 above the fold), 0 tab screens; blue: New Inspection
- **Field** (`field`): heading "Field", 1.1 screens tall, 2 sections (1 above the fold), 2 tab screens; blue: New Item
- **Photos** (`photos`): heading "Photos", 1.5 screens tall, 0 sections (0 above the fold), 6 tab screens; blue: Add Photos
- **Deliveries** (`recv`): heading "Deliveries", 0.5 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: Received
- **Materials** (`mat`): heading "Materials", 1.3 screens tall, 1 sections (1 above the fold), 5 tab screens; blue: New Material
- **Documents** (`files`): heading "Documents", 2.1 screens tall, 0 sections (0 above the fold), 10 tab screens; blue: Upload Files
- **Drawings** (`plans`): heading "Drawings — 121 State Street", 2.8 screens tall, 3 sections (2 above the fold), 0 tab screens; blue: none
- **Mail** (`inbox`): heading "Mail", 1.0 screens tall, 2 sections (1 above the fold), 0 tab screens; blue: Review All New

### Coordinator (Chen), desktop, 45 Cranberry St — design

Strip (shown): Projects, Overview, Project Settings, Schedule, Tasks 1, Decisions, Submittals, Permits, Field, Photos, Deliveries, Materials, Documents, Drawings, Mail.

- **Job Page** (`dash`): heading "Overview", 1.8 screens tall, 6 sections (1 above the fold), 0 tab screens; blue: none
- **Project Settings** (`proj`): heading "Project Settings", 1.5 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: none
- **Schedule** (`sched`): heading "Schedule", 0.8 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: New Task
- **Tasks** (`tasks`): heading "Tasks", 0.4 screens tall, 0 sections (0 above the fold), 14 tab screens; blue: New Task
- **Decisions** (`dec`): heading "Decisions", 0.4 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: New Decision
- **Submittals** (`subm`): heading "Submittals", 0.6 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: New Submittal
- **Permits** (`insp`): heading "Permits", 0.6 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: New Inspection
- **Field** (`field`): heading "Field", 0.5 screens tall, 2 sections (2 above the fold), 2 tab screens; blue: New Item
- **Photos** (`photos`): heading "Photos", 0.9 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: Add Photos
- **Deliveries** (`recv`): heading "Deliveries", 0.2 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none; nearly empty (22 words)
- **Materials** (`mat`): heading "Materials", 0.4 screens tall, 0 sections (0 above the fold), 5 tab screens; blue: New Material
- **Documents** (`files`): heading "Documents", 0.7 screens tall, 0 sections (0 above the fold), 10 tab screens; blue: Upload Files
- **Drawings** (`plans`): heading "Drawings — 45 Cranberry St", 1.5 screens tall, 5 sections (2 above the fold), 0 tab screens; blue: none
- **Mail** (`inbox`): heading "Mail", 0.6 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: Review All New

### Coordinator (Chen), phone, 121 State Street

Strip (shown): Projects, Overview 12, Project Settings, Schedule, Tasks, Decisions 3, Submittals 2, Permits 1, Field 3, Photos, Deliveries, Materials 5, Documents, Drawings, Mail.

- **Job Page as it opens (All projects)** (`dash`): heading "Look-Ahead", 4.8 screens tall, 5 sections (0 above the fold), 0 tab screens; blue: none
- **Job Page** (`dash`): heading "Look-Ahead", 4.4 screens tall, 5 sections (0 above the fold), 0 tab screens; blue: none
- **Project Settings** (`proj`): heading "Project Settings", 2.2 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: none
- **Schedule** (`sched`): heading "Schedule", 3.9 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: New Task
- **Tasks** (`tasks`): heading "Tasks", 1.3 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- **Decisions** (`dec`): heading "Decisions", 1.1 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: Decide; runs past the edge: cut off by pr-m (8 days late · Owed by Architect / design, 3 days late · Owed by Architect / design)
- **Submittals** (`subm`): heading "Submittals", 1.3 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: New Submittal
- **Permits** (`insp`): heading "Permits", 2.0 screens tall, 2 sections (0 above the fold), 0 tab screens; blue: New Inspection; runs past the edge: cut off by pr-m (Rough plumbing · 9/10 · not scheduled · , Punch list, stair runner & final inspect)
- **Field** (`field`): heading "Field", 1.3 screens tall, 2 sections (1 above the fold), 2 tab screens; blue: New Item; runs past the edge: cut off by pr-m (I Need Something · 121 State Street · An, Drawing Question · 121 State Street · An)
- **Photos** (`photos`): heading "Photos", 2.2 screens tall, 0 sections (0 above the fold), 6 tab screens; blue: Add Photos
- **Deliveries** (`recv`): heading "Deliveries", 0.4 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- **Materials** (`mat`): heading "Materials", 2.9 screens tall, 1 sections (1 above the fold), 5 tab screens; blue: New Material; runs past the edge: cut off by pr-m (Parlor kitchen countertop (template → in, Millwork – parlor kitchen & laundry · 8/)
- **Documents** (`files`): heading "Documents", 5.5 screens tall, 0 sections (0 above the fold), 10 tab screens; blue: Upload Files
- **Drawings** (`plans`): heading "Drawings — 121 State Street", 5.7 screens tall, 3 sections (1 above the fold), 0 tab screens; blue: none
- **Mail** (`inbox`): heading "Mail", 2.1 screens tall, 2 sections (0 above the fold), 0 tab screens; blue: Review All New

### Coordinator (Chen), phone, 45 Cranberry St — design

Strip (shown): Projects, Overview, Project Settings, Schedule, Tasks 1, Decisions, Submittals, Permits, Field, Photos, Deliveries, Materials, Documents, Drawings, Mail.

- **Job Page** (`dash`): heading "Look-Ahead", 2.5 screens tall, 5 sections (0 above the fold), 0 tab screens; blue: none
- **Project Settings** (`proj`): heading "Project Settings", 2.2 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: none
- **Schedule** (`sched`): heading "Schedule", 1.2 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: New Task
- **Tasks** (`tasks`): heading "Tasks", 1.0 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none; runs past the edge: cut off by tk2-sub (Tomorrow)
- **Decisions** (`dec`): heading "Decisions", 0.6 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: none
- **Submittals** (`subm`): heading "Submittals", 0.9 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: New Submittal
- **Permits** (`insp`): heading "Permits", 1.1 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: New Inspection
- **Field** (`field`): heading "Field", 0.8 screens tall, 2 sections (2 above the fold), 2 tab screens; blue: New Item
- **Photos** (`photos`): heading "Photos", 1.5 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: Add Photos
- **Deliveries** (`recv`): heading "Deliveries", 0.3 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none; nearly empty (8 words)
- **Materials** (`mat`): heading "Materials", 0.7 screens tall, 0 sections (0 above the fold), 5 tab screens; blue: New Material
- **Documents** (`files`): heading "Documents", 1.0 screens tall, 0 sections (0 above the fold), 10 tab screens; blue: Upload Files
- **Drawings** (`plans`): heading "Drawings — 45 Cranberry St", 3.4 screens tall, 5 sections (1 above the fold), 0 tab screens; blue: none
- **Mail** (`inbox`): heading "Mail", 1.1 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: Review All New

### Foreman (Angel), desktop, 121 State Street

- **Job Page** (`fsite`): heading "Site", 3.3 screens tall, 4 sections (1 above the fold), 0 tab screens; blue: none
- **Daily Log** (`flog`): heading "Daily Log", 1.4 screens tall, 3 sections (3 above the fold), 6 tab screens; blue: Next
- **Requests** (`req`): heading "Requests", 0.8 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: Send the Request
- **Crew** (`fcrew`): heading "Crew", 1.3 screens tall, 4 sections (3 above the fold), 0 tab screens; blue: Approve 2 Clean
- **Drawings** (`plans`): heading "Drawings — 121 State Street", 2.8 screens tall, 3 sections (2 above the fold), 0 tab screens; blue: none
- **Schedule** (`sched`): heading "Schedule", 1.0 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: none
- **Photos** (`photos`): heading "Photos", 1.5 screens tall, 0 sections (0 above the fold), 6 tab screens; blue: Add Photos
- **Documents** (`files`): heading "Documents", 1.9 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: Upload Files

### Foreman (Angel), desktop, 45 Cranberry St — design

- **Job Page** (`fsite`): heading "Site", 0.8 screens tall, 4 sections (4 above the fold), 0 tab screens; blue: none
- **Daily Log** (`flog`): heading "Daily Log", 0.8 screens tall, 3 sections (3 above the fold), 6 tab screens; blue: Next
- **Requests** (`req`): heading "Requests", 0.6 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: Send the Request
- **Crew** (`fcrew`): heading "Crew", 1.1 screens tall, 4 sections (4 above the fold), 0 tab screens; blue: Log Toolbox Talk
- **Drawings** (`plans`): heading "Drawings — 45 Cranberry St", 1.5 screens tall, 5 sections (2 above the fold), 0 tab screens; blue: none
- **Schedule** (`sched`): heading "Schedule", 0.3 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: none
- **Photos** (`photos`): heading "Photos", 0.9 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: Add Photos
- **Documents** (`files`): heading "Documents", 0.7 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: Upload Files

### Foreman (Angel), phone, 121 State Street

- **Job Page** (`fsite`): heading "Site", 3.5 screens tall, 4 sections (1 above the fold), 0 tab screens; blue: none; runs past the edge: cut off by pr-m (DOB · call by Wed, Sep 2 · gates Rough p, DOB · scheduled Tue, Sep 8 · gates Rough)
- **Daily Log** (`flog`): heading "Daily Log", 2.1 screens tall, 3 sections (3 above the fold), 6 tab screens; blue: Next
- **Requests** (`req`): heading "Requests", 1.1 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: Send the Request
- **Crew** (`fcrew`): heading "Crew", 2.0 screens tall, 4 sections (2 above the fold), 0 tab screens; blue: Clock the Crew
- **Drawings** (`plans`): heading "Drawings — 121 State Street", 5.5 screens tall, 3 sections (2 above the fold), 0 tab screens; blue: none; runs past the edge: cut off by pr-m (Structural Consultant · 9/1 · Maya Natar)
- **Schedule** (`sched`): heading "Schedule", 3.1 screens tall, 14 sections (4 above the fold), 0 tab screens; blue: none
- **Photos** (`photos`): heading "Photos", 2.3 screens tall, 0 sections (0 above the fold), 6 tab screens; blue: Add Photos
- **Documents** (`files`): heading "Documents", 4.7 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: none

### Foreman (Angel), phone, 45 Cranberry St — design

- **Job Page** (`fsite`): heading "Site", 1.1 screens tall, 4 sections (4 above the fold), 0 tab screens; blue: none
- **Daily Log** (`flog`): heading "Daily Log", 1.3 screens tall, 3 sections (3 above the fold), 6 tab screens; blue: Next
- **Requests** (`req`): heading "Requests", 0.8 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: Send the Request
- **Crew** (`fcrew`): heading "Crew", 1.6 screens tall, 4 sections (2 above the fold), 0 tab screens; blue: Clock the Crew
- **Drawings** (`plans`): heading "Drawings — 45 Cranberry St", 3.5 screens tall, 5 sections (2 above the fold), 0 tab screens; blue: none
- **Schedule** (`sched`): heading "Schedule", 1.3 screens tall, 7 sections (6 above the fold), 0 tab screens; blue: none
- **Photos** (`photos`): heading "Photos", 1.6 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: Add Photos
- **Documents** (`files`): heading "Documents", 1.1 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: none

### Designer (Sarah), desktop, 121 State Street

Strip (shown): Design, Project Board, Filings, Selections.

- **Job Page** (`sboard`): heading "Project Board", 1.0 screens tall, 11 sections (11 above the fold), 3 tab screens; blue: none
- **Schedule** (`sched`): heading "Schedule", 1.0 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: none
- **Tasks** (`tasks`): heading "Tasks", 1.1 screens tall, 0 sections (0 above the fold), 17 tab screens; blue: New Task
- **Decisions** (`dec`): heading "Decisions", 0.8 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: none
- **Photos** (`photos`): heading "Photos", 1.5 screens tall, 0 sections (0 above the fold), 6 tab screens; blue: Add Photos
- **Documents** (`files`): heading "Documents", 2.1 screens tall, 0 sections (0 above the fold), 10 tab screens; blue: Upload Files

### Designer (Sarah), desktop, 45 Cranberry St — design

Strip (shown): Design, Project Board, Filings, Selections.

- **Job Page** (`sboard`): heading "Project Board", 0.9 screens tall, 5 sections (5 above the fold), 3 tab screens; blue: none
- **Schedule** (`sched`): heading "Schedule", 0.3 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: none
- **Tasks** (`tasks`): heading "Tasks", 0.4 screens tall, 0 sections (0 above the fold), 14 tab screens; blue: New Task
- **Decisions** (`dec`): heading "Decisions", 0.4 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: none
- **Photos** (`photos`): heading "Photos", 0.9 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: Add Photos
- **Documents** (`files`): heading "Documents", 0.7 screens tall, 0 sections (0 above the fold), 10 tab screens; blue: Upload Files
- **Drawings** (`plans`): heading "Drawings — 45 Cranberry St", 1.5 screens tall, 5 sections (2 above the fold), 0 tab screens; blue: New Revision; opens `plans` when asked for `sdraw`

### Designer (Sarah), phone, 121 State Street

Strip (shown): Design, Project Board, Filings, Selections.

- **Job Page** (`sboard`): heading "Project Board", 2.8 screens tall, 11 sections (2 above the fold), 3 tab screens; blue: none
- **Schedule** (`sched`): heading "Schedule", 2.8 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: none
- **Tasks** (`tasks`): heading "Tasks", 1.3 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- **Decisions** (`dec`): heading "Decisions", 1.1 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: Decide; runs past the edge: cut off by pr-m (8 days late · Owed by Architect / design, 3 days late · Owed by Architect / design)
- **Photos** (`photos`): heading "Photos", 2.2 screens tall, 0 sections (0 above the fold), 6 tab screens; blue: Add Photos
- **Documents** (`files`): heading "Documents", 5.5 screens tall, 0 sections (0 above the fold), 10 tab screens; blue: none

### Designer (Sarah), phone, 45 Cranberry St — design

Strip (shown): Design, Project Board, Filings, Selections.

- **Job Page** (`sboard`): heading "Project Board", 1.7 screens tall, 5 sections (2 above the fold), 3 tab screens; blue: none
- **Schedule** (`sched`): heading "Schedule", 0.5 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: none; nearly empty (20 words)
- **Tasks** (`tasks`): heading "Tasks", 1.0 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none; runs past the edge: cut off by tk2-sub (Tomorrow)
- **Decisions** (`dec`): heading "Decisions", 0.6 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: none
- **Photos** (`photos`): heading "Photos", 1.5 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: Add Photos
- **Documents** (`files`): heading "Documents", 1.0 screens tall, 0 sections (0 above the fold), 10 tab screens; blue: none
- **Drawings** (`plans`): heading "Drawings — 45 Cranberry St", 3.5 screens tall, 5 sections (1 above the fold), 0 tab screens; blue: New Revision; opens `plans` when asked for `sdraw`

### Billing, desktop, 121 State Street

Strip (shown): Projects, Overview 12, Documents.

- **Job Page** (`dash`): heading "Overview", 3.4 screens tall, 6 sections (1 above the fold), 0 tab screens; blue: none
- **Documents** (`files`): heading "Documents", 2.1 screens tall, 0 sections (0 above the fold), 10 tab screens; blue: Upload Files

### Billing, desktop, 45 Cranberry St — design

Strip (shown): Projects, Overview, Documents.

- **Job Page** (`dash`): heading "Overview", 1.8 screens tall, 6 sections (1 above the fold), 0 tab screens; blue: none
- **Documents** (`files`): heading "Documents", 0.7 screens tall, 0 sections (0 above the fold), 10 tab screens; blue: Upload Files

### Billing, phone, 121 State Street

Strip (shown): Projects, Overview 12, Documents.

- **Job Page as it opens (All projects)** (`dash`): heading "Look-Ahead", 4.7 screens tall, 5 sections (0 above the fold), 0 tab screens; blue: none
- **Job Page** (`dash`): heading "Look-Ahead", 4.4 screens tall, 5 sections (0 above the fold), 0 tab screens; blue: none
- **Documents** (`files`): heading "Documents", 5.5 screens tall, 0 sections (0 above the fold), 10 tab screens; blue: none

### Billing, phone, 45 Cranberry St — design

Strip (shown): Projects, Overview, Documents.

- **Job Page** (`dash`): heading "Look-Ahead", 2.5 screens tall, 5 sections (0 above the fold), 0 tab screens; blue: none
- **Documents** (`files`): heading "Documents", 1.0 screens tall, 0 sections (0 above the fold), 10 tab screens; blue: none

### Controller, desktop, 121 State Street

Strip (shown): Ledger, Controls 15, Budget.

- **Job Page** (`gl`): heading "Ledger", 0.8 screens tall, 3 sections (3 above the fold), 6 tab screens; blue: none

### Controller, desktop, 45 Cranberry St — design

Strip (shown): Ledger, Controls 15, Budget.

- **Job Page** (`gl`): heading "Ledger", 0.8 screens tall, 3 sections (3 above the fold), 6 tab screens; blue: none

### Controller, phone, 121 State Street

Strip (shown): Ledger, Controls 15, Budget.

- **Job Page** (`gl`): heading "Ledger", 1.4 screens tall, 3 sections (2 above the fold), 6 tab screens; blue: none

### Controller, phone, 45 Cranberry St — design

Strip (shown): Ledger, Controls 15, Budget.

- **Job Page** (`gl`): heading "Ledger", 1.4 screens tall, 3 sections (2 above the fold), 6 tab screens; blue: none

### Client (Klein), desktop, 121 State Street

- **Job Page** (`client`): heading "Overview", 1.9 screens tall, 6 sections (4 above the fold), 0 tab screens; blue: Choose
- **Schedule** (`sched`): heading "Schedule", 2.3 screens tall, 6 sections (4 above the fold), 0 tab screens; blue: none
- **Decisions** (`dec`): heading "Decisions", 1.2 screens tall, 5 sections (5 above the fold), 0 tab screens; blue: Choose
- **Account** (`clacct`): heading "Account", 0.9 screens tall, 3 sections (3 above the fold), 0 tab screens; blue: none
- **Chat** (`chat`): heading "Messages", 1.0 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: Send

### Client (Klein), phone, 121 State Street

- **Job Page** (`client`): heading "Overview", 3.7 screens tall, 6 sections (1 above the fold), 0 tab screens; blue: Choose
- **Schedule** (`sched`): heading "Schedule", 2.9 screens tall, 6 sections (4 above the fold), 0 tab screens; blue: none
- **Decisions** (`dec`): heading "Decisions", 1.7 screens tall, 5 sections (2 above the fold), 0 tab screens; blue: Choose
- **Account** (`clacct`): heading "Account", 1.3 screens tall, 3 sections (3 above the fold), 0 tab screens; blue: none
- **Chat** (`chat`): heading "Chat", 0.2 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: Send; nearly empty (22 words)

### Crew (Alberto), desktop, 121 State Street

- **Job Page** (`sched`): heading "Schedule", 1.0 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: none
- **Requests** (`req`): heading "Requests", 0.7 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: Send the Request
- **Photos** (`files`): heading "Photos", 1.9 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: Upload Files
- **Deliveries** (`recv`): heading "Deliveries", 0.5 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: Received
- **Drawings** (`plans`): heading "Drawings — 121 State Street", 2.8 screens tall, 3 sections (2 above the fold), 0 tab screens; blue: none

### Crew (Alberto), desktop, 45 Cranberry St — design

- **Job Page** (`sched`): heading "Schedule", 0.3 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: none
- **Requests** (`req`): heading "Requests", 0.6 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: Send the Request
- **Photos** (`files`): heading "Photos", 0.7 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: Upload Files
- **Deliveries** (`recv`): heading "Deliveries", 0.2 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none; nearly empty (22 words)
- **Drawings** (`plans`): heading "Drawings — 45 Cranberry St", 1.5 screens tall, 5 sections (2 above the fold), 0 tab screens; blue: none

### Crew (Alberto), phone, 121 State Street

- **Job Page** (`sched`): heading "Schedule", 3.6 screens tall, 14 sections (3 above the fold), 0 tab screens; blue: none
- **Requests** (`req`): heading "Requests", 1.0 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: Send the Request
- **Photos** (`files`): heading "Photos", 4.7 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: Take a Photo
- **Deliveries** (`recv`): heading "Deliveries", 0.5 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- **Drawings** (`plans`): heading "Drawings — 121 State Street", 5.5 screens tall, 3 sections (2 above the fold), 0 tab screens; blue: none; runs past the edge: cut off by pr-m (Structural Consultant · 9/1 · Maya Natar)

### Crew (Alberto), phone, 45 Cranberry St — design

- **Job Page** (`sched`): heading "Schedule", 1.3 screens tall, 7 sections (6 above the fold), 0 tab screens; blue: none
- **Requests** (`req`): heading "Requests", 0.8 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: Send the Request; nearly empty (24 words)
- **Photos** (`files`): heading "Photos", 1.1 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: Take a Photo
- **Deliveries** (`recv`): heading "Deliveries", 0.4 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none; nearly empty (9 words)
- **Drawings** (`plans`): heading "Drawings — 45 Cranberry St", 3.5 screens tall, 5 sections (2 above the fold), 0 tab screens; blue: none

### Driver (Alex), desktop, 121 State Street

- **Job Page** (`files`): heading "Receipts", 1.9 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: Upload Files
- **Requests** (`req`): heading "Requests", 0.8 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: Send the Request

### Driver (Alex), desktop, 45 Cranberry St — design

- **Job Page** (`files`): heading "Receipts", 0.7 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: Upload Files
- **Requests** (`req`): heading "Requests", 0.6 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: Send the Request

### Driver (Alex), phone, 121 State Street

- **Job Page** (`files`): heading "Receipts", 4.7 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: Snap a Receipt
- **Requests** (`req`): heading "Requests", 1.1 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: Send the Request

### Driver (Alex), phone, 45 Cranberry St — design

- **Job Page** (`files`): heading "Receipts", 1.1 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: Snap a Receipt
- **Requests** (`req`): heading "Requests", 0.7 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: Send the Request; nearly empty (23 words)

## 10. What This Census Did Not Check, and How Sure It Is

- **Records are found by their words** (the information map's rule): a record shown as a number, a chart or in other words is not counted, so duplication counts are a floor, and a record whose words appear inside another (a decision named in a material's "held by") counts on that page too.
- **Figures** are read from tiles, two-column tables, definition lists and the bold money that leads a note. A figure inside a sentence is not read. Labels are compared with numbers and small words removed, so two different figures with one label show as a disagreement and need a person to judge.
- **Tabs** are rows of two or more buttons with exactly one on. A dropdown that switches the view, a row of toggles (a job's working days), Project Settings' rows and a button that commits (New, Send, Approve...) are never pressed. One level of revealed tabs is walked, and a tab group seen once on a page is not walked again from another route to the same page (Change Orders, Estimates and Billing are one page with three entries).
- **What opens, not what is two taps away:** a record opened from a row (an invoice, a PO, a decision sheet), "N more" rows and folded cards are not walked.
- **The client** is walked on their own job only; the second job is not theirs. **Field roles** are walked on the job pages of their own menus; they have no job page with a strip.
- **Each role starts as a new device:** what the overview remembers (All projects or one job) is cleared before each sign-in, so the phone shows what a person sees the first time. A person who once picks a job in the switcher keeps that job.
- **Data changes:** every save() during the walk is counted per screen (section 4). None means the walk changed nothing.
- **Not judged:** whether the content is right, what is missing, and what should merge. That is step 2: the role-expert PM and the information-architecture reviewer walk every page with this census in hand.

