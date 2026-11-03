"""clock_lint: one clock (CLAUDE.md "One clock"; BACKLOG section 9 item 1). A source lint, no browser.

The app's day is today() and its time appNow() / appNowIso() / stampText(). The wall clock (new Date() with no argument,
Date.now(), tzToday(), tzNow()) may stand only where it measures time passing on this machine (a timer, a debounce, a
token's expiry), never where a record is stamped or a day is decided. Each use of it in src/*.js is allowed when:
  - it sits in a clock function (CLOCK_FNS: the functions that define the app clock), or
  - it is arithmetic or a comparison on the same line (Date.now() - t0, Date.now() < until, Date.now() + 4e3), which
    measures time passing and is never stored as a date, or
  - its line (or the line above) carries the comment "wall clock:" with the reason (a timer's start, a real mailbox's
    cursor, a recording's length).
A name is never a reason: `rec.createdAt = Date.now()` or `{ at: Date.now() }` is a stamp until someone writes why it is
not (review, 11-03: an "...At = " rule let three such stamps pass). Anything else fails, so a new wall-clock stamp fails
here the day it is written. Why the screen checks missed it: ONE_CLOCK in tests/lint.py reads dates printed on screen,
and a stamp shows only as a relative age ("passed 81 days ago").
Usage: python3 clock_lint.py [--selftest]   (prints each offence as file:line; exit 1 on any)"""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
CLOCK_FNS = ('tzParts', 'tzPartsRaw', 'appClock', 'fmtYear', 'tzToday', 'tzNow', 'tzTime', 'appDay', 'appDayPinned')
USE = re.compile(r'new Date\(\)|Date\.now\(\)|\btzToday\(\)|\btzNow\(\)')
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


def offences(name, text):
    lines = text.split('\n')
    spans = fn_spans(lines)
    bad = []
    for i, l in enumerate(lines):
        for m in USE.finditer(l):
            if any(a <= i <= b for a, b in spans): continue
            if 'wall clock:' in l or (i and 'wall clock:' in lines[i - 1]): continue
            if l.lstrip().startswith('//'): continue
            if m.group(0) == 'Date.now()' and ELAPSED.search(l): continue
            bad.append(f'{name}:{i + 1}: {l.strip()[:160]}')
            break
    return bad


def check():
    bad = []
    for f in sorted(os.listdir(SRC)):
        if f.endswith('.js'): bad += offences(f, open(os.path.join(SRC, f), encoding='utf-8').read())
    return bad


def selftest():
    """the lint against what it must catch (the review's three) and what it must let pass"""
    must_fail = ['rec.createdAt = Date.now();', 'const x = { at: Date.now(), by: "me" };', 'p.receivedAt = Date.now();',
                 'r.date = new Date().toISOString();', 'it.raisedAt = tzToday();']
    must_pass = ['if (Date.now() - t0 > 2e3) return;', 'until = Date.now() + 4e3;', 'press = Date.now(); // wall clock: a press timer',
                 'const t = appNowIso();']
    out = []
    for s in must_fail:
        if not offences('plant.js', s): out.append(f'SELFTEST missed a stamp: {s}')
    for s in must_pass:
        if offences('plant.js', s): out.append(f'SELFTEST flagged a timer: {s}')
    return out


if __name__ == '__main__':
    st = selftest()
    for b in st: print(b)
    if '--selftest' in sys.argv:
        print('SELFTEST', 'PASS' if not st else 'FAIL'); sys.exit(1 if st else 0)
    bad = check()
    for b in bad: print('WALL CLOCK', b)
    print(f'{len(bad)} wall-clock uses outside the clock and timers' + (f'; selftest {len(st)} failed' if st else ''))
    sys.exit(1 if bad or st else 0)
