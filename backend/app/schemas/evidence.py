"""Evidence layer schemas for multi-source landing assembly."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SourceInventoryItem(BaseModel):
    source_id: str
    filename: str
    file_type: str
    char_count: int = 0
    slide_count: int | None = None
    page_count: int | None = None
    table_count: int | None = None
    detected_source_type: str = "unknown"
    source_role: str = "unknown"
    confidence: float = 0.0
    markers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class EvidenceItem(BaseModel):
    evidence_id: str
    source_id: str
    filename: str
    file_type: str
    location_type: str = "unknown"
    location_index: int | None = None
    location_label: str | None = None
    text: str = ""
    normalized_text: str = ""
    section_hint: str | None = None
    field_candidates: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    entities: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    people: list[str] = Field(default_factory=list)
    dates: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class FieldEvidence(BaseModel):
    field_name: str
    items: list[EvidenceItem] = Field(default_factory=list)
    confidence: float = 0.0
    coverage: str = "missing"
    selected_texts: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)


class FieldSourceTrace(BaseModel):
    field_name: str
    source_filename: str
    location_type: str
    location_index: int | None = None
    reason: str = ""
    confidence: float = 0.0


class EvidenceAssemblyReport(BaseModel):
    project_id: str | None = None
    sources: list[SourceInventoryItem] = Field(default_factory=list)
    total_evidence_items: int = 0
    fields: dict[str, FieldEvidence] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    weak_fields: list[str] = Field(default_factory=list)
    strong_fields: list[str] = Field(default_factory=list)
    parser_strategy: str = "multi_source_assembly"
    confidence: float = 0.0
    warnings: list[str] = Field(default_factory=list)
    field_traces: list[FieldSourceTrace] = Field(default_factory=list)


class TeamMemberCandidate(BaseModel):
    name: str
    role: str = ""
    project_area: str = ""
    contributions: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
