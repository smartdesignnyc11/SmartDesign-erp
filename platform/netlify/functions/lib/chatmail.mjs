// Replies from people outside the firm, filed into the chat they answer by the server (2026-10-20), so a guest's
// email reaches the conversation and buzzes its members even when nobody has the app open. The app's msgFileReplies
// does the same when it reads the mail; both mark the line with the mail it came from (viaMail: the Gmail id in that
// mailbox; mailId: the Message-ID header, the same in every mailbox), so a reply is filed once however many members'
// mailboxes it lands in. A mail is filed only into a chat the watched person is a member of, only when it carries the
// chat's [SD-<id>] token or its Gmail thread, and only when it is from one of that chat's guests. Mail is data: its
// text becomes a line and nothing else.
import crypto from 'node:crypto';
import {rest} from './auth.mjs';
import {pushTo} from './push.mjs';
const enc = encodeURIComponent;
const SKIP = ['SENT', 'DRAFT', 'SPAM', 'TRASH'];
const hdr = (m, n) => (((m.payload || {}).headers || []).find(h => (h.name || '').toLowerCase() === n) || {}).value || '';
const addr = s => ((String(s).match(/<([^>]+)>/) || [])[1] || String(s)).trim().toLowerCase();
const clip = (s, n) => { s = String(s || '').replace(/\s+/g, ' ').trim(); return s.length > n ? s.slice(0, n - 1).trimEnd() + '…' : s; };
const first = n => String(n || '').trim().split(/\s+/)[0] || 'Someone';
const b64 = d => { try { return Buffer.from(String(d), 'base64url').toString('utf8'); } catch { return ''; } };
const unhtml = s => String(s).replace(/<(script|style)[\s\S]*?<\/\1>/gi, '').replace(/<br\s*\/?>|<\/p>|<\/div>/gi, '\n').replace(/<[^>]+>/g, '')
  .replace(/&nbsp;/g, ' ').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, '&');

