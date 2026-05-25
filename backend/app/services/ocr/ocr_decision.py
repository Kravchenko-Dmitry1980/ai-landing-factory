"""Targeted OCR decision rules."""

from __future__ import annotations

from app.config import settings
from app.schemas.extraction import FileExtraction
from app.services.contract_fidelity.pptx_team_markers import (
    iter_pptx_slides,
    slide_title_has_team_marker,
    text_has_team_markers,
)
from app.services.evidence.people_extractor import extract_people_from_text
from app.services.ocr.ocr_contracts import OcrDecision, OcrDecisionAction, OcrTarget
from app.services.ocr.renderers.pptx_image_extractor import slide_image_counts

OCR_DISABLED_WARNING = (
    "OCR disabled. Image-only slides/pages may not be parsed."
)


def should_ocr_source(
    source: FileExtraction,
    *,
    missing_fields: list[str] | None = None,
    source_path: str | None = None,
) -> OcrDecision:
    """Decide whether OCR should run for a single uploaded source."""
    missing_fields = missing_fields or []
    team_missing = "team" in missing_fields

    if not settings.ocr_enabled:
        return OcrDecision(
            action=OcrDecisionAction.DISABLED,
            warnings=[OCR_DISABLED_WARNING],
            reason="ocr_disabled",
        )

    path = source_path or source.metadata.get("source_path")
    if not path:
        return OcrDecision(
            action=OcrDecisionAction.SKIP,
            reason="no_source_path",
        )

    file_type = source.file_type
    text = (source.extracted_text or "").strip()
    min_chars = settings.ocr_min_text_chars

    if file_type == "pptx":
        return _decide_pptx(source, text, team_missing, path)
    if file_type == "pdf":
        return _decide_pdf(source, text, team_missing, path)
    if file_type in ("docx", "doc"):
        return _decide_docx(source, text, team_missing, path)
    if file_type in ("png", "jpg", "jpeg", "webp", "image"):
        return OcrDecision(
            action=OcrDecisionAction.RUN,
            targets=[
                OcrTarget(
                    source_type="standalone_image",
                    reason="standalone_image_upload",
                )
            ],
            reason="standalone_image",
        )

    return OcrDecision(action=OcrDecisionAction.SKIP, reason="unsupported_type")


def _decide_pptx(
    source: FileExtraction,
    text: str,
    team_missing: bool,
    path: str,
) -> OcrDecision:
    from pathlib import Path

    min_chars = settings.ocr_min_text_chars
    image_counts = slide_image_counts(Path(path))
    if not image_counts:
        return OcrDecision(action=OcrDecisionAction.SKIP, reason="no_pptx_images")

    slides = iter_pptx_slides(text) if text else []
    slide_chars = {idx: len(body.strip()) for idx, body, _title in slides}
    people = extract_people_from_text(
        text,
        source_ref=source.filename,
        in_team_section=text_has_team_markers(text),
    )
    likely_team_image = _likely_team_image_slide(text, slides, image_counts)

    targets: list[OcrTarget] = []
    for slide_idx, image_count in sorted(image_counts.items()):
        if slide_idx > settings.ocr_max_slides:
            continue
        chars = slide_chars.get(slide_idx, 0)
        has_team_marker = any(
            slide_title_has_team_marker(title, body)
            for idx, body, title in slides
            if idx == slide_idx
        )
        low_text = chars < min_chars
        if image_count <= 0:
            continue
        if low_text and (team_missing or likely_team_image or has_team_marker or not people):
            targets.append(
                OcrTarget(
                    source_type="pptx_slide_image",
                    page_or_slide=slide_idx,
                    reason="low_text_with_images",
                )
            )

    if not targets and team_missing and likely_team_image:
        last_slide = max(image_counts)
        targets.append(
            OcrTarget(
                source_type="pptx_slide_image",
                page_or_slide=last_slide,
                reason="possible_image_only_team_slide",
            )
        )

    if not targets:
        return OcrDecision(action=OcrDecisionAction.SKIP, reason="pptx_no_ocr_targets")

    return OcrDecision(
        action=OcrDecisionAction.RUN,
        targets=targets[: settings.ocr_max_slides],
        reason="pptx_low_text_images",
    )


def _decide_pdf(
    source: FileExtraction,
    text: str,
    team_missing: bool,
    path: str,
) -> OcrDecision:
    min_chars = settings.ocr_min_text_chars
    total_chars = len(text)
    pages_count = int(source.metadata.get("pages_count") or 0)
    if pages_count <= 0 and text:
        pages_count = text.count("Page ") + text.count("Страница ")

    targets: list[OcrTarget] = []
    if total_chars < min_chars * max(1, pages_count // 2):
        limit = min(pages_count or settings.ocr_max_pages, settings.ocr_max_pages)
        for page_idx in range(1, limit + 1):
            targets.append(
                OcrTarget(
                    source_type="pdf_page",
                    page_or_slide=page_idx,
                    reason="low_document_text",
                )
            )
    elif team_missing and total_chars < min_chars:
        targets.append(
            OcrTarget(
                source_type="pdf_page",
                page_or_slide=1,
                reason="pdf_low_text_team_missing",
            )
        )

    if not targets:
        return OcrDecision(action=OcrDecisionAction.SKIP, reason="pdf_text_sufficient")

    return OcrDecision(
        action=OcrDecisionAction.RUN,
        targets=targets,
        reason="pdf_low_text",
    )


def _decide_docx(
    source: FileExtraction,
    text: str,
    team_missing: bool,
    path: str,
) -> OcrDecision:
    if not team_missing:
        return OcrDecision(action=OcrDecisionAction.SKIP, reason="docx_team_present")
    people = extract_people_from_text(text, source_ref=source.filename)
    if people:
        return OcrDecision(action=OcrDecisionAction.SKIP, reason="docx_team_in_text")
    # DOCX embedded image OCR is deferred unless images metadata present
    if source.metadata.get("has_images"):
        return OcrDecision(
            action=OcrDecisionAction.RUN,
            targets=[
                OcrTarget(
                    source_type="embedded_image",
                    reason="docx_team_missing_with_images",
                )
            ],
            reason="docx_embedded_images",
        )
    return OcrDecision(action=OcrDecisionAction.SKIP, reason="docx_no_embedded_ocr_path")


def _likely_team_image_slide(
    text: str,
    slides: list[tuple[int, str, str]],
    image_counts: dict[int, int],
) -> bool:
    if not image_counts:
        return False
    if text_has_team_markers(text):
        for idx, body, title in slides:
            if slide_title_has_team_marker(title, body) and len(body.strip()) < settings.ocr_min_text_chars:
                return True
        if not extract_people_from_text(text, in_team_section=True):
            return True
    last_slide = max(image_counts)
    if image_counts.get(last_slide, 0) > 0:
        body = next((b for i, b, _t in slides if i == last_slide), "")
        if len(body.strip()) < settings.ocr_min_text_chars:
            return True
    return False


def detect_missing_fields(extraction_files: list[FileExtraction]) -> list[str]:
    """Heuristic missing-field detection before evidence assembly."""
    missing: list[str] = []
    combined = "\n".join((f.extracted_text or "") for f in extraction_files)
    people = extract_people_from_text(
        combined,
        in_team_section=text_has_team_markers(combined),
    )
    if not people:
        missing.append("team")
    return missing
