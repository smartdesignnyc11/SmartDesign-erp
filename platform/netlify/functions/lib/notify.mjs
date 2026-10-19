// A new message, pushed to the people it is for (BACKLOG §1.21 phase 2: "as fast as WhatsApp, or people won't switch").
// The app calls /api/notify {threadKey, msgId} after the line has saved. The server reads the conversation itself
// (never trusts the page): the caller must be able to read it and must be the line's sender. A direct or group thread
// notifies its other members; a job's thread notifies only the people @mentioned in the line who may read it (the
// field only on its own jobs, never a client-thread line or a money card). Never the sender. At most one notification
// per conversation per person every 2 minutes (notify_claim), so a burst of lines is one buzz.
import {rest} from './auth.mjs';
import {pushTo} from './push.mjs';
const FIELD = ['foreman', 'crew', 'driver'];
const OFFICE = ['owner', 'pm', 'coord', 'designer', 'design_mgr', 'billing', 'controller'];
const MONEY_CARDS = ['invoice', 'co', 'estimate', 'payment'];
const KEY = /^(dm|job|client):([A-Za-z0-9_.-]{1,80})$/;
const enc = encodeURIComponent;
const clip = (s, n) => { s = String(s || '').replace(/\s+/g, ' ').trim(); return s.length > n ? s.slice(0, n - 1).trimEnd() + '…' : s; };
const first = n => String(n || '').trim().split(/\s+/)[0] || 'Someone';
const sleep = ms => new Promise(r => setTimeout(r, ms));
const out = (status, body) => ({status, body});

// May this person (role, app user id) read this conversation's row?
function reads(kind, data, role, app) {
  if (!app) return false;
  if (kind === 'dm') return Array.isArray(data.members) && data.members.includes(app);
  if (OFFICE.includes(role)) return true;
  return kind === 'job' && FIELD.includes(role) && Array.isArray(data.team) && data.team.includes(app);
}
// May they read this line of a job's thread? (the app's msgVisible, on the server's copy)
function readsLine(kind, line, role) {
  if (OFFICE.includes(role)) return true;
  if (kind === 'client' || line.aud === 'client' || (line.dm && line.to)) return false;
  return !(line.cards || []).some(c => c && MONEY_CARDS.includes(c.kind));
}

export async function notifyMessage(profile, body, o = {}) {
  const push = o.push || pushTo, wait = o.wait ?? 1000;
  const ws = profile.workspace_id, me = profile.app_user_id || '';
  if (!me) return out(403, {error: 'this sign-in is not linked to a person in the app yet: ask the owner'});
  const m = KEY.exec(String((body || {}).threadKey || '')), msgId = String((body || {}).msgId || '');
  if (!m || !msgId || msgId.length > 80) return out(400, {error: 'threadKey (dm:<id>, job:<id> or client:<id>) and msgId are needed'});
  const kind = m[1], id = m[2], name = (kind === 'dm' ? 'thread:' : 'project:') + id;
  // The line may still be on its way up (the page asks right after its save): look again, briefly.
  let data = null, line = null;
  for (let i = 0; i < 3 && !line; i++) {
    if (i) await sleep(wait);
    const rows = await rest(`collections?select=data&workspace_id=eq.${enc(ws)}&name=eq.${enc(name)}`);
    data = rows && rows[0] && rows[0].data;
    if (!data || !reads(kind, data, profile.role, me)) return out(404, {error: 'no such conversation'});
    line = ((kind === 'dm' ? data.msgs : data.chat) || []).find(x => x && x.id === msgId) || null;
  }
  if (!line) return out(404, {error: 'no such message'});
  if (line.fromUid !== me) return out(403, {error: 'only the sender asks for a message to be announced'});
  // who it is for
  let ids = kind === 'dm' ? (data.members || []) : (line.mentions || []);
  ids = [...new Set(ids.filter(x => typeof x === 'string' && /^[A-Za-z0-9_.-]{1,80}$/.test(x) && x !== me))].slice(0, 50);
  if (!ids.length) return out(200, {sent: 0, people: 0});
  const people = await rest(`profiles?select=id,role,app_user_id,private_key&workspace_id=eq.${enc(ws)}&app_user_id=in.(${ids.map(x => '"' + x + '"').join(',')})`) || [];
  const keys = new Map();
  for (const p of people) {
    if (!p.app_user_id || p.app_user_id === me || ![...OFFICE, ...FIELD].includes(p.role)) continue;
    if (!reads(kind, data, p.role, p.app_user_id) || (kind !== 'dm' && !readsLine(kind, line, p.role))) continue;
    keys.set(p.private_key || p.id, p.app_user_id);
  }
  // what it says: who, where, the line itself (a voice note or a photo says so)
  const who = first(line.by), job = clip(((data.project || {}).name) || 'the job', 40);
  const title = kind === 'dm'
    ? ((data.kind === 'group' || (data.members || []).length > 2) ? `${who} in ${clip(data.title || 'your group', 40)}` : clip(line.by || 'New message', 60))
    : `${who} mentioned you on ${job}`;
  const text = line.voice ? 'Voice note' + (line.text ? ': ' + line.text : '') : (line.text || ((line.cards || []).length ? 'Shared a record' : (line.files || []).length ? 'Sent a photo' : ''));
  const msg = {title, body: clip(text, 140), url: '/?msg=' + enc(`${kind}:${id}`), tag: `sdp-msg-${kind}-${id}`};
  let sent = 0, quiet = 0;
  for (const key of keys.keys()) {
    const fresh = await rest('rpc/notify_claim', {method: 'POST', body: JSON.stringify({p_key: key, p_thread: `${kind}:${id}`, p_ws: ws})});
    if (!fresh) { quiet++; continue; }
    try { sent += await push(key, msg); } catch (e) { console.warn('notify push', e.message); }
  }
  return out(200, {sent, people: keys.size, quiet});
}
