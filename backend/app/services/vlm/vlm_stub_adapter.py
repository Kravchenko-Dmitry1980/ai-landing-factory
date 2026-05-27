"""Deterministic stub VLM adapter — no hallucination, context-only extraction."""

from __future__ import annotations

import re
import time

from app.config import settings
from app.schemas.vlm import VlmFieldCandidate, VlmStructuredExtraction, VlmTaskType
from app.services.vlm.vlm_contracts import KNOWN_TECH_MARKERS, VlmExtractionContext
from app.services.vlm.vlm_prompt_builder import build_vlm_prompt


class StubVlmAdapter:
    """Fake VLM for contract tests — never invents people or unseen facts."""

    provider = "stub"

    def is_available(self) -> bool:
        return settings.vlm_provider == "stub"

    def extract(
        self,
        image_bytes: bytes,
        task_type: VlmTaskType,
        context: VlmExtractionContext,
    ) -> VlmStructuredExtraction:
        started = time.perf_counter()
        blob = _context_blob(context)
        warnings: list[str] = []
        errors: list[str] = []
        candidates: list[VlmFieldCandidate] = []

        if not image_bytes:
            warnings.append("Stub VLM received empty image bytes; using context text only")

        if task_type == VlmTaskType.extract_team:
            warnings.append("Stub VLM does not infer people from image.")
            candidates = []
        elif task_type == VlmTaskType.extract_tech_stack:
            tech = _extract_known_tech(blob)
            if tech:
                candidates.append(
                    VlmFieldCandidate(
                        field_name="tech_stack",
                        value=tech,
                        confidence=0.72,
                        source_slide=context.page_or_slide,
                        evidence_text=", ".join(tech),
                        reason="stub_echo_from_context",
                    )
                )
            else:
                warnings.append("Stub VLM: no tech markers in context")
        elif task_type == VlmTaskType.extract_architecture:
            arch = _extract_architecture_from_context(blob)
            if arch:
                candidates.append(
                    VlmFieldCandidate(
                        field_name="modules",
                        value=arch,
                        confidence=0.68,
                        source_slide=context.page_or_slide,
                        evidence_text=arch if isinstance(arch, str) else str(arch),
                        reason="stub_architecture_from_context",
                    )
                )
            else:
                warnings.append("Stub VLM: no architecture cues in context")
        elif task_type == VlmTaskType.extract_goals:
            goals = _extract_lines_matching(blob, ("цель", "задач", "проблем"))
            if goals:
                candidates.append(
                    VlmFieldCandidate(
                        field_name="tasks",
                        value=goals[:5],
                        confidence=0.65,
                        source_slide=context.page_or_slide,
                        reason="stub_goals_from_context",
                    )
                )
        elif task_type == VlmTaskType.extract_metrics:
            metrics = _extract_lines_matching(blob, ("метрик", "accuracy", "uptime", "%"))
            if metrics:
                candidates.append(
                    VlmFieldCandidate(
                        field_name="results",
                        value=metrics[:5],
                        confidence=0.64,
                        source_slide=context.page_or_slide,
                        reason="stub_metrics_from_context",
                    )
                )
        elif task_type == VlmTaskType.extract_roadmap:
            roadmap = _extract_lines_matching(blob, ("развит", "roadmap", "перспектив", "план"))
            if roadmap:
                candidates.append(
                    VlmFieldCandidate(
                        field_name="outlook",
                        value=roadmap[:5],
                        confidence=0.63,
                        source_slide=context.page_or_slide,
                        reason="stub_roadmap_from_context",
                    )
                )
        elif task_type == VlmTaskType.extract_ui_features:
            ui = _extract_lines_matching(blob, ("интерфейс", "dashboard", "streamlit", "экран"))
            if ui:
                candidates.append(
                    VlmFieldCandidate(
                        field_name="outputs",
                        value=ui[:5],
                        confidence=0.62,
                        source_slide=context.page_or_slide,
                        reason="stub_ui_from_context",
                    )
                )
        elif task_type == VlmTaskType.extract_table:
            warnings.append("Stub VLM: table extraction deferred to future provider")
        else:
            if blob.strip():
                candidates.append(
                    VlmFieldCandidate(
                        field_name="essence",
                        value=[blob[:240].strip()],
                        confidence=0.5,
                        source_slide=context.page_or_slide,
                        reason="stub_general_summary_from_context",
                    )
                )

        prompt = build_vlm_prompt(task_type, context)
        runtime_ms = int((time.perf_counter() - started) * 1000)
        confidence = max((c.confidence for c in candidates), default=0.0)

        return VlmStructuredExtraction(
            provider=self.provider,
            model_name=settings.vlm_model_name or "stub-v1",
            source_filename=context.filename,
            source_location=_source_location(context),
            visual_content_type=context.visual_content_type,
            task_type=task_type.value,
            field_candidates=candidates,
            raw_response=prompt if settings.vlm_store_raw_response else None,
            normalized_response={
                "field_candidates": {c.field_name: c.value for c in candidates},
                "confidence": confidence,
                "warnings": warnings,
            },
            confidence=confidence,
            runtime_ms=runtime_ms,
            warnings=warnings,
            errors=errors,
        )


def _context_blob(context: VlmExtractionContext) -> str:
    parts = [context.text_layer_preview or "", context.ocr_text_preview or ""]
    return "\n".join(p for p in parts if p.strip())


def _extract_known_tech(blob: str) -> list[str]:
    low = blob.lower()
    found: list[str] = []
    for marker in KNOWN_TECH_MARKERS:
        if marker in low:
            label = marker.upper() if marker.islower() and len(marker) <= 6 else marker.title()
            if marker == "qdrant":
                label = "Qdrant"
            elif marker == "neo4j":
                label = "Neo4j"
            elif marker == "bertopic":
                label = "BERTopic"
            elif marker == "fastapi":
                label = "FastAPI"
            elif marker == "postgresql":
                label = "PostgreSQL"
            elif marker == "yolov":
                label = "YOLOv8"
            if label not in found:
                found.append(label)
    return found


def _extract_architecture_from_context(blob: str) -> str | None:
    low = blob.lower()
    components = _extract_known_tech(blob)
    if "->" in blob or "→" in blob:
        chain = re.sub(r"\s+", " ", blob.strip())[:300]
        return chain
    if any(k in low for k in ("архитектур", "pipeline", "пайплайн", "поток", "flow")):
        if components:
            return " -> ".join(components)
        lines = [ln.strip() for ln in blob.splitlines() if ln.strip()]
        return lines[0][:240] if lines else None
    return None


def _extract_lines_matching(blob: str, keywords: tuple[str, ...]) -> list[str]:
    results: list[str] = []
    for line in blob.splitlines():
        low = line.lower()
        if any(k in low for k in keywords) and line.strip():
            results.append(line.strip()[:200])
    return results


def _source_location(context: VlmExtractionContext) -> str:
    if context.page_or_slide is not None:
        return f"slide-{context.page_or_slide}"
    return context.filename
