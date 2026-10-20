#!/usr/bin/env python3
"""Build dist/smartdesigns_projects.html: one self-contained file, as the app has always shipped.
src/head.html (meta, title, fonts) + src/styles.css + src/body.html (shell markup) + docs/STANDARD.md (as data)
+ src/app.js + src/mind.js + src/subs.js + src/assistant.js."""
import os, subprocess, sys
H = os.path.dirname(os.path.abspath(__file__))
r = lambda p: open(os.path.join(H, p), encoding='utf-8').read()
# src/mind.js (how the assistant thinks: its reach, prompt, loop, check and learning) and src/assistant.js (the one
# assistant per person, BACKLOG §1.27/§1.24: its screens) ride after app.js in the same script, in that order, so
# assistant.js's wrappers are the outermost ones and every name app.js declares is in scope. src/subs.js (subcontracts
# and the payment check, BACKLOG §1.10 #1 and §1.12) rides between them: it wraps app.js's money paths and adds its
# query tables to mind.js's MD_VIEWS.
js = r('src/app.js') + '\n' + r('src/mind.js') + '\n' + r('src/subs.js') + '\n' + r('src/assistant.js')
for f in ('src/app.js', 'src/mind.js', 'src/subs.js', 'src/assistant.js'):
    if subprocess.run(['node', '--check', os.path.join(H, f)]).returncode:
        sys.exit(f + ' has a syntax error; not building')
# The SmartDesign Standard (docs/STANDARD.md, Alan's own document) rides in the page word for word: the app seeds
# its live, versioned copy from it (standardParse in src/app.js), so the text is loaded, never paraphrased in code.
std = r('docs/STANDARD.md').replace('</script', '<\\/script')
out = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n' + r('src/head.html') +
       '<style>\n' + r('src/styles.css') + '</style>\n</head><body>\n' + r('src/body.html') +
       '\n<script type="text/plain" id="sd-standard-md">\n' + std + '</script>' +
       '\n<script>\n' + js.replace('</script', '<\\/script') + '\n</script>\n</body></html>\n')
os.makedirs(os.path.join(H, 'dist'), exist_ok=True)
open(os.path.join(H, 'dist/smartdesigns_projects.html'), 'w', encoding='utf-8').write(out)
print('built dist/smartdesigns_projects.html', len(out), 'bytes')
