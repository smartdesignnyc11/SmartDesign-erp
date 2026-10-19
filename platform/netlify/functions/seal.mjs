// /api/seal: the books' seals held by the server. 'seal' (the owner or the controller, when a month closes) recomputes
// that month's chain from the server's copy of the books and keeps it, add-only. 'verify' (any office role) checks
// every sealed month's latest seal against the server's books now, independent of any browser.
import {caller, json, rest} from './lib/auth.mjs';
import {chain, fnv, compare} from './lib/chain.mjs';
const SEALERS = ['owner', 'controller'], READERS = ['owner', 'controller', 'pm', 'billing', 'coord'];
const books = async ws => ((await rest(`collections?select=data&workspace_id=eq.${encodeURIComponent(ws)}&name=eq.gl`))[0] || {}).data || {};
export default async (req) => {
  if (req.method !== 'POST') return json(405, {error: 'POST only'});
  const who = await caller(req);
  if (who instanceof Response) return who;
  const {user, profile} = who;
  let b = {}; try { b = await req.json(); } catch {}
  const ws = profile.workspace_id;
  if (b.action === 'seal') {
    if (!SEALERS.includes(profile.role)) return json(403, {error: 'only the owner or the controller closes a month'});
    if (!/^\d{4}-\d{2}$/.test(String(b.ym || ''))) return json(400, {error: 'ym required, like 2026-08'});
    const gl = await books(ws), s = chain(gl, b.ym), f = chain(gl, b.ym, fnv);
    const row = {workspace_id: ws, ym: b.ym, n: s.n, head_sha: s.head, head_fnv: f.head, app_head: b.head || null,
      matches: b.head ? b.head === f.head : null, links: s.links, by_user: user.id, by_name: profile.name || ''};
    await rest('period_seals', {method: 'POST', headers: {prefer: 'return=minimal'}, body: JSON.stringify(row)});
    return json(200, {ym: b.ym, n: s.n, head: s.head, matches: row.matches});
  }
  if (b.action === 'verify') {
    if (!READERS.includes(profile.role)) return json(403, {error: 'office roles only'});
    const seals = await rest(`period_seals?select=ym,n,head_sha,head_fnv,app_head,matches,links,sealed_at,by_name&workspace_id=eq.${encodeURIComponent(ws)}&order=ym.asc,sealed_at.desc`);
    const latest = []; const seen = new Set();
    for (const s of seals || []) if (!seen.has(s.ym)) { seen.add(s.ym); latest.push(s); }
    const gl = await books(ws);
    return json(200, {months: latest.map(s => ({ym: s.ym, sealedAt: s.sealed_at, by: s.by_name, sealedN: s.n, sawSame: s.matches, ...compare(s, gl)}))});
  }
  return json(400, {error: 'unknown action'});
};
export const config = {path: '/api/seal'};
