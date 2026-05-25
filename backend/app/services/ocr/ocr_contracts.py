"""Internal OCR contracts and decision types."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class OcrDecisionAction(StrEnum):
    RUN = "run"
    SKIP = "skip"
    DISABLED = "disabled"


@dataclass
class OcrTarget:
    """Single OCR target (slide/page/image)."""

    source_type: str
    page_or_slide: int | None = None
    image_index: int | None = None
    reason: str = ""


@dataclass
class OcrDecision:
    action: OcrDecisionAction
    targets: list[OcrTarget] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    reason: str = ""


@dataclass
class OcrEngineResult:
    text: str = ""
    confidence: float | None = None
    warnings: list[str] = field(default_factory=list)
