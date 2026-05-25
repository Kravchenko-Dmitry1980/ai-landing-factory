"""Deterministic people / team extraction from evidence text."""

from __future__ import annotations

import re

from app.schemas.evidence import TeamMemberCandidate
from app.services.contract_fidelity.team_parser import (
    _is_valid_name,
    _split_name_list,
    _strip_urls,
)
from app.services.evidence.technology_dictionary import TECHNOLOGY_ENTRIES

FIO_RE = re.compile(
    r"^[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?$"
)
LEAD_RE = re.compile(r"Тимлид\s*:\s*(.+?)(?:\n|$)", re.IGNORECASE)
ASSISTANT_RE = re.compile(
    r"Помощник\s+тимлида\s*:\s*(.+?)(?:\n|$)", re.IGNORECASE
)
ROLE_LINE_RE = re.compile(
    r"^(Тимлид|Помощник тимлида|Участник|Разработчик|Аналитик)\s*:\s*(.+)$",
    re.IGNORECASE,
)
NUMBERED_RE = re.compile(r"^\d+\.\s+(.+)$")
NAME_ROLE_RE = re.compile(r"^(.+?)\s*[—–-]\s*(.+)$")

TECH_NAMES = {v[1].lower() for v in TECHNOLOGY_ENTRIES.values()}
TECH_NAMES.update(k.lower() for k in TECHNOLOGY_ENTRIES)
TECH_NAMES.update(
    {
        "qdrant",
        "bertopic",
        "neo4j",
        "python",
        "telegram",
        "openai",
        "react",
        "docker",
    }
)


def _is_person_name(line: str) -> bool:
    line = _strip_urls(line.strip())
    if len(line) < 5 or len(line) > 80:
        return False
    if line.lower() in TECH_NAMES:
        return False
    if any(tok in line.lower() for tok in ("api", "docker", "python", "slide")):
        return False
    return _is_valid_name(line) or bool(FIO_RE.match(line))


def extract_people_from_text(
    text: str,
    *,
    source_ref: str = "",
) -> list[TeamMemberCandidate]:
    """Extract team member candidates from a text block."""
    members: list[TeamMemberCandidate] = []
    seen: set[str] = set()

    def _add(name: str, role: str = "") -> None:
        name = _strip_urls(name.strip())
        if not name or name.lower() in seen:
            return
        if not _is_person_name(name):
            return
        seen.add(name.lower())
        members.append(
            TeamMemberCandidate(
                name=name,
                role=role,
                source_refs=[source_ref] if source_ref else [],
            )
        )

    for match in LEAD_RE.finditer(text):
        _add(match.group(1).strip(), "Тимлид")

    for match in ASSISTANT_RE.finditer(text):
        _add(match.group(1).strip(), "Помощник тимлида")

    for line in text.splitlines():
        line = line.strip()
        if not line or line.lower().startswith(("команда", "участники", "тимлид проекта")):
            continue

        role_match = ROLE_LINE_RE.match(line)
        if role_match:
            _add(role_match.group(2).strip(), role_match.group(1).strip())
            continue

        cleaned = _strip_urls(line)
        numbered = NUMBERED_RE.match(cleaned)
        payload = numbered.group(1).strip() if numbered else cleaned

        inline_role = ""
        name_role = NAME_ROLE_RE.match(payload)
        if name_role:
            payload = name_role.group(1).strip()
            inline_role = name_role.group(2).strip()

        if "," in payload:
            for name in _split_name_list(payload):
                _add(name, inline_role)
            continue

        if _is_person_name(payload):
            _add(payload, inline_role)

    return members
