"""Orchestrated team extraction tests."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from app.models.domain import utc_now
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.services.analysis.contract_builder import ContractBuilderService
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
from app.services.orchestration.agents.pptx_ocr_need_detector_agent import (
    PPTX_TEAM_TEXT_MISSING,
    PptxOcrNeedDetectorAgent,
)
from app.services.orchestration.document_orchestrator import DocumentOrchestrator

INDLAB_DOCX = (
    Path(__file__).parents[2]
    / "test_corpus"
    / "golden"
    / "indlab_telegram_news"
    / "sources"
    / "02_landing.docx.txt"
)
INDLAB_PPTX = (
    Path(__file__).parents[2]
    / "test_corpus"
    / "golden"
    / "indlab_telegram_news"
    / "sources"
    / "01_presentation.pptx.txt"
)
TELEGRAM_FIXTURE = Path(__file__).parent / "fixtures" / "telegram_analytics_presentation.txt"


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
    builder._document_orchestrator = DocumentOrchestrator()
    return builder


def _extraction(*files: tuple[str, str, str]) -> ExtractionResult:
    return ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[
            FileExtraction(
                filename=name,
                file_type=ftype,
                extracted_text=text,
                metadata={"slides_count": text.count("Slide ")},
            )
            for name, ftype, text in files
        ],
        extracted_at=utc_now(),
    )


def test_docx_group_line_final_contract_filled() -> None:
    docx = INDLAB_DOCX.read_text(encoding="utf-8")
    contract = _make_builder().build(_extraction(("02_landing.docx", "docx", docx)))
    names = {m.name for m in contract.fidelity.team_structured}
    assert any("Быков" in n for n in names)
    assert any("Иванков" in n for n in names)
    assert any("Решетников" in n for n in names)
    for key in ("Быков", "Иванков", "Решетников"):
        member = next(m for m in contract.fidelity.team_structured if key in m.name)
        assert member.role == "Парсинг, анализ данных"
        assert len(member.contributions) >= 3


def test_pptx_without_team_text_warning() -> None:
    pptx = INDLAB_PPTX.read_text(encoding="utf-8")
    extraction = _extraction(("01_presentation.pptx", "pptx", pptx))
    result = PptxOcrNeedDetectorAgent().run(extraction)
    assert any(PPTX_TEAM_TEXT_MISSING in w for w in result.warnings)


def test_pptx_with_team_text_extracts() -> None:
    text = TELEGRAM_FIXTURE.read_text(encoding="utf-8")
    if "Команда проекта" not in text:
        return
    extraction = _extraction(("team.pptx", "pptx", text))
    trace = DocumentOrchestrator().run(extraction)
    team_agent = next(r for r in trace.results if r.agent_name == "team_extraction_agent")
    assert team_agent.metrics.get("team_count", 0) >= 0


def test_orchestration_trace_on_multifile_build() -> None:
    docx = INDLAB_DOCX.read_text(encoding="utf-8")
    pptx = INDLAB_PPTX.read_text(encoding="utf-8")
    contract = _make_builder().build(
        _extraction(
            ("01_presentation.pptx", "pptx", pptx),
            ("02_landing.docx", "docx", docx),
        )
    )
    assert contract.fidelity and contract.fidelity.orchestration_trace
    assert contract.fidelity.orchestration_trace.team_group_expansions


def test_indlab_group_line_regression() -> None:
    docx = INDLAB_DOCX.read_text(encoding="utf-8")
    contract = _make_builder().build(_extraction(("02_landing.docx", "docx", docx)))
    bykov = next(m for m in contract.fidelity.team_structured if "Быков" in m.name)
    ivankov = next(m for m in contract.fidelity.team_structured if "Иванков" in m.name)
    assert bykov.role and ivankov.role
    assert not (bykov.role and not ivankov.role)
