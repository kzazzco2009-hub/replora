# Replora — Full Plan Review (v1 → v1.1)

**Date:** 2026-11-23 · **Reviewer stance:** senior engineer reviewing the plan before any code is written.
**Scope:** `plan.md`, `testing.md`, `security.md`, `design.md`, `api_contract.md`, `backend_plan.md`, `frontend_plan.md`.
**Outcome:** the plan is sound in its core, but 24 gaps were found. All of them are now **fixed in the documents (v1.1)** or raised as owner decisions (D11–D14).

## 1. Verdict

| Area | v1 | v1.1 | Notes |
|---|:-:|:-:|---|
| Architecture fit for the product | ✅ | ✅ | Typed DAG, registry-only operations and an approval bound to plan_hash are right for a trust-sensitive file tool. |
| Functional completeness | ⚠️ | ✅ | No requirement traceability. No user-facing planner before Phase 12. Missing invites, account deletion and onboarding. |
| Production feasibility (Vercel + Supabase) | ⚠️ | ✅ | Biggest risk: the serverless worker chain and function bundle size were only checked at the end. A **feasibility spike** has been added at Phase 8 (staging only). |
| Non-functional coverage | ⚠️ | ✅ | Missing availability, recovery point and recovery time (RPO/RTO), browser support, cost and bundle-size targets. Observability started too late. |
| Security | ✅ | ✅ | Strong. Added MFA, account deletion and export, SBOM, log retention, and malware-scanning risk. |
| Testing | ✅ | ✅ | Strong. Added cross-browser, staging load, onboarding and concurrency (If-Match) tests. |
| UX and design | ✅ | ✅ | Strong. Added first-run onboarding with sample data, timezone handling and Arabic CSV opening in Excel. |
| Process for 2 developers | ⚠️ | ✅ | The "one gate at a time" rule conflicted with parallel tracks. A per-track gate rule has been added. |
| Schedule realism | ❌ | ⚠️ | 27 weeks × 2 × 20 h ≈ 1,080 h vs the original estimate of 1,800–2,560 h. The timelines are now marked as MVP-first, with a realistic full-scope range. |

**Conclusion:** after the v1.1 fixes, the plan is suitable and functional for this project, with one condition: the **Phase 8 feasibility spike must pass**. If it fails, D9 (the production worker) changes to a container worker, and only Phase 19 is affected.

## 2. Findings and fixes

### Functional
| # | Finding | Severity | Fix (where) |
|---|---|---|---|
| F1 | No list of functional requirements, so coverage cannot be proven. | High | Added an **FR traceability table** linking each requirement to phases and tests (plan.md §1b). |
| F2 | Before Phase 12 the only planner is the `MockPlanner` (test-only), so real users of the MVP have no way to get a plan. | **High** | Added a **TemplatePlanner**: user-facing, rule-based templates such as "reconcile two files" and "merge files" (P3.9, API `planner: "template"`). |
| F3 | Inviting a member who has no account yet is not defined. | Medium | Invite token plus accept flow (P5.9, API §3, T5.13). |
| F4 | No account deletion or data export (privacy law expectation). | High | P5.10, API `DELETE /auth/me` and `POST /auth/me/export`, S‑29, T5.14. |
| F5 | The approval expiry time is undefined. | Medium | AWAITING_APPROVAL expires after 24 h (configurable) (P3.6). |
| F6 | The 10-files-per-run limit and the per-workspace storage quota are not enforced anywhere. | Medium | P6.7, T6.10. |
| F7 | Money is compared without a defined precision. Ambiguous dates (03/04) would be guessed. | **High** | `Decimal` everywhere, tolerance as a parameter, ambiguous dates make the run NEEDS_REVIEW (P7.5, T7.10, T7.11). |
| F8 | An Arabic CSV opened in Excel shows mojibake without a UTF‑8 BOM. | **High** (core audience) | Excel-compatible CSV (UTF‑8 with BOM) by default (P7.5, T7.12). |
| F9 | Two tabs editing the same draft overwrite each other silently. | Medium | `If-Match` / ETag required on PATCH; a stale ETag gets 412 (API §1, T8.9). |
| F10 | There is no first-run onboarding, so a new user faces an empty app. | High (adoption) | "Try with sample files" onboarding (P10.9, T10.11). |
| F11 | Dates are shown without the user's timezone. | Low | Timezone stored on the user and display uses `Intl` (P10.10). |
| F12 | Legal pages are missing (privacy policy and terms), and there is no public landing page. | Medium | P17.8 (minimal, bilingual). |
| F13 | Out-of-scope items are not stated, so scope creep is likely. | Medium | Added an "Out of scope for v1" list (plan.md §1c). |

