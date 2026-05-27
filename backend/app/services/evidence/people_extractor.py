"""Deterministic people / team extraction from evidence text."""

from __future__ import annotations

import re

from app.schemas.evidence import TeamMemberCandidate
from app.services.contract_fidelity.pptx_team_markers import text_has_team_markers
from app.services.contract_fidelity.team_parser import _split_name_list, _strip_urls
from app.services.contract_fidelity.team_parser import _split_name_list, _strip_urls
from app.services.evidence.group_team_parser import (
    parse_team_blocks,
    expand_group_block,
    merge_team_members as merge_group_team_members,
)
from app.services.contract_fidelity.team_candidate_validator import (
    filter_team_candidates,
    is_team_context,
    is_valid_person_name,
    is_valid_team_role,
    validate_team_candidate,
    validate_team_candidate_with_reason,
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


TABLE_ROW_RE = re.compile(r"^(.+?)\s*\|\s*(.+?)(?:\s*\|\s*(.+))?$")


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
    team_ctx = in_team_section or is_team_context(section_hint, text) or text_has_team_markers(text)

    if team_ctx:
        from app.services.ocr.postprocess.ocr_team_text_normalizer import detect_team_ocr_section

        if detect_team_ocr_section(text):
            from app.services.evidence.ocr_team_extractor import extract_team_from_ocr_text

            ocr_result = extract_team_from_ocr_text(text, source_trace=source_ref)
            if ocr_result.members:
                return ocr_result.members

    if team_ctx and text_has_team_markers(text):
        block_members: list[TeamMemberCandidate] = []
        for block in parse_team_blocks(text):
            for member in expand_group_block(block):
                block_members.append(
                    TeamMemberCandidate(
                        name=member.name,
                        role=member.role,
                        project_area=member.project_area,
                        contributions=list(member.contributions),
                        source_refs=[source_ref] if source_ref else [],
                    )
                )
        if block_members:
            return filter_team_candidates(
                merge_group_candidates(block_members),
                section_hint=section_hint,
                source_text=text,
                in_team_section=team_ctx,
            )

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
        if not line or line.lower().startswith(("команда проекта", "участники команды", "тимлид проекта")):
            continue

        table_match = TABLE_ROW_RE.match(line)
        if table_match and team_ctx:
            name_cell = table_match.group(1).strip()
            role_cell = (table_match.group(2) or "").strip()
            area_cell = (table_match.group(3) or "").strip()
            if is_valid_person_name(name_cell):
                _add(name_cell, role_cell or area_cell)
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


def diagnose_people_from_text(
    text: str,
    *,
    section_hint: str = "",
    in_team_section: bool = False,
) -> tuple[list[TeamMemberCandidate], list[tuple[str, str, str]], list[tuple[str, str, str]]]:
    """Return (accepted, rejected_with_reason, raw_attempts)."""
    accepted: list[TeamMemberCandidate] = []
    rejected: list[tuple[str, str, str]] = []
    raw: list[tuple[str, str, str]] = []
    team_ctx = in_team_section or is_team_context(section_hint, text) or text_has_team_markers(text)

    def _consider(name: str, role: str = "") -> None:
        name = _strip_urls(name.strip())
        if not name:
            return
        ok, reason = validate_team_candidate_with_reason(
            name,
            role=role,
            section_hint=section_hint,
            source_text=text,
            in_team_section=team_ctx,
        )
        raw.append((name, role, reason))
        if ok:
            accepted.append(TeamMemberCandidate(name=name, role=role, source_refs=[]))
        else:
            rejected.append((name, role, reason))

    for match in LEAD_RE.finditer(text):
        _consider(match.group(1).strip(), "Тимлид")
    for match in ASSISTANT_RE.finditer(text):
        _consider(match.group(1).strip(), "Помощник тимлида")

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        table_match = TABLE_ROW_RE.match(line)
        if table_match and team_ctx:
            name_cell = table_match.group(1).strip()
            role_cell = (table_match.group(2) or "").strip()
            if is_valid_person_name(name_cell):
                _consider(name_cell, role_cell)
            continue
        role_match = ROLE_LINE_RE.match(line)
        if role_match:
            _consider(role_match.group(2).strip(), role_match.group(1).strip())
            continue
        cleaned = _strip_urls(line)
        numbered = NUMBERED_RE.match(cleaned)
        payload = numbered.group(1).strip() if numbered else cleaned
        name_role = NAME_ROLE_RE.match(payload)
        role = ""
        if name_role:
            payload = name_role.group(1).strip()
            role = name_role.group(2).strip()
        if is_valid_person_name(payload):
            _consider(payload, role)

    filtered = filter_team_candidates(
        accepted,
        section_hint=section_hint,
        source_text=text,
        in_team_section=team_ctx,
    )
    return filtered, rejected, raw


def merge_group_candidates(
    members: list[TeamMemberCandidate],
) -> list[TeamMemberCandidate]:
    merged: dict[str, TeamMemberCandidate] = {}
    for member in members:
        key = member.name.lower()
        existing = merged.get(key)
        if existing is None:
            merged[key] = member
            continue
        merged[key] = TeamMemberCandidate(
            name=existing.name,
            role=existing.role or member.role,
            project_area=existing.project_area or member.project_area,
            contributions=list(
                dict.fromkeys(existing.contributions + member.contributions)
            ),
            source_refs=list(dict.fromkeys(existing.source_refs + member.source_refs)),
        )
    return list(merged.values())
