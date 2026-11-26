# Replora — Frontend Plan (Developer B)

**Version:** v1.1 (2026-11-23), derived from the master plan, with all decisions approved by the owner.
**Owns:** `frontend/**`, the design system, i18n (AR/EN, RTL), theming, responsive layouts, UX iteration, the Playwright E2E suite, and Lighthouse and axe CI.
**Co-owns:** `contracts/**` (with the backend developer), Phase 17 hardening, and Phase 19 go-live.
Step IDs (`P9.1`, `T10.2`, `S‑60`…) match the master plan, so both developers refer to the same items.

---

## 1. Working rules (MANDATORY)

### Process
- **Work incrementally, ALWAYS.** Small, simple steps. Validate and check each increment before moving on.
- Mark a step `[x]` only after its tests pass and its evidence (command plus result) is written in `session_log.md`.
- **A phase is finished only when** all of its steps are `[x]`, all of its tests in `testing.md` pass, and all of its items in `security.md` are verified.
- **Phase gate:** at the end of each phase, report the results to the gate approver — Developer B for this track's gates, both developers for the shared gates (0, 17, 18 and 19) — and **ask for permission** before starting the next phase.
- Your track's gates are approved independently of the backend track. **Integration milestones and shared phases need both tracks green.**
- Record all progress in `session_log.md` (started, finished, blockers, decisions, next step).

### Code style
- Do not overengineer. Do not program defensively. Use error handling (error boundaries, try/catch) only where needed.
- Identify the root cause before fixing issues. Prove it with evidence, then fix.
- Use the **latest library APIs** (verify versions at P0.1 and record them in `session_log.md`).
- Use `pnpm` as the package manager. Strict TypeScript, no `any`.
- Favor clear, concise doc comments (TSDoc). Be sparing with other comments.
- Favor short components, modules and functions. Name things clearly.

### Debugging and fixing
- ALWAYS identify the root cause BEFORE fixing. PROVE THE PROBLEM FIRST; don't guess.
- Try one test at a time. Be methodical. Don't jump to conclusions, and don't apply workarounds.
- For every bug, first write a failing test that reproduces it, then fix it, and keep the test.

---

## 2. Approved decisions that affect the frontend

| ID | Decision |
|---|---|
| D2 | **Next.js (App Router, latest) + TypeScript + Tailwind CSS v4**, deployed on Vercel. |
| D3 | **Backend-owned auth.** The browser gets `HttpOnly` cookies (`replora_access`, `replora_refresh`) plus a readable `replora_csrf` cookie, and sends its value as the `X-CSRF-Token` header on unsafe methods. The frontend never sees or stores tokens. |
| D7 | AI planner through the backend only. The UI must show **what is sent to AI** (metadata only by default) and an explicit consent toggle for sample rows. |
| D10 | Default language comes from `Accept-Language` (ar or en), with English as the fallback. The choice is saved in a cookie. |
| D12 | Optional TOTP MFA, strongly prompted for owners and admins. The UI needs enroll (QR plus recovery codes), challenge and disable screens. |
| D14 | Privacy policy and terms pages (bilingual), following Egypt PDPL plus GDPR-ready practices. |
| — | Limits shown in the UI come from `GET /limits` (`max_file_size`, `max_files_per_run`, `max_nodes`, `workspace_quota`), never hard-coded. Today: 50 MiB per file, 10 files per run, a per-workspace storage quota (413 `QUOTA_EXCEEDED`). |

---

## 3. Stack
Next.js (App Router) · React · TypeScript strict, **pinned to 6.0.3** (typescript-eslint supports `<6.1.0`; revisit TS 7 later) · Tailwind CSS v4 · next-intl · next-themes · TanStack Query · openapi-typescript + openapi-fetch · MSW · Vitest + Testing Library · Playwright + @axe-core/playwright · Lighthouse CI · Lucide icons · TanStack Virtual.
Runtimes are pinned in the repo: Node **26.13.1** (`.nvmrc`, `engines`) and pnpm **12.23.0** (root `package.json` → `packageManager`). The versions agreed at P0.1 are in `../session_log.md` (Recorded versions).
Verify the current major versions at P0.1. For example, Next.js 16 renamed `middleware.ts` to `proxy.ts`; confirm the current API before using it.

