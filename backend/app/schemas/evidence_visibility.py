"""Slim evidence visibility schemas for editor UI (no raw document payloads)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EvidenceSourceView(BaseModel):
    source_id: str
    filename: str
    file_type: str
    detected_source_type: str = "unknown"
    source_role: str = "unknown"
    evidence_count: int = 0
    char_count: int = 0
    slide_count: int | None = None
    page_count: int | None = None
    status: str = "empty"
    notes: list[str] = Field(default_factory=list)


class FieldSourceView(BaseModel):
    field_name: str
    coverage: str = "missing"
    confidence: float = 0.0
    source_refs: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    selected_snippets: list[str] = Field(default_factory=list)


class EvidenceVisibilityResponse(BaseModel):
    project_id: str
    parser_mode: str = "heuristic"
    source_count: int = 0
    evidence_count: int = 0
    assembly_confidence: float = 0.0
    sources: list[EvidenceSourceView] = Field(default_factory=list)
    field_sources: dict[str, FieldSourceView] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    weak_fields: list[str] = Field(default_factory=list)
    strong_fields: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    improvement_hints: list[str] = Field(default_factory=list)
    field_decisions: dict[str, str] = Field(default_factory=dict)
