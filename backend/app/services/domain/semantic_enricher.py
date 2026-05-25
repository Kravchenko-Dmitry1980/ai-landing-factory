"""Enrich semantic narrative and sections using domain intelligence report."""

from app.schemas.domain_intelligence import DomainIntelligenceReport, PrimaryDomain
from app.schemas.landing_contract import LandingContract
from app.schemas.semantic_generation import (
    GeneratedSemanticLanding,
    SectionConfidence,
    SectionType,
    SemanticNarrative,
    SemanticSection,
)


def _domain_focus(primary: PrimaryDomain) -> dict[str, str]:
    mapping = {
        PrimaryDomain.MEDICAL_AI: {
            "tone": "clinical-safety-first",
            "focus": "clinical workflow, validation, audit, safety, physician-in-the-loop",
        },
        PrimaryDomain.EDUCATION_AI: {
            "tone": "learning-centric",
            "focus": "learning path, personalization, progress analytics, CEFR, engagement",
        },
        PrimaryDomain.ANALYTICS_PLATFORM: {
            "tone": "data-driven",
            "focus": "ingestion, semantic search, dashboards, trend detection, data quality",
        },
        PrimaryDomain.RAG_SYSTEM: {
            "tone": "knowledge-grounded",
            "focus": "retrieval pipeline, embeddings, knowledge base, grounding",
        },
        PrimaryDomain.SPEECH_AI: {
            "tone": "realtime-pipeline",
            "focus": "STT, diarization, structuring, medical record integration",
        },
        PrimaryDomain.MULTI_AGENT_SYSTEM: {
            "tone": "orchestration-first",
            "focus": "agent roles, planner, critic, orchestration flow",
        },
    }
    return mapping.get(primary, {"tone": "engineering-first", "focus": "system architecture and modules"})


def apply_domain_intelligence(
    semantic: GeneratedSemanticLanding,
    contract: LandingContract,
    report: DomainIntelligenceReport,
) -> GeneratedSemanticLanding:
    graph = report.graph
    profile = graph.domain_profile
    focus = _domain_focus(profile.primary_domain)

    narrative = semantic.narrative.model_copy(
        update={
            "tone": focus["tone"],
            "architecture": (
                semantic.narrative.architecture
                + f"\nDomain focus: {focus['focus']}"
            ).strip()[:800],
        }
    )

    extra_sections: list[SemanticSection] = []
    if graph.risks and not any(
        (s.section_type.value if hasattr(s.section_type, "value") else str(s.section_type)) == "compliance"
        for s in semantic.sections
    ):
        extra_sections.append(
            SemanticSection(
                section_type=SectionType.COMPLIANCE,
                title="Risks & constraints",
                bullets=graph.risks[:6],
                narrative="; ".join(graph.constraints[:3]),
                confidence=SectionConfidence(overall=0.7, factual_grounding=0.85),
                source_keys=["domain_intelligence"],
            )
        )

    if graph.metrics:
        for section in semantic.sections:
            st = section.section_type.value if hasattr(section.section_type, "value") else str(section.section_type)
            if st == "metrics" and not section.metrics:
                idx = semantic.sections.index(section)
                semantic.sections[idx] = section.model_copy(update={"metrics": graph.metrics[:8]})
                break

    metadata = semantic.metadata.model_copy(
        update={
            "domain_intelligence_id": str(report.project_id),
            "assumptions": list(
                dict.fromkeys(semantic.metadata.assumptions + report.assumptions[:5])
            ),
        }
    )

    return semantic.model_copy(
        update={
            "narrative": narrative,
            "sections": [*semantic.sections, *extra_sections],
            "metadata": metadata,
            "intelligence_domain_profile": profile.model_dump(),
            "system_archetypes": [a.model_dump() for a in graph.system_archetypes],
            "architecture_patterns": [p.model_dump() for p in graph.architecture_patterns],
        }
    )
