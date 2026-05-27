"""Unit tests for export theme defaults and style_config CSS (no live project)."""

from app.services.export.export_theme import ExportTheme
from app.services.export.export_theme_css import build_export_css
from app.services.export.theme_tokens import normalize_theme_tokens
from app.schemas.style_config import LandingStyleConfigModel, LandingStyleProfile, ThemeTokensModel


def test_export_theme_default_is_university():
    assert ExportTheme.from_query(None) == ExportTheme.UNIVERSITY_PLATFORM
    assert ExportTheme.from_query("") == ExportTheme.UNIVERSITY_PLATFORM
    assert ExportTheme.from_query("neon") == ExportTheme.UNIVERSITY_PLATFORM


def test_export_theme_profiles():
    assert ExportTheme.from_query("tech") == ExportTheme.TECH
    assert ExportTheme.from_query("bold") == ExportTheme.BOLD
    assert ExportTheme.TECH.body_class() == "theme-tech"


def test_token_css_uses_alf_variables():
    cfg = LandingStyleConfigModel(
        profile="custom",
        theme_tokens=ThemeTokensModel(
            accent="blue",
            hero_mode="future_3d",
            color_scheme="dark",
        ),
    )
    css = build_export_css(ExportTheme.CUSTOM, cfg)
    assert "--alf-accent: #2563eb" in css
    assert "--alf-bg:" in css
    assert "--bg: var(--alf-bg)" in css
    tokens = normalize_theme_tokens(cfg)
    assert tokens.heroMode == "future_3d"
