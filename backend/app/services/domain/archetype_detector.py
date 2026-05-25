"""System archetype detector from domain profile and contract signals."""

from app.schemas.domain_intelligence import (
    DomainProfile,
    PrimaryDomain,
    SystemArchetype,
    SystemArchetypeType,
)
from app.schemas.landing_contract import LandingContract
from app.services.domain.corpus import contract_corpus_lower

ARCHETYPE_RULES: list[tuple[SystemArchetypeType, tuple[str, ...], PrimaryDomain | None]] = [
    (
        SystemArchetypeType.AI_COPILOT,
        ("copilot", "assistant", "врач", "doctor", "physician", "real-time"),
        PrimaryDomain.MEDICAL_AI,
    ),
    (
        SystemArchetypeType.RAG_KNOWLEDGE_ASSISTANT,
        ("rag", "retrieval", "knowledge base", "vector", "embedding"),
        PrimaryDomain.RAG_SYSTEM,
    ),
    (
        SystemArchetypeType.MULTI_AGENT_ORCHESTRATOR,
        ("orchestrator", "multi-agent", "planner", "critic", "agent"),
        PrimaryDomain.MULTI_AGENT_SYSTEM,
    ),
    (
        SystemArchetypeType.ANALYTICS_DASHBOARD,
        ("dashboard", "analytics", "kpi", "visualization", "clustering"),
        PrimaryDomain.ANALYTICS_PLATFORM,
    ),
    (
        SystemArchetypeType.DECISION_SUPPORT_SYSTEM,
        ("decision support", "clinical audit", "second opinion", "diagnosis", "диагноз"),
        PrimaryDomain.MEDICAL_AI,
    ),
    (
        SystemArchetypeType.WORKFLOW_AUTOMATION_PLATFORM,
        ("workflow", "automation", "pipeline", "orchestration"),
        None,
    ),
    (
        SystemArchetypeType.DOCUMENT_PROCESSING_PIPELINE,
        ("docx", "pdf", "document", "extraction", "ocr"),
        PrimaryDomain.DOCUMENT_AI,
    ),
    (
        SystemArchetypeType.REALTIME_SPEECH_PIPELINE,
        ("whisper", "stt", "diarization", "transcript", "audio"),
        PrimaryDomain.SPEECH_AI,
    ),
    (
        SystemArchetypeType.CV_DIAGNOSTIC_ASSISTANT,
        ("yolo", "detection", "image", "bbox", "segmentation"),
        PrimaryDomain.COMPUTER_VISION,
    ),
    (
        SystemArchetypeType.LEARNING_PLATFORM,
        ("lesson", "tutor", "student", "cefr", "learning path", "course"),
        PrimaryDomain.EDUCATION_AI,
    ),
    (
        SystemArchetypeType.RECOMMENDATION_ENGINE,
        ("recommendation", "scoring", "personalized", "planning", "vitacalc"),
        None,
    ),
]


def detect_archetypes(
    contract: LandingContract,
    domain_profile: DomainProfile,
) -> list[SystemArchetype]:
    corpus = contract_corpus_lower(contract)
    results: list[SystemArchetype] = []

    for archetype, keywords, required_domain in ARCHETYPE_RULES:
        if required_domain and domain_profile.primary_domain not in (
            required_domain,
            *domain_profile.secondary_domains,
        ):
            if required_domain != domain_profile.primary_domain:
                continue

        hits = [kw for kw in keywords if kw in corpus]
        if not hits:
            continue

        confidence = min(0.92, 0.5 + len(hits) * 0.12)
        if required_domain == domain_profile.primary_domain:
            confidence = min(0.95, confidence + 0.1)

        results.append(
            SystemArchetype(
                archetype=archetype,
                confidence=confidence,
                reason=f"Matched {len(hits)} signal(s) for {archetype.value}",
                evidence=[f"signal:{h}" for h in hits[:5]],
            )
        )

    results.sort(key=lambda a: a.confidence, reverse=True)
    return results[:3]
