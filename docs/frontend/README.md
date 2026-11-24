# Replora — Frontend Planning Package

> **In the repo:** this package lives in `docs/frontend/`. The shared documents are one level up: `../api_contract.md` and `../design.md` (single copies), plus `../decisions.md` and the master `../plan.md`. The frontend session log is kept by Developer B.

Welcome. This folder holds everything the **frontend developer (Developer B)** needs to build the Replora web app in parallel with the backend developer (Developer A, the project owner).

## What Replora is
Replora is a SaaS tool for repetitive file work. A user uploads business files (CSV, Excel, JSON, ZIP, PDF…) and describes what they want. Replora proposes a step-by-step plan (a pipeline of known operations), checks it, and shows it for review. The user approves it explicitly, the plan runs, and the user gets results that can be traced row by row. A saved plan can run again on next month's files.
The first real use case is **reconciling orders with payments** (matched, different, missing on either side).

The UI is **bilingual (Arabic RTL and English LTR)**, has **light and dark modes**, and is **responsive for phone, tablet and laptop**.

## Files in this package (read them in this order)

| File | What it is |
|---|---|
| `README.md` | This file. |
| `plan.md` | **Your plan.** Rules, stack, phases F0–F11 plus shared phases, steps with checkboxes, gates, integration milestones. |
| `../design.md` | The design system and UX spec (tokens, typography, RTL, responsive layouts, screens, copy, accessibility, the UI iteration protocol). |
| `../api_contract.md` | The API contract between frontend and backend. It is the single source of truth for every endpoint and payload. |
| `testing.md` | All frontend tests per phase (unit, E2E, accessibility, performance, cross-browser) and the non-functional targets. |
| `security.md` | Frontend security controls per phase (XSS, CSP, cookies, open redirect, upload safety…). |
| `session_log.md` | **Your progress log.** Read it at the start of every session and update it at the end. |

## How we work together
1. **Contract first.** We agree `api_contract.md` at Gate G0, before any feature code. After that, `contracts/` in the repo is the source of truth.
2. **Until the backend is ready, you build against mocks.** MSW serves the fixtures in `contracts/fixtures/`, and the TypeScript types are generated from `contracts/openapi.json`.
3. **One repo, separate folders.** You own `frontend/**` and the backend developer owns `backend/**`. `contracts/**` is shared and needs both approvals.
4. **Small PRs** (≤ 400 lines, branches ≤ 2 days). The other developer reviews every PR, and nobody merges their own.
5. **Phase gates.** At the end of each of your phases, all steps, tests and security items must be done and logged. Then ask the project owner for permission before starting the next phase.
6. **Integration milestones** (I1–I6). We pair for half a day each time to connect the real API.
7. **Contract problems** become a Change Request (`api_contract.md` §9), never a workaround in the client.

## The repository layout you will see
```
replora/
├── backend/      Developer A — FastAPI (Python, uv)
├── frontend/     YOU — Next.js
├── contracts/    shared — openapi.json, error-codes.json, schemas/, fixtures/
├── docs/         shared — plans, API contract, design, decisions (frontend package in docs/frontend/)
└── .github/      CI, CODEOWNERS, PR template
```
