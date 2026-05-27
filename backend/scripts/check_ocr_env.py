#!/usr/bin/env python3
"""Check OCR runtime environment."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.services.ocr.ocr_env import (
    any_engine_ready,
    collect_ocr_runtime_status,
    format_status_text,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check OCR runtime environment")
    parser.add_argument("--json", action="store_true", help="Print JSON status")
    parser.add_argument(
        "--require-ocr",
        action="store_true",
        help="Exit 1 if no engine ready (includes inference smoke test)",
    )
    parser.add_argument("--test-image", action="store_true", help="Run synthetic image OCR test")
    parser.add_argument("--test-pptx", default="", help="Optional PPTX path for slide checks")
    parser.add_argument("--slides", default="", help="Comma-separated slide numbers")
    args = parser.parse_args(argv)

    pptx_path = Path(args.test_pptx) if args.test_pptx else None
    slides = [int(x.strip()) for x in args.slides.split(",") if x.strip().isdigit()]

    require_inference = args.require_ocr or args.test_image
    status = collect_ocr_runtime_status(
        test_image=args.test_image or args.require_ocr,
        require_inference=require_inference,
        test_pptx=pptx_path,
        test_slides=slides or None,
    )

    if args.json:
        print(json.dumps(status.model_dump(mode="json"), ensure_ascii=False, indent=2))
    else:
        print(format_status_text(status))

    if args.require_ocr:
        if not status.ocr_enabled:
            print("\nFAIL: --require-ocr but OCR_ENABLED=false", file=sys.stderr)
            return 1
        if not any_engine_ready(status, require_inference=True):
            print("\nFAIL: --require-ocr but no OCR engine passed readiness checks", file=sys.stderr)
            if status.paddleocr.init_ok and status.paddleocr.inference_ok is False:
                print(
                    f"PaddleOCR init_ok=True but inference_ok=False "
                    f"({status.paddleocr.error_code or 'inference_failed'})",
                    file=sys.stderr,
                )
            return 1
        if status.test_image_ok is False:
            print("\nFAIL: --require-ocr but test image OCR failed", file=sys.stderr)
            return 1

    if status.ocr_enabled and not any_engine_ready(status) and args.require_ocr:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
