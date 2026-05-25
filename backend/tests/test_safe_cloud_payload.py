"""Tests for safe cloud payload preview API logic."""

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.config import Settings
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.schemas.pii import PrivacyMode
from app.services.analysis.llm_contract_builder import LLMContractBuilderService
from app.services.analysis.contract_builder import ContractBuilderService
from app.repositories.contract_repository import ContractRepository
from app.services.pipeline.pii_stage import PIIStageService
from app.services.pii.safe_payload import SafeCloudPayloadService


def _extraction(text: str) -> ExtractionResult:
    return ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[FileExtraction(filename="b.docx", file_type="docx", extracted_text=text)],
        extracted_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def services(tmp_path):
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
        settings.contracts_dir,
        settings.extractions_dir,
        settings.pii_reports_dir,
    ):
        p.mkdir(parents=True, exist_ok=True)
    repo = ContractRepository(settings)
    stage = PIIStageService(settings)
    llm = LLMContractBuilderService(settings, repo, ContractBuilderService(repo), pii_stage=stage)
    payload_svc = SafeCloudPayloadService(settings, stage)
    return settings, stage, payload_svc, llm


def test_hybrid_safe_payload_has_no_raw_fio(services):
    _settings, stage, payload_svc, llm = services
    text = "Кравченко Дмитрий Александрович — тимлид, email: a@b.com"
    extraction = _extraction(text)
    report, _ = asyncio.run(stage.prescan(extraction))
    preview = asyncio.run(
        payload_svc.build_preview(extraction.project_id, extraction, report, llm)
    )
    assert preview.safe_for_cloud
    assert "Кравченко" not in preview.preview_text_redacted
    assert "a@b.com" not in preview.preview_text_redacted


def test_local_only_blocks_cloud(services):
    settings, stage, payload_svc, llm = services
    settings.privacy_mode = "local_only"
    stage = PIIStageService(settings)
    payload_svc = SafeCloudPayloadService(settings, stage)
    extraction = _extraction("Email: x@y.com")
    report, _ = asyncio.run(stage.prescan(extraction))
    preview = asyncio.run(
        payload_svc.build_preview(extraction.project_id, extraction, report, llm)
    )
    assert preview.blocked_reason == "local_only"
    assert preview.safe_for_cloud is False


def test_cloud_unsafe_dev_marks_unsafe(services):
    settings, stage, payload_svc, llm = services
    settings.privacy_mode = "cloud_unsafe_dev"
    stage = PIIStageService(settings)
    payload_svc = SafeCloudPayloadService(settings, stage)
    extraction = _extraction("Кравченко Дмитрий Александрович")
    report, _ = asyncio.run(stage.prescan(extraction))
    preview = asyncio.run(
        payload_svc.build_preview(extraction.project_id, extraction, report, llm)
    )
    assert preview.unsafe is True
    assert preview.safe_for_cloud is False
    assert "cloud_unsafe_dev_active" in preview.warnings
