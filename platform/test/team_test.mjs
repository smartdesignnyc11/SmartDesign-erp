// The owner's invitation from the team's own workspace (/api/team, TASKS_PLAN §2 Phase 1 item 1), with Supabase mocked:
// a new address is invited into the owner's current workspace; someone already signed in to another of the owner's
// workspaces (the demo) is brought in and keeps the demo in his list; another firm's address is refused; nobody but
// the owner invites. Nothing is sent: the Supabase invite endpoint is a mock. Run: node test/team_test.mjs
import assert from 'node:assert/strict';
process.env.SUPABASE_URL = 'https://db.example'; process.env.SUPABASE_SERVICE_ROLE_KEY = 'svc';
const tok = sub => 'h.' + Buffer.from(JSON.stringify({sub, session_id: 's-' + sub})).toString('base64url') + '.sig';
const db = {
  profiles: {
    alan: {id: 'alan', role: 'owner', workspace_id: 'sd-team', workspaces: ['smartdesign'], email: 'alan@example.com'},
    chen: {id: 'chen', role: 'coord', workspace_id: 'smartdesign', workspaces: [], email: 'coord@example.com'},
    far: {id: 'far', role: 'pm', workspace_id: 'otherfirm', workspaces: [], email: 'far@example.com'},
    bea: {id: 'bea', role: 'billing', workspace_id: 'sd-team', workspaces: [], email: 'bea@example.com'},
  },
  invited: [], patches: [],
};
globalThis.fetch = async (url, opts = {}) => {
  const u = new URL(url), body = opts.body ? JSON.parse(opts.body) : null;
  const res = (s, o) => new Response(JSON.stringify(o), {status: s});
  if (u.pathname === '/auth/v1/user') { const sub = JSON.parse(Buffer.from(opts.headers.authorization.split('.')[1], 'base64url')).sub; return res(200, {id: sub}); }
  if (u.pathname === '/auth/v1/invite') { const id = 'new-' + db.invited.length; db.invited.push(body.email); db.profiles[id] = {id, role: 'none', workspace_id: 'smartdesign', workspaces: [], email: body.email}; return res(200, {id}); }
  if (u.pathname === '/rest/v1/rpc/session_alive_for') return res(200, true);
  if (u.pathname === '/rest/v1/profiles') {
    const q = u.searchParams, [k, v] = q.get('id') ? ['id', q.get('id')] : ['email', q.get('email')], val = v.replace(/^eq\./, '');
    if ((opts.method || 'GET') === 'PATCH') { const p = Object.values(db.profiles).find(x => x[k] === val); Object.assign(p, body); db.patches.push([val, body]); return new Response(null, {status: 204}); }
    return res(200, Object.values(db.profiles).filter(x => x[k] === val).map(x => ({...x})));
  }
  return res(404, {error: 'unmocked ' + u.pathname});
};
const {default: team} = await import('../netlify/functions/team.mjs');
const call = async (who, b) => { const r = await team(new Request('https://x/api/team', {method: 'POST', headers: {authorization: 'Bearer ' + tok(who)}, body: JSON.stringify(b)})); return [r.status, await r.json()]; };
let n = 0; const ok = (c, msg) => { assert.ok(c, msg); n++; };

let [s, j] = await call('alan', {action: 'invite', email: 'new.admin@example.com', role: 'billing', appUserId: 'u_x1', name: 'New Admin'});
ok(s === 200 && j.invited && db.invited.includes('new.admin@example.com'), 'a new address is invited (the mock stands in for Supabase\'s email)');
const nw = Object.values(db.profiles).find(p => p.email === 'new.admin@example.com');
ok(nw.workspace_id === 'sd-team' && nw.role === 'billing' && nw.app_user_id === 'u_x1' && nw.name === 'New Admin', `into the owner's team workspace, with the role and the person in the app: ${JSON.stringify(nw)}`);
[s, j] = await call('alan', {action: 'invite', email: 'coord@example.com', role: 'coord', appUserId: 'u_c'});
ok(s === 200 && !j.invited && j.moved, `the coordinator, already in the demo, is brought in without a second email: ${JSON.stringify(j)}`);
ok(db.profiles.chen.workspace_id === 'sd-team' && db.profiles.chen.workspaces.join() === 'smartdesign', `and keeps the demo in his list: ${JSON.stringify(db.profiles.chen)}`);
ok(db.invited.length === 1, 'no email went to someone who already had an account');
[s, j] = await call('alan', {action: 'invite', email: 'far@example.com', role: 'pm'});
ok(s === 409 && db.profiles.far.workspace_id === 'otherfirm', 'an address in another firm is refused and untouched');
[s, j] = await call('alan', {action: 'invite', email: 'x@example.com', role: 'owner'});
ok(s === 400, 'nobody is invited as a second owner');
[s, j] = await call('bea', {action: 'invite', email: 'y@example.com', role: 'crew'});
ok(s === 403 && !db.invited.includes('y@example.com'), 'only the owner invites');
console.log(`team_test: ALL PASS (${n} checks)`);
