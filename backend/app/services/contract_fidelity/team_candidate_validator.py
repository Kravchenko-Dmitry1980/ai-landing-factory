"""Strict validation for team member candidates (false positive guard)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.schemas.evidence import TeamMemberCandidate
from app.schemas.fidelity import TeamMember

PERSON_NAME_RE = re.compile(
    r"^[А-ЯЁ][а-яё-]+(?:\s+[А-ЯЁ][а-яё-]+){1,2}$"
)

PREPOSITION_START = frozenset({"из", "для", "по", "на", "в", "с", "от", "к", "у", "о", "об"})

STOP_WORDS = frozenset(
    {
        "telegram",
        "qdrant",
        "bertopic",
        "neo4j",
        "api",
        "cloud",
        "google",
        "colab",
        "посты",
        "пост",
        "из",
        "схема",
        "данные",
        "векторная",
        "бд",
        "пользовательский",
        "запрос",
        "новости",
        "темы",
        "граф",
        "сущности",
        "обработка",
        "пайплайн",
        "семантический",
        "поиск",
        "индексация",
        "кластеризация",
        "классификация",
        "дайджест",
        "дашборд",
        "backend",
        "frontend",
        "docker",
        "python",
        "redis",
        "postgres",
        "streamlit",
        "openai",
        "react",
        "slide",
        "канал",
        "каналы",
        "сообщение",
        "сообщения",
        "корпус",
        "чанк",
        "чанки",
        "эмбеддинг",
        "модель",
        "модели",
        "pipeline",
        "архитектура",
        "система",
        "платформа",
        "интерфейс",
        "прототип",
    }
)

TEAM_CONTEXT_HINTS = (
    "команда",
    "участник",
    "тимлид",
    "разработчик",
    "исполнитель",
    "помощник тимлида",
)

ROLE_MARKERS = (
    "тимлид",
    "помощник тимлида",
    "разработчик",
    "аналитик",
    "дизайнер",
    "frontend",
    "backend",
    "ml engineer",
    "data scientist",
    "qa",
    "project manager",
    "руководитель",
    "архитектор",
    "engineer",
    "devops",
    "лид",
    "тестирован",
    "стажер",
    "стажёр",
)


@dataclass(frozen=True)
class TeamCandidateContext:
    section_hint: str = ""
    source_text: str = ""
    role: str = ""
    in_team_section: bool = False


def is_valid_person_name(text: str) -> bool:
    """Return True if text looks like a Russian person name (2–3 words)."""
    name = _normalize_name(text)
    if not name:
        return False

    words = name.split()
    if len(words) not in (2, 3):
        return False

    if words[0].lower() in PREPOSITION_START:
        return False

    if not PERSON_NAME_RE.match(name):
        return False

    if re.search(r"[A-Za-z]", name):
        return False

    words_lower = {w.lower() for w in words}
    if words_lower & STOP_WORDS:
        return False

    lowered = name.lower()
    for stop in STOP_WORDS:
        if " " in stop and stop in lowered:
            return False

    return True


def is_valid_team_role(text: str) -> bool:
    if not text or len(text) > 120:
        return False
    low = text.lower()
    if is_valid_person_name(text):
        return False
    return any(marker in low for marker in ROLE_MARKERS)


def is_team_context(section_hint: str, source_text: str = "") -> bool:
    blob = f"{section_hint}\n{source_text[:400]}".lower()
    return any(hint in blob for hint in TEAM_CONTEXT_HINTS)


def validate_team_candidate(
    name: str,
    *,
    role: str = "",
    section_hint: str = "",
    source_text: str = "",
    in_team_section: bool = False,
) -> bool:
    if not is_valid_person_name(name):
        return False

    if in_team_section or is_team_context(section_hint, source_text):
        return True

    if role and is_valid_team_role(role):
        return True

    if _has_inline_role_marker(name, source_text):
        return True

    return False


def validate_team_member(member: TeamMember) -> bool:
    return validate_team_candidate(
        member.name,
        role=member.role,
        source_text=member.project_area,
        in_team_section=True,
    )


def filter_team_candidates(
    candidates: list[TeamMemberCandidate],
    *,
    section_hint: str = "",
    source_text: str = "",
    in_team_section: bool = False,
) -> list[TeamMemberCandidate]:
    out: list[TeamMemberCandidate] = []
    seen: set[str] = set()
    for candidate in candidates:
        if not validate_team_candidate(
            candidate.name,
            role=candidate.role,
            section_hint=section_hint,
            source_text=source_text,
            in_team_section=in_team_section,
        ):
            continue
        key = candidate.name.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(candidate)
    return out


def filter_team_members(members: list[TeamMember]) -> list[TeamMember]:
    out: list[TeamMember] = []
    seen: set[str] = set()
    for member in members:
        if not validate_team_member(member):
            continue
        key = member.name.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(member)
    return out


def _normalize_name(text: str) -> str:
    text = re.sub(r"\s+https?://\S+", "", text.strip())
    text = re.sub(r"\s*\([^)]+\)\s*$", "", text)
    text = re.sub(r"^\d+\.\s+", "", text)
    if " — " in text:
        text = text.split(" — ", 1)[0].strip()
    elif " - " in text:
        text = text.split(" - ", 1)[0].strip()
    return text.strip()


def _has_inline_role_marker(name: str, source_text: str) -> bool:
    if " — " in name or " - " in name:
        role_part = name.split(" — ", 1)[-1] if " — " in name else name.split(" - ", 1)[-1]
        return is_valid_team_role(role_part)
    for line in source_text.splitlines()[:6]:
        if name in line and (" — " in line or " - " in line):
            role_part = line.split(" — ", 1)[-1] if " — " in line else line.split(" - ", 1)[-1]
            if is_valid_team_role(role_part):
                return True
    return False
