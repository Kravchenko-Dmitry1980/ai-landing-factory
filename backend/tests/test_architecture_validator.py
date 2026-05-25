"""Tests for architecture_validator."""

from app.schemas.architecture import ArchitectureTopology, TopologyEdge, TopologyNode
from app.services.architecture.architecture_validator import validate_topology


def test_drops_invalid_edges():
    nodes = [
        TopologyNode(id="a", label="A"),
        TopologyNode(id="b", label="B"),
    ]
    edges = [
        TopologyEdge(id="a->b", source="a", target="b"),
        TopologyEdge(id="a->x", source="a", target="missing"),
    ]
    topo = ArchitectureTopology(nodes=nodes, edges=edges)
    validated = validate_topology(topo)
    assert len(validated.edges) == 1
    assert any("Dropped edge" in w for w in validated.warnings)


def test_orphan_warning():
    nodes = [
        TopologyNode(id="a", label="A"),
        TopologyNode(id="b", label="B"),
        TopologyNode(id="c", label="C"),
    ]
    edges = [TopologyEdge(id="a->b", source="a", target="b")]
    topo = ArchitectureTopology(nodes=nodes, edges=edges)
    validated = validate_topology(topo)
    assert any("Orphan" in w for w in validated.warnings)
