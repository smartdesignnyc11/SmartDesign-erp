"""Field roles receive only their jobs (BACKLOG §1.21 phase 2, §5 item 2), checked live as each person. Runs against the
real Supabase project with the QA accounts in the 'qa' workspace, never the firm's (the foreman acts as u_angel, the
crew member as u_alberto: test/qa_accounts.py links them). The accounts file lives OUTSIDE the repo.
Offline first: SDP_PG=… python3 test/schema_pg_test.py runs the same rules on a local Postgres.
Run: SD_QA_USERS=/abs/qa_users.json python3 test/live_fieldjobs_test.py"""
import json, os, sys, urllib.request, urllib.error
REF = os.environ.get('SDP_SUPABASE_REF', 'eenpabyrmiltfqvzirhw'); BASE = f'https://{REF}.supabase.co'
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
def view(t, q=''):
    s, j = http('GET', BASE + '/rest/v1/collections_view?select=name,version,data' + q, token=t)
    return {r['name']: r for r in j} if s == 200 and isinstance(j, list) else {}
save = lambda t, items: http('POST', BASE + '/rest/v1/rpc/save_collections', {'p_items': items}, token=t)
n = 0; fails = []
def ok(c, msg):
    global n; n += 1
    if not c: fails.append(msg); print('FAIL', msg)
def reset_qa():
    q = "delete from public.collections where workspace_id = 'qa'"
    urllib.request.urlopen(urllib.request.Request(f'https://api.supabase.com/v1/projects/{REF}/database/query', method='POST', data=json.dumps({'query': q}).encode(), headers={'content-type': 'application/json'}))

reset_qa()
T = {k: token(k) for k in ('owner', 'foreman', 'crew')}
job = lambda i, team: {'id': i, 'project': {'name': 'QA ' + i}, 'team': team, 'budget': 75000, 'tasks': [{'id': 't1', 'name': 'Frame', 'cost': 900}], 'chat': [{'id': 'c0', 'text': 'SECRET-OF-' + i}]}
items = [{'name': 'project:qaA', 'data': job('qaA', ['u_angel']), 'base': 0},
         {'name': 'project:qaB', 'data': job('qaB', ['u_alberto']), 'base': 0},
         {'name': 'project:qaC', 'data': {k: v for k, v in job('qaC', []).items() if k != 'team'}, 'base': 0}]
s, res = save(T['owner'], items)
ok(s == 200 and all('version' in r for r in res), f'the owner saves three jobs (Angel on A, Alberto on B, nobody on C): {s} {res}')

# each field person receives only the jobs whose crew names them, money stripped; the office receives all
v = view(T['owner']); ok({'project:qaA', 'project:qaB', 'project:qaC'} <= set(v), 'the owner reads every job')
v = view(T['foreman']); raw = json.dumps(v)
ok('project:qaA' in v and 'project:qaB' not in v and 'project:qaC' not in v, f'the foreman receives only job A: {sorted(k for k in v if k.startswith("project:"))}')
ok('SECRET-OF-qaB' not in raw and 'SECRET-OF-qaC' not in raw, 'not a byte of the other jobs reaches his phone')
ok('budget' not in v['project:qaA']['data'] and 'cost' not in v['project:qaA']['data']['tasks'][0], 'and job A arrives with the money stripped')
v = view(T['crew'])
ok('project:qaB' in v and 'project:qaA' not in v and 'project:qaC' not in v, f'the crew member receives only job B: {sorted(k for k in v if k.startswith("project:"))}')
s, j = http('POST', BASE + '/rest/v1/rpc/collection_versions', {}, token=T['foreman'])
ok(s == 200 and {r['name'] for r in j if r['name'].startswith('project:')} == {'project:qaA'}, f"the foreman's version poll names job A only: {s}")
s, j = http('GET', BASE + "/rest/v1/collections?select=name&name=like.project:*", token=T['foreman'])
ok(s == 200 and {r['name'] for r in j} <= {'project:qaA'}, f"the change feed's columns name no other job to the foreman: {s} {j}")

# the foreman writes his job: his line is kept, the crew list and the money are not his to change
pa = view(T['foreman'])['project:qaA']
d = pa['data']; d['chat'].append({'id': 'c1', 'text': 'rough-in inspected'}); d['team'] = ['u_angel', 'u_alberto']; d['budget'] = 1
s, res = save(T['foreman'], [{'name': 'project:qaA', 'data': d, 'base': pa['version']}])
ok(s == 200 and res[0].get('version'), f'the foreman saves job A: {res}')
o = view(T['owner'], '&name=eq.project:qaA')['project:qaA']['data']
ok(o['chat'][-1]['text'] == 'rough-in inspected', 'his line reached the office')
ok(o['team'] == ['u_angel'] and o['budget'] == 75000 and o['tasks'][0]['cost'] == 900, f'the crew list and the money stand: {o["team"]} {o["budget"]}')
s, res = save(T['foreman'], [{'name': 'project:qaB', 'data': job('qaB', ['u_angel', 'u_alberto']), 'base': 99}])
ok(res and res[0].get('refused'), f'the foreman cannot write a job he is not on, nor put himself on it: {res}')
s, res = save(T['foreman'], [{'name': 'project:qaC', 'data': job('qaC', ['u_angel']), 'base': 0}])
ok(res and res[0].get('refused'), f'nor claim a job with no crew yet: {res}')
s, res = save(T['foreman'], [{'name': 'project:qaNEW', 'data': job('qaNEW', ['u_angel']), 'base': 0}])
ok(res and res[0].get('refused'), f'nor start a job: {res}')
ok(view(T['owner'], '&name=eq.project:qaB')['project:qaB']['data']['team'] == ['u_alberto'], "job B's crew is untouched")

# the PM (here the owner) takes Angel off A and puts him on C: his phone loses A and gains C
v = view(T['owner'])
a, c = v['project:qaA'], v['project:qaC']
a['data']['team'] = []; c['data']['team'] = ['u_angel']
s, res = save(T['owner'], [{'name': 'project:qaA', 'data': a['data'], 'base': a['version']}, {'name': 'project:qaC', 'data': c['data'], 'base': c['version']}])
ok(s == 200 and all('version' in r for r in res), f'the owner changes the crews: {res}')
v = view(T['foreman'])
ok('project:qaA' not in v and 'project:qaC' in v, f'the foreman now receives job C and no longer job A: {sorted(k for k in v if k.startswith("project:"))}')
s, res = save(T['foreman'], [{'name': 'project:qaA', 'data': d, 'base': 99}])
ok(res and res[0].get('refused'), f'and can no longer write job A: {res}')

# the field still writes its own collections (its time)
s, cur = http('GET', BASE + '/rest/v1/collections_view?select=version&name=eq.time', token=T['foreman'])
s, res = save(T['foreman'], [{'name': 'time', 'data': [{'id': 'te1', 'empId': 'em1', 'projectId': 'qaC', 'date': '2026-09-03'}], 'base': (cur[0]['version'] if cur else 0)}])
ok(s == 200 and res[0].get('version'), f'the foreman still saves his time: {res}')

print('ALL PASS' if not fails else f'{len(fails)} FAILED', f'({n} checks)')
sys.exit(1 if fails else 0)
