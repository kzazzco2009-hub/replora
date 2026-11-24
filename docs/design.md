# Replora — Design System and UX Spec

Implemented in Phases 9–11 (and the UI parts of 12, 13 and 16). The product is **bilingual (Arabic RTL and English LTR)** with **light and dark modes**, and it is responsive for **phone, tablet and laptop**.

## 1. Brief

- **Subject:** a file workbench. People drop in messy business files (sales exports, payment logs, invoices), describe what they want in their own words, check a proposed pipeline, approve it, and get a clean, traceable result.
- **Audience:** owners of small businesses and online shops, accountants and office admins in Arabic- and English-speaking markets. They know their data well, but they are not engineers.
- **Primary job of the UI:** make a machine-built plan **legible enough to trust** before it runs, and make the result **explainable row by row** after it runs.
- **Emotional target:** calm and in control, with the precision of a well-kept ledger. Nothing should feel magical or hidden.

## 2. Design direction: "The sorting desk"

The world of this product is the back office: ledgers, stamped approvals, sorting trays, matched and unmatched slips. The design borrows the **clarity of a ledger** (aligned figures, clear columns, status marks) and the **approval stamp** (one decisive, warm action color). It avoids both the generic AI chat look and a dense spreadsheet clone.

**Signature element (where the boldness goes): the pipeline rail.**
A workflow is drawn as a continuous rail. Files enter at the start, operations sit on the rail as stations, and the results leave at the end. Each connection is colored by the **artifact type** that flows through it (table, text, document, image…). On laptop the rail runs horizontally, following reading direction (left→right in EN, right→left in AR). On phone and tablet it runs vertically. During a run, the rail fills station by station. **This is the one orchestrated motion moment in the product.** Everything else stays quiet.

### Plan review against generic defaults (what changed and why)
- *First idea:* a cream background with a serif display and a clay accent. **Rejected.** That is the most common AI-generated look, and a serif display fights Arabic typography.
- *Second idea:* a dark UI with a neon-green "success" accent. **Rejected.** It is a cliché, and it reads as a developer tool, not a back-office tool.
- *Third idea:* identical rounded cards for everything. **Rejected.** Hierarchy now comes from the rail, tables and spacing. Cards are only used for things you can pick up (a file, a saved workflow).
- *Kept:* a cool mineral neutral base, a deep **petrol** ink-blue for structure, and a **saffron** "stamp" reserved for approval and attention. Saffron is familiar across the region (spice markets, official stamps). Petrol reads as trustworthy without being corporate blue.

## 3. Tokens

### Color (CSS variables; Tailwind v4 `@theme` maps to them)

| Token | Role | Light | Dark |
|---|---|---|---|
| `--bg` | app background (gypsum) | `#EEF1EF` | `#0D1B1F` |
| `--surface` | panels, tables | `#FFFFFF` | `#13262B` |
| `--surface-raised` | dialogs, menus | `#FFFFFF` | `#1A3137` |
| `--ink` | primary text | `#17232B` | `#E3ECEA` |
| `--ink-muted` | secondary text | `#4E5F66` | `#9DB2B0` |
| `--line` | borders and dividers | `#D3DBD8` | `#28434A` |
| `--petrol` | primary actions, focus, rail | `#0E5E6F` | `#4FB0C0` |
| `--petrol-contrast` | text on petrol | `#FFFFFF` | `#06171B` |
| `--saffron` | approval stamp, attention | `#D99A0B` | `#F0B43A` |
| `--saffron-contrast` | text on saffron | `#1E1600` | `#1E1600` |
| `--ok` | matched / succeeded | `#237A57` | `#5CC594` |
| `--diff` | value_diff / partial | `#A86400` | `#F2A64A` |
| `--missing` | missing / failed | `#B3261E` | `#F2867E` |
| `--review` | needs review | `#5B4BC4` | `#A99CF5` |
| `--focus-ring` | 2 px outline + 2 px offset | `--petrol` | `--petrol` |

