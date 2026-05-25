"""Tests for LandingDocumentDetector."""

from pathlib import Path

import pytest

from app.services.contract_fidelity.landing_document_detector import LandingDocumentDetector

FIXTURE = Path(__file__).parent / "fixtures" / "endocrinology_landing.txt"


@pytest.fixture
def endocrinology_text() -> str:
    return FIXTURE.read_text(encoding="utf-8")


def test_detector_high_confidence(endocrinology_text: str) -> None:
    result = LandingDocumentDetector().detect(endocrinology_text)
    assert result.is_structured_landing is True
    assert result.confidence >= 0.8
    assert "essence" in result.detected_sections
    assert "tasks" in result.detected_sections
    assert "team" in result.detected_sections


def test_detector_empty_text() -> None:
    result = LandingDocumentDetector().detect("")
    assert result.is_structured_landing is False
    assert result.confidence == 0.0


def test_detector_plain_text() -> None:
    result = LandingDocumentDetector().detect("Простой текст без структуры ленда.")
    assert result.is_structured_landing is False
