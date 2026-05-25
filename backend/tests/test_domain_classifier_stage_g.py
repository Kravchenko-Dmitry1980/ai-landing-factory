"""Tests for Stage G domain classifier."""

from uuid import uuid4

from app.models.domain import utc_now
from app.schemas.landing_contract import LandingBlock, LandingContract, LandingStylePreset
from app.services.domain.domain_classifier import classify_domain
from app.schemas.domain_intelligence import PrimaryDomain


def _c(text: str) -> LandingContract:
    return LandingContract(
        project_id=uuid4(),
        style=LandingStylePreset.MINIMAL,
        blocks=[LandingBlock(key="essence", title="E", content=text, bullets=[])],
        updated_at=utc_now(),
    )


def test_medical_ai_domain():
    r = classify_domain(_c("ОКТ пациент врач диагноз клинический аудит"))
    assert r.profile.primary_domain == PrimaryDomain.MEDICAL_AI
    assert r.profile.confidence >= 0.45


def test_education_ai_domain():
    r = classify_domain(_c("CEFR lesson tutor student learning path"))
    assert r.profile.primary_domain == PrimaryDomain.EDUCATION_AI


def test_rag_system_domain():
    r = classify_domain(_c("RAG Qdrant embeddings retrieval knowledge base"))
    assert r.profile.primary_domain == PrimaryDomain.RAG_SYSTEM


def test_speech_ai_domain():
    r = classify_domain(_c("Whisper STT diarization audio transcript"))
    assert r.profile.primary_domain == PrimaryDomain.SPEECH_AI


def test_multi_agent_domain():
    r = classify_domain(_c("orchestrator agents planner critic multi-agent"))
    assert r.profile.primary_domain == PrimaryDomain.MULTI_AGENT_SYSTEM
