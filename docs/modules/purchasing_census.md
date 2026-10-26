# The Purchasing Module, Page by Page: the Census

**Asked by Alan, 2026-10-26:** "Go through all the modules with screenshots. It's important to understand the format of every page and what's on it." The loop's experts and the client expert walk every page of their module with this in hand in round one of the improvement loop (docs/IMPROVEMENT_LOOP.md).

**What this is.** A machine inventory, not a judgment, in the format of the Projects census (`docs/modules/projects_census.md`). No app code changed. `tests/module_census.py` (its helpers `tests/module_census_js.js` sit on the projects census's reader `tests/census_js.js` and the information map's `tests/ia_js.js`) signs in as each role on a fresh app at 1440 and at 390, reads the role's running menu, and reaches each page of this module the way the person does: the phone bar, or the menu (the hamburger on the phone), the group, then the strip. It presses every tab of every tab group and the tabs those reveal, follows the page's own links to this module's pages the menu did not reach, reads every screen and shoots it. The primary role is the coordinator; every role whose menu holds a page of this module is walked. Job-scoped pages show **121 State Street** wherever the role may open it.

**Build bd3180c27e33** (master 1cc2eb9), the one build every module census of this round ran on. 103 screens in all. Walked 2026-10-26 06:29 on the demo day (Thu 2026-09-03); the walk of every module took 54.4 minutes. Raw read: `review/census/purchasing/data.json`. Every screen per role in tables: `review/census/purchasing/tables.md`. Screenshots of every screen, both devices: `review/census/purchasing/shots/` (`desktop_` or `phone_`, the role, the page, then the tab; up to 3 desktop or 5 phone screens tall). The first screen of each page is committed; the tabs stay on the machine that ran it.

