#!/bin/bash
# The drafts check in four shards by role, each through slot.sh, in parallel (PROCESS.md rule 7, 10-26: one full run was
# 100 minutes on one slot). Each shard writes review/w1trust/shard<N>/; the last line sums the four.
# Usage: tests/drafts_shards.sh [extra drafts_test args, e.g. --quiet]
cd "$(dirname "$0")"; R=../review/w1trust
SHARDS=("u_owner,u_klein" "u_alan,u_sarah,u_alex" "u_chen,u_angel,u_alberto" "u_billing,u_controller")
for i in 0 1 2 3; do
  mkdir -p $R/shard$i
  SD_DRAFTS_OUT=$R/shard$i ./slot.sh timeout 5400 python3 -u drafts_test.py --user "${SHARDS[$i]}" "$@" > $R/shard$i/run.log 2>&1 &
done
wait
rc=0; for i in 0 1 2 3; do grep -E "^FAIL" $R/shard$i/run.log; tail -1 $R/shard$i/run.log | grep -q "ALL PASS" || rc=1; done
for i in 0 1 2 3; do echo "shard$i (${SHARDS[$i]}): $(grep -E '^(ALL PASS|[0-9]+ FAILED)' $R/shard$i/run.log | tail -1) | $(tail -1 $R/shard$i/run.log)"; done
[ $rc = 0 ] && echo "DRAFTS SHARDS ALL PASS" || echo "DRAFTS SHARDS FAILED"
exit $rc
