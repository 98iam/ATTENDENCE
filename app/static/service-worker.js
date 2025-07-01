const CACHE_NAME = 'attendance-app-cache-v1';
const urlsToCache = [
  '/',
  '/static/css/style.css',
  // Add other important static assets here - e.g., core JS files, logo if any
  // The manifest and icons are often cached implicitly or handled by browser, but good to list key ones.
  '/static/manifest.json',
  '/static/icons/icon-192x192.png', // Assuming you've created these PNGs
  '/static/icons/icon-512x512.png'  // Assuming you've created these PNGs
];

// Pages that should be available offline (these need to be actual routes)
// For a Flask app, these are often dynamic, so caching strategies might need to be more nuanced.
// Start with caching the main entry points that are mostly static or can show some offline content.
const offlinePages = [
  '/', // Assuming this is your main dashboard or redirects to it
  '/dashboard', // If you have a /dashboard route
  // Add other key pages you want to be accessible offline
  // e.g., '/attendance', '/history', '/marks_entry', '/all_marks'
  // Be mindful that dynamic content fetched from backend won't be live offline unless API responses are also cached.
];

self.addEventListener('install', event => {
  console.log('[ServiceWorker] Install');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[ServiceWorker] Caching app shell');
        const allToCache = [...new Set([...urlsToCache, ...offlinePages])];
        return cache.addAll(allToCache.map(url => new Request(url, { cache: 'reload' }))); // Force network request for initial caching
      })
      .catch(error => {
        console.error('[ServiceWorker] Failed to cache resources during install:', error);
      })
  );
});

self.addEventListener('activate', event => {
  console.log('[ServiceWorker] Activate');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('[ServiceWorker] Clearing old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  return self.clients.claim();
});

self.addEventListener('fetch', event => {
  const requestUrl = new URL(event.request.url);

  // Serve API calls from network always (or define specific caching for them if needed)
  // This is a simple check; adjust if your API routes are different
  if (event.request.method !== 'GET' || requestUrl.pathname.startsWith('/api/') || requestUrl.pathname.startsWith('/get_') || requestUrl.pathname.startsWith('/save_') || requestUrl.pathname.startsWith('/mark_') || requestUrl.pathname.startsWith('/delete_') || requestUrl.pathname.startsWith('/update_') || requestUrl.pathname.startsWith('/add_') || requestUrl.pathname.startsWith('/clear_')) {
    event.respondWith(fetch(event.request));
    return;
  }

  // For HTML pages (navigation requests), try network first, then cache, then offline fallback.
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          // If response is good, cache it (optional, for dynamic content)
          // Be careful caching all navigated pages, might fill up cache quickly.
          // For now, we rely on the initial offlinePages caching.
          return response;
        })
        .catch(() => {
          // Network failed, try to serve from cache
          return caches.match(event.request)
            .then(cachedResponse => {
              if (cachedResponse) {
                return cachedResponse;
              }
              // If specific page not in cache, try to return a generic offline page
              // return caches.match('/offline.html'); // You would need to create an offline.html
              // For now, if not in cache, it will just fail like normal offline.
              console.warn('[ServiceWorker] Page not in cache and network failed:', event.request.url);
              return new Response('<h1>You are offline</h1><p>This page is not available offline.</p>', { headers: { 'Content-Type': 'text/html' } });
            })
        })
    );
    return;
  }

  // For other static assets (CSS, JS, images), use cache-first strategy
  event.respondWith(
    caches.match(event.request)
      .then(cachedResponse => {
        if (cachedResponse) {
          return cachedResponse;
        }
        return fetch(event.request).then(
          response => {
            // Check if we received a valid response
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }

            // IMPORTANT: Clone the response. A response is a stream
            // and because we want the browser to consume the response
            // as well as the cache consuming the response, we need
            // to clone it so we have two streams.
            var responseToCache = response.clone();

            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(event.request, responseToCache);
              });

            return response;
          }
        );
      })
  );
});

// Optional: Listen for messages from client to skip waiting
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
