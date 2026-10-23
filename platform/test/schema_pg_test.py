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

# the owner reads every conversation, writes only once he has joined it (in the open), and nobody else gains anything
person('chen', 'coord', 'u_chen')
r = save('crew', [{'name': 'thread:t9', 'data': {'id': 't9', 'kind': 'direct', 'members': ['u_alberto', 'u_chen'], 'msgs': [{'id': 'a', 'text': 'CREW-TO-CHEN'}]}, 'base': 0}])['thread:t9']
ok(r.get('version'), f'the crew member starts a direct chat with Chen: {r}')
ok('thread:t9' in view('owner') and 'CREW-TO-CHEN' in json.dumps(view('owner')), 'the owner reads a chat he is not in')
ok('thread:t9' not in view('foreman') and 'thread:t9' not in view('pm'), 'nobody else who is not in it does, the PM included')
rows, err = as_('owner', "select json_agg(name) from public.collections where name = 'thread:t9';")
ok(not err and rows and 'thread:t9' in rows[0], f"the owner's change feed hears it: {rows} {err[:120]}")
r = save('owner', [{'name': 'thread:t9', 'data': {'id': 't9', 'members': ['u_alberto', 'u_chen'], 'msgs': [{'id': 'a', 'text': 'CREW-TO-CHEN'}, {'id': 'b', 'text': 'IN THEIR NAME'}]}, 'base': ver('owner', 'thread:t9')}])['thread:t9']
ok(r.get('refused'), f'the owner cannot write in it before he joins: {r}')
rows, err = as_('pm', "select public.thread_join('t9');")
ok('only the owner' in err, f'nobody but the owner can join a chat he is not in: {err[:120]}')
rows, err = as_('owner', "select public.thread_join('t9');")
ok(not err and '"joined": true' in rows[0], f'the owner joins it: {rows} {err[:120]}')
d = view('owner')['thread:t9']
ok('u_owner' in d['members'] and d['msgs'][-1].get('system') and d['msgs'][-1]['text'].endswith('joined'), f'he is a member now, and a line says so: {d}')
ok('thread:t9' in view('crew') and 'joined' in json.dumps(view('crew')['thread:t9']), 'the others see that he joined')
d['msgs'].append({'id': 'c', 'text': 'OWNER-AFTER-JOIN'})
r = save('owner', [{'name': 'thread:t9', 'data': d, 'base': ver('owner', 'thread:t9')}])['thread:t9']
ok(r.get('version'), f'and then writes in it: {r}')

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

# a guest's email reply filed by the watcher (2026-10-20): only into a chat the mailbox's person is in, once per mail
# (by its Gmail id or its Message-ID), the version moves so members' pages refetch it; nobody signed in can call it
line = json.dumps({'id': 'g1', 'by': 'Imogen Varga', 'text': 'GUEST-REPLY', 'viaMail': 'gm1', 'mailId': '<abc@mail>'}).replace("'", "''")
v0 = ver('crew', 'thread:t9')
v1 = psql(f"select public.thread_file_mail('qa', 't9', 'u_chen', '{line}'::jsonb);").stdout.strip()
ok(v1 == str(v0 + 1) and 'GUEST-REPLY' in json.dumps(view('crew')['thread:t9']), f'mail: filed into a chat the person is in, version {v0} to {v1}')
again = json.dumps({'id': 'g2', 'text': 'GUEST-REPLY', 'viaMail': 'other-box-id', 'mailId': '<abc@mail>'}).replace("'", "''")
ok(psql(f"select public.thread_file_mail('qa', 't9', 'u_owner', '{again}'::jsonb);").stdout.strip() == '0', 'mail: the same mail from another member\'s mailbox is not filed twice')
ok(json.dumps(view('crew')['thread:t9']).count('GUEST-REPLY') == 1, 'mail: one line')
ok(psql(f"select public.thread_file_mail('qa', 't9', 'u_angel', '{line.replace('gm1', 'gm9').replace('abc@', 'zz@')}'::jsonb);").stdout.strip() == '0', 'mail: never into a chat the mailbox\'s person is not in')
ok(psql(f"select public.thread_file_mail('qa', 'nope', 'u_chen', '{line}'::jsonb);").stdout.strip() == '0', 'mail: nothing for a chat that does not exist')
rows, err = as_('owner', f"select public.thread_file_mail('qa', 't9', 'u_owner', '{line}'::jsonb);")
ok('permission denied' in err, f'mail: nobody signed in calls it: {err[:120]}')

