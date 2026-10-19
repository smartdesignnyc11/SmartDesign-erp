// /api/ai: the app's only door to Claude. The Anthropic key stays on the server.
// - Only a signed-in member of the firm may call it (lib/auth.mjs).
// - The server picks the model by tier (AI_MODEL, AI_MODEL_BRAIN, AI_MODEL_SMALL); a model named by the page is ignored.
// - Spend is checked before every call against a per-person and a per-firm monthly cap (AI_CAP_USER_USD, AI_CAP_FIRM_USD),
//   and every call is logged to ai_usage with its tokens and cost. The prompt and the answer are never stored.
// - Only plain fields pass through: no MCP servers from the page, no sampling settings the current models refuse.
import {caller, json, rest} from './lib/auth.mjs';

// Dollars per million tokens: [input, output]. Cache writes cost 1.25x input, cache reads 0.1x input.
export const PRICES = {
  'claude-opus-5-5': [4, 20], 'claude-sonnet-5-5': [2, 10], 'claude-haiku-5-5': [0.10, 0.50],
  'claude-fable-5-1': [10, 50], 'claude-opus-5': [5, 25], 'claude-sonnet-5': [2, 10],
};
const WEB_SEARCH_USD = 0.01;                       // per search
const FALLBACK_OK = new Set(['claude-opus-5-5', 'claude-sonnet-5-5', 'claude-opus-5', 'claude-fable-5-1']);
const BRAIN_ROLES = ['owner', 'pm', 'controller'];
const EFFORTS = new Set(['low', 'medium', 'high']);

export function modelFor(tier, role, env = process.env) {
  if (tier === 'brain' && BRAIN_ROLES.includes(role)) return env.AI_MODEL_BRAIN || 'claude-opus-5-5';
  if (tier === 'small') return env.AI_MODEL_SMALL || 'claude-haiku-5-5';
  return env.AI_MODEL || 'claude-sonnet-5-5';
}

export function costOf(model, usage = {}) {
  const [pin, pout] = PRICES[model] || PRICES['claude-opus-5-5'];
  const m = 1e6;
  return (usage.input_tokens || 0) * pin / m + (usage.output_tokens || 0) * pout / m
    + (usage.cache_creation_input_tokens || 0) * pin * 1.25 / m + (usage.cache_read_input_tokens || 0) * pin * 0.1 / m
    + ((usage.server_tool_use && usage.server_tool_use.web_search_requests) || 0) * WEB_SEARCH_USD;
}

// The request the server sends, built from an allow-list of what the page may set.
export function cleanBody(body, model, tier) {
  const out = {model, messages: body.messages};
  out.max_tokens = Math.max(1, Math.min(Number(body.max_tokens) || 1000, tier === 'brain' ? 8000 : 4000));
  if (body.system) out.system = body.system;
  if (Array.isArray(body.stop_sequences)) out.stop_sequences = body.stop_sequences.slice(0, 4);
  if (Array.isArray(body.tools)) {
    out.tools = body.tools.filter(t => t && (t.input_schema || (typeof t.type === 'string' && t.type.startsWith('web_search'))))
      .map(t => t.input_schema ? {name: t.name, description: t.description, input_schema: t.input_schema}
                               : {type: 'web_search_20260209', name: 'web_search', max_uses: Math.min(Number(t.max_uses) || 3, 5)});
    if (!out.tools.length) delete out.tools;
  }
  if (body.tool_choice && ['auto', 'none'].includes(body.tool_choice.type)) out.tool_choice = {type: body.tool_choice.type};
  const effort = body.output_config && body.output_config.effort;
  out.output_config = {effort: EFFORTS.has(effort) ? effort : (tier === 'small' ? 'low' : 'medium')};
  out.cache_control = {type: 'ephemeral'};           // the Standard and long system prompts repeat; cache them
  return out;
}

