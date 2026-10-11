# Review protocol: the role experts and the four lenses

From round 5 the reviewers are the role experts in `.claude/agents/` (owner, pm, coordinator, foreman, crew, designer, billing, controller, client) plus the founder lens. Each runs a full working day as that person with their Demo Workspace (mailbox, calendar, drive) connected, tests every hand-off to the other roles, and grades the screens, the assistant and the brain separately (`.claude/agents/_PROTOCOL.md` has the report format). The four lenses below remain the grading scale: founder, UX (the role experts' flow findings), finance (the controller and billing), ops (the pm, coordinator, foreman and client).

- **Connect your Demo Workspace first.** Settings › Connections › "Connect Demo Workspace" (or `gcDemoConnect()` as your user), then Sync Now: an invented mailbox, calendar and drive for your persona, served through the same code real Google uses; nothing in it is real, and Disconnect removes it (docs/ARCHITECTURE.md, "Demo Workspace").

Every improvement round ends with the same four independent reviewers re-scoring. Run each reviewer as a separate subagent that did NOT write the code. Each one:
- drives `dist/smartdesigns_projects.html` with Playwright;
- saves screenshots and scripts under `review/r<N>_<lens>_*`;
- returns a report.

## Report format (strict, under 160 lines)
1. **Verdict.** Three sentences, plus what is fixed vs the previous report (by finding number), plus an overall grade out of 10 against the leaders in that lens, with the reason.
2. **What best-in-class does here that this does not.** Concrete.
3. **Findings.** Numbered, most important first. Each gives: what was seen (screen, role, steps), why it hurts the person, the fix, severity 1–3 and effort S/M/L. Mark each REMAINS / FIXED / NEW.
4. **The five things to do next.**
5. **If below 9: "What stands between this and 9".** Concrete steps, what happens, what should happen, the fix.

A 9 means a seasoned professional in that lens would choose this over the leader for this firm, with no severity-1 or severity-2 finding left.

## How to drive the app
- Open the file and wait for `document.body.dataset.booted==='1'`.
- Sign in with `signIn('<user>'); render()`. Users:

  | Id | Role |
  |---|---|
  | `u_owner` | owner |
  | `u_alan` | pm |
  | `u_chen` | coord |
  | `u_angel` | foreman |
  | `u_alberto` | crew |
  | `u_alex` | driver |
  | `u_klein` | client: Sarah & David Klein, 121 State Street |
  | `u_cambri` | client: 140 Prospect |
  | `u_sarah` | designer |
  | `u_billing` | billing |
  | `u_controller` | controller |

- Navigate with `view='<id>'; render()`, but click the real buttons whenever judging flow.
- Viewports: desktop 1440x900 (or 1440x1000), phone 390x844 with `is_mobile` and `has_touch`.
- App day: 2026-09-03.
- The assistant: `paAsk(question)` returns `{headline, note, work[], kind, interp}`.
- The query engine: `erpQuery({entity, where, group, agg, sort, limit, q})`.
- Finance helpers: `jobFin(project)` and `companyPL([from, to])`.

## Founder lens (an AI-native ERP founder vs NetSuite, Procore, Buildertrend, HubSpot, Copilot)
- **Sweep.** Every role's landing and nav, on desktop and phone. Click every rail entry and phone bottom-bar entry plus More, and every owner view (about 88).
- **Badges.** Every sub-view for owner, pm and coord: the rail badge = the overview count, and a tab badge = its page.
- **Ask.** The scripted 25 questions, plus 15 new unscripted ones each round, re-asked in fresh sessions to rule out leftover context.
- **One-tool test.** Is there one list per noun? Does one label always give one number? Is the next step obvious? Can every record be found (⌘K) and reported on (Report Builder)?

## UX lens (a senior product designer: flow and ease of input)
- **The eight jobs.** Do each end to end as the named role and count clicks or taps, typed fields, dead ends, and whether the next step is visible. Round-4 costs are in brackets.

  | Job | Role | Steps | Round 4 cost |
  |---|---|---|---|
  | 1. Receive + bill | coord | Purchasing › Deliveries › Received › "Bill It" in the toast › invoice # › Enter | 4 clicks + 1 field |
  | 2. CO from the estimate | PM | Billing › Change Orders › New Change Order › title + tick a line › Start › price › Send to Client › Send | 3 + 1 field + 1 tick, then 3 |
  | 3. Progress invoice + payment | billing | Brief "Draft It" › New Invoice › Send to Client › Send › Record Payment › Enter | 6 clicks, 0 typed |
  | 4. Foreman, on phone | foreman | Clock in; Materials (Ask › Materials › task › one line › Next › Send › Done); Hidden condition (Ask › Problem › Hidden Condition › one line › Send) | 1 tap; 5 taps + 1 select + 1 line; 4 taps + 1 line |
  | 5. Owner | owner | Brief; approve WW-2026-118 and AMP-311; open a decision | 0; 2 clicks each; 1 click |
  | 6. Task for Chen | PM | New Task › title › assignee › Friday › Enter | — |
  | 7. "What is on order from Carlos" | coord | Ask; ⌘K | vendor ranks first |
  | 8. Client decision | client | Choose › option card › Confirm Choice | 3 taps, no typing |

- **One job per new capability:**
  - the controller reconciles a bank account and reviews the budget;
  - the PM takes a submittal through to Release Order;
  - the foreman files a phone daily log with a % update and photos;
  - the client sees progress and shared photos.
- **Phone in the field (from round 5):** every expert tests the phone in field conditions, not at a desk: one hand and gloves (44px targets in thumb reach), glare (16px text, AA contrast, 130% text size), slow 3G and offline (actions queue and land; nothing typed is lost), interruptions (come back to where you were), the on-screen keyboard, voice input, seconds per field job (under 30 s, under 5 taps), camera, landscape, a 4x-slower CPU. `.claude/agents/_PROTOCOL.md` has the checklist.
- **Phone sweep:** 16 key screens plus every document type: no overflow, active sub-tab in view, inputs not covering labels.

## Finance lens (a construction CFO/controller vs NetSuite / QuickBooks Enterprise)
- **Cross-checks on every surface:** cash, AR, unmatched, AP (owed vs awaiting approval), recognition, WIP over/under, backlog, net YTD, safe to spend. HANDOFF.md has the expected values.
- **30 CFO questions to Ask,** as owner and as controller. Topics: cash, AR aging, overdue invoices, bills to approve, AP, margin by job, WIP, backlog, payroll, 1099 / W-9, sales tax, disputes, close status, budget.
- **Month-end, end to end:**
  1. short-pay WW-2026-118 (Approve PO Amount, Dispute Difference);
  2. Approve as Billed on AMP-311;
  3. import an Amex August CSV and reconcile Amex, Chase July and Chase August;
  4. code the rest and close August;
  5. post seven late changes (card line, bill edit, payroll approval, feed lines);
  6. reopen and re-close.
  - **Expect:** August holds in both ledger and management views; WIP = 2500/1200 per job; the Pack = the ledger.
- **Probes:**
  - Dispute: does earned revenue swing?
  - 1099: by instrument, Zelle payees, $2,000 threshold for 2026.
  - Payroll: accrual from the submitted run; allocation coverage gate.
  - The opening entry: who signed it?
  - Needs Category: one count.
  - Re-dating: into or out of a closed month is refused; a reason is required.
  - Budget: locks and roles enforced in functions; Owner activates a version.
  - Feeds: provenance honesty; Demo Feed ≠ bank evidence.

## Ops lens (a PM / client-services lead vs Procore / Buildertrend)
- **The thread on 121 State Street:**
  1. priced options on a decision › Send to Client;
  2. the client chooses (+$1,850) › Home › Tasks › Open › Raise Change Order;
  3. the CO is sent and approved;
  4. Billing: New Change Order with the Framing line ticked, 5 days, $6,400, approved;
  5. Revise R1 ($7,200, 7 days) and approve; R2 ($5,000, 3 days) and approve;
  6. Pull In;
  7. a no-show slip on Framing (+5);
  8. Publish.
  - **Check:**
    - the publish dialog and the client's What Changed split per cause;
    - revisions show deltas;
    - days come back;
    - CO lines bill from 0;
    - tasks open their record and close themselves;
    - the forecast tile names the right cause;
    - milestone pills are honest;
    - the portal shows only certified completion.
- **Elsewhere:** 45 Cranberry (mark Design Development done, reload after 0.4 s, check the Studio phase); the 140 Prospect portal; Project Messages (one list, one clock, outbound included); the designer's day.
- **Field:** % complete into the pay app; the Daily Log from time punches, with delays into move reasons; the photo stream; the submittal register with the PO gate.

## A month of the company (optional, about 30 minutes)
`tests/month_sim.py` runs 9/3 to 10/2 (21 working days) on one page with `tests/month_book.json` (293 invented events) and scripted people who act only on their own screens. It writes `review/month/ledger.md` and `ledger.json` (every event on time, late or missed; the day it reached the right screen; money left behind; schedule days lost; the function responsible) and the line `MONTH caught X/Y on time · Z late · W missed · $M left behind · D schedule days lost`. The integrator runs it on the merged build (`tests/run_all.sh month_sim`); a fix lane starts from the function the ledger names.

## Automated guard rails that must stay at zero
`lint.py` (desktop and phone), `counts_lint.py`, `smoke_test.py`, `baseline_test.py`, the Ask bank (held-out score reported), `daywalk.py` and `finance_xcheck.py`. BACKLOG.md §0 has the specs.
