"""Fuzzy name matching against trusted roster."""

from __future__ import annotations

from difflib import SequenceMatcher

from app.services.team_verification.name_quality import normalize_cyrillic_name

STRONG_MATCH_THRESHOLD = 0.88
WEAK_MATCH_THRESHOLD = 0.75


def name_similarity(a: str, b: str) -> float:
    """Deterministic fuzzy similarity between two names."""
    na = normalize_cyrillic_name(a)
    nb = normalize_cyrillic_name(b)
    if na == nb:
        return 1.0
    return SequenceMatcher(None, na, nb).ratio()


def find_best_match(
    candidate: str,
    trusted_names: list[str],
) -> tuple[str | None, float]:
    """Return (best_trusted_name, score) or (None, 0.0)."""
    if not trusted_names:
        return None, 0.0

    best_name: str | None = None
    best_score = 0.0
    for trusted in trusted_names:
        score = name_similarity(candidate, trusted)
        if score > best_score:
            best_score = score
            best_name = trusted
    return best_name, best_score


def classify_match_score(score: float) -> str:
    """Return match tier label."""
    if score >= 1.0:
        return "exact"
    if score >= STRONG_MATCH_THRESHOLD:
        return "strong_fuzzy"
    if score >= WEAK_MATCH_THRESHOLD:
        return "weak_fuzzy"
    return "no_match"
