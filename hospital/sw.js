/* Offline cache for the EHR simulator (2D). Bumped automatically on every build. */
const CACHE = 'ehrsim2d-eb11af08d2';
const FILES = ['./', './index.html', './index.js', './index.pck', './index.wasm.gz', './index.audio.worklet.js', './index.audio.position.worklet.js', './index.apple-touch-icon.png', './index.icon.png'];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).catch(() => {})); self.skipWaiting(); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith('ehrsim2d-') && k !== CACHE).map(k => caches.delete(k))))); self.clients.claim(); });
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(fetch(e.request).then(r => { if (r.ok && new URL(e.request.url).origin === location.origin) { const c = r.clone(); caches.open(CACHE).then(x => x.put(e.request, c)); } return r; })
    .catch(() => caches.match(e.request, { ignoreSearch: true })));
});
