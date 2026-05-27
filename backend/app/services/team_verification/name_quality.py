"""Name quality scoring for OCR team candidates."""

from __future__ import annotations

import re

LATIN_RE = re.compile(r"[A-Za-z]")
DIGIT_RE = re.compile(r"\d")
RUSSIAN_NAME_RE = re.compile(
    r"^[А-ЯЁ][а-яё-]+(?:\s+[А-ЯЁ][а-яё-]+){1,2}$"
)
SUSPICIOUS_ENDINGS = frozenset(
    {
        "ец",
        "св",
        "ый",
        "ая",
        "енда",
        "аный",
        "юков",
    }
)
OCR_ARTIFACT_CHARS = frozenset("Il1O0|")


def normalize_cyrillic_name(name: str) -> str:
    """Normalize name for matching: lowercase, ё→е, collapse spaces."""
    text = name.strip().lower().replace("ё", "е")
    return re.sub(r"\s+", " ", text)


def score_name_quality(raw_name: str) -> tuple[float, list[str]]:
    """Return (score 0..1, warnings)."""
    warnings: list[str] = []
    name = raw_name.strip()
    if not name:
        return 0.0, ["empty_name"]

    score = 1.0

    if len(name) < 5:
        score -= 0.4
        warnings.append("too_short")
    if len(name) > 80:
        score -= 0.3
        warnings.append("too_long")

    if DIGIT_RE.search(name):
        score -= 0.5
        warnings.append("contains_digits")

    latin = len(LATIN_RE.findall(name))
    cyrillic = len(re.findall(r"[А-Яа-яЁё]", name))
    if latin > 0 and cyrillic > 0:
        ratio = latin / max(latin + cyrillic, 1)
        if ratio > 0.15:
            score -= 0.5
            warnings.append("mixed_latin_cyrillic")

    if not RUSSIAN_NAME_RE.match(name):
        score -= 0.25
        warnings.append("invalid_russian_name_pattern")

    parts = name.split()
    if len(parts) < 2:
        score -= 0.2
        warnings.append("single_token_name")

    for part in parts:
        lower = part.lower()
        for ending in SUSPICIOUS_ENDINGS:
            if lower.endswith(ending) and len(part) > 4:
                # Only flag if not a common valid surname pattern
                if ending in ("ец", "св", "енда", "аный"):
                    score -= 0.15
                    warnings.append(f"suspicious_ending:{ending}")
                    break

    artifact_count = sum(1 for ch in name if ch in OCR_ARTIFACT_CHARS)
    if artifact_count >= 2:
        score -= 0.3
        warnings.append("ocr_artifact_chars")

    if name.isupper() and len(name) > 10:
        score -= 0.1
        warnings.append("all_uppercase_noise")

    return max(0.0, min(1.0, score)), warnings


def score_role_quality(role: str | None, contributions: list[str]) -> float:
    """Score role/contributions quality 0..1."""
    if role and role.strip():
        return 0.9
    if contributions:
        return 0.7
    return 0.0
