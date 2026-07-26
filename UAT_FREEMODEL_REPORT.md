# UAT FreeModel Report

## 1. Project

| Поле | Значение |
|---|---|
| Path | `C:\Dima\Projects\CURSOR\_uat\ai-landing-factory-fresh` |
| Branch | `main` |
| Commit | `495f44c` — v1.0.0 add final demo pack build and smoke scripts |
| Date/time | 2026-07-26, ~16:50–17:10 (local) |
| Working tree | чистый (2 untracked: `-files logs`, `.cursor/rules/ironbee-devtools-use.mdc`) |

## 2. Environment

| Component | Value |
|---|---|
| OS | Windows 11 Pro 10.0.26200 |
| Python | 3.12.3 (`.venv\Scripts\python.exe`) |
| Node | v24.14.0 |
| npm | 11.11.0 |
| git | 2.45.2.windows.1 |
| venv | `.venv` в корне репозитория, присутствует |
| shell | Git Bash (PowerShell-скрипты запускались через `powershell.exe -NoProfile -ExecutionPolicy Bypass -File`) |

Установка зависимостей **не выполнялась**: запуск через `run.ps1 -SkipInstall`
(`.venv` и `frontend/node_modules` уже готовы). Сеть на PyPI/npm не дёргалась.

## 3. Documentation Read

| File | Status | Notes |
|---|---|---|
| `README.md` | OK | Quick Start = `.\run.ps1`; advanced OCR/VLM отключены по умолчанию |
| `README_RUN.md` | OK (присутствует, 40 KB) | Подробный runbook |
| `UAT_FRESH_CLONE_REPORT.md` | OK (заглушка-ссылка) | Ссылается на `docs/UAT_FRESH_CLONE_P2.md` |
| `UAT_RELEASE_REPORT.md` | OK | Fresh-clone gate PASS на коммите `accd750` |
| `docs/BACKEND_FULL_SUITE_DEBT_AUDIT_A2.md` | OK | 11/570 падений, все — test debt, release blockers = 0 |
| `docs/FINAL_DEMO_PACK_P8_2.md` | OK | Структура demo pack и команды сборки |
| `BACKEND_FULL_SUITE_AUDIT_RAW.log` / `..._VERBOSE.log` | Присутствуют | Локальные логи, не в git |

Отсутствует: отдельного `BACKEND_FULL_SUITE_AUDIT_*.md` в корне нет — актуальный аудит лежит в `docs/`.

## 4. Services

| Service | Command | Port | Status | Notes |
|---|---|---:|---|---|
| Backend (FastAPI/uvicorn) | `run.ps1 -SkipInstall` → `scripts/start_dev.ps1` | 8001 | **UP** | `http://127.0.0.1:8001` |
| Frontend (Next.js dev) | тот же скрипт | 3000 | **UP** | `http://localhost:3000` |
| Stop | `.\scripts\stop_dev.ps1` | — | доступен | не выполнялся |

## 5. Frontend Smoke

- URL: `http://localhost:3000`

| Route | HTTP | Bytes | Result |
|---|---:|---:|---|
| `/` | 200 | 17 354 | PASS, `<title>AI Landing Factory</title>` |
| `/showcase` | 200 | 16 979 | PASS |
| `/editor/{projectId}` | 200 | 41 595 | PASS |
| `/preview/{projectId}` | 200 | 17 761 | PASS |
| `/editor?projectId=…` | 404 | — | **Ожидаемо**: маршруты dynamic-path (`/editor/[projectId]`), query-форма не существует |

Issues: белого экрана нет, SSR-разметка возвращается. Прежний WARN из `UAT_RELEASE_REPORT.md`
про 404 на `/editor` и `/preview` — не дефект, а неверный формат URL в старом смоуке.

## 6. Backend Smoke

- Health endpoint: `GET /health` → **200** `{"status":"ok","service":"AI Landing Factory"}`
- `GET /api/v1/health` → 404 (такого маршрута нет — health вне версионированного префикса)
- `GET /docs` → 200, `GET /openapi.json` → 200
- Обнаружено 46 маршрутов (`/api/v1/projects*`, `/api/v1/showcase*`, `/health`)

End-to-end сценарий (реальные HTTP-вызовы, без AI):

