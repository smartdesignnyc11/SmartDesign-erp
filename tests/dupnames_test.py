"""Static check: no top-level function name is declared twice across the build.
build.py joins every file in SRC into one script, so a second `function name(` anywhere replaces the first one
everywhere, silently, before any wrapper runs. Found 2026-10-20: reports.js declared its own `function rpOpen`
(the report drill-down), which replaced Report a Problem's rpOpen, so the Report a Problem button opened nothing on
every screen and no test noticed. The wrapper pattern (`const base = fn; fn = function () {...}`) is the way to change
a function; a new name is the way to add one.
Run: python3 dupnames_test.py"""
import os, re, sys, collections
H = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(H)
SRC = re.findall(r"'([^']+)'", re.search(r"SRC = \((.*?)\)", open(os.path.join(ROOT, 'build.py'), encoding='utf-8').read()).group(1))
seen = collections.defaultdict(list)
for f in SRC:
    for i, line in enumerate(open(os.path.join(ROOT, f), encoding='utf-8')):
        # a top-level const, let or class as well (2026-10-21: the tasks lane's `const tkFirst` and the fix lane's
        # `function tkFirst` met on a merge and the page stopped booting: "Identifier has already been declared")
        m = re.match(r'^(?:(?:async )?function\*? ?([A-Za-z_$][\w$]*)\s*\(|(?:const|let|class) ([A-Za-z_$][\w$]*)\b)', line)
        # (a const, let or class declared twice does not replace the first: the whole script refuses to run)
        if m: seen[m.group(1) or m.group(2)].append(f'{f}:{i + 1}')
fails = [f'{k} is declared {len(v)} times: {", ".join(v)} (the last one replaces the others everywhere)' for k, v in sorted(seen.items()) if len(v) > 1]
for x in fails: print('FAIL', x)
print(f'{len(fails)} FAILED ({len(seen)} names in {len(SRC)} files)' if fails else f'ALL PASS ({len(seen)} names in {len(SRC)} files)')
sys.exit(1 if fails else 0)
