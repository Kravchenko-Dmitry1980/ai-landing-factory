"""Tests for PII prescan after upload pipeline."""

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.config import Settings
from app.repositories.contract_repository import ContractRepository
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.schemas.pii import PIIRiskLevel
from app.services.pipeline import ContentPipeline
from app.services.pipeline.pii_stage import PIIStageService


def _settings(tmp_path):
    settings = Settings(
        data_dir=tmp_path / "data",
        uploads_dir=tmp_path / "data" / "uploads",
        contracts_dir=tmp_path / "data" / "contracts",
        extractions_dir=tmp_path / "data" / "extractions",
        privacy_mode="hybrid_safe",
        enable_pii_detection=True,
    )
    for p in (
        settings.data_dir,
        settings.uploads_dir,
        settings.contracts_dir,
        settings.extractions_dir,
        settings.pii_reports_dir,
        settings.pii_safe_payloads_dir,
    ):
        p.mkdir(parents=True, exist_ok=True)
    return settings


def _extraction() -> ExtractionResult:
    return ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[
            FileExtraction(
                filename="brief.docx",
                file_type="docx",
                extracted_text="Email: secret@test.com, тел +7 999 111-22-33",
            )
        ],
        extracted_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def stage_repo(tmp_path):
    settings = _settings(tmp_path)
    return PIIStageService(settings), ContractRepository(settings)


def test_prescan_detects_pii(stage_repo):
    stage, repo = stage_repo
    extraction = _extraction()
    report, summary = asyncio.run(stage.prescan(extraction))
    assert report.has_pii
    assert summary.has_pii
    assert summary.risk_level != PIIRiskLevel.UNKNOWN
    asyncio.run(repo.save_pii_report(report))
    loaded = asyncio.run(repo.get_pii_report(extraction.project_id))
    assert loaded is not None


def test_prescan_failure_does_not_crash(stage_repo, monkeypatch):
    stage, _repo = stage_repo
    extraction = _extraction()

    def boom(_self, _ext):
        raise RuntimeError("detector failed")

    monkeypatch.setattr(
        "app.services.pii.redactor.PIIRedactor.redact_extraction",
        boom,
    )
    report, summary = asyncio.run(stage.prescan(extraction))
    assert summary.risk_level == PIIRiskLevel.UNKNOWN
    assert summary.safe_for_cloud_current_mode is False
    assert "prescan_failed" in summary.warnings


def test_pipeline_returns_pii_summary(tmp_path, monkeypatch):
    settings = _settings(tmp_path)
    repo = ContractRepository(settings)
    stage = PIIStageService(settings)
    extraction = _extraction()

    class FakeExtractor:
        async def extract(self, project_id):
            return extraction.model_copy(update={"project_id": project_id})

    class FakeBuilder:
        async def build_and_save(self, ext):
            return None

    class FakeGen:
        async def generate(self, project_id):
            return None

    pipeline = ContentPipeline(FakeExtractor(), FakeBuilder(), FakeGen(), repo, stage)
    summary = asyncio.run(pipeline.run_after_upload(extraction.project_id))
    assert summary is not None
    assert summary["has_pii"] is True
