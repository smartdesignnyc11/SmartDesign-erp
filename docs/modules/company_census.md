# The Company and Settings Module, Page by Page: the Census

**Asked by Alan, 2026-10-26:** "Go through all the modules with screenshots. It's important to understand the format of every page and what's on it." The loop's experts and the client expert walk every page of their module with this in hand in round one of the improvement loop (docs/IMPROVEMENT_LOOP.md).

**What this is.** A machine inventory, not a judgment, in the format of the Projects census (`docs/modules/projects_census.md`). No app code changed. `tests/module_census.py` (its helpers `tests/module_census_js.js` sit on the projects census's reader `tests/census_js.js` and the information map's `tests/ia_js.js`) signs in as each role on a fresh app at 1440 and at 390, reads the role's running menu, and reaches each page of this module the way the person does: the phone bar, or the menu (the hamburger on the phone), the group, then the strip. It presses every tab of every tab group and the tabs those reveal, follows the page's own links to this module's pages the menu did not reach, reads every screen and shoots it. The primary role is the owner; every role whose menu holds a page of this module is walked. Job-scoped pages show **121 State Street** wherever the role may open it.

**Where this module's pages sit.** Settings' Company Settings tile opens the job's settings page in its company mode (users, entities, approval rules, the company block); it is walked here as Company Settings, read as it opens (its rows of buttons are settings and are never pressed). The Brain opens the Ask page (`pa`), the page More calls Chief of Staff.

**Build bd3180c27e33** (master 1cc2eb9), the one build every module census of this round ran on. 268 screens in all. Walked 2026-10-26 06:29 on the demo day (Thu 2026-09-03); the walk of every module took 54.4 minutes. Raw read: `review/census/company/data.json`. Every screen per role in tables: `review/census/company/tables.md`. Screenshots of every screen, both devices: `review/census/company/shots/` (`desktop_` or `phone_`, the role, the page, then the tab; up to 3 desktop or 5 phone screens tall). The first screen of each page is committed; the tabs stay on the machine that ran it.

