import fs from "node:fs";
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const httpsEnabled = ["1", "true", "yes", "on"].includes(
    (env.VITE_DEV_HTTPS || "").toLowerCase(),
  );
  const certFile = env.VITE_DEV_SSL_CERT;
  const keyFile = env.VITE_DEV_SSL_KEY;

  let https = false;

  if (httpsEnabled) {
    if (certFile && keyFile) {
      https = {
        cert: fs.readFileSync(certFile),
        key: fs.readFileSync(keyFile),
      };
    } else {
      https = true;
    }
  }

  return {
    base: env.VITE_BASE_PATH || "/",
    plugins: [react()],
    server: {
      host: env.VITE_DEV_HOST || "127.0.0.1",
      port: Number(env.VITE_DEV_PORT || 5173),
      https,
      proxy: {
        "/api": {
          target: env.VITE_BACKEND_URL || "http://127.0.0.1:8000",
          changeOrigin: false,
          secure: false,
        },
      },
    },
    preview: {
      host: env.VITE_PREVIEW_HOST || "127.0.0.1",
      port: Number(env.VITE_PREVIEW_PORT || 4173),
    },
  };
});
