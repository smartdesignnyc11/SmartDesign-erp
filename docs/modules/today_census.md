# The Today Module, Page by Page: the Census

**Asked by Alan, 2026-10-26:** "Go through all the modules with screenshots. It's important to understand the format of every page and what's on it." The loop's experts and the client expert walk every page of their module with this in hand in round one of the improvement loop (docs/IMPROVEMENT_LOOP.md).

**What this is.** A machine inventory, not a judgment, in the format of the Projects census (`docs/modules/projects_census.md`). No app code changed. `tests/module_census.py` (its helpers `tests/module_census_js.js` sit on the projects census's reader `tests/census_js.js` and the information map's `tests/ia_js.js`) signs in as each role on a fresh app at 1440 and at 390, reads the role's running menu, and reaches each page of this module the way the person does: the phone bar, or the menu (the hamburger on the phone), the group, then the strip. It presses every tab of every tab group and the tabs those reveal, follows the page's own links to this module's pages the menu did not reach, reads every screen and shoots it. The primary role is every role; every role whose menu holds a page of this module is walked. Job-scoped pages show **121 State Street** wherever the role may open it.

**Where this module's pages sit.** The crew's first page is Clock (Time and Payroll), the driver's Route (Field and Site) and the client's Overview (the Client Portal): those three roles have no Today page. The PM, owner and coordinator open Chief of Staff from More; it is the Ask page (`pa`), the same page the Company menu calls The Brain.

**Build bd3180c27e33** (master 1cc2eb9), the one build every module census of this round ran on. 183 screens in all. Walked 2026-10-26 06:29 on the demo day (Thu 2026-09-03); the walk of every module took 54.4 minutes. Raw read: `review/census/today/data.json`. Every screen per role in tables: `review/census/today/tables.md`. Screenshots of every screen, both devices: `review/census/today/shots/` (`desktop_` or `phone_`, the role, the page, then the tab; up to 3 desktop or 5 phone screens tall). The first screen of each page is committed; the tabs stay on the machine that ran it.

