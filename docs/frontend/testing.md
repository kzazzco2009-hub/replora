# Replora — Frontend Testing Plan

**A phase is not finished until every test in its section passes** and the evidence (command plus result) is logged in `session_log.md`.

## 0. Tooling and conventions

| Layer | Tool | Command |
|---|---|---|
| Unit and component | Vitest + Testing Library (jsdom) | `pnpm test` |
| API mocking | MSW (fixtures from `contracts/fixtures`) | — |
| Contract types | the generated client must type-check against `contracts/openapi.json` | `pnpm gen:api && pnpm typecheck` |
| E2E | Playwright | `pnpm e2e` |
| Accessibility | @axe-core/playwright | in the E2E run |
| Performance | Lighthouse CI | `pnpm lhci` |
| Visual regression | Playwright screenshots | `pnpm e2e --project=visual` |
| Security | `pnpm audit`, ESLint security rules, gitleaks | CI |

**Playwright projects:**

| Project | Viewport | Device |
|---|---|---|
| `laptop` | 1440×900 | Chromium |
| `tablet` | 820×1180 | iPad, WebKit |
| `phone` | 390×844 | iPhone (WebKit) or Pixel (Chromium) |
| `firefox` | 1440×900 | Firefox (from P17.7) |

Each project runs in `ar` and `en` and in `light` and `dark`, through the test parameters `locale` and `colorScheme`.

**Coverage gate:** `src/lib/**` and `src/components/**` ≥ 80 % lines.
**Rule:** for every bug, write a failing test that reproduces it first, then fix it.
**Naming:** `<component>.test.tsx` next to the component. E2E specs go in `tests/e2e/<flow>.spec.ts`.

### Non-functional targets owned by the frontend

| ID | Target |
|---|---|
| NFR‑4 | Lighthouse (mobile): Performance ≥ 90, Accessibility ≥ 95, Best Practices ≥ 95 |
| NFR‑5 | Core Web Vitals: LCP < 2.5 s, CLS < 0.05, INP < 200 ms |
| NFR‑6 | Zero serious or critical axe violations on all screens × 2 languages × 2 themes |
| NFR‑8 | Initial JS for an authenticated page < 200 KB gzip |
| NFR‑11 | Last 2 versions of Chrome, Edge, Firefox and Safari; iOS Safari 17+; Android Chrome |
| NFR‑14 | ESLint clean, components ≤ ~150 lines as guidance, no circular imports |

---

## F0 — Foundation
- [ ] T0.2 The home page renders (Vitest smoke) and `pnpm build` succeeds.
- [ ] T0.3 CI is green on a no-op PR. CI fails on an intentional lint or type error (prove the gate works, then revert).
- [ ] T0.5 gitleaks blocks a commit that contains a fake secret.
- [ ] T0.F1 The error boundary renders the `correlation_id` from a mocked 500 problem+json.

## F1–F3 — Foundation UI (Phase 9)
**Unit (Vitest)**
- [ ] T9.1 Every UI kit component renders, works with the keyboard and has an accessible name. Each is tested under both `dir="ltr"` and `dir="rtl"`.
- [ ] T9.2 The theme toggle persists. The system preference is respected. The SSR HTML has the correct theme class before hydration (no flash).
- [ ] T9.3 i18n:
  - every key exists in both `ar.json` and `en.json` (key parity test);
  - Arabic plural forms (zero, one, two, few, many, other) render;
  - numbers and dates are formatted per locale.
- [ ] T9.4 The error-code mapper has an AR and an EN message for **every** code in `contracts/error-codes.json` (parity test), and `ar.json` and `en.json` have identical key sets (CI check).
- [ ] T9.U1 With no `replora_csrf` cookie, the app calls `GET /auth/csrf` before the first unsafe request. The API client sends `X-CSRF-Token` on POST, PUT, PATCH and DELETE (login and register included), and never on GET. After login and logout it uses the rotated token. On a 401 it refreshes once and retries once; a second 401 redirects to sign-in.

**E2E (mocked API)**
- [ ] T9.5 Sign up, sign in, sign out, and the MFA challenge, plus validation errors, on phone, tablet and laptop.
- [ ] T9.6 A protected route redirects to sign-in and returns to the original URL. `returnTo=https://evil.com` and `//evil.com` are ignored.
- [ ] T9.7 Responsive shell: sidebar at 1440, rail at 820, bottom tabs at 390. No horizontal scroll at 320 px.
- [ ] T9.8 Skeletons appear during an artificial MSW delay, and the measured CLS is < 0.05.
- [ ] T9.9 The language switch keeps the current page and flips `dir`. Directional icons mirror. IDs, numbers and code stay LTR (`bdi`).

