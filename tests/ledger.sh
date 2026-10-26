#!/bin/bash
# The run ledger (docs/PROCESS.md rule 6: never run the same thing twice on the same build). tests/slot.sh runs every
# suite through this once it holds a slot: the command runs unchanged (stdout is copied, stderr untouched, the exit
# code kept) and one row goes into the machine's ledger: when, the build's hash, where and what ran, PASS or FAIL,
# the seconds, and the suite's last line. tests/run_once.sh reads it to skip a suite already green on the same build.
# The ledger is shared by every worktree: <main checkout>/review/runs.md (git-ignored), or SD_RUNS_LEDGER.
#   tests/ledger.sh --hash      the build hash this checkout would record
#   tests/ledger.sh --ledger    where the ledger is
here="$(cd "$(dirname "$0")" && pwd)"
root="$(cd "$here/.." && pwd)"
ledger_path() {
  if [ -n "$SD_RUNS_LEDGER" ]; then echo "$SD_RUNS_LEDGER"; return; fi
  local common; common="$(git -C "$root" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)"
  if [ -n "$common" ] && [ -d "$common" ]; then echo "$(dirname "$common")/review/runs.md"; else echo "$root/review/runs.md"; fi
}
build_hash() {   # the build under test: the hash of the assembled single-file app (first 12 hex)
  local f="${SIM_DIST:-$root/dist/smartdesigns_projects.html}"
  if [ -f "$f" ]; then sha256sum "$f" | cut -c1-12; else echo "no-build"; fi
}
where() { local p; p="$(pwd)"; case "$p" in "$root") echo "." ;; "$root"/*) echo "${p#"$root"/}" ;; *) echo "$p" ;; esac; }
if [ "$1" = "--hash" ]; then build_hash; exit 0; fi
if [ "$1" = "--ledger" ]; then ledger_path; exit 0; fi
L="$(ledger_path)"; mkdir -p "$(dirname "$L")"
h="$(build_hash)"; w="$(where)"; cmd="$*"; t0=$(date +%s); when="$(date '+%Y-%m-%d %H:%M:%S')"
out="$(mktemp)"
"$@" | tee "$out"
rc=${PIPESTATUS[0]}
last="$(grep -v '^[[:space:]]*$' "$out" | tail -n 1 | tr '|' '/' | cut -c1-200)"
rm -f "$out"
res=FAIL; [ "$rc" -eq 0 ] && res=PASS
(
  flock 8
  [ -s "$L" ] || printf '# The run ledger (tests/ledger.sh; docs/PROCESS.md rule 6)\n\n| When | Build | Where | Suite | Result | Seconds | Last line |\n|---|---|---|---|---|---|---|\n' > "$L"
  printf '| %s | %s | %s | %s | %s | %s | %s |\n' "$when" "$h" "$w" "$cmd" "$res" "$(( $(date +%s) - t0 ))" "$last" >> "$L"
) 8>>"$L.lock"
exit "$rc"
