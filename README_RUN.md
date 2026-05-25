# AI Landing Factory — запуск MVP

Content-first pipeline:

```
материалы → extraction → LandingContract → generation → preview/export
```

## Структура проекта

```
Lend/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI entry
│   │   ├── config.py
│   │   ├── api/v1/               # REST: projects, upload, contract
│   │   ├── schemas/              # Pydantic: contract, extraction, generation
│   │   ├── repositories/         # file + contract persistence (JSON)
│   │   ├── services/
│   │   │   ├── extraction/       # dispatcher + docx/pdf/pptx + stub fallback
│   │   ├── scripts/smoke_extract.py
│   │   │   ├── analysis/         # ContractBuilder
│   │   │   ├── generation/       # LandingGenerator interface + stub
│   │   │   ├── export/           # HTML export
│   │   │   ├── prompts/          # PromptEngine + templates
│   │   │   └── pipeline.py       # orchestration
│   │   └── core/dependencies.py
│   ├── data/                     # runtime (uploads, contracts) — gitignored
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/                  # upload / editor / preview pages
│       ├── components/
│       └── lib/api.ts
└── README_RUN.md
```

## Требования

- Python 3.12+
- Node.js 20+
- PowerShell (Windows)

## Friendly one-command dev start

Запуск backend + frontend одной командой. Если порт **3000** или **8001** занят, скрипт автоматически выберет следующий свободный (до 3010 / 8010). **Не нужно** вручную разбираться с `netstat`, PID или `taskkill` — чужие процессы не останавливаются.

```powershell
cd C:\Dima\Projects\CURSOR\Lend
.\scripts\start_dev.ps1
```

В консоли появятся актуальные URL, например:

```
Backend:  http://127.0.0.1:8001
Frontend: http://localhost:3000

Откройте:
http://localhost:3000
```

Текущие порты сохраняются в `.runtime/ports.json`. Логи: `logs/dev/backend_*.log`, `logs/dev/frontend_*.log`.

`start_dev.ps1` автоматически синхронизирует frontend port с backend CORS: backend получает `BACKEND_CORS_ORIGINS` для `localhost` / `127.0.0.1` портов **3000–3010**, а `frontend/.env.local` — актуальный `NEXT_PUBLIC_API_URL`.

**Остановить** только процессы, запущенные `start_dev.ps1`:

```powershell
.\scripts\stop_dev.ps1
```

**Проверить** (автоматически подхватит URL из `.runtime/ports.json`):

```powershell
.\scripts\check_all.ps1
```

Первый запуск (если нет `.venv`):

```powershell
cd C:\Dima\Projects\CURSOR\Lend
python -m venv .venv
.\.venv\Scripts\pip.exe install -r backend\requirements.txt
cd frontend
npm install
cd ..
.\scripts\start_dev.ps1
```

Ручной запуск (для разработчиков) — см. разделы Backend / Frontend ниже.

## Backend

```powershell
cd c:\Dima\Projects\CURSOR\Lend
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Если порт 8000 занят, используйте **8001**:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

Проверка: http://127.0.0.1:8001/health (или :8000)  
Документация API: http://127.0.0.1:8001/docs

### CORS (browser frontend)

Dev default в `backend/app/config.py` разрешает `http://localhost:3000` … `:3010` и `http://127.0.0.1:3000` … `:3010`.

При запуске через `.\scripts\start_dev.ps1` CORS синхронизируется автоматически — вручную править `.env` не нужно.

Для **ручного** запуска uvicorn добавьте origin frontend в `backend/.env`:

```
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001
```

Перезапустите uvicorn после изменения.

## Frontend

```powershell
cd c:\Dima\Projects\CURSOR\Lend\frontend
copy .env.local.example .env.local
npm install
npm run dev
```

Открыть: http://localhost:3000 (или 3001, если 3000 занят)

`npm run dev` автоматически освобождает порт 3000 от stale `node` (zombie Next.js после crash или `next start`).  
Если preview отдаёт HTTP 500 — перезапустите dev: `Ctrl+C`, затем снова `npm run dev`.

### Frontend ↔ Backend URL

В `frontend/.env.local` укажите **полный base URL с `/api/v1`**:

```
NEXT_PUBLIC_API_URL=http://127.0.0.1:8001/api/v1
```

После изменения `.env.local` **перезапустите** `npm run dev`.

Проверка связи:

```powershell
cd frontend
node scripts/smoke-api.mjs
```

Ожидается: `Status: 200 OK`.

