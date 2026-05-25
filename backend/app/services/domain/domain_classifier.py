"""Hybrid domain classifier — deterministic keyword rules + optional LLM."""

import re
from dataclasses import dataclass

from app.schemas.domain_intelligence import DomainProfile, PrimaryDomain
from app.schemas.landing_contract import LandingContract
from app.services.domain.corpus import contract_corpus_lower

DOMAIN_KEYWORDS: dict[PrimaryDomain, tuple[str, ...]] = {
    PrimaryDomain.MEDICAL_AI: (
        "окт", "oct", "врач", "doctor", "диагноз", "diagnosis", "клиническ",
        "clinical", "пациент", "patient", "медиц", "medical", "hospital",
        "glaucoma", "глауком", "ophthalm",
    ),
    PrimaryDomain.EDUCATION_AI: (
        "cefr", "lesson", "tutor", "student", "learning path", "обучен",
        "курс", "course", "учеб", "education", "teacher", "curriculum",
    ),
    PrimaryDomain.ENTERPRISE_AI: (
        "enterprise", "corporate", "organization", "корпорат", "b2b", "saas",
    ),
    PrimaryDomain.ANALYTICS_PLATFORM: (
        "analytics", "dashboard", "kpi", "clustering", "trend", "аналит",
        "дашборд", "semantic search", "indlab",
    ),
    PrimaryDomain.NEUROASSISTANT: (
        "neuro", "brain", "eeg", "нейро", "cognitive", "neuroassistant",
    ),
    PrimaryDomain.RAG_SYSTEM: (
        "rag", "retrieval", "vector", "qdrant", "embedding", "knowledge base",
        "chromadb", "pinecone", "faiss",
    ),
    PrimaryDomain.MULTI_AGENT_SYSTEM: (
        "agent", "orchestrator", "planner", "critic", "multi-agent", "crew",
        "autogen", "langgraph",
    ),
    PrimaryDomain.COMPUTER_VISION: (
        "yolo", "detection", "bbox", "image", "cv", "segmentation", "opencv",
        "computer vision", "classification model",
    ),
    PrimaryDomain.SPEECH_AI: (
        "stt", "whisper", "diarization", "audio", "transcript", "speech",
        "asr", "tts", "voice",
    ),
    PrimaryDomain.HR_AI: (
        "hr", "recruitment", "hiring", "candidate", "resume", "кадр", "hrtech",
    ),
    PrimaryDomain.SALES_AI: (
        "crm", "sales", "lead", "conversion", "pipeline", "продаж", "лид",
    ),
    PrimaryDomain.DOCUMENT_AI: (
        "docx", "pdf", "document processing", "ocr", "extraction", "парсинг",
        "document ai",
    ),
    PrimaryDomain.INFRASTRUCTURE_AI: (
        "kubernetes", "devops", "cloud", "infrastructure", "terraform",
        "microservice deploy", "инфраструктур",
    ),
}


@dataclass
class DomainClassificationResult:
    profile: DomainProfile
    signals: list[str]


def classify_domain(contract: LandingContract, min_confidence: float = 0.45) -> DomainClassificationResult:
    corpus = contract_corpus_lower(contract)
    if not corpus.strip():
        return DomainClassificationResult(
            profile=DomainProfile(
                primary_domain=PrimaryDomain.GENERAL,
                confidence=0.3,
                evidence=["empty_contract"],
                warnings=["No contract content for domain classification"],
            ),
            signals=["empty_contract"],
        )

    scores: dict[PrimaryDomain, int] = {}
    signals: list[str] = []
    for domain, keywords in DOMAIN_KEYWORDS.items():
        hits = 0
        for kw in keywords:
            if re.search(re.escape(kw), corpus, re.I):
                hits += 1
                if len(signals) < 12:
                    signals.append(f"{domain.value}:{kw}")
        if hits:
            scores[domain] = hits

    if not scores:
        return DomainClassificationResult(
            profile=DomainProfile(
                primary_domain=PrimaryDomain.GENERAL,
                confidence=0.4,
                evidence=["no_domain_signals"],
            ),
            signals=["no_domain_signals"],
        )

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_domain, best_score = ranked[0]
    total = sum(scores.values())
    confidence = min(0.95, 0.45 + best_score / max(total, 1) * 0.5)

    secondary: list[PrimaryDomain] = []
    for domain, score in ranked[1:3]:
        if score >= best_score * 0.5:
            secondary.append(domain)

    warnings: list[str] = []
    if confidence < min_confidence:
        warnings.append(f"Domain confidence {confidence:.2f} below threshold {min_confidence}")

    evidence = [f"keyword_hits:{best_score}", *signals[:6]]
    return DomainClassificationResult(
        profile=DomainProfile(
            primary_domain=best_domain,
            secondary_domains=secondary,
            confidence=confidence,
            evidence=evidence,
            warnings=warnings,
        ),
        signals=signals,
    )
