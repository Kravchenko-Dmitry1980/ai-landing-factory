"""Merge OCR blocks from multiple targets."""

from app.services.ocr.postprocess.ocr_text_cleaner import clean_ocr_text, merge_ocr_blocks
from app.services.ocr.postprocess.ocr_team_text_normalizer import (
    detect_team_ocr_section,
    normalize_ocr_team_text,
)

__all__ = [
    "clean_ocr_text",
    "merge_ocr_blocks",
    "detect_team_ocr_section",
    "normalize_ocr_team_text",
]
