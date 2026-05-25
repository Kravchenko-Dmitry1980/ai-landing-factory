"""Validate semantic LLM output structure."""

import json
from typing import Any

from pydantic import ValidationError

from app.schemas.architecture import ArchitectureTopology
from app.schemas.semantic_generation import (
    ArchitectureNode,
    GeneratedSemanticLanding,
    SemanticNarrative,
    SemanticSection,
    SectionConfidence,
    SectionType,
)
from app.services.analysis.normalization import parse_llm_json, repair_json_text


def validate_semantic_llm_output(raw: dict | str, project_id=None) -> GeneratedSemanticLanding:
    data = parse_llm_json(repair_json_text(raw) if isinstance(raw, str) else raw)
    return _coerce_semantic(data, project_id=project_id)


def _coerce_section(item: dict) -> SemanticSection:
    conf_raw = item.get("confidence") or {}
    if isinstance(conf_raw, (int, float)):
        conf = SectionConfidence(overall=float(conf_raw))
    else:
        conf = SectionConfidence(
            overall=float(conf_raw.get("overall", conf_raw.get("score", 0.5))),
            factual_grounding=float(conf_raw.get("factual_grounding", 0.5)),
            completeness=float(conf_raw.get("completeness", 0.5)),
        )
    st = item.get("section_type", "essence")
    try:
        section_type = SectionType(st)
    except ValueError:
        section_type = st
    arch_raw = item.get("architecture_nodes") or []
    arch_nodes: list[ArchitectureNode] = []
    for n in arch_raw:
        if isinstance(n, dict) and n.get("id") and n.get("label"):
            arch_nodes.append(
                ArchitectureNode(
                    id=str(n["id"]),
                    label=str(n["label"]),
                    role=n.get("role"),
                    connections=_as_str_list(n.get("connections")),
                )
            )
    return SemanticSection(
        section_type=section_type,
        semantic_goal=str(item.get("semantic_goal", "")),
        title=str(item.get("title", "")),
        subtitle=item.get("subtitle"),
        narrative=str(item.get("narrative", "")),
        bullets=_as_str_list(item.get("bullets")),
        metrics=_as_str_list(item.get("metrics")),
        architecture_nodes=arch_nodes,
        risks=_as_str_list(item.get("risks")),
        insights=_as_str_list(item.get("insights")),
        callouts=_as_str_list(item.get("callouts")),
        visual_hints=_as_str_list(item.get("visual_hints")),
        confidence=conf,
        source_keys=_as_str_list(item.get("source_keys")),
        missing_data=_as_str_list(item.get("missing_data")),
        assumptions=_as_str_list(item.get("assumptions")),
    )


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return []


def _coerce_semantic(data: dict, project_id=None) -> GeneratedSemanticLanding:
    sections = [_coerce_section(s) for s in data.get("sections", []) if isinstance(s, dict)]
    narrative_raw = data.get("narrative") or {}
    narrative = SemanticNarrative(**narrative_raw) if isinstance(narrative_raw, dict) else SemanticNarrative()
    meta_raw = data.get("metadata") or {}
    from app.models.domain import utc_now
    from app.schemas.semantic_generation import DomainProfile, SemanticGenerationMetadata
    from uuid import UUID

    domain_str = data.get("domain") or meta_raw.get("domain") or "general"
    try:
        domain = DomainProfile(domain_str)
    except ValueError:
        domain = DomainProfile.GENERAL

    pid = project_id
    if pid is None and data.get("project_id"):
        pid = UUID(str(data["project_id"]))

    metadata = SemanticGenerationMetadata(
        provider=str(meta_raw.get("provider", "llm")),
        llm_enabled=True,
        fallback_used=False,
        domain=domain,
        layout_preset=str(data.get("layout_preset", meta_raw.get("layout_preset", "architecture_first"))),
        style_profile=str(data.get("style_profile", meta_raw.get("style_profile", "enterprise"))),
        selected_sections=[str(s.section_type) for s in sections],
        missing_fields=_as_str_list(meta_raw.get("missing_fields")),
        assumptions=_as_str_list(meta_raw.get("assumptions")),
        generated_at=utc_now(),
    )

    arch_raw = data.get("architecture")
    architecture = None
    if isinstance(arch_raw, dict):
        try:
            architecture = ArchitectureTopology(**arch_raw)
        except Exception:
            architecture = None

    return GeneratedSemanticLanding(
        project_id=pid or UUID("00000000-0000-0000-0000-000000000001"),
        domain=domain,
        layout_preset=metadata.layout_preset,
        style_profile=metadata.style_profile,
        narrative=narrative,
        sections=sections,
        architecture=architecture,
        metadata=metadata,
    )


def try_parse_semantic(raw: dict | str, project_id=None) -> GeneratedSemanticLanding | None:
    try:
        return validate_semantic_llm_output(raw, project_id=project_id)
    except (ValidationError, json.JSONDecodeError, KeyError, ValueError):
        return None
