"""Setup OCR runtime script tests."""

from __future__ import annotations

from pathlib import Path

from scripts import setup_ocr_runtime as setup_mod


def test_write_env_appends_ocr_keys(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("LLM_ENABLED=false\n", encoding="utf-8")
    count, keys = setup_mod.write_env_keys(env_path)
    text = env_path.read_text(encoding="utf-8")
    assert count > 0
    assert "OCR_ENABLED=false" in text
    assert "OCR_ENGINE=paddleocr" in text
    assert "LLM_ENABLED=false" in text
    assert "OCR_ENABLED" in keys


def test_write_env_preserves_existing_values(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("OCR_ENABLED=true\nOCR_ENGINE=tesseract\n", encoding="utf-8")
    count, keys = setup_mod.write_env_keys(env_path)
    text = env_path.read_text(encoding="utf-8")
    assert "OCR_ENABLED=true" in text
    assert "OCR_ENGINE=tesseract" in text
    assert "OCR_ENABLED" not in keys


def test_pip_env_sets_no_proxy() -> None:
    env = setup_mod.build_pip_env(use_no_proxy=True)
    assert env.get("NO_PROXY") == "*"


def test_socks_proxy_guidance_message() -> None:
    message = "SOCKS proxy detected. Set NO_PROXY=* or install PySocks first."
    assert "SOCKS proxy detected" in message
