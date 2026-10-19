# The plan: everything we said we'd do

This is the one list. The chief of staff keeps it current on every ask, lane report and merge. Details live in the BACKLOG sections named. Status words: **Running** · **Next** · **Queued** · **Waiting on Alan** · **Later** (deferred by Alan) · **Done**.

Last updated 2026-10-18 (platform set up).

## 0. Usage rule (Alan)
- Warn before any heavy step.
- Don't start a big round when weekly usage is above about 60%.
- One build lane is roughly 6–10% of a week's allowance. The lean pilot is about 2–5%.

## Version 11: published 2026-10-18 (build 84687e4)
- https://claude.ai/artifact/2c28fUyespjyJFyRFbnXAp
- Full net: 32 of 32 suites green.
- Scripted month: 258 of 292 on time, 29 missed, $9,537 left behind, 1 schedule day lost. The previous best was 239/291, 46 missed, $109,613.
- The 29 misses remaining are queued below ("From the scripted month").

## Platform: first slice live (2026-10-18)
- **Where:** https://smartdesigns-erp.netlify.app (new Netlify site; the 12 old sites untouched) on a new Supabase project in us-east-1. Alan is invited as owner by email. How it works: `platform/README.md`.
- **Built and checked live:** invited sign-in only; roles set by the owner on the server; field roles never receive the books, bank, payroll or bills and get money stripped from jobs, and their saves cannot touch money; clients refused until per-client rows; edits sync between two devices both ways, simultaneous edits on the same job both kept; `/api/ai` refuses anyone not signed in or without a role, answers members on the model the server picks, and logs each call's cost (live checks 27/27 and 17/17).
- **Supabase is on Pro** (daily backups, no pausing), so real data can go in once the import (§6) is built.
- **Sign In with Google is on** (2026-10-19), invited addresses only; the consent screen reads SmartDesigns Projects.
- **Mail, calendar and Drive are private to each person** (2026-10-19): own rows only that sign-in can read, the owner included; live checks 37/37 and 25/25. Fixed on the way: device settings (who is on the phone, the open job) were syncing, so one phone's save switched other devices to that person.
- **Alan's Google is connected** (2026-10-19, signed in as alan@smartdesign.nyc): first sync 40 mails, 55 calendar entries, 500 Drive files, all in his private rows, none in shared rows, no Google tokens stored. Both sign-ins now share one private store (server-set link).
- **The watcher is live** (2026-10-19): every 15 minutes, weekdays 7am to 7pm New York, new mail, calendar changes and Drive files go into each watching person's private inbox; the app files them on opening. Alan turns it on with Settings › Connections › Keep Watching When It Is Closed. The watcher's key reads only (it cannot send mail). Push notifications are live: at most one per run, for vendors, clients, jobs, agencies and meetings in the next two days. Alan turns them on in Settings › notifications (iPhone: add to Home Screen first). The watcher's finds now become nudges in the assistant's conversation. The owner invites people and signs any account out everywhere from Settings › Team Accounts; a signed-out phone loses access at once and erases its copy.
- **The document reader is live** (2026-10-19): text PDFs and Word read free on the server; scanned PDFs and photos read by the small Claude model within the caps (a receipt photo read exactly in the live test). Spreadsheets and HEIC photos get a note for now.
- **Alan signed in** (2026-10-19, email link); the firm workspace holds the first upload (84 collections, demo data).
- **Not built yet:** spreadsheets and HEIC in the reader, per-client portal rows, the server-side hash-chain head, document reader, mail/calendar/drive watcher, Plaid, push, the agents.

## Overnight 2026-10-18: where things stand (for Alan at 10am)
- **Published:** version 11 (v11.1 folded in). Build 84687e4: 32/32 suites green; scripted month 258/292 on time.
- **Pilot:** 3 days, 9 role experts, both workshops. Reports are in `docs/pilot/pilot1/`, and the menu result is in `docs/MENU_DRAFT.md`.
- **Merged on master since v11:**
  - plans control phase 1;
  - cross-set consistency, demo phase (xset_test 66/66);
  - find it again after every save: the new record is highlighted, or listed in a "Made Today" card with Open (15 cases, findable2_test 185/185); the pay app starts each line at its billed cumulative and refuses to go below it; outbox mail shows Name <email>, and invoice mail goes to the billing contact;
  - pilot fixes batch 2 (pilot_fixes2_test 72/72): real clock times, mail cards on every sync, money matching, Reverse Payment, In the Bank Not Applied, agency notices move bookings, the driver's pickups, card accounts from statements;
  - pilot fixes batch 1 (19 items and follow-ups);
  - the calendar date fix.
