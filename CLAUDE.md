# Replora — instructions for Claude Code

Replora is a bilingual (Arabic RTL and English) SaaS app for repetitive file work. It turns a task description into a typed workflow of known operations. The user approves the workflow, bound to a `plan_hash`, and it runs with row-level lineage. **No model-generated code is ever executed.**

## Start of every session
1. Read **`docs/session_log.md`** (Current status → Next step) before anything else. The frontend developer keeps their own session log for the frontend track.
2. Then `git fetch --all --prune`, switch to the working branch and `git pull --ff-only`. Work may have been pushed from another machine.
3. Plans: `docs/plan.md` (master), `docs/backend_plan.md`, `docs/frontend/` (frontend package), `docs/testing.md`, `docs/security.md`, `docs/design.md`, `docs/api_contract.md`, and `docs/decisions.md`.

## Layout and ownership
| Path | Owner |
|---|---|
| `backend/` | Developer A (backend): FastAPI, Python 3.14, uv |
| `frontend/` | Developer B (frontend): Next.js, TypeScript 6.0.3, Tailwind v4, pnpm |
| `contracts/`, `docs/`, `.github/`, root files | both developers (a change needs the other developer's review) |

## Process (mandatory)
- Work incrementally in small steps, and validate each step before the next.
- Mark a plan step `[x]` only after its tests pass and the evidence (command plus result) is in the session log.
- **Phase gates:** a phase is done only when all its steps, tests (`testing.md`) and security items (`security.md`) are verified. Then stop, report, and **ask the gate approver for permission** before starting the next phase: Developer A (the owner) for backend gates, Developer B for frontend gates, and both for the shared gates (0, 17, 18, 19).
- Check the production compatibility checklist (`docs/plan.md` §4) at every step.
- End of session: update the session log, commit and push. Never leave uncommitted work, because the next session may be on another machine.

## Code style (mandatory)
- Do not overengineer. Do not program defensively. Use exception handlers only when needed.
- Short modules and short functions with clear names. Use concise docstrings, and few comments outside them.
- Use the latest library APIs for the pinned versions.
- **Python:** always `uv run …` and `uv add …`, never `python …` or `pip install …`.
- **Frontend:** `pnpm`, strict TypeScript, no `any`.
- **Debugging:** find and prove the root cause before fixing. Test one thing at a time. No workarounds.

## Contract
- `contracts/openapi.json` is **generated** from the FastAPI route stubs, never hand-written. CI checks it for drift.
- The contract freezes per section (auth at G5, files at G6, runs and outputs at G8, all of v1 at P8.7). After a freeze, a change needs a Change Request (`docs/api_contract.md` §9).
- Error messages shown to users are keyed by the error `code` (`contracts/error-codes.json`), with both AR and EN translations.

## Git and GitHub
- Branch from `main`. Make small PRs (≤ 400 lines, short-lived branches). **No direct push to `main` and no self-merge.** Branch protection is a manual rule until the repo moves to an organization.
- Never commit `.env` or any secret. Run `gitleaks git .` before pushing; CI runs it too.
- Use the PR template (`.github/pull_request_template.md`), including the tested SHA, test commands and results, and the security impact.
- Coordinate with the other developer through GitHub Issues and PR comments, in English. Record final decisions in `docs/decisions.md`.

## Machines and tools (Windows)
- The owner works from more than one machine. **If a tool is missing, give the owner the install commands instead of installing it yourself.**
- Pinned versions: `.python-version` (3.14), `.nvmrc` (26.13.1), `package.json` → `packageManager` (pnpm 12.23.0). The lockfiles (`uv.lock`, `pnpm-lock.yaml`) are the source of truth.
- Keep the clone outside OneDrive (for example `D:\Projects\replora`).
- `gh` works from PowerShell, not from Git Bash.
- After a winget install, a running session does not see the new PATH. Reload it with `$env:Path = [Environment]::GetEnvironmentVariable('Path','User') + ';' + [Environment]::GetEnvironmentVariable('Path','Machine')`.
- For multi-line git commit messages in PowerShell, write the message to a file and run `git commit -F <file>`.
