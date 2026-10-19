# Decisions and requests: Alan's log

What Alan asked for or decided, with the date, where it lives, and its status. The chief of staff keeps this current: every new ask is logged the same hour, with the lane it went to. Newest first within each day.

Status: **Built** (merged and tested) · **Building** (a lane is on it) · **Spec** (written, not started) · **Waiting on Alan** · **Later** (deferred by Alan).

## Waiting on Alan
| Asked | Decision needed | Default until he decides |
|---|---|---|
| 2026-10-19 | Should the owner's Brain read everyone's mail (BACKLOG §5 item 8), or does mail stay private to each person? | Private to each person, the owner included |
| 2026-10-18 | AI spend caps inside the app, below the $50 Anthropic hard limit, so the app stops and says so before Anthropic refuses mid-task. | Firm $40 a month; $8 per person a month; the owner sees spend per person. |
| 2026-10-11 | Leftover material from a cost-plus or reimbursable job: return it to the client, credit it on their invoice, or take it into firm stock? | Flagged "client-owned surplus, ask the PM"; never moved into firm stock automatically. |
| 2026-10-11 | Confirm with the accountant that out-of-state material purchases owe NY use tax, and at what rate. | Landed cost adds use tax at 8.875% (editable). A bill with no tax charged is flagged "use tax to accrue". |
| 2026-10-11 | ChatGPT history export, to deepen `docs/ALAN.md`. | Profile built from the build sessions and the Standard only. |
| 2026-10-10 | Re-authorise QuickBooks for the July-to-date pull. | Truth layer runs on bank and card lines and the QBO bridge snapshot. |

The overnight run of 2026-10-19 builds on the defaults above and does not decide them. The menu and navigation questions from `docs/MENU_DRAFT.md` were waiting on Alan; they were decided overnight under his instruction (below) and are no longer waiting.

## 2026-10-19
| Ask or decision | Where it lives | Status |
|---|---|---|
| Alan, going to sleep: "Focus on all the updates we had waiting - AI's, brain, chat, user interface/user experience, etc. Do not wait for my approvals and go ahead." Five lanes: menu, today, assistant, messages, and platform (main session) | `docs/LANES.md` "Overnight 2026-10-19", BACKLOG §1.11, §1.14, §1.15, §1.21, §1.24, §1.27, §5 | All four lanes merged to master; see LANES "How the merge went" |
| The menu and navigation calls below, made on Alan's behalf overnight | `docs/MENU_DRAFT.md`, BACKLOG §1.15 | Decided overnight under his instruction; reversible; built and merged |
| Alan: "Where's the chat? I don't see it anywhere." | Chat button in the header beside Ask for every office role, unread count on it; the controller given Chat | Done (be81b5a..), live with tonight's deploy |
| Alan: "Ask must work and operate like Dot by ChatGPT. It's a personal assistant, not just a bot that answers questions. It needs to think and act like a Fortune 500 executive assistant, an assistant project manager." | BACKLOG §1.27, §1.24; plan in PLAN.md | Alan: "Go" (2026-10-19). Lane "executive assistant" building the page side; the server's runs for each person built by the main session (not live until the lane merges); caps by role to be raised at deploy (owner $40, PM $25, others $15, firm $150) |
| Alan: "the ai assistant chat needs to feel like our chat on here and or Dot by chatgpt" | Sent to the executive assistant lane as a first-order requirement: the conversation is the page, answers as full-width rich text streaming in, composer pinned at the bottom with attach, mic and send/stop, copy and retry under answers, history panel, no clutter, the day's briefing as the first message | Building (lane executive assistant) |
| Alan: "The messages should not be robotic... analyze the information, decide if it needs to look for more info in another place like the drive, email, calendar, erp... go into every line in the estimates, invoices, vendor quotes, rfq's, expenses, AR, AP... get smarter with every new piece of information... learn the role and person... double check their work" | New lane "assistant mind": line-level reach for every record, multi-source search (ERP, mail thread, Drive, calendar), analysis and recommendation in a genuine voice, a verification pass on every figure it cites, a person model and learning with rules approved by the owner, mind_eval (40+ hard questions) | Building |
| Alan: "we lost 3 hours... we could have been working all that time" | The screens lane stopped after one commit three hours earlier and the main session did not notice (it waited for a completion notice); an interrupt then stopped speed and messages 2. Fix: all three relaunched from what they had saved; every lane commits after each step; a lane watcher reports commits and any lane quiet for 40 minutes, every 10 minutes | Done |
| Alan: "Are you being efficient by only running 1 task?" | Two more lanes in parallel with the executive assistant: speed and messages phase 2, chosen to stay out of each other's code. Client portal held for his explicit go (security) | Building |
| Merge calls made overnight (main session): (1) the core checks and each lane's suite after each merge, the full net once at the end, instead of four full nets; (2) The Brain stays in the menu under Company and the Chief of Staff in More; both open the one assistant on their tab, and the page heading reads as the entry; (3) Approvals, Inbox and Tasks stay as full-list pages in the menu as well as filters of Today, with the same counts; (4) the owner's assistant rules for another person travel on the firm's delegation log and apply on that person's device, later choice wins | `docs/LANES.md`, `tests/menu_test.py`, `tests/shared_system_test.py` | Done; each reversible |

