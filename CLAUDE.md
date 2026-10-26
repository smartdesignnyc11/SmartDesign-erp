# SmartDesigns Projects ERP: standing instructions for Claude Code

Read this file, then HANDOFF.md, then docs/BACKLOG.md, before touching code.

**The plan** is `docs/PLAN.md`: everything promised, running, next, queued and waiting on Alan. Update it on every ask, lane report and merge. Nothing Alan asks for may exist only in chat.

**Alan's chief of staff** (`.claude/agents/chief-of-staff.md`) keeps `docs/DECISIONS.md` (every ask and decision, and what waits on him) and `docs/LANES.md` (who is building what, and the merge plan), working from `docs/ALAN.md` (how he thinks). Log every new ask there the same hour, and consult the chief of staff at each new ask, each lane report and before each merge or release.

## Who this is for
- **Owner:** Alan Mishali, founder of SmartDesign NYC / Mercer & Bond. The firm does design-build-develop work: landmark brownstone and townhouse renovation in Manhattan and Brooklyn, with SD Plumbing and SD Electric in-house.
- **What it is:** one ERP for every person in the firm (owner, PM, coordinator/procurement, foreman, crew, driver, designer, billing, controller) and for the firm's clients through a portal.
- **The goal:** each person runs their day from it and is 10x more productive. The firm stops needing NetSuite, QuickBooks, Procore, Buildertrend and a CRM.

## The ambition and how to think (Alan, 2026-10-11): this is how I work
**The ambition.** SmartDesigns Projects becomes, on its own, the best ERP and CRM for construction, design, and design-build firms. It must be better than NetSuite, QuickBooks, Salesforce, Procore and Buildertrend for this industry, because it is built for how this industry actually works. It gets there by being living and learning. It improves itself autonomously from everything that happens, and people approve every change that commits money, the firm, a client or the system itself.

**Alan's lens: apply it to every feature, fix and report before he has to ask.**
1. **End to end.** Does it work across the whole chain and every role it touches: prospect, estimate, contract, PO and RFQ, receiving, bill, bank, invoice and progress billing, job cost, reports? Prove it by doing it as each person would, not by checking one screen.
2. **On the go.** Is it fast and easy on a phone, one-handed, outdoors, interrupted? Does it fill itself in (items, descriptions, defaults from context), so nobody types what the system knows?
3. **The back end.** Does every record carry the accounting truth (job, client, entity, cost code, line links, accounts, tax, retainage)? Does it flow into the reports with the right number and tie to the bank?
4. **The client's eyes.** How does it look and read to the client: clear, premium, nothing that makes them call to ask?
5. **Money.** Where could money leak? Overpaying, not billing, paying more than before, buying what is in stock, waste. "Every dollar matters."
6. **Findable, one place.** Can the person find what they just made, and everything they owe, in one place? Saved is not enough.
7. **What the checks didn't check.** Why would our tests miss this? Fix the class and add the check that makes it fail loudly next time.
8. **The people who use it.** What would the role experts say after working with it? Ask them through the agent month and the workshops, and let real use decide, not guesses.
9. **Autonomy with approval.** What can the AI do on its own, and what needs a person? Is it delegated, logged and switchable?
10. **Learning.** Does it get better from what happens (lessons, price history, lead times, descriptions), with the owner approving changes to rules?
11. **Think past it.** What isn't he thinking about? How can it be better? What goes wrong if it isn't thought through?
12. **The bar.** Would a seasoned professional in that seat pick this over NetSuite, QuickBooks, Salesforce or Procore for this firm? If not, what closes the gap?

**This is how Claude thinks, not only how the ERP behaves (Alan, 2026-10-11).** Every session, every lane and the chief of staff reason with this lens about their own work: the plans, the estimates, the tests, the merges and what they tell Alan. Before saying something is done or estimating anything:
- Check it end to end, as the person, on the phone.
- Ask what the checks didn't check.
- Give the real number with what it rests on, not the hoped-for one.
- Say plainly what is built and tested, what isn't, and what you're unsure of.
- Raise what Alan would ask next, before he asks.

Lessons from this session's own misses:
- Calling the scripted month "the experts".
- Promising a pilot would cost half without measuring it.
- Letting parallel lanes each add a queue.
- Not checking that saved tasks were findable.

