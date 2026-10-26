# The Design Module, Page by Page: the Census

**Asked by Alan, 2026-10-26:** "Go through all the modules with screenshots. It's important to understand the format of every page and what's on it." The loop's experts and the client expert walk every page of their module with this in hand in round one of the improvement loop (docs/IMPROVEMENT_LOOP.md).

**What this is.** A machine inventory, not a judgment, in the format of the Projects census (`docs/modules/projects_census.md`). No app code changed. `tests/module_census.py` (its helpers `tests/module_census_js.js` sit on the projects census's reader `tests/census_js.js` and the information map's `tests/ia_js.js`) signs in as each role on a fresh app at 1440 and at 390, reads the role's running menu, and reaches each page of this module the way the person does: the phone bar, or the menu (the hamburger on the phone), the group, then the strip. It presses every tab of every tab group and the tabs those reveal, follows the page's own links to this module's pages the menu did not reach, reads every screen and shoots it. The primary role is the designer and the PM; every role whose menu holds a page of this module is walked. Job-scoped pages show **121 State Street** wherever the role may open it.

**Where this module's pages sit.** The PM's Drawings sits in the Projects menu group (the Projects census); the PM reaches Project Board, Filings, Selections and Design through More. The coordinator reaches Selections through More.

**Build bd3180c27e33** (master 1cc2eb9), the one build every module census of this round ran on. 92 screens in all. Walked 2026-10-26 06:29 on the demo day (Thu 2026-09-03); the walk of every module took 54.4 minutes. Raw read: `review/census/design/data.json`. Every screen per role in tables: `review/census/design/tables.md`. Screenshots of every screen, both devices: `review/census/design/shots/` (`desktop_` or `phone_`, the role, the page, then the tab; up to 3 desktop or 5 phone screens tall). The first screen of each page is committed; the tabs stay on the machine that ran it.

