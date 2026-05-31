"""Tests for demo-ready showcase templates (Stage P.6.3)."""

from __future__ import annotations

import pytest

from app.services.showcase.showcase_schema import (
    ShowcaseLayout,
    ShowcaseMode,
    ShowcaseTheme,
)
from app.services.showcase.showcase_templates import (
    ShowcaseTemplateId,
    create_default_showcase_template,
)


def test_uii_ai_projects_template_title_subtitle_org() -> None:
    req = create_default_showcase_template(ShowcaseTemplateId.UII_AI_PROJECTS)
    assert req.title == "Витрина AI-проектов УИИ"
    assert "VR/AR" in (req.subtitle or "")
    assert req.organization == "Университет искусственного интеллекта"


def test_uii_ai_projects_uses_gallery_arc_layout() -> None:
    req = create_default_showcase_template()
    assert req.layout == ShowcaseLayout.GALLERY_ARC


def test_uii_ai_projects_uses_tech_theme_and_vr_ready() -> None:
    req = create_default_showcase_template()
    assert req.theme == ShowcaseTheme.TECH
    assert req.mode == ShowcaseMode.VR_READY


def test_unknown_template_id_rejected() -> None:
    with pytest.raises(ValueError):
        create_default_showcase_template("unknown")  # type: ignore[arg-type]
