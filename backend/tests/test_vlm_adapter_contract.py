"""VLM adapter contract unit tests (H.9.2)."""

from __future__ import annotations

import json
from uuid import uuid4

import pytest

from app.config import settings
from app.models.domain import utc_now
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.schemas.visual_evidence import (
    VisualClassification,
    VisualContentType,
    VisualRouteAction,
    VisualEvidenceReport,
    VisualSourceItem,
)
from app.schemas.vlm import VlmTaskType
from app.services.analysis.contract_builder import ContractBuilderService
from app.services.vlm.vlm_contracts import VlmExtractionContext
from app.services.vlm.vlm_evidence_builder import VlmEvidenceBuilder
from app.services.vlm.vlm_prompt_builder import (
    build_vlm_prompt,
    prompt_forbids_invention,
    prompt_requires_json_only,
)
from app.services.vlm.vlm_result_parser import parse_vlm_json_response
from app.services.vlm.vlm_router import (
    VlmEnrichmentService,
    map_content_type_to_task,
    select_vlm_candidates,
)
from app.services.vlm.vlm_stub_adapter import StubVlmAdapter


def _vlm_candidate(confidence: float = 0.85) -> VisualClassification:
    return VisualClassification(
        item=VisualSourceItem(
            source_id="deck#7",
            filename="deck.pptx",
            source_type="pptx",
            page_or_slide=7,
            text_chars=120,
            image_count=1,
            has_text_layer=True,
            has_images=True,
            raw_text_preview="Qdrant Neo4j BERTopic architecture pipeline",
        ),
        content_type=VisualContentType.architecture_diagram,
        confidence=confidence,
        route_action=VisualRouteAction.mark_vlm_candidate_only,
        vlm_candidate=True,
    )


def test_disabled_vlm_returns_skipped_report(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "vlm_enabled", False)
    extraction = ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[],
        extracted_at=utc_now(),
    )
    _, report = VlmEnrichmentService().enrich(extraction)
    assert report.enabled is False
    assert "disabled" in report.warnings[0].lower()


def test_visual_candidate_selected_for_vlm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "vlm_min_visual_confidence", 0.6)
    report = VisualEvidenceReport(classifications=[_vlm_candidate()])
    selected, selections = select_vlm_candidates(report)
    assert len(selected) == 1
    assert selections[0].selected is True


def test_visual_candidate_below_confidence_skipped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "vlm_min_visual_confidence", 0.9)
    report = VisualEvidenceReport(classifications=[_vlm_candidate(confidence=0.5)])
    selected, selections = select_vlm_candidates(report)
    assert not selected
    assert selections[0].skipped_reason.startswith("confidence_below")


def test_content_type_maps_to_task() -> None:
    assert map_content_type_to_task("tech_stack_slide") == VlmTaskType.extract_tech_stack
    assert map_content_type_to_task("ui_screenshot") == VlmTaskType.extract_ui_features


def test_stub_no_hallucinated_team() -> None:
    adapter = StubVlmAdapter()
    ctx = VlmExtractionContext(
        filename="x.pptx",
        page_or_slide=25,
        visual_content_type="team_slide",
        text_layer_preview="Команда проекта",
    )
    result = adapter.extract(b"", VlmTaskType.extract_team, ctx)
    assert result.field_candidates == []
    assert any("does not infer people" in w for w in result.warnings)


def test_stub_extracts_tech_only_from_context() -> None:
    adapter = StubVlmAdapter()
    ctx = VlmExtractionContext(
        filename="x.pptx",
        text_layer_preview="Stack uses Qdrant and Neo4j",
    )
    result = adapter.extract(b"x", VlmTaskType.extract_tech_stack, ctx)
    tech = result.field_candidates[0].value
    assert "Qdrant" in tech
    assert "Neo4j" in tech


def test_prompt_builder_rules() -> None:
    prompt = build_vlm_prompt(
        VlmTaskType.extract_team,
        VlmExtractionContext(filename="a.pptx"),
    )
    assert prompt_requires_json_only(prompt)
    assert prompt_forbids_invention(prompt)


