"""Tests for live project JSON verdict gate."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from app.services.diagnostics.live_project_verdict import (
    classify_live_project_diagnostic,
    normalize_diagnostic_payload,
    verdict_exit_code,
)

FIXTURES = Path(__file__).parent / "fixtures" / "diagnostics"
BACKEND = Path(__file__).resolve().parents[1]
CHECK_SCRIPT = BACKEND / "scripts" / "check_live_project_verdict.py"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_single_file_no_team_source() -> None:
    gate = classify_live_project_diagnostic(_load("single_file_no_team_source.json"))
    assert gate.status == "USER_ACTION_REQUIRED"
    assert gate.classification == "single_file_no_team_source"
    assert gate.layer == "user_input"
    assert verdict_exit_code(gate.status) == 0


def test_docx_present_but_team_missing() -> None:
    gate = classify_live_project_diagnostic(_load("docx_present_but_team_missing.json"))
    assert gate.status == "BUG"
    assert gate.classification == "docx_present_but_team_missing"
    assert verdict_exit_code(gate.status) == 1


def test_contract_has_team_but_export_missing() -> None:
    gate = classify_live_project_diagnostic(
        _load("contract_has_team_but_export_missing.json")
    )
    assert gate.status == "BUG"
    assert gate.classification == "contract_has_team_but_export_missing"
    assert gate.layer == "export"


def test_stale_generated_landing() -> None:
    gate = classify_live_project_diagnostic(_load("stale_generated_landing.json"))
    assert gate.status == "STALE"
    assert gate.classification == "stale_generated_landing"
    assert verdict_exit_code(gate.status) == 1


def test_team_pipeline_ok() -> None:
    gate = classify_live_project_diagnostic(_load("team_pipeline_ok.json"))
    assert gate.status == "OK"
    assert gate.classification == "team_pipeline_ok"
    assert verdict_exit_code(gate.status) == 0


def test_ambiguous_inconsistent_state() -> None:
    gate = classify_live_project_diagnostic(
        {
            "source_count": 0,
            "filenames": [],
            "team_structured_count": 0,
            "export_has_team": False,
        }
    )
    assert gate.status == "BUG"
    assert gate.classification == "ambiguous_inconsistent_state"


def test_normalize_legacy_export_field() -> None:
    payload = normalize_diagnostic_payload(
        {
            "export_has_team_section": True,
            "landing_has_team": True,
            "team_structured_count": 3,
        }
    )
    assert payload["export_has_team"] is True
    assert payload["generated_landing_has_team"] is True
    assert payload["contract_has_team"] is True


def test_check_script_json_file_exit_code() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(CHECK_SCRIPT),
            "--json-file",
            str(FIXTURES / "single_file_no_team_source.json"),
        ],
        cwd=str(BACKEND),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "USER_ACTION_REQUIRED" in result.stdout
    assert "single_file_no_team_source" in result.stdout


def test_check_script_bug_exit_code() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(CHECK_SCRIPT),
            "--json-file",
            str(FIXTURES / "docx_present_but_team_missing.json"),
        ],
        cwd=str(BACKEND),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "BUG" in result.stdout
