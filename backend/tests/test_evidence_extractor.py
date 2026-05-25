"""Evidence extractor unit tests."""

from pathlib import Path
from uuid import uuid4

import pytest

from app.models.domain import utc_now
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.services.evidence.evidence_extractor import EvidenceExtractor
from app.services.evidence.source_inventory import SourceInventoryBuilder

TELEGRAM_FIXTURE = Path(__file__).parent / "fixtures" / "telegram_analytics_presentation.txt"


@pytest.fixture
def telegram_text() -> str:
    return TELEGRAM_FIXTURE.read_text(encoding="utf-8")


@pytest.fixture
def telegram_extraction(telegram_text: str) -> ExtractionResult:
    return ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[
            FileExtraction(
                filename="presentation.pptx",
                file_type="pptx",
                extracted_text=telegram_text,
                metadata={"slides_count": 12},
            )
        ],
        extracted_at=utc_now(),
    )


def test_evidence_count_ge_slide_count(
    telegram_extraction: ExtractionResult, telegram_text: str
) -> None:
    inventory = SourceInventoryBuilder().build(telegram_extraction)
    items = EvidenceExtractor().extract(telegram_extraction, inventory)
    slide_markers = telegram_text.count("Slide ")
    assert len(items) >= slide_markers
    assert all(item.source_id for item in items)
    assert all(item.location_index is not None for item in items if item.location_type == "slide")


def test_evidence_field_candidates_and_technologies(
    telegram_extraction: ExtractionResult,
) -> None:
    inventory = SourceInventoryBuilder().build(telegram_extraction)
    items = EvidenceExtractor().extract(telegram_extraction, inventory)
    all_tech = {t for it in items for t in it.technologies}
    assert "Qdrant" in all_tech
    assert "BERTopic" in all_tech
    assert "Neo4j" in all_tech
    title_items = [it for it in items if "title" in it.field_candidates]
    assert title_items


def test_timeline_on_slide_one(telegram_extraction: ExtractionResult) -> None:
    inventory = SourceInventoryBuilder().build(telegram_extraction)
    items = EvidenceExtractor().extract(telegram_extraction, inventory)
    slide1 = next(it for it in items if it.location_index == 1)
    assert slide1.dates
    assert "01.09" in slide1.dates[0] or "30.11" in slide1.dates[0]
