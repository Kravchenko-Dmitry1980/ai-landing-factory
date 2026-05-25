"""Contract fidelity schemas — structured landing detection, parsing, completeness."""

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.evidence import EvidenceAssemblyReport, FieldSourceTrace


class LandingModule(BaseModel):
    name: str
    description: str = ""
    type: str = ""


class TeamMember(BaseModel):
    name: str
    role: str = ""
    project_area: str = ""
    contributions: list[str] = Field(default_factory=list)


class DetectionResult(BaseModel):
    is_structured_landing: bool = False
    confidence: float = 0.0
    detected_sections: list[str] = Field(default_factory=list)
    missing_sections: list[str] = Field(default_factory=list)
    reason: str = ""


class SourceTypeResult(BaseModel):
    source_type: str = "unknown"
    confidence: float = 0.0
    signals: list[str] = Field(default_factory=list)
    reason: str = ""


class SectionInfo(BaseModel):
    key: str
    title: str
    length: int = 0
    item_count: int = 0


class SourceStructureReport(BaseModel):
    parser_mode: str = "heuristic"
    detection: DetectionResult
    sections: list[SectionInfo] = Field(default_factory=list)
    parser_confidence: float = 0.0
    missing_sections: list[str] = Field(default_factory=list)


class ContractCompletenessReport(BaseModel):
    score: int = 0
    missing_fields: list[str] = Field(default_factory=list)
    weak_fields: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    recommended_action: str = ""
    complete: bool = False
    export_incomplete: bool = False


class ParsedStructuredLanding(BaseModel):
    title: str | None = None
    client: str | None = None
    timeline: str | None = None
    lead: str | None = None
    essence: str = ""
    tasks: list[str] = Field(default_factory=list)
    purpose: list[str] = Field(default_factory=list)
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    results: list[str] = Field(default_factory=list)
    outlook: list[str] = Field(default_factory=list)
    tech_stack_grouped: dict[str, list[str]] = Field(default_factory=dict)
    team: list[TeamMember] = Field(default_factory=list)
    modules: list[LandingModule] = Field(default_factory=list)
    tagline: str | None = None
    section_lengths: dict[str, int] = Field(default_factory=dict)


class FidelityMetadata(BaseModel):
    parser_mode: str = "heuristic"
    detection: DetectionResult | None = None
    completeness: ContractCompletenessReport | None = None
    modules: list[LandingModule] = Field(default_factory=list)
    team_structured: list[TeamMember] = Field(default_factory=list)
    tech_stack_grouped: dict[str, list[str]] = Field(default_factory=dict)
    source_count: int = 0
    evidence_count: int = 0
    source_types: list[str] = Field(default_factory=list)
    field_sources: list[FieldSourceTrace] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    weak_fields: list[str] = Field(default_factory=list)
    assembly_confidence: float = 0.0
    evidence_report: EvidenceAssemblyReport | None = None
    fusion_trace: Any | None = None
    field_decisions: dict[str, Any] = Field(default_factory=dict)
    orchestration_trace: Any | None = None
