"""VLM candidate selection, adapter routing, and extraction enrichment."""

from __future__ import annotations

import logging
from pathlib import Path

from app.config import settings
from app.schemas.extraction import ExtractionResult, FileExtraction
from app.schemas.visual_evidence import VisualClassification, VisualEvidenceReport
from app.schemas.vlm import (
    VlmCandidateSelection,
    VlmExtractionReport,
    VlmProvider,
    VlmTaskType,
)
from app.services.vlm.vlm_adapter_base import VlmAdapter
from app.services.vlm.vlm_contracts import (
    CONTENT_TYPE_TO_TASK,
    TASK_TARGET_FIELDS,
    VLM_ROUTE_ACTIONS,
    VlmExtractionContext,
)
from app.services.vlm.vlm_evidence_builder import VlmEvidenceBuilder
from app.services.vlm.vlm_stub_adapter import StubVlmAdapter

logger = logging.getLogger(__name__)


def select_vlm_adapter() -> VlmAdapter | None:
    provider = (settings.vlm_provider or "stub").lower()
    if provider == VlmProvider.stub.value:
        adapter = StubVlmAdapter()
        return adapter if adapter.is_available() else None
    # Future providers: local_transformers, ollama, vllm, cloud
    logger.warning("VLM provider %s is not implemented yet", provider)
    return None


def map_content_type_to_task(content_type: str) -> VlmTaskType:
    from app.schemas.visual_evidence import VisualContentType

    try:
        ctype = VisualContentType(content_type)
    except ValueError:
        return VlmTaskType.general_visual_summary
    return CONTENT_TYPE_TO_TASK.get(ctype, VlmTaskType.general_visual_summary)


def select_vlm_candidates(
    visual_report: VisualEvidenceReport | None,
) -> tuple[list[VisualClassification], list[VlmCandidateSelection]]:
    """Select visual classifications eligible for VLM processing."""
    selections: list[VlmCandidateSelection] = []
    selected: list[VisualClassification] = []

    if not visual_report:
        return selected, selections

    allowed = settings.vlm_allowed_content_types_set
    min_conf = settings.vlm_min_visual_confidence

    for idx, cls in enumerate(visual_report.classifications):
        task = map_content_type_to_task(cls.content_type.value)
        sel = VlmCandidateSelection(
            classification_index=idx,
            source_filename=cls.item.filename,
            page_or_slide=cls.item.page_or_slide,
            visual_content_type=cls.content_type.value,
            route_action=cls.route_action.value,
            confidence=cls.confidence,
            task_type=task.value,
        )

        if cls.route_action not in VLM_ROUTE_ACTIONS:
            sel.skipped_reason = "route_not_vlm_candidate"
            selections.append(sel)
            continue
        if not cls.vlm_candidate:
            sel.skipped_reason = "vlm_candidate_flag_false"
            selections.append(sel)
            continue
        if cls.confidence < min_conf:
            sel.skipped_reason = f"confidence_below_{min_conf}"
            selections.append(sel)
            continue
        if cls.content_type.value not in allowed:
            sel.skipped_reason = "content_type_not_allowed"
            selections.append(sel)
            continue

        sel.selected = True
        selections.append(sel)
        selected.append(cls)

    cap = settings.vlm_max_slides
    if len(selected) > cap:
        overflow = selected[cap:]
        selected = selected[:cap]
        for cls in overflow:
            for sel in selections:
                if (
                    sel.source_filename == cls.item.filename
                    and sel.page_or_slide == cls.item.page_or_slide
                    and sel.selected
                ):
                    sel.selected = False
                    sel.skipped_reason = f"cap_exceeded_max_{cap}"
                    break

    return selected, selections


class VlmEnrichmentService:
    """Append VLM-derived virtual evidence files when enabled."""

    def enrich(
        self,
        extraction: ExtractionResult,
        *,
        visual_report: VisualEvidenceReport | None = None,
    ) -> tuple[ExtractionResult, VlmExtractionReport]:
        if not settings.vlm_enabled:
            return extraction, _disabled_report(visual_report)

        adapter = select_vlm_adapter()
        if adapter is None:
            return extraction, VlmExtractionReport(
                enabled=True,
                provider=settings.vlm_provider,
                warnings=[f"VLM provider unavailable: {settings.vlm_provider}"],
                errors=["adapter_unavailable"],
                skipped_count=_vlm_candidate_count(visual_report),
                candidates_count=_vlm_candidate_count(visual_report),
            )

        candidates, selections = select_vlm_candidates(visual_report)
        report = VlmExtractionReport(
            enabled=True,
            provider=adapter.provider,
            candidates_count=len(
                [s for s in selections if s.skipped_reason != "route_not_vlm_candidate"]
            ),
            skipped_count=len([s for s in selections if not s.selected]),
        )

        sources_by_name = {
            f.filename: f
            for f in extraction.files
            if not f.metadata.get("is_vlm_derivative")
        }
        ocr_by_source_slide = _index_ocr_previews(extraction.files)

        for cls in candidates:
            source = sources_by_name.get(cls.item.filename)
            if source is None:
                report.skipped_count += 1
                report.warnings.append(f"Source missing for VLM: {cls.item.filename}")
                continue

            task_type = map_content_type_to_task(cls.content_type.value)
            image_bytes = _load_image_bytes(source, cls.item.page_or_slide)
            context = VlmExtractionContext(
                filename=cls.item.filename,
                page_or_slide=cls.item.page_or_slide,
                image_index=cls.item.image_index,
                visual_content_type=cls.content_type.value,
                text_layer_preview=cls.item.raw_text_preview or cls.item.title_hint,
                ocr_text_preview=ocr_by_source_slide.get(
                    (cls.item.filename, cls.item.page_or_slide)
                ),
                target_fields=TASK_TARGET_FIELDS.get(task_type, []),
            )

            try:
                result = adapter.extract(image_bytes, task_type, context)
                report.extractions.append(result)
                report.processed_count += 1
                report.warnings.extend(result.warnings)
                report.errors.extend(result.errors)
            except Exception as exc:
                report.errors.append(f"{cls.item.filename}#{cls.item.page_or_slide}: {exc}")
                report.skipped_count += 1
                logger.warning("VLM extraction failed: %s", exc)

        vlm_files = VlmEvidenceBuilder.build_file_extractions(report)
        if vlm_files:
            extraction = extraction.model_copy(
                update={"files": list(extraction.files) + vlm_files}
            )
            logger.info(
                "VLM enrichment added %d virtual sources for project %s",
                len(vlm_files),
                extraction.project_id,
            )

        return extraction, report


