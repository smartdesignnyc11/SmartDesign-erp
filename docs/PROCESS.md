# How we work: the process rules and why each one exists (Alan, 10-26)

> "You have to be constantly checking how we do things to find ways to improve the process and not spend time needlessly ... you don't want to do the same things twice or do things without fully thinking everything through."

Each rule below comes from time we lost this week. Every iteration of the improvement loop ends with a short retro: what cost time without a result, and the one rule that changes because of it. The retro is added here.

## Before anything is built
1. **Evidence means a person doing the work.** A check counts as evidence only if it does the job the way a person does: through the screens, from a blank start, on the phone and the desktop, with the outcome checked in the records. Function calls and view jumps on seeded data prove the code runs, not that the work can be done. *(Lost: weeks of green nets while the PM could not add a line to an estimate on the phone.)*
2. **No lane without a failing journey step.** Every lane starts from a step in `docs/JOURNEYS.md` that fails in `tests/cycle_walk.py`, and it is done when that step passes on both devices. If the problem cannot be written as a failing step, it is not understood yet: think, do not build. *(Lost: lanes that fixed what their own checks measured.)*
3. **Finish the core before adding.** No new module or feature while any of the ten journeys fails, unless Alan asks for it by name. *(Lost: a 159k-line file that grew sideways while the core path stayed broken.)*

## Before anything is measured
4. **Test the instrument first.** Every new harness, pilot or walk runs one turn or one journey as a dry run, and its output is read critically, before the full run is paid for. *(Lost: Pilot 3 spent four turns before two harness faults were found, Ask not found and news dropped. Both would have shown in one turn.)*
5. **The instrument must see what a person sees:**
   - the page as a picture as well as text;
   - the live site with sign-in and sync, not only a local copy;
   - a world that answers like real people;
   - memory between turns;
   - the real assistant.

   Any gap is written next to the result it limits. *(Lost: half the puzzle unseen.)*
6. **Never run the same thing twice on the same build.** Results are kept by build hash (`review/runs.md`). A suite already green on an unchanged build is not re-run. Only what a change touches is re-run, plus the month walk and the screen walk before a deploy. *(Lost: hours of nets re-run after a docs-only change.)*

## While building
7. **One or two lanes, never sharing files; two test tiers (Alan, 10-26: "why does it feel like everything is taking 8x longer?").**
   - **Review first.** The chief of staff reads a lane's diff as soon as its code is done, before the long tests. *(Lost 10-26: the estimate lane's 2-hour net ran before the review found two money faults, so it runs again.)*
   - **The fast tier, per lane and per merge (about 20 to 30 minutes):** smoke, the suites of the modules touched, the lane's own new checks, and the screen walk. A lane hands back on the fast tier.
   - **The full tier, once per deploy batch:** everything in the net, the drafts check (sharded by role across the slots) and the month walk, on the merged head that will ship. Lanes merged in one batch share one full tier.
   - **Lanes do not merge master mid-work** unless a conflict forces it; the main session merges. *(Lost 10-26: the estimate lane merged master twice and re-ran its net twice.)*
   *(Lost before: four lanes green alone and red together; a month walk that collapsed because no lane had run it. The full tier on the merged batch still catches that.)*
8. **A pinned check changes only for an approved design.** The commit names which design changed what the check pins. Otherwise the app is wrong, not the check.
9. **Ask what the checks did not check.** Before calling anything done, name the class of thing no check covers and either add the check or say plainly that it is uncovered.

## Reporting to Alan
10. **Progress is journeys passing, N of 10 per device,** with what each rests on and what is uncertain. Never lanes merged or checks green.
11. **Recommend, and warn before heavy usage.** One recommendation with its cost, not a list of options.

