"""Internal VLM contracts and context types."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas.visual_evidence import VisualContentType, VisualRouteAction
from app.schemas.vlm import VlmTaskType

CONTENT_TYPE_TO_TASK: dict[VisualContentType, VlmTaskType] = {
    VisualContentType.team_slide: VlmTaskType.extract_team,
    VisualContentType.architecture_diagram: VlmTaskType.extract_architecture,
    VisualContentType.tech_stack_slide: VlmTaskType.extract_tech_stack,
    VisualContentType.goals_slide: VlmTaskType.extract_goals,
    VisualContentType.metrics_slide: VlmTaskType.extract_metrics,
    VisualContentType.roadmap_slide: VlmTaskType.extract_roadmap,
    VisualContentType.table_or_matrix: VlmTaskType.extract_table,
    VisualContentType.ui_screenshot: VlmTaskType.extract_ui_features,
    VisualContentType.generic_image: VlmTaskType.general_visual_summary,
    VisualContentType.unknown: VlmTaskType.general_visual_summary,
}

VLM_ROUTE_ACTIONS: frozenset[VisualRouteAction] = frozenset(
    {
        VisualRouteAction.mark_vlm_candidate_only,
        VisualRouteAction.run_ocr_and_mark_vlm_candidate,
    }
)

TASK_TARGET_FIELDS: dict[VlmTaskType, list[str]] = {
    VlmTaskType.extract_team: ["team"],
    VlmTaskType.extract_tech_stack: ["tech_stack"],
    VlmTaskType.extract_architecture: ["modules", "tech_stack"],
    VlmTaskType.extract_goals: ["tasks", "purpose", "essence"],
    VlmTaskType.extract_metrics: ["results"],
    VlmTaskType.extract_roadmap: ["outlook"],
    VlmTaskType.extract_ui_features: ["outputs", "results"],
    VlmTaskType.extract_table: ["results", "modules"],
    VlmTaskType.general_visual_summary: ["essence", "results"],
}

KNOWN_TECH_MARKERS: tuple[str, ...] = (
    "qdrant",
    "neo4j",
    "bertopic",
    "fastapi",
    "react",
    "postgresql",
    "docker",
    "streamlit",
    "python",
    "redis",
    "kafka",
    "yolov",
    "pytorch",
    "tensorflow",
)


@dataclass
class VlmExtractionContext:
    filename: str
    page_or_slide: int | None = None
    image_index: int | None = None
    visual_content_type: str = "unknown"
    text_layer_preview: str | None = None
    ocr_text_preview: str | None = None
    known_project_title: str | None = None
    target_fields: list[str] = field(default_factory=list)
