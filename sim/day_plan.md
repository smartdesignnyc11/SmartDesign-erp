# The agent month: how the main session runs a day

The harness is in `sim/` (README.md). The main session is the conductor: it runs the world, gives each person
their turn as a subagent, then lets the referee score and the day advance. Turns are strictly one at a time
(the server refuses anyone acting out of turn), so subagents run sequentially, never in parallel.
The same plan, machine-readable, is `sim/day_plan.json`.

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
- `screen` pages are capped at about 3,600 characters (about 900-1,100 tokens); `find "text"` returns a few lines.
  Agents are told to prefer `find` and never to re-read a screen a tap just returned.
- Caps per turn (12 / 20 / 20 / 12 actions) stop wandering; the server refuses action 13 of a 12-action turn.
- A turn prompt plus `_common.md`, the role briefing and today's diary is about 3,000-4,000 tokens to read.
- Estimate per routine turn: 4-8k tokens of input context growth (about 8-15 tool calls, half of them screens at
  roughly 1k tokens and half short results) plus the reading above: about 10-20k tokens per turn, 30-40 turns a
  day. See README.md for the arithmetic.

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
