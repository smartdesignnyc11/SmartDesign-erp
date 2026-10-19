// Personal records (mail, Google Calendar, Drive, the Google connection, the assistant) go only into the person's
// own shard, never a shared one, and come back where the app expects them. Run: node test/private_test.mjs
import fs from 'node:fs'; import vm from 'node:vm'; import assert from 'node:assert/strict';
const src = fs.readFileSync(new URL('../public/cloud.js', import.meta.url), 'utf8');
const ctx = {window: {fetch: async () => {}, SDP_CONFIG: {}, __cloudPerson: 'uA'}, navigator: {onLine: true}, location: {href: 'https://x/', origin: 'https://x'}, URL, Headers, localStorage: {getItem: () => null, setItem() {}, removeItem() {}}, document: {addEventListener() {}}, console};
ctx.window.window = ctx.window; vm.createContext(ctx); vm.runInContext(src, ctx);
const C = ctx.window.Cloud; C._test.session({user: {id: 'auth-A'}, access_token: 't'});
const J = v => JSON.parse(JSON.stringify(v));
let n = 0; const ok = (c, msg) => { assert.ok(c, msg); n++; };
const DB = {users: [{id: 'uA'}, {id: 'uB'}], projects: [{id: 'p1'}],
  comms: [{id: 'm1', owner: 'uA', source: 'google', text: 'A private'}, {id: 'm2', owner: 'uB', source: 'google', text: 'B private'},
          {id: 'm3', text: 'job chat'}, {id: 'm4', owner: 'uA', source: 'manual', text: 'logged call'}],
  gdrive: [{id: 'f1', owner: 'uA'}, {id: 'f2', owner: 'uB'}],
  calendar: {external: [{id: 'e1', owner: 'uA', source: 'google'}, {id: 'e2', owner: 'uA', source: 'erp'}, {id: 'e3', owner: 'uB', source: 'google'}], prefs: 1},
  conn: {uA: {google: {email: 'a@x'}}, uB: {google: {email: 'b@x'}}},
  asst: {uA: {thread: [1]}, uB: {thread: [2]}, settings: {x: 1}}};
const s = J(C.shards(DB));
const shared = JSON.stringify(Object.entries(s).filter(([k]) => !k.startsWith('own:')));
ok(!shared.includes('A private') && !shared.includes('B private'), 'no Google mail in any shared shard');
ok(s.comms.map(x => x.id).join() === 'm3,m4', 'job chat and logged calls stay shared');
ok(s['own:auth-A:comms'].map(x => x.id).join() === 'm1', 'my mail goes to my own shard');
ok(!JSON.stringify(s).includes('B private') && !Object.keys(s).some(k => k.includes('uB') || k.includes('auth-B')), "another person's records are never sent from this device");
ok(s.gdrive.length === 0 && s['own:auth-A:gdrive'].map(x => x.id).join() === 'f1', 'Drive files private');
ok(s.calendar.external.map(x => x.id).join() === 'e2' && s.calendar.prefs === 1 && s['own:auth-A:calendar'].map(x => x.id).join() === 'e1', 'Google events private, ERP holds shared');
ok(JSON.stringify(s.conn) === '{}' && s['own:auth-A:conn'].uA.google.email === 'a@x', 'my Google connection private');
ok(JSON.stringify(s.asst) === '{"settings":{"x":1}}' && s['own:auth-A:asst'].uA.thread[0] === 1, "my assistant private; the firm's settings shared");
// the server hands back the shared rows and my own; the app gets one DB.comms etc.
const back = {users: J(DB.users), projects: []};
for (const [k, v] of Object.entries(s)) if (!k.startsWith('own:') && k !== '__meta' && !k.startsWith('project:')) C._test.setPart(back, k, J(v));
for (const [k, v] of Object.entries(s)) if (k.startsWith('own:')) C._test.setPart(back, k, J(v));
ok(back.comms.map(x => x.id).sort().join() === 'm1,m3,m4', 'mail rejoins DB.comms');
ok(back.calendar.external.map(x => x.id).sort().join() === 'e1,e2' && back.calendar.prefs === 1, 'events rejoin DB.calendar.external');
ok(back.conn.uA && back.asst.uA && back.asst.settings, 'connection and assistant rejoin');
// another device of mine deleted m1 and added m9: the own shard update replaces exactly my part
C._test.setPart(back, 'own:auth-A:comms', [{id: 'm9', owner: 'uA', source: 'google'}]);
ok(back.comms.map(x => x.id).sort().join() === 'm3,m4,m9', 'an update to my shard replaces my part only');
C._test.setPart(back, 'comms', [{id: 'm3'}, {id: 'm5'}]);
ok(back.comms.map(x => x.id).sort().join() === 'm3,m5,m9', 'an update to the shared part keeps my mail');
// an emptied list still syncs, so a deleted last mail does not come back
const e = J(C.shards({users: DB.users, projects: [], comms: []}));
ok(Array.isArray(e['own:auth-A:comms']) && e['own:auth-A:comms'].length === 0, 'an empty own shard is still sent');
// before the person is known (boot), personal records are neither shared nor sent
ctx.window.__cloudPerson = null;
const pre = J(C.shards(DB));
ok(!JSON.stringify(pre).includes('private') && !Object.keys(pre).some(k => k.startsWith('own:')), 'before sign-in mapping nothing personal is sent');
const d = J(C.shards({users: DB.users, projects: [], deviceUser: 'uA', role: 'owner', me: 'Alan', currentId: 'p1', notify: true, lastMail: 'x', clients: []}));
ok(!['deviceUser', 'role', 'me', 'currentId', 'notify', 'lastMail'].some(k => k in d) && 'clients' in d, 'device settings (who is on this phone, the open job) are never synced');
const dev = {deviceUser: 'uA', role: 'owner'}; C._test.setPart(dev, 'deviceUser', 'uB'); C._test.setPart(dev, 'role', 'foreman');
ok(dev.deviceUser === 'uA' && dev.role === 'owner', 'and never taken from the server');
console.log('ALL PASS', `(${n} checks)`);
