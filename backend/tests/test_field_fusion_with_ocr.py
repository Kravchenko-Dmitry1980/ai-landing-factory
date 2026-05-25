"""Field fusion picks team from OCR derivative source."""

from __future__ import annotations

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
from app.services.orchestration.document_orchestrator import DocumentOrchestrator


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
    from app.services.ocr.ocr_enrichment import OcrEnrichmentService

    builder._ocr_enrichment = OcrEnrichmentService()
    return builder


def test_fusion_uses_ocr_team_source() -> None:
    pptx_text = "Slide 1:\nЦель проекта\n\nSlide 2:\nАрхитектура системы"
    ocr_text = (
        "Slide 25:\n"
        "Команда проекта\n"
        "Тимлид: Кравченко Дмитрий\n"
        "Помощник тимлида: Смирнова Анна\n"
        "Участники: Иванов Иван, Петров Петр"
    )
    extraction = ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[
            FileExtraction(
                filename="01_presentation.pptx",
                file_type="pptx",
                extracted_text=pptx_text,
                metadata={"slides_count": 25},
            ),
            FileExtraction(
                filename="01_presentation.pptx#ocr-slide-25",
                file_type="ocr",
                extracted_text=ocr_text,
                metadata={
                    "is_ocr_derivative": True,
                    "source_role": "supporting_visual_evidence",
                    "source_filename": "01_presentation.pptx",
                    "page_or_slide": 25,
                    "ocr_engine": "tesseract",
                },
            ),
        ],
        extracted_at=utc_now(),
    )
    contract = _make_builder().build(extraction)
    names = {m.name for m in (contract.fidelity.team_structured or [])}
    assert "Кравченко Дмитрий" in names

    traces = contract.fidelity.field_sources or []
    team_traces = [t for t in traces if t.field_name == "team"]
    assert any("ocr-slide-25" in t.source_filename for t in team_traces)
