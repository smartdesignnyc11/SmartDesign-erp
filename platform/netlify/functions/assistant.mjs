// /api/assistant: a person asks their own assistant to read their day now (the briefing lands in a minute or two).
// Only their own run, charged to them within their cap.
import {caller, json} from './lib/auth.mjs';
import {assistantKey} from './assistant-background.mjs';
const OFFICE = ['owner', 'pm', 'coord', 'designer', 'design_mgr', 'billing', 'controller'];
export default async (req) => {
  if (req.method !== 'POST') return json(405, {error: 'POST only'});
  const who = await caller(req);
  if (who instanceof Response) return who;
  if (!OFFICE.includes(who.profile.role)) return json(403, {error: 'the assistant\'s scheduled runs are for office roles'});
  const base = process.env.URL || new URL(req.url).origin;
  const r = await fetch(base + '/.netlify/functions/assistant-background', {method: 'POST', headers: {'x-assistant-key': assistantKey(), 'content-type': 'application/json'},
    body: JSON.stringify({ws: who.profile.workspace_id, only: who.profile.id})});
  return json(r.status === 202 || r.ok ? 200 : 502, {started: r.status === 202 || r.ok});
};
export const config = {path: '/api/assistant'};
