# Final Demo Pack (Stage P.8.2)

Финальный демонстрационный комплект для показа руководителю: интерактивный WOW
ZIP, static WOW HTML, Showcase VR/AR ZIP и standard landing HTML. Сборка не меняет
product pipeline — только вызывает существующие export-сервисы.

## Назначение

Один каталог `demo_release_YYYYMMDD_HHMM/` с понятной структурой:

```
demo_release_YYYYMMDD_HHMM/
├── README_DEMO_RU.md
├── 01_interactive_wow_landing/ai-wow-landing.zip
├── 02_static_wow_landing/wow_landing.html
├── 03_showcase_vr_ar/ai-showcase.zip
├── 04_standard_landing/standard_landing.html
├── CHECKS/
│   ├── DEMO_PACK_CHECKLIST.md
│   └── DEMO_PACK_REPORT.md
└── OPTIONAL/
```

## Как собрать

Из корня репозитория (Windows PowerShell):

```powershell
cd C:\Dima\Projects\CURSOR\_uat\ai-landing-factory-fresh

# Полный цикл: gates + WOW build + pack
.\scripts\build_demo_pack.ps1

# Только пересборка pack (gates и dist-wow уже готовы)
.\scripts\build_demo_pack.ps1 -SkipGates -SkipBuild

# Явный project_id
.\scripts\build_demo_pack.ps1 -ProjectId 8d1393c9-0803-4096-8ec9-8b4ca3ee7364
```

Порядок project_id: CLI → `.runtime/last_project.json` → первый проект с
контрактом в `backend/data/projects.json` → synthetic Indlab fixture.

## Как проверить

```powershell
.\scripts\smoke_demo_pack.ps1
.\scripts\smoke_demo_pack.ps1 -DemoDir demo_release_20260531_1200
```

Smoke проверяет структуру ZIP/HTML, cat mascot markers v3, vendored A-Frame,
отсутствие stale robot/ring markers — без dev-server и без интернета.

## Что показать руководителю

1. **Interactive WOW** — распаковать `ai-wow-landing.zip`, открыть `index.html`.
2. **Showcase** — распаковать `ai-showcase.zip`, открыть `showcase.html`.
3. **Standard** — `standard_landing.html` двойным кликом.
4. **Static WOW** — `wow_landing.html` как fallback.

Подробный сценарий: `README_DEMO_RU.md` внутри pack.

## Артефакты

| Артефакт | Источник | Offline |
|----------|----------|---------|
| Interactive WOW ZIP | `wow_bundle_exporter` + `frontend/dist-wow` | Да |
| Static WOW HTML | `WowHtmlExporter` (CSS-only, cat data URI) | Да |
| Showcase ZIP | `showcase_zip_exporter` + demo config | Runtime да; demo links — по клику |
| Standard HTML | `StyledHtmlExporter` | Да |

## Troubleshooting

### `file://` блокирует скрипты

```powershell
cd path\to\unzipped\folder
python -m http.server 8080
```

### WOW bundle 503 / smoke FAIL

```powershell
cd frontend
npm run build:wow-bundle
cd ..\backend
..\.venv\Scripts\python.exe scripts\smoke_wow_bundle_export.py
```

### Release gate FAIL

```powershell
.\scripts\release_check.ps1 -SkipFrontendBuild
.\scripts\release_check.ps1 -Full -SkipFrontendBuild
```

Не собирайте demo pack как PASS, пока gates не зелёные.

## Что не входит

- Новый дизайн hero / котика / анимаций
- LongCat-Video, Shap-E, GLTF
- OCR/VLM runtime
- Изменения PRODUCT_MODE
- Commit сгенерированных ZIP/HTML (`demo_release_*` в `.gitignore`)

## Связанные документы

- [WOW Interactive Bundle P.7.2](WOW_INTERACTIVE_BUNDLE_P7_2.md)
- [VR/AR Showcase P.5](VR_AR_SHOWCASE_P5.md)
- [Showcase Demo Checklist](SHOWCASE_DEMO_CHECKLIST.md)
