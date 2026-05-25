"""Merge OCR blocks from multiple targets."""

from app.services.ocr.postprocess.ocr_text_cleaner import clean_ocr_text, merge_ocr_blocks

__all__ = ["clean_ocr_text", "merge_ocr_blocks"]
