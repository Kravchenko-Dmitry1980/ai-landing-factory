#!/usr/bin/env python3
"""Smoke test: heuristic visual-difference gate (standard vs WOW).

Not a screenshot diff — a structural heuristic that prevents a "fake" WOW
implementation that merely re-skins the standard export. Verifies the WOW
output is substantially larger, has more visual sections, distinct body
mode, required classes, and that standard has none of them.
"""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.schemas.export_mode import Wow3dRuntime
from app.services.export.export_theme import ExportTheme
from app.services.export.styled_html_exporter import StyledHtmlExporter
from app.services.export.wow.wow_exporter import WowExportOptions, WowHtmlExporter
from tests.fixtures.export_contract_fixture import (
    make_wow_indlab_fixture,
    patch_repo_with_fixture,
)

LENGTH_DELTA_THRESHOLD = 1500  # WOW must add at least this many chars of markup.
WOW_SECTION_IDS = (
    "id='wow-hero'",
    "id='wow-metrics'",
    "id='wow-pipeline'",
    "id='wow-cta'",
)
WOW_REQUIRED_CLASSES = ("wow-landing", "wow-cockpit", "wow-metric-panel", "wow-pipeline-map")


@dataclass(frozen=True)
class Check:
    ok: bool
    label: str

    @property
    def prefix(self) -> str:
        return "OK" if self.ok else "FAIL"


def _repo(contract, landing):
    repo = type("R", (), {})()
    patch_repo_with_fixture(repo, contract.project_id, contract, landing)
    return repo


def _run() -> int:
    _, contract, landing = make_wow_indlab_fixture()
    repo = _repo(contract, landing)
    standard = asyncio.run(
        StyledHtmlExporter(repo).to_html(contract.project_id, theme=ExportTheme.TECH)
    )
    wow = asyncio.run(
        WowHtmlExporter(repo).to_html(
            contract.project_id,
            theme=ExportTheme.TECH,
            options=WowExportOptions(runtime=Wow3dRuntime.NONE),
        )
    )

    checks: list[Check] = []

    delta = len(wow) - len(standard)
    checks.append(
        Check(
            delta >= LENGTH_DELTA_THRESHOLD,
            f"wow markup larger than standard by >= {LENGTH_DELTA_THRESHOLD} "
            f"(delta={delta})",
        )
    )

    wow_sections = sum(1 for sid in WOW_SECTION_IDS if sid in wow)
    checks.append(
        Check(wow_sections >= 4, f"wow has >= 4 visual sections (found {wow_sections})")
    )

    checks.append(
        Check('data-export-mode="wow"' in wow, "wow declares data-export-mode=wow")
    )
    checks.append(
        Check('data-export-mode="wow"' not in standard, "standard does not declare wow mode")
    )

    # Body mode/class differs.
    checks.append(
        Check("wow-landing" in wow and "wow-landing" not in standard, "body marker differs")
    )

    for cls in WOW_REQUIRED_CLASSES:
        checks.append(Check(cls in wow, f"wow contains required class {cls!r}"))

    checks.append(
        Check("wow-metric-panel" not in standard, "standard does not include metric panel")
    )

    failed = 0
    for c in checks:
        print(f"{c.prefix}: {c.label}")
        if not c.ok:
            failed += 1

    print()
    print(f"standard length: {len(standard)}  wow length: {len(wow)}")
    if failed:
        print(f"=== WOW VISUAL DIFFERENCE SMOKE FAILED ({failed} check(s)) ===", file=sys.stderr)
        return 1
    print("=== WOW VISUAL DIFFERENCE SMOKE PASSED ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(_run())
