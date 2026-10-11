# Decisions and requests: Alan's log

What Alan asked for or decided, with the date, where it lives, and its status. The chief of staff keeps this current: every new ask is logged the same hour, with the lane it went to. Newest first within each day.

Status: **Built** (merged and tested) · **Building** (a lane is on it) · **Spec** (written, not started) · **Waiting on Alan** · **Later** (deferred by Alan).

## Waiting on Alan
| Asked | Decision needed | Default until he decides |
|---|---|---|
| 2026-10-11 | Leftover material from a cost-plus or reimbursable job: return it to the client, credit it on their invoice, or take it into firm stock? | Flagged "client-owned surplus, ask the PM"; never moved into firm stock automatically. |
| 2026-10-11 | Confirm with the accountant that out-of-state material purchases owe NY use tax, and at what rate. | Landed cost adds use tax at 8.875% (editable). A bill with no tax charged is flagged "use tax to accrue". |
| 2026-10-11 | ChatGPT history export, to deepen `docs/ALAN.md`. | Profile built from the build sessions and the Standard only. |
| 2026-10-10 | Re-authorise QuickBooks for the July-to-date pull. | Truth layer runs on bank and card lines and the QBO bridge snapshot. |

## 2026-10-11
| Ask or decision | Where it lives | Status |
|---|---|---|
| A chief of staff that thinks like Alan, tracks the changes and manages the agents | `.claude/agents/chief-of-staff.md`, `docs/ALAN.md`, this file, `docs/LANES.md` | Built (docs) |
| Invoices and receipts attach straight to the PO, the bill or both; the AI checks every figure lines up; open mismatch blocks payment | BACKLOG §1.9 item 8 | Building (lane "track") |
| Version 11 should be the strongest update yet | Merge plan in `docs/LANES.md` | Building |
| Tracking numbers, invoices, receipts, delivery dates and vendor promises filed in place; vendor follow-ups sent autonomously (within delegation) | BACKLOG §1.9 | Building (lane "track") |
| Think past every ask: what's missed, how to make it better, what could go wrong | `CLAUDE.md` | Built (standing rule) |
| Check inventory before buying; only the driver or procurement manager overrides, with a reason | BACKLOG §1.8 item 12 | Building (lane "stock") |
| Owner approves price-watch explanations and baseline changes ("lumber up 8%") | BACKLOG §1.8 item 11 | Spec (lane "pricewatch", queued) |
| Price watch: flag purchases above past prices and anything abnormal | BACKLOG §1.8 item 11 | Spec (lane "pricewatch", queued) |
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
