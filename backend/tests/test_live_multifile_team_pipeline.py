"""Live multifile team pipeline: service-level acceptance without HTTP."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

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
from app.services.contract_fidelity.structured_landing_parser import StructuredLandingParser
from app.services.evidence.evidence_visibility import EvidenceVisibilityBuilder
from app.services.evidence.multi_source_assembler import MultiSourceEvidenceAssembler
from app.services.evidence.source_inventory import SourceInventoryBuilder
from app.services.fusion.field_fusion_engine import FieldFusionEngine
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

FORBIDDEN_TEAM_NAMES = (
    "Посты Telegram",
    "Из Telegram",
    "Qdrant Cloud",
    "Google Colab",
)

MIN_TEAM = 10


def _make_builder() -> ContractBuilderService:
    builder = ContractBuilderService.__new__(ContractBuilderService)
    builder._detector = LandingDocumentDetector()
    builder._source_type_detector = SourceTypeDetector()
    builder._structured_parser = StructuredLandingParser()
    builder._presentation_synthesizer = PresentationLandingSynthesizer()
    builder._completeness_gate = ContractCompletenessGate()
    builder._inventory_builder = SourceInventoryBuilder()
    builder._multi_source_assembler = MultiSourceEvidenceAssembler()
    builder._field_fusion_engine = FieldFusionEngine()
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


def test_live_multifile_team_pipeline_contract() -> None:
    contract = _make_builder().build(_indlab_extraction())
    assert contract.fidelity is not None
    assert contract.fidelity.source_count == 2
    assert contract.fidelity.parser_mode == "field_level_fusion"
    assert len(contract.fidelity.team_structured) >= MIN_TEAM

    report = EvidenceVisibilityBuilder().build(contract)
    team_view = report.field_sources.get("team")
    assert team_view is not None
    assert team_view.coverage in ("strong", "weak")


def test_live_multifile_team_pipeline_export() -> None:
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

    exporter = StyledHtmlExporter(ContractRepository(settings))
    html = exporter._render_from_contract(contract, landing, ExportTheme.UNIVERSITY_PLATFORM)
    assert "id='team'" in html or 'id="team"' in html
    assert "team-card" in html
    for forbidden in FORBIDDEN_TEAM_NAMES:
        assert f"<h3>{forbidden}</h3>" not in html


def test_presentation_only_team_missing_in_export() -> None:
    pres = INDLAB_PRES.read_text(encoding="utf-8")
    extraction = ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[
            FileExtraction(
                filename="01_presentation.pptx",
                file_type="pptx",
                extracted_text=pres,
                metadata={"slides_count": pres.count("Slide ")},
            ),
        ],
        extracted_at=utc_now(),
    )
    contract = _make_builder().build(extraction)
    team = contract.fidelity.team_structured if contract.fidelity else []
    assert len(team) < MIN_TEAM

    report = EvidenceVisibilityBuilder().build(contract)
    team_view = report.field_sources.get("team")
    assert team_view is not None
    assert team_view.coverage in ("missing", "weak")

    exporter = StyledHtmlExporter(ContractRepository(settings))
    html = exporter._render_from_contract(contract, None, ExportTheme.UNIVERSITY_PLATFORM)
    assert "id='team'" not in html and 'id="team"' not in html
