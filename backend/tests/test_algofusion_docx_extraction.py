"""Algofusion DOCX text → section extraction acceptance tests."""

from __future__ import annotations

from pathlib import Path

from app.services.contract_fidelity.landing_document_detector import LandingDocumentDetector
from app.services.contract_fidelity.structured_landing_parser import StructuredLandingParser
from app.services.evidence.source_inventory import SourceInventoryBuilder, has_single_high_confidence_ready_doc
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from datetime import datetime, timezone
from uuid import uuid4

FIXTURE = Path(__file__).parent / "fixtures" / "algofusion_landing.txt"


def test_algofusion_sections_detected() -> None:
    text = FIXTURE.read_text(encoding="utf-8")
    det = LandingDocumentDetector().detect(text)
    assert det.is_structured_landing is True
    assert det.confidence >= 0.65
    for key in ("essence", "tasks", "purpose", "results", "outlook", "tech_stack", "team"):
        assert key in det.detected_sections


def test_algofusion_parser_core_fields() -> None:
    text = FIXTURE.read_text(encoding="utf-8")
    parsed = StructuredLandingParser().parse(text)
    assert parsed.title and "Computer Vision" in parsed.title
    assert parsed.client and "АлгоФьюжн" in parsed.client
    assert parsed.timeline and "марта" in parsed.timeline
    assert parsed.lead and "Кус" in parsed.lead
    assert "валютно-обмен" in (parsed.essence or "").lower()
    assert len(parsed.purpose) >= 4
    assert len(parsed.tasks) >= 5
    assert len(parsed.results) >= 8
    assert len(parsed.outlook) >= 5
    assert parsed.tagline and "цифровой паспорт" in parsed.tagline.lower()


def test_algofusion_metrics_and_stack_and_team() -> None:
    text = FIXTURE.read_text(encoding="utf-8")
    parsed = StructuredLandingParser().parse(text)
    assert len(parsed.tech_stack_grouped) >= 4
    flat = " ".join(item for items in parsed.tech_stack_grouped.values() for item in items)
    for token in ("YOLO", "ByteTrack", "Redis", "Docker", "FSM", "React"):
        assert token in flat
    assert len(parsed.team) >= 10
    names = " ".join(m.name for m in parsed.team)
    assert "Кривонос" in names
    assert "Гречко" in names
    assert "Семин" in names


def test_algofusion_classified_as_ready_landing_doc() -> None:
    text = FIXTURE.read_text(encoding="utf-8")
    extraction = ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[
            FileExtraction(
                filename="algofusion.docx",
                file_type="docx",
                extracted_text=text,
            )
        ],
        extracted_at=datetime.now(timezone.utc),
    )
    inventory = SourceInventoryBuilder().build(extraction)
    assert inventory[0].detected_source_type == "ready_landing_doc"
    assert has_single_high_confidence_ready_doc(inventory) is True
