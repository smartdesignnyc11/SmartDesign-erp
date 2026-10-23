// The team meeting's transcript, from Drive to the Meeting Review (docs/TASKS_PLAN.md §2 item 6). Run inside each
// watch run of the organiser (lib/watch.mjs), with their short-lived Google key, read-only:
//   1. the folders the owner set in the app (Settings in Meetings: company.meetWatch [{id, name, folder,
//      organizerUid, ownerUid, on}]) whose organiser is this person;
//   2. each new "Notes by Gemini" doc in that folder (that folder only: the query names its id), read through the
//      Docs API so each transcript heading keeps its link (documents.get, tabs included), else Drive's Markdown
//      export;
//   3. the doc's parse (lib/meetdoc_core.cjs, the same file the app runs) is filed on the meeting: the meeting's
//      notes on the shared meetings row (joined to Meeting Mode's record of that day when there is one), and the
//      transcript on its own row (meettx:<meeting id>) that only the meeting's attendees and the owner can read;
//   4. the model's read starts in the background (meetread-background), so the review is ready when the meeting's
//      owner opens the app, about 15 minutes after the call.
// The transcript's words are never logged: only counts and ids.
import {rest} from './auth.mjs';
import CORE from './meetdoc_core.cjs';
import crypto from 'node:crypto';
export {CORE};
export const meetKey = () => crypto.createHmac('sha256', process.env.WATCH_KEY || '').update('meetread-run').digest('hex');

