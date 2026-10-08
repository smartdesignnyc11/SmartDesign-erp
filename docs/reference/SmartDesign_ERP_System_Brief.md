# SmartDesign / Mercer & Bond — ERP prototype
## System brief for technical review

**Prepared for:** an external reviewer assessing the working prototype and recommending improvements
**Subject of review:** `smartdesigns_projects.html` — a single self-contained file, ~2.75 MB
**Date:** 10 September 2026

---

## 0. How to open it

Open the HTML file in a browser. There is no server, no build step and no install. It runs entirely
client-side and stores its data in the browser's `localStorage`, seeding a full demonstration dataset on
first run — four projects, four clients, eleven vendors, 88 bank transactions, 30 time entries, a
schedule of values, purchase orders, bills, filings and an audit trail.

A sign-in screen offers **thirteen personas**. The application is role-shaped: what you can see and do
is a function of who you signed in as, and reviewing it as one role will give a misleading picture.
Section 6 says which personas matter and what to do as each.

Two things about the prototype, so they are not mistaken for design decisions:

- **No backend.** Everything is in one file. A production build would put this behind an API and a
  database; the data model here is written as though that is coming.
- **An assistant endpoint is optional.** Several features call a language model (parsing a request,
  reading a receipt, finding invoices in email). **Every one of them has a deterministic offline path**,
  and the offline path is what runs when the network is absent. That is deliberate — see §2, rule 5.

---

## 1. The objective

SmartDesign NYC is a vertically integrated design-build firm working on landmark brownstones and
townhouses in New York City historic districts, with wholly owned plumbing and electrical subsidiaries.
It designs, files, builds and, under the Mercer & Bond brand, develops. That means one job carries a
design contract billed in hours, filings billed as fixed fees against agency milestones, and a
construction contract billed as progress against a schedule of values — three different commercial
shapes on the same address, at the same time.

**The problem this system exists to solve is not reporting. It is that facts are known at the moment
they happen and lost before they reach the ledger.**

The firm's own review of its accounting, transcribed and analysed in full, produced the diagnosis:

- The bank feed says "Apple" nine times and breaks nothing down, so the bookkeeper opens the bank in a
  second window and clicks through each charge.
- Sub-cards roll into the parent account, so nobody can see who spent what.
- Receipts arrive as photographs in an email folder, searched by date or by amount.
- One supplier receipt is timber for the window frames **and** masks for the crew, so it is split by
  hand and the real answer typed into a memo field no report can read.
- Cost codes are "just numbers" copied into that memo.
- Nothing ties to a line on an estimate. Asked whether costs matched estimate lines, the bookkeeper's
  answer was: *"never has."*

And the consequence, all of it found by one person reading rather than by any system: a $2,200 washer
and dryer billed at $1,648.98; a pull-out never billed; a second pull-out ordered and billed once; a
hood that cost more than the client was charged; $9,030 of European oak sitting unpriced. The owner's
question — *"who says that there aren't more that aren't caught?"* — is the requirement.

**Every one of those facts existed at the moment of purchase.** The person at the counter knew the job,
the line and what it was for. So the design objective is:

> Capture each fact where it is created, carry it forward on the record itself, and make every
> downstream number a **reading** of those records rather than a reconstruction of them.

A secondary objective, equally load-bearing: **tell people before it is too late to act.** A design
studio 40 hours past a client's agreed hours, a purchase order cut past a line's budget, a filing stage
approved and never invoiced — each is a decision that was free yesterday and expensive today.

---

## 2. The five rules the system is built on

These are not style preferences. They are enforced in code, they explain most of the design decisions a
reviewer will encounter, and departures from them should be treated as defects.

**1. One record, many lenses.** A cost, an hour, a selection or a line is stored once. Grids, reports,
dashboards and client documents are *readings* of that record, never separate copies. If a number
appears in two places it is computed twice from the same record, not stored twice.

**2. Machine proposes, person confirms.** Nothing posts on its own. Matching, categorising, splitting a
receipt, filling a progress invoice, assigning a card — all of it produces proposals with the evidence
attached, and a person confirms. This is what makes the numbers defensible.

**3. Say what you know; refuse to guess what you do not.** Where the system cannot determine something
it says so and leaves it blank rather than filling in a plausible default. Examples in the code: a
schedule that shows nothing started on a trade money has been spent on is treated as *absent evidence*,
not as evidence of zero; a receipt line with nothing to identify it is left uncoded rather than dropped
into "materials"; a time entry whose cost code is ambiguous is shown as ambiguous.

