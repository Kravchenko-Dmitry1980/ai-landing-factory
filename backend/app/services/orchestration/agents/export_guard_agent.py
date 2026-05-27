"""Export guard for team cards."""

from __future__ import annotations

from app.schemas.fidelity import TeamMember
from app.schemas.team_verification import TeamVerificationReport
from app.services.contract_fidelity.team_candidate_validator import (
    filter_team_members,
    is_valid_person_name,
)
from app.services.team_verification.export_policy import filter_team_for_public_export


def guard_team_for_export(
    members: list[TeamMember],
    verification_report: TeamVerificationReport | None = None,
    publication_mode: str | None = None,
    accepted_ids: list[str] | None = None,
) -> tuple[list[TeamMember], list[str]]:
    """Filter invalid team cards and collect warnings."""
    warnings: list[str] = []

    if verification_report is not None:
        filtered, policy_warnings = filter_team_for_public_export(
            members,
            verification_report,
            publication_mode or "safe_public",
            accepted_ids or [],
        )
        warnings.extend(policy_warnings)
        members = filtered

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
