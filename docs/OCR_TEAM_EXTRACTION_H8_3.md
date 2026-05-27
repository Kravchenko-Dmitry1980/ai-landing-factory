# OCR Team Extraction (Stage H.8.3)

Postprocessing and fuzzy team extraction for noisy OCR text from image-only slides.

## Pipeline

```
PPTX image-only slide
  → Tesseract OCR (rus+eng)
  → clean_ocr_text()
  → normalize_ocr_team_text()
  → extract_team_from_ocr_text()
  → FieldFusionEngine (unchanged)
  → contract.team_structured
```

## OCR text normalization

Safe fixes only — no invented names:

| OCR artifact | Normalized |
|--------------|------------|
| `Тимлидпроекта` | `Тимлид проекта` |
| `помошниктиылида` | `помощник тимлида` |
| `\|`, `` ` ``, `©` | spaces / removed |

Team section markers trigger normalization:

- команда проекта
- тимлид проекта
- участники команды проекта
- помощник тимлида
- разработчики

## Fuzzy team extraction

`extract_team_from_ocr_text()`:

1. Detect team section markers
2. Normalize OCR text
3. Parse structured blocks (group lines, name — role)
4. Validate names via strict `team_candidate_validator`
5. Reject low-quality name lines with warnings (no hallucination)

Rejected lines appear in `debug_ocr_source.py` output.

## Tesseract language

Configure in `backend/.env`:

```
OCR_TESSERACT_LANG=rus+eng
```

If `rus` language pack is missing, a warning is emitted:

> Russian language data 'rus' is missing. OCR of Russian names may be poor.

Install Russian data via Tesseract installer (Windows) or `tesseract-ocr-rus` package.

## Debug commands

```powershell
cd C:\Dima\Projects\CURSOR\Lend\backend

..\.venv\Scripts\python.exe scripts\debug_ocr_source.py `
  --file "C:\Dima\Projects\CURSOR\Lend\test_corpus\golden\indlab_telegram_news\sources\01_presentation.pptx" `
  --slides 25 `
  --require-ocr
```

Output sections:

- OCR raw preview
- OCR normalized preview
- team section detected
- accepted / rejected candidates
- tesseract lang

## Smoke test

```powershell
..\.venv\Scripts\python.exe scripts\smoke_pptx_ocr_team.py --require-ocr
..\.venv\Scripts\python.exe scripts\smoke_pptx_ocr_team.py --min-team-candidates 2
..\.venv\Scripts\python.exe scripts\smoke_pptx_ocr_team.py --strict-team-count 5
```

## Known limitations

- Heavily corrupted OCR names are rejected, not repaired
- No cross-project name cache / hallucination
- Full team recovery depends on Tesseract quality and `rus` language pack
- PPTX-only projects without DOCX may extract fewer members than golden contract

## Related docs

- [OCR_RUNTIME_SETUP_H8_2.md](OCR_RUNTIME_SETUP_H8_2.md)
- [OCR_LAYER_H8.md](OCR_LAYER_H8.md)