## 4. Frontend architecture
```
frontend/
├── src/app/[locale]/          routes (ar | en); each data route has loading.tsx
│   ├── (auth)/                sign-in, sign-up, verify, forgot, reset, mfa, invite/accept
│   ├── (app)/                 home, new-run/*, runs/[id], runs/[id]/results, workflows, files, settings
│   └── (public)/              landing, privacy, terms
├── src/components/ui/         design system (Button, Input, Dialog, Sheet, Table, Skeleton…)
├── src/components/features/   pipeline-rail, upload, results-table, lineage-sheet…
├── src/lib/api/               generated client + query hooks + error-code mapper
├── src/mocks/                 MSW handlers reading contracts/fixtures
├── messages/                  ar.json, en.json
└── tests/                     unit/, e2e/
```
- **Same-origin API:** Next.js rewrites `/api/*` to the backend, both locally and in production. There are no cross-site cookies, and API calls need no CORS. **The one exception is the file upload PUT:** in production it goes straight to a Supabase Storage signed URL (a different origin), so `connect-src` adds the storage origin from the `STORAGE_ORIGIN` environment variable. Locally the upload URL is same-origin and `connect-src 'self'` is enough. See api_contract.md §4.
- **Mocks switch:** `NEXT_PUBLIC_API_MOCKS=1` uses MSW, and unset uses the real backend.
- **Caching:** fingerprinted static assets are immutable, fonts are self-hosted via `next/font`, and API GETs use ETag revalidation. TanStack Query `staleTime`: runs in progress 0 (polling), finished runs 5 min, operations and templates 1 h.
- **Skeletons:** every data route has a `loading.tsx` whose skeleton matches the final layout (CLS ≈ 0). Skeletons are static under reduced motion.

---

## 5. Timeline and dependencies on the backend
*About 20 h/week. The week numbers are illustrative and are re-baselined after F3. Realistic MVP: 14–18 weeks.*

| Week | Frontend phase | Needs from backend | Sync point |
|---|---|---|---|
| 1 | F0 Foundation + contract draft | — | **G0, both agree the contract** |
| 2–3 | F1 Tokens, themes, i18n/RTL, app shell | — | — |
| 3–4 | F2 UI kit, skeletons, API client, MSW | domain fixtures | — |
| 4–5 | F3 Auth screens (mocked), loading routes | auth fixtures | **Gate G9** |
| 5–7 | F4 Wizard: upload, describe, review (pipeline rail), approve | validation fixtures, templates | — |
| 7–8 | F5 Run detail + results | run-state fixtures | **I1, real auth** |
| 8–9 | F6 Home, files, runs, settings, invitations, MFA, onboarding | — | **I2, real upload** |
| 10–11 | F7 Switch to the real API | frozen OpenAPI v1 | **I3, end to end → Gate G10** |
| 11–12 | F8 UX iteration and accessibility | — | **Gate G11** |
| 12–13 | F9 AI planner UI | AI planner endpoints | **I4 → Gate G12** |
| 13–14 | F10 Workflows and replay UI | replay endpoints | **I5 → Gate G13** |
| 15+ | F11 Format UI, OCR review UI, polish | new types and warning codes | — |
| later | Shared Phase 17, then Phase 19 | staging URL | **I6 staging**, go-live |

---

## 6. Phases

