#!/bin/bash
# Run a suite only if it is not already green on this build (docs/PROCESS.md rule 6). The build is the hash of
# dist/smartdesigns_projects.html; the record is the run ledger tests/ledger.sh keeps (review/runs.md).
#   tests/run_once.sh smoke_test                      a suite in tests/ by name (runs `python3 smoke_test.py` in tests/)
#   cd tests && ./run_once.sh python3 smoke_test.py   any command, keyed by where it runs and what it is
#   tests/run_once.sh --force smoke_test              run it even if it is green on this build
# A skip prints the earlier result and exits 0; otherwise the suite runs through tests/slot.sh (a free slot, the ledger).
here="$(cd "$(dirname "$0")" && pwd)"
force=0; [ "$1" = "--force" ] && { force=1; shift; }
[ $# -ge 1 ] || { sed -n 2,7p "$0"; exit 2; }
if [ $# -eq 1 ] && [ -f "$here/$1.py" ]; then cd "$here" || exit 1; set -- python3 "$1.py"; fi
L="$("$here/ledger.sh" --ledger)"; h="$("$here/ledger.sh" --hash)"
root="$(cd "$here/.." && pwd)"; p="$(pwd)"
case "$p" in "$root") w="." ;; "$root"/*) w="${p#"$root"/}" ;; *) w="$p" ;; esac
cmd="$*"
if [ $force -eq 0 ] && [ "$h" != "no-build" ] && [ -f "$L" ]; then
  hit="$(awk -F' [|] ' -v h="$h" -v w="$w" -v c="$cmd" '$2 == h && $3 == w && $4 == c && $5 == "PASS"' "$L" | tail -n 1)"
  if [ -n "$hit" ]; then
    echo "run_once: skipped \"$cmd\" ($w): already green on build $h"
    echo "run_once: earlier result: $hit"
    exit 0
  fi
fi
exec "$here/slot.sh" "$@"
