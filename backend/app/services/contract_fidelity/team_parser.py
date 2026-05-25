"""Parse team members from structured landing team section."""

from __future__ import annotations

import re

from app.schemas.fidelity import TeamMember

NAME_RE = re.compile(
    r"^[А-ЯЁA-Z][а-яёa-z]+(?:\s+[А-ЯЁA-Z][а-яёa-z]+){1,2}$"
)
BULLET_RE = re.compile(r"^[\s]*(?:[-•*·]|–)\s+(.+)$")
NUMBERED_RE = re.compile(r"^\d+\.\s+(.+)$")
URL_RE = re.compile(r"\s+https?://\S+")
NAME_ROLE_RE = re.compile(r"^(.+?)\s*[—–-]\s*(.+)$")
ALIAS_RE = re.compile(r"\s*\([^)]+\)\s*$")

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

TECH_NAME_BLOCKLIST = frozenset(
    {
        "qdrant",
        "bertopic",
        "neo4j",
        "python",
        "telegram",
        "openai",
        "react",
        "docker",
        "redis",
        "postgres",
        "streamlit",
        "fastapi",
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
)


def parse_team_section(text: str) -> list[TeamMember]:
    """Parse team block into structured members."""
    if not text.strip():
        return []

    members: list[TeamMember] = []
    seen: set[str] = set()
    for block in _split_member_blocks(text):
        for member in _parse_member_blocks(block):
            key = member.name.lower()
            if key in seen:
                continue
            seen.add(key)
            members.append(member)

    return members


def team_to_bullets(members: list[TeamMember]) -> list[str]:
    """Serialize team for contract block bullets."""
    lines: list[str] = []
    for m in members:
        header = m.name
        if m.role:
            header += f" — {m.role}"
        if m.project_area:
            header += f" ({m.project_area})"
        lines.append(header)
        for c in m.contributions[:5]:
            lines.append(f"  · {c}")
    return lines


def _split_member_blocks(text: str) -> list[str]:
    lines = text.splitlines()
    blocks: list[str] = []
    current: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.lower() in SKIP_HEADERS:
            continue
        if URL_RE.fullmatch(stripped) or stripped.startswith("http"):
            if current:
                current.append(stripped)
            continue

        starts = _member_starts(stripped)
        if starts:
            if current:
                blocks.append("\n".join(current))
            if len(starts) == 1:
                current = [starts[0]]
            else:
                for block in starts[:-1]:
                    blocks.append(block)
                current = [starts[-1]]
            continue

        if current:
            current.append(stripped)

    if current:
        blocks.append("\n".join(current))
    return blocks


def _member_starts(line: str) -> list[str]:
    """Return one or more block-start lines for a source line."""
    cleaned = _strip_urls(line)
    numbered = NUMBERED_RE.match(cleaned)
    payload = numbered.group(1).strip() if numbered else cleaned

    role_match = NAME_ROLE_RE.match(payload)
    if role_match:
        name_part = role_match.group(1).strip()
        role = role_match.group(2).strip()
        names = _split_name_list(name_part)
        if names:
            return [f"{name}\n{role}" if role else name for name in names]
        if _is_valid_name(name_part):
            return [f"{name_part}\n{role}" if role else name_part]

    if "," in payload and not role_match:
        names = _split_name_list(payload)
        if len(names) > 1:
            return names

    if _is_valid_name(payload):
        return [payload]
    return []


def _parse_member_blocks(block: str) -> list[TeamMember]:
    lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
    if not lines:
        return []

    first = _strip_urls(lines[0])
    name = ALIAS_RE.sub("", first).strip()
    role = ""
    project_area = ""
    contributions: list[str] = []
    start_idx = 1

    if not _is_valid_name(name) and len(lines) > 1:
        second = lines[1]
        if _looks_like_role(second) and _is_valid_name(name):
            role = second
            start_idx = 2
        else:
            return []

    if start_idx < len(lines) and _looks_like_role(lines[start_idx]) and not role:
        role = lines[start_idx]
        if "проект" in role.lower() or "«" in role:
            project_area = role
        start_idx += 1

    i = start_idx
    while i < len(lines):
        line = lines[i]
        if line.startswith("http") or URL_RE.fullmatch(line):
            i += 1
            continue

        bullet = BULLET_RE.match(line)
        if bullet:
            contributions.append(bullet.group(1).strip())
            i += 1
            continue

        if not role and _looks_like_role(line):
            role = line
            if "проект" in line.lower() or "«" in line:
                project_area = line
            i += 1
            continue

        if line.endswith(";") or len(line) > 40:
            contributions.extend(_split_contributions(line))
        elif not project_area and ("проект" in line.lower() or "/" in line):
            if _looks_like_role(line) or len(line) < 80:
                project_area = line
            else:
                contributions.append(line)
        else:
            contributions.append(line)
        i += 1

    if not _is_valid_name(name):
        return []

    return [
        TeamMember(
            name=name,
            role=role,
            project_area=project_area,
            contributions=contributions,
        )
    ]


def _split_name_list(text: str) -> list[str]:
    names: list[str] = []
    for part in text.split(","):
        cleaned = ALIAS_RE.sub("", part.strip())
        cleaned = _strip_urls(cleaned)
        if _is_valid_name(cleaned):
            names.append(cleaned)
    return names


def _strip_urls(text: str) -> str:
    return URL_RE.sub("", text).strip()


def _is_valid_name(name: str) -> bool:
    name = ALIAS_RE.sub("", name.strip())
    if len(name) < 5 or len(name) > 80:
        return False
    if name.lower() in TECH_NAME_BLOCKLIST:
        return False
    return bool(NAME_RE.match(name))


def _looks_like_role(line: str) -> bool:
    low = line.lower()
    if len(line) > 120:
        return False
    if _is_valid_name(line):
        return False
    return any(h in low for h in ROLE_HINTS) or "," in line


def _split_contributions(text: str) -> list[str]:
    parts = re.split(r";\s*", text)
    return [p.strip() for p in parts if p.strip()]
