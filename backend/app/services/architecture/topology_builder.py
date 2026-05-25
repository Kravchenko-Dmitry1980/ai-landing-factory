"""Architecture Topology Engine — Stage F orchestrator."""

from app.models.domain import utc_now
from app.schemas.architecture import ArchitectureFlow, ArchitectureLayer, ArchitectureTopology
from app.schemas.domain_intelligence import ProjectKnowledgeGraph
from app.schemas.landing_contract import LandingContract
from app.schemas.semantic_generation import GeneratedSemanticLanding
from app.services.architecture.architecture_validator import validate_topology
from app.services.architecture.diagram_hints import infer_diagram_type
from app.services.architecture.edge_builder import build_edges
from app.services.architecture.graph_extractor import extract_nodes
from app.services.architecture.layer_classifier import apply_layers, build_layer_groups
from app.services.architecture.layout_inference import infer_layout


def build_topology(
    contract: LandingContract,
    semantic: GeneratedSemanticLanding,
    knowledge_graph: ProjectKnowledgeGraph | None = None,
) -> ArchitectureTopology:
    """Build grounded architecture graph from contract + semantic + optional KG (no LLM)."""
    nodes = apply_layers(extract_nodes(contract, semantic, knowledge_graph=knowledge_graph))
    edges = build_edges(nodes, contract, semantic, knowledge_graph=knowledge_graph)
    diagram_type = infer_diagram_type(semantic, semantic.domain, knowledge_graph=knowledge_graph)
    layout = infer_layout(diagram_type, len(nodes))

    layers = [
        ArchitectureLayer(id=lid, label=lid.replace("_", " ").title(), node_ids=nids)
        for lid, nids in build_layer_groups(nodes)
    ]

    flows: list[ArchitectureFlow] = []
    pipeline_path = [n.id for n in nodes[:6]]
    if pipeline_path:
        flows.append(ArchitectureFlow(id="primary", label="Primary flow", path=pipeline_path))

    topology = ArchitectureTopology(
        diagram_type=diagram_type,
        layout=layout,
        nodes=nodes,
        edges=edges,
        layers=layers,
        flows=flows,
        generated_at=utc_now(),
    )
    return validate_topology(topology)


def enrich_semantic_topology(
    contract: LandingContract,
    semantic: GeneratedSemanticLanding,
    knowledge_graph: ProjectKnowledgeGraph | None = None,
) -> GeneratedSemanticLanding:
    """Attach topology to semantic landing and sync section architecture_nodes."""
    topology = build_topology(contract, semantic, knowledge_graph=knowledge_graph)

    # Sync per-section nodes from global topology for architecture sections
    updated_sections = []
    arch_nodes = [
        {"id": n.id, "label": n.label, "role": str(n.node_type), "connections": []}
        for n in topology.nodes[:12]
    ]
    for section in semantic.sections:
        st = section.section_type.value if hasattr(section.section_type, "value") else str(
            section.section_type
        )
        if st in ("architecture", "pipeline", "orchestration", "system") and not section.architecture_nodes:
            from app.schemas.semantic_generation import ArchitectureNode

            section = section.model_copy(
                update={
                    "architecture_nodes": [
                        ArchitectureNode(**an) for an in arch_nodes[:8]
                    ]
                }
            )
        updated_sections.append(section)

    return semantic.model_copy(
        update={
            "sections": updated_sections,
            "architecture": topology,
        }
    )
