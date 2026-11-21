import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
// @ts-expect-error Local Node middleware is an untyped ESM module.
import { irrigationApi } from "./irrigation-api.mjs";

// public/data and public/land.geojson are symlinks to ../app/data and ../app/assets/land.geojson,
// so this front end reads exactly the export of app/build_data.py (contract: app/data/SCHEMA.md).
export default defineConfig({
  plugins: [
    react(),
    {
      name: "irrigation-api",
      configureServer(server) {
        server.middlewares.use(irrigationApi);
      },
      configurePreviewServer(server) {
        server.middlewares.use(irrigationApi);
      },
    },
  ],
  base: "./",
  build: { chunkSizeWarningLimit: 900 },
});
