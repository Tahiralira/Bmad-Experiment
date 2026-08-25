/**
 * Web Push handlers for the ClearDues service worker (WS12).
 *
 * This file is pulled into the generated service worker via workbox's
 * `importScripts` (see vite.config.ts) rather than by switching the PWA
 * plugin to `injectManifest`. That keeps WS11's generated precache — and
 * its deliberate "never cache the API" rules — exactly as they are, and
 * confines push to the one concern it owns.
 *
 * It is served from /public verbatim, so it must be plain ES5-safe JS with
 * no bundler transforms: nothing here goes through Vite.
 */

/* global self, clients */

self.addEventListener("push", (event) => {
  if (!event.data) return

  let payload
  try {
    payload = event.data.json()
  } catch (err) {
    // A push with an unreadable body still has to show something — Chrome
    // revokes push permission from workers that receive a message and
    // display nothing.
    payload = { title: "ClearDues", body: "You have an update." }
  }

  const title = payload.title || "ClearDues"
  const options = {
    body: payload.body || "",
    icon: "/pwa-192x192.png",
    badge: "/pwa-192x192.png",
    // Same tag = the new nudge REPLACES the old one for that group rather
    // than stacking. A reminder engine that piles up notifications is the
    // nagging this product exists not to do.
    tag: payload.tag || "cleardues",
    renotify: false,
    data: { url: payload.url || "/" },
  }

  event.waitUntil(self.registration.showNotification(title, options))
})

self.addEventListener("notificationclick", (event) => {
  event.notification.close()
  const target = (event.notification.data && event.notification.data.url) || "/"

  event.waitUntil(
    clients
      .matchAll({ type: "window", includeUncontrolled: true })
      .then((windowClients) => {
        // Prefer focusing a tab that's already open — opening a second copy
        // of an installed PWA is disorienting.
        for (const client of windowClients) {
          if ("focus" in client) {
            client.navigate(target)
            return client.focus()
          }
        }
        if (clients.openWindow) {
          return clients.openWindow(target)
        }
        return undefined
      }),
  )
})
