import { defineConfig } from "vite";

export default defineConfig({
  build: {
    target: "es2021",
  },
  server: {
    proxy: {
      "/api/stt": {
        target: "http://localhost:8010",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/stt/, ""),
      },
      "/api/tts": {
        target: "http://localhost:8011",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/tts/, ""),
      },
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
