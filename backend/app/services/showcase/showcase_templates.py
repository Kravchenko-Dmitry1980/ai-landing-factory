"""Demo-ready showcase templates (Stage P.6.3).

Pure helpers for prefilled showcase create payloads. No storage or API changes.
"""

from __future__ import annotations

from enum import StrEnum

from app.services.showcase.showcase_schema import (
    ShowcaseCreateRequest,
    ShowcaseLayout,
    ShowcaseMode,
    ShowcaseTheme,
)


class ShowcaseTemplateId(StrEnum):
    """Known showcase starter templates."""

    UII_AI_PROJECTS = "uii_ai_projects"


_TEMPLATE_DEFAULTS: dict[ShowcaseTemplateId, ShowcaseCreateRequest] = {
    ShowcaseTemplateId.UII_AI_PROJECTS: ShowcaseCreateRequest(
        title="Витрина AI-проектов УИИ",
        subtitle=(
            "Интерактивная VR/AR-витрина учебных и исследовательских AI-проектов"
        ),
        organization="Университет искусственного интеллекта",
        layout=ShowcaseLayout.GALLERY_ARC,
        mode=ShowcaseMode.VR_READY,
        theme=ShowcaseTheme.TECH,
    ),
}


def create_default_showcase_template(
    template_id: ShowcaseTemplateId | str = ShowcaseTemplateId.UII_AI_PROJECTS,
) -> ShowcaseCreateRequest:
    """Return a create payload prefilled for the given template id."""

    key = ShowcaseTemplateId(template_id)
    return _TEMPLATE_DEFAULTS[key].model_copy(deep=True)
