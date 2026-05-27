# UAT Release Report

Fresh-clone gate report for AI Landing Factory simple product release.

## Metadata

| Field | Value |
|-------|-------|
| Date | 2026-05-27 |
| Commit hash | `accd750` — fix(run.ps1): SOCKS-safe pip install for fresh clone gate |
| Clone path | `C:\Dima\Projects\CURSOR\_uat\ai-landing-factory-fresh-release` (GitHub fresh clone) |
| Gate | Fresh Clone checks via `uat_fresh_clone_check.ps1` |

## run.ps1

| Check | Result |
|-------|--------|
| `.venv` created | PASS |
| pip upgrade (direct PyPI, no SOCKS error) | PASS (pip 26.1.1) |
| backend requirements install | PASS (fastapi, httpx, pydantic, uvicorn, pytest, python-docx, python-pptx, etc.) |
| `npm install` | PASS (454 packages) |
| Backend started | PASS (`http://127.0.0.1:8001`) |
| Frontend started | PASS (`http://localhost:3000`) |
| Proxy diagnostics | PASS (`Clear-ProxyEnv` + `Invoke-PipSafe`; no manual env commands) |

## Dependency audit

```
python backend/scripts/audit_simple_dependencies.py
OK: simple dependency audit passed
  forbidden_absent=8 checked
  required_present=8 checked
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
| Frontend HTTP smoke | WARN (`/editor` and `/preview` without projectId return 404; root OK) |

## Frontend

| Check | Result |
|-------|--------|
| Home page loads | PASS (HTTP 200) |
| Upload form present | PASS (via smoke) |

## Export

| Check | Result |
|-------|--------|
| Offline university export smoke | PASS (via release_check / check_all) |
| `--alf-*` tokens in HTML | PASS |
| No external script/CDN | PASS |

## Release gate (R.1.1 session)

| Check | Result |
|-------|--------|
| `test_ps1_syntax.ps1` | PASS (Clear-ProxyEnv, Invoke-PipSafe contracts) |
| `release_check.ps1 -SkipFrontendBuild` | PASS |
| GitHub fresh clone `run.ps1` | PASS |
| `uat_fresh_clone_check.ps1` | PASS |

## Verdict

**PASS** — GitHub fresh clone gate cleared after R.1.1 SOCKS proxy fix.

Root cause fixed: pip in fresh `.venv` no longer fails on system SOCKS proxy (`socks://127.0.0.1:10808`); `run.ps1` clears proxy env vars and uses direct PyPI index via `Invoke-PipSafe`.

## Commands run

```powershell
cd C:\Dima\Projects\CURSOR\_uat\ai-landing-factory-fresh
.\scripts\test_ps1_syntax.ps1
.\scripts\release_check.ps1 -SkipFrontendBuild
git push origin main

cd C:\Dima\Projects\CURSOR\_uat
Remove-Item -Recurse -Force .\ai-landing-factory-fresh-release
git clone https://github.com/Kravchenko-Dmitry1980/ai-landing-factory.git ai-landing-factory-fresh-release
cd ai-landing-factory-fresh-release
.\run.ps1
.\scripts\uat_fresh_clone_check.ps1
.\scripts\stop_dev.ps1
```
