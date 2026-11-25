import nextConfig from "eslint-config-next";

const config = [{ ignores: ["src/lib/api/schema.d.ts"] }, ...nextConfig];

export default config;
