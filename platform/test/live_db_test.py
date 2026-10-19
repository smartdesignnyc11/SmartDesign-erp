"""The live database's rules, checked as each kind of person (BACKLOG §5 item 2). Runs against the real Supabase project
with QA accounts in the 'qa' workspace, never the firm's. The accounts come from a JSON file OUTSIDE the repo
(SD_QA_USERS=/abs/path.json: {"owner": {"email","password"}, "foreman": …, "crew": …, "nobody": …, "client": …}).
Make the accounts first: python3 test/qa_accounts.py /abs/qa_users.json
Run: SD_QA_USERS=… python3 test/live_db_test.py   (the AI check costs about a cent)"""
import json, os, sys, urllib.request, urllib.error
REF = os.environ.get('SDP_SUPABASE_REF', 'eenpabyrmiltfqvzirhw'); BASE = f'https://{REF}.supabase.co'
SITE = os.environ.get('SDP_SITE', 'https://smartdesigns-erp.netlify.app')
path = os.environ.get('SD_QA_USERS') or sys.exit('set SD_QA_USERS to the QA accounts file (outside the repo)')
if os.path.realpath(path).startswith(os.path.realpath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) + os.sep):
    sys.exit('the QA accounts file must live outside the repo')
QA = json.load(open(path))
ANON = os.environ.get('SDP_SUPABASE_ANON_KEY') or [k['api_key'] for k in json.load(urllib.request.urlopen(f'https://api.supabase.com/v1/projects/{REF}/api-keys')) if k['name'] == 'anon'][0]

def http(method, url, body=None, token=None, headers=None):
    h = {'apikey': ANON, 'content-type': 'application/json', 'authorization': 'Bearer ' + (token or ANON)}; h.update(headers or {})
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=90) as r: t = r.read().decode(); return r.status, (json.loads(t) if t else None)
    except urllib.error.HTTPError as e:
        t = e.read().decode()
        try: return e.code, json.loads(t)
        except Exception: return e.code, t
def token(who):
    s, j = http('POST', BASE + '/auth/v1/token?grant_type=password', {'email': QA[who]['email'], 'password': QA[who]['password']})
    assert s == 200, (who, s, j); return j['access_token']
view = lambda t, q='': http('GET', BASE + '/rest/v1/collections_view?select=name,version,data' + q, token=t)
save = lambda t, items: http('POST', BASE + '/rest/v1/rpc/save_collections', {'p_items': items}, token=t)
n = 0; fails = []
def ok(c, msg):
    global n; n += 1
    if not c: fails.append(msg); print('FAIL', msg)

def reset_qa():
    """Empty the QA workspace (never the firm's) through the Supabase management API, so each run starts clean."""
    import urllib.request as u, json as j
    ref = os.environ.get('SDP_SUPABASE_REF', 'eenpabyrmiltfqvzirhw')
    q = "delete from public.collections where workspace_id = 'qa'"
    u.urlopen(u.Request(f'https://api.supabase.com/v1/projects/{ref}/database/query', method='POST', data=j.dumps({'query': q}).encode(), headers={'content-type': 'application/json'}))

reset_qa()
T = {k: token(k) for k in QA}
# the owner lays down a known state
s, cur = view(T['owner'])
ver = {r['name']: r['version'] for r in (cur or [])}
s, res = save(T['owner'], [
    {'name': 'qa_bills', 'data': [{'id': 'b1', 'amount': 1200}], 'base': ver.get('qa_bills', 0)},
    {'name': 'bills', 'data': [{'id': 'b1', 'vendor': 'QA Lumber', 'amount': 1200}], 'base': ver.get('bills', 0)},
    {'name': 'project:qa1', 'data': {'id': 'qa1', 'name': 'QA job', 'budget': 50000, 'logs': [{'id': 'l1', 'note': 'start', 'cost': 10}]}, 'base': ver.get('project:qa1', 0)}])
ok(s == 200 and all('version' in r for r in res), f'owner saves: {s} {res}')
ver = {r['name']: r['version'] for r in res}

# nobody outside the firm
s, j = http('GET', BASE + '/rest/v1/collections_view?select=name')
ok(s in (401, 403) or j == [], f'anonymous reads nothing: {s} {j}')
s, j = http('GET', BASE + '/rest/v1/collections?select=name,data', token=T['owner'])
ok(s in (401, 403), f'no one reads the table directly, owner included: {s}')
s, j = http('GET', BASE + '/rest/v1/collections?select=name,version', token=T['foreman'])
ok(s == 200 or s in (401, 403), f'change-feed columns: {s}')
for who in ('nobody', 'client'):
    s, j = view(T[who]); ok(s == 200 and j == [], f'{who} sees nothing: {s} {j if not isinstance(j, list) else len(j)}')
    s, j = save(T[who], [{'name': 'project:qa1', 'data': {'id': 'qa1'}, 'base': 99}]); ok(s >= 400, f'{who} cannot save: {s}')

# the field gets the job without the money
s, rows = view(T['foreman']); names = {r['name']: r for r in rows}
ok('bills' not in names, 'foreman never receives bills')
ok('project:qa1' in names, 'foreman receives the job')
p = names['project:qa1']['data']
ok('budget' not in p and 'cost' not in p['logs'][0], f'money stripped from the job: {p}')
s, res = save(T['foreman'], [{'name': 'bills', 'data': [], 'base': 99}, {'name': 'company', 'data': {}, 'base': 99}])
ok(all(r.get('refused') for r in res), f'foreman cannot write bills or company: {res}')
p2 = dict(p); p2['logs'] = p['logs'] + [{'id': 'l2', 'note': 'framing inspected'}]; p2['budget'] = 1
s, res = save(T['foreman'], [{'name': 'project:qa1', 'data': p2, 'base': names['project:qa1']['version']}])
ok(s == 200 and res[0].get('version'), f'foreman saves a log: {res}')
s, rows = view(T['owner'], '&name=eq.project:qa1'); po = rows[0]['data']
ok(po['budget'] == 50000, f'the budget survives the field save, and the field cannot set it: {po.get("budget")}')
ok(po['logs'][0].get('cost') == 10 and po['logs'][1]['note'] == 'framing inspected', f'the log is added and the cost kept: {po["logs"]}')

