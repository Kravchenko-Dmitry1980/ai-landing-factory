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
from app.services.evidence.ocr_team_extractor import extract_team_from_ocr_text
from app.services.evidence.people_extractor import extract_people_from_text
from app.services.extraction.dispatcher import ExtractionDispatcher
from app.services.ocr.engines.paddleocr_engine import PaddleOcrEngine
from app.services.ocr.engines.tesseract_engine import (
    TesseractOcrEngine,
    check_russian_language_available,
)
from app.services.ocr.ocr_env import any_engine_ready, collect_ocr_runtime_status
from app.services.ocr.ocr_router import run_ocr_for_source
from app.services.ocr.postprocess.ocr_team_text_normalizer import (
    detect_team_ocr_section,
    normalize_ocr_team_text,
)
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
    parser.add_argument(
        "--min-team-candidates",
        type=int,
        default=1,
        help="Minimum accepted team candidates",
    )
    parser.add_argument(
        "--strict-team-count",
        type=int,
        default=0,
        help="Fail if accepted candidates are fewer than this value (0=disabled)",
    )
    args = parser.parse_args()

    if not settings.ocr_enabled:
        print("WARN: OCR disabled. Image-only slides/pages may not be parsed.")
        if args.require_ocr:
            return 1
        return 0

    runtime = collect_ocr_runtime_status(test_image=True, require_inference=True)
    if not any_engine_ready(runtime, require_inference=True):
        print("WARN: OCR engine unavailable or inference not ready.")
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
    slide_text = "\n\n".join(i.text for i in slide_items if i.text.strip())
    chars = sum(i.char_count for i in slide_items)
    normalized = normalize_ocr_team_text(slide_text or result.full_text)
    team_detected = detect_team_ocr_section(slide_text or result.full_text)

    ocr_team = extract_team_from_ocr_text(
        slide_text or result.full_text,
        source_trace=f"{path.name}#slide-{args.slide}",
    )
    people = ocr_team.members or extract_people_from_text(
        normalized,
        in_team_section=True,
    )

    has_rus, _langs = check_russian_language_available()

    print(f"file: {path.name}")
    print(f"slide: {args.slide}")
    print(f"ocr engine: {result.engine or '-'}")
    print(f"ocr chars on slide: {chars}")
    print(f"team section detected: {team_detected}")
    print(f"normalized contains team marker: {'команда проекта' in normalized.lower()}")
    print(f"team candidates: {len(people)}")
    print(f"rus language available: {has_rus}")
    for warning in result.warnings:
        print(f"warning: {warning}")
    for warning in ocr_team.warnings:
        print(f"ocr_team warning: {warning}")

    expected_path = REPO_ROOT / "test_corpus" / "golden" / "indlab_telegram_news" / "expected_contract.yml"
    expected_names: list[str] = []
    if expected_path.is_file():
        cfg = _load_simple_yaml(expected_path.read_text(encoding="utf-8"))
        team_cfg = cfg.get("team") or {}
        if isinstance(team_cfg, dict):
            expected_names = list(team_cfg.get("expected_names") or [])

    if chars <= 0:
        print("WARN: OCR produced no text for target slide.")
        return 1 if args.require_ocr else 0

    if len(people) < args.min_team_candidates:
        print(
            f"FAIL: team candidates {len(people)} < min {args.min_team_candidates}",
        )
        return 1

    if args.strict_team_count and len(people) < args.strict_team_count:
        print(
            f"FAIL: team candidates {len(people)} < strict {args.strict_team_count}",
        )
        return 1

    if has_rus and len(people) >= 2:
        print("INDLAB PPTX OCR TEAM SMOKE PASSED (multi-member)")
    elif people:
        print("INDLAB PPTX OCR TEAM SMOKE PASSED")
        if expected_names:
            found = {p.name for p in people}
            missing = [n for n in expected_names if n not in found]
            if missing:
                print(f"WARN: expected names not found via OCR: {missing}")
    else:
        print("WARN: OCR completed but no valid team candidates found.")
        return 1 if args.require_ocr else 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
