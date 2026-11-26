# Replora — Master Implementation Plan

**Created:** 2026-11-23
**Source:** `../Replora_Complete_Project_Plan_AR.md` (v0.6 Architecture Closure + v0.6.1 Sprint plan, Arabic)
**Status:** DRAFT — awaiting owner review. **Nothing is implemented until this plan is approved.**

Companion documents (all in `docs/` in the repo; the old OneDrive `Planning/` copy is frozen):

| File | Purpose |
|---|---|
| `plan.md` | This file. Phases, steps, gates. |
| `testing.md` | Unit / integration / functional / non-functional tests per phase. |
| `security.md` | Security controls per phase (OWASP Top 10:2025 + file-processing threats). |
| `design.md` | UI/UX design system, screens, responsive rules, i18n (AR/EN), dark/light. |
| `api_contract.md` | The API contract that connects the two developer tracks. |
| `backend_plan.md` | Developer A track (backend). |
| `frontend_plan.md` | Pointer to the frontend package. |
| `frontend/` | The agreed frontend package (README, plan, testing, security). Owned by Developer B. |
| `session_log.md` | Progress log. Read it first at the start of every session. |
| `plan_review.md` | Full review of plan v1 and the 24 fixes applied in v1.1. |
| `decisions.md` | One line per final decision (decisions reached in Issues are recorded here). |

**Plan version:** v1.1 (2026-11-23), revised after the full review.

---

## 1. Senior engineering review of the original plan

### What is strong and is kept
- **Typed DAG engine with a registry of known operations.** No model-generated code is ever executed. This is the core safety property and stays non-negotiable.
- **The AI planner only proposes a `WorkflowDraft`.** An independent validator checks it, and the user approves it explicitly, with the approval bound to a `plan_hash`.
- **An explicit run state machine.** States: DRAFT, VALIDATED, AWAITING_APPROVAL, QUEUED, RUNNING, NEEDS_REVIEW, SUCCEEDED, PARTIAL, FAILED, CANCEL_REQUESTED, CANCELLED, EXPIRED.
- **Explicit resource limits**, plus ZIP and XML safety, lineage, idempotency and replay with pinned versions.
- **A concrete acceptance test for the first real pipeline** (orders.csv + payments.json → comparison report).

### Problems found and how this plan fixes them

| # | Issue in original plan | Risk | Fix in this plan |
|---|---|---|---|
| 1 | The UI is optional (FE‑01 is a mock) and the commercial UI is not planned. | No usable product for two developers working in parallel. | The frontend is a full track. It is contract-first and runs against mocks until the backend lands. |
| 2 | All 14 formats are required before the first release. | Scope too large for 2 developers. Value is proven late. | Ship a vertical-slice MVP first (ZIP/CSV/JSON + UI + auth). Formats come in later batches behind gates. |
| 3 | **Vercel request body limit (~4.5 MB)** vs a 50 MiB file limit. | Uploads fail in production. | Files upload **directly to storage** through short-lived signed URLs. Files never pass through a Vercel function body. |
| 4 | Run timeout of 900 s vs the Vercel function maximum duration (plan-dependent, ≤ 800 s on Pro). | Long runs are killed mid-way. | Execution is checkpointed **node by node** (each node ≤ 120 s). A run is a chain of short invocations, and state is persisted after every node. |
| 5 | DOC conversion (LibreOffice) and OCR (Tesseract) need native binaries. | They do not fit Vercel function bundle limits. | Decision gate D5/D6: a container worker (Fly.io, Render or Railway) **or** pure-Python alternatives **or** dropping the format. This is decided before Phase 15/16. |
| 6 | SQLite locally vs Supabase Postgres in production. | Dialect drift (types, locking, JSON, case sensitivity). | Use portable SQLAlchemy types only. Alembic migrations run on both databases. **CI runs the full test suite on SQLite and on Postgres** from Phase 4. |
| 7 | Supabase exposes tables through PostgREST using the anon key. | Data leaks if RLS is off. | Enable RLS on every table, add no anon policies, keep the app schema non-exposed, and never ship the service key to the browser. See security.md S‑40. |
| 8 | Rate limiting and queues rely on in-memory state. | Serverless instances share no memory. | Rate limits and the job queue are stored in the database (portable), with an option to move to Vercel Queues or Upstash at Phase 19. |
| 9 | Supabase Free plan has a 50 MB global file size limit. | Equals the file limit, with no headroom. | Use the Pro plan in production, or reduce the file limit to 45 MiB. Decision D8. |
| 10 | `.env` with `OPENROUTER_API_KEY` sits in a OneDrive-synced folder with no git yet. | Secret leaks on first commit or cloud sync. | Add `.gitignore` and gitleaks before the first commit (P0.2). Rotate the key if it was ever shared. |
| 11 | Multi-AI-agent roles (Codex, Work, Claude Chat) add coordination overhead. | Slows down 2 humans. | Two human owners and one contract. AI tools are helpers, not owners of a track. |

### Decisions (all recommendations APPROVED by owner on 2026-11-23)

| ID | Decision | Recommendation |
|---|---|---|
| D1 | Backend framework | **FastAPI + SQLAlchemy 2 + Alembic + Pydantic v2** (Python, managed with `uv`). |
| D2 | Frontend framework | **Next.js (App Router, latest) + TypeScript + Tailwind CSS v4**, deployed on Vercel. |
| D3 | Authentication | **Backend-owned auth** (argon2id, httpOnly cookie sessions, refresh rotation). It works the same on SQLite and Supabase. The alternative is Supabase Auth, which needs the Supabase CLI and Docker locally. |
| D4 | Email provider (verification, reset) | Console sink locally; **Resend** in production. |
| D5 | DOC (legacy Word) support | Defer. Offer "convert to DOCX first" guidance in the MVP. Revisit with a container worker. |
| D6 | OCR engine | Container worker with Tesseract (keeps data private) vs an external OCR API (needs a separate privacy consent). Decide at the Phase 16 gate. |
| D7 | AI planner provider | OpenRouter (key already present), with a configurable model and **no raw file content sent by default**. |
| D8 | Supabase plan and file limit | Pro plan, keeping the 50 MiB limit. |
| D9 | Production worker | Start with Vercel functions plus a DB-backed job table and chained invocations. Move to Vercel Queues or a container worker if Phase 17 load tests fail. |
| D10 | Default UI language | Arabic or English, chosen by browser `Accept-Language`, with English as the fallback. |
| D11 | Data retention | Inputs 30 days, outputs 90 days, audit log 1 year. Users can delete their files at any time. |
| D12 | MFA | Optional TOTP for all users, **strongly prompted** for owners and admins (Phase 5). |
| D13 | Data-processing library | Python stdlib `csv` + `Decimal` for the MVP, with `polars` only if profiling proves it is needed. Avoid pandas, which risks the Vercel bundle size. |
| D14 | Legal jurisdiction | Egypt PDPL (Law 151/2020) plus GDPR-ready practices. This decides the Supabase region and the privacy policy. |

