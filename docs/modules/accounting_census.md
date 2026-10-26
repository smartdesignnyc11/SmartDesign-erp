# The Accounting Module, Page by Page: the Census

**Asked by Alan, 2026-10-26:** "Go through all the modules with screenshots. It's important to understand the format of every page and what's on it." The loop's experts and the client expert walk every page of their module with this in hand in round one of the improvement loop (docs/IMPROVEMENT_LOOP.md).

**What this is.** A machine inventory, not a judgment, in the format of the Projects census (`docs/modules/projects_census.md`). No app code changed. `tests/module_census.py` (its helpers `tests/module_census_js.js` sit on the projects census's reader `tests/census_js.js` and the information map's `tests/ia_js.js`) signs in as each role on a fresh app at 1440 and at 390, reads the role's running menu, and reaches each page of this module the way the person does: the phone bar, or the menu (the hamburger on the phone), the group, then the strip. It presses every tab of every tab group and the tabs those reveal, follows the page's own links to this module's pages the menu did not reach, reads every screen and shoots it. The primary role is the controller; every role whose menu holds a page of this module is walked. Job-scoped pages show **121 State Street** wherever the role may open it.

**Build bd3180c27e33** (master 1cc2eb9), the one build every module census of this round ran on. 435 screens in all. Walked 2026-10-26 06:29 on the demo day (Thu 2026-09-03); the walk of every module took 54.4 minutes. Raw read: `review/census/accounting/data.json`. Every screen per role in tables: `review/census/accounting/tables.md`. Screenshots of every screen, both devices: `review/census/accounting/shots/` (`desktop_` or `phone_`, the role, the page, then the tab; up to 3 desktop or 5 phone screens tall). The first screen of each page is committed; the tabs stay on the machine that ran it.

