# The agent month: how the main session runs a day

The harness is in `sim/` (README.md). The main session is the conductor: it runs the world, gives each person
their turn as a subagent, then lets the referee score and the day advance. Turns are strictly one at a time
(the server refuses anyone acting out of turn), so subagents run sequentially, never in parallel.
The same plan, machine-readable, is `sim/day_plan.json`; the lean pilot Alan chose is `sim/day_plan_lean.json` (`sim/simctl plan sim/day_plan_lean.json` once, after starting the run).
**Pilot 2** runs `sim/day_plan_pilot2.json` (same three days, the whole firm, phone and desktop); its own section is at the end.

## Before day one
1. `python3 build.py` (the build the month runs on; note its commit in the run notes).
2. Start the world once, in the background, and leave it running: `python3 sim/server.py --run <name>`
   (about a minute to boot; `sim/runs/<name>/server.json` appears when it listens; the log line `ready` when the
   company is seeded, the app day pinned to the book's first day and every staff Demo Workspace connected).
   After a crash or a usage pause: `python3 sim/server.py --run <name> --resume` and carry on from the last step
   the log shows (`sim/simctl status` gives the day, slot and any open turn; an open turn can simply be ended).
3. Optional: `sim/simctl world-agent on` to let an LLM voice the outside parties' replies (below).

## A day (four slots)
For each slot in order (morning, work1, work2, eod):
1. **The world.** `sim/simctl world <slot>` (`--watchers` in morning and work2: each staff mailbox is pulled
   and the app's assistant reads it, the way the lost hosted watcher did; `--no-watchers` in work1 and eod).
   It delivers the slot's scripted and held-out events, replies that fell due, the bank's statement mail, and
   situations (`news`) to the people they happened to.
2. **The turns.** For each person in the slot's list (`day_plan.json`; optional people only when
   `sim/simctl brief <uid>` shows news or unread mail):
   - `sim/simctl begin <uid> <slot> --cap <cap>` (caps: morning 12, work 20, eod 12);
   - `sim/simctl prompt <uid>` prints the filled per-turn prompt (`sim/turn_prompt.md`);
   - run ONE subagent with that prompt and Bash (it reads its briefing and diary, works through `sim/act`,
     writes its diary, ends with `DONE: ...`). Routine turns on a mid-tier model; the eod turn, where the expert
     writes the judgement, on the strongest model;
   - `sim/simctl end` (saves, and delivers what they mailed: to a colleague's mailbox, to the client agent, or
     out to the world, whose rules schedule the reply).
3. **World-agent hook (optional).** If `world-agent` is on, after each slot look in
   `sim/runs/<name>/world/pending/`: for each `<id>.json` with no `answers/<id>.txt` yet, a cheap subagent
   playing that party (its `persona`, the message it got, the template reply) writes the free-text reply to
   `answer_file`. The world sends it at the due slot instead of the template; timing and money stay with the rules.
4. After eod: `sim/simctl advance` (the referee scores the day into `ledger.md` / `ledger.json`, a copy of the
   database is kept as `db_<day>.json`, the app day moves on and the day's hooks run).

At the end of the pilot's last day, before stopping the server: the Navigation and Pages Workshop
(`sim/workshop_nav.md`: `sim/simctl menus`, `python3 sim/workshop.py usage`, one expert subagent per person from
`python3 sim/workshop.py prompt <uid>`, then `python3 sim/workshop.py score` and its synthesis subagent; output
`runs/<run>/nav_workshop.md`).

Every five days: `sim/simctl referee` and read `ledger.md` (the strongest model) for what to raise. At the end:
`sim/simctl referee --final`, `sim/simctl persist`, `sim/simctl stop`; then collect each person's diary verdicts.

## Turn order and why
- **Morning:** the field first (Angel, Alberto, Alex: on site at 7), then the office (owner, PM, Chen, Sarah,
  billing, controller), the client last (the Kleins read their mail and the portal after the kids leave).
- **Work 1:** whoever has the most hand-offs moves first: Angel, the PM, Chen, the controller, billing, Sarah,
  the owner, then the crew and driver.
- **Work 2:** the core loop again (Angel, PM, Chen, controller, billing); the rest only if something reached them.
- **End of day:** the field closes out first (log, clock out), then the office, the owner, the client.

## Token rules
- `screen` pages are capped at about 3,600 characters (about 1,000 tokens); `find "text"` returns 100-300 tokens;
  `type` and `pick` return one line. Agents are told to prefer `find` and never to re-read a screen a tap returned.
- Caps per turn stop wandering; the server refuses the action after the cap. A Documents Workshop task raises its
  turn's cap to the task's (CO 24, estimate 36, PO 24, RFQ 24, invoice 18, pay application 24, bill 16, request 12).

## Token estimate
Terms: **new context** is what a turn adds (its reading plus every tool result plus what it writes); **processed
input** is what the model reads across all its calls in the turn, mostly cache reads, counting about 10k tokens of
fixed subagent overhead (system prompt and tools) per call. That overhead is an assumption; it dominates.
| Turn | Calls | New context | Processed input | Output |
|---|---|---|---|---|
| morning, about 6 actions | 10 | 8k | 160k | 1k |
| routine work, about 11 actions | 15 | 13k | 270k | 3k |
| document task, about 28 actions | 32 | 22k | 740k | 4k |
| small document task (request, bill), about 12 actions | 16 | 14k | 350k | 3k |
| end of day, about 5 actions and the diary and judgement | 9 | 9k | 150k | 2.5k |

**Lean pilot (`day_plan_lean.json`): 3 days, 7 daily roles, 3 slots, crew and driver on day 3, client by rules.**
- A day: 7 morning turns (1.1M), about 6 work turns of which 2 are big document tasks, 1 small, 3 routine
  (1.5M + 0.35M + 0.8M), 7 end-of-day turns (1.05M): about **4.8M processed, 0.22M new context, 45k output**.
- Day 3 adds the crew's and the driver's one work turn and short end of day (about 0.6M).
- Workshops at the end of day 3: Navigation and Pages for 9 staff (about 25k processed each: 0.23M), Documents
  for 5 creators, the one client read (it reads 4-8 rendered documents, text plus one look at each image, about
  40k), 2 brand reads and 2 syntheses (about 0.35M together).
- **Total: about 15M processed input (about 90% cache reads), 0.7M new context, 0.17M output.** Wall time: about
  180 toolkit actions a day at 2-8 s, plus page reloads (6-10 s per turn) and the world steps: about 20-25 minutes of
  harness time a day, plus the agents' own thinking.

**The full plan (`day_plan.json`), for comparison, in the same terms:** 10 roles, 4 slots, about 35 turns a day:
about 8-9M processed a day, so about 26M for 3 days and about 170M for 20 days. (My first estimate, 3-5M a day,
left out the fixed per-call overhead.)

## A Workflow-ready description
Inputs: run name, number of days, `day_plan.json`. State lives in the server (`sim/simctl status`), so the
workflow can stop and resume at any step.

```
status = simctl status
for day in remaining days (status.days after status.days_done):
  for slot in plan.slots:
    sh(slot.world)
    people = slot.turns + [p for p in slot.optional if simctl brief p shows news>0 or unread>0]
    for uid in people:
      sh("sim/simctl begin {uid} {slot} --cap {plan.caps[slot]}")
      prompt = sh("sim/simctl prompt {uid}")
      agent(prompt, tools=[Bash, Read, Edit], model = plan.models.eod if slot == eod else plan.models.routine)
      sh("sim/simctl end")
    if world-agent on: for each pending reply without an answer: agent(party prompt) -> write answer_file
  sh("sim/simctl advance")
  if day index % 5 == 4: sh("sim/simctl referee"); agent(review ledger.md, strongest model)
sh("sim/simctl referee --final"); sh("sim/simctl persist"); sh("sim/simctl stop")
```
A subagent that fails or runs out of actions still gets `simctl end`; the next turn goes on. If the server is not
answering, start it with `--resume` and repeat the step `status` shows as open.

## Measuring the cost (every run; Pilot 2 reports day 1 before days 2 and 3)
Two numbers per turn, side by side in `runs/<run>/cost.jsonl`, totalled per day in `cost_<day>.json` and `cost.md`
(and summarised in `ledger.md`):
1. **Measured, by the conductor.** The Agent (Task) tool's result for each subagent ends with its usage: total tokens,
   tool uses and duration. Right after `sim/simctl end`, copy them in:
   `sim/simctl cost <uid> --tokens <total_tokens> --tool-uses <tool_uses> --ms <duration_ms>`. It attaches to that
   person's last ended turn. A workshop subagent or a world-agent voice: `sim/simctl cost workshop:<uid> --tokens N`
   (any label not starting with `u_` gets a line of its own). If the tool shows input, output and cache reads apart,
   add `--input`, `--output`, `--cache-read`. Nothing is guessed: a turn the conductor did not measure says so.
2. **Measured, by the harness.** The server counts every toolkit call of the turn, the characters each sent and got
   back (every result is context the model rereads on each later call), the prompt `simctl prompt` printed and the
   files it points to (`_common.md`, the briefing, the diary; `simctl prompt` reports their sizes), and the diary
   characters written. From these it estimates new context, processed input (each call rereads the context so far
   plus the fixed per-call overhead, 10k tokens assumed, `OVERHEAD` in server.py) and output. The estimate is what
   stands in for an unmeasured turn; where both exist, report the measured one and how far the estimate was off.

After day 1: `sim/simctl advance`, then read `runs/<run>/cost.md` and give Alan the measured day-1 total, the turns
it covers, the share of turns measured, and the projection for days 2 and 3 (day 1 x the turn ratio in
`day_plan_pilot2.json` "turns_per_day", plus the workshops) before running on.

## Pilot 2: turns and cost (sim/day_plan_pilot2.json)
**What changes from Pilot 1.** The same days (9/3, 9/4, 9/8) and Pilot 1's events, untouched, plus 30 events tagged
`pilot2` (prospect to client, estimate, contract, deposit, payment, progress invoice; the pantry CO and its billing; a
PO from the GWB line received one line short, its bill and the short line held; clock in and out for the foreman,
crew and driver; payroll built and approved; a portal question; task hand-offs and closes; the Monday meeting in
Meeting Mode). The referee prints "Pilot 1 events" and "all events" apart. Start the server with `--seed 9806211`
(Pilot 1's) so the held-out events match where the live records allow.

**Devices.** `simctl begin` reads `devices` in the plan (day, slot, person): `phone`, `desktop`, or `a+b` (start on
a, may `act <uid> device b`, with `switch_cap` more actions). A doc task's `device` wins. Every office role has a
phone turn each day; the field looks at the desktop once, at the end of day 3. Every action logs its device.

**Turns.** Day 1: 20-21 (morning 7, work 6 plus Sarah when news reached her, eod 7). Day 2: 20-21. Day 3: 26-27
(the crew and driver add a morning, a work and an eod turn each). Workshops: 10 for Navigation and Pages (9 experts
and the synthesis), 10 for Documents (6 creators, the client read, 2 brand reads, the synthesis). About 69 turns and
20 workshop runs in all.

**Estimate, in the terms above (processed input; the 10k-per-call overhead is an assumption, day 1 measures it):**
| Day | Turns | Doc tasks | Processed input | New context | Output |
|---|---|---|---|---|---|
| 1 | 21 | CO (phone), PO (phone), request (phone), bill | about 5.5M | about 0.25M | about 50k |
| 2 | 21 | estimate (phone), estimate (owner), RFQ, invoice | about 5.9M | about 0.27M | about 55k |
| 3 | 27 | meeting, payroll, pay application, CO; the five-second looks on both devices | about 7.3M | about 0.33M | about 70k |
| Workshops | 20 | 8 screenshots per expert (phone and desktop) | about 1.0M | about 0.25M | about 30k |
| **Total** | **89** | | **about 20M** | **about 1.1M** | **about 0.2M** |
Against the lean Pilot 1's estimate of 15M: the owner's work turns become mandatory, two more doc tasks, the crew and
driver morning on day 3, a longer end of day (the two-device judgement, cap 10) and twice the screenshots. Wall time:
about 25-35 minutes of harness time a day plus the agents' thinking. These are estimates; day 1's measurement
replaces them.

**The loop for one turn (Pilot 2):**
```
sim/simctl begin <uid> <slot>            # device and cap from the plan and the doc task
sim/simctl prompt <uid>                  # hand it to ONE subagent with Bash (routine: mid-tier; eod: strongest)
sim/simctl end
sim/simctl cost <uid> --tokens N --tool-uses N --ms N    # from the Agent tool's result
```