**Artifact type colors** (rail connections and port dots): Table `#0E5E6F`/`#4FB0C0`, Text `#6A5A3E`/`#CDB98F`, Document `#7A3E6B`/`#D59AC6`, Image `#2F6E2F`/`#8FD08F`, Archive `#4E5F66`/`#9DB2B0`, Structured `#3D4DA8`/`#9AA6EE`.

**Rules**
- Status is **never shown by color alone**. It always has an icon and a text label.
- All text/background pairs meet WCAG AA (4.5:1 for body, 3:1 for large text and UI). An automated test checks this (T11.3).
- Dark mode is designed, not inverted. Surfaces are lifted with lighter tones, not shadows.
- Theme: follow the system by default. The user can override it (Light, Dark, System) in the header and in settings. It is persisted in a cookie so the server renders the correct theme with no flash.

### Typography
- **Primary family: Readex Pro** (variable, designed for Arabic and Latin together, weights 200–700). One family keeps AR and EN harmonized. It is loaded with `next/font/google`, subsetted to `arabic` and `latin`.
- **Data and IDs: JetBrains Mono** is used only for machine values (hashes, IDs, raw cell previews in debug views). It is not used for labels.
- Figures: `font-variant-numeric: tabular-nums` in tables and money columns.
- **Scale (major third, 1.25):** 12 / 14 / **16 base** / 20 / 25 / 31 / 39 px.
- **Line height:** Latin body 1.5 and Arabic body **1.7** (Arabic ascenders and descenders need room). Headings 1.2 (EN) and 1.35 (AR).
- **Line length** at most 72 characters for prose.
- Weights: 400 body, 500 labels and buttons, 600 headings. Headings use sentence case. Labels are never all caps (all caps also has no meaning in Arabic).
- Arabic is never letter-spaced (it breaks the connected letters). Latin headings use −0.01em tracking.

### Space, shape, elevation
- 4 px base grid: 4, 8, 12, 16, 24, 32, 48, 64.
- The radius follows hierarchy, not one value for everything: inputs and buttons 8 px, panels 12 px, dialogs 16 px, status chips fully round. Table cells have no radius.
- Elevation is used only for overlays (menus, dialogs, sheets). Panels are separated by `--line` borders and spacing.
- Icons: Lucide, 20 px, 1.75 stroke. Direction-bearing icons (arrows, chevrons, "next") **flip in RTL**. Icons that show real-world objects (download, clock) do not.

### Motion
- Durations: 120 ms (press and hover feedback), 200 ms (open and close), 400 ms (the rail station fill).
- Motion is used only when it answers a user action (a sheet opening, a row expanding, an approval confirming), plus the single rail-fill moment during runs.
- `prefers-reduced-motion`: transitions become instant fades, and skeletons are static (no shimmer).

## 4. Layout and responsive rules

| Breakpoint | Width | Navigation | Content |
|---|---|---|---|
| Phone | < 640 px | bottom tab bar (Home, New run, Runs, Files, More) | single column, sticky primary action at bottom, sheets instead of dialogs |
| Tablet | 640–1023 px | collapsible icon rail (start side) | 1–2 columns, side panel becomes an overlay sheet |
| Laptop | ≥ 1024 px | full sidebar (start side, 248 px) | content max-width 1200 px, detail panels side by side |
| Wide | ≥ 1440 px | same as laptop | results table may use full width |

- **Logical properties only** (`margin-inline-start`, `ps-4`, `text-start`). The `start` side is left in EN and right in AR.
- Touch targets ≥ 44×44 px on phone and tablet.
- There is no horizontal page scroll at 320 px. Wide tables scroll inside their container with a sticky first column.
- Content alignment is start-aligned everywhere (left in EN, right in AR). The only centered content is empty states.

### Wireframes

**App shell, laptop (EN; mirrored for AR)**
```
┌────────────┬───────────────────────────────────────────────────┐
│ Replora    │ Workspace ▾                    ◐ theme  AR|EN  👤  │
│            ├───────────────────────────────────────────────────┤
│ ● Home     │                                                   │
│ + New run  │   page content (max 1200)                         │
│   Runs     │                                                   │
│   Workflows│                                                   │
│   Files    │                                                   │
│   Settings │                                                   │
└────────────┴───────────────────────────────────────────────────┘
```

