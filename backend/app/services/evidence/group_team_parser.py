"""Parse team blocks with shared role/contributions for group name lines."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

from app.schemas.fidelity import TeamMember
from app.services.contract_fidelity.team_candidate_validator import (
    filter_team_members,
    is_valid_person_name,
)

BULLET_RE = re.compile(r"^[\s]*(?:[-•*·]|–)\s+(.+)$")
NUMBERED_RE = re.compile(r"^\d+\.\s+(.+)$")
URL_RE = re.compile(r"\s+https?://\S+")
NAME_ROLE_RE = re.compile(r"^(.+?)\s*[—–-]\s*(.+)$")
ALIAS_RE = re.compile(r"\s*\(([^)]+)\)\s*$")
GROUP_PREFIX_RE = re.compile(
    r"^(?:команда\s+данных|тимлиды?|участники|разработчики)\s*:\s*",
    re.IGNORECASE,
)
BLOCK_START_RE = re.compile(r"^\d+\.\s+")

SKIP_HEADERS = frozenset(
    {
        "команда проекта",
        "тимлид проекта",
        "участники команды проекта",
        "участники",
        "команда",
        "тимлид",
        "роли",
        "разработчики",
    }
)

ROLE_HINTS = (
    "тимлид",
    "помощник",
    "project manager",
    "lead",
    "backend",
    "frontend",
    "devops",
    "qa",
    "архитектор",
    "разработчик",
    "лид",
    "руководитель",
    "engineer",
    "manager",
    "проект",
    "аналитик",
    "тестирован",
    "парсинг",
    "pipeline",
    "devops",
)

SECTION_END_MARKERS = frozenset({"фраза проекта", "используемый технологический стек"})

FALSE_GROUP_MARKERS = frozenset(
    {
        "посты telegram",
        "из telegram",
        "qdrant cloud",
        "google colab",
        "qdrant",
        "bertopic",
        "neo4j",
        "схема обработки данных",
        "векторная бд",
    }
)


class ParsedPersonName(BaseModel):
    name: str
    alias: str = ""


class TeamBlock(BaseModel):
    block_index: int = 0
    raw_header: str = ""
    names: list[ParsedPersonName] = Field(default_factory=list)
    shared_role: str | None = None
    inline_role: str | None = None
    shared_contributions: list[str] = Field(default_factory=list)
    source_location: str | None = None


def parse_group_header(line: str) -> list[ParsedPersonName]:
    """Extract person names from a header line."""
    raw = line.strip()
    if not raw or raw.lower() in SKIP_HEADERS:
        return []

    payload = BLOCK_START_RE.sub("", raw).strip()
    payload = GROUP_PREFIX_RE.sub("", payload).strip()
    if not payload:
        return []

    low_payload = payload.lower()
    if any(marker in low_payload for marker in FALSE_GROUP_MARKERS):
        return []

    role_match = NAME_ROLE_RE.match(payload)
    if role_match:
        payload = role_match.group(1).strip()

    if "," not in payload:
        person = _parse_single_name(payload)
        return [person] if person else []

    names = _split_group_names(payload)
    return names


def detect_shared_role(lines_after_header: list[str]) -> str | None:
    for line in lines_after_header:
        stripped = line.strip()
        if not stripped or _is_url_line(stripped):
            continue
        if BULLET_RE.match(stripped) or BLOCK_START_RE.match(stripped):
            return None
        if _looks_like_role(stripped) or (
            len(stripped) < 120 and not is_valid_person_name(_strip_urls(stripped))
        ):
            return stripped
        if is_valid_person_name(_strip_urls(stripped)):
            return None
    return None


def collect_shared_contributions(lines_after_role: list[str]) -> list[str]:
    contributions: list[str] = []
    for line in lines_after_role:
        stripped = line.strip()
        if not stripped:
            continue
        if BLOCK_START_RE.match(stripped) or stripped.lower() in SECTION_END_MARKERS:
            break
        if _is_url_line(stripped):
            continue
        bullet = BULLET_RE.match(stripped)
        if bullet:
            contributions.append(bullet.group(1).strip())
            continue
        if is_valid_person_name(_strip_urls(stripped)) and not contributions:
            break
        if stripped.endswith(";") or len(stripped) > 40:
            contributions.extend(_split_contributions(stripped))
        elif not _looks_like_role(stripped) or contributions:
            contributions.append(stripped)
    return [c for c in contributions if c]


def parse_team_blocks(text: str) -> list[TeamBlock]:
    lines = text.splitlines()
    blocks: list[TeamBlock] = []
    i = 0

    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped:
            i += 1
            continue
        if stripped.lower() in SKIP_HEADERS or stripped.lower() in SECTION_END_MARKERS:
            i += 1
            continue

        names = parse_group_header(stripped)
        if not names and is_valid_person_name(_strip_urls(stripped)):
            names = [_parse_single_name(_strip_urls(stripped))]  # type: ignore[list-item]
            names = [n for n in names if n]

        if not names:
            i += 1
            continue

        header_payload = BLOCK_START_RE.sub("", stripped).strip()
        inline_role = None
        role_match = NAME_ROLE_RE.match(header_payload)
        if role_match and len(names) == 1:
            inline_role = role_match.group(2).strip()

        block_index = _extract_block_index(stripped) or len(blocks) + 1
        i += 1

        while i < len(lines) and _is_url_line(lines[i].strip()):
            i += 1

        remaining = lines[i:]
        shared_role = inline_role or detect_shared_role(remaining)

        role_offset = 0
        if shared_role and not inline_role:
            for j, line in enumerate(remaining):
                if line.strip() == shared_role:
                    role_offset = j + 1
                    break

        contributions = collect_shared_contributions(remaining[role_offset:])
        i += role_offset + _lines_consumed_for_contributions(
            remaining[role_offset:], contributions
        )

        blocks.append(
            TeamBlock(
                block_index=block_index,
                raw_header=stripped,
                names=names,
                shared_role=shared_role,
                inline_role=inline_role,
                shared_contributions=contributions,
                source_location=f"block:{block_index}",
            )
        )

    return blocks


def expand_group_block(block: TeamBlock) -> list[TeamMember]:
    role = block.shared_role or block.inline_role or ""
    contribs = list(block.shared_contributions)
    return [
        TeamMember(
            name=person.name,
            role=role,
            project_area=person.alias or "",
            contributions=list(contribs),
        )
        for person in block.names
    ]


def merge_team_members(members: list[TeamMember]) -> list[TeamMember]:
    merged: dict[str, TeamMember] = {}
    for member in members:
        key = member.name.lower()
        existing = merged.get(key)
        if existing is None:
            merged[key] = member
            continue
        merged[key] = TeamMember(
            name=existing.name,
            role=existing.role or member.role,
            project_area=existing.project_area or member.project_area,
            contributions=list(
                dict.fromkeys(existing.contributions + member.contributions)
            ),
        )
    return filter_team_members(list(merged.values()))


def parse_team_section_group_aware(text: str) -> list[TeamMember]:
    if not text.strip():
        return []
    blocks = parse_team_blocks(text)
    members: list[TeamMember] = []
    for block in blocks:
        members.extend(expand_group_block(block))
    return merge_team_members(members)


def group_expansion_trace(text: str) -> list[dict[str, str]]:
    trace: list[dict[str, str]] = []
    for block in parse_team_blocks(text):
        if len(block.names) <= 1:
            continue
        names = ", ".join(p.name for p in block.names)
        role = block.shared_role or block.inline_role or ""
        trace.append(
            {
                "header": block.raw_header,
                "names": names,
                "shared_role": role,
                "contributions_count": str(len(block.shared_contributions)),
            }
        )
    return trace


def _parse_single_name(text: str) -> ParsedPersonName | None:
    cleaned = _strip_urls(text.strip())
    alias = ""
    alias_match = ALIAS_RE.search(cleaned)
    if alias_match:
        alias = alias_match.group(1).strip()
        cleaned = ALIAS_RE.sub("", cleaned).strip()
    if not is_valid_person_name(cleaned):
        return None
    return ParsedPersonName(name=cleaned, alias=alias)


def _split_group_names(text: str) -> list[ParsedPersonName]:
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if not parts:
        return []
    low_joined = ", ".join(parts).lower()
    if any(marker in low_joined for marker in FALSE_GROUP_MARKERS):
        return []

    names: list[ParsedPersonName] = []
    for idx, part in enumerate(parts):
        alias = ""
        if idx == len(parts) - 1:
            alias_match = ALIAS_RE.search(part)
            if alias_match:
                alias = alias_match.group(1).strip()
                part = ALIAS_RE.sub("", part).strip()
        cleaned = _strip_urls(part)
        if is_valid_person_name(cleaned):
            names.append(ParsedPersonName(name=cleaned, alias=alias))
    return names


def _looks_like_role(line: str) -> bool:
    low = line.lower()
    if len(line) > 120:
        return False
    if is_valid_person_name(_strip_urls(line)):
        return False
    return any(h in low for h in ROLE_HINTS) or "," in line


def _split_contributions(text: str) -> list[str]:
    parts = re.split(r";\s*", text)
    return [p.strip() for p in parts if p.strip()]


def _strip_urls(text: str) -> str:
    return URL_RE.sub("", text).strip()


def _is_url_line(line: str) -> bool:
    return bool(URL_RE.fullmatch(line.strip()) or line.strip().startswith("http"))


def _extract_block_index(line: str) -> int | None:
    match = re.match(r"^(\d+)\.", line.strip())
    return int(match.group(1)) if match else None


def _lines_consumed_for_contributions(lines: list[str], contributions: list[str]) -> int:
    if not contributions:
        return 0
    count = 0
    matched = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            count += 1
            continue
        if BLOCK_START_RE.match(stripped) or stripped.lower() in SECTION_END_MARKERS:
            break
        if _is_url_line(stripped):
            count += 1
            continue
        count += 1
        matched += 1
        if matched >= len(contributions):
            break
    return count
