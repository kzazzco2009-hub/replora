# Replora — Session Log

**Read this file first at the start of every session.** Then continue from "Next step".
Append a new entry per session (newest at the top). For each step record: what was done, the commands run, the results (pass or fail counts), and the decisions made.

> **Start here (next session):** read "Current status" and "Next step". Session 16 is finishing Phase 1 one PR per step; open PRs are listed below.

---

## Current status
| Item | Value |
|---|---|
| Current phase | **Phase 3 — Execution engine (B3): complete, G3 awaiting Developer A.** Session 16. **G1 and G2 passed** 2026-11-26 (Developer A), on the condition that their stacks merge after the frontend's review. `main` is at **`ef29ba7`** (#69).

**Phase 1:** 7/7 steps, T1.1–T1.6, S‑10, S‑11.
**Phase 2:** 6/6 steps, T2.1–T2.8, S‑12.
**Phase 3:** 9/9 steps, T3.1–T3.11, S‑11 (Phase 3 part), S‑13 (Phase 3 part; timeouts, memory and quota at T17.6). End-of-phase run on the top of the stack: 1433 backend + 186 frontend tests, no drift, no leaks.

**Merged:** #68 P1.5, #69 P1.5b. **Open backend stack (merge in order; after each merge, rebase the next onto `main`, show the range-diff and ping the frontend to re-approve):** #70 P1.6 (rebased at `9447c56`, waiting for re-approval) → #71 P1.7/S‑10 → #72 P2.1 → #73 P2.2+P2.5 → #74 P2.3 → #75 P2.4+P2.6 → #77 P3.1+P3.2+G2 record → #78 P3.3 → #79 P3.4 (`run_codes`) → #80 P3.5 → #81 P3.6 → #82 P3.7 → #83 P3.8 → #84 P3.9 reconcile (`planner_codes`) → `feat/p3.9-merge-template` (merge template, G3 record).

**Frontend PRs:** #76 approved (TanStack Query provider), and their 401 note answered. |
| Last gate passed | **G2** (2026-11-26, Developer A, `decisions.md`). **G3 is ready and awaiting Developer A.** |
| Waiting on | **Developer A:** **approve G3** (or not), then Phase 4 can start.

