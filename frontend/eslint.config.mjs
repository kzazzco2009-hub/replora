import nextConfig from "eslint-config-next";
import noPhysicalDirection from "./eslint-rules/no-physical-direction.mjs";

const config = [
  { ignores: ["src/lib/api/schema.d.ts"] },
  ...nextConfig,
  { linterOptions: { reportUnusedDisableDirectives: "error" } },
  {
    files: ["src/**/*.{ts,tsx}"],
    plugins: {
      local: { rules: { "no-physical-direction": noPhysicalDirection } },
    },
    rules: { "local/no-physical-direction": "error" },
  },
];

export default config;