# the shared lists that mix jobs (2026-10-20): a field sign-in reads only its jobs' records and records with no job,
# and a field save keeps the records it could not see. The owner first puts Angel back on Job A only.
ow = view('owner'); a, cj = ow['project:pA'], ow['project:pC']; a['team'] = ['u_angel']; cj['team'] = []
save('owner', [{'name': 'project:pA', 'data': a, 'base': ver('owner', 'project:pA')}, {'name': 'project:pC', 'data': cj, 'base': ver('owner', 'project:pC')}])
res = save('owner', [
    {'name': 'photos', 'data': [{'id': 'ph1', 'projectId': 'pA'}, {'id': 'ph2', 'projectId': 'pB'}, {'id': 'ph3', 'projectId': ''}], 'base': ver('owner', 'photos')},
    {'name': 'time', 'data': [{'id': 't1', 'projectId': 'pA', 'hours': 8}, {'id': 't2', 'projectId': 'pC', 'hours': 6}], 'base': ver('owner', 'time')},
    {'name': 'field', 'data': {'logs': [{'id': 'l1', 'projectId': 'pA'}, {'id': 'l2', 'projectId': 'pB'}], 'punch': [{'id': 'pu1', 'projectId': 'pC'}], 'other': 1}, 'base': ver('owner', 'field')},
    {'name': 'hub', 'data': {'contacts': [{'id': 'c1', 'name': 'A LEAD'}]}, 'base': ver('owner', 'hub')},
    {'name': 'budgetPlan', 'data': {'versions': []}, 'base': ver('owner', 'budgetPlan')}])
ok(all('version' in r for r in res.values()), f'the owner saves the shared lists: {res}')
v = view('foreman')
ok([x['id'] for x in v['photos']] == ['ph1', 'ph3'], f"the foreman's photos: his job's and the unfiled, not Job B's: {v['photos']}")
ok([x['id'] for x in v['time']] == ['t1'], f"his hours list holds only his job's: {v['time']}")
ok([x['id'] for x in v['field']['logs']] == ['l1'] and v['field']['punch'] == [] and v['field']['other'] == 1, f"inside a collection too (logs, punch): {v['field']}")
ok('hub' not in v and 'budgetPlan' not in v, f'no sales CRM, no budget plan: {sorted(k for k in v if k in ("hub","budgetPlan","studio"))}')
ok(len(view('owner')['photos']) == 3 and len(view('pm')['time']) == 2, 'the office still reads every record')
# the foreman adds a photo on his job and edits his log; nothing of Job B or Job C may be lost
mine = v['photos'] + [{'id': 'ph4', 'projectId': 'pA'}]
fl = dict(v['field']); fl['logs'] = [{'id': 'l1', 'projectId': 'pA', 'note': 'edited'}]
res = save('foreman', [{'name': 'photos', 'data': mine, 'base': ver('foreman', 'photos')}, {'name': 'field', 'data': fl, 'base': ver('foreman', 'field')}])
ok(all('version' in r for r in res.values()), f'the foreman saves: {res}')
o = view('owner')
ok(sorted(x['id'] for x in o['photos']) == ['ph1', 'ph2', 'ph3', 'ph4'], f"Job B's photo survives the foreman's save: {o['photos']}")
ok(sorted(x['id'] for x in o['field']['logs']) == ['l1', 'l2'] and [x['id'] for x in o['field']['punch']] == ['pu1'] and any(x.get('note') == 'edited' for x in o['field']['logs']), f"his edit lands, the others' logs and punch stay: {o['field']}")
# he cannot write a record into a job he is not on
res = save('foreman', [{'name': 'photos', 'data': view('foreman')['photos'] + [{'id': 'ph5', 'projectId': 'pB'}], 'base': ver('foreman', 'photos')}])
ok('ph5' not in [x['id'] for x in view('owner')['photos']], 'a record for a job he is not on is not written')