**App shell, phone**
```
┌──────────────────────────┐
│ Workspace ▾       ◐  👤  │
├──────────────────────────┤
│                          │
│   page content           │
│                          │
│ [ Primary action      ]  │  ← sticky
├──────────────────────────┤
│ Home  New  Runs  Files ⋯ │
└──────────────────────────┘
```

**New run: steps (a real sequence, so numbered markers are justified)**
```
 1 Upload ── 2 Describe ── 3 Review plan ── 4 Run ── 5 Results
```

**Review plan, laptop: the pipeline rail**
```
┌───────────────────────────────────────────────────────────────┐
│ Review the plan before it runs                                │
│ "Match orders with payments and show the differences"         │
│                                                               │
│  sales.zip ━━▶ [Open ZIP] ━┳━▶ [Read orders.csv] ━┓            │
│                            ┗━▶ [Read payments.json]┻━▶[Compare] ━▶ [Report] ━▶ results.zip
│              (connection color = artifact type)               │
├───────────────────────────────┬───────────────────────────────┤
│ Selected step: Compare        │ What happens                  │
│ Match on: order_id            │ • 2 files read, nothing sent  │
│ Compare: amount (±0.00)       │   to AI except column names   │
│ [Edit]                        │ • 2 warnings  ⚠               │
├───────────────────────────────┴───────────────────────────────┤
│                 [ Back ]   [ Approve and run ] ← saffron stamp │
└───────────────────────────────────────────────────────────────┘
```
On phone, the rail becomes vertical. Tapping a station opens a bottom sheet with its details, and the approve button is sticky.

**Results**
```
┌───────────────────────────────────────────────────────────────┐
│ Run finished · 4 rows compared                [Download all]  │
│ ✔ 1 matched   ≠ 1 different   ⟵ 1 only in orders   ⟶ 1 only in payments │
├───────────────────────────────────────────────────────────────┤
│ [All] [Different] [Missing]          🔍 Search                 │
│ order_id │ orders.amount │ payments.amount │ Status            │
│ O-101    │ 100.00        │ 100.00          │ ✔ Matched         │
│ O-102    │ 200.00        │ 190.00          │ ≠ Different (−10) │
│ …  row click → side sheet: where this row came from (lineage) │
└───────────────────────────────────────────────────────────────┘
```

## 5. Screens and required states

Every data screen has **loading (skeleton), empty, error and success** states, designed in both languages and both themes.

| Screen | Key content | Empty state | Skeleton |
|---|---|---|---|
| Sign in / Sign up / Reset | single column, 400 px max, language and theme switch available before login | — | — |
| Home | recent runs, saved workflows, "Start a new run" | "No runs yet. Upload two files to compare them." + Start a new run | list rows ×5 |
| New run, Upload | drop zone, file list with per-file progress and validation result | drop zone is the empty state | — |
| New run, Describe | prompt box, 3 example prompts per locale, attached files summary | — | — |
| New run, Review plan | pipeline rail, step detail panel, warnings and errors on stations, AI disclosure | — | rail skeleton (stations as blocks) |
| Run detail | rail with live station states, event timeline, Cancel run | — | rail + timeline |
| Results | status summary, filter tabs, virtualized table, lineage side sheet, downloads | "Nothing to compare: both files were empty." | summary + table rows ×10 |
| Workflows | list, version history, Run again | "Save a plan to reuse it on next month's files." | list rows |
| Replay mapping | old column → new column pickers with suggestions | — | form rows |
| Files | table with type, size, uploaded by, expires | "Files you upload appear here." | table rows |
| Settings | profile, language, theme, timezone, security (MFA, sessions), workspace members, invitations and roles, export my data, delete account (a danger zone with typed confirmation) | — | form blocks |
| Accept invitation | workspace name, inviter, role, then Accept or Sign up to accept | "This invitation has expired. Ask the workspace admin for a new one." | — |
| MFA challenge | 6-digit code input (LTR even in Arabic), "Use a recovery code" | — | — |
| First-run onboarding | "Try it with sample files" panel on Home, then a guided wizard pass with short inline hints | — | — |
| Landing, privacy, terms | public, bilingual, same tokens, no app shell | — | — |

