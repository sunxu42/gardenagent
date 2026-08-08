import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "node:path";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) {
            if (id.includes("/features/config/")) {
              return "feature-config";
            }
            if (
              id.includes("/features/chat/components/Affect") ||
              id.includes("/features/chat/components/affect/")
            ) {
              return "feature-affect";
            }
            if (id.includes("/features/strategy/")) {
              return "feature-strategy";
            }
            return undefined;
          }

          if (id.includes("react-syntax-highlighter") || id.includes("refractor")) {
            return "vendor-syntax";
          }
          if (id.includes("js-yaml")) {
            return "vendor-yaml";
          }
          if (id.includes("lucide-react")) {
            return "vendor-icons";
          }
          if (id.includes("@radix-ui")) {
            return "vendor-radix";
          }
          if (
            id.includes("/react/") ||
            id.includes("/react-dom/") ||
            id.includes("react-router") ||
            id.includes("scheduler/")
          ) {
            return "vendor-react";
          }
          return undefined;
        },
      },
    },
  },
  server: {
    proxy: {
      "/ws": {
        target: "http://127.0.0.1:8005",
        ws: true,
        changeOrigin: true,
        configure: (proxy) => {
          const isBenignProxyError = (err: NodeJS.ErrnoException) =>
            err.code === "EPIPE" ||
            err.code === "ECONNRESET" ||
            err.code === "ECONNREFUSED";

          proxy.on("error", (err) => {
            if (isBenignProxyError(err)) {
              return;
            }
            console.error("[vite] ws proxy error:", err);
          });

          proxy.on("proxyReqWs", (_proxyReq, _req, socket) => {
            socket.on("error", (err) => {
              if (isBenignProxyError(err)) {
                return;
              }
              console.error("[vite] ws proxy socket error:", err);
            });
          });
        },
      },
      "/api/prompt-editor": {
        target: "http://127.0.0.1:8005",
        changeOrigin: true,
      },
      "/api/eval": {
        target: "http://127.0.0.1:8005",
        changeOrigin: true,
      },
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      "@a2ui-catalog": path.resolve(__dirname, "../agent/a2ui/catalog"),
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
  },
});
