"""Extract candidate nodes from contract + semantic payload."""

import re

from app.schemas.landing_contract import LandingContract
from app.schemas.semantic_generation import GeneratedSemanticLanding, SectionType
from app.services.architecture.node_normalizer import normalize_label, normalize_node_type, slugify
from app.schemas.architecture import TopologyNode
from app.schemas.domain_intelligence import ProjectKnowledgeGraph

_ARCH_SECTIONS = {
    SectionType.ARCHITECTURE,
    SectionType.PIPELINE,
    SectionType.ORCHESTRATION,
    SectionType.STACK,
    SectionType.INGESTION,
    SectionType.SYSTEM,
    SectionType.MODULES,
}

_SPLIT_RE = re.compile(r"[,;|\n•·]+")


def _corpus_text(contract: LandingContract, semantic: GeneratedSemanticLanding | None) -> str:
    parts: list[str] = []
    for b in contract.blocks:
        parts.append(b.content or "")
        parts.extend(b.bullets)
    if semantic:
        for s in semantic.sections:
            parts.append(s.narrative or "")
            parts.extend(s.bullets)
        n = semantic.narrative
        parts.extend([n.problem, n.system, n.architecture, n.modules])
    return " ".join(parts).lower()


def _is_grounded(label: str, corpus: str) -> bool:
    norm = label.lower().strip()
    if len(norm) < 3:
        return False
    if norm in corpus:
        return True
    tokens = [t for t in re.split(r"\W+", norm) if len(t) > 2]
    if not tokens:
        return False
    return sum(1 for t in tokens if t in corpus) >= max(1, len(tokens) // 2)


def _tokens_from_text(text: str) -> list[str]:
    items: list[str] = []
    for chunk in _SPLIT_RE.split(text):
        chunk = chunk.strip(" -–—•")
        if 2 < len(chunk) <= 80:
            items.append(chunk)
    return items


def _add_node(
    seen: dict[str, TopologyNode],
    label: str,
    source: str,
    corpus: str,
    *,
    inferred: bool = False,
) -> None:
    label = normalize_label(label)
    if not label or len(label) < 2:
        return
    grounded = _is_grounded(label, corpus)
    if not grounded and not inferred:
        return
    node_id = slugify(label)
    if node_id in seen:
        existing = seen[node_id]
        if source not in existing.source:
            seen[node_id] = existing.model_copy(
                update={"source": list(dict.fromkeys([*existing.source, source]))}
            )
        return
    nt = normalize_node_type(label)
    confidence = 0.85 if grounded else 0.45
    seen[node_id] = TopologyNode(
        id=node_id,
        label=label,
        node_type=nt,
        confidence=confidence,
        source=[source],
        inferred=inferred or not grounded,
    )


def extract_nodes(
    contract: LandingContract,
    semantic: GeneratedSemanticLanding | None = None,
    knowledge_graph: ProjectKnowledgeGraph | None = None,
) -> list[TopologyNode]:
    corpus = _corpus_text(contract, semantic)
    seen: dict[str, TopologyNode] = {}

    for key in ("inputs", "outputs", "tech_stack", "tasks"):
        block = next((b for b in contract.blocks if b.key == key), None)
        if not block:
            continue
        for item in _tokens_from_text(block.content or ""):
            _add_node(seen, item, key, corpus)
        for bullet in block.bullets:
            _add_node(seen, bullet, key, corpus)

    if semantic:
        for section in semantic.sections:
            st = section.section_type.value if hasattr(section.section_type, "value") else str(
                section.section_type
            )
            try:
                section_enum = SectionType(st)
            except ValueError:
                section_enum = None
            if section_enum and section_enum not in _ARCH_SECTIONS:
                continue
            for bullet in section.bullets:
                _add_node(seen, bullet, st, corpus)
            for node in section.architecture_nodes:
                _add_node(seen, node.label, st, corpus, inferred=False)

    if knowledge_graph:
        for entity in knowledge_graph.entities[:40]:
            etype = entity.entity_type.value if hasattr(entity.entity_type, "value") else str(entity.entity_type)
            if etype in ("team_role", "stakeholder") and not entity.pii_safe:
                continue
            _add_node(
                seen,
                entity.label,
                f"kg:{etype}",
                corpus,
                inferred=entity.source_fields == ["domain_inference"],
            )

    # Pipeline anchors from inputs/outputs when present
    inputs_block = next((b for b in contract.blocks if b.key == "inputs"), None)
    outputs_block = next((b for b in contract.blocks if b.key == "outputs"), None)
    if inputs_block and (inputs_block.content or inputs_block.bullets):
        _add_node(seen, "Data Ingestion", "inputs", corpus, inferred=True)
    if outputs_block and (outputs_block.content or outputs_block.bullets):
        _add_node(seen, "Output Delivery", "outputs", corpus, inferred=True)

    return list(seen.values())
