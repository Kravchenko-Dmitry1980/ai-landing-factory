# AI Landing Factory

Content-first pipeline: materials → extraction → LandingContract → preview/export.

## Quick Start

```powershell
git clone https://github.com/Kravchenko-Dmitry1980/ai-landing-factory.git
cd ai-landing-factory
.\run.ps1
```

Open the URL printed in the console (for example `http://localhost:3000`).

Then:

1. Upload PPTX / DOCX / TXT / PDF
2. Review the generated landing
3. Edit sections if something was missed
4. Export HTML (default visual style: **University / Платформа УИИ**)

### Landing visual style

- Default preview/export profile: `university_platform`
- Editor: presets (Minimal, Corporate, Tech, Bold) or **Custom** text intent → safe theme tokens
- Details: [docs/FRONTEND_STYLE_SYSTEM_P3.md](docs/FRONTEND_STYLE_SYSTEM_P3.md)

**Advanced OCR/VLM is optional and disabled by default.** You do not need Tesseract, EasyOCR, PaddleOCR, Ollama, or local models for the default path.

## Stop

```powershell
.\scripts\stop_dev.ps1
```

## Simple QA (no OCR/VLM)

```powershell
.\scripts\release_check.ps1
.\scripts\check_all.ps1 -Simple
```

Details: [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md)

Fresh-clone demo gate: [docs/UAT_FRESH_CLONE_P2.md](docs/UAT_FRESH_CLONE_P2.md)

## VR/AR Showcase mode

Дополнительный режим (Stage P.5): собрать витрину из нескольких лендингов
и демо-проектов (например, AI Google Studio) и экспортировать offline-ready
HTML с 3D-стендом A-Frame (локальный vendored runtime) и 2D-фолбэком.
Обычный landing export не меняется.

```powershell
cd backend
..\.venv\Scripts\python.exe scripts\export_showcase_demo.py
# → backend/data/exports/showcase_demo.html
# → backend/data/exports/vendor/aframe/aframe.min.js  (offline runtime)
```

Vendored runtime в репозитории: `frontend/public/vendor/aframe/aframe.min.js`.
CDN override: `--aframe-src https://aframe.io/releases/1.7.0/aframe.min.js`.

UI: страница `/showcase`. Подробности: [docs/VR_AR_SHOWCASE_P5.md](docs/VR_AR_SHOWCASE_P5.md)

## Operator guide (Russian)

See [docs/USER_QUICKSTART.md](docs/USER_QUICKSTART.md).

## Full developer docs

See [README_RUN.md](README_RUN.md) — advanced OCR/VLM, benchmarks, and research tools are documented at the bottom of that file.
