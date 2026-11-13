// The merge that keeps two phones' edits (public/cloud.js merge3). Run: node test/cloud_merge_test.mjs
import fs from 'node:fs'; import vm from 'node:vm'; import assert from 'node:assert/strict';
const src = fs.readFileSync(new URL('../public/cloud.js', import.meta.url), 'utf8');
const ctx = {window: {fetch: async () => {}, SDP_CONFIG: {}}, navigator: {onLine: true}, location: {href: 'https://x/', origin: 'https://x'}, URL, Headers, localStorage: {getItem: () => null, setItem() {}, removeItem() {}}, document: {addEventListener() {}}, console};
ctx.window.window = ctx.window; vm.createContext(ctx); vm.runInContext(src, ctx);
const {merge3} = ctx.window.Cloud;
const m = (b, l, s) => { const conf = {n: 0}; return [JSON.parse(JSON.stringify(merge3(b, l, s, conf))), conf.n]; };
let n = 0; const ok = (a, b, msg) => { assert.deepEqual(a, b, msg); n++; };
const base = [{id: 'a', v: 1}, {id: 'b', v: 1}];
// two phones edit different records: both kept, no conflict
ok(m(base, [{id: 'a', v: 2}, {id: 'b', v: 1}], [{id: 'a', v: 1}, {id: 'b', v: 3}]), [[{id: 'a', v: 2}, {id: 'b', v: 3}], 0], 'different records');
// a note added offline on each phone: both kept
ok(m(base, [...base, {id: 'c', v: 1}], [...base, {id: 'd', v: 1}]), [[...base, {id: 'd', v: 1}, {id: 'c', v: 1}], 0], 'two new records');
// the same field on both: the server's stands, counted as a conflict
ok(m(base, [{id: 'a', v: 2}, {id: 'b', v: 1}], [{id: 'a', v: 5}, {id: 'b', v: 1}]), [[{id: 'a', v: 5}, {id: 'b', v: 1}], 1], 'same field');
// different fields of the same record: both kept
ok(m({id: 'p', a: 1, b: 1}, {id: 'p', a: 2, b: 1}, {id: 'p', a: 1, b: 2}), [{id: 'p', a: 2, b: 2}, 0], 'different fields');
// deleted here, untouched there: stays deleted
ok(m(base, [{id: 'a', v: 1}], base), [[{id: 'a', v: 1}], 0], 'local delete');
// deleted there, changed here: kept, and said
ok(m(base, [{id: 'a', v: 1}, {id: 'b', v: 9}], [{id: 'a', v: 1}], 0)[1], 1, 'delete vs edit');
// nested: a project shard with daily logs added on two phones and the budget changed in the office
const pb = {id: 'p1', budget: 100, logs: [{id: 'l1', t: 'x'}]};
ok(m(pb, {...pb, logs: [...pb.logs, {id: 'l2', t: 'site'}]}, {...pb, budget: 120}), [{id: 'p1', budget: 120, logs: [{id: 'l1', t: 'x'}, {id: 'l2', t: 'site'}]}, 0], 'nested');
// no common ancestor (boot re-push): the server's records stand, records only this phone has are added
ok(m(undefined, [{id: 'a', v: 2}, {id: 'z', v: 1}], [{id: 'a', v: 1}]), [[{id: 'a', v: 1}, {id: 'z', v: 1}], 1], 'no ancestor');

