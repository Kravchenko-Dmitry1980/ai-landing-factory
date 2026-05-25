"""Tests for university_platform HTML export theme."""

from pathlib import Path
from uuid import uuid4

import pytest

from app.models.domain import utc_now
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.services.analysis.contract_builder import ContractBuilderService
from app.services.export.export_theme import ExportTheme
from app.services.export.html_bullet_utils import normalize_bullet
from app.services.export.styled_html_exporter import StyledHtmlExporter
from tests.test_styled_html_exporter import FIXTURE, _FakeRepo


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
async def test_university_export_light_theme(endocrinology_contract) -> None:
    exporter = StyledHtmlExporter(_FakeRepo(endocrinology_contract))
    html = await exporter.to_html(
        endocrinology_contract.project_id,
        theme=ExportTheme.UNIVERSITY_PLATFORM,
    )
    assert "#ffffff" in html or "--bg: #ffffff" in html
    assert "#7C3AED" in html
    assert "border-bottom" in html
    assert "GlaucoLogic" in html
    assert "Copilot врача" in html
    assert "VitaCalc" in html
    assert "team-card" in html
    assert "stack-tag" in html
    assert "max-width: 1200px" in html


@pytest.mark.asyncio
async def test_university_export_no_dark_markers(endocrinology_contract) -> None:
    exporter = StyledHtmlExporter(_FakeRepo(endocrinology_contract))
    html = await exporter.to_html(
        endocrinology_contract.project_id,
        theme=ExportTheme.UNIVERSITY_PLATFORM,
    )
    assert "--bg: #0f1419" not in html
    assert "--surface: #1a2332" not in html
    assert "max-width:720px" not in html
    assert "max-width: 720px" not in html
    assert "Project Landing" not in html


@pytest.mark.asyncio
async def test_enterprise_dark_export_unchanged(endocrinology_contract) -> None:
    exporter = StyledHtmlExporter(_FakeRepo(endocrinology_contract))
    html = await exporter.to_html(
        endocrinology_contract.project_id,
        theme=ExportTheme.ENTERPRISE_DARK,
    )
    assert "--bg: #0f1419" in html
    assert "--surface: #1a2332" in html
    assert "GlaucoLogic" in html


def test_normalize_bullet_strips_duplicate_markers() -> None:
    assert normalize_bullet("● ● Some task") == "Some task"
    assert normalize_bullet("• item") == "item"
    assert normalize_bullet("- item") == "item"
