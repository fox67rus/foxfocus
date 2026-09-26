import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/health": "http://127.0.0.1:8000",
      "/capture": "http://127.0.0.1:8000",
      "/tasks": "http://127.0.0.1:8000",
      "/notes": "http://127.0.0.1:8000",
      "/audit": "http://127.0.0.1:8000",
      "/ai": "http://127.0.0.1:8000",
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test-setup.ts",
  },
});