Run it: `python3 build.py && cd tests && ./slot.sh python3 module_census.py --module company` (then `python3 module_census.py --report` rewrites every module's page from data.json).

## Headline

- **Owner: 12 pages with 25 more screens behind their tabs on the desktop (12 pages and 15 tab screens on the phone)**, about 36 desktop screens end to end.
- **Pages each role reaches in this module, desktop:** Owner 12, PM 11, Coordinator 9, Foreman 3, Designer 3, Billing 4, Controller 8, Crew 3, Driver 3.
- **Reached only one way** by Owner: Calendar (desktop and phone), Company (desktop and phone), Obligations (desktop and phone), Settings (desktop and phone), The Brain (desktop and phone) (one menu entry, not on the phone bar, and no walked page links to it; section 1).
- **The same page under another module's menu** (Owner, desktop): Company Settings is also Projects › Project Settings (`proj`); The Brain is also Today › Chief of Staff (`pa`).
- **22 records show on two or more of this module's pages** for Owner on the desktop (5 vendors, 3 approvals, 3 schedule lines, 2 meetings). "LLC biennial statement — SmartDesign Group LLC" is on 4: Calendar, Company, Obligations, The Brain.
- **1 pairs of pages list largely the same records,** led by Company and The Brain (6 shared).
- **The same records in other modules** (Owner, desktop): Accounting › Dashboard lists 33; Tasks and Messages › Tasks lists 27; Projects › Job Page lists 25; Accounting › Reports lists 24; Purchasing › Buy Board lists 20 of the 116 records this module lists.
- **On the phone** (Owner): 5 of the 12 pages are taller than three screens (Calendar, The Brain, Connections, The SmartDesign Standard, Company Settings); 6 have no section heading above the fold; 5 are reached through a strip entry that sits off screen until the strip is swiped (The Brain, Obligations, Problem Reports, Your Own Data); 0 screens scroll sideways.
- **Nothing crashed and no page raised an error**; every page opened.
- **Reading changed nothing:** no save during the walk.

## 1. The Tree, Role by Role

**Pages** are the module's pages the role reaches from its menu (and the links those pages show). **Tabs** are the screens behind each page's tab groups, and behind the tabs those reveal. **Sections** are the headed parts of each page as it opens. Each cell reads desktop / phone.

| Role | Primary | First page of the module, reached by (desktop / phone) | Pages | Tab screens | Sections | Screens |
|---|---|---|---|---|---|---|
| Owner | yes | Company (1 tap) / menu › Company (2 taps) | 12 / 12 | 25 / 15 | 93 / 91 | 37 / 27 |
| PM (Alan) |  | Company (1 tap) / menu › Company (2 taps) | 11 / 11 | 28 / 12 | 84 / 82 | 39 / 23 |
| Coordinator (Chen) |  | Company (1 tap) / menu › Company (2 taps) | 9 / 9 | 25 / 9 | 71 / 69 | 34 / 18 |
| Foreman (Angel) |  | Team (1 tap) / menu › Team (2 taps) | 3 / 3 | 0 / 0 | 61 / 61 | 3 / 3 |
| Designer (Sarah) |  | More (1 tap) / menu › More (2 taps) | 3 / 3 | 2 / 2 | 63 / 63 | 5 / 5 |
| Billing |  | More › Team (2 taps) / menu › More › swipe the strip, Team (3 taps) | 4 / 4 | 2 / 2 | 65 / 63 | 6 / 6 |
| Controller |  | More › Calendar (2 taps) / menu › More › swipe the strip, Calendar (3 taps) | 8 / 8 | 25 / 9 | 68 / 68 | 33 / 17 |
| Crew (Alberto) |  | Team (1 tap) / menu › Team (2 taps) | 3 / 3 | 0 / 0 | 61 / 61 | 3 / 3 |
| Driver (Alex) |  | Team (1 tap) / menu › Team (2 taps) | 3 / 3 | 0 / 0 | 61 / 61 | 3 / 3 |

### Which pages each role reaches (desktop)

Each cell is the number of screens the page has (the page and its tabs); "-" means the role does not reach it.

| Page | Owner | PM | Coordinator | Foreman | Designer | Billing | Controller | Crew | Driver |
|---|---|---|---|---|---|---|---|---|---|
| Company | 1 | 1 | 1 | - | - | - | 1 | - | - |
| Calendar | 7 | 7 | 7 | - | - | - | 7 | - | - |
| Team | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| The Brain | 12 | 18 | 18 | - | - | - | 18 | - | - |
| Obligations | 1 | 1 | 1 | - | - | - | 1 | - | - |
| Settings | 1 | 1 | - | - | - | - | 1 | - | - |
| Connections | 3 | 3 | 3 | 1 | 3 | 3 | 3 | 1 | 1 |
| The SmartDesign Standard | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| Problem Reports | 4 | 4 | - | - | - | - | - | - | - |
| Your Own Data | 4 | - | 1 | - | - | - | - | - | - |
| Sales Settings | 1 | 1 | 1 | - | - | 1 | - | - | - |
| Company Settings | 1 | 1 | - | - | - | - | - | - | - |

### Owner's tree at a glance

Reached by is the taps from the role's first page, desktop then phone. Tall is in screens, desktop / phone. Sections are the headed parts as the page opens (phone above the fold). Tabs are the screens behind its tab groups, desktop / phone. "What it lists" counts the records found on the page as it opens.

| Page | Reached by (desktop / phone) | Heading | Tall | Sections (phone above the fold) | Tabs | Tiles and figures | What it lists | Blue button | First button | Shots |
|---|---|---|---|---|---|---|---|---|---|---|
| Company | Company (1 tap) / menu › Company (2 taps) | Company | 0.7 / 0.9 | 0 (0) | 0 / 0 | Renewals Due 1; Meetings to Review 2; Not Matched 0; Changes to Approve 3 | 3 approvals, 2 meetings, 1 obligations | none | Renewals Due 1 licenses, ins | [desktop](../../review/census/company/shots/desktop_owner_company.jpg) [phone](../../review/census/company/shots/phone_owner_company.jpg) |
| Calendar | Company › Calendar (2 taps) / menu › Company › Calendar (3 taps) | Calendar | 1.7 / 4.5 | 1 (0) | 6 / 6 | - | 10 to-dos, 8 decisions, 1 inspections, 1 materials | none | Copy as ICS | [desktop](../../review/census/company/shots/desktop_owner_calendar.jpg) [phone](../../review/census/company/shots/phone_owner_calendar.jpg) |
| Team | Company › Team (2 taps) / menu › Company › Team (3 taps) | Team | 1.4 / 2.3 | 0 (0) | 0 / 0 | - | - | none | Edit | [desktop](../../review/census/company/shots/desktop_owner_team.jpg) [phone](../../review/census/company/shots/phone_owner_team.jpg) |
| The Brain | Company › The Brain (2 taps) / menu › Company › swipe the strip, The Brain (3 taps) | The Brain | 5.2 / 7.2 | 6 (1) | 11 / 1 | Events Seen Today 18; Lessons Proposed Today 9; Rules Fired Today 0; Changes Drafted Today 3 | 5 vendors, 4 approvals, 4 bank and card lines, 2 schedule lines | Approve | Chat | [desktop](../../review/census/company/shots/desktop_owner_the_brain.jpg) [phone](../../review/census/company/shots/phone_owner_the_brain.jpg) |
| Obligations | Company › Obligations (2 taps) / menu › Company › swipe the strip, Obligations (3 taps) | Obligations | 1.0 / 1.3 | 0 (0) | 0 / 0 | Lapsed 1; Renew Now 1; Active 10; Premiums $10,550 | 5 vendors, 5 obligations, 1 COI lapses | New Obligation | New Obligation (blue) | [desktop](../../review/census/company/shots/desktop_owner_obligations.jpg) [phone](../../review/census/company/shots/phone_owner_obligations.jpg) |
| Settings | Settings (1 tap) / menu › Settings (2 taps) | Settings | 0.6 / 0.5 | 1 (1) | 0 / 0 | - | - | none | Company Settings users, enti | [desktop](../../review/census/company/shots/desktop_owner_settings.jpg) [phone](../../review/census/company/shots/phone_owner_settings.jpg) |
| Connections | Settings › Connections (2 taps) / menu › Settings › Connections (3 taps) | Connections | 3.5 / 5.5 | 4 (2) | 2 / 2 | - | - | none | Import Statement | [desktop](../../review/census/company/shots/desktop_owner_connections.jpg) [phone](../../review/census/company/shots/phone_owner_connections.jpg) |
| The SmartDesign Standard | Settings › The SmartDesign Standard (2 taps) / menu › Settings › The SmartDesign Standard (3 taps) | The SmartDesign Standard | 11.0 / 25.3 | 59 (1) | 0 / 0 | - | 2 to-dos | none | Edit the Standard | [desktop](../../review/census/company/shots/desktop_owner_the_smartdesign_standard.jpg) [phone](../../review/census/company/shots/phone_owner_the_smartdesign_standard.jpg) |
| Problem Reports | Settings › Problem Reports (2 taps) / menu › Settings › swipe the strip, Problem Reports (3 taps) | Problem Reports | 0.5 / 0.6 | 0 (0) | 3 / 3 | Someone Is Stuck 0; Still Open 0; Most Common —; Waiting on a Word 0 | - | none | Copy All for the Developer | [desktop](../../review/census/company/shots/desktop_owner_problem_reports.jpg) [phone](../../review/census/company/shots/phone_owner_problem_reports.jpg) |
| Your Own Data | Settings › Your Own Data (2 taps) / menu › Settings › swipe the strip, Your Own Data (3 taps) | Your Own Data | 1.1 / 1.9 | 4 (2) | 3 / 3 | Projects 4; Clients 6; Vendors and Subs 12; People 9 | - | none | Save a Backup | [desktop](../../review/census/company/shots/desktop_owner_your_own_data.jpg) [phone](../../review/census/company/shots/phone_owner_your_own_data.jpg) |
| Sales Settings | Settings › Sales Settings (2 taps) / menu › Settings › swipe the strip, Sales Settings (3 taps) | Sales Settings | 0.7 / 1.0 | 2 (0) | 0 / 0 | - | - | Save | Pipelines | [desktop](../../review/census/company/shots/desktop_owner_sales_settings.jpg) [phone](../../review/census/company/shots/phone_owner_sales_settings.jpg) |
| Company Settings | Settings › link: Company Settings users, entities, approv / Settings › link: Company Settings | Settings | 8.7 / 12.6 | 16 (2) | 0 / 0 | - | 9 materials, 6 schedule lines, 3 clients, 3 purchase orders | Save | Project Settings | [desktop](../../review/census/company/shots/desktop_owner_company_settings.jpg) [phone](../../review/census/company/shots/phone_owner_company_settings.jpg) |

### How each page is reached, and the pages reached only one way

Menu places are the role's menu entries that open the page (a page in two groups has two). The phone bar counts as one more way in on the phone (its pages are in the menu too). Links are the walked pages, in any module, that show a link to it. **One way** means one menu place and nothing else: lose that entry and the page is lost.

| Role | Device | Page | Menu places | Phone bar | Linked from | Ways in |
|---|---|---|---|---|---|---|
| Owner | desktop | Company | Company | - | - | 1 (one way) |
| Owner | desktop | Calendar | Company › Calendar | - | - | 1 (one way) |
| Owner | desktop | Team | Company › Team | - | Company and Settings › The SmartDesign Standard, Projects › Tasks, Tasks and Messages › Messages | 4 |
| Owner | desktop | The Brain | Company › The Brain | - | - | 1 (one way) |
| Owner | desktop | Obligations | Company › Obligations | - | - | 1 (one way) |
| Owner | desktop | Settings | Settings | - | - | 1 (one way) |
| Owner | desktop | Connections | Settings › Connections | - | Company and Settings › Settings | 2 |
| Owner | desktop | The SmartDesign Standard | Settings › The SmartDesign Standard | - | Company and Settings › Settings | 2 |
| Owner | desktop | Problem Reports | Settings › Problem Reports | - | Company and Settings › Settings | 2 |
| Owner | desktop | Your Own Data | Settings › Your Own Data | - | Company and Settings › Settings | 2 |
| Owner | desktop | Sales Settings | Settings › Sales Settings | - | Company and Settings › Settings | 2 |
| Owner | desktop | Company Settings | Projects › Project Settings | - | Accounting › Banking, Company and Settings › Settings, Tasks and Messages › Meetings, Time and Payroll › Time & Crew | 5 |
| Owner | phone | Company | Company | - | - | 1 (one way) |
| Owner | phone | Calendar | Company › Calendar | - | - | 1 (one way) |
| Owner | phone | Team | Company › Team | - | Company and Settings › The SmartDesign Standard, Tasks and Messages › Messages | 3 |
| Owner | phone | The Brain | Company › The Brain | - | - | 1 (one way) |
| Owner | phone | Obligations | Company › Obligations | - | - | 1 (one way) |
| Owner | phone | Settings | Settings | - | - | 1 (one way) |
| Owner | phone | Connections | Settings › Connections | - | Company and Settings › Settings | 2 |
| Owner | phone | The SmartDesign Standard | Settings › The SmartDesign Standard | - | Company and Settings › Settings | 2 |
| Owner | phone | Problem Reports | Settings › Problem Reports | - | Company and Settings › Settings | 2 |
| Owner | phone | Your Own Data | Settings › Your Own Data | - | Company and Settings › Settings | 2 |
| Owner | phone | Sales Settings | Settings › Sales Settings | - | Company and Settings › Settings | 2 |
| Owner | phone | Company Settings | Projects › Project Settings | - | Company and Settings › Settings | 2 |
| PM (Alan) | desktop | Company | Company | - | - | 1 (one way) |
| PM (Alan) | desktop | Calendar | Company › Calendar | - | - | 1 (one way) |
| PM (Alan) | desktop | Team | Company › Team | - | Company and Settings › The SmartDesign Standard, Projects › Tasks, Tasks and Messages › Messages | 4 |
| PM (Alan) | desktop | The Brain | Company › The Brain | - | - | 1 (one way) |
| PM (Alan) | desktop | Obligations | Company › Obligations | - | - | 1 (one way) |
| PM (Alan) | desktop | Settings | Settings | - | - | 1 (one way) |
| PM (Alan) | desktop | Connections | Settings › Connections | - | Company and Settings › Settings | 2 |
| PM (Alan) | desktop | The SmartDesign Standard | Settings › The SmartDesign Standard | - | Company and Settings › Settings | 2 |
| PM (Alan) | desktop | Problem Reports | Settings › Problem Reports | - | Company and Settings › Settings | 2 |
| PM (Alan) | desktop | Sales Settings | Settings › Sales Settings | - | Company and Settings › Settings | 2 |
| PM (Alan) | desktop | Company Settings | Projects › Project Settings | - | Accounting › Banking, Company and Settings › Settings, Tasks and Messages › Meetings, Time and Payroll › Time & Crew | 5 |
| PM (Alan) | phone | Company | Company | - | - | 1 (one way) |
| PM (Alan) | phone | Calendar | Company › Calendar | - | - | 1 (one way) |
| PM (Alan) | phone | Team | Company › Team | - | Company and Settings › The SmartDesign Standard, Tasks and Messages › Messages | 3 |
| PM (Alan) | phone | The Brain | Company › The Brain | - | - | 1 (one way) |
| PM (Alan) | phone | Obligations | Company › Obligations | - | - | 1 (one way) |
| PM (Alan) | phone | Settings | Settings | - | - | 1 (one way) |
| PM (Alan) | phone | Connections | Settings › Connections | - | Company and Settings › Settings | 2 |
| PM (Alan) | phone | The SmartDesign Standard | Settings › The SmartDesign Standard | - | Company and Settings › Settings | 2 |
| PM (Alan) | phone | Problem Reports | Settings › Problem Reports | - | Company and Settings › Settings | 2 |
| PM (Alan) | phone | Sales Settings | Settings › Sales Settings | - | Company and Settings › Settings | 2 |
| PM (Alan) | phone | Company Settings | Projects › Project Settings | - | Company and Settings › Settings | 2 |
| Coordinator (Chen) | desktop | Company | Company | - | - | 1 (one way) |
| Coordinator (Chen) | desktop | Calendar | Company › Calendar | - | - | 1 (one way) |
| Coordinator (Chen) | desktop | Team | Company › Team | - | Company and Settings › The SmartDesign Standard, Tasks and Messages › Messages | 3 |
| Coordinator (Chen) | desktop | The Brain | Company › The Brain | - | - | 1 (one way) |
| Coordinator (Chen) | desktop | Obligations | Company › Obligations | - | - | 1 (one way) |
| Coordinator (Chen) | desktop | Connections | Settings › Connections | - | - | 1 (one way) |
| Coordinator (Chen) | desktop | The SmartDesign Standard | Settings › The SmartDesign Standard | - | - | 1 (one way) |
| Coordinator (Chen) | desktop | Your Own Data | Settings › Your Own Data | - | - | 1 (one way) |
| Coordinator (Chen) | desktop | Sales Settings | Settings › Sales Settings | - | - | 1 (one way) |
| Coordinator (Chen) | phone | Company | Company | - | - | 1 (one way) |
| Coordinator (Chen) | phone | Calendar | Company › Calendar | - | - | 1 (one way) |
| Coordinator (Chen) | phone | Team | Company › Team | - | Company and Settings › The SmartDesign Standard, Tasks and Messages › Messages | 3 |
| Coordinator (Chen) | phone | The Brain | Company › The Brain | - | - | 1 (one way) |
| Coordinator (Chen) | phone | Obligations | Company › Obligations | - | - | 1 (one way) |
| Coordinator (Chen) | phone | Connections | Settings › Connections | - | - | 1 (one way) |
| Coordinator (Chen) | phone | The SmartDesign Standard | Settings › The SmartDesign Standard | - | - | 1 (one way) |
| Coordinator (Chen) | phone | Your Own Data | Settings › Your Own Data | - | - | 1 (one way) |
| Coordinator (Chen) | phone | Sales Settings | Settings › Sales Settings | - | - | 1 (one way) |
| Foreman (Angel) | desktop | Team | Team | - | Company and Settings › The SmartDesign Standard, Tasks and Messages › Messages | 3 |
| Foreman (Angel) | desktop | Connections | Connections | - | - | 1 (one way) |
| Foreman (Angel) | desktop | The SmartDesign Standard | The SmartDesign Standard | - | - | 1 (one way) |
| Foreman (Angel) | phone | Team | Team | - | Company and Settings › The SmartDesign Standard, Tasks and Messages › Messages | 3 |
| Foreman (Angel) | phone | Connections | Connections | - | - | 1 (one way) |
| Foreman (Angel) | phone | The SmartDesign Standard | The SmartDesign Standard | - | - | 1 (one way) |
| Designer (Sarah) | desktop | Team | More › Team | - | Company and Settings › The SmartDesign Standard, Tasks and Messages › Messages | 3 |
| Designer (Sarah) | desktop | Connections | Settings › Connections | - | - | 1 (one way) |
| Designer (Sarah) | desktop | The SmartDesign Standard | Settings › The SmartDesign Standard | - | - | 1 (one way) |
| Designer (Sarah) | phone | Team | More › Team | - | Company and Settings › The SmartDesign Standard, Tasks and Messages › Messages | 3 |
| Designer (Sarah) | phone | Connections | Settings › Connections | - | - | 1 (one way) |
| Designer (Sarah) | phone | The SmartDesign Standard | Settings › The SmartDesign Standard | - | - | 1 (one way) |
| Billing | desktop | Team | More › Team | - | Company and Settings › The SmartDesign Standard, Tasks and Messages › Messages | 3 |
| Billing | desktop | Connections | Settings › Connections | - | - | 1 (one way) |
| Billing | desktop | The SmartDesign Standard | Settings › The SmartDesign Standard | - | - | 1 (one way) |
| Billing | desktop | Sales Settings | Settings › Sales Settings | - | - | 1 (one way) |
| Billing | phone | Team | More › Team | - | Company and Settings › The SmartDesign Standard, Tasks and Messages › Messages | 3 |
| Billing | phone | Connections | Settings › Connections | - | - | 1 (one way) |
| Billing | phone | The SmartDesign Standard | Settings › The SmartDesign Standard | - | - | 1 (one way) |
| Billing | phone | Sales Settings | Settings › Sales Settings | - | - | 1 (one way) |
| Controller | desktop | Calendar | More › Calendar | - | - | 1 (one way) |
| Controller | desktop | The Brain | More › The Brain | - | - | 1 (one way) |
| Controller | desktop | Obligations | More › Obligations | - | - | 1 (one way) |
| Controller | desktop | Company | More › Company | - | - | 1 (one way) |
| Controller | desktop | Team | More › Team | - | Company and Settings › The SmartDesign Standard, Tasks and Messages › Messages | 3 |
| Controller | desktop | Settings | Settings | - | - | 1 (one way) |
| Controller | desktop | Connections | Settings › Connections | - | Company and Settings › Settings | 2 |
| Controller | desktop | The SmartDesign Standard | Settings › The SmartDesign Standard | - | Company and Settings › Settings | 2 |
| Controller | phone | Calendar | More › Calendar | - | - | 1 (one way) |
| Controller | phone | The Brain | More › The Brain | - | - | 1 (one way) |
| Controller | phone | Obligations | More › Obligations | - | - | 1 (one way) |
| Controller | phone | Company | More › Company | - | - | 1 (one way) |
| Controller | phone | Team | More › Team | - | Company and Settings › The SmartDesign Standard, Tasks and Messages › Messages | 3 |
| Controller | phone | Settings | Settings | - | - | 1 (one way) |
| Controller | phone | Connections | Settings › Connections | - | Company and Settings › Settings | 2 |
| Controller | phone | The SmartDesign Standard | Settings › The SmartDesign Standard | - | Company and Settings › Settings | 2 |
| Crew (Alberto) | desktop | Team | Team | - | Company and Settings › The SmartDesign Standard | 2 |
| Crew (Alberto) | desktop | Connections | Connections | - | - | 1 (one way) |
| Crew (Alberto) | desktop | The SmartDesign Standard | The SmartDesign Standard | - | - | 1 (one way) |
| Crew (Alberto) | phone | Team | Team | - | Company and Settings › The SmartDesign Standard | 2 |
| Crew (Alberto) | phone | Connections | Connections | - | - | 1 (one way) |
| Crew (Alberto) | phone | The SmartDesign Standard | The SmartDesign Standard | - | - | 1 (one way) |
| Driver (Alex) | desktop | Team | Team | - | Company and Settings › The SmartDesign Standard | 2 |
| Driver (Alex) | desktop | Connections | Connections | - | - | 1 (one way) |
| Driver (Alex) | desktop | The SmartDesign Standard | The SmartDesign Standard | - | - | 1 (one way) |
| Driver (Alex) | phone | Team | Team | - | Company and Settings › The SmartDesign Standard | 2 |
| Driver (Alex) | phone | Connections | Connections | - | - | 1 (one way) |
| Driver (Alex) | phone | The SmartDesign Standard | The SmartDesign Standard | - | - | 1 (one way) |

## 2. Where the Data Lives, and Where It Shows Twice

Records are found by their own words (the information map's catalog, the job's nouns and this census's: clients, vendors, leads, contacts, companies, every invoice, bill and PO, payroll runs, stock, meetings, journals, obligations, lessons, partners, bank lines, threads), so these are floors. A page's tabs count as the page.

### Owner, desktop: each kind of record, and the pages that list it

| Records | Found | Pages that list them (how many each) | Also in other modules |
|---|---|---|---|
| obligations | 5 | 4: Obligations 5, Company 1, Calendar 1, The Brain 1 | Tasks and Messages › Tasks 5, Accounting › Dashboard 1 |
| vendors | 9 | 4: The Brain 8, Obligations 5, Company Settings 3, Calendar 1 | Purchasing › Vendors 9, Accounting › Banking 8, Accounting › Dashboard 8, Accounting › Ledger 7 |
| meetings | 2 | 3: Company 2, The Brain 2, Company Settings 2 | Tasks and Messages › Meetings 2 |
| to-dos | 14 | 3: Calendar 10, The Brain 4, The SmartDesign Standard 2 | Tasks and Messages › Tasks 14, Accounting › Dashboard 8, Projects › Job Page 8, Projects › Tasks 8 |
| purchase orders | 4 | 3: Company Settings 3, The Brain 2, Calendar 1 | Purchasing › Orders 4, Accounting › Reports 3, Today › Approvals 2, Projects › Job Page 2 |
| files | 4 | 3: Company Settings 3, The Brain 2, Calendar 1 | Purchasing › Orders 4, Accounting › Reports 3, Accounting › Spend 2, Today › Approvals 2 |
| approvals | 6 | 2: The Brain 6, Company 3 | Today › Today 5, Today › Approvals 5, Tasks and Messages › Meetings 3 |
| decisions | 11 | 2: Calendar 8, The Brain 4 | Accounting › Dashboard 9, Projects › Decisions 8, Design › Project Board 8, Purchasing › Buy Board 5 |
| materials | 10 | 2: Company Settings 9, Calendar 1 | Accounting › Reports 10, Purchasing › Buy Board 10, Projects › Costs 8, Sales and Clients › Estimates 7 |
| schedule lines | 6 | 2: Company Settings 6, The Brain 3 | Accounting › Reports 6, Tasks and Messages › Tasks 5, Accounting › Dashboard 3, Projects › Job Page 2 |
| clients | 4 | 2: Company Settings 3, The Brain 1 | Accounting › Reports 3, Tasks and Messages › Messages 3, Sales and Clients › Companies 3, Sales and Clients › People 3 |
| COI lapses | 2 | 2: The Brain 2, Obligations 1 | Accounting › Dashboard 2, Today › Approvals 2, Today › Today 1, Accounting › Reports 1 |
| inspections | 1 | 1: Calendar 1 | Projects › Permits 1, Accounting › Dashboard 1, Projects › Job Page 1 |
| field requests | 1 | 1: The Brain 1 | Purchasing › Quotes 1, Projects › Job Page 1, Purchasing › Buy Board 1, Field and Site › Route 1 |
| leads | 5 | 1: The Brain 5 | Sales and Clients › People 5, Sales and Clients › Clients 5, Sales and Clients › Companies 5, Sales and Clients › Sales 5 |
| bills | 2 | 1: The Brain 2 | Accounting › Spend 2, Accounting › Bills & Payroll 2, Accounting › Ledger 2, Accounting › Dashboard 1 |
| money flags | 26 | 1: The Brain 26 | - |
| findings | 14 | 1: The Brain 14 | Today › Today 2, Today › Approvals 2 |
| contacts | 5 | 1: The Brain 5 | Sales and Clients › People 6, Sales and Clients › Clients 6, Sales and Clients › Companies 6, Sales and Clients › Sales 5 |
| bank and card lines | 7 | 1: The Brain 7 | Accounting › Spend 7, Accounting › Banking 7, Accounting › Ledger 7, Accounting › Controls 7 |
| site questions | 1 | 1: The Brain 1 | Projects › Field 1, Today › Approvals 1 |

### Records on two or more pages, and lists that are the same list twice

**Owner, desktop:** 22 records on two or more pages: vendors 5 (up to 3 pages); approvals 3 (up to 2 pages); schedule lines 3 (up to 2 pages); meetings 2 (up to 3 pages); to-dos 2 (up to 2 pages); purchase orders 2 (up to 2 pages); files 2 (up to 2 pages); obligations 1 (up to 4 pages); decisions 1 (up to 2 pages); COI lapses 1 (up to 2 pages).

- "LLC biennial statement — SmartDesign Group LLC" (obligations) on 4 pages: Calendar, Company, Obligations, The Brain
- "121 State St - Schedule Review" (meetings) on 3 pages: Company, Company Settings, The Brain
- "Team Catch Up" (meetings) on 3 pages: Company, Company Settings, The Brain
- "Carlos Millwork" (vendors) on 3 pages: Calendar, Obligations, The Brain
- "Window Works" (vendors) on 3 pages: Company Settings, Obligations, The Brain
- "Nemo Tile" (vendors) on 3 pages: Company Settings, Obligations, The Brain
- the same list twice (3 or more shared records, at least half of the shorter list): Company and The Brain (6 shared, of 6 and 77: approvals, meetings, obligations)

**PM (Alan), desktop:** 29 records on two or more pages: materials 8 (up to 2 pages); vendors 5 (up to 3 pages); schedule lines 3 (up to 2 pages); meetings 2 (up to 3 pages); obligations 2 (up to 4 pages); to-dos 2 (up to 2 pages); purchase orders 2 (up to 2 pages); files 2 (up to 2 pages); decisions 1 (up to 2 pages); COI lapses 1 (up to 2 pages); clients 1 (up to 2 pages).

- the same list twice (3 or more shared records, at least half of the shorter list): Company Settings and The Brain (17 shared, of 23 and 127: materials, schedule lines, meetings); Company and The Brain (3 shared, of 3 and 127: meetings, obligations); Obligations and The Brain (3 shared, of 6 and 127: obligations, COI lapses)

**Coordinator (Chen), desktop:** 14 records on two or more pages: vendors 4 (up to 3 pages); to-dos 3 (up to 2 pages); meetings 2 (up to 2 pages); obligations 1 (up to 4 pages); decisions 1 (up to 2 pages); purchase orders 1 (up to 2 pages); files 1 (up to 2 pages); COI lapses 1 (up to 2 pages).

- the same list twice (3 or more shared records, at least half of the shorter list): Company and The Brain (3 shared, of 3 and 99: meetings, obligations)

**Controller, desktop:** 12 records on two or more pages: vendors 4 (up to 3 pages); to-dos 3 (up to 2 pages); meetings 2 (up to 2 pages); decisions 1 (up to 2 pages); obligations 1 (up to 4 pages); COI lapses 1 (up to 2 pages).

- the same list twice (3 or more shared records, at least half of the shorter list): Company and The Brain (3 shared, of 3 and 151: meetings, obligations)

**Owner, phone:** 19 records on two or more pages: vendors 5 (up to 3 pages); approvals 3 (up to 2 pages); schedule lines 3 (up to 2 pages); meetings 2 (up to 3 pages); to-dos 2 (up to 2 pages); obligations 1 (up to 3 pages); COI lapses 1 (up to 2 pages); purchase orders 1 (up to 2 pages); files 1 (up to 2 pages).

- "121 State St - Schedule Review" (meetings) on 3 pages: Company, Company Settings, The Brain
- "Team Catch Up" (meetings) on 3 pages: Company, Company Settings, The Brain
- "LLC biennial statement — SmartDesign Group LLC" (obligations) on 3 pages: Calendar, Company, Obligations
- "Window Works" (vendors) on 3 pages: Company Settings, Obligations, The Brain
- "A step carried twice becomes a dated task with an owner" (approvals) on 2 pages: Company, The Brain
- "Weekly check-in from the ERP, not a spreadsheet" (approvals) on 2 pages: Company, The Brain
- the same list twice (3 or more shared records, at least half of the shorter list): Company and The Brain (5 shared, of 6 and 19: approvals, meetings)

### The same records in other modules

For each role on the desktop: the pages of other modules (the Projects census's 121 State Street pages included) that list records this module lists, with how many.

- **Owner** (116 records here): Accounting › Dashboard 33; Tasks and Messages › Tasks 27; Projects › Job Page 25; Accounting › Reports 24; Purchasing › Buy Board 20; Today › Approvals 19; Accounting › Spend 15; Today › Today 14
- **PM (Alan)** (157 records here): Accounting › Dashboard 40; Projects › Job Page 34; Purchasing › Buy Board 30; Accounting › Reports 27; Tasks and Messages › Tasks 26; Projects › Tasks 14; Today › Today 13; Purchasing › Orders 13
- **Coordinator (Chen)** (121 records here): Accounting › Dashboard 34; Purchasing › Buy Board 31; Projects › Job Page 30; Today › Today 23; Tasks and Messages › Tasks 21; Today › Approvals 13; Purchasing › Orders 13; Projects › Tasks 11
- **Foreman (Angel)** (2 records here): Today › Today 2
- **Designer (Sarah)** (2 records here): Tasks and Messages › Tasks 2; Projects › Tasks 2
- **Billing** (2 records here): Accounting › Dashboard 2; Projects › Job Page 2; Tasks and Messages › Tasks 2
- **Controller** (175 records here): Accounting › Banking 31; Accounting › Controls 31; Accounting › Spend 31; Accounting › Ledger 29; Accounting › Dashboard 27; Tasks and Messages › Tasks 20; Accounting › Reports 14; Today › Today 12
- **Crew (Alberto)**: none found.
- **Driver (Alex)**: none found.

Names (clients, vendors, leads, contacts, companies, partners) are left out here: a page that writes a name counts as listing it. A page that is the same page as one of this module's (one view under two menus) is left out too and listed next.

### The same page under two modules' menus

- Owner: Company Settings here is also Projects › Project Settings (`proj`)
- Owner: The Brain here is also Today › Chief of Staff (`pa`)
- PM (Alan): Company Settings here is also Projects › Project Settings (`proj`)
- PM (Alan): The Brain here is also Today › Chief of Staff (`pa`)
- Coordinator (Chen): The Brain here is also Today › Chief of Staff (`pa`)
- Controller: The Brain here is also Today › Chief of Staff (`pa`)

## 3. One Label, Different Numbers

The same label (a tile, a figure, a tab or section count) with numbers that share no value on two pages, for one role. Some are right about different scopes ("Open" against "All", one job against every job); the person still reads one word with two numbers. Each needs a person to judge.

Inside the module: none found.

Against other modules, Owner, desktop: none found.

## 4. Empty, Dead and Broken Screens

| Device | Role | Screen | What |
|---|---|---|---|
| desktop | Owner | The Brain | opens pa when asked for brain |
| desktop | Owner | Problem Reports | lists nothing: "Nothing reported yet. The Report a Problem button is on ever" |
| desktop | Owner | Sales Settings | lists nothing: "None" |
| desktop | PM (Alan) | The Brain | opens pa when asked for brain |
| desktop | PM (Alan) | Problem Reports | lists nothing: "Nothing reported yet. The Report a Problem button is on ever" |
| desktop | PM (Alan) | Sales Settings | lists nothing: "None" |
| desktop | Coordinator (Chen) | The Brain | opens pa when asked for brain |
| desktop | Coordinator (Chen) | Sales Settings | lists nothing: "None" |
| desktop | Billing | Sales Settings | lists nothing: "None" |
| desktop | Controller | The Brain | opens pa when asked for brain |
| phone | Owner | The Brain | opens pa when asked for brain |
| phone | Owner | Problem Reports | lists nothing: "No reports yet. Ask the team to press Report a Problem the m" |
| phone | Owner | Sales Settings | lists nothing: "None Delete None Delete None Delete Value Delete Value, Clos" |
| phone | PM (Alan) | Team | lists nothing: "no email on file" |
| phone | PM (Alan) | The Brain | opens pa when asked for brain |
| phone | PM (Alan) | Settings | 10 words |
| phone | PM (Alan) | Problem Reports | lists nothing: "No reports yet. Ask the team to press Report a Problem the m" |
| phone | PM (Alan) | Sales Settings | lists nothing: "None Delete None Delete None Delete Value Delete Value, Clos" |
| phone | Coordinator (Chen) | Team | lists nothing: "no email on file" |
| phone | Coordinator (Chen) | The Brain | opens pa when asked for brain |
| phone | Coordinator (Chen) | Sales Settings | lists nothing: "None Delete None Delete None Delete Value Delete Value, Clos" |
| phone | Designer (Sarah) | Team | lists nothing: "no email on file" |
| phone | Billing | Team | lists nothing: "no email on file" |
| phone | Billing | Sales Settings | lists nothing: "None Delete None Delete None Delete Value Delete Value, Clos" |
| phone | Controller | The Brain | opens pa when asked for brain |
| phone | Controller | Team | lists nothing: "no email on file" |
| phone | Controller | Settings | 4 words |

## 5. The Phone at 390

"Cut off" is text the phone ends early; "scrolls inside" is a strip of tiles or tabs the person swipes sideways inside the page (the page itself does not move). "Strip swipe" counts pages whose strip entry sits off screen until the strip is swiped. Pages taller than 3 phone screens are listed with their height.

| Role | Screens | The page scrolls sideways | Text cut off at the edge | Strips that scroll inside the page | Strip swipe | Pages taller than 3 screens |
|---|---|---|---|---|---|---|
| Owner | 27 | 0 | 2: Company Settings, The Brain | 10: Calendar, Company, Company Settings, Connections, Obligations, Problem Reports, Sales Settings, Settings | 5: The Brain, Obligations, Problem Reports, Your Own Data, Sales Settings | 5: Calendar 4.5, The Brain 7.2, Connections 5.5, The SmartDesign Standard 25.3, Company Settings 12.6 |
| PM (Alan) | 23 | 0 | 2: Company Settings, The Brain | 9: Calendar, Company, Company Settings, Connections, Obligations, Problem Reports, Sales Settings, Settings | 4: The Brain, Obligations, Problem Reports, Sales Settings | 5: Calendar 4.5, The Brain 3.4, Connections 5.2, The SmartDesign Standard 25.3, Company Settings 11.6 |
| Coordinator (Chen) | 18 | 0 | 1: The Brain | 6: Calendar, Company, Connections, Obligations, Sales Settings, The Brain | 4: The Brain, Obligations, Your Own Data, Sales Settings | 4: Calendar 4.5, The Brain 3.4, Connections 5.4, The SmartDesign Standard 25.3 |
| Foreman (Angel) | 3 | 0 | 0 | 1: Connections | 0 | 1: The SmartDesign Standard 29.8 |
| Designer (Sarah) | 5 | 0 | 0 | 1: Connections | 0 | 2: Connections 4.7, The SmartDesign Standard 25.3 |
| Billing | 6 | 0 | 0 | 2: Connections, Sales Settings | 2: Team, Sales Settings | 2: Connections 5.0, The SmartDesign Standard 25.3 |
| Controller | 17 | 0 | 1: The Brain | 5: Calendar, Company, Connections, Obligations, The Brain | 5: Calendar, The Brain, Obligations, Company, Team | 4: Calendar 4.5, The Brain 3.4, Connections 4.6, The SmartDesign Standard 25.3 |
| Crew (Alberto) | 3 | 0 | 0 | 1: Connections | 0 | 1: The SmartDesign Standard 29.8 |
| Driver (Alex) | 3 | 0 | 0 | 1: Connections | 0 | 1: The SmartDesign Standard 29.8 |

## 6. Page by Page, in Full

Every page the primary role reaches, as it opens, then each of its tabs. Heights are in screens of that device (900px desktop, 844px phone); "above the fold" is above the bottom bar on the phone.

### Owner, desktop

- reached by: Company (1 tap); first button "Renewals Due 1 licenses, insurance, leas"; shot [desktop](../../review/census/company/shots/desktop_owner_company.jpg)
- **Company** (`ovoffice`): heading "Company", 0.7 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
  - lead: "What the firm has promised to renew and what the meetings left for somebody to answer."
  - figures: Renewals Due 1; Meetings to Review 2; Not Matched 0; Changes to Approve 3
  - records: 3 approvals, 2 meetings, 1 obligations
  - columns: table: KIND, WHAT, PARTY, DATE, STATUS, THEN (6 rows)
  - fields: Search…
- reached by: Company › Calendar (2 taps); first button "Copy as ICS"; shot [desktop](../../review/census/company/shots/desktop_owner_calendar.jpg)
- **Calendar** (`calendar`): heading "Calendar", 1.7 screens tall, 1 sections (1 above the fold), 6 tab screens; blue: none
  - lead: "Everything dated in the ERP on one page — meetings, escalations, decisions, deliveries, inspections, renewals, milestones · Google Calendar syncs both ways on t"
  - sections: This Month (26)
  - records: 10 to-dos, 8 decisions, 1 inspections, 1 materials, 1 purchase orders, 1 files, 1 vendors, 1 obligations
  - tab groups: All / Task 10 / Decision 8 / Inspection 1 / Milestone 5 / Delivery 1 / Expiry 1
  - tab **Task**: heading "Calendar", 1 sections; 10 to-dos
  - tab **Decision**: heading "Calendar", 1 sections; 8 decisions, 1 materials
  - tab **Inspection**: heading "Calendar", 1 sections; 1 inspections
  - tab **Milestone**: heading "Calendar", 1 sections
  - tab **Delivery**: heading "Calendar", 1 sections; 1 purchase orders, 1 files, 1 vendors
  - tab **Expiry**: heading "Calendar", 1 sections; 1 obligations
- reached by: Company › Team (2 taps); first button "Edit"; shot [desktop](../../review/census/company/shots/desktop_owner_team.jpg)
- **Team** (`team`): heading "Team", 1.4 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
  - lead: "Everyone at the firm, with their phone and email. Message them here, or pick them in any email's To and Cc."
  - fields: Search the team
  - empty states: "no email on file"; "no phone on file · no email on file"; "no phone on file"
- reached by: Company › The Brain (2 taps); first button "Chat"; shot [desktop](../../review/census/company/shots/desktop_owner_the_brain.jpg)
- **The Brain** (`pa`): heading "The Brain", 5.2 screens tall, 6 sections (1 above the fold), 11 tab screens; blue: Approve; opens `pa` when asked for `brain`
  - lead: "What the firm has learned and proposes, and what each person's assistant may do on its own. Only you see this."
  - sections: Approval Rules, Everyone; The Brain; Lessons to Approve (9); Seen Today (18); Rules Fired Today (0); Thresholds the Checklists Enforce
  - figures: Events Seen Today 18; Lessons Proposed Today 9; Rules Fired Today 0; Changes Drafted Today 3
  - records: 5 vendors, 4 approvals, 4 bank and card lines, 2 schedule lines, 2 COI lapses, 2 meetings, 1 site questions, 1 bills
  - fields: Whose Rules Owner (you) Alan · the PM Ch
  - empty states: "No rule fired today."
  - tab groups: Chat / Findings 38 / Activity / Brain Settings; Act Alone / Ask First / Hand It to Me; Act Alone / Ask First / Hand It to Me; Act Alone / Ask First / Hand It to Me
  - tab **Chat**: heading "Ask", 1 sections; 2 vendors, 1 to-dos, 1 schedule lines, 1 COI lapses
  - tab **Findings**: heading "Chief of Staff", 9 sections; 4 decisions, 1 to-dos, 1 schedule lines, 1 files
  - tab **Findings › For You**: heading "Ask", 1 sections; 22 money flags, 3 vendors, 3 to-dos, 3 bank and card lines
  - tab **Findings › Checklist**: heading "Ask", 13 sections; 14 findings, 6 money flags, 4 leads, 4 contacts
  - tab **Activity**: heading "Ask", 4 sections
  - tab **Activity › On Its Own**: heading "Ask", 4 sections
  - tab **Activity › Proposed**: heading "Ask", 4 sections
  - tab **Activity › Decided**: heading "Ask", 4 sections
  - tab **Activity › Handed to You**: heading "Ask", 4 sections
  - tab **Act Alone**: heading "The Brain", 6 sections; 5 vendors, 4 approvals, 4 bank and card lines, 2 schedule lines
  - tab **Hand It to Me**: heading "The Brain", 6 sections; 5 vendors, 4 approvals, 4 bank and card lines, 2 schedule lines
- reached by: Company › Obligations (2 taps); first button "New Obligation"; shot [desktop](../../review/census/company/shots/desktop_owner_obligations.jpg)
- **Obligations** (`obligations`): heading "Obligations", 1.0 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Obligation
  - lead: "Policies, permits, filings, warranties and licenses — with the renewal on the calendar 30 days ahead, by rule."
  - figures: Lapsed 1; Renew Now 1; Active 10; Premiums $10,550
  - records: 5 vendors, 5 obligations, 1 COI lapses
  - columns: table: KIND, OBLIGATION, WITH, COVERS, EXPIRES, OWNER, STATUS (10 rows)
- reached by: Settings (1 tap); first button "Company Settings users, entities, approv"; shot [desktop](../../review/census/company/shots/desktop_owner_settings.jpg)
- **Settings** (`setup`): heading "Settings", 0.6 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: none
  - lead: "The firm's setup, your connected accounts, the team's problem reports and your own data — one place."
  - sections: Live Jobs Demo
- reached by: Settings › Connections (2 taps); first button "Import Statement"; shot [desktop](../../review/census/company/shots/desktop_owner_connections.jpg)
- **Connections** (`conn`): heading "Connections", 3.5 screens tall, 4 sections (2 above the fold), 2 tab screens; blue: none
  - lead: "Your assistant reads what you connect here and keeps checking it. Each person connects their own account — what arrives in your mail is yours, and nobody else's"
  - sections: Bank Feeds & Statements; Google — Owner; Setting the Firm Up — Once, for Everybody; What My Assistant May Do for Me
  - fields: …apps.googleusercontent.com, mercerandbond.com, gc-every, Whose Rules Owner (you) Alan · the PM Ch
  - tab groups: Act Alone / Ask First / Hand It to Me; Act Alone / Ask First / Hand It to Me; Act Alone / Ask First / Hand It to Me; Act Alone / Ask First / Hand It to Me
  - tab **Act Alone**: heading "Connections", 4 sections
  - tab **Hand It to Me**: heading "Connections", 4 sections
- reached by: Settings › The SmartDesign Standard (2 taps); first button "Edit the Standard"; shot [desktop](../../review/census/company/shots/desktop_owner_the_smartdesign_standard.jpg)
- **The SmartDesign Standard** (`standard`): heading "The SmartDesign Standard", 11.0 screens tall, 59 sections (2 above the fold), 0 tab screens; blue: none
  - lead: "Values, principles and standards — for every employee, agent and assistant. Version 1, Alan Mishali, Thu, Sep 3. Every assistant, background job and the brain w"
  - sections: Standard Watch; Not Measured Yet; How to Use This Document; Who We Are; Core Values; 1. OWN IT; 2. THE CLIENT COMES FIRST; 3. CRAFT WITHOUT COMPROMISE; 4. THINK AHEAD; 5. EVERY DOLLAR MATTERS; 6. TRUTH, EARLY; 7. ONE TEAM; Decision Principles; THE FOUR TESTS; DECIDE OR ESCALATE; Company-Wide Standards and 43 more
  - records: 2 to-dos
  - empty states: "None today"; "No purchase without a PO Money standard · Coordinator"
- reached by: Settings › Problem Reports (2 taps); first button "Copy All for the Developer"; shot [desktop](../../review/census/company/shots/desktop_owner_problem_reports.jpg)
- **Problem Reports** (`rpbox`): heading "Problem Reports", 0.5 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: none
  - lead: "Nothing reported yet. The Report a Problem button is on every screen, for every role."
  - figures: Someone Is Stuck 0; Still Open 0; Most Common —; Waiting on a Word 0; People Reporting 0
  - empty states: "Nothing reported yet. The Report a Problem button is on every screen, for every role."; "No reports yet. Ask the team to press Report a Problem the moment something is wrong — it takes one "
  - tab groups: Open / New / Accepted / Fixed / Everything
  - tab **Accepted**: heading "Problem Reports", 0 sections
  - tab **Fixed**: heading "Problem Reports", 0 sections
  - tab **Everything**: heading "Problem Reports", 0 sections
  - tabs that would not press (the row changed once one was pressed): New
- reached by: Settings › Your Own Data (2 taps); first button "Save a Backup"; shot [desktop](../../review/census/company/shots/desktop_owner_your_own_data.jpg)
- **Your Own Data** (`rdata`): heading "Your Own Data", 1.1 screens tall, 4 sections (3 above the fold), 3 tab screens; blue: none
  - lead: "4 of these are the demo — invented jobs made to show what every screen does. Before the team uses it for real, put your own in and take the demo out."
  - sections: Import from Asana; Bring in What You Already Have; Move This Device's Data; Take the Demo Out
  - figures: Projects 4; Clients 6; Vendors and Subs 12; People 9
  - fields: Project Name Client Address Contract $ S
  - tab groups: Projects / Clients / Vendors and Subs / People
  - tab **Clients**: heading "Your Own Data", 4 sections
  - tab **Vendors and Subs**: heading "Your Own Data", 4 sections
  - tab **People**: heading "Your Own Data", 4 sections
- reached by: Settings › Sales Settings (2 taps); first button "Pipelines"; shot [desktop](../../review/census/company/shots/desktop_owner_sales_settings.jpg)
- **Sales Settings** (`hbsettings`): heading "Sales Settings", 0.7 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: Save
  - lead: "Pipelines, properties, products and the tools behind Sales."
  - sections: SETTINGS; MORE TOOLS
  - columns: table: STAGE NAME, WIN PROBABILITY, WON / LOST, UPDATE STAGE PROPERTIES (7 rows)
  - fields: Pipeline, Stage Name — , Win Probability — , Won / Lost — 
  - empty states: "None"
  - tab groups: Pipelines / Properties / Record Customization / Products / Users & Teams
- reached by: Settings › link: Company Settings users, entities, approv; first button "Project Settings"; shot [desktop](../../review/census/company/shots/desktop_owner_company_settings.jpg)
- **Company Settings** (`proj`): heading "Settings", 8.7 screens tall, 16 sections (2 above the fold), 0 tab screens; blue: Save
  - lead: "Users, entities, approval rules, the company block, the library, appearance, data."
  - sections: The Firm's Clock; Users & Roles; Legal Entities (4); Appearance; Purchasing, Budgets & Overhead; Accounting; Item Library; PROPOSED FROM USE 7; Approval & Verification Rules; Company (Appears on Estimates, Change Orders and Invoices); Client Documents: Letterhead and How to Pay; Data; Change Log; What the Assistant May Do; Backlog — Agreed, Not Yet Built; How the Schedule Logic Works
  - records: 9 materials, 6 schedule lines, 3 clients, 3 purchase orders, 3 files, 3 vendors, 2 meetings
  - columns: Item Library: ITEM, COST CODE, UNIT, PRICE, UNIT COST, LAST BOUGHT, USED (99 rows)
  - fields: Timezone, As Of, Owner's language, Alan's language, Chen Biron's language, Angel's language, Alberto's language, Satish's language, Alex's language, Sarah Klein's language, Rachel (M&B acquisitions)'s language, Priya (M&B analyst)'s language
  - empty states: "Nothing is ordered without a PO"
  - tab groups: Color / Mono

### Owner, phone

- reached by: menu › Company (2 taps); first button "Renewals Due 1"; shot [phone](../../review/census/company/shots/phone_owner_company.jpg)
- **Company** (`ovoffice`): heading "Company", 0.9 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
  - lead: "What the firm has promised to renew and what the meetings left for somebody to answer."
  - figures: Renewals Due 1; Meetings to Review 2; Not Matched 0; Changes to Approve 3
  - records: 3 approvals, 2 meetings, 1 obligations
  - columns: table: Kind, What, Party, Date, Status, Then (6 rows)
  - fields: Search…
- reached by: menu › Company › Calendar (3 taps); first button "Copy as ICS"; shot [phone](../../review/census/company/shots/phone_owner_calendar.jpg)
- **Calendar** (`calendar`): heading "Calendar", 4.5 screens tall, 1 sections (0 above the fold), 6 tab screens; blue: none
  - lead: "Everything dated in the ERP on one page — meetings, escalations, decisions, deliveries, inspections, renewals, milestones · Google Calendar syncs both ways on t"
  - sections: This Month (26)
  - records: 10 to-dos, 8 decisions, 1 inspections, 1 materials, 1 purchase orders, 1 files, 1 vendors, 1 obligations
  - tab groups: All / Task 10 / Decision 8 / Inspection 1 / Milestone 5 / Delivery 1 / Expiry 1
  - tab **Task**: heading "Calendar", 1 sections; 10 to-dos
  - tab **Decision**: heading "Calendar", 1 sections; 8 decisions, 1 materials
  - tab **Inspection**: heading "Calendar", 1 sections; 1 inspections
  - tab **Milestone**: heading "Calendar", 1 sections
  - tab **Delivery**: heading "Calendar", 1 sections; 1 purchase orders, 1 files, 1 vendors
  - tab **Expiry**: heading "Calendar", 1 sections; 1 obligations
- reached by: menu › Company › Team (3 taps); first button "Edit"; shot [phone](../../review/census/company/shots/phone_owner_team.jpg)
- **Team** (`team`): heading "Team", 2.3 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
  - lead: "Everyone at the firm, with their phone and email. Message them here, or pick them in any email's To and Cc."
  - fields: Search the team
  - empty states: "no email on file"; "no phone on file · no email on file"; "no phone on file"
- reached by: menu › Company › swipe the strip, The Brain (3 taps); first button "Chat"; shot [phone](../../review/census/company/shots/phone_owner_the_brain.jpg)
- **The Brain** (`pa`): heading "The Brain", 7.2 screens tall, 6 sections (1 above the fold), 1 tab screens; blue: none; opens `pa` when asked for `brain`; runs past the edge: cut off by pr-m (A reminder for the coordinator: Text eac, A process step for the PM: An extra from)
  - lead: "What the firm has learned and proposes, and what each person's assistant may do on its own. Only you see this."
  - sections: Approval Rules, Everyone; The Brain; Lessons to Approve (9); Seen Today (18); Rules Fired Today (0); Thresholds the Checklists Enforce
  - figures: Events Seen Today 18; Lessons Proposed Today 9; Rules Fired Today 0; Changes Drafted Today 3
  - records: 5 vendors, 4 bank and card lines, 3 approvals, 2 schedule lines, 2 COI lapses, 2 meetings, 1 site questions, 1 bills
  - fields: Whose Rules Owner (you) Alan · the PM Ch
  - empty states: "No rule fired today."
  - tab groups: Chat / Findings 38 / Activity / Brain Settings; Act Alone / Ask First / Hand It to Me; Act Alone / Ask First / Hand It to Me; Act Alone / Ask First / Hand It to Me
  - tab **Chat**: heading "Ask", 0 sections; 2 vendors, 1 to-dos, 1 schedule lines, 1 COI lapses
  - tabs that would not press (the row changed once one was pressed): Findings, Activity, Act Alone, Hand It to Me
- reached by: menu › Company › swipe the strip, Obligations (3 taps); first button "New Obligation"; shot [phone](../../review/census/company/shots/phone_owner_obligations.jpg)
- **Obligations** (`obligations`): heading "Obligations", 1.3 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Obligation
  - lead: "Policies, permits, filings, warranties and licenses — with the renewal on the calendar 30 days ahead, by rule."
  - figures: Lapsed 1; Renew Now 1; Active 10; Premiums $10,550
  - records: 5 vendors, 5 obligations, 1 COI lapses
  - columns: table: Kind, Obligation, With, Covers, Expires, Owner, Status (10 rows)
- reached by: menu › Settings (2 taps); first button "Company Settings"; shot [phone](../../review/census/company/shots/phone_owner_settings.jpg)
- **Settings** (`setup`): heading "Settings", 0.5 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: none
  - lead: "The firm's setup, your connected accounts, the team's problem reports and your own data — one place."
  - sections: Live Jobs Demo
- reached by: menu › Settings › Connections (3 taps); first button "Import Statement"; shot [phone](../../review/census/company/shots/phone_owner_connections.jpg)
- **Connections** (`conn`): heading "Connections", 5.5 screens tall, 4 sections (2 above the fold), 2 tab screens; blue: none
  - lead: "Your assistant reads what you connect here and keeps checking it. Each person connects their own account — what arrives in your mail is yours, and nobody else's"
  - sections: Bank Feeds & Statements; Google — Owner; Setting the Firm Up — Once, for Everybody; What My Assistant May Do for Me
  - fields: …apps.googleusercontent.com, mercerandbond.com, gc-every, Whose Rules Owner (you) Alan · the PM Ch
  - tab groups: Act Alone / Ask First / Hand It to Me; Act Alone / Ask First / Hand It to Me; Act Alone / Ask First / Hand It to Me; Act Alone / Ask First / Hand It to Me
  - tab **Act Alone**: heading "Connections", 4 sections
  - tab **Hand It to Me**: heading "Connections", 4 sections
- reached by: menu › Settings › The SmartDesign Standard (3 taps); first button "Edit the Standard"; shot [phone](../../review/census/company/shots/phone_owner_the_smartdesign_standard.jpg)
- **The SmartDesign Standard** (`standard`): heading "The SmartDesign Standard", 25.3 screens tall, 59 sections (1 above the fold), 0 tab screens; blue: none
  - lead: "Values, principles and standards — for every employee, agent and assistant. Version 1, Alan Mishali, Thu, Sep 3. Every assistant, background job and the brain w"
  - sections: Standard Watch; Not Measured Yet; How to Use This Document; Who We Are; Core Values; 1. OWN IT; 2. THE CLIENT COMES FIRST; 3. CRAFT WITHOUT COMPROMISE; 4. THINK AHEAD; 5. EVERY DOLLAR MATTERS; 6. TRUTH, EARLY; 7. ONE TEAM; Decision Principles; THE FOUR TESTS; DECIDE OR ESCALATE; Company-Wide Standards and 43 more
  - records: 2 to-dos
  - empty states: "None today"; "No purchase without a PO Money standard · Coordinator"
- reached by: menu › Settings › swipe the strip, Problem Reports (3 taps); first button "Copy All for the Developer"; shot [phone](../../review/census/company/shots/phone_owner_problem_reports.jpg)
- **Problem Reports** (`rpbox`): heading "Problem Reports", 0.6 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: none
  - lead: "Nothing reported yet. The Report a Problem button is on every screen, for every role."
  - figures: Someone Is Stuck 0; Still Open 0; Most Common —; Waiting on a Word 0; People Reporting 0
  - empty states: "No reports yet. Ask the team to press Report a Problem the moment something is wrong — it takes one "
  - tab groups: Open / New / Accepted / Fixed / Everything
  - tab **Accepted**: heading "Problem Reports", 0 sections
  - tab **Fixed**: heading "Problem Reports", 0 sections
  - tab **Everything**: heading "Problem Reports", 0 sections
  - tabs that would not press (the row changed once one was pressed): New
- reached by: menu › Settings › swipe the strip, Your Own Data (3 taps); first button "Save a Backup"; shot [phone](../../review/census/company/shots/phone_owner_your_own_data.jpg)
- **Your Own Data** (`rdata`): heading "Your Own Data", 1.9 screens tall, 4 sections (2 above the fold), 3 tab screens; blue: none
  - lead: "4 of these are the demo — invented jobs made to show what every screen does. Before the team uses it for real, put your own in and take the demo out."
  - sections: Import from Asana; Bring in What You Already Have; Move This Device's Data; Take the Demo Out
  - figures: Projects 4; Clients 6; Vendors and Subs 12; People 9
  - fields: Project Name Client Address Contract $ S
  - tab groups: Projects / Clients / Vendors and Subs / People
  - tab **Clients**: heading "Your Own Data", 4 sections
  - tab **Vendors and Subs**: heading "Your Own Data", 4 sections
  - tab **People**: heading "Your Own Data", 4 sections
- reached by: menu › Settings › swipe the strip, Sales Settings (3 taps); first button "Pipelines"; shot [phone](../../review/census/company/shots/phone_owner_sales_settings.jpg)
- **Sales Settings** (`hbsettings`): heading "Sales Settings", 1.0 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: Save
  - lead: "Pipelines, properties, products and the tools behind Sales."
  - columns: table: Stage Name, Win Probability, Won / Lost, Update Stage Properties (7 rows)
  - fields: Pipeline
  - empty states: "None Delete None Delete None Delete Value Delete Value, Close Date Delete None Closed lost reason"; "None Delete"; "None"
  - tab groups: Pipelines / Properties / Record Customization / Products / Users & Teams
- reached by: Settings › link: Company Settings; first button "Project Settings"; shot [phone](../../review/census/company/shots/phone_owner_company_settings.jpg)
- **Company Settings** (`proj`): heading "Settings", 12.6 screens tall, 16 sections (2 above the fold), 0 tab screens; blue: Save; runs past the edge: cut off by [object (path.[object); cut off by v-proj (English Español (in review), sarah.klein@example.com · Sarah & David )
  - lead: "Users, entities, approval rules, the company block, the library, appearance, data."
  - sections: The Firm's Clock; Users & Roles; Legal Entities (4); Appearance; Purchasing, Budgets & Overhead; Accounting; Item Library; PROPOSED FROM USE 7; Approval & Verification Rules; Company (Appears on Estimates, Change Orders and Invoices); Client Documents: Letterhead and How to Pay; Data; Change Log; What the Assistant May Do; Backlog — Agreed, Not Yet Built; How the Schedule Logic Works
  - records: 9 materials, 6 schedule lines, 3 clients, 3 purchase orders, 3 files, 3 vendors, 2 meetings
  - columns: Item Library: Item, Cost Code, Unit, Price, Unit Cost, Last Bought, Used (99 rows)
  - fields: Timezone, As Of, Owner's language, Alan's language, Chen Biron's language, Angel's language, Alberto's language, Satish's language, Alex's language, Sarah Klein's language, Rachel (M&B acquisitions)'s language, Priya (M&B analyst)'s language
  - empty states: "Nothing is ordered without a PO"
  - tab groups: Color / Mono

## 7. The Other Roles, One Line a Page

### PM (Alan), desktop

- reached by: Company (1 tap); shot [desktop](../../review/census/company/shots/desktop_pm_company.jpg)
- **Company** (`ovoffice`): heading "Company", 0.5 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- reached by: Company › Calendar (2 taps); shot [desktop](../../review/census/company/shots/desktop_pm_calendar.jpg)
- **Calendar** (`calendar`): heading "Calendar", 1.7 screens tall, 1 sections (1 above the fold), 6 tab screens; blue: none
- reached by: Company › Team (2 taps); shot [desktop](../../review/census/company/shots/desktop_pm_team.jpg)
- **Team** (`team`): heading "Team", 1.4 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- reached by: Company › The Brain (2 taps); shot [desktop](../../review/census/company/shots/desktop_pm_the_brain.jpg)
- **The Brain** (`pa`): heading "The Brain", 3.0 screens tall, 4 sections (2 above the fold), 17 tab screens; blue: none; opens `pa` when asked for `brain`
- reached by: Company › Obligations (2 taps); shot [desktop](../../review/census/company/shots/desktop_pm_obligations.jpg)
- **Obligations** (`obligations`): heading "Obligations", 1.0 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Obligation
- reached by: Settings (1 tap); shot [desktop](../../review/census/company/shots/desktop_pm_settings.jpg)
- **Settings** (`setup`): heading "Settings", 0.4 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- reached by: Settings › Connections (2 taps); shot [desktop](../../review/census/company/shots/desktop_pm_connections.jpg)
- **Connections** (`conn`): heading "Connections", 3.3 screens tall, 4 sections (2 above the fold), 2 tab screens; blue: none
- reached by: Settings › The SmartDesign Standard (2 taps); shot [desktop](../../review/census/company/shots/desktop_pm_the_smartdesign_standard.jpg)
- **The SmartDesign Standard** (`standard`): heading "The SmartDesign Standard", 11.0 screens tall, 59 sections (2 above the fold), 0 tab screens; blue: none
- reached by: Settings › Problem Reports (2 taps); shot [desktop](../../review/census/company/shots/desktop_pm_problem_reports.jpg)
- **Problem Reports** (`rpbox`): heading "Problem Reports", 0.5 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: none
- reached by: Settings › Sales Settings (2 taps); shot [desktop](../../review/census/company/shots/desktop_pm_sales_settings.jpg)
- **Sales Settings** (`hbsettings`): heading "Sales Settings", 0.7 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: Save
- reached by: Settings › link: Company Settings users, entities, approv; shot [desktop](../../review/census/company/shots/desktop_pm_company_settings.jpg)
- **Company Settings** (`proj`): heading "Settings", 8.0 screens tall, 14 sections (2 above the fold), 0 tab screens; blue: Save

### PM (Alan), phone

- reached by: menu › Company (2 taps); shot [phone](../../review/census/company/shots/phone_pm_company.jpg)
- **Company** (`ovoffice`): heading "Company", 0.6 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- reached by: menu › Company › Calendar (3 taps); shot [phone](../../review/census/company/shots/phone_pm_calendar.jpg)
- **Calendar** (`calendar`): heading "Calendar", 4.5 screens tall, 1 sections (0 above the fold), 6 tab screens; blue: none
- reached by: menu › Company › Team (3 taps); shot [phone](../../review/census/company/shots/phone_pm_team.jpg)
- **Team** (`team`): heading "Team", 2.3 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- reached by: menu › Company › swipe the strip, The Brain (3 taps); shot [phone](../../review/census/company/shots/phone_pm_the_brain.jpg)
- **The Brain** (`pa`): heading "The Brain", 3.4 screens tall, 4 sections (2 above the fold), 1 tab screens; blue: none; opens `pa` when asked for `brain`; runs past the edge: cut off by pr-m (A reminder for the coordinator: Text eac, A process step for the PM: An extra from)
- reached by: menu › Company › swipe the strip, Obligations (3 taps); shot [phone](../../review/census/company/shots/phone_pm_obligations.jpg)
- **Obligations** (`obligations`): heading "Obligations", 1.3 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Obligation
- reached by: menu › Settings (2 taps); shot [phone](../../review/census/company/shots/phone_pm_settings.jpg)
- **Settings** (`setup`): heading "Settings", 0.3 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none; nearly empty (10 words)
- reached by: menu › Settings › Connections (3 taps); shot [phone](../../review/census/company/shots/phone_pm_connections.jpg)
- **Connections** (`conn`): heading "Connections", 5.2 screens tall, 4 sections (2 above the fold), 2 tab screens; blue: none
- reached by: menu › Settings › The SmartDesign Standard (3 taps); shot [phone](../../review/census/company/shots/phone_pm_the_smartdesign_standard.jpg)
- **The SmartDesign Standard** (`standard`): heading "The SmartDesign Standard", 25.3 screens tall, 59 sections (1 above the fold), 0 tab screens; blue: none
- reached by: menu › Settings › swipe the strip, Problem Reports (3 taps); shot [phone](../../review/census/company/shots/phone_pm_problem_reports.jpg)
- **Problem Reports** (`rpbox`): heading "Problem Reports", 0.6 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: none
- reached by: menu › Settings › swipe the strip, Sales Settings (3 taps); shot [phone](../../review/census/company/shots/phone_pm_sales_settings.jpg)
- **Sales Settings** (`hbsettings`): heading "Sales Settings", 1.0 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: Save
- reached by: Settings › link: Company Settings; shot [phone](../../review/census/company/shots/phone_pm_company_settings.jpg)
- **Company Settings** (`proj`): heading "Settings", 11.6 screens tall, 14 sections (2 above the fold), 0 tab screens; blue: Save; runs past the edge: cut off by [object (path.[object); cut off by v-proj (English Español (in review), sarah.klein@example.com · Sarah & David )

### Coordinator (Chen), desktop

- reached by: Company (1 tap); shot [desktop](../../review/census/company/shots/desktop_coord_company.jpg)
- **Company** (`ovoffice`): heading "Company", 0.5 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- reached by: Company › Calendar (2 taps); shot [desktop](../../review/census/company/shots/desktop_coord_calendar.jpg)
- **Calendar** (`calendar`): heading "Calendar", 1.7 screens tall, 1 sections (1 above the fold), 6 tab screens; blue: none
- reached by: Company › Team (2 taps); shot [desktop](../../review/census/company/shots/desktop_coord_team.jpg)
- **Team** (`team`): heading "Team", 1.4 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- reached by: Company › The Brain (2 taps); shot [desktop](../../review/census/company/shots/desktop_coord_the_brain.jpg)
- **The Brain** (`pa`): heading "The Brain", 3.0 screens tall, 4 sections (2 above the fold), 17 tab screens; blue: none; opens `pa` when asked for `brain`
- reached by: Company › Obligations (2 taps); shot [desktop](../../review/census/company/shots/desktop_coord_obligations.jpg)
- **Obligations** (`obligations`): heading "Obligations", 1.0 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Obligation
- reached by: Settings (1 tap); shot [desktop](../../review/census/company/shots/desktop_coord_connections.jpg)
- **Connections** (`conn`): heading "Connections", 3.4 screens tall, 4 sections (2 above the fold), 2 tab screens; blue: none
- reached by: Settings › The SmartDesign Standard (2 taps); shot [desktop](../../review/census/company/shots/desktop_coord_the_smartdesign_standard.jpg)
- **The SmartDesign Standard** (`standard`): heading "The SmartDesign Standard", 11.0 screens tall, 59 sections (2 above the fold), 0 tab screens; blue: none
- reached by: Settings › Your Own Data (2 taps); shot [desktop](../../review/census/company/shots/desktop_coord_your_own_data.jpg)
- **Your Own Data** (`rdata`): heading "Your Own Data", 0.4 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: none
- reached by: Settings › Sales Settings (2 taps); shot [desktop](../../review/census/company/shots/desktop_coord_sales_settings.jpg)
- **Sales Settings** (`hbsettings`): heading "Sales Settings", 0.7 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: Save

### Coordinator (Chen), phone

- reached by: menu › Company (2 taps); shot [phone](../../review/census/company/shots/phone_coord_company.jpg)
- **Company** (`ovoffice`): heading "Company", 0.6 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- reached by: menu › Company › Calendar (3 taps); shot [phone](../../review/census/company/shots/phone_coord_calendar.jpg)
- **Calendar** (`calendar`): heading "Calendar", 4.5 screens tall, 1 sections (0 above the fold), 6 tab screens; blue: none
- reached by: menu › Company › Team (3 taps); shot [phone](../../review/census/company/shots/phone_coord_team.jpg)
- **Team** (`team`): heading "Team", 2.3 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- reached by: menu › Company › swipe the strip, The Brain (3 taps); shot [phone](../../review/census/company/shots/phone_coord_the_brain.jpg)
- **The Brain** (`pa`): heading "The Brain", 3.4 screens tall, 4 sections (2 above the fold), 1 tab screens; blue: none; opens `pa` when asked for `brain`; runs past the edge: cut off by pr-m (A reminder for the coordinator: Text eac, A process step for the PM: An extra from)
- reached by: menu › Company › swipe the strip, Obligations (3 taps); shot [phone](../../review/census/company/shots/phone_coord_obligations.jpg)
- **Obligations** (`obligations`): heading "Obligations", 1.3 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Obligation
- reached by: menu › Settings (2 taps); shot [phone](../../review/census/company/shots/phone_coord_connections.jpg)
- **Connections** (`conn`): heading "Connections", 5.4 screens tall, 4 sections (2 above the fold), 2 tab screens; blue: none
- reached by: menu › Settings › The SmartDesign Standard (3 taps); shot [phone](../../review/census/company/shots/phone_coord_the_smartdesign_standard.jpg)
- **The SmartDesign Standard** (`standard`): heading "The SmartDesign Standard", 25.3 screens tall, 59 sections (1 above the fold), 0 tab screens; blue: none
- reached by: menu › Settings › swipe the strip, Your Own Data (3 taps); shot [phone](../../review/census/company/shots/phone_coord_your_own_data.jpg)
- **Your Own Data** (`rdata`): heading "Your Own Data", 0.6 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: none
- reached by: menu › Settings › swipe the strip, Sales Settings (3 taps); shot [phone](../../review/census/company/shots/phone_coord_sales_settings.jpg)
- **Sales Settings** (`hbsettings`): heading "Sales Settings", 1.0 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: Save

### Foreman (Angel), desktop

- reached by: Team (1 tap); shot [desktop](../../review/census/company/shots/desktop_foreman_team.jpg)
- **Team** (`team`): heading "Team", 1.4 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- reached by: Connections (1 tap); shot [desktop](../../review/census/company/shots/desktop_foreman_connections.jpg)
- **Connections** (`conn`): heading "Connections", 1.3 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: none
- reached by: The SmartDesign Standard (1 tap); shot [desktop](../../review/census/company/shots/desktop_foreman_the_smartdesign_standard.jpg)
- **The SmartDesign Standard** (`standard`): heading "The SmartDesign Standard", 11.0 screens tall, 59 sections (2 above the fold), 0 tab screens; blue: none

### Foreman (Angel), phone

- reached by: menu › Team (2 taps); shot [phone](../../review/census/company/shots/phone_foreman_team.jpg)
- **Team** (`team`): heading "Team", 2.4 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- reached by: menu › Connections (2 taps); shot [phone](../../review/census/company/shots/phone_foreman_connections.jpg)
- **Connections** (`conn`): heading "Connections", 2.2 screens tall, 2 sections (1 above the fold), 0 tab screens; blue: none
- reached by: menu › The SmartDesign Standard (2 taps); shot [phone](../../review/census/company/shots/phone_foreman_the_smartdesign_standard.jpg)
- **The SmartDesign Standard** (`standard`): heading "The SmartDesign Standard", 29.8 screens tall, 59 sections (1 above the fold), 0 tab screens; blue: none

### Designer (Sarah), desktop

- reached by: More (1 tap); shot [desktop](../../review/census/company/shots/desktop_designer_team.jpg)
- **Team** (`team`): heading "Team", 1.4 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- reached by: Settings (1 tap); shot [desktop](../../review/census/company/shots/desktop_designer_connections.jpg)
- **Connections** (`conn`): heading "Connections", 3.1 screens tall, 4 sections (2 above the fold), 2 tab screens; blue: none
- reached by: Settings › The SmartDesign Standard (2 taps); shot [desktop](../../review/census/company/shots/desktop_designer_the_smartdesign_standard.jpg)
- **The SmartDesign Standard** (`standard`): heading "The SmartDesign Standard", 11.0 screens tall, 59 sections (2 above the fold), 0 tab screens; blue: none

### Designer (Sarah), phone

- reached by: menu › More (2 taps); shot [phone](../../review/census/company/shots/phone_designer_team.jpg)
- **Team** (`team`): heading "Team", 2.3 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- reached by: menu › Settings (2 taps); shot [phone](../../review/census/company/shots/phone_designer_connections.jpg)
- **Connections** (`conn`): heading "Connections", 4.7 screens tall, 4 sections (2 above the fold), 2 tab screens; blue: none
- reached by: menu › Settings › The SmartDesign Standard (3 taps); shot [phone](../../review/census/company/shots/phone_designer_the_smartdesign_standard.jpg)
- **The SmartDesign Standard** (`standard`): heading "The SmartDesign Standard", 25.3 screens tall, 59 sections (1 above the fold), 0 tab screens; blue: none

### Billing, desktop

- reached by: More › Team (2 taps); shot [desktop](../../review/census/company/shots/desktop_billing_team.jpg)
- **Team** (`team`): heading "Team", 1.4 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- reached by: Settings (1 tap); shot [desktop](../../review/census/company/shots/desktop_billing_connections.jpg)
- **Connections** (`conn`): heading "Connections", 3.2 screens tall, 4 sections (2 above the fold), 2 tab screens; blue: none
- reached by: Settings › The SmartDesign Standard (2 taps); shot [desktop](../../review/census/company/shots/desktop_billing_the_smartdesign_standard.jpg)
- **The SmartDesign Standard** (`standard`): heading "The SmartDesign Standard", 11.0 screens tall, 59 sections (2 above the fold), 0 tab screens; blue: none
- reached by: Settings › Sales Settings (2 taps); shot [desktop](../../review/census/company/shots/desktop_billing_sales_settings.jpg)
- **Sales Settings** (`hbsettings`): heading "Sales Settings", 0.7 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: Save

### Billing, phone

- reached by: menu › More › swipe the strip, Team (3 taps); shot [phone](../../review/census/company/shots/phone_billing_team.jpg)
- **Team** (`team`): heading "Team", 2.3 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- reached by: menu › Settings (2 taps); shot [phone](../../review/census/company/shots/phone_billing_connections.jpg)
- **Connections** (`conn`): heading "Connections", 5.0 screens tall, 4 sections (2 above the fold), 2 tab screens; blue: none
- reached by: menu › Settings › The SmartDesign Standard (3 taps); shot [phone](../../review/census/company/shots/phone_billing_the_smartdesign_standard.jpg)
- **The SmartDesign Standard** (`standard`): heading "The SmartDesign Standard", 25.3 screens tall, 59 sections (1 above the fold), 0 tab screens; blue: none
- reached by: menu › Settings › swipe the strip, Sales Settings (3 taps); shot [phone](../../review/census/company/shots/phone_billing_sales_settings.jpg)
- **Sales Settings** (`hbsettings`): heading "Sales Settings", 1.0 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: Save

### Controller, desktop

- reached by: More › Calendar (2 taps); shot [desktop](../../review/census/company/shots/desktop_controller_calendar.jpg)
- **Calendar** (`calendar`): heading "Calendar", 1.7 screens tall, 1 sections (1 above the fold), 6 tab screens; blue: none
- reached by: More › The Brain (2 taps); shot [desktop](../../review/census/company/shots/desktop_controller_the_brain.jpg)
- **The Brain** (`pa`): heading "The Brain", 3.0 screens tall, 4 sections (2 above the fold), 17 tab screens; blue: none; opens `pa` when asked for `brain`
- reached by: More › Obligations (2 taps); shot [desktop](../../review/census/company/shots/desktop_controller_obligations.jpg)
- **Obligations** (`obligations`): heading "Obligations", 1.0 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Obligation
- reached by: More › Company (2 taps); shot [desktop](../../review/census/company/shots/desktop_controller_company.jpg)
- **Company** (`ovoffice`): heading "Company", 0.5 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- reached by: More › Team (2 taps); shot [desktop](../../review/census/company/shots/desktop_controller_team.jpg)
- **Team** (`team`): heading "Team", 1.4 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- reached by: Settings (1 tap); shot [desktop](../../review/census/company/shots/desktop_controller_settings.jpg)
- **Settings** (`setup`): heading "Settings", 0.3 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- reached by: Settings › Connections (2 taps); shot [desktop](../../review/census/company/shots/desktop_controller_connections.jpg)
- **Connections** (`conn`): heading "Connections", 2.9 screens tall, 4 sections (2 above the fold), 2 tab screens; blue: none
- reached by: Settings › The SmartDesign Standard (2 taps); shot [desktop](../../review/census/company/shots/desktop_controller_the_smartdesign_standard.jpg)
- **The SmartDesign Standard** (`standard`): heading "The SmartDesign Standard", 11.0 screens tall, 59 sections (2 above the fold), 0 tab screens; blue: none

### Controller, phone

- reached by: menu › More › swipe the strip, Calendar (3 taps); shot [phone](../../review/census/company/shots/phone_controller_calendar.jpg)
- **Calendar** (`calendar`): heading "Calendar", 4.5 screens tall, 1 sections (0 above the fold), 6 tab screens; blue: none
- reached by: menu › More › swipe the strip, The Brain (3 taps); shot [phone](../../review/census/company/shots/phone_controller_the_brain.jpg)
- **The Brain** (`pa`): heading "The Brain", 3.4 screens tall, 4 sections (2 above the fold), 1 tab screens; blue: none; opens `pa` when asked for `brain`; runs past the edge: cut off by pr-m (A reminder for the coordinator: Text eac, A process step for the PM: An extra from)
- reached by: menu › More › swipe the strip, Obligations (3 taps); shot [phone](../../review/census/company/shots/phone_controller_obligations.jpg)
- **Obligations** (`obligations`): heading "Obligations", 1.3 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Obligation
- reached by: menu › More › swipe the strip, Company (3 taps); shot [phone](../../review/census/company/shots/phone_controller_company.jpg)
- **Company** (`ovoffice`): heading "Company", 0.6 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- reached by: menu › More › swipe the strip, Team (3 taps); shot [phone](../../review/census/company/shots/phone_controller_team.jpg)
- **Team** (`team`): heading "Team", 2.3 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- reached by: menu › Settings (2 taps); shot [phone](../../review/census/company/shots/phone_controller_settings.jpg)
- **Settings** (`setup`): heading "Settings", 0.3 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none; nearly empty (4 words)
- reached by: menu › Settings › Connections (3 taps); shot [phone](../../review/census/company/shots/phone_controller_connections.jpg)
- **Connections** (`conn`): heading "Connections", 4.6 screens tall, 4 sections (2 above the fold), 2 tab screens; blue: none
- reached by: menu › Settings › The SmartDesign Standard (3 taps); shot [phone](../../review/census/company/shots/phone_controller_the_smartdesign_standard.jpg)
- **The SmartDesign Standard** (`standard`): heading "The SmartDesign Standard", 25.3 screens tall, 59 sections (1 above the fold), 0 tab screens; blue: none

### Crew (Alberto), desktop

- reached by: Team (1 tap); shot [desktop](../../review/census/company/shots/desktop_crew_team.jpg)
- **Team** (`team`): heading "Team", 1.4 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- reached by: Connections (1 tap); shot [desktop](../../review/census/company/shots/desktop_crew_connections.jpg)
- **Connections** (`conn`): heading "Connections", 1.3 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: none
- reached by: The SmartDesign Standard (1 tap); shot [desktop](../../review/census/company/shots/desktop_crew_the_smartdesign_standard.jpg)
- **The SmartDesign Standard** (`standard`): heading "The SmartDesign Standard", 11.0 screens tall, 59 sections (2 above the fold), 0 tab screens; blue: none

### Crew (Alberto), phone

- reached by: menu › Team (2 taps); shot [phone](../../review/census/company/shots/phone_crew_team.jpg)
- **Team** (`team`): heading "Team", 2.4 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- reached by: menu › Connections (2 taps); shot [phone](../../review/census/company/shots/phone_crew_connections.jpg)
- **Connections** (`conn`): heading "Connections", 2.2 screens tall, 2 sections (1 above the fold), 0 tab screens; blue: none
- reached by: menu › The SmartDesign Standard (2 taps); shot [phone](../../review/census/company/shots/phone_crew_the_smartdesign_standard.jpg)
- **The SmartDesign Standard** (`standard`): heading "The SmartDesign Standard", 29.8 screens tall, 59 sections (1 above the fold), 0 tab screens; blue: none

### Driver (Alex), desktop

- reached by: Team (1 tap); shot [desktop](../../review/census/company/shots/desktop_driver_team.jpg)
- **Team** (`team`): heading "Team", 1.4 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- reached by: Connections (1 tap); shot [desktop](../../review/census/company/shots/desktop_driver_connections.jpg)
- **Connections** (`conn`): heading "Connections", 1.3 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: none
- reached by: The SmartDesign Standard (1 tap); shot [desktop](../../review/census/company/shots/desktop_driver_the_smartdesign_standard.jpg)
- **The SmartDesign Standard** (`standard`): heading "The SmartDesign Standard", 11.0 screens tall, 59 sections (2 above the fold), 0 tab screens; blue: none

### Driver (Alex), phone

- reached by: menu › Team (2 taps); shot [phone](../../review/census/company/shots/phone_driver_team.jpg)
- **Team** (`team`): heading "Team", 2.4 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- reached by: menu › Connections (2 taps); shot [phone](../../review/census/company/shots/phone_driver_connections.jpg)
- **Connections** (`conn`): heading "Connections", 2.2 screens tall, 2 sections (1 above the fold), 0 tab screens; blue: none
- reached by: menu › The SmartDesign Standard (2 taps); shot [phone](../../review/census/company/shots/phone_driver_the_smartdesign_standard.jpg)
- **The SmartDesign Standard** (`standard`): heading "The SmartDesign Standard", 29.8 screens tall, 59 sections (1 above the fold), 0 tab screens; blue: none

## 8. What This Census Did Not Check, and How Sure It Is

- **Records are found by their words** (the information map's rule): a record shown as a number, a chart or in other words is not counted, so duplication counts are floors. Names (clients, vendors, leads, contacts, companies, partners) match wherever the name is written, so a page that only mentions a client counts as listing it.
- **Figures** are read from tiles, two-column tables, definition lists and the bold money that leads a note; a figure inside a sentence is not read. Labels are compared with numbers and small words removed, so two different figures with one label show as a disagreement and need a person to judge.
- **Tabs** are rows of two or more buttons with exactly one on. A dropdown that switches the view, a row of toggles, the rows of Settings and Project Settings, and a button that commits (New, Send, Approve...) are never pressed. One level of revealed tabs is walked; a tab group seen once on a page is not walked again from another route to the same page.
- **What opens, not what is two taps away:** a record opened from a row (an invoice, a PO, a bill), "N more" rows, folded cards and sheets are not walked.
- **Ways in are a floor:** a link counts when the element names a page in a data attribute or its onclick; a tap that opens a record (a PO number, a bill) and lands on its page, ⌘K search and Ask are not counted. "One way" means one menu entry and no counted link.
- **The phone menu** is the hamburger at the top left, which opens the same rail as the desktop; the strip under the header scrolls sideways, and an entry past the edge is recorded as "swipe the strip" (the strip also ends in a More button that lists its entries, one more way the census does not count).
- **One job:** job-scoped pages are read on 121 State Street where the role may open it. The Projects census reads two jobs.
- **Each role runs on a fresh app,** as a new device: what a page remembers (a tab, All projects on the phone) starts as a first visit.
- **Not judged:** whether the content is right, what is missing, and what should merge. That is the experts' walk with this census in hand.

