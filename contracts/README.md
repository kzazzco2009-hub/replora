# contracts/

Shared between backend and frontend. Changes need both developers' review (CODEOWNERS).

| File | Source | Rule |
|---|---|---|
| `openapi.json` | **Generated** from the FastAPI app (`cd backend && uv run python -m app.export_openapi`). Never edit by hand. | CI fails if it differs from the code (`--check`). Regenerate and commit it in every API PR. |

The frontend generates its types from `openapi.json` (`pnpm gen:api`). Further shared artifacts (`error-codes.json`, `schemas/`, `fixtures/`) are added as their phases land; see `docs/api_contract.md` §10.