### Non-functional and production
| # | Finding | Severity | Fix |
|---|---|---|---|
| N1 | **The Vercel worker-chaining mechanism is unproven.** Vercel Cron is per-minute at best, and background execution after the response is not guaranteed for Python. | **Critical** | **P8.8 production feasibility spike** on staging (Vercel preview + Supabase staging): chaining, pooler, signed upload, bundle size, cold start. The result decides D9 before the frontend is integrated. |
| N2 | Python function bundle limit (~250 MB unzipped). A heavy stack (pandas + numpy + pdf + office libraries) may exceed it. | High | Decision D13 (stdlib `csv` + `Decimal`, polars only if it is measured as needed). Bundle size is a non-functional requirement (NFR‑13) checked in the spike. |
| N3 | Observability (logs, correlation IDs) only arrived in Phase 19, which makes debugging blind until then. | High | Moved to P0.11 (structured JSON logs and correlation IDs from day one). |
| N4 | No availability, RPO or RTO targets. | Medium | NFR‑9 (99.5 % monthly), NFR‑10 (RPO ≤ 24 h, or ≤ 5 min with PITR; RTO ≤ 4 h). |
| N5 | No browser support matrix, and E2E ran on Chromium only. | Medium | NFR‑11. Playwright now includes WebKit (Safari/iOS) and Firefox (T17.7). |
| N6 | No cost target (Vercel, Supabase, OpenRouter). | Medium | NFR‑12 budget, plus cost alerts (P19.5). |
| N7 | The load test ran only on localhost, which does not reflect serverless cold starts or pooler behavior. | High | Load test repeated on staging (P18.8, T18.6). |
| N8 | The data retention period is undefined. | Medium | Decision D11 (recommend 30 days for inputs, 90 days for outputs, audit kept 1 year). |

### Security
| # | Finding | Fix |
|---|---|---|
| X1 | No MFA for owners and admins. | S‑28: optional TOTP (decision D12; recommended for owner and admin), T5.15. |
| X2 | Uploaded originals can be downloaded by other members, but no malware check is done. | S‑47: an accepted risk for v1 (files are parsed, never executed, and downloaded with `attachment`). Add ClamAV in the container worker if D9 leads to one. |
| X3 | No SBOM or provenance. | S‑86: CycloneDX SBOM per release. |
| X4 | Log retention and PII-in-logs policy not defined. | S‑87: logs kept 30 days, PII scrubbing tested. |

### Process and schedule
| # | Finding | Fix |
|---|---|---|
| P1 | "Don't start the next phase until the gate passes" conflicts with two developers working at the same time. | Gate rule per track: each track's phase gate is approved separately, and integration milestones need both. Shared phases need both (plan.md §2). |
| P2 | Schedule too optimistic for the full scope. | Timelines are labelled **MVP-first**. MVP through G13 ≈ 14 weeks. Full scope through G19 is realistically **9–12 months** at 2 × 20 h/week. Re-baseline after G3. |
| P3 | Decision D14 (legal jurisdiction for data, such as Egypt PDPL 151/2020 and GDPR if there are EU users) was missing. | Added D14. It affects the Supabase region and the privacy policy. |

## 3. What was deliberately **not** added (to avoid overengineering)
- Microservices, Kubernetes, event sourcing or GraphQL: not needed at this scale.
- Real-time server push (SSE or WebSockets): polling with backoff is enough. The contract allows SSE later.
- Multi-region and high availability: the 99.5 % target does not justify it.
- A custom admin back-office: Supabase dashboard and audit logs are enough for v1.
- Mutation testing and a formal threat-modeling tool: the security.md per-phase checklist covers the need.
