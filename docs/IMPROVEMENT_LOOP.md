# The improvement loop (Alan, 10-26)

> "Create agents for the owner, PM, procurement, and billing/accountants ... have those agents constantly working on the site, writing reports, answering questions that will help us improve the site, and then implementing them in a way that's successful and doesn't create bugs. Then the agent tests again and repeats until this is perfect to roll out to the team with real data."

**The measure:** `docs/JOURNEYS.md`, ten journeys, reported as **N of 10 pass on the phone and N of 10 on the desktop**. Feature counts and check counts are not progress.

**The experts:** four agents in `.claude/agents/`, with `_PROTOCOL.md` and `_LOOP.md`:
- `owner.md` (u_owner);
- `pm.md` (u_alan);
- `coordinator.md`, procurement (u_chen);
- `accounting.md`, billing and the books (u_billing, u_controller).

Each has twenty years in the seat and works the way today's tools allow.

## One iteration
1. **Walk.** `tests/cycle_walk.py` runs the ten journeys through the screens on the current build, phone and desktop, with no AI. It gives pass or fail per journey step. This is free (machine time only) and runs first, so the experts never spend tokens on a step a script can show is broken.
2. **Experts.** The four experts each work their journeys and their routine on the same build, through the pilot toolkit on a fresh run with the live assistant. They write `docs/loop/<n>/<role>.md` (format in `_LOOP.md`). A realism judge (`sim/realism_judge.md`) flags turns no professional would take; those are discounted.
3. **Triage.** The main session (with the chief of staff) merges the four reports and the walk into one fix list, grouped by class, ranked by severity and by the journey step each blocks. Each entry gets an acceptance check: the journey step that must pass. Anything that changes a decision of Alan's goes to him as a recommendation; everything else proceeds under the standing go.
4. **Fix.** One or two lanes at a time, on journeys whose files do not overlap. Each lane must do four things:
   - start from the failing journey step, reproduced in the walk;
   - fix the class, not the instance, folding wrappers it touches;
   - pass that step in the walk on both devices, the full net one suite at a time, and the month walk at baseline or better;
   - not hand back until all of that has run on its final head.
5. **Ship.** Each green lane merges and deploys under the standing go, with the live checks.
6. **Retest.** The next iteration starts with the walk on the new build. The experts re-walk the journeys that changed, check that each fix holds and that nothing next to it broke, and walk the rest.

## How bugs are kept out
- The walk is screen-only and starts new, so it fails the way people fail.
- A lane is not green until the journey step it touched passes on both devices, in addition to the net and the month.
- Lanes never share files in the same iteration, so nothing is lost in integration. When two must touch the same screen, they run one after the other.
- A pinned check changes only when an approved design changed what it pins, and the commit says which design.
- Every iteration ends with the experts' retest of the fixes. "Fixed" means the person can now do the step.

## When it is ready for the team and real data
All five of these must hold:
1. All ten journeys pass the walk on both devices, inside budget.
2. Each expert grades their journeys 9 or higher on both devices, with valid coverage (60% or more of their module) and no S1 or S2 open.
3. The money cross-checks tie (chain, finance cross-check, the month walk), and every figure has its bank line.
4. Chen and Jeanette each do their journeys for 15 minutes on their own phones, and nothing stops them.
5. Alan says go.

## Cost and cadence
- **Per iteration:**
  - the walk is free;
  - four experts are about 0.4M tokens each, 1.6M, measured on Pilot 3 day 1 at about 96k a turn, four turns each;
  - triage is about 0.1M;
  - one or two fix lanes are 0.5 to 1M each;
  - so about 2.5 to 3.5M an iteration.
- **Cadence:** iterations run back to back under the standing go. When weekly usage passes the threshold Alan sets (default 85%), the loop pauses after the current iteration and resumes after the reset. Each iteration ends with a short scoreboard to Alan:
  - journeys passing, phone and desktop;
  - expert grades;
  - S1 and S2 open;
  - what was fixed;
  - what is next;
  - the measured cost.

## The scoreboard
| Iteration | Date | Phone | Desktop | Owner | PM | Procurement | Accounting | S1 / S2 open | Cost |
|---|---|---|---|---|---|---|---|---|---|
| 0 (Pilot 3 day 1) | 10-25 | not measured | not measured | 5 / 5 | 4 / 5 | - | - | many | 0.97M |
