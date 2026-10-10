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
| `ct*` (closetie, §1.1) | just before the truthpct section, and an outermost layer after `PRED` | The close read back: `ctCloseStatus(ym)`, `ctCloseHistory()`, `ctAccrualAtClose(ym)`, `ctWipTie(ym)` / `ctWipTieRows(ym)` (the blocking tie-out `fin2RunClose` runs), `ctOrphanAccruals()` with Record the Run / Reverse…, `bfIsDemoOnly`, `bfVoidNotAtBank` (through `truthVoidTxn`), `billChangeDate`, `budGuard`, budget CSV export/import, EQ tables `closes`, `wiptie`, `orphanaccruals`, predicates `orphanAccruals`, `notAtBank`. In the fin3 area: `fin3JobAdjust` (adjustments inside the raw read, before the freeze) and `fin3PostDated` / `postOn` (the posting period every management figure honours). The outermost layer: `ctHoldBasis` (a revenue basis that moves over 5 points in a day waits for the CTC review), `ctBalanceAt` (a closed Pack's balances at its month end), `ctCloseAsk` and the `journal` / `close` kinds in DELEGATION. |
| `PRED` | end of file | The predicate registry: every counted question (waiting on me, late material/decision/submittal, a job's Needs You, buy-board filters, unsigned, open POs, bills awaiting approval…) defined once with its rule. Screens, badges, tiles, Ask and saved searches read it by name; add a predicate here rather than a new filter in a screen. |
| `tdRender` / `TD_PULSE` / `CATCH` | after `PRED` (today) | The Owner's and PM's Home, drawn by the outermost `renderHome` (no older Home layer runs for them). `TD_PULSE[role]`: three numbers, each `PRED.<name>` (`safeToSpend`, `overdueAR`, `jobsAtRisk`; PM: `jobsLate`, `clientDecisionsDue`, `siteQuestions` over their jobs), each opening a sheet of its rows; the job-level ones (`jobsAtRisk`, `jobsLate`) count jobs and list each job's late items (`PRED.jobLate`) underneath. Do Now is `PRED.waitingOnMe` ranked by `tdScore` (who is blocked, money at stake). `CATCH` is the detector registry for Caught for You: push `{name, label, rows()}` with rows `{key, what, sub, amount, verb, run}` to add one. `tdChrome` is the phone header (the page title, search, Ask, New, the flag; 44px targets), hides the page's own heading where the header carries the same title, and drops the sub-tab strip that repeats the bottom tab bar. |
| `DELEGATION` / `apprOwner` | next to `APPR_CHIPS`, before `renderMApprove` | Whose queue an approval sits in: kind → the role that owns it, the rule in words, and `who(it)` where the record decides (a pm-approved bill, an escalated question and a PM's own hours go to the owner). The last `mApprovals` layer (just before `PRED`) sets `it.who` and keeps the signed-in role's items; `mApprovals({everyone: true})` is the whole queue, the owner's "N more wait on the others" on Approvals. Every producer pushes for every seat; only the delegation decides. |
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

## Demo Workspace (demows: the end of `src/app.js`)
An invented Google-shaped workspace per app user (mailbox, calendar, drive), served through the **same code paths real Google uses**, so every watcher, router, nudge, draft, filing and lesson runs on it. The lost server half (assistant-watch every 15 minutes, `doctext.mjs` for PDFs) is stood in for in the browser.
- **Connecting is explicit and per user.** Settings › Connections › "Connect Demo Workspace" (shown when the firm has no Google client id), the assistant's "I am not connected" offer, or `gcDemoConnect()` as the signed-in user. The client role has no workspace. A boot adds nothing. Disconnect removes the rows it pulled in (`gcWipe` also drops `demo` rows, the unapproved meetings read from them, their payment claims and the nudges that pointed at them).
- **Where the state lives:** exactly where the real path puts it. `DB.conn[uid].google = {demo: true, email, name: "Demo Workspace", cursors: {gmailAt, calTok, driveAt}, lastSync, every: 15, …}`, so `gcOn()`, `gcMine()`, `gcIsDemo()`, `gsTimer` and the Connections card work unchanged. `DB.asst[uid]` holds the nudges and the expectation ledger. What a session writes into the workspace (drafts, sent mail, holds) persists in `DB.demoWs[uid]` and is merged on the next build.
- **Serving:** `gcFetch` hands every request to `gsFetchDemo(url, opts)` when the connection is demo, before any token work; a real token never reaches it. `gsFetchDemo` answers in API shape: `messages.list` (q `after:`/`newer_than:`/`in:sent`/`label:`, `maxResults`, `pageToken`, `historyId`), `messages.get?format=full` (payload, headers, base64url parts, attachments), `attachments.get`, `messages.modify`, `drafts` and `drafts/send` (into the mailbox's Drafts and Sent), `history.list`; `events.list` (`timeMin`/`timeMax`/`updatedMin`, `syncToken` → `nextSyncToken`), events `POST` (holds and bookings), `freeBusy`; `files.list` (q `trashed`, `modifiedTime >`, `name contains`, `fullText contains`), `files.get?alt=media` and `export` (the file's text). `gcDocText` and `gcAttachText` read the `text` a demo file or attachment carries, which stands in for the server-side PDF reader; the comment in `gsAtt` says so.
- **Content** (`demoWsBuild(uid)`, scenes shared across personas): u_owner, u_alan, u_chen, u_angel, u_sarah, u_billing, u_controller get 14–24 threads, 8–10 events and 8–9 files each; u_alberto and u_alex a handful. All invented, all on the app clock (`today()`), all against the seed records: 121 State / the Kleins, 45 Cranberry / the Riveras, 140 Prospect / the Jessops, 206 Lenox; Window Works, Alberto M Plumbing, Carlos Millwork, Tino, Nemo Tile, Bedrosians; the structural PE on the flitch beams; the expediter and DOB NOW; LPC on the brick mold and the 45 Cranberry hearing; the answering service; Home Depot receipts; the Amex August statement; A-301 and S-101; a transcript; a proposal to a quiet lead.
- **The watcher in the browser:** `gsTimer` (every `g.every` minutes while the page is visible; 15 for the demo) and Sync Now call `gsRun`, which pulls, then `paWatch` runs the nudges and, through the demows wrapper, `paMailExpectSweep` (a message I sent that asked something, with nothing back on the thread, becomes an expectation `paChaseWatch` chases), `paPaymentClaimSweep` (a client's "we paid Tuesday" matched to a bank credit and the recorded payment, or watched for) and `paChaseWatch`. `cmImport` routes (`cmRoute`) and reads (`cmRead`) every message, `mtScan` ingests meeting notes (`mtIngest` → proposals, `mtDraftChanges(mtLearn())`, `bnRun`).
- **What the reader learned for this** (`cmRead`/`cmApply`, root): attachments' text is part of what is read (a vendor's invoice PDF becomes a `bill` proposal with its amount, number, due date and job; a COI carries its policy period into `coi.exp`, and approving it sets the vendor's `insuranceExp`, which clears the compliance block); "we paid Tuesday" is a `deposit` claim; a vendor `quote` names the Buy Board line it prices (`materialId`), and approving it puts cost, vendor, lead and "quoted" on the line; `lpc` comments attach to the project's LPC inspection or submittal and `permitNotes`; `noshow` for a sub who did not show; `receipt` matches a store receipt to the card line; `statement` for our own card or bank statement (never a vendor bill) and for a vendor chasing a bill already on file (never a second bill); `unrouted` for a sender nobody has on file (never dropped; a proposal to create the vendor, client, lead or project); newsletters and promotions with nobody we know on them are `ignored`. `gsRouteFile` also routes a Drive file to a vendor (COI, W-9, quote) and names its kind (drawing, statement, transcript, invoice, proposal); `gaFile` files on a vendor too.
- **Privacy:** a connected mailbox is its owner's. `cmListFor`/`renderCommsInbox` show the firm inbox (no owner) plus my own; `eqOwnOk` (Ask) hides other owners' `google` and `demo` rows; `paMail`/`paDrive`/`paEvents` are mine. `CM_STAFF()` no longer counts client-portal users as staff.
- **A workspace loaded at run time (Loaded Workspace):** `gsAttachWorkspace(uid, ws)` registers a workspace object for the session; `gcDemoConnect()` then serves it and names it "Loaded Workspace" everywhere. `tests/harness.py: attach_workspace(pg, uid, path)` reads it from an absolute path outside the repo or `SD_WORKSPACE_<uid>`, and refuses a path inside the repo; a real export never enters the repo, tests, docs, dist or a commit, and reports about one carry counts only. `*.workspace.json` is git-ignored. `dwFromJson` accepts the export shape as well as the short one: `labelIds` or `labels`, `internalDate` or `date`, Google-shaped events (`start`/`end` as `{dateTime}` or `{date}`, `summary`, `location`, `attendees` as objects, `organizer.email`, `status` — cancelled ones are dropped), files with `modifiedTime`, `owners`, `parents`, and `accounts.gmailMailbox`/`ownerEmails` for the owner's address when `email` is missing. Shape (dates are ISO, or relative to the app day as `{day, time}`):

  ```json
  { "email": "chen@smartdesign.nyc", "name": "Chen Biron", "exportedAt": "2026-10-12T18:00:00Z",
    "mail": { "threads": [ { "id": "t1", "messages": [ { "id": "m1", "date": "2026-10-02T10:15:00",
        "from": "Nemo Tile <sales@nemotile.example>", "to": ["Chen Biron <chen@smartdesign.nyc>"], "cc": [],
        "subject": "Quote Q-2271", "text": "Hi Chen, …", "labelIds": ["INBOX", "UNREAD"],
        "attachments": [ { "filename": "quote.pdf", "mimeType": "application/pdf", "text": "the PDF's text" } ] } ] } ] },
    "calendar": { "events": [ { "id": "e1", "summary": "Site visit — 121 State Street", "start": {"dateTime": "2026-10-13T14:00:00-04:00"},
        "end": {"dateTime": "2026-10-13T15:30:00-04:00"}, "status": "confirmed", "location": "121 State Street", "description": "",
        "attendees": [{"email": "angel@smartdesign.nyc"}], "organizer": {"email": "chen@smartdesign.nyc"}, "updated": "2026-10-05T12:00:00Z" } ] },
    "drive": { "files": [ { "id": "f1", "name": "121 State - A-301 Stair Section Rev 2.pdf", "mimeType": "application/pdf",
        "modifiedTime": "2026-10-09T16:00:00Z", "owners": [], "text": "the file's text" } ] } }
  ```
- **The clock a sync runs on** (`gsNow`, `gsNowIso`, `gsFirstDays`, `gsCalWindow`): real Google and the built-in demo run on the app clock; a Loaded Workspace runs on its own `exportedAt` (else the latest thing in it), so the first-sync window is its whole span (`W.firstDays`), the calendar window covers its events (`W.calFrom`..`W.calTo`), and the cursors `gmailAt`/`driveAt` are stamped with its date, never the wall clock. The seed's app day stays 2026-09-03: records written by the app (`at`, `createdAt`, tasks' dates) stay on `today()`, so a loaded mailbox dated after the app day reads as "in the future" to the chase and due-date logic; that is the honest consequence of two clocks, and it is why the Loaded Workspace is for ingestion and routing calibration, not for the day's nudges.
- **Paging and the cursor** (root, `gsGmail`/`gsDrive`): the list is paged (`pageToken`) until the window is exhausted or the run has its fill (`gsRunCap`: 40 messages a run on Google, the whole window on a demo or loaded workspace), and the mail cursor advances only when the run read everything the window listed; otherwise the next run lists the same window and carries on, skipping what it already holds. Drive follows `nextPageToken`. Before this, one newest page read once starved everything older: a loaded mailbox landed 40 of 524 messages and then nothing, and 100 of 200 files.
- **A first sync is not a storm** (`paWatch` wrapper): on `delta.first`, each message, event and file from the last two weeks of the sync clock is raised on its own; everything older is routed, read and proposed on the comms screen, and raised once as one line.
- **Master data from unrouted mail** (`paMasterClusters`, `paMasterSweep`, `paMasterApply`, `paMasterIgnore`; BACKLOG §1.7 #13): threads that match no client, project or vendor are clustered by correspondent (an organisation's domain → "vendor or firm"; a person at a public mail provider → lead or client) and by the project-like addresses they name (→ job). The clusters live on `DB.asst[uid].master` with their evidence (threads, messages, first and last date, money words, attachments, contact, addresses); one nudge summarises them and Ask answers "who is not on file" with one-tap offers. Approving one creates the record (vendor, lead or client, or a job from the project template, linked to the person who wrote about the address) and routes every thread in the cluster, re-reading their proposals (an invoice from a newly created vendor becomes a bill proposal). Nothing is created on its own; "not ours" sets the cluster's threads to ignored. A job created this way is a clone of the project template, like every new project (see the founder finding on 206 Lenox).
- **Suite:** `tests/demo_ws_test.py` connects each persona in a fresh context, syncs, asserts the flows above, prints what each assistant proposed, syncs twice, checks the client (u_klein) sees none of it, and disconnects.