// ---- a child record deleted on one side stays deleted unless the other side changed that same record (live
// 11-08/09: a server write replaced the placeholder line of 23 invoices; a phone holding the older copy saved having
// only re-cached _base and the amounts, and the placeholder came back beside the new lines, doubling each total).
// Derived fields (docMark's _base, docAmountsSync's amount, ctNumber's num, a copied line's shipping) are not edits.
const J = v => JSON.parse(JSON.stringify(v));
const mk = (b, l, s, k) => { const conf = {n: 0}; return [J(merge3(b, l, s, conf, k)), conf.n]; };
const P = {id: 'ln_p', item: 'Placeholder', desc: 'Progress billing, see schedule', qty: 1, rate: 100};
const L = [1, 2, 3].map(i => ({id: 'ln_' + i, item: 'Item ' + i, desc: 'Work ' + i, qty: 1, rate: 100 * i}));
const inv0 = {id: 'inv_901', number: 'INV-2026-901', clientId: 'cl_h', status: 'sent', amount: 100, _base: '[["title","Harrow St"]]', lines: [P]};
const pays0 = [{id: 'pay_a', invoiceId: 'inv_901', amount: 50, date: '2026-09-01'}, {id: 'pay_b', invoiceId: 'inv_901', amount: 25, date: '2026-09-02'}];
const cl0 = [{id: 'cl_h', name: 'Harrow Street Owner', invoices: [inv0], payments: pays0}];
const serverSide = () => { const c = J(cl0); Object.assign(c[0].invoices[0], {lines: J(L), amount: 600}); return c; };
// this device only re-cached: a new _base, the cached amount by another rounding, a line number, the line's keys
// in another order (a revert re-adds them)
const recached = () => { const c = J(cl0); const d = c[0].invoices[0]; d._base = '[["title","Harrow St"],["lines",[]]]'; d.amount = 100.01; d.lines = [{num: '1', rate: 100, qty: 1, desc: P.desc, item: P.item, id: P.id}]; return c; };
let [r, nc] = mk(cl0, recached(), serverSide(), 'clients');
ok(r[0].invoices[0].lines.map(x => x.id), ['ln_1', 'ln_2', 'ln_3'], 'server replaced the lines, this device only re-cached: exactly the new lines');
ok([r[0].invoices[0].amount, r[0].invoices[0]._base, nc], [600, inv0._base, 0], 're-cached fields take the server value and are no conflict');
// the same when the server's write left the cached amount as it was
{ const s = serverSide(); s[0].invoices[0].amount = 100; [r, nc] = mk(cl0, recached(), s, 'clients'); ok([r[0].invoices[0].lines.length, nc], [3, 0], 'server left the amount: still exactly the new lines'); }
// this device really edited the placeholder: it is kept beside the new lines, and the conflict is counted
{ const l = recached(); l[0].invoices[0].lines[0].rate = 120; [r, nc] = mk(cl0, l, serverSide(), 'clients');
  ok([r[0].invoices[0].lines.map(x => x.id), r[0].invoices[0].lines[3].rate, nc], [['ln_1', 'ln_2', 'ln_3', 'ln_p'], 120, 1], 'a real edit to the deleted line keeps it and counts the conflict'); }
// the mirror: deleted here, the server only re-cached it: stays deleted
{ const l = J(cl0); l[0].invoices[0].lines = J(L); const s = J(cl0); s[0].invoices[0].lines[0].num = '1'; s[0].invoices[0]._base = 'x';
  [r, nc] = mk(cl0, l, s, 'clients'); ok([r[0].invoices[0].lines.map(x => x.id), nc], [['ln_1', 'ln_2', 'ln_3'], 0], 'deleted here, only re-cached there: stays deleted'); }
// a line copied from its estimate line (fromLine): docMark writes its shipping, which is not an edit
{ const fl = {id: 'ln_f', fromLine: 'est_1:el_1', item: 'Vanity', qty: 1, rate: 900};
  const b = [{id: 'inv_902', lines: [fl]}], s = [{id: 'inv_902', lines: J(L)}], l = [{id: 'inv_902', lines: [{...fl, shipping: 0, shipMarkupPct: 0}]}];
  [r, nc] = mk(b, l, s, 'invoices'); ok([r[0].lines.length, nc], [3, 0], 'a copied line\'s shipping written by docMark is not an edit');
  // on a line of the person's own (no fromLine), shipping is a real edit
  const own = {id: 'ln_o', item: 'Tile', qty: 1, rate: 40}; [r, nc] = mk([{id: 'e1', lines: [own]}], [{id: 'e1', lines: [{...own, shipping: 30}]}], [{id: 'e1', lines: J(L)}], 'estimates');
  ok([r[0].lines.length, nc], [4, 1], 'shipping typed on a line is an edit'); }
// both sides re-cached the amount differently: the server's, no conflict
[r, nc] = mk([{id: 'i', amount: 1}], [{id: 'i', amount: 2}], [{id: 'i', amount: 3}], 'invoices'); ok([r[0].amount, nc], [3, 0], 'a derived field changed on both is no conflict');
// payments: the server removed one (voided and re-entered) and added another; this device only re-cached the invoice
{ const s = J(cl0); s[0].payments = [pays0[0], {id: 'pay_c', invoiceId: 'inv_901', amount: 25, date: '2026-09-03'}];
  const l = J(cl0); l[0].invoices[0]._base = 'y'; l[0].invoices[0].amount = 100.01;
  [r, nc] = mk(cl0, l, s, 'clients'); ok([r[0].payments.map(p => p.id), nc], [['pay_a', 'pay_c'], 0], 'a payment the server removed stays removed');
  // this device changed that payment's amount (a payment's amount is never derived): kept, and said
  l[0].payments[1].amount = 26; [r, nc] = mk(cl0, l, s, 'clients');
  ok([r[0].payments.map(p => p.id), nc], [['pay_a', 'pay_c', 'pay_b'], 1], 'a payment edited here that the server removed is kept and counted');
  // the same payment's amount changed on both: the server's stands, counted
  const s2 = J(cl0); s2[0].payments[0].amount = 55; const l2 = J(cl0); l2[0].payments[0].amount = 60;
  [r, nc] = mk(cl0, l2, s2, 'clients'); ok([r[0].payments[0].amount, nc], [55, 1], 'a payment amount changed on both is a conflict'); }
console.log('ALL PASS', `(${n} checks)`);
