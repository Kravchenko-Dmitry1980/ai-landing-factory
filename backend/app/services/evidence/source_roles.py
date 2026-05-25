"""Source role constants and inference for multi-source assembly."""

from __future__ import annotations

import re

from app.schemas.evidence import SourceInventoryItem
from app.schemas.extraction import ExtractionResult, FileExtraction
from app.services.contract_fidelity.structured_landing_parser import StructuredLandingParser

SOURCE_ROLES = (
    "primary_project_doc",
    "supporting_presentation",
    "module_presentation",
    "technical_spec",
    "report",
    "team_source",
    "supporting_visual_evidence",
    "unknown",
)

PRIMARY_DOC_THRESHOLD = 0.65
SLIDE_RE = re.compile(r"(?:^|\n)\s*Slide\s+\d+\s*:", re.IGNORECASE)


def infer_source_roles(
    items: list[SourceInventoryItem],
    extraction: ExtractionResult,
) -> list[SourceInventoryItem]:
    """Assign source_role to each inventory item after type classification."""
    if not items:
        return items

    file_map = {f.filename: f for f in extraction.files}
    primary = _select_primary_doc(items)

    primary_modules: list[str] = []
    if primary:
        text = (file_map.get(primary.filename).extracted_text or "") if primary.filename in file_map else ""
        if text.strip():
            parsed = StructuredLandingParser().parse(text)
            primary_modules = [m.name for m in parsed.modules]

    updated: list[SourceInventoryItem] = []
    for item in items:
        role = _infer_role(item, primary, primary_modules, file_map.get(item.filename))
        updated.append(item.model_copy(update={"source_role": role}))
    return updated


def _select_primary_doc(items: list[SourceInventoryItem]) -> SourceInventoryItem | None:
    ready = [
        s for s in items
        if s.detected_source_type == "ready_landing_doc"
        and s.confidence >= PRIMARY_DOC_THRESHOLD
    ]
    if not ready:
        return None
    return max(ready, key=lambda s: (s.confidence, s.char_count))


def _infer_role(
    item: SourceInventoryItem,
    primary: SourceInventoryItem | None,
    primary_modules: list[str],
    file_rec: FileExtraction | None,
) -> str:
    if primary and item.source_id == primary.source_id:
        return "primary_project_doc"

    text = (file_rec.extracted_text or "") if file_rec else ""

    if file_rec and (
        file_rec.file_type == "ocr"
        or file_rec.metadata.get("source_role") == "supporting_visual_evidence"
    ):
        return "supporting_visual_evidence"
    if item.source_role == "supporting_visual_evidence":
        return "supporting_visual_evidence"

    if item.detected_source_type == "technical_spec":
        return "technical_spec"
    if item.detected_source_type == "report":
        return "report"
    if item.detected_source_type == "team_list":
        return "team_source"

    is_presentation = (
        item.file_type == "pptx"
        or item.detected_source_type == "pptx_project_presentation"
    )
    if is_presentation and _is_module_presentation(item, text, primary_modules):
        return "module_presentation"
    if is_presentation:
        return "supporting_presentation"

    if item.detected_source_type == "ready_landing_doc":
        return "primary_project_doc"

    return "unknown"


def _is_module_presentation(
    item: SourceInventoryItem,
    text: str,
    primary_modules: list[str],
) -> bool:
    if not primary_modules:
        return False

    filename_lower = item.filename.lower()
    slide_title = _first_slide_title(text)
    haystack = f"{filename_lower} {slide_title}".lower()

    for module_name in primary_modules:
        tokens = _module_match_tokens(module_name)
        if any(token in haystack for token in tokens):
            return True
        if slide_title and _names_overlap(module_name, slide_title):
            return True
    return False


def _module_match_tokens(module_name: str) -> list[str]:
    name = module_name.lower().strip()
    tokens = {name}
    if "copilot" in name:
        tokens.add("copilot")
    if "glauco" in name:
        tokens.add("glauco")
    if "vitacalc" in name:
        tokens.add("vitacalc")
    first = name.split()[0]
    if len(first) >= 4:
        tokens.add(first)
    return [t for t in tokens if len(t) >= 4]


def _first_slide_title(text: str) -> str:
    if not text.strip():
        return ""
    parts = SLIDE_RE.split(text)
    if len(parts) >= 3:
        body = parts[2]
    else:
        body = text
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    if lines and re.match(r"Slide\s+\d+", lines[0], re.IGNORECASE):
        lines = lines[1:]
    for line in lines:
        low = line.lower()
        if low in ("проект:", "проект") or low.startswith("сроки"):
            continue
        if len(line) > 5:
            return line[:120]
    return lines[0][:120] if lines else ""


def _names_overlap(module_name: str, candidate: str) -> bool:
    mod = module_name.lower()
    cand = candidate.lower()
    if mod in cand or cand in mod:
        return True
    mod_tokens = _module_match_tokens(module_name)
    return any(token in cand for token in mod_tokens)
