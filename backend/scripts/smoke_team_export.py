#!/usr/bin/env python3
"""Smoke test: team section present in contract and HTML export."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
DEFAULT_CORPUS = REPO_ROOT / "test_corpus" / "golden"
DEFAULT_BACKEND_URL = "http://127.0.0.1:8001"

sys.path.insert(0, str(BACKEND))

from app.config import settings
from app.repositories.contract_repository import ContractRepository
from app.services.export.styled_html_exporter import ExportTheme, StyledHtmlExporter

from scripts.smoke_corpus import (  # noqa: E402
    _builder,
    _load_simple_yaml,
    _load_project_sources,
    _validate_contract,
)


def _build_project_contract(project_slug: str):
    project_dir = DEFAULT_CORPUS / project_slug
    expected = _load_simple_yaml(project_dir / "expected_contract.yml")
    files = _load_project_sources(project_dir)
    from app.models.domain import utc_now
    from app.schemas.extraction import ExtractionPayload, ExtractionResult
    from uuid import uuid4

    extraction = ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=files,
        extracted_at=utc_now(),
    )
    contract = _builder().build(extraction)
    return contract, expected


def _render_export_html(contract) -> str:
    exporter = StyledHtmlExporter(ContractRepository(settings))
    return exporter._render_from_contract(contract, None, ExportTheme.UNIVERSITY_PLATFORM)


def _team_required(expected: dict) -> bool:
    if expected.get("must_have_team"):
        return True
    return int(expected.get("min_team", 0)) > 0


FORBIDDEN_HTML_NAMES = (
    "Посты Telegram",
    "Из Telegram",
    "Схема обработки данных",
    "Векторная БД",
)


def _validate_team(contract, expected: dict, html: str) -> list[str]:
    errors: list[str] = []
    team = contract.fidelity.team_structured if contract.fidelity else []
    team_count = len(team)
    required = _team_required(expected)
    names = [m.name for m in team]

    for forbidden in expected.get("forbidden_team_names") or FORBIDDEN_HTML_NAMES:
        if forbidden in names:
            errors.append(f"forbidden team member in contract: {forbidden}")
        if f"<h3>{forbidden}</h3>" in html:
            errors.append(f"forbidden team-card in export: {forbidden}")

    if required and team_count == 0:
        errors.append("contract team_structured is empty but team is required")
        return errors

    if not required and team_count == 0:
        if "id='team'" in html or 'id="team"' in html:
            errors.append("export renders team section without valid team")
        return errors

    if team_count > 0:
        if "Команда проекта" not in html:
            errors.append("export HTML missing heading 'Команда проекта'")
        if "team-card" not in html:
            errors.append("export HTML missing team-card")
        if "id='team'" not in html and 'id="team"' not in html:
            errors.append("export HTML missing section id=team")
        for frag in expected.get("must_have_team") or []:
            if not any(frag.lower() in n.lower() for n in names):
                errors.append(f"expected team surname missing: {frag}")

    return errors


def run_offline(project_slug: str) -> int:
    contract, expected = _build_project_contract(project_slug)
    contract_errors = _validate_contract(contract, expected, project_slug)
    html = _render_export_html(contract)
    team_errors = _validate_team(contract, expected, html)
    errors = contract_errors + team_errors
    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        return 1
    team_count = len(contract.fidelity.team_structured) if contract.fidelity else 0
    print(f"OK: team export smoke for {project_slug}")
    print(f"  team_count={team_count} team-card={html.count('team-card')}")
    return 0


def run_api(project_id: str, backend_url: str) -> int:
    base = backend_url.rstrip("/")
    contract_url = f"{base}/api/v1/projects/{project_id}/contract"
    export_url = f"{base}/api/v1/projects/{project_id}/export/html"
    with httpx.Client(timeout=60.0, trust_env=False) as client:
        contract_resp = client.get(contract_url)
        if contract_resp.status_code != 200:
            print(f"FAIL: contract HTTP {contract_resp.status_code}", file=sys.stderr)
            return 1
        export_resp = client.get(export_url, params={"theme": "university_platform"})
        if export_resp.status_code != 200:
            print(f"FAIL: export HTTP {export_resp.status_code}", file=sys.stderr)
            return 1
        payload = export_resp.json()
        html = payload.get("html", "")

    from app.schemas.landing_contract import LandingContract

    contract = LandingContract.model_validate(contract_resp.json())
    team_count = len(contract.fidelity.team_structured) if contract.fidelity else 0
    if team_count == 0:
        print("WARN: contract has no team_structured")
        return 0
    errors = _validate_team(contract, {"min_team": 1}, html)
    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        return 1
    print(f"OK: team export smoke for project_id={project_id}")
    print(f"  team_count={team_count} team-card={html.count('team-card')}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Team section export smoke test")
    parser.add_argument("--project", help="Corpus project slug, e.g. indlab_telegram_news")
    parser.add_argument("--project-id", help="Existing project UUID on running backend")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    args = parser.parse_args()

    if args.project_id:
        return run_api(args.project_id, args.backend_url)
    if args.project:
        return run_offline(args.project)
    parser.error("Provide --project or --project-id")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
