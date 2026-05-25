"""Parse team members from structured landing team section."""

from __future__ import annotations

import re

from app.schemas.fidelity import TeamMember

NAME_RE = re.compile(
    r"^[А-ЯЁA-Z][а-яёa-z]+(?:\s+[А-ЯЁA-Z][а-яёa-z]+){1,2}$"
)
BULLET_RE = re.compile(r"^[\s]*(?:[-•*·]|–)\s+(.+)$")
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
)


def parse_team_section(text: str) -> list[TeamMember]:
    """Parse team block into structured members."""
    if not text.strip():
        return []

    members: list[TeamMember] = []
    blocks = _split_member_blocks(text)

    for block in blocks:
        member = _parse_member_block(block)
        if member:
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

        if NAME_RE.match(stripped):
            if current:
                blocks.append("\n".join(current))
            current = [stripped]
        elif current:
            current.append(stripped)

    if current:
        blocks.append("\n".join(current))
    return blocks


def _parse_member_block(block: str) -> TeamMember | None:
    lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
    if not lines:
        return None

    name = lines[0]
    if not NAME_RE.match(name):
        return None

    role = ""
    project_area = ""
    contributions: list[str] = []

    i = 1
    while i < len(lines):
        line = lines[i]
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
            project_area = line
        else:
            contributions.append(line)
        i += 1

    return TeamMember(
        name=name,
        role=role,
        project_area=project_area,
        contributions=contributions,
    )


def _looks_like_role(line: str) -> bool:
    low = line.lower()
    if len(line) > 120:
        return False
    return any(h in low for h in ROLE_HINTS) or "," in line


def _split_contributions(text: str) -> list[str]:
    parts = re.split(r";\s*", text)
    return [p.strip() for p in parts if p.strip()]
