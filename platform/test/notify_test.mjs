// Message notifications (/api/notify, lib/notify.mjs) with Supabase and the push service mocked: the server reads the
// conversation itself, refuses non-members and anyone but the sender, pushes a direct or group line to the other
// members and a job line to the people @mentioned who may read it, never the sender, once per conversation per person
// per 2 minutes. Run: node test/notify_test.mjs
import assert from 'node:assert/strict';
Object.assign(process.env, {SUPABASE_URL: 'https://db', SUPABASE_SERVICE_ROLE_KEY: 's'});
const {notifyMessage} = await import('../netlify/functions/lib/notify.mjs');
const handler = (await import('../netlify/functions/notify.mjs')).default;
let n = 0; const ok = (c, m) => { assert.ok(c, m); n++; };
const P = {
  u_owner: {id: 'a-owner', role: 'owner', app_user_id: 'u_owner', private_key: 'pk-alan'},
  u_alan: {id: 'a-pm', role: 'pm', app_user_id: 'u_alan', private_key: null},
  u_chen: {id: 'a-chen', role: 'coord', app_user_id: 'u_chen', private_key: null},
  u_angel: {id: 'a-angel', role: 'foreman', app_user_id: 'u_angel', private_key: null},
  u_alberto: {id: 'a-alberto', role: 'crew', app_user_id: 'u_alberto', private_key: null},
};
const rows = {
  'thread:t1': {id: 't1', kind: 'direct', members: ['u_chen', 'u_angel'], msgs: [{id: 'm1', by: 'Chen Biron', fromUid: 'u_chen', text: 'The vanity ships Friday'}]},
  'thread:g1': {id: 'g1', kind: 'group', title: 'Site Leads', members: ['u_alan', 'u_chen', 'u_angel'], msgs: [{id: 'g-1', by: 'Alan', fromUid: 'u_alan', text: 'Walk at 10', voice: null}, {id: 'g-2', by: 'Angel', fromUid: 'u_angel', text: '', voice: {id: 'vn1', dur: 7}}]},
  'project:p121': {id: 'p121', project: {name: '121 State Street'}, team: ['u_angel'], chat: [
    {id: 'c1', by: 'Alan', fromUid: 'u_alan', text: '@Angel @Alberto @Chen panel cover off by 10', mentions: ['u_angel', 'u_alberto', 'u_chen', 'u_alan']},
    {id: 'c2', by: 'Alan', fromUid: 'u_alan', text: 'Here is the bill @Angel @Chen', mentions: ['u_angel', 'u_chen'], cards: [{kind: 'invoice', id: 'inv1'}]},
    {id: 'c3', by: 'Alan', fromUid: 'u_alan', text: 'no one named'}]},
};
const W = {claims: new Map(), pushed: [], queries: []};
let clock = 0;   // minutes, for the 2-minute rule
globalThis.fetch = async (url, o = {}) => {
  const u = decodeURIComponent(String(url)), J = (x, s = 200) => new Response(JSON.stringify(x), {status: s});
  if (u === 'https://db/auth/v1/user') return (o.headers.authorization || '').endsWith('tok-chen') ? J({id: 'a-chen'}) : (o.headers.authorization || '').endsWith('tok-none') ? J({id: 'a-none'}) : J({}, 401);
  if (u.endsWith('/rpc/session_alive_for')) return J(true);
  if (u.includes('/rest/v1/profiles?select=id,role,workspace_id')) return J(u.includes('a-none') ? [{id: 'a-none', role: 'none', workspace_id: 'smartdesign'}] : [Object.assign({workspace_id: 'smartdesign', name: 'Chen Biron'}, P.u_chen)]);
  if (u.includes('/rest/v1/collections?')) { W.queries.push(u); const name = /name=eq\.([^&]+)/.exec(u)[1]; return J(rows[name] && u.includes('workspace_id=eq.smartdesign') ? [{data: rows[name]}] : []); }
  if (u.includes('/rest/v1/profiles?select=id,role,app_user_id,private_key')) { const ids = /in\.\(([^)]*)\)/.exec(u)[1].split(',').map(x => x.replace(/"/g, '')); return J(Object.values(P).filter(p => ids.includes(p.app_user_id))); }
  if (u.endsWith('/rpc/notify_claim')) { const b = JSON.parse(o.body), k = b.p_key + '|' + b.p_thread, at = W.claims.get(k); if (at !== undefined && clock - at < 2) return J(false); W.claims.set(k, clock); return J(true); }
  throw new Error('unexpected ' + u);
};
const push = async (key, msg) => { W.pushed.push([key, msg]); return 1; };
const as = (who, body) => notifyMessage(Object.assign({workspace_id: 'smartdesign'}, P[who]), body, {push, wait: 5});
const sentTo = () => W.pushed.map(x => x[0]).sort();

// a direct message: the other member, never the sender
let r = await as('u_chen', {threadKey: 'dm:t1', msgId: 'm1'});
ok(r.status === 200 && r.body.sent === 1 && sentTo().join() === 'a-angel', `a direct message goes to the other member only: ${JSON.stringify(r.body)} ${sentTo()}`);
const m = W.pushed[0][1];
ok(m.title === 'Chen Biron' && m.body === 'The vanity ships Friday' && m.url === '/?msg=dm%3At1' && m.tag === 'sdp-msg-dm-t1', `it names the sender and the line, and opens the thread: ${JSON.stringify(m)}`);
ok(W.queries.every(q => q.includes('workspace_id=eq.smartdesign')), "it reads the caller's own workspace only");
// the 2-minute rule: a second line inside 2 minutes is quiet; after 2 minutes it buzzes again
W.pushed = [];
r = await as('u_chen', {threadKey: 'dm:t1', msgId: 'm1'});
ok(r.status === 200 && r.body.sent === 0 && r.body.quiet === 1 && !W.pushed.length, `a burst inside 2 minutes is one notification: ${JSON.stringify(r.body)}`);
clock = 3; r = await as('u_chen', {threadKey: 'dm:t1', msgId: 'm1'});
ok(r.body.sent === 1, 'after 2 minutes the next line notifies again');
// the checks: a member, the sender, a message that exists
W.pushed = [];
r = await as('u_alberto', {threadKey: 'dm:t1', msgId: 'm1'});
ok(r.status === 404 && !W.pushed.length, `someone not in the thread cannot use it (and learns nothing about it): ${r.status}`);
r = await as('u_angel', {threadKey: 'dm:t1', msgId: 'm1'});
ok(r.status === 403 && !W.pushed.length, `a member who did not write the line cannot announce it: ${r.status}`);
r = await as('u_chen', {threadKey: 'dm:t1', msgId: 'nope'});
ok(r.status === 404, `a message that does not exist: ${r.status}`);
r = await as('u_chen', {threadKey: 'thread:t1; drop table', msgId: 'm1'});
ok(r.status === 400, `a malformed conversation key is refused: ${r.status}`);
r = await notifyMessage({workspace_id: 'smartdesign', role: 'coord', id: 'x', app_user_id: null}, {threadKey: 'dm:t1', msgId: 'm1'}, {push});
ok(r.status === 403, 'a sign-in not linked to a person in the app is refused');
// a group: every other member; a voice note says so; the title names the group
W.pushed = []; clock = 10;
r = await as('u_angel', {threadKey: 'dm:g1', msgId: 'g-2'});
ok(sentTo().join() === 'a-chen,a-pm', `a group line goes to every other member: ${sentTo()}`);
ok(W.pushed[0][1].title === 'Angel in Site Leads' && W.pushed[0][1].body === 'Voice note', `a group's title and a voice note: ${JSON.stringify(W.pushed[0][1])}`);
// a job thread: only the people mentioned who may read it; the field only on its own job; never the sender
W.pushed = []; clock = 20;
r = await as('u_alan', {threadKey: 'job:p121', msgId: 'c1'});
ok(sentTo().join() === 'a-angel,a-chen', `a job line goes to the mentioned people who read the job (Angel on its crew, Chen in the office), not Alberto (not on it), not the sender: ${sentTo()}`);
ok(W.pushed[0][1].title === 'Alan mentioned you on 121 State Street' && W.pushed[0][1].url === '/?msg=job%3Ap121', `it says who mentioned them, where: ${JSON.stringify(W.pushed[0][1])}`);
W.pushed = []; clock = 30;
r = await as('u_alan', {threadKey: 'job:p121', msgId: 'c2'});
ok(sentTo().join() === 'a-chen', `a line with a money card never reaches the field, not even its words: ${sentTo()}`);
W.pushed = []; clock = 40;
r = await as('u_alan', {threadKey: 'job:p121', msgId: 'c3'});
ok(r.status === 200 && !W.pushed.length, 'a job line naming nobody notifies nobody');
r = await as('u_alberto', {threadKey: 'job:p121', msgId: 'c1'});
ok(r.status === 404, 'a field person not on the job cannot use it');
r = await as('u_owner', {threadKey: 'job:p999', msgId: 'c1'});
ok(r.status === 404, 'a job that is not there');
// the linked private key is the one pushed to (Alan's two sign-ins share one)
W.pushed = []; clock = 50; rows['thread:t2'] = {id: 't2', members: ['u_owner', 'u_chen'], msgs: [{id: 'x1', by: 'Chen Biron', fromUid: 'u_chen', text: 'Sign the CO'}]};
await as('u_chen', {threadKey: 'dm:t2', msgId: 'x1'});
ok(sentTo().join() === 'pk-alan', `the push goes to the person's private key: ${sentTo()}`);
// the door: signed in, a member role, POST
const jwt = who => 'h.' + Buffer.from(JSON.stringify({session_id: 's-' + who})).toString('base64url') + '.tok-' + who;
const req = (tok, body, method = 'POST') => new Request('https://x/api/notify', {method, headers: Object.assign({'content-type': 'application/json'}, tok ? {authorization: 'Bearer ' + tok} : {}), body: method === 'POST' ? JSON.stringify(body) : undefined});
ok((await handler(req(null, {threadKey: 'dm:t1', msgId: 'm1'}))).status === 401, 'the door: no session refused');
ok((await handler(req(jwt('none'), {threadKey: 'dm:t1', msgId: 'm1'}))).status === 403, 'the door: an account with no role refused');
ok((await handler(req(jwt('chen'), {}, 'GET'))).status === 405, 'the door: POST only');
clock = 60; const res = await handler(req(jwt('chen'), {threadKey: 'dm:t1', msgId: 'm1'}));
ok(res.status === 200 && (await res.json()).people === 1, 'the door: the signed-in sender gets an answer');
console.log('ALL PASS', `(${n} checks)`);
