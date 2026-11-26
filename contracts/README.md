# contracts/

Shared between backend and frontend. Changes need both developers' review (CODEOWNERS).

| File | Source | Rule |
|---|---|---|
| `openapi.json` | **Generated** from the FastAPI app (`cd backend && uv run python -m app.export_openapi`). Never edit by hand. | CI fails if it differs from the code (`--check`). Regenerate and commit it in every API PR. |
| `error-codes.json` | Hand-written: `problem_codes`, `validation_codes`, `rejection_codes`, and `workflow_codes` (the validator's `Issue` codes, Phase 2). | Every code the API sends is listed in the same PR; backend tests check it. |
| `schemas/<Name>.schema.json` | **Generated** JSON Schemas (draft 2020-12) of the domain models in `backend/app/core/` (`cd backend && uv run python -m app.export_schemas`). Never edit by hand. | CI fails if they differ from the models (`--check`). |
| `fixtures/domain/<Name>.json` | Hand-written golden cases per schema: `valid`, `invalid`, and `invalid_backend_only` (a cross-field rule JSON Schema can't express, such as `ValidationReport.valid` without errors). | `backend/tests/unit/test_domain_schemas.py`: the schema accepts `valid` and rejects `invalid`; the backend model rejects both invalid groups; valid cases round-trip (T1.1, T1.6). |
| `fixtures/auth/<operationId>.json` | Hand-written example responses for every §2 endpoint: `{"<scenario>": {"status", "body"}}`, always with an `ok` scenario. `body: null` means no body. | `backend/tests/unit/test_auth_fixtures.py` validates each body against `openapi.json` and each error `code` against `error-codes.json` (with its status). |

The frontend generates its types from `openapi.json` (`pnpm gen:api`), and its MSW handlers can serve `fixtures/` with one switch per scenario (P9.6). See `docs/api_contract.md` §10.
