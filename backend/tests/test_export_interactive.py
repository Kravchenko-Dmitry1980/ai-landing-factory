"""P.4 interactive static export: anchor nav, CSS-only motion, collapsible sections."""

from __future__ import annotations

import asyncio
import re

import pytest

from app.schemas.fidelity import FidelityMetadata, LandingModule, TeamMember
from app.schemas.generation import GeneratedLanding, LandingBlockContent
from app.schemas.landing_contract import ContractStatus, LandingBlock, LandingContract, LandingStylePreset
from app.schemas.style_config import LandingStyleConfigModel, LandingStyleProfile
from app.services.export.export_interactive_css import CSS_INTERACTIVE
from app.services.export.export_theme import ExportTheme
from app.services.export.export_theme_css import build_export_css
from app.services.export.styled_html_exporter import StyledHtmlExporter
from tests.fixtures.export_contract_fixture import make_export_fixture, patch_repo_with_fixture
from uuid import uuid4
from datetime import datetime, timezone


def _rich_export_fixture():
    project_id = uuid4()
    now = datetime.now(timezone.utc)
    long_essence = "A" * 400
    blocks = [
        LandingBlock(key="tagline", title="Tagline", content="Demo tagline.", bullets=[]),
        LandingBlock(key="essence", title="Суть", content=long_essence, bullets=[]),
        LandingBlock(
            key="tasks",
            title="Задачи",
            content="",
            bullets=[f"Task {i}" for i in range(1, 9)],
        ),
        LandingBlock(key="team", title="Team", content="", bullets=["Alex Dev — Lead"]),
        LandingBlock(
            key="outlook",
            title="Outlook",
            content="",
            bullets=["Future item 1", "Future item 2"],
        ),
    ]
    contract = LandingContract(
        project_id=project_id,
        status=ContractStatus.DRAFT,
        style=LandingStylePreset.TECH,
        title="Interactive Export Fixture",
        client="QA Lab",
        goals=["demo"],
        presentation_style="tech",
        style_config=LandingStyleConfigModel(profile=LandingStyleProfile.TECH),
        blocks=blocks,
        fidelity=FidelityMetadata(
            parser_mode="structured",
            modules=[
                LandingModule(name="Core API", description="Main service", type="backend"),
                LandingModule(name="UI", description="Frontend", type="frontend"),
            ],
            team_structured=[
                TeamMember(name="Alex Dev", role="Lead", project_area="Backend", contributions=["Built API"]),
            ],
            tech_stack_grouped={"Backend": ["Python", "FastAPI"], "Frontend": ["React"]},
        ),
        updated_at=now,
        version=1,
    )
    landing = GeneratedLanding(
        project_id=project_id,
        style=LandingStylePreset.TECH,
        blocks=[
            LandingBlockContent(key="tagline", title="Tagline", body="Demo", bullets=[]),
        ],
        generated_at=now,
        prompt_version="test",
    )
    return project_id, contract, landing


def test_css_interactive_has_reduced_motion_and_nav() -> None:
    assert "prefers-reduced-motion" in CSS_INTERACTIVE
    assert ".alf-section-nav" in CSS_INTERACTIVE
    assert "hero--future-3d::after" in CSS_INTERACTIVE
    assert "alf-card--interactive" in CSS_INTERACTIVE


def test_export_html_contains_anchor_nav() -> None:
    pid, contract, landing = _rich_export_fixture()
    repo = type("R", (), {})()
    patch_repo_with_fixture(repo, pid, contract, landing)
    exporter = StyledHtmlExporter(repo)
    html = asyncio.run(exporter.to_html(pid, theme=ExportTheme.TECH))

    assert "alf-section-nav" in html
    assert "href='#essence'" in html
    assert "href='#tasks'" in html
    assert "href='#modules'" in html
    assert "href='#stack'" in html
    assert "href='#team'" in html
    assert "href='#outlook'" in html
    assert "Суть" in html
    assert "Системы" in html


def test_export_html_contains_interactive_css_block() -> None:
    pid, contract, landing = _rich_export_fixture()
    repo = type("R", (), {})()
    patch_repo_with_fixture(repo, pid, contract, landing)
    html = asyncio.run(StyledHtmlExporter(repo).to_html(pid, theme=ExportTheme.TECH))

    assert "scroll-behavior: smooth" in html
    assert "collapsible-section" in html
    assert "alf-card--interactive" in html
    assert "--alf-bg:" in html


def test_export_html_no_external_cdn_or_scripts() -> None:
    pid, contract, landing = _rich_export_fixture()
    repo = type("R", (), {})()
    patch_repo_with_fixture(repo, pid, contract, landing)
    html = asyncio.run(StyledHtmlExporter(repo).to_html(pid, theme=ExportTheme.TECH))

    assert "<script" not in html.lower()
    assert re.search(r'<link[^>]+href=["\']https?://', html, re.I) is None
    assert re.search(r'src=["\']https?://', html, re.I) is None


def test_custom_prompt_no_injection_in_interactive_export() -> None:
    cfg = LandingStyleConfigModel(
        profile=LandingStyleProfile.CUSTOM,
        custom_style_prompt="тёмный <script>alert(1)</script> технологичный 3D",
        theme_tokens={"color_scheme": "dark", "accent": "blue", "hero_mode": "future_3d"},
    )
    pid, contract, landing = make_export_fixture(style_config=cfg)
    repo = type("R", (), {})()
    patch_repo_with_fixture(repo, pid, contract, landing)
    html = asyncio.run(StyledHtmlExporter(repo).to_html(pid))

    assert "<script>" not in html
    assert "alert(1)" not in html
    assert "hero--future-3d" in html
    assert "alf-section-nav" in html or "section-nav" in html


def test_tech_profile_css_includes_glass_cards() -> None:
    cfg = LandingStyleConfigModel(profile=LandingStyleProfile.TECH)
    css = build_export_css(ExportTheme.TECH, cfg) + CSS_INTERACTIVE
    assert "theme-tech" in css or ".theme-tech" in css
    assert "backdrop-filter" in css
