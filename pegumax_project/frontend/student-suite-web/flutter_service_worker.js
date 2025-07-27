'use strict';
const MANIFEST = 'flutter-app-manifest';
const TEMP = 'flutter-temp-cache';
const CACHE_NAME = 'flutter-app-cache';

const RESOURCES = {"assets/AssetManifest.bin": "4b05e3ffd4819bb1984bb6346077e0f3",
"assets/AssetManifest.bin.json": "209cfba1c314666aff6a743c367f2852",
"assets/AssetManifest.json": "8b3a0c2cf32199427615a6f3e1a995a1",
"assets/assets/fonts/latosce.ttf": "6f81d0fdd6cc3e2effe138210c278603",
"assets/assets/fonts/Metamorphous-Regular.ttf": "2f1070bd8ec6dcc73b2de36ad3a577c4",
"assets/assets/fonts/Montserrat-Bold.ttf": "d3085f686df272f9e1a267cc69b2d24f",
"assets/assets/fonts/Montserrat-Regular.ttf": "07689d4eaaa3d530d58826b5d7f84735",
"assets/assets/fonts/Pacifico.ttf": "9b79bde19b07cbc80daeff1aaa085b5c",
"assets/assets/fonts/Roboto-Black.ttf": "a77b7fc4cf040eb5bb26b0685893a9df",
"assets/assets/fonts/Roboto-BlackItalic.ttf": "4ed7470bb05534191cd12d87cc02c598",
"assets/assets/fonts/Roboto-Bold.ttf": "afa7a91dadd77b23634a0fdf18c148f3",
"assets/assets/fonts/Roboto-BoldItalic.ttf": "d0108b3d28ce9d0261b33838cdf5ce68",
"assets/assets/fonts/Roboto-Italic.ttf": "2991e14ab958afe393cf5815cd4e6915",
"assets/assets/fonts/Roboto-Light.ttf": "e22062b3188c8199283ef2aa835d4653",
"assets/assets/fonts/Roboto-LightItalic.ttf": "1e27387f589f7cce254e05151df253bc",
"assets/assets/fonts/Roboto-Medium.ttf": "99fc0816a09395454061301fefa42bf1",
"assets/assets/fonts/Roboto-MediumItalic.ttf": "a0338073eed8fa60d0a779b3980d2cf0",
"assets/assets/fonts/Roboto-Regular.ttf": "54a91b0619ccf9373d525109268219dc",
"assets/assets/fonts/Roboto-Thin.ttf": "5ecbc99d1a81fed7dc71cb068ec0a74d",
"assets/assets/fonts/Roboto-ThinItalic.ttf": "84e36ae92150293a5a61f5eb1e1b3d6c",
"assets/assets/img/beach.jpg": "c01c363237ad2343292a71adaacc5f82",
"assets/assets/img/frames/flowers.png": "bd4cc1aaf2660be28376771ea9607a07",
"assets/assets/img/frames/meta.png": "5dab06e2cb589985475dc521bd7851d5",
"assets/assets/img/frames/student.png": "bb178d95f9a274f9c71641e26352729e",
"assets/assets/img/frames/tech.png": "ffd487f35d4e4ed249edbe1f28442e65",
"assets/assets/img/space.jpg": "a5127978854f84b5e00f5ca79e652a39",
"assets/assets/img/tech.jpg": "343c6ab219593bc20c1f440a18c662ce",
"assets/assets/models/mistral-7b-instruct-v0.1.Q4_K_M.gguf": "9cfab7b0e378473415241229dad8de47",
"assets/assets/models/Phi-3-mini-4k-instruct-Q4_K_M.gguf": "b2e3e618dc7f98975e64d249c3e266f7",
"assets/FontManifest.json": "f471746692c59cbee893e0b2250d9c94",
"assets/fonts/MaterialIcons-Regular.otf": "8b8332b307ed53f85e5696c800b7db51",
"assets/NOTICES": "485ecf934a603c638ebe0a7a771176ab",
"assets/packages/cupertino_icons/assets/CupertinoIcons.ttf": "33b7d9392238c04c131b6ce224e13711",
"assets/shaders/ink_sparkle.frag": "ecc85a2e95f5e9f53123dcaf8cb9b6ce",
"canvaskit/canvaskit.js": "728b2d477d9b8c14593d4f9b82b484f3",
"canvaskit/canvaskit.js.symbols": "bdcd3835edf8586b6d6edfce8749fb77",
"canvaskit/canvaskit.wasm": "7a3f4ae7d65fc1de6a6e7ddd3224bc93",
"canvaskit/chromium/canvaskit.js": "8191e843020c832c9cf8852a4b909d4c",
"canvaskit/chromium/canvaskit.js.symbols": "b61b5f4673c9698029fa0a746a9ad581",
"canvaskit/chromium/canvaskit.wasm": "f504de372e31c8031018a9ec0a9ef5f0",
"canvaskit/skwasm.js": "ea559890a088fe28b4ddf70e17e60052",
"canvaskit/skwasm.js.symbols": "e72c79950c8a8483d826a7f0560573a1",
"canvaskit/skwasm.wasm": "39dd80367a4e71582d234948adc521c0",
"favicon.png": "5dcef449791fa27946b3d35ad8803796",
"flutter.js": "83d881c1dbb6d6bcd6b42e274605b69c",
"flutter_bootstrap.js": "acc607a431b471eaef23fe7b2dac9b1e",
"icons/Icon-192.png": "ac9a721a12bbc803b44f645561ecb1e1",
"icons/Icon-512.png": "96e752610906ba2a93c65f8abe1645f1",
"icons/Icon-maskable-192.png": "c457ef57daa1d16f64b27b786ec2ea3c",
"icons/Icon-maskable-512.png": "301a7604d45b3e739efc881eb04896ea",
"index.html": "c8341f72cd6165b2752b0be823124c0c",
"/": "c8341f72cd6165b2752b0be823124c0c",
"main.dart.js": "6dfd39a18e17291fe89ff8f02548ac38",
"manifest.json": "1c24408fd60d547d321e4d36e24caa15",
"version.json": "4116d92fd5768e7de325363b0ee68073"};
// The application shell files that are downloaded before a service worker can
// start.
const CORE = ["main.dart.js",
"index.html",
"flutter_bootstrap.js",
"assets/AssetManifest.bin.json",
"assets/FontManifest.json"];

