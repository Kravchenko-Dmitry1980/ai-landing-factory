"""Architecture pattern detector from contract stack/modules/tasks."""

import re

from app.schemas.domain_intelligence import (
    ArchitecturePattern,
    ArchitecturePatternType,
    DomainProfile,
    PrimaryDomain,
)
from app.schemas.landing_contract import LandingContract
from app.services.domain.corpus import contract_corpus_lower, tokens_from_text

PATTERN_RULES: list[tuple[ArchitecturePatternType, tuple[str, ...], str]] = [
    (ArchitecturePatternType.INGESTION_PIPELINE, ("ingestion", "upload", "extract", "parse", "etl"), "stack"),
    (ArchitecturePatternType.RAG_PIPELINE, ("rag", "retrieval", "embedding", "vector", "qdrant"), "architecture"),
    (ArchitecturePatternType.MULTI_AGENT_ORCHESTRATION, ("agent", "orchestrator", "planner", "crew"), "modules"),
    (ArchitecturePatternType.EVENT_DRIVEN_ARCHITECTURE, ("kafka", "event", "pubsub", "queue", "rabbitmq"), "stack"),
    (ArchitecturePatternType.REAL_TIME_STREAMING, ("websocket", "stream", "real-time", "realtime", "live"), "architecture"),
    (ArchitecturePatternType.HUMAN_IN_THE_LOOP, ("human-in-the-loop", "physician", "review", "audit", "validation"), "tasks"),
    (ArchitecturePatternType.PRIVACY_FIRST_ARCHITECTURE, ("pii", "privacy", "mask", "redact", "gdpr", "hipaa"), "stack"),
    (ArchitecturePatternType.MICROSERVICES, ("microservice", "kubernetes", "docker", "service mesh"), "stack"),
    (ArchitecturePatternType.MONOLITH_MVP, ("monolith", "mvp", "fastapi", "single service"), "stack"),
    (ArchitecturePatternType.API_GATEWAY, ("gateway", "api gateway", "nginx", "kong"), "stack"),
    (ArchitecturePatternType.ASYNC_WORKER_PIPELINE, ("celery", "worker", "async", "background job", "redis queue"), "stack"),
    (ArchitecturePatternType.VECTOR_SEARCH, ("vector", "embedding", "similarity search", "qdrant", "faiss"), "stack"),
    (ArchitecturePatternType.SEMANTIC_ENRICHMENT, ("semantic", "enrichment", "nlp", "llm enrich"), "tasks"),
    (ArchitecturePatternType.CLINICAL_DECISION_SUPPORT, ("clinical", "diagnosis", "decision support", "cdss"), "results"),
    (ArchitecturePatternType.SCORING_ENGINE, ("scoring", "score", "ranking", "classifier"), "results"),
    (ArchitecturePatternType.RECOMMENDATION_ENGINE, ("recommend", "personalized", "planning"), "results"),
]


def _block_text(contract: LandingContract, key: str) -> str:
    for b in contract.blocks:
        if b.key == key:
            parts = [b.content or "", *b.bullets]
            return " ".join(parts)
    return ""


def _related_modules(contract: LandingContract, pattern_keywords: tuple[str, ...]) -> list[str]:
    tasks = _block_text(contract, "tasks")
    modules = tokens_from_text(tasks)
    related: list[str] = []
    for mod in modules:
        mod_lower = mod.lower()
        if any(kw in mod_lower for kw in pattern_keywords):
            related.append(mod)
    return related[:5]


def detect_patterns(
    contract: LandingContract,
    domain_profile: DomainProfile,
) -> list[ArchitecturePattern]:
    corpus = contract_corpus_lower(contract)
    results: list[ArchitecturePattern] = []

    for pattern, keywords, detected_from in PATTERN_RULES:
        hits = [kw for kw in keywords if re.search(re.escape(kw), corpus, re.I)]
        if not hits:
            continue

        confidence = min(0.9, 0.48 + len(hits) * 0.1)
        if domain_profile.primary_domain == PrimaryDomain.RAG_SYSTEM and pattern == ArchitecturePatternType.RAG_PIPELINE:
            confidence = min(0.95, confidence + 0.08)
        if domain_profile.primary_domain == PrimaryDomain.SPEECH_AI and pattern == ArchitecturePatternType.REAL_TIME_STREAMING:
            confidence = min(0.92, confidence + 0.06)

        related = _related_modules(contract, keywords)
        results.append(
            ArchitecturePattern(
                pattern=pattern,
                confidence=confidence,
                detected_from=detected_from,
                evidence=[f"signal:{h}" for h in hits[:4]],
                related_modules=related,
            )
        )

    results.sort(key=lambda p: p.confidence, reverse=True)
    return results[:10]
