"""The team's own workspace (TASKS_PLAN §2 Phase 1 item 1) on a local Postgres, offline: schema.sql's workspace rules
run as each person before they go near the live database. The owner opens the team workspace; the coordinator and the
office admin (billing) are brought into it the way /api/team does it (the service role); each reads and writes the
workspace's tasks and nothing of the demo's; nobody can give himself a workspace or read the workspace list.
Supabase's own pieces are stubbed exactly as in schema_pg_test.py. A throwaway database (sdp_ws_test) is created and
dropped; nothing live is touched.
Run: SDP_PG='-h /var/run/postgresql -U postgres' python3 test/workspace_pg_test.py   (any local Postgres 14+; psql on PATH)"""
import json, os, shlex, subprocess, sys, uuid
H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PG = os.environ.get('SDP_PG')
if PG is None: sys.exit('set SDP_PG to the psql connection flags of a local Postgres (e.g. "-h /var/run/postgresql -U postgres")')
DBN = 'sdp_ws_test'
def psql(sql, db=DBN, check=True):
    r = subprocess.run(['psql', *shlex.split(PG), '-d', db, '-v', 'ON_ERROR_STOP=1', '-qAtX'], input=sql, capture_output=True, text=True)
    if check and r.returncode: raise SystemExit('psql failed:\n' + r.stderr[-2000:])
    return r
psql(f'drop database if exists {DBN}; create database {DBN};', db='postgres')
STUB = r"""
do $$ begin
  if not exists (select 1 from pg_roles where rolname = 'anon') then create role anon nologin; end if;
  if not exists (select 1 from pg_roles where rolname = 'authenticated') then create role authenticated nologin; end if;
  if not exists (select 1 from pg_roles where rolname = 'service_role') then create role service_role nologin bypassrls; end if;
end $$;
create schema auth;
create table auth.users (id uuid primary key, email text, raw_user_meta_data jsonb default '{}'::jsonb);
create table auth.sessions (id uuid primary key, user_id uuid);
create function auth.jwt() returns jsonb language sql stable as $$ select coalesce(nullif(current_setting('request.jwt.claims', true), ''), '{}')::jsonb $$;
create function auth.uid() returns uuid language sql stable as $$ select nullif(auth.jwt()->>'sub', '')::uuid $$;
grant usage on schema auth, public to anon, authenticated, service_role;
grant execute on function auth.uid(), auth.jwt() to anon, authenticated;
create schema storage;
create table storage.buckets (id text primary key, name text, public boolean);
create table storage.objects (bucket_id text, name text);
alter table storage.objects enable row level security;
create publication supabase_realtime;
alter default privileges in schema public grant all on tables to anon, authenticated, service_role;
alter default privileges in schema public grant all on functions to anon, authenticated, service_role;
alter default privileges in schema public grant all on sequences to anon, authenticated, service_role;
"""
psql(STUB)
schema = open(os.path.join(H, 'supabase', 'schema.sql')).read()
psql(schema); psql(schema)                                   # twice: idempotent

n = 0; fails = []
def ok(c, msg):
    global n; n += 1
    if not c: fails.append(msg); print('FAIL', msg)
P = {}
def person(key, role, app_user, ws='smartdesign'):
    uid, sid = str(uuid.uuid4()), str(uuid.uuid4())
    psql(f"insert into auth.users (id, email) values ('{uid}', '{key}@example.com'); insert into auth.sessions values ('{sid}', '{uid}');"
         f"update public.profiles set role = '{role}', workspace_id = '{ws}', app_user_id = {('$$' + app_user + '$$') if app_user else 'null'} where id = '{uid}';")
    P[key] = (uid, sid)
def as_(key, sql):
    uid, sid = P[key]
    claims = json.dumps({'sub': uid, 'session_id': sid, 'role': 'authenticated'})
    r = psql(f"set role authenticated; select set_config('request.jwt.claims', $${claims}$$, false);\n" + sql, check=False)
    lines = r.stdout.strip().splitlines()
    return (lines[1:] if lines else []), r.stderr.strip()
def one(key, sql):
    rows, err = as_(key, sql)
    return (json.loads(rows[0]) if rows and rows[0] else None), err
def view(key):
    rows, err = as_(key, "select json_agg(json_build_object('name', name, 'data', data)) from public.collections_view;")
    return {r['name']: r['data'] for r in (json.loads(rows[0]) if rows and rows[0] else [])}
