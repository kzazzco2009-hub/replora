# Replora

AI-assisted file workflow automation. Describe a task in Arabic or English, review the proposed plan of typed operations, approve it, and get reconciled outputs with row-level lineage.

## Repository layout
| Path | Owner | Contents |
|---|---|---|
| `backend/` | Developer A | FastAPI, Python 3.14, `uv` (from P0.3) |
| `frontend/` | Developer B | Next.js, TypeScript, Tailwind v4, `pnpm` (from P0.4) |
| `contracts/` | both | OpenAPI, JSON schemas, fixtures, error codes (from P0.5) |
| `docs/` | both | Plan, testing, security, design, API contract, decisions, session log |

Start with `docs/plan.md`, then `docs/session_log.md` for the current status.

## Toolchain
- Python 3.14 (`.python-version`) with [uv](https://docs.astral.sh/uv/): always `uv run …` and `uv add …`.
- Node 26 LTS (`.nvmrc`) with pnpm 12.23.0 (pinned in `package.json` → `packageManager`).
- Local setup: copy `.env.example` to `.env` and fill in the values. `.env` is git-ignored.
- Git hooks: install [pre-commit](https://pre-commit.com) (`uv tool install pre-commit`) and gitleaks (on PATH), then run `pre-commit install` once per clone. On every commit the hooks run gitleaks, ruff (lint and format), and the frontend ESLint, prettier and typecheck. `.gitleaks.toml` adds project rules (for example OpenRouter keys) on top of the gitleaks defaults, and CI uses it too.

### Backend (from `backend/`)
```
uv sync                                                  # install the locked dependencies
uv run uvicorn app.main:create_app --factory --reload    # http://localhost:8000/api/v1/health
uv run pytest                                            # tests
uv run python -m app.export_openapi                      # regenerate contracts/openapi.json (commit it)
uv run ruff check . && uv run ruff format --check .      # lint
```
### Frontend (from the repo root)
```
pnpm install --frozen-lockfile    # install the locked dependencies
pnpm -C frontend dev              # http://localhost:3000
pnpm -C frontend run gen:api      # regenerate src/lib/api/schema.d.ts after a contract change (commit it)
```

### Local dev, both together
Run the backend (`uvicorn` above, port 8000) and `pnpm -C frontend dev` in two terminals, and open `http://localhost:3000`. In development, Next.js rewrites `/api/*` to the backend (`BACKEND_ORIGIN`, default `http://localhost:8000`). So the browser stays on one origin, and cookies and CSRF work without CORS. More frontend commands: `frontend/README.md`.

## Contributing
- Every change reaches `main` through a small PR (≤ 400 lines) reviewed by the other developer. No direct pushes and no self-merge.
- CI must be green. See `.github/pull_request_template.md`.
