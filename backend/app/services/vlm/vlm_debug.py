"""Debug formatting for VLM candidate routing."""

from __future__ import annotations

import json

from app.schemas.vlm import VlmCandidateSelection, VlmExtractionReport, VlmStructuredExtraction


def format_candidate_table(
    selections: list[VlmCandidateSelection],
    *,
    slide_filter: set[int] | None = None,
) -> str:
    header = "slide | visual_type | route | vlm_task | selected | skipped_reason"
    rows = [header, "-" * len(header)]
    for sel in selections:
        if slide_filter and sel.page_or_slide not in slide_filter:
            continue
        slide = sel.page_or_slide if sel.page_or_slide is not None else "-"
        selected = "yes" if sel.selected else "no"
        rows.append(
            f"{slide} | {sel.visual_content_type} | {sel.route_action} | "
            f"{sel.task_type} | {selected} | {sel.skipped_reason or '-'}"
        )
    return "\n".join(rows)


def format_stub_extractions(extractions: list[VlmStructuredExtraction]) -> str:
    lines: list[str] = ["=== stub extractions ==="]
    for ext in extractions:
        lines.append(
            f"{ext.source_location} task={ext.task_type} "
            f"fields={len(ext.field_candidates)} conf={ext.confidence:.2f}"
        )
        for cand in ext.field_candidates:
            lines.append(f"  - {cand.field_name}: {cand.value}")
        for warning in ext.warnings:
            lines.append(f"  warning: {warning}")
    return "\n".join(lines)


def format_report_json(report: VlmExtractionReport) -> str:
    return json.dumps(report.model_dump(), ensure_ascii=False, indent=2)
