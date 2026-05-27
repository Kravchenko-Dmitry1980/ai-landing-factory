"""Export theme identifiers for HTML export."""

from __future__ import annotations

from enum import StrEnum

from app.schemas.landing_contract import LandingContract, LandingStylePreset
from app.schemas.style_config import (
    LandingStyleConfigModel,
    LandingStyleProfile,
    default_style_config,
    effective_style_config,
)


class ExportTheme(StrEnum):
    UNIVERSITY_PLATFORM = "university_platform"
    MINIMAL = "minimal"
    CORPORATE = "corporate"
    TECH = "tech"
    BOLD = "bold"
    CUSTOM = "custom"
    ENTERPRISE_DARK = "enterprise_dark"

    def body_class(self) -> str:
        if self == ExportTheme.ENTERPRISE_DARK:
            return "theme-enterprise_dark"
        return f"theme-{self.value}"

    @classmethod
    def from_profile(cls, profile: str | LandingStyleProfile) -> ExportTheme:
        raw = profile.value if isinstance(profile, LandingStyleProfile) else str(profile)
        try:
            return cls(raw)
        except ValueError:
            if raw == cls.ENTERPRISE_DARK:
                return cls.ENTERPRISE_DARK
            return cls.UNIVERSITY_PLATFORM

    @classmethod
    def from_query(cls, theme: str | None) -> ExportTheme:
        if not theme or not theme.strip():
            return cls.UNIVERSITY_PLATFORM
        key = theme.strip().lower()
        if key == cls.ENTERPRISE_DARK:
            return cls.ENTERPRISE_DARK
        try:
            return cls(key)
        except ValueError:
            return cls.UNIVERSITY_PLATFORM


def legacy_style_to_profile(
    style: LandingStylePreset | str | None,
    presentation_style: str | None,
    *,
    has_style_config: bool,
) -> LandingStyleProfile | None:
    """Map legacy contract fields when style_config is absent."""
    if has_style_config:
        return None
    ps = (presentation_style or "").strip()
    if ps and not ps.startswith("layout:"):
        try:
            return LandingStyleProfile(ps)
        except ValueError:
            pass
    style_val = style.value if isinstance(style, LandingStylePreset) else str(style or "")
    mapping = {
        "minimal": LandingStyleProfile.MINIMAL,
        "corporate": LandingStyleProfile.CORPORATE,
        "tech": LandingStyleProfile.TECH,
        "bold": LandingStyleProfile.BOLD,
        "university_platform": LandingStyleProfile.UNIVERSITY_PLATFORM,
    }
    return mapping.get(style_val)


def resolve_export_style(
    contract: LandingContract | None,
    *,
    theme_query: str | None = None,
    style_config_query: LandingStyleConfigModel | None = None,
) -> tuple[ExportTheme, LandingStyleConfigModel, str]:
    """
    Priority:
    1. style_config query (temporary override)
    2. contract.style_config
    3. legacy presentation_style / style preset
    4. theme query
    5. university default
    """
    if style_config_query is not None:
        cfg = style_config_query
        theme = ExportTheme.from_profile(cfg.profile)
        return theme, cfg, theme.body_class()

    if theme_query and theme_query.strip():
        theme = ExportTheme.from_query(theme_query)
        try:
            profile = LandingStyleProfile(theme.value)
            cfg = LandingStyleConfigModel(profile=profile)
        except ValueError:
            cfg = default_style_config()
        return theme, cfg, theme.body_class()

    if contract:
        cfg = effective_style_config(contract)
        theme = ExportTheme.from_profile(cfg.profile)
        return theme, cfg, theme.body_class()

    theme = ExportTheme.UNIVERSITY_PLATFORM
    return theme, default_style_config(), theme.body_class()
