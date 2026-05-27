"""OCR engine benchmark tests."""

from __future__ import annotations

import json

import pytest

from app.schemas.ocr_benchmark import OcrEngineBenchmarkResult
from app.services.ocr.ocr_benchmark import (
    benchmark_engine_on_images,
    compute_benchmark_score,
    count_known_name_hits,
    format_benchmark_table,
    run_ocr_benchmark,
    select_best_engine,
)


def test_compute_benchmark_score() -> None:
    good = OcrEngineBenchmarkResult(
        engine="easyocr",
        ok=True,
        raw_chars=600,
        accepted_team_count=2,
        known_names_hit_count=1,
        team_section_detected=True,
        rejected_person_count=1,
    )
    good.score = compute_benchmark_score(good)
    bad = OcrEngineBenchmarkResult(engine="paddleocr", ok=False, error_code="paddle_fail")
    bad.score = compute_benchmark_score(bad)
    assert good.score > bad.score


def test_known_name_hits() -> None:
    text = "\u0422\u0430\u0442\u044c\u044f\u043d\u0430 \u0415\u0440\u044e\u043a\u043e\u0432\u0430 \u2014 \u043f\u043e\u043c\u043e\u0449\u043d\u0438\u043a \u0442\u0438\u043c\u043b\u0438\u0434\u0430"
    name1 = "\u0422\u0430\u0442\u044c\u044f\u043d\u0430 \u0415\u0440\u044e\u043a\u043e\u0432\u0430"
    name2 = "\u0415\u0433\u043e\u0440 \u0411\u044b\u043a\u043e\u0432"
    hits = count_known_name_hits(text, [name1], [name1, name2])
    assert hits == 1
    hits2 = count_known_name_hits(
        f"{text}. {name2} \u0440\u0430\u0437\u0440\u0430\u0431\u043e\u0442\u0447\u0438\u043a",
        [name1, name2],
        [name1, name2],
    )
    assert hits2 == 2


def test_select_best_engine_by_accepted_team() -> None:
    tesseract = OcrEngineBenchmarkResult(
        engine="tesseract",
        ok=True,
        accepted_team_count=1,
        raw_chars=500,
        score=compute_benchmark_score(
            OcrEngineBenchmarkResult(
                engine="tesseract",
                ok=True,
                accepted_team_count=1,
                raw_chars=500,
                team_section_detected=True,
            )
        ),
    )
    easyocr = OcrEngineBenchmarkResult(
        engine="easyocr",
        ok=True,
        accepted_team_count=3,
        raw_chars=800,
        team_section_detected=True,
        known_names_hit_count=2,
    )
    easyocr.score = compute_benchmark_score(easyocr)
    best, reason = select_best_engine([tesseract, easyocr])
    assert best == "easyocr"
    assert "accepted_team=3" in reason


def test_paddle_error_does_not_fail_benchmark(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FailPaddle:
        name = "paddleocr"

        def is_available(self):
            return True

        def extract_text(self, image):
            from app.services.ocr.ocr_contracts import OcrEngineResult

            return OcrEngineResult(
                warnings=[
                    "PaddleOCR failed: ConvertPirAttribute2RuntimeAttribute onednn_instruction.cc"
                ]
            )

    class _OkTess:
        name = "tesseract"

        def is_available(self):
            return True

        def extract_text(self, image):
            from app.services.ocr.ocr_contracts import OcrEngineResult

            return OcrEngineResult(text="Команда проекта\nТатьяна Ерюкова — помощник тимлида")

    def _create(name):
        if name == "paddleocr":
            return _FailPaddle()
        if name == "tesseract":
            return _OkTess()
        return None

    monkeypatch.setattr("app.services.ocr.ocr_benchmark.create_engine", _create)
    images = [b"fake"]
    paddle = benchmark_engine_on_images("paddleocr", images)
    tess = benchmark_engine_on_images("tesseract", images)
    assert paddle.ok is False
    assert paddle.error_code is not None
    assert tess.ok is True
    best, _ = select_best_engine([paddle, tess])
    assert best == "tesseract"


def test_json_report_stable() -> None:
    result = OcrEngineBenchmarkResult(engine="tesseract", ok=True, raw_chars=100)
    payload = result.model_dump(mode="json")
    json.dumps(payload)
    assert payload["engine"] == "tesseract"


def test_format_benchmark_table() -> None:
    from app.schemas.ocr_benchmark import OcrBenchmarkReport

    report = OcrBenchmarkReport(
        source_file="deck.pptx",
        page_or_slide=25,
        results=[
            OcrEngineBenchmarkResult(engine="tesseract", ok=True, raw_chars=100),
        ],
        best_engine="tesseract",
        reason="score=10",
    )
    text = format_benchmark_table(report)
    assert "tesseract" in text
    assert "best_engine" in text
