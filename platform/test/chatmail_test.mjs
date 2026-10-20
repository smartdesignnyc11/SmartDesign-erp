// A guest's email reply filed into the chat it answers by the watcher, with Supabase and Gmail mocked: only from the
// chat's guests, only into chats the mailbox's person is in (by their profile, not by what the page said), only their
// own words, once per mail, and the members are buzzed. node test/chatmail_test.mjs
import assert from 'node:assert/strict';
Object.assign(process.env, {SUPABASE_URL: 'https://db', SUPABASE_SERVICE_ROLE_KEY: 's', VAPID_PRIVATE_KEY: ''});
const {matchReplies, fileChatReplies, stripQuote, bodyText, nyIso} = await import('../netlify/functions/lib/chatmail.mjs');
let n = 0; const ok = (c, m) => { assert.ok(c, m); n++; };
const b64 = s => Buffer.from(s).toString('base64url');
const mail = (id, from, subject, text, o = {}) => ({id, threadId: o.threadId || 'gt-' + id, internalDate: String(Date.parse('2026-10-20T14:05:00Z')), labelIds: o.labels || ['INBOX', 'UNREAD'],
  payload: {headers: [{name: 'From', value: from}, {name: 'Subject', value: subject}, {name: 'Message-ID', value: o.mid || `<${id}@mail>`}],
    mimeType: 'multipart/alternative', parts: [{mimeType: 'text/plain', body: {data: b64(text)}}, {mimeType: 'text/html', body: {data: b64('<p>html</p>')}}]}});
const T1 = {id: 't1', kind: 'direct', title: 'Imogen', members: ['u_alan', 'u_owner'], guests: [{id: 'g1', name: 'Imogen Varga', email: 'Imogen@Example.com'}], mailThread: 'gt-77', msgs: [{id: 'a', text: 'Can you send samples?', fromUid: 'u_alan'}]};
const T2 = {id: 't2', title: 'Pella group', members: ['u_chen', 'u_owner', 'u_alan'], guests: [{id: 'g2', name: 'Ray Pella', email: 'ray@pella.example'}], msgs: []};
const T3 = {id: 't3', members: ['u_alan', 'u_owner'], msgs: []};   // no guests: never touched

// ---- the words
ok(stripQuote('Thursday works.\n\nOn Mon, Oct 19, 2026 at 3:00 PM Maya wrote:\n> Can you\n> come') === 'Thursday works.', 'only the guest\'s own words, not the quoted history');
ok(bodyText(mail('x', 'a', 's', 'plain words')) === 'plain words' && bodyText({payload: {mimeType: 'text/html', body: {data: b64('<p>Hi &amp; bye</p><script>x()</script>')}}}).trim() === 'Hi & bye', 'plain text first; HTML stripped of markup and scripts');
ok(nyIso(Date.parse('2026-10-20T14:05:00Z')) === '2026-10-20T10:05:00', 'the firm\'s clock: New York time');

// ---- what is filed where
const M = [
  mail('m1', 'Imogen Varga <imogen@example.com>', 'Re: Imogen [SD-t1]', 'Thursday works.\n\nOn Mon Maya wrote:\n> old'),
  mail('m2', 'Ray <ray@pella.example>', 'Re: Pella group [SD-t2]', 'Shipping Friday'),
  mail('m3', 'Imogen Varga <imogen@example.com>', 'changed subject', 'By thread id', {threadId: 'gt-77'}),
  mail('m4', 'Stranger <x@evil.example>', 'Re: Imogen [SD-t1]', 'NOT A GUEST'),
  mail('m5', 'Maya <maya@firm.example>', 'Re: Imogen [SD-t1]', 'MY OWN SENT', {labels: ['SENT']}),
  mail('m6', 'Imogen Varga <imogen@example.com>', 'Unrelated', 'NO TOKEN'),
  mail('m7', 'Imogen Varga <imogen@example.com>', 'Re: [SD-t3]', 'NO GUESTS THREAD'),
];
let F = matchReplies([T1, T2, T3], M, 'u_alan');
ok(F.length === 3 && F.map(f => f.line.viaMail).join() === 'm1,m2,m3', 'filed: the token, the Gmail thread; not a stranger, not my own sent mail, not an unrelated mail, not a chat with no guests');
const L = F[0].line;
ok(F[0].thread.id === 't1' && L.by === 'Imogen Varga' && L.fromGuest === 'g1' && L.text === 'Thursday works.' && L.mailId === '<m1@mail>' && L.at === '2026-10-20T10:05:00' && L.t === '10/20, 10:05 AM' && !L.fromUid, 'the line: the guest by name, their words, the mail it came from, New York time, never as a member');
ok(matchReplies([T1, T2], M, 'u_klein').length === 0 && matchReplies([T1, T2], [M[1]], 'u_chen').length === 1, 'only into a chat the mailbox\'s person is a member of');
ok(matchReplies([{...T1, msgs: [{id: 'z', viaMail: 'other', mailId: '<m1@mail>'}]}], [M[0]], 'u_alan').length === 0, 'a mail already filed (from any member\'s mailbox) is not filed again');