Each one was a failure to apply the lens to my own work.

**Speed with no bugs.** Expedite toward a platform the firm can use, without bugs. Fix by class, never by instance. Test as the person, on the phone. Measure, don't assume. Never ship a red test net.

## The mission (Alan, 2026-10-10): never forget this
SmartDesigns Projects is a living, breathing, evolving ERP that constantly wants to improve and help the company succeed at the highest level. Two things make it that, and they are the most important features in the system:
- **The brain.** It consumes all the data it can: every record, email, calendar, drive file, meeting transcript, bank line, field report and outcome. It learns what is working and what is not, analyses it, and turns that into changes that raise productivity and stop mistakes from recurring: new rules, process changes, reminders, lessons and, when a person approves, changes to the ERP itself and to each role's process.
- **The personal assistant, one per person.** Think of a frontier chat assistant fully customised to SmartDesign and to that person's role. It uses all the information in the company to help its user succeed at a very high level: it makes sure they never miss an opportunity or a deadline, helps them do their work, manages their day to day, and acts on their behalf (drafts, chases, schedules, files, proposes) with the ability to get things done. People approve what moves money, commits the firm or reaches a client.
- The experts who test every round are role experts from a design-build firm with in-house trades (construction, plumbing, electric, design, architecture, permitting and LPC, coordination with engineers and consultants), 20 years in their field and fluent in today's AI. Their definitions live in `.claude/agents/`. They judge the assistant and the brain as hard as they judge the screens.

## The SmartDesign Standard (Alan, 2026-10-11): every person, agent and assistant acts by it
`docs/STANDARD.md` is Alan's own document (original PDF in `docs/source/`): who we are, the seven values, the decision principles in priority order (safety, law/code/landmarks, integrity, quality, client experience, schedule, cost), the four tests, decide-or-escalate, the company standards, the escalation table, a playbook per role, and the rules for AI agents and assistants. It is the operating instructions for everything in the ERP that acts:
- The live, versioned copy is in the app (`DB.company.standard`, Settings › The SmartDesign Standard). Alan edits it; every edit records who, when and why and is hash-chained. Code loads it; never paraphrase or hard-code it.
- Every assistant gets the company sections plus the playbook of the role it supports, and the AI section. Every proposal, chase, catch and brain lesson names the value or standard behind it, ranks by the decision-principle order, and escalates in the standard format (what happened, impact on cost/schedule/quality, options, recommendation, decision deadline).
- Measurable standards (2-hour client acknowledgement, CO within 48 hours, three quotes over $2,500, invoice within 2 business days of a milestone, collections at due/7/15/30, three-way match, COI 30 days ahead, books by the 10th, and the rest) are checked by the ERP, not just written down.
- **Why money matters (Alan, 2026-10-11): remember this.** Money wasted is money that cannot go to employees' raises and bonuses, to more staff and resources, to charity, or to extra value for the client at no additional cost (charity added by Alan, 2026-10-17). Every leak the ERP catches says so in plain words.
- New AI features must do all of the above.

## How purchasing starts (Alan, 2026-10-11)
Most purchases and requests for quote begin from one or more line items on an estimate or invoice. This is a fact about how the firm works, not a target to measure. Build for it: the obvious way to buy or ask for quotes is from the line (single or multi-select, on the phone too), the record carries the link to its line from the start, and blank starts stay available but secondary.

## The north star (Alan, 2026-10-08): weigh every change against this
A custom, tailored ERP for SmartDesign, built for the future. It uses AI to raise each employee's output and to make sure nothing is forgotten:
- **Nothing slips.** No forgotten task, follow-up, reminder or promise. Agents in the ERP originate, chase and remind; people approve.
- **Real-time truth with no manual entries.** Reporting ties straight to the transactions and expenses that hit the bank accounts and credit cards. All truth is in the ERP, and every record links end to end: prospect › client › estimate › invoice line, and PO › bill › bank/card transaction › line item.
- **Money leaks are caught automatically:**
  - overspending against budget, PO or estimate line;
  - work done but not billed;
  - purchases made on a client's behalf that were not billed back;
  - returns and refunds that were never credited or matched;
  - overhead analysed and reported automatically.
