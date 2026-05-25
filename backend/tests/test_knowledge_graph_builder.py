"""Tests for knowledge graph builder."""

from uuid import uuid4

from app.models.domain import utc_now
from app.schemas.landing_contract import LandingBlock, LandingContract, LandingStylePreset
from app.services.domain.knowledge_graph_builder import build_knowledge_graph
from app.schemas.domain_intelligence import PrimaryDomain


def _medical_contract() -> LandingContract:
    return LandingContract(
        project_id=uuid4(),
        title="GlaucoLogic",
        style=LandingStylePreset.TECH,
        blocks=[
            LandingBlock(
                key="essence",
                title="Essence",
                content="ОКТ анализ для врача",
                bullets=[],
            ),
            LandingBlock(
                key="tech_stack",
                title="Stack",
                content="",
                bullets=["FastAPI", "OpenAI", "PostgreSQL"],
            ),
            LandingBlock(
                key="tasks",
                title="Tasks",
                content="",
                bullets=["OCT analysis", "Clinical audit"],
            ),
            LandingBlock(
                key="results",
                title="Results",
                content="",
                bullets=["Diagnostic accuracy 94%"],
            ),
        ],
        updated_at=utc_now(),
    )


def test_graph_not_empty():
    graph = build_knowledge_graph(_medical_contract())
    assert graph.domain_profile.primary_domain == PrimaryDomain.MEDICAL_AI
    assert len(graph.entities) >= 2
    assert graph.confidence_summary.overall > 0


def test_no_invented_team_members():
    c = _medical_contract()
    graph = build_knowledge_graph(c)
    labels = {e.label.lower() for e in graph.entities}
    assert "john doe" not in labels
    assert "fake client" not in labels


def test_missing_knowledge_detected():
    graph = build_knowledge_graph(_medical_contract())
    assert any("inputs" in m for m in graph.missing_knowledge)
