# Replora — Security Plan

Security is implemented **inside each phase**, not at the end. Every control has an ID (`S‑xx`), the phase where it is built, how it is implemented, and how it is verified (a test ID from `testing.md` or a manual check). A phase is not finished until all of its S‑items are verified and logged in `session_log.md`.

Reference frameworks: **OWASP Top 10:2025**, OWASP ASVS 5 (Level 2 target), OWASP File Upload Cheat Sheet, OWASP Top 10 for LLM Applications, and NIST SP 800‑63B for passwords.

## OWASP Top 10:2025 mapping

| OWASP 2025 | Replora controls |
|---|---|
| A01 Broken Access Control | S‑14, S‑21…S‑23, S‑29, S‑36, S‑40, S‑45 |
| A02 Security Misconfiguration | S‑02, S‑50, S‑53, S‑80, S‑81, S‑84 |
| A03 Software Supply Chain Failures | S‑03, S‑04, S‑05, S‑85, S‑86 |
| A04 Cryptographic Failures | S‑20, S‑24, S‑28, S‑46, S‑82 |
| A05 Injection (SQL, XSS, formula, prompt) | S‑15, S‑37, S‑38, S‑60, S‑61, S‑71 |
| A06 Insecure Design | S‑10…S‑13, S‑30…S‑35, S‑47, S‑70 |
| A07 Authentication Failures | S‑20, S‑24…S‑28 |
| A08 Software or Data Integrity Failures | S‑11, S‑16, S‑44, S‑72 |
| A09 Security Logging and Alerting Failures | S‑26, S‑52, S‑83, S‑87 |
| A10 Mishandling of Exceptional Conditions | S‑17, S‑51 |

---

## Phase 0 — Foundation
| ID | Control | Implementation | Verify |
|---|---|---|---|
| S‑01 | **Secrets are never committed** | Root `.gitignore` is created before the first commit (`.env*` except `.env.example`). gitleaks runs in pre-commit and CI. The existing `OPENROUTER_API_KEY` is **rotated if it was ever shared or synced publicly** (the folder is on OneDrive). | T0.5, T0.6 |
| S‑02 | Config via environment only | `pydantic-settings`, with secrets typed as `SecretStr` so they are never logged. The app refuses to start in prod mode if required secrets are missing or `DEBUG` is on. | unit test |
| S‑03 | Locked dependencies | `uv.lock` and `pnpm-lock.yaml` are committed. CI uses `uv sync --locked` and `pnpm install --frozen-lockfile`. | CI |
| S‑04 | Dependency vulnerability scanning | `uv run pip-audit`, `pnpm audit --audit-level=high` and Dependabot (weekly). CI fails on high or critical. | CI |
| S‑05 | Repository protection | Protected `main`, required reviews from the other developer, required status checks, no force-push, signed commits recommended, CODEOWNERS. | manual check, logged |

