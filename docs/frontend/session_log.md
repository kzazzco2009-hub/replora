# Replora Frontend — Session Log

**Read this file first at the start of every frontend session.** Then continue from "Next step".
Append a new entry per session (newest first). Record what was done, the commands run, the results and the decisions.

---

## Current status
| Item | Value |
|---|---|
| Current phase | Phase 0, frontend half (F0). P0.1, P0.4 done. P0.5 implemented on branch `feat/p0.5-gen-api`, PR open — not ticked until merged. |
| Last gate passed | Planning approved. G0 agreement confirmed by both sides in issue #1. The formal G0 gate (end of Phase 0) is still open. |
| Next step | Wait for CI and review on the P0.5 PR. The generated `schema.d.ts` will need a re-run of `pnpm gen:api` once PRs #10, #11, #12 merge (workspaces, files, auth follow-ups extend the contract). |
| Blockers | none |

## Recorded versions (P0.1)
| Item | Version |
|---|---|
| Node | 26.13.1 (`.nvmrc`, `engines`) |
| pnpm | 12.23.0 (root `packageManager`) |
| TypeScript | 6.0.3 (typescript-eslint 8.x supports `<6.1.0`; revisit TS 7 later) |
| next | 16.4.6 |
| react | 19.3.1 |
| tailwindcss | 4.3.5 |
| next-intl | 4.16.1 |
| @tanstack/react-query | 5.108.4 |
| vitest | 5.1.1 |
| @playwright/test | 1.65.1 |
| msw | 3.0.7 |
| eslint | 10.15.0 |
| gitleaks / pre-commit | 8.30.1 / 4.7.0 |

Vitest against TypeScript 6.0.3 is verified when F0 first runs `pnpm test`.

---

## Session 1 — 2026-11-24
Done:
- Agreed the G0 terms and versions with the backend developer in issue #1 (TypeScript 6.0.3, Node 26.13.1, pnpm 12.23.0).
- Approved PR #2 (repo skeleton and docs) and accepted `6ce85a8`. PR #2 and PR #3 are merged. `main` is at `47d2863`.
- Merged `origin/main` into `frontend/setup` (`8b88af0`) and pushed. This branch will be deleted.
- Codespace aligned. Evidence (commands and results):
  - `node --version` gave v26.13.1 (`nvm install 26.13.1`, set as default).
  - `pnpm --version` gave 12.23.0 (`npm install -g pnpm@12.23.0`).
  - `gitleaks version` gave 8.30.1 (official release, checksum OK).
  - `pre-commit --version` gave pre-commit 4.7.0.
- Wrote `frontend/CLAUDE.md` (frontend-only rules, no conflict with the root file).
- Note: running `pnpm` in the repo created an untracked root `pnpm-lock.yaml` (only `packageManagerDependencies`). Not committed here. It is regenerated and committed in F0.

Decisions:
- Work from `docs/` only. `Frontend_Planning/` is frozen. The frontend plan is `docs/frontend/plan.md`.
- Add files by name, never `git add .`.

---

