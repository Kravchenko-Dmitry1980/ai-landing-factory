"""Deterministic semantic landing from LandingContract (no LLM)."""

from uuid import UUID

from app.models.domain import utc_now
from app.schemas.landing_contract import LandingContract
from app.schemas.semantic_generation import (
    DomainProfile,
    GeneratedSemanticLanding,
    SectionConfidence,
    SectionType,
    SemanticGenerationMetadata,
    SemanticNarrative,
    SemanticSection,
    SourceTraceEntry,
)
from app.services.semantic.domain_classifier import classify_domain
from app.services.semantic.narrative_builder import build_narrative
from app.services.semantic.section_planner import layout_for_domain, plan_sections, style_for_domain

BLOCK_TO_SECTION: dict[str, SectionType] = {
    "essence": SectionType.ESSENCE,
    "purpose": SectionType.PROBLEM,
    "tasks": SectionType.MODULES,
    "inputs": SectionType.ARCHITECTURE,
    "outputs": SectionType.ARCHITECTURE,
    "results": SectionType.METRICS,
    "outlook": SectionType.ROADMAP,
    "tech_stack": SectionType.STACK,
    "team": SectionType.TEAM,
    "tagline": SectionType.ESSENCE,
}

SECTION_TITLES: dict[SectionType, str] = {
    SectionType.PROBLEM: "Problem statement",
    SectionType.SYSTEM: "System overview",
    SectionType.ARCHITECTURE: "Architecture",
    SectionType.MODULES: "Modules",
    SectionType.METRICS: "Results & metrics",
    SectionType.PIPELINE: "Processing pipeline",
    SectionType.COMPLIANCE: "Compliance",
    SectionType.VALIDATION: "Validation",
    SectionType.LEARNING_FLOW: "Learning flow",
    SectionType.DASHBOARDS: "Dashboards",
    SectionType.INGESTION: "Data ingestion",
    SectionType.ORCHESTRATION: "Orchestration",
    SectionType.ROADMAP: "Development roadmap",
    SectionType.STACK: "Technology stack",
    SectionType.TEAM: "Project team",
    SectionType.ESSENCE: "Project essence",
    SectionType.INSIGHTS: "Insights",
}


def _block(contract: LandingContract, key: str):
    for b in contract.blocks:
        if b.key == key:
            return b
    return None


def _section_from_block(
    section_type: SectionType,
    contract: LandingContract,
    source_key: str,
) -> SemanticSection | None:
    b = _block(contract, source_key)
    if not b:
        return None
    has = bool(b.content.strip()) or b.bullets
    if not has:
        return None
    conf = SectionConfidence(
        overall=0.75 if b.content else 0.6,
        factual_grounding=0.9,
        completeness=0.7 if b.bullets else 0.5,
    )
    return SemanticSection(
        section_type=section_type,
        semantic_goal=f"Present {source_key} from contract",
        title=b.title or SECTION_TITLES.get(section_type, section_type.value),
        narrative=b.content,
        bullets=list(b.bullets),
        confidence=conf,
        source_keys=[source_key],
        visual_hints=["diagram" if section_type == SectionType.ARCHITECTURE else "cards"],
    )


def generate_fallback_semantic(
    contract: LandingContract,
    domain: DomainProfile | None = None,
) -> GeneratedSemanticLanding:
    classification = classify_domain(contract)
    dom = domain or classification.domain
    narrative = build_narrative(contract)
    plan = plan_sections(dom)

    sections: list[SemanticSection] = []
    trace: list[SourceTraceEntry] = []
    missing: list[str] = []

    mapping = {
        SectionType.ESSENCE: "essence",
        SectionType.PROBLEM: "purpose",
        SectionType.MODULES: "tasks",
        SectionType.ARCHITECTURE: "inputs",
        SectionType.METRICS: "results",
        SectionType.ROADMAP: "outlook",
        SectionType.STACK: "tech_stack",
        SectionType.TEAM: "team",
        SectionType.PIPELINE: "inputs",
        SectionType.COMPLIANCE: "purpose",
        SectionType.VALIDATION: "results",
        SectionType.LEARNING_FLOW: "tasks",
        SectionType.DASHBOARDS: "results",
        SectionType.INGESTION: "inputs",
        SectionType.ORCHESTRATION: "tasks",
        SectionType.SYSTEM: "essence",
        SectionType.INSIGHTS: "results",
    }

    seen_keys: set[str] = set()
    for st in plan:
        src = mapping.get(st, "essence")
        if src in seen_keys and st != SectionType.ARCHITECTURE:
            continue
        sec = _section_from_block(st, contract, src)
        if sec:
            sections.append(sec)
            seen_keys.add(src)
            trace.append(
                SourceTraceEntry(
                    field=src,
                    section_type=str(st.value),
                    source_key=src,
                    evidence=(sec.narrative or sec.bullets[0] if sec.bullets else "")[:200],
                )
            )
        else:
            missing.append(str(st.value))

    if contract.quote or contract.title:
        sections.insert(
            0,
            SemanticSection(
                section_type=SectionType.ESSENCE,
                semantic_goal="Lead narrative",
                title=contract.title or "Project overview",
                subtitle=contract.timeline,
                narrative=contract.quote or contract.lead or "",
                bullets=[f"Client: {contract.client}"] if contract.client else [],
                confidence=SectionConfidence(overall=0.8, factual_grounding=0.95, completeness=0.6),
                source_keys=["tagline", "title"],
            ),
        )

    meta = SemanticGenerationMetadata(
        provider="fallback",
        llm_enabled=False,
        fallback_used=True,
        domain=dom,
        layout_preset=layout_for_domain(dom),
        style_profile=style_for_domain(dom),
        selected_sections=[str(s.section_type) for s in sections],
        missing_fields=missing,
        assumptions=["Deterministic mapping from LandingContract blocks"],
        source_trace=trace,
        generated_at=utc_now(),
        prompt_version="semantic-fallback-v1",
    )

    return GeneratedSemanticLanding(
        project_id=contract.project_id,
        domain=dom,
        layout_preset=meta.layout_preset,
        style_profile=meta.style_profile,
        narrative=narrative,
        sections=sections,
        metadata=meta,
    )
