// The team meeting's Drive watcher and the doc's parse, with Supabase, Google and the model mocked, offline
// (docs/TASKS_PLAN.md §2 item 6). The organiser's watch run finds the new "Notes by Gemini" doc in the folder the
// owner set (that folder only), reads it through the Docs API with each heading's link (or Drive's export when the
// Docs API is off), files the notes on Meeting Mode's record of that day and the transcript on its own row for the
// attendees, never twice, never logging the words; the background read asks the model in parts and keeps its items
// with the transcript, and tells the meeting's owner. node test/meetwatch_test.mjs
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
Object.assign(process.env, {SUPABASE_URL: 'https://db', SUPABASE_SERVICE_ROLE_KEY: 's', GOOGLE_CLIENT_ID: 'cid', GOOGLE_CLIENT_SECRET: 'csec', WATCH_KEY: crypto.randomBytes(32).toString('base64'), URL: 'https://site'});
const here = (p) => fileURLToPath(new URL(p, import.meta.url));
let n = 0; const ok = (c, m) => { assert.ok(c, m); n++; };
ok(fs.readFileSync(here('../netlify/functions/lib/meetdoc_core.cjs'), 'utf8') === fs.readFileSync(here('../../src/meetdoc_core.js'), 'utf8'), 'lib/meetdoc_core.cjs is a copy of src/meetdoc_core.js (run platform/build.py)');
const SAMPLE = fs.readFileSync(here('../../tests/meeting_sample_gemini.md'), 'utf8');
const NAME = 'Weekly Jobs - 2026/09/03 09:58 EDT - Notes by Gemini';
const {seal} = await import('../netlify/functions/lib/seal.mjs');
const MW = await import('../netlify/functions/lib/meetwatch.mjs');
const {CORE} = MW;
const {watchOne} = await import('../netlify/functions/lib/watch.mjs');
const BG = await import('../netlify/functions/meetread-background.mjs');

