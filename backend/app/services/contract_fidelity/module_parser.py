"""Parse numbered module/system descriptions from essence section."""

from __future__ import annotations

import re

from app.schemas.fidelity import LandingModule

MODULE_INTRO_RE = re.compile(
    r"разрабатывал(?:ись|и)\s+(?:три|несколько|\d+)\s+ключев(?:ые|ых)\s+систем",
    re.IGNORECASE,
)

NUMBERED_MODULE_RE = re.compile(
    r"^\s*(?:\d+[.)]\s+)(.+?)\s*$",
    re.MULTILINE,
)

MODULE_TYPE_HINTS: list[tuple[str, str]] = [
    (r"glauco|окт|глауком", "medical_ai / decision_support"),
    (r"copilot|транскриб|диаризац|медкарт", "ai_copilot / speech_ai"),
    (r"vitacalc|питани|нутрит|диет|menu", "recommendation_engine"),
    (r"rag|баз[аы]\s+знан", "knowledge_system"),
]


def parse_modules(text: str) -> list[LandingModule]:
    """Extract named modules from numbered lists in essence text."""
    if not text.strip():
        return []

    modules: list[LandingModule] = []
    if not MODULE_INTRO_RE.search(text) and not NUMBERED_MODULE_RE.search(text):
        return modules

    matches = list(NUMBERED_MODULE_RE.finditer(text))
    if not matches:
        return modules

    for i, match in enumerate(matches):
        name = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        description = text[start:end].strip()
        description = re.sub(r"^\s*\n+", "", description)
        description = description.split("\n\n")[0].strip() if description else ""
        modules.append(
            LandingModule(
                name=name,
                description=description,
                type=_infer_module_type(name, description),
            )
        )

    return modules


def _infer_module_type(name: str, description: str) -> str:
    combined = f"{name} {description}".lower()
    for pattern, mod_type in MODULE_TYPE_HINTS:
        if re.search(pattern, combined, re.IGNORECASE):
            return mod_type
    return "system"
