// Service Worker for EasyMeal PWA
const CACHE_NAME = 'easymeal-v9';
const STATIC_CACHE = 'easymeal-static-v9';
const API_CACHE = 'easymeal-api-v9';

// Files to cache on install
const STATIC_FILES = [
  '/easymeal/',
  '/easymeal/static/index.html',
  '/easymeal/static/style.css',
  '/easymeal/static/app.js',
  '/easymeal/static/manifest.json'
];

// Install event - cache static files
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing...');
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => {
      console.log('[Service Worker] Caching static files');
      return cache.addAll(STATIC_FILES);
    })
  );
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== STATIC_CACHE && cacheName !== API_CACHE) {
            console.log('[Service Worker] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  return self.clients.claim();
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // Ensure HTTPS for all requests (fix mixed content)
  // This handles both absolute HTTP URLs and relative URLs that resolve to HTTP
  if (url.protocol === 'http:' && url.hostname === self.location.hostname) {
    url.protocol = 'https:';
    // Create new request with HTTPS URL, preserving all request properties
    const newRequestInit = {
      method: event.request.method,
      headers: event.request.headers,
      mode: event.request.mode,
      credentials: event.request.credentials,
      cache: event.request.cache,
      redirect: event.request.redirect,
      referrer: event.request.referrer,
      body: event.request.body,
      bodyUsed: event.request.bodyUsed,
      referrerPolicy: event.request.referrerPolicy
    };
    const newRequest = new Request(url.toString(), newRequestInit);
    event.respondWith(fetch(newRequest));
    return;
  }
  
  // Skip cross-origin requests
  if (url.origin !== self.location.origin) {
    return;
  }
  
  // API requests - network first, then cache
  if (url.pathname.startsWith('/easymeal/api/')) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          // Clone the response
          const responseClone = response.clone();
          
          // Cache successful GET requests
          if (event.request.method === 'GET' && response.status === 200) {
            caches.open(API_CACHE).then((cache) => {
              cache.put(event.request, responseClone);
            });
          }
          
          return response;
        })
        .catch(() => {
          // Network failed, try cache
          return caches.match(event.request).then((cachedResponse) => {
            if (cachedResponse) {
              return cachedResponse;
            }
            // Return offline response for API calls
            if (event.request.headers.get('accept') && event.request.headers.get('accept').includes('application/json')) {
              return new Response(
                JSON.stringify({ error: 'Offline', message: 'You are currently offline' }),
                {
                  status: 503,
                  headers: { 'Content-Type': 'application/json' }
                }
              );
            }
          });
        })
    );
    return;
  }
  
  // Static files - cache first, then network
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      
      return fetch(event.request).then((response) => {
        // Don't cache if not a valid response
        if (!response || response.status !== 200 || response.type !== 'basic') {
          return response;
        }
        
        // Clone the response
        const responseToCache = response.clone();
        
        caches.open(STATIC_CACHE).then((cache) => {
          cache.put(event.request, responseToCache);
        });
        
        return response;
      });
    })
  );
});

// Background sync for offline actions (future enhancement)
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-meals') {
    event.waitUntil(syncMeals());
  }
});

async function syncMeals() {
  // This would sync any pending offline actions
  console.log('[Service Worker] Syncing meals...');
}

