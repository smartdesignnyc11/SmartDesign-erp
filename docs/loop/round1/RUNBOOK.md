# Round one: the runbook (main session)

**Starts** when the estimate lane (J1, J1b, J2) has merged and deployed. Rule 6: the experts judge the build people will use, not one being fixed. The feedback recorder and the drafts lane should also be in it.

## 0. Test the instrument (rule 4)
1. Run `tests/slot.sh python3 tests/cycle_walk.py --keep --devices desktop` on the deployed build. This gives the scoreboard's walk numbers and a checkpoint of the company before each journey, at `sim/runs/cw_<stamp>_desktop.ck/<J>`.
2. Do one dry turn: the PM, five actions, on a world resumed from the J2 checkpoint, with pictures on. Read the trail and the pictures. Go on only if:
   - the pictures arrive;
   - the notes files (news, said) are listed in the prompt;
   - the assistant reaches the live model.

## 1. The experts' worlds
Each expert works in their own world, resumed from the checkpoint before their first journey:

| Expert | Agent | Journeys | Starts from | Modules for the page walk |
|---|---|---|---|---|
| Owner | role-owner | J1, J10 (approvals, cash, job cost) | J1 checkpoint (blank start) | Today, Sales and Clients, Company and Settings |
| PM | role-pm | J2, J3, J4 | J2 checkpoint | Projects, Field and Site, Design |
| Procurement | role-coordinator | J5, J6, J7 | J5 checkpoint (signed estimate) | Purchasing |
| Accounting | role-accounting | J8, J9, J10 (the books) | J8 checkpoint (signed contract) | Billing, Accounting, Time and Payroll |
| Client | role-client | the portal: approve a CO, pay the deposit, ask a question | the J4 checkpoint (signed) | Client Portal |

To start a world: `python3 sim/server.py --run r1_<role> --resume` after copying the checkpoint folder to `sim/runs/r1_<role>`, then `sim/simctl plan sim/day_plan_pilot3.json`, `sim/simctl cycle on` and `sim/simctl world-voice on`. Set `SIM_AI_TOKEN_FILE` to a QA owner token file, refreshed every 40 minutes, so the assistant is the live one.

## 2. Each expert's turns (about 0.6M tokens each)
1. **Two local turns** on their journeys: morning (plan, then work) and work (finish the journeys), with pictures on.
2. **One live turn** (`sim/server.py --live <role>`, qa-loop accounts): the same job started on the phone and finished on the desktop.
3. **The page walk:** with `docs/modules/<module>_census.md` and the shots in `review/census/<module>/shots/`, open every page and sub-page of their modules through the toolkit (`screen --shot` where the shot is old). For each page, give:
   - keep, merge into another page, move to another role, or remove;
   - what is on it that is too much or not for them;
   - what is missing that belongs there.
4. **The report:** `docs/loop/round1/<role>.md` in the `_LOOP.md` format. That means the journeys, the twelve questions, the findings by class, the per-page verdicts, the retest, and the grades.
5. **The realism judge** on each local turn (`simctl judge <uid>`).

## 3. Triage (main session and the chief of staff)
- `docs/loop/round1/TRIAGE.md`: one list, grouped by class, ranked by severity and by the journey step each blocks, each with its acceptance step.
- The page verdicts are tallied per page across experts. A page that two or more experts would merge or remove becomes one consolidation item, checked against `docs/CONSOLIDATION.md`.
- The scoreboard row in `docs/IMPROVEMENT_LOOP.md`, and the retro line in `docs/PROCESS.md`.

## 4. Fix lanes
One or two at a time, never sharing files, in the triage's order. Each starts from its failing journey step and ends with the walk, the net and the month on its final head.
