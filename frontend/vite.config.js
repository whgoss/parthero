// frontend/vite.config.js
import { defineConfig } from "vite";
import { resolve } from "path";

export default defineConfig({
  root: __dirname,
  build: {
    outDir: resolve(__dirname, "../static/frontend"),
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(__dirname, "src/main.js"),
      output: {
        // fixed filenames so Django templates don't have to chase hashes yet
        entryFileNames: "bundle.js",
        assetFileNames: "bundle.[ext]",
      },
    },
  },
});
