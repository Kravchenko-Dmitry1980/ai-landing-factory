"""Field-level multi-source fusion engine tests."""

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
from app.services.fusion.field_fusion_engine import FieldFusionEngine

REPO = Path(__file__).resolve().parents[2]
INDLAB_PPTX = REPO / "test_corpus" / "golden" / "indlab_telegram_news" / "sources" / "01_presentation.pptx.txt"
INDLAB_DOCX = REPO / "test_corpus" / "golden" / "indlab_telegram_news" / "sources" / "02_landing.docx.txt"
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
    builder._field_fusion_engine = FieldFusionEngine()
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


def test_team_from_docx_modules_from_pptx() -> None:
    pptx = INDLAB_PPTX.read_text(encoding="utf-8")
    docx = INDLAB_DOCX.read_text(encoding="utf-8")
    contract = _make_builder().build(
        _extraction(
            ("01_presentation.pptx", "pptx", pptx),
            ("02_landing.docx", "docx", docx),
        )
    )
    assert contract.fidelity
    assert contract.fidelity.parser_mode == "field_level_fusion"
    assert len(contract.fidelity.team_structured) >= 10
    assert len(contract.fidelity.modules) >= 3
    flat = [t.lower() for vals in contract.fidelity.tech_stack_grouped.values() for t in vals]
    assert any("qdrant" in t for t in flat)
    team_names = " ".join(m.name for m in contract.fidelity.team_structured).lower()
    assert "кравченко" in team_names
    module_names = " ".join(m.name for m in contract.fidelity.modules).lower()
    assert "qdrant" in module_names or "семант" in module_names


def test_title_primary_doc_wins() -> None:
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


def test_team_union_dedupe() -> None:
    landing = INDLAB_DOCX.read_text(encoding="utf-8")
    pptx = TELEGRAM_FIXTURE.read_text(encoding="utf-8")
    contract = _make_builder().build(
        _extraction(
            ("02_landing.docx", "docx", landing),
            ("01_presentation.pptx", "pptx", pptx),
        )
    )
    names = [m.name.lower() for m in contract.fidelity.team_structured]
    assert len(names) == len(set(names))
    assert len(names) >= 10


def test_tech_stack_union() -> None:
    pptx = TELEGRAM_FIXTURE.read_text(encoding="utf-8")
    docx = INDLAB_DOCX.read_text(encoding="utf-8")
    contract = _make_builder().build(
        _extraction(
            ("01_presentation.pptx", "pptx", pptx),
            ("02_landing.docx", "docx", docx),
        )
    )
    flat = [t.lower() for vals in contract.fidelity.tech_stack_grouped.values() for t in vals]
    assert any("qdrant" in t for t in flat)
    assert any("bertopic" in t for t in flat)
    assert any("postgres" in t or "python" in t for t in flat)


def test_no_false_team() -> None:
    pptx = TELEGRAM_FIXTURE.read_text(encoding="utf-8")
    contract = _make_builder().build(_extraction(("01_presentation.pptx", "pptx", pptx)))
    names = " ".join(m.name.lower() for m in (contract.fidelity.team_structured or []))
    assert "посты telegram" not in names
    assert "qdrant cloud" not in names
    assert "схема обработки данных" not in names


def test_modules_deduped_reasonable() -> None:
    pptx = TELEGRAM_FIXTURE.read_text(encoding="utf-8")
    contract = _make_builder().build(_extraction(("01_presentation.pptx", "pptx", pptx)))
    modules = contract.fidelity.modules if contract.fidelity else []
    assert len(modules) <= 12
    names = [m.name.lower() for m in modules]
    assert names.count("задачи проекта") == 0


def test_field_trace_created() -> None:
    pptx = INDLAB_PPTX.read_text(encoding="utf-8")
    docx = INDLAB_DOCX.read_text(encoding="utf-8")
    contract = _make_builder().build(
        _extraction(
            ("01_presentation.pptx", "pptx", pptx),
            ("02_landing.docx", "docx", docx),
        )
    )
    fidelity = contract.fidelity
    assert fidelity and fidelity.fusion_trace
    decisions = fidelity.field_decisions
    assert "title" in decisions
    assert "team" in decisions
    assert "modules" in decisions
    assert "tech_stack" in decisions


def test_source_fallback() -> None:
    docx = INDLAB_DOCX.read_text(encoding="utf-8")
    contract = _make_builder().build(_extraction(("02_landing.docx", "docx", docx)))
    assert contract.fidelity
    assert contract.fidelity.parser_mode == "structured"

    pptx = TELEGRAM_FIXTURE.read_text(encoding="utf-8")
    contract2 = _make_builder().build(_extraction(("01_presentation.pptx", "pptx", pptx)))
    assert contract2.fidelity
    assert contract2.fidelity.parser_mode in ("multi_source_assembly", "project_presentation")
