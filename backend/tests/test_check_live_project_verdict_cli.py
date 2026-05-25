"""CLI tests for check_live_project_verdict.py."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pytest

from app.services.diagnostics.project_discovery import ProjectDiscoveryError, ResolvedProject
from scripts import check_live_project_verdict as cli_mod


def test_parser_accepts_latest_and_current_flags() -> None:
    parser = cli_mod.build_parser()
    args = parser.parse_args(["--latest"])
    assert args.latest is True
    assert args.current is False

    args2 = parser.parse_args(["--current"])
    assert args2.current is True


def test_resolve_target_json_file_skips_project() -> None:
    parser = cli_mod.build_parser()
    args = parser.parse_args(["--json-file", "dummy.json"])
    assert cli_mod.resolve_target(args) is None


def test_resolve_target_requires_mode() -> None:
    parser = cli_mod.build_parser()
    args = parser.parse_args([])
    with pytest.raises(ProjectDiscoveryError, match="--latest"):
        cli_mod.resolve_target(args)


def test_main_json_file_no_discovery(monkeypatch, tmp_path: Path) -> None:
    fixture = {
        "source_count": 2,
        "filenames": ["a.pptx", "b.docx"],
        "team_structured_count": 15,
        "export_has_team": True,
        "landing_stale": False,
    }
    path = tmp_path / "ok.json"
    path.write_text(json.dumps(fixture), encoding="utf-8")

    exit_code = cli_mod.main(["--json-file", str(path)])
    assert exit_code == 0


def test_main_resolved_project(monkeypatch) -> None:
    pid = str(uuid4())
    monkeypatch.setattr(
        cli_mod,
        "resolve_target",
        lambda _args: ResolvedProject(
            project_id=pid,
            backend_url="http://127.0.0.1:8010",
            source="latest",
            project_name="Demo",
        ),
    )
    monkeypatch.setattr(
        cli_mod,
        "load_payload",
        lambda **kwargs: {
            "source_count": 1,
            "verdict": "single_file_no_team_source",
            "filenames": ["x.pptx"],
            "team_structured_count": 0,
            "export_has_team": False,
            "landing_stale": False,
        },
    )
    assert cli_mod.main(["--latest"]) == 0


def test_resolve_backend_url_from_runtime(monkeypatch, tmp_path: Path) -> None:
    runtime = tmp_path / ".runtime"
    runtime.mkdir()
    (runtime / "ports.json").write_text(
        json.dumps({"backend_url": "http://127.0.0.1:8006"}),
        encoding="utf-8",
    )
    parser = cli_mod.build_parser()
    args = parser.parse_args(["--latest", "--runtime-root", str(tmp_path)])
    assert cli_mod.resolve_backend_url(args) == "http://127.0.0.1:8006"
