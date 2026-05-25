"""Validate topology graph integrity and grounding."""

from app.schemas.architecture import ArchitectureTopology, TopologyEdge, TopologyNode


def _orphan_ids(nodes: list[TopologyNode], edges: list[TopologyEdge]) -> set[str]:
    if not edges:
        return {n.id for n in nodes}
    connected: set[str] = set()
    for e in edges:
        connected.add(e.source)
        connected.add(e.target)
    return {n.id for n in nodes if n.id not in connected}


def validate_topology(topology: ArchitectureTopology) -> ArchitectureTopology:
    warnings = list(topology.warnings)
    node_ids = {n.id for n in topology.nodes}
    valid_edges: list[TopologyEdge] = []

    for edge in topology.edges:
        if edge.source not in node_ids or edge.target not in node_ids:
            warnings.append(f"Dropped edge {edge.id}: endpoint missing")
            continue
        valid_edges.append(edge)

    orphans = _orphan_ids(topology.nodes, valid_edges)
    if orphans and len(topology.nodes) > 1:
        warnings.append(f"Orphan nodes: {', '.join(sorted(orphans))}")

    low_conf_edges = [e.id for e in valid_edges if e.confidence < 0.5]
    if low_conf_edges:
        warnings.append(f"Low confidence edges: {len(low_conf_edges)}")

    inferred_nodes = [n.id for n in topology.nodes if n.inferred]
    if len(inferred_nodes) > len(topology.nodes) // 2:
        warnings.append("Majority of nodes are inferred — weak grounding")

    density = 0.0
    n = len(topology.nodes)
    if n > 1:
        density = len(valid_edges) / (n * (n - 1))
    if density > 0.35:
        warnings.append("High graph density — chaotic topology risk")

    if n > 40:
        warnings.append("Node count exceeds recommended visualization limit (40)")

    return topology.model_copy(
        update={
            "edges": valid_edges,
            "warnings": warnings,
            "node_count": len(topology.nodes),
            "edge_count": len(valid_edges),
            "graph_density": round(density, 4),
        }
    )