### Calls made on Alan's behalf overnight (reversible)
Under his instruction of 2026-10-19 not to wait for approvals, every bracketed recommendation in `docs/MENU_DRAFT.md` is adopted. Each can be reversed in the morning; the menu test pins whatever he settles on.

The eight disagreements from the workshop:
1. Change orders live in the job's Money tab. Billing shows "approved, not billed" from the same list.
2. One Today page. Approvals, Inbox and Tasks become filters of it; the bill sheet stays as the detail.
3. Billing and the controller start on Billing and Banking, not Today.
4. The field phone bars are the experts': foreman Today, Site, Daily Log, Requests, Crew; crew Clock, Requests, Schedule, Photos, Chat; driver Route (Requests folded in), Chat, Clock, Receipts.
5. No separate Deposits page. The Payments tab shows the bank lines.
6. Drawings: one register per job; a top item for the designer; a view under Site for the foreman.
7. Permits: one list per job; Design shows them across jobs.
8. Names: Design, Purchasing, Company; Today for every office role; Clock stays Clock.

The six open questions:
1. Ask becomes a button on every screen, not a menu item.
2. One directory for clients, contacts and companies.
3. Billing sits under Accounting for the owner and controller and is a top item for the billing role.
4. PMs get Sales only if they estimate. The default is no.
5. "Office" is renamed "Company".
6. Estimates live in Sales for new jobs, and in the job's Money tab for change orders.