def test_parser_valid_json() -> None:
    raw = json.dumps(
        {
            "field_candidates": {"tech_stack": ["Qdrant"]},
            "confidence": 0.8,
            "warnings": [],
        }
    )
    parsed = parse_vlm_json_response(raw)
    assert parsed["field_candidates"]["tech_stack"] == ["Qdrant"]
    assert parsed["confidence"] == 0.8


def test_parser_markdown_fenced_json() -> None:
    raw = '```json\n{"field_candidates": {"goals": ["Goal A"]}, "confidence": 0.7}\n```'
    parsed = parse_vlm_json_response(raw)
    assert parsed["field_candidates"]["goals"] == ["Goal A"]
    assert any("fence" in w.lower() for w in parsed["warnings"])


def test_parser_invalid_json_graceful() -> None:
    parsed = parse_vlm_json_response("not json at all")
    assert parsed["field_candidates"] == {}
    assert parsed["errors"]


def test_vlm_evidence_builder_creates_virtual_file() -> None:
    from app.schemas.vlm import VlmExtractionReport, VlmFieldCandidate, VlmStructuredExtraction

    report = VlmExtractionReport(
        enabled=True,
        provider="stub",
        extractions=[
            VlmStructuredExtraction(
                provider="stub",
                source_filename="deck.pptx",
                source_location="slide-7",
                visual_content_type="tech_stack_slide",
                task_type="extract_tech_stack",
                field_candidates=[
                    VlmFieldCandidate(
                        field_name="tech_stack",
                        value=["Qdrant", "Neo4j"],
                        confidence=0.8,
                        source_slide=7,
                    )
                ],
                confidence=0.8,
            )
        ],
    )
    files = VlmEvidenceBuilder.build_file_extractions(report)
    assert len(files) == 1
    assert files[0].file_type == "vlm"
    assert files[0].metadata["is_vlm_derivative"] is True
    assert "Qdrant" in files[0].extracted_text


def test_contract_builder_vlm_disabled_preserves_flow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "vlm_enabled", False)
    monkeypatch.setattr(settings, "ocr_enabled", False)
    text = "Slide 1:\nЦели проекта\nАвтоматизация процесса"
    extraction = ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[
            FileExtraction(
                filename="deck.pptx",
                file_type="pptx",
                extracted_text=text,
                metadata={"slides_count": 1},
            )
        ],
        extracted_at=utc_now(),
    )
    builder = ContractBuilderService.__new__(ContractBuilderService)
    from app.services.contract_fidelity.completeness_gate import ContractCompletenessGate
    from app.services.contract_fidelity.landing_document_detector import LandingDocumentDetector
    from app.services.contract_fidelity.presentation_landing_synthesizer import (
        PresentationLandingSynthesizer,
    )
    from app.services.contract_fidelity.source_type_detector import SourceTypeDetector
    from app.services.contract_fidelity.structured_landing_parser import StructuredLandingParser
    from app.services.evidence.multi_source_assembler import MultiSourceEvidenceAssembler
    from app.services.evidence.source_inventory import SourceInventoryBuilder
    from app.services.fusion.field_fusion_engine import FieldFusionEngine
    from app.services.ocr.ocr_enrichment import OcrEnrichmentService
    from app.services.orchestration.document_orchestrator import DocumentOrchestrator
    from app.services.visual.visual_source_classifier import VisualSourceClassifier
    from app.services.vlm.vlm_router import VlmEnrichmentService

    builder._detector = LandingDocumentDetector()
    builder._source_type_detector = SourceTypeDetector()
    builder._structured_parser = StructuredLandingParser()
    builder._presentation_synthesizer = PresentationLandingSynthesizer()
    builder._completeness_gate = ContractCompletenessGate()
    builder._inventory_builder = SourceInventoryBuilder()
    builder._multi_source_assembler = MultiSourceEvidenceAssembler()
    builder._field_fusion_engine = FieldFusionEngine()
    builder._document_orchestrator = DocumentOrchestrator()
    builder._ocr_enrichment = OcrEnrichmentService()
    builder._visual_classifier = VisualSourceClassifier()
    builder._vlm_enrichment = VlmEnrichmentService()

    contract = builder.build(extraction)
    assert contract.fidelity is not None
    assert contract.fidelity.vlm_extraction_report is not None
    assert contract.fidelity.vlm_extraction_report.enabled is False
