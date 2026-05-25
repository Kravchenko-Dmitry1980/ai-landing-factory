"""Tests for archetype detector."""

from uuid import uuid4

from app.models.domain import utc_now
from app.schemas.landing_contract import LandingBlock, LandingContract, LandingStylePreset
from app.services.domain.archetype_detector import detect_archetypes
from app.services.domain.domain_classifier import classify_domain
from app.schemas.domain_intelligence import SystemArchetypeType


def _contract(text: str) -> LandingContract:
    return LandingContract(
        project_id=uuid4(),
        style=LandingStylePreset.TECH,
        blocks=[
            LandingBlock(key="essence", title="E", content=text, bullets=[]),
            LandingBlock(key="tasks", title="T", content="", bullets=["STT module", "Diarization"]),
        ],
        updated_at=utc_now(),
    )


def test_rag_archetype():
    c = _contract("RAG retrieval vector knowledge base Qdrant embeddings")
    profile = classify_domain(c).profile
    archetypes = detect_archetypes(c, profile)
    assert any(
        a.archetype == SystemArchetypeType.RAG_KNOWLEDGE_ASSISTANT for a in archetypes
    )


def test_decision_support_medical():
    c = _contract("clinical diagnosis decision support second opinion audit")
    profile = classify_domain(c).profile
    archetypes = detect_archetypes(c, profile)
    assert len(archetypes) >= 1
