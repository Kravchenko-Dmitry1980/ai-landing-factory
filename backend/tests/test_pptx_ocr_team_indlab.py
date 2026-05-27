"""Indlab PPTX slide 25 OCR team integration tests (offline fixtures)."""

from __future__ import annotations

from app.services.evidence.ocr_team_extractor import extract_team_from_ocr_text
from app.services.ocr.postprocess.ocr_team_text_normalizer import (
    detect_team_ocr_section,
    normalize_ocr_team_text,
)

INDLAB_OCR_FIXTURE = """
Команда проекта
Тимлидпроекта
Кравченко Дмитрий
Руководство проектом, архитектура
Участники команды проекта
1. Татьяна Ерюкова — помошниктиылида
Архитектура, кластеризация, парсинг
2. Малицкий Андрей — помощник тимлида
3. Дмитрий Блюхеров
UI, backend-модули
"""


def test_indlab_fixture_team_section_detected() -> None:
    assert detect_team_ocr_section(INDLAB_OCR_FIXTURE)


def test_indlab_fixture_normalization() -> None:
    normalized = normalize_ocr_team_text(INDLAB_OCR_FIXTURE)
    assert "Тимлид проекта" in normalized
    assert "помощник тимлида" in normalized.lower()


def test_indlab_fixture_extracts_multiple_members() -> None:
    result = extract_team_from_ocr_text(INDLAB_OCR_FIXTURE, source_trace="indlab#25")
    names = {m.name for m in result.members}
    assert "Татьяна Ерюкова" in names
    assert len(result.members) >= 2
    tatyana = next(m for m in result.members if m.name == "Татьяна Ерюкова")
    assert "помощник" in tatyana.role.lower()
