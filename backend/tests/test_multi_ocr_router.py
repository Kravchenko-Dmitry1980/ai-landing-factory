"""Multi-OCR router (auto mode) tests."""

from __future__ import annotations

import pytest

from app.services.ocr.multi_ocr_router import select_auto_engine, select_engine_by_name


def test_select_engine_by_name_tesseract(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Tess:
        name = "tesseract"

        def is_available(self):
            return True

    monkeypatch.setattr(
        "app.services.ocr.multi_ocr_router.create_engine",
        lambda name: _Tess() if name == "tesseract" else None,
    )
    engine = select_engine_by_name("tesseract")
    assert engine is not None
    assert engine.name == "tesseract"


def test_auto_chooses_first_working_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Easy:
        name = "easyocr"

        def is_available(self):
            return True

    class _Paddle:
        name = "paddleocr"

        def is_available(self):
            return False

    def _create(name):
        if name == "tesseract":
            return None
        if name == "easyocr":
            return _Easy()
        if name == "paddleocr":
            return _Paddle()
        return None

    monkeypatch.setattr("app.services.ocr.multi_ocr_router.create_engine", _create)
    monkeypatch.setattr(
        "app.services.ocr.multi_ocr_router.get_engine_priority",
        lambda: ["tesseract", "easyocr", "paddleocr"],
    )
    engine = select_auto_engine()
    assert engine is not None
    assert engine.name == "easyocr"


def test_auto_mode_from_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import settings
    from app.services.ocr.multi_ocr_router import select_configured_engine

    class _Tess:
        name = "tesseract"

        def is_available(self):
            return True

    monkeypatch.setattr(settings, "ocr_engine", "auto")
    monkeypatch.setattr(
        "app.services.ocr.multi_ocr_router.select_auto_engine",
        lambda **kwargs: _Tess(),
    )
    engine = select_configured_engine()
    assert engine is not None
    assert engine.name == "tesseract"
