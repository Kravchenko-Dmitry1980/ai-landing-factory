# OCR Engine Benchmark (Stage H.8.4)

Compare optional OCR engines on image-only slides and pick the best by metrics.

## Supported engines

| Engine | Status | Install |
|--------|--------|---------|
| tesseract | stable fallback | Tesseract binary + pytesseract |
| easyocr | optional | `pip install easyocr` |
| paddleocr | optional | `pip install paddleocr paddlepaddle` |
| surya | experimental | `pip install surya-ocr` |

Missing engines are reported but do not crash the benchmark.

## Quick start

```powershell
cd C:\Dima\Projects\CURSOR\Lend

.\scripts\setup_ocr_runtime.ps1 -InstallEasyOCR

cd backend
..\.venv\Scripts\python.exe scripts\benchmark_ocr_engines.py `
  --file "C:\Dima\Projects\CURSOR\Lend\test_corpus\golden\indlab_telegram_news\sources\01_presentation.pptx" `
  --slides 25 `
  --engines tesseract,easyocr,paddleocr `
  --known-name "Татьяна Ерюкова" `
  --known-name "Надежда Глазунова" `
  --known-name "Егор Быков"
```

## Output metrics

Per engine:

- `raw_chars` / `normalized_chars`
- `team_section_detected`
- `accepted_team_count` / `rejected_person_count`
- `known_names_hit_count` (when `--known-name` provided)
- `runtime_ms`
- `error_code` (e.g. paddle oneDNN/PIR failure)
- text previews

## Scoring (deterministic)

```
score =
  accepted_team_count * 10
  + known_names_hit_count * 5
  + team_section_detected * 3
  + min(raw_chars / 300, 5)
  - rejected_person_count * 1
  - error_penalty (if failed)
```

Highest score → `best_engine`.

## Config

```env
OCR_EASYOCR_LANGS=ru,en
OCR_EASYOCR_GPU=false
OCR_ENGINE_PRIORITY=tesseract,easyocr,paddleocr
OCR_ENGINE=auto   # optional, not default
```

`OCR_ENGINE=auto` picks first available engine from `OCR_ENGINE_PRIORITY`.

## Save JSON report

```powershell
..\.venv\Scripts\python.exe scripts\benchmark_ocr_engines.py `
  --file deck.pptx --slides 25 --json `
  --save-report backend/data/ocr_benchmarks/indlab_slide25.json
```

## Related

- [OCR_TEAM_EXTRACTION_H8_3.md](OCR_TEAM_EXTRACTION_H8_3.md)
- [OCR_RUNTIME_SETUP_H8_2.md](OCR_RUNTIME_SETUP_H8_2.md)