- **Still building:**
- **v11.2 published (2026-10-18, artifact Version 3, build 379182f):**
  - full net 37/37 green;
  - scripted month 258/292 on time, 29 missed, $9,537 left behind, 1 schedule day: identical to v11 event by event;
  - the merges first dropped the month to 251/291. Lane monthfix found 2 app bugs (a template-to-install order held for its own template; a client credit read as a double bill) and 2 month actors still acting on old screens (the foreman's Daily Log, the driver's route drop).
- **Batch 3, queued from the Documents Workshop:**
  - a send gate on every client document: strip internal notes, require cost codes, bill-to and true titles, print how to pay, one letterhead;
  - progress billing tells the truth: one pay app per period, stop when billed exceeds measured, no $0 apps, one "Amount due";
  - every record keeps its line link;
  - the item library (§1.18).

## v11.1 (first thing after the reset)
- **Fix the v11 net regressions** (2026-10-11 run):
  - client questions are missing from the PM's Home (likely the own-sent-mail filter);
  - emailed asks and calls no longer become proposals;
  - the short-pay path on Do Now;
  - purchasing, client and flow tests that predate the vendor-on-file rule;
  - track_test crashes on a click timeout;
  - pricewatch "why is this flagged".
- **Ranking (Alan):** anyone blocked today, such as crew waiting, ranks above older overdue items, and both stay visible.
- **Harness findings 6–8:**
  - a new CO defaults to the wrong client;
  - the PM's phone menu is hidden under More;
  - the client portal's View doesn't open.
- **Review:** integrate's three held commits.

Then the full net, the scripted month and the final crawl; then publish v11.

## 1. Running now
| What | Where | Status |
|---|---|---|
| Second integration pass | lane integrate2 | Running |
| Agent-month harness: the shared world, the screen-only toolkit, the outside world, the referee, role briefings | lane agentsim, BACKLOG §1.17 | Running |

The integration pass covers:
- price watch and order tracking alerts linked to the Standard;
- one "What My Assistant May Send for Me" card;
- Enter the Bill;
- tasks findable after save, plus find-it-again tests for every create;
- stock held as inventory.

## 2. Version 11 release (next)
1. Merge integrate2 (crawl merged; smoke 2,436 pass on the merged build).
2. Run the full test set, one suite at a time.
3. Run the scripted month simulation.
4. Run the phone check at 390px.
5. Publish, push, and send Alan the link.

## 3. The order of work (updated 2026-10-18, folding in the Oct 17 Cowork session)
The Cowork plan's first steps are already done in this repo:
- the code is on GitHub;
- the test net was rebuilt (screen lint, counts lint, the Ask bank with held-out sets, the day walk, the finance cross-check);
- round 5 was redone (closetie, truthpct, askgen, clientpo).

What remains, in order. Usage is a share of one week's allowance.

