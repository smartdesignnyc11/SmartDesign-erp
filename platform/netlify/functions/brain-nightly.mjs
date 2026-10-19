// Every night at 03:07 New York (07:07 UTC; 02:07 in winter): start the Brain's run for the firm.
import {brainKey} from './brain-background.mjs';
export default async () => {
  const base = process.env.URL || 'https://smartdesigns-erp.netlify.app';
  const r = await fetch(base + '/.netlify/functions/brain-background', {method: 'POST', headers: {'x-brain-key': brainKey(), 'content-type': 'application/json'}, body: JSON.stringify({ws: 'smartdesign'})});
  console.log('brain started', r.status);
  return new Response('ok');
};
export const config = {schedule: '7 7 * * *'};
