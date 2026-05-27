# OCR Runtime Setup (Stage H.8.2)

Windows-focused guide for stable local OCR diagnostics.

## Quick start

```powershell
cd C:\Dima\Projects\CURSOR\Lend

.\scripts\check_ocr_env.ps1
.\scripts\setup_ocr_runtime.ps1 -WriteEnv
.\scripts\setup_ocr_runtime.ps1 -InstallBasic
.\scripts\setup_ocr_runtime.ps1 -InstallPaddle
.\scripts\check_ocr_env.ps1 -RequireOcr -TestImage
```

## OCR readiness contract

An OCR engine is **ready** only when all of the following hold:

1. Python package installed
2. Backend dependency installed (paddlepaddle / Tesseract binary)
3. Model/init OK
4. Inference smoke test on synthetic image succeeds (no runtime exception)
5. Extracted chars > 0, or valid empty result without runtime error

`init_ok=True` alone is **not** sufficient. Use `-RequireOcr` or `-TestImage` to run inference smoke.

## What check_ocr_env reports

| Check | Meaning |
|-------|---------|
| OCR_ENABLED | Feature flag from backend/.env |
| paddleocr package | Python package import |
| Paddle init_ok / model_ready | Adaptive init + model download |
| Paddle inference_ok | Synthetic image OCR without runtime exception |
| pytesseract package | Python wrapper |
| Tesseract binary | Windows `tesseract.exe` in PATH |
| Pillow / PyMuPDF | Image and PDF rendering deps |
| cache dir | `backend/data/ocr_cache` writable |
| test image OCR | Router-level synthetic OCR smoke |
| Indlab slide 25 | PPTX binary has team image slide |
| Paddle env flags | `FLAGS_use_mkldnn`, `FLAGS_enable_pir_api`, etc. |

JSON mode:

```powershell
.\scripts\check_ocr_env.ps1 -Json -RequireOcr -TestImage
```

## Proxy / SOCKS issue

If pip or Paddle model download fails behind SOCKS proxy:

```powershell
$env:NO_PROXY="*"
pip install PySocks
pip install paddleocr
```

`setup_ocr_runtime.py` detects SOCKS proxies and prints guidance before installs.

## PaddleOCR model warmup

```powershell
cd backend
..\.venv\Scripts\python.exe scripts\warmup_ocr_models.py --engine paddleocr
..\.venv\Scripts\python.exe scripts\warmup_ocr_models.py --engine paddleocr --test-image
```

Warmup separates **init** from **inference smoke**:

- `OK: PaddleOCR initialized` — models loaded
- `inference_ok: True` — synthetic OCR succeeded

Exit code 1 if inference fails (unless `--allow-init-only`).

Typical model cache paths on Windows:

- `%USERPROFILE%\.paddleocr`
- `%USERPROFILE%\.paddlex\official_models`

If init fails with HuggingFace / model source errors:

1. Check internet/proxy.
2. Run warmup script.
3. Re-run `check_ocr_env.ps1 -RequireOcr`.

## Known unstable stack (Windows)

**paddleocr 3.5.0 + paddlepaddle 3.3.1** may initialize but fail inference with:

```
ConvertPirAttribute2RuntimeAttribute not support [pir::ArrayAttribute<pir::DoubleAttribute>]
(at ... onednn_instruction.cc:118)
```

Classification: `error_code=paddleocr_pir_onednn_unimplemented`, `failure_stage=inference`.

### Option A — Tesseract fallback (recommended for screenshots/text slides)

Install [Tesseract OCR for Windows](https://github.com/UB-Mannheim/tesseract/wiki) and add to PATH.

### Option B — Disable oneDNN / PIR via env flags

```powershell
$env:FLAGS_use_mkldnn="0"
$env:FLAGS_enable_pir_api="0"
# or
$env:PADDLE_DISABLE_ONEDNN="true"
$env:PADDLE_DISABLE_PIR="true"

cd backend
..\.venv\Scripts\python.exe scripts\warmup_ocr_models.py --engine paddleocr
```

Do not set these globally until verified on your machine.

### Option C — Pin older Paddle stack

```powershell
pip uninstall paddleocr paddlepaddle -y
pip install paddlepaddle==3.0.0 paddleocr==3.0.0
```

### Option D — PaddleOCR 2.x line

```powershell
pip uninstall paddleocr paddlepaddle -y
pip install paddlepaddle==2.6.2 paddleocr==2.7.3
```

Do not hard-pin in requirements until verified on target hardware.

## Tesseract on Windows

Python package alone is not enough:

```powershell
pip install pytesseract Pillow
```

Install binary:

- [Tesseract OCR for Windows](https://github.com/UB-Mannheim/tesseract/wiki)
- Add `C:\Program Files\Tesseract-OCR` to PATH

Verify:

```powershell
tesseract --version
.\scripts\check_ocr_env.ps1 -RequireOcr
```

## Debug one document

```powershell
cd backend
..\.venv\Scripts\python.exe scripts\debug_ocr_source.py `
  --file "C:\Dima\Projects\CURSOR\Lend\test_corpus\golden\indlab_telegram_news\sources\01_presentation.pptx" `
  --slides 25 `
  --require-ocr
```

Without `--require-ocr`, missing engines produce classified warnings (no traceback).

## check_all integration

Default QA pipeline skips OCR:

```powershell
.\scripts\check_all.ps1
```

Optional OCR smoke:

```powershell
.\scripts\check_all.ps1 -RunOcrSmoke
```

## Common errors

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Unknown argument: show_log` | Old Paddle init | Fixed in H.8.1 |
| `model source blocked` | No internet / HF blocked | warmup + NO_PROXY |
| `tesseract is not installed` | Binary missing | Install Tesseract for Windows |
| `OCR disabled` | OCR_ENABLED=false | Set true in backend/.env |
| init_ok=True, inference_ok=False | oneDNN/PIR runtime bug | env flags / Tesseract / pin versions |
| ready=True but OCR broken | Old check (init-only) | Use -RequireOcr -TestImage |

## Limitations

- Paddle model download requires network on first run.
- Synthetic corpus `.pptx.txt` does not reproduce image-only slides.
- OCR remains optional for default CI/check_all.