**4. A control that fires on everything is a control nobody reads.** Findings are tuned hard. During
development the progress-billing screen produced 15 warnings on one job; three successive corrections
reduced it to 2, both real. Reviewers should treat noisy output as a bug of equal severity to a wrong
number.

**5. Offline first where the work is.** The field runs in cellars and on blocks with no signal. Any
feature a foreman or crew member uses answers immediately from local logic and is *refined* by the
assistant if and when it replies — never the other way round.

---

## 3. How everything is linked

This is the core of the system and the thing most worth scrutinising.

### 3.1 The universal key: the estimate line

Every cost, commitment, hour and bill in the system points at a **contract line** through a single
string key:

```
estimate:<estimateId>:<lineId>        e.g.  estimate:es1:l1
co:<changeOrderId>:<lineId>           (change-order lines are first-class contract lines)
```

`findLine(key)` resolves it. `lineFin(key)` is the single function that computes everything financial
about a line — price, budget, billed %, collected, retained, outstanding, committed on open POs, actual
cost, projected cost, margin, hours budget, hours spent, overhead burden and true margin. **Every
financial screen in the application reads `lineFin`.** That is rule 1 made concrete, and it is the first
thing a reviewer should stress-test.

### 3.2 The two classification axes

Every cost carries two independent labels, and conflating them is a common failure in construction
software:

- **Cost code** (`COST_CODES`, 22 of them: 01 general conditions … 14 permits, then **15–21 for the
  professional side** — architecture, interior design, MEP, structural, filing and expediting, testing
  and surveys, special inspections — and 99 unassigned). This is *what the money was for*.
- **Category** (`CATEGORIES`) with a `type` of `cogs`, `oh`, `inc` or `non`. This is *how it behaves in
  the P&L*. Overhead never mixes into gross profit; it is applied through one burden rate computed from
  the last three months and shown behind a single firm-wide Gross / After-overhead switch.

A **cost class** — rough materials · finish materials · labour · subs · other — is decided once, at the
source, by the person who was there.

### 3.3 The chain, end to end

```
   ESTIMATE LINE  ──────────────────────────────────────────────────────┐
        │  (converted)                                                   │
        ├──► SCHEDULE OF VALUES line  (sov.lineRef = the line key)       │
        │         └──► progress invoice line  (l.sovId)  ──► pay app     │
        │                                                                │
        ├──► SCHEDULE TASK  (task.trade → codeForTrade → cost code)      │
        │         ├──► material REQUEST (req.taskId)                     │
        │         │        └──► PURCHASE ORDER line (po.line = key,      │
        │         │              po.line.code)                           │
        │         │                   ├──► receipt of goods (l.received) │
        │         │                   ├──► VENDOR BILL (bill.poId,       │
        │         │                   │      bill.line, three-way match) │
        │         │                   └──► BANK TRANSACTION (t.poId)     │
        │         └──► TIME ENTRY work split (w.taskId, w.code, w.line)  │
        │                   └──► PAYROLL RUN ──► labour cost on the line │
        │                                                                │
        ├──► SELECTION (finish material) sel.id ──► po.line.selId        │
        │         └──► client-facing selection sheet / FM package        │
        │                                                                │
        └──► SPEND RECORD (field receipt, card purchase, reimbursement)  │
                  ├── carries: job · line · cost code · class · who ·    │
                  │            evidence · authorisation                  │
                  └──► settles a BANK TRANSACTION (spend.txnId)  ────────┘
                            └── the transaction INHERITS all of it
```

**The single most important idea in the system is the direction of that last arrow.** Conventional
accounting software asks the bank transaction *"what are you?"* weeks after the fact. Here the record is
born where the money is committed — at the counter, on the timesheet, on the purchase order — carrying
everything a person knew at that moment. The bank transaction then has exactly one job, and it is not
data entry: **find the spend record it settles.** Everything else it inherits. A transaction that finds
nothing is money that left with nobody's name on it — a finding, not a chore.

### 3.4 Worked example — follow one dollar

A crew member buys Douglas fir and a box of N95 masks on one supplier receipt, on the field card.

1. **At the counter** he photographs the receipt in the app. The reader extracts every printed line with
   quantity and unit price, and codes each from a construction vocabulary (`RC_VOCAB`): lumber → 03
   framing, masks → 01 general conditions *as "other", not as rough materials*. It also reads the
   handwriting on the paper and checks it against the print — see §5.
2. The record is created as **two costs on one receipt**, each with its own line, code and class, and
   the crew member's note survives verbatim in the language he wrote it (the capture form speaks
   English and Spanish).
