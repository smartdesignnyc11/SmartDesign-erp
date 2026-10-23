"""The hosted copy, offline: the app with the real cloud layer (platform/public/cloud.js) over an in-memory stand-in for
Supabase, held here in Python so several browser contexts (the owner's laptop, the coordinator's phone) share one server.
It answers what cloud.js asks (the session, profiles, the collections view, save_collections with versions and
conflicts, collection_versions, the workspace calls) and /api/team (no email is ever sent: invitations are recorded).
Row security is not modelled here (platform/test/workspace_pg_test.py proves it on Postgres): every person here is an
office role and reads their workspace. Used by tests/team_ws_test.py."""
import json, os, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MOCK_JS = r"""
(() => {
  const call = async (op, a) => JSON.parse(await window.__srv(window.__mockUid || '', op, JSON.stringify(a === undefined ? null : a)));
  const q = (table) => {
    const st = {table, filters: [], single: false, patch: null};
    const b = {
      select() { return b; }, eq(k, v) { st.filters.push([k, v]); return b; }, order() { return b; }, limit() { return b; },
      maybeSingle() { st.single = true; return b; }, update(p) { st.patch = p; return b; },
      then(res, rej) { return call(st.patch ? 'update' : 'select', st).then(r => (r && r.__error ? {data: null, error: {message: r.__error}} : {data: r, error: null})).then(res, rej); },
    };
    return b;
  };
  window.supabase = {createClient: () => ({
    auth: {
      getSession: async () => ({data: {session: await call('session')}}),
      onAuthStateChange() {}, signInWithPassword: async () => ({data: {session: await call('session')}}),
      signInWithOtp: async () => ({}), resetPasswordForEmail: async () => ({}), signInWithOAuth: async () => ({}), signOut: async () => ({}),
    },
    rpc: async (fn, args) => { const r = await call('rpc', {fn, args}); return r && r.__error ? {data: null, error: {message: r.__error}} : {data: r, error: null}; },
    from: q,
    channel: () => { const c = {on() { return c; }, subscribe() { return c; }}; return c; },
    storage: {from: () => ({upload: async () => ({error: null}), download: async () => ({data: null, error: {message: 'none'}})})},
  })};
  const f0 = window.fetch.bind(window);
  window.fetch = async (input, init) => {
    const u = typeof input === 'string' ? input : input.url;
    if (/\/api\/team$/.test(u)) { const r = await call('team', JSON.parse((init && init.body) || '{}')); return new Response(JSON.stringify(r.body), {status: r.status}); }
    if (/\/api\//.test(u)) return new Response('{"ok":false}', {status: 404});
    return f0(input, init);
  };
})();
"""

def hosted_page():
    """dist/ with the cloud layer in its head, as platform/build.py puts it, written outside the repo."""
    html = open(os.environ.get('SD_DIST') or os.path.join(ROOT, 'dist', 'smartdesigns_projects.html'), encoding='utf-8').read()
    cloud = open(os.path.join(ROOT, 'platform', 'public', 'cloud.js'), encoding='utf-8').read()
    OPEN = '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n'
    assert html.startswith(OPEN)
    cfg = {'appName': 'SmartDesigns Projects', 'supabaseUrl': 'https://mock.invalid', 'supabaseAnonKey': 'anon', 'aiUrl': '/api/ai', 'functions': '/api', 'googleSignIn': False, 'vapidPublicKey': '', 'build': 'test'}
    tags = '<script>' + MOCK_JS + '</script>\n<script>window.SDP_CONFIG = ' + json.dumps(cfg) + ';</script>\n<script>' + cloud.replace('</script', '<\\/script') + '</script>\n'
    d = tempfile.mkdtemp(prefix='sd_hosted_')
    p = os.path.join(d, 'index.html')
    open(p, 'w', encoding='utf-8').write(OPEN + tags + html[len(OPEN):])
    return 'file://' + p

