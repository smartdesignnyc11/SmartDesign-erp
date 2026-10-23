// The owner's team tools: invite a person (email, role, who they are in the app) and Sign Out Everywhere.
// Anyone may sign out their own other devices; only the owner may sign out someone else or invite.
import {caller, json, rest} from './lib/auth.mjs';
const ROLES = ['owner', 'pm', 'coord', 'foreman', 'crew', 'driver', 'designer', 'design_mgr', 'billing', 'controller', 'none'];
const SVC = () => process.env.SUPABASE_SERVICE_ROLE_KEY, BASE = () => process.env.SUPABASE_URL;
async function admin(path, method, body) {
  const r = await fetch(BASE() + '/auth/v1' + path, {method, headers: {apikey: SVC(), authorization: 'Bearer ' + SVC(), 'content-type': 'application/json'}, body: body ? JSON.stringify(body) : undefined});
  const t = await r.text(); let j = {}; try { j = t ? JSON.parse(t) : {}; } catch {}
  if (!r.ok) throw new Error(j.msg || j.message || j.error_description || ('auth ' + r.status));
  return j;
}
export default async (req) => {
  if (req.method !== 'POST') return json(405, {error: 'POST only'});
  const who = await caller(req);
  if (who instanceof Response) return who;
  const {user, profile} = who;
  let b = {}; try { b = await req.json(); } catch {}
  const owner = profile.role === 'owner';

  if (b.action === 'signout') {
    const target = b.profileId || user.id;
    if (target !== user.id && !owner) return json(403, {error: 'only the owner can sign someone else out'});
    const rows = await rest('profiles?select=id,workspace_id,email&id=eq.' + encodeURIComponent(target));
    if (!rows[0] || rows[0].workspace_id !== profile.workspace_id) return json(404, {error: 'no such person in this firm'});
    const n = await rest('rpc/admin_signout', {method: 'POST', body: JSON.stringify({p_user: target})});
    return json(200, {signedOut: n, email: rows[0].email});
  }
  if (b.action === 'invite') {
    if (!owner) return json(403, {error: 'only the owner invites'});
    const email = String(b.email || '').trim().toLowerCase();
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return json(400, {error: 'that is not an email address'});
    const role = ROLES.includes(b.role) ? b.role : 'none';
    if (role === 'owner') return json(400, {error: 'a second owner is set by hand, not by invitation'});
    const found = await rest('profiles?select=id,workspace_id,workspaces,role&email=eq.' + encodeURIComponent(email));
    let id, move = null;
    if (found[0]) {
      // Someone already signed in to another of the owner's own workspaces (the demo, when the owner invites from the
      // team's workspace) is brought into this one and keeps the other in his list. Anyone else's firm is refused.
      const mine = [profile.workspace_id, ...(profile.workspaces || [])];
      if (found[0].workspace_id !== profile.workspace_id) {
        if (!mine.includes(found[0].workspace_id)) return json(409, {error: 'that address belongs to another firm'});
        move = [...new Set([...(found[0].workspaces || []), found[0].workspace_id])].filter(w => w !== profile.workspace_id);
      }
      id = found[0].id;
    } else {
      try { id = (await admin('/invite', 'POST', {email, data: {name: b.name || ''}})).id; }
      catch (e) { return json(400, {error: 'Supabase could not send the invitation: ' + e.message}); }
    }
    await rest('profiles?id=eq.' + id, {method: 'PATCH', headers: {prefer: 'return=minimal'}, body: JSON.stringify({role, workspace_id: profile.workspace_id, app_user_id: b.appUserId || null, ...(b.name ? {name: b.name} : {}), ...(move ? {workspaces: move} : {})})});
    return json(200, {invited: !found[0], moved: !!move, id, email, role});
  }
  return json(400, {error: 'unknown action'});
};
export const config = {path: '/api/team'};
