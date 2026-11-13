// Unsynced edits pushed at the next boot merge against the server copy they were based on (public/cloud.js
// keepAncestors, pushPending). Before, no ancestor survived a reload, so every child record the server deleted
// meanwhile looked new on this phone and came back: the live 11-08/09 invoices whose replaced placeholder line
// returned beside the new lines. Invented data. Run: node test/cloud_boot_merge_test.mjs
import fs from 'node:fs'; import vm from 'node:vm'; import assert from 'node:assert/strict';
const src = fs.readFileSync(new URL('../public/cloud.js', import.meta.url), 'utf8');
const J = v => JSON.parse(JSON.stringify(v));
let n = 0; const ok = (a, b, msg) => { assert.deepEqual(a, b, msg); n++; };
const tick = () => new Promise(r => setTimeout(r, 0));

// One phone's storage: localStorage (the pending marker, the versions) and the kept ancestors (IndexedDB in the browser).
const phone = () => { const ls = new Map(), anc = new Map(); return {
  localStorage: {getItem: k => (ls.has(k) ? ls.get(k) : null), setItem: (k, v) => ls.set(k, String(v)), removeItem: k => ls.delete(k)},
  anc: {get: async k => J(anc.get(k) ?? null) || undefined, put: async (k, v) => { anc.set(k, J(v)); }, clear: async () => anc.clear()}, ancMap: anc}; };
const server = {rows: {}, saves: []};
const sbMock = {
  rpc: async (fn, args) => {
    if (fn === 'session_alive') return {data: true};
    if (fn === 'save_collections') {
      server.saves.push(J(args.p_items));
      return {data: args.p_items.map(it => { const r = server.rows[it.name]; if (r && r.v !== it.base) return {name: it.name, conflict: true}; server.rows[it.name] = {v: (r ? r.v : 0) + 1, data: J(it.data)}; return {name: it.name, version: server.rows[it.name].v}; })};
    }
    throw new Error('rpc ' + fn);
  },
  from: () => ({select: () => ({eq: (k, name) => ({maybeSingle: async () => { const r = server.rows[name]; return {data: r ? {name, data: J(r.data), version: r.v} : null}; }})})}),
};
// A page load: a fresh cloud layer on the phone's storage.
function boot(ph) {
  const ctx = {window: {fetch: async () => {}, SDP_CONFIG: {supabaseUrl: 'https://db', supabaseAnonKey: 'anon'}, supabase: {}}, navigator: {onLine: true}, location: {href: 'https://x/', origin: 'https://x'}, URL, Headers,
    localStorage: ph.localStorage, document: {addEventListener() {}, visibilityState: 'visible'}, console, setTimeout, clearTimeout};
  ctx.window.window = ctx.window; vm.createContext(ctx); vm.runInContext(src, ctx);
  const C = ctx.window.Cloud, T = C._test;
  T.sb(sbMock); T.anc(ph.anc); T.session({user: {id: 'auth-owner'}, access_token: 't'}); T.profile({role: 'owner', workspace_id: 'demo'});
  return {C, T};
}

const P = {id: 'ln_p', item: 'Placeholder', desc: 'Progress billing, see schedule', qty: 1, rate: 100};
const L = [1, 2, 3].map(i => ({id: 'ln_' + i, item: 'Item ' + i, desc: 'Work ' + i, qty: 1, rate: 100 * i}));
const firm = () => ({users: [], clients: [{id: 'cl_h', name: 'Harrow Street Owner', invoices: [{id: 'inv_901', number: 'INV-2026-901', amount: 100, _base: '[["title","Harrow St"]]', lines: [J(P)]}],
  payments: [{id: 'pay_a', invoiceId: 'inv_901', amount: 50}, {id: 'pay_b', invoiceId: 'inv_901', amount: 25}]}]});

// Session 1 syncs, goes offline, re-caches (or edits); the server then replaces the invoice's lines and drops pay_b;
// session 2 (the next boot) pushes the pending save. Returns what the server holds after, and pushPending's answer.
async function scenario(localChange, opts = {}) {
  server.rows = {}; server.saves = [];
  const ph = phone(); const DB = firm();
  const {C, T} = boot(ph); C.setDbRef(() => DB);
  for (const [name, data] of Object.entries(C.shards(DB))) { server.rows[name] = {v: 5, data: J(data)}; T.remember(name, data, 5); }
  C.state.online = false;
  localChange(DB);
  await C.push(DB); await tick(); await tick();                         // offline: marked pending, ancestor kept
  if (opts.noAncestor) ph.ancMap.clear();                               // a marker left by a build before the ancestor was kept
  const s = J(server.rows.clients.data); s[0].invoices[0].lines = J(L); s[0].invoices[0].amount = 600; s[0].payments = s[0].payments.filter(p => p.id !== 'pay_b');
  server.rows.clients = {v: 6, data: s};                                // the server-side write
  const two = boot(ph);                                                 // the next boot, same phone
  const res = await two.C.pushPending(J(DB));
  return {res, inv: server.rows.clients.data[0].invoices[0], pays: server.rows.clients.data[0].payments.map(p => p.id), saves: server.saves.length};
}

const recache = DB => { const d = DB.clients[0].invoices[0]; d._base = '[["title","Harrow St"],["lines",[]]]'; d.amount = 100.01; d.lines[0] = {num: '1', ...d.lines[0]}; };
let o = await scenario(recache);
ok(o.inv.lines.map(l => l.id), ['ln_1', 'ln_2', 'ln_3'], 'boot push after the server replaced the lines, this phone only re-cached: exactly the new lines');
ok([o.inv.amount, o.pays, o.res.conflicts], [600, ['pay_a'], 0], 'the server amount and its removed payment stand; no conflict');

o = await scenario(DB => { recache(DB); DB.clients[0].invoices[0].lines[0].rate = 120; });
ok([o.inv.lines.map(l => l.id), o.inv.lines[3].rate, o.res.conflicts], [['ln_1', 'ln_2', 'ln_3', 'ln_p'], 120, 1], 'this phone really edited the placeholder: kept beside the new lines, conflict counted');

o = await scenario(DB => { DB.clients[0].payments[1].amount = 26; });
ok([o.pays, o.res.conflicts], [['pay_a', 'pay_b'], 1], 'a payment edited here that the server removed is kept and counted');

o = await scenario(DB => { DB.clients[0].payments.push({id: 'pay_n', invoiceId: 'inv_901', amount: 10}); });
ok([o.pays, o.inv.lines.length, o.res.conflicts], [['pay_a', 'pay_n'], 3, 0], 'a payment new on this phone is added; the deleted one and the old line stay gone');

// Without a kept ancestor (an older build's marker) the boot falls back to keeping this phone's records: the gap this closes.
o = await scenario(recache, {noAncestor: true});
ok(o.inv.lines.length, 4, 'no ancestor: the old fallback (documented, not wanted) still adds the phone-only line');
console.log('ALL PASS', `(${n} checks)`);
