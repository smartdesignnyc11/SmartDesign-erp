# Lanes: who is building what

The chief of staff keeps this board current. A lane is one build agent in its own git worktree (`.claude/worktrees/<name>`, branch `lane-<name>`). Lanes never push or merge. The main session merges them one at a time and runs the full net after each.

## Version 11.2: in flight (2026-10-18)
| Lane | Scope | Status |
|---|---|---|
| plans | Plans control phase 1 (BACKLOG §1.22) | Merged (29effe9) |
| pilotfix1 | Pilot fixes batch 1, 19 items and follow-ups | Merged (8961d73) |
| xset | Cross-set consistency, demo phase (BACKLOG §1.23) | Merged (3683251); xset_test 66/66, plans_test 152/152 |
| findable2 | Find-it-again after every save, pay app %, the outbox address | Merged; findable2_test 185/185 in lane. Adds a "Made Today" card (pointers only, no new store); design gate note in BACKLOG §1.16 |
| pilotfix2 | Pilot fixes batch 2: clock, mail cards, money matching, Reverse Payment, the driver's route, agency mail, card accounts | Merged (8a2f952); pilot_fixes2_test 72/72; leaks2 [6] and flow (slab PO held by the plans guard) handed to netfix |
| netfix | learn, flow, leaks2, chain reconciled with the pilot fixes | Merged; chain 367/0, learn 121, flow 78, leaks2 0 flags in lane |

