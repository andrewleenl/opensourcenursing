const CACHE_NAME = 'osn-pwa-v1';
const CORE_ASSETS = [
  './',
  './index.html',
  './ehrsim.html',
  './manifest.json',
  './icon.svg',
  './icon-192.png',
  './icon-512.png'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(CORE_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);

  // Skip caching large binary downloads (.pptx, .pdf) so student device storage isn't exhausted
  if (url.pathname.endsWith('.pptx') || url.pathname.endsWith('.pdf')) {
    return;
  }

  // Network-first for HTML pages and local assets, falling back to cache when offline
  event.respondWith(
    fetch(req)
      .then(networkRes => {
        if (networkRes && networkRes.status === 200 && url.origin === location.origin) {
          const copy = networkRes.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(req, copy));
        }
        return networkRes;
      })
      .catch(() => caches.match(req).then(cached => cached || caches.match('./index.html')))
  );
});
