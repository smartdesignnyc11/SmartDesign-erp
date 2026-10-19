// The app's "Keep Watching When It Is Closed": a one-time Google code becomes the long-lived key, sealed, so the
// watcher can read the person's mail, calendar and Drive while nobody has the app open. Also: disconnect, status,
// and a short-lived access token for the person's own browser (so a sync on opening needs no Google window).
import {caller, json, rest} from './lib/auth.mjs';
import {seal, open} from './lib/seal.mjs';
import {exchange, access, revoke, whoami} from './lib/google.mjs';
import {watchOne} from './lib/watch.mjs';
import {pushTo} from './lib/push.mjs';
const READ_ONLY = new Set(['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/calendar.readonly',
  'https://www.googleapis.com/auth/drive.readonly', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']);

export default async (req) => {
  if (req.method !== 'POST') return json(405, {error: 'POST only'});
  const who = await caller(req);
  if (who instanceof Response) return who;
  const {user, profile} = who;
  const key = profile.private_key || user.id;
  let body = {}; try { body = await req.json(); } catch {}
  const mine = async () => (await rest('google_watch?select=*&person_key=eq.' + encodeURIComponent(key)))[0] || null;

  if (body.action === 'disconnect') {
    const row = await mine();
    if (row) { try { await revoke(open(row.sealed)); } catch {} await rest('google_watch?person_key=eq.' + encodeURIComponent(key), {method: 'DELETE'}); }
    return json(200, {connected: false});
  }
  if (body.action === 'status') {
    const row = await mine();
    return json(200, row ? {connected: true, email: row.email, lastRun: row.last_run, lastOk: row.last_ok, lastError: row.last_error} : {connected: false});
  }
  if (body.action === 'token') {
    const row = await mine(); if (!row) return json(404, {error: 'not watching'});
    try { const t = await access(open(row.sealed)); return json(200, {token: t.access_token, expiresIn: t.expires_in}); }
    catch (e) { return json(502, {error: e.message}); }
  }
  if (body.action === 'testpush') {                                  // the confirmation when someone turns notifications on
    const sent = await pushTo(key, {title: 'SmartDesigns Projects', body: 'Notifications reach this device. Mail and meetings that matter will show here while the app is closed.', url: '/'});
    return json(200, {sent});
  }
  if (body.action === 'run') {                                       // the person's own watch, now
    const row = await mine(); if (!row) return json(404, {error: 'not watching'});
    return json(200, await watchOne(row));
  }
  if (!body.code) return json(400, {error: 'code required'});
  let t;
  try { t = await exchange(body.code); } catch (e) { return json(400, {error: e.message}); }
  // The watcher holds reading only. A key that can send, change or delete is refused (and not kept), so the
  // server can never be the way someone sends mail as this person.
  const granted = String(t.scope || '').split(/\s+/).filter(Boolean);
  const broad = granted.filter(sc => /googleapis\.com\/auth\//.test(sc) && !READ_ONLY.has(sc));
  if (broad.length) return json(400, {error: 'Google gave the watcher more than reading (' + broad.map(x => x.split('/').pop()).join(', ') + '). Remove SmartDesigns Projects at myaccount.google.com/permissions, then press Keep Watching again.'});
  if (!t.refresh_token) return json(400, {error: 'Google did not hand over a long-lived key. Remove SmartDesigns Projects at myaccount.google.com/permissions, then press Keep Watching again.'});
  const info = await whoami(t.access_token);
  const old = await mine();
  if (old) { try { await revoke(open(old.sealed)); } catch {} }
  await rest('google_watch', {method: 'POST', headers: {prefer: 'resolution=merge-duplicates,return=minimal'}, body: JSON.stringify({
    person_key: key, workspace_id: profile.workspace_id, app_user_id: body.appUserId || null, email: info.email || body.email || '',
    sealed: seal(t.refresh_token), scopes: t.scope || '', cursors: {}, connected_at: new Date().toISOString(), last_error: ''})});
  return json(200, {connected: true, email: info.email || ''});
};
export const config = {path: '/api/google-connect'};
