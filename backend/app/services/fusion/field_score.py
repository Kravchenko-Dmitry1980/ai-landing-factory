"""Score field candidates for fusion ranking."""

from __future__ import annotations

from app.schemas.fusion import FieldCandidate
from app.services.fusion.fusion_config import PARSER_MODE_PRIORITY, ROLE_PRIORITY


def score_candidate(candidate: FieldCandidate, field_name: str) -> float:
    base = candidate.confidence
    role_boost = ROLE_PRIORITY.get(candidate.source_role, 30) / 100.0
    parser_boost = PARSER_MODE_PRIORITY.get(candidate.parser_mode, 40) / 100.0
    evidence_boost = min(candidate.evidence_count * 0.02, 0.15)
    priority_boost = candidate.priority / 200.0

    if field_name in ("title", "client", "timeline", "lead"):
        return role_boost * 0.55 + parser_boost * 0.25 + base * 0.15 + priority_boost
    if field_name == "team":
        if candidate.source_role in ("primary_project_doc", "ready_landing_doc"):
            return 0.95
        return base * 0.4 + role_boost * 0.35 + parser_boost * 0.25
    if field_name == "modules":
        if candidate.source_role in ("supporting_presentation", "module_presentation"):
            return 0.85 + base * 0.1
        return base * 0.5 + parser_boost * 0.3 + role_boost * 0.2
    return base * 0.45 + parser_boost * 0.3 + role_boost * 0.15 + evidence_boost


def rank_candidates(candidates: list[FieldCandidate], field_name: str) -> list[FieldCandidate]:
    return sorted(
        candidates,
        key=lambda c: score_candidate(c, field_name),
        reverse=True,
    )
