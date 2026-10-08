# Handoff: where the work stands (2026-10-08)

## What this repo is
`src/app.js` and the shell files rebuild the exact build Alan has open today: the claude.ai artifact "SmartDesigns Projects", Version 136, published 2026-10-04 at the end of expert round 4.
- **Proven:** `tests/smoke_test.py` booted all 10 users on desktop and phone and opened every view each may open. That is 2,338 checks with 0 errors, at most one primary button per screen, no sideways scroll and no emoji.
- **Same numbers:** the rebuild reproduces the published build's figures. `tests/baseline_test.py` pins them.

## What was lost, and what to do about it
The cloud workspace that built rounds 1–5 was reclaimed. Four things were lost:
1. **The commented source with section markers.** The minifier stripped them.
   - **Recover:** for any area, read the same function in `legacy/commented-source-v96/app.js` for the original intent and comments.
2. **About 150 Playwright suites, plus the tools that ran them:** `lint.py` (the screen standard), `counts_lint.py`, `daywalk.py` and the reviewer scripts.
   - **Recover:** rebuild the essentials first (BACKLOG.md §0). The specs are in docs/REVIEW_PROTOCOL.md.
3. **Round-5 work.** Two lanes finished and were verified, but their code was lost before integration: **closetie** (finance) and **truthpct** (one % complete / EAC / portal truth). Two lanes were cut off by a usage limit before finishing: **askgen** (Ask generalisation) and **clientpo** (Release Order, client approvals, phone fixes).
   - **Recover:** BACKLOG.md §1 restates all four as specs, including the exact figures the finished lanes produced, so they can be re-implemented and checked against those numbers.
4. **The hosted backend after 2026-09-15.** `legacy/hosted-app-2026-09-15.zip` has the earlier Netlify/Supabase app. Lost since then:
   - **AI and documents:**
     - `netlify/functions/ai.mjs`: the Anthropic proxy, with the model pinned via the `AI_MODEL` env and an optional `AI_APP_TOKEN` door.
     - `doctext.mjs`: PDF, HTML and Office text extraction.
   - **Google, per user:**
     - `google-connect.mjs`: trades the OAuth code for a refresh token, per user.
     - `assistant-watch.mjs`: a scheduled function, `*/15 11-23 * * 1-5`, that reads each user's Gmail, Calendar and Drive and writes nudges.
     - `lib/guser.mjs` and `lib/watch-score.mjs`.
     - `supabase/assistant.sql`: a `google_user_token` table with no client policies, plus a private `asst:%` row policy.
   - **Plaid:**
     - `lib/bankfeed.mjs`: tokens sealed with AES-256-GCM using `BANKFEED_KEY`.
     - `plaid-link-token`, `plaid-exchange`, `plaid-sync` (/transactions/sync with a cursor; idempotent; handles added, modified and removed), `plaid-sync-scheduled` (even New York hours, 6–22) and `plaid-webhook` (ES256 JWT verification).
     - `supabase/bankfeed.sql`: row-level security per firm; the token table is service-role only.
   - **Sync (`public/cloud.js`):**
     - per-user `asst:<uid>` shards;
     - `Cloud.token()`;
     - pending-shard markers and a keepalive push on pagehide, re-pushed before `pullAll`, so a local edit is never overwritten by the server copy.
   - **Tests:** node tests for the above with Plaid mocked.

   The browser half of all of this IS in `src/app.js` (gc*, gs*, ga*, mind*, bf* functions). Only the server half needs rebuilding.

## How the work was run, rounds 1–4
- **The protocol, every round:**
  - Four independent expert reviewers walked the app as each role, with Playwright at 1440x900 and 390x844.
  - They wrote graded reports with numbered findings.
  - Parallel lanes fixed them, each in its own clone with its own suite.
  - An integrator composed the lanes and ran every suite, both lints, the counts lint and the day walk.
  - The same reviewers re-scored.
- **Grades:**

  | Round | Founder | UX | Finance | Ops |
  |---|---|---|---|---|
  | 3 | 6.5 | 7 | 6 | 7 |
  | 4 | 7.5 | 7.5 | 7.5 | 8 |

- **Round 4 shipped 14 lanes:**
  - **Correctness:**
    - **close:** a period-true, repeatable close.
    - **payables:** Approve PO Amount / Dispute Difference; a 1099 register by payment instrument with the 2026 $2,000 threshold; Needs Category suggestions.
    - **onecount:** one list per noun; one predicate per label.
    - **ask4:** document numbers, "Did you mean" and "I read this as".
    - **cause:** per-cause "What Changed"; CO revision deltas; days given back; CO lines billed from 0.
  - **Flow and trust:**
    - **billing:** the Billing Queue; one Ready to Bill figure; a safe blue button; the owner approves in one step.
    - **records2:** locks past draft; receiving leads to the bill; read summaries; toasts.
    - **client:** tasks follow their source record; client titles; seeded options; one client nav; the verb "Choose".
    - **trust:** Title Case on labels only; one app clock; inert panels; immediate save flush.
    - **screens:** one control strip per screen; one Tasks component.
  - **New capabilities:**
    - **budget:** versions, and budget vs actual everywhere.
    - **bankfeed:** line provenance, OFX/QFX/CSV import, a QuickBooks-style reconcile, a Demo Feed, feed health.
    - **submittals:** reviewers, revisions, the PO gate, client approval.
    - **field:** % complete driving the pay app, a guided Daily Log, a photo stream.

## Key figures in the current build (app day 2026-09-03; owner)
| Figure | Value |
|---|---|
| Cash | $184,231 |
| AR | $92,265 |
| Unmatched bank lines | 16 · $75,272 |
| AP owed | $0 bills + $16,040 payroll past due ($43,300 is awaiting approval, not owed) |
| WIP over-billed | $154,742 |
| Backlog | $581,408 |
| Net YTD | −$3,797 (income $144,292) |
| Safe to spend | −$2,618 |
| Ready to Bill | $20,980 (2 rows; 121 State held as billed ahead) |
| Rail badges | Projects 2, Sales 4, Purchasing 10, Accounting 6, Billing 2 |

If a change moves one of these, say exactly why. The finance reviewer checks every surface agrees.

## Live artifact
- **Published copy:** https://claude.ai/artifact/BcFBruG3KKGRH2fYd9eLjp (Alan's).
- **Deploying from Claude Code:** produce `dist/smartdesigns_projects.html` and give it to Alan to publish, or deploy through the hosted copy.
