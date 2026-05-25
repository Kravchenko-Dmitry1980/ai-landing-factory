"""Tests for strict team candidate validation."""

from __future__ import annotations

import pytest

from app.services.contract_fidelity.team_candidate_validator import (
    filter_team_candidates,
    is_team_context,
    is_valid_person_name,
    is_valid_team_role,
    validate_team_candidate,
)
from app.schemas.evidence import TeamMemberCandidate

VALID_NAMES = (
    "Кравченко Дмитрий",
    "Кравченко Дмитрий Александрович",
    "Бугров Алексей",
    "Ерюкова Мария",
    "Глазунова Анна",
)

INVALID_NAMES = (
    "Посты Telegram",
    "Из Telegram",
    "Схема обработки данных",
    "Векторная БД",
    "Пользовательский запрос",
    "Семантический поиск",
    "Темы BERTopic",
    "Граф новостей",
    "Qdrant Cloud",
    "Telegram API",
    "Google Colab",
)


@pytest.mark.parametrize("name", VALID_NAMES)
def test_valid_person_names(name: str) -> None:
    assert is_valid_person_name(name)


@pytest.mark.parametrize("name", INVALID_NAMES)
def test_invalid_person_names(name: str) -> None:
    assert not is_valid_person_name(name)


def test_team_role_markers() -> None:
    assert is_valid_team_role("тимлид проекта")
    assert is_valid_team_role("backend-разработчик")
    assert not is_valid_team_role("Посты Telegram")


def test_team_context_detection() -> None:
    assert is_team_context("Команда проекта", "Участники команды")
    assert not is_team_context("Схема обработки данных", "Посты Telegram")


def test_context_acceptance_rules() -> None:
    assert validate_team_candidate(
        "Иванов Иван",
        section_hint="Команда проекта",
        in_team_section=True,
    )
    assert validate_team_candidate(
        "Иванов Иван",
        role="backend-разработчик",
        section_hint="Slide 5",
        source_text="Иванов Иван — backend-разработчик",
    )
    assert not validate_team_candidate(
        "Посты Telegram",
        section_hint="Схема обработки данных",
        source_text="Посты Telegram",
    )


def test_filter_team_candidates() -> None:
    candidates = [
        TeamMemberCandidate(name="Кравченко Дмитрий", role="Тимлид"),
        TeamMemberCandidate(name="Посты Telegram", role=""),
    ]
    filtered = filter_team_candidates(candidates, in_team_section=True)
    assert len(filtered) == 1
    assert filtered[0].name == "Кравченко Дмитрий"
