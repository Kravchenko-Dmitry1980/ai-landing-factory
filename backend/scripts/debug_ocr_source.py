#!/usr/bin/env python3
"""Debug OCR extraction for a single PPTX/PDF/image source."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.config import settings
from app.schemas.extraction import FileExtraction
from app.services.evidence.people_extractor import extract_people_from_text
from app.services.extraction.dispatcher import ExtractionDispatcher
from app.services.ocr.engines.paddleocr_engine import PaddleOcrEngine
from app.services.ocr.engines.tesseract_engine import TesseractOcrEngine
from app.services.ocr.ocr_decision import should_ocr_source
from app.services.ocr.ocr_router import run_ocr_for_source
from app.services.ocr.renderers.pptx_image_extractor import extract_pptx_images_by_slide


def _print_header(title: str) -> None:
    print(f"\n=== {title} ===")


def main() -> int:
    parser = argparse.ArgumentParser(description="Debug OCR for one source file")
    parser.add_argument("--file", required=True, help="Path to PPTX/PDF/image")
    parser.add_argument(
        "--slides",
        default="",
        help="Comma-separated slide/page numbers to inspect (optional filter)",
    )
    args = parser.parse_args()

    path = Path(args.file)
    if not path.is_file():
        print(f"File not found: {path}", file=sys.stderr)
        return 1

    slide_filter = {
        int(x.strip())
        for x in args.slides.split(",")
        if x.strip().isdigit()
    }

    _print_header("Source")
    print(f"path: {path}")
    print(f"type: {path.suffix.lower()}")

    dispatcher = ExtractionDispatcher()
    extracted = dispatcher.extract_file(path, path.name)
    print(f"normal text chars: {len((extracted.extracted_text or '').strip())}")
    print(f"warnings: {extracted.warnings}")

    _print_header("OCR config")
    print(f"OCR_ENABLED: {settings.ocr_enabled}")
    print(f"OCR_ENGINE: {settings.ocr_engine}")
    print(f"paddleocr available: {PaddleOcrEngine().is_available()}")
    print(f"tesseract available: {TesseractOcrEngine().is_available()}")

    if path.suffix.lower() == ".pptx":
        images = extract_pptx_images_by_slide(path)
        if slide_filter:
            images = [img for img in images if img.slide_index in slide_filter]
        _print_header("PPTX image-only candidates")
        print(f"images found: {len(images)}")
        for img in images[:20]:
            print(
                f"  slide={img.slide_index} idx={img.image_index} "
                f"bytes={len(img.image_bytes)} reason={img.probable_reason}"
            )

    source = FileExtraction(
        filename=path.name,
        file_type=extracted.file_type,
        extracted_text=extracted.extracted_text,
        metadata={
            **extracted.metadata,
            "source_path": str(path.resolve()),
        },
        warnings=extracted.warnings,
    )

    decision = should_ocr_source(source, missing_fields=["team"])
    _print_header("OCR decision")
    print(f"action: {decision.action}")
    print(f"reason: {decision.reason}")
    for warning in decision.warnings:
        print(f"warning: {warning}")
    for target in decision.targets:
        print(
            f"  target type={target.source_type} slide/page={target.page_or_slide} "
            f"reason={target.reason}"
        )

    result = run_ocr_for_source(source, missing_fields=["team"], source_path=path)
    _print_header("OCR result")
    print(f"engine: {result.engine or '-'}")
    print(f"total chars: {result.total_chars}")
    for warning in result.warnings:
        print(f"warning: {warning}")
    for item in result.items:
        if slide_filter and item.page_or_slide not in slide_filter:
            continue
        preview = item.text[:240].replace("\n", " | ")
        print(
            f"  item slide/page={item.page_or_slide} chars={item.char_count} "
            f"engine={item.engine} preview={preview!r}"
        )

    people = extract_people_from_text(
        result.full_text,
        source_ref=f"{path.name}#ocr",
        in_team_section=True,
    )
    _print_header("Team candidates")
    print(f"count: {len(people)}")
    for member in people[:20]:
        print(f"  - {member.name} ({member.role})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
