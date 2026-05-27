"""EasyOCR optional engine tests."""

from __future__ import annotations

import sys
import types

import pytest

from app.services.ocr.engines.easyocr_engine import EasyOcrEngine, get_easyocr_langs


def test_easyocr_unavailable_no_crash(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delitem(sys.modules, "easyocr", raising=False)
    engine = EasyOcrEngine()
    assert engine.is_available() is False
    result = engine.extract_text(b"fake")
    assert result.text == ""
    assert result.warnings


def test_easyocr_extracts_lines(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeReader:
        def readtext(self, path):
            return [
                ([], "Команда проекта", 0.91),
                ([], "Татьяна Ерюкова", 0.88),
            ]

    fake_module = types.ModuleType("easyocr")
    fake_module.Reader = lambda *a, **k: _FakeReader()
    monkeypatch.setitem(sys.modules, "easyocr", fake_module)

    engine = EasyOcrEngine()
    assert engine.is_available() is True
    assert engine._ensure_reader() is True
    result = engine.extract_text(b"fake-image")
    assert "Команда проекта" in result.text
    assert "Татьяна Ерюкова" in result.text
    assert result.confidence is not None


def test_easyocr_langs_from_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "ocr_easyocr_langs", "ru,en")
    assert get_easyocr_langs() == ["ru", "en"]
