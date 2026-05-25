"""Build edges between topology nodes."""

from app.schemas.architecture import TopologyEdge, TopologyNode
from app.schemas.domain_intelligence import ProjectKnowledgeGraph
from app.schemas.landing_contract import LandingContract
from app.schemas.semantic_generation import GeneratedSemanticLanding, SectionType


def _find(nodes: list[TopologyNode], *keywords: str) -> TopologyNode | None:
    for node in nodes:
        label = node.label.lower()
        if any(k in label for k in keywords):
            return node
    return None


def _edge(
    source: str,
    target: str,
    label: str | None = None,
    *,
    inferred: bool = False,
    confidence: float = 0.75,
    source_refs: list[str] | None = None,
) -> TopologyEdge:
    eid = f"{source}->{target}"
    return TopologyEdge(
        id=eid,
        source=source,
        target=target,
        label=label,
        flow_type="data",
        confidence=confidence,
        source_refs=source_refs or [],
        inferred=inferred,
    )


def build_edges(
    nodes: list[TopologyNode],
    contract: LandingContract,
    semantic: GeneratedSemanticLanding | None = None,
    knowledge_graph: ProjectKnowledgeGraph | None = None,
) -> list[TopologyEdge]:
    if len(nodes) < 2:
        return []

    by_id = {n.id: n for n in nodes}
    edges: list[TopologyEdge] = []
    seen: set[str] = set()

    def add(edge: TopologyEdge) -> None:
        if edge.source not in by_id or edge.target not in by_id:
            return
        if edge.id in seen or edge.source == edge.target:
            return
        seen.add(edge.id)
        edges.append(edge)

    # Section-level architecture_nodes connections
    if semantic:
        for section in semantic.sections:
            st = str(section.section_type)
            for an in section.architecture_nodes:
                nid = next((n.id for n in nodes if n.label.lower() == an.label.lower()), None)
                if not nid:
                    continue
                for conn_label in an.connections:
                    target = next(
                        (n.id for n in nodes if conn_label.lower() in n.label.lower()),
                        None,
                    )
                    if target:
                        add(
                            _edge(nid, target, source_refs=[st], confidence=0.9, inferred=False)
                        )

    # Pipeline: ingestion → orchestrator/worker → output
    ingestion = _find(nodes, "ingestion", "input", "upload")
    orchestrator = _find(nodes, "orchestrat", "pipeline", "worker", "processor")
    output = _find(nodes, "output", "delivery", "preview", "landing")
    pii = _find(nodes, "pii", "privacy", "guard", "redact")

    if ingestion and orchestrator:
        add(_edge(ingestion.id, orchestrator.id, "process", source_refs=["inputs"], confidence=0.8))
    if orchestrator and output:
        add(_edge(orchestrator.id, output.id, "deliver", source_refs=["outputs"], confidence=0.8))
    if ingestion and pii and orchestrator:
        add(_edge(ingestion.id, pii.id, "scan", source_refs=["pii"], confidence=0.85))
        add(_edge(pii.id, orchestrator.id, "safe payload", source_refs=["pii"], confidence=0.85))

    # Sequential chain within layers (inferred, low confidence)
    from app.services.architecture.layer_classifier import _LAYER_ORDER, classify_layer

    layer_nodes: dict[str, list[TopologyNode]] = {}
    for node in nodes:
        layer = node.layer or classify_layer(node)
        layer_nodes.setdefault(layer, []).append(node)

    for layer in _LAYER_ORDER:
        group = layer_nodes.get(layer, [])
        for i in range(len(group) - 1):
            add(
                _edge(
                    group[i].id,
                    group[i + 1].id,
                    inferred=True,
                    confidence=0.4,
                    source_refs=[f"layer:{layer}"],
                )
            )

    # Cross-layer: frontend → backend → data (when types match)
    front = [n for n in nodes if str(n.node_type) in ("frontend", "NodeType.FRONTEND") or getattr(n.node_type, "value", "") == "frontend"]
    back = [n for n in nodes if getattr(n.node_type, "value", "") == "backend"]
    data = [n for n in nodes if (n.layer or "") == "data"]
    if front and back:
        add(_edge(front[0].id, back[0].id, "API", inferred=True, confidence=0.5))
    if back and data:
        add(_edge(back[0].id, data[0].id, "persist", inferred=True, confidence=0.5))

    if knowledge_graph:
        id_map = {n.label.lower(): n.id for n in nodes}
        for rel in knowledge_graph.relations[:60]:
            src = next((n.id for n in nodes if n.id == rel.source_id), None)
            tgt = next((n.id for n in nodes if n.id == rel.target_id), None)
            if src and tgt:
                rtype = rel.relation_type.value if hasattr(rel.relation_type, "value") else str(rel.relation_type)
                add(
                    _edge(
                        src,
                        tgt,
                        rtype,
                        inferred=rel.inferred,
                        confidence=rel.confidence,
                        source_refs=["knowledge_graph"],
                    )
                )

    return edges
