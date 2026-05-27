"""Product mode helpers — simple vs advanced vs research."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.config import Settings

logger = logging.getLogger(__name__)

VALID_PRODUCT_MODES = frozenset({"simple", "advanced", "research"})

SIMPLE_IMAGE_ONLY_HINT = (
    "Некоторые слайды содержат текст как изображение. Система может не извлечь "
    "всю информацию. Для лучшего результата загрузите DOCX/TXT или отредактируйте "
    "блоки вручную."
)

SIMPLE_TEAM_REVIEW_HINT = (
    "Команда не найдена или требует проверки. Добавьте её вручную в редакторе."
)

SIMPLE_TEAM_OCR_REVIEW_HINT = (
    "Список команды требует проверки. Отредактируйте участников вручную при необходимости."
)

OCR_ENABLED_IN_SIMPLE_WARNING = (
    "OCR is enabled in simple mode. This is advanced configuration."
)

VLM_ENABLED_IN_SIMPLE_WARNING = (
    "VLM is enabled in simple mode. This is advanced configuration."
)

_TECHNICAL_TERMS = re.compile(
    r"(?i)\b("
    r"ocr|vlm|paddleocr|paddle|tesseract|easyocr|surya|"
    r"inference|mkldnn|onednn|gpu|cuda|ollama|vllm|lm\s*studio"
    r")\b"
)


def normalize_product_mode(value: str | None) -> str:
    raw = (value or "simple").strip().lower()
    if raw not in VALID_PRODUCT_MODES:
        return "simple"
    return raw


def collect_product_mode_warnings(settings: Settings) -> list[str]:
    """Non-fatal configuration warnings logged at startup."""
    warnings: list[str] = []
    mode = settings.normalized_product_mode
    if mode == "simple":
        if settings.ocr_enabled:
            warnings.append(OCR_ENABLED_IN_SIMPLE_WARNING)
        if settings.vlm_enabled:
            warnings.append(VLM_ENABLED_IN_SIMPLE_WARNING)
        if settings.advanced_visual_pipeline:
            warnings.append(
                "ADVANCED_VISUAL_PIPELINE is true in simple mode; "
                "pipeline stays disabled in simple product mode."
            )
    return warnings


def log_product_mode_warnings(settings: Settings) -> None:
    for message in collect_product_mode_warnings(settings):
        logger.warning("%s", message)


def sanitize_user_message(text: str, *, advanced: bool) -> str:
    """Map technical OCR/VLM messages to user-facing copy in simple mode."""
    if advanced or not text:
        return text
    lowered = text.lower()
    if "image-only" in lowered or "изображен" in lowered:
        if "ocr" in lowered or "текстов" in lowered:
            return SIMPLE_IMAGE_ONLY_HINT
    if "ocr" in lowered or "paddle" in lowered or "tesseract" in lowered:
        if "team" in lowered or "команд" in lowered:
            return SIMPLE_TEAM_OCR_REVIEW_HINT
        return SIMPLE_IMAGE_ONLY_HINT
    if "vlm" in lowered or "inference" in lowered:
        return SIMPLE_IMAGE_ONLY_HINT
    if _TECHNICAL_TERMS.search(text):
        return SIMPLE_IMAGE_ONLY_HINT
    return text


def sanitize_message_list(messages: list[str], *, advanced: bool) -> list[str]:
    if advanced:
        return messages
    out: list[str] = []
    seen: set[str] = set()
    for raw in messages:
        cleaned = sanitize_user_message(raw, advanced=False)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            out.append(cleaned)
    return out


def map_improvement_hint(hint: str, *, advanced: bool) -> str:
    if advanced:
        return hint
    if "ocr" in hint.lower() or "текстовую версию" in hint.lower():
        return SIMPLE_IMAGE_ONLY_HINT
    if "команд" in hint.lower() and "ocr" in hint.lower():
        return (
            "В презентации не найден извлекаемый текст команды. "
            "Добавьте DOCX/TXT со списком участников или отредактируйте блок команды вручную."
        )
    return hint
