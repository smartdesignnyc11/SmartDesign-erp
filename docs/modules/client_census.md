# The The Client Portal Module, Page by Page: the Census

**Asked by Alan, 2026-10-26:** "Go through all the modules with screenshots. It's important to understand the format of every page and what's on it." The loop's experts and the client expert walk every page of their module with this in hand in round one of the improvement loop (docs/IMPROVEMENT_LOOP.md).

**What this is.** A machine inventory, not a judgment, in the format of the Projects census (`docs/modules/projects_census.md`). No app code changed. `tests/module_census.py` (its helpers `tests/module_census_js.js` sit on the projects census's reader `tests/census_js.js` and the information map's `tests/ia_js.js`) signs in as each role on a fresh app at 1440 and at 390, reads the role's running menu, and reaches each page of this module the way the person does: the phone bar, or the menu (the hamburger on the phone), the group, then the strip. It presses every tab of every tab group and the tabs those reveal, follows the page's own links to this module's pages the menu did not reach, reads every screen and shoots it. The primary role is the client; every role whose menu holds a page of this module is walked. Job-scoped pages show **121 State Street** wherever the role may open it.

**Where this module's pages sit.** The client sees their own job only (121 State Street) and has no menu groups: five entries on the rail and the phone bar.

**Build bd3180c27e33** (master 1cc2eb9), the one build every module census of this round ran on. 12 screens in all. Walked 2026-10-26 06:29 on the demo day (Thu 2026-09-03); the walk of every module took 54.4 minutes. Raw read: `review/census/client/data.json`. Every screen per role in tables: `review/census/client/tables.md`. Screenshots of every screen, both devices: `review/census/client/shots/` (`desktop_` or `phone_`, the role, the page, then the tab; up to 3 desktop or 5 phone screens tall). The first screen of each page is committed; the tabs stay on the machine that ran it.

