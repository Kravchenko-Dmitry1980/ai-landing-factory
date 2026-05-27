"""Tests for OCR team text normalizer."""

from __future__ import annotations

from app.services.ocr.postprocess.ocr_team_text_normalizer import (
    detect_team_ocr_section,
    normalize_ocr_role,
    normalize_ocr_team_text,
)


def test_timlid_project_glue_fixed() -> None:
    assert "Тимлид проекта" in normalize_ocr_team_text("Тимлидпроекта")


def test_assistant_role_glue_fixed() -> None:
    normalized = normalize_ocr_team_text("Татьяна Ерюкова — помошниктиылида:")
    assert "помощник тимлида" in normalized.lower()


def test_symbols_cleanup() -> None:
    normalized = normalize_ocr_team_text("Команда проекта | `Qdrant` © test")
    assert "|" not in normalized
    assert "`" not in normalized
    assert "©" not in normalized


def test_team_section_markers_detected() -> None:
    assert detect_team_ocr_section("Команда проекта\nТимлид проекта")
    assert detect_team_ocr_section("участники команды проекта")
    assert not detect_team_ocr_section("Технологический стек")


def test_normalize_ocr_role_fuzzy() -> None:
    assert "помощник" in normalize_ocr_role("помошник тимлида").lower()
    assert normalize_ocr_role("тимлид проекта") == "тимлид проекта"
