"""Multi-source assembly integration tests."""

from pathlib import Path
from uuid import uuid4

import pytest

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
from app.services.evidence.field_candidates import is_generic_title

TELEGRAM_FIXTURE = Path(__file__).parent / "fixtures" / "telegram_analytics_presentation.txt"
KSK_FIXTURE = Path(__file__).parent / "fixtures" / "ksk_it_presentation.txt"
ENDO_FIXTURE = Path(__file__).parent / "fixtures" / "endocrinology_landing.txt"


def _make_builder() -> ContractBuilderService:
    builder = ContractBuilderService.__new__(ContractBuilderService)
    builder._detector = LandingDocumentDetector()
    builder._source_type_detector = SourceTypeDetector()
    builder._structured_parser = StructuredLandingParser()
    builder._presentation_synthesizer = PresentationLandingSynthesizer()
    builder._completeness_gate = ContractCompletenessGate()
    from app.services.evidence.multi_source_assembler import MultiSourceEvidenceAssembler
    from app.services.evidence.source_inventory import SourceInventoryBuilder

    builder._inventory_builder = SourceInventoryBuilder()
    builder._multi_source_assembler = MultiSourceEvidenceAssembler()
    return builder


def _extraction(text: str, filename: str, file_type: str, extra_files=None):
    files = [
        FileExtraction(
            filename=filename,
            file_type=file_type,
            extracted_text=text,
            metadata={"slides_count": text.count("Slide ")},
        )
    ]
    if extra_files:
        files.extend(extra_files)
    return ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=files,
        extracted_at=utc_now(),
    )


def test_telegram_analytics_completeness() -> None:
    text = TELEGRAM_FIXTURE.read_text(encoding="utf-8")
    extraction = _extraction(text, "Proekt.pptx", "pptx")
    contract = _make_builder().build(extraction)
    assert contract.fidelity
    assert contract.fidelity.parser_mode == "multi_source_assembly"
    assert contract.title
    assert not is_generic_title(contract.title)
    assert "Интеллектуальный агрегатор" in contract.title
    assert contract.timeline
    essence = next(b for b in contract.blocks if b.key == "essence")
    assert len(essence.content) >= 300
    tasks = next(b for b in contract.blocks if b.key == "tasks")
    task_text = " ".join(tasks.bullets).lower()
    assert "qdrant" in task_text or "семантический" in task_text
    assert contract.fidelity.completeness
    assert contract.fidelity.completeness.score >= 75
    stack = contract.fidelity.tech_stack_grouped
    flat = [t.lower() for vals in stack.values() for t in vals]
    assert any("qdrant" in t for t in flat)
    assert any("bertopic" in t for t in flat)
    assert any("neo4j" in t for t in flat)


def test_ksk_regression_completeness() -> None:
    text = KSK_FIXTURE.read_text(encoding="utf-8")
    contract = _make_builder().build(_extraction(text, "КСК_ИТ.pptx", "pptx"))
    assert contract.fidelity and contract.fidelity.completeness
    assert contract.fidelity.completeness.score >= 80
    assert len(contract.fidelity.modules) >= 5
    flat = [t.lower() for vals in contract.fidelity.tech_stack_grouped.values() for t in vals]
    assert any("yolo" in t for t in flat)
    assert any("streamlit" in t for t in flat)


def test_endocrinology_structured_path() -> None:
    text = ENDO_FIXTURE.read_text(encoding="utf-8")
    contract = _make_builder().build(
        _extraction(text, "Ленд проекта Эндокринология.docx", "docx")
    )
    assert contract.fidelity
    assert contract.fidelity.parser_mode == "structured"
    assert contract.fidelity.completeness
    assert contract.fidelity.completeness.score >= 85


def test_telegram_with_aux_txt_still_multi_source() -> None:
    text = TELEGRAM_FIXTURE.read_text(encoding="utf-8")
    extraction = _extraction(
        text,
        "Proekt.pptx",
        "pptx",
        extra_files=[
            FileExtraction(
                filename="description.txt",
                file_type="txt",
                extracted_text="телеграм",
                metadata={},
            )
        ],
    )
    contract = _make_builder().build(extraction)
    assert contract.fidelity.parser_mode == "multi_source_assembly"
    assert contract.title and "Интеллектуальный" in contract.title
