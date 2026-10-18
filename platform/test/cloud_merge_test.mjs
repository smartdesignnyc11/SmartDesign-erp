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
console.log('ALL PASS', `(${n} checks)`);
