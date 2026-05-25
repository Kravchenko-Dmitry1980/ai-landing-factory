"""Configuration for field-level fusion strategies."""

from __future__ import annotations

FIELD_STRATEGIES: dict[str, str] = {
    "title": "primary_priority_single",
    "client": "primary_metadata_priority",
    "timeline": "primary_metadata_priority",
    "lead": "primary_metadata_priority",
    "quote": "primary_metadata_priority",
    "essence": "best_plus_enrichment",
    "tasks": "union_dedupe_ranked",
    "purpose": "union_dedupe_ranked",
    "inputs": "union_dedupe_ranked",
    "outputs": "union_dedupe_ranked",
    "results": "union_dedupe_ranked",
    "outlook": "union_dedupe_ranked",
    "tech_stack": "union_grouped_tech",
    "team": "union_validated_people",
    "modules": "union_modules_with_source_priority",
}

FIELD_CAPS: dict[str, int] = {
    "tasks": 10,
    "purpose": 8,
    "inputs": 8,
    "outputs": 8,
    "results": 8,
    "outlook": 8,
    "modules": 12,
}

ROLE_PRIORITY: dict[str, int] = {
    "primary_project_doc": 100,
    "ready_landing_doc": 90,
    "supporting_presentation": 60,
    "module_presentation": 20,
    "report": 70,
    "auxiliary": 40,
    "unknown": 30,
}

PARSER_MODE_PRIORITY: dict[str, int] = {
    "structured": 95,
    "multi_source_assembly": 85,
    "project_presentation": 70,
    "heuristic": 40,
}

FORBIDDEN_TEAM_NAMES: frozenset[str] = frozenset(
    {
        "посты telegram",
        "из telegram",
        "qdrant cloud",
        "google colab",
        "схема обработки данных",
        "векторная бд",
    }
)

GENERIC_MODULE_NAMES: frozenset[str] = frozenset(
    {
        "задачи проекта",
        "этапы работы",
        "схема обработки данных",
        "пользовательский запрос → qdrant",
        "пользовательский запрос",
        "направления развития",
        "архитектура",
        "команда проекта",
    }
)

HEADING_BULLET_PATTERNS: frozenset[str] = frozenset(
    {
        "задачи проекта",
        "этапы работы",
        "схема обработки данных",
        "результаты проекта",
        "перспектива развития",
    }
)
