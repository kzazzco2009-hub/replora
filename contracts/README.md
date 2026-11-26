# contracts/

Shared between backend and frontend. Changes need both developers' review (CODEOWNERS).

| File | Source | Rule |
|---|---|---|
| `openapi.json` | **Generated** from the FastAPI app (`cd backend && uv run python -m app.export_openapi`). Never edit by hand. | CI fails if it differs from the code (`--check`). Regenerate and commit it in every API PR. |
| `error-codes.json` | Hand-written: `problem_codes`, `validation_codes`, `rejection_codes`. | Every code the API sends is listed in the same PR; backend tests check it. |
| `fixtures/auth/<operationId>.json` | Hand-written example responses for every §2 endpoint: `{"<scenario>": {"status", "body"}}`, always with an `ok` scenario. `body: null` means no body. | `backend/tests/unit/test_auth_fixtures.py` validates each body against `openapi.json` and each error `code` against `error-codes.json` (with its status). |

The frontend generates its types from `openapi.json` (`pnpm gen:api`), and its MSW handlers can serve `fixtures/` with one switch per scenario (P9.6). `schemas/` (the workflow JSON Schema) comes in Phase 1; see `docs/api_contract.md` §10.
