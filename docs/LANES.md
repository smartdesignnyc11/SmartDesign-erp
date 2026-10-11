# Lanes: who is building what

The chief of staff keeps this board current. A lane is one build agent in its own git worktree (`.claude/worktrees/<name>`, branch `lane-<name>`). Lanes never push or merge. The main session merges them one at a time and runs the full net after each.

## Version 11: in flight (2026-10-11)
| Lane | Scope | Spec | Status | Hooks other lanes must call |
|---|---|---|---|---|
| crawl | Click every button in every role and view, on phone and desktop. Flag dead ends, no-ops, wrong pages, silent saves, leaks and destructive actions, then fix the classes. | BACKLOG §8 | Building | — |
| chain | Estimate → sign → POs from lines → receive → bills → bank and card, including overhead → matching → progress billing → payment → close → reports checked independently. Gross and net-of-overhead margin. Fix the boot rewriting document amounts. PO lines link to estimate, CO and invoice lines both ways. Line-first New PO. | BACKLOG §8, §1.6 | Building | PO line fields `estimateLineId`, `coLineId`, overhead category, `invoiceLineId` |
| charter | The SmartDesign Standard in the app: live, versioned and hash-chained copy; role playbook in each assistant's prompt; a "because" on every proposal; ranking by the decision principles; guard and refusals; Standard Watch; vendor region; PO sourcing field. | `docs/STANDARD.md` | Building | `standard()`, `charterWhy()`, `STANDARD_RULES` (register rules) |
| rfq | RFQ from lines or plans → foreman → purchasing → vendors → quotes read → leveling → negotiation → award to POs. Sourcing research, vendor vetting, use tax, delivery logistics. | BACKLOG §1.8 items 1–10 | Done in lane (rfq_test 120/120). Before merge: rerun counts_lint on a quiet machine. Follow-ups: savings measured against the whole estimate line including labor (should be material only, or say there is no material budget); invoice lines missing as an RFQ source. | Calls `stockGuardOk` on send; registers its Watch rules after merge |
| stock | Inventory before buying: requests split, PO and RFQ guard, override by driver or procurement manager only, stock cost moves to the job, returns to stock, reservations expire, override patterns. | BACKLOG §1.8 item 12 | Built in lane; full net running | `stockCheck()`, `stockGuardOk()` |
| track | Documents attach to PO and bill, with line-up checks; tracking and promise ledger; autonomous vendor follow-ups within delegation. | BACKLOG §1.9 | Building | `DB.asst[uid].delegate.orderFollowups` |
| pricewatch | Price watch with owner-approved explanations, plus the rfq follow-ups. Starts from branch lane-rfq. | BACKLOG §1.8 item 11 | Queued: starts when crawl, chain, charter or stock finishes (the machine is overloaded) | — |

## Merge plan for version 11
1. **Order:** crawl, chain, charter, stock, rfq, then track if it is ready. Each merge is followed by the full net (`tests/run_all.sh`), one suite at a time.
2. **Wiring after merge:** RFQ send calls `stockGuardOk`; rfq and stock register their rules in `STANDARD_RULES`; every new CATCH id and DELEGATION kind maps in `charterWhy` (standard_test enforces this); price watch absorbs `boughtWhileInStock`.
3. **Then:** run the month simulation and the phone checks at 390px; publish the artifact as version 11; push to GitHub.
4. **If a lane isn't ready,** ship without it as 11 and follow with 11.1. Never hold the release for one lane, and never ship a red net.

## After version 11
- The role-expert regrade after the 2026-10-15 weekly reset, phone-first, in field conditions.
- Platform (BACKLOG §5) on Supabase plus Netlify. This is what turns the demo-phase AI live: inbox watching, document reading, web search, sending, and bank and card feeds.
