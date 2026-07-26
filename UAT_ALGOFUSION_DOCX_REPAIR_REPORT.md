# UAT Algofusion DOCX Repair Report

Дата: 2026-07-26 · Проект: `ai-landing-factory-fresh` · Commit базы: `495f44c`

## 1. Problem

После загрузки `Лендинг_АлгоФьюжн_CV.docx` в preview/export попадали только
фрагменты (короткий title, generic bullets, нули в метриках команды/стека).
Полные секции DOCX (цели, задачи, стек, результаты, перспективы, команда, фраза)
терялись до renderer.

## 2. Root Cause

| Stage | Verdict |
|---|---|
| extractor | OK — текст извлечён (~9583 chars, 107 paragraphs) |
| section parser | Partial — не ловил `Перспективы развития` / `Стажировка` |
| metrics extractor | FAIL — нулевые fallback cards |
| team extractor | Partial — тимлид и вклад терялись |
| contract mapper | **FAIL** — DOCX классифицировался как `team_list`, structured path не включался |
| renderer/exporter | Downstream — пустой contract → пустой landing |

Главный баг: `SourceInventoryBuilder` выбирал `team_list` (score 0.9) вместо
`ready_landing_doc` из‑за плотности русских ФИО + «тимлид», поэтому
`has_single_high_confidence_ready_doc()` возвращал `False`.

Подробности: `.runtime/diagnostics/algofusion/12_root_cause.md`

## 3. Changes

| File | Change | Why |
|---|---|---|
| `backend/app/services/evidence/source_inventory.py` | Prefer ready_landing_doc over team_list; more markers | Open structured path |
| `backend/app/services/contract_fidelity/structured_landing_parser.py` | Стажировка / Перспективы / Участники / lead inject | Full section coverage |
| `backend/app/services/contract_fidelity/landing_document_detector.py` | Same aliases | Detection confidence |
| `backend/app/services/contract_fidelity/stack_parser.py` | Inline `Cat: a, b` + CV categories | Tech stack cards |
| `backend/app/services/contract_fidelity/team_parser.py` | `Name (Role): contrib` | Lead + roster |
| `backend/app/services/export/wow/wow_pipeline.py` | Domain CV/FSM 8-stage pipeline | Replace generic flow |
| `backend/app/services/export/wow/wow_metrics.py` | Labeled metrics, min 8, no zero pad | Impact cards |
| `backend/app/services/export/wow/wow_sections.py` | Essence/results/team cards | WOW completeness |
| `backend/app/services/export/wow_bundle_data.py` | Prefer quote subtitle | Phrase in ZIP |
| `frontend/src/lib/wowHeroMapping.ts` | Mirror CV pipeline + metrics | Preview parity |
| `backend/tests/test_algofusion_*.py` | New acceptance tests | Regression lock |
| `backend/tests/fixtures/algofusion_landing.txt` | Plain-text fixture | No binary DOCX in tests |

## 4. Source Coverage

| Source section | Extracted | Rendered | Exported |
|---|---|---|---|
| Title / identity | Yes | Yes | Yes |
| Заказчик / Стажировка / Тимлид | Yes | Yes | Yes |
| Суть проекта | Yes | Yes | Yes |
| Цель / задачи | Yes | Yes | Yes |
| Tech stack (5 groups) | Yes | Yes | Yes |
| Результаты | Yes (9+) | Yes | Yes |
| Перспективы | Yes (6) | Yes | Yes |
| Команда (11) | Yes | Yes | Yes |
| Фраза проекта | Yes | Yes | Yes |
| CV pipeline | Derived | Yes (WOW) | Yes |

## 5. Key Facts Validation

UAT project: `fc390ae9-f0e6-42b4-bfb8-8bbc980d30e7`

| Fact | Preview | HTML | WOW ZIP |
|---|---|---|---|
| ООО «АлгоФьюжн» | Yes | Yes | Yes |
| YOLO v11 nano | Yes | Yes | Yes |
| ByteTrack | Yes | Yes | Yes |
| Random Forest | Yes | Yes | Yes |
| Compliance Engine | Yes | Yes | Yes |
| CASHIER WATCH | Yes | Yes | Yes |
| mAP50 = 0.956 | Yes | Yes | As metric `mAP50=0.956` |
| 95.12% / 97% | Yes | Yes | Yes |
| Кус / Кривонос / Гречко / Семин | Yes | Yes | Yes |
| цифровой паспорт | Yes | Yes | Yes |

## 6. Tests

| Test | Result |
|---|---|
| `test_algofusion_docx_extraction.py` | PASS |
| `test_algofusion_contract_mapping.py` | PASS |
| `test_algofusion_export_contains_key_facts.py` | PASS |
| `test_product_mode_simple` + university + wow + llm | 39 passed |
| Related parser/detector/stack/wow suite | 47 passed |

## 7. Runtime Validation

| Check | Result |
|---|---|
| `GET /health` | 200 ok |
| Frontend `:3000` | 200 |
| DOCX upload → structured | `parser_mode=structured`, team=11, stack=30 |
| Preview browser | Full content visible (ARIA) |
| Standard HTML export | 29618 B, missing=[] |
| WOW ZIP | index + assets + landing-contract.json |
| Export buttons in UI | Standard HTML 200, WOW ZIP 200 |
| semantic-landing 404 | Expected optional endpoint, non-blocker |

## 8. Remaining Risks

- Некоторые role/contribution swap для 1–2 участников (Андреев/Федченко) — heuristic team parser.
- WOW interactive bundle хранит mAP50 как `{label,value}`, не как строку `mAP50 = 0.956`.
- Старые проекты с уже сохранённым пустым contract нужно перезагрузить/перегенерировать.
- Full `pytest tests/` не гонялся (известный test debt вне scope).

## 9. Verdict

**GO FOR DEMO ONLY**

Локальный DOCX → full landing → export цикл восстановлен и проверен.
Production deploy / FreeModel AI — вне этой задачи, без изменений.
