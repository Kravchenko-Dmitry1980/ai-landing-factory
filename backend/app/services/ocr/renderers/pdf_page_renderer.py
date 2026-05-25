"""Render PDF pages to images for OCR."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class PdfPageRenderResult:
    page_index: int
    image_bytes: bytes
    warnings: list[str]


def pymupdf_available() -> bool:
    try:
        import fitz  # noqa: F401

        return True
    except ImportError:
        return False


def render_pdf_page(path: Path, page_index: int, dpi: int = 250) -> PdfPageRenderResult | None:
    """Render a single PDF page (1-based index) to PNG bytes."""
    if not pymupdf_available():
        return PdfPageRenderResult(
            page_index=page_index,
            image_bytes=b"",
            warnings=["PyMuPDF not installed; PDF OCR skipped."],
        )
    try:
        import fitz

        doc = fitz.open(str(path))
        if page_index < 1 or page_index > len(doc):
            doc.close()
            return PdfPageRenderResult(
                page_index=page_index,
                image_bytes=b"",
                warnings=[f"PDF page {page_index} out of range (pages={len(doc)})"],
            )
        page = doc[page_index - 1]
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        data = pix.tobytes("png")
        doc.close()
        return PdfPageRenderResult(page_index=page_index, image_bytes=data, warnings=[])
    except Exception as exc:
        logger.warning("PDF page render failed page=%s path=%s: %s", page_index, path, exc)
        return PdfPageRenderResult(
            page_index=page_index,
            image_bytes=b"",
            warnings=[f"PDF render failed: {exc}"],
        )


def render_pdf_pages(path: Path, dpi: int = 250, max_pages: int = 30) -> list[PdfPageRenderResult]:
    """Render low-text candidate pages up to max_pages."""
    if not pymupdf_available():
        return [
            PdfPageRenderResult(
                page_index=0,
                image_bytes=b"",
                warnings=["PyMuPDF not installed; PDF OCR skipped."],
            )
        ]
    try:
        import fitz

        doc = fitz.open(str(path))
        total = min(len(doc), max_pages)
        doc.close()
    except Exception as exc:
        return [
            PdfPageRenderResult(
                page_index=0,
                image_bytes=b"",
                warnings=[f"PDF open failed: {exc}"],
            )
        ]
    return [render_pdf_page(path, idx, dpi=dpi) for idx in range(1, total + 1)]
