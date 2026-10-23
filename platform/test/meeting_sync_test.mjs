// Two people in the team meeting at once (docs/TASKS_PLAN.md Phase 1 item 4, "several people at once"): what the
// hosted copy's merge (public/cloud.js merge3) keeps when two sessions edit tasks and log to the same meeting record
// at the same moment. Run: node test/meeting_sync_test.mjs. Invented data only.
import fs from 'node:fs'; import vm from 'node:vm'; import assert from 'node:assert/strict';
const src = fs.readFileSync(new URL('../public/cloud.js', import.meta.url), 'utf8');
const ctx = {window: {fetch: async () => {}, SDP_CONFIG: {}}, navigator: {onLine: true}, location: {href: 'https://x/', origin: 'https://x'}, URL, Headers, localStorage: {getItem: () => null, setItem() {}, removeItem() {}}, document: {addEventListener() {}}, console};
ctx.window.window = ctx.window; vm.createContext(ctx); vm.runInContext(src, ctx);
const {merge3} = ctx.window.Cloud;
const clone = (x) => JSON.parse(JSON.stringify(x));
const m3 = (b, l, s) => { const conf = {n: 0}; return [clone(merge3(b, l, s, conf)), conf.n]; };
let n = 0; const ok = (c, msg) => { assert.ok(c, msg); n++; };

// the shared rows: one job (its own row, project:p1) and the meetings collection
const project = {id: 'p1', project: {name: 'Invented Duplex', prefix: 'IND', keyNext: 3}, actions: [
  {id: 'a1', code: 'IND-1', title: 'Order the vanity', assignee: 'Chen Biron', due: '2026-10-27', status: 'todo', thread: [{id: 'a1_n', at: '2026-10-20', by: 'Chen Biron', text: 'Sample approved'}]},
  {id: 'a2', code: 'IND-2', title: 'Confirm the tile ETA', assignee: 'Alan', due: '2026-10-28', status: 'todo', thread: []},
]};
const meetings = [{id: 'mt1', kind: 'team', title: 'Team Meeting', startedAt: '2026-10-26T10:00:00', endedAt: '', changes: [], screenLog: [], created: [], decisions: []}];

// 1. two sessions edit different tasks at the same time: both edits stay, no conflict
{
  const A = clone(project), B = clone(project);
  A.actions[0].due = '2026-10-29'; A.actions[0].thread.push({id: 'cA', at: '2026-10-26T10:03:00', by: 'Owner', text: 'Vendor promised Thursday'});
  B.actions[1].status = 'waiting'; B.actions[1].waitingOn = {name: 'Tile supplier', what: 'ETA', promised: '2026-10-29', evidence: 'call'}; B.actions[1].waitsOn = 'Tile supplier';
  const [out, conf] = m3(project, A, B);
  ok(conf === 0, 'different tasks: no conflict');
  ok(out.actions[0].due === '2026-10-29' && out.actions[0].thread.length === 2, 'different tasks: the date and the comment on IND-1 kept');
  ok(out.actions[1].status === 'waiting' && out.actions[1].waitingOn.name === 'Tile supplier', 'different tasks: Waiting On on IND-2 kept');
}
// 2. both comment on the same task at once: each comment has an id, so both are kept
{
  const A = clone(project), B = clone(project);
  A.actions[0].thread.push({id: 'cA', at: '2026-10-26T10:03:00', by: 'Owner', text: 'From the owner'});
  B.actions[0].thread.push({id: 'cB', at: '2026-10-26T10:03:05', by: 'Chen Biron', text: 'From the coordinator'});
  const [out, conf] = m3(project, A, B);
  ok(conf === 0 && out.actions[0].thread.length === 3, 'same task: both comments kept');
}
// 2b. without ids (how a thread was written before this round) one comment was lost: the reason for the ids
{
  const P = clone(project); P.actions[0].thread = [{at: '2026-10-20', by: 'Chen Biron', text: 'Sample approved'}];
  const A = clone(P), B = clone(P);
  A.actions[0].thread.push({at: '1', by: 'Owner', text: 'A'}); B.actions[0].thread.push({at: '2', by: 'Chen Biron', text: 'B'});
  const [out, conf] = m3(P, A, B);
  ok(conf === 1 && out.actions[0].thread.length === 2, 'without ids: one comment lost (the server copy stands)');
}
// 3. both log to the same meeting at once: changes and screen-log lines carry ids, so both are kept
{
  const A = clone(meetings), B = clone(meetings);
  A[0].changes.push({id: 'mcA', taskKey: 'IND-1', field: 'due', from: '2026-10-27', to: '2026-10-29', by: 'Owner', at: '2026-10-26T10:03:00'});
  A[0].screenLog.push({id: 'msA', taskKey: 'IND-1', from: '2026-10-26T10:02:00', to: ''});
  B[0].changes.push({id: 'mcB', taskKey: 'IND-2', field: 'waitingOn', from: '', to: 'Tile supplier', by: 'Chen Biron', at: '2026-10-26T10:03:02'});
  const [out, conf] = m3(meetings, A, B);
  ok(conf === 0, 'same meeting: no conflict');
  ok(out[0].changes.length === 2 && out[0].screenLog.length === 1, 'same meeting: both changes and the screen line kept');
}
// 4. both add a task to the same project at once: the two tasks are kept; their plain-key list (created) keeps only
// one device's, which is why the app rebuilds created from the changes, and both may say IND-3, which the app's
// sweep puts right (the later one moves to IND-4) after the merge
{
  const PA = clone(project), PB = clone(project), MA = clone(meetings), MB = clone(meetings);
  PA.actions.push({id: 'a3', code: 'IND-3', title: 'Book the plumber', assignee: 'Alan', createdAt: '2026-10-26', status: 'todo'}); PA.project.keyNext = 4;
  PB.actions.push({id: 'a4', code: 'IND-3', title: 'Send the client the tile options', assignee: 'Chen Biron', createdAt: '2026-10-26', status: 'todo'}); PB.project.keyNext = 4;
  MA[0].created.push('IND-3'); MA[0].changes.push({id: 'mcA', taskKey: 'IND-3', ref: 'action:a3:p1', field: 'created'});
  MB[0].created.push('IND-3'); MB[0].changes.push({id: 'mcB', taskKey: 'IND-3', ref: 'action:a4:p1', field: 'created'});
  const [P, c1] = m3(project, PA, PB), [M, c2] = m3(meetings, MA, MB);
  ok(c1 === 0 && P.actions.length === 4, 'two new tasks: both kept');
  ok(P.actions.filter((a) => a.code === 'IND-3').length === 2, 'two new tasks: both say IND-3 until the sweep runs');
  ok(M[0].changes.filter((c) => c.field === 'created').length === 2, 'two new tasks: both created lines kept, each with its record');
  ok(new Set(M[0].changes.map((c) => c.ref)).size === 2, 'two new tasks: the lines point at two records, so the minutes name both');
  void c2;
}
// 5. the same field on the same task from both sessions: the server's value stands and the merge says so
{
  const A = clone(project), B = clone(project);
  A.actions[0].due = '2026-10-29'; B.actions[0].due = '2026-10-30';
  const [out, conf] = m3(project, A, B);
  ok(conf === 1 && out.actions[0].due === '2026-10-30', 'same field: one value stands, counted as a conflict');
}
console.log('ALL PASS', `(${n} checks)`);
