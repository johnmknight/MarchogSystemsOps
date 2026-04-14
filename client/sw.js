// MarchogSystemsOps service worker
//
// Caches the Shell for offline kiosk use with a version-aware cache name.
// The server substitutes `{{BUILD_VERSION}}` into this file at request time
// (see /sw.js route in server/main.py), so every build gets its own cache
// namespace. On activate we evict any `marchog-*` caches that don't match
// the current build, which guarantees the kiosk won't serve stale pages
// from a previous deploy after a reload.

const BUILD_VERSION = '{{BUILD_VERSION}}';
const CACHE_NAME = 'marchog-' + BUILD_VERSION;

self.addEventListener('install', (event) => {
  // skipWaiting() + clients.claim() together mean a new SW activates
  // immediately instead of waiting for every client to close. This is
  // what lets `/api/screens/reload-all` actually swap in new code on
  // already-running kiosks without manual refresh.
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    (async () => {
      // Evict any marchog-* caches whose version no longer matches ours
      const keys = await caches.keys();
      await Promise.all(keys.map(k => {
        if (k.startsWith('marchog-') && k !== CACHE_NAME) {
          console.log('[sw] Evicting stale cache:', k);
          return caches.delete(k);
        }
      }));
      await clients.claim();
    })()
  );
});

self.addEventListener('fetch', (event) => {
  // Network-first strategy — always try live server, fall back to cache.
  // Critical for kiosks so that config changes propagate immediately.
  event.respondWith(
    fetch(event.request)
      .then(response => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});
