"""Tests for fuzzy OCR team extraction."""

from __future__ import annotations

from app.services.evidence.ocr_team_extractor import extract_team_from_ocr_text


def test_tatyana_eryukova_assistant_role() -> None:
    text = """
    Команда проекта
    Тимлидпроекта
    1. Татьяна Ерюкова — помошниктиылида
    """
    result = extract_team_from_ocr_text(text, source_trace="test#ocr")
    names = {m.name for m in result.members}
    assert "Татьяна Ерюкова" in names
    tatyana = next(m for m in result.members if m.name == "Татьяна Ерюкова")
    assert "помощник" in tatyana.role.lower()
    assert "тимлида" in tatyana.role.lower()


def test_no_hallucinated_members_on_noise() -> None:
    text = """
    Команда проекта
    Qdrant Cloud pipeline Neo4j Telegram posts
    """
    result = extract_team_from_ocr_text(text)
    assert not result.members
    assert not any("Qdrant" in w for w in result.warnings if "rejected" in w.lower())


def test_group_line_extracts_three_names() -> None:
    text = """
    Команда проекта
    Участники: Егор Быков, Максим Иванков, Алексей Решетников — разработка
    """
    result = extract_team_from_ocr_text(text)
    names = {m.name for m in result.members}
    assert "Егор Быков" in names
    assert "Максим Иванков" in names
    assert "Алексей Решетников" in names


def test_false_positives_not_persons() -> None:
    text = """
    Команда проекта
    Qdrant — векторная БД
    Telegram — канал
    Neo4j — граф
    """
    result = extract_team_from_ocr_text(text)
    names = {m.name.lower() for m in result.members}
    assert "qdrant" not in names
    assert "telegram" not in names
    assert "neo4j" not in names


def test_rejected_invalid_name_warning() -> None:
    text = """
    Команда проекта
    Тимлид проекта
    Xx yy zz — тимлид
    """
    result = extract_team_from_ocr_text(text)
    assert any("rejected" in r[2] for r in result.rejected) or not result.members
