# PPTX Team Extraction Audit — Stage H.4.1

Date: 2026-05-25  
Scope: PPTX-only team path for Indlab and general PPTX improvements

## 1. Slides containing team (Indlab)

Audit of `test_corpus/golden/indlab_telegram_news/sources/01_presentation.pptx.txt`:

| Slide | Title / topic | Team markers | ФИО |
|-------|---------------|--------------|-----|
| 1–13 | Goals, architecture, pipeline, Neo4j demo | **none** | **none** |
| 3 | «Цели проекта» | «команды **заказчика**» (false context) | none |
| 17 | «Команда проекта достигла…» (KSK-style phrase absent) | false context only | none |

**Conclusion:** In the extractable PPTX text for Indlab there is **no slide** with:
- «Команда проекта» / «Участники команды»
- «Тимлид: …» / «Помощник тимлида: …»
- ФИО участников (Кравченко, Ерюкова, Глазунова)

Team for Indlab lives in `02_landing.docx.txt` (section «Команда проекта», 15 members).

If the live `.pptx` binary has a team slide as **image/table without text layer**, OCR would be required (out of scope).

## 2. pptx_extractor visibility

Before H.4.1: read `shape.text` only (missed grouped shapes, table cells, paragraph runs).

After H.4.1: recursive `extract_shape_texts()` — groups, tables, text frames, runs.

Indlab snapshot: extractor sees all 18 slides with text; **team content still absent** because it is not in source text.

## 3. Team text in ExtractionResult.full_text

Indlab PPTX-only: **NO** team markers in `extracted_text`.  
KSK PPTX slide 19: **YES** — «КОМАНДА УПРАВЛЕНИЯ ПОЕКТОМ», «Тимлид: Бугров Алексей», «Помощник тимлида: Кравченко Дмитрий».

## 4. metadata.slides[]

Each slide now includes: `index`, `title`, `text`, `notes`, `char_count`.

## 5. EvidenceReport candidates (Indlab PPTX-only)

- `field_candidates` for `team` no longer triggered by bare substring «команда» (e.g. «команды заказчика»).
- Slide 14 pipeline text («Посты Telegram», «Qdrant Cloud») → **no team candidates** (false positive guard).
- `team` coverage: **missing**

## 6. Acceptance / rejection reasons

New reason codes in `validate_team_candidate_with_reason()`:

| Code | Meaning |
|------|---------|
| `accepted: valid_name_in_team_context` | ФИО in team slide/section |
| `accepted: valid_name_with_role` | ФИО + valid role |
| `rejected: domain_stop_word` | Tech/domain token |
| `rejected: not_person_name` | Not 2–3 word Russian name |
| `rejected: outside_team_context` | Name without team context |

## 7. Where team was lost (Indlab PPTX-only)

| Stage | Result |
|-------|--------|
| **extraction** | No team text in file → nothing to extract |
| evidence | No team-marked slides → no team evidence items |
| team_parser / people_extractor | N/A (no input) |
| field_assembler | `team=[]` |
| export | No `section#team` (correct) |

**Not a parser bug** — **missing source content** in PPTX text layer.

## 8. Fixes applied

1. `pptx_shape_text.py` — recursive shape/table/group extraction  
2. `pptx_team_markers.py` — team slide markers + false context filter  
3. `people_extractor.py` — table rows, numbered bullets, `diagnose_people_from_text()`  
4. `team_candidate_validator.py` — reason codes, tighter team context hints  
5. `field_candidates.py` — specific team markers (not bare «команда»)  
6. `evidence_extractor.py` — team section hints on slides  
7. `presentation_landing_synthesizer.py` — expanded team slide rules  
8. `contract_builder._supplement_pptx_team()` — PPTX-only fallback via presentation synthesizer  
9. `evidence_visibility.py` — PPTX-only missing team hint  
10. `debug_pptx_team_extraction.py`, `smoke_pptx_only_team.py`, `test_pptx_team_extraction.py`

## 9. expected_contract.yml (Indlab)

```yaml
pptx_only:
  must_have_team: false
  min_team: 0
  reason: no_extractable_team_text_in_pptx
```

## 10. Verification commands

```powershell
cd C:\Dima\Projects\CURSOR\Lend\backend
..\.venv\Scripts\python.exe scripts\debug_pptx_team_extraction.py `
  --snapshot ..\test_corpus\golden\indlab_telegram_news\sources\01_presentation.pptx.txt
..\.venv\Scripts\python.exe -m pytest tests\test_pptx_team_extraction.py -q
..\.venv\Scripts\python.exe scripts\smoke_pptx_only_team.py --corpus-project indlab_telegram_news
..\.venv\Scripts\python.exe scripts\smoke_corpus.py
```

## 11. Known limitations

- Indlab team requires DOCX/TXT (or PPTX slide with **text** ФИО).  
- Image-only team slides need OCR.  
- `smoke_pptx_only_team.py` not in default `check_all.ps1` (manual / optional).
