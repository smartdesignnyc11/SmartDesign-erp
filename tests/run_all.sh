#!/usr/bin/env bash
# Builds, then runs every guard rail one at a time (the machine may be slow) and prints one line per suite.
# Full logs land in review/run_all/. Usage: tests/run_all.sh [suite ...]   (default: all)
# Optional, not in the default list (about 30 minutes): month_sim, a month of the company with a crack ledger
# in review/month/ (tests/run_all.sh month_sim). It exits 1 while anything falls through the cracks.
cd "$(dirname "$0")/.." || exit 1
python3 build.py || exit 1
mkdir -p review/run_all
SUITES=${*:-"baseline_test smoke_test lint counts_lint daywalk finance_xcheck ask_bank leak_test truth_test closetie_test truthpct_test today_test askgen_privacy_test demo_ws_test ops_test client_test purchasing_test appday_test learn_test flow_test leaks2_test track_test"}
rc=0
for s in $SUITES; do
  start=$(date +%s)
  (cd tests && python3 "$s.py" > "../review/run_all/$s.txt" 2>&1); r=$?
  [ $r -ne 0 ] && rc=1
  printf '%-15s %-5s %4ss  %s\n' "$s" "$([ $r -eq 0 ] && echo PASS || echo FAIL)" "$(( $(date +%s) - start ))" "$(grep -v '^\s*$' "review/run_all/$s.txt" | tail -1)"
done
exit $rc
