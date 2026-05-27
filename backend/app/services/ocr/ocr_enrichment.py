"""Enrich ExtractionResult with OCR-derived evidence sources."""

from __future__ import annotations

import logging

from app.schemas.extraction import ExtractionResult, FileExtraction
from app.schemas.visual_evidence import VisualClassification, VisualEvidenceReport
from app.services.ocr.ocr_decision import detect_missing_fields
from app.services.ocr.ocr_router import run_ocr_for_source

logger = logging.getLogger(__name__)


class OcrEnrichmentService:
    """Append OCR text as virtual evidence files before contract assembly."""

    def enrich(
        self,
        extraction: ExtractionResult,
        *,
        visual_report: VisualEvidenceReport | None = None,
    ) -> tuple[ExtractionResult, list[str]]:
        missing_fields = detect_missing_fields(extraction.files)
        warnings: list[str] = []
        ocr_files: list[FileExtraction] = []
        visual_by_source = _index_visual_classifications(visual_report)

        for source in extraction.files:
            if source.metadata.get("is_ocr_derivative"):
                continue
            result = run_ocr_for_source(source, missing_fields=missing_fields)
            warnings.extend(result.warnings)
            if not result.items:
                continue

            source_visual = visual_by_source.get(source.filename, {})

            for item in result.items:
                if not item.text.strip():
                    continue
                slide_label = item.page_or_slide or 1
                block = f"Slide {slide_label}:\n{item.text}"
                if item.source_type == "pdf_page":
                    block = f"Page {slide_label}:\n{item.text}"

                visual_meta = _visual_metadata_for_slide(
                    source_visual,
                    item.page_or_slide,
                )

                ocr_files.append(
                    FileExtraction(
                        filename=item.filename,
                        file_type="ocr",
                        extracted_text=block,
                        metadata={
                            "is_ocr_derivative": True,
                            "ocr_engine": item.engine,
                            "ocr_confidence": item.confidence,
                            "ocr_reason": item.reason,
                            "source_filename": source.filename,
                            "source_type": "ocr",
                            "source_role": "supporting_visual_evidence",
                            "page_or_slide": item.page_or_slide,
                            "image_index": item.image_index,
                            "parent_source_path": source.metadata.get("source_path"),
                            **visual_meta,
                        },
                        warnings=list(item.warnings),
                    )
                )

        if not ocr_files:
            return extraction, list(dict.fromkeys(warnings))

        merged_files = list(extraction.files) + ocr_files
        logger.info(
            "OCR enrichment added %d derivative sources for project %s",
            len(ocr_files),
            extraction.project_id,
        )
        return extraction.model_copy(update={"files": merged_files}), list(dict.fromkeys(warnings))


def _index_visual_classifications(
    report: VisualEvidenceReport | None,
) -> dict[str, dict[int, VisualClassification]]:
    indexed: dict[str, dict[int, VisualClassification]] = {}
    if not report:
        return indexed
    for cls in report.classifications:
        fname = cls.item.filename
        slide = cls.item.page_or_slide
        if slide is None:
            continue
        indexed.setdefault(fname, {})[slide] = cls
    return indexed


def _visual_metadata_for_slide(
    source_visual: dict[int, VisualClassification],
    page_or_slide: int | None,
) -> dict[str, object]:
    if page_or_slide is None:
        return {}
    cls = source_visual.get(page_or_slide)
    if not cls:
        return {}
    return {
        "visual_content_type": cls.content_type.value,
        "visual_route_action": cls.route_action.value,
        "visual_confidence": cls.confidence,
        "vlm_candidate": cls.vlm_candidate,
        "visual_markers": list(cls.markers[:8]),
    }