// A person's monthly cap: by role when AI_CAP_ROLE_USD names it (JSON, e.g. {"owner":40,"pm":25}), else
// AI_CAP_USER_USD. The executive assistant runs for each person on a schedule, so the owner's and the PMs' need more.
export function capFor(role) {
  try { const m = JSON.parse(process.env.AI_CAP_ROLE_USD || '{}'); if (m && Number.isFinite(+m[role]) && +m[role] > 0) return +m[role]; } catch {}
  return Number(process.env.AI_CAP_USER_USD || 8);
}
// One call to Claude for a signed-in member: caps checked before, the model by tier, cost logged after.
// The AI door below and the document reader (doctext.mjs) both go through it, so neither can skip the caps.
async function prepare(user, profile, body) {
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) return {status: 500, text: JSON.stringify({error: 'ANTHROPIC_API_KEY is not set on the server'})};
  const capFirm = Number(process.env.AI_CAP_FIRM_USD || 40), capUser = capFor(profile.role);
  let spend;
  try { spend = await rest('rpc/ai_spend', {method: 'POST', body: JSON.stringify({p_ws: profile.workspace_id, p_user: user.id})}); }
  catch (e) { return {status: 503, text: JSON.stringify({error: 'could not check this month\'s AI spend, so the call was not made'})}; }
  if (spend.firm >= capFirm) return {status: 429, text: JSON.stringify({error: `The firm's AI budget for this month ($${capFirm}) is used up. The owner can raise it in Netlify (AI_CAP_FIRM_USD).`, cap: 'firm'})};
  if (spend.user >= capUser) return {status: 429, text: JSON.stringify({error: `Your AI budget for this month ($${capUser}) is used up. Ask the owner to raise it.`, cap: 'user'})};

  const tier = ['brain', 'small'].includes(body.tier) ? body.tier : 'assistant';
  const model = modelFor(tier, profile.role);
  const out = cleanBody(body, model, tier);
  const headers = {'content-type': 'application/json', 'x-api-key': key, 'anthropic-version': '2023-06-01'};
  // A key that is not scoped to one Anthropic workspace must name the workspace on every call.
  if (process.env.ANTHROPIC_WORKSPACE_ID) headers['anthropic-workspace-id'] = process.env.ANTHROPIC_WORKSPACE_ID;
  if (FALLBACK_OK.has(model)) { out.fallbacks = 'default'; headers['anthropic-beta'] = 'server-side-fallback-2026-07-01'; }
  return {out, headers, model, tier};
}
async function logUse(user, profile, body, tier, model, served, status, usage) {
  const cost = costOf(PRICES[served] ? served : model, usage || {});
  try {
    await rest('ai_usage', {method: 'POST', headers: {prefer: 'return=minimal'}, body: JSON.stringify({
      user_id: user.id, workspace_id: profile.workspace_id, tier: body.purpose ? tier + ':' + body.purpose : tier, model: served, status,
      input_tokens: (usage || {}).input_tokens || 0, output_tokens: (usage || {}).output_tokens || 0,
      cache_read_tokens: (usage || {}).cache_read_input_tokens || 0, cache_write_tokens: (usage || {}).cache_creation_input_tokens || 0,
      cost_usd: Number(cost.toFixed(6))})});
  } catch (e) { console.error('ai_usage log failed', e.message); }
}
export async function claude(user, profile, body) {
  const p = await prepare(user, profile, body);
  if (p.status) return p;
  const {out, headers, model, tier} = p;
  let r, text;
  try {
    r = await fetch('https://api.anthropic.com/v1/messages', {method: 'POST', headers, body: JSON.stringify(out)});
    text = await r.text();
  } catch (e) { return {status: 502, text: JSON.stringify({error: 'could not reach the model: ' + (e.message || e)})}; }
  let usage = {}, served = model;
  try { const j = JSON.parse(text); usage = j.usage || {}; served = j.model || model; } catch {}
  await logUse(user, profile, body, tier, model, served, r.status, usage);
  return {status: r.status, text};
}

