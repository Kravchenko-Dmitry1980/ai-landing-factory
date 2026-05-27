"""Format and parse editable team text for review UI."""

from __future__ import annotations

from app.schemas.fidelity import TeamMember
from app.schemas.team_review import TeamReviewCandidate
from app.services.contract_fidelity.team_candidate_validator import filter_team_members
from app.services.contract_fidelity.team_parser import parse_team_section, team_to_bullets


from app.services.team_verification.candidate_ids import make_candidate_id


def format_team_as_text(candidates: list[TeamReviewCandidate]) -> str:
    """Generate editable plain-text team list."""
    publishable = [c for c in candidates if c.status != "rejected"]
    if not publishable:
        return ""

    lines: list[str] = []
    uncertain = [
        c
        for c in publishable
        if c.status in ("needs_review", "probable") and c.source_is_ocr
    ]
    if uncertain:
        lines.append("# OCR требует проверки:")

    for candidate in publishable:
        role_part = candidate.role or ""
        lines.append(f"{candidate.display_name} — {role_part}")
        for contrib in candidate.contributions:
            lines.append(f"- {contrib}")
        lines.append("")

    return "\n".join(lines).strip()


def parse_manual_team_text(text: str) -> list[TeamMember]:
    """Parse user-edited team text into TeamMember list."""
    cleaned_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        cleaned_lines.append(line)

    block = "Команда проекта\n" + "\n".join(cleaned_lines)
    return filter_team_members(parse_team_section(block))


def team_members_to_editable_text(members: list[TeamMember]) -> str:
    """Format TeamMember list as editable text."""
    lines: list[str] = []
    for member in members:
        lines.append(f"{member.name} — {member.role or ''}")
        for contrib in member.contributions:
            lines.append(f"- {contrib}")
        lines.append("")
    return "\n".join(lines).strip()


def apply_team_to_contract_blocks(
    members: list[TeamMember],
    blocks: list,
) -> None:
    """Update team block bullets from structured members."""
    bullets = team_to_bullets(members)
    for block in blocks:
        if block.key == "team":
            block.bullets = bullets
            return
