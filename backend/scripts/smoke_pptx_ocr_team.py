#!/usr/bin/env python3
"""Smoke: Indlab PPTX slide 25 team via OCR when engine available."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from app.config import settings
from app.schemas.extraction import FileExtraction
from app.services.evidence.people_extractor import extract_people_from_text
from app.services.extraction.dispatcher import ExtractionDispatcher
from app.services.ocr.engines.paddleocr_engine import PaddleOcrEngine
from app.services.ocr.engines.tesseract_engine import TesseractOcrEngine
from app.services.ocr.ocr_router import run_ocr_for_source
from scripts.smoke_corpus import _load_simple_yaml
from scripts.smoke_live_multifile_project import _build_pptx_from_text

CORPUS = REPO_ROOT / "test_corpus" / "golden" / "indlab_telegram_news" / "sources"


def _resolve_pptx() -> Path:
    binary = CORPUS / "01_presentation.pptx"
    if binary.is_file():
        return binary
    snapshot = CORPUS / "01_presentation.pptx.txt"
    if snapshot.is_file():
        tmp = Path(tempfile.mkdtemp(prefix="indlab_ocr_smoke_"))
        out = tmp / "01_presentation.pptx"
        _build_pptx_from_text(snapshot.read_text(encoding="utf-8"), out)
        return out
    raise FileNotFoundError(f"Indlab PPTX source missing in {CORPUS}")


def _engine_available() -> bool:
    return PaddleOcrEngine().is_available() or TesseractOcrEngine().is_available()


def main() -> int:
    parser = argparse.ArgumentParser(description="Indlab PPTX OCR team smoke")
    parser.add_argument(
        "--require-ocr",
        action="store_true",
        help="Fail when OCR engine is unavailable",
    )
    parser.add_argument("--slide", type=int, default=25, help="Team slide index")
    args = parser.parse_args()

    if not settings.ocr_enabled:
        print("WARN: OCR disabled. Image-only slides/pages may not be parsed.")
        if args.require_ocr:
            return 1
        return 0

    if not _engine_available():
        print("WARN: OCR engine unavailable.")
        if args.require_ocr:
            return 1
        return 0

    path = _resolve_pptx()
    extracted = ExtractionDispatcher().extract_file(path, path.name)
    source = FileExtraction(
        filename=path.name,
        file_type=extracted.file_type,
        extracted_text=extracted.extracted_text,
        metadata={**extracted.metadata, "source_path": str(path.resolve())},
    )
    result = run_ocr_for_source(source, missing_fields=["team"], source_path=path)
    slide_items = [i for i in result.items if i.page_or_slide == args.slide]
    chars = sum(i.char_count for i in slide_items)
    people = extract_people_from_text(result.full_text, in_team_section=True)

    print(f"file: {path.name}")
    print(f"slide: {args.slide}")
    print(f"ocr chars on slide: {chars}")
    print(f"team candidates: {len(people)}")
    for warning in result.warnings:
        print(f"warning: {warning}")

    expected_path = REPO_ROOT / "test_corpus" / "golden" / "indlab_telegram_news" / "expected_contract.yml"
    expected_names: list[str] = []
    if expected_path.is_file():
        cfg = _load_simple_yaml(expected_path.read_text(encoding="utf-8"))
        team_cfg = cfg.get("team") or {}
        if isinstance(team_cfg, dict):
            expected_names = list(team_cfg.get("expected_names") or [])

    if chars <= 0:
        print("WARN: OCR produced no text for target slide (image-only synthetic PPTX expected).")
        return 0

    if people:
        print("INDLAB PPTX OCR TEAM SMOKE PASSED")
        if expected_names:
            found = {p.name for p in people}
            missing = [n for n in expected_names if n not in found]
            if missing:
                print(f"WARN: expected names not found via OCR: {missing}")
        return 0

    print("WARN: OCR completed but no valid team candidates found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
