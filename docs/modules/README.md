# The Module Census

**Asked by Alan, 2026-10-26:** "Go through all the modules with screenshots. It's important to understand the format of every page and what's on it." Each module has a census: every page, tab and sub-tab each role reaches, the way the person reaches it, at 1440 and at 390, with a screenshot of every screen. The four loop experts (owner, PM, procurement, accounting) and the client expert walk their modules with these in hand in round one of the improvement loop (docs/IMPROVEMENT_LOOP.md).

**One build:** bd3180c27e33 (every module census of this round, the Projects census included). Walked by `tests/module_census.py` (every module but Projects) and `tests/projects_census.py` (Projects, two jobs), each run once through `tests/slot.sh`. Screenshots: `review/census/<module>/shots/`; the first screen of each page is committed, the tabs stay on the machine that ran it.

A page belongs to the module whose menu group holds it, read from the running menu (`mnMap()`); More and Settings place each page by its noun, and a page in two groups is walked in each module that holds it. Pages, tab screens and screens count what each role reaches; each cell reads desktop / phone.

| Module | Primary role | Roles walked | Pages | Tab screens | Screens | Top three duplications | Census |
|---|---|---|---|---|---|---|---|
| Today | every role | 7 | 3 / 3 (Owner; screens: every role) | 31 / 7 | 132 / 51 | Chief of Staff is the same page as Company and Settings › The Brain (`pa`); Approvals and Chief of Staff list 30 of the same records; Approvals and Today list 23 of the same records | [today_census.md](today_census.md) |
| Sales and Clients | the owner | 6 | 11 / 11 (Owner; screens: every role) | 30 / 31 | 128 / 130 | Estimates is the same page as Billing › Billing, Projects › Change Orders, Projects › Estimates (`billing`); Estimates and Accounting › Reports list 20 of the same records; `billing` sits in 4 menu places (Projects › Change Orders, Projects › Estimates, Accounting › Billing, Sales › Estimates) | [sales_census.md](sales_census.md) |
| Projects | the PM | 10 | 18 / 18 (PM, 121 State Street; screens: every role, two jobs) | 57 / 41 | 644 / 506 | Job Page and Tasks list 27 of the same records; Job Page and Schedule list 22 of the same records; Schedule and Tasks list 22 of the same records | [projects_census.md](projects_census.md) |
| Field and Site | the foreman and the PM | 6 | 9 / 9 (Foreman; screens: every role) | 23 / 19 | 64 / 56 | Daily Log and Today › Today list 9 of the same records; Daily Log and Schedule list 8 of the same records; Raise and Tasks and Messages › Messages list 5 of the same records | [field_census.md](field_census.md) |
| Design | the designer and the PM | 4 | 5 / 5 (Designer; screens: every role) | 8 / 8 | 46 / 46 | Project Board and Projects › Decisions list 9 of the same records; Project Board and Today › Today list 7 of the same records; Design and Accounting › Dashboard list 4 of the same records | [design_census.md](design_census.md) |
| Purchasing | the coordinator | 5 | 6 / 6 (Coordinator; screens: every role) | 11 / 8 | 56 / 47 | Orders and Today › Chief of Staff list 13 of the same records; Orders and Company and Settings › The Brain list 13 of the same records; Buy Board and Orders list 9 of the same records | [purchasing_census.md](purchasing_census.md) |
| Billing | billing | 4 | 1 / 1 (Billing; screens: every role) | 7 / 7 | 32 / 32 | Billing and Accounting › Reports list 20 of the same records | [billing_census.md](billing_census.md) |
| Accounting | the controller | 6 | 9 / 9 (Controller; screens: every role) | 51 / 46 | 229 / 206 | Banking and Ledger list 95 of the same records; Banking and Controls list 94 of the same records; Controls and Ledger list 89 of the same records | [accounting_census.md](accounting_census.md) |
| Time and Payroll | the controller, the coordinator and the crew | 6 | 1 / 1 (Controller; screens: every role) | 3 / 3 | 24 / 24 | - | [timepay_census.md](timepay_census.md) |
| Tasks and Messages | every office role | 9 | 3 / 3 (Owner; screens: every role) | 28 / 9 | 170 / 66 | Tasks and Projects › Tasks list 34 of the same records; Meetings and Today › Chief of Staff list 8 of the same records; `tkall` sits in 2 menu places (Today › Tasks, Tasks › Tasks) | [tasks_census.md](tasks_census.md) |
| Company and Settings | the owner | 9 | 12 / 12 (Owner; screens: every role) | 25 / 15 | 163 / 105 | The Brain is the same page as Today › Chief of Staff (`pa`); Company Settings is the same page as Projects › Project Settings (`proj`); Company Settings and Accounting › Reports list 19 of the same records | [company_census.md](company_census.md) |
| The Client Portal | the client | 1 | 5 / 5 (Client; screens: every role) | 1 / 1 | 6 / 6 | Overview and Schedule list 16 of the same records; Decisions and Overview list 13 of the same records; Decisions and Schedule list 9 of the same records | [client_census.md](client_census.md) |

