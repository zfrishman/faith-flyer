const C='faithflyer-v3',F=['./','index.html','manifest.webmanifest','icon-180.png','icon-192.png','icon-512.png','art/bg-eden.webp','art/bg-noah.webp','art/end-tree.webp','art/end-ark.webp','art/plane-1.png','art/plane-2.png','art/plane-3.png','art/plane-4.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(F)));self.skipWaiting()});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==C).map(x=>caches.delete(x)))));self.clients.claim()});
self.addEventListener('fetch',e=>{e.respondWith(caches.match(e.request,{ignoreSearch:true}).then(r=>r||fetch(e.request)))});
