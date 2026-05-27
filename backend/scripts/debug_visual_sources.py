#!/usr/bin/env python3
"""Debug visual source classifier for PPTX/PDF/image files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from uuid import uuid4

from app.models.domain import utc_now
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.services.extraction.dispatcher import ExtractionDispatcher
from app.services.visual.visual_debug import format_classification_table, format_report_json
from app.services.visual.visual_source_classifier import VisualSourceClassifier


def main() -> int:
    parser = argparse.ArgumentParser(description="Debug visual source classifier")
    parser.add_argument("--file", required=True, help="Path to PPTX/PDF/image")
    parser.add_argument(
        "--slides",
        default="",
        help="Comma-separated slide/page numbers (optional filter)",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON report")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.is_file():
        print(f"File not found: {path}", file=sys.stderr)
        return 1

    slide_filter = {
        int(x.strip()) for x in args.slides.split(",") if x.strip().isdigit()
    } or None

    dispatcher = ExtractionDispatcher()
    extracted = dispatcher.extract_file(path, path.name)
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

    classifier = VisualSourceClassifier()
    report = classifier.classify_extraction(
        ExtractionResult(
            project_id=uuid4(),
            payload=ExtractionPayload(),
            files=[source],
            extracted_at=utc_now(),
        )
    )

    if args.json:
        print(format_report_json(report))
    else:
        print(format_classification_table(report.classifications, slide_filter=slide_filter))
        print()
        print(
            f"sources={report.source_count} items={report.visual_items_count} "
            f"vlm_candidates={report.vlm_candidates_count} "
            f"ocr_candidates={report.ocr_candidates_count}"
        )
        for warning in report.warnings:
            print(f"warning: {warning}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