## Сценарий MVP

1. На главной ввести название проекта и выбрать файл(ы) или `.txt` бриф.
2. Нажать **Загрузить и создать ленд**.
3. Backend сохраняет файлы, запускает pipeline:
   - `DispatcherExtractionService` (DOCX/PDF/PPTX/TXT + stub fallback) → `ExtractionResult`
   - `ContractBuilderService` → `LandingContract` (draft)
   - `StubGenerationService` → `GeneratedLanding`
4. Откроется **редактор** — правка блоков и стиля.
5. **Preview** — интерактивный ленд (Framer Motion).
6. **Экспорт HTML** — скачивание статической страницы.

## API (кратко)

| Method | Path | Назначение |
|--------|------|------------|
| POST | `/api/v1/projects` | Создать проект |
| POST | `/api/v1/projects/{id}/upload` | Загрузить материалы + pipeline |
| GET | `/api/v1/projects/{id}/contract` | LandingContract |
| PATCH | `/api/v1/projects/{id}/contract` | Редактировать контракт |
| POST | `/api/v1/projects/{id}/contract/enrich` | LLM enrichment → LandingContract |
| POST | `/api/v1/projects/{id}/semantic-generate` | Semantic AI generation (Stage E) |
| POST | `/api/v1/projects/{id}/generate` | Перегенерировать landing (stub) |
| GET | `/api/v1/projects/{id}/semantic-landing` | GeneratedSemanticLanding |
| GET | `/api/v1/projects/{id}/landing` | Preview data |
| GET | `/api/v1/projects/{id}/export/html` | Экспорт |

## Extraction (DOCX / PDF / PPTX)

Зависимости: `python-docx`, `pypdf`, `python-pptx` (см. `backend/requirements.txt`).

**Smoke-тест без API:**

```powershell
cd c:\Dima\Projects\CURSOR\Lend\backend
python scripts\smoke_extract.py path\to\file.docx
python scripts\smoke_extract.py path\to\folder
```

**Unit-тесты payload:**

```powershell
cd c:\Dima\Projects\CURSOR\Lend\backend
..\.venv\Scripts\python.exe -m pytest tests\ -q
```

Pipeline: для каждого файла → `FileExtraction` (text + metadata + warnings) → агрегация в `ExtractionPayload` → `LandingContract`. Неизвестный формат не падает — stub fallback с warning.

## Multi-source landing assembly

Можно загружать **несколько файлов** одного проекта (PPTX, DOCX, PDF, TXT/MD, отчёты, ТЗ, список команды, краткий бриф). Система:

1. Строит **SourceInventory** по каждому файлу.
2. Разбивает материалы на **EvidenceItem** (слайд / секция / страница / абзац).
3. Собирает поля контракта через **MultiSourceEvidenceAssembler** (`parser_mode: multi_source_assembly`).
4. Если уверенность ниже порога — fallback на `project_presentation` или `heuristic`, с отчётом `evidence_report` в `fidelity`.

Каждый файл может содержать только часть данных; в метаданных контракта доступны `missing_fields`, `weak_fields`, `field_sources`, `source_count`, `evidence_count`.

**Для лучшего результата приложите:**

- презентацию проекта (PPTX);
- техническое задание (DOCX/PDF);
- описание команды;
- отчёт / итоги;
- явный технологический стек.

**Smoke:**

```powershell
cd C:\Dima\Projects\CURSOR\Lend\backend
..\.venv\Scripts\python.exe scripts\smoke_multi_source_assembly.py --fixture telegram_analytics
..\.venv\Scripts\python.exe scripts\smoke_multi_source_assembly.py --project-id <uuid>
..\.venv\Scripts\python.exe scripts\smoke_multi_source_assembly.py --files deck.pptx tz.docx team.txt
```

**Тесты:**

```powershell
..\.venv\Scripts\python.exe -m pytest tests\test_pptx_extractor_all_slides.py tests\test_evidence_extractor.py tests\test_field_assembler.py tests\test_multi_source_assembly.py -q
```

Загрузка через UI: тот же upload pipeline → `ContractBuilderService.build()` после extraction.

## Evidence Visibility in Editor

В редакторе (`/editor/{projectId}`) под блоком **Качество контракта** отображается секция **Source & Evidence** — прозрачность сборки ленда из загруженных материалов.

**Что видно:**

