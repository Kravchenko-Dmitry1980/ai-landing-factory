"""Build FieldEvidence map from evidence items."""

from __future__ import annotations

from app.schemas.evidence import EvidenceItem, FieldEvidence, SourceInventoryItem

CONTRACT_FIELDS = (
    "title", "client", "timeline", "essence", "tasks", "purpose",
    "inputs", "outputs", "results", "outlook", "tech_stack", "team", "modules",
)

FIELD_TEXT_HINTS: dict[str, list[str]] = {
    "tasks": ["задачи проекта", "этапы работы"],
    "purpose": ["цели проекта", "главная цель", "польза проекта"],
    "inputs": ["исходные данные", "входные данные", "подготовка данных"],
    "outputs": ["выходные данные", "пользовательский интерфейс"],
    "results": ["метрики и результаты", "достигнутые показатели"],
    "outlook": ["направления развития", "планы по расширению"],
    "essence": ["цели проекта", "контекст и цель"],
    "modules": ["архитектура пайплайна", "семантический поиск"],
}

SOURCE_PRIORITY: dict[str, dict[str, float]] = {
    "title": {"ready_landing_doc": 1.0, "pptx_project_presentation": 0.9},
    "inputs": {"technical_spec": 1.0, "pptx_project_presentation": 0.7},
    "outputs": {"technical_spec": 1.0, "pptx_project_presentation": 0.75},
    "team": {"team_list": 1.0, "ready_landing_doc": 0.9},
    "results": {"report": 1.0, "pptx_project_presentation": 0.7},
    "outlook": {"report": 1.0, "pptx_project_presentation": 0.6},
    "modules": {"pptx_project_presentation": 1.0, "architecture_doc": 0.9},
    "essence": {"ready_landing_doc": 1.0, "pptx_project_presentation": 0.85},
}

SOURCE_ROLE_PRIORITY: dict[str, dict[str, float]] = {
    "title": {
        "primary_project_doc": 1.0,
        "supporting_presentation": 0.45,
        "module_presentation": 0.05,
    },
    "client": {
        "primary_project_doc": 1.0,
        "supporting_presentation": 0.3,
        "module_presentation": 0.05,
    },
    "timeline": {
        "primary_project_doc": 1.0,
        "supporting_presentation": 0.5,
        "module_presentation": 0.05,
    },
    "essence": {
        "primary_project_doc": 1.0,
        "module_presentation": 0.55,
        "supporting_presentation": 0.5,
    },
    "tasks": {"primary_project_doc": 1.0, "supporting_presentation": 0.6},
    "purpose": {"primary_project_doc": 1.0, "supporting_presentation": 0.6},
    "inputs": {"primary_project_doc": 0.95, "technical_spec": 1.0},
    "outputs": {"primary_project_doc": 0.95, "technical_spec": 1.0},
    "results": {"primary_project_doc": 0.95, "report": 1.0},
    "outlook": {"primary_project_doc": 0.95, "report": 1.0},
    "team": {"primary_project_doc": 0.95, "team_source": 1.0, "team_list": 1.0},
    "modules": {
        "primary_project_doc": 1.0,
        "module_presentation": 0.85,
        "supporting_presentation": 0.75,
    },
    "tech_stack": {
        "primary_project_doc": 0.95,
        "module_presentation": 0.8,
        "supporting_presentation": 0.7,
    },
}


class FieldEvidenceBuilder:
    """Group evidence items by target contract field."""

    def build(
        self,
        items: list[EvidenceItem],
        inventory: list[SourceInventoryItem],
    ) -> dict[str, FieldEvidence]:
        inv_map = {s.source_id: s for s in inventory}
        fields: dict[str, FieldEvidence] = {}

        for field_name in CONTRACT_FIELDS:
            hints = FIELD_TEXT_HINTS.get(field_name, [])
            matched = [
                it for it in items
                if field_name in it.field_candidates
                or any(h in it.normalized_text.lower() for h in hints)
            ]
            matched.sort(
                key=lambda it: _item_score(it, inv_map.get(it.source_id), field_name),
                reverse=True,
            )
            selected = [it.normalized_text[:800] for it in matched[:8]]
            refs = [
                f"{it.filename}#{it.location_type}:{it.location_index}"
                for it in matched[:8]
            ]
            confidence = _field_confidence(matched)
            coverage = _coverage(field_name, matched, selected)

            fields[field_name] = FieldEvidence(
                field_name=field_name,
                items=matched,
                confidence=confidence,
                coverage=coverage,
                selected_texts=selected,
                source_refs=refs,
            )
        return fields


def _item_score(
    item: EvidenceItem,
    inv: SourceInventoryItem | None,
    field_name: str,
) -> float:
    score = item.confidence
    if inv:
        role_pri = SOURCE_ROLE_PRIORITY.get(field_name, {})
        score += role_pri.get(inv.source_role, 0.15) * 0.6
        pri = SOURCE_PRIORITY.get(field_name, {})
        score += pri.get(inv.detected_source_type, 0.2) * 0.35
        score += inv.confidence * 0.2
    score += min(len(item.normalized_text) / 500, 0.3)
    if (
        item.location_type == "slide"
        and field_name == "title"
        and item.location_index == 1
        and (not inv or inv.source_role != "module_presentation")
    ):
        score += 0.15
    return score


def _field_confidence(items: list[EvidenceItem]) -> float:
    if not items:
        return 0.0
    return round(min(sum(i.confidence for i in items[:5]) / 5 + 0.1, 1.0), 3)


def _coverage(field_name: str, items: list[EvidenceItem], selected: list[str]) -> str:
    if not items:
        return "missing"
    text_len = sum(len(s) for s in selected)
    mins = {
        "title": 15, "essence": 200, "tasks": 80, "purpose": 60,
        "inputs": 60, "outputs": 60, "results": 60, "outlook": 40,
        "tech_stack": 10, "team": 5, "modules": 40,
    }
    if field_name == "title":
        return "strong" if text_len >= mins["title"] else "weak"
    if text_len >= mins.get(field_name, 50) and len(items) >= 1:
        if field_name in ("tasks", "modules") and len(items) < 2:
            return "weak"
        return "strong"
    if text_len > 0:
        return "weak"
    return "missing"
