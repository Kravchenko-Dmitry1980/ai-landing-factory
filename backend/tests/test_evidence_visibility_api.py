"""Evidence visibility API tests."""

from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.domain import utc_now
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

ENDO_LANDING = Path(__file__).parent / "fixtures" / "endocrinology_landing.txt"
GLAUCO_PPTX = Path(__file__).parent / "fixtures" / "glauco_module_presentation.txt"


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


def _multi_source_contract() -> LandingContract:
    landing = ENDO_LANDING.read_text(encoding="utf-8")
    glauco = GLAUCO_PPTX.read_text(encoding="utf-8")
    extraction = ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[
            FileExtraction(
                filename="01_landing.docx",
                file_type="docx",
                extracted_text=landing,
            ),
            FileExtraction(
                filename="02_glaucologic_presentation.pptx",
                file_type="pptx",
                extracted_text=glauco,
                metadata={"slides_count": glauco.count("Slide ")},
            ),
            FileExtraction(
                filename="03_ai_copilot_presentation.pptx",
                file_type="pptx",
                extracted_text="",
                metadata={"slides_count": 12},
            ),
        ],
        extracted_at=utc_now(),
    )
    return _make_builder().build(extraction)


@pytest.fixture
def multi_source_contract() -> LandingContract:
    return _multi_source_contract()


def test_evidence_report_returns_200(monkeypatch, multi_source_contract) -> None:
    class _FakeRepo:
        async def get_contract(self, _pid):
            return multi_source_contract

    from app.api.v1 import contracts

    monkeypatch.setattr(contracts, "get_contract_repository", lambda: _FakeRepo())

    client = TestClient(app)
    pid = multi_source_contract.project_id
    response = client.get(f"/api/v1/projects/{pid}/evidence-report")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["parser_mode"] == "multi_source_assembly"
    assert body["source_count"] == 3
    assert body["evidence_count"] > 0
    assert body["field_sources"]["title"]["coverage"] in ("strong", "weak", "missing")


def test_evidence_report_no_raw_huge_text(multi_source_contract) -> None:
    report = EvidenceVisibilityBuilder().build(multi_source_contract)
    payload = report.model_dump_json()
    assert len(payload) < 200_000
    for field in report.field_sources.values():
        for snippet in field.selected_snippets:
            assert len(snippet) <= 180


def test_evidence_report_includes_source_roles(multi_source_contract) -> None:
    report = EvidenceVisibilityBuilder().build(multi_source_contract)
    roles = {s.filename: s.source_role for s in report.sources}
    assert roles["01_landing.docx"] == "primary_project_doc"
    assert roles["02_glaucologic_presentation.pptx"] == "module_presentation"


def test_evidence_report_field_sources_title_modules_stack(multi_source_contract) -> None:
    report = EvidenceVisibilityBuilder().build(multi_source_contract)
    title = report.field_sources.get("title")
    assert title
    assert any("01_landing.docx" in ref for ref in title.source_refs + title.reasons) or (
        title.coverage == "strong"
    )
    modules = report.field_sources.get("modules")
    assert modules
    stack = report.field_sources.get("tech_stack")
    assert stack


def test_empty_source_gets_empty_status(multi_source_contract) -> None:
    report = EvidenceVisibilityBuilder().build(multi_source_contract)
    copilot = next(
        (s for s in report.sources if s.filename == "03_ai_copilot_presentation.pptx"),
        None,
    )
    assert copilot
    assert copilot.status == "empty"
    assert copilot.evidence_count == 0


def test_unknown_project_returns_404(monkeypatch) -> None:
    class _FakeRepo:
        async def get_contract(self, _pid):
            return None

    from app.api.v1 import contracts

    monkeypatch.setattr(contracts, "get_contract_repository", lambda: _FakeRepo())

    client = TestClient(app)
    response = client.get(f"/api/v1/projects/{uuid4()}/evidence-report")
    assert response.status_code == 404
