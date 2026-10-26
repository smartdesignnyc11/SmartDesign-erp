# The Billing Module, Page by Page: the Census

**Asked by Alan, 2026-10-26:** "Go through all the modules with screenshots. It's important to understand the format of every page and what's on it." The loop's experts and the client expert walk every page of their module with this in hand in round one of the improvement loop (docs/IMPROVEMENT_LOOP.md).

**What this is.** A machine inventory, not a judgment, in the format of the Projects census (`docs/modules/projects_census.md`). No app code changed. `tests/module_census.py` (its helpers `tests/module_census_js.js` sit on the projects census's reader `tests/census_js.js` and the information map's `tests/ia_js.js`) signs in as each role on a fresh app at 1440 and at 390, reads the role's running menu, and reaches each page of this module the way the person does: the phone bar, or the menu (the hamburger on the phone), the group, then the strip. It presses every tab of every tab group and the tabs those reveal, follows the page's own links to this module's pages the menu did not reach, reads every screen and shoots it. The primary role is billing; every role whose menu holds a page of this module is walked. Job-scoped pages show **121 State Street** wherever the role may open it.

**Where this module's pages sit.** Billing is one page. Its tabs hold the queue (Ready to Bill), Progress Billing, Estimates, Change Orders, Invoices, Schedule of Values, Payments and Client Funds. The owner reaches it under Accounting, the PM under Projects, billing and the controller from their own Billing entry; the Projects census walks the Change Orders and Estimates strip entries that open the same page on a tab.

**Build bd3180c27e33** (master 1cc2eb9), the one build every module census of this round ran on. 64 screens in all. Walked 2026-10-26 06:29 on the demo day (Thu 2026-09-03); the walk of every module took 54.4 minutes. Raw read: `review/census/billing/data.json`. Every screen per role in tables: `review/census/billing/tables.md`. Screenshots of every screen, both devices: `review/census/billing/shots/` (`desktop_` or `phone_`, the role, the page, then the tab; up to 3 desktop or 5 phone screens tall). The first screen of each page is committed; the tabs stay on the machine that ran it.

