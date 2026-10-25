#!/usr/bin/env bash
# Builds, then runs every guard rail one at a time (the machine may be slow) and prints one line per suite.
# Full logs land in review/run_all/. Usage: tests/run_all.sh [suite ...]   (default: all)
# In the default list since 2026-10-20 (about 30 minutes; chief of staff: no month recorded since v11.2): month_sim, a month of the company with a crack ledger
# in review/month/ (tests/run_all.sh month_sim). It exits 1 while anything falls through the cracks.
# ia_map (about 20 minutes, since 2026-10-21) measures every screen of every role, then holds each check to
# tests/ia_ratchet.json: a check's failures may go down, never up (CONSOLIDATION §2.5).
# chain_test (about 40 minutes) runs one new job end to end and reads every report against its records.
# Optional, not in the default list (a full run takes three to five hours on this build: about 11,000 presses over every
# screen of every role, desktop and phone, each pressed from a fresh state, then each flag pressed again from a
# fresh boot): crawl, the click crawler (tests/run_all.sh crawl). Report in review/crawl/report.md; filter with
# python3 tests/crawl.py --user/--view/--phone/--desktop/--rule while fixing.
cd "$(dirname "$0")/.." || exit 1
python3 build.py || exit 1
mkdir -p review/run_all
SUITES=${*:-"baseline_test smoke_test lint counts_lint daywalk finance_xcheck ask_bank leak_test truth_test closetie_test truthpct_test today_test askgen_privacy_test demo_ws_test ops_test client_test purchasing_test appday_test learn_test flow_test leaks2_test standard_test stock_test rfq_test phone390_test chain_test pricewatch_test track_test task_findable_test meeting_brain_test ranking_test harness_findings_test plans_test pilot_fixes_test xset_test pilot_fixes2_test findable2_test today_lane_test menu_test assistant_lane_test messages_lane_test seed_guard_test shared_system_test made_today_test mind_eval mind_history_test messages2_test read_receipts_test toast_leave_test livejobs_test subs_test payrun_test loop_test meetread_test dupnames_test specialists_test costintel_test speed_test exec_assistant_test field_money_test po_gates_test items_test spanish_test reports_test learn_test today_test tasks_phone_test phone_rows_lint phone_rows_test ia_map s1fix_test month_sim"}
rc=0
for s in $SUITES; do
  start=$(date +%s)
  args=""; [ "$s" = ia_map ] && args="--walk --pre --tasks --report --check"
  (cd tests && ./slot.sh python3 "$s.py" $args > "../review/run_all/$s.txt" 2>&1); r=$?
  [ $r -ne 0 ] && rc=1
  printf '%-15s %-5s %4ss  %s\n' "$s" "$([ $r -eq 0 ] && echo PASS || echo FAIL)" "$(( $(date +%s) - start ))" "$(grep -v '^\s*$' "review/run_all/$s.txt" | tail -1)"
done
exit $rc
