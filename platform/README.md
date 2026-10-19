# The hosted copy (Netlify + Supabase)

The firm's shared system: https://smartdesigns-erp.netlify.app. Built 2026-10-18 (BACKLOG §5, PLAN row 11).

| Piece | Where |
|---|---|
| Netlify site | `smartdesigns-erp` (team alan-i60sjeo). Netlify login protects deploy previews only; production is guarded by the app's own sign-in. The 12 older sites are untouched. |
| Supabase project | `smartdesigns-projects`, ref `eenpabyrmiltfqvzirhw`, us-east-1, Pro plan (daily backups) since 2026-10-18. Sign-up is off: people are invited. |
| Secrets | Netlify only: `ANTHROPIC_API_KEY` (team), `SUPABASE_SERVICE_ROLE_KEY` and `GOOGLE_CLIENT_SECRET` (site, secret; the Google secret is also in Supabase's Google provider). `GOOGLE_CLIENT_ID` is public. Never in the repo, the page or chat. |
| Settings | Netlify site env: `AI_MODEL` (assistant tier, claude-sonnet-5-5), `AI_MODEL_BRAIN` (claude-opus-5-5, owner/PM/controller only), `AI_MODEL_SMALL` (claude-haiku-5-5), `AI_CAP_FIRM_USD` (40), `AI_CAP_USER_USD` (8), `ANTHROPIC_WORKSPACE_ID` (needed while the Anthropic key is not scoped to a workspace). |

## What it does
- **Sign-in and roles.** Supabase email sign-in, and Sign In with Google (on since 2026-10-19; the button shows only while Supabase's Google provider is on). Google never creates an account: sign-up is off, so only invited addresses get in. A new account is role `none` and sees nothing. Only the owner sets a role (`public.profiles`); sign-up metadata is ignored.
- **One truth, many phones.** `public/cloud.js` stores the app's DB as one row per collection and per job. Every save names the version it was based on; a stale save is refused, merged record by record (`merge3`) and saved again. Edits a phone could not sync are pushed at the next boot before the server copy is pulled. Changes arrive by the Supabase change feed, with a 30-second version poll behind it.
- **Security in the database.** Office roles (owner, PM, coordinator, designer, design director, billing, controller) see everything in their workspace. Field roles (foreman, crew, driver) never receive the books, bank, payroll, bills, deals or investors, get money keys stripped from jobs, cannot write the company records, and their saves get the stripped money put back by the server. Clients and the M&B roles are refused until per-client rows exist.
- **AI.** `/api/ai` (netlify/functions/ai.mjs) needs a signed-in member, picks the model by tier, drops page-only fields (MCP servers, sampling, thinking budgets), checks this month's spend against the person's and the firm's cap before calling, and logs who, model, tokens and cost to `ai_usage` (never the prompt or the answer).
- **Seeding.** Once the server holds the firm's records, no device seeds demo data (`window.__sdServerTruth` in `sdSeedsOff`). The first office sign-in on an empty workspace uploads that device's records.

## Build, deploy, test
```
cd platform
python3 build.py                     # builds ../dist, then public/ (index.html, config.js, sw.js, vendor/)
mkdir -p .netlify && echo '{"siteId":"1bdb5200-477c-492a-8294-fb475014deaa"}' > .netlify/state.json   # links the site (the CLI's --site flag fails here)
NETLIFY_AUTH_TOKEN=x netlify deploy --prod --dir public --functions netlify/functions   # the session proxy supplies the real token
npm test                             # merge and AI-proxy unit tests (offline)
python3 test/qa_accounts.py /abs/qa_users.json      # QA accounts (qa workspace), passwords written outside the repo
SD_QA_USERS=/abs/qa_users.json python3 test/live_db_test.py    # the database rules as each role, live (QA workspace)
SD_QA_USERS=/abs/qa_users.json python3 test/live_app_test.py   # owner on desktop + foreman on phone, live
```
The QA accounts file lives outside the repo. The live tests only touch the `qa` workspace and empty it first.
`supabase/schema.sql` is idempotent; apply it with the management API (`POST /v1/projects/<ref>/database/query`).

## Not built yet
Gmail/Calendar/Drive access per person (the same Google client, more scopes), per-client rows for the portal, the server-side hash-chain head, the document reader (`doctext`), the Gmail/Calendar/Drive watcher, Plaid, push notifications, the agents (BACKLOG §5 items 3–8). Field roles currently receive every job, not only theirs.
