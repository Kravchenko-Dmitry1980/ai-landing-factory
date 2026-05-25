"""Source role priority tests for multi-source assembly."""

from __future__ import annotations

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
from app.services.evidence.multi_source_assembler import MultiSourceEvidenceAssembler
from app.services.evidence.source_inventory import SourceInventoryBuilder

ENDO_LANDING = Path(__file__).parent / "fixtures" / "endocrinology_landing.txt"
GLAUCO_PPTX = Path(__file__).parent / "fixtures" / "glauco_module_presentation.txt"
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


def test_primary_ready_landing_gets_primary_project_doc_role() -> None:
    text = ENDO_LANDING.read_text(encoding="utf-8")
    extraction = _extraction(("01_landing.docx", "docx", text))
    inventory = SourceInventoryBuilder().build(extraction)
    primary = [s for s in inventory if s.source_role == "primary_project_doc"]
    assert len(primary) == 1
    assert primary[0].filename == "01_landing.docx"


def test_module_presentation_role_when_name_matches_primary_modules() -> None:
    landing = ENDO_LANDING.read_text(encoding="utf-8")
    glauco = GLAUCO_PPTX.read_text(encoding="utf-8")
    extraction = _extraction(
        ("01_landing.docx", "docx", landing),
        ("02_glaucologic_presentation.pptx", "pptx", glauco),
    )
    inventory = SourceInventoryBuilder().build(extraction)
    roles = {s.filename: s.source_role for s in inventory}
    assert roles["01_landing.docx"] == "primary_project_doc"
    assert roles["02_glaucologic_presentation.pptx"] == "module_presentation"


def test_module_presentation_does_not_override_project_title() -> None:
    landing = ENDO_LANDING.read_text(encoding="utf-8")
    glauco = GLAUCO_PPTX.read_text(encoding="utf-8")
    contract = _make_builder().build(
        _extraction(
            ("01_landing.docx", "docx", landing),
            ("02_glaucologic_presentation.pptx", "pptx", glauco),
        )
    )
    assert contract.title
    assert "Эндокринология" in contract.title
    assert "GlaucoLogic" not in (contract.title or "")


def test_endocrinology_multi_source_preserves_modules_and_completeness() -> None:
    landing = ENDO_LANDING.read_text(encoding="utf-8")
    glauco = GLAUCO_PPTX.read_text(encoding="utf-8")
    contract = _make_builder().build(
        _extraction(
            ("01_landing.docx", "docx", landing),
            ("02_glaucologic_presentation.pptx", "pptx", glauco),
        )
    )
    assert contract.fidelity
    assert contract.fidelity.parser_mode == "field_level_fusion"
    assert contract.fidelity.completeness
    assert contract.fidelity.completeness.score >= 85
    module_names = " ".join(m.name for m in contract.fidelity.modules).lower()
    assert "glauco" in module_names
    assert "copilot" in module_names
    assert "vitacalc" in module_names


def test_supporting_presentation_still_wins_title_without_primary_doc() -> None:
    text = TELEGRAM_FIXTURE.read_text(encoding="utf-8")
    extraction = _extraction(("01_presentation.pptx", "pptx", text))
    inventory = SourceInventoryBuilder().build(extraction)
    assert inventory[0].source_role == "supporting_presentation"
    contract = _make_builder().build(extraction)
    assert contract.fidelity
    assert contract.fidelity.completeness
    assert contract.fidelity.completeness.score >= 75
    assert "Интеллектуальный" in (contract.title or "")
