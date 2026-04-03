// Track the Ticket — Service Worker
// Purpose: PWA installability only. No caching whatsoever.
// All requests go straight to the network.

self.addEventListener('install', () => {
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  // Clear any caches left from previous versions
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.map((k) => caches.delete(k))))
  )
  self.clients.claim()
})

// No fetch handler — all requests pass through to the network normally
