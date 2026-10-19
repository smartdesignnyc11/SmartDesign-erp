"""supabase/schema.sql on a local Postgres, offline: the rules run as each kind of person before they go near the live
database. Supabase's own pieces (auth.uid(), auth.jwt(), auth.sessions, storage, the realtime publication, the anon
and authenticated roles and their default grants) are stubbed; everything else is the real file, applied twice to
prove it idempotent. A throwaway database (sdp_schema_test) is created and dropped; nothing live is touched.
Run: SDP_PG='-h /var/run/postgresql -U postgres' python3 test/schema_pg_test.py   (any local Postgres 14+; psql on PATH)"""
import json, os, shlex, subprocess, sys, uuid
H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PG = os.environ.get('SDP_PG')
if PG is None: sys.exit('set SDP_PG to the psql connection flags of a local Postgres (e.g. "-h /var/run/postgresql -U postgres")')
DBN = 'sdp_schema_test'
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
-- Supabase grants everything in public to its API roles by default; schema.sql revokes what it must
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
def person(key, role, app_user, ws='qa'):
    uid, sid = str(uuid.uuid4()), str(uuid.uuid4())
    psql(f"insert into auth.users (id, email) values ('{uid}', '{key}@example.com'); insert into auth.sessions values ('{sid}', '{uid}');"
         f"update public.profiles set role = '{role}', workspace_id = '{ws}', app_user_id = {('$$' + app_user + '$$') if app_user else 'null'} where id = '{uid}';")
    P[key] = (uid, sid)
person('owner', 'owner', 'u_owner'); person('pm', 'pm', 'u_alan'); person('foreman', 'foreman', 'u_angel'); person('crew', 'crew', 'u_alberto')
person('driver', 'driver', None)
def as_(key, sql):
    uid, sid = P[key]
    claims = json.dumps({'sub': uid, 'session_id': sid, 'role': 'authenticated'})
    r = psql(f"set role authenticated; select set_config('request.jwt.claims', $${claims}$$, false);\n" + sql, check=False)
    lines = r.stdout.strip().splitlines()
    return (lines[1:] if lines else []), r.stderr.strip()
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

# the owner lays down three jobs: Angel's, Alberto's and one with no crew yet
res = save('owner', [
    {'name': 'project:pA', 'data': {'id': 'pA', 'project': {'name': 'Job A'}, 'team': ['u_angel'], 'budget': 50000, 'chat': []}, 'base': 0},
    {'name': 'project:pB', 'data': {'id': 'pB', 'project': {'name': 'Job B'}, 'team': ['u_alberto'], 'chat': []}, 'base': 0},
    {'name': 'project:pC', 'data': {'id': 'pC', 'project': {'name': 'Job C'}, 'chat': []}, 'base': 0},
    {'name': 'pos', 'data': [{'id': 'po1', 'projectId': 'pA', 'total': 10}], 'base': 0}])
ok(all('version' in r for r in res.values()), f'the owner saves three jobs: {res}')
ok(set(view('owner')) >= {'project:pA', 'project:pB', 'project:pC'}, 'the owner reads every job')
ok({'project:pA', 'project:pB', 'project:pC'} <= set(view('pm')), 'the PM reads every job')
v = view('foreman')
ok('project:pA' in v and 'project:pB' not in v and 'project:pC' not in v, f'the foreman reads only the job he is on: {sorted(v)}')
ok('budget' not in v.get('project:pA', {}), 'and with the money stripped')
v = view('crew')
ok('project:pB' in v and 'project:pA' not in v and 'project:pC' not in v, f'the crew member reads only his job: {sorted(v)}')
ok(not any(k.startswith('project:') for k in view('driver')), 'a field sign-in the owner has not linked to a person reads no job')
rows, err = as_('foreman', 'select json_agg(name) from public.collection_versions();')
names = json.loads(rows[0]) if rows and rows[0] else []
ok('project:pA' in names and 'project:pB' not in names and 'project:pC' not in names, f'the version list shows the foreman his job only: {names}')
# the change feed: the column-granted select the realtime server runs as the person, through the policy
rows, err = as_('foreman', "select json_agg(name) from public.collections where name like 'project:%';")
names = json.loads(rows[0]) if rows and rows[0] else []
ok(not err and names == ['project:pA'], f'the change feed announces only his job, not even another job by name: {names} {err[:200]}')
rows, err = as_('owner', "select json_agg(name) from public.collections where name like 'project:%';")
ok(not err and len(json.loads(rows[0])) == 3, f'the owner hears every job: {rows} {err[:200]}')

