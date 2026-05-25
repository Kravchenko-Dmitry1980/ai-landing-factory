"""Detect source material type: ready landing doc vs project presentation."""

from __future__ import annotations

import re

from app.schemas.fidelity import SourceTypeResult
from app.services.contract_fidelity.landing_document_detector import (
    CONFIDENCE_THRESHOLD,
    LandingDocumentDetector,
)

PRESENTATION_MARKERS: list[tuple[str, list[str]]] = [
    ("goal", ["цель проекта"]),
    ("stages", ["этапы проекта"]),
    ("data_prep", ["подготовка данных"]),
    ("results", ["итоги проекта"]),
    ("team", ["команда управления", "команда проекта"]),
    ("demo", ["демо-панель", "демо панель"]),
    ("pipeline", [r"шаг\s*1", r"шаг\s*2"]),
    ("sources", ["первоисточник", "ссылки на"]),
]

PRESENTATION_CONFIDENCE_THRESHOLD = 0.6

SLIDE_HEADER_RE = re.compile(r"(?:^|\n)\s*Slide\s+\d+\s*:", re.IGNORECASE)
UPPERCASE_HEADER_RE = re.compile(
    r"(?:^|\n)\s*[А-ЯЁA-Z][А-ЯЁA-Z\s\-]{3,40}(?:\n|$)"
)


class SourceTypeDetector:
    """Classify extracted source text into processing modes."""

    def __init__(self) -> None:
        self._landing_detector = LandingDocumentDetector()

    def detect(
        self,
        text: str,
        *,
        file_type: str | None = None,
    ) -> SourceTypeResult:
        if not text or not text.strip():
            return SourceTypeResult(
                source_type="unknown",
                confidence=0.0,
                reason="empty text",
            )

        landing = self._landing_detector.detect(text)
        if landing.is_structured_landing and landing.confidence >= CONFIDENCE_THRESHOLD:
            return SourceTypeResult(
                source_type="ready_landing_doc",
                confidence=landing.confidence,
                signals=["structured_sections"],
                reason=landing.reason,
            )

        normalized = _normalize(text)
        signals: list[str] = []
        marker_hits = 0

        for key, variants in PRESENTATION_MARKERS:
            if _has_marker(normalized, variants):
                marker_hits += 1
                signals.append(key)

        slide_count = len(SLIDE_HEADER_RE.findall(text))
        if slide_count >= 3:
            signals.append(f"slides:{slide_count}")
        uppercase_headers = len(UPPERCASE_HEADER_RE.findall(text))
        if uppercase_headers >= 3:
            signals.append(f"uppercase_headers:{uppercase_headers}")

        marker_score = marker_hits / max(len(PRESENTATION_MARKERS), 1)
        slide_score = min(slide_count / 8.0, 1.0) if slide_count else 0.0
        header_score = min(uppercase_headers / 6.0, 1.0) if uppercase_headers else 0.0

        confidence = round(
            marker_score * 0.55 + slide_score * 0.25 + header_score * 0.20,
            3,
        )
        if file_type == "pptx":
            confidence = min(round(confidence + 0.12, 3), 1.0)
            signals.append("file_type:pptx")

        if confidence >= PRESENTATION_CONFIDENCE_THRESHOLD and marker_hits >= 3:
            return SourceTypeResult(
                source_type="project_presentation",
                confidence=confidence,
                signals=signals,
                reason=(
                    f"presentation markers {marker_hits}/{len(PRESENTATION_MARKERS)}, "
                    f"slides={slide_count}, conf={confidence}"
                ),
            )

        if marker_hits >= 1 or slide_count >= 2:
            return SourceTypeResult(
                source_type="raw_materials",
                confidence=round(confidence * 0.7, 3),
                signals=signals,
                reason=f"partial presentation signals, conf={confidence}",
            )

        return SourceTypeResult(
            source_type="unknown",
            confidence=confidence,
            signals=signals,
            reason="no strong landing or presentation signals",
        )


def _normalize(text: str) -> str:
    text = text.replace("\u00a0", " ").replace("\u000b", "\n").replace("\r\n", "\n")
    return text.lower()


def _has_marker(normalized: str, variants: list[str]) -> bool:
    for variant in variants:
        if variant.startswith(r"шаг") or "\\" in variant:
            if re.search(variant, normalized, re.IGNORECASE):
                return True
        elif variant in normalized:
            return True
    return False
