// A person's private lists (mail, Google Calendar entries, Drive files: the own:<sign-in>:<list> rows) never hold one
// id twice (public/cloud.js setPart, split, drainInbox). Live 11-13: the owner's 36 demo mails became 72 on the
// device and then on the server. The device had made those records itself, so the sync layer did not know them as
// "the ones the server gave me"; when the server's copy of the same row arrived (the echo of the device's own save
// landing before the save's answer, a version poll in that gap, or the person's other device saving), it was added
// beside them instead of replacing them. Invented data. Run: node test/cloud_own_dup_test.mjs
import fs from 'node:fs'; import vm from 'node:vm'; import assert from 'node:assert/strict';
const src = fs.readFileSync(new URL('../public/cloud.js', import.meta.url), 'utf8');
const J = v => JSON.parse(JSON.stringify(v));
let n = 0; const ok = (a, b, msg) => { assert.deepEqual(a, b, msg); n++; };
const wait = ms => new Promise(r => setTimeout(r, ms));
const ME = 'u_owner', AUTH = 'auth-owner', OWN = k => `own:${AUTH}:${k}`;

// A device: a fresh cloud layer over a mocked server. server.afterCommit runs once inside the next save, after the
// rows are written and before the save's answer reaches the device (where the change feed's echo can land);
// server.beforeCommit runs once before the next save is looked at (another writer getting in first).
function device(server) {
  const handed = [];
  const ctx = {window: {fetch: async () => {}, SDP_CONFIG: {supabaseUrl: 'https://db', supabaseAnonKey: 'anon'}, supabase: {}, __cloudPerson: ME, gsIngestServer: box => { handed.push(J(box)); return 1; }},
    navigator: {onLine: true}, location: {href: 'https://x/', origin: 'https://x'}, URL, Headers,
    localStorage: {getItem: () => null, setItem() {}, removeItem() {}}, document: {addEventListener() {}, visibilityState: 'visible'}, console, setTimeout, clearTimeout};
  ctx.window.window = ctx.window; vm.createContext(ctx); vm.runInContext(src, ctx);
  const C = ctx.window.Cloud, T = C._test;
  const all = () => Object.entries(server.rows).map(([name, r]) => ({name, data: J(r.data), version: r.v}));
  T.sb({
    rpc: async (fn, args) => {
      if (fn === 'session_alive') return {data: true};
      if (fn === 'collection_versions') return {data: Object.entries(server.rows).map(([name, r]) => ({name, version: r.v}))};
      if (fn === 'save_collections') {
        if (server.beforeCommit) { const f = server.beforeCommit; server.beforeCommit = null; await f(); }
        const res = args.p_items.map(it => { const r = server.rows[it.name]; if (r && r.v !== it.base) return {name: it.name, conflict: true}; server.rows[it.name] = {v: (r ? r.v : 0) + 1, data: J(it.data)}; return {name: it.name, version: server.rows[it.name].v}; });
        if (server.afterCommit) { const f = server.afterCommit; server.afterCommit = null; await f(); }
        return {data: res};
      }
      throw new Error('rpc ' + fn);
    },
    from: () => ({select: () => ({then: (res, rej) => Promise.resolve({data: all()}).then(res, rej),
      eq: (k, name) => ({maybeSingle: async () => { const r = server.rows[name]; return {data: r ? {name, data: J(r.data), version: r.v} : null}; }})})}),
  });
  T.session({user: {id: AUTH}, access_token: 't'}); T.profile({role: 'owner', workspace_id: 'qa'});
  return {C, T, handed, win: ctx.window};
}
const mails = (k = 36, tag = 'm') => Array.from({length: k}, (_, i) => ({id: `cm_${tag}${i}`, msgId: `g_${tag}${i}`, owner: ME, source: 'demo', subject: 'Invented ' + i}));
const firm = () => ({users: [{id: ME}], projects: [], comms: [{id: 'cm_job', text: 'job chat'}, ...mails()],
  calendar: {external: [{id: 'ev_1', owner: ME, source: 'demo'}, {id: 'ev_hold', source: 'erp'}], prefs: 1}, gdrive: [{id: 'gd_1', owner: ME}, {id: 'gd_2', owner: ME}]});
const mine = DB => DB.comms.filter(c => c.owner === ME).map(c => c.id);
const dup = ids => ids.length - new Set(ids).size;
const counts = DB => [mine(DB).length, dup(DB.comms.map(c => c.id)), DB.calendar.external.length, dup(DB.calendar.external.map(e => e.id)), DB.gdrive.length, dup(DB.gdrive.map(f => f.id))];

// 1. The first save's echo lands before its answer (the live failure): still 36, each id once, here and on the server.
{ const server = {rows: {}}; const {C, T} = device(server); const DB = firm(); C.setDbRef(() => DB);
  server.afterCommit = () => T.pollOnce();
  await C.push(DB);
  ok(counts(DB), [36, 0, 2, 0, 2, 0], 'echo of the first save: the private lists are not doubled on the device');
  await C.push(DB);
  ok([server.rows[OWN('comms')].data.length, dup(server.rows[OWN('comms')].data.map(c => c.id)), server.rows.comms.data.map(c => c.id)], [36, 0, ['cm_job']], 'nor on the server; the shared row holds only the job chat'); }

