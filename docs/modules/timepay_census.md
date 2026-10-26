# The Time and Payroll Module, Page by Page: the Census

**Asked by Alan, 2026-10-26:** "Go through all the modules with screenshots. It's important to understand the format of every page and what's on it." The loop's experts and the client expert walk every page of their module with this in hand in round one of the improvement loop (docs/IMPROVEMENT_LOOP.md).

**What this is.** A machine inventory, not a judgment, in the format of the Projects census (`docs/modules/projects_census.md`). No app code changed. `tests/module_census.py` (its helpers `tests/module_census_js.js` sit on the projects census's reader `tests/census_js.js` and the information map's `tests/ia_js.js`) signs in as each role on a fresh app at 1440 and at 390, reads the role's running menu, and reaches each page of this module the way the person does: the phone bar, or the menu (the hamburger on the phone), the group, then the strip. It presses every tab of every tab group and the tabs those reveal, follows the page's own links to this module's pages the menu did not reach, reads every screen and shoots it. The primary role is the controller, the coordinator and the crew; every role whose menu holds a page of this module is walked. Job-scoped pages show **121 State Street** wherever the role may open it.

**Where this module's pages sit.** Time and Payroll is one page (`time`): Time & Crew for the office, Clock for the crew and the driver. Payroll runs are made and approved on Bills & Payroll (its New Payroll Run button and tabs), which sits in the Accounting menu and is in the Accounting census.

**Build bd3180c27e33** (master 1cc2eb9), the one build every module census of this round ran on. 48 screens in all. Walked 2026-10-26 06:29 on the demo day (Thu 2026-09-03); the walk of every module took 54.4 minutes. Raw read: `review/census/timepay/data.json`. Every screen per role in tables: `review/census/timepay/tables.md`. Screenshots of every screen, both devices: `review/census/timepay/shots/` (`desktop_` or `phone_`, the role, the page, then the tab; up to 3 desktop or 5 phone screens tall). The first screen of each page is committed; the tabs stay on the machine that ran it.

