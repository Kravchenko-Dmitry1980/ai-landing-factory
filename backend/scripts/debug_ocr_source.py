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
from app.services.evidence.ocr_team_extractor import extract_team_from_ocr_text
from app.services.evidence.people_extractor import extract_people_from_text
from app.services.extraction.dispatcher import ExtractionDispatcher
from app.services.ocr.engines.tesseract_engine import TesseractOcrEngine, get_tesseract_lang
from app.services.ocr.ocr_decision import should_ocr_source
from app.services.ocr.ocr_env import any_engine_ready, collect_ocr_runtime_status, format_status_text
from app.services.ocr.ocr_router import run_ocr_for_source
from app.services.ocr.postprocess.ocr_team_text_normalizer import (
    detect_team_ocr_section,
    normalize_ocr_team_text,
)
from app.services.ocr.renderers.pptx_image_extractor import extract_pptx_images_by_slide


def _print_header(title: str) -> None:
    print(f"\n=== {title} ===")


def _preview(text: str, limit: int = 480) -> str:
    compact = text[:limit].replace("\n", " | ")
    if len(text) > limit:
        compact += " ..."
    return compact


def main() -> int:
    parser = argparse.ArgumentParser(description="Debug OCR for one source file")
    parser.add_argument("--file", required=True, help="Path to PPTX/PDF/image")
    parser.add_argument(
        "--slides",
        default="",
        help="Comma-separated slide/page numbers to inspect (optional filter)",
    )
    parser.add_argument(
        "--require-ocr",
        action="store_true",
        help="Exit 1 if no OCR engine is ready",
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

    runtime = collect_ocr_runtime_status(
        test_image=True,
        require_inference=True,
        test_pptx=path,
        test_slides=list(slide_filter) or None,
    )
    _print_header("OCR runtime summary")
    print(format_status_text(runtime))

    if args.require_ocr and not any_engine_ready(runtime, require_inference=True):
        print("\nFAIL: --require-ocr but no OCR engine is ready", file=sys.stderr)
        if runtime.paddleocr.init_ok and runtime.paddleocr.inference_ok is False:
            print(
                f"PaddleOCR inference failed: {runtime.paddleocr.error_code or 'unknown'}",
                file=sys.stderr,
            )
        return 1

    _print_header("Source")
    print(f"path: {path}")
    print(f"type: {path.suffix.lower()}")
    print(f"configured_engine: {settings.ocr_engine}")
    print(f"fallback_engine: {settings.ocr_fallback_engine}")
    tess = TesseractOcrEngine()
    if tess.is_available():
        print(f"tesseract_lang: {get_tesseract_lang()}")

    dispatcher = ExtractionDispatcher()
    extracted = dispatcher.extract_file(path, path.name)
    print(f"normal text chars: {len((extracted.extracted_text or '').strip())}")
    print(f"warnings: {extracted.warnings}")

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

    if not any_engine_ready(runtime, require_inference=True):
        print("\nSkipping OCR extraction: no engine ready.")
        for error in runtime.errors:
            print(f"error: {error}")
        print(f"recommended: {runtime.recommended_action}")
        return 1 if args.require_ocr else 0

    result = run_ocr_for_source(source, missing_fields=["team"], source_path=path)
    _print_header("OCR result")
    print(f"engine: {result.engine or '-'}")
    print(f"total chars: {result.total_chars}")
    fallback_used = (
        result.engine
        and settings.ocr_engine.lower() != (result.engine or "").lower()
        and result.engine == settings.ocr_fallback_engine
    )
    print(f"fallback_used: {fallback_used}")
    for warning in result.warnings:
        print(f"warning: {warning}")

    slide_texts: list[str] = []
    for item in result.items:
        if slide_filter and item.page_or_slide not in slide_filter:
            continue
        slide_texts.append(item.text)
        preview = _preview(item.text)
        print(
            f"  item slide/page={item.page_or_slide} chars={item.char_count} "
            f"engine={item.engine} preview={preview!r}"
        )

    focus_text = "\n\n".join(slide_texts) if slide_texts else result.full_text
    normalized = normalize_ocr_team_text(focus_text)
    team_detected = detect_team_ocr_section(focus_text)

    _print_header("OCR text preview")
    print(f"team section detected: {team_detected}")
    print(f"raw preview: {_preview(focus_text)!r}")
    print(f"normalized preview: {_preview(normalized)!r}")

    ocr_team = extract_team_from_ocr_text(
        focus_text,
        source_trace=f"{path.name}#ocr",
    )
    people = ocr_team.members or extract_people_from_text(
        normalized,
        source_ref=f"{path.name}#ocr",
        in_team_section=True,
    )

    _print_header("Team extraction")
    print(f"accepted count: {len(people)}")
    for member in people[:20]:
        print(f"  + {member.name} ({member.role})")

    if ocr_team.rejected:
        _print_header("Rejected person candidates")
        for name, role, reason in ocr_team.rejected[:20]:
            print(f"  - {name!r} role={role!r} reason={reason}")

    for warning in ocr_team.warnings:
        print(f"warning: {warning}")

    slide_num = next(iter(slide_filter), 0)
    _print_header("Benchmark hint")
    print("Compare engines:")
    print(
        f'  python scripts/benchmark_ocr_engines.py --file "{path}" '
        f"--slides {slide_num} --engines tesseract,easyocr,paddleocr"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