class Server:
    DEVICE = {'deviceUser', 'role', 'me', 'currentId', 'notify', 'lastMail'}
    def __init__(self):
        self.ws = {}          # id -> {kind, name}
        self.profiles = {}    # uid -> profile
        self.rows = {}        # (ws, name) -> {'data', 'version'}
        self.invites = []
        self.saves = []
    def person(self, uid, email, name, role, ws, others=(), app_user_id=None):
        self.profiles[uid] = {'id': uid, 'email': email, 'name': name, 'role': role, 'workspace_id': ws, 'workspaces': list(others), 'app_user_id': app_user_id, 'private_key': None, 'phone': ''}
    def info(self, p):
        w = self.ws.get(p['workspace_id'], {})
        return {'id': p['workspace_id'], 'kind': w.get('kind', 'demo'), 'name': w.get('name') or p['workspace_id'],
                'others': [{'id': o, 'kind': self.ws.get(o, {}).get('kind', 'demo'), 'name': self.ws.get(o, {}).get('name') or o} for o in p['workspaces'] if o != p['workspace_id']]}
    def names(self, ws):
        return sorted(n for (w, n) in self.rows if w == ws)
    def data(self, ws):
        return {n: r['data'] for (w, n), r in self.rows.items() if w == ws}
    async def handle(self, uid, op, raw):
        a = json.loads(raw) if raw else None
        p = self.profiles.get(uid)
        if op == 'session':
            return json.dumps({'user': {'id': uid, 'email': p['email']}, 'access_token': 'tok-' + uid} if p else None)
        if not p: return json.dumps({'__error': 'not signed in'})
        ws = p['workspace_id']
        if op == 'select':
            if a['table'] == 'profiles':
                f = dict(a['filters'])
                L = [dict(x) for x in self.profiles.values() if (('id' in f and x['id'] == f['id']) or ('id' not in f and x['workspace_id'] == ws))]
                return json.dumps((L[0] if L else None) if a['single'] else L)
            if a['table'] == 'collections_view':
                f = dict(a['filters'])
                L = [{'name': n, 'data': r['data'], 'version': r['version']} for (w, n), r in self.rows.items() if w == ws and ('name' not in f or n == f['name'])]
                return json.dumps((L[0] if L else None) if a['single'] else L)
            return json.dumps([])
        if op == 'update':
            if a['table'] == 'profiles':
                f = dict(a['filters']); t = self.profiles.get(f.get('id'))
                if t and p['role'] == 'owner' and t['workspace_id'] == ws:
                    for k in ('name', 'role', 'app_user_id', 'phone'):
                        if k in a['patch']: t[k] = a['patch'][k]
                    return json.dumps(None)
                return json.dumps({'__error': 'permission denied'})
            return json.dumps(None)
        if op == 'team':
            if p['role'] != 'owner': return json.dumps({'status': 403, 'body': {'error': 'only the owner invites'}})
            em = (a.get('email') or '').lower(); found = [x for x in self.profiles.values() if x['email'] == em]
            self.invites.append({'email': em, 'role': a.get('role'), 'appUserId': a.get('appUserId'), 'name': a.get('name'), 'sent': not found})
            if found:
                t = found[0]; moved = t['workspace_id'] != ws
                if moved: t['workspaces'] = sorted(set(t['workspaces'] + [t['workspace_id']]) - {ws}); t['workspace_id'] = ws
            else:
                nid = 'auth-' + em.split('@')[0]; self.person(nid, em, a.get('name') or em, 'none', ws); t = self.profiles[nid]; moved = False
            t.update({'role': a.get('role'), 'app_user_id': a.get('appUserId') or None, 'workspace_id': ws})
            if a.get('name'): t['name'] = a['name']
            return json.dumps({'status': 200, 'body': {'invited': not found, 'moved': moved, 'id': t['id'], 'email': em, 'role': t['role']}})
        if op == 'rpc':
            fn, args = a['fn'], a.get('args') or {}
            if fn == 'session_alive': return json.dumps(True)
            if fn == 'my_workspace_info': return json.dumps(self.info(p))
            if fn == 'collection_versions': return json.dumps([{'name': n, 'version': r['version']} for (w, n), r in self.rows.items() if w == ws])
            if fn == 'switch_workspace':
                to = args['p_ws']
                if to != ws and to not in p['workspaces']: return json.dumps({'__error': 'not one of your workspaces'})
                p['workspaces'] = sorted((set(p['workspaces']) - {to}) | {ws}); p['workspace_id'] = to
                return json.dumps(self.info(p))
            if fn == 'save_collections':
                out = []
                for it in args['p_items']:
                    nm = it['name']
                    if nm in self.DEVICE: out.append({'name': nm, 'refused': True}); continue
                    cur = self.rows.get((ws, nm)); base = it.get('base')
                    if cur and base is not None and base < cur['version']: out.append({'name': nm, 'conflict': True, 'version': cur['version']}); continue
                    v = (cur['version'] + 1) if cur else 1
                    self.rows[(ws, nm)] = {'data': it['data'], 'version': v}; self.saves.append((ws, nm)); out.append({'name': nm, 'version': v})
                return json.dumps(out)
            if fn == 'delete_collections':
                for nm in args.get('p_names') or []: self.rows.pop((ws, nm), None)
                return json.dumps(None)
            return json.dumps(None)
        return json.dumps({'__error': 'unknown op ' + op})

async def open_hosted(browser, server, url, uid, phone=False, when='2026-10-26T13:30:00Z'):
    """A device signed in as `uid` (a key of server.profiles) on the hosted copy, its clock at `when` (the wall clock)."""
    from harness import DESKTOP, PHONE
    ctx = await browser.new_context(viewport=PHONE if phone else DESKTOP, is_mobile=phone, has_touch=phone)
    await ctx.expose_function('__srv', server.handle)
    await ctx.add_init_script(f'window.__mockUid = {json.dumps(uid)};')
    pg = await ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    if when: await pg.clock.install(time=when)
    await pg.goto(url)
    await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=90000)
    await pg.wait_for_timeout(600)
    return ctx, pg, errs