def save(key, items):
    rows, err = as_(key, f"select public.save_collections($${json.dumps(items)}$$::jsonb);")
    if err: return {'error': err}
    return {r['name']: r for r in json.loads(rows[0])}
def ver(key, name):
    rows, err = as_(key, f"select version from public.collections_view where name = $${name}$$;")
    return int(rows[0]) if rows and rows[0] else 0
info = lambda key: one(key, 'select public.my_workspace_info();')[0]

# the demo as it is today: the owner, the coordinator and the office admin in 'smartdesign', with the demo's records
person('owner', 'owner', 'u_owner'); person('coord', 'coord', 'u_chen'); person('billing', 'billing', 'u_billing')
person('pm', 'pm', 'u_alan'); person('nobody', 'none', None); person('stranger', 'owner', 'u_x', ws='otherfirm')
res = save('owner', [{'name': 'project:p121', 'data': {'id': 'p121', 'project': {'name': '121 State Street'}, 'actions': [{'id': 'a1', 'title': 'DEMO TASK'}]}, 'base': 0},
                     {'name': 'tasks', 'data': [{'id': 'dt1', 'title': 'DEMO OFFICE TASK'}], 'base': 0}])
ok(all('version' in r for r in res.values()), f'the demo holds its records: {res}')
i = info('owner')
ok(i and i['id'] == 'smartdesign' and i['kind'] == 'demo' and i['others'] == [], f'a workspace made before this change reads as the demo: {i}')
ok(info('nobody')['kind'] == 'none', 'an account with no role learns nothing about any workspace')

# only the owner opens the team's workspace; the id must be new and well formed
_, err = as_('coord', "select public.open_team_workspace('sd-team', 'SmartDesign');")
ok('only the owner' in err, f'the coordinator cannot open a workspace: {err[:120]}')
for bad in ('smartdesign', 'otherfirm', 'X', 'has space'):
    _, err = as_('owner', f"select public.open_team_workspace('{bad}', 'x');")
    ok(err, f'the owner cannot open {bad!r} as a team workspace (taken or malformed)')
ok(info('owner')['id'] == 'smartdesign', 'and a refused open leaves him where he was')
i, err = one('owner', "select public.open_team_workspace('sd-team', 'SmartDesign');")
ok(not err and i['id'] == 'sd-team' and i['kind'] == 'team' and [o['id'] for o in i['others']] == ['smartdesign'], f'the owner opens the team workspace and keeps the demo in his list: {i} {err[:200]}')
v = view('owner')
ok(v == {}, f'the team workspace starts empty: no demo record reaches it ({sorted(v)})')
i, err = one('owner', "select public.open_team_workspace('sd-team', 'SmartDesign');")
ok(not err and i['id'] == 'sd-team', f'opening it again is harmless: {err[:120]}')

# the owner lays down the team's real projects and tasks (invented here)
res = save('owner', [{'name': 'project:pPAD', 'data': {'id': 'pPAD', 'project': {'name': 'Pine Ave Duplex', 'prefix': 'PAD'}, 'actions': [{'id': 'k1', 'key': 'PAD-23', 'title': 'TEAM TASK', 'owner': 'u_owner'}]}, 'base': 0},
                     {'name': 'tasks', 'data': [{'id': 'ot1', 'title': 'TEAM OFFICE TASK'}], 'base': 0}])
ok(all('version' in r for r in res.values()), f'the owner saves in the team workspace: {res}')
ok('TEAM TASK' not in json.dumps(view('coord')) and 'DEMO TASK' in json.dumps(view('coord')), 'the coordinator, still in the demo, sees the demo and not the team')
ok('TEAM' not in json.dumps(view('pm')), 'nobody left in the demo reads the team workspace')
ok('TEAM' not in json.dumps(view('stranger')), 'nor does another firm')

# /api/team brings the coordinator and the office admin in (the service role; schema-level effect reproduced here)
for k in ('coord', 'billing'):
    psql(f"update public.profiles set workspace_id = 'sd-team', workspaces = array['smartdesign'] where id = '{P[k][0]}';")
for k in ('coord', 'billing'):
    v = json.dumps(view(k))
    ok('TEAM TASK' in v and 'TEAM OFFICE TASK' in v and 'DEMO' not in v, f'{k} reads the team workspace\'s tasks and none of the demo\'s')
    ok(info(k)['kind'] == 'team', f'{k} is told it is the team workspace')
