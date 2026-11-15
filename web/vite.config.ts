import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// public/data and public/land.geojson are symlinks to ../app/data and ../app/assets/land.geojson,
// so this front end reads exactly the export of app/build_data.py (contract: app/data/SCHEMA.md).
export default defineConfig({
  plugins: [react()],
  base: "./",
  build: { chunkSizeWarningLimit: 900 },
});
