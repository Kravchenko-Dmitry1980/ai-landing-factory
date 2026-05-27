"""Build slim evidence visibility response for editor UI."""

from __future__ import annotations

from app.schemas.evidence import EvidenceAssemblyReport, FieldEvidence, FieldSourceTrace
from app.schemas.evidence_visibility import (
    EvidenceSourceView,
    EvidenceVisibilityResponse,
    FieldSourceView,
)
from app.config import settings
from app.schemas.fidelity import FidelityMetadata
from app.schemas.landing_contract import LandingContract
from app.schemas.vlm import VlmExtractionSummaryLine
from app.product_mode import (
    SIMPLE_IMAGE_ONLY_HINT,
    map_improvement_hint,
    sanitize_message_list,
)
from app.services.visual.visual_evidence_builder import VisualEvidenceBuilder

SNIPPET_MAX = 180

CONTRACT_FIELD_ORDER = (
    "title",
    "client",
    "timeline",
    "lead",
    "essence",
    "tasks",
    "purpose",
    "inputs",
    "outputs",
    "results",
    "outlook",
    "tech_stack",
    "team",
    "modules",
    "quote",
)

ROLE_NOTES: dict[str, str] = {
    "primary_project_doc": "Задаёт название, заказчика и основную структуру проекта.",
    "module_presentation": "Используется для обогащения модуля, но не меняет название проекта.",
    "supporting_presentation": "Дополняет стек, результаты или архитектуру.",
    "technical_spec": "Источник требований, входных и выходных данных.",
    "report": "Источник результатов, метрик и перспектив развития.",
    "team_source": "Источник состава команды.",
    "unknown": "Роль источника не определена однозначно.",
}

PPTX_ONLY_TEAM_HINT = (
    "В презентации не найден извлекаемый текст команды. Если команда находится "
    "на изображении, нужен OCR или отдельный DOCX/TXT."
)

PPTX_ONLY_TEAM_HINT_SIMPLE = (
    "В презентации не найден извлекаемый текст команды. "
    "Добавьте DOCX/TXT со списком участников или отредактируйте блок команды вручную."
)

SINGLE_FILE_WARNING = (
    "Загружен только один файл. Для полного ленда обычно нужен комплект: "
    "PPTX + DOCX/TXT."
)

SINGLE_FILE_TEAM_HINT = (
    "Загружен только один файл. Команда не найдена. Добавьте DOCX/TXT со списком "
    "участников или PPTX со слайдом «Команда проекта» с ФИО и ролями в текстовом слое."
)

FIELD_IMPROVEMENT_HINTS: dict[str, str] = {
    "team": (
        "Добавьте файл или слайд с составом команды (DOCX/TXT или слайд "
        "«Команда проекта» с ФИО и ролями)."
    ),
    "results": "Добавьте отчёт или слайд с итогами проекта.",
    "outlook": "Добавьте материалы о перспективах развития проекта.",
    "tech_stack": "Добавьте презентацию или ТЗ с технологиями проекта.",
    "modules": "Добавьте описание модулей в ленд или модульную презентацию.",
    "essence": "Добавьте раздел «Суть проекта» в основной документ.",
    "tasks": "Добавьте задачи проекта в основной документ или презентацию.",
    "title": "Добавьте готовый ленд или презентацию с названием проекта.",
}


