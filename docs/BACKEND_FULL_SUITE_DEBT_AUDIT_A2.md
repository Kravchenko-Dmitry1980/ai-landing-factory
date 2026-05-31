# STAGE A.2 — Аудит технического долга полного backend test suite

**Проект:** `ai-landing-factory-fresh`  
**Checkpoint:** после HOTFIX A.1 / v0.9.2 candidate  
**Дата аудита:** 2026-05-31  
**Окружение:** Windows, Python 3.12.3, pip 26.1.1, `.venv` в корне репозитория

---

## 1. Краткий вывод

Полный backend suite (`pytest tests/`) **не является надёжным release-сигналом**: 11 падений из 570 тестов (~1,9%), при этом **все текущие release gates (Simple, Full, targeted pytest) — PASS**.

Ни одно из 11 падений **не блокирует** `release_check.ps1`, `run.ps1` (simple path) или targeted release-тесты. Долг сосредоточен в трёх кластерах:

1. **LEGACY_EXPECTATION (3)** — устаревшие assert на литеральные CSS-токены `--bg: #ffffff` / `--bg: #0f1419` после миграции на `--alf-*` и alias `--bg: var(--alf-bg)` (P.3 style system).
2. **TEST_BUG / API drift (7)** — прямые вызовы `StyledHtmlExporter._render_from_contract()` без обязательного 4-го аргумента `style_config` после рефакторинга экспорта.
3. **TEST_BUG / OCR refactor (1)** — `monkeypatch` на несуществующий атрибут `ocr_router.PaddleOcrEngine` после переноса выбора движка в `multi_ocr_router.select_configured_engine()`.

**Verdict:** продукт для simple/full release в порядке; полный suite требует **целевого обновления legacy/advanced тестов**, а не отката продуктового кода. Массовые skip/delete не применялись.

---

## 2. Текущее состояние release gates

| Gate | Команда | Результат |
|------|---------|-----------|
| Simple | `.\scripts\release_check.ps1 -SkipFrontendBuild` | **PASS** |
| Full | `.\scripts\release_check.ps1 -Full -SkipFrontendBuild` | **PASS** |
| Targeted backend (расширенный набор из задания A.2) | см. §13 | **PASS** (104 passed) |

**Targeted pytest в `release_check.ps1` (Simple/Full):**

- `test_product_mode_simple.py`
- `test_style_config_persistence.py`
- `test_export_theme_api.py`
- `test_export_theme_tokens.py`
- `test_export_interactive.py`
- `test_university_export_offline.py`
- `test_wow_landing_export.py`

**Full-only дополнительно:** showcase ZIP/registry smokes + `test_showcase_*` (69 passed в прогоне Full gate).

**Примечание:** `check_all` внутри release_check запускается с `-Simple` и **не** гоняет полный `pytest tests/`. Dev-серверы на момент аудита были остановлены (`stop_dev.ps1`); предупреждения о недоступности backend/frontend в `check_all` не влияют на итог (offline/smoke-only шаги).

---

## 3. Сводка полного backend pytest

| Метрика | Значение |
|---------|----------|
| Собрано тестов | **570** |
| Passed | **559** |
| Failed | **11** |
| Errors | **0** |
| Skipped (runtime) | **0** (в этом прогоне; условные `skipif` не сработали) |
| Warnings | **1** (`pkg_resources` deprecated в `pymorphy2` via `test_llm_contract_builder`) |
| Время | ~18 с |

**Команда:**

