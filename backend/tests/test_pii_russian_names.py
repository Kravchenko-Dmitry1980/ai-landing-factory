"""Extended Russian FIO and PII detection tests."""

import re

import pytest

from app.config import Settings
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.schemas.pii import PIIEntityType
from app.models.domain import utc_now
from app.services.pii.detector import PIIDetector, reset_natasha_cache
from app.services.pii.redactor import PIIRedactor
from app.services.pii.safe_payload import SafeCloudPayloadService
from app.services.analysis.contract_builder import ContractBuilderService
from app.services.analysis.llm_contract_builder import LLMContractBuilderService
from app.repositories.contract_repository import ContractRepository
from app.services.pipeline.pii_stage import PIIStageService
from uuid import uuid4


@pytest.fixture
def detector():
    reset_natasha_cache()
    settings = Settings(enable_pii_detection=True, pii_mask_names=True)
    return PIIDetector(settings)


@pytest.fixture
def hybrid_settings(tmp_path):
    s = Settings(
        data_dir=tmp_path / "data",
        extractions_dir=tmp_path / "data" / "extractions",
        privacy_mode="hybrid_safe",
        enable_pii_detection=True,
        pii_mask_names=True,
    )
    s.pii_reports_dir.mkdir(parents=True, exist_ok=True)
    s.pii_safe_payloads_dir.mkdir(parents=True, exist_ok=True)
    return s


FIO_CASES = [
    ("Кравченко Дмитрий Александрович — тимлид проекта", ["Кравченко", "Дмитрий"]),
    (
        "Александр Васильевич Древаль, главный эндокринолог Московской области",
        ["Древаль", "Александр"],
    ),
    (
        "Беляев Борис Олегович разработал техническое задание",
        ["Беляев", "Борис"],
    ),
    (
        "Дмитриева Анна Анатольевна — Lead по промптам",
        ["Дмитриева", "Анна"],
    ),
    (
        "Шкрыль Ярослав Васильевич — ведущий разработчик",
        ["Шкрыль", "Ярослав"],
    ),
]


@pytest.mark.parametrize("text,expected_parts", FIO_CASES)
def test_russian_fio_detected(detector, text, expected_parts):
    entities, _ = detector.detect_text(text)
    joined = " ".join(e.original for e in entities)
    for part in expected_parts:
        assert part in joined


def test_moniki_not_person(detector):
    text = "МОНИКИ им. М. Ф. Владимирского"
    entities, _ = detector.detect_text(text)
    persons = [e for e in entities if e.type == PIIEntityType.PERSON_NAME]
    joined = " ".join(e.original for e in persons).lower()
    assert "моники" not in joined
    assert "владимирского" not in joined


def test_tech_names_not_person(detector):
    text = "OpenAI, Qwen, Meditron, FastAPI, Docker"
    entities, _ = detector.detect_text(text)
    persons = [e for e in entities if e.type == PIIEntityType.PERSON_NAME]
    assert not persons


def test_phone_email_masked(detector):
    text = "Телефон: +7 999 123-45-67, email: test@example.com"
    entities, _ = detector.detect_text(text)
    types = {e.type for e in entities}
    assert PIIEntityType.PHONE in types
    assert PIIEntityType.EMAIL in types

    extraction = ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[FileExtraction(filename="t.txt", file_type="txt", extracted_text=text)],
        extracted_at=utc_now(),
    )
    redactor = PIIRedactor(detector)
    redacted, ents, _ = redactor.redact_extraction(extraction)
    combined = redacted.files[0].extracted_text
    assert "test@example.com" not in combined
    assert "999 123" not in combined or "[PHONE" in combined
    placeholders = {e.placeholder for e in ents if e.placeholder}
    assert any("EMAIL" in p for p in placeholders)
    assert any("PHONE" in p for p in placeholders)


def test_public_report_no_original(hybrid_settings):
    import asyncio

    text = (
        "Кравченко Дмитрий Александрович — тимлид\n"
        "Email: secret@example.com\n"
        "Тел: +7 999 123-45-67\n"
    )
    extraction = ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[FileExtraction(filename="brief.docx", file_type="docx", extracted_text=text)],
        extracted_at=utc_now(),
    )
    stage = PIIStageService(hybrid_settings)
    report, _ = asyncio.run(stage.prescan(extraction))
    from app.services.pii.report import to_public_report

    public = to_public_report(report)
    dumped = public.model_dump_json()
    assert "secret@example.com" not in dumped
    assert "Кравченко" not in dumped
    for ent in public.entities:
        data = ent.model_dump()
        assert "original" not in data


def test_safe_cloud_payload_no_raw_pii(hybrid_settings):
    import asyncio

    text = "Кравченко Дмитрий — email: person@corp.ru"
    extraction = ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[FileExtraction(filename="x.docx", file_type="docx", extracted_text=text)],
        extracted_at=utc_now(),
    )
    stage = PIIStageService(hybrid_settings)
    report, _ = asyncio.run(stage.prescan(extraction))
    repo = ContractRepository(hybrid_settings)
    llm = LLMContractBuilderService(
        hybrid_settings, repo, ContractBuilderService(repo), pii_stage=stage
    )
    payload_svc = SafeCloudPayloadService(hybrid_settings, stage)
    preview = asyncio.run(
        payload_svc.build_preview(extraction.project_id, extraction, report, llm)
    )
    assert preview.safe_for_cloud is True
    assert "person@corp.ru" not in preview.preview_text_redacted
    assert "Кравченко" not in preview.preview_text_redacted
    assert re.search(r"\[PERSON_\d+\]|\[EMAIL_\d+\]", preview.preview_text_redacted)


@pytest.mark.parametrize(
    "mode,expect_blocked,expect_unsafe",
    [
        ("local_only", True, False),
        ("cloud_unsafe_dev", False, True),
    ],
)
def test_privacy_modes(tmp_path, mode, expect_blocked, expect_unsafe):
    import asyncio

    settings = Settings(
        data_dir=tmp_path / "data",
        extractions_dir=tmp_path / "data" / "extractions",
        privacy_mode=mode,
        enable_pii_detection=True,
    )
    settings.pii_reports_dir.mkdir(parents=True, exist_ok=True)
    settings.pii_safe_payloads_dir.mkdir(parents=True, exist_ok=True)
    pid = uuid4()
    extraction = ExtractionResult(
        project_id=pid,
        payload=ExtractionPayload(),
        files=[
            FileExtraction(
                filename="x.docx",
                file_type="docx",
                extracted_text="Иванов Иван",
            )
        ],
        extracted_at=utc_now(),
    )
    stage = PIIStageService(settings)
    report, _ = asyncio.run(stage.prescan(extraction))
    repo = ContractRepository(settings)
    llm = LLMContractBuilderService(
        settings, repo, ContractBuilderService(repo), pii_stage=stage
    )
    preview = asyncio.run(
        SafeCloudPayloadService(settings, stage).build_preview(pid, extraction, report, llm)
    )
    assert preview.safe_for_cloud is False
    if expect_blocked:
        assert preview.blocked_reason == "local_only"
    if expect_unsafe:
        assert preview.unsafe is True
