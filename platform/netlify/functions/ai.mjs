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

// One call to Claude for a signed-in member: caps checked before, the model by tier, cost logged after.
// The AI door below and the document reader (doctext.mjs) both go through it, so neither can skip the caps.
export async function claude(user, profile, body) {
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) return {status: 500, text: JSON.stringify({error: 'ANTHROPIC_API_KEY is not set on the server'})};
  const capFirm = Number(process.env.AI_CAP_FIRM_USD || 40), capUser = Number(process.env.AI_CAP_USER_USD || 8);
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

  let r, text;
  try {
    r = await fetch('https://api.anthropic.com/v1/messages', {method: 'POST', headers, body: JSON.stringify(out)});
    text = await r.text();
  } catch (e) { return {status: 502, text: JSON.stringify({error: 'could not reach the model: ' + (e.message || e)})}; }
  let usage = {}, served = model;
  try { const j = JSON.parse(text); usage = j.usage || {}; served = j.model || model; } catch {}
  const cost = costOf(PRICES[served] ? served : model, usage);
  try {
    await rest('ai_usage', {method: 'POST', headers: {prefer: 'return=minimal'}, body: JSON.stringify({
      user_id: user.id, workspace_id: profile.workspace_id, tier: body.purpose ? tier + ':' + body.purpose : tier, model: served, status: r.status,
      input_tokens: usage.input_tokens || 0, output_tokens: usage.output_tokens || 0,
      cache_read_tokens: usage.cache_read_input_tokens || 0, cache_write_tokens: usage.cache_creation_input_tokens || 0,
      cost_usd: Number(cost.toFixed(6))})});
  } catch (e) { console.error('ai_usage log failed', e.message); }
  return {status: r.status, text};
}

export default async (req) => {
  if (req.method !== 'POST') return json(405, {error: 'POST only'});
  const who = await caller(req);
  if (who instanceof Response) return who;
  let body;
  try { body = await req.json(); } catch { return json(400, {error: 'bad JSON'}); }
  if (!body || !Array.isArray(body.messages) || !body.messages.length) return json(400, {error: 'messages required'});
  delete body.purpose;
  const r = await claude(who.user, who.profile, body);
  return new Response(r.text, {status: r.status, headers: {'content-type': 'application/json', 'cache-control': 'no-store'}});
};
export const config = {path: '/api/ai'};
