"""Integration tests: team false positive guard."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from app.config import settings
from app.models.domain import utc_now
from app.repositories.contract_repository import ContractRepository
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.services.analysis.contract_builder import ContractBuilderService
from app.services.contract_fidelity.completeness_gate import ContractCompletenessGate
from app.services.contract_fidelity.landing_document_detector import LandingDocumentDetector
from app.services.contract_fidelity.presentation_landing_synthesizer import (
    PresentationLandingSynthesizer,
)
from app.services.contract_fidelity.source_type_detector import SourceTypeDetector
from app.services.contract_fidelity.structured_landing_parser import StructuredLandingParser
from app.services.evidence.evidence_visibility import EvidenceVisibilityBuilder
from app.services.evidence.multi_source_assembler import MultiSourceEvidenceAssembler
from app.services.evidence.source_inventory import SourceInventoryBuilder
from app.services.export.styled_html_exporter import ExportTheme, StyledHtmlExporter

INDLAB_LANDING = (
    Path(__file__).parents[2]
    / "test_corpus"
    / "golden"
    / "indlab_telegram_news"
    / "sources"
    / "02_landing.docx.txt"
)
INDLAB_PRES = (
    Path(__file__).parents[2]
    / "test_corpus"
    / "golden"
    / "indlab_telegram_news"
    / "sources"
    / "01_presentation.pptx.txt"
)

FORBIDDEN_TEAM_NAMES = (
    "Посты Telegram",
    "Из Telegram",
    "Схема обработки данных",
    "Векторная БД",
)


def _make_builder() -> ContractBuilderService:
    builder = ContractBuilderService.__new__(ContractBuilderService)
    builder._detector = LandingDocumentDetector()
    builder._source_type_detector = SourceTypeDetector()
    builder._structured_parser = StructuredLandingParser()
    builder._presentation_synthesizer = PresentationLandingSynthesizer()
    builder._completeness_gate = ContractCompletenessGate()
    builder._inventory_builder = SourceInventoryBuilder()
    builder._multi_source_assembler = MultiSourceEvidenceAssembler()
    return builder


def _indlab_extraction() -> ExtractionResult:
    pres = INDLAB_PRES.read_text(encoding="utf-8")
    land = INDLAB_LANDING.read_text(encoding="utf-8")
    return ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[
            FileExtraction(
                filename="01_presentation.pptx",
                file_type="pptx",
                extracted_text=pres,
                metadata={"slides_count": pres.count("Slide ")},
            ),
            FileExtraction(
                filename="02_landing.docx",
                file_type="docx",
                extracted_text=land,
            ),
        ],
        extracted_at=utc_now(),
    )


def test_presentation_only_junk_does_not_create_team() -> None:
    text = """
Slide 1: Схема обработки данных
Посты Telegram
Из Telegram-постов мы строим единый корпус
Qdrant Cloud
BERTopic
Neo4j
"""
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
    contract = _make_builder().build(extraction)
    team = contract.fidelity.team_structured if contract.fidelity else []
    assert len(team) == 0

    exporter = StyledHtmlExporter(ContractRepository(settings))
    html = exporter._render_from_contract(contract, None, ExportTheme.UNIVERSITY_PLATFORM)
    assert "id='team'" not in html and 'id="team"' not in html

    report = EvidenceVisibilityBuilder().build(contract)
    team_view = report.field_sources.get("team")
    assert team_view is None or team_view.coverage in ("missing", "weak")


def test_indlab_real_team_without_false_positives() -> None:
    contract = _make_builder().build(_indlab_extraction())
    assert contract.fidelity
    team = contract.fidelity.team_structured
    names = [m.name for m in team]
    assert len(team) >= 10
    assert any("Кравченко" in n for n in names)
    for forbidden in FORBIDDEN_TEAM_NAMES:
        assert forbidden not in names

    exporter = StyledHtmlExporter(ContractRepository(settings))
    html = exporter._render_from_contract(contract, None, ExportTheme.UNIVERSITY_PLATFORM)
    assert "Команда проекта" in html
    assert "team-card" in html
    for forbidden in FORBIDDEN_TEAM_NAMES:
        assert f"<h3>{forbidden}</h3>" not in html