Run it: `python3 build.py && cd tests && ./slot.sh python3 module_census.py --module client` (then `python3 module_census.py --report` rewrites every module's page from data.json).

## Headline

- **Client (Klein): 5 pages with 1 more screen behind their tabs on the desktop (5 pages and 1 tab screen on the phone)**, about 7 desktop screens end to end.
- **Pages each role reaches in this module, desktop:** Client 5.
- **Reached only one way** by Client (Klein): Account (desktop), Overview (desktop), Schedule (desktop) (one menu entry, not on the phone bar, and no walked page links to it; section 1).
- **22 records show on two or more of this module's pages** for Client (Klein) on the desktop (8 schedule lines, 5 decisions, 4 materials, 1 submittals). "Rough plumbing" is on 3: Decisions, Overview, Schedule.
- **3 pairs of pages list largely the same records,** led by Overview and Schedule (16 shared); Decisions and Overview (13 shared); Decisions and Schedule (9 shared).
- **On the phone** (Client): 1 of the 5 pages are taller than three screens (Overview); 1 have no section heading above the fold; 0 screens scroll sideways.
- **Nothing crashed and no page raised an error**; every page opened.
- **Reading changed nothing:** no save during the walk.

## 1. The Tree, Role by Role

**Pages** are the module's pages the role reaches from its menu (and the links those pages show). **Tabs** are the screens behind each page's tab groups, and behind the tabs those reveal. **Sections** are the headed parts of each page as it opens. Each cell reads desktop / phone.

| Role | Primary | First page of the module, reached by (desktop / phone) | Pages | Tab screens | Sections | Screens |
|---|---|---|---|---|---|---|
| Client (Klein) | yes | Overview (1 tap) / bar: Overview (1 tap) | 5 / 5 | 1 / 1 | 20 / 20 | 6 / 6 |

### Which pages each role reaches (desktop)

Each cell is the number of screens the page has (the page and its tabs); "-" means the role does not reach it.

| Page | Client |
|---|---|
| Overview | 1 |
| Schedule | 1 |
| Decisions | 1 |
| Account | 1 |
| Chat | 2 |

### Client (Klein)'s tree at a glance

Reached by is the taps from the role's first page, desktop then phone. Tall is in screens, desktop / phone. Sections are the headed parts as the page opens (phone above the fold). Tabs are the screens behind its tab groups, desktop / phone. "What it lists" counts the records found on the page as it opens.

| Page | Reached by (desktop / phone) | Heading | Tall | Sections (phone above the fold) | Tabs | Tiles and figures | What it lists | Blue button | First button | Shots |
|---|---|---|---|---|---|---|---|---|---|---|
| Overview | Overview (1 tap) / bar: Overview (1 tap) | Overview | 1.9 / 3.7 | 6 (1) | 0 / 0 | Waiting on You 7; Invoices Due $68,265; Finish Date Wed, Nov 4 | 9 schedule lines, 5 decisions, 4 materials, 1 submittals | Choose | Waiting on You 7 1 needed no | [desktop](../../review/census/client/shots/desktop_client_overview.jpg) [phone](../../review/census/client/shots/phone_client_overview.jpg) |
| Schedule | Schedule (1 tap) / bar: Schedule (1 tap) | Schedule | 2.3 / 2.9 | 6 (4) | 0 / 0 | Finish Date Wed, Nov 4; Stages Finished 0 of 36; Happening Now Rough electrical | 8 schedule lines, 5 decisions, 3 materials, 1 obligations | none | Parlor kitchen base boxes go | [desktop](../../review/census/client/shots/desktop_client_schedule.jpg) [phone](../../review/census/client/shots/phone_client_schedule.jpg) |
| Decisions | Decisions (1 tap) / bar: Decisions (1 tap) | Decisions | 1.2 / 1.7 | 5 (2) | 0 / 0 | - | 8 decisions, 4 materials, 2 schedule lines, 2 submittals | Choose | Choose (blue) | [desktop](../../review/census/client/shots/desktop_client_decisions.jpg) [phone](../../review/census/client/shots/phone_client_decisions.jpg) |
| Account | Account (1 tap) / bar: Account (1 tap) | Account | 0.9 / 1.3 | 3 (3) | 0 / 0 | Open Balance $68,265; Waiting on Your Signat 1; Paid to Date $169,750; Photos of the Job 4 | 3 invoices, 2 change orders | none | View | [desktop](../../review/census/client/shots/desktop_client_account.jpg) [phone](../../review/census/client/shots/phone_client_account.jpg) |
| Chat | Chat (1 tap) / bar: Chat (1 tap) | Messages | 1.0 / 0.2 | 0 (0) | 1 / 1 | - | - | Send | Ask the Assistant | [desktop](../../review/census/client/shots/desktop_client_chat.jpg) [phone](../../review/census/client/shots/phone_client_chat.jpg) |

### How each page is reached, and the pages reached only one way

Menu places are the role's menu entries that open the page (a page in two groups has two). The phone bar counts as one more way in on the phone (its pages are in the menu too). Links are the walked pages, in any module, that show a link to it. **One way** means one menu place and nothing else: lose that entry and the page is lost.

| Role | Device | Page | Menu places | Phone bar | Linked from | Ways in |
|---|---|---|---|---|---|---|
| Client (Klein) | desktop | Overview | Overview | - | - | 1 (one way) |
| Client (Klein) | desktop | Schedule | Schedule | - | - | 1 (one way) |
| Client (Klein) | desktop | Decisions | Decisions | - | The Client Portal › Overview | 2 |
| Client (Klein) | desktop | Account | Account | - | - | 1 (one way) |
| Client (Klein) | desktop | Chat | Chat | - | The Client Portal › Chat | 2 |
| Client (Klein) | phone | Overview | Overview | yes | - | 2 |
| Client (Klein) | phone | Schedule | Schedule | yes | - | 2 |
| Client (Klein) | phone | Decisions | Decisions | yes | The Client Portal › Overview | 3 |
| Client (Klein) | phone | Account | Account | yes | - | 2 |
| Client (Klein) | phone | Chat | Chat | yes | The Client Portal › Chat | 3 |

## 2. Where the Data Lives, and Where It Shows Twice

Records are found by their own words (the information map's catalog, the job's nouns and this census's: clients, vendors, leads, contacts, companies, every invoice, bill and PO, payroll runs, stock, meetings, journals, obligations, lessons, partners, bank lines, threads), so these are floors. A page's tabs count as the page.

### Client (Klein), desktop: each kind of record, and the pages that list it

| Records | Found | Pages that list them (how many each) | Also in other modules |
|---|---|---|---|
| decisions | 8 | 3: Decisions 8, Overview 5, Schedule 5 | - |
| materials | 4 | 3: Overview 4, Decisions 4, Schedule 3 | - |
| schedule lines | 10 | 3: Overview 9, Schedule 8, Decisions 2 | - |
| change orders | 2 | 3: Account 2, Overview 1, Decisions 1 | - |
| vendors | 1 | 2: Overview 1, Decisions 1 | - |
| obligations | 1 | 2: Overview 1, Schedule 1 | - |
| invoices | 3 | 2: Account 3, Overview 1 | - |
| submittals | 2 | 2: Decisions 2, Overview 1 | - |

### Records on two or more pages, and lists that are the same list twice

**Client (Klein), desktop:** 22 records on two or more pages: schedule lines 8 (up to 3 pages); decisions 5 (up to 3 pages); materials 4 (up to 3 pages); submittals 1 (up to 2 pages); invoices 1 (up to 2 pages); change orders 1 (up to 3 pages); vendors 1 (up to 2 pages); obligations 1 (up to 2 pages).

- "Rough plumbing" (schedule lines) on 3 pages: Decisions, Overview, Schedule
- "Confirm new 3rd fl tile selection is in stock" (decisions) on 3 pages: Decisions, Overview, Schedule
- "Exterior paint finish / sheen" (decisions) on 3 pages: Decisions, Overview, Schedule
- "3rd fl lighting layout approval" (decisions) on 3 pages: Decisions, Overview, Schedule
- "Garden kitchen backsplash: tile or stone?" (decisions) on 3 pages: Decisions, Overview, Schedule
- "2nd fl bathroom finishes re-review with client" (decisions) on 3 pages: Decisions, Overview, Schedule
- the same list twice (3 or more shared records, at least half of the shorter list): Overview and Schedule (16 shared, of 22 and 17: schedule lines, decisions, materials); Decisions and Overview (13 shared, of 17 and 22: decisions, materials, schedule lines); Decisions and Schedule (9 shared, of 17 and 17: decisions, materials, schedule lines)

**Client (Klein), phone:** 22 records on two or more pages: schedule lines 8 (up to 3 pages); decisions 5 (up to 3 pages); materials 4 (up to 3 pages); submittals 1 (up to 2 pages); invoices 1 (up to 2 pages); change orders 1 (up to 3 pages); vendors 1 (up to 2 pages); obligations 1 (up to 2 pages).

- "Rough plumbing" (schedule lines) on 3 pages: Decisions, Overview, Schedule
- "Confirm new 3rd fl tile selection is in stock" (decisions) on 3 pages: Decisions, Overview, Schedule
- "Exterior paint finish / sheen" (decisions) on 3 pages: Decisions, Overview, Schedule
- "3rd fl lighting layout approval" (decisions) on 3 pages: Decisions, Overview, Schedule
- "Garden kitchen backsplash: tile or stone?" (decisions) on 3 pages: Decisions, Overview, Schedule
- "2nd fl bathroom finishes re-review with client" (decisions) on 3 pages: Decisions, Overview, Schedule
- the same list twice (3 or more shared records, at least half of the shorter list): Overview and Schedule (16 shared, of 22 and 17: schedule lines, decisions, materials); Decisions and Overview (13 shared, of 17 and 22: decisions, materials, schedule lines); Decisions and Schedule (9 shared, of 17 and 17: decisions, materials, schedule lines)

### The same records in other modules

For each role on the desktop: the pages of other modules (the Projects census's 121 State Street pages included) that list records this module lists, with how many.

- **Client (Klein)**: none found.

Names (clients, vendors, leads, contacts, companies, partners) are left out here: a page that writes a name counts as listing it. A page that is the same page as one of this module's (one view under two menus) is left out too and listed next.

### The same page under two modules' menus

None found.

## 3. One Label, Different Numbers

The same label (a tile, a figure, a tab or section count) with numbers that share no value on two pages, for one role. Some are right about different scopes ("Open" against "All", one job against every job); the person still reads one word with two numbers. Each needs a person to judge.

Inside the module: none found.

Against other modules, Client (Klein), desktop: none found.

## 4. Empty, Dead and Broken Screens

| Device | Role | Screen | What |
|---|---|---|---|
| desktop | Client (Klein) | Chat | lists nothing: "No messages yet Ask anything. Your project team answers here" |
| desktop | Client (Klein) | Chat[Ask the Assistant] | the tab leaves for pa |
| phone | Client (Klein) | Chat | 22 words; lists nothing: "No messages yet Ask anything. Your project team answers here" |
| phone | Client (Klein) | Chat[Ask the Assistant] | the tab leaves for pa |

## 5. The Phone at 390

"Cut off" is text the phone ends early; "scrolls inside" is a strip of tiles or tabs the person swipes sideways inside the page (the page itself does not move). "Strip swipe" counts pages whose strip entry sits off screen until the strip is swiped. Pages taller than 3 phone screens are listed with their height.

| Role | Screens | The page scrolls sideways | Text cut off at the edge | Strips that scroll inside the page | Strip swipe | Pages taller than 3 screens |
|---|---|---|---|---|---|---|
| Client (Klein) | 6 | 0 | 0 | 1: Chat | 0 | 1: Overview 3.7 |

## 6. Page by Page, in Full

Every page the primary role reaches, as it opens, then each of its tabs. Heights are in screens of that device (900px desktop, 844px phone); "above the fold" is above the bottom bar on the phone.

### Client (Klein), desktop

- reached by: Overview (1 tap); first button "Waiting on You 7 1 needed now — the sche"; shot [desktop](../../review/census/client/shots/desktop_client_overview.jpg)
- **Overview** (`client`): heading "Overview", 1.9 screens tall, 6 sections (4 above the fold), 0 tab screens; blue: Choose
  - lead: "121 State Street — where it stands, what we need from you, and what is owed."
  - sections: Waiting on You (7); Your Account; What's Coming Up; Progress; Recently Completed; Questions?
  - figures: Waiting on You 7; Invoices Due $68,265; Finish Date Wed, Nov 4
  - records: 9 schedule lines, 5 decisions, 4 materials, 1 submittals, 1 invoices, 1 change orders, 1 vendors, 1 obligations
- reached by: Schedule (1 tap); first button "Parlor kitchen base boxes going in"; shot [desktop](../../review/census/client/shots/desktop_client_schedule.jpg)
- **Schedule** (`sched`): heading "Schedule", 2.3 screens tall, 6 sections (4 above the fold), 0 tab screens; blue: none
  - lead: "Site hours 07:30–16:30, Mon Tue Wed Thu Fri, 30 min lunch (8.5 h/day). All tracks — design, permitting, procurement, construction and closeout share one depende"
  - sections: From Alan; What Changed; Milestones; Progress (4); What Comes Next; What We Need from You
  - figures: Finish Date Wed, Nov 4; Stages Finished 0 of 36; Happening Now Rough electrical
  - records: 8 schedule lines, 5 decisions, 3 materials, 1 obligations
  - empty states: "No dates moved since the last update. When one does, it is listed here with the reason before anythi"
- reached by: Decisions (1 tap); first button "Choose"; shot [desktop](../../review/census/client/shots/desktop_client_decisions.jpg)
- **Decisions** (`dec`): heading "Decisions", 1.2 screens tall, 5 sections (5 above the fold), 0 tab screens; blue: Choose
  - lead: "Selections, layouts and sign-offs that block an order or a task. Due dates come from what they block."
  - sections: We Need Your Choice; Approve the Change; Approve Before We Order; Already Settled; We Are Deciding These
  - records: 8 decisions, 4 materials, 2 schedule lines, 2 submittals, 1 change orders, 1 vendors
- reached by: Account (1 tap); first button "View"; shot [desktop](../../review/census/client/shots/desktop_client_account.jpg)
- **Account** (`clacct`): heading "Account", 0.9 screens tall, 3 sections (3 above the fold), 0 tab screens; blue: none
  - lead: "$68,265 is open, next due Tue, Sep 15. Every invoice, change order and photo of the job is here."
  - sections: Invoices; Change Orders; Photos of the Job
  - figures: Open Balance $68,265; Waiting on Your Signature 1; Paid to Date $169,750; Photos of the Job 4
  - records: 3 invoices, 2 change orders
- reached by: Chat (1 tap); first button "Ask the Assistant"; shot [desktop](../../review/census/client/shots/desktop_client_chat.jpg)
- **Chat** (`chat`): heading "Messages", 1.0 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: Send
  - lead: "Write to Alan, your project manager. Alan and the team on your job read it and answer here."
  - fields: Message
  - empty states: "No messages yet Ask anything. Your project team answers here."
  - tab groups: Ask the Assistant / Write to Alan
  - tab **Ask the Assistant**: heading "Chat", 0 sections (the tab leaves for `pa`)

### Client (Klein), phone

- reached by: bar: Overview (1 tap); first button "Waiting on You 7"; shot [phone](../../review/census/client/shots/phone_client_overview.jpg)
- **Overview** (`client`): heading "Overview", 3.7 screens tall, 6 sections (1 above the fold), 0 tab screens; blue: Choose
  - lead: "121 State Street — where it stands, what we need from you, and what is owed."
  - sections: Waiting on You (7); Your Account; What's Coming Up; Progress; Recently Completed; Questions?
  - figures: Waiting on You 7; Invoices Due $68,265; Finish Date Wed, Nov 4
  - records: 9 schedule lines, 5 decisions, 4 materials, 1 submittals, 1 invoices, 1 change orders, 1 vendors, 1 obligations
- reached by: bar: Schedule (1 tap); first button "Parlor kitchen base boxes going in"; shot [phone](../../review/census/client/shots/phone_client_schedule.jpg)
- **Schedule** (`sched`): heading "Schedule", 2.9 screens tall, 6 sections (4 above the fold), 0 tab screens; blue: none
  - lead: "Site hours 07:30–16:30, Mon Tue Wed Thu Fri, 30 min lunch (8.5 h/day). All tracks — design, permitting, procurement, construction and closeout share one depende"
  - sections: From Alan; What Changed; Milestones; Progress (4); What Comes Next; What We Need from You
  - figures: Finish Date Wed, Nov 4; Stages Finished 0 of 36; Happening Now Rough electrical
  - records: 8 schedule lines, 5 decisions, 3 materials, 1 obligations
  - empty states: "No dates moved since the last update. When one does, it is listed here with the reason before anythi"
- reached by: bar: Decisions (1 tap); first button "Choose"; shot [phone](../../review/census/client/shots/phone_client_decisions.jpg)
- **Decisions** (`dec`): heading "Decisions", 1.7 screens tall, 5 sections (2 above the fold), 0 tab screens; blue: Choose
  - lead: "Selections, layouts and sign-offs that block an order or a task. Due dates come from what they block."
  - sections: We Need Your Choice; Approve the Change; Approve Before We Order; Already Settled; We Are Deciding These
  - records: 8 decisions, 4 materials, 2 schedule lines, 2 submittals, 1 change orders, 1 vendors
- reached by: bar: Account (1 tap); first button "View"; shot [phone](../../review/census/client/shots/phone_client_account.jpg)
- **Account** (`clacct`): heading "Account", 1.3 screens tall, 3 sections (3 above the fold), 0 tab screens; blue: none
  - lead: "$68,265 is open, next due Tue, Sep 15. Every invoice, change order and photo of the job is here."
  - sections: Invoices; Change Orders; Photos of the Job
  - figures: Open Balance $68,265; Waiting on Your Signature 1; Paid to Date $169,750; Photos of the Job 4
  - records: 3 invoices, 2 change orders
- reached by: bar: Chat (1 tap); first button "Ask the Assistant"; shot [phone](../../review/census/client/shots/phone_client_chat.jpg)
- **Chat** (`chat`): heading "Chat", 0.2 screens tall, 0 sections (0 above the fold), 1 tab screens; blue: Send; nearly empty (22 words)
  - lead: "Write to Alan, your project manager. Alan and the team on your job read it and answer here."
  - fields: Message
  - empty states: "No messages yet Ask anything. Your project team answers here."
  - tab groups: Ask the Assistant / Write to Alan
  - tab **Ask the Assistant**: heading "Chat", 0 sections (the tab leaves for `pa`)

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

