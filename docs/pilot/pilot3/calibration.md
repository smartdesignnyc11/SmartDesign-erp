# Pilot 3 calibration: one hour with the firm's own coordinator and billing person

Alan, 10-25: "make sure they are using it as if they were a real person." The agents are role experts on paper. This hour shows how the firm's real coordinator and real billing person do the same work. Their behaviour is then compared with the agents' trails, and the role cards (`sim/roles/p3/`) and the realism judge (`sim/realism_judge.md`) are corrected from it.

This is a script for Alan to run. Nobody has been contacted.

## Before the session (the conductor, 15 minutes)
1. Start a calibration world:
   - `python3 sim/server.py --run calib-<name> --seed 9806211`
   - `sim/simctl plan sim/day_plan_pilot3.json`
   - `sim/simctl cycle on`
2. Play the world to day 2, morning, so that 214 Lincoln Place is signed:
   - Either play days 1 and 2 with the agents.
   - Or let the owner's and PM's steps be done by hand on the conductor's screen, to the point where the estimate is signed and the buy list has gone out.
3. Open the app in a normal browser as the person:
   - the coordinator signs in as Chen (`u_chen`);
   - billing signs in as Billing (`u_billing`).
   They use the real screens with a mouse or their phone. The `act` toolkit is not used.
4. Print the person's objectives from `sim/cycle_book.json` (`objectives`) and their role card. Do not give them the steps, the leaks or the referee's list.
5. Open a timer sheet with three columns: clock, what they are doing, what they said. Ask permission to record the screen and their voice. If they say no, take written notes only.

## The session (one hour each, separately)
Say only this:

> This is a normal Friday morning, and 214 Lincoln Place signed yesterday. Here is what Alan wants from you this week (the objectives). Work it the way you would on Monday. Say out loud what you are looking at and why. I will only answer what a colleague would answer.

**For the coordinator:**
- The huddle note with the buy list and the yards is in their news.
- The quotes come back the way the book plants them:
  - one as a table;
  - one as a PDF with a typo price;
  - one in prose with no lead time;
  - one tile quote by the box.
- At about 20 minutes in, ring their phone as Gowanus. The 1/2" cement board is backordered; offer Durock at the same price.

**For billing:**
- The "contract signed" note is in their news.
- The deposit lands at the bank. The vanity change is approved.
- At about 15 minutes in, send them David Klein's mail asking about the retainage.

**The conductor:**
- Answers as the vendor or the client would, from the book's text.
- Never says what to click.
- Never names a leak.

## What to record, step by step
| What | How |
|---|---|
| The order they did things in | the clock at the start of each task |
| How long each step took | from the first look to the save or send |
| Where they stopped or hesitated (more than 20 seconds with no action) | the clock, the screen, what they said |
| What they checked before they called something done | e.g. "looked at the PO against the quote", "opened the job's costs after the PO" |
| What they looked for and could not find, and where they expected it | their words |
| What they did with the messy inputs | the typo price, the missing lead time, the per-box price, the backorder call |
| Whether they caught each planted leak, and how | the drywall over its line, the stock already on the shelf, Nemo's price against last time; for billing, the pendants and the measured % |
| What they would have done outside the app | a call, a text, a spreadsheet, a note on paper |
| What they said they would do next week that the agents never do | their words |

## Afterwards (the conductor, 30 minutes)
1. Run `sim/simctl referee` on the calibration world. The Business cycle section shows their steps and their leaks on the same table as the agents'.
2. Write `docs/pilot/pilot3/calibration_<role>.md`, comparing the person with the agent playing the same role in the pilot:
   - order of work;
   - time per step;
   - checks made;
   - stops;
   - leaks caught;
   - the reasons given.
   Use the agent's trail from `sim/simctl judge <uid>` and the referee's step and leak tables.
3. Change from it:
   - **the role cards**, where the real person's habits differ: what they check first, what they never skip;
   - **the judge's flags**, where something the judge would flag is what the real person does, or the reverse;
   - **the minutes per action** in `sim/server.py` (`MINUTES`), where the real times differ by more than half.
4. Real names, real vendors and real figures from the session stay out of the repo. Write what was learned in invented terms: "the coordinator checks the last price before the quote," not who said it.
