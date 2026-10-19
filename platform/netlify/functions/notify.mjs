// /api/notify {threadKey, msgId}: the app asks, right after a new message saved, that the people it is for be told on
// their phones. lib/notify.mjs checks everything against the database (membership, sender, who may read the line).
import {caller, json} from './lib/auth.mjs';
import {notifyMessage} from './lib/notify.mjs';
export default async (req) => {
  if (req.method !== 'POST') return json(405, {error: 'POST only'});
  const who = await caller(req);
  if (who instanceof Response) return who;
  let body = {};
  try { body = await req.json(); } catch (e) { return json(400, {error: 'send JSON'}); }
  try { const r = await notifyMessage(who.profile, body); return json(r.status, r.body); }
  catch (e) { console.warn('notify', e.message); return json(502, {error: 'could not notify'}); }
};
export const config = {path: '/api/notify'};
