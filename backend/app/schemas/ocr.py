"""OCR layer schemas (Stage H.8)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class OcrSourceType(StrEnum):
    PPTX_SLIDE_IMAGE = "pptx_slide_image"
    PDF_PAGE = "pdf_page"
    EMBEDDED_IMAGE = "embedded_image"
    STANDALONE_IMAGE = "standalone_image"


class OcrItem(BaseModel):
    source_id: str
    filename: str
    source_type: str
    page_or_slide: int | None = None
    image_index: int | None = None
    text: str = ""
    confidence: float | None = None
    engine: str = ""
    reason: str = ""
    warnings: list[str] = Field(default_factory=list)
    char_count: int = 0


class OcrExtractionResult(BaseModel):
    source_id: str
    filename: str
    items: list[OcrItem] = Field(default_factory=list)
    full_text: str = ""
    total_chars: int = 0
    engine: str = ""
    warnings: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
