"""Team slide / text markers for PPTX extraction diagnostics."""

from __future__ import annotations

import re

TEAM_SLIDE_TITLE_MARKERS: tuple[str, ...] = (
    "команда проекта",
    "участники команды",
    "команда управления",
    "роли в проекте",
    "состав команды",
)

TEAM_TEXT_MARKERS: tuple[str, ...] = (
    "команда проекта",
    "участники команды",
    "команда управления",
    "роли в проекте",
    "тимлид:",
    "тимлид ",
    "помощник тимлида",
    "участники:",
    "разработчик:",
    "разработчики",
)

TEAM_LINE_MARKERS: tuple[str, ...] = (
    "тимлид",
    "помощник тимлида",
    "участник",
    "разработчик",
    "аналитик",
)

# Substrings that mention "команда" but are NOT project team sections.
TEAM_FALSE_CONTEXT: tuple[str, ...] = (
    "команды заказчика",
    "команда заказчика",
    "команда проекта достигла",
)


def _normalize(blob: str) -> str:
    return blob.lower().replace("\u00a0", " ")


def is_false_team_context(text: str) -> bool:
    low = _normalize(text)
    return any(marker in low for marker in TEAM_FALSE_CONTEXT)


def slide_title_has_team_marker(title: str | None, body: str = "") -> bool:
    blob = _normalize(f"{title or ''}\n{body[:200]}")
    if is_false_team_context(blob):
        return False
    return any(marker in blob for marker in TEAM_SLIDE_TITLE_MARKERS)


def text_has_team_markers(text: str) -> bool:
    low = _normalize(text)
    if is_false_team_context(low):
        return False
    return any(marker in low for marker in TEAM_TEXT_MARKERS)


def matched_team_markers(text: str) -> list[str]:
    low = _normalize(text)
    if is_false_team_context(low):
        return []
    return [m for m in TEAM_TEXT_MARKERS if m in low]


def is_team_slide_title(line: str) -> bool:
    low = _normalize(line)
    if is_false_team_context(low):
        return False
    return any(marker in low for marker in TEAM_SLIDE_TITLE_MARKERS)


SLIDE_SPLIT_RE = re.compile(r"(?:^|\n)(Slide\s+\d+\s*:)", re.IGNORECASE)


def iter_pptx_slides(text: str) -> list[tuple[int, str, str | None]]:
    """Return (index, full_slide_text, title_guess) from extracted PPTX text."""
    parts = SLIDE_SPLIT_RE.split(text)
    slides: list[tuple[int, str, str | None]] = []
    i = 1
    while i < len(parts):
        header = parts[i].strip()
        body = parts[i + 1] if i + 1 < len(parts) else ""
        match = re.search(r"(\d+)", header)
        idx = int(match.group(1)) if match else len(slides) + 1
        full = f"{header}\n{body}".strip()
        title = _guess_slide_title(full)
        slides.append((idx, full, title))
        i += 2
    if not slides and text.strip():
        slides.append((1, text.strip(), _guess_slide_title(text)))
    return slides


def _guess_slide_title(slide_text: str) -> str | None:
    lines = [ln.strip() for ln in slide_text.splitlines() if ln.strip()]
    if lines and re.match(r"Slide\s+\d+", lines[0], re.IGNORECASE):
        lines = lines[1:]
    for line in lines:
        if line.lower() in ("проект:", "проект"):
            continue
        if len(line) > 4 and not line.lower().startswith("сроки"):
            return line[:120]
    return lines[0][:120] if lines else None
