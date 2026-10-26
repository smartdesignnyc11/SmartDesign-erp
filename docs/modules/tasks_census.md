# The Tasks and Messages Module, Page by Page: the Census

**Asked by Alan, 2026-10-26:** "Go through all the modules with screenshots. It's important to understand the format of every page and what's on it." The loop's experts and the client expert walk every page of their module with this in hand in round one of the improvement loop (docs/IMPROVEMENT_LOOP.md).

**What this is.** A machine inventory, not a judgment, in the format of the Projects census (`docs/modules/projects_census.md`). No app code changed. `tests/module_census.py` (its helpers `tests/module_census_js.js` sit on the projects census's reader `tests/census_js.js` and the information map's `tests/ia_js.js`) signs in as each role on a fresh app at 1440 and at 390, reads the role's running menu, and reaches each page of this module the way the person does: the phone bar, or the menu (the hamburger on the phone), the group, then the strip. It presses every tab of every tab group and the tabs those reveal, follows the page's own links to this module's pages the menu did not reach, reads every screen and shoots it. The primary role is every office role; every role whose menu holds a page of this module is walked. Job-scoped pages show **121 State Street** wherever the role may open it.

**Where this module's pages sit.** Tasks (`tkall`) has its own rail entry and is also under Today for the office roles; Messages (`chat`) has its own rail entry, and its Mail tab opens the Inbox (`comms`, in the Today census). Meetings sit in the Company menu group and are walked here.

**Build bd3180c27e33** (master 1cc2eb9), the one build every module census of this round ran on. 236 screens in all. Walked 2026-10-26 06:29 on the demo day (Thu 2026-09-03); the walk of every module took 54.4 minutes. Raw read: `review/census/tasks/data.json`. Every screen per role in tables: `review/census/tasks/tables.md`. Screenshots of every screen, both devices: `review/census/tasks/shots/` (`desktop_` or `phone_`, the role, the page, then the tab; up to 3 desktop or 5 phone screens tall). The first screen of each page is committed; the tabs stay on the machine that ran it.

