// The Google watcher's server half with Supabase and Google mocked: who may connect, the key sealed at rest,
// a run filing new mail, events and files into the person's own inbox, cursors, disconnect. node test/watch_test.mjs
import assert from 'node:assert/strict';
const GOOD = 'h.' + Buffer.from(JSON.stringify({session_id: 's1'})).toString('base64url') + '.sig'; import crypto from 'node:crypto';
Object.assign(process.env, {SUPABASE_URL: 'https://db', SUPABASE_SERVICE_ROLE_KEY: 's', GOOGLE_CLIENT_ID: 'cid', GOOGLE_CLIENT_SECRET: 'csec', WATCH_KEY: crypto.randomBytes(32).toString('base64')});
const {seal, open} = await import('../netlify/functions/lib/seal.mjs');
const connect = (await import('../netlify/functions/google-connect.mjs')).default;
const watchAll = (await import('../netlify/functions/assistant-watch.mjs')).default;
let n = 0; const ok = (c, m) => { assert.ok(c, m); n++; };
const W = {rows: {}, inbox: {}, profile: {id: 'u1', role: 'owner', workspace_id: 'w', private_key: 'pk1'}, refresh: 'RT-SECRET', revoked: [], gmailCalls: 0};
globalThis.fetch = async (url, o = {}) => {
  const u = String(url), body = o.body ? (typeof o.body === 'string' ? o.body : String(o.body)) : '';
  const J = (x, s = 200) => new Response(JSON.stringify(x), {status: s});
  if (u.endsWith('/auth/v1/user')) return o.headers.authorization === 'Bearer ' + GOOD ? J({id: 'u1'}) : J({}, 401);
  if (u.endsWith('/rest/v1/rpc/session_alive_for')) return new Response(JSON.stringify(!globalThis.SESSION_DEAD));
  if (u.includes('/rest/v1/profiles')) return J([W.profile]);
  if (u.includes('/rest/v1/google_watch')) {
    if ((o.method || 'GET') === 'GET') { const k = decodeURIComponent(u.split('person_key=eq.')[1] || ''); return J(k ? (W.rows[k] ? [W.rows[k]] : []) : Object.values(W.rows)); }
    if (o.method === 'POST') { const r = JSON.parse(body); W.rows[r.person_key] = r; return new Response(null, {status: 201}); }
    if (o.method === 'PATCH') { const k = decodeURIComponent(u.split('person_key=eq.')[1]); Object.assign(W.rows[k], JSON.parse(body)); return new Response(null, {status: 204}); }
    if (o.method === 'DELETE') { const k = decodeURIComponent(u.split('person_key=eq.')[1]); delete W.rows[k]; return new Response(null, {status: 204}); }
  }
  if (u.includes('/rest/v1/collections?')) return J([{name: 'vendors', data: [{email: 'ray@pella.example'}]}]);
  if (u.includes('/rest/v1/push_subs')) { W.pushLookups = (W.pushLookups || 0) + 1; return J([]); }
  if (u.endsWith('/rest/v1/rpc/watch_put_inbox')) { const b = JSON.parse(body); const box = W.inbox[b.p_key] ||= {}; for (const [k, v] of Object.entries(b.p_items)) box[k] = (box[k] || []).concat(v); return J(1); }
  if (u === 'https://oauth2.googleapis.com/token') {
    const p = new URLSearchParams(body);
    ok(p.get('client_secret') === 'csec', 'the client secret is sent only to Google');
    if (p.get('grant_type') === 'authorization_code') return p.get('code') === 'nolong' ? J({access_token: 'AT', scope: 's'}) : J({access_token: 'AT', refresh_token: W.refresh, expires_in: 3599, scope: p.get('code') === 'broad'
      ? 'openid https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.readonly'
      : 'openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/calendar.readonly https://www.googleapis.com/auth/drive.readonly'});
    return p.get('refresh_token') === W.refresh ? J({access_token: 'AT2', expires_in: 3599}) : J({error: 'invalid_grant'}, 400);
  }
  if (u.startsWith('https://oauth2.googleapis.com/revoke')) { W.revoked.push(u); return J({}); }
  if (u.startsWith('https://openidconnect.googleapis.com')) return J({email: 'alan@example.com'});
  if (u.includes('/gmail/v1/users/me/messages?')) { W.gmailCalls++; return J({messages: [{id: 'g1'}, {id: 'g2'}]}); }
  if (u.includes('/gmail/v1/users/me/messages/')) { const id = u.split('/messages/')[1].split('?')[0]; return J({id, threadId: 't' + id, payload: {headers: [{name: 'Subject', value: 'Hello ' + id}]}}); }
  if (u.includes('/calendar/v3/')) return J({items: [{id: 'e1', summary: 'Site walk'}], nextSyncToken: 'CAL1'});
  if (u.includes('/drive/v3/files')) return J({files: [{id: 'f1', name: 'Plans.pdf'}]});
  throw new Error('unexpected ' + u);
};
const req = (b, tok = GOOD) => new Request('https://x/api/google-connect', {method: 'POST', headers: tok ? {authorization: 'Bearer ' + tok} : {}, body: JSON.stringify(b)});

