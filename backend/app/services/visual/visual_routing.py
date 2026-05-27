"""Deterministic routing decisions for classified visual sources."""

from __future__ import annotations

from app.config import settings
from app.schemas.visual_evidence import (
    VisualClassification,
    VisualContentType,
    VisualRouteAction,
    VisualSourceItem,
)
from app.services.evidence.people_extractor import extract_people_from_text
from app.services.visual.visual_contracts import (
    CHART_LIKE_MARKERS,
    DIAGRAM_HEAVY_MARKERS,
    LOW_TEXT_THRESHOLD,
    VLM_HEAVY_TYPES,
)


def _is_vlm_action(action: VisualRouteAction) -> bool:
    return action in (
        VisualRouteAction.run_ocr_and_mark_vlm_candidate,
        VisualRouteAction.mark_vlm_candidate_only,
    )


def _chart_like(blob: str) -> bool:
    low = blob.lower()
    return any(m in low for m in CHART_LIKE_MARKERS) or "%" in blob


def _diagram_heavy(blob: str, image_count: int, text_chars: int) -> bool:
    low = blob.lower()
    if any(m in low for m in DIAGRAM_HEAVY_MARKERS):
        return True
    return image_count > 0 and text_chars < LOW_TEXT_THRESHOLD


def decide_route(
    content_type: VisualContentType,
    item: VisualSourceItem,
    *,
    blob: str,
) -> tuple[VisualRouteAction, str, list[str]]:
    """Return route_action, reason, warnings for a classified item."""
    warnings: list[str] = []
    text_chars = item.text_chars
    image_count = item.image_count
    has_text = item.has_text_layer and text_chars >= LOW_TEXT_THRESHOLD
    has_images = item.has_images and image_count > 0
    ocr_enabled = settings.ocr_enabled

    if content_type == VisualContentType.team_slide:
        people = extract_people_from_text(blob, in_team_section=True)
        if people and text_chars >= LOW_TEXT_THRESHOLD:
            return VisualRouteAction.use_text_layer, "team markers with extractable names", warnings
        if text_chars < LOW_TEXT_THRESHOLD and has_images:
            return (
                VisualRouteAction.run_ocr_and_mark_vlm_candidate,
                "team markers/image-only",
                warnings,
            )
        if has_text:
            return VisualRouteAction.use_text_layer, "team markers with text layer", warnings
        if has_images and ocr_enabled:
            return VisualRouteAction.run_ocr, "team markers need OCR", warnings
        return VisualRouteAction.skip, "team slide without actionable content", warnings

    if content_type == VisualContentType.tech_stack_slide:
        if has_text:
            if _diagram_heavy(blob, image_count, text_chars):
                return (
                    VisualRouteAction.mark_vlm_candidate_only,
                    "tech stack with diagram-heavy layout",
                    warnings,
                )
            return VisualRouteAction.use_text_layer, "tech stack text available", warnings
        if has_images and ocr_enabled:
            action = VisualRouteAction.run_ocr_and_mark_vlm_candidate
            if _diagram_heavy(blob, image_count, text_chars):
                return action, "tech stack image-only diagram", warnings
            return VisualRouteAction.run_ocr, "tech stack image-only", warnings
        if has_images:
            return VisualRouteAction.mark_vlm_candidate_only, "tech stack visual", warnings
        return VisualRouteAction.skip, "tech stack without content", warnings

    if content_type == VisualContentType.architecture_diagram:
        if has_images:
            if ocr_enabled and text_chars < LOW_TEXT_THRESHOLD:
                return (
                    VisualRouteAction.run_ocr_and_mark_vlm_candidate,
                    "architecture diagram image-heavy",
                    warnings,
                )
            return VisualRouteAction.mark_vlm_candidate_only, "architecture visual", warnings
        if has_text:
            return (
                VisualRouteAction.mark_vlm_candidate_only,
                "architecture text (VLM candidate for layout)",
                warnings,
            )
        return VisualRouteAction.skip, "architecture without visual/text", warnings

    if content_type == VisualContentType.goals_slide:
        if has_text:
            return VisualRouteAction.use_text_layer, "goals text available", warnings
        if has_images and ocr_enabled:
            return VisualRouteAction.run_ocr, "goals image-only", warnings
        if has_images:
            return VisualRouteAction.mark_vlm_candidate_only, "goals visual", warnings
        return VisualRouteAction.skip, "goals without content", warnings

    if content_type == VisualContentType.metrics_slide:
        if has_text:
            if _chart_like(blob) and has_images:
                return (
                    VisualRouteAction.mark_vlm_candidate_only,
                    "metrics chart-like visual",
                    warnings,
                )
            return VisualRouteAction.use_text_layer, "metrics text available", warnings
        if has_images and ocr_enabled:
            action = VisualRouteAction.run_ocr_and_mark_vlm_candidate
            if _chart_like(blob):
                return action, "metrics chart image-only", warnings
            return VisualRouteAction.run_ocr, "metrics image-only", warnings
        if has_images:
            return VisualRouteAction.mark_vlm_candidate_only, "metrics visual", warnings
        return VisualRouteAction.skip, "metrics without content", warnings

    if content_type == VisualContentType.roadmap_slide:
        if has_text:
            return VisualRouteAction.use_text_layer, "roadmap text available", warnings
        if has_images and ocr_enabled:
            return VisualRouteAction.run_ocr, "roadmap image-only", warnings
        if has_images:
            return VisualRouteAction.mark_vlm_candidate_only, "roadmap visual", warnings
        return VisualRouteAction.skip, "roadmap without content", warnings

    if content_type == VisualContentType.table_or_matrix:
        if has_images:
            if ocr_enabled and text_chars < LOW_TEXT_THRESHOLD:
                return (
                    VisualRouteAction.run_ocr_and_mark_vlm_candidate,
                    "table/matrix image-heavy",
                    warnings,
                )
            return VisualRouteAction.mark_vlm_candidate_only, "table/matrix visual", warnings
        if has_text:
            return VisualRouteAction.use_text_layer, "table/matrix text", warnings
        return VisualRouteAction.skip, "table/matrix empty", warnings

    if content_type == VisualContentType.ui_screenshot:
        if has_images:
            if ocr_enabled and text_chars < LOW_TEXT_THRESHOLD:
                return (
                    VisualRouteAction.run_ocr_and_mark_vlm_candidate,
                    "ui screenshot image-only",
                    warnings,
                )
            return VisualRouteAction.mark_vlm_candidate_only, "ui screenshot", warnings
        if has_text:
            return VisualRouteAction.use_text_layer, "ui description in text", warnings
        return VisualRouteAction.skip, "ui without content", warnings

    if content_type == VisualContentType.generic_image:
        if not has_text and not has_images:
            return VisualRouteAction.skip, "decorative/empty", warnings
        if has_images and ocr_enabled and text_chars < LOW_TEXT_THRESHOLD:
            return VisualRouteAction.run_ocr, "generic image low text", warnings
        if has_images and text_chars < LOW_TEXT_THRESHOLD:
            return VisualRouteAction.mark_vlm_candidate_only, "generic visual candidate", warnings
        if has_text:
            return VisualRouteAction.use_text_layer, "generic with text", warnings
        return VisualRouteAction.skip, "generic no action", warnings

    # unknown
    if not has_text and not has_images:
        return VisualRouteAction.skip, "empty slide/page", warnings
    if has_images and ocr_enabled and text_chars < LOW_TEXT_THRESHOLD:
        if image_count > 0:
            return (
                VisualRouteAction.run_ocr_and_mark_vlm_candidate,
                "unknown image-only visual candidate",
                warnings,
            )
        return VisualRouteAction.run_ocr, "unknown image-only", warnings
    if has_images and text_chars < LOW_TEXT_THRESHOLD:
        return VisualRouteAction.mark_vlm_candidate_only, "unknown visual candidate", warnings
    if has_text:
        return VisualRouteAction.use_text_layer, "unknown with text", warnings
    return VisualRouteAction.skip, "unknown no action", warnings


def apply_route_to_classification(
    classification: VisualClassification,
    blob: str,
) -> VisualClassification:
    """Recompute route from content type + item features."""
    action, reason, warnings = decide_route(
        classification.content_type,
        classification.item,
        blob=blob,
    )
    vlm = _is_vlm_action(action) or classification.content_type in VLM_HEAVY_TYPES
    if action == VisualRouteAction.mark_vlm_candidate_only:
        vlm = True
    return classification.model_copy(
        update={
            "route_action": action,
            "reason": reason,
            "warnings": list(dict.fromkeys(classification.warnings + warnings)),
            "vlm_candidate": vlm,
        }
    )
