# Release Checklist

Release philosophy: **simple product first**. Default path is `PRODUCT_MODE=simple` with base requirements only. OCR/VLM/advanced visual pipeline is optional research tooling and must not block push or demo.

## Release Gate Matrix

| Gate | When | Command | Requires OCR/VLM | Requires live ENDO |
|------|------|---------|------------------|-------------------|
| **A. Simple Release** | Before push / release | `.\scripts\release_check.ps1` | No | No |
| **B. Fresh Clone** | Before demo / major release | See section below | No | No |
| **C. Full Dev** | Weekly / pre-merge (optional) | `.\scripts\release_check.ps1 -Full` | No | No |
| **D. Advanced / Research** | OCR/VLM work only | `.\scripts\check_all.ps1 -RunOcrSmoke` | Yes | Optional |

### A. Simple Release Gate (mandatory)

```powershell
cd C:\Dima\Projects\CURSOR\_uat\ai-landing-factory-fresh

.\scripts\release_check.ps1
# or faster (skip frontend build):
.\scripts\release_check.ps1 -Fast
```

Equivalent manual steps:

```powershell
.\scripts\check_git_hygiene.ps1
.\scripts\check_all.ps1 -Simple -SkipFrontendBuild

cd frontend
npm test
npm run build

cd ..\backend
..\.venv\Scripts\python.exe -m pytest `
  tests/test_product_mode_simple.py `
  tests/test_style_config_persistence.py `
  tests/test_export_theme_api.py `
  tests/test_export_theme_tokens.py `
  tests/test_export_interactive.py `
  tests/test_university_export_offline.py `
  -q
```

**PASS criteria:**

- `RELEASE CHECK: PASS` (exit 0)
- No OCR/VLM packages in `.venv` (audit_simple_dependencies)
- University export smoke offline (theme tokens, anchor nav, no script/CDN)
- Frontend tests + build green
- Backend targeted style/export tests green

### B. Fresh Clone Gate (before demo)

```powershell
cd C:\Dima\Projects\CURSOR\_uat
Remove-Item -Recurse -Force .\ai-landing-factory-fresh -ErrorAction SilentlyContinue
git clone https://github.com/Kravchenko-Dmitry1980/ai-landing-factory.git ai-landing-factory-fresh
cd ai-landing-factory-fresh
.\run.ps1
.\scripts\uat_fresh_clone_check.ps1
.\scripts\stop_dev.ps1
```

**PASS criteria:**

- `.venv` created, base requirements installed
- `frontend/node_modules` installed
- `PRODUCT_MODE=simple`
- Upload / contract / export smoke passes
- Forbidden OCR/VLM packages absent

Report template: [UAT_RELEASE_REPORT.md](../UAT_RELEASE_REPORT.md)

### C. Full Dev Gate (optional)

```powershell
.\scripts\release_check.ps1 -Full
# or:
.\scripts\check_all.ps1 -SkipFrontendBuild -SkipVisualSmoke
cd frontend && npm test && npm run build
```

Includes corpus smoke, team group blocks, full backend pytest (when not `-Simple`), more regression. Still **no OCR/VLM** unless explicit flags.

### D. Advanced / Research Gate (non-blocking)

```powershell
.\scripts\check_all.ps1 -RunOcrSmoke
.\scripts\check_ocr_env.ps1 -RequireOcr -TestImage
cd backend
..\.venv\Scripts\python.exe scripts\benchmark_ocr_engines.py ...
..\.venv\Scripts\python.exe scripts\debug_vlm_candidates.py ...
```

May require Tesseract / EasyOCR / Paddle / GPU stack. Failures here do **not** block simple product release.

---

## Before commit

1. `git status --short` - review changed files
2. `.\scripts\check_git_hygiene.ps1`
3. Targeted tests for your change area (backend pytest or `npm test`)

## Before push

```powershell
.\scripts\release_check.ps1
```

## Before demo

1. Simple Release Gate PASS
2. Fresh Clone Gate (see B above)
3. Manual smoke: upload sample, preview, export HTML (University profile)

## check_all modes

| Flag | Meaning |
|------|---------|
| `-Simple` | Product path only: product smoke, style export, offline university export, product mode tests. Skips OCR/VLM/visual/full pytest/frontend build. |
| (default) | Full dev regression + optional live HTTP smokes if servers up |
| `-RunOcrSmoke` | Advanced: OCR env + PPTX OCR team smoke |
| `-SkipVisualClassifierSmoke` | Skip visual classifier (default in `-Simple`) |
| `-SkipVlmContractSmoke` | Skip VLM contract smoke (default in `-Simple`) |

University export smoke always uses **offline synthetic fixture** (`smoke_university_export.py --offline`). No live ENDO project required.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| PowerShell execution policy | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| pip SOCKS/proxy errors | Unset `HTTP_PROXY`/`HTTPS_PROXY` or use direct connection |
| Frontend port busy | `.\scripts\stop_dev.ps1` then `.\run.ps1` (auto-picks free port) |
| `npm run build` vendor-chunks error | `Remove-Item -Recurse -Force frontend\.next` then rebuild |
| Backend port busy | Same - start_dev picks 8001-8050 |
| `node_modules` missing | `cd frontend && npm install` |
| `.venv` missing | `.\run.ps1` from repo root |
| `backend/.env` missing | `copy backend\.env.example backend\.env` |
| University smoke FAIL | Run `python scripts\smoke_university_export.py --offline` for details |

---

## Last verified (local)

Run date: 2026-05-27

| `npm test` | 118/118 PASS |
| `npm run build` | PASS (clean `.next` if vendor-chunks error) |
| Backend targeted pytest | 41/41 PASS |
| `check_all -Simple` | PASS |
| `release_check.ps1 -SkipFrontendBuild` | PASS |
| `uat_fresh_clone_check.ps1` (local) | PASS |

Update this table after each release gate run.
