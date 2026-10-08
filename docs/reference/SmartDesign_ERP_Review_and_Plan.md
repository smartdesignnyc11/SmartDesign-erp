# SmartDesign ERP — Expert Review and Reorganisation Plan

**Prepared for:** Alan Mishali · **Date:** 11 September 2026
**Basis:** four specialist reviews of the running application (information architecture, ERP architecture, visual design, and a practitioner panel of eight roles), each working from 58 screenshots at desktop and phone width and from live walks of the app; plus the consultant's *ERP Review and Improvement Guide*, whose fourteen questions were the rubric.
**Status:** Passes 1–7 are built, tested and published. What remains — the entity selector (waiting on per-entity data), one project selector, a communications log as a record, and saved-search unification — is specified below.

---

## 1. The diagnosis, in one page

The complaint was: unorganised, duplicated, mislabelled, lumped together. The reviews confirmed all four and located each.

**The menu did not describe its contents.** "Clients & billing" held one view — Clients. Billing did not exist as a place; every invoice, estimate and change order lived three levels down inside a client record. "People & time" held material requests and the delivery route. Project Settings held the firm's user roster, legal entities and approval rules. Verification was reachable only by typing its view name.

**Seven screens were dashboards.** Brief, Dashboard (six presets, 41 widgets), All Projects, Today, Studio, My Day, and Reports › CEO Dashboard. Margin-at-completion appeared on three presets; WIP over/under billing on three presets *and* as a flag on twelve of sixteen cost lines; cash on five screens — and two of them disagreed ($205,581 on All Projects, $184,231 on the Brief), because one read the book balance and the other the raw bank-feed figure.

**Headings disagreed with tabs.** The tab said *All projects*, the page said *Company overview*. *Purchase orders* opened a page called *Purchasing* whose first section was a buy board and whose fourth section was the purchase orders. *Banking* was *Banking & transactions*. *Time & crew*, *Costs*, *Field*, *Receiving* — each had a second name.

**One landing page served five roles.** Owner, PM, Coordinator, Design Director and Driver all received the Owner's brief with the name swapped. Procurement landed on bank matches she cannot confirm; the design director landed on a construction job's look-ahead; the driver's Clock tab was the office payroll screen.

**Two roles did not exist.** No Billing persona, no Controller persona — the two roles the guide names explicitly.

