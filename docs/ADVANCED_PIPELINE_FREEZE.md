# Advanced Pipeline Freeze (Stage P.1)

Advanced features are **implemented but optional**. They are not part of the default user path.

## In scope (frozen, no new mandatory deps)

- OCR runtime (`scripts/setup_ocr_runtime.ps1`)
- Engines: EasyOCR, Tesseract, PaddleOCR (optional pip installs)
- OCR team verification gate
- Visual source classifier
- VLM adapter contract (stub / local providers)

## Default product path

- `PRODUCT_MODE=simple`
- `.\run.ps1` — base `backend/requirements.txt` only
- Text-layer extraction + field-level fusion + manual editor fallback
- No OCR/VLM smoke in `check_all.ps1 -Simple`

## Rules

1. **No new advanced dependency** may be required for `.\run.ps1`.
2. Heavy packages live in `backend/requirements-ocr.txt` / `backend/requirements-advanced.txt`, not in base requirements.
3. Do not continue VLM product integration in simple mode; research/advanced only.
4. If extraction is imperfect, prefer **editable landing sections**, not “install another model”.
5. Existing OCR/VLM tests must keep passing when advanced deps are installed.

## Enable advanced (developers)

```env
PRODUCT_MODE=advanced
ADVANCED_VISUAL_PIPELINE=true
ENABLE_ADVANCED_DIAGNOSTICS=true
OCR_ENABLED=true
VLM_ENABLED=false
```

```powershell
.\scripts\setup_ocr_runtime.ps1 -InstallBasic
.\scripts\check_ocr_env.ps1
```

Research / benchmarks: `PRODUCT_MODE=research`, see `README_RUN.md` advanced sections.
