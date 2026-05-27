# Visual Source Classifier — H.9.1

## Зачем

OCR извлекает **текст** с изображений, но не понимает **визуальную семантику**:

- архитектурные схемы и пайплайны;
- UI-скриншоты и дашборды;
- диаграммы метрик и roadmap;
- image-only слайды команды.

Visual Source Classifier — **routing layer** между extraction и OCR/VLM: классифицирует визуальные блоки и решает, что делать дальше, **без запуска VLM**.

## Типы визуального содержимого

| `VisualContentType` | Примеры маркеров |
|---------------------|------------------|
| `team_slide` | команда проекта, тимлид, разработчики |
| `architecture_diagram` | архитектура, pipeline, data flow |
| `tech_stack_slide` | стек, Qdrant, FastAPI, React |
| `goals_slide` | цели проекта, задачи, проблема |
| `metrics_slide` | метрики, accuracy, % |
| `roadmap_slide` | направления развития, roadmap |
| `table_or_matrix` | таблица, матрица |
| `ui_screenshot` | интерфейс, dashboard, Streamlit |
| `generic_image` | изображение без маркеров |
| `unknown` | fallback |

## Routing decisions

| `VisualRouteAction` | Когда |
|---------------------|-------|
| `skip` | пустой слайд, нет текста и картинок |
| `use_text_layer` | достаточно текстового слоя |
| `run_ocr` | image-only, нужен OCR |
| `run_ocr_and_mark_vlm_candidate` | team/image-only + VLM позже |
| `mark_vlm_candidate_only` | схемы, UI, chart-like без OCR |

**Важно:** существующая OCR-логика (`ocr_decision.py`) **не заменяется**. Если OCR говорит RUN, а visual router — skip, **побеждает OCR**. Visual router добавляет metadata и VLM-кандидатов в fidelity.

## Архитектура

```
ExtractionResult
  → VisualSourceClassifier
  → VisualEvidenceReport
  → OcrEnrichmentService (metadata enrichment)
  → FidelityMetadata.visual_evidence_report
  → GET /evidence-report (visual_evidence_summary)
```

Модули: `backend/app/services/visual/`

## Примеры

### Team image slide (Indlab slide 25)

```
slide 25 | 0 | 1 | team_slide | 0.91 | run_ocr_and_mark_vlm_candidate | team markers/image-only | команда проекта
```

### Architecture diagram

Текст «Архитектура пайплайна Qdrant BERTopic Neo4j» → `architecture_diagram` → `mark_vlm_candidate_only`.

### Tech stack screenshot

Image-only слайд «Технологический стек» → `tech_stack_slide` → `run_ocr` или `run_ocr_and_mark_vlm_candidate`.

### Metrics chart

Слайд с «метрики», `%`, chart-like → `metrics_slide` → `mark_vlm_candidate_only` если chart-heavy.

## Ограничения

- Детерминированные правила по маркерам — без LLM/VLM.
- PDF: per-page эвристика (нет rich image metadata без рендера).
- Не классифицирует содержимое пикселей — только текстовые маркеры + metadata.
- VLM **не запускается** на этом этапе.

## Будущая VLM-интеграция

Кандидаты с `vlm_candidate=true` сохраняются в `FidelityMetadata.vlm_candidates_count`. Будущий VLM Adapter будет читать `visual_evidence_report` и обрабатывать только помеченные слайды.

## Команды

```powershell
cd C:\Dima\Projects\CURSOR\Lend\backend

..\.venv\Scripts\python.exe scripts\debug_visual_sources.py `
  --file "path\presentation.pptx" --slides 25

..\.venv\Scripts\python.exe scripts\smoke_visual_classifier.py --project indlab_telegram_news

..\.venv\Scripts\python.exe -m pytest tests\test_visual_source_classifier.py -q
```
