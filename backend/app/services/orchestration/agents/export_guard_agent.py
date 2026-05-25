"""Export guard for team cards."""

from __future__ import annotations

from app.schemas.fidelity import TeamMember
from app.services.contract_fidelity.team_candidate_validator import (
    filter_team_members,
    is_valid_person_name,
)


def guard_team_for_export(members: list[TeamMember]) -> tuple[list[TeamMember], list[str]]:
    """Filter invalid team cards and collect warnings."""
    warnings: list[str] = []
    cleaned: list[TeamMember] = []

    for member in filter_team_members(members):
        if not member.name or not is_valid_person_name(member.name):
            continue
        if not member.role and not member.contributions:
            warnings.append(
                f"team member '{member.name}' has no role and no contributions"
            )
        cleaned.append(member)

    return cleaned, warnings
