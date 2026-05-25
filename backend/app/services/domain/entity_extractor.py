"""Extract grounded knowledge entities from LandingContract."""

from app.schemas.domain_intelligence import EntityType, KnowledgeEntity, PrimaryDomain
from app.schemas.landing_contract import LandingContract
from app.services.domain.corpus import contract_corpus_lower, is_grounded, slugify, tokens_from_text

TECH_HINTS: dict[str, EntityType] = {
    "openai": EntityType.LLM,
    "gpt": EntityType.LLM,
    "llm": EntityType.LLM,
    "whisper": EntityType.SPEECH_MODEL,
    "yolo": EntityType.CV_MODEL,
    "qdrant": EntityType.VECTOR_DB,
    "postgres": EntityType.DATABASE,
    "postgresql": EntityType.DATABASE,
    "redis": EntityType.DATABASE,
    "fastapi": EntityType.API,
    "react": EntityType.TECHNOLOGY,
    "docker": EntityType.TECHNOLOGY,
    "kubernetes": EntityType.TECHNOLOGY,
}

BLOCK_ENTITY_MAP: dict[str, EntityType] = {
    "tasks": EntityType.MODULE,
    "inputs": EntityType.DATA_SOURCE,
    "outputs": EntityType.OUTPUT,
    "results": EntityType.METRIC,
    "tech_stack": EntityType.TECHNOLOGY,
    "team": EntityType.TEAM_ROLE,
}


def _infer_entity_type(label: str, default: EntityType) -> EntityType:
    lower = label.lower()
    for hint, etype in TECH_HINTS.items():
        if hint in lower:
            return etype
    if "api" in lower:
        return EntityType.API
    if "pipeline" in lower:
        return EntityType.PIPELINE
    if "model" in lower:
        return EntityType.AI_MODEL
    return default


def extract_entities(
    contract: LandingContract,
    primary_domain: PrimaryDomain,
    max_entities: int = 120,
) -> list[KnowledgeEntity]:
    corpus = contract_corpus_lower(contract)
    seen: dict[str, KnowledgeEntity] = {}

    if contract.title:
        eid = slugify(contract.title)
        seen[eid] = KnowledgeEntity(
            id=eid,
            label=contract.title[:80],
            entity_type=EntityType.PROJECT,
            description="Project title from contract",
            confidence=0.95,
            source_fields=["title"],
            evidence=["contract.title"],
            pii_safe=True,
        )

    for block in contract.blocks:
        default_type = BLOCK_ENTITY_MAP.get(block.key, EntityType.MODULE)
        tokens = tokens_from_text(block.content) + list(block.bullets)
        for token in tokens:
            if not is_grounded(token, corpus):
                continue
            eid = slugify(token)
            if eid in seen:
                continue
            etype = _infer_entity_type(token, default_type)
            seen[eid] = KnowledgeEntity(
                id=eid,
                label=token[:80],
                entity_type=etype,
                description=f"From block {block.key}",
                confidence=0.82 if block.key == "tech_stack" else 0.75,
                source_fields=[block.key],
                evidence=[f"block:{block.key}"],
                pii_safe=block.key != "team",
            )

    if primary_domain == PrimaryDomain.MEDICAL_AI:
        for kw, etype in [("clinical workflow", EntityType.PROCESS), ("validation", EntityType.PROCESS)]:
            if kw in corpus and slugify(kw) not in seen:
                seen[slugify(kw)] = KnowledgeEntity(
                    id=slugify(kw),
                    label=kw.title(),
                    entity_type=etype,
                    description="Inferred from medical domain signals",
                    confidence=0.55,
                    source_fields=["domain_inference"],
                    evidence=[f"domain:{primary_domain.value}"],
                    pii_safe=True,
                )

    entities = list(seen.values())
    entities.sort(key=lambda e: e.confidence, reverse=True)
    return entities[:max_entities]
