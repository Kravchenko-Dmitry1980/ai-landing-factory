"""Tests for ContractCompletenessGate."""

from pathlib import Path
from uuid import uuid4

import pytest

from app.models.domain import utc_now
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.services.analysis.contract_builder import ContractBuilderService
from app.services.contract_fidelity.completeness_gate import ContractCompletenessGate

FIXTURE = Path(__file__).parent / "fixtures" / "endocrinology_landing.txt"


@pytest.fixture
def endocrinology_contract():
    text = FIXTURE.read_text(encoding="utf-8")
    extraction = ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[
            FileExtraction(
                filename="Ленд проекта Эндокринология.docx",
                file_type="docx",
                extracted_text=text,
            )
        ],
        extracted_at=utc_now(),
    )
    from app.services.contract_fidelity.completeness_gate import ContractCompletenessGate
    from app.services.contract_fidelity.landing_document_detector import LandingDocumentDetector
    from app.services.contract_fidelity.structured_landing_parser import StructuredLandingParser

    builder = ContractBuilderService.__new__(ContractBuilderService)
    builder._detector = LandingDocumentDetector()
    builder._structured_parser = StructuredLandingParser()
    builder._completeness_gate = ContractCompletenessGate()
    return builder.build(extraction)


def test_completeness_score_high(endocrinology_contract) -> None:
    report = ContractCompletenessGate().evaluate(endocrinology_contract)
    assert report.score >= 85
    assert report.complete is True
    assert report.export_incomplete is False


def test_completeness_empty_contract() -> None:
    from app.schemas.landing_contract import ContractStatus, LandingContract

    contract = LandingContract(
        project_id=uuid4(),
        status=ContractStatus.DRAFT,
        updated_at=utc_now(),
    )
    report = ContractCompletenessGate().evaluate(contract)
    assert report.score < 70
    assert report.export_incomplete is True
