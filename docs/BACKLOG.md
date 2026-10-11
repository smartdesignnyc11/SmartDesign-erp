# Backlog to 9 in every lens

Every item comes from the round-4 expert reports (2026-10-04) or from round-5 work that was lost. Each is written as: what happens, what should happen, and the fix.

Severity scale:
- **S1:** wrong money or wrong client-facing truth.
- **S2:** a professional would hit it in a normal day.
- **S3:** polish.

Order of work:
1. §0 (the test net)
2. §1 (re-do round 5)
3. §2
4. §3
5. re-score

---

## §0 Rebuild the test net first (it was lost)
1. **`tests/lint.py`: the screen standard as code.** For every role × every view × desktop (1440x900) and phone (390x844), flag:
   - more than one visible `.btn.primary`, or a blue button used for housekeeping;
   - any emoji, or a glyph character standing in for an icon inside a button or link (› → ← ‹ ▾ ✓ ✎ ⋮);
   - a non-Title-Case label (button, tab, heading, th, tile label) or "Money";
   - a heading that does not match its nav entry;
   - phone sideways scroll, an element wider than the viewport, or tap targets under 8px apart;
   - an input covering its own label;
   - an SVG rendered larger than 64px unless it is a deliberate illustration;
   - page errors and console errors.
   - Output: `N flags`. **The target is 0.**
