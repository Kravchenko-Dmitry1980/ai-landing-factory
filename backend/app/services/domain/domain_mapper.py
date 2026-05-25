"""Map Stage G primary domains to Stage E semantic DomainProfile."""

from app.schemas.domain_intelligence import PrimaryDomain
from app.schemas.semantic_generation import DomainProfile

PRIMARY_TO_SEMANTIC: dict[PrimaryDomain, DomainProfile] = {
    PrimaryDomain.MEDICAL_AI: DomainProfile.MEDICAL,
    PrimaryDomain.EDUCATION_AI: DomainProfile.EDUCATION,
    PrimaryDomain.ENTERPRISE_AI: DomainProfile.ENTERPRISE,
    PrimaryDomain.ANALYTICS_PLATFORM: DomainProfile.ANALYTICS,
    PrimaryDomain.NEUROASSISTANT: DomainProfile.NEURO,
    PrimaryDomain.RAG_SYSTEM: DomainProfile.AI_RESEARCH,
    PrimaryDomain.MULTI_AGENT_SYSTEM: DomainProfile.AI_RESEARCH,
    PrimaryDomain.COMPUTER_VISION: DomainProfile.AI_RESEARCH,
    PrimaryDomain.SPEECH_AI: DomainProfile.MEDICAL,
    PrimaryDomain.HR_AI: DomainProfile.ENTERPRISE,
    PrimaryDomain.SALES_AI: DomainProfile.ENTERPRISE,
    PrimaryDomain.DOCUMENT_AI: DomainProfile.ENTERPRISE,
    PrimaryDomain.INFRASTRUCTURE_AI: DomainProfile.INFRASTRUCTURE,
    PrimaryDomain.GENERAL: DomainProfile.GENERAL,
}


def map_to_semantic_domain(primary: PrimaryDomain) -> DomainProfile:
    return PRIMARY_TO_SEMANTIC.get(primary, DomainProfile.GENERAL)