| # | Work | Spec | Lanes | Usage |
|---|---|---|---|---|
| **Week 1** | | | | |
| 1 | v11.1: fix the merge regressions, crew-waiting-first ranking, harness findings 6–8; full net; publish v11 | PLAN v11.1 | 1–2 | 10–15% |
| 2 | Lean expert pilot (3 days) + the Navigation, Pages and Documents workshops, with the visual review | §1.17 | runs | 3–6% |
| 3 | Plans control + the cross-set consistency workflow (demo phase) | §1.22, §1.23 | 2 | 15% |
| 4 | Simplify: the menu (from the workshop), one task system, one queue per person, the alert budget, the structure lint and completeness tests | §1.14–1.16, §1.11 | 3 | 25% |
| | Integration and merges | | | 10% |
| **Week 2** | | | | |
| 5 | Live-job capabilities on invented equivalents: two payers per contract, range estimates with allowances and a paid exploratory phase, the HTC calculator and hard/soft/contingency estimate, the contractor-to-employee user | §1.25, §1.26 | 2 | 15% |
| 6 | One assistant per person (four screens into one), approval rules, activity log | §1.27 | 1–2 | 12% |
| 7 | Role specialists on the demo + planted-problem banks; cost intelligence (cash-negative jobs, benchmarks, receipt price book, driver store list phase 1); savings ledger | §1.28–1.31 | 3 | 25% |
| 8 | Item library, Messages phase 1 (with record cards and @assistant), Spanish for the field | §1.18, §1.21, §1.20 | 3 | 25% |
| | Integration and merges | | | 10% |
| **Week 3** | | | | |
| 9 | Subcontractors, lien waivers and the payment check | §1.10 item 1, §1.12 | 2 | 15% |
| 10 | Reporting proven end to end | §1.13 | 2 | 15% |
| 11 | Platform foundation: database, sign-in, permissions, sync, AI connection with caps (**first slice live 2026-10-18**); next: watchers, document reader, push, Google sign-in, per-client rows | §5 | 3–4 | 35% |
| | Integration and merges | | | 10% |
| **Week 4** | | | | |
| 12 | The live AI on Claude:<br>- Ask like Claude;<br>- the always-on assistant per person;<br>- role specialists and Brain timers;<br>- the documents and drawing reader;<br>- driver routes phase 2 (Maps);<br>- live jobs loaded into the private platform;<br>- the improvement loop | §1.24, §1.27–1.29, §1.19, §5.8 | 4 | 40% |
| 13 | Real-data pilot with the team; the full ten-expert regrade to 9+; go-live checklist | §6 | runs | 20% |

**Totals.** About four weekly allowances on the current plan, so roughly four weeks of calendar time. Each week fits under the 60% rule only if a week's round is split into two halves.

**Bought as extra usage at API prices,** the same work is about $1,500–3,000.

**Running costs once live:** about $150–700 a month, mostly AI, under a cap Alan sets.

## 4. Queued (built after the above, or folded in where they fit)
- **The transcript reader** (§1.33): Claude reads the whole meeting, corrects Gemini's notes, and turns lessons into process changes for approval. It joins week 4's live AI (row 12). The notes reader is built (2026-10-18).
- **Speed:** boot under 2 s, view switch under 100 ms on a phone (§1.11 item 5).
- **Notifications:** push notifications and morning and evening digests, on the platform (§1.11 item 6).
- **Office and field input:**
  - voice input for the field (§1.11 item 7);
  - bulk actions for the office (§1.11 item 8);
  - the first week for each role, and empty states (§1.11 item 10).
- **History and the agents:**
  - import 12–24 months of history from QuickBooks and the bank, so price watch and on-time records work on day one (§1.10 item 2);
  - agent heartbeats, an AI activity log, and a pause switch per agent (§1.10 item 3).
- **Money and controls:**
  - cost-plus honesty: credits and overpayments flow to the client's invoice (§1.10 item 4);
  - vendor creation and bank changes need two people; separation of duties (§1.10 item 5);
  - the right entity on every PO, bill and stock item, and intercompany transfers (§1.10 item 6).
- **Shared purchasing address** for the agents, with SPF and DKIM (§1.10 item 7).
- **Rollout and proof:**
  - rollout: each person acknowledges the Standard, and gets a first-week guide (§1.10 item 8);
  - the "AI pays for itself" scorecard (§1.10 item 9).
- **Records and accounting:**
  - seven-year retention, nightly backups, full export, offline plan (§1.10 item 10);
  - a read-only accountant role (§1.10 item 11).
- **Estimates and stock:**
  - material and labour split per estimate line, so savings and price checks have a material budget;
  - a trip-cost model for the "not worth the trip" stock override.
- **From the platform session (2026-10-19):**
  - the inbox reader turns any question in mail into a to-do nudge, including personal mail from senders not on file ("Lunch Friday? Are you free?"); recommend: senders not on file need a job, money or date before they nudge;
  - spreadsheets and iPhone HEIC photos in the document reader;
  - a real push on Alan's phone and a real watcher run on his Gmail, not yet seen.