**Where each role starts** (the first page after sign-in, and its module): Owner `home` (Today); PM (Alan) `home` (Today); Coordinator (Chen) `home` (Today); Foreman (Angel) `ftoday` (Today); Designer (Sarah) `sday` (Today); Billing `home` (Today); Controller `home` (Today); Crew (Alberto) `time` (Time and Payroll); Driver (Alex) `route` (Field and Site); Client (Klein) `client` (The Client Portal).

## Pages, Tabs and Screens per Role and Device

Each cell: pages / tab screens / screens, desktop then phone. "-" means the role opens no page of the module.

| Module | Owner | PM | Coordinator | Foreman | Designer | Billing | Controller | Client | Crew | Driver |
|---|---|---|---|---|---|---|---|---|---|---|
| Today | 3/31/34 · 3/7/10 | 3/26/29 · 3/10/13 | 3/24/27 · 3/8/11 | 1/0/1 · 1/0/1 | 1/0/1 · 1/0/1 | 3/13/16 · 3/4/7 | 3/21/24 · 3/5/8 | - | - | - |
| Sales and Clients | 11/30/41 · 11/31/42 | 10/23/33 · 10/24/34 | 9/17/26 · 9/17/26 | - | 1/0/1 · 1/0/1 | 9/17/26 · 9/17/26 | 1/0/1 · 1/0/1 | - | - | - |
| Projects | 17/57/74 · 17/39/57 | 18/57/75 · 18/41/60 | 14/47/61 · 14/30/45 | 8/23/31 · 8/19/27 | 6/41/47 · 6/24/30 | 2/10/12 · 2/10/13 | 1/2/3 · 1/2/3 | 5/1/6 · 5/1/6 | 5/11/16 · 5/7/12 | 2/7/9 · 2/7/9 |
| Field and Site | 2/0/2 · 2/0/2 | 2/0/2 · 2/0/2 | 2/0/2 · 2/0/2 | 9/23/32 · 9/19/28 | - | - | - | - | 5/11/16 · 5/7/12 | 3/7/10 · 3/7/10 |
| Design | 6/8/14 · 6/8/14 | 5/8/13 · 5/8/13 | 1/5/6 · 1/5/6 | - | 5/8/13 · 5/8/13 | - | - | - | - | - |
| Purchasing | 6/12/18 · 6/9/15 | 6/11/17 · 6/8/14 | 6/11/17 · 6/8/14 | - | - | 1/0/1 · 1/0/1 | 3/0/3 · 3/0/3 | - | - | - |
| Billing | 1/7/8 · 1/7/8 | 1/7/8 · 1/7/8 | - | - | - | 1/7/8 · 1/7/8 | 1/7/8 · 1/7/8 | - | - | - |
| Accounting | 9/54/63 · 9/47/56 | 7/48/55 · 7/41/48 | 1/1/2 · 1/1/2 | - | 1/1/2 · 1/1/2 | 6/41/47 · 6/37/43 | 9/51/60 · 9/46/55 | - | - | - |
| Time and Payroll | 1/3/4 · 1/3/4 | 1/3/4 · 1/3/4 | 1/3/4 · 1/3/4 | - | - | - | 1/3/4 · 1/3/4 | - | 1/3/4 · 1/3/4 | 1/3/4 · 1/3/4 |
| Tasks and Messages | 3/28/31 · 3/9/12 | 3/20/23 · 3/7/10 | 3/21/24 · 3/7/10 | 1/2/3 · 1/1/2 | 2/23/25 · 2/4/6 | 3/27/30 · 3/8/11 | 3/27/30 · 3/8/11 | - | 1/1/2 · 1/1/2 | 1/1/2 · 1/1/2 |
| Company and Settings | 12/25/37 · 12/15/27 | 11/28/39 · 11/12/23 | 9/25/34 · 9/9/18 | 3/0/3 · 3/0/3 | 3/2/5 · 3/2/5 | 4/2/6 · 4/2/6 | 8/25/33 · 8/9/17 | - | 3/0/3 · 3/0/3 | 3/0/3 · 3/0/3 |
| The Client Portal | - | - | - | - | - | - | - | 5/1/6 · 5/1/6 | - | - |

Projects counts 121 State Street only (its census also walks a design-stage job).