# the improvement loop's signals (2026-10-20): the foreman starts the list with his own report and an anonymous one;
# the office reads them all; he reads only his own; he can update his own, never change or drop anyone else's
res = save('foreman', [{'name': 'signals', 'data': [{'id': 'rp:f1', 'kind': 'report', 'uid': 'u_angel', 'text': 'MINE'}, {'id': 'rp:anon', 'kind': 'report', 'uid': '', 'text': 'NO NAME'}, {'id': 'rp:forged', 'kind': 'report', 'uid': 'u_alan', 'text': 'AS THE PM'}], 'base': 0}])
ok(res.get('signals', {}).get('version'), f'a field phone may start the signals list: {res}')
o = view('owner').get('signals', [])
ok(sorted(x['id'] for x in o) == ['rp:anon', 'rp:f1'], f'his and the anonymous report land; one in another person\'s name does not: {o}')
save('pm', [{'name': 'signals', 'data': o + [{'id': 'us:d:u_alan', 'kind': 'usage', 'uid': 'u_alan', 'by': {'po': {'export': 2}}}], 'base': ver('pm', 'signals')}])
ok([x['id'] for x in view('foreman')['signals']] == ['rp:f1'], f"the foreman reads only his own signals: {view('foreman')['signals']}")
ok(len(view('owner')['signals']) == 3, 'the office reads every signal')
mine = view('foreman')['signals']; mine[0]['text'] = 'MINE, EDITED'
res = save('foreman', [{'name': 'signals', 'data': mine, 'base': ver('foreman', 'signals')}])
o = {x['id']: x for x in view('owner')['signals']}
ok(o['rp:f1']['text'] == 'MINE, EDITED' and 'us:d:u_alan' in o and 'rp:anon' in o, f"his edit lands; the PM's and the anonymous signals survive a save that did not carry them: {list(o)}")
res = save('foreman', [{'name': 'signals', 'data': [{'id': 'us:d:u_alan', 'kind': 'usage', 'uid': 'u_alan', 'by': {}}, {'id': 'rp:anon', 'uid': '', 'text': 'CHANGED'}], 'base': ver('foreman', 'signals')}])
o = {x['id']: x for x in view('owner')['signals']}
ok(o['us:d:u_alan']['by'] == {'po': {'export': 2}} and o['rp:anon']['text'] == 'NO NAME', f'he cannot change the PM\'s counts or an anonymous report: {o}')

