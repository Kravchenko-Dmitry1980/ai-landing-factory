"""Tesseract language configuration tests."""

from __future__ import annotations

import pytest

from app.config import settings
from app.services.ocr.engines import tesseract_engine


def test_tesseract_lang_defaults_to_rus_eng(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ocr_tesseract_lang", "")
    assert tesseract_engine.get_tesseract_lang() == "rus+eng"


def test_tesseract_lang_from_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ocr_tesseract_lang", "rus")
    assert tesseract_engine.get_tesseract_lang() == "rus"


def test_warning_if_rus_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        tesseract_engine,
        "check_russian_language_available",
        lambda: (False, ["eng"]),
    )
    warnings = tesseract_engine.tesseract_language_warnings()
    assert any("rus" in w.lower() for w in warnings)
