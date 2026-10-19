// A field phone drops a job it may no longer read (public/cloud.js): the PM takes the person off a job, and the next
// version check, change event or refused save takes it off the phone. Run: node test/fieldjobs_test.mjs
import fs from 'node:fs'; import vm from 'node:vm'; import assert from 'node:assert/strict';
const src = fs.readFileSync(new URL('../public/cloud.js', import.meta.url), 'utf8');
const ctx = {window: {fetch: async () => {}, SDP_CONFIG: {supabaseUrl: "https://db", supabaseAnonKey: "anon"}, supabase: {}, __cloudPerson: 'u_angel'}, navigator: {onLine: true}, location: {href: 'https://x/', origin: 'https://x'}, URL, Headers,
  localStorage: {getItem: () => null, setItem() {}, removeItem() {}}, document: {addEventListener() {}, visibilityState: 'visible'}, console, setTimeout, clearTimeout};
ctx.window.window = ctx.window; vm.createContext(ctx); vm.runInContext(src, ctx);
const C = ctx.window.Cloud, T = C._test;
let n = 0; const ok = (c, msg) => { assert.ok(c, msg); n++; };
const job = (id, team) => ({id, project: {name: 'Job ' + id}, team, chat: []});
const server = {rows: {'project:pA': {v: 3, data: job('pA', ['u_angel'])}, 'project:pB': {v: 2, data: job('pB', ['u_angel'])}, 'thread:t1': {v: 1, data: {id: 't1', members: ['u_angel', 'u_chen'], msgs: []}}, tasks: {v: 1, data: []}}, saves: []};
const visible = () => Object.entries(server.rows).filter(([k, r]) => !k.startsWith('project:') || (r.data.team || []).includes('u_angel'));
T.sb({
  rpc: async (fn, args) => {
    if (fn === 'session_alive') return {data: true};
    if (fn === 'collection_versions') return {data: visible().map(([name, r]) => ({name, version: r.v}))};
    if (fn === 'save_collections') { server.saves.push(args.p_items); return {data: args.p_items.map(it => visible().some(([k]) => k === it.name) || !it.name.startsWith('project:') ? {name: it.name, version: 9} : {name: it.name, refused: true})}; }
    throw new Error('rpc ' + fn);
  },
  from: () => ({select: () => ({eq: (k, name) => ({maybeSingle: async () => { const r = visible().find(([k2]) => k2 === name); return {data: r ? {name, data: r[1].data, version: r[1].v} : null}; }})})}),
});
T.session({user: {id: 'auth-angel'}, access_token: 't'}); T.profile({role: 'foreman', workspace_id: 'qa'});
const DB = ctx.window.DB = {users: [{id: 'u_angel'}, {id: 'u_chen'}], projects: [job('pA', ['u_angel']), job('pB', ['u_angel'])], threads: [server.rows['thread:t1'].data], tasks: []};
C.setDbRef(() => DB);
for (const [k, r] of Object.entries(server.rows)) T.remember(k, r.data, r.v);
const told = []; T.subscribe((name, data) => { told.push([name, data]); if (data === null && name.startsWith('project:')) DB.projects = DB.projects.filter(p => 'project:' + p.id !== name); });
// nothing changed: nothing dropped
await T.pollOnce();
ok(DB.projects.length === 2 && !told.length, 'while the foreman is on both jobs the phone keeps both');
// the PM takes him off job B: the version list no longer shows it, and the phone drops it
server.rows['project:pB'] = {v: 3, data: job('pB', ['u_alberto'])};
await T.pollOnce();
ok(DB.projects.map(p => p.id).join() === 'pA', 'the job he was taken off leaves the phone at the next version check');
ok(told.some(([k, d]) => k === 'project:pB' && d === null) && T.versions['project:pB'] === undefined, 'the app is told (cloudApply removes it) and the sync forgets it');
// a refused save of a job (taken off between checks) drops it too, and is not retried
server.rows['project:pA'] = {v: 4, data: job('pA', [])};
DB.projects[0].chat.push({id: 'c1', text: 'framing done'});
await C.push(DB);
ok(!DB.projects.length && T.versions['project:pA'] === undefined, 'a save the server refuses because the job was taken off him drops the job');
const before = server.saves.length; await C.push(DB);
ok(server.saves.length === before || !server.saves.slice(before).flat().some(i => i.name === 'project:pA'), 'and the phone does not keep sending it');
// a thread he was taken out of goes the same way; the shared collections are never dropped
delete server.rows['thread:t1'];
await T.pollOnce();
ok(!DB.threads.length && told.some(([k]) => k === 'threads'), 'a thread no longer his leaves the phone');
ok(T.versions.tasks === 1 && Array.isArray(DB.tasks), 'a shared collection is never dropped by this');
console.log('ALL PASS', `(${n} checks)`);
