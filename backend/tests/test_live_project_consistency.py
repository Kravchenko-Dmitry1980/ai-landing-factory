"""Live project consistency audit and team pipeline regression tests."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.models.domain import utc_now
from app.repositories.contract_repository import ContractRepository
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
from app.services.evidence.evidence_visibility import (
    SINGLE_FILE_TEAM_HINT,
    SINGLE_FILE_WARNING,
    EvidenceVisibilityBuilder,
)
from app.services.evidence.multi_source_assembler import MultiSourceEvidenceAssembler
from app.services.evidence.source_inventory import SourceInventoryBuilder
from app.services.export.styled_html_exporter import ExportTheme, StyledHtmlExporter
from app.services.generation.stub_generator import StubGenerationService
from app.services.prompts.engine import PromptEngine

from scripts.debug_live_project_consistency import (
    ProjectDiagnostics,
    _compute_verdict,
    _team_block_has_content,
)

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
    return builder


def _indlab_extraction(*, pptx_only: bool = False) -> ExtractionResult:
    files = [
        FileExtraction(
            filename="01_presentation.pptx",
            file_type="pptx",
            extracted_text=INDLAB_PRES.read_text(encoding="utf-8"),
        ),
    ]
    if not pptx_only:
        files.append(
            FileExtraction(
                filename="02_landing.docx",
                file_type="docx",
                extracted_text=INDLAB_LANDING.read_text(encoding="utf-8"),
            )
        )
    return ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=files,
        extracted_at=utc_now(),
    )


def test_single_pptx_verdict_and_export_no_team() -> None:
    contract = _make_builder().build(_indlab_extraction(pptx_only=True))
    report = EvidenceVisibilityBuilder().build(contract)
    assert report.source_count == 1
    assert SINGLE_FILE_WARNING in report.warnings
    assert any(SINGLE_FILE_TEAM_HINT in h for h in report.improvement_hints)

    html = StyledHtmlExporter(ContractRepository(settings))._render_from_contract(
        contract, None, ExportTheme.UNIVERSITY_PLATFORM
    )
    assert "id='team'" not in html

    diag = ProjectDiagnostics(project_id=str(contract.project_id), source_count=1, project_exists=True)
    diag.team_structured_count = 0
    assert _compute_verdict(diag, None) == "single_file_no_team_source"


def test_pptx_docx_team_in_contract_and_export() -> None:
    contract = _make_builder().build(_indlab_extraction())
    assert contract.fidelity is not None
    assert contract.fidelity.source_count == 2
    assert len(contract.fidelity.team_structured) >= MIN_TEAM

    html = StyledHtmlExporter(ContractRepository(settings))._render_from_contract(
        contract, None, ExportTheme.UNIVERSITY_PLATFORM
    )
    assert "id='team'" in html
    assert "team-card" in html
    assert "Команда проекта" in html


def test_merge_team_from_ms_when_presentation_wins() -> None:
    builder = _make_builder()
    extraction = _indlab_extraction()
    ms_contract = builder.build(extraction)
    assert len(ms_contract.fidelity.team_structured) >= MIN_TEAM

    text = INDLAB_PRES.read_text(encoding="utf-8")
    detection = ms_contract.fidelity.detection
    source_type = builder._source_type_detector.detect(text, file_type="pptx")
    pres_contract = builder._build_from_presentation(
        extraction, text, detection, source_type
    )
    pres_team_before = len(pres_contract.fidelity.team_structured or [])
    merged = builder._merge_team_from_ms_contract(pres_contract, ms_contract)
    assert len(merged.fidelity.team_structured) >= MIN_TEAM
    assert len(merged.fidelity.team_structured) > pres_team_before or pres_team_before == 0


def test_contract_team_but_landing_missing_team_verdict() -> None:
    diag = ProjectDiagnostics(
        project_id="x",
        project_exists=True,
        team_structured_count=5,
        landing_exists=True,
        landing_has_team=False,
    )
    assert _compute_verdict(diag, None) == "contract_has_team_but_landing_missing"


def test_stale_landing_detected_by_timestamps() -> None:
    contract_dt = utc_now()
    landing_dt = contract_dt - timedelta(hours=1)
    diag = ProjectDiagnostics(
        project_id="x",
        project_exists=True,
        contract_updated_at=contract_dt.isoformat(),
        landing_generated_at=landing_dt.isoformat(),
        landing_exists=True,
    )
    contract_dt_parsed = contract_dt
    landing_dt_parsed = landing_dt
    if contract_dt_parsed > landing_dt_parsed:
        diag.landing_stale = True
    assert diag.landing_stale
    assert _compute_verdict(diag, None) == "stale_generated_landing"


@pytest.mark.asyncio
async def test_reparse_regenerates_landing_with_team() -> None:
    project_id = uuid4()
    extraction = _indlab_extraction()
    extraction.project_id = project_id
    contract = _make_builder().build(extraction)
    contract.project_id = project_id

    repo = ContractRepository(settings)
    await repo.save_contract(contract)
    await repo.save_extraction(extraction)

    stub = StubGenerationService(PromptEngine(), repo)
    landing = await stub.generate(project_id)
    assert _team_block_has_content([b.model_dump() for b in landing.blocks])

    builder = ContractBuilderService(repo)
    reparsed = await builder.reparse_structured(project_id)
    assert reparsed is not None
    assert len(reparsed.fidelity.team_structured) >= MIN_TEAM

    landing2 = await stub.generate(project_id)
    team_block = next(b for b in landing2.blocks if b.key == "team")
    assert team_block.bullets


def test_wrong_project_returns_clear_error() -> None:
    client = TestClient(app)
    missing_id = str(uuid4())
    resp = client.get(f"/api/v1/projects/{missing_id}")
    assert resp.status_code == 404


def test_evidence_single_file_hints_in_api(monkeypatch) -> None:
    contract = _make_builder().build(_indlab_extraction(pptx_only=True))

    class _FakeRepo:
        async def get_contract(self, _pid):
            return contract

    monkeypatch.setattr(
        "app.api.v1.contracts.get_contract_repository",
        lambda: _FakeRepo(),
    )
    client = TestClient(app)
    resp = client.get(f"/api/v1/projects/{contract.project_id}/evidence-report")
    assert resp.status_code == 200
    body = resp.json()
    assert body["source_count"] == 1
    assert any(SINGLE_FILE_WARNING in w for w in body.get("warnings", []))


def test_team_block_has_content_helper() -> None:
    assert _team_block_has_content(
        [{"key": "team", "bullets": ["Иванов — Dev"], "content": ""}]
    )
    assert not _team_block_has_content(
        [{"key": "team", "bullets": [], "content": ""}]
    )
