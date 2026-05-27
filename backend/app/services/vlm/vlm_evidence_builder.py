"""Convert VLM extractions into virtual FileExtraction evidence sources."""

from __future__ import annotations

from app.schemas.extraction import FileExtraction
from app.schemas.vlm import VlmExtractionReport, VlmFieldCandidate, VlmStructuredExtraction


class VlmEvidenceBuilder:
    """Build virtual evidence files from structured VLM output."""

    @staticmethod
    def build_file_extractions(report: VlmExtractionReport) -> list[FileExtraction]:
        files: list[FileExtraction] = []
        for extraction in report.extractions:
            text = VlmEvidenceBuilder.extraction_to_text(extraction)
            if not text.strip():
                continue
            slide = _slide_from_extraction(extraction)
            base_name = extraction.source_filename.rsplit(".", 1)[0]
            suffix = extraction.source_filename.rsplit(".", 1)[-1]
            virtual_name = f"{base_name}.{suffix}#vlm-{extraction.source_location}"

            block = text
            if slide is not None:
                block = f"Slide {slide}:\n{text}"

            files.append(
                FileExtraction(
                    filename=virtual_name,
                    file_type="vlm",
                    extracted_text=block,
                    metadata={
                        "is_vlm_derivative": True,
                        "provider": extraction.provider,
                        "model_name": extraction.model_name,
                        "visual_content_type": extraction.visual_content_type,
                        "task_type": extraction.task_type,
                        "confidence": extraction.confidence,
                        "source_filename": extraction.source_filename,
                        "source_type": "vlm",
                        "source_role": "supporting_visual_evidence",
                        "page_or_slide": slide,
                        "source_location": extraction.source_location,
                        "field_candidate_count": len(extraction.field_candidates),
                    },
                    warnings=list(extraction.warnings),
                    errors=list(extraction.errors),
                )
            )
        return files

    @staticmethod
    def extraction_to_text(extraction: VlmStructuredExtraction) -> str:
        lines: list[str] = []
        for candidate in extraction.field_candidates:
            lines.append(_candidate_line(candidate))
        if extraction.warnings:
            lines.append("VLM warnings: " + "; ".join(extraction.warnings[:3]))
        return "\n".join(lines)

    @staticmethod
    def summarize_report(report: VlmExtractionReport) -> list[dict[str, object]]:
        from app.schemas.vlm import VlmExtractionSummaryLine

        lines: list[VlmExtractionSummaryLine] = []
        for ext in report.extractions:
            slide = _slide_from_extraction(ext)
            lines.append(
                VlmExtractionSummaryLine(
                    source_filename=ext.source_filename,
                    page_or_slide=slide,
                    visual_content_type=ext.visual_content_type,
                    task_type=ext.task_type,
                    provider=ext.provider,
                    confidence=round(ext.confidence, 2),
                    field_count=len(ext.field_candidates),
                    warnings=list(ext.warnings[:3]),
                )
            )
        return [line.model_dump() for line in lines]


def _candidate_line(candidate: VlmFieldCandidate) -> str:
    value = candidate.value
    if isinstance(value, list):
        rendered = ", ".join(str(v) for v in value)
    elif isinstance(value, dict):
        rendered = "; ".join(f"{k}: {v}" for k, v in value.items())
    else:
        rendered = str(value)
    return f"VLM extracted {candidate.field_name}: {rendered}"


def _slide_from_extraction(extraction: VlmStructuredExtraction) -> int | None:
    for candidate in extraction.field_candidates:
        if candidate.source_slide is not None:
            return candidate.source_slide
    loc = extraction.source_location or ""
    if loc.startswith("slide-"):
        try:
            return int(loc.split("-", 1)[1])
        except ValueError:
            return None
    return None
