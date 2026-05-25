"""Deterministic people / team extraction from evidence text."""

from __future__ import annotations

import re

from app.schemas.evidence import TeamMemberCandidate
from app.services.contract_fidelity.team_parser import _split_name_list, _strip_urls
from app.services.contract_fidelity.team_candidate_validator import (
    filter_team_candidates,
    is_team_context,
    is_valid_person_name,
    is_valid_team_role,
    validate_team_candidate,
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


def extract_people_from_text(
    text: str,
    *,
    source_ref: str = "",
    section_hint: str = "",
    in_team_section: bool = False,
) -> list[TeamMemberCandidate]:
    """Extract team member candidates from a text block."""
    members: list[TeamMemberCandidate] = []
    seen: set[str] = set()
    team_ctx = in_team_section or is_team_context(section_hint, text)

    def _add(name: str, role: str = "") -> None:
        name = _strip_urls(name.strip())
        if not name or name.lower() in seen:
            return
        if not validate_team_candidate(
            name,
            role=role,
            section_hint=section_hint,
            source_text=text,
            in_team_section=team_ctx,
        ):
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

        if not team_ctx and inline_role and not is_valid_team_role(inline_role):
            inline_role = ""

        if "," in payload:
            for name in _split_name_list(payload):
                if is_valid_person_name(name):
                    _add(name, inline_role)
            continue

        if is_valid_person_name(payload):
            _add(payload, inline_role)

    return filter_team_candidates(
        members,
        section_hint=section_hint,
        source_text=text,
        in_team_section=team_ctx,
    )
