"""The team that may appear on a public page: one rule for every renderer."""

from __future__ import annotations

from app.schemas.fidelity import FidelityMetadata, TeamMember
from app.schemas.landing_contract import LandingBlock
from app.services.contract_fidelity.team_candidate_validator import filter_team_members
from app.services.orchestration.agents.export_guard_agent import guard_team_for_export


def members_from_team_bullets(bullets: list[str]) -> list[TeamMember]:
    """'Имя — Роль' header lines of the team block; '·' lines are contributions and are skipped."""
    members: list[TeamMember] = []
    seen: set[str] = set()
    for line in bullets:
        header = line.strip()
        if not header or header.startswith("·") or header.startswith("  ·"):
            continue
        name = header.split(" — ", 1)[0].strip()
        role = header.split(" — ", 1)[1].strip() if " — " in header else ""
        if len(name) < 5 or name.lower() in seen:
            continue
        seen.add(name.lower())
        members.append(TeamMember(name=name, role=role, project_area="", contributions=[]))
    return filter_team_members(members)


def publishable_team(block: LandingBlock | None, fidelity: FidelityMetadata | None) -> list[TeamMember]:
    """Structured team (or the team block) passed through the verification and publication policy."""
    verification_report = fidelity.team_verification_report if fidelity else None
    publication_mode = fidelity.team_publication_mode if fidelity else "safe_public"
    accepted_ids = list(fidelity.accepted_team_candidate_ids) if fidelity else []
    members: list[TeamMember] = list(fidelity.team_structured) if fidelity else []
    if not members and block and block.bullets:
        members = members_from_team_bullets(block.bullets)
    members, _warnings = guard_team_for_export(members, verification_report, publication_mode, accepted_ids)
    return filter_team_members(members)