```powershell
cd C:\Dima\Projects\CURSOR\_uat\ai-landing-factory-fresh\backend
..\.venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

**Краткая выдержка итога (не коммитить raw log):**

```
11 failed, 559 passed, 1 warning in 18.34s
```

Полные логи сохранены локально (не в git): `BACKEND_FULL_SUITE_AUDIT_RAW.log`, `BACKEND_FULL_SUITE_AUDIT_VERBOSE.log` в корне репозитория.

---

## 4. Таблица падений

| № | Тест | Файл | Симптом | Stack trace / ошибка | Контур | Категория | Блокирует release? | Рекомендация |
|---|------|------|---------|----------------------|--------|-----------|-------------------|--------------|
| 1 | `test_university_export_preserves_names_and_polish` | `tests/test_export_polish.py` | Assert на `--bg: #ffffff` | `assert '--bg: #ffffff' in html` — в HTML есть `--bg: var(--alf-bg)`, не литерал | `export` | **LEGACY_EXPECTATION** | Нет | Заменить assert на `--alf-bg:` + `--bg: var(--alf-bg)` (как в `test_university_export_offline.py`); оставить проверки имён/polish |
| 2 | `test_live_multifile_team_pipeline_export` | `tests/test_live_multifile_team_pipeline.py` | TypeError сигнатуры | `missing 1 required positional argument: 'style_config'` | `legacy` / `advanced_ocr` | **TEST_BUG** | Нет | Передавать `default_style_config()` 4-м аргом или вызывать `to_html()`; marker `legacy` |
| 3 | `test_presentation_only_team_missing_in_export` | `tests/test_live_multifile_team_pipeline.py` | То же | TypeError `style_config` | `legacy` / `export` | **TEST_BUG** | Нет | То же + вынести в gate «live multifile» (сейчас skip в Simple check_all) |
| 4 | `test_single_pptx_verdict_and_export_no_team` | `tests/test_live_project_consistency.py` | То же | TypeError `style_config` | `legacy` | **TEST_BUG** | Нет | `default_style_config()` + marker `legacy` |
| 5 | `test_pptx_docx_team_in_contract_and_export` | `tests/test_live_project_consistency.py` | То же | TypeError `style_config` | `legacy` / `advanced_ocr` | **TEST_BUG** | Нет | То же |
| 6 | `test_router_no_engine_warning_not_crash` | `tests/test_ocr_router_no_engine.py` | Monkeypatch fail | `ocr_router` has no attribute `PaddleOcrEngine` | `advanced_ocr` | **TEST_BUG** | Нет | Патчить `multi_ocr_router.select_configured_engine` / `create_engine`, не модульный re-export |
| 7 | `test_indlab_pptx_only_no_false_team` | `tests/test_pptx_team_extraction.py` | TypeError | `style_config` missing | `advanced_ocr` / `export` | **TEST_BUG** | Нет | 4-й аргумент + marker `advanced` / `ocr` |
| 8 | `test_enterprise_dark_export_unchanged` | `tests/test_styled_html_exporter_university.py` | Assert dark token | `assert '--bg: #0f1419' in html` — enterprise_dark через style tokens | `export` / `legacy` | **LEGACY_EXPECTATION** | Нет | Проверять dark через `LandingStyleProfile.TECH` tokens или явный legacy theme smoke; не требовать литерал в inline CSS |
| 9 | `test_presentation_only_junk_does_not_create_team` | `tests/test_team_false_positive_guard.py` | TypeError | `style_config` missing | `advanced_ocr` | **TEST_BUG** | Нет | `default_style_config()` |
| 10 | `test_indlab_real_team_without_false_positives` | `tests/test_team_false_positive_guard.py` | TypeError | `style_config` missing | `advanced_ocr` | **TEST_BUG** | Нет | То же |
| 11 | `test_styled_html_exporter_renders_team_card` | `tests/test_team_visibility_pipeline.py` | TypeError | `style_config` missing | `export` | **TEST_BUG** | Нет | То же; использовать public API `to_html` где возможно |

---

## 5. Классификация падений (сводка)

| Категория | Кол-во | Тесты |
|-----------|--------|-------|
| **LEGACY_EXPECTATION** | 3 | №1, №8; частично пересекается с №1 (polish) |
| **TEST_BUG** | 8 | №2–7, №9–11 |
| **REAL_REGRESSION** | 0 | — |
| **ADVANCED_OCR** (содержание, не причина падения) | 5 | live multifile, indlab, false positive guard, ocr router |
| **ENVIRONMENT_DEPENDENT** | 0 failures | 1 warning (pymorphy2/setuptools) |
| **FLAKY** | 0 | — |
| **FIXTURE_DRIFT** | 0 | — |
| **UNKNOWN** | 0 | — |

**Группировка по контурам:**

- **export / simple path:** №1, №8, №11 (+ косвенно №2–3 через export HTML)
- **legacy / live pipelines:** №2–5, №9–10
- **advanced_ocr:** №6–7, №9–10
- **не в release gate:** все 11

