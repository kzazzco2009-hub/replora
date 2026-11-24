# Replora Frontend — Session Log

**Read this file first at the start of every frontend session.** Then continue from "Next step".
Append a new entry per session (newest first). Record what was done, the commands run, the results and the decisions.

---

## Current status
| Item | Value |
|---|---|
| Current phase | Phase 0, frontend half (F0). P0.1 done. |
| Last gate passed | Planning approved. G0 agreement confirmed by both sides in issue #1. The formal G0 gate (end of Phase 0) is still open. |
| Next step | Open the small docs PR (this log and `frontend/CLAUDE.md`), delete `frontend/setup`, branch F0 from `main`, then P0.4 onward. P0.5 waits for the backend's `contracts/openapi.json`. |
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
