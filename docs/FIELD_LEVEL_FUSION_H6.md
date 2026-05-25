# STAGE H.6 — Field-Level Multi-Source Fusion Engine

## Проблема document-level winner

Раньше `ContractBuilderService` выбирал **один победивший parser** (presentation vs multi-source) по completeness score. Это ломало ключевой сценарий продукта:

- PPTX содержит modules, tech_stack, architecture;
- DOCX содержит team, client, detailed sections;
- presentation побеждает → **team из DOCX теряется**.

## Решение: field-level fusion

При `source_count >= 2` система собирает **candidate contracts** от разных parser paths и вызывает `FieldFusionEngine`:

```
ExtractionResult (2+ files)
  → MultiSourceEvidenceAssembler → ms_contract
  → PresentationLandingSynthesizer → pres_contract (если PPTX)
  → FieldFusionEngine.fuse(ms + pres)
  → final LandingContract (parser_mode = field_level_fusion)
```

## Архитектура

```
backend/app/services/fusion/
├── field_fusion_engine.py      # orchestrator
├── field_candidate.py          # FieldCandidateBuilder
├── field_strategies.py         # per-field strategies
├── field_score.py              # candidate ranking
├── conflict_resolver.py        # title/client conflicts
├── completeness_critic.py      # post-fusion gate
├── source_value_normalizer.py  # dedupe, tech aliases
├── fusion_config.py            # caps, priorities
└── fusion_trace.py             # evidence-compatible trace
```

## Таблица стратегий

| Поле | Стратегия | Поведение |
|------|-----------|-----------|
| title | primary_priority_single | primary doc > presentation > longest |
| client, timeline, lead | primary_metadata_priority | metadata из primary DOCX |
| essence | best_plus_enrichment | лучший текст + non-overlap enrichment |
| tasks, purpose, inputs, outputs, results, outlook | union_dedupe_ranked | union из всех источников, cap |
| tech_stack | union_grouped_tech | union + normalize (Qdrant Cloud → Qdrant) |
| team | union_validated_people | union + filter_team_members |
| modules | union_modules_with_source_priority | merge по title, без slide garbage |

## Примеры

### Indlab: PPTX + DOCX

- `title` ← DOCX (primary)
- `team` ← DOCX (12+ участников)
- `modules` ← PPTX + DOCX union
- `tech_stack` ← PPTX + DOCX union (Qdrant, BERTopic, Neo4j, Postgres…)

### Endocrinology: landing DOCX + module PPTX

- `title` = «Эндокринология+» (primary doc wins)
- `modules` включают GlaucoLogic / Copilot / VitaCalc
- module PPTX **не перебивает** title

### KSK: single PPTX

- fusion **не вызывается** (`source_count == 1`)
- сохраняется `multi_source_assembly` / `project_presentation`

## Trace / Evidence

`FidelityMetadata` расширен:

- `fusion_trace` — полный FusionTrace
- `field_decisions` — per-field selected_sources
- `parser_mode = field_level_fusion`

Evidence report (`/evidence-report`) отдаёт `field_decisions` для UI.

## Diagnostics

`check_live_project_verdict`:

- при `source_count >= 2` + DOCX/TXT + пустой team → BUG
- при `field_level_fusion` + team ≥ 10 → OK (Indlab)

## Ограничения

- Deterministic only — без LLM judge
- Single-source projects не используют fusion
- OCR не поддерживается (image-only slides → team missing)
- Module dedup эвристический — возможны ложные module cards на edge cases

## Проверка

```powershell
cd C:\Dima\Projects\CURSOR\Lend\backend
..\.venv\Scripts\python.exe -m pytest tests\test_field_level_fusion_engine.py -q
..\.venv\Scripts\python.exe scripts\smoke_field_fusion.py --all
..\.venv\Scripts\python.exe scripts\smoke_corpus.py
```
