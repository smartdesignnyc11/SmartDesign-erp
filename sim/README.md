# sim/: the agent month harness (docs/BACKLOG.md §1.17)

The role experts (`.claude/agents/`) work 20 working days in ONE shared company, through the app's screens only.
This folder is the harness; the main session runs the agents (`day_plan.md`). The scripted month
(`tests/month_sim.py`) stays as the cheap regression check; this run complements it.

| File | What it is |
|---|---|
| `server.py` | The world: serves the build on localhost, one browser context (one IndexedDB), a page per person, the clock, the turn lock, the action log, snapshots, `/act` and `/admin`. |
| `page_tools.js` | The server's in-page reader: screen to text with numbered controls, the mailbox, the find-it-again probes. Only the server runs it. |
| `act` | The agents' toolkit (the only way in). `sim/act <uid> help`. |
| `simctl` | The main session's controls: world, begin/end a turn, prompt, referee, advance, persist, stop. |
| `world.py`, `world_book.json` | The outside world: scripted events (from `tests/month_book.json` via `make_book.py`), seeded held-out events, reply rules, the world-agent hook. |
| `referee.py` | The scorer: ledger.json / ledger.md after each day. |
| `roles/` | `_common.md` plus one briefing per person. |
| `turn_prompt.md`, `day_plan.md`, `day_plan.json` | The per-turn prompt template and the day's turn order. |
| `workshop_nav.md`, `workshop.py` | The Navigation and Pages Workshop at the end of the pilot: usage (pages, time, taps, trails, back-tracks, top jobs, where each person looked first), the expert prompt (27 short questions, each finding tagged page, frequency, severity), and the scorer that groups findings across roles for the synthesis. `sim/simctl menus` captures each role's menu. |
| `workshop_docs.md`, `docs.py` | The Documents Workshop: documents made as real work (the day plan's `doc_tasks`, some on the phone), measured (taps, seconds, screens, typed vs filled, characters per line, validation stops, found after save), audited by the referee (job, client, entity, cost codes, line links, tax, retainage, terms, CO budget effect, pay-application % against the SOV, PO sourcing, and the reports), rendered as the client receives them (`simctl client-docs`: portal on the phone, print, PDF), judged by creators, the client, the owner and the designer, and a gallery for Alan (`docs.py gallery`). |
| `day_plan_pilot2.json`, `checks_p2.js` | Pilot 2: the same 3 days, the whole firm (30 book events tagged `pilot2`, some in chains that open when the step before is done), every office role on the phone at least one turn a day and the field on the desktop once, the UI/UX judgement per device, the click check, the cost per turn. `checks_p2.js` holds Pilot 2's checks on top of month_runtime's. |
| `day_plan_lean.json` | The lean pilot: 3 days, 7 daily roles, 3 slots, crew and driver on day 3, the client's portal side played by world rules (`simctl world-client on`). |
| `day_plan_pilot3.json`, `cycle_book.py` > `cycle_book.json`, `cycle.py`, `script_p3.js`, `pilot3.py`, `turn_prompt_p3.md`, `roles/p3/`, `realism_judge.md`, `plan_p3.py` | Pilot 3, the business cycle (below). |
| `selftest.py`, `selftest_cycle.py` | A scripted mini-day through `act` with no LLM; proves the harness. `selftest_cycle.py` (also `selftest.py --unit`) checks Pilot 3's book, referee, coverage and judge on invented fixture companies, with no browser. |
| `live.py`, `turn_prompt_live.md` | Live mode (`server.py --live <role>`): the same verbs on the hosted site as the role's QA account, a phone and a desktop that meet only through sync, no world, no clock pin (below). |
| `voicer.py` | The voicer (`simctl world-voice on`): each outside reply written in the party's own words by the live model, facts kept, template on failure (below). |
| `picture_cost.py` | What one screen picture costs a model, measured through the live AI door. |
| `selftest_gaps.py` | Units for the picture, memory, the voicer, live mode and the run ledger (in `selftest.py --unit`). |
| `runs/<run>/` | Everything a run writes (git-ignored): `world.json` (server state), `db.json` (the database snapshot, after every change), `db_<day>.json`, `actions.jsonl`, `diary/<uid>.md`, `files/<uid>/` (attachments and photos), `shots/`, `world/pending` and `world/answers`, `ledger.*`. |

## Run it
```
python3 build.py
python3 sim/server.py --run pilot1 &          # about a minute to boot; --resume after a crash or pause
sim/simctl world morning
sim/simctl begin u_angel morning --cap 12
sim/simctl prompt u_angel                      # hand this to a subagent with Bash
sim/simctl end
...                                            # day_plan.md has the whole loop
sim/simctl advance
sim/simctl referee --final; sim/simctl persist; sim/simctl stop
python3 sim/selftest.py                        # the harness check, about 5-10 minutes
```
`act` and `simctl` find the server through `sim/runs/.current` (or `SIM_RUN=<run>`).

## What the harness guarantees
- **One company.** Every page shares one IndexedDB. Before a person acts, their page reloads if anyone saved
  since it loaded; after each action it saves (`saveNow`) and the version moves. Pages that are not acting
  cannot write (their IndexedDB writes are dropped), so a stale timer cannot overwrite the company. If a page
  had to reload, a tap on an old number is refused and the fresh screen is returned.
- **Screens only.** `/act` takes a fixed set of verbs; text an agent types is passed as data, never evaluated.
  Unknown verbs (eval, db, js, query, ...) are refused at the CLI and at the server, and logged.
  `/admin` needs the run's token (`runs/<run>/.admin_token`); the briefings forbid reading `runs/`.
  `--debug` adds a developer-only `simctl debug-eval`; never start a run with agents that way.
- **The clock.** The app day moves only through `appSetDay` on the world page (the day's APP_DAY_HOOKS run once).
  The time of day is pinned per slot (morning 07:30, work1 10:00, work2 13:30, eod 16:30) plus two minutes per
  action, in America/New_York. The browser's own wall clock never leaks in.
- **Phones.** Field roles and the client get a 390x844 page with mobile metrics and touch through CDP (one
  context cannot mix `is_mobile` pages otherwise). Any person's turn can be on either device (`simctl begin
  --device`, or the plan's `devices`); with `--switch` the person may `act <uid> device desktop|phone` mid-turn. It is
  the same page re-laid out, so the one-IndexedDB and one-turn guarantees hold. Every action logs its device.
- **The click check.** Every tap, key, menu go and back logs where it started and landed (view, page heading, the
  sheet on top, a fingerprint of the screen, the first words, whether a toast offers Open). The referee classifies
  each against its label (landed, done, dead, off-label, wrong, silent, failed, back-tracks), per person, page and
  device (`ledger.md` "Click check").
- **The cost.** Per turn: toolkit calls, characters in and out, prompt and reads, diary written, the estimate they
  imply, and the conductor's measured tokens (`simctl cost`): `cost.jsonl`, `cost_<day>.json`, `cost.md`.
- **Chains.** A book event with `gate` / `after` waits for its check to pass on the world page, then fires (dated that
  slot, plus `delay` working days) with what the check found filled into its text and expectation.
- **Ids.** `Math.random` is seeded per page boot (different on every boot) so ids never collide across pages.
- **Logged.** Every action: who, app day, slot and time, the screen it started on and ended on, the control,
  the result, toasts, page errors, and the find-it-again check for every record it created (`creates`). A record
  not visible to its creator right after saving is checked again after their next reload.
- **Resumable.** `world.json` and `db.json` are written after every change; `--resume` loads the snapshot into
  IndexedDB before the app boots.

## The outside world
`world_book.json` holds the scripted month converted for agents: mail, calendar, Drive and bank lines as they
were; field and client events as **situations** each person learns through `act <uid> news` (what is in front of
them; whether it reaches the app is now up to them); three "facts" applied through the app's functions. Every
event keeps its expectation, so the referee scores what the scripted month scores. Each morning a seeded
generator adds held-out events from the live records: late deliveries, partial shipments, a price change, a
client change request, a failed inspection, a vendor invoice over its PO, a meeting transcript in Drive, card
lines. Bank and card lines reach the controller as a statement CSV attached to the bank's mail; the controller
imports it through Banking > Import Statement (`act upload`).

Mail staff send is delivered by the server's post office: to a colleague's Demo Workspace, to the client agent's
mailbox, or out to the world, whose rules answer with delays and randomness (some parties never answer). An
issued PO that reaches its supplier sets off the truck (a situation for the foreman), the invoice by mail, and
for card suppliers a card line on the next statement. Promised client payments arrive as bank deposits.
**World-agent hook:** `sim/simctl world-agent on` writes each scheduled reply to `runs/<run>/world/pending/`;
an LLM can voice it into `world/answers/<id>.txt` before it is due.
**Assistant hook:** the app's `/api/ai` calls reach the server. With a signed-in member's Supabase session token in
`SIM_AI_TOKEN` (or a file named by `SIM_AI_TOKEN_FILE`, re-read on every call so the conductor can refresh it), the server
forwards `/api/` to the hosted proxy (`SIM_AI_URL`, default https://smartdesigns-erp.netlify.app) during a person's turn, so
the assistant is the real one. Every call is that member's, under their monthly cap, and the model is picked by their role
on the server. Only the path, status, size and time are logged. Without a token it answers 503 and the assistant uses its
built-in logic.

## The referee
`ledger.md` / `ledger.json`: every due event on time, late or missed and the first time it reached the right
person's screen (from the screens they actually rendered); money left behind and schedule days lost;
find-it-again failures; places to look per person, day and kind (owed, approve, money) from the screens they
acted on; the bank tie-out (lines the bank sent and the ERP lacks, typed lines, payments with no deposit, bills
paid with no debit, unmatched lines); outside the Standard (mail that left without a person's own send,
approvals by a role the delegation does not name, refused attempts); and the PERSIST reload check.
It reuses `tests/month_runtime.js` (`M.check`) for the event checks, and month_sim's ledger arithmetic.

## Pilot 3: the business cycle (Alan, 2026-10-25)
Pilot 2 fed people mail and due dates; nobody had to run the business, and the referee could not say whether purchasing
overspent a line. Pilot 3 adds required work the referee verifies in the data:
- **Four roles play:** the owner, the PM, the coordinator and billing. The foreman's, the crew's and the controller's steps
  are scripted world actions (`script_p3.js`): receiving against the PO with one delivery short and one damaged, hours on
  cost codes, the daily log and the measured %, the statement import through Banking's own import, the app's own proposed
  matches confirmed, and the payroll build. The referee checks each one so the cycle closes, and grades none of them.
- **The required-work book** (`cycle_book.py` writes `cycle_book.json`). One invented job carried end to end by the people
  who do each step: the Ashbys at 214 Lincoln Place.
  - The steps run: inquiry, lead, client, project, a 12-line estimate from the walk-through notes, a question back, sent,
    signed, contract and SOV.
  - Then: RFQs from estimate lines to three vendors, quotes back by mail in messy formats, award, POs from the lines, sent.
  - Then: deliveries, the vendors' bills, the deposit invoice and its payment against the bank line, a change order priced
    and approved, the progress invoice from the SOV with retainage, the Friday review and client updates, and Tuesday's numbers.
  - Nine money leaks are planted:
    - a PO over its line;
    - stock already on the shelf;
    - a price above last time;
    - a bill over its PO;
    - a short delivery and a damaged one, both billed in full;
    - a card purchase for the client;
    - an approved change order not billed;
    - measured work not billed.
  - Interruptions cut into turns.
- **Top-down, like a person:**
  - Each person gets the firm's objectives for the week (outcomes, never steps or screen names) and their role card (`roles/p3/`).
  - Each person gets the Standard as the app holds it today (`pilot3.py` renders `DB.company.standard` with their playbook).
  - Each morning they write a plan, each evening a review, and give a `--why` on every significant action.
  - Every action costs the minutes a person would spend (`MINUTES` in `server.py`). A turn has a budget of minutes as well as actions.
- **The referee** (`cycle.py`, in `ledger.md` as "Business cycle") reads the raw records, never the app's report functions.
  - **Per step:** done right, done wrong (what), not done, or scripted, and who owned it.
  - **Per planted leak:** whether it held, who caught it, and the money left behind.
  - **Its own figures:** job cost per estimate line (budget, committed, actual, over), work done not billed,
    reimbursables, cash and AR.
  - **The answers:** each person's written answers graded against those figures.
  - **Coverage** of each role's main module: below the floor (60%), the grade is not valid.
  - **The realism judge** (`realism_judge.md`, `simctl judge <uid>`): its flagged turns are listed and discounted from the grade.
- **The live assistant:** `/api/` is forwarded to the hosted proxy only with a signed-in member's session token, given at run
  time (`SIM_AI_TOKEN` or `SIM_AI_TOKEN_FILE`) and never written to the repo. Without it the assistant answers from its
  built-in logic.
- **Mail** takes several recipients and cc (`mail send "Chen, Billing" ... --cc "..."`, `mail reply <n> --all`).
- **Documents** report what is *missing*: first what never reached the person who gets it, then the back-end fields.
- **Turns and tokens:** `plan_p3.py` measures Pilot 2's run. The estimate is in `day_plan_pilot3.json`, `turns_and_tokens`.
- **Calibration** against the firm's real coordinator and billing person: `docs/pilot/pilot3/calibration.md`.

## What the instrument sees, and what it still does not (Alan 10-26: "we only see 50% of the puzzle")
- **The page as a picture.** When an action lands on a screen the person has not seen this turn (a new view, page
  heading, sheet, record, tab, or the other device), the server saves a JPEG at the device's size under
  `runs/<run>/shots/<uid>/` and the result ends with `Screen picture: <path>`. The expert reads it before acting. At most
  one per screen; 8 per journey turn (`SIM_PICTURE_CAP`) and 30 per page walk (`simctl begin ... --kind pages`,
  `SIM_PICTURE_CAP_PAGES`; `--pictures N` for one turn); `SIM_PICTURES=0` turns them off (the screen walk). Cost: 437 tokens
  a phone picture, 1,719 a desktop one (docs/IMPROVEMENT_LOOP.md).
- **The live site.** `SD_QA_USERS=<file> python3 sim/server.py --run live-pm-1 --live pm` (owner, pm, coord, billing,
  controller; the QA accounts in the 'qa-loop' workspace, `platform/test/qa_accounts.py --add`). Then
  `SIM_RUN=live-pm-1 sim/simctl begin u_alan live --device phone` and `simctl prompt u_alan`. Two browsers (phone, desktop),
  each signed in through the real sign-in screen with its own copy; `act <uid> device desktop` picks up the other one;
  every screen ends with the app's save status. `news`, `call` and `mail` say there is no world. The scripted check of
  the same is `platform/test/live_journeys_test.py`.
- **A world that answers like people.** `simctl world-voice on` (with `SIM_AI_TOKEN_FILE` on the server, e.g. from
  `platform/test/qa_token.py owner <file> --every 40`): a reply that falls due is written by the live model as that party,
  in a style seeded per run and reply (plain, terse, a question back, another layout, a slot late, or in two parts). Every
  fact of the rule's reply (prices, dates, quantities, numbers, a decision's words) must be kept and none invented, or the
  template goes out; `world/voice.jsonl` and "World voice" in ledger.md say which. Who answers, when, and the money stay
  with the rules.
- **Memory between turns.** What a person heard is in `files/<uid>/news.md`, what they said and promised (mail sent, calls
  both ways) in `files/<uid>/said.md`, and each turn ends with an `## Open promises` list in the diary that the next turn
  reads.
- **Still different from an employee:** a turn is a fresh agent that reads its notes rather than remembers; the expert sees
  a picture only of new screens, not every glance; the world's people are a model voicing rules, not people with their own
  agenda (they never start a conversation, change their mind or call back on their own); the live site has no world and
  shares one QA workspace; a day is a few turns, not eight hours.

## Limits worth knowing
- An action takes 2-8 s; a page reload (when someone else saved) 6-10 s. A 35-turn day of about 12 actions each
  is roughly 40-70 minutes of wall time on this machine, plus the agents' own thinking.
- Places-to-look and outside-the-Standard are heuristics on control labels (approve / money / owed) and on the
  delegation in plain terms; read them as leads, not verdicts.
- The world's replies are template text unless the voicer (`world-voice on`) or the world-agent hook is used. Held-out events need live records
  (open POs); early days with few POs get fewer of them.
