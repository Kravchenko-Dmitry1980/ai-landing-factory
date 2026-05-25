"""Hybrid domain classifier from LandingContract text."""

import re
from dataclasses import dataclass

from app.schemas.landing_contract import LandingContract
from app.schemas.semantic_generation import DomainProfile

DOMAIN_KEYWORDS: dict[DomainProfile, tuple[str, ...]] = {
    DomainProfile.MEDICAL: (
        "medical", "clinical", "patient", "hospital", "diagnosis", "медиц", "клиник", "пациент",
    ),
    DomainProfile.EDUCATION: (
        "education", "learning", "course", "student", "обучен", "курс", "студент", "учеб",
    ),
    DomainProfile.AI_RESEARCH: (
        "ai", "ml", "model", "research", "llm", "neural", "исследован", "модель", "нейро",
    ),
    DomainProfile.ANALYTICS: (
        "analytics", "dashboard", "metrics", "kpi", "аналит", "дашборд", "метрик", "отчет",
    ),
    DomainProfile.ENTERPRISE: (
        "enterprise", "corporate", "organization", "корпорат", "предприят", "организац",
    ),
    DomainProfile.NEURO: ("neuro", "brain", "eeg", "нейро", "мозг"),
    DomainProfile.FINTECH: ("fintech", "bank", "payment", "finance", "финтех", "банк", "платеж"),
    DomainProfile.INFRASTRUCTURE: (
        "infrastructure", "cloud", "devops", "kubernetes", "инфраструктур", "облак",
    ),
    DomainProfile.CYBERSECURITY: (
        "security", "cyber", "compliance", "audit", "безопасност", "кибер", "комплаенс",
    ),
}


@dataclass
class DomainClassification:
    domain: DomainProfile
    confidence: float
    signals: list[str]


def _contract_corpus(contract: LandingContract) -> str:
    parts: list[str] = []
    for field in (contract.title, contract.client, contract.lead, contract.quote):
        if field:
            parts.append(field)
    parts.extend(contract.goals)
    for block in contract.blocks:
        parts.append(block.title)
        parts.append(block.content)
        parts.extend(block.bullets)
    return "\n".join(parts).lower()


def classify_domain(contract: LandingContract) -> DomainClassification:
    corpus = _contract_corpus(contract)
    if not corpus.strip():
        return DomainClassification(DomainProfile.GENERAL, 0.3, ["empty_contract"])

    scores: dict[DomainProfile, int] = {}
    signals: list[str] = []
    for domain, keywords in DOMAIN_KEYWORDS.items():
        hits = 0
        for kw in keywords:
            if re.search(re.escape(kw), corpus, re.I):
                hits += 1
                if len(signals) < 8:
                    signals.append(f"{domain.value}:{kw}")
        if hits:
            scores[domain] = hits

    if not scores:
        return DomainClassification(DomainProfile.GENERAL, 0.4, ["no_domain_signals"])

    best = max(scores, key=scores.get)
    total = sum(scores.values())
    confidence = min(0.95, 0.45 + scores[best] / max(total, 1) * 0.5)
    return DomainClassification(best, confidence, signals)