# a stale save is refused, not applied
s, res = save(T['owner'], [{'name': 'project:qa1', 'data': {'id': 'qa1', 'name': 'stale'}, 'base': 1}])
ok(res and res[0].get('conflict'), f'stale save refused as a conflict: {res}')
s, rows = view(T['owner'], '&name=eq.project:qa1'); ok(rows[0]['data']['name'] == 'QA job', 'and nothing was overwritten')

# roles come from the owner only
me = QA['foreman']
s, j = http('PATCH', BASE + '/rest/v1/profiles?id=eq.' + me['id'], {'role': 'owner'}, token=T['foreman'], headers={'prefer': 'return=representation'})
ok(s >= 400 or j == [], f'foreman cannot make himself owner: {s} {j}')
s, j = http('GET', BASE + '/rest/v1/profiles?select=role&id=eq.' + me['id'], token=T['foreman'])
ok(j and j[0]['role'] == 'foreman', f'role unchanged: {j}')
s, j = http('PATCH', BASE + '/rest/v1/profiles?id=eq.' + me['id'], {'workspace_id': 'smartdesign'}, token=T['owner'], headers={'prefer': 'return=representation'})
ok(s >= 400, f'not even the owner moves someone into another firm: {s}')

# a person's own rows: nobody else reads or writes them, the owner included
own_o = 'own:' + QA['owner']['id'] + ':comms'; own_f = 'own:' + QA['foreman']['id'] + ':comms'
s, res = save(T['owner'], [{'name': own_o, 'data': [{'id': 'gm1', 'owner': 'x', 'source': 'google', 'text': 'OWNER-PRIVATE-MAIL'}], 'base': 0}])
ok(s == 200 and res[0].get('version'), f'the owner saves his own mail row: {res}')
s, res = save(T['foreman'], [{'name': own_f, 'data': [{'id': 'gm2', 'owner': 'y', 'source': 'google', 'text': 'FOREMAN-PRIVATE-MAIL'}], 'base': 0}])
ok(s == 200 and res[0].get('version'), f'the foreman saves his own mail row: {res}')
for who, mine, theirs in (('foreman', 'FOREMAN', 'OWNER'), ('owner', 'OWNER', 'FOREMAN'), ('crew', None, 'OWNER')):
    s, rows = view(T[who]); txt = json.dumps(rows)
    ok(theirs + '-PRIVATE-MAIL' not in txt and (who == 'crew' or 'FOREMAN' not in txt or who == 'foreman'), f'{who} never receives another person\'s mail')
    if mine: ok(mine + '-PRIVATE-MAIL' in txt, f'{who} receives his own mail')
s, res = save(T['foreman'], [{'name': own_o, 'data': [], 'base': 99}])
ok(res and res[0].get('refused'), f"the foreman cannot write the owner's mail row: {res}")
s, res = save(T['owner'], [{'name': own_f, 'data': [], 'base': 99}])
ok(res and res[0].get('refused'), f"the owner cannot write the foreman's mail row either: {res}")
s, j = http('POST', BASE + '/rest/v1/rpc/collection_versions', {}, token=T['foreman'])
ok(s == 200 and not any(r['name'] == own_o for r in j), "the version list does not show the owner's mail row to the foreman")

# the AI door
def ai(who, body):
    h = {'content-type': 'application/json'}
    if who: h['authorization'] = 'Bearer ' + T[who]
    req = urllib.request.Request(SITE + '/api/ai', method='POST', data=json.dumps(body).encode(), headers=h)
    try:
        with urllib.request.urlopen(req, timeout=90) as r: return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e: return e.code, e.read().decode()[:300]
q = {'tier': 'small', 'max_tokens': 30, 'messages': [{'role': 'user', 'content': 'Reply with the single word ready.'}]}
ok(ai(None, q)[0] == 401, 'AI: no session refused')
ok(ai('nobody', q)[0] == 403, 'AI: an account with no role refused')
ok(ai('client', q)[0] == 403, 'AI: a client refused (until per-client rows)')
s, j = ai('foreman', q)
ok(s == 200 and any(b.get('type') == 'text' for b in j.get('content', [])), f'AI: foreman answered: {s} {str(j)[:200]}')
ok(isinstance(j, dict) and j.get('model') == 'claude-haiku-5-5', f'AI: the server picked the small model: {j.get("model") if isinstance(j, dict) else j}')
s, j = http('GET', BASE + '/rest/v1/ai_usage?select=user_id,model,cost_usd&order=at.desc&limit=5', token=T['foreman'])
ok(s == 200 and j and all(r['user_id'] == me['id'] for r in j) and float(j[0]['cost_usd']) > 0, f'AI: the call is logged with its cost, and the foreman sees only his own: {j}')
s, j = http('GET', BASE + '/rest/v1/ai_usage?select=user_id&limit=50', token=T['owner'])
ok(s == 200 and any(r['user_id'] == me['id'] for r in j), 'AI: the owner sees the firm\'s spend')

print('ALL PASS' if not fails else f'{len(fails)} FAILED', f'({n} checks)')
sys.exit(1 if fails else 0)
