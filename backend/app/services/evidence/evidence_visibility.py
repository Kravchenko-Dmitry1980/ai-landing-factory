"""Build slim evidence visibility response for editor UI."""

from __future__ import annotations

from app.schemas.evidence import EvidenceAssemblyReport, FieldEvidence, FieldSourceTrace
from app.schemas.evidence_visibility import (
    EvidenceSourceView,
    EvidenceVisibilityResponse,
    FieldSourceView,
)
from app.schemas.fidelity import FidelityMetadata
from app.schemas.landing_contract import LandingContract

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
            return self._from_report(contract, fidelity, report)

        return self._fallback(contract, fidelity)

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
        )

        parser_mode = fidelity.parser_mode if fidelity else report.parser_strategy
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
            warnings=list(report.warnings),
            improvement_hints=hints,
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
        hints.extend(
            FIELD_IMPROVEMENT_HINTS[f]
            for f in missing + weak
            if f in FIELD_IMPROVEMENT_HINTS
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
            warnings=warnings,
            improvement_hints=_dedupe(hints),
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


def _build_improvement_hints(
    missing: list[str],
    weak: list[str],
    sources: list[EvidenceSourceView],
) -> list[str]:
    hints: list[str] = []
    for field in missing + weak:
        hint = FIELD_IMPROVEMENT_HINTS.get(field)
        if hint and hint not in hints:
            hints.append(hint)
    for src in sources:
        if src.status == "empty":
            hints.append(
                f"Файл «{src.filename}» похож на image-only презентацию. "
                "Для анализа нужен OCR или текстовая версия."
            )
    if "team" in missing and sources and all(
        s.file_type == "pptx" for s in sources if s.status != "empty"
    ):
        if PPTX_ONLY_TEAM_HINT not in hints:
            hints.append(PPTX_ONLY_TEAM_HINT)
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