**Frontend:** re-approve #70 so the stack can keep merging; review the Phase 2 and 3 PRs (the shared files are `error-codes.json` → `run_codes` and `planner_codes`, `.env.example`); add the i18n keys `templates.{reconcile,merge}.{title,description}` and `plans.{reconcile,merge}`. |
| Next step | 0) **Resume:** Phase 5 is done and G5 (backend) is recorded. The standing go covers **Phases 6, 7, 8 and 9** without asking: update this log, push, and message the frontend after each phase. Next: **P6.1**.
1) **Phase 4** (persistence: SQLAlchemy, Alembic, workspace-scoped repositories; P4.6 persists runs, run_nodes, artifacts and the idempotency ledger).
2) Merge the stack in order as the frontend approves it (recipe in the notes below and in memory).
3) Phase 7 registers the real operations under the ids the templates use: `parse_csv`, `parse_json`, `compare`, `report_csv`, `append_rows`, `export_csv`.
4) `RunEvent.payload` becomes a discriminated union on `type` before G8 (#1, 7186123958). The API request body size cap belongs to Phase 8 (S‑12 note). |
| Resume (next session) | **On any machine**, in PowerShell from the clone (`D:\Projects\replora`).
1. `git fetch --all --prune; git switch main; git pull --ff-only` (if a log PR is still open, switch to its branch and pull). Then read "Current status".
2. Install from the lockfiles: `pnpm install --frozen-lockfile; cd backend; uv sync --locked; cd ..`. Once per clone: `pre-commit install`.
3. Check: `git status` is clean. Then `cd backend; uv run pytest -q; uv run python -m app.export_openapi --check; cd ..`. See "Current status" for the expected count.
4. **Old local branches:** every Phase 0 branch is merged. Check each one's PR is `MERGED`, then `git branch -D <name>`. Merged remote branches are for their author to delete.
5. GitHub: `gh pr list -R kzazzco2009-hub/replora --state all --limit 20` and the new #1 comments (id > 7200405319).
6. The Claude Code memory on each machine is local and may be stale. **This log is the source of truth.**

**Notes:**
- `gh` works from PowerShell only. `gh --jq` breaks in PowerShell 5.1, so pipe to `ConvertFrom-Json`, and loop with `foreach` (piping a parsed array to `Where-Object` doesn't unroll it).
- Write commit message files with `[IO.File]::WriteAllText` (no BOM). `Out-File -Encoding utf8` adds a BOM to the subject. Read UTF-8 files with `-Encoding UTF8`, or ANSI mojibake follows.
- If gitleaks isn't found, reload PATH (root `CLAUDE.md`).
- **Both machines** have a root `.env` with `OPENROUTER_API_KEY`. So `APP_ENV=production` starts locally; to see the S‑02 refusal, also set `DEBUG=true`.
- Approving PRs and deleting remote branches are blocked for Claude by the permission check; Developer A runs those commands.
- **Owners and merges:** a PR merges after the other developer's approval and an explicit go; then either may merge it. Every push dismisses approvals (`dismiss_stale_reviews_on_push`). |
| Blockers | none. Work from **`D:\Projects\replora`** (Claude Code memory: `~/.claude/projects/D--Projects-replora/memory/`). |

## Phase tracker
| Phase | Steps | Tests | Security | Gate approved |
|---|---|---|---|---|
| 0 Foundation | 11/11 | 7/7 | 5/5 | ☑ G0 2026-11-26 |
| 1 Contracts | 7/7 | 6/6 | 2/2 (S‑11 re-checked at G3) | ☑ G1 2026-11-26 (Developer A; stack merging) |
| 2 Validator | 6/6 | 8/8 | 1/1 | ☑ G2 2026-11-26 (Developer A; stack merging) |
| 3 Engine | 9/9 | 11/11 | 1/1 (S‑13 timeouts at T17.6) | ☑ G3 2026-11-26 (Developer A; stack merging) |
| 4 Persistence | 7/7 | 8/8 | 2/2 | ☑ G4 2026-11-27 (pre-approved by Developer A; stack merging) |
| 5 Auth | 11/11 | 15/15 | 10/10 | ☑ G5 2026-11-27 (backend; pre-approved by Developer A; I1 with the frontend) |
| 6 Files | 7/7 | 10/10 | 7/7 + S‑29 rest (S‑35 partly at T15.2/T17.6) | ☑ G6 2026-11-27 (backend; pre-approved; I2 with the frontend) |
| 7 First pipeline | 0/6 | 0/12 | 0/1 | ☐ |
| 8 API + worker | 0/9 | 0/10 | 0/6 | ☐ |
| 9 FE foundation | 3/8 | 0/9 | 0/5 | ☐ |
| 10 FE core flow | 0/10 | 0/11 | 0/2 | ☐ |
| 11 UX + a11y | 0/5 | 1/7 | — | ☐ |
| 12 AI planner | 0/5 | 0/6 | 0/5 | ☐ |
| 13 Replay | 0/4 | 0/4 | — | ☐ |
| 14 Formats A | 0/5 | 0/6 | 0/2 | ☐ |
| 15 Formats B | 0/5 | 0/4 | 0/2 | ☐ |
| 16 Formats C | 0/4 | 0/4 | 0/1 | ☐ |
| 17 Hardening | 0/8 | 0/8 | all | ☐ |
| 18 Supabase | 0/8 | 0/7 | 0/4 | ☐ |
| 19 Vercel | 0/8 | 0/8 | 0/8 | ☐ |

## Decisions log
| Date | ID | Decision | By |
|---|---|---|---|
| 2026-11-23 | — | Planning docs in English. The app is bilingual (Arabic RTL and English) with light and dark modes. | Owner |
| 2026-11-23 | D1–D14 | **All recommendations approved** as written in plan.md §1 (FastAPI; Next.js; backend-owned auth; Resend; DOC deferred; OCR decided at Phase 16 gate; OpenRouter metadata-only; Supabase Pro + 50 MiB; DB job chain proven by P8.8; locale by Accept-Language; retention 30/90/365 days; optional TOTP; stdlib csv+Decimal; Egypt PDPL + GDPR-ready). | Owner |
| 2026-11-23 | — | Owner = **Developer A (backend)**. Frontend developer receives `Frontend_Planning/`. | Owner |
| 2026-11-24 | — | Python target **3.14** (newest that Vercel supports), Node **26 LTS**, Postgres **17**. pnpm pinned through `packageManager`. Pending frontend confirmation for the frontend versions. | Owner (proposed) |
| 2026-11-24 | — | Backend positions on the issue #1 open points (see Session 6). | Owner (proposed) → **Both (confirmed in Session 7)** |
| 2026-11-24 | — | All issue #1 proposals accepted by the frontend: server-side sha256 (removed from `upload-intent`), auth fixtures in B0/B1, `GET /auth/csrf`, draft types (`Column`, `RunSummary`, `OutputArtifact`, `Lineage`, `AuditEvent`), preview `status`/`q`, full-definition PATCH with `If-Match` and the `params_schema` subset, Visual Builder out of v1, `Planning/` → `docs/`, `GET /limits`, staged contract freeze, `openapi.json` from 501 stubs, i18n key-parity CI (frontend adds it), `explanation_key`, shared CODEOWNERS for root files, small PRs with no self-merge. | Both |
| 2026-11-24 | — | Gate ownership: frontend gates are approved by the frontend developer, backend gates by the owner, and shared gates (0, 17, 18, 19) by both. Review times: 24 h for PRs, 48 h for gates. | Both |
| 2026-11-24 | — | Branch protection needs GitHub Pro, a public repo or an organization. Until then the rule is manual: no direct push to `main`, no self-merge. Moving to a free organization will be decided after the skeleton merge. Discussions are dropped; use Issues, and record final decisions in `docs/decisions.md`. | Both |
| 2026-11-24 | — | The backend owns the repo skeleton and CI. Later changes to root files go through a small PR reviewed by the other developer. | Both |

## Recorded versions (filled at P0.1, checked 2026-11-24 from PyPI, npm and the release pages)
The lockfiles (`uv.lock`, `pnpm-lock.yaml`) are the source of truth once they exist.

| Area | Tool / library | Latest | Chosen / note |
|---|---|---|---|
| Runtime | Python | 3.15.2 | **3.14.x** (3.14.10), the newest that Vercel supports (3.12 default, 3.13, 3.14). Pin with `.python-version` and check the Vercel build log. |
| Runtime | Node.js | LTS 26.13.1 | **26 LTS** (Vitest 5 needs ^22.12, ^24 or ≥26; Next ≥20.9) |
| Runtime | PostgreSQL | 17.x on Supabase | **17** (CI service container, matches Supabase) |
| Tool | uv | 0.13.9 | installed |
| Tool | pnpm | 12.23.0 | — |
| Tool | gitleaks | v8.30.1 | — |
| Tool | pre-commit | 4.7.0 | `uv tool install pre-commit` |
| Backend | fastapi | 0.165.0 | |
| Backend | uvicorn | 0.54.0 | |
| Backend | pydantic | 2.14.4 | |
| Backend | pydantic-settings | 2.16.3 | |
| Backend | sqlalchemy | 2.1.9 | 2.1 line. Use 2.1 APIs. |
| Backend | alembic | 1.20.1 | |
| Backend | psycopg | 3.3.9 | |
| Backend | pwdlib | 0.4.2 | with the `argon2` extra (argon2-cffi 25.1.0) |
| Backend | httpx | 0.28.1 | test client |
| Backend test | pytest 9.2.0 · hypothesis 6.170.17 · schemathesis 4.34.2 · locust 2.47.0 | | |
| Backend QA | ruff 0.17.6 · pip-audit 2.10.1 | | |
| Formats (later) | defusedxml 0.7.1 · openpyxl 3.1.5 · xlrd 2.0.2 · pypdf 7.1.1 · python-docx 1.2.0 · python-pptx 1.0.2 · pillow 13.0.0 · polars 2.1.0 | | re-check at each phase |
| Frontend | next | 16.4.6 | |
| Frontend | react / react-dom | 19.3.1 | |
| Frontend | tailwindcss / @tailwindcss/postcss | 4.3.5 | |
| Frontend | next-intl 4.16.1 · next-themes 0.4.6 · @tanstack/react-query 5.108.4 | | |
| Frontend | typescript | 7.0.2 | **Pinned 6.0.3** (newest 6.x). typescript-eslint 8.74.0 peer range is `>=4.8.4 <6.1.0`, and ESLint crashes on 7.0.2 (frontend, issue #1). Revisit TS 7 when typescript-eslint supports it. Frontend verifies Vitest in F0. |
| Frontend QA | eslint 10.15.0 · eslint-config-next 16.4.6 · prettier 3.10.1 | | |
| Frontend test | vitest 5.1.1 · @playwright/test 1.65.1 · msw 3.0.7 · @axe-core/playwright 4.14.0 · @lhci/cli 0.16.1 | | |
| Contract | openapi-typescript 7.13.0 · openapi-fetch 0.17.0 | | |

**Dev machine (Developer A), 2026-11-24:** git 2.56.1 ✓ · gh 2.105.0 ✓ · uv 0.13.9 ✓ · Python 3.13.14 (Microsoft Store; use a uv-managed 3.14 instead) · Docker 29.9.3 ✓ (Desktop installed, but the daemon was not running) · VS Code 1.147 ✓ · psql is not needed (use Postgres in Docker).
**Final state 2026-11-24 (verified with `Get-Command` and `--version`, all on PATH):**
- git 2.56.1 · gh 2.105.0 (keyring login `khaledhagar`; works from PowerShell, not from Git Bash)
- uv 0.13.9 · Python **3.14.10** (managed by uv) · pre-commit 4.7.0 (`~/.local/bin`, now on the user PATH)
- Node 26.13.1 · npm 11.20.0 · gitleaks 8.30.1 · Docker 29.9.3 (start Docker Desktop at Phase 4) · VS Code 1.147
- **pnpm:** 12.21.0 on PATH (winget, which has no newer version yet). `pnpm self-update` put 12.23.0 in `%LOCALAPPDATA%\pnpm`, which is not on PATH. This does not matter: the repo pins `packageManager: pnpm@12.23.0`, and pnpm then uses exactly that version.

**Second dev machine (Developer A), checked 2026-11-24 in Session 8:** git 2.49.0 · gh 2.102.0 · uv 0.11.6 · Node 22.16.0 · npm 10.9.2 · Docker 29.5.2 · Python 3.13.3 and 3.12 only. Missing at first: gitleaks, pnpm, pre-commit, Python 3.14. `D:\Projects\replora` did not exist and was cloned again.
**After the owner's installs (same session):** gitleaks 8.30.1 · pnpm 12.23.0 · Node 26.13.1 · uv 0.13.9 · Python 3.14 (uv-managed) · pre-commit 4.7.0. git 2.49 and gh 2.102 kept as they are.

---

## Session 16 — 2026-11-26 (other machine, `D:\Projects\replora`): finish Phase 1
**Goal (Developer A):** finish Phase 1 without stopping for permission between steps. Check for frontend replies at every step and post the state.

**Setup:** ran handover Parts 1–5. 12 merged local branches were deleted (each PR `MERGED`, #27–#45), and the memory notes were restored. On `feat/p1.4-plan-hash` `5570037`: ruff clean (56 files), **491 passed**, no drift, pip-audit clean, frontend lint/typecheck/test **186 passed** (26 files), gitleaks no leaks. Not done here: `pre-commit install` and the `noreply` email in global git config (blocked for Claude, left to Developer A).

**Merges and reviews:**
- **#60 (P1.4) merged** as `881de20` (frontend approval at `5570037`, CI 4/4, Developer A's standing go).
- **Developer A's approvals** on the frontend's PRs, each delta read first: **#58** `75528d1`, **#61** `6d19d8d` (docs), **#62** Select `99f0a68`, **#63** Tabs `7c3f520`, **#64** StatusChip + Skeleton `8771fa1` (the 12 states match `api_contract.md:154`), **#65** EmptyState + ErrorState `65f60ce`.
- **#66 Table `44d097a`: changes requested in a comment.** In RTL, a numeric `<td dir="ltr">` resolves `text-end` to the right, while its `<th>` resolves it to the left. The test compares class names only. Suggested fix: keep the `<td>` in the table direction and wrap the digits in `<span dir="ltr">`.
- State posted on #1 (7200405319).

**P1.5: `app/core/run_state.py`** (branch `feat/p1.5-run-state`):
- `RunState` (12, moved from `run_models.py` with the same docstring, so **`openapi.json` is unchanged**) and `RunAction` (12 actions).
- `TRANSITIONS`: a read-only `(state, action) → state` table with **16 entries**:
  - `DRAFT →validate→ VALIDATED →request_approval→ AWAITING_APPROVAL`, and `VALIDATED →request_review→ NEEDS_REVIEW`;
  - `AWAITING_APPROVAL`: `approve → QUEUED`, `expire → EXPIRED`, `cancel → CANCEL_REQUESTED`;
  - `NEEDS_REVIEW`: `resolve → AWAITING_APPROVAL` (a new `plan_hash`, approved again), and `cancel → CANCELLED` straight away (#1, 7186123958);
  - `QUEUED`: `start → RUNNING`, `cancel → CANCEL_REQUESTED`;
  - `RUNNING`: `succeed`, `finish_partial`, `fail`, `request_review → NEEDS_REVIEW` (a low-confidence result or replay drift, P3.4 and P13.2), `cancel → CANCEL_REQUESTED`;
  - `CANCEL_REQUESTED →confirm_cancel→ CANCELLED` (the worker checks between nodes, P3.6).
- `TERMINAL_STATES` (`SUCCEEDED`, `PARTIAL`, `FAILED`, `CANCELLED`, `EXPIRED`) is derived from the table. `next_state()` raises `InvalidTransitionError` with `params = {from, action}`, which is the 409 `INVALID_STATE_TRANSITION` body. `can_move(source, target)` answers for a pair.
- **TDD:** `test_run_state.py` was red first (collection error, no module), then **297 passed**. **T1.5:** all 144 pairs are checked against an `ALLOWED` set written out by hand from §7, plus all 144 `(state, action)` pairs against the table. Also: approve only in `AWAITING_APPROVAL`, the cancel rules, resolve, terminal states have no way out, every state is reachable from `DRAFT`, the table can't be changed at runtime, and the API reuses the core enum.
- **The tests bite:** making `NEEDS_REVIEW` cancel go to `CANCEL_REQUESTED` fails 3, and allowing `FAILED → RUNNING` fails 2. Restored, 297 pass.
- Checks: ruff clean (58 files), **788 passed**, no drift.
- **P1.5 and T1.5 ticked.** Opened as **#68**. Also approved the frontend's new **#67** (error-code mapper, `41ac63d`): its `PROBLEM_CODES` equals the 26 `problem_codes`.

**P1.5b: the `NEEDS_REVIEW` resolution endpoint** (branch `feat/p1.5b-resolve-review`, stacked on #68). `api_contract.md` §7 said it is specified with the P1.5 table at G1.
- `POST /workspaces/{ws}/runs/{id}/resolve` (`runs_resolve`): body `ResolveRequest {plan_hash, choices: [ReviewChoice {code, path, value}]}` (1–100 choices), a required `Idempotency-Key`, and 200 `Run` back. It's a 501 stub until Phase 8.
- `Run.review_issues: [Issue]` (default `[]`): the open questions. Each issue lists its allowed answers in `params.options`.
- The cancel docstring now says `NEEDS_REVIEW` stops at once. `api_contract.md` §7 has the resolve row, `review_issues`, the cancel rule and the **transition table**.
- **TDD:** 9 red (the path, the idempotency key, the 422 bodies, the schema fields), then 30 passed in `test_run_stubs.py`.
- **The contract change only adds:** a script comparing `HEAD` and the new `openapi.json` shows schemas added `JsonValue`, `ResolveRequest`, `ReviewChoice`, none removed; the path added is `…/resolve`, no path changed; `Run` gains only the optional `review_issues` (`required` unchanged). `schema.d.ts` regenerated.
- Checks: ruff clean (58 files), **795 passed**, no drift, frontend typecheck clean and **186 passed**. Opened as **#69** (base #68).

**P1.6: domain JSON Schemas and golden fixtures** (branch `feat/p1.6-json-schemas`, stacked on #69):
- `app/export_schemas.py` writes `contracts/schemas/<Name>.schema.json` (draft 2020-12, with `$schema` and `$id`) for `ArtifactRef`, `OperationContract`, `RunState`, `ValidationReport`, `WorkflowDefinition` and `WorkflowDraft`, via `TypeAdapter(...).json_schema()`. `--check` fails on drift or a stale file. **CI runs it** in the backend job (new step).
- `contracts/fixtures/domain/<Name>.json`: `valid`, `invalid` and `invalid_backend_only` cases. The last group breaks a cross-field rule that JSON Schema can't express (workflow id without version, explanation key xor text, `valid` ⇔ no errors, lineage completeness), so only the backend model rejects it.
- **The API's `WorkflowDefinition` placeholder is replaced** by the core model (`draft_models.py` re-exports it). `openapi.json` gains `Edge`, `InputContract`, `Node`, `OutputContract`, `PortRef`, `ResourcePolicy`, `ReviewPolicy`; only `WorkflowDefinition` changed, and no path changed (comparison script). `schema.d.ts` regenerated; the frontend typecheck and its 186 tests pass. The draft stub test's sample PATCH body is now a real definition, and a new test shows `{}`, a definition missing `inputs`/`outputs`, or one with an extra field gets 422.
- **TDD:** `test_domain_schemas.py` was red first (no `app.export_schemas`), then **60 passed**: drift, schema ↔ fixture file parity, each schema is valid draft 2020-12, valid cases pass the schema and round-trip (dict and JSON, T1.1), invalid cases fail the schema and the model, backend-only cases pass the schema and fail the model (T1.6).
- **The tests bite:** a typo in a valid fixture's `code` fails 1; `additionalProperties: true` in a committed schema fails the drift test. Restored, 60 pass.
- Checks: ruff clean, **856 passed**, both drift checks exit 0, frontend typecheck, format and 186 tests pass.
- **P1.6 and T1.6 ticked.** Opened as **#70** (base #69). Answered the frontend's question on #67 (7200812426): their copy for the four client-bug codes and `PRECONDITION_FAILED` matches `error-codes.json`.

**P1.7, S‑10, S‑11** (branch `feat/p1.7-model-audit`, stacked on #70):
- **`test_model_audit.py` (T1.2):** walks the `app` package and audits **every** Pydantic model it finds (96, so a new model is audited without being listed): `extra="forbid"` and `frozen=True`. It was **red first: 78 failed** (every API body lacked `frozen`, and `Health` was a plain `BaseModel`).
- Fix: `ApiModel` is now `ConfigDict(extra="forbid", frozen=True)`, and `Health` is an `ApiModel`. The only contract change is `additionalProperties: false` on `Health`. `schema.d.ts` is unchanged.
- **T1.1:** every golden fixture round-trips (P1.6), as do the per-module round-trip tests of P1.1–P1.3.
- **S‑10:** `test_no_code_execution.py`, an AST scan of `app/` (no semgrep; see `decisions.md` 2026-11-26). A probe showed ruff's banned-api misses `compile()` and `__import__()`. The scan has 14 probe cases, one per banned form. The first run flagged `from importlib.metadata import version` (`main.py`, `health.py`), which only reads the package version, so `importlib.metadata` is allow-listed. A probe file `app/_s10_probe.py` with `eval("1")` fails the scan; removed, it passes.
- **S‑11 (Phase 1 part):** T1.3 and T1.4 pass; `approve` and `resolve` need the `plan_hash` the user saw; `Run` has `approved_by` and `approved_at`. Storing and checking the approver is **T3.1**, so S‑11 is re-verified at G3 (`security.md`).
- **P1.7, T1.1, T1.2 and S‑10 ticked.**

**End-of-phase run (Phase 1), on `feat/p1.7-model-audit` (the top of the stack):**
| Check | Result |
|---|---|
| `uv run ruff check .` · `ruff format --check .` | clean · 62 files |
| `uv run pytest -q` | **1101 passed** |
| Phase 1 tests only (`test_core_*`, `test_plan_hash`, `test_run_state`, `test_domain_schemas`, `test_model_audit`, `test_no_code_execution`) | **691 passed** |
| `export_openapi --check` · `export_schemas --check` | exit 0 · exit 0 |
| `uv run pip-audit` | no known vulnerabilities |
| `pnpm gen:api` + `git diff --exit-code schema.d.ts` | no drift |
| frontend lint · format:check · typecheck · test · build | clean · clean · clean · **186 passed** · built |
| `pnpm audit --audit-level=high` | no known vulnerabilities |
| `gitleaks git .` | no leaks found |

**Gate G1: approved by Developer A** (the gate approver for backend gates), in this session's instructions: finish Phase 1 and then continue into Phase 2 without stopping for permission. **Condition:** the stack #68 → #69 → #70 → the P1.7 PR merges with the frontend's review (contract changes in #69 and #70). Phase 2 work is stacked on top until then. Recorded in `decisions.md`.

**Phase 2 starts (G1 approved).**

**P2.1: `app/core/registry.py`** (branch `feat/p2.1-operation-registry`, stacked on #71):
- `OperationRegistry(contracts)`: `register`, `get(id, version)`, `versions(id)` and `list()` (sorted by id then version, for `GET /operations`). Two versions of one operation live side by side.
- `RegistryError(code, **params)`. `OP_DUPLICATE` (a repeated `(id, version)`) and `OP_PARAMS_SCHEMA_INVALID` are startup errors for developers. `OP_UNKNOWN` and `OP_VERSION_INVALID` (with `params.known`) reach users through the validator.
- A params schema must be in the §5 subset: a `type: object` whose properties are `string` (an `enum` only here), `integer`, `boolean` or an array of strings. No `oneOf`, `anyOf`, `allOf`, `not`, `$ref`, `$defs` or `if/then/else` anywhere. Pure Python, no new dependency.
- **New `contracts/error-codes.json` → `workflow_codes`** (the validator's `Issue` codes), mirrored by `app/core/issue_codes.py` `IssueCode`, with a parity test. It starts with `OP_UNKNOWN` and `OP_VERSION_INVALID`; each Phase 2 step adds its own. The frontend's #67 parity test reads the other sections by name, so it is unaffected.
- **TDD:** `test_registry.py` was red first (no module), then **16 passed**. The parity tests were red (2 failed) until the section was added. **The tests bite:** without the duplicate guard 1 fails; accepting any array `items` fails 1.
- Checks: ruff clean (65 files), **1120 passed**, no drift.
- **P2.1 and T2.1 ticked.** Opened as **#72** (base #71).

**P2.2 + P2.5: `app/core/validator/`** (branch `feat/p2.2-structural-validator`, stacked on #72):
- `validate(definition, registry) -> ValidationReport`. **It never raises.** `Graph.build` indexes the nodes and resolves each operation. `structure.check` covers the edge and IO references, port bindings, unbound required inputs and cycles.
- Codes (in `workflow_codes` and `IssueCode`):
  - `NODE_ID_DUPLICATE` (the second node, `nodes/i/id`);
  - `OP_UNKNOWN` / `OP_VERSION_INVALID` (`nodes/i/operation`, with `params.known`; versions ≤ 0 too: P2.5);
  - `NODE_UNKNOWN` (`…/node_id`, `params.node_id`);
  - `PORT_UNKNOWN` (`…/port`, `params.port` and `params.direction`, so an edge *from* an input port is caught);
  - `EDGE_DUPLICATE` (the second edge);
  - `PORT_BOUND_TWICE` (an input fed twice; one output may feed many inputs);
  - `PORT_UNBOUND` (a required input with no edge and no workflow input, `nodes/i`, `params.port`);
  - `DAG_CYCLE` (`params.nodes`: only the nodes on the loop).
- **Cycles:** Kahn's algorithm forwards, then on the reversed edges of what is left. That drops nodes downstream or upstream of a loop, so only the loop is named. It's linear in nodes plus edges, so an oversized definition can't make the validator slow (the limits come in P2.4).
- A node whose operation didn't resolve gets no port findings, so one mistake gives one issue.
- **TDD:** `test_validator_structure.py` was red first (no module), then **22 passed**. They include T2.2 (self-loop, 2-cycle, a 6-cycle with nodes before and after it), T2.4 and T2.7, and three hypothesis tests: **T2.8** random DAGs validate and one back-edge always gives `DAG_CYCLE` (200 examples each), and random malformed definitions never raise (300). One real bug was found on the way: the `issue()` helper's `node_id` parameter swallowed `params.node_id`, and it was renamed.
- **The tests bite:** skipping the reverse peel fails 1; dropping the bound-twice rule fails 1; ignoring self-loops fails 1.
- Checks: ruff clean (70 files), **1145 passed**, no drift.
- **P2.2, P2.5, T2.2, T2.4, T2.7 and T2.8 ticked.** Opened as **#73** (base #72). It's 508 added lines, over the 400 guideline (code 175, tests and the shared samples 286); I noted that in the PR.

**P2.3: `app/core/validator/types.py`** (branch `feat/p2.3-type-checks`, stacked on #73):
- **Ports match exactly, with no implicit conversion**, on edges (`edges/i`), workflow inputs (`inputs/i/targets/j`) and outputs (`outputs/i/source`): `PORT_TYPE_MISMATCH` with `params.port`, `expected` and `got`. A port that doesn't resolve is skipped, since it's already `PORT_UNKNOWN`.
- **Params:** `PARAM_INVALID` at `nodes/i/params/<field>` with `params.field` and `params.rule` (the JSON Schema keyword: `required`, `type`, `enum`, `pattern`, `additionalProperties`, …). Never the library's English message. One issue per field.
- **`jsonschema` moved from the dev group to the runtime dependencies** (`uv remove --dev jsonschema; uv add "jsonschema>=4.26.0"`). The lock keeps the same versions (4.26.0, `referencing` 0.37.0, `rpds-py` 2026.9.1), and pip-audit is clean.
- **TDD:** `test_validator_types.py` was 9 red first, then **12 passed** (T2.3 TabularArtifact ← TextDocumentArtifact rejected; T2.6 one case per rule). **The tests bite:** skipping the type compare fails 3; dropping the `required` check fails 2.
- Checks: ruff clean, **1158 passed**, no drift, pip-audit clean.
- **P2.3, T2.3 and T2.6 ticked.** Opened as **#74** (base #73).

**Frontend update (#1, 7201098960):** they merged #58, #61, #62, #64, #65 and #67. #63 was re-approved at `e5e5b27` after their merge from `main` (against `main` the diff is only Tabs). They are fixing #66. **They asked that #68–#71 not be merged before their review** (agreed, 7201146791).

**P2.4 + P2.6: limits and the location guarantee** (branch `feat/p2.4-validator-limits`, stacked on #74):
- `app/core/limits.py`: `MAX_NODES = 30`, `MAX_DEPTH = 10` (nodes on the longest path), `MAX_FAN_IN = MAX_FAN_OUT = 10`.
- `app/core/validator/limits.py`, run **first**: `LIMIT_NODES` (`nodes`), `LIMIT_DEPTH` (`edges`; measured only when there's no cycle, since that is `DAG_CYCLE`), `LIMIT_FAN_IN` / `LIMIT_FAN_OUT` (`nodes/i`), `LIMIT_FILES` (`inputs` for workflow inputs, `files` for the files given), `LIMIT_FILE_SIZE` (`files/i`). All carry `params.limit` and `params.actual`. File limits come from the definition's `ResourcePolicy`, so a stricter policy lowers them.
- `validate(definition, registry, file_sizes=())`: the run path will pass the bound files' sizes.
- **TDD:** `test_validator_limits.py` was red first (no module), then **18 passed**. T2.5 tests each boundary on both sides: 30/31 nodes, depth 10/11, fan-in and fan-out 10/11, files 2/3 under `max_files=2` and 10/11 given, size 50 MiB / +1 byte. A 5000-node chain is reported in about 0.2 s (bound: 2 s). **The tests bite:** `>=` instead of `>` fails 7; counting depth in edges fails 1; dropping the given-files count fails 1.
- **P2.6:** `test_validator_codes.py` has one scenario per `IssueCode` (**18 codes**). A code without a scenario fails the parity test (checked by adding a fake one). Each issue's path resolves inside the definition (all but the last segment; `files/…` refers to the given files). Node-scoped codes name a real node, and port codes name the port. These passed on the first run, because they assert properties the code already had.
- **`workflow_codes` is complete for Phase 2**: OP_UNKNOWN, OP_VERSION_INVALID, NODE_ID_DUPLICATE, NODE_UNKNOWN, PORT_UNKNOWN, PORT_UNBOUND, PORT_BOUND_TWICE, EDGE_DUPLICATE, DAG_CYCLE, PORT_TYPE_MISMATCH, PARAM_INVALID and LIMIT_NODES/DEPTH/FAN_IN/FAN_OUT/FILES/FILE_SIZE.
- **P2.4, P2.6, T2.5 and S‑12 ticked.**

**End-of-phase run (Phase 2), on `feat/p2.4-validator-limits` (the top of the stack):**
| Check | Result |
|---|---|
| `uv run ruff check .` · `ruff format --check .` | clean · 76 files |
| `uv run pytest -q` | **1196 passed** |
| Phase 2 tests only (`test_registry`, `test_validator_*`, `test_error_codes`) | **117 passed** |
| `export_openapi --check` · `export_schemas --check` | exit 0 · exit 0 (Phase 2 doesn't change `openapi.json`) |
| `uv run pip-audit` | no known vulnerabilities |
| `pnpm gen:api` + `git diff --exit-code schema.d.ts` | no drift |
| frontend lint · format:check · typecheck · test | clean · clean · clean · **186 passed** (on this stack's base; the frontend's newer merges are on `main`) |
| `pnpm audit --audit-level=high` | no known vulnerabilities |
| `gitleaks git .` | no leaks found |

**Merges after the frontend's review (#1, 7201202275):** they approved #68–#71 at their heads and asked for in-order merges with a ping after each rebase (a push dismisses approvals). **#68 merged** (`1eb5085`). **#69** was rebased with `git rebase --onto origin/main f552b36` (range-diff `a3bf12e = 06c1568`) and retargeted to `main`. On the rebased branch: 795 passed, no drift, and the frontend typecheck plus 367 tests pass with their merged PRs. Pinged on #69 (7201289845). **#66** re-approved at `f80642e` (the RTL fix is right).

**Gate G2: Phase 2 is complete and waiting for Developer A's approval.** Developer A's instruction was to finish Phase 2, not to go past it. So Phase 3 doesn't start until G2 is approved.

**G2 approved** by Developer A (2026-11-26, `decisions.md`). **#69 merged** (`ef29ba7`). **#70** rebased (`b1d1ae2 = 9447c56`; 856 passed, no drift), retargeted to `main`, pinged (7202790463). **#76** (frontend, TanStack Query provider and `useMe`) reviewed and approved.

**Phase 3 starts: P3.1 and P3.2** (`app/core/engine/run.py`, `tests/unit/test_engine_run.py`, TDD: collection failed first). `transition` enforces the P1.5 table (all 16 allowed pairs move the run, and all 128 illegal pairs raise `InvalidTransitionError` with `{from, action}`). `approve` needs the run's exact `plan_hash` and records who approved and when. `START` re-checks the approval against the current definition (T3.1, S‑11 Phase 3 part). Mutation checks: dropping each of the three guards fails 1–2 tests.

| Command | Result |
|---|---|
| `uv run pytest -q` | **1353 passed** |
| `ruff check` · `ruff format --check` | clean · clean |
| `export_openapi --check` · `export_schemas --check` | exit 0 · exit 0 |
| `gitleaks git .` | no leaks found |

PR **#77** (stacked on #75).

**P3.3, the in-memory executor** (`app/core/engine/executor.py`, `store.py`, `tests/unit/test_engine_executor.py`; TDD: collection failed first).
- `topological_order` is Kahn's algorithm. When several nodes are ready, the one listed first in the definition goes first, so the order is stable.
- `execute` starts the run, so the approval is checked, then runs each node through its handler (keyed by `(op id, version)`). Every output goes into the `ArtifactStore` with its SHA‑256 and its lineage: run, node, operation and parent artifacts. The run ends `SUCCEEDED`.
- Run and artifact IDs are UUIDv7 (`uuid.uuid7`, Python 3.14).
- **T3.2:** a diamond graph (fan-out a→b,c and fan-in b,c→d, listed out of order) runs as `a, c, b, d`, with each node run once. The tests check content, hash, lineage, input feeding, and that an unapproved run doesn't execute.
- Mutation checks: reversing the tie-break, dropping the parents, skipping `START`, or ignoring the indegree each fails 1–3 tests.
- `uv run pytest -q`: **1360 passed**. ruff is clean.

PR **#78** (stacked on #77).

**P3.4, failure semantics** (`executor.py` now has a small `_Runner`; `app/core/run_issue_codes.py`; `tests/unit/test_engine_failures.py`; the shared fakes moved to `tests/unit/engine_samples.py`; TDD: collection failed first).
- Handlers now return `Result(outputs, warnings)`. A handler that raises `OperationError(code, **params)` fails its node (`NODE_FAILED`, `params.error` is the operation's code). A node whose required input came from a failed or skipped node is skipped (`NODE_SKIPPED`, with `params.port` and `params.source`).
- The run ends `FAILED` when a workflow output is missing (`OUTPUT_MISSING`). It ends `PARTIAL` when something failed but every output exists. It stops at once as `NEEDS_REVIEW` when a node warns (for example `LOW_CONFIDENCE`) under `review_policy.on_warning = review`; under `continue`, the warning is kept and the run finishes.
- **New `contracts/error-codes.json` → `run_codes`** (NODE_FAILED, NODE_SKIPPED, OUTPUT_MISSING, LOW_CONFIDENCE), mirrored by `RunIssueCode` with a parity test. `contracts/README.md` was updated. The frontend's parity test reads its sections by name, so it is unaffected.
- **T3.3:** an optional branch → PARTIAL, a required branch → FAILED (the dependent node never runs), a failed output node → FAILED, low confidence → NEEDS_REVIEW and later nodes don't start, and the continue policy → SUCCEEDED with the warning.
- Mutation checks: each of the five rules fails 1–3 tests when removed.
- `uv run pytest -q`: **1367 passed**. ruff is clean.

PR **#79** (stacked on #78).

**P3.5, retry and idempotency** (`executor.py`, `tests/unit/test_engine_retry.py`; TDD: collection failed first).
- Only a `TransientError` (a subclass of `OperationError`) is retried: at most `MAX_RETRIES = 2` more times, with backoff of 0.5 s then 1 s. `sleep` is injectable, so the tests don't wait.
- `NODE_FAILED` now has `params.attempts`. Any other `OperationError` gets a single attempt.
- **Idempotency:** a node that succeeds is recorded in the ledger under `(run_id, node_id, sorted (port, input sha256))`. A later attempt with the same ledger reuses its artifacts and warnings and doesn't call the handler. A failed node isn't recorded, so the next attempt runs it, and the nodes after it run again only if their inputs changed.
- **T3.4 and T3.5:**
  - recovery after 2 transient errors;
  - 3 attempts at most;
  - a non-transient error is never retried;
  - a second execution has a spy count of 1 per node and the same outputs;
  - the key includes the run;
  - a failed node is re-run later.
- Mutation checks: the ledger check, the run in the key, the input hashes in the key, retrying any `OperationError`, the backoff growth, and both off-by-ones in the attempt guard each fail 1–4 tests. A redundant `range` bound survived a mutation, so it was replaced by `itertools.count`.
- `uv run pytest -q`: **1374 passed**. ruff is clean.

PR **#80** (stacked on #79).

**P3.6, cancellation and expiry** (`run.py`, `executor.py`, `app/config.py`, `tests/unit/test_engine_cancel.py`; the cancel tests failed first).
- `transition(run, action, at)` now takes the time, and `Run.state_since` records when the current state began. The executor gets the time from an injectable `clock`.
- **Cancel:** `execute(..., cancelled=...)` asks before every node. Once it says yes, the run goes RUNNING → CANCEL_REQUESTED → CANCELLED and no other node starts. A run already CANCEL_REQUESTED when it is picked up is confirmed CANCELLED without starting. The cancel API itself is the P1.5 table: NEEDS_REVIEW → CANCELLED at once.
- **Expiry:** `expire_if_stale(run, now, ttl)` expires a run that has been AWAITING_APPROVAL for **longer** than the TTL. `Settings.approval_ttl_hours` defaults to 24 (`APPROVAL_TTL_HOURS` in `.env.example`). The scheduler that calls it belongs to the worker (Phase 8).
- **T3.6 and T3.7:**
  - cancel after two nodes → CANCELLED, with only those two artifacts;
  - cancel before the first node;
  - cancelled while queued → never starts;
  - the TTL boundary on both sides;
  - only AWAITING_APPROVAL expires;
  - the setting.
- Mutation checks: the between-node check, the queued-cancel check, `>` vs `>=`, the state guard, and recording `state_since` each fail 1–11 tests.
- `uv run pytest -q`: **1392 passed**. ruff is clean.

PR **#81** (stacked on #80). Answered the frontend's 401 note on #76 (7203186020): refresh is a CSRF-protected POST, and refreshes must be single-flight because the token rotates.

**P3.7, replay** (`app/core/engine/replay.py`, `tests/unit/test_engine_replay.py`; collection failed first).
- `start_replay(definition, inputs, now)` takes a **saved** version only (otherwise `ValueError`) and the new files, each a `ReplayInput(ref, columns)`.
- Each file is checked against its input contract. A different artifact type gives `INPUT_TYPE_MISMATCH`, and missing expected columns give `INPUT_COLUMNS_MISSING`; extra columns are fine. A mismatch gives NEEDS_REVIEW with the issues. Otherwise the run is AWAITING_APPROVAL and still needs its own approval (S‑11).
- Two new `run_codes`, mirrored in `RunIssueCode`.
- **T3.8:** two replays of the same pinned version on the same content give identical output hashes.
- Mutation checks: each of the five rules fails 1–3 tests.
- `uv run pytest -q`: **1398 passed**. ruff is clean.

PR **#82** (stacked on #81).

**P3.8, the MockPlanner and fake adapters** (test-only, `tests/integration/fakes.py` and `test_engine_pipeline.py`).
- Five fake operations with real stdlib logic: `fake_unzip` (one ZIP → CSV and JSON members), `fake_parse_csv`, `fake_parse_json`, `fake_compare` (key and value, giving match, mismatch, only_left and only_right), and `fake_render` (a CSV report).
- `MockPlanner.plan()` returns the same draft for any task. A test checks that nothing under `app/` mentions `MockPlanner`.
- **T3.9:** the planner's draft validates. The pipeline runs end to end, and the report equals the expected CSV byte for byte.
- **T3.10:**
  - a transient JSON-parse failure is retried twice and recovers;
  - a second attempt with the same ledger calls no handler (5 calls in total);
  - a cancel after the unzip stops both branches;
  - a failed JSON branch gives FAILED, with compare and render skipped;
  - a replay of the saved pipeline gives the same report hash.
- A sanity mutation (compare always says "match") fails 2 tests.
- The TTL test now uses `Settings(_env_file=None)`, so a developer's `.env` can't affect it.
- `uv run pytest -q`: **1406 passed** (unit and integration). ruff is clean.

PR **#83** (stacked on #82).

**P3.9 part 1, the TemplatePlanner's reconcile template** (`app/core/planner/template.py`, `app/core/planner_codes.py`, `tests/unit/test_template_planner.py`; collection failed first).
- `plan(template_id, files)` takes `FileFacts` (label, format csv|json, and columns with kind and uniqueness, never rows) and returns a deterministic `WorkflowDraft`: `parse_csv|parse_json` ×2 → `compare{key, value}` → `report_csv`. The input contracts carry each file's columns, for replay drift.
- **Rules:**
  - Columns match when their names are equal after NFKC and trimming, case-sensitive, so the planner never guesses.
  - The key is a column both files have and that is unique in both. The value is a shared numeric column other than the key.
  - Among several candidates, a name hint (`id`, `code`, `رقم`…; `amount`, `المبلغ`…, compared case-insensitively) can settle a tie, but never picks a column on its own.
  - When it is still unclear, the parameter is left out and the draft carries a warning. The validator then reports `PARAM_INVALID`, so the user must choose.
- **Operation ids the templates use:** `parse_csv`, `parse_json`, `compare` and `report_csv`. Phase 7 must register them under these ids (P7.1 and P7.2).
- **New `contracts/error-codes.json` → `planner_codes`** (KEY_NOT_FOUND, KEY_AMBIGUOUS, VALUE_NOT_FOUND, VALUE_AMBIGUOUS), mirrored by `PlannerCode` with a parity test.
- **T3.11:**
  - picks `order_id` and `amount` on acceptance-like files;
  - no shared key → `KEY_NOT_FOUND` and no key;
  - ambiguous → `KEY_AMBIGUOUS` with the candidates;
  - deterministic `plan_hash`;
  - Arabic columns (`رقم الطلب`, `المبلغ`) work.
- Mutation checks: all 6 rules are caught. Two survived at first (a numeric key excluded from the value, and case-insensitive hints), so tests were added for both.
- The merge template follows in the next PR, which closes P3.9.
- `uv run pytest -q`: **1426 passed**. ruff is clean.

PR **#84** (stacked on #83).

**P3.9 part 2, the merge template** (`template.py`, `tests/unit/test_template_merge.py`; the tests failed first). `plan("merge", files)` takes 2–10 files and builds parse ×N → `append_rows` (in the given order, `in_0…`) → `export_csv`. A file whose columns differ from the first file's (after NFKC and trimming, in any order) gets a `COLUMNS_DIFFER` warning with `{file, missing, extra}`, so the merge is never silent. `TemplateSpec.max_inputs` was added, and `COLUMNS_DIFFER` joined `planner_codes`. Mutation checks: all 5 rules are caught. **P3.9 is done.**

**End-of-Phase-3 run** (top of the stack, `feat/p3.9-merge-template`):
| Command | Result |
|---|---|
| `uv run ruff check .` · `ruff format --check .` | clean · 96 files formatted |
| `uv run pytest -q` | **1433 passed** (unit and integration) |
| `export_openapi --check` · `export_schemas --check` | exit 0 · exit 0 |
| `uv run pip-audit` | no known vulnerabilities |
| `pnpm -C frontend run gen:api` + `git diff --exit-code schema.d.ts` | no drift |
| frontend lint · format:check · typecheck · test · build | clean · clean · clean · **186 passed** · built (on this stack's base) |
| `pnpm audit --audit-level=high` | no known vulnerabilities |
| `gitleaks git .` | no leaks found |

**Gate G3: Phase 3 is complete and waiting for Developer A's approval.** The instruction was to approve G2 and start Phase 3, not to go past it, so Phase 4 doesn't start until G3 is approved. **S‑13 note for the gate:** retries and cancellation are verified now. Node and run timeouts, the memory guard and the temp-dir quota need the worker that can stop a node (P8.3), so they are verified at T17.6, as `security.md` lists.

PR **#85** (stacked on #84).

**G3 approved** by Developer A (2026-11-26, `decisions.md`). They also said to do **Phases 4 and 5**: G4 is pre-approved once Phase 4 is verified, and **G5 stops for approval** (it is also I1). The final state and every open item were sent to the frontend on #1 (7203533845).

**P4.1, engine and sessions** (`app/db/engine.py`, `tests/unit/test_db_engine.py`; collection failed first).
- `uv add sqlalchemy alembic "psycopg[binary]"` locked sqlalchemy 2.1.9, alembic 1.20.1 and psycopg 3.3.9.
- `Settings.database_url` defaults to `sqlite:///<repo>/.data/replora.db` (`.data/` is git-ignored).
- `make_engine`: SQLite runs `PRAGMA journal_mode=WAL` and `foreign_keys=ON` on every connection. Postgres gets the psycopg 3 driver (a plain `postgres://` URL from Supabase is normalized) and `NullPool`. `make_sessions` uses `expire_on_commit=False`.
- `uv run pytest -q`: **1440 passed**. ruff is clean, pip-audit clean, no drift, no leaks.

PR **#86** (stacked on #85).

**P4.2 and P4.3 part 1: the base and the identity tables** (`app/db/base.py`, `app/db/models/identity.py`, `tests/unit/test_db_models.py`). The models came first here. The tests were then mutation-checked: dropping an index, the case-insensitive email index, the UTC conversion, the naive-timestamp refusal, or the foreign-keys pragma each fails 2–3 tests.
- **Base:** UUIDv7 primary keys (`uuid.uuid7`). `UtcDateTime` stores and returns UTC and refuses a naive datetime. JSON becomes JSONB on Postgres. A naming convention covers PK, FK and check constraints; indexes are named by hand, as §6 lists them.
- **Tables:** users (`uq_users_email` on `lower(email)`), workspaces (plus `personal`), memberships, sessions, auth_tokens, invitations, mfa_recovery_codes, audit_events (the actor is SET NULL on user deletion, so the entry is anonymized; S‑29) and rate_limits.
- **T4.6 (part):** the test parses `plan.md` §6 (18 tables). Every table is documented, every documented index exists, and every FK column leads an index. §6 gains `ix_invitations_invited_by` and `workspaces.personal`.
- **T4.5:** IDs are v7 and sort in creation order; a +03:00 time round-trips as UTC.
- **T4.7 (part):** a duplicate email in different case → IntegrityError; a duplicate membership → IntegrityError; FKs are enforced.
- `uv run pytest -q`: **1469 passed**. ruff is clean.

PR **#87** (stacked on #86).

**P4.2 and P4.3 part 2: the work tables** (`app/db/models/work.py`; the tests failed first, 6 failed).
- Tables: files, workflows, workflow_versions, drafts, runs, run_nodes, artifacts, run_events and jobs. The workspace FKs cascade, and the "by" FKs are SET NULL.
- `runs` gains `state_since` (for expiry) and `issues`. `run_nodes` gains `outputs` and `warnings`, so a done node is never re-executed (P4.6). §6 is updated, along with the extra FK indexes `ix_workflows_created_by` and `ix_runs_approved_by`.
- **T4.6:** all 18 §6 tables exist, every documented index exists, and every FK leads an index. **T4.5** is done. **T4.7 (part):** unique run idempotency key per workspace, workflow version, run node and event seq. JSON round-trips, Arabic included.
- Mutation checks: dropping `unique` on each of three indexes fails a test.
- **P4.2 and P4.3 are done.**
- `uv run pytest -q`: **1494 passed**. ruff is clean.

PR **#88** (stacked on #87).

**P4.4, Alembic** (`backend/alembic.ini`, `backend/migrations/`, `tests/integration/test_migrations.py`).
- `env.py` takes the URL from `DATABASE_URL` (or `config.attributes` in tests), with `render_as_batch=True` and `compare_type=True`. `UtcDateTime` is rendered as `sa.DateTime(timezone=True)`, so migrations don't import app code.
- `0001_initial_schema` was autogenerated on an empty SQLite and then **fixed by hand for two real bugs**:
  - Autogenerate used `Text()` without importing it, which would have been a `NameError`.
  - It **silently left out the expression index `uq_users_email` (`lower(email)`)**. Without the fix, case-insensitive email uniqueness would have existed only in the models.
- **T4.1:** upgrade → downgrade base → upgrade, with exactly the model tables each time. **T4.2:** `compare_metadata` gives no diff. A third test checks that the **migrated** schema rejects a duplicate email in a different case.
- Mutation checks: dropping the email index or `ix_sessions_user_id` from the migration fails a test.
- `uv run alembic upgrade head` works locally (`.data/replora.db`, `0001 (head)`), and the command is added to `README.md`.
- Postgres runs come with P4.7.
- `uv run pytest -q`: **1497 passed**. ruff is clean.

PR **#89** (stacked on #88).

**P4.5, workspace-scoped repositories** (`app/db/repos.py`, `tests/integration/test_repos.py`, `tests/unit/test_tenant_scoping_lint.py`; both failed first).
- `scoped(model, workspace_id)`: tenant tables filter on their own `workspace_id`; child tables are joined to the parent's workspace. `get` returns None for another workspace's row (404). `page` is newest first, with a `(created_at, id)` keyset cursor.
- **S‑14 lint:** no `select`, `update`, `delete` or `session.get` of a tenant model outside `scoped`. **S‑15 lint:** no `text()` built from an f-string, `%` or `.format()`. Each has probe cases. A `decisions.md` row records the choice of an AST lint over semgrep.
- **T4.3:** for all 8 tenant and child tables, workspace A and B each see only their own rows, and a cross-workspace `get` gives None. SQL payloads are stored and matched as plain data.
- Mutation checks: dropping the tenant filter, the child filter, the cursor direction, the order, or the scoping in `get` fails 1–14 tests.
- `uv run pytest -q`: **1652 passed**. ruff is clean.

PR **#90** (stacked on #89).

**P4.6, checkpointing** (`app/db/engine_state.py`, `tests/integration/test_checkpoint.py`; collection failed first).
- `DbLedger` keeps one `run_nodes` row per done node, keyed by a hash of (run, node, input hashes) and committed per node. `DbArtifactStore` writes `artifacts` rows with their lineage, and the content to a local blob folder until Phase 6 storage. `save_run` and `load_run` persist the run; it is found only in its own workspace.
- The executor now takes a `Store` protocol and a `Ledger` protocol, resumes a RUNNING run (re-checking its approval), and calls `checkpoint` when the run starts and ends.
- **T4.4:** killed at node 3 of 5, the run is RUNNING in the DB with 2 done nodes. A fresh process resumes, the done nodes are not re-executed, and the run ends SUCCEEDED.
- Mutation checks: the resume path, both checkpoints, and the input-hash check each fail a test.
- `uv run pytest -q`: **1660 passed**.

PR **#91** (stacked on #90).

## Session 17 — 2026-11-27: the stack starts merging, T4.8
- The frontend approved the whole stack up to #85 (#1, 7203581422 and 7203609353). **#70 merged** (`c5b735d`). I rebased #71–#91 locally in one pass (`git rebase --onto origin/main b1d1ae2 --update-refs`): all 21 commits are `=` in the range-diff. On the rebased top: 1660 backend and 396 frontend tests pass, no drift. Only **#71** was pushed (`e828fa5`) and pinged. The others are rebased one at a time, because every squash merge forces the next rebase (adjacent log and plan edits).
- I offered the frontend **option B**: squash-merge an approved contiguous range through its top PR (#1, 7205287647). A stays the default until they agree.
- **Frontend requests (additive contract):** `Limits.max_depth`, `max_fan_in` and `max_fan_out`, and `Run.approval_expires_at`. I promised one small contract PR on top of the stack.
- Reviewed and approved the frontend's **#92** (refresh and CSRF retry). The Phase 5 promises are recorded there: `GET /auth/csrf` always sets a fresh cookie, and a reused refresh token gives 401 `UNAUTHENTICATED` and revokes the family.
- **T4.8 and the rest of T4.7** (`app/db/jobs.py`, `tests/integration/test_jobs.py`; collection failed first):
  - `claim` leases the oldest due job in one atomic `UPDATE … WHERE id = (SELECT … LIMIT 1) RETURNING id`, with `FOR UPDATE SKIP LOCKED` on Postgres. An expired lease can be claimed again.
  - Two threads draining 40 jobs never share one. A naive select-then-update version made 65 claims for 40 jobs in 5 of 5 runs, so the test catches real double claims.
  - `uv run pytest -q`: **1667 passed**.
PR **#93** (stacked on #91).

**P4.7, the Postgres 17 CI job** (#94). The `backend-postgres` job runs `uv run pytest` against a `postgres:17` service through `TEST_DATABASE_URL`. A shared `db_url` fixture gives every database test a fresh SQLite file, or the CI Postgres with its schema reset. The first run failed only on `test_repo_rules`, which requires every CI job to be a required check, so `.github/rulesets/main.json` now lists the new job. The admin applies it **after** #94 merges. **CI run 45909868665: all 5 jobs green, and 1667 tests pass on Postgres.**

**Gate G4 passed** (pre-approved by Developer A, recorded in `decisions.md`). Phase 4: 7/7 steps, T4.1–T4.8, S‑14 and S‑15. **Next: the small contract PR** (`Limits.max_depth`, `max_fan_in`, `max_fan_out` and `Run.approval_expires_at`), **then Phase 5.**

PR **#94** (P4.7 and G4) and PR **#95** (contract: `Limits` depth and fan limits, `Run.approval_expires_at`).

**Phase 5 starts. P5.1, passwords** (`app/auth/passwords.py`, `app/auth/breached_passwords.txt`, `tests/unit/test_passwords.py`; collection failed first). The step text says "register and login", but the endpoints come with P5.2; this step is the hashing and the policy.
- `uv add "pwdlib[argon2]"` locked pwdlib 0.4.2. Hashes are argon2id with recommended parameters. `verify_and_update` upgrades old parameter sets at login (S‑20). Text is NFKC-normalized first.
- **Policy (NIST 800‑63B):** 12–256 characters (request models) and no composition rules. The breached list has 1183 entries of 12+ characters, lower-cased, from SecLists `100k-most-used-passwords-NCSC.txt` (MIT, downloaded with curl, filtered). It is checked ignoring case and outer spaces through an `AfterValidator` on `Password`, so `openapi.json` is unchanged and the 422 carries `PASSWORD_BREACHED` at `body.password`.
- **New `validation_codes` → `PASSWORD_BREACHED`.** The frontend's parity test on `main` allow-lists `validation_codes` exactly, and it is not on this stack's base. **When this PR is rebased onto `main`, add `"PASSWORD_BREACHED"` to `frontend/tests/unit/error-messages-parity.test.ts` in the same commit.**
- **T5.1 and T5.2:** argon2id and salted; right and wrong passwords; NFKC; rehash on login; breached ignoring case; long English and Arabic passphrases accepted; API 422 codes; no password field on `User` or `Me`. Mutation checks: all 3 rules are caught.
- `uv run pytest -q`: **1688 passed**. No drift, and pip-audit is clean.
PR **#96** (stacked on #95).

**P5.2 part 1: session and token logic** (`app/auth/tokens.py`, `app/auth/sessions.py`, migration `0002`; both test files failed first). `uv add pyjwt` locked 2.15.1.
- **Access token:** a JWT, **HS256 pinned** (`none` and HS512 are refused), 15 minutes, carrying `sub` (user) and `sid` (session). Time is checked against the injected `now`, so PyJWT's wall-clock `iat` check is off. Malformed tokens, other keys and missing claims give None.
- **Refresh token:** 256 random bits, and the DB keeps only its SHA‑256. `rotate` issues a new token on each use and moves the old hash into the new table `used_refresh_tokens`. **A used token seen again revokes the whole session (T5.4).** Revoked, expired (30 days) and unknown tokens don't refresh.
- **Migration 0002:** `users.display_name` (NOT NULL, `server_default ''`, so existing users upgrade) and `used_refresh_tokens`. §6 is updated to 19 tables.
- **Two bugs found and fixed.** Autogenerate added `display_name` as NOT NULL with no default, which would fail on a database that already has users; a test now upgrades one. Worse, **on SQLite a batch rebuild of `users` silently drops the expression index `uq_users_email`**, because reflection can't see it. 0002 now drops and recreates it around each rebuild, and a test checks case-insensitive uniqueness after every up and down. Mutation: without the guard, 3 tests fail. **Every future migration that rebuilds `users` must do the same.**
- `uv run pytest -q`: **1714 passed**. No drift.
PR **#97** (stacked on #96).

**P5.2 part 2: the session endpoints** (`app/api/v1/auth.py`, `app/api/session.py`, `app/auth/accounts.py`, `tests/integration/test_auth_api.py`; 11 tests failed first). **P5.2 is done.**
- `register`, `login`, `logout`, `refresh` and `GET /me` are real. Everything is read from the `Request`, so **`openapi.json` is unchanged**.
- The app holds its sessions, JWT key and clock in `app.state`. `Settings.jwt_secret` is a production secret (`JWT_SECRET` in `.env.example`); outside production a random key is made at startup.
- **Register:** always 202 with an empty body. The same argon2 cost is paid whether or not the email exists. A new user gets a **personal workspace with the owner role** (part of P5.5).
- **Login:** a generic 401 `INVALID_CREDENTIALS` (unknown users are verified against a dummy hash) and a rehash on login. It sets `replora_access` (15 min) and `replora_refresh` (30 days): **HttpOnly, SameSite=Lax, Path=/, and Secure in production (T5.6)**.
- **Refresh:** rotates the token. A reused token gives 401 and signs everyone out (T5.4 over HTTP). **Logout** revokes the session, after which its refresh token and even its **unexpired access token** are refused.
- Test updates: the production config tests pass a `jwt_secret`; the observability test's 501 example is now `/auth/sessions`; and the stub test skips the 5 endpoints that are real.
- Mutation checks: the revoked-session check (it survived at first, so a test now replays the access token after logout), Secure, HttpOnly and the password check are all caught.
- `uv run pytest -q`: **1727 passed**. No drift.
PR **#98** (stacked on #97).

**P5.3, CSRF** (`app/api/csrf.py`, `tests/integration/test_csrf.py`; failed first).
- A dependency on the whole v1 router: every POST, PUT, PATCH and DELETE needs `X-CSRF-Token` to equal the readable `replora_csrf` cookie (constant-time compare), login and register included. An `Origin` header, when present, must be in `Settings.allowed_origins` (`ALLOWED_ORIGINS`, default `http://localhost:3000`). A failure gives 403 `CSRF_FAILED`. It reads only the `Request`, so `openapi.json` is unchanged.
- `GET /auth/csrf` always sets a fresh cookie (as promised on #92), and login and logout rotate it. The cookie is readable (not HttpOnly), SameSite=Lax, Path=/, and Secure in production.
- **T5.5:** **every unsafe route in `openapi.json` (more than 30)** refuses a request without the token. Also tested: a mismatched token, a header without the cookie, a foreign `Origin` even with the token, safe methods passing, and rotation.
- Test clients use `conftest.with_csrf`, which copies the current cookie into the header on each request, as the browser client does. The production cookie test uses `https://testserver`, because Secure cookies only come back over https.
- Mutation checks: the Origin check, the compare, and the cookie requirement each fail 1–2 tests.
- `uv run pytest -q`: **1738 passed**.
PR **#99** (stacked on #98).

**P5.4, email verification and password reset** (`app/auth/one_time.py`, `app/auth/mail.py`, `tests/integration/test_auth_tokens_api.py`; collection failed first).
- One-time tokens: 256 bits, stored as SHA‑256 in `auth_tokens` with their kind, a **30-minute** expiry and `used_at`. They work once, and only for their own kind.
- **Mail** goes through `app.state.mailer`: `ConsoleMailer` locally (it prints the link), `Outbox` in tests. Subjects are in AR and EN, by the user's locale. Links point at `Settings.app_url` (`APP_URL`).
- **Register** sends a verification link to a new address, and a notice with no token to an existing account. **Verify** sets `email_verified_at`.
- **Forgot** always answers 202 with an empty body. **Reset** sets the new password (policy applied) and **revokes every session (S‑27)**. A bad, used, expired or wrong-kind token gives 400 `TOKEN_INVALID`.
- **T5.3** (now with verify), **T5.8** (single use, the 29/30-minute boundary, sessions revoked) and **T5.11** (same answer and body; timing difference < 50 ms) pass. Mutation checks: used and expired, the kind filter, and session revocation are all caught.
- Lesson: endpoint docstrings are OpenAPI descriptions, so changing one is contract drift. The S‑27 note is a comment.
- `uv run pytest -q`: **1750 passed**. No drift.
PR **#100** (stacked on #99).

**Developer A's standing go (2026-11-27):** finish Phase 5, then do **Phases 6, 7, 8 and 9** without asking. Update this log and push, and message the frontend with progress and open questions at the end of each phase. Keep working if the computer goes idle.

**P5.5 and P5.6, roles and route permissions** (`app/auth/permissions.py`, `app/auth/access.py`, `tests/integration/test_permissions.py`).
- The roles are owner, admin, member and viewer. `MATRIX` maps 15 permissions to roles, and `security.md` mirrors it, now with the read permissions and `runs.create`. A personal workspace (owner) is created at registration (P5.2).
- **`TABLE`** declares all 64 routes as public, signed-in, or needing a permission. **`authorize`**, a v1 router dependency next to CSRF, enforces it:
  - 401 `UNAUTHENTICATED` with no session;
  - **404 `NOT_FOUND`** when the caller isn't a member, or the id is malformed;
  - 403 **`PERMISSION_DENIED`** (a new problem code) when the role lacks the permission.
- **`check_table`** runs at startup and refuses an app whose routes and table differ (S‑21). The routes come from the OpenAPI document, because FastAPI 0.165 keeps included routers lazy. `openapi.json` is unchanged.
- **T5.9:** 64 routes × 6 callers (owner, admin, member, viewer, non-member, anonymous), generated from the table, plus a malformed id. **T5.10** is covered at the route level: a non-member gets 404 on every workspace resource route. A row in another workspace looked up from your own is None in the repositories (T4.3).
- The stub tests use `conftest.stub_app()`, with `authorize` turned off, because they test the contract stubs and the matrix test covers access.
- Mutation checks: membership, role, signed-in and the startup check are all caught (1–64 tests each).
- **Cross-track:** `PERMISSION_DENIED` is a new `problem_codes` entry. The frontend's parity test on `main` requires `PROBLEM_CODES` to equal the catalogue, so the frontend must add it with AR/EN messages when this lands. This goes in the end-of-phase message.
- `uv run pytest -q`: **2121 passed**.
PR **#101** (stacked on #100).

**P5.7, throttling and the audit log** (`app/auth/limits.py`, `app/auth/audit.py`, `tests/integration/test_throttle_audit.py`; 7 failed first).
- **Fixed windows in `rate_limits`, counted with an atomic upsert** (the dialect's `ON CONFLICT DO UPDATE`). Login failures: 5 per 15 minutes per account **and** per IP. Register and forgot-password: 3 per hour per IP. Over the limit gives 429 `RATE_LIMITED` with `Retry-After` (`ProblemError` can carry headers now). While locked, even the right password is refused, and the lock releases when the window ends. Successful logins don't count.
- IPs are kept only as an HMAC (`client_ip`), and so are the sessions' `ip_hash` values.
- **Audit:** `auth.register`, `auth.login`, `auth.login_failed` (no actor for an unknown email), `auth.logout` and `auth.password_reset`. No raw email is stored. Role changes are audited with P5.8.
- The permission-matrix fixture gives each simulated user its own client address.
- **T5.7 and T5.12** pass. Mutation checks: the limit boundary, the per-account count (it survived at first, so a many-addresses test was added), the check itself and the upsert are all caught.
- `uv run pytest -q`: **2137 passed**. No drift.
PR **#102** (stacked on #101).

**P5.8, profile, sessions, workspaces and members** (`app/api/v1/workspaces.py`, `app/api/v1/auth.py`, `tests/integration/test_workspaces_api.py`; 13 failed first).
- `PATCH /auth/me` (display name, locale, theme, and timezone checked against the IANA list, so an unknown zone is 422 `INVALID` at `body.timezone`). `GET /auth/sessions` lists live sessions with `current`. `DELETE /auth/sessions/{id}` revokes your own session (someone else's is 404) and clears the cookies when it is the current one.
- `GET` and `POST /workspaces` (the creator is owner; `workspace.created` is audited). `DELETE /workspaces/{ws}` is owner-only, with 409 `PERSONAL_WORKSPACE_UNDELETABLE` for the personal workspace; its rows cascade.
- `GET members`. `PATCH` and `DELETE members/{user}` (audited as `member.role_changed` and `member.removed`): the owner can't be changed or removed, not even by themselves; managers handle only members ranked below them and never grant above their own role; a non-member target is 404.
- Mutation checks: the owner guard (it survived at first, so a self-demotion test was added), the rank rule and the personal-workspace guard are all caught.
- `uv run pytest -q`: **2143 passed**. No drift.
PR **#103** (stacked on #102).

**P5.9, invitations** (`app/api/v1/workspaces.py`, `tests/integration/test_invitations_api.py`; 10 failed first).
- Invite (members.manage): the email is normalized; the token is 256 bits stored only as SHA‑256; it expires after **7 days**; it is emailed as `{APP_URL}/invite?token=…` (a new `invite` mail kind, AR/EN); `member.invited` is audited. List shows status: pending, accepted, revoked or expired. Revoke is audited.
- Accept (signed in): a dead token (unknown, expired, revoked or used) gives 400 `TOKEN_INVALID`; **a signed-in email that doesn't match gives 403 `PERMISSION_DENIED`**; otherwise the user joins with the invited role (`member.joined`). It works for an existing user, and for a new sign-up after registering with the invited email.
- **S‑29 "no role above the inviter's" holds by structure:** only owners and admins hold members.manage, and `GrantableRole` stops at admin. A test pins both. A runtime check I wrote first was unreachable (a mutant survived), so it was removed.
- **T5.13** passes. Mutation checks: the email binding and the status checks are caught.
- `uv run pytest -q`: **2149 passed**. No drift.
PR **#104** (stacked on #103).

**P5.10, account deletion and export** (`app/auth/privacy.py`, `tests/integration/test_privacy_api.py`; collection failed first).
- `DELETE /auth/me {password}`: a wrong password gives 400 `PASSWORD_INCORRECT`. Otherwise it sets `deleted_at`, **revokes every session**, clears the cookies and returns 202; sign-in is refused from then on. **It is refused with 409 `OWNS_SHARED_WORKSPACE` (new problem code) while the user owns a shared workspace** (decision recorded).
- `purge_deleted(session, now, grace)` removes users whose grace period is over (`DELETION_GRACE_DAYS`, 30), with their workspaces. Audit entries stay, with no actor. The worker schedules it (P8); deleting files from storage comes with Phase 6.
- `POST /auth/me/export` builds a ZIP (profile, memberships, and the personal workspace's workflows and versions, drafts, runs and file records; never hashes or secrets) under `DATA_DIR/exports/<user>/<id>.zip`. `GET` reports `ready` (someone else's is 404). **`url` stays null until Phase 6 storage gives a signed link: an open item for the frontend.**
- **T5.14** passes. Mutation checks: the shared-workspace guard, the session revocation and the workspace filter (both masked at first; the tests were strengthened) are all caught.
- One full run had a single flaky failure, most likely the T5.11 timing check (< 50 ms) under load; the next run was green. Watch it in CI.
- `uv run pytest -q`: **2156 passed**.
PR **#105** (stacked on #104).

**P5.11 part 1, MFA enrollment** (`app/auth/totp.py`, migration `0003`, `tests/unit/test_totp.py`, `tests/integration/test_mfa_api.py`; collection failed first).
- **TOTP is RFC 6238** (SHA‑1, 6 digits, 30 s), written directly with `hmac` and checked against **the 4 RFC appendix B vectors**. It accepts one step either side, and **never a step already used** (`users.mfa_last_step`), so a code can't be replayed.
- The secret is **encrypted at rest with Fernet** (`uv add cryptography`, 50.0.2) under `MFA_KEY`, a production secret (`.env.example`). Development uses a fixed key, so devices keep working across restarts.
- `POST /auth/mfa/enroll` returns the `otpauth://` URI and 10 recovery codes, stored as SHA‑256; MFA stays off until confirmed. `.../confirm` activates it. `DELETE /auth/mfa` needs the password and a current code. The codes are 400 `MFA_CODE_INVALID`, 409 `MFA_ALREADY_ENABLED` and 409 `MFA_NOT_ENABLED`, and `User.mfa_enabled` follows `mfa_enabled_at`.
- **Migration 0003** (`mfa_enabled_at`, `mfa_last_step`) carries the `uq_users_email` guard around the SQLite rebuild, as recorded after 0002.
- Mutation checks: replay, the window and the RFC truncation are all caught.
- The login challenge is the next PR.
- `uv run pytest -q`: **2170 passed**. No drift.
PR **#106** (stacked on #105).

**P5.11 part 2, the MFA login challenge** (7 failed first). **P5.11 is done.**
- With MFA on, login answers `{mfa_required: true}` and sets **only** `replora_mfa_challenge`: HttpOnly, SameSite=Lax, Secure in production, 5 minutes. Its token is random and stored hashed in `auth_tokens` (kind `mfa`), bound to the user. **No session cookies are issued.**
- `POST /auth/mfa/challenge` takes a TOTP code (no replay) or a recovery code (single use). Success uses the challenge up, starts the session, clears the challenge cookie and rotates CSRF. A missing, expired or used challenge gives 401 `MFA_CHALLENGE_INVALID`. A wrong code gives 400 `MFA_CODE_INVALID`, counts toward the **login throttle** (5 per 15 minutes per account and per IP, then 429), and does not use the challenge up.
- `one_time.find` looks a token up without using it.
- **Every §2 auth endpoint is real now**, so the empty 501 stub test is gone.
- Mutation checks: single-use recovery codes, using the challenge up, the throttle and the MFA branch are all caught.
- `uv run pytest -q`: **2176 passed**. No drift.
**End-of-Phase-5 run** (`feat/p5.11-mfa-challenge`):
| Command | Result |
|---|---|
| `uv run ruff check .` · `ruff format --check .` | clean · 144 files formatted |
| `uv run pytest -q` | **2176 passed** (12 skipped on purpose: the shared matrix callers aren't signed out) |
| `export_openapi --check` · `export_schemas --check` | exit 0 · exit 0 |
| `uv run pip-audit` · `pnpm audit --audit-level=high` | clean · clean |
| frontend `gen:api` drift · lint · typecheck · test · build | none · clean · clean · **186 passed** · built (on this stack's base) |
| `gitleaks git .` | no leaks found |

**Gate G5 (backend) passed** (pre-approved, recorded in `decisions.md`). I1 is the frontend's part. **Next: Phase 6 (files).**
## Phase 6 — files

**P6.1, storage** (`app/storage/`, `tests/integration/test_storage.py`; collection failed first).
- `LocalStorage` under `DATA_DIR/storage`: `create_upload_url`, `put`, `open`, `exists`, `size`, `delete` and `signed_download_url`. Keys are `workspace/file` and can't leave the root: `..`, absolute paths, backslashes and empty keys are refused (S‑33).
- `app/storage/signing.py`: base64url claims plus HMAC‑SHA256. Each token is single-purpose (`put` or `get`, one key), expiring after **10 minutes for upload** (with the declared size) and **5 minutes for download** (S‑34, S‑36).
- **Local stand-ins for Supabase signed URLs:** `PUT` and `GET /api/v1/storage/{token}` are **outside the v1 router and the contract** (`include_in_schema=False`; a test checks that they're absent from OpenAPI). The token is the authorization. A PUT larger than declared gives 413 and nothing is stored; downloads are `attachment`, `nosniff`, `no-store`; forged or expired tokens give 403.
- Mutation checks: the MAC check and the op check are caught.
- `uv run pytest -q`: **2205 passed**. No drift.
PR **#108** (stacked on #107).

**P6.2 and P6.3, upload intent and complete** (`app/files/detect.py`, `app/files/service.py`, migration `0004`; both test files failed first).
- **Intent:** a declared size over 50 MiB gives 413 `FILE_TOO_LARGE` (S‑31, the boundary on both sides). Otherwise it creates a `pending` row with key `ws/file_id`, a sanitized display name and an `expires_at` of now + 30 days (D11), and returns a 10-minute signed PUT.
- **Complete:** it reads the stored bytes once. No bytes → `FILE_EMPTY`; size ≠ declared → `FILE_SIZE_MISMATCH`; otherwise the **server's SHA‑256** is stored and the type is detected from the content. Rejected bytes are deleted. A second complete gives 409. `file.uploaded` is audited.
- **Detection (S‑30):** ZIP magic; JSON (else `FILE_CORRUPT`); CSV text in UTF‑8, UTF‑8 BOM or Windows‑1256. Executables, PDF, images, OLE, HTML/XML and text with control characters give `FILE_TYPE_UNSUPPORTED`, whatever the name.
- **Display names (S‑33):** no path, no control or bidi characters (U+202E), Windows reserved names prefixed with `_`, at most 255 characters keeping the extension, and Arabic preserved.
- **Contract (additive, before the G6 freeze):** `DetectedType` gains `json`, which Phase 7 needs (ZIP with CSV and JSON). `openapi.json` and `schema.d.ts` are regenerated.
- **Migration 0004:** `files.rejection_code` and `files.members`. Autogenerate wrote the bare `Text()` again, fixed as in 0001.
- **T6.1, T6.2, T6.3 and T6.8** pass. Mutation checks: the size check and the delete of rejected bytes (masked at first) are caught.
- `uv run pytest -q`: **2245 passed**.
PR **#109** (stacked on #108).

**P6.4, ZIP safety** (`app/files/zip_safety.py`, `tests/unit/test_zip_safety.py`; collection failed first).
- Member by member, counting **real** bytes while streaming (headers are never trusted). It stops at a ratio over 100:1 per member (`ZIP_RATIO_EXCEEDED`) or over 200 MiB in total (`ZIP_TOO_LARGE`).
- Before reading: unsafe paths (`..`, absolute, drive letters, backslashes) → `ZIP_UNSAFE_PATH`; symlinks → `ZIP_SYMLINK`; the encryption flag → `ZIP_ENCRYPTED`; more than 25 files → `ZIP_TOO_MANY_MEMBERS`. Each member is detected from its content: a nested ZIP → `ZIP_NESTED`; not CSV or JSON → `ZIP_MEMBER_UNSUPPORTED`. A damaged archive → `FILE_CORRUPT`.
- `complete` stores the `members` of a ready ZIP.
- **T6.4:** a 100 MiB zero bomb is rejected in under 0.5 s. **T6.5** and **T6.6** pass. Mutation checks: the ratio, `..` and nesting checks are caught.
- `uv run pytest -q`: **2263 passed**. No drift.
PR **#110** (stacked on #109).

**P6.5, file endpoints and samples** (8 new tests; 7 failed first).
- List: newest first, `limit`, an opaque `next_cursor` (a file id from this workspace; anything else is 422), and `?type=` filtering. Download: `ready` files only (otherwise 409); a **5-minute signed URL** with `attachment` and the display name, audited as `file.downloaded`. Delete: the row and the bytes, audited as `file.deleted`. A cross-workspace id is 404.
- **Samples:** `app/files/samples/` holds the Phase 7 acceptance files, `orders.csv` (O‑101, O‑102, O‑103) and `payments.json` (O‑101, O‑102 with another amount, O‑104). They go through the same `complete`.
- `repos.page_query` pages an already-scoped, filtered query.
- **All §4 file endpoints are real now**, so the empty 501 stub test is gone. **T6.7** passes.
- **The flaky test:** T5.11's timing check is now the median of 5 requests per kind, each from its own address. That was the single intermittent failure seen in two full runs.
- Mutation checks: deleting the bytes, the ready-only download and the cursor are caught.
- `uv run pytest -q`: **2267 passed**. No drift.
PR **#111** (stacked on #110).

**P6.6 and P6.7, retention and quotas**, plus the rest of S‑29.
- `purge_expired` deletes files past `expires_at` (30 days, D11) from storage **and** the database (T6.9). It is the one function the S‑14 lint allows to cross workspaces (`SYSTEM_JOBS`, named on purpose). The worker schedules it (P8).
- **Quota:** stored and pending bytes per workspace, plus the new file, must stay within `WORKSPACE_QUOTA_BYTES` (2 GiB); otherwise upload intent gives 413 `QUOTA_EXCEEDED`. Rejected files don't count. `check_files_per_run` gives 413 above 10 files; the runs endpoint calls it in P8 (T6.10).
- **S‑29:** `purge_deleted` also deletes the personal workspace's file bytes. **Exports now live in storage, and `GET /auth/me/export/{id}` returns a 5-minute signed `url`**, which closes that open item.
- Mutation checks: the quota, deleting the bytes on expiry and on account purge, and excluding rejected files (masked at first, then tested) are all caught.

**End-of-Phase-6 run** (`feat/p6.6-retention-quotas`): ruff and format clean; **2271 passed**; no drift in `openapi.json` or the schemas; pip-audit clean; frontend `gen:api` no drift, typecheck, lint, **186 tests** and build OK; `pnpm audit` clean; gitleaks no leaks.

**Gate G6 (backend) passed** (pre-approved, recorded in `decisions.md`). I2 is the frontend's part. **Next: Phase 7.**
PR **#112** (stacked on #111). Phase 6 summary sent to the frontend (#1, 7210626804).

## Phase 7 — the first real pipeline

**P7.1, the adapters** (`app/ops/table.py`, `csv_adapter.py`, `json_adapter.py`, `zip_adapter.py`; both test files failed first).
- **`Table`:** columns, rows of text (read as numbers or dates only by `normalize`), and per-row lineage (`file`, `member`, `row`). It travels on the engine's ports as canonical JSON.
- **CSV:** a BOM decides (UTF‑8 or UTF‑16), else UTF‑8, else Windows‑1256. The delimiter is sniffed among `,` `;` and tab. Quoted newlines are kept and headers are trimmed. **Ragged rows are padded or cut and reported** (`CSV_ROW_RAGGED` with the rows). Empty → `CSV_EMPTY`, duplicate headers → `CSV_DUPLICATE_HEADER`; header-only is an empty table.
- **JSON:** an array of objects. Nested objects become dotted columns, lists stay JSON text, and number text is kept exactly. **Mixed key sets become the union and are reported** (`JSON_KEYS_MIXED`). Not an array, empty, duplicate key and depth over 10 each fail with a code.
- **ZIP:** `extract_member(path)` adds `member` to the lineage; a missing member gives `ZIP_MEMBER_MISSING` with the paths found.
- **T7.5 and T7.7** pass. `uv run pytest -q`: **2297 passed**.
PR **#113** (stacked on #112). (The P7.1 entry's count was wrong: the full run then was **2312 passed**.)

**P7.2 part 1, normalize and compare** (`app/ops/numbers.py`, `dates.py`, `normalize.py`, `compare.py`; collection failed first).
- **Numbers (P7.5):** `Decimal` only. `1,234.50` and `1.234,50` (the last mark is the decimal); `12,5`; Arabic-Indic and Persian digits and the Arabic separators; `(100)` is negative; empty and `NaN` are missing; anything else is `ValueError`. `0.1 + 0.2 == 0.3`.
- **Dates (P7.5):** ISO, or day/month/year with the order **proven by the column** (a first part over 12 means DMY, a second over 12 means MDY). An all-ambiguous column returns the choice `["DMY", "MDY"]` instead of guessing; `date_orders` answers it.
- **`normalize`:** key trim and case; number and date columns; it reports `NUMBER_INVALID` (with rows), `DATE_AMBIGUOUS` (with options) and `DATE_INVALID`; an absent column gives `COLUMN_MISSING`.
- **`compare`:** key and value with a Decimal `tolerance` (exact by default). Outcomes: matched, value_diff, missing_right, missing_left, with the difference and both rows' lineage. **A key duplicated on either side lists every occurrence as `duplicate_key`** and gives the `KEY_DUPLICATED` warning (T7.9). The summary has the four contract counts.
- **T7.6, T7.9, T7.10 and T7.11** pass. Mutation checks: both sides' duplicates (the right side survived at first and is now tested), the tolerance boundary, the ambiguity, the decimal mark and the sign are all caught.
- `uv run pytest -q`: **2356 passed**.
PR **#114** (stacked on #113).

**P7.2 part 2 and P7.3, the outputs** (`app/ops/outputs.py`, `tests/unit/test_outputs.py`).
- `report_csv`: key, status, both values, the difference, then **each side's file, member and row, plus the operations each row went through**. UTF‑8 **with a BOM** by default, plain UTF‑8 as an option, Arabic kept. `summary_json` is sorted with no timestamps. `bundle_zip` uses fixed ZIP dates, so it is **byte-identical** every time. `map_columns` renames, refusing a missing or clashing name.
- **S‑37:** `escape_cell` prefixes `'` to cells starting with `= + - @`, tab or CR, **except plain numbers** (`-10`). The `decisions.md` row gives the reason.
- **T7.8 and T7.12** pass (the Excel check is manual and is logged with the acceptance run). Mutation checks: the number exception, tab and CR, and the default BOM are caught.
- **P7.2 and P7.3 are done.** `uv run pytest -q`: **2372 passed**.
PR **#115** (stacked on #114).

**P7.2 part 3, the operation registry** (`app/ops/registry.py`, `app/ops/codes.py`; collection failed first).
- **11 operations, v1:** `extract_member`, `parse_csv`, `parse_json`, `normalize`, `map_columns`, `compare`, `report_csv`, `summary_json`, `bundle_zip`, `append_rows` and `export_csv`. The **TemplatePlanner's ids are all there**. Params fit the form subset (lists and enums; `map_columns` takes `source` and `target` lists; `normalize` takes one `date_order`).
- `Data.source` carries `file` and `member`. Every handler adds `op@1` to each row's lineage `ops` (P7.4).
- **Schema drift:** a column missing in `normalize` gives a `SCHEMA_DRIFT` warning (with `available`) and the table unchanged, so the review policy stops the run as NEEDS_REVIEW (T7.4).
- **New `contracts/error-codes.json` → `operation_codes`** (18). A test scans `app/ops` for every `OperationError` and `Issue` code and requires each to be in the enum, and the enum to equal the catalogue section.
- `uv run pytest -q`: **2382 passed**. No drift.
**Earlier pause:****Session paused here (usage limit).** Phase 4 left: **T4.7 (rest)/T4.8** (job claim, never twice: a conditional UPDATE, plus SKIP LOCKED on Postgres) and **P4.7** (Postgres 17 CI job, with the DB tests parametrized on `TEST_POSTGRES_URL`). Then G4 (pre-approved once verified), then Phase 5.

## Session 15, part 2 — 2026-11-26: Phase 1 starts (P1.1)
**Goal:** P1.1, the domain models `ArtifactType`, `ArtifactRef`, `Port` and `OperationContract`.

**Design:** `app/core/` is now the single source of these types (plan §3: pure, no I/O):
- `model.py`: `ContractModel` (`extra="forbid"`, `frozen=True`; P1.7 for these models).
- `artifact_type.py`: `ArtifactType` (11 kinds). It's its own module so that `artifacts` and `operations` don't import each other.
- `operations.py`: `Port`, `OperationContract` and `OperationRef`.
- `artifacts.py`:
  - `ArtifactRef` = `id`, `type`, `format` (`^[a-z0-9]{1,16}$`), `sha256` (64 lowercase hex), `workspace_id` (the owner scope) and `lineage`.
  - `ArtifactLineage`: an upload has no run, node, operation or parents. A produced artifact has `run_id`, `node_id` and `operation` together, plus its `parents`.
- The API modules (`operation_models.py`, `output_models.py`) now re-export these classes and keep the same names and docstrings. So **`openapi.json` is unchanged**: the drift check exits 0, and the frontend's types are untouched. `OperationRef` moved from `output_models.py` to core.

**TDD:** `tests/unit/test_core_contracts.py` was red first (collection error, no `app.core`), then **22 passed**. It covers the 11 kinds, round-trips (dict and JSON), extra fields rejected, frozen, the `sha256` and `format` patterns, the lineage rules, an unknown artifact type rejected, and the API reusing the core classes.

| Check | Result |
|---|---|
| `uv run ruff check .` · `ruff format --check .` | clean · 49 files formatted |
| `uv run pytest -q` | **424 passed** |
| `uv run python -m app.export_openapi --check` | exit 0, no drift |

**P1.1 ticked.** T1.1 and T1.2 are covered for these models, but stay open until P1.2–P1.5 add theirs.

**Backend review of the frontend's #53** (MSW auth handlers, `910d053`, comment 7190985110). Nothing blocking:
- A script compared the PR's `ENDPOINTS` table with `openapi.json`: 19/19 `auth_*` operations match on method and path (only the path parameter names differ). All 19 fixtures have `ok`, and every case is `{status, body}`.
- Non-blocking points:
  1. errors are mocked as `application/json`, not `application/problem+json`;
  2. there's no `Retry-After` on 429 and no `X-Request-ID`;
  3. a typo in a scenario name gives an unclear 500.
- Idea: a parity test of fixtures ↔ `ENDPOINTS` ↔ `openapi.json`.

**P1.2 follow-up, IO labels** (branch `feat/p1.2-io-labels`, after #56 merged as `30b1025`, option (a) chosen by Developer A):
- The frontend asked on #56 (7191619340) for an optional display `label` on `InputContract` and `OutputContract`, for Arabic slot and result names.
- Added `label: Label | None` (free Unicode, at most 100 characters; `Label` is shared with `Node.label`).
- TDD: 3 red, then green. The first version of the length test passed for the wrong reason (an unknown `label` is `extra_forbidden`, and that message also contains "label"), so it now matches "at most 100 characters".
- Checks: ruff clean, **456 passed**, no drift.
- #55 (`LICENSE`, `3600675`) and #56 (`30b1025`) were merged on Developer A's go. #57 was rebased onto `main` (`--onto origin/main a8fd013`, range-diff `=`, 473 passed, no drift) as `25585dc`.

**#52 merged** (`8cf1c1b`, P1.1) on Developer A's go. **Backend review of the frontend's #54** (Toast, `799fd09`, 7191428081). Nothing blocking:
- the installed `sonner` container `<section>` is already `aria-live="polite"`, so the `role="status"`/`role="alert"` inside it is a nested live region, which some screen readers announce twice;
- error toasts could show the API's `correlation_id`.

**P1.2: `app/core/workflow.py`** (branch `feat/p1.2-workflow-definition`):
- `PortRef(node_id, port)`, `Node(id, operation: OperationRef, params: dict[str, JsonValue], label?)` and `Edge(source, target)`.
- `InputContract(name, artifact_type, columns, targets)`: the expected columns feed replay drift (P13.2).
- `OutputContract(name, artifact_type, source)`.
- `ResourcePolicy`: defaults and maximums are 10 files, 50 MiB per file, 120 s per node and 900 s per run (D8, P19.3).
- `ReviewPolicy(on_warning: continue | review)`, default `review`.
- `WorkflowDefinition(workflow_id?, workflow_version?, schema_version: 1, nodes, edges, inputs, outputs, resource_policy, review_policy)`. A draft has neither ID nor version; a saved version has both.
- Names (node IDs, ports, IO names) match `^[A-Za-z0-9_-]{1,64}$`. A label is free Unicode, up to 100 characters.
- **Shapes only.** Unique IDs, known ports, no cycles and the limits belong to the P2 validator, which returns a report. So an empty workflow is a valid shape.
- **The API's `WorkflowDefinition` placeholder (an object) is not replaced yet.** That changes `openapi.json` and the frontend's types, so it goes with the JSON Schema export in P1.6, as the placeholder's docstring says. The drift check passes.
- **TDD:** `test_core_workflow.py` was red first (no module), then 29 passed. Checks: ruff clean (51 files), **453 passed**, no drift.
- Opened as **#56**.

**P1.3: `app/core/validation.py` and `app/core/draft.py`** (branch `feat/p1.3-draft-validation-report`, stacked on #56):
- **`Issue`, `ValidationReport` and `Explanation` moved from `draft_models.py` to core**, with the same fields, docstrings and descriptions. `draft_models.py` re-exports them, and `run_models.py` still imports `Issue` through it.
- Two new rules, both model validators, so the JSON schema is unchanged:
  - `ValidationReport.valid` is true exactly when there are no errors;
  - `Explanation` is either a `key` (with optional `params`) or a `text`.
- **New `WorkflowDraft(definition, explanation, warnings=[])`**: what a planner returns. It's never trusted, because the validator re-checks it (P12.3).
- **TDD:** `test_core_draft.py` was red first (no module), then 20 passed. Checks: ruff clean (54 files), **473 passed**, no drift.

**Merges (Developer A's go, each with the frontend's approval on its final head and CI 4/4):** #56 P1.2 (`30b1025`), #57 P1.3 (`458c23b`, rebased on `main`) and #59 IO labels (`6190e52`). The combined `main` gives **476 passed**, no drift. Also merged: the frontend's #54. **Developer A approved the frontend's #58** at `2276713`. Its new commit (a non-JSON error falls back to `INTERNAL_ERROR`, with 3 tests) was read before approving.

**P1.4: `app/core/plan_hash.py`** (branch `feat/p1.4-plan-hash`):
- `canonical_json(value)` is `json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)` in UTF-8.
- **Numbers are normalized:** an integral float within ±(2^53 − 1) is written as an int, so `2.0 → 2` and `-0.0 → 0`. JSON, and so the browser, can't tell those apart. Other floats keep their shortest round-trip form (`0.1`, `1e+300`). NaN and ±inf raise `ValueError`.
- `plan_hash(definition)` = lowercase hex SHA-256 of `canonical_json(definition.model_dump(mode="json"))`. The whole definition counts, including the workflow version and the policies.
- Strings are hashed as given, with no Unicode normalization (two different column names must never collide). List order counts.
- **New dev dependency `hypothesis` 6.170.17** (MPL-2.0, released 2026-11-20, pip-audit clean), with `uv add --dev hypothesis`.
- **Tests** (`test_plan_hash.py`, 15):
  - a **golden hash** for a fixed definition with an Arabic label and `2.0`. Its canonical bytes were checked by eye, and `sha256sum` on those bytes gave the same `0edcdef6…08e0`;
  - the canonical form, number normalization, and NaN/inf rejected;
  - **T1.3** (hypothesis): random key order plus indented JSON gives the same hash;
  - **T1.4** (hypothesis): adding or changing a node param, adding an edge, or bumping an operation version or the workflow version changes the hash.
- **The tests bite:** with `sort_keys=False`, 3 fail. With number normalization off, 4 fail. Restored, 15 pass.
- ruff caught `Random(seed)` (S311), so the test uses hypothesis `st.randoms()`.
- Checks: ruff clean (56 files), **491 passed**, no drift.
- **P1.4, T1.3 and T1.4 ticked.** S‑11 stays open, because it also needs T3.1 (the approver ID and time).
- Opened as **#60** (`7285ddb`), CI 4/4 green, waiting on the frontend's review.

**End of Session 15 (this machine):**
- **The frontend's #58** moved to `75528d1`. Its new commit was re-reviewed (7192378154): status-matched fallback codes (413 `FILE_TOO_LARGE`, 429 `RATE_LIMITED`, else `INTERNAL_ERROR`), `X-CSRF-Token` same-origin only, and an idempotency reset on body change. The `CSRF_FAILED` retry moves to their refresh PR. **Claude's re-approval was blocked by the permission check**, so Developer A approves it.
- **Status sent to the frontend:** #1, 7192378739.
- **Claude memory:** 4 notes (`commit-msg-no-bom`, `check-reviews-before-push`, `merge-rules`, `powershell-gotchas`). **Handover for the other machine:** `D:\Projects\replora_handover.md`, outside the repo. It holds the memory notes, the commands to reach this state, and the expected check results.
- **State:** `main` `6190e52` (476 passed); `feat/p1.4-plan-hash` (#60) 491 passed; no drift.

## Session 15 — 2026-11-26 (`D:\Projects\replora`, after Session 14 on the other machine)
**Goal:** check that this machine matches Session 14, answer the frontend, and finalize P0.5 and P0.8.

**Alignment:**
- `docs/session-14-final` was `6c20595`, the same as `origin`. Every open PR head matched the log: #40 `6dcabef`, #41 `d138c28`, #42 `ceedd01`, #44 `8052294`, #45 `a73b4e2`. `main` was `ef49ab3` with CI green.
- `pnpm install --frozen-lockfile` and `uv sync --locked` passed, and ruff was clean.
- On this branch (based on `308f2f9`, one before #34): **254 passed**, no drift. On `origin/main` in a scratch worktree: **281 passed**, no drift.

**New from the frontend (#1, 7185139284, 7185394516, 7185622268):**
- The repo is public (a gitleaks full-history scan found 0 leaks), and the ruleset is live.
- **Approved:** #44, #45 and #40, with two non-blocking questions on #40.
- **Changes requested on #41** (row number and status per preview row, ints above 2^53) **and on #42** (mapping per input).
- They asked us to correct "#34 merged by the owner". Developer A confirmed it was their own go, so the wording now names Developer A.

**Answered on #1 (7186123958):** all of the above, as decided by Developer A (see Next step 1–3). `created_by` stays a UUID, and the UI resolves the name from the members endpoint.

**P0.8 and S‑05 ticked.** Evidence from `gh api repos/kzazzco2009-hub/replora/rules/branches/main`:
- `deletion` and `non_fast_forward`;
- `pull_request`: `required_approving_review_count: 1`, `dismiss_stale_reviews_on_push: true`, `allowed_merge_methods: [squash]`;
- `required_status_checks`: `Secret scan (gitleaks)`, `Backend (lint, test, audit)` and `Frontend (lint, typecheck, test, audit)`.

`gh api repos/kzazzco2009-hub/replora` gives `allow_merge_commit: false` and `allow_rebase_merge: false`. Fork-PR approval (403) and secret scanning (field empty) need admin rights, so they're on the frontend's word until they confirm them in the UI.

**#41 change (`7790f9e`, a new commit so the delta is easy to review):**
- `Preview.rows` is `PreviewRow[]` = `{row ≥ 0, status: ReconcileStatus | null, cells}`. `status` is null outside a reconciliation, which the frontend's proposal didn't cover.
- An `integer` cell is limited to ±(2^53 − 1) in the type, so it shows as `minimum`/`maximum` in `openapi.json`.
- TDD: 2 red, then **327 passed**. Ruff, drift, `tsc` and prettier clean, CI green. Commented on #41 (7186468639).

**#42 rebase and change:**
- `git rebase --onto 7790f9e d138c28` was clean. Regenerating changed nothing, and range-diff shows `=` (`7dbec8e`), with 350 passed.
- Then `f125e7c`: `mapping: dict[str, dict[str, str]]` (`{input: {expected: found}}`). The docstring says an input left out keeps its columns and an unknown one is a 422. The §7 and §8 stub notes in `api_contract.md` are updated.
- TDD: 4 red, then **352 passed**. All checks clean, CI green. Pushed with `--force-with-lease`. Commented on #42 (7186470568).
- The work was done in a scratch worktree, so the uncommitted `plan.md` line in the main clone wasn't touched.

**Backend review of the frontend PRs.** All read in full, with CI green. Developer A approved **#39** (`a7faeb2`), **#46** (`c736a34`), **#47** (`bca2816`) and **#48** (`628949b`). There were no blocking points. The non-blocking points were posted as PR comments:
- **#46** (7187753894): the active state is an exact match, so nested routes are never highlighted; the "More" `<details>` stays open after navigation; safe-area inset; use the next-intl `Link`; `lucide` icons; a route group to keep the auth pages without the shell.
- **#47** (7187754869): a signed-in locale or theme switch must also `PATCH /auth/me`, because `User.locale` drives the emails; the query string is dropped on switch (the #41 preview filters); full language names as accessible names.
- **#48** (7187755689): a caller's `aria-describedby` overrides the error link; `duration-*` without `transition-*`; merging `className`.

**G0 readiness check on `main` `f07e323`** (detached in the main clone, the tree clean before and after; `pnpm install --frozen-lockfile` and `uv sync --locked`):

| Check | Command | Result |
|---|---|---|
| Backend lint | `uv run ruff check .` · `ruff format --check .` | clean · 40 files formatted |
| Backend tests | `uv run pytest -q` | **377 passed** |
| Contract drift | `uv run python -m app.export_openapi --check` | exit 0 |
| Backend audit | `uv run pip-audit` | no known vulnerabilities |
| Frontend | `pnpm -C frontend lint` · `typecheck` · `format:check` | all exit 0 |
| Frontend tests | `pnpm -C frontend test` | **14 files, 123 passed** |
| Frontend build | `pnpm -C frontend build` | exit 0 |
| Frontend audit | `pnpm audit --audit-level=high` | no known vulnerabilities |
| Secrets | `gitleaks git .` | no leaks |
| **T0.4, re-proven** | one byte appended to `openapi.json`, then `--check` | exit 1 "is out of date", restored |
| **T0.5, re-proven** | a fake `sk-or-v1-<64 hex>` in an empty temp dir, `gitleaks dir --config .gitleaks.toml` | `leaks found: 1` (`openrouter-api-key`), exit 1, probe removed |
| **T0.3 lint gate, re-proven locally** | a probe file with `className="ml-2"`, then `eslint` | `local/no-physical-direction` error, exit 1, probe removed |

**G0 gate report (posted on #1, 7189613742, with the G0 request to both developers; PR #50 opened, stacked on #43):**

| Item | State | Evidence |
|---|---|---|
| P0.1–P0.4, P0.6, P0.7, P0.9–P0.11 | ✅ | #2, #6, #14, #19, #25, #26 and the earlier sessions |
| P0.5 contract and types | ✅ | §2 #8 · §3 #10, #27 · §4 #11, #32 · §5 #28 · §6 #34 · §7 #40, #41 · §8 #42 · `gen:api` on `main` `8e8b24b` (402 passed, no drift). `openapi-fetch` → P9.6 |
| P0.8 governance | ✅ | ruleset `main` live (Session 15), CODEOWNERS, PR template |
| Tests T0.1–T0.7 | ✅ 7/7 | T0.3–T0.5 re-proven above |
| Security S‑01–S‑05 | ✅ 5/5 | `security.md` Phase 0; S‑05 Session 15 |
| api_contract.md draft | ✅ | agreed on #1; §2–§8 stubbed in `openapi.json`; §2 fixtures #44 |
| Frontend F0 | ✅ steps | P0.4, P0.5 (types) and T0.2 are ticked in `docs/frontend/plan.md`. Their F0 gate line (line 107) is theirs to tick |
| Open owner items | — | `LICENSE` (both); confirming fork-PR approval and secret scanning in Settings (frontend) |

The G0 decision needs **both developers**. No Phase 1 work starts before it.

**Housekeeping:** 11 merged local branches deleted after checking them:
- 8 had tips equal to their PR's final head;
- `feat/p0.5-workspace-codes` was #27 before its rebase (range-diff `=` in Session 14);
- `feat/p0.5-file-stubs` held an old log line that `main` supersedes;
- `backend/setup` held only the initial commit, already in `main`.

`feat/p0.5-workflows-stubs` (#42, now merged) was kept. The merged remote branches #40, #41, #42, #44 and #45 are for Developer A to delete (Claude can't).

**P0.5 ticked** (`plan.md` and `backend_plan.md`) after #42 merged. The evidence is on `main` `8e8b24b`, in a scratch worktree (`pnpm install --frozen-lockfile`, `uv sync --locked`):

| Check | Command | Result |
|---|---|---|
| Lint | `uv run ruff check .` | all checks passed |
| Backend tests | `uv run pytest -q` | **402 passed** |
| Contract drift | `uv run python -m app.export_openapi --check` | exit 0 |
| TS types | `pnpm -C frontend gen:api`, then `git status --porcelain frontend/src/lib/api` | no diff |
| Frontend | `pnpm -C frontend typecheck` · `test` | exit 0 · **21 files, 147 passed** |

§2–§8 are all stubbed (#8, #10, #11, #27, #28, #32, #34, #40, #41, #42). `openapi-fetch` is P9.6 in the frontend's plan. Earlier note: P0.5 waited on #41/#42 and on `openapi-fetch`, which isn't in `frontend/package.json` (only `openapi-typescript`).

**T0 and S‑01…S‑05 re-run on `main` `8e8b24b`** (scratch worktree, `--frozen-lockfile` and `--locked`, Developer A asked):

| Item | Command | Result |
|---|---|---|
| T0.1 | `uv run pytest -q tests/unit/test_health.py` | 1 passed |
| T0.2 | `pnpm -C frontend test home` · `pnpm -C frontend build` | 3 passed · exit 0 |
| T0.3 | a probe `import os` with `ruff check`, a probe `className="ml-2"` with `eslint`; CI on `main` `8e8b24b` | exit 1 (F401), exit 1 (`local/no-physical-direction`); CI success |
| T0.4 | one byte appended to `openapi.json`, then `export_openapi --check` | exit 1 "is out of date", then restored with exit 0 |
| T0.5 | a fake `sk-or-v1-…` staged, then `pre-commit run gitleaks` | **Failed**, `RuleID: openrouter-api-key`, exit 1 |
| T0.6 | `git check-ignore -v .env` | `.gitignore:2:.env` |
| T0.7 | `uv run pytest -q tests/unit/test_observability.py` | 19 passed |
| All backend tests | `uv run pytest -q` | 402 passed |
| S‑01 | T0.5, T0.6; `git ls-files` shows only `.env.example`; `gitleaks git .` | no leaks |
| S‑02 | `pytest tests/unit/test_config.py`; `APP_ENV=production` without the key / with `DEBUG=true` / clean | 10 passed; "production needs: openrouter_api_key" / "debug must be off in production" / builds |
| S‑03 | lockfiles tracked; CI `uv sync --locked`, `pnpm install --frozen-lockfile` (ci.yml:63, 83) | both pass locally |
| S‑04 | `uv run pip-audit` · `pnpm audit --audit-level=high` · `dependabot.yml` | no known vulnerabilities · none · uv, npm and actions weekly |
| S‑05 | `gh api …/rules/branches/main` · repo settings · `CODEOWNERS` | deletion, non_fast_forward, PR + 1 approval with stale-review dismissal, 3 required checks, squash only · public, no merge or rebase merges · owners per path |

**Found:** the gitleaks pre-commit hook **was not installed in this clone** (`.git/hooks/pre-commit` missing), so a probe commit with the fake key went through. It landed only on the detached scratch worktree, was reset, and was never pushed. The hook config works (T0.5 above), and CI still scans the full history. Fix, per clone, on both machines: `pre-commit install` (`.pre-commit-config.yaml` line 1).

**Stray `plan.md` line:** an uncommitted blank line at the end of `docs/plan.md` was there on arrival. Developer A said to drop it (`git restore docs/plan.md`).

**G0 closing:**
- The frontend approved #43 at `e6b26fc`, and it was merged as `ff55103` on Developer A's go.
- #50 was retargeted to `main` and rebased with `--onto origin/main origin/docs/session-14-final`. Range-diff shows `=` for all 6 commits, and the `+`/`-` lines are identical. The frontend approved `353a1d7`, CI was green on 4/4, and it was merged as `3932c3a` on Developer A's go.
- **G0 approvals:** Developer A (7189738362) and Developer B (7190193580), both conditional on #43 and #50. Recorded in `decisions.md`. `plan.md:190` and `backend_plan.md:44` are ticked, and the tracker shows ☑.
- **The pre-commit hook is now installed in both clones:** the frontend's (7190303587) and Developer A's on this machine (`Test-Path .git/hooks/pre-commit` is True). Developer A's other machine is still to do.
- Developer A's git email is now `143901646+khaledhagar@users.noreply.github.com`. Developer A approved #47 (`708cbb9`, since merged as `5ca29b2`) and #49 (`b3ab133`), and deleted `docs/session-14-final`.

**End-of-session state check:**
- `origin/main` = `6f7eb5f`. The frontend's #39, #46 and #48 merged after `f07e323`. `git diff --name-only f07e323 origin/main` shows only `frontend/`, `docs/frontend/` and `pnpm-lock.yaml`.
- #42 `84f588b`: mergeable, 4/4 checks green. The frontend approved it at 08:22, and the approval was dismissed at 08:43 by the rebase push.
- The ruleset has `strict_required_status_checks_policy: false`, so #42 doesn't need a rebase onto `6f7eb5f`.
- #47 is now `708cbb9`, and Developer A's approval on `bca2816` was dismissed. #49 is new (`2617c7d`) and has no review.
- The stale "Current status" cells (they still showed `ef49ab3` and listed merged PRs as open) are rewritten.
- **#42 merged at 12:21** (`8e8b24b`, Developer A).
- The BOM in the subject of `8079955` was removed by `--amend` and `--force-with-lease`, giving `78780e6` (same tree, no approvals dismissed). Developer A approved this. A detached commit, `006bf69`, was dropped and never pushed: it was a log edit read as ANSI from `main`'s old log, which gave mojibake.

**Backend reviews (posted as PR comments; Developer A posts the approvals):**
- **#47** `708cbb9` (7189297790): the `+`/`-` lines of `git diff c736a34 bca2816` and `git diff origin/main...708cbb9` are identical, and CI is green. Nothing blocking. Two notes from the first review are re-raised (query string dropped on switch, `aria-label` with the full language name).
- **#49** `2617c7d` (7189299199):
  - Proven from the `@radix-ui/react-presence` source (it waits only on `animationName`/`animationend`): the Sheet's `transition-transform` slide never runs. Suggested keyframe animations.
  - The `rtl` test cases render in a portal outside the `<div dir>`, so they don't test RTL.
  - Checked and fine: `aria-describedby={undefined}` is taken out before the props spread, so the description link stays.

## Session 14 — 2026-11-25 (first machine, after Session 13 on the other one)
**Goal:** align this machine with the other machine, rebase #27, answer the frontend, then continue Phase 0 (P0.5 part 4, S‑02).

**Alignment:**
- On arrival, `feat/p0.5-file-stubs` was 10 commits ahead and 38 behind `origin`, and `main` was 23 behind. This was the Session 12 state; Session 13 had rebased and merged the branches.
- **Checked that nothing was only local:** `git cherry` showed all 10 as "+" (squash-merged or rebased, so the patch IDs differ). Then a content diff of `HEAD` against `origin/main` over `backend/` and `contracts/`: `main` held every local change in its later, reviewed form.
- Fast-forwarded `main` to `f463fea`. `pnpm install --frozen-lockfile` and `uv sync --locked` passed. `ruff` clean, **244 passed**, and both drift checks clean.
- **Deleted 5 merged local branches** (owner's go): `feat/p0.5-auth-stubs` (#8), `feat/p0.5-openapi-export` (#6), `feat/p0.5-workspace-stubs` (#10), `feat/p0.5-file-stubs` (#11) and `docs/original-plan` (#7). `-D` was needed because squash merges aren't ancestors; each PR's `MERGED` state was checked first.

**#27 rebase:** `git rebase origin/main` applied with no conflicts. Regenerating both files gave no diff, so nothing new was committed. `git range-diff 8b756a8..5754260 origin/main..cc0e01c`: identical patches, apart from one hunk-header context line. **247 passed**, no drift, no leaks. Pushed `cc0e01c` with `--force-with-lease`.

**Frontend review of #31** (root `pnpm-workspace.yaml`, `allowBuilds` denying `@parcel/watcher` and `@swc/core`):
- In a scratch worktree, #30 alone (`81c071d`): `pnpm install --frozen-lockfile` exits 1, `Ignored build scripts: @parcel/watcher@2.6.0, @swc/core@1.16.22`.
- With #31's file: exit 0, and `pnpm -C frontend build` passes.
- I couldn't post the approval: the permission check blocks `gh pr review --approve`. The #1 comment 7169288460 had already called it approved; this was corrected in 7169675538.
- **The owner approved and squash-merged #31** (`a536353`). The first merge attempt didn't take: the PR stayed `OPEN` with `mergeStateStatus: CLEAN`, so the merge was run again. CI on `main` at `a536353`: all jobs green (run 45679116372). Told the frontend on #30 (7171493813).

**Replies posted:** on #27 (7169287531) and #1 (7169288460). The #1 comment covers the rebase, the repo-public request, the 4 open #25 questions, #28's questions (taken as accepted unless they object), and the `rejection_code` plan.

**#32 `File.rejection_code` values** (`8909c07`):
- 12 codes in a new `rejection_codes` section, from T6.1, T6.4–T6.6, T6.8 and S‑32.
- `RejectionCode` is a `Literal`, and a test keeps the JSON section and the `Literal` identical.
- TDD: red first (`ImportError`, then 2 failures for the missing section). **245 passed.**

**#33 S‑02** (`6405b69`):
- With `APP_ENV=production`, `Settings` refuses a missing `PRODUCTION_SECRETS` entry (`openrouter_api_key`) or `DEBUG=true`. A new `debug` setting is passed to `FastAPI(debug=)`.
- **Root cause found while proving it:** `uvicorn --factory` first *started* in production. This machine's `.env` sets `OPENROUTER_API_KEY` (checked by key name only), so that was correct behavior. With `DEBUG=true` it refused, but pydantic printed `input_value={'openrouter_api_key': 's...`, echoing the raw secret input.
- **Fix:** `hide_input_in_errors=True`. The test now asserts that no `input_value` and no key prefix appear; it was red before the fix.
- **248 passed.** The startup refusal is proven: exit 1, `Value error, debug must be off in production [type=value_error]`.
- A stray uvicorn from the first attempt (port 8765) was stopped.

**#34 §6 drafts stubs** (`b52afbe`):
- `GET /templates` (public, 1 h cache) and drafts `POST`, `GET`, `PATCH`, each with `ETag`. `PATCH` takes `If-Match` and documents 412 and 428.
- `DraftCreate` limits: 1–10 `file_ids`, `prompt` ≤ 4,000, `planner` `template | ai`.
- New codes `PRECONDITION_FAILED`, `PRECONDITION_REQUIRED`, `TOO_SHORT` and `TOO_LONG`.
- TDD: 27 red first. One of my own test bugs: `dict.items() <=` fails with dict values; I now compare `(in, name)` pairs. FastAPI names the header `if-match` by default, so I set `alias="If-Match"`. `test_workspace_stubs` now excludes `/drafts`.
- **271 passed**, `tsc --noEmit` clean, no drift.

**#35 P0.8 ruleset as code** (`f91f774`):
- This account is `push`, not admin (`gh api repos/... .permissions`), and the private repo's rulesets API returns 403 "Upgrade to GitHub Pro or make this repository public". So the protection is prepared as `.github/rulesets/main.json`, with apply and verify steps for the admin.
- `require_code_owner_review` is off: the single-owner `/backend/` and `/frontend/` paths would self-block.
- `test_repo_rules.py` checks that the required checks equal the CI job names. I mutated one check name and the test failed. The restore needed a manual edit, because `git checkout` can't restore an untracked file. **246 passed.**
- Posted on #1 (7171185834).

**Decisions (proposed, waiting on the frontend):** the ruleset as above;
`rejection_codes` as a third section; `Template.required_inputs = [{title_key, artifact_type}]`; `ETag` on the `POST` 201; `If-Match` optional in the schema, with 428 when it's missing.

**Later in Session 14:**
- **#31:** the owner approved it. The first merge didn't take (still `OPEN`, `mergeStateStatus: CLEAN`), and the second did: `a536353`, CI green (run 45679116372).
- **Frontend reviews:** all of #27, #32, #33, #34, #35 and #36 approved. #27, #33, #35 and #36 merged first, then #32.
- **#32 rebased** on `08ea043`: `066160d`, range-diff `=`, 254 passed.
- **The frontend's process note** said #31 was merged "before he said go". **Answered on #1 (7172828609):** #31 was merged from Developer A's account after its approval, and a PR merges only after the other developer's approval. The comment was later edited to say that **both developers are owners** (#45). The same comment gives the go to make the repo public now (decided in Session 13, reconfirmed today).
- **`replora_env_setup.txt` (untracked, repo root) was staged by `git add -A`** while committing #40. I unstaged it before the commit. `git log --all -- replora_env_setup.txt` shows 0 commits, and `gitleaks dir` finds no leaks. Since then every commit stages files by name. Waiting on the owner's decision (move it out, or ignore it).
- **#40 §7 runs** (P0.5 4c): 6 endpoints, `Idempotency-Key` (required UUID header), `RunState` enum, and `DRAFT_INVALID`, `PLAN_HASH_MISMATCH`, `INVALID_STATE_TRANSITION` and `IDEMPOTENCY_KEY_MISMATCH`. TDD (27 red first). `openapi.json` showed −732 lines. It was proven to be only moves: a schema and path comparison found 11 schemas and 5 paths added, none removed, and no existing schema changed.
- **#41 §7 outputs** (4d): list, preview (`limit` 1–100, `status`, `q` ≤ 200), download (`DownloadLink`) and lineage. TDD (17 red first). Only additions (6 schemas).
- **#42 §8 workflows** (4e): 7 endpoints and `BASE_VERSION_STALE` (409), plus stub notes for §7 and §8 in `api_contract.md`. TDD (23 red first). Only additions (11 schemas).
- **Stack rebase after #32 merged:**
  - **#34:** `git rebase` would have replayed 3 log commits; the last one resets `session_log.md` to `f463fea` and would have overwritten #36. I aborted and checked that `git diff b52afbe ececfe7` is empty. Then I rebuilt the branch: `git reset --hard origin/main`, `git cherry-pick b52afbe`, and one conflict in `error-codes.json` with both sides kept. → `97724a6`, 281 passed.
  - **#40, #41, #42:** `git rebase --onto <new base> <old base head>`, applied cleanly. Regenerating changed nothing. → `1df0c55` (308 passed), `131c035` (325) and `d764eb1` (348).
  - `git range-diff` shows `=` for every code commit. CI is green on all four.
- **Owner's decisions at the end:**
  - **`.gitignore`** now lists `replora_env_setup.txt`, on this PR's branch (`git check-ignore -v`: `.gitignore:51`).
  - **#34 merged** by Developer A on their own go, squash, `ef49ab3`, with `main` CI green. The frontend had approved `b52afbe`; the merged `97724a6` has an identical patch (range-diff `=`).
- **Co-ownership (#45, `a73b4e2`).** The owner asked whether the frontend could be owner, then decided: **both are owners. GitHub stays as it is, and in a disagreement each developer sticks to their own side of development.**
  - The change is a new `decisions.md` row, plus forward-looking wording in `CLAUDE.md`, `plan.md` and `backend_plan.md` ("the owner" becomes "the gate approver", or "both owners" for P16.3 and P19.8).
  - Historical lines are kept: D1–D14 and P0.10 were approved by the owner of the time.
  - Not edited: `docs/frontend/plan.md` line 16 and `frontend/CLAUDE.md`, which are the frontend's own files; they're pointed out in #45.
  - Open point raised in #45: "no self-merge" against practice (#30, #37, #38 and #34 were merged by their authors after approval).
  - At Developer A's request, the #1 comments 7172828609 and 7174794670 were edited so they state co-ownership (#45) instead of a single owner.
- **#44 §2 auth fixtures** (`8052294`). This was the only Phase 0 deliverable still missing: B0 "auth fixtures in B0/B1", agreed in Session 7.
  - **Design:** `contracts/fixtures/auth/<operationId>.json` = `{scenario: {status, body}}`, always with an `ok`. 19 files, 48 scenarios, written by a scratch script that wasn't committed.
  - **The test** validates them against the generated `openapi.json` with `jsonschema` (refs resolved by attaching `components`), rather than walking `app.routes`: on FastAPI 0.165 that gives 4 entries, with the routers wrapped in a lazy `_IncludedRouter`.
  - **TDD:** 2 red without fixtures. Then 3 deliberate mutations (a wrong status for a code, a missing `email`, an undocumented 418) gave exactly 3 failures. **331 passed**, and pip-audit found no known vulnerabilities.
  - I amended the commit message once before opening the PR (47 → 48 scenarios); no PR existed yet.
- **Stack after #34:** #40 was retargeted to `main` (`gh pr edit 40 --base main`), then `git rebase --onto origin/main 97724a6`, then #41 and #42 `--onto` the new heads. All three applied cleanly, regenerating changed nothing, and range-diff shows `=`. → `6dcabef` (308 passed), `d138c28` (325) and `ceedd01` (348).

## Session 13 — 2026-11-25 (other machine, `D:\Projects\replora`)
**Goal:** check the state is aligned, then do the #8 review follow-ups.

**Alignment check:**
- `git fetch --all --prune`: every local branch equals its remote (`feat/p0.5-file-stubs` `3e9c06f`, #10 `ea4464a`, #8 `50ccf31`, `main` `c6f6e92`).
- There was no new GitHub activity since Session 12. The last #1 comment is ours (7145400523). #10 and #11 have no reviews, and #8 is still unmerged.
- `.env` is present here, and git ignores it.
- **Deleted an untracked root `pnpm-lock.yaml`.** It was 9 lines with empty importers (`.: {}`), made on this machine at 08:55 by a pnpm run on this pre-#9 branch. It would have blocked the rebase onto `main`, which has the real 5,075-line lockfile.
- Found the log out of date in two places, now fixed:
  - P0.4 (#9) was done but not counted (now 5/11);
  - `ExportStatus.status` was still listed as waiting, though the #8 review had confirmed it.
- **Owner:** deleted the old OpenRouter key and the OneDrive `Replora/` folder.
- This machine has **no global git identity**. The commit used `git -c user.name=khaledhagar -c user.email=…` (the same identity as the history). Owner: run `git config --global user.name khaledhagar` and `git config --global user.email <your email>`.

**#8 follow-ups → PR #12** (`fix/p0.5-auth-followups`, `9f288cc`, stacked on #8 because the code exists only there):
1. 404 is documented on `GET /auth/me/export/{export_id}` and `DELETE /auth/sessions/{session_id}` (`NOT_FOUND_RESPONSE`).
2. `HTTPException` (routing 404/405) and unhandled exceptions now answer problem+json.
   - `code` = the HTTP status name, or `INTERNAL_ERROR` for an unhandled error.
   - `detail` and exception text are never sent.
   - Headers such as `Allow` are kept.
3. `PasswordRequest` and `MfaDisableRequest` passwords are bounded `1..256` (`CurrentPassword`). Before this, an empty password was also accepted.
4. The 422 codes come from the explicit `VALIDATION_CODES` (11 types, the same names as before); an unlisted type maps to `INVALID`. The 11 types were found by probing every model with bad input. Each is pinned by a request test.

**Proof:**
- TDD: the new tests were red first.
- With only the 2 new handlers disabled, 4/5 of `test_problem.py` failed (404, 405, HTTPException, 500).
- Restored: **101 passed** (79 on #8 + 22) · ruff check and format clean · drift check exit 0 · `uv sync --locked` · pip-audit "No known vulnerabilities found" · gitleaks no leaks.

**Found while probing, asked on #12:**
- `VALUE_ERROR` (meaning an invalid email) is vague: rename it to `INVALID_EMAIL`?
- The `/auth/mfa/challenge` union puts model names into `errors[].path` (`body.MfaCodeRequest.code`). I lean to one model with an exactly-one check at G5.
- The `error-codes.json` shape.

**P0.6 → PR #14** (`chore/p0.6-pre-commit`, `7800507`, from `main`; approved by the frontend):
- **Hooks:** `.pre-commit-config.yaml` has 4 local hooks: gitleaks (staged), ruff check `--fix`, ruff format, and frontend ESLint. They run the tools from the lockfiles, so the versions match CI.
- **A gap found while proving T0.5:** the default gitleaks rules catch `OPENROUTER_API_KEY=sk-or-…` only through `generic-api-key`, and **miss a bare key in code** (`Client("sk-or-v1-…")` → exit 0). Added `.gitleaks.toml` (the defaults plus `openrouter-api-key`); after it, both cases are caught. The full history scan with the new config: no leaks.
- **T0.5 proof:** in a scratch clone, `pre-commit install`, then committing a fake key gave `Failed`, `RuleID: openrouter-api-key`, commit exit 1. T0.5 is ticked in `testing.md`. P0.6 in `plan.md` stays open for the frontend's prettier and typecheck hooks.
- **Root cause of a slow hook:** `frontend/node_modules` was missing on this machine, so pnpm 12 (`verifyDepsBeforeRun`) auto-installed before `pnpm run`, against a slow registry (10–30 s per request). Fixed by running `pnpm install --frozen-lockfile` once. After that, ESLint takes about 10–25 s here.
- **Incident, fixed:** my first T0.5 script failed to clone (no local `main` branch), and the following commands ran in the real repo. They made a local branch `scratch/t0.5` with one commit, installed the hook in the real repo and staged two fake-key files (the commit was blocked). Nothing was pushed. All of it was reverted (`git rm --cached`, `reset --soft`, `branch -D`, `pre-commit uninstall`). The rerun used `$ErrorActionPreference='Stop'` and `git -C <scratch>`.

**Frontend activity (issue #1):**
- #8 was squash-merged (`c4ea4a9`), and #12, #10 and #11 were approved.
- They answered the #12 points: `INVALID_EMAIL`, MFA option (b), and the `error-codes.json` shape `problem_codes {status, description}` + `validation_codes {description}`.
- They accepted the four #10/#11 points. `detected_type` stays an enum.
- New request before G5: fixed lists for `AuditEvent.action` and `target_type`.

**#12 rebased** onto `main` (`78a2a0f`): `git diff 9f288cc 78a2a0f -- backend contracts` is empty. 101 passed, the checks are clean, it's retargeted to `main`, CI is green and the frontend job now runs.

**#16** (`feat/p0.5-error-codes`, `fc31d4b`, stacked on #12):
- `contracts/error-codes.json` v0: 6 problem codes, and 12 validation codes plus `INVALID`.
- `Email` = `EmailStr` + `WrapValidator`, which raises `invalid_email`. `value_error` is no longer mapped.
- `MfaChallengeRequest {code?, recovery_code?}` with an exactly-one check (`MFA_CODE_OR_RECOVERY_REQUIRED` on `body`), and `recovery_code` bounded to `1..64`.
- **Proof:** TDD red first (7 failed). With the JSON removed, the 9 tests error; with one code misspelled, the parity test fails. Result: **118 passed**, ruff clean, no drift, pip-audit clean, gitleaks clean, CI green.

**Frontend reply (issue #1, 7156875222), and our answers:**
- They merged #12 (head `78a2a0f`) and #13. They accepted that backend PRs regenerate `schema.d.ts`, on one condition: no other file under `frontend/`, and it still goes through CODEOWNERS.
- They approved **#16**, with two non-blocking requests: the full §2 `problem_codes` before G5, and a regenerated `schema.d.ts` after #17.
- They opened **#17** (`ci.yml`: the `schema.d.ts` drift check, `next build`, and the regenerated stale types from #12). They pushed **`ec2ccca` on #15**, which fixes all three of our notes.
- **Checking #17:** `pnpm dlx openapi-typescript@7.13.0` on `main`'s `openapi.json` gives exactly their `schema.d.ts`. The only differences were BOM and `§` artifacts from PowerShell `Out-File` on our side. Comment review posted: no blockers.
- **#15 re-check:** posted; all resolved.
- **#16 reply:** posted. The §2 codes come in a separate PR after #16, so the approval stays valid.
- **Issue #1, 7158357090:** proposed 11 §2 codes (`UNAUTHENTICATED`, `INVALID_CREDENTIALS`, `MFA_CODE_INVALID`, `PASSWORD_INCORRECT`, `TOKEN_INVALID`, `CSRF_FAILED`, `EMAIL_NOT_VERIFIED`, `MFA_ALREADY_ENABLED`, `MFA_NOT_ENABLED`, `RATE_LIMITED`, plus the existing `MFA_CHALLENGE_INVALID`).
  - **Rule:** 401 only means "no session". A wrong secret is 400, so the client does not log the user out.
  - **No "email taken" code (S‑26):** register returns 202 with no body in every case, and an existing account gets a notice email. This waits for their confirmation.
- **Note:** this branch has no `frontend/` and no root `pnpm-lock.yaml` (it predates #9). So a `pnpm` run here makes an untracked root lockfile, which was deleted again. That was also the cause of the one found at the start of Session 13.

**Frontend reply (issue #1, 7158585607): all three §2 points confirmed** (the 11 codes, the 400-vs-401 rule, register → 202). The §2 PR comes right after #16. They merged #17 (`73ef4b1`), #14 (`dbe9565`) and #15 (`75b8279`).

**#16 rebased:**
- `git rebase --onto origin/main 78a2a0f` → `c6da1d1`, no conflict.
- `pnpm install --frozen-lockfile`, then `gen:api` → `72813b9`, which touches only `schema.d.ts`: `MfaChallengeRequest` added, `MfaRecoveryRequest` removed, and the challenge body.
- **Checks:** 118 passed, ruff clean, drift exit 0, frontend typecheck passes, 5 frontend tests pass, gitleaks clean.
- **Pitfall:** I pushed before retargeting the base, so GitHub showed `CONFLICTING` against the old base and no CI ran. Retargeting does not trigger CI. Local `merge-tree` against `main` was clean. **Fix:** `gh pr close 16; gh pr reopen 16` → `MERGEABLE CLEAN`, and CI succeeded on `72813b9`.
- Retargeted to `main`, PR body updated, and replied in #1 (7158806753) with the next steps.

**Frontend replies (#1, 7158635728 and 7158990094):**
- #16 was merged at `72813b9` (`main` is `38095c2`, CI green). They checked that `c6da1d1` has the same patches as the approved `fc31d4b`.
- Our order is accepted: #10, then the §2 PR. They asked for reviews of #18 and #19.

**Our reviews:**
- **#19** (`df40f54`): verified locally. `format:check` passes, fails on an unformatted line (exit 1), and passes after `gen:api` (`schema.d.ts` is in `.prettierignore`). **Asked for `format:check` in the CI `frontend` job**, since hooks can be skipped. Explained the local "uv not found": the ruff hooks only match `backend/`, so use `SKIP=ruff-check,ruff-format` or install uv.
- **#18** (`99574dd`): ok. Noted that `7955d6f` is #13's PR head and `14fd30b` its squash commit, so neither is wrong. The `decisions.md` rows come in our §2 PR.

**Continued: #18 and #19 merged, #10 rebased, §2 PR #22:**
- The frontend merged #18 (`d836afe`) and #19 (`6651beb`). #19 added `format:check` to CI, as asked.
- **#10 rebased:**
  - `git rebase --onto origin/main 50ccf31` gave 2 conflicts. `problem.py`: kept the generic "Not found, or not yours". `openapi.json`: regenerated.
  - **Found:** the invitation email (`InvitationRequest.email`, a plain `EmailStr`) still answered `INVALID`, not `INVALID_EMAIL`. #16's `Email` lived in `auth_models.py`, which imports `workspace_models`, so a direct import would be circular. **Fix:** moved `Email` to `app/api/models.py`. A test was red first (2 failed).
  - `gen:api` → `schema.d.ts`.
  - The base was retargeted to `main` **before** the push this time, and CI was green on `55f6a1a`.
  - **Checks:** 161 passed, ruff clean, drift 0, frontend typecheck and `format:check` pass.
- **#22** (`feat/p0.5-auth-error-codes`, from `main`):
  - **TDD:** 18 new tests failed first (10 code pins, 6 "400 documented", 2 register).
  - 10 new codes in `error-codes.json`.
  - `WRONG_SECRET_RESPONSE` (400) on verify-email, password/reset, mfa/enroll/confirm, mfa/challenge, `DELETE /auth/mfa` and `DELETE /auth/me`.
  - The 401, 403 and 429 descriptions name their codes.
  - Register → 202 with no body. FastAPI documents every body-less 202 as `{"schema": {}}`, so the test asserts it equals `password/forgot`'s 202.
  - `api_contract.md`: the §1 rule, the §2 row, a revision line. `decisions.md`: 2 rows.
  - `schema.d.ts` regenerated.
  - **Result:** 135 passed, ruff clean, drift 0, pip-audit clean, gitleaks clean, frontend typecheck, `format:check` and tests (5) pass.
- Updated the #10 PR body, and replied in #1 (7160558200).

**Continued: #10 merged, #22 rebased, #11 rebased, #20 and #21 reviewed:**
- The frontend merged **#10** at `55f6a1a` (`main` is `7b2f66b`), one minute before our #1 comment asking them to re-check it. Corrected in #1 (7160831011).
- **#22's first CI run failed the drift check.** The cause: CI tests the PR merged into the new `main`, and #10's 11 §3 routes still had the old 401, 403 and 429 texts. Reproduced locally after `git rebase origin/main`: `--check` exit 1, and exit 0 after regenerating. Commit `076ba16` holds the generated files only. Result: 178 passed, CI green.
- **#11 rebased:**
  - `git rebase --onto origin/main ea4464a` replayed 11 commits with no conflict, because `main`'s log is unchanged since `ea4464a`.
  - **Patch check:** `git patch-id` per file. Every file is identical to the approved `76bbe42`, except `problem.py`: one context line differs (the 404 text) and the added lines are the same.
  - **Gap found by probing:** number errors (`size`, `limit`) fell back to `INVALID`. Added `int_parsing`, `int_from_float`, `greater_than`, `greater_than_equal` and `less_than_equal` to `VALIDATION_CODES` and `error-codes.json`, plus `FILE_TOO_LARGE` and `QUOTA_EXCEEDED`. 7 tests were red first. Result: 198 passed.
  - Retargeted before the push. CI green on `e4c707a`.
- **#20 and #21 reviewed** (comment reviews, no blockers):
  - #20: `correlation_id` arrives with our P0.11; the dev-only rewrite means no proxy under `next start`; `lang="en"` placeholder.
  - #21: light `--diff` on `--bg` is 4.11:1, so not for text; add `--surface-raised` pairs (all ≥ 5.4:1 today); theme `system` needs a pre-paint `data-theme` or a `prefers-color-scheme` block.

**Plan ticks, #11 after #22, frontend questions:**
- **Owner asked why nothing was ticked in `plan.md`.** Only P0.1, P0.2, P0.3 and P0.10 were ticked. I had deferred every tick to "the next shared docs PR" and never opened it.
  - **#25** ticks P0.4, P0.6, P0.7 and P0.9 (with the root `README.md` local-dev section), plus `error-codes.json` v0, T0.2 and T0.5.
  - **Count corrected:** 4 → 8 of 11 ticked. My first #25 text said 8 before P0.9, which was one too many.
  - **New rule:** tick each step in the PR that finishes it.
- **Frontend merged** #20, #21, #22, #23 (`/tokens-preview`) and #24 (their plan: P0.6, P0.9, P0.11 and P9.1 ticked). `main` is `6eef1fd`.
- **#11 rebased again after #22.** There were conflicts in `error-codes.json` and `test_error_codes.py`, resolved by keeping both. `openapi.json` was stale (`--check` exit 1), so I regenerated it and `schema.d.ts` (`8c55bd8`). Result: 215 passed, CI green.
- **Local vitest:** workers time out while starting ("Timeout waiting for worker to respond", 0 files, about 120 s). It passed here earlier today, and CI ran green on #11 and #25. It's the machine; no frontend config was changed.
- **Asked the frontend 5 questions on #25** (`openapi-fetch`, the F0 contract box, the F0 tests line, frontend S‑01/03/04, S‑05 as a manual rule). Final state posted in #1 (7161976673).

**While waiting for the frontend:**
- **Asked them in #1 (7162100230)** to list every shared-plan item finished on their side: P9.1 (#21, #23) and T11.3 (#21) so far. Their reply gets added to #25 in one commit.
- **#26 (P0.11 backend, T0.7, S‑87)**, from `main`:
  - `app/observability.py`: a pure ASGI `RequestIdMiddleware` (UUIDv7, or a kept incoming ID matching `[A-Za-z0-9._-]{1,64}`), `JsonFormatter` (key-based redaction and email masking) and `configure_logging` (uvicorn's access log off, because it records the IP).
  - `_problem_response` adds `correlation_id` and `X-Request-ID`. The 500 is sent from outside the middleware, so the header is set there too. `_handle_unexpected` logs the traceback.
  - **Tests:** 19 new. Middleware turned off: 18 fail. Scrubbing turned off: the formatter test fails. Result: 197 passed.
  - **Manual uvicorn run:** every line is JSON, the header matches `correlation_id`, and there's no password or email in the log. Uvicorn's `color_message` field is dropped.
  - Ticks P0.11 (with the frontend's #20) and T0.7.
- **#27 (§3):**
  - `PERSONAL_WORKSPACE_UNDELETABLE` (409).
  - `AuditAction` (16 values) and `AuditTargetType` (8) as `Literal`s, documented in `api_contract.md` §3. Auth events aren't included, because they have no workspace.
  - **Tests:** 2 red first, then 181 passed. `schema.d.ts` regenerated.

**#28, §5 registry (P0.5 part 4a)**, from `main`:
- **Routes:** `GET /operations` → `OperationContract[]`; `GET /limits` → `Limits` (4 integers).
- **Public:** no 401, 403 or 404 documented; `Cache-Control: public, max-age=3600` documented on the 200. `api_contract.md` §5 says so.
- **`ArtifactType`:** a `StrEnum` of the 11 kinds. The list comes from `docs/history/Replora_Complete_Project_Plan_AR.md` (`plan.md` P1.1 only says "all 11"). P1.1 will own it.
- `params_schema` is `dict[str, Any]`, with the §5 subset in its description.
- **Tests:** 10 red first (404 and `KeyError`), then 188 passed. Ruff clean, drift 0, pip-audit clean, `schema.d.ts` regenerated, typecheck and `format:check` pass.

**End of Session 13: ticks and final state:**
- **#28 CI green** (`c60e118`).
- **#25 rebased onto `6eef1fd`**, now `6d0a66c`. It also ticks **P9.1** (#21, #23) and **T11.3** (contrast test, #21), and adds a **Phase 0 status list in `security.md`**:
  - S‑01 [x]: gitleaks in pre-commit and CI, T0.5/T0.6, the old key deleted;
  - S‑02 [ ]: no production start-up check yet;
  - S‑03 [x]: locked installs in CI;
  - S‑04 [x]: pip-audit, pnpm audit, Dependabot for uv, npm and Actions;
  - S‑05 [ ]: branch protection, the owner's decision.
- **Not ticked anywhere yet:** P0.11 and T0.7. They're ticked in #26 and count once it merges.
- Claude Code memory updated (project state and the resume rule). Every branch pushed. Final state posted in #1.

**Session close:**
- **Owner set the global git identity** on this machine (checked: `khaledhagar <khaledhagareyad@gmail.com>`; plain `git commit` works).
- **Owner decided: make the repo public**, for free branch protection.
  - Before the decision, I checked what it would expose: full-history gitleaks found 94 commits and no leaks. Both Gmail addresses are in the author history, the docs and plans become public, and there's no `LICENSE`.
  - I recommended private plus GitHub Pro; the owner chose public.
  - I asked the frontend (the repo admin) in #1 (7163028157), with a checklist: a final gitleaks run, noreply emails from now on, the license as the owner's call, then a `main` ruleset (1 approval, the 3 CI checks, no force-push, no bypass), secret scanning with push protection, and approval for fork PRs.
- **The frontend merged #11 (`d4ae8f6`) and #26 (`8b756a8`).** My last log commit (`4ea3072`) landed after #11 merged, so it was cherry-picked here (`e66dd6b`).
- **#25, #27 and #28 were rebased onto `8b756a8`:**
  - **#25:** `backend_plan.md` conflict, resolved with the ticks and an updated P0.5 note.
  - **#27:** `error-codes.json`, keeping both sides. No regeneration needed. 237 passed.
  - **#28:** router conflict (`files` plus `operations`); `openapi.json` and `schema.d.ts` regenerated. 244 passed.
  - All three: no drift, typecheck and `format:check` pass.

**Reviews posted** (comment reviews; the owner approves from their account):
- **#13:** nothing blocks it. Asked for a `schema.d.ts` drift check in CI, and who regenerates it.
- **#15:** nothing blocks it. Flagged the `Claude-Session:` URL trailer, which writes a private link into permanent history, and the tautological `textContent` assertion.

---

## Session 12 — 2026-11-24 (first session in `D:\Projects\replora`)
**Goal:** review frontend PR #9 (P0.4) and do P0.5 part 3 (§3–§4 stubs) while #8 waits.

Before starting: `git fetch --all --prune`. PR #8 is **approved** by the frontend but not merged. New PR #9 from the frontend: P0.4 Next.js skeleton, CI green.

**PR #9 review:**
- Manual review plus `/code-review`. Nothing blocks the merge. The skeleton is minimal and its versions match the agreement. `.gitignore` covers `.next/`, `next-env.d.ts` and `*.tsbuildinfo`, and none of them are tracked. The tested SHA `80aafbd` ≠ head `6150624`, but the only difference is 4 lines in their session log.
- Posted 6 follow-ups on #9 ([comment 7145011476](https://github.com/kzazzco2009-hub/replora/pull/9#issuecomment-7145011476)):
  1. Testing Library cleanup is not wired (no `globals` and no setup file).
  2. Record the ESLint 10 vs plugin-peer (^9) risk in `decisions.md`.
  3. The `toBeDefined()` after `getByRole` is redundant.
  4. Stale T0.3 note in their log.
  5. `next build` in CI goes in a separate `ci.yml` PR.
  6. Tick §4 in the PR body.
- Not kept: the hardcoded `lang="en"`, because locale routing is planned work (D10, Phase 9).
- The approval must come from the owner's account (the permission check blocks `gh pr review --approve` for me): `gh pr review 9 -R kzazzco2009-hub/replora --approve -b LGTM`.

**P0.5 part 3**, split in two because the hand-written diff was 479 lines (> 400). §3 freezes at G5 and §4 at G6:
- **3a `feat/p0.5-workspace-stubs` (`ea4464a`, stacked on #8), 291 lines:**
  - 11 routes (workspaces, members, invitations + `/invitations/accept`, audit).
  - Generic `Page[T]` (`items`, `next_cursor`) with `Cursor`/`Limit` (1..100) query types.
  - `GrantableRole` (no `owner` by invitation or role change; S‑23, S‑29).
  - `AuditEvent.actor_id` is nullable (anonymized on deletion, S‑29).
  - Shared `client`/`openapi`/`schemas` fixtures moved to `tests/conftest.py`.
  - Finding: FastAPI **merges** route-level `responses` into the router-level ones, so a per-route override cannot remove the 404. Fixed with a nested `scoped` router for `/workspaces/{ws_id}`. Proven: with 404 back on the main router, `test_unscoped_routes_document_no_404` failed 3 times; after the fix it passed.
- **3b `feat/p0.5-file-stubs` (stacked on 3a), 260 lines:**
  - 7 routes. The raw `PUT upload.url` is a storage URL, so it is not in the contract.
  - upload-intent: no client `sha256` (422), `size > 0`, 413 on this route only.
  - `FilePage` with a `type` filter.
  - `DetectedType = csv | zip`, the MVP set; Phases 14–16 add values.
  - `sha256` and `detected_type` are null until `complete`.
  - **To confirm with the frontend in the PR:** the `detected_type` set, the nullable fields, and `ws_id`/`file_id`/`user_id`/`invitation_id` as path-parameter names.
- TDD: 41 + 30 tests, all red first (404 or `KeyError` on missing paths and schemas), then green.
- Checks on 3b: **150 passed** · ruff clean · 22 files formatted · drift check exit 0 · `uv sync --locked` · pip-audit "No known vulnerabilities found" · `gitleaks git --pre-commit --staged` no leaks (PATH reloaded first: gitleaks was not on this session's PATH).
- No PRs opened yet: stacked parts open after their base merges (same as part 2).

**Frontend reply on issue #1** (comment 7145138629, 21:35 UTC):
- They approved #8 and run `pnpm gen:api` once it is merged.
- They asked us to squash-merge #9.
- T0.3 proven in real CI. I verified both runs with `gh run view`:
  - 45491885639 (`0e592cc`) failed in the Frontend job at `pnpm -C frontend run lint`;
  - the revert 45492118286 (`4b1da81`) made every job green again.
- `git diff 6150624 5756b20` shows only docs changed since my review.
- They ticked P0.1 and P0.4 in `docs/frontend/plan.md`, which closes my #8 request.
- Their reply came before my #9 comment, so it does not answer the follow-ups.

**Reply posted** ([comment 7145266627](https://github.com/kzazzco2009-hub/replora/issues/1#issuecomment-7145266627)):
- T0.3 runs verified; the owner approves and squash-merges #9.
- The #9 follow-ups are non-blocking and fine in a later PR.
- **Please squash-merge #8 yourselves**: under no-self-merge we cannot merge our own PR. This settles who merges what: the reviewer merges the other side's PR.
- Part 3 is ready on two stacked branches, with the 4 points to confirm.

- **#9 merged** by the owner (approved, squash `c6f6e92`, branch deleted). CI on `main` passed (lint, typecheck, test, audit). #8 is still `MERGEABLE`/`CLEAN` on the new `main` (`git merge-tree` exit 0; #9 touched only `frontend/`, `docs/frontend/` and `pnpm-lock.yaml`).

- **Opened #10 (3a) and #11 (3b)** as stacked PRs with reviewer `kzazzco2009-hub`, so the frontend can review all of P0.5 part 3 now. CI: backend and gitleaks pass on both; the frontend job is skipped because these branches predate #9, and it runs after the rebase. Posted the merge order and the points to confirm on #1 ([comment 7145400523](https://github.com/kzazzco2009-hub/replora/issues/1#issuecomment-7145400523)).
- Wrote `D:\Projects\replora_env_setup.txt` (outside the repo, never committed) with the steps to create `.env` on the other machine: clone or pull, `Copy-Item .env.example .env`, `APP_ENV` plus `OPENROUTER_API_KEY`, and checks (`git check-ignore`, a `Settings()` load that prints only the key length, 150 tests). **It holds no secret.** The key goes through a password manager, or a new per-machine key is made on openrouter.ai.

**End of session:** everything is committed and pushed on `feat/p0.5-file-stubs`, which holds the newest log. `feat/p0.5-workspace-stubs` and `feat/p0.5-auth-stubs` (#8) are pushed. No uncommitted work.

---

## Session 11 — 2026-11-24 (second dev machine, handover)
**Goal:** get the latest state to the frontend, retire the OneDrive folder, and hand over to a session opened in `D:\Projects\replora`.

Done:
- **PRs:**
  - #5 (frontend log + `frontend/CLAUDE.md`) was merged by the frontend.
  - #6 is approved.
  - On issue #1 ([comment 7144367719](https://github.com/kzazzco2009-hub/replora/issues/1#issuecomment-7144367719)) I gave the owner's go to merge #6, asked for a review and merge of #7, and previewed part 2. Part 2 includes the proposal `ExportStatus.status = pending | ready | failed`, to confirm at G5.
- **PR #7 (`docs/original-plan`):** `docs/history/Replora_Complete_Project_Plan_AR.md`, a byte-identical copy (SHA-256 `16247D27FCE2…C3`), plus a README marking it historical and superseded by `plan.md` v1.1. Read in full first: no secrets; it names a person and the old multi-AI-agent roles. CI green.
- **OneDrive decision:** the repo lives on the local disk (`D:\Projects\replora`) and GitHub is the sync between machines. OneDrive is unsuitable for git: risk of `.git` corruption, conflict copies instead of merges, `.env` uploaded to the cloud, `.venv`/`node_modules` churn, and files-on-demand placeholders.
  - Before deleting the OneDrive folder I checked its contents: `.env`, the frozen `Planning/` and `Frontend_Planning/`, the original plan (now in #7) and the frontend zip (a copy of `Frontend_Planning/`).
- **Secrets (S‑01):**
  - The owner created a **new OpenRouter key** in `D:\Projects\replora\.env`.
  - Verified without printing it: `git check-ignore` gives `.gitignore:2:.env`; not tracked or staged; `Settings()` loads it (`sk-or-` prefix, 73 characters, no stray quotes or spaces; the repr hides it); it differs from the OneDrive copy.
  - Still for the owner: **delete the old key** on openrouter.ai, then delete the OneDrive folder and empty the recycle bin (local and onedrive.com).
- **Claude Code memory** copied to `~/.claude/projects/D--Projects-replora/memory/` (for sessions opened in the repo folder). It holds this machine only; the other machine relies on the root `CLAUDE.md`.
- No code changes in this session.

- **#6 and #7 merged** (squash, by the frontend: `7343aea`, `887892a`). Their #6 review asked for two things in the auth-stubs PR:
  1. Errors documented as problem+json with a shared `ProblemDetails` schema (401, 403, 409, 422, 429).
  2. Short, stable `operationId`s (`auth_login`).
- **Rebased part 2** onto `main` (`git rebase --onto origin/main b156a40`; the squash dropped the old part 1 commit). 56 passed and the drift check was clean after the rebase.
- **Feedback applied with TDD (23 new tests seen red first):**
  - `Problem` renamed to **`ProblemDetails`**. Explicit 401/403/409/422/429/501 responses, all `application/problem+json` with `$ref ProblemDetails`. FastAPI's `HTTPValidationError` is not exposed.
  - **Runtime 422 handler:** before, FastAPI answered `application/json` `{detail: […]}`, which bypassed the error-code mapper. Now it answers problem+json `VALIDATION_FAILED` with `errors[{path, code, params}]`, for example `body.password` / `STRING_TOO_SHORT` / `{min_length: 12}`.
  - **Security finding:** FastAPI's default 422 **echoed the rejected input**, so a too-short password came back in the response body. Proven by temporarily restoring the default handler: `'tiny-secret' is contained here`. Our handler never includes `input`. Also fixed a bug in my own test: the first secret (`short-secret`) was exactly 12 characters, so it was valid and proved nothing.
  - `operationId` = `<tag>_<function>` via `generate_unique_id_function` (20 IDs: `auth_login`, `auth_get_me`, …, `health_get`). They are unique and match `[a-z]+_[a-z_]+`.
  - Checks: **79 passed** · ruff clean · drift exit 0 · `uv sync --locked` · pip-audit clean.
- **Track-plan ticks (found when the owner asked why only P0.3 looked ticked):** `docs/plan.md` was right (P0.1, P0.2, P0.3, P0.10 ticked). But `docs/backend_plan.md` B0 was **one combined checkbox**, so it could not show progress, even though the file says "tick here **and** in plan.md". I split it into one line per step and ticked P0.1, P0.2, P0.3, the api_contract draft, T0.1, T0.3, T0.4 and T0.6.
  - `docs/frontend/plan.md` P0.1 is unticked although the frontend logged it as done. It is the frontend's file, so I asked them on #8 to tick it.

**Handover:** the newest log is on `feat/p0.5-auth-stubs` until its PR merges (`main` has up to Session 10, through #6). Start the next session in `D:\Projects\replora` with `git fetch --all --prune`, then read this file on `main`, or on the branch if the PR is still open.

---

## Session 10 — 2026-11-24 (second dev machine)
**Goal:** review PR #5, then start P0.5 (generated OpenAPI + drift check).

Before starting:
- **PR #4 (P0.3)** was approved and merged by the frontend (`8722ebf`, squash), and CI on `main` is green.
  - They could not check the `setup-node` and `pnpm/action-setup` SHAs, so I posted the tag-to-commit lookups ([comment](https://github.com/kzazzco2009-hub/replora/pull/4#issuecomment-7143688000)).
- **PR #5 (frontend):** adds `docs/frontend/session_log.md` (P0.1 versions match the agreement) and `frontend/CLAUDE.md` (no conflict with the root file).
  - I reviewed it. The `gh pr review --approve` call was blocked by the permission check, so the owner approved it from their own account. It is approved, and the merge is theirs.
  - I posted the full Phase 0 status on issue #1 ([comment](https://github.com/kzazzco2009-hub/replora/issues/1#issuecomment-7143770831)).
- **`backend/setup` deleted** by the owner (the `gh api -X DELETE` call was also blocked for me). `frontend/setup` goes once F0 exists.
- The OneDrive `Planning/` still showed `[ ] P0.3` because it is frozen, which confused the owner. I added `00_FROZEN_README.md` to `Planning/` and `Frontend_Planning/`.
- Found a slip of mine: T0.6 had passed in Session 8 but was not ticked in `testing.md`. Fixed here.

**P0.5 is split into small PRs:**
1. The export pipeline and drift check (this PR).
2. 501 stubs for auth (§2).
3. 501 stubs for workspaces and files (§3–§4).
4. 501 stubs for operations, drafts, runs and workflows (§5–§8).
- The frontend `pnpm gen:api` follows the first stubs.

Done (branch `feat/p0.5-openapi-export`):
- **TDD:** `tests/unit/test_export_openapi.py`, 5 tests: health is in the document with the package version, rendering is deterministic, `check` passes after `write`, fails on a drifted file (T0.4) and fails on a missing file. All 5 were red first (`NotImplementedError` stubs), then green.
  - The version assertion cannot yet tell explicit wiring from FastAPI's default `"0.1.0"`; it catches a missing wiring at the first version bump. `create_app` now sets `version=` from the package metadata explicitly.
- `app/export_openapi.py`: `uv run python -m app.export_openapi` writes `contracts/openapi.json` (OpenAPI 3.1.0, 55 lines, `/api/v1/health` only), and `--check` exits 1 on drift.
  - CLI proof: I changed the title in the file, and `--check` printed `…openapi.json is out of date…` with exit 1. After regenerating, it exited 0.
- CI: new backend step "Contract drift check" (`uv run python -m app.export_openapi --check`).
- Root `CLAUDE.md`: phase gates now name the gate approver (Developer A for backend gates, Developer B for frontend gates, both for shared gates), as noted in the PR #5 review.
- `contracts/README.md` (what is generated and how). README: the export command.
- **T0.4 passed** (unit and CLI). **T0.6 ticked** (evidence in Session 8).
- **P0.5 partly done:** the export and the drift check are done; the stubs and the frontend client are next.
- **P0.5 part 2 (§2 auth stubs)**, branch `feat/p0.5-auth-stubs` (stacked on part 1; its PR opens after #6 merges):
  - TDD: `tests/unit/test_auth_stubs.py` with 44 tests. They cover: every §2 operation documented with its success status; every stub answering 501 `application/problem+json` `{type, title, status, code: NOT_IMPLEMENTED}`; exactly the 19 contract operations and nothing more; the `User` fields and enums; login documented as `User | MfaRequired`; errors documented only as problem+json; register rejecting a password under 12 characters; unknown body fields rejected. All 44 were red first (routes missing), then green.
  - Code: `app/api/models.py` (`ApiModel`, `extra=forbid`), `app/api/problem.py` (`Problem`, `ProblemError`, `not_implemented()`, the handler, and `use_problem_media_type`), `app/api/v1/auth_models.py`, `app/api/v1/workspace_models.py` (`Workspace`, `Role`) and `app/api/v1/auth.py` (19 routes). `uv add email-validator` (2.4.0) for `EmailStr`.
  - Finding: FastAPI documents error models under `application/json`, the route's media type, and has no option to change that (I checked with a scratch script). `problem.install` post-processes the document, moving `4XX`/`5XX` schemas to `application/problem+json`, so the live and committed documents match the real responses.
  - Bug found and fixed (in my test): the drift test wrote with `write_text()` and no encoding, which is cp1252 on Windows. Once the document contained `§`, the UTF-8 read failed (`0xa7`). Proven with `locale.getpreferredencoding()` and the offending text; fixed with `encoding="utf-8"`. It would have passed on Linux CI and failed on Windows only.
  - ruff `S105`/`S106` are ignored in `tests/**` only, for fake credentials.
  - Checks: ruff clean · 16 files formatted · **56 passed** · drift check exit 0 · `uv sync --locked` · pip-audit clean. `openapi.json` now has 19 auth operations and 21 schemas (1,569 generated lines).

---

## Session 9 — 2026-11-24 (second dev machine)
**Goal:** P0.3, the backend skeleton with `GET /api/v1/health`.

Before starting:
- PR #3 (`CLAUDE.md` + `/docs/frontend/` CODEOWNERS) was approved and merged by the frontend (`47d2863`, CI green on `main`).
- The frontend confirmed `6ce85a8` (alignment of the frontend package) on PR #2: "happy with all of it".
- I posted the alignment checklist on issue #1 ([comment 7143099550](https://github.com/kzazzco2009-hub/replora/issues/1#issuecomment-7143099550)):
  - F0 branches from `main`, because `frontend/setup` and `backend/setup` are 0 ahead / 9 behind;
  - only the repo `docs/` is used, since the OneDrive copies are frozen;
  - environment check: Node 26.13.1, pnpm 12.23.0, gitleaks 8.30.1, pre-commit 4.7.0;
  - P0.1 recorded in `docs/frontend/session_log.md`;
  - `frontend/CLAUDE.md` without contradictions to the root file;
  - what the F0 CI job needs.
  - **Frontend reply (20:13 and 20:18 UTC): every point agreed. Their environment matches:** Node v26.13.1 (`nvm install 26.13.1`), pnpm 12.23.0, gitleaks 8.30.1 (checksum verified), pre-commit 4.7.0.
    - They work only from `docs/`. F0 branches from `main`.
    - Branch cleanup is agreed: the owner deletes `backend/setup` (0 ahead), and the frontend deletes `frontend/setup` once F0 exists. They merged `origin/main` into it (`8b88af0`), so it holds no work of its own.
    - They will propose a shared `.devcontainer/devcontainer.json` that pins Node 26.13.1.
    - **Both sides are now on the same state.**

Done (branch `feat/p0.3-backend-skeleton` from `main`):
- `uv init backend --bare --no-pin-python --name replora-backend --python 3.14`.
  - `uv add fastapi pydantic-settings uvicorn`.
  - `uv add --dev pytest httpx2 ruff pip-audit`.
  - Resolved: fastapi 0.165.0, pydantic 2.14.4, pydantic-settings 2.16.3, uvicorn 0.54.0, starlette 1.10.0, pytest 9.2.0, ruff 0.17.6, pip-audit 2.10.1, httpx2 2.16.2, on Python 3.14.10.
- **`httpx2` instead of `httpx`:** Starlette 1.10 deprecates `httpx` for its test client (`StarletteDeprecationWarning: … install httpx2 instead`), so the dev dependency uses `httpx2`.
- `app` is an installed package (`uv_build`, `module-root = ""`). `/health` reads the version from the package metadata, so `pyproject.toml` is the single source.
- **TDD** (each test seen red first, for the right reason):
  - T0.1 health: red with `404 != 200`, then green.
  - Config, 6 tests: unknown `APP_ENV` rejected (`literal_error`), `SecretStr` never in repr or dump, values read from the environment, blank `.env.example` values fall back to the defaults, `/docs` and `/openapi.json` 404 in production and served in development.
    - The first version of the `APP_ENV` test passed for the wrong reason (`extra_forbidden`), so I tightened it to assert the `literal_error` on `app_env`.
    - The blank-value test was written together with its fix, so I removed `env_ignore_empty` to watch it fail (`literal_error`, `input_value=''`), then restored it.
  - Tests never read the developer's real `.env` (`_env_file=None`).
- **Local CI checks (in `backend/`):** `uv sync --locked` ok · `uv run ruff check .` all passed · `uv run ruff format --check .` 8 files formatted · `uv run pytest` **7 passed**, no warnings · `uv run pip-audit` no known vulnerabilities (skips only our own package).
- **Real run:** `uv run uvicorn app.main:create_app --factory --port 8000`, then `GET /api/v1/health` gave **200 `{"status":"ok","version":"0.1.0"}`** and `/docs` gave 200.
- **P0.3 done. T0.1 passed.**
- **PR #4** opened. The first backend CI run **failed in 2 s**: `Unable to resolve action astral-sh/setup-uv@v10, unable to find version v10`.
  - Root cause: setup-uv publishes only full release tags (`v10.4.0`). This was my mistake in the PR #2 workflow, and it showed up only now because the backend job ran for the first time.
  - I checked all action refs with `gh api …/git/ref/tags/…`. Fix (`018c525`): **every action is pinned to its commit SHA** with the version as a comment (checkout v7.0.1, setup-uv v10.4.0, setup-node v7.1.0, pnpm/action-setup v6.1.1).
  - After the fix, the backend job passed in 15 s on CPython 3.14.4: 51 packages, ruff clean, 8 files formatted, 7 passed, no known vulnerabilities.
- **T0.3 passed.** The clean PR was green.
  - A deliberate unused import (`09f66e2`) made the backend job fail (`F401`, `E402`, `Found 2 errors`, exit 1).
  - The revert (`a8ea5e4`) brought the tree back to `018c525` (`git diff --stat` empty) and CI green again.
  - On the first revert attempt, `git revert -q` was rejected and my `--amend` then mislabeled the lint commit locally. The push was rejected (non-fast-forward), so nothing wrong reached GitHub. I checked that the trees were identical, reset to the remote, and reverted properly.
- `gitleaks dir backend` reports 200 findings, all in the git-ignored `.venv` (SPDX data in `license_expression`, a pip-audit dependency), and 0 in tracked files. `gitleaks git .` is clean.
- **S‑02 partly done:** env-only config and `SecretStr` are verified. The "refuse to start in production when a required secret is missing" check is added with the first required secret (`DATABASE_URL` at P4 or the session key at P5).
- On this machine, uv warns about hardlinks between the C: cache and the D: repo. `UV_LINK_MODE=copy` silences it. It's cosmetic.

---

## Session 8 — 2026-11-24 (second dev machine)
**Goal:** read the latest issue #1 reply and prepare the `chore/repo-skeleton` PR.

Done:
- **Issue #1, new frontend reply:**
  - frontend versions confirmed;
  - **TypeScript pinned to the newest 6.x**, because typescript-eslint does not support 7.0.2;
  - Node and pnpm are to be pinned for everyone, and the frontend asked the backend to confirm Node 26 LTS.
  - Verified with `npm view`: typescript 6.0.3 is the newest 6.x; typescript-eslint 8.74.0 peer range is `typescript >=4.8.4 <6.1.0`; pnpm 12.23.0; Node 26.13.1. **P0.1 done** (`[x]` in plan.md). **P0.10 done** (D1–D14 recorded in Session 3).
- `D:\Projects\replora` was missing on this machine, so I re-cloned it with `gh repo clone`. The remote was unchanged (`ab63da8`, branches `main`, `backend/setup`, `frontend/setup`, no PRs). Created branch `chore/repo-skeleton` from `origin/main`.
- Applied the issue #1 agreement to the docs with a scratch script that requires exactly one match per edit:
  - `api_contract.md`: 15 edits (§0 freeze schedule, CSRF endpoint, sha256 server-side, `/limits`, `params_schema` subset, full PATCH, `Explanation`, preview `status`/`q`, draft shapes, §10 fixtures and the i18n parity check);
  - `plan.md`: 8 edits (`docs/` paths, Visual Builder out of scope, Python 3.14, gate approvals, P0.1 and P0.10 ticked);
  - `security.md`: S‑34;
  - `testing.md`: T6.8 and the reports paths.
  - Line endings are normalized to LF.
- Skeleton files written:
  - `.gitignore`, `.gitattributes` (LF) and `.env.example` (key names only);
  - `.python-version` 3.14, `.nvmrc` 26.13.1, a root `package.json` (`packageManager: pnpm@12.23.0`, `engines.node >=26.13.1 <27`) and `pnpm-workspace.yaml` (`frontend`);
  - `.github/workflows/ci.yml`:
    - a `detect` job;
    - a gitleaks job that scans the full history, with the downloaded binary's checksum verified;
    - backend and frontend jobs that are skipped until `backend/pyproject.toml` or `frontend/package.json` exists;
  - `.github/CODEOWNERS`, `.github/pull_request_template.md` and `.github/dependabot.yml` (actions, uv, npm weekly);
  - `docs/decisions.md` and `README.md`. `Planning/*.md` copied to `docs/`.
  - Action versions were checked with `gh api …/releases/latest`: checkout v7, setup-uv v10, setup-node v7, pnpm/action-setup v6.
- **T0.6 passed:** `git check-ignore -v` matches `.env`, `.env.local`, `.env.production`, `backend/.env` and `.data/replora.db`, and `.env.example` is not ignored.
- **Tools installed** by the owner (see the versions above). gitleaks and pnpm were installed but not on this session's PATH, so the PATH was reloaded from the registry.
- **gitleaks (S‑01):**
  - probe: a fake `OPENROUTER_API_KEY=sk-or-v1-…` in a scratch dir outside the repo gave `leaks found: 1`, exit 1;
  - `gitleaks git --pre-commit --staged` on the 22 staged files: no leaks, exit 0;
  - `gitleaks dir .`: no leaks, exit 0;
  - `gitleaks git .` over the history (1 commit): no leaks, exit 0.
  - **P0.2 done.** T0.5 proper (the pre-commit hook blocking a commit) is done with P0.6.
- Commits `653876c` (skeleton) and `31cca94` (docs) on `chore/repo-skeleton`. A final `gitleaks git .` found no leaks; then pushed.
- Opened [PR #2](https://github.com/kzazzco2009-hub/replora/pull/2) with reviewer `kzazzco2009-hub`.
- **CI on PR #2** (`gh pr checks 2 --watch`, run 45471829251): `Detect project parts` pass (4 s), `Secret scan (gitleaks)` pass (11 s; checksum verified, full history), Backend and Frontend skipped as designed.
  - The first half of T0.3 (green on a no-op PR) passed.
  - The second half (CI fails on an intentional lint error) waits for the backend job to exist (P0.3), so T0.3 stays open.
- Posted the final state on issue #1, with Node 26.13.1 confirmed and the PR link.
- **PR #2 review (frontend):** no blockers, but four questions.
  - Cause of points 1 and 3: `docs/` was copied from `Planning/` only, so the agreed `Frontend_Planning/` package (plan 191 lines, testing, security, README) was missing, and with it T0.F1, T9.U1, T10.U1/U2 and T12.U1.
  - Fix: the package is copied to `docs/frontend/` (without its outdated `api_contract.md`/`design.md` copies or its session log), `docs/frontend_plan.md` became a pointer, and the "hand-written OpenAPI" wording now says "generated from 501 stubs".
  - Verified: every listed ID is found by grep in `docs/frontend/`, and no hand-written wording is left. Replied on PR #2.
- **Frontend package aligned with issue #1** (commit on PR #2; 17 edits in `docs/frontend/` plan, testing and security):
  - no browser sha256 (P10.1, S‑65; T10.2 duplicate check now uses the server `sha256`);
  - `GET /auth/csrf` bootstrap and CSRF on login and register (P9.6, T9.U1, S‑25);
  - limits from `GET /limits`; preview `status`/`q`; full-definition PATCH and the `params_schema` form;
  - `Explanation` key/params vs AI text; i18n key parity (T9.4); pinned TS 6.0.3, Node 26.13.1, pnpm 12.23.0; S‑05 manual protection rule.
  - grep shows no `Web Crypto`, browser-hash or `(latest)` wording left. Sent to the frontend on PR #2 for approval.
- Added a root `CLAUDE.md` (commit on PR #2) with the session start steps, ownership, process and phase gates, code style, contract rules, git rules and the Windows/multi-machine notes. Every Claude Code session on any machine loads it.
- **PR #2 merged** by the frontend at 19:59 UTC (`1e0691b`), approved after they verified `193b07a`.
  - `6ce85a8` (frontend alignment) was included in the merge, so I asked them to confirm it.
  - `f75fa68` (`CLAUDE.md`) was pushed just after the merge and missed it. I cherry-picked it onto `chore/claude-md` from `main` (`f562659`) and added the requested `/docs/frontend/ @kzazzco2009-hub` CODEOWNERS line, as PR #3.
  - Dependabot ran on `main`: github-actions and npm succeeded, while `uv in /backend` failed because `backend/` does not exist yet. That is expected until P0.3.
- **Still open with the frontend (before the merge):** PR #2 approval (incl. the root pnpm workspace layout), `docs/frontend/` ownership in CODEOWNERS, and the move to an organization. The `NEEDS_REVIEW` resolution endpoint and the full `error-codes.json` come at G1.
- `actionlint` was not run locally because the permission check blocked `uvx`; the CI run on the PR validates the workflow instead. The P0.7 contract-drift job is added with P0.5. P0.8 branch protection waits on the organization decision.

---

## Session 7 — 2026-11-24
**Goal:** read the frontend reply on issue #1, record the agreement, and answer it.

Done:
- Ran `gh issue view 1 -R kzazzco2009-hub/replora --comments` from PowerShell. The frontend developer (`kzazzco2009-hub`) **accepted every backend proposal as written** and confirmed the G0 agreement on both sides (see the decisions log, 2026-11-24 rows).
- Frontend notes:
  - branch protection needs GitHub Pro, a public repo or an organization, so the rule is manual for now;
  - Discussions are not needed;
  - **F0 waits until the skeleton PR is merged**.
- Their reply did **not** confirm the frontend versions or TypeScript 7.0.2.
- Posted the backend reply, [comment 7141783468](https://github.com/kzazzco2009-hub/replora/issues/1#issuecomment-7141783468). It acknowledges the agreement, lists the skeleton PR contents, and asks the frontend to confirm the versions, in particular TS 7 support in Next 16.4, typescript-eslint and Vitest.
- Not done (on purpose): no repo changes and no code. P0.1 is still unticked, because it waits on the frontend version confirmation.

**Next step:** create the `chore/repo-skeleton` PR (see Current status).

---

## Session 6 — 2026-11-24
**Goal:** answer the frontend's G0 issue on GitHub, verify the latest versions (P0.1), and prepare the dev machine.

Done:
- Installed `gh` 2.105.0 and logged in as `khaledhagar`. Verified with `gh api`: the repo is private, `kzazzco2009-hub` is admin, `khaledhagar` has write only, and no branch is protected. Discussions are off.
- Read issue #1 ("G0: frontend approval + requirements before F0"). Frontend approves G0 and asks for the repo skeleton on `main`, Discussions, a 24 h review time, plus 7 open points.
- Posted the backend reply (issue #1 comment 7130830551). Proposals:
  - skeleton through a `chore/repo-skeleton` PR; the admin enables protection and Discussions; protection may need GitHub Pro or an org;
  - 24 h for PRs and 48 h for gates;
  - server-side sha256, removed from `upload-intent`;
  - auth fixtures in B0/B1;
  - new `GET /auth/csrf`;
  - draft types `Column`, `RunSummary`, `OutputArtifact`, `Lineage`, `AuditEvent`;
  - preview `status`/`q` instead of `filter=`;
  - PATCH draft sends the full `definition` with `If-Match`, plus a `params_schema` subset;
  - Visual Builder out of scope; `Planning/` moves to repo `docs/`;
  - `GET /limits`, a staged contract freeze, `openapi.json` from 501 stubs, an i18n key parity CI check, `explanation_key` for the TemplatePlanner, shared CODEOWNERS for root and contracts, PR-only merges.

- **P0.1 (versions):** checked PyPI, npm, the Node, uv and gitleaks releases, the Vercel Python docs and the Supabase changelog. The results are in "Recorded versions". Key finding: Python 3.15 is out, but Vercel supports only up to 3.14, so the target is 3.14. P0.1 is left unticked until the frontend confirms the frontend versions (TypeScript 7.0.2 is a major change to verify).
- **Dev machine:** installed Node 26 LTS, pnpm, gitleaks (winget), plus Python 3.14.10 and pre-commit (uv). Fixed PATH for `~/.local/bin`. The final state is verified (see "Recorded versions" → Final state).
- Not done (on purpose): no repo changes and no code. `D:\Projects\replora` is still at `ab63da8 Initial commit`, clean.

**Waiting on:** the frontend developer's confirmation on issue #1, and the admin enabling `main` protection and Discussions.
**Next step:** read the issue #1 reply. If agreed, tick P0.1 and open the `chore/repo-skeleton` PR (see Current status).

---

## Session 5 — 2026-11-24
**Goal:** answer the frontend developer's pre-G0 review and close the contract gaps that block both tracks.

Done:
- Repo `kzazzco2009-hub/replora` verified (branches `main`, `backend/setup`, `frontend/setup`, README only). Cloned `backend/setup` to `D:\Projects\replora` (outside OneDrive). No code committed.
- Contract must-haves applied to **both** copies of `api_contract.md`: MFA login challenge cookie and split endpoints (`/auth/mfa/enroll/confirm`, `/auth/mfa/challenge`), `/auth/sessions` list and revoke, `timezone` in `PATCH /auth/me`, `DELETE /workspaces/{ws}`, `POST /files/samples`, the cross-origin upload note, and run state rules (`DRAFT_INVALID`, approve only in `AWAITING_APPROVAL`, `NEEDS_REVIEW` resolution defined at G1).
- `plan.md` (§3 CORS wording, P5.8, P5.11), `security.md` (S‑28, S‑50, S‑61) and `Frontend_Planning/plan.md` and `security.md` (CORS wording, S‑61, S‑28) updated to match.
- New error codes to add to `contracts/error-codes.json` v0: `MFA_CHALLENGE_INVALID`, `PERSONAL_WORKSPACE_UNDELETABLE`, `DRAFT_INVALID`, `INVALID_STATE_TRANSITION`.
- Package sent to the frontend developer for review: `Frontend_Planning/` plus `plan.md` and `backend_plan.md`.

Open (to settle in the G0 meeting): server-side sha256 vs browser hashing, `status`/`q` instead of `filter=`, limits from the API, staged contract freeze, params_schema subset, i18n key parity file, explanation language, the openapi.json-from-stubs approach, 24 h review time.
Blocker for P0.1: `uv` is not on PATH on the dev machine.

**Next step:** G0 meeting with the frontend developer, then B0 / P0.1.

---

## Session 4 — 2026-11-23 (handover point)
**Goal:** confirm the frontend handover and close the planning stage.

Done:
- **Owner confirmed that `Frontend_Planning/` was sent to the frontend developer (Developer B).** From now on the frontend developer keeps their own `session_log.md`.
- Planning stage closed. Plan v1.1 and decisions D1–D14 are approved.
- No code implemented.

Reminders for the next session:
- `.env` (holding `OPENROUTER_API_KEY`) is in the project root and git is not initialized. **P0.2 must create `.gitignore` before any commit.** Verify with `git check-ignore .env` (T0.6).
- Phase 0 is shared. Do the backend half (B0) plus the repo-wide items (git, CI, CODEOWNERS, branch protection). Draft `api_contract.md` → `contracts/` with the frontend developer for joint Gate G0.
- Changes to `design.md` and `api_contract.md` must also be sent to the frontend developer until `contracts/` exists in the repo.
- Work incrementally, log the evidence for every step, and ask the owner for permission at the end of Phase 0 (Gate G0).

**Next session starts with:** backend Phase 0 (B0), step **P0.1**.

---

## Session 3 — 2026-11-23
**Goal:** record the owner approvals and create the frontend package.

Done:
- Owner approved all recommendations D1–D14 (decisions log updated).
- Owner = backend developer (Developer A).
- Created `../Frontend_Planning/` (self-contained, to be sent to the frontend developer):
  - `README.md`, `plan.md` (F0–F11 + shared phases), `testing.md`, `security.md`, `session_log.md`;
  - `design.md` and `api_contract.md` (copies of the master).
- **Sync rule:** any change to `design.md` or `api_contract.md` must be applied to both copies until the repo exists. After Phase 0 the repo `contracts/` and docs become the single source.
- No code implemented.

Next step: send `Frontend_Planning/` to the frontend developer. Then start Phase 0 / P0.1 (backend half) and agree the contract jointly at G0.

---

## Session 2 — 2026-11-23
**Goal:** a full review of the plan for suitability and coverage of functional and non-functional requirements.

Done:
- Wrote `plan_review.md`, which found 24 gaps:
  - 13 functional;
  - 8 non-functional or production;
  - 4 security;
  - 3 process or schedule.
- Applied all fixes, so the plan is now **v1.1**. The main changes:
  - **P8.8 production feasibility spike** (staging only). It proves Vercel worker chaining, bundle size, the pooler and 50 MiB uploads before the frontend is integrated, and it decides D9.
  - **TemplatePlanner** (P3.9), so MVP users get plans before the AI planner exists.
  - Decimal money handling, ambiguous dates sent to NEEDS_REVIEW, and UTF‑8 BOM CSV output for Arabic in Excel (P7.5).
  - Invitations, account export and deletion, and optional MFA (P5.9–P5.11, S‑28, S‑29).
  - Observability moved to P0.11. Added NFR‑9…NFR‑14 (availability, RPO/RTO, browsers, cost, bundle size, maintainability).
  - Load test repeated on staging (P18.8) and a restore drill (T18.7). Cross-browser E2E (P17.7). Legal and landing pages (P17.8).
  - `If-Match` concurrency on PATCH (P8.9). Onboarding with sample files (P10.9). Timezones (P10.10).
  - Gate rule for parallel tracks. Realistic schedule: MVP in 14–18 weeks, full scope in 9–12 months.
  - New decisions D11–D14.
- No code implemented.

Next step: owner review of v1.1 and answers to D1–D14, then Phase 0 / P0.1.

---

## Session 1 — 2026-11-23
**Goal:** review the original plan and produce the new planning set.

Done:
- Reviewed `Replora_Complete_Project_Plan_AR.md` (v0.6/v0.6.1 summary, Arabic).
- Found 11 issues. The main ones: Vercel body and duration limits vs the file and run limits, native binaries for DOC and OCR, SQLite→Postgres drift, Supabase RLS exposure, an unplanned UI, too much scope before the MVP, and the `.env` secret in a synced folder without git.
- Created `Planning/`: `plan.md` (20 phases, 0–19), `testing.md`, `security.md`, `design.md`, `api_contract.md`, `backend_plan.md`, `frontend_plan.md`, `session_log.md`.
- **No code implemented** (per instruction: wait for review).

Notes for the next session:
- The `.env` file exists in the project root with `OPENROUTER_API_KEY`. Git is not initialized yet. P0.2 must add `.gitignore` before the first commit.
- Ask the owner for D1–D10 answers before P0.1.

Next step: owner review, then Phase 0 / P0.1.
