// Every night at 03:23 New York (07:23 UTC; 02:23 in winter), after the Brain: start the improvement loop's run.
import {loopKey} from './loop-background.mjs';
export default async () => {
  const base = process.env.URL || 'https://smartdesigns-erp.netlify.app';
  const r = await fetch(base + '/.netlify/functions/loop-background', {method: 'POST', headers: {'x-loop-key': loopKey(), 'content-type': 'application/json'}, body: JSON.stringify({ws: 'smartdesign'})});
  console.log('loop started', r.status);
  return new Response('ok');
};
export const config = {schedule: '23 7 * * *'};
