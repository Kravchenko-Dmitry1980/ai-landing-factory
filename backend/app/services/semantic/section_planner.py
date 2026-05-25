"""Section planning by domain profile."""

from app.schemas.semantic_generation import DomainProfile, SectionType

DOMAIN_SECTION_PLAN: dict[DomainProfile, list[SectionType]] = {
    DomainProfile.MEDICAL: [
        SectionType.ESSENCE,
        SectionType.ARCHITECTURE,
        SectionType.COMPLIANCE,
        SectionType.PIPELINE,
        SectionType.METRICS,
        SectionType.VALIDATION,
        SectionType.STACK,
        SectionType.TEAM,
        SectionType.ROADMAP,
    ],
    DomainProfile.EDUCATION: [
        SectionType.ESSENCE,
        SectionType.LEARNING_FLOW,
        SectionType.SYSTEM,
        SectionType.MODULES,
        SectionType.METRICS,
        SectionType.STACK,
        SectionType.TEAM,
        SectionType.ROADMAP,
    ],
    DomainProfile.ANALYTICS: [
        SectionType.ESSENCE,
        SectionType.DASHBOARDS,
        SectionType.PIPELINE,
        SectionType.INGESTION,
        SectionType.ORCHESTRATION,
        SectionType.METRICS,
        SectionType.STACK,
        SectionType.ROADMAP,
    ],
    DomainProfile.AI_RESEARCH: [
        SectionType.PROBLEM,
        SectionType.SYSTEM,
        SectionType.ARCHITECTURE,
        SectionType.MODULES,
        SectionType.METRICS,
        SectionType.VALIDATION,
        SectionType.STACK,
        SectionType.TEAM,
        SectionType.ROADMAP,
    ],
    DomainProfile.CYBERSECURITY: [
        SectionType.ESSENCE,
        SectionType.ARCHITECTURE,
        SectionType.COMPLIANCE,
        SectionType.PIPELINE,
        SectionType.METRICS,
        SectionType.STACK,
        SectionType.TEAM,
        SectionType.ROADMAP,
    ],
}

DEFAULT_PLAN: list[SectionType] = [
    SectionType.PROBLEM,
    SectionType.SYSTEM,
    SectionType.ARCHITECTURE,
    SectionType.MODULES,
    SectionType.METRICS,
    SectionType.STACK,
    SectionType.TEAM,
    SectionType.ROADMAP,
]

DOMAIN_LAYOUT: dict[DomainProfile, str] = {
    DomainProfile.MEDICAL: "architecture_first",
    DomainProfile.EDUCATION: "research_report",
    DomainProfile.ANALYTICS: "dashboard",
    DomainProfile.AI_RESEARCH: "technical_system",
    DomainProfile.ENTERPRISE: "enterprise_overview",
    DomainProfile.CYBERSECURITY: "architecture_first",
    DomainProfile.INFRASTRUCTURE: "technical_system",
    DomainProfile.FINTECH: "enterprise_overview",
    DomainProfile.NEURO: "research_report",
    DomainProfile.GENERAL: "architecture_first",
}

DOMAIN_STYLE: dict[DomainProfile, str] = {
    DomainProfile.MEDICAL: "medical",
    DomainProfile.EDUCATION: "education",
    DomainProfile.ANALYTICS: "analytics",
    DomainProfile.AI_RESEARCH: "ai_research",
    DomainProfile.NEURO: "ai_research",
    DomainProfile.ENTERPRISE: "enterprise",
    DomainProfile.FINTECH: "enterprise",
    DomainProfile.INFRASTRUCTURE: "enterprise",
    DomainProfile.CYBERSECURITY: "enterprise",
    DomainProfile.GENERAL: "enterprise",
}


def plan_sections(domain: DomainProfile) -> list[SectionType]:
    return list(DOMAIN_SECTION_PLAN.get(domain, DEFAULT_PLAN))


def layout_for_domain(domain: DomainProfile) -> str:
    return DOMAIN_LAYOUT.get(domain, "architecture_first")


def style_for_domain(domain: DomainProfile) -> str:
    return DOMAIN_STYLE.get(domain, "enterprise")
