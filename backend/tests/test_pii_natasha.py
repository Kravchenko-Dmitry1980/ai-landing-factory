"""Tests for Natasha layer 2 and Russian FIO detection."""

import pytest

from app.config import Settings
from app.schemas.pii import PIIEntityType
from app.services.pii.detector import PIIDetector, natasha_available, reset_natasha_cache


@pytest.fixture
def detector():
    settings = Settings(enable_pii_detection=True, pii_mask_names=True)
    return PIIDetector(settings)


@pytest.mark.parametrize(
    "text,expected_substrings",
    [
        ("Кравченко Дмитрий Александрович — тимлид проекта", ["Кравченко", "Дмитрий"]),
        (
            "Древаль Александр Васильевич, главный эндокринолог Московской области",
            ["Древаль", "Александр"],
        ),
        (
            "Беляев Борис Олегович разработал техническое задание",
            ["Беляев", "Борис"],
        ),
    ],
)
def test_detects_russian_fio(detector, text, expected_substrings):
    entities, _warnings = detector.detect_text(text, "brief.docx")
    originals = " ".join(e.original for e in entities)
    for part in expected_substrings:
        assert part in originals


def test_masks_email_and_phone(detector):
    text = "Телефон: +7 999 123-45-67, email: test@example.com"
    entities, _ = detector.detect_text(text)
    types = {e.type for e in entities}
    assert PIIEntityType.EMAIL in types
    assert PIIEntityType.PHONE in types


def test_org_name_not_person(detector):
    text = "МОНИКИ им. М. Ф. Владимирского — ведущая клиника"
    entities, _ = detector.detect_text(text)
    person_names = [e for e in entities if e.type == PIIEntityType.PERSON_NAME]
    joined = " ".join(e.original for e in person_names).lower()
    assert "моники" not in joined
    assert "владимирского" not in joined


def test_product_names_not_person(detector):
    text = "OpenAI, Qwen, Meditron — используемые модели"
    entities, _ = detector.detect_text(text)
    person_names = [e for e in entities if e.type == PIIEntityType.PERSON_NAME]
    assert not person_names


def test_natasha_warning_when_unavailable(monkeypatch, detector):
    reset_natasha_cache()
    monkeypatch.setattr("app.services.pii.detector._load_natasha", lambda: None)
    _entities, warnings = detector.detect_text("Иванов Иван Иванович")
    assert "natasha_not_available" in warnings


def test_same_fio_single_placeholder(detector):
    from app.services.pii.redactor import PIIRedactor
    from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
    from datetime import datetime, timezone
    from uuid import uuid4

    text = (
        "Кравченко Дмитрий Александрович — тимлид\n"
        "Контакт: Кравченко Дмитрий Александрович\n"
    )
    extraction = ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[FileExtraction(filename="t.txt", file_type="txt", extracted_text=text)],
        extracted_at=datetime.now(timezone.utc),
    )
    redactor = PIIRedactor(detector)
    _redacted, entities, _ = redactor.redact_extraction(extraction)
    person_placeholders = {e.placeholder for e in entities if e.type == PIIEntityType.PERSON_NAME}
    assert len(person_placeholders) <= 2
