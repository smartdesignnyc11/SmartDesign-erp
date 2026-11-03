# Sales and Clients: mock-up and spec

Mock-up only; nothing in `src/` changes until Alan says yes. Figures are the demo company's, read from the running build
(master a5b0a82, demo day Thu 9/3) as the owner; `[PLACEHOLDER]` marks what the records do not hold. Decisions it builds on:
Won means signed and Set Up the Job comes before Won; send from the app (both 10-26); inside a record everything is that
record (11-03). Triage classes 11 (inquiry to job) and 12 (mail not linked to people) are the main faults it answers.

## 1. Today's pages and tabs (census build bd3180c27e33, owner, desktop)

| Page | Where | Tabs and figures today | Screens |
|---|---|---|---|
| Sales (`ovsales`) | Sales | Leads 1, Stalled 1, No Next Step 3, Open Pipeline $1.3M; List / Board; 3 pipelines; Import, Export, Columns | 2 |
| Estimates (`billing`) | Sales › Estimates (also Billing, Projects) | Billing Queue / Progress Billing / Estimates 4 / Change Orders 2 / Invoices 6 / SOV / Payments 4 / Client Funds | 8 |
| Numbers (`salesnum`) | Sales › Numbers | First Reply 3 h, No Next Step 3, Proposals Aging 0, Won This Quarter $210K; Funnel / By Source / Lost and Why / Marketing Spend / Ranges | 7 |
| Forecast (`hbforecast`), Sales Dashboard (`hbdash`) | Numbers › links | by rep and stage; 7 dashboard panels | 7 |
| Partners (`partners`) | Sales › Partners | Thank-Yous Owed 1, Due a Touch 1, Leads This Quarter 3, Won Through Partners $210K | 1 |
| Playbook (`playbook`) | Sales › Playbook | 5 sections, 2.2 screens (4.4 on the phone) | 1 |
| Clients (`clients`) | Clients | Past Due $0, Owed to Us $92K, Unsigned 1, Waiting on Client 1; Clients / People / Companies | 3 |
| People (`hbcontacts`), Companies (`hbcompanies`) | Clients › links | Needs Follow-Up 5, New This Week 7, Unreachable 0, Decision Makers 9; 19 people, 6 companies | 10 |
| A client (`openclient:cl121`) | a row on Clients | Overview / Projects 1 / Billing 5 / Communications / Documents 5 / Activity 4 | 6 |
| Sales Settings (`hbsettings`) | Settings › Sales Settings | Pipelines / Properties / Record Customization / Products / Users & Teams | 1 |

11 pages and 46 desktop screens for the owner; the rail shows Sales 4 and Clients with no count. One label, two numbers: "No
Next Step 3" reads "3 past their date"; Stalled 1 (14 days) against "Gone Quiet 4" (8 days) in Chief of Staff; Qualified
22% here and 82% on the Dashboard; "Last Touch" reads "no contact logged" on every client although Sarah Klein wrote on 9/2.

## 2. Proposed: two sub-pages and two record pages