**The visual layer amplified all of it.** Up to eight KPI tiles per screen (half saying "0"); tab rows stacked up to five deep before any data; colour used as decoration (a green *+$116,992 over-billed*); counts rendered inside labels ("To approve2"); headers truncated to "Prim…", "COs unsig…", "Bille…"; three dates styled identically in the top bar; two clocks (the app's *as-of* date and the real date) leaking into the same screen.

Under all of this the records and their links are sound. Nothing in the reviews recommends restarting; everything recommends putting each thing in one place and calling it one name.

---

## 2. The information architecture

Eight groups for the office. Mercer & Bond stays its own workspace, untouched.

| Group | Purpose | Views |
|---|---|---|
| **Home** | What needs me today, and the numbers | Brief · Dashboard |
| **Projects** | Run one job | All Projects · Today · Schedule · Tasks · Decisions · Permits · Field · Materials · Documents · Costs · Inbox · Chat · Deliveries · Project Settings |
| **Studio** | Design and filing work | Studio · My Day · Project Board · Drawings · Filings |
| **Clients** | Who and where — people, properties, conversation | Clients |
| **Billing** | Every document the client signs or pays | Billable Now · Estimates · Change Orders · Invoices · Schedule of Values · Payments · Client Funds |
| **Purchasing** | Commit to vendors, receive, return | Selections · Buy Board · Purchase Orders · Requests · Route · Vendors · Inventory |
| **Money** | Every document the firm pays or must explain | Spend · Bills & Payroll · Time & Crew · Banking · Controls |
| **Reports** | Read-only, period-bounded, printable | Reports |

**The rules that decided it.** A record lives in the module that owns its lifecycle; every other module reads it by reference. Billing owns what the client pays; Money owns what the firm pays. A control (something whose state changes when a person acts — approve, reconcile, verify) belongs in Money › Controls; a report has no state and belongs in Reports. A CRM screen shows no dollar amounts.

**Naming.** Title Case for every group, view, tab and column. Nouns for places (*Banking*, *Vendors*), verb-plus-object for buttons (*New Client*, *Create PO*). No ampersand groups joining unrelated nouns. A page heading equals its tab. A count is a separate element beside the word, never part of it. A firm-wide screen does not wear a project's name or dates.

---

## 3. What changed today — Pass 1

Built as one module (`ia.js`) and one stylesheet pass, spliced last so nothing underneath moved. 32 new checks in `ia_test.py`; 64 of the 67 existing suites pass (the three that fail — `comply`, `ns`, `pr` — failed before this pass; see §9).

**Navigation.** The eight groups above, with the labels above. *Clients & billing* → *Clients* and *Billing*. Requests and Route moved to Purchasing. Controls (formerly the hidden *Verification*) sits in Money. Every heading now says what its tab says — verified for All Projects, Purchase Orders, Banking, Buy Board, Time & Crew, Inventory and Controls. Firm-wide screens (Home, Clients, Billing, Money, Reports) no longer show the current project's completion dates in the top bar, and their breadcrumb is just the place.

**Billing exists.** A new view with the document family as tabs. Invoices, Estimates and Change Orders are cross-client lists (with a client filter) that open the *same* editor the client record uses — no second implementation, no drift. Schedule of Values and Payments are cross-client tables. Client Funds moved here from Reports, because it has actions. Billable Now puts the evidence-driven construction application and the design-and-filings billing side by side. The deep links that used to open a client's Financials tab now open Billing.

**Clients is a CRM.** The list shows Client · Contact · Phone · Email · Property · Building · Projects · Decisions · Last Contact. The four money tiles and the Revised Contract / Outstanding / Overdue columns are gone; a *Billing ›* button stands where they were. The intercompany LLC (206 Lenox) no longer appears among clients. Inside the record, the money tab is called *Billing*. A latent crash — opening a client seeded without a documents collection — is fixed.

**Roles.** Billing and Controller personas exist with their own view sets. Procurement lands on the Buy Board, the Design Director in the Studio, Billing in Billing, the Controller on Banking. The Driver's Clock is now the crew clock; the office roster, *Build payroll* and *Add time entry* are hidden from that role.

**Visual pass.** Five type steps (20/14/11/13/12); a 4-px rhythm; KPI numerals in ink, not colour — colour is reserved for state; the second tab level rendered as a segmented control instead of a second underlined row; table headers wrap instead of truncating; sort arrows and the project-selector caret are line-drawn SVG, not glyphs; pills lose their dots; nav counts sit beside the word with a space; empty states get one sentence. All against existing class names.

**Published.** The hosted artifact (v55), the Netlify bundle, and the standalone file all carry the pass.

---

## 4. Duplication register

What appears in more than one place, which place should own it, and what the others do instead. Items marked ● were resolved in Pass 1.

| Information | Appears in | Owner | The others |
|---|---|---|---|
| Cash / safe-to-spend / 13-week low | Brief; Dashboard; All Projects chart; CEO Dashboard; Banking tiles | Dashboard › Cash runway, from one function | Brief: three numbers + link. All Projects: delete chart. CEO Dashboard: delete. Banking: book **and** feed, labelled, with the gap |
| Receivables / aging | Brief; Clients tiles ●; Client › Financials; Reports; Dashboard | Billing › Invoices aging strip | Links |
| Margin at completion | 3 Dashboard presets; Costs; Procurement › Cost by line; Reports | Projects › Costs (job) and Dashboard › Owner (portfolio) | Delete Procurement › Cost by line; one preset |
| WIP over/under | 3 presets; Costs tile + section + 12 row flags; Today; All Projects; Clients column ● | Costs › Work in progress | One project-level flag; row flags only where a line differs from the project |
| Decisions | Decisions; Today; 2 widgets; Client Overview; My Day; Materials; PO board | Projects › Decisions | Counts + link; keep status pills on the blocked object |
| Field requests | Requests; PO › Field requests; Today; Route | Purchasing › Requests | Delete the PO-page section; Route reads the queue |
| From the field | Brief (PM) and Projects › Field, pixel-identical | Projects › Field | Brief: one line + link |
| Bank matches | Banking; Brief; Spend › Money to settle | Money › Banking | Delete Spend › Money to settle |
| Vendor bills queue | Bills; Spend › Vendor bills arriving; Brief ×2; Dashboard | Money › Bills | Delete the Spend pane |
| Hours to approve | Time; Spend › Hours & payroll; Bills row; Brief; Today on site; Studio | Money › Time & Payroll (site) · Studio (design) | Delete the Spend pane |
| Items to buy | Materials "Order this week"; Buy Board; PO page's buy board — three counts for one question | Purchasing › Buy Board, all projects | PO page = purchase orders only; Materials = need-by view |
| Cost by line | Costs; Procurement; Client › By line; Reports; Dashboard | Projects › Costs | Links and exports |
| Documents | Projects; Inbox panel; Client; Drawings | Projects › Documents (job) · Clients › Documents (contracts) | Delete the Inbox panel |
| Client Funds ● | Reports; PO page; Dashboard widget | Billing › Client Funds | Links |
| Global settings | Project Settings (13 sections) | Settings (rail footer) | Project Settings keeps project fields only |
| Project selector | Projects, Studio, Purchasing — three, out of sync | One, in the top bar | — |
| Clock | *As-of* date and real date on the same screen | One `today()` | Studio's real-date leak fixed |

---

## 5. Role by role

**Owner.** Landing is right. *Decide* must open the record, not the list it is in (today: three clicks and a native prompt). Cash appears in four framings in one viewport — make it one. Dashboard clones the same two decisions under three projects. *One change:* every Decide opens the thing to be decided with approve/reject above the fold, and says plainly when the money already left.

**Project Manager.** Landing is right — the best in the app. The project tile says *On target* while health is 48 and two decisions are overdue. Decisions are owed by a category, not a person, with no chase action. *One change:* a "Blocking this week" list across all jobs — field questions, overdue decisions with a name, sub no-shows — on the Brief.

**Procurement.** ● Now lands on the Buy Board. Still: three buy queues (Materials, Buy Board, PO page), and a drafted PO shows *For task: —* and *From line: —* when the links exist. Field requests are on a fourth list. *One change:* one all-projects buy queue merging selections, schedule materials, requests and returns, sorted by order-by.

**Billing.** ● Persona and module now exist. Still: Create Invoice ends in silence (no number, no Send); nothing says whether a progress bill is due on a job with $116,992 billed ahead. *One change:* the queue — ready to bill, drafts awaiting approval, sent/unpaid by age, deposits recorded but not in bank — and a Send step.

**Controller.** ● Persona exists, lands on Banking. Still: Reconcile pre-fills the statement balance with the cleared balance and pre-ticks every line, so the difference is $0 by construction; verification exceptions have no owner and no resolve action; a card charge was matched to a bill that was only PM-approved. *One change:* an honest Reconcile (typed statement balance, nothing pre-ticked) and an owner on every exception.

**Design Director.** ● Now lands in the Studio. Still: the Studio table sums phases, so Schematic at 41.5/40 hours reads as fine until the project is opened. "Hours not logged" lists future dates (real-clock leak). *One change:* colour the Hours cell by the worst phase, not the total.

**Foreman.** Landing right; receipt after sending a request is excellent. Still: two request UIs (Ask sheet then a Requests screen); the "What is it for" task defaults to the first task, so an insulation request silently costs to demolition; deliveries sit below seven sub cards with no "nothing arriving today". *One change:* one sheet, no default task, "Arriving today" on Today.

**Driver.** ● Clock is now the crew clock. Still: the store run lists an item procurement has not acknowledged; the promised dump stop is absent. *One change:* a hold state for unacknowledged items.

**Crew and Client.** Crew is right. The client portal shows *0% of the work complete* beside *Work completed $136,691 · 28%* — two denominators on one card.

---

## 6. The design standard

Applied in Pass 1 as CSS; the markup rules follow in Pass 2.

- **Type:** page title 20/600 · section 14/600 · table header 11/600 uppercase · body 13 · caption 12 · numeral 24/600 tabular. A page has a heading only when the tab does not already name it.
- **Rhythm:** 4-px base; 8 inside a component, 16 between related, 24 between sections; gutter 32 desktop / 16 phone; row 40 desktop / 48 phone; one column by default, a right sidebar only for secondary information.
- **Colour:** ink ×4, paper ×3, rule ×2, one accent, four states. Colour is state, never decoration. The accent appears in exactly three places: the one primary button per view, the active tab, links.
- **Components:** KPI strip max 4 and only where the numbers drive action today; one tab row per page, second level a segmented switch, third level a filter row or left rail; tables never truncate a header; cards only where an image is the point; empty states are one sentence and one button; a badge is its own element; one primary button per view; five pill states.
- **Icons:** line-drawn 24 px, 1.8 stroke, in nav and phone tab bar only. The remaining glyphs — ✕ ✓ ⚠ ▲ ▼ ● and the emoji in pickers (🧰 📦 💬 📎 📄 📐) — are listed for replacement in Pass 2.
- **Phone:** 44-px targets, one primary action per screen, the bottom sheet for any per-item action, the *Signed in as* toast gone in two seconds.

---

## 7. ERP boundaries and data

Findings from the architecture review that go beyond navigation.

**Four progress-percent engines.** `billingSuggestions` (cost-to-cost), `progressPrefill` (pre-fills a progress invoice from actual ÷ budget — the exact "cost is progress" error the brief forbids, and it is what the client record's *New progress invoice* produces), `pgRows` (evidence-driven, correct), and `ptBillable`. Keep `pgRows`; route the others through it; delete `progressPrefill`.

**Two cash numbers.** `companyBalance()` returns the book balance; `renderBank` displays `account.balance`, the raw feed figure. Rule: no screen reads the feed balance except Banking, which shows both, labelled, with the gap as a reconciliation control. `companyBalance` is wrapped three times and one wrapper recomputes *available* from a stale input — collapse to one definition.

**The CRM record set.** Leads before clients (today a prospect is a $0 client with a draft estimate, which inflates *contracted*). Properties as first-class records with building type (condo / co-op / townhouse), managing agent, superintendent, alteration-agreement and elevator rules — per building, so a client with two addresses works. Contacts with typed roles (decision, payer, owner's rep, architect of record, super) that Billing, Decisions and Purchasing read. A communications log as a record, not a regex over email addresses.

**Multi-entity.** SD Plumbing and SD Electric share one bank list and one approval ladder. An entity selector in the top bar should govern Banking, Bills & Payroll queues, approval thresholds, numbering and payroll runs; every AR document needs an `entityId`. Never mixed: bank accounts across entities in one reconciliation; consolidated P&L without intercompany elimination; Mercer & Bond in the SD selector.

**NetSuite's one idea, applied.** A saved search over a dataset renders as a KPI, a reminder, a portlet and a report. The app is 80% there (`REP_DS`, `search.js`) and then forks three ways: Reports › Build a Report is a second unsaveable query builder; Dashboard › Customize offers 40 hard-coded widgets that compute their own numbers; KPIs are defined in four places. Unify: one registry of datasets, metrics and saved searches; every portlet references a search or a metric; one builder, reachable from Dashboard › Customize; Reports lists saved searches read-only.

---

## 8. The plan

Each pass is one coherent workflow, tested against the real screens before it is called done.

| Pass | What | Why first | Files | Risk |
|---|---|---|---|---|
| **1 ●** | Eight groups; Billing view; CRM list; role landings; Billing/Controller personas; heading = tab; design CSS | The menu is what everyone touches; nothing under it moves | `ia.js`, `ia.css` | Done — 32 checks, 64/67 suites |
| **2 ●** | The Buy Board carries both populations (Finish Selections · Contract Lines & Requests) and the PO page is the purchase orders; *Decide* opens the bill itself, and an analyst finding about one vendor's bill opens that bill; a document you just created is the next thing on screen; Billing opens on a worklist — ready to bill, drafts to send, sent-not-paid by age, recorded-not-in-bank; the foreman's material request must name the work it is for (nothing pre-chosen) and Today opens with *Arriving today*; the Studio table names the phase that is over | The highest-traffic dead ends the panel hit | `pass2.js`, `pass2b.js` | Done — 22 checks; `buy_test`/`f3_test` updated for the moved board and the required pick |
| **3 ●** | Reconcile takes a typed statement balance with nothing pre-ticked; Banking tiles show book and bank feed with the gap; the progress-invoice pre-fill now comes from `pgRows` — schedule where trackable, deliveries for materials, cost only as a labelled fallback, and a line with no evidence left blank; every verification exception carries an owner (serious flags → Owner, missing receipt → the card holder, the rest → Controller), its age, and a Respond action. Still open: the entity selector — the seed data puts everything on one entity, so it would show nothing yet | Numbers people trust | `pass3.js`, `pass3b.js`, `pass3c.js` | Done — 21 checks |
| **4** | ● Dashboards: four views (My Dashboard · Owner · Projects · Studio), 59 widgets, each on exactly one view. ● Spend keeps money-out; Ready to bill and Design & filings went to Billing; approval routing, terms and reconciled-through joined Verification under Money › Controls. ● Reports lost the CEO Dashboard and Client Funds (old links redirect). ● Settings: the firm's twelve sections leave Project Settings for a Settings entry in the rail footer; Project Settings keeps the project. ● One clock: the as-of date is the firm's, set once under Settings, read by every project. Still open: one project selector | Duplication register, resolved | `pass4a.js`, `pass4b.js`, `pass4c.js` | Done — 32 checks; six suites re-pointed at the moved panes, one retired |
| **6 ●** | The worst screens by layout: All Projects is one sortable table (health · done · urgent · completion · vs target · contract · billed · outstanding · next) instead of a card per client per project, and the cash chart above it is gone — the Dashboard owns cash; the Buy Board header no longer repeats the Vendors and Deliveries tabs; a lump-billed contract shows one note above the Costs table instead of "billed 52% vs N% complete" on twelve of sixteen lines | The IA reviewer's ten worst | `pass6.js` — 9 checks | Low |
| **5** | ● Buildings as records on the client — address, building type (townhouse · condo · co-op · single-family · multi-family · commercial), and for a condo or co-op the managing company, agent and superintendent, revealed only when the building needs them; a client can hold several. ● Typed contact roles (Owner — decisions, Owner — payments, Owner's rep, Architect of record, Attorney, Managing agent, Superintendent, Tenant). ● Leads before clients — a Leads tab beside Clients with stage, scope, source, next step and due date; Won creates the client with the building and contact carried over; Lost asks why. ● The foreman's required task and Arriving today, and the Studio's worst phase, landed in Pass 2. ● The foreman's material request is one sheet: choose the work, say what you need, check the list (read locally, at once, lines editable, "did you forget"), send, receipt — no second screen. ● The driver's store list holds any line the office has not acknowledged: checkbox disabled, the line says why, a note at the top. Still open: communications log as a record; saved-search unification | The guide's explicit requirements, and the long tail | `crm.js`, `pass7.js` — 22 checks | Low per item |

---

## 9. Boundaries and known items

- **Pre-existing test failures**: `comply`, `ns` and `pr` were repaired during Pass 2 (a persona that changed role, a classic-home button, a typo). `home2`, `home3` and `boot` fail identically on the build from before this work; they test the classic portlet home and a boot-time fault injection, and are left as they were. `dash_test` was retired with the report dashboard it tested.
- **Not touched:** Mercer & Bond workspace; the foreman's phone module; the client portal; every renderer and record shape. The IA module only reorganises where things sit and what they are called.
- **The commitment guard, construction deposit at signing, per-line approval/e-signature, landed-cost comparison, subcontractor compliance, closeout/warranty and multi-entity consolidation** remain on the back burner as recorded in the system brief.
- **Screenshots** of every screen before the pass are kept for comparison; after-screenshots for Billing, Clients, Purchase Orders, Banking and Spend accompany this document.
