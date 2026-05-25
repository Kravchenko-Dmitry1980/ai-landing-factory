"""Assign architecture layers to nodes."""

from app.schemas.architecture import NodeType, TopologyNode

_LAYER_BY_TYPE: dict[str, str] = {
    NodeType.FRONTEND.value: "frontend",
    NodeType.API_GATEWAY.value: "frontend",
    NodeType.ORCHESTRATOR.value: "orchestration",
    NodeType.WORKER.value: "orchestration",
    NodeType.QUEUE.value: "orchestration",
    NodeType.AI_SERVICE.value: "ai",
    NodeType.LLM_GATEWAY.value: "ai",
    NodeType.VECTOR_DB.value: "data",
    NodeType.POSTGRES.value: "data",
    NodeType.REDIS.value: "data",
    NodeType.STORAGE.value: "data",
    NodeType.BACKEND.value: "backend",
    NodeType.ANALYTICS.value: "backend",
    NodeType.EXTERNAL_API.value: "backend",
    NodeType.SECURITY_LAYER.value: "security",
    NodeType.PII_GUARD.value: "security",
    NodeType.MONITORING.value: "infra",
    NodeType.GENERIC.value: "backend",
}

_LAYER_ORDER = [
    "frontend",
    "orchestration",
    "ai",
    "backend",
    "data",
    "security",
    "infra",
]


def classify_layer(node: TopologyNode) -> str:
    nt = node.node_type.value if hasattr(node.node_type, "value") else str(node.node_type)
    return _LAYER_BY_TYPE.get(nt, "backend")


def apply_layers(nodes: list[TopologyNode]) -> list[TopologyNode]:
    out: list[TopologyNode] = []
    for node in nodes:
        layer = node.layer or classify_layer(node)
        out.append(node.model_copy(update={"layer": layer}))
    return out


def build_layer_groups(nodes: list[TopologyNode]) -> list[tuple[str, list[str]]]:
    groups: dict[str, list[str]] = {lid: [] for lid in _LAYER_ORDER}
    for node in nodes:
        layer = node.layer or "backend"
        if layer not in groups:
            groups[layer] = []
        groups[layer].append(node.id)
    return [(lid, groups[lid]) for lid in _LAYER_ORDER if groups.get(lid)]
