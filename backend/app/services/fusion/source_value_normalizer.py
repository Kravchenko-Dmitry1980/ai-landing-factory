"""Normalize field values for fusion comparison."""

from __future__ import annotations

import re

from app.schemas.fidelity import LandingModule, TeamMember
from app.services.fusion.fusion_config import (
    FORBIDDEN_TEAM_NAMES,
    GENERIC_MODULE_NAMES,
    HEADING_BULLET_PATTERNS,
)

TECH_ALIASES: dict[str, str] = {
    "qdrant cloud": "Qdrant",
    "neo4j graph database": "Neo4j",
    "sentence transformers": "Sentence Transformers",
    "sentence-transformers": "Sentence Transformers",
    "bertopic": "BERTopic",
    "fastapi": "FastAPI",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "docker compose": "Docker Compose",
    "docker-compose": "Docker Compose",
    "google colab": "Google Colab",
    "chatgpt": "ChatGPT",
    "gigachat": "GigaChat",
}


def normalize_text_key(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())[:120]


def normalize_bullet(text: str) -> str:
    line = re.sub(r"^[\s•\-*·–]+", "", text.strip())
    line = re.sub(r"^\d+[.)]\s*", "", line)
    return re.sub(r"\s+", " ", line).strip()


def normalize_tech_name(name: str) -> str:
    key = name.strip()
    lower = key.lower()
    if lower in TECH_ALIASES:
        return TECH_ALIASES[lower]
    if lower.startswith("neo4j"):
        return "Neo4j"
    if "qdrant" in lower:
        return "Qdrant"
    if "bertopic" in lower:
        return "BERTopic"
    return key


def dedupe_strings(items: list[str], cap: int | None = None) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        normalized = normalize_bullet(item)
        if not normalized or len(normalized) < 8:
            continue
        key = normalize_text_key(normalized)
        if key in seen:
            continue
        seen.add(key)
        out.append(normalized)
        if cap and len(out) >= cap:
            break
    return out


def is_heading_bullet(text: str) -> bool:
    key = normalize_text_key(text)
    if key in HEADING_BULLET_PATTERNS:
        return True
    return len(text) < 25 and key.endswith(":")


def normalize_module_name(name: str) -> str:
    return normalize_text_key(name.replace("Компонент:", "").strip())


def is_garbage_module(name: str) -> bool:
    key = normalize_module_name(name)
    if key in GENERIC_MODULE_NAMES:
        return True
    if len(key) < 4:
        return True
    if key.startswith("slide "):
        return True
    if "→" in name and len(key) < 40:
        return True
    if "пользовательский запрос" in key and "qdrant" in key:
        return True
    return False


def normalize_team_member(member: TeamMember) -> TeamMember:
    return TeamMember(
        name=member.name.strip(),
        role=member.role.strip(),
        project_area=member.project_area.strip(),
        contributions=list(member.contributions),
    )


def normalize_person_key(name: str) -> str:
    parts = re.sub(r"https?://\S+", "", name).strip().split()
    if len(parts) >= 2:
        return f"{parts[0].lower()} {parts[1].lower()}"
    return normalize_text_key(name)


def is_forbidden_team_name(name: str) -> bool:
    return normalize_text_key(name) in FORBIDDEN_TEAM_NAMES


def merge_team_members(members: list[TeamMember]) -> list[TeamMember]:
    merged: dict[str, TeamMember] = {}
    for member in members:
        if is_forbidden_team_name(member.name):
            continue
        key = normalize_person_key(member.name)
        if not key or len(key) < 4:
            continue
        existing = merged.get(key)
        if existing is None:
            merged[key] = normalize_team_member(member)
            continue
        role = existing.role or member.role
        area = existing.project_area or member.project_area
        contributions = list(dict.fromkeys(existing.contributions + member.contributions))
        merged[key] = TeamMember(
            name=existing.name if len(existing.name) >= len(member.name) else member.name,
            role=role,
            project_area=area,
            contributions=contributions,
        )
    return list(merged.values())


def merge_modules(modules: list[LandingModule]) -> list[LandingModule]:
    merged: dict[str, LandingModule] = {}
    for mod in modules:
        if is_garbage_module(mod.name):
            continue
        key = normalize_module_name(mod.name)
        if not key:
            continue
        existing = merged.get(key)
        if existing is None:
            merged[key] = LandingModule(
                name=mod.name.strip(),
                description=mod.description.strip(),
                type=mod.type,
            )
            continue
        desc = existing.description
        if mod.description and mod.description not in desc:
            desc = f"{desc} {mod.description}".strip()[:400]
        merged[key] = LandingModule(
            name=existing.name if len(existing.name) >= len(mod.name) else mod.name,
            description=desc[:400],
            type=existing.type or mod.type,
        )
    return list(merged.values())


def merge_tech_stacks(stacks: list[dict[str, list[str]]]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    seen: set[str] = set()
    for stack in stacks:
        for category, items in stack.items():
            bucket = grouped.setdefault(category, [])
            for item in items:
                canonical = normalize_tech_name(item)
                key = canonical.lower()
                if key in seen:
                    continue
                seen.add(key)
                bucket.append(canonical)
    return grouped