- **It learns.** It learns from emails and transcripts, keeps a memory, and turns lessons into process changes, so the same mistake does not happen twice.
- **Financial truth (Alan, 2026-10-10).** The ERP's financials are the single most valuable source of truth for income and expenses, so:
  - every income and expense figure is linked directly to the bank and credit-card accounts; a figure with no bank or card line behind it is not truth and is shown as such;
  - manual journal entries are always flagged, everywhere they appear (ledger, statements, Pack, drill-downs, Ask), with who, when and why;
  - nothing posted can be changed or manipulated silently: posted money records are append-only, a change is a linked reversal and re-post with a reason, and the audit trail is tamper-evident;
  - every transaction is matched to a line item: cost to a bill or PO line and its estimate line, income to an invoice line; an unmatched transaction is a flag, never a silent cost;
  - QuickBooks is a bridge for comparison and import, never the truth; the ERP shows where QuickBooks, the bank and the ERP disagree.

## The bar
Four expert lenses grade every round against the field leaders:
- **Founder:** an AI-native ERP founder, judged against NetSuite, Procore, Buildertrend, HubSpot and Copilot-style assistants.
- **UX:** a senior product designer, judged on flow, the next step and ease of input.
- **Finance:** a construction CFO/controller, judged against NetSuite and QuickBooks Enterprise.
- **Ops:** a PM / client-services lead, judged against Procore and Buildertrend.

The target is **9/10 or higher in every lens**: a seasoned professional would pick this over the leader for this firm, with no severity-1 or severity-2 finding left. The last grades (round 4) were founder 7.5, UX 7.5, finance 7.5, ops 8. docs/BACKLOG.md is the contract.

## The owner's standards (non-negotiable)
- **Ownership.** Research how the leaders do it (NetSuite first, then QuickBooks Enterprise, Procore, Buildertrend, Salesforce/HubSpot, Copper). Adapt it to this firm and beat it; never copy one-for-one.
- **Review by doing.** Perform the workflow as the person (create an estimate, invoice, PO, CO, daily log…), one module at a time. Flow, button placement, the obvious next step and ease of input matter more than feature lists.
- **NetSuite's differentiator, app-wide.** Anything in the system can be queried and reported on: every entity in `erpQuery` (EQ_TABLES), in ⌘K search and in the Report Builder.
- **Labels.** Title Case on labels, tabs, buttons and headings ONLY. Never on record values, units, names from data, or sentences. Connecting words stay lowercase ("Send to Client"). "New X" creates a record; "Add" is for a child line. "Accounting", never "Money".
- **Visuals.** Line-drawn SVG icons only: no emoji, no glyph characters standing in for icons (› → ✓ ▾).
- **One blue primary button per screen,** and it is always the safe next step. Housekeeping is never blue.
- **One question, one number.** The same label shows the same count everywhere (rail badge, tab badge, tile, header line, Ask). A tile's count equals the rows its filter shows. One noun has one list.
- **Phone (390px):** never scrolls sideways; tap targets at least 8px apart; the foreman's screens are one job, big targets, plain words.
- **Toasts.** Every mutation toasts what happened, with an Open link to the record. A page heading matches its nav entry.
- **One clock.** The app's day is `today()`, pinned to 2026-09-03 in the demo. Never stamp a record with the wall clock: use `appNow()` / `appNowIso()` / `stampText()`.
- **AI assists, people commit.** The assistant may read, extract, match, flag and propose. Writes become proposals with a button. People approve, pay, send, close and certify.
- **House voice:** plain, specific, no exclamation marks.
- **Communication with Alan.** He is terse and decisive and wants concrete recommendations, not option lists. Warn him before anything that will use a lot of usage.
- **Think past the ask (Alan, 2026-10-11).** Every time Alan adds a task, before building it, ask and answer three questions, and put the answers into the spec and into the reply:
  - What is he not thinking about?
  - How can this be made better?
  - What could go wrong if this isn't thought through: for data, money, tax, fraud, people, the field, the phone and the books?
  Fold the good answers into the build; bring the ones that need his call to him as a recommendation.

