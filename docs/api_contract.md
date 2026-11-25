# Replora — API Contract v1 (Backend ⇄ Frontend)

This contract is what lets the two developers work at the same time. **Draft agreed at Gate G0. Frozen as `contracts/openapi.json` at P8.7.** Any change after freezing follows §9.

**Revision 2026-11-24 (issue #1 G0 agreement):** `GET /auth/csrf` (§2); server-side sha256, so `sha256` is removed from `upload-intent` (§4); `GET /limits` (§5); full-definition PATCH, the `params_schema` subset and `explanation` keys (§6); draft shapes for `Column`, `RunSummary`, `OutputArtifact`, `Lineage` and `AuditEvent`; preview `status`/`q` instead of `filter=` (§7); staged freeze and `openapi.json` generated from stubs (§0, §10).

**Revision 2026-11-24 (G0 must-haves):** MFA login challenge (§2), sessions list and revoke (§2), `timezone` in `PATCH /auth/me` (§2), workspace deletion (§3), onboarding samples endpoint and the cross-origin upload note (§4), run state rules (§7). New error codes: `MFA_CHALLENGE_INVALID`, `PERSONAL_WORKSPACE_UNDELETABLE`, `DRAFT_INVALID`, `INVALID_STATE_TRANSITION`.

**Revision 2026-11-25 (issue #1, §2 error codes):** the §2 `problem_codes` in `contracts/error-codes.json`; the 401 vs 400 rule (§1); `POST /auth/register` always returns 202 with no body (S‑26).

## 0. Freeze schedule
- From B0, `contracts/openapi.json` is **generated from FastAPI route stubs** (real Pydantic request and response models, handlers return 501 `application/problem+json` with `code: "NOT_IMPLEMENTED"`). Request bodies reject unknown fields (422). §2 auth stubs: P0.5 part 2. `ExportStatus.status` is proposed as `pending | ready | failed` (confirm at G5). It is never hand-written, so the frontend can generate its client from day one.
- The contract freezes **per section** when its backend phase passes its gate: auth (§2, §3) at G5, files (§4) at G6, operations, drafts, runs and outputs (§5–§7) at G8. The whole of v1 is frozen at P8.7.
- Until a section is frozen, changes are made by PR with the other developer's review. After it is frozen, changes follow §9.

## 1. Conventions
- **Base URL:** `/api/v1`. The browser always calls the same origin, because Next.js rewrites `/api/*` to the backend in both local and production.
- **Format:** JSON (UTF‑8). Field names are `snake_case`. IDs are UUIDv7 strings. Timestamps are ISO‑8601 UTC (`2026-11-23T10:00:00Z`). Money and decimals are **strings** (`"190.00"`) so no precision is lost.
- **Auth:** the `replora_access` and `replora_refresh` cookies are HttpOnly. The `replora_csrf` cookie is readable, and its value is sent as the `X-CSRF-Token` header on POST, PUT, PATCH and DELETE, **including** `login` and `register` (login CSRF). The client gets the cookie from `GET /auth/csrf` when the app starts and the cookie is missing. The token is rotated after login and logout.
- **Workspace scope:** workspace resources live under `/workspaces/{ws_id}/...`.
- **Pagination:** cursor-based. Request `?limit=25&cursor=<opaque>`; the response has `{ "items": [...], "next_cursor": "…" | null }`. `limit` ≤ 100.
- **Caching:** GET responses carry an `ETag`. The client sends `If-None-Match` and gets a 304 if nothing changed.
- **Idempotency:** `Idempotency-Key: <uuid>` is required on `POST /runs` and `POST /runs/{id}/approve`.
- **Optimistic concurrency:** `PATCH` on drafts and workflows **requires** `If-Match: <etag>`. A missing header gives 428 and a stale ETag gives 412 `PRECONDITION_FAILED`.
- **Correlation:** every response has an `X-Request-ID` header, and problem+json includes it as `correlation_id`.
- **Errors:** RFC 9457 `application/problem+json`:
```json
{ "type": "about:blank", "title": "Validation failed", "status": 422,
  "code": "PORT_TYPE_MISMATCH", "detail": "…", "correlation_id": "01J…",
  "errors": [{ "path": "nodes[2].inputs.left", "code": "PORT_TYPE_MISMATCH", "params": {"expected":"TabularArtifact","got":"TextDocumentArtifact"} }] }
```
  The frontend shows translated messages keyed by `code` (`contracts/error-codes.json`), never `detail`.
- **401 vs 400:** 401 always means "no session (or it expired), go to sign-in": `UNAUTHENTICATED`, or `INVALID_CREDENTIALS` on login, `MFA_CHALLENGE_INVALID` on the challenge. A wrong secret while a session or a challenge exists is **400** (`MFA_CODE_INVALID`, `PASSWORD_INCORRECT`, `TOKEN_INVALID`), and the user stays on the form.
- **Status codes:** 200, 201, 202 (accepted async), 204, 304, 400, 401, 403 (CSRF or authenticated but not allowed in this workspace), 404 (missing **or not yours**), 409 (conflict or idempotency mismatch), 413, 415, 422, 429 (with `Retry-After`), 500.

## 2. Auth
| Method | Path | Body | Response |
|---|---|---|---|
| GET | `/auth/csrf` | — | 204 + sets the `replora_csrf` cookie (no auth needed) |
| POST | `/auth/register` | `{email, password, display_name, locale}` | 202, no body, in every case (S‑26): a new address gets the verification email, an existing account gets a notice email. The client gets the `User` after the first login |
| POST | `/auth/login` | `{email, password}` | 200 `User` + cookies, **or** 200 `{mfa_required: true}` + challenge cookie (see below) |
| POST | `/auth/logout` | — | 204, clears cookies, revokes the session |
| POST | `/auth/refresh` | — (refresh cookie) | 204 + rotated cookies |
| GET | `/auth/me` | — | 200 `Me` = `User` + `memberships[]` |
| PATCH | `/auth/me` | `{display_name?, locale?, theme?, timezone?}` (`timezone` is an IANA name, e.g. `Africa/Cairo`) | 200 `User` |
| POST | `/auth/verify-email` | `{token}` | 204 |
| POST | `/auth/password/forgot` | `{email}` | 202 (always) |
| POST | `/auth/password/reset` | `{token, password}` | 204 |
| POST | `/auth/mfa/enroll` | — | 200 `{otpauth_uri, recovery_codes[]}` (shown once; MFA is not active yet) |
| POST | `/auth/mfa/enroll/confirm` | `{code}` | 204 (activates MFA) |
| POST | `/auth/mfa/challenge` | `{code}` **or** `{recovery_code}` (+ challenge cookie) | 200 `User` + session cookies; the challenge cookie is cleared · 401 `MFA_CHALLENGE_INVALID` · 422 `MFA_CODE_OR_RECOVERY_REQUIRED` (on `body`) when both or neither are sent |
| DELETE | `/auth/mfa` | `{password, code}` | 204 |
| POST | `/auth/me/export` | — | 202 `{export_id}`, then `GET /auth/me/export/{id}` returns `{status, url?}` |
| DELETE | `/auth/me` | `{password}` | 202 (deletion scheduled after the grace period) |
| GET | `/auth/sessions` | — | `Session[]` (my active sessions) |
| DELETE | `/auth/sessions/{id}` | — | 204 (revokes it; revoking the current session also clears its cookies) |

`User = {id, email, display_name, locale: "ar"|"en", theme: "light"|"dark"|"system", timezone, mfa_enabled: bool, email_verified: bool, created_at}`
`Session = {id, user_agent, created_at, expires_at, current: bool}`

**MFA login:** when MFA is enabled, `/auth/login` returns 200 `{mfa_required: true}` and sets a `replora_mfa_challenge` cookie (HttpOnly, Secure, SameSite=Lax, 5 minutes, single use, stored hashed and bound to the user). No session cookies are issued yet. The client then calls `/auth/mfa/challenge`; the backend identifies the user from the challenge cookie. Wrong codes count toward the login throttle (P5.7). A missing, expired or used challenge returns 401 `MFA_CHALLENGE_INVALID`, and the client goes back to the sign-in form.

## 3. Workspaces and members
| Method | Path | Body | Response | Permission |
|---|---|---|---|---|
| GET | `/workspaces` | — | `Workspace[]` (mine) | auth |
| POST | `/workspaces` | `{name}` | 201 `Workspace` | auth |
| DELETE | `/workspaces/{ws}` | — | 204 (deletes the workspace with its files, runs and workflows) · 409 `PERSONAL_WORKSPACE_UNDELETABLE` | owner only |
| GET | `/workspaces/{ws}/members` | — | `Member[]` | any member |
| POST | `/workspaces/{ws}/invitations` | `{email, role}` | 201 `Invitation` | members.manage |
| GET | `/workspaces/{ws}/invitations` | — | `Invitation[]` | members.manage |
| DELETE | `/workspaces/{ws}/invitations/{id}` | — | 204 (revoke) | members.manage |
| POST | `/invitations/accept` | `{token}` | 200 `Workspace` | auth (email must match) |
| PATCH | `/workspaces/{ws}/members/{user_id}` | `{role}` | 200 `Member` | members.manage |
| DELETE | `/workspaces/{ws}/members/{user_id}` | — | 204 | members.manage |
| GET | `/workspaces/{ws}/audit` | `?cursor&limit` | page of `AuditEvent` | audit.read |

`Workspace = {id, name, role, created_at}` · `Member = {user_id, email, display_name, role: "owner"|"admin"|"member"|"viewer"}` · `Invitation = {id, email, role, invited_by, expires_at, status: "pending"|"accepted"|"revoked"|"expired"}`

## 4. Files (direct-to-storage upload)
| Method | Path | Body | Response |
|---|---|---|---|
| POST | `/workspaces/{ws}/files/upload-intent` | `{display_name, size, content_type}` | 201 `{file_id, upload: {url, method: "PUT", headers: {...}, expires_at}}` · 413 `FILE_TOO_LARGE` / `QUOTA_EXCEEDED` |
| *(PUT)* | `upload.url` | raw bytes | 200 (local: backend endpoint; prod: Supabase signed URL) |
| POST | `/workspaces/{ws}/files/{id}/complete` | — | 200 `File` (status `ready` or `rejected` + `rejection_code`) |
| POST | `/workspaces/{ws}/files/samples` | — | 201 `File[]` (the server copies the bundled onboarding sample files into the workspace, status `ready`; no browser upload) |
| GET | `/workspaces/{ws}/files` | `?cursor&limit&type` | page of `File` |
| GET | `/workspaces/{ws}/files/{id}` | — | `File` |
| GET | `/workspaces/{ws}/files/{id}/download` | — | 200 `{url, expires_at}` |
| DELETE | `/workspaces/{ws}/files/{id}` | — | 204 |

`File = {id, display_name, detected_type: "csv"|"xlsx"|…|"zip", size, sha256, status: "pending"|"ready"|"rejected", rejection_code?, members?: [{path, detected_type, size}], uploaded_by, created_at, expires_at}`

**Integrity:** the server computes `sha256` on `complete`, because it reads the file there anyway for magic-byte detection, and a client-supplied hash cannot be trusted. The browser does not hash files. `size` declared at intent must match the stored size.

**Frontend rule:** use the `upload.url`, `method` and `headers` exactly as returned. Never build storage URLs yourself.

**Cross-origin note:** the `upload.url` PUT is the only browser request that may be cross-origin. Every API call is same-origin under `/api`, so the API itself needs no CORS. Locally `upload.url` is a same-origin `/api/v1/...` URL, so `connect-src 'self'` is enough. In production it is a Supabase Storage signed URL, so the CSP `connect-src` adds the storage origin, taken from an environment variable (one CSP code path for every environment). The storage CORS setup is verified in the P8.8 spike.

## 5. Operations (registry)
| Method | Path | Response | Cache |
|---|---|---|---|
| GET | `/operations` | `OperationContract[]` | `public, max-age=3600` |
| GET | `/limits` | `Limits` | `public, max-age=3600` |

Both endpoints are **public**: no session is needed, and the answer is the same for every user (hence the public cache).

`OperationContract = {id, version, title_key, inputs: [Port], outputs: [Port], params_schema (JSON Schema)}` · `Port = {name, artifact_type, required}`
`artifact_type` is one of the 11 kinds (P1.1): `RawFile`, `ArchiveManifest`, `TabularArtifact`, `TextDocumentArtifact`, `PagedArtifact`, `PresentationArtifact`, `ImageArtifact`, `StructuredObjectArtifact`, `ValidationReport`, `ComparisonReport`, `OutputFile`. Ports connect only when the types match exactly.
`Limits = {max_file_size, max_files_per_run, max_nodes, workspace_quota}` (bytes and counts). The frontend reads limits from here and never hard-codes them.

**Supported `params_schema` subset** (so the frontend can render a form from it): `string`, `integer`, `boolean`, `enum`, and `array` of strings. Decimals are `string` with a `pattern`. `x-replora-widget: "column"` means "pick a column from an input port". No `oneOf`, `anyOf` or `$ref`.

## 6. Drafts (planning and validation)
| Method | Path | Body | Response |
|---|---|---|---|
| GET | `/templates` | — | `Template[]` = `{id, title_key, description_key, required_inputs}` (public cache 1 h) |
| POST | `/workspaces/{ws}/drafts` | `{file_ids[], prompt, planner: "template"|"ai", template_id?, share_samples: false}` | 201 `Draft` |
| GET | `/workspaces/{ws}/drafts/{id}` | — | `Draft` + `ETag` |
| PATCH | `/workspaces/{ws}/drafts/{id}` | `{definition}` (the **full** definition) + `If-Match` | 200 `Draft` (re-validated, new plan_hash) · 412 if stale |

**PATCH rule:** the client always sends the complete `definition`. The parameter form edits only parameters, but the request carries the whole definition. The server re-validates it and computes the new `plan_hash` in one place.

`planner: "mock"` exists only in test builds and is never exposed in production.

`Draft = {id, prompt, planner, definition: WorkflowDefinition, plan_hash, explanation: Explanation, ai_disclosure: {sent_fields[], samples_sent: bool}, validation: ValidationReport, created_at}`
`Explanation = {key?, params?, text?}`. The TemplatePlanner returns `key` + `params` only (no free text), and the frontend translates the key. The AI planner (Phase 12) returns `text`, written in `user.locale`.
`ValidationReport = {valid: bool, errors: [Issue], warnings: [Issue]}` · `Issue = {code, path, node_id?, params}`
`WorkflowDefinition` = the JSON Schema in `contracts/schemas/workflow_definition.json` (Phase 1).

## 7. Runs
| Method | Path | Body | Response |
|---|---|---|---|
| POST | `/workspaces/{ws}/runs` | `{draft_id}` **or** `{workflow_id, version, file_ids[]}` | 201 `Run` (state `AWAITING_APPROVAL` or `NEEDS_REVIEW`) |
| POST | `/workspaces/{ws}/runs/{id}/approve` | `{plan_hash}` | 202 `Run` (state `QUEUED`); 409 `PLAN_HASH_MISMATCH` |
| POST | `/workspaces/{ws}/runs/{id}/cancel` | — | 202 `Run` (`CANCEL_REQUESTED`) |
| GET | `/workspaces/{ws}/runs` | `?cursor&limit&state` | page of `RunSummary` |
| GET | `/workspaces/{ws}/runs/{id}` | — | `Run` |
| GET | `/workspaces/{ws}/runs/{id}/events` | `?after=<seq>` | `{events: [RunEvent], last_seq}` |
| GET | `/workspaces/{ws}/runs/{id}/outputs` | — | `OutputArtifact[]` |
| GET | `/workspaces/{ws}/runs/{id}/outputs/{artifact_id}/preview` | `?offset=0&limit=100&status=matched\|value_diff\|missing_left\|missing_right&q=<text>` | `{columns: [Column], rows: [[...]], total, offset}` |
| GET | `/workspaces/{ws}/runs/{id}/outputs/{artifact_id}/download` | — | `{url, expires_at}` |
| GET | `/workspaces/{ws}/runs/{id}/outputs/{artifact_id}/rows/{row}/lineage` | — | `Lineage` |

`Run = {id, state, plan_hash, definition, nodes: [{node_id, operation_id, state, attempt, started_at, finished_at, error_code?, warnings[]}], summary?: {matched, value_diff, missing_left, missing_right}, approved_by?, approved_at?, created_at, finished_at?}`
`state ∈ DRAFT | VALIDATED | AWAITING_APPROVAL | QUEUED | RUNNING | NEEDS_REVIEW | SUCCEEDED | PARTIAL | FAILED | CANCEL_REQUESTED | CANCELLED | EXPIRED`
**State rules:**
- `POST /runs` from a draft whose `validation.valid` is `false` returns 422 `DRAFT_INVALID` with the validation issues in `errors`. No run is created.
- `approve` is allowed **only** in `AWAITING_APPROVAL`. In any other state, including `NEEDS_REVIEW`, it returns 409 `INVALID_STATE_TRANSITION` with `params: {from, action}`.
- `cancel` is allowed in `AWAITING_APPROVAL`, `QUEUED` and `RUNNING`. In a terminal state it returns 409 `INVALID_STATE_TRANSITION`.
- `NEEDS_REVIEW` is resolved by a user decision (for example a date format or a column mapping). The decision produces a new `plan_hash` and returns the run to `AWAITING_APPROVAL`, where it must be approved again. The resolution endpoint is specified together with the transition table (P1.5) at G1.

**Draft shapes (locked at G1):**
- `Column = {name, type: "string"|"decimal"|"integer"|"date"|"boolean", nullable: bool}`
- `RunSummary = {id, state, title, created_at, finished_at?, summary?}`
- `OutputArtifact = {id, name, type, format, size, row_count?, created_at}`
- `Lineage = {sources: [{file_id, member_path?, row, page?}], operations: [{id, version}]}`
- `AuditEvent = {id, actor_id, action, target_type, target_id, created_at}` (§3)
  - `action`: `workspace.created`, `member.invited`, `member.invitation_revoked`, `member.joined`, `member.role_changed`, `member.removed`, `file.uploaded`, `file.downloaded`, `file.deleted`, `workflow.saved`, `workflow.deleted`, `run.created`, `run.approved`, `run.cancelled`, `output.downloaded`, `planner.called`. Auth events (login, logout, reset) are audited too (P5.7) but have no workspace, so this endpoint never returns them.
  - `target_type`: `workspace`, `invitation`, `member` (`target_id` is the user id), `file`, `workflow`, `draft`, `run`, `output`.

`RunEvent = {seq, type: "state_changed"|"node_started"|"node_finished"|"warning", node_id?, payload, created_at}`

**Polling contract:** while the state is `QUEUED`, `RUNNING` or `CANCEL_REQUESTED`, poll `events?after=last_seq` every 1 s, backing off to 5 s. Stop when the state is terminal. (SSE may be added later without breaking this.)

## 8. Workflows and replay (Phase 13)
| Method | Path | Body | Response |
|---|---|---|---|
| POST | `/workspaces/{ws}/workflows` | `{name, draft_id}` | 201 `Workflow` (version 1) |
| GET | `/workspaces/{ws}/workflows` | `?cursor&limit&q` | page of `Workflow` |
| GET | `/workspaces/{ws}/workflows/{id}` | — | `Workflow` + `versions[]` |
| GET | `/workspaces/{ws}/workflows/{id}/versions/{v}` | — | `WorkflowVersion` |
| POST | `/workspaces/{ws}/workflows/{id}/replay-check` | `{file_ids[]}` | `{compatible: bool, drift: [{input, expected_columns, found_columns, suggestions}]}` |
| POST | `/workspaces/{ws}/workflows/{id}/versions` | `{base_version, mapping}` | 201 `WorkflowVersion` (new version) |
| DELETE | `/workspaces/{ws}/workflows/{id}` | — | 204 (soft delete) |

## 9. Change Request process (after a freeze)
1. Open a PR that edits `contracts/` **only**, with the label `contract-change`, describing the change, the reason and the impact on the other side.
2. It must be backward compatible within v1 (add optional fields or new endpoints). A breaking change requires `/api/v2`.
3. Both developers approve. The backend updates fixtures and tests, and the frontend regenerates the client. The merge happens only when both sides are green.

## 10. Shared artifacts in `contracts/`
```
contracts/
├── openapi.json            generated from the backend route stubs (B0 onward), committed, CI drift check
├── error-codes.json        every error code (frontend translates each one; parity test)
├── schemas/                JSON Schemas for domain models (Phase 1)
└── fixtures/
    ├── auth/*.json         request/response pairs
    ├── files/*.json
    ├── drafts/*.json
    ├── runs/*.json         including every run state
    └── files-binary/       sample ZIP/CSV/JSON used by both backend tests and E2E
```
- **Backend:** tests assert that the real responses validate against `openapi.json` and match the fixture shapes.
- **Backend:** fixtures for every §2 auth endpoint and `error-codes.json` are delivered in B0/B1, and B5 tests assert that real responses match them.
- **Frontend:** a CI check asserts that `ar.json` and `en.json` have the same keys and that every code in `error-codes.json` has a translation in both languages.
- **Frontend:** the MSW handlers serve these fixtures, and the TS types are generated from `openapi.json` (`pnpm gen:api`).
