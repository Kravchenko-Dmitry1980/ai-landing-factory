"""Regression: contract API exposes structured fidelity fields."""

from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.domain import utc_now
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.schemas.landing_contract import ContractStatus, LandingContract
from app.services.analysis.contract_builder import ContractBuilderService

FIXTURE = Path(__file__).parent / "fixtures" / "endocrinology_landing.txt"


@pytest.fixture
def endocrinology_contract() -> LandingContract:
    text = FIXTURE.read_text(encoding="utf-8")
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
    builder = ContractBuilderService.__new__(ContractBuilderService)
    from app.services.contract_fidelity.completeness_gate import ContractCompletenessGate
    from app.services.contract_fidelity.landing_document_detector import LandingDocumentDetector
    from app.services.contract_fidelity.structured_landing_parser import StructuredLandingParser

    builder._detector = LandingDocumentDetector()
    builder._structured_parser = StructuredLandingParser()
    builder._completeness_gate = ContractCompletenessGate()
    return builder.build(extraction)


def test_contract_response_includes_fidelity_structured_fields(
    endocrinology_contract: LandingContract,
) -> None:
    """Serialized contract must expose modules, team_structured, tech_stack_grouped."""
    data = endocrinology_contract.model_dump(mode="json")
    fidelity = data.get("fidelity") or {}
    assert fidelity.get("modules"), "expected fidelity.modules"
    names = {m["name"] for m in fidelity["modules"]}
    assert "GlaucoLogic" in names
    assert len(fidelity.get("team_structured") or []) >= 15
    assert len(fidelity.get("tech_stack_grouped") or {}) >= 5


def test_get_contract_route_returns_fidelity(monkeypatch, endocrinology_contract) -> None:
    """GET /contract returns fidelity when repository has structured contract."""

    class _FakeRepo:
        async def get_contract(self, _pid):
            return endocrinology_contract

    from app.api.v1 import projects

    monkeypatch.setattr(projects, "get_contract_repository", lambda: _FakeRepo())

    client = TestClient(app)
    response = client.get(f"/api/v1/projects/{endocrinology_contract.project_id}/contract")
    assert response.status_code == 200, response.text
    body = response.json()
    fidelity = body.get("fidelity") or {}
    assert len(fidelity.get("modules") or []) >= 3
    assert len(fidelity.get("team_structured") or []) >= 15
    assert len(fidelity.get("tech_stack_grouped") or {}) >= 5
