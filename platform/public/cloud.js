/* SmartDesigns Projects: the cloud layer (Supabase: Postgres, auth, storage, realtime).
   Rebuilt 2026-10-18 from legacy/hosted-app-2026-09-15.zip (public/cloud.js). The app keeps its in-memory DB;
   this layer stores it as one row per collection (company, clients, … and one row per project) and keeps every
   device in step. What changed from the old copy:
   - The workspace comes from the person's profile on the server, never from the page's config.
   - Every save says which version it was based on. If another device saved first, the server refuses that
     collection; this layer merges record by record (merge3) and saves again. Two people editing different
     records both keep their edits; the same field edited on two devices keeps the server's value and says so.
   - A change from another device is merged into unsynced local edits instead of replacing them.
   - Unsynced edits leave a marker in localStorage; the next boot pushes them before it pulls, so a local edit
     is never overwritten by the server copy. On pagehide a small change is sent with a keepalive request.
   - Calls to this site's /api/* carry the person's session token, so the AI proxy knows who is asking.
   When no config is present the app runs exactly as before: local, one device. */
window.Cloud = (() => {
  const cfg = window.SDP_CONFIG || {};
  let sb = null, session = null, profile = null, channel = null, onChange = null, dbRef = () => window.DB, poller = null;
  const last = {};      // name -> hash of the JSON last in step with the server
  const base = {};      // name -> the server's copy as last synced (the common ancestor for merges)
  const versions = {};  // name -> server version we hold
  const state = {online: navigator.onLine, syncing: false, pending: false, err: '', note: '', noteAt: 0, conflicts: 0};
  const on = () => !!(cfg.supabaseUrl && cfg.supabaseAnonKey && window.supabase);
  const ws = () => (profile && profile.workspace_id) || '';
  const hash = s => { let h = 0; for (let i = 0; i < s.length; i++) { h = (h * 31 + s.charCodeAt(i)) | 0; } return h + ':' + s.length; };
  const clone = v => v === undefined ? undefined : JSON.parse(JSON.stringify(v));
  const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);

  // ---- role lists (the server enforces the same lists in schema.sql; these only avoid sending what it refuses)
  const OFFICE = ['owner', 'pm', 'coord', 'designer', 'design_mgr', 'billing', 'controller'];
  const FIELD = ['foreman', 'crew', 'driver'];
  const FIELD_HIDDEN = ['gl', 'txns', 'bills', 'inbills', 'payroll', 'accounts', 'rules', 'vendorStats', 'audit', 'deals', 'properties',
    'investors', 'raises', 'partners', 'principals', 'mbinc', 'mb', 'spend', 'cards', 'bankImports', 'bankRecons', 'bankFeeds',
    'bankPending', 'bankReconDraft', 'payments', 'statements', 'periods', 'cpSpend', 'mktSpend', 'employees', 'leads',
    'priceWatch', 'slBench', 'sourcing', 'lib', 'catalog', 'entities', 'integrations', 'conn', 'learn', 'brainQueue', 'lessons'];
  const FIELD_READONLY = ['__meta', 'company', 'clients', 'users', 'vendors', 'stock', 'inventory', 'obligations', 'watches', 'migrations'];
  const isOffice = () => OFFICE.includes(profile && profile.role);
  const isField = () => FIELD.includes(profile && profile.role);
  const mayWrite = name => name.startsWith('own:') || isOffice() || (isField() && !FIELD_HIDDEN.includes(name) && !FIELD_READONLY.includes(name));

  // ---- the pending marker: unsynced edits survive a closed tab or a dead battery
  const pkey = () => 'sdp:pending:' + (user() ? user().id : '');
  const vkey = () => 'sdp:versions:' + (user() ? user().id : '');
  const mark = names => { try { localStorage.setItem(pkey(), JSON.stringify({at: Date.now(), names})); localStorage.setItem(vkey(), JSON.stringify(versions)); } catch (e) {} };
  const unmark = () => { try { localStorage.removeItem(pkey()); localStorage.setItem(vkey(), JSON.stringify(versions)); } catch (e) {} };
  function hasPending() { try { return !!localStorage.getItem(pkey()); } catch (e) { return false; } }
  function savedVersions() { try { return JSON.parse(localStorage.getItem(vkey()) || '{}'); } catch (e) { return {}; } }

  // ---- the session token on this site's /api/* calls
  const fetch0 = window.fetch.bind(window);
  window.fetch = function (input, init) {
    try {
      const url = new URL(typeof input === 'string' ? input : input.url, location.href);
      if (url.origin === location.origin && url.pathname.startsWith('/api/') && session && session.access_token) {
        init = Object.assign({}, init);
        const h = new Headers(init.headers || (typeof input !== 'string' && input.headers) || {});
        if (!h.has('authorization')) h.set('authorization', 'Bearer ' + session.access_token);
        init.headers = h;
      }
    } catch (e) {}
    return fetch0(input, init);
  };

  async function init() {
    if (!on()) return false;
    sb = window.supabase.createClient(cfg.supabaseUrl, cfg.supabaseAnonKey, {auth: {persistSession: true, autoRefreshToken: true, detectSessionInUrl: true}});
    const {data} = await sb.auth.getSession(); session = data.session || null;
    sb.auth.onAuthStateChange((_e, s) => { session = s; });
    window.addEventListener('online', () => { state.online = true; if (state.pending) push(dbRef()); });
    window.addEventListener('offline', () => { state.online = false; });
    window.addEventListener('pagehide', keepalive);
    document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') keepalive(); else if (user()) pollOnce(); });
    return true;
  }
  const user = () => (session && session.user) || null;
  async function signIn(email, password) { const {data, error} = await sb.auth.signInWithPassword({email, password}); if (error) throw error; session = data.session; profile = null; return session; }
  // Google sign-in: Supabase sends the person to Google and back. Sign-up is off, so a Google account with no
  // invitation comes back with an error in the address, which authError() hands to the sign-in screen.
  async function signInGoogle() { const {error} = await sb.auth.signInWithOAuth({provider: 'google', options: {redirectTo: location.origin + location.pathname, queryParams: {prompt: 'select_account'}}}); if (error) throw error; }
  function authError() {
    const q = new URLSearchParams(location.search + '&' + location.hash.replace(/^#/, ''));
    const d = q.get('error_description') || q.get('error'); if (!d) return '';
    try { history.replaceState(null, '', location.pathname); } catch (e) {}
    return /signups? not allowed|user not found/i.test(d) ? 'This Google account has no invitation. Ask the office to invite the same email address.' : d.replace(/\+/g, ' ');
  }
  async function magicLink(email) { const {error} = await sb.auth.signInWithOtp({email, options: {emailRedirectTo: location.origin + location.pathname, shouldCreateUser: false}}); if (error) throw error; }
  async function resetPassword(email) { const {error} = await sb.auth.resetPasswordForEmail(email, {redirectTo: location.origin + location.pathname}); if (error) throw error; }
  async function signOut() { try { await sb.auth.signOut(); } catch (e) {} session = null; profile = null; }
  async function getProfile() {
    if (profile) return profile; if (!user()) return null;
    const {data, error} = await sb.from('profiles').select('*').eq('id', user().id).maybeSingle(); if (error) throw error;
    profile = data || null;
    if (profile && !OFFICE.includes(profile.role) && !FIELD.includes(profile.role)) state.err = 'This account has no access yet: ask the owner to set your role.';
    return profile;
  }

  // ---- merging: base is the common ancestor, local and server the two sides
  const isObj = v => v && typeof v === 'object' && !Array.isArray(v);
  const byId = a => Array.isArray(a) && a.length > 0 && a.every(x => isObj(x) && x.id != null);
  function merge3(b, l, s, conf) {
    if (eq(l, s)) return s;
    if (eq(l, b)) return s;                        // only the server changed
    if (eq(s, b)) return l;                        // only this device changed
    if ((byId(l) || byId(s)) && (Array.isArray(l) || l == null) && (Array.isArray(s) || s == null)) {
      const B = new Map((Array.isArray(b) ? b : []).filter(isObj).map(x => [String(x.id), x]));
      const L = new Map((l || []).map(x => [String(x.id), x]));
      const out = [];
      for (const sx of (s || [])) {
        const id = String(sx.id), lx = L.get(id), bx = B.get(id);
        if (lx !== undefined) out.push(merge3(bx, lx, sx, conf));
        else if (bx !== undefined && eq(sx, bx)) continue;          // deleted here, untouched there: stays deleted
        else { if (bx !== undefined) conf.n++; out.push(sx); }        // deleted here, changed there: keep theirs
      }
      const S = new Set((s || []).map(x => String(x.id)));
      for (const lx of (l || [])) {
        const id = String(lx.id); if (S.has(id)) continue;
        const bx = B.get(id);
        if (bx === undefined) out.push(lx);                           // new on this device
        else if (!eq(lx, bx)) { conf.n++; out.push(lx); }             // deleted there, changed here: keep ours, say so
      }
      return out;
    }
    if (isObj(l) && isObj(s)) {
      const out = {}, bo = isObj(b) ? b : {};
      for (const k of new Set([...Object.keys(s), ...Object.keys(l)])) {
        const v = merge3(bo[k], l[k], s[k], conf);
        if (v !== undefined) out[k] = v;
      }
      return out;
    }
    conf.n++; return s;                              // the same value changed on both: the server's stands
  }

  // ---- collections
  // ---- personal records: what came from one person's Google account never goes into a shared row
  // Each lives in own:<sign-in id>:<collection>, which the database lets only that sign-in read or write.
  // `priv` says which records are personal; a device only ever sends its own person's (owner === me).
  const fromAccount = it => !!(it && it.owner && (it.source === 'google' || it.source === 'demo'));
  const PRIV = {
    comms: {kind: 'list', priv: fromAccount},                                           // mail
    gdrive: {kind: 'list', priv: it => !!(it && it.owner)},                              // Drive files
    calendar: {kind: 'nested', field: 'external', priv: e => !!(e && e.owner && e.source !== 'erp')},  // Google Calendar; ERP holds stay shared
    conn: {kind: 'keyed'},                                                                // each person's Google connection
    asst: {kind: 'keyed'},                                                                // each person's assistant: thread, memory, delegation
  };
  const meApp = () => window.__cloudPerson || null;                                         // the person in the app (DB.users id)
  const ownName = k => 'own:' + user().id + ':' + k;
  const ownIds = {};                                                                      // own shard -> ids (or keys) last put into DB
  function split(DB, k, out) {
    const r = PRIV[k], me = meApp(), mine = !!(me && user());
    if (r.kind === 'list') {
      const arr = Array.isArray(DB[k]) ? DB[k] : [];
      out[k] = arr.filter(i => !r.priv(i));
      if (mine) out[ownName(k)] = arr.filter(i => r.priv(i) && i.owner === me);
    } else if (r.kind === 'nested') {
      const obj = DB[k] || {}, arr = Array.isArray(obj[r.field]) ? obj[r.field] : [];
      out[k] = Object.assign({}, obj, {[r.field]: arr.filter(i => !r.priv(i))});
      if (mine) out[ownName(k)] = arr.filter(i => r.priv(i) && i.owner === me);
    } else {
      const obj = DB[k] || {}, people = new Set((DB.users || []).map(u => u.id)), shared = {};
      for (const key of Object.keys(obj)) if (!people.has(key)) shared[key] = obj[key];
      out[k] = shared;
      if (mine) out[ownName(k)] = obj[me] !== undefined ? {[me]: obj[me]} : {};
    }
  }
  // Settings of this device, not records of the firm: who is using it, their role and name, the job on screen,
  // notifications, the mail marker. Synced, one phone's save signed every other device in as that person.
  const DEVICE = ['deviceUser', 'role', 'me', 'currentId', 'notify', 'lastMail'];
  function shards(DB) {
    const out = {}; const meta = {};
    for (const k of Object.keys(DB)) { if (k === 'projects' || DEVICE.includes(k)) continue; if (k.startsWith('__')) { meta[k] = DB[k]; continue; } if (PRIV[k]) split(DB, k, out); else out[k] = DB[k]; }
    if (user() && meApp()) for (const k of Object.keys(PRIV)) if (!(ownName(k) in out)) split(DB, k, out);   // an emptied list still syncs as empty
    out.__meta = meta; (DB.projects || []).forEach(p => { out['project:' + p.id] = p; }); return out;
  }
  // Put one shard's value into DB: a whole collection, a project, or one part of a split collection.
  function setPart(DB, name, data) {
    if (name.startsWith('project:')) { const i = DB.projects.findIndex(p => p.id === data.id); i >= 0 ? (DB.projects[i] = data) : DB.projects.push(data); return 'projects'; }
    if (name === '__meta') { Object.assign(DB, data || {}); return null; }
    if (DEVICE.includes(name)) return null;                                                // never taken from the server
    const own = name.startsWith('own:'), k = own ? name.split(':').slice(2).join(':') : name, r = PRIV[k];
    if (!r) { DB[name] = data; return name; }
    if (r.kind === 'keyed') {
      if (own) { DB[k] = DB[k] || {}; (ownIds[name] || []).forEach(key => delete DB[k][key]); Object.assign(DB[k], data || {}); ownIds[name] = Object.keys(data || {}); }
      else { const keep = {}, people = new Set((DB.users || []).map(u => u.id)); for (const [key, v] of Object.entries(DB[k] || {})) if (people.has(key)) keep[key] = v; DB[k] = Object.assign({}, data || {}, keep); }
      return k;
    }
    const get = () => r.kind === 'list' ? (DB[k] || []) : ((DB[k] || {})[r.field] || []);
    const put = arr => { if (r.kind === 'list') DB[k] = arr; else { DB[k] = DB[k] || {}; DB[k][r.field] = arr; } };
    if (own) { const was = new Set(ownIds[name] || []); const list = Array.isArray(data) ? data : []; put(get().filter(i => !was.has(i && i.id)).concat(list)); ownIds[name] = list.map(i => i && i.id); }
    else if (r.kind === 'list') { DB[k] = (Array.isArray(data) ? data : []).concat((DB[k] || []).filter(r.priv)); }
    else { const keepPriv = ((DB[k] || {})[r.field] || []).filter(r.priv); DB[k] = Object.assign({}, data || {}); DB[k][r.field] = ((data || {})[r.field] || []).concat(keepPriv); }
    return k;
  }
  function remember(name, data, version) { last[name] = hash(JSON.stringify(data)); base[name] = clone(data); versions[name] = version; }
  function assemble(rows) {
    if (!rows.length) return null; const DB = {projects: []};
    const own = rows.filter(r => r.name.startsWith('own:'));
    for (const r of rows.filter(r => !r.name.startsWith('own:'))) { setPart(DB, r.name, r.data); remember(r.name, r.data, r.version); }
    for (const r of own) { setPart(DB, r.name, r.data); remember(r.name, r.data, r.version); }   // after the shared parts they join
    return DB;
  }
  async function pullAll() { const {data, error} = await sb.from('collections_view').select('name,data,version'); if (error) throw error; return assemble(data || []); }
  async function pullOne(name) { const {data, error} = await sb.from('collections_view').select('name,data,version').eq('name', name).maybeSingle(); if (error) throw error; return data; }

  // Put one collection's value into the app's DB (the app's own cloudApply re-renders).
  function applyLocal(name, data) {
    const DB = dbRef(); if (!DB) return;
    const k = setPart(DB, name, data);
    if (onChange && k) onChange(k === 'projects' ? name : k, k === 'projects' ? data : DB[k]);   // the app's cloudApply re-renders
  }
  // The server moved past us on `name`: merge our unsynced edits into its copy.
  function absorb(name, row) {
    const DB = dbRef(); const local = DB ? shards(DB)[name] : undefined;
    const dirty = local !== undefined && last[name] !== undefined && hash(JSON.stringify(local)) !== last[name];
    const conf = {n: 0};
    const merged = dirty ? merge3(base[name], local, row.data, conf) : row.data;
    remember(name, row.data, row.version);
    if (conf.n) { state.conflicts += conf.n; state.noteAt = Date.now(); state.note = `Merged with another device's change; ${conf.n} ${conf.n === 1 ? 'edit' : 'edits'} kept the other device's value`; console.warn('sync conflict', name, conf.n); }
    applyLocal(name, merged);
    return dirty;
  }

  async function push(DB, depth = 0) {
    if (!on() || !user()) return {ok: false, msg: 'not signed in'};
    if (!profile) { try { await getProfile(); } catch (e) {} }
    if (!isOffice() && !isField()) return {ok: false, msg: 'This account has no access yet: ask the owner to set your role'};
    const s = shards(DB); const items = []; const names = new Set(Object.keys(s));
    for (const [name, data] of Object.entries(s)) { if (!mayWrite(name)) continue; const str = JSON.stringify(data); if (str === undefined || last[name] === hash(str)) continue; items.push({name, data, base: versions[name] || 0}); }
    if (items.length) mark(items.map(i => i.name));
    if (!state.online) { state.pending = true; return {ok: false, msg: 'Offline: saved on this phone, will sync when back'}; }
    if (state.syncing) { state.pending = true; return {ok: true, msg: 'queued'}; }
    state.syncing = true; state.pending = false;
    if (state.note && Date.now() - state.noteAt > 60000) state.note = '';
    try {
      let again = false;
      if (items.length) {
        const {data: res, error} = await sb.rpc('save_collections', {p_items: items}); if (error) throw error;
        const sent = new Map(items.map(i => [i.name, i.data]));
        for (const r of (res || [])) {
          if (r.conflict) { const row = await pullOne(r.name); if (row) { absorb(r.name, row); again = true; } }
          else if (r.refused) { last[r.name] = hash(JSON.stringify(sent.get(r.name))); }
          else remember(r.name, sent.get(r.name), r.version);
        }
      }
      if (isOffice()) { const gone = Object.keys(last).filter(n => n.startsWith('project:') && !names.has(n)); if (gone.length) { const {error} = await sb.rpc('delete_collections', {p_names: gone}); if (error) throw error; gone.forEach(n => { delete last[n]; delete base[n]; delete versions[n]; }); } }
      state.err = ''; state.syncing = false;
      if (again && depth < 3) return push(dbRef(), depth + 1);
      unmark();
      if (state.pending) setTimeout(() => push(dbRef()), 300);
      return {ok: true, n: items.length, note: state.note};
    } catch (e) { state.syncing = false; state.err = e.message || String(e); state.pending = true; setTimeout(() => push(dbRef()), 15000); return {ok: false, msg: 'Not synced yet: ' + state.err}; }
  }
  // Boot: edits left unsynced by the last session go up before the server copy comes down.
  async function pushPending(localDB) {
    let names = [];
    try { names = (JSON.parse(localStorage.getItem(pkey()) || '{}').names) || []; } catch (e) {}
    if (!names.length || !localDB) { unmark(); return {ok: true, n: 0}; }
    const vs = savedVersions(); const s = shards(localDB); const items = [];
    for (const name of names) if (mayWrite(name) && s[name] !== undefined) items.push({name, data: s[name], base: vs[name] || 0});
    if (!items.length) { unmark(); return {ok: true, n: 0}; }
    const {data: res, error} = await sb.rpc('save_collections', {p_items: items}); if (error) return {ok: false, msg: error.message};
    let kept = 0;
    for (const r of (res || [])) {
      if (!r.conflict) continue;
      // No common ancestor survives a reload: keep the server's records and add the ones only this phone has.
      const row = await pullOne(r.name); if (!row) continue;
      const mine = s[r.name]; const conf = {n: 0};
      const merged = merge3(undefined, mine, row.data, conf);
      if (!eq(merged, row.data)) { const {data: res2} = await sb.rpc('save_collections', {p_items: [{name: r.name, data: merged, base: row.version}]}); if (res2 && res2[0] && !res2[0].conflict) kept++; }
    }
    unmark();
    return {ok: true, n: items.length, kept};
  }
  function keepalive() {
    if (!on() || !user() || !session) return;
    const DB = dbRef(); if (!DB) return;
    const s = shards(DB); const items = [];
    for (const [name, data] of Object.entries(s)) { if (!mayWrite(name)) continue; const str = JSON.stringify(data); if (last[name] !== hash(str)) items.push({name, data, base: versions[name] || 0}); }
    if (!items.length) return;
    mark(items.map(i => i.name));
    const body = JSON.stringify({p_items: items});
    if (body.length > 60000) return;               // too big for a keepalive request: the marker covers it next boot
    try { fetch0(cfg.supabaseUrl + '/rest/v1/rpc/save_collections', {method: 'POST', keepalive: true, headers: {'content-type': 'application/json', apikey: cfg.supabaseAnonKey, authorization: 'Bearer ' + session.access_token}, body}); } catch (e) {}
  }

  // Another device changed a row: refetch it through the view (field roles never see money) and merge it in.
  async function remoteChanged(name, version) {
    if (versions[name] && version <= versions[name]) return;      // our own write, or older
    try { const row = await pullOne(name); if (!row) return; const dirty = absorb(name, row); if (dirty) push(dbRef()); } catch (e) { console.warn('refetch failed', e); }
  }
  async function pollOnce() {
    if (!sb || !user() || !profile) return;
    try { const {data, error} = await sb.rpc('collection_versions'); if (error) return; for (const r of (data || [])) if (!versions[r.name] || r.version > versions[r.name]) await remoteChanged(r.name, r.version); } catch (e) {}
  }
  function subscribe(cb) {
    onChange = cb; if (channel) return;
    channel = sb.channel('collections').on('postgres_changes', {event: '*', schema: 'public', table: 'collections', filter: `workspace_id=eq.${ws()}`}, payload => {
      const name = (payload.new && payload.new.name) || (payload.old && payload.old.name); if (!name) return;
      if (payload.eventType === 'DELETE') { delete last[name]; delete base[name]; delete versions[name]; onChange && onChange(name, null); return; }
      remoteChanged(name, payload.new.version);
    }).subscribe();
    // The change feed can drop on a phone's network; a light poll of versions catches anything it missed.
    poller = setInterval(() => { if (document.visibilityState === 'visible') pollOnce(); }, 30000);
  }

  // ---- files (photos, documents)
  const dataUrlToBlob = d => { const [meta, b64] = d.split(','); const mime = (meta.match(/data:(.*?);/) || [])[1] || 'application/octet-stream'; const bin = atob(b64); const arr = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i); return new Blob([arr], {type: mime}); };
  const blobToDataUrl = b => new Promise((res, rej) => { const r = new FileReader(); r.onload = () => res(r.result); r.onerror = rej; r.readAsDataURL(b); });
  async function putBlob(id, dataUrl) { if (!on() || !user() || !ws()) return false; const blob = dataUrlToBlob(dataUrl); const {error} = await sb.storage.from('files').upload(`${ws()}/${id}`, blob, {upsert: true, contentType: blob.type}); if (error) { console.warn('upload failed', error); return false; } return true; }
  async function getBlob(id) { if (!on() || !user() || !ws()) return null; const {data, error} = await sb.storage.from('files').download(`${ws()}/${id}`); if (error || !data) return null; return await blobToDataUrl(data); }

  // ---- the team (the owner sets roles; the database enforces it)
  async function listProfiles() { const {data, error} = await sb.from('profiles').select('*').order('name'); if (error) throw error; return data; }
  async function updateProfile(id, patch) { const {error} = await sb.from('profiles').update(patch).eq('id', id); if (error) throw error; return true; }
  async function aiSpend() { const {data, error} = await sb.from('ai_usage').select('at,user_id,tier,model,cost_usd').order('at', {ascending: false}).limit(500); if (error) throw error; return data || []; }
  // Not rebuilt yet (M&B signals, the web clipper): the screens that call these show nothing rather than fail.
  const none = async () => [];

  return {on, init, isOffice, isField, token: () => (session && session.access_token) || '', setDbRef: f => { dbRef = f; }, user, profile: getProfile,
    signIn, signInGoogle, authError, magicLink, resetPassword, signOut, pullAll, pullOne, push, pushPending, hasPending, subscribe, pollOnce, putBlob, getBlob,
    listProfiles, updateProfile, aiSpend, listSignals: none, setSignalStatus: async () => true, listClips: none, claimClips: async () => 0,
    saveClipToken: async () => true, screenPoint: async () => null, state, shards, merge3, cfg,
    _test: {session: s => { session = s; }, setPart: (DB, n, d) => setPart(DB, n, d)}};
})();
