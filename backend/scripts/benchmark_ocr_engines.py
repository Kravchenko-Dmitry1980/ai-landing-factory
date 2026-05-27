#!/usr/bin/env python3
"""Benchmark OCR engines on a PPTX/PDF/image slide."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.services.ocr.engine_registry import parse_engine_list
from app.services.ocr.ocr_benchmark import format_benchmark_table, run_ocr_benchmark


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark OCR engines on one slide/page")
    parser.add_argument("--file", required=True, help="Path to PPTX/PDF/image")
    parser.add_argument("--slides", type=int, default=0, help="Slide/page number (default 0)")
    parser.add_argument(
        "--engines",
        default="tesseract,easyocr,paddleocr,surya",
        help="Comma-separated engine list",
    )
    parser.add_argument(
        "--known-name",
        action="append",
        default=[],
        dest="known_names",
        help="Known person name for hit counting (repeatable)",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON report")
    parser.add_argument("--save-report", default="", help="Save JSON report to path")
    args = parser.parse_args(argv)

    source = Path(args.file)
    if not source.is_file():
        print(f"File not found: {source}", file=sys.stderr)
        return 1

    engines = parse_engine_list(args.engines)
    if not engines:
        print("No engines specified.", file=sys.stderr)
        return 1

    report = run_ocr_benchmark(
        source,
        page_or_slide=args.slides,
        engines=engines,
        known_names=args.known_names,
    )

    if args.json:
        print(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2))
    else:
        print(format_benchmark_table(report))
        print("")
        for result in report.results:
            if result.accepted_names:
                print(f"{result.engine} accepted: {', '.join(result.accepted_names)}")
            if result.warnings:
                for warning in result.warnings[:5]:
                    print(f"{result.engine} warning: {warning}")

    if args.save_report:
        out = Path(args.save_report)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Saved report: {out}")

    return 0 if report.best_engine else 1


if __name__ == "__main__":
    raise SystemExit(main())
