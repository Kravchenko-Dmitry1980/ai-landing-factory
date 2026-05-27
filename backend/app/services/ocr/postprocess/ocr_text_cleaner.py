"""OCR text post-processing."""

from __future__ import annotations

import re

from app.services.ocr.postprocess.ocr_team_text_normalizer import (
    detect_team_ocr_section,
    normalize_ocr_team_text,
)

MULTISPACE_RE = re.compile(r"[ \t]{2,}")
BULLET_RE = re.compile(r"^\s*[•●▪◦·]\s*", re.MULTILINE)


def clean_ocr_text(text: str) -> str:
    """Normalize OCR output without hallucinating names."""
    if not text:
        return ""
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = BULLET_RE.sub("- ", cleaned)
    cleaned = MULTISPACE_RE.sub(" ", cleaned)
    lines = [ln.strip() for ln in cleaned.splitlines()]
    cleaned = "\n".join(ln for ln in lines if ln).strip()
    if detect_team_ocr_section(cleaned):
        return normalize_ocr_team_text(cleaned)
    return cleaned


def merge_ocr_blocks(blocks: list[str]) -> str:
    """Merge OCR blocks from multiple images/pages."""
    parts = [clean_ocr_text(b) for b in blocks if b and b.strip()]
    merged = "\n\n".join(parts).strip()
    if detect_team_ocr_section(merged):
        return normalize_ocr_team_text(merged)
    return merged