3. **Somebody approves it.** Who and when are recorded; a rejection carries a reason back.
4. **A week later the card charge clears.** It is scored against open spend records on amount, vendor
   and timing — a charge dated before the purchase is never proposed — and one record settles one
   transaction. Confirming hands the transaction the job, the two lines, the two cost codes, the
   classes, the receipt image and the person, and writes the split rather than a lump.
5. The card's last four, read off the paper, identifies **which card and therefore which person** — the
   sub-card blindness that made "who is spending what" unanswerable.
6. The lumber now appears on the framing line's actual cost, in cost-by-line, in profit-at-completion,
   and — if it has not been billed — in *Cost not billed*, which is a draft progress invoice away.

### 3.5 Worked example — follow one hour

1. The foreman **clocks in**. Location picks the job: within 300 m it clocks him into the site he is
   standing on; beyond that it asks rather than guesses, because a wrong job on a timesheet is wrong in
   two places and looks right in both.
2. He works. He marks tasks started and done on Today.
3. He **clocks out**. One question: which of today's work did the hours go to? Today's scheduled tasks
   are listed with their cost codes, pre-ticked from what he marked started, hours splitting evenly
   across what is ticked, adjustable.
4. Each split carries `taskId` → the task's trade → `codeForTrade` → the cost code, and the task's
   `lineRef` where one exists. `labLineFor()` resolves the estimate line in order of trustworthiness:
   **stated · from the task · from a unique cost code · honestly unresolved.**
5. **Run payroll** takes approved hours and approved reimbursements together, creates labour spend
   records carrying line and code, settles both against the run and marks the hours paid.
6. The hour is now on the line, next to materials, subs and finish, in the same margin calculation.

---

## 4. The roles

Thirteen personas. Role is not a permission layer bolted on top — it determines the whole shape of the
interface, and three of them get a purpose-built phone UI rather than a filtered version of the desktop.

| Persona | Role | Sees | Purpose |
|---|---|---|---|
| **Owner** | `owner` | 43 views | Everything, plus approvals above threshold, escalations and the audit trail. The only role that can approve at the top of the ladder. |
| **Alan** | `pm` | 34 views | Runs jobs: schedule, decisions, filings, client documents, change orders, margin. Answers the field. |
| **Chen Biron** | `coord` | 24 views | Procurement: selections, purchase orders, deliveries, returns and credits, vendor management, the requests queue. |
| **Angel** | `foreman` | 9 views | **Phone-first.** Five places — Today · Ask · Site · Crew · Log. Runs the site and is the origin of most field data. |
| **Alberto, Satish** | `crew` | 7 views | Phone. Clock, requests, schedule, photos, chat. |
| **Alex** | `driver` | 5 views | Phone. The day's route — pickups, purchases, drop-offs, dump runs — planned by capacity and distance. |
| **Sarah Davis** | `designer` | 12 views | The studio: rooms, drawings, filings, the day sheet where design hours are logged against proposal phases. |
| **Design director** | `design_mgr` | 18 views | Every design job on one screen: hours against the proposal, retainers, filings in review, surveys outstanding, sheets to re-issue. |
| **Sarah Klein, Cambri Jessop** | `client` | 4 views | Client portal: their documents, selections to approve, progress. Sees nothing internal. |
| **Rachel, Priya** | `mb_user`, `mb_analyst` | 8 views | Mercer & Bond acquisitions — the development and Historic Tax Credit side, deliberately partitioned from the construction business. |

### Why the foreman is phone-first and what he does

The foreman is the origin of most of what the office later has to reconcile, so his module was rebuilt
around the actual shape of a day rather than around the data structures behind it:

- **Today** — the clock (geo-based, §3.5) and today's work off the schedule, marked started and done.
- **Ask** — the three things that leave a site, told apart by what they *are*: **materials** (which open
  by asking what work they are for, so the cost has somewhere to go), a **dump run** (a size, a location
  and a date — a different kind of thing entirely), and a **problem or question**, routed by type to the
  right person with a clock on it. Everything sent produces a **receipt**: what was asked for, who has
  it now, when it is needed, and an undo.
- **Site** — everything arriving: subcontractors confirmed / on site / no-show, and deliveries received.
- **Crew** — hours to approve, with the ones worth questioning flagged (late start, far from site, no
  work logged).
- **Log** — the daily record, pre-filled from the clock, the subs and what was marked done. It is the
  legal record if there is ever a dispute.

---

## 5. Feature areas — what each does and how it links

