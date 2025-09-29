// EstateCore Mobile PWA Service Worker
// Advanced offline-first architecture with background sync and push notifications

const CACHE_NAME = 'estatecore-mobile-v1.0.0';
const DATA_CACHE_NAME = 'estatecore-data-v1.0.0';
const STATIC_CACHE_NAME = 'estatecore-static-v1.0.0';

// Define what to cache
const STATIC_FILES = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  '/offline.html',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png'
];

const API_CACHE_PATTERNS = [
  /\/api\/properties/,
  /\/api\/tenants/,
  /\/api\/maintenance/,
  /\/api\/collaboration/,
  /\/api\/analytics/
];

const CACHE_FIRST_PATTERNS = [
  /\/static\//,
  /\/icons\//,
  /\/images\//,
  /\.(?:png|jpg|jpeg|svg|gif|webp|ico|woff2?|ttf|eot)$/
];

const NETWORK_FIRST_PATTERNS = [
  /\/api\/auth/,
  /\/api\/payments/,
  /\/api\/integrations/
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker');
  
  event.waitUntil(
    Promise.all([
      // Cache static files
      caches.open(STATIC_CACHE_NAME).then((cache) => {
        console.log('[SW] Caching static files');
        return cache.addAll(STATIC_FILES);
      }),
      
      // Skip waiting to activate immediately
      self.skipWaiting()
    ])
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker');
  
  event.waitUntil(
    Promise.all([
      // Clean up old caches
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME && 
                cacheName !== DATA_CACHE_NAME && 
                cacheName !== STATIC_CACHE_NAME) {
              console.log('[SW] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      }),
      
      // Claim all clients
      self.clients.claim()
    ])
  );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-HTTP requests
  if (!request.url.startsWith('http')) {
    return;
  }
  
  // Handle different types of requests with appropriate strategies
  if (CACHE_FIRST_PATTERNS.some(pattern => pattern.test(url.pathname))) {
    // Cache First - static assets
    event.respondWith(cacheFirst(request));
  } else if (NETWORK_FIRST_PATTERNS.some(pattern => pattern.test(url.pathname))) {
    // Network First - critical API calls
    event.respondWith(networkFirst(request));
  } else if (API_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname))) {
    // Stale While Revalidate - API data
    event.respondWith(staleWhileRevalidate(request));
  } else if (request.mode === 'navigate') {
    // Network First for navigation with offline fallback
    event.respondWith(handleNavigationRequest(request));
  } else {
    // Default to network with cache fallback
    event.respondWith(networkWithCacheFallback(request));
  }
});

// Caching Strategies

async function cacheFirst(request) {
  try {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(STATIC_CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.error('[SW] Cache first error:', error);
    return new Response('Offline', { status: 503 });
  }
}

async function networkFirst(request) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(DATA_CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.log('[SW] Network first fallback to cache:', request.url);
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    throw error;
  }
}

async function staleWhileRevalidate(request) {
  const cache = await caches.open(DATA_CACHE_NAME);
  const cachedResponse = await cache.match(request);
  
  // Fetch from network in background
  const networkResponsePromise = fetch(request).then((networkResponse) => {
    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  }).catch(() => {
    // Network failed, but we might have cache
    return null;
  });
  
  // Return cached version immediately if available
  if (cachedResponse) {
    return cachedResponse;
  }
  
  // Wait for network if no cache
  return networkResponsePromise || new Response('Offline', { status: 503 });
}

async function networkWithCacheFallback(request) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    throw error;
  }
}

async function handleNavigationRequest(request) {
  try {
    const networkResponse = await fetch(request);
    return networkResponse;
  } catch (error) {
    // Return cached page or offline page
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return offline page
    return caches.match('/offline.html');
  }
}

// Background Sync for offline actions
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync triggered:', event.tag);
  
  if (event.tag === 'property-sync') {
    event.waitUntil(syncProperties());
  } else if (event.tag === 'inspection-sync') {
    event.waitUntil(syncInspections());
  } else if (event.tag === 'message-sync') {
    event.waitUntil(syncMessages());
  }
});

async function syncProperties() {
  try {
    console.log('[SW] Syncing properties');
    
    // Get pending property updates from IndexedDB
    const db = await openIndexedDB();
    const pendingUpdates = await getPendingUpdates(db, 'properties');
    
    for (const update of pendingUpdates) {
      try {
        const response = await fetch('/api/properties/sync', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(update.data)
        });
        
        if (response.ok) {
          await removePendingUpdate(db, 'properties', update.id);
          console.log('[SW] Property synced:', update.id);
        }
      } catch (error) {
        console.error('[SW] Failed to sync property:', update.id, error);
      }
    }
  } catch (error) {
    console.error('[SW] Property sync failed:', error);
  }
}

async function syncInspections() {
  try {
    console.log('[SW] Syncing inspections');
    
    const db = await openIndexedDB();
    const pendingInspections = await getPendingUpdates(db, 'inspections');
    
    for (const inspection of pendingInspections) {
      try {
        const response = await fetch('/api/inspections/sync', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(inspection.data)
        });
        
        if (response.ok) {
          await removePendingUpdate(db, 'inspections', inspection.id);
          console.log('[SW] Inspection synced:', inspection.id);
        }
      } catch (error) {
        console.error('[SW] Failed to sync inspection:', inspection.id, error);
      }
    }
  } catch (error) {
    console.error('[SW] Inspection sync failed:', error);
  }
}

