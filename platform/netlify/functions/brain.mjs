// /api/brain: the owner starts the Brain's run now (it answers in the owner's Changes list a few minutes later).
import {caller, json} from './lib/auth.mjs';
import {brainKey} from './brain-background.mjs';
export default async (req) => {
  if (req.method !== 'POST') return json(405, {error: 'POST only'});
  const who = await caller(req);
  if (who instanceof Response) return who;
  if (who.profile.role !== 'owner') return json(403, {error: 'only the owner runs the Brain'});
  const base = process.env.URL || new URL(req.url).origin;
  const r = await fetch(base + '/.netlify/functions/brain-background', {method: 'POST', headers: {'x-brain-key': brainKey(), 'content-type': 'application/json'}, body: JSON.stringify({ws: who.profile.workspace_id})});
  return json(r.status === 202 || r.ok ? 200 : 502, {started: r.status === 202 || r.ok});
};
export const config = {path: '/api/brain'};