// Rebuild the final message from Anthropic's event stream: text, thinking, tool calls (their input arrives as JSON
// in pieces), server tool blocks, stop reason and usage.
export function assemble(events) {
  let msg = null; const blocks = [];
  for (const e of events) {
    if (e.type === 'message_start') msg = {...e.message, content: []};
    else if (e.type === 'content_block_start') blocks[e.index] = {...e.content_block, _json: ''};
    else if (e.type === 'content_block_delta') {
      const b = blocks[e.index], d = e.delta || {};
      if (!b) continue;
      if (d.type === 'text_delta') b.text = (b.text || '') + d.text;
      else if (d.type === 'input_json_delta') b._json += d.partial_json || '';
      else if (d.type === 'thinking_delta') b.thinking = (b.thinking || '') + d.thinking;
      else if (d.type === 'signature_delta') b.signature = d.signature;
      else if (d.type === 'citations_delta') (b.citations = b.citations || []).push(d.citation);
    } else if (e.type === 'message_delta' && msg) {
      Object.assign(msg, e.delta || {});
      msg.usage = {...(msg.usage || {}), ...(e.usage || {})};
    }
  }
  if (!msg) return null;
  msg.content = blocks.filter(Boolean).map(b => {
    const {_json, ...rest} = b;
    if (_json) { try { rest.input = JSON.parse(_json); } catch { rest.input = {}; } }
    return rest;
  });
  return msg;
}

// The AI door's answer as a stream: the server reads Anthropic's event stream and sends a space every few seconds
// so the connection is never idle (Netlify cuts an idle response at 30 s), then the whole message as JSON. JSON
// allows leading whitespace, so the app reads it exactly as before. The cost is logged when the message ends.
// When a cut answer's usage is unknown, charge the time at the model's top speed (thinking is billed but unseen).
function cutUsage(msg, cut, model, started) {
  const u = (msg && msg.usage) || {};
  if (!cut) return u;
  const rate = /haiku/.test(model) ? 250 : /sonnet/.test(model) ? 130 : 90;
  const chars = ((msg && msg.content) || []).reduce((a, b) => a + String(b.text || b.thinking || '').length + (b.input ? JSON.stringify(b.input).length : 0), 0);
  return {...u, output_tokens: Math.max(u.output_tokens || 0, Math.ceil(chars / 3.5), Math.ceil(((Date.now() - started) / 1000) * rate))};
}

// body.stream === 'client': Anthropic's event stream goes to the page as it comes (the assistant renders the answer
// while it is written), then one `event: sd_done` with the usage and whether it was cut at 52 s. Parsed on the way
// through so the cost is logged like every other call.
function passThrough(r, enc, started, done) {
  const stream = new ReadableStream({
    async start(ctl) {
      const events = []; let buf = '', cut = false, err = null;
      const rd = r.body.getReader(), dec = new TextDecoder();
      try {
        for (;;) {
          const left = started + 52000 - Date.now();
          if (left <= 0) { cut = true; try { await rd.cancel(); } catch {} break; }
          const res = await Promise.race([rd.read(), new Promise(ok => setTimeout(() => ok({timeout: true}), left))]);
          if (res.timeout) { cut = true; try { await rd.cancel(); } catch {} break; }
          if (res.done) break;
          const text = dec.decode(res.value, {stream: true});
          ctl.enqueue(enc.encode(text));
          buf += text; let i;
          while ((i = buf.indexOf('\n\n')) >= 0) {
            const chunk = buf.slice(0, i); buf = buf.slice(i + 2);
            const data = chunk.split('\n').filter(l => l.startsWith('data:')).map(l => l.slice(5).trim()).join('');
            if (!data) continue;
            try { const e = JSON.parse(data); if (e.type === 'error') err = e; else events.push(e); } catch {}
          }
        }
      } catch (e) { err = {type: 'error', error: {message: String(e.message || e)}}; }
      const msg = assemble(events);
      try { await done(msg, cut, err); } catch {}
      const u = (msg && msg.usage) || {};
      ctl.enqueue(enc.encode(`\n\nevent: sd_done\ndata: ${JSON.stringify({usage: u, cut, error: err ? (err.error && err.error.message) || 'stream error' : null})}\n\n`));
      ctl.close();
    },
  });
  return new Response(stream, {status: 200, headers: {'content-type': 'text/event-stream', 'cache-control': 'no-store', 'x-accel-buffering': 'no'}});
}

