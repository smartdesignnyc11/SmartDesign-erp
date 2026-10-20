# The plan: everything we said we'd do

This is the one list. The chief of staff keeps it current on every ask, lane report and merge. Details live in the BACKLOG sections named. Status words: **Running** · **Next** · **Queued** · **Waiting on Alan** · **Later** (deferred by Alan) · **Done**.

Last updated 2026-10-20 (Alan: "Go" on week 4 and on the three calls; three lanes and the main session running).

## 0. Usage rule (Alan)
- Warn before any heavy step.
- Don't start a big round when weekly usage is above about 60%.
- One build lane is roughly 6–10% of a week's allowance. The lean pilot is about 2–5%.

## Week 4 (2026-10-20, Alan: "Go")
Alan's "Go" approved the week-4 live AI round (about 40% of a week's usage) and the three recommendations below. Each call is reversible; `docs/DECISIONS.md` logs them.

**What this round builds.** Row 7 of the order of work (role specialists, cost intelligence, the savings ledger) was never built, so this round builds row 7 and the parts of row 12 that depend on it.

**Running now** (board and design gates in `docs/LANES.md`):
| Lane | Builds | Spec |
|---|---|---|
| role specialists | A standing auditor per role with the six-step handling of every finding; the savings ledger; planted-problem banks per role with recall and precision; workload (an overloaded person, work moved to someone with capacity, the manager approving) | §1.28, §1.30, §1.31, §1.32 item 2 |
| cost intelligence | Jobs spending more than they bring in (one shared rule); benchmarks per trade per unit; the receipt price book across stores; the driver's store list (routes phase 1); the price-book and route tests | §1.29, §1.31 (price book and routes) |
| improvement loop | One improvement queue from every signal; the Brain triages and proposes; the owner approves; the reporter is told; checked a month later; lessons from meetings carry to the next matching job; admin chased within the approval rules; approved changes become build requests; the Brain on timers | §1.19, §1.32 items 1, 3, 4, 5 |
| main session | The three decisions built in, then the merge follow-ups below | — |