Run it: `python3 build.py && cd tests && ./slot.sh python3 module_census.py --module accounting` (then `python3 module_census.py --report` rewrites every module's page from data.json).

## Headline

- **Controller: 9 pages with 51 more screens behind their tabs on the desktop (9 pages and 46 tab screens on the phone)**, about 16 desktop screens end to end.
- **Pages each role reaches in this module, desktop:** Owner 9, PM 7, Coordinator 1, Designer 1, Billing 6, Controller 9.
- **Reached only one way** by Controller: Controls (desktop and phone), Dashboard (desktop and phone), Ledger (desktop and phone), Reports (desktop and phone), Spend (phone) (one menu entry, not on the phone bar, and no walked page links to it; section 1).
- **131 records show on two or more of this module's pages** for Controller on the desktop (95 bank and card lines, 8 vendors, 7 schedule lines, 4 materials). "WW-2026-118" is on 7: Banking, Bills & Payroll, Controls, Dashboard, Ledger, Reports, Spend.
- **6 pairs of pages list largely the same records,** led by Banking and Ledger (95 shared); Banking and Controls (94 shared); Controls and Ledger (89 shared); Banking and Spend (34 shared).
- **The same records in other modules** (Controller, desktop): Company and Settings › The Brain lists 43; Today › Chief of Staff lists 43; Tasks and Messages › Tasks lists 26; Billing › Billing lists 23; Purchasing › Purchasing lists 22 of the 219 records this module lists.
- **On the phone** (Controller): 3 of the 9 pages are taller than three screens (Banking, Reports, Dashboard); 4 have no section heading above the fold; 0 screens scroll sideways.
- **Nothing crashed and no page raised an error**; every page opened.
- **Reading changed nothing:** no save during the walk.

## 1. The Tree, Role by Role

**Pages** are the module's pages the role reaches from its menu (and the links those pages show). **Tabs** are the screens behind each page's tab groups, and behind the tabs those reveal. **Sections** are the headed parts of each page as it opens. Each cell reads desktop / phone.

| Role | Primary | First page of the module, reached by (desktop / phone) | Pages | Tab screens | Sections | Screens |
|---|---|---|---|---|---|---|
| Owner |  | Accounting (1 tap) / menu › Accounting (2 taps) | 9 / 9 | 54 / 47 | 29 / 26 | 63 / 56 |
| PM (Alan) |  | Reports (1 tap) / menu › Reports (2 taps) | 7 / 7 | 48 / 41 | 20 / 19 | 55 / 48 |
| Coordinator (Chen) |  | More › Dashboard (2 taps) / menu › More › swipe the strip, Dashboard (3 taps) | 1 / 1 | 1 / 1 | 3 / 3 | 2 / 2 |
| Designer (Sarah) |  | More › Dashboard (2 taps) / menu › More › Dashboard (3 taps) | 1 / 1 | 1 / 1 | 0 / 0 | 2 / 2 |
| Billing |  | Banking (1 tap) / menu › Banking (2 taps) | 6 / 6 | 41 / 37 | 21 / 20 | 47 / 43 |
| Controller | yes | Banking (1 tap) / bar: Banking (1 tap) | 9 / 9 | 51 / 46 | 26 / 23 | 60 / 55 |

### Which pages each role reaches (desktop)

Each cell is the number of screens the page has (the page and its tabs); "-" means the role does not reach it.

| Page | Owner | PM | Coordinator | Designer | Billing | Controller |
|---|---|---|---|---|---|---|
| Accounting | 1 | 1 | - | - | 1 | 1 |
| Bills & Payroll | 4 | 4 | - | - | 4 | 4 |
| Banking | 6 | 6 | - | - | 6 | 6 |
| Spend | 7 | 7 | - | - | 7 | 5 |
| Ledger | 7 | - | - | - | - | 7 |
| Controls | 7 | 7 | - | - | - | 7 |
| Budget | 1 | - | - | - | - | 1 |
| Reports | 26 | 26 | - | - | 26 | 26 |
| Dashboard | 4 | 4 | 2 | 2 | 3 | 3 |

### Controller's tree at a glance

Reached by is the taps from the role's first page, desktop then phone. Tall is in screens, desktop / phone. Sections are the headed parts as the page opens (phone above the fold). Tabs are the screens behind its tab groups, desktop / phone. "What it lists" counts the records found on the page as it opens.

| Page | Reached by (desktop / phone) | Heading | Tall | Sections (phone above the fold) | Tabs | Tiles and figures | What it lists | Blue button | First button | Shots |
|---|---|---|---|---|---|---|---|---|---|---|
| Banking | Banking (1 tap) / bar: Banking (1 tap) | Banking | 3.8 / 7.5 | 4 (1) | 5 / 5 | To Review 15; Oldest Unmatched 19 days; Cash in Bank $184K; Unexplained 0 | 17 bank and card lines, 6 vendors, 3 materials, 1 subs to confirm | Reconcile | Reconcile (blue) | [desktop](../../review/census/accounting/shots/desktop_controller_banking.jpg) [phone](../../review/census/accounting/shots/phone_controller_banking.jpg) |
| Spend | Banking › Spend (2 taps) / menu › Banking › Spend (3 taps) | Spend | 0.7 / 0.7 | 0 (0) | 4 / 2 | Missing Receipts 0; Uncoded 0; To Approve 2; No Record Behind 15 | - | New Receipt | New Receipt (blue) | [desktop](../../review/census/accounting/shots/desktop_controller_spend.jpg) [phone](../../review/census/accounting/shots/phone_controller_spend.jpg) |
| Bills & Payroll | Bills & Payroll (1 tap) / bar: Bills & Payroll (1 tap) | Bills & Payroll | 1.0 / 1.2 | 2 (2) | 3 / 1 | Needs Approval 2; Overdue to Pay 1; Due This Week 0; Flagged Bills 2 | 4 vendors, 2 bills, 1 payroll runs | New Vendor Bill | New Payroll Run | [desktop](../../review/census/accounting/shots/desktop_controller_bills_payroll.jpg) [phone](../../review/census/accounting/shots/phone_controller_bills_payroll.jpg) |
| Ledger | Ledger (1 tap) / menu › Ledger (2 taps) | Ledger | 0.8 / 1.4 | 3 (2) | 6 / 6 | Journals to Approve 0; Period Open August; Drift 0; Uncoded Cost 1 | - | none | Overview | [desktop](../../review/census/accounting/shots/desktop_controller_ledger.jpg) [phone](../../review/census/accounting/shots/phone_controller_ledger.jpg) |
| Controls | Ledger › Controls (2 taps) / menu › Ledger › Controls (3 taps) | Controls | 1.2 / 1.8 | 0 (0) | 6 / 6 | Exceptions Open 15; Aged Exceptions 1; Not Yet Checked 36; Verified 0% | 16 bank and card lines, 4 vendors | Run Verification | Run Verification (blue) | [desktop](../../review/census/accounting/shots/desktop_controller_controls.jpg) [phone](../../review/census/accounting/shots/phone_controller_controls.jpg) |
| Budget | Ledger › Budget (2 taps) / menu › Ledger › Budget (3 taps) | Budget | 1.9 / 2.2 | 2 (0) | 0 / 0 | - | - | Review Variances | Review Variances (blue) | [desktop](../../review/census/accounting/shots/desktop_controller_budget.jpg) [phone](../../review/census/accounting/shots/phone_controller_budget.jpg) |
| Reports | Reports (1 tap) / menu › Reports (2 taps) | Reports | 3.9 / 7.0 | 11 (2) | 25 / 24 | Revenue (earned) $191, $142,759; Job cost (COGS) 76% of $108,494; Gross Profit 24% $34,265; Net Profit -4% −$5,330 | 3 clients | none | Print / PDF | [desktop](../../review/census/accounting/shots/desktop_controller_reports.jpg) [phone](../../review/census/accounting/shots/phone_controller_reports.jpg) |
| Dashboard | Reports › Dashboard (2 taps) / menu › Reports › Dashboard (3 taps) | Dashboard | 2.1 / 4.2 | 3 (0) | 2 / 2 | - | 12 schedule lines, 9 decisions, 8 to-dos, 7 materials | none | Customize | [desktop](../../review/census/accounting/shots/desktop_controller_dashboard.jpg) [phone](../../review/census/accounting/shots/phone_controller_dashboard.jpg) |
| Accounting | More › Accounting (2 taps) / menu › More › Accounting (3 taps) | Accounting | 0.6 / 0.8 | 1 (1) | 0 / 0 | No Record Behind 15; Receipts to Approve 6; Hours to Approve 4; Cards and Bills 16 | - | none | No Record Behind 15 bank lin | [desktop](../../review/census/accounting/shots/desktop_controller_accounting.jpg) [phone](../../review/census/accounting/shots/phone_controller_accounting.jpg) |

### How each page is reached, and the pages reached only one way

Menu places are the role's menu entries that open the page (a page in two groups has two). The phone bar counts as one more way in on the phone (its pages are in the menu too). Links are the walked pages, in any module, that show a link to it. **One way** means one menu place and nothing else: lose that entry and the page is lost.

| Role | Device | Page | Menu places | Phone bar | Linked from | Ways in |
|---|---|---|---|---|---|---|
| Owner | desktop | Accounting | Accounting | - | Accounting › Spend | 2 |
| Owner | desktop | Bills & Payroll | Accounting › Bills & Payroll | - | Accounting › Reports | 2 |
| Owner | desktop | Banking | Accounting › Banking | - | Billing › Billing, Projects › Change Orders, Purchasing › Vendors, Sales and Clients › Estimates | 5 |
| Owner | desktop | Spend | Accounting › Spend | - | Purchasing › Vendors, Sales and Clients › Numbers, Sales and Clients › Numbers — Dashboard, Sales and Clients › Numbers — Forecast | 5 |
| Owner | desktop | Ledger | Accounting › Ledger | - | - | 1 (one way) |
| Owner | desktop | Controls | Accounting › Controls | - | - | 1 (one way) |
| Owner | desktop | Budget | Accounting › Budget | - | Accounting › Accounting, Accounting › Reports | 3 |
| Owner | desktop | Reports | Reports | - | - | 1 (one way) |
| Owner | desktop | Dashboard | Reports › Dashboard | - | - | 1 (one way) |
| Owner | phone | Accounting | Accounting | - | Accounting › Spend | 2 |
| Owner | phone | Bills & Payroll | Accounting › Bills & Payroll | - | Accounting › Reports | 2 |
| Owner | phone | Banking | Accounting › Banking | - | Purchasing › Vendors | 2 |
| Owner | phone | Spend | Accounting › Spend | - | Sales and Clients › Numbers, Sales and Clients › Numbers — Dashboard, Sales and Clients › Numbers — Forecast | 4 |
| Owner | phone | Ledger | Accounting › Ledger | - | - | 1 (one way) |
| Owner | phone | Controls | Accounting › Controls | - | - | 1 (one way) |
| Owner | phone | Budget | Accounting › Budget | - | Accounting › Accounting, Accounting › Reports | 3 |
| Owner | phone | Reports | Reports | - | - | 1 (one way) |
| Owner | phone | Dashboard | Reports › Dashboard | - | - | 1 (one way) |
| PM (Alan) | desktop | Reports | Reports | - | - | 1 (one way) |
| PM (Alan) | desktop | Dashboard | Reports › Dashboard | - | - | 1 (one way) |
| PM (Alan) | desktop | Banking | More › Banking | - | Billing › Billing, Projects › Change Orders, Purchasing › Vendors | 4 |
| PM (Alan) | desktop | Bills & Payroll | More › Bills & Payroll | - | Accounting › Reports | 2 |
| PM (Alan) | desktop | Spend | More › Spend | - | Purchasing › Vendors, Sales and Clients › Numbers, Sales and Clients › Numbers — Dashboard, Sales and Clients › Numbers — Forecast | 5 |
| PM (Alan) | desktop | Controls | More › Controls | - | - | 1 (one way) |
| PM (Alan) | desktop | Accounting | More › Accounting | - | Accounting › Spend | 2 |
| PM (Alan) | phone | Reports | Reports | - | - | 1 (one way) |
| PM (Alan) | phone | Dashboard | Reports › Dashboard | - | - | 1 (one way) |
| PM (Alan) | phone | Banking | More › Banking | - | Purchasing › Vendors | 2 |
| PM (Alan) | phone | Bills & Payroll | More › Bills & Payroll | - | Accounting › Reports | 2 |
| PM (Alan) | phone | Spend | More › Spend | - | Sales and Clients › Numbers, Sales and Clients › Numbers — Dashboard, Sales and Clients › Numbers — Forecast | 4 |
| PM (Alan) | phone | Controls | More › Controls | - | - | 1 (one way) |
| PM (Alan) | phone | Accounting | More › Accounting | - | Accounting › Spend | 2 |
| Coordinator (Chen) | desktop | Dashboard | More › Dashboard | - | - | 1 (one way) |
| Coordinator (Chen) | phone | Dashboard | More › Dashboard | - | - | 1 (one way) |
| Designer (Sarah) | desktop | Dashboard | More › Dashboard | - | - | 1 (one way) |
| Designer (Sarah) | phone | Dashboard | More › Dashboard | - | - | 1 (one way) |
| Billing | desktop | Banking | Banking | - | Billing › Billing, Purchasing › Vendors | 3 |
| Billing | desktop | Reports | Reports | - | - | 1 (one way) |
| Billing | desktop | Dashboard | Reports › Dashboard | - | - | 1 (one way) |
| Billing | desktop | Bills & Payroll | More › Bills & Payroll | - | Accounting › Reports | 2 |
| Billing | desktop | Spend | More › Spend | - | Purchasing › Vendors | 2 |
| Billing | desktop | Accounting | More › Accounting | - | - | 1 (one way) |
| Billing | phone | Banking | Banking | - | Purchasing › Vendors | 2 |
| Billing | phone | Reports | Reports | - | - | 1 (one way) |
| Billing | phone | Dashboard | Reports › Dashboard | - | - | 1 (one way) |
| Billing | phone | Bills & Payroll | More › Bills & Payroll | - | Accounting › Reports | 2 |
| Billing | phone | Spend | More › Spend | - | - | 1 (one way) |
| Billing | phone | Accounting | More › Accounting | - | - | 1 (one way) |
| Controller | desktop | Banking | Banking | - | Billing › Billing, Purchasing › Vendors | 3 |
| Controller | desktop | Spend | Banking › Spend | - | Purchasing › Vendors | 2 |
| Controller | desktop | Bills & Payroll | Bills & Payroll | - | Accounting › Reports | 2 |
| Controller | desktop | Ledger | Ledger | - | - | 1 (one way) |
| Controller | desktop | Controls | Ledger › Controls | - | - | 1 (one way) |
| Controller | desktop | Budget | Ledger › Budget | - | Accounting › Accounting, Accounting › Reports | 3 |
| Controller | desktop | Reports | Reports | - | - | 1 (one way) |
| Controller | desktop | Dashboard | Reports › Dashboard | - | - | 1 (one way) |
| Controller | desktop | Accounting | More › Accounting | - | Accounting › Spend | 2 |
| Controller | phone | Banking | Banking | yes | Purchasing › Vendors | 3 |
| Controller | phone | Spend | Banking › Spend | - | - | 1 (one way) |
| Controller | phone | Bills & Payroll | Bills & Payroll | yes | Accounting › Reports | 3 |
| Controller | phone | Ledger | Ledger | - | - | 1 (one way) |
| Controller | phone | Controls | Ledger › Controls | - | - | 1 (one way) |
| Controller | phone | Budget | Ledger › Budget | - | Accounting › Accounting, Accounting › Reports | 3 |
| Controller | phone | Reports | Reports | - | - | 1 (one way) |
| Controller | phone | Dashboard | Reports › Dashboard | - | - | 1 (one way) |
| Controller | phone | Accounting | More › Accounting | - | Accounting › Spend | 2 |

## 2. Where the Data Lives, and Where It Shows Twice

Records are found by their own words (the information map's catalog, the job's nouns and this census's: clients, vendors, leads, contacts, companies, every invoice, bill and PO, payroll runs, stock, meetings, journals, obligations, lessons, partners, bank lines, threads), so these are floors. A page's tabs count as the page.

### Controller, desktop: each kind of record, and the pages that list it

| Records | Found | Pages that list them (how many each) | Also in other modules |
|---|---|---|---|
| bills | 2 | 7: Spend 2, Bills & Payroll 2, Ledger 2, Banking 1, Controls 1, Reports 1, Dashboard 1 | Today › Chief of Staff 2, Company and Settings › The Brain 2 |
| vendors | 10 | 7: Dashboard 9, Banking 8, Ledger 7, Controls 7, Spend 6, Reports 6, Bills & Payroll 4 | Purchasing › Vendors 10, Today › Chief of Staff 8, Company and Settings › The Brain 8, Company and Settings › Obligations 5 |
| materials | 24 | 6: Dashboard 14, Reports 11, Banking 4, Spend 2, Ledger 1, Controls 1 | Purchasing › Purchasing 22, Billing › Billing 7, Purchasing › Orders 5, Tasks and Messages › Tasks 2 |
| bank and card lines | 95 | 5: Banking 95, Ledger 93, Controls 89, Spend 30, Reports 7 | Today › Chief of Staff 26, Company and Settings › The Brain 26 |
| files | 4 | 5: Reports 3, Spend 2, Banking 1, Controls 1, Dashboard 1 | Today › Today 4, Today › Approvals 4, Purchasing › Orders 4, Purchasing › Vendors 2 |
| purchase orders | 4 | 5: Reports 3, Spend 2, Banking 1, Controls 1, Dashboard 1 | Today › Today 4, Today › Approvals 4, Purchasing › Orders 4, Today › Chief of Staff 2 |
| clients | 4 | 4: Reports 4, Ledger 3, Dashboard 3, Banking 1 | Tasks and Messages › Messages 4, Billing › Billing 3, Sales and Clients › Clients 3, Today › Chief of Staff 1 |
| schedule lines | 21 | 3: Dashboard 14, Reports 13, Banking 1 | Tasks and Messages › Tasks 14, Billing › Billing 6, Company and Settings › The Brain 3, Today › Chief of Staff 3 |
| subs to confirm | 1 | 2: Banking 1, Controls 1 | Company and Settings › The Brain 1, Today › Chief of Staff 1 |
| journal entries | 26 | 2: Ledger 26, Reports 3 | - |
| invoices | 6 | 2: Ledger 6, Reports 4 | Billing › Billing 6 |
| change orders | 2 | 2: Reports 2, Dashboard 1 | Billing › Billing 2 |
| COI lapses | 2 | 2: Dashboard 2, Reports 1 | Company and Settings › The Brain 2, Today › Chief of Staff 2, Today › Today 1, Today › Approvals 1 |
| selections | 1 | 1: Banking 1 | - |
| payroll runs | 1 | 1: Bills & Payroll 1 | - |
| estimates | 2 | 1: Reports 2 | Billing › Billing 2 |
| submittals | 9 | 1: Reports 9 | - |
| to-dos | 8 | 1: Dashboard 8 | Company and Settings › Calendar 8, Tasks and Messages › Tasks 8, Company and Settings › The SmartDesign Standard 2 |
| decisions | 9 | 1: Dashboard 9 | Company and Settings › Calendar 6, Tasks and Messages › Meetings 4, Company and Settings › The Brain 4, Today › Chief of Staff 4 |
| inspections | 1 | 1: Dashboard 1 | Company and Settings › Calendar 1 |
| obligations | 1 | 1: Dashboard 1 | Company and Settings › Obligations 1, Tasks and Messages › Tasks 1 |

### Records on two or more pages, and lists that are the same list twice

**Owner, desktop:** 134 records on two or more pages: bank and card lines 95 (up to 5 pages); vendors 8 (up to 7 pages); schedule lines 8 (up to 2 pages); materials 6 (up to 6 pages); invoices 4 (up to 2 pages); clients 3 (up to 4 pages); journal entries 3 (up to 2 pages); bills 2 (up to 7 pages); subs to confirm 1 (up to 2 pages); files 1 (up to 5 pages); purchase orders 1 (up to 5 pages); COI lapses 1 (up to 2 pages); change orders 1 (up to 2 pages).

- the same list twice (3 or more shared records, at least half of the shorter list): Banking and Ledger (95 shared, of 105 and 128: bank and card lines, bills, materials); Banking and Controls (94 shared, of 105 and 94: bank and card lines, subs to confirm, bills); Controls and Ledger (89 shared, of 94 and 128: bank and card lines, bills, materials); Banking and Spend (34 shared, of 105 and 38: bank and card lines, bills, purchase orders); Controls and Spend (34 shared, of 94 and 38: bank and card lines, bills, purchase orders); Ledger and Spend (33 shared, of 128 and 38: bank and card lines, bills, materials)

**PM (Alan), desktop:** 121 records on two or more pages: bank and card lines 89 (up to 4 pages); vendors 8 (up to 6 pages); schedule lines 8 (up to 2 pages); materials 6 (up to 5 pages); clients 3 (up to 3 pages); bills 2 (up to 6 pages); files 1 (up to 5 pages); purchase orders 1 (up to 5 pages); COI lapses 1 (up to 2 pages); change orders 1 (up to 2 pages); subs to confirm 1 (up to 2 pages).

- the same list twice (3 or more shared records, at least half of the shorter list): Banking and Controls (94 shared, of 105 and 94: bank and card lines, subs to confirm, bills); Banking and Spend (34 shared, of 105 and 38: bank and card lines, bills, purchase orders); Controls and Spend (34 shared, of 94 and 38: bank and card lines, bills, purchase orders)

**Billing, desktop:** 64 records on two or more pages: bank and card lines 36 (up to 3 pages); vendors 8 (up to 5 pages); schedule lines 7 (up to 2 pages); materials 4 (up to 4 pages); clients 3 (up to 3 pages); bills 2 (up to 5 pages); files 1 (up to 4 pages); purchase orders 1 (up to 4 pages); COI lapses 1 (up to 2 pages); change orders 1 (up to 2 pages).

- the same list twice (3 or more shared records, at least half of the shorter list): Banking and Spend (34 shared, of 105 and 38: bank and card lines, bills, files)

**Controller, desktop:** 131 records on two or more pages: bank and card lines 95 (up to 5 pages); vendors 8 (up to 7 pages); schedule lines 7 (up to 2 pages); materials 4 (up to 6 pages); invoices 4 (up to 2 pages); clients 3 (up to 4 pages); journal entries 3 (up to 2 pages); bills 2 (up to 7 pages); subs to confirm 1 (up to 2 pages); files 1 (up to 5 pages); purchase orders 1 (up to 5 pages); COI lapses 1 (up to 2 pages); change orders 1 (up to 2 pages).

- "WW-2026-118" (bills) on 7 pages: Banking, Bills & Payroll, Controls, Dashboard, Ledger, Reports, Spend
- "Window Works" (vendors) on 7 pages: Banking, Bills & Payroll, Controls, Dashboard, Ledger, Reports, Spend
- "Alberto M Plumbing" (vendors) on 7 pages: Banking, Bills & Payroll, Controls, Dashboard, Ledger, Reports, Spend
- "Nemo Tile" (vendors) on 7 pages: Banking, Bills & Payroll, Controls, Dashboard, Ledger, Reports, Spend
- "Satish Electric Inc" (vendors) on 6 pages: Banking, Controls, Dashboard, Ledger, Reports, Spend
- "Flooring" (materials) on 6 pages: Banking, Controls, Dashboard, Ledger, Reports, Spend
- the same list twice (3 or more shared records, at least half of the shorter list): Banking and Ledger (95 shared, of 105 and 128: bank and card lines, bills, materials); Banking and Controls (94 shared, of 105 and 94: bank and card lines, subs to confirm, bills); Controls and Ledger (89 shared, of 94 and 128: bank and card lines, bills, materials); Banking and Spend (34 shared, of 105 and 38: bank and card lines, bills, purchase orders); Controls and Spend (34 shared, of 94 and 38: bank and card lines, bills, purchase orders); Ledger and Spend (33 shared, of 128 and 38: bank and card lines, bills, materials)

**Controller, phone:** 130 records on two or more pages: bank and card lines 94 (up to 5 pages); vendors 8 (up to 7 pages); schedule lines 7 (up to 2 pages); materials 4 (up to 5 pages); invoices 4 (up to 2 pages); clients 3 (up to 4 pages); journal entries 3 (up to 2 pages); bills 2 (up to 6 pages); subs to confirm 1 (up to 2 pages); files 1 (up to 4 pages); purchase orders 1 (up to 4 pages); COI lapses 1 (up to 2 pages); change orders 1 (up to 2 pages).

- "Window Works" (vendors) on 7 pages: Banking, Bills & Payroll, Controls, Dashboard, Ledger, Reports, Spend
- "Alberto M Plumbing" (vendors) on 7 pages: Banking, Bills & Payroll, Controls, Dashboard, Ledger, Reports, Spend
- "WW-2026-118" (bills) on 6 pages: Banking, Bills & Payroll, Controls, Dashboard, Ledger, Reports
- "Satish Electric Inc" (vendors) on 6 pages: Banking, Controls, Dashboard, Ledger, Reports, Spend
- "Bedrosians" (vendors) on 5 pages: Banking, Controls, Dashboard, Ledger, Spend
- "Nemo Tile" (vendors) on 5 pages: Banking, Controls, Dashboard, Ledger, Reports
- the same list twice (3 or more shared records, at least half of the shorter list): Banking and Ledger (89 shared, of 98 and 128: bank and card lines, bills); Controls and Ledger (89 shared, of 94 and 128: bank and card lines, bills, materials); Banking and Controls (87 shared, of 98 and 94: bank and card lines, subs to confirm, bills); Controls and Spend (31 shared, of 94 and 31: bank and card lines, materials); Ledger and Spend (31 shared, of 128 and 31: bank and card lines, materials); Banking and Spend (27 shared, of 98 and 31: bank and card lines)

### The same records in other modules

For each role on the desktop: the pages of other modules (the Projects census's 121 State Street pages included) that list records this module lists, with how many.

- **Owner** (225 records here): Today › Chief of Staff 66; Projects › Job Page 47; Purchasing › Buy Board 35; Tasks and Messages › Tasks 28; Sales and Clients › Estimates 23; Billing › Billing 23; Projects › Tasks 22; Company and Settings › The Brain 22
- **PM (Alan)** (199 records here): Projects › Job Page 47; Today › Chief of Staff 39; Company and Settings › The Brain 39; Purchasing › Buy Board 35; Tasks and Messages › Tasks 28; Projects › Tasks 22; Company and Settings › Company Settings 21; Projects › Schedule 20
- **Coordinator (Chen)** (51 records here): Projects › Job Page 36; Purchasing › Buy Board 20; Tasks and Messages › Tasks 19; Today › Chief of Staff 18; Company and Settings › The Brain 18; Projects › Tasks 18; Projects › Materials 16; Company and Settings › Calendar 16
- **Designer (Sarah)** (21 records here): Tasks and Messages › Tasks 7; Projects › Decisions 7; Design › Project Board 7; Today › Today 6; Projects › Tasks 5; Design › Selections 4; Design › Design 4
- **Billing** (193 records here): Projects › Job Page 39; Tasks and Messages › Tasks 26; Billing › Billing 21; Today › Chief of Staff 14; Projects › Documents 9; Tasks and Messages › Meetings 6; Purchasing › Vendors 5; Today › Approvals 4
- **Controller** (219 records here): Company and Settings › The Brain 43; Today › Chief of Staff 43; Tasks and Messages › Tasks 26; Billing › Billing 23; Purchasing › Purchasing 22; Company and Settings › Calendar 18; Purchasing › Orders 13; Today › Today 9

Names (clients, vendors, leads, contacts, companies, partners) are left out here: a page that writes a name counts as listing it. A page that is the same page as one of this module's (one view under two menus) is left out too and listed next.

### The same page under two modules' menus

None found.

## 3. One Label, Different Numbers

The same label (a tile, a figure, a tab or section count) with numbers that share no value on two pages, for one role. Some are right about different scopes ("Open" against "All", one job against every job); the person still reads one word with two numbers. Each needs a person to judge.

Inside the module: none found.

Against other modules, Controller, desktop: none found.

## 4. Empty, Dead and Broken Screens

None found.

## 5. The Phone at 390

"Cut off" is text the phone ends early; "scrolls inside" is a strip of tiles or tabs the person swipes sideways inside the page (the page itself does not move). "Strip swipe" counts pages whose strip entry sits off screen until the strip is swiped. Pages taller than 3 phone screens are listed with their height.

| Role | Screens | The page scrolls sideways | Text cut off at the edge | Strips that scroll inside the page | Strip swipe | Pages taller than 3 screens |
|---|---|---|---|---|---|---|
| Owner | 56 | 0 | 5: Banking, Bills & Payroll, Controls, Ledger, Reports | 7: Accounting, Banking, Bills & Payroll, Controls, Ledger, Reports, Spend | 5: Banking, Spend, Ledger, Controls, Budget | 3: Banking 7.5, Reports 7.9, Dashboard 4.2 |
| PM (Alan) | 48 | 0 | 4: Banking, Bills & Payroll, Controls, Reports | 6: Accounting, Banking, Bills & Payroll, Controls, Reports, Spend | 3: Spend, Controls, Accounting | 3: Reports 7.9, Dashboard 9.3, Banking 7.5 |
| Coordinator (Chen) | 2 | 0 | 0 | 0 | 1: Dashboard | 1: Dashboard 3.2 |
| Designer (Sarah) | 2 | 0 | 0 | 0 | 0 | 1: Dashboard 6.0 |
| Billing | 43 | 0 | 4: Banking, Bills & Payroll, Reports, Spend | 5: Accounting, Banking, Bills & Payroll, Reports, Spend | 0 | 3: Banking 7.5, Reports 7.0, Dashboard 4.2 |
| Controller | 55 | 0 | 5: Banking, Bills & Payroll, Controls, Ledger, Reports | 7: Accounting, Banking, Bills & Payroll, Controls, Ledger, Reports, Spend | 0 | 3: Banking 7.5, Reports 7.0, Dashboard 4.2 |

## 6. Page by Page, in Full

Every page the primary role reaches, as it opens, then each of its tabs. Heights are in screens of that device (900px desktop, 844px phone); "above the fold" is above the bottom bar on the phone.

### Controller, desktop

- reached by: Banking (1 tap); first button "Reconcile"; shot [desktop](../../review/census/accounting/shots/desktop_controller_banking.jpg)
- **Banking** (`bank`): heading "Banking", 3.8 screens tall, 4 sections (2 above the fold), 5 tab screens; blue: Reconcile
  - lead: "Every bank and card transaction lands here, gets a category and a job, and rolls into job costs. Rules learn from what you approve; the assistant handles the re"
  - sections: Matches Waiting for Your Confirmation (2); Needs Category (11); Statement Imports (9); Bank Feeds & Statements
  - figures: To Review 15; Oldest Unmatched 19 days; Cash in Bank $184K; Unexplained 0; Chase Business Checking ····4471 $184,231; Amex Business Platinum ····1009 −$12,648; Home Depot Pro Xtra ····7720 −$3,419
  - records: 17 bank and card lines, 6 vendors, 3 materials, 1 subs to confirm, 1 bills, 1 files, 1 purchase orders, 1 schedule lines
  - columns: table: DATE, ACCOUNT, DESCRIPTION, AMOUNT, SOURCE, CATEGORY, JOB, ESTIMATE / CO LINE (15 rows); Bank Rules 6 · applied to every line as it arrives: Description Contains, Category, Job, Code, Account, Used (6 rows)
  - fields: Search…, Category — , Job — , Estimate / CO Line — 
  - empty states: "No suggestion — no open order, history or job names this payee; code it in the list below."
  - tab groups: Needs Review / All / Unreconciled; All Accounts / Chase 4471 / Amex 1009 / Home 7720
  - tab **All**: heading "Banking", 4 sections; 95 bank and card lines, 8 vendors, 4 materials, 1 subs to confirm
  - tab **Unreconciled**: heading "Banking", 4 sections; 45 bank and card lines, 8 vendors, 4 materials, 1 subs to confirm
  - tab **Chase**: heading "Banking", 4 sections; 15 bank and card lines, 6 vendors, 3 materials, 1 subs to confirm
  - tab **Amex**: heading "Banking", 4 sections; 16 bank and card lines, 6 vendors, 3 materials, 1 subs to confirm
  - tab **Home**: heading "Banking", 4 sections; 14 bank and card lines, 6 vendors, 3 materials, 1 subs to confirm
- reached by: Banking › Spend (2 taps); first button "New Receipt"; shot [desktop](../../review/census/accounting/shots/desktop_controller_spend.jpg)
- **Spend** (`spend`): heading "Spend", 0.7 screens tall, 0 sections (0 above the fold), 4 tab screens; blue: New Receipt
  - lead: "Every dollar starts where it is spent, not at the bank. A receipt captured at the counter already knows the job, the line and what it is for — so the transactio"
  - figures: Missing Receipts 0; Uncoded 0; To Approve 2; No Record Behind 15
  - columns: table: CAPTURED, WHO, VENDOR, JOB, WHAT IT IS FOR, AMOUNT, RECEIPT (2 rows)
  - fields: sp-proj
  - tab groups: Missing Receipts 0 every card line has i / Uncoded 0 every line carries a job and a / To Approve 2 captured, waiting on a yes / No Record Behind 15 bank lines with no r; The Day 2 / Where Cost Starts 3; To Approve 2 / To Settle / Cost Not Billed 1 / Everything
  - tab **Missing Receipts 0 every card line has i**: heading "Spend", 2 sections; 16 bank and card lines, 4 vendors
  - tab **Where Cost Starts**: heading "Spend", 3 sections; 23 bank and card lines, 2 vendors, 1 materials
  - tab **Where Cost Starts › Hours & Payroll**: heading "Spend", 0 sections; 1 materials
  - tab **Where Cost Starts › Vendor Bills Arriving**: heading "Spend", 1 sections; 2 bills, 2 files, 2 vendors, 2 purchase orders
  - tabs that would not press (the row changed once one was pressed): Uncoded 0 every line carries a job and a, No Record Behind 15 bank lines with no r, To Settle, Cost Not Billed, Everything
- reached by: Bills & Payroll (1 tap); first button "New Payroll Run"; shot [desktop](../../review/census/accounting/shots/desktop_controller_bills_payroll.jpg)
- **Bills & Payroll** (`ap`): heading "Bills & Payroll", 1.0 screens tall, 2 sections (2 above the fold), 3 tab screens; blue: New Vendor Bill
  - lead: "Nothing is paid without an approved bill or payroll run. PMs recommend bills and the Owner approves them; a payroll run is approved by the Owner or the Controll"
  - sections: Paid Before Approval; Payments
  - figures: Needs Approval 2; Overdue to Pay 1; Due This Week 0; Flagged Bills 2
  - records: 4 vendors, 2 bills, 1 payroll runs
  - columns: Paid Before Approval: BILL, PROJECT, AMOUNT, CLEARED, STATUS (1 rows); table: ITEM, ENTITY, PROJECT / ALLOCATION, DATE, DUE, AMOUNT, STATUS, CONTROLS (3 rows); Payments: DATE, VENDOR, BILL, ENTITY, FROM, METHOD, AMOUNT, CLEARED (2 rows)
  - fields: Search…
  - tab groups: Awaiting Approval / Approved · To Pay / Paid / All
  - tab **Approved · To Pay**: heading "Bills & Payroll", 2 sections; 3 vendors, 2 bills
  - tab **Paid**: heading "Bills & Payroll", 2 sections; 3 vendors, 2 bills
  - tab **All**: heading "Bills & Payroll", 2 sections; 4 vendors, 2 bills, 1 payroll runs
- reached by: Ledger (1 tap); first button "Overview"; shot [desktop](../../review/census/accounting/shots/desktop_controller_ledger.jpg)
- **Ledger** (`gl`): heading "Ledger", 0.8 screens tall, 3 sections (3 above the fold), 6 tab screens; blue: none
  - lead: "Every entry behind the numbers, and the management view beside the books."
  - sections: Truth; Ledger Against the Management View; How the Ledger Is Kept
  - figures: Journals to Approve 0; Period Open August; Drift 0; Uncoded Cost 1; Net income on the ledger $175,285.70; Net income in the management view — fully explained −$5,329.88
  - fields: Entity, gl-from, to
  - empty states: "no month sealed yet; the first close seals its postings"
  - tab groups: Overview / Journal / Accounts / Statements / Close / New Entry
  - tab **Journal**: heading "Ledger", 0 sections; 93 bank and card lines, 26 journal entries, 7 vendors, 6 invoices
  - tab **Accounts**: heading "Ledger", 0 sections
  - tab **Statements**: heading "Ledger", 0 sections
  - tab **Statements › Balance Sheet**: heading "Ledger", 0 sections
  - tab **Statements › Cash Flow**: heading "Ledger", 0 sections
  - tab **Statements › Trial Balance**: heading "Ledger", 0 sections
  - tabs that would not press (the row changed once one was pressed): Close, New Entry
- reached by: Ledger › Controls (2 taps); first button "Run Verification"; shot [desktop](../../review/census/accounting/shots/desktop_controller_controls.jpg)
- **Controls** (`verify`): heading "Controls", 1.2 screens tall, 0 sections (0 above the fold), 6 tab screens; blue: Run Verification
  - lead: "Every transaction that hits a bank or card account is checked against approved bills, payroll and POs after it clears. What doesn't reconcile is an exception, a"
  - figures: Exceptions Open 15; Aged Exceptions 1; Not Yet Checked 36; Verified 0%
  - records: 16 bank and card lines, 4 vendors
  - columns: table: CLEARED, ACCOUNT, TRANSACTION, AMOUNT, MATCHED TO, STATUS, OWNER, AGE, FLAGS (15 rows)
  - fields: Search…
  - empty states: "Not yet verified — press Run Verification · open by owner: Controller 15"
  - tab groups: Verification / Approvals / Terms & Early Payment / Reconciled Through / Unassigned Cost; Open Exceptions / Verified / All Transactions
  - tab **Approvals**: heading "Controls", 1 sections; 2 vendors, 1 subs to confirm, 1 bills, 1 files
  - tab **Terms & Early Payment**: heading "Controls", 1 sections; 2 vendors, 1 bills, 1 files, 1 purchase orders
  - tab **Reconciled Through**: heading "Controls", 2 sections
  - tab **Unassigned Cost**: heading "Controls", 1 sections; 3 bank and card lines
  - tab **Verified**: heading "Controls", 0 sections
  - tab **All Transactions**: heading "Controls", 0 sections; 89 bank and card lines, 7 vendors, 1 materials
- reached by: Ledger › Budget (2 taps); first button "Review Variances"; shot [desktop](../../review/census/accounting/shots/desktop_controller_budget.jpg)
- **Budget** (`budget`): heading "Budget", 1.9 screens tall, 2 sections (0 above the fold), 0 tab screens; blue: Review Variances
  - lead: "The 2026 operating budget by entity, account and month. One version is active; Reports, the Pack, the Flash and the Close read it."
  - sections: Job Budgets; History
  - columns: table: ACCOUNT, JAN, FEB, MAR, APR, MAY, JUN, JUL, AUG (21 rows); Job Budgets: JOB, CONTRACT, COST BUDGET, REVENUE IN VERSION, COST IN VERSION (3 rows); History: ON, BY, WHAT, DETAIL (3 rows)
  - fields: Version, Entity
- reached by: Reports (1 tap); first button "Print / PDF"; shot [desktop](../../review/census/accounting/shots/desktop_controller_reports.jpg)
- **Reports** (`reports`): heading "Reports", 3.9 screens tall, 11 sections (4 above the fold), 25 tab screens; blue: none
  - lead: "Profitability by project, line and cost code; client statements; any dataset grouped and totalled."
  - sections: Company; PROFIT & LOSS — YEAR TO DATE (6); PROFIT & LOSS VS BUDGET — YEAR TO DATE; JOB COST BY CATEGORY; OVERHEAD BY CATEGORY (6); JAN 26 TO SEP 26 BY MONTH (6); PROJECTS (6); P&L BY PROJECT; P&L BY CLIENT; JOB REPORTS AND THE P&L (6); P&L TIES
  - figures: Revenue (earned) $191,100 collected $142,759; Job cost (COGS) 76% of income $108,494; Gross Profit 24% $34,265; Net Profit -4% −$5,330
  - records: 3 clients
  - columns: table: ACTUAL, BUDGET, VARIANCE $, VARIANCE % (5 rows); table: MONTH, INCOME, JOB COST, GROSS, OVERHEAD, NET, NET % (9 rows); table: PROJECT, CONTRACT, BILLED, COLLECTED, ACTUAL COST, PROJ. MARGIN, WIP (4 rows); table: PROJECT, CLIENT, INCOME, JOB COST, GROSS PROFIT, OVERHEAD, NET PROFIT, NET % (7 rows)
  - fields: select, Compare with, Entity
  - tab groups: Financials / Projects / Cash & Receivables / Review / Build a Report; P&L Detail / Statements / Budget vs Actual / Monthly Pack / Three-Way Tie-Out; Accrual / Cash
  - tab **Projects**: heading "Reports", 2 sections; 4 clients
  - tab **Projects › Project Profitability**: heading "Reports", 8 sections; 8 materials, 1 schedule lines, 1 clients
  - tab **Projects › Cost Intelligence**: heading "Reports", 7 sections; 2 purchase orders, 2 files, 2 vendors, 2 schedule lines
  - tab **Projects › WIP Schedule**: heading "Reports", 4 sections; 4 clients
  - tab **Projects › Studio**: heading "Reports", 4 sections; 2 estimates, 2 clients
  - tab **Projects › Cost Library**: heading "Reports", 1 sections; 10 materials, 6 schedule lines, 4 vendors
  - tab **Projects › Submittal Log**: heading "Reports", 5 sections; 9 submittals, 4 vendors, 1 materials
  - tab **Projects › Daily Log Summary**: heading "Reports", 2 sections; 4 schedule lines, 1 vendors
  - tab **Projects › Progress vs Plan**: heading "Reports", 2 sections; 8 schedule lines
  - tab **Cash & Receivables**: heading "Reports", 3 sections; 3 invoices, 2 clients, 2 journal entries
  - tab **Cash & Receivables › Payables**: heading "Reports", 8 sections; 6 vendors, 3 clients, 1 bills
  - tab **Cash & Receivables › Client Statement**: heading "Reports", 3 sections; 3 invoices, 1 change orders, 1 clients
  - tab **Cash & Receivables › Cash Forecast**: heading "Reports", 7 sections; 7 bank and card lines, 2 invoices, 2 purchase orders, 2 files
  - tab **Review**: heading "Reports", 1 sections; 6 bank and card lines, 1 COI lapses, 1 files, 1 vendors
  - tab **Review › Weekly Flash**: heading "Reports", 6 sections; 1 COI lapses, 1 vendors
  - tab **Review › Act Now**: heading "Reports", 1 sections; 1 COI lapses, 1 files, 1 vendors, 1 purchase orders
  - tab **Review › This Week**: heading "Reports", 1 sections; 1 COI lapses, 1 vendors
  - tab **Review › Housekeeping**: heading "Reports", 1 sections; 6 bank and card lines, 1 COI lapses, 1 vendors
  - tab **Build a Report**: heading "Reports", 1 sections
  - tab **Statements**: heading "Reports", 15 sections; 3 journal entries, 1 clients, 1 invoices
  - tab **Budget vs Actual**: heading "Reports", 1 sections
  - tab **Budget vs Actual › By Month**: heading "Reports", 1 sections
  - tab **Monthly Pack**: heading "Reports", 14 sections; 2 journal entries, 2 change orders, 1 clients, 1 invoices
  - tab **Three-Way Tie-Out**: heading "Reports", 4 sections
  - tab **Cash**: heading "Reports", 11 sections; 2 clients
- reached by: Reports › Dashboard (2 taps); first button "Customize"; shot [desktop](../../review/census/accounting/shots/desktop_controller_dashboard.jpg)
- **Dashboard** (`dashboard`): heading "Dashboard", 2.1 screens tall, 3 sections (0 above the fold), 2 tab screens; blue: none
  - lead: "The numbers you watch, laid out the way you arranged them."
  - sections: DECIDE 6; APPROVE 5; WATCH 34
  - records: 12 schedule lines, 9 decisions, 8 to-dos, 7 materials, 1 COI lapses, 1 change orders, 1 files, 1 clients
  - columns: table: PROJECT, VARIANCE, FINISH, DRIVER (4 rows)
  - empty states: "nothing urgent"
  - tab groups: My Dashboard / Owner / Projects
  - tab **Owner**: heading "Dashboard", 0 sections; 3 clients, 2 COI lapses, 2 vendors, 1 schedule lines
  - tab **Projects**: heading "Dashboard", 0 sections; 14 materials, 13 schedule lines, 9 decisions, 9 vendors
- reached by: More › Accounting (2 taps); first button "No Record Behind 15 bank lines with no r"; shot [desktop](../../review/census/accounting/shots/desktop_controller_accounting.jpg)
- **Accounting** (`ovmoney`): heading "Accounting", 0.6 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: none
  - lead: "Today’s Review — the lines with nothing behind them first, then what is waiting on you, then what cannot be costed."
  - sections: Today’s Review
  - figures: No Record Behind 15; Receipts to Approve 6; Hours to Approve 4; Cards and Bills 16

### Controller, phone

- reached by: bar: Banking (1 tap); first button "Reconcile"; shot [phone](../../review/census/accounting/shots/phone_controller_banking.jpg)
- **Banking** (`bank`): heading "Banking", 7.5 screens tall, 4 sections (1 above the fold), 5 tab screens; blue: Reconcile; runs past the edge: cut off by pr-m (8/31 · HOUSE OF ANTIQUE HDW CREDIT · +$1, 8/29 · ZELLE TO M RODRIGUEZ M RodriguezC)
  - lead: "Every bank and card transaction lands here, gets a category and a job, and rolls into job costs. Rules learn from what you approve; the assistant handles the re"
  - sections: Statement Imports (9); Matches Waiting for Your Confirmation (2); Needs Category (11); Bank Feeds & Statements
  - figures: To Review 15; Oldest Unmatched 19 days; Cash in Bank $184K; Unexplained 0; Chase Business Checking ····4471 $184,231; Amex Business Platinum ····1009 −$12,648; Home Depot Pro Xtra ····7720 −$3,419
  - records: 15 bank and card lines, 6 vendors, 3 materials, 1 subs to confirm, 1 bills, 1 files, 1 purchase orders, 1 schedule lines
  - columns: table: Date, Account, Description, Amount, Source, Category, Job, Estimate / CO Line (15 rows); Bank Rules 6 · applied to every line as it arrives: Description Contains, Category, Job, Code, Account, Used (6 rows)
  - fields: Search…
  - empty states: "No suggestion — no open order, history or job names this payee; code it in the list below."
  - tab groups: Needs Review / All / Unreconciled; All Accounts / Chase 4471 / Amex 1009 / Home 7720
  - tab **All**: heading "Banking", 4 sections; 89 bank and card lines, 6 vendors, 3 materials, 1 subs to confirm (runs past the edge: cut off by pr-m (8/31 · HOUSE OF ANTIQUE HDW CREDIT · +$1, 8/29 · DEPOSIT CHECK 2214 KLEINCreate Ru))
  - tab **Unreconciled**: heading "Banking", 4 sections; 39 bank and card lines, 6 vendors, 3 materials, 1 subs to confirm (runs past the edge: cut off by pr-m (8/31 · HOUSE OF ANTIQUE HDW CREDIT · +$1, 8/29 · ZELLE TO M RODRIGUEZ M RodriguezC))
  - tab **Chase**: heading "Banking", 4 sections; 15 bank and card lines, 6 vendors, 3 materials, 1 subs to confirm (runs past the edge: cut off by pr-m (8/29 · ZELLE TO M RODRIGUEZ M RodriguezC))
  - tab **Amex**: heading "Banking", 4 sections; 14 bank and card lines, 6 vendors, 3 materials, 1 subs to confirm (runs past the edge: cut off by pr-m (8/31 · HOUSE OF ANTIQUE HDW CREDIT · +$1, 8/25 · SQ *WINDOW WORKS BKLYN Window Wor))
  - tab **Home**: heading "Banking", 4 sections; 14 bank and card lines, 6 vendors, 3 materials, 1 subs to confirm
- reached by: menu › Banking › Spend (3 taps); first button "New Receipt"; shot [phone](../../review/census/accounting/shots/phone_controller_spend.jpg)
- **Spend** (`spend`): heading "Spend", 0.7 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: New Receipt
  - lead: "Every dollar starts where it is spent, not at the bank. A receipt captured at the counter already knows the job, the line and what it is for — so the transactio"
  - figures: Missing Receipts 0; Uncoded 0; To Approve 2; No Record Behind 15
  - columns: table: Captured, Who, Vendor, Job, What It Is For, Amount, Receipt (2 rows)
  - fields: sp-proj
  - tab groups: Missing Receipts 0 / Uncoded 0 / To Approve 2 / No Record Behind 15; The Day 2 / Where Cost Starts 3; To Approve 2 / To Settle / Cost Not Billed 1 / Everything
  - tab **Missing Receipts**: heading "Spend", 2 sections; 16 bank and card lines, 4 vendors
  - tab **Where Cost Starts**: heading "Spend", 3 sections; 23 bank and card lines, 2 vendors, 1 materials
  - tabs that would not press (the row changed once one was pressed): Uncoded, No Record Behind, To Settle, Cost Not Billed, Everything
- reached by: bar: Bills & Payroll (1 tap); first button "New Payroll Run"; shot [phone](../../review/census/accounting/shots/phone_controller_bills_payroll.jpg)
- **Bills & Payroll** (`ap`): heading "Bills & Payroll", 1.2 screens tall, 2 sections (2 above the fold), 1 tab screens; blue: Review; runs past the edge: cut off by pr-m ($16,040 · due 9/1 · 45 Cranberry St — de)
  - lead: "Nothing is paid without an approved bill or payroll run. PMs recommend bills and the Owner approves them; a payroll run is approved by the Owner or the Controll"
  - sections: Paid Before Approval; Payments
  - figures: Needs Approval 2; Overdue to Pay 1; Due This Week 0; Flagged Bills 2
  - records: 2 bills, 2 vendors, 1 payroll runs
  - columns: Paid Before Approval: Bill, Project, Amount, Cleared, Status (1 rows); table: Item, Entity, Project / Allocation, Date, Due, Amount, Status, Controls (3 rows); Payments: Date, Vendor, Bill, Entity, From, Method, Amount, Cleared (2 rows)
  - fields: Search…
  - tab groups: Needs Approval 2 / Overdue to Pay 1 / Due This Week 0 / Flagged Bills 2 / Awaiting Approval / Approved · To Pay / Paid / All
  - tab **Needs Approval**: heading "Bills & Payroll", 2 sections; 2 bills, 2 vendors, 1 payroll runs (runs past the edge: cut off by pr-m ($16,040 · due 9/1 · 45 Cranberry St — de))
  - tabs that would not press (the row changed once one was pressed): Overdue to Pay, Due This Week, Flagged Bills, Approved · To Pay, Paid, All
- reached by: menu › Ledger (2 taps); first button "Overview"; shot [phone](../../review/census/accounting/shots/phone_controller_ledger.jpg)
- **Ledger** (`gl`): heading "Ledger", 1.4 screens tall, 3 sections (2 above the fold), 6 tab screens; blue: none
  - lead: "Every entry behind the numbers, and the management view beside the books."
  - sections: Truth; Ledger Against the Management View; How the Ledger Is Kept
  - figures: Journals to Approve 0; Period Open August; Drift 0; Uncoded Cost 1; Net income on the ledger $175,285.70; Net income in the management view — fully explained −$5,329.88
  - fields: Entity, gl-from, to
  - empty states: "no month sealed yet; the first close seals its postings"
  - tab groups: Overview / Journal / Accounts / Statements / Close / New Entry
  - tab **Journal**: heading "Ledger", 0 sections; 93 bank and card lines, 26 journal entries, 7 vendors, 6 invoices (runs past the edge: cut off by pr-t (Opening · by system (demo seed) · Thu, S))
  - tab **Accounts**: heading "Ledger", 0 sections
  - tab **Statements**: heading "Ledger", 0 sections
  - tab **Statements › Balance Sheet**: heading "Ledger", 0 sections
  - tab **Statements › Cash Flow**: heading "Ledger", 0 sections
  - tab **Statements › Trial Balance**: heading "Ledger", 0 sections
  - tabs that would not press (the row changed once one was pressed): Close, New Entry
- reached by: menu › Ledger › Controls (3 taps); first button "Run Verification"; shot [phone](../../review/census/accounting/shots/phone_controller_controls.jpg)
- **Controls** (`verify`): heading "Controls", 1.8 screens tall, 0 sections (0 above the fold), 6 tab screens; blue: Run Verification; runs past the edge: cut off by pr-m (8/15 · CHECK 2205 ALBERTO M PLUMBING LLC, 8/25 · SQ *WINDOW WORKS BKLYN Window Wor)
  - lead: "Every transaction that hits a bank or card account is checked against approved bills, payroll and POs after it clears. What doesn't reconcile is an exception, a"
  - figures: Exceptions Open 15; Aged Exceptions 1; Not Yet Checked 36; Verified 0%
  - records: 16 bank and card lines, 4 vendors
  - columns: table: Cleared, Account, Transaction, Amount, Matched To, Status, Owner, Age, Flags (15 rows)
  - fields: Search…
  - empty states: "Not yet verified — press Run Verification · open by owner: Controller 15"
  - tab groups: Verification / Approvals / Terms & Early Payment / Reconciled Through / Unassigned Cost; Open Exceptions / Verified / All Transactions
  - tab **Approvals**: heading "Controls", 1 sections; 2 vendors, 1 subs to confirm, 1 bills (runs past the edge: cut off by pr-m ($9,800 · it is with the project manager, $300 · it is with the project manager))
  - tab **Terms & Early Payment**: heading "Controls", 1 sections; 2 vendors, 1 bills, 1 files, 1 purchase orders
  - tab **Reconciled Through**: heading "Controls", 2 sections (runs past the edge: cut off by pr-m ($40,678.8714 lines · $41,044.5113 lines , $588.993 lines · $588.993 lines · closed))
  - tab **Unassigned Cost**: heading "Controls", 1 sections; 3 bank and card lines
  - tab **Verified**: heading "Controls", 0 sections
  - tab **All Transactions**: heading "Controls", 0 sections; 89 bank and card lines, 7 vendors, 1 materials (runs past the edge: cut off by pr-m (8/12 · ACH DEBIT NEMO TILE SUPPLY Nemo T, 8/14 · HOME DEPOT #6166 BROOKLYN NY Home))
- reached by: menu › Ledger › Budget (3 taps); shot [phone](../../review/census/accounting/shots/phone_controller_budget.jpg)
- **Budget** (`budget`): heading "Budget", 2.2 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
  - lead: "The 2026 operating budget by entity, account and month. One version is active; Reports, the Pack, the Flash and the Close read it."
  - fields: Version, Entity, Month
- reached by: menu › Reports (2 taps); first button "Print / PDF"; shot [phone](../../review/census/accounting/shots/phone_controller_reports.jpg)
- **Reports** (`reports`): heading "Company", 7.0 screens tall, 10 sections (2 above the fold), 24 tab screens; blue: none
  - lead: "Profitability by project, line and cost code; client statements; any dataset grouped and totalled."
  - sections: PROFIT & LOSS — YEAR TO DATE (6); PROFIT & LOSS VS BUDGET — YEAR TO DATE; JOB COST BY CATEGORY; OVERHEAD BY CATEGORY (6); JAN 26 TO SEP 26 BY MONTH (6); PROJECTS (6); P&L BY PROJECT; P&L BY CLIENT; JOB REPORTS AND THE P&L (6); P&L TIES
  - figures: Revenue (earned) $191,100 collected $142,759; Job cost (COGS) 76% of income $108,494; Gross Profit 24% $34,265; Net Profit -4% −$5,330
  - records: 3 clients
  - columns: table: Actual, Budget, Variance $, Variance % (5 rows); table: Month, Income, Job Cost, Gross, Overhead, Net, Net % (9 rows); table: Project, Contract, Billed, Collected, Actual Cost, Proj. Margin, WIP (4 rows); table: Project, Client, Income, Job Cost, Gross Profit, Overhead, Net Profit, Net % (7 rows)
  - fields: select
  - tab groups: Financials / Projects / Cash & Receivables / Review / Build a Report; P&L Detail / Statements / Budget vs Actual / Monthly Pack / Three-Way Tie-Out; Accrual / Cash
  - tab **Projects**: heading "Portfolio Profitability", 1 sections; 4 clients
  - tab **Projects › Project Profitability**: heading "121 State Street", 7 sections; 8 materials, 1 schedule lines, 1 clients
  - tab **Projects › Cost Intelligence**: heading "Cost Intelligence", 6 sections; 2 schedule lines, 1 materials
  - tab **Projects › WIP Schedule**: heading "Work-In-Progress Schedule", 3 sections; 4 clients
  - tab **Projects › Studio**: heading "Studio — Design Fees, Hours and Utilization", 3 sections; 2 estimates, 2 clients
  - tab **Projects › Cost Library**: heading "Cost Library", 0 sections; 10 materials, 6 schedule lines, 4 vendors
  - tab **Projects › Submittal Log**: heading "Submittal Log", 4 sections; 9 submittals, 4 vendors, 1 materials (runs past the edge: cut off by pr-m (06 40 00-001 · Carlos Millwork · Control, 09 30 00-001 · Nemo Tile · Nemo Tile10 w))
  - tab **Projects › Daily Log Summary**: heading "Daily Log Summary", 1 sections; 4 schedule lines
  - tab **Projects › Progress vs Plan**: heading "Progress vs Plan", 1 sections; 8 schedule lines
  - tab **Cash & Receivables**: heading "Receivables", 2 sections; 3 invoices, 2 clients, 2 journal entries
  - tab **Cash & Receivables › Payables**: heading "Payables", 7 sections; 6 vendors, 3 clients, 1 subs to confirm, 1 bills
  - tab **Cash & Receivables › Client Statement**: heading "Account Statement", 2 sections; 3 invoices, 1 change orders, 1 clients (runs past the edge: cut off by v-reports (214 Court Street, Brooklyn, NY 11201 (71, (718) 555-0190 · office@smartdesign.exam))
  - tab **Cash & Receivables › Cash Forecast**: heading "Cash Forecast", 6 sections; 7 bank and card lines, 2 invoices, 2 purchase orders, 2 files
  - tab **Review**: heading "Analyst", 0 sections; 6 bank and card lines, 1 COI lapses, 1 files, 1 vendors
  - tab **Review › Weekly Flash**: heading "CEO Weekly Flash", 5 sections; 1 COI lapses, 1 vendors
  - tab **Review › Act Now**: heading "Analyst", 0 sections; 1 COI lapses, 1 files, 1 vendors, 1 purchase orders
  - tab **Review › This Week**: heading "Analyst", 0 sections; 1 COI lapses, 1 vendors
  - tab **Review › Housekeeping**: heading "Analyst", 0 sections; 6 bank and card lines, 1 COI lapses, 1 vendors
  - tab **Build a Report**: heading "Report Builder", 0 sections
  - tab **Statements**: heading "Management View", 14 sections; 3 journal entries, 1 clients, 1 invoices (runs past the edge: cut off by v-reports (Opening · by system (demo seed) · Thu, S))
  - tab **Budget vs Actual**: heading "Budget vs Actual", 0 sections (runs past the edge: cut off by v-reports (Original 2026 · Locked Reforecast Q3 (Ac))
  - tab **Monthly Pack**: heading "Monthly Management Report", 13 sections; 2 journal entries, 2 change orders, 1 clients, 1 invoices (runs past the edge: cut off by pr-m (CO-2026-001 · Radiant floor heat in prim, CO-2026-002 · Sand & stain existing trea))
  - tab **Three-Way Tie-Out**: heading "Three-Way Tie-Out", 3 sections
  - tab **Cash**: heading "Company", 10 sections; 2 clients
- reached by: menu › Reports › Dashboard (3 taps); first button "Customize"; shot [phone](../../review/census/accounting/shots/phone_controller_dashboard.jpg)
- **Dashboard** (`dashboard`): heading "Dashboard", 4.2 screens tall, 3 sections (0 above the fold), 2 tab screens; blue: none
  - lead: "The numbers you watch, laid out the way you arranged them."
  - sections: DECIDE 6; APPROVE 5; WATCH 34
  - records: 12 schedule lines, 9 decisions, 8 to-dos, 7 materials, 1 COI lapses, 1 change orders, 1 files, 1 clients
  - columns: table: Project, Variance, Finish, Driver (4 rows)
  - tab groups: My Dashboard / Owner / Projects
  - tab **Owner**: heading "Dashboard", 0 sections; 3 clients, 2 COI lapses, 2 vendors, 1 schedule lines
  - tab **Projects**: heading "Dashboard", 0 sections; 14 materials, 13 schedule lines, 9 decisions, 9 vendors
- reached by: menu › More › Accounting (3 taps); first button "No Record Behind 15"; shot [phone](../../review/census/accounting/shots/phone_controller_accounting.jpg)
- **Accounting** (`ovmoney`): heading "Accounting", 0.8 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: none
  - lead: "Today’s Review — the lines with nothing behind them first, then what is waiting on you, then what cannot be costed."
  - sections: Today’s Review
  - figures: No Record Behind 15; Receipts to Approve 6; Hours to Approve 4; Cards and Bills 16

## 7. The Other Roles, One Line a Page

### Owner, desktop

- reached by: Accounting (1 tap); shot [desktop](../../review/census/accounting/shots/desktop_owner_accounting.jpg)
- **Accounting** (`ovmoney`): heading "Accounting", 0.6 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: none
- reached by: Accounting › Bills & Payroll (2 taps); shot [desktop](../../review/census/accounting/shots/desktop_owner_bills_payroll.jpg)
- **Bills & Payroll** (`ap`): heading "Bills & Payroll", 1.1 screens tall, 3 sections (2 above the fold), 3 tab screens; blue: New Vendor Bill
- reached by: Accounting › Banking (2 taps); shot [desktop](../../review/census/accounting/shots/desktop_owner_banking.jpg)
- **Banking** (`bank`): heading "Banking", 3.8 screens tall, 4 sections (1 above the fold), 5 tab screens; blue: Reconcile
- reached by: Accounting › Spend (2 taps); shot [desktop](../../review/census/accounting/shots/desktop_owner_spend.jpg)
- **Spend** (`spend`): heading "Spend", 0.7 screens tall, 0 sections (0 above the fold), 6 tab screens; blue: New Receipt
- reached by: Accounting › Ledger (2 taps); shot [desktop](../../review/census/accounting/shots/desktop_owner_ledger.jpg)
- **Ledger** (`gl`): heading "Ledger", 0.8 screens tall, 3 sections (3 above the fold), 6 tab screens; blue: none
- reached by: Accounting › Controls (2 taps); shot [desktop](../../review/census/accounting/shots/desktop_owner_controls.jpg)
- **Controls** (`verify`): heading "Controls", 1.2 screens tall, 0 sections (0 above the fold), 6 tab screens; blue: Run Verification
- reached by: Accounting › Budget (2 taps); shot [desktop](../../review/census/accounting/shots/desktop_owner_budget.jpg)
- **Budget** (`budget`): heading "Budget", 1.9 screens tall, 2 sections (0 above the fold), 0 tab screens; blue: Review Variances
- reached by: Reports (1 tap); shot [desktop](../../review/census/accounting/shots/desktop_owner_reports.jpg)
- **Reports** (`reports`): heading "Reports", 4.4 screens tall, 13 sections (4 above the fold), 25 tab screens; blue: none
- reached by: Reports › Dashboard (2 taps); shot [desktop](../../review/census/accounting/shots/desktop_owner_dashboard.jpg)
- **Dashboard** (`dashboard`): heading "Dashboard", 2.2 screens tall, 3 sections (0 above the fold), 3 tab screens; blue: none

### Owner, phone

- reached by: menu › Accounting (2 taps); shot [phone](../../review/census/accounting/shots/phone_owner_accounting.jpg)
- **Accounting** (`ovmoney`): heading "Accounting", 0.8 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: none
- reached by: menu › Accounting › Bills & Payroll (3 taps); shot [phone](../../review/census/accounting/shots/phone_owner_bills_payroll.jpg)
- **Bills & Payroll** (`ap`): heading "Bills & Payroll", 1.3 screens tall, 3 sections (2 above the fold), 1 tab screens; blue: Review; runs past the edge: cut off by pr-m ($16,040 · due 9/1 · 45 Cranberry St — de)
- reached by: menu › Accounting › swipe the strip, Banking (3 taps); shot [phone](../../review/census/accounting/shots/phone_owner_banking.jpg)
- **Banking** (`bank`): heading "Banking", 7.5 screens tall, 4 sections (1 above the fold), 5 tab screens; blue: Reconcile; runs past the edge: cut off by pr-m (8/31 · HOUSE OF ANTIQUE HDW CREDIT · +$1, 8/29 · ZELLE TO M RODRIGUEZ M RodriguezC)
- reached by: menu › Accounting › swipe the strip, Spend (3 taps); shot [phone](../../review/census/accounting/shots/phone_owner_spend.jpg)
- **Spend** (`spend`): heading "Spend", 0.7 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: New Receipt
- reached by: menu › Accounting › swipe the strip, Ledger (3 taps); shot [phone](../../review/census/accounting/shots/phone_owner_ledger.jpg)
- **Ledger** (`gl`): heading "Ledger", 1.4 screens tall, 3 sections (2 above the fold), 6 tab screens; blue: none
- reached by: menu › Accounting › swipe the strip, Controls (3 taps); shot [phone](../../review/census/accounting/shots/phone_owner_controls.jpg)
- **Controls** (`verify`): heading "Controls", 1.8 screens tall, 0 sections (0 above the fold), 6 tab screens; blue: Run Verification; runs past the edge: cut off by pr-m (8/15 · CHECK 2205 ALBERTO M PLUMBING LLC, 8/25 · SQ *WINDOW WORKS BKLYN Window Wor)
- reached by: menu › Accounting › swipe the strip, Budget (3 taps); shot [phone](../../review/census/accounting/shots/phone_owner_budget.jpg)
- **Budget** (`budget`): heading "Budget", 2.2 screens tall, 0 sections (0 above the fold), 0 tab screens; blue: none
- reached by: menu › Reports (2 taps); shot [phone](../../review/census/accounting/shots/phone_owner_reports.jpg)
- **Reports** (`reports`): heading "Company", 7.9 screens tall, 12 sections (1 above the fold), 24 tab screens; blue: none
- reached by: menu › Reports › Dashboard (3 taps); shot [phone](../../review/census/accounting/shots/phone_owner_dashboard.jpg)
- **Dashboard** (`dashboard`): heading "Dashboard", 4.2 screens tall, 3 sections (0 above the fold), 3 tab screens; blue: none

### PM (Alan), desktop

- reached by: Reports (1 tap); shot [desktop](../../review/census/accounting/shots/desktop_pm_reports.jpg)
- **Reports** (`reports`): heading "Reports", 4.4 screens tall, 13 sections (4 above the fold), 25 tab screens; blue: none
- reached by: Reports › Dashboard (2 taps); shot [desktop](../../review/census/accounting/shots/desktop_pm_dashboard.jpg)
- **Dashboard** (`dashboard`): heading "Dashboard", 5.0 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: Bill $17,
- reached by: More (1 tap); shot [desktop](../../review/census/accounting/shots/desktop_pm_banking.jpg)
- **Banking** (`bank`): heading "Banking", 3.8 screens tall, 4 sections (2 above the fold), 5 tab screens; blue: Reconcile
- reached by: More › Bills & Payroll (2 taps); shot [desktop](../../review/census/accounting/shots/desktop_pm_bills_payroll.jpg)
- **Bills & Payroll** (`ap`): heading "Bills & Payroll", 1.0 screens tall, 2 sections (2 above the fold), 3 tab screens; blue: New Vendor Bill
- reached by: More › Spend (2 taps); shot [desktop](../../review/census/accounting/shots/desktop_pm_spend.jpg)
- **Spend** (`spend`): heading "Spend", 0.7 screens tall, 0 sections (0 above the fold), 6 tab screens; blue: New Receipt
- reached by: More › Controls (2 taps); shot [desktop](../../review/census/accounting/shots/desktop_pm_controls.jpg)
- **Controls** (`verify`): heading "Controls", 1.2 screens tall, 0 sections (0 above the fold), 6 tab screens; blue: Run Verification
- reached by: More › Accounting (2 taps); shot [desktop](../../review/census/accounting/shots/desktop_pm_accounting.jpg)
- **Accounting** (`ovmoney`): heading "Accounting", 0.6 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: none

### PM (Alan), phone

- reached by: menu › Reports (2 taps); shot [phone](../../review/census/accounting/shots/phone_pm_reports.jpg)
- **Reports** (`reports`): heading "Company", 7.9 screens tall, 12 sections (1 above the fold), 24 tab screens; blue: none
- reached by: menu › Reports › Dashboard (3 taps); shot [phone](../../review/census/accounting/shots/phone_pm_dashboard.jpg)
- **Dashboard** (`dashboard`): heading "Dashboard", 9.3 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: Bill $17,
- reached by: menu › More (2 taps); shot [phone](../../review/census/accounting/shots/phone_pm_banking.jpg)
- **Banking** (`bank`): heading "Banking", 7.5 screens tall, 4 sections (1 above the fold), 5 tab screens; blue: Reconcile; runs past the edge: cut off by pr-m (8/31 · HOUSE OF ANTIQUE HDW CREDIT · +$1, 8/29 · ZELLE TO M RODRIGUEZ M RodriguezC)
- reached by: menu › More › Bills & Payroll (3 taps); shot [phone](../../review/census/accounting/shots/phone_pm_bills_payroll.jpg)
- **Bills & Payroll** (`ap`): heading "Bills & Payroll", 1.2 screens tall, 2 sections (2 above the fold), 1 tab screens; blue: Review; runs past the edge: cut off by pr-m ($16,040 · due 9/1 · 45 Cranberry St — de)
- reached by: menu › More › swipe the strip, Spend (3 taps); shot [phone](../../review/census/accounting/shots/phone_pm_spend.jpg)
- **Spend** (`spend`): heading "Spend", 0.7 screens tall, 0 sections (0 above the fold), 2 tab screens; blue: New Receipt
- reached by: menu › More › swipe the strip, Controls (3 taps); shot [phone](../../review/census/accounting/shots/phone_pm_controls.jpg)
- **Controls** (`verify`): heading "Controls", 1.8 screens tall, 0 sections (0 above the fold), 6 tab screens; blue: Run Verification; runs past the edge: cut off by pr-m (8/15 · CHECK 2205 ALBERTO M PLUMBING LLC, 8/25 · SQ *WINDOW WORKS BKLYN Window Wor)
- reached by: menu › More › swipe the strip, Accounting (3 taps); shot [phone](../../review/census/accounting/shots/phone_pm_accounting.jpg)
- **Accounting** (`ovmoney`): heading "Accounting", 0.8 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: none

### Coordinator (Chen), desktop

- reached by: More › Dashboard (2 taps); shot [desktop](../../review/census/accounting/shots/desktop_coord_dashboard.jpg)
- **Dashboard** (`dashboard`): heading "Dashboard", 1.7 screens tall, 3 sections (0 above the fold), 1 tab screens; blue: none

### Coordinator (Chen), phone

- reached by: menu › More › swipe the strip, Dashboard (3 taps); shot [phone](../../review/census/accounting/shots/phone_coord_dashboard.jpg)
- **Dashboard** (`dashboard`): heading "Dashboard", 3.2 screens tall, 3 sections (0 above the fold), 1 tab screens; blue: none

### Designer (Sarah), desktop

- reached by: More › Dashboard (2 taps); shot [desktop](../../review/census/accounting/shots/desktop_designer_dashboard.jpg)
- **Dashboard** (`dashboard`): heading "Dashboard", 3.1 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: none

### Designer (Sarah), phone

- reached by: menu › More › Dashboard (3 taps); shot [phone](../../review/census/accounting/shots/phone_designer_dashboard.jpg)
- **Dashboard** (`dashboard`): heading "Dashboard", 6.0 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: none

### Billing, desktop

- reached by: Banking (1 tap); shot [desktop](../../review/census/accounting/shots/desktop_billing_banking.jpg)
- **Banking** (`bank`): heading "Banking", 3.8 screens tall, 4 sections (2 above the fold), 5 tab screens; blue: Reconcile
- reached by: Reports (1 tap); shot [desktop](../../review/census/accounting/shots/desktop_billing_reports.jpg)
- **Reports** (`reports`): heading "Reports", 3.9 screens tall, 11 sections (4 above the fold), 25 tab screens; blue: none
- reached by: Reports › Dashboard (2 taps); shot [desktop](../../review/census/accounting/shots/desktop_billing_dashboard.jpg)
- **Dashboard** (`dashboard`): heading "Dashboard", 2.1 screens tall, 3 sections (0 above the fold), 2 tab screens; blue: none
- reached by: More (1 tap); shot [desktop](../../review/census/accounting/shots/desktop_billing_bills_payroll.jpg)
- **Bills & Payroll** (`ap`): heading "Bills & Payroll", 1.0 screens tall, 2 sections (2 above the fold), 3 tab screens; blue: New Vendor Bill
- reached by: More › Spend (2 taps); shot [desktop](../../review/census/accounting/shots/desktop_billing_spend.jpg)
- **Spend** (`spend`): heading "Spend", 0.6 screens tall, 0 sections (0 above the fold), 6 tab screens; blue: New Receipt
- reached by: More › Accounting (2 taps); shot [desktop](../../review/census/accounting/shots/desktop_billing_accounting.jpg)
- **Accounting** (`ovmoney`): heading "Accounting", 0.6 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: none

### Billing, phone

- reached by: menu › Banking (2 taps); shot [phone](../../review/census/accounting/shots/phone_billing_banking.jpg)
- **Banking** (`bank`): heading "Banking", 7.5 screens tall, 4 sections (1 above the fold), 5 tab screens; blue: Reconcile; runs past the edge: cut off by pr-m (8/31 · HOUSE OF ANTIQUE HDW CREDIT · +$1, 8/29 · ZELLE TO M RODRIGUEZ M RodriguezC)
- reached by: menu › Reports (2 taps); shot [phone](../../review/census/accounting/shots/phone_billing_reports.jpg)
- **Reports** (`reports`): heading "Company", 7.0 screens tall, 10 sections (2 above the fold), 24 tab screens; blue: none
- reached by: menu › Reports › Dashboard (3 taps); shot [phone](../../review/census/accounting/shots/phone_billing_dashboard.jpg)
- **Dashboard** (`dashboard`): heading "Dashboard", 4.2 screens tall, 3 sections (0 above the fold), 2 tab screens; blue: none
- reached by: menu › More (2 taps); shot [phone](../../review/census/accounting/shots/phone_billing_bills_payroll.jpg)
- **Bills & Payroll** (`ap`): heading "Bills & Payroll", 1.2 screens tall, 2 sections (2 above the fold), 1 tab screens; blue: Review; runs past the edge: cut off by pr-m ($16,040 · due 9/1 · 45 Cranberry St — de)
- reached by: menu › More › Spend (3 taps); shot [phone](../../review/census/accounting/shots/phone_billing_spend.jpg)
- **Spend** (`spend`): heading "Spend", 0.6 screens tall, 0 sections (0 above the fold), 5 tab screens; blue: New Receipt
- reached by: menu › More › Accounting (3 taps); shot [phone](../../review/census/accounting/shots/phone_billing_accounting.jpg)
- **Accounting** (`ovmoney`): heading "Accounting", 0.8 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: none

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

