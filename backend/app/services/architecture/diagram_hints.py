"""Infer diagram type from domain and section signals."""

from app.schemas.architecture import DiagramType
from app.schemas.semantic_generation import DomainProfile, GeneratedSemanticLanding, SectionType


def infer_diagram_type(
    semantic: GeneratedSemanticLanding | None,
    domain: DomainProfile | str | None = None,
    knowledge_graph=None,
) -> DiagramType:
    section_types = set()
    if semantic:
        for s in semantic.sections:
            st = s.section_type.value if hasattr(s.section_type, "value") else str(s.section_type)
            section_types.add(st)

    domain_val = domain.value if hasattr(domain, "value") else str(domain or "general")

    if knowledge_graph:
        pattern_names = [
            p.pattern.value if hasattr(p.pattern, "value") else str(p.pattern)
            for p in knowledge_graph.architecture_patterns
        ]
        if any("rag" in p for p in pattern_names):
            return DiagramType.RESEARCH_GRAPH
        if any("pipeline" in p or "ingestion" in p for p in pattern_names):
            return DiagramType.PIPELINE
        if any("speech" in p or "streaming" in p for p in pattern_names):
            return DiagramType.PIPELINE
        archetypes = [
            a.archetype.value if hasattr(a.archetype, "value") else str(a.archetype)
            for a in knowledge_graph.system_archetypes
        ]
        if any("Multi-Agent" in a for a in archetypes):
            return DiagramType.HUB_SPOKE
        if any("Analytics" in a for a in archetypes):
            return DiagramType.DASHBOARD_FLOW

    if SectionType.PIPELINE.value in section_types or SectionType.INGESTION.value in section_types:
        return DiagramType.PIPELINE
    if domain_val == DomainProfile.AI_RESEARCH.value:
        return DiagramType.RESEARCH_GRAPH
    if domain_val == DomainProfile.ANALYTICS.value or SectionType.DASHBOARDS.value in section_types:
        return DiagramType.DASHBOARD_FLOW
    if SectionType.ORCHESTRATION.value in section_types:
        return DiagramType.HUB_SPOKE
    if len(section_types) >= 6:
        return DiagramType.MICROSERVICES
    if domain_val in (DomainProfile.ENTERPRISE.value, DomainProfile.INFRASTRUCTURE.value):
        return DiagramType.LAYERED
    return DiagramType.PIPELINE
