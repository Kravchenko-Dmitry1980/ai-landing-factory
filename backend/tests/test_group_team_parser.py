"""Tests for group team line parser."""

from __future__ import annotations

from app.services.contract_fidelity.team_candidate_validator import is_valid_person_name
from app.services.evidence.group_team_parser import (
    expand_group_block,
    parse_group_header,
    parse_team_blocks,
    parse_team_section_group_aware,
    TeamBlock,
    ParsedPersonName,
)


GROUP_BLOCK = """
12. Егор Быков, Максим Иванков, Алексей Решетников (Алмаз)
Парсинг, анализ данных
• Формирование требований к датасету.
• Анализ тематик и структуры каналов.
• Валидация подготовленных материалов.
• Поддержка второй группы по данным.
"""

SINGLE_BLOCK = """
1. Татьяна Ерюкова — помощник тимлида
Архитектура, кластеризация, парсинг, аналитика
• Переработка архитектуры парсера (многослойная модель).
• Кластеризация BERTopic на датасете 37k постов.
"""


def test_three_names_shared_role_and_bullets() -> None:
    members = parse_team_section_group_aware(GROUP_BLOCK)
    bykov = next(m for m in members if "Быков" in m.name)
    ivankov = next(m for m in members if "Иванков" in m.name)
    reshetnikov = next(m for m in members if "Решетников" in m.name)

    assert bykov.role == "Парсинг, анализ данных"
    assert ivankov.role == "Парсинг, анализ данных"
    assert reshetnikov.role == "Парсинг, анализ данных"
    assert len(bykov.contributions) >= 3
    assert bykov.contributions == ivankov.contributions == reshetnikov.contributions


def test_alias_in_parentheses() -> None:
    names = parse_group_header(
        "12. Егор Быков, Максим Иванков, Алексей Решетников (Алмаз)"
    )
    last = next(n for n in names if "Решетников" in n.name)
    assert last.alias == "Алмаз"


def test_numbered_header_parsed() -> None:
    blocks = parse_team_blocks(GROUP_BLOCK)
    assert len(blocks) == 1
    assert blocks[0].block_index == 12
    assert len(blocks[0].names) == 3


def test_single_person_block_still_works() -> None:
    members = parse_team_section_group_aware(SINGLE_BLOCK)
    assert len(members) == 1
    assert "Ерюкова" in members[0].name
    assert members[0].role
    assert len(members[0].contributions) >= 2


def test_duplicate_person_merge() -> None:
    block_a = TeamBlock(
        names=[ParsedPersonName(name="Егор Быков")],
        shared_role="Роль A",
        shared_contributions=["One"],
    )
    block_b = TeamBlock(
        names=[ParsedPersonName(name="Егор Быков")],
        shared_role="Роль B",
        shared_contributions=["Two"],
    )
    members = expand_group_block(block_a) + expand_group_block(block_b)
    merged = parse_team_section_group_aware(
        "1. Егор Быков\nРоль A\n• One\n1. Егор Быков\nРоль B\n• Two"
    )
    bykov = next(m for m in merged if "Быков" in m.name)
    assert bykov.role
    assert len(bykov.contributions) >= 1


def test_false_positives_rejected() -> None:
    names = parse_group_header("Посты Telegram, Qdrant Cloud, Google Colab")
    assert names == []


def test_no_empty_team_cards_in_group_block() -> None:
    members = parse_team_section_group_aware(GROUP_BLOCK)
    for member in members:
        assert member.name
        assert is_valid_person_name(member.name)
        assert member.role
        assert member.contributions