class EvidenceVisibilityBuilder:
    """Transform contract fidelity into editor-safe evidence visibility payload."""

    def build(self, contract: LandingContract) -> EvidenceVisibilityResponse:
        fidelity = contract.fidelity
        report = fidelity.evidence_report if fidelity else None

        if report:
            return _finalize_visibility(
                self._from_report(contract, fidelity, report),
            )

        return _finalize_visibility(self._fallback(contract, fidelity))

    def _from_report(
        self,
        contract: LandingContract,
        fidelity: FidelityMetadata | None,
        report: EvidenceAssemblyReport,
    ) -> EvidenceVisibilityResponse:
        evidence_by_source = _count_evidence_by_source(report.fields)
        strong_sources = _strong_source_filenames(report, fidelity)
        sources = [
            _build_source_view(src, evidence_by_source, strong_sources)
            for src in report.sources
        ]
        field_sources = _build_field_sources(report, fidelity)
        hints = _build_improvement_hints(
            report.missing_fields,
            report.weak_fields,
            sources,
            source_count=len(report.sources),
            team_structured_count=len(fidelity.team_structured) if fidelity else 0,
        )

        warnings = list(report.warnings)
        warnings.extend(
            _build_source_warnings(
                len(report.sources),
                fidelity.team_structured if fidelity else [],
                report.missing_fields,
            )
        )

        parser_mode = fidelity.parser_mode if fidelity else report.parser_strategy
        field_decisions = _fusion_field_decisions(fidelity)
        orch = fidelity.orchestration_trace if fidelity else None
        team_group_expansions: list[dict[str, str]] = []
        orchestration_payload = None
        if orch:
            team_group_expansions = list(getattr(orch, "team_group_expansions", []) or [])
            orchestration_payload = orch.model_dump() if hasattr(orch, "model_dump") else orch
        if field_decisions:
            field_sources = _merge_fusion_field_sources(field_sources, field_decisions)

        team_verification = fidelity.team_verification_report if fidelity else None
        ocr_review = list(fidelity.ocr_review_candidates) if fidelity else []
        team_policy = fidelity.team_publication_policy if fidelity else "verified_only"
        pub_mode = fidelity.team_publication_mode if fidelity else "draft_auto"
        review_warning = fidelity.team_review_warning if fidelity else None
        if team_verification and team_verification.warnings:
            warnings.extend(team_verification.warnings)
        if review_warning:
            warnings.append(review_warning)

        visual_summary = _visual_evidence_summary(fidelity)
        vlm_summary = _vlm_extraction_summary(fidelity)

        return EvidenceVisibilityResponse(
            project_id=str(contract.project_id),
            parser_mode=parser_mode,
            source_count=len(report.sources),
            evidence_count=report.total_evidence_items,
            assembly_confidence=report.confidence,
            sources=sources,
            field_sources=field_sources,
            missing_fields=list(report.missing_fields),
            weak_fields=list(report.weak_fields),
            strong_fields=list(report.strong_fields),
            warnings=_dedupe(warnings),
            improvement_hints=hints,
            field_decisions=field_decisions,
            orchestration_trace=orchestration_payload,
            team_group_expansions=team_group_expansions,
            team_verification_report=team_verification,
            ocr_review_candidates=ocr_review,
            team_publication_policy=team_policy,
            team_publication_mode=pub_mode,
            team_review_warning=review_warning,
            visual_evidence_summary=visual_summary,
            visual_items_count=fidelity.visual_items_count if fidelity else 0,
            vlm_candidates_count=fidelity.vlm_candidates_count if fidelity else 0,
            ocr_visual_candidates_count=fidelity.ocr_visual_candidates_count if fidelity else 0,
            vlm_enabled=fidelity.vlm_enabled if fidelity else False,
            vlm_provider=fidelity.vlm_provider if fidelity else "disabled",
            vlm_processed_count=fidelity.vlm_processed_count if fidelity else 0,
            vlm_skipped_count=fidelity.vlm_skipped_count if fidelity else 0,
            vlm_extraction_summary=vlm_summary,
            advanced_diagnostics_enabled=settings.show_advanced_diagnostics,
        )

    def _fallback(
        self,
        contract: LandingContract,
        fidelity: FidelityMetadata | None,
    ) -> EvidenceVisibilityResponse:
        parser_mode = fidelity.parser_mode if fidelity else "heuristic"
        missing = list(fidelity.missing_fields) if fidelity else []
        weak = list(fidelity.weak_fields) if fidelity else []
        hints: list[str] = []
        warnings: list[str] = []

        if not fidelity or not fidelity.evidence_report:
            warnings.append(
                "Данные о сборке из источников недоступны для этого контракта."
            )
        if parser_mode == "heuristic":
            hints.append(
                "Система использовала fallback-эвристику. Добавьте больше "
                "структурированных материалов или нажмите reparse после загрузки "
                "дополнительных файлов."
            )
        hints = _dedupe(
            hints
            + _build_improvement_hints(
                missing,
                weak,
                [],
                source_count=fidelity.source_count if fidelity else 0,
                team_structured_count=len(fidelity.team_structured) if fidelity else 0,
            )
        )
        warnings.extend(
            _build_source_warnings(
                fidelity.source_count if fidelity else 0,
                fidelity.team_structured if fidelity else [],
                missing,
            )
        )

        strong: list[str] = []
        if fidelity and fidelity.evidence_report:
            strong = list(fidelity.evidence_report.strong_fields)
        field_sources = _field_sources_from_traces(
            fidelity.field_sources if fidelity else [],
            missing,
            weak,
            strong,
        )
        vlm_summary = _vlm_extraction_summary(fidelity)

        return EvidenceVisibilityResponse(
            project_id=str(contract.project_id),
            parser_mode=parser_mode,
            source_count=fidelity.source_count if fidelity else 0,
            evidence_count=fidelity.evidence_count if fidelity else 0,
            assembly_confidence=fidelity.assembly_confidence if fidelity else 0.0,
            sources=[],
            field_sources=field_sources,
            missing_fields=missing,
            weak_fields=weak,
            strong_fields=[],
            warnings=_dedupe(warnings),
            improvement_hints=hints,
            field_decisions=_fusion_field_decisions(fidelity),
            visual_evidence_summary=_visual_evidence_summary(fidelity),
            visual_items_count=fidelity.visual_items_count if fidelity else 0,
            vlm_candidates_count=fidelity.vlm_candidates_count if fidelity else 0,
            ocr_visual_candidates_count=fidelity.ocr_visual_candidates_count if fidelity else 0,
            vlm_enabled=fidelity.vlm_enabled if fidelity else False,
            vlm_provider=fidelity.vlm_provider if fidelity else "disabled",
            vlm_processed_count=fidelity.vlm_processed_count if fidelity else 0,
            vlm_skipped_count=fidelity.vlm_skipped_count if fidelity else 0,
            vlm_extraction_summary=vlm_summary,
            advanced_diagnostics_enabled=settings.show_advanced_diagnostics,
        )


