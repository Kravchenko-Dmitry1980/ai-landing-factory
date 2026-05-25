"""Tests for architecture pattern detector."""

from uuid import uuid4

from app.models.domain import utc_now
from app.schemas.landing_contract import LandingBlock, LandingContract, LandingStylePreset
from app.services.domain.domain_classifier import classify_domain
from app.services.domain.pattern_detector import detect_patterns
from app.schemas.domain_intelligence import ArchitecturePatternType


def _contract(**blocks: list[str]) -> LandingContract:
    return LandingContract(
        project_id=uuid4(),
        style=LandingStylePreset.TECH,
        blocks=[
            LandingBlock(key="tech_stack", title="Stack", content="", bullets=blocks.get("stack", [])),
            LandingBlock(key="tasks", title="Tasks", content="", bullets=blocks.get("tasks", [])),
        ],
        updated_at=utc_now(),
    )


def test_rag_pattern_detected():
    c = _contract(stack=["Qdrant", "embeddings", "RAG retrieval"])
    profile = classify_domain(c).profile
    patterns = detect_patterns(c, profile)
    assert any(p.pattern == ArchitecturePatternType.RAG_PIPELINE for p in patterns)


def test_no_pattern_without_evidence():
    c = _contract(stack=["React", "TypeScript"])
    profile = classify_domain(c).profile
    patterns = detect_patterns(c, profile)
    assert not any("kafka" in str(p.pattern) for p in patterns)
