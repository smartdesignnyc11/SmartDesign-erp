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