- **Parser mode** — `multi_source_assembly`, `structured`, `project_presentation`, `heuristic`
- **Sources / Evidence items / Assembly confidence**
- **Strong / Weak / Missing fields**
- Таблица источников: файл, тип, **source role**, число evidence, статус, заметки
- **Field coverage** — для каждого поля: strong / weak / missing, источник, location (slide / page / section), reason
- **Improvement hints** — что добавить для улучшения ленда

**Source roles:**

| Role | Назначение |
|------|------------|
| `primary_project_doc` | Задаёт название, заказчика и основную структуру проекта |
| `module_presentation` | Обогащает модуль, не меняет название проекта |
| `supporting_presentation` | Дополняет стек, результаты, архитектуру |
| `technical_spec` | Требования, входные/выходные данные |
| `report` | Итоги, метрики, перспективы |
| `team_source` | Состав команды |

**Field coverage:** `strong` — явный источник; `weak` — частично; `missing` — поле отсутствует.

**Примеры:**

- **Endocrinology:** `01_landing.docx` → `primary_project_doc`, title source = primary doc; `02_glaucologic_presentation.pptx` → `module_presentation`; `03_ai_copilot_presentation.pptx` → status `empty` (image-only, text=0).
- **Indlab:** landing + presentation; stack sources включают Qdrant / BERTopic / Neo4j.
- **KSK:** один PPTX, evidence по слайдам.

**API:** `GET /api/v1/projects/{project_id}/evidence-report` — slim payload без полного raw-текста документов (snippets ≤ 180 символов).

**Smoke:**

```powershell
cd C:\Dima\Projects\CURSOR\Lend\backend
..\.venv\Scripts\python.exe scripts\smoke_evidence_visibility.py --project-id <uuid>
```

**Тесты:**

```powershell
..\.venv\Scripts\python.exe -m pytest tests\test_evidence_visibility_api.py -q
cd ..\frontend
npm test -- EvidenceVisibilityPanel
```

Если поля weak/missing — добавьте соответствующий файл (команда, отчёт, текстовая версия презентации) и нажмите **Перепарсить** или перезагрузите материалы.

## Test corpus (регрессия)

Каталог `test_corpus/`: **одна папка = один проект = один LandingContract**. Эталоны в `test_corpus/golden/` (лёгкие `sources/*.pptx.txt`, без бинарников в git).

```powershell
cd C:\Dima\Projects\CURSOR\Lend\backend
..\.venv\Scripts\python.exe scripts\smoke_corpus.py
..\.venv\Scripts\python.exe scripts\smoke_corpus.py --project indlab_telegram_news
```

Ожидания: `expected_contract.yml` (шаблон — `test_corpus/expected_contract.yml.template`).

В **`check_all.ps1`** шаг **Test corpus smoke** включён по умолчанию: прогоняет все проекты из `test_corpus/golden/` (только lightweight `sources/*.txt` в git). Пропуск: `-SkipCorpusSmoke`.

## PPTX project presentation support

Если загруженный файл — **проектная презентация** (PPTX со слайдами «Цель проекта», «Этапы», «Подготовка данных», pipeline-шаги, «Итоги», «Команда»), система автоматически собирает полноценный `LandingContract` через `PresentationLandingSynthesizer` (или через multi-source assembly, если тот даёт более высокий completeness).

**Режим парсера в редакторе:** `project_presentation` (не `heuristic`).

**Поддерживаемые типы слайдов:**

| Слайд | Что извлекается |
|-------|-----------------|
| Цель проекта | essence, purpose, tasks |
| Этапы проекта | tasks, timeline |
| Подготовка данных | inputs |
| Шаг 1–N (pipeline) | modules, outputs |
| Демо-панель / Streamlit | outputs, results, stack |
| Итоги проекта | results, outlook |
| Ссылки на первоисточники | tech_stack |
| Команда | team |

**Для лучшего результата** используйте явные заголовки слайдов: «Цель проекта», «Итоги проекта», «Команда управления проектом», нумерованные «Шаг 1: …».

**Тесты:**

```powershell
cd C:\Dima\Projects\CURSOR\Lend\backend
..\.venv\Scripts\python.exe -m pytest tests\test_presentation_landing_synthesizer.py -q
```

**Smoke (manual, не входит в check_all по умолчанию):**

```powershell
cd C:\Dima\Projects\CURSOR\Lend\backend
..\.venv\Scripts\python.exe scripts\smoke_pptx_presentation_contract.py --project-id <id>
..\.venv\Scripts\python.exe scripts\smoke_pptx_presentation_contract.py --pptx "C:\path\to\presentation.pptx"
```