## Architecture
- **Build.** One self-contained HTML file. `python3 build.py` assembles `src/head.html` + `src/styles.css` + `src/body.html` + `src/app.js` into `dist/smartdesigns_projects.html`, and runs `node --check` first.
- **`src/app.js` (~159k lines).** Recovered from the last published build (round 4) and pretty-printed. It is the true current code, but its comments and section markers were stripped by the minifier. For the intent behind older code, read `legacy/commented-source-v96/app.js`: the September 15 source, fully commented, with sections marked `/*<<name.js>>*/`.
- **The override pattern.** Every feature after the core was appended as a section that wraps existing functions: `const base = fn; fn = function(){ … base.apply(this, arguments) … }`. Later sections are outer wrappers. Many functions (render, paAsk, jobFin, companyPL, toast, save, docAction…) are wrapped 5–15 times, so before changing behaviour, grep for every reassignment of that function and understand the chain.
  - Prefer fixing the root definition, and fold redundant wrappers into one clear function when you touch an area. Reducing the layering is part of the job.
  - Call tables and functions through, never hold old references: `EQ_TABLES` entries are thunks.
- **Data.** A global `DB` (clients, projects with schedule/tasks/decisions/files, estimates, invoices, COs, POs, bills, payments, transactions, periods, budgetPlan, photos refs, …), persisted to IndexedDB through `save()` / `saveNow()`. Photos are blobs in IndexedDB `sd_photos`. Demo data seeds on first boot.
- **Identity.** `signIn('u_owner'|'u_alan'(pm)|'u_chen'(coord)|'u_angel'(foreman)|'u_alberto'(crew)|'u_alex'(driver)|'u_klein'(client)|'u_sarah'(designer)|'u_billing'|'u_controller')`, then `render()`. Navigation is `view='<id>'; render()`. `IA_GROUPS` holds the nav groups and `ROLE_VIEWS[role]` the views each role may open.
- **The hosted copy (Netlify + Supabase)** adds sign-in, sync (`public/cloud.js`), `/api/ai` (Anthropic proxy, model pinned server-side), Google OAuth per user, mail/calendar watchers and Plaid. The latest hosted code was lost (see HANDOFF.md). `legacy/hosted-app-2026-09-15.zip` is the last surviving copy; rebuild the later pieces from the specs in HANDOFF.md.

docs/ARCHITECTURE.md has the module map and the line numbers of the key functions.

## How we work: the process rules (Alan, 10-26)
`docs/PROCESS.md` holds the rules and why each exists. Read it before planning any lane, test or pilot, and add to its retro log after every iteration. In short:
- evidence is a person doing the work through the screens, from a blank start, on both devices;
- no lane without a failing journey step (`docs/JOURNEYS.md`, `tests/cycle_walk.py`);
- finish the core before adding;
- test the instrument with one turn before paying for the run;
- never run the same thing twice on the same build;
- one or two lanes that never share files, each running the screen walk, the net and the month walk before handing back;
- progress is N of 10 journeys per device.

## How to work
1. **Reproduce first.** Write a Playwright check that fails the way the reviewer saw it, then fix it, then prove the fix on the neighbouring screens with the same pattern. A fix is a class fix.
2. **Run the tests.** `python3 build.py && cd tests && python3 smoke_test.py && python3 baseline_test.py`, plus the suites you add, and `tests/slot.sh python3 cycle_walk.py` (the ten journeys through the screens) before any merge that touches sales, estimates, purchasing, billing or Today. Suites open `../dist/smartdesigns_projects.html` through `tests/harness.py`; never hardcode paths. The machine running tests may be slow, so run suites one at a time.
3. **Keep the guard rails, and rebuild the lost ones early (see BACKLOG.md "Rebuild the test net"):**
   - the screen-standard lint;
   - the counts lint, where every label shows one number and a tile equals its rows;
   - the Ask question bank;
   - the day walk;
   - the finance cross-check.
4. **Work in loops.** Fix a backlog slice, re-run the four lenses' walks (docs/REVIEW_PROTOCOL.md), score honestly, repeat. Use subagents for independent slices and for independent reviewers. Reviewers never review their own work.
5. **Design gate (2026-10-11).** Before building, name the noun, list and queue registry entries the change extends (BACKLOG §1.16). A new store, list, queue or menu item for something that already exists needs a reason in the spec, or it gets folded in. The structure lint enforces this.
6. **Commit small and often,** with messages that say what was wrong and why the change fixes it.

## Privacy
- Real mailbox, meeting-transcript and bank content never goes into seeds, tests, docs or commits. Demo data is invented.
- Never commit credentials, tokens or account numbers (last 4 digits at most).
