#!/usr/bin/env python3
"""Debug VLM candidate routing and optional stub extraction."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from uuid import uuid4

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.config import settings
from app.models.domain import utc_now
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.services.extraction.dispatcher import ExtractionDispatcher
from app.services.visual.visual_source_classifier import VisualSourceClassifier
from app.services.vlm.vlm_debug import format_candidate_table, format_stub_extractions
from app.services.vlm.vlm_router import plan_vlm_candidates, run_stub_extractions


def _parse_slides(raw: str) -> set[int] | None:
    if not raw.strip():
        return None
    return {int(x.strip()) for x in raw.split(",") if x.strip().isdigit()}


def main() -> int:
    parser = argparse.ArgumentParser(description="Debug VLM candidate routing")
    parser.add_argument("--file", required=True, help="Path to PPTX/PDF/image")
    parser.add_argument(
        "--slides",
        default="",
        help="Comma-separated slide/page numbers (optional filter)",
    )
    parser.add_argument(
        "--enable-stub",
        action="store_true",
        help="Run stub VLM on selected candidates",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON report")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.is_file():
        print(f"File not found: {path}", file=sys.stderr)
        return 1

    slide_filter = _parse_slides(args.slides)

    dispatcher = ExtractionDispatcher()
    extracted = dispatcher.extract_file(path, path.name)
    source = FileExtraction(
        filename=path.name,
        file_type=extracted.file_type,
        extracted_text=extracted.extracted_text,
        metadata={**extracted.metadata, "source_path": str(path.resolve())},
        warnings=extracted.warnings,
    )
    extraction = ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[source],
        extracted_at=utc_now(),
    )

    visual_report = VisualSourceClassifier().classify_extraction(extraction)
    selections, report = plan_vlm_candidates(visual_report)

    print(f"vlm_enabled={settings.vlm_enabled} provider={settings.vlm_provider}")
    print(f"visual_vlm_candidates={visual_report.vlm_candidates_count}")
    print()
    print(format_candidate_table(selections, slide_filter=slide_filter))

    if args.enable-stub:
        stub_report = run_stub_extractions(
            extraction,
            visual_report,
            slide_filter=slide_filter,
        )
        print()
        print(format_stub_extractions(stub_report.extractions))
        if args.json:
            from app.services.vlm.vlm_debug import format_report_json

            print(format_report_json(stub_report))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
