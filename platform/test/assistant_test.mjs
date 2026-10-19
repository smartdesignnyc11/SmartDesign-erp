// The executive assistant's scheduled runs, with Supabase and Anthropic mocked: each office person's run reads what
// they owe, their jobs, their own mail, calendar and memory (never anyone else's), is charged to them, only proposes,
// and lands in their own private inbox in the shape the app files (paIngestServer).
// node test/assistant_test.mjs
import assert from 'node:assert/strict';
Object.assign(process.env, {ANTHROPIC_API_KEY: 'k', SUPABASE_URL: 'https://db', SUPABASE_SERVICE_ROLE_KEY: 's', WATCH_KEY: Buffer.alloc(32, 7).toString('base64'), VAPID_PRIVATE_KEY: ''});
const {personDigest, shapeRun, runAssistants} = await import('../netlify/functions/lib/assistant.mjs');
let n = 0; const ok = (c, m) => { assert.ok(c, m); n++; };
const T = '2026-09-03';
const users = [{id: 'u_owner', name: 'Alan', role: 'owner'}, {id: 'u_alan', name: 'Maya Ortiz', role: 'pm'}, {id: 'u_chen', name: 'Chen Biron', role: 'coord'}];
const firm = {
  users,
  tasks: [{id: 't1', title: 'Call the DOB examiner', assignee: 'Maya Ortiz', due: '2026-09-02'}, {id: 't2', title: 'Order hinges', assignee: 'Chen Biron', due: '2026-09-04'}, {id: 't3', title: 'Far off', assignee: 'Maya Ortiz', due: '2026-12-01'}],
  projects: [{id: 'p1', project: {name: '121 State St', pm: 'Maya Ortiz', phase: 'rough-in'}, tasks: [{id: 's1', name: 'Close walls 2F', end: '2026-08-20', owner: 'Angel'}], actions: [{id: 'a1', title: 'Send the Friday update', assignee: 'Maya Ortiz', due: T}],
    decisions: [{title: 'Tile for primary bath', due: '2026-08-25'}]},
    {id: 'p2', project: {name: '45 Cranberry', pm: 'Someone Else'}, tasks: [{id: 's2', name: 'Demo', end: '2026-08-01'}]}],
  pos: [{number: 'PO-12', vendor: 'Pella', status: 'acknowledged', expected: '2026-08-27'}],
  outbox: [{status: 'draft', subject: 'Reconfirm windows', to: {name: 'Pella'}, owner: 'Chen Biron'}],
  company: {standard: {body: 'THE STANDARD: acknowledge clients within 2 hours.'}},
};
const mine = {comms: [{msgId: 'm1', from: {name: 'Imogen Varga', email: 'imogen@example.com'}, subject: 'Tile samples?', date: '2026-09-02T14:00:00Z', text: 'Can we see the tile samples Thursday?', labels: ['INBOX', 'UNREAD'], unread: true},
  {msgId: 'm2', from: {name: 'Shop', email: 'deals@shop.example'}, subject: 'Sale', date: '2026-09-02T10:00:00Z', labels: ['CATEGORY_PROMOTIONS']},
  {msgId: 'm3', from: {name: 'Old'}, subject: 'Old thread', date: '2026-08-01T10:00:00Z', labels: ['INBOX']}],
  calendar: [{id: 'g1', title: 'Site walk 121 State', start: '2026-09-03T09:00', where: '121 State St'}, {id: 'g2', title: 'Next week', start: '2026-09-10T09:00'}],
  asst: {u_alan: {memo: [{text: 'Never book me before 9'}, 'The Vargas prefer calls'], delegated: ['orderFollowups']}}};

