"""Build visual evidence report and fidelity summaries."""

from __future__ import annotations

from app.schemas.visual_evidence import (
    VisualClassification,
    VisualEvidenceReport,
    VisualEvidenceSummaryLine,
    VisualRouteAction,
)


class VisualEvidenceBuilder:
    """Aggregate classifier output for fidelity metadata and evidence API."""

    @staticmethod
    def summarize_report(report: VisualEvidenceReport) -> list[VisualEvidenceSummaryLine]:
        lines: list[VisualEvidenceSummaryLine] = []
        for cls in report.classifications:
            item = cls.item
            lines.append(
                VisualEvidenceSummaryLine(
                    source_filename=item.filename,
                    page_or_slide=item.page_or_slide,
                    content_type=cls.content_type.value,
                    route_action=cls.route_action.value,
                    confidence=round(cls.confidence, 2),
                    vlm_candidate=cls.vlm_candidate,
                    reason=cls.reason,
                    markers=list(cls.markers[:6]),
                )
            )
        return lines

    @staticmethod
    def format_summary_line(line: VisualEvidenceSummaryLine) -> str:
        loc = f"slide {line.page_or_slide}" if line.page_or_slide else "source"
        vlm = ", vlm_candidate=true" if line.vlm_candidate else ""
        return (
            f"{loc}: {line.content_type}, route={line.route_action}{vlm}"
            f" ({line.reason})"
        )

    @staticmethod
    def ocr_route_slides(classifications: list[VisualClassification]) -> set[int]:
        """Slides/pages where visual router suggests OCR (advisory; OCR layer may override)."""
        ocr_actions = {
            VisualRouteAction.run_ocr,
            VisualRouteAction.run_ocr_and_mark_vlm_candidate,
        }
        slides: set[int] = set()
        for cls in classifications:
            if cls.route_action in ocr_actions and cls.item.page_or_slide:
                slides.add(cls.item.page_or_slide)
        return slides

    @staticmethod
    def vlm_candidates(classifications: list[VisualClassification]) -> list[VisualClassification]:
        return [c for c in classifications if c.vlm_candidate]
