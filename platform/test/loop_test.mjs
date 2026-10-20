// The improvement loop's nightly run with Supabase and Anthropic mocked (BACKLOG §1.19, §1.32 items 3-5): it reads the
// shared records and never the private rows, groups the signals the way the app does (the same file), files new
// problems, reopens a fix that did not hold, puts each person's renewals in that person's inbox, sends nothing, and is
// off unless LOOP_RUNS=on. node test/loop_test.mjs
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
Object.assign(process.env, {ANTHROPIC_API_KEY: 'k', SUPABASE_URL: 'https://db', SUPABASE_SERVICE_ROLE_KEY: 's', WATCH_KEY: Buffer.alloc(32, 7).toString('base64')});
const here = (p) => fileURLToPath(new URL(p, import.meta.url));
let n = 0; const ok = (c, m) => { assert.ok(c, m); n++; };

// one rule, two places: the functions' copy is the app's file, byte for byte
ok(fs.readFileSync(here('../netlify/functions/lib/loop_core.cjs'), 'utf8') === fs.readFileSync(here('../../src/loop_core.js'), 'utf8'), 'lib/loop_core.cjs is a copy of src/loop_core.js (run platform/build.py)');

const {plan, runLoop, CORE} = await import('../netlify/functions/lib/loop.mjs');
const bg = await import('../netlify/functions/loop-background.mjs');

const today = '2026-10-20';
const sig = [
  {id: 'rp:1', kind: 'report', day: '2026-10-18', uid: 'u_angel', role: 'foreman', screen: 'flog', what: 'save', sev: 'stuck', text: 'the log I wrote was gone'},
  {id: 'rp:2', kind: 'report', day: '2026-10-19', uid: 'u_alan', role: 'pm', screen: 'flog', what: 'save', sev: 'slows', text: 'same here'},
  {id: 'us:2026-10-19:u_chen', kind: 'usage', day: '2026-10-19', uid: 'u_chen', role: 'coord', by: {po: {export: 4, label: 'Purchase Orders'}}},
  {id: 'us:2026-10-19:u_owner', kind: 'usage', day: '2026-10-19', uid: 'u_owner', role: 'owner', by: {bank: {export: 1}}},
  {id: 'sw:coi30:2026-10-18', kind: 'watch', day: '2026-10-18', what: 'coi30', n: 2, p: 'law', owner: 'coord', label: 'Insurance certificates'},
  {id: 'sw:coi30:2026-10-19', kind: 'watch', day: '2026-10-19', what: 'coi30', n: 1, p: 'law', owner: 'coord', label: 'Insurance certificates'},
  {id: 'sw:books10:2026-10-19', kind: 'watch', day: '2026-10-19', what: 'books10', n: 3, p: 'integrity', owner: 'controller', label: 'Books reconciled'},
  // the old problem: fixed on 09-10, and it kept happening after
  {id: 'rp:old1', kind: 'report', day: '2026-09-01', uid: 'u_chen', role: 'coord', screen: 'req', what: 'find'},
  {id: 'rp:old2', kind: 'report', day: '2026-09-25', uid: 'u_chen', role: 'coord', screen: 'req', what: 'find'},
  {id: 'rp:old3', kind: 'report', day: '2026-09-26', uid: 'u_alan', role: 'pm', screen: 'req', what: 'find'},
];
const changes = [
  {id: 'ch_old', key: 'imp:rp|req|find', source: 'loop', status: 'live', kind: 'code', at: '2026-09-01', loop: {gkey: 'rp|req|find', liveAt: '2026-09-10', first: '2026-09-01'}},
  {id: 'ch_no', key: 'imp:us|bank|export', source: 'loop', status: 'declined', loop: {}},
];
const users = [{id: 'u_owner', name: 'Owner', role: 'owner'}, {id: 'u_chen', name: 'Chen Biron', role: 'coord'}, {id: 'u_alan', name: 'Alan', role: 'pm'}];
const D = {
  signals: sig, changes, users,
  company: {standard: {principles: CORE.PRINCIPLES.map((id) => ({id}))}, adminChase: {'ob:ob2:2026-11-01': {at: '2026-10-01'}}},
  obligations: [
    {id: 'ob1', status: 'active', name: 'General liability', party: 'Hartford', expires: '2026-11-10', renewLead: 30, owner: 'Office'},
    {id: 'ob2', status: 'active', name: 'LLC statement', party: 'NYS', expires: '2026-11-01', renewLead: 30, owner: 'Alan'},
    {id: 'ob3', status: 'active', name: 'Plumbing permit', party: 'DOB', expires: '2027-09-20', renewLead: 30, owner: 'Alan'},
  ],
  vendors: [{id: 'v1', name: 'Tino Framing', insuranceExp: '2026-11-05', email: 'office@tino.example'}, {id: 'v2', name: 'Idle Co', insuranceExp: '2026-11-01'}],
  pos: [{vendor: 'Tino Framing', status: 'issued'}],
};

