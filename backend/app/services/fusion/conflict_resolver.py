"""Detect and resolve cross-source field conflicts."""

from __future__ import annotations

from app.schemas.fusion import FieldCandidate, FieldFusionDecision, FusionConflict


class ConflictResolver:
    """Record conflicts between candidate sources."""

    SINGLE_VALUE_FIELDS = frozenset({"title", "client", "timeline", "lead", "quote"})

    def detect_conflicts(
        self,
        field_name: str,
        candidates: list[FieldCandidate],
        decision: FieldFusionDecision,
    ) -> list[FusionConflict]:
        conflicts: list[FusionConflict] = []
        if field_name not in self.SINGLE_VALUE_FIELDS:
            return conflicts

        values = {
            str(c.value).strip()
            for c in candidates
            if c.value is not None and str(c.value).strip()
        }
        if len(values) <= 1:
            return conflicts

        sources = [c.filename or c.parser_mode for c in candidates if c.value]
        conflicts.append(
            FusionConflict(
                field_name=field_name,
                conflict_type=f"{field_name}_mismatch",
                sources=list(dict.fromkeys(sources)),
                resolution=decision.reason,
                warning=decision.warnings[0] if decision.warnings else f"{field_name}_conflict_resolved",
            )
        )
        return conflicts
