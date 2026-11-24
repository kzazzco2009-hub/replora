# Replora — Frontend Security Plan

Security is built **inside each phase**. An item is done only when its verification passes and it is logged in `session_log.md`.
References: OWASP Top 10:2025, OWASP ASVS 5 (Level 2), and the OWASP cheat sheets for XSS, CSP and CSRF.
The backend enforces all authorization. **The frontend never relies on hiding UI for security.**

## Shared repository controls (F0)
| ID | Control | Implementation | Verify |
|---|---|---|---|
| S‑01 | Secrets are never committed | `.env*` is gitignored except `.env.example`. gitleaks runs in pre-commit and CI. Only `NEXT_PUBLIC_*` variables reach the browser, and **they must not contain secrets**. | T0.5, a CI grep of the build output for `sk-`, `service_role` and `SUPABASE_SERVICE` |
| S‑03 | Locked dependencies | `pnpm-lock.yaml` is committed, and CI uses `pnpm install --frozen-lockfile`. | CI |
| S‑04 | Vulnerability scanning | `pnpm audit --audit-level=high` and Dependabot (weekly). CI fails on high or critical. | CI |
| S‑05 | Repository protection | Protected `main`, required reviews and CI, no force-push, and CODEOWNERS (`frontend/**` is yours; `contracts/**`, `docs/**`, `.github/**` and root files need both developers). Until the repo moves to an organization, protection is a manual rule: no direct push to `main`, no self-merge. | manual check, logged |

## F1–F3 (Phase 9)
| ID | Control | Implementation | Verify |
|---|---|---|---|
| S‑60 | **XSS** | React escaping only. `dangerouslySetInnerHTML` is banned (ESLint `react/no-danger`, set to error). File names, column names and cell values are always rendered as text. No user data goes into `href`, `src` or `style`. No `eval` or `new Function`. | lint, T17.F1 |
| S‑61 | Content Security Policy | A per-request nonce set in the Next.js proxy: `default-src 'self'; script-src 'self' 'nonce-…' 'strict-dynamic'; style-src 'self' 'nonce-…'; img-src 'self' data: blob:; connect-src 'self' <supabase-storage-origin>; object-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'`. The storage origin comes from the `STORAGE_ORIGIN` environment variable (empty locally, where uploads are same-origin), so there is one CSP code path for every environment. | T19.F3 |
| S‑62 | Open redirect | `returnTo` accepts only paths that start with a single `/`. `//`, `http:`, `https:`, `javascript:` and backslashes are rejected. | T9.6 |
| S‑63 | No tokens in JavaScript | Auth cookies are `HttpOnly`, so the app never reads them. Only the theme, locale and onboarding-dismissed flag are stored client-side. Nothing sensitive goes in `localStorage` or `sessionStorage`. | code review, an E2E assertion on storage contents |
| S‑64 | Client checks are UX only | Every limit and permission shown in the UI is also enforced by the API. The UI handles 401, 403, 404, 413 and 429 gracefully. | T10.U2 |
| S‑25 | CSRF (client side) | Get the cookie from `GET /auth/csrf` when it is missing. Read the `replora_csrf` cookie and send it as `X-CSRF-Token` on every unsafe method (login and register included), through the generated client only. Use the rotated token after login and logout. | T9.U1 |
| S‑28 | MFA UX safety | Recovery codes are shown once with "copy" and "download as .txt" options and are never stored client-side. The OTP input is `autocomplete="one-time-code"`, LTR and numeric. The login challenge state lives only in the HttpOnly `replora_mfa_challenge` cookie; the app keeps nothing about it client-side and returns to the sign-in form on 401 `MFA_CHALLENGE_INVALID`. | T10.U1 |

## F4–F7 (Phase 10)
| ID | Control | Implementation | Verify |
|---|---|---|---|
| S‑65 | Direct upload safety | The PUT goes only to the `upload.url` returned by the API, with its exact method and headers. The URL is never built from user input. The browser does not hash files: the server computes sha256 on `complete` and never trusts a client hash (backend S‑34). | T10.2 |
| S‑66 | Clickjacking and MIME sniffing | `frame-ancestors 'none'`, `X-Content-Type-Options: nosniff` and `Referrer-Policy: strict-origin-when-cross-origin`. | T19.F3 |
| S‑F1 | Safe downloads | Downloads use the short-lived signed URL from the API, opened as a download (`attachment`). File contents are never rendered as HTML, and previews come from the JSON preview endpoint. | E2E |
| S‑F2 | Destructive actions | Delete account and delete workspace need typed confirmation. Delete file and cancel run need a confirm dialog. | T10.U1 |

## F9 (Phase 12) — AI transparency
| ID | Control | Implementation | Verify |
|---|---|---|---|
| S‑72 | Data minimization UX | The disclosure shows exactly which fields go to the AI. The sample-rows consent is **off by default** and applies per run only. | T12.U1 |
| S‑74 | No AI keys in the browser | All AI calls go through the backend. The CI grep checks the build output for `sk-or`. | CI |

## Phase 19 (production)
| ID | Control | Implementation | Verify |
|---|---|---|---|
| S‑80 | Security headers | CSP (S‑61), `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`, nosniff, Referrer-Policy, a Permissions-Policy that disables camera, microphone and geolocation, and `Cross-Origin-Opener-Policy: same-origin`. | T19.F3 |
| S‑81 | Environment separation | Preview deployments point to the staging API only and are protected by Vercel deployment protection. | review |
| S‑82 | TLS | HTTPS only with HSTS. | T19.F3 |
| S‑84 | No debug in production | No source maps served publicly (or uploaded privately to error tracking only), no React DevTools hints, and no mock handlers in the production build. | build check |

## Per-phase security exit checklist (copy into session_log for each phase)
- [ ] All S‑items for this phase are implemented and verified.
- [ ] `pnpm audit` has no new high or critical findings. gitleaks is clean.
- [ ] No `dangerouslySetInnerHTML`, `eval` or unsafe `href` with user data (lint clean).
- [ ] New API calls go only through the generated client (CSRF included).
- [ ] New user-visible data is rendered as text. New redirects are validated.
- [ ] The backend developer reviewed the security impact section of the PR.