| Шаг | Запрос | Результат |
|---|---|---|
| 1. Create project | `POST /api/v1/projects` | 200, `project_id=1892f9e8-7dee-41ca-8ed7-7fef83f1dd8a` |
| 2. Upload | `POST /projects/{id}/upload`, `telegram_analytics_presentation.txt` (5 556 B) | 200, файл распознан как `text`, черновой LandingContract готов |
| 3. PII prescan (авто) | в ответе upload | `has_pii=true`, `risk_level=low`, `redaction_count=4`, детекторы `natasha+regex`, `safe_for_cloud_current_mode=true` |
| 4. Generate | `POST /projects/{id}/generate` `{"mode":"full","enrich":false}` | 200 за 0.05 s; `domain=ai_research`, `layout_preset=technical_system` |
| 5. Export HTML | `GET /projects/{id}/export/html` | 200, 20 935 B, внешних `src=`/`href=` на CDN **нет** |
| 6. Export WOW bundle | `GET /projects/{id}/export/wow-bundle` | 200, ZIP 948 849 B |

CORS: frontend читает `NEXT_PUBLIC_API_URL=http://127.0.0.1:8001/api/v1`,
backend CORS покрывает localhost:3000–3050 — конфликтов не выявлено.

Targeted backend-тесты (быстрый набор из release gate):

```
pytest tests/test_product_mode_simple.py tests/test_university_export_offline.py \
       tests/test_wow_landing_export.py tests/test_llm_contract_builder.py -q
→ 39 passed, 1 warning in 3.53s
```

Полный `pytest tests/` **не запускался** (по аудиту A.2 там 11 известных test-debt падений).

## 7. AI Provider Detection

| Параметр | Значение |
|---|---|
| Provider abstraction | `backend/app/services/llm/` — `LLMClient` (base), `MockLLMClient`, `OpenAIClient` |
| Активный провайдер | `LLM_PROVIDER=mock` |
| LLM включён | `LLM_ENABLED=false` |
| Base URL | Был захардкожен на `https://api.openai.com/v1/chat/completions`. **Исправлено в этой сессии**: добавлена `OPENAI_BASE_URL` (дефолт прежний) |
| Model | `OPENAI_MODEL=gpt-4o-mini` |
| API key | `OPENAI_API_KEY` присутствует в `backend/.env`, но значение **пустое** (значение не выводилось) |
| Точки вызова LLM | `services/analysis/llm_contract_builder.py:61-64`, `services/semantic/generator.py:84,155` |
| Прочие LLM-флаги | `SEMANTIC_USE_LLM=false`, `DOMAIN_USE_LLM=false` |
| Anthropic / OpenRouter / FreeModel | в коде **не найдены** |
| FreeModel-compatible | **Да, после патча.** Осталось внести ключ и base URL в `backend/.env` |

## 8. FreeModel Smoke Test

- Test type: не проводился
- Number of API calls: **0**
- Model: —
- Result: **BLOCKED — ожидает ключа пользователя** (код разблокирован)
- Balance protection: **OK** — ни одного платного вызова не сделано, баланс не тронут.

### Что было заблокировано

1. base URL захардкожен на `api.openai.com` — переключить провайдера невозможно → **исправлено**;
2. `OPENAI_API_KEY` в `backend/.env` пуст — ключа FreeModel нет → **остаётся, вносит пользователь**.

### Применённый патч (по подтверждению пользователя, 2026-07-26)

| Файл | Изменение |
|---|---|
| `backend/app/config.py` | добавлено `openai_base_url: str = "https://api.openai.com/v1"` (+ комментарий) |
| `backend/app/services/llm/openai_client.py` | `self._base_url` из настроек; POST на `f"{base_url}/chat/completions"`; лог и текст ошибки теперь содержат base URL вместо жёсткого «OpenAI» |

Обратная совместимость: дефолт равен прежнему хардкоду. Проверено:

```
Settings().openai_base_url → https://api.openai.com/v1
pytest tests/test_llm_contract_builder.py tests/test_product_mode_simple.py -q
→ 13 passed, 1 warning in 2.12s
```

Backend после патча: `GET /health` → 200, frontend → 200.

`backend/.env.example` **не обновлён** — доступ к файлу заблокирован настройками
окружения. Строку `OPENAI_BASE_URL=https://api.openai.com/v1` в шаблон нужно добавить вручную.

### Что осталось сделать пользователю

Внести в `backend/.env` (ключ мне не присылать):

```env
LLM_ENABLED=true
LLM_PROVIDER=openai
OPENAI_BASE_URL=<base URL из FreeModel dashboard, обычно .../v1>
OPENAI_API_KEY=<ваш ключ FreeModel>
OPENAI_MODEL=<модель из FreeModel dashboard>
```

После этого backend нужно перезапустить (`.\scripts\stop_dev.ps1` → `.\run.ps1 -SkipInstall`),
и я сделаю **1 минимальный smoke-вызов**.

Дополнительное замечание: `OpenAIClient` запрашивает `response_format={"type":"json_object"}`.
Не все OpenAI-compatible шлюзы это поддерживают — при отказе потребуется fallback
на обычный текстовый ответ с парсингом JSON. Это выяснится на первом smoke-вызове.