ok(open(seal('hello')) === 'hello' && seal('hello') !== seal('hello'), 'seal round-trips, and never the same twice');
let r = await connect(req({code: 'c'}, null)); ok(r.status === 401, 'connect needs a signed-in person');
W.profile.role = 'none'; r = await connect(req({code: 'c'})); ok(r.status === 403, 'an account with no role cannot connect'); W.profile.role = 'owner';
r = await connect(req({code: 'nolong'})); ok(r.status === 400 && /long-lived/.test((await r.json()).error), 'no long-lived key: says what to do');
r = await connect(req({code: 'broad'})); ok(r.status === 400 && /more than reading/.test((await r.json()).error) && !W.rows.pk1, 'a key that can send mail is refused and not kept');
r = await connect(req({code: 'c', appUserId: 'uminbq', email: 'x'})); const j = await r.json();
ok(r.status === 200 && j.connected && j.email === 'alan@example.com', 'connected, with the Google address');
ok(W.rows.pk1 && !JSON.stringify(W.rows).includes('RT-SECRET') && open(W.rows.pk1.sealed) === 'RT-SECRET', 'the key is stored sealed, under the private key, never in plain');
r = await connect(req({action: 'token'})); ok((await r.json()).token === 'AT2', "the person's browser gets a short-lived key");
r = await connect(req({action: 'status'})); const st = await r.json(); ok(st.connected && !('sealed' in st), 'status never returns the key');
await watchAll();
const box = W.inbox.pk1 || {};
ok(box.gmail && box.gmail.length === 2 && box.gmail[0].payload, 'the watch filed new mail into the private inbox');
ok(box.cal && box.cal[0].summary === 'Site walk' && box.drive && box.drive[0].name === 'Plans.pdf', 'and calendar changes and Drive files');
ok(W.rows.pk1.cursors.gmailAfter > 0 && W.rows.pk1.cursors.calTok === 'CAL1' && W.rows.pk1.cursors.driveAt, 'cursors move so the next run reads only what is new');
ok(W.rows.pk1.last_ok && W.rows.pk1.last_error === '', 'the run is recorded');
W.refresh = 'rotated'; await watchAll();
ok(/invalid_grant/.test(W.rows.pk1.last_error), 'a key Google no longer accepts is recorded as the error, not thrown');
r = await connect(req({action: 'disconnect'})); ok((await r.json()).connected === false && !W.rows.pk1 && W.revoked.length >= 1, 'disconnect revokes at Google and deletes the key');
ok(!process.env.VAPID_PRIVATE_KEY && !W.pushLookups, 'with no push key the watcher sends nothing and does not look');
console.log('ALL PASS', `(${n} checks)`);
