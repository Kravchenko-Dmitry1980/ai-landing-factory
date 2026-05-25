"""Deterministic tagline fallbacks for HTML export."""

from __future__ import annotations

MEDICAL_TAGLINE = (
    "AI-экосистема для клинической аналитики, поддержки врача "
    "и автоматизации медицинских данных"
)
EDUCATION_TAGLINE = (
    "AI-платформа персонализированного обучения и аналитики прогресса"
)
ANALYTICS_TAGLINE = (
    "Интеллектуальная система анализа данных и поддержки принятия решений"
)
GENERIC_TAGLINE = (
    "Интеллектуальная система для анализа, структурирования "
    "и представления проектных данных"
)


def resolve_tagline(
    title: str | None,
    tagline: str | None,
    essence: str | None = None,
    domain: str | None = None,
) -> str:
    """
    Return a tagline that does not duplicate the project title.
    Deterministic fallbacks only — no LLM.
    """
    title_norm = (title or "").strip()
    tagline_norm = (tagline or "").strip()
    domain_norm = (domain or "").strip().lower()
    essence_norm = (essence or "").strip().lower()

    if tagline_norm and title_norm and tagline_norm.casefold() != title_norm.casefold():
        return tagline_norm

    title_lower = title_norm.casefold()
    if "эндокринолог" in title_lower:
        return MEDICAL_TAGLINE

    if domain_norm in ("medical_ai", "medical"):
        return MEDICAL_TAGLINE
    if "medical" in domain_norm or "клинич" in essence_norm or "врач" in essence_norm:
        return MEDICAL_TAGLINE

    if domain_norm in ("education_ai", "education"):
        return EDUCATION_TAGLINE
    if "education" in domain_norm or "обучен" in essence_norm:
        return EDUCATION_TAGLINE

    if domain_norm == "analytics" or "analytics" in domain_norm:
        return ANALYTICS_TAGLINE

    return GENERIC_TAGLINE