Run it: `python3 build.py && cd tests && ./slot.sh python3 module_census.py --module timepay` (then `python3 module_census.py --report` rewrites every module's page from data.json).

## Headline

- **Controller: 1 page with 3 more screens behind their tabs on the desktop (1 page and 3 tab screens on the phone)**, about 1 desktop screen end to end.
- **Coordinator (Chen): 1 page with 3 more screens behind their tabs on the desktop (1 page and 3 tab screens on the phone)**, about 1 desktop screen end to end.
- **Crew (Alberto): 1 page with 3 more screens behind their tabs on the desktop (1 page and 3 tab screens on the phone)**, about 1 desktop screen end to end.
- **Pages each role reaches in this module, desktop:** Owner 1, PM 1, Coordinator 1, Controller 1, Crew 1, Driver 1.
- **Reached only one way** by Coordinator (Chen): Time & Crew (desktop and phone) (one menu entry, not on the phone bar, and no walked page links to it; section 1).
- **Reached only one way** by Crew (Alberto): Clock (desktop) (one menu entry, not on the phone bar, and no walked page links to it; section 1).
- **The same records in other modules** (Controller, desktop): Accounting › Dashboard lists 2; Accounting › Reports lists 2; Accounting › Spend lists 1; Tasks and Messages › Tasks lists 1; Purchasing › Purchasing lists 1 of the 2 records this module lists.
- **On the phone** (Controller): 1 have no section heading above the fold; 0 screens scroll sideways.
- **Nothing crashed and no page raised an error**; every page opened.
- **Reading changed nothing:** no save during the walk.

## 1. The Tree, Role by Role

**Pages** are the module's pages the role reaches from its menu (and the links those pages show). **Tabs** are the screens behind each page's tab groups, and behind the tabs those reveal. **Sections** are the headed parts of each page as it opens. Each cell reads desktop / phone.

| Role | Primary | First page of the module, reached by (desktop / phone) | Pages | Tab screens | Sections | Screens |
|---|---|---|---|---|---|---|
| Owner |  | Accounting › Time & Crew (2 taps) / menu › Accounting › Time & Crew (3 taps) | 1 / 1 | 3 / 3 | 0 / 0 | 4 / 4 |
| PM (Alan) |  | More › Time & Crew (2 taps) / menu › More › swipe the strip, Time & Crew (3 taps) | 1 / 1 | 3 / 3 | 0 / 0 | 4 / 4 |
| Coordinator (Chen) | yes | More (1 tap) / menu › More (2 taps) | 1 / 1 | 3 / 3 | 2 / 2 | 4 / 4 |
| Controller | yes | Bills & Payroll › Time & Crew (2 taps) / menu › Bills & Payroll › Time & Crew (3 taps) | 1 / 1 | 3 / 3 | 0 / 0 | 4 / 4 |
| Crew (Alberto) | yes | Clock (1 tap) / bar: Clock (1 tap) | 1 / 1 | 3 / 3 | 0 / 1 | 4 / 4 |
| Driver (Alex) |  | Clock (1 tap) / bar: Clock (1 tap) | 1 / 1 | 3 / 3 | 0 / 1 | 4 / 4 |

### Which pages each role reaches (desktop)

Each cell is the number of screens the page has (the page and its tabs); "-" means the role does not reach it.

| Page | Owner | PM | Coordinator | Controller | Crew | Driver |
|---|---|---|---|---|---|---|
| Time & Crew | 4 | 4 | 4 | 4 | - | - |
| Clock | - | - | - | - | 4 | 4 |

### Controller's tree at a glance

Reached by is the taps from the role's first page, desktop then phone. Tall is in screens, desktop / phone. Sections are the headed parts as the page opens (phone above the fold). Tabs are the screens behind its tab groups, desktop / phone. "What it lists" counts the records found on the page as it opens.

| Page | Reached by (desktop / phone) | Heading | Tall | Sections (phone above the fold) | Tabs | Tiles and figures | What it lists | Blue button | First button | Shots |
|---|---|---|---|---|---|---|---|---|---|---|
| Time & Crew | Bills & Payroll › Time & Crew (2 taps) / menu › Bills & Payroll › Time & Crew (3 taps) | Time & Crew | 0.6 / 0.8 | 0 (0) | 3 / 3 | Entries to Approve 4; Missing Time 1; On Site Now 0; Overtime 0.0 h | 1 schedule lines | Build Payroll from Approved Ti | Employees | [desktop](../../review/census/timepay/shots/desktop_controller_time_crew.jpg) [phone](../../review/census/timepay/shots/phone_controller_time_crew.jpg) |

### Coordinator (Chen)'s tree at a glance

Reached by is the taps from the role's first page, desktop then phone. Tall is in screens, desktop / phone. Sections are the headed parts as the page opens (phone above the fold). Tabs are the screens behind its tab groups, desktop / phone. "What it lists" counts the records found on the page as it opens.

| Page | Reached by (desktop / phone) | Heading | Tall | Sections (phone above the fold) | Tabs | Tiles and figures | What it lists | Blue button | First button | Shots |
|---|---|---|---|---|---|---|---|---|---|---|
| Time & Crew | More (1 tap) / menu › More (2 taps) | Time & Crew | 1.2 / 1.8 | 2 (1) | 3 / 3 | Entries to Approve 4; Missing Time 1; On Site Now 0; Overtime 0.0 h | 3 schedule lines, 1 stock items | none | Employees | [desktop](../../review/census/timepay/shots/desktop_coord_time_crew.jpg) [phone](../../review/census/timepay/shots/phone_coord_time_crew.jpg) |

### Crew (Alberto)'s tree at a glance

Reached by is the taps from the role's first page, desktop then phone. Tall is in screens, desktop / phone. Sections are the headed parts as the page opens (phone above the fold). Tabs are the screens behind its tab groups, desktop / phone. "What it lists" counts the records found on the page as it opens.

| Page | Reached by (desktop / phone) | Heading | Tall | Sections (phone above the fold) | Tabs | Tiles and figures | What it lists | Blue button | First button | Shots |
|---|---|---|---|---|---|---|---|---|---|---|
| Clock | Clock (1 tap) / bar: Clock (1 tap) | Clock | 0.8 / 2.0 | 0 (1) | 3 / 3 | - | 4 schedule lines | Clock In | Clock In (blue) | [desktop](../../review/census/timepay/shots/desktop_crew_clock.jpg) [phone](../../review/census/timepay/shots/phone_crew_clock.jpg) |

### How each page is reached, and the pages reached only one way

Menu places are the role's menu entries that open the page (a page in two groups has two). The phone bar counts as one more way in on the phone (its pages are in the menu too). Links are the walked pages, in any module, that show a link to it. **One way** means one menu place and nothing else: lose that entry and the page is lost.

| Role | Device | Page | Menu places | Phone bar | Linked from | Ways in |
|---|---|---|---|---|---|---|
| Owner | desktop | Time & Crew | Accounting › Time & Crew | - | Accounting › Accounting | 2 |
| Owner | phone | Time & Crew | Accounting › Time & Crew | - | Accounting › Accounting | 2 |
| PM (Alan) | desktop | Time & Crew | More › Time & Crew | - | Accounting › Accounting, Today › Approvals | 3 |
| PM (Alan) | phone | Time & Crew | More › Time & Crew | - | Accounting › Accounting, Today › Approvals | 3 |
| Coordinator (Chen) | desktop | Time & Crew | More › Time & Crew | - | - | 1 (one way) |
| Coordinator (Chen) | phone | Time & Crew | More › Time & Crew | - | - | 1 (one way) |
| Controller | desktop | Time & Crew | Bills & Payroll › Time & Crew | - | Accounting › Accounting | 2 |
| Controller | phone | Time & Crew | Bills & Payroll › Time & Crew | - | Accounting › Accounting | 2 |
| Crew (Alberto) | desktop | Clock | Clock | - | - | 1 (one way) |
| Crew (Alberto) | phone | Clock | Clock | yes | - | 2 |
| Driver (Alex) | desktop | Clock | Clock | - | - | 1 (one way) |
| Driver (Alex) | phone | Clock | Clock | yes | - | 2 |

## 2. Where the Data Lives, and Where It Shows Twice

Records are found by their own words (the information map's catalog, the job's nouns and this census's: clients, vendors, leads, contacts, companies, every invoice, bill and PO, payroll runs, stock, meetings, journals, obligations, lessons, partners, bank lines, threads), so these are floors. A page's tabs count as the page.

### Controller, desktop: each kind of record, and the pages that list it

| Records | Found | Pages that list them (how many each) | Also in other modules |
|---|---|---|---|
| materials | 1 | 1: Time & Crew 1 | Accounting › Spend 1, Accounting › Dashboard 1, Tasks and Messages › Tasks 1, Purchasing › Purchasing 1 |
| schedule lines | 1 | 1: Time & Crew 1 | Accounting › Dashboard 1, Today › Chief of Staff 1, Accounting › Reports 1, Company and Settings › The Brain 1 |

### Records on two or more pages, and lists that are the same list twice

### The same records in other modules

For each role on the desktop: the pages of other modules (the Projects census's 121 State Street pages included) that list records this module lists, with how many.

- **Owner** (2 records here): Accounting › Dashboard 2; Today › Chief of Staff 2; Accounting › Reports 2; Company and Settings › Company Settings 2; Projects › Job Page 2; Projects › Field 2; Projects › Schedule 2; Projects › Costs 2
- **PM (Alan)** (2 records here): Accounting › Dashboard 2; Today › Chief of Staff 2; Company and Settings › Company Settings 2; Accounting › Reports 2; Projects › Job Page 2; Company and Settings › The Brain 2; Projects › Field 2; Projects › Schedule 2
- **Coordinator (Chen)** (5 records here): Accounting › Dashboard 4; Projects › Job Page 4; Projects › Schedule 4; Field and Site › Requests 4; Purchasing › Buy Board 3; Today › Chief of Staff 2; Company and Settings › The Brain 2; Projects › Field 2
- **Controller** (2 records here): Accounting › Dashboard 2; Accounting › Reports 2; Accounting › Spend 1; Tasks and Messages › Tasks 1; Purchasing › Purchasing 1; Billing › Billing 1; Today › Chief of Staff 1; Company and Settings › The Brain 1
- **Crew (Alberto)** (4 records here): Field and Site › Schedule 4; Field and Site › Requests 2
- **Driver (Alex)** (4 records here): Field and Site › Requests 2

Names (clients, vendors, leads, contacts, companies, partners) are left out here: a page that writes a name counts as listing it. A page that is the same page as one of this module's (one view under two menus) is left out too and listed next.

### The same page under two modules' menus

None found.

## 3. One Label, Different Numbers

The same label (a tile, a figure, a tab or section count) with numbers that share no value on two pages, for one role. Some are right about different scopes ("Open" against "All", one job against every job); the person still reads one word with two numbers. Each needs a person to judge.

Inside the module: none found.

Against other modules, Controller, desktop: none found.

**Against other modules, Coordinator (Chen), desktop** (1):
- site: 2 on Purchasing › Stock; 0 on Time and Payroll › Time & Crew

Against other modules, Crew (Alberto), desktop: none found.

## 4. Empty, Dead and Broken Screens

| Device | Role | Screen | What |
|---|---|---|---|
| phone | Driver (Alex) | Clock | lists nothing: "Nothing on the schedule with your name today — ask in Chat o" |

## 5. The Phone at 390

"Cut off" is text the phone ends early; "scrolls inside" is a strip of tiles or tabs the person swipes sideways inside the page (the page itself does not move). "Strip swipe" counts pages whose strip entry sits off screen until the strip is swiped. Pages taller than 3 phone screens are listed with their height.

| Role | Screens | The page scrolls sideways | Text cut off at the edge | Strips that scroll inside the page | Strip swipe | Pages taller than 3 screens |
|---|---|---|---|---|---|---|
| Owner | 4 | 0 | 0 | 1: Time & Crew | 0 | 0 |
| PM (Alan) | 4 | 0 | 0 | 1: Time & Crew | 1: Time & Crew | 0 |
| Coordinator (Chen) | 4 | 0 | 0 | 1: Time & Crew | 0 | 0 |
| Controller | 4 | 0 | 0 | 1: Time & Crew | 0 | 0 |
| Crew (Alberto) | 4 | 0 | 0 | 1: Clock | 0 | 0 |
| Driver (Alex) | 4 | 0 | 0 | 1: Clock | 0 | 0 |

## 6. Page by Page, in Full

Every page the primary role reaches, as it opens, then each of its tabs. Heights are in screens of that device (900px desktop, 844px phone); "above the fold" is above the bottom bar on the phone.

### Controller, desktop

- reached by: Bills & Payroll › Time & Crew (2 taps); first button "Employees"; shot [desktop](../../review/census/timepay/shots/desktop_controller_time_crew.jpg)
- **Time & Crew** (`time`): heading "Time & Crew", 0.6 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: Build Payroll from Approved Time
  - lead: "Crew clock in and out on their phones with location. Approved hours become payroll and labor cost."
  - figures: Entries to Approve 4; Missing Time 1; On Site Now 0; Overtime 0.0 h
  - records: 1 schedule lines
  - columns: table: DATE, EMPLOYEE, IN, OUT, HOURS, WORK, LOCATION, STATUS (4 rows)
  - fields: Search…
  - tab groups: Awaiting Approval / This Week / Approved · Unpaid / All
  - tab **This Week**: heading "Time & Crew", 0 sections; 1 schedule lines, 1 materials
  - tab **Approved · Unpaid**: heading "Time & Crew", 0 sections; 1 schedule lines, 1 materials
  - tab **All**: heading "Time & Crew", 0 sections; 1 schedule lines, 1 materials

### Controller, phone

- reached by: menu › Bills & Payroll › Time & Crew (3 taps); first button "Employees"; shot [phone](../../review/census/timepay/shots/phone_controller_time_crew.jpg)
- **Time & Crew** (`time`): heading "Time & Crew", 0.8 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: Build Payroll from Approved Time
  - lead: "Crew clock in and out on their phones with location. Approved hours become payroll and labor cost."
  - figures: Entries to Approve 4; Missing Time 1; On Site Now 0; Overtime 0.0 h
  - columns: table: Date, Employee, In, Out, Hours, Work, Location, Status (4 rows)
  - fields: Search…
  - tab groups: Awaiting Approval / This Week / Approved · Unpaid / All
  - tab **This Week**: heading "Time & Crew", 0 sections
  - tab **Approved · Unpaid**: heading "Time & Crew", 0 sections
  - tab **All**: heading "Time & Crew", 0 sections

### Coordinator (Chen), desktop

- reached by: More (1 tap); first button "Employees"; shot [desktop](../../review/census/timepay/shots/desktop_coord_time_crew.jpg)
- **Time & Crew** (`time`): heading "Time & Crew", 1.2 screens tall, 2 sections (2 above the fold), 3 tab screens; blue: none
  - lead: "Crew clock in and out on their phones with location. Approved hours become payroll and labor cost."
  - sections: Missing Hours (5); Payroll Run
  - figures: Entries to Approve 4; Missing Time 1; On Site Now 0; Overtime 0.0 h
  - records: 3 schedule lines, 1 stock items
  - columns: table: DATE, EMPLOYEE, IN, OUT, HOURS, WORK, LOCATION, STATUS (4 rows)
  - fields: Search…
  - empty states: "No time for Thu, Aug 27, Fri, Aug 28, Mon, Aug 31, Tue, Sep 1, Wed, Sep 2."
  - tab groups: Awaiting Approval / This Week / Approved · Unpaid / All
  - tab **This Week**: heading "Time & Crew", 2 sections; 3 schedule lines, 1 materials, 1 stock items
  - tab **Approved · Unpaid**: heading "Time & Crew", 2 sections; 3 schedule lines, 1 materials, 1 stock items
  - tab **All**: heading "Time & Crew", 2 sections; 3 schedule lines, 1 materials, 1 stock items

### Coordinator (Chen), phone

- reached by: menu › More (2 taps); first button "Employees"; shot [phone](../../review/census/timepay/shots/phone_coord_time_crew.jpg)
- **Time & Crew** (`time`): heading "Time & Crew", 1.8 screens tall, 2 sections (1 above the fold), 3 tab screens; blue: none
  - lead: "Crew clock in and out on their phones with location. Approved hours become payroll and labor cost."
  - sections: Missing Hours (5); Payroll Run
  - figures: Entries to Approve 4; Missing Time 1; On Site Now 0; Overtime 0.0 h
  - records: 2 schedule lines, 1 stock items
  - columns: table: Date, Employee, In, Out, Hours, Work, Location, Status (4 rows)
  - fields: Search…
  - empty states: "No time for Thu, Aug 27, Fri, Aug 28, Mon, Aug 31, Tue, Sep 1, Wed, Sep 2."
  - tab groups: Awaiting Approval / This Week / Approved · Unpaid / All
  - tab **This Week**: heading "Time & Crew", 2 sections; 2 schedule lines, 1 stock items
  - tab **Approved · Unpaid**: heading "Time & Crew", 2 sections; 2 schedule lines, 1 stock items
  - tab **All**: heading "Time & Crew", 2 sections; 2 schedule lines, 1 stock items

### Crew (Alberto), desktop

- reached by: Clock (1 tap); first button "Clock In"; shot [desktop](../../review/census/timepay/shots/desktop_crew_clock.jpg)
- **Clock** (`time`): heading "Clock", 0.8 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: Clock In
  - lead: "Crew clock in and out on their phones with location. Approved hours become payroll and labor cost."
  - records: 4 schedule lines
  - columns: table: DATE, EMPLOYEE, IN, OUT, HOURS, WORK, LOCATION, STATUS (1 rows)
  - fields: Ask about the company — “what's due this, Search…
  - tab groups: Awaiting Approval / This Week / Approved · Unpaid / All
  - tab **This Week**: heading "Clock", 0 sections; 4 schedule lines
  - tab **Approved · Unpaid**: heading "Clock", 0 sections; 4 schedule lines
  - tab **All**: heading "Clock", 0 sections; 4 schedule lines

### Crew (Alberto), phone

- reached by: bar: Clock (1 tap); first button "Clock In"; shot [phone](../../review/census/timepay/shots/phone_crew_clock.jpg)
- **Clock** (`time`): heading "Clock", 2.0 screens tall, 1 sections (1 above the fold), 3 tab screens; blue: Clock In
  - lead: "Crew clock in and out on their phones with location. Approved hours become payroll and labor cost."
  - sections: Today
  - records: 5 schedule lines, 1 field requests, 1 materials
  - columns: table: Date, Employee, In, Out, Hours, Work, Location, Status (1 rows)
  - fields: Search…
  - tab groups: Awaiting Approval / This Week / Approved · Unpaid / All
  - tab **This Week**: heading "Clock", 1 sections; 5 schedule lines, 1 field requests, 1 materials
  - tab **Approved · Unpaid**: heading "Clock", 1 sections; 5 schedule lines, 1 field requests, 1 materials
  - tab **All**: heading "Clock", 1 sections; 5 schedule lines, 1 field requests, 1 materials

## 7. The Other Roles, One Line a Page

### Owner, desktop

- reached by: Accounting › Time & Crew (2 taps); shot [desktop](../../review/census/timepay/shots/desktop_owner_time_crew.jpg)
- **Time & Crew** (`time`): heading "Time & Crew", 0.6 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: Build Payroll from Approved Time

### Owner, phone

- reached by: menu › Accounting › Time & Crew (3 taps); shot [phone](../../review/census/timepay/shots/phone_owner_time_crew.jpg)
- **Time & Crew** (`time`): heading "Time & Crew", 0.9 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: Build Payroll from Approved Time

### PM (Alan), desktop

- reached by: More › Time & Crew (2 taps); shot [desktop](../../review/census/timepay/shots/desktop_pm_time_crew.jpg)
- **Time & Crew** (`time`): heading "Time & Crew", 0.6 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: Build Payroll from Approved Time

### PM (Alan), phone

- reached by: menu › More › swipe the strip, Time & Crew (3 taps); shot [phone](../../review/census/timepay/shots/phone_pm_time_crew.jpg)
- **Time & Crew** (`time`): heading "Time & Crew", 0.9 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: Build Payroll from Approved Time

### Driver (Alex), desktop

- reached by: Clock (1 tap); shot [desktop](../../review/census/timepay/shots/desktop_driver_clock.jpg)
- **Clock** (`time`): heading "Clock", 0.7 screens tall, 0 sections (0 above the fold), 3 tab screens; blue: Clock In

### Driver (Alex), phone

- reached by: bar: Clock (1 tap); shot [phone](../../review/census/timepay/shots/phone_driver_clock.jpg)
- **Clock** (`time`): heading "Clock", 0.9 screens tall, 1 sections (1 above the fold), 3 tab screens; blue: Clock In

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

