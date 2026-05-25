"""Build relations between knowledge entities."""

from app.schemas.domain_intelligence import (
    ArchitecturePattern,
    KnowledgeEntity,
    KnowledgeRelation,
    RelationType,
)
from app.schemas.landing_contract import LandingContract
from app.services.domain.corpus import slugify

ENTITY_TYPE_RELATIONS: dict[tuple[str, str], RelationType] = {
    ("module", "technology"): RelationType.USES,
    ("module", "llm"): RelationType.USES,
    ("module", "database"): RelationType.STORES,
    ("module", "vector_db"): RelationType.RETRIEVES_FROM,
    ("pipeline", "data_source"): RelationType.CONSUMES,
    ("pipeline", "output"): RelationType.PRODUCES,
    ("ai_model", "data_source"): RelationType.TRANSFORMS,
    ("metric", "output"): RelationType.VALIDATES,
    ("security_layer", "module"): RelationType.PROTECTS,
}


def _etype(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def build_relations(
    contract: LandingContract,
    entities: list[KnowledgeEntity],
    patterns: list[ArchitecturePattern],
    max_relations: int = 240,
) -> list[KnowledgeRelation]:
    relations: list[KnowledgeRelation] = []
    seen: set[str] = set()
    by_type: dict[str, list[KnowledgeEntity]] = {}
    for e in entities:
        by_type.setdefault(_etype(e.entity_type), []).append(e)

    project_entities = by_type.get("project", [])
    modules = by_type.get("module", []) + by_type.get("pipeline", [])
    technologies = (
        by_type.get("technology", [])
        + by_type.get("llm", [])
        + by_type.get("database", [])
        + by_type.get("vector_db", [])
    )
    outputs = by_type.get("output", [])
    data_sources = by_type.get("data_source", [])
    metrics = by_type.get("metric", [])

    def add_rel(source: KnowledgeEntity, target: KnowledgeEntity, rtype: RelationType, evidence: str, inferred: bool = False):
        rid = f"{source.id}:{rtype.value}:{target.id}"
        if rid in seen:
            return
        seen.add(rid)
        relations.append(
            KnowledgeRelation(
                id=rid,
                source_id=source.id,
                target_id=target.id,
                relation_type=rtype,
                confidence=0.7 if not inferred else 0.45,
                evidence=[evidence],
                inferred=inferred,
            )
        )

    for mod in modules:
        for tech in technologies[:8]:
            add_rel(mod, tech, RelationType.USES, f"module_uses_tech:{tech.label}")

    for ds in data_sources:
        for mod in modules[:6]:
            add_rel(mod, ds, RelationType.CONSUMES, f"module_consumes:{ds.label}")

    for mod in modules:
        for out in outputs[:4]:
            add_rel(mod, out, RelationType.PRODUCES, f"module_produces:{out.label}")

    for metric in metrics:
        for out in outputs[:3]:
            add_rel(metric, out, RelationType.VALIDATES, f"metric_validates:{out.label}")

    if project_entities:
        proj = project_entities[0]
        for mod in modules[:8]:
            add_rel(proj, mod, RelationType.BELONGS_TO, "project_contains_module", inferred=True)

    for pattern in patterns:
        for mod_label in pattern.related_modules:
            mod_id = slugify(mod_label)
            mod_entity = next((e for e in entities if e.id == mod_id), None)
            if not mod_entity:
                continue
            for tech in technologies[:3]:
                add_rel(mod_entity, tech, RelationType.DEPENDS_ON, f"pattern:{pattern.pattern}", inferred=True)

    return relations[:max_relations]
