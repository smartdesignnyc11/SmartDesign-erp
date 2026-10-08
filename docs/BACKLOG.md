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
1. **Release Order makes a real PO (S1).**
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
3. **The estimate hint stays out of the description.**
   - What happens: the hint "…Contract line on EST-2026-014: $34,500 — for reference; enter this change's quantity or price" is saved into the CO line `desc` and prints on the client's CO and PDF.
   - Fix: keep it in `refAmount`, shown as a hint only, and clean already-saved descriptions.
4. **The client sees what they approve.**
   - Each client submittal approval gets "View the Sheets", which opens the file, plus a confirmation step like CO signing.
   - It counts in Waiting on You, the nav badge and the Decisions tile.
   - Fold the client's four lists (Your Decisions / To Sign / Waiting on You / Approve Before We Order) into ONE Waiting on You list, with one count.
5. **The client Overview shows progress.**
   - Show Progress (the certified figure from §1.2) plus the last 3 shared photos.
   - Retire the stale "last update from Alan on Tue, Jul 28" line.
   - The PM writes a client caption when sharing; internal tags (DAILY LOG) are never shown.
6. **Portal approvals are not inbox work.** They land in project Messages as handled activity, not "New" with Review / Ignore / Delete.
7. **Phone document overflow (regression).** On the CO draft, the meta block (621px in 268px) pushes Title / Project / Date to x=645. Collapse the meta block to one column under 480px, and sweep every document type on phone for elements wider than the viewport.
8. **Icons.**
   - `.bp-ic` has no size: the PO "Documents:" note renders a ~1,000px PDF glyph, and the Documents grid crops 209px glyphs.
   - Default SVG size 16px; proper 48px file tiles.
9. **A dirty document keeps its primary.** Pricing a CO line hides "Send to Client" behind "Unsaved changes · Save". Send saves first, a quantity commits on blur, and the primary never disappears. Apply this to every document type.

### 1.5 leaks: money leaks and slipped work are caught automatically (north star; from tests/leak_test.py, 2026-10-08)
Baseline: 2 MISSED, 4 PARTIAL. Every item is proven by its leak_test scenario turning CAUGHT.
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

---

## §2 Remaining round-4 findings

### Founder
- **206 Lenox is a clone (S2).**
  - What happens: "3rd floor turnover", $0 contract, carries 121 State's 39 schedule lines and its decisions verbatim. Owner Approvals shows 3 duplicate decisions, Ask's "11 decisions waiting on the client" includes 5 clones, and Chen's tasks and Purchasing's 28 rows include clone items. Purchasing also lists 140 Prospect's "LPC application" as a thing to buy.
  - Fix: reseed 206 with its own small scope, and strip non-materials from Purchasing.
- **The owner's Approvals is a catch-all (S2).**
  - What happens: 26 items, but the chips cover only 13 (Bills 2, Hours 4, Decisions 7). The rest are crew hours, a material acknowledgement, meeting proposals, "a build" and lessons.
  - Fix:
    - Chips sum to Everything.
    - Delegation rules: hours to the PM or foreman, material acknowledgements to Chen, bills under a threshold to the PM.
    - One waiting count shared by Home, the rail and Ask.
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
