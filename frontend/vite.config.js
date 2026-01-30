import { defineConfig } from "vite";
import { resolve } from "path";
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  root: __dirname,
  plugins: [tailwindcss()],
  build: {
    outDir: resolve(__dirname, "../static/frontend"),
    emptyOutDir: true,
    sourcemap: true,
    cssCodeSplit: false,
    rollupOptions: {
      input: {
        main: resolve(__dirname, "src/main.js"),
        programs: resolve(__dirname, "src/programs.js"),
        pieces: resolve(__dirname, "src/pieces.js"),
      },
      output: {
        entryFileNames: "[name].js",
        assetFileNames: "bundle.[ext]",
      },
    },
  },
});
