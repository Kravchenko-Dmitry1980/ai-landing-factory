"""Fusion trace helpers."""

from __future__ import annotations

from app.schemas.evidence import FieldSourceTrace
from app.schemas.fusion import FieldFusionDecision, FusionTrace


def build_field_sources(trace: FusionTrace) -> list[FieldSourceTrace]:
    """Convert fusion decisions to evidence-compatible field source traces."""
    sources: list[FieldSourceTrace] = []
    for field_name, decision in trace.field_decisions.items():
        if not decision.selected_sources:
            continue
        for source in decision.selected_sources:
            sources.append(
                FieldSourceTrace(
                    field_name=field_name,
                    source_filename=source,
                    location_type="fusion",
                    location_index=0,
                    reason=decision.reason,
                    confidence=decision.confidence,
                )
            )
    return sources


def summarize_decisions(trace: FusionTrace) -> dict[str, str]:
    """Human-readable field → source mapping for evidence UI."""
    summary: dict[str, str] = {}
    for field_name, decision in trace.field_decisions.items():
        if decision.selected_sources:
            summary[field_name] = " + ".join(decision.selected_sources)
    return summary
