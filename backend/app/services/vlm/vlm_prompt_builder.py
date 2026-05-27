"""VLM prompt contract — structured JSON-only extraction instructions."""

from __future__ import annotations

from app.schemas.vlm import VlmTaskType
from app.services.vlm.vlm_contracts import VlmExtractionContext

JSON_SCHEMA_BLOCK = """{
  "field_candidates": {
    "team": [],
    "tech_stack": [],
    "modules": [],
    "goals": [],
    "metrics": [],
    "architecture": [],
    "results": [],
    "roadmap": [],
    "ui_features": []
  },
  "confidence": 0.0,
  "warnings": []
}"""


def build_vlm_prompt(
    task_type: VlmTaskType,
    context: VlmExtractionContext,
) -> str:
    """Build deterministic prompt contract for future VLM backends."""
    text_hint = _combined_context_text(context)
    return (
        "Task:\n"
        "Extract factual information from this slide image for a landing page contract.\n\n"
        f"Task type: {task_type.value}\n"
        f"Source: {context.filename}"
        + (f" slide/page {context.page_or_slide}" if context.page_or_slide else "")
        + "\n"
        f"Visual content type: {context.visual_content_type}\n"
        f"Target fields: {', '.join(context.target_fields) or 'general'}\n"
        + (f"Text layer preview:\n{text_hint[:1200]}\n" if text_hint else "")
        + "\nReturn JSON only:\n"
        + JSON_SCHEMA_BLOCK
        + "\n\nRules:\n"
        "- Do not invent names.\n"
        "- Do not infer hidden text.\n"
        "- Use only visible evidence.\n"
        "- If uncertain, put item into warnings.\n"
        "- For people names, include raw visible text and confidence.\n"
        "- For diagrams, extract components and relationships.\n"
        "- Respond with valid JSON only, no markdown unless fenced.\n"
    )


def _combined_context_text(context: VlmExtractionContext) -> str:
    parts = [
        context.text_layer_preview or "",
        context.ocr_text_preview or "",
    ]
    return "\n".join(p.strip() for p in parts if p.strip())


def prompt_requires_json_only(prompt: str) -> bool:
    return "Return JSON only" in prompt or "JSON only" in prompt


def prompt_forbids_invention(prompt: str) -> bool:
    low = prompt.lower()
    return "do not invent" in low and "visible evidence" in low
