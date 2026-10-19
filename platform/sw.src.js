// Service worker: keeps the app shell so it opens fast and on a bad signal. It never caches data or /api calls,
// so one person's records can never be served to the next person on a shared phone. VERSION is set by build.py.
const VERSION = 'sdp-v1';
const SHELL = ['./', './index.html', './cloud.js', './config.js', './vendor/supabase.js', './manifest.webmanifest', './icons/icon-192.png', './icons/icon-512.png'];
self.addEventListener('install', e => { e.waitUntil(caches.open(VERSION).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== VERSION).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET') return;
  if (url.origin !== location.origin) return;            // Supabase, fonts: straight to the network
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/.netlify/')) return;
  // the shell: network first (so updates land), the cache when offline
  e.respondWith(fetch(e.request).then(r => { if (r.ok) { const copy = r.clone(); caches.open(VERSION).then(c => c.put(e.request, copy)); } return r; })
    .catch(() => caches.match(e.request).then(m => m || caches.match('./index.html'))));
});
// Push: the watcher's one notification per run. Tapping it opens the app (or brings an open copy forward).
self.addEventListener('push', e => {
  let m = {}; try { m = e.data ? e.data.json() : {}; } catch (err) { m = {title: 'SmartDesigns Projects', body: e.data ? e.data.text() : ''}; }
  e.waitUntil(self.registration.showNotification(m.title || 'SmartDesigns Projects', {body: m.body || '', icon: './icons/icon-192.png', badge: './icons/icon-192.png', tag: 'sdp-watch', renotify: true, data: {url: m.url || './'}}));
});
self.addEventListener('notificationclick', e => {
  e.notification.close();
  const url = (e.notification.data && e.notification.data.url) || './';
  e.waitUntil(self.clients.matchAll({type: 'window', includeUncontrolled: true}).then(cs => { const c = cs.find(x => 'focus' in x); return c ? c.focus() : self.clients.openWindow(url); }));
});
