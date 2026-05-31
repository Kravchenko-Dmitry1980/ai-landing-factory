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
HTML/ZIP с 3D-стендом A-Frame и 2D-фолбэком. Обычный landing export не меняется.

```powershell
cd backend
# HTML + vendor folder
..\.venv\Scripts\python.exe scripts\export_showcase_demo.py
# Portable ZIP (recommended for offline demo)
..\.venv\Scripts\python.exe scripts\export_showcase_demo.py --zip
```

ZIP содержит `showcase.html`, `vendor/aframe/aframe.min.js`, `LICENSE.txt`.
Распакуйте и откройте `showcase.html` без интернета.

Vendored runtime: `frontend/public/vendor/aframe/aframe.min.js`.
Full release gate validates VR/AR Showcase ZIP and registry lifecycle
(`.\scripts\release_check.ps1 -Full`, not Simple Gate).
Подробности: [docs/VR_AR_SHOWCASE_P5.md](docs/VR_AR_SHOWCASE_P5.md)

### VR/AR Showcase Builder (Stage P.6)

Витрина теперь — сохраняемый объект (JSON registry), а не только разовый
экспорт. Базовый сценарий в UI:

1. открыть `/showcase`;
2. создать витрину;
3. добавить проекты (вручную или **Добавить из лендов** — ссылка на preview
   подставляется автоматически);
4. прикрепить demo-ссылки (`demo_url`, например AI Google Studio);
5. экспортировать **HTML** или **ZIP для офлайн-демо**.

При добавлении проекта из готовых лендов ссылка на preview подставляется
автоматически; demo-ссылку AI Google Studio добавьте отдельно.

Список витрин — `/showcase`, редактор — `/showcase/{id}`. CRUD API:
`/api/v1/showcases`. Реестр-смоук (вручную, изолированный temp storage):

```powershell
cd backend
..\.venv\Scripts\python.exe scripts\smoke_showcase_registry.py
```

Подробности: [docs/SHOWCASE_REGISTRY_P6.md](docs/SHOWCASE_REGISTRY_P6.md)

**Demo checklist:** [docs/SHOWCASE_DEMO_CHECKLIST.md](docs/SHOWCASE_DEMO_CHECKLIST.md)

#### Demo-ready VR/AR showcase (P.6.3)

На `/showcase` — кнопка **Создать витрину AI-проектов УИИ** (шаблон УИИ с
prefilled title/layout/theme). В редакторе — панель готовности к демо,
разделение landing/demo URL и экспорт ZIP с локальным A-Frame runtime.

## Interactive WOW Bundle (Stage P.7.2)

Отдельный режим экспорта: переносимый ZIP с **настоящей React/R3F-версией**
лендинга (интерактивный 3D WOW-hero). Работает офлайн, без backend, без
dev-сервера и без CDN — распакуйте и откройте `index.html`. Standard / WOW HTML
экспорт не меняются; это **не** значение по умолчанию.

```powershell
# 1. собрать standalone bundle (esbuild → frontend/dist-wow)
cd frontend
npm run build:wow-bundle
# из корня: .\scripts\build_wow_bundle.ps1 [-Smoke]

# 2. экспортировать ZIP
#    UI: preview → «Экспорт интерактивного WOW ZIP»
#    API: GET /api/v1/projects/{project_id}/export/wow-bundle
```

ZIP: `index.html`, `assets/wow-app.js` (+ `wow-app.css`),
`data/landing-contract.json`, `README_DEMO.txt`. Данные проекта встроены в
`index.html` (без `fetch`). Если bundle не собран — endpoint вернёт 503 с
инструкцией по сборке. Не входит в Simple Gate; по умолчанию не в Full Gate.

Подробности: [docs/WOW_INTERACTIVE_BUNDLE_P7_2.md](docs/WOW_INTERACTIVE_BUNDLE_P7_2.md)

## Final Demo Pack (Stage P.8.2)

Финальный demo pack для показа руководителю (WOW ZIP, Showcase ZIP, standard +
static HTML). Сборка и smoke:

```powershell
.\scripts\build_demo_pack.ps1
.\scripts\smoke_demo_pack.ps1
```

Подробности: [docs/FINAL_DEMO_PACK_P8_2.md](docs/FINAL_DEMO_PACK_P8_2.md)

## Operator guide (Russian)

See [docs/USER_QUICKSTART.md](docs/USER_QUICKSTART.md).

## Full developer docs

See [README_RUN.md](README_RUN.md) — advanced OCR/VLM, benchmarks, and research tools are documented at the bottom of that file.
