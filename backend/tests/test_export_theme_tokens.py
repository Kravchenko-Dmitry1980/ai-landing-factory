"""Theme token normalization and export CSS variable parity."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.schemas.style_config import LandingStyleConfigModel, LandingStyleProfile
from app.services.export.export_theme import ExportTheme
from app.services.export.export_theme_css import build_export_css
from app.services.export.styled_html_exporter import StyledHtmlExporter
from app.services.export.theme_tokens import (
    normalize_theme_tokens,
    serialize_theme_tokens,
    theme_tokens_to_css_vars,
)
from tests.fixtures.export_contract_fixture import make_export_fixture, patch_repo_with_fixture

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "theme_tokens"


def _load_fixtures() -> list[tuple[str, dict]]:
    cases = []
    for path in sorted(FIXTURE_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        cases.append((data["id"], data))
    return cases


@pytest.mark.parametrize("fixture_id,fixture", _load_fixtures())
def test_fixture_token_parity(fixture_id: str, fixture: dict) -> None:
    cfg = LandingStyleConfigModel.model_validate(fixture["styleConfig"])
    tokens = serialize_theme_tokens(cfg)
    for key, value in fixture["expected"].items():
        assert tokens[key] == value, f"{fixture_id}.{key}"


def test_every_profile_emits_alf_css_vars() -> None:
    for profile in LandingStyleProfile:
        cfg = LandingStyleConfigModel(profile=profile)
        css = build_export_css(ExportTheme.from_profile(profile), cfg)
        assert "--alf-bg:" in css
        assert "--alf-accent:" in css
        assert "--bg: var(--alf-bg)" in css
        assert "--surface: var(--alf-surface)" in css


def test_compatibility_aliases_in_css_vars_map() -> None:
    tokens = normalize_theme_tokens(LandingStyleConfigModel(profile=LandingStyleProfile.TECH))
    vars_map = theme_tokens_to_css_vars(tokens)
    assert vars_map["--bg"] == "var(--alf-bg)"
    assert vars_map["--accent-light"] == "var(--alf-accent-light)"


def test_custom_style_config_no_raw_prompt_injection() -> None:
    cfg = LandingStyleConfigModel(
        profile=LandingStyleProfile.CUSTOM,
        custom_style_prompt="тёмный <script>alert(1)</script>",
        theme_tokens={"color_scheme": "dark", "accent": "blue", "hero_mode": "future_3d"},
    )
    pid, contract, landing = make_export_fixture(style_config=cfg)
    repo = type("R", (), {})()
    patch_repo_with_fixture(repo, pid, contract, landing)
    exporter = StyledHtmlExporter(repo)

    import asyncio

    html = asyncio.run(exporter.to_html(pid))
    assert "<script>" not in html
    assert "alert(1)" not in html
    assert "theme-custom" in html
    assert "--alf-bg:" in html
    assert "hero--future-3d" in html


def test_token_overrides_removed_from_legacy_apply() -> None:
    """StyledHtmlExporter uses build_export_css, not ad-hoc :root overrides."""
    cfg = LandingStyleConfigModel(profile=LandingStyleProfile.BOLD)
    css = build_export_css(ExportTheme.BOLD, cfg)
    assert "--alf-motion-duration: 0.45s" in css
    assert "--alf-card-transform:" in css
