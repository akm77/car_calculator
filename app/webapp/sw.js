// Service Worker для оффлайн работы калькулятора
const CACHE_NAME = 'car-calculator-v1';
const urlsToCache = [
  '/',
  '/manifest.json',
  'https://telegram.org/js/telegram-web-app.js'
];

// Установка Service Worker
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        return cache.addAll(urlsToCache);
      })
  );
});

// Обработка запросов
self.addEventListener('fetch', function(event) {
  // Skip non-GET requests and Chrome extension requests
  if (event.request.method !== 'GET' || event.request.url.includes('chrome-extension://')) {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then(function(response) {
        // Возвращаем кэшированную версию или делаем запрос к сети
        if (response) {
          return response;
        }

        // Clone request and allow redirects
        return fetch(event.request.clone(), {
          redirect: 'follow'
        }).catch(function(error) {
          console.log('Fetch failed; returning offline page instead.', error);
          // Could return a custom offline page here
        });
      }
    )
  );
});

// Обновление кэша
self.addEventListener('activate', function(event) {
  const cacheWhitelist = [CACHE_NAME];

  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});
