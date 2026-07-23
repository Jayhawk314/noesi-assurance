import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    // Dev-mode convenience only; production is served by workbench-api.
    proxy: { "/api": "http://127.0.0.1:8347" },
  },
  build: { outDir: "dist", sourcemap: false },
});