def _finalize_visibility(
    report: EvidenceVisibilityResponse,
) -> EvidenceVisibilityResponse:
    advanced = settings.show_advanced_diagnostics
    if advanced:
        return report

    hints = [
        map_improvement_hint(h, advanced=False) for h in report.improvement_hints
    ]
    warnings = sanitize_message_list(list(report.warnings), advanced=False)
    review_warning = report.team_review_warning
    if review_warning:
        from app.product_mode import sanitize_user_message

        review_warning = sanitize_user_message(review_warning, advanced=False)

    return report.model_copy(
        update={
            "improvement_hints": _dedupe(hints),
            "warnings": warnings,
            "team_review_warning": review_warning,
            "visual_evidence_summary": [],
            "vlm_extraction_summary": [],
            "vlm_candidates_count": 0,
            "ocr_visual_candidates_count": 0,
            "vlm_enabled": False,
            "vlm_provider": "disabled",
            "vlm_processed_count": 0,
            "vlm_skipped_count": 0,
            "visual_items_count": 0,
            "ocr_review_candidates": [],
            "team_verification_report": None,
            "orchestration_trace": None,
            "advanced_diagnostics_enabled": False,
        }
    )


def _count_evidence_by_source(fields: dict[str, FieldEvidence]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for fe in fields.values():
        for item in fe.items:
            key = item.source_id or item.filename
            counts[key] = counts.get(key, 0) + 1
            counts[item.filename] = counts.get(item.filename, 0) + 1
    return counts


def _strong_source_filenames(
    report: EvidenceAssemblyReport,
    fidelity: FidelityMetadata | None,
) -> set[str]:
    strong_fields = set(report.strong_fields)
    filenames: set[str] = set()
    traces = report.field_traces or (fidelity.field_sources if fidelity else [])
    for trace in traces:
        if trace.field_name in strong_fields:
            filenames.add(trace.source_filename)
    for field_name in strong_fields:
        fe = report.fields.get(field_name)
        if not fe:
            continue
        for item in fe.items[:3]:
            filenames.add(item.filename)
    return filenames


def _build_source_view(
    src,
    evidence_by_source: dict[str, int],
    strong_sources: set[str],
) -> EvidenceSourceView:
    ev_count = evidence_by_source.get(src.source_id, 0)
    if ev_count == 0:
        ev_count = evidence_by_source.get(src.filename, 0)

    notes: list[str] = []
    role_note = ROLE_NOTES.get(src.source_role)
    if role_note:
        notes.append(role_note)
    notes.extend(src.warnings[:2])

    if src.char_count == 0 or ev_count == 0:
        status = "empty"
        notes.append(
            "Текст не извлечён. Вероятно, файл содержит изображения без текстового слоя."
        )
    elif src.filename in strong_sources:
        status = "used"
    elif ev_count > 0:
        status = "weak"
    else:
        status = "ignored"

    return EvidenceSourceView(
        source_id=src.source_id,
        filename=src.filename,
        file_type=src.file_type,
        detected_source_type=src.detected_source_type,
        source_role=src.source_role,
        evidence_count=ev_count,
        char_count=src.char_count,
        slide_count=src.slide_count,
        page_count=src.page_count,
        status=status,
        notes=_dedupe(notes),
    )


def _build_field_sources(
    report: EvidenceAssemblyReport,
    fidelity: FidelityMetadata | None,
) -> dict[str, FieldSourceView]:
    result: dict[str, FieldSourceView] = {}
    traces_by_field = _group_traces(report.field_traces or [])

    for field_name in CONTRACT_FIELD_ORDER:
        fe = report.fields.get(field_name)
        traces = traces_by_field.get(field_name, [])
        if not fe and not traces:
            if field_name in report.missing_fields:
                result[field_name] = FieldSourceView(
                    field_name=field_name,
                    coverage="missing",
                )
            continue

        coverage = fe.coverage if fe else _coverage_from_lists(
            field_name, report.missing_fields, report.weak_fields, report.strong_fields
        )
        source_refs = list(fe.source_refs) if fe else [
            t.source_filename for t in traces
        ]
        reasons = [t.reason for t in traces if t.reason]
        snippets = [
            _truncate(s) for s in (fe.selected_texts if fe else [])[:3]
        ]

        result[field_name] = FieldSourceView(
            field_name=field_name,
            coverage=coverage,
            confidence=fe.confidence if fe else (traces[0].confidence if traces else 0.0),
            source_refs=_dedupe(source_refs),
            reasons=_dedupe(reasons),
            selected_snippets=snippets,
        )

    return result


def _field_sources_from_traces(
    traces: list[FieldSourceTrace],
    missing: list[str],
    weak: list[str],
    strong: list[str],
) -> dict[str, FieldSourceView]:
    grouped = _group_traces(traces)
    result: dict[str, FieldSourceView] = {}
    for field_name in CONTRACT_FIELD_ORDER:
        field_traces = grouped.get(field_name, [])
        if not field_traces and field_name not in missing + weak:
            continue
        coverage = _coverage_from_lists(field_name, missing, weak, strong)
        result[field_name] = FieldSourceView(
            field_name=field_name,
            coverage=coverage,
            confidence=max((t.confidence for t in field_traces), default=0.0),
            source_refs=[t.source_filename for t in field_traces],
            reasons=[t.reason for t in field_traces if t.reason],
            selected_snippets=[],
        )
    return result


def _group_traces(traces: list[FieldSourceTrace]) -> dict[str, list[FieldSourceTrace]]:
    grouped: dict[str, list[FieldSourceTrace]] = {}
    for trace in traces:
        grouped.setdefault(trace.field_name, []).append(trace)
    return grouped


def _coverage_from_lists(
    field_name: str,
    missing: list[str],
    weak: list[str],
    strong: list[str],
) -> str:
    if field_name in missing:
        return "missing"
    if field_name in weak:
        return "weak"
    if field_name in strong:
        return "strong"
    return "missing"


def _build_source_warnings(
    source_count: int,
    team_structured: list,
    missing_fields: list[str],
) -> list[str]:
    warnings: list[str] = []
    if source_count == 1:
        if SINGLE_FILE_WARNING not in warnings:
            warnings.append(SINGLE_FILE_WARNING)
        if not team_structured and "team" in missing_fields:
            warnings.append(SINGLE_FILE_TEAM_HINT)
    return warnings


def _build_improvement_hints(
    missing: list[str],
    weak: list[str],
    sources: list[EvidenceSourceView],
    *,
    source_count: int = 0,
    team_structured_count: int = 0,
) -> list[str]:
    hints: list[str] = []
    for field in missing + weak:
        hint = FIELD_IMPROVEMENT_HINTS.get(field)
        if hint and hint not in hints:
            hints.append(hint)
    for src in sources:
        if src.status == "empty":
            if settings.show_advanced_diagnostics:
                hints.append(
                    f"Файл «{src.filename}» похож на image-only презентацию. "
                    "Для анализа нужен OCR или текстовая версия."
                )
            else:
                hints.append(SIMPLE_IMAGE_ONLY_HINT)
    if source_count == 1 and team_structured_count == 0:
        if SINGLE_FILE_TEAM_HINT not in hints:
            hints.append(SINGLE_FILE_TEAM_HINT)
    if "team" in missing and sources and all(
        s.file_type == "pptx" for s in sources if s.status != "empty"
    ):
        team_hint = (
            PPTX_ONLY_TEAM_HINT
            if settings.show_advanced_diagnostics
            else PPTX_ONLY_TEAM_HINT_SIMPLE
        )
        if team_hint not in hints:
            hints.append(team_hint)
    return _dedupe(hints)


def _truncate(text: str) -> str:
    text = (text or "").strip()
    if len(text) <= SNIPPET_MAX:
        return text
    return text[: SNIPPET_MAX - 1] + "…"


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _vlm_extraction_summary(fidelity: FidelityMetadata | None) -> list[VlmExtractionSummaryLine]:
    if not fidelity or not fidelity.vlm_extraction_report:
        return []
    report = fidelity.vlm_extraction_report
    lines: list[VlmExtractionSummaryLine] = []
    for ext in report.extractions:
        slide = None
        for cand in ext.field_candidates:
            if cand.source_slide is not None:
                slide = cand.source_slide
                break
        if slide is None and ext.source_location.startswith("slide-"):
            try:
                slide = int(ext.source_location.split("-", 1)[1])
            except ValueError:
                slide = None
        lines.append(
            VlmExtractionSummaryLine(
                source_filename=ext.source_filename,
                page_or_slide=slide,
                visual_content_type=ext.visual_content_type,
                task_type=ext.task_type,
                provider=ext.provider,
                confidence=round(ext.confidence, 2),
                field_count=len(ext.field_candidates),
                warnings=list(ext.warnings[:3]),
            )
        )
    return lines


def _visual_evidence_summary(fidelity: FidelityMetadata | None):
    if not fidelity or not fidelity.visual_evidence_report:
        return []
    return VisualEvidenceBuilder.summarize_report(fidelity.visual_evidence_report)


def _fusion_field_decisions(fidelity: FidelityMetadata | None) -> dict[str, str]:
    if not fidelity or not fidelity.field_decisions:
        return {}
    summary: dict[str, str] = {}
    for field_name, raw in fidelity.field_decisions.items():
        if isinstance(raw, dict):
            sources = raw.get("selected_sources") or []
            if sources:
                summary[field_name] = " + ".join(str(s) for s in sources)
        elif isinstance(raw, str):
            summary[field_name] = raw
    return summary


def _merge_fusion_field_sources(
    field_sources: dict[str, FieldSourceView],
    field_decisions: dict[str, str],
) -> dict[str, FieldSourceView]:
    for field_name, sources_label in field_decisions.items():
        refs = [part.strip() for part in sources_label.split("+") if part.strip()]
        existing = field_sources.get(field_name)
        if existing:
            merged_refs = _dedupe(list(existing.source_refs) + refs)
            field_sources[field_name] = existing.model_copy(
                update={
                    "source_refs": merged_refs,
                    "reasons": _dedupe(
                        list(existing.reasons) + [f"field fusion: {sources_label}"]
                    ),
                    "coverage": existing.coverage if existing.coverage != "missing" else "strong",
                }
            )
        else:
            field_sources[field_name] = FieldSourceView(
                field_name=field_name,
                coverage="strong",
                confidence=0.85,
                source_refs=refs,
                reasons=[f"field fusion: {sources_label}"],
            )
    return field_sources
