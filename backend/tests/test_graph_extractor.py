"""Tests for graph_extractor."""

from uuid import uuid4

from app.models.domain import utc_now
from app.schemas.landing_contract import LandingBlock, LandingContract, LandingStylePreset
from app.services.architecture.graph_extractor import extract_nodes
from app.services.architecture.node_normalizer import normalize_node_type


def _contract() -> LandingContract:
    return LandingContract(
        project_id=uuid4(),
        style=LandingStylePreset.MINIMAL,
        blocks=[
            LandingBlock(key="tech_stack", title="Stack", content="", bullets=["Redis", "PostgreSQL"]),
        ],
        updated_at=utc_now(),
    )


def test_extract_from_stack():
    nodes = extract_nodes(_contract())
    labels = {n.label for n in nodes}
    assert "Redis" in labels
    assert "PostgreSQL" in labels


def test_normalize_redis():
    assert normalize_node_type("Redis cache layer").value == "redis"


def test_skips_ungrounded():
    contract = LandingContract(
        project_id=uuid4(),
        style=LandingStylePreset.MINIMAL,
        blocks=[
            LandingBlock(key="essence", title="Essence", content="Simple platform", bullets=[]),
        ],
        updated_at=utc_now(),
    )
    nodes = extract_nodes(contract)
    assert not any("Kafka" in n.label for n in nodes)
