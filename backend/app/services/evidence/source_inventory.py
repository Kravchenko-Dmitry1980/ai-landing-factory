"""Build source inventory from extraction files."""

from __future__ import annotations

import re
import uuid

from app.schemas.evidence import SourceInventoryItem
from app.schemas.extraction import ExtractionResult, FileExtraction
from app.services.evidence.source_roles import infer_source_roles

SOURCE_MARKERS: dict[str, list[str]] = {
    "ready_landing_doc": [
        "суть проекта", "задачи проекта", "для чего", "вводные данные",
        "выходные данные", "результаты проекта", "перспектива развития",
        "используемый технологический стек", "команда проекта",
    ],
    "pptx_project_presentation": [
        "цель проекта", "цели проекта", "этапы проекта", "этапы работы",
        "подготовка данных", "итоги проекта", "демо", "шаг 1", "шаг 2",
        "ссылки на первоисточники", "стажировка", "slide ",
        "метрики и результаты", "архитектура системы", "архитектура пайплайна",
    ],
    "technical_spec": [
        "техническое задание", "тз", "требования", "функциональные требования",
        "нефункциональные требования", "входные данные", "выходные данные",
        "api", "интеграция",
    ],
    "report": [
        "отчёт", "отчет", "итоги", "результаты", "проведено",
        "реализовано", "рекомендации", "метрики",
    ],
    "team_list": [
        "команда", "тимлид", "помощник тимлида", "участники",
    ],
    "architecture_doc": [
        "архитектура", "pipeline", "модули", "сервисы", "backend",
        "frontend", "data layer", "llm", "rag",
    ],
    "raw_notes": [],
}

SLIDE_RE = re.compile(r"(?:^|\n)\s*Slide\s+\d+\s*:", re.IGNORECASE)


class SourceInventoryBuilder:
    """Classify each uploaded file and produce inventory items."""

    def build(self, extraction: ExtractionResult) -> list[SourceInventoryItem]:
        items: list[SourceInventoryItem] = []
        for idx, file_rec in enumerate(extraction.files):
            text = (file_rec.extracted_text or "").strip()
            if not text and not file_rec.filename:
                continue
            source_id = f"src-{idx}-{uuid.uuid4().hex[:8]}"
            items.append(self._classify_file(source_id, file_rec, text))
        return infer_source_roles(items, extraction)

    def _classify_file(
        self,
        source_id: str,
        file_rec: FileExtraction,
        text: str,
    ) -> SourceInventoryItem:
        if file_rec.file_type == "ocr" or file_rec.metadata.get("is_ocr_derivative"):
            return SourceInventoryItem(
                source_id=source_id,
                filename=file_rec.filename,
                file_type="ocr",
                char_count=len(text),
                slide_count=_int_or_none(file_rec.metadata.get("page_or_slide")),
                detected_source_type="team_list" if "команда" in text.lower() else "mixed_project_materials",
                source_role=str(file_rec.metadata.get("source_role") or "supporting_visual_evidence"),
                confidence=0.55,
                markers=["ocr_derivative"],
                warnings=list(file_rec.warnings or []),
            )

        if file_rec.file_type == "vlm" or file_rec.metadata.get("is_vlm_derivative"):
            return SourceInventoryItem(
                source_id=source_id,
                filename=file_rec.filename,
                file_type="vlm",
                char_count=len(text),
                slide_count=_int_or_none(file_rec.metadata.get("page_or_slide")),
                detected_source_type="mixed_project_materials",
                source_role=str(file_rec.metadata.get("source_role") or "supporting_visual_evidence"),
                confidence=float(file_rec.metadata.get("confidence") or 0.5),
                markers=["vlm_derivative", str(file_rec.metadata.get("task_type") or "")],
                warnings=list(file_rec.warnings or []),
            )

        normalized = text.lower().replace("\u00a0", " ")
        markers_hit: list[str] = []
        scores: dict[str, float] = {}

        for source_type, markers in SOURCE_MARKERS.items():
            if not markers:
                continue
            hits = sum(1 for m in markers if m in normalized)
            if hits:
                scores[source_type] = hits / len(markers)
                markers_hit.extend(m for m in markers if m in normalized)

        slide_count = len(SLIDE_RE.findall(text)) or file_rec.metadata.get("slides_count")
        if file_rec.file_type == "pptx" and slide_count:
            scores["pptx_project_presentation"] = max(
                scores.get("pptx_project_presentation", 0.0),
                min(int(slide_count) / 10.0, 1.0) if isinstance(slide_count, int) else 0.5,
            )
            markers_hit.append("file_type:pptx")

        person_lines = sum(
            1 for ln in text.splitlines()
            if re.match(r"^[А-ЯЁ][а-яё]+\s+[А-ЯЁ]", ln.strip())
        )
        if person_lines >= 3 and "тимлид" in normalized:
            scores["team_list"] = max(scores.get("team_list", 0.0), 0.6)

        if scores:
            detected = max(scores, key=scores.get)
            confidence = round(min(scores[detected] + 0.15, 1.0), 3)
        elif file_rec.file_type in ("txt", "md") and len(text) < 200:
            detected = "raw_notes"
            confidence = 0.3
        elif len(scores) == 0 and len(text) > 500:
            detected = "mixed_project_materials"
            confidence = 0.4
        else:
            detected = "unknown"
            confidence = 0.2

        warnings = list(file_rec.warnings or [])
        meta = file_rec.metadata or {}
        return SourceInventoryItem(
            source_id=source_id,
            filename=file_rec.filename,
            file_type=file_rec.file_type,
            char_count=len(text),
            slide_count=_int_or_none(meta.get("slides_count")),
            page_count=_int_or_none(meta.get("page_count")),
            table_count=_int_or_none(meta.get("table_count")),
            detected_source_type=detected,
            confidence=confidence,
            markers=list(dict.fromkeys(markers_hit))[:20],
            warnings=warnings,
        )


def _int_or_none(value) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def has_single_high_confidence_ready_doc(
    inventory: list[SourceInventoryItem],
    *,
    threshold: float = 0.65,
) -> bool:
    """True when exactly one ready_landing_doc and no other useful sources."""
    ready = [
        s for s in inventory
        if s.detected_source_type == "ready_landing_doc" and s.confidence >= threshold
    ]
    if len(ready) != 1:
        return False
    others = [
        s for s in inventory
        if s.source_id != ready[0].source_id and s.char_count > 100
    ]
    return len(others) == 0