Run it: `python3 build.py && cd tests && ./slot.sh python3 module_census.py --module purchasing` (then `python3 module_census.py --report` rewrites every module's page from data.json).

## Headline

- **Coordinator (Chen): 6 pages with 11 more screens behind their tabs on the desktop (6 pages and 8 tab screens on the phone)**, about 8 desktop screens end to end.
- **Pages each role reaches in this module, desktop:** Owner 6, PM 6, Coordinator 6, Billing 1, Controller 3.
- **Reached only one way** by Coordinator (Chen): Buy Board (desktop), Orders (desktop and phone), Quotes (desktop and phone), Stock (desktop and phone), Vendors (desktop and phone) (one menu entry, not on the phone bar, and no walked page links to it; section 1).
- **The same page under another module's menu** (Coordinator, desktop): Deliveries is also Projects › Deliveries (`recv`).
- **17 records show on two or more of this module's pages** for Coordinator (Chen) on the desktop (6 vendors, 5 materials, 2 purchase orders, 2 files). "PO-2026-047" is on 4: Buy Board, Deliveries, Orders, Vendors.
- **6 pairs of pages list largely the same records,** led by Buy Board and Orders (9 shared); Buy Board and Deliveries (6 shared); Deliveries and Orders (6 shared); Buy Board and Vendors (4 shared).
- **The same records in other modules** (Coordinator, desktop): Today › Chief of Staff lists 31; Company and Settings › The Brain lists 31; Projects › Materials lists 25; Projects › Job Page lists 25; Accounting › Dashboard lists 23 of the 78 records this module lists.
- **One label, different numbers against other modules:** "site" 2 on Purchasing › Stock against 0 on Time and Payroll › Time & Crew (1 in all, section 3).
- **On the phone** (Coordinator): 1 of the 6 pages are taller than three screens (Buy Board); 4 have no section heading above the fold; 3 are reached through a strip entry that sits off screen until the strip is swiped (Deliveries, Vendors, Stock); 0 screens scroll sideways.
- **Nothing crashed and no page raised an error**; every page opened.
- **Reading changed nothing:** no save during the walk.

## 1. The Tree, Role by Role

**Pages** are the module's pages the role reaches from its menu (and the links those pages show). **Tabs** are the screens behind each page's tab groups, and behind the tabs those reveal. **Sections** are the headed parts of each page as it opens. Each cell reads desktop / phone.

| Role | Primary | First page of the module, reached by (desktop / phone) | Pages | Tab screens | Sections | Screens |
|---|---|---|---|---|---|---|
| Owner |  | Purchasing (1 tap) / menu › Purchasing (2 taps) | 6 / 6 | 12 / 9 | 7 / 6 | 18 / 15 |
| PM (Alan) |  | Purchasing (1 tap) / menu › Purchasing (2 taps) | 6 / 6 | 11 / 8 | 6 / 5 | 17 / 14 |
| Coordinator (Chen) | yes | Purchasing (1 tap) / bar: Buy Board (1 tap) | 6 / 6 | 11 / 8 | 6 / 5 | 17 / 14 |
| Billing |  | More › Vendors (2 taps) / menu › More › swipe the strip, Vendors (3 taps) | 1 / 1 | 0 / 0 | 0 / 0 | 1 / 1 |
| Controller |  | Purchasing (1 tap) / menu › Purchasing (2 taps) | 3 / 3 | 0 / 0 | 3 / 3 | 3 / 3 |

### Which pages each role reaches (desktop)

Each cell is the number of screens the page has (the page and its tabs); "-" means the role does not reach it.

| Page | Owner | PM | Coordinator | Billing | Controller |
|---|---|---|---|---|---|
| Buy Board | 5 | 5 | 5 | - | - |
| Quotes | 4 | 4 | 4 | - | - |
| Orders | 1 | 1 | 1 | - | 1 |
| Deliveries | 1 | 1 | 1 | - | - |
| Vendors | 1 | 1 | 1 | 1 | 1 |
| Stock | 6 | 5 | 5 | - | - |
| Purchasing | - | - | - | - | 1 |

### Coordinator (Chen)'s tree at a glance

Reached by is the taps from the role's first page, desktop then phone. Tall is in screens, desktop / phone. Sections are the headed parts as the page opens (phone above the fold). Tabs are the screens behind its tab groups, desktop / phone. "What it lists" counts the records found on the page as it opens.

| Page | Reached by (desktop / phone) | Heading | Tall | Sections (phone above the fold) | Tabs | Tiles and figures | What it lists | Blue button | First button | Shots |
|---|---|---|---|---|---|---|---|---|---|---|
| Buy Board | Purchasing (1 tap) / bar: Buy Board (1 tap) | Buy Board | 2.9 / 5.7 | 1 (0) | 4 / 1 | - | 38 materials, 5 decisions, 4 schedule lines, 4 vendors | Order | FF&E Buying Tools | [desktop](../../review/census/purchasing/shots/desktop_coord_buy_board.jpg) [phone](../../review/census/purchasing/shots/phone_coord_buy_board.jpg) |
| Quotes | Purchasing › Quotes (2 taps) / menu › Purchasing › Quotes (3 taps) | Quotes | 0.5 / 0.8 | 1 (1) | 3 / 3 | - | - | New RFQ | New RFQ (blue) | [desktop](../../review/census/purchasing/shots/desktop_coord_quotes.jpg) [phone](../../review/census/purchasing/shots/phone_coord_quotes.jpg) |
| Orders | Purchasing › Orders (2 taps) / menu › Purchasing › Orders (3 taps) | Orders | 1.4 / 2.3 | 3 (1) | 0 / 0 | Late to Site 0; Not Issued 0; Flagged Orders 1; Open Commitment $39K | 5 materials, 4 purchase orders, 4 files, 4 vendors | New PO | Run Matching | [desktop](../../review/census/purchasing/shots/desktop_coord_orders.jpg) [phone](../../review/census/purchasing/shots/phone_coord_orders.jpg) |
| Deliveries | Purchasing › Deliveries (2 taps) / menu › Purchasing › swipe the strip, Deliveries (3 taps) | Deliveries | 0.5 / 0.4 | 0 (0) | 0 / 0 | - | 2 materials, 2 purchase orders, 2 files, 2 vendors | Received | All Projects | [desktop](../../review/census/purchasing/shots/desktop_coord_deliveries.jpg) [phone](../../review/census/purchasing/shots/phone_coord_deliveries.jpg) |
| Vendors | Purchasing › Vendors (2 taps) / menu › Purchasing › swipe the strip, Vendors (3 taps) | Vendors | 1.1 / 1.4 | 0 (0) | 0 / 0 | Blocked 1; No Certificate 7; Expiring Soon 0; Bank Changes 0 | 12 vendors, 2 purchase orders, 2 files, 1 COI lapses | New Vendor | Performance | [desktop](../../review/census/purchasing/shots/desktop_coord_vendors.jpg) [phone](../../review/census/purchasing/shots/phone_coord_vendors.jpg) |
| Stock | Purchasing › Stock (2 taps) / menu › Purchasing › swipe the strip, Stock (3 taps) | Stock | 1.3 / 2.1 | 1 (0) | 4 / 4 | Out of Stock 0; Reorder Now 1; On This Site 2; Tools Unplaced 0 | 17 stock items | New Item | Move / Adjust | [desktop](../../review/census/purchasing/shots/desktop_coord_stock.jpg) [phone](../../review/census/purchasing/shots/phone_coord_stock.jpg) |

### How each page is reached, and the pages reached only one way

Menu places are the role's menu entries that open the page (a page in two groups has two). The phone bar counts as one more way in on the phone (its pages are in the menu too). Links are the walked pages, in any module, that show a link to it. **One way** means one menu place and nothing else: lose that entry and the page is lost.

| Role | Device | Page | Menu places | Phone bar | Linked from | Ways in |
|---|---|---|---|---|---|---|
| Owner | desktop | Buy Board | Purchasing › Buy Board | - | - | 1 (one way) |
| Owner | desktop | Quotes | Purchasing › Quotes | - | - | 1 (one way) |
| Owner | desktop | Orders | Purchasing › Orders | - | - | 1 (one way) |
| Owner | desktop | Deliveries | Projects › Deliveries; Purchasing › Deliveries | - | - | 2 |
| Owner | desktop | Vendors | Purchasing › Vendors | - | Company and Settings › Your Own Data | 2 |
| Owner | desktop | Stock | Purchasing › Stock | - | - | 1 (one way) |
| Owner | phone | Buy Board | Purchasing › Buy Board | - | - | 1 (one way) |
| Owner | phone | Quotes | Purchasing › Quotes | - | - | 1 (one way) |
| Owner | phone | Orders | Purchasing › Orders | - | - | 1 (one way) |
| Owner | phone | Deliveries | Projects › Deliveries; Purchasing › Deliveries | - | - | 2 |
| Owner | phone | Vendors | Purchasing › Vendors | - | Company and Settings › Your Own Data | 2 |
| Owner | phone | Stock | Purchasing › Stock | - | - | 1 (one way) |
| PM (Alan) | desktop | Buy Board | Purchasing › Buy Board | - | - | 1 (one way) |
| PM (Alan) | desktop | Quotes | Purchasing › Quotes | - | - | 1 (one way) |
| PM (Alan) | desktop | Orders | Purchasing › Orders | - | - | 1 (one way) |
| PM (Alan) | desktop | Deliveries | Projects › Deliveries; Purchasing › Deliveries | - | - | 2 |
| PM (Alan) | desktop | Vendors | Purchasing › Vendors | - | - | 1 (one way) |
| PM (Alan) | desktop | Stock | Purchasing › Stock | - | - | 1 (one way) |
| PM (Alan) | phone | Buy Board | Purchasing › Buy Board | - | - | 1 (one way) |
| PM (Alan) | phone | Quotes | Purchasing › Quotes | - | - | 1 (one way) |
| PM (Alan) | phone | Orders | Purchasing › Orders | - | - | 1 (one way) |
| PM (Alan) | phone | Deliveries | Projects › Deliveries; Purchasing › Deliveries | - | - | 2 |
| PM (Alan) | phone | Vendors | Purchasing › Vendors | - | - | 1 (one way) |
| PM (Alan) | phone | Stock | Purchasing › Stock | - | - | 1 (one way) |
| Coordinator (Chen) | desktop | Buy Board | Purchasing › Buy Board | - | - | 1 (one way) |
| Coordinator (Chen) | desktop | Quotes | Purchasing › Quotes | - | - | 1 (one way) |
| Coordinator (Chen) | desktop | Orders | Purchasing › Orders | - | - | 1 (one way) |
| Coordinator (Chen) | desktop | Deliveries | Purchasing › Deliveries; Projects › Deliveries | - | - | 2 |
| Coordinator (Chen) | desktop | Vendors | Purchasing › Vendors | - | - | 1 (one way) |
| Coordinator (Chen) | desktop | Stock | Purchasing › Stock | - | - | 1 (one way) |
| Coordinator (Chen) | phone | Buy Board | Purchasing › Buy Board | yes | - | 2 |
| Coordinator (Chen) | phone | Quotes | Purchasing › Quotes | - | - | 1 (one way) |
| Coordinator (Chen) | phone | Orders | Purchasing › Orders | - | - | 1 (one way) |
| Coordinator (Chen) | phone | Deliveries | Purchasing › Deliveries; Projects › Deliveries | - | - | 2 |
| Coordinator (Chen) | phone | Vendors | Purchasing › Vendors | - | - | 1 (one way) |
| Coordinator (Chen) | phone | Stock | Purchasing › Stock | - | - | 1 (one way) |
| Billing | desktop | Vendors | More › Vendors | - | - | 1 (one way) |
| Billing | phone | Vendors | More › Vendors | - | - | 1 (one way) |
| Controller | desktop | Purchasing | Purchasing | - | - | 1 (one way) |
| Controller | desktop | Orders | Purchasing › Orders | - | - | 1 (one way) |
| Controller | desktop | Vendors | Purchasing › Vendors | - | - | 1 (one way) |
| Controller | phone | Purchasing | Purchasing | - | - | 1 (one way) |
| Controller | phone | Orders | Purchasing › Orders | - | - | 1 (one way) |
| Controller | phone | Vendors | Purchasing › Vendors | - | - | 1 (one way) |

**Pages of this module the role may open (ROLE_VIEWS) that no menu entry of this module or walked link reached.** Where the census landed on the page from another module (a tab that leaves, another group's entry), that place is named; "not reached" means no walked screen showed it, which for most is a retired page that lands on another (MN_ALIAS, OC_RETIRED) and is left to search and old links.

- Owner, desktop: `ovbuy` (not reached)
- Owner, phone: `ovbuy` (not reached)
- PM (Alan), desktop: `ovbuy` (not reached)
- PM (Alan), phone: `ovbuy` (not reached)
- Coordinator (Chen), desktop: `ovbuy` (not reached)
- Coordinator (Chen), phone: `ovbuy` (not reached)

## 2. Where the Data Lives, and Where It Shows Twice

Records are found by their own words (the information map's catalog, the job's nouns and this census's: clients, vendors, leads, contacts, companies, every invoice, bill and PO, payroll runs, stock, meetings, journals, obligations, lessons, partners, bank lines, threads), so these are floors. A page's tabs count as the page.

### Coordinator (Chen), desktop: each kind of record, and the pages that list it

| Records | Found | Pages that list them (how many each) | Also in other modules |
|---|---|---|---|
| vendors | 12 | 5: Vendors 12, Buy Board 4, Orders 4, Quotes 2, Deliveries 2 | Accounting › Dashboard 9, Today › Chief of Staff 8, Company and Settings › The Brain 8, Design › Selections 5 |
| purchase orders | 4 | 4: Orders 4, Buy Board 2, Deliveries 2, Vendors 2 | Today › Chief of Staff 4, Company and Settings › The Brain 4, Projects › Job Page 2, Today › Approvals 2 |
| files | 4 | 4: Orders 4, Buy Board 2, Deliveries 2, Vendors 2 | Company and Settings › The Brain 4, Today › Chief of Staff 4, Today › Approvals 2, Tasks and Messages › Messages 1 |
| materials | 39 | 3: Buy Board 39, Orders 5, Deliveries 2 | Projects › Materials 22, Today › Chief of Staff 20, Company and Settings › The Brain 20, Today › Today 17 |
| field requests | 2 | 2: Buy Board 2, Quotes 1 | Projects › Job Page 2, Field and Site › Route 2, Field and Site › Requests 2, Today › Today 1 |
| stock items | 17 | 2: Stock 17, Quotes 1 | Time and Payroll › Time & Crew 1 |
| decisions | 5 | 1: Buy Board 5 | Projects › Decisions 5, Company and Settings › Calendar 4, Tasks and Messages › Meetings 3, Accounting › Dashboard 3 |
| schedule lines | 6 | 1: Buy Board 6 | Projects › Schedule 6, Accounting › Dashboard 4, Projects › Job Page 4, Field and Site › Requests 3 |
| COI lapses | 1 | 1: Vendors 1 | Accounting › Dashboard 1, Today › Today 1, Today › Chief of Staff 1, Today › Approvals 1 |

### Records on two or more pages, and lists that are the same list twice

**Owner, desktop:** 17 records on two or more pages: vendors 6 (up to 4 pages); materials 5 (up to 3 pages); purchase orders 2 (up to 4 pages); files 2 (up to 4 pages); field requests 1 (up to 2 pages); stock items 1 (up to 2 pages).

- the same list twice (3 or more shared records, at least half of the shorter list): Buy Board and Orders (9 shared, of 56 and 13: materials, purchase orders, files); Buy Board and Deliveries (6 shared, of 56 and 6: materials, purchase orders, files); Deliveries and Orders (6 shared, of 6 and 13: materials, purchase orders, files); Buy Board and Vendors (4 shared, of 56 and 5: purchase orders, files); Deliveries and Vendors (4 shared, of 6 and 5: purchase orders, files); Orders and Vendors (4 shared, of 13 and 5: purchase orders, files)

**PM (Alan), desktop:** 17 records on two or more pages: vendors 6 (up to 4 pages); materials 5 (up to 3 pages); purchase orders 2 (up to 4 pages); files 2 (up to 4 pages); field requests 1 (up to 2 pages); stock items 1 (up to 2 pages).

- the same list twice (3 or more shared records, at least half of the shorter list): Buy Board and Orders (9 shared, of 56 and 13: materials, files, purchase orders); Buy Board and Deliveries (6 shared, of 56 and 6: files, materials, purchase orders); Deliveries and Orders (6 shared, of 6 and 13: files, materials, purchase orders); Buy Board and Vendors (4 shared, of 56 and 5: files, purchase orders); Deliveries and Vendors (4 shared, of 6 and 5: files, purchase orders); Orders and Vendors (4 shared, of 13 and 5: files, purchase orders)

**Coordinator (Chen), desktop:** 17 records on two or more pages: vendors 6 (up to 4 pages); materials 5 (up to 3 pages); purchase orders 2 (up to 4 pages); files 2 (up to 4 pages); field requests 1 (up to 2 pages); stock items 1 (up to 2 pages).

- "PO-2026-047" (purchase orders) on 4 pages: Buy Board, Deliveries, Orders, Vendors
- "PO-2026-048" (purchase orders) on 4 pages: Buy Board, Deliveries, Orders, Vendors
- "PO-2026-047 — Tino.pdf" (files) on 4 pages: Buy Board, Deliveries, Orders, Vendors
- "PO-2026-048 — Carlos Millwork.pdf" (files) on 4 pages: Buy Board, Deliveries, Orders, Vendors
- "Carlos Millwork" (vendors) on 4 pages: Buy Board, Deliveries, Orders, Vendors
- "Tino" (vendors) on 4 pages: Buy Board, Deliveries, Orders, Vendors
- the same list twice (3 or more shared records, at least half of the shorter list): Buy Board and Orders (9 shared, of 56 and 13: materials, files, purchase orders); Buy Board and Deliveries (6 shared, of 56 and 6: materials, files, purchase orders); Deliveries and Orders (6 shared, of 6 and 13: materials, files, purchase orders); Buy Board and Vendors (4 shared, of 56 and 5: purchase orders, files); Deliveries and Vendors (4 shared, of 6 and 5: purchase orders, files); Orders and Vendors (4 shared, of 13 and 5: purchase orders, files)

**Controller, desktop:** 15 records on two or more pages: vendors 6 (up to 3 pages); materials 5 (up to 2 pages); purchase orders 2 (up to 2 pages); files 2 (up to 2 pages).

- the same list twice (3 or more shared records, at least half of the shorter list): Orders and Vendors (4 shared, of 13 and 5: purchase orders, files)

**Coordinator (Chen), phone:** 17 records on two or more pages: vendors 6 (up to 4 pages); materials 5 (up to 2 pages); purchase orders 2 (up to 3 pages); files 2 (up to 3 pages); field requests 1 (up to 2 pages); stock items 1 (up to 2 pages).

- "Carlos Millwork" (vendors) on 4 pages: Buy Board, Deliveries, Orders, Vendors
- "Tino" (vendors) on 4 pages: Buy Board, Deliveries, Orders, Vendors
- "PO-2026-047" (purchase orders) on 3 pages: Buy Board, Deliveries, Orders
- "PO-2026-048" (purchase orders) on 3 pages: Buy Board, Deliveries, Orders
- "PO-2026-047 — Tino.pdf" (files) on 3 pages: Buy Board, Deliveries, Orders
- "PO-2026-048 — Carlos Millwork.pdf" (files) on 3 pages: Buy Board, Deliveries, Orders
- the same list twice (3 or more shared records, at least half of the shorter list): Buy Board and Orders (9 shared, of 54 and 13: materials, files, purchase orders); Buy Board and Deliveries (4 shared, of 54 and 4: files, purchase orders); Deliveries and Orders (4 shared, of 4 and 13: files, purchase orders)

### The same records in other modules

For each role on the desktop: the pages of other modules (the Projects census's 121 State Street pages included) that list records this module lists, with how many.

- **Owner** (78 records here): Today › Chief of Staff 33; Accounting › Dashboard 27; Projects › Materials 25; Projects › Job Page 25; Accounting › Reports 21; Company and Settings › Company Settings 15; Projects › Decisions 11; Projects › Schedule 10
- **PM (Alan)** (78 records here): Accounting › Dashboard 27; Projects › Materials 25; Projects › Job Page 25; Today › Chief of Staff 25; Company and Settings › The Brain 25; Accounting › Reports 21; Company and Settings › Company Settings 15; Projects › Decisions 11
- **Coordinator (Chen)** (78 records here): Today › Chief of Staff 31; Company and Settings › The Brain 31; Projects › Materials 25; Projects › Job Page 25; Accounting › Dashboard 23; Today › Today 19; Projects › Decisions 11; Projects › Schedule 10
- **Billing** (5 records here): Accounting › Reports 5; Projects › Documents 2; Accounting › Dashboard 1; Today › Approvals 1; Projects › Job Page 1
- **Controller** (51 records here): Accounting › Reports 18; Accounting › Dashboard 16; Today › Approvals 9; Today › Today 8; Billing › Billing 7; Today › Chief of Staff 7; Company and Settings › The Brain 7; Accounting › Spend 6

Names (clients, vendors, leads, contacts, companies, partners) are left out here: a page that writes a name counts as listing it. A page that is the same page as one of this module's (one view under two menus) is left out too and listed next.

### The same page under two modules' menus

- Owner: Deliveries here is also Projects › Deliveries (`recv`)
- PM (Alan): Deliveries here is also Projects › Deliveries (`recv`)
- Coordinator (Chen): Deliveries here is also Projects › Deliveries (`recv`)

## 3. One Label, Different Numbers

The same label (a tile, a figure, a tab or section count) with numbers that share no value on two pages, for one role. Some are right about different scopes ("Open" against "All", one job against every job); the person still reads one word with two numbers. Each needs a person to judge.

Inside the module: none found.

**Against other modules, Coordinator (Chen), desktop** (1):
- site: 2 on Purchasing › Stock; 0 on Time and Payroll › Time & Crew

## 4. Empty, Dead and Broken Screens

| Device | Role | Screen | What |
|---|---|---|---|
| desktop | Owner | Quotes | lists nothing: "Nothing awarded in 2026-09 yet. Report savings monthly: fina" |
| desktop | PM (Alan) | Quotes | lists nothing: "Nothing awarded in 2026-09 yet. Report savings monthly: fina" |
| desktop | Coordinator (Chen) | Quotes | lists nothing: "Nothing awarded in 2026-09 yet. Report savings monthly: fina" |
| phone | Owner | Quotes | lists nothing: "Nothing awarded in 2026-09 yet. Report savings monthly: fina" |
| phone | PM (Alan) | Quotes | lists nothing: "Nothing awarded in 2026-09 yet. Report savings monthly: fina" |
| phone | Coordinator (Chen) | Quotes | lists nothing: "Nothing awarded in 2026-09 yet. Report savings monthly: fina" |

## 5. The Phone at 390

"Cut off" is text the phone ends early; "scrolls inside" is a strip of tiles or tabs the person swipes sideways inside the page (the page itself does not move). "Strip swipe" counts pages whose strip entry sits off screen until the strip is swiped. Pages taller than 3 phone screens are listed with their height.

| Role | Screens | The page scrolls sideways | Text cut off at the edge | Strips that scroll inside the page | Strip swipe | Pages taller than 3 screens |
|---|---|---|---|---|---|---|
| Owner | 15 | 0 | 2: Orders, Quotes | 4: Orders, Quotes, Stock, Vendors | 3: Deliveries, Vendors, Stock | 1: Buy Board 5.7 |
| PM (Alan) | 14 | 0 | 2: Orders, Quotes | 4: Orders, Quotes, Stock, Vendors | 3: Deliveries, Vendors, Stock | 1: Buy Board 5.7 |
| Coordinator (Chen) | 14 | 0 | 2: Orders, Quotes | 4: Orders, Quotes, Stock, Vendors | 3: Deliveries, Vendors, Stock | 1: Buy Board 5.7 |
| Billing | 1 | 0 | 0 | 1: Vendors | 1: Vendors | 0 |
| Controller | 3 | 0 | 2: Orders, Purchasing | 3: Orders, Purchasing, Vendors | 0 | 1: Purchasing 3.2 |

## 6. Page by Page, in Full

Every page the primary role reaches, as it opens, then each of its tabs. Heights are in screens of that device (900px desktop, 844px phone); "above the fold" is above the bottom bar on the phone.

### Coordinator (Chen), desktop

- reached by: Purchasing (1 tap); first button "FF&E Buying Tools"; shot [desktop](../../review/census/purchasing/shots/desktop_coord_buy_board.jpg)
- **Buy Board** (`proc`): heading "Buy Board", 2.9 screens tall, 1 sections (1 above the fold), 4 tab screens; blue: Order
  - sections: Wall-mount lavatory faucet, cross handles
  - records: 38 materials, 5 decisions, 4 schedule lines, 4 vendors, 2 field requests, 2 purchase orders, 2 files
  - fields: Search needs, vendors and lines, Project, Vendor, Trade
  - tab groups: To Buy 35 / Arriving 1; All 35 / To Acknowledge 1 / Late 16 / Order This Week 1 / Waiting on Quotes 0
  - tab **Arriving**: heading "Buy Board", 1 sections; 1 schedule lines, 1 materials
  - tab **To Acknowledge**: heading "Buy Board", 1 sections; 1 schedule lines, 1 field requests, 1 materials
  - tab **Late**: heading "Buy Board", 1 sections; 19 materials, 3 schedule lines, 3 vendors, 2 purchase orders
  - tab **Waiting on Quotes**: heading "Buy Board", 0 sections
  - tabs that would not press (the row changed once one was pressed): Order This Week
- reached by: Purchasing › Quotes (2 taps); first button "New RFQ"; shot [desktop](../../review/census/purchasing/shots/desktop_coord_quotes.jpg)
- **Quotes** (`rfq`): heading "Quotes", 0.5 screens tall, 1 sections (1 above the fold), 3 tab screens; blue: New RFQ
  - lead: "0 open"
  - sections: Savings This Month
  - empty states: "Nothing awarded in 2026-09 yet. Report savings monthly: final price vs. first quote and vs. budget ("
  - tab groups: Requests / Prospects / Sourcing Research / Price Watch
  - tab **Prospects**: heading "RFQs", 0 sections
  - tab **Sourcing Research**: heading "RFQs", 0 sections
  - tab **Price Watch**: heading "RFQs", 7 sections; 2 vendors, 1 field requests, 1 stock items
- reached by: Purchasing › Orders (2 taps); first button "Run Matching"; shot [desktop](../../review/census/purchasing/shots/desktop_coord_orders.jpg)
- **Orders** (`po`): heading "Orders", 1.4 screens tall, 3 sections (2 above the fold), 0 tab screens; blue: New PO
  - lead: "Purchase orders commit cost before it's spent. Incoming transactions match against them automatically; anything off on price, quantity or vendor is flagged."
  - sections: Order Documents and Promises; Client Funds Waiting to Be Spent; Purchase Orders
  - figures: Late to Site 0; Not Issued 0; Flagged Orders 1; Open Commitment $39K
  - records: 5 materials, 4 purchase orders, 4 files, 4 vendors
  - columns: table: PO, VENDOR, JOB, ITEMS, ISSUED, EXPECTED, TOTAL, PAID, STATUS (4 rows); Client Funds Waiting to Be Spent: LINE, COLLECTED, SPENT, OPEN POS, STILL TO BUY, CLIENT FUNDS HELD (7 rows)
  - fields: Jobs, Search…
- reached by: Purchasing › Deliveries (2 taps); also in Projects › Deliveries; first button "All Projects"; shot [desktop](../../review/census/purchasing/shots/desktop_coord_deliveries.jpg)
- **Deliveries** (`recv`): heading "Deliveries", 0.5 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: Received
  - lead: "Check in what arrived, line by line. Materials on the schedule update themselves."
  - records: 2 materials, 2 purchase orders, 2 files, 2 vendors
  - fields: input
- reached by: Purchasing › Vendors (2 taps); first button "Performance"; shot [desktop](../../review/census/purchasing/shots/desktop_coord_vendors.jpg)
- **Vendors** (`vendors`): heading "Vendors", 1.1 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Vendor
  - lead: "One record per vendor and sub: people, W-9, insurance and license expirations, banking (changes need Owner verification), terms, and everything bought from them"
  - figures: Blocked 1; No Certificate 7; Expiring Soon 0; Bank Changes 0; Open Balance $43K
  - records: 12 vendors, 2 purchase orders, 2 files, 1 COI lapses
  - columns: table: VENDOR, TRADE, OPEN ORDERS, INSURANCE, LICENSE, W-9, TERMS, PAID, STATUS (12 rows)
  - fields: Search…
- reached by: Purchasing › Stock (2 taps); first button "Move / Adjust"; shot [desktop](../../review/census/purchasing/shots/desktop_coord_stock.jpg)
- **Stock** (`inv`): heading "Stock", 1.3 screens tall, 1 sections (0 above the fold), 4 tab screens; blue: New Item
  - lead: "What the company owns and stocks, and where it is right now — warehouse, truck, or which job site. Crew request from it; consumables count down; tools move with"
  - sections: Stock Log (0)
  - figures: Out of Stock 0; Reorder Now 1; On This Site 2; Tools Unplaced 0
  - records: 17 stock items
  - columns: table: ITEM, TYPE, ON HAND, AVAILABLE, WHERE, REORDER AT, STATUS (17 rows)
  - fields: Search…, Hold picks days
  - empty states: "No overrides, counts or stock used on jobs yet."
  - tab groups: All / Tools & Machinery / Stock / Low Stock / On This Job
  - tab **Tools & Machinery**: heading "Stock", 1 sections; 8 stock items
  - tab **Stock**: heading "Stock", 1 sections; 9 stock items
  - tab **Low Stock**: heading "Stock", 1 sections; 1 stock items
  - tab **On This Job**: heading "Stock", 1 sections; 2 stock items

### Coordinator (Chen), phone

- reached by: bar: Buy Board (1 tap); first button "Search the Buy Board"; shot [phone](../../review/census/purchasing/shots/phone_coord_buy_board.jpg)
- **Buy Board** (`proc`): heading "Buy Board", 5.7 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: none
  - records: 38 materials, 5 decisions, 4 schedule lines, 4 vendors, 2 field requests, 2 purchase orders, 2 files
  - tab groups: To Buy 35 / Arriving 1
  - tab **Arriving**: heading "Buy Board", 0 sections; 1 materials
- reached by: menu › Purchasing › Quotes (3 taps); first button "New RFQ"; shot [phone](../../review/census/purchasing/shots/phone_coord_quotes.jpg)
- **Quotes** (`rfq`): heading "Quotes", 0.8 screens tall, 1 sections (1 above the fold), 3 tab screens; blue: New RFQ
  - lead: "0 open"
  - sections: Savings This Month
  - empty states: "Nothing awarded in 2026-09 yet. Report savings monthly: final price vs. first quote and vs. budget ("
  - tab groups: Requests / Prospects / Sourcing Research / Price Watch
  - tab **Prospects**: heading "Quotes", 0 sections
  - tab **Sourcing Research**: heading "Quotes", 0 sections
  - tab **Price Watch**: heading "RFQs", 7 sections; 2 vendors, 1 field requests, 1 stock items (runs past the edge: cut off by pr-m ($3.98Brooklyn Lumber — Red Hook, Wed, Se, $54.90Brooklyn Lumber — Red Hook, Wed, S))
- reached by: menu › Purchasing › Orders (3 taps); first button "Run Matching"; shot [phone](../../review/census/purchasing/shots/phone_coord_orders.jpg)
- **Orders** (`po`): heading "Orders", 2.3 screens tall, 3 sections (1 above the fold), 0 tab screens; blue: New PO; runs past the edge: cut off by pr-m (PO-2026-044 · 121 State Street · Double-, PO-2026-041 · 121 State Street · Calacat)
  - lead: "Purchase orders commit cost before it's spent. Incoming transactions match against them automatically; anything off on price, quantity or vendor is flagged."
  - sections: Order Documents and Promises; Client Funds Waiting to Be Spent; Purchase Orders
  - figures: Late to Site 0; Not Issued 0; Flagged Orders 1; Open Commitment $39K
  - records: 5 materials, 4 purchase orders, 4 files, 4 vendors
  - columns: table: PO, Vendor, Job, Items, Issued, Expected, Total, Paid, Status (4 rows); Client Funds Waiting to Be Spent: Line, Collected, Spent, Open POs, Still to Buy, Client Funds Held (7 rows)
  - fields: Jobs, Search…
- reached by: menu › Purchasing › swipe the strip, Deliveries (3 taps); also in Projects › Deliveries; first button "All Projects"; shot [phone](../../review/census/purchasing/shots/phone_coord_deliveries.jpg)
- **Deliveries** (`recv`): heading "Deliveries", 0.4 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
  - lead: "Check in what arrived, line by line. Materials on the schedule update themselves."
  - records: 2 purchase orders, 2 files, 2 vendors
- reached by: menu › Purchasing › swipe the strip, Vendors (3 taps); first button "Performance"; shot [phone](../../review/census/purchasing/shots/phone_coord_vendors.jpg)
- **Vendors** (`vendors`): heading "Vendors", 1.4 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Vendor
  - lead: "One record per vendor and sub: people, W-9, insurance and license expirations, banking (changes need Owner verification), terms, and everything bought from them"
  - figures: Blocked 1; No Certificate 7; Expiring Soon 0; Bank Changes 0; Open Balance $43K
  - records: 12 vendors, 1 COI lapses
  - columns: table: Vendor, Trade, Open Orders, Insurance, License, W-9, Terms, Paid, Status (12 rows)
  - fields: Search…
- reached by: menu › Purchasing › swipe the strip, Stock (3 taps); first button "Move / Adjust"; shot [phone](../../review/census/purchasing/shots/phone_coord_stock.jpg)
- **Stock** (`inv`): heading "Stock", 2.1 screens tall, 1 sections (0 above the fold), 4 tab screens; blue: New Item
  - lead: "What the company owns and stocks, and where it is right now — warehouse, truck, or which job site. Crew request from it; consumables count down; tools move with"
  - sections: Stock Log (0)
  - figures: Out of Stock 0; Reorder Now 1; On This Site 2; Tools Unplaced 0
  - records: 17 stock items
  - columns: table: Item, Type, On Hand, Available, Where, Reorder At, Status (17 rows)
  - fields: Search…, Hold picks days
  - empty states: "No overrides, counts or stock used on jobs yet."
  - tab groups: All / Tools & Machinery / Stock / Low Stock / On This Job
  - tab **Tools & Machinery**: heading "Stock", 1 sections; 8 stock items
  - tab **Stock**: heading "Stock", 1 sections; 9 stock items
  - tab **Low Stock**: heading "Stock", 1 sections; 1 stock items
  - tab **On This Job**: heading "Stock", 1 sections; 2 stock items

## 7. The Other Roles, One Line a Page

### Owner, desktop

- reached by: Purchasing (1 tap); shot [desktop](../../review/census/purchasing/shots/desktop_owner_buy_board.jpg)
- **Buy Board** (`proc`): heading "Buy Board", 2.9 screens tall, 1 sections (1 above the fold), 4 tab screens; blue: Order
- reached by: Purchasing › Quotes (2 taps); shot [desktop](../../review/census/purchasing/shots/desktop_owner_quotes.jpg)
- **Quotes** (`rfq`): heading "Quotes", 0.5 screens tall, 1 sections (1 above the fold), 3 tab screens; blue: New RFQ
- reached by: Purchasing › Orders (2 taps); shot [desktop](../../review/census/purchasing/shots/desktop_owner_orders.jpg)
- **Orders** (`po`): heading "Orders", 1.4 screens tall, 3 sections (2 above the fold), 0 tab screens; blue: New PO
- reached by: Purchasing › Deliveries (2 taps); shot [desktop](../../review/census/purchasing/shots/desktop_owner_deliveries.jpg)
- **Deliveries** (`recv`): heading "Deliveries", 0.5 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: Received
- reached by: Purchasing › Vendors (2 taps); shot [desktop](../../review/census/purchasing/shots/desktop_owner_vendors.jpg)
- **Vendors** (`vendors`): heading "Vendors", 1.1 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Vendor
- reached by: Purchasing › Stock (2 taps); shot [desktop](../../review/census/purchasing/shots/desktop_owner_stock.jpg)
- **Stock** (`inv`): heading "Stock", 1.4 screens tall, 2 sections (0 above the fold), 5 tab screens; blue: New Item

### Owner, phone

- reached by: menu › Purchasing (2 taps); shot [phone](../../review/census/purchasing/shots/phone_owner_buy_board.jpg)
- **Buy Board** (`proc`): heading "Buy Board", 5.7 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: none
- reached by: menu › Purchasing › Quotes (3 taps); shot [phone](../../review/census/purchasing/shots/phone_owner_quotes.jpg)
- **Quotes** (`rfq`): heading "Quotes", 0.8 screens tall, 1 sections (1 above the fold), 3 tab screens; blue: New RFQ
- reached by: menu › Purchasing › Orders (3 taps); shot [phone](../../review/census/purchasing/shots/phone_owner_orders.jpg)
- **Orders** (`po`): heading "Orders", 2.3 screens tall, 3 sections (1 above the fold), 0 tab screens; blue: New PO; runs past the edge: cut off by pr-m (PO-2026-044 · 121 State Street · Double-, PO-2026-041 · 121 State Street · Calacat)
- reached by: menu › Purchasing › swipe the strip, Deliveries (3 taps); shot [phone](../../review/census/purchasing/shots/phone_owner_deliveries.jpg)
- **Deliveries** (`recv`): heading "Deliveries", 0.4 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- reached by: menu › Purchasing › swipe the strip, Vendors (3 taps); shot [phone](../../review/census/purchasing/shots/phone_owner_vendors.jpg)
- **Vendors** (`vendors`): heading "Vendors", 1.4 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Vendor
- reached by: menu › Purchasing › swipe the strip, Stock (3 taps); shot [phone](../../review/census/purchasing/shots/phone_owner_stock.jpg)
- **Stock** (`inv`): heading "Stock", 2.3 screens tall, 2 sections (0 above the fold), 5 tab screens; blue: New Item

### PM (Alan), desktop

- reached by: Purchasing (1 tap); shot [desktop](../../review/census/purchasing/shots/desktop_pm_buy_board.jpg)
- **Buy Board** (`proc`): heading "Buy Board", 2.9 screens tall, 1 sections (1 above the fold), 4 tab screens; blue: Order
- reached by: Purchasing › Quotes (2 taps); shot [desktop](../../review/census/purchasing/shots/desktop_pm_quotes.jpg)
- **Quotes** (`rfq`): heading "Quotes", 0.4 screens tall, 1 sections (1 above the fold), 3 tab screens; blue: New RFQ
- reached by: Purchasing › Orders (2 taps); shot [desktop](../../review/census/purchasing/shots/desktop_pm_orders.jpg)
- **Orders** (`po`): heading "Orders", 1.4 screens tall, 3 sections (2 above the fold), 0 tab screens; blue: New PO
- reached by: Purchasing › Deliveries (2 taps); shot [desktop](../../review/census/purchasing/shots/desktop_pm_deliveries.jpg)
- **Deliveries** (`recv`): heading "Deliveries", 0.5 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: Received
- reached by: Purchasing › Vendors (2 taps); shot [desktop](../../review/census/purchasing/shots/desktop_pm_vendors.jpg)
- **Vendors** (`vendors`): heading "Vendors", 1.1 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Vendor
- reached by: Purchasing › Stock (2 taps); shot [desktop](../../review/census/purchasing/shots/desktop_pm_stock.jpg)
- **Stock** (`inv`): heading "Stock", 1.3 screens tall, 1 sections (0 above the fold), 4 tab screens; blue: New Item

### PM (Alan), phone

- reached by: menu › Purchasing (2 taps); shot [phone](../../review/census/purchasing/shots/phone_pm_buy_board.jpg)
- **Buy Board** (`proc`): heading "Buy Board", 5.7 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: none
- reached by: menu › Purchasing › Quotes (3 taps); shot [phone](../../review/census/purchasing/shots/phone_pm_quotes.jpg)
- **Quotes** (`rfq`): heading "Quotes", 0.7 screens tall, 1 sections (1 above the fold), 3 tab screens; blue: New RFQ
- reached by: menu › Purchasing › Orders (3 taps); shot [phone](../../review/census/purchasing/shots/phone_pm_orders.jpg)
- **Orders** (`po`): heading "Orders", 2.3 screens tall, 3 sections (1 above the fold), 0 tab screens; blue: New PO; runs past the edge: cut off by pr-m (PO-2026-044 · 121 State Street · Double-, PO-2026-041 · 121 State Street · Calacat)
- reached by: menu › Purchasing › swipe the strip, Deliveries (3 taps); shot [phone](../../review/census/purchasing/shots/phone_pm_deliveries.jpg)
- **Deliveries** (`recv`): heading "Deliveries", 0.4 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- reached by: menu › Purchasing › swipe the strip, Vendors (3 taps); shot [phone](../../review/census/purchasing/shots/phone_pm_vendors.jpg)
- **Vendors** (`vendors`): heading "Vendors", 1.4 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Vendor
- reached by: menu › Purchasing › swipe the strip, Stock (3 taps); shot [phone](../../review/census/purchasing/shots/phone_pm_stock.jpg)
- **Stock** (`inv`): heading "Stock", 2.0 screens tall, 1 sections (0 above the fold), 4 tab screens; blue: New Item

### Billing, desktop

- reached by: More › Vendors (2 taps); shot [desktop](../../review/census/purchasing/shots/desktop_billing_vendors.jpg)
- **Vendors** (`vendors`): heading "Vendors", 1.1 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Vendor

### Billing, phone

- reached by: menu › More › swipe the strip, Vendors (3 taps); shot [phone](../../review/census/purchasing/shots/phone_billing_vendors.jpg)
- **Vendors** (`vendors`): heading "Vendors", 1.4 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Vendor

### Controller, desktop

- reached by: Purchasing (1 tap); shot [desktop](../../review/census/purchasing/shots/desktop_controller_purchasing.jpg)
- **Purchasing** (`ovbuy`): heading "Purchasing", 1.1 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- reached by: Purchasing › Orders (2 taps); shot [desktop](../../review/census/purchasing/shots/desktop_controller_orders.jpg)
- **Orders** (`po`): heading "Orders", 1.4 screens tall, 3 sections (2 above the fold), 0 tab screens; blue: New PO
- reached by: Purchasing › Vendors (2 taps); shot [desktop](../../review/census/purchasing/shots/desktop_controller_vendors.jpg)
- **Vendors** (`vendors`): heading "Vendors", 1.1 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Vendor

### Controller, phone

- reached by: menu › Purchasing (2 taps); shot [phone](../../review/census/purchasing/shots/phone_controller_purchasing.jpg)
- **Purchasing** (`ovbuy`): heading "Purchasing", 3.2 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none; runs past the edge: cut off by pr-m (121 State Street · Carlos Millwork · $76)
- reached by: menu › Purchasing › Orders (3 taps); shot [phone](../../review/census/purchasing/shots/phone_controller_orders.jpg)
- **Orders** (`po`): heading "Orders", 2.3 screens tall, 3 sections (1 above the fold), 0 tab screens; blue: New PO; runs past the edge: cut off by pr-m (PO-2026-044 · 121 State Street · Double-, PO-2026-041 · 121 State Street · Calacat)
- reached by: menu › Purchasing › Vendors (3 taps); shot [phone](../../review/census/purchasing/shots/phone_controller_vendors.jpg)
- **Vendors** (`vendors`): heading "Vendors", 1.4 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: New Vendor

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