// ---- end to end, with the database mocked
const W = {filed: [], pushed: [], claims: []};
globalThis.fetch = async (url, o = {}) => {
  const u = decodeURIComponent(String(url)), J = (x, s = 200) => new Response(JSON.stringify(x), {status: s});
  if (u.includes('/rest/v1/profiles?select=app_user_id')) return J(u.includes('private_key=eq.pk-maya') ? [{app_user_id: 'u_alan'}] : u.includes('id=eq.0f0e0d0c-0000-4000-8000-000000000001') ? [{app_user_id: 'u_chen'}] : []);
  if (u.includes('/rest/v1/profiles?')) return J([{id: 'i1', role: 'pm', app_user_id: 'u_alan', private_key: 'pk-maya'}, {id: 'i2', role: 'owner', app_user_id: 'u_owner', private_key: 'pk-alan'}, {id: 'i3', role: 'owner', app_user_id: 'u_owner', private_key: 'pk-alan'}]);
  if (u.includes('/rest/v1/collections?')) { ok(u.includes('name=like.thread:*') && u.includes('workspace_id=eq.w'), 'reads only this workspace\'s chats'); return J([T1, T2, T3].map(d => ({data: d}))); }
  if (u.endsWith('/rpc/thread_file_mail')) { const b = JSON.parse(o.body); W.filed.push(b); return J(W.filed.length === 2 ? 0 : 5); }
  if (u.endsWith('/rpc/notify_claim')) { W.claims.push(JSON.parse(o.body)); return J(true); }
  if (u.includes('/rest/v1/push_subs')) return J([]);
  throw new Error('unexpected ' + u);
};
const push = async (key, msg) => { W.pushed.push({key, msg}); return 1; };
let R = await fileChatReplies('w', 'pk-maya', M, {push});
ok(W.filed.length === 3 && W.filed.every(f => f.p_member === 'u_alan' && f.p_ws === 'w') && W.filed[0].p_id === 't1', 'each reply goes to the database\'s filing, as the mailbox\'s person');
ok(R.filed === 2, 'one the database had already (another mailbox filed it first) is not counted or announced');
ok(W.pushed.length === 4 && new Set(W.pushed.map(p => p.key)).size === 2 && W.pushed.every(p => p.key !== 'i3'), 'the members are buzzed, once per person (two sign-ins, one key)');
const p1 = W.pushed.find(p => p.msg.tag === 'sdp-msg-dm-t1');
ok(p1 && p1.msg.title === 'Imogen Varga (email)' && p1.msg.body === 'Thursday works.' && p1.msg.url === '/?msg=dm%3At1', 'the buzz: who wrote, their words, opens the chat');
W.filed = []; W.pushed = [];
R = await fileChatReplies('w', 'pk-unlinked', M, {push});
ok(R.filed === 0 && W.filed.length === 0, 'a mailbox whose sign-in is not linked to a person files nothing');
R = await fileChatReplies('w', '0f0e0d0c-0000-4000-8000-000000000001', M, {push});
ok(R.filed === 1 && W.filed[0].p_id === 't2' && W.filed[0].p_member === 'u_chen', 'a person with no private key is found by their id');
W.filed = [];
R = await fileChatReplies('w', 'pk-maya', [M[4]], {push});
ok(R.filed === 0 && W.filed.length === 0, 'a run with only my own sent mail reads nothing');
console.log('ALL PASS', `(${n} checks)`);