### 1b. Functional requirements traceability

| FR | Requirement | Phases | Tests |
|---|---|---|---|
| FR‑01 | Sign up, verify email, sign in and out, reset password, optional MFA | 5, 9 | T5.*, T9.5 |
| FR‑02 | Workspaces with roles, invite members, change roles | 5, 10 | T5.9, T5.13 |
| FR‑03 | Upload up to 10 files per run (≤ 50 MiB each), validated by content | 6, 10 | T6.*, T10.2 |
| FR‑04 | Describe the task in Arabic or English | 10, 12 | T10.1, T12.6 |
| FR‑05 | Get a proposed plan (template planner in the MVP, AI planner later) | 3, 8, 12 | T3.11, T12.* |
| FR‑06 | Validate the plan (structure, types, limits, versions) and show errors per step | 2, 10 | T2.*, T10.3 |
| FR‑07 | Review and edit step parameters, then approve explicitly (bound to plan_hash) | 3, 8, 10 | T3.1, T8.9, T10.4 |
| FR‑08 | Run with live progress, cancel, and clear PARTIAL, FAILED and NEEDS_REVIEW outcomes | 3, 8, 10 | T3.*, T8.6, T10.5 |
| FR‑09 | Preview results with filters, see the source of each row (lineage), download outputs | 7, 8, 10 | T7.1, T7.2, T10.6 |
| FR‑10 | Save a plan as a versioned workflow and run it again on new files, with drift mapping | 13 | T13.* |
| FR‑11 | Support all 14 formats (at least one tested pipeline each) | 7, 14–16 | T7, T14–T16 |
| FR‑12 | Arabic and English UI (RTL), light and dark mode, phone, tablet and laptop | 9–11 | T9.*, T11.* |
| FR‑13 | Files library, runs history, audit log | 6, 8, 10 | T6.7, T10.7 |
| FR‑14 | Delete account and export my data | 5 | T5.14 |
| FR‑15 | First-run onboarding with sample files | 10 | T10.11 |

### 1c. Out of scope for v1 (stated to prevent scope creep)
Billing and subscriptions, a public API with API keys, SSO/SAML, real-time collaboration, a mobile native app, a custom admin back-office, user-defined code or formulas, a Visual Builder (drag-and-drop workflow editor), fetching files from URLs or cloud drives, and email or webhook notifications on run completion (candidate for v1.1).

---

## 2. Working rules (MANDATORY — apply to every phase)

