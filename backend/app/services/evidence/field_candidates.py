"""Assign LandingContract field candidates to evidence items."""

from __future__ import annotations

import re

from app.schemas.evidence import EvidenceItem
from app.services.contract_fidelity.pptx_team_markers import (
    slide_title_has_team_marker,
    text_has_team_markers,
)

FIELD_RULES: list[tuple[str, list[str]]] = [
    ("title", ["проект:", "название проекта", "slide 1"]),
    ("client", ["заказчик", "ооо", "ао", "ип", "компания «"]),
    ("timeline", ["сроки проекта", "сроки:", "01.", "02.", "03.", "04.", "05.", "06."]),
    ("essence", [
        "цель проекта", "цели проекта", "описание проекта",
        "главная цель", "суть проекта", "контекст и цель",
    ]),
    ("tasks", [
        "задачи проекта", "задачи", "этапы", "фаза", "разработка",
        "реализация", "этапы работы", "подключить и настроить",
    ]),
    ("purpose", [
        "для чего", "назначение", "польза проекта", "обеспечить",
        "повысить", "снизить", "автоматизировать", "цель:",
    ]),
    ("inputs", [
        "входные данные", "вход", "источники данных", "подготовка данных",
        "требования к входным", "исходные данные", "telegram api",
        "кадры", "видео", "документы", "сообщения",
    ]),
    ("outputs", [
        "выходные данные", "выход", "демо", "прототип", "модель",
        "веб-приложение", "дашборд", "интерфейс", "streamlit",
    ]),
    ("results", [
        "итоги", "результаты", "достигнуто", "реализовано",
        "метрики и результаты", "полученные результаты", "показатели",
    ]),
    ("outlook", [
        "рекомендации", "перспектива", "дальнейшее развитие",
        "следующий этап", "roadmap", "направления развития", "планы по",
    ]),
    ("tech_stack", [
        "технологический стек", "архитектура системы", "архитектура пайплайна",
        "stack", "pipeline", "ml pipeline",
    ]),
    ("team", [
        "команда проекта",
        "команда управления",
        "участники команды",
        "роли в проекте",
        "тимлид:",
        "помощник тимлида:",
    ]),
    ("modules", [
        "шаг 1", "шаг 2", "pipeline", "архитектура", "модули",
        "семантический поиск", "темы (", "граф новостей",
        "пользовательский запрос", "обнаружение", "идентификация",
    ]),
]

GENERIC_TITLES = frozenset({
    "проект", "презентация", "слайд", "landing", "slide 1", "slide 1:",
})


def classify_field_candidates(item: EvidenceItem) -> list[str]:
    """Return field names this evidence may support."""
    text = item.normalized_text or item.text
    normalized = text.lower().replace("\u00a0", " ")
    candidates: list[str] = []

    for field_name, markers in FIELD_RULES:
        if any(marker in normalized for marker in markers):
            candidates.append(field_name)

    if item.location_type == "slide" and item.location_index == 1:
        if "title" not in candidates:
            candidates.append("title")
        if "timeline" not in candidates and re.search(r"\d{2}\.\d{2}", text):
            candidates.append("timeline")

    if "задачи проекта" in normalized:
        if "tasks" not in candidates:
            candidates.append("tasks")

    if "направления развития" in normalized or "планы по расширению" in normalized:
        if "outlook" not in candidates:
            candidates.append("outlook")

    if item.technologies:
        if "tech_stack" not in candidates:
            candidates.append("tech_stack")

    if item.people or text_has_team_markers(text):
        if "team" not in candidates:
            candidates.append("team")

    if item.location_type == "slide" and slide_title_has_team_marker(
        item.location_label, text
    ):
        if "team" not in candidates:
            candidates.append("team")

    if item.location_type == "table":
        for field in ("inputs", "outputs", "tasks"):
            if field not in candidates:
                candidates.append(field)

    return list(dict.fromkeys(candidates))


def is_generic_title(value: str) -> bool:
    cleaned = value.strip().lower().rstrip(":")
    return not cleaned or cleaned in GENERIC_TITLES or len(cleaned) < 4
