"""OCR runtime environment diagnostics tests."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from app.schemas.ocr_runtime import EngineRuntimeStatus, OcrRuntimeStatus
from app.services.ocr import ocr_env
from app.services.ocr.engines.paddleocr_engine import classify_paddle_error


def test_ocr_disabled_graceful(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ocr_env.settings, "ocr_enabled", False)
    monkeypatch.setattr(ocr_env, "check_paddleocr_status", lambda **kwargs: EngineRuntimeStatus())
    monkeypatch.setattr(ocr_env, "check_tesseract_status", lambda **kwargs: EngineRuntimeStatus())
    monkeypatch.setattr(ocr_env, "ensure_cache_dir", lambda: (Path("/tmp/ocr_cache"), True))

    status = ocr_env.collect_ocr_runtime_status()
    assert status.ready is True
    assert any("disabled" in w.lower() for w in status.warnings)


def test_paddle_missing_no_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ocr_env, "package_installed", lambda name: name != "paddleocr")
    status = ocr_env.check_paddleocr_status()
    assert status.package_installed is False
    assert status.error is not None
    assert status.failure_stage == "import"


def test_tesseract_wrapper_without_binary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ocr_env, "package_installed", lambda name: name == "pytesseract")

    class _FakePytesseract:
        @staticmethod
        def get_tesseract_version():
            raise RuntimeError("tesseract is not installed")

    monkeypatch.setitem(__import__("sys").modules, "pytesseract", _FakePytesseract())
    status = ocr_env.check_tesseract_status()
    assert status.package_installed is True
    assert status.binary_available is False
    assert "Windows binary is missing" in " ".join(status.warnings)


def test_cache_dir_can_be_created(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache = tmp_path / "ocr_cache"
    monkeypatch.setattr(ocr_env.settings, "ocr_cache_dir_env", str(cache))
    path, ok = ocr_env.ensure_cache_dir()
    assert ok is True
    assert path.exists()


def test_socks_proxy_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        ocr_env,
        "detect_socks_proxy",
        lambda: (True, {"http": "socks5://127.0.0.1:1080"}),
    )
    monkeypatch.setattr(ocr_env.settings, "ocr_enabled", False)
    monkeypatch.setattr(ocr_env, "check_paddleocr_status", lambda **kwargs: EngineRuntimeStatus())
    monkeypatch.setattr(ocr_env, "check_tesseract_status", lambda **kwargs: EngineRuntimeStatus())
    monkeypatch.setattr(ocr_env, "ensure_cache_dir", lambda: (Path("/tmp/ocr_cache"), True))

    status = ocr_env.collect_ocr_runtime_status()
    assert any("SOCKS proxy detected" in w for w in status.warnings)


def test_require_ocr_fails_when_no_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import check_ocr_env as cli

    monkeypatch.setattr(
        cli,
        "collect_ocr_runtime_status",
        lambda **kwargs: OcrRuntimeStatus(
            ocr_enabled=True,
            ready=False,
            paddleocr=EngineRuntimeStatus(package_installed=True, init_ok=False),
            tesseract=EngineRuntimeStatus(package_installed=False, binary_available=False),
        ),
    )
    assert cli.main(["--require-ocr"]) == 1


def test_json_output_has_stable_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ocr_env.settings, "ocr_enabled", False)
    monkeypatch.setattr(ocr_env, "check_paddleocr_status", lambda **kwargs: EngineRuntimeStatus())
    monkeypatch.setattr(ocr_env, "check_tesseract_status", lambda **kwargs: EngineRuntimeStatus())
    monkeypatch.setattr(ocr_env, "ensure_cache_dir", lambda: (Path("/tmp/ocr_cache"), True))

    status = ocr_env.collect_ocr_runtime_status()
    payload = status.model_dump(mode="json")
    for key in (
        "ocr_enabled",
        "configured_engine",
        "paddleocr",
        "tesseract",
        "ready",
        "recommended_action",
    ):
        assert key in payload
    assert "inference_ok" in payload["paddleocr"]
    json.dumps(payload)


def test_paddle_init_ok_but_inference_failed_not_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pir_error = (
        "(Unimplemented) ConvertPirAttribute2RuntimeAttribute not support "
        "[pir::ArrayAttribute<pir::DoubleAttribute>] (at ... onednn_instruction.cc:118)"
    )

    def _paddle_status(**kwargs):
        run_inference = kwargs.get("run_inference", False)
        status = EngineRuntimeStatus(
            package_installed=True,
            init_ok=True,
            model_ready=True,
            version="3.5.0",
        )
        if run_inference:
            status.inference_ok = False
            status.test_image_ok = False
            status.test_image_chars = 0
            status.error = pir_error
            code, stage, action = classify_paddle_error(pir_error, stage="inference")
            status.error_code = code
            status.failure_stage = stage
            status.recommended_action = action
        return status

    monkeypatch.setattr(ocr_env.settings, "ocr_enabled", True)
    monkeypatch.setattr(ocr_env, "check_paddleocr_status", _paddle_status)
    monkeypatch.setattr(
        ocr_env,
        "check_tesseract_status",
        lambda **kwargs: EngineRuntimeStatus(
            package_installed=True,
            binary_available=False,
            init_ok=False,
        ),
    )
    monkeypatch.setattr(ocr_env, "ensure_cache_dir", lambda: (Path("/tmp/ocr_cache"), True))
    monkeypatch.setattr(ocr_env, "run_test_image_ocr", lambda: (False, 0, pir_error))

    status = ocr_env.collect_ocr_runtime_status(require_inference=True, test_image=True)
    assert status.paddleocr.init_ok is True
    assert status.paddleocr.inference_ok is False
    assert status.paddleocr.error_code == "paddleocr_pir_onednn_unimplemented"
    assert status.paddleocr.failure_stage == "inference"
    assert status.ready is False


def test_classify_paddle_pir_onednn_error() -> None:
    error = "ConvertPirAttribute2RuntimeAttribute not support onednn_instruction.cc"
    code, stage, action = classify_paddle_error(error, stage="inference")
    assert code == "paddleocr_pir_onednn_unimplemented"
    assert stage == "inference"
    assert "oneDNN" in action or "Tesseract" in action


def test_recommend_tesseract_when_paddle_inference_failed_and_tesseract_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ocr_env.settings, "ocr_enabled", True)
    status = OcrRuntimeStatus(
        ocr_enabled=True,
        paddleocr=EngineRuntimeStatus(
            init_ok=True,
            model_ready=True,
            inference_ok=False,
            error_code="paddleocr_pir_onednn_unimplemented",
        ),
        tesseract=EngineRuntimeStatus(
            package_installed=True,
            binary_available=False,
            init_ok=False,
        ),
    )
    action = ocr_env.build_recommended_action(status, require_inference=True)
    assert "Tesseract" in action
    assert "fallback" in action.lower()


def test_env_flags_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FLAGS_use_mkldnn", "0")
    monkeypatch.setenv("FLAGS_enable_pir_api", "0")
    monkeypatch.setattr(ocr_env.settings, "ocr_enabled", False)
    monkeypatch.setattr(ocr_env, "check_paddleocr_status", lambda **kwargs: EngineRuntimeStatus())
    monkeypatch.setattr(ocr_env, "check_tesseract_status", lambda **kwargs: EngineRuntimeStatus())
    monkeypatch.setattr(ocr_env, "ensure_cache_dir", lambda: (Path("/tmp/ocr_cache"), True))

    status = ocr_env.collect_ocr_runtime_status()
    text = ocr_env.format_status_text(status)
    assert "FLAGS_use_mkldnn: 0" in text
    assert "FLAGS_enable_pir_api: 0" in text


def test_warmup_fails_when_test_image_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import warmup_ocr_models as warmup

    class _FakeEngine:
        _init_error = None
        _init_kwargs = {"lang": "ru"}

        def _ensure_engine(self) -> bool:
            return True

    monkeypatch.setattr(warmup, "PaddleOcrEngine", lambda: _FakeEngine())
    monkeypatch.setattr(
        warmup,
        "run_engine_inference_smoke",
        lambda name: (False, 0, "ConvertPirAttribute2RuntimeAttribute onednn_instruction.cc"),
    )

    assert warmup.warmup_paddle(allow_init_only=False) == 1


def test_warmup_passes_with_allow_init_only(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import warmup_ocr_models as warmup

    class _FakeEngine:
        _init_error = None
        _init_kwargs = {"lang": "ru"}

        def _ensure_engine(self) -> bool:
            return True

    monkeypatch.setattr(warmup, "PaddleOcrEngine", lambda: _FakeEngine())
    monkeypatch.setattr(
        warmup,
        "run_engine_inference_smoke",
        lambda name: (False, 0, "inference failed"),
    )

    assert warmup.warmup_paddle(allow_init_only=True) == 0


def test_apply_paddle_env_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FLAGS_use_mkldnn", raising=False)
    monkeypatch.delenv("FLAGS_enable_pir_api", raising=False)
    monkeypatch.setenv("PADDLE_DISABLE_ONEDNN", "true")
    monkeypatch.setenv("PADDLE_DISABLE_PIR", "true")
    ocr_env.apply_paddle_env_flags()
    assert os.environ.get("FLAGS_use_mkldnn") == "0"
    assert os.environ.get("FLAGS_enable_pir_api") == "0"
