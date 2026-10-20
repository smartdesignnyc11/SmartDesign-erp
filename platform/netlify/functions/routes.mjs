// /api/routes: drive times between the stops of the driver's route (BACKLOG §1.29 item 4, phase 2).
// - With GOOGLE_MAPS_KEY set in Netlify (a Google Cloud key with the Routes API enabled; Alan adds it under the site's
//   environment variables), one computeRouteMatrix call returns the minutes and miles between every pair of stops,
//   with traffic for the departure time when that time is still ahead.
// - Without the key it says so plainly, and the app keeps its offline estimate. Nothing is ever scraped.
// Signed-in members only, through the same door as every function (caller); at most 25 stops (625 pairs, the API's
// limit for a traffic-aware matrix). The points are coordinates only: no names, no jobs, no money leave the firm.
import {caller, json} from './lib/auth.mjs';
export const MAX_POINTS = 25;
export const NO_KEY = 'GOOGLE_MAPS_KEY is not set in Netlify, so drive times stay estimated offline. Alan adds the key (a Google Cloud key with the Routes API enabled) under the site\'s environment variables; nothing else changes.';
const URL_ = 'https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix';

// The matrix: min[i][j] (drive minutes) and miles[i][j]; a pair with no route is null.
export async function routeMatrix(points, departAt, key, fetchFn = fetch) {
  const wp = points.map(p => ({waypoint: {location: {latLng: {latitude: +p.lat, longitude: +p.lng}}}}));
  const body = {origins: wp, destinations: wp, travelMode: 'DRIVE', routingPreference: 'TRAFFIC_AWARE'};
  const t = departAt ? Date.parse(departAt) : NaN;
  if (isFinite(t) && t > Date.now() + 60e3) body.departureTime = new Date(t).toISOString();
  const r = await fetchFn(URL_, {method: 'POST', headers: {'content-type': 'application/json', 'X-Goog-Api-Key': key, 'X-Goog-FieldMask': 'originIndex,destinationIndex,duration,distanceMeters,condition'}, body: JSON.stringify(body)});
  const txt = await r.text();
  if (!r.ok) {
    let msg = '';
    try { const j = JSON.parse(txt); msg = (j.error && (j.error.message || j.error.status)) || ''; } catch {}
    throw new Error(`the Routes API answered ${r.status}${msg ? ': ' + msg : ''}`);
  }
  let rows = [];
  try { rows = JSON.parse(txt); } catch { throw new Error('the Routes API answered in a shape we cannot read'); }
  if (!Array.isArray(rows)) throw new Error('the Routes API answered in a shape we cannot read');
  const n = points.length, min = [], miles = [];
  for (let i = 0; i < n; i++) { min.push(new Array(n).fill(null)); miles.push(new Array(n).fill(null)); min[i][i] = 0; miles[i][i] = 0; }
  rows.forEach(e => {
    const i = e.originIndex || 0, j = e.destinationIndex || 0;
    if (i >= n || j >= n || (e.condition && e.condition !== 'ROUTE_EXISTS')) return;
    const s = parseFloat(String(e.duration || '').replace(/s$/, ''));
    if (isFinite(s)) min[i][j] = Math.round(s / 6) / 10;
    if (isFinite(+e.distanceMeters)) miles[i][j] = Math.round((+e.distanceMeters / 1609.34) * 100) / 100;
  });
  return {min, miles, departure: body.departureTime || ''};
}

export default async (req) => {
  if (req.method !== 'POST') return json(405, {error: 'POST only'});
  const who = await caller(req);
  if (who instanceof Response) return who;
  let b; try { b = await req.json(); } catch { return json(400, {error: 'bad JSON'}); }
  const pts = Array.isArray(b && b.points) ? b.points : [];
  if (pts.length < 2) return json(400, {error: 'two stops or more'});
  if (pts.length > MAX_POINTS) return json(413, {ok: false, why: `At most ${MAX_POINTS} stops in one request: split the day into two routes`});
  if (pts.some(p => !p || !isFinite(+p.lat) || !isFinite(+p.lng) || Math.abs(+p.lat) > 90 || Math.abs(+p.lng) > 180)) return json(400, {error: 'every stop needs a latitude and a longitude'});
  const key = process.env.GOOGLE_MAPS_KEY;
  if (!key) return json(200, {ok: false, provider: 'offline', why: NO_KEY});
  try {
    const M = await routeMatrix(pts, b.departAt, key);
    return json(200, {ok: true, provider: 'google', ...M});
  } catch (e) {
    return json(200, {ok: false, provider: 'offline', why: 'Drive times stay estimated: ' + String(e.message || e).slice(0, 200)});
  }
};
export const config = {path: '/api/routes'};