// 2. The echo of a later save (the device changed a mail it made itself, and is dirty when the echo lands).
{ const server = {rows: {}}; const {C, T} = device(server); const DB = firm(); C.setDbRef(() => DB);
  await C.push(DB);
  DB.comms[1].unread = false;
  server.afterCommit = () => T.pollOnce();
  await C.push(DB); await C.push(DB);
  ok([counts(DB), server.rows[OWN('comms')].data.length], [[36, 0, 2, 0, 2, 0], 36], 'echo of a later save: not doubled'); }

// 3. The person's other device saved the same row with one more mail, event and file: one of each id, the new ones added.
{ const server = {rows: {}}; const {C, T} = device(server); const DB = firm(); C.setDbRef(() => DB);
  await C.push(DB);
  for (const [k, x] of [['comms', {id: 'cm_new', msgId: 'g_new', owner: ME, source: 'demo'}], ['calendar', {id: 'ev_2', owner: ME, source: 'demo'}], ['gdrive', {id: 'gd_3', owner: ME}]]) {
    const r = server.rows[OWN(k)]; server.rows[OWN(k)] = {v: r.v + 1, data: [...r.data, x]}; }
  await T.pollOnce();
  ok(counts(DB), [37, 0, 3, 0, 3, 0], 'the other device\'s save: its new records arrive, nothing this device made is doubled');
  ok(DB.calendar.external.some(e => e.id === 'ev_hold') && DB.comms.some(c => c.id === 'cm_job'), true, 'the shared entries stay'); }

// 3b. The other device deleted a mail this device had made and saved: it goes here too, and is not sent back.
{ const server = {rows: {}}; const {C, T} = device(server); const DB = firm(); C.setDbRef(() => DB);
  await C.push(DB);
  const r = server.rows[OWN('comms')]; server.rows[OWN('comms')] = {v: r.v + 1, data: r.data.filter(c => c.id !== 'cm_m5')};
  await T.pollOnce(); await C.push(DB);
  ok([mine(DB).length, mine(DB).includes('cm_m5'), server.rows[OWN('comms')].data.length], [35, false, 35], 'a mail deleted on the other device goes here and stays gone on the server'); }

// 4. A row the bug already doubled on the server heals: the next open holds each id once and saves it back clean.
{ const once = mails(); const server = {rows: {comms: {v: 3, data: [{id: 'cm_job', text: 'job chat'}]}, users: {v: 1, data: [{id: ME}]}, [OWN('comms')]: {v: 4, data: [...once, ...J(once)]}}};
  const {C} = device(server); const DB = await C.pullAll(); C.setDbRef(() => DB);
  ok([mine(DB).length, dup(DB.comms.map(c => c.id))], [36, 0], 'a doubled server row opens with each id once');
  await C.push(DB);
  ok([server.rows[OWN('comms')].data.length, server.rows[OWN('comms')].v], [36, 5], 'and is saved back clean'); }

// 5. A device whose own list is already doubled never sends an id twice.
{ const server = {rows: {}}; const {C} = device(server); const DB = firm(); DB.comms.push(...J(mails())); DB.gdrive.push({id: 'gd_1', owner: ME});
  const s = C.shards(DB);
  ok([s[OWN('comms')].length, s[OWN('gdrive')].length], [36, 2], 'the own rows sent hold each id once'); }

// 6. The watcher's inbox: what the app was handed once is not handed again when the emptying save is refused because
// the watcher added more meanwhile (the row is read again and holds the earlier finds too). A changed item is new.
{ const g = i => ({id: 'g' + i, snippet: 'invented ' + i});
  const server = {rows: {}}; const {C, T, handed} = device(server); const DB = firm(); C.setDbRef(() => DB);
  await C.push(DB);
  server.rows[OWN('inbox')] = {v: 1, data: {gmail: [g(1), g(2)], cal: [{id: 'e1', summary: 'Walkthrough'}]}};
  server.beforeCommit = () => { server.rows[OWN('inbox')] = {v: 9, data: {gmail: [g(1), g(2), g(3)], cal: [{id: 'e1', summary: 'Walkthrough moved'}]}}; };   // the watcher's next run, mid-drain
  await T.pollOnce(); await wait(900);
  const got = handed.map(b => [(b.gmail || []).map(m => m.id).join(), (b.cal || []).map(e => e.summary).join()]);
  ok(got, [['g1,g2', 'Walkthrough'], ['g3', 'Walkthrough moved']], 'each inbox find is handed to the app once; a changed entry is handed as new');
  ok(server.rows[OWN('inbox')].data, {}, 'and the inbox ends empty'); }
console.log('ALL PASS', `(${n} checks)`);