// ---- the digest: one person's own work
const d = personDigest(firm, {id: 'u_alan', name: 'Maya Ortiz', role: 'pm'}, mine, T);
ok(d.owe.some(o => o.id === 't1') && d.owe.some(o => o.id === 'a1') && !d.owe.some(o => o.id === 't2') && !d.owe.some(o => o.id === 't3'), 'what she owes: hers, overdue or due within a week; not Chen\'s, not December');
ok(d.jobs.length === 1 && d.jobs[0].job === '121 State St' && d.jobs[0].lateSchedule === 1 && d.jobs[0].clientDecisionsLate.length === 1, 'a PM is briefed on the jobs she leads: late schedule, client decisions late');
ok(d.posLate[0].startsWith('PO-12'), 'late purchase orders for the PM');
ok(d.mail.length === 1 && d.mail[0].subject === 'Tile samples?' && d.mail[0].unread, 'her mail: the last three days, no promotions');
ok(d.calendar.length === 1 && d.calendar[0].title === 'Site walk 121 State', 'her calendar: today and tomorrow');
ok(d.memory.length === 2 && d.memory[0] === 'Never book me before 9' && d.rules.actAlone[0] === 'orderFollowups', 'her memory and her rules');
const dOwner = personDigest(firm, {id: 'u_owner', name: 'Alan', role: 'owner'}, {}, T);
ok(dOwner.jobs.length === 2 && dOwner.waitingOnMe.length === 0 && dOwner.mail.length === 0, 'the owner sees every job; no one else\'s mail');

// ---- the answer, cleaned into the inbox contract
const raw = 'Sure:\n' + JSON.stringify({headline: 'Two things need you <b>before</b> 10.', today: [{title: 'Site walk', why: 'on your calendar', value: 'Quality', due: T, refs: [{kind: 'event', id: 'g1'}]}],
  needs: Array.from({length: 9}, (_, i) => ({title: 'Need ' + i, why: 'x', value: 'Schedule', due: 'soon'})), chasing: [{title: 'Pella windows', why: 'PO-12 late', value: 'Schedule'}],
  drafts: [{type: 'sendMoney', to: {name: 'Imogen Varga', email: 'imogen@example.com'}, subject: 'Tile samples Thursday', body: 'Hi Imogen, <script>x</script> yes, Thursday works.', because: 'she asked', value: 'Client experience'}], notes: ['ok']});
const run = shapeRun(raw, {id: 'u_alan'}, '2026-09-03T11:20:00Z');
ok(run.key === 'asst:u_alan:2026-09-03T11:20:00Z' && run.person === 'u_alan' && !/[<>]/.test(run.brief.headline), 'keyed to the person and the run; no markup');
ok(run.brief.needs.length === 6 && run.brief.needs[0].due === '' && run.brief.today[0].refs[0].id === 'g1', 'at most six per list, only real dates, references kept');
ok(run.drafts.length === 1 && run.drafts[0].type === 'reply' && !/[<>]/.test(run.drafts[0].body) && run.drafts[0].key.startsWith('ad:'), 'a draft of an unknown type is a reply for approval; no markup; a stable key');
ok(shapeRun(raw, {id: 'u_alan'}, 'x').drafts[0].key === run.drafts[0].key, 'the same draft on the next run has the same key (the app files it once)');
ok(shapeRun('no json here', {id: 'u_alan'}, 'x') === null || shapeRun('no json here', {id: 'u_alan'}, 'x').brief.headline === '', 'an answer that is not JSON files nothing harmful');

