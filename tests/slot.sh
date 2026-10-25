#!/bin/bash
# Run one suite when one of two machine-wide slots is free: python3 build.py && tests/slot.sh python3 smoke_test.py
# The machine has 15 GB; four browser suites at once (one per lane) restarted the container twice on 2026-10-20.
# Every lane and the main session run their suites through this, so at most three browsers run at a time.
# 2026-10-25: three slots; with two, nine suites queued an hour while memory sat at 2 GB used of 15.
L=/tmp/sd-suite-slot
while true; do
  for i in 1 2 3; do
    exec 9>"$L$i"
    if flock -n 9; then "$@"; exit $?; fi
    exec 9>&-
  done
  sleep 5
done
