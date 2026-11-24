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
