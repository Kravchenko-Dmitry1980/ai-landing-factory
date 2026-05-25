"""Document renderers for OCR."""

from app.services.ocr.renderers.image_loader import load_image_bytes
from app.services.ocr.renderers.pdf_page_renderer import render_pdf_page, render_pdf_pages
from app.services.ocr.renderers.pptx_image_extractor import (
    extract_pptx_images_by_slide,
    slide_image_counts,
)

__all__ = [
    "extract_pptx_images_by_slide",
    "slide_image_counts",
    "render_pdf_page",
    "render_pdf_pages",
    "load_image_bytes",
]
