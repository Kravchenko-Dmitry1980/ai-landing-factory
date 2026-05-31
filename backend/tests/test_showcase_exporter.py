"""Tests for the VR/AR Showcase HTML exporter (Stage P.5)."""

from __future__ import annotations

import pytest

from app.services.showcase.showcase_html_exporter import ShowcaseHtmlExporter
from app.services.showcase.showcase_layout import compute_placements
from app.services.showcase.showcase_safety import sanitize_url
from app.services.showcase.showcase_schema import (
    ShowcaseConfig,
    ShowcaseLayout,
    ShowcaseProject,
)


def _project(**overrides) -> ShowcaseProject:
    base = dict(
        id="p1",
        title="Проект",
        description="Описание проекта.",
        demo_url="https://aistudio.google.com/",
        landing_url="/landings/p1",
        category="Demo",
        tags=["a", "b"],
    )
    base.update(overrides)
    return ShowcaseProject(**base)


def _config(projects: list[ShowcaseProject]) -> ShowcaseConfig:
    return ShowcaseConfig(title="Витрина", projects=projects)


def test_generates_valid_html_with_a_scene() -> None:
    result = ShowcaseHtmlExporter().export(_config([_project()]))
    assert result.html.startswith("<!DOCTYPE html>")
    assert "<a-scene" in result.html
    assert "</a-scene>" in result.html
    assert "aframe" in result.html.lower()


def test_includes_fallback_2d_section() -> None:
    result = ShowcaseHtmlExporter().export(_config([_project()]))
    assert 'class="showcase-fallback"' in result.html
    assert "Проекты витрины" in result.html


def test_project_cards_count_matches_input() -> None:
    projects = [_project(id=f"p{i}", title=f"Проект {i}") for i in range(4)]
    result = ShowcaseHtmlExporter().export(_config(projects))
    assert result.project_count == 4
    # One fallback card per project.
    assert result.html.count('class="showcase-card"') == 4


def test_demo_urls_escaped_and_validated() -> None:
    project = _project(demo_url="https://aistudio.google.com/?a=1&b=2")
    result = ShowcaseHtmlExporter().export(_config([project]))
    # Ampersand must be escaped in the rendered href attribute.
    assert "https://aistudio.google.com/?a=1&amp;b=2" in result.html
    assert "?a=1&b=2\"" not in result.html


def test_javascript_url_rejected() -> None:
    project = _project(demo_url="javascript:alert(1)", landing_url=None)
    result = ShowcaseHtmlExporter().export(_config([project]))
    assert "javascript:alert(1)" not in result.html
    assert any("demo_url rejected" in w for w in result.warnings)


@pytest.mark.parametrize(
    "bad_url",
    [
        "javascript:alert(1)",
        "data:text/html,<script>alert(1)</script>",
        "vbscript:msgbox(1)",
        "file:///etc/passwd",
    ],
)
def test_sanitize_url_rejects_dangerous_schemes(bad_url: str) -> None:
    assert sanitize_url(bad_url) is None


@pytest.mark.parametrize(
    "good_url",
    [
        "https://example.com/x",
        "http://example.com",
        "/relative/path",
        "./local.html",
        "#anchor",
    ],
)
def test_sanitize_url_accepts_safe_urls(good_url: str) -> None:
    assert sanitize_url(good_url) == good_url


def test_malicious_title_escaped() -> None:
    project = _project(title="<script>alert('xss')</script>")
    result = ShowcaseHtmlExporter().export(_config([project]))
    assert "<script>alert('xss')</script>" not in result.html
    assert "&lt;script&gt;" in result.html


def test_empty_project_list_returns_warning_but_valid_html() -> None:
    result = ShowcaseHtmlExporter().export(_config([]))
    assert result.project_count == 0
    assert "<a-scene" in result.html
    assert 'class="showcase-fallback"' in result.html
    assert result.warnings
    assert any("no projects" in w.lower() for w in result.warnings)


def test_gallery_arc_positions_deterministic() -> None:
    first = compute_placements(ShowcaseLayout.GALLERY_ARC, 3)
    second = compute_placements(ShowcaseLayout.GALLERY_ARC, 3)
    assert first == second
    assert len(first) == 3
    # Middle card of a symmetric arc sits on the central axis.
    assert first[1].x == pytest.approx(0.0, abs=1e-6)
    # Symmetric outer cards mirror across X.
    assert first[0].x == pytest.approx(-first[2].x, abs=1e-6)


def test_grid_hall_and_circle_booths_layouts() -> None:
    grid = compute_placements(ShowcaseLayout.GRID_HALL, 5)
    circle = compute_placements(ShowcaseLayout.CIRCLE_BOOTHS, 5)
    assert len(grid) == 5
    assert len(circle) == 5
    # Grid second row exists for 5 items with 4 columns.
    assert grid[4].y < grid[0].y


def test_runtime_note_present() -> None:
    result = ShowcaseHtmlExporter().export(_config([_project()]))
    assert "VR/AR Showcase export uses A-Frame runtime." in result.html
