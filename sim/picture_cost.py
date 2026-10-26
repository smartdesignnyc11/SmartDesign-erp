#!/usr/bin/env python3
"""sim/picture_cost.py: what one screen picture costs an expert, measured (docs/IMPROVEMENT_LOOP.md, cost).

Sends the same one-line question twice through the live AI door (/api/ai), once with no picture and once with the
picture, and reports the difference in input tokens: the tokens one picture adds every time a model reads it. It asks
for a one-token answer, so a measurement costs about a cent. The session token is a signed-in QA member's
(SIM_AI_TOKEN_FILE, as the sim's assistant uses; never written to the repo).

    SIM_AI_TOKEN_FILE=/abs/token python3 sim/picture_cost.py <picture.jpg> [<picture.jpg> ...] [--tier brain|assistant|small]
"""
import base64, json, os, ssl, sys, urllib.error, urllib.request

AI_URL = os.environ.get('SIM_AI_URL', 'https://smartdesigns-erp.netlify.app').rstrip('/')


def token():
    f = os.environ.get('SIM_AI_TOKEN_FILE', '')
    t = open(f).read().strip() if f and os.path.exists(f) else os.environ.get('SIM_AI_TOKEN', '').strip()
    if not t: sys.exit('set SIM_AI_TOKEN_FILE (a signed-in QA member\'s session token)')
    return t


def ask(content, tier):
    ca = os.environ.get('SSL_CERT_FILE') or os.environ.get('REQUESTS_CA_BUNDLE')
    ctx = ssl.create_default_context(cafile=ca) if ca and os.path.exists(ca) else ssl.create_default_context()
    body = {'tier': tier, 'max_tokens': 1, 'messages': [{'role': 'user', 'content': content}]}
    req = urllib.request.Request(AI_URL + '/api/ai', data=json.dumps(body).encode(), method='POST',
                                 headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token()})
    try:
        with urllib.request.urlopen(req, timeout=120, context=ctx) as r: j = json.loads(r.read().decode().strip())
    except urllib.error.HTTPError as e: sys.exit(f'the AI door answered {e.code}: {e.read().decode()[:200]}')
    u = j.get('usage') or {}
    return (u.get('input_tokens') or 0) + (u.get('cache_creation_input_tokens') or 0) + (u.get('cache_read_input_tokens') or 0), j.get('model', '')


def measure(path, tier='brain'):
    """(tokens the picture adds, model, width, height, bytes)"""
    q = {'type': 'text', 'text': 'Reply with the single word ok.'}
    base, model = ask([q], tier)
    data = base64.b64encode(open(path, 'rb').read()).decode()
    with_pic, model = ask([{'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/jpeg', 'data': data}}, q], tier)
    w = h = 0
    try:
        from PIL import Image
        w, h = Image.open(path).size
    except Exception: pass
    return with_pic - base, model, w, h, os.path.getsize(path)


if __name__ == '__main__':
    a = sys.argv[1:]
    tier = a[a.index('--tier') + 1] if '--tier' in a else 'brain'
    pics = [x for i, x in enumerate(a) if not x.startswith('--') and (i == 0 or a[i - 1] != '--tier')]
    if not pics: sys.exit(__doc__)
    for p in pics:
        n, model, w, h, b = measure(p, tier)
        print(f'{os.path.basename(p)}: {w}x{h}, {b // 1024} KB -> {n} input tokens on {model}')
