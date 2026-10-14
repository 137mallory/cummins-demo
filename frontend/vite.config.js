
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fetchPulse, fetchStockHistory } from "./src/lib/pulseFetch.js";
import { tickerFor } from "./src/lib/tickers.js";
import { getMockStockHistory } from "./src/lib/mockStockHistory.js";

async function apiMiddleware(req, res, next) {
  const requestUrl = req.url || "";
  const baseUrl = "http://localhost";

  // Forward dataset requests to the local FastAPI backend.
  if (requestUrl.startsWith("/api/dataset")) {
    return next();
  }

  // Image proxy.
  if (requestUrl.startsWith("/api/img")) {
    try {
      const src = new URL(requestUrl, baseUrl).searchParams.get("u") || "";

      if (!/^https?:\/\//i.test(src)) {
        res.statusCode = 400;
        return res.end("bad url");
      }

      const upstream = await fetch(src, {
        headers: {
          "user-agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
          accept: "image/*,*/*",
        },
        redirect: "follow",
        signal: AbortSignal.timeout(12000),
      });

      const contentType = upstream.headers.get("content-type") || "";

      if (!upstream.ok || !/^image\//i.test(contentType)) {
        res.statusCode = 404;
        return res.end("not an image");
      }

      const buffer = Buffer.from(await upstream.arrayBuffer());

      res.setHeader("Content-Type", contentType);
      res.setHeader("Cache-Control", "public, max-age=86400");

      return res.end(buffer);
    } catch {
      res.statusCode = 404;
      return res.end("img fetch failed");
    }
  }

  // Stock history endpoint.
  if (requestUrl.startsWith("/api/pulse/history")) {
    const query = new URL(requestUrl, baseUrl).searchParams;
    const cid = query.get("cid") || "";
    const name = query.get("name") || "";
    const range = query.get("range") || "1y";
    const ticker =
      tickerFor(cid) || (cid ? `${cid.toUpperCase().slice(0, 6)}.NS` : "LT.NS");

    try {
      let data = await fetchStockHistory({ ticker, range, name });

      if (!data?.points?.length) {
        data = getMockStockHistory({ cid, name, ticker, range });
      }

      res.setHeader("Content-Type", "application/json");
      res.setHeader("Cache-Control", "public, max-age=300");

      return res.end(JSON.stringify(data));
    } catch {
      const data = getMockStockHistory({ cid, name, ticker, range });

      res.setHeader("Content-Type", "application/json");
      return res.end(JSON.stringify(data));
    }
  }

  // Company pulse endpoint.
  if (requestUrl.startsWith("/api/pulse")) {
    try {
      const query = new URL(requestUrl, baseUrl).searchParams;
      const cid = query.get("cid") || "";
      const name = query.get("name") || "";
      const product = query.get("product") || "";

      const data = await fetchPulse({
        name,
        ticker: tickerFor(cid),
        product,
      });

      res.setHeader("Content-Type", "application/json");
      res.setHeader("Cache-Control", "public, max-age=300");

      return res.end(JSON.stringify(data));
    } catch (error) {
      res.statusCode = 200;
      res.setHeader("Content-Type", "application/json");

      return res.end(
        JSON.stringify({
          stock: null,
          trending: [],
          error: String(error?.message || error),
        })
      );
    }
  }

  return next();
}

export default defineConfig({
  plugins: [
    react(),
    {
      name: "api-local",
      configureServer(server) {
        server.middlewares.use(apiMiddleware);
      },
      configurePreviewServer(server) {
        server.middlewares.use(apiMiddleware);
      },
    },
  ],

  preview: {
    port: 5179,
    host: true,
    strictPort: true,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8600",
        changeOrigin: true,
      },
    },
  },

  server: {
    port: 5178,
    host: true,
    strictPort: true,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8600",
        changeOrigin: true,
      },
    },
  },
});
