// Google for the server: trade a one-time code for the long-lived key, mint short-lived access, and read what is new.
// The watcher only reads. Nothing here can send mail or change a calendar.
export const SCOPES_NEEDED = ['gmail', 'calendar', 'drive'];
const form = o => new URLSearchParams(o).toString();
async function tokenCall(body) {
  const r = await fetch('https://oauth2.googleapis.com/token', {method: 'POST', headers: {'content-type': 'application/x-www-form-urlencoded'},
    body: form({client_id: process.env.GOOGLE_CLIENT_ID, client_secret: process.env.GOOGLE_CLIENT_SECRET, ...body})});
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error('Google: ' + (j.error_description || j.error || r.status));
  return j;
}
export const exchange = code => tokenCall({code, grant_type: 'authorization_code', redirect_uri: 'postmessage'});
export const access = refresh => tokenCall({refresh_token: refresh, grant_type: 'refresh_token'});
export async function revoke(token) { try { await fetch('https://oauth2.googleapis.com/revoke?token=' + encodeURIComponent(token), {method: 'POST'}); } catch {} }
export async function whoami(accessToken) {
  const r = await fetch('https://openidconnect.googleapis.com/v1/userinfo', {headers: {authorization: 'Bearer ' + accessToken}});
  return r.ok ? r.json() : {};
}
async function get(tok, url) {
  const r = await fetch(url.startsWith('http') ? url : 'https://www.googleapis.com' + url, {headers: {authorization: 'Bearer ' + tok}});
  if (r.status === 410) { const e = new Error('gone'); e.gone = true; throw e; }
  if (!r.ok) throw new Error(`Google ${r.status}: ${(await r.text()).slice(0, 120)}`);
  return r.json();
}
// New mail since the cursor (seconds), full messages, at most `cap` a run; the cursor moves only when the window is read.
export async function newMail(tok, cursor, cap = 40, deadline = Infinity) {
  const q = encodeURIComponent(cursor ? `after:${cursor} -in:chats` : 'newer_than:2d -in:chats');
  const ids = []; let page = '', pages = 0, exhausted = false;
  do {
    const j = await get(tok, `/gmail/v1/users/me/messages?maxResults=50&q=${q}${page ? '&pageToken=' + encodeURIComponent(page) : ''}`);
    (j.messages || []).forEach(m => ids.includes(m.id) || ids.push(m.id));
    page = j.nextPageToken || ''; pages++; if (!page) exhausted = true;
  } while (page && ids.length < cap && pages < 10);
  const out = [];
  for (const id of ids.slice(0, cap)) {
    if (Date.now() > deadline) { exhausted = false; break; }
    try { out.push(await get(tok, `/gmail/v1/users/me/messages/${id}?format=full`)); } catch {}
  }
  return {messages: out, done: exhausted && ids.length <= cap};
}
export async function calChanges(tok, syncToken) {
  const url = syncToken ? `/calendar/v3/calendars/primary/events?singleEvents=true&syncToken=${encodeURIComponent(syncToken)}`
    : `/calendar/v3/calendars/primary/events?singleEvents=true&maxResults=250&timeMin=${encodeURIComponent(new Date(Date.now() - 7 * 864e5).toISOString())}&timeMax=${encodeURIComponent(new Date(Date.now() + 60 * 864e5).toISOString())}`;
  const items = []; let page = '', next = '', pages = 0;
  do {
    const j = await get(tok, url + (page ? '&pageToken=' + encodeURIComponent(page) : ''));
    items.push(...(j.items || [])); page = j.nextPageToken || ''; next = j.nextSyncToken || next; pages++;
  } while (page && pages < 5);
  return {items, syncToken: next};
}
export async function driveChanges(tok, since) {
  const q = encodeURIComponent('trashed = false' + (since ? ` and modifiedTime > '${since}'` : ''));
  const j = await get(tok, `/drive/v3/files?q=${q}&orderBy=modifiedTime desc&pageSize=50&fields=files(id,name,mimeType,modifiedTime,webViewLink,iconLink,size,owners(displayName,emailAddress),parents)`);
  return j.files || [];
}
