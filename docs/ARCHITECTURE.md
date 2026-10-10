# Architecture map

## Files
| File | What it holds |
|---|---|
| `src/head.html` | Meta tags, title, fonts |
| `src/styles.css` | All CSS: the base design tokens, then each feature's block appended in order |
| `src/body.html` | The shell markup: rail, topbar, one `<section class="view" id="v-…">` per view, drawer, palette, viewer, toast |
| `src/app.js` | All logic (recovered from the round-4 build and pretty-printed; comments stripped) |
| `legacy/commented-source-v96/app.js` | The commented source as of 2026-09-15, with `/*<<section.js>>*/` markers: read it for intent |

## Section order inside `src/app.js` (oldest first; later sections wrap earlier functions)
1. **Core.** Dates (`DAY`, `iso`, `parse`, `addDays`, `fmt`), the clock (`today()`, `appNow`, `appNowIso`, `stampText` near the top), seed data, the schedule engine, the Gantt, estimates, invoices, POs, bills, payments, bank, job cost, `render()`, the views.
2. **Accounting module.** Ledger (`ledger`, `glSync`, `glDerive`), COA (`GL_COA`), periods and locks, close, WIP, statements, Pack, Flash, report builder (`REP_DS`, `REP_DEFS`).
3. **IA layer.** `IA_GROUPS` (nav groups and their views), `ROLE_VIEWS`, overviews (`OV_BUILD`, `OV_TILES`, `renderOvPage`), tiles (`TL_SETS`, `TL_HOST`), `needs(gid)`.
4. **Assistant.**
   - Per-user assistant: `pa*`, store `DB.asst[uid]`.
   - Google layer:
     - `gc*`: OAuth through GIS; the token in memory and sessionStorage only.
     - `gs*`: Gmail/Calendar/Drive pulls.
     - `ga*`: drafts, holds, filing.
   - Query engine: `EQ_TABLES`, `erpQuery`, `erpResolve`.
   - Translators: `qa*`.
   - Model loop: `mind*` (tools only; results wrapped `{untrusted, source, data}`; writes become proposals).
5. **Round 1–2 lanes.** frontdoor, records, create, finance, ops, flow, integ, overview, locks, finance2, thread, ask, integ2.
6. **Round 4.**

   | Wave | Lanes, with each lane's function prefix |
   |---|---|
   | A | close (`fin3*`), payables (`pay3*`), onecount (`readyToBill`, `salesRows`, `jobNeeds`, `OC_BADGE`), ask4 (`a4*`, `ASK_INTENTS`), cause (`cz*`) |
   | B | billing (`bl*`, `billingNeeds`, `apOpenBills`), records2 (`rc*`), client (`cl*`), screens (`os*`, `t2*`), trust (`tr*`, `tcase`, `appWeek`, the clock rewrite) |
   | C | budget (`bud*`, `bva*`), bankfeed (`bf*`), submittals (`sm*`), field (`prg*`, `pst*`, `dl*`, `fx*`) |
   | Then | integ4, integ5 |
7. **Round 5.** askgen (`ag*`, `eqRows`, `eqSchema`), after the predicate registry: the schema-aware Ask parser and the one privacy scope under `erpQuery`.