// ---- the parse, on its own
const doc = CORE.parseDoc(SAMPLE, {name: NAME});
ok(doc.title === 'Weekly Jobs' && doc.date === '2026-09-03' && doc.start === '2026-09-03T09:58:00', `the file name gives the title, the day and the recording's start: ${doc.title} ${doc.date} ${doc.start}`);
ok(doc.lines.length === 22 && doc.lines.every((l) => l.speaker && l.text && /^\d\d:\d\d:\d\d$/.test(l.ts)), `every transcript line, with its speaker and its time: ${doc.lines.length}`);
ok(doc.lines.find((l) => /tomorrow then/.test(l.text)).ts === '00:12:27' && doc.lines.find((l) => /LEN-7/.test(l.text)).exact, 'a heading\'s first line is exact; the next ones fall by their words before the next heading');
ok(doc.steps.length === 3 && doc.steps[0].owner === 'Chen Biron' && doc.steps[0].title === 'Chase Shop Drawings', 'next steps: [Person] Title: text');
ok(doc.decisions.length === 2 && doc.decisions[0].status === 'aligned' && doc.decisions[1].status === 'discuss', 'decisions, aligned and to discuss');
ok(doc.details.length === 3 && doc.details[1].ts === '00:07:40' && doc.links['00:07:40'] === '#heading=h.t0740', 'details keep their [hh:mm:ss] links');
ok(doc.quick.length === 2 && doc.sections.length === 2 && /walked the board/.test(doc.summary), 'quick notes and the summary');
ok(['Chen Biron', 'Carlos', 'Ruth Okafor'].every((x) => doc.attendees.includes(x)), 'the invited and the speakers are the attendees');
// the same doc pasted from the page (no Markdown) reads the same transcript
const plain = SAMPLE.replace(/^#+\s*/gm, '').replace(/\*\*/g, '').replace(/^\* /gm, '').replace(/^- \[ \] /gm, '');
const d2 = CORE.parseDoc(plain, {name: NAME});
ok(d2.lines.length === 22 && d2.steps.length === 3 && d2.decisions.length === 2, `the doc pasted as plain text reads the same: ${d2.lines.length} lines, ${d2.steps.length} steps, ${d2.decisions.length} decisions`);
// the rules read the whole transcript: what Gemini's next steps missed is there
const R = CORE.rules(doc, {staff: ['Owner', 'Alan', 'Chen Biron', 'Angel', 'Maya'], date: doc.date});
const has = (k, ...rx) => R.some((x) => x.kind === k && rx.every((r) => r.test(JSON.stringify(x))));
ok(has('waiting', /Ruth Okafor/, /2026-09-08/) && has('date', /2026-09-04/, /00:12:27/) && has('project', /88 Orchard Street/) && has('waiting', /portal samples/, /Carlos/), 'the rules find what the next steps missed: the expediter\'s promise, the new date, the new project, the vendor\'s promise');
ok(has('done', /00:06:43/) && has('owner', /"owner":"Alan"/) && has('note', /phone/) && has('money', /1250/, /credit/) && has('meeting', /2026-09-10/) && has('decision', /discuss/), 'and the completion, the reassignment, the note, the credit, the meeting to set up and the decision to discuss');
ok(R.filter((x) => /clear the bathroom/i.test(x.what)).length === 1, "Gemini's step said in the room is one item, not two");
ok(!R.some((x) => /^STA-2\d, the/.test(x.quote || '')), 'naming the next task is the walk, not an item');
// who is talking (2026-10-23): the invited carry their Google addresses; a dial-in is a speaker nobody knows; two
// people on one label are flagged; a first-person promise makes the speaker the owner; "have X do Y" makes X the doer
const SP = CORE.parseDoc(fs.readFileSync(here('../../tests/meeting_sample_speakers.md'), 'utf8'), {name: 'Coordination - 2026/09/03 14:00 EDT - Notes by Gemini'});
ok(SP.invited.some((x) => x.name === 'C. Biron' && x.email === 'chen@example.com') && SP.speakers.includes('+1 212-555-0144'), `the invited keep their addresses; a dial-in is a speaker: ${SP.speakers}`);
ok(SP.shared.length === 1 && SP.shared[0].label === 'C. Biron' && SP.shared[0].with === 'Maya Lund', `"C. Biron and Maya reviewed", with Maya never speaking, is a shared device: ${JSON.stringify(SP.shared)}`);
ok(doc.shared.length === 0, 'the first meeting has no shared device');
const MAP = {'C. Biron': {name: 'Chen Biron'}, Alan: {name: 'Alan'}};
const SR = CORE.rules(SP, {staff: ['Owner', 'Alan', 'Chen Biron', 'Angel'], date: SP.date, speakerOf: (l) => MAP[l] || {unknown: true}});
const sp = (rx) => SR.find((x) => rx.test(x.what || ''));
ok(sp(/call the expediter/i).owner === 'Alan' && sp(/call the expediter/i).ownerFrom === 'speaker' && sp(/call the expediter/i).due === '2026-09-04', "'I'll call the expediter tomorrow': Alan, the speaker, owns it");
ok(sp(/tile layout/i).owner === 'Chen Biron', "'I'm going to send': the speaker owns it");
ok(sp(/measure the parlor/i).owner === 'Angel' && sp(/measure the parlor/i).kind === 'task', "'have Angel measure': Angel does it");
ok(sp(/template photos/i).kind === 'waiting' && sp(/template photos/i).party === 'Kestrel' && sp(/template photos/i).owner === 'Chen Biron', "'have Kestrel send': Kestrel is Waiting On, the speaker owns the chase");
ok(sp(/permit drawings/i).owner === '' && sp(/permit drawings/i).speakerUnknown, "a dial-in's promise asks who is speaking before anyone owns it");
const SR2 = CORE.rules(SP, {staff: ['Owner', 'Alan', 'Chen Biron', 'Angel'], date: SP.date, speakerOf: (l) => MAP[l] || {outside: true}});
ok(SR2.find((x) => /permit drawings/i.test(x.what)).kind === 'waiting', 'once the dial-in is someone outside the team, the promise is Waiting On');
ok(/Speakers \(the label/.test(CORE.prompt('x', 0, 1, {speakers: ['C. Biron: Chen Biron']})), 'the model is told who each speaker is');
// time against the screen log
const log = [{taskKey: 'LEN-7', from: '2026-09-03T10:08:30', to: '2026-09-03T10:11:00'}, {taskKey: 'LEN-8', from: '2026-09-03T10:11:00', to: '2026-09-03T10:13:00'}];
ok(CORE.onScreen(log, CORE.wall('2026-09-03T09:58:00') + 747) === 'LEN-7', '00:12:27 after a 09:58 start is LEN-7 on screen');
ok(CORE.bestShift([{sec: CORE.wall('2026-09-03T09:58:00') + 630 + 40, key: 'LEN-7'}, {sec: CORE.wall('2026-09-03T09:58:00') + 780 + 40, key: 'LEN-8'}], log, 300) <= 0, 'a recording that started late is shifted back by the IDs said aloud');
// the model's answer, read strictly
const A = CORE.parseAnswer('Sure: {"items":[{"kind":"waiting","party":"Carlos","what":"samples","due":"2026-09-09","quote":"We will deliver","ts":"0:15:16"},{"kind":"bogus"},{"kind":"task","ref":"not an id","due":"Friday"}]}');
ok(A.length === 2 && A[0].ts === '00:15:16' && A[1].ref === '' && A[1].due === '', 'the model\'s items are kept to the shape: unknown kinds dropped, a ref is an ID, a date is a date');

// ---- the watch run, mocked
const W = {collections: {}, rpc: [], fetched: [], docsOff: false, started: [], logs: []};
const rowName = (u) => decodeURIComponent((/name=eq\.([^&]+)/.exec(u) || [])[1] || '');
W.collections.company = {meetWatch: [{id: 'mw1', name: 'Weekly Jobs', folder: 'FOLDER123456', organizerUid: 'u_chen', ownerUid: 'u_chen', on: true}, {id: 'mw2', name: 'Other', folder: 'OTHERFOLDER99', organizerUid: 'u_alan', ownerUid: 'u_alan', on: true}]};
W.collections.users = [{id: 'u_owner', name: 'Owner', role: 'owner'}, {id: 'u_alan', name: 'Alan', role: 'pm'}, {id: 'u_chen', name: 'Chen Biron', role: 'coord'}, {id: 'u_angel', name: 'Angel', role: 'foreman'}, {id: 'u_billing', name: 'Billing', role: 'billing'}, {id: 'u_klein', name: 'Sarah Klein', role: 'client'}];
W.collections.meetings = [{id: 'mt_live', title: 'Weekly Jobs', date: '2026-09-03', screenLog: log, changes: [{taskKey: 'LEN-7', field: 'note', to: 'x'}], proposals: [{id: 'keep'}], owner: {uid: 'u_chen', name: 'Chen Biron'}, steps: []}];
// a Google Docs document built from the sample: headings with ids, bold runs
function docsJson(md) {
  const content = md.split('\n').filter((l) => l.trim()).map((l, i) => {
    const h = /^(#{1,6})\s*(.*)$/.exec(l);
    if (h) return {paragraph: {paragraphStyle: {namedStyleType: `HEADING_${h[1].length}`, headingId: `h.id${i}`}, elements: [{textRun: {content: h[2] + '\n'}}]}};
    const b = /^\*\*([^*]+)\*\*\s*(.*)$/.exec(l);
    return {paragraph: {paragraphStyle: {namedStyleType: 'NORMAL_TEXT'}, elements: b ? [{textRun: {content: b[1], textStyle: {bold: true}}}, {textRun: {content: ' ' + b[2] + '\n'}}] : [{textRun: {content: l.replace(/^\* /, '') + '\n'}}], bullet: /^\* /.test(l) ? {} : undefined}};
  });
  const cut = content.findIndex((c) => /Transcript/.test(JSON.stringify(c)) && /HEADING_1/.test(JSON.stringify(c)));
  return {tabs: [{tabProperties: {tabId: 't.notes'}, documentTab: {body: {content: content.slice(0, cut)}}}, {tabProperties: {tabId: 't.transcript'}, documentTab: {body: {content: content.slice(cut)}}}]};
}
const J = (x, s = 200) => new Response(JSON.stringify(x), {status: s});
function metFile(p) {     // what the database function does, in JS (its SQL is proven in test/schema_pg_test.py)
  const arr = W.collections.meetings || [];
  let i = arr.findIndex((m) => m.id === p.p_meeting.id || (p.p_meeting.doc && p.p_meeting.doc.id && m.doc && m.doc.id === p.p_meeting.doc.id));
  if (i < 0) i = arr.findIndex((m) => m.date === p.p_meeting.date && !(m.doc && m.doc.id) && ((p.p_meeting.series && m.series === p.p_meeting.series) || m.screenLog));
  const inc = {...p.p_meeting}; ['id', 'proposals', 'changes', 'screenLog', 'status', 'createdAt', 'projectId', 'clientId'].forEach((k) => delete inc[k]);
  let id;
  if (i >= 0) { id = arr[i].id; if (arr[i].owner && arr[i].owner.uid) delete inc.owner; if ((arr[i].steps || []).length) delete inc.steps; if (arr[i].title) delete inc.title; arr[i] = {...arr[i], ...inc}; }
  else { id = p.p_meeting.id; arr.push(p.p_meeting); }
  W.collections.meetings = arr;
  if (p.p_text) W.collections['meettx:' + id] = {...(W.collections['meettx:' + id] || {}), ...p.p_text, id: 'mx_' + id, meetingId: id};
  return {id, merged: i >= 0};
}
globalThis.fetch = async (url, o = {}) => {
  const u = String(url), body = o.body ? String(o.body) : '';
  W.fetched.push(u);
  if (u.includes('/rest/v1/collections?')) {
    const m = /name=in\.\(([^)]*)\)/.exec(decodeURIComponent(u));
    const names = m ? m[1].split(',').map((x) => x.replace(/"/g, '')) : [rowName(u)];
    return J(names.filter((nm) => W.collections[nm] !== undefined).map((nm) => ({name: nm, data: W.collections[nm]})));
  }
  if (u.endsWith('/rest/v1/rpc/meet_file')) { const p = JSON.parse(body); W.rpc.push(p); return J(metFile(p)); }
  if (u.endsWith('/rest/v1/rpc/watch_put_inbox')) return J(1);
  if (u.includes('/rest/v1/google_watch')) return new Response(null, {status: 204});
  if (u.includes('/rest/v1/profiles')) return J(u.includes('u_chen') ? [{id: 'p-chen', role: 'coord', workspace_id: 'w', name: 'Chen Biron', private_key: 'pk-chen', app_user_id: 'u_chen'}] : []);
  if (u.includes('/rest/v1/push_subs')) return J([]);
  if (u === 'https://oauth2.googleapis.com/token') return J({access_token: 'AT', expires_in: 3599});
  if (u.includes('/gmail/v1/users/me/messages?')) return J({messages: []});
  if (u.includes('/calendar/v3/')) return J({items: [], nextSyncToken: 'C'});
  if (u.includes('/drive/v3/files?') && u.includes('Notes%20by%20Gemini')) {
    const q = decodeURIComponent(u);
    W.folderQ = (W.folderQ || []).concat(q);
    return J({files: q.includes("'FOLDER123456' in parents") && !q.includes("modifiedTime > '2026-09-03T11:00:00Z'") ? [{id: 'DOC1', name: NAME, createdTime: '2026-09-03T14:20:00Z', modifiedTime: '2026-09-03T14:21:00Z', webViewLink: 'https://docs.google.com/document/d/DOC1/edit'}] : []});
  }
  if (u.includes('/drive/v3/files?')) return J({files: []});
  if (u.startsWith('https://docs.googleapis.com/v1/documents/')) return W.docsOff ? J({error: {code: 403}}, 403) : J(docsJson(SAMPLE));
  if (u.includes('/drive/v3/files/DOC1/export')) { W.exported = (W.exported || 0) + 1; return new Response(SAMPLE, {status: 200}); }
  if (u === 'https://site/.netlify/functions/meetread-background') { W.started.push({key: o.headers['x-meet-key'], body: JSON.parse(body)}); return new Response('', {status: 202}); }
  throw new Error('unexpected ' + u);
};
const log0 = console.log, err0 = console.error;
console.log = (...a) => W.logs.push(a.join(' ')); console.error = (...a) => W.logs.push(a.join(' '));
const row = {person_key: 'pk-chen', workspace_id: 'w', app_user_id: 'u_chen', email: 'chen@example.com', sealed: seal('RT'), cursors: {}};
let r;
try { r = await watchOne(row, Date.now() + 20000, {push: false}); } finally { console.log = log0; console.error = err0; }
ok(r.meetings === 1 && !r.error, `the organiser's watch run filed the meeting: ${JSON.stringify(r)}`);
ok((W.folderQ || []).length === 1 && W.folderQ[0].includes("'FOLDER123456' in parents") && !W.folderQ.some((q) => q.includes('OTHERFOLDER99')), 'only the folder set for this organiser is read');
const M = W.collections.meetings, m = M.find((x) => x.id === 'mt_live');
ok(M.length === 1 && m.doc.id === 'DOC1' && m.series === 'mw1' && m.review.state === 'reading', `the doc joins Meeting Mode's record of that day: ${M.map((x) => x.id)}`);
ok(m.proposals.length === 1 && m.proposals[0].id === 'keep' && m.changes.length === 1 && m.screenLog.length === 2, "the meeting's own lists are never overwritten");
ok(m.steps.length === 3 && m.decisions.length === 2 && m.summary, "Gemini's notes are on the shared record");
const shared = JSON.stringify(W.rpc[0].p_meeting);
ok(!/Halden|confirmed it by phone|template on Monday/.test(shared), 'the transcript is not on the shared meeting record');
const T = W.collections['meettx:mt_live'];
ok(T && T.lines.length === 22 && /Halden kitchen/.test(T.text) && T.start === '2026-09-03T09:58:00', 'the transcript is on its own row, with its timed lines');
ok(['u_chen', 'u_alan', 'u_angel', 'u_owner'].every((x) => T.members.includes(x)) && !T.members.includes('u_billing') && !T.members.includes('u_klein'), `readable by the attendees who use the app: ${T.members}`);
ok(/docs\.google\.com\/document\/d\/DOC1\/edit\?tab=t\.transcript#heading=h\.id\d+/.test(T.links['00:07:40'] || ''), `each transcript heading keeps its link in the doc: ${T.links['00:07:40']}`);
ok(W.started.length === 1 && W.started[0].key === MW.meetKey() && W.started[0].body.meeting === 'mt_live', 'the model\'s read starts in the background, with the server\'s key');
ok(row.cursors.meet === undefined, 'the run keeps its cursor on the watch row, not on the caller\'s copy');
ok(!W.logs.some((l) => /Halden|inspection slot|honed marble|portal samples|template on Monday/.test(l)), 'the transcript\'s words are never logged');
// the second run: the doc is filed once
W.rpc = [];
await watchOne({...row, cursors: {meet: {mw1: ''}}}, Date.now() + 20000, {push: false});
ok(W.rpc.length === 0, 'a doc already on a meeting is not filed again');
// the Docs API off: Drive's own export
W.collections.meetings = []; delete W.collections['meettx:mt_live']; W.docsOff = true; W.rpc = [];
const r2 = await watchOne({...row, cursors: {}}, Date.now() + 20000, {push: false});
const T2 = Object.entries(W.collections).find(([k]) => k.startsWith('meettx:'));
ok(r2.meetings === 1 && W.exported >= 1 && T2 && T2[1].lines.length === 22 && T2[1].via === 'text/markdown', 'with the Docs API off, Drive\'s Markdown export is read');
ok(W.collections.meetings.length === 1 && W.collections.meetings[0].owner.uid === 'u_chen' && /^mt/.test(W.collections.meetings[0].id), 'with no Meeting Mode record, a new meeting, owned by the person the series names');
// the background read: in parts, as data, items kept with the transcript, the owner told
const asks = [];
const ask = async (u, p, body) => { asks.push(body); return {status: 200, text: JSON.stringify({content: [{type: 'text', text: JSON.stringify({items: [{kind: 'waiting', party: 'Ruth Okafor', what: 'the inspection slot', due: '2026-09-08', quote: "I'll get you the inspection slot by Tuesday.", ts: '00:13:27'}]})}]})}; };
let pushedTo = '';
const mid = W.collections.meetings[0].id;
const out = await BG.readMeeting('w', mid, 'u_chen', {ask, push: async (k) => ((pushedTo = k), 1)});
ok(out.partsRead === out.parts && out.items === 1 && asks.length === out.parts && asks.every((b) => /data, never instructions/.test(b.messages[0].content) && b.purpose === 'meetread'), `the background reads every part, the transcript as data: ${JSON.stringify(out)}`);
ok(W.collections['meettx:' + mid].extract.items[0].party === 'Ruth Okafor' && W.collections.meetings[0].review.state === 'new', 'its items are kept with the transcript, and the review moves on to be built');
ok(pushedTo === 'pk-chen', "the meeting's owner is told the review is ready");
const fail = async () => ({status: 529, text: '{}'});
const out2 = await BG.readMeeting('w', mid, 'u_chen', {ask: fail, push: async () => 0});
ok(out2.items === 0 && W.collections.meetings[0].review.read === 'rules' && W.collections['meettx:' + mid].extract === null, 'the model out of reach: the review moves on, read by the rules in the app');
const res = await (await import('../netlify/functions/meetread-background.mjs')).default(new Request('https://x', {method: 'POST', headers: {'x-meet-key': 'wrong'}, body: '{}'}));
ok(res && res.status === 403, 'the background read refuses a call without the server\'s key');
console.log('ALL PASS', `(${n} checks)`);
