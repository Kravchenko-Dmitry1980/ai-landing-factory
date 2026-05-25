"""OCR router — decision, extraction, engine, cache."""

from __future__ import annotations

import logging
from pathlib import Path

from app.config import settings
from app.schemas.extraction import FileExtraction
from app.schemas.ocr import OcrExtractionResult, OcrItem, OcrSourceType
from app.services.evidence.people_extractor import extract_people_from_text
from app.services.ocr.engines.paddleocr_engine import PaddleOcrEngine
from app.services.ocr.engines.tesseract_engine import TesseractOcrEngine
from app.services.ocr.ocr_cache import get_cached_item, store_cached_item
from app.services.ocr.ocr_contracts import OcrDecisionAction
from app.services.ocr.ocr_decision import should_ocr_source
from app.services.ocr.postprocess.ocr_text_cleaner import clean_ocr_text, merge_ocr_blocks
from app.services.ocr.renderers.image_loader import load_image_bytes
from app.services.ocr.renderers.pdf_page_renderer import render_pdf_page
from app.services.ocr.renderers.pptx_image_extractor import extract_pptx_images_by_slide

logger = logging.getLogger(__name__)

ENGINE_UNAVAILABLE_WARNING = "OCR engine unavailable."


def _select_engine():
    primary_name = settings.ocr_engine.lower()
    fallback_name = settings.ocr_fallback_engine.lower()
    engines = {
        "paddleocr": PaddleOcrEngine(),
        "tesseract": TesseractOcrEngine(),
    }
    primary = engines.get(primary_name, PaddleOcrEngine())
    fallback = engines.get(fallback_name, TesseractOcrEngine())
    if primary.is_available():
        return primary
    if fallback.is_available():
        return fallback
    return None


def run_ocr_for_source(
    source: FileExtraction,
    *,
    missing_fields: list[str] | None = None,
    source_path: str | Path | None = None,
) -> OcrExtractionResult:
    """Run targeted OCR for one uploaded source."""
    path_str = str(source_path or source.metadata.get("source_path") or "")
    decision = should_ocr_source(
        source,
        missing_fields=missing_fields,
        source_path=path_str or None,
    )

    if decision.action == OcrDecisionAction.DISABLED:
        return OcrExtractionResult(
            source_id=source.filename,
            filename=source.filename,
            warnings=list(decision.warnings),
            metrics={"decision": decision.reason},
        )

    if decision.action != OcrDecisionAction.RUN or not decision.targets:
        return OcrExtractionResult(
            source_id=source.filename,
            filename=source.filename,
            warnings=list(decision.warnings),
            metrics={"decision": decision.reason, "skipped": True},
        )

    engine = _select_engine()
    if engine is None:
        warnings = list(decision.warnings) + [ENGINE_UNAVAILABLE_WARNING]
        return OcrExtractionResult(
            source_id=source.filename,
            filename=source.filename,
            warnings=warnings,
            metrics={"decision": decision.reason, "engine_available": False},
        )

    path = Path(path_str) if path_str else None
    if path is None or not path.exists():
        return OcrExtractionResult(
            source_id=source.filename,
            filename=source.filename,
            warnings=["Source path missing for OCR."],
            metrics={"decision": "missing_path"},
        )

    file_bytes = path.read_bytes()
    items: list[OcrItem] = []
    warnings: list[str] = list(decision.warnings)

    for target in decision.targets:
        if target.source_type == OcrSourceType.PPTX_SLIDE_IMAGE:
            items.extend(
                _ocr_pptx_slide(
                    source,
                    path,
                    file_bytes,
                    target.page_or_slide or 1,
                    engine,
                    target.reason,
                )
            )
        elif target.source_type == OcrSourceType.PDF_PAGE:
            items.extend(
                _ocr_pdf_page(
                    source,
                    path,
                    file_bytes,
                    target.page_or_slide or 1,
                    engine,
                    target.reason,
                )
            )
        elif target.source_type in (OcrSourceType.STANDALONE_IMAGE, OcrSourceType.EMBEDDED_IMAGE):
            items.extend(_ocr_standalone(source, path, file_bytes, engine, target.reason))

    texts = [item.text for item in items if item.text.strip()]
    full_text = merge_ocr_blocks(texts)
    people = extract_people_from_text(full_text, source_ref=source.filename, in_team_section=True)
    if items and not people:
        warnings.append("OCR completed but no valid team candidates found.")
    if any(t.reason == "possible_image_only_team_slide" for t in decision.targets):
        warnings.append("Possible image-only team slide.")

    return OcrExtractionResult(
        source_id=source.filename,
        filename=source.filename,
        items=items,
        full_text=full_text,
        total_chars=len(full_text),
        engine=engine.name,
        warnings=list(dict.fromkeys(warnings)),
        metrics={
            "targets": len(decision.targets),
            "items": len(items),
            "people_candidates": len(people),
        },
    )


