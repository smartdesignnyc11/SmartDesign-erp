// The chain over a month's postings, the same canonical text the app hashes (truthChain in src/app.js), computed
// here from the server's own copy of the books. SHA-256 is the server's seal; the app's FNV-1a is computed too, to
// show whether the browser that closed the month saw the same books.
import crypto from 'node:crypto';
const r2 = n => Math.round(100 * (+n || 0)) / 100;
export function fnv(s) { let h = 0x811c9dc5; const str = String(s); for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; } return h.toString(16).padStart(8, '0'); }
export const sha = s => crypto.createHash('sha256').update(String(s)).digest('hex');
export function postings(gl, ym) {
  return ((gl || {}).journals || []).filter(j => ['posted', 'reversed'].includes(j.status) && String(j.date || '').slice(0, 7) === ym).sort((a, b) => (a.n || 0) - (b.n || 0));
}
const canon = (prior, j) => `${prior}|${j.n}|${j.id}|${j.key || j.kind}|${j.sourceType || ''}:${j.sourceId || ''}|${j.date}|${(j.lines || []).map(l => `${l.acct}:${r2(l.dr || 0)}:${r2(l.cr || 0)}`).join(',')}`;
export function chain(gl, ym, h = sha) {
  let prior = h === sha ? '' : '0'; const links = [];
  for (const j of postings(gl, ym)) { prior = h(canon(prior, j)); links.push({id: j.id, n: j.n, h: prior}); }
  return {n: links.length, head: h === sha ? (prior || sha('')) : prior, links};
}
// Compare a seal with the books now: which postings changed, went missing, or were added since.
export function compare(seal, gl) {
  const now = chain(gl, seal.ym), J = postings(gl, seal.ym), byId = Object.fromEntries(J.map(j => [j.id, j]));
  const changed = [], missing = [];
  let prior = '';
  for (const l of seal.links || []) {
    const j = byId[l.id];
    if (!j) { missing.push(l.n ? '#' + l.n : l.id); continue; }
    if (sha(canon(prior, j)) !== l.h) changed.push('#' + (j.n || '?') + (j.memo ? ' ' + j.memo : ''));
    prior = l.h;
  }
  const sealed = new Set((seal.links || []).map(l => l.id));
  const added = J.filter(j => !sealed.has(j.id)).map(j => '#' + (j.n || '?') + (j.memo ? ' ' + j.memo : ''));
  return {ok: !changed.length && !missing.length && !added.length && now.head === seal.head_sha, changed, missing, added, n: now.n};
}
