# Hosting on Netlify

Two accounts, one config file, about 30 minutes. Netlify serves the app and runs the server side: the AI proxy, the sourcing harvest, and the inbox parser.

---

## 1. Supabase — database, sign-in, files (10 min)

1. supabase.com → **New project**. Name `smartdesigns`, region **US East**, save the database password.
2. **SQL Editor → New query** → paste all of `supabase/schema.sql` → Run.
3. New query again → paste all of `supabase/mb_incentives.sql` → Run. (Creates the sourcing tables, the PostGIS screening function, and the Harlem watch area.)
4. **Authentication → Users → Add user** for yourself, then each team member. Tick *Auto confirm*.
5. **Project Settings → API** — copy three values:
   - **Project URL**
   - **anon public** key — safe in the browser
   - **service_role** key — server only, never in the browser, never committed

---

## 2. Netlify — hosting and functions (10 min)

1. Push this folder to a private GitHub repo.
2. netlify.com → **Add new site → Import an existing project** → pick the repo. `netlify.toml` already sets publish directory, functions directory and the schedules, so accept the defaults and deploy.
3. **Site configuration → Environment variables** → add:

| Variable | Value | Needed for |
|---|---|---|
| `SUPABASE_URL` | your project URL | everything |
| `ANTHROPIC_MODEL` | *(optional)* model id | the clipper's tidy-up step |
| `ALERT_WEBHOOK` | *(optional)* a Slack / Teams / generic webhook URL | the morning digest from `credit-watch` |
| `SUPABASE_ANON_KEY` | anon public key | signals API |
| `SUPABASE_SERVICE_ROLE_KEY` | service_role key | harvest jobs writing signals |
| `ANTHROPIC_API_KEY` | console.anthropic.com key | the Assistant |
| `CRON_SECRET` | any long random string | stops strangers triggering a harvest |
| `CLIP_REQUIRE_TOKEN` | *(optional)* `1` | refuse clips without an issued token, from the first deploy |
| `WORKSPACE_ID` | `default` | multi-workspace later |
| `NYC_APP_TOKEN` | *(optional)* Socrata app token | raises the open-data rate limit |

Add the mailbox variables in step 4.

4. Redeploy so the variables take effect. Note the address, e.g. `https://smartdesigns.netlify.app`. Add a custom domain (`app.smartdesign.nyc`) under **Domain management** whenever you like.

---

## 3. Point the app at Supabase (2 min)

Edit `public/config.js`:

```js
window.SDP_CONFIG = {
  appName: 'SmartDesigns Projects',
  supabaseUrl: 'https://xxxx.supabase.co',
  supabaseAnonKey: 'eyJ…',
  workspace: 'default',
  aiUrl: '/api/ai'
};
```

Commit and push. In Supabase → **Authentication → URL Configuration**, set *Site URL* to your Netlify address so sign-in links and password resets come back to the app.

---

## 4. The alert mailbox (10 min) — this is what gives you portal coverage

Create a dedicated mailbox, e.g. `deals@mercerandbond.com`. On each portal, set your saved searches to email **that** address:

| Portal | Where |
|---|---|
| StreetEasy | Saved Searches → alert frequency → *Instant* or *Daily* |
| Zillow | Saved searches → email updates |
| LoopNet | Saved searches → email alerts |
| Crexi | Saved searches → notifications |
| Auction.com | Saved searches / property alerts |
| Ten-X | Watchlist alerts |

Broker blasts sent to you directly can simply be forwarded to the same address.

Then pick one of two ways for the job to read it.

**A. IMAP pull (simplest).** Add to Netlify env:

```
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USER=deals@mercerandbond.com
IMAP_PASS=<16-character app password>
IMAP_MAILBOX=INBOX
```

Gmail: turn on 2-step verification, then create an **App password** (Google Account → Security → App passwords) — your normal password will not work. The job reads unread mail every fifteen minutes and marks it read only after it has parsed it, so a failure re-reads rather than silently dropping mail.

**B. Webhook push.** If you would rather not store a mailbox password, forward the mail to the function instead — Cloudflare Email Workers, SendGrid Inbound Parse or Mailgun Routes all POST to a URL:

```
POST https://your-site.netlify.app/api/inbox
Header: x-inbox-secret: <INBOX_WEBHOOK_SECRET>
```

