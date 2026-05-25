"""Classify live project diagnostic JSON into actionable verdict gate."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class DiagnosticVerdict:
    status: str
    classification: str
    layer: str
    reason: str
    action: str
    checks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def verdict_exit_code(status: str) -> int:
    if status in ("OK", "USER_ACTION_REQUIRED"):
        return 0
    return 1


def normalize_diagnostic_payload(raw: dict[str, Any]) -> dict[str, Any]:
    """Unify field names from debug_live_project_consistency JSON."""
    payload = dict(raw)
    team_structured = int(payload.get("team_structured_count") or 0)
    team_bullets = int(payload.get("team_count") or 0)
    contract_team_count = int(payload.get("contract_team_count") or max(team_structured, team_bullets))

    export_has_team = payload.get("export_has_team")
    if export_has_team is None:
        export_has_team = bool(payload.get("export_has_team_section"))

    generated_landing_has_team = payload.get("generated_landing_has_team")
    if generated_landing_has_team is None:
        generated_landing_has_team = bool(payload.get("landing_has_team"))

    contract_has_team = payload.get("contract_has_team")
    if contract_has_team is None:
        contract_has_team = team_structured > 0 or contract_team_count > 0

    payload["team_structured_count"] = team_structured
    payload["contract_team_count"] = contract_team_count
    payload["contract_has_team"] = bool(contract_has_team)
    payload["export_has_team"] = bool(export_has_team)
    payload["generated_landing_has_team"] = bool(generated_landing_has_team)
    payload["landing_stale"] = bool(payload.get("landing_stale"))
    payload["source_count"] = int(payload.get("source_count") or 0)
    payload["filenames"] = list(payload.get("filenames") or [])
    payload["verdict"] = str(payload.get("verdict") or "")
    return payload


def _has_team_source_file(filenames: list[str]) -> bool:
    for name in filenames:
        lower = name.lower()
        if lower.endswith(".docx") or lower.endswith(".txt"):
            return True
    return False


def _contract_has_team(payload: dict[str, Any]) -> bool:
    if payload.get("contract_has_team"):
        return True
    if payload.get("team_structured_count", 0) > 0:
        return True
    if payload.get("contract_team_count", 0) > 0:
        return True
    return False


def classify_live_project_diagnostic(payload: dict[str, Any]) -> DiagnosticVerdict:
    """Apply verdict gate rules to normalized diagnostic payload."""
    data = normalize_diagnostic_payload(payload)
    checks: list[str] = []

    source_count = data["source_count"]
    filenames = data["filenames"]
    verdict = data["verdict"]
    team_structured_count = data["team_structured_count"]
    export_has_team = data["export_has_team"]
    landing_stale = data["landing_stale"]
    contract_has_team = _contract_has_team(data)

    checks.append(f"source_count={source_count}")
    checks.append(f"filenames={filenames}")
    checks.append(f"team_structured_count={team_structured_count}")
    checks.append(f"export_has_team={export_has_team}")
    checks.append(f"landing_stale={landing_stale}")

    # Rule 1 — single file, no team source
    if source_count == 1 and verdict == "single_file_no_team_source":
        return DiagnosticVerdict(
            status="USER_ACTION_REQUIRED",
            classification="single_file_no_team_source",
            layer="user_input",
            reason="Загружен один файл. Команда не найдена в источниках.",
            action=(
                "Загрузите DOCX/TXT со списком команды или PPTX со слайдом "
                "'Команда проекта' в текстовом слое."
            ),
            checks=checks,
        )

    # Rule 2 — DOCX/TXT present, but team missing
    if (
        source_count >= 2
        and _has_team_source_file(filenames)
        and team_structured_count == 0
    ):
        return DiagnosticVerdict(
            status="BUG",
            classification="docx_present_but_team_missing",
            layer="extraction/team_parser/merge",
            reason="В проекте есть DOCX/TXT, но team_structured пуст.",
            action=(
                "Проверить extraction, team_parser, field_assembler, "
                "_merge_team_from_ms_contract."
            ),
            checks=checks,
        )

    # Rule 3 — contract has team, export lost team
    if contract_has_team and not export_has_team:
        return DiagnosticVerdict(
            status="BUG",
            classification="contract_has_team_but_export_missing",
            layer="export",
            reason="Команда есть в контракте, но отсутствует в HTML export.",
            action=(
                "Проверить landing_bridge, StyledHtmlExporter._team_section, "
                "export source selection."
            ),
            checks=checks,
        )

    # Rule 4 — stale landing
    if landing_stale:
        return DiagnosticVerdict(
            status="STALE",
            classification="stale_generated_landing",
            layer="generation",
            reason="Generated landing устарел относительно contract.",
            action=(
                "Выполнить regenerate landing или исправить auto-invalidation "
                "после reparse."
            ),
            checks=checks,
        )

    # Rule 5 — OK
    if (
        source_count >= 2
        and team_structured_count > 0
        and export_has_team
        and not landing_stale
    ):
        return DiagnosticVerdict(
            status="OK",
            classification="team_pipeline_ok",
            layer="all",
            reason="Команда найдена и отображается в export.",
            action="Нет действий.",
            checks=checks,
        )

    # Rule 6 — ambiguous
    return DiagnosticVerdict(
        status="BUG",
        classification="ambiguous_inconsistent_state",
        layer="unknown",
        reason="Состояние не попало ни в один ожидаемый сценарий.",
        action="Проверить полный JSON debug_live_project_consistency.",
        checks=checks,
    )


def format_verdict_report(
    gate: DiagnosticVerdict,
    payload: dict[str, Any],
) -> str:
    """Human-readable gate output."""
    data = normalize_diagnostic_payload(payload)
    lines = [
        "LIVE PROJECT VERDICT",
        f"Status: {gate.status}",
        f"Classification: {gate.classification}",
        f"Layer: {gate.layer}",
        "",
        "Evidence:",
        f"- source_count: {data['source_count']}",
        f"- filenames: {data['filenames']}",
        f"- team_structured_count: {data['team_structured_count']}",
        f"- contract_team_count: {data['contract_team_count']}",
        f"- contract_has_team: {data['contract_has_team']}",
        f"- export_has_team: {data['export_has_team']}",
        f"- generated_landing_has_team: {data['generated_landing_has_team']}",
        f"- landing_stale: {data['landing_stale']}",
        f"- parser_mode: {data.get('parser_mode', '')}",
        f"- evidence_count: {data.get('evidence_count', '')}",
        f"- team_coverage: {data.get('team_coverage', '')}",
        f"- debug_verdict: {data.get('verdict', '')}",
        "",
        "Reason:",
        gate.reason,
        "",
        "Action:",
        gate.action,
        "",
        f"Exit code: {verdict_exit_code(gate.status)}",
    ]
    return "\n".join(lines)
