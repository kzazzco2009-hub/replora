# Developer A — Backend Track

**Owns:** `backend/**`, DB schema and migrations, worker, storage, API security, and `contracts/openapi.json` generation.
**Co-owns:** `contracts/**` (with Developer B), Phase 17 hardening, and Phase 18/19 production.
**Stack:** Python 3.13+ · `uv` · FastAPI · Pydantic v2 · SQLAlchemy 2 · Alembic · pytest/hypothesis/schemathesis.
**Rules:** all MANDATORY rules in `plan.md` §2 apply. The phase gates, tests (`testing.md`) and security items (`security.md`) apply unchanged. Each phase ends with a request for the owner's permission.

## Track timeline (parallel with frontend_plan.md)

| Week* | Backend phase | Delivers to frontend | Sync point |
|---|---|---|---|
| 1 | B0 = Phase 0 (backend half) + **api_contract.md draft** | contract draft, `error-codes.json` v0, fixtures skeleton | **G0 — both agree the contract** |
| 2–3 | B1 = Phase 1 contracts | `contracts/schemas/*` + domain fixtures | FE renders the rail from fixtures |
| 3–4 | B2 = Phase 2 validator | error codes + validation fixtures | FE maps codes to stations |
| 4–6 | B3 = Phase 3 engine | run-state fixtures for every state | FE run-detail states |
| 6–7 | B4 = Phase 4 persistence | — | — |
| 7–8 | B5 = Phase 5 auth | real auth endpoints | **I1 — auth integration** |
| 8–9 | B6 = Phase 6 files | real upload flow | **I2 — upload integration** |
| 9–10 | B7 = Phase 7 first pipeline | acceptance ZIP in `contracts/fixtures/files-binary` | FE results screen with real data |
| 10–11 | B8 = Phase 8 API + worker, **OpenAPI frozen** | full MVP API | **I3 — end-to-end MVP (G10)** |
| 12–13 | B12 = Phase 12 planner (backend) | `planner: "ai"` + disclosure fields | **I4** |
| 13–14 | B13 = Phase 13 replay (backend) | workflows + replay-check endpoints | **I5** |
| 15–22 | B14–B16 = Phases 14–16 formats | new `detected_type` values + warnings codes | FE adds format icons and warning copy |
| 23–24 | Phase 17 (shared) | perf and security fixes | joint |
| 25–26 | Phase 18 Supabase (lead) | staging URL | **I6 — staging** |
| 27 | Phase 19 (backend deploy) | production API | joint go-live |

\*Weeks assume ~20 h/week per developer. They are illustrative only and are re-baselined after B3.

## Phases (steps reference `plan.md`; tick here **and** in plan.md)

### B0 — Foundation (backend half of Phase 0)
- [x] P0.1 versions (backend libraries)
- [x] P0.2 git and `.gitignore`
- [x] P0.3 FastAPI health
- [ ] P0.5 OpenAPI export *(in progress: export and drift check #6; §2 #8; §3 #10; §4 #11; §5 in #28; §6–§8 next)*
- [x] P0.6 pre-commit (ruff, gitleaks) *(#14; the frontend hooks in #19)*
- [x] P0.7 backend CI jobs (SQLite now, Postgres job added in B4) *(backend job, `openapi.json` drift check, pip-audit, gitleaks)*
- [x] Write the **api_contract.md draft** together with Developer B *(agreed at G0 in issue #1; `docs/api_contract.md`)*
- [x] Commit `contracts/error-codes.json` v0 *(#16)*
- [ ] Tests: [x] T0.1 · [x] T0.3 (backend job) · [x] T0.4 · [x] T0.5 · [x] T0.6
- [ ] Security S‑01…S‑05 verified *(S‑02 partly; see `testing.md` and `security.md`)*
- [ ] **Gate G0** (shared: both tracks green)

### B1 — Core contracts → Phase 1 (P1.1–P1.7) · T1.* · S‑10, S‑11 · **Gate G1**
### B2 — Registry and validator → Phase 2 (P2.1–P2.6) · T2.* · S‑12 · **Gate G2**
### B3 — Engine → Phase 3 (P3.1–P3.9, including the user-facing TemplatePlanner) · T3.* · S‑13 · **Gate G3**
### B4 — Persistence → Phase 4 (P4.1–P4.7) · T4.* · S‑14, S‑15 · **Gate G4**
### B5 — Auth → Phase 5 (P5.1–P5.11: invitations, export and deletion, MFA) · T5.* · S‑20…S‑29 · **Gate G5 → I1 with frontend**
### B6 — Files → Phase 6 (P6.1–P6.6) · T6.* · S‑30…S‑36 · **Gate G6 → I2**
### B7 — First pipeline → Phase 7 (P7.1–P7.5) · T7.* · S‑37 · **Gate G7**
### B8 — API and worker → Phase 8 (P8.1–P8.9, including the **P8.8 production feasibility spike** that decides D9) · T8.* · S‑16, S‑17, S‑50…S‑53 · **Gate G8 → I3**
### B12 — AI planner → Phase 12 (P12.1–P12.4) · T12.1–T12.6 · S‑70…S‑74 · **Gate G12 (with FE P12.5) → I4**
### B13 — Replay → Phase 13 (P13.1–P13.3) · T13.1–T13.3 · **Gate G13 (with FE P13.4) → I5**
### B14 / B15 / B16 — Formats → Phases 14, 15, 16 (backend steps) · T14–T16 · S‑38, S‑39, S‑41…S‑43 · **Gates G14–G16**
### Shared — Phase 17 (backend: P17.1–P17.3, P17.5–P17.6) · Phase 18 (lead, all steps) · Phase 19 (P19.1 backend, P19.2–P19.3, P19.5, P19.7)

## What the backend guarantees to the frontend
1. Every endpoint in `api_contract.md` has committed request and response fixtures **before** its implementation PR merges.
2. Every new error code is added to `contracts/error-codes.json` in the same PR.
3. `contracts/openapi.json` is regenerated in every API PR. The CI drift check enforces this.
4. A local seed command (`uv run python -m app.seed`) creates a demo user, workspace and the acceptance files, so the frontend developer can run the real stack in one step.
5. No breaking change to v1 after P8.7 (Change Request process, api_contract.md §9).
