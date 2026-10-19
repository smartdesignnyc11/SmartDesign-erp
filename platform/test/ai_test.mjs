// /api/ai: who may call it, the caps, the model the server picks, what is logged. Supabase and Anthropic are mocked.
// Run: node test/ai_test.mjs
import assert from 'node:assert/strict';
const GOOD = 'h.' + Buffer.from(JSON.stringify({session_id: 's1'})).toString('base64url') + '.sig';
Object.assign(process.env, {ANTHROPIC_API_KEY: 'k', SUPABASE_URL: 'https://db', SUPABASE_SERVICE_ROLE_KEY: 's', AI_CAP_FIRM_USD: '40', AI_CAP_USER_USD: '8', AI_MODEL: 'claude-sonnet-5-5'});
const ai = await import('../netlify/functions/ai.mjs');
let world, calls;
const reset = (o = {}) => { world = {role: 'pm', firm: 0, user: 0, ...o}; calls = {anthropic: [], logged: []}; };
globalThis.fetch = async (url, opts = {}) => {
  const u = String(url);
  if (u.endsWith('/auth/v1/user')) return opts.headers.authorization === 'Bearer ' + GOOD ? new Response(JSON.stringify({id: 'u1'})) : new Response('{}', {status: 401});
  if (u.endsWith('/rest/v1/rpc/session_alive_for')) return new Response(JSON.stringify(!globalThis.SESSION_DEAD));
  if (u.includes('/rest/v1/profiles')) return new Response(JSON.stringify([{id: 'u1', role: world.role, workspace_id: 'w'}]));
  if (u.endsWith('/rest/v1/rpc/ai_spend')) return new Response(JSON.stringify({firm: world.firm, user: world.user}));
  if (u.endsWith('/rest/v1/ai_usage')) { calls.logged.push(JSON.parse(opts.body)); return new Response(null, {status: 201}); }
  if (u === 'https://api.anthropic.com/v1/messages') { const b = JSON.parse(opts.body); calls.anthropic.push({b, h: opts.headers}); return new Response(JSON.stringify({model: b.model, content: [{type: 'text', text: 'hi'}], usage: {input_tokens: 1000, output_tokens: 200}})); }
  throw new Error('unexpected fetch ' + u);
};
const req = (body, token = GOOD) => new Request('https://site/api/ai', {method: 'POST', headers: token ? {authorization: 'Bearer ' + token} : {}, body: JSON.stringify(body)});
const body = {model: 'claude-opus-4-1', max_tokens: 99999, temperature: 1, mcp_servers: [{url: 'https://evil'}], thinking: {type: 'enabled', budget_tokens: 5000}, messages: [{role: 'user', content: 'SECRET-PROMPT'}]};
let n = 0; const ok = (c, msg) => { assert.ok(c, msg); n++; };

reset(); let r = await ai.default(req(body, null)); ok(r.status === 401 && !calls.anthropic.length, 'no session: refused, no model call');
reset(); r = await ai.default(req(body, 'bad')); ok(r.status === 401 && !calls.anthropic.length, 'bad session: refused');
for (const role of ['none', 'client', 'mb_user']) { reset({role}); r = await ai.default(req(body)); ok(r.status === 403 && !calls.anthropic.length, role + ': refused'); }
reset({firm: 40}); r = await ai.default(req(body)); ok(r.status === 429 && !calls.anthropic.length && (await r.json()).cap === 'firm', 'firm cap: refused before the call');
reset({user: 8.01}); r = await ai.default(req(body)); ok(r.status === 429 && !calls.anthropic.length, 'person cap: refused before the call');
reset(); r = await ai.default(req(body)); ok(r.status === 200, 'member under cap: answered');
const sent = calls.anthropic[0].b;
ok(sent.model === 'claude-sonnet-5-5', 'the server picks the model, not the page');
ok(sent.max_tokens === 4000, 'max_tokens clamped');
ok(!('temperature' in sent) && !('mcp_servers' in sent) && !('thinking' in sent), 'page-only fields dropped');
ok(sent.fallbacks === 'default' && calls.anthropic[0].h['anthropic-beta'] === 'server-side-fallback-2026-07-01', 'refusal fallback on');
const log = calls.logged[0];
ok(log && log.user_id === 'u1' && log.model === 'claude-sonnet-5-5' && Math.abs(log.cost_usd - (1000 * 2 + 200 * 10) / 1e6) < 1e-9, 'logged with cost');
ok(!JSON.stringify(calls.logged).includes('SECRET-PROMPT') && !JSON.stringify(calls.logged).includes('hi'), 'prompt and answer never logged');
reset({role: 'crew'}); await ai.default(req({...body, tier: 'brain'})); ok(calls.anthropic[0].b.model === 'claude-sonnet-5-5', 'brain tier refused to crew');
reset({role: 'owner'}); await ai.default(req({...body, tier: 'brain'})); ok(calls.anthropic[0].b.model === 'claude-opus-5-5' && calls.anthropic[0].b.max_tokens === 8000, 'brain tier for the owner');
reset(); await ai.default(req({...body, tier: 'small'})); ok(calls.anthropic[0].b.model === 'claude-haiku-5-5' && !calls.anthropic[0].b.fallbacks, 'small tier');
reset(); await ai.default(req({...body, tools: [{type: 'web_search_20250305', name: 'web_search', max_uses: 50}, {type: 'bash_20250124', name: 'bash'}, {name: 'erpQuery', description: 'q', input_schema: {type: 'object'}}]}));
const tools = calls.anthropic[0].b.tools;
ok(tools.length === 2 && tools[0].type === 'web_search_20260209' && tools[0].max_uses === 5 && tools[1].name === 'erpQuery', 'tools allow-listed');
process.env.ANTHROPIC_WORKSPACE_ID = 'wrkspc_x'; reset(); await ai.default(req(body)); ok(calls.anthropic[0].h['anthropic-workspace-id'] === 'wrkspc_x', 'workspace header when set');
reset(); r = await ai.default(new Request('https://site/api/ai', {method: 'GET'})); ok(r.status === 405, 'GET refused');
globalThis.SESSION_DEAD = true; reset(); r = await ai.default(req(body)); ok(r.status === 401 && !calls.anthropic.length, 'a signed-out session is refused even with an unexpired key'); globalThis.SESSION_DEAD = false;
console.log('ALL PASS', `(${n} checks)`);