This supersedes call (1) of 2026-10-18 (the PM's phone bar Home, Approvals, Projects, Tasks, Field, More). Under the adopted menu that bar becomes Today, Projects, Clients, Purchasing and More, with Approvals and Tasks as filters of Today. The menu lane settles the exact bar and says so in its report.
| Server-held seals of the books (BACKLOG §5 item 2: "the hash chain's head per period stored server-side"). Built stronger than asked: SHA-256 recomputed from the server's own books, add-only, beside the app's FNV head | `platform/README.md` | Built; unit 13, live 66/66 |
| Document reader (BACKLOG §5 item 5), rebuilt: text PDFs and Word free, scans and photos by the small model within the caps; spreadsheets and HEIC get a note (the common Excel reader has unfixed advisories for untrusted files) | `platform/README.md` | Built; unit 14/14, live PDF and receipt photo read |
| Keep going without waiting (Alan): watcher nudges into the assistant; invites and Sign Out Everywhere for a lost phone (sessions ended at once, the phone erases its copy) | `platform/README.md` | Built; live 60/60 and 28/28 |
| Is it safe that the ERP reads his mail and Drive? Recommended and built: the watcher's key reads only; push notifications for what matters. Advised: 2-Step Verification on both Google accounts, sign in with Google | `platform/README.md` | Built; live 49/49. Real push on his phone not yet seen (headless browsers refuse notifications) |
| Merge Alan's two sign-ins and build the watcher | `platform/README.md` | Built: one private store for both addresses (server-set); google-connect seals the long-lived key, assistant-watch every 15 minutes on weekdays 7am to 7pm New York fills each person's private inbox, the app files it on opening. Live 43/43 and 25/25; unit 66; inbox filing 11/11. Alan turns it on in Connections; real-Google run not yet seen |
| Email syncing, step 1: each person's mail, Google Calendar, Drive files, connection and assistant in private rows only that sign-in reads (the owner included); device settings no longer sync. Firm client ID set in the app | `platform/README.md` | Built; live 37/37 and 25/25. Alan connected his Google the same day (40 mails, 55 events, 500 files, private); the watcher is next |
| Google sign-in: Alan made the OAuth client; Sign In with Google is on, invited addresses only | `platform/README.md` | Built; consent screen renamed to SmartDesigns Projects. Alan signed in by email link and the first upload filled the firm workspace (84 collections, demo data); a Google round trip still to try |

## 2026-10-18
| Ask or decision | Where it lives | Status |
|---|---|---|
| Set up the platform: new Supabase project (us-east-1), security in the database, the hosted copy, the AI connection with caps, a new clearly named Netlify site (the 12 old sites left alone), deploy, live check. Google sign-in, Plaid, watchers, the document reader and real data come later | BACKLOG §5, `docs/LANES.md` lane "platform", `platform/README.md` | Built, first slice: live at https://smartdesigns-erp.netlify.app; Alan invited as owner. Anthropic workspace ID set by Alan the same day; live checks all green (database and AI 27/27, two devices 17/17) |
| Supabase moved to Pro by Alan (daily backups, no pausing); confirmed through the API, first backup on record | `platform/README.md` | Built |
| Overnight run: continue v11.1 and beyond without approvals until 10am (weekly usage 4%) | `docs/LANES.md`, `docs/PLAN.md` | Running |
| Version 11 published (v11.1 folded in): 32 of 32 suites green; scripted month 258/292 on time, $9,537 left behind | `docs/PLAN.md` | Built |
| Lean expert pilot (3 days, 9 roles) and both workshops run on v11 | `docs/pilot/pilot1/` | Done. Agent ledger 24/55 on time, $80,036 left behind; expert grades mostly 4–6; menu result in `docs/MENU_DRAFT.md` was waiting on Alan; decided overnight on 2026-10-19 under his instruction (see that day) |
| Plans control phase 1 (register, VOID, acknowledgments, holds, order flag, filed-sheet amendment) | BACKLOG §1.22 | Built (29effe9) |
| Pilot fixes batch 1 (19 items: daily log, controller POs, money matches, CO/estimate entry, Ask words…) | `tests/pilot_fixes_test.py` | Built (2ff680c) |
| Call Alan can change: an escalated site question still waits on whoever it was addressed to, and the owner is informed (it used to move to the owner) | pilotfix1 item 19 | Built; Alan can change |
| Call Alan can change: vendor order follow-ups stay on by default for the coordinator (as decided 10-11), with a first-day notice and an activity log to come in the one-assistant work | BACKLOG §1.27 | Spec |
| Calls made overnight that Alan can change: (1) the PM's phone bar is Home, Approvals, Projects, Tasks, Field, More; (2) New Change Order, Invoice or Estimate started off a job's screen asks for the client instead of using the last job's; (3) a task saved with no owner goes to the job's PM, recorded who, when and why, and switchable; (4) the owner's "Waiting on the Others" list follows the one ranking order (32 rows; grouping by person is proposed for the one-queue-per-person work) | `docs/PLAN.md` §6 | Built; Alan can change |
| Cross-set consistency check, demo phase (plans across sets disagree: a shared room held, the RFI opened where the role can see it) | BACKLOG §1.23, `tests/xset_test.py` | Built (3683251); the check does not run at boot yet; rework avoided is an estimate; the platform phase needs real drawing reading |
| Pilot fixes batch 2 (hours, mail digest, money matching and Reverse Payment, agency mail, driver, card accounts) | `tests/pilot_fixes2_test.py` | Built (8a2f952). Call Alan can change: Reverse Payment is limited to Billing and the Controller |
| Find it again after every save; truthful pay app %; outbox recipients | `tests/findable2_test.py` | Built. Call Alan can change: a pay app line never bills below what was already billed; where the evidence measures less, the line says so and the PM decides |
| Call Alan can change: every mailed vendor bill goes to the Controller, PO or not, whatever mailbox it landed in (three-way match is the office playbook; Bills & Payroll is the Controller's). Track's Enter the Bill moved from Billing to the Controller too | lane netfix, `tests/learn_test.py` | Built; Alan can change |
| Version 11.2 published: lanes xset, pilotfix2, findable2, netfix, monthfix; full net 37/37; month identical to v11 | `docs/PLAN.md` | Built (379182f) |
| Make sure the brain gets everything from the Oct 15 team meeting transcript and takes the right learning action, judged to the highest AI standard | BACKLOG §1.33, `tests/meeting_brain_test.py` | Notes reader built and tested (27 checks); the transcript reader is Spec (platform, Claude). The real meeting was run privately; its content stays out of the repo |

## 2026-10-17 (from the Cowork session, folded in on 2026-10-18)
| Ask or decision | Where it lives | Status |
|---|---|---|
| Live jobs: two payers per contract; range estimates with allowances and a paid exploratory phase; the HTC calculator and hard/soft/contingency model; one estimating test job | BACKLOG §1.25 | Spec. Real details stay out of the repo and load on the private platform |
| The senior designer as a contractor user who can later be converted to an employee | BACKLOG §1.26 | Spec |
| One assistant per person: four screens become one; Act Alone / Ask First / Hand It to Me; an activity log; better than Muse and dots | BACKLOG §1.27 | Building (lane assistant, 2026-10-19) |
| Role specialists: a standing auditor per role with the six-step finding handling | BACKLOG §1.28 | Spec |
| Cost intelligence: jobs spending more than they bring in, benchmarks per trade per unit, a receipt price book across stores, driver routes, a weekly process improvement | BACKLOG §1.29 | Spec |
| Savings ledger with wage, bonus and charity pools; the money line now includes charity | BACKLOG §1.30, `CLAUDE.md` | Spec |
| Firm chat additions: record cards, @assistant, a private DM with your own assistant | BACKLOG §1.21 | Building, phase 1 (lane messages, 2026-10-19) |
| Proof: planted-problem banks per role, price-book and route tests, privacy tests | BACKLOG §1.31 | Spec |
| Warn before any heavy step; don't start a big round when weekly usage is above about 60% | `docs/PLAN.md` | Standing rule |

## 2026-10-11
| Ask or decision | Where it lives | Status |
|---|---|---|
| Each role's assistant reads that person's chats, to help with tasks, follow-ups and reminders | BACKLOG §1.24 item 4b | Spec (platform) |
| Ask must feel like this chat and work like Claude, across the ERP, Gmail, Drive, Calendar and internal chat | BACKLOG §1.24 | Building, page side (lane assistant) and streaming (platform), 2026-10-19 |
| AI reviews every set (design, LPC, DOB, construction documents) for inconsistencies and flags them | BACKLOG §1.23 | Spec (with plans control) |
| Messages: subs, vendors and the architect join their job thread as guests (link or SMS/email bridge); import the WhatsApp group histories per job | BACKLOG §1.21 | Decided: yes to both |
| Plans control: correct plans always saved, everyone on the latest, the field told when plans are being revised; key project files in the chats | BACKLOG §1.22 | Spec (first after the pilot) |
| Messaging replaces WhatsApp and iMessage: messages become tasks, POs and files; threads hold the latest plans; the assistant helps act (the CO-from-chat example) | BACKLOG §1.21 | Building, phase 1 (lane messages, 2026-10-19) |
| Ranking: crew waiting today outranks older overdue items; both stay visible. Order: immediate safety and law; then anyone blocked today (crew or field waiting); then overdue, today, this week; then the decision principle | `docs/PLAN.md` v11.1 | To build after the reset |
| Spanish is needed for the field | BACKLOG §1.20 | Spec (before go-live) |
| Estimates and invoices auto-populate items with descriptions | BACKLOG §1.18 | Spec (right after Simplify; shaped by the Documents Workshop) |
| Pilot runs leaner to save usage (Alan: "both"). Fewer daily roles: owner, PM, coordinator, foreman (phone), billing, controller and designer work every day (Alan swapped the client for the designer). Crew and driver join only on day 3. The client's approvals and payments are played by the world rules, and one short client read of the rendered documents keeps the client-view check, for one short work turn and the workshops. Shorter days: three slots (morning, work, end of day) with action caps 8, 14 and 8 | `docs/PLAN.md` | Agreed |
| Check document creation (estimates, invoices, progress billing, POs and the rest): easy on the go, quick, right in the back end, and how it looks to the client | BACKLOG §1.17 Documents Workshop | In the pilot |
| Pilot starts once the second wiring pass merges (v11's feature set), with release testing alongside | `docs/PLAN.md` | Agreed |
| Menu: think more and consult the role agents working the site before building; SmartDesign workspace only | `docs/MENU_DRAFT.md`, pilot menu workshop | Workshop done 2026-10-18; decided overnight 2026-10-19 under Alan's instruction (reversible); Building |
| The month simulation is the role experts themselves working 20 days in one shared company, together | BACKLOG §1.17 | Harness building; pilot after v11; full run after the reset |
| Organise the side menu | BACKLOG §1.15 | Building (lane menu, 2026-10-19) |
| Tasks are a very important feature: one task system | BACKLOG §1.14 | Building (lane today, 2026-10-19) |
| Reporting proven end to end: income, expenses, job costing, line-item income to cost, P&L by company, client and project, overhead analysis | BACKLOG §1.13 | Spec (after simplify and subs) |
| Vendors never overpaid: every payment checked against the vendor's estimate or contract, prior payments, receipts, work done, retainage, deposits and credits | BACKLOG §1.12 | Spec (with subs and lien waivers) |
| Order after v11: review, simplify, subs and payments, reporting, platform, full regrade | `docs/LANES.md` | Agreed |
| Real agents on the Claude API: approved, with a spending limit; Alan wants me to do the setup | BACKLOG §5.8 | Waiting on Alan for the three sign-ups and tokens; I do everything else |
| A chief of staff that thinks like Alan, tracks the changes and manages the agents | `.claude/agents/chief-of-staff.md`, `docs/ALAN.md`, this file, `docs/LANES.md` | Built (docs) |
| Invoices and receipts attach straight to the PO, the bill or both; the AI checks every figure lines up; open mismatch blocks payment | BACKLOG §1.9 item 8 | Built in lane; merging |
| Version 11 should be the strongest update yet | Merge plan in `docs/LANES.md` | Building |
| Tracking numbers, invoices, receipts, delivery dates and vendor promises filed in place; vendor follow-ups sent autonomously (within delegation) | BACKLOG §1.9 | Built in lane; merging |
| Think past every ask: what's missed, how to make it better, what could go wrong | `CLAUDE.md` | Built (standing rule) |
| Check inventory before buying; only the driver or procurement manager overrides, with a reason | BACKLOG §1.8 item 12 | Building (lane "stock") |
| Owner approves price-watch explanations and baseline changes ("lumber up 8%") | BACKLOG §1.8 item 11 | Built in lane; merging |
| Price watch: flag purchases above past prices and anything abnormal | BACKLOG §1.8 item 11 | Built in lane; merging |
| "75% start from a line item" is context, not a benchmark. Build line-first defaults; no metric | `CLAUDE.md` "How purchasing starts" | Building (lanes "rfq", "chain") |
| Create an RFQ from one or several line items | BACKLOG §1.8 | Building (lane "rfq") |
| PO lines link to estimate, CO or invoice lines, both ways | lane "chain" | Building |
| Sourcing research: the AI reasons where it is cheaper, searches, and makes the case | BACKLOG §1.8 item 10 | Building (demo); live web search waits on the platform |
| AI-run RFQ: plans → foreman → purchasing → vendors → quotes read → leveling → negotiation draft → approval → award | BACKLOG §1.8 | Done in lane, awaiting merge |
| Look for vendors outside Manhattan and Brooklyn, and out of state | `docs/STANDARD.md` Procurement | Built (Standard); app side Building |
| Ask "direct to the source or a middleman?" on every purchase | `docs/STANDARD.md` Procurement | Built (Standard); app side Building |
| The SmartDesign Standard is the operating instructions for every agent, assistant and the brain; wasted money hurts raises, bonuses, staff and client value | `docs/STANDARD.md`, `CLAUDE.md` | Built (docs); app side Building (lane "charter") |
| Hosting: Supabase plus Netlify | BACKLOG §5 | Later (starts after the 2026-10-15 weekly reset) |
| The phone is tested on the go, in field conditions | `docs/REVIEW_PROTOCOL.md`, `.claude/agents/_PROTOCOL.md` | Built |
| Overhead recorded properly; true project profitability net of overhead | lane "chain" | Building |
| Full chain test: estimate → invoice → PO → progress billing → matching → reports | lane "chain" | Building |
| Every click does the right thing and goes to the right page | lane "crawl" | Building |
| Everything saves to the right place | `tests/month_sim.py` PERSIST check | Built |
| Fixes before grading again | BACKLOG §8 | Building |

## 2026-10-10 and earlier
| Ask or decision | Where it lives | Status |
|---|---|---|
| Month-long simulation of the company, not a scripted walk | `tests/month_sim.py` | Built |
| Financial truth: bank and card linked, journals flagged, append-only, every transaction matched to a line, QuickBooks only a bridge | `CLAUDE.md`, BACKLOG §1.6 | Built (truth layer); QuickBooks pull waiting on re-auth |
| The mission: the brain and a personal assistant per person | `CLAUDE.md` | Building across lanes |
| Role-expert agents (20 years, AI-fluent) test end to end with mail, calendar and drive linked | `.claude/agents/` | Built |
| Use Alan's Gmail, Calendar and Drive for testing only | `docs/BACKLOG.md` §1.7, workspace kept outside the repo | Built |
| NY rules (§7) | BACKLOG §7 | Later ("I need to better understand this") |
| Clean up the site: messy and overwhelming on the iPhone | BACKLOG §3, Today redesign | Built (round 5); regrade pending |
| North star: nothing slips, real-time truth, leaks caught, learns | `CLAUDE.md` | Standing |