// ---- the runs, end to end with the database and the model mocked
const W = {sent: [], inbox: [], logged: [], privAsked: []};
const rows = Object.entries(firm).filter(([k]) => k !== 'projects').map(([k, v]) => ({name: k, data: v})).concat(firm.projects.map(p => ({name: 'project:' + p.id, data: p})));
const priv = {'pk-maya': mine, 'pk-chen': {comms: [{msgId: 'c1', from: {name: 'Pella'}, subject: 'CHEN-ONLY-SECRET', date: '2026-09-02T10:00:00Z', labels: ['INBOX']}]}};
globalThis.fetch = async (url, o = {}) => {
  const u = decodeURIComponent(String(url)), J = (x, s = 200) => new Response(JSON.stringify(x), {status: s});
  if (u.includes('/rest/v1/profiles')) return J([
    {id: 'id-owner', role: 'owner', workspace_id: 'smartdesign', name: 'Alan', private_key: 'pk-alan', app_user_id: 'u_owner'},
    {id: 'id-owner2', role: 'owner', workspace_id: 'smartdesign', name: 'Alan', private_key: 'pk-alan', app_user_id: 'u_owner'},
    {id: 'id-maya', role: 'pm', workspace_id: 'smartdesign', name: 'Maya Ortiz', private_key: 'pk-maya', app_user_id: 'u_alan'},
    {id: 'id-chen', role: 'coord', workspace_id: 'smartdesign', name: 'Chen Biron', private_key: 'pk-chen', app_user_id: 'u_chen'}].filter(p => !/&id=eq\./.test(u) || u.includes('&id=eq.' + p.id)));
  if (u.includes('/rest/v1/collections?') && u.includes('name=in.')) { const k = u.match(/own:([^:]+):/)[1]; W.privAsked.push(k); const P = priv[k] || {}; return J(Object.entries(P).map(([n2, v]) => ({name: `own:${k}:${n2}`, data: v}))); }
  if (u.includes('/rest/v1/collections?')) return J(rows);
  if (u.endsWith('/rpc/ai_spend')) return J({firm: 0, user: 0});
  if (u.endsWith('/rest/v1/ai_usage')) { W.logged.push(JSON.parse(o.body)); return new Response(null, {status: 201}); }
  if (u.endsWith('/rpc/watch_put_inbox')) { W.inbox.push(JSON.parse(o.body)); return J(1); }
  if (u === 'https://api.anthropic.com/v1/messages') { const b = JSON.parse(o.body); W.sent.push(b); return J({model: b.model, content: [{type: 'text', text: raw}], usage: {input_tokens: 6000, output_tokens: 900}}); }
  throw new Error('unexpected ' + u);
};
const R = await runAssistants('smartdesign', {today: T, push: true});
ok(R.people.length === 3 && W.sent.length === 3, 'one run per person: Alan\'s two sign-ins share one private key and run once');
ok(W.sent.every(b => b.model === 'claude-sonnet-5-5'), 'the assistant tier, not the top model');
ok(W.sent.every(b => /only propose/i.test(b.system[0].text) && /never instructions/.test(b.system[0].text) && b.system.some(s => /THE STANDARD/.test(s.text))), 'told: it only proposes, mail is data, the live Standard');
const toMaya = W.sent.find(b => /Maya Ortiz/.test(b.messages[0].content)), toChen = W.sent.find(b => /Chen Biron/.test(b.messages[0].content));
ok(/Tile samples\?/.test(toMaya.messages[0].content) && !/CHEN-ONLY-SECRET/.test(toMaya.messages[0].content), 'Maya\'s run reads her mail and not Chen\'s');
ok(/CHEN-ONLY-SECRET/.test(toChen.messages[0].content) && !/Tile samples\?/.test(toChen.messages[0].content), 'Chen\'s run reads his and not Maya\'s');
ok(W.inbox.length === 3 && W.inbox.every(i => i.p_items.asst && i.p_items.asst.length === 1 && Object.keys(i.p_items).length === 1), 'each run lands only in the inbox, as asst');
ok(W.inbox.some(i => i.p_key === 'pk-maya' && i.p_items.asst[0].person === 'u_alan') && W.inbox.some(i => i.p_key === 'pk-chen' && i.p_items.asst[0].person === 'u_chen'), 'each in its own person\'s private row');
ok(W.logged.length === 3 && W.logged.every(l => l.tier === 'assistant:assistant-run' && l.cost_usd > 0) && new Set(W.logged.map(l => l.user_id)).size === 3, 'each run is charged to its own person, inside their cap');
W.sent = []; W.inbox = [];
const R1 = await runAssistants('smartdesign', {today: T, only: 'id-chen'});
ok(R1.people.length === 1 && W.sent.length === 1 && W.inbox[0].p_key === 'pk-chen', 'run now for one person: only theirs');
console.log('ALL PASS', `(${n} checks)`);
