"""OCR runtime environment diagnostics."""

from __future__ import annotations

import importlib
import importlib.util
import logging
import os
from io import BytesIO
from pathlib import Path

from app.config import settings
from app.schemas.ocr_runtime import EngineRuntimeStatus, OcrRuntimeStatus
from app.services.ocr.engines.paddleocr_engine import classify_paddle_error

logger = logging.getLogger(__name__)

PADDLE_MODEL_GUIDANCE = (
    "PaddleOCR package is installed but model initialization failed. "
    "Possible causes: no internet; model source blocked; cache permission issue; "
    "incompatible PaddleOCR/PaddlePaddle versions. "
    "Run: python scripts/warmup_ocr_models.py --engine paddleocr"
)

TESSERACT_BINARY_GUIDANCE = (
    "Tesseract Python wrapper is installed, but Windows binary is missing. "
    "Install Tesseract OCR for Windows, then add installation directory to PATH. "
    "Example: C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
)

PADDLE_INFERENCE_FAILURE_GUIDANCE = (
    "PaddleOCR initializes but inference fails. Try:\n"
    "  1. set FLAGS_use_mkldnn=0\n"
    "  2. set FLAGS_enable_pir_api=0\n"
    "  3. use Tesseract fallback\n"
    "  4. pin compatible PaddleOCR/PaddlePaddle versions"
)


def apply_paddle_env_flags() -> None:
    """Apply optional Paddle runtime flags from env before import/init."""
    if os.environ.get("PADDLE_DISABLE_ONEDNN", "").lower() in ("1", "true", "yes"):
        os.environ.setdefault("FLAGS_use_mkldnn", "0")
    if os.environ.get("PADDLE_DISABLE_PIR", "").lower() in ("1", "true", "yes"):
        os.environ.setdefault("FLAGS_enable_pir_api", "0")


def get_paddle_env_flags() -> dict[str, str | None]:
    return {
        "FLAGS_use_mkldnn": os.environ.get("FLAGS_use_mkldnn"),
        "FLAGS_enable_pir_api": os.environ.get("FLAGS_enable_pir_api"),
        "PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK": os.environ.get(
            "PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"
        ),
        "PADDLE_DISABLE_ONEDNN": os.environ.get("PADDLE_DISABLE_ONEDNN"),
        "PADDLE_DISABLE_PIR": os.environ.get("PADDLE_DISABLE_PIR"),
    }