## 9. OCR Smoke

- Test file: не использовался
- OCR settings: `OCR_ENABLED=false`, `OCR_ENGINE=paddleocr`, `OCR_DPI=250`, `OCR_MAX_PAGES=30`, `PRODUCT_MODE=simple`
- Result: **N/A (disabled by design)** — не FAIL

`scripts/check_ocr_env.ps1`:

| Движок | Статус |
|---|---|
| PaddleOCR | package missing |
| Tesseract (`pytesseract`) | package missing |
| EasyOCR | package missing |
| Surya | package missing |
| PyMuPDF (`fitz`) | not installed → PDF page rendering skipped |
| Summary | `ready: True`, «OCR is disabled. Set OCR_ENABLED=true when ready» |

Для реального OCR-смоука нужна установка пакетов (`scripts/setup_ocr_runtime.ps1 -InstallBasic`) —
это установка зависимостей, **требует отдельного подтверждения**. `.env` не изменялся,
`OCR_MAX_PAGES` не трогался.

## 10. Demo Pack

Каталог: `demo_release_20260531_2247`

| Артефакт | Размер, B | Статус |
|---|---:|---|
| `01_interactive_wow_landing/ai-wow-landing.zip` | 949 041 | PASS |
| `02_static_wow_landing/wow_landing.html` | 890 472 | PASS |
| `03_showcase_vr_ar/ai-showcase.zip` | 340 974 | PASS |
| `04_standard_landing/standard_landing.html` | 27 092 | PASS |
| `README_DEMO_RU.md` | 3 888 | PASS |
| `CHECKS/DEMO_PACK_CHECKLIST.md` + `DEMO_PACK_REPORT.md` | 1 185 / 1 785 | PASS |
| `demo_pack_meta.json` | 851 | PASS |

Распаковка WOW-бандла в `.runtime/demo_unpack` (исходный ZIP не тронут):

```
index.html            (4 361 B, <title>Нейро-ассистент для фильтрации и аналитики новостных потоков</title>)
assets/wow-app.js
assets/wow-app.css
assets/wow/cat-assistant.png
data/landing-contract.json
README_DEMO.txt
```

Offline-проверка: в HTML/JS нет загрузок с CDN — найдены только XML-namespace URI
(`w3.org`) и строки ошибок React (`react.dev/errors/`), сетевых запросов не делают.
`ai-showcase.zip` содержит `showcase.html` + вендоренный `vendor/aframe/aframe.min.js` — тоже offline.

## 11. Issues

| Severity | Area | Problem | Evidence | Fix | Status |
|---|---|---|---|---|---|
| ~~HIGH~~ | AI provider | Невозможно подключить FreeModel: base URL захардкожен | `openai_client.py:42` | Добавлен `openai_base_url` в `Settings` + используется в клиенте | **FIXED** 2026-07-26 |
| **HIGH** | AI provider | `OPENAI_API_KEY` пуст → любой не-mock LLM-путь падает с `LLMUnavailableError` | `backend/.env`, `openai_client.py:15-16` | Внести ключ FreeModel вручную в `backend/.env` | OPEN, нужен ключ от пользователя |
| MEDIUM | Backend tests | 11/570 падений в полном pytest (test debt, не регрессии) | `docs/BACKEND_FULL_SUITE_DEBT_AUDIT_A2.md` | Обновить legacy-asserts и сигнатуры `_render_from_contract` | Известно, не блокирует |
| LOW | Docs | В `UAT_RELEASE_REPORT.md` 404 на `/editor`/`/preview` записан как WARN | Проверка: `/editor/{id}` → 200 | Поправить формулировку смоука | OPEN, косметика |
| LOW | Repo hygiene | Мусорный untracked-файл `-files logs` в корне | `git status` | Удалить (требует подтверждения) | OPEN |
| INFO | OCR | Движки OCR не установлены | `check_ocr_env.ps1` | Ожидаемо для `PRODUCT_MODE=simple` | Не дефект |

## 12. Verdict

- **Local demo readiness: GO.** Frontend, backend, E2E-пайплайн (upload → generate → export),
  demo pack — всё работает offline, без AI.
- **FreeModel readiness: код готов, ключа нет.** Provider-патч применён и проверен;
  остался единственный блокер — пустой `OPENAI_API_KEY`. Кредиты не потрачены (0 вызовов).
- **Server readiness: NOT READY** — не хватает параметров сервера (см. `SERVER_DEPLOY_PREP.md`).
- Blockers для FreeModel: пустой `OPENAI_API_KEY` + не заполнен `OPENAI_BASE_URL` под FreeModel.
- Next action: внести ключ и base URL FreeModel в `backend/.env` вручную, перезапустить backend,
  затем выполнить 1 smoke-вызов.
