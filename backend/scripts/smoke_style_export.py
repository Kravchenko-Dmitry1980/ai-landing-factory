"""Offline + optional HTTP smoke for export style profiles."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from uuid import UUID

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.schemas.style_config import (
    LandingStyleConfigModel,
    LandingStyleProfile,
    ThemeTokensModel,
    default_style_config,
)
from app.services.export.styled_html_exporter import StyledHtmlExporter
from tests.fixtures.export_contract_fixture import make_export_fixture, patch_repo_with_fixture


async def _offline_checks() -> list[str]:
    errors: list[str] = []
    exporter_cls = StyledHtmlExporter

    cases = [
        ("default", default_style_config(), "theme-university_platform"),
        ("tech", LandingStyleConfigModel(profile=LandingStyleProfile.TECH), "theme-tech"),
        ("bold", LandingStyleConfigModel(profile=LandingStyleProfile.BOLD), "theme-bold"),
        (
            "custom",
            LandingStyleConfigModel(
                profile=LandingStyleProfile.CUSTOM,
                custom_style_prompt="тёмный <script>alert(1)</script>",
                theme_tokens=ThemeTokensModel(
                    color_scheme="dark",
                    accent="blue",
                    hero_mode="future_3d",
                ),
            ),
            "theme-custom",
        ),
    ]

    for label, cfg, expected_class in cases:
        pid, contract, landing = make_export_fixture(style_config=cfg)
        repo = type("R", (), {})()
        patch_repo_with_fixture(repo, pid, contract, landing)
        exporter = exporter_cls(repo)
        html = await exporter.to_html(pid)
        if expected_class not in html:
            errors.append(f"{label}: missing {expected_class}")
        if "<script>" in html:
            errors.append(f"{label}: script leaked")
        if "--alf-bg:" not in html:
            errors.append(f"{label}: missing --alf-bg")
        if "--bg: var(--alf-bg)" not in html:
            errors.append(f"{label}: missing compatibility alias --bg")
        if label == "tech" and "--alf-bg: #0f172a" not in html:
            errors.append(f"{label}: tech dark bg missing")
        if label == "bold" and "--alf-motion-duration: 0.45s" not in html:
            errors.append(f"{label}: bold expressive motion missing")
        if label == "custom" and "alert(1)" in html:
            errors.append(f"{label}: prompt leaked")
        if label == "custom" and "hero--future-3d" not in html:
            errors.append(f"{label}: missing hero--future-3d")
        if label == "custom" and (
            "--alf-hero-gradient:" not in html or "gradient" not in html
        ):
            errors.append(f"{label}: missing hero gradient token")

    return errors


def _http_checks(base_url: str, project_id: str) -> list[str]:
    import urllib.error
    import urllib.request

    errors: list[str] = []
    api = f"{base_url.rstrip('/')}/api/v1/projects/{project_id}/export/html"

    def fetch(query: str = "") -> str:
        url = f"{api}{query}"
        with urllib.request.urlopen(url, timeout=15) as resp:
            return json.loads(resp.read().decode())["html"]

    try:
        html = fetch()
        if "theme-university_platform" not in html:
            errors.append("HTTP default: missing theme-university_platform")
        if "--alf-bg:" not in html:
            errors.append("HTTP default: missing --alf-bg")
    except (urllib.error.URLError, TimeoutError, KeyError) as exc:
        errors.append(f"HTTP default skipped: {exc}")
        return errors

    try:
        html = fetch("?theme=tech")
        if "theme-tech" not in html:
            errors.append("HTTP tech: missing theme-tech")
        if "--bg: var(--alf-bg)" not in html:
            errors.append("HTTP tech: missing alias")
    except Exception as exc:
        errors.append(f"HTTP tech: {exc}")

    return errors


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend-url", default="")
    parser.add_argument("--project-id", default="")
    args = parser.parse_args()

    errors = await _offline_checks()
    if args.backend_url and args.project_id:
        try:
            errors.extend(_http_checks(args.backend_url, args.project_id))
        except Exception as exc:
            print(f"WARN: HTTP smoke skipped: {exc}")

    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        return 1
    print("OK: style export smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