## Retro log
| Date | What cost time without a result | The rule that changed |
|---|---|---|
| 10-26 | Green nets while real work failed; harness faults found after four turns; four lanes colliding at integration; re-running nets on unchanged builds | rules 1 to 7 written |
- **10-26, afternoon.** Alan: everything takes 8x longer. Measured: a full net is 2 to 3 hours of wall time (drafts 100 min, month 60, walk 18) on four slots; today three merges each paid it, the estimate lane's review came after its net and sent it back, and an hour went to a drafts failure that was the check's own. Changed rule 7: review first, a fast tier per lane, one full tier per deploy batch, lanes stop chasing master, the drafts check sharded by role. Expected: lane to live from about 8 to 9 hours to 4 to 5. Measure it on the next two lanes.
- **10-26, first batch under rule 7.** The estimate lane's two fixes came back in 35 minutes on the fast tier (its first hand-back took 5.5 hours with full nets). The full tier on the merge took about 55 minutes of wall time; the sharded drafts check was 21 to 33 minutes per shard but shared four slots with the other suites and the lane. Sharding also exposed a failure the single run never reached (a sheet family's Keep and Discard check now lands on another person's sheet); it is the same on the live build. Lesson: a shard order changes which sheet a per-family check sees, so per-family checks should run on every family member in turn across runs, not only the first.
- **10-26, round one.** What cost time without a result: five journeys the walk does not check and the worlds could not stage (no delivery for J7, no controller seat for J10); caps that cut the journeys (40 actions, 8 pictures); an hour behind a sheet the reader could not see; and experts re-finding what two built, unmerged lanes claim to fix. The rule that changes (rule 4): the dry run tests the instrument against the whole round, not one turn. Before a round, the walk covers every journey the experts are graded on, each world holds the event and the seat its journey needs, and no built lane sits unmerged.
- **10-26, evening: lane 1 held three times, each time for money logic the lane's own checks did not reach.** Each hold came from the reviewer probing the ledger directly (a payment counted twice; progress revenue in Customer Deposits; a deposit liability never paid down; a title edit re-booking posted money). The lane tested the screens it changed; the books behind them were tested only by the reviewer. Rule added to 9: a lane that touches money adds ledger invariants to its own checks before it hands back (every deposit nets to zero once billed; collected never exceeds what the bank backs; no edit to a sent or paid document changes the books; one question about a record is answered by one function), and the finance cross-check grows to hold them for every later lane.
- **11-12, the expert round on the live build.** What cost: features released on 11-06 and 11-07 without an expert doing the work through the screens carried S1s to live, and they stayed there until Alan asked for an all-out hour. The experts found 14 S1s on live in wave 2; 11 of them came in with those releases (the main session's first count was 6; the 11 are listed in BACKLOG §11, S1 rows 2 to 12). The nets were at their known state each time: they checked what the lanes had built, not whether a coordinator, a bookkeeper or a foreman could trust what the screen said.
  - **The rule that follows: no release without the seat's expert walking it.** The expert of each seat a release touches does the changed work through the screens on the built release, on both devices, and the release row says who walked what and what was not reached. It sharpens rule 1: an expert day before the build is not a walk of the build. Alan may waive it for a named release, and the row says so (waiting on his yes, DECISIONS 11-12).
  - **This week's releases that skipped it: all five.**
    - 11-06 18:20 (b799fca), purchasing and phone tasks: experts worked the screens before the build, nobody after.
    - 11-06 21:20 (308c1ba), automatic clock-in: no walk. Four S1s (two switches, the overlap approved, the hidden punch, the silent second punch).
    - 11-07 15:20 (a504d66), the item table and bills against receipts: no walk, and it shipped on "ship now" with the tier red (rfq_test, leaks2 [8], the month 5 schedule days short). Seven S1s (five on the item table; Hold at What Arrived reading $0; a bill over what arrived raising no control).
    - 11-09 (47ce749), quantity on progress bills, and 11-09 (64d2246), the Controller's job pages: no walk, and the month, drafts and screen walk were not re-run. No expert has reached either yet, so they are unjudged, not clean.
  - **Also from the hour, for the next retro to measure:** eleven lanes ran at once against rule 7, eight of them in `src/app.js`; one expert pass lost its ten minutes to a script that imported a whole suite (rule 4, test the instrument first); and three live S1s were older than this week (Record Payment's default, the two EAC figures, the three over-billed numbers), so the release rule alone would not have caught them. Each seat still needs a full walk of what is already live.