def package_installed(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def package_version(name: str) -> str | None:
    try:
        module = importlib.import_module(name)
    except Exception:
        return None
    version = getattr(module, "__version__", None)
    return str(version) if version else None


def detect_socks_proxy() -> tuple[bool, dict[str, str]]:
    import urllib.request

    proxies = urllib.request.getproxies()
    socks = any(
        "socks" in str(value).lower()
        for value in proxies.values()
        if value
    )
    return socks, proxies


def classify_paddle_init_error(error: str) -> tuple[str, list[str]]:
    error_code, _stage, _action = classify_paddle_error(error, stage="init")
    warnings: list[str] = []
    if error_code in ("model_download_failed", "unknown_init_error"):
        warnings.append(PADDLE_MODEL_GUIDANCE)
    elif error_code == "incompatible_version":
        warnings.append("PaddleOCR version may be incompatible with current init kwargs.")
    return error_code, warnings


def _is_inference_runtime_error(error: str) -> bool:
    error_code, stage, _ = classify_paddle_error(error, stage="inference")
    return stage == "inference" and error_code != "unknown_init_error"


def run_engine_inference_smoke(engine_name: str) -> tuple[bool, int, str | None]:
    """Run synthetic image OCR against a specific engine.

    Returns (inference_ok, chars, error_message).
    inference_ok=True when OCR completes without runtime exception.
    """
    image_bytes = generate_test_image_bytes()
    if image_bytes is None:
        return False, 0, "Pillow not available for synthetic OCR test image"

    if engine_name == "paddleocr":
        from app.services.ocr.engines.paddleocr_engine import PaddleOcrEngine

        engine = PaddleOcrEngine()
        if not engine._ensure_engine():
            return False, 0, engine._init_error or "PaddleOCR init failed"
    elif engine_name == "tesseract":
        from app.services.ocr.engines.tesseract_engine import TesseractOcrEngine

        engine = TesseractOcrEngine()
        if not engine.is_available():
            return False, 0, "Tesseract not available (wrapper or binary missing)"
    elif engine_name == "easyocr":
        from app.services.ocr.engines.easyocr_engine import EasyOcrEngine

        engine = EasyOcrEngine()
        if not engine.is_available():
            return False, 0, "EasyOCR not available"
    else:
        return False, 0, f"Unknown engine: {engine_name}"

    result = engine.extract_text(image_bytes)
    chars = len((result.text or "").strip())

    for warning in result.warnings or []:
        if _is_inference_runtime_error(warning) or warning.startswith("PaddleOCR failed:"):
            return False, chars, warning

    if engine_name == "paddleocr" and result.warnings:
        for warning in result.warnings:
            low = warning.lower()
            if "failed" in low or "error" in low:
                return False, chars, warning

    return True, chars, None


def check_paddleocr_status(*, run_inference: bool = False) -> EngineRuntimeStatus:
    status = EngineRuntimeStatus()
    apply_paddle_env_flags()

    if not package_installed("paddleocr"):
        status.error = "paddleocr package is not installed"
        status.failure_stage = "import"
        status.error_code = "paddleocr_missing"
        status.warnings.append("Install with: pip install paddleocr")
        return status

    status.package_installed = True
    status.version = package_version("paddleocr")

    if not package_installed("paddle"):
        status.error = "paddlepaddle is not installed"
        status.failure_stage = "dependency"
        status.error_code = "paddlepaddle_missing"
        status.recommended_action = "pip install paddlepaddle"
        status.warnings.append("Install with: pip install paddlepaddle")
        return status

    paddle_ver = package_version("paddle")
    if paddle_ver:
        status.warnings.append(f"paddle version: {paddle_ver}")

    try:
        from app.services.ocr.engines.paddleocr_engine import PaddleOcrEngine

        engine = PaddleOcrEngine()
        if not engine._ensure_engine():
            error = engine._init_error or "PaddleOCR init failed"
            status.error = error
            error_code, extra = classify_paddle_init_error(error)
            status.error_code = error_code
            status.failure_stage = "init"
            code, stage, action = classify_paddle_error(error, stage="init")
            status.error_code = code
            status.failure_stage = stage
            status.recommended_action = action
            status.warnings.extend(extra)
            status.init_ok = False
            status.model_ready = False
            return status

        status.init_ok = True
        status.model_ready = True
        if engine._init_kwargs:
            status.warnings.append(f"init kwargs: {engine._init_kwargs}")
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        status.error = error
        error_code, extra = classify_paddle_init_error(error)
        code, stage, action = classify_paddle_error(error, stage="init")
        status.error_code = code
        status.failure_stage = stage
        status.recommended_action = action
        status.warnings.extend(extra)
        return status

    if run_inference and status.init_ok:
        inference_ok, chars, err = run_engine_inference_smoke("paddleocr")
        status.inference_ok = inference_ok
        status.test_image_chars = chars
        status.test_image_ok = inference_ok and chars > 0
        if not inference_ok:
            error = err or "PaddleOCR inference failed on test image"
            status.error = error
            code, stage, action = classify_paddle_error(error, stage="inference")
            status.error_code = code
            status.failure_stage = stage
            status.recommended_action = action
            status.warnings.append(PADDLE_INFERENCE_FAILURE_GUIDANCE)
        elif chars == 0:
            status.warnings.append("PaddleOCR inference completed but test image returned 0 chars")

    return status


def check_tesseract_status(*, run_inference: bool = False) -> EngineRuntimeStatus:
    status = EngineRuntimeStatus()
    if not package_installed("pytesseract"):
        status.error = "pytesseract package is not installed"
        status.failure_stage = "import"
        status.error_code = "pytesseract_missing"
        status.warnings.append("Install with: pip install pytesseract")
        status.binary_available = False
        return status

    status.package_installed = True
    status.version = package_version("pytesseract")

    try:
        import pytesseract

        version = pytesseract.get_tesseract_version()
        status.binary_available = True
        status.init_ok = True
        status.model_ready = True
        status.warnings.append(f"tesseract binary version: {version}")
    except Exception as exc:
        status.binary_available = False
        status.init_ok = False
        status.model_ready = False
        status.error = f"{type(exc).__name__}: {exc}"
        status.failure_stage = "dependency"
        status.error_code = "tesseract_binary_missing"
        status.recommended_action = "Install Tesseract OCR for Windows as fallback."
        status.warnings.append(TESSERACT_BINARY_GUIDANCE)
        return status

    if run_inference and status.init_ok:
        inference_ok, chars, err = run_engine_inference_smoke("tesseract")
        status.inference_ok = inference_ok
        status.test_image_chars = chars
        status.test_image_ok = inference_ok and chars > 0
        if not inference_ok:
            status.error = err or "Tesseract inference failed on test image"
            status.failure_stage = "inference"
            status.error_code = "tesseract_inference_failed"

    return status


def check_easyocr_status(*, run_inference: bool = False) -> EngineRuntimeStatus:
    status = EngineRuntimeStatus()
    if not package_installed("easyocr"):
        status.error = "easyocr package is not installed"
        status.failure_stage = "import"
        status.error_code = "easyocr_missing"
        status.warnings.append("Install with: pip install easyocr")
        return status

    status.package_installed = True
    status.version = package_version("easyocr")

    try:
        from app.services.ocr.engines.easyocr_engine import EasyOcrEngine

        engine = EasyOcrEngine()
        if not engine.is_available():
            status.error = engine._init_error or "EasyOCR not available"
            status.failure_stage = "import"
            status.error_code = "easyocr_unavailable"
            return status
        status.warnings.append(f"langs: {settings.ocr_easyocr_langs}")
        if run_inference:
            if not engine._ensure_reader():
                status.error = engine._init_error or "EasyOCR init failed"
                status.failure_stage = "init"
                status.error_code = "easyocr_init_failed"
                return status
            status.init_ok = True
            status.model_ready = True
        else:
            status.init_ok = True
            status.model_ready = None
    except Exception as exc:
        status.error = f"{type(exc).__name__}: {exc}"
        status.failure_stage = "init"
        status.error_code = "easyocr_init_failed"
        return status

    if run_inference and status.init_ok:
        inference_ok, chars, err = run_engine_inference_smoke("easyocr")
        status.inference_ok = inference_ok
        status.test_image_chars = chars
        status.test_image_ok = inference_ok and chars > 0
        if not inference_ok:
            status.error = err or "EasyOCR inference failed on test image"
            status.failure_stage = "inference"
            status.error_code = "easyocr_inference_failed"

    return status


def check_surya_status() -> EngineRuntimeStatus:
    status = EngineRuntimeStatus()
    if not package_installed("surya"):
        status.error = "surya package is not installed"
        status.failure_stage = "import"
        status.error_code = "surya_missing"
        status.warnings.append("Experimental. Install with: pip install surya-ocr")
        return status

    status.package_installed = True
    status.version = package_version("surya")
    try:
        from app.services.ocr.engines.surya_engine import SuryaOcrEngine

        engine = SuryaOcrEngine()
        status.init_ok = engine.is_available()
        status.model_ready = status.init_ok
        if not status.init_ok:
            status.error = engine._init_error or "Surya OCR package not installed or API unsupported."
            status.error_code = "surya_unavailable"
            status.warnings.append(status.error)
    except Exception as exc:
        status.error = f"{type(exc).__name__}: {exc}"
        status.error_code = "surya_unavailable"
    return status


def ensure_cache_dir() -> tuple[Path, bool]:
    cache_dir = settings.ocr_cache_dir
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        test_file = cache_dir / ".write_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        return cache_dir, True
    except Exception as exc:
        logger.debug("OCR cache dir not writable: %s", exc)
        return cache_dir, False


def generate_test_image_bytes() -> bytes | None:
    if not package_installed("PIL"):
        return None
    try:
        from PIL import Image, ImageDraw

        img = Image.new("RGB", (480, 120), color="white")
        draw = ImageDraw.Draw(img)
        text = "OCR test 123"
        draw.text((20, 40), text, fill="black")
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return None


def run_test_image_ocr() -> tuple[bool, int, str | None]:
    """Run OCR smoke via router-selected engine (primary + fallback)."""
    image_bytes = generate_test_image_bytes()
    if image_bytes is None:
        return False, 0, "Pillow not available for synthetic OCR test image"

    from app.services.ocr.ocr_router import _select_engine

    engine = _select_engine()
    if engine is None:
        return False, 0, "No OCR engine ready for test image"

    result = engine.extract_text(image_bytes)
    chars = len((result.text or "").strip())

    for warning in result.warnings or []:
        if _is_inference_runtime_error(warning) or warning.startswith("PaddleOCR failed:"):
            return False, chars, warning

    if chars > 0:
        return True, chars, None
    warning = "; ".join(result.warnings) if result.warnings else "OCR returned empty text"
    return False, 0, warning


def check_indlab_slide25(pptx_path: Path | None = None) -> tuple[bool | None, str]:
    default = (
        Path(__file__).resolve().parents[4]
        / "test_corpus"
        / "golden"
        / "indlab_telegram_news"
        / "sources"
        / "01_presentation.pptx"
    )
    path = pptx_path or default
    if not path.is_file():
        return None, f"Indlab PPTX not found: {path}"

    try:
        from app.services.ocr.renderers.pptx_image_extractor import extract_pptx_images_by_slide

        images = [img for img in extract_pptx_images_by_slide(path) if img.slide_index == 25]
        if not images:
            return False, "Slide 25 has no embedded images in PPTX binary"
        return True, f"Slide 25 has {len(images)} image(s), {len(images[0].image_bytes)} bytes"
    except Exception as exc:
        return False, f"Indlab slide 25 check failed: {exc}"


def _engine_fully_ready(engine: EngineRuntimeStatus, *, require_inference: bool) -> bool:
    if not engine.init_ok:
        return False
    if engine.model_ready is False:
        return False
    if engine.binary_available is False:
        return False
    if require_inference:
        return engine.inference_ok is True
    if engine.inference_ok is False:
        return False
    return True


def any_engine_ready(status: OcrRuntimeStatus, *, require_inference: bool = False) -> bool:
    engines = (
        status.paddleocr,
        status.tesseract,
        status.easyocr,
        status.surya,
    )
    return any(_engine_fully_ready(e, require_inference=require_inference) for e in engines)


def build_recommended_action(status: OcrRuntimeStatus, *, require_inference: bool = False) -> str:
    if not status.ocr_enabled:
        return "OCR is disabled. Set OCR_ENABLED=true in backend/.env when ready."

    paddle = status.paddleocr
    tess = status.tesseract

    if paddle.init_ok and paddle.inference_ok is False:
        if tess.binary_available is False:
            return (
                "Install Tesseract OCR for Windows as fallback. "
                "PaddleOCR inference failed; Tesseract binary is missing."
            )
        actions = [
            "PaddleOCR initializes but inference fails. Try:",
            "1. set FLAGS_use_mkldnn=0",
            "2. set FLAGS_enable_pir_api=0",
            "3. use Tesseract fallback",
            "4. pin compatible PaddleOCR/PaddlePaddle versions",
        ]
        if paddle.recommended_action:
            actions.append(f"Detail: {paddle.recommended_action}")
        return " ".join(actions)

    if any_engine_ready(status, require_inference=require_inference):
        if status.test_image_ok is False and require_inference:
            return "Engine initialized but test image OCR failed. Run warmup_ocr_models.py."
        return "OCR runtime ready. Use debug_ocr_source.py for document-level checks."

    if not paddle.package_installed and not tess.package_installed:
        return "Run: .\\scripts\\setup_ocr_runtime.ps1 -InstallBasic -InstallPaddle"

    if paddle.package_installed and not paddle.init_ok:
        return "PaddleOCR installed but models not ready. Run warmup_ocr_models.py --engine paddleocr"

    if tess.package_installed and tess.binary_available is False:
        return "Install Tesseract OCR for Windows binary and add to PATH."

    if require_inference:
        return (
            "No OCR engine passed inference smoke test. "
            "Try env flags, Tesseract fallback, or version pinning."
        )

    return "Run: .\\scripts\\setup_ocr_runtime.ps1 then .\\scripts\\check_ocr_env.ps1 -RequireOcr"


def collect_ocr_runtime_status(
    *,
    test_image: bool = False,
    require_inference: bool = False,
    test_pptx: Path | None = None,
    test_slides: list[int] | None = None,
) -> OcrRuntimeStatus:
    run_inference = test_image or require_inference
    cache_dir, cache_writable = ensure_cache_dir()
    paddle = check_paddleocr_status(run_inference=run_inference)
    tesseract = check_tesseract_status(run_inference=run_inference)
    easyocr = check_easyocr_status(run_inference=False)
    surya = check_surya_status()

    status = OcrRuntimeStatus(
        ocr_enabled=settings.ocr_enabled,
        configured_engine=settings.ocr_engine,
        fallback_engine=settings.ocr_fallback_engine,
        paddleocr=paddle,
        tesseract=tesseract,
        easyocr=easyocr,
        surya=surya,
        pillow_available=package_installed("PIL"),
        pymupdf_available=package_installed("fitz"),
        cache_enabled=settings.ocr_cache_enabled,
        cache_dir=str(cache_dir),
        cache_dir_writable=cache_writable,
    )

    if not settings.ocr_cache_enabled:
        status.warnings.append("OCR_CACHE_ENABLED=false; OCR results will not be cached.")

    if not cache_writable:
        status.errors.append(f"OCR cache dir is not writable: {cache_dir}")

    if not status.pillow_available:
        status.warnings.append("Pillow not installed. Required for image OCR and synthetic tests.")

    if not status.pymupdf_available:
        status.warnings.append("PyMuPDF (fitz) not installed. PDF page OCR rendering will be skipped.")

    env_flags = get_paddle_env_flags()
    for key, value in env_flags.items():
        status.warnings.append(f"{key}={value if value is not None else '(unset)'}")

    socks, proxies = detect_socks_proxy()
    if socks:
        status.warnings.append(
            "SOCKS proxy detected. Set NO_PROXY=* or install PySocks before pip install."
        )
        if proxies:
            status.warnings.append(f"Detected proxies: {proxies}")

    if not status.ocr_enabled:
        status.warnings.append("OCR disabled. Image-only slides/pages may not be parsed.")

    if run_inference:
        ok, chars, err = run_test_image_ocr()
        status.test_image_ok = ok
        status.test_image_chars = chars
        if err:
            status.warnings.append(f"Test image OCR (router): {err}")

    indlab_ok, indlab_note = check_indlab_slide25(test_pptx)
    status.indlab_slide25_ready = indlab_ok
    status.indlab_slide25_note = indlab_note

    if settings.ocr_enabled and not any_engine_ready(status, require_inference=run_inference):
        if paddle.init_ok and paddle.inference_ok is False:
            status.errors.append(
                "OCR_ENABLED=true but PaddleOCR inference failed "
                f"({paddle.error_code or 'paddleocr_inference_failed'})."
            )
        else:
            status.errors.append("OCR_ENABLED=true but no OCR engine is ready.")

    if settings.ocr_enabled:
        status.ready = any_engine_ready(status, require_inference=run_inference)
    else:
        status.ready = True

    status.recommended_action = build_recommended_action(
        status,
        require_inference=run_inference,
    )
    return status


def format_status_text(status: OcrRuntimeStatus) -> str:
    env_flags = get_paddle_env_flags()
    lines: list[str] = [
        "=== OCR Runtime Status ===",
        "",
        "--- Config ---",
        f"OCR_ENABLED: {status.ocr_enabled}",
        f"OCR_ENGINE: {status.configured_engine}",
        f"OCR_FALLBACK_ENGINE: {status.fallback_engine}",
        f"OCR_DPI: {settings.ocr_dpi}",
        f"OCR_CACHE_ENABLED: {status.cache_enabled}",
        f"OCR cache dir: {status.cache_dir} (writable={status.cache_dir_writable})",
        "",
        "--- Paddle env flags ---",
    ]
    for key, value in env_flags.items():
        lines.append(f"{key}: {value if value is not None else '(unset)'}")
    lines.extend(
        [
            "",
            "--- Python packages ---",
            f"Pillow: {'OK' if status.pillow_available else 'MISSING'}",
            f"PyMuPDF: {'OK' if status.pymupdf_available else 'MISSING'}",
            f"paddleocr: {'OK' if status.paddleocr.package_installed else 'MISSING'}",
            f"pytesseract: {'OK' if status.tesseract.package_installed else 'MISSING'}",
            f"easyocr: {'OK' if status.easyocr.package_installed else 'MISSING'}",
            f"surya: {'OK' if status.surya.package_installed else 'MISSING'}",
            "",
            "--- PaddleOCR ---",
            f"package: {'installed' if status.paddleocr.package_installed else 'missing'}",
            f"version: {status.paddleocr.version or '-'}",
            f"init_ok: {status.paddleocr.init_ok}",
            f"model_ready: {status.paddleocr.model_ready}",
        ]
    )
    if status.paddleocr.inference_ok is not None:
        lines.append(f"inference_ok: {status.paddleocr.inference_ok}")
    if status.paddleocr.test_image_ok is not None:
        lines.append(f"test_image_ok: {status.paddleocr.test_image_ok}")
    if status.paddleocr.test_image_chars is not None:
        lines.append(f"test_image_chars: {status.paddleocr.test_image_chars}")
    if status.paddleocr.failure_stage:
        lines.append(f"failure_stage: {status.paddleocr.failure_stage}")
    if status.paddleocr.error_code:
        lines.append(f"error_code: {status.paddleocr.error_code}")
    if status.paddleocr.error:
        lines.append(f"error: {status.paddleocr.error}")
    if status.paddleocr.recommended_action:
        lines.append(f"recommended_action: {status.paddleocr.recommended_action}")
    for warning in status.paddleocr.warnings:
        lines.append(f"warning: {warning}")

    lines.extend(
        [
            "",
            "--- Tesseract ---",
            f"package: {'installed' if status.tesseract.package_installed else 'missing'}",
            f"binary: {status.tesseract.binary_available}",
            f"init_ok: {status.tesseract.init_ok}",
        ]
    )
    if status.tesseract.inference_ok is not None:
        lines.append(f"inference_ok: {status.tesseract.inference_ok}")
    if status.tesseract.error:
        lines.append(f"error: {status.tesseract.error}")
    for warning in status.tesseract.warnings:
        lines.append(f"warning: {warning}")

    lines.extend(
        [
            "",
            "--- EasyOCR ---",
            f"package: {'installed' if status.easyocr.package_installed else 'missing'}",
            f"init_ok: {status.easyocr.init_ok}",
            f"model_ready: {status.easyocr.model_ready}",
        ]
    )
    if status.easyocr.error:
        lines.append(f"error: {status.easyocr.error}")
    if status.easyocr.error_code:
        lines.append(f"error_code: {status.easyocr.error_code}")
    for warning in status.easyocr.warnings:
        lines.append(f"warning: {warning}")

    lines.extend(
        [
            "",
            "--- Surya (experimental) ---",
            f"package: {'installed' if status.surya.package_installed else 'missing'}",
            f"init_ok: {status.surya.init_ok}",
        ]
    )
    if status.surya.error:
        lines.append(f"error: {status.surya.error}")
    for warning in status.surya.warnings:
        lines.append(f"warning: {warning}")

    if status.test_image_ok is not None:
        lines.extend(
            [
                "",
                "--- Test image OCR (router) ---",
                f"ok: {status.test_image_ok}",
                f"chars: {status.test_image_chars or 0}",
            ]
        )

    if status.indlab_slide25_note:
        lines.extend(
            [
                "",
                "--- Indlab slide 25 ---",
                f"ready: {status.indlab_slide25_ready}",
                f"note: {status.indlab_slide25_note}",
            ]
        )

    lines.extend(
        [
            "",
            "--- Summary ---",
            f"ready: {status.ready}",
            f"recommended: {status.recommended_action}",
        ]
    )
    for warning in status.warnings:
        lines.append(f"warning: {warning}")
    for error in status.errors:
        lines.append(f"error: {error}")

    return "\n".join(lines)