Run it: `python3 build.py && cd tests && ./slot.sh python3 module_census.py --module design` (then `python3 module_census.py --report` rewrites every module's page from data.json).

## Headline

- **Designer (Sarah): 5 pages with 8 more screens behind their tabs on the desktop (5 pages and 8 tab screens on the phone)**, about 7 desktop screens end to end.
- **PM (Alan): 5 pages with 8 more screens behind their tabs on the desktop (5 pages and 8 tab screens on the phone)**, about 5 desktop screens end to end.
- **Pages each role reaches in this module, desktop:** Owner 6, PM 5, Coordinator 1, Designer 5.
- **Reached only one way** by Designer (Sarah): Design (desktop and phone), Drawings (desktop), Filings (desktop and phone), Project Board (desktop and phone), Selections (desktop and phone) (one menu entry, not on the phone bar, and no walked page links to it; section 1).
- **Reached only one way** by PM (Alan): Design (desktop and phone), Filings (desktop and phone), Project Board (desktop and phone), Selections (phone) (one menu entry, not on the phone bar, and no walked page links to it; section 1).
- **1 records show on two or more of this module's pages** for Designer (Sarah) on the desktop (1 clients). "Sarah & David Klein" is on 2: Design, Project Board.
- **The same records in other modules** (Designer, desktop): Accounting › Dashboard lists 15; Projects › Decisions lists 9; Today › Today lists 8; Tasks and Messages › Tasks lists 4; Projects › Documents lists 1 of the 28 records this module lists.
- **On the phone** (Designer): 1 of the 5 pages are taller than three screens (Drawings); 1 have no section heading above the fold; 0 screens scroll sideways.
- **Nothing crashed and no page raised an error**; every page opened.
- **Reading changed nothing:** no save during the walk.

## 1. The Tree, Role by Role

**Pages** are the module's pages the role reaches from its menu (and the links those pages show). **Tabs** are the screens behind each page's tab groups, and behind the tabs those reveal. **Sections** are the headed parts of each page as it opens. Each cell reads desktop / phone.

| Role | Primary | First page of the module, reached by (desktop / phone) | Pages | Tab screens | Sections | Screens |
|---|---|---|---|---|---|---|
| Owner |  | Design (1 tap) / menu › Design (2 taps) | 6 / 6 | 8 / 8 | 19 / 19 | 14 / 14 |
| PM (Alan) | yes | More › Project Board (2 taps) / menu › More › swipe the strip, Project Board (3 taps) | 5 / 5 | 8 / 8 | 16 / 16 | 13 / 13 |
| Coordinator (Chen) |  | More › Selections (2 taps) / menu › More › swipe the strip, Selections (3 taps) | 1 / 1 | 5 / 5 | 0 / 0 | 6 / 6 |
| Designer (Sarah) | yes | Drawings (1 tap) / bar: Drawings (1 tap) | 5 / 5 | 8 / 8 | 17 / 17 | 13 / 13 |

### Which pages each role reaches (desktop)

Each cell is the number of screens the page has (the page and its tabs); "-" means the role does not reach it.

| Page | Owner | PM | Coordinator | Designer |
|---|---|---|---|---|
| Design | 1 | 1 | - | 1 |
| Project Board | 4 | 4 | - | 4 |
| Drawings | 1 | - | - | 1 |
| Filings | 1 | 1 | - | 1 |
| Selections | 6 | 6 | 6 | 6 |
| Design (by the link 2 projects need attention) | 1 | 1 | - | - |

### Designer (Sarah)'s tree at a glance

Reached by is the taps from the role's first page, desktop then phone. Tall is in screens, desktop / phone. Sections are the headed parts as the page opens (phone above the fold). Tabs are the screens behind its tab groups, desktop / phone. "What it lists" counts the records found on the page as it opens.

| Page | Reached by (desktop / phone) | Heading | Tall | Sections (phone above the fold) | Tabs | Tiles and figures | What it lists | Blue button | First button | Shots |
|---|---|---|---|---|---|---|---|---|---|---|
| Drawings | Drawings (1 tap) / bar: Drawings (1 tap) | Drawings — 121 State Street | 3.1 / 5.8 | 3 (1) | 0 / 0 | Found Before Work 0; Found in the Field 1; Rework Avoided $0; Our Cost $0 | 2 vendors, 1 schedule lines, 1 subs to confirm, 1 files | New Revision | Mark in Revision | [desktop](../../review/census/design/shots/desktop_designer_drawings.jpg) [phone](../../review/census/design/shots/phone_designer_drawings.jpg) |
| Design | Design (1 tap) / menu › Design (2 taps) | Design | 0.9 / 1.2 | 2 (2) | 0 / 0 | Projects to Survey 1; Sets to Re-Issue 1; Over Hours or Gated 1; At the Agency 1 | 5 schedule lines, 3 clients | none | Projects to Survey 1 11 room | [desktop](../../review/census/design/shots/desktop_designer_design.jpg) [phone](../../review/census/design/shots/phone_designer_design.jpg) |
| Project Board | Design › Project Board (2 taps) / menu › Design › Project Board (3 taps) | Project Board | 1.0 / 2.8 | 11 (2) | 3 / 3 | - | 1 clients | none | New Room | [desktop](../../review/census/design/shots/desktop_designer_project_board.jpg) [phone](../../review/census/design/shots/phone_designer_project_board.jpg) |
| Filings | Design › Filings (2 taps) / menu › Design › Filings (3 taps) | Filings | 0.4 / 0.6 | 1 (1) | 0 / 0 | - | - | none | none | [desktop](../../review/census/design/shots/desktop_designer_filings.jpg) [phone](../../review/census/design/shots/phone_designer_filings.jpg) |
| Selections | Design › Selections (2 taps) / menu › Design › Selections (3 taps) | Selections — 121 State Street | 1.5 / 1.1 | 0 (0) | 5 / 5 | Red Flags 4; To Check 4; Awaiting Approval 2; Still to Buy 5 | 8 materials, 5 vendors, 3 selections | Clip an Item | Get Clips | [desktop](../../review/census/design/shots/desktop_designer_selections.jpg) [phone](../../review/census/design/shots/phone_designer_selections.jpg) |

### PM (Alan)'s tree at a glance

Reached by is the taps from the role's first page, desktop then phone. Tall is in screens, desktop / phone. Sections are the headed parts as the page opens (phone above the fold). Tabs are the screens behind its tab groups, desktop / phone. "What it lists" counts the records found on the page as it opens.

| Page | Reached by (desktop / phone) | Heading | Tall | Sections (phone above the fold) | Tabs | Tiles and figures | What it lists | Blue button | First button | Shots |
|---|---|---|---|---|---|---|---|---|---|---|
| Project Board | More › Project Board (2 taps) / menu › More › swipe the strip, Project Board (3 taps) | Project Board | 1.0 / 2.8 | 11 (2) | 3 / 3 | - | 1 clients | none | New Room | [desktop](../../review/census/design/shots/desktop_pm_project_board.jpg) [phone](../../review/census/design/shots/phone_pm_project_board.jpg) |
| Filings | More › Filings (2 taps) / menu › More › swipe the strip, Filings (3 taps) | Filings | 0.4 / 0.6 | 1 (1) | 0 / 0 | - | - | none | none | [desktop](../../review/census/design/shots/desktop_pm_filings.jpg) [phone](../../review/census/design/shots/phone_pm_filings.jpg) |
| Selections | More › Selections (2 taps) / menu › More › swipe the strip, Selections (3 taps) | Selections | 1.5 / 1.1 | 0 (0) | 5 / 5 | Red Flags 4; To Check 4; Awaiting Approval 2; Still to Buy 5 | 8 materials, 5 vendors, 3 selections | Clip an Item | Get Clips | [desktop](../../review/census/design/shots/desktop_pm_selections.jpg) [phone](../../review/census/design/shots/phone_pm_selections.jpg) |
| Design | More › Design (2 taps) / menu › More › swipe the strip, Design (3 taps) | Design | 0.9 / 1.2 | 2 (2) | 0 / 0 | Projects to Survey 1; Sets to Re-Issue 1; Over Hours or Gated 1; At the Agency 1 | 5 schedule lines, 3 clients | none | Projects to Survey 1 11 room | [desktop](../../review/census/design/shots/desktop_pm_design.jpg) [phone](../../review/census/design/shots/phone_pm_design.jpg) |
| Design (by the link 2 projects need attention) | Design › link: 2 projects need attention / Design › link: 2 projects need attention | Design | 0.9 / 1.2 | 2 (2) | 0 / 0 | Projects to Survey 1; Sets to Re-Issue 1; Over Hours or Gated 1; At the Agency 1 | 5 schedule lines, 3 clients | none | Projects to Survey 1 11 room | [desktop](../../review/census/design/shots/desktop_pm_2_projects_need_attention.jpg) [phone](../../review/census/design/shots/phone_pm_2_projects_need_attention.jpg) |

### How each page is reached, and the pages reached only one way

Menu places are the role's menu entries that open the page (a page in two groups has two). The phone bar counts as one more way in on the phone (its pages are in the menu too). Links are the walked pages, in any module, that show a link to it. **One way** means one menu place and nothing else: lose that entry and the page is lost.

| Role | Device | Page | Menu places | Phone bar | Linked from | Ways in |
|---|---|---|---|---|---|---|
| Owner | desktop | Design | Design | - | - | 1 (one way) |
| Owner | desktop | Project Board | Design › Project Board | - | - | 1 (one way) |
| Owner | desktop | Drawings | Projects › Drawings; Design › Drawings | - | - | 2 |
| Owner | desktop | Filings | Design › Filings | - | - | 1 (one way) |
| Owner | desktop | Selections | Design › Selections | - | Accounting › Banking, Time and Payroll › Time & Crew | 3 |
| Owner | desktop | Design (by the link 2 projects need attention) | none (reached by a link) | - | - | 0 |
| Owner | phone | Design | Design | - | - | 1 (one way) |
| Owner | phone | Project Board | Design › Project Board | - | - | 1 (one way) |
| Owner | phone | Drawings | Projects › Drawings; Design › Drawings | - | - | 2 |
| Owner | phone | Filings | Design › Filings | - | - | 1 (one way) |
| Owner | phone | Selections | Design › Selections | - | - | 1 (one way) |
| Owner | phone | Design (by the link 2 projects need attention) | none (reached by a link) | - | - | 0 |
| PM (Alan) | desktop | Project Board | More › Project Board | - | - | 1 (one way) |
| PM (Alan) | desktop | Filings | More › Filings | - | - | 1 (one way) |
| PM (Alan) | desktop | Selections | More › Selections | - | Accounting › Banking, Time and Payroll › Time & Crew | 3 |
| PM (Alan) | desktop | Design | More › Design | - | - | 1 (one way) |
| PM (Alan) | desktop | Design (by the link 2 projects need attention) | none (reached by a link) | - | - | 0 |
| PM (Alan) | phone | Project Board | More › Project Board | - | - | 1 (one way) |
| PM (Alan) | phone | Filings | More › Filings | - | - | 1 (one way) |
| PM (Alan) | phone | Selections | More › Selections | - | - | 1 (one way) |
| PM (Alan) | phone | Design | More › Design | - | - | 1 (one way) |
| PM (Alan) | phone | Design (by the link 2 projects need attention) | none (reached by a link) | - | - | 0 |
| Coordinator (Chen) | desktop | Selections | More › Selections | - | Time and Payroll › Time & Crew | 2 |
| Coordinator (Chen) | phone | Selections | More › Selections | - | - | 1 (one way) |
| Designer (Sarah) | desktop | Drawings | Drawings | - | - | 1 (one way) |
| Designer (Sarah) | desktop | Design | Design | - | - | 1 (one way) |
| Designer (Sarah) | desktop | Project Board | Design › Project Board | - | - | 1 (one way) |
| Designer (Sarah) | desktop | Filings | Design › Filings | - | - | 1 (one way) |
| Designer (Sarah) | desktop | Selections | Design › Selections | - | - | 1 (one way) |
| Designer (Sarah) | phone | Drawings | Drawings | yes | - | 2 |
| Designer (Sarah) | phone | Design | Design | - | - | 1 (one way) |
| Designer (Sarah) | phone | Project Board | Design › Project Board | - | - | 1 (one way) |
| Designer (Sarah) | phone | Filings | Design › Filings | - | - | 1 (one way) |
| Designer (Sarah) | phone | Selections | Design › Selections | - | - | 1 (one way) |

**Pages of this module the role may open (ROLE_VIEWS) that no menu entry of this module or walked link reached.** Where the census landed on the page from another module (a tab that leaves, another group's entry), that place is named; "not reached" means no walked screen showed it, which for most is a retired page that lands on another (MN_ALIAS, OC_RETIRED) and is left to search and old links.

- Owner, desktop: `sdraw` (not reached)
- Owner, phone: `sdraw` (not reached)
- PM (Alan), desktop: `plans` (reached as Projects › Drawings); `sdraw` (not reached)
- PM (Alan), phone: `plans` (reached as Projects › Drawings); `sdraw` (not reached)
- Coordinator (Chen), desktop: `plans` (reached as Projects › Drawings)
- Coordinator (Chen), phone: `plans` (reached as Projects › Drawings)
- Designer (Sarah), desktop: `sdraw` (not reached)
- Designer (Sarah), phone: `sdraw` (not reached)

## 2. Where the Data Lives, and Where It Shows Twice

Records are found by their own words (the information map's catalog, the job's nouns and this census's: clients, vendors, leads, contacts, companies, every invoice, bill and PO, payroll runs, stock, meetings, journals, obligations, lessons, partners, bank lines, threads), so these are floors. A page's tabs count as the page.

### Designer (Sarah), desktop: each kind of record, and the pages that list it

| Records | Found | Pages that list them (how many each) | Also in other modules |
|---|---|---|---|
| vendors | 7 | 2: Selections 5, Drawings 2 | Tasks and Messages › Tasks 1 |
| schedule lines | 6 | 2: Design 5, Drawings 1 | Accounting › Dashboard 4, Tasks and Messages › Tasks 3, Today › Today 1 |
| clients | 3 | 2: Design 3, Project Board 1 | Tasks and Messages › Messages 3, Sales and Clients › Clients 3 |
| materials | 9 | 2: Selections 8, Project Board 1 | Accounting › Dashboard 5, Today › Today 1, Projects › Decisions 1 |
| files | 1 | 1: Drawings 1 | Projects › Documents 1 |
| subs to confirm | 1 | 1: Drawings 1 | - |
| decisions | 8 | 1: Project Board 8 | Projects › Decisions 8, Today › Today 6, Accounting › Dashboard 6, Tasks and Messages › Tasks 1 |
| selections | 3 | 1: Selections 3 | - |

### Records on two or more pages, and lists that are the same list twice

**Owner, desktop:** 8 records on two or more pages: schedule lines 5 (up to 2 pages); clients 3 (up to 3 pages).

- the same list twice (3 or more shared records, at least half of the shorter list): Design and Design (by the link 2 projects need attention) (5 shared, of 5 and 5: schedule lines)

**PM (Alan), desktop:** 8 records on two or more pages: schedule lines 5 (up to 2 pages); clients 3 (up to 3 pages).

- "Sarah & David Klein" (clients) on 3 pages: Design, Design (by the link 2 projects need attention), Project Board
- "Existing-conditions survey — every room, every crevice" (schedule lines) on 2 pages: Design, Design (by the link 2 projects need attention)
- "Kitchen option 3 — antique island, sink under arched window" (schedule lines) on 2 pages: Design, Design (by the link 2 projects need attention)
- "Primary bath / dressing options (angled tub, WC compartment," (schedule lines) on 2 pages: Design, Design (by the link 2 projects need attention)
- "Design development" (schedule lines) on 2 pages: Design, Design (by the link 2 projects need attention)
- "LPC Certificate of Appropriateness" (schedule lines) on 2 pages: Design, Design (by the link 2 projects need attention)
- the same list twice (3 or more shared records, at least half of the shorter list): Design and Design (by the link 2 projects need attention) (5 shared, of 5 and 5: schedule lines)

**Designer (Sarah), desktop:** 1 records on two or more pages: clients 1 (up to 2 pages).

- "Sarah & David Klein" (clients) on 2 pages: Design, Project Board

**PM (Alan), phone:** 7 records on two or more pages: schedule lines 4 (up to 2 pages); clients 3 (up to 3 pages).

- "Sarah & David Klein" (clients) on 3 pages: Design, Design (by the link 2 projects need attention), Project Board
- "Existing-conditions survey — every room, every crevice" (schedule lines) on 2 pages: Design, Design (by the link 2 projects need attention)
- "Kitchen option 3 — antique island, sink under arched window" (schedule lines) on 2 pages: Design, Design (by the link 2 projects need attention)
- "Primary bath / dressing options (angled tub, WC compartment," (schedule lines) on 2 pages: Design, Design (by the link 2 projects need attention)
- "Design development" (schedule lines) on 2 pages: Design, Design (by the link 2 projects need attention)
- "Rivera family" (clients) on 2 pages: Design, Design (by the link 2 projects need attention)
- the same list twice (3 or more shared records, at least half of the shorter list): Design and Design (by the link 2 projects need attention) (4 shared, of 4 and 4: schedule lines)

**Designer (Sarah), phone:** 1 records on two or more pages: clients 1 (up to 2 pages).

- "Sarah & David Klein" (clients) on 2 pages: Design, Project Board

### The same records in other modules

For each role on the desktop: the pages of other modules (the Projects census's 121 State Street pages included) that list records this module lists, with how many.

- **Owner** (28 records here): Accounting › Dashboard 15; Purchasing › Buy Board 12; Projects › Decisions 9; Today › Chief of Staff 9; Company and Settings › Calendar 7; Projects › Job Page 7; Tasks and Messages › Meetings 6; Company and Settings › The Brain 5
- **PM (Alan)** (25 records here): Accounting › Dashboard 15; Purchasing › Buy Board 12; Projects › Decisions 9; Today › Chief of Staff 8; Company and Settings › The Brain 8; Company and Settings › Calendar 7; Projects › Job Page 7; Tasks and Messages › Meetings 6
- **Coordinator (Chen)** (11 records here): Purchasing › Buy Board 6; Today › Today 4; Today › Chief of Staff 4; Company and Settings › The Brain 4; Projects › Job Page 2
- **Designer (Sarah)** (28 records here): Accounting › Dashboard 15; Projects › Decisions 9; Today › Today 8; Tasks and Messages › Tasks 4; Projects › Documents 1; Projects › Tasks 1

Names (clients, vendors, leads, contacts, companies, partners) are left out here: a page that writes a name counts as listing it. A page that is the same page as one of this module's (one view under two menus) is left out too and listed next.

### The same page under two modules' menus

- Owner: Drawings here is also Projects › Drawings (`plans`)

## 3. One Label, Different Numbers

The same label (a tile, a figure, a tab or section count) with numbers that share no value on two pages, for one role. Some are right about different scopes ("Open" against "All", one job against every job); the person still reads one word with two numbers. Each needs a person to judge.

Inside the module: none found.

Against other modules, Designer (Sarah), desktop: none found.

Against other modules, PM (Alan), desktop: none found.

## 4. Empty, Dead and Broken Screens

| Device | Role | Screen | What |
|---|---|---|---|
| desktop | Owner | Filings | lists nothing: "No fixed-fee filings on this proposal. Add one from the Fili" |
| desktop | Owner | Design (by the link 2 projects need attention) | opens ovstudio when asked for studio |
| desktop | PM (Alan) | Filings | lists nothing: "No fixed-fee filings on this proposal. Add one from the Fili" |
| desktop | PM (Alan) | Design (by the link 2 projects need attention) | opens ovstudio when asked for studio |
| desktop | Designer (Sarah) | Filings | lists nothing: "No fixed-fee filings on this proposal. Add one from the Fili" |
| phone | Owner | Filings | lists nothing: "No fixed-fee filings on this proposal. Add one from the Fili" |
| phone | Owner | Design (by the link 2 projects need attention) | opens ovstudio when asked for studio |
| phone | PM (Alan) | Filings | lists nothing: "No fixed-fee filings on this proposal. Add one from the Fili" |
| phone | PM (Alan) | Design (by the link 2 projects need attention) | opens ovstudio when asked for studio |
| phone | Designer (Sarah) | Filings | lists nothing: "No fixed-fee filings on this proposal. Add one from the Fili" |

## 5. The Phone at 390

"Cut off" is text the phone ends early; "scrolls inside" is a strip of tiles or tabs the person swipes sideways inside the page (the page itself does not move). "Strip swipe" counts pages whose strip entry sits off screen until the strip is swiped. Pages taller than 3 phone screens are listed with their height.

| Role | Screens | The page scrolls sideways | Text cut off at the edge | Strips that scroll inside the page | Strip swipe | Pages taller than 3 screens |
|---|---|---|---|---|---|---|
| Owner | 14 | 0 | 3: Design, Design (by the link 2 projects need attention), Project Board | 5: Design, Design (by the link 2 projects need attention), Filings, Project Board, Selections | 1: Selections | 1: Drawings 5.8 |
| PM (Alan) | 13 | 0 | 3: Design, Design (by the link 2 projects need attention), Project Board | 5: Design, Design (by the link 2 projects need attention), Filings, Project Board, Selections | 4: Project Board, Filings, Selections, Design | 0 |
| Coordinator (Chen) | 6 | 0 | 0 | 1: Selections | 1: Selections | 0 |
| Designer (Sarah) | 13 | 0 | 2: Design, Project Board | 4: Design, Filings, Project Board, Selections | 0 | 1: Drawings 5.8 |

## 6. Page by Page, in Full

Every page the primary role reaches, as it opens, then each of its tabs. Heights are in screens of that device (900px desktop, 844px phone); "above the fold" is above the bottom bar on the phone.

### Designer (Sarah), desktop

- reached by: Drawings (1 tap); first button "Mark in Revision"; shot [desktop](../../review/census/design/shots/desktop_designer_drawings.jpg)
- **Drawings** (`plans`): heading "Drawings — 121 State Street", 3.1 screens tall, 3 sections (2 above the fold), 0 tab screens; blue: New Revision
  - lead: "The job's drawing register: current sheets only unless you ask for the history. A superseded revision is VOID and opens stamped VOID."
  - sections: Set Check; WHAT THE SETS TEACH; Field Acknowledgments
  - figures: Found Before Work 0; Found in the Field 1; Rework Avoided $0; Our Cost $0; Days to Resolve 3.8; Open Conflicts 0
  - records: 2 vendors, 1 schedule lines, 1 subs to confirm, 1 files
  - columns: table: SHEET, TITLE, SET, REV, STATUS, DATE, ISSUED BY, WHAT CHANGED, FIELD (17 rows)
  - fields: Set All Sets Design Presentation LPC DOB, Status Current Sheets All Revisions For 
  - empty states: "No open conflicts between this job's sets."
- reached by: Design (1 tap); first button "Projects to Survey 1 11 rooms on listing"; shot [desktop](../../review/census/design/shots/desktop_designer_design.jpg)
- **Design** (`ovstudio`): heading "Design", 0.9 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: none
  - lead: "Every design project — the phase it is in, the hours against the proposal, the rooms and sheets that are not ready."
  - sections: Hours Not Logged (5); Who Is on What
  - figures: Projects to Survey 1; Sets to Re-Issue 1; Over Hours or Gated 1; At the Agency 1
  - records: 5 schedule lines, 3 clients
  - columns: table: PROJECT, CLIENT, PHASE, HOURS, RETAINER, SURVEY, DRAWINGS, FILINGS, GATES (3 rows)
  - fields: Search…
- reached by: Design › Project Board (2 taps); first button "New Room"; shot [desktop](../../review/census/design/shots/desktop_designer_project_board.jpg)
- **Project Board** (`sboard`): heading "Project Board", 1.0 screens tall, 11 sections (11 above the fold), 3 tab screens; blue: none
  - lead: "121 State Street — room by room, where the design stands and what is blocking it."
  - sections: Parlor kitchen; Garden kitchen; Primary bath; Garden bath; Stair; Garden bedroom; Living and dining; Laundry; Office; Facade and windows; Precedents
  - records: 1 clients
  - empty states: "All clear phases over hours · unmeasured rooms · sheets to re-issue · filings in review — nothing ne"; "No design proposal on this job yet."
  - tab groups: Rooms / Client / Meetings / FF&E
  - tab **Client**: heading "Project Board", 6 sections; 8 decisions, 1 clients, 1 materials
  - tab **Meetings**: heading "Project Board", 0 sections; 1 clients
  - tab **FF&E**: heading "121 State Street", 0 sections; 1 clients
- reached by: Design › Filings (2 taps); shot [desktop](../../review/census/design/shots/desktop_designer_filings.jpg)
- **Filings** (`sfile`): heading "Filings", 0.4 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: none
  - lead: "The filings this job needs, what each costs and who is carrying it."
  - sections: Before Anything Is Filed
  - empty states: "No fixed-fee filings on this proposal. Add one from the Filings settings, or leave it — filings can "
- reached by: Design › Selections (2 taps); first button "Get Clips"; shot [desktop](../../review/census/design/shots/desktop_designer_selections.jpg)
- **Selections** (`sel`): heading "Selections — 121 State Street", 1.5 screens tall, 0 sections (0 above the fold), 5 tab screens; blue: Clip an Item
  - lead: "The designer's board and the buyer's list are the same record. Clip an item once; every screen after this reads what was captured, not what someone retyped."
  - figures: Red Flags 4; To Check 4; Awaiting Approval 2; Still to Buy 5
  - records: 8 materials, 5 vendors, 3 selections
  - tab groups: All Rooms / Guest bath / Kitchen / Parlor / Primary bath / Whole house
  - tab **Guest bath**: heading "Selections — 121 State Street", 0 sections; 1 selections
  - tab **Kitchen**: heading "Selections — 121 State Street", 0 sections; 2 materials, 2 vendors, 1 selections
  - tab **Parlor**: heading "Selections — 121 State Street", 0 sections; 1 materials, 1 vendors
  - tab **Primary bath**: heading "Selections — 121 State Street", 0 sections; 4 materials, 2 vendors, 1 selections
  - tab **Whole house**: heading "Selections — 121 State Street", 0 sections; 1 materials, 1 vendors

### Designer (Sarah), phone

- reached by: bar: Drawings (1 tap); first button "Mark in Revision"; shot [phone](../../review/census/design/shots/phone_designer_drawings.jpg)
- **Drawings** (`plans`): heading "Drawings — 121 State Street", 5.8 screens tall, 3 sections (1 above the fold), 0 tab screens; blue: New Revision
  - lead: "The job's drawing register: current sheets only unless you ask for the history. A superseded revision is VOID and opens stamped VOID."
  - sections: Set Check; WHAT THE SETS TEACH; Field Acknowledgments
  - figures: Found Before Work 0; Found in the Field 1; Rework Avoided $0; Our Cost $0; Days to Resolve 3.8; Open Conflicts 0
  - records: 2 vendors, 1 schedule lines, 1 subs to confirm, 1 files
  - fields: Set All Sets Design Presentation LPC DOB, Status Current Sheets All Revisions For 
  - empty states: "No open conflicts between this job's sets."
- reached by: menu › Design (2 taps); first button "Projects to Survey 1"; shot [phone](../../review/census/design/shots/phone_designer_design.jpg)
- **Design** (`ovstudio`): heading "Design", 1.2 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: none; runs past the edge: cut off by pr-m (Rivera family · Design development · 121)
  - lead: "Every design project — the phase it is in, the hours against the proposal, the rooms and sheets that are not ready."
  - sections: Hours Not Logged (5); Who Is on What
  - figures: Projects to Survey 1; Sets to Re-Issue 1; Over Hours or Gated 1; At the Agency 1
  - records: 4 schedule lines, 3 clients
  - columns: table: Project, Client, Phase, Hours, Retainer, Survey, Drawings, Filings, Gates (3 rows)
  - fields: Search…
- reached by: menu › Design › Project Board (3 taps); first button "New Room"; shot [phone](../../review/census/design/shots/phone_designer_project_board.jpg)
- **Project Board** (`sboard`): heading "Project Board", 2.8 screens tall, 11 sections (2 above the fold), 3 tab screens; blue: none
  - lead: "121 State Street — room by room, where the design stands and what is blocking it."
  - sections: Parlor kitchen; Garden kitchen; Primary bath; Garden bath; Stair; Garden bedroom; Living and dining; Laundry; Office; Facade and windows; Precedents
  - records: 1 clients
  - empty states: "All clear phases over hours · unmeasured rooms · sheets to re-issue · filings in review — nothing ne"; "No design proposal on this job yet."
  - tab groups: Rooms / Client / Meetings / FF&E
  - tab **Client**: heading "Project Board", 6 sections; 8 decisions, 1 clients, 1 materials
  - tab **Meetings**: heading "Project Board", 0 sections; 1 clients (runs past the edge: cut off by [object (path.[object))
  - tab **FF&E**: heading "121 State Street", 0 sections; 1 clients
- reached by: menu › Design › Filings (3 taps); shot [phone](../../review/census/design/shots/phone_designer_filings.jpg)
- **Filings** (`sfile`): heading "Filings", 0.6 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: none
  - lead: "The filings this job needs, what each costs and who is carrying it."
  - sections: Before Anything Is Filed
  - empty states: "No fixed-fee filings on this proposal. Add one from the Filings settings, or leave it — filings can "
- reached by: menu › Design › Selections (3 taps); first button "Get Clips"; shot [phone](../../review/census/design/shots/phone_designer_selections.jpg)
- **Selections** (`sel`): heading "Selections — 121 State Street", 1.1 screens tall, 0 sections (0 above the fold), 5 tab screens; blue: Clip an Item
  - lead: "The designer's board and the buyer's list are the same record. Clip an item once; every screen after this reads what was captured, not what someone retyped."
  - figures: Red Flags 4; To Check 4; Awaiting Approval 2; Still to Buy 5
  - records: 8 materials, 3 selections
  - tab groups: All Rooms / Guest bath / Kitchen / Parlor / Primary bath / Whole house
  - tab **Guest bath**: heading "Selections — 121 State Street", 0 sections; 1 selections
  - tab **Kitchen**: heading "Selections — 121 State Street", 0 sections; 2 materials, 2 vendors, 1 selections
  - tab **Parlor**: heading "Selections — 121 State Street", 0 sections; 1 materials, 1 vendors
  - tab **Primary bath**: heading "Selections — 121 State Street", 0 sections; 4 materials, 1 selections
  - tab **Whole house**: heading "Selections — 121 State Street", 0 sections; 1 materials, 1 vendors

### PM (Alan), desktop

- reached by: More › Project Board (2 taps); first button "New Room"; shot [desktop](../../review/census/design/shots/desktop_pm_project_board.jpg)
- **Project Board** (`sboard`): heading "Project Board", 1.0 screens tall, 11 sections (11 above the fold), 3 tab screens; blue: none
  - lead: "121 State Street — room by room, where the design stands and what is blocking it."
  - sections: Parlor kitchen; Garden kitchen; Primary bath; Garden bath; Stair; Garden bedroom; Living and dining; Laundry; Office; Facade and windows; Precedents
  - records: 1 clients
  - empty states: "All clear phases over hours · unmeasured rooms · sheets to re-issue · filings in review — nothing ne"; "No design proposal on this job yet."
  - tab groups: Rooms / Client / Meetings / FF&E
  - tab **Client**: heading "Project Board", 6 sections; 8 decisions, 1 clients, 1 materials
  - tab **Meetings**: heading "Project Board", 0 sections; 1 clients
  - tab **FF&E**: heading "121 State Street", 0 sections; 1 clients
- reached by: More › Filings (2 taps); shot [desktop](../../review/census/design/shots/desktop_pm_filings.jpg)
- **Filings** (`sfile`): heading "Filings", 0.4 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: none
  - lead: "The filings this job needs, what each costs and who is carrying it."
  - sections: Before Anything Is Filed
  - empty states: "No fixed-fee filings on this proposal. Add one from the Filings settings, or leave it — filings can "
- reached by: More › Selections (2 taps); first button "Get Clips"; shot [desktop](../../review/census/design/shots/desktop_pm_selections.jpg)
- **Selections** (`sel`): heading "Selections", 1.5 screens tall, 0 sections (0 above the fold), 5 tab screens; blue: Clip an Item
  - lead: "The designer's board and the buyer's list are the same record. Clip an item once; every screen after this reads what was captured, not what someone retyped."
  - figures: Red Flags 4; To Check 4; Awaiting Approval 2; Still to Buy 5
  - records: 8 materials, 5 vendors, 3 selections
  - tab groups: All Rooms / Guest bath / Kitchen / Parlor / Primary bath / Whole house
  - tab **Guest bath**: heading "Selections", 0 sections; 1 selections
  - tab **Kitchen**: heading "Selections", 0 sections; 2 materials, 2 vendors, 1 selections
  - tab **Parlor**: heading "Selections", 0 sections; 1 materials, 1 vendors
  - tab **Primary bath**: heading "Selections", 0 sections; 4 materials, 2 vendors, 1 selections
  - tab **Whole house**: heading "Selections", 0 sections; 1 materials, 1 vendors
- reached by: More › Design (2 taps); first button "Projects to Survey 1 11 rooms on listing"; shot [desktop](../../review/census/design/shots/desktop_pm_design.jpg)
- **Design** (`ovstudio`): heading "Design", 0.9 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: none
  - lead: "Every design project — the phase it is in, the hours against the proposal, the rooms and sheets that are not ready."
  - sections: Hours Not Logged (5); Who Is on What
  - figures: Projects to Survey 1; Sets to Re-Issue 1; Over Hours or Gated 1; At the Agency 1
  - records: 5 schedule lines, 3 clients
  - columns: table: PROJECT, CLIENT, PHASE, HOURS, RETAINER, SURVEY, DRAWINGS, FILINGS, GATES (3 rows)
  - fields: Search…
- reached by: Design › link: 2 projects need attention; first button "Projects to Survey 1 11 rooms on listing"; shot [desktop](../../review/census/design/shots/desktop_pm_2_projects_need_attention.jpg)
- **Design (by the link 2 projects need attention)** (`ovstudio`): heading "Design", 0.9 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: none; opens `ovstudio` when asked for `studio`
  - lead: "Every design project — the phase it is in, the hours against the proposal, the rooms and sheets that are not ready."
  - sections: Hours Not Logged (5); Who Is on What
  - figures: Projects to Survey 1; Sets to Re-Issue 1; Over Hours or Gated 1; At the Agency 1
  - records: 5 schedule lines, 3 clients
  - columns: table: PROJECT, CLIENT, PHASE, HOURS, RETAINER, SURVEY, DRAWINGS, FILINGS, GATES (3 rows)
  - fields: Search…

### PM (Alan), phone

- reached by: menu › More › swipe the strip, Project Board (3 taps); first button "New Room"; shot [phone](../../review/census/design/shots/phone_pm_project_board.jpg)
- **Project Board** (`sboard`): heading "Project Board", 2.8 screens tall, 11 sections (2 above the fold), 3 tab screens; blue: none
  - lead: "121 State Street — room by room, where the design stands and what is blocking it."
  - sections: Parlor kitchen; Garden kitchen; Primary bath; Garden bath; Stair; Garden bedroom; Living and dining; Laundry; Office; Facade and windows; Precedents
  - records: 1 clients
  - empty states: "All clear phases over hours · unmeasured rooms · sheets to re-issue · filings in review — nothing ne"; "No design proposal on this job yet."
  - tab groups: Rooms / Client / Meetings / FF&E
  - tab **Client**: heading "Project Board", 6 sections; 8 decisions, 1 clients, 1 materials
  - tab **Meetings**: heading "Project Board", 0 sections; 1 clients (runs past the edge: cut off by [object (path.[object))
  - tab **FF&E**: heading "121 State Street", 0 sections; 1 clients
- reached by: menu › More › swipe the strip, Filings (3 taps); shot [phone](../../review/census/design/shots/phone_pm_filings.jpg)
- **Filings** (`sfile`): heading "Filings", 0.6 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: none
  - lead: "The filings this job needs, what each costs and who is carrying it."
  - sections: Before Anything Is Filed
  - empty states: "No fixed-fee filings on this proposal. Add one from the Filings settings, or leave it — filings can "
- reached by: menu › More › swipe the strip, Selections (3 taps); first button "Get Clips"; shot [phone](../../review/census/design/shots/phone_pm_selections.jpg)
- **Selections** (`sel`): heading "Selections", 1.1 screens tall, 0 sections (0 above the fold), 5 tab screens; blue: Clip an Item
  - lead: "The designer's board and the buyer's list are the same record. Clip an item once; every screen after this reads what was captured, not what someone retyped."
  - figures: Red Flags 4; To Check 4; Awaiting Approval 2; Still to Buy 5
  - records: 8 materials, 3 selections
  - tab groups: All Rooms / Guest bath / Kitchen / Parlor / Primary bath / Whole house
  - tab **Guest bath**: heading "Selections", 0 sections; 1 selections
  - tab **Kitchen**: heading "Selections", 0 sections; 2 materials, 2 vendors, 1 selections
  - tab **Parlor**: heading "Selections", 0 sections; 1 materials, 1 vendors
  - tab **Primary bath**: heading "Selections", 0 sections; 4 materials, 1 selections
  - tab **Whole house**: heading "Selections", 0 sections; 1 materials, 1 vendors
- reached by: menu › More › swipe the strip, Design (3 taps); first button "Projects to Survey 1"; shot [phone](../../review/census/design/shots/phone_pm_design.jpg)
- **Design** (`ovstudio`): heading "Design", 1.2 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: none; runs past the edge: cut off by pr-m (Rivera family · Design development · 121)
  - lead: "Every design project — the phase it is in, the hours against the proposal, the rooms and sheets that are not ready."
  - sections: Hours Not Logged (5); Who Is on What
  - figures: Projects to Survey 1; Sets to Re-Issue 1; Over Hours or Gated 1; At the Agency 1
  - records: 4 schedule lines, 3 clients
  - columns: table: Project, Client, Phase, Hours, Retainer, Survey, Drawings, Filings, Gates (3 rows)
  - fields: Search…
- reached by: Design › link: 2 projects need attention; first button "Projects to Survey 1"; shot [phone](../../review/census/design/shots/phone_pm_2_projects_need_attention.jpg)
- **Design (by the link 2 projects need attention)** (`ovstudio`): heading "Design", 1.2 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: none; opens `ovstudio` when asked for `studio`; runs past the edge: cut off by pr-m (Rivera family · Design development · 121)
  - lead: "Every design project — the phase it is in, the hours against the proposal, the rooms and sheets that are not ready."
  - sections: Hours Not Logged (5); Who Is on What
  - figures: Projects to Survey 1; Sets to Re-Issue 1; Over Hours or Gated 1; At the Agency 1
  - records: 4 schedule lines, 3 clients
  - columns: table: Project, Client, Phase, Hours, Retainer, Survey, Drawings, Filings, Gates (3 rows)
  - fields: Search…

## 7. The Other Roles, One Line a Page

### Owner, desktop

- reached by: Design (1 tap); shot [desktop](../../review/census/design/shots/desktop_owner_design.jpg)
- **Design** (`ovstudio`): heading "Design", 0.9 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: none
- reached by: Design › Project Board (2 taps); shot [desktop](../../review/census/design/shots/desktop_owner_project_board.jpg)
- **Project Board** (`sboard`): heading "Project Board", 1.0 screens tall, 11 sections (11 above the fold), 3 tab screens; blue: none
- reached by: Design › Drawings (2 taps); shot [desktop](../../review/census/design/shots/desktop_owner_drawings.jpg)
- **Drawings** (`plans`): heading "Drawings — 121 State Street", 3.1 screens tall, 3 sections (2 above the fold), 0 tab screens; blue: New Revision
- reached by: Design › Filings (2 taps); shot [desktop](../../review/census/design/shots/desktop_owner_filings.jpg)
- **Filings** (`sfile`): heading "Filings", 0.4 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: none
- reached by: Design › Selections (2 taps); shot [desktop](../../review/census/design/shots/desktop_owner_selections.jpg)
- **Selections** (`sel`): heading "Selections", 1.5 screens tall, 0 sections (0 above the fold), 5 tab screens; blue: Clip an Item
- reached by: Design › link: 2 projects need attention; shot [desktop](../../review/census/design/shots/desktop_owner_2_projects_need_attention.jpg)
- **Design (by the link 2 projects need attention)** (`ovstudio`): heading "Design", 0.9 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: none; opens `ovstudio` when asked for `studio`

### Owner, phone

- reached by: menu › Design (2 taps); shot [phone](../../review/census/design/shots/phone_owner_design.jpg)
- **Design** (`ovstudio`): heading "Design", 1.2 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: none; runs past the edge: cut off by pr-m (Rivera family · Design development · 121)
- reached by: menu › Design › Project Board (3 taps); shot [phone](../../review/census/design/shots/phone_owner_project_board.jpg)
- **Project Board** (`sboard`): heading "Project Board", 2.8 screens tall, 11 sections (2 above the fold), 3 tab screens; blue: none
- reached by: menu › Design › Drawings (3 taps); shot [phone](../../review/census/design/shots/phone_owner_drawings.jpg)
- **Drawings** (`plans`): heading "Drawings — 121 State Street", 5.8 screens tall, 3 sections (1 above the fold), 0 tab screens; blue: New Revision
- reached by: menu › Design › Filings (3 taps); shot [phone](../../review/census/design/shots/phone_owner_filings.jpg)
- **Filings** (`sfile`): heading "Filings", 0.6 screens tall, 1 sections (1 above the fold), 0 tab screens; blue: none
- reached by: menu › Design › swipe the strip, Selections (3 taps); shot [phone](../../review/census/design/shots/phone_owner_selections.jpg)
- **Selections** (`sel`): heading "Selections", 1.1 screens tall, 0 sections (0 above the fold), 5 tab screens; blue: Clip an Item
- reached by: Design › link: 2 projects need attention; shot [phone](../../review/census/design/shots/phone_owner_2_projects_need_attention.jpg)
- **Design (by the link 2 projects need attention)** (`ovstudio`): heading "Design", 1.2 screens tall, 2 sections (2 above the fold), 0 tab screens; blue: none; opens `ovstudio` when asked for `studio`; runs past the edge: cut off by pr-m (Rivera family · Design development · 121)

### Coordinator (Chen), desktop

- reached by: More › Selections (2 taps); shot [desktop](../../review/census/design/shots/desktop_coord_selections.jpg)
- **Selections** (`sel`): heading "Selections", 1.5 screens tall, 0 sections (0 above the fold), 5 tab screens; blue: Clip an Item

### Coordinator (Chen), phone

- reached by: menu › More › swipe the strip, Selections (3 taps); shot [phone](../../review/census/design/shots/phone_coord_selections.jpg)
- **Selections** (`sel`): heading "Selections", 1.1 screens tall, 0 sections (0 above the fold), 5 tab screens; blue: Clip an Item

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