# the foreman writes his job: his line lands, the crew list and the money do not move
pa = view('foreman')['project:pA']
pa['chat'] = [{'id': 'c1', 'text': 'framing done'}]; pa['team'] = ['u_angel', 'u_alberto', 'u_satish']; pa['budget'] = 1; pa['teamAt'] = {'u_satish': '2026-09-03T08:00:00'}
r = save('foreman', [{'name': 'project:pA', 'data': pa, 'base': ver('foreman', 'project:pA')}])['project:pA']
ok(r.get('version'), f'the foreman saves his job: {r}')
o = view('owner')['project:pA']
ok(o['chat'][0]['text'] == 'framing done' and o['team'] == ['u_angel'] and o['budget'] == 50000, f'his line is kept; the crew list and the budget are not his to change: {o}')
ok('teamAt' not in o, f'nor when anyone joined it: {o}')
pa2 = dict(pa); pa2.pop('team')
save('foreman', [{'name': 'project:pA', 'data': pa2, 'base': ver('foreman', 'project:pA')}])
ok(view('owner')['project:pA']['team'] == ['u_angel'], 'a save that drops the crew list keeps it')
r = save('foreman', [{'name': 'project:pB', 'data': {'id': 'pB', 'team': ['u_angel'], 'chat': [{'id': 'x', 'text': 'forged'}]}, 'base': 99}])['project:pB']
ok(r.get('refused'), f"the foreman cannot write a job he is not on, or put himself on it: {r}")
ok(view('owner')['project:pB']['team'] == ['u_alberto'], 'and the job is untouched')
r = save('foreman', [{'name': 'project:pZ', 'data': {'id': 'pZ', 'team': ['u_angel']}, 'base': 0}])['project:pZ']
ok(r.get('refused'), f'the field never starts a job: {r}')
r = save('foreman', [{'name': 'project:pC', 'data': {'id': 'pC', 'team': ['u_angel']}, 'base': 0}])['project:pC']
ok(r.get('refused'), f'nor claims a job with no crew yet: {r}')

# the PM takes Angel off job A and puts him on job C: the phone loses A and gains C
o = view('pm'); a, c = o['project:pA'], o['project:pC']
a['team'] = []; c['team'] = ['u_angel']
res = save('pm', [{'name': 'project:pA', 'data': a, 'base': ver('pm', 'project:pA')}, {'name': 'project:pC', 'data': c, 'base': ver('pm', 'project:pC')}])
ok(all('version' in r for r in res.values()), f'the PM changes the crews: {res}')
v = view('foreman')
ok('project:pA' not in v and 'project:pC' in v, f'the foreman now reads job C and not job A: {sorted(v)}')
r = save('foreman', [{'name': 'project:pA', 'data': pa, 'base': 99}])['project:pA']
ok(r.get('refused'), f'and can no longer write job A: {r}')

# threads and own rows are unchanged by this, and still hidden from the change feed of everyone else
save('owner', [{'name': 'thread:t1', 'data': {'id': 't1', 'members': ['u_owner', 'u_alberto'], 'msgs': []}, 'base': 0},
               {'name': 'own:' + P['owner'][0] + ':comms', 'data': [], 'base': 0}])
rows, err = as_('foreman', "select json_agg(name) from public.collections where name like 'thread:%' or name like 'own:%';")
ok(not err and (not rows or rows[0] in ('', None)), f"the foreman's change feed never names another person's thread or private row: {rows} {err[:200]}")
rows, err = as_('crew', "select json_agg(name) from public.collections where name like 'thread:%';")
ok(not err and rows and 'thread:t1' in rows[0], f'the crew member, a member, hears his thread: {rows} {err[:200]}')

# notifications: one per conversation per person every 2 minutes, and nobody signed in can call or read it
first = psql("select public.notify_claim('pk1', 'dm:t1', 'qa');").stdout.strip()
second = psql("select public.notify_claim('pk1', 'dm:t1', 'qa');").stdout.strip()
other = psql("select public.notify_claim('pk1', 'job:pA', 'qa');").stdout.strip()
ok(first == 't' and second == 'f' and other == 't', f'notify: once per conversation inside 2 minutes ({first} {second} {other})')
psql("update public.notify_sent set at = now() - interval '3 minutes' where thread_key = 'dm:t1';")
ok(psql("select public.notify_claim('pk1', 'dm:t1', 'qa');").stdout.strip() == 't', 'notify: again after 2 minutes')
rows, err = as_('owner', "select public.notify_claim('pk1', 'dm:t9', 'qa');")
ok('permission denied' in err, f'notify: nobody signed in calls it, the owner included: {err[:120]}')
rows, err = as_('owner', 'select count(*) from public.notify_sent;')
ok('permission denied' in err, f'notify: nobody signed in reads it: {err[:120]}')

psql(f'drop database if exists {DBN};', db='postgres')
print('ALL PASS' if not fails else f'{len(fails)} FAILED', f'({n} checks)')
sys.exit(1 if fails else 0)