// During install, the TEMP cache is populated with the application shell files.
self.addEventListener("install", (event) => {
  self.skipWaiting();
  return event.waitUntil(
    caches.open(TEMP).then((cache) => {
      return cache.addAll(
        CORE.map((value) => new Request(value, {'cache': 'reload'})));
    })
  );
});
// During activate, the cache is populated with the temp files downloaded in
// install. If this service worker is upgrading from one with a saved
// MANIFEST, then use this to retain unchanged resource files.
self.addEventListener("activate", function(event) {
  return event.waitUntil(async function() {
    try {
      var contentCache = await caches.open(CACHE_NAME);
      var tempCache = await caches.open(TEMP);
      var manifestCache = await caches.open(MANIFEST);
      var manifest = await manifestCache.match('manifest');
      // When there is no prior manifest, clear the entire cache.
      if (!manifest) {
        await caches.delete(CACHE_NAME);
        contentCache = await caches.open(CACHE_NAME);
        for (var request of await tempCache.keys()) {
          var response = await tempCache.match(request);
          await contentCache.put(request, response);
        }
        await caches.delete(TEMP);
        // Save the manifest to make future upgrades efficient.
        await manifestCache.put('manifest', new Response(JSON.stringify(RESOURCES)));
        // Claim client to enable caching on first launch
        self.clients.claim();
        return;
      }
      var oldManifest = await manifest.json();
      var origin = self.location.origin;
      for (var request of await contentCache.keys()) {
        var key = request.url.substring(origin.length + 1);
        if (key == "") {
          key = "/";
        }
        // If a resource from the old manifest is not in the new cache, or if
        // the MD5 sum has changed, delete it. Otherwise the resource is left
        // in the cache and can be reused by the new service worker.
        if (!RESOURCES[key] || RESOURCES[key] != oldManifest[key]) {
          await contentCache.delete(request);
        }
      }
      // Populate the cache with the app shell TEMP files, potentially overwriting
      // cache files preserved above.
      for (var request of await tempCache.keys()) {
        var response = await tempCache.match(request);
        await contentCache.put(request, response);
      }
      await caches.delete(TEMP);
      // Save the manifest to make future upgrades efficient.
      await manifestCache.put('manifest', new Response(JSON.stringify(RESOURCES)));
      // Claim client to enable caching on first launch
      self.clients.claim();
      return;
    } catch (err) {
      // On an unhandled exception the state of the cache cannot be guaranteed.
      console.error('Failed to upgrade service worker: ' + err);
      await caches.delete(CACHE_NAME);
      await caches.delete(TEMP);
      await caches.delete(MANIFEST);
    }
  }());
});
// The fetch handler redirects requests for RESOURCE files to the service
// worker cache.
self.addEventListener("fetch", (event) => {
  if (event.request.method !== 'GET') {
    return;
  }
  var origin = self.location.origin;
  var key = event.request.url.substring(origin.length + 1);
  // Redirect URLs to the index.html
  if (key.indexOf('?v=') != -1) {
    key = key.split('?v=')[0];
  }
  if (event.request.url == origin || event.request.url.startsWith(origin + '/#') || key == '') {
    key = '/';
  }
  // If the URL is not the RESOURCE list then return to signal that the
  // browser should take over.
  if (!RESOURCES[key]) {
    return;
  }
  // If the URL is the index.html, perform an online-first request.
  if (key == '/') {
    return onlineFirst(event);
  }
  event.respondWith(caches.open(CACHE_NAME)
    .then((cache) =>  {
      return cache.match(event.request).then((response) => {
        // Either respond with the cached resource, or perform a fetch and
        // lazily populate the cache only if the resource was successfully fetched.
        return response || fetch(event.request).then((response) => {
          if (response && Boolean(response.ok)) {
            cache.put(event.request, response.clone());
          }
          return response;
        });
      })
    })
  );
});
self.addEventListener('message', (event) => {
  // SkipWaiting can be used to immediately activate a waiting service worker.
  // This will also require a page refresh triggered by the main worker.
  if (event.data === 'skipWaiting') {
    self.skipWaiting();
    return;
  }
  if (event.data === 'downloadOffline') {
    downloadOffline();
    return;
  }
});
// Download offline will check the RESOURCES for all files not in the cache
// and populate them.
async function downloadOffline() {
  var resources = [];
  var contentCache = await caches.open(CACHE_NAME);
  var currentContent = {};
  for (var request of await contentCache.keys()) {
    var key = request.url.substring(origin.length + 1);
    if (key == "") {
      key = "/";
    }
    currentContent[key] = true;
  }
  for (var resourceKey of Object.keys(RESOURCES)) {
    if (!currentContent[resourceKey]) {
      resources.push(resourceKey);
    }
  }
  return contentCache.addAll(resources);
}
// Attempt to download the resource online before falling back to
// the offline cache.
function onlineFirst(event) {
  return event.respondWith(
    fetch(event.request).then((response) => {
      return caches.open(CACHE_NAME).then((cache) => {
        cache.put(event.request, response.clone());
        return response;
      });
    }).catch((error) => {
      return caches.open(CACHE_NAME).then((cache) => {
        return cache.match(event.request).then((response) => {
          if (response != null) {
            return response;
          }
          throw error;
        });
      });
    })
  );
}
