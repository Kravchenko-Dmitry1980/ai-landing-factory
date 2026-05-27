"""Deterministic visual source classifier for PPTX/PDF/image sources."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from app.schemas.extraction import ExtractionResult, FileExtraction
from app.schemas.visual_evidence import (
    VisualClassification,
    VisualContentType,
    VisualEvidenceReport,
    VisualRouteAction,
    VisualSourceItem,
)
from app.services.contract_fidelity.pptx_team_markers import iter_pptx_slides
from app.services.ocr.renderers.pptx_image_extractor import slide_image_counts
from app.services.visual.visual_contracts import LOW_TEXT_THRESHOLD, MARKER_SETS
from app.services.visual.visual_routing import apply_route_to_classification

logger = logging.getLogger(__name__)

PAGE_SPLIT_RE = re.compile(r"(?:^|\n)(Page\s+\d+\s*:)", re.IGNORECASE)


class VisualSourceClassifier:
    """Classify visual blocks and decide routing without running VLM/OCR."""

    def classify_extraction(self, extraction: ExtractionResult) -> VisualEvidenceReport:
        all_classifications: list[VisualClassification] = []
        warnings: list[str] = []
        source_files = [
            f for f in extraction.files if not f.metadata.get("is_ocr_derivative")
        ]

        for source in source_files:
            if source.file_type not in ("pptx", "pdf", "docx", "png", "jpg", "jpeg", "webp", "image"):
                continue
            try:
                items = self.build_visual_items(source)
                for item in items:
                    all_classifications.append(self.classify_item(item))
            except Exception as exc:
                msg = f"Visual classification failed for {source.filename}: {exc}"
                logger.warning(msg)
                warnings.append(msg)

        vlm_count = sum(1 for c in all_classifications if c.vlm_candidate)
        ocr_count = sum(
            1
            for c in all_classifications
            if c.route_action
            in (
                VisualRouteAction.run_ocr,
                VisualRouteAction.run_ocr_and_mark_vlm_candidate,
            )
        )

        return VisualEvidenceReport(
            source_count=len(source_files),
            visual_items_count=len(all_classifications),
            classifications=all_classifications,
            vlm_candidates_count=vlm_count,
            ocr_candidates_count=ocr_count,
            warnings=warnings,
        )

    def build_visual_items(self, source: FileExtraction) -> list[VisualSourceItem]:
        file_type = source.file_type
        if file_type == "pptx":
            return self._items_from_pptx(source)
        if file_type == "pdf":
            return self._items_from_pdf(source)
        if file_type in ("png", "jpg", "jpeg", "webp", "image"):
            return [self._item_from_standalone_image(source)]
        if file_type in ("docx", "doc"):
            return self._items_from_docx(source)
        return []

    def classify_item(self, item: VisualSourceItem) -> VisualClassification:
        blob = self._item_blob(item)
        content_type, confidence, markers = self._score_content_type(blob, item)
        base = VisualClassification(
            item=item,
            content_type=content_type,
            confidence=confidence,
            route_action=VisualRouteAction.skip,
            reason="pending",
            markers=markers,
        )
        return apply_route_to_classification(base, blob)

    def _item_blob(self, item: VisualSourceItem) -> str:
        parts = [item.filename or "", item.title_hint or "", item.raw_text_preview or ""]
        return "\n".join(p for p in parts if p).strip()

    def _score_content_type(
        self,
        blob: str,
        item: VisualSourceItem,
    ) -> tuple[VisualContentType, float, list[str]]:
        low = blob.lower().replace("\u00a0", " ")
        scores: dict[VisualContentType, list[str]] = {}

        for ctype, markers in MARKER_SETS.items():
            matched = [m for m in markers if m in low]
            if matched:
                scores[ctype] = matched

        if not scores:
            if item.has_images and item.text_chars < LOW_TEXT_THRESHOLD:
                return VisualContentType.generic_image, 0.35, []
            return VisualContentType.unknown, 0.25, []

        best_type = max(scores, key=lambda t: len(scores[t]))
        matched = scores[best_type]

        # Disambiguate architecture vs tech stack when both match
        if (
            VisualContentType.architecture_diagram in scores
            and VisualContentType.tech_stack_slide in scores
        ):
            arch_n = len(scores[VisualContentType.architecture_diagram])
            tech_n = len(scores[VisualContentType.tech_stack_slide])
            if arch_n >= tech_n:
                best_type = VisualContentType.architecture_diagram
            else:
                best_type = VisualContentType.tech_stack_slide
            matched = scores[best_type]

        confidence = min(0.95, 0.45 + 0.12 * len(matched))
        if item.has_images and item.text_chars < LOW_TEXT_THRESHOLD:
            confidence = min(0.95, confidence + 0.08)

        return best_type, round(confidence, 2), matched

    def _items_from_pptx(self, source: FileExtraction) -> list[VisualSourceItem]:
        path = source.metadata.get("source_path")
        image_counts: dict[int, int] = {}
        image_bytes: dict[int, int] = {}
        if path:
            try:
                from app.services.ocr.renderers.pptx_image_extractor import (
                    extract_pptx_images_by_slide,
                )

                for img in extract_pptx_images_by_slide(Path(path)):
                    image_counts[img.slide_index] = image_counts.get(img.slide_index, 0) + 1
                    image_bytes[img.slide_index] = image_bytes.get(img.slide_index, 0) + len(
                        img.image_bytes
                    )
            except Exception as exc:
                logger.debug("PPTX image metadata unavailable: %s", exc)
                image_counts = slide_image_counts(Path(path)) if path else {}

        slides_count = int(source.metadata.get("slides_count") or 0)
        structured = {
            int(s.get("index", 0)): s for s in source.metadata.get("slides") or [] if s.get("index")
        }
        parsed = {
            idx: (body, title)
            for idx, body, title in iter_pptx_slides(source.extracted_text or "")
        }

        indices: set[int] = set()
        if slides_count:
            indices.update(range(1, slides_count + 1))
        indices.update(structured.keys())
        indices.update(parsed.keys())
        indices.update(image_counts.keys())

        if not indices:
            indices.add(1)

        items: list[VisualSourceItem] = []
        for idx in sorted(indices):
            meta = structured.get(idx, {})
            body, title = parsed.get(idx, ("", None))
            title_hint = (meta.get("title") or title or "").strip() or None
            raw = (meta.get("text") or body or "").strip()
            text_chars = int(meta.get("char_count") or len(raw))
            img_count = image_counts.get(idx, 0)

            items.append(
                VisualSourceItem(
                    source_id=f"{source.filename}#slide-{idx}",
                    filename=source.filename,
                    source_type="pptx",
                    page_or_slide=idx,
                    text_chars=text_chars,
                    image_count=img_count,
                    has_text_layer=text_chars >= LOW_TEXT_THRESHOLD,
                    has_images=img_count > 0,
                    extracted_image_bytes=image_bytes.get(idx),
                    title_hint=title_hint,
                    raw_text_preview=(raw[:500] if raw else title_hint),
                )
            )
        return items

    def _items_from_pdf(self, source: FileExtraction) -> list[VisualSourceItem]:
        pages_count = int(source.metadata.get("pages_count") or 0)
        text = source.extracted_text or ""
        page_parts = self._split_pdf_pages(text)
        if not pages_count:
            pages_count = len(page_parts) or 1

        items: list[VisualSourceItem] = []
        for page_idx in range(1, pages_count + 1):
            page_text = page_parts.get(page_idx, "")
            title_hint = self._first_line(page_text)
            text_chars = len(page_text.strip())
            items.append(
                VisualSourceItem(
                    source_id=f"{source.filename}#page-{page_idx}",
                    filename=source.filename,
                    source_type="pdf",
                    page_or_slide=page_idx,
                    text_chars=text_chars,
                    image_count=1 if text_chars < LOW_TEXT_THRESHOLD else 0,
                    has_text_layer=text_chars >= LOW_TEXT_THRESHOLD,
                    has_images=text_chars < LOW_TEXT_THRESHOLD,
                    title_hint=title_hint,
                    raw_text_preview=page_text[:500] if page_text else None,
                )
            )
        return items

    def _items_from_docx(self, source: FileExtraction) -> list[VisualSourceItem]:
        text = (source.extracted_text or "").strip()
        has_images = bool(source.metadata.get("has_images"))
        return [
            VisualSourceItem(
                source_id=source.filename,
                filename=source.filename,
                source_type="docx",
                text_chars=len(text),
                image_count=1 if has_images else 0,
                has_text_layer=len(text) >= LOW_TEXT_THRESHOLD,
                has_images=has_images,
                title_hint=self._first_line(text),
                raw_text_preview=text[:500] if text else None,
            )
        ]

    def _item_from_standalone_image(self, source: FileExtraction) -> VisualSourceItem:
        path = source.metadata.get("source_path")
        byte_size: int | None = None
        if path:
            try:
                byte_size = Path(path).stat().st_size
            except OSError:
                byte_size = None
        text = (source.extracted_text or "").strip()
        return VisualSourceItem(
            source_id=source.filename,
            filename=source.filename,
            source_type="image",
            text_chars=len(text),
            image_count=1,
            has_text_layer=len(text) >= LOW_TEXT_THRESHOLD,
            has_images=True,
            extracted_image_bytes=byte_size,
            raw_text_preview=text[:500] if text else None,
        )

    @staticmethod
    def _split_pdf_pages(text: str) -> dict[int, str]:
        parts = PAGE_SPLIT_RE.split(text)
        pages: dict[int, str] = {}
        i = 1
        while i < len(parts):
            header = parts[i].strip()
            body = parts[i + 1] if i + 1 < len(parts) else ""
            match = re.search(r"(\d+)", header)
            idx = int(match.group(1)) if match else len(pages) + 1
            pages[idx] = f"{header}\n{body}".strip()
            i += 2
        if not pages and text.strip():
            pages[1] = text.strip()
        return pages

    @staticmethod
    def _first_line(text: str) -> str | None:
        for line in text.splitlines():
            stripped = line.strip()
            if stripped and not re.match(r"^(Slide|Page)\s+\d+", stripped, re.I):
                return stripped[:120]
        return None
