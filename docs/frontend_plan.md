# Developer B — Frontend Track

**Owns:** `frontend/**`, the design system (`design.md`), i18n (AR/EN, RTL), theming (light/dark), responsive layouts (phone, tablet, laptop), UX iteration, the Playwright E2E suite, Lighthouse and axe CI.
**Co-owns:** `contracts/**` (with Developer A), Phase 17 hardening, and Phase 19 go-live.
**Stack:** Next.js (App Router, latest) · React (latest) · TypeScript strict · Tailwind CSS v4 · next-intl · next-themes · TanStack Query · openapi-typescript + openapi-fetch · MSW · Vitest + Testing Library · Playwright + axe · Lucide icons · TanStack Virtual (tables).
**Rules:** all MANDATORY rules in `plan.md` §2 apply (short components, clear names, no overengineering, latest APIs, root cause before fixes). Phase gates, `testing.md` and `security.md` apply unchanged. Each phase ends with a request for the owner's permission.

## How the frontend works before the backend exists
- Types are generated from `contracts/openapi.json`. While it is still a draft, a hand-written OpenAPI from api_contract.md is committed at G0, and the backend replaces it as each endpoint lands.
- **MSW** serves `contracts/fixtures/**` in development and in tests. A `NEXT_PUBLIC_API_MOCKS=1` flag switches between mocks and the real `/api` rewrite.
- MSW scenario switches simulate every run state, slow networks (for skeleton testing) and every error code.

## Track timeline (parallel with backend_plan.md)

| Week* | Frontend phase | Needs from backend | Sync point |
|---|---|---|---|
| 1 | F0 = Phase 0 (frontend half) + contract draft | — | **G0** |
| 2–3 | F1 = P9.1–P9.4 tokens, themes, i18n/RTL, app shell | — | — |
| 3–4 | F2 = P9.5 UI kit + Skeletons, P9.6 API client + MSW | domain fixtures (B1) | — |
| 4–5 | F3 = P9.7–P9.8 auth screens (mocked), loading routes | auth fixtures | **Gate G9** |
| 5–7 | F4 = P10.1–P10.4 wizard: upload, describe, review (pipeline rail), approve | validation fixtures (B2) | — |
| 7–8 | F5 = P10.5–P10.6 run detail + results table | run-state fixtures (B3) | **I1 auth (real)** |
| 8–9 | F6 = P10.7 files, runs, home, settings, members | — | **I2 upload (real)** |
| 10–11 | F7 = P10.8 switch to real API | B8 frozen API | **I3 → Gate G10** |
| 11–12 | F8 = Phase 11 UX iteration + accessibility | — | **Gate G11** |
| 12–13 | F9 = P12.5 AI disclosure and consent UI | B12 | **I4** |
| 13–14 | F10 = P13.4 workflows, versions, replay, mapping editor | B13 | **I5** |
| 15–22 | F11 = format-specific UI (icons, warnings, P16.4 OCR review UI), continuous UX polish, visual regression baselines | B14–B16 codes | — |
| 23–24 | Phase 17 (shared): Lighthouse budgets, bundle, caching | — | joint |
| 25–27 | Phase 19: Vercel frontend project, headers and CSP, E2E on staging and prod | staging API | **I6**, go-live |

\*Weeks are illustrative (~20 h/week) and are re-baselined after F3.

## Phases

### F0 — Foundation (frontend half of Phase 0)
- [ ] P0.1 versions (frontend libraries) · P0.4 Next.js skeleton (pnpm) · P0.6 lint, prettier, typecheck in pre-commit · P0.7 frontend CI jobs (lint, typecheck, Vitest, build) · P0.9 `/api` rewrite to backend in dev
- [ ] Co-write the api_contract.md draft. Commit the hand-written draft OpenAPI and `pnpm gen:api`.
- [ ] Tests T0.2, T0.3 · Security S‑03, S‑04 · **Gate G0**

### F1 — Tokens, themes, i18n, shell → P9.1–P9.4 · T9.2, T9.3, T9.7, T9.9
- [ ] Design tokens as CSS variables (light and dark) in Tailwind v4 `@theme`, plus the token contrast test (T11.3 written early).
- [ ] `next-themes` with a cookie so the server renders the right theme (no flash).
- [ ] `next-intl` with `[locale]` routing, `dir` on `<html>`, Readex Pro via `next/font`, logical properties only (ESLint/stylelint rule against `left`, `right`, `ml-`, `mr-`).
- [ ] App shell at 3 breakpoints.

### F2 — UI kit and data layer → P9.5–P9.6 · T9.1, T9.4
- [ ] Components per design.md §3, each with a Vitest test in LTR and RTL. Skeleton variants per layout.
- [ ] Generated API client, TanStack Query setup (per-resource `staleTime`, ETag-aware fetch), MSW handlers from fixtures, error-code → message mapper with a parity test.

### F3 — Auth and loading routes → P9.7–P9.8 · T9.5, T9.6, T9.8 · S‑60…S‑64 · **Gate G9**

### F4–F7 — Core flow → Phase 10 (P10.1–P10.8) · T10.* · S‑65, S‑66 · **Gate G10**
- [ ] F4: Upload (direct PUT to the returned URL, progress, per-file errors), Describe (template picker in the MVP, with the free-text prompt enabled at F9), **Review with the pipeline rail** (horizontal on laptop following reading direction, vertical on phone and tablet, a keyboard-navigable list fallback), Approve (saffron stamp).
- [ ] F5: Run detail (polling with backoff, rail fill animation, cancel), Results (summary, filter tabs, virtualized table, lineage side sheet, downloads).
- [ ] F6: Home, Files, Runs history, Settings (profile, language, theme, timezone, MFA enroll with QR and recovery codes, members and invitations by role, export my data, delete account), invitation-accept page, MFA login challenge.
- [ ] F6b: First-run onboarding with sample files (P10.9), timezone-aware dates (P10.10).
- [ ] F7: Real API integration and contract mismatch fixes (Change Request only).

### F8 — UX iteration and accessibility → Phase 11 (P11.1–P11.5) · T11.* · **Gate G11**
- [ ] 12-shot matrix per screen, critique checklist (design.md §10), ≥ 2 rounds, usability sessions.

### F9 — AI planner UI → P12.5 · T12 UI parts · **Gate G12 (joint)**
### F10 — Workflows and replay UI → P13.4 · T13.4 · **Gate G13 (joint)**
### F11 — Formats UI → icons and copy per format, OCR review UI (P16.4)
### Shared — Phase 17 (P17.4, P17.7 cross-browser, P17.8 legal and landing pages, plus frontend parts of P17.5) · Phase 19 (P19.1 frontend, P19.4, P19.6)

## What the frontend guarantees to the backend
1. API calls only go through the generated client. There is no hand-built URL or ad-hoc type.
2. Every backend error code has an AR and an EN message (parity test in CI).
3. No business rule is enforced only in the UI. Hiding an action is UX, and the API remains the authority.
4. The idempotency key is generated once per user action and reused on retry.
5. Contract issues are raised as Change Requests, never worked around in the client.
