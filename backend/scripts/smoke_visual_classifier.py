#!/usr/bin/env python3
"""Lightweight smoke for visual source classifier (no OCR/VLM execution)."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
DEFAULT_CORPUS = REPO_ROOT / "test_corpus" / "golden"

sys.path.insert(0, str(BACKEND))

from app.config import settings
from app.schemas.extraction import ExtractionResult, FileExtraction
from app.schemas.visual_evidence import VisualContentType, VisualRouteAction
from app.services.extraction.dispatcher import ExtractionDispatcher
from app.services.visual.visual_source_classifier import VisualSourceClassifier
from scripts.smoke_corpus import _read_snapshot_text, _resolve_source
from scripts.smoke_live_multifile_project import _build_pptx_from_text


def _corpus_dir(project: str) -> Path:
    return DEFAULT_CORPUS / project / "sources"


def _load_pptx_source(project: str) -> tuple[Path, FileExtraction]:
    sources = _corpus_dir(project)
    binary = sources / "01_presentation.pptx"
    snapshot = sources / "01_presentation.pptx.txt"

    if binary.is_file():
        path = binary
    elif snapshot.is_file():
        tmp = Path(tempfile.mkdtemp(prefix=f"visual_smoke_{project}_"))
        path = tmp / "01_presentation.pptx"
        _build_pptx_from_text(_read_snapshot_text(snapshot), path)
    else:
        raise FileNotFoundError(f"No PPTX source for {project} in {sources}")

    extracted = ExtractionDispatcher().extract_file(path, path.name)
    source = FileExtraction(
        filename=path.name,
        file_type=extracted.file_type,
        extracted_text=extracted.extracted_text,
        metadata={**extracted.metadata, "source_path": str(path.resolve())},
        warnings=extracted.warnings,
    )
    return path, source


def _text_only_source(project: str) -> FileExtraction:
    snapshot = _corpus_dir(project) / "01_presentation.pptx.txt"
    if not snapshot.is_file():
        raise FileNotFoundError(snapshot)
    text = _read_snapshot_text(snapshot)
    resolved = _resolve_source(snapshot)
    if not resolved:
        raise ValueError(f"Cannot resolve source type for {snapshot}")
    logical_name, file_type = resolved
    return FileExtraction(
        filename=logical_name,
        file_type=file_type,
        extracted_text=text,
        metadata={"slides_count": text.count("Slide ")},
    )


def _find_classification(report, *, slide: int | None = None, content_types=None):
    content_types = content_types or []
    for cls in report.classifications:
        if slide is not None and cls.item.page_or_slide != slide:
            continue
        if content_types and cls.content_type not in content_types:
            continue
        return cls
    return None


def _check_indlab(classifier: VisualSourceClassifier) -> list[str]:
    errors: list[str] = []
    try:
        _path, source = _load_pptx_source("indlab_telegram_news")
    except FileNotFoundError:
        source = _text_only_source("indlab_telegram_news")

    report = classifier.classify_extraction(_extraction_from_files([source]))

    from app.schemas.visual_evidence import VisualSourceItem

    synthetic = VisualSourceItem(
        source_id=f"{source.filename}#slide-25",
        filename=source.filename,
        source_type="pptx",
        page_or_slide=25,
        text_chars=0,
        image_count=1,
        has_text_layer=False,
        has_images=True,
        title_hint="Команда проекта",
    )
    team_cls = classifier.classify_item(synthetic)

    if team_cls.content_type != VisualContentType.team_slide:
        errors.append(
            f"indlab slide 25 expected team_slide, got {team_cls.content_type.value}"
        )
    if team_cls.route_action not in (
        VisualRouteAction.run_ocr,
        VisualRouteAction.run_ocr_and_mark_vlm_candidate,
    ):
        errors.append(
            f"indlab slide 25 route expected OCR, got {team_cls.route_action.value}"
        )
    if not team_cls.vlm_candidate:
        errors.append("indlab slide 25 expected vlm_candidate=true")

    arch = next(
        (
            c
            for c in report.classifications
            if c.content_type
            in (VisualContentType.architecture_diagram, VisualContentType.tech_stack_slide)
        ),
        None,
    )
    if arch is None:
        errors.append("indlab: no architecture/stack slide classified")

    print(
        f"indlab: team slide 25 -> {team_cls.content_type.value}, "
        f"route={team_cls.route_action.value}, vlm={team_cls.vlm_candidate}"
    )
    if arch:
        print(
            f"indlab: arch/stack slide {arch.item.page_or_slide} -> "
            f"{arch.content_type.value}"
        )
    print(f"indlab: visual_items={report.visual_items_count} vlm={report.vlm_candidates_count}")
    return errors


def _check_ksk(classifier: VisualSourceClassifier) -> list[str]:
    errors: list[str] = []
    source = _text_only_source("ksk_it_barrier")
    report = classifier.classify_extraction(_extraction_from_files([source]))

    steps = _find_classification(report, slide=7) or next(
        (c for c in report.classifications if c.item.page_or_slide == 7),
        None,
    )
    ui = next(
        (
            c
            for c in report.classifications
            if c.content_type == VisualContentType.ui_screenshot
            or "streamlit" in (c.item.raw_text_preview or "").lower()
        ),
        None,
    )
    if steps is None:
        errors.append("ksk: slide 7 (pipeline steps) not classified")
    if ui is None:
        errors.append("ksk: no ui/streamlit slide classified")

    if steps:
        print(f"ksk: slide 7 -> {steps.content_type.value}, route={steps.route_action.value}")
    if ui:
        print(f"ksk: ui slide {ui.item.page_or_slide} -> {ui.content_type.value}")
    return errors


def _check_endocrinology(classifier: VisualSourceClassifier) -> list[str]:
    errors: list[str] = []
    snapshot = _corpus_dir("endocrinology") / "02_glaucologic_presentation.pptx.txt"
    if not snapshot.is_file():
        errors.append("endocrinology: glauco snapshot missing")
        return errors

    text = _read_snapshot_text(snapshot)
    source = FileExtraction(
        filename="02_glaucologic_presentation.pptx",
        file_type="pptx",
        extracted_text=text,
        metadata={"slides_count": text.count("Slide ")},
    )
    report = classifier.classify_extraction(_extraction_from_files([source]))

    arch = next(
        (
            c
            for c in report.classifications
            if c.content_type == VisualContentType.architecture_diagram
        ),
        None,
    )
    visual_candidates = [
        c
        for c in report.classifications
        if c.vlm_candidate or c.route_action != VisualRouteAction.skip
    ]
    if not visual_candidates:
        errors.append("endocrinology: no visual candidates detected")
    if arch is None:
        errors.append("endocrinology: architecture slide not classified")

    print(
        f"endocrinology: visual_candidates={len(visual_candidates)} "
        f"arch_slide={arch.item.page_or_slide if arch else '-'}"
    )
    return errors


def _extraction_from_files(files: list[FileExtraction]) -> ExtractionResult:
    from uuid import uuid4

    from app.models.domain import utc_now
    from app.schemas.extraction import ExtractionPayload

    return ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=files,
        extracted_at=utc_now(),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Visual classifier corpus smoke")
    parser.add_argument(
        "--project",
        default="all",
        choices=["all", "indlab_telegram_news", "ksk_it_barrier", "endocrinology"],
    )
    args = parser.parse_args()

    if not settings.ocr_enabled:
        print("NOTE: OCR disabled — smoke validates classification only (no OCR run).")

    classifier = VisualSourceClassifier()
    errors: list[str] = []

    if args.project in ("all", "indlab_telegram_news"):
        errors.extend(_check_indlab(classifier))
    if args.project in ("all", "ksk_it_barrier"):
        errors.extend(_check_ksk(classifier))
    if args.project in ("all", "endocrinology"):
        errors.extend(_check_endocrinology(classifier))

    if errors:
        print("VISUAL CLASSIFIER SMOKE FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("VISUAL CLASSIFIER SMOKE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
