"""Visual source classification and routing schemas (H.9.1)."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class VisualContentType(StrEnum):
    team_slide = "team_slide"
    architecture_diagram = "architecture_diagram"
    tech_stack_slide = "tech_stack_slide"
    goals_slide = "goals_slide"
    metrics_slide = "metrics_slide"
    roadmap_slide = "roadmap_slide"
    table_or_matrix = "table_or_matrix"
    ui_screenshot = "ui_screenshot"
    generic_image = "generic_image"
    unknown = "unknown"


class VisualRouteAction(StrEnum):
    skip = "skip"
    use_text_layer = "use_text_layer"
    run_ocr = "run_ocr"
    run_ocr_and_mark_vlm_candidate = "run_ocr_and_mark_vlm_candidate"
    mark_vlm_candidate_only = "mark_vlm_candidate_only"


class VisualSourceItem(BaseModel):
    source_id: str
    filename: str
    source_type: str
    page_or_slide: int | None = None
    image_index: int | None = None
    text_chars: int = 0
    image_count: int = 0
    has_text_layer: bool = False
    has_images: bool = False
    extracted_image_bytes: int | None = None
    title_hint: str | None = None
    raw_text_preview: str | None = None


class VisualClassification(BaseModel):
    item: VisualSourceItem
    content_type: VisualContentType
    confidence: float = 0.0
    route_action: VisualRouteAction
    reason: str = ""
    markers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    vlm_candidate: bool = False


class VisualEvidenceReport(BaseModel):
    source_count: int = 0
    visual_items_count: int = 0
    classifications: list[VisualClassification] = Field(default_factory=list)
    vlm_candidates_count: int = 0
    ocr_candidates_count: int = 0
    warnings: list[str] = Field(default_factory=list)


class VisualEvidenceSummaryLine(BaseModel):
    """Slim line for evidence-report API."""

    source_filename: str
    page_or_slide: int | None = None
    content_type: str
    route_action: str
    confidence: float = 0.0
    vlm_candidate: bool = False
    reason: str = ""
    markers: list[str] = Field(default_factory=list)
