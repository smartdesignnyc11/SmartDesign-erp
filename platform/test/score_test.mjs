// Which watch finds deserve a notification, and what it says. node test/score_test.mjs
import assert from 'node:assert/strict';
import {contextFrom, score, message} from '../netlify/functions/lib/score.mjs';
let n = 0; const ok = (c, m) => { assert.ok(c, m); n++; };
const ctx = contextFrom({vendors: [{name: 'Pella', email: 'ray@pellawindows.example'}], clients: [{name: 'Klein', contacts: [{email: 'sarah.klein@gmail.com'}]}],
  projects: [{project: {name: '121 State St — Klein', address: '121 State St, Brooklyn'}}]});
ok(ctx.emails.has('ray@pellawindows.example') && ctx.domains.has('pellawindows.example') && !ctx.domains.has('gmail.com'), 'firm people read from vendors and clients; public mail domains are not trusted wholesale');
const m = (from, subj, labels = ['INBOX'], extra = []) => ({labelIds: labels, snippet: '', payload: {headers: [{name: 'From', value: from}, {name: 'Subject', value: subj}, ...extra]}});
const soon = new Date(Date.now() + 5 * 3600e3).toISOString(), later = new Date(Date.now() + 9 * 864e5).toISOString();
const found = {gmail: [
  m('Ray <ray@pellawindows.example>', 'Revised quote'),                      // vendor
  m('Dana <dana@pellawindows.example>', 'Delivery date'),                    // vendor's domain
  m('Sarah Klein <sarah.klein@gmail.com>', 'Tile choice'),                   // client
  m('Neighbor <n@example.com>', 'Noise at 121 State St this morning'),       // names a job
  m('DOB <noreply@buildings.nyc.gov>', 'Inspection result'),                 // agency
  m('Shop <deals@shop.example>', 'Sale', ['INBOX', 'CATEGORY_PROMOTIONS']),  // promotion
  m('News <news@letter.example>', '121 State market report', ['INBOX'], [{name: 'List-Unsubscribe', value: '<x>'}]),  // newsletter naming the job
  m('Friend <f@gmail.com>', 'Lunch?'),                                        // personal
  m('Alan <alan@smartdesign.nyc>', 'Re: quote', ['SENT'])],                   // own sent
  cal: [{summary: 'Site walk', start: {dateTime: soon}}, {summary: 'Board meeting', start: {dateTime: later}}]};
const items = score(found, ctx, 'alan@smartdesign.nyc');
const lines = items.map(i => i.line).join('\n');
ok(/Revised quote/.test(lines) && /Delivery date/.test(lines) && /Tile choice/.test(lines), 'vendors, their colleagues and clients notify');
ok(/Noise at 121 State/.test(lines) && /Inspection result/.test(lines), 'a job named and a city agency notify');
ok(!/Sale|market report|Lunch|Re: quote/.test(lines), 'promotions, newsletters, personal mail and own sent mail do not');
ok(/Site walk/.test(lines) && !/Board meeting/.test(lines), 'a meeting in the next two days notifies; one next week does not');
const msg = message(items);
ok(msg.title === '5 new from people and jobs you work with · 1 calendar change in the next two days', msg.title);
ok(msg.body.split('\n').length === 4 && /and 3 more$/.test(msg.body), 'three lines and a count, nothing more');
ok(message([]) === null, 'nothing that matters: no notification');
console.log('ALL PASS', `(${n} checks)`);