Set `INBOX_WEBHOOK_SECRET` in Netlify. The endpoint accepts JSON (`{from, subject, html, text, date}`), SendGrid's form fields, or raw MIME.

**Test it without writing anything.** Paste any alert email and see exactly what would be filed:

```bash
curl -X POST "https://your-site.netlify.app/api/inbox?dry=1" \
  -H 'content-type: application/json' \
  -d '{"from":"StreetEasy <noreply@mail.streeteasy.com>","subject":"New listing","html":"<a href=\"https://streeteasy.com/building/140-prospect-place\">140 Prospect Place</a><div>$3,495,000 · 4 beds</div>"}'
```

---

## 5. First harvest (2 min)

Run each job once by hand — they are idempotent, so re-running costs nothing:

```bash
curl "https://your-site.netlify.app/api/harvest-acris?days=30&key=$CRON_SECRET"
curl "https://your-site.netlify.app/api/harvest-gov?days=60&key=$CRON_SECRET"
curl "https://your-site.netlify.app/api/inbox?key=$CRON_SECRET"
```

`harvest-gov` runs seven feeds. Run one at a time while you are watching it:

```bash
curl "https://your-site.netlify.app/api/harvest-gov?feeds=sales&days=180&key=$CRON_SECRET"
```

`feeds=` accepts `taxlien, hpd, ecb, dobviol, dob, dobnow, sales` — all seven by default.

Each returns a JSON report — blocks scanned, rows found, rows saved, and any error by name. Then open the app → **Mercer & Bond → Watchlist**; the signals appear at the top with source, score, and a link to the record.

Check the datasets are answering at any time:

```bash
curl "https://your-site.netlify.app/api/harvest-gov?probe=1&key=$CRON_SECRET"
```

Empty output is good. A named dataset means an ID drifted — tell me which one and it is a one-line fix.

---

## What runs when

| Job | Schedule (UTC) | Does |
|---|---|---|
| `harvest-acris` | 11:00 daily | Lis pendens, notices of pendency, assignments of leases, referee's deeds, mortgages, satisfactions, deeds — for every watched block |
| `harvest-gov` | 11:20 daily | Tax lien sale list, HPD open violations, ECB open balances, DOB violations, legacy DOB job filings, DOB NOW permits, DOF recorded sales |
| `harvest-inbox` | every 15 min, 11:00–23:59 | Saved-search alerts and forwarded broker mail |
| `credit-watch` | 11:00 weekdays | Credits that landed against a return, return windows closing, boxes sent back and not credited |

Netlify's free tier covers this comfortably; the jobs are small and the open-data APIs are free.

---

## Scoring

Signals are ranked so the feed puts the sharpest first.

| Signal | Base | Why |
|---|---|---|
| Lis pendens / notice of pendency | 100 | Foreclosure has started |
| Referee's deed | 95 | Sold at foreclosure — REO owner, motivated |
| Tax lien on the sale list | 85 | Published before the sale, so you are early |
| HPD class-C violations open | 35 + 12 each | Distress and leverage |
| Auction listing | 70 | Dated, forced timeline |
| Assignment of leases | 60 | Lender tightening |
| Water lien only | 55 | Softer than a tax lien |
| Deed recorded | 50 | Who is buying on your blocks |
| New listing | 40 | Ordinary market inventory |
| DOB Alt-1 or new building filed | 45 | Someone is investing next door |
| DOB NOW permit issued — major work | 45 | A real job started on the block |
| Open ECB balance | 40 + 5 per $10k | Distress with a number attached |
| Two or more open DOB violations | 35 + 4 each | Conditions the owner is carrying |
| Recorded sale | 50 (+10 under $600/sf) | What the block actually trades at |
| Mortgage / satisfaction | 30–35 | Ownership activity |

Two adjustments on top: **+15** if the lot sits in a historic district — landmark stock is the thesis — and **+20** if a listing geocodes inside one of your watch areas. A price cut adds 15; an open-house blast loses 10.

---

---

## The property dossier

`GET /api/property` answers one address with everything the public record holds. It is what a deal
profile pulls when you open it.

```bash
curl "https://your-site.netlify.app/api/property?address=254%20W%20121st%20Street"
curl "https://your-site.netlify.app/api/property?bbl=1017190034&include=owner,sales"
```

