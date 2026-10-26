#!/bin/bash
# Run one suite when one of two machine-wide slots is free: python3 build.py && tests/slot.sh python3 smoke_test.py
# The machine has 15 GB; four browser suites at once (one per lane) restarted the container twice on 2026-10-20.
# Every lane and the main session run their suites through this, so at most four browsers run at a time.
# 2026-10-26: each suite that gets a slot is recorded in the run ledger (tests/ledger.sh, review/runs.md, by build hash);
# tests/run_once.sh skips a suite already green on the same build. The locking is unchanged.
# 2026-10-25: four slots; with two, nine suites queued an hour while memory sat at 2 GB used of 15. Watch the memlog.
L=/tmp/sd-suite-slot
while true; do
  for i in 1 2 3 4; do
    exec 9>"$L$i"
    if flock -n 9; then "$(dirname "$0")/ledger.sh" "$@"; exit $?; fi   # the suite runs unchanged; the run ledger records it
    exec 9>&-
  done
  sleep 5
done
