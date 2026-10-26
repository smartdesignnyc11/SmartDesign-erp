# The Sales and Clients Module, Page by Page: the Census

**Asked by Alan, 2026-10-26:** "Go through all the modules with screenshots. It's important to understand the format of every page and what's on it." The loop's experts and the client expert walk every page of their module with this in hand in round one of the improvement loop (docs/IMPROVEMENT_LOOP.md).

**What this is.** A machine inventory, not a judgment, in the format of the Projects census (`docs/modules/projects_census.md`). No app code changed. `tests/module_census.py` (its helpers `tests/module_census_js.js` sit on the projects census's reader `tests/census_js.js` and the information map's `tests/ia_js.js`) signs in as each role on a fresh app at 1440 and at 390, reads the role's running menu, and reaches each page of this module the way the person does: the phone bar, or the menu (the hamburger on the phone), the group, then the strip. It presses every tab of every tab group and the tabs those reveal, follows the page's own links to this module's pages the menu did not reach, reads every screen and shoots it. The primary role is the owner; every role whose menu holds a page of this module is walked. Job-scoped pages show **121 State Street** wherever the role may open it.

**Where this module's pages sit.** Estimates as the owner sees them is the Billing page on its Estimates tab (Sales › Estimates); the Billing census walks the same page from the Billing menu.

**Build bd3180c27e33** (master 1cc2eb9), the one build every module census of this round ran on. 258 screens in all. Walked 2026-10-26 06:29 on the demo day (Thu 2026-09-03); the walk of every module took 54.4 minutes. Raw read: `review/census/sales/data.json`. Every screen per role in tables: `review/census/sales/tables.md`. Screenshots of every screen, both devices: `review/census/sales/shots/` (`desktop_` or `phone_`, the role, the page, then the tab; up to 3 desktop or 5 phone screens tall). The first screen of each page is committed; the tabs stay on the machine that ran it.

