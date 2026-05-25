# OCR Layer (Stage H.8)

## Why OCR is required

Some project materials store critical facts only as raster content:

- image-only PPTX slides (Canva/Figma/Gamma exports);
- scanned PDF pages;
- screenshots embedded in DOCX/PPTX;
- diagrams and tables rendered as pictures.

The Indlab case showed the problem clearly: slide 25 contains the team visually, but `python-pptx` text extraction returns **0 chars** for that slide. Without OCR, `team` stays missing even when the slide is uploaded.

## Architecture

```
ExtractionResult (text layer)
  → missing-field detection (team)
  → OcrDecision (targeted)
  → renderers (PPTX images / PDF pages)
  → OcrEngine (PaddleOCR → Tesseract fallback)
  → OCR text cleaner
  → virtual evidence files (*.pptx#ocr-slide-N)
  → EvidenceExtractor → TeamParser → FieldFusionEngine
```

OCR is **not** run for every file. It activates when:

- slide/page text `< OCR_MIN_TEXT_CHARS` and images exist;
- team is missing;
- image-only team slide is suspected.

## Feature flags

Set in `backend/.env`:

```env
OCR_ENABLED=true
OCR_ENGINE=paddleocr
OCR_FALLBACK_ENGINE=tesseract
OCR_DPI=250
OCR_MAX_PAGES=30
OCR_MAX_SLIDES=40
OCR_MIN_TEXT_CHARS=40
OCR_CACHE_ENABLED=true
```

Default: `OCR_ENABLED=false` for safe rollout.

When disabled, pipeline emits:

> OCR disabled. Image-only slides/pages may not be parsed.

## Engine options

| Engine | Python package | System dependency |
|--------|----------------|-----------------|
| PaddleOCR (primary) | `paddleocr` | optional GPU |
| Tesseract (fallback) | `pytesseract`, `Pillow` | Tesseract binary |

If neither engine is installed, pipeline continues with warnings (no crash).

Optional PDF OCR rendering:

- `pymupdf` (`fitz`) for page rasterization.

## Diagnostics

```powershell
cd C:\Dima\Projects\CURSOR\Lend\backend

..\.venv\Scripts\python.exe scripts\debug_ocr_source.py `
  --file "C:\path\to\presentation.pptx" `
  --slides 25
```

Optional smoke:

```powershell
..\.venv\Scripts\python.exe scripts\smoke_pptx_ocr_team.py
..\.venv\Scripts\python.exe scripts\smoke_pptx_ocr_team.py --require-ocr
```

## Limitations

- OCR text can be noisy; names are validated, not hallucinated.
- DOCX embedded-image OCR path is minimal (requires `has_images` metadata).
- Synthetic corpus PPTX built from `.pptx.txt` snapshots may not reproduce image-only slides.
- Heavy OCR is optional in `check_all.ps1` (`-SkipOcrSmoke` default).

## Future production path

1. Enable `OCR_ENABLED=true` in staging.
2. Install PaddleOCR + Tesseract on worker nodes.
3. Add Prometheus metrics for OCR latency/cache hit rate.
4. Promote `-SkipOcrSmoke:$false` after stable engine install.
