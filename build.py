#!/usr/bin/env python3
"""Build dist/smartdesigns_projects.html: one self-contained file, as the app has always shipped.
src/head.html (meta, title, fonts) + src/styles.css + src/body.html (shell markup) + docs/STANDARD.md and docs/STANDARD_ES.md (as data)
+ src/app.js + src/mind.js + src/subs.js + src/assistant.js + src/livejobs.js + src/reports.js
+ src/costintel.js + src/specialists.js + src/tasks.js (the one task list and sheet) + src/taskviews.js (its Table, Board, Calendar and saved views) + src/meeting.js (the task record
and Meeting Mode) + src/teamws.js (the team's workspace and the Asana import) + src/meetdoc_core.js and src/mtreview.js (the meeting transcript and its review) + src/p0money.js + src/phonerows.js (one phone row for every list the phone opens) + src/p2fix.js + src/p2nav.js + src/buyboard.js (the Buy Board) + src/items.js + src/field_es.js + src/field_es_words.js (the SRC list below)."""
import os, subprocess, sys
H = os.path.dirname(os.path.abspath(__file__))
r = lambda p: open(os.path.join(H, p), encoding='utf-8').read()
# src/mind.js (how the assistant thinks: its reach, prompt, loop, check and learning) and src/assistant.js (the one
# assistant per person, BACKLOG §1.27/§1.24: its screens) ride after app.js in the same script, in that order, so
# assistant.js's wrappers are the outermost ones and every name app.js declares is in scope. src/subs.js (subcontracts
# and the payment check, BACKLOG §1.10 #1 and §1.12) rides between them: it wraps app.js's money paths and adds its
# query tables to mind.js's MD_VIEWS. src/livejobs.js (BACKLOG §1.25/§1.26: two payers, ranges and phases, the cost
# model and tax credits, the contractor) rides after the assistant, then src/reports.js (BACKLOG §1.13: the report
# ties, P&L by project and client, line income to cost, the cash forecast), which reads every lane's records, then
# src/costintel.js (BACKLOG §1.29: jobs spending more than they bring in, the receipt price book, benchmarks, the
# driver's route), then src/specialists.js (BACKLOG §1.28-§1.32: a checklist per role over the existing detectors, the six steps on each
# finding, the savings ledger and workload), which reads every detector the lanes before it registered. src/items.js (one item library that fills every
# line, BACKLOG §1.18) and src/field_es.js (the field's screens in Spanish, §1.20) ride last: their wrappers are
# outermost, and the Spanish pass reads every screen as finally drawn. src/loop_core.js (the improvement loop's pure rules,
# shared with the server's nightly run) and src/loop.js (the loop in the app, BACKLOG §1.19 and §1.32) ride before them.
SRC = ('src/app.js', 'src/mind.js', 'src/subs.js', 'src/assistant.js', 'src/livejobs.js', 'src/reports.js', 'src/loop_core.js', 'src/loop.js', 'src/meetread.js', 'src/costintel.js', 'src/specialists.js', 'src/tasks.js', 'src/taskviews.js', 'src/meeting.js', 'src/teamws.js', 'src/meetdoc_core.js', 'src/mtreview.js', 'src/p0money.js', 'src/phonerows.js', 'src/p2fix.js', 'src/p2nav.js', 'src/buyboard.js', 'src/clientdocs.js', 'src/items.js', 'src/field_es.js', 'src/field_es_words.js')
js = '\n'.join(r(f) for f in SRC)
for f in SRC:
    if subprocess.run(['node', '--check', os.path.join(H, f)]).returncode:
        sys.exit(f + ' has a syntax error; not building')
# The script ships as ASCII (speed, BACKLOG §1.11 item 5). One em dash anywhere makes the browser hold all 11 MB of
# the script two bytes a character, and decoding and tokenizing it took about 0.4 s longer on a throttled phone
# before the first line ran. Every character past ASCII is written as its \u escape, which means the same thing in a
# string, a template, a regular expression (with or without the u flag: a pair stands for one character) and a
# comment. Two places would read it differently, so the build refuses them: String.raw (it keeps the escape as
# typed) and a backslash right before the character.
import re
for m in re.finditer(r'String\.raw`', js):
    end = m.end()
    while js[end] != '`': end += 2 if js[end] == '\\' else 1
    if re.search(r'[^\x00-\x7f]', js[m.end():end]):
        sys.exit('a String.raw template holds a character past ASCII; write it as a ${"\\u…"} part: ' + js[m.start():m.start() + 80])
if re.search(r'\\[^\x00-\x7f]', js):
    sys.exit('a backslash stands before a character past ASCII; drop the backslash or write the \\u escape')
u16 = lambda c: [ord(c)] if ord(c) < 0x10000 else [0xD800 + ((ord(c) - 0x10000) >> 10), 0xDC00 + ((ord(c) - 0x10000) & 0x3FF)]
js = re.sub(r'[^\x00-\x7f]', lambda m: ''.join('\\u%04x' % u for u in u16(m.group())), js)
# The SmartDesign Standard (docs/STANDARD.md, Alan's own document) rides in the page word for word: the app seeds
# its live, versioned copy from it (standardParse in src/app.js), so the text is loaded, never paraphrased in code.
std = r('docs/STANDARD.md').replace('</script', '<\\/script')
# The field's parts of the Standard in Spanish (docs/STANDARD_ES.md, BACKLOG §1.20): shown to a field person whose
# language is Spanish; Alan's English stays the source, and the page says when the English has moved on.
std_es = r('docs/STANDARD_ES.md').replace('</script', '<\\/script')
out = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n' + r('src/head.html') +
       '<style>\n' + r('src/styles.css') + '</style>\n</head><body>\n' + r('src/body.html') +
       '\n<script type="text/plain" id="sd-standard-md">\n' + std + '</script>' +
       '\n<script type="text/plain" id="sd-standard-es-md">\n' + std_es + '</script>' +
       '\n<script>\n' + js.replace('</script', '<\\/script') + '\n</script>\n</body></html>\n')
os.makedirs(os.path.join(H, 'dist'), exist_ok=True)
open(os.path.join(H, 'dist/smartdesigns_projects.html'), 'w', encoding='utf-8').write(out)
print('built dist/smartdesigns_projects.html', len(out), 'bytes')