### Estimating and selections
Estimates with 22 cost codes, per-line budgets, drag-to-reorder, and a **column registry** for finish
materials with images, resizable and sortable columns, custom columns and a client-preview mode that
shows only client-visible fields. A browser clipper captures vendor pages into selection records
(product, SKU, price, finish, dimensions, lead time, spec sheets), which are verified against the vendor
page and become purchase-order lines. Selections carry `selId` onto PO lines, which is how a material
cost is later known to be *finish* rather than *rough*.

### Purchasing
The purchase order is a **document, not a dialog**: items are selected on the board and land on an
editable PO. One vendor and one job per PO, always, because it must match one payment and be
job-costable. Splitting by vendor, by FM package or into one document is the buyer's choice. Every PO
line carries its estimate line and cost code. Guardrails: an item already on a live PO cannot be bought
twice; an unresolved verification flag stops that item, not the whole run; the vendor's promised date
and our required-on-site date are separate fields.

### Receiving, returns and credits
Deliveries checked in against PO lines. Returns tracked to the credit that should follow, with chase
windows and a distinction between a box still on site and one in transit.

### Spend — where money starts
Field capture with the camera, splits as first-class, approval, settlement scoring, orphan detection
(money with nobody's name on it, excluding overhead), and **cost the client has not been billed for**,
computed per contract line. On the seeded job that last one finds $15,620.

### Reading the paper
A receipt reader that extracts every printed line and codes it from the counter's vocabulary, and reads
the **handwriting** on the receipt — checking it against the print under one rule, enforced in code:

> **Handwriting chooses among what the printed receipt already says. It never overrides it.**

Ink that agrees raises confidence and fills the answer in. Ink that disagrees is a finding and the print
stands. A written amount is checked against every printed line *and against the smallest run of lines
that sums to it*, which is how "86.18 office" is confirmed as the masks plus the contractor bags. The
splits always sum to the paper; what could not be classified is carried as a visible unclassified
remainder rather than quietly vanishing.

### Cards
A register of the firm's cards with holders, so the parent-account rollup stops being opaque. Which card
a charge belongs to resolves in order of trust — stated · the last four on the receipt · the last four
in the feed · the only live card on that account — with the first three stamped as facts and the fourth
only ever proposed. Per card and per person: what went out, how much came back with a receipt, how much
has still not reached a job.

### Vendor bills — three-way match
Invoices read from email or pasted, matched against **the purchase order, what was received, and what is
being invoiced**. Catches duplicates (including a resend under a new number for the same money in the
same fortnight), over-quantity, price variance *measured by what the difference costs rather than the
per-unit gap*, goods not received, over-total and over-cumulative, and bills with no PO at all. Equally
important, it refuses to flag unit-of-measure differences and lump-sum invoices, which are not errors.

### Controls
- **Reconciled through** — statements typed from the paper, because checking the feed against the feed
  proves nothing. Produces the number the firm has never had: a **date the books are true up to**, with
  a gap in the middle breaking the run.
- **Approval routing** — a ladder by size (coordinator → PM → owner) *and* controls that ignore size
  entirely: no purchase order behind it, a vendor's first payment, a bill that takes an order over, and
  **a vendor whose bank details changed recently** — the most common construction fraud, using a field
  that was already on the vendor record and had never been read. Nobody approves what they raised.
- **Terms** — "2/10 net 30" parsed and annualised. Two percent for paying twenty days early is a ~37%
  annual return; the screen says so, and says what has already been given away.

### Billing
Progress billing on a G702/G703 pay application with retainage, previous applications and change orders.
The percentage per line is **proposed from evidence** — the schedule where the work is trackable,
deliveries for material lines, cost only as a labelled fallback capped at 100%. The governing rule:

> **Cost is not progress.** Sixty percent of a budget spent can mean sixty percent complete or a line
> running badly over. Billing off cost would quietly convert an overrun into an invoice.

Materials on site but not installed are identified separately and billed only where the contract allows.

### Design contracts
Design is sold as **hours**; filings as **fixed fees**. Two ceilings are tracked and never conflated:
**hours paid for** (money collected ÷ rate — a cash problem, answered by an invoice) and **hours agreed**
(the signed proposal — a scope problem, answered by the client's signature). The guard runs at the
moment an hour is logged, not in a report afterwards. Hours go against **phases** matching the proposal's
own line items; a phase over its estimate is *information*, the job over its total is a *problem*, and
the phase warning always shows where the job stands so somebody can decide not to act. Work that is not
on the proposal at all is logged as exactly that and prompts the client conversation the same day.

Filings bill 50% deposit at signing · 30% on submission · 10% on approval · 10% at sign-off, driven by
dates the agencies have already put on the record. A **deposit at signing** action raises half the whole
contract on one document, less anything already invoiced against either half.

### Reporting
Cost by line (rough / labour / subs / finish), profit now versus at completion, WIP over/under billing,
cash runway, backlog, retainage, DSO, margin at completion versus bid, and a NetSuite-style analytics
layer where panels are composed rather than hard-coded.

---

## 6. How to review this

**Sign in as at least four personas.** Reviewing as the Owner only will hide most of the design.

1. **Angel (Foreman), on a phone-width window.** Clock in. Mark work started. Ask for materials and note
   what it asks you first. Send a dump run. Clock out and answer the day question. This is the origin of
   the data everything else depends on.
2. **Chen Biron (Coordinator).** Selections → purchase orders → receiving. Cut a PO from the board.
3. **Alan (PM).** Money → the five groups. Read *Cost not billed*, then *Ready to bill*. Then
   *Design & filings*.
4. **Owner.** *Who has to say yes* and *Reconciled through*.

**Questions worth answering, in rough order of value to us:**

1. **Does the linkage in §3 actually hold everywhere?** Find a screen where a number is stored rather
   than computed from `lineFin`, or where a cost reaches a report without a line key.
2. **Where does the system guess?** Rule 3 says it should not. Find where it does.
3. **Where is it noisy?** Rule 4. A finding that would fire on most jobs most weeks is a defect.
4. **What would break at 40 projects instead of 4?** Both in performance and in whether a screen still
   makes sense at that volume.
5. **What is missing that a firm of this shape needs?** Particularly around: subcontractor management
   (compliance, insurance expiry, lien waivers), warranty and punch after closeout, and multi-entity
   consolidation across the parent and the two subsidiaries.
6. **The data model, judged as though a backend is coming.** Where would this shape hurt when it moves
   behind an API?
7. **Accessibility and one-handed phone use** for the field roles.

---

## 7. Known gaps — please do not spend time rediscovering these

These are understood and deliberately not yet built.

- **The commitment guard.** Nothing stops a purchase order or subcontract being cut past a line's
  budget at the moment it is committed — only afterwards, in reports. The intended design distinguishes
  three causes that pay from different pockets: scope added (change order), an overrun on the same scope
  (margin, and never billable to the client), and a delay caused by hidden conditions or the client
  (a claim, with evidence). The second and third look identical in the numbers.
- **Deposit at signing on a construction contract.** Works on design proposals only.
- **Spec / tear-sheet automation** carrying the verified sheet to the PO and the foreman's phone.
- **Cheapest-price comparison** across vendor accounts as *landed* cost — needs a trade-discount field
  on the vendor record, which does not exist.
- **Per-line client approval and e-signature** on selections.
- **The site delivery window on the PO** — the PO says when we need it, not when the site can receive it.
- **Subcontractor compliance** — insurance expiry is on the vendor record but nothing gates payment on
  it; no lien waiver tracking.
- Smaller: bulk select on the selections grid, partial invoicing by category, save-as-template and merge
  for proposals, shipping sidemarks, per-item billing/shipping addresses.

**Data quality observations from the seeded set that are true of the real business**, not bugs:

- The construction schedule is not consistently maintained — several trades show nothing started while
  money has landed on them. The billing engine treats that as *absent evidence* rather than zero
  progress, but it is the single input whose improvement would most improve everything downstream.
- One design job has 404 agreed hours and nothing collected, with the retainer invoiced and unpaid.
- Another has one hour of funded time left at a burn of ~25 hours a week.

---

## 8. Engineering notes

- **One file, assembled.** Source is `app_head.html` (markup and CSS) plus `app.js`; a build step
  concatenates them. `app.js` is a base application with **23 feature modules spliced in**, each wrapped
  in sentinels (`/*<<name.js>>*/ … /*<</name.js>>*/`) so a module can be replaced in place, syntax-checked
  and rolled back on failure.
- **Modules extend rather than fork.** The pattern throughout is
  `const fooBase = foo; foo = function(){ … fooBase(); … }` — function declarations hoist and are
  reassignable, so a module can wrap a base behaviour without touching it. Read a module bottom-up: the
  mounting overrides are at the end.
- **Tests.** 67 suites: Playwright end-to-end runs against the built file plus offline Node suites. They
  are written as sentences about behaviour rather than about implementation (*"a written amount nothing
  printed supports is a conflict, not a correction"*), which makes them readable as a specification of
  intent. Running them is the fastest way to learn what the system believes about itself.
- **Every module carries a header comment** explaining the problem it solves, usually quoting the person
  who raised it, and the rule it enforces. Those are the design record; they are worth reading before
  the code beneath them.
