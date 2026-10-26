# The Field and Site Module, Page by Page: the Census

**Asked by Alan, 2026-10-26:** "Go through all the modules with screenshots. It's important to understand the format of every page and what's on it." The loop's experts and the client expert walk every page of their module with this in hand in round one of the improvement loop (docs/IMPROVEMENT_LOOP.md).

**What this is.** A machine inventory, not a judgment, in the format of the Projects census (`docs/modules/projects_census.md`). No app code changed. `tests/module_census.py` (its helpers `tests/module_census_js.js` sit on the projects census's reader `tests/census_js.js` and the information map's `tests/ia_js.js`) signs in as each role on a fresh app at 1440 and at 390, reads the role's running menu, and reaches each page of this module the way the person does: the phone bar, or the menu (the hamburger on the phone), the group, then the strip. It presses every tab of every tab group and the tabs those reveal, follows the page's own links to this module's pages the menu did not reach, reads every screen and shoots it. The primary role is the foreman and the PM; every role whose menu holds a page of this module is walked. Job-scoped pages show **121 State Street** wherever the role may open it.

**Where this module's pages sit.** The PM's, owner's and coordinator's field pages (Field, Photos, Deliveries, Drawings, Daily Log) sit in the Projects menu group and are in the Projects census; here those roles reach Requests and Route through More. The foreman, crew and driver reach their field pages from their own menus.

**Build bd3180c27e33** (master 1cc2eb9), the one build every module census of this round ran on. 120 screens in all. Walked 2026-10-26 06:29 on the demo day (Thu 2026-09-03); the walk of every module took 54.4 minutes. Raw read: `review/census/field/data.json`. Every screen per role in tables: `review/census/field/tables.md`. Screenshots of every screen, both devices: `review/census/field/shots/` (`desktop_` or `phone_`, the role, the page, then the tab; up to 3 desktop or 5 phone screens tall). The first screen of each page is committed; the tabs stay on the machine that ran it.

