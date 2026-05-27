# UAT Release Report

Fresh-clone gate report for AI Landing Factory simple product release.

## Metadata

| Field | Value |
|-------|-------|
| Date | 2026-05-27 |
| Commit hash | local working tree (R.1 docs/scripts not yet pushed) |
| Clone path | `ai-landing-factory-fresh` (local UAT, not GitHub clone) |
| Gate | Fresh Clone checks via `uat_fresh_clone_check.ps1` |

## run.ps1

| Check | Result |
|-------|--------|
| `.venv` created | PASS (pre-existing from prior `run.ps1`) |
| Base pip install | PASS |
| `npm install` | PASS |
| Backend started | PASS (`http://127.0.0.1:8003`) |
| Frontend started | PASS (`http://localhost:3001`) |

## Dependency audit

```
python backend/scripts/audit_simple_dependencies.py
OK: simple dependency audit passed
```

| Check | Result |
|-------|--------|
| Forbidden OCR/VLM absent | PASS |
| Required base packages | PASS |

## Product mode

| Check | Result |
|-------|--------|
| `PRODUCT_MODE=simple` | PASS |
| OCR/VLM disabled at runtime | PASS |

## User flow (`uat_fresh_clone_check.ps1`)

| Check | Result |
|-------|--------|
| Product mode runtime smoke | PASS |
| Simple user flow smoke | PASS |
| Frontend HTTP smoke | WARN (`/editor` and `/preview` without projectId return 500; root OK) |

## Frontend

| Check | Result |
|-------|--------|
| Home page loads | PASS (HTTP 200) |
| Upload form present | PASS (via smoke) |

## Export

| Check | Result |
|-------|--------|
| Offline university export smoke | PASS |
| `--alf-*` tokens in HTML | PASS |
| No external script/CDN | PASS |

## Release gate (same session)

| Check | Result |
|-------|--------|
| `check_git_hygiene.ps1` | PASS |
| `release_check.ps1 -SkipFrontendBuild` | PASS |
| `npm test` | 118/118 PASS |
| `npm run build` | PASS after `Remove-Item frontend\.next -Recurse -Force` |
| Backend targeted pytest | 41/41 PASS |

## Verdict

**PASS** (local UAT). Full GitHub fresh-clone gate pending push of R.1 commits.

Notes:

- Run `git clone ... ai-landing-factory-fresh-release` after push to validate remote clone path.
- Stale `frontend/.next` can break `npm run build`; delete before release build if vendor-chunks error appears.

## Commands run

```powershell
cd C:\Dima\Projects\CURSOR\_uat\ai-landing-factory-fresh
.\scripts\uat_fresh_clone_check.ps1
.\scripts\release_check.ps1 -SkipFrontendBuild
cd frontend
npm test
Remove-Item -Recurse -Force .next -ErrorAction SilentlyContinue
npm run build
```
