#!/usr/bin/env python3
"""Lightweight smoke for VLM adapter contract (stub only, no GPU/network)."""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from app.config import settings
from app.models.domain import utc_now
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.schemas.visual_evidence import (
    VisualClassification,
    VisualContentType,
    VisualRouteAction,
    VisualSourceItem,
)
from app.schemas.vlm import VlmTaskType
from app.services.evidence.evidence_extractor import EvidenceExtractor
from app.services.evidence.source_inventory import SourceInventoryBuilder
from app.services.vlm.vlm_router import (
    VlmEnrichmentService,
    map_content_type_to_task,
    select_vlm_candidates,
)
from app.services.vlm.vlm_stub_adapter import StubVlmAdapter
from app.services.vlm.vlm_contracts import VlmExtractionContext
from scripts.smoke_corpus import _read_snapshot_text


def test_disabled_no_crash() -> list[str]:
    errors: list[str] = []
    prev = settings.vlm_enabled
    try:
        settings.vlm_enabled = False
        extraction = _sample_extraction()
        updated, report = VlmEnrichmentService().enrich(extraction, visual_report=None)
        if report.enabled:
            errors.append("disabled VLM should report enabled=false")
        if "disabled" not in report.provider:
            errors.append(f"expected disabled provider, got {report.provider}")
        if len(updated.files) != len(extraction.files):
            errors.append("disabled VLM should not add files")
    finally:
        settings.vlm_enabled = prev
    print("OK disabled VLM skipped without crash")
    return errors


def test_stub_processes_candidates() -> list[str]:
    errors: list[str] = []
    prev_enabled = settings.vlm_enabled
    prev_provider = settings.vlm_provider
    try:
        settings.vlm_enabled = True
        settings.vlm_provider = "stub"
        visual_report = _visual_report_with_candidates()
        selected, _ = select_vlm_candidates(visual_report)
        if not selected:
            errors.append("expected selected VLM candidates")
        extraction = _sample_extraction()
        updated, report = VlmEnrichmentService().enrich(
            extraction,
            visual_report=visual_report,
        )
        if report.processed_count <= 0:
            errors.append("stub should process at least one candidate")
        vlm_files = [f for f in updated.files if f.file_type == "vlm"]
        if not vlm_files:
            errors.append("stub should add virtual vlm FileExtraction")
        item_count = len(updated.files)
    finally:
        settings.vlm_enabled = prev_enabled
        settings.vlm_provider = prev_provider
    print(f"OK stub processed candidates files={item_count}")
    return errors


def test_stub_no_team_hallucination() -> list[str]:
    errors: list[str] = []
    adapter = StubVlmAdapter()
    context = VlmExtractionContext(
        filename="team.pptx",
        page_or_slide=25,
        visual_content_type="team_slide",
        text_layer_preview="Команда проекта",
        target_fields=["team"],
    )
    result = adapter.extract(b"fake-image", VlmTaskType.extract_team, context)
    if result.field_candidates:
        errors.append("stub must not return team field candidates")
    if not any("does not infer people" in w for w in result.warnings):
        errors.append("stub team warning missing")
    print("OK stub does not hallucinate team")
    return errors


def test_stub_echoes_tech_from_context() -> list[str]:
    errors: list[str] = []
    adapter = StubVlmAdapter()
    context = VlmExtractionContext(
        filename="deck.pptx",
        page_or_slide=7,
        visual_content_type="tech_stack_slide",
        text_layer_preview="Stack: Qdrant, Neo4j, BERTopic pipeline",
        target_fields=["tech_stack"],
    )
    result = adapter.extract(b"img", VlmTaskType.extract_tech_stack, context)
    values = []
    for cand in result.field_candidates:
        if cand.field_name == "tech_stack" and isinstance(cand.value, list):
            values.extend(cand.value)
    if "Qdrant" not in values or "Neo4j" not in values:
        errors.append(f"stub should echo tech from context, got {values}")
    print(f"OK stub tech echo: {values}")
    return errors


def test_vlm_virtual_source_evidence_extractor() -> list[str]:
    errors: list[str] = []
    prev_enabled = settings.vlm_enabled
    prev_provider = settings.vlm_provider
    try:
        settings.vlm_enabled = True
        settings.vlm_provider = "stub"
        extraction = _sample_extraction()
        updated, report = VlmEnrichmentService().enrich(
            extraction,
            visual_report=_visual_report_with_candidates(),
        )
        inventory = SourceInventoryBuilder().build(updated)
        items = EvidenceExtractor().extract(updated, inventory)
        vlm_files = [f for f in updated.files if f.file_type == "vlm"]
        if report.processed_count > 0 and vlm_files and not items:
            errors.append("EvidenceExtractor should consume virtual VLM sources")
        item_count = len(items)
    finally:
        settings.vlm_enabled = prev_enabled
        settings.vlm_provider = prev_provider
    print(f"OK evidence extractor items={item_count}")
    return errors


def test_content_type_task_mapping() -> list[str]:
    errors: list[str] = []
    if map_content_type_to_task("architecture_diagram") != VlmTaskType.extract_architecture:
        errors.append("architecture mapping failed")
    if map_content_type_to_task("team_slide") != VlmTaskType.extract_team:
        errors.append("team mapping failed")
    print("OK content type task mapping")
    return errors


def _sample_extraction() -> ExtractionResult:
    snap = (
        REPO_ROOT
        / "test_corpus"
        / "golden"
        / "indlab_telegram_news"
        / "sources"
        / "01_presentation.pptx.txt"
    )
    text = _read_snapshot_text(snap) if snap.is_file() else "Slide 7:\nQdrant Neo4j BERTopic"
    return ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[
            FileExtraction(
                filename="01_presentation.pptx",
                file_type="pptx",
                extracted_text=text,
                metadata={"slides_count": text.count("Slide ")},
            )
        ],
        extracted_at=utc_now(),
    )


def _visual_report_with_candidates():
    from app.schemas.visual_evidence import VisualEvidenceReport

    cls = VisualClassification(
        item=VisualSourceItem(
            source_id="deck#7",
            filename="01_presentation.pptx",
            source_type="pptx",
            page_or_slide=7,
            text_chars=200,
            image_count=1,
            has_text_layer=True,
            has_images=True,
            title_hint="Архитектура",
            raw_text_preview="Qdrant BERTopic Neo4j pipeline architecture",
        ),
        content_type=VisualContentType.tech_stack_slide,
        confidence=0.85,
        route_action=VisualRouteAction.mark_vlm_candidate_only,
        reason="tech stack visual",
        vlm_candidate=True,
    )
    return VisualEvidenceReport(
        source_count=1,
        visual_items_count=1,
        classifications=[cls],
        vlm_candidates_count=1,
    )


def main() -> int:
    errors: list[str] = []
    errors.extend(test_disabled_no_crash())
    errors.extend(test_content_type_task_mapping())
    errors.extend(test_stub_no_team_hallucination())
    errors.extend(test_stub_echoes_tech_from_context())
    errors.extend(test_stub_processes_candidates())
    errors.extend(test_vlm_virtual_source_evidence_extractor())

    if errors:
        print("VLM ADAPTER CONTRACT SMOKE FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("VLM ADAPTER CONTRACT SMOKE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
