# The hosted copy (Netlify + Supabase)

The firm's shared system: https://smartdesigns-erp.netlify.app. Built 2026-10-18 (BACKLOG §5, PLAN row 11).

| Piece | Where |
|---|---|
| Netlify site | `smartdesigns-erp` (team alan-i60sjeo). Netlify login protects deploy previews only; production is guarded by the app's own sign-in. The 12 older sites are untouched. |
| Supabase project | `smartdesigns-projects`, ref `eenpabyrmiltfqvzirhw`, us-east-1, Pro plan (daily backups) since 2026-10-18. Sign-up is off: people are invited. |
| Secrets | Netlify only: `ANTHROPIC_API_KEY` (team), `SUPABASE_SERVICE_ROLE_KEY`, `GOOGLE_CLIENT_SECRET`, `WATCH_KEY` and `VAPID_PRIVATE_KEY` (site, secret; WATCH_KEY seals each person's Google key at rest; the Google secret is also in Supabase's Google provider). `GOOGLE_CLIENT_ID` is public. Never in the repo, the page or chat. |
| Settings | Netlify site env: `AI_MODEL` (assistant tier, claude-sonnet-5-5), `AI_MODEL_BRAIN` (claude-opus-5-5, owner/PM/controller only), `AI_MODEL_SMALL` (claude-haiku-5-5), `AI_CAP_FIRM_USD` (40), `AI_CAP_USER_USD` (8), `ANTHROPIC_WORKSPACE_ID` (needed while the Anthropic key is not scoped to a workspace). |

