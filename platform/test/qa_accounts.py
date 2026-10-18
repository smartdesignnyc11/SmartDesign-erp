"""Create (or reset) the QA accounts the live checks sign in as, all in the 'qa' workspace, never the firm's.
Writes their emails and fresh random passwords to a JSON file OUTSIDE the repo. --delete removes them.
Run: python3 test/qa_accounts.py /abs/path/qa_users.json [--delete]
Uses the Supabase management API (the session's injected credentials) to read the service key; nothing is printed."""
import json, os, secrets, sys, urllib.request, urllib.error
REF = os.environ.get('SDP_SUPABASE_REF', 'eenpabyrmiltfqvzirhw'); BASE = f'https://{REF}.supabase.co'
ROLES = {'owner': 'owner', 'foreman': 'foreman', 'crew': 'crew', 'nobody': 'none', 'client': 'client'}
out_path = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else sys.exit(__doc__)
repo = os.path.realpath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if not os.path.isabs(out_path) or os.path.realpath(out_path).startswith(repo + os.sep): sys.exit('the accounts file must be an absolute path outside the repo')
svc = [k['api_key'] for k in json.load(urllib.request.urlopen(f'https://api.supabase.com/v1/projects/{REF}/api-keys')) if k['name'] == 'service_role'][0]
def call(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={'apikey': svc, 'authorization': 'Bearer ' + svc, 'content-type': 'application/json', 'prefer': 'return=representation'})
    try:
        with urllib.request.urlopen(req) as r: t = r.read().decode(); return json.loads(t) if t else None
    except urllib.error.HTTPError as e: return {'error': e.code, 'body': e.read().decode()[:200]}
users = call('GET', '/auth/v1/admin/users?per_page=200').get('users', [])
existing = {u['email']: u['id'] for u in users if u['email'].startswith('qa-') and u['email'].endswith('@example.com')}
if '--delete' in sys.argv:
    for email, uid in existing.items(): call('DELETE', '/auth/v1/admin/users/' + uid)
    print('deleted', len(existing)); sys.exit(0)
acc = {}
for key, role in ROLES.items():
    email = f'qa-{key}@example.com'; pw = secrets.token_urlsafe(18)
    if email in existing: uid = existing[email]; call('PUT', '/auth/v1/admin/users/' + uid, {'password': pw})
    else: uid = call('POST', '/auth/v1/admin/users', {'email': email, 'password': pw, 'email_confirm': True})['id']
    call('PATCH', '/rest/v1/profiles?id=eq.' + uid, {'role': role, 'workspace_id': 'qa', 'name': 'QA ' + key})
    acc[key] = {'email': email, 'password': pw, 'id': uid}
fd = os.open(out_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
with os.fdopen(fd, 'w') as f: json.dump(acc, f)
print('ready', ', '.join(acc), '->', out_path)
