"""PaddleOCR engine (optional dependency) with 2.x / 3.x compatibility."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

from app.services.ocr.engines.base import OcrEngine
from app.services.ocr.ocr_contracts import OcrEngineResult

logger = logging.getLogger(__name__)

PADDLE_INFERENCE_ERROR_MARKERS = (
    "convertpirattribute2runtimeattribute",
    "onednn_instruction.cc",
    "paddle_static",
)


def classify_paddle_error(
    error: str,
    *,
    stage: str = "unknown",
) -> tuple[str, str, str]:
    """Classify PaddleOCR init/inference errors.

    Returns (error_code, failure_stage, recommended_action).
    """
    low = error.lower()

    if any(marker in low for marker in PADDLE_INFERENCE_ERROR_MARKERS):
        return (
            "paddleocr_pir_onednn_unimplemented",
            "inference",
            "Try disabling oneDNN/PIR flags, install Tesseract fallback, "
            "or pin PaddleOCR/PaddlePaddle versions.",
        )
    if "paddlepaddle is not installed" in low:
        return (
            "paddlepaddle_missing",
            "dependency",
            "pip install paddlepaddle",
        )
    if any(token in low for token in ("download", "model", "network", "huggingface", "model source")):
        return (
            "model_download_failed",
            "model_download",
            "Check internet/proxy and run warmup_ocr_models.py --engine paddleocr.",
        )
    if "unknown argument" in low or "unexpected keyword" in low:
        return (
            "incompatible_version",
            "init",
            "Pin compatible PaddleOCR/PaddlePaddle versions or use Tesseract fallback.",
        )
    if stage == "inference":
        return (
            "paddleocr_inference_runtime_error",
            "inference",
            "Try env flags (FLAGS_use_mkldnn=0, FLAGS_enable_pir_api=0), "
            "Tesseract fallback, or pin Paddle versions.",
        )
    return ("unknown_init_error", stage, "Run warmup_ocr_models.py --engine paddleocr.")


def _parse_paddle_result(raw_result: Any) -> tuple[str, float | None, list[str]]:
    """Parse PaddleOCR output across legacy and 3.x formats."""
    warnings: list[str] = []
    lines: list[str] = []
    confidences: list[float] = []

    if raw_result is None:
        return "", None, warnings

    if isinstance(raw_result, dict):
        texts, scores, dict_warnings = _parse_rec_texts_dict(raw_result)
        warnings.extend(dict_warnings)
        lines.extend(texts)
        confidences.extend(scores)
    elif isinstance(raw_result, list):
        for item in raw_result:
            if isinstance(item, dict):
                texts, scores, dict_warnings = _parse_rec_texts_dict(item)
                warnings.extend(dict_warnings)
                lines.extend(texts)
                confidences.extend(scores)
            elif isinstance(item, list):
                text, score, line_warnings = _parse_legacy_line_group(item)
                warnings.extend(line_warnings)
                if text:
                    lines.append(text)
                if score is not None:
                    confidences.append(score)
            else:
                warnings.append(f"Unexpected PaddleOCR list item type: {type(item).__name__}")
    else:
        warnings.append(f"Unexpected PaddleOCR result type: {type(raw_result).__name__}")

    if not lines and not warnings and raw_result:
        warnings.append("PaddleOCR returned unknown result structure.")

    text = "\n".join(lines)
    avg_conf = sum(confidences) / len(confidences) if confidences else None
    return text, avg_conf, warnings


def _parse_rec_texts_dict(data: dict[str, Any]) -> tuple[list[str], list[float], list[str]]:
    warnings: list[str] = []
    texts_raw = data.get("rec_texts")
    scores_raw = data.get("rec_scores")
    if texts_raw is None:
        return [], [], warnings

    texts = [str(t).strip() for t in texts_raw if str(t).strip()]
    scores: list[float] = []
    if scores_raw is not None:
        for score in scores_raw:
            try:
                scores.append(float(score))
            except (TypeError, ValueError):
                warnings.append(f"Invalid rec_score value: {score!r}")
    return texts, scores, warnings


def _parse_legacy_line_group(group: list[Any]) -> tuple[str, float | None, list[str]]:
    warnings: list[str] = []
    if _is_single_legacy_line(group):
        text, score, line_warnings = _parse_single_legacy_line(group)
        warnings.extend(line_warnings)
        return text, score, warnings

    lines: list[str] = []
    confidences: list[float] = []

    for line in group:
        if not isinstance(line, list) or len(line) < 2:
            continue
        text, score, line_warnings = _parse_single_legacy_line(line)
        warnings.extend(line_warnings)
        if text:
            lines.append(text)
        if score is not None:
            confidences.append(score)

    text = "\n".join(lines)
    avg_conf = sum(confidences) / len(confidences) if confidences else None
    return text, avg_conf, warnings


def _is_single_legacy_line(entry: list[Any]) -> bool:
    if len(entry) < 2:
        return False
    text_part = entry[1]
    return isinstance(text_part, (list, tuple, str))


def _parse_single_legacy_line(line: list[Any]) -> tuple[str, float | None, list[str]]:
    warnings: list[str] = []
    text_part = line[1]
    if isinstance(text_part, (list, tuple)) and text_part:
        text = str(text_part[0])
        score: float | None = None
        if len(text_part) > 1 and text_part[1] is not None:
            try:
                score = float(text_part[1])
            except (TypeError, ValueError):
                warnings.append(f"Invalid legacy score: {text_part[1]!r}")
        return text, score, warnings
    if isinstance(text_part, str):
        return text_part, None, warnings
    return "", None, warnings


class PaddleOcrEngine(OcrEngine):
    name = "paddleocr"

    def __init__(self) -> None:
        self._ocr = None
        self._available: bool | None = None
        self._init_error: str | None = None
        self._init_kwargs: dict[str, Any] | None = None
        self._init_failed = False

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            from paddleocr import PaddleOCR  # noqa: F401

            self._available = True
        except ImportError as exc:
            logger.debug("PaddleOCR not installed")
            self._init_error = f"paddleocr import failed: {exc}"
            self._available = False
        return self._available

    def _ensure_engine(self) -> bool:
        if self._ocr is not None:
            return True
        if self._init_failed:
            return False
        try:
            from app.services.ocr.ocr_env import apply_paddle_env_flags

            apply_paddle_env_flags()
            from paddleocr import PaddleOCR
        except Exception as exc:
            self._init_error = f"paddleocr import failed: {exc}"
            self._available = False
            self._init_failed = True
            return False

        init_attempts: list[dict[str, Any]] = [
            {"lang": "ru"},
            {"use_angle_cls": True, "lang": "ru"},
            {
                "lang": "ru",
                "use_doc_orientation_classify": False,
                "use_doc_unwarping": False,
                "use_textline_orientation": True,
            },
        ]

        errors: list[str] = []
        for kwargs in init_attempts:
            try:
                self._ocr = PaddleOCR(**kwargs)
                self._init_kwargs = kwargs
                self._init_error = None
                return True
            except Exception as exc:
                errors.append(f"{kwargs}: {type(exc).__name__}: {exc}")

        self._init_error = "PaddleOCR init failed: " + " | ".join(errors)
        self._ocr = None
        self._init_failed = True
        logger.warning(self._init_error)
        return False

    def extract_text(self, image: bytes | Path) -> OcrEngineResult:
        if not self._ensure_engine():
            if self._init_error:
                return OcrEngineResult(warnings=[self._init_error])
            return OcrEngineResult(
                warnings=["PaddleOCR not installed; install paddleocr for primary OCR."],
            )
        try:
            if isinstance(image, bytes):
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp.write(image)
                    path = tmp.name
            else:
                path = str(image)

            raw_result = self._run_ocr(path)
            text, avg_conf, parse_warnings = _parse_paddle_result(raw_result)
            return OcrEngineResult(
                text=text,
                confidence=avg_conf,
                warnings=parse_warnings,
            )
        except Exception as exc:
            logger.warning("PaddleOCR extraction failed: %s", exc)
            return OcrEngineResult(warnings=[f"PaddleOCR failed: {exc}"])

    def _run_ocr(self, path: str) -> Any:
        try:
            return self._ocr.ocr(path, cls=True)
        except TypeError:
            return self._ocr.ocr(path)
