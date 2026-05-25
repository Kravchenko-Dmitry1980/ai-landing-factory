"""Architecture topology schemas (Stage F)."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class NodeType(str, Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    AI_SERVICE = "ai_service"
    LLM_GATEWAY = "llm_gateway"
    VECTOR_DB = "vector_db"
    POSTGRES = "postgres"
    REDIS = "redis"
    QUEUE = "queue"
    ORCHESTRATOR = "orchestrator"
    WORKER = "worker"
    ANALYTICS = "analytics"
    API_GATEWAY = "api_gateway"
    EXTERNAL_API = "external_api"
    SECURITY_LAYER = "security_layer"
    PII_GUARD = "pii_guard"
    MONITORING = "monitoring"
    STORAGE = "storage"
    GENERIC = "generic"


class DiagramType(str, Enum):
    PIPELINE = "pipeline"
    LAYERED = "layered"
    HUB_SPOKE = "hub_spoke"
    MICROSERVICES = "microservices"
    DASHBOARD_FLOW = "dashboard_flow"
    RESEARCH_GRAPH = "research_graph"


class LayoutStyle(str, Enum):
    VERTICAL_PIPELINE = "vertical_pipeline"
    HORIZONTAL = "horizontal"
    LAYERED = "layered"
    MESH = "mesh"
    ORCHESTRATION_MAP = "orchestration_map"


class TopologyNode(BaseModel):
    id: str
    label: str
    node_type: NodeType | str = NodeType.GENERIC
    layer: str | None = None
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    source: list[str] = Field(default_factory=list)
    inferred: bool = False

    @field_validator("confidence", mode="before")
    @classmethod
    def clamp_confidence(cls, v: object) -> float:
        try:
            f = float(v)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return 0.5
        return max(0.0, min(1.0, f))


class TopologyEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str | None = None
    flow_type: str = "data"
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    source_refs: list[str] = Field(default_factory=list)
    inferred: bool = False

    @field_validator("confidence", mode="before")
    @classmethod
    def clamp_confidence(cls, v: object) -> float:
        try:
            f = float(v)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return 0.5
        return max(0.0, min(1.0, f))


class ArchitectureLayer(BaseModel):
    id: str
    label: str
    node_ids: list[str] = Field(default_factory=list)


class ArchitectureFlow(BaseModel):
    id: str
    label: str
    path: list[str] = Field(default_factory=list)


class ArchitectureTopology(BaseModel):
    diagram_type: DiagramType | str = DiagramType.PIPELINE
    layout: LayoutStyle | str = LayoutStyle.VERTICAL_PIPELINE
    nodes: list[TopologyNode] = Field(default_factory=list)
    edges: list[TopologyEdge] = Field(default_factory=list)
    layers: list[ArchitectureLayer] = Field(default_factory=list)
    flows: list[ArchitectureFlow] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    node_count: int = 0
    edge_count: int = 0
    graph_density: float = 0.0
    generated_at: datetime | None = None
