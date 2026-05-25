"""Deterministic people / team extraction from evidence text."""

from __future__ import annotations

import re

from app.schemas.evidence import TeamMemberCandidate
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

TECH_NAMES = {v[1].lower() for v in TECHNOLOGY_ENTRIES.values()}
TECH_NAMES.update(k.lower() for k in TECHNOLOGY_ENTRIES)


def _is_person_name(line: str) -> bool:
    line = line.strip()
    if len(line) < 5 or len(line) > 80:
        return False
    if line.lower() in TECH_NAMES:
        return False
    if any(tok in line.lower() for tok in ("api", "docker", "python", "slide")):
        return False
    return bool(FIO_RE.match(line))


def extract_people_from_text(
    text: str,
    *,
    source_ref: str = "",
) -> list[TeamMemberCandidate]:
    """Extract team member candidates from a text block."""
    members: list[TeamMemberCandidate] = []
    seen: set[str] = set()

    for match in LEAD_RE.finditer(text):
        name = match.group(1).strip()
        if name and name.lower() not in seen:
            seen.add(name.lower())
            members.append(
                TeamMemberCandidate(
                    name=name,
                    role="Тимлид",
                    source_refs=[source_ref] if source_ref else [],
                )
            )

    for match in ASSISTANT_RE.finditer(text):
        name = match.group(1).strip()
        if name and name.lower() not in seen:
            seen.add(name.lower())
            members.append(
                TeamMemberCandidate(
                    name=name,
                    role="Помощник тимлида",
                    source_refs=[source_ref] if source_ref else [],
                )
            )

    for line in text.splitlines():
        line = line.strip()
        role_match = ROLE_LINE_RE.match(line)
        if role_match:
            role = role_match.group(1).strip()
            name = role_match.group(2).strip()
            if name and name.lower() not in seen:
                seen.add(name.lower())
                members.append(
                    TeamMemberCandidate(
                        name=name,
                        role=role,
                        source_refs=[source_ref] if source_ref else [],
                    )
                )
            continue
        if _is_person_name(line) and line.lower() not in seen:
            seen.add(line.lower())
            members.append(
                TeamMemberCandidate(
                    name=line,
                    role="",
                    source_refs=[source_ref] if source_ref else [],
                )
            )

    return members
