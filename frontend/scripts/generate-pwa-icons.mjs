/**
 * Rasterise the ClearDues mark into the PNG sizes a web app manifest needs.
 *
 *   node scripts/generate-pwa-icons.mjs
 *
 * The mark is the balanced-ledger "=" from src/components/Common/Logo.tsx, in
 * the Quiet Ink accent (#1F6E68 on #FCFCFB). Everything is drawn from the
 * numbers below rather than traced from a bitmap, so re-running this after a
 * palette change reproduces the set exactly.
 *
 * Chromium does the rasterising — Playwright is already a dependency, so this
 * needs no image toolchain (no sharp, no ImageMagick).
 *
 * Maskable icons get their own geometry: Android crops to a circle inscribed
 * in the square and can shave ~10% off each edge, so the glyph is drawn at 60%
 * scale on a full-bleed background instead of in a rounded card.
 */

import { mkdir, writeFile } from "node:fs/promises"
import path from "node:path"
import { fileURLToPath } from "node:url"

import { chromium } from "@playwright/test"

const ACCENT = "#1F6E68"
const PAPER = "#FCFCFB"

const OUT_DIR = path.join(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
  "public",
)

/** The mark on a rounded-square card, as it appears in the app header. */
function anyPurposeSvg(size) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="14" fill="${ACCENT}"/>
  <rect x="16" y="25" width="32" height="6" rx="3" fill="${PAPER}"/>
  <rect x="16" y="37" width="32" height="6" rx="3" fill="${PAPER}"/>
</svg>`
}

/** Full-bleed accent with the glyph inside the maskable safe zone. */
function maskableSvg(size) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 64 64">
  <rect width="64" height="64" fill="${ACCENT}"/>
  <rect x="22" y="27.2" width="20" height="3.8" rx="1.9" fill="${PAPER}"/>
  <rect x="22" y="34.6" width="20" height="3.8" rx="1.9" fill="${PAPER}"/>
</svg>`
}

const TARGETS = [
  { file: "pwa-192x192.png", size: 192, svg: anyPurposeSvg },
  { file: "pwa-512x512.png", size: 512, svg: anyPurposeSvg },
  { file: "pwa-maskable-512x512.png", size: 512, svg: maskableSvg },
  { file: "apple-touch-icon.png", size: 180, svg: maskableSvg },
]

const browser = await chromium.launch()

try {
  await mkdir(OUT_DIR, { recursive: true })

  for (const { file, size, svg } of TARGETS) {
    const page = await browser.newPage({
      viewport: { width: size, height: size },
      deviceScaleFactor: 1,
    })

    await page.setContent(
      `<body style="margin:0">${svg(size)}</body>`,
      { waitUntil: "load" },
    )

    const png = await page.screenshot({ omitBackground: true })
    await writeFile(path.join(OUT_DIR, file), png)
    await page.close()

    console.log(`wrote public/${file} (${size}x${size})`)
  }
} finally {
  await browser.close()
}
