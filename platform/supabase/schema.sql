-- SmartDesigns Projects: the hosted database (Supabase Postgres).
-- Rebuilt 2026-10-18 from legacy/hosted-app-2026-09-15.zip (supabase/schema.sql), with these changes:
--   * A person's role comes only from public.profiles, which only the owner edits. Sign-up metadata is ignored
--     (the old trigger trusted raw_user_meta_data.role, which the person signing up controls).
--   * New accounts start as role 'none' and see nothing until the owner sets their role.
--   * Clients (and the M&B roles) are refused by the server until per-client rows exist (BACKLOG §5 item 2):
--     the firm's data is one JSON document per collection, so row security cannot hide another client's records.
--   * Field roles (foreman, crew, driver) never receive the money collections, and money keys are stripped
--     from what they do receive; their saves get the stripped keys restored from the stored row.
--   * Saves carry the version they were based on. A stale save is refused per collection (conflict), and the
--     page merges record by record and saves again, so one phone never silently overwrites another.
--   * ai_usage logs every AI call (who, when, model, tokens, cost), never the prompt or the answer.
-- Run order: this file once, then any later migrations. It is idempotent.

-- ---------------------------------------------------------------- people and roles
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text,
  name text,
  role text not null default 'none',
  app_user_id text,                 -- the person in the app (DB.users[].id), set by the owner
  phone text,
  workspace_id text not null default 'smartdesign',
  created_at timestamptz default now()
);
alter table public.profiles drop constraint if exists profiles_role_check;
alter table public.profiles add constraint profiles_role_check check (role in
  ('none','owner','pm','coord','foreman','crew','driver','designer','design_mgr','billing','controller','client','mb_admin','mb_user','mb_analyst','mb_readonly'));

create or replace function public.handle_new_user() returns trigger language plpgsql security definer set search_path = public as $$
begin
  -- The role is never taken from sign-up metadata: the owner sets it.
  insert into public.profiles (id, email, name, role)
  values (new.id, lower(new.email), coalesce(new.raw_user_meta_data->>'name', split_part(new.email,'@',1)), 'none')
  on conflict (id) do nothing;
  return new;
end $$;
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created after insert on auth.users for each row execute procedure public.handle_new_user();

-- A signed-in request counts only while its session is alive: Sign Out Everywhere deletes the sessions, and
-- from that moment the phone's still-unexpired key reads and writes nothing (not an hour later).
create or replace function public.session_alive() returns boolean language sql stable security definer set search_path = public, auth as $$
  select exists (select 1 from auth.sessions s where s.id = nullif(auth.jwt()->>'session_id', '')::uuid and s.user_id = auth.uid());
$$;
grant execute on function public.session_alive() to authenticated;
create or replace function public.my_role() returns text language sql stable security definer set search_path = public as $$
  select case when public.session_alive() then coalesce((select role from public.profiles where id = auth.uid()), 'none') else 'none' end;
$$;
create or replace function public.my_workspace() returns text language sql stable security definer set search_path = public as $$
  select coalesce((select workspace_id from public.profiles where id = auth.uid()), '');
$$;
-- Office roles read and write everything in their workspace.
create or replace function public.is_office() returns boolean language sql stable security definer set search_path = public as $$
  select public.my_role() in ('owner','pm','coord','designer','design_mgr','billing','controller');
$$;
-- Field roles read the working collections with money stripped.
create or replace function public.is_field() returns boolean language sql stable security definer set search_path = public as $$
  select public.my_role() in ('foreman','crew','driver');
$$;
create or replace function public.is_member() returns boolean language sql stable security definer set search_path = public as $$
  select public.is_office() or public.is_field();
$$;

