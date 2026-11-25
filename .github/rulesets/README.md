# Repository rulesets (P0.8, S-05)

`main.json` is the protection for `main`, kept as code so that changes to it are reviewed like any other change. Only a repo admin can apply it, and on GitHub Free it needs a public repository.

## What it enforces
- Changes reach `main` only through a pull request with **1 approving review**. GitHub never counts the author's own approval, so the approval comes from the other developer. A new push dismisses earlier approvals.
- **Squash merge only.**
- The 3 CI checks must pass: `Secret scan (gitleaks)`, `Backend (lint, test, audit)` and `Frontend (lint, typecheck, test, audit)`. These names must match the job `name:` values in `.github/workflows/ci.yml`.
- No force-push to `main`, and `main` can't be deleted.
- **No bypass list.** The rules apply to admins too, as agreed at G0.

`require_code_owner_review` is off on purpose. `/backend/` and `/frontend/` each have a single owner in `CODEOWNERS`, so on your own PR you'd be the only code owner, and you can't approve it. The rule "1 approval from the other developer" covers the intent. `strict_required_status_checks_policy` is off because CI already tests the merge result, so a PR isn't forced to rebase after every merge.

## Apply (repo admin, PowerShell, from the repo root)
```powershell
$r = 'kzazzco2009-hub/replora'
# 1. Visibility (rulesets need a public repo on GitHub Free). Run the gitleaks history scan first:
gitleaks git --redact --log-opts="--all" .
gh repo edit $r --visibility public --accept-visibility-change-consequences
# 2. The ruleset
gh api -X POST "repos/$r/rulesets" --input .github/rulesets/main.json
# 3. Squash-only merge button (matches the ruleset)
gh repo edit $r --enable-squash-merge --enable-merge-commit=false --enable-rebase-merge=false
# 4. Security features: Dependabot alerts, secret scanning with push protection
gh api -X PUT "repos/$r/vulnerability-alerts"
'{"security_and_analysis":{"secret_scanning":{"status":"enabled"},"secret_scanning_push_protection":{"status":"enabled"}}}' | gh api -X PATCH "repos/$r" --input -
# 5. Fork PRs: every external contributor's workflow run needs approval
gh api -X PUT "repos/$r/actions/permissions/fork-pr-contributor-approval" -f approval_policy=all_external_contributors
```
If a command fails, the same setting is in the web UI: Settings → General (visibility, merge button), Settings → Rules → Rulesets → Import a ruleset (`main.json`), Settings → Code security, and Settings → Actions → General.

## Verify (any collaborator)
```powershell
gh api repos/kzazzco2009-hub/replora/rules/branches/main | ConvertFrom-Json | ForEach-Object { $_.type }
# expected: deletion, non_fast_forward, pull_request, required_status_checks
```
To update the ruleset later, change `main.json` in a PR. After it merges, the admin runs `gh api -X PUT "repos/$r/rulesets/<id>" --input .github/rulesets/main.json`. The id comes from `gh api "repos/$r/rulesets"`.
