import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "");
  const backendTarget = env.BACKEND_URL || "http://127.0.0.1:8000";
  const wsTarget = env.BACKEND_WS_URL || "ws://127.0.0.1:8000";

  return {
    plugins: [react()],
    server: {
      port: 5173,
      host: true,
      proxy: {
        "/api": {
          target: backendTarget,
          changeOrigin: true,
        },
        "/ws": {
          target: wsTarget,
          ws: true,
        },
      },
    },
  };
});


