"""Slim evidence visibility schemas for editor UI (no raw document payloads)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.team_verification import TeamCandidateQuality, TeamVerificationReport
from app.schemas.visual_evidence import VisualEvidenceSummaryLine
from app.schemas.vlm import VlmExtractionSummaryLine


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
    orchestration_trace: dict[str, object] | None = None
    team_group_expansions: list[dict[str, str]] = Field(default_factory=list)
    team_verification_report: TeamVerificationReport | None = None
    ocr_review_candidates: list[TeamCandidateQuality] = Field(default_factory=list)
    team_publication_policy: str = "verified_only"
    team_publication_mode: str = "draft_auto"
    team_review_warning: str | None = None
    visual_evidence_summary: list[VisualEvidenceSummaryLine] = Field(default_factory=list)
    visual_items_count: int = 0
    vlm_candidates_count: int = 0
    ocr_visual_candidates_count: int = 0
    vlm_enabled: bool = False
    vlm_provider: str = "disabled"
    vlm_processed_count: int = 0
    vlm_skipped_count: int = 0
    vlm_extraction_summary: list[VlmExtractionSummaryLine] = Field(default_factory=list)
    advanced_diagnostics_enabled: bool = False