Run it: `python3 build.py && cd tests && ./slot.sh python3 module_census.py --module tasks` (then `python3 module_census.py --report` rewrites every module's page from data.json).

## Headline

- **Owner: 3 pages with 28 more screens behind their tabs on the desktop (3 pages and 9 tab screens on the phone)**, about 3 desktop screens end to end.
- **PM (Alan): 3 pages with 20 more screens behind their tabs on the desktop (3 pages and 7 tab screens on the phone)**, about 2 desktop screens end to end.
- **Coordinator (Chen): 3 pages with 21 more screens behind their tabs on the desktop (3 pages and 7 tab screens on the phone)**, about 2 desktop screens end to end.
- **Designer (Sarah): 2 pages with 23 more screens behind their tabs on the desktop (2 pages and 4 tab screens on the phone)**, about 1 desktop screen end to end.
- **Billing: 3 pages with 27 more screens behind their tabs on the desktop (3 pages and 8 tab screens on the phone)**, about 2 desktop screens end to end.
- **Controller: 3 pages with 27 more screens behind their tabs on the desktop (3 pages and 8 tab screens on the phone)**, about 2 desktop screens end to end.
- **Pages each role reaches in this module, desktop:** Owner 3, PM 3, Coordinator 3, Foreman 1, Designer 2, Billing 3, Controller 3, Crew 1, Driver 1.
- **Reached only one way** by Coordinator (Chen): Meetings (desktop and phone) (one menu entry, not on the phone bar, and no walked page links to it; section 1).
- **Reached only one way** by Designer (Sarah): Messages (desktop) (one menu entry, not on the phone bar, and no walked page links to it; section 1).
- **Reached only one way** by Billing: Meetings (desktop and phone) (one menu entry, not on the phone bar, and no walked page links to it; section 1).
- **Reached only one way** by Controller: Meetings (desktop and phone) (one menu entry, not on the phone bar, and no walked page links to it; section 1).
- **6 records show on two or more of this module's pages** for Owner on the desktop (2 to-dos, 2 vendors, 1 decisions, 1 materials). "Shop drawings for the parlor bookcases" is on 2: Meetings, Tasks.
- **The same records in other modules** (Owner, desktop): Projects › Tasks lists 34; Projects › Job Page lists 28; Accounting › Dashboard lists 27; Projects › Schedule lists 22; Today › Chief of Staff lists 17 of the 77 records this module lists.
- **One label, different numbers inside the module:** "count: everything" 55 on Tasks against 10 on Messages (1 in all, section 3).
- **On the phone** (Owner): 3 have no section heading above the fold; 0 screens scroll sideways.
- **Nothing crashed and no page raised an error**; every page opened.
- **Reading changed nothing:** no save during the walk.

## 1. The Tree, Role by Role

**Pages** are the module's pages the role reaches from its menu (and the links those pages show). **Tabs** are the screens behind each page's tab groups, and behind the tabs those reveal. **Sections** are the headed parts of each page as it opens. Each cell reads desktop / phone.

| Role | Primary | First page of the module, reached by (desktop / phone) | Pages | Tab screens | Sections | Screens |
|---|---|---|---|---|---|---|
| Owner | yes | Today › Tasks (2 taps) / menu › Today › Tasks (3 taps) | 3 / 3 | 28 / 9 | 0 / 0 | 31 / 12 |
| PM (Alan) | yes | Today › Tasks (2 taps) / bar: Tasks (1 tap) | 3 / 3 | 20 / 7 | 0 / 0 | 23 / 10 |
| Coordinator (Chen) | yes | Today › Tasks (2 taps) / bar: Tasks (1 tap) | 3 / 3 | 21 / 7 | 0 / 0 | 24 / 10 |
| Foreman (Angel) |  | Messages (1 tap) / bar: Messages (1 tap) | 1 / 1 | 2 / 1 | 0 / 0 | 3 / 2 |
| Designer (Sarah) | yes | Today › Tasks (2 taps) / menu › Today › Tasks (3 taps) | 2 / 2 | 23 / 4 | 0 / 0 | 25 / 6 |
| Billing | yes | Today › Tasks (2 taps) / menu › Today › Tasks (3 taps) | 3 / 3 | 27 / 8 | 0 / 0 | 30 / 11 |
| Controller | yes | Today › Tasks (2 taps) / menu › Today › Tasks (3 taps) | 3 / 3 | 27 / 8 | 0 / 0 | 30 / 11 |
| Crew (Alberto) |  | Messages (1 tap) / bar: Messages (1 tap) | 1 / 1 | 1 / 1 | 0 / 0 | 2 / 2 |
| Driver (Alex) |  | Messages (1 tap) / bar: Messages (1 tap) | 1 / 1 | 1 / 1 | 0 / 0 | 2 / 2 |

### Which pages each role reaches (desktop)

Each cell is the number of screens the page has (the page and its tabs); "-" means the role does not reach it.

| Page | Owner | PM | Coordinator | Foreman | Designer | Billing | Controller | Crew | Driver |
|---|---|---|---|---|---|---|---|---|---|
| Tasks | 16 | 16 | 16 | - | 16 | 16 | 16 | - | - |
| Messages | 11 | 3 | 4 | 3 | 9 | 10 | 10 | 2 | 2 |
| Meetings | 4 | 4 | 4 | - | - | 4 | 4 | - | - |

### Owner's tree at a glance

Reached by is the taps from the role's first page, desktop then phone. Tall is in screens, desktop / phone. Sections are the headed parts as the page opens (phone above the fold). Tabs are the screens behind its tab groups, desktop / phone. "What it lists" counts the records found on the page as it opens.

| Page | Reached by (desktop / phone) | Heading | Tall | Sections (phone above the fold) | Tabs | Tiles and figures | What it lists | Blue button | First button | Shots |
|---|---|---|---|---|---|---|---|---|---|---|
| Tasks | Today › Tasks (2 taps) / menu › Today › Tasks (3 taps) | Tasks | 1.3 / 1.5 | 0 (0) | 15 / 2 | - | 12 to-dos, 5 contacts, 3 leads, 1 clients | New Task | List | [desktop](../../review/census/tasks/shots/desktop_owner_tasks.jpg) [phone](../../review/census/tasks/shots/phone_owner_tasks.jpg) |
| Messages | Messages (1 tap) / bar: Messages (1 tap) | Messages | 0.9 / 1.1 | 0 (0) | 10 / 4 | - | - | Record a voice note | Team | [desktop](../../review/census/tasks/shots/desktop_owner_messages.jpg) [phone](../../review/census/tasks/shots/phone_owner_messages.jpg) |
| Meetings | Company › Meetings (2 taps) / menu › Company › Meetings (3 taps) | Meetings | 0.6 / 0.8 | 0 (0) | 3 / 3 | Meetings to Review 2; Not Matched 0; Carried Over 2; Changes to Approve 3 | 2 meetings | none | Paste Notes | [desktop](../../review/census/tasks/shots/desktop_owner_meetings.jpg) [phone](../../review/census/tasks/shots/phone_owner_meetings.jpg) |

### PM (Alan)'s tree at a glance

Reached by is the taps from the role's first page, desktop then phone. Tall is in screens, desktop / phone. Sections are the headed parts as the page opens (phone above the fold). Tabs are the screens behind its tab groups, desktop / phone. "What it lists" counts the records found on the page as it opens.

| Page | Reached by (desktop / phone) | Heading | Tall | Sections (phone above the fold) | Tabs | Tiles and figures | What it lists | Blue button | First button | Shots |
|---|---|---|---|---|---|---|---|---|---|---|
| Tasks | Today › Tasks (2 taps) / bar: Tasks (1 tap) | Tasks | 0.7 / 1.0 | 0 (0) | 15 / 2 | - | 7 to-dos, 1 vendors | New Task | List | [desktop](../../review/census/tasks/shots/desktop_pm_tasks.jpg) [phone](../../review/census/tasks/shots/phone_pm_tasks.jpg) |
| Messages | Messages (1 tap) / bar: Messages (1 tap) | Messages | 0.9 / 1.0 | 0 (0) | 2 / 2 | - | 1 message threads | Record a voice note | Team | [desktop](../../review/census/tasks/shots/desktop_pm_messages.jpg) [phone](../../review/census/tasks/shots/phone_pm_messages.jpg) |
| Meetings | Company › Meetings (2 taps) / menu › Company › Meetings (3 taps) | Meetings | 0.6 / 0.8 | 0 (0) | 3 / 3 | Meetings to Review 2; Not Matched 0; Carried Over 2; Changes with the Owner 3 | 2 meetings | none | Paste Notes | [desktop](../../review/census/tasks/shots/desktop_pm_meetings.jpg) [phone](../../review/census/tasks/shots/phone_pm_meetings.jpg) |

### Coordinator (Chen)'s tree at a glance

Reached by is the taps from the role's first page, desktop then phone. Tall is in screens, desktop / phone. Sections are the headed parts as the page opens (phone above the fold). Tabs are the screens behind its tab groups, desktop / phone. "What it lists" counts the records found on the page as it opens.

| Page | Reached by (desktop / phone) | Heading | Tall | Sections (phone above the fold) | Tabs | Tiles and figures | What it lists | Blue button | First button | Shots |
|---|---|---|---|---|---|---|---|---|---|---|
| Tasks | Today › Tasks (2 taps) / bar: Tasks (1 tap) | Tasks | 0.6 / 1.0 | 0 (0) | 15 / 2 | - | 2 schedule lines, 1 to-dos, 1 decisions, 1 vendors | New Task | List | [desktop](../../review/census/tasks/shots/desktop_coord_tasks.jpg) [phone](../../review/census/tasks/shots/phone_coord_tasks.jpg) |
| Messages | Messages (1 tap) / bar: Messages (1 tap) | Messages | 0.9 / 1.0 | 0 (0) | 3 / 2 | - | 1 purchase orders, 1 files, 1 vendors, 1 message threads | Record a voice note | Team | [desktop](../../review/census/tasks/shots/desktop_coord_messages.jpg) [phone](../../review/census/tasks/shots/phone_coord_messages.jpg) |
| Meetings | Company › Meetings (2 taps) / menu › Company › Meetings (3 taps) | Meetings | 0.6 / 0.8 | 0 (0) | 3 / 3 | Meetings to Review 2; Not Matched 0; Carried Over 2; Changes with the Owner 3 | 2 meetings | none | Paste Notes | [desktop](../../review/census/tasks/shots/desktop_coord_meetings.jpg) [phone](../../review/census/tasks/shots/phone_coord_meetings.jpg) |

### Designer (Sarah)'s tree at a glance

Reached by is the taps from the role's first page, desktop then phone. Tall is in screens, desktop / phone. Sections are the headed parts as the page opens (phone above the fold). Tabs are the screens behind its tab groups, desktop / phone. "What it lists" counts the records found on the page as it opens.

| Page | Reached by (desktop / phone) | Heading | Tall | Sections (phone above the fold) | Tabs | Tiles and figures | What it lists | Blue button | First button | Shots |
|---|---|---|---|---|---|---|---|---|---|---|
| Tasks | Today › Tasks (2 taps) / menu › Today › Tasks (3 taps) | Tasks | 0.4 / 1.0 | 0 (0) | 15 / 2 | - | 1 to-dos, 1 site questions | New Task | List | [desktop](../../review/census/tasks/shots/desktop_designer_tasks.jpg) [phone](../../review/census/tasks/shots/phone_designer_tasks.jpg) |
| Messages | Messages (1 tap) / bar: Messages (1 tap) | Messages | 0.9 / 1.0 | 0 (0) | 8 / 2 | - | - | Record a voice note | Team | [desktop](../../review/census/tasks/shots/desktop_designer_messages.jpg) [phone](../../review/census/tasks/shots/phone_designer_messages.jpg) |

### Billing's tree at a glance

Reached by is the taps from the role's first page, desktop then phone. Tall is in screens, desktop / phone. Sections are the headed parts as the page opens (phone above the fold). Tabs are the screens behind its tab groups, desktop / phone. "What it lists" counts the records found on the page as it opens.

| Page | Reached by (desktop / phone) | Heading | Tall | Sections (phone above the fold) | Tabs | Tiles and figures | What it lists | Blue button | First button | Shots |
|---|---|---|---|---|---|---|---|---|---|---|
| Tasks | Today › Tasks (2 taps) / menu › Today › Tasks (3 taps) | Tasks | 0.3 / 1.0 | 0 (0) | 15 / 2 | - | - | New Task | List | [desktop](../../review/census/tasks/shots/desktop_billing_tasks.jpg) [phone](../../review/census/tasks/shots/phone_billing_tasks.jpg) |
| Messages | Messages (1 tap) / bar: Messages (1 tap) | Messages | 0.9 / 1.0 | 0 (0) | 9 / 3 | - | - | Record a voice note | Team | [desktop](../../review/census/tasks/shots/desktop_billing_messages.jpg) [phone](../../review/census/tasks/shots/phone_billing_messages.jpg) |
| Meetings | More › Meetings (2 taps) / menu › More › swipe the strip, Meetings (3 taps) | Meetings | 0.6 / 0.8 | 0 (0) | 3 / 3 | Meetings to Review 2; Not Matched 0; Carried Over 2; Changes with the Owner 3 | 2 meetings | none | Paste Notes | [desktop](../../review/census/tasks/shots/desktop_billing_meetings.jpg) [phone](../../review/census/tasks/shots/phone_billing_meetings.jpg) |

### Controller's tree at a glance

Reached by is the taps from the role's first page, desktop then phone. Tall is in screens, desktop / phone. Sections are the headed parts as the page opens (phone above the fold). Tabs are the screens behind its tab groups, desktop / phone. "What it lists" counts the records found on the page as it opens.

| Page | Reached by (desktop / phone) | Heading | Tall | Sections (phone above the fold) | Tabs | Tiles and figures | What it lists | Blue button | First button | Shots |
|---|---|---|---|---|---|---|---|---|---|---|
| Tasks | Today › Tasks (2 taps) / menu › Today › Tasks (3 taps) | Tasks | 0.4 / 1.0 | 0 (0) | 15 / 2 | - | 1 to-dos | New Task | List | [desktop](../../review/census/tasks/shots/desktop_controller_tasks.jpg) [phone](../../review/census/tasks/shots/phone_controller_tasks.jpg) |
| Messages | Messages (1 tap) / bar: Messages (1 tap) | Messages | 0.9 / 1.0 | 0 (0) | 9 / 3 | - | - | Record a voice note | Team | [desktop](../../review/census/tasks/shots/desktop_controller_messages.jpg) [phone](../../review/census/tasks/shots/phone_controller_messages.jpg) |
| Meetings | More › Meetings (2 taps) / menu › More › swipe the strip, Meetings (3 taps) | Meetings | 0.6 / 0.8 | 0 (0) | 3 / 3 | Meetings to Review 2; Not Matched 0; Carried Over 2; Changes with the Owner 3 | 2 meetings | none | Paste Notes | [desktop](../../review/census/tasks/shots/desktop_controller_meetings.jpg) [phone](../../review/census/tasks/shots/phone_controller_meetings.jpg) |

### How each page is reached, and the pages reached only one way

Menu places are the role's menu entries that open the page (a page in two groups has two). The phone bar counts as one more way in on the phone (its pages are in the menu too). Links are the walked pages, in any module, that show a link to it. **One way** means one menu place and nothing else: lose that entry and the page is lost.

| Role | Device | Page | Menu places | Phone bar | Linked from | Ways in |
|---|---|---|---|---|---|---|
| Owner | desktop | Tasks | Today › Tasks; Tasks | - | - | 2 |
| Owner | desktop | Messages | Messages | - | Company and Settings › The Brain, Today › Chief of Staff | 3 |
| Owner | desktop | Meetings | Company › Meetings | - | Design › Project Board | 2 |
| Owner | phone | Tasks | Today › Tasks; Tasks | - | - | 2 |
| Owner | phone | Messages | Messages | yes | Company and Settings › The Brain, Today › Chief of Staff | 4 |
| Owner | phone | Meetings | Company › Meetings | - | Design › Project Board | 2 |
| PM (Alan) | desktop | Tasks | Today › Tasks; Tasks | - | - | 2 |
| PM (Alan) | desktop | Messages | Messages | - | Company and Settings › The Brain, Today › Chief of Staff | 3 |
| PM (Alan) | desktop | Meetings | Company › Meetings | - | Design › Project Board | 2 |
| PM (Alan) | phone | Tasks | Today › Tasks; Tasks | yes | - | 3 |
| PM (Alan) | phone | Messages | Messages | yes | Company and Settings › The Brain, Today › Chief of Staff | 4 |
| PM (Alan) | phone | Meetings | Company › Meetings | - | Design › Project Board | 2 |
| Coordinator (Chen) | desktop | Tasks | Today › Tasks; Tasks | - | - | 2 |
| Coordinator (Chen) | desktop | Messages | Messages | - | Company and Settings › The Brain, Today › Chief of Staff | 3 |
| Coordinator (Chen) | desktop | Meetings | Company › Meetings | - | - | 1 (one way) |
| Coordinator (Chen) | phone | Tasks | Today › Tasks; Tasks | yes | - | 3 |
| Coordinator (Chen) | phone | Messages | Messages | yes | Company and Settings › The Brain, Today › Chief of Staff | 4 |
| Coordinator (Chen) | phone | Meetings | Company › Meetings | - | - | 1 (one way) |
| Foreman (Angel) | desktop | Messages | Messages | - | - | 1 (one way) |
| Foreman (Angel) | phone | Messages | Messages | yes | - | 2 |
| Designer (Sarah) | desktop | Tasks | Today › Tasks; Tasks | - | - | 2 |
| Designer (Sarah) | desktop | Messages | Messages | - | - | 1 (one way) |
| Designer (Sarah) | phone | Tasks | Today › Tasks; Tasks | - | - | 2 |
| Designer (Sarah) | phone | Messages | Messages | yes | - | 2 |
| Billing | desktop | Tasks | Today › Tasks; Tasks | - | - | 2 |
| Billing | desktop | Messages | Messages | - | Today › Chief of Staff | 2 |
| Billing | desktop | Meetings | More › Meetings | - | - | 1 (one way) |
| Billing | phone | Tasks | Today › Tasks; Tasks | - | - | 2 |
| Billing | phone | Messages | Messages | yes | Today › Chief of Staff | 3 |
| Billing | phone | Meetings | More › Meetings | - | - | 1 (one way) |
| Controller | desktop | Tasks | Today › Tasks; Tasks | - | - | 2 |
| Controller | desktop | Messages | Messages | - | Company and Settings › The Brain, Today › Chief of Staff | 3 |
| Controller | desktop | Meetings | More › Meetings | - | - | 1 (one way) |
| Controller | phone | Tasks | Today › Tasks; Tasks | - | - | 2 |
| Controller | phone | Messages | Messages | yes | Company and Settings › The Brain, Today › Chief of Staff | 4 |
| Controller | phone | Meetings | More › Meetings | - | - | 1 (one way) |
| Crew (Alberto) | desktop | Messages | Messages | - | - | 1 (one way) |
| Crew (Alberto) | phone | Messages | Messages | yes | - | 2 |
| Driver (Alex) | desktop | Messages | Messages | - | - | 1 (one way) |
| Driver (Alex) | phone | Messages | Messages | yes | - | 2 |

## 2. Where the Data Lives, and Where It Shows Twice

Records are found by their own words (the information map's catalog, the job's nouns and this census's: clients, vendors, leads, contacts, companies, every invoice, bill and PO, payroll runs, stock, meetings, journals, obligations, lessons, partners, bank lines, threads), so these are floors. A page's tabs count as the page.

### Owner, desktop: each kind of record, and the pages that list it

| Records | Found | Pages that list them (how many each) | Also in other modules |
|---|---|---|---|
| vendors | 3 | 3: Tasks 2, Meetings 2, Messages 1 | Today › Chief of Staff 3, Accounting › Reports 3, Company and Settings › The Brain 3, Purchasing › Vendors 3 |
| clients | 5 | 2: Messages 4, Tasks 1 | Sales and Clients › Companies 4, Sales and Clients › People 4, Sales and Clients › Clients 4, Accounting › Reports 4 |
| to-dos | 29 | 2: Tasks 29, Meetings 2 | Company and Settings › Calendar 10, Projects › Tasks 10, Projects › Job Page 9, Accounting › Dashboard 8 |
| materials | 3 | 2: Tasks 2, Meetings 2 | Accounting › Dashboard 3, Accounting › Reports 3, Projects › Materials 3, Purchasing › Buy Board 3 |
| decisions | 6 | 2: Meetings 6, Tasks 1 | Projects › Decisions 5, Design › Project Board 5, Accounting › Dashboard 4, Purchasing › Buy Board 3 |
| schedule lines | 25 | 1: Tasks 25 | Projects › Schedule 19, Projects › Tasks 19, Projects › Job Page 13, Accounting › Dashboard 11 |
| contacts | 5 | 1: Tasks 5 | Sales and Clients › People 6, Sales and Clients › Clients 6, Sales and Clients › Companies 6, Today › Chief of Staff 3 |
| leads | 3 | 1: Tasks 3 | Sales and Clients › People 3, Sales and Clients › Clients 3, Today › Chief of Staff 3, Company and Settings › The Brain 3 |
| obligations | 5 | 1: Tasks 5 | Company and Settings › Obligations 5, Today › Chief of Staff 2, Company and Settings › The Brain 1, Company and Settings › Calendar 1 |
| site questions | 2 | 1: Tasks 2 | Projects › Tasks 2, Projects › Job Page 1, Projects › Field 1 |
| mail | 1 | 1: Messages 1 | Today › Today 1 |
| message threads | 1 | 1: Messages 1 | - |
| meetings | 2 | 1: Meetings 2 | Today › Chief of Staff 2, Company and Settings › Company Settings 2, Company and Settings › The Brain 2, Company and Settings › Company 2 |
| approvals | 3 | 1: Meetings 3 | Today › Today 3, Today › Chief of Staff 3, Today › Approvals 3, Company and Settings › The Brain 3 |

### Records on two or more pages, and lists that are the same list twice

**Owner, desktop:** 6 records on two or more pages: to-dos 2 (up to 2 pages); vendors 2 (up to 2 pages); decisions 1 (up to 2 pages); materials 1 (up to 2 pages).

- "Shop drawings for the parlor bookcases" (to-dos) on 2 pages: Meetings, Tasks
- "Replacement boxes for the chipped floor tile" (to-dos) on 2 pages: Meetings, Tasks
- "Nemo Tile" (vendors) on 2 pages: Meetings, Tasks
- "Carlos Millwork" (vendors) on 2 pages: Meetings, Tasks
- "Confirm new 3rd fl tile selection is in stock" (decisions) on 2 pages: Meetings, Tasks
- "Flooring" (materials) on 2 pages: Meetings, Tasks

**PM (Alan), desktop:** 6 records on two or more pages: to-dos 2 (up to 2 pages); vendors 2 (up to 2 pages); decisions 1 (up to 2 pages); materials 1 (up to 2 pages).

- "Replacement boxes for the chipped floor tile" (to-dos) on 2 pages: Meetings, Tasks
- "Nemo Tile" (vendors) on 2 pages: Meetings, Tasks
- "Shop drawings for the parlor bookcases" (to-dos) on 2 pages: Meetings, Tasks
- "Carlos Millwork" (vendors) on 2 pages: Meetings, Tasks
- "Confirm new 3rd fl tile selection is in stock" (decisions) on 2 pages: Meetings, Tasks
- "Flooring" (materials) on 2 pages: Meetings, Tasks

**Coordinator (Chen), desktop:** 7 records on two or more pages: to-dos 2 (up to 2 pages); vendors 2 (up to 2 pages); materials 2 (up to 2 pages); decisions 1 (up to 2 pages).

- "Shop drawings for the parlor bookcases" (to-dos) on 2 pages: Meetings, Tasks
- "Confirm new 3rd fl tile selection is in stock" (decisions) on 2 pages: Meetings, Tasks
- "Carlos Millwork" (vendors) on 2 pages: Meetings, Tasks
- "Insulation" (materials) on 2 pages: Messages, Tasks
- "Replacement boxes for the chipped floor tile" (to-dos) on 2 pages: Meetings, Tasks
- "Nemo Tile" (vendors) on 2 pages: Meetings, Tasks

**Billing, desktop:** 6 records on two or more pages: to-dos 2 (up to 2 pages); vendors 2 (up to 2 pages); decisions 1 (up to 2 pages); materials 1 (up to 2 pages).

- "Shop drawings for the parlor bookcases" (to-dos) on 2 pages: Meetings, Tasks
- "Replacement boxes for the chipped floor tile" (to-dos) on 2 pages: Meetings, Tasks
- "Nemo Tile" (vendors) on 2 pages: Meetings, Tasks
- "Carlos Millwork" (vendors) on 2 pages: Meetings, Tasks
- "Confirm new 3rd fl tile selection is in stock" (decisions) on 2 pages: Meetings, Tasks
- "Flooring" (materials) on 2 pages: Meetings, Tasks

**Controller, desktop:** 6 records on two or more pages: to-dos 2 (up to 2 pages); vendors 2 (up to 2 pages); decisions 1 (up to 2 pages); materials 1 (up to 2 pages).

- "Shop drawings for the parlor bookcases" (to-dos) on 2 pages: Meetings, Tasks
- "Replacement boxes for the chipped floor tile" (to-dos) on 2 pages: Meetings, Tasks
- "Nemo Tile" (vendors) on 2 pages: Meetings, Tasks
- "Carlos Millwork" (vendors) on 2 pages: Meetings, Tasks
- "Confirm new 3rd fl tile selection is in stock" (decisions) on 2 pages: Meetings, Tasks
- "Flooring" (materials) on 2 pages: Meetings, Tasks

**PM (Alan), phone:** 2 records on two or more pages: to-dos 1 (up to 2 pages); vendors 1 (up to 2 pages).

- "Replacement boxes for the chipped floor tile" (to-dos) on 2 pages: Meetings, Tasks
- "Nemo Tile" (vendors) on 2 pages: Meetings, Tasks

**Coordinator (Chen), phone:** 3 records on two or more pages: to-dos 1 (up to 2 pages); decisions 1 (up to 2 pages); vendors 1 (up to 2 pages).

- "Shop drawings for the parlor bookcases" (to-dos) on 2 pages: Meetings, Tasks
- "Confirm new 3rd fl tile selection is in stock" (decisions) on 2 pages: Meetings, Tasks
- "Carlos Millwork" (vendors) on 2 pages: Meetings, Tasks

### The same records in other modules

For each role on the desktop: the pages of other modules (the Projects census's 121 State Street pages included) that list records this module lists, with how many.

- **Owner** (77 records here): Projects › Tasks 34; Projects › Job Page 28; Accounting › Dashboard 27; Projects › Schedule 22; Today › Chief of Staff 17; Company and Settings › Calendar 15; Company and Settings › The Brain 14; Projects › Materials 12
- **PM (Alan)** (77 records here): Projects › Tasks 34; Projects › Job Page 31; Accounting › Dashboard 28; Projects › Schedule 23; Company and Settings › Calendar 15; Today › Chief of Staff 15; Company and Settings › The Brain 15; Today › Today 14
- **Coordinator (Chen)** (77 records here): Projects › Tasks 34; Projects › Job Page 30; Accounting › Dashboard 23; Projects › Schedule 22; Company and Settings › Calendar 15; Company and Settings › The Brain 13; Today › Chief of Staff 13; Projects › Materials 12
- **Foreman (Angel)** (8 records here): Field and Site › Raise 5; Field and Site › Site 4; Field and Site › Daily Log 2; Today › Today 2; Field and Site › Schedule 2; Field and Site › Photos 1
- **Designer (Sarah)** (65 records here): Projects › Tasks 34; Projects › Schedule 15; Accounting › Dashboard 7; Today › Today 5; Projects › Decisions 3; Company and Settings › The SmartDesign Standard 2; Design › Design 2; Design › Project Board 1
- **Billing** (73 records here): Projects › Job Page 28; Accounting › Dashboard 24; Accounting › Reports 11; Today › Chief of Staff 7; Billing › Billing 6; Company and Settings › The SmartDesign Standard 2; Sales and Clients › Sales 2; Accounting › Spend 2
- **Controller** (73 records here): Accounting › Dashboard 24; Company and Settings › Calendar 15; Accounting › Reports 11; Company and Settings › The Brain 10; Today › Chief of Staff 10; Billing › Billing 6; Company and Settings › Obligations 5; Purchasing › Purchasing 3
- **Crew (Alberto)**: none found.
- **Driver (Alex)**: none found.

Names (clients, vendors, leads, contacts, companies, partners) are left out here: a page that writes a name counts as listing it. A page that is the same page as one of this module's (one view under two menus) is left out too and listed next.

### The same page under two modules' menus

None found.

## 3. One Label, Different Numbers

The same label (a tile, a figure, a tab or section count) with numbers that share no value on two pages, for one role. Some are right about different scopes ("Open" against "All", one job against every job); the person still reads one word with two numbers. Each needs a person to judge.

**Inside the module, Owner, desktop** (1):
- count: everything: 55 on Tasks; 10 on Messages

**Inside the module, PM (Alan), desktop** (1):
- count: everything: 55 on Tasks; 10 on Messages

**Inside the module, Coordinator (Chen), desktop** (1):
- count: everything: 55 on Tasks; 10 on Messages

**Inside the module, Designer (Sarah), desktop** (1):
- count: everything: 55 on Tasks; 10 on Messages

**Inside the module, Billing, desktop** (1):
- count: everything: 55 on Tasks; 10 on Messages

**Inside the module, Controller, desktop** (1):
- count: everything: 55 on Tasks; 10 on Messages

Against other modules, Owner, desktop: none found.

Against other modules, PM (Alan), desktop: none found.

Against other modules, Coordinator (Chen), desktop: none found.

Against other modules, Designer (Sarah), desktop: none found.

Against other modules, Billing, desktop: none found.

Against other modules, Controller, desktop: none found.

## 4. Empty, Dead and Broken Screens

| Device | Role | Screen | What |
|---|---|---|---|
| desktop | Owner | Messages | lists nothing: "No messages yet Post what happened on site today. Everyone o" |
| desktop | Owner | Messages[Mail] | the tab leaves for comms |
| desktop | PM (Alan) | Messages[Mail] | the tab leaves for comms |
| desktop | Coordinator (Chen) | Messages[Mail] | the tab leaves for comms |
| desktop | Designer (Sarah) | Messages | lists nothing: "No messages yet Post what happened on site today. Everyone o" |
| desktop | Designer (Sarah) | Messages[Mail] | the tab leaves for comms |
| desktop | Billing | Tasks | lists nothing: "Nothing due in the next 7 days, and nothing late." |
| desktop | Billing | Messages | lists nothing: "No messages yet Post what happened on site today. Everyone o" |
| desktop | Billing | Messages[Mail] | the tab leaves for comms |
| desktop | Controller | Messages | lists nothing: "No messages yet Post what happened on site today. Everyone o" |
| desktop | Controller | Messages[Mail] | the tab leaves for comms |
| desktop | Crew (Alberto) | Messages | lists nothing: "No messages yet Post an update and everyone on the job sees " |
| desktop | Driver (Alex) | Messages | lists nothing: "No messages yet Post an update and everyone on the job sees " |
| phone | Owner | Messages[Mail] | the tab leaves for comms |
| phone | PM (Alan) | Messages[Mail] | the tab leaves for comms |
| phone | Coordinator (Chen) | Messages[Mail] | the tab leaves for comms |
| phone | Designer (Sarah) | Tasks[Waiting] | 22 words |
| phone | Designer (Sarah) | Messages[Mail] | the tab leaves for comms |
| phone | Billing | Tasks | lists nothing: "Nothing due in the next 7 days, and nothing late." |
| phone | Billing | Tasks[Waiting] | 22 words |
| phone | Billing | Tasks[By Status] | 24 words |
| phone | Billing | Messages[Mail] | the tab leaves for comms |
| phone | Controller | Tasks[Waiting] | 22 words |
| phone | Controller | Messages[Mail] | the tab leaves for comms |
| phone | Crew (Alberto) | Messages | 24 words |
| phone | Crew (Alberto) | Messages[206 Lenox Team No messages yet] | 24 words |
| phone | Driver (Alex) | Messages | 24 words |
| phone | Driver (Alex) | Messages[206 Lenox Team No messages yet] | 24 words |

## 5. The Phone at 390

"Cut off" is text the phone ends early; "scrolls inside" is a strip of tiles or tabs the person swipes sideways inside the page (the page itself does not move). "Strip swipe" counts pages whose strip entry sits off screen until the strip is swiped. Pages taller than 3 phone screens are listed with their height.

| Role | Screens | The page scrolls sideways | Text cut off at the edge | Strips that scroll inside the page | Strip swipe | Pages taller than 3 screens |
|---|---|---|---|---|---|---|
| Owner | 12 | 0 | 0 | 3: Meetings, Messages, Tasks | 0 | 0 |
| PM (Alan) | 10 | 0 | 0 | 2: Meetings, Messages | 0 | 0 |
| Coordinator (Chen) | 10 | 0 | 0 | 2: Meetings, Messages | 0 | 0 |
| Foreman (Angel) | 2 | 0 | 0 | 1: Messages | 0 | 0 |
| Designer (Sarah) | 6 | 0 | 0 | 1: Messages | 0 | 0 |
| Billing | 11 | 0 | 0 | 2: Meetings, Messages | 1: Meetings | 0 |
| Controller | 11 | 0 | 0 | 2: Meetings, Messages | 1: Meetings | 0 |
| Crew (Alberto) | 2 | 0 | 0 | 0 | 0 | 0 |
| Driver (Alex) | 2 | 0 | 0 | 0 | 0 | 0 |

## 6. Page by Page, in Full

Every page the primary role reaches, as it opens, then each of its tabs. Heights are in screens of that device (900px desktop, 844px phone); "above the fold" is above the bottom bar on the phone.

### Owner, desktop

- reached by: Today › Tasks (2 taps); also in Tasks; first button "List"; shot [desktop](../../review/census/tasks/shots/desktop_owner_tasks.jpg)
- **Tasks** (`tkall`): heading "Tasks", 1.3 screens tall, 0 sections (0 above the fold), 15 tab screens; blue: New Task
  - lead: "15 open for you · 55 across the firm · 3 overdue"
  - records: 12 to-dos, 5 contacts, 3 leads, 1 clients, 1 obligations
  - fields: Search tasks, How the list is grouped
  - tab groups: List / Table / Board / Calendar; All Open 15 / My Week 12 / Waiting on Others 2 / Everything 55 / New View
  - tab **Table**: heading "Tasks", 0 sections; 12 to-dos, 5 contacts, 3 leads, 1 clients
  - tab **Table › Owner**: heading "Tasks", 0 sections; 12 to-dos, 5 contacts, 3 leads, 1 clients
  - tab **Table › Status**: heading "Tasks", 0 sections; 12 to-dos, 5 contacts, 3 leads, 1 clients
  - tab **Board**: heading "Tasks", 0 sections; 12 to-dos, 5 contacts, 3 leads, 1 clients
  - tab **Calendar**: heading "Tasks", 0 sections; 12 to-dos, 5 contacts, 3 leads, 1 clients
  - tab **Calendar › Week**: heading "Tasks", 0 sections; 12 to-dos, 5 contacts, 3 leads, 1 clients
  - tab **All Open**: heading "Tasks", 0 sections; 15 to-dos, 5 contacts, 4 obligations, 3 leads
  - tab **Waiting on Others**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Waiting on Others › Owner: Alan**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Waiting on Others › Due Sat, Sep**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Waiting on Others › Status: Waiting On**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Waiting on Others › Owner: Chen Biron**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Waiting on Others › Due Mon, Sep**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Waiting on Others › Status: Waiting On**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Everything**: heading "Tasks", 0 sections; 29 to-dos, 25 schedule lines, 5 contacts, 5 obligations
  - tabs that would not press (the row changed once one was pressed): New View
- reached by: Messages (1 tap); first button "Team"; shot [desktop](../../review/census/tasks/shots/desktop_owner_messages.jpg)
- **Messages** (`chat`): heading "Messages", 0.9 screens tall, 0 sections (0 above the fold), 10 tab screens; blue: Record a voice note
  - lead: "The team's thread for this job. Every post is read by the assistant and becomes a proposal in the Inbox when it changes the project."
  - fields: Search conversations, Message
  - empty states: "No messages yet Post what happened on site today. Everyone on the job's team reads it."
  - tab groups: Team / Mail 1 / Field; My Chats / All Chats; 121 State Street Team No messages yet / 121 State Street Client No messages yet / 140 Prospect Place Team No messages yet / 140 Prospect Place Client No messages ye / 206 Lenox Team No messages yet / 206 Lenox Client No messages yet / 45 Cranberry St Team No messages yet / 45 Cranberry St Client No messages yet
  - tab **Mail**: heading "Messages", 0 sections; 1 mail (the tab leaves for `comms`)
  - tab **Field**: heading "Messages", 0 sections
  - tab **All Chats**: heading "Messages", 0 sections; 1 vendors, 1 message threads
  - tab **121 State Street Client No messages yet**: heading "Messages", 0 sections; 1 clients
  - tab **140 Prospect Place Team No messages yet**: heading "Messages", 0 sections
  - tab **140 Prospect Place Client No messages ye**: heading "Messages", 0 sections; 1 clients
  - tab **206 Lenox Team No messages yet**: heading "Messages", 0 sections
  - tab **206 Lenox Client No messages yet**: heading "Messages", 0 sections; 1 clients
  - tab **45 Cranberry St Team No messages yet**: heading "Messages", 0 sections
  - tab **45 Cranberry St Client No messages yet**: heading "Messages", 0 sections; 1 clients
- reached by: Company › Meetings (2 taps); first button "Paste Notes"; shot [desktop](../../review/census/tasks/shots/desktop_owner_meetings.jpg)
- **Meetings** (`meetings`): heading "Meetings", 0.6 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: none
  - lead: "What was said, what was decided, who owes what — read from the notes Gemini takes, and turned into the record."
  - figures: Meetings to Review 2; Not Matched 0; Carried Over 2; Changes to Approve 3
  - records: 2 meetings
  - columns: table: DATE, MEETING, PROJECT, WITH, NEXT STEPS, WAITING, STATUS (2 rows)
  - fields: Search…
  - tab groups: Meetings / What We Are Learning / Changes · 3 / Settings
  - tab **What We Are Learning**: heading "Meetings", 9 sections; 6 decisions, 2 meetings, 2 materials, 2 approvals
  - tab **Changes ·**: heading "Meetings", 5 sections; 3 approvals, 2 meetings, 1 materials
  - tab **Settings**: heading "Meetings", 5 sections

### Owner, phone

- reached by: menu › Today › Tasks (3 taps); also in Tasks; first button "Menu"; shot [phone](../../review/census/tasks/shots/phone_owner_tasks.jpg)
- **Tasks** (`tkall`): heading "Tasks", 1.5 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: none
  - records: 12 to-dos, 5 contacts, 3 leads, 1 clients, 1 obligations
  - fields: Add a task
  - tab groups: Due Soon 12 / Waiting 0 / By Status / By Project
  - tab **Waiting**: heading "Tasks", 0 sections
  - tab **By Status**: heading "Tasks", 0 sections; 12 to-dos, 5 contacts, 3 leads, 1 clients
  - tabs that would not press (the row changed once one was pressed): By Project
- reached by: bar: Messages (1 tap); first button "Team"; shot [phone](../../review/census/tasks/shots/phone_owner_messages.jpg)
- **Messages** (`chat`): heading "Messages", 1.1 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: none
  - lead: "The team's thread for this job. Every post is read by the assistant and becomes a proposal in the Inbox when it changes the project."
  - fields: Search conversations
  - tab groups: Team / Mail 1 / Field; My Chats / All Chats; 121 State Street Team No messages yet / 121 State Street Client No messages yet / 140 Prospect Place Team No messages yet / 140 Prospect Place Client No messages ye / 206 Lenox Team No messages yet / 206 Lenox Client No messages yet / 45 Cranberry St Team No messages yet / 45 Cranberry St Client No messages yet
  - tab **Mail**: heading "Messages", 1 sections; 1 mail (the tab leaves for `comms`)
  - tab **Field**: heading "Messages", 0 sections
  - tab **All Chats**: heading "Messages", 0 sections; 1 vendors, 1 message threads
  - tab **121 State Street Client No messages yet**: heading "Messages", 0 sections; 1 clients
  - tabs that would not press (the row changed once one was pressed): 140 Prospect Place Team No messages yet, 140 Prospect Place Client No messages ye, 206 Lenox Team No messages yet, 206 Lenox Client No messages yet, 45 Cranberry St Team No messages yet, 45 Cranberry St Client No messages yet
- reached by: menu › Company › Meetings (3 taps); first button "Paste Notes"; shot [phone](../../review/census/tasks/shots/phone_owner_meetings.jpg)
- **Meetings** (`meetings`): heading "Meetings", 0.8 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: none
  - lead: "What was said, what was decided, who owes what — read from the notes Gemini takes, and turned into the record."
  - figures: Meetings to Review 2; Not Matched 0; Carried Over 2; Changes to Approve 3
  - records: 2 meetings
  - columns: table: Date, Meeting, Project, With, Next Steps, Waiting, Status (2 rows)
  - fields: Search…
  - tab groups: Meetings / What We Are Learning / Changes · 3 / Settings
  - tab **What We Are Learning**: heading "Meetings", 9 sections; 6 decisions, 2 meetings, 2 materials, 2 approvals
  - tab **Changes ·**: heading "Meetings", 5 sections; 3 approvals, 2 meetings, 1 materials
  - tab **Settings**: heading "Meetings", 5 sections

### PM (Alan), desktop

- reached by: Today › Tasks (2 taps); also in Tasks; first button "List"; shot [desktop](../../review/census/tasks/shots/desktop_pm_tasks.jpg)
- **Tasks** (`tkall`): heading "Tasks", 0.7 screens tall, 0 sections (0 above the fold), 15 tab screens; blue: New Task
  - lead: "6 open for you · 55 across the firm"
  - records: 7 to-dos, 1 vendors
  - fields: Search tasks, How the list is grouped
  - tab groups: List / Table / Board / Calendar; All Open 6 / My Week 5 / Waiting on Others 2 / Everything 55 / New View; Waiting on Nemo Tile for a ship date for / Owner: Alan / Due Sat, Sep / Status: Waiting On
  - tab **Table**: heading "Tasks", 0 sections; 7 to-dos, 1 vendors
  - tab **Table › Owner**: heading "Tasks", 0 sections; 7 to-dos, 1 vendors
  - tab **Table › Status**: heading "Tasks", 0 sections; 7 to-dos, 1 vendors
  - tab **Board**: heading "Tasks", 0 sections; 7 to-dos, 1 vendors
  - tab **Calendar**: heading "Tasks", 0 sections; 7 to-dos
  - tab **Calendar › Week**: heading "Tasks", 0 sections; 7 to-dos
  - tab **All Open**: heading "Tasks", 0 sections; 8 to-dos, 1 site questions, 1 vendors
  - tab **Waiting on Others**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Waiting on Others › Owner: Chen Biron**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Waiting on Others › Due Mon, Sep**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Waiting on Others › Status: Waiting On**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Everything**: heading "Tasks", 0 sections; 29 to-dos, 25 schedule lines, 5 contacts, 5 obligations
  - tab **Owner: Alan**: heading "Tasks", 0 sections; 7 to-dos, 1 vendors
  - tab **Due Sat, Sep**: heading "Tasks", 0 sections; 7 to-dos, 1 vendors
  - tab **Status: Waiting On**: heading "Tasks", 0 sections; 7 to-dos, 1 vendors
  - tabs that would not press (the row changed once one was pressed): New View
- reached by: Messages (1 tap); first button "Team"; shot [desktop](../../review/census/tasks/shots/desktop_pm_messages.jpg)
- **Messages** (`chat`): heading "Messages", 0.9 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: Record a voice note
  - lead: "A private conversation. Only the people in it can read it."
  - records: 1 message threads
  - fields: Search conversations, Message
  - tab groups: Team / Mail 1 / Field 2; Site Leads Angel: Will do. The electrici / Start a Chat on a Job 8 job conversation
  - tab **Mail**: heading "Messages", 0 sections; 1 mail (the tab leaves for `comms`)
  - tab **Field**: heading "Messages", 0 sections; 2 site questions, 1 schedule lines
  - tabs that would not press (the row changed once one was pressed): Start a Chat on a Job 8 job conversation
- reached by: Company › Meetings (2 taps); first button "Paste Notes"; shot [desktop](../../review/census/tasks/shots/desktop_pm_meetings.jpg)
- **Meetings** (`meetings`): heading "Meetings", 0.6 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: none
  - lead: "What was said, what was decided, who owes what — read from the notes Gemini takes, and turned into the record."
  - figures: Meetings to Review 2; Not Matched 0; Carried Over 2; Changes with the Owner 3
  - records: 2 meetings
  - columns: table: DATE, MEETING, PROJECT, WITH, NEXT STEPS, WAITING, STATUS (2 rows)
  - fields: Search…
  - tab groups: Meetings / What We Are Learning / Changes · 3 / Settings
  - tab **What We Are Learning**: heading "Meetings", 9 sections; 6 decisions, 2 meetings, 2 materials, 2 to-dos
  - tab **Changes ·**: heading "Meetings", 5 sections; 2 meetings, 1 materials
  - tab **Settings**: heading "Meetings", 5 sections

### PM (Alan), phone

- reached by: bar: Tasks (1 tap); also in Tasks; first button "Menu"; shot [phone](../../review/census/tasks/shots/phone_pm_tasks.jpg)
- **Tasks** (`tkall`): heading "Tasks", 1.0 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: none
  - records: 7 to-dos, 1 vendors
  - fields: Add a task
  - tab groups: Due Soon 5 / Waiting 1 / By Status / By Project
  - tab **Waiting**: heading "Tasks", 0 sections; 1 to-dos, 1 vendors
  - tab **By Status**: heading "Tasks", 0 sections; 7 to-dos, 1 vendors
  - tabs that would not press (the row changed once one was pressed): By Project
- reached by: bar: Messages (1 tap); first button "Team"; shot [phone](../../review/census/tasks/shots/phone_pm_messages.jpg)
- **Messages** (`chat`): heading "Messages", 1.0 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: none
  - lead: "The team's thread for this job. Every post is read by the assistant and becomes a proposal in the Inbox when it changes the project."
  - records: 1 message threads
  - fields: Search conversations
  - tab groups: Team / Mail 1 / Field 2
  - tab **Mail**: heading "Messages", 1 sections; 1 mail (the tab leaves for `comms`)
  - tab **Field**: heading "Messages", 0 sections; 2 site questions, 1 schedule lines
- reached by: menu › Company › Meetings (3 taps); first button "Paste Notes"; shot [phone](../../review/census/tasks/shots/phone_pm_meetings.jpg)
- **Meetings** (`meetings`): heading "Meetings", 0.8 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: none
  - lead: "What was said, what was decided, who owes what — read from the notes Gemini takes, and turned into the record."
  - figures: Meetings to Review 2; Not Matched 0; Carried Over 2; Changes with the Owner 3
  - records: 2 meetings
  - columns: table: Date, Meeting, Project, With, Next Steps, Waiting, Status (2 rows)
  - fields: Search…
  - tab groups: Meetings / What We Are Learning / Changes · 3 / Settings
  - tab **What We Are Learning**: heading "Meetings", 9 sections; 6 decisions, 2 meetings, 2 materials, 2 to-dos
  - tab **Changes ·**: heading "Meetings", 5 sections; 2 meetings, 1 materials
  - tab **Settings**: heading "Meetings", 5 sections

### Coordinator (Chen), desktop

- reached by: Today › Tasks (2 taps); also in Tasks; first button "List"; shot [desktop](../../review/census/tasks/shots/desktop_coord_tasks.jpg)
- **Tasks** (`tkall`): heading "Tasks", 0.6 screens tall, 0 sections (0 above the fold), 15 tab screens; blue: New Task
  - lead: "9 open for you · 55 across the firm"
  - records: 2 schedule lines, 1 to-dos, 1 decisions, 1 vendors, 1 obligations
  - fields: Search tasks, How the list is grouped
  - tab groups: List / Table / Board / Calendar; All Open 9 / My Week 3 / Waiting on Others 2 / Everything 55 / New View; Waiting on Carlos Millwork for the shop  / Owner: Chen Biron / Due Mon, Sep / Status: Waiting On
  - tab **Table**: heading "Tasks", 0 sections; 2 schedule lines, 1 to-dos, 1 decisions, 1 vendors
  - tab **Table › Owner**: heading "Tasks", 0 sections; 2 schedule lines, 1 to-dos, 1 decisions, 1 vendors
  - tab **Table › Status**: heading "Tasks", 0 sections; 2 schedule lines, 1 to-dos, 1 decisions, 1 vendors
  - tab **Board**: heading "Tasks", 0 sections; 2 schedule lines, 1 to-dos, 1 decisions, 1 vendors
  - tab **Calendar**: heading "Tasks", 0 sections; 2 schedule lines, 1 to-dos, 1 decisions, 1 obligations
  - tab **Calendar › Week**: heading "Tasks", 0 sections; 2 schedule lines, 1 to-dos, 1 decisions, 1 obligations
  - tab **All Open**: heading "Tasks", 0 sections; 7 schedule lines, 2 to-dos, 1 decisions, 1 materials
  - tab **Waiting on Others**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Waiting on Others › Owner: Alan**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Waiting on Others › Due Sat, Sep**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Waiting on Others › Status: Waiting On**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Everything**: heading "Tasks", 0 sections; 29 to-dos, 25 schedule lines, 5 contacts, 5 obligations
  - tab **Owner: Chen Biron**: heading "Tasks", 0 sections; 2 schedule lines, 1 to-dos, 1 decisions, 1 vendors
  - tab **Due Mon, Sep**: heading "Tasks", 0 sections; 2 schedule lines, 1 to-dos, 1 decisions, 1 vendors
  - tab **Status: Waiting On**: heading "Tasks", 0 sections; 2 schedule lines, 1 to-dos, 1 decisions, 1 vendors
  - tabs that would not press (the row changed once one was pressed): New View
- reached by: Messages (1 tap); first button "Team"; shot [desktop](../../review/census/tasks/shots/desktop_coord_messages.jpg)
- **Messages** (`chat`): heading "Messages", 0.9 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: Record a voice note
  - lead: "A private conversation. Only the people in it can read it."
  - records: 1 purchase orders, 1 files, 1 vendors, 1 message threads
  - fields: Search conversations, Message
  - tab groups: Team / Mail 1 / Field 1; A Angel You: Yes, Tino confirmed it. Her / Site Leads Angel: Will do. The electrici / Start a Chat on a Job 8 job conversation
  - tab **Mail**: heading "Messages", 0 sections; 1 mail (the tab leaves for `comms`)
  - tab **Field**: heading "Messages", 0 sections; 1 materials, 1 site questions
  - tab **Site Leads Angel: Will do. The electrici**: heading "Messages", 0 sections; 1 vendors, 1 message threads
  - tabs that would not press (the row changed once one was pressed): Start a Chat on a Job 8 job conversation
- reached by: Company › Meetings (2 taps); first button "Paste Notes"; shot [desktop](../../review/census/tasks/shots/desktop_coord_meetings.jpg)
- **Meetings** (`meetings`): heading "Meetings", 0.6 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: none
  - lead: "What was said, what was decided, who owes what — read from the notes Gemini takes, and turned into the record."
  - figures: Meetings to Review 2; Not Matched 0; Carried Over 2; Changes with the Owner 3
  - records: 2 meetings
  - columns: table: DATE, MEETING, PROJECT, WITH, NEXT STEPS, WAITING, STATUS (2 rows)
  - fields: Search…
  - tab groups: Meetings / What We Are Learning / Changes · 3 / Settings
  - tab **What We Are Learning**: heading "Meetings", 9 sections; 6 decisions, 2 meetings, 2 materials, 2 to-dos
  - tab **Changes ·**: heading "Meetings", 5 sections; 2 meetings, 1 materials
  - tab **Settings**: heading "Meetings", 5 sections

### Coordinator (Chen), phone

- reached by: bar: Tasks (1 tap); also in Tasks; first button "Menu"; shot [phone](../../review/census/tasks/shots/phone_coord_tasks.jpg)
- **Tasks** (`tkall`): heading "Tasks", 1.0 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: none
  - records: 2 schedule lines, 1 to-dos, 1 decisions, 1 vendors, 1 obligations
  - fields: Add a task
  - tab groups: Due Soon 3 / Waiting 1 / By Status / By Project
  - tab **Waiting**: heading "Tasks", 0 sections; 1 to-dos, 1 vendors
  - tab **By Status**: heading "Tasks", 0 sections; 2 schedule lines, 1 to-dos, 1 decisions, 1 vendors
  - tabs that would not press (the row changed once one was pressed): By Project
- reached by: bar: Messages (1 tap); first button "Team"; shot [phone](../../review/census/tasks/shots/phone_coord_messages.jpg)
- **Messages** (`chat`): heading "Messages", 1.0 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: none
  - lead: "The team's thread for this job. Every post is read by the assistant and becomes a proposal in the Inbox when it changes the project."
  - records: 1 vendors, 1 message threads
  - fields: Search conversations
  - tab groups: Team / Mail 1 / Field 1
  - tab **Mail**: heading "Messages", 1 sections; 1 mail (the tab leaves for `comms`)
  - tab **Field**: heading "Messages", 0 sections; 1 materials, 1 site questions
- reached by: menu › Company › Meetings (3 taps); first button "Paste Notes"; shot [phone](../../review/census/tasks/shots/phone_coord_meetings.jpg)
- **Meetings** (`meetings`): heading "Meetings", 0.8 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: none
  - lead: "What was said, what was decided, who owes what — read from the notes Gemini takes, and turned into the record."
  - figures: Meetings to Review 2; Not Matched 0; Carried Over 2; Changes with the Owner 3
  - records: 2 meetings
  - columns: table: Date, Meeting, Project, With, Next Steps, Waiting, Status (2 rows)
  - fields: Search…
  - tab groups: Meetings / What We Are Learning / Changes · 3 / Settings
  - tab **What We Are Learning**: heading "Meetings", 9 sections; 6 decisions, 2 meetings, 2 materials, 2 to-dos
  - tab **Changes ·**: heading "Meetings", 5 sections; 2 meetings, 1 materials
  - tab **Settings**: heading "Meetings", 5 sections

### Designer (Sarah), desktop

- reached by: Today › Tasks (2 taps); also in Tasks; first button "List"; shot [desktop](../../review/census/tasks/shots/desktop_designer_tasks.jpg)
- **Tasks** (`tkall`): heading "Tasks", 0.4 screens tall, 0 sections (0 above the fold), 15 tab screens; blue: New Task
  - lead: "1 open for you · 55 across the firm"
  - records: 1 to-dos, 1 site questions
  - fields: Search tasks, How the list is grouped
  - tab groups: List / Table / Board / Calendar; All Open 1 / My Week 1 / Waiting on Others 2 / Everything 55 / New View
  - tab **Table**: heading "Tasks", 0 sections; 1 to-dos, 1 site questions
  - tab **Table › Owner**: heading "Tasks", 0 sections; 1 to-dos, 1 site questions
  - tab **Table › Status**: heading "Tasks", 0 sections; 1 to-dos, 1 site questions
  - tab **Board**: heading "Tasks", 0 sections; 1 to-dos, 1 site questions
  - tab **Calendar**: heading "Tasks", 0 sections; 1 to-dos, 1 site questions
  - tab **Calendar › Week**: heading "Tasks", 0 sections; 1 to-dos, 1 site questions
  - tab **All Open**: heading "Tasks", 0 sections; 1 to-dos, 1 site questions
  - tab **Waiting on Others**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Waiting on Others › Owner: Alan**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Waiting on Others › Due Sat, Sep**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Waiting on Others › Status: Waiting On**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Waiting on Others › Owner: Chen Biron**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Waiting on Others › Due Mon, Sep**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Waiting on Others › Status: Waiting On**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Everything**: heading "Tasks", 0 sections; 29 to-dos, 25 schedule lines, 5 contacts, 5 obligations
  - tabs that would not press (the row changed once one was pressed): New View
- reached by: Messages (1 tap); first button "Team"; shot [desktop](../../review/census/tasks/shots/desktop_designer_messages.jpg)
- **Messages** (`chat`): heading "Messages", 0.9 screens tall, 0 sections (0 above the fold), 8 tab screens; blue: Record a voice note
  - lead: "The team's thread for this job. Every post is read by the assistant and becomes a proposal in the Inbox when it changes the project."
  - fields: Search conversations, Message
  - empty states: "No messages yet Post what happened on site today. Everyone on the job's team reads it."
  - tab groups: Team / Mail 1; 121 State Street Team No messages yet / 121 State Street Client No messages yet / 140 Prospect Place Team No messages yet / 140 Prospect Place Client No messages ye / 206 Lenox Team No messages yet / 206 Lenox Client No messages yet / 45 Cranberry St Team No messages yet / 45 Cranberry St Client No messages yet
  - tab **Mail**: heading "Messages", 0 sections; 1 mail (the tab leaves for `comms`)
  - tab **121 State Street Client No messages yet**: heading "Messages", 0 sections; 1 clients
  - tab **140 Prospect Place Team No messages yet**: heading "Messages", 0 sections
  - tab **140 Prospect Place Client No messages ye**: heading "Messages", 0 sections; 1 clients
  - tab **206 Lenox Team No messages yet**: heading "Messages", 0 sections
  - tab **206 Lenox Client No messages yet**: heading "Messages", 0 sections; 1 clients
  - tab **45 Cranberry St Team No messages yet**: heading "Messages", 0 sections
  - tab **45 Cranberry St Client No messages yet**: heading "Messages", 0 sections; 1 clients

### Designer (Sarah), phone

- reached by: menu › Today › Tasks (3 taps); also in Tasks; first button "Menu"; shot [phone](../../review/census/tasks/shots/phone_designer_tasks.jpg)
- **Tasks** (`tkall`): heading "Tasks", 1.0 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: none
  - records: 1 to-dos, 1 site questions
  - fields: Add a task
  - tab groups: Due Soon 1 / Waiting 0 / By Status / By Project
  - tab **Waiting**: heading "Tasks", 0 sections (nearly empty (22 words))
  - tab **By Status**: heading "Tasks", 0 sections; 1 to-dos, 1 site questions
  - tabs that would not press (the row changed once one was pressed): By Project
- reached by: bar: Messages (1 tap); first button "Team"; shot [phone](../../review/census/tasks/shots/phone_designer_messages.jpg)
- **Messages** (`chat`): heading "Messages", 1.0 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: none
  - lead: "The team's thread for this job. Every post is read by the assistant and becomes a proposal in the Inbox when it changes the project."
  - fields: Search conversations
  - tab groups: Team / Mail 1; 121 State Street Team No messages yet / 121 State Street Client No messages yet / 140 Prospect Place Team No messages yet / 140 Prospect Place Client No messages ye / 206 Lenox Team No messages yet / 206 Lenox Client No messages yet / 45 Cranberry St Team No messages yet / 45 Cranberry St Client No messages yet
  - tab **Mail**: heading "Messages", 1 sections; 1 mail (the tab leaves for `comms`)
  - tab **121 State Street Client No messages yet**: heading "Messages", 0 sections; 1 clients
  - tabs that would not press (the row changed once one was pressed): 140 Prospect Place Team No messages yet, 140 Prospect Place Client No messages ye, 206 Lenox Team No messages yet, 206 Lenox Client No messages yet, 45 Cranberry St Team No messages yet, 45 Cranberry St Client No messages yet

### Billing, desktop

- reached by: Today › Tasks (2 taps); also in Tasks; first button "List"; shot [desktop](../../review/census/tasks/shots/desktop_billing_tasks.jpg)
- **Tasks** (`tkall`): heading "Tasks", 0.3 screens tall, 0 sections (0 above the fold), 15 tab screens; blue: New Task
  - lead: "0 open for you · 55 across the firm"
  - fields: Search tasks, How the list is grouped
  - empty states: "Nothing due in the next 7 days, and nothing late."
  - tab groups: List / Table / Board / Calendar; All Open 0 / My Week 0 / Waiting on Others 2 / Everything 55 / New View
  - tab **Table**: heading "Tasks", 0 sections
  - tab **Table › Owner**: heading "Tasks", 0 sections
  - tab **Table › Status**: heading "Tasks", 0 sections
  - tab **Board**: heading "Tasks", 0 sections
  - tab **Calendar**: heading "Tasks", 0 sections
  - tab **Calendar › Week**: heading "Tasks", 0 sections
  - tab **All Open**: heading "Tasks", 0 sections
  - tab **Waiting on Others**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Waiting on Others › Owner: Alan**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Waiting on Others › Due Sat, Sep**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Waiting on Others › Status: Waiting On**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Waiting on Others › Owner: Chen Biron**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Waiting on Others › Due Mon, Sep**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Waiting on Others › Status: Waiting On**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Everything**: heading "Tasks", 0 sections; 29 to-dos, 25 schedule lines, 5 contacts, 5 obligations
  - tabs that would not press (the row changed once one was pressed): New View
- reached by: Messages (1 tap); first button "Team"; shot [desktop](../../review/census/tasks/shots/desktop_billing_messages.jpg)
- **Messages** (`chat`): heading "Messages", 0.9 screens tall, 0 sections (0 above the fold), 9 tab screens; blue: Record a voice note
  - lead: "The team's thread for this job. Every post is read by the assistant and becomes a proposal in the Inbox when it changes the project."
  - fields: Search conversations, Message
  - empty states: "No messages yet Post what happened on site today. Everyone on the job's team reads it."
  - tab groups: Team / Mail 1 / Field; 121 State Street Team No messages yet / 121 State Street Client No messages yet / 140 Prospect Place Team No messages yet / 140 Prospect Place Client No messages ye / 206 Lenox Team No messages yet / 206 Lenox Client No messages yet / 45 Cranberry St Team No messages yet / 45 Cranberry St Client No messages yet
  - tab **Mail**: heading "Messages", 0 sections; 1 mail (the tab leaves for `comms`)
  - tab **Field**: heading "Messages", 0 sections
  - tab **121 State Street Client No messages yet**: heading "Messages", 0 sections; 1 clients
  - tab **140 Prospect Place Team No messages yet**: heading "Messages", 0 sections
  - tab **140 Prospect Place Client No messages ye**: heading "Messages", 0 sections; 1 clients
  - tab **206 Lenox Team No messages yet**: heading "Messages", 0 sections
  - tab **206 Lenox Client No messages yet**: heading "Messages", 0 sections; 1 clients
  - tab **45 Cranberry St Team No messages yet**: heading "Messages", 0 sections
  - tab **45 Cranberry St Client No messages yet**: heading "Messages", 0 sections; 1 clients
- reached by: More › Meetings (2 taps); first button "Paste Notes"; shot [desktop](../../review/census/tasks/shots/desktop_billing_meetings.jpg)
- **Meetings** (`meetings`): heading "Meetings", 0.6 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: none
  - lead: "What was said, what was decided, who owes what — read from the notes Gemini takes, and turned into the record."
  - figures: Meetings to Review 2; Not Matched 0; Carried Over 2; Changes with the Owner 3
  - records: 2 meetings
  - columns: table: DATE, MEETING, PROJECT, WITH, NEXT STEPS, WAITING, STATUS (2 rows)
  - fields: Search…
  - tab groups: Meetings / What We Are Learning / Changes · 3 / Settings
  - tab **What We Are Learning**: heading "Meetings", 9 sections; 6 decisions, 2 meetings, 2 materials, 2 to-dos
  - tab **Changes ·**: heading "Meetings", 5 sections; 2 meetings, 1 materials
  - tab **Settings**: heading "Meetings", 5 sections

### Billing, phone

- reached by: menu › Today › Tasks (3 taps); also in Tasks; first button "Menu"; shot [phone](../../review/census/tasks/shots/phone_billing_tasks.jpg)
- **Tasks** (`tkall`): heading "Tasks", 1.0 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: none
  - fields: Add a task
  - empty states: "Nothing due in the next 7 days, and nothing late."
  - tab groups: Due Soon 0 / Waiting 0 / By Status / By Project
  - tab **Waiting**: heading "Tasks", 0 sections (nearly empty (22 words))
  - tab **By Status**: heading "Tasks", 0 sections (nearly empty (24 words))
  - tabs that would not press (the row changed once one was pressed): By Project
- reached by: bar: Messages (1 tap); first button "Team"; shot [phone](../../review/census/tasks/shots/phone_billing_messages.jpg)
- **Messages** (`chat`): heading "Messages", 1.0 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: none
  - lead: "The team's thread for this job. Every post is read by the assistant and becomes a proposal in the Inbox when it changes the project."
  - fields: Search conversations
  - tab groups: Team / Mail 1 / Field; 121 State Street Team No messages yet / 121 State Street Client No messages yet / 140 Prospect Place Team No messages yet / 140 Prospect Place Client No messages ye / 206 Lenox Team No messages yet / 206 Lenox Client No messages yet / 45 Cranberry St Team No messages yet / 45 Cranberry St Client No messages yet
  - tab **Mail**: heading "Messages", 1 sections; 1 mail (the tab leaves for `comms`)
  - tab **Field**: heading "Messages", 0 sections
  - tab **121 State Street Client No messages yet**: heading "Messages", 0 sections; 1 clients
  - tabs that would not press (the row changed once one was pressed): 140 Prospect Place Team No messages yet, 140 Prospect Place Client No messages ye, 206 Lenox Team No messages yet, 206 Lenox Client No messages yet, 45 Cranberry St Team No messages yet, 45 Cranberry St Client No messages yet
- reached by: menu › More › swipe the strip, Meetings (3 taps); first button "Paste Notes"; shot [phone](../../review/census/tasks/shots/phone_billing_meetings.jpg)
- **Meetings** (`meetings`): heading "Meetings", 0.8 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: none
  - lead: "What was said, what was decided, who owes what — read from the notes Gemini takes, and turned into the record."
  - figures: Meetings to Review 2; Not Matched 0; Carried Over 2; Changes with the Owner 3
  - records: 2 meetings
  - columns: table: Date, Meeting, Project, With, Next Steps, Waiting, Status (2 rows)
  - fields: Search…
  - tab groups: Meetings / What We Are Learning / Changes · 3 / Settings
  - tab **What We Are Learning**: heading "Meetings", 9 sections; 6 decisions, 2 meetings, 2 materials, 2 to-dos
  - tab **Changes ·**: heading "Meetings", 5 sections; 2 meetings, 1 materials
  - tab **Settings**: heading "Meetings", 5 sections

### Controller, desktop

- reached by: Today › Tasks (2 taps); also in Tasks; first button "List"; shot [desktop](../../review/census/tasks/shots/desktop_controller_tasks.jpg)
- **Tasks** (`tkall`): heading "Tasks", 0.4 screens tall, 0 sections (0 above the fold), 15 tab screens; blue: New Task
  - lead: "1 open for you · 55 across the firm"
  - records: 1 to-dos
  - fields: Search tasks, How the list is grouped
  - tab groups: List / Table / Board / Calendar; All Open 1 / My Week 1 / Waiting on Others 2 / Everything 55 / New View
  - tab **Table**: heading "Tasks", 0 sections; 1 to-dos
  - tab **Table › Owner**: heading "Tasks", 0 sections; 1 to-dos
  - tab **Table › Status**: heading "Tasks", 0 sections; 1 to-dos
  - tab **Board**: heading "Tasks", 0 sections; 1 to-dos
  - tab **Calendar**: heading "Tasks", 0 sections; 1 to-dos
  - tab **Calendar › Week**: heading "Tasks", 0 sections; 1 to-dos
  - tab **All Open**: heading "Tasks", 0 sections; 1 to-dos
  - tab **Waiting on Others**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Waiting on Others › Owner: Alan**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Waiting on Others › Due Sat, Sep**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Waiting on Others › Status: Waiting On**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Waiting on Others › Owner: Chen Biron**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Waiting on Others › Due Mon, Sep**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Waiting on Others › Status: Waiting On**: heading "Tasks", 0 sections; 2 to-dos, 2 vendors
  - tab **Everything**: heading "Tasks", 0 sections; 29 to-dos, 25 schedule lines, 5 contacts, 5 obligations
  - tabs that would not press (the row changed once one was pressed): New View
- reached by: Messages (1 tap); first button "Team"; shot [desktop](../../review/census/tasks/shots/desktop_controller_messages.jpg)
- **Messages** (`chat`): heading "Messages", 0.9 screens tall, 0 sections (0 above the fold), 9 tab screens; blue: Record a voice note
  - lead: "The team's thread for this job. Every post is read by the assistant and becomes a proposal in the Inbox when it changes the project."
  - fields: Search conversations, Message
  - empty states: "No messages yet Post what happened on site today. Everyone on the job's team reads it."
  - tab groups: Team / Mail 1 / Field; 121 State Street Team No messages yet / 121 State Street Client No messages yet / 140 Prospect Place Team No messages yet / 140 Prospect Place Client No messages ye / 206 Lenox Team No messages yet / 206 Lenox Client No messages yet / 45 Cranberry St Team No messages yet / 45 Cranberry St Client No messages yet
  - tab **Mail**: heading "Messages", 0 sections; 1 mail (the tab leaves for `comms`)
  - tab **Field**: heading "Messages", 0 sections
  - tab **121 State Street Client No messages yet**: heading "Messages", 0 sections; 1 clients
  - tab **140 Prospect Place Team No messages yet**: heading "Messages", 0 sections
  - tab **140 Prospect Place Client No messages ye**: heading "Messages", 0 sections; 1 clients
  - tab **206 Lenox Team No messages yet**: heading "Messages", 0 sections
  - tab **206 Lenox Client No messages yet**: heading "Messages", 0 sections; 1 clients
  - tab **45 Cranberry St Team No messages yet**: heading "Messages", 0 sections
  - tab **45 Cranberry St Client No messages yet**: heading "Messages", 0 sections; 1 clients
- reached by: More › Meetings (2 taps); first button "Paste Notes"; shot [desktop](../../review/census/tasks/shots/desktop_controller_meetings.jpg)
- **Meetings** (`meetings`): heading "Meetings", 0.6 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: none
  - lead: "What was said, what was decided, who owes what — read from the notes Gemini takes, and turned into the record."
  - figures: Meetings to Review 2; Not Matched 0; Carried Over 2; Changes with the Owner 3
  - records: 2 meetings
  - columns: table: DATE, MEETING, PROJECT, WITH, NEXT STEPS, WAITING, STATUS (2 rows)
  - fields: Search…
  - tab groups: Meetings / What We Are Learning / Changes · 3 / Settings
  - tab **What We Are Learning**: heading "Meetings", 9 sections; 6 decisions, 2 meetings, 2 materials, 2 to-dos
  - tab **Changes ·**: heading "Meetings", 5 sections; 2 meetings, 1 materials
  - tab **Settings**: heading "Meetings", 5 sections

### Controller, phone

- reached by: menu › Today › Tasks (3 taps); also in Tasks; first button "Menu"; shot [phone](../../review/census/tasks/shots/phone_controller_tasks.jpg)
- **Tasks** (`tkall`): heading "Tasks", 1.0 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: none
  - records: 1 to-dos
  - fields: Add a task
  - tab groups: Due Soon 1 / Waiting 0 / By Status / By Project
  - tab **Waiting**: heading "Tasks", 0 sections (nearly empty (22 words))
  - tab **By Status**: heading "Tasks", 0 sections; 1 to-dos
  - tabs that would not press (the row changed once one was pressed): By Project
- reached by: bar: Messages (1 tap); first button "Team"; shot [phone](../../review/census/tasks/shots/phone_controller_messages.jpg)
- **Messages** (`chat`): heading "Messages", 1.0 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: none
  - lead: "The team's thread for this job. Every post is read by the assistant and becomes a proposal in the Inbox when it changes the project."
  - fields: Search conversations
  - tab groups: Team / Mail 1 / Field; 121 State Street Team No messages yet / 121 State Street Client No messages yet / 140 Prospect Place Team No messages yet / 140 Prospect Place Client No messages ye / 206 Lenox Team No messages yet / 206 Lenox Client No messages yet / 45 Cranberry St Team No messages yet / 45 Cranberry St Client No messages yet
  - tab **Mail**: heading "Messages", 1 sections; 1 mail (the tab leaves for `comms`)
  - tab **Field**: heading "Messages", 0 sections
  - tab **121 State Street Client No messages yet**: heading "Messages", 0 sections; 1 clients
  - tabs that would not press (the row changed once one was pressed): 140 Prospect Place Team No messages yet, 140 Prospect Place Client No messages ye, 206 Lenox Team No messages yet, 206 Lenox Client No messages yet, 45 Cranberry St Team No messages yet, 45 Cranberry St Client No messages yet
- reached by: menu › More › swipe the strip, Meetings (3 taps); first button "Paste Notes"; shot [phone](../../review/census/tasks/shots/phone_controller_meetings.jpg)
- **Meetings** (`meetings`): heading "Meetings", 0.8 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: none
  - lead: "What was said, what was decided, who owes what — read from the notes Gemini takes, and turned into the record."
  - figures: Meetings to Review 2; Not Matched 0; Carried Over 2; Changes with the Owner 3
  - records: 2 meetings
  - columns: table: Date, Meeting, Project, With, Next Steps, Waiting, Status (2 rows)
  - fields: Search…
  - tab groups: Meetings / What We Are Learning / Changes · 3 / Settings
  - tab **What We Are Learning**: heading "Meetings", 9 sections; 6 decisions, 2 meetings, 2 materials, 2 to-dos
  - tab **Changes ·**: heading "Meetings", 5 sections; 2 meetings, 1 materials
  - tab **Settings**: heading "Meetings", 5 sections

## 7. The Other Roles, One Line a Page

### Foreman (Angel), desktop

- reached by: Messages (1 tap); shot [desktop](../../review/census/tasks/shots/desktop_foreman_messages.jpg)
- **Messages** (`chat`): heading "Messages", 0.9 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: Record a voice note

### Foreman (Angel), phone

- reached by: bar: Messages (1 tap); shot [phone](../../review/census/tasks/shots/phone_foreman_messages.jpg)
- **Messages** (`chat`): heading "Messages", 1.0 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: none

### Crew (Alberto), desktop

- reached by: Messages (1 tap); shot [desktop](../../review/census/tasks/shots/desktop_crew_messages.jpg)
- **Messages** (`chat`): heading "Messages", 0.9 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: Record a voice note

### Crew (Alberto), phone

- reached by: bar: Messages (1 tap); shot [phone](../../review/census/tasks/shots/phone_crew_messages.jpg)
- **Messages** (`chat`): heading "Messages", 0.9 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: none; nearly empty (24 words)

### Driver (Alex), desktop

- reached by: Messages (1 tap); shot [desktop](../../review/census/tasks/shots/desktop_driver_messages.jpg)
- **Messages** (`chat`): heading "Messages", 0.9 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: Record a voice note

### Driver (Alex), phone

- reached by: bar: Messages (1 tap); shot [phone](../../review/census/tasks/shots/phone_driver_messages.jpg)
- **Messages** (`chat`): heading "Messages", 0.9 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: none; nearly empty (24 words)

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