Run it: `python3 build.py && cd tests && ./slot.sh python3 module_census.py --module today` (then `python3 module_census.py --report` rewrites every module's page from data.json).

## Headline

- **Owner: 3 pages with 31 more screens behind their tabs on the desktop (3 pages and 7 tab screens on the phone)**, about 10 desktop screens end to end.
- **PM (Alan): 3 pages with 26 more screens behind their tabs on the desktop (3 pages and 10 tab screens on the phone)**, about 9 desktop screens end to end.
- **Coordinator (Chen): 3 pages with 24 more screens behind their tabs on the desktop (3 pages and 8 tab screens on the phone)**, about 7 desktop screens end to end.
- **Foreman (Angel): 1 page with 0 more screens behind their tabs on the desktop (1 page and 0 tab screens on the phone)**, about 5 desktop screens end to end.
- **Designer (Sarah): 1 page with 0 more screens behind their tabs on the desktop (1 page and 0 tab screens on the phone)**, about 2 desktop screens end to end.
- **Billing: 3 pages with 13 more screens behind their tabs on the desktop (3 pages and 4 tab screens on the phone)**, about 6 desktop screens end to end.
- **Controller: 3 pages with 21 more screens behind their tabs on the desktop (3 pages and 5 tab screens on the phone)**, about 6 desktop screens end to end.
- **Pages each role reaches in this module, desktop:** Owner 3, PM 3, Coordinator 3, Foreman 1, Designer 1, Billing 3, Controller 3.
- **Reached only one way** by Owner: Approvals (desktop and phone), Chief of Staff (desktop and phone), Today (desktop) (one menu entry, not on the phone bar, and no walked page links to it; section 1).
- **Reached only one way** by PM (Alan): Approvals (desktop and phone), Chief of Staff (desktop and phone), Today (desktop) (one menu entry, not on the phone bar, and no walked page links to it; section 1).
- **Reached only one way** by Coordinator (Chen): Approvals (desktop and phone), Chief of Staff (desktop and phone), Today (desktop) (one menu entry, not on the phone bar, and no walked page links to it; section 1).
- **Reached only one way** by Foreman (Angel): Today (desktop) (one menu entry, not on the phone bar, and no walked page links to it; section 1).
- **Reached only one way** by Designer (Sarah): Today (desktop) (one menu entry, not on the phone bar, and no walked page links to it; section 1).
- **Reached only one way** by Billing: Approvals (desktop and phone), Chief of Staff (desktop and phone), Today (desktop) (one menu entry, not on the phone bar, and no walked page links to it; section 1).
- **Reached only one way** by Controller: Approvals (desktop and phone), Chief of Staff (desktop and phone), Today (desktop) (one menu entry, not on the phone bar, and no walked page links to it; section 1).
- **The same page under another module's menu** (Owner, desktop): Chief of Staff is also Company and Settings › The Brain (`pa`).
- **The same page under another module's menu** (PM, desktop): Chief of Staff is also Company and Settings › The Brain (`pa`).
- **The same page under another module's menu** (Coordinator, desktop): Chief of Staff is also Company and Settings › The Brain (`pa`).
- **The same page under another module's menu** (Controller, desktop): Chief of Staff is also Company and Settings › The Brain (`pa`).
- **51 records show on two or more of this module's pages** for Owner on the desktop (21 approvals, 5 lessons, 3 vendors, 3 leads). "WW-2026-118" is on 3: Approvals, Chief of Staff, Today.
- **3 pairs of pages list largely the same records,** led by Approvals and Chief of Staff (30 shared); Approvals and Today (23 shared); Chief of Staff and Today (15 shared).
- **The same records in other modules** (Owner, desktop): Accounting › Spend lists 33; Accounting › Banking lists 32; Accounting › Controls lists 30; Accounting › Dashboard lists 28; Purchasing › Buy Board lists 28 of the 168 records this module lists.
- **On the phone** (Owner): 2 of the 3 pages are taller than three screens (Approvals, Chief of Staff); 1 have no section heading above the fold; 0 screens scroll sideways.
- **Nothing crashed and no page raised an error**; every page opened.
- **3 screen(s) saved while the census only read and pressed tabs** (Coordinator (Chen) desktop, Chief of Staff[Activity][On Its Own]; Billing desktop, Chief of Staff[Activity][On Its Own]; Controller desktop, Chief of Staff[Activity][On Its Own]). Each role ran on a fresh app, so a save never reached the next role.

## 1. The Tree, Role by Role

**Pages** are the module's pages the role reaches from its menu (and the links those pages show). **Tabs** are the screens behind each page's tab groups, and behind the tabs those reveal. **Sections** are the headed parts of each page as it opens. Each cell reads desktop / phone.

| Role | Primary | First page of the module, reached by (desktop / phone) | Pages | Tab screens | Sections | Screens |
|---|---|---|---|---|---|---|
| Owner | yes | Today (1 tap) / bar: Today (1 tap) | 3 / 3 | 31 / 7 | 13 / 12 | 34 / 10 |
| PM (Alan) | yes | Today (1 tap) / bar: Today (1 tap) | 3 / 3 | 26 / 10 | 12 / 11 | 29 / 13 |
| Coordinator (Chen) | yes | Today (1 tap) / bar: Today (1 tap) | 3 / 3 | 24 / 8 | 12 / 11 | 27 / 11 |
| Foreman (Angel) | yes | Today (1 tap) / bar: Today (1 tap) | 1 / 1 | 0 / 0 | 9 / 9 | 1 / 1 |
| Designer (Sarah) | yes | Today (1 tap) / bar: Today (1 tap) | 1 / 1 | 0 / 0 | 8 / 8 | 1 / 1 |
| Billing | yes | Today (1 tap) / bar: Today (1 tap) | 3 / 3 | 13 / 4 | 11 / 10 | 16 / 7 |
| Controller | yes | Today (1 tap) / bar: Today (1 tap) | 3 / 3 | 21 / 5 | 13 / 12 | 24 / 8 |

### Which pages each role reaches (desktop)

Each cell is the number of screens the page has (the page and its tabs); "-" means the role does not reach it.

| Page | Owner | PM | Coordinator | Foreman | Designer | Billing | Controller |
|---|---|---|---|---|---|---|---|
| Today | 3 | 3 | 3 | 1 | 1 | 3 | 3 |
| Approvals | 5 | 8 | 6 | - | - | 2 | 3 |
| Chief of Staff | 26 | 18 | 18 | - | - | 11 | 18 |

### Owner's tree at a glance

Reached by is the taps from the role's first page, desktop then phone. Tall is in screens, desktop / phone. Sections are the headed parts as the page opens (phone above the fold). Tabs are the screens behind its tab groups, desktop / phone. "What it lists" counts the records found on the page as it opens.

| Page | Reached by (desktop / phone) | Heading | Tall | Sections (phone above the fold) | Tabs | Tiles and figures | What it lists | Blue button | First button | Shots |
|---|---|---|---|---|---|---|---|---|---|---|
| Today | Today (1 tap) / bar: Today (1 tap) | Today | 1.3 / 1.4 | 3 (1) | 2 / 2 | - | 5 to-dos, 5 approvals, 4 contacts, 3 leads | Draft the Renewal | All 34 | [desktop](../../review/census/today/shots/desktop_owner_today.jpg) [phone](../../review/census/today/shots/phone_owner_today.jpg) |
| Approvals | Today › Approvals (2 taps) / menu › Today › Approvals (3 taps) | Approvals | 5.4 / 3.2 | 1 (0) | 4 / 4 | - | 21 approvals, 5 lessons, 3 vendors, 3 bank and card lines | Approve | Everything22 | [desktop](../../review/census/today/shots/desktop_owner_approvals.jpg) [phone](../../review/census/today/shots/phone_owner_approvals.jpg) |
| Chief of Staff | More › Chief of Staff (2 taps) / menu › More › Chief of Staff (3 taps) | Chief of Staff | 3.5 / 3.5 | 9 (2) | 25 / 1 | - | 4 decisions, 1 to-dos, 1 schedule lines, 1 files | none | Chat | [desktop](../../review/census/today/shots/desktop_owner_chief_of_staff.jpg) [phone](../../review/census/today/shots/phone_owner_chief_of_staff.jpg) |

### PM (Alan)'s tree at a glance

Reached by is the taps from the role's first page, desktop then phone. Tall is in screens, desktop / phone. Sections are the headed parts as the page opens (phone above the fold). Tabs are the screens behind its tab groups, desktop / phone. "What it lists" counts the records found on the page as it opens.

| Page | Reached by (desktop / phone) | Heading | Tall | Sections (phone above the fold) | Tabs | Tiles and figures | What it lists | Blue button | First button | Shots |
|---|---|---|---|---|---|---|---|---|---|---|
| Today | Today (1 tap) / bar: Today (1 tap) | Today | 1.1 / 1.3 | 2 (1) | 2 / 2 | - | 6 to-dos, 3 decisions, 2 schedule lines, 2 site questions | Answer | All 21 | [desktop](../../review/census/today/shots/desktop_pm_today.jpg) [phone](../../review/census/today/shots/phone_pm_today.jpg) |
| Approvals | Today › Approvals (2 taps) / menu › Today › Approvals (3 taps) | Approvals | 4.0 / 2.7 | 1 (0) | 7 / 7 | - | 5 decisions, 3 approvals, 2 site questions, 2 vendors | Answer | Everything15 | [desktop](../../review/census/today/shots/desktop_pm_approvals.jpg) [phone](../../review/census/today/shots/phone_pm_approvals.jpg) |
| Chief of Staff | More › Chief of Staff (2 taps) / menu › More › swipe the strip, Chief of Staff (3 taps) | Chief of Staff | 3.5 / 3.5 | 9 (2) | 17 / 1 | - | 4 decisions, 1 to-dos, 1 schedule lines, 1 files | none | Chat | [desktop](../../review/census/today/shots/desktop_pm_chief_of_staff.jpg) [phone](../../review/census/today/shots/phone_pm_chief_of_staff.jpg) |

### Coordinator (Chen)'s tree at a glance

Reached by is the taps from the role's first page, desktop then phone. Tall is in screens, desktop / phone. Sections are the headed parts as the page opens (phone above the fold). Tabs are the screens behind its tab groups, desktop / phone. "What it lists" counts the records found on the page as it opens.

| Page | Reached by (desktop / phone) | Heading | Tall | Sections (phone above the fold) | Tabs | Tiles and figures | What it lists | Blue button | First button | Shots |
|---|---|---|---|---|---|---|---|---|---|---|
| Today | Today (1 tap) / bar: Today (1 tap) | Today | 1.1 / 1.3 | 2 (1) | 2 / 2 | - | 4 materials, 3 schedule lines, 2 approvals, 2 vendors | Chase COI | All 29 | [desktop](../../review/census/today/shots/desktop_coord_today.jpg) [phone](../../review/census/today/shots/phone_coord_today.jpg) |
| Approvals | Today › Approvals (2 taps) / menu › Today › Approvals (3 taps) | Approvals | 2.5 / 1.9 | 1 (1) | 5 / 5 | - | 6 approvals, 3 materials, 3 vendors, 2 purchase orders | Chase COI | Everything8 | [desktop](../../review/census/today/shots/desktop_coord_approvals.jpg) [phone](../../review/census/today/shots/phone_coord_approvals.jpg) |
| Chief of Staff | More › Chief of Staff (2 taps) / menu › More › swipe the strip, Chief of Staff (3 taps) | Chief of Staff | 3.5 / 3.5 | 9 (2) | 17 / 1 | - | 4 decisions, 1 to-dos, 1 schedule lines, 1 files | none | Chat | [desktop](../../review/census/today/shots/desktop_coord_chief_of_staff.jpg) [phone](../../review/census/today/shots/phone_coord_chief_of_staff.jpg) |

### Foreman (Angel)'s tree at a glance

Reached by is the taps from the role's first page, desktop then phone. Tall is in screens, desktop / phone. Sections are the headed parts as the page opens (phone above the fold). Tabs are the screens behind its tab groups, desktop / phone. "What it lists" counts the records found on the page as it opens.

| Page | Reached by (desktop / phone) | Heading | Tall | Sections (phone above the fold) | Tabs | Tiles and figures | What it lists | Blue button | First button | Shots |
|---|---|---|---|---|---|---|---|---|---|---|
| Today | Today (1 tap) / bar: Today (1 tap) | Today | 4.5 / 2.1 | 9 (1) | 0 / 0 | - | 16 schedule lines, 3 subs to confirm, 3 decisions, 2 to-dos | Clock In | Take Photo | [desktop](../../review/census/today/shots/desktop_foreman_today.jpg) [phone](../../review/census/today/shots/phone_foreman_today.jpg) |

### Designer (Sarah)'s tree at a glance

Reached by is the taps from the role's first page, desktop then phone. Tall is in screens, desktop / phone. Sections are the headed parts as the page opens (phone above the fold). Tabs are the screens behind its tab groups, desktop / phone. "What it lists" counts the records found on the page as it opens.

| Page | Reached by (desktop / phone) | Heading | Tall | Sections (phone above the fold) | Tabs | Tiles and figures | What it lists | Blue button | First button | Shots |
|---|---|---|---|---|---|---|---|---|---|---|
| Today | Today (1 tap) / bar: Today (1 tap) | Today | 2.3 / 3.5 | 8 (2) | 0 / 0 | Due Soon 1; To Re-Issue 6; Hours Not Logged 4; Waiting on Decisions 11 | 6 decisions, 6 drawing sheets, 2 schedule lines, 2 site questions | none | Due Soon 1 Exposed-beam ceil | [desktop](../../review/census/today/shots/desktop_designer_today.jpg) [phone](../../review/census/today/shots/phone_designer_today.jpg) |

### Billing's tree at a glance

Reached by is the taps from the role's first page, desktop then phone. Tall is in screens, desktop / phone. Sections are the headed parts as the page opens (phone above the fold). Tabs are the screens behind its tab groups, desktop / phone. "What it lists" counts the records found on the page as it opens.

| Page | Reached by (desktop / phone) | Heading | Tall | Sections (phone above the fold) | Tabs | Tiles and figures | What it lists | Blue button | First button | Shots |
|---|---|---|---|---|---|---|---|---|---|---|
| Today | Today (1 tap) / bar: Today (1 tap) | Today | 0.9 / 1.1 | 1 (0) | 2 / 2 | - | 4 approvals, 3 findings, 1 mail, 1 clients | Resolve, $16, | All 5 | [desktop](../../review/census/today/shots/desktop_billing_today.jpg) [phone](../../review/census/today/shots/phone_billing_today.jpg) |
| Approvals | Today › Approvals (2 taps) / menu › Today › Approvals (3 taps) | Approvals | 1.7 / 1.7 | 1 (1) | 1 / 1 | - | 4 approvals, 3 findings, 1 materials, 1 COI lapses | Resolve | Everything4 | [desktop](../../review/census/today/shots/desktop_billing_approvals.jpg) [phone](../../review/census/today/shots/phone_billing_approvals.jpg) |
| Chief of Staff | More › Chief of Staff (2 taps) / menu › More › swipe the strip, Chief of Staff (3 taps) | Chief of Staff | 3.5 / 3.5 | 9 (2) | 10 / 1 | - | 4 decisions, 1 to-dos, 1 schedule lines, 1 files | none | Chat | [desktop](../../review/census/today/shots/desktop_billing_chief_of_staff.jpg) [phone](../../review/census/today/shots/phone_billing_chief_of_staff.jpg) |

### Controller's tree at a glance

Reached by is the taps from the role's first page, desktop then phone. Tall is in screens, desktop / phone. Sections are the headed parts as the page opens (phone above the fold). Tabs are the screens behind its tab groups, desktop / phone. "What it lists" counts the records found on the page as it opens.

| Page | Reached by (desktop / phone) | Heading | Tall | Sections (phone above the fold) | Tabs | Tiles and figures | What it lists | Blue button | First button | Shots |
|---|---|---|---|---|---|---|---|---|---|---|
| Today | Today (1 tap) / bar: Today (1 tap) | Today | 1.0 / 1.4 | 3 (1) | 2 / 2 | - | 4 purchase orders, 4 approvals, 4 files, 3 vendors | Enter the Bill, $2, | All 6 | [desktop](../../review/census/today/shots/desktop_controller_today.jpg) [phone](../../review/census/today/shots/phone_controller_today.jpg) |
| Approvals | Today › Approvals (2 taps) / menu › Today › Approvals (3 taps) | Approvals | 1.6 / 1.7 | 1 (1) | 2 / 2 | - | 4 purchase orders, 4 approvals, 4 files, 3 vendors | Open | Everything4 | [desktop](../../review/census/today/shots/desktop_controller_approvals.jpg) [phone](../../review/census/today/shots/phone_controller_approvals.jpg) |
| Chief of Staff | More › Chief of Staff (2 taps) / menu › More › swipe the strip, Chief of Staff (3 taps) | Chief of Staff | 3.5 / 3.5 | 9 (2) | 17 / 1 | - | 4 decisions, 1 to-dos, 1 schedule lines, 1 files | none | Chat | [desktop](../../review/census/today/shots/desktop_controller_chief_of_staff.jpg) [phone](../../review/census/today/shots/phone_controller_chief_of_staff.jpg) |

### How each page is reached, and the pages reached only one way

Menu places are the role's menu entries that open the page (a page in two groups has two). The phone bar counts as one more way in on the phone (its pages are in the menu too). Links are the walked pages, in any module, that show a link to it. **One way** means one menu place and nothing else: lose that entry and the page is lost.

| Role | Device | Page | Menu places | Phone bar | Linked from | Ways in |
|---|---|---|---|---|---|---|
| Owner | desktop | Today | Today | - | - | 1 (one way) |
| Owner | desktop | Approvals | Today › Approvals | - | - | 1 (one way) |
| Owner | desktop | Chief of Staff | More › Chief of Staff | - | - | 1 (one way) |
| Owner | phone | Today | Today | yes | - | 2 |
| Owner | phone | Approvals | Today › Approvals | - | - | 1 (one way) |
| Owner | phone | Chief of Staff | More › Chief of Staff | - | - | 1 (one way) |
| PM (Alan) | desktop | Today | Today | - | - | 1 (one way) |
| PM (Alan) | desktop | Approvals | Today › Approvals | - | - | 1 (one way) |
| PM (Alan) | desktop | Chief of Staff | More › Chief of Staff | - | - | 1 (one way) |
| PM (Alan) | phone | Today | Today | yes | - | 2 |
| PM (Alan) | phone | Approvals | Today › Approvals | - | - | 1 (one way) |
| PM (Alan) | phone | Chief of Staff | More › Chief of Staff | - | - | 1 (one way) |
| Coordinator (Chen) | desktop | Today | Today | - | - | 1 (one way) |
| Coordinator (Chen) | desktop | Approvals | Today › Approvals | - | - | 1 (one way) |
| Coordinator (Chen) | desktop | Chief of Staff | More › Chief of Staff | - | - | 1 (one way) |
| Coordinator (Chen) | phone | Today | Today | yes | - | 2 |
| Coordinator (Chen) | phone | Approvals | Today › Approvals | - | - | 1 (one way) |
| Coordinator (Chen) | phone | Chief of Staff | More › Chief of Staff | - | - | 1 (one way) |
| Foreman (Angel) | desktop | Today | Today | - | - | 1 (one way) |
| Foreman (Angel) | phone | Today | Today | yes | - | 2 |
| Designer (Sarah) | desktop | Today | Today | - | - | 1 (one way) |
| Designer (Sarah) | phone | Today | Today | yes | - | 2 |
| Billing | desktop | Today | Today | - | - | 1 (one way) |
| Billing | desktop | Approvals | Today › Approvals | - | - | 1 (one way) |
| Billing | desktop | Chief of Staff | More › Chief of Staff | - | - | 1 (one way) |
| Billing | phone | Today | Today | yes | - | 2 |
| Billing | phone | Approvals | Today › Approvals | - | - | 1 (one way) |
| Billing | phone | Chief of Staff | More › Chief of Staff | - | - | 1 (one way) |
| Controller | desktop | Today | Today | - | - | 1 (one way) |
| Controller | desktop | Approvals | Today › Approvals | - | - | 1 (one way) |
| Controller | desktop | Chief of Staff | More › Chief of Staff | - | - | 1 (one way) |
| Controller | phone | Today | Today | yes | - | 2 |
| Controller | phone | Approvals | Today › Approvals | - | - | 1 (one way) |
| Controller | phone | Chief of Staff | More › Chief of Staff | - | - | 1 (one way) |

**Pages of this module the role may open (ROLE_VIEWS) that no menu entry of this module or walked link reached.** Where the census landed on the page from another module (a tab that leaves, another group's entry), that place is named; "not reached" means no walked screen showed it, which for most is a retired page that lands on another (MN_ALIAS, OC_RETIRED) and is left to search and old links.

- Owner, desktop: `comms` (reached as Tasks and Messages › Messages)
- Owner, phone: `comms` (reached as Tasks and Messages › Messages)
- PM (Alan), desktop: `comms` (reached as Tasks and Messages › Messages)
- PM (Alan), phone: `comms` (reached as Tasks and Messages › Messages)
- Coordinator (Chen), desktop: `comms` (reached as Tasks and Messages › Messages)
- Coordinator (Chen), phone: `comms` (reached as Tasks and Messages › Messages)
- Designer (Sarah), desktop: `comms` (reached as Tasks and Messages › Messages)
- Designer (Sarah), phone: `comms` (reached as Tasks and Messages › Messages)
- Billing, desktop: `comms` (reached as Tasks and Messages › Messages)
- Billing, phone: `comms` (reached as Tasks and Messages › Messages)
- Controller, desktop: `comms` (reached as Tasks and Messages › Messages)
- Controller, phone: `comms` (reached as Tasks and Messages › Messages)

## 2. Where the Data Lives, and Where It Shows Twice

Records are found by their own words (the information map's catalog, the job's nouns and this census's: clients, vendors, leads, contacts, companies, every invoice, bill and PO, payroll runs, stock, meetings, journals, obligations, lessons, partners, bank lines, threads), so these are floors. A page's tabs count as the page.

### Owner, desktop: each kind of record, and the pages that list it

| Records | Found | Pages that list them (how many each) | Also in other modules |
|---|---|---|---|
| approvals | 27 | 3: Approvals 21, Today 17, Chief of Staff 17 | Company and Settings › Company 3, Tasks and Messages › Meetings 3 |
| bills | 2 | 3: Chief of Staff 2, Today 1, Approvals 1 | Accounting › Spend 2, Accounting › Bills & Payroll 2, Accounting › Ledger 2, Accounting › Dashboard 1 |
| schedule lines | 4 | 3: Chief of Staff 3, Today 1, Approvals 1 | Company and Settings › Company Settings 4, Accounting › Reports 4, Tasks and Messages › Tasks 3, Accounting › Dashboard 3 |
| purchase orders | 4 | 3: Chief of Staff 4, Approvals 2, Today 1 | Purchasing › Orders 4, Company and Settings › Company Settings 3, Accounting › Reports 3, Projects › Job Page 2 |
| vendors | 8 | 3: Chief of Staff 8, Approvals 3, Today 1 | Purchasing › Vendors 8, Accounting › Banking 7, Accounting › Dashboard 7, Accounting › Ledger 6 |
| files | 4 | 3: Chief of Staff 4, Approvals 2, Today 1 | Purchasing › Orders 4, Accounting › Reports 3, Company and Settings › Company Settings 3, Purchasing › Vendors 2 |
| findings | 14 | 3: Chief of Staff 14, Today 2, Approvals 2 | - |
| COI lapses | 2 | 3: Approvals 2, Chief of Staff 2, Today 1 | Accounting › Dashboard 2, Accounting › Reports 1, Purchasing › Vendors 1, Company and Settings › Obligations 1 |
| to-dos | 7 | 2: Today 5, Chief of Staff 4 | Tasks and Messages › Tasks 7 |
| contacts | 6 | 2: Chief of Staff 5, Today 4 | Sales and Clients › People 7, Sales and Clients › Clients 7, Sales and Clients › Companies 7, Sales and Clients › Sales 5 |
| leads | 5 | 2: Chief of Staff 5, Today 3 | Sales and Clients › People 5, Sales and Clients › Clients 5, Sales and Clients › Companies 5, Sales and Clients › Sales 5 |
| site questions | 3 | 2: Chief of Staff 3, Approvals 1 | Projects › Field 3 |
| lessons | 8 | 2: Chief of Staff 8, Approvals 5 | - |
| bank and card lines | 25 | 2: Chief of Staff 25, Approvals 3 | Accounting › Spend 25, Accounting › Banking 25, Accounting › Ledger 25, Accounting › Controls 25 |
| mail | 1 | 1: Today 1 | Tasks and Messages › Messages 1 |
| subs to confirm | 1 | 1: Approvals 1 | Accounting › Banking 1, Accounting › Controls 1 |
| money flags | 32 | 1: Chief of Staff 32 | - |
| field requests | 2 | 1: Chief of Staff 2 | Projects › Job Page 2, Purchasing › Buy Board 2, Field and Site › Route 2, Field and Site › Requests 2 |
| materials | 21 | 1: Chief of Staff 21 | Purchasing › Buy Board 21, Accounting › Dashboard 12, Projects › Job Page 12, Accounting › Reports 9 |
| obligations | 2 | 1: Chief of Staff 2 | Tasks and Messages › Tasks 2, Company and Settings › Obligations 2, Company and Settings › Calendar 1, Company and Settings › Company 1 |
| submittals | 2 | 1: Chief of Staff 2 | Projects › Submittals 2, Accounting › Reports 2, Projects › Documents 1 |
| decisions | 4 | 1: Chief of Staff 4 | Accounting › Dashboard 4, Projects › Decisions 3, Projects › Job Page 3, Design › Project Board 3 |
| clients | 3 | 1: Chief of Staff 3 | Sales and Clients › Companies 3, Sales and Clients › People 3, Sales and Clients › Clients 3, Design › Design 2 |
| inspections | 1 | 1: Chief of Staff 1 | Projects › Permits 1, Projects › Job Page 1 |
| meetings | 2 | 1: Chief of Staff 2 | Company and Settings › Company Settings 2, Company and Settings › Company 2, Tasks and Messages › Meetings 2 |

### Records on two or more pages, and lists that are the same list twice

**Owner, desktop:** 51 records on two or more pages: approvals 21 (up to 3 pages); lessons 5 (up to 2 pages); vendors 3 (up to 3 pages); leads 3 (up to 2 pages); contacts 3 (up to 2 pages); bank and card lines 3 (up to 2 pages); to-dos 2 (up to 2 pages); findings 2 (up to 3 pages); files 2 (up to 3 pages); purchase orders 2 (up to 3 pages); COI lapses 2 (up to 3 pages); bills 1 (up to 3 pages); schedule lines 1 (up to 2 pages); site questions 1 (up to 2 pages).

- "WW-2026-118" (bills) on 3 pages: Approvals, Chief of Staff, Today
- "Renew LLC biennial statement by 8/29" (approvals) on 3 pages: Approvals, Chief of Staff, Today
- "Not in the budget: Roll Off Dumpster" (approvals) on 3 pages: Approvals, Chief of Staff, Today
- "A step carried twice becomes a dated task with an owner" (approvals) on 3 pages: Approvals, Chief of Staff, Today
- "Renew LLC biennial statement by 8/29" (findings) on 3 pages: Approvals, Chief of Staff, Today
- "Not in the budget: Roll Off Dumpster" (findings) on 3 pages: Approvals, Chief of Staff, Today
- the same list twice (3 or more shared records, at least half of the shorter list): Approvals and Chief of Staff (30 shared, of 41 and 152: approvals, lessons, bank and card lines); Approvals and Today (23 shared, of 41 and 30: approvals, findings, bills); Chief of Staff and Today (15 shared, of 152 and 30: approvals, findings, to-dos)

**PM (Alan), desktop:** 13 records on two or more pages: decisions 3 (up to 3 pages); vendors 3 (up to 2 pages); site questions 2 (up to 3 pages); schedule lines 1 (up to 3 pages); COI lapses 1 (up to 2 pages); files 1 (up to 2 pages); purchase orders 1 (up to 2 pages); meetings 1 (up to 2 pages).

- "Restoration" (schedule lines) on 3 pages: Approvals, Chief of Staff, Today
- "Garden bedroom framing layout" (decisions) on 3 pages: Approvals, Chief of Staff, Today
- "Laundry layout with new washer/dryer sizes" (decisions) on 3 pages: Approvals, Chief of Staff, Today
- "3rd floor paint colors and sheen" (decisions) on 3 pages: Approvals, Chief of Staff, Today
- "Restoration crew (Tomas) did not show today" (site questions) on 3 pages: Approvals, Chief of Staff, Today
- "Exposed-beam ceiling — 3" drop or 2"? Satish needs it to set" (site questions) on 2 pages: Approvals, Today
- the same list twice (3 or more shared records, at least half of the shorter list): Approvals and Chief of Staff (9 shared, of 16 and 127: decisions, meetings, COI lapses)

**Coordinator (Chen), desktop:** 35 records on two or more pages: materials 18 (up to 3 pages); vendors 4 (up to 3 pages); approvals 3 (up to 3 pages); purchase orders 2 (up to 2 pages); files 2 (up to 2 pages); to-dos 1 (up to 2 pages); schedule lines 1 (up to 2 pages); field requests 1 (up to 3 pages); site questions 1 (up to 2 pages); COI lapses 1 (up to 3 pages); meetings 1 (up to 2 pages).

- "2x4x8 KD studs" (field requests) on 3 pages: Approvals, Chief of Staff, Today
- "Insulation" (materials) on 3 pages: Approvals, Chief of Staff, Today
- "40 ea 2x4x8 KD studs" (materials) on 3 pages: Approvals, Chief of Staff, Today
- "Window Works" (COI lapses) on 3 pages: Approvals, Chief of Staff, Today
- "Window Works — COI expired 8/15" (approvals) on 3 pages: Approvals, Chief of Staff, Today
- "Approve Alex's route" (approvals) on 3 pages: Approvals, Chief of Staff, Today
- the same list twice (3 or more shared records, at least half of the shorter list): Chief of Staff and Today (22 shared, of 99 and 28: materials, approvals, to-dos); Approvals and Chief of Staff (13 shared, of 18 and 99: materials, approvals, files)

**Billing, desktop:** 11 records on two or more pages: approvals 4 (up to 3 pages); findings 3 (up to 3 pages); clients 1 (up to 3 pages); files 1 (up to 2 pages); vendors 1 (up to 2 pages); purchase orders 1 (up to 2 pages).

- "Resolve: Rivera family $16,350 recorded Fri, Aug 14, not in " (approvals) on 3 pages: Approvals, Chief of Staff, Today
- "Resolve: Rivera family $5,000 recorded Thu, Jul 30, not in t" (approvals) on 3 pages: Approvals, Chief of Staff, Today
- "Billed ahead: 121 State Street, $66,470 on 7 lines" (approvals) on 3 pages: Approvals, Chief of Staff, Today
- "Bill the stored materials: 121 State Street · Windows — fron" (approvals) on 3 pages: Approvals, Chief of Staff, Today
- "Resolve: Rivera family $16,350 recorded Fri, Aug 14, not in " (findings) on 3 pages: Approvals, Chief of Staff, Today
- "Resolve: Rivera family $5,000 recorded Thu, Jul 30, not in t" (findings) on 3 pages: Approvals, Chief of Staff, Today
- the same list twice (3 or more shared records, at least half of the shorter list): Approvals and Chief of Staff (9 shared, of 11 and 55: approvals, findings, files); Approvals and Today (7 shared, of 11 and 8: approvals, findings); Chief of Staff and Today (7 shared, of 55 and 8: approvals, findings)

**Controller, desktop:** 20 records on two or more pages: purchase orders 4 (up to 3 pages); approvals 4 (up to 3 pages); files 4 (up to 3 pages); vendors 4 (up to 3 pages); COI lapses 2 (up to 2 pages); findings 1 (up to 3 pages); money flags 1 (up to 2 pages).

- "PO-2026-047" (purchase orders) on 3 pages: Approvals, Chief of Staff, Today
- "Chase Business Checking: Fri, Jul 31 not reconciled" (approvals) on 3 pages: Approvals, Chief of Staff, Today
- "Nemo Tile says $2,140 is owed by SmartDesign Group LLC · #88" (approvals) on 3 pages: Approvals, Chief of Staff, Today
- "Purchase tax corrected on 3 orders" (approvals) on 3 pages: Approvals, Chief of Staff, Today
- "Chase Business Checking: Fri, Jul 31 not reconciled" (findings) on 3 pages: Approvals, Chief of Staff, Today
- "PO-2026-044 — Window Works.pdf" (files) on 3 pages: Approvals, Chief of Staff, Today
- the same list twice (3 or more shared records, at least half of the shorter list): Approvals and Today (13 shared, of 14 and 17: files, approvals, purchase orders); Chief of Staff and Today (10 shared, of 151 and 17: approvals, purchase orders, files); Approvals and Chief of Staff (9 shared, of 14 and 151: approvals, purchase orders, files)

**Owner, phone:** 24 records on two or more pages: approvals 17 (up to 2 pages); findings 2 (up to 2 pages); bills 1 (up to 2 pages); files 1 (up to 3 pages); vendors 1 (up to 3 pages); purchase orders 1 (up to 3 pages); COI lapses 1 (up to 3 pages).

- "PO-2026-044 — Window Works.pdf" (files) on 3 pages: Approvals, Chief of Staff, Today
- "Window Works" (vendors) on 3 pages: Approvals, Chief of Staff, Today
- "PO-2026-044" (purchase orders) on 3 pages: Approvals, Chief of Staff, Today
- "Window Works" (COI lapses) on 3 pages: Approvals, Chief of Staff, Today
- "WW-2026-118" (bills) on 2 pages: Approvals, Today
- "Renew LLC biennial statement by 8/29" (approvals) on 2 pages: Approvals, Today
- the same list twice (3 or more shared records, at least half of the shorter list): Approvals and Today (23 shared, of 41 and 28: approvals, findings, bills)

**PM (Alan), phone:** 9 records on two or more pages: decisions 3 (up to 3 pages); vendors 2 (up to 2 pages); schedule lines 1 (up to 2 pages); site questions 1 (up to 2 pages); files 1 (up to 2 pages); purchase orders 1 (up to 2 pages).

- "Garden bedroom framing layout" (decisions) on 3 pages: Approvals, Chief of Staff, Today
- "Laundry layout with new washer/dryer sizes" (decisions) on 3 pages: Approvals, Chief of Staff, Today
- "3rd floor paint colors and sheen" (decisions) on 3 pages: Approvals, Chief of Staff, Today
- "Restoration" (schedule lines) on 2 pages: Approvals, Today
- "Restoration crew (Tomas) did not show today" (site questions) on 2 pages: Approvals, Today
- "PO-2026-044 — Window Works.pdf" (files) on 2 pages: Approvals, Chief of Staff
- the same list twice (3 or more shared records, at least half of the shorter list): Approvals and Chief of Staff (5 shared, of 16 and 7: decisions, files, purchase orders); Approvals and Today (5 shared, of 16 and 10: decisions, site questions, schedule lines)

**Coordinator (Chen), phone:** 11 records on two or more pages: materials 2 (up to 3 pages); approvals 2 (up to 2 pages); vendors 2 (up to 3 pages); to-dos 1 (up to 2 pages); field requests 1 (up to 3 pages); COI lapses 1 (up to 2 pages); files 1 (up to 2 pages); purchase orders 1 (up to 2 pages).

- "2x4x8 KD studs" (field requests) on 3 pages: Approvals, Chief of Staff, Today
- "40 ea 2x4x8 KD studs" (materials) on 3 pages: Approvals, Chief of Staff, Today
- "Window Works" (vendors) on 3 pages: Approvals, Chief of Staff, Today
- "Shop drawings for the parlor bookcases" (to-dos) on 2 pages: Chief of Staff, Today
- "Window Works" (COI lapses) on 2 pages: Approvals, Today
- "Window Works — COI expired 8/15" (approvals) on 2 pages: Approvals, Today
- the same list twice (3 or more shared records, at least half of the shorter list): Approvals and Chief of Staff (6 shared, of 18 and 11: materials, field requests, purchase orders)

**Billing, phone:** 5 records on two or more pages: approvals 1 (up to 2 pages); clients 1 (up to 3 pages); files 1 (up to 2 pages); vendors 1 (up to 2 pages); purchase orders 1 (up to 2 pages).

- "Rivera family" (clients) on 3 pages: Approvals, Chief of Staff, Today
- "Billed ahead: 121 State Street, $66,470 on 7 lines" (approvals) on 2 pages: Chief of Staff, Today
- "PO-2026-044 — Window Works.pdf" (files) on 2 pages: Approvals, Chief of Staff
- "Window Works" (vendors) on 2 pages: Approvals, Chief of Staff
- "PO-2026-044" (purchase orders) on 2 pages: Approvals, Chief of Staff

**Controller, phone:** 16 records on two or more pages: purchase orders 4 (up to 3 pages); approvals 4 (up to 3 pages); files 4 (up to 3 pages); vendors 3 (up to 3 pages); findings 1 (up to 3 pages).

- "Chase Business Checking: Fri, Jul 31 not reconciled" (approvals) on 3 pages: Approvals, Chief of Staff, Today
- "Nemo Tile says $2,140 is owed by SmartDesign Group LLC · #88" (approvals) on 3 pages: Approvals, Chief of Staff, Today
- "Purchase tax corrected on 3 orders" (approvals) on 3 pages: Approvals, Chief of Staff, Today
- "Chase Business Checking: Fri, Jul 31 not reconciled" (findings) on 3 pages: Approvals, Chief of Staff, Today
- "PO-2026-044 — Window Works.pdf" (files) on 3 pages: Approvals, Chief of Staff, Today
- "Nemo Tile" (vendors) on 3 pages: Approvals, Chief of Staff, Today
- the same list twice (3 or more shared records, at least half of the shorter list): Approvals and Today (13 shared, of 14 and 17: approvals, purchase orders, files); Approvals and Chief of Staff (6 shared, of 14 and 11: approvals, findings, files); Chief of Staff and Today (6 shared, of 11 and 17: approvals, findings, files)

### The same records in other modules

For each role on the desktop: the pages of other modules (the Projects census's 121 State Street pages included) that list records this module lists, with how many.

- **Owner** (168 records here): Accounting › Spend 33; Accounting › Banking 32; Accounting › Controls 30; Accounting › Dashboard 28; Purchasing › Buy Board 28; Accounting › Ledger 28; Accounting › Reports 24; Projects › Job Page 23
- **PM (Alan)** (143 records here): Accounting › Dashboard 32; Projects › Job Page 29; Purchasing › Buy Board 23; Accounting › Reports 22; Company and Settings › Company Settings 18; Tasks and Messages › Tasks 17; Company and Settings › Calendar 11; Projects › Tasks 11
- **Coordinator (Chen)** (108 records here): Purchasing › Buy Board 26; Projects › Job Page 23; Accounting › Dashboard 21; Purchasing › Orders 13; Tasks and Messages › Tasks 10; Projects › Materials 7; Projects › Field 6; Field and Site › Requests 6
- **Foreman (Angel)** (27 records here): Field and Site › Site 10; Field and Site › Schedule 10; Field and Site › Daily Log 9; Field and Site › Requests 3; Company and Settings › The SmartDesign Standard 2; Field and Site › Raise 2; Tasks and Messages › Messages 2; Field and Site › Photos 2
- **Designer (Sarah)** (19 records here): Projects › Decisions 8; Design › Project Board 7; Accounting › Dashboard 6; Tasks and Messages › Tasks 5; Projects › Tasks 4; Projects › Schedule 1; Design › Design 1
- **Billing** (58 records here): Accounting › Dashboard 8; Accounting › Spend 8; Accounting › Banking 8; Accounting › Reports 7; Tasks and Messages › Tasks 5; Tasks and Messages › Meetings 3; Projects › Job Page 3; Billing › Billing 2
- **Controller** (158 records here): Accounting › Spend 33; Accounting › Banking 31; Accounting › Controls 31; Accounting › Ledger 29; Accounting › Reports 13; Accounting › Dashboard 11; Purchasing › Orders 9; Tasks and Messages › Tasks 7

Names (clients, vendors, leads, contacts, companies, partners) are left out here: a page that writes a name counts as listing it. A page that is the same page as one of this module's (one view under two menus) is left out too and listed next.

### The same page under two modules' menus

- Owner: Chief of Staff here is also Company and Settings › The Brain (`pa`)
- PM (Alan): Chief of Staff here is also Company and Settings › The Brain (`pa`)
- Coordinator (Chen): Chief of Staff here is also Company and Settings › The Brain (`pa`)
- Controller: Chief of Staff here is also Company and Settings › The Brain (`pa`)

## 3. One Label, Different Numbers

The same label (a tile, a figure, a tab or section count) with numbers that share no value on two pages, for one role. Some are right about different scopes ("Open" against "All", one job against every job); the person still reads one word with two numbers. Each needs a person to judge.

Inside the module: none found.

Against other modules, Owner, desktop: none found.

Against other modules, PM (Alan), desktop: none found.

Against other modules, Coordinator (Chen), desktop: none found.

Against other modules, Foreman (Angel), desktop: none found.

Against other modules, Designer (Sarah), desktop: none found.

Against other modules, Billing, desktop: none found.

Against other modules, Controller, desktop: none found.

Against other modules, Client (Klein), desktop: none found.

Against other modules, Crew (Alberto), desktop: none found.

Against other modules, Driver (Alex), desktop: none found.

## 4. Empty, Dead and Broken Screens

| Device | Role | Screen | What |
|---|---|---|---|
| desktop | Owner | Chief of Staff | opens pa when asked for cos |
| desktop | PM (Alan) | Chief of Staff | opens pa when asked for cos |
| desktop | Coordinator (Chen) | Chief of Staff | opens pa when asked for cos |
| desktop | Coordinator (Chen) | Chief of Staff[Activity][On Its Own] | 1 save(s) while reading |
| desktop | Billing | Chief of Staff | opens pa when asked for cos |
| desktop | Billing | Chief of Staff[Activity][On Its Own] | 1 save(s) while reading |
| desktop | Controller | Chief of Staff | opens pa when asked for cos |
| desktop | Controller | Chief of Staff[Activity][On Its Own] | 1 save(s) while reading |
| phone | Owner | Chief of Staff | opens pa when asked for cos |
| phone | PM (Alan) | Chief of Staff | opens pa when asked for cos |
| phone | Coordinator (Chen) | Chief of Staff | opens pa when asked for cos |
| phone | Billing | Chief of Staff | opens pa when asked for cos |
| phone | Controller | Chief of Staff | opens pa when asked for cos |

## 5. The Phone at 390

"Cut off" is text the phone ends early; "scrolls inside" is a strip of tiles or tabs the person swipes sideways inside the page (the page itself does not move). "Strip swipe" counts pages whose strip entry sits off screen until the strip is swiped. Pages taller than 3 phone screens are listed with their height.

| Role | Screens | The page scrolls sideways | Text cut off at the edge | Strips that scroll inside the page | Strip swipe | Pages taller than 3 screens |
|---|---|---|---|---|---|---|
| Owner | 10 | 0 | 1: Approvals | 1: Approvals | 0 | 2: Approvals 3.2, Chief of Staff 3.5 |
| PM (Alan) | 13 | 0 | 1: Approvals | 1: Approvals | 1: Chief of Staff | 1: Chief of Staff 3.5 |
| Coordinator (Chen) | 11 | 0 | 1: Approvals | 1: Approvals | 1: Chief of Staff | 1: Chief of Staff 3.5 |
| Foreman (Angel) | 1 | 0 | 0 | 0 | 0 | 0 |
| Designer (Sarah) | 1 | 0 | 0 | 1: Today | 0 | 1: Today 3.5 |
| Billing | 7 | 0 | 1: Approvals | 1: Approvals | 1: Chief of Staff | 1: Chief of Staff 3.5 |
| Controller | 8 | 0 | 1: Approvals | 1: Approvals | 1: Chief of Staff | 1: Chief of Staff 3.5 |

## 6. Page by Page, in Full

Every page the primary role reaches, as it opens, then each of its tabs. Heights are in screens of that device (900px desktop, 844px phone); "above the fold" is above the bottom bar on the phone.

### Owner, desktop

- reached by: Today (1 tap); first button "All 34"; shot [desktop](../../review/census/today/shots/desktop_owner_today.jpg)
- **Today** (`home`): heading "Today", 1.3 screens tall, 3 sections (2 above the fold), 2 tab screens; blue: Draft the Renewal
  - lead: "Everything that needs you today, in the order it matters."
  - sections: NOW; APPROVALS; THIS WEEK
  - records: 5 to-dos, 5 approvals, 4 contacts, 3 leads, 2 findings, 1 bills, 1 files, 1 vendors
  - tab groups: All 34 / Late 6 / Approvals 22
  - tab **Late**: heading "Today", 1 sections; 3 approvals, 2 to-dos, 2 leads, 2 contacts
  - tab **Approvals**: heading "Today", 2 sections; 17 approvals, 2 findings, 1 bills, 1 files
- reached by: Today › Approvals (2 taps); first button "Everything22"; shot [desktop](../../review/census/today/shots/desktop_owner_approvals.jpg)
- **Approvals** (`mapprove`): heading "Approvals", 5.4 screens tall, 1 sections (0 above the fold), 4 tab screens; blue: Approve
  - lead: "Every yes or no that is waiting on you — bills, hours, questions from the site, decisions we owe. Approve here; open the record when you need the detail."
  - sections: Also on Your List (22)
  - records: 21 approvals, 5 lessons, 3 vendors, 3 bank and card lines, 2 COI lapses, 2 findings, 1 schedule lines, 1 site questions
  - tab groups: Everything 22 / Bills 1 / Changes 3 / Lessons 6 / Other 12 / 17.1 h with no flags
  - tab **Bills**: heading "Approvals", 1 sections; 1 COI lapses, 1 bills, 1 vendors
  - tab **Changes**: heading "Approvals", 1 sections; 3 approvals, 1 COI lapses, 1 files, 1 vendors
  - tab **Lessons**: heading "Approvals", 1 sections; 6 approvals, 5 lessons, 1 subs to confirm, 1 COI lapses
  - tab **Other**: heading "Approvals", 1 sections; 13 approvals, 3 vendors, 3 bank and card lines, 2 COI lapses
  - tabs that would not press (the row changed once one was pressed): 17.1 h with no flags
- reached by: More › Chief of Staff (2 taps); first button "Chat"; shot [desktop](../../review/census/today/shots/desktop_owner_chief_of_staff.jpg)
- **Chief of Staff** (`pa`): heading "Chief of Staff", 3.5 screens tall, 9 sections (2 above the fold), 25 tab screens; blue: none; opens `pa` when asked for `cos`
  - lead: "What I caught for you, most important first by the Standard, each with the reason and the value behind it."
  - sections: Chief of Staff; ACCOUNTING; COMMITMENTS; PROMISES; OBLIGATIONS; PEOPLE; You Asked Me to Remember (0); What I Have Done (0); The 17 checks, and what each one asks
  - records: 4 decisions, 1 to-dos, 1 schedule lines, 1 files, 1 vendors, 1 purchase orders, 1 obligations
  - columns: The 17 checks, and what each one asks: Chain, Check, The Rule, Found (17 rows)
  - empty states: "No new order should go out and no bill should be approved until a current certificate arrives."; "None of it is waiting on anybody else, so it needs a hand or a date moved."; "Nothing yet. Tell me above and I will hold it."; "Nothing yet. Every button I press lands here with the reason."
  - tab groups: Chat / Findings 38 / Activity / Brain Settings; For You / Checklist / Every Chain
  - tab **Chat**: heading "Ask", 1 sections; 2 vendors, 1 to-dos, 1 schedule lines, 1 COI lapses
  - tab **Activity**: heading "Ask", 4 sections
  - tab **Activity › On Its Own**: heading "Ask", 4 sections
  - tab **Activity › Proposed**: heading "Ask", 4 sections
  - tab **Activity › Decided**: heading "Ask", 4 sections
  - tab **Activity › Handed to You**: heading "Ask", 4 sections
  - tab **Activity › Act Alone**: heading "Ask", 4 sections
  - tab **Activity › Hand It to Me**: heading "Ask", 4 sections
  - tab **Brain Settings**: heading "The Brain", 6 sections; 5 vendors, 4 approvals, 4 bank and card lines, 2 schedule lines
  - tab **Brain Settings › Lessons**: heading "The Brain", 5 sections; 8 lessons, 5 approvals, 5 vendors, 4 bank and card lines
  - tab **Brain Settings › Proposed**: heading "The Brain", 3 sections; 6 approvals, 5 lessons
  - tab **Brain Settings › Workload**: heading "The Brain", 4 sections
  - tab **Brain Settings › Hands**: heading "The Brain", 4 sections
  - tab **Brain Settings › Watching**: heading "The Brain", 3 sections; 1 materials
  - tab **Brain Settings › Plugins**: heading "The Brain", 3 sections
  - tab **For You**: heading "Ask", 1 sections; 22 money flags, 3 vendors, 3 to-dos, 3 bank and card lines
  - tab **For You › Caught**: heading "Ask", 1 sections; 22 money flags, 3 vendors, 3 to-dos, 3 bank and card lines
  - tab **For You › Waiting for You**: heading "Ask", 1 sections; 2 COI lapses, 2 vendors, 1 decisions, 1 bills
  - tab **Checklist**: heading "Ask", 13 sections; 14 findings, 6 money flags, 4 leads, 4 contacts
  - tab **Checklist › Controller**: heading "Ask", 8 sections; 24 bank and card lines, 20 money flags, 6 vendors, 4 approvals
  - tab **Checklist › PM**: heading "Ask", 4 sections; 19 materials, 4 decisions, 3 to-dos, 3 vendors
  - tab **Checklist › Procurement**: heading "Ask", 4 sections; 19 materials, 7 vendors, 4 purchase orders, 4 files
  - tab **Checklist › Billing**: heading "Ask", 2 sections; 5 money flags, 3 approvals, 1 clients
  - tab **Checklist › Designer**: heading "Ask", 3 sections; 4 decisions
  - tab **Checklist › Foreman**: heading "Ask", 3 sections; 3 materials, 3 site questions, 2 field requests, 1 schedule lines

### Owner, phone

- reached by: bar: Today (1 tap); first button "All 34"; shot [phone](../../review/census/today/shots/phone_owner_today.jpg)
- **Today** (`home`): heading "Now", 1.4 screens tall, 2 sections (1 above the fold), 2 tab screens; blue: Draft the Renewal
  - lead: "Everything that needs you today, in the order it matters."
  - sections: APPROVALS; THIS WEEK
  - records: 4 approvals, 2 findings, 1 to-dos, 1 bills, 1 files, 1 vendors, 1 purchase orders, 1 leads
  - tab groups: All 34 / Late 6 / Approvals 22
  - tab **Late**: heading "Now", 0 sections; 3 approvals, 2 to-dos, 2 leads, 2 contacts
  - tab **Approvals**: heading "Now", 1 sections; 17 approvals, 2 findings, 1 bills, 1 files
- reached by: menu › Today › Approvals (3 taps); first button "Everything22"; shot [phone](../../review/census/today/shots/phone_owner_approvals.jpg)
- **Approvals** (`mapprove`): heading "Approvals", 3.2 screens tall, 1 sections (0 above the fold), 4 tab screens; blue: Approve; runs past the edge: cut off by pr-m ($33,500 · Compliance blocks: Insurance (, $16,040 · 6 people · prepared by Chen · )
  - lead: "Every yes or no that is waiting on you — bills, hours, questions from the site, decisions we owe. Approve here; open the record when you need the detail."
  - sections: Also on Your List (22)
  - records: 21 approvals, 5 lessons, 3 vendors, 3 bank and card lines, 2 COI lapses, 2 findings, 1 schedule lines, 1 site questions
  - tab groups: Everything 22 / Bills 1 / Changes 3 / Lessons 6 / Other 12
  - tab **Bills**: heading "Approvals", 1 sections; 1 COI lapses, 1 bills, 1 vendors (runs past the edge: cut off by pr-m ($33,500 · Compliance blocks: Insurance ())
  - tab **Changes**: heading "Approvals", 1 sections; 3 approvals, 1 COI lapses, 1 files, 1 vendors
  - tab **Lessons**: heading "Approvals", 1 sections; 6 approvals, 5 lessons, 1 subs to confirm, 1 COI lapses
  - tab **Other**: heading "Approvals", 1 sections; 13 approvals, 3 vendors, 3 bank and card lines, 2 COI lapses
- reached by: menu › More › Chief of Staff (3 taps); first button "Chat"; shot [phone](../../review/census/today/shots/phone_owner_chief_of_staff.jpg)
- **Chief of Staff** (`pa`): heading "Chief of Staff", 3.5 screens tall, 9 sections (2 above the fold), 1 tab screens; blue: none; opens `pa` when asked for `cos`
  - lead: "What I caught for you, most important first by the Standard, each with the reason and the value behind it."
  - sections: Chief of Staff; ACCOUNTING; COMMITMENTS; PROMISES; OBLIGATIONS; PEOPLE; You Asked Me to Remember (0); What I Have Done (0); The 17 checks, and what each one asks
  - records: 4 decisions, 1 files, 1 vendors, 1 purchase orders
  - columns: The 17 checks, and what each one asks: Chain, Check, The Rule, Found (17 rows)
  - empty states: "No new order should go out and no bill should be approved until a current certificate arrives."; "Nothing yet. Tell me above and I will hold it."; "Nothing yet. Every button I press lands here with the reason."
  - tab groups: Chat / Findings 38 / Activity / Brain Settings; For You / Checklist / Every Chain
  - tab **Chat**: heading "Ask", 0 sections; 2 vendors, 1 to-dos, 1 schedule lines, 1 COI lapses
  - tabs that would not press (the row changed once one was pressed): Activity, Brain Settings, For You, Checklist

### PM (Alan), desktop

- reached by: Today (1 tap); first button "All 21"; shot [desktop](../../review/census/today/shots/desktop_pm_today.jpg)
- **Today** (`home`): heading "Today", 1.1 screens tall, 2 sections (2 above the fold), 2 tab screens; blue: Answer
  - lead: "Everything that needs you today, in the order it matters."
  - sections: NOW; FOR YOU
  - records: 6 to-dos, 3 decisions, 2 schedule lines, 2 site questions
  - tab groups: All 21 / Late 4 / Waiting 1
  - tab **Late**: heading "Today", 1 sections; 3 decisions, 1 mail, 1 schedule lines
  - tab **Waiting**: heading "Today", 1 sections; 1 to-dos, 1 vendors, 1 schedule lines
- reached by: Today › Approvals (2 taps); first button "Everything15"; shot [desktop](../../review/census/today/shots/desktop_pm_approvals.jpg)
- **Approvals** (`mapprove`): heading "Approvals", 4.0 screens tall, 1 sections (0 above the fold), 7 tab screens; blue: Answer
  - lead: "Every yes or no that is waiting on you — bills, hours, questions from the site, decisions we owe. Approve here; open the record when you need the detail."
  - sections: Also on Your List (15)
  - records: 5 decisions, 3 approvals, 2 site questions, 2 vendors, 1 schedule lines, 1 submittals, 1 COI lapses, 1 files
  - empty states: "No change order yet: Garden bath: joist notched by old plumber — needs sistering…"
  - tab groups: Everything 15 / Bills 1 / Hours 4 / Decisions 5 / Submittals 1 / Site Questions 2 / Meetings 1 / Other 1 / 17.1 h with no flags
  - tab **Bills**: heading "Approvals", 1 sections; 2 vendors, 1 COI lapses, 1 approvals, 1 files
  - tab **Hours**: heading "Approvals", 1 sections; 1 COI lapses, 1 files, 1 vendors, 1 purchase orders
  - tab **Decisions**: heading "Approvals", 1 sections; 5 decisions, 1 COI lapses, 1 files, 1 vendors
  - tab **Submittals**: heading "Approvals", 1 sections; 1 submittals, 1 COI lapses, 1 files, 1 vendors
  - tab **Site Questions**: heading "Approvals", 1 sections; 2 site questions, 1 schedule lines, 1 COI lapses, 1 files
  - tab **Meetings**: heading "Approvals", 1 sections; 1 COI lapses, 1 approvals, 1 files, 1 vendors
  - tab **Other**: heading "Approvals", 1 sections; 1 COI lapses, 1 approvals, 1 files, 1 vendors
  - tabs that would not press (the row changed once one was pressed): 17.1 h with no flags
- reached by: More › Chief of Staff (2 taps); first button "Chat"; shot [desktop](../../review/census/today/shots/desktop_pm_chief_of_staff.jpg)
- **Chief of Staff** (`pa`): heading "Chief of Staff", 3.5 screens tall, 9 sections (2 above the fold), 17 tab screens; blue: none; opens `pa` when asked for `cos`
  - lead: "What I caught for you, most important first by the Standard, each with the reason and the value behind it."
  - sections: Chief of Staff; ACCOUNTING; COMMITMENTS; PROMISES; OBLIGATIONS; PEOPLE; You Asked Me to Remember (0); What I Have Done (0); The 17 checks, and what each one asks
  - records: 4 decisions, 1 to-dos, 1 schedule lines, 1 files, 1 vendors, 1 purchase orders, 1 obligations
  - columns: The 17 checks, and what each one asks: Chain, Check, The Rule, Found (17 rows)
  - empty states: "No new order should go out and no bill should be approved until a current certificate arrives."; "None of it is waiting on anybody else, so it needs a hand or a date moved."; "Nothing yet. Tell me above and I will hold it."; "Nothing yet. Every button I press lands here with the reason."
  - tab groups: Chat / Findings 62 / Activity; For You / Checklist / The Brain / Every Chain
  - tab **Chat**: heading "Ask", 1 sections; 2 decisions, 1 schedule lines, 1 vendors
  - tab **Activity**: heading "Ask", 4 sections
  - tab **Activity › On Its Own**: heading "Ask", 4 sections
  - tab **Activity › Proposed**: heading "Ask", 4 sections
  - tab **Activity › Decided**: heading "Ask", 4 sections
  - tab **Activity › Handed to You**: heading "Ask", 4 sections
  - tab **Activity › Act Alone**: heading "Ask", 4 sections
  - tab **Activity › Hand It to Me**: heading "Ask", 4 sections
  - tab **For You**: heading "Ask", 1 sections; 26 money flags, 13 materials, 4 decisions, 2 site questions
  - tab **Checklist**: heading "Ask", 5 sections; 33 findings, 19 materials, 5 money flags, 4 decisions
  - tab **The Brain**: heading "The Brain", 4 sections; 5 vendors, 4 bank and card lines, 2 schedule lines, 2 meetings
  - tab **The Brain › Lessons**: heading "The Brain", 3 sections; 8 lessons, 5 vendors, 4 approvals, 4 bank and card lines
  - tab **The Brain › Proposed**: heading "The Brain", 1 sections; 6 approvals, 5 lessons
  - tab **The Brain › Workload**: heading "The Brain", 2 sections
  - tab **The Brain › Hands**: heading "The Brain", 2 sections
  - tab **The Brain › Watching**: heading "The Brain", 1 sections; 1 materials
  - tab **The Brain › Plugins**: heading "The Brain", 1 sections

### PM (Alan), phone

- reached by: bar: Today (1 tap); first button "All 21"; shot [phone](../../review/census/today/shots/phone_pm_today.jpg)
- **Today** (`home`): heading "Now", 1.3 screens tall, 1 sections (1 above the fold), 2 tab screens; blue: Answer
  - lead: "Everything that needs you today, in the order it matters."
  - sections: FOR YOU
  - records: 2 to-dos, 2 decisions, 1 schedule lines, 1 site questions
  - tab groups: All 21 / Late 4 / Waiting 1
  - tab **Late**: heading "Now", 0 sections; 3 decisions, 1 mail, 1 schedule lines
  - tab **Waiting**: heading "For You", 0 sections; 1 to-dos, 1 vendors
- reached by: menu › Today › Approvals (3 taps); first button "Everything15"; shot [phone](../../review/census/today/shots/phone_pm_approvals.jpg)
- **Approvals** (`mapprove`): heading "Approvals", 2.7 screens tall, 1 sections (0 above the fold), 7 tab screens; blue: Answer; runs past the edge: cut off by pr-m (by 9/3 · 121 State Street · Angel · Call, by 9/4 · 121 State Street · Angel · Plan)
  - lead: "Every yes or no that is waiting on you — bills, hours, questions from the site, decisions we owe. Approve here; open the record when you need the detail."
  - sections: Also on Your List (15)
  - records: 5 decisions, 3 approvals, 2 site questions, 2 vendors, 1 schedule lines, 1 submittals, 1 COI lapses, 1 files
  - empty states: "No change order yet: Garden bath: joist notched by old plumber — needs sistering…"
  - tab groups: Everything 15 / Bills 1 / Hours 4 / Decisions 5 / Submittals 1 / Site Questions 2 / Meetings 1 / Other 1
  - tab **Bills**: heading "Approvals", 1 sections; 2 vendors, 1 COI lapses, 1 approvals, 1 files (runs past the edge: cut off by pr-m ($9,800 · First review — your recommendat))
  - tab **Hours**: heading "Approvals", 1 sections; 1 COI lapses, 1 files, 1 vendors, 1 purchase orders
  - tab **Decisions**: heading "Approvals", 1 sections; 5 decisions, 1 COI lapses, 1 files, 1 vendors
  - tab **Submittals**: heading "Approvals", 1 sections; 1 submittals, 1 COI lapses, 1 files, 1 vendors
  - tab **Site Questions**: heading "Approvals", 1 sections; 2 site questions, 1 schedule lines, 1 COI lapses, 1 files (runs past the edge: cut off by pr-m (by 9/3 · 121 State Street · Angel · Call, by 9/4 · 121 State Street · Angel · Plan))
  - tab **Meetings**: heading "Approvals", 1 sections; 1 COI lapses, 1 approvals, 1 files, 1 vendors (runs past the edge: cut off by pr-m (8 · 8 proposals from the meeting notes —))
  - tab **Other**: heading "Approvals", 1 sections; 1 COI lapses, 1 approvals, 1 files, 1 vendors
- reached by: menu › More › swipe the strip, Chief of Staff (3 taps); first button "Chat"; shot [phone](../../review/census/today/shots/phone_pm_chief_of_staff.jpg)
- **Chief of Staff** (`pa`): heading "Chief of Staff", 3.5 screens tall, 9 sections (2 above the fold), 1 tab screens; blue: none; opens `pa` when asked for `cos`
  - lead: "What I caught for you, most important first by the Standard, each with the reason and the value behind it."
  - sections: Chief of Staff; ACCOUNTING; COMMITMENTS; PROMISES; OBLIGATIONS; PEOPLE; You Asked Me to Remember (0); What I Have Done (0); The 17 checks, and what each one asks
  - records: 4 decisions, 1 files, 1 vendors, 1 purchase orders
  - columns: The 17 checks, and what each one asks: Chain, Check, The Rule, Found (17 rows)
  - empty states: "No new order should go out and no bill should be approved until a current certificate arrives."; "Nothing yet. Tell me above and I will hold it."; "Nothing yet. Every button I press lands here with the reason."
  - tab groups: Chat / Findings 62 / Activity; For You / Checklist / The Brain / Every Chain
  - tab **Chat**: heading "Ask", 0 sections; 2 decisions, 1 schedule lines, 1 vendors
  - tabs that would not press (the row changed once one was pressed): Activity, For You, Checklist, The Brain

### Coordinator (Chen), desktop

- reached by: Today (1 tap); first button "All 29"; shot [desktop](../../review/census/today/shots/desktop_coord_today.jpg)
- **Today** (`home`): heading "Today", 1.1 screens tall, 2 sections (2 above the fold), 2 tab screens; blue: Chase COI
  - lead: "Everything that needs you today, in the order it matters."
  - sections: NOW; FOR YOU
  - records: 4 materials, 3 schedule lines, 2 approvals, 2 vendors, 1 to-dos, 1 field requests, 1 site questions, 1 COI lapses
  - tab groups: All 29 / Late 14 / Waiting 2
  - tab **Late**: heading "Today", 1 sections; 15 materials, 1 mail, 1 schedule lines, 1 COI lapses
  - tab **Waiting**: heading "Today", 2 sections; 2 vendors, 1 to-dos, 1 materials, 1 schedule lines
- reached by: Today › Approvals (2 taps); first button "Everything8"; shot [desktop](../../review/census/today/shots/desktop_coord_approvals.jpg)
- **Approvals** (`mapprove`): heading "Approvals", 2.5 screens tall, 1 sections (0 above the fold), 5 tab screens; blue: Chase COI
  - lead: "Every yes or no that is waiting on you — bills, hours, questions from the site, decisions we owe. Approve here; open the record when you need the detail."
  - sections: Also on Your List (8)
  - records: 6 approvals, 3 materials, 3 vendors, 2 purchase orders, 2 files, 1 schedule lines, 1 field requests, 1 site questions
  - empty states: "No PO behind AMP-311 · Alberto M Plumbing $9,800"; "No sourcing choice: PO-2026-047 · Tino $8,721"
  - tab groups: Everything 8 / Field Requests 1 / Site Questions 1 / Meetings 1 / Prepayments 1 / Other 4 / 17.1 h with no flags
  - tab **Field Requests**: heading "Approvals", 1 sections; 1 field requests, 1 materials, 1 COI lapses, 1 files
  - tab **Site Questions**: heading "Approvals", 1 sections; 1 materials, 1 site questions, 1 COI lapses, 1 files
  - tab **Meetings**: heading "Approvals", 1 sections; 1 COI lapses, 1 approvals, 1 files, 1 vendors
  - tab **Prepayments**: heading "Approvals", 1 sections; 2 purchase orders, 2 files, 2 vendors, 1 materials
  - tab **Other**: heading "Approvals", 1 sections; 4 approvals, 3 vendors, 2 purchase orders, 2 files
  - tabs that would not press (the row changed once one was pressed): 17.1 h with no flags
- reached by: More › Chief of Staff (2 taps); first button "Chat"; shot [desktop](../../review/census/today/shots/desktop_coord_chief_of_staff.jpg)
- **Chief of Staff** (`pa`): heading "Chief of Staff", 3.5 screens tall, 9 sections (2 above the fold), 17 tab screens; blue: none; opens `pa` when asked for `cos`
  - lead: "What I caught for you, most important first by the Standard, each with the reason and the value behind it."
  - sections: Chief of Staff; ACCOUNTING; COMMITMENTS; PROMISES; OBLIGATIONS; PEOPLE; You Asked Me to Remember (0); What I Have Done (0); The 17 checks, and what each one asks
  - records: 4 decisions, 1 to-dos, 1 schedule lines, 1 files, 1 vendors, 1 purchase orders, 1 obligations
  - columns: The 17 checks, and what each one asks: Chain, Check, The Rule, Found (17 rows)
  - empty states: "No new order should go out and no bill should be approved until a current certificate arrives."; "None of it is waiting on anybody else, so it needs a hand or a date moved."; "Nothing yet. Tell me above and I will hold it."; "Nothing yet. Every button I press lands here with the reason."
  - tab groups: Chat / Findings 6 / Activity; For You / Checklist / The Brain / Every Chain
  - tab **Chat**: heading "Ask", 1 sections; 2 materials, 1 to-dos, 1 field requests, 1 approvals
  - tab **Activity**: heading "Ask", 4 sections
  - tab **Activity › On Its Own**: heading "Ask", 4 sections (1 save(s) while reading)
  - tab **Activity › Proposed**: heading "Ask", 4 sections
  - tab **Activity › Decided**: heading "Ask", 4 sections
  - tab **Activity › Handed to You**: heading "Ask", 4 sections
  - tab **Activity › Ask First**: heading "Ask", 4 sections
  - tab **Activity › Hand It to Me**: heading "Ask", 4 sections
  - tab **For You**: heading "Ask", 1 sections; 6 money flags, 5 materials, 2 COI lapses, 2 vendors
  - tab **Checklist**: heading "Ask", 4 sections; 24 findings, 19 materials, 7 vendors, 4 purchase orders
  - tab **The Brain**: heading "The Brain", 4 sections; 5 vendors, 4 bank and card lines, 2 schedule lines, 2 COI lapses
  - tab **The Brain › Lessons**: heading "The Brain", 3 sections; 8 lessons, 5 vendors, 4 approvals, 4 bank and card lines
  - tab **The Brain › Proposed**: heading "The Brain", 1 sections; 6 approvals, 5 lessons
  - tab **The Brain › Workload**: heading "The Brain", 2 sections
  - tab **The Brain › Hands**: heading "The Brain", 2 sections
  - tab **The Brain › Watching**: heading "The Brain", 1 sections; 1 materials
  - tab **The Brain › Plugins**: heading "The Brain", 1 sections

### Coordinator (Chen), phone

- reached by: bar: Today (1 tap); first button "All 29"; shot [phone](../../review/census/today/shots/phone_coord_today.jpg)
- **Today** (`home`): heading "Now", 1.3 screens tall, 1 sections (1 above the fold), 2 tab screens; blue: Chase COI
  - lead: "Everything that needs you today, in the order it matters."
  - sections: FOR YOU
  - records: 3 materials, 2 vendors, 1 to-dos, 1 field requests, 1 COI lapses, 1 approvals, 1 schedule lines
  - tab groups: All 29 / Late 14 / Waiting 2
  - tab **Late**: heading "Now", 0 sections; 15 materials, 1 mail, 1 schedule lines, 1 COI lapses
  - tab **Waiting**: heading "Now", 1 sections; 2 vendors, 1 to-dos, 1 materials, 1 schedule lines
- reached by: menu › Today › Approvals (3 taps); first button "Everything8"; shot [phone](../../review/census/today/shots/phone_coord_approvals.jpg)
- **Approvals** (`mapprove`): heading "Approvals", 1.9 screens tall, 1 sections (1 above the fold), 5 tab screens; blue: Chase COI; runs past the edge: cut off by pr-m (4 · 4 proposals from the meeting notes —, $8,000 · Amex Business Platinum ····1009)
  - lead: "Every yes or no that is waiting on you — bills, hours, questions from the site, decisions we owe. Approve here; open the record when you need the detail."
  - sections: Also on Your List (8)
  - records: 5 approvals, 3 materials, 3 vendors, 2 purchase orders, 2 files, 1 schedule lines, 1 field requests, 1 site questions
  - empty states: "No PO behind AMP-311 · Alberto M Plumbing $9,800 · $9,800 on 121 State Street Open"; "No PO behind AMP-311 · Alberto M Plumbing $9,800 · $9,800 on 121 State Street"; "No PO behind AMP-311 · Alberto M Plumbing"; "No sourcing choice: PO-2026-047 · Tino $8,721 · $8,721 on 121 State Street Open"
  - tab groups: Everything 8 / Field Requests 1 / Site Questions 1 / Meetings 1 / Prepayments 1 / Other 4
  - tab **Field Requests**: heading "Approvals", 1 sections; 1 field requests, 1 materials, 1 COI lapses, 1 files
  - tab **Site Questions**: heading "Approvals", 1 sections; 1 materials, 1 site questions, 1 COI lapses, 1 files
  - tab **Meetings**: heading "Approvals", 1 sections; 1 COI lapses, 1 approvals, 1 files, 1 vendors
  - tab **Prepayments**: heading "Approvals", 1 sections; 2 purchase orders, 2 files, 2 vendors, 1 materials
  - tab **Other**: heading "Approvals", 1 sections; 4 approvals, 3 vendors, 2 purchase orders, 2 files
- reached by: menu › More › swipe the strip, Chief of Staff (3 taps); first button "Chat"; shot [phone](../../review/census/today/shots/phone_coord_chief_of_staff.jpg)
- **Chief of Staff** (`pa`): heading "Chief of Staff", 3.5 screens tall, 9 sections (2 above the fold), 1 tab screens; blue: none; opens `pa` when asked for `cos`
  - lead: "What I caught for you, most important first by the Standard, each with the reason and the value behind it."
  - sections: Chief of Staff; ACCOUNTING; COMMITMENTS; PROMISES; OBLIGATIONS; PEOPLE; You Asked Me to Remember (0); What I Have Done (0); The 17 checks, and what each one asks
  - records: 4 decisions, 1 files, 1 vendors, 1 purchase orders
  - columns: The 17 checks, and what each one asks: Chain, Check, The Rule, Found (17 rows)
  - empty states: "No new order should go out and no bill should be approved until a current certificate arrives."; "Nothing yet. Tell me above and I will hold it."; "Nothing yet. Every button I press lands here with the reason."
  - tab groups: Chat / Findings 6 / Activity; For You / Checklist / The Brain / Every Chain
  - tab **Chat**: heading "Ask", 0 sections; 2 materials, 1 to-dos, 1 field requests, 1 approvals
  - tabs that would not press (the row changed once one was pressed): Activity, For You, Checklist, The Brain

### Foreman (Angel), desktop

- reached by: Today (1 tap); first button "Take Photo"; shot [desktop](../../review/census/today/shots/desktop_foreman_today.jpg)
- **Today** (`ftoday`): heading "Today", 4.5 screens tall, 9 sections (3 above the fold), 0 tab screens; blue: Clock In
  - lead: "Your day on this job: who is coming, what is landing, what is in the way."
  - sections: Packing Slip or Receipt; For You (1); Now; Put on You (2); Arriving Today (2); Today's Work; Who's Here; Tomorrow — Fri, Sep 4 (5); Next Two Weeks
  - records: 16 schedule lines, 3 subs to confirm, 3 decisions, 2 to-dos, 2 vendors, 1 site questions, 1 materials, 1 obligations
  - empty states: "No daily log for Fri, Aug 28 File Late Log · 8/28"

### Foreman (Angel), phone

- reached by: bar: Today (1 tap); first button "Clock In"; shot [phone](../../review/census/today/shots/phone_foreman_today.jpg)
- **Today** (`ftoday`): heading "Today", 2.1 screens tall, 9 sections (1 above the fold), 0 tab screens; blue: Clock In
  - lead: "Your day on this job: who is coming, what is landing, what is in the way."
  - sections: TODAY'S WORK; ARRIVING TODAY (2); FOR YOU (1); More for Today 8 (2); Now; Put on You (2); Who's Here; Tomorrow — Fri, Sep 4 (5); Next Two Weeks
  - records: 9 schedule lines, 3 subs to confirm, 2 vendors, 2 to-dos, 2 decisions, 1 site questions, 1 materials
  - empty states: "No daily log for Fri, Aug 28File Late Log · 8/28"

### Designer (Sarah), desktop

- reached by: Today (1 tap); first button "Due Soon 1 Exposed-beam ceiling: confirm"; shot [desktop](../../review/census/today/shots/desktop_designer_today.jpg)
- **Today** (`sday`): heading "Today", 2.3 screens tall, 8 sections (4 above the fold), 0 tab screens; blue: none
  - lead: "Sarah Davis · Thursday, September 3"
  - sections: From the Field (1); Due Soon (1); Promised; Waiting on a Decision; Drawings; Day Sheet — what you touched; tap to make it hours; Projects (10); This Week 13 hrs
  - figures: Due Soon 1; To Re-Issue 6; Hours Not Logged 4; Waiting on Decisions 11; Over Budget Now 1
  - records: 6 decisions, 6 drawing sheets, 2 schedule lines, 2 site questions, 1 findings, 1 to-dos, 1 materials
  - fields: — what you touched; tap to make it hours, Day, hrs, what
  - empty states: "Nothing is on the record until you confirm it"

### Designer (Sarah), phone

- reached by: bar: Today (1 tap); first button "Due Soon 1"; shot [phone](../../review/census/today/shots/phone_designer_today.jpg)
- **Today** (`sday`): heading "Today", 3.5 screens tall, 8 sections (2 above the fold), 0 tab screens; blue: none
  - lead: "Sarah Davis · Thursday, September 3"
  - sections: From the Field (1); Due Soon (1); Promised; Waiting on a Decision; Drawings; Day Sheet — what you touched; tap to make it hours; Projects (10); This Week 13 hrs
  - figures: Due Soon 1; To Re-Issue 6; Hours Not Logged 4; Waiting on Decisions 11; Over Budget Now 1
  - records: 6 decisions, 6 drawing sheets, 2 schedule lines, 2 site questions, 1 findings, 1 to-dos, 1 materials
  - fields: — what you touched; tap to make it hours, Day, hrs, what
  - empty states: "Nothing is on the record until you confirm it"

### Billing, desktop

- reached by: Today (1 tap); first button "All 5"; shot [desktop](../../review/census/today/shots/desktop_billing_today.jpg)
- **Today** (`home`): heading "Today", 0.9 screens tall, 1 sections (1 above the fold), 2 tab screens; blue: Resolve, $16,
  - lead: "Everything that needs you today, in the order it matters."
  - sections: NOW
  - records: 4 approvals, 3 findings, 1 mail, 1 clients
  - tab groups: All 5 / Late 1 / Waiting 0
  - tab **Late**: heading "Today", 1 sections; 1 mail
  - tab **Waiting**: heading "Today", 0 sections
- reached by: Today › Approvals (2 taps); first button "Everything4"; shot [desktop](../../review/census/today/shots/desktop_billing_approvals.jpg)
- **Approvals** (`mapprove`): heading "Approvals", 1.7 screens tall, 1 sections (0 above the fold), 1 tab screens; blue: Resolve
  - lead: "Every yes or no that is waiting on you — bills, hours, questions from the site, decisions we owe. Approve here; open the record when you need the detail."
  - sections: Also on Your List (4)
  - records: 4 approvals, 3 findings, 1 materials, 1 COI lapses, 1 files, 1 clients, 1 vendors, 1 purchase orders
  - tab groups: Everything 4 / Other 4 / 17.1 h with no flags
  - tab **Other**: heading "Approvals", 1 sections; 4 approvals, 3 findings, 1 materials, 1 COI lapses
  - tabs that would not press (the row changed once one was pressed): 17.1 h with no flags
- reached by: More › Chief of Staff (2 taps); first button "Chat"; shot [desktop](../../review/census/today/shots/desktop_billing_chief_of_staff.jpg)
- **Chief of Staff** (`pa`): heading "Chief of Staff", 3.5 screens tall, 9 sections (2 above the fold), 10 tab screens; blue: none; opens `pa` when asked for `cos`
  - lead: "What I caught for you, most important first by the Standard, each with the reason and the value behind it."
  - sections: Chief of Staff; ACCOUNTING; COMMITMENTS; PROMISES; OBLIGATIONS; PEOPLE; You Asked Me to Remember (0); What I Have Done (0); The 17 checks, and what each one asks
  - records: 4 decisions, 1 to-dos, 1 schedule lines, 1 files, 1 vendors, 1 purchase orders, 1 obligations
  - columns: The 17 checks, and what each one asks: Chain, Check, The Rule, Found (17 rows)
  - empty states: "No new order should go out and no bill should be approved until a current certificate arrives."; "None of it is waiting on anybody else, so it needs a hand or a date moved."; "Nothing yet. Tell me above and I will hold it."; "Nothing yet. Every button I press lands here with the reason."
  - tab groups: Chat / Findings 27 / Activity; For You / Checklist / Every Chain
  - tab **Chat**: heading "Ask", 1 sections; 1 to-dos, 1 approvals, 1 clients, 1 vendors
  - tab **Activity**: heading "Ask", 4 sections
  - tab **Activity › On Its Own**: heading "Ask", 4 sections (1 save(s) while reading)
  - tab **Activity › Proposed**: heading "Ask", 4 sections
  - tab **Activity › Decided**: heading "Ask", 4 sections
  - tab **Activity › Handed to You**: heading "Ask", 4 sections
  - tab **Activity › Act Alone**: heading "Ask", 4 sections
  - tab **Activity › Hand It to Me**: heading "Ask", 4 sections
  - tab **For You**: heading "Ask", 1 sections; 26 money flags, 6 findings, 5 bank and card lines, 3 vendors
  - tab **Checklist**: heading "Ask", 2 sections; 8 findings, 5 money flags, 3 approvals, 1 clients

### Billing, phone

- reached by: bar: Today (1 tap); first button "All 5"; shot [phone](../../review/census/today/shots/phone_billing_today.jpg)
- **Today** (`home`): heading "Now", 1.1 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: Resolve, $16,
  - lead: "Everything that needs you today, in the order it matters."
  - records: 3 approvals, 2 findings, 1 clients
  - tab groups: All 5 / Late 1 / Waiting 0
  - tab **Late**: heading "Now", 0 sections; 1 mail
  - tab **Waiting**: heading "Today", 0 sections
- reached by: menu › Today › Approvals (3 taps); first button "Everything4"; shot [phone](../../review/census/today/shots/phone_billing_approvals.jpg)
- **Approvals** (`mapprove`): heading "Approvals", 1.7 screens tall, 1 sections (1 above the fold), 1 tab screens; blue: Resolve; runs past the edge: cut off by pr-m ($16,350 · 20 days on the books with no b, $5,000 · 35 days on the books with no ba)
  - lead: "Every yes or no that is waiting on you — bills, hours, questions from the site, decisions we owe. Approve here; open the record when you need the detail."
  - sections: Also on Your List (4)
  - records: 1 materials, 1 COI lapses, 1 approvals, 1 findings, 1 files, 1 clients, 1 vendors, 1 purchase orders
  - tab groups: Everything 4 / Other 4
  - tab **Other**: heading "Approvals", 1 sections; 1 materials, 1 COI lapses, 1 approvals, 1 findings (runs past the edge: cut off by pr-m ($16,350 · 20 days on the books with no b, $5,000 · 35 days on the books with no ba))
- reached by: menu › More › swipe the strip, Chief of Staff (3 taps); first button "Chat"; shot [phone](../../review/census/today/shots/phone_billing_chief_of_staff.jpg)
- **Chief of Staff** (`pa`): heading "Chief of Staff", 3.5 screens tall, 9 sections (2 above the fold), 1 tab screens; blue: none; opens `pa` when asked for `cos`
  - lead: "What I caught for you, most important first by the Standard, each with the reason and the value behind it."
  - sections: Chief of Staff; ACCOUNTING; COMMITMENTS; PROMISES; OBLIGATIONS; PEOPLE; You Asked Me to Remember (0); What I Have Done (0); The 17 checks, and what each one asks
  - records: 4 decisions, 1 files, 1 vendors, 1 purchase orders
  - columns: The 17 checks, and what each one asks: Chain, Check, The Rule, Found (17 rows)
  - empty states: "No new order should go out and no bill should be approved until a current certificate arrives."; "Nothing yet. Tell me above and I will hold it."; "Nothing yet. Every button I press lands here with the reason."
  - tab groups: Chat / Findings 27 / Activity; For You / Checklist / Every Chain
  - tab **Chat**: heading "Ask", 0 sections; 1 to-dos, 1 approvals, 1 clients, 1 vendors
  - tabs that would not press (the row changed once one was pressed): Activity, For You, Checklist

### Controller, desktop

- reached by: Today (1 tap); first button "All 6"; shot [desktop](../../review/census/today/shots/desktop_controller_today.jpg)
- **Today** (`home`): heading "Today", 1.0 screens tall, 3 sections (3 above the fold), 2 tab screens; blue: Enter the Bill, $2,
  - lead: "Everything that needs you today, in the order it matters."
  - sections: NOW; APPROVALS; THIS WEEK
  - records: 4 purchase orders, 4 approvals, 4 files, 3 vendors, 1 to-dos, 1 mail, 1 findings, 1 COI lapses
  - tab groups: All 6 / Late 2 / Approvals 4
  - tab **Late**: heading "Today", 1 sections; 2 vendors, 1 approvals, 1 mail, 1 COI lapses
  - tab **Approvals**: heading "Today", 2 sections; 4 purchase orders, 4 approvals, 4 files, 3 vendors
- reached by: Today › Approvals (2 taps); first button "Everything4"; shot [desktop](../../review/census/today/shots/desktop_controller_approvals.jpg)
- **Approvals** (`mapprove`): heading "Approvals", 1.6 screens tall, 1 sections (0 above the fold), 2 tab screens; blue: Open
  - lead: "Every yes or no that is waiting on you — bills, hours, questions from the site, decisions we owe. Approve here; open the record when you need the detail."
  - sections: Also on Your List (4)
  - records: 4 purchase orders, 4 approvals, 4 files, 3 vendors, 1 COI lapses, 1 findings
  - tab groups: Everything 4 / Purchase Tax 1 / Other 3 / 17.1 h with no flags
  - tab **Purchase Tax**: heading "Approvals", 1 sections; 3 purchase orders, 3 files, 1 COI lapses, 1 approvals
  - tab **Other**: heading "Approvals", 1 sections; 3 approvals, 3 vendors, 2 purchase orders, 2 files
  - tabs that would not press (the row changed once one was pressed): 17.1 h with no flags
- reached by: More › Chief of Staff (2 taps); first button "Chat"; shot [desktop](../../review/census/today/shots/desktop_controller_chief_of_staff.jpg)
- **Chief of Staff** (`pa`): heading "Chief of Staff", 3.5 screens tall, 9 sections (2 above the fold), 17 tab screens; blue: none; opens `pa` when asked for `cos`
  - lead: "What I caught for you, most important first by the Standard, each with the reason and the value behind it."
  - sections: Chief of Staff; ACCOUNTING; COMMITMENTS; PROMISES; OBLIGATIONS; PEOPLE; You Asked Me to Remember (0); What I Have Done (0); The 17 checks, and what each one asks
  - records: 4 decisions, 1 to-dos, 1 schedule lines, 1 files, 1 vendors, 1 purchase orders, 1 obligations
  - columns: The 17 checks, and what each one asks: Chain, Check, The Rule, Found (17 rows)
  - empty states: "No new order should go out and no bill should be approved until a current certificate arrives."; "None of it is waiting on anybody else, so it needs a hand or a date moved."; "Nothing yet. Tell me above and I will hold it."; "Nothing yet. Every button I press lands here with the reason."
  - tab groups: Chat / Findings 30 / Activity; For You / Checklist / The Brain / Every Chain
  - tab **Chat**: heading "Ask", 1 sections; 3 approvals, 2 vendors, 1 to-dos, 1 findings
  - tab **Activity**: heading "Ask", 4 sections
  - tab **Activity › On Its Own**: heading "Ask", 4 sections (1 save(s) while reading)
  - tab **Activity › Proposed**: heading "Ask", 4 sections
  - tab **Activity › Decided**: heading "Ask", 4 sections
  - tab **Activity › Handed to You**: heading "Ask", 4 sections
  - tab **Activity › Act Alone**: heading "Ask", 4 sections
  - tab **Activity › Hand It to Me**: heading "Ask", 4 sections
  - tab **For You**: heading "Ask", 1 sections; 26 money flags, 18 findings, 5 bank and card lines, 3 vendors
  - tab **Checklist**: heading "Ask", 8 sections; 51 findings, 24 bank and card lines, 20 money flags, 6 vendors
  - tab **The Brain**: heading "The Brain", 4 sections; 5 vendors, 4 bank and card lines, 2 schedule lines, 2 COI lapses
  - tab **The Brain › Lessons**: heading "The Brain", 3 sections; 8 lessons, 5 vendors, 4 approvals, 4 bank and card lines
  - tab **The Brain › Proposed**: heading "The Brain", 1 sections; 6 approvals, 5 lessons
  - tab **The Brain › Workload**: heading "The Brain", 2 sections
  - tab **The Brain › Hands**: heading "The Brain", 2 sections
  - tab **The Brain › Watching**: heading "The Brain", 1 sections; 1 materials
  - tab **The Brain › Plugins**: heading "The Brain", 1 sections

### Controller, phone

- reached by: bar: Today (1 tap); first button "All 6"; shot [phone](../../review/census/today/shots/phone_controller_today.jpg)
- **Today** (`home`): heading "Now", 1.4 screens tall, 2 sections (1 above the fold), 2 tab screens; blue: Enter the Bill, $2,
  - lead: "Everything that needs you today, in the order it matters."
  - sections: APPROVALS; THIS WEEK
  - records: 3 purchase orders, 3 approvals, 3 files, 2 vendors, 1 to-dos, 1 mail, 1 findings, 1 COI lapses
  - tab groups: All 6 / Late 2 / Approvals 4
  - tab **Late**: heading "Now", 0 sections; 2 vendors, 1 approvals, 1 mail, 1 COI lapses
  - tab **Approvals**: heading "Now", 1 sections; 4 purchase orders, 4 approvals, 4 files, 3 vendors
- reached by: menu › Today › Approvals (3 taps); first button "Everything4"; shot [phone](../../review/census/today/shots/phone_controller_approvals.jpg)
- **Approvals** (`mapprove`): heading "Approvals", 1.7 screens tall, 1 sections (1 above the fold), 2 tab screens; blue: Open; runs past the edge: cut off by pr-m (3 orders · PO-2026-041, PO-2026-044, PO-)
  - lead: "Every yes or no that is waiting on you — bills, hours, questions from the site, decisions we owe. Approve here; open the record when you need the detail."
  - sections: Also on Your List (4)
  - records: 4 purchase orders, 4 files, 3 approvals, 3 vendors, 1 COI lapses, 1 findings
  - tab groups: Everything 4 / Purchase Tax 1 / Other 3
  - tab **Purchase Tax**: heading "Approvals", 1 sections; 3 purchase orders, 3 files, 1 COI lapses, 1 approvals (runs past the edge: cut off by pr-m (3 orders · PO-2026-041, PO-2026-044, PO-))
  - tab **Other**: heading "Approvals", 1 sections; 3 approvals, 3 vendors, 2 purchase orders, 2 files
- reached by: menu › More › swipe the strip, Chief of Staff (3 taps); first button "Chat"; shot [phone](../../review/census/today/shots/phone_controller_chief_of_staff.jpg)
- **Chief of Staff** (`pa`): heading "Chief of Staff", 3.5 screens tall, 9 sections (2 above the fold), 1 tab screens; blue: none; opens `pa` when asked for `cos`
  - lead: "What I caught for you, most important first by the Standard, each with the reason and the value behind it."
  - sections: Chief of Staff; ACCOUNTING; COMMITMENTS; PROMISES; OBLIGATIONS; PEOPLE; You Asked Me to Remember (0); What I Have Done (0); The 17 checks, and what each one asks
  - records: 4 decisions, 1 files, 1 vendors, 1 purchase orders
  - columns: The 17 checks, and what each one asks: Chain, Check, The Rule, Found (17 rows)
  - empty states: "No new order should go out and no bill should be approved until a current certificate arrives."; "Nothing yet. Tell me above and I will hold it."; "Nothing yet. Every button I press lands here with the reason."
  - tab groups: Chat / Findings 30 / Activity; For You / Checklist / The Brain / Every Chain
  - tab **Chat**: heading "Ask", 0 sections; 3 approvals, 2 vendors, 1 to-dos, 1 findings
  - tabs that would not press (the row changed once one was pressed): Activity, For You, Checklist, The Brain

## 7. The Other Roles, One Line a Page

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