2. **`tests/counts_lint.py`: one number per label.** For owner, pm, coord, billing, controller, designer, foreman and client, it fails when:
   - (a) the same visible label shows two numbers for one role and one scope;
   - (b) a tile or tab badge differs from the number of rows its filter shows (click the tile, read the list's "N of M");
   - (c) a rail badge differs from its overview's count;
   - (d) **NEW:** Ask's headline count for "what is waiting on me", "what's late on <job>" or "how many tasks does <person> have" differs from the screen that lists them.
3. **`tests/ask_bank.py`: the Ask question bank.**
   - Ground truth is computed from `DB` inside the page, never typed by hand.
   - Include the founder's 25 + 15 questions (§1.3) and 100 role-by-role messy questions (typos, pronouns, relative dates, negations, comparisons, names not in master data).
   - **Keep 40 held out.** Never tune against them; report their score separately.
4. **`tests/daywalk.py`: a working day per role,** step by step through the real buttons, ending with no dead end:
   - owner brief and approvals;
   - PM CO and decision;
   - coordinator receive and bill;
   - billing invoice and payment;
   - controller reconcile and close;
   - foreman clock-in, materials, problem and daily log on phone;
   - client choose and approve;
   - designer day.
5. **`tests/finance_xcheck.py`.** Every surface that shows cash, AR, unmatched, AP, WIP over-billed, backlog, net YTD and safe to spend agrees: Statements, P&L, Pack, Flash, Ledger, Home, Ask, Chief of Staff. Values are pinned in `baseline_test.py`.

6. **`tests/leak_test.py`: money leaks are caught (north star, CLAUDE.md).** Each scenario is injected through the app's own import or record paths, never by hand-editing totals. Each must surface, with a link to the record and a proposed action, on the screen the responsible person works from, and in Ask:
   - **Unbilled reimbursable.** A card or bank purchase coded to a job, or bought for a client, that is on no invoice after N days.
   - **Work done, not billed.** A measured % or an approved CO that is above what has been billed.
   - **Overspend.** A cost line over its budget, PO or estimate line, flagged at the moment the bill or transaction lands, not at month end.
   - **Returns and refunds.** A card or bank credit from a vendor that is matched to the original purchase, relieves the job's cost or the PO, and is credited back to the client when the original was billed.
   - **No manual entries.** Every figure on the job and company reports traces to a bank or card line, a bill, an invoice or a payroll run.
   - **Nothing slips.** Promises made in email or meetings, overdue follow-ups, and tasks past due with no owner each produce a reminder for a named person.
   - Gaps found here become §1.5 items.
7. **The phone is really 390px wide.** The rebuild lost the `<meta name="viewport">` tag, so every phone run rendered at 980px and the sideways-scroll check passed vacuously. Restore the tag. Every phone suite asserts `innerWidth === 390`, and also flags clipped text (an element's scroll width greater than its client width while its overflow is hidden).

---

## §1 Re-do round 5 (lost before integration)

### 1.1 closetie: the WIP ties to the GL on close day (finance S1/S2)
This lane was finished and verified at 96 checks before it was lost. Re-implement it and hit the same figures.
- **Status (2026-10-10): re-implemented.** `tests/closetie_test.py` drives the finance lens's month-end and reads every target below (114 checks), plus the controller's round-5 findings 3, 4, 5, 6, 10, 14, 16, 17 and 18. The code sits in two `closetie` sections of `src/app.js` (`ct*`, `fin3JobAdjust`, `fin3PostDated`, `budGuard`, `bfIsDemoOnly`, `bfVoidNotAtBank`, `billChangeDate`, `ctHoldBasis`).
- **#1 Tie-out.**
  - What happens: with WW-2026-118 short-paid (PO $29,700 approved, $3,800 held in 1300), `jobFin` for a closed month reads the frozen figures, and the short-pay wrapper then subtracts the hold a second time (frozen actual $90,210 → $86,410).
  - Wages are accrued AFTER the WIP is planned (45 Cranberry labour −$123 moves its over-billing $325).
  - Result: the August Pack reads 121 State $67,326 / 45 Cranberry $6,323 while ledger 2500 holds $62,466 / $5,998.
  - Fix:
    - Apply every wrapper's adjustment only inside a raw read (`fin3Raw > 0`), so it lands before the freeze and never on top of frozen figures.
    - `fin2RunClose`: post wages, then plan the WIP.
    - Add a blocking tie-out (`WIP schedule = 2500/1200 per job`). On any difference the close refuses, reverses its entries and locks nothing.
    - For a closed month, show a WIP Tie-Out table.
  - Target: 121 State $62,466.02 and 45 Cranberry $6,323.09 equal 2500, and the Pack equals the ledger.
- **#2 Posting period.** A line posted on the first open day because its month was closed is stamped `postOn` / `postOnWhy`, and every management calculation honours it. This covers txns, bills, invoices, payments and payroll. Target: after reopen and re-close, August cost reads $103,305.11 in BOTH views and September carries the late $1,000 in both.
- **#3 PO relief.** A bank line matched to a PO with no bill relieves the PO's open amount in `jobFin.committed` and the by-code committed column. Target: accepting TINO $8,000 against PO-2026-047 moves 121 State committed from $46,010 to $38,010.
- **#5 Honest Demo Feed.**
  - The sandbox serves a fixed bank file with no duplicate dumpster charge, instead of echoing the register.
  - Lines confirmed only by the Demo Feed read "Demo Feed", not "backed", in coverage, reconcile ticks and the close.
  - Target: August coverage goes 54% → 51%, never 96%.
- **#6 Budget governance.**
  - Guards inside `budSetCell`, `budSpreadApply`, `budCopyApply`, `budRefreshJobs`, `budNewVersion`, `budLock` and `budMakeActive`: role (`budCanEdit`) and locked version. Make Active is the Owner's only. Each refusal toasts and writes an audit row.
  - CSV export, and CSV import with a column-mapping preview.
- **#7 Stale bridge.** After a close, the WIP line reads "WIP movement since the August 2026 close". The "await approval and are in neither" payroll sentence goes once a close has accrued the run.
- **#8** "Outside the P&L" counts only the bank leg of a transfer or card payment: $42,013, not $84,026.
- **#9 Orphan accrual.** Timesheet accruals with no run (the $3,699 for 8/4–8/13) are flagged once the next pay date passes, with Record the Run and Reverse… (Reverse needs a reason). The flag shows on the Close page, Bills & Payroll and the checklist.
- **#10** "Unallocated Labor" everywhere, and run burden in the Pack and the labor-cost KPI (not $5,790 standard vs $5,667 run).
- **#11** On the reconcile screen, a typed line the imported statement lacks gets "Not at the Bank — Void" (with a reason; the ledger reverses it), plus a close-checklist item listing such lines.
- **#12** Re-dating a posted bill needs a typed reason (a Change Date… dialog), with the date history kept.
- **Supporting functions for Ask:** `ctCloseStatus(ym)`, `ctCloseHistory()`, `ctAccrualAtClose(ym)`, `ctWipTie(ym)`, `ctOrphanAccruals()`. `pay3Disputes()` already exists.

### 1.2 truthpct: one completion number, an EAC that moves, portal truth (founder S1, ops S1/S2)
This lane was finished and verified at 53 checks. Target figures follow.
- **One job % complete:** `tpJobPct(p)`.
  - Physical (`prgJob`) where tasks are measured, weighting each SOV line by value: a line's own tasks at measured % (done 100, running and unmeasured at planned %, not started 0). A line with no task is cost-to-cost, deposits excluded.
  - 121 State reads **14%** in Ask "how far along", a Projects-table % Complete column, Reports › Portfolio, "which job is bleeding" and the backlog and margin answers.
  - Ask may never print a cost ratio as "% complete". Cost wording reads "X% through its estimated cost (cost-to-cost)".
  - WIP keeps cost-to-cost as the revenue basis, labelled "Cost Basis %", with a "Variance Flag: Measured on Site vs Cost Basis" table.
- **EAC = actual + committed + cost to complete,** rolled up from estimate and approved-CO lines. Each line counts at max(budget, actual + committed). A short-pay counts only its approved amount. A PM-reviewed CTC wins.
  - Targets: 121 State EAC $384,087.50 → $388,887.50 (Windows +$3,800, Millwork +$1,000); Margin at Completion 21.81% → 20.83%.
  - Millwork reads "…$38,000 of it a deposit, not progress — heading over by about $1,000", not "$35,768 over".
  - Knock-on figures: 121 State earned $124,158.26 → $122,625.79; WIP over-billing $129,525.25 → $131,057.72; backlog $367,041.74 → $368,574.21; YTD revenue −$1,532.47. August and closed months are unchanged.
  - Avoid recursion: `lineFin` → overhead burden → P&L → `jobFin`. Read the overhead-free line figure and add a re-entry guard.
- **Portal.** The client never sees internal earned revenue. The card reads "Completed to Date $253,684 · 51.65% certified on INV-2026-038 · 14% measured on site". Audit every client view and client email.
- **Measured pay application.**
  - Map tasks to SOV lines ("Windows & interior trim" → Windows). Measured % wins, and cost never lifts a measured line: Windows proposes 20%, not 100% from a $33,500 vs $29,700 overrun.
  - Cost-only lines carry a "No Field Measure" pill and a "confirm" finding.
  - Add a Materials Stored column (G703 column F).
  - Target: "Fill the Draft Anyway" on 121 State drops from $29,449 to $11,386.
- **Forecast cause.** The Today forecast tile and the Schedule forecast card explain the gap from the cause.js history causes. After R2 gives back 4 days un-pulled, they read "4 working days late · 4 days still on Framing & blocking – 3rd floor from CO-…-R1 — Pull In", and clicking opens Pull In. Name a driver task only when it is critical or its lag exceeds its float.
- **Milestones and revisions.**
  - Client milestone pills read Done / Upcoming / "N Working Days Past Agreement", never "Ahead".
  - Revisions net into one client row per CO: "Your change order CO-2026-004 (as revised, R2) +3".
  - Superseded CO copies are marked in chips and in the task editor's Linked list.
- **Studio phase status.** Phases read their status from the task. Marking DD done makes CDs current, with DD shown "Done" on the board and the phase strip.

### 1.3 askgen: Ask generalises (founder S1). Unfinished; build it in full
- **The problem.** `paAsk` is wrapped by 10+ keyword-intent layers. Scripted questions pass, but 8 of 15 new questions failed, and the "I read this as" line fired on only 2 of the 8. Intents refuse ("206 Lenox is a job, so I hold no people against them") before `erpQuery`, which could answer, is ever reached.
- **Build a schema-aware parser in front of all refusals:**
  - **Entity:** from EQ_TABLES names, aliases, plurals and synonyms.
  - **Filters:**
    - names matched against master records AND free-text fields;
    - an unknown name ("Home Depot") falls through to a text search of transactions, bills and POs;
    - dates and relative periods ("in August", "yesterday", "this week" = Monday to today via `appWeek`);
    - statuses ("approved but not billed", "not submitted", "late", "holding up");
    - negation ("who has NOT submitted hours");
    - job-scoped people, crew, materials, logs and photos.
  - **Measure:** count, sum, max and min. "Which vendor do we owe the most" ranks by amount owed under `apOpenBills`, not billed.
  - **Grouping:** "by vendor", "per job".
  - Always show "I ran: <entity> where … grouped by … (N rows)".
  - Remove the "is a job, so I hold no …" refusal class.
  - No carry-over of a previous question's job into a self-contained question.
- **Decision (2026-10-08): "what's late" means late only.**
  - A job's Late = `PRED.jobLate`, the union of `lateMaterial`, `lateDecision` and `lateSubmittal`. On 121 State that is 3 + 3 + 2 = 8.
  - Ask states it, then "Also needs you: 1 inspection to book, 3 site questions (12 in Needs You)", with each number matching its own label.
  - Today shows a Late figure next to Needs You.
  - The Ask bank's truth for this question reads `PRED.jobLate`.
- **The founder's 15 new questions** (all must pass):
  - gross margin YTD (from `companyPL`);
  - which vendor do we owe the most;
  - when will 206 Lenox finish (the same finish as the Projects table, 12/15);
  - what did the crew do yesterday at 121 State Street (daily log + time);
  - who has not submitted their hours this week;
  - how much did we spend at Home Depot in August;
  - which submittals are holding up an order (the 2 late ones);
  - which change orders are approved but not billed;
  - plus the 7 he got right.
- **Finance and ops questions:**
  - "how much is in dispute with vendors" → $3,800, WW-2026-118, held in 1300 (today it says $85,550);
  - "is August closed", "what was accrued at the August close", budget lock state;
  - "what moved the finish and whose days are they" (cause history);
  - "photos shared with the Kleins" (only their jobs);
  - "what did Angel log today" (Angel's log and time, not the PM's day).
- **"What is waiting on me"** reads the same `needs()` and Approvals list the screen shows. Today Ask says owner 46 / pm 45 / billing 44, while the screens say 26 / 26 / 9, and the controller is told "Approvals are not part of what your account sees" while Home shows 13.
- **The online path (hosted).** The model's `query` tool must list every entity and field (budget, bank feeds, submittals, daily logs, photos, progress), and the system prompt tells it to show the query it ran.
- **Honest evaluation.** Tune on 50, report 50 held out, then write 25 fresh held-out questions and report that too.

### 1.4 clientpo: Release Order, client approvals, phone (UX S1/S2, ops S2). Unfinished
1. **Release Order makes a real PO (S1).** **Done (lane purchasing, 2026-10-10):** `poValid` on every issue path, `smReleaseDialog`, `poRepairInvalid`; proven by `tests/purchasing_test.py` (release).
   - What happens: submittal 26 51 00-001 › Release Order drafts PO-2026-049 with the vendor "— choose vendor —", $0 total, no Needed on Site and no task. Issue PO succeeds anyway and marks material m17 "ordered" at $0, so the Buy Board stops chasing the lighting.
   - Fix:
     - Carry the item, quantities, prices, on-site date, task, spec section and job, and ask for the supplier (picker of vendors who sold this item or trade).
     - Every Issue PO path (Release Order, the PO record, Buy Board runs, `selPORun`, the ct picker) refuses with no vendor, a $0 line or no lines, through the house validator.
     - Never mark a material ordered on an invalid PO, and repair the ones already marked (boot migration).
2. **CO from a field issue at Procore change-event level.**
   - What happens: Field › "joist notched" › Write Change Order lands in Clients, Extends Task is "No task", none of the 2 photos are attached, and the memo prints the PM's note to the foreman.
   - Fix:
     - Open it in the project, with Extends Task = the item's task.
     - Attach the photos as exhibits, shared with the client.
     - Draft the client memo from the item's description; the PM's reply goes to Internal Notes.
   - Done (lane ops, 2026-10-10): the memo is the item's title and note, the answer is in Internal Notes (never on the approval dialog, the email or the PDF), the item's photos attach as exhibits shared with the client and show in the editor, the dialog and the email; `tests/ops_test.py fieldco`.
3. **The estimate hint stays out of the description.**
   - What happens: the hint "…Contract line on EST-2026-014: $34,500 — for reference; enter this change's quantity or price" is saved into the CO line `desc` and prints on the client's CO and PDF.
   - Fix: keep it in `refAmount`, shown as a hint only, and clean already-saved descriptions.
4. **The client sees what they approve.** Done (clientfix, tests/client_test.py): "View the Sheets" opens the read-only client viewer (`clFileView`), the approval sheet stays open underneath, and every file write refuses the client role in the function.
   - Each client submittal approval gets "View the Sheets", which opens the file, plus a confirmation step like CO signing.
   - It counts in Waiting on You, the nav badge and the Decisions tile.
   - Fold the client's four lists (Your Decisions / To Sign / Waiting on You / Approve Before We Order) into ONE Waiting on You list, with one count.
5. **The client Overview shows progress.** Done; and a design job before its schedule is published reads a design-phase Overview (`clDesignOverviewHtml`), never a construction card; one billed figure ("Billed to date $238,015 after retainage ($253,684 before)").
   - Show Progress (the certified figure from §1.2) plus the last 3 shared photos.
   - Retire the stale "last update from Alan on Tue, Jul 28" line.
   - The PM writes a client caption when sharing; internal tags (DAILY LOG) are never shown.
6. **Portal approvals are not inbox work.** Done (clientfix): a choice, a signature, a sample approval and a question each land in Project Messages as one handled activity line (`clActivity`); a client's question is the PM's Do Now item "Answer <client>" with a drafted reply from the published schedule and the statement (`clqRaise` / `clqAnswer`), and the client reads "Sent to Alan" and the answer. The client has an Ask door (header, the Chat switch, a scoped `pa` surface) and the intents a client uses (`CL_ASK`).
7. **Phone document overflow (regression).** On the CO draft, the meta block (621px in 268px) pushes Title / Project / Date to x=645. Collapse the meta block to one column under 480px, and sweep every document type on phone for elements wider than the viewport.
8. **Icons.**
   - `.bp-ic` has no size: the PO "Documents:" note renders a ~1,000px PDF glyph, and the Documents grid crops 209px glyphs.
   - Default SVG size 16px; proper 48px file tiles.
9. **A dirty document keeps its primary.** Pricing a CO line hides "Send to Client" behind "Unsaved changes · Save". Send saves first, a quantity commits on blur, and the primary never disappears. Apply this to every document type.

### 1.5 leaks: money leaks and slipped work are caught automatically (north star; from tests/leak_test.py, 2026-10-08)
Baseline: 2 MISSED, 4 PARTIAL. Every item is proven by its leak_test scenario turning CAUGHT.
**Lane leaks (2026-10-10):** #1 (reimbursables, floated client purchases, Billable Expenses pull, spUnbilled one number), #2 (hold per line, CO lines from 0, Send on a draft) and the client credit of #4 delivered; leak_test 1 and 2 CAUGHT; tests/leaks2_test.py proves eight of the month's cracks (docs/ARCHITECTURE.md, leaks2). #3, the deposit-applied line of #2, #5's byCode source ids, document attachments and labor from the run, and #6 remain.
1. **Unbilled reimbursables (MISSED, S1).**
   - What happens: card purchases coded to a job land in job cost, but no field records whether they were billed back.
   - Fix (NetSuite Billable Expenses; QuickBooks Unbilled Charges):
     - Add `billable`, `markupPct` and `invoiceLineId` to transactions and bill lines. The default comes from the job's contract type (cost-plus / T&M) or a rule.
     - Add a "Billable Expenses" pull in the invoice editor.
     - `readyToBill()` gets a `reimbursable` row kind once a line is older than `company.rebillDays` (14). It feeds the Billing Queue, Home, `needs('billing')` and Ask.
2. **Work done, not billed, hidden by a job-level hold (PARTIAL, S1).**
   - What happens: `readyToBill` holds all of 121 State because of `wipRow(p).over > 0`. Approved CO lines and measured lines that are ahead of billing disappear with it.
   - Fix (AIA G703 per line): never hold CO SOV lines. Hold per line, not per job, and net the deposit as a "Deposit Applied" line. Held rows show their reason and a Bill button.
3. **Overspend when the cost lands (PARTIAL, S2).**
   - What happens: PO overrun is flagged, but budget and estimate-line overrun is caught only by the Analyst report, at more than 10% over.
   - Fix (Procore budget alerts; NetSuite budget check):
     - One `jcCheck(project, code, line, amt)` called from `billFlags`, `txnState` and `bfIngest`/`applyRules`.
     - The PM gets a reminder with Raise CO / Move Budget / Dispute.
     - An Ask intent reads the same function.
4. **Returns and refunds (MISSED, S1).**
   - What happens:
     - A positive job-coded refund never lowers job cost, because `jobFin` only counts `t.amt < 0`.
     - Rules auto-code a refund as materials with no project.
     - Nothing links the credit to the original charge, bill or PO, and no client credit is proposed.
   - Fix:
     - Credits reduce job cost.
     - `bfIngest` scores each credit against the same vendor's last 90 days and proposes `creditOf`, which inherits the original's project, code and line.
     - When the original was billed, propose a client credit row in `readyToBill`.
     - Rules never code a positive amount as materials.
5. **Every figure traces to a source (PARTIAL, S2).**
   - What happens:
     - `jobFin().byCode` returns bare numbers.
     - Labor is costed from time × rate with no payroll run.
     - Hand-typed costs carry no mark.
   - Fix:
     - `byCode` rows carry `src` ids, with a drill-down from every figure.
     - Time entries are stamped with `payrollId`, and labor is costed from the run.
     - A "No Source" badge with Match to Bank / Attach Bill.
     - Back the seed with statement lines and bill files.
6. **Nothing slips (PARTIAL, S2).**
   - What happens:
     - An unowned overdue task sits only in Tasks › Overdue › Everyone.
     - An outbound "I'll send … Friday" becomes only a note.
   - Fix:
     - `clTaskSweep` proposes the project PM as owner, with Assign on Home.
     - A promise rule in `cmRead` turns "I'll / we'll send … <day>" into a task for the sender, due on that day.
     - Outbound mail is routed by recipient.
     - The person's due-soon items go to Home and Ask "My Day".
7. **Bug.** The New Bill drawer's Vendor gate (`vfHold`) stays on the shared `#d-save` button, so the transaction drawer cannot save until Vendor is filled. Clear it when the drawer opens.

### 1.6 truth: the ERP's financials are the single source of truth (Alan, 2026-10-10; CLAUDE.md "Financial truth")
Proven by `tests/truth_test.py`. Every item is a class, applied to every money record type (invoice, payment, bill, bill payment, PO, bank and card line, payroll run, journal).
**Delivered 2026-10-10 (lane truth):** `tests/truth_test.py` runs 112 checks across six sections (cov, manual, tamper, match, qbo, guard) by driving the real flows; docs/ARCHITECTURE.md lists the functions (`truth*`, `qboLoad`). The hash chain is FNV-1a 32 over the month's postings in posting order; a close seals it into `DB.periods.chains[ym]`. The match model is `txn.match = {billId, billLineId, poId, poLineId, estimateLineId, invoiceId, invoiceLineId, payrollId}` (`truthMatchOf`). `*.qbo.json` is git-ignored; the harness refuses a snapshot path inside the repo.
1. **Bank and card are the source.** Every P&L and job-cost figure carries its coverage: backed by a bank or card line, backed by an approved document only (accrual), or by hand. Coverage shows on the Statements, the Pack, the job report and Ask ("how much of August's cost is backed by the bank"). The Demo Feed never counts as bank evidence (§1.1 #5).
2. **Journal entries always flagged.** A manual journal (and any posting that did not derive from a document) carries a visible flag on every surface it touches: ledger rows, statement lines (count and amount of manual entries per line, drill-down), the Pack, the close checklist and Ask. Drafted by the Controller, posted by the Owner with a typed reason; never silent.
3. **Tamper-evident.** Posted money records and ledger postings are append-only: an edit is a reversal plus a re-post, linked, with who, when and why (already the rule for open periods; make it universal and visible). A hash chain over postings per period, verified at close and on demand ("Verify the Books" on Ledger), so a changed or deleted posting is detected and named. Deleting a posted record is refused; voiding is a reversal with a reason.
4. **Every transaction matched to a line.** A bank or card line resolves to a bill line or PO line and through it to an estimate line (cost side), or to an invoice line (income side); a payroll run to its time entries; a client payment to invoice lines. Unmatched is a named state with a count on Banking, Home (Caught for You), the close checklist and Ask, never a silent cost. A close refuses while unmatched lines exist in the month, or lists them with a signed exception.
5. **QuickBooks is a bridge, not the truth.** Load a QuickBooks snapshot (customers, estimates and invoices with lines, open AR and AP, P&L, balance sheet, payroll) through the app's own import paths into clients, documents and periods, marked `source: quickbooks`; then show a Three-Way Tie-Out: QuickBooks says / the bank says / the ERP says, per month and per account, with every difference listed and explained or flagged. The snapshot file lives outside the repo (`tests/harness.py: load_qbo_snapshot(pg, path)`, refusing paths inside the repo) and is never committed, seeded or published.

### 1.7 assistant gaps: what did not fire on a synced workspace (from tests/demo_ws_test.py, 2026-10-10)
Each is proven by a demo_ws_test check turning from "did not fire" to "fired as a proposal". AI proposes, people approve, throughout.
1. **Field and design assistants know no jobs (S2).** `paMine().projects` is empty unless the person is the project's PM, so `paTerms` carries no project or client terms: the foreman got 1 nudge from 14 messages (the DOB inspection window and the plumber's no-show never reached him); the designer 4 of 15. A person's jobs are the jobs they are assigned to, clocked on, or named on (schedule, submittals, decisions), not only the ones they manage.
2. **Meeting tasks apply without approval (S2).** The seed ships `company.meetAuto.task = true`, so tasks from meeting notes are created on sync. Default to proposals; a firm may switch auto-apply on per kind, and the Brain says so. **Done (lane learn):** `meetAuto.task` defaults to false; The Brain's Today says what applies without asking.
3. **Engineer's calcs are only a note.** The PE's flitch-beam calcs should file on the job, update the S-101 submittal, and propose "stamp the shop drawings before fabrication".
4. **Vendor delivery dates in mail stay notes.** Propose setting or confirming the PO's expected date, the foreman's Arriving Today, and an elevator or street reservation task.
5. **Field requests in mail stay notes.** "25 boards GWB by Thursday" becomes a material request on the Buy Board with its order-by date.
6. **Meeting notes and transcripts in Drive are only nudged** ("belongs on the job"); ingest them like mail (`mtIngest` from Drive text).
7. **A client's dated ask inside a decision email** ("confirm the laundry layout before Friday") becomes a dated task for the PM, not only an offer.
8. **The quiet-lead chase** fires only when the sent message asked a question; any proposal or quote sent with no reply is watched.
9. **A DOB NOW notice** sets the inspection date on the project's inspection record (as a proposal), not only a permit note. Done (lane ops, 2026-10-10): `cmDobNow` proposes the booking with its window on the matching open inspection; approving it books through `inspBook` (calendar hold, foreman told, trade drafted, the Book task closed); `tests/ops_test.py insp`.
10. **Lessons are not proposed from events.** The no-show and the expired COI never became lessons; `bnSuggestLessons` runs only when The Brain renders. Run it on every sync and on every closed field issue, bill dispute and late delivery. **Done (lane learn):** `LEARN_EVENTS` + `lnLoop` (APP_DAY_HOOKS, sync, field, dispute, delivery, close); lessons are proposed with evidence, approved by the Owner, and fire once per record; proven in `tests/learn_test.py`.
11. **A call from the answering service** matches the client by phone and proposes the reply draft, not only a task.
12. **A bank or card statement in Drive** proposes the import (and the reconcile), not only a nudge.
13. **Unrouted mail becomes master data** (from the real-workspace test): a thread matching no client, project or vendor proposes creating it, with the evidence; the owner approves in one tap and the thread routes. **Done (lane realws, 2026-10-10):** `paMasterClusters` clusters unrouted threads by correspondent domain, person and project-like address; one nudge and Ask ("who is not on file") carry one-tap offers; `paMasterApply` creates the vendor, lead, client or job and routes the cluster. Proven on an invented loaded workspace in `demo_ws_test.py` ("loaded"). Still open from the same run: a Loaded Workspace dated after the app day reads as the future to the chase and due-date logic (two clocks, documented in ARCHITECTURE.md), and the first sync of a seven-month mailbox still proposes per-message notes by the hundred.
14. **Proposals from mail you can approve** (owner review r5 findings 1, 2, 3, 7, 8, 11, 14, 15; PM review r5 findings 9, 10). **Done (lane brain, 2026-10-10):** money direction from who pays whom, unclassified money mail, bank notices as bank-line matches only; "attachment not read" on every proposal and in the first-sync summary; Not Ours in bulk, merged addresses and people, names from signatures, blank jobs from mail; routing by address and by the job's short name, property mail to the entity; image tokens and "Alan" in the owner's notes; personal statements left out of Bank › Import; Needs an Answer by threads; one permit proposal per thread; requests as tasks on the reader; LPC resubmissions as dated designer tasks; one Drive card; no nudge for my own mail. Each class is reproduced by invented threads in `demo_ws_test.py`. Still open: attachments are not read at all (the server-side PDF reader is lost); the brain now says so instead of guessing.

---

### 1.8 rfq: AI-run requests for quote, from the plans to the negotiated price (Alan, 2026-10-11)
Alan: "create an RFQ and choose the vendors to send it to and the AI takes it from there … constantly be looking for new vendors … the AI helps in every step." The flow, each step with its owner and the AI's part:
1. **Draft from the plans (AI).** A rough-materials RFQ (framing first: studs, plates, headers, joists, rim, blocking, sheathing, fasteners, hangers) drafted from the job's drawings and room-by-room takeoff. Every line shows how it was derived (wall length, height, spacing, waste factor) and what was assumed, kept apart from what was read (the Standard: label facts, assumptions and recommendations). Need-by dates come from the schedule and lead times.
2. **Foreman review (foreman).** The draft lands in the foreman's queue, on the phone: adjust quantities, add or remove lines, approve. One tap per line, big targets.
3. **Purchasing (procurement manager).** Picks the vendors. The AI proposes the list: vendors in the category, past price and on-time record, at least one out-of-NYC vendor for shippable materials, direct versus middleman per the Standard, and new prospects. The manager sets the due date and presses Send. That press is the approval to send.
4. **Out to vendors (AI).** One email per vendor with the RFQ number in the subject and a line-item sheet. Non-responders are chased before the due date (drafts the manager approves, or sent automatically only if the manager has delegated RFQ chases).
5. **Quotes back (AI).** Replies are matched to the RFQ by number and sender, read (email body, PDF or spreadsheet) and entered as quote lines: price, unit, freight, lead time, validity, substitutions and missing items flagged. A reply that could not be read says so.
6. **Leveling (AI).** Who is cheapest for the whole basket; who is cheapest per item; the best split award once freight and minimums are counted; landed cost, lead time against the need-by date, region. A recommendation in the Standard's format.
7. **Negotiation (AI drafts, manager approves).** An email per vendor asking for reductions on the items where they are not best, citing only real competing figures and never naming the competitor (the Standard: integrity; never mislead a vendor). The manager edits and approves; round-two quotes are read the same way.
8. **Award (manager).** Award by vendor or by line; POs are created from the award with the sourcing choice recorded; savings recorded as final price against first quote and against budget, rolled into the monthly savings report.
9. **Vendor discovery (AI, always on).** A prospects list fed by unknown suppliers in the mail, categories with fewer than three vendors or no out-of-NYC vendor, and sourcing research. Each prospect is a proposal the manager adds or dismisses; added ones are suggested for the next RFQ.
10. **Sourcing research: the AI reasons about where it is cheaper, then goes and finds it (Alan, 2026-10-11).** For a category (lumber first), the AI:
    - **Reasons about supply geography and cost structure.** Where is it made, and why would it be cheaper there? Examples: near the raw material (mills by the timberlands), large plants with the lowest unit cost, small outfits with low overhead, fewer hands between mill and site, regions with lower labor, rent and insurance than NYC. Each reason is labeled a hypothesis until data backs it.
    - **Searches online** for the companies that fit (mills, wholesalers, regional yards), and builds a profile for each: location, size, what they make, grades and certifications, delivery range, minimums, and every source link.
    - **Estimates landed cost to the job:** price signals found, freight to Brooklyn or Manhattan by truckload or LTL, lead time, minimum order, returns. It compares this with what we pay now from POs and quotes, with the arithmetic shown.
    - **Checks the quality is the same or better:** grade stamp and grading agency, species and grade equivalence, kiln-dried, certifications, references and reviews, insurance and licence. A different species or grade is a substitution and needs PM and designer approval (Standard: Procurement).
    - **Proposes, never commits.** The procurement manager gets a short case per prospect: why it may be cheaper (facts with sources, kept apart from hypotheses), the estimated saving, the quality check, and the next step (add to the next RFQ, ask for a price list, or order a sample first). Nothing is presented as fact without a source.
    - **Runs continuously.** Categories are re-researched on a cadence and when prices rise. What the AI learns (which regions and outfits actually came in cheaper) feeds the brain, so the next search starts smarter.

11. **Price watch: paid more than before, or something looks off (Alan, 2026-10-11).** The AI reviews every purchase (PO lines, bill lines, card and bank lines matched to items) against what the firm has paid before:
    - **Item price history.** Unit price per item, normalised by unit and pack size, by vendor and date, built from POs, bills, receipts and quotes. Uncertain item matches are proposed for a person to confirm, not assumed.
    - **Paid more than before.** Unit price above the recent typical price for that item (default: more than 10% over the trailing median, editable), or above a cheaper recent price from another vendor, or above the quote or PO price it was bought against.
    - **Abnormal.** Quantity far beyond the estimate line or takeoff; a duplicate or near-duplicate charge; purchases split to stay under the $2,500 three-quote threshold or an approval limit; a fee or freight spike; a vendor the firm rarely uses for that category; an item not delivered to a job; a card purchase with no job, PO or receipt.
    - **Each flag is a case, not an accusation (the Standard: one team, integrity):** the history behind it with sources, the money at stake, likely innocent explanations labeled as such (market move, small quantity, rush delivery), and a recommended next step (ask the vendor for a credit as a draft the manager approves, update the price book, add the item to the next RFQ, or mark it explained).
    - **Checked at three moments:** when a PO is drafted (a warning with the history, before money is committed), when a bill arrives (bill against PO against history), and when a bank or card line is matched.
    - **The owner approves explanations (Alan, 2026-10-11).** Anyone can propose "explained" with a reason, but the note goes to the owner. The flag stays open, and nothing changes, until the owner approves it. A baseline change (for example, "lumber up 8% this quarter") takes effect only on the owner's approval, with who proposed it, who approved it and when kept on the record.
    - **It learns.** Once the owner approves an explanation, the baseline adjusts and the brain records it, so the same normal change is not flagged twice. A monthly figure shows the dollars paid above the best recent price.

12. **Inventory before buying (Alan, 2026-10-11).** Before anything is bought, the ERP checks the firm's own stock (`DB.inventory`, `invAvailable`), at every door: a foreman's material request, a PO draft, an RFQ line, and after the fact on a card purchase.
    - **Example.** The foreman requests 24 sheets of 5/8" drywall and 12 are in stock. The request splits: 12 are reserved from stock for the driver to pick, and only 12 go to purchasing. The driver and the procurement manager are both told.
    - **Only the driver or the procurement manager can override,** to buy the full quantity instead of using stock, and only with a reason. The reasons: count was wrong (the driver marks it short, and the stock count is corrected and logged), damaged, wrong spec (for example, Type X against moisture-resistant), reserved for another job, or not worth the trip. Every override records who, when and why.
    - **Spec matters.** Stock is matched on item and spec, not on a loose name. An uncertain match is a question to the procurement manager, not an assumption.
    - **After the fact.** A purchase made while matching stock sat available, with no override, is flagged in price watch as abnormal.
    - Today's "Inventory first" note on requests is advisory only. This makes it the default path, with a guarded override.
    - Done (2026-10-11, lane stock; `tests/stock_test.py`): the section "Inventory before buying" next to the inventory code in `src/app.js`. `stockCheck({item, spec, unit, qty, jobId})` matches on item and spec (thickness, type, size, unit, pack); an uncertain or near match is a coordinator question on Needs Your Hand. `addRequest` splits a request (stock part reserved for the driver's pick, rest to buy); `stockOverride` (driver or coordinator, reason from `STOCK_REASONS`, append-only in `DB.stock.overrides`; Count Was Wrong logs an adjustment and asks for a recount). `poValid` refuses a line that buys free stock (`stockGuardOk(lines, ctx)`), the PO page and the Order sheet warn inline; the RFQ lane calls `stockRfqGuard(rfq)` and `stockLineNote(line, ctx)`. CATCH/PRED `boughtWhileInStock` (abnormal; price watch absorbs it). Also from the coordinator's review: stock issued to a job records its carried cost on the job's estimate line (`DB.stock.use`), Return to Stock credits it (a cost-plus job's leftovers go to the PM as client-owned surplus), picks lapse after `DB.stock.holdDays` (5), the driver's Count This, the owner's Override Patterns. erpQuery: `stockoverrides`, `stockadjustments`, `stocksplits`, `stockuse`.
    - Open: stock use is recorded per job and line but not yet posted to the ledger or `jobFin` (a system journal, job materials against the inventory asset, belongs with the finance lane and finance_xcheck); no trip cost model exists, so Not Worth the Trip shows distance only.

Phase one runs in the demo and on the Demo Workspace (invented vendors and replies). Real sending, inbox watching, PDF and drawing reading, and web search for sourcing research arrive with the platform (§5: AI proxy with the web-search tool, watchers, document reader).
- **Done, phase one (lane rfq, 2026-10-11): items 1 to 10.** The rfq section in `src/app.js` (after purchasing) and `tests/rfq_test.py` (120 checks, walked as the foreman at 390px and the coordinator). Line-first New RFQ ("Which Lines?", multi-select on the phone; From Plans and Start Blank secondary); each RFQ line carries `line`/`estimateLineId`/`coLineId` and its budget through to the PO line. From review notes: NY sales/use tax and a hand-unload allowance in landed cost; AI-read figures unconfirmed until the coordinator confirms them; a new vendor is vetted (W-9, COI, business check) before its first PO; relationship and delivery facts shown beside price. Waiting on the platform: real sending and inbox watching, the CSV as a real Gmail attachment (the draft path is text-only, so the CSV is inline), PDF and drawing reading, web search for sourcing research (the provider is a stub), `charterWhy` wiring. Not built: item 11 (price watch), the bill-arrival use-tax flag, and precision tracking (both belong to price watch).

### 1.9 track: every order document filed, every vendor promise tracked, follow-ups sent on their own (Alan, 2026-10-11, "very important")
Alan: tracking numbers, invoices, receipts, delivery dates and vendor promises all land in their right place automatically, for easy access and automated tracking; the assistant and the brain learn from them, keep things on track, and follow up with vendors, autonomously.
1. **Capture from everywhere.** Sources: mail (each person's connected Gmail, and a shared purchasing address), attachments, the driver's and foreman's phone photos (packing slips, paper receipts, delivery tickets), card and bank lines, and a quick "log a promise" for calls and texts (the Standard: verbal becomes written within 24 hours). Today the brain only notices a delivery mention and proposes it (`cm` "delivery" kind, around line 71091).
2. **File it where it belongs, linked.** Each document is read, classified and attached to its record with the source kept:
   - order acknowledgment → PO (compared line by line with the PO: quantity, price, date, spec; differences flagged);
   - tracking number → PO and shipment (carrier detected: UPS, FedEx, USPS, freight PRO);
   - vendor invoice → bill, linked to the PO;
   - receipt → card or bank line, job and PO line;
   - packing slip or delivery ticket → receiving record (partial deliveries and backorders);
   - delivery date or promise → the promise ledger on the PO line.
   Anything uncertain is proposed for a person to confirm, never filed silently in the wrong job. Everything is searchable (⌘K) and queryable.
3. **The promise ledger.** Every vendor promise (ship date, delivery date, price, "will call back Tuesday") is a record with who promised, when, the source message, and its due date. When it comes due, it is checked against tracking or receiving. Kept promises and broken ones build each vendor's on-time record.
4. **Tracking runs on its own.** Shipment status and ETA (carrier tracking on the platform) are compared with the need-by date from the schedule. A slip that threatens the schedule goes to the procurement manager and the PM the same day, per the escalation table ("long-lead item late or at risk"), with the impact on the three-week look-ahead and a recommendation.
5. **Vendor follow-ups, sent autonomously within the Standard.** The Standard lets the AI send to a vendor only for a message type a person has delegated. So the procurement manager delegates "order follow-ups" once (on by default for new installs, owner can switch it off), and from then on the AI sends them on its own, on a cadence:
   - confirm the order and date after the PO;
   - ask for tracking before the ship date;
   - check two days before delivery (the Standard: reconfirm 48 hours ahead);
   - chase a missing invoice, receipt or packing slip;
   - chase a broken promise.
   These follow-ups can only ask, confirm and request documents. They never accept a new date that moves the schedule, change an order, discuss money or payment, or dispute anything; those come to a person as a proposal. Every message sent is logged on the PO with its reply.
6. **Learning.** Per vendor and category: real lead time versus quoted, on-time rate, how often an acknowledgment differs from the PO, and documents missing. These pad future need-by dates ("assume nothing arrives on time unless someone confirmed it"), rank vendors in RFQs, and become lessons the brain proposes.
7. **Guards.**
   - Payment or bank-detail instructions found in a vendor email are never acted on (§5.4, two people and a call-back).
   - Marketing mail and personal mail are ignored. Only purchasing traffic is filed.
   - Duplicates are detected.
   - A document that could not be read says so.
   - Missing documents are a count that opens its rows: delivered with no packing slip, billed with no invoice copy, card line with no receipt.
8. **Documents attach to the PO, the bill, or both, and the AI checks they line up (Alan, 2026-10-11).**
    - **Getting documents in.** Any document can be added directly on a PO or a bill: camera on the phone, iPhone share sheet, drag and drop, or forwarded to a purchasing address. One invoice usually attaches to both its bill and its PO. A receipt attaches to its card line and, where there is one, its PO. A multi-invoice PDF is split, a blurry photo gets a request to retake, and phone captures queue offline.
    - **The original is evidence.** It is stored unchanged and hash-stamped (the financial-truth rule: a figure with no document or bank line behind it is shown as such). Corrections never overwrite it.
    - **The AI reads it and checks every match** against the PO, the receiving record, the bill, the bank or card line and the estimate line:
      - vendor, job and address, and the PO number referenced;
      - each line's quantity, unit price and extension;
      - subtotal, tax at the right rate (or use tax due), freight and total;
      - items not on the PO, or billed before they were delivered;
      - price above the quote or PO (price watch);
      - duplicate invoice numbers or amounts;
      - payment terms against the vendor's terms;
      - a changed remit-to address or bank details (never acted on: two people and a call-back);
      - on card receipts: items with no job purpose, tips, or a store far from any job.
    - **The result is plain.** "Lines up" shows as a quiet tick with what was checked. Anything off becomes a case: the field, the two values, the money at stake, and a next step (ask the vendor for a corrected invoice or credit as a draft, hold the bill, or have a person accept the difference with a reason). A bill with an open mismatch cannot be approved for payment until it is resolved or accepted. Small rounding has a tolerance the owner sets.
    - **Confidence shows.** Every figure the AI read shows its confidence. A low-confidence read is confirmed by a person before it counts.

Phase one runs in the demo and on the Demo Workspace with invented vendor mail, photos and tracking. Live mail watching, carrier tracking, document reading and autonomous sending arrive with the platform (§5.5–5.6).

## §2 Remaining round-4 findings

### Founder
- **206 Lenox is a clone (S2).**
  - What happens: "3rd floor turnover", $0 contract, carries 121 State's 39 schedule lines and its decisions verbatim. Owner Approvals shows 3 duplicate decisions, Ask's "11 decisions waiting on the client" includes 5 clones, and Chen's tasks and Purchasing's 28 rows include clone items. Purchasing also lists 140 Prospect's "LPC application" as a thing to buy.
  - Fix: reseed 206 with its own small scope, and strip non-materials from Purchasing.
  - Done (lane ops, 2026-10-10): the template copies phases and inspections only; 206 Lenox has its own turnover scope (six tasks, one decision, two materials, `lenoxScope`); `tplStripClones` strips clone copies from a saved database at boot; `tests/ops_test.py lenox`. Purchasing's non-materials remain open.
- **The owner's Approvals is a catch-all (S2).**
  - What happens: 26 items, but the chips cover only 13 (Bills 2, Hours 4, Decisions 7). The rest are crew hours, a material acknowledgement, meeting proposals, "a build" and lessons.
  - Fix:
    - Chips sum to Everything.
    - Delegation rules: hours to the PM or foreman, material acknowledgements to Chen, bills under a threshold to the PM.
    - One waiting count shared by Home, the rail and Ask.
  - Done (2026-10-10, lane polish): `DELEGATION` in `src/app.js` (next to `APPR_CHIPS`) names the one role each kind waits on, with the owner-only overrides as `who(it)`; the last `mApprovals` layer applies it, so every queue, badge, tile and Ask count follows. Owner 26 → 10 (WW-2026-118, the brain's change, 8 lessons), PM 26 → 16, Chen 20 → 3, billing 9 → 0, controller 13 → 0; the owner's Approvals still lists what waits on the others under "N more wait on the others".
- **Purchasing overview is a third "to buy" list (S2).**
  - What happens: the overview has 28 rows, Buy Board › Contract Lines 33, Finish Selections 5 (the submittal-gated items are missing from the overview), and clicking a row opens the top of the Buy Board.
  - Fix: the overview IS the Buy Board's rows, with row actions (New PO, Set Up to Order) and the submittal gate shown.
- **Saved searches use their own predicates (S2).**
  - What happens: the Report Builder's "Bills awaiting approval" shows 1 while Approvals shows 2; "Open POs by vendor" shows 4 while Ask says 2.
  - Fix: seeded searches reuse the app's predicates.
- **New records can't be found (S2).**
  - ⌘K finds nothing for "09 30 00-001", "hidden condition", "daily log", "Reforecast" or "home depot".
  - The Report Builder lacks Tasks, Decisions, Submittals, Opportunities, Materials and Inspections.
  - Fix: index every erpQuery entity in both.
- **Late materials, three counts (S2).** On 121 State: Purchasing shows 4, Projects › Materials "Late to Order 3", Ask "7". Ask's "late on 121 State" leaves out the 2 late submittals that Today counts. The Accounting badge 6 counts review lines next to "Receipts to Approve 6". Fix: one lateness predicate per noun, with the label stating the rule.
- **Blocked views fall through to Ask silently (S3).** PM opening Budget, or coord opening Bills or Banking, should land on Home with a toast naming who can open it.
- **Daily Log weather is typed by hand (S3).** Leave a hook to pull weather from the job address on the hosted copy. The floating "Say It" covers Next on every phone step: dock it off the step nav.
- **Residue (S3):**
  - "Review ›" and "Budget vs Actual by Account ›" glyph links;
  - the brief's "yes; and 8 more below";
  - Ask's note pointing to "Sales › Leads" (gone);
  - both New Opportunity and New Lead on one list;
  - phone Home shows Approvals twice (sub-tabs and bottom bar).

### UX
- **Phone Daily Log Crew and Sign Off are broken (S2).**
  - Crew: hour inputs sit over the names ("Alberto" shows as "A"), and the role text wraps one word per line.
  - Sign Off: the attestation is an empty grey box, with "I was on site today…" running down a one-letter column.
  - Fix: name and role stacked over a narrow hours input; a full-width checkbox row for the attestation.
- **Daily Log content gaps (S3):**
  - the review's PHOTOS section is blank while the step said "3 photos";
  - hours are unrounded (6.97 h) — round to 0.25;
  - the morning field report "Restoration crew did not show" is not pre-filled as a delay;
  - the % sheet note never reaches "What got done";
  - subs carry headcount but no hours.
- **Banking (S3):**
  - the primary should be "Review 16" (or Reconcile when an imported statement waits), not Connect / Sync;
  - the reconcile summary names lines reconciled but not yet matched to a bill;
  - Budget vs Actual "Overhead +$27,475" splits out the $22,841 uncoded;
  - the AMOUNT header jumps when a line is unticked.
- **Title Case residue on labels (S3):**
  - record h1 "Change order";
  - "Unsaved changes", "Discard changes", "Edit milestones", "Find matches";
  - "Take photo";
  - foreman chips "I need something", "Drawing question", "Hidden condition / extra", "Sub no-show", "Materials or a tool", "Dump run";
  - "1 change orders awaiting signature".
- **Copy (S3):**
  - the Billing page lead prints under the Invoice and CO h1;
  - "Approve All Hours (2)" sits above 4 cards;
  - a paid-in-one-go invoice lights "partial" in the status flow;
  - the Materials check says "2.5in drywall screws — we already have these" because it matched a drywall lift.

### Ops
- **Daily Log PDF (S3).** Print / PDF / send-to-owner on the PM log list; owners' reps ask for Procore's daily-log PDF.
- **The photo stream stops at viewing (S3).** Add markup and annotation, comments, delete and re-tag, download, a photo report or PDF, and attach to RFI / CO / punch item. Add bulk select for sharing.
- **Minor (S3):**
  - the CO Extends Task hint wraps one word per line;
  - "Pending COs $2K" for $1,850;
  - the client Finish tile cuts the PM note mid-word;
  - the decision header sits under the sticky project bar;
  - a client submittal approval needs a confirmation (see §1.4).

---

## §3 Toward "10x", once §0–§2 are green
These are not reviewer findings. They are what the reviewers kept circling: the product must feel like ONE tool, not a stack of fixes.
1. **Fold the wrapper chains.** For each heavily wrapped function (render, paAsk, jobFin, companyPL, toast, save, docAction/docActions, openEditor, thCoBar, eaToday, closeChecklist), write one clear function that does what the chain does today, prove it against the suites, and delete the layers. It is faster, debuggable, and stops seams such as double-applied adjustments.
2. **One predicate registry.** `needs()`, lateness, "waiting on", "ready to bill", "open AP" and "late material" are each defined once, as named predicates. Screens, badges, tiles, Ask, ⌘K and the Report Builder read them by name. counts_lint enforces it.
3. **Every person's day starts in one place.**
   - Home is the queue, ordered by what blocks someone else.
   - Each item carries its one next action inline (Approve, Draft It, Bill It, Reply, Choose).
   - Delegation moves items to the right person, so the owner's queue is only what only the owner can do.
4. **Performance.** Measure boot, view switch and input latency on a mid-range phone (6x CPU throttle). Target view switch under 100ms and boot under 2s. Memoise jobFin and companyPL per DB revision.
5. **Accessibility.** Keyboard paths for every primary flow, focus management after dialogs, ARIA on tabs and grids, contrast AA.

---

## §4 Round 5: the role experts' first walk (2026-10-10)
Reviewers: `.claude/agents/` role experts, each a full day with a linked workspace (the owner on his real one). Reports in `review/r5_<role>/report.md` (git-ignored).

| Role | Screens | Assistant | Brain | Overall | Would choose it over… |
|---|---|---|---|---|---|
| Owner | 6.5 | 4 | 4.5 | 5.5 | "beside QuickBooks and my inbox for a quarter; not yet let anyone tap Approve on what it proposes from mail" |
| PM | 7 | 5 | 6 | 6.5 | Procore / Buildertrend on the schedule story; not until the two S1s are gone |
| Coordinator | 6 | 5 | 4 | 5.5 | "the day the PO chain and the owner's approval queue hold money correctly" |
| Controller | 7.5 | 5.5 | 4 | 7 | QuickBooks today for the gates and the audit chain; NetSuite once the WIP ties |
| Client | 6.5 | 4 | 4 | 5.5 | Buildertrend's portal once the file editor and the design-phase truth are fixed |

### Severity 1, with the lane that owns the fix
1. Money proposals from mail point the wrong way (Zelle credits as bills, rent as AR, a stranger's deposit claim watched). **brain**
2. "View the Sheets" opens the staff file editor to the client, with Save and Delete. **clientfix**
3. The design-phase portal states construction truths on an unpaid retainer. **clientfix**
4. A give-back never closes; a second Pull In pulls 4 more days; the next publish would send a false finish. **ops**
5. A client's approved overage has no path to a change order. **ops**
6. A PO with no vendor and a $0 line issues from a released submittal (§1.4 #1 was never rebuilt). **purchasing**
7. A bill read from mail lands with no PO and no job; Bill Remaining ignores it ($95,000 billed on a $76,000 order). **purchasing**
8. Submittal responses recorded on someone's behalf are attributed to the reviewer, including the client. **purchasing**
9. A PO submitted for the owner's approval reaches nobody. **purchasing**
10. WIP does not tie to the ledger after the close (§1.1 #1); the close does not refuse. **closetie**
11. Budget activation and lock are unguarded in the functions (§1.1 #6). **closetie**
12. One coding click re-recognised $27,000 of revenue by cost-to-cost against an unreviewed EAC. **closetie**

### The classes behind the severity-2 findings
- **Regression from the askgen merge (found 2026-10-10 by the ops lane):** truthpct_test's 8 Ask money checks fail on master: "margin by job" answers the company's YTD margin, the backlog and margin answers lost their per-job rows with "14% complete", and the EAC answer lost "Estimate at completion on …". The figures are right; the per-job breakdown is gone. truthpct_test is now in run_all's default list so this cannot slip again. **assistant**
- **The assistant guesses:** typo correction overreaches on known nouns; client names resolve to staff; "friday" is Thursday; memory rewrites the user's words; drafts are a template; chases send nothing; a slow answer hangs the thread. **assistant**
- **The brain does not learn from events:** lessons are a fixed menu, fired 0×; nothing from a no-show, an extra before its CO, an LPC resubmit, a wrong-finish return, a $0 PO, a dispute, a void, a reopen, thirteen meetings. **learn**
- **Proposals never reach a hand:** mail-read bills, imports, quotes, receipts, W-9 chases sit on the Comms screen; "X wrote about Y" with no button. **learn** (Needs Your Hand queue)
- **Field answers stop at "save a record":** no-show, inspection booking, the client's choice, the sample approval. **ops**, **clientfix**
- **The reader does not finish the job:** quote → task not price; receipt → uncoded line; delivery date → note; credit memo → nothing. **purchasing**
- **Clones and counts:** 206 Lenox carries 121 State's decisions and materials; "late" and "blocked" still have several numbers on the purchasing screens; two Alans; "[image: …]" as a person. **ops**, **brain**

---

## §5 Platform: from a single-player demo to the firm's system
**Decision (Alan, 2026-10-11): Supabase (Postgres, auth, row-level security) plus Netlify (functions, scheduled functions, hosting), as the firm's earlier hosted copy. The lost server pieces are rebuilt from HANDOFF.md's specs and `legacy/hosted-app-2026-09-15.zip`. Secrets (Anthropic API key, Plaid, Google OAuth client, BANKFEED_KEY) live only in Netlify and Supabase settings, never in the repo or chat. Starts after the 2026-10-15 weekly reset, on the plan's included usage.** (Alan, 2026-10-10: "to the highest level, especially all the AI features")
Today every person's data lives in their own browser and every guard runs in the page. Rebuild the hosted half (HANDOFF "What was lost") so ten people on ten phones share one truth.
1. **Shared database, sign-in, sync.** Supabase (Postgres) as the system of record; Google sign-in per person; `cloud.js` rebuilt (per-user assistant shards, pending markers, keepalive push on pagehide, re-push before pull so a local edit is never overwritten); offline on site with conflict rules (money records server-wins with a visible conflict, field notes merge).
2. **Security in the database, not the page.** Row-level security per firm, per role and per client: a client's phone never receives another client's rows; field roles never receive money; the budget, close, journal and approval rules enforced by database functions; the hash chain's head per period stored server-side, so rebuilding the chain in a browser is detected. The browser checks stay as the first line, never the only one.
3. **The AI connection, to the highest level.** A server proxy (`/api/ai`), with server-side web search for sourcing research (§1.8 item 10), with the model pinned by environment and a per-person and per-firm cost ceiling. The assistant is the model with the ERP as its tools: every entity and field of `erpQuery`, the PRED predicates, truth coverage, drafts, proposals and the expectation ledger; answers cite the query they ran; writes are proposals with a button. One assistant per person, with that person's role, jobs, standing orders, memory and connected mail, calendar and drive. The deterministic parser stays as the offline path and as the model's grounding tools. An evaluation harness runs the Ask bank (tune, held-out, held-out-2) against the live model on every release.
4. **AI guardrails.** Mail, documents and transcripts are data, never instructions (prompt-injection tests with hostile mail: "pay this now", "update our bank details", "ignore previous instructions"); a change to a vendor's or the firm's bank details needs two people and a call-back; every AI action is logged with its evidence and reason; the brain can propose an ERP change but a person approves and it ships through a review.
5. **Document reading.** The server extracts text from PDFs, Office files and images (the lost `doctext`), so every vendor invoice, quote, COI and statement is read; a proposal says when a document could not be read.
6. **Watchers that run while phones are in pockets.** The per-user Gmail, Calendar and Drive watcher (the lost `assistant-watch`), Plaid bank and card feeds with webhooks (link, exchange, cursor sync, sealed tokens), and the daily sweep (chases, reminders, lesson triggers, obligations) on a schedule.
7. **iPhone and speed.** Safari (WebKit) checks on a real iPhone or a WebKit runner, storage persistence (Safari can clear site data after a week unused; the server copy is the cure), and boot under 2 s and view switch under 100 ms with a mid-range phone's CPU (§3.4).

8. **The real agents (Alan, 2026-10-11: "creating the real AI agents").** These are the ERP's own agents, running on the Claude API through the server, not in the page. Each one has a job, a schedule, tools (erpQuery, the PRED and CATCH registries, mail, calendar, drive, document reading, and web search where named), a budget, and the Standard as its operating instructions (`standardPrompt`, the AI section in full, plus the playbook of the role it serves). Every write it makes is a proposal unless the person has delegated that message type (`standardAllows`). Every run is logged with its evidence, its reason and its cost.
   | Agent | Serves | Runs | Does on its own | Proposes |
   |---|---|---|---|---|
   | Personal assistant (one per person) | that person | on demand, plus a morning brief | reads, answers, drafts, reminds | anything that writes, sends or commits |
   | The brain | owner | nightly | reads every record, mail, transcript and outcome; finds patterns and repeat mistakes | rules, process changes and lessons (the owner approves) |
   | Procurement | procurement manager | hourly in business hours | RFQ ingest, quote reading, leveling, sourcing research (web search), price watch, delegated follow-ups | awards, negotiation emails, new vendors |
   | Documents | billing, coordinator | as mail and photos arrive | reads invoices, receipts, slips, acknowledgments and COIs; files them; checks they line up | low-confidence reads and mismatches for a person |
   | Schedule and look-ahead | PM, foreman | daily, plus Friday | three-week look-ahead, need-by dates against lead times, slips | resequencing, client updates (the PM sends) |
   | Billing and collections | billing | daily | ready to bill, the collections cadence (due, 7, 15, 30) | invoices and reminders (billing sends) |
   | Compliance | coordinator, owner | daily | COIs, licences, permits and LPC dates, 30 days ahead | chases (sent if delegated) |
   | Books | controller | daily, plus close | bank and card matching, unmatched lines, close checks by the 10th | journal entries (always flagged), close |
   - **Models.** The highest-capability Claude model for the brain and hard reasoning; a mid-tier model for assistants and procurement; the smallest model for classifying and filing. Each is pinned in server settings, never in the page.
   - **Cost control.** Each agent has a monthly budget and the firm has a hard ceiling. The Standard and the role playbooks are prompt-cached. The owner sees spend per agent per month. An agent that hits its budget stops and says so.
   - **Evaluation before go-live.** The Ask bank (tune, held-out, held-out-2) runs against the live model; prompt-injection tests run with hostile mail; and each agent shadows for a week (proposals only, compared with what people did) before any delegated autonomy is switched on.
   - **What Alan sets up.** An Anthropic API account with billing and a spending limit (separate from his Claude plan), Supabase, Netlify, and a Google OAuth client. Keys go only into Netlify and Supabase settings.

## §6 Go-live and the 10x scorecard
1. **Real data in.** Clients, jobs, vendors, people, open estimates, invoices, bills and POs imported (the existing paste-from-Excel import, the QuickBooks snapshot load, and the master-data proposals from real mail), demo data removed, opening balances from QuickBooks.
2. **A parallel month.** The ERP runs beside QuickBooks for one month; the Three-Way Tie-Out must agree every week before QuickBooks is retired; a cutover checklist with an owner and a date.
3. **Who moves first.** The owner, the PM and billing; then the coordinator and the controller; then the field; then clients in the portal.
4. **The 10x scorecard, measured before and after.** Days from work done to invoice sent; days from invoice to cash; hours a week each person spends on email and admin; days to close a month; dollars of unbilled work and reimbursables found; chases answered on time; items that slipped (the month simulation's ledger). The baseline is taken from QuickBooks history and the real mailbox before cutover.

## §7 Later (Alan, 2026-10-10: "leave for later; I need to better understand this")
New York rules a design-build firm lives by: Lien Law Article 3-A trust funds per job; sales tax on capital improvements vs repairs (ST-124); site safety training cards at clock-in (NYC Local Law 196); workers' comp and COI enforcement before payment.

---

## §8 The month (tests/month_sim.py, first full run 2026-10-10, on the build before the ops, clientfix and purchasing merges)
`MONTH caught 153/290 on time · 3 late · 134 missed · $519,735 left behind · 29 schedule days lost` (dollars summed per event; the same money can count twice).
Per person (expected · on time · missed): owner 21 · 4 · 17; PM 56 · 28 · 28; coordinator 58 · 26 · 30; billing 42 · 17 · 25; controller 68 · 48 · 20; designer 23 · 14 · 8; foreman 12 · 8 · 4; driver 5 · 4 · 1; Kleins 5 · 4 · 1.
The cracks, each owned by a lane:
1. **Deposits never recorded** (Kleins $68,265, Lenox $15,000, Jessops $12,000): once the controller codes a deposit, nothing raises Record Payment for billing; Rivera $21,350 recorded but never in the bank has no path to resolve. **learn** (Needs Your Hand) with billingNeeds.
2. **Payroll runs in no one's Approvals** ($16,040, $18,100, $18,680): DELEGATION has no payroll kind; the controller cannot approve a run he built; payrollFromTime spans 8/4–9/4. **learn**
3. **Payroll and tax debits and card charges matched to nothing** (34 lines unmatched at close); the 10/1 close refused. **brain** (truthCandidates) and **learn**
4. **Earned-not-billed held by a job-level hold** ($25,000; measured 60–100% billed at 51.67%); floating client purchases and reimbursables reported, never billed (spUnbilled $111,269 at month end). §1.5 #1–#2. **leaks** (next)
5. **Bills at the PM's turn hide under "waiting on the others"** (AMP-311, SE-0951, TF-5512, WW-131). **learn** (delegation of bills)
6. **Chases send nothing** for leads, retainers and client decisions (4 days lost). purchasing built vendor chases; **assistant** extends to people.
7. **A bill over its PO approved in full** when it had no PO link (CM-0109, $4,600 over); the Window Works dispute has no path to close by credit memo. **purchasing** (verify on the re-run)
8. **Late order lines have no order path from the line** (11 days). **purchasing**
9. **Vendor slips, LPC revisions, hearing decks, mailed promises stay notes** (5 days on the hearing deck); calendar events are not on Today. **brain** and **learn**
10. **The designer has no Inbox; the foreman's Today lacks deliveries and the plumber's visit; the driver never saw the pickup; the client's sample approval failed on the portal.** **learn** / **clientfix** (verify on the re-run)

**Flow lane (2026-10-10, tests/flow_test.py):** cracks 6, 8, 9 (deliveries, visits, dated asks, mailed choices) and 10 (sample approval) fixed at the path a person takes: Order on every late or due line (a quote's Apply opens it), mail proposals for field asks, choices, dated asks, deliveries and visits, meeting holds and CO disputes routed on Needs Your Hand, the field answer writes the priced CO, every Chase drafts to the person, escalation on site hours. Month at db8d418: 206/291 on time · 80 missed · $137,278 · 13 schedule days; after: `MONTH caught 239/291 on time · 6 late · 46 missed · $109,613 left behind · 3 schedule days lost`. Still open in this class: the joist CO has no price on the record (E039, and the dispute that follows), the lighting submittal waits on the architect nobody in the month plays (E042/E043), Tomas Restoration is not a vendor on file (E138).

### The month, build by build (2026-10-10 to 10-11)
| Build | On time | Late | Missed | Left behind | Schedule days lost |
|---|---|---|---|---|---|
| Start of round 5 fixes | 153/290 | 3 | 134 | $519,735 | 29 |
| + ops, clientfix, purchasing | 160/290 | 4 | 126 | $483,362 | 23 |
| + brain | 172/290 | 5 | 113 | $453,462 | 23 |
| + learn, assistant, seams (v8) | 206/291 | 5 | 80 | $137,278 | 13 |
| + leaks and flow (master 265579f) | **257/292** | 6 | **29** | **$1,937** | **3** |
Still open after leaks and flow: the lighting submittal never released (no architect event in the book), the joist CO unpriced (no price on record), Tomas Restoration not a vendor on file, the countertop slab and radiant mats ordered 2 and 1 days late, payroll runs ($7,920 and $10,932) below what the bank paid ($18,100 and $18,680) with the gap not yet shown as hours paid but not approved, and leak_test's three PARTIALs (overspend at landing, per-figure source ids, nothing-slips edge cases).

