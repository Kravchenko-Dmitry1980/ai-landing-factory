"""Bullet text normalization for HTML export."""

from __future__ import annotations

import re

BULLET_PREFIX_RE = re.compile(r"^[●•·▸▪◦\-\*–—]\s*")

MAX_TEAM_CONTRIBUTION_BULLETS = 4
MAX_TEAM_BULLET_CHARS = 240

_BAD_ENDING_WORDS = frozenset(
    {
        "с",
        "в",
        "на",
        "для",
        "по",
        "из",
        "к",
        "и",
        "через",
        "между",
        "над",
        "под",
        "при",
        "от",
        "до",
        "а",
        "но",
        "или",
        "у",
        "о",
        "об",
    }
)


def normalize_bullet(text: str) -> str:
    """Strip leading bullet symbols to avoid duplicate markers in HTML."""
    return normalize_bullet_text(text)


def normalize_bullet_text(text: str) -> str:
    """Strip leading bullet symbols to avoid duplicate markers in HTML."""
    cleaned = text.strip()
    while True:
        next_text = BULLET_PREFIX_RE.sub("", cleaned, count=1).strip()
        if next_text == cleaned:
            break
        cleaned = next_text
    return cleaned


def truncate_at_word(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    cut = text[:max_len].rsplit(" ", 1)[0]
    return cut if cut else text[:max_len]


def _last_word(text: str) -> str:
    stripped = text.rstrip("…").rstrip(".;,!")
    parts = stripped.split()
    return parts[-1].casefold() if parts else ""


def _ends_on_bad_word(text: str) -> bool:
    return _last_word(text) in _BAD_ENDING_WORDS


def truncate_sentence_safe(text: str, max_chars: int = MAX_TEAM_BULLET_CHARS) -> str:
    """
    Truncate contribution text without cutting mid-word or on prepositions/conjunctions.
    """
    cleaned = normalize_bullet_text(text)
    if not cleaned:
        return cleaned
    if len(cleaned) <= max_chars:
        return cleaned

    segment = cleaned[:max_chars]
    candidates: list[str] = []

    for sep in (".", ";", ","):
        idx = segment.rfind(sep)
        if idx >= int(max_chars * 0.35):
            candidate = segment[:idx].strip()
            if candidate:
                candidates.append(candidate)

    space_cut = segment.rsplit(" ", 1)[0].strip() if " " in segment else segment.strip()
    if space_cut:
        candidates.append(space_cut)

    chosen = ""
    for candidate in candidates:
        if not _ends_on_bad_word(candidate):
            chosen = candidate
            break

    if not chosen:
        chosen = truncate_at_word(cleaned, max_chars).strip()
        while chosen and _ends_on_bad_word(chosen) and " " in chosen:
            chosen = chosen.rsplit(" ", 1)[0].strip()

    if not chosen:
        chosen = cleaned[:max_chars].rsplit(" ", 1)[0].strip() or cleaned[:max_chars].strip()

    if len(chosen) < len(cleaned):
        if not chosen.endswith("…"):
            chosen = f"{chosen.rstrip('.,;')}…"
    return chosen


def limit_bullets(
    bullets: list[str],
    max_visible: int = MAX_TEAM_CONTRIBUTION_BULLETS,
) -> tuple[list[str], int]:
    normalized = [normalize_bullet_text(item) for item in bullets]
    normalized = [item for item in normalized if item]
    shown = normalized[:max_visible]
    remaining = max(0, len(normalized) - len(shown))
    return shown, remaining


def format_more_count(count: int) -> str:
    n = abs(int(count))
    mod100 = n % 100
    mod10 = n % 10
    if 11 <= mod100 <= 14:
        word = "пунктов"
    elif mod10 == 1:
        word = "пункт"
    elif mod10 in (2, 3, 4):
        word = "пункта"
    else:
        word = "пунктов"
    return f"+ ещё {n} {word}"
