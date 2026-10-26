"""A QA member's session token for the sim's live doors (the assistant through /api/ai, the world's voicer, the picture
cost), written to a file OUTSIDE the repo with mode 0600. A token lasts an hour: --every 40 rewrites it every 40 minutes.
Accounts from SD_QA_USERS (test/qa_accounts.py). Nothing is printed but the length.

    SD_QA_USERS=/abs/qa_users.json python3 test/qa_token.py owner /abs/ai_token [--every 40]
"""
import json, os, sys, time, urllib.request, urllib.error

REF = os.environ.get('SDP_SUPABASE_REF', 'eenpabyrmiltfqvzirhw'); BASE = f'https://{REF}.supabase.co'


def anon():
    return os.environ.get('SDP_SUPABASE_ANON_KEY') or [k['api_key'] for k in json.load(urllib.request.urlopen(f'https://api.supabase.com/v1/projects/{REF}/api-keys')) if k['name'] == 'anon'][0]


def session(who, qa=None, key=None):
    """the access token of QA account `who` (owner, pm, coord, billing, controller, ...)"""
    qa = qa or json.load(open(os.environ.get('SD_QA_USERS') or sys.exit('set SD_QA_USERS')))
    key = key or anon()
    req = urllib.request.Request(BASE + '/auth/v1/token?grant_type=password', method='POST', data=json.dumps({'email': qa[who]['email'], 'password': qa[who]['password']}).encode(),
                                 headers={'apikey': key, 'content-type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read().decode())['access_token']


if __name__ == '__main__':
    if len(sys.argv) < 3: sys.exit(__doc__)
    who, out = sys.argv[1], sys.argv[2]
    repo = os.path.realpath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    if not os.path.isabs(out) or os.path.realpath(out).startswith(repo + os.sep): sys.exit('the token file must be an absolute path outside the repo')
    every = float(sys.argv[sys.argv.index('--every') + 1]) if '--every' in sys.argv else 0
    k = anon()
    while True:
        t = session(who, key=k)
        fd = os.open(out + '.tmp', os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w') as f: f.write(t)
        os.replace(out + '.tmp', out)
        print(time.strftime('%H:%M'), f'{who}: token written ({len(t)} characters)', flush=True)
        if not every: break
        time.sleep(every * 60)
