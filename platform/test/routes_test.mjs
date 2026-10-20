// The route service (/api/routes) offline: sign-in required, the plain "no key" answer, the Routes API call it makes
// once GOOGLE_MAPS_KEY is set (headers, body, traffic only for a time ahead), the matrix it reads back, and the fallback
// when Google refuses. node test/routes_test.mjs
import assert from 'node:assert/strict';
Object.assign(process.env, {SUPABASE_URL: 'https://db', SUPABASE_SERVICE_ROLE_KEY: 's'});
delete process.env.GOOGLE_MAPS_KEY;
const GOOD = 'h.' + Buffer.from(JSON.stringify({session_id: 's1'})).toString('base64url') + '.sig';
const W = {calls: [], answer: null};
globalThis.fetch = async (url, o = {}) => {
  const u = String(url), J = (x, s = 200) => new Response(JSON.stringify(x), {status: s});
  if (u.endsWith('/auth/v1/user')) return o.headers.authorization === 'Bearer ' + GOOD ? J({id: 'u1'}) : J({}, 401);
  if (u.endsWith('/rpc/session_alive_for')) return J(true);
  if (u.includes('/rest/v1/profiles')) return J([{id: 'u1', role: 'coord', workspace_id: 'w'}]);
  if (u.startsWith('https://routes.googleapis.com/')) { W.calls.push({u, o, body: JSON.parse(o.body)}); return W.answer(); }
  throw new Error('unexpected ' + u);
};
const mod = await import('../netlify/functions/routes.mjs');
const routes = mod.default;
let n = 0; const ok = (c, m) => { assert.ok(c, m); n++; };
const call = async (b, tok = GOOD) => { const r = await routes(new Request('https://x/api/routes', {method: 'POST', headers: tok ? {authorization: 'Bearer ' + tok} : {}, body: JSON.stringify(b)})); return [r.status, await r.json()]; };
const P = [{lat: 40.6784, lng: -73.995}, {lat: 40.6708, lng: -73.9973}, {lat: 40.6907, lng: -73.9929}];

// sign-in is required, and the request is checked before anything leaves the server
let [s, j] = await call({points: P}, '');
ok(s === 401, 'no session: 401');
[s, j] = await call({points: [P[0]]});
ok(s === 400 && /two stops/.test(j.error), 'one stop is refused');
[s, j] = await call({points: P.concat([{lat: 'x', lng: 1}])});
ok(s === 400 && /latitude/.test(j.error), 'a stop without coordinates is refused');
[s, j] = await call({points: Array.from({length: 26}, () => P[0])});
ok(s === 413 && /25 stops/.test(j.why), 'more than 25 stops is refused with the reason');

// no key: a plain answer, the app keeps its estimate, and Google is never called
[s, j] = await call({points: P});
ok(s === 200 && j.ok === false && j.provider === 'offline' && /GOOGLE_MAPS_KEY is not set in Netlify/.test(j.why), 'no key: says so plainly');
ok(W.calls.length === 0, 'no key: Google is not called');

// with the key: one matrix call, the key in the header, a field mask, traffic only for a time still ahead
process.env.GOOGLE_MAPS_KEY = 'test-key';
W.answer = () => new Response(JSON.stringify([
  {originIndex: 0, destinationIndex: 1, duration: '420s', distanceMeters: 1609, condition: 'ROUTE_EXISTS'},
  {originIndex: 1, destinationIndex: 2, duration: '900s', distanceMeters: 3218, condition: 'ROUTE_EXISTS'},
  {originIndex: 2, destinationIndex: 0, duration: '600s', distanceMeters: 2414, condition: 'ROUTE_NOT_FOUND'},
]), {status: 200});
const ahead = new Date(Date.now() + 3600e3).toISOString();
[s, j] = await call({points: P, departAt: ahead});
const c = W.calls[0];
ok(s === 200 && j.ok === true && j.provider === 'google', 'with the key: the Google matrix');
ok(c && c.o.headers['X-Goog-Api-Key'] === 'test-key' && /duration/.test(c.o.headers['X-Goog-FieldMask']), 'the key and the field mask are sent as headers');
ok(c.body.origins.length === 3 && c.body.destinations.length === 3 && c.body.travelMode === 'DRIVE' && c.body.routingPreference === 'TRAFFIC_AWARE', 'every stop is an origin and a destination, driving, with traffic');
ok(c.body.origins[1].waypoint.location.latLng.latitude === 40.6708, 'coordinates only');
ok(c.body.departureTime === new Date(Date.parse(ahead)).toISOString(), 'a departure ahead is sent');
ok(j.min[0][1] === 7 && j.min[1][2] === 15 && j.miles[0][1] === 1 && j.miles[1][2] === 2, `minutes and miles read back: ${JSON.stringify(j.min)} ${JSON.stringify(j.miles)}`);
ok(j.min[2][0] === null && j.min[0][0] === 0, 'a pair with no route stays empty; a stop to itself is 0');
await call({points: P, departAt: '2020-01-01T08:00:00Z'});
ok(!('departureTime' in W.calls[1].body), 'a departure in the past is not sent (Google refuses it)');

// Google refuses: the app is told why and keeps its estimate
W.answer = () => new Response(JSON.stringify({error: {status: 'PERMISSION_DENIED', message: 'Routes API has not been used in project'}}), {status: 403});
[s, j] = await call({points: P});
ok(s === 200 && j.ok === false && j.provider === 'offline' && /403/.test(j.why) && /Routes API has not been used/.test(j.why), 'a refusal falls back with the reason');
console.log(`routes: ${n} checks passed`);