d = view('billing')['project:pPAD']
d['actions'].append({'id': 'k2', 'key': 'PAD-24', 'title': 'ADDED BY THE OFFICE ADMIN', 'owner': 'u_billing'})
r = save('billing', [{'name': 'project:pPAD', 'data': d, 'base': ver('billing', 'project:pPAD')}])['project:pPAD']
ok(r.get('version'), f'the office admin writes a task on a team project: {r}')
ok('ADDED BY THE OFFICE ADMIN' in json.dumps(view('owner')) and 'ADDED BY THE OFFICE ADMIN' in json.dumps(view('coord')), 'and the owner and the coordinator read it')
o = view('coord')['tasks']; o.append({'id': 'ot2', 'title': 'COORD OFFICE TASK'})
r = save('coord', [{'name': 'tasks', 'data': o, 'base': ver('coord', 'tasks')}])['tasks']
ok(r.get('version') and 'COORD OFFICE TASK' in json.dumps(view('billing')), 'the coordinator\'s office task reaches the office admin')
ok('COORD' not in json.dumps(view('pm')) and 'ADDED BY' not in json.dumps(view('pm')), 'none of it reaches the demo')
# the change feed: the realtime select runs as the person through the policy
rows, err = as_('coord', "select json_agg(name order by name) from public.collections;")
ok(not err and json.loads(rows[0]) == ['project:pPAD', 'tasks'], f"the coordinator's change feed names only the team's rows: {rows} {err[:200]}")
rows, err = as_('pm', "select json_agg(name order by name) from public.collections;")
ok(not err and json.loads(rows[0]) == ['project:p121', 'tasks'], f"the demo PM's change feed names only the demo's rows: {rows} {err[:200]}")

# switching back and forth: only to a workspace one holds
i, err = one('owner', "select public.switch_workspace('smartdesign');")
ok(not err and i['id'] == 'smartdesign' and i['kind'] == 'demo' and [o['id'] for o in i['others']] == ['sd-team'], f'the owner switches to the demo, the team stays in his list: {i}')
v = json.dumps(view('owner'))
ok('DEMO TASK' in v and 'TEAM' not in v, 'in the demo he reads the demo only')
i, err = one('owner', "select public.switch_workspace('sd-team');")
ok(not err and i['id'] == 'sd-team', 'and back')
_, err = as_('owner', "select public.switch_workspace('otherfirm');")
ok('not one of your workspaces' in err, f'nobody switches into a workspace he does not hold: {err[:120]}')
_, err = as_('pm', "select public.switch_workspace('sd-team');")
ok('not one of your workspaces' in err, f'the demo PM cannot walk into the team workspace by naming it: {err[:120]}')
_, err = as_('nobody', "select public.switch_workspace('sd-team');")
ok(err, 'an account with no role switches nowhere')

# nobody signed in can give himself a workspace, read the list of workspaces or change a workspace's kind
_, err = as_('pm', f"update public.profiles set workspaces = array['sd-team'] where id = '{P['pm'][0]}';")
ok('permission denied' in err, f'a person cannot add a workspace to his own profile: {err[:120]}')
_, err = as_('owner', f"update public.profiles set workspace_id = 'sd-team' where id = '{P['pm'][0]}';")
ok('permission denied' in err, f'nor can the owner move someone by hand from the page (the server does it): {err[:120]}')
_, err = as_('owner', "select count(*) from public.workspaces;")
ok('permission denied' in err, f'the workspace list is the server\'s: {err[:120]}')
_, err = as_('owner', "update public.workspaces set kind = 'demo';")
ok('permission denied' in err, f'nor can anyone turn the team workspace back into a demo: {err[:120]}')
# the owner's profile list shows the people of the workspace he is in
rows, err = as_('owner', "select json_agg(email order by email) from public.profiles;")
emails = json.loads(rows[0]) if rows and rows[0] else []
ok({'billing@example.com', 'coord@example.com', 'owner@example.com'} <= set(emails) and 'pm@example.com' not in emails, f'Team Accounts in the team workspace lists its people: {emails}')

psql(f'drop database if exists {DBN};', db='postgres')
print('ALL PASS' if not fails else f'{len(fails)} FAILED', f'({n} checks)')
sys.exit(1 if fails else 0)
