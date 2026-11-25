# Replora frontend

Next.js app (TypeScript, Tailwind, pnpm). See `../docs/frontend/` for the plan, testing and security docs, and `../docs/api_contract.md` for the API.

## Run locally

```
pnpm install
pnpm dev
```

Needs the backend running at `http://localhost:8000` (see `../backend/README.md`).

## The `/api` proxy

In development, `next.config.ts` rewrites `/api/:path*` to `${BACKEND_ORIGIN ?? "http://localhost:8000"}/api/:path*`, so the browser calls the backend on the same origin as the frontend. This keeps cookies and CSRF simple (no CORS). Set `BACKEND_ORIGIN` to point at a different backend. There is no rewrite in production builds; the production proxy is handled by Vercel (P19.1).

## Commands

| Command | Does |
|---|---|
| `pnpm dev` | Start the dev server |
| `pnpm build` | Production build |
| `pnpm lint` | ESLint |
| `pnpm typecheck` | `tsc --noEmit` |
| `pnpm test` | Vitest |
| `pnpm format` | Prettier, write |
| `pnpm format:check` | Prettier, check only |
| `pnpm gen:api` | Regenerate `src/lib/api/schema.d.ts` from `../contracts/openapi.json` |
