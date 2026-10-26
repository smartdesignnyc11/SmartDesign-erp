// Personal records (mail, Google Calendar, Drive, the Google connection, the assistant) go only into the person's
// own shard, never a shared one, and come back where the app expects them. Run: node test/private_test.mjs
import fs from 'node:fs'; import vm from 'node:vm'; import assert from 'node:assert/strict';
const src = fs.readFileSync(new URL('../public/cloud.js', import.meta.url), 'utf8');
const ctx = {window: {fetch: async () => {}, SDP_CONFIG: {}, __cloudPerson: 'uA'}, navigator: {onLine: true}, location: {href: 'https://x/', origin: 'https://x'}, URL, Headers, localStorage: {getItem: () => null, setItem() {}, removeItem() {}}, document: {addEventListener() {}}, console};
ctx.window.window = ctx.window; vm.createContext(ctx); vm.runInContext(src, ctx);
const C = ctx.window.Cloud; C._test.session({user: {id: 'auth-A'}, access_token: 't'}); C._test.profile({role: 'owner'});
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
// two sign-ins of one person, linked by the server: both write and read the same private rows
C._test.profile({role: 'owner', private_key: 'alan-key'}); ctx.window.__cloudPerson = 'uA';
const linked = J(C.shards({users: DB.users, projects: [], comms: [{id: 'm1', owner: 'uA', source: 'google'}]}));
ok(linked['own:alan-key:comms'] && linked['own:alan-key:comms'].length === 1 && !Object.keys(linked).some(k => k.includes('auth-A')), "linked sign-ins share one private store");
// the watcher's inbox is filed by the app, never merged into DB as a collection
const ib = {users: DB.users, projects: []}; C._test.setPart(ib, 'own:alan-key:inbox', {gmail: [{id: 'x'}]});
ok(!('inbox' in ib) && !Object.keys(ib).some(k => k.startsWith('own:')), "the watcher's inbox is not stored as a collection");
C._test.profile({role: 'owner'}); ctx.window.__cloudPerson = 'uA';
const th = J(C.shards({users: DB.users, projects: [], threads: [{id: 't1', members: ['uA', 'uB'], msgs: [{t: 'hi'}]}, {id: 't2', members: ['uB', 'uC'], msgs: [{t: 'B and C only'}]}]}));
ok(th['thread:t1'] && !th['thread:t2'] && !('threads' in th), "each thread is its own row; a device sends only its person's threads");
const tb = {users: DB.users, projects: []}; C._test.setPart(tb, 'thread:t1', {id: 't1', members: ['uA'], msgs: []}); C._test.setPart(tb, 'thread:t1', {id: 't1', members: ['uA'], msgs: [{t: 'x'}]});
ok(tb.threads.length === 1 && tb.threads[0].msgs.length === 1, 'thread rows join DB.threads by id');
// read markers: each person's own, never in a shared row, and they come back where the app reads them
const ms = J(C.shards({users: DB.users, projects: [{id: 'p1', chat: []}], msgSeen: {uA: {'job:p1': {id: 'c9', n: 9}}, uB: {'dm:t1': {id: 'x', n: 1}}}}));
ok(JSON.stringify(ms.msgSeen) === '{}' && ms['own:auth-A:msgSeen'].uA['job:p1'].n === 9 && !JSON.stringify(ms).includes('dm:t1'), "my read markers go to my own row; another person's are never sent");
const mb = {users: DB.users, projects: []}; C._test.setPart(mb, 'msgSeen', {}); C._test.setPart(mb, 'own:auth-A:msgSeen', {uA: {'job:p1': {id: 'c9', n: 9}}});
ok(mb.msgSeen.uA['job:p1'].id === 'c9', 'and rejoin DB.msgSeen');
// a recorded feedback session is its person's own, like their mail: never a shared row, and back into DB.rpSessions
const fs1 = J(C.shards({users: DB.users, projects: [], rpSessions: [{id: 'R-AAAAA', owner: 'uA', title: 'A session', events: [{k: 'tap'}]}, {id: 'R-BBBBB', owner: 'uB', title: 'B session'}]}));
ok(JSON.stringify(fs1.rpSessions) === '[]' && fs1['own:auth-A:rpSessions'].map(x => x.id).join() === 'R-AAAAA' && !JSON.stringify(fs1).includes('B session'), 'my feedback sessions go to my own row; another person\'s are never sent');
const fb = {users: DB.users, projects: []}; C._test.setPart(fb, 'rpSessions', []); C._test.setPart(fb, 'own:auth-A:rpSessions', fs1['own:auth-A:rpSessions']);
ok(fb.rpSessions.length === 1 && fb.rpSessions[0].events.length === 1, 'and rejoin DB.rpSessions');
console.log('ALL PASS', `(${n} checks)`);