- **Gaps the build lanes found:**
  - a toast's Open link sits above the editor's scrim and can navigate away with the editor still open (closing on navigation would drop unsaved edits; needs an "unsaved changes" prompt instead);
  - client portal: pay online, or "we paid";
  - the foreman can only measure today's tasks;
  - sub POs default to SD Plumbing;
  - a mailed bill's PDF is not attached to the bill.
- **From the scripted month:**
  - (2026-10-18 run) a vendor credit memo has no path to close a held dispute ($3,800);
  - an approved overage never becomes a priced CO (the joist, $1,450);
  - client purchases on a card have no reimbursable row ($487);
  - a statement in mail or Drive becomes a task, not an import and reconcile;
  - agency mail (DOB, LPC, inspections) closes no schedule task;
  - a quote's Apply opens a task instead of pricing the line;
  - a vendor date in mail never becomes the PO's expected date;
  - Chase writes a note instead of a draft to the party;
  - a COI for a sub not on file is only noted;
  - the designer's and PM's Home miss some items;
  - the lighting submittal never released;
  - the joist CO unpriced;
  - Tomas Restoration not on file;
  - the countertop and radiant mats ordered late;
  - payroll paid but hours not approved (show "hours paid but not approved").
- **Test gaps:**
  - leak_test's three partial catches (overspend at landing, per-figure source ids, nothing-slips edge cases);
  - Ask held-out 35 of 40;
  - 413 PDF attachments unread (needs the platform's document reader).
- **Go-live and the 10x scorecard** (§6).

## 5. Waiting on Alan
| Asked | Decision or action | Default until then |
|---|---|---|
| 2026-10-11 | Which email address the vendor follow-ups come from (recommend purchasing@ on the firm's domain) | Outbox only (demo) |
| 2026-10-11 | Who the accountant is. To confirm with them: use tax; the overhead method; Mercer & Bond development costs capitalised; revenue recognition for tax; stock held as inventory | The defaults in §1.13 item 8, labelled "confirm with your accountant" |
| 2026-10-11 | Leftover material on cost-plus jobs: back to the client, a credit on their invoice, or into firm stock | "Client-owned surplus, ask the PM" |
| 2026-10-11 | ChatGPT export, for `docs/ALAN.md` | Profile from the build sessions and the Standard |
| 2026-10-10 | Re-authorise QuickBooks (July to date, then the history import) | Bank and card lines and the bridge snapshot |
| Later | Google sign-in consent screen (guided, about 5 minutes) | — |

## 6. Calls I made that Alan can change
- **Ranking:** overdue and today first, then the decision principles. Immediate safety and law always lead, and a missing insurance certificate counts as immediate.
- **Explanations:** a "this quarter" price explanation expires at the quarter's end.
- **Stock matching:** "5/8 sheetrock" with no type asks the procurement manager rather than guessing between Type X and moisture-resistant.
- **Phone home screen:** it hides the "because" lines to stay under 180 words; they show on Approvals and on desktop.
- **Quote rule:** "outside Manhattan and Brooklyn" means any other borough or out of state.

- **PM's phone bar (2026-10-18):** Home, Approvals, Projects, Tasks, Field, More.
- **New CO, Invoice or Estimate off a job's screen asks for the client** (it used to take the last job's).
- **A task saved with no owner goes to the job's PM** (or the design director on a design job), with who, when and why recorded; it can be switched off.
- **The owner's "Waiting on the Others" list** follows the one ranking order. Grouping it by person is proposed for the one-queue-per-person work.

## 7. Later (Alan deferred)
- NY rules (§7): "I need to better understand this."

## 8. Done recently
Full detail is in `docs/DECISIONS.md`.
- The Standard in the app.
- Inventory before buying.
- The RFQ flow.
- The job chain and overhead model.
- Price watch.
- Order tracking.
- The first integration pass.
- The chief of staff.
- The prevention method (§1.16).
- Click crawler: 11,098 controls pressed, 544 flags fixed by class to 0.
