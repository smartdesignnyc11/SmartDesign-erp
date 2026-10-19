// Web push to every phone or browser a person turned notifications on for. A subscription the push service has
// dropped (404/410) is deleted; other failures are counted.
import webpush from 'web-push';
import {rest} from './auth.mjs';
export async function pushTo(personKey, msg) {
  if (!msg || !process.env.VAPID_PRIVATE_KEY) return 0;
  webpush.setVapidDetails('mailto:alan@smartdesign.nyc', process.env.VAPID_PUBLIC_KEY, process.env.VAPID_PRIVATE_KEY);
  const subs = await rest('push_subs?select=endpoint,sub,fails&person_key=eq.' + encodeURIComponent(personKey));
  let sent = 0;
  for (const s of subs || []) {
    const ep = 'push_subs?endpoint=eq.' + encodeURIComponent(s.endpoint);
    try {
      await webpush.sendNotification(s.sub, JSON.stringify(msg), {TTL: 6 * 3600, urgency: 'normal'});
      sent++; await rest(ep, {method: 'PATCH', headers: {prefer: 'return=minimal'}, body: JSON.stringify({last_ok: new Date().toISOString(), fails: 0})});
    } catch (e) {
      if (e.statusCode === 404 || e.statusCode === 410) await rest(ep, {method: 'DELETE'});
      else await rest(ep, {method: 'PATCH', headers: {prefer: 'return=minimal'}, body: JSON.stringify({fails: (s.fails || 0) + 1})});
    }
  }
  return sent;
}
