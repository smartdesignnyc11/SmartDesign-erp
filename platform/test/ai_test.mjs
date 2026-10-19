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
  if (u === 'https://api.anthropic.com/v1/messages') {
    const b = JSON.parse(opts.body); calls.anthropic.push({b, h: opts.headers});
    if (!b.stream) return new Response(JSON.stringify({model: b.model, content: [{type: 'text', text: 'hi'}], usage: {input_tokens: 1000, output_tokens: 200}}));
    const ev = [{type: 'message_start', message: {id: 'm1', type: 'message', role: 'assistant', model: b.model, content: [], usage: {input_tokens: 1000, output_tokens: 1}}},
      {type: 'content_block_start', index: 0, content_block: {type: 'text', text: ''}}, {type: 'content_block_delta', index: 0, delta: {type: 'text_delta', text: 'h'}},
      {type: 'content_block_delta', index: 0, delta: {type: 'text_delta', text: 'i'}}, {type: 'content_block_stop', index: 0},
      {type: 'content_block_start', index: 1, content_block: {type: 'tool_use', id: 't1', name: 'erpQuery', input: {}}},
      {type: 'content_block_delta', index: 1, delta: {type: 'input_json_delta', partial_json: '{"table":"inv'}}, {type: 'content_block_delta', index: 1, delta: {type: 'input_json_delta', partial_json: 'oices"}'}},
      {type: 'content_block_stop', index: 1}, {type: 'message_delta', delta: {stop_reason: 'tool_use'}, usage: {output_tokens: 200}}, {type: 'message_stop'}];
    const sse = ev.map(e => `event: ${e.type}\ndata: ${JSON.stringify(e)}\n\n`).join('');
    return new Response(new ReadableStream({start(c) { const enc = new TextEncoder(); for (let i = 0; i < sse.length; i += 37) c.enqueue(enc.encode(sse.slice(i, i + 37))); c.close(); }}), {status: 200, headers: {'content-type': 'text/event-stream'}});
  }
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
reset(); r = await ai.default(req(body)); const txt = await r.text(); const msg = JSON.parse(txt);
ok(r.status === 200, 'member under cap: answered');
ok(msg.content[0].text === 'hi' && msg.content[1].input.table === 'invoices' && msg.stop_reason === 'tool_use' && msg.usage.output_tokens === 200, 'the streamed answer is rebuilt whole: text, a tool call with its input, the stop reason, usage');
ok(calls.anthropic[0].b.stream === true, 'the door asks Anthropic for a stream');
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
reset(); r = await ai.default(req({...body, stream: 'client'})); const sse = await r.text();
ok(r.headers.get('content-type') === 'text/event-stream' && /event: message_start/.test(sse) && /input_json_delta/.test(sse), 'stream to the page: Anthropic events pass through');
const done = JSON.parse(sse.split('event: sd_done')[1].split('data: ')[1]);
ok(done.cut === false && done.usage.output_tokens === 200 && calls.logged.some(l => l.output_tokens === 200 && l.cost_usd > 0), 'and it ends with sd_done, the usage logged');
ok(!('stream' in calls.anthropic[0].b) || calls.anthropic[0].b.stream === true, 'the page\'s stream flag is not passed on as is');
process.env.AI_CAP_ROLE_USD = '{"owner":40,"pm":25}';
reset({role: 'owner', user: 30}); r = await ai.default(req(body)); ok(r.status === 200, 'the owner under the owner\'s role cap ($30 of $40) is answered');
reset({role: 'pm', user: 26}); r = await ai.default(req(body)); ok(r.status === 429 && !calls.anthropic.length, 'a PM over the PM cap ($26 of $25) is refused');
reset({role: 'coord', user: 8.5}); r = await ai.default(req(body)); ok(r.status === 429, 'a role the map does not name keeps AI_CAP_USER_USD ($8)');
process.env.AI_CAP_ROLE_USD = 'not json'; reset({role: 'owner', user: 8.5}); r = await ai.default(req(body)); ok(r.status === 429, 'a broken role map falls back to the person cap');
delete process.env.AI_CAP_ROLE_USD;
console.log('ALL PASS', `(${n} checks)`);
