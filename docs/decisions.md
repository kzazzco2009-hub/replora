# Replora — Decisions

One line per final decision. Discussion happens in Issues or PRs; the outcome is recorded here and linked.
Details and history are in `session_log.md` (decisions log).

| Date | ID | Decision | Approved by | Link |
|---|---|---|---|---|
| 2026-11-23 | D1–D14 | All planning recommendations approved as written in `plan.md` §1 (FastAPI; Next.js; backend-owned auth; Resend; DOC deferred; OCR at the Phase 16 gate; OpenRouter metadata-only; Supabase Pro + 50 MiB; DB job chain proven by P8.8; locale by Accept-Language; retention 30/90/365 days; optional TOTP; stdlib csv + Decimal; Egypt PDPL + GDPR-ready). | Owner | — |
| 2026-11-24 | — | Runtimes: Python 3.14, Node 26 LTS (26.13.1), Postgres 17, pnpm 12.23.0 (pinned via `packageManager`, `.nvmrc`, `.python-version`). | Both | #1 |
| 2026-11-24 | — | TypeScript pinned to the newest 6.x (6.0.3) because typescript-eslint 8.x supports `<6.1.0`. Revisit TS 7 when typescript-eslint supports it. | Both | #1 |
| 2026-11-24 | — | Server computes the file sha256 on `complete`; `sha256` removed from `upload-intent`. | Both | #1 |
| 2026-11-24 | — | Contract: `GET /auth/csrf`, `GET /limits`, draft shapes (`Column`, `RunSummary`, `OutputArtifact`, `Lineage`, `AuditEvent`), preview `status`/`q`, full-definition PATCH with `If-Match`, the `params_schema` subset, `Explanation` keys. | Both | #1 |
| 2026-11-24 | — | `openapi.json` is generated from FastAPI 501 stubs from B0. Staged freeze: auth at G5, files at G6, runs and outputs at G8, all of v1 at P8.7. | Both | #1 |
| 2026-11-24 | — | Visual Builder is out of scope for v1. | Both | #1 |
| 2026-11-24 | — | Single copy of the docs in `docs/`, changed by PR only. | Both | #1 |
| 2026-11-24 | — | Gate approvals: backend gates by Developer A, frontend gates by Developer B, shared gates (0, 17, 18, 19) by both. Review time 24 h for PRs, 48 h for gates. | Both | #1 |
| 2026-11-24 | — | Branch protection needs GitHub Pro, a public repo or an organization. Until decided: no direct push to `main`, no self-merge (manual rule). Small PRs (≤ 400 lines). Use Issues, not Discussions. | Both | #1 |
| 2026-11-24 | — | CODEOWNERS: root files, `.github/`, `contracts/`, `docs/` shared; `backend/**` Developer A; `frontend/**` Developer B. | Both | #1 |
| 2026-11-25 | — | Accepted risk: ESLint 10.15.0 although eslint-plugin-react 7.37.5, eslint-plugin-import 2.32.0 and eslint-plugin-jsx-a11y 6.10.2 cap their peers at ESLint ^9; and openapi-typescript 7.13.0 caps typescript at ^5.x while we pin 6.0.3. Lint, build and gen:api pass today. Revisit when those packages support them. A removed ESLint API could crash lint or silently stop a rule. | Both | #9 |
| 2026-11-25 | — | A backend PR that changes `contracts/openapi.json` also runs `pnpm -C frontend run gen:api` and commits `frontend/src/lib/api/schema.d.ts`, and no other file under `frontend/`. It still goes through CODEOWNERS. CI checks both files for drift. | Both | #1, #17 |
| 2026-11-25 | — | §2 error codes: 401 only means "no session" (`UNAUTHENTICATED`, `INVALID_CREDENTIALS`, `MFA_CHALLENGE_INVALID`); a wrong secret is 400 (`MFA_CODE_INVALID`, `PASSWORD_INCORRECT`, `TOKEN_INVALID`). Also `CSRF_FAILED` and `EMAIL_NOT_VERIFIED` (403), `MFA_ALREADY_ENABLED` and `MFA_NOT_ENABLED` (409), `RATE_LIMITED` (429). There is no "email already registered" code: `POST /auth/register` always returns 202 with no body (S‑26). | Both | #1 |
| 2026-11-25 | — | `main` protection is kept as code in `.github/rulesets/main.json` (P0.8, S‑05), with a test that its required checks match the CI job names. It requires a PR with 1 approval (stale approvals dismissed), squash merge only, the 3 CI checks, no force-push or deletion, and no bypass. **`require_code_owner_review` is off**, because single-owner paths (`/backend/`, `/frontend/`) would make every PR need its own author's approval. Changes go through a PR, and the admin then re-applies the file. | Both (proposed) | this PR |