**Pipeline** (`Pipeline.dc.html` phone, `DeskPipeline.dc.html` desktop). Opens on Need You.
1. What: every open deal from the first inquiry to the signature, and which ones need you.
2. "Pipeline" (the approved menu's word; the owner says "pipeline" and "deals").
3. Each deal lives here once; Today shows its next step, the client page shows the client's deals.
4. The owner (he sells); the PM and coordinator see it read-only. "Which deal is slipping, and what do I do next?"
5. Not a record page; each row opens the deal.
6. Need You (next step past its date, no touch in 14 days, or signed with no job set up), then On Track; How Sales Is
   Going one tap down.
7. Need You 4 equals its rows and Today's "Deals That Need You" (and each is a row on Today); the menu group shows no badge,
   as approved 11-03.
8. One + : Lead from a Mail (filled, duplicate check shown) or Lead, Typed In.
9. One row per deal, the value labelled by its stage, 44px buttons; the desktop board is not drawn on the phone.
10. One page with three chips (Need You, All Open, Won and Lost) and a fold, replacing Sales, Numbers, Forecast, Dashboard
    and Partners' figures.

**Clients** (`Clients.dc.html`). Opens on Need You.
1. What: everyone the firm works for or with on the sales side (clients and the partners who refer them), and who is waiting.
2. "Clients". 3. A person or company lives once, under the client, partner or vendor they belong to; search finds anyone.
4. Owner, PM, billing; "who is waiting on us, and who owes us?". 5. Each row opens the client.
6. Need You (a client waiting on us, money past due, someone writing as a client who is not on file); All; Partners.
7. Need You 2 equals its rows; the header says "owed to us $92,265, none past due" in words, not a badge.
8. One + (New Client); a client made from a deal comes from Set Up the Job. 9. One column, 44px. 10. One page, three chips.

**A client's page** (`Client.dc.html` phone, `DeskClient.dc.html` desktop). Everything on it is the Kleins.
1. What: the Kleins: their job, what waits on whom, their contract and billing, every message. 2. Their name.
3. Records live in their homes (the job, the invoice, the mail); the page lists them filtered to the client.
4. PM and owner before a call; billing before a reminder. "Where do we stand with them?"
5. Every tile, count and row is theirs: Waiting on Us 2 (Sarah's 9/2 mail; the managing agent's 9/2 call about
   Friday's elevator booking, which the answering service logged as a client), Waiting on Them 6, They Owe $68,265, Left to Bill $237,516.
6. What waits on us first (Sarah's 9/2 mail, the agent's call), then what waits on them, then the sections.
7. Each tile equals its rows (6 = 5 decisions + 1 change order to sign). 8. One + "New for the Kleins": Message, Task,
   Note or Call, Meeting, Estimate, Change Order, Invoice, Job, each with the client (and the job, when there is one) filled.
9. Tiles two across, labelled; rows 52px. 10. Three tabs on the desktop (Overview, Contract and Billing, Messages),
   five rows on the phone, down from six tabs.

**A deal's page** (`Deal.dc.html`, Ana Petrova). The next step with its button, the road to signed (the close plan), Set Up
the Job, then the proposal, why she is buying, people, building and every touch, each one tap down on the page.

## 3. Old page or tab, and its new home (nothing lost)

| Old | New home |
|---|---|
| Sales › List, Board; Leads, Stalled, No Next Step tiles | Pipeline: Need You chip (one rule), All Open (board on the desktop) |
| Sales › Import, Export, Columns, Save as a View | Pipeline's desktop table menu; out of the first screen |
| Sales › Estimates (8 billing tabs) | Estimates: the deal (before the job) and the job's Contract and Billing; the other tabs to Accounting › Billing |
| Numbers (Funnel, By Source, Lost and Why, Ranges We Quote), Forecast, Sales Dashboard | Pipeline › How Sales Is Going (one fold); Marketing Spend to Reports |
| Partners (page and figures) | Clients › Partners chip; thank-yous owed in How Sales Is Going |
| Playbook | The SmartDesign Standard, Sales playbook section; each deal's next step quotes its stage's lines |
| Clients › Clients | Clients › All |
| Clients › People, Companies (HubSpot columns, 19 and 6 rows) | Inside the client, partner or vendor they belong to; ⌘K search finds anyone |
| A client › Overview, Projects | Client › Overview (their job, what waits, people and building) |
| A client › Billing (By Line, Invoices, COs, Estimates, SOV, Payments) | Client › Contract and Billing, one list; the SOV opens on the job |
| A client › Communications, Activity | Client › Messages (mail, texts, calls, portal chat, meeting notes, logged events) |
| A client › Documents | The record each file belongs to (the contract PDF on the contract, the alteration agreement on the building) |
| Sales Settings | Company and Settings › Company Settings › Sales |
| Retired, already unreachable: `hbdeals`, `hbquotes`, `hbsequences`, `hbworkspace`, `hbplaybooks`, `scleads` | Stay retired; old links land on Pipeline |

Old 11 pages and 46 desktop screens; new 2 pages (about 6 chip screens) plus the client and deal record pages.

## 4. What each role sees
| Role | Pipeline | Clients |
|---|---|---|
| Owner | All deals, edit; Need You on his Today | All; Need You |
| PM | Read-only; his deals' next steps if he owns any | His clients first; their messages and decisions |
| Coordinator | Read-only (to see what is coming) | Read-only |
| Billing | No | All, with money first; Contract and Billing tab opens by default |
| Controller, designer | No | Read-only (designer: her clients' decisions) |
| Foreman, crew, driver | No | No (the job page names the client) |
| The client (portal) | No | Their own page is the portal; unchanged here |

## 5. Decisions made, and why
- **Estimates is not a sub-page; recommend dropping it from the approved menu.** The approved menu (11-03) lists Pipeline,
  Estimates, Clients. Every estimate has a home already: the deal before the job exists, the job's Contract and Billing after.
  Alan's own verdict was "remove from Sales; add Proposals", and his open proposals are Pipeline's Proposals Out tile
  ($400,000). A third list of the same records breaks question 3. **Alan's call**: if he wants it, it is a filter of the Pipeline.
- **Need You is one rule:** a next step past its date, or no touch in 14 days. The census build counts 4 because Ana Petrova's
  deal says 9/2 while her task and close plan say 9/4; one record holds one date, so it is 3 here (Priya, Okafor, Marcus).
- **Won means signed.** The Nakamuras are signed (7/25, "handwritten note at signing") with no job on file, so their row
  offers Set Up the Job. A stage "Job Set Up, Not Signed" sits before Won on the board.
- **People and Companies fold into the records they belong to.** A HubSpot-style table of 19 people is a second home for
  each person; search covers finding one.
- **Billed $253,684 and $238,015 are one figure:** gross, and net of $15,668 retainage. The client page prints both, labelled.
- **Partners sit with Clients**, since a partner is a relationship you keep, like a client, and Alan said "merge into Companies".

## 6. Unsure, or for Alan
- Ana Petrova is a repeat client with no client record, and Aliya Chen writes as a client (374 Washington Ave) with none:
  the page offers "Add Her as a Client". Is 374 Washington Avenue real work in the demo, or a stray mail?
- No estimate is linked to Marcus Bell's or Ana Petrova's proposals (`[PLACEHOLDER]`).
- The activity log says "Sent INV-003" where the invoice is INV-2026-038: a naming slip to fix in the build (BACKLOG §10).
  The mock now shows the record's own number.
- Bank lines behind the Kleins' two payments were not read for this mock-up (`[PLACEHOLDER]`).

## 7. Self-review against the ten questions
| Page | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Pipeline | pass | pass | pass | pass | n/a | pass | pass | pass | pass | pass |
| Clients | pass, see below | pass | pass | pass | n/a | pass | pass | pass | pass | pass |
| A client | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| A deal | pass | pass | pass | pass | pass | pass | pass | pass | pass | n/a |
- Revised in review: Pipeline's first draft carried a placeholder for Signed This Quarter; the record shows the Nakamuras
  signed on 7/25, so it reads $210,000. Ana Petrova's stage bar put Signed before Job Set Up; it now follows decision 2.
- Clients question 1 holds partners as well as clients. Kept in one page because both are relationships the owner keeps on a
  cadence; if Alan reads "Clients" as clients only, Partners moves to a chip on the Pipeline.
- The desktop Pipeline's "Open Pipeline $1.3M" tile is not something waiting on you (question 7). Kept as the one "where
  things stand" figure, as the approved job page keeps Margin at Completion.

## 8. Chief of staff review (11-03, overnight)
Verdict: **build after the must-fix list below.**

| Page | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | Grade |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Pipeline | pass | pass | pass (Estimates decided, below) | pass | n/a | pass | **gap**: a signed deal with no job is not in Need You | pass | pass | pass | 8 |
| Clients | pass (partners kept) | pass | pass | pass | n/a | pass | fixed: All and Partners carry no count | pass | pass | pass | 8.5 |
| A client | pass | pass | pass | pass | fixed: the managing agent's call is the Kleins' | pass | fixed: Waiting on Us 2 | pass | pass | pass | 8.5 |
| A deal | pass | pass | pass | pass | pass | pass | pass | pass | pass | n/a | 9 |

Fixed in the mock tonight: counts off the All Open, All and Partners chips (nothing waits there; the approved job page's chips
carry none); the Kleins' Waiting on Us is 2 with R. Torres's call about Friday's delivery; the activity row names
CO-2026-002 and INV-2026-038, not "INV-003"; the deal's Set Up the Job copy no longer claims a client record that is not on file.

Calls made (DECISIONS 11-03): Estimates leaves the Sales menu, reversibly, flagged for Alan in the morning.

**Must fix before build** (11-03 overnight pass: done in the mock-up or left for the build lane)
1. **Done in mock-up, 11-03.** Need You adds "signed, no job set up": the Nakamuras (signed 7/25, 40 days) are the first row
   on the Pipeline (phone and desktop, blue Set Up the Job), a row on Today, and Today's Deals That Need You reads 4; the
   Pipeline, the tile and Today move together. Whether their deposit invoice went is still not read: the build reads it.
2. **Left for the build lane.** Billed gross, retainage and net tie to the cent from one function (BACKLOG §10 item 5); the mock
   cannot say whether gross is $253,683 or $253,684 until the records are summed.
3. **Done in mock-up, 11-03.** The stage is "Design Proposal" on the Pipeline, the desktop board, the Clients row and Company
   Settings' proposed stages. The build renames the stage in the pipeline's settings and its stored deals.
4. **Left for the build lane** (routing): old `billing` links from Sales land on Pipeline › Proposals Out (drawn on
   `DeskPipeline.dc.html`), each estimate with its deal.
5. **Done in the spec, 11-03** (section 9 below); the lane confirms each entry against `tests/ia_map.py` before it starts.

## 9. Registry (BACKLOG §1.16): what each page extends
The registry is `ONE_PLACE`, `QUEUE` and `CONTEXT_OK` in `tests/ia_map.py`, with counts named in `PRED`.

| Page | Noun (registry key) | Its one list | Queue and counts | New? |
|---|---|---|---|---|
| Pipeline | deal (`DB.deals`, `DB.leads`; add `deal: {'ovsales'}` to `ONE_PLACE`) | `ovsales`, renamed Pipeline | Need You is one predicate read by the Pipeline, its tile and Today's Deals That Need You (BACKLOG §10 item 1(b)); a deal's next step is a link to its open `task`, never a copied date | No. `salesnum`, `hbforecast`, `hbdash` fold into its How Sales Is Going fold; `partners`' figures too |
| Clients | client (`DB.clients`) and partner (a kind of company, `DB.partners` read as a filter) | `clients` | Need You: a client waiting on us, money past due, a stranger writing as a client (§10 item 4's "Who Is This?") | No. `hbcontacts` and `hbcompanies` fold into the record each person belongs to; ⌘K finds anyone |
| A client | client | the record page `openclient:<id>`; its tabs are filters of `invoice` (`billing`, `clacct`), `inbox` / message thread, `decision` (`dec`) | Waiting on Us, Waiting on Them, They Owe, Left to Bill: each equals its rows | No |
| A deal | deal | the record page; the close plan is the deal's `task` rows | its next step | No |
| Estimates | estimate | stays in `billing` (the job's Contract and Billing) and the deal; Proposals Out is a filter, not a list | Proposals Out tile | No: the menu item leaves (reversible, flagged for Alan) |

Reasons recorded: none needed, nothing new. The structure lint should add `deal` and `client` to `ONE_PLACE`; today they
are unregistered, so a second deal list would not fail.
