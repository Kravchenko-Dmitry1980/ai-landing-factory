# VLM Adapter Contract — H.9.2

## Зачем не vLLM сразу

Stage H.9.1 определяет **кандидатов** для VLM (`vlm_candidate=true`), но без контрактного слоя нельзя безопасно подключить:

- local transformers VLM;
- Ollama;
- vLLM server;
- cloud VLM API.

H.9.2 добавляет **интерфейс и stub** — без GPU, сети и тяжёлых зависимостей.

## Provider abstraction

| `VlmProvider` | Статус |
|---------------|--------|
| `stub` | Реализован (deterministic) |
| `local_transformers` | Future |
| `ollama` | Future |
| `vllm` | Future |
| `cloud` | Future |
| `disabled` | Default when `VLM_ENABLED=false` |

## Disabled by default

```env
VLM_ENABLED=false
VLM_PROVIDER=stub
```

При `VLM_ENABLED=false`:

- pipeline **не падает**;
- `vlm_extraction_report.enabled=false`;
- `vlm_skipped_count` отражает число visual candidates;
- существующий contract output **не меняется**.

## Stub adapter

`StubVlmAdapter`:

- **не выдумывает** ФИО команды;
- echo tech stack **только** если Qdrant/Neo4j/etc. есть в `text_layer_preview` / `ocr_text_preview`;
- architecture — только из контекста;
- deterministic для тестов.

## Structured output contract

`VlmStructuredExtraction` → `VlmFieldCandidate[]` → virtual `FileExtraction` (`file_type=vlm`).

Пример evidence text:

```
VLM extracted tech_stack: Qdrant, Neo4j, BERTopic
```

Prompt contract (`vlm_prompt_builder.py`) требует **JSON only**, **do not invent**, **visible evidence only**.

## Pipeline

```
VisualEvidenceReport
  → select vlm_candidate=true
  → VlmRouter / VlmEnrichmentService
  → VlmAdapter (stub)
  → VlmEvidenceBuilder
  → ExtractionResult.files (+vlm)
  → EvidenceExtractor → FieldFusionEngine
```

## Safety rule

**VLM evidence = candidate evidence, not source of truth.**

- Team names из VLM stub **не публикуются** (пустой список + warning).
- OCR team verification gate остаётся для people.
- Fusion может использовать VLM tech/architecture как supporting evidence.

## Future providers

1. Реализовать `VlmAdapter` для выбранного backend.
2. Зарегистрировать в `select_vlm_adapter()`.
3. Использовать `vlm_prompt_builder` + `vlm_result_parser`.
4. Включить `VLM_ENABLED=true`.

## Команды

```powershell
cd C:\Dima\Projects\CURSOR\Lend\backend

..\.venv\Scripts\python.exe scripts\debug_vlm_candidates.py --file path\deck.pptx --slides 7,25

..\.venv\Scripts\python.exe scripts\debug_vlm_candidates.py --file path\deck.pptx --enable-stub

..\.venv\Scripts\python.exe scripts\smoke_vlm_adapter_contract.py

..\.venv\Scripts\python.exe -m pytest tests\test_vlm_adapter_contract.py -q
```

## Ограничения H.9.2

- Нет реальной VLM inference.
- PDF image bytes — ограниченно (без page render).
- Stub не анализирует пиксели.

## Next step

H.9.3 — первый local provider (Ollama или vLLM) за feature flag, только для `architecture_diagram` / `tech_stack_slide`.
