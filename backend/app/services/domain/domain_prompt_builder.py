"""Build optional LLM prompts for domain refinement (PII-safe contract only)."""

from pathlib import Path

from app.schemas.domain_intelligence import DomainProfile


def build_domain_refinement_prompts(
    safe_payload: dict,
    current_profile: DomainProfile,
    templates_dir: Path | None = None,
) -> tuple[str, str]:
    system = (
        "You refine domain classification for an AI project landing. "
        "Return JSON: {primary_domain, secondary_domains[], confidence, evidence[]}. "
        "Use only evidence from the payload. Do not invent technologies or people."
    )
    user = (
        f"Current classification: {current_profile.primary_domain.value} "
        f"(confidence {current_profile.confidence:.2f}).\n"
        f"Payload:\n{safe_payload}"
    )
    return system, user
