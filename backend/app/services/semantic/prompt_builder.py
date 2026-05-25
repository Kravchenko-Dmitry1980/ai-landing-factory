"""PII-safe contract payload for cloud semantic generation."""

from app.schemas.landing_contract import LandingContract
from app.services.pii.detector import PIIDetector


def _redact_text(text: str, detector: PIIDetector, filename: str = "contract") -> str:
    if not text.strip():
        return text
    entities, _ = detector.detect_text(text, filename)
    if not entities:
        return text
    out = text
    for ent in sorted(entities, key=lambda e: len(e.original), reverse=True):
        if ent.original and ent.placeholder:
            out = out.replace(ent.original, ent.placeholder)
    return out


def build_safe_contract_payload(
    contract: LandingContract,
    detector: PIIDetector | None = None,
) -> dict:
    """
    Safe intermediate representation — ONLY contract fields, redacted.
    No raw files, no extraction text.
    """
    det = detector
    if det is None:
        from app.config import settings
        det = PIIDetector(settings)

    blocks = []
    for b in contract.blocks:
        content = _redact_text(b.content, det, f"block_{b.key}")
        bullets = [_redact_text(x, det, f"block_{b.key}") for x in b.bullets]
        blocks.append({"key": b.key, "title": b.title, "content": content, "bullets": bullets})

    enrichment = None
    if contract.enrichment:
        enrichment = {
            "missing_fields": contract.enrichment.missing_fields,
            "assumptions": contract.enrichment.assumptions,
            "source_trace": [
                {"field": t.field, "filename": t.filename, "evidence": t.evidence[:200]}
                for t in contract.enrichment.source_trace[:15]
            ],
        }

    return {
        "title": _redact_text(contract.title or "", det, "title"),
        "client": _redact_text(contract.client or "", det, "client"),
        "timeline": contract.timeline or "",
        "lead": _redact_text(contract.lead or "", det, "lead"),
        "quote": _redact_text(contract.quote or "", det, "quote"),
        "goals": [_redact_text(g, det, "goals") for g in contract.goals],
        "blocks": blocks,
        "enrichment": enrichment,
    }


def build_semantic_prompts(
    safe_payload: dict,
    domain: str,
    section_plan: list[str],
    narrative_summary: str,
    templates_dir,
) -> tuple[str, str]:
    import json
    from pathlib import Path

    base = Path(templates_dir)
    system = (base / "semantic_generation_system.txt").read_text(encoding="utf-8")
    user_tpl = (base / "semantic_generation_user.txt").read_text(encoding="utf-8")
    user = user_tpl.format(
        domain=domain,
        section_plan=", ".join(section_plan),
        narrative_summary=narrative_summary[:2000],
        contract_json=json.dumps(safe_payload, ensure_ascii=False, indent=2)[:12000],
    )
    return system, user
