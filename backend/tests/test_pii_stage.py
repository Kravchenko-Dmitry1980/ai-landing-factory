import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.config import Settings
from app.repositories.contract_repository import ContractRepository
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.schemas.pii import PrivacyMode
from app.services.pipeline.pii_stage import PIIStageService


def _pii_extraction() -> ExtractionResult:
    pid = uuid4()
    return ExtractionResult(
        project_id=pid,
        payload=ExtractionPayload(client="ООО Ромашка"),
        files=[
            FileExtraction(
                filename="brief.docx",
                file_type="docx",
                extracted_text=(
                    "Руководитель: Александр Васильевич Древаль\n"
                    "Email: alex.dreval@example.com\n"
                    "Тел: +7 (495) 123-45-67\n"
                    "Диагноз: сахарный диабет 2 типа\n"
                ),
            )
        ],
        extracted_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def stage(tmp_path):
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
    ):
        p.mkdir(parents=True, exist_ok=True)
    return PIIStageService(settings), ContractRepository(settings)


def test_detects_and_redacts_pii(stage):
    svc, repo = stage
    extraction = _pii_extraction()
    redacted, report, llm_view = asyncio.run(svc.process(extraction))

    assert report.has_pii
    assert report.redaction_count >= 2
    assert "[EMAIL_" in llm_view.files[0].extracted_text or "[PERSON_" in llm_view.files[0].extracted_text
    assert "alex.dreval@example.com" not in llm_view.files[0].extracted_text
    assert redacted.mapping
    asyncio.run(repo.save_pii_report(report))
    loaded = asyncio.run(repo.get_pii_report(extraction.project_id))
    assert loaded is not None
    assert loaded.has_pii


def test_rehydrator_restores_placeholders(stage):
    from app.services.pii.detector import PIIDetector
    from app.services.pii.redactor import PIIRedactor
    from app.services.pii.rehydrator import PIIRehydrator

    svc, _ = stage
    extraction = _pii_extraction()
    redactor = PIIRedactor(PIIDetector(svc._settings))
    redacted, entities, _ = redactor.redact_extraction(extraction)
    mapping = redacted.mapping
    rehydrator = PIIRehydrator(mapping)
    out = rehydrator._replace_in_string("Контакт: [EMAIL_1], лид: [PERSON_1]")
    assert "@" in out or "Александр" in out


def test_cloud_unsafe_keeps_raw_text(stage):
    svc, _ = stage
    svc._settings.privacy_mode = "cloud_unsafe_dev"
    extraction = _pii_extraction()
    _, report, llm_view = asyncio.run(svc.process(extraction))
    assert report.has_pii
    assert "alex.dreval@example.com" in llm_view.files[0].extracted_text


def test_public_report_has_no_originals(stage):
    from app.services.pii.report import to_public_report

    svc, _ = stage
    extraction = _pii_extraction()
    _, report, _ = asyncio.run(svc.process(extraction))
    public = to_public_report(report)
    for ent in public.entities:
        assert not hasattr(ent, "original") or "original" not in ent.model_dump()
