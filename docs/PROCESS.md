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
