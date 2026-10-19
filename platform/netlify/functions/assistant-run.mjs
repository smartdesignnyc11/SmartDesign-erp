// Weekdays at 7:20, 12:20 and 16:20 New York (11:20, 16:20, 20:20 UTC in summer time; an hour earlier in winter): each
// office person's assistant reads their day and writes them a briefing and drafts. The morning run may notify a phone.
import {assistantKey} from './assistant-background.mjs';
export default async () => {
  const base = process.env.URL || 'https://smartdesigns-erp.netlify.app';
  const morning = new Date().getUTCHours() < 13;
  const r = await fetch(base + '/.netlify/functions/assistant-background', {method: 'POST', headers: {'x-assistant-key': assistantKey(), 'content-type': 'application/json'}, body: JSON.stringify({ws: 'smartdesign', push: morning})});
  console.log('assistant runs started', r.status);
  return new Response('ok');
};
export const config = {schedule: '20 11,16,20 * * 1-5'};