---

## 6. Что блокирует simple/full release

**Release blockers: нет (0).**

По политике A.2:

| Критерий | Статус |
|----------|--------|
| `release_check.ps1 -SkipFrontendBuild` | PASS |
| `release_check.ps1 -Full -SkipFrontendBuild` | PASS |
| Targeted pytest (release + showcase + wow + editor) | PASS |
| Standard export / university offline smoke | PASS |
| Showcase Registry / ZIP Full gate | PASS |
| WOW export smokes | PASS |

Падающие тесты **не входят** в списки `release_check.ps1` и **не запускаются** в Simple `check_all` (full pytest / live multifile / export polish public smoke — skip).

---

## 7. Что относится к advanced/research

Следующие области suite в основном **PASS**, но относятся к advanced-контуру и **не должны** блокировать simple/full по умолчанию:

- OCR: `test_ocr_*`, `test_multi_ocr_router.py`, `test_pptx_ocr_*`, `test_field_fusion_with_ocr.py`, …
- VLM: `test_vlm_adapter_contract.py`, visual classifier
- Team extraction live: `test_live_multifile_team_pipeline.py`, `test_orchestrated_team_extraction.py`
- Benchmarks: `test_ocr_benchmark.py`

**Единственный advanced-related failure:** №6 (`test_ocr_router_no_engine`) — это **ошибка теста** (устаревший monkeypatch), а не отсутствие Tesseract/Paddle в окружении.

---

## 8. Устаревшие тесты (legacy expectations)

### 8.1 CSS-токены экспорта (№1, №8)

**Было (ожидание тестов):** inline `--bg: #ffffff` / `--bg: #0f1419`.

**Стало (продукт, подтверждено gate):**

- `test_university_export_offline.py` → `--alf-bg:` + `--bg: var(--alf-bg)`
- `scripts/smoke_university_export.py --offline` → те же маркеры
- `docs/FRONTEND_STYLE_SYSTEM_P3.md` — профили и `LandingStyleConfig`

Тест `test_university_export_light_theme` уже допускает `#ffffff` **или** `--bg: #ffffff`; `test_enterprise_dark_export_unchanged` — нет, отсюда расхождение в одном файле.

### 8.2 Прямой вызов `_render_from_contract` (№2–5, №7, №9–11)

Сигнатура в `styled_html_exporter.py`:

```python
def _render_from_contract(
    self,
    contract: LandingContract,
    landing: GeneratedLanding | None,
    theme: ExportTheme,
    style_config: LandingStyleConfigModel,
) -> str:
```

Публичный путь `to_html()` мержит `style_config` — release-тесты используют его корректно.

### 8.3 OCR router monkeypatch (№6)

`ocr_router._select_engine()` делегирует в `multi_ocr_router.select_configured_engine()`. Классы движков больше не реэкспортируются в `ocr_router`.

---

## 9. Flaky / environment-sensitive

| Элемент | Тип | Влияние на A.2 |
|---------|-----|----------------|
| `pkg_resources` deprecation (pymorphy2) | Warning | Не failure; мониторить при обновлении setuptools |
| `pytest.skip("Pillow required")` в OCR fixtures | ENVIRONMENT_DEPENDENT | Не сработало в прогоне |
| `@pytest.mark.skipif(not VENDOR_SOURCE.is_file())` showcase | ENVIRONMENT_DEPENDENT | Vendor present — тесты выполнились |
| Tesseract/Paddle/EasyOCR optional tests | ADVANCED_OCR | **PASS** в полном suite (нет failures) |
| Live dev servers | infra | Не требуются для pytest; release_check offline OK |

**Flaky failures:** не выявлено.

---

## 10. Fixture / data debt

| Область | Статус |
|---------|--------|
| `tests/fixtures/export_contract_fixture.py` | Актуален; используется passing gate-тестами |
| FIXTURE docx для export polish | Данные валидны (имена в HTML есть); падает только CSS assert |
| test_corpus golden | PASS в check_all smoke |
| Live project paths в consistency tests | Зависят от `settings`/data dirs; падение до HTML — на API drift, не на fixture |

**FIXTURE_DRIFT как причина failure:** не подтверждён.

---