**The three decisions (Alan's "Go", 2026-10-20), built by the main session:**
1. **Who releases vendor payments.** The controller keys, matches and prepares the weekly Payment Run; the owner releases it in one tap; billing is the backup releaser when he is away. Separation of duties stays on.
2. **What "we owe" means.** Approved bills, equal to the books (account 2000). Bills awaiting approval on their own line, the same number everywhere. The cash forecast counts both.
3. **Spanish.** Jeanette reviews the ~900 words, safety terms first. Crews stay in English until she does. Alan asks her.

**The merge follow-ups (main session):**
- scope a payer's Ask on the hosted AI by payer, before any two-payer client gets the portal;
- payNormalise must not hide a double payment (an unmatched check stays unmatched; a second payment on one bill is flagged; a planted double payment in the finance cross-check);
- a separation-of-duties test (the controller keys a bill and tries to release it; the coordinator sets up a vendor and tries to release its payment; billing as backup tries a bill it keyed);
- three quotes checked when a subcontract issues, with a written reason when fewer;
- two blue buttons with a bill's drawer open, and the screen lint judging what is on top;
- the accounting-choices card says in plain words that the choices do not change the statements yet;
- the close-out cost factor read by estimating and folded into the item library (one price book). Do this before the cost intelligence lane merges, because its benchmarks feed estimating too.

**Not in this round, and why:**
- **The live jobs load** waits on Alan handing over his file in a private session (§5).
- **Driver routes phase 2** needs a Google Maps key in Netlify, Alan's to add (§5).
- **The transcript reader** (§1.33) was promised for week 4 and no lane holds it. Recommended: add it to the improvement loop lane, whose §1.32 item 1 (lessons from meetings) needs it. Otherwise it slips.
- **The drawing reader** (§1.23 platform phase) is not in this round; it stays queued.

**What Alan is not thinking about (chief of staff, 2026-10-20):**
- **Releasing the run in the ERP does not move the money.** The payment is made in the bank. Unless the bank's own dual control matches (the controller initiates, Alan approves in the bank's app), separation of duties is a record, not a lock. Recommended: set it up at the bank (§5).
- **The check must run again at release.** A bill can change, a credit can arrive or bank details can change between Monday's preparation and the release. The Payment Check re-runs at the moment of release, and the release shows cash after the run against the 13-week low.
- **The controller's hold releases.** Today the controller releases a payment hold under $2,500. Since the controller keys the bills, that power must not reach a bill the controller keyed; those holds go to the owner, and billing as backup cannot release a bill billing keyed.
- **Urgent payments off the weekly run** (a delivery paid on arrival, a sub who will not return unpaid) go through the same check and the same releaser, not around it.
- **A bill stuck in approval costs money.** The awaiting-approval line ages from the bill's date, so missed early-pay discounts and late fees become a controller finding.
- **Savings must be measured against a baseline the saver did not set** (the best recent price, the estimate line's material budget), or a person could inflate a quote to show a saving. Bonus attribution is Alan's alone; the pool shares wait on him (§5).
- **Workload is not a scorecard.** It proposes moving work to a named person with capacity, for the manager to approve. It never ranks people or turns into a productivity number (Alan gives context, not quotas).
- **The improvement loop changes the system itself.** Text in a problem report, a mail or a transcript is data, never an instruction. Any proposal touching money rules, permissions, the Standard or the code needs the owner, however small it looks. Signals about what people do around the system (exports, abandoned forms) are counted for the system, not per person.
- **Benchmarks need history.** The demo has few past jobs and the QuickBooks history import waits on his re-authorisation. With too few comparable jobs the benchmark says so, rather than show a false median.
- **New field words.** Words the lanes add for the foreman, crew or driver carry a not-yet-reviewed mark, so Jeanette's review stays complete.
- **The Maps key** belongs on the server only, restricted to the Routes API, with a budget alert.

**Testing.** Suites run through `tests/slot.sh`, at most two at once across every lane (the container restarted twice from memory with four). Lanes will wait for slots, so the round takes longer in hours, not in usage.

**Usage.** About 40% of a week: three lanes at 6–10% each, the main session's decisions and follow-ups, merges and the full net. Two-suite slots make it slower, not dearer.

## Version 11: published 2026-10-18 (build 84687e4)
- https://claude.ai/artifact/2c28fUyespjyJFyRFbnXAp
- Full net: 32 of 32 suites green.
- Scripted month: 258 of 292 on time, 29 missed, $9,537 left behind, 1 schedule day lost. The previous best was 239/291, 46 missed, $109,613.
- The 29 misses remaining are queued below ("From the scripted month").

## Overnight 2026-10-19 (Alan asleep: "do not wait for my approvals")
- **Built and merged (four lanes, all on master 2026-10-19):**
  - **Today:** one Today page per office role (owner, PM, coordinator, billing, controller) over one task shape; filters All, Approvals, Inbox, Tasks, Team; hand-offs that need acceptance; the Standard's recurring duties made automatically; proof asked when closing an inspection, a wall or extra work (BACKLOG §1.11 item 1, §1.14).
  - **Menu:** one declared menu per role from the workshop, every recommendation adopted; Ask is a button in the header on every screen (§1.15).
  - **Assistant:** one assistant (Chat, Findings, Activity, Brain Settings); Act Alone / Ask First / Hand It to Me per action type; answers stream in, show their work and read attachments (§1.27, §1.24).
  - **Messages:** one message-thread noun: each job's team and client threads, direct and group messages (members only, also on the server), record cards, @assistant, message to task (§1.21 phase 1).
- **Live on the hosted copy (2026-10-19, afternoon):** all four lanes, the fixes, and Chat in the header. Full net 44/44 on the merged build; live checks 73/73 (database rules) and 33/33 (two devices: an assistant answer streamed through the real AI door, a direct message office to phone and back).
- **Live (2026-10-19 evening): the new Ask and its mind, and phone speed.** Ask looks and works like the Claude app; the day opens on a briefing written as a message; it reads every line, looks in more than one place, checks every figure and learns (rules through the owner); the server writes each office person a briefing three times a weekday (first run tomorrow 7:20). Reopen on a phone under 3 s. Net 22/22 before deploy, the rest running; live: briefing run end to end 6/6.
- **Live (2026-10-20): the team chat, phase 2.** WhatsApp/iMessage-style chat, New Chat with anyone, the owner's All Chats, field roles only on their crew's jobs (schema applied), private read markers, notifications. Net green on the merged build; live: database rules 74/74, field jobs 28/28, two devices 33/33. Found live and fixed: a field person on no job could not open the app.
- **Done (was waiting on Alan's go): the executive assistant (Alan, 2026-10-19: "a Fortune 500 executive assistant, an assistant project manager, not a bot that answers questions").** Ask opens on what it has done and what it needs from you, not an empty box: a briefing it wrote (today, what it did since you last looked, decisions with one-tap approve, what it is chasing for you); it works between your visits (the server runs it on a schedule for each person, from the watcher and the records), drafts replies, prepares meetings, chases vendors and subs within each person's rules, keeps a ledger of what it did; it remembers how you work (people, preferences, standing instructions) in memory only you can see; you can talk to it on the phone; for a PM it runs the job like an assistant PM (late tasks, open RFIs and submittals, the weekly update drafted). One lane, about 6–10% of a week's usage; the AI caps need raising for the scheduled runs (the owner's $8 a month will not cover them).
- **Found and fixed while merging, each with a check that failed first:** the menu and the assistant disagreed on The Brain and the Chief of Staff (now entries that open the assistant on their tab); after sending one invoice the next draft had no Send to Client (the Made Today card swallowed the header); on a phone, Open on a sent invoice's mail left the line below the screen; the demo's message threads could have seeded into the live workspace; the owner's assistant rules for someone never reached that person on the hosted copy; two phones would each make the Friday update.
- **Done by the main session tonight:** the AI door streams to the page; the nightly Brain on the server (first live run on QA data proposed five grounded changes for 5 cents); the books' seals; the document reader with spreadsheets; Sign Out Everywhere and invites; the watcher's nudges; faster phone start-up (part).

## Platform: first slice live (2026-10-18)
- **Where:** https://smartdesigns-erp.netlify.app (new Netlify site; the 12 old sites untouched) on a new Supabase project in us-east-1. Alan is invited as owner by email. How it works: `platform/README.md`.
- **Built and checked live:** invited sign-in only; roles set by the owner on the server; field roles never receive the books, bank, payroll or bills and get money stripped from jobs, and their saves cannot touch money; clients refused until per-client rows; edits sync between two devices both ways, simultaneous edits on the same job both kept; `/api/ai` refuses anyone not signed in or without a role, answers members on the model the server picks, and logs each call's cost (live checks 27/27 and 17/17).
- **Supabase is on Pro** (daily backups, no pausing), so real data can go in once the import (§6) is built.
- **Sign In with Google is on** (2026-10-19), invited addresses only; the consent screen reads SmartDesigns Projects.
- **Mail, calendar and Drive are private to each person** (2026-10-19): own rows only that sign-in can read, the owner included; live checks 37/37 and 25/25. Fixed on the way: device settings (who is on the phone, the open job) were syncing, so one phone's save switched other devices to that person.
- **Alan's Google is connected** (2026-10-19, signed in as alan@smartdesign.nyc): first sync 40 mails, 55 calendar entries, 500 Drive files, all in his private rows, none in shared rows, no Google tokens stored. Both sign-ins now share one private store (server-set link).
- **The watcher is live** (2026-10-19): every 15 minutes, weekdays 7am to 7pm New York, new mail, calendar changes and Drive files go into each watching person's private inbox; the app files them on opening. Alan turns it on with Settings › Connections › Keep Watching When It Is Closed. The watcher's key reads only (it cannot send mail). Push notifications are live: at most one per run, for vendors, clients, jobs, agencies and meetings in the next two days. Alan turns them on in Settings › notifications (iPhone: add to Home Screen first). The watcher's finds now become nudges in the assistant's conversation. The owner invites people and signs any account out everywhere from Settings › Team Accounts; a signed-out phone loses access at once and erases its copy.
- **Long AI answers no longer vanish** (2026-10-19): the door streams, so answers past 30 s arrive (4,000 tokens in 41 s), and anything past 52 s comes back cut short with its cost logged. Before, a long answer was lost at 30 s and its cost escaped the caps. Longer work belongs to the scheduled agents.
- **The books' seals are held by the server** (2026-10-19): each closed month is sealed with SHA-256 from the server's own copy of the books, add-only; Verify the Books checks against it and names any changed, missing or added posting.
- **The document reader is live** (2026-10-19): text PDFs and Word read free on the server; scanned PDFs and photos read by the small Claude model within the caps (a receipt photo read exactly in the live test). Spreadsheets are read since the same night; HEIC photos get a note for now.
- **Alan signed in** (2026-10-19, email link); the firm workspace holds the first upload (84 collections, demo data).
- **Next platform lane (recommended):** the client package for the portal (BACKLOG §5 note): clients stay refused until a client's phone can receive only its own figures, proven by a planted-secret test.
- **Not built yet:** HEIC photos in the reader, per-client portal rows (clients stay refused), Plaid, the agents beyond the nightly Brain. Field roles still receive every job.

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
  - the item library (§1.18): done 2026-10-20 (merged with Spanish).

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
| 5 | **Done 2026-10-20 (merged fa3337d).** Live-job capabilities on invented equivalents: two payers per contract, range estimates with allowances and a paid exploratory phase, the HTC calculator and hard/soft/contingency estimate, the contractor-to-employee user. Follow-ups in §4 | §1.25, §1.26 | 1 | 15% |
| 6 | One assistant per person (four screens into one), approval rules, activity log | §1.27 | 1–2 | 12% |
| 7 | **Running 2026-10-20 (week 4, lanes role specialists and cost intelligence).** Role specialists on the demo + planted-problem banks; cost intelligence (cash-negative jobs, benchmarks, receipt price book, driver store list phase 1); savings ledger | §1.28–1.31 | 3 | 25% |
| 8 | **Done 2026-10-20 (items and Spanish merged 8d9c1f7; Messages phase 1 merged 2026-10-19).** Item library, Messages phase 1 (with record cards and @assistant), Spanish for the field. Follow-ups in §4 | §1.18, §1.21, §1.20 | 3 | 25% |
| | Integration and merges | | | 10% |
| **Week 3** | | | | |
| 9 | **Done 2026-10-20 (merged 3fc848f).** Subcontractors, lien waivers and the Payment Check before every vendor payment. Follow-ups in §4 | §1.10 item 1, §1.12 | 1 | 15% |
| 10 | **Done 2026-10-20 (merged 560057d), pending the full net on the merged build.** Reporting proven end to end. Follow-ups in §4 | §1.13 | 2 | 15% |
| 11 | Platform foundation: database, sign-in, permissions, sync, AI connection with caps (**first slice live 2026-10-18**); next: watchers, document reader, push, Google sign-in, per-client rows | §5 | 3–4 | 35% |
| | Integration and merges | | | 10% |
| **Week 4** | | | | |
| 12 | **Running 2026-10-20 (Alan: "Go"), with row 7.** Ask like Claude and the always-on assistant are done (2026-10-19); this round builds role specialists, the Brain's timers and the improvement loop; the live jobs load waits on Alan's file; routes phase 2 waits on the Maps key; the drawing reader is queued.<br>The live AI on Claude:<br>- Ask like Claude;<br>- the always-on assistant per person;<br>- role specialists and Brain timers;<br>- the documents and drawing reader;<br>- driver routes phase 2 (Maps);<br>- live jobs loaded into the private platform;<br>- the improvement loop | §1.24, §1.27–1.29, §1.19, §5.8 | 4 | 40% |
| 13 | Real-data pilot with the team; the full ten-expert regrade to 9+; go-live checklist | §6 | runs | 20% |

**Totals.** About four weekly allowances on the current plan, so roughly four weeks of calendar time. Each week fits under the 60% rule only if a week's round is split into two halves.

**Bought as extra usage at API prices,** the same work is about $1,500–3,000.

**Running costs once live:** about $150–700 a month, mostly AI, under a cap Alan sets.

## 4. Queued (built after the above, or folded in where they fit)
- **The transcript reader** (§1.33): Claude reads the whole meeting, corrects Gemini's notes, and turns lessons into process changes for approval. It joins week 4's live AI (row 12). The notes reader is built (2026-10-18). Not in any week-4 lane yet: recommended for the improvement loop lane (see "Week 4").
- **Speed:** boot under 2 s, view switch under 100 ms on a phone (§1.11 item 5). Measured on the hosted copy 2026-10-19 with a mid-range phone (CPU 4x slower, 1.5 MB/s): reopening took about 20 s, against 7.5 s for the local copy on the same CPU. Fixed so far: the time-zone formatter (4.6 s of it, now 0.16 s) and the page download on every open (the shell now opens from the phone's copy: 0 bytes, page ready in 1.9 s). Left: about 10 s of start-up work in finishBoot and the first render (job financials, overhead allocation, and render wrapped about 40 deep), which is this lane's work. `platform/test/live_speed.py` measures it; numbers taken while the full net ran are noisy.
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
  - vendor creation and bank changes need two people; separation of duties (§1.10 item 5). Partly built by the subs lane (2026-10-20): a bank change holds every payment until someone other than the requester calls the number on file, and whoever entered a bill or set up the vendor cannot release its payment. Not built: a second person to create a vendor;
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
  - iPhone HEIC photos in the document reader (spreadsheets are read since 2026-10-19);
  - a real push on Alan's phone and a real watcher run on his Gmail, not yet seen.
- **From the live jobs lane (merged 2026-10-20):**
  - Done 2026-10-20 (02746eb): a payment on account on a two-payer contract now waits as Not Assigned until billing assigns it to a payer, audited, raised on Today (livejobs_test);
  - Running (main session, week 4): a payer's Ask on the hosted AI is not scoped by payer (the screens and the query layer are); scope it before any two-payer client gets the portal;
  - contractor bills have no PO, so the no-PO checks name them, and her W-9 shows missing (recommendation waiting on Alan: a contractor agreement as her PO, no payment until the W-9 is on file, a 1099 total for year end). Since the subs merge the Payment Check holds her payments until the W-9 is on file;
  - demo payments have no bank lines, so the truth layer shows them as unbacked (demo only; real payments come from the bank);
  - Mercer & Bond on a job is a flag only, with no link to a deal record in the Mercer & Bond workspace;
  - the client's proposal shows a "Net" after tax credits (recommendation waiting on Alan: keep it internal until the tax-credit consultant confirms eligibility and timing);
  - the real jobs load into the private platform database through the import (§6), from the Cowork handoff's `docs/LIVE_JOBS.md`, which is not in this repo and must never be (joins row 12).
- **From the subs lane (merged 2026-10-20, 3fc848f):**
  - before deploy: the full net on the merged build (live jobs, the two-payer fix and subs together). The lane ran about 20 suites on its branch, not the 44-suite net on the merged result;
  - Running (main session, week 4): before any real bank or card data is loaded: when a check with no bank line is recorded, payNormalise ties it to whatever card line is on the bill, which can hide a double payment after the fact (pre-existing; financial truth). Fix it so an unmatched check stays unmatched and a second payment against one bill is flagged, with a planted double payment in the finance cross-check;
  - Running (main session, week 4): separation of duties has no planted case (now also billing as the backup releaser): every subs_test bill is entered by "Billing", so no test proves the person who keyed a bill is held from paying it. Add the case (the controller keys a bill and tries to pay it; the coordinator sets up a vendor and tries to release its payment);
  - Running (main session, week 4): the Standard's "three quotes on every subcontract" is not checked when a subcontract issues; it should be checked there, with a written reason when fewer;
  - Running (main session, week 4): a bill's drawer open leaves New Vendor Bill blue beside Pay (two primaries, pre-existing). The screen lint judges the page without the drawer; fix the class so it judges what is on top;
  - not built: the monthly vendor statement reconciliation; a deposit taken off a sub's later pay applications line by line (today the contract check holds such a bill, so money does not leak, but a good bill can wait); sub bid leveling by scope and backcharges; a sub's emailed invoice read into a pay application; a Kind column (Subcontractor, Supplier) on the vendor list;
  - Done 2026-10-20: the reports lane took master with subs in (f9716df) and ties retainage payable (2050), cleared payments and bills awaiting approval to the cent (reports_test).
- **Before the next deploy (chief of staff, 2026-10-20):**
  - Done 2026-10-20: live jobs, subs, items and Spanish, and reporting went live after a net of 26 suites on the merged build (chain 367/0, reports 450, subs 139, livejobs 172, items 68, spanish 109) and three fixes it found (`docs/LANES.md`).
  - Not yet run on that build: the other 28 of the 54 suites in `tests/run_all.sh`, and the scripted month (none recorded since v11.2). Run them through `tests/slot.sh` before the first week-4 merge, so a week-4 failure is not confused with an older one. Reporting moved ledger net YTD by $5,000, customer deposits, the 13-week low and cash-basis YTD, so the month's money figures are expected to move; each move needs its reason;
  - the books' seals: reporting's retainer fix changes how an August invoice posts (2400, not negative revenue). On the hosted copy the server holds August's seal, so Verify the Books will likely name a changed August posting. Check it on the QA workspace; if it does, it is recorded as an owner-approved correction with the reason, never re-sealed quietly.
- **From the items and Spanish lane (merged 2026-10-20, 8d9c1f7; items_test 68, spanish_test 109):**
  - the assistant drafting lines from notes, photos and takeoffs (§1.18 item 4);
  - income and expense accounts per item, so a line from the library carries its accounts into the books (today only "taxable" is on the form);
  - voice in the item picker (the request box keeps its own microphone);
  - the library's proposals in the owner's Approvals, with the counts lint (today they sit on the library's own card, so they can be missed);
  - automatic English beside a Spanish daily log or request, so the PM, the records and anything that reaches a client read English;
  - push notifications in Spanish (they go out in English);
  - offline assistant answers stay in English;
  - Jeanette has not reviewed the ~900 Spanish words; crews are not switched to Spanish until she has (safety words first). Decided 2026-10-20; Alan asks her (§5). Each word to carry a reviewed mark, so new field words show as not yet reviewed.
- **From the reports lane (merged 2026-10-20, 560057d; reports_test 450/450):**
  - Running (main session, week 4): one price book: close-out writes a cost factor per cost code to `DB.company.costBook`, and the item library keeps item costs in `DB.company.itemLib`. Fold the factor into the library's fill so estimating reads one place; today nothing reads the cost factor (BACKLOG §1.16);
  - Running (main session, week 4): the accounting choices are recorded with who, when and why but do not change the statements yet. Until they do, the card says so in plain words (a controller who picks "Capitalise" will expect the P&L to move);
  - the development-cost stake finds owned-property jobs by client name; key it on the Mercer & Bond flag the live jobs lane added;
  - the read-only accountant role (platform, §1.10 item 11);
  - QuickBooks comparison unchanged (the Three-Way Tie-Out);
  - "owed" in payables: decided 2026-10-20 (approved bills; awaiting approval on its own line); being built by the main session.
- **Gaps the build lanes found:**
  - Done 2026-10-20: a toast's Open link closes an open editor first and asks before dropping anything typed (Keep Editing is the blue step); toast_leave_test 18;
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
| 2026-10-20 | Tax credits on the client's proposal: show the "Net" after credits, or keep it internal | Internal until the tax-credit consultant confirms the church and rectory qualify and when the credits arrive; the client sees credits only as "subject to certification and your tax adviser" |
| 2026-10-20 | Hand over the real live-jobs file (`docs/LIVE_JOBS.md` from the Cowork handoff) for loading on the private platform | Invented demo jobs only |
| 2026-10-20 | The contractor designer: a contractor agreement as her PO, W-9 before the first payment, classification confirmed with the accountant | Bills with no PO, flagged; payments held until the W-9 is on file |
| 2026-10-20 | Ask Jeanette to review the ~900 Spanish words (decided with his "Go"; the asking is his). Recommended: one sheet for her (English, Spanish, where it appears, safety words marked), her sign-off recorded word by word | Crews stay in English until she has reviewed, safety words first |
| 2026-10-20 | Add a Google Maps key in Netlify for driver routes phase 2. Recommended: Routes API only, server-side, with a budget alert | The driver's list names the cheapest store per item (phase 1), no route |
| 2026-10-20 | The savings ledger: the shares for the wage, bonus and charity pools; who sees savings by person; bonus attribution | Every saving recorded; pools shown at 0% until he sets them; by person for the owner only; nothing attributed or paid without him |
| 2026-10-20 | Set the bank's dual control to match the Payment Run: the controller initiates, Alan approves in the bank's app | The ERP records who released each run; the bank itself does not enforce it yet |
| Later | Google sign-in consent screen (guided, about 5 minutes) | — |

## 6. Calls I made that Alan can change
- **Ranking:** overdue and today first, then the decision principles. Immediate safety and law always lead, and a missing insurance certificate counts as immediate.
- **Explanations:** a "this quarter" price explanation expires at the quarter's end.
- **Stock matching:** "5/8 sheetrock" with no type asks the procurement manager rather than guessing between Type X and moisture-resistant.
- **Phone home screen:** it hides the "because" lines to stay under 180 words; they show on Approvals and on desktop.
- **Quote rule:** "outside Manhattan and Brooklyn" means any other borough or out of state.

- **Mail nudges (2026-10-19):** a question from someone not on file (no vendor, client, staff or user with that address) becomes a nudge only when the mail names a job or money; "Lunch Friday? Are you free?" stays in the inbox. Alan can change this.
- **PM's phone bar (2026-10-18):** Home, Approvals, Projects, Tasks, Field, More.
- **New CO, Invoice or Estimate off a job's screen asks for the client** (it used to take the last job's).
- **A task saved with no owner goes to the job's PM** (or the design director on a design job), with who, when and why recorded; it can be switched off.
- **The owner's "Waiting on the Others" list** follows the one ranking order. Grouping it by person is proposed for the one-queue-per-person work.
- **Payment holds (subs lane, 2026-10-20):** the controller releases a hold under $2,500 (the same line as the Standard's three quotes); the owner above it, always with a logged reason. A bank-detail change cannot be released by a reason, the owner's included: only the call-back to the number on file, by someone other than the requester, clears it. A sub payment with no lien waiver no longer has "Release Without It": it needs the waiver recorded, or the owner's release with a reason. Whoever entered a bill or set up the vendor cannot release its payment.

- **Reporting (2026-10-20):** the accounting choices default to expensing Mercer & Bond development costs, percentage of completion for tax, and overhead shared by total direct cost, each labelled "confirm with your accountant"; group figures are consolidated at the subsidiary's cost (SD Plumbing and SD Electric markup to the firm eliminated); close-out starts at 85% of estimated cost, and a cost code off by 10% and $500 or more can be proposed to the price book, the owner approving each.
- **Item library (2026-10-20):** the owner or a PM approves or declines what the library proposes from use; a declined proposal never returns; a sent document never changes when the library does; the field sees items without prices.

- **Decided by Alan, 2026-10-20 ("Go"; reversible):** the controller prepares the weekly Payment Run and the owner releases it in one tap, billing the backup; "We Owe" is approved bills, equal to the books, with bills awaiting approval on their own line; crews stay in English until Jeanette has reviewed the Spanish.

## 7. Later (Alan deferred)
- NY rules (§7): "I need to better understand this."

## 8. Done recently
Full detail is in `docs/DECISIONS.md`.
- Reporting proven end to end (2026-10-20, pending the full net): every report recomputed from the records to the cent in a test, the ties on screen, drill to the bank line, manual journals flagged, P&L by project and client, cash basis, intercompany eliminated, line income to cost, close-out estimate against actual proposing price-book changes for the owner, overhead and break-even, the 13-week cash forecast as a report, Excel on every tab, Ask reading the reports. Eight money errors found and fixed at the root.
- The item library and Spanish for the field (2026-10-20): one library fills every typed line (estimate, CO, invoice, PO, RFQ, bill, request, receipt), learns from use with the owner or PM approving; the foreman, crew and driver read every screen in Spanish by their setting, chat lines translated on request.
- Subcontractors and the Payment Check (2026-10-20): subcontracts on the PO with scope, changes and retainage; pay applications against what the site measured; lien waivers per payment and per job; every vendor payment and Payment Run checked against contract, prior payments, receipt, work in place, retainage, credits, duplicates, papers and the bank call-back; holds in Approvals; the per-vendor, per-job ledger in Ask.
- Live jobs on invented demo jobs (2026-10-20): two payers on one contract, ranges, allowances and a paid exploratory phase, the tax credit budget, the contractor who becomes an employee.
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
