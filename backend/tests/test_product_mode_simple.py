"""Product mode (Stage P.1) configuration and evidence UX tests."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.config import Settings
from app.models.domain import utc_now
from app.product_mode import (
    OCR_ENABLED_IN_SIMPLE_WARNING,
    SIMPLE_IMAGE_ONLY_HINT,
    collect_product_mode_warnings,
    sanitize_user_message,
)
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.schemas.landing_contract import LandingContract
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


def test_default_product_mode_is_simple() -> None:
    s = Settings(product_mode="simple")
    assert s.normalized_product_mode == "simple"
    assert s.is_simple_product
    assert not s.effective_advanced_visual_pipeline


def test_simple_mode_disables_advanced_pipeline() -> None:
    s = Settings(product_mode="simple", advanced_visual_pipeline=True)
    assert s.advanced_visual_pipeline is False
    assert not s.effective_advanced_visual_pipeline


def test_explicit_ocr_in_simple_warns_not_crash() -> None:
    s = Settings(product_mode="simple", ocr_enabled=True)
    warnings = collect_product_mode_warnings(s)
    assert OCR_ENABLED_IN_SIMPLE_WARNING in warnings
    assert s.ocr_enabled is True


def test_contract_builder_without_ocr_deps() -> None:
    text = "Суть проекта\nОписание.\n\nКоманда проекта\nИванов Иван — тимлид"
    extraction = ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[
            FileExtraction(
                filename="doc.txt",
                file_type="txt",
                extracted_text=text,
            )
        ],
        extracted_at=utc_now(),
    )
    contract = _make_builder().build(extraction)
    assert contract.blocks


def test_evidence_hides_advanced_diagnostics_in_simple(
    multi_source_contract: LandingContract,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.services.evidence.evidence_visibility.settings",
        Settings(product_mode="simple", enable_advanced_diagnostics=False),
    )
    report = EvidenceVisibilityBuilder().build(multi_source_contract)
    assert report.advanced_diagnostics_enabled is False
    assert report.vlm_extraction_summary == []
    assert report.visual_evidence_summary == []
    payload = report.model_dump_json().lower()
    assert "paddleocr" not in payload
    assert "tesseract" not in payload


def test_image_only_warning_user_facing() -> None:
    raw = "Файл deck.pptx похож на image-only. Для анализа нужен OCR или текст."
    cleaned = sanitize_user_message(raw, advanced=False)
    assert "OCR" not in cleaned
    assert "изображение" in cleaned or "DOCX" in cleaned
    assert cleaned == SIMPLE_IMAGE_ONLY_HINT


def test_advanced_mode_exposes_diagnostics(
    multi_source_contract: LandingContract,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PRODUCT_MODE", "advanced")
    monkeypatch.setenv("ENABLE_ADVANCED_DIAGNOSTICS", "true")
    advanced_settings = Settings()
    monkeypatch.setattr(
        "app.services.evidence.evidence_visibility.settings",
        advanced_settings,
    )
    assert advanced_settings.show_advanced_diagnostics is True
    report = EvidenceVisibilityBuilder().build(multi_source_contract)
    assert report.advanced_diagnostics_enabled is True


@pytest.fixture
def multi_source_contract() -> LandingContract:
    from pathlib import Path

    endo = Path(__file__).parent / "fixtures" / "endocrinology_landing.txt"
    glauco = Path(__file__).parent / "fixtures" / "glauco_module_presentation.txt"
    extraction = ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[
            FileExtraction(
                filename="01_landing.docx",
                file_type="docx",
                extracted_text=endo.read_text(encoding="utf-8"),
            ),
            FileExtraction(
                filename="02_glaucologic_presentation.pptx",
                file_type="pptx",
                extracted_text=glauco.read_text(encoding="utf-8"),
            ),
        ],
        extracted_at=utc_now(),
    )
    return _make_builder().build(extraction)