## Where to find things (first mention in `src/app.js`; grep to find every reassignment)
| Symbol | Line | Note |
|---|---|---|
| `appNowIso` / clock | ~109 | |
| `ROLE_VIEWS` | ~3,269 | |
| `render(` | ~3,563 | then wrapped many times; grep `render = function` |
| `signIn` | ~16,599 | |
| `ledger` | ~23,416 | |
| `companyPL` | ~23,493 | |
| `jobFin` | ~27,148 | |
| `IA_GROUPS` | ~62,257 | |
| `glSync` | ~67,684 | |
| `paAsk` | ~108,191 | wrapped 10+ times |
| `gcConnect` | ~108,845 | |
| `EQ_TABLES` | ~110,953 | |
| `erpQuery` | ~111,054 | |
| `mindAsk` | ~112,485 | |
| `fin2RunClose` | ~126,601 | |
| `ASK_INTENTS` | ~130,184 | |
| `fin3Raw` (close.js) | ~131,534 | |
| `pay3Register` | ~134,090 | |
| `jobNeeds` | ~134,965 | |
| `salesRows` | ~135,135 | |
| `readyToBill` | ~135,842 | |
| `a4Past` | ~136,401 | |
| `czCauseOf` | ~138,571 | |
| `billingNeeds` | ~139,780 | |
| `rcToast` | ~140,820 | |
| `clTaskSweep` | ~142,436 | |
| `osFold` | ~144,567 | |
| `trInert` | ~145,227 | |
| `budActual` | ~145,993 | |
| `bfCoverage` | ~148,298 | |
| `smOpen` | ~152,078 | |
| `prgJob` | ~155,073 | |
| `dlMissing` | ~156,093 | |
| `jobFinDerive` | after `jobFin` | eac → earned, over/under, backlog, GP in one place; every jobFin wrapper that moves `actual` calls it |
| `tpJobPct` / `jobFinEac` | just before `PRED` (truthpct) | `tpJobPct(p)`: the one job % complete (SOV lines weighted by value, measured on site; `tpJobPctDetail(p)` gives the lines). `jobFin(p).eac` is rolled up by estimate/CO line (`J.eacLines`, `jobFinEac`); `J.pct` is the cost basis (revenue), never printed as "% complete" (`tpCostWords(J)`). `tpCertified(c)`: what the client is shown as complete. `tpForecastWhy(p)`: the forecast's cause. |
| `eqRows` / `agParse` / `agRead` | after `PRED` | askgen (BACKLOG §1.3). `eqRows(entity)` is the one scope for every Ask path and `erpQuery`: a client reads only their own jobs' rows, foreman, crew and driver read no money. `agParse` reads a question into entity, filters (jobs, clients, vendors, people, payees the books hold, a period on `today()`/`appWeek()`, statuses, negation), measure and grouping; `agRead` runs the readers (`AG_FIN`, `AG_OPS`, `AG_ENT`, then `agGeneric`) and every answer carries "I ran: …" in `interp`. The outermost `paAsk` wrapper: the older chain only answers what no reader takes (memory, reminders, mail, documents by number), and a refusal from it comes back for a text search. |
| `PRED` | end of file | The predicate registry: every counted question (waiting on me, late material/decision/submittal, a job's Needs You, buy-board filters, unsigned, open POs, bills awaiting approval…) defined once with its rule. Screens, badges, tiles, Ask and saved searches read it by name; add a predicate here rather than a new filter in a screen. |
| `tdRender` / `TD_PULSE` / `CATCH` | after `PRED` (today) | The Owner's and PM's Home, drawn by the outermost `renderHome` (no older Home layer runs for them). `TD_PULSE[role]`: three numbers, each `PRED.<name>` (`safeToSpend`, `overdueAR`, `jobsAtRisk`; PM: `jobLate`, `clientDecisionsDue`, `siteQuestions` over their jobs), each opening a sheet of its rows. Do Now is `PRED.waitingOnMe` ranked by `tdScore` (who is blocked, money at stake). `CATCH` is the detector registry for Caught for You: push `{name, label, rows()}` with rows `{key, what, sub, amount, verb, run}` to add one. `tdChrome` is the phone header (search, Ask, New) and drops the sub-tab strip that repeats the bottom tab bar. |
| `truthBacking` / `truthCoverage` / `truthFlagOf` / `truthChain` / `truthMatchOf` / `qboLoad` | end of file (truth, BACKLOG §1.6) | One function per truth figure. `truthBacking(row)`: the evidence behind a management-ledger row (bank/card-backed, document-backed accrual, by hand; the Demo Feed is never bank evidence); `truthCoverage(range, {projectId})` adds them up for Statements, the Pack, the job report, the Ledger overview and Ask. `truthFlagOf(j)`: a posting with no source document (manual, opening, close, accrual) is flagged "Manual · by who · when · why" on ledger rows, statement lines (`truthManual(range).byAcct`, drill-down), the Pack, the Flash, the close checklist and Ask; the Controller drafts (`glEntrySave`), the Owner posts with a typed reason (`glApprove(id, why)`). Append-only: `truthEdit(kind, ref, why, fn)` amends a posted record as a linked reversal and re-post (`truthWhyNext` carries who/why into `glReverse`/`glPost`), `truthVoidTxn` moves a typed line to `DB.voided`, `truthHistory(key)` and the History strip; delete is refused on posted records. `truthChain(ym)` (FNV-1a 32 over `prior|n|id|key|source|date|acct:dr:cr…`) is sealed by the close into `DB.periods.chains[ym]` and re-verified by `truthVerify(ym)` (Verify the Books). `truthMatchOf(t)` is the one link model `{billId, billLineId, poId, poLineId, estimateLineId, invoiceId, invoiceLineId, payrollId}` written by `truthSetMatch`; `truthCandidates`/`truthProposeAll` propose where amount, vendor and date agree, people confirm; `PRED.unmatchedTxns` (with `byMonth()`), the `unmatchedTxns` CATCH entry, a close blocker and `truthException` (Owner or Controller, with a reason). `qboLoad(snapshot)` loads a QuickBooks snapshot idempotently (`source: "quickbooks"`, `qboId`) and `truthTieOut(ym)` is the Three-Way Tie-Out (Reports › Financials › Three-Way Tie-Out, Ask). |
| `apprBillYes` / `fAnswerRaise` | before `renderMApprove` / after `fOfficeCard` | The one yes on a waiting bill (through `billAction`, so over-PO opens the short-pay sheet) and the one Answer to a field question; Approvals, the field card and Do Now all call them. |

## Data (global `DB`, persisted with `save()` / `saveNow()` to IndexedDB)
- **Firm:** company (with `asOf`), people and users, clients (contacts, properties), vendors.
- **Projects:** each `p.project` (name, contract, target, out, lpc…), schedule tasks (pct, pctLog, history with `ev` / `seq` causes), decisions (options, clientTitle), issues/RFIs, files, submittals, and a published snapshot (`pub`).
- **Documents:** estimates, change orders (revisions `-R<n>`, `supersedes`), invoices / pay applications (SOV lines), purchase orders, bills (`short` for disputed differences), payments.
- **Bank and payroll:** bank and card transactions (`prov` provenance), statements, `bankFeeds`, `bankRecons`, payroll runs (alloc, accruals), time entries.
- **Accounting:** periods (`locked`, `frozen`, `history`), journals, `budgetPlan` (versions, active, audit).
- **Assistant and messaging:** `asst[uid]` (thread, memo, standing, log), outbox, messages, audit.
- **Field:** `photos` (references; blobs in IndexedDB `sd_photos`), `field` (daily logs, `dlDraft`).

## Hosted copy (Netlify + Supabase)
- **Last surviving copy:** see `legacy/hosted-app-2026-09-15.zip`. Later server pieces that must be rebuilt are listed in HANDOFF.md.
- **What it does:** builds `public/index.html` + `public/app.js` from the same src. `cloud.js` syncs DB collections as rows; field roles get money stripped server-side.
- **Netlify functions:** `/api/ai` proxies Anthropic. The rest cover mail, calendar, clipper, harvest, qbo, etc.