| Section | What comes back | Source |
|---|---|---|
| `lot` | Class, year built, floors, units, lot and building area and dimensions, zoning, built vs. maximum FAR and the unused square footage, assessed value, historic district | MapPLUTO |
| `owner` | The head officer, corporate owner and managing agent behind the LLC, each with a business mailing address | HPD Multiple Dwelling Registrations + Registration Contacts |
| `sales` | This lot's sale history, the block's recent trades, and the block's median $/sf | DOF Citywide Annualized Sales |
| `violations` | Open HPD by class, open DOB, open ECB with the balance due | HPD, DOB, ECB |
| `permits` | DOB NOW permits with scope, cost, owner and contractor; legacy BIS filings | DOB NOW, DOB BIS |
| `acris` | Every recorded document on the lot with a link to the image | ACRIS |

`include=` trims the call to the sections you want. Responses cache for fifteen minutes.

The owner lookup only answers for buildings HPD requires to register — multiple dwellings. A one- or
two-family house comes back `registered: false`, which is the correct answer, not a failure.

---

---

## Money that came back

`credit-watch` runs at 11:00 UTC on weekdays — about 6am in New York, before anyone opens the app. It
asks the questions the Procurement screen asks, using the same rule module, and files what it finds in
`sel_alert` so it is waiting rather than discovered:

- a credit that landed against an open return, with the reason it believes the pair
- money in from a vendor with no return behind it
- a return window already closed, or closing within seven days
- a box sent back more than ten days ago with no credit against it

It never confirms a match. Machine proposes, person confirms — and a job running at six in the morning
with nobody awake is the last place to relax that.

```bash
# see what it would file, writing nothing
curl "https://your-site.netlify.app/api/credit-watch?dry=1&key=$CRON_SECRET"
```

Set `ALERT_WEBHOOK` to a Slack, Teams or generic incoming-webhook URL and it posts the digest as well.
Findings that stop being true — a credit confirmed, a return closed — are deleted rather than left
shouting, so the list is only ever what is still open.

**The rule lives in one file.** `netlify/functions/lib/creditmatch.mjs` decides what a match is; the
browser copy is generated from it by `npm run gen`, and `npm test` fails if the two have drifted. Two
implementations of a money rule is one too many.

---

## The clipper

The browser extension lives in `extension/`. Load it unpacked from `chrome://extensions`, set the board
address and token in its options, and a vendor page becomes a selections-board item in one click.
`CLIPPER.md` has the full picture — how it reads a page, and the verification checks it feeds.

Tokens are issued from the board — **Procurement → Clipper access** — and stored as hashes in
`sel_token`. Set `CLIP_REQUIRE_TOKEN=1` if you want the endpoint closed before the first token exists. `POST /api/clip` files into `sel_clip`; both tables live in
`supabase/mb_incentives.sql`, so re-run that file if your database predates the clipper.

```bash
# does the server-side fallback work on a given vendor?
curl "https://your-site.netlify.app/api/clip?url=https://www.build.com/some-product"
```

```bash
# is this spec sheet really for the SKU we bought?
curl "https://your-site.netlify.app/api/specsheet?url=https://cdn.vendor.com/rgls02.pdf&sku=RGLS02-UB"
```

A `blocked: true` reply means the vendor refuses servers — expected on several of them, and exactly why
the extension exists.

---

## What this does not do

No phone numbers, and no interior photos. Those come from skip-trace data brokers and MLS feeds on
paid subscriptions; every source above is a public record with no licence and no terms-of-use barrier.

Portals are never scraped. StreetEasy, Zillow, LoopNet, Crexi, Ten-X and Auction.com all prohibit automated access, they block it, and CoStar in particular litigates it. The inbox route works because it reads mail the firm is entitled to receive. If REBNY RLS access lands, it drops in as another `source` value with no schema change.

## Refreshing the app itself

`public/index.html` and `public/app.js` are built from the prototype:

```bash
python3 build.py        # rebuilds public/ from src/
git commit -am "app update" && git push    # Netlify redeploys
```

## Tests

```bash
npm test                # inbox (15) + harvest/owner/property (24) + clipper (21) + spec sheets (15) + credit matching (28)
npm run gen             # regenerate the browser copy of the credit-matching rule
```