async function syncMessages() {
  try {
    console.log('[SW] Syncing messages');
    
    const db = await openIndexedDB();
    const pendingMessages = await getPendingUpdates(db, 'messages');
    
    for (const message of pendingMessages) {
      try {
        const response = await fetch('/api/collaboration/messages/sync', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(message.data)
        });
        
        if (response.ok) {
          await removePendingUpdate(db, 'messages', message.id);
          console.log('[SW] Message synced:', message.id);
        }
      } catch (error) {
        console.error('[SW] Failed to sync message:', message.id, error);
      }
    }
  } catch (error) {
    console.error('[SW] Message sync failed:', error);
  }
}

// Push Notifications
self.addEventListener('push', (event) => {
  console.log('[SW] Push notification received');
  
  const options = {
    badge: '/icons/badge-72x72.png',
    icon: '/icons/icon-192x192.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'view',
        title: 'View',
        icon: '/icons/view-icon.png'
      },
      {
        action: 'dismiss',
        title: 'Dismiss',
        icon: '/icons/dismiss-icon.png'
      }
    ]
  };
  
  if (event.data) {
    const data = event.data.json();
    options.title = data.title || 'EstateCore Notification';
    options.body = data.body || 'You have a new notification';
    options.tag = data.tag || 'default';
    options.data = { ...options.data, ...data };
  } else {
    options.title = 'EstateCore';
    options.body = 'You have a new notification';
  }
  
  event.waitUntil(
    self.registration.showNotification(options.title, options)
  );
});

// Notification Click Handler
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification clicked:', event.notification.tag);
  
  event.notification.close();
  
  if (event.action === 'view') {
    // Open the app to specific page
    const urlToOpen = event.notification.data?.url || '/';
    
    event.waitUntil(
      clients.matchAll({ type: 'window' }).then((clientList) => {
        // Check if app is already open
        for (const client of clientList) {
          if (client.url === urlToOpen && 'focus' in client) {
            return client.focus();
          }
        }
        
        // Open new window
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
    );
  }
});

// Share Target Handler
self.addEventListener('fetch', (event) => {
  if (event.request.url.endsWith('/share') && event.request.method === 'POST') {
    event.respondWith(handleSharedContent(event.request));
  }
});

async function handleSharedContent(request) {
  try {
    const formData = await request.formData();
    const title = formData.get('title') || '';
    const text = formData.get('text') || '';
    const url = formData.get('url') || '';
    const files = formData.getAll('documents');
    
    // Store shared content for the app to process
    const db = await openIndexedDB();
    const sharedContent = {
      id: Date.now(),
      title,
      text,
      url,
      files: files.map(file => ({
        name: file.name,
        type: file.type,
        size: file.size
      })),
      timestamp: new Date().toISOString()
    };
    
    await storeSharedContent(db, sharedContent);
    
    // Redirect to share handler page
    return Response.redirect('/share-handler', 303);
  } catch (error) {
    console.error('[SW] Share handling error:', error);
    return new Response('Share failed', { status: 500 });
  }
}

// IndexedDB Helper Functions
async function openIndexedDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('EstateCoreMobile', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      
      // Create object stores
      if (!db.objectStoreNames.contains('pendingUpdates')) {
        const updateStore = db.createObjectStore('pendingUpdates', { keyPath: 'id' });
        updateStore.createIndex('type', 'type', { unique: false });
      }
      
      if (!db.objectStoreNames.contains('sharedContent')) {
        db.createObjectStore('sharedContent', { keyPath: 'id' });
      }
      
      if (!db.objectStoreNames.contains('offlineData')) {
        const dataStore = db.createObjectStore('offlineData', { keyPath: 'key' });
        dataStore.createIndex('category', 'category', { unique: false });
      }
    };
  });
}

async function getPendingUpdates(db, type) {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['pendingUpdates'], 'readonly');
    const store = transaction.objectStore('pendingUpdates');
    const index = store.index('type');
    const request = index.getAll(type);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
  });
}

async function removePendingUpdate(db, type, id) {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['pendingUpdates'], 'readwrite');
    const store = transaction.objectStore('pendingUpdates');
    const request = store.delete(id);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve();
  });
}

async function storeSharedContent(db, content) {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['sharedContent'], 'readwrite');
    const store = transaction.objectStore('sharedContent');
    const request = store.add(content);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve();
  });
}

// Cleanup old data periodically
setInterval(async () => {
  try {
    const db = await openIndexedDB();
    
    // Clean up old cached data (older than 30 days)
    const cutoffDate = Date.now() - (30 * 24 * 60 * 60 * 1000);
    
    const transaction = db.transaction(['offlineData'], 'readwrite');
    const store = transaction.objectStore('offlineData');
    const request = store.openCursor();
    
    request.onsuccess = (event) => {
      const cursor = event.target.result;
      if (cursor) {
        if (cursor.value.timestamp < cutoffDate) {
          cursor.delete();
        }
        cursor.continue();
      }
    };
  } catch (error) {
    console.error('[SW] Cleanup error:', error);
  }
}, 24 * 60 * 60 * 1000); // Run daily

console.log('[SW] Service worker loaded successfully');