"""Build lightweight project knowledge graph from contract."""

from uuid import UUID

from app.config import Settings
from app.schemas.domain_intelligence import (
    ConfidenceSummary,
    DomainProfile,
    ProjectKnowledgeGraph,
)
from app.schemas.landing_contract import LandingContract
from app.services.domain.archetype_detector import detect_archetypes
from app.services.domain.domain_classifier import classify_domain
from app.services.domain.entity_extractor import extract_entities
from app.services.domain.pattern_detector import detect_patterns
from app.services.domain.relation_builder import build_relations


def _collect_risks(contract: LandingContract, profile: DomainProfile) -> list[str]:
    risks: list[str] = []
    corpus = " ".join(b.content for b in contract.blocks).lower()
    if "pii" in corpus or "privacy" in corpus:
        risks.append("PII handling requires validation")
    if profile.primary_domain.value == "medical_ai":
        risks.extend(["Clinical validation required", "Physician-in-the-loop recommended"])
    for b in contract.blocks:
        if b.key == "results" and not b.bullets and not b.content.strip():
            risks.append("Missing measurable results in contract")
    return list(dict.fromkeys(risks))


def _collect_metrics(contract: LandingContract) -> list[str]:
    for b in contract.blocks:
        if b.key == "results":
            return [x for x in b.bullets if x.strip()][:10]
    return []


def _collect_constraints(contract: LandingContract) -> list[str]:
    constraints: list[str] = []
    for b in contract.blocks:
        text = (b.content or "").lower()
        if "gdpr" in text or "hipaa" in text or "compliance" in text:
            constraints.append(b.content[:120])
    if not constraints and any("pii" in (b.content or "").lower() for b in contract.blocks):
        constraints.append("Privacy-first data handling")
    return constraints


def _missing_knowledge(contract: LandingContract) -> list[str]:
    missing: list[str] = []
    for key in ("tasks", "inputs", "outputs", "results", "tech_stack"):
        block = next((b for b in contract.blocks if b.key == key), None)
        if not block or (not block.content.strip() and not block.bullets):
            missing.append(f"Contract block '{key}' is empty")
    return missing


def _recommendations(profile: DomainProfile, missing: list[str]) -> list[str]:
    recs: list[str] = []
    domain = profile.primary_domain.value
    if domain == "medical_ai":
        recs.extend(["Emphasize clinical workflow and audit trail", "Highlight validation metrics"])
    elif domain == "education_ai":
        recs.extend(["Show learning path personalization", "Include progress analytics"])
    elif domain == "analytics_platform":
        recs.extend(["Highlight ingestion and semantic search", "Show trend detection dashboards"])
    elif domain == "rag_system":
        recs.extend(["Document retrieval pipeline", "Knowledge base grounding"])
    if missing:
        recs.append("Fill missing contract blocks before final landing")
    return recs


def build_knowledge_graph(
    contract: LandingContract,
    settings: Settings | None = None,
) -> ProjectKnowledgeGraph:
    min_conf = getattr(settings, "domain_min_confidence", 0.45) if settings else 0.45
    max_entities = getattr(settings, "domain_graph_max_entities", 120) if settings else 120
    max_relations = getattr(settings, "domain_graph_max_relations", 240) if settings else 240

    classification = classify_domain(contract, min_confidence=min_conf)
    profile = classification.profile
    archetypes = detect_archetypes(contract, profile)
    patterns = detect_patterns(contract, profile)
    entities = extract_entities(contract, profile.primary_domain, max_entities=max_entities)
    relations = build_relations(contract, entities, patterns, max_relations=max_relations)
    missing = _missing_knowledge(contract)

    entity_conf = sum(e.confidence for e in entities) / max(len(entities), 1)
    rel_conf = sum(r.confidence for r in relations) / max(len(relations), 1)
    pattern_conf = sum(p.confidence for p in patterns) / max(len(patterns), 1)
    archetype_conf = sum(a.confidence for a in archetypes) / max(len(archetypes), 1)

    confidence_summary = ConfidenceSummary(
        overall=min(
            0.95,
            (profile.confidence + entity_conf + rel_conf + pattern_conf + archetype_conf) / 5,
        ),
        domain=profile.confidence,
        archetype=archetype_conf,
        patterns=pattern_conf,
        entities=entity_conf,
        relations=rel_conf,
    )

    return ProjectKnowledgeGraph(
        project_id=contract.project_id,
        domain_profile=profile,
        system_archetypes=archetypes,
        architecture_patterns=patterns,
        entities=entities,
        relations=relations,
        risks=_collect_risks(contract, profile),
        metrics=_collect_metrics(contract),
        constraints=_collect_constraints(contract),
        recommendations=_recommendations(profile, missing),
        missing_knowledge=missing,
        confidence_summary=confidence_summary,
    )