Run it: `python3 build.py && cd tests && ./slot.sh python3 module_census.py --module billing` (then `python3 module_census.py --report` rewrites every module's page from data.json).

## Headline

- **Billing: 1 page with 7 more screens behind their tabs on the desktop (1 page and 7 tab screens on the phone)**, about 1 desktop screen end to end.
- **Pages each role reaches in this module, desktop:** Owner 1, PM 1, Billing 1, Controller 1.
- **The same records in other modules** (Billing, desktop): Accounting › Reports lists 20; Tasks and Messages › Tasks lists 6; Projects › Job Page lists 6; Accounting › Dashboard lists 5; Accounting › Spend lists 2 of the 25 records this module lists.
- **One label, different numbers against other modules:** "ready bill" $46K on Billing › Billing against $12,651 on Projects › Job Page (1 in all, section 3).
- **On the phone** (Billing): 1 have no section heading above the fold; 0 screens scroll sideways.
- **Nothing crashed and no page raised an error**; every page opened.
- **Reading changed nothing:** no save during the walk.

## 1. The Tree, Role by Role

**Pages** are the module's pages the role reaches from its menu (and the links those pages show). **Tabs** are the screens behind each page's tab groups, and behind the tabs those reveal. **Sections** are the headed parts of each page as it opens. Each cell reads desktop / phone.

| Role | Primary | First page of the module, reached by (desktop / phone) | Pages | Tab screens | Sections | Screens |
|---|---|---|---|---|---|---|
| Owner |  | Accounting › Billing (2 taps) / menu › Accounting › swipe the strip, Billing (3 taps) | 1 / 1 | 7 / 7 | 0 / 0 | 8 / 8 |
| PM (Alan) |  | Projects › Billing (2 taps) / menu › Projects › swipe the strip, Billing (3 taps) | 1 / 1 | 7 / 7 | 0 / 0 | 8 / 8 |
| Billing | yes | Billing (1 tap) / bar: Billing (1 tap) | 1 / 1 | 7 / 7 | 0 / 0 | 8 / 8 |
| Controller |  | Billing (1 tap) / menu › Billing (2 taps) | 1 / 1 | 7 / 7 | 0 / 0 | 8 / 8 |

### Which pages each role reaches (desktop)

Each cell is the number of screens the page has (the page and its tabs); "-" means the role does not reach it.

| Page | Owner | PM | Billing | Controller |
|---|---|---|---|---|
| Billing | 8 | 8 | 8 | 8 |

### Billing's tree at a glance

Reached by is the taps from the role's first page, desktop then phone. Tall is in screens, desktop / phone. Sections are the headed parts as the page opens (phone above the fold). Tabs are the screens behind its tab groups, desktop / phone. "What it lists" counts the records found on the page as it opens.

| Page | Reached by (desktop / phone) | Heading | Tall | Sections (phone above the fold) | Tabs | Tiles and figures | What it lists | Blue button | First button | Shots |
|---|---|---|---|---|---|---|---|---|---|---|
| Billing | Billing (1 tap) / bar: Billing (1 tap) | Billing | 0.7 / 1.1 | 0 (0) | 7 / 7 | Ready to Bill $46K; Drafts 0; Sent and Unpaid $92K; Overdue $0 | 3 clients, 2 invoices | Draft $17,080 — 45 Cranberry S | Draft $17,080 — 45 Cranberry (blue) | [desktop](../../review/census/billing/shots/desktop_billing_billing.jpg) [phone](../../review/census/billing/shots/phone_billing_billing.jpg) |

### How each page is reached, and the pages reached only one way

Menu places are the role's menu entries that open the page (a page in two groups has two). The phone bar counts as one more way in on the phone (its pages are in the menu too). Links are the walked pages, in any module, that show a link to it. **One way** means one menu place and nothing else: lose that entry and the page is lost.

| Role | Device | Page | Menu places | Phone bar | Linked from | Ways in |
|---|---|---|---|---|---|---|
| Owner | desktop | Billing | Accounting › Billing | - | Company and Settings › The Brain, Today › Chief of Staff | 3 |
| Owner | phone | Billing | Accounting › Billing | - | - | 1 (one way) |
| PM (Alan) | desktop | Billing | Projects › Billing | - | - | 1 (one way) |
| PM (Alan) | phone | Billing | Projects › Billing | - | - | 1 (one way) |
| Billing | desktop | Billing | Billing | - | Sales and Clients › Forecast, Sales and Clients › Sales Dashboard, Today › Today | 4 |
| Billing | phone | Billing | Billing | yes | Sales and Clients › Forecast, Sales and Clients › Sales Dashboard, Today › Today | 5 |
| Controller | desktop | Billing | Billing | - | - | 1 (one way) |
| Controller | phone | Billing | Billing | - | - | 1 (one way) |

## 2. Where the Data Lives, and Where It Shows Twice

Records are found by their own words (the information map's catalog, the job's nouns and this census's: clients, vendors, leads, contacts, companies, every invoice, bill and PO, payroll runs, stock, meetings, journals, obligations, lessons, partners, bank lines, threads), so these are floors. A page's tabs count as the page.

### Billing, desktop: each kind of record, and the pages that list it

| Records | Found | Pages that list them (how many each) | Also in other modules |
|---|---|---|---|
| clients | 3 | 1: Billing 3 | Accounting › Dashboard 3, Accounting › Reports 3, Tasks and Messages › Messages 3, Sales and Clients › Companies 3 |
| schedule lines | 6 | 1: Billing 6 | Accounting › Reports 5, Tasks and Messages › Tasks 4, Projects › Job Page 4, Accounting › Dashboard 2 |
| invoices | 6 | 1: Billing 6 | Accounting › Reports 4 |
| estimates | 4 | 1: Billing 4 | Accounting › Reports 2 |
| materials | 7 | 1: Billing 7 | Accounting › Reports 7, Accounting › Spend 2, Accounting › Dashboard 2, Tasks and Messages › Tasks 2 |
| change orders | 2 | 1: Billing 2 | Projects › Documents 2, Accounting › Reports 2, Accounting › Dashboard 1 |

### Records on two or more pages, and lists that are the same list twice

### The same records in other modules

For each role on the desktop: the pages of other modules (the Projects census's 121 State Street pages included) that list records this module lists, with how many.

- **Owner** (25 records here): Accounting › Reports 20; Projects › Job Page 8; Today › Chief of Staff 8; Company and Settings › Company Settings 8; Projects › Field 7; Projects › Schedule 7; Accounting › Ledger 7; Purchasing › Buy Board 7
- **PM (Alan)** (21 records here): Accounting › Reports 18; Projects › Job Page 8; Today › Chief of Staff 8; Company and Settings › Company Settings 8; Company and Settings › The Brain 8; Projects › Field 7; Projects › Schedule 7; Purchasing › Buy Board 7
- **Billing** (25 records here): Accounting › Reports 20; Tasks and Messages › Tasks 6; Projects › Job Page 6; Accounting › Dashboard 5; Accounting › Spend 2; Projects › Documents 2; Accounting › Banking 2; Today › Chief of Staff 1
- **Controller** (25 records here): Accounting › Reports 20; Accounting › Ledger 7; Purchasing › Purchasing 7; Tasks and Messages › Tasks 6; Accounting › Dashboard 5; Purchasing › Orders 4; Accounting › Spend 2; Today › Chief of Staff 2

Names (clients, vendors, leads, contacts, companies, partners) are left out here: a page that writes a name counts as listing it. A page that is the same page as one of this module's (one view under two menus) is left out too and listed next.

### The same page under two modules' menus

- Owner: Billing here is also Projects › Change Orders, Projects › Estimates, Sales and Clients › Estimates (`billing`)
- PM (Alan): Billing here is also Projects › Billing, Projects › Change Orders, Projects › Estimates (`billing`)

## 3. One Label, Different Numbers

The same label (a tile, a figure, a tab or section count) with numbers that share no value on two pages, for one role. Some are right about different scopes ("Open" against "All", one job against every job); the person still reads one word with two numbers. Each needs a person to judge.

Inside the module: none found.

**Against other modules, Billing, desktop** (1):
- ready bill: $46K on Billing › Billing; $12,651 on Projects › Job Page

## 4. Empty, Dead and Broken Screens

None found.

## 5. The Phone at 390

"Cut off" is text the phone ends early; "scrolls inside" is a strip of tiles or tabs the person swipes sideways inside the page (the page itself does not move). "Strip swipe" counts pages whose strip entry sits off screen until the strip is swiped. Pages taller than 3 phone screens are listed with their height.

| Role | Screens | The page scrolls sideways | Text cut off at the edge | Strips that scroll inside the page | Strip swipe | Pages taller than 3 screens |
|---|---|---|---|---|---|---|
| Owner | 8 | 0 | 1: Billing | 1: Billing | 1: Billing | 0 |
| PM (Alan) | 8 | 0 | 1: Billing | 1: Billing | 1: Billing | 0 |
| Billing | 8 | 0 | 1: Billing | 1: Billing | 0 | 0 |
| Controller | 8 | 0 | 1: Billing | 1: Billing | 0 | 0 |

## 6. Page by Page, in Full

Every page the primary role reaches, as it opens, then each of its tabs. Heights are in screens of that device (900px desktop, 844px phone); "above the fold" is above the bottom bar on the phone.

### Billing, desktop

- reached by: Billing (1 tap); first button "Draft $17,080 — 45 Cranberry St"; shot [desktop](../../review/census/billing/shots/desktop_billing_billing.jpg)
- **Billing** (`billing`): heading "Billing", 0.7 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: Draft $17,080 — 45 Cranberry St
  - lead: "What is ready to bill, what is drafted, what is sent and what is still owed."
  - figures: Ready to Bill $46K; Drafts 0; Sent and Unpaid $92K; Overdue $0
  - records: 3 clients, 2 invoices
  - columns: table: STAGE, WHAT, JOB, AMOUNT, WHERE IT STANDS, NEXT STEP (6 rows)
  - fields: Search…
  - tab groups: Billing Queue / Progress Billing / Estimates 4 / Change Orders 2 / Invoices 6 / Schedule of Values / Payments 4 / Client Funds
  - tab **Progress Billing**: heading "Billing", 6 sections; 6 schedule lines, 6 materials, 2 clients, 1 change orders
  - tab **Estimates**: heading "Billing", 0 sections; 4 estimates, 3 clients
  - tab **Change Orders**: heading "Billing", 0 sections; 2 change orders, 1 clients
  - tab **Invoices**: heading "Billing", 0 sections; 6 invoices, 3 clients
  - tab **Schedule of Values**: heading "Billing", 3 sections; 3 clients
  - tab **Payments**: heading "Billing", 1 sections; 4 invoices, 2 clients
  - tab **Client Funds**: heading "Billing", 3 sections; 4 materials

### Billing, phone

- reached by: bar: Billing (1 tap); first button "Draft $17,080 — 45 Cranberry St"; shot [phone](../../review/census/billing/shots/phone_billing_billing.jpg)
- **Billing** (`billing`): heading "Billing", 1.1 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: Draft $17,080 — 45 Cranberry St
  - lead: "What is ready to bill, what is drafted, what is sent and what is still owed."
  - figures: Ready to Bill $46K; Drafts 0; Sent and Unpaid $92K; Overdue $0
  - records: 3 clients, 2 invoices
  - columns: table: Stage, What, Job, Amount, Where It Stands, Next Step (6 rows)
  - fields: Search…
  - tab groups: Billing Queue / Progress Billing / Estimates 4 / Change Orders 2 / Invoices 6 / Schedule of Values / Payments 4 / Client Funds
  - tab **Progress Billing**: heading "Billing", 6 sections; 6 materials, 2 clients, 1 change orders, 1 schedule lines (runs past the edge: cut off by pr-m (Demolition & disposalContract · 02 · $28, Framing, blocking & rough carpentryContr))
  - tab **Estimates**: heading "Billing", 0 sections; 4 estimates, 3 clients
  - tab **Change Orders**: heading "Billing", 0 sections; 2 change orders, 1 clients
  - tab **Invoices**: heading "Billing", 0 sections; 6 invoices, 3 clients
  - tab **Schedule of Values**: heading "Billing", 3 sections; 3 clients
  - tab **Payments**: heading "Billing", 1 sections; 4 invoices, 2 clients
  - tab **Client Funds**: heading "Client Funds & Purchasing Obligations", 2 sections; 4 materials

## 7. The Other Roles, One Line a Page

### Owner, desktop

- reached by: Accounting › Billing (2 taps); shot [desktop](../../review/census/billing/shots/desktop_owner_billing.jpg)
- **Billing** (`billing`): heading "Billing", 0.7 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: Draft $17,080 — 45 Cranberry St

### Owner, phone

- reached by: menu › Accounting › swipe the strip, Billing (3 taps); shot [phone](../../review/census/billing/shots/phone_owner_billing.jpg)
- **Billing** (`billing`): heading "Billing", 1.1 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: Draft $17,080 — 45 Cranberry St

### PM (Alan), desktop

- reached by: Projects › Billing (2 taps); shot [desktop](../../review/census/billing/shots/desktop_pm_billing.jpg)
- **Billing** (`billing`): heading "Billing", 0.7 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: Draft $17,080 — 45 Cranberry St

### PM (Alan), phone

- reached by: menu › Projects › swipe the strip, Billing (3 taps); shot [phone](../../review/census/billing/shots/phone_pm_billing.jpg)
- **Billing** (`billing`): heading "Billing", 1.1 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: Draft $17,080 — 45 Cranberry St

### Controller, desktop

- reached by: Billing (1 tap); shot [desktop](../../review/census/billing/shots/desktop_controller_billing.jpg)
- **Billing** (`billing`): heading "Billing", 0.7 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: Draft $17,080 — 45 Cranberry St

### Controller, phone

- reached by: menu › Billing (2 taps); shot [phone](../../review/census/billing/shots/phone_controller_billing.jpg)
- **Billing** (`billing`): heading "Billing", 1.1 screens tall, 0 sections (0 above the fold), 7 tab screens; blue: Draft $17,080 — 45 Cranberry St

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