| monthfix | The scripted month regressed after the merges (251/291 vs v11's 258/292; $10,387 vs $9,537): daily logs not filed (5 events), the late slab PO, the Brooklyn Lumber pickup, the Klein tile credit ($850) | Building |

Merge order: findable2, pilotfix2, then netfix last (it reconciles the suites the others change). Full net after each, then the scripted month and v11.2.

## Version 11.1: in flight (2026-10-18, overnight run Alan approved; weekly usage 4% at start)
| Lane | Scope | Status |
|---|---|---|
| v111-inbox | Emailed asks, calls and client questions become proposals again (demo_ws, client, flow) | Merged (770d829) |
| v111-buy | Purchasing tests vs the vendor-on-file rule; over-budget confirmation; short-pay from Do Now (daywalk); the track drawer click; pricewatch "why is this flagged" | Merged (5cfd2e7) |
| v111-ask | Ask held-out 35/40 by class (negation, relative dates, pronouns, ops, finance); leak_test overspend at landing, source ids, nothing-slips | Merged (28652e9); ask_bank 225/225 and held-out 40/40 |
| v111-feat | Ranking: safety/law, then anyone blocked today, then overdue/today/week, then the principle; harness findings 6–8; integrate's three held commits | Merged (8686794, b361bf9) |
| v111-seed | leak_test [5]: demo costs backed by bank and card lines, bills with their documents, hours tied to payroll runs | Building |

Merge order: inbox, buy, ask, feat (feat last because ranking touches every Home). Full net after each merge, one suite at a time; then the scripted month, the phone check, and publishing v11.

## Version 11: in flight (2026-10-11)
| Lane | Scope | Spec | Status | Hooks other lanes must call |
|---|---|---|---|---|
| crawl | Click every button in every role and view, on phone and desktop. Flag dead ends, no-ops, wrong pages, silent saves, leaks and destructive actions, then fix the classes. | BACKLOG §8 | Merged to master. 11,098 controls over 646 screens, 11 users × phone and desktop; 544 flags to 0 by class. | — |
| chain | Estimate → sign → POs from lines → receive → bills → bank and card, including overhead → matching → progress billing → payment → close → reports checked independently. Gross and net-of-overhead margin. Fix the boot rewriting document amounts. PO lines link to estimate, CO and invoice lines both ways. Line-first New PO. | BACKLOG §8, §1.6 | Merged to master (6dddd48). chain_test 364/364; overhead model; PO line links. | PO line fields `estimateLineId`, `coLineId`, overhead category, `invoiceLineId` |
| charter | The SmartDesign Standard in the app: live, versioned and hash-chained copy loaded from docs/STANDARD.md; role playbook in each assistant's prompt; a "because" on every proposal; ranking by the decision principles; guard and refusals; Standard Watch; vendor region; PO sourcing field. | `docs/STANDARD.md` | Merged to master (ce7f3d0). | `standard()`, `standardWhy()`, `standardAllows()`, `standardRegisterRule()`, `DB.asst[uid].delegated` (message types) |
| rfq | RFQ from lines or plans → foreman → purchasing → vendors → quotes read → leveling → negotiation → award to POs. Sourcing research, vendor vetting, use tax, delivery logistics. | BACKLOG §1.8 items 1–10 | Merged to master (d94db79). Done in lane (rfq_test 120/120). Before merge: rerun counts_lint on a quiet machine. Follow-ups: savings measured against the whole estimate line including labor (should be material only, or say there is no material budget); invoice lines missing as an RFQ source. | Calls `stockGuardOk` on send; registers its Watch rules after merge |
| stock | Inventory before buying: requests split, PO and RFQ guard, override by driver or procurement manager only, stock cost moves to the job, returns to stock, reservations expire, override patterns. | BACKLOG §1.8 item 12 | Merged to master (1d45e70). stock_test 67/67. | `stockCheck()`, `stockGuardOk()` |
| track | Documents attach to PO and bill, with line-up checks; tracking and promise ledger; autonomous vendor follow-ups within delegation. | BACKLOG §1.9 | Merged to master (974a38e). | `DB.asst[uid].delegate.orderFollowups` |
| pricewatch | Price watch with owner-approved explanations, plus the rfq follow-ups (savings against material only; invoice lines as an RFQ source). Starts from branch lane-rfq. | BACKLOG §1.8 item 11 | Merged to master (72473d9). | Absorbs `boughtWhileInStock` at merge |
| integrate | The integration pass below, on master after charter, stock, rfq and chain merged. | `docs/LANES.md` | Merged to master (7a9b7df). Three later commits are not merged (349025c, 62c0712, 390d65b): a second, parallel tasks fix that conflicts with integrate2's, plus "Approvals does what the Do Now card does". Review for v11.1 after the reset: keep integrate2's tasks fix and cherry-pick only the Approvals fix if it is still needed. | — |
| integrate2 | Wire price watch and track to the Standard; one delegation card; Enter the Bill; tasks findable after save (Alan's report) plus find-it-again tests for every create; stock purchases held as inventory. | BACKLOG §1.8, §1.9, §1.14, §1.16 | Building | — |

## Merge plan for version 11
1. **Order:** crawl, chain, charter, stock, rfq, then track if it is ready. Each merge is followed by the full net (`tests/run_all.sh`), one suite at a time.
2. **Integration pass after the merges (one small lane or the main session):**
   - Ranking: urgency first (overdue, today, this week), then the decision principle within each bucket. Immediate safety and law items always come first. Sorting by principle alone put an LLC filing due in 25 days above a bill due today.
   - One delegation model, `DB.asst[uid].delegated`. rfq's `delegate.rfqChases` and track's follow-ups move onto it, behind the "What My Assistant May Send for Me" settings card.
   - `rfqWhy` / `trackWhy` → `standardWhy`.
   - Make the Standard Watch "not measured yet" list measurable where the new lanes now hold the data: three quotes (rfq), deliveries reconfirmed 48h ahead and delivery checks (track).
   - Post stock used on a job to the ledger and job cost (job materials against the inventory asset), checked by finance_xcheck. Today it is recorded and queryable but not in jobFin, so job profit is overstated when stock is used.
   - **Wiring:** RFQ send calls `stockGuardOk`; rfq and stock register their rules in `STANDARD_RULES`; every new CATCH id and DELEGATION kind maps in `charterWhy` (standard_test enforces this); price watch absorbs `boughtWhileInStock`.
3. **Then:** run the month simulation and the phone checks at 390px; publish the artifact as version 11; push to GitHub.
4. **If a lane isn't ready,** ship without it as 11 and follow with 11.1. Never hold the release for one lane, and never ship a red net.

## After version 11 (the order Alan agreed, 2026-10-11)
1. Focused expert review on the published version: controller, procurement, foreman on the phone, and a design expert. Fixes the same day.
2. Simplify: the side menu (§1.15), one task system (§1.14), and §1.11 items 1, 2, 3, 4, 9.
3. Subcontractors, lien waivers and the payment check (§1.10 item 1, §1.12).
4. Reporting (§1.13).
5. The platform and the real agents (§5), as soon as Alan's keys are in.
6. The full ten-expert regrade after the weekly reset.

## Earlier notes
- The role-expert regrade after the 2026-10-15 weekly reset, phone-first, in field conditions.
- Platform (BACKLOG §5) on Supabase plus Netlify. This is what turns the demo-phase AI live: inbox watching, document reading, web search, sending, and bank and card feeds.
