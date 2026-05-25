"""Parse grouped technology stack sections from landing text."""

from __future__ import annotations

import re

KNOWN_CATEGORIES = [
    "AI / LLM",
    "Backend / API",
    "Frontend",
    "Data Layer",
    "Инфраструктура",
    "DevOps",
    "Security",
]

CATEGORY_ALIASES: dict[str, str] = {
    "ai / llm": "AI / LLM",
    "ai/llm": "AI / LLM",
    "backend / api": "Backend / API",
    "backend/api": "Backend / API",
    "frontend": "Frontend",
    "data layer": "Data Layer",
    "инфраструктура": "Инфраструктура",
    "devops": "DevOps",
    "security": "Security",
}

BULLET_RE = re.compile(r"^[\s]*(?:[-•*·]|–)\s+(.+)$")


def parse_stack_section(text: str) -> dict[str, list[str]]:
    """Extract category → items mapping from tech stack block text."""
    if not text.strip():
        return {}

    lines = text.splitlines()
    result: dict[str, list[str]] = {}
    current_category: str | None = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        cat = _match_category(stripped)
        if cat:
            current_category = cat
            result.setdefault(current_category, [])
            continue

        bullet = BULLET_RE.match(stripped)
        if bullet and current_category:
            item = bullet.group(1).strip()
            if item and item not in result[current_category]:
                result[current_category].append(item)

    return result


def stack_to_bullets(grouped: dict[str, list[str]]) -> list[str]:
    """Flat bullet list preserving category grouping for contract blocks."""
    bullets: list[str] = []
    for category in KNOWN_CATEGORIES:
        items = grouped.get(category, [])
        if items:
            bullets.append(f"{category}: {', '.join(items)}")
    for category, items in grouped.items():
        if category not in KNOWN_CATEGORIES and items:
            bullets.append(f"{category}: {', '.join(items)}")
    return bullets


def _match_category(line: str) -> str | None:
    normalized = line.strip().rstrip(":").lower()
    if normalized in CATEGORY_ALIASES:
        return CATEGORY_ALIASES[normalized]
    for known in KNOWN_CATEGORIES:
        if normalized == known.lower():
            return known
    return None
