"""Tests for PPTX project presentation → LandingContract synthesis."""

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

FIXTURE = Path(__file__).parent / "fixtures" / "ksk_it_presentation.txt"
ENDO_FIXTURE = Path(__file__).parent / "fixtures" / "endocrinology_landing.txt"


def _make_builder() -> ContractBuilderService:
    builder = ContractBuilderService.__new__(ContractBuilderService)
    builder._detector = LandingDocumentDetector()
    builder._source_type_detector = SourceTypeDetector()
    builder._structured_parser = StructuredLandingParser()
    builder._presentation_synthesizer = PresentationLandingSynthesizer()
    builder._completeness_gate = ContractCompletenessGate()
    return builder


@pytest.fixture
def ksk_text() -> str:
    return FIXTURE.read_text(encoding="utf-8")


@pytest.fixture
def ksk_extraction(ksk_text: str) -> ExtractionResult:
    return ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[
            FileExtraction(
                filename="КСК_ИТ.pptx",
                file_type="pptx",
                extracted_text=ksk_text,
                metadata={"slides_count": 19},
            )
        ],
        extracted_at=utc_now(),
    )


@pytest.fixture
def ksk_contract(ksk_extraction: ExtractionResult):
    return _make_builder().build(ksk_extraction)


def test_source_type_project_presentation(ksk_text: str) -> None:
    result = SourceTypeDetector().detect(ksk_text, file_type="pptx")
    assert result.source_type == "project_presentation"
    assert result.confidence >= 0.6


def test_parser_mode_project_presentation(ksk_contract) -> None:
    assert ksk_contract.fidelity is not None
    assert ksk_contract.fidelity.parser_mode == "project_presentation"


def test_title_and_client(ksk_contract) -> None:
    assert ksk_contract.title
    assert "Автоматизация открытия шлагбаума" in ksk_contract.title
    assert ksk_contract.client
    assert "КСК ИТ" in ksk_contract.client


def test_essence_length(ksk_contract) -> None:
    essence = next(b for b in ksk_contract.blocks if b.key == "essence")
    assert len(essence.content) > 300


def test_tasks_count(ksk_contract) -> None:
    tasks = next(b for b in ksk_contract.blocks if b.key == "tasks").bullets
    assert len(tasks) >= 5


def test_purpose_count(ksk_contract) -> None:
    purpose = next(b for b in ksk_contract.blocks if b.key == "purpose").bullets
    assert len(purpose) >= 4


def test_inputs_count(ksk_contract) -> None:
    inputs = next(b for b in ksk_contract.blocks if b.key == "inputs").bullets
    assert len(inputs) >= 4


def test_outputs_count(ksk_contract) -> None:
    outputs = next(b for b in ksk_contract.blocks if b.key == "outputs").bullets
    assert len(outputs) >= 4


def test_results_count(ksk_contract) -> None:
    results = next(b for b in ksk_contract.blocks if b.key == "results").bullets
    assert len(results) >= 4


def test_outlook_count(ksk_contract) -> None:
    outlook = next(b for b in ksk_contract.blocks if b.key == "outlook").bullets
    assert len(outlook) >= 3


def test_tech_stack_keywords(ksk_contract) -> None:
    grouped = ksk_contract.fidelity.tech_stack_grouped if ksk_contract.fidelity else {}
    flat = " ".join(item for items in grouped.values() for item in items).lower()
    for token in ("yolov8", "streamlit", "cvat", "roboflow"):
        assert token in flat


def test_modules_pipeline(ksk_contract) -> None:
    modules = [m.name for m in (ksk_contract.fidelity.modules if ksk_contract.fidelity else [])]
    expected = (
        "Обнаружение автомобиля",
        "Идентификация спецтранспорта",
        "Обнаружение номера автомобиля",
        "Распознавание символов номера",
        "Проверка номера в базе данных",
    )
    for name in expected:
        assert any(name.lower() in m.lower() for m in modules), f"missing module {name}"


def test_team_members(ksk_contract) -> None:
    team = ksk_contract.fidelity.team_structured if ksk_contract.fidelity else []
    names = [m.name for m in team]
    assert any("Бугров Алексей" in n for n in names)
    assert any("Кравченко Дмитрий" in n for n in names)


def test_completeness_score(ksk_contract) -> None:
    report = ksk_contract.fidelity.completeness if ksk_contract.fidelity else None
    assert report is not None
    assert report.score >= 80


def test_contract_builder_chooses_presentation_synthesizer(ksk_extraction) -> None:
    contract = _make_builder().build(ksk_extraction)
    assert contract.fidelity.parser_mode == "project_presentation"


def test_endocrinology_still_structured() -> None:
    text = ENDO_FIXTURE.read_text(encoding="utf-8")
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
    contract = _make_builder().build(extraction)
    assert contract.fidelity.parser_mode == "structured"