## 6. Content and voice

- Plain verbs, sentence case and active voice. Name things by what users understand ("Match orders with payments", not "Fan-in compare node").
- **An action keeps its name through the whole flow:** the button "Approve and run" is followed by the toast "Run started". "Cancel run" is followed by "Run cancelled". "Save as workflow" is followed by "Workflow saved".
- Errors say what happened and how to fix it, with no apologies: "This file is a PDF renamed to .csv. Upload the original CSV export." Every backend `code` maps to an AR and an EN message plus a fix hint.
- Every PARTIAL or NEEDS_REVIEW result explains why and offers the next action.
- **Arabic copy** is written natively in Modern Standard Arabic, not machine-translated. Technical terms are explained once (for example "مسار العمل (Workflow)").
- Numbers: Western digits (0–9) by default in both locales for data integrity. Dates and money use `Intl` formatting per locale. Arabic-Indic digits are an option in settings, display only, and are never used in exported files.
- Mixed-direction text: IDs, file names, numbers and code are wrapped in `<bdi>` or `dir="ltr"` spans inside Arabic text.

## 7. i18n and RTL implementation rules
- `next-intl` with routes `/ar/...` and `/en/...`. The locale comes from the cookie, then `Accept-Language`, then `en`. The language switch keeps the current path.
- `<html lang dir>` is set on the server. Do not mirror the layout with CSS transforms.
- Messages live in `messages/{ar,en}.json` with ICU plurals (Arabic has zero, one, two, few, many and other forms). A key-parity test runs in CI.
- Tables in RTL: column order mirrors, numbers stay right-aligned in both directions for scanning, and text columns are start-aligned.
- The rail direction follows the reading direction on laptop.

## 8. Loading, caching and perceived speed
- Each route's `loading.tsx` skeleton matches the final layout exactly (same heights) so CLS ≈ 0.
- Optimistic UI for cancel, delete and rename, with rollback on error.
- Data from the previous visit shows instantly (TanStack Query cache) while it revalidates in the background, with a subtle "Updated" indicator only on change.
- Large previews are paginated from the server and virtualized on the client.

## 9. Accessibility (quality floor)
- WCAG 2.2 AA. Visible focus (2 px petrol ring with offset). Skip link. A landmark per region.
- The rail is navigable by keyboard (arrow keys follow visual direction, Enter opens the detail) and has an equivalent **list view** for screen readers.
- Live regions announce run state changes politely.
- Forms: labels are always visible (placeholders are not labels), and errors are linked with `aria-describedby`.

## 10. UI/UX iteration protocol (Phase 11, repeated per new screen)
1. Build the screen to this spec.
2. Take screenshots at **390 / 820 / 1440 × light / dark × AR / EN** (12 shots per screen).
3. Critique each shot against the checklist below and log the findings in `session_log.md`, rated high, medium or low.
4. Fix and re-shoot. Repeat until no high or medium findings remain (at least 2 rounds).
5. Before signing off, remove one unnecessary element.

**Critique checklist**
- [ ] Is the one primary action obvious within 3 seconds?
- [ ] Is the hierarchy clear without relying on boxes? Is any card unnecessary?
- [ ] Does the RTL mirror correctly (icons, rail direction, alignment, `bdi` on IDs and numbers)?
- [ ] Is Arabic text comfortable (line height, no letter-spacing, no clipped diacritics)?
- [ ] Are there no colour-only signals? Does it pass AA contrast in both themes?
- [ ] Does the skeleton match the final layout (no jump)?
- [ ] Do empty and error states give the next action?
- [ ] Is it usable at 320 px with no horizontal scroll and touch targets ≥ 44 px?
- [ ] Does the copy keep the same names for the same actions everywhere?
- [ ] Is there no decorative motion or gradient that serves no purpose?