def plan_vlm_candidates(
    visual_report: VisualEvidenceReport | None,
) -> tuple[list[VlmCandidateSelection], VlmExtractionReport]:
    """Dry-run candidate selection for debug scripts."""
    if not settings.vlm_enabled:
        return [], _disabled_report(visual_report)

    _, selections = select_vlm_candidates(visual_report)
    report = VlmExtractionReport(
        enabled=settings.vlm_enabled,
        provider=settings.vlm_provider,
        candidates_count=len(selections),
        skipped_count=len([s for s in selections if not s.selected]),
    )
    return selections, report


def run_stub_extractions(
    extraction: ExtractionResult,
    visual_report: VisualEvidenceReport | None,
    *,
    slide_filter: set[int] | None = None,
) -> VlmExtractionReport:
    """Run stub adapter on selected candidates (debug helper)."""
    prev_enabled = settings.vlm_enabled
    prev_provider = settings.vlm_provider
    try:
        settings.vlm_enabled = True
        settings.vlm_provider = "stub"
        candidates, _ = select_vlm_candidates(visual_report)
        if slide_filter:
            candidates = [
                c for c in candidates if c.item.page_or_slide in slide_filter
            ]

        adapter = StubVlmAdapter()
        ocr_by_source_slide = _index_ocr_previews(extraction.files)
        sources = {f.filename: f for f in extraction.files}

        report = VlmExtractionReport(enabled=True, provider="stub")
        for cls in candidates:
            source = sources.get(cls.item.filename)
            if not source:
                continue
            task_type = map_content_type_to_task(cls.content_type.value)
            context = VlmExtractionContext(
                filename=cls.item.filename,
                page_or_slide=cls.item.page_or_slide,
                visual_content_type=cls.content_type.value,
                text_layer_preview=cls.item.raw_text_preview or cls.item.title_hint,
                ocr_text_preview=ocr_by_source_slide.get(
                    (cls.item.filename, cls.item.page_or_slide)
                ),
                target_fields=TASK_TARGET_FIELDS.get(task_type, []),
            )
            image_bytes = _load_image_bytes(source, cls.item.page_or_slide)
            report.extractions.append(adapter.extract(image_bytes, task_type, context))
            report.processed_count += 1
        return report
    finally:
        settings.vlm_enabled = prev_enabled
        settings.vlm_provider = prev_provider


def _disabled_report(visual_report: VisualEvidenceReport | None) -> VlmExtractionReport:
    count = _vlm_candidate_count(visual_report)
    return VlmExtractionReport(
        enabled=False,
        provider=VlmProvider.disabled.value,
        candidates_count=count,
        skipped_count=count,
        warnings=["VLM disabled (VLM_ENABLED=false)"],
    )


def _vlm_candidate_count(visual_report: VisualEvidenceReport | None) -> int:
    if not visual_report:
        return 0
    return visual_report.vlm_candidates_count or sum(
        1 for c in visual_report.classifications if c.vlm_candidate
    )


def _index_ocr_previews(files: list[FileExtraction]) -> dict[tuple[str, int | None], str]:
    indexed: dict[tuple[str, int | None], str] = {}
    for f in files:
        if not f.metadata.get("is_ocr_derivative"):
            continue
        src = f.metadata.get("source_filename") or f.filename
        slide = f.metadata.get("page_or_slide")
        indexed[(src, slide)] = (f.extracted_text or "")[:2000]
    return indexed


def _load_image_bytes(source: FileExtraction, page_or_slide: int | None) -> bytes:
    path_str = source.metadata.get("source_path")
    if not path_str:
        return b""
    path = Path(path_str)
    if not path.exists():
        return b""

    if source.file_type == "pptx" and page_or_slide:
        from app.services.ocr.renderers.pptx_image_extractor import extract_pptx_images_by_slide

        for img in extract_pptx_images_by_slide(path):
            if img.slide_index == page_or_slide:
                return img.image_bytes
        return b""

    if source.file_type in ("png", "jpg", "jpeg", "webp", "image"):
        return path.read_bytes()

    return b""
