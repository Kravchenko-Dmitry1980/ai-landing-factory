"""PaddleOCR engine compatibility tests."""

from __future__ import annotations

import sys
import types

import pytest

from app.services.ocr.engines.paddleocr_engine import (
    PaddleOcrEngine,
    _parse_paddle_result,
)


class _FakePaddleOCR:
    calls: list[dict] = []
    succeed_on_attempt = 2

    def __init__(self, **kwargs):
        type(self).calls.append(dict(kwargs))
        if "show_log" in kwargs:
            raise ValueError("Unknown argument: show_log")
        attempt = len(type(self).calls)
        if attempt < type(self).succeed_on_attempt:
            raise ValueError(f"init failed on attempt {attempt}")

    def ocr(self, path, cls=True):
        return [
            [
                [[0, 0], [1, 0], [1, 1], [0, 1]],
                ("Иванов Иван", 0.91),
            ]
        ]


@pytest.fixture(autouse=True)
def _reset_fake_paddle(monkeypatch: pytest.MonkeyPatch):
    _FakePaddleOCR.calls = []
    _FakePaddleOCR.succeed_on_attempt = 2
    fake_module = types.ModuleType("paddleocr")
    fake_module.PaddleOCR = _FakePaddleOCR
    monkeypatch.setitem(sys.modules, "paddleocr", fake_module)
    yield


def test_paddle_engine_init_does_not_use_show_log() -> None:
    _FakePaddleOCR.succeed_on_attempt = 1
    engine = PaddleOcrEngine()
    engine._available = True
    assert engine._ensure_engine() is True
    assert engine._ocr is not None
    for call in _FakePaddleOCR.calls:
        assert "show_log" not in call


def test_paddle_engine_fallback_attempts() -> None:
    _FakePaddleOCR.succeed_on_attempt = 2
    engine = PaddleOcrEngine()
    engine._available = True
    assert engine._ensure_engine() is True
    assert len(_FakePaddleOCR.calls) == 2
    assert engine._init_kwargs == {"use_angle_cls": True, "lang": "ru"}


def test_parse_old_paddle_result() -> None:
    raw = [
        [
            [[0, 0], [1, 0], [1, 1], [0, 1]],
            ("Команда проекта", 0.95),
        ],
        [
            [[0, 0], [1, 0], [1, 1], [0, 1]],
            ("Тимлид: Иванов Иван", 0.88),
        ],
    ]
    text, confidence, warnings = _parse_paddle_result(raw)
    assert "Команда проекта" in text
    assert "Тимлид: Иванов Иван" in text
    assert confidence is not None
    assert confidence > 0.8
    assert not warnings


def test_parse_new_paddle_result_rec_texts() -> None:
    raw = {
        "rec_texts": ["Команда проекта", "Тимлид: Петров Петр"],
        "rec_scores": [0.93, 0.87],
    }
    text, confidence, warnings = _parse_paddle_result(raw)
    assert "Команда проекта" in text
    assert "Тимлид: Петров Петр" in text
    assert confidence is not None
    assert not warnings


def test_engine_init_failure_returns_warning_not_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _AlwaysFailPaddleOCR:
        def __init__(self, **kwargs):
            if "show_log" in kwargs:
                raise ValueError("Unknown argument: show_log")
            raise RuntimeError("init failed")

    fake_module = types.ModuleType("paddleocr")
    fake_module.PaddleOCR = _AlwaysFailPaddleOCR
    monkeypatch.setitem(sys.modules, "paddleocr", fake_module)

    engine = PaddleOcrEngine()
    engine._available = True
    result = engine.extract_text(b"fake")
    assert result.text == ""
    assert result.warnings
    assert "PaddleOCR init failed" in result.warnings[0]


def test_classify_paddle_inference_pir_error() -> None:
    from app.services.ocr.engines.paddleocr_engine import classify_paddle_error

    error = (
        "(Unimplemented) ConvertPirAttribute2RuntimeAttribute not support "
        "[pir::ArrayAttribute<pir::DoubleAttribute>] (at ... onednn_instruction.cc:118)"
    )
    code, stage, action = classify_paddle_error(error, stage="inference")
    assert code == "paddleocr_pir_onednn_unimplemented"
    assert stage == "inference"
    assert "Tesseract" in action or "oneDNN" in action


def test_classify_paddlepaddle_missing() -> None:
    from app.services.ocr.engines.paddleocr_engine import classify_paddle_error

    code, stage, _ = classify_paddle_error("paddlepaddle is not installed", stage="dependency")
    assert code == "paddlepaddle_missing"
    assert stage == "dependency"