def _ocr_pptx_slide(
    source: FileExtraction,
    path: Path,
    file_bytes: bytes,
    slide_index: int,
    engine,
    reason: str,
) -> list[OcrItem]:
    images = [
        img for img in extract_pptx_images_by_slide(path) if img.slide_index == slide_index
    ]
    items: list[OcrItem] = []
    for img in images:
        cached = get_cached_item(
            file_bytes,
            slide_index,
            img.image_index,
            engine.name,
            settings.ocr_dpi,
        )
        if cached:
            items.append(cached)
            continue
        result = engine.extract_text(img.image_bytes)
        text = clean_ocr_text(result.text)
        item = OcrItem(
            source_id=f"{source.filename}#ocr-slide-{slide_index}",
            filename=f"{source.filename}#ocr-slide-{slide_index}",
            source_type=OcrSourceType.PPTX_SLIDE_IMAGE,
            page_or_slide=slide_index,
            image_index=img.image_index,
            text=text,
            confidence=result.confidence,
            engine=engine.name,
            reason=reason or img.probable_reason,
            warnings=list(result.warnings),
            char_count=len(text),
        )
        store_cached_item(file_bytes, item, slide_index, img.image_index, engine.name, settings.ocr_dpi)
        items.append(item)
    return items


def _ocr_pdf_page(
    source: FileExtraction,
    path: Path,
    file_bytes: bytes,
    page_index: int,
    engine,
    reason: str,
) -> list[OcrItem]:
    render = render_pdf_page(path, page_index, dpi=settings.ocr_dpi)
    if render is None:
        return []
    if render.warnings and not render.image_bytes:
        return [
            OcrItem(
                source_id=f"{source.filename}#ocr-page-{page_index}",
                filename=f"{source.filename}#ocr-page-{page_index}",
                source_type=OcrSourceType.PDF_PAGE,
                page_or_slide=page_index,
                text="",
                engine=engine.name,
                reason=reason,
                warnings=render.warnings,
            )
        ]
    cached = get_cached_item(
        file_bytes, page_index, None, engine.name, settings.ocr_dpi
    )
    if cached:
        return [cached]
    result = engine.extract_text(render.image_bytes)
    text = clean_ocr_text(result.text)
    item = OcrItem(
        source_id=f"{source.filename}#ocr-page-{page_index}",
        filename=f"{source.filename}#ocr-page-{page_index}",
        source_type=OcrSourceType.PDF_PAGE,
        page_or_slide=page_index,
        text=text,
        confidence=result.confidence,
        engine=engine.name,
        reason=reason,
        warnings=list(result.warnings) + render.warnings,
        char_count=len(text),
    )
    store_cached_item(file_bytes, item, page_index, None, engine.name, settings.ocr_dpi)
    return [item]


def _ocr_standalone(
    source: FileExtraction,
    path: Path,
    file_bytes: bytes,
    engine,
    reason: str,
) -> list[OcrItem]:
    loaded = load_image_bytes(path)
    if loaded is None:
        return []
    cached = get_cached_item(file_bytes, None, 1, engine.name, settings.ocr_dpi)
    if cached:
        return [cached]
    result = engine.extract_text(loaded.image_bytes)
    text = clean_ocr_text(result.text)
    item = OcrItem(
        source_id=f"{source.filename}#ocr",
        filename=f"{source.filename}#ocr",
        source_type=OcrSourceType.STANDALONE_IMAGE,
        image_index=1,
        text=text,
        confidence=result.confidence,
        engine=engine.name,
        reason=reason,
        warnings=list(result.warnings),
        char_count=len(text),
    )
    store_cached_item(file_bytes, item, None, 1, engine.name, settings.ocr_dpi)
    return [item]
