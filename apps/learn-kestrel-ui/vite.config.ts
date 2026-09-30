// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// The Kestrel Learn course: static pages, no Noesi server. The build is packed
// into one HTML file for the Streamlit host (scripts/build-learn-standalone.mjs).
export default defineConfig({
  base: "/kestrel/",
  plugins: [react()],
  build: { outDir: "dist", sourcemap: false },
});
