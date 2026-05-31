#!/usr/bin/env python3
"""Smoke test: WOW landing export (standard vs wow vs wow+A-Frame).

Offline, synthetic Indlab-like contract. Asserts the WOW export is materially
different from standard, contains required classes/metrics/pipeline, and that
the A-Frame variant uses the local vendored runtime only (no CDN).
"""

from __future__ import annotations

import asyncio
import re
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

WOW_REQUIRED = (
    "wow-landing",
    "wow-hero",
    "wow-cockpit",
    "wow-metric-panel",
    "wow-metric-card",
    "wow-pipeline-map",
    "wow-pipeline-node",
    "wow-demo-cta",
    'data-export-mode="wow"',
)
EXTERNAL_CDN_RE = re.compile(r'(?:src|href)\s*=\s*["\']https?://', re.I)


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


def _build_all() -> tuple[str, str, str]:
    _, contract, landing = make_wow_indlab_fixture()
    repo = _repo(contract, landing)
    standard = asyncio.run(
        StyledHtmlExporter(repo).to_html(contract.project_id, theme=ExportTheme.TECH)
    )
    wow_css = asyncio.run(
        WowHtmlExporter(repo).to_html(
            contract.project_id,
            theme=ExportTheme.TECH,
            options=WowExportOptions(runtime=Wow3dRuntime.NONE),
        )
    )
    wow_aframe = asyncio.run(
        WowHtmlExporter(repo).to_html(
            contract.project_id,
            theme=ExportTheme.TECH,
            options=WowExportOptions(runtime=Wow3dRuntime.AFRAME),
        )
    )
    return standard, wow_css, wow_aframe


def _run() -> int:
    standard, wow_css, wow_aframe = _build_all()
    checks: list[Check] = []

    # Standard must not contain wow markers.
    for cls in ("wow-landing", "wow-cockpit", "wow-pipeline-map"):
        checks.append(Check(cls not in standard, f"standard has no {cls!r}"))
    checks.append(Check("<a-scene" not in standard, "standard has no <a-scene>"))

    # WOW CSS-only must contain required markers.
    for token in WOW_REQUIRED:
        checks.append(Check(token in wow_css, f"wow has {token!r}"))
    checks.append(
        Check(wow_css.count("wow-metric-card") >= 4, "wow has >= 4 metric cards")
    )
    checks.append(Check("/showcase" in wow_css, "wow has showcase CTA link"))

    # Impact metrics present.
    for token in ("800", "17"):
        checks.append(Check(token in wow_css, f"wow metrics contain {token!r}"))

    # CSS-only safety: no scripts, no CDN, no a-scene.
    checks.append(Check("<script" not in wow_css, "wow CSS-only has no <script>"))
    checks.append(Check("<a-scene" not in wow_css, "wow CSS-only has no <a-scene>"))
    checks.append(
        Check(not EXTERNAL_CDN_RE.search(wow_css), "wow CSS-only has no external CDN")
    )

    # A-Frame variant: local vendored runtime + scene, no CDN.
    checks.append(
        Check("vendor/aframe/aframe.min.js" in wow_aframe, "wow A-Frame uses local vendor runtime")
    )
    checks.append(Check("<a-scene" in wow_aframe, "wow A-Frame has <a-scene>"))
    checks.append(
        Check("https://aframe.io" not in wow_aframe, "wow A-Frame has no aframe.io CDN")
    )
    checks.append(
        Check(not EXTERNAL_CDN_RE.search(wow_aframe), "wow A-Frame has no external CDN")
    )

    failed = 0
    for c in checks:
        print(f"{c.prefix}: {c.label}")
        if not c.ok:
            failed += 1

    print()
    if failed:
        print(f"=== WOW LANDING EXPORT SMOKE FAILED ({failed} check(s)) ===", file=sys.stderr)
        return 1
    print("=== WOW LANDING EXPORT SMOKE PASSED ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(_run())
