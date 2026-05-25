"""Tests for StyledHtmlExporter."""

from pathlib import Path
from uuid import uuid4

import pytest

from app.models.domain import utc_now
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.schemas.landing_contract import ContractStatus, LandingContract
from app.services.analysis.contract_builder import ContractBuilderService
from app.services.export.styled_html_exporter import StyledHtmlExporter

FIXTURE = Path(__file__).parent / "fixtures" / "endocrinology_landing.txt"


class _FakeRepo:
    def __init__(self, contract: LandingContract) -> None:
        self._contract = contract
        self._landing = None

    async def get_contract(self, _pid):
        return self._contract

    async def get_landing(self, _pid):
        return self._landing


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
    builder = ContractBuilderService.__new__(ContractBuilderService)
    from app.services.contract_fidelity.completeness_gate import ContractCompletenessGate
    from app.services.contract_fidelity.landing_document_detector import LandingDocumentDetector
    from app.services.contract_fidelity.structured_landing_parser import StructuredLandingParser

    builder._detector = LandingDocumentDetector()
    builder._structured_parser = StructuredLandingParser()
    builder._completeness_gate = ContractCompletenessGate()
    return builder.build(extraction)


@pytest.mark.asyncio
async def test_styled_export_contains_modules(endocrinology_contract) -> None:
    exporter = StyledHtmlExporter(_FakeRepo(endocrinology_contract))
    html = await exporter.to_html(endocrinology_contract.project_id)
    assert "GlaucoLogic" in html
    assert "Copilot врача" in html
    assert "VitaCalc" in html


@pytest.mark.asyncio
async def test_styled_export_has_css_and_team(endocrinology_contract) -> None:
    exporter = StyledHtmlExporter(_FakeRepo(endocrinology_contract))
    html = await exporter.to_html(endocrinology_contract.project_id)
    assert "team-card" in html
    assert "stack-tag" in html
    assert "@media" in html
    assert "max-width: 1200px" in html


@pytest.mark.asyncio
async def test_styled_export_no_contract_fallback() -> None:
    repo = _FakeRepo(
        LandingContract(
            project_id=uuid4(),
            status=ContractStatus.DRAFT,
            updated_at=utc_now(),
        )
    )
    html = await StyledHtmlExporter(repo).to_html(uuid4())
    assert "<html" in html
