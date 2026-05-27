"""CLI tests for check_ocr_env.py."""

from __future__ import annotations

import json

import pytest

from app.schemas.ocr_runtime import EngineRuntimeStatus, OcrRuntimeStatus
from scripts import check_ocr_env as cli


def test_cli_json_mode(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(
        cli,
        "collect_ocr_runtime_status",
        lambda **kwargs: OcrRuntimeStatus(
            ocr_enabled=False,
            ready=True,
            recommended_action="ok",
        ),
    )
    assert cli.main(["--json"]) == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["ocr_enabled"] is False
    assert payload["ready"] is True


def test_cli_text_mode(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(
        cli,
        "collect_ocr_runtime_status",
        lambda **kwargs: OcrRuntimeStatus(
            ocr_enabled=False,
            ready=True,
            recommended_action="ok",
        ),
    )
    assert cli.main([]) == 0
    out = capsys.readouterr().out
    assert "OCR Runtime Status" in out


def test_check_ocr_env_ready_requires_inference_when_require_ocr(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        cli,
        "collect_ocr_runtime_status",
        lambda **kwargs: OcrRuntimeStatus(
            ocr_enabled=True,
            ready=False,
            test_image_ok=False,
            paddleocr=EngineRuntimeStatus(
                package_installed=True,
                init_ok=True,
                model_ready=True,
                inference_ok=False,
                error_code="paddleocr_pir_onednn_unimplemented",
                failure_stage="inference",
            ),
            tesseract=EngineRuntimeStatus(package_installed=False, binary_available=False),
            recommended_action="Try Tesseract fallback",
        ),
    )
    assert cli.main(["--require-ocr"]) == 1
    err = capsys.readouterr().err
    assert "inference_ok=False" in err or "readiness checks" in err


def test_check_ocr_env_passes_when_inference_ok(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        cli,
        "collect_ocr_runtime_status",
        lambda **kwargs: OcrRuntimeStatus(
            ocr_enabled=True,
            ready=True,
            test_image_ok=True,
            test_image_chars=10,
            paddleocr=EngineRuntimeStatus(
                package_installed=True,
                init_ok=True,
                model_ready=True,
                inference_ok=True,
                test_image_ok=True,
                test_image_chars=10,
            ),
        ),
    )
    assert cli.main(["--require-ocr"]) == 0
