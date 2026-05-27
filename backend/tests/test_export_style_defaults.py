"""Unit tests for export theme defaults and style_config CSS (no live project)."""

from app.services.export.export_interactive_css import ACCENT_HEX
from app.services.export.export_theme import ExportTheme
from app.services.export.styled_html_exporter import StyledHtmlExporter
from app.schemas.style_config import LandingStyleConfigModel, ThemeTokensModel


def test_export_theme_default_is_university():
    assert ExportTheme.from_query(None) == ExportTheme.UNIVERSITY_PLATFORM
    assert ExportTheme.from_query("") == ExportTheme.UNIVERSITY_PLATFORM
    assert ExportTheme.from_query("neon") == ExportTheme.UNIVERSITY_PLATFORM


def test_token_overrides_inject_accent_and_hero():
    css = ":root { --bg: #fff; }\n"
    config = LandingStyleConfigModel(
        profile="custom",
        theme_tokens=ThemeTokensModel(
            accent="blue",
            hero_mode="future_3d",
            color_scheme="dark",
        ),
    )
    out = StyledHtmlExporter._apply_token_overrides(css, config)
    assert f"--accent: {ACCENT_HEX['blue']}" in out
    assert "--bg: #0f1419" in out