## What it does
- **Sign-in and roles.** Supabase email sign-in, and Sign In with Google (on since 2026-10-19; the button shows only while Supabase's Google provider is on). Google never creates an account: sign-up is off, so only invited addresses get in. A new account is role `none` and sees nothing. Only the owner sets a role (`public.profiles`); sign-up metadata is ignored.
- **One truth, many phones.** `public/cloud.js` stores the app's DB as one row per collection and per job. Every save names the version it was based on; a stale save is refused, merged record by record (`merge3`) and saved again. Edits a phone could not sync are pushed at the next boot before the server copy is pulled. Changes arrive by the Supabase change feed, with a 30-second version poll behind it.
- **Security in the database.** Office roles (owner, PM, coordinator, designer, design director, billing, controller) see everything in their workspace. Field roles (foreman, crew, driver) never receive the books, bank, payroll, bills, deals or investors, get money keys stripped from jobs, cannot write the company records, and their saves get the stripped money put back by the server. Clients and the M&B roles are refused until per-client rows exist.
- **AI.** `/api/ai` (netlify/functions/ai.mjs) needs a signed-in member, picks the model by tier, drops page-only fields (MCP servers, sampling, thinking budgets), checks this month's spend against the person's and the firm's cap before calling, and logs who, model, tokens and cost to `ai_usage` (never the prompt or the answer).
- **Private to each person.** What came from a person's own Google account (mail, Google Calendar entries, Drive files), their Google connection and their assistant live in `own:<sign-in id>:<collection>` rows. The database lets only that sign-in read or write them, the owner included; `cloud.js` splits them out on save and rejoins them on load, and a device only ever sends its own person's. Job chat, logged calls and ERP calendar holds stay shared.
- **Device settings stay on the device.** Who is using it, their role and name, the job on screen, notifications and the mail marker are never synced (early builds did, and one phone's save switched every other device to that person); the server refuses them.
- **Google connection.** The firm's client ID is in the app's settings; each person connects their own account under Connections, and mail, calendar and Drive are checked while the app is open.
- **One person, several sign-ins.** `profiles.private_key` links sign-ins of one person to one private store (Alan's two addresses). Only the server sets it; nobody signed in can change it.
- **The watcher.** Settings › Connections › Keep Watching When It Is Closed hands the server a one-time Google code; `google-connect` trades it for the long-lived key, seals it (AES-256-GCM, `WATCH_KEY`) into `google_watch`, which nothing signed in can read. `assistant-watch` runs every 15 minutes, weekdays 7am to 7pm New York: each person's new mail, calendar changes and Drive files go into their private `own:<key>:inbox` row; the app files the inbox on opening through the same code as a browser sync (`gsIngestServer`), then empties it. While watching, the browser takes its short-lived Google key from the server, so opening the app syncs with no Google window. The watcher only reads; it cannot send mail or change a calendar. Disconnect revokes the key at Google and deletes it.
- **The watcher's key reads only** (Gmail, Calendar and Drive read-only, `include_granted_scopes` off); `google-connect` refuses and does not keep any key that could send, change or delete. Sending, drafting and booking from the app ask Google in its own window at that moment (`gcFetch` falls back on an insufficient-scope answer), so a stolen server key could read but never send mail as anyone.
- **Push notifications.** Turning on Settings › notifications registers the device (`push_subs`, filed under the private key, unreadable by anyone signed in) and sends a test. After each run the watcher scores what it found (`lib/score.mjs`: a vendor or client on file or their company domain, a job's name or address, a city agency, a calendar entry in the next 48 hours; never promotions, social, newsletters or one's own sent mail) and sends at most one notification naming the first three. Web push with VAPID keys (public in config.js, private a Netlify secret). On an iPhone the app must be added to the Home Screen first.
- **The watcher's finds reach the assistant.** Filing the inbox runs the same follow-up as a browser sync: `paWatch` turns what matters into nudges in the person's assistant conversation (once each), today's brief is rebuilt, the lessons loop runs.
- **Team tools (`/api/team`).** The owner invites people from Settings › Team Accounts (email, role, person in the app; Supabase sends the email; nobody can be invited as a second owner; an address already here just gets the role). Sign Out Everywhere (the owner for anyone, anyone for themselves) deletes the account's sessions and its notification registrations.
- **A session the server ended is dead at once.** Every database check requires a live session (`session_alive()` inside `my_role()`), and the functions check it too, so a lost phone's unexpired key reads and writes nothing from the moment it is signed out. The phone notices within 30 seconds (or at its next start), deletes its local database (records and photos) and its stored sign-in, and shows the sign-in screen.
- **The document reader (`/api/doctext`, the lost doctext.mjs rebuilt).** The app sends a file and gets its text: PDFs with a text layer and Word documents are read on the server at no cost (unpdf, mammoth); scanned PDFs and photos (receipts, slips, certificates) are read by the small Claude model through the same capped, logged door as every AI call (`claude()` in ai.mjs, logged as `small:doctext`); spreadsheets, iPhone HEIC photos and files over 4.5 MB get a plain note of what to do. Files are read in memory and not kept.
- **Partial records do not stop the app.** A job or message from the server missing its lists is repaired on arrival (`normalizeProject` in cloudApply, `cmInit`), and boot tolerates a job without tasks.
- **Seeding.** Once the server holds the firm's records, no device seeds demo data (`window.__sdServerTruth` in `sdSeedsOff`). The first office sign-in on an empty workspace uploads that device's records.

## Build, deploy, test
```
cd platform
python3 build.py                     # builds ../dist, then public/ (index.html, config.js, sw.js, vendor/)
mkdir -p .netlify && echo '{"siteId":"1bdb5200-477c-492a-8294-fb475014deaa"}' > .netlify/state.json   # links the site (the CLI's --site flag fails here)
NETLIFY_AUTH_TOKEN=x netlify deploy --prod --dir public --functions netlify/functions   # the session proxy supplies the real token
npm test                             # merge, AI proxy, private records, watcher, notification-rule and document-reader unit tests (offline)
SDP_APP_HTML=/abs/app.html python3 build.py   # deploy an app build made elsewhere, so dist/ is not rewritten under a running net
python3 test/ingest_test.py          # the app files the watcher's inbox like a sync run (local build)
python3 test/qa_accounts.py /abs/qa_users.json      # QA accounts (qa workspace), passwords written outside the repo
SD_QA_USERS=/abs/qa_users.json python3 test/live_db_test.py    # the database rules as each role, live (QA workspace)
SD_QA_USERS=/abs/qa_users.json python3 test/live_app_test.py   # owner on desktop + foreman on phone, live
```
The QA accounts file lives outside the repo. The live tests only touch the `qa` workspace and empty it first.
`supabase/schema.sql` is idempotent; apply it with the management API (`POST /v1/projects/<ref>/database/query`).

## Not built yet
nudges from the watcher into the assistant thread, per-client rows for the portal, the server-side hash-chain head, Plaid, push notifications, the agents (BACKLOG §5 items 3–8). Field roles currently receive every job, not only theirs.
