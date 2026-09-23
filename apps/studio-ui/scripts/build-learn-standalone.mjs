// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
// Pack the built studio (dist/) into ONE self-contained HTML file for hosts
// that serve a single document, e.g. Streamlit's components.html. With no
// session token in the page, the app runs as the Learn course only.
// Usage: npm run build && node scripts/build-learn-standalone.mjs
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const dist = join(root, "dist");
const out = join(root, "..", "learn-streamlit", "learn.html");
let html = readFileSync(join(dist, "index.html"), "utf-8");

const asset = (url) => readFileSync(join(dist, url.replace(/^\/studio\//, "")), "utf-8");
html = html.replace(/<link rel="stylesheet"[^>]*href="([^"]+)"[^>]*>/g,
  (_, href) => `<style>${asset(href)}</style>`);
html = html.replace(/<script type="module"[^>]*src="([^"]+)"[^>]*><\/script>/g,
  // "</script" inside the code would end the inline tag early.
  (_, src) => `<script type="module">${asset(src).replace(/<\/script/gi, "<\/script")}</script>`);
html = html.replace(/<title>[^<]*<\/title>/, "<title>Learn the audit — Noesi</title>");

if (/src="\/studio\/|href="\/studio\//.test(html)) throw new Error("an asset was not inlined");
writeFileSync(out, html);
console.log(`wrote ${out} (${(html.length / 1024).toFixed(0)} KB)`);