Готовый Word-ленд (`ready_landing_doc`) по-прежнему обрабатывается structured parser — презентационный режим его не затрагивает.

## LLM Contract Builder (Stage C)

Pipeline:

```
Upload → ExtractionResult → [optional] LLM Enrich → LandingContract → Generation → Preview
```

Upload по-прежнему строит **эвристический** контракт. LLM — отдельно: кнопка в редакторе или API.

### Без LLM (по умолчанию)

В `backend/.env`:

```
LLM_ENABLED=false
LLM_PROVIDER=mock
```

Работает mock/heuristic fallback, статус `draft_fallback` при enrich.

### С OpenAI

```
LLM_ENABLED=true
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

Перезапустить uvicorn после изменения `.env`.

### Проверка enrich

```powershell
# После upload — взять project_id из ответа или data/contracts/
cd c:\Dima\Projects\CURSOR\Lend\backend
python scripts\smoke_enrich.py <project_id>
```

Или в UI: **Улучшить через LLM** на странице редактора.

Ответ включает: `contract`, `enrichment.confidence`, `missing_fields`, `assumptions`, `source_trace`.

## PII Guard (Stage C.5 / C.6)

После upload автоматически запускается **PII pre-scan**. В ответе upload — optional `pii_summary`.

### Privacy modes (`backend/.env`)

```
PRIVACY_MODE=hybrid_safe   # local_only | hybrid_safe | cloud_unsafe_dev
ENABLE_PII_DETECTION=true
ENABLE_REHYDRATION=true
```

### Natasha (русские ФИО, layer 2)

```powershell
pip install natasha>=1.6.0
```

Без Natasha: regex-only + warning `natasha_not_available`.

### Safe cloud payload preview

```
GET /api/v1/projects/{id}/safe-cloud-payload
```

В редакторе: панель **Privacy & PII** → «Что будет отправлено в облачную модель».

### TTL cleanup

```
PII_REPORT_TTL_HOURS=72
PII_CLEANUP_ENABLED=true
```

```powershell
python backend\scripts\cleanup_pii.py
# или POST /api/v1/projects/privacy/cleanup
```

Документация: `backend/docs/PII_GUARD_HARDENING.md`, `backend/docs/PII_STORAGE_POLICY.md`.

### Тесты PII

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest tests\test_pii_*.py -q
```

## Stage D — Interactive Renderer

Preview (`/preview/{id}`) использует typed rendering platform (не LLM HTML):

```
GeneratedLanding + LandingContract → StyleProfile → LayoutPreset → SectionRegistry → InteractiveRenderer
```

Документация: `frontend/docs/README_RENDERING.md`  
Dev panel: `?dev=1` на preview (style profile, layout, hallmark warnings).

```powershell
cd c:\Dima\Projects\CURSOR\Lend\frontend
npm test
```

## Stage E — Semantic AI Generation Engine

Pipeline (evolution-first, без raw HTML от LLM):

```
LandingContract → SemanticGenerationEngine → GeneratedSemanticLanding → landing_bridge → GeneratedLanding → Stage D Renderer
```

- LLM получает **только PII-redacted contract JSON** (не raw files, не extraction text).
- `hallucination_guard` удаляет неподтверждённые metrics/team.
- Renderer **не меняется** — semantic → canonical blocks → typed sections.

### Env

```
SEMANTIC_GENERATION_ENABLED=true
SEMANTIC_USE_LLM=false          # fallback deterministic
LLM_ENABLED=true                # для cloud semantic
LLM_PROVIDER=openai|mock
```

### Smoke

```powershell
cd c:\Dima\Projects\CURSOR\Lend\backend
python scripts\smoke_semantic.py <project_id>
```

### UI

- Редактор: **Semantic generate**
- Preview debug: `?semantic_debug=1` (domain, sections, confidence, trace)

