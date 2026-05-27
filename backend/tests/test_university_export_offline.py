"""Offline university_platform export smoke — no live ENDO project required."""

from __future__ import annotations

import asyncio
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from app.services.export.export_theme import ExportTheme
from app.services.export.styled_html_exporter import StyledHtmlExporter
from tests.fixtures.export_contract_fixture import (
    make_university_export_fixture,
    patch_repo_with_fixture,
)

BACKEND = Path(__file__).resolve().parents[1]
SCRIPT_PATH = BACKEND / "scripts" / "smoke_university_export.py"


async def _export_university_html() -> str:
    pid, contract, landing = make_university_export_fixture(long_essence=True)
    repo = type("R", (), {})()
    patch_repo_with_fixture(repo, pid, contract, landing)
    exporter = StyledHtmlExporter(repo)
    return await exporter.to_html(pid, theme=ExportTheme.UNIVERSITY_PLATFORM)


def test_synthetic_contract_exports_university_theme() -> None:
    html = asyncio.run(_export_university_html())
    assert "body class='theme-university_platform'" in html
    assert "University Platform Export Fixture" in html


def test_export_contains_anchor_nav() -> None:
    html = asyncio.run(_export_university_html())
    assert "alf-section-nav" in html
    assert "href='#team'" in html
    assert "href='#stack'" in html


def test_export_contains_collapsible_for_long_essence() -> None:
    html = asyncio.run(_export_university_html())
    assert "collapsible-section" in html


def test_export_contains_alf_tokens_and_aliases() -> None:
    html = asyncio.run(_export_university_html())
    assert "--alf-bg:" in html
    assert "--bg: var(--alf-bg)" in html
    assert "--alf-accent:" in html


def test_export_no_external_script_or_cdn() -> None:
    html = asyncio.run(_export_university_html())
    assert re.search(r"<script\b", html, re.I) is None
    assert re.search(r'(?:src|href)\s*=\s*["\']https?://', html, re.I) is None


def test_offline_smoke_script_exit_zero() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND)
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--offline"],
        cwd=str(BACKEND),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
