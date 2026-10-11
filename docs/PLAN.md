# The plan: everything we said we'd do

This is the one list. The chief of staff keeps it current on every ask, lane report and merge. Details live in the BACKLOG sections named. Status words: **Running** · **Next** · **Queued** · **Waiting on Alan** · **Later** (deferred by Alan) · **Done**.

Last updated 2026-10-11.

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

## 3. After version 11, in the agreed order
| # | What | Where |
|---|---|---|
| 1 | Focused expert review (controller, procurement manager, foreman on the phone, design expert); fixes the same day | REVIEW_PROTOCOL plus the system lens |
| 2 | Agent-month pilot, lean (Alan, 2026-10-11): 3 working days. Seven roles work daily; designer, crew and driver join on day 3. Three slots a day with smaller action caps, with the Documents Workshop (estimates, COs, invoices, progress billing, POs, RFQs and bills: on the go, speed, back end, client view) and ending with the Navigation and Pages Workshop (each expert proposes their menu from what they actually used; `docs/MENU_DRAFT.md`) | §1.17 |
| 3 | **Simplify:** organised side menu (SmartDesign only, after Alan agrees the plan); one task system; one queue per person; an alert budget; role navigation; one timeline per request; one way to do each thing; the structure lint and completeness tests that stop the next tasks-type problem | §1.15, §1.14, §1.11 (items 1–4, 9), §1.16 |
| 4 | Subcontractors: bid leveling by scope, COI before start, pay applications, retainage, **lien waivers with every payment**, backcharges; **payment check** so vendors are never overpaid | §1.10 item 1, §1.12 |
| 5 | **Reporting proven**: income and expenses (accrual and cash), job costing, line-item income to cost, P&L by company, entity, client and project, overhead analysis, WIP, cash flow, aging, closed periods frozen, QuickBooks comparison | §1.13 |
| 6 | **Platform and the real agents** (Supabase plus Netlify): sign-in, shared database, row-level security, AI proxy with cost caps, live assistants, documents, procurement, the brain, schedule, billing, compliance and books agents, each with a shadow week first | §5, §5.8 |
| 7 | Full agent month: 20 working days in two halves, after the weekly reset | §1.17 |
| 8 | Full ten-expert regrade (target 9+ in every lens, no severity-1 or severity-2 findings) | REVIEW_PROTOCOL |

## 4. Queued (built after the above, or folded in where they fit)
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
- **Gaps the build lanes found:**
  - client portal: pay online, or "we paid";
  - the foreman can only measure today's tasks;
  - sub POs default to SD Plumbing;
  - a mailed bill's PDF is not attached to the bill.
- **From the scripted month:**
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
| 2026-10-11 | Three sign-ups: Anthropic API ($50/month cap), Supabase, Netlify. Keys go in the environment settings as ANTHROPIC_API_KEY, SUPABASE_ACCESS_TOKEN and NETLIFY_AUTH_TOKEN, then start a new session with "set up the platform" | Platform waits; everything else continues |
| 2026-10-11 | Which email address the vendor follow-ups come from (recommend purchasing@ on the firm's domain) | Outbox only (demo) |
| 2026-10-11 | Spanish for crew screens and assistant? | English only |
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