export async function claudeStream(user, profile, body) {
  const started = Date.now();
  const clientStream = body.stream === 'client';
  delete body.stream;
  const p = await prepare(user, profile, body);
  if (p.status) return new Response(p.text, {status: p.status, headers: {'content-type': 'application/json', 'cache-control': 'no-store'}});
  const {out, headers, model, tier} = p;
  let r;
  try { r = await fetch('https://api.anthropic.com/v1/messages', {method: 'POST', headers, body: JSON.stringify({...out, stream: true})}); }
  catch (e) { return json(502, {error: 'could not reach the model: ' + (e.message || e)}); }
  if (!r.ok || !r.body) {                                   // refused up front: pass the answer through as before
    const text = await r.text();
    await logUse(user, profile, body, tier, model, model, r.status, {});
    return new Response(text, {status: r.status, headers: {'content-type': 'application/json', 'cache-control': 'no-store'}});
  }
  const enc = new TextEncoder();
  if (clientStream) return passThrough(r, enc, started, async (msg, cut, err) => {
    await logUse(user, profile, body, tier, model, (msg && msg.model) || model, err ? 500 : 200, cutUsage(msg, cut, model, started));
  });
  const stream = new ReadableStream({
    async start(ctl) {
      const tick = setInterval(() => { try { ctl.enqueue(enc.encode(' ')); } catch {} }, 4000);
      const events = []; let buf = '', err = null, cut = false;
      // Netlify stops a function at 60 s. At 52 s stop reading, send what has come, marked as cut short, and log
      // its cost from what was produced, so nothing is lost and nothing escapes the caps.
      const deadline = started + 52000;
      try {
        const rd = r.body.getReader(), dec = new TextDecoder();
        for (;;) {
          const left = deadline - Date.now();
          if (left <= 0) { cut = true; try { await rd.cancel(); } catch {} break; }
          const res = await Promise.race([rd.read(), new Promise(ok => setTimeout(() => ok({timeout: true}), left))]);
          if (res.timeout) { cut = true; try { await rd.cancel(); } catch {} break; }
          const {value, done} = res; if (done) break;
          buf += dec.decode(value, {stream: true});
          let i;
          while ((i = buf.indexOf('\n\n')) >= 0) {
            const chunk = buf.slice(0, i); buf = buf.slice(i + 2);
            const data = chunk.split('\n').filter(l => l.startsWith('data:')).map(l => l.slice(5).trim()).join('');
            if (!data) continue;
            try { const e = JSON.parse(data); if (e.type === 'error') err = e; else events.push(e); } catch {}
          }
        }
      } catch (e) { err = {type: 'error', error: {type: 'stream_error', message: String(e.message || e)}}; }
      clearInterval(tick);
      const msg = assemble(events);
      if (msg && cut) {
        msg.stop_reason = 'time_limit';
        msg.usage = cutUsage(msg, true, model, started);
        msg.content.push({type: 'text', text: '\n\n(Cut short: an answer here can run 52 seconds. Ask for the rest, or a shorter version.)'});
      }
      await logUse(user, profile, body, tier, model, (msg && msg.model) || model, err ? 500 : 200, (msg && msg.usage) || {});
      ctl.enqueue(enc.encode(JSON.stringify(err && !msg ? err : msg || {type: 'error', error: {type: 'empty', message: 'the model sent nothing'}})));
      ctl.close();
    },
  });
  return new Response(stream, {status: 200, headers: {'content-type': 'application/json', 'cache-control': 'no-store', 'x-accel-buffering': 'no'}});
}

export default async (req) => {
  if (req.method !== 'POST') return json(405, {error: 'POST only'});
  const who = await caller(req);
  if (who instanceof Response) return who;
  let body;
  try { body = await req.json(); } catch { return json(400, {error: 'bad JSON'}); }
  if (!body || !Array.isArray(body.messages) || !body.messages.length) return json(400, {error: 'messages required'});
  delete body.purpose;
  return claudeStream(who.user, who.profile, body);
};
export const config = {path: '/api/ai'};
