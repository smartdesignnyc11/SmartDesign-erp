# Decisions and requests: Alan's log

What Alan asked for or decided, with the date, where it lives, and its status. The chief of staff keeps this current: every new ask is logged the same hour, with the lane it went to. Newest first within each day.

Status: **Built** (merged and tested) · **Building** (a lane is on it) · **Spec** (written, not started) · **Waiting on Alan** · **Later** (deferred by Alan).

## Waiting on Alan
| Asked | Decision needed | Default until he decides |
|---|---|---|
| 2026-10-18 | AI spend caps inside the app, below the $50 Anthropic hard limit, so the app stops and says so before Anthropic refuses mid-task. | Firm $40 a month; $8 per person a month; the owner sees spend per person. |
| 2026-10-18 | Supabase plan before any real job, client or bank data goes in. The free plan pauses after a week unused and has no daily backups. | Free plan, invented demo data only. Move to Pro ($25 a month: daily backups, no pausing) before the first real record. |
| 2026-10-18 | Google sign-in for the hosted copy needs a Google OAuth client only he can create. | Email sign-in, invited people only; Google sign-in next session once the client exists. |
| 2026-10-11 | Leftover material from a cost-plus or reimbursable job: return it to the client, credit it on their invoice, or take it into firm stock? | Flagged "client-owned surplus, ask the PM"; never moved into firm stock automatically. |
| 2026-10-11 | Confirm with the accountant that out-of-state material purchases owe NY use tax, and at what rate. | Landed cost adds use tax at 8.875% (editable). A bill with no tax charged is flagged "use tax to accrue". |
| 2026-10-11 | ChatGPT history export, to deepen `docs/ALAN.md`. | Profile built from the build sessions and the Standard only. |
| 2026-10-10 | Re-authorise QuickBooks for the July-to-date pull. | Truth layer runs on bank and card lines and the QBO bridge snapshot. |

## 2026-10-18
| Ask or decision | Where it lives | Status |
|---|---|---|
| Set up the platform: new Supabase project (us-east-1), security in the database, the hosted copy, the AI connection with caps, a new clearly named Netlify site (the 12 old sites left alone), deploy, live check. Google sign-in, Plaid, watchers, the document reader and real data come later | BACKLOG §5, `docs/LANES.md` lane "platform", `platform/README.md` | Built, first slice: live at https://smartdesigns-erp.netlify.app; Alan invited as owner. Anthropic workspace ID set by Alan the same day; live checks all green (database and AI 27/27, two devices 17/17) |
| Overnight run: continue v11.1 and beyond without approvals until 10am (weekly usage 4%) | `docs/LANES.md`, `docs/PLAN.md` | Running |
| Version 11 published (v11.1 folded in): 32 of 32 suites green; scripted month 258/292 on time, $9,537 left behind | `docs/PLAN.md` | Built |
| Lean expert pilot (3 days, 9 roles) and both workshops run on v11 | `docs/pilot/pilot1/` | Done. Agent ledger 24/55 on time, $80,036 left behind; expert grades mostly 4–6; menu result in `docs/MENU_DRAFT.md` waiting on Alan |
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
| One assistant per person: four screens become one; Act Alone / Ask First / Hand It to Me; an activity log; better than Muse and dots | BACKLOG §1.27 | Spec |
| Role specialists: a standing auditor per role with the six-step finding handling | BACKLOG §1.28 | Spec |
| Cost intelligence: jobs spending more than they bring in, benchmarks per trade per unit, a receipt price book across stores, driver routes, a weekly process improvement | BACKLOG §1.29 | Spec |
| Savings ledger with wage, bonus and charity pools; the money line now includes charity | BACKLOG §1.30, `CLAUDE.md` | Spec |
| Firm chat additions: record cards, @assistant, a private DM with your own assistant | BACKLOG §1.21 | Spec |
| Proof: planted-problem banks per role, price-book and route tests, privacy tests | BACKLOG §1.31 | Spec |
| Warn before any heavy step; don't start a big round when weekly usage is above about 60% | `docs/PLAN.md` | Standing rule |

## 2026-10-11
| Ask or decision | Where it lives | Status |
|---|---|---|
| Each role's assistant reads that person's chats, to help with tasks, follow-ups and reminders | BACKLOG §1.24 item 4b | Spec (platform) |
| Ask must feel like this chat and work like Claude, across the ERP, Gmail, Drive, Calendar and internal chat | BACKLOG §1.24 | Spec (platform; needs the API key) |
| AI reviews every set (design, LPC, DOB, construction documents) for inconsistencies and flags them | BACKLOG §1.23 | Spec (with plans control) |
| Messages: subs, vendors and the architect join their job thread as guests (link or SMS/email bridge); import the WhatsApp group histories per job | BACKLOG §1.21 | Decided: yes to both |
| Plans control: correct plans always saved, everyone on the latest, the field told when plans are being revised; key project files in the chats | BACKLOG §1.22 | Spec (first after the pilot) |
| Messaging replaces WhatsApp and iMessage: messages become tasks, POs and files; threads hold the latest plans; the assistant helps act (the CO-from-chat example) | BACKLOG §1.21 | Spec |
| Ranking: crew waiting today outranks older overdue items; both stay visible. Order: immediate safety and law; then anyone blocked today (crew or field waiting); then overdue, today, this week; then the decision principle | `docs/PLAN.md` v11.1 | To build after the reset |
| Spanish is needed for the field | BACKLOG §1.20 | Spec (before go-live) |
| Estimates and invoices auto-populate items with descriptions | BACKLOG §1.18 | Spec (right after Simplify; shaped by the Documents Workshop) |
| Pilot runs leaner to save usage (Alan: "both"). Fewer daily roles: owner, PM, coordinator, foreman (phone), billing, controller and designer work every day (Alan swapped the client for the designer). Crew and driver join only on day 3. The client's approvals and payments are played by the world rules, and one short client read of the rendered documents keeps the client-view check, for one short work turn and the workshops. Shorter days: three slots (morning, work, end of day) with action caps 8, 14 and 8 | `docs/PLAN.md` | Agreed |
| Check document creation (estimates, invoices, progress billing, POs and the rest): easy on the go, quick, right in the back end, and how it looks to the client | BACKLOG §1.17 Documents Workshop | In the pilot |
| Pilot starts once the second wiring pass merges (v11's feature set), with release testing alongside | `docs/PLAN.md` | Agreed |
| Menu: think more and consult the role agents working the site before building; SmartDesign workspace only | `docs/MENU_DRAFT.md`, pilot menu workshop | Draft; decided after the workshop |
| The month simulation is the role experts themselves working 20 days in one shared company, together | BACKLOG §1.17 | Harness building; pilot after v11; full run after the reset |
| Organise the side menu | BACKLOG §1.15 | Spec (Simplify, right after v11) |
| Tasks are a very important feature: one task system | BACKLOG §1.14 | Spec (Simplify, right after v11) |
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
