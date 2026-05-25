"""Team visibility pipeline: extraction → contract → landing → export."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from app.config import settings
from app.models.domain import utc_now
from app.repositories.contract_repository import ContractRepository
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.schemas.semantic_generation import GeneratedSemanticLanding, SemanticGenerationMetadata
from app.services.analysis.contract_builder import ContractBuilderService
from app.services.contract_fidelity.completeness_gate import ContractCompletenessGate
from app.services.contract_fidelity.landing_document_detector import LandingDocumentDetector
from app.services.contract_fidelity.presentation_landing_synthesizer import (
    PresentationLandingSynthesizer,
)
from app.services.contract_fidelity.source_type_detector import SourceTypeDetector
from app.services.contract_fidelity.structured_landing_parser import (
    StructuredLandingParser,
    _split_sections,
)
from app.services.contract_fidelity.team_parser import parse_team_section
from app.services.evidence.evidence_visibility import EvidenceVisibilityBuilder
from app.services.evidence.multi_source_assembler import MultiSourceEvidenceAssembler
from app.services.evidence.people_extractor import extract_people_from_text
from app.services.evidence.source_inventory import SourceInventoryBuilder
from app.services.export.styled_html_exporter import ExportTheme, StyledHtmlExporter
from app.services.semantic.landing_bridge import semantic_to_landing

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


def test_team_extracted_from_docx_like_text() -> None:
    text = INDLAB_LANDING.read_text(encoding="utf-8")
    team_text = _split_sections(text.replace("\u00a0", " ").replace("\r\n", "\n")).get("team", "")
    members = parse_team_section(team_text)
    assert len(members) >= 10
    assert any("Кравченко" in m.name for m in members)


def test_team_extracted_from_presentation_metadata_line() -> None:
    text = "Тимлид: Дмитрий Кравченко\nSlide 1: intro"
    people = extract_people_from_text(text)
    assert any("Кравченко" in p.name for p in people)


def test_ready_landing_doc_team_wins_over_presentation() -> None:
    contract = _make_builder().build(_indlab_extraction())
    assert contract.fidelity
    team = contract.fidelity.team_structured
    assert len(team) >= 10
    assert any("Ерюкова" in m.name for m in team)
    assert not any(m.name.lower() == "qdrant" for m in team)


def test_contract_with_team_produces_generated_landing_team_block() -> None:
    contract = _make_builder().build(_indlab_extraction())
    landing = semantic_to_landing(
        GeneratedSemanticLanding(
            project_id=contract.project_id,
            sections=[],
            metadata=SemanticGenerationMetadata(prompt_version="test"),
        ),
        contract,
    )
    team_block = next(b for b in landing.blocks if b.key == "team")
    assert team_block.bullets or contract.fidelity.team_structured


def test_styled_html_exporter_renders_team_card() -> None:
    contract = _make_builder().build(_indlab_extraction())
    exporter = StyledHtmlExporter(ContractRepository(settings))
    html = exporter._render_from_contract(contract, None, ExportTheme.UNIVERSITY_PLATFORM)
    assert "Команда проекта" in html
    assert "team-card" in html
    assert "id='team'" in html or 'id="team"' in html


def test_indlab_corpus_requires_team() -> None:
    contract = _make_builder().build(_indlab_extraction())
    assert contract.fidelity
    assert len(contract.fidelity.team_structured) >= 10


def test_evidence_report_marks_team_when_absent() -> None:
    extraction = ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[
            FileExtraction(
                filename="deck.pptx",
                file_type="pptx",
                extracted_text="Slide 1: Цель проекта\nСистема аналитики",
                metadata={"slides_count": 1},
            )
        ],
        extracted_at=utc_now(),
    )
    contract = _make_builder().build(extraction)
    report = EvidenceVisibilityBuilder().build(contract)
    team_view = report.field_sources.get("team")
    assert not contract.fidelity or len(contract.fidelity.team_structured) == 0
    assert team_view is not None
    assert team_view.coverage == "missing"