Run it: `python3 build.py && cd tests && ./slot.sh python3 module_census.py --module field` (then `python3 module_census.py --report` rewrites every module's page from data.json).

## Headline

- **Foreman (Angel): 9 pages with 23 more screens behind their tabs on the desktop (9 pages and 19 tab screens on the phone)**, about 15 desktop screens end to end.
- **PM (Alan): 2 pages with 0 more screens behind their tabs on the desktop (2 pages and 0 tab screens on the phone)**, about 2 desktop screens end to end.
- **Pages each role reaches in this module, desktop:** Owner 2, PM 2, Coordinator 2, Foreman 9, Crew 5, Driver 3.
- **Reached only one way** by Foreman (Angel): Daily Log (desktop), Documents (desktop and phone), Drawings (desktop and phone), Photos (desktop and phone), Schedule (desktop and phone) (one menu entry, not on the phone bar, and no walked page links to it; section 1).
- **Reached only one way** by PM (Alan): Requests (phone) (one menu entry, not on the phone bar, and no walked page links to it; section 1).
- **21 records show on two or more of this module's pages** for Foreman (Angel) on the desktop (11 schedule lines, 3 vendors, 2 materials, 2 field requests). "Restoration" is on 5: Daily Log, Photos, Raise, Schedule, Site.
- **1 pairs of pages list largely the same records,** led by Daily Log and Schedule (8 shared).
- **The same records in other modules** (Foreman, desktop): Today › Today lists 16; Tasks and Messages › Messages lists 7 of the 118 records this module lists.
- **On the phone** (Foreman): 4 of the 9 pages are taller than three screens (Site, Drawings, Schedule, Documents); 3 have no section heading above the fold; 0 screens scroll sideways.
- **Nothing crashed and no page raised an error**; every page opened.
- **1 screen(s) saved while the census only read and pressed tabs** (Coordinator (Chen) desktop, Requests). Each role ran on a fresh app, so a save never reached the next role.

## 1. The Tree, Role by Role

**Pages** are the module's pages the role reaches from its menu (and the links those pages show). **Tabs** are the screens behind each page's tab groups, and behind the tabs those reveal. **Sections** are the headed parts of each page as it opens. Each cell reads desktop / phone.

| Role | Primary | First page of the module, reached by (desktop / phone) | Pages | Tab screens | Sections | Screens |
|---|---|---|---|---|---|---|
| Owner |  | More (1 tap) / menu › More (2 taps) | 2 / 2 | 0 / 0 | 8 / 8 | 2 / 2 |
| PM (Alan) | yes | More › Requests (2 taps) / menu › More › swipe the strip, Requests (3 taps) | 2 / 2 | 0 / 0 | 7 / 7 | 2 / 2 |
| Coordinator (Chen) |  | More › Requests (2 taps) / menu › More › swipe the strip, Requests (3 taps) | 2 / 2 | 0 / 0 | 9 / 9 | 2 / 2 |
| Foreman (Angel) | yes | Daily Log (1 tap) / bar: Daily Log (1 tap) | 9 / 9 | 23 / 19 | 15 / 29 | 32 / 28 |
| Crew (Alberto) |  | Requests (1 tap) / bar: Requests (1 tap) | 5 / 5 | 11 / 7 | 4 / 18 | 16 / 12 |
| Driver (Alex) |  | Route (1 tap) / bar: Route (1 tap) | 3 / 3 | 7 / 7 | 8 / 8 | 10 / 10 |

### Which pages each role reaches (desktop)

Each cell is the number of screens the page has (the page and its tabs); "-" means the role does not reach it.

| Page | Owner | PM | Coordinator | Foreman | Crew | Driver |
|---|---|---|---|---|---|---|
| Requests | 1 | 1 | 1 | 1 | 1 | 1 |
| Route | 1 | 1 | 1 | - | - | 1 |
| Daily Log | - | - | - | 7 | - | - |
| Site | - | - | - | 1 | - | - |
| Crew | - | - | - | 1 | - | - |
| Drawings | - | - | - | 1 | 1 | - |
| Schedule | - | - | - | 5 | 5 | - |
| Photos | - | - | - | 7 | 8 | - |
| Documents | - | - | - | 8 | - | - |
| Raise | - | - | - | 1 | - | - |
| Deliveries | - | - | - | - | 1 | - |
| Receipts | - | - | - | - | - | 8 |

### Foreman (Angel)'s tree at a glance

Reached by is the taps from the role's first page, desktop then phone. Tall is in screens, desktop / phone. Sections are the headed parts as the page opens (phone above the fold). Tabs are the screens behind its tab groups, desktop / phone. "What it lists" counts the records found on the page as it opens.

| Page | Reached by (desktop / phone) | Heading | Tall | Sections (phone above the fold) | Tabs | Tiles and figures | What it lists | Blue button | First button | Shots |
|---|---|---|---|---|---|---|---|---|---|---|
| Daily Log | Daily Log (1 tap) / bar: Daily Log (1 tap) | Daily Log | 1.4 / 2.1 | 3 (3) | 6 / 6 | - | - | Next | Weather | [desktop](../../review/census/field/shots/desktop_foreman_daily_log.jpg) [phone](../../review/census/field/shots/phone_foreman_daily_log.jpg) |
| Site | Site (1 tap) / bar: Site (1 tap) | Site | 3.3 / 3.5 | 4 (1) | 0 / 0 | - | 7 schedule lines, 4 materials, 4 inspections, 3 subs to confirm | none | Add a Sub Day | [desktop](../../review/census/field/shots/desktop_foreman_site.jpg) [phone](../../review/census/field/shots/phone_foreman_site.jpg) |
| Requests | Requests (1 tap) / bar: Requests (1 tap) | Requests | 0.8 / 1.1 | 1 (1) | 0 / 0 | - | 3 schedule lines, 2 field requests, 2 materials | Send the Request | Open the Kit | [desktop](../../review/census/field/shots/desktop_foreman_requests.jpg) [phone](../../review/census/field/shots/phone_foreman_requests.jpg) |
| Crew | Crew (1 tap) / menu › Crew (2 taps) | Crew | 1.3 / 2.0 | 4 (2) | 0 / 0 | - | 1 schedule lines | Approve 2 Clean | Call | [desktop](../../review/census/field/shots/desktop_foreman_crew.jpg) [phone](../../review/census/field/shots/phone_foreman_crew.jpg) |
| Drawings | Drawings (1 tap) / menu › Drawings (2 taps) | Drawings — 121 State Street | 2.8 / 5.5 | 3 (2) | 0 / 0 | Found Before Work 0; Found in the Field 1; Days to Resolve 3.8; Open Conflicts 0 | 2 vendors, 1 schedule lines, 1 subs to confirm, 1 files | none | Check the Sets | [desktop](../../review/census/field/shots/desktop_foreman_drawings.jpg) [phone](../../review/census/field/shots/phone_foreman_drawings.jpg) |
| Schedule | Schedule (1 tap) / menu › Schedule (2 taps) | Schedule | 1.0 / 3.1 | 0 (4) | 4 / 0 | - | 26 schedule lines, 3 materials, 1 vendors | none | Gantt | [desktop](../../review/census/field/shots/desktop_foreman_schedule.jpg) [phone](../../review/census/field/shots/phone_foreman_schedule.jpg) |
| Photos | Photos (1 tap) / menu › Photos (2 taps) | Photos | 1.5 / 2.3 | 0 (0) | 6 / 6 | - | 2 schedule lines, 1 files, 1 vendors, 1 purchase orders | Add Photos | All | [desktop](../../review/census/field/shots/desktop_foreman_photos.jpg) [phone](../../review/census/field/shots/phone_foreman_photos.jpg) |
| Documents | Documents (1 tap) / menu › Documents (2 taps) | Documents | 1.9 / 4.7 | 0 (0) | 7 / 7 | Added This Week 8; Unfiled 4; Drawings 24; Cards & Permits 0 | 33 files, 24 drawing sheets, 5 submittals, 4 vendors | Upload Files | Added This Week 8 0 from the | [desktop](../../review/census/field/shots/desktop_foreman_documents.jpg) [phone](../../review/census/field/shots/phone_foreman_documents.jpg) |
| Raise | Raise (1 tap) / menu › Raise (2 taps) | Raise | 1.1 / 1.5 | 0 (0) | 0 / 0 | - | 3 site questions, 2 field requests, 1 schedule lines, 1 materials | none | Materials or a Tool Studs, s | [desktop](../../review/census/field/shots/desktop_foreman_raise.jpg) [phone](../../review/census/field/shots/phone_foreman_raise.jpg) |

### PM (Alan)'s tree at a glance

Reached by is the taps from the role's first page, desktop then phone. Tall is in screens, desktop / phone. Sections are the headed parts as the page opens (phone above the fold). Tabs are the screens behind its tab groups, desktop / phone. "What it lists" counts the records found on the page as it opens.

| Page | Reached by (desktop / phone) | Heading | Tall | Sections (phone above the fold) | Tabs | Tiles and figures | What it lists | Blue button | First button | Shots |
|---|---|---|---|---|---|---|---|---|---|---|
| Requests | More › Requests (2 taps) / menu › More › swipe the strip, Requests (3 taps) | Requests | 0.9 / 1.2 | 1 (1) | 0 / 0 | - | 3 schedule lines, 2 field requests, 2 materials | Send the Request | Open the Kit | [desktop](../../review/census/field/shots/desktop_pm_requests.jpg) [phone](../../review/census/field/shots/phone_pm_requests.jpg) |
| Route | More › Route (2 taps) / menu › More › swipe the strip, Route (3 taps) | Route | 1.3 / 2.5 | 6 (3) | 0 / 0 | - | 2 field requests, 2 materials, 1 vendors | Approve Route | Count This | [desktop](../../review/census/field/shots/desktop_pm_route.jpg) [phone](../../review/census/field/shots/phone_pm_route.jpg) |

### How each page is reached, and the pages reached only one way

Menu places are the role's menu entries that open the page (a page in two groups has two). The phone bar counts as one more way in on the phone (its pages are in the menu too). Links are the walked pages, in any module, that show a link to it. **One way** means one menu place and nothing else: lose that entry and the page is lost.

| Role | Device | Page | Menu places | Phone bar | Linked from | Ways in |
|---|---|---|---|---|---|---|
| Owner | desktop | Requests | More › Requests | - | Purchasing › Buy Board | 2 |
| Owner | desktop | Route | More › Route | - | Accounting › Controls | 2 |
| Owner | phone | Requests | More › Requests | - | - | 1 (one way) |
| Owner | phone | Route | More › Route | - | Accounting › Controls | 2 |
| PM (Alan) | desktop | Requests | More › Requests | - | Purchasing › Buy Board | 2 |
| PM (Alan) | desktop | Route | More › Route | - | Accounting › Controls | 2 |
| PM (Alan) | phone | Requests | More › Requests | - | - | 1 (one way) |
| PM (Alan) | phone | Route | More › Route | - | Accounting › Controls | 2 |
| Coordinator (Chen) | desktop | Requests | More › Requests | - | Purchasing › Buy Board, Sales and Clients › Forecast, Sales and Clients › Sales Dashboard, Today › Approvals and 1 more | 6 |
| Coordinator (Chen) | desktop | Route | More › Route | - | Sales and Clients › Forecast, Sales and Clients › Sales Dashboard, Today › Approvals, Today › Today | 5 |
| Coordinator (Chen) | phone | Requests | More › Requests | - | Sales and Clients › Forecast, Sales and Clients › Sales Dashboard, Today › Approvals, Today › Today | 5 |
| Coordinator (Chen) | phone | Route | More › Route | - | Today › Approvals | 2 |
| Foreman (Angel) | desktop | Daily Log | Daily Log | - | - | 1 (one way) |
| Foreman (Angel) | desktop | Site | Site | - | Today › Today | 2 |
| Foreman (Angel) | desktop | Requests | Requests | - | Field and Site › Site | 2 |
| Foreman (Angel) | desktop | Crew | Crew | - | Field and Site › Daily Log, Today › Today | 3 |
| Foreman (Angel) | desktop | Drawings | Drawings | - | - | 1 (one way) |
| Foreman (Angel) | desktop | Schedule | Schedule | - | - | 1 (one way) |
| Foreman (Angel) | desktop | Photos | Photos | - | - | 1 (one way) |
| Foreman (Angel) | desktop | Documents | Documents | - | - | 1 (one way) |
| Foreman (Angel) | desktop | Raise | Raise | - | Today › Today | 2 |
| Foreman (Angel) | phone | Daily Log | Daily Log | yes | - | 2 |
| Foreman (Angel) | phone | Site | Site | yes | Today › Today | 3 |
| Foreman (Angel) | phone | Requests | Requests | yes | Field and Site › Site | 3 |
| Foreman (Angel) | phone | Crew | Crew | - | Field and Site › Daily Log, Today › Today | 3 |
| Foreman (Angel) | phone | Drawings | Drawings | - | - | 1 (one way) |
| Foreman (Angel) | phone | Schedule | Schedule | - | - | 1 (one way) |
| Foreman (Angel) | phone | Photos | Photos | - | - | 1 (one way) |
| Foreman (Angel) | phone | Documents | Documents | - | - | 1 (one way) |
| Foreman (Angel) | phone | Raise | Raise | - | Today › Today | 2 |
| Crew (Alberto) | desktop | Requests | Requests | - | - | 1 (one way) |
| Crew (Alberto) | desktop | Schedule | Schedule | - | - | 1 (one way) |
| Crew (Alberto) | desktop | Photos | Photos | - | - | 1 (one way) |
| Crew (Alberto) | desktop | Deliveries | Deliveries | - | - | 1 (one way) |
| Crew (Alberto) | desktop | Drawings | Drawings | - | - | 1 (one way) |
| Crew (Alberto) | phone | Requests | Requests | yes | - | 2 |
| Crew (Alberto) | phone | Schedule | Schedule | yes | - | 2 |
| Crew (Alberto) | phone | Photos | Photos | - | - | 1 (one way) |
| Crew (Alberto) | phone | Deliveries | Deliveries | - | - | 1 (one way) |
| Crew (Alberto) | phone | Drawings | Drawings | - | - | 1 (one way) |
| Driver (Alex) | desktop | Route | Route | - | - | 1 (one way) |
| Driver (Alex) | desktop | Receipts | Receipts | - | - | 1 (one way) |
| Driver (Alex) | desktop | Requests | Requests | - | - | 1 (one way) |
| Driver (Alex) | phone | Route | Route | yes | - | 2 |
| Driver (Alex) | phone | Receipts | Receipts | yes | - | 2 |
| Driver (Alex) | phone | Requests | Requests | - | - | 1 (one way) |

## 2. Where the Data Lives, and Where It Shows Twice

Records are found by their own words (the information map's catalog, the job's nouns and this census's: clients, vendors, leads, contacts, companies, every invoice, bill and PO, payroll runs, stock, meetings, journals, obligations, lessons, partners, bank lines, threads), so these are floors. A page's tabs count as the page.

### Foreman (Angel), desktop: each kind of record, and the pages that list it

| Records | Found | Pages that list them (how many each) | Also in other modules |
|---|---|---|---|
| schedule lines | 28 | 8: Schedule 26, Daily Log 8, Site 7, Requests 3, Photos 2, Crew 1, Drawings 1, Raise 1 | Today › Today 11, Tasks and Messages › Messages 1 |
| vendors | 5 | 6: Documents 4, Site 3, Drawings 2, Daily Log 1, Schedule 1, Photos 1 | Today › Today 2, Tasks and Messages › Messages 1 |
| materials | 7 | 4: Site 4, Schedule 3, Requests 2, Raise 1 | Tasks and Messages › Messages 1 |
| files | 36 | 4: Documents 33, Site 2, Drawings 1, Photos 1 | Tasks and Messages › Messages 1 |
| site questions | 3 | 2: Raise 3, Daily Log 1 | Tasks and Messages › Messages 3, Today › Today 1 |
| purchase orders | 3 | 2: Site 2, Photos 1 | Tasks and Messages › Messages 1 |
| subs to confirm | 3 | 2: Site 3, Drawings 1 | Today › Today 3 |
| field requests | 2 | 2: Requests 2, Raise 2 | - |
| inspections | 4 | 1: Site 4 | - |
| obligations | 1 | 1: Site 1 | Today › Today 1 |
| drawing sheets | 24 | 1: Documents 24 | - |
| submittals | 5 | 1: Documents 5 | - |
| bills | 2 | 1: Documents 2 | - |

### Records on two or more pages, and lists that are the same list twice

**Owner, desktop:** 4 records on two or more pages: field requests 2 (up to 2 pages); materials 2 (up to 2 pages).

- the same list twice (3 or more shared records, at least half of the shorter list): Requests and Route (4 shared, of 7 and 4: field requests, materials)

**PM (Alan), desktop:** 4 records on two or more pages: field requests 2 (up to 2 pages); materials 2 (up to 2 pages).

- "2x4x8 KD studs" (field requests) on 2 pages: Requests, Route
- "Blue tape + 4 mil plastic" (field requests) on 2 pages: Requests, Route
- "1 case Blue tape + 4 mil plastic" (materials) on 2 pages: Requests, Route
- "40 ea 2x4x8 KD studs" (materials) on 2 pages: Requests, Route
- the same list twice (3 or more shared records, at least half of the shorter list): Requests and Route (4 shared, of 7 and 4: field requests, materials)

**Coordinator (Chen), desktop:** 4 records on two or more pages: field requests 2 (up to 2 pages); materials 2 (up to 2 pages).

- the same list twice (3 or more shared records, at least half of the shorter list): Requests and Route (4 shared, of 12 and 4: field requests, materials)

**Foreman (Angel), desktop:** 21 records on two or more pages: schedule lines 11 (up to 5 pages); vendors 3 (up to 4 pages); materials 2 (up to 3 pages); field requests 2 (up to 2 pages); site questions 1 (up to 2 pages); subs to confirm 1 (up to 2 pages); files 1 (up to 2 pages).

- "Restoration" (schedule lines) on 5 pages: Daily Log, Photos, Raise, Schedule, Site
- "Carlos Millwork" (vendors) on 4 pages: Daily Log, Documents, Drawings, Site
- "Rough electrical" (schedule lines) on 4 pages: Daily Log, Photos, Schedule, Site
- "Window Works" (vendors) on 4 pages: Documents, Drawings, Photos, Site
- "Demo & subfloor prep" (schedule lines) on 3 pages: Daily Log, Requests, Schedule
- "Windows & interior trim" (schedule lines) on 3 pages: Daily Log, Schedule, Site
- the same list twice (3 or more shared records, at least half of the shorter list): Daily Log and Schedule (8 shared, of 9 and 29: schedule lines)

**Crew (Alberto), desktop:** 8 records on two or more pages: schedule lines 3 (up to 2 pages); vendors 3 (up to 3 pages); materials 1 (up to 2 pages); files 1 (up to 2 pages).

- the same list twice (3 or more shared records, at least half of the shorter list): Requests and Schedule (3 shared, of 5 and 29: schedule lines)

**Driver (Alex), desktop:** 4 records on two or more pages: field requests 2 (up to 2 pages); materials 2 (up to 2 pages).

- the same list twice (3 or more shared records, at least half of the shorter list): Requests and Route (4 shared, of 7 and 4: field requests, materials)

**PM (Alan), phone:** 4 records on two or more pages: field requests 2 (up to 2 pages); materials 2 (up to 2 pages).

- "2x4x8 KD studs" (field requests) on 2 pages: Requests, Route
- "Blue tape + 4 mil plastic" (field requests) on 2 pages: Requests, Route
- "1 case Blue tape + 4 mil plastic" (materials) on 2 pages: Requests, Route
- "40 ea 2x4x8 KD studs" (materials) on 2 pages: Requests, Route
- the same list twice (3 or more shared records, at least half of the shorter list): Requests and Route (4 shared, of 7 and 4: field requests, materials)

**Foreman (Angel), phone:** 18 records on two or more pages: schedule lines 10 (up to 5 pages); vendors 2 (up to 4 pages); field requests 2 (up to 2 pages); site questions 1 (up to 2 pages); subs to confirm 1 (up to 2 pages); materials 1 (up to 2 pages); files 1 (up to 2 pages).

- "Restoration" (schedule lines) on 5 pages: Daily Log, Photos, Raise, Schedule, Site
- "Carlos Millwork" (vendors) on 4 pages: Daily Log, Documents, Drawings, Site
- "Rough electrical" (schedule lines) on 4 pages: Daily Log, Photos, Schedule, Site
- "Window Works" (vendors) on 4 pages: Documents, Drawings, Photos, Site
- "Demo & subfloor prep" (schedule lines) on 3 pages: Daily Log, Requests, Schedule
- "Windows & interior trim" (schedule lines) on 3 pages: Daily Log, Schedule, Site
- the same list twice (3 or more shared records, at least half of the shorter list): Daily Log and Schedule (8 shared, of 9 and 10: schedule lines); Schedule and Site (5 shared, of 10 and 23: schedule lines)

### The same records in other modules

For each role on the desktop: the pages of other modules (the Projects census's 121 State Street pages included) that list records this module lists, with how many.

- **Owner** (7 records here): Projects › Job Page 7; Purchasing › Buy Board 7; Today › Chief of Staff 4; Accounting › Dashboard 3; Projects › Schedule 3; Accounting › Reports 2; Purchasing › Quotes 1; Company and Settings › The Brain 1
- **PM (Alan)** (7 records here): Projects › Job Page 7; Purchasing › Buy Board 7; Accounting › Dashboard 3; Projects › Schedule 3; Accounting › Reports 2; Purchasing › Quotes 1; Projects › Decisions 1; Tasks and Messages › Tasks 1
- **Coordinator (Chen)** (12 records here): Projects › Job Page 12; Purchasing › Buy Board 8; Projects › Field 6; Projects › Schedule 6; Today › Chief of Staff 5; Company and Settings › The Brain 5; Accounting › Dashboard 5; Today › Today 4
- **Foreman (Angel)** (118 records here): Today › Today 16; Tasks and Messages › Messages 7
- **Crew (Alberto)** (102 records here): Time and Payroll › Clock 4
- **Driver (Alex)** (71 records here): Time and Payroll › Clock 2

Names (clients, vendors, leads, contacts, companies, partners) are left out here: a page that writes a name counts as listing it. A page that is the same page as one of this module's (one view under two menus) is left out too and listed next.

### The same page under two modules' menus

None found.

## 3. One Label, Different Numbers

The same label (a tile, a figure, a tab or section count) with numbers that share no value on two pages, for one role. Some are right about different scopes ("Open" against "All", one job against every job); the person still reads one word with two numbers. Each needs a person to judge.

Inside the module: none found.

Against other modules, Foreman (Angel), desktop: none found.

Against other modules, PM (Alan), desktop: none found.

## 4. Empty, Dead and Broken Screens

| Device | Role | Screen | What |
|---|---|---|---|
| desktop | Coordinator (Chen) | Requests | 1 save(s) while reading |

## 5. The Phone at 390

"Cut off" is text the phone ends early; "scrolls inside" is a strip of tiles or tabs the person swipes sideways inside the page (the page itself does not move). "Strip swipe" counts pages whose strip entry sits off screen until the strip is swiped. Pages taller than 3 phone screens are listed with their height.

| Role | Screens | The page scrolls sideways | Text cut off at the edge | Strips that scroll inside the page | Strip swipe | Pages taller than 3 screens |
|---|---|---|---|---|---|---|
| Owner | 2 | 0 | 0 | 0 | 0 | 0 |
| PM (Alan) | 2 | 0 | 0 | 0 | 2: Requests, Route | 0 |
| Coordinator (Chen) | 2 | 0 | 0 | 0 | 2: Requests, Route | 0 |
| Foreman (Angel) | 28 | 0 | 3: Documents, Drawings, Site | 2: Documents, Photos | 0 | 4: Site 3.5, Drawings 5.5, Schedule 3.1, Documents 4.7 |
| Crew (Alberto) | 12 | 0 | 2: Drawings, Photos | 1: Photos | 0 | 3: Schedule 3.6, Photos 4.7, Drawings 5.5 |
| Driver (Alex) | 10 | 0 | 1: Receipts | 1: Receipts | 0 | 1: Receipts 4.7 |

## 6. Page by Page, in Full

Every page the primary role reaches, as it opens, then each of its tabs. Heights are in screens of that device (900px desktop, 844px phone); "above the fold" is above the bottom bar on the phone.

### Foreman (Angel), desktop

- reached by: Daily Log (1 tap); first button "Weather"; shot [desktop](../../review/census/field/shots/desktop_foreman_daily_log.jpg)
- **Daily Log** (`flog`): heading "Daily Log", 1.4 screens tall, 3 sections (3 above the fold), 6 tab screens; blue: Next
  - lead: "The record of the day — weather, who worked, what went in, what went wrong. Sent at the end of the shift."
  - sections: Today — Thu, Sep 3; Weather; Earlier (1)
  - fields: e.g. 78
  - empty states: "No log filed"
  - tab groups: Weather / Crew / On Site / Work / Delays & Safety / Photos / Sign Off
  - tab **Crew**: heading "Daily Log", 3 sections
  - tab **On Site**: heading "Daily Log", 7 sections; 1 vendors
  - tab **Work**: heading "Daily Log", 3 sections; 8 schedule lines
  - tab **Delays & Safety**: heading "Daily Log", 6 sections; 2 schedule lines, 1 site questions
  - tab **Delays & Safety › Yes**: heading "Daily Log", 6 sections; 2 schedule lines, 1 site questions
  - tab **Photos**: heading "Daily Log", 3 sections
  - tabs that would not press (the row changed once one was pressed): Sign Off
- reached by: Site (1 tap); first button "Add a Sub Day"; shot [desktop](../../review/census/field/shots/desktop_foreman_site.jpg)
- **Site** (`fsite`): heading "Site", 3.3 screens tall, 4 sections (1 above the fold), 0 tab screens; blue: none
  - lead: "Who is on site, what is due to arrive, and what has to be signed off before the next trade."
  - sections: Subs — Next Two Weeks; Deliveries; Inspections; Punch List
  - records: 7 schedule lines, 4 materials, 4 inspections, 3 subs to confirm, 3 vendors, 2 purchase orders, 2 files, 1 obligations
- reached by: Requests (1 tap); first button "Open the Kit"; shot [desktop](../../review/census/field/shots/desktop_foreman_requests.jpg)
- **Requests** (`req`): heading "Requests", 0.8 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: Send the Request
  - lead: "Materials, tools, machinery, debris. Say it, pick a kit, or photograph a list — then send. Procurement and the driver are notified; status shows here."
  - sections: Requests on This Job (2)
  - records: 3 schedule lines, 2 field requests, 2 materials
  - fields: What do you need? e.g. 40 2x4x8, a box o
- reached by: Crew (1 tap); first button "Call"; shot [desktop](../../review/census/field/shots/desktop_foreman_crew.jpg)
- **Crew** (`fcrew`): heading "Crew", 1.3 screens tall, 4 sections (3 above the fold), 0 tab screens; blue: Approve 2 Clean
  - lead: "Who is on site right now, the week so far, hours to approve and the safety log."
  - sections: On Site Now; This Week; Hours to Approve; Safety
  - records: 1 schedule lines
- reached by: Drawings (1 tap); first button "Check the Sets"; shot [desktop](../../review/census/field/shots/desktop_foreman_drawings.jpg)
- **Drawings** (`plans`): heading "Drawings — 121 State Street", 2.8 screens tall, 3 sections (2 above the fold), 0 tab screens; blue: none
  - lead: "The job's drawing register: current sheets only unless you ask for the history. A superseded revision is VOID and opens stamped VOID."
  - sections: Set Check; WHAT THE SETS TEACH; Field Acknowledgments
  - figures: Found Before Work 0; Found in the Field 1; Days to Resolve 3.8; Open Conflicts 0
  - records: 2 vendors, 1 schedule lines, 1 subs to confirm, 1 files
  - columns: table: SHEET, TITLE, SET, REV, STATUS, DATE, ISSUED BY, WHAT CHANGED, FIELD (17 rows)
  - fields: Set All Sets Design Presentation LPC DOB, Status Current Sheets All Revisions For 
  - empty states: "No open conflicts between this job's sets."
- reached by: Schedule (1 tap); first button "Gantt"; shot [desktop](../../review/census/field/shots/desktop_foreman_schedule.jpg)
- **Schedule** (`sched`): heading "Schedule", 1.0 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: none
  - lead: "Site hours 07:30–16:30, Mon Tue Wed Thu Fri, 30 min lunch (8.5 h/day). Construction track — items in other tracks that gate these still show as dependencies."
  - records: 26 schedule lines, 3 materials, 1 vendors
  - columns: table: TASK, TRACK, OWNER, START, END, DAYS, STATUS, PATH (29 rows)
  - fields: Search…
  - tab groups: Gantt / List / Changes
  - tab **Gantt**: heading "Schedule", 0 sections; 26 schedule lines, 3 materials, 1 vendors
  - tab **Gantt › Wide**: heading "Schedule", 0 sections; 26 schedule lines, 3 materials, 1 vendors
  - tab **Gantt › Day**: heading "Schedule", 0 sections; 26 schedule lines, 3 materials, 1 vendors
  - tab **Changes**: heading "Schedule", 1 sections
- reached by: Photos (1 tap); first button "All"; shot [desktop](../../review/census/field/shots/desktop_foreman_photos.jpg)
- **Photos** (`photos`): heading "Photos", 1.5 screens tall, 0 sections (0 above the fold), 6 tab screens; blue: Add Photos
  - lead: "121 State Street — every photo from the site in one stream: daily logs, progress updates, hidden conditions, drawing questions, deliveries and receipts."
  - records: 2 schedule lines, 1 files, 1 vendors, 1 purchase orders
  - fields: Any Date, Any Task, Any Area, Any Trade
  - tab groups: All / Hidden Condition / Daily Log / Progress / Drawing Question / Receipt / Delivery
  - tab **Hidden Condition**: heading "Photos", 0 sections
  - tab **Daily Log**: heading "Photos", 0 sections; 2 schedule lines
  - tab **Progress**: heading "Photos", 0 sections
  - tab **Drawing Question**: heading "Photos", 0 sections
  - tab **Receipt**: heading "Photos", 0 sections
  - tab **Delivery**: heading "Photos", 0 sections; 1 files, 1 vendors, 1 purchase orders
- reached by: Documents (1 tap); first button "Added This Week 8 0 from the field"; shot [desktop](../../review/census/field/shots/desktop_foreman_documents.jpg)
- **Documents** (`files`): heading "Documents", 1.9 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: Upload Files
  - lead: "Photos, delivery tickets, inspection cards, receipts, drawings and permits — uploaded from the field or the office, kept with the project, and linked to what th"
  - figures: Added This Week 8; Unfiled 4; Drawings 24; Cards & Permits 0
  - records: 33 files, 24 drawing sheets, 5 submittals, 4 vendors, 2 bills
  - tab groups: All / Photos / Delivery Tickets / Receipts / Inspections & Permits / Drawings & Plans / Other; Grid / List
  - tab **Photos**: heading "Documents", 0 sections
  - tab **Delivery Tickets**: heading "Documents", 0 sections
  - tab **Receipts**: heading "Documents", 0 sections; 4 files, 4 vendors, 2 bills
  - tab **Inspections & Permits**: heading "Documents", 0 sections
  - tab **Drawings & Plans**: heading "Documents", 0 sections; 25 files, 24 drawing sheets, 2 vendors
  - tab **Other**: heading "Documents", 0 sections
  - tab **List**: heading "Documents", 0 sections; 33 files, 24 drawing sheets, 5 submittals, 4 vendors
- reached by: Raise (1 tap); first button "Materials or a Tool Studs, screws, a saw"; shot [desktop](../../review/census/field/shots/desktop_foreman_raise.jpg)
- **Raise** (`fraise`): heading "Raise", 1.1 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
  - lead: "Send something to the office: material, a tool, a dump run, a problem or a question. It reaches them with the job on it."
  - records: 3 site questions, 2 field requests, 1 schedule lines, 1 materials

### Foreman (Angel), phone

- reached by: bar: Daily Log (1 tap); first button "Weather"; shot [phone](../../review/census/field/shots/phone_foreman_daily_log.jpg)
- **Daily Log** (`flog`): heading "Daily Log", 2.1 screens tall, 3 sections (3 above the fold), 6 tab screens; blue: Next
  - lead: "The record of the day — weather, who worked, what went in, what went wrong. Sent at the end of the shift."
  - sections: Today — Thu, Sep 3; Weather; Earlier (1)
  - fields: e.g. 78
  - empty states: "No log filed"
  - tab groups: Weather / Crew / On Site / Work / Delays & Safety / Photos / Sign Off
  - tab **Crew**: heading "Daily Log", 3 sections
  - tab **On Site**: heading "Daily Log", 7 sections; 1 vendors
  - tab **Work**: heading "Daily Log", 3 sections; 8 schedule lines
  - tab **Delays & Safety**: heading "Daily Log", 6 sections; 2 schedule lines, 1 site questions
  - tab **Delays & Safety › Yes**: heading "Daily Log", 6 sections; 2 schedule lines, 1 site questions
  - tab **Photos**: heading "Daily Log", 3 sections
  - tabs that would not press (the row changed once one was pressed): Sign Off
- reached by: bar: Site (1 tap); first button "Add a Sub Day"; shot [phone](../../review/census/field/shots/phone_foreman_site.jpg)
- **Site** (`fsite`): heading "Site", 3.5 screens tall, 4 sections (1 above the fold), 0 tab screens; blue: none; runs past the edge: cut off by pr-m (DOB · call by Wed, Sep 2 · gates Rough p, DOB · scheduled Tue, Sep 8 · gates Rough)
  - lead: "Who is on site, what is due to arrive, and what has to be signed off before the next trade."
  - sections: Subs — Next Two Weeks; Deliveries; Inspections; Punch List
  - records: 7 schedule lines, 4 materials, 4 inspections, 3 subs to confirm, 3 vendors, 2 purchase orders, 2 files, 1 obligations
- reached by: bar: Requests (1 tap); first button "Open the Kit"; shot [phone](../../review/census/field/shots/phone_foreman_requests.jpg)
- **Requests** (`req`): heading "Requests", 1.1 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: Send the Request
  - lead: "Materials, tools, machinery, debris. Say it, pick a kit, or photograph a list — then send. Procurement and the driver are notified; status shows here."
  - sections: Requests on This Job (2)
  - records: 3 schedule lines, 2 field requests, 2 materials
  - fields: What do you need? e.g. 40 2x4x8, a box o
- reached by: menu › Crew (2 taps); first button "Clock the Crew"; shot [phone](../../review/census/field/shots/phone_foreman_crew.jpg)
- **Crew** (`fcrew`): heading "Crew", 2.0 screens tall, 4 sections (2 above the fold), 0 tab screens; blue: Clock the Crew
  - lead: "Who is on site right now, the week so far, hours to approve and the safety log."
  - sections: On Site Now; This Week; Hours to Approve; Safety
  - records: 1 schedule lines
- reached by: menu › Drawings (2 taps); first button "Check the Sets"; shot [phone](../../review/census/field/shots/phone_foreman_drawings.jpg)
- **Drawings** (`plans`): heading "Drawings — 121 State Street", 5.5 screens tall, 3 sections (2 above the fold), 0 tab screens; blue: none; runs past the edge: cut off by pr-m (Structural Consultant · 9/1 · Maya Natar)
  - lead: "The job's drawing register: current sheets only unless you ask for the history. A superseded revision is VOID and opens stamped VOID."
  - sections: Set Check; WHAT THE SETS TEACH; Field Acknowledgments
  - figures: Found Before Work 0; Found in the Field 1; Days to Resolve 3.8; Open Conflicts 0
  - records: 2 vendors, 1 schedule lines, 1 subs to confirm, 1 files
  - fields: Set All Sets Design Presentation LPC DOB, Status Current Sheets All Revisions For 
  - empty states: "No open conflicts between this job's sets."
- reached by: menu › Schedule (2 taps); first button "Show the Whole Schedule"; shot [phone](../../review/census/field/shots/phone_foreman_schedule.jpg)
- **Schedule** (`sched`): heading "Schedule", 3.1 screens tall, 14 sections (4 above the fold), 0 tab screens; blue: none
  - lead: "What is on the schedule with your name, day by day. Site hours 07:30–16:30."
  - sections: Today · Thu, Sep 3 (3); Also on site that day; Fri, Sep 4 (3); Also on site that day; Mon, Sep 7 (3); Also on site that day; Tue, Sep 8 (3); Also on site that day; Wed, Sep 9 (3); Also on site that day; Thu, Sep 10 (3); Also on site that day; Fri, Sep 11 (3); Also on site that day
  - records: 10 schedule lines
- reached by: menu › Photos (2 taps); first button "All"; shot [phone](../../review/census/field/shots/phone_foreman_photos.jpg)
- **Photos** (`photos`): heading "Photos", 2.3 screens tall, 0 sections (0 above the fold), 6 tab screens; blue: Add Photos
  - lead: "121 State Street — every photo from the site in one stream: daily logs, progress updates, hidden conditions, drawing questions, deliveries and receipts."
  - records: 2 schedule lines, 1 files, 1 vendors, 1 purchase orders
  - fields: Any Date, Any Task, Any Area, Any Trade
  - tab groups: All / Hidden Condition / Daily Log / Progress / Drawing Question / Receipt / Delivery
  - tab **Hidden Condition**: heading "Photos", 0 sections
  - tab **Daily Log**: heading "Photos", 0 sections; 2 schedule lines
  - tab **Progress**: heading "Photos", 0 sections
  - tab **Drawing Question**: heading "Photos", 0 sections
  - tab **Receipt**: heading "Photos", 0 sections
  - tab **Delivery**: heading "Photos", 0 sections; 1 files, 1 vendors, 1 purchase orders
- reached by: menu › Documents (2 taps); first button "Added This Week 8"; shot [phone](../../review/census/field/shots/phone_foreman_documents.jpg)
- **Documents** (`files`): heading "Documents", 4.7 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: none
  - lead: "Photos, delivery tickets, inspection cards, receipts, drawings and permits — uploaded from the field or the office, kept with the project, and linked to what th"
  - figures: Added This Week 8; Unfiled 4; Drawings 24; Cards & Permits 0
  - records: 33 files, 24 drawing sheets, 5 submittals, 4 vendors, 2 bills
  - tab groups: All / Photos / Delivery Tickets / Receipts / Inspections & Permits / Drawings & Plans / Other; Grid / List
  - tab **Photos**: heading "Documents", 0 sections
  - tab **Delivery Tickets**: heading "Documents", 0 sections
  - tab **Receipts**: heading "Documents", 0 sections; 4 files, 4 vendors, 2 bills
  - tab **Inspections & Permits**: heading "Documents", 0 sections
  - tab **Drawings & Plans**: heading "Documents", 0 sections; 25 files, 24 drawing sheets, 2 vendors
  - tab **Other**: heading "Documents", 0 sections
  - tab **List**: heading "Documents", 0 sections; 33 files, 24 drawing sheets, 4 submittals, 4 vendors (runs past the edge: cut off by pr-m (Submittal · 26 51 00-001 Lighting fixtur, Drawing / plan / sketch · 9/1 · Maya Nat))
- reached by: menu › Raise (2 taps); first button "Materials or a Tool Studs, screws, a saw"; shot [phone](../../review/census/field/shots/phone_foreman_raise.jpg)
- **Raise** (`fraise`): heading "Raise", 1.5 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
  - lead: "Send something to the office: material, a tool, a dump run, a problem or a question. It reaches them with the job on it."
  - records: 3 site questions, 2 field requests, 1 schedule lines, 1 materials

### PM (Alan), desktop

- reached by: More › Requests (2 taps); first button "Open the Kit"; shot [desktop](../../review/census/field/shots/desktop_pm_requests.jpg)
- **Requests** (`req`): heading "Requests", 0.9 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: Send the Request
  - lead: "Materials, tools, machinery, debris. Say it, pick a kit, or photograph a list — then send. Procurement and the driver are notified; status shows here."
  - sections: Requests on This Job (2)
  - records: 3 schedule lines, 2 field requests, 2 materials
  - fields: Job, What do you need? e.g. 40 2x4x8, a box o
- reached by: More › Route (2 taps); first button "Count This"; shot [desktop](../../review/census/field/shots/desktop_pm_route.jpg)
- **Route** (`route`): heading "Route", 1.3 screens tall, 6 sections (3 above the fold), 0 tab screens; blue: Approve Route
  - lead: "Everything to pick up, buy, drop off and dump — planned into a day."
  - sections: Picks from Stock (0); Store Run (2); Suggested Day Plan (3); Preview the shopping list (2); 121 State Street; Office Pickups
  - records: 2 field requests, 2 materials, 1 vendors
  - fields: Store, Run Length
  - empty states: "Nothing reserved from stock right now."; "No price on file for these: the store already on the way"; "Nothing at the office is wanted on site in the next 10 days."

### PM (Alan), phone

- reached by: menu › More › swipe the strip, Requests (3 taps); first button "Open the Kit"; shot [phone](../../review/census/field/shots/phone_pm_requests.jpg)
- **Requests** (`req`): heading "Requests", 1.2 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: Send the Request
  - lead: "Materials, tools, machinery, debris. Say it, pick a kit, or photograph a list — then send. Procurement and the driver are notified; status shows here."
  - sections: Requests on This Job (2)
  - records: 3 schedule lines, 2 field requests, 2 materials
  - fields: Job, What do you need? e.g. 40 2x4x8, a box o
- reached by: menu › More › swipe the strip, Route (3 taps); first button "Count This"; shot [phone](../../review/census/field/shots/phone_pm_route.jpg)
- **Route** (`route`): heading "Route", 2.5 screens tall, 6 sections (3 above the fold), 0 tab screens; blue: Approve Route
  - lead: "Everything to pick up, buy, drop off and dump — planned into a day."
  - sections: Picks from Stock (0); Store Run (2); Suggested Day Plan (3); Preview the shopping list (2); 121 State Street; Office Pickups
  - records: 2 field requests, 2 materials, 1 vendors
  - fields: Store, Run Length
  - empty states: "Nothing reserved from stock right now."; "No price on file for these: the store already on the way"; "Nothing at the office is wanted on site in the next 10 days."

## 7. The Other Roles, One Line a Page

### Owner, desktop

- reached by: More (1 tap); shot [desktop](../../review/census/field/shots/desktop_owner_requests.jpg)
- **Requests** (`req`): heading "Requests", 1.1 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: Send the Request
- reached by: More › Route (2 taps); shot [desktop](../../review/census/field/shots/desktop_owner_route.jpg)
- **Route** (`route`): heading "Route", 1.3 screens tall, 6 sections (3 above the fold), 0 tab screens; blue: Approve Route

### Owner, phone

- reached by: menu › More (2 taps); shot [phone](../../review/census/field/shots/phone_owner_requests.jpg)
- **Requests** (`req`): heading "Requests", 1.7 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: Send the Request
- reached by: menu › More › Route (3 taps); shot [phone](../../review/census/field/shots/phone_owner_route.jpg)
- **Route** (`route`): heading "Route", 2.5 screens tall, 6 sections (3 above the fold), 0 tab screens; blue: Approve Route

### Coordinator (Chen), desktop

- reached by: More › Requests (2 taps); shot [desktop](../../review/census/field/shots/desktop_coord_requests.jpg)
- **Requests** (`req`): heading "Requests", 1.5 screens tall, 3 sections (2 above the fold), 0 tab screens; blue: Send the Request; 1 save(s) while reading
- reached by: More › Route (2 taps); shot [desktop](../../review/census/field/shots/desktop_coord_route.jpg)
- **Route** (`route`): heading "Route", 1.3 screens tall, 6 sections (3 above the fold), 0 tab screens; blue: Approve Route

### Coordinator (Chen), phone

- reached by: menu › More › swipe the strip, Requests (3 taps); shot [phone](../../review/census/field/shots/phone_coord_requests.jpg)
- **Requests** (`req`): heading "Requests", 2.2 screens tall, 3 sections (2 above the fold), 0 tab screens; blue: Send the Request
- reached by: menu › More › swipe the strip, Route (3 taps); shot [phone](../../review/census/field/shots/phone_coord_route.jpg)
- **Route** (`route`): heading "Route", 2.5 screens tall, 6 sections (3 above the fold), 0 tab screens; blue: Approve Route

### Crew (Alberto), desktop

- reached by: Requests (1 tap); shot [desktop](../../review/census/field/shots/desktop_crew_requests.jpg)
- **Requests** (`req`): heading "Requests", 0.7 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: Send the Request
- reached by: Schedule (1 tap); shot [desktop](../../review/census/field/shots/desktop_crew_schedule.jpg)
- **Schedule** (`sched`): heading "Schedule", 1.0 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: none
- reached by: Photos (1 tap); shot [desktop](../../review/census/field/shots/desktop_crew_photos.jpg)
- **Photos** (`files`): heading "Photos", 1.9 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: Upload Files
- reached by: Deliveries (1 tap); shot [desktop](../../review/census/field/shots/desktop_crew_deliveries.jpg)
- **Deliveries** (`recv`): heading "Deliveries", 0.5 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: Received
- reached by: Drawings (1 tap); shot [desktop](../../review/census/field/shots/desktop_crew_drawings.jpg)
- **Drawings** (`plans`): heading "Drawings — 121 State Street", 2.8 screens tall, 3 sections (2 above the fold), 0 tab screens; blue: none

### Crew (Alberto), phone

- reached by: bar: Requests (1 tap); shot [phone](../../review/census/field/shots/phone_crew_requests.jpg)
- **Requests** (`req`): heading "Requests", 1.0 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: Send the Request
- reached by: bar: Schedule (1 tap); shot [phone](../../review/census/field/shots/phone_crew_schedule.jpg)
- **Schedule** (`sched`): heading "Schedule", 3.6 screens tall, 14 sections (3 above the fold), 0 tab screens; blue: none
- reached by: menu › Photos (2 taps); shot [phone](../../review/census/field/shots/phone_crew_photos.jpg)
- **Photos** (`files`): heading "Photos", 4.7 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: Take a Photo
- reached by: menu › Deliveries (2 taps); shot [phone](../../review/census/field/shots/phone_crew_deliveries.jpg)
- **Deliveries** (`recv`): heading "Deliveries", 0.5 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- reached by: menu › Drawings (2 taps); shot [phone](../../review/census/field/shots/phone_crew_drawings.jpg)
- **Drawings** (`plans`): heading "Drawings — 121 State Street", 5.5 screens tall, 3 sections (2 above the fold), 0 tab screens; blue: none; runs past the edge: cut off by pr-m (Structural Consultant · 9/1 · Maya Natar)

### Driver (Alex), desktop

- reached by: Route (1 tap); shot [desktop](../../review/census/field/shots/desktop_driver_route.jpg)
- **Route** (`route`): heading "Route", 1.4 screens tall, 7 sections (4 above the fold), 0 tab screens; blue: I'm at the Store
- reached by: Receipts (1 tap); shot [desktop](../../review/census/field/shots/desktop_driver_receipts.jpg)
- **Receipts** (`files`): heading "Receipts", 1.9 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: Upload Files
- reached by: Requests (1 tap); shot [desktop](../../review/census/field/shots/desktop_driver_requests.jpg)
- **Requests** (`req`): heading "Requests", 0.8 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: Send the Request

### Driver (Alex), phone

- reached by: bar: Route (1 tap); shot [phone](../../review/census/field/shots/phone_driver_route.jpg)
- **Route** (`route`): heading "Route", 2.6 screens tall, 7 sections (3 above the fold), 0 tab screens; blue: Clock In
- reached by: bar: Receipts (1 tap); shot [phone](../../review/census/field/shots/phone_driver_receipts.jpg)
- **Receipts** (`files`): heading "Receipts", 4.7 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: Snap a Receipt
- reached by: menu › Requests (2 taps); shot [phone](../../review/census/field/shots/phone_driver_requests.jpg)
- **Requests** (`req`): heading "Requests", 1.1 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: Send the Request

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