## 11. Рекомендации по markers / gates

### 11.1 Предлагаемые pytest markers (не внедрены в A.2)

```ini
markers =
    simple: simple product release scope
    full: full dev release scope (showcase, extended export)
    showcase: showcase registry / ZIP / API
    wow: WOW landing / bundle export
    editor: editor runtime API
    export: HTML export / theme / style
    advanced: research / non-blocking for simple release
    ocr: requires OCR runtime or OCR pipeline mocks
    vlm: VLM adapter / vision contracts
    slow: > N seconds or corpus-scale
    flaky: known unstable (quarantine)
    legacy: pre-P.3 export/team expectations
```

**Целевой gate-набор (будущее):**

```powershell
..\.venv\Scripts\python.exe -m pytest tests/ -m "not advanced and not ocr and not legacy" -q
```

### 11.2 Предложение по `pytest.ini`

На этапе **A.3** — только объявление markers + CI/profile документация, без массовой разметки 99 файлов.

### 11.3 Альтернатива без markers

Добавить в `backend/scripts/` профиль `pytest_release_core.ini` с `testpaths` = явный список как в `release_check.ps1` + wow/showcase/editor — **уже фактически есть** в `release_check.ps1`.

---

## 12. План исправления по этапам

| Этап | Scope | Effort | Риск |
|------|-------|--------|------|
| **A.3.1** | Документ + markers в `pytest.ini` (decl only) | S | Низкий |
| **A.3.2** | Пачка TEST_BUG: 7× `style_config=default_style_config()` | M | Низкий — только тесты |
| **A.3.3** | Пачка LEGACY: 3× CSS asserts → alf tokens | S | Низкий — выровнять с offline smoke |
| **A.3.4** | `test_ocr_router_no_engine`: patch `select_configured_engine` | S | Низкий |
| **A.3.5** | CI job `pytest -m "not (advanced or legacy)"` optional | M | Средний — согласовать с ADVANCED_PIPELINE_FREEZE |
| **A.3.6** | Quarantine flaky (если появятся) | — | — |

**Не делать:** откат `StyledHtmlExporter`, возврат литеральных `--bg` в продукт, blanket `skip` на файлы.

---

## 13. Команды для воспроизведения

```powershell
cd C:\Dima\Projects\CURSOR\_uat\ai-landing-factory-fresh
.\scripts\stop_dev.ps1

cd backend
..\.venv\Scripts\python.exe --version
..\.venv\Scripts\python.exe -m pip --version

# Полный suite
..\.venv\Scripts\python.exe -m pytest tests/ -q --tb=short

# Release gates (из корня)
cd ..
.\scripts\release_check.ps1 -SkipFrontendBuild
.\scripts\release_check.ps1 -Full -SkipFrontendBuild

# Targeted release backend (расширенный)
cd backend
..\.venv\Scripts\python.exe -m pytest `
  tests/test_editor_runtime_api.py `
  tests/test_wow_bundle_exporter.py `
  tests/test_wow_landing_export.py `
  tests/test_export_theme_api.py `
  tests/test_showcase_registry.py `
  tests/test_showcase_api.py `
  tests/test_showcase_zip_exporter.py `
  tests/test_showcase_exporter.py `
  -q
```

---

## 14. Итоговый verdict

| Вопрос | Ответ |
|--------|-------|
| Можно ли доверять полному `pytest tests/` как release-сигналу? | **Нет**, пока не закрыты 11 известных долгов |
| Безопасен ли release v0.9.2 по текущим gates? | **Да** — Simple/Full/targeted PASS |
| Есть ли REAL_REGRESSION в продукте по этим 11? | **Нет** — расхождение тест ↔ задокументированное поведение P.3 |
| Нужны ли изменения OCR/VLM pipeline? | **Нет** |
| Рекомендуемый следующий шаг | A.3.2–A.3.4: точечные правки тестов (~11 файлов, ~30 LOC) |

---

## Приложение: минимальные исправления в A.2

**Не применялись** — соблюдён принцип «сначала аудит, потом fix». Все 11 падений классифицированы как non-blocker; правки отложены на A.3 для минимального diff и отдельного commit.

---

*Аудит: STAGE A.2, Principal Backend QA / Release Engineer.*
