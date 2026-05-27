"""Debug formatting helpers for visual source classifier."""

from __future__ import annotations

import json

from app.schemas.visual_evidence import VisualClassification, VisualEvidenceReport


def format_classification_table(
    classifications: list[VisualClassification],
    *,
    slide_filter: set[int] | None = None,
) -> str:
    rows: list[str] = []
    header = "slide | text_chars | images | content_type | confidence | route | reason | markers"
    rows.append(header)
    rows.append("-" * len(header))

    for cls in classifications:
        item = cls.item
        if slide_filter and item.page_or_slide not in slide_filter:
            continue
        slide = item.page_or_slide if item.page_or_slide is not None else "-"
        markers = ", ".join(cls.markers[:4]) if cls.markers else "-"
        rows.append(
            f"{slide} | {item.text_chars} | {item.image_count} | "
            f"{cls.content_type.value} | {cls.confidence:.2f} | "
            f"{cls.route_action.value} | {cls.reason} | {markers}"
        )
    return "\n".join(rows)


def format_report_json(report: VisualEvidenceReport) -> str:
    return json.dumps(report.model_dump(), ensure_ascii=False, indent=2)