Run it: `python3 build.py && cd tests && ./slot.sh python3 module_census.py --module sales` (then `python3 module_census.py --report` rewrites every module's page from data.json).

## Headline

- **Owner: 11 pages with 30 more screens behind their tabs on the desktop (11 pages and 31 tab screens on the phone)**, about 10 desktop screens end to end.
- **Pages each role reaches in this module, desktop:** Owner 11, PM 10, Coordinator 9, Designer 1, Billing 9, Controller 1.
- **Reached only one way** by Owner: Partners (desktop and phone), Playbook (desktop and phone), Sales (desktop) (one menu entry, not on the phone bar, and no walked page links to it; section 1).
- **The same page under another module's menu** (Owner, desktop): Estimates is also Billing › Billing, Projects › Change Orders, Projects › Estimates (`billing`).
- **42 records show on two or more of this module's pages** for Owner on the desktop (19 contacts, 9 leads, 6 companies, 5 clients). "Daniel Okafor" is on 5: Clients, Companies, People, Sales, Sales (by the link Leads 1 inquiries to qualify).
- **The same records in other modules** (Owner, desktop): Accounting › Reports lists 20; Tasks and Messages › Tasks lists 8; Projects › Job Page lists 8; Today › Chief of Staff lists 8; Company and Settings › Company Settings lists 8 of the 27 records this module lists.
- **One label, different numbers against other modules:** "ready bill" $46K on Billing › Billing against $12,651 on Projects › Job Page; "past due" $0 on Sales and Clients › Clients against 3 on Projects › Decisions (2 in all, section 3).
- **On the phone** (Owner): 1 of the 11 pages are taller than three screens (Playbook); 8 have no section heading above the fold; 1 are reached through a strip entry that sits off screen until the strip is swiped (Playbook); 0 screens scroll sideways.
- **Nothing crashed and no page raised an error**; every page opened.
- **1 screen(s) saved while the census only read and pressed tabs** (Coordinator (Chen) phone, Forecast). Each role ran on a fresh app, so a save never reached the next role.

## 1. The Tree, Role by Role

**Pages** are the module's pages the role reaches from its menu (and the links those pages show). **Tabs** are the screens behind each page's tab groups, and behind the tabs those reveal. **Sections** are the headed parts of each page as it opens. Each cell reads desktop / phone.

| Role | Primary | First page of the module, reached by (desktop / phone) | Pages | Tab screens | Sections | Screens |
|---|---|---|---|---|---|---|
| Owner | yes | Sales (1 tap) / bar: Sales (1 tap) | 11 / 11 | 30 / 31 | 13 / 13 | 41 / 42 |
| PM (Alan) |  | Clients (1 tap) / bar: Clients (1 tap) | 10 / 10 | 23 / 24 | 13 / 13 | 33 / 34 |
| Coordinator (Chen) |  | More › Forecast (2 taps) / menu › More › Forecast (3 taps) | 9 / 9 | 17 / 17 | 12 / 12 | 26 / 26 |
| Designer (Sarah) |  | Clients (1 tap) / menu › Clients (2 taps) | 1 / 1 | 0 / 0 | 0 / 0 | 1 / 1 |
| Billing |  | Clients (1 tap) / bar: Clients (1 tap) | 9 / 9 | 17 / 17 | 12 / 12 | 26 / 26 |
| Controller |  | More › Clients (2 taps) / menu › More › swipe the strip, Clients (3 taps) | 1 / 1 | 0 / 0 | 0 / 0 | 1 / 1 |

### Which pages each role reaches (desktop)

Each cell is the number of screens the page has (the page and its tabs); "-" means the role does not reach it.

| Page | Owner | PM | Coordinator | Designer | Billing | Controller |
|---|---|---|---|---|---|---|
| Sales | 2 | 2 | 2 | - | 2 | - |
| Estimates | 8 | - | - | - | - | - |
| Numbers | 7 | 7 | - | - | - | - |
| Partners | 1 | 1 | 1 | - | 1 | - |
| Playbook | 1 | 1 | 1 | - | 1 | - |
| Clients | 3 | 3 | 3 | 1 | 3 | 1 |
| Sales (by the link Leads 1 inquiries to qualify) | 2 | 2 | 2 | - | 2 | - |
| Numbers — Forecast | 4 | 4 | - | - | - | - |
| Numbers — Dashboard | 3 | 3 | - | - | - | - |
| People | 5 | 5 | 5 | - | 5 | - |
| Companies | 5 | 5 | 5 | - | 5 | - |
| Forecast | - | - | 4 | - | 4 | - |
| Sales Dashboard | - | - | 3 | - | 3 | - |

### Owner's tree at a glance

Reached by is the taps from the role's first page, desktop then phone. Tall is in screens, desktop / phone. Sections are the headed parts as the page opens (phone above the fold). Tabs are the screens behind its tab groups, desktop / phone. "What it lists" counts the records found on the page as it opens.

| Page | Reached by (desktop / phone) | Heading | Tall | Sections (phone above the fold) | Tabs | Tiles and figures | What it lists | Blue button | First button | Shots |
|---|---|---|---|---|---|---|---|---|---|---|
| Sales | Sales (1 tap) / bar: Sales (1 tap) | Sales | 0.7 / 1.1 | 0 (0) | 1 / 1 | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | 6 leads, 6 contacts, 1 to-dos, 1 clients | New Lead | New Opportunity | [desktop](../../review/census/sales/shots/desktop_owner_sales.jpg) [phone](../../review/census/sales/shots/phone_owner_sales.jpg) |
| Estimates | Sales › Estimates (2 taps) / menu › Sales › Estimates (3 taps) | Estimates | 0.6 / 0.9 | 0 (0) | 7 / 7 | - | 4 estimates, 3 clients | New Estimate | Billing Queue | [desktop](../../review/census/sales/shots/desktop_owner_estimates.jpg) [phone](../../review/census/sales/shots/phone_owner_estimates.jpg) |
| Numbers | Sales › Numbers (2 taps) / menu › Sales › Numbers (3 taps) | Numbers | 0.7 / 1.1 | 1 (1) | 6 / 7 | First Reply 3 h; No Next Step 3; Proposals Aging 0; Won This Quarter $210K | - | none | Numbers | [desktop](../../review/census/sales/shots/desktop_owner_numbers.jpg) [phone](../../review/census/sales/shots/phone_owner_numbers.jpg) |
| Partners | Sales › Partners (2 taps) / menu › Sales › Partners (3 taps) | Partners | 0.6 / 0.7 | 0 (0) | 0 / 0 | Thank-Yous Owed 1; Due a Touch 1; Leads This Quarter 3; Won Through Partners $210K | 3 contacts, 3 companies, 3 partners | New Partner | Thank-Yous Owed 1 David sent | [desktop](../../review/census/sales/shots/desktop_owner_partners.jpg) [phone](../../review/census/sales/shots/phone_owner_partners.jpg) |
| Playbook | Sales › Playbook (2 taps) / menu › Sales › swipe the strip, Playbook (3 taps) | Playbook | 2.2 / 4.4 | 5 (1) | 0 / 0 | - | - | none | none | [desktop](../../review/census/sales/shots/desktop_owner_playbook.jpg) [phone](../../review/census/sales/shots/phone_owner_playbook.jpg) |
| Clients | Clients (1 tap) / menu › Clients (2 taps) | Clients | 0.7 / 0.9 | 0 (0) | 2 / 2 | Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1 | 5 clients, 5 contacts, 2 leads | New Client | Clients | [desktop](../../review/census/sales/shots/desktop_owner_clients.jpg) [phone](../../review/census/sales/shots/phone_owner_clients.jpg) |
| Sales (by the link Leads 1 inquiries to qualify) | Sales › link: Leads 1 inquiries to qualify · every one / - | Sales | 0.5 / - | 0 (-) | 1 / 0 | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | 1 leads, 1 contacts | New Lead | New Opportunity | [desktop](../../review/census/sales/shots/desktop_owner_leads_1_inquiries_to_qualify_every_one.jpg) |
| Numbers — Forecast | Numbers › link: Forecast / Numbers › link: Forecast | Numbers — Forecast | 0.9 / 1.4 | 0 (0) | 3 / 3 | - | - | none | Numbers | [desktop](../../review/census/sales/shots/desktop_owner_forecast.jpg) [phone](../../review/census/sales/shots/phone_owner_forecast.jpg) |
| Numbers — Dashboard | Numbers › link: Sales Dashboard / Numbers › link: Sales Dashboard | Numbers — Dashboard | 0.8 / 2.0 | 7 (2) | 2 / 2 | - | - | none | Numbers | [desktop](../../review/census/sales/shots/desktop_owner_sales_dashboard.jpg) [phone](../../review/census/sales/shots/phone_owner_sales_dashboard.jpg) |
| People | Clients › link: People / Clients › link: People | People | 1.4 / 2.0 | 0 (0) | 4 / 4 | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | 19 contacts, 8 leads, 3 companies, 3 partners | New Person | Clients | [desktop](../../review/census/sales/shots/desktop_owner_people.jpg) [phone](../../review/census/sales/shots/phone_owner_people.jpg) |
| Companies | Clients › link: Companies / Clients › link: Companies | Companies | 0.6 / 0.9 | 0 (0) | 4 / 4 | - | 6 companies | New Company | Clients | [desktop](../../review/census/sales/shots/desktop_owner_companies.jpg) [phone](../../review/census/sales/shots/phone_owner_companies.jpg) |

### How each page is reached, and the pages reached only one way

Menu places are the role's menu entries that open the page (a page in two groups has two). The phone bar counts as one more way in on the phone (its pages are in the menu too). Links are the walked pages, in any module, that show a link to it. **One way** means one menu place and nothing else: lose that entry and the page is lost.

| Role | Device | Page | Menu places | Phone bar | Linked from | Ways in |
|---|---|---|---|---|---|---|
| Owner | desktop | Sales | Sales | - | - | 1 (one way) |
| Owner | desktop | Estimates | Projects › Estimates; Sales › Estimates | - | Company and Settings › The Brain, Today › Chief of Staff | 4 |
| Owner | desktop | Numbers | Sales › Numbers | - | Sales and Clients › Numbers, Sales and Clients › Numbers — Dashboard, Sales and Clients › Numbers — Forecast | 4 |
| Owner | desktop | Partners | Sales › Partners | - | - | 1 (one way) |
| Owner | desktop | Playbook | Sales › Playbook | - | - | 1 (one way) |
| Owner | desktop | Clients | Clients | - | Company and Settings › Your Own Data, Sales and Clients › Clients, Sales and Clients › Companies, Sales and Clients › People | 5 |
| Owner | desktop | Sales (by the link Leads 1 inquiries to qualify) | none (reached by a link) | - | - | 0 |
| Owner | desktop | Numbers — Forecast | none (reached by a link) | - | Sales and Clients › Numbers, Sales and Clients › Numbers — Dashboard, Sales and Clients › Numbers — Forecast | 3 |
| Owner | desktop | Numbers — Dashboard | none (reached by a link) | - | Sales and Clients › Numbers, Sales and Clients › Numbers — Dashboard, Sales and Clients › Numbers — Forecast | 3 |
| Owner | desktop | People | none (reached by a link) | - | Sales and Clients › Clients, Sales and Clients › Companies, Sales and Clients › People | 3 |
| Owner | desktop | Companies | none (reached by a link) | - | Sales and Clients › Clients, Sales and Clients › Companies, Sales and Clients › People | 3 |
| Owner | phone | Sales | Sales | yes | - | 2 |
| Owner | phone | Estimates | Projects › Estimates; Sales › Estimates | - | - | 2 |
| Owner | phone | Numbers | Sales › Numbers | - | Sales and Clients › Numbers, Sales and Clients › Numbers — Dashboard, Sales and Clients › Numbers — Forecast | 4 |
| Owner | phone | Partners | Sales › Partners | - | - | 1 (one way) |
| Owner | phone | Playbook | Sales › Playbook | - | - | 1 (one way) |
| Owner | phone | Clients | Clients | - | Company and Settings › Your Own Data, Sales and Clients › Clients, Sales and Clients › Companies, Sales and Clients › People | 5 |
| Owner | phone | Sales (by the link Leads 1) | none (reached by a link) | - | - | 0 |
| Owner | phone | Numbers — Forecast | none (reached by a link) | - | Sales and Clients › Numbers, Sales and Clients › Numbers — Dashboard, Sales and Clients › Numbers — Forecast | 3 |
| Owner | phone | Numbers — Dashboard | none (reached by a link) | - | Sales and Clients › Numbers, Sales and Clients › Numbers — Dashboard, Sales and Clients › Numbers — Forecast | 3 |
| Owner | phone | People | none (reached by a link) | - | Sales and Clients › Clients, Sales and Clients › Companies, Sales and Clients › People | 3 |
| Owner | phone | Companies | none (reached by a link) | - | Sales and Clients › Clients, Sales and Clients › Companies, Sales and Clients › People | 3 |
| PM (Alan) | desktop | Clients | Clients | - | Sales and Clients › Clients, Sales and Clients › Companies, Sales and Clients › People | 4 |
| PM (Alan) | desktop | Sales | More › Sales | - | - | 1 (one way) |
| PM (Alan) | desktop | Partners | More › Partners | - | - | 1 (one way) |
| PM (Alan) | desktop | Playbook | More › Playbook | - | - | 1 (one way) |
| PM (Alan) | desktop | Numbers | More › Numbers | - | Sales and Clients › Numbers, Sales and Clients › Numbers — Dashboard, Sales and Clients › Numbers — Forecast | 4 |
| PM (Alan) | desktop | People | none (reached by a link) | - | Sales and Clients › Clients, Sales and Clients › Companies, Sales and Clients › People | 3 |
| PM (Alan) | desktop | Companies | none (reached by a link) | - | Sales and Clients › Clients, Sales and Clients › Companies, Sales and Clients › People | 3 |
| PM (Alan) | desktop | Sales (by the link Leads 1 inquiries to qualify) | none (reached by a link) | - | - | 0 |
| PM (Alan) | desktop | Numbers — Forecast | none (reached by a link) | - | Sales and Clients › Numbers, Sales and Clients › Numbers — Dashboard, Sales and Clients › Numbers — Forecast | 3 |
| PM (Alan) | desktop | Numbers — Dashboard | none (reached by a link) | - | Sales and Clients › Numbers, Sales and Clients › Numbers — Dashboard, Sales and Clients › Numbers — Forecast | 3 |
| PM (Alan) | phone | Clients | Clients | yes | Sales and Clients › Clients, Sales and Clients › Companies, Sales and Clients › People | 5 |
| PM (Alan) | phone | Sales | More › Sales | - | - | 1 (one way) |
| PM (Alan) | phone | Partners | More › Partners | - | - | 1 (one way) |
| PM (Alan) | phone | Playbook | More › Playbook | - | - | 1 (one way) |
| PM (Alan) | phone | Numbers | More › Numbers | - | Sales and Clients › Numbers, Sales and Clients › Numbers — Dashboard, Sales and Clients › Numbers — Forecast | 4 |
| PM (Alan) | phone | People | none (reached by a link) | - | Sales and Clients › Clients, Sales and Clients › Companies, Sales and Clients › People | 3 |
| PM (Alan) | phone | Companies | none (reached by a link) | - | Sales and Clients › Clients, Sales and Clients › Companies, Sales and Clients › People | 3 |
| PM (Alan) | phone | Sales (by the link Leads 1) | none (reached by a link) | - | - | 0 |
| PM (Alan) | phone | Numbers — Forecast | none (reached by a link) | - | Sales and Clients › Numbers, Sales and Clients › Numbers — Dashboard, Sales and Clients › Numbers — Forecast | 3 |
| PM (Alan) | phone | Numbers — Dashboard | none (reached by a link) | - | Sales and Clients › Numbers, Sales and Clients › Numbers — Dashboard, Sales and Clients › Numbers — Forecast | 3 |
| Coordinator (Chen) | desktop | Forecast | More › Forecast | - | Sales and Clients › Forecast, Sales and Clients › Sales Dashboard | 3 |
| Coordinator (Chen) | desktop | Sales Dashboard | More › Sales Dashboard | - | Sales and Clients › Forecast, Sales and Clients › Sales Dashboard | 3 |
| Coordinator (Chen) | desktop | Sales | More › Sales | - | - | 1 (one way) |
| Coordinator (Chen) | desktop | Partners | More › Partners | - | - | 1 (one way) |
| Coordinator (Chen) | desktop | Playbook | More › Playbook | - | - | 1 (one way) |
| Coordinator (Chen) | desktop | Clients | More › Clients | - | Sales and Clients › Clients, Sales and Clients › Companies, Sales and Clients › People | 4 |
| Coordinator (Chen) | desktop | Sales (by the link Leads 1 inquiries to qualify) | none (reached by a link) | - | - | 0 |
| Coordinator (Chen) | desktop | People | none (reached by a link) | - | Sales and Clients › Clients, Sales and Clients › Companies, Sales and Clients › People | 3 |
| Coordinator (Chen) | desktop | Companies | none (reached by a link) | - | Sales and Clients › Clients, Sales and Clients › Companies, Sales and Clients › People | 3 |
| Coordinator (Chen) | phone | Forecast | More › Forecast | - | Sales and Clients › Forecast, Sales and Clients › Sales Dashboard | 3 |
| Coordinator (Chen) | phone | Sales Dashboard | More › Sales Dashboard | - | Sales and Clients › Forecast, Sales and Clients › Sales Dashboard | 3 |
| Coordinator (Chen) | phone | Sales | More › Sales | - | - | 1 (one way) |
| Coordinator (Chen) | phone | Partners | More › Partners | - | - | 1 (one way) |
| Coordinator (Chen) | phone | Playbook | More › Playbook | - | - | 1 (one way) |
| Coordinator (Chen) | phone | Clients | More › Clients | - | Sales and Clients › Clients, Sales and Clients › Companies, Sales and Clients › People | 4 |
| Coordinator (Chen) | phone | Sales (by the link Leads 1) | none (reached by a link) | - | - | 0 |
| Coordinator (Chen) | phone | People | none (reached by a link) | - | Sales and Clients › Clients, Sales and Clients › Companies, Sales and Clients › People | 3 |
| Coordinator (Chen) | phone | Companies | none (reached by a link) | - | Sales and Clients › Clients, Sales and Clients › Companies, Sales and Clients › People | 3 |
| Designer (Sarah) | desktop | Clients | Clients | - | - | 1 (one way) |
| Designer (Sarah) | phone | Clients | Clients | - | - | 1 (one way) |
| Billing | desktop | Clients | Clients | - | Sales and Clients › Clients, Sales and Clients › Companies, Sales and Clients › People | 4 |
| Billing | desktop | Forecast | More › Forecast | - | Sales and Clients › Forecast, Sales and Clients › Sales Dashboard | 3 |
| Billing | desktop | Sales Dashboard | More › Sales Dashboard | - | Sales and Clients › Forecast, Sales and Clients › Sales Dashboard | 3 |
| Billing | desktop | Sales | More › Sales | - | - | 1 (one way) |
| Billing | desktop | Partners | More › Partners | - | - | 1 (one way) |
| Billing | desktop | Playbook | More › Playbook | - | - | 1 (one way) |
| Billing | desktop | People | none (reached by a link) | - | Sales and Clients › Clients, Sales and Clients › Companies, Sales and Clients › People | 3 |
| Billing | desktop | Companies | none (reached by a link) | - | Sales and Clients › Clients, Sales and Clients › Companies, Sales and Clients › People | 3 |
| Billing | desktop | Sales (by the link Leads 1 inquiries to qualify) | none (reached by a link) | - | - | 0 |
| Billing | phone | Clients | Clients | yes | Sales and Clients › Clients, Sales and Clients › Companies, Sales and Clients › People | 5 |
| Billing | phone | Forecast | More › Forecast | - | Sales and Clients › Forecast, Sales and Clients › Sales Dashboard | 3 |
| Billing | phone | Sales Dashboard | More › Sales Dashboard | - | Sales and Clients › Forecast, Sales and Clients › Sales Dashboard | 3 |
| Billing | phone | Sales | More › Sales | - | - | 1 (one way) |
| Billing | phone | Partners | More › Partners | - | - | 1 (one way) |
| Billing | phone | Playbook | More › Playbook | - | - | 1 (one way) |
| Billing | phone | People | none (reached by a link) | - | Sales and Clients › Clients, Sales and Clients › Companies, Sales and Clients › People | 3 |
| Billing | phone | Companies | none (reached by a link) | - | Sales and Clients › Clients, Sales and Clients › Companies, Sales and Clients › People | 3 |
| Billing | phone | Sales (by the link Leads 1) | none (reached by a link) | - | - | 0 |
| Controller | desktop | Clients | More › Clients | - | - | 1 (one way) |
| Controller | phone | Clients | More › Clients | - | - | 1 (one way) |

**Pages of this module the role may open (ROLE_VIEWS) that no menu entry of this module or walked link reached.** Where the census landed on the page from another module (a tab that leaves, another group's entry), that place is named; "not reached" means no walked screen showed it, which for most is a retired page that lands on another (MN_ALIAS, OC_RETIRED) and is left to search and old links.

- Owner, desktop: `hbdeals` (not reached); `hbplaybooks` (not reached); `hbquotes` (not reached); `hbsequences` (not reached); `hbworkspace` (not reached); `scleads` (not reached)
- Owner, phone: `hbdeals` (not reached); `hbplaybooks` (not reached); `hbquotes` (not reached); `hbsequences` (not reached); `hbworkspace` (not reached); `scleads` (not reached)
- PM (Alan), desktop: `hbdeals` (not reached); `hbplaybooks` (not reached); `hbquotes` (not reached); `hbsequences` (not reached); `hbworkspace` (not reached); `scleads` (not reached)
- PM (Alan), phone: `hbdeals` (not reached); `hbplaybooks` (not reached); `hbquotes` (not reached); `hbsequences` (not reached); `hbworkspace` (not reached); `scleads` (not reached)
- Coordinator (Chen), desktop: `hbdeals` (not reached); `hbplaybooks` (not reached); `hbquotes` (not reached); `hbsequences` (not reached); `hbworkspace` (not reached); `scleads` (not reached)
- Coordinator (Chen), phone: `hbdeals` (not reached); `hbplaybooks` (not reached); `hbquotes` (not reached); `hbsequences` (not reached); `hbworkspace` (not reached); `scleads` (not reached)
- Billing, desktop: `hbdeals` (not reached); `hbplaybooks` (not reached); `hbquotes` (not reached); `hbsequences` (not reached); `hbworkspace` (not reached); `scleads` (not reached)
- Billing, phone: `hbdeals` (not reached); `hbplaybooks` (not reached); `hbquotes` (not reached); `hbsequences` (not reached); `hbworkspace` (not reached); `scleads` (not reached)

## 2. Where the Data Lives, and Where It Shows Twice

Records are found by their own words (the information map's catalog, the job's nouns and this census's: clients, vendors, leads, contacts, companies, every invoice, bill and PO, payroll runs, stock, meetings, journals, obligations, lessons, partners, bank lines, threads), so these are floors. A page's tabs count as the page.

### Owner, desktop: each kind of record, and the pages that list it

| Records | Found | Pages that list them (how many each) | Also in other modules |
|---|---|---|---|
| contacts | 19 | 6: Clients 19, People 19, Companies 19, Sales 6, Partners 3, Sales (by the link Leads 1 inquiries to qualify) 2 | Tasks and Messages › Tasks 5, Today › Chief of Staff 5, Company and Settings › The Brain 5, Today › Today 4 |
| leads | 9 | 5: Clients 9, People 9, Companies 9, Sales 6, Sales (by the link Leads 1 inquiries to qualify) 2 | Today › Chief of Staff 5, Company and Settings › The Brain 5, Tasks and Messages › Tasks 3, Today › Today 3 |
| clients | 5 | 5: Clients 5, People 5, Companies 5, Estimates 3, Sales 1 | Today › Chief of Staff 3, Design › Design 3, Accounting › Dashboard 3, Accounting › Reports 3 |
| partners | 3 | 4: Partners 3, Clients 3, People 3, Companies 3 | - |
| companies | 6 | 4: Clients 6, People 6, Companies 6, Partners 3 | - |
| to-dos | 2 | 1: Sales 2 | Tasks and Messages › Tasks 2 |
| schedule lines | 6 | 1: Estimates 6 | Accounting › Reports 5, Projects › Field 5, Projects › Schedule 5, Tasks and Messages › Tasks 4 |
| invoices | 6 | 1: Estimates 6 | Accounting › Ledger 6, Accounting › Reports 4 |
| estimates | 4 | 1: Estimates 4 | Accounting › Reports 2 |
| materials | 7 | 1: Estimates 7 | Today › Chief of Staff 7, Accounting › Reports 7, Company and Settings › Company Settings 7, Purchasing › Buy Board 7 |
| change orders | 2 | 1: Estimates 2 | Accounting › Reports 2, Projects › Documents 2, Accounting › Dashboard 1 |

### Records on two or more pages, and lists that are the same list twice

**Owner, desktop:** 42 records on two or more pages: contacts 19 (up to 5 pages); leads 9 (up to 5 pages); companies 6 (up to 4 pages); clients 5 (up to 4 pages); partners 3 (up to 4 pages).

- "Daniel Okafor" (leads) on 5 pages: Clients, Companies, People, Sales, Sales (by the link Leads 1 inquiries to qualify)
- "Marcus Bell" (leads) on 5 pages: Clients, Companies, People, Sales, Sales (by the link Leads 1 inquiries to qualify)
- "Daniel Okafor" (contacts) on 5 pages: Clients, Companies, People, Sales, Sales (by the link Leads 1 inquiries to qualify)
- "Marcus Bell" (contacts) on 5 pages: Clients, Companies, People, Sales, Sales (by the link Leads 1 inquiries to qualify)
- "The Lindqvists" (clients) on 4 pages: Clients, Companies, People, Sales
- "Priya Raman" (leads) on 4 pages: Clients, Companies, People, Sales

**PM (Alan), desktop:** 42 records on two or more pages: contacts 19 (up to 5 pages); leads 9 (up to 5 pages); companies 6 (up to 4 pages); clients 5 (up to 4 pages); partners 3 (up to 4 pages).


**Coordinator (Chen), desktop:** 57 records on two or more pages: contacts 19 (up to 5 pages); leads 9 (up to 5 pages); companies 6 (up to 4 pages); clients 5 (up to 4 pages); materials 4 (up to 2 pages); partners 3 (up to 4 pages); schedule lines 2 (up to 2 pages); approvals 2 (up to 2 pages); vendors 2 (up to 2 pages); to-dos 1 (up to 2 pages); field requests 1 (up to 2 pages); site questions 1 (up to 2 pages); COI lapses 1 (up to 2 pages); obligations 1 (up to 2 pages).

- the same list twice (3 or more shared records, at least half of the shorter list): Forecast and Sales Dashboard (13 shared, of 13 and 13: materials, schedule lines, approvals)

**Billing, desktop:** 50 records on two or more pages: contacts 19 (up to 5 pages); leads 9 (up to 5 pages); companies 6 (up to 4 pages); clients 5 (up to 5 pages); approvals 4 (up to 2 pages); partners 3 (up to 4 pages); findings 3 (up to 2 pages); mail 1 (up to 2 pages).

- the same list twice (3 or more shared records, at least half of the shorter list): Forecast and Sales Dashboard (8 shared, of 8 and 8: approvals, findings, mail)

**Owner, phone:** 39 records on two or more pages: contacts 19 (up to 5 pages); leads 9 (up to 5 pages); clients 5 (up to 4 pages); companies 3 (up to 4 pages); partners 3 (up to 4 pages).

- "Daniel Okafor" (leads) on 5 pages: Clients, Companies, People, Sales, Sales (by the link Leads 1)
- "Marcus Bell" (leads) on 5 pages: Clients, Companies, People, Sales, Sales (by the link Leads 1)
- "Daniel Okafor" (contacts) on 5 pages: Clients, Companies, People, Sales, Sales (by the link Leads 1)
- "Marcus Bell" (contacts) on 5 pages: Clients, Companies, People, Sales, Sales (by the link Leads 1)
- "The Lindqvists" (clients) on 4 pages: Clients, Companies, People, Sales
- "Priya Raman" (leads) on 4 pages: Clients, Companies, People, Sales

### The same records in other modules

For each role on the desktop: the pages of other modules (the Projects census's 121 State Street pages included) that list records this module lists, with how many.

- **Owner** (27 records here): Accounting › Reports 20; Tasks and Messages › Tasks 8; Projects › Job Page 8; Today › Chief of Staff 8; Company and Settings › Company Settings 8; Projects › Field 7; Projects › Schedule 7; Accounting › Ledger 7
- **PM (Alan)** (2 records here): Tasks and Messages › Tasks 2
- **Coordinator (Chen)** (15 records here): Today › Chief of Staff 9; Company and Settings › The Brain 9; Today › Approvals 8; Projects › Job Page 6; Tasks and Messages › Tasks 6; Purchasing › Buy Board 5; Accounting › Dashboard 5; Field and Site › Requests 4
- **Designer (Sarah)**: none found.
- **Billing** (10 records here): Today › Chief of Staff 7; Today › Approvals 7; Tasks and Messages › Tasks 2; Tasks and Messages › Messages 1
- **Controller**: none found.

Names (clients, vendors, leads, contacts, companies, partners) are left out here: a page that writes a name counts as listing it. A page that is the same page as one of this module's (one view under two menus) is left out too and listed next.

### The same page under two modules' menus

- Owner: Estimates here is also Billing › Billing, Projects › Change Orders, Projects › Estimates (`billing`)

## 3. One Label, Different Numbers

The same label (a tile, a figure, a tab or section count) with numbers that share no value on two pages, for one role. Some are right about different scopes ("Open" against "All", one job against every job); the person still reads one word with two numbers. Each needs a person to judge.

Inside the module: none found.

**Against other modules, Owner, desktop** (2):
- ready bill: $46K on Billing › Billing, Projects › Change Orders, Sales and Clients › Estimates; $12,651 on Projects › Job Page
- past due: $0 on Sales and Clients › Clients, Sales and Clients › Companies, Sales and Clients › People; 3 on Projects › Decisions

## 4. Empty, Dead and Broken Screens

| Device | Role | Screen | What |
|---|---|---|---|
| desktop | Owner | Numbers[Forecast] | the tab leaves for hbforecast |
| desktop | Owner | Numbers[Sales Dashboard] | the tab leaves for hbdash |
| desktop | Owner | Clients[People] | the tab leaves for hbcontacts |
| desktop | Owner | Clients[Companies] | the tab leaves for hbcompanies |
| desktop | Owner | Sales (by the link Leads 1 inquiries to qualify) | opens ovsales when asked for leads |
| desktop | Owner | Numbers — Forecast[Numbers] | the tab leaves for salesnum |
| desktop | Owner | Numbers — Forecast[Sales Dashboard] | the tab leaves for hbdash |
| desktop | Owner | Numbers — Dashboard[Numbers] | the tab leaves for salesnum |
| desktop | Owner | Numbers — Dashboard[Forecast] | the tab leaves for hbforecast |
| desktop | Owner | People[Clients] | the tab leaves for clients |
| desktop | Owner | People[Companies] | the tab leaves for hbcompanies |
| desktop | Owner | Companies[Clients] | the tab leaves for clients |
| desktop | Owner | Companies[People] | the tab leaves for hbcontacts |
| desktop | PM (Alan) | Clients[People] | the tab leaves for hbcontacts |
| desktop | PM (Alan) | Clients[Companies] | the tab leaves for hbcompanies |
| desktop | PM (Alan) | Numbers[Forecast] | the tab leaves for hbforecast |
| desktop | PM (Alan) | Numbers[Sales Dashboard] | the tab leaves for hbdash |
| desktop | PM (Alan) | People[Clients] | the tab leaves for clients |
| desktop | PM (Alan) | People[Companies] | the tab leaves for hbcompanies |
| desktop | PM (Alan) | Companies[Clients] | the tab leaves for clients |
| desktop | PM (Alan) | Companies[People] | the tab leaves for hbcontacts |
| desktop | PM (Alan) | Sales (by the link Leads 1 inquiries to qualify) | opens ovsales when asked for leads |
| desktop | PM (Alan) | Numbers — Forecast[Numbers] | the tab leaves for salesnum |
| desktop | PM (Alan) | Numbers — Forecast[Sales Dashboard] | the tab leaves for hbdash |
| desktop | PM (Alan) | Numbers — Dashboard[Numbers] | the tab leaves for salesnum |
| desktop | PM (Alan) | Numbers — Dashboard[Forecast] | the tab leaves for hbforecast |
| desktop | Coordinator (Chen) | Forecast[Numbers] | the tab leaves for home |
| desktop | Coordinator (Chen) | Forecast[Sales Dashboard] | the tab leaves for hbdash |
| desktop | Coordinator (Chen) | Sales Dashboard[Numbers] | the tab leaves for home |
| desktop | Coordinator (Chen) | Sales Dashboard[Forecast] | the tab leaves for hbforecast |
| desktop | Coordinator (Chen) | Clients[People] | the tab leaves for hbcontacts |
| desktop | Coordinator (Chen) | Clients[Companies] | the tab leaves for hbcompanies |
| desktop | Coordinator (Chen) | Sales (by the link Leads 1 inquiries to qualify) | opens ovsales when asked for leads |
| desktop | Coordinator (Chen) | People[Clients] | the tab leaves for clients |
| desktop | Coordinator (Chen) | People[Companies] | the tab leaves for hbcompanies |
| desktop | Coordinator (Chen) | Companies[Clients] | the tab leaves for clients |
| desktop | Coordinator (Chen) | Companies[People] | the tab leaves for hbcontacts |
| desktop | Billing | Clients[People] | the tab leaves for hbcontacts |
| desktop | Billing | Clients[Companies] | the tab leaves for hbcompanies |
| desktop | Billing | Forecast[Numbers] | the tab leaves for home |
| desktop | Billing | Forecast[Sales Dashboard] | the tab leaves for hbdash |
| desktop | Billing | Sales Dashboard[Numbers] | the tab leaves for home |
| desktop | Billing | Sales Dashboard[Forecast] | the tab leaves for hbforecast |
| desktop | Billing | People[Clients] | the tab leaves for clients |
| desktop | Billing | People[Companies] | the tab leaves for hbcompanies |
| desktop | Billing | Companies[Clients] | the tab leaves for clients |
| desktop | Billing | Companies[People] | the tab leaves for hbcontacts |
| desktop | Billing | Sales (by the link Leads 1 inquiries to qualify) | opens ovsales when asked for leads |
| phone | Owner | Numbers[Forecast] | the tab leaves for hbforecast |
| phone | Owner | Numbers[Sales Dashboard] | the tab leaves for hbdash |
| phone | Owner | Clients[People] | the tab leaves for hbcontacts |
| phone | Owner | Clients[Companies] | the tab leaves for hbcompanies |
| phone | Owner | Sales (by the link Leads 1) | opens ovsales when asked for leads |
| phone | Owner | Numbers — Forecast[Numbers] | the tab leaves for salesnum |
| phone | Owner | Numbers — Forecast[Sales Dashboard] | the tab leaves for hbdash |
| phone | Owner | Numbers — Dashboard[Numbers] | the tab leaves for salesnum |
| phone | Owner | Numbers — Dashboard[Forecast] | the tab leaves for hbforecast |
| phone | Owner | People[Clients] | the tab leaves for clients |
| phone | Owner | People[Companies] | the tab leaves for hbcompanies |
| phone | Owner | Companies[Clients] | the tab leaves for clients |
| phone | Owner | Companies[People] | the tab leaves for hbcontacts |
| phone | PM (Alan) | Clients[People] | the tab leaves for hbcontacts |
| phone | PM (Alan) | Clients[Companies] | the tab leaves for hbcompanies |
| phone | PM (Alan) | Numbers[Forecast] | the tab leaves for hbforecast |
| phone | PM (Alan) | Numbers[Sales Dashboard] | the tab leaves for hbdash |
| phone | PM (Alan) | People[Clients] | the tab leaves for clients |
| phone | PM (Alan) | People[Companies] | the tab leaves for hbcompanies |
| phone | PM (Alan) | Companies[Clients] | the tab leaves for clients |
| phone | PM (Alan) | Companies[People] | the tab leaves for hbcontacts |
| phone | PM (Alan) | Sales (by the link Leads 1) | opens ovsales when asked for leads |
| phone | PM (Alan) | Numbers — Forecast[Numbers] | the tab leaves for salesnum |
| phone | PM (Alan) | Numbers — Forecast[Sales Dashboard] | the tab leaves for hbdash |
| phone | PM (Alan) | Numbers — Dashboard[Numbers] | the tab leaves for salesnum |
| phone | PM (Alan) | Numbers — Dashboard[Forecast] | the tab leaves for hbforecast |
| phone | Coordinator (Chen) | Forecast | 1 save(s) while reading |
| phone | Coordinator (Chen) | Forecast[Numbers] | the tab leaves for home |
| phone | Coordinator (Chen) | Forecast[Sales Dashboard] | the tab leaves for hbdash |
| phone | Coordinator (Chen) | Sales Dashboard[Numbers] | the tab leaves for home |
| phone | Coordinator (Chen) | Sales Dashboard[Forecast] | the tab leaves for hbforecast |
| phone | Coordinator (Chen) | Clients[People] | the tab leaves for hbcontacts |
| phone | Coordinator (Chen) | Clients[Companies] | the tab leaves for hbcompanies |
| phone | Coordinator (Chen) | Sales (by the link Leads 1) | opens ovsales when asked for leads |
| phone | Coordinator (Chen) | People[Clients] | the tab leaves for clients |
| phone | Coordinator (Chen) | People[Companies] | the tab leaves for hbcompanies |
| phone | Coordinator (Chen) | Companies[Clients] | the tab leaves for clients |
| phone | Coordinator (Chen) | Companies[People] | the tab leaves for hbcontacts |
| phone | Billing | Clients[People] | the tab leaves for hbcontacts |
| phone | Billing | Clients[Companies] | the tab leaves for hbcompanies |
| phone | Billing | Forecast[Numbers] | the tab leaves for home |
| phone | Billing | Forecast[Sales Dashboard] | the tab leaves for hbdash |
| phone | Billing | Sales Dashboard[Numbers] | the tab leaves for home |
| phone | Billing | Sales Dashboard[Forecast] | the tab leaves for hbforecast |
| phone | Billing | People[Clients] | the tab leaves for clients |
| phone | Billing | People[Companies] | the tab leaves for hbcompanies |
| phone | Billing | Companies[Clients] | the tab leaves for clients |
| phone | Billing | Companies[People] | the tab leaves for hbcontacts |
| phone | Billing | Sales (by the link Leads 1) | opens ovsales when asked for leads |

## 5. The Phone at 390

"Cut off" is text the phone ends early; "scrolls inside" is a strip of tiles or tabs the person swipes sideways inside the page (the page itself does not move). "Strip swipe" counts pages whose strip entry sits off screen until the strip is swiped. Pages taller than 3 phone screens are listed with their height.

| Role | Screens | The page scrolls sideways | Text cut off at the edge | Strips that scroll inside the page | Strip swipe | Pages taller than 3 screens |
|---|---|---|---|---|---|---|
| Owner | 42 | 0 | 5: Clients, Companies, Estimates, People, Sales | 10: Clients, Companies, Estimates, Numbers, Numbers — Dashboard, Numbers — Forecast, Partners, People | 1: Playbook | 1: Playbook 4.4 |
| PM (Alan) | 34 | 0 | 5: Clients, Companies, People, Sales, Sales (by the link Leads 1) | 9: Clients, Companies, Numbers, Numbers — Dashboard, Numbers — Forecast, Partners, People, Sales | 4: Sales, Partners, Playbook, Numbers | 1: Playbook 4.4 |
| Coordinator (Chen) | 26 | 0 | 5: Clients, Companies, People, Sales, Sales (by the link Leads 1) | 6: Clients, Companies, Partners, People, Sales, Sales (by the link Leads 1) | 5: Sales Dashboard, Sales, Partners, Playbook, Clients | 1: Playbook 4.4 |
| Designer (Sarah) | 1 | 0 | 0 | 1: Clients | 0 | 0 |
| Billing | 26 | 0 | 5: Clients, Companies, People, Sales, Sales (by the link Leads 1) | 6: Clients, Companies, Partners, People, Sales, Sales (by the link Leads 1) | 5: Forecast, Sales Dashboard, Sales, Partners, Playbook | 1: Playbook 4.4 |
| Controller | 1 | 0 | 0 | 1: Clients | 1: Clients | 0 |

## 6. Page by Page, in Full

Every page the primary role reaches, as it opens, then each of its tabs. Heights are in screens of that device (900px desktop, 844px phone); "above the fold" is above the bottom bar on the phone.

### Owner, desktop

- reached by: Sales (1 tap); first button "New Opportunity"; shot [desktop](../../review/census/sales/shots/desktop_owner_sales.jpg)
- **Sales** (`ovsales`): heading "Sales", 0.7 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: New Lead
  - lead: "Every open opportunity, from the first inquiry to the proposal — what it is worth, who owns it and the next step that is due."
  - figures: Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M
  - records: 6 leads, 6 contacts, 1 to-dos, 1 clients
  - columns: table: OPPORTUNITY, STAGE, VALUE, OWNER, NEXT STEP, DUE, LAST TOUCH, CLOSE (6 rows)
  - fields: Search…, Saved view, Pipeline
  - tab groups: List / Board
  - tab **Board**: heading "Sales", 0 sections; 6 leads, 6 contacts, 2 to-dos, 1 clients
- reached by: Sales › Estimates (2 taps); also in Projects › Change Orders; Projects › Estimates; Accounting › Billing; first button "Billing Queue"; shot [desktop](../../review/census/sales/shots/desktop_owner_estimates.jpg)
- **Estimates** (`billing`): heading "Estimates", 0.6 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: New Estimate
  - lead: "What is ready to bill, what is drafted, what is sent and what is still owed."
  - records: 4 estimates, 3 clients
  - columns: table: NUMBER, CLIENT, PROJECT, TITLE, DATE, VALID UNTIL, TOTAL, STATUS (4 rows)
  - fields: bill-client, Search…
  - tab groups: Billing Queue / Progress Billing / Estimates 4 / Change Orders 2 / Invoices 6 / Schedule of Values / Payments 4 / Client Funds
  - tab **Billing Queue**: heading "Billing", 0 sections; 3 clients, 2 invoices
  - tab **Progress Billing**: heading "Billing", 6 sections; 6 schedule lines, 6 materials, 2 clients, 1 change orders
  - tab **Change Orders**: heading "Billing", 0 sections; 2 change orders, 1 clients
  - tab **Invoices**: heading "Billing", 0 sections; 6 invoices, 3 clients
  - tab **Schedule of Values**: heading "Billing", 3 sections; 3 clients
  - tab **Payments**: heading "Billing", 1 sections; 4 invoices, 2 clients
  - tab **Client Funds**: heading "Billing", 3 sections; 4 materials
- reached by: Sales › Numbers (2 taps); first button "Numbers"; shot [desktop](../../review/census/sales/shots/desktop_owner_numbers.jpg)
- **Numbers** (`salesnum`): heading "Numbers", 0.7 screens tall, 1 sections (1 above the fold), 6 tab screens; blue: none
  - lead: "Which sources pay, where the process leaks, how fast we reply, and why we lose."
  - sections: From Inquiry to Agreement (22)
  - figures: First Reply 3 h; No Next Step 3; Proposals Aging 0; Won This Quarter $210K
  - tab groups: Numbers / Forecast / Sales Dashboard; Design-Build / Construction Only / Design Only; Funnel / By Source / Lost and Why / Marketing Spend / Ranges We Quote
  - tab **Forecast**: heading "Numbers — Forecast", 0 sections (the tab leaves for `hbforecast`)
  - tab **Sales Dashboard**: heading "Numbers — Dashboard", 7 sections (the tab leaves for `hbdash`)
  - tab **Construction Only**: heading "Numbers", 1 sections
  - tab **Design Only**: heading "Numbers", 1 sections
  - tab **By Source**: heading "Numbers", 1 sections
  - tab **By Source › Funnel**: heading "Numbers", 1 sections
  - tabs that would not press (the row changed once one was pressed): Lost and Why, Marketing Spend, Ranges We Quote
- reached by: Sales › Partners (2 taps); first button "Thank-Yous Owed 1 David sent us work and"; shot [desktop](../../review/census/sales/shots/desktop_owner_partners.jpg)
- **Partners** (`partners`): heading "Partners", 0.6 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Partner
  - lead: "The brokers, architects, managing agents and past clients who send us work — and what we owe them."
  - figures: Thank-Yous Owed 1; Due a Touch 1; Leads This Quarter 3; Won Through Partners $210K
  - records: 3 contacts, 3 companies, 3 partners
  - columns: table: PARTNER, KIND, LEADS, WON, VALUE WON, LAST TOUCH, OWED (3 rows)
- reached by: Sales › Playbook (2 taps); shot [desktop](../../review/census/sales/shots/desktop_owner_playbook.jpg)
- **Playbook** (`playbook`): heading "Playbook", 2.2 screens tall, 5 sections (2 above the fold), 0 tab screens; blue: none
  - lead: "How we sell: the discovery script, the objections, the up-front contract, the words, the cadence."
  - sections: Discovery — The Script, in Order; Objections — Label, Then a Calibrated Question; The Up-Front Contract — Every Meeting; Words; Cadence — Ten Touches Over Thirty Days, Each One Adds Value
  - fields: Search the playbook
- reached by: Clients (1 tap); first button "Clients"; shot [desktop](../../review/census/sales/shots/desktop_owner_clients.jpg)
- **Clients** (`clients`): heading "Clients", 0.7 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: New Client
  - lead: "People, properties and the conversation. Invoices and payments live in Billing."
  - figures: Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1
  - records: 5 clients, 5 contacts, 2 leads
  - columns: table: CLIENT, PERSON, PHONE, EMAIL, PROPERTY, Building, PROJECTS, Decisions, LAST TOUCH (5 rows)
  - fields: Search…
  - tab groups: Clients / People / Companies
  - tab **People**: heading "People", 0 sections; 19 contacts, 8 leads, 3 companies, 3 partners (the tab leaves for `hbcontacts`)
  - tab **Companies**: heading "Companies", 0 sections; 6 companies (the tab leaves for `hbcompanies`)
- reached by: Sales › link: Leads 1 inquiries to qualify · every one; first button "New Opportunity"; shot [desktop](../../review/census/sales/shots/desktop_owner_leads_1_inquiries_to_qualify_every_one.jpg)
- **Sales (by the link Leads 1 inquiries to qualify)** (`ovsales`): heading "Sales", 0.5 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: New Lead; opens `ovsales` when asked for `leads`
  - lead: "Every open opportunity, from the first inquiry to the proposal — what it is worth, who owns it and the next step that is due."
  - figures: Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M
  - records: 1 leads, 1 contacts
  - columns: table: OPPORTUNITY, STAGE, VALUE, OWNER, NEXT STEP, DUE, LAST TOUCH, CLOSE (1 rows)
  - fields: Search…, Saved view, Pipeline
  - tab groups: Leads 1 inquiries to qualify · every one / Stalled 1 no touch in 14 days — an oppor / No Next Step 3 3 past their date / Open Pipeline $1.3M 6 opportunities · we; List / Board
  - tab **Stalled 1 no touch in 14 days — an oppor**: heading "Sales", 0 sections; 1 leads, 1 contacts
  - tabs that would not press (the row changed once one was pressed): No Next Step 3 3 past their date, Open Pipeline $1.3M 6 opportunities · we
- reached by: Numbers › link: Forecast; first button "Numbers"; shot [desktop](../../review/census/sales/shots/desktop_owner_forecast.jpg)
- **Numbers — Forecast** (`hbforecast`): heading "Numbers — Forecast", 0.9 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: none
  - lead: "What is expected to close this period, by stage and by forecast category."
  - columns: table: TEAM / REP, GOAL, CLOSED WON, GAP, FORECAST SUBMISSION, OPEN PIPELINE, COVERAGE, WEIGHTED PIPELINE, INQUIRY (11 rows)
  - fields: Pipeline, Close Date, Team
  - tab groups: Numbers / Forecast / Sales Dashboard; Stage / Forecast Category
  - tab **Numbers**: heading "Numbers", 1 sections (the tab leaves for `salesnum`)
  - tab **Sales Dashboard**: heading "Numbers — Dashboard", 7 sections (the tab leaves for `hbdash`)
  - tab **Forecast Category**: heading "Forecast", 0 sections
- reached by: Numbers › link: Sales Dashboard; first button "Numbers"; shot [desktop](../../review/census/sales/shots/desktop_owner_sales_dashboard.jpg)
- **Numbers — Dashboard** (`hbdash`): heading "Numbers — Dashboard", 0.8 screens tall, 7 sections (7 above the fold), 2 tab screens; blue: none
  - lead: "How sales is going: what came in, what moved, what closed."
  - sections: FORECAST; OPPORTUNITIES CLOSED VS GOAL (1); STAGE FUNNEL; SALES ACTIVITY; OPPORTUNITIES CREATED BY SOURCE; MEETINGS BOOKED; OPEN OPPORTUNITIES BY STAGE
  - columns: table: REP, CALLS, EMAILS, MEETINGS, NOTES (1 rows)
  - fields: Dashboard, Date Range, Owner
  - tab groups: Numbers / Forecast / Sales Dashboard
  - tab **Numbers**: heading "Numbers", 1 sections (the tab leaves for `salesnum`)
  - tab **Forecast**: heading "Numbers — Forecast", 0 sections (the tab leaves for `hbforecast`)
- reached by: Clients › link: People; first button "Clients"; shot [desktop](../../review/census/sales/shots/desktop_owner_people.jpg)
- **People** (`hbcontacts`): heading "People", 1.4 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: New Person
  - lead: "19 records"
  - figures: Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9
  - records: 19 contacts, 8 leads, 3 companies, 3 partners, 1 clients
  - columns: table: NAME, EMAIL, PHONE NUMBER, LEAD STATUS, LIFECYCLE STAGE, COMPANY NAME, OWNER, LAST ACTIVITY (19 rows)
  - fields: Saved view, Owner, Lead Status, Search name, phone, email…, Rows per Page
  - tab groups: Clients / People / Companies; Prev /  / Next
  - tab **Clients**: heading "Clients", 0 sections; 5 clients, 5 contacts, 2 leads (the tab leaves for `clients`)
  - tab **Companies**: heading "Companies", 0 sections; 6 companies (the tab leaves for `hbcompanies`)
  - tab **Prev**: heading "People", 0 sections; 19 contacts, 8 leads, 3 companies, 3 partners
  - tab **Next**: heading "People", 0 sections; 19 contacts, 8 leads, 3 companies, 3 partners
- reached by: Clients › link: Companies; first button "Clients"; shot [desktop](../../review/census/sales/shots/desktop_owner_companies.jpg)
- **Companies** (`hbcompanies`): heading "Companies", 0.6 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: New Company
  - lead: "6 records"
  - records: 6 companies
  - columns: table: COMPANY NAME, COMPANY DOMAIN NAME, TYPE, CITY, OWNER, LAST ACTIVITY (6 rows)
  - fields: Saved view, Owner, Lead Status, Search name, domain…, Rows per Page
  - tab groups: Clients / People / Companies; Prev /  / Next
  - tab **Clients**: heading "Clients", 0 sections; 5 clients, 5 contacts, 2 leads (the tab leaves for `clients`)
  - tab **People**: heading "People", 0 sections; 19 contacts, 8 leads, 3 companies, 3 partners (the tab leaves for `hbcontacts`)
  - tab **Prev**: heading "Companies", 0 sections; 6 companies
  - tab **Next**: heading "Companies", 0 sections; 6 companies

### Owner, phone

- reached by: bar: Sales (1 tap); first button "New Opportunity"; shot [phone](../../review/census/sales/shots/phone_owner_sales.jpg)
- **Sales** (`ovsales`): heading "Sales", 1.1 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: New Lead; runs past the edge: cut off by pr-m ($260,000 · You · Answer the board questi, $420,000 · You · Walk the house with the)
  - lead: "Every open opportunity, from the first inquiry to the proposal — what it is worth, who owns it and the next step that is due."
  - figures: Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M
  - records: 6 leads, 6 contacts, 1 to-dos, 1 clients
  - columns: table: Opportunity, Stage, Value, Owner, Next Step, Due, Last Touch, Close (6 rows)
  - fields: Search…, Saved view, Pipeline
  - tab groups: List / Board
  - tab **Board**: heading "Sales", 0 sections; 6 leads, 6 contacts, 2 to-dos, 1 clients
- reached by: menu › Sales › Estimates (3 taps); also in Projects › Change Orders; Projects › Estimates; Accounting › Billing; first button "Billing Queue"; shot [phone](../../review/census/sales/shots/phone_owner_estimates.jpg)
- **Estimates** (`billing`): heading "Estimates", 0.9 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: New Estimate
  - lead: "What is ready to bill, what is drafted, what is sent and what is still owed."
  - records: 4 estimates, 3 clients
  - columns: table: Number, Client, Project, Title, Date, Valid Until, Total, Status (4 rows)
  - fields: bill-client, Search…
  - tab groups: Billing Queue / Progress Billing / Estimates 4 / Change Orders 2 / Invoices 6 / Schedule of Values / Payments 4 / Client Funds
  - tab **Billing Queue**: heading "Billing", 0 sections; 3 clients, 2 invoices
  - tab **Progress Billing**: heading "Billing", 6 sections; 6 materials, 2 clients, 1 change orders, 1 schedule lines (runs past the edge: cut off by pr-m (Demolition & disposalContract · 02 · $28, Framing, blocking & rough carpentryContr))
  - tab **Change Orders**: heading "Billing", 0 sections; 2 change orders, 1 clients
  - tab **Invoices**: heading "Billing", 0 sections; 6 invoices, 3 clients
  - tab **Schedule of Values**: heading "Billing", 3 sections; 3 clients
  - tab **Payments**: heading "Billing", 1 sections; 4 invoices, 2 clients
  - tab **Client Funds**: heading "Client Funds & Purchasing Obligations", 2 sections; 4 materials
- reached by: menu › Sales › Numbers (3 taps); first button "Numbers"; shot [phone](../../review/census/sales/shots/phone_owner_numbers.jpg)
- **Numbers** (`salesnum`): heading "Numbers", 1.1 screens tall, 1 sections (1 above the fold), 7 tab screens; blue: none
  - lead: "Which sources pay, where the process leaks, how fast we reply, and why we lose."
  - sections: From Inquiry to Agreement (22)
  - figures: First Reply 3 h; No Next Step 3; Proposals Aging 0; Won This Quarter $210K
  - tab groups: Numbers / Forecast / Sales Dashboard; Design-Build / Construction Only / Design Only; Funnel / By Source / Lost and Why / Marketing Spend / Ranges We Quote
  - tab **Forecast**: heading "Numbers — Forecast", 0 sections (the tab leaves for `hbforecast`)
  - tab **Sales Dashboard**: heading "Numbers — Dashboard", 7 sections (the tab leaves for `hbdash`)
  - tab **Construction Only**: heading "Numbers", 1 sections
  - tab **Design Only**: heading "Numbers", 1 sections
  - tab **By Source**: heading "Numbers", 1 sections
  - tab **By Source › Funnel**: heading "Numbers", 1 sections
  - tab **Lost and Why**: heading "Numbers", 2 sections; 2 leads, 2 contacts
  - tabs that would not press (the row changed once one was pressed): Marketing Spend, Ranges We Quote
- reached by: menu › Sales › Partners (3 taps); first button "Thank-Yous Owed 1"; shot [phone](../../review/census/sales/shots/phone_owner_partners.jpg)
- **Partners** (`partners`): heading "Partners", 0.7 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Partner
  - lead: "The brokers, architects, managing agents and past clients who send us work — and what we owe them."
  - figures: Thank-Yous Owed 1; Due a Touch 1; Leads This Quarter 3; Won Through Partners $210K
  - records: 3 contacts, 3 companies, 3 partners
  - columns: table: Partner, Kind, Leads, Won, Value Won, Last Touch, Owed (3 rows)
- reached by: menu › Sales › swipe the strip, Playbook (3 taps); shot [phone](../../review/census/sales/shots/phone_owner_playbook.jpg)
- **Playbook** (`playbook`): heading "Playbook", 4.4 screens tall, 5 sections (1 above the fold), 0 tab screens; blue: none
  - lead: "How we sell: the discovery script, the objections, the up-front contract, the words, the cadence."
  - sections: Discovery — The Script, in Order; Objections — Label, Then a Calibrated Question; The Up-Front Contract — Every Meeting; Words; Cadence — Ten Touches Over Thirty Days, Each One Adds Value
  - fields: Search the playbook
- reached by: menu › Clients (2 taps); first button "Clients"; shot [phone](../../review/census/sales/shots/phone_owner_clients.jpg)
- **Clients** (`clients`): heading "Clients", 0.9 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: New Client
  - lead: "People, properties and the conversation. Invoices and payments live in Billing."
  - figures: Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1
  - records: 5 clients, 5 contacts, 2 leads
  - columns: table: Client, Person, Phone, Email, Property, Building, Projects, Decisions, Last Touch (5 rows)
  - fields: Search…
  - tab groups: Clients / People / Companies
  - tab **People**: heading "People", 0 sections; 19 contacts, 8 leads, 3 partners, 2 companies (runs past the edge: cut off by pr-m (sofia.adler@example.com · Attempted to c, +1 917 555 0188 · Attempted to contact ·); the tab leaves for `hbcontacts`)
  - tab **Companies**: heading "Companies", 0 sections; 1 companies (the tab leaves for `hbcompanies`)
- reached by: Sales › link: Leads 1; first button "New Opportunity"; shot [phone](../../review/census/sales/shots/phone_owner_leads_1.jpg)
- **Sales (by the link Leads 1)** (`ovsales`): heading "Sales", 0.7 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: New Lead; opens `ovsales` when asked for `leads`
  - lead: "Every open opportunity, from the first inquiry to the proposal — what it is worth, who owns it and the next step that is due."
  - figures: Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M
  - records: 1 leads, 1 contacts
  - columns: table: Opportunity, Stage, Value, Owner, Next Step, Due, Last Touch, Close (1 rows)
  - fields: Search…, Saved view, Pipeline
  - tab groups: Leads 1 / Stalled 1 / No Next Step 3 / Open Pipeline $1.3M; List / Board
  - tab **Stalled**: heading "Sales", 0 sections; 1 leads, 1 contacts
  - tabs that would not press (the row changed once one was pressed): No Next Step, Open Pipeline $1.3M
- reached by: Numbers › link: Forecast; first button "Numbers"; shot [phone](../../review/census/sales/shots/phone_owner_forecast.jpg)
- **Numbers — Forecast** (`hbforecast`): heading "Numbers — Forecast", 1.4 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: none
  - lead: "What is expected to close this period, by stage and by forecast category."
  - columns: table: Team / Rep, Goal, Closed Won, Gap, Forecast Submission, Open Pipeline, Coverage, Weighted Pipeline, Inquiry (11 rows)
  - fields: Pipeline, Close Date, Team
  - tab groups: Numbers / Forecast / Sales Dashboard; Stage / Forecast Category
  - tab **Numbers**: heading "Numbers", 1 sections (the tab leaves for `salesnum`)
  - tab **Sales Dashboard**: heading "Numbers — Dashboard", 7 sections (the tab leaves for `hbdash`)
  - tab **Forecast Category**: heading "Forecast", 0 sections
- reached by: Numbers › link: Sales Dashboard; first button "Numbers"; shot [phone](../../review/census/sales/shots/phone_owner_sales_dashboard.jpg)
- **Numbers — Dashboard** (`hbdash`): heading "Numbers — Dashboard", 2.0 screens tall, 7 sections (2 above the fold), 2 tab screens; blue: none
  - lead: "How sales is going: what came in, what moved, what closed."
  - sections: FORECAST; OPPORTUNITIES CLOSED VS GOAL (1); STAGE FUNNEL; SALES ACTIVITY; OPPORTUNITIES CREATED BY SOURCE; MEETINGS BOOKED; OPEN OPPORTUNITIES BY STAGE
  - columns: table: Rep, Calls, Emails, Meetings, Notes (1 rows)
  - fields: Dashboard, Date Range, Owner
  - tab groups: Numbers / Forecast / Sales Dashboard
  - tab **Numbers**: heading "Numbers", 1 sections (the tab leaves for `salesnum`)
  - tab **Forecast**: heading "Numbers — Forecast", 0 sections (the tab leaves for `hbforecast`)
- reached by: Clients › link: People; first button "Clients"; shot [phone](../../review/census/sales/shots/phone_owner_people.jpg)
- **People** (`hbcontacts`): heading "People", 2.0 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: New Person; runs past the edge: cut off by pr-m (sofia.adler@example.com · Attempted to c, +1 917 555 0188 · Attempted to contact ·)
  - lead: "19 records"
  - figures: Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9
  - records: 19 contacts, 8 leads, 3 partners, 2 companies, 1 clients
  - columns: table: Name, Email, Phone Number, Lead Status, Lifecycle Stage, Company Name, Owner, Last Activity (19 rows)
  - fields: Saved view, Owner, Lead Status, Search name, phone, email…, Rows per Page
  - tab groups: Clients / People / Companies; Prev /  / Next
  - tab **Clients**: heading "Clients", 0 sections; 5 clients, 5 contacts, 2 leads (the tab leaves for `clients`)
  - tab **Companies**: heading "Companies", 0 sections; 1 companies (the tab leaves for `hbcompanies`)
  - tab **Prev**: heading "People", 0 sections; 19 contacts, 8 leads, 3 partners, 2 companies (runs past the edge: cut off by pr-m (sofia.adler@example.com · Attempted to c, +1 917 555 0188 · Attempted to contact ·))
  - tab **Next**: heading "People", 0 sections; 19 contacts, 8 leads, 3 partners, 2 companies (runs past the edge: cut off by pr-m (sofia.adler@example.com · Attempted to c, +1 917 555 0188 · Attempted to contact ·))
- reached by: Clients › link: Companies; first button "Clients"; shot [phone](../../review/census/sales/shots/phone_owner_companies.jpg)
- **Companies** (`hbcompanies`): heading "Companies", 0.9 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: New Company
  - lead: "6 records"
  - records: 1 companies
  - columns: table: Company Name, Company Domain Name, Type, City, Owner, Last Activity (6 rows)
  - fields: Saved view, Owner, Lead Status, Search name, domain…, Rows per Page
  - tab groups: Clients / People / Companies; Prev /  / Next
  - tab **Clients**: heading "Clients", 0 sections; 5 clients, 5 contacts, 2 leads (the tab leaves for `clients`)
  - tab **People**: heading "People", 0 sections; 19 contacts, 8 leads, 3 partners, 2 companies (runs past the edge: cut off by pr-m (sofia.adler@example.com · Attempted to c, +1 917 555 0188 · Attempted to contact ·); the tab leaves for `hbcontacts`)
  - tab **Prev**: heading "Companies", 0 sections; 1 companies
  - tab **Next**: heading "Companies", 0 sections; 1 companies

## 7. The Other Roles, One Line a Page

### PM (Alan), desktop

- reached by: Clients (1 tap); shot [desktop](../../review/census/sales/shots/desktop_pm_clients.jpg)
- **Clients** (`clients`): heading "Clients", 0.7 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: New Client
- reached by: More › Sales (2 taps); shot [desktop](../../review/census/sales/shots/desktop_pm_sales.jpg)
- **Sales** (`ovsales`): heading "Sales", 0.7 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: New Lead
- reached by: More › Partners (2 taps); shot [desktop](../../review/census/sales/shots/desktop_pm_partners.jpg)
- **Partners** (`partners`): heading "Partners", 0.6 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Partner
- reached by: More › Playbook (2 taps); shot [desktop](../../review/census/sales/shots/desktop_pm_playbook.jpg)
- **Playbook** (`playbook`): heading "Playbook", 2.2 screens tall, 5 sections (2 above the fold), 0 tab screens; blue: none
- reached by: More › Numbers (2 taps); shot [desktop](../../review/census/sales/shots/desktop_pm_numbers.jpg)
- **Numbers** (`salesnum`): heading "Numbers", 0.7 screens tall, 1 sections (1 above the fold), 6 tab screens; blue: none
- reached by: Clients › link: People; shot [desktop](../../review/census/sales/shots/desktop_pm_people.jpg)
- **People** (`hbcontacts`): heading "People", 1.4 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: New Person
- reached by: Clients › link: Companies; shot [desktop](../../review/census/sales/shots/desktop_pm_companies.jpg)
- **Companies** (`hbcompanies`): heading "Companies", 0.6 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: New Company
- reached by: Sales › link: Leads 1 inquiries to qualify · every one; shot [desktop](../../review/census/sales/shots/desktop_pm_leads_1_inquiries_to_qualify_every_one.jpg)
- **Sales (by the link Leads 1 inquiries to qualify)** (`ovsales`): heading "Sales", 0.5 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: New Lead; opens `ovsales` when asked for `leads`
- reached by: Numbers › link: Forecast; shot [desktop](../../review/census/sales/shots/desktop_pm_forecast.jpg)
- **Numbers — Forecast** (`hbforecast`): heading "Numbers — Forecast", 0.9 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: none
- reached by: Numbers › link: Sales Dashboard; shot [desktop](../../review/census/sales/shots/desktop_pm_sales_dashboard.jpg)
- **Numbers — Dashboard** (`hbdash`): heading "Numbers — Dashboard", 0.8 screens tall, 7 sections (7 above the fold), 2 tab screens; blue: none

### PM (Alan), phone

- reached by: bar: Clients (1 tap); shot [phone](../../review/census/sales/shots/phone_pm_clients.jpg)
- **Clients** (`clients`): heading "Clients", 0.9 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: New Client
- reached by: menu › More › swipe the strip, Sales (3 taps); shot [phone](../../review/census/sales/shots/phone_pm_sales.jpg)
- **Sales** (`ovsales`): heading "Sales", 1.1 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: New Lead; runs past the edge: cut off by pr-m ($140,000 · Owner · Follow up on the prop, $260,000 · Owner · Answer the board ques)
- reached by: menu › More › swipe the strip, Partners (3 taps); shot [phone](../../review/census/sales/shots/phone_pm_partners.jpg)
- **Partners** (`partners`): heading "Partners", 0.7 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Partner
- reached by: menu › More › swipe the strip, Playbook (3 taps); shot [phone](../../review/census/sales/shots/phone_pm_playbook.jpg)
- **Playbook** (`playbook`): heading "Playbook", 4.4 screens tall, 5 sections (1 above the fold), 0 tab screens; blue: none
- reached by: menu › More › swipe the strip, Numbers (3 taps); shot [phone](../../review/census/sales/shots/phone_pm_numbers.jpg)
- **Numbers** (`salesnum`): heading "Numbers", 1.1 screens tall, 1 sections (1 above the fold), 7 tab screens; blue: none
- reached by: Clients › link: People; shot [phone](../../review/census/sales/shots/phone_pm_people.jpg)
- **People** (`hbcontacts`): heading "People", 2.0 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: New Person; runs past the edge: cut off by pr-m (sofia.adler@example.com · Attempted to c, +1 917 555 0188 · Attempted to contact ·)
- reached by: Clients › link: Companies; shot [phone](../../review/census/sales/shots/phone_pm_companies.jpg)
- **Companies** (`hbcompanies`): heading "Companies", 0.9 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: New Company
- reached by: Sales › link: Leads 1; shot [phone](../../review/census/sales/shots/phone_pm_leads_1.jpg)
- **Sales (by the link Leads 1)** (`ovsales`): heading "Sales", 0.7 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: New Lead; opens `ovsales` when asked for `leads`
- reached by: Numbers › link: Forecast; shot [phone](../../review/census/sales/shots/phone_pm_forecast.jpg)
- **Numbers — Forecast** (`hbforecast`): heading "Numbers — Forecast", 1.4 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: none
- reached by: Numbers › link: Sales Dashboard; shot [phone](../../review/census/sales/shots/phone_pm_sales_dashboard.jpg)
- **Numbers — Dashboard** (`hbdash`): heading "Numbers — Dashboard", 2.0 screens tall, 7 sections (2 above the fold), 2 tab screens; blue: none

### Coordinator (Chen), desktop

- reached by: More › Forecast (2 taps); shot [desktop](../../review/census/sales/shots/desktop_coord_forecast.jpg)
- **Forecast** (`hbforecast`): heading "Forecast", 0.9 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: none
- reached by: More › Sales Dashboard (2 taps); shot [desktop](../../review/census/sales/shots/desktop_coord_sales_dashboard.jpg)
- **Sales Dashboard** (`hbdash`): heading "Sales Dashboard", 0.8 screens tall, 7 sections (7 above the fold), 2 tab screens; blue: none
- reached by: More › Sales (2 taps); shot [desktop](../../review/census/sales/shots/desktop_coord_sales.jpg)
- **Sales** (`ovsales`): heading "Sales", 0.7 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: New Lead
- reached by: More › Partners (2 taps); shot [desktop](../../review/census/sales/shots/desktop_coord_partners.jpg)
- **Partners** (`partners`): heading "Partners", 0.6 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Partner
- reached by: More › Playbook (2 taps); shot [desktop](../../review/census/sales/shots/desktop_coord_playbook.jpg)
- **Playbook** (`playbook`): heading "Playbook", 2.2 screens tall, 5 sections (2 above the fold), 0 tab screens; blue: none
- reached by: More › Clients (2 taps); shot [desktop](../../review/census/sales/shots/desktop_coord_clients.jpg)
- **Clients** (`clients`): heading "Clients", 0.7 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: New Client
- reached by: Sales › link: Leads 1 inquiries to qualify · every one; shot [desktop](../../review/census/sales/shots/desktop_coord_leads_1_inquiries_to_qualify_every_one.jpg)
- **Sales (by the link Leads 1 inquiries to qualify)** (`ovsales`): heading "Sales", 0.5 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: New Lead; opens `ovsales` when asked for `leads`
- reached by: Clients › link: People; shot [desktop](../../review/census/sales/shots/desktop_coord_people.jpg)
- **People** (`hbcontacts`): heading "People", 1.4 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: New Person
- reached by: Clients › link: Companies; shot [desktop](../../review/census/sales/shots/desktop_coord_companies.jpg)
- **Companies** (`hbcompanies`): heading "Companies", 0.6 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: New Company

### Coordinator (Chen), phone

- reached by: menu › More › Forecast (3 taps); shot [phone](../../review/census/sales/shots/phone_coord_forecast.jpg)
- **Forecast** (`hbforecast`): heading "Forecast", 1.4 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: none; 1 save(s) while reading
- reached by: menu › More › swipe the strip, Sales Dashboard (3 taps); shot [phone](../../review/census/sales/shots/phone_coord_sales_dashboard.jpg)
- **Sales Dashboard** (`hbdash`): heading "Sales Dashboard", 2.0 screens tall, 7 sections (2 above the fold), 2 tab screens; blue: none
- reached by: menu › More › swipe the strip, Sales (3 taps); shot [phone](../../review/census/sales/shots/phone_coord_sales.jpg)
- **Sales** (`ovsales`): heading "Sales", 1.1 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: New Lead; runs past the edge: cut off by pr-m ($140,000 · Owner · Follow up on the prop, $260,000 · Owner · Answer the board ques)
- reached by: menu › More › swipe the strip, Partners (3 taps); shot [phone](../../review/census/sales/shots/phone_coord_partners.jpg)
- **Partners** (`partners`): heading "Partners", 0.7 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Partner
- reached by: menu › More › swipe the strip, Playbook (3 taps); shot [phone](../../review/census/sales/shots/phone_coord_playbook.jpg)
- **Playbook** (`playbook`): heading "Playbook", 4.4 screens tall, 5 sections (1 above the fold), 0 tab screens; blue: none
- reached by: menu › More › swipe the strip, Clients (3 taps); shot [phone](../../review/census/sales/shots/phone_coord_clients.jpg)
- **Clients** (`clients`): heading "Clients", 0.9 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: New Client
- reached by: Sales › link: Leads 1; shot [phone](../../review/census/sales/shots/phone_coord_leads_1.jpg)
- **Sales (by the link Leads 1)** (`ovsales`): heading "Sales", 0.7 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: New Lead; opens `ovsales` when asked for `leads`
- reached by: Clients › link: People; shot [phone](../../review/census/sales/shots/phone_coord_people.jpg)
- **People** (`hbcontacts`): heading "People", 2.0 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: New Person; runs past the edge: cut off by pr-m (sofia.adler@example.com · Attempted to c, +1 917 555 0188 · Attempted to contact ·)
- reached by: Clients › link: Companies; shot [phone](../../review/census/sales/shots/phone_coord_companies.jpg)
- **Companies** (`hbcompanies`): heading "Companies", 0.9 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: New Company

### Designer (Sarah), desktop

- reached by: Clients (1 tap); shot [desktop](../../review/census/sales/shots/desktop_designer_clients.jpg)
- **Clients** (`clients`): heading "Clients", 0.6 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Client

### Designer (Sarah), phone

- reached by: menu › Clients (2 taps); shot [phone](../../review/census/sales/shots/phone_designer_clients.jpg)
- **Clients** (`clients`): heading "Clients", 0.8 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Client

### Billing, desktop

- reached by: Clients (1 tap); shot [desktop](../../review/census/sales/shots/desktop_billing_clients.jpg)
- **Clients** (`clients`): heading "Clients", 0.7 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: New Client
- reached by: More › Forecast (2 taps); shot [desktop](../../review/census/sales/shots/desktop_billing_forecast.jpg)
- **Forecast** (`hbforecast`): heading "Forecast", 0.9 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: none
- reached by: More › Sales Dashboard (2 taps); shot [desktop](../../review/census/sales/shots/desktop_billing_sales_dashboard.jpg)
- **Sales Dashboard** (`hbdash`): heading "Sales Dashboard", 0.8 screens tall, 7 sections (7 above the fold), 2 tab screens; blue: none
- reached by: More › Sales (2 taps); shot [desktop](../../review/census/sales/shots/desktop_billing_sales.jpg)
- **Sales** (`ovsales`): heading "Sales", 0.7 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: New Lead
- reached by: More › Partners (2 taps); shot [desktop](../../review/census/sales/shots/desktop_billing_partners.jpg)
- **Partners** (`partners`): heading "Partners", 0.6 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Partner
- reached by: More › Playbook (2 taps); shot [desktop](../../review/census/sales/shots/desktop_billing_playbook.jpg)
- **Playbook** (`playbook`): heading "Playbook", 2.2 screens tall, 5 sections (2 above the fold), 0 tab screens; blue: none
- reached by: Clients › link: People; shot [desktop](../../review/census/sales/shots/desktop_billing_people.jpg)
- **People** (`hbcontacts`): heading "People", 1.4 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: New Person
- reached by: Clients › link: Companies; shot [desktop](../../review/census/sales/shots/desktop_billing_companies.jpg)
- **Companies** (`hbcompanies`): heading "Companies", 0.6 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: New Company
- reached by: Sales › link: Leads 1 inquiries to qualify · every one; shot [desktop](../../review/census/sales/shots/desktop_billing_leads_1_inquiries_to_qualify_every_one.jpg)
- **Sales (by the link Leads 1 inquiries to qualify)** (`ovsales`): heading "Sales", 0.5 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: New Lead; opens `ovsales` when asked for `leads`

### Billing, phone

- reached by: bar: Clients (1 tap); shot [phone](../../review/census/sales/shots/phone_billing_clients.jpg)
- **Clients** (`clients`): heading "Clients", 0.9 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: New Client
- reached by: menu › More › swipe the strip, Forecast (3 taps); shot [phone](../../review/census/sales/shots/phone_billing_forecast.jpg)
- **Forecast** (`hbforecast`): heading "Forecast", 1.4 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: none
- reached by: menu › More › swipe the strip, Sales Dashboard (3 taps); shot [phone](../../review/census/sales/shots/phone_billing_sales_dashboard.jpg)
- **Sales Dashboard** (`hbdash`): heading "Sales Dashboard", 2.0 screens tall, 7 sections (2 above the fold), 2 tab screens; blue: none
- reached by: menu › More › swipe the strip, Sales (3 taps); shot [phone](../../review/census/sales/shots/phone_billing_sales.jpg)
- **Sales** (`ovsales`): heading "Sales", 1.1 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: New Lead; runs past the edge: cut off by pr-m ($140,000 · Owner · Follow up on the prop, $260,000 · Owner · Answer the board ques)
- reached by: menu › More › swipe the strip, Partners (3 taps); shot [phone](../../review/census/sales/shots/phone_billing_partners.jpg)
- **Partners** (`partners`): heading "Partners", 0.7 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Partner
- reached by: menu › More › swipe the strip, Playbook (3 taps); shot [phone](../../review/census/sales/shots/phone_billing_playbook.jpg)
- **Playbook** (`playbook`): heading "Playbook", 4.4 screens tall, 5 sections (1 above the fold), 0 tab screens; blue: none
- reached by: Clients › link: People; shot [phone](../../review/census/sales/shots/phone_billing_people.jpg)
- **People** (`hbcontacts`): heading "People", 2.0 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: New Person; runs past the edge: cut off by pr-m (sofia.adler@example.com · Attempted to c, +1 917 555 0188 · Attempted to contact ·)
- reached by: Clients › link: Companies; shot [phone](../../review/census/sales/shots/phone_billing_companies.jpg)
- **Companies** (`hbcompanies`): heading "Companies", 0.9 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: New Company
- reached by: Sales › link: Leads 1; shot [phone](../../review/census/sales/shots/phone_billing_leads_1.jpg)
- **Sales (by the link Leads 1)** (`ovsales`): heading "Sales", 0.7 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: New Lead; opens `ovsales` when asked for `leads`

### Controller, desktop

- reached by: More › Clients (2 taps); shot [desktop](../../review/census/sales/shots/desktop_controller_clients.jpg)
- **Clients** (`clients`): heading "Clients", 0.6 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Client

### Controller, phone

- reached by: menu › More › swipe the strip, Clients (3 taps); shot [phone](../../review/census/sales/shots/phone_controller_clients.jpg)
- **Clients** (`clients`): heading "Clients", 0.8 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Client

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

