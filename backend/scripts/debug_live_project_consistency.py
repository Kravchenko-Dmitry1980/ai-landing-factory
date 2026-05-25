#!/usr/bin/env python3
"""Live project consistency audit: sources → contract → landing → export."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from app.config import settings  # noqa: E402
from app.services.diagnostics.live_project_verdict import (  # noqa: E402
    classify_live_project_diagnostic,
    format_verdict_report,
    verdict_exit_code,
)
from app.services.diagnostics.project_discovery import (  # noqa: E402
    ProjectDiscoveryError,
    get_backend_url_from_runtime,
    resolve_project_id,
)

DEFAULT_BACKEND_URL = "http://127.0.0.1:8001"

FORBIDDEN_HTML_NAMES = (
    "Посты Telegram",
    "Из Telegram",
    "Схема обработки данных",
    "Векторная БД",
    "Google Colab",
    "Qdrant Cloud",
)

SINGLE_FILE_HINT = (
    "Загружен только один файл. Команда не найдена. Добавьте DOCX/TXT со списком "
    "участников или PPTX со слайдом команды в текстовом слое."
)

VERDICTS = (
    "OK",
    "single_file_no_team_source",
    "uploaded_docx_but_extraction_missing",
    "evidence_has_team_but_contract_missing",
    "contract_has_team_but_landing_missing",
    "landing_has_team_but_export_missing",
    "contract_has_team_but_export_missing",
    "stale_generated_landing",
    "stale_export_or_wrong_project",
)


@dataclass
class ProjectDiagnostics:
    project_id: str
    project_exists: bool = False
    project_name: str | None = None
    source_count: int = 0
    filenames: list[str] = field(default_factory=list)
    extensions: list[str] = field(default_factory=list)
    has_docx: bool = False
    has_pptx_only: bool = False
    extraction_char_counts: dict[str, int] = field(default_factory=dict)
    parser_mode: str = ""
    evidence_count: int = 0
    team_count: int = 0
    team_structured_count: int = 0
    team_coverage: str = "missing"
    missing_fields: list[str] = field(default_factory=list)
    weak_fields: list[str] = field(default_factory=list)
    landing_exists: bool = False
    landing_has_team: bool = False
    landing_generated_at: str | None = None
    contract_version: int = 0
    contract_updated_at: str | None = None
    export_has_team_section: bool = False
    export_has_team_title: bool = False
    export_has_team_card: bool = False
    export_forbidden_names: list[str] = field(default_factory=list)
    landing_stale: bool = False
    improvement_hints: list[str] = field(default_factory=list)
    verdict: str = "OK"
    errors: list[str] = field(default_factory=list)


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _team_block_has_content(blocks: list[dict[str, Any]]) -> bool:
    for block in blocks:
        if block.get("key") == "team":
            bullets = block.get("bullets") or []
            content = (block.get("content") or "").strip()
            return bool(bullets or content)
    return False


def _extension(name: str) -> str:
    lower = name.lower()
    if "." in lower:
        return lower.rsplit(".", 1)[-1]
    return ""


def audit_project(backend_url: str, project_id: str) -> ProjectDiagnostics:
    diag = ProjectDiagnostics(project_id=project_id)
    base = backend_url.rstrip("/")
    api = f"{base}/api/v1"

    with httpx.Client(timeout=120.0, trust_env=False) as client:
        proj_resp = client.get(f"{api}/projects/{project_id}")
        if proj_resp.status_code == 404:
            diag.errors.append("Project not found")
            diag.verdict = "stale_export_or_wrong_project"
            return diag
        if proj_resp.status_code != 200:
            diag.errors.append(f"GET project HTTP {proj_resp.status_code}")
            diag.verdict = "stale_export_or_wrong_project"
            return diag

        proj = proj_resp.json()
        diag.project_exists = True
        diag.project_name = proj.get("name")

        contract: dict[str, Any] | None = None
        contract_resp = client.get(f"{api}/projects/{project_id}/contract")
        if contract_resp.status_code == 200:
            contract = contract_resp.json()
        elif contract_resp.status_code != 404:
            diag.errors.append(f"GET contract HTTP {contract_resp.status_code}")

        evidence: dict[str, Any] | None = None
        evidence_resp = client.get(f"{api}/projects/{project_id}/evidence-report")
        if evidence_resp.status_code == 200:
            evidence = evidence_resp.json()
        elif contract and evidence_resp.status_code != 404:
            diag.errors.append(f"GET evidence-report HTTP {evidence_resp.status_code}")

        landing: dict[str, Any] | None = None
        landing_resp = client.get(f"{api}/projects/{project_id}/landing")
        if landing_resp.status_code == 200:
            landing = landing_resp.json()
        elif landing_resp.status_code not in (404,):
            diag.errors.append(f"GET landing HTTP {landing_resp.status_code}")

        html = ""
        export_resp = client.get(
            f"{api}/projects/{project_id}/export/html",
            params={"theme": "university_platform"},
        )
        if export_resp.status_code == 200:
            payload = export_resp.json()
            html = payload.get("html") or ""
        elif export_resp.status_code != 404:
            diag.errors.append(f"GET export/html HTTP {export_resp.status_code}")

    if evidence:
        diag.source_count = int(evidence.get("source_count") or 0)
        sources = evidence.get("sources") or []
        diag.filenames = [s.get("filename", "") for s in sources if s.get("filename")]
        diag.extensions = sorted({_extension(n) for n in diag.filenames if n})
        diag.extraction_char_counts = {
            s.get("filename", "?"): int(s.get("char_count") or 0) for s in sources
        }
        diag.has_docx = any(_extension(n) == "docx" for n in diag.filenames)
        diag.evidence_count = int(evidence.get("evidence_count") or 0)
        diag.improvement_hints = list(evidence.get("improvement_hints") or [])
        team_view = (evidence.get("field_sources") or {}).get("team") or {}
        diag.team_coverage = team_view.get("coverage") or "missing"

    if contract:
        fidelity = contract.get("fidelity") or {}
        diag.parser_mode = fidelity.get("parser_mode") or ""
        if not diag.source_count:
            diag.source_count = int(fidelity.get("source_count") or 0)
        diag.team_structured_count = len(fidelity.get("team_structured") or [])
        team_block = next(
            (b for b in contract.get("blocks") or [] if b.get("key") == "team"),
            None,
        )
        diag.team_count = diag.team_structured_count or len(
            (team_block or {}).get("bullets") or []
        )
        diag.missing_fields = list(fidelity.get("missing_fields") or [])
        diag.weak_fields = list(fidelity.get("weak_fields") or [])
        diag.contract_version = int(contract.get("version") or 0)
        diag.contract_updated_at = contract.get("updated_at")

        if not diag.filenames and diag.source_count:
            traces = fidelity.get("field_sources") or []
            diag.filenames = sorted(
                {t.get("source_filename") for t in traces if t.get("source_filename")}
            )
            diag.extensions = sorted({_extension(n) for n in diag.filenames if n})
            diag.has_docx = any(_extension(n) == "docx" for n in diag.filenames)

    if landing:
        diag.landing_exists = True
        diag.landing_has_team = _team_block_has_content(landing.get("blocks") or [])
        diag.landing_generated_at = landing.get("generated_at")

    if contract and landing:
        contract_dt = _parse_dt(diag.contract_updated_at)
        landing_dt = _parse_dt(diag.landing_generated_at)
        if contract_dt and landing_dt and contract_dt > landing_dt:
            diag.landing_stale = True
        if diag.team_structured_count > 0 and not diag.landing_has_team:
            diag.landing_stale = True

    pptx_ext = {"pptx", "ppt"}
    diag.has_pptx_only = (
        diag.source_count == 1
        and diag.extensions
        and all(ext in pptx_ext for ext in diag.extensions)
    )

    if html:
        diag.export_has_team_section = "id='team'" in html or 'id="team"' in html
        diag.export_has_team_title = "Команда проекта" in html
        diag.export_has_team_card = "team-card" in html
        diag.export_forbidden_names = [
            name for name in FORBIDDEN_HTML_NAMES if f"<h3>{name}</h3>" in html
        ]

    diag.verdict = _compute_verdict(diag, evidence)
    return diag


def _compute_verdict(
    diag: ProjectDiagnostics,
    evidence: dict[str, Any] | None,
) -> str:
    if not diag.project_exists:
        return "stale_export_or_wrong_project"

    if diag.landing_stale:
        return "stale_generated_landing"

    docx_empty = False
    if evidence and diag.has_docx:
        for src in evidence.get("sources") or []:
            if _extension(src.get("filename", "")) == "docx":
                if int(src.get("char_count") or 0) == 0 or src.get("status") == "empty":
                    docx_empty = True
                    break
    if docx_empty:
        return "uploaded_docx_but_extraction_missing"

    team_evidence = False
    if evidence:
        team_view = (evidence.get("field_sources") or {}).get("team") or {}
        team_evidence = team_view.get("coverage") in ("strong", "weak") or bool(
            team_view.get("source_refs")
        )
        if "team" in (evidence.get("strong_fields") or []):
            team_evidence = True

    if team_evidence and diag.team_structured_count == 0:
        return "evidence_has_team_but_contract_missing"

    if diag.team_structured_count > 0 and diag.landing_exists and not diag.landing_has_team:
        return "contract_has_team_but_landing_missing"

    if diag.landing_has_team and not diag.export_has_team_section:
        return "landing_has_team_but_export_missing"

    if diag.team_structured_count > 0 and not diag.export_has_team_section:
        return "contract_has_team_but_export_missing"

    if diag.source_count == 1 and diag.team_structured_count == 0:
        return "single_file_no_team_source"

    if diag.has_docx and diag.team_coverage != "strong" and diag.team_structured_count == 0:
        return "uploaded_docx_but_extraction_missing"

    return "OK"


def diagnostics_to_payload(diag: ProjectDiagnostics) -> dict[str, Any]:
    """JSON payload with gate-compatible alias fields."""
    payload = asdict(diag)
    payload["export_has_team"] = diag.export_has_team_section
    payload["contract_team_count"] = max(diag.team_structured_count, diag.team_count)
    payload["contract_has_team"] = (
        diag.team_structured_count > 0 or diag.team_count > 0
    )
    payload["generated_landing_has_team"] = diag.landing_has_team
    return payload


def print_report(diag: ProjectDiagnostics, as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(diagnostics_to_payload(diag), ensure_ascii=False, indent=2))
        return

    print(f"=== Live Project Consistency: {diag.project_id} ===")
    print(f"Project: {diag.project_name or '(unknown)'} exists={diag.project_exists}")
    print()
    print("--- Sources ---")
    print(f"source_count={diag.source_count}")
    print(f"filenames={diag.filenames}")
    print(f"extensions={diag.extensions}")
    print(f"has_docx={diag.has_docx} pptx_only={diag.has_pptx_only}")
    if diag.extraction_char_counts:
        for name, chars in diag.extraction_char_counts.items():
            print(f"  {name}: char_count={chars}")
    print()
    print("--- Contract ---")
    print(f"parser_mode={diag.parser_mode}")
    print(f"evidence_count={diag.evidence_count}")
    print(f"team_structured={diag.team_structured_count} team_bullets={diag.team_count}")
    print(f"team_coverage={diag.team_coverage}")
    print(f"missing_fields={diag.missing_fields}")
    print(f"weak_fields={diag.weak_fields}")
    print(f"version={diag.contract_version} updated_at={diag.contract_updated_at}")
    print()
    print("--- Generated landing ---")
    print(f"exists={diag.landing_exists} has_team={diag.landing_has_team}")
    print(f"generated_at={diag.landing_generated_at} stale={diag.landing_stale}")
    print()
    print("--- Export HTML ---")
    print(f"section#team={diag.export_has_team_section}")
    print(f"title 'Команда проекта'={diag.export_has_team_title}")
    print(f"team-card={diag.export_has_team_card}")
    if diag.export_forbidden_names:
        print(f"forbidden_names={diag.export_forbidden_names}")
    print()
    print(f"VERDICT: {diag.verdict}")
    if diag.improvement_hints:
        print("Hints:")
        for hint in diag.improvement_hints:
            print(f"  - {hint}")
    if diag.errors:
        print("Errors:")
        for err in diag.errors:
            print(f"  - {err}")


def assert_acceptance(diag: ProjectDiagnostics, assert_team_if_docx: bool) -> list[str]:
    failures: list[str] = []
    if not diag.project_exists:
        failures.append("project not found")
        return failures

    if assert_team_if_docx:
        if diag.has_docx:
            if diag.team_structured_count == 0:
                failures.append("DOCX present but contract team_structured is empty")
            if not diag.export_has_team_section:
                failures.append("DOCX present but export missing section#team")
            if not diag.export_has_team_card:
                failures.append("DOCX present but export missing team-card")
        elif diag.source_count == 1:
            if diag.verdict != "single_file_no_team_source":
                failures.append(
                    f"expected single_file_no_team_source, got {diag.verdict}"
                )

    bad_verdicts = {
        "evidence_has_team_but_contract_missing",
        "contract_has_team_but_landing_missing",
        "landing_has_team_but_export_missing",
        "contract_has_team_but_export_missing",
        "stale_generated_landing",
        "stale_export_or_wrong_project",
    }
    if diag.verdict in bad_verdicts:
        failures.append(f"verdict={diag.verdict}")

    if diag.export_forbidden_names:
        failures.append(f"forbidden names in export: {diag.export_forbidden_names}")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit live project source → contract → landing → export consistency",
    )
    parser.add_argument("--project-id", default="")
    parser.add_argument("--latest", action="store_true")
    parser.add_argument("--current", action="store_true")
    parser.add_argument("--runtime-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--backend-url", default="")
    parser.add_argument("--json", action="store_true", help="Print JSON diagnostics")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 on consistency failures (smoke mode)",
    )
    parser.add_argument(
        "--assert-team-if-docx-present",
        action="store_true",
        help="Require team in export when DOCX is among sources",
    )
    parser.add_argument(
        "--classify",
        action="store_true",
        help="Apply verdict gate classification to diagnostic output",
    )
    args = parser.parse_args()

    backend_url = args.backend_url.rstrip("/") if args.backend_url else get_backend_url_from_runtime(args.runtime_root)

    try:
        if args.latest and args.current:
            raise ProjectDiscoveryError("Use only one of --latest or --current.")
        if not args.project_id and not args.latest and not args.current:
            raise ProjectDiscoveryError(
                "Укажите --project-id, --latest или --current."
            )
        resolved = resolve_project_id(
            project_id=args.project_id or None,
            latest=args.latest,
            current=args.current,
            base_url=backend_url,
            runtime_root=args.runtime_root,
            data_dir=settings.data_dir,
        )
        project_id = resolved.project_id
        backend_url = resolved.backend_url
        if not args.json:
            print(f"Resolved project: {resolved.project_name or project_id} ({resolved.source})")
    except ProjectDiscoveryError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    diag = audit_project(backend_url, project_id)
    payload = diagnostics_to_payload(diag)
    print_report(diag, as_json=args.json)

    gate = None
    if args.classify:
        gate = classify_live_project_diagnostic(payload)
        if not args.json:
            print()
        print(format_verdict_report(gate, payload))

    if args.check or args.assert_team_if_docx_present:
        failures = assert_acceptance(diag, args.assert_team_if_docx_present)
        if failures:
            for item in failures:
                print(f"ASSERT FAIL: {item}", file=sys.stderr)
            return 1
        print("ASSERT OK")
        return 0

    if args.classify and gate is not None:
        return verdict_exit_code(gate.status)

    if diag.verdict != "OK" and diag.verdict != "single_file_no_team_source":
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
