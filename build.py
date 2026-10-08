#!/usr/bin/env python3
"""Build dist/smartdesigns_projects.html: one self-contained file, as the app has always shipped.
src/head.html (meta, title, fonts) + src/styles.css + src/body.html (shell markup) + src/app.js."""
import os, subprocess, sys
H = os.path.dirname(os.path.abspath(__file__))
r = lambda p: open(os.path.join(H, p), encoding='utf-8').read()
js = r('src/app.js')
if subprocess.run(['node', '--check', os.path.join(H, 'src/app.js')]).returncode:
    sys.exit('src/app.js has a syntax error; not building')
out = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n' + r('src/head.html') +
       '<style>\n' + r('src/styles.css') + '</style>\n</head><body>\n' + r('src/body.html') +
       '\n<script>\n' + js.replace('</script', '<\\/script') + '\n</script>\n</body></html>\n')
os.makedirs(os.path.join(H, 'dist'), exist_ok=True)
open(os.path.join(H, 'dist/smartdesigns_projects.html'), 'w', encoding='utf-8').write(out)
print('built dist/smartdesigns_projects.html', len(out), 'bytes')
