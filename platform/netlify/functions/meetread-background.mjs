// The model's read of a team meeting's transcript, in the background (up to 15 minutes; the caller gets 202 at once).
// Started by the Drive watcher (lib/meetwatch.mjs) with a key only the server knows, once the doc is filed. It reads
// the whole transcript in parts with the shared question (meetdoc_core.cjs: prompt, parseAnswer, merge), charged to
// the meeting's organiser within the caps, and keeps the items on the transcript's own row (meettx:<id>, the
// attendees'). The meeting's review moves to "new": the first app of someone who may read it builds the Meeting
// Review (matching by time against Meeting Mode, reconciling what was entered live). If the model cannot be reached,
// the review moves on anyway and the app reads the transcript with the rules. The words are never logged.
import {rest} from './lib/auth.mjs';
import {claude} from './ai.mjs';
import {CORE, meetKey} from './lib/meetwatch.mjs';
import {pushTo} from './lib/push.mjs';

export async function readMeeting(ws, meetingId, organizerUid, {ask = claude, push = pushTo} = {}) {
  const rows = await rest(`collections?select=name,data&workspace_id=eq.${encodeURIComponent(ws)}&name=in.(${['meetings', 'users', 'company', 'meettx:' + meetingId].map((n) => encodeURIComponent(`"${n}"`)).join(',')})`);
  const C = {}; for (const r of rows || []) C[r.name] = r.data;
  const m = (C.meetings || []).find((x) => x && x.id === meetingId), T = C['meettx:' + meetingId];
  if (!m || !T || !T.text) return {error: 'nothing to read'};
  const users = C.users || [];
  const staff = users.filter((u) => u && u.name && u.role !== 'client' && !/^mb_/.test(u.role || '')).map((u) => u.name);
  const profs = await rest(`profiles?select=id,role,workspace_id,name,private_key,app_user_id&workspace_id=eq.${encodeURIComponent(ws)}&app_user_id=eq.${encodeURIComponent(organizerUid || (m.owner || {}).uid || '')}&limit=1`);
  const prof = profs && profs[0];
  let items = null, parts = 0, got = 0;
  if (prof) {
    const map = ((C.company || {}).meetSpeakers) || {}, nk = (x) => String(x || '').toLowerCase().replace(/[^a-z0-9 ]+/g, ' ').replace(/\s+/g, ' ').trim();
    const speakers = (T.speakers || []).map((l) => { const x = map[nk(l)]; return `${l}: ${x ? (x.outside ? 'outside the team' : x.name) : (staff.find((n) => nk(n) === nk(l)) || 'not known')}`; });
    const ctx = {staff, speakers, date: m.date, notes: {steps: (m.steps || []).map((s) => `[${s.owner}] ${s.title}: ${s.detail}`), decisions: (m.decisions || []).map((d) => d.text)}, projects: []};
    const P = CORE.parts(T.text); parts = P.length;
    const lists = [];
    for (let i = 0; i < P.length; i++) {
      const r = await ask({id: prof.id}, prof, {purpose: 'meetread', max_tokens: 4000, messages: [{role: 'user', content: CORE.prompt(P[i], i, P.length, ctx)}]});
      if (r.status !== 200) continue;
      try {
        const j = JSON.parse(r.text);
        const L = CORE.parseAnswer((j.content || []).filter((b) => b.type === 'text').map((b) => b.text).join(''));
        L && (lists.push(L), got++);
      } catch {}
    }
    got && (items = CORE.merge(lists));
  }
  const now = new Date().toISOString();
  await rest('rpc/meet_file', {method: 'POST', body: JSON.stringify({p_ws: ws,
    p_meeting: {id: meetingId, review: {state: 'new', at: now, source: 'drive', read: items ? 'model' : 'rules'}},
    p_text: items ? {extract: {by: 'model', at: now, items, parts, partsRead: got}} : {extract: null}})});
  // the meeting's owner hears that the review is ready
  let pushed = 0;
  try {
    const own = await rest(`profiles?select=id,private_key&workspace_id=eq.${encodeURIComponent(ws)}&app_user_id=eq.${encodeURIComponent((m.owner || {}).uid || '')}&limit=1`);
    const o = own && own[0];
    o && (pushed = await push(o.private_key || o.id, {title: 'Meeting Review ready', body: `${m.title}: what the meeting said, to approve`, url: '/'}));
  } catch (e) { console.error('meetread push', e.message); }
  return {meeting: meetingId, parts, partsRead: got, items: items ? items.length : 0, pushed};
}
export default async (req) => {
  if (req.headers.get('x-meet-key') !== meetKey()) return new Response('no', {status: 403});
  let b = {}; try { b = await req.json(); } catch {}
  const r = await readMeeting(b.ws, b.meeting, b.organizer);
  console.log('meetread', JSON.stringify(r));
};
