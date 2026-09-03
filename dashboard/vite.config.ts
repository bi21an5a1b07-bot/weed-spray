/**
 * Vite dashboard on :8080.
 * `/api` is proxied to the GCS backend with the prefix stripped.
 * `/ws` is proxied as a WebSocket to the same backend.
 */
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 8080,
    strictPort: true,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        rewrite: (p) => p.replace(/^\/api/, ""),
      },
      "/ws": {
        target: "ws://127.0.0.1:8000",
        ws: true,
      },
      // Same-origin camera. Direct :8889 fails from a Windows browser into WSL
      // ("127.0.0.1 refused to connect") even when the dashboard on :8080 loads.
      "/cam": {
        target: "http://127.0.0.1:8889",
        changeOrigin: true,
        ws: true,
      },
      // HLS for the <video> player. MediaMTX sets a Secure cookie that browsers
      // drop on http://, which 302-loops; strip Secure and keep the path on /hls.
      "/hls": {
        target: "http://127.0.0.1:8888",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/hls/, ""),
        configure: (proxy) => {
          proxy.on("proxyRes", (proxyRes) => {
            const loc = proxyRes.headers.location;
            if (typeof loc === "string" && loc.includes("/cam/")) {
              const path = loc.startsWith("http")
                ? new URL(loc).pathname + new URL(loc).search
                : loc;
              proxyRes.headers.location = `/hls${path.startsWith("/") ? path : `/${path}`}`;
            }
            const cookies = proxyRes.headers["set-cookie"];
            if (cookies) {
              proxyRes.headers["set-cookie"] = cookies.map((c) =>
                c.replace(/;\s*Secure/gi, "").replace(/;\s*Partitioned/gi, ""),
              );
            }
          });
        },
      },
    },
  },
});
