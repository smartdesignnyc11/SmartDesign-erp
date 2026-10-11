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
| `selftest.py` | A scripted mini-day through `act` with no LLM; proves the harness. |
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
  context cannot mix `is_mobile` pages otherwise).
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
**Assistant hook:** the app's `/api/ai` calls reach the server and get a 503, so the assistant answers from its
built-in logic. To run the Claude-backed assistant, forward `/api/` in `Sim.handle` to the AI proxy.

## The referee
`ledger.md` / `ledger.json`: every due event on time, late or missed and the first time it reached the right
person's screen (from the screens they actually rendered); money left behind and schedule days lost;
find-it-again failures; places to look per person, day and kind (owed, approve, money) from the screens they
acted on; the bank tie-out (lines the bank sent and the ERP lacks, typed lines, payments with no deposit, bills
paid with no debit, unmatched lines); outside the Standard (mail that left without a person's own send,
approvals by a role the delegation does not name, refused attempts); and the PERSIST reload check.
It reuses `tests/month_runtime.js` (`M.check`) for the event checks, and month_sim's ledger arithmetic.

## Limits worth knowing
- An action takes 2-8 s; a page reload (when someone else saved) 6-10 s. A 35-turn day of about 12 actions each
  is roughly 40-70 minutes of wall time on this machine, plus the agents' own thinking.
- Places-to-look and outside-the-Standard are heuristics on control labels (approve / money / owed) and on the
  delegation in plain terms; read them as leads, not verdicts.
- The world's replies are template text unless the world-agent hook is used. Held-out events need live records
  (open POs); early days with few POs get fewer of them.
