#!/usr/bin/env python3
"""Build the hosted copy into platform/public/: the app (dist/smartdesigns_projects.html, built first by ../build.py)
with the cloud layer, the Supabase client, the service worker and the PWA tags added to its head.
config.js carries only public values (the project URL and the anon key, which row security makes safe to ship);
SDP_SUPABASE_URL and SDP_SUPABASE_ANON_KEY set them, or the build fetches them through the Supabase management API."""
import os, re, sys, json, shutil, hashlib, subprocess, urllib.request
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(H); PUB = os.path.join(H, 'public')
REF = os.environ.get('SDP_SUPABASE_REF', 'eenpabyrmiltfqvzirhw')
# SDP_APP_HTML names an app build made elsewhere (so a deploy never rewrites dist/ under a running test net).
APP = os.environ.get('SDP_APP_HTML')
if not APP:
    if subprocess.run([sys.executable, os.path.join(ROOT, 'build.py')]).returncode: sys.exit('app build failed')
    APP = os.path.join(ROOT, 'dist', 'smartdesigns_projects.html')
html = open(APP, encoding='utf-8').read()
# The improvement loop's rules are one file (src/loop_core.js) run by the app and by the nightly function: the
# functions get a byte-for-byte copy (test/loop_test.mjs fails when the two differ).
shutil.copyfile(os.path.join(ROOT, 'src', 'loop_core.js'), os.path.join(H, 'netlify', 'functions', 'lib', 'loop_core.cjs'))
url = os.environ.get('SDP_SUPABASE_URL') or f'https://{REF}.supabase.co'
anon = os.environ.get('SDP_SUPABASE_ANON_KEY')
if not anon:
    with urllib.request.urlopen(f'https://api.supabase.com/v1/projects/{REF}/api-keys') as r:
        anon = [k['api_key'] for k in json.load(r) if k['name'] == 'anon'][0]
# the Supabase browser client, vendored so the app does not depend on a CDN at boot
sbjs = os.path.join(H, 'node_modules', '@supabase', 'supabase-js', 'dist', 'umd', 'supabase.js')
if not os.path.exists(sbjs):
    subprocess.run(['npm', 'ci', '--silent', '--prefix', H], check=True)
shutil.rmtree(os.path.join(PUB, 'vendor'), ignore_errors=True)
shutil.copytree(os.path.dirname(sbjs), os.path.join(PUB, 'vendor'))   # supabase.js and the chunk it loads on demand
# Google sign-in shows on the sign-in screen only once the Google provider is switched on in Supabase.
google = os.environ.get('SDP_GOOGLE_SIGNIN')
if google is None:
    try:
        with urllib.request.urlopen(f'https://api.supabase.com/v1/projects/{REF}/config/auth') as r: google = '1' if json.load(r).get('external_google_enabled') else ''
    except Exception: google = ''
# The public half of the push key (the private half is a Netlify secret), read from the site's settings.
vapid = os.environ.get('SDP_VAPID_PUBLIC_KEY', '')
if not vapid:
    try:
        with urllib.request.urlopen('https://api.netlify.com/api/v1/accounts/alan-i60sjeo/env/VAPID_PUBLIC_KEY?site_id=1bdb5200-477c-492a-8294-fb475014deaa') as r:
            vapid = [v['value'] for v in json.load(r)['values']][0]
    except Exception: vapid = ''
ver = hashlib.md5((html + open(os.path.join(PUB, 'cloud.js')).read()).encode()).hexdigest()[:8]
open(os.path.join(PUB, 'config.js'), 'w').write(
    '// Public values only. The Anthropic key and the service key live in Netlify, never here.\n'
    'window.SDP_CONFIG = ' + json.dumps({'appName': 'SmartDesigns Projects', 'supabaseUrl': url, 'supabaseAnonKey': anon, 'aiUrl': '/api/ai', 'functions': '/api', 'googleSignIn': bool(google), 'vapidPublicKey': vapid, 'build': ver}) + ';\n')
tags = f'''<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<script src="vendor/supabase.js?v={ver}"></script>
<script src="config.js?v={ver}"></script>
<script src="cloud.js?v={ver}"></script>
<script>if ('serviceWorker' in navigator && location.protocol === 'https:') addEventListener('load', () => navigator.serviceWorker.register('sw.js').catch(e => console.warn('sw', e)));</script>
'''
# ../build.py starts the page with this exact head opening; the app's own code holds other '</head>' strings (print views)
OPEN = '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n'
assert html.startswith(OPEN), 'the app shell no longer starts with the head ../build.py writes'
open(os.path.join(PUB, 'index.html'), 'w', encoding='utf-8').write(OPEN + tags + html[len(OPEN):])
sw = open(os.path.join(H, 'sw.src.js')).read()
open(os.path.join(PUB, 'sw.js'), 'w').write(re.sub(r"const VERSION = '[^']*';", f"const VERSION = 'sdp-{ver}';", sw))
print('built platform/public', ver)
