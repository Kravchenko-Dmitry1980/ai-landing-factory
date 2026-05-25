"""Detect whether extracted text is a pre-structured project landing document."""

from __future__ import annotations

import re

from app.schemas.fidelity import DetectionResult

SECTION_MARKERS: list[tuple[str, list[str]]] = [
    ("essence", ["суть проекта", "описание проекта"]),
    ("tasks", ["задачи проекта", "задачи"]),
    ("purpose", ["для чего", "цель проекта", "цели проекта"]),
    ("inputs", ["вводные данные", "исходные данные"]),
    ("outputs", ["выходные данные", "результирующие данные"]),
    ("results", ["результаты проекта", "результаты"]),
    ("outlook", ["перспектива развития", "roadmap", "дальнейшее развитие"]),
    ("tech_stack", [
        "используемый технологический стек",
        "технологический стек",
        "стек",
    ]),
    ("team", ["команда проекта", "участники команды проекта"]),
]

METADATA_MARKERS: list[tuple[str, str]] = [
    ("client", r"заказчик\s*:"),
    ("timeline", r"период\s+реализации\s*:"),
    ("lead", r"тимлид\s*:"),
]

CONFIDENCE_THRESHOLD = 0.65


class LandingDocumentDetector:
    """Heuristic detector for Russian structured project landing documents."""

    def detect(self, text: str) -> DetectionResult:
        if not text or not text.strip():
            return DetectionResult(
                is_structured_landing=False,
                confidence=0.0,
                reason="empty text",
            )

        normalized = _normalize(text)
        detected: list[str] = []
        missing: list[str] = []

        for key, variants in SECTION_MARKERS:
            if _has_section(normalized, variants):
                detected.append(key)
            else:
                missing.append(key)

        meta_found = sum(
            1 for _, pattern in METADATA_MARKERS if re.search(pattern, normalized)
        )

        section_score = len(detected) / max(len(SECTION_MARKERS), 1)
        meta_score = meta_found / max(len(METADATA_MARKERS), 1)
        confidence = round(section_score * 0.75 + meta_score * 0.25, 3)

        is_structured = confidence >= CONFIDENCE_THRESHOLD and len(detected) >= 5

        reason_parts: list[str] = []
        if is_structured:
            reason_parts.append(
                f"detected {len(detected)}/{len(SECTION_MARKERS)} sections"
            )
            if meta_found:
                reason_parts.append(f"metadata {meta_found}/{len(METADATA_MARKERS)}")
        else:
            reason_parts.append(
                f"insufficient structure ({len(detected)} sections, conf={confidence})"
            )

        return DetectionResult(
            is_structured_landing=is_structured,
            confidence=confidence,
            detected_sections=detected,
            missing_sections=missing if is_structured else missing,
            reason="; ".join(reason_parts),
        )


def _normalize(text: str) -> str:
    text = text.replace("\u00a0", " ").replace("\r\n", "\n")
    return text.lower()


def _has_section(normalized: str, variants: list[str]) -> bool:
    for variant in variants:
        pattern = rf"(?:^|\n)\s*#{{0,3}}\s*{re.escape(variant)}\s*(?:\n|$)"
        if re.search(pattern, normalized, re.IGNORECASE):
            return True
    return False