**Phase 0 status** (the evidence is in `session_log.md`, Session 13):
- [x] **S‑01:** `.gitignore` before the first commit, gitleaks in pre-commit (#14, with the OpenRouter rule) and CI. T0.5 and T0.6 pass. The old OpenRouter key was deleted by the owner.
- [ ] **S‑02:** settings come from the environment (`pydantic-settings`, `SecretStr`). **Missing:** the app does not yet refuse to start in production when a required secret is missing or `DEBUG` is on.
- [x] **S‑03:** `uv.lock` and `pnpm-lock.yaml` are committed. CI runs `uv sync --locked` and `pnpm install --frozen-lockfile`.
- [x] **S‑04:** CI runs `uv run pip-audit` and `pnpm audit --audit-level=high`. Dependabot runs weekly for uv, npm and GitHub Actions.
- [ ] **S‑05:** CODEOWNERS and the PR template are in. Protecting `main` needs GitHub Pro, a public repo or an organization (the owner's decision). Until then it's the manual rule in `decisions.md`. The protection is ready as code in `.github/rulesets/main.json` (apply and verify steps in its README). S‑05 is ticked once the admin has applied it and `gh api repos/kzazzco2009-hub/replora/rules/branches/main` shows its rules.

## Phase 1–3 — Core engine (secure by design)
| ID | Control | Implementation | Verify |
|---|---|---|---|
| S‑10 | **No arbitrary code execution** | Only registered operations run. There is no `eval`, `exec` or `pickle`, and no dynamic imports from user or AI data. A semgrep rule bans those calls in `app/`. | semgrep in CI |
| S‑11 | Approval integrity | Approval is bound to `plan_hash` (canonical SHA‑256). Any change invalidates it. The approver ID and time are stored. | T1.3, T1.4, T3.1 |
| S‑12 | Resource-exhaustion limits in the validator | Limits on nodes, depth, fan-in and fan-out, file counts and sizes are enforced **before** execution. | T2.5 |
| S‑13 | Execution limits | Node timeout of 120 s and run timeout of 900 s, a memory guard and a temp-dir quota (500 MiB). Retries happen only for transient errors (at most 2). | T3.4, T17.6 |

## Phase 4 — Persistence
| ID | Control | Implementation | Verify |
|---|---|---|---|
| S‑14 | **Tenant isolation at the data layer** | Every repository function requires `workspace_id`, so no unscoped query is possible. A lint test checks that every `select()` on a tenant table includes the workspace filter. | T4.3, T5.10 |
| S‑15 | **SQL injection prevention** | SQLAlchemy Core and ORM bound parameters only. There is no f-string or `%` SQL, and `text()` is allowed only with bind params (semgrep rule). Sort and filter fields are whitelisted enums, never raw column names from requests. | semgrep, schemathesis T8.2, manual payload test (`' OR 1=1--`, `; DROP TABLE`) in filters and sort |
| S‑16 | Idempotency and integrity | Unique `(workspace_id, idempotency_key)`. Artifacts are addressed by sha256 and verified on read. | T8.3 |
| S‑17 | Safe failure | DB errors map to generic 500 problem responses with a correlation ID. The details go to logs only. | T8.8 |

## Phase 5 — Authentication and authorization
| ID | Control | Implementation | Verify |
|---|---|---|---|
| S‑20 | Password storage | argon2id (`pwdlib`) with recommended parameters, rehashed on login if the parameters change. | T5.1 |
| S‑21 | **Role-based permissions** | One permission matrix in code (table below). The `require(perm)` dependency is applied on every router, and a startup check fails if any route lacks a permission declaration. | T5.9 |
| S‑22 | **Broken access control / IDOR** | Resources are fetched by `(workspace_id, id)`. Another workspace's resource gives **404**. IDs are UUIDv7 (non-sequential, but not relied on for security). | T5.10 |
| S‑23 | Mass assignment | Request models are separate from DB models, with `extra="forbid"`. Role, owner and workspace_id are never accepted from the client body. | T8.1 |
| S‑24 | Session security | Access JWT (15 min, `EdDSA` or `HS256` with a ≥ 256-bit key; `alg` is pinned, and `none` is rejected). The opaque refresh token is stored as a SHA‑256 hash and **rotated on every use, with reuse detection**. Cookies are `HttpOnly; Secure; SameSite=Lax; Path=/`. | T5.3, T5.4, T5.6 |
| S‑25 | CSRF | Double-submit token header on POST, PUT, PATCH and DELETE, plus `SameSite=Lax` and an Origin header check. | T5.5 |
| S‑26 | Brute-force and enumeration | DB-backed rate limits: login 5 per 15 min per account and per IP hash, register and forgot-password 3 per hour per IP. Responses are generic. The audit log covers all auth events. | T5.7, T5.11, T5.12 |
| S‑27 | Account recovery | Single-use hashed reset and verify tokens (30 min). All sessions are revoked on password change. There is no security question. | T5.8 |
| S‑28 | MFA (TOTP) | RFC 6238 TOTP. The secret is encrypted at rest (an app-level key from the environment). Recovery codes are hashed and single-use. Codes are throttled. Owners and admins are prompted to enroll. The login challenge is an HttpOnly, Secure, SameSite=Lax `replora_mfa_challenge` cookie: random, stored hashed, bound to the user, valid 5 minutes and single use. No session cookies are issued before the challenge succeeds. | T5.15 |
| S‑29 | Privacy rights and invitations | Data export holds only the user's own data. Deletion revokes sessions, purges files after a grace period and anonymizes the audit actor. Invite tokens are hashed, single-use and bound to an email, expire after 7 days, and cannot grant a role above the inviter's. | T5.13, T5.14 |

**Permission matrix (initial)**

| Permission | owner | admin | member | viewer |
|---|:-:|:-:|:-:|:-:|
| workspace.manage / delete | ✔ | — | — | — |
| members.manage | ✔ | ✔ | — | — |
| files.upload / delete | ✔ | ✔ | ✔ | — |
| files.read / download | ✔ | ✔ | ✔ | ✔ |
| drafts.create / workflows.save | ✔ | ✔ | ✔ | — |
| runs.approve / cancel | ✔ | ✔ | ✔ (own runs) | — |
| runs.read / outputs.download | ✔ | ✔ | ✔ | ✔ |
| audit.read | ✔ | ✔ | — | — |

## Phase 6–7 — File intake and processing
| ID | Control | Implementation | Verify |
|---|---|---|---|
| S‑30 | Content-based type detection | Magic bytes plus structural parse. The extension and client MIME are never trusted. An allow-list holds only the 14 supported types. | T6.1 |
| S‑31 | Size limits | 50 MiB per file, enforced on intent (declared size), on storage (bucket limit) and on complete (actual size). | T6.2, T18.4 |
| S‑32 | **Zip bomb / zip slip** | Streaming extraction with counters (members ≤ 25, uncompressed ≤ 200 MiB, ratio ≤ 100:1). No nested archives. Absolute paths, `..` and symlinks are rejected, and paths are never joined with user input. | T6.4–T6.6 |
| S‑33 | Filename safety | The storage key is `workspace_id/uuid`. The display name is sanitized (control characters, bidi overrides, length) and is never used in a filesystem path. | T6.3 |
| S‑34 | Upload integrity | sha256 is computed by the server on complete (a client-supplied hash is never trusted), and the declared size must match the stored size. The upload URL is single-purpose and short-lived (≤ 10 min). | T6.8 |
| S‑35 | Processing isolation | Parsers run with temp-dir quotas and timeouts. There is no network access from operations. Parsers never execute macros, scripts or embedded objects. | T3, T15.2 |
| S‑36 | Download authorization | Each download goes through the API, which checks permission and issues a signed URL (≤ 5 min) with `Content-Disposition: attachment`. | T6.7 |
| S‑47 | Malware in uploaded originals (**accepted risk for v1**) | Files are only parsed by registered adapters, never executed. Downloads are `attachment` with `nosniff`, and macro formats are rejected. If D9 introduces a container worker, add a ClamAV scan on `complete`. Re-assessed at Phase 17. | review at G17 |
| S‑37 | **CSV and spreadsheet formula injection** | Output cells starting with `= + - @ \t \r` are prefixed with `'`. This applies to CSV and XLSX writers. | T7.8, T14.6 |

## Phase 8 — API
| ID | Control | Implementation | Verify |
|---|---|---|---|
| S‑50 | CORS | Browser traffic is same-origin via the `/api` rewrite, so CORS uses an explicit allow-list (the frontend origins only) and never `*` with credentials. The only cross-origin browser request is the upload PUT to the Supabase Storage signed URL in production; its CORS is verified in the P8.8 spike. | T8.1 |
| S‑51 | Error handling | RFC 9457 problem+json with a stable `code`. No stack traces, SQL or paths. Unhandled errors are logged with a correlation ID. | T8.8 |
| S‑52 | Audit logging | Approve, cancel, delete, role change, download, auth events and planner calls. Logs hold no passwords, tokens or file contents, and IPs are stored hashed. | T5.12, review |
| S‑53 | Request limits | Max JSON body 1 MB, pagination `limit` ≤ 100, prompt length ≤ 4,000 characters, plus per-user rate limits on expensive endpoints (drafts, runs). | T8.5 |

## Phase 9–11 — Frontend
| ID | Control | Implementation | Verify |
|---|---|---|---|
| S‑60 | **XSS** | React escaping only. `dangerouslySetInnerHTML` is banned (ESLint rule). File contents are rendered as text in the table viewer. User-supplied names are never placed in `href`. | lint, E2E with `<img onerror>` payload in filename and cells |
| S‑61 | Content Security Policy | A nonce-based CSP set in the Next.js proxy: `default-src 'self'; script-src 'self' 'nonce-…' 'strict-dynamic'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'`, plus the Supabase storage origin in `connect-src`. The storage origin comes from the `STORAGE_ORIGIN` environment variable (empty locally, where uploads are same-origin), so there is one CSP code path for every environment. | T19.4 |
| S‑62 | Open redirect | The `returnTo` parameter only allows relative same-origin paths. | T9.6 |
| S‑63 | No tokens in JS | The auth cookie is `HttpOnly`. Nothing sensitive goes in `localStorage`. Only theme and locale are persisted client-side. | code review, E2E check of storage |
| S‑64 | Client-side checks are UX only | Every check is repeated on the server. The UI hides actions by role, but the API enforces them. | T5.9 |
| S‑65 | Direct upload safety | The PUT goes to the signed URL from the API only. The URL comes from the API response, never from user input. | T10.2 |
| S‑66 | Clickjacking and MIME sniffing | `frame-ancestors 'none'`, `X-Content-Type-Options: nosniff` and `Referrer-Policy: strict-origin-when-cross-origin`. | T19.4 |

## Phase 12 — AI planner (OWASP LLM Top 10)
| ID | Control | Implementation | Verify |
|---|---|---|---|
| S‑70 | AI cannot act | The planner returns a draft only. The validator and explicit human approval are always required. The planner has no tools and no network. | T12.1 |
| S‑71 | **Prompt injection** | File-derived text is placed in delimited data blocks with an instruction that it is data. The output must match the JSON schema and the registered operations only. | T12.3 |
| S‑72 | Data minimization | By default only metadata is sent, with opt-in per-run consent for samples. The consent is recorded in the audit log. | T12.2 |
| S‑73 | Cost and abuse limits | A per-workspace daily token and cost cap, per-user rate limit, timeout and output length cap. | T12.5 |
| S‑74 | Key protection | The OpenRouter key is server-side only (`SecretStr`), never reaches the browser and is never logged. | code review, bundle grep for `sk-or` |

## Phase 14–16 — Formats
| ID | Control | Implementation | Verify |
|---|---|---|---|
| S‑38 | **XXE and entity expansion** | `defusedxml` only. DTDs and external entities are forbidden, with depth and size limits. | T14.4 |
| S‑39 | Spreadsheet safety | `openpyxl` read-only, no formula evaluation, macros are ignored, and `.xlsm` is rejected or its macros stripped. | T14.2 |
| S‑41 | PDF safety | No JavaScript or action execution, encrypted PDFs are rejected, page limits apply and there is a parser timeout. | T15.1 |
| S‑42 | Office macro safety | `.docm`, `.pptm` and `.xlsm` are rejected. Embedded OLE objects are ignored with a warning. | T15.2 |
| S‑43 | Image bombs and metadata | `Image.MAX_IMAGE_PIXELS` is set to 20 MP and checked before decode. EXIF is stripped on output. | T16.1, T16.2 |

## Phase 18 — Supabase
| ID | Control | Implementation | Verify |
|---|---|---|---|
| S‑40 | **RLS everywhere** | `ALTER TABLE … ENABLE ROW LEVEL SECURITY` on every table, applied in a migration with no policies for `anon` or `authenticated`. The app schema is removed from the exposed Data API schemas. | T18.2 |
| S‑44 | Least-privilege DB role | The backend uses a dedicated role with only DML rights on the app schema. Migrations use a separate role. The service-role key is **never** in the frontend or in Vercel frontend env. | review, bundle grep |
| S‑45 | Private storage | A private bucket, signed URLs only, bucket size and MIME limits, and object paths prefixed by workspace. | T18.4 |
| S‑46 | Encryption and backups | TLS is enforced on DB connections (`sslmode=require`). Supabase encryption at rest. PITR or daily backups with a restore drill. | T18.5, manual drill |

## Phase 19 — Vercel production
| ID | Control | Implementation | Verify |
|---|---|---|---|
| S‑80 | Security headers | CSP (S‑61), `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`, nosniff, Referrer-Policy, a Permissions-Policy that disables unused features, and COOP. | T19.4 |
| S‑81 | Environment separation | Separate Supabase projects and secrets for preview, staging and production. Previews never use production data. Preview deployments are protected (Vercel deployment protection). | review |
| S‑82 | TLS | HTTPS only, HSTS, Secure cookies, and a TLS 1.2 minimum. | T19.4 |
| S‑83 | Monitoring and alerting | Error tracking (PII scrubbed), alerts on 5xx, auth failure spikes, failed-run spikes and rate-limit spikes. | T19.7 |
| S‑84 | Debug off | No debug, docs or OpenAPI UI publicly in production (the OpenAPI UI is disabled or behind auth). | smoke check |
| S‑85 | Release integrity | Deploys come from protected `main` only, through required checks. Rollback is tested. A dependency audit runs before release. | T19.6 |
| S‑86 | SBOM | A CycloneDX SBOM is generated per release for the backend (uv) and the frontend (pnpm) and attached to the GitHub release. | CI artifact |
| S‑87 | Log retention and PII | Logs are kept 30 days. Passwords, tokens, cookies, file contents and raw emails are scrubbed (from P0.11). IPs are hashed. The access-log format is reviewed. | T0.7, review |

---

## Per-phase security exit checklist (copy into session_log for each phase)
- [ ] All S‑items for this phase are implemented and verified (test IDs pass).
- [ ] semgrep, bandit, pip-audit and pnpm audit have no new high or critical findings.
- [ ] gitleaks is clean.
- [ ] A new endpoint has a permission declaration plus authz matrix rows (T5.9 regenerated).
- [ ] A new input has bounds and validation. A new output is encoded or escaped.
- [ ] A new table has workspace scoping, indexes, and RLS in the Supabase migration.
- [ ] The reviewer (the other developer) confirmed the security impact section of the PR.