## Session 2 — 2026-11-24
P0.4 (frontend skeleton), staged, in progress.
Done:
- PR #5 merged (`a297561`). Branched `feat/p0.4-frontend-skeleton` from `origin/main`. `docs/frontend-claude-and-log` untouched.
- Compatibility check (`pnpm view`, before installing):
  - `eslint-config-next@16.4.6` peers `eslint >=9.0.0`, `typescript >=3.3.1` — both satisfied.
  - It depends on `typescript-eslint: "^8.56.0"`, which resolves to `8.74.0`; that version's peer is `typescript: ">=4.8.4 <6.1.0"`, so TS 6.0.3 is supported (confirms the `<6.1.0` note above — the exact pin 8.56.0 would *not* have supported it, but the caret range resolves past it).
  - 3 of the 4 ESLint plugins `eslint-config-next` pulls (`eslint-plugin-react@7.37.5`, `eslint-plugin-import@2.32.0`, `eslint-plugin-jsx-a11y@6.10.2`) cap their peer range at ESLint `^9`, not `^10` — confirmed unmet-peer **warnings** after install (`pnpm peers check`). This is a known, documented Next.js gap (their docs note ESLint 10 peers aren't listed yet on some plugins), not a hard error; install and resolution succeed.
  - `@testing-library/react`, `vitest`, `@vitejs/plugin-react` needed extra explicit deps not in the first draft: `@types/react-dom`, `@testing-library/dom`, `vite` (peer of both vitest and the Vite React plugin, not a transitive dependency).
- Installed (`pnpm add --save-exact`, resolved versions below). No pending build-script approvals (`pnpm approve-builds` → "no packages awaiting approval").

Resolved versions (P0.4 install):
| Package | Version |
|---|---|
| next | 16.4.6 |
| react / react-dom | 19.3.1 |
| typescript | 6.0.3 (7.0.2 available, staying pinned) |
| eslint | 10.15.0 |
| eslint-config-next | 16.4.6 |
| tailwindcss | 4.3.5 |
| @tailwindcss/postcss | 4.3.5 |
| postcss | 8.5.33 |
| vitest | 5.1.1 |
| vite | 8.3.8 |
| @vitejs/plugin-react | 6.3.0 |
| @testing-library/react | 16.3.3 |
| @testing-library/dom | 10.4.2 |
| jsdom | 31.0.1 |
| @types/node | 26.6.6 |
| @types/react | 19.3.0 |
| @types/react-dom | 19.3.0 |

- Created the skeleton: `tsconfig.json`, `next.config.ts`, `postcss.config.mjs` (Tailwind v4 CSS-first), `eslint.config.mjs` (flat config — `eslint-config-next@16.4.6`'s default export is already a flat-config array, no `FlatCompat` needed), `src/app/{layout,page}.tsx` + `globals.css` (one page, no `[locale]` routing yet — out of P0.4 scope), `vitest.config.ts`, `tests/unit/home.test.tsx` (T0.2, no `jest-dom` — uses `toBeDefined()` since that package wasn't in the approved install list).
- Ran locally, all green: `pnpm typecheck` (tsc --noEmit), `pnpm lint` (eslint ., 0 errors despite the 3 peer warnings above), `pnpm test` (vitest, 1/1 passed — T0.2), `pnpm build` (next build / Turbopack, static page generated).
- `next build` auto-adjusted `tsconfig.json`: `jsx` → `react-jsx` (Next requires the automatic JSX runtime) and added `.next/dev/types/**/*.ts` to `include`. Expected Next.js behavior, left as-is.

- T0.3: added a deliberate `react-hooks/rules-of-hooks` violation to `src/app/page.tsx` (calling `useState` at module top level). `pnpm lint` failed as expected (`exit code 1`, 1 error). Reverted the file; `pnpm lint` passed again (`exit code 0`), confirmed clean. Done locally with the exact command CI runs (`pnpm -C frontend run lint`); the full CI-level proof (GitHub Actions run) still needs the branch pushed — that's stage (f), not done yet pending explicit "go".

- Replaced "owner" with "Developer B" in `frontend/CLAUDE.md` (4 occurrences).
- `gitleaks git .`: no leaks found. Committed by name (`80aafbd`), pushed `feat/p0.4-frontend-skeleton`, opened PR #9.

Next step: wait for CI on PR #9, then review/merge with the backend developer. After merge: P0.6 (pre-commit), P0.7 gap (add `pnpm build` to ci.yml — separate shared-file PR), P0.5 once `contracts/openapi.json` exists.

PR #9 follow-up: ticked `[x] P0.1` and `[x] P0.4` in `docs/frontend/plan.md` §F0 (both verified above — versions recorded, skeleton built and tested). No other checklist item touched. Commit `3525107`.

T0.3 in real CI: pushed the deliberate `react-hooks/rules-of-hooks` violation (commit `0e592cc`) — the `Frontend` job failed exactly at `pnpm -C frontend run lint`:
> React Hook "useState" cannot be called at the top level. React Hooks must be called in a React function component or a custom React Hook function (frontend/src/app/page.tsx#4)
Failed run: https://github.com/kzazzco2009-hub/replora/actions/runs/45491885639
Reverted with `git revert` (no force-push), commit `4b1da81`. `Frontend` job green again.
Green run: https://github.com/kzazzco2009-hub/replora/actions/runs/45492118286

---

## Session 3 — 2026-11-25
P0.5 (`pnpm gen:api`), staged, in progress.

Done:
- Branched `feat/p0.5-gen-api` from `main` at `c4ea4a9` (confirms PR #8 merged: `contracts/openapi.json` has `/api/v1/auth/login`).
- Version check before installing: `pnpm view openapi-typescript` → latest `7.13.0`, `peerDependencies: { typescript: "^5.x" }`, no `engines` field. Our pinned TypeScript `6.0.3` does not satisfy `^5.x` — same kind of unmet-peer gap already seen with `eslint-config-next`'s plugins in P0.4. No `.npmrc` strict-peer setting in the repo, so this is a warning, not an install failure. No pinned versions changed.
- Installed `openapi-typescript@7.13.0` exact (devDependency only; no `openapi-fetch` — that's P9.6). `pnpm peers check` confirmed the predicted `unmet peer typescript` warning (wanted `^5.x`, installed `6.0.3`), plus the pre-existing ESLint peer warnings. No new dependency added for the type test — Vitest's built-in `expectTypeOf` was used.
- Added script `"gen:api": "openapi-typescript ../contracts/openapi.json -o src/lib/api/schema.d.ts"`. Ran it: generated `frontend/src/lib/api/schema.d.ts` (2142 lines, 67,223 bytes), committed. The tool's own banner ("auto-generated... do not make direct changes") serves as the "generated, do not edit" header.
- `eslint.config.mjs`: added `{ ignores: ["src/lib/api/schema.d.ts"] }` ahead of the Next config array. No prettier exists anywhere in this repo (checked), so there is nothing to add a prettier-ignore to.
- Added the contract type check `tests/unit/api-schema.test.ts` (Vitest `expectTypeOf`, no network): proves `paths["/api/v1/auth/login"]["post"]` and `paths["/api/v1/health"]["get"]` exist, and that a `501` response on `/api/v1/auth/login` has a typed `application/problem+json` body.
- Evidence (commands and results):
  - `pnpm typecheck` → clean, no errors.
  - `pnpm lint` → 0 errors, 0 warnings (fixed an incidental `import/no-anonymous-default-export` warning by naming the config array before exporting it).
  - `pnpm test` → 3/3 passed (1 existing `home.test.tsx` + 2 new in `api-schema.test.ts`).
  - `pnpm build` → compiled successfully, 3 static routes generated (Turbopack).
  - Determinism: staged `schema.d.ts`, ran `pnpm gen:api` a second time — identical SHA-256 (`61b025a7...`), `git diff` on the file showed 0 lines.

Next step: gitleaks, commit, push, open the PR (template-filled, SHA + test results + security/contract impact). Do **not** tick P0.5 in `docs/frontend/plan.md` until the PR is merged — `schema.d.ts` will need regenerating once #10/#11/#12 land.
