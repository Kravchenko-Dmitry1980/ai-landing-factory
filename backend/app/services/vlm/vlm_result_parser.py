"""Parse structured JSON responses from VLM backends."""

from __future__ import annotations

import json
import re
from typing import Any

ALLOWED_FIELD_KEYS = frozenset(
    {
        "team",
        "tech_stack",
        "modules",
        "goals",
        "metrics",
        "architecture",
        "results",
        "roadmap",
        "ui_features",
    }
)

ALLOWED_TOP_KEYS = frozenset({"field_candidates", "confidence", "warnings"})

FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


def parse_vlm_json_response(raw: str) -> dict[str, Any]:
    """Parse VLM JSON; tolerate fences and trailing text with warnings."""
    warnings: list[str] = []
    errors: list[str] = []
    text = (raw or "").strip()
    if not text:
        return {
            "field_candidates": {},
            "confidence": 0.0,
            "warnings": ["Empty VLM response"],
            "errors": ["empty_response"],
        }

    json_text, fence_warning = _extract_json_text(text)
    if fence_warning:
        warnings.append(fence_warning)

    parsed: Any = None
    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError:
        start = json_text.find("{")
        end = json_text.rfind("}")
        if start >= 0 and end > start:
            try:
                parsed = json.loads(json_text[start : end + 1])
                warnings.append("Parsed JSON from embedded object in response text")
            except json.JSONDecodeError as exc:
                errors.append(f"invalid_json: {exc}")
        else:
            errors.append("invalid_json: no JSON object found")

    if not isinstance(parsed, dict):
        return {
            "field_candidates": {},
            "confidence": 0.0,
            "warnings": warnings + ["Response is not a JSON object"],
            "errors": errors or ["not_object"],
        }

    if text != json_text and not fence_warning:
        warnings.append("Leading/trailing non-JSON text stripped from response")

    field_candidates_raw = parsed.get("field_candidates")
    if not isinstance(field_candidates_raw, dict):
        field_candidates_raw = {
            k: v for k, v in parsed.items() if k in ALLOWED_FIELD_KEYS
        }
        if field_candidates_raw:
            warnings.append("field_candidates inferred from top-level keys")

    field_candidates: dict[str, list] = {}
    for key, value in (field_candidates_raw or {}).items():
        if key not in ALLOWED_FIELD_KEYS:
            warnings.append(f"Dropped unknown field key: {key}")
            continue
        if value is None:
            field_candidates[key] = []
        elif isinstance(value, list):
            field_candidates[key] = value
        elif isinstance(value, str) and value.strip():
            field_candidates[key] = [value.strip()]
        else:
            warnings.append(f"Ignored non-list field value for {key}")

    confidence = parsed.get("confidence", 0.0)
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        warnings.append("Invalid confidence value")
        confidence = 0.0

    resp_warnings = parsed.get("warnings") or []
    if isinstance(resp_warnings, list):
        warnings.extend(str(w) for w in resp_warnings if w)
    elif resp_warnings:
        warnings.append(str(resp_warnings))

    for key in list(parsed.keys()):
        if key not in ALLOWED_TOP_KEYS and key not in ALLOWED_FIELD_KEYS:
            warnings.append(f"Dropped unknown top-level key: {key}")

    return {
        "field_candidates": field_candidates,
        "confidence": max(0.0, min(1.0, confidence)),
        "warnings": list(dict.fromkeys(warnings)),
        "errors": errors,
    }


def _extract_json_text(text: str) -> tuple[str, str | None]:
    match = FENCE_RE.search(text)
    if match:
        return match.group(1).strip(), "Stripped markdown code fence from response"
    return text, None
