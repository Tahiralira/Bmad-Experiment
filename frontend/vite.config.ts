import path from "node:path"
import tailwindcss from "@tailwindcss/vite"
import { tanstackRouter } from "@tanstack/router-plugin/vite"
import react from "@vitejs/plugin-react-swc"
import { VitePWA } from "vite-plugin-pwa"
import { defineConfig } from "vitest/config"

// https://vitejs.dev/config/
export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  plugins: [
    tanstackRouter({
      target: "react",
      autoCodeSplitting: true,
    }),
    react(),
    tailwindcss(),
    /**
     * PWA install shell (WS11).
     *
     * Scope is deliberately narrow: this makes ClearDues installable and gives
     * it a service worker — the prerequisite for web push in WS12 — and
     * nothing more. **Offline data is explicitly out of scope.** API responses
     * are never cached: a stale balance shown as current is worse than no
     * balance at all in an app about who owes whom.
     */
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["favicon.svg", "apple-touch-icon.png"],
      manifest: {
        name: "ClearDues",
        short_name: "ClearDues",
        description:
          "ClearDues keeps score of shared expenses so you never have to ask.",
        start_url: "/",
        scope: "/",
        display: "standalone",
        orientation: "portrait",
        // Quiet Ink light ground; the in-page <meta name="theme-color">
        // still switches per colour scheme, which the manifest cannot do.
        theme_color: "#FCFCFB",
        background_color: "#FCFCFB",
        icons: [
          {
            src: "/pwa-192x192.png",
            sizes: "192x192",
            type: "image/png",
            purpose: "any",
          },
          {
            src: "/pwa-512x512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "any",
          },
          {
            src: "/pwa-maskable-512x512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "maskable",
          },
        ],
      },
      workbox: {
        // The shell only — JS, CSS, HTML, icons.
        globPatterns: ["**/*.{js,css,html,svg,png,ico,woff2}"],
        // Never let the SW answer for the API, and never hand a cached
        // index.html to an /api request.
        navigateFallbackDenylist: [/^\/api\//],
        runtimeCaching: [],
        cleanupOutdatedCaches: true,
        // WS12: pull the push/notificationclick handlers into the generated
        // SW. importScripts keeps WS11's generateSW precache (and its
        // "never answer for /api" rules) untouched — switching to
        // injectManifest to add two listeners would put that whole policy
        // back in hand-written code.
        importScripts: ["/push-sw.js"],
      },
      devOptions: {
        // Keep the SW out of `npm run dev`; a stale precache during hot
        // reload is pure confusion.
        enabled: false,
      },
    }),
  ],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          "vendor-react": ["react", "react-dom"],
          "vendor-tanstack": [
            "@tanstack/react-router",
            "@tanstack/react-query",
            "@tanstack/react-table",
          ],
          "vendor-forms": ["react-hook-form", "zod", "@hookform/resolvers"],
        },
      },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
  },
})
