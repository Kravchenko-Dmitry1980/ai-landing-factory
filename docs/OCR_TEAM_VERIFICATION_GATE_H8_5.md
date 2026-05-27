# OCR Team Verification Gate (Stage H.8.5)

## Проблема

OCR-движки (EasyOCR, Tesseract) могут извлекать **похожие, но искажённые ФИО** с image-only слайдов. Старый pipeline проверял только «похоже ли на имя» (`team_candidate_validator`), но не проверял:

- подтверждение другим источником (DOCX/TXT);
- OCR confidence;
- fuzzy match к trusted roster;
- наличие роли/вклада;
- безопасность для публичного export.

**Пример Indlab slide 25 (EasyOCR):**

| OCR raw | Проблема |
|---------|----------|
| Татьяна Залоротец | искажённая фамилия |
| Наденда Глазунова | OCR-опечатка |
| Денис Калюаный | OCR-артефакт |
| Александр Егорсв | обрезанная фамилия |

Такие имена **не должны** попадать в публичный HTML export без verification.

## Статусная модель

| Status | Значение | Public export |
|--------|----------|---------------|
| `verified` | Подтверждено trusted source или strong fuzzy match | ✅ Да |
| `needs_review` | OCR-only, weak match, нет роли | ❌ Нет |
| `probable` | Не подтверждено, но не явный мусор | ❌ Нет |
| `rejected` | Garbage, mixed script, низкий quality score | ❌ Нет |

## Trusted sources

**Доверенные:**

1. DOCX/TXT structured landing с секцией «Команда проекта»
2. Manually approved roster (future API)
3. `expected_contract.yml` (только corpus/smoke tests)
4. `known_names` list (benchmark CLI)
5. Previously verified roster same `project_id` (future)

**Недоверенные:**

- OCR-only candidates без cross-source confirmation
- PPTX image-only OCR без fuzzy match к roster
- Low-confidence OCR text
- Пустая роль + пустые contributions

## Pipeline

```
team candidates (fusion/assembly)
  → TeamVerificationService.verify()
  → classification: verified | needs_review | probable | rejected
  → contract.fidelity.team_structured = verified only
  → ocr_review_candidates → evidence / team-review API
  → StyledHtmlExporter uses export_policy (defense in depth)
```

## Public export policy

В публичный HTML попадает член команды только если:

1. `verification_status == verified`, **или**
2. non-OCR trusted source с valid name (до verification gate)

**Не попадает:**

- `needs_review`, `probable`, `rejected`
- OCR-only без match к trusted roster
- `name_quality_score < 0.5`

Если `verified_count == 0` и есть OCR review candidates:

- team section **скрывается** в public export
- warning в evidence: *«OCR found possible team members, but they require verification before public export.»*

## Fuzzy correction

Коррекция OCR-имени (`corrected_name`) применяется **только** при:

- `match_score >= 0.88` (strong fuzzy)
- trusted source существует

Weak fuzzy (0.75–0.88) → `needs_review` с `matched_trusted_name` как подсказка, **без** auto-correction.

## API

```
GET /api/v1/projects/{project_id}/team-review
```

Returns: `verified`, `needs_review`, `rejected`, `probable`, reasons.

Evidence report (`/evidence-report`) включает:

- `team_verification_report`
- `ocr_review_candidates`
- `team_publication_policy`

## Indlab example

**Before H.8.5:** public export содержал OCR-искажения.

**After H.8.5:**

- DOCX team (15 verified) → export OK
- OCR bad names → `needs_review`, excluded from export
- С trusted roster: `Наденда` → suggested match `Надежда Глазунова`, verified only if score ≥ 0.88

## Smoke / tests

```powershell
cd C:\Dima\Projects\CURSOR\Lend\backend

..\.venv\Scripts\python.exe scripts\smoke_ocr_team_verification.py `
  --project indlab_telegram_news

..\.venv\Scripts\python.exe -m pytest `
  tests/test_team_verification_service.py `
  tests/test_export_team_verification_policy.py `
  tests/test_ocr_team_verification_indlab.py -q
```

## Known limitations

- Manual approval API — следующий этап
- OCR confidence не всегда доступен на уровне отдельного ФИО
- `expected_contract.yml` team names используются только в smoke/corpus, не в production runtime

## Future: manual approval UI

UI: «Найдены OCR-кандидаты команды, требуется проверка» с raw/suggested match/status/source/engine.