## F4–F7 — Core flow (Phase 10)
**E2E (mocked, then against the real backend at F7)**
- [ ] T10.1 The full wizard (upload, describe, review, approve, run, results) with the acceptance data shows 4 statuses: matched, different, missing on each side. It runs on phone, tablet and laptop × AR and EN × light and dark.
- [ ] T10.2 Upload edge cases:
  - wrong type gives a per-file error;
  - oversize (`max_file_size` + 1 byte, 50 MiB today) is blocked;
  - one file more than `max_files_per_run` (an 11th file today) is blocked;
  - the limits come from a mocked `GET /limits` (change them in MSW and the UI follows);
  - a network drop mid-upload shows retry, and the retry succeeds;
  - a duplicate file is flagged after `complete` (same `sha256` returned by the server as an existing file);
  - `upload-intent` is sent without `sha256`;
  - a 413 `QUOTA_EXCEEDED` message is shown.
- [ ] T10.3 Validation errors appear on the correct station in the pipeline rail and in the list fallback.
- [ ] T10.4 Approve:
  - the button is disabled until the plan is valid;
  - a double click sends one request (same Idempotency-Key);
  - a 409 `PLAN_HASH_MISMATCH` asks the user to review again;
  - a PATCH returning 412 shows the reload message.
- [ ] T10.5 Cancel during a run shows CANCELLED. FAILED, PARTIAL and NEEDS_REVIEW each show a distinct explanation and next action.
- [ ] T10.6 Results table: 100k rows (server paginated) scroll smoothly (frames < 16 ms on laptop), with sticky header and first column, and RTL column order in Arabic.
- [ ] T10.7 Empty states (no files, no runs, no workflows) each have a primary action.
- [ ] T10.8 Browser back and forward work through the wizard. A refresh mid-wizard keeps the draft.
- [ ] T10.9 The full suite passes against the real local backend with MSW disabled.
- [ ] T10.10 Dates display correctly for `Africa/Cairo` and `Asia/Riyadh` (Playwright `timezoneId`), including a DST transition.
- [ ] T10.11 Onboarding: a new user completes the sample run in AR and EN. Once dismissed it stays hidden, and it can be reopened from Help.
- [ ] T10.U1 Settings:
  - MFA enroll shows the QR and recovery codes once;
  - invitations can be sent and revoked;
  - the invite-accept page handles valid, expired and revoked tokens;
  - delete account requires typed confirmation;
  - export shows progress and then a download.
- [ ] T10.U2 Role-based UI: a viewer sees no upload, approve or delete actions. A direct URL to an admin page shows the 403/404 state (the API is still the authority).

## F8 — UX iteration and accessibility (Phase 11)
- [ ] T11.1 axe: zero serious or critical violations on all screens × AR and EN × light and dark.
- [ ] T11.2 Keyboard-only run of the full wizard. The focus order is logical in both LTR and RTL. The rail is navigable with the arrow keys.
- [ ] T11.3 Every token text/background pair passes WCAG AA in both themes (automated).
- [ ] T11.4 With `reducedMotion: 'reduce'`, no non-essential animation runs and skeletons are static.
- [ ] T11.5 Screen-reader smoke test (NVDA on Windows, VoiceOver on iOS) for the wizard and results. Run state changes are announced politely.
- [ ] T11.6 Visual regression baselines are committed for the 12-shot matrix of every screen.
- [ ] T11.7 Usability sessions (≥ 3 people): task success ≥ 90 % for "reconcile two files" without help.

## F9 — AI planner UI (Phase 12)
- [ ] T12.U1 The "What will be sent to AI" disclosure matches `ai_disclosure`. The consent toggle is off by default and is sent as `share_samples`.
- [ ] T12.U2 An invalid AI draft shows validation errors (it never reaches approval as valid). AI unavailable shows the fallback to templates.
- [ ] T12.U3 `PLANNER_BUDGET_EXCEEDED` (429) shows a clear message and suggests templates.

## F10 — Workflows and replay (Phase 13)
- [ ] T13.4 Save as workflow, view versions, run again on compatible files, and run again on drifted files (the mapping editor creates a new version and a new approval is needed). Tested on phone, tablet and laptop.

## F11 — Formats UI (Phases 14–16)
- [ ] T14.U1 Every `detected_type` has an icon and a label, and every warning code has AR and EN copy (parity test).
- [ ] T16.U1 OCR review UI: low-confidence fields are highlighted, can be edited and confirmed by keyboard, and work in RTL.

## Shared — Phase 17
- [ ] T17.3 Lighthouse CI meets NFR‑4, NFR‑5 and NFR‑8 on 5 key screens (home, upload, review, results, settings).
- [ ] T17.7 The full Playwright suite is green on Chromium, WebKit and Firefox.
- [ ] T17.8 The landing, privacy and terms pages exist in AR and EN, are linked from the footer and the sign-up page, and pass axe.
- [ ] T17.F1 XSS payloads (`<img src=x onerror=alert(1)>`) in file names, column names and cell values render as text everywhere.

## Shared — Phase 19 (production)
- [ ] T19.F1 Smoke test on the production URL: sign up, upload, run, download.
- [ ] T19.F2 The E2E suite passes on production for the phone, tablet and laptop projects × AR and EN.
- [ ] T19.F3 Headers: the CSP has a nonce and `frame-ancestors 'none'`. HSTS, nosniff and Referrer-Policy are present (grade A).
- [ ] T19.F4 Cache headers: `/_next/static/*` is `immutable`, HTML pages are not publicly cached, and fonts are self-hosted.
