"""Parse grouped technology stack sections from landing text."""

from __future__ import annotations

import re

KNOWN_CATEGORIES = [
    "AI / LLM",
    "AI & CV",
    "Backend / API",
    "Frontend",
    "UI & Frontend",
    "Data Layer",
    "Data & Annotation",
    "Compliance Engine",
    "Infrastructure",
    "Инфраструктура",
    "DevOps",
    "Security",
]

CATEGORY_ALIASES: dict[str, str] = {
    "ai / llm": "AI / LLM",
    "ai/llm": "AI / LLM",
    "ai & cv": "AI & CV",
    "ai&cv": "AI & CV",
    "ai and cv": "AI & CV",
    "computer vision": "AI & CV",
    "cv": "AI & CV",
    "backend / api": "Backend / API",
    "backend/api": "Backend / API",
    "frontend": "Frontend",
    "ui & frontend": "UI & Frontend",
    "ui/frontend": "UI & Frontend",
    "data layer": "Data Layer",
    "data & annotation": "Data & Annotation",
    "data and annotation": "Data & Annotation",
    "annotation": "Data & Annotation",
    "compliance engine": "Compliance Engine",
    "compliance": "Compliance Engine",
    "process compliance engine": "Compliance Engine",
    "fsm": "Compliance Engine",
    "infrastructure": "Infrastructure",
    "инфраструктура": "Инфраструктура",
    "devops": "DevOps",
    "security": "Security",
}

BULLET_RE = re.compile(r"^[\s]*(?:[-•*·]|–)\s+(.+)$")
INLINE_CATEGORY_RE = re.compile(r"^([^:]{2,60}?)\s*:\s*(.+)$")


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
            # Inline "Category: a, b, c" on the same line.
            inline = INLINE_CATEGORY_RE.match(stripped)
            if inline and inline.group(2).strip():
                for item in _split_items(inline.group(2)):
                    if item not in result[current_category]:
                        result[current_category].append(item)
            continue

        inline = INLINE_CATEGORY_RE.match(stripped)
        if inline:
            maybe_cat = _match_category(inline.group(1))
            if maybe_cat:
                current_category = maybe_cat
                result.setdefault(current_category, [])
                for item in _split_items(inline.group(2)):
                    if item not in result[current_category]:
                        result[current_category].append(item)
                continue

        bullet = BULLET_RE.match(stripped)
        payload = bullet.group(1).strip() if bullet else stripped
        if current_category:
            for item in _split_items(payload) if "," in payload else [payload]:
                cleaned = item.strip()
                if cleaned and cleaned not in result[current_category]:
                    result[current_category].append(cleaned)

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
    # Strip trailing payload for "Category: items".
    if ":" in normalized:
        normalized = normalized.split(":", 1)[0].strip()
    if normalized in CATEGORY_ALIASES:
        return CATEGORY_ALIASES[normalized]
    for known in KNOWN_CATEGORIES:
        if normalized == known.lower():
            return known
    return None


def _split_items(text: str) -> list[str]:
    """Split comma-separated tech items, keeping commas inside parentheses."""
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    for ch in text:
        if ch == "(":
            depth += 1
            buf.append(ch)
        elif ch == ")":
            depth = max(depth - 1, 0)
            buf.append(ch)
        elif ch == "," and depth == 0:
            item = "".join(buf).strip().strip(".;")
            if item:
                parts.append(item)
            buf = []
        else:
            buf.append(ch)
    item = "".join(buf).strip().strip(".;")
    if item:
        parts.append(item)
    return parts
