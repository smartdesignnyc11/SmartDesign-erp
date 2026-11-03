"""clock_lint: one clock (CLAUDE.md "One clock"; BACKLOG section 9 item 1). A source lint, no browser.

The app's day is today() and its time appNow() / appNowIso() / stampText(). The wall clock (new Date() with no argument,
Date.now(), tzToday(), tzNow()) may stand only where it measures time passing on this machine (a timer, a debounce, a
token's expiry), never where a record is stamped or a day is decided. Each use of it in src/*.js is allowed when:
  - it sits in a clock function (CLOCK_FNS: the functions that define the app clock), or
  - it measures elapsed time or a deadline: Date.now() in arithmetic or a comparison, or assigned to a timer name
    (...At, ...Ms, ...Until, t0, t1, now, start, wall), or
  - its line carries the comment "wall clock:" with the reason (a real mailbox's cursor, a recording's length).
Anything else fails, so a new wall-clock stamp fails here the day it is written. Why the old checks missed it: ONE_CLOCK
in tests/lint.py reads the dates printed on screen, and a stamp shows only as a relative age ("passed 81 days ago").
Usage: python3 clock_lint.py   (prints each offence as file:line and the line; exit 1 on any)"""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
CLOCK_FNS = ('tzParts', 'tzPartsRaw', 'appClock', 'fmtYear', 'tzToday', 'tzNow', 'tzTime', 'appDay', 'appDayPinned')
USE = re.compile(r'new Date\(\)|Date\.now\(\)|\btzToday\(\)|\btzNow\(\)')
TIMER_NAME = re.compile(r'(?:\b\w*(?:At|Ms|Until|Time)|\bt[0-9]?|\bnow|\bstart|\bwall|\bat|\bpress|\bt)\s*[:=]\s*$')
ELAPSED = re.compile(r'Date\.now\(\)\s*[-+<>]|[-+<>]=?\s*Date\.now\(\)|Math\.floor\(Date\.now\(\)\s*/')


def fn_spans(lines):
    """the line spans of the clock functions (a function or a const arrow, to the end of its body by brace depth)"""
    spans = []
    for i, l in enumerate(lines):
        m = re.match(r'\s*(?:function\s+(\w+)|(?:const\s+|,\s*|let\s+)?(\w+)\s*=\s*(?:\([^)]*\)|\w+)\s*=>)', l)
        name = m and (m.group(1) or m.group(2))
        if name not in CLOCK_FNS: continue
        depth, j, opened = 0, i, False
        while j < len(lines):
            depth += lines[j].count('{') - lines[j].count('}')
            opened = opened or '{' in lines[j]
            if opened and depth <= 0: break
            if not opened and j > i: break
            j += 1
        spans.append((i, j))
    return spans


def check():
    bad = []
    for f in sorted(os.listdir(SRC)):
        if not f.endswith('.js'): continue
        lines = open(os.path.join(SRC, f), encoding='utf-8').read().split('\n')
        spans = fn_spans(lines)
        for i, l in enumerate(lines):
            for m in USE.finditer(l):
                if any(a <= i <= b for a, b in spans): continue
                if 'wall clock:' in l or (i and 'wall clock:' in lines[i - 1]): continue
                if l.lstrip().startswith('//'): continue
                tok = m.group(0)
                if tok == 'Date.now()':
                    if ELAPSED.search(l): continue
                    if TIMER_NAME.search(l[:m.start()]): continue
                bad.append(f'{f}:{i + 1}: {l.strip()[:160]}')
    return bad


if __name__ == '__main__':
    bad = check()
    for b in bad: print('WALL CLOCK', b)
    print(f'{len(bad)} wall-clock uses outside the clock and timers')
    sys.exit(1 if bad else 0)
