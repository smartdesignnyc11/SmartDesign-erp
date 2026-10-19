// The server's seal of a closed month: the same postings the app chains, its FNV head equal to the app's own
// (truthChain, taken from src/app.js), and a changed, deleted or added posting named. node test/chain_test.mjs
import assert from 'node:assert/strict'; import fs from 'node:fs';
Object.assign(process.env, {SUPABASE_URL: 'https://db', SUPABASE_SERVICE_ROLE_KEY: 's'});
const {chain, fnv, compare} = await import('../netlify/functions/lib/chain.mjs');
let n = 0; const ok = (c, m) => { assert.ok(c, m); n++; };
// the app's own functions, lifted from src/app.js so the two can never drift apart unnoticed
const app = fs.readFileSync(new URL('../../src/app.js', import.meta.url), 'utf8');
const grab = name => { const i = app.indexOf('function ' + name + '('); let d = 0, j = app.indexOf('{', i); for (; j < app.length; j++) { if (app[j] === '{') d++; else if (app[j] === '}' && !--d) break; } return app.slice(i, j + 1); };
const appChain = new Function('DB', 'r2', 'glYm', grab('truthHash') + '\nconst TRUTH_HASH_SCHEME="x";\n' + grab('truthChain') + '\nreturn truthChain;');
const J = (nn, id, date, acct, amt, status = 'posted') => ({n: nn, id, date, status, key: 'bill', sourceType: 'bill', sourceId: 'b' + nn, memo: 'Bill ' + nn, lines: [{acct, dr: amt}, {acct: '2000', cr: amt}]});
const gl = {journals: [J(1, 'j1', '2026-08-04', '5100', 1200), J(2, 'j2', '2026-08-09', '5200', 340.5), J(3, 'j3', '2026-08-30', '5100', 87.4, 'reversed'), J(4, 'j4', '2026-09-02', '5100', 10), J(5, 'j5', '2026-08-12', '5300', 50, 'draft')]};
const r2 = v => Math.round(100 * (+v || 0)) / 100, glYm = d => (d || '').slice(0, 7);
const a = appChain({gl}, r2, glYm)('2026-08');
const f = chain(gl, '2026-08', fnv);
ok(a.n === 3 && f.n === 3, 'posted and reversed postings of the month only, drafts and other months out');
ok(a.head === f.head, `the server's FNV head equals the app's own (${f.head})`);
const s = chain(gl, '2026-08');
ok(/^[0-9a-f]{64}$/.test(s.head) && s.head !== f.head, 'the server seals with SHA-256');
const seal = {ym: '2026-08', head_sha: s.head, links: s.links, n: s.n};
ok(compare(seal, gl).ok, 'untouched books verify');
const g2 = JSON.parse(JSON.stringify(gl)); g2.journals[1].lines[0].dr = 3405; g2.journals[1].lines[1].cr = 3405;
const c2 = compare(seal, g2); ok(!c2.ok && c2.changed.join() === '#2 Bill 2', `a changed amount is named: ${c2.changed}`);
const g3 = JSON.parse(JSON.stringify(gl)); g3.journals.splice(0, 1);
const c3 = compare(seal, g3); ok(!c3.ok && c3.missing.join() === '#1', `a deleted posting is named: ${c3.missing}`);
const g4 = JSON.parse(JSON.stringify(gl)); g4.journals.push(J(9, 'j9', '2026-08-20', '5100', 999));
const c4 = compare(seal, g4); ok(!c4.ok && c4.added.join() === '#9 Bill 9', `a posting slipped in after the close is named: ${c4.added}`);
const g5 = JSON.parse(JSON.stringify(gl)); g5.journals[0].memo = 'a new memo';
ok(compare(seal, g5).ok, 'a memo edit is not a change to the money');
// the function: who may seal and verify
const W = {rows: [], gl, role: 'controller'};
globalThis.fetch = async (url, o = {}) => {
  const u = String(url), Jr = (x, st = 200) => new Response(JSON.stringify(x), {status: st});
  if (u.endsWith('/auth/v1/user')) return Jr({id: 'u1'});
  if (u.endsWith('/rpc/session_alive_for')) return Jr(true);
  if (u.includes('/rest/v1/profiles')) return Jr([{id: 'u1', role: W.role, workspace_id: 'w', name: 'Controller'}]);
  if (u.includes('/rest/v1/collections?')) return Jr([{data: W.gl}]);
  if (u.includes('/rest/v1/period_seals')) { if (o.method === 'POST') { W.rows.unshift(JSON.parse(o.body)); return new Response(null, {status: 201}); } return Jr(W.rows.map(r => ({...r, sealed_at: '2026-09-10T12:00:00Z'}))); }
  throw new Error('unexpected ' + u);
};
const fn = (await import('../netlify/functions/seal.mjs')).default;
const TOK = 'h.' + Buffer.from(JSON.stringify({session_id: 's'})).toString('base64url') + '.x';
const call = async b => { const r = await fn(new Request('https://x/api/seal', {method: 'POST', headers: {authorization: 'Bearer ' + TOK}, body: JSON.stringify(b)})); return [r.status, await r.json()]; };
W.role = 'pm'; let [st, j] = await call({action: 'seal', ym: '2026-08', head: a.head}); ok(st === 403, 'only the owner or the controller seals');
W.role = 'controller'; [st, j] = await call({action: 'seal', ym: '2026-08', head: a.head});
ok(st === 200 && j.matches === true && W.rows.length === 1 && W.rows[0].head_sha === s.head, 'sealed from the server\'s own books; the browser saw the same');
[st, j] = await call({action: 'verify'}); ok(st === 200 && j.months.length === 1 && j.months[0].ok, 'verify: the books match the seal');
W.gl = g2; [st, j] = await call({action: 'verify'}); ok(!j.months[0].ok && j.months[0].changed.length === 1, 'verify after a rewrite in the books: caught and named');
W.role = 'crew'; [st, j] = await call({action: 'verify'}); ok(st === 403, 'the field cannot read the seals');
console.log('ALL PASS', `(${n} checks)`);
