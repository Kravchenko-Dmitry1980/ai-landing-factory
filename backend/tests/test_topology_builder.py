"""Tests for topology_builder."""

from uuid import uuid4

from app.models.domain import utc_now
from app.schemas.landing_contract import LandingBlock, LandingContract, LandingStylePreset
from app.schemas.semantic_generation import (
    DomainProfile,
    GeneratedSemanticLanding,
    SectionType,
    SemanticGenerationMetadata,
    SemanticNarrative,
    SemanticSection,
)
from app.services.architecture.topology_builder import build_topology, enrich_semantic_topology


def _contract() -> LandingContract:
    return LandingContract(
        project_id=uuid4(),
        style=LandingStylePreset.TECH,
        title="AI Landing Factory",
        blocks=[
            LandingBlock(
                key="inputs",
                title="Inputs",
                content="DOCX, PDF uploads",
                bullets=["FastAPI backend", "PII Guard"],
            ),
            LandingBlock(
                key="outputs",
                title="Outputs",
                content="",
                bullets=["Interactive landing", "PostgreSQL storage"],
            ),
            LandingBlock(
                key="tech_stack",
                title="Stack",
                content="",
                bullets=["React frontend", "Redis cache", "OpenAI LLM"],
            ),
        ],
        updated_at=utc_now(),
    )


def _semantic(contract: LandingContract) -> GeneratedSemanticLanding:
    return GeneratedSemanticLanding(
        project_id=contract.project_id,
        domain=DomainProfile.ENTERPRISE,
        narrative=SemanticNarrative(architecture="Pipeline from uploads to landing"),
        sections=[
            SemanticSection(
                section_type=SectionType.ARCHITECTURE,
                title="Architecture",
                bullets=["FastAPI backend", "React frontend"],
            ),
        ],
        metadata=SemanticGenerationMetadata(fallback_used=True),
    )


def test_build_topology_grounded_nodes():
    contract = _contract()
    semantic = _semantic(contract)
    topo = build_topology(contract, semantic)
    labels = {n.label.lower() for n in topo.nodes}
    assert any("fastapi" in l for l in labels)
    assert any("react" in l for l in labels)
    assert topo.node_count == len(topo.nodes)
    assert topo.diagram_type


def test_no_hallucinated_nodes():
    contract = _contract()
    semantic = _semantic(contract)
    topo = build_topology(contract, semantic)
    corpus = " ".join(
        b.content + " ".join(b.bullets) for b in contract.blocks
    ).lower()
    for node in topo.nodes:
        if not node.inferred:
            assert any(t in corpus for t in node.label.lower().split() if len(t) > 3)


def test_enrich_attaches_architecture():
    contract = _contract()
    semantic = _semantic(contract)
    enriched = enrich_semantic_topology(contract, semantic)
    assert enriched.architecture is not None
    assert len(enriched.architecture.nodes) >= 2


def test_edge_endpoints_valid():
    contract = _contract()
    topo = build_topology(contract, _semantic(contract))
    ids = {n.id for n in topo.nodes}
    for edge in topo.edges:
        assert edge.source in ids
        assert edge.target in ids
