"""Multi-OCR engine selection (auto mode)."""

from __future__ import annotations

import logging

from app.config import settings
from app.services.ocr.engine_registry import create_engine, parse_engine_list
from app.services.ocr.engines.base import OcrEngine

logger = logging.getLogger(__name__)


def get_engine_priority() -> list[str]:
    raw = settings.ocr_engine_priority or "tesseract,easyocr,paddleocr"
    return parse_engine_list(raw)


def select_engine_by_name(name: str) -> OcrEngine | None:
    engine = create_engine(name)
    if engine is None:
        return None
    if engine.is_available():
        return engine
    return None


def select_auto_engine(*, require_text: bool = False) -> OcrEngine | None:
    """Pick first working engine from OCR_ENGINE_PRIORITY."""
    for name in get_engine_priority():
        engine = create_engine(name)
        if engine is None:
            continue
        if not engine.is_available():
            logger.debug("Auto OCR skip %s: not available", name)
            continue
        if require_text:
            from app.services.ocr.ocr_env import generate_test_image_bytes

            sample = generate_test_image_bytes()
            if sample is None:
                return engine
            result = engine.extract_text(sample)
            if result.text.strip() and not _has_hard_failure(result.warnings):
                return engine
            logger.debug("Auto OCR skip %s: empty or failed smoke", name)
            continue
        return engine
    return None


def _has_hard_failure(warnings: list[str]) -> bool:
    for warning in warnings:
        low = warning.lower()
        if "failed" in low or "not available" in low or "not installed" in low:
            return True
    return False


def select_configured_engine() -> OcrEngine | None:
    primary = settings.ocr_engine.lower().strip()
    if primary == "auto":
        return select_auto_engine()

    engine = select_engine_by_name(primary)
    if engine is not None:
        return engine

    fallback = settings.ocr_fallback_engine.lower().strip()
    if fallback and fallback != primary:
        return select_engine_by_name(fallback)
    return None
