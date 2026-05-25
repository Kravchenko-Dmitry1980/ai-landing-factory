"""Normalize evidence text for matching and assembly."""

from __future__ import annotations

import re

_WS_RE = re.compile(r"[ \t]+")
_BLANK_RE = re.compile(r"\n{3,}")


def normalize_text(text: str) -> str:
    text = text.replace("\u00a0", " ").replace("\u000b", "\n").replace("\r\n", "\n")
    text = _BLANK_RE.sub("\n\n", text)
    lines = [_WS_RE.sub(" ", ln).strip() for ln in text.splitlines()]
    return "\n".join(lines).strip()


def extract_dates(text: str) -> list[str]:
    patterns = [
        r"\d{2}\.\d{2}\.\d{2,4}\s*[-–—]\s*\d{2}\.\d{2}\.\d{2,4}",
        r"\d{2}\.\d{2}\s*[-–—]\s*\d{2}\.\d{2}\.\d{4}",
        r"\(\d{2}\.\d{2}[-–—]\d{2}\.\d{2}\.\d{4}\)",
        r"Сроки проекта:\s*([^\n]+)",
    ]
    found: list[str] = []
    for pat in patterns:
        for match in re.finditer(pat, text, re.IGNORECASE):
            val = match.group(0) if match.lastindex is None else match.group(1)
            val = val.strip()
            if val and val not in found:
                found.append(val)
    return found


def extract_keywords(text: str, limit: int = 12) -> list[str]:
    words = re.findall(r"[а-яёa-z]{5,}", text.lower())
    freq: dict[str, int] = {}
    stop = {
        "который", "которые", "проект", "слайд", "slide", "данных",
        "система", "модель", "можно", "будет", "этого",
    }
    for w in words:
        if w in stop:
            continue
        freq[w] = freq.get(w, 0) + 1
    ranked = sorted(freq, key=freq.get, reverse=True)
    return ranked[:limit]