// The plain text of a Gmail message (the first text/plain part, else its HTML stripped, else the snippet).
export function bodyText(m) {
  const walk = p => {
    if (!p) return '';
    if (p.mimeType === 'text/plain' && p.body && p.body.data) return b64(p.body.data);
    for (const q of p.parts || []) { const t = walk(q); if (t) return t; }
    return p.mimeType === 'text/html' && p.body && p.body.data ? unhtml(b64(p.body.data)) : '';
  };
  return walk(m.payload) || m.snippet || '';
}
// Only the guest's own words: the quoted history below them is left out (the app's msgStripQuote).
export function stripQuote(s) {
  const out = [];
  for (const l of String(s || '').replace(/\r/g, '').split('\n')) {
    if (/^\s*>/.test(l) || /^On .+wrote:\s*$/.test(l.trim()) || /^-{2,}\s*Original Message/i.test(l.trim()) || /^From:\s/.test(l.trim())) break;
    out.push(l);
  }
  return out.join('\n').trim();
}
// The firm's clock: New York local time, in the app's shape (YYYY-MM-DDTHH:MM:SS, no zone), and its stamp text.
export function nyIso(ms) {
  const p = Object.fromEntries(new Intl.DateTimeFormat('en-US', {timeZone: 'America/New_York', hourCycle: 'h23', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit'})
    .formatToParts(new Date(ms)).map(x => [x.type, x.value]));
  return `${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}:${p.second}`;
}
const stamp = iso => { const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(iso); if (!m) return iso; const h = +m[4]; return `${+m[2]}/${+m[3]}, ${h % 12 || 12}:${m[5]} ${h >= 12 ? 'PM' : 'AM'}`; };

// Which of these mails answer which of these chats, as the lines to file. Pure, for the tests.
export function matchReplies(threads, mails, me) {
  const mine = (threads || []).filter(t => t && t.id && Array.isArray(t.guests) && t.guests.length && Array.isArray(t.members) && t.members.includes(me));
  const out = [];
  if (!mine.length) return out;
  for (const m of mails || []) {
    if (!m || !m.id || (m.labelIds || []).some(l => SKIP.includes(l))) continue;
    const tok = /\[SD-([A-Za-z0-9_]+)\]/.exec(hdr(m, 'subject'));
    const t = mine.find(x => (tok && tok[1] === x.id) || (m.threadId && x.mailThread && m.threadId === x.mailThread));
    if (!t) continue;
    const from = addr(hdr(m, 'from')), g = t.guests.find(x => x && x.email && String(x.email).trim().toLowerCase() === from);
    if (!g) continue;
    const mailId = hdr(m, 'message-id').trim();
    if ((t.msgs || []).some(x => x && ((x.viaMail && x.viaMail === m.id) || (mailId && x.mailId === mailId)))) continue;
    const ms = +m.internalDate || Date.parse(hdr(m, 'date')) || Date.now(), at = nyIso(ms);
    out.push({thread: t, line: {id: 'ch' + crypto.randomBytes(4).toString('hex'), by: g.name || g.email, fromGuest: g.id || '', text: clip(stripQuote(bodyText(m)), 4000) || '(an email with no text)',
      at, t: stamp(at), files: [], viaMail: m.id, mailId, bySrv: 'mail'}});
  }
  return out;
}

// File the replies found in one watch run of one person's mailbox, and tell the chat's members. Who the mailbox's
// person is in the app comes from their profile (set by the owner), never from what the page said when it connected.
export async function fileChatReplies(ws, personKey, mails, o = {}) {
  const push = o.push || pushTo;
  if (!personKey || !(mails || []).some(m => m && !(m.labelIds || []).some(l => SKIP.includes(l)))) return {filed: 0, pushed: 0};
  // the key is the profile's private key, or its id when it has none (my_private_key)
  let prof = await rest(`profiles?select=app_user_id&workspace_id=eq.${enc(ws)}&private_key=eq.${enc(personKey)}`) || [];
  if (!prof.some(p => p.app_user_id) && /^[0-9a-f-]{36}$/i.test(personKey)) prof = await rest(`profiles?select=app_user_id&workspace_id=eq.${enc(ws)}&id=eq.${enc(personKey)}`) || [];
  const me = (prof.find(p => p.app_user_id) || {}).app_user_id;
  if (!me) return {filed: 0, pushed: 0};
  const rows = await rest(`collections?select=data&workspace_id=eq.${enc(ws)}&name=like.thread:*`) || [];
  const found = matchReplies(rows.map(r => r.data), mails, me);
  let filed = 0, pushed = 0;
  for (const {thread: t, line} of found) {
    const v = await rest('rpc/thread_file_mail', {method: 'POST', body: JSON.stringify({p_ws: ws, p_id: t.id, p_member: me, p_line: line})});
    if (!v) continue;
    filed++;
    if (o.push === false) continue;
    const ids = (t.members || []).filter(x => typeof x === 'string' && /^[A-Za-z0-9_.-]{1,80}$/.test(x)).slice(0, 50);
    if (!ids.length) continue;
    const people = await rest(`profiles?select=id,role,app_user_id,private_key&workspace_id=eq.${enc(ws)}&app_user_id=in.(${ids.map(x => '"' + x + '"').join(',')})`) || [];
    const keys = [...new Set(people.filter(p => p.app_user_id && p.role && p.role !== 'client').map(p => p.private_key || p.id))];
    const msg = {title: (t.members || []).length > 2 || t.kind === 'group' ? `${first(line.by)} in ${clip(t.title || 'your group', 40)}` : clip(line.by, 60) + ' (email)',
      body: clip(line.text, 140), url: '/?msg=' + enc('dm:' + t.id), tag: 'sdp-msg-dm-' + t.id};
    for (const key of keys) {
      const fresh = await rest('rpc/notify_claim', {method: 'POST', body: JSON.stringify({p_key: key, p_thread: 'dm:' + t.id, p_ws: ws})});
      if (!fresh) continue;
      try { pushed += await push(key, msg); } catch (e) { console.warn('chatmail push', e.message); }
    }
  }
  return {filed, pushed};
}
