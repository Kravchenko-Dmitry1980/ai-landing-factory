"""Field-level multi-source fusion schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.landing_contract import LandingContract


class FieldName:
    """Canonical contract field identifiers."""

    TITLE = "title"
    CLIENT = "client"
    TIMELINE = "timeline"
    LEAD = "lead"
    ESSENCE = "essence"
    TASKS = "tasks"
    PURPOSE = "purpose"
    INPUTS = "inputs"
    OUTPUTS = "outputs"
    RESULTS = "results"
    OUTLOOK = "outlook"
    TECH_STACK = "tech_stack"
    TEAM = "team"
    MODULES = "modules"
    QUOTE = "quote"

    ALL = (
        TITLE,
        CLIENT,
        TIMELINE,
        LEAD,
        ESSENCE,
        TASKS,
        PURPOSE,
        INPUTS,
        OUTPUTS,
        RESULTS,
        OUTLOOK,
        TECH_STACK,
        TEAM,
        MODULES,
        QUOTE,
    )


class FieldCandidate(BaseModel):
    field_name: str
    value: Any
    source_id: str
    filename: str = ""
    source_role: str = "unknown"
    source_type: str = "unknown"
    parser_mode: str = ""
    confidence: float = 0.5
    evidence_count: int = 0
    location: str | None = None
    reason: str = ""
    priority: int = 50


class FieldFusionDecision(BaseModel):
    field_name: str
    strategy: str
    selected_sources: list[str] = Field(default_factory=list)
    rejected_sources: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    reason: str = ""
    warnings: list[str] = Field(default_factory=list)


class FusionConflict(BaseModel):
    field_name: str
    conflict_type: str
    sources: list[str] = Field(default_factory=list)
    resolution: str = ""
    warning: str = ""


class FusionTrace(BaseModel):
    source_count: int = 0
    candidate_count: int = 0
    field_decisions: dict[str, FieldFusionDecision] = Field(default_factory=dict)
    conflicts: list[FusionConflict] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    weak_fields: list[str] = Field(default_factory=list)
    final_completeness: int = 0
    original_parser_modes: list[str] = Field(default_factory=list)


class FinalFusionResult(BaseModel):
    contract: LandingContract
    trace: FusionTrace