### F0 — Foundation (frontend half of Phase 0)
- [x] P0.1 Verify the latest stable versions of every frontend library. Record them in session_log.
- [x] P0.4 Next.js skeleton (TS, App Router, Tailwind v4, ESLint) with pnpm. It renders one page.
- [x] P0.5 `pnpm gen:api` generates the types from `contracts/openapi.json`. `contracts/openapi.json` is generated from the FastAPI route stubs (handlers return 501) from B0, never hand-written (api_contract.md §0). Regenerate the types whenever it changes.
- [x] P0.6 Pre-commit: ESLint, prettier, typecheck, gitleaks. (#19)
- [x] P0.7 CI jobs: lint, typecheck, Vitest, `pnpm build`, `pnpm audit --audit-level=high`, and a contract type check.
- [x] P0.9 Dev `/api` rewrite to the backend (`http://localhost:8000`), documented in the README. (#20)
- [x] P0.11 A global error boundary that shows the `correlation_id` from problem+json. (#20)
- [x] Co-write the `api_contract.md` draft with the backend developer. *(agreed at G0 in issue #1; `docs/api_contract.md`; same step ticked in `docs/backend_plan.md:39`)*
- [x] Tests T0.2, T0.3, T0.5 · Security S‑01, S‑03, S‑04, S‑05 · **Gate G0 (joint)**

### F1 — Tokens, themes, i18n, app shell (P9.1–P9.4)
- [x] P9.1 Design tokens from `design.md` §3 as CSS variables in Tailwind v4 `@theme`, light and dark. Write the token contrast test (T11.3) now. (#21)
- [x] P9.2 Theme with `next-themes`: system default, a Light, Dark and System toggle, a cookie so the server renders the right theme, and no flash on load. (#29)
- [x] P9.3 `next-intl` with `[locale]` routing (`/ar`, `/en`), `<html lang dir>` set on the server, Readex Pro (arabic and latin subsets) via `next/font`, and logical CSS properties only (a lint rule bans `left`, `right`, `ml-*`, `mr-*`, `pl-*`, `pr-*`). (#30, #37, #38)
- [x] P9.4 App shell: sidebar at ≥ 1024 px, icon rail at 640–1023 px, bottom tab bar below 640 px. No horizontal scroll at 320 px. (#46, #47)
- [ ] Tests T9.2, T9.3, T9.7, T9.9

### F2 — UI kit and data layer (P9.5–P9.6)
- [ ] P9.5 Components: Button, Input, Select, Dialog, Sheet, Toast, Tabs, Table, Badge, StatusChip (icon plus text), EmptyState, ErrorState, and Skeleton variants per layout. Each has a Vitest test in LTR and RTL.
  - Progress: 3 of 4 PRs merged — #48 (Button, Input, Badge primitives), #49 (Dialog and Sheet), #54 (Toast). Still open: Controls (Select, Tabs) and Data display (Table, StatusChip, EmptyState, ErrorState, Skeleton).
- [ ] P9.6 The generated client (openapi-fetch) with CSRF header injection (on app start, call `GET /auth/csrf` if the `replora_csrf` cookie is missing; login and register send the token too; re-read the cookie after login and logout because the token rotates), an ETag-aware fetch and a 401 → refresh → retry-once flow. TanStack Query provider. MSW handlers from `contracts/fixtures`, with scenario switches (each run state, slow network, each error code). An error-code → AR/EN message mapper with a parity test against `contracts/error-codes.json`, and a CI check that `ar.json` and `en.json` have the same keys.
  - Progress: PR 1 (#53, MSW auth handlers) merged. PR 2 (#58, typed client, CSRF, Idempotency-Key) in review. PRs 3 and 4 not started.
- [ ] Tests T9.1, T9.4

### F3 — Auth screens and loading routes (P9.7–P9.8) · Gate G9
- [ ] P9.7 Sign in, sign up, verify email, forgot and reset password, and the MFA challenge. Route protection runs in the Next.js request proxy, and `returnTo` accepts only relative same-origin paths.
- [ ] P9.8 A `loading.tsx` with a layout-matched skeleton for every data route. Suspense boundaries for in-page data.
- [ ] Tests T9.5, T9.6, T9.8 · Security S‑60…S‑64 · **Gate G9**

### F4 — Wizard: upload, describe, review, approve (P10.1–P10.4)
- [ ] P10.1 Upload: drag and drop plus file picker. For each file: call `upload-intent` (`display_name`, `size`, `content_type`; **no sha256**, the server computes it on `complete`), **PUT to the exact returned URL, method and headers**, then call `complete`. Show per-file progress and per-file validation errors. Enforce the file-count and size limits from `GET /limits` in the UI as well (the server still decides).
- [ ] P10.2 Describe: a template picker (`GET /templates`) in the MVP. The draft's `explanation` from the TemplatePlanner is `{key, params}`; translate it through next-intl (no free text from the server). The free-text prompt with example prompts in AR and EN is enabled at F9.
- [ ] P10.3 Review: the **pipeline rail** (design.md §2). It is horizontal on laptop and follows reading direction (RTL in Arabic), and vertical on phone and tablet. Station detail opens in a side panel (laptop) or a bottom sheet (phone). Validation errors and warnings are mapped to stations. There is a keyboard-navigable list fallback for screen readers. The parameter form is rendered from the operation's `params_schema` (the supported subset in `../api_contract.md` §5: `string`, `integer`, `boolean`, `enum`, string arrays, decimals as strings with `pattern`, and `x-replora-widget: "column"` for a column picker). Parameter edits send a PATCH with the **full** `definition` and `If-Match`; the server re-validates and returns the new `plan_hash`. On 412, show "This plan changed in another tab. Reload to see the latest version."
- [ ] P10.4 Approve: a plan summary and the saffron "Approve and run" button, sent with a single `Idempotency-Key` per click (reused on retry) and the current `plan_hash`. On 409 `PLAN_HASH_MISMATCH`, ask the user to review again.

### F5 — Run detail and results (P10.5–P10.6)
- [ ] P10.5 Run detail: poll `events?after=last_seq` every 1 s, backing off to 5 s, and stop at a terminal state. The rail fill animation is the one orchestrated motion in the product. Cancel run is optimistic, then confirmed. FAILED, PARTIAL and NEEDS_REVIEW each have an explanation and a next action.
- [ ] P10.6 Results: status summary, filter tabs (All, Different, Missing) and a search box mapped to `preview?offset&limit&status=matched|value_diff|missing_left|missing_right&q=`, a virtualized table backed by server pagination, sticky header and first column, RTL column order, a lineage side sheet on row click, and downloads (signed URL from the API).

### F6 — App pages, settings, onboarding (P10.7, P10.9, P10.10)
- [ ] P10.7 Home (recent runs, saved workflows), Files, Runs history. Settings: profile, language, theme, timezone; Security (MFA enroll with QR and recovery codes shown once, disable MFA); Members and invitations (by role); Export my data; Delete account (danger zone with typed confirmation). An invitation-accept page.
- [ ] P10.9 First-run onboarding: "Try it with sample files" runs the sample reconciliation once. It can be dismissed and reopened from Help.
- [ ] P10.10 Dates in the user's timezone and locale via `Intl`. Western digits by default, with Arabic-Indic digits as a display-only option.

### F7 — Real API integration (P10.8) · Gate G10
- [ ] P10.8 Turn MSW off and run the full suite against the local backend (`uv run python -m app.seed` creates the demo data). Fix mismatches through Change Requests only.
- [ ] Tests T10.* · Security S‑65, S‑66 · **I3 → Gate G10 (joint)**

### F8 — UX iteration and accessibility (Phase 11) · Gate G11
- [ ] P11.1 Screenshot matrix for every screen: 390, 820 and 1440 px × light and dark × AR and EN (12 shots each).
- [ ] P11.2 Critique every shot with the design.md §10 checklist and log the findings (high, medium, low) in session_log.
- [ ] P11.3 Fix, re-shoot and re-critique. At least 2 rounds, until no high or medium findings remain.
- [ ] P11.4 Accessibility: zero serious or critical axe violations, the full flow works by keyboard, focus is visible, contrast is AA, reduced motion is respected, and screen-reader labels exist in both languages.
- [ ] P11.5 Usability sessions with 3 or more people (Arabic and English). Fix the issues found.
- [ ] Tests T11.* · **Gate G11**

### F9 — AI planner UI (P12.5) · Gate G12 (joint)
- [ ] Enable the free-text prompt. Add a planner explanation panel (the AI planner returns `explanation.text`, already written in `user.locale`; template drafts keep using `key` + `params`) and a "What will be sent to AI" disclosure (from `ai_disclosure`). The sample-rows consent toggle is off by default. Fallback messages appear when the AI is unavailable or the budget is exceeded (`PLANNER_BUDGET_EXCEEDED`).
- [ ] Tests T12.U1–T12.U3

### F10 — Workflows and replay UI (P13.4) · Gate G13 (joint)
- [ ] Workflows list, version history, "Save as workflow", "Run again" dialog (`replay-check`), and a mapping editor for drifted columns. Saving a mapping creates a new version and needs a new approval.
- [ ] Tests T13.4

### F11 — Formats UI (Phases 14–16, UI parts)
- [ ] Icons and labels for each new `detected_type`. Copy for each new warning code (AR and EN). The OCR low-confidence review UI (P16.4).
- [ ] Tests T14.U1, T16.U1

### Shared — Phase 17 hardening (frontend parts)
- [ ] P17.4 Lighthouse CI budgets (NFR‑4, NFR‑5, NFR‑8), bundle analysis, image and font optimization, cache headers on static assets.
- [ ] P17.5 Frontend security review (security.md checklist), plus participation in the joint audit.
- [ ] P17.7 The Playwright suite is green on Chromium, WebKit and Firefox.
- [ ] P17.8 Bilingual landing, privacy and terms pages.
- [ ] Tests T17.3, T17.7, T17.8

### Shared — Phase 19 production (frontend parts)
- [ ] P19.1 Vercel frontend project with the `/api` rewrite to the production backend. Preview deployments for PRs, with deployment protection.
- [ ] P19.4 Nonce-based CSP and security headers verified on the production domain.
- [ ] P19.6 Smoke tests and the E2E suite on the production URL (phone, tablet and laptop × AR and EN).
- [ ] Tests T19.F1–T19.F4 · Security S‑61, S‑66, S‑80…S‑82, S‑84 · **Gate G19 (joint)**

---

## 7. What you guarantee to the backend
1. API calls go only through the generated client. There is no hand-built URL or ad-hoc type.
2. Every backend error code has an AR and an EN message (parity test in CI).
3. No business rule is enforced only in the UI. Hiding an action is UX, and the API remains the authority.
4. One `Idempotency-Key` per user action, reused on retry.
5. Contract issues are raised as Change Requests and never worked around.

## 8. What the backend guarantees to you
1. Every endpoint has committed request and response fixtures in `contracts/fixtures/` **before** its implementation merges.
2. Every new error code is added to `contracts/error-codes.json` in the same PR.
3. `contracts/openapi.json` is regenerated in every API PR (enforced by a CI drift check).
4. `uv run python -m app.seed` creates a demo user, workspace and sample files for local integration.
5. No breaking changes to v1 after the freeze.
