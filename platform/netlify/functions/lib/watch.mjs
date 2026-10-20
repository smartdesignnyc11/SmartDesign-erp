// One watch run for one person: fresh access from the sealed key, then new mail, calendar changes and Drive
// files into their private inbox row (own:<person>:inbox). The app files the inbox through its own sync code
// when it opens, so routing, proposals and filing are the same as a sync run in the browser.
import {rest} from './auth.mjs';
import {open} from './seal.mjs';
import {access, newMail, calChanges, driveChanges} from './google.mjs';
import {contextFrom, score, message} from './score.mjs';
import {pushTo} from './push.mjs';
import {fileChatReplies} from './chatmail.mjs';

// The firm's vendors, clients and jobs, read once per run of the whole watch (cached per workspace).
const ctxCache = {};
async function firmContext(ws) {
  if (ctxCache[ws]) return ctxCache[ws];
  const rows = await rest(`collections?select=name,data&workspace_id=eq.${encodeURIComponent(ws)}&or=(name.in.(vendors,clients),name.like.project:*)`);
  const cols = {vendors: [], clients: [], projects: []};
  for (const r of rows || []) { if (r.name.startsWith('project:')) cols.projects.push(r.data); else cols[r.name] = r.data; }
  return (ctxCache[ws] = contextFrom(cols));
}

export async function watchOne(row, deadline = Date.now() + 20000, opts = {}) {
  const cur = row.cursors || {}, next = {...cur}, found = {gmail: [], cal: [], drive: []};
  let error = '';
  try {
    const tok = (await access(open(row.sealed))).access_token;
    const started = Math.floor(Date.now() / 1000) - 120;          // a little overlap; the app skips what it holds
    const m = await newMail(tok, cur.gmailAfter, 40, deadline);
    found.gmail = m.messages; if (m.done) next.gmailAfter = started;
    if (Date.now() < deadline) {
      try { const c = await calChanges(tok, cur.calTok); found.cal = c.items; if (c.syncToken) next.calTok = c.syncToken; }
      catch (e) { if (e.gone) next.calTok = ''; else throw e; }
    }
    if (Date.now() < deadline) {
      const at = new Date().toISOString();
      found.drive = await driveChanges(tok, cur.driveAt); next.driveAt = at;
    }
  } catch (e) { error = String(e.message || e).slice(0, 300); }
  const items = Object.fromEntries(Object.entries(found).filter(([, v]) => v.length));
  if (Object.keys(items).length) await rest('rpc/watch_put_inbox', {method: 'POST', body: JSON.stringify({p_ws: row.workspace_id, p_key: row.person_key, p_items: items})});
  // A guest's email reply to a chat this person is in goes into that chat now, not when someone next opens the app.
  let chat = {filed: 0};
  if (found.gmail.length) {
    try { chat = await fileChatReplies(row.workspace_id, row.person_key, found.gmail, {push: opts.push}); }
    catch (e) { console.error('chatmail', e.message); }
  }
  let pushed = 0;
  if (!error && (found.gmail.length || found.cal.length) && opts.push !== false) {
    try { pushed = await pushTo(row.person_key, message(score(found, await firmContext(row.workspace_id), String(row.email || '').toLowerCase()))); }
    catch (e) { console.error('push', e.message); }
  }
  const now = new Date().toISOString();
  await rest('google_watch?person_key=eq.' + encodeURIComponent(row.person_key), {method: 'PATCH', headers: {prefer: 'return=minimal'},
    body: JSON.stringify({cursors: next, last_run: now, last_error: error, ...(error ? {} : {last_ok: now})})});
  return {mail: found.gmail.length, chat: chat.filed, events: found.cal.length, files: found.drive.length, pushed, error};
}
