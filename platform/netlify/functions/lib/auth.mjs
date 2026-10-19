// Who is calling: the Supabase session token the page sends, checked against Supabase, and the caller's role
// read from public.profiles (which only the owner edits). The service key never leaves the server.
const URL_ = () => process.env.SUPABASE_URL;
const SVC = () => process.env.SUPABASE_SERVICE_ROLE_KEY;
export const MEMBER_ROLES = ['owner','pm','coord','designer','design_mgr','billing','controller','foreman','crew','driver'];

export const json = (status, obj) => new Response(JSON.stringify(obj), {status, headers: {'content-type': 'application/json', 'cache-control': 'no-store'}});

export async function rest(path, opts = {}) {
  const r = await fetch(URL_() + '/rest/v1/' + path, {...opts, headers: {apikey: SVC(), authorization: 'Bearer ' + SVC(), 'content-type': 'application/json', ...(opts.headers || {})}});
  const t = await r.text();
  if (!r.ok) throw new Error('database ' + r.status + ': ' + t.slice(0, 200));
  return t ? JSON.parse(t) : null;
}

// Returns {user, profile} or a Response to send back.
export async function caller(req) {
  if (!URL_() || !SVC()) return json(500, {error: 'the server is not configured (SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY)'});
  const h = req.headers.get('authorization') || '';
  const token = h.startsWith('Bearer ') ? h.slice(7) : '';
  if (!token) return json(401, {error: 'sign in first'});
  const r = await fetch(URL_() + '/auth/v1/user', {headers: {apikey: SVC(), authorization: 'Bearer ' + token}});
  if (!r.ok) return json(401, {error: 'your session has ended: sign in again'});
  const user = await r.json();
  // The session must still be alive (Sign Out Everywhere ends it before the key expires).
  try {
    const sid = JSON.parse(Buffer.from(token.split('.')[1], 'base64url').toString()).session_id;
    if (sid && !(await rest('rpc/session_alive_for', {method: 'POST', body: JSON.stringify({p_session: sid, p_user: user.id})})))
      return json(401, {error: 'this device was signed out: sign in again'});
  } catch (e) { return json(401, {error: 'sign in again'}); }
  const rows = await rest('profiles?select=id,role,workspace_id,name,private_key,app_user_id&id=eq.' + encodeURIComponent(user.id));
  const profile = rows && rows[0];
  if (!profile || !MEMBER_ROLES.includes(profile.role)) return json(403, {error: 'this account has no access yet: ask the owner to set your role'});
  return {user, profile};
}
