// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Served by workbench-api at /studio/. The typed API client is shared with
// the workbench UI (../workbench-ui/src/api.ts) rather than copied.
export default defineConfig({
  base: "/studio/",
  plugins: [react()],
  server: { proxy: { "/api": "http://127.0.0.1:8347" } },
  build: { outDir: "dist", sourcemap: false },
});
