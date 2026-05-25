"""Validate domain intelligence report — hallucination guard."""

import re

from app.schemas.domain_intelligence import (
    DomainIntelligenceReport,
    KnowledgeEntity,
    ProjectKnowledgeGraph,
)
from app.schemas.landing_contract import LandingContract
from app.services.domain.corpus import contract_corpus_lower, is_grounded

PII_PATTERNS = [
    re.compile(r"\b[\w.-]+@[\w.-]+\.\w+\b"),
    re.compile(r"\b\+?\d[\d\s\-()]{8,}\d\b"),
]

FORBIDDEN_IN_REPORT = ("@gmail", "@mail", "passport", "inn ", "снилс")


def _has_pii(text: str) -> bool:
    for pat in PII_PATTERNS:
        if pat.search(text):
            return True
    return any(f in text.lower() for f in FORBIDDEN_IN_REPORT)


def _validate_entity(entity: KnowledgeEntity, corpus: str) -> list[str]:
    warnings: list[str] = []
    if entity.source_fields == ["domain_inference"] and entity.confidence > 0.6:
        warnings.append(f"Entity '{entity.label}' is pattern-inferred with high confidence")
    if entity.source_fields != ["domain_inference"] and not is_grounded(entity.label, corpus):
        warnings.append(f"Entity '{entity.label}' not grounded in contract")
    if not entity.pii_safe:
        warnings.append(f"Entity '{entity.label}' marked not PII-safe")
    return warnings


def validate_domain_report(
    contract: LandingContract,
    graph: ProjectKnowledgeGraph,
) -> tuple[list[str], list[str], ProjectKnowledgeGraph]:
    """Return warnings, rejected labels, and cleaned graph."""
    corpus = contract_corpus_lower(contract)
    warnings: list[str] = []
    rejected: list[str] = []

    clean_entities: list[KnowledgeEntity] = []
    labels_seen: set[str] = set()

    for entity in graph.entities:
        label_key = entity.label.lower().strip()
        if label_key in labels_seen:
            warnings.append(f"Duplicate entity label: {entity.label}")
            continue
        labels_seen.add(label_key)

        if _has_pii(entity.label) or _has_pii(entity.description):
            rejected.append(entity.label)
            warnings.append(f"PII rejected from entity: {entity.label[:30]}")
            continue

        if entity.source_fields != ["domain_inference"] and not is_grounded(entity.label, corpus):
            if entity.entity_type in ("team_role",):
                rejected.append(entity.label)
                continue
            if entity.confidence < 0.5:
                rejected.append(entity.label)
                continue

        entity_warnings = _validate_entity(entity, corpus)
        warnings.extend(entity_warnings)
        clean_entities.append(entity)

    entity_ids = {e.id for e in clean_entities}
    clean_relations = [
        r for r in graph.relations
        if r.source_id in entity_ids and r.target_id in entity_ids
    ]
    orphan_modules = [
        e.label for e in clean_entities
        if str(e.entity_type) in ("module", "EntityType.MODULE")
        and not any(r.source_id == e.id or r.target_id == e.id for r in clean_relations)
    ]
    if len(orphan_modules) > 3:
        warnings.append(f"Orphan modules detected: {', '.join(orphan_modules[:5])}")

    if not graph.confidence_summary.overall:
        warnings.append("confidence_summary.overall missing — will be computed")

    clean_graph = graph.model_copy(
        update={"entities": clean_entities, "relations": clean_relations}
    )
    return warnings, rejected, clean_graph


def validate_report(report: DomainIntelligenceReport, contract: LandingContract) -> DomainIntelligenceReport:
    warnings, _, clean_graph = validate_domain_report(contract, report.graph)
    all_warnings = list(dict.fromkeys(report.warnings + warnings))
    return report.model_copy(update={"graph": clean_graph, "warnings": all_warnings})