# the team meeting's transcript (2026-10-23): the watcher files the notes on Meeting Mode's record of that day and
# the words on their own row; the attendees and the owner read the words, nobody else; the record's own lists stay
save('pm', [{'name': 'meetings', 'data': [{'id': 'mtL', 'title': 'Weekly Jobs', 'date': '2026-09-03', 'startedAt': '2026-09-03T09:59:30', 'screenLog': [{'taskKey': 'STA-21', 'from': '2026-09-03T10:00:40'}], 'changes': [{'taskKey': 'STA-21', 'field': 'due'}], 'proposals': [{'id': 'keep'}], 'owner': {'uid': 'u_alan', 'name': 'Alan'}}], 'base': ver('pm', 'meetings')}])
mt = {'id': 'mtNEW', 'series': 'mw1', 'title': 'Weekly Jobs (doc)', 'date': '2026-09-03', 'start': '2026-09-03T09:58:00', 'doc': {'id': 'DOC1'}, 'summary': 'NOTES', 'proposals': [], 'changes': [], 'owner': {'uid': 'u_chen'}, 'review': {'state': 'reading'}}
tx = {'members': ['u_alan', 'u_owner'], 'text': 'SECRET-WORDS', 'lines': []}
r = json.loads(psql(f"select public.meet_file('qa', $${json.dumps(mt)}$$::jsonb, $${json.dumps(tx)}$$::jsonb);").stdout.strip())
o = view('owner')
m = [x for x in o['meetings'] if x['id'] == 'mtL']
ok(r['id'] == 'mtL' and r['merged'] and len(o['meetings']) == 1, f'meet_file: the doc joins the live record of that day: {r}')
ok(m and m[0]['doc']['id'] == 'DOC1' and m[0]['summary'] == 'NOTES' and m[0]['proposals'] == [{'id': 'keep'}] and len(m[0]['changes']) == 1 and m[0]['owner']['uid'] == 'u_alan' and m[0]['title'] == 'Weekly Jobs', f"meet_file: the record's lists, owner and title stay: {m}")
ok('SECRET-WORDS' not in json.dumps(o['meetings']) and o.get('meettx:mtL', {}).get('text') == 'SECRET-WORDS', 'meet_file: the words are on their own row')
ok('meettx:mtL' in view('pm') and 'meettx:mtL' not in view('foreman') and 'meettx:mtL' not in view('crew'), 'an attendee reads the transcript; nobody else does')
person('billing', 'billing', 'u_billing')
ok('meettx:mtL' not in view('billing') and any(x['id'] == 'mtL' for x in view('billing')['meetings']), 'the office who were not there see the meeting, not its words')
rows, err = as_('billing', "select json_agg(name) from public.collections where name like 'meettx:%';")
ok(not err and (not rows or rows[0] in ('', None)), f'nor hear of it in the change feed: {rows} {err[:120]}')
r = save('billing', [{'name': 'meettx:mtL', 'data': {'members': ['u_billing'], 'text': 'X'}, 'base': ver('owner', 'meettx:mtL')}])['meettx:mtL']
ok(r.get('refused') and view('owner')['meettx:mtL']['text'] == 'SECRET-WORDS', f'nor write it, or add themselves: {r}')
r = save('foreman', [{'name': 'meettx:mtZ', 'data': {'members': ['u_angel'], 'text': 'X'}, 'base': 0}])['meettx:mtZ']
ok(r.get('refused'), f'the field never writes a transcript: {r}')
again = json.loads(psql(f"select public.meet_file('qa', $${json.dumps({'id': 'mtL', 'review': {'state': 'new'}})}$$::jsonb, $${json.dumps({'extract': {'items': [1]}})}$$::jsonb);").stdout.strip())
o = view('owner')
ok(again['id'] == 'mtL' and [x for x in o['meetings'] if x['id'] == 'mtL'][0]['review']['state'] == 'new' and o['meettx:mtL']['extract'] == {'items': [1]} and o['meettx:mtL']['text'] == 'SECRET-WORDS', 'meet_file: the background read adds its items and moves the review on')
other = json.loads(psql(f"select public.meet_file('qa', $${json.dumps({'id': 'mtPM', 'date': '2026-09-03', 'start': '2026-09-03T15:00:00', 'doc': {'id': 'DOC2'}, 'title': 'Afternoon'})}$$::jsonb, null);").stdout.strip())
ok(other['id'] == 'mtPM' and not other['merged'] and len(view('owner')['meetings']) == 2, f'meet_file: an afternoon meeting on the same day is its own meeting: {other}')
rows, err = as_('owner', "select public.meet_file('qa', '{\"id\":\"x\"}'::jsonb, null);")
ok(err and 'permission' in err.lower(), f'meet_file is the server\'s only: {err[:120]}')

psql(f'drop database if exists {DBN};', db='postgres')
print('ALL PASS' if not fails else f'{len(fails)} FAILED', f'({n} checks)')
sys.exit(1 if fails else 0)