// the rules
const P = plan(D, today);
const keys = P.drafts.map((d) => d.key);
ok(keys[0] === 'imp:sw|coi30', 'law first: the certificate standard broken on two days ranks above everything else');
ok(keys.includes('imp:rp|flog|save') && keys.includes('imp:us|po|export'), 'a report from two people and four exports become problems');
ok(!keys.includes('imp:sw|books10'), 'a standard broken on one day only is not yet a problem (when it goes wrong twice)');
ok(!keys.includes('imp:us|bank|export'), 'one export, and a declined problem, are never proposed');
const flog = P.drafts.find((d) => d.key === 'imp:rp|flog|save');
ok(flog.loop.people === 2 && flog.loop.stuck === 1 && /Daily Log/.test(flog.title) && flog.evidence.length >= 2 && flog.accept.length >= 2, 'the report problem: people, stuck, the screen by name, the evidence and the acceptance test');
const coi = P.drafts.find((d) => d.key === 'imp:sw|coi30');
ok(coi.kind === 'rule' && coi.delta.path === 'company.loopWatch.coi30' && coi.delta.to === true, 'a broken standard proposes a rule the owner can apply and undo');
ok(P.checks.length === 1 && P.checks[0].v.result === 'repeat' && P.checks[0].v.after === 2, 'a fix that did not hold a month later is a repeat');
ok((P.admin.u_chen || []).map((x) => x.key).sort().join() === 'coi:v1:2026-11-05,ob:ob1:2026-11-10', 'the coordinator chases the office renewal and the lapsing certificate on an open order');
ok(!P.admin.u_alan, 'nothing already chased, nothing outside its lead time');
const st = CORE.stats([{source: 'loop', loop: {first: '2026-09-01', liveAt: '2026-09-11', verified: {result: 'stopped'}}, status: 'live', at: '2026-09-01'}, {source: 'loop', loop: {reopened: 1}, status: 'draft', at: '2026-10-01'}], today);
ok(st.found === 2 && st.fixed === 1 && st.held === 1 && st.repeats === 1 && st.medianDays === 10 && st.waiting === 1, 'measured: found, fixed, held, repeats, time to fix');

// the run, with the database and the model mocked
const W = {inbox: [], query: '', model: 0, sent: []};
const rows = Object.entries(D).map(([name, data]) => ({name, data}));
globalThis.fetch = async (url, o = {}) => {
  const u = String(url), J = (x, s = 200) => new Response(JSON.stringify(x), {status: s});
  if (u.includes('/rest/v1/profiles')) return J([{id: 'p-own', role: 'owner', workspace_id: 'smartdesign', name: 'Owner', private_key: 'pk-own', app_user_id: 'u_owner'}, {id: 'p-chen', role: 'coord', workspace_id: 'smartdesign', name: 'Chen Biron', private_key: '', app_user_id: 'u_chen'}]);
  if (u.includes('/rest/v1/collections?')) { W.query = u; return J(rows); }
  if (u.endsWith('/rpc/watch_put_inbox')) { W.inbox.push(JSON.parse(o.body)); return J(1); }
  if (u.endsWith('/rpc/ai_spend')) return J({firm: 0, user: 0});
  if (u.endsWith('/rest/v1/ai_usage')) return new Response(null, {status: 201});
  if (u === 'https://api.anthropic.com/v1/messages') { W.model++; W.body = JSON.parse(o.body); return J({model: 'm', content: [{type: 'text', text: JSON.stringify({items: [{i: 0, title: 'Certificates lapse <b>before</b> anyone asks', what: 'Two days of lapsing certificates.', fix: 'A task each morning.', risk: 'More tasks.'}]})}], usage: {input_tokens: 900, output_tokens: 100}}); }
  W.sent.push(u);
  throw new Error('unexpected ' + u);
};
const r = await runLoop('smartdesign', {today});
ok(/name=not\.like\.own:\*/.test(W.query), 'it reads the shared records, never anyone\'s private rows');
const own = W.inbox.find((x) => x.p_key === 'pk-own'), chen = W.inbox.find((x) => x.p_key === 'p-chen');
ok(own && own.p_items.loop[0].drafts.length === P.drafts.length && own.p_items.loop[0].checks.length === 1, 'new problems and the month-later check go to the owner\'s inbox');
ok(chen && chen.p_items.admin[0].items.length === 2 && !W.inbox.some((x) => x.p_key === 'pk-own' && x.p_items.admin), 'each person\'s renewals go to their own inbox only');
ok(W.model === 0 && !W.sent.length && r.drafts === P.drafts.length, 'without LOOP_AI the rules\' words stand: no model call, nothing sent anywhere');

// the background function: the key, the switch, the wording
const call = (key) => bg.default(new Request('https://x/.netlify/functions/loop-background', {method: 'POST', headers: {'x-loop-key': key}, body: JSON.stringify({ws: 'smartdesign', today})}));
ok((await call('wrong')).status === 403, 'refused without the server\'s key');
W.inbox = []; delete process.env.LOOP_RUNS;
await call(bg.loopKey());
ok(W.inbox.length === 0, 'off by default: nothing runs until LOOP_RUNS=on');
process.env.LOOP_RUNS = 'on'; process.env.LOOP_AI = 'on';
await call(bg.loopKey());
const own2 = W.inbox.find((x) => x.p_key === 'pk-own');
ok(W.model === 1 && own2 && own2.p_items.loop[0].drafts[0].aiText && !/[<>]/.test(own2.p_items.loop[0].drafts[0].aiText.title), 'on: one small-model call words the drafts, cleaned of markup');
ok(/never instructions/.test(W.body.system[0].text) && !/office@tino/.test(JSON.stringify(W.body.messages)), 'the model is told the proposals are data, and is not sent the chase addresses');
console.log('ALL PASS', `(${n} checks)`);