async function gget(tok, url, asText) {
  const r = await fetch(url.startsWith('http') ? url : 'https://www.googleapis.com' + url, {headers: {authorization: 'Bearer ' + tok}});
  if (!r.ok) { const e = new Error(`Google ${r.status}`); e.status = r.status; throw e; }
  return asText ? r.text() : r.json();
}
// The new notes docs in one folder since the cursor (its id is the only folder named in the query).
export async function folderDocs(tok, folder, since) {
  const safe = String(folder || '').replace(/[^A-Za-z0-9_-]/g, '');
  if (!safe) return [];
  const q = encodeURIComponent(`'${safe}' in parents and trashed = false and mimeType = 'application/vnd.google-apps.document' and name contains 'Notes by Gemini'` + (since ? ` and modifiedTime > '${since}'` : ''));
  const j = await gget(tok, `/drive/v3/files?q=${q}&orderBy=createdTime&pageSize=20&fields=files(id,name,createdTime,modifiedTime,webViewLink)`);
  return j.files || [];
}
// A Google Docs document as the text the parser reads: headings as Markdown headings, bold runs as **bold**, and the
// link of every heading (the transcript's ### hh:mm:ss and the notes' sections), so the review can open the doc there.
export function docsToText(doc, docId) {
  const out = [], links = {};
  const tabs = [];
  const walk = (T) => (T || []).forEach((t) => { tabs.push(t); walk(t.childTabs); });
  walk(doc.tabs);
  const bodies = tabs.length ? tabs.map((t) => ({tab: (t.tabProperties || {}).tabId || '', body: ((t.documentTab || {}).body || {}).content || []})) : [{tab: '', body: (doc.body || {}).content || []}];
  for (const {tab, body} of bodies) {
    for (const el of body) {
      const p = el.paragraph;
      if (!p) continue;
      const style = (p.paragraphStyle || {}).namedStyleType || '', hid = (p.paragraphStyle || {}).headingId || '';
      let line = '';
      for (const e of p.elements || []) {
        const tr = e.textRun; if (!tr) continue;
        const s = String(tr.content || '').replace(/\n$/, '');
        if (!s) continue;
        line += (tr.textStyle || {}).bold && s.trim() ? `**${s.trim()}**${/\s$/.test(s) ? ' ' : ''}` : s;
      }
      line = line.replace(/\*\*\s*\*\*/g, '').trim();
      if (!line) continue;
      const h = /^HEADING_(\d)$/.exec(style) || (style === 'TITLE' ? [0, '1'] : null);
      if (h) {
        out.push('#'.repeat(Math.min(6, +h[1])) + ' ' + line.replace(/\*\*/g, ''));
        if (hid) { const ts = (/(\d{1,2}:\d{2}:\d{2})/.exec(line) || [])[1]; const url = `https://docs.google.com/document/d/${docId}/edit${tab ? `?tab=${tab}` : ''}#heading=${hid}`; links[ts ? ts.padStart(8, '0') : line.replace(/\*\*/g, '').slice(0, 60)] = url; }
      } else out.push((p.bullet ? '* ' : '') + line);
    }
  }
  return {text: out.join('\n'), links};
}
export async function readDoc(tok, file) {
  try {
    const d = await gget(tok, `https://docs.googleapis.com/v1/documents/${encodeURIComponent(file.id)}?includeTabsContent=true`);
    const r = docsToText(d, file.id);
    if (r.text.trim()) return {...r, via: 'docs'};
  } catch (e) { if (e.status === 404) throw e; }
  // the Docs API off for the firm's Google project: Drive's own export (no heading links)
  for (const mt of ['text/markdown', 'text/plain']) {
    try { const t = await gget(tok, `/drive/v3/files/${encodeURIComponent(file.id)}/export?mimeType=${encodeURIComponent(mt)}`, true); if (t && t.trim()) return {text: t, links: {}, via: mt}; } catch {}
  }
  return {text: '', links: {}, via: 'none'};
}
// The firm's settings and people, read once per run.
async function firm(ws) {
  const rows = await rest(`collections?select=name,data&workspace_id=eq.${encodeURIComponent(ws)}&name=in.(company,users,meetings)`);
  const C = {}; for (const r of rows || []) C[r.name] = r.data;
  return {watch: (((C.company || {}).meetWatch) || []).filter((w) => w && w.folder && w.on !== false), users: C.users || [], meetings: Array.isArray(C.meetings) ? C.meetings : []};
}
const norm = (s) => String(s || '').toLowerCase().replace(/[^a-z0-9 ]+/g, ' ').replace(/\s+/g, ' ').trim();
// The people in the meeting who use the app: their ids, who may read the transcript.
export function membersOf(doc, users, extra) {
  const U = (users || []).filter((u) => u && u.id && u.role !== 'client' && !/^mb_/.test(u.role || ''));
  const ids = new Set(extra.filter(Boolean));
  // the invited list carries each Google account's address: a user with that address reads the transcript
  (doc.invited || []).forEach((x) => { const u = U.find((v) => x.email && String(v.email || '').toLowerCase() === x.email); u && ids.add(u.id); });
  (doc.attendees || []).forEach((n) => {
    const k = norm(n), full = U.find((u) => norm(u.name) === k), first = U.filter((u) => norm(u.name).split(' ')[0] === k.split(' ')[0]);
    const u = full || (first.length === 1 ? first[0] : null);
    u && ids.add(u.id);
  });
  return [...ids];
}
// What is filed: the meeting's notes (shared) and its transcript (the attendees').
export function filing(doc, file, w, users, read) {
  const id = 'mt' + crypto.createHash('sha256').update(file.id).digest('hex').slice(0, 10);
  const owner = (users || []).find((u) => u.id === w.ownerUid) || (users || []).find((u) => u.role === 'coord') || {};
  const meeting = {
    id, source: 'drive', msgId: 'drive:' + file.id, series: w.id, title: doc.title || w.name || 'Team meeting', date: doc.date || String(file.createdTime || '').slice(0, 10),
    summary: doc.summary || '', sections: (doc.sections || []).concat(doc.quick || []), decisions: (doc.decisions || []).map((d) => ({text: d.name ? `${d.name}: ${d.text}` : d.text, name: d.name || '', status: d.status === 'discuss' ? 'needs-further-discussion' : 'aligned'})),
    steps: doc.steps || [], details: doc.details || [], attendees: doc.attendees || [], docUrl: file.webViewLink || `https://docs.google.com/document/d/${file.id}/edit`, docRead: true,
    doc: {id: file.id, url: file.webViewLink || '', name: file.name || ''}, owner: {uid: owner.id || '', name: owner.name || ''},
    review: {state: 'reading', at: new Date().toISOString(), source: 'drive'}, status: 'new', proposals: [], projectId: '', clientId: '', createdAt: (doc.date || new Date().toISOString().slice(0, 10)),
  };
  const text = {id: 'mx_' + id, meetingId: id, members: membersOf(doc, users, [w.organizerUid, w.ownerUid]), text: CORE.transcriptText(doc), lines: doc.lines, start: doc.start || '', links: Object.assign({}, doc.links || {}, read.links || {}), url: meeting.docUrl, at: new Date().toISOString(), via: read.via};
  return {meeting, text};
}
// One organiser's folders: what was filed (ids and counts only), and each folder's cursor.
export async function watchMeetings(row, tok, opts = {}) {
  const deadline = opts.deadline || Date.now() + 15000, out = [], cur = Object.assign({}, (row.cursors && row.cursors.meet) || {});
  if (!row.app_user_id) return {filed: out, meet: cur};
  const F = await firm(row.workspace_id);
  const mine = F.watch.filter((w) => w.organizerUid === row.app_user_id);
  if (!mine.length) return {filed: out, meet: cur};
  for (const w of mine) {
    if (Date.now() > deadline) break;
    const since = cur[w.id] || '';
    let files = [];
    try { files = await folderDocs(tok, w.folder, since); } catch (e) { out.push({series: w.id, error: String(e.message).slice(0, 80)}); continue; }
    for (const f of files) {
      if (Date.now() > deadline) break;
      if (F.meetings.some((m) => m && m.doc && m.doc.id === f.id)) { cur[w.id] = f.modifiedTime || cur[w.id]; continue; }
      const read = await readDoc(tok, f);
      const doc = CORE.parseDoc(read.text, {name: f.name});
      if (!doc.lines.length && !doc.steps.length) { cur[w.id] = f.modifiedTime || cur[w.id]; continue; }
      const {meeting, text} = filing(doc, f, w, F.users, read);
      const r = await rest('rpc/meet_file', {method: 'POST', body: JSON.stringify({p_ws: row.workspace_id, p_meeting: meeting, p_text: text})});
      const filedId = (r && r.id) || meeting.id;
      out.push({series: w.id, doc: f.id, meeting: filedId, lines: doc.lines.length, via: read.via, merged: !!(r && r.merged)});
      cur[w.id] = f.modifiedTime || cur[w.id];
      if (opts.read !== false) {
        try {
          const base = process.env.URL || 'https://smartdesigns-erp.netlify.app';
          await fetch(base + '/.netlify/functions/meetread-background', {method: 'POST', headers: {'x-meet-key': meetKey(), 'content-type': 'application/json'}, body: JSON.stringify({ws: row.workspace_id, meeting: filedId, organizer: row.app_user_id})});
        } catch (e) { console.error('meetread start', e.message); }
      }
    }
  }
  return {filed: out, meet: cur};
}