-- Whose private rows a sign-in reads: its own, unless the server has linked several sign-ins of one person
-- (Alan's two addresses). Only the server sets it: the column is not granted to anyone signed in.
alter table public.profiles add column if not exists private_key text;
create or replace function public.my_private_key() returns text language sql stable security definer set search_path = public as $$
  select coalesce((select nullif(private_key, '') from public.profiles where id = auth.uid()), auth.uid()::text);
$$;

-- The person a sign-in is in the app (DB.users id), set by the owner; direct and group message threads are visible
-- by it. Unset: no threads.
create or replace function public.my_app_user() returns text language sql stable security definer set search_path = public as $$
  select nullif((select app_user_id from public.profiles where id = auth.uid()), '');
$$;
create or replace function public.thread_member(d jsonb) returns boolean language sql stable security definer set search_path = public as $$
  select public.my_app_user() is not null and coalesce(d->'members', '[]'::jsonb) ? public.my_app_user();
$$;
-- The field's jobs (2026-10-19). A job's crew is the job's own list of people (p.team, DB.users ids), set by the PM or
-- the owner. A field sign-in reads and writes only the jobs whose crew names its person; a job with no crew list is
-- the office's alone (privacy by default: a new job reaches nobody in the field until someone is put on it).
create or replace function public.field_job(d jsonb) returns boolean language sql stable security definer set search_path = public as $$
  select public.my_app_user() is not null and jsonb_typeof(d->'team') = 'array' and (d->'team') ? public.my_app_user();
$$;
-- A field save of a job keeps the stored crew list: the field never changes who is on a job, so nobody can put
-- himself on another job or take a colleague off one.
create or replace function public.keep_team(old jsonb, nw jsonb) returns jsonb language sql immutable as $$
  select case when jsonb_typeof(nw) is distinct from 'object' then old
              when old ? 'team' then nw || jsonb_build_object('team', old->'team')
              else nw - 'team' end;
$$;

-- ---------------------------------------------------------------- what field roles may not see or write
-- Collections a field phone never receives (money, books, bank, people's pay, deals and investors).
create or replace function public.field_hidden() returns text[] language sql immutable as $$
  select array['gl','txns','bills','inbills','payroll','accounts','rules','vendorStats','audit','deals','properties',
               'investors','raises','partners','principals','mbinc','mb','spend','cards','bankImports','bankRecons','bankFeeds',
               'bankPending','bankReconDraft','payments','statements','periods','cpSpend','mktSpend','employees','leads',
               'priceWatch','slBench','sourcing','lib','catalog','entities','integrations','conn','learn','brainQueue','lessons']::text[];
$$;
-- Collections a field phone may read but never write.
create or replace function public.field_readonly() returns text[] language sql immutable as $$
  select array['__meta','company','clients','users','vendors','stock','inventory','obligations','watches','migrations']::text[];
$$;
create or replace function public.money_keys() returns text[] language sql immutable as $$
  select array['rate','burden','billRate','price','unitPrice','cost','unitCost','total','subtotal','amount','amt','contract','retainer',
               'budget','margin','minMargin','markup','gross','net','taxes','tax','fee','deposit','paid','balance','bank','routing',
               'account','accountNumber','ein','ssn','tin','salary','pay','payRate','wage','payroll','bills','invoices','payments',
               'changeOrders','estimates','costVar','ap','ar','txns','accounts','byCode','sov','lines_price','retainage','credit',
               'value','eac','profit','overhead','cash']::text[];
$$;

create or replace function public.strip_money(j jsonb) returns jsonb language plpgsql immutable as $$
declare k text; v jsonb; out jsonb; keys text[] := public.money_keys();
begin
  if j is null then return null; end if;
  if jsonb_typeof(j) = 'object' then
    out := '{}'::jsonb;
    for k, v in select * from jsonb_each(j) loop
      if k = any(keys) then continue; end if;
      out := out || jsonb_build_object(k, public.strip_money(v));
    end loop;
    return out;
  elsif jsonb_typeof(j) = 'array' then
    select coalesce(jsonb_agg(public.strip_money(e)), '[]'::jsonb) into out from jsonb_array_elements(j) e;
    return out;
  end if;
  return j;
end $$;

-- A field phone saves back a stripped copy: put the stripped keys back from the stored row (matched by id in arrays).
create or replace function public.restore_money(old jsonb, nw jsonb) returns jsonb language plpgsql immutable as $$
declare k text; v jsonb; out jsonb; e jsonb; o jsonb; i int; keys text[] := public.money_keys();
begin
  if nw is null then return old; end if;
  if old is null then return public.strip_money(nw); end if;   -- a new record from the field carries no money
  if jsonb_typeof(nw) = 'object' and jsonb_typeof(old) = 'object' then
    out := '{}'::jsonb;
    for k, v in select * from jsonb_each(nw) loop
      if k = any(keys) then continue; end if;                   -- the field never writes a money key
      out := out || jsonb_build_object(k, public.restore_money(old->k, v));
    end loop;
    for k, v in select * from jsonb_each(old) loop
      if k = any(keys) then out := out || jsonb_build_object(k, v); end if;
    end loop;
    return out;
  elsif jsonb_typeof(nw) = 'array' and jsonb_typeof(old) = 'array' then
    out := '[]'::jsonb; i := 0;
    for e in select * from jsonb_array_elements(nw) loop
      o := null;
      if jsonb_typeof(e) = 'object' and e ? 'id' then
        select x into o from jsonb_array_elements(old) x where jsonb_typeof(x) = 'object' and x->>'id' = e->>'id' limit 1;
      elsif jsonb_array_length(old) > i then
        o := old->i;
      end if;
      out := out || jsonb_build_array(public.restore_money(o, e)); i := i + 1;
    end loop;
    return out;
  end if;
  return nw;
end $$;

-- ---------------------------------------------------------------- the firm's data
create table if not exists public.collections (
  workspace_id text not null,
  name text not null,                  -- company | clients | pos | … | project:<id>
  data jsonb not null,
  version integer not null default 1,
  updated_by uuid,
  updated_at timestamptz default now(),
  primary key (workspace_id, name)
);
alter table public.collections enable row level security;
alter table public.profiles enable row level security;

-- Every read goes through this view. It runs as its owner, so it does its own checks: members of the workspace only,
-- office roles see everything, field roles see the working collections with money stripped, everyone else nothing.
create or replace view public.collections_view with (security_invoker = false) as
  select c.workspace_id, c.name, c.version, c.updated_by, c.updated_at,
         case when public.is_office() then c.data else public.strip_money(c.data) end as data
  from public.collections c
  where c.workspace_id = public.my_workspace()
    and (public.is_office() or (public.is_field() and not (c.name = any(public.field_hidden()))))
    -- A person's own rows (own:<their sign-in id>:<collection>): the mail, calendar and Drive files from their
    -- Google account, their connection and their assistant's memory. Nobody else reads them, the owner included.
    and (c.name not like 'own:%' or split_part(c.name, ':', 2) = public.my_private_key())
    -- A direct or group message thread (one row each, thread:<id>) is read by its members only, the owner included.
    and (c.name not like 'thread:%' or public.thread_member(c.data))
    -- A job (project:<id>) reaches a field sign-in only when its crew list names that person.
    and (c.name not like 'project:%' or public.is_office() or public.field_job(c.data));
revoke all on public.collections_view from anon;
grant select on public.collections_view to authenticated;

-- No direct table access from the page at all: reads through the view, writes through save_collections.
revoke all on public.collections from anon, authenticated;

drop policy if exists "profiles: read own or owner" on public.profiles;
create policy "profiles: read own or owner" on public.profiles for select to authenticated
  using (id = auth.uid() or (public.my_role() in ('owner','pm') and workspace_id = public.my_workspace()));
drop policy if exists "profiles: owner edits" on public.profiles;
create policy "profiles: owner edits" on public.profiles for update to authenticated
  using (public.my_role() = 'owner' and workspace_id = public.my_workspace())
  with check (public.my_role() = 'owner' and workspace_id = public.my_workspace());
revoke insert, delete on public.profiles from anon, authenticated;
revoke update on public.profiles from anon, authenticated;
grant update (name, role, app_user_id, phone) on public.profiles to authenticated;

-- Save many collections in one call: [{name, data, base}] -> [{name, version} | {name, conflict:true, version}].
-- base is the version the page last held; a save based on an older version is refused for that collection.
create or replace function public.save_collections(p_items jsonb) returns jsonb language plpgsql security definer set search_path = public as $$
declare it jsonb; nm text; cur record; newv int; base int; result jsonb := '[]'::jsonb;
  office boolean := public.is_office(); field boolean := public.is_field(); wsid text := public.my_workspace();
begin
  if auth.uid() is null then raise exception 'not signed in'; end if;
  if not (office or field) or wsid = '' then raise exception 'this account has no access yet: ask the owner to set your role'; end if;
  for it in select * from jsonb_array_elements(p_items) loop
    nm := it->>'name';
    if nm is null or length(nm) > 200 then continue; end if;
    if nm in ('deviceUser','role','me','currentId','notify','lastMail') then   -- settings of one device, never shared
      result := result || jsonb_build_array(jsonb_build_object('name', nm, 'refused', true)); continue;
    end if;
    if nm like 'thread:%' and not (public.thread_member(it->'data') and not exists (select 1 from public.collections x where x.workspace_id = wsid and x.name = nm and not public.thread_member(x.data))) then
      -- a thread is written only by a member, and an existing thread only by one of its members
      result := result || jsonb_build_array(jsonb_build_object('name', nm, 'refused', true)); continue;
    end if;
    if nm like 'own:%' and split_part(nm, ':', 2) <> public.my_private_key() then
      result := result || jsonb_build_array(jsonb_build_object('name', nm, 'refused', true)); continue;
    end if;
    if field and nm not like 'own:%' and nm not like 'thread:%' and (nm = any(public.field_hidden()) or nm = any(public.field_readonly())) then
      result := result || jsonb_build_array(jsonb_build_object('name', nm, 'refused', true)); continue;
    end if;
    if field and nm like 'project:%' and not exists (select 1 from public.collections x where x.workspace_id = wsid and x.name = nm and public.field_job(x.data)) then
      -- the field writes only the jobs it is on, and never starts one
      result := result || jsonb_build_array(jsonb_build_object('name', nm, 'refused', true)); continue;
    end if;
    base := nullif(it->>'base','')::int;
    select * into cur from public.collections c where c.workspace_id = wsid and c.name = nm for update;
    if found then
      if base is not null and base < cur.version then
        result := result || jsonb_build_array(jsonb_build_object('name', nm, 'conflict', true, 'version', cur.version)); continue;
      end if;
      newv := cur.version + 1;
      update public.collections
         set data = case when office then it->'data'
                         when nm like 'project:%' then public.keep_team(cur.data, public.restore_money(cur.data, it->'data'))
                         else public.restore_money(cur.data, it->'data') end,
             version = newv, updated_by = auth.uid(), updated_at = now()
       where workspace_id = wsid and name = nm;
    else
      if field and nm not like 'project:%' and nm not like 'own:%' and nm not like 'thread:%' and nm not in ('field','time','photos','tasks','comms','meetings') then
        result := result || jsonb_build_array(jsonb_build_object('name', nm, 'refused', true)); continue;
      end if;
      newv := 1;
      insert into public.collections (workspace_id, name, data, version, updated_by)
      values (wsid, nm, case when office then it->'data' else public.strip_money(it->'data') end, 1, auth.uid());
    end if;
    result := result || jsonb_build_array(jsonb_build_object('name', nm, 'version', newv));
  end loop;
  return result;
end $$;
revoke all on function public.save_collections(jsonb) from public, anon;
grant execute on function public.save_collections(jsonb) to authenticated;

create or replace function public.delete_collections(p_names text[]) returns void language plpgsql security definer set search_path = public as $$
begin
  if not public.is_office() then raise exception 'office roles only'; end if;
  delete from public.collections where workspace_id = public.my_workspace() and name = any(p_names) and name like 'project:%';
end $$;
revoke all on function public.delete_collections(text[]) from public, anon;
grant execute on function public.delete_collections(text[]) to authenticated;

-- Realtime: the page is told a row changed (name and version only matter) and refetches it through the view,
-- so a field phone never receives unstripped data from the change feed. Realtime honours the table's RLS, and the
-- page has no table grant, so it gets the event through this policy only for its own workspace.
drop policy if exists "collections: members see change events" on public.collections;
-- The same rules as the view decide who is told: another person's own rows, a thread one is not in, and a job a field
-- person is not on are never announced to them, not even by name.
create policy "collections: members see change events" on public.collections for select to authenticated
  using (workspace_id = public.my_workspace() and public.is_member()
    and (name not like 'own:%' or split_part(name, ':', 2) = public.my_private_key())
    and (name not like 'thread:%' or public.thread_member(data))
    and (name not like 'project:%' or public.is_office() or public.field_job(data)));
grant select (workspace_id, name, version, updated_by, updated_at) on public.collections to authenticated;
do $$ begin
  alter publication supabase_realtime add table public.collections;
exception when duplicate_object then null; end $$;

-- ---------------------------------------------------------------- files (photos, documents)
insert into storage.buckets (id, name, public) values ('files','files',false) on conflict (id) do nothing;
drop policy if exists "files: members read" on storage.objects;
create policy "files: members read" on storage.objects for select to authenticated
  using (bucket_id = 'files' and public.is_member() and split_part(name,'/',1) = public.my_workspace());
drop policy if exists "files: members write" on storage.objects;
create policy "files: members write" on storage.objects for insert to authenticated
  with check (bucket_id = 'files' and public.is_member() and split_part(name,'/',1) = public.my_workspace());
drop policy if exists "files: members update" on storage.objects;
create policy "files: members update" on storage.objects for update to authenticated
  using (bucket_id = 'files' and public.is_member() and split_part(name,'/',1) = public.my_workspace());

-- ---------------------------------------------------------------- AI spend
-- One row per call. Written only by the server (service role); never the prompt or the answer.
create table if not exists public.ai_usage (
  id bigserial primary key,
  at timestamptz not null default now(),
  user_id uuid,
  workspace_id text,
  tier text,
  model text,
  input_tokens integer default 0,
  output_tokens integer default 0,
  cache_read_tokens integer default 0,
  cache_write_tokens integer default 0,
  cost_usd numeric(12,6) default 0,
  status integer
);
create index if not exists ai_usage_ws_at on public.ai_usage (workspace_id, at);
create index if not exists ai_usage_user_at on public.ai_usage (user_id, at);
alter table public.ai_usage enable row level security;
revoke all on public.ai_usage from anon, authenticated;
grant select on public.ai_usage to authenticated;
drop policy if exists "ai_usage: own, or owner and controller" on public.ai_usage;
create policy "ai_usage: own, or owner and controller" on public.ai_usage for select to authenticated
  using (user_id = auth.uid() or (public.my_role() in ('owner','controller') and workspace_id = public.my_workspace()));

-- The page's fallback when the change feed is down: what it may see, and each row's version.
create or replace function public.collection_versions() returns table(name text, version integer, updated_at timestamptz)
language sql stable security definer set search_path = public as $$
  select v.name, v.version, v.updated_at from public.collections_view v;
$$;
revoke all on function public.collection_versions() from public, anon;
grant execute on function public.collection_versions() to authenticated;

-- This month's AI spend (New York calendar month) for the firm and for one person. Server only.
create or replace function public.ai_spend(p_ws text, p_user uuid) returns jsonb language sql stable security definer set search_path = public as $$
  with m as (select (date_trunc('month', now() at time zone 'America/New_York') at time zone 'America/New_York') as start)
  select jsonb_build_object(
    'firm', coalesce((select sum(cost_usd) from public.ai_usage u, m where u.workspace_id = p_ws and u.at >= m.start), 0),
    'user', coalesce((select sum(cost_usd) from public.ai_usage u, m where u.user_id = p_user and u.at >= m.start), 0));
$$;
revoke all on function public.ai_spend(text, uuid) from public, anon, authenticated;

-- One-time cleanup (2026-10-19): device settings that early builds synced as if they were the firm's records.
delete from public.collections where name in ('deviceUser','role','me','currentId','notify','lastMail');

-- ---------------------------------------------------------------- the Google watcher (2026-10-19)
-- One row per person who handed the server their long-lived Google key. The key is sealed (AES-256-GCM with
-- WATCH_KEY, which lives only in Netlify); nothing signed in can read this table at all, only the server.
create table if not exists public.google_watch (
  person_key text primary key,
  workspace_id text not null,
  app_user_id text,
  email text,
  sealed text not null,
  scopes text,
  cursors jsonb not null default '{}'::jsonb,
  connected_at timestamptz default now(),
  last_run timestamptz,
  last_ok timestamptz,
  last_error text default ''
);
alter table public.google_watch enable row level security;
revoke all on public.google_watch from anon, authenticated;

-- The watcher adds what it found to the person's inbox row; the app files it and empties it.
create or replace function public.watch_put_inbox(p_ws text, p_key text, p_items jsonb) returns integer
language plpgsql security definer set search_path = public as $$
declare nm text := 'own:' || p_key || ':inbox'; cur jsonb; k text; merged jsonb; v int;
begin
  select data into cur from public.collections where workspace_id = p_ws and name = nm for update;
  merged := coalesce(cur, '{}'::jsonb);
  for k in select * from jsonb_object_keys(p_items) loop
    merged := jsonb_set(merged, array[k], coalesce(merged->k, '[]'::jsonb) || (p_items->k), true);
  end loop;
  insert into public.collections (workspace_id, name, data, version) values (p_ws, nm, merged, 1)
  on conflict (workspace_id, name) do update set data = excluded.data, version = public.collections.version + 1, updated_at = now()
  returning version into v;
  return v;
end $$;
revoke all on function public.watch_put_inbox(text, text, jsonb) from public, anon, authenticated;

-- What a person may see of their own watch: connected, when it last ran, the last error. Never the key.
create or replace function public.my_watch() returns jsonb language sql stable security definer set search_path = public as $$
  select coalesce((select jsonb_build_object('watching', true, 'email', email, 'connectedAt', connected_at, 'lastRun', last_run, 'lastOk', last_ok, 'lastError', last_error)
    from public.google_watch where person_key = public.my_private_key()), jsonb_build_object('watching', false));
$$;
revoke all on function public.my_watch() from public, anon;
grant execute on function public.my_watch() to authenticated;

-- ---------------------------------------------------------------- push notifications (2026-10-19)
-- One row per phone or browser that said yes to notifications, filed under the person's private key.
create table if not exists public.push_subs (
  endpoint text primary key,
  person_key text not null,
  workspace_id text not null,
  sub jsonb not null,
  created_at timestamptz default now(),
  last_ok timestamptz,
  fails integer default 0
);
create index if not exists push_subs_person on public.push_subs (person_key);
alter table public.push_subs enable row level security;
revoke all on public.push_subs from anon, authenticated;
create or replace function public.push_subscribe(p_sub jsonb) returns void language plpgsql security definer set search_path = public as $$
begin
  if not public.is_member() then raise exception 'no access'; end if;
  if coalesce(p_sub->>'endpoint', '') !~ '^https://' then raise exception 'bad subscription'; end if;
  insert into public.push_subs (endpoint, person_key, workspace_id, sub) values (p_sub->>'endpoint', public.my_private_key(), public.my_workspace(), p_sub)
  on conflict (endpoint) do update set person_key = excluded.person_key, workspace_id = excluded.workspace_id, sub = excluded.sub, fails = 0;
end $$;
create or replace function public.push_unsubscribe(p_endpoint text) returns void language sql security definer set search_path = public as $$
  delete from public.push_subs where endpoint = p_endpoint and person_key = public.my_private_key();
$$;
revoke all on function public.push_subscribe(jsonb) from public, anon;
revoke all on function public.push_unsubscribe(text) from public, anon;
grant execute on function public.push_subscribe(jsonb) to authenticated;
grant execute on function public.push_unsubscribe(text) to authenticated;

-- ---------------------------------------------------------------- sign out everywhere (2026-10-19)
-- Ends every session of one sign-in and removes the person's notification registrations (subject lines on a
-- lost phone's lock screen stop). Server only; the team function checks who may ask.
create or replace function public.admin_signout(p_user uuid) returns integer language plpgsql security definer set search_path = public, auth as $$
declare n integer; pk text;
begin
  select coalesce(nullif(private_key, ''), id::text) into pk from public.profiles where id = p_user;
  delete from auth.sessions where user_id = p_user;
  get diagnostics n = row_count;
  delete from public.push_subs where person_key = pk;
  return n;
end $$;
revoke all on function public.admin_signout(uuid) from public, anon, authenticated;
create or replace function public.session_alive_for(p_session uuid, p_user uuid) returns boolean language sql stable security definer set search_path = public, auth as $$
  select exists (select 1 from auth.sessions where id = p_session and user_id = p_user);
$$;
revoke all on function public.session_alive_for(uuid, uuid) from public, anon, authenticated;

-- ---------------------------------------------------------------- the books' seals, held by the server (2026-10-19)
-- When a month closes, the server recomputes the chain over that month's postings from its own copy of the books
-- (SHA-256, and the app's FNV head to compare) and keeps the seal here. Add-only: no one can change or delete a seal,
-- the owner included; a reopened and re-closed month gets a new row. Verify recomputes from the server's books.
create table if not exists public.period_seals (
  id bigserial primary key,
  workspace_id text not null,
  ym text not null,
  n integer not null,
  head_sha text not null,
  head_fnv text,
  app_head text,
  matches boolean,
  links jsonb not null,
  sealed_at timestamptz not null default now(),
  by_user uuid,
  by_name text
);
create index if not exists period_seals_ws_ym on public.period_seals (workspace_id, ym, sealed_at desc);
alter table public.period_seals enable row level security;
revoke all on public.period_seals from anon, authenticated;

-- Threads are rows of their own now (thread:<id>); a single shared "threads" row would show every DM to everyone.
delete from public.collections where name = 'threads';

-- ---------------------------------------------------------------- message notifications (2026-10-19)
-- /api/notify pushes a new message to the other members of a direct or group thread, or to a person @mentioned in a
-- job's thread: at most one per conversation per person every 2 minutes, so a burst of lines is one buzz. Server only.
create table if not exists public.notify_sent (
  person_key text not null,
  thread_key text not null,
  workspace_id text not null,
  at timestamptz not null default now(),
  primary key (person_key, thread_key)
);
alter table public.notify_sent enable row level security;
revoke all on public.notify_sent from anon, authenticated;
-- True when this person may be told about this conversation now (and records that they were); false inside 2 minutes.
create or replace function public.notify_claim(p_key text, p_thread text, p_ws text) returns boolean language plpgsql security definer set search_path = public as $$
declare n integer;
begin
  insert into public.notify_sent (person_key, thread_key, workspace_id, at) values (p_key, p_thread, p_ws, now())
  on conflict (person_key, thread_key) do update set at = now(), workspace_id = excluded.workspace_id
    where public.notify_sent.at < now() - interval '2 minutes';
  get diagnostics n = row_count;
  return n > 0;
end $$;
revoke all on function public.notify_claim(text, text, text) from public, anon, authenticated;