### Тесты

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest tests\test_semantic_*.py tests\test_domain_classifier.py tests\test_hallucination_guard.py -q
```

## University export polish

Публичный HTML export (`theme=university_platform`) сохраняет **ФИО участников команды** — система не обезличивает команду автоматически.

Перед публикацией убедитесь, что есть согласие на использование ФИО в ленде.

Polish включает:
- tagline не дублирует title (deterministic fallback);
- аккуратные team cards без обрыва на предлогах;
- корректное склонение «+ ещё N пункт(ов)»;
- линейный список команды без группировки по подпроектам.

Проверка качества:

```powershell
cd c:\Dima\Projects\CURSOR\Lend\backend
..\.venv\Scripts\python.exe scripts\smoke_public_export.py --project-id 55a98f90-73fc-4d26-a477-3c974a0cbeed --backend-url http://127.0.0.1:8001
```

Unit-тесты:

```powershell
..\.venv\Scripts\python.exe -m pytest tests\test_export_polish.py -q
```

В `check_all.ps1` шаг **Export polish smoke** включён по умолчанию (`-SkipPublicExportSmoke` чтобы пропустить).

## University export smoke

Quality gate для HTML export темы `university_platform` (светлый стиль УИИ, не dark enterprise).

Backend должен быть запущен:

```powershell
cd c:\Dima\Projects\CURSOR\Lend\backend
..\.venv\Scripts\python.exe scripts\smoke_university_export.py --project-id 55a98f90-73fc-4d26-a477-3c974a0cbeed
```

Другой порт backend:

```powershell
..\.venv\Scripts\python.exe scripts\smoke_university_export.py --project-id <id> --backend-url http://127.0.0.1:8001
```

Ожидается `UNIVERSITY EXPORT SMOKE PASSED` и exit code `0`.  
Если exporter ещё не поддерживает `theme=university_platform`, скрипт честно вернёт `FAIL` на dark CSS markers.

Чеклист: `docs/WEB_QUALITY_GATE.md`

Unit-тесты validation helpers:

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest tests\test_smoke_university_export_script.py -q
```

## One-command QA pipeline

Единая локальная проверка перед демо, передачей коллегам или новым этапом разработки.

### Перед запуском smoke

**Рекомендуется** — одна команда (auto-port):

```powershell
cd C:\Dima\Projects\CURSOR\Lend
.\scripts\start_dev.ps1
```

**Или вручную** — backend (отдельный терминал):

```powershell
cd C:\Dima\Projects\CURSOR\Lend\backend
..\.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8001
```

**Frontend** (отдельный терминал, если не используете `start_dev.ps1`):

```powershell
cd C:\Dima\Projects\CURSOR\Lend\frontend
npm run dev
```

### Запуск

Из корня проекта:

```powershell
cd C:\Dima\Projects\CURSOR\Lend
.\scripts\check_all.ps1
```

С параметрами:

```powershell
.\scripts\check_all.ps1 -ProjectId 55a98f90-73fc-4d26-a477-3c974a0cbeed

.\scripts\check_all.ps1 -BackendUrl http://127.0.0.1:8001 -FrontendUrl http://localhost:3000

.\scripts\check_all.ps1 -FailFast

.\scripts\check_all.ps1 -SkipFrontendBuild

.\scripts\check_all.ps1 -SkipCorpusSmoke

.\scripts\check_all.ps1 -VerboseOutput
```

Быстрая проверка без сборки фронта (corpus smoke по golden-проектам всё равно выполняется):

```powershell
.\scripts\check_all.ps1 -SkipFrontendBuild
```

### Что проверяет pipeline

| Шаг | Требует сервер |
|-----|----------------|
| PII env check | нет |
| Backend tests (`pytest`) | нет |
| Test corpus smoke (`smoke_corpus.py`, golden projects) | нет |
| Endocrinology acceptance smoke | backend |
| University export smoke | backend |
| Export polish smoke | backend |
| Frontend tests (`npm test`) | нет |
| Frontend build (`npm run build`) | нет |
| Visual acceptance smoke | backend + frontend |

Лог каждого запуска: `logs/qa/check_all_YYYYMMDD_HHMMSS.log`

Ожидается в конце: `Overall: PASS` и exit code `0`.  
Если backend/frontend не запущены — smoke шаги **FAIL** (не SKIP), `Overall: FAIL`.

Документация visual smoke: `frontend/docs/VISUAL_ACCEPTANCE_UNIVERSITY.md`

## Расширение (следующие шаги)

- `ImageOcrExtractor` для скриншотов.
- OpenAI semantic with richer section schemas (architecture_nodes diagrams).
- PostgreSQL вместо JSON-файлов.
- Очередь задач (Celery/ARQ) для тяжёлого extraction.
- React export (PDF/zip) в `services/export`.

## Переменные окружения

`backend/.env.example` — `LLM_ENABLED`, `LLM_PROVIDER`, `OPENAI_API_KEY`, `OPENAI_MODEL`.  
`frontend/.env.local` — `NEXT_PUBLIC_API_URL=http://127.0.0.1:8001/api/v1` (порт backend + `/api/v1`)
