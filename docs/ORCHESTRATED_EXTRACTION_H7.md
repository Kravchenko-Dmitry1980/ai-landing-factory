# STAGE H.7 — Orchestrated Extraction Agents + Group Team Line Parser

## Почему не LLM multi-agent

LLM-агенты в runtime дают:
- низкую воспроизводимость;
- риск hallucination;
- сложность тестирования и объяснения.

Вместо этого — **deterministic orchestrated agents**: typed input/output, trace, unit tests.

## Архитектура

```
ExtractionResult
  → DocumentOrchestrator.run()
      → pptx_ocr_need_detector_agent
      → team_extraction_agent
  → ContractBuilderService (fusion as before)
  → LandingContract.fidelity.orchestration_trace
```

Модули:
- `backend/app/services/orchestration/document_orchestrator.py`
- `backend/app/services/orchestration/agents/*`
- `backend/app/services/evidence/group_team_parser.py`

## Group team line

**Было:** строка `Егор Быков, Максим Иванков, Алексей Решетников (Алмаз)` разбивалась на 3 отдельных блока без роли и bullets — только у последнего появлялись поля.

**Стало:** один `TeamBlock` → `expand_group_block()` → 3 `TeamMember` с общей ролью и contributions.

Пример:

```
12. Егор Быков, Максим Иванков, Алексей Решетников (Алмаз)
Парсинг, анализ данных
• Формирование требований к датасету.
...
```

→ все трое: role = «Парсинг, анализ данных», alias «Алмаз» у Решетникова.

## PPTX image-only limitation

Если в extracted text PPTX нет ФИО команды:
- agent добавляет warning `pptx_team_text_missing`;
- `possible_image_only_team_slide`;
- рекомендация: DOCX/TXT или OCR (OCR — future stage).

**Не утверждаем**, что команда извлечена из PPTX, если её нет в text layer.

## Диагностика

Evidence report (`/evidence-report`):
- `orchestration_trace`
- `team_group_expansions`

Verdict gate: multifile + DOCX → team обязателен (как раньше).

## Проверка

```powershell
cd C:\Dima\Projects\CURSOR\Lend\backend
..\.venv\Scripts\python.exe -m pytest tests\test_group_team_parser.py -q
..\.venv\Scripts\python.exe scripts\smoke_team_group_blocks.py
..\.venv\Scripts\python.exe scripts\smoke_field_fusion.py --all
```

## Future

- OCR pipeline для image-only team slides;
- optional LLM reviewer (advisory only);
- полный routing всех полей через orchestrator agents.
