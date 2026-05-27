"""VLM adapter schemas — structured visual extraction contract (H.9.2)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class VlmProvider(StrEnum):
    stub = "stub"
    local_transformers = "local_transformers"
    ollama = "ollama"
    vllm = "vllm"
    cloud = "cloud"
    disabled = "disabled"


class VlmTaskType(StrEnum):
    extract_team = "extract_team"
    extract_tech_stack = "extract_tech_stack"
    extract_architecture = "extract_architecture"
    extract_goals = "extract_goals"
    extract_metrics = "extract_metrics"
    extract_roadmap = "extract_roadmap"
    extract_ui_features = "extract_ui_features"
    extract_table = "extract_table"
    general_visual_summary = "general_visual_summary"


class VlmFieldCandidate(BaseModel):
    field_name: str
    value: str | list[str] | dict[str, Any]
    confidence: float = 0.0
    source_slide: int | None = None
    source_page: int | None = None
    source_image_index: int | None = None
    evidence_text: str | None = None
    reason: str = ""
    warnings: list[str] = Field(default_factory=list)


class VlmStructuredExtraction(BaseModel):
    provider: str = "stub"
    model_name: str | None = None
    source_filename: str = ""
    source_location: str = ""
    visual_content_type: str = "unknown"
    task_type: str = "general_visual_summary"
    field_candidates: list[VlmFieldCandidate] = Field(default_factory=list)
    raw_response: str | None = None
    normalized_response: dict[str, Any] | None = None
    confidence: float = 0.0
    runtime_ms: int = 0
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class VlmExtractionReport(BaseModel):
    enabled: bool = False
    provider: str = "disabled"
    candidates_count: int = 0
    processed_count: int = 0
    skipped_count: int = 0
    extractions: list[VlmStructuredExtraction] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class VlmCandidateSelection(BaseModel):
    """Router decision for one visual classification."""

    classification_index: int = 0
    source_filename: str = ""
    page_or_slide: int | None = None
    visual_content_type: str = ""
    route_action: str = ""
    confidence: float = 0.0
    task_type: str = ""
    selected: bool = False
    skipped_reason: str = ""


class VlmExtractionSummaryLine(BaseModel):
    """Slim line for evidence-report API."""

    source_filename: str
    page_or_slide: int | None = None
    visual_content_type: str = ""
    task_type: str = ""
    provider: str = ""
    confidence: float = 0.0
    field_count: int = 0
    warnings: list[str] = Field(default_factory=list)
