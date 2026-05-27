"""OCR team-section text normalization (safe fixes only, no name hallucination)."""

from __future__ import annotations

import re
from difflib import SequenceMatcher

TEAM_SECTION_MARKERS = (
    "команда проекта",
    "тимлид проекта",
    "участники команды проекта",
    "участники команды",
    "помощник тимлида",
    "участники",
    "разработчики",
    "команда",
    "тимлид",
)

# Literal glued-word repairs observed in Tesseract OCR output.
GLUED_REPAIRS: tuple[tuple[str, str], ...] = (
    (r"Тимлидпроекта", "Тимлид проекта"),
    (r"тимлидпроекта", "тимлид проекта"),
    (r"Тимлид\s*проекта\.", "Тимлид проекта"),
    (r"помошниктиылида", "помощник тимлида"),
    (r"помощниктилида", "помощник тимлида"),
    (r"помошник\s*тимлида", "помощник тимлида"),
    (r"помощник\s*тилида", "помощник тимлида"),
    (r"Участникикоманды", "Участники команды"),
    (r"участникикоманды", "участники команды"),
    (r"Командпроекта", "Команда проекта"),
    (r"командпроекта", "команда проекта"),
    (r"Командапроекта", "Команда проекта"),
    (r"командапроекта", "команда проекта"),
)

SYMBOL_CLEANUP_RE = re.compile(r"[|`©®™•●▪◦·]+")
QUOTE_NORMALIZE_RE = re.compile(r"[«»""„‟'']")
MULTISPACE_RE = re.compile(r"[ \t]{2,}")
BULLET_LINE_RE = re.compile(r"^\s*[-•●▪◦·]\s+", re.MULTILINE)

ROLE_CANONICAL = {
    "тимлид": "тимлид",
    "тимлид проекта": "тимлид проекта",
    "помощник тимлида": "помощник тимлида",
    "помошник тимлида": "помощник тимлида",
    "разработчик": "разработчик",
    "архитектор": "архитектор",
    "аналитик": "аналитик",
    "аналитика": "аналитика",
    "разработка": "разработка",
    "парсинг": "парсинг",
    "данные": "данные",
}


def detect_team_ocr_section(text: str) -> bool:
    """Return True when text contains team-section markers."""
    if not text or not text.strip():
        return False
    low = text.lower()
    return any(marker in low for marker in TEAM_SECTION_MARKERS)


def normalize_ocr_role(role: str) -> str:
    """Fuzzy-normalize OCR-distorted role words (not person names)."""
    cleaned = role.strip().rstrip(":;.")
    if not cleaned:
        return ""
    low = cleaned.lower()
    for canonical in sorted(ROLE_CANONICAL, key=len, reverse=True):
        if canonical in low or low in canonical:
            return ROLE_CANONICAL.get(canonical, canonical)
    best = cleaned
    best_score = 0.0
    for canonical in ROLE_CANONICAL:
        score = SequenceMatcher(None, low, canonical).ratio()
        if score > best_score:
            best_score = score
            best = canonical
    if best_score >= 0.72:
        return ROLE_CANONICAL.get(best, best)
    return cleaned


def normalize_ocr_team_text(text: str) -> str:
    """Apply safe OCR fixes for team sections without inventing names."""
    if not text:
        return ""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = SYMBOL_CLEANUP_RE.sub(" ", normalized)
    normalized = QUOTE_NORMALIZE_RE.sub('"', normalized)
    normalized = BULLET_LINE_RE.sub("- ", normalized)

    for pattern, replacement in GLUED_REPAIRS:
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)

    # Insert space between glued header words: "Участники команды проекта."
    normalized = re.sub(
        r"(Участники)\s*(команды)\s*(проекта)",
        r"\1 \2 \3",
        normalized,
        flags=re.IGNORECASE,
    )

    lines: list[str] = []
    for line in normalized.splitlines():
        stripped = MULTISPACE_RE.sub(" ", line.strip())
        if not stripped:
            continue
        role_match = re.match(r"^(.+?)\s*[—–-]\s*(.+)$", stripped)
        if role_match:
            name_part = role_match.group(1).strip()
            role_part = normalize_ocr_role(role_match.group(2).strip())
            stripped = f"{name_part} — {role_part}"
        lines.append(stripped)

    return "\n".join(lines).strip()
