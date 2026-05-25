"""Infer graph layout from diagram type and node count."""

from app.schemas.architecture import DiagramType, LayoutStyle


def infer_layout(diagram_type: DiagramType | str, node_count: int) -> LayoutStyle:
    dt = diagram_type.value if hasattr(diagram_type, "value") else str(diagram_type)

    if dt == DiagramType.PIPELINE.value:
        return LayoutStyle.VERTICAL_PIPELINE
    if dt == DiagramType.LAYERED.value:
        return LayoutStyle.LAYERED
    if dt == DiagramType.HUB_SPOKE.value:
        return LayoutStyle.ORCHESTRATION_MAP
    if dt == DiagramType.MICROSERVICES.value:
        return LayoutStyle.MESH if node_count > 8 else LayoutStyle.HORIZONTAL
    if dt == DiagramType.DASHBOARD_FLOW.value:
        return LayoutStyle.HORIZONTAL
    if dt == DiagramType.RESEARCH_GRAPH.value:
        return LayoutStyle.MESH
    return LayoutStyle.VERTICAL_PIPELINE
