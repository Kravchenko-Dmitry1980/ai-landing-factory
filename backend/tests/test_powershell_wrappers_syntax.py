"""PowerShell wrapper syntax smoke tests (check_last/current_project.ps1)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

WRAPPERS = [
    REPO_ROOT / "scripts" / "check_last_project.ps1",
    REPO_ROOT / "scripts" / "check_current_project.ps1",
]


def _run_powershell(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["powershell", "-NoProfile", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        cwd=str(REPO_ROOT),
    )


@pytest.mark.parametrize("wrapper", WRAPPERS, ids=lambda p: p.name)
def test_powershell_wrapper_parses_without_missing_brace(wrapper: Path) -> None:
    path = str(wrapper).replace("'", "''")
    result = _run_powershell(
        [
            "-Command",
            f"[scriptblock]::Create((Get-Content -LiteralPath '{path}' -Raw -Encoding UTF8)) | Out-Null",
        ]
    )
    assert result.returncode == 0, result.stderr or result.stdout


@pytest.mark.parametrize("wrapper", WRAPPERS, ids=lambda p: p.name)
def test_powershell_wrapper_help_exits_zero(wrapper: Path) -> None:
    result = _run_powershell(
        [
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(wrapper),
            "-Help",
        ]
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "Usage:" in result.stdout