### Process
- **Work incrementally, ALWAYS.** Small, simple steps. Validate and check each increment before moving on.
- Mark each step `[x]` only after its tests pass and its evidence (command plus result) is written in `session_log.md`.
- **A phase is finished only when** all of its steps are `[x]`, every test for that phase in `testing.md` passes, and every security item for that phase in `security.md` is verified.
- **Phase gate:** at the end of every phase, stop, report the results to the gate approver, and **ask for permission** before starting the next phase.
- Before each step, check the **production compatibility checklist** (§4).
- Record all progress in `session_log.md` (started, finished, blockers, decisions, next step).
- **Owners (2026-11-25):** both developers are co-owners. Owner decisions (for example the `LICENSE`, changes to D1–D14, data retention, and which accounts production uses) need both. In a disagreement, each developer decides within their own track (backend or frontend), and a shared file (root files, `.github/`, `contracts/`, `docs/`) changes only when both agree.
- **Gate approvals (agreed in issue #1):** backend gates are approved by Developer A, frontend gates by Developer B, and shared gates (0, 17, 18, 19) by both. Review time is 24 h for PRs and 48 h for gates (working days; a "working on it" reply counts).
- **Gates with two developers working in parallel:** each track (backend phases B*, frontend phases F*) passes its own phase gates independently, but each track still needs its gate approver's permission before moving to its next phase. Integration milestones (I1–I6) and shared phases (0, 17, 18, 19) need **both** tracks green before the gate.

### MANDATORY code style
- Do not overengineer. Do not program defensively. Use exception handlers only when needed.
- Identify the root cause before fixing issues. Prove it with evidence, then fix.
- Work incrementally. Small steps. Validate each increment.
- Use the **latest library APIs** (verify versions at P0.1 and record them in `session_log.md`).
- Use `uv` as the Python package manager. Always `uv run xxx`, never `python3 xxx`. Always `uv add xxx`, never `pip install xxx`.
- Favor clear, concise docstring comments. Be sparing with comments outside docstrings.
- Favor short modules and short functions. Name things clearly.
- Frontend: use `pnpm`. Use strict TypeScript. Do not use `any`.

### Debugging and fixing
- When troubleshooting, ALWAYS identify the root cause BEFORE fixing.
- PROVE THE PROBLEM FIRST. Don't guess.
- Try one test at a time. Be methodical.
- Don't jump to conclusions. Don't apply workarounds.

---

## 3. Target architecture

```
replora/                         (one GitHub repo, monorepo)
├── backend/                     Python 3.14, uv, FastAPI           (Developer A)
│   ├── app/
│   │   ├── core/                contracts, registry, validator, engine (pure, no I/O)
│   │   ├── operations/          typed operations (parse, normalize, compare, report…)
│   │   ├── adapters/            file adapters per format → typed artifacts
│   │   ├── planner/             MockPlanner, AIPlanner (OpenRouter), privacy guard
│   │   ├── db/                  SQLAlchemy models, repositories, Alembic migrations
│   │   ├── storage/             LocalStorage | SupabaseStorage (one interface)
│   │   ├── auth/                users, sessions, workspaces, roles, permissions
│   │   ├── api/v1/              FastAPI routers (thin)
│   │   └── worker/              job queue + node-by-node runner
│   └── tests/                   unit/ integration/ functional/ security/ fixtures/
├── frontend/                    Next.js (App Router), TS, Tailwind v4 (Developer B)
│   ├── src/app/[locale]/        routes (ar | en)
│   ├── src/components/          ui/ (design system), features/
│   ├── src/lib/api/             generated client from OpenAPI
│   ├── messages/                ar.json, en.json
│   └── tests/                   unit (Vitest), e2e (Playwright), mocks (MSW)
├── contracts/                   SHARED — openapi.json, JSON schemas, fixtures
├── docs/                        these documents (single source, changed by PR only)
└── .github/                     CI workflows, CODEOWNERS, PR template
```

**Request path (local):** browser → Next.js dev server → `/api/*` rewrite → FastAPI (uvicorn) → SQLite + `./.data/storage`.
**Request path (production):** browser → Vercel (Next.js) → `/api/*` rewrite → Vercel Python function (FastAPI) → Supabase Postgres (pooler) and Supabase Storage (private bucket, signed URLs).
The same-origin rewrite means cookies are first-party. There are no cross-site cookies, and API traffic needs no CORS. **The one exception is the file upload PUT:** in production it goes straight to a Supabase Storage signed URL (a different origin), so the CSP `connect-src` adds the storage origin from an environment variable. Locally the upload URL is a same-origin backend endpoint. See api_contract.md §4.

---

## 4. Production compatibility checklist (check at every step)
- [ ] Only portable SQLAlchemy types are used (`Uuid`, `JSON` with a `JSONB` variant, `DateTime(timezone=True)`, `String(n)`, `Numeric`). No SQLite-only SQL.
- [ ] No local-disk assumptions outside `storage/` (Vercel's filesystem is read-only except `/tmp`).
- [ ] No in-process state that must survive between requests (no global caches, schedulers or in-memory queues in the API).
- [ ] Each request or node finishes within the function duration budget. No request body above 4 MB.
- [ ] All config comes from environment variables (`pydantic-settings`), and secrets are never committed.
- [ ] Native binaries are not required on the Vercel path.
- [ ] Every new table has indexes for its foreign keys and query filters, and the migration runs on SQLite **and** Postgres.

---

## 5. Phases

Legend: `[ ]` todo · `[x]` done (with evidence in session_log) · **Gate** = stop and ask the gate approver for permission.
Sizing: S ≈ ≤ 1 week, M ≈ 1–2 weeks, L ≈ 2–4 weeks for one developer. These are estimates, not commitments. Re-baseline after Phase 3.
**Realistic schedule (2 developers × ~20 h/week):** the MVP (Phases 0–13) takes about 14–18 weeks. The full scope (Phases 0–19, all 14 formats) realistically takes **9–12 months**. The original v0.6 estimate was 1,800–2,560 engineering hours. The week numbers in the track plans describe the MVP path and are re-baselined at G3.

### Phase 0 — Foundation and repository setup (S)
Goal: a clean, secure, reproducible monorepo with CI that is green on empty skeletons.
- [x] P0.1 Verify the latest stable versions (Python, uv, FastAPI, Pydantic, SQLAlchemy, Alembic, Next.js, React, Tailwind, next-intl, TanStack Query, Playwright, Vitest). Record them in session_log.
- [x] P0.2 `git init`. Add a root `.gitignore` (`.env*`, `.data/`, `.venv/`, `node_modules/`, `.next/`, coverage) **before the first commit**. Add `.env.example` with key names only. Run a gitleaks scan.
- [x] P0.3 Backend skeleton: `uv init backend`. Add FastAPI, pydantic-settings, ruff and pytest. `GET /api/v1/health` returns `{status:"ok", version}`.
- [x] P0.4 Frontend skeleton: create a Next.js app (TS, App Router, Tailwind v4, ESLint) with pnpm. It renders one page.
- [x] P0.5 `contracts/` folder: an OpenAPI export script (`uv run python -m app.export_openapi`). Generate the TS types with `openapi-typescript` (`pnpm gen:api`). The typed `openapi-fetch` client over them is P9.6 (`docs/frontend/plan.md`).
- [x] P0.6 Pre-commit hooks: ruff (lint and format), the TS linter and prettier, and gitleaks.
- [x] P0.7 GitHub Actions CI: backend lint and test, frontend lint, typecheck and test, a contract drift check (the generated OpenAPI must match the committed file), gitleaks, and dependency audit (`uv run pip-audit` and `pnpm audit`).
- [x] P0.8 Repo governance: protected `main`, required CI, 1 approving review by the other developer, CODEOWNERS, a PR template (summary, commit SHA, test commands and results, security impact).
- [x] P0.9 Local dev commands documented in `README.md` (`uv run uvicorn …`, `pnpm dev`, with a `/api` rewrite to the backend).
- [x] P0.10 Owner answers decisions D1–D14. Record the answers in `session_log.md`.
- [x] P0.11 Observability from day one: structured JSON logs (backend), a correlation ID per request (`X-Request-ID`, returned in problem+json), PII scrubbing, and a frontend error boundary that reports the correlation ID.
- [x] Tests T0.* pass · Security S‑01…S‑05 verified · **Gate G0**

### Phase 1 — Core contracts (M)
Goal: frozen domain models that both developers rely on.
- [x] P1.1 Pydantic v2 models: `ArtifactType` enum (all 11 artifact kinds), `ArtifactRef` (id, type, format, sha256, lineage, owner scope), `Port`, and `OperationContract` (id, version, input/output ports, params schema).
- [x] P1.2 `Node`, `Edge`, and `WorkflowDefinition` (workflow_id, workflow_version, schema_version, nodes, edges, IO contracts, resource policy, review policy).
- [ ] P1.3 `WorkflowDraft` (planner output, explanation, warnings) and `ValidationReport` (errors and warnings with codes).
- [ ] P1.4 `plan_hash` = SHA‑256 of the canonical JSON (sorted keys, no whitespace, normalized numbers). It is stable across runs and machines.
- [ ] P1.5 `RunState` enum and the allowed transition table, as data.
- [ ] P1.6 Export JSON Schemas to `contracts/schemas/`. Add golden fixtures (valid and invalid) to `contracts/fixtures/`.
- [ ] P1.7 Every model uses `extra="forbid"` and `frozen=True` where it is immutable.
- [ ] Tests T1.* pass · Security S‑10, S‑11 verified · **Gate G1 (contracts v1 frozen. Changes after this need a Change Request in `api_contract.md` §9)**

### Phase 2 — Operation registry and DAG validator (M)
- [ ] P2.1 `OperationRegistry`: register and look up by `(id, version)`. Duplicates are rejected. `list()` is used for the API.
- [ ] P2.2 Validator, structural checks: unique node IDs, edges reference existing nodes and ports, **no cycles** (Kahn topological sort), no orphan required inputs.
- [ ] P2.3 Validator, type checks: port artifact types match exactly (**no implicit conversion**), and parameters validate against the operation's params schema.
- [ ] P2.4 Validator, limit checks: ≤ 30 nodes, depth ≤ 10, fan-in and fan-out ≤ 10, plus file count and size limits from the resource policy.
- [ ] P2.5 Validator, version checks: unknown or unpinned operation versions are rejected.
- [ ] P2.6 Every error returns a stable `code` (for example `DAG_CYCLE` or `PORT_TYPE_MISMATCH`) plus the node and port location. The frontend translates codes to AR/EN.
- [ ] Tests T2.* pass · Security S‑12 verified · **Gate G2**

### Phase 3 — Execution engine (in-memory, fake adapters) (M)
- [ ] P3.1 State machine: `transition(run, event)` enforces the P1.5 table. Illegal transitions raise errors.
- [ ] P3.2 Approval: `approve(run, plan_hash)` must match the current plan hash exactly. A changed plan invalidates the approval.
- [ ] P3.3 In-memory executor: topological order, node-by-node execution, outputs stored as artifacts with lineage.
- [ ] P3.4 Failure semantics: a failed required branch makes the run FAILED, a failed optional branch makes it PARTIAL with warnings, and a low-confidence result makes it NEEDS_REVIEW.
- [ ] P3.5 Retry: only `TransientError`, at most 2 extra attempts with backoff. Idempotency key = `(run_id, node_id, input_hashes)`, so a node is never executed twice for the same inputs.
- [ ] P3.6 Cancellation: CANCEL_REQUESTED is checked between nodes and leads to CANCELLED. EXPIRED applies when approval times out (AWAITING_APPROVAL older than 24 h, configurable).
- [ ] P3.7 Replay: re-run a pinned workflow version on new inputs. A contract mismatch leads to NEEDS_REVIEW.
- [ ] P3.8 `MockPlanner` plus fake adapters (fake ZIP with fake CSV and JSON branches). This is the integration test for the original S1.4. **The MockPlanner is test-only.**
- [ ] P3.9 `TemplatePlanner` (user-facing, deterministic). Templates such as "Reconcile two files on a key" and "Merge files with the same columns" are filled from file metadata (column-name matching). This is what MVP users get before the AI planner exists, and it remains the fallback afterwards.
- [ ] Tests T3.* pass · Security S‑13 verified · **Gate G3 (equivalent of original Sprint 1 exit)**

### Phase 4 — Persistence layer (SQLite locally, Postgres-ready) (M)
- [ ] P4.1 SQLAlchemy 2 engine and session from `DATABASE_URL`. SQLite uses WAL and `foreign_keys=ON`. Postgres uses psycopg 3, and `NullPool` is configured for serverless.
- [ ] P4.2 Models: `users`, `workspaces`, `memberships`, `sessions`, `files`, `artifacts`, `workflows`, `workflow_versions`, `drafts`, `runs`, `run_nodes`, `jobs`, `audit_events`, `rate_limits`. All IDs are UUIDv7 and all timestamps are UTC.
- [ ] P4.3 **Indexes on every table** (see §6 below). They are verified by a test that inspects the metadata.
- [ ] P4.4 Alembic setup (`render_as_batch=True` for SQLite). The initial migration. `upgrade` and `downgrade` are tested.
- [ ] P4.5 Repositories: every query function takes a `workspace_id` and filters by it. No unscoped query is possible.
- [ ] P4.6 Persist engine state: runs, run_nodes and artifacts are saved after each node (checkpointing for serverless).
- [ ] P4.7 CI job: run the full backend suite against **Postgres 17** (service container) in addition to SQLite.
- [ ] Tests T4.* pass · Security S‑14, S‑15 verified · **Gate G4**

### Phase 5 — Authentication and authorization (M)
- [ ] P5.1 Register and login with argon2id hashing (`pwdlib`). Password policy follows NIST 800‑63B (length ≥ 12, breached-password check offline list, no composition rules).
- [ ] P5.2 Sessions: short access token (15 min) and a rotating refresh token (stored hashed, revocable), both in `HttpOnly; Secure; SameSite=Lax` cookies. Logout revokes the session.
- [ ] P5.3 CSRF protection: a double-submit token (`X-CSRF-Token`) on all unsafe methods.
- [ ] P5.4 Email verification and password reset (single-use, hashed, 30‑min tokens). The email goes to the console sink locally.
- [ ] P5.5 Workspaces and roles: `owner`, `admin`, `member`, `viewer`. The permission matrix is defined in code (security.md S‑21). Each user gets a personal workspace on signup.
- [ ] P5.6 A `require(permission)` FastAPI dependency. Resources from another workspace return **404** (no existence leak).
- [ ] P5.7 Login throttling and account lockout with backoff (DB-backed rate limit). Every auth event is written to the audit log.
- [ ] P5.8 `GET /auth/me`, `PATCH /auth/me` (including `timezone`), session list and revoke (`/auth/sessions`), workspace deletion (owner only, not the personal workspace), and membership management endpoints.
- [ ] P5.9 Invitations: a hashed, single-use, 7-day invite token. Accepting it works for existing users and for new sign-ups. The admin can revoke it.
- [ ] P5.10 Account deletion (with a grace period, cascading to the personal workspace and its files) and data export (a ZIP of the user's files, workflows and run history).
- [ ] P5.11 Optional TOTP MFA (per D12) with recovery codes (hashed). It is prompted for owners and admins. Login with MFA uses a short-lived, single-use `replora_mfa_challenge` cookie (api_contract.md §2), so no session is issued until `/auth/mfa/challenge` succeeds.
- [ ] Tests T5.* pass · Security S‑20…S‑29 verified · **Gate G5**

### Phase 6 — File intake and storage (M)
- [ ] P6.1 `Storage` interface: `create_upload_url`, `put` (local only), `open`, `delete`, `signed_download_url`. Implement `LocalStorage` (`./.data/storage`, keys never derived from user filenames).
- [ ] P6.2 Upload flow: `upload-intent` returns a file_id and an upload URL, the client PUTs the file, then calls `complete`, which triggers validation. This flow is identical in production with Supabase signed upload URLs.
- [ ] P6.3 Validation on `complete`: size ≤ 50 MiB, sha256, **magic-byte detection** (not the extension), an allowed type list, and the filename is sanitized for display only.
- [ ] P6.4 ZIP safety: ≤ 25 members, ≤ 200 MiB uncompressed, ratio ≤ 100:1, no nested ZIP, no absolute or `..` paths, no symlinks, and streaming extraction with counters.
- [ ] P6.5 Files list, get, delete and download (signed, short-lived) endpoints, workspace-scoped.
- [ ] P6.6 Retention: an `expires_at` on files and a cleanup job (periods per D11).
- [ ] P6.7 Quotas: ≤ 10 files per run, plus a per-workspace storage quota (default 2 GiB, configurable). Exceeding it returns 413 with `QUOTA_EXCEEDED`.
- [ ] Tests T6.* pass · Security S‑30…S‑36 verified · **Gate G6**

### Phase 7 — First real pipeline: ZIP + CSV + JSON reconciliation (M)
- [ ] P7.1 Adapters: `ZipAdapter` (produces ArchiveManifest), `CsvAdapter` (encoding detection, delimiter sniffing, produces TabularArtifact), `JsonAdapter` (array of objects, produces TabularArtifact).
- [ ] P7.2 Operations: `extract_member`, `map_columns`, `normalize` (trim, number and decimal parsing, key casing), `compare` (fan-in on key, giving matched / value_diff / missing_left / missing_right), `report_csv`, `summary_json`, `bundle_zip`.
- [ ] P7.3 CSV output is protected against formula injection (security.md S‑37).
- [ ] P7.4 Lineage: every output row records its source file, member, row and operation versions.
- [ ] P7.5 Data correctness rules:
  - money and numbers use `Decimal` only (never float), and the comparison tolerance is a parameter (default exact);
  - ambiguous dates (`03/04/2026`) make the run NEEDS_REVIEW with a format choice, never a silent guess;
  - CSV outputs default to **UTF‑8 with BOM** so Arabic opens correctly in Excel, with plain UTF‑8 as an option.
- [ ] P7.6 **Acceptance test (from the original §9):** O‑101 matched, O‑102 value_diff, O‑103 missing_right, O‑104 missing_left. A failure in a required branch means no success. Schema drift leads to NEEDS_REVIEW.
- [ ] Tests T7.* pass · Security S‑37 verified · **Gate G7**

### Phase 8 — Workflow and run API plus background worker (M)
- [ ] P8.1 Endpoints for templates, drafts (TemplatePlanner), validate, runs (create, approve, cancel, get, list), events and outputs (with preview pagination) per `api_contract.md`.
- [ ] P8.2 DB-backed job queue (`jobs` table, `SELECT … FOR UPDATE SKIP LOCKED` on Postgres, simple locking on SQLite). The local worker runs as `uv run python -m app.worker`.
- [ ] P8.3 Node-by-node runner: each job executes **one node**, persists the result, and enqueues the next. This proves the serverless chaining model locally.
- [ ] P8.4 An `Idempotency-Key` header on `POST /runs` and `POST /runs/{id}/approve`.
- [ ] P8.5 HTTP caching: `ETag` with `If-None-Match` (304) on GET resources. `Cache-Control: private, no-cache` for user data. `public, max-age=3600` for `/operations`.
- [ ] P8.6 Errors use RFC 9457 `application/problem+json` with a stable `code`.
- [ ] P8.7 **Freeze OpenAPI v1.** Commit it to `contracts/openapi.json`. CI fails on any undeclared drift.
- [ ] P8.8 **Production feasibility spike (staging only, not go-live).** Deploy the backend to a Vercel preview with a throwaway Supabase staging project and measure:
  - the Python function bundle size (must be < 250 MB unzipped);
  - cold start time;
  - the **node-chaining mechanism** (background continuation vs Vercel Queues vs cron), proven with a 6-node run;
  - the transaction-pooler connection;
  - a 50 MiB signed upload.
  Record the results. **Decide D9.** Tear down or keep it as staging.
- [ ] P8.9 `If-Match` (ETag) required on PATCH of drafts and workflows. A stale version gets 412 `PRECONDITION_FAILED`.
- [ ] Tests T8.* pass · Security S‑16, S‑17, S‑50…S‑53 verified · **Gate G8 (backend MVP complete + production path proven)**

### Phase 9 — Frontend foundation (M) *(runs in parallel with Phases 4–8, see frontend_plan.md)*
- [x] P9.1 Design tokens from `design.md` as CSS variables. Tailwind v4 `@theme`. Light and dark palettes.
- [x] P9.2 Theme: system default, a manual toggle that persists, and no flash on load (`next-themes`). *(#29; ticked in the frontend plan)*
- [x] P9.3 i18n: `next-intl` with `/ar` and `/en` routes. `dir="rtl"` for Arabic. **Logical CSS properties only** (`ms-`, `pe-`, `start`, `end`). The Arabic and Latin fonts load via `next/font`. *(#30 routing and `lang`/`dir`, #37 Readex Pro and messages, #38 logical-CSS lint rule; marked done by the frontend in #39)*
- [ ] P9.4 App shell, responsive at three sizes: sidebar (≥ 1024 px), collapsible rail (640–1023 px), bottom navigation (< 640 px).
- [ ] P9.5 Core UI kit: Button, Input, Select, Dialog, Sheet, Toast, Tabs, Table, Badge, EmptyState, ErrorState, **Skeleton** (one variant per layout).
- [ ] P9.6 API client generated from `contracts/openapi.json`. TanStack Query (staleTime and ETag aware). MSW mocks from `contracts/fixtures`.
- [ ] P9.7 Auth screens: sign in, sign up, verify email, forgot and reset password. Protected routes in the Next.js request proxy (`proxy.ts` in Next 16; verify the current name at P0.1).
- [ ] P9.8 Route `loading.tsx` with layout-matched skeletons for every data page. Suspense boundaries.
- [ ] Tests T9.* pass · Security S‑60…S‑64 verified · **Gate G9**

### Phase 10 — Frontend core flow (L)
- [ ] P10.1 New run wizard, step 1 Upload: drag and drop plus picker, per-file progress, direct-to-storage PUT, validation errors per file.
- [ ] P10.2 Step 2 Describe: pick a template (MVP) or write a natural-language prompt (after Phase 12), with example prompts in AR and EN.
- [ ] P10.3 Step 3 Review plan: the **pipeline rail** (design.md signature), node details, parameters, warnings, and validation errors mapped to nodes.
- [ ] P10.4 Step 4 Approve: shows the plan hash summary, then explicit approval.
- [ ] P10.5 Run detail: live status (polling `events?after=` with backoff), per-node state, cancel action.
- [ ] P10.6 Results: summary, a virtualized table preview with diff colors, and downloads. PARTIAL and NEEDS_REVIEW states are explained.
- [ ] P10.7 Files library, runs history, workspace home (recent runs, saved workflows), and settings: profile, language, theme, timezone, MFA, members and invitations, export my data, delete account. Also the invitation-accept page.
- [ ] P10.8 Integrate with the real backend (MSW off). Fix contract mismatches through Change Requests only.
- [ ] P10.9 First-run onboarding: "Try it with sample files" loads the bilingual sample orders and payments files and walks through the wizard once. It can be dismissed and reopened from Help.
- [ ] P10.10 Timezone: stored per user (default from the browser). All dates are displayed in the user's timezone and locale, and stored in UTC.
- [ ] Tests T10.* pass · Security S‑65, S‑66 verified · **Gate G10 (end-to-end MVP on localhost)**

### Phase 11 — UI/UX iteration and accessibility (S–M)
- [ ] P11.1 Screenshot matrix: 3 viewports (390, 820, 1440) × 2 themes × 2 languages for every screen (agent-browser or Playwright).
- [ ] P11.2 Critique each screen against the design.md checklist. Record findings in session_log.
- [ ] P11.3 Iterate: fix, re-shoot, re-critique. At least 2 rounds, and continue until no high or medium findings remain.
- [ ] P11.4 Accessibility: axe has zero serious or critical violations, the whole flow works by keyboard, focus is visible, contrast is AA, `prefers-reduced-motion` is respected, and screen-reader labels exist in both languages.
- [ ] P11.5 Usability test of the MVP flow with 3 or more people (AR and EN users). Record the issues and fix them.
- [ ] Tests T11.* pass · **Gate G11 (MVP ready for internal demo)**

### Phase 12 — AI planner (OpenRouter) and privacy guard (M)
- [ ] P12.1 `AIPlanner` implements the same interface as `MockPlanner`. The model is set by an env var. It uses structured JSON output validated against the `WorkflowDraft` schema.
- [ ] P12.2 Privacy guard: by default the planner receives **only metadata** (file names, types, column names, row counts), never cell values. Sending sample rows requires explicit per-run consent.
- [ ] P12.3 The prompt treats all file-derived text as data (prompt-injection defense). Output is always re-validated by the independent validator and never auto-approved.
- [ ] P12.4 Timeouts, a token budget and cost cap per workspace, and a fallback to the MockPlanner or a manual template on failure.
- [ ] P12.5 Frontend: a planner explanation panel, "what will be sent to AI" disclosure, and the consent toggle.
- [ ] Tests T12.* pass · Security S‑70…S‑74 verified · **Gate G12**

### Phase 13 — Saved workflows, replay and schema drift (M)
- [ ] P13.1 Save a draft as a versioned workflow. Versions are immutable.
- [ ] P13.2 Replay on new files with the input contract check. On drift (missing or renamed columns) the run becomes NEEDS_REVIEW with a mapping UI.
- [ ] P13.3 A mapping update creates a new workflow version and needs a new approval.
- [ ] P13.4 Frontend: workflows list, version history, replay dialog, mapping editor.
- [ ] Tests T13.* pass · **Gate G13**

### Phase 14 — Formats batch A: TXT, XLSX, XLS, XML (L)
- [ ] P14.1 TXT adapter (encoding detection, line and delimited modes).
- [ ] P14.2 XLSX adapter (`openpyxl` read-only mode, sheet selection, merged cells reported, formulas read as values with a warning).
- [ ] P14.3 XLS adapter (`xlrd`, pure Python, Vercel-friendly).
- [ ] P14.4 XML adapter (`defusedxml`, record path selection, produces TabularArtifact or StructuredObjectArtifact).
- [ ] P14.5 XLSX output writer. At least one useful end-to-end pipeline per format with fixtures, including malformed and edge files. **Silent fidelity loss is forbidden**: every loss is surfaced as a warning.
- [ ] Tests T14.* pass · Security S‑38, S‑39 verified · **Gate G14**

### Phase 15 — Formats batch B: PDF text, DOCX, PPTX (+ DOC decision) (L)
- [ ] P15.1 PDF text extraction (`pypdf`, or `pdfplumber` for tables), ≤ 100 pages, encrypted PDFs rejected with a clear message.
- [ ] P15.2 DOCX (`python-docx`): paragraphs and tables produce TextDocumentArtifact and TabularArtifact.
- [ ] P15.3 PPTX (`python-pptx`): slides, text and tables produce PresentationArtifact.
- [ ] P15.4 DOC: implement per decision D5 (container worker with LibreOffice, or "unsupported, convert to DOCX" guidance).
- [ ] P15.5 Low-confidence extraction makes the run NEEDS_REVIEW, and lineage includes page and slide numbers.
- [ ] Tests T15.* pass · Security S‑41, S‑42 verified · **Gate G15**

### Phase 16 — Formats batch C: JPG, PNG, WEBP plus OCR (L, decision gate D6 first)
- [ ] P16.1 Image adapter (Pillow, 20 MP limit, EXIF stripped on outputs).
- [ ] P16.2 OCR per D6, ≤ 20 pages per run, Arabic and English.
- [ ] P16.3 Holdout quality set (AR and EN) with measured accuracy thresholds agreed by both owners.
- [ ] P16.4 Review UI for low-confidence OCR fields.
- [ ] Tests T16.* pass · Security S‑43 verified · **Gate G16**

### Phase 17 — Hardening: performance, caching, regression, security audit (M)
- [ ] P17.1 Full all-format regression suite in CI (SQLite and Postgres).
- [ ] P17.2 Load test (Locust via `uv run locust`) against the agreed targets (testing.md NFR table).
- [ ] P17.3 Query review: `EXPLAIN` on the top 20 queries in Postgres to confirm index usage. Add missing indexes.
- [ ] P17.4 Frontend performance: Lighthouse CI budgets, bundle analysis, image and font optimization, immutable caching for static assets.
- [ ] P17.5 Security audit: run the full security.md checklist, OWASP ZAP baseline scan, semgrep, dependency audit, and a manual IDOR sweep.
- [ ] P17.6 Fix all critical and high findings. Document any accepted residual risks.
- [ ] P17.7 Cross-browser: the Playwright suite passes on Chromium, WebKit (Safari/iOS) and Firefox (NFR‑11).
- [ ] P17.8 Legal and public pages, bilingual: privacy policy, terms of use, and a minimal landing page (what Replora does, sign up). Content is reviewed against D14.
- [ ] Tests T17.* pass · all security items re-verified · **Gate G17 (application complete on localhost)**

### Phase 18 — Production I: Supabase (M)
- [ ] P18.1 Create the Supabase project (region near users). Separate staging and production projects.
- [ ] P18.2 Connect via the **transaction pooler** (port 6543) for serverless with `NullPool` and prepared statements disabled. Use a direct connection for migrations.
- [ ] P18.3 Run Alembic migrations on staging. Verify the schema and indexes.
- [ ] P18.4 RLS enabled on every table, no anon or authenticated policies, a dedicated DB role for the backend, and the app schema not exposed through the Data API.
- [ ] P18.5 `SupabaseStorage` implementation: private bucket, signed upload and download URLs (short TTL), a size limit on the bucket, and an allowed MIME list.
- [ ] P18.6 Backups and point-in-time recovery reviewed. A data retention job is scheduled.
- [ ] P18.7 Full test suite against staging Supabase (integration and E2E).
- [ ] P18.8 Load test against **staging** (Vercel + Supabase, real cold starts and pooler) for NFR‑1, NFR‑2 and NFR‑7. Compare with the localhost results, then tune or escalate D9.
- [ ] Tests T18.* pass · Security S‑40, S‑44…S‑46 verified · **Gate G18**

### Phase 19 — Production II: Vercel deployment and go-live (M)
- [ ] P19.1 Vercel projects: `frontend` (Next.js) and `backend` (FastAPI Python function), or a single project with `/api` routing. Preview deployments are used for PRs.
- [ ] P19.2 Environment variables per environment (development, preview, production). Secrets live only in Vercel and Supabase.
- [ ] P19.3 Worker in production per D9: job chaining via a background invocation or Vercel Queues, plus a cron for retention and expired runs. Verify that the 120 s node and 900 s run limits are enforced.
- [ ] P19.4 Security headers and CSP verified on the production domain. HSTS. A custom domain with TLS.
- [ ] P19.5 Production observability (structured logs exist from P0.11): error tracking, uptime check, alerts on failed-run rate and 5xx rate, and **cost alerts** for Vercel, Supabase and OpenRouter (NFR‑12).
- [ ] P19.6 Smoke tests and the E2E suite against the production URL (phone, tablet and laptop projects).
- [ ] P19.7 Rollback plan tested (instant rollback in Vercel, migration downgrade path).
- [ ] P19.8 Go-live checklist signed off by both owners.
- [ ] Tests T19.* pass · Security S‑80…S‑85 verified · **Gate G19 (production release)**

---

## 6. Database tables and indexes (Phase 4 baseline)

Every foreign key is indexed. Every list query uses `(workspace_id, created_at DESC)`-style composite indexes for cursor pagination.

| Table | Key columns | Indexes |
|---|---|---|
| users | id, email (unique, lower-cased), password_hash, email_verified_at, locale, theme, timezone, mfa_secret_enc, deleted_at, created_at | `uq_users_email`, `ix_users_created_at`, `ix_users_deleted_at` |
| invitations | id, workspace_id, email, role, token_hash, invited_by, expires_at, accepted_at, revoked_at | `uq_invitations_token_hash`, `ix_invitations_ws_email`, `ix_invitations_expires_at` |
| mfa_recovery_codes | id, user_id, code_hash, used_at | `ix_mfa_recovery_user_id` |
| workspaces | id, name, owner_id, created_at | `ix_workspaces_owner_id` |
| memberships | id, workspace_id, user_id, role | `uq_memberships_ws_user (workspace_id,user_id)`, `ix_memberships_user_id` |
| sessions | id, user_id, refresh_hash, expires_at, revoked_at, user_agent, ip_hash | `uq_sessions_refresh_hash`, `ix_sessions_user_id`, `ix_sessions_expires_at` |
| auth_tokens | id, user_id, kind (verify/reset), token_hash, expires_at, used_at | `uq_auth_tokens_hash`, `ix_auth_tokens_user_kind` |
| files | id, workspace_id, uploaded_by, storage_key, display_name, detected_type, size, sha256, status, expires_at, created_at | `ix_files_ws_created (workspace_id,created_at)`, `ix_files_ws_sha256`, `ix_files_expires_at`, `ix_files_uploaded_by` |
| artifacts | id, workspace_id, run_id, node_id, type, format, sha256, storage_key, lineage (JSON), created_at | `ix_artifacts_run_id`, `ix_artifacts_ws_created`, `ix_artifacts_sha256` |
| workflows | id, workspace_id, name, created_by, latest_version, created_at, deleted_at | `ix_workflows_ws_created`, `ix_workflows_ws_name` |
| workflow_versions | id, workflow_id, version, definition (JSON), plan_hash, created_at | `uq_wfv_workflow_version`, `ix_wfv_plan_hash` |
| drafts | id, workspace_id, created_by, prompt, draft (JSON), plan_hash, planner, created_at | `ix_drafts_ws_created`, `ix_drafts_created_by` |
| runs | id, workspace_id, workflow_version_id, draft_id, state, plan_hash, approved_by, approved_at, idempotency_key, created_at, finished_at | `ix_runs_ws_created`, `ix_runs_ws_state`, `uq_runs_ws_idem (workspace_id,idempotency_key)`, `ix_runs_wfv_id`, `ix_runs_draft_id` |
| run_nodes | id, run_id, node_id, state, attempt, idempotency_key, started_at, finished_at, error_code | `uq_run_nodes_run_node (run_id,node_id)`, `uq_run_nodes_idem`, `ix_run_nodes_state` |
| run_events | id, run_id, seq, type, payload (JSON), created_at | `uq_run_events_run_seq (run_id,seq)` |
| jobs | id, kind, payload (JSON), run_at, locked_until, attempts, status | `ix_jobs_status_run_at (status,run_at)`, `ix_jobs_locked_until` |
| audit_events | id, workspace_id, actor_id, action, target_type, target_id, ip_hash, created_at | `ix_audit_ws_created`, `ix_audit_actor_created`, `ix_audit_target` |
| rate_limits | key, window_start, count | PK `(key, window_start)`, `ix_rate_limits_window_start` |

---

## 7. Caching and loading strategy
- **Browser caching:** Next.js static assets are fingerprinted, so they get `Cache-Control: public, max-age=31536000, immutable`. Fonts are self-hosted through `next/font`. API GETs use `ETag` with 304 revalidation. User data is `private, no-cache`. The operation registry is `public, max-age=3600, stale-while-revalidate=86400`. Downloads are signed URLs and are never cached publicly.
- **Client cache:** TanStack Query with per-resource `staleTime` (runs in progress: 0 with polling; finished runs: 5 min; operations: 1 h). Mutations invalidate precisely.
- **Skeleton loading:** every data route has a `loading.tsx` skeleton that matches the final layout, so layout shift (CLS) stays ≈ 0. Components fetching data inside a page use Suspense with a matching skeleton. Skeletons respect reduced motion (no shimmer, static tint).
- **Indexes:** §6. They are verified by a test (T4.6) and by `EXPLAIN` in Phase 17.

---

## 8. Two-developer split (summary — details in backend_plan.md, frontend_plan.md, api_contract.md)

| | Developer A — Backend | Developer B — Frontend |
|---|---|---|
| Owns | `backend/**`, DB, worker, storage, security of the API | `frontend/**`, design system, i18n, responsive, UX, E2E |
| Phases | 0 (backend half), 1–8, 12 (backend), 13 (backend), 14–16, 18 | 0 (frontend half), 9–11, 12/13 (UI), 16.4, 19 (frontend deploy) |
| Shared | `contracts/**` (OpenAPI, schemas, fixtures), Phase 17 hardening, Phase 19 go-live | same |
| Parallelism | Phase 1 freezes the domain contracts. P8.7 freezes the HTTP contract, and a **draft** of `api_contract.md` is agreed at G0. | Builds against MSW mocks generated from the draft contract from Week 1. It switches to the real API at Integration Milestones. |

**Integration milestones:** I1 auth (after G5 and G9), I2 files upload (after G6), I3 run flow end to end (after G8 and G10), I4 AI planner (G12), I5 replay (G13), I6 staging (G18).

### Suggestions for working together
1. **Contract first.** Agree on `api_contract.md` at G0, before any feature code. Treat `contracts/` as a mini-repo that both developers must approve.
2. **Fixtures are the handshake.** Every endpoint has request and response fixtures in `contracts/fixtures/`. The backend tests assert that real responses match them, and the frontend MSW serves them. If both pass, integration works.
3. **Short-lived branches** (≤ 2 days), small PRs (≤ 400 lines), and the other developer reviews every PR. No self-merge.
4. **A daily 10-minute sync** (async message is fine) plus a weekly demo on `main`.
5. **Vertical slices at the milestones.** Both developers pair for half a day at each I‑milestone.
6. If Developer B is faster, they take the **Playwright E2E suite and Lighthouse/axe CI**. If Developer A is faster, they take the **staging Supabase setup** early.
7. Swap reviewers' perspective: the backend developer reviews frontend PRs for API usage and security, and the frontend developer reviews backend PRs for error codes, pagination and contract clarity.
