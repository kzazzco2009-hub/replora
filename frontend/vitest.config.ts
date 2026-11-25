import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "./src"),
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    server: {
      // next-intl uses extensionless ESM imports internally; inlining lets
      // Vite's bundler-style resolution handle them instead of Node's
      // strict ESM resolver. https://github.com/vercel/next.js/issues/77200
      deps: { inline: ["next-intl"] },
    },
  },
});
